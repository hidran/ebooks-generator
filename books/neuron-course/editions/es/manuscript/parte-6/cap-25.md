# Capítulo 25 — Proyecto final B: el servicio de soporte agéntico

**Stack:** Laravel 12 + `neuron-core/neuron-laravel`.
**Cubre:** todo lo que hay en este libro.

## Qué vas a construir

Una aplicación de atención al cliente multi-tenant donde un agente gestiona las consultas de principio a fin:

- Responde preguntas sobre políticas a partir de una base de conocimiento (RAG)
- Consulta pedidos y estado de los envíos (tools)
- Prepara reembolsos, que se pausan para aprobación humana por encima de un umbral (workflow + interrupción)
- Transmite su trabajo al cliente en vivo
- Escala a un humano cuando no puede ayudar
- Registra todo para auditoría

Este es el Caso C de la Sección 1.7, aquel en el que las cuatro preguntas apuntaban al peldaño 4. Se gana cada pieza de la maquinaria de este libro, que es exactamente por lo que es el proyecto final.

## La arquitectura

```
Cliente (chat Livewire)
   │
   ├─ POST del mensaje
   │
SupportAgent (RAG + tools + historial en Eloquent)
   │
   ├─ pregunta de política → recuperación, filtrada por tenant + visibilidad
   ├─ pregunta de pedido   → SearchOrdersTool / GetOrderStatusTool
   └─ petición de reembolso → RefundWorkflow
                          │
                          ├─ EligibilityNode   (structured output)
                          ├─ AmountNode        (tool: calcula el reembolso)
                          ├─ ApprovalNode      (interrumpe si > umbral)
                          │      │
                          │      └─ EloquentPersistence → fila PendingApproval
                          │                                    │
                          │                              El responsable aprueba
                          │                                    │
                          │                              Trabajo ResumeWorkflow
                          │
                          └─ ExecuteRefundNode (idempotente, auditado)
```

## Orden de construcción

**1 — Preparación de Laravel.** `composer require`, publica configuración y migraciones, una prueba de humo de la facade `Neuron`, la estructura `app/Neuron`.

**2 — Andamiaje del dominio.** Tenants, usuarios, pedidos, reembolsos, artículos de la base de conocimiento. Factorías y seeders. Todavía nada de IA, deliberadamente, para que veas qué poco de la aplicación es agéntico.

**3 — El primer agente.** `SupportAgent` con inyección de dependencias, `EloquentChatHistory` delimitado por tenant y usuario, un controlador, una página Blade sencilla.

**4 — Ingesta de la base de conocimiento.** El trabajo `IndexArticle`, un splitter de Markdown propio, metadatos de tenant y visibilidad, la alerta de desfase de `indexed_at`.

**5 — RAG con filtros de permisos.** `vectorStore()` con filtros de tenant y visibilidad, el system prompt antialucinación y el test en CI que afirma que un artículo restringido nunca aflora.

**6 — Tools de pedidos.** `SearchOrdersTool` y `GetOrderStatusTool` con el tenant como dependencia del constructor, selección de columnas, resultados acotados, cadenas para el caso vacío.

**7 — Chat con streaming en Livewire.** `wire:stream`, etiquetas de actividad de tools mediante lista de permitidos, la lista de comprobación de buffering verificada contra staging.

**8 — El workflow de reembolso.** Eventos, nodos, structured output `RefundEligibility`, el bucle acotado, una subclase de `WorkflowState`.

**9 — Humano en el circuito.** `interrupt()` con un `RefundApprovalInterrupt` propio, `checkpoint()` alrededor de la llamada de elegibilidad, `EloquentPersistence`, la tabla `PendingApproval`.

**10 — La pantalla de aprobación.** Páginas de índice y de detalle, una policy, resolución con `lockForUpdate()`, el trabajo `ResumeWorkflow`, notificaciones con caducidad.

**11 — Observabilidad y evaluaciones.** Inspector con el paquete de Laravel, registro del uso, una suite de evaluación con `FaithfulnessJudge`, los tests de aislamiento entre tenants y de permisos en CI.

**12 — Endurecimiento para producción.** Presupuestos, límites de tasa, respaldo entre providers, la tabla de auditoría y la lista de comprobación de despliegue de la Sección 23.6 recorrida punto por punto.

## Las tres partes más difíciles

### 1. El error del checkpoint

Constrúyelo mal primero. Calcula la elegibilidad del reembolso dentro de `ApprovalNode` sin checkpoint, interrumpe, reanuda, y observa que la elegibilidad recalculada difiere de la que aprobó el responsable.

Después envuélvelo:

```php
$eligibility = $this->checkpoint('eligibility', fn () => EligibilityAgent::make()->structured(
    new UserMessage($this->describeOrder($order)),
    RefundEligibility::class
));
```

El mismo contenido al reanudar.

**Son los veinte minutos más valiosos del proyecto final**: un fallo de corrección demostrable, arreglado en una línea, que ningún tutorial cubre. En un workflow de reembolsos es la diferencia entre aprobar un importe y pagar otro.

### 2. Ejecución idempotente del reembolso

```php
class ExecuteRefundNode extends Node
{
    public function __invoke(RefundApproved $event, RefundState $state): StopEvent
    {
        $refund = DB::transaction(function () use ($event, $state) {
            $order = Order::whereKey($state->orderId())->lockForUpdate()->firstOrFail();

            $existing = $order->refunds()
                ->where('workflow_id', $state->workflowId())
                ->first();

            if ($existing !== null) {
                return $existing;   // this workflow already refunded — return the same record
            }

            return $order->refunds()->create([
                'amount'      => $event->amount,
                'reason'      => $event->reason,
                'workflow_id' => $state->workflowId(),
                'approved_by' => $event->approvedBy,
            ]);
        });

        AgentAction::record($state, 'execute_refund', ['refund_id' => $refund->id]);

        return new StopEvent(result: $refund->id);
    }
}
```

El `workflow_id` del registro de reembolso es la clave de idempotencia. Un workflow reanudado dos veces —porque un trabajo reintentó, o porque dos responsables aprobaron simultáneamente— crea un solo reembolso.

Esto no es una preocupación de IA. Es higiene corriente de sistemas distribuidos, e importa aquí porque los sistemas agénticos reintentan y se reanudan mucho más que los gestores de peticiones típicos.

### 3. El camino de escalado

Todo agente necesita una forma de rendirse:

```php
class EscalateTool extends Tool
{
    public function __construct(
        private readonly Conversation $conversation,
    ) {
        parent::__construct(
            'escalate_to_human',
            'Hand this conversation to a human support agent. Use this when you cannot answer '
            . 'from the knowledge base, when the customer explicitly asks for a human, when the '
            . 'customer is upset, or when the request is outside what your tools can do. '
            . 'Using this tool is always an acceptable outcome — prefer it over guessing.'
        );
    }

    public function __invoke(string $reason): string
    {
        $this->conversation->escalate($reason);

        return 'This conversation has been passed to a human agent. '
             . 'Tell the customer someone will reply shortly.';
    }
}
```

> **"Using this tool is always an acceptable outcome — prefer it over guessing."**

Esa frase es la cadena más importante de la aplicación. Sin una vía de escape explícita, un modelo ante una petición imposible inventará algo, porque producir una respuesta es lo que hace. Darle una forma legítima de fallar es la medida antialucinación más eficaz de todo el sistema, y cuesta una tool.

## Rúbrica de evaluación

| Área | Criterio |
|---|---|
| **Aislamiento** | El test de tenants pasa con IDs de conversación que colisionan |
| **Recuperación** | El test de artículos restringidos pasa; filtros aplicados dentro de `vectorStore()` |
| **Tools** | Delimitadas por constructor; acotadas; `visible()` desde policies; tools de escritura con tope 1 |
| **Workflow** | Toda llamada al LLM previa a una interrupción con checkpoint; bucles acotados |
| **Aprobación** | Resolución con `lockForUpdate()`; caducidad programada; reanudación enviada, no en línea |
| **Idempotencia** | El reembolso lleva una clave ligada al workflow; la doble reanudación crea un solo registro |
| **Observabilidad** | Inspector configurado con `autoFlush` en los workers; uso registrado |
| **Calidad** | Suite de evaluación con `FaithfulnessJudge`; una puntuación de referencia registrada |
| **Auditoría** | Toda tool con consecuencias escribe una fila en `agent_actions` |
| **Escalado** | El agente tiene, y usa, una forma de rendirse |

## El ejercicio final

Responde por escrito a las cinco preguntas de la Sección 23.6 sobre tu propio proyecto final:

1. ¿Cuánto cuesta este agente por petición, y a qué volumen eso se convierte en un problema?
2. ¿Qué es lo peor que puede hacer, y qué lo detiene?
3. ¿Cómo averiguaría qué hizo, dentro de tres semanas?
4. ¿Qué pasa cuando el provider está caído?
5. ¿Qué datos salen de mi infraestructura, y adónde van?

Escribe las respuestas en lugar de limitarte a pensarlas. Las que cuesta escribir son aquellas en las que el sistema no está terminado.

Quien pueda responder a las cinco sobre código que escribió él mismo ha terminado este libro en el sentido que importa.
