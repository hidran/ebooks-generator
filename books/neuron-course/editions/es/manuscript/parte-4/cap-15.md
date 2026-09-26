# Capítulo 15 — Humano en el circuito

::: {.callout .callout-tip}
[El código de este capítulo]{.callout-title}

La versión ejecutable de cada listado que sigue está en [`chapters/Ch15`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch15), en el repositorio complementario. Clónalo, ejecuta `composer install` y los ejemplos funcionan contra un Ollama local sin ninguna clave de API.
:::

## 15.1 La interrupción: la funcionalidad, no el fallo

### Qué hace

El patrón de interrupción de NeuronAI permite que un flujo de trabajo **pause la ejecución y espere una entrada externa antes de reanudarse.**

No «para y empieza de nuevo». Pausa —en mitad de un nodo—, preservando todo lo que la ejecución ha hecho hasta ese momento, y continúa desde ese nodo con la respuesta del humano inyectada.

### Las cuatro fases

1. **Petición** — un nodo identifica algo que requiere intervención humana y llama a `$this->interrupt()` con un `InterruptRequest` que lo describe.
2. **Pausa** — el ejecutor persiste la ejecución y `run()` devuelve un estado marcado como interrumpido. A tu código no se le lanza nada.
3. **Decisión** — tu aplicación presenta la petición a un humano, que aprueba, rechaza o edita.
4. **Reanudación** — devuelves la decisión como un array simple con `resume($payload)->run()`. Los nodos completados se reproducen desde el almacén, el nodo en pausa se ejecuta otra vez y, esta vez, `interrupt()` devuelve la decisión.

> Un flujo de trabajo puede pausarse con seguridad en cualquier punto, persistir su estado y reanudarse donde lo dejó, **incluso entre sesiones distintas.**

### Por qué «incluso entre sesiones distintas» es toda la historia

Léelo literalmente. El proceso PHP termina. La petición web se completa. El servidor se redespliega. Pasan tres días.

Entonces el responsable pincha «aprobar» en un correo, y el flujo de trabajo continúa desde el nodo donde se detuvo, con todo su contexto intacto.

Para un público de PHP esto es genuinamente notable, porque el modelo de ejecución de PHP es célebremente de ámbito de petición. La respuesta del framework son los pasos duraderos de la Sección 13.5 más una capa de persistencia, y convierte «la IA lo hace todo» en «la IA hace el trabajo, un humano toma las decisiones», que es la única forma que la mayoría de las empresas desplegará de verdad para algo con consecuencias.

### Una pausa es un resultado, no una excepción

Una ejecución suspendida es un resultado ordinario de `run()`. Lo compruebas en el estado devuelto:

```php
$state = $workflow->run();

if ($state->isInterrupted()) {
    $request = $state->getInterruptRequest();
    // show it to a human
}
```

Dentro del motor, `interrupt()` sigue desenrollando el nodo: lanza una señal interna que el ejecutor captura en el límite del paso. Por eso cualquier código de un nodo puede interrumpir, por muy adentro de un ayudante que esté, sin que cada capa intermedia tenga que hilar un valor de retorno de vuelta. Pero la señal nunca te llega. El ejecutor la convierte en una suspensión persistida y retorna con normalidad.

La consecuencia práctica: no hay nada que capturar, ni nada que se registre por accidente como una caída. Lo que no debes olvidar, en cambio, es *mirar*. Un llamador que ignore `isInterrupted()` tratará una ejecución en pausa como una terminada y leerá un estado que todavía no se ha escrito. La Sección 15.4 cubre la gestión.

### Dónde cambia esto lo que puedes construir

Las cuatro capas de defensa de la Sección 5.10 incluían «ofrecida, con puerta en ejecución». Esta es esa capa, y desbloquea toda una categoría de aplicación:

- Reembolsos por encima de un umbral
- Correos enviados a clientes en nombre de la empresa
- Cualquier borrado
- Publicar contenido
- Cualquier cosa con un requisito de visto bueno regulatorio

Sin interrupción, estas cosas están o totalmente automatizadas (inaceptable) o no automatizadas (sin valor). Con ella, la IA hace la preparación y un humano decide, lo que es a la vez seguro y útil.

### Puntos clave

- Pausa a mitad de nodo, persiste la ejecución, reanuda con intervención humana.
- Cuatro fases: petición, pausa, decisión, reanudación.
- Sobrevive a la muerte del proceso y a esperas largas: esta es la funcionalidad distintiva.
- Una pausa se devuelve, no se lanza: comprueba `isInterrupted()` en cada estado que recibas.

## 15.2 interrupt() y ApprovalRequest

### La petición integrada

```php
namespace App\Neuron;

use NeuronAI\Agent\Interrupt\ApprovalRequest;
use NeuronAI\Workflow\Interrupt\Action;
use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\WorkflowState;

class InterruptionNode extends Node
{
    public function __invoke(InputEvent $event, WorkflowState $state): InputEvent|OutputEvent
    {
        // Interrupt the workflow and wait for the feedback.
        $payload = $this->interrupt(
            new ApprovalRequest(
                message: 'Should I continue?',
                actions: [
                    new Action('delete_file', 'Delete File', 'Delete /var/log/old.txt'),
                ],
            )
        );

        $decision = $payload['delete_file'] ?? 'reject';

        if ($decision === 'approve') {
            $state->set('is_sufficient', true);

            return new OutputEvent();
        }

        $state->set('is_sufficient', false);
        $state->set('user_feedback', \is_array($decision) ? $decision[1] : null);

        return new InputEvent();
    }
}
```

### Leerlo

**`$this->interrupt($request)`** — la pausa. En la primera pasada la ejecución se detiene aquí. Al reanudarse, el nodo se ejecuta otra vez e `interrupt()` devuelve el array que el llamador pasó a `resume()`.

**`ApprovalRequest`** — la petición integrada para el caso más común: aprobar acciones. Vive en `NeuronAI\Agent\Interrupt`, porque la aprobación de herramientas del propio agente (Sección 15.5) se construye sobre ella, mientras que `Action` sigue en `NeuronAI\Workflow\Interrupt`. Nada impide que la use un nodo de un flujo de trabajo cualquiera.

**`Action`** — un único elemento decidible: un identificador, una etiqueta y una descripción. Varias acciones en una misma petición significa que el humano decide varias cosas en una sola interacción, que es la diferencia entre una pantalla de aprobación y cinco.

**El payload** — un array simple, con las claves que tú decidas. Este libro usa la misma convención que la aprobación de herramientas del agente, con el ID de la acción como clave: `'approve'`, `'reject'` o `['reject', 'reason']`. Es un contrato entre el nodo y quien reanude la ejecución, así que elige una forma y mantenla.

**El motivo de un rechazo** — más útil de lo que parece. Un rechazo con motivo puede ir directo a la siguiente llamada del agente como orientación, convirtiendo «no» en «no, porque X» y permitiendo que el bucle mejore de verdad.

**Devolver `InputEvent` al rechazar** — este nodo vuelve atrás. El rechazo no es un fallo; es otra iteración. Esa combinación de interrupción más bucle es el patrón de refinamiento con humano en el circuito, y es lo que construye el Laboratorio 10.

`ApprovalRequest` y `Action` son **solo de salida**. `Action` es un objeto de valor de solo lectura: sus propiedades son `readonly` y no tiene métodos `approve()`, `reject()` ni `feedback()`. La petición describe lo que se pregunta; la respuesta viaja de vuelta por separado, como payload. Nunca modificas la petición para registrar una decisión.

::: {.callout .callout-warning}
[Los ejemplos de la documentación no coinciden con el código]{.callout-title}

La documentación importa `ApprovalRequest` desde `NeuronAI\Workflow\Interrupt`, que no existe; la clase es `NeuronAI\Agent\Interrupt\ApprovalRequest`. Su ejemplo de petición propia sobrescribe `jsonSerialize()`, que es `final` en `InterruptRequest`, y su ejemplo de reanudación usa un argumento de constructor `runId:` que `Workflow` no tiene. Los tres fallan en la primera ejecución. Apéndice A, puntos 34 a 36.
:::

### Guía de diseño para las peticiones de aprobación

**Escribe el mensaje para quien decide, no para el desarrollador.** Lo están viendo en un correo o en una pantalla de administración, sin contexto. `'Should I continue?'` es un mal mensaje. `'Approve a €240 refund for order #4471 — customer reports item arrived damaged'` permite decidir sin abrir otro sistema.

**Incluye en la descripción lo suficiente para decidir.** El tercer argumento de `Action` es donde va la sustancia.

**Agrupa las decisiones relacionadas en una sola petición.** Cinco acciones en una petición gana a cinco interrupciones sucesivas, cada una de las cuales es un despertar, una notificación y una espera aparte. Los ID de las acciones deben ser únicos dentro de una petición; un duplicado se rechaza al construir la petición, porque su decisión nunca podría entregarse.

### Puntos clave

- `$this->interrupt($request)` pausa y, al reanudarse, devuelve el array del payload.
- `ApprovalRequest` (en `NeuronAI\Agent\Interrupt`) más `Action` cubre aprobar/rechazar.
- La petición es solo de salida; la decisión vuelve como un array simple cuya forma defines tú.
- Escribe los mensajes para quien decide; agrupa las decisiones relacionadas.

## 15.3 Peticiones de interrupción propias

### Por qué aprobar/rechazar no siempre basta

`ApprovalRequest` cubre «¿debería hacer esta acción?». No cubre «aquí tienes un borrador: edítalo antes de que lo guarde», ni «elige una de estas tres opciones», ni «rellena el campo que falta».

La arquitectura es deliberadamente abierta. Hay dos tipos de pausa —esperar un evento y esperar una hora del reloj—, y `ApprovalRequest` es simplemente una `WaitForEventRequest` que escucha un evento llamado `approval`. Creas las tuyas extendiendo `WaitForEventRequest` de la misma manera.

### La implementación

```php
use NeuronAI\Workflow\Interrupt\WaitForEventRequest;

class ContentReviewInterrupt extends WaitForEventRequest
{
    public function __construct(
        protected string $message,
        protected string $content,
    ) {
        parent::__construct('content.reviewed');
    }

    public function getMessage(): string
    {
        return $this->message;
    }

    public function getContent(): string
    {
        return $this->content;
    }

    protected function metadata(): array
    {
        return [
            'message' => $this->message,
            'content' => $this->content,
        ];
    }
}
```

Tres responsabilidades:

**Nombrar el evento** que espera: aquí, `content.reviewed`. Ese nombre es el que `signal()` comprueba al reanudar (más abajo).

**Llevar los datos** que el humano necesita para decidir, más lo que vaya a editar.

**`metadata()`** — los campos que necesita tu frontend. `jsonSerialize()` es `final`: el framework siempre emite el ID de la interrupción, el tipo y el nombre del evento, y fusiona tus metadatos después. Fíjate en la implicación: tu interrupción cruza una frontera JSON. Mantenla serializable y plana.

Lo que vuelve no es un objeto de petición reconstruido. El motor persiste la propia petición, así que no hay ningún `fromArray()` que escribir. La respuesta del humano llega como un array de payload, y el nodo lee de él lo que necesita.

Ese viaje de ida y vuelta —objeto PHP → JSON → interfaz → campos editados → array de payload— es todo el ciclo de vida, y conocerlo es saber dónde encaja tu frontend.

### Usarla

```php
class InterruptionNode extends Node
{
    public function __invoke(InputEvent $event, WorkflowState $state): SaveEvent
    {
        // Generate an article, once. See Section 15.5 for why this is memoized.
        $draft = $this->memoize('draft', fn (): string => ContentCreatorAgent::make()
            ->chat(new UserMessage($event->prompt))
            ->getMessage()
            ?->getContent() ?? '');

        // Interrupt the workflow and wait for the edited version.
        $payload = $this->interrupt(
            new ContentReviewInterrupt(
                message: 'This is the new article. Review the content before saving it to the database.',
                content: $draft
            )
        );

        // Save the content the human sent back
        $state->set('content', $payload['content'] ?? $draft);

        return new SaveEvent();
    }
}
```

Y la reanudación, desde lo que sea que reciba la edición:

```php
$state = ArticleWorkflow::make(workflowId: $workflowId)
    ->setPersistence($persistence)
    ->signal('content.reviewed', ['content' => $editedText])
    ->run();
```

`signal()` es `resume()` con una protección: entrega el payload solo si la interrupción actual está esperando ese nombre de evento, y lanza una excepción en caso contrario. Úsalo cuando el llamador sabe a qué está respondiendo: un gestor de webhook para `payment.received` no debería poder responder a una aprobación por accidente.

### El patrón que merece un nombre

El agente generó contenido. El humano lo **editó**. El flujo de trabajo guardó la versión **editada**.

Eso no es aprobación: es colaboración. La IA produce un borrador, el humano lo corrige, el sistema usa la versión corregida. Para generación de contenidos, redacción de documentos, sugerencias de código y extracción de datos, esto es mejor producto que aprobar/rechazar, porque el caso común es «casi bien» y no «sí o no».

Como principio de diseño: **cuando la respuesta humana probable sea «casi, pero cambia esto», construye una interrupción editable en lugar de una aprobación.**

::: {.callout .callout-warning}
[Este ejemplo genera contenido antes de interrumpir]{.callout-title}

Que es exactamente la situación de la que trata la Sección 15.5. Sin el `memoize()` a su alrededor, reanudar este nodo vuelve a ejecutar `ContentCreatorAgent` y la edición del humano se aplica a un borrador *distinto*. Lee la Sección 15.5 antes de publicar nada con esta forma.
:::

### Esperar eventos y horas

Dos ayudantes cubren las pausas que no son en absoluto una decisión humana:

```php
// Suspend until an external event arrives, or the deadline passes.
$payment = $this->awaitEvent('payment.received', expiresAt: new \DateTimeImmutable('+2 days'));

if ($payment === null) {
    return new OrderExpired();       // the deadline passed, nothing arrived
}

// Suspend until a clock time.
$this->sleepUntil(new \DateTimeImmutable('tomorrow 09:00'));
```

`awaitEvent()` es `interrupt()` con una `WaitForEventRequest`; `sleepUntil()` es `interrupt()` con una `SleepUntilRequest`. El motor registra el plazo, pero no ejecuta ningún temporizador: en el núcleo nada se despierta por sí solo. Tu planificador (cron, un trabajo diferido en cola) llama a `resume()->run()` sin payload cuando llega el momento, y el flujo de trabajo comprueba el reloj por sí mismo: antes del plazo la ejecución sigue suspendida; después, `awaitEvent()` devuelve `null` y `sleepUntil()` retorna. El nodo nunca compara relojes.

`ApprovalRequest` acepta el mismo plazo opcional como tercer argumento, `expiresAt:`.

### Diseño de las peticiones de interrupción

- Incluye todo lo necesario para decidir. El humano no debería tener que abrir otro sistema.
- Mantenla plana y serializable: se convierte en JSON y se persiste con la ejecución.
- Incluye una referencia estable a lo que se está decidiendo (un ID), para poder detectar una petición obsoleta.
- Fija una caducidad. Una petición de aprobación que aparece tres semanas después puede estar respondiendo a una pregunta que ya no aplica, y `expiresAt` convierte el tiempo de espera en una rama de tu nodo en lugar de un trabajo de limpieza.

### Puntos clave

- Extiende `WaitForEventRequest` para cualquier cosa más allá de aprobar/rechazar; nombra el evento que espera.
- Sobrescribe `metadata()`, no `jsonSerialize()`; no hay `fromArray()`: la respuesta vuelve como un array de payload.
- `signal($name, $payload)` reanuda solo si la petición actual espera ese evento.
- `awaitEvent()` y `sleepUntil()` pausan a la espera de eventos y horas; tu planificador llama a `resume()->run()`.
- Cuando la respuesta suele ser «casi», hazla editable.

## 15.4 Persistir, detectar y reanudar

### La persistencia es obligatoria

```php
$workflow = PublishWorkflow::make()
    ->setPersistence(new FilePersistence($storage));
```

Por defecto, un flujo de trabajo usa `InMemoryPersistence`, que vive y muere con el proceso PHP. Con ella una ejecución puede pausarse y continuar dentro de un mismo script, pero en cuanto el proceso termina la ejecución en pausa desaparece.

Sin persistencia duradera no hay reanudación entre procesos. Esto es lo primero que hay que hacer bien. Puedes fijarla en el punto de llamada como arriba, o devolverla desde el hook `persistence()` del flujo de trabajo para que todas las instancias de la clase la reciban.

### Detectar la pausa

```php
$state = $workflow->run();

if (!$state->isInterrupted()) {
    echo 'Completed without interruption: ' . \var_export($state->get('outcome'), true) . "\n";
    exit(0);
}

$request = $state->getInterruptRequest();
$workflowId = $state->getWorkflowId();

\file_put_contents(
    $storage . "/pending-{$workflowId}.json",
    \json_encode($request, \JSON_PRETTY_PRINT | \JSON_THROW_ON_ERROR),
);
```

Del estado salen dos cosas:

- **`getInterruptRequest()`** — qué mostrarle al humano. Es `JsonSerializable`.
- **`getWorkflowId()`** — el identificador para continuar. Sin él no puedes reanudar.

El framework ya ha persistido la ejecución: sus pasos completados, su estado y la propia petición. Lo que almacenas *tú* es el ID del flujo de trabajo y lo que necesite tu interfaz, para que tu aplicación pueda encontrar la decisión pendiente, presentarla y reconectar la respuesta. El `start.php` del repositorio complementario escribe la petición en un archivo JSON, que para una CLI es exactamente suficiente:

```
Suspended, awaiting a human decision.
  Workflow ID : workflow_7509539539310313472
  Request     : {"interruptId":1,"type":"wait_for_event","eventName":"approval",...}
```

### Reanudar

```php
$payload = [
    'delete_file' => $decision === 'approve'
        ? 'approve'
        : ['reject', 'Keep it until the audit closes.'],
];

$state = PublishWorkflow::make(workflowId: $workflowId)
    ->setPersistence(new FilePersistence($storage))
    ->resume($payload)
    ->run();
```

Tres requisitos:

1. **La misma clase de flujo de trabajo**: el proceso que reanuda tiene que reconstruir un grafo idéntico, y una clase es la forma de garantizarlo.
2. **La misma capa de persistencia** y **el mismo ID del flujo de trabajo.**
3. **El payload**, que lleva la decisión del humano, pasado a `resume()`.

`resume()` solo prepara la respuesta; `run()` la ejecuta. Los dos van siempre juntos. Cambia `run()` por `events()` y la continuación se transmite, exactamente como una ejecución nueva (Sección 14.4).

Ejecuta `start.php` y `resume.php` del repositorio complementario como dos comandos separados. La propuesta generada antes de la interrupción se imprime una vez, en el primer proceso, y nunca en el segundo. Ejecuta `resume.php` una segunda vez con el mismo ID y falla con «No run in flight»: una ejecución completada limpia tras de sí.

### ID del flujo de trabajo e ID de ejecución

Una ejecución lleva dos identificadores, y solo uno de ellos sirve para continuar.

**El ID del flujo de trabajo** nombra la partición del almacén donde viven los registros de la ejecución. Es el identificador para continuar: lo que guardas y lo que pasas a `make(workflowId: ...)`. Un flujo de trabajo simple recibe uno generado (`workflow_…`) en su primer `run()`; antes de eso, `getWorkflowId()` es `null`.

**El ID de ejecución** (`getRunId()`) es un sello de generación dentro de esa partición. Cambia cada vez que arranca una ejecución nueva bajo el mismo ID del flujo de trabajo, y se usa para las barreras y la observabilidad: nunca para continuar.

Un flujo de trabajo también puede declarar su ID como clave de negocio sobrescribiendo `workflowId()`:

```php
class RefundWorkflow extends Workflow
{
    public function __construct(protected string $orderId)
    {
        parent::__construct();
    }

    public function workflowId(): ?string
    {
        return 'refund:' . $this->orderId;
    }
}

// Later, in a process that knows only the order:
RefundWorkflow::make(orderId: $orderId)
    ->setPersistence($persistence)
    ->resume(['refund' => 'approve'])
    ->run();
```

Ahora no hay nada que guardar aparte: el ID del pedido *es* el camino de vuelta a la ejecución. Además impone una regla que de otro modo tendrías que construir tú: **una sola ejecución viva por ID del flujo de trabajo**. Llamar a `run()` mientras una ejecución para esa clave está suspendida lanza `RunInFlightException`, cuyo mensaje indica qué la resuelve y cuya propiedad `interrupt` contiene la petición pendiente. El Agent usa exactamente este mecanismo, con su ID de hilo como ID del flujo de trabajo (Sección 15.5).

### Motores de persistencia

```php
use NeuronAI\Workflow\Persistence\DatabasePersistence;

$persistence = new DatabasePersistence(new \PDO($dsn, $user, $password));   // table: workflow_store
```

**MySQL / MariaDB:**

```sql
CREATE TABLE workflow_store (
    `partition` VARCHAR(255) NOT NULL,
    `key`       VARCHAR(255) NOT NULL,
    `value`     TEXT NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`partition`, `key`)
);
```

**PostgreSQL:**

```sql
CREATE TABLE workflow_store (
    "partition" VARCHAR(255) NOT NULL,
    "key"       VARCHAR(255) NOT NULL,
    "value"     TEXT NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("partition", "key")
);
```

Lee el esquema con atención, porque te dice qué está pasando. Una sola tabla, con clave por partición y clave: cada registro de una ejecución —su evento de inicio, su registro de control, cada paso completado, cada valor memoizado, el estado suspendido— es una fila en la partición que lleva el nombre de su ID del flujo de trabajo. Los valores son cadenas serializadas opacas; la tabla no sabe nada de flujos de trabajo. `partition` y `key` son palabras reservadas en MySQL, de ahí las comillas invertidas. Y `updated_at` está ahí para que puedas encontrar ejecuciones obsoletas; añade un índice si piensas consultarlo.

Los demás motores almacenan los mismos registros:

- **`EloquentPersistence(WorkflowStore::class)`** — un modelo de Laravel con columnas `partition`, `key` y `value` (Capítulo 18).
- **`RedisPersistence($redis, prefix: 'neuron:workflow:')`** — un hash por ejecución, necesita `ext-redis`. No fija ningún TTL: la limpieza es tarea del flujo de trabajo, así que configura la expulsión para que no descarte ejecuciones vivas.

Usa `FilePersistence` para CLI y desarrollo: sobrevive a los reinicios, pero está pensada para un solo proceso. Usa los motores de base de datos, Eloquent o Redis para cualquier cosa con varios procesos o de producción; cada una de sus escrituras es una operación condicional y atómica, que es en lo que se apoya la sección siguiente.

### Las cuatro preguntas operativas

Ningún tutorial las cubre y todo sistema de producción las necesita.

**1. ¿A quién se notifica?** La interrupción no envía un correo. Lo hace tu código. Conecta la notificación donde detectes `isInterrupted()`.

**2. ¿Y si nadie responde?** Dale a la petición un `expiresAt` y programa para esa hora un trabajo que llame a `resume()->run()` sin payload. El flujo de trabajo comprueba el plazo por sí mismo y el nodo toma su rama de tiempo agotado: escalar, hacer caducar o rechazar automáticamente es una decisión de tu nodo, no un script de limpieza. Para las ejecuciones que simplemente quieras eliminar, `abandonRun()` descarta una ejecución en pausa y libera su ID del flujo de trabajo.

**3. ¿Cómo evitas la doble reanudación?** Dos responsables abren el mismo enlace de aprobación y ambos pinchan. La carrera la gestiona el motor: cada modificación es una escritura condicional sobre el registro de control de la ejecución, así que solo gana una continuación, una respuesta aceptada no puede sustituirse por otra en conflicto, y la reanudación de una ejecución completada falla con «No run in flight». Lo que el motor no puede saber es a *qué* petición iba destinada una entrega retrasada. Un trabajo en cola que pueda reintentarse debe llevar el ID de ejecución y el intento de ejecución que observó, y pasarlos como barreras:

```php
$state = $workflow->resume(
    $payload,
    expectedRunId: $runId,
    expectedExecutionAttempt: $attempt,
)->run();
```

Si la ejecución ha avanzado —una nueva generación, u otro proceso ya la ha continuado—, la llamada lanza `StaleWorkflowRunException` antes de tocar nada. Aun así, tu interfaz debería marcar la petición como resuelta para que el segundo responsable vea «ya decidido» en lugar de un error.

**4. ¿Y si hay un despliegue en medio?** El estado persistido es PHP serializado, y contiene tus clases: el objeto de estado, los eventos, la petición de interrupción. Un despliegue que renombre una clase o cambie una property romperá la deserialización de las ejecuciones en vuelo. O bien vacías antes de desplegar, o versionas tus peticiones de interrupción. Lo mismo se aplica al actualizar el propio NeuronAI: las ejecuciones suspendidas con una versión anterior del formato del almacén no pueden reanudarse con una más reciente.

Esa última es la arista afilada, y merece detenerse en ella. Los objetos PHP serializados de larga vida a través de despliegues son un problema difícil conocido, y la interrupción te mete de lleno en él. La mitigación —mantén las peticiones de interrupción y el estado pequeños, planos y cámbialos rara vez— es una regla de diseño, no algo que descubrir durante un incidente.

### Puntos clave

- La persistencia duradera es obligatoria para reanudar entre procesos; `FilePersistence` para CLI, un motor de base de datos, Eloquent o Redis para producción.
- `run()` retorna; comprueba `isInterrupted()`, guarda `getWorkflowId()` y muestra `getInterruptRequest()`.
- Reanuda con la misma clase, la misma persistencia y el mismo ID del flujo de trabajo: `resume($payload)->run()`.
- El ID del flujo de trabajo es el identificador para continuar; el ID de ejecución es un sello de generación. Declara `workflowId()` para reanudar por clave de negocio.
- Cuatro preguntas operativas: notificación, tiempo de espera (`expiresAt`), doble reanudación (escrituras condicionales y barreras), compatibilidad con los despliegues.

## 15.5 Memoización, interrupciones condicionales y middleware

### El problema de la reejecución

Esta sección contiene la advertencia de corrección más importante del libro.

Cuando un flujo de trabajo se reanuda, los nodos completados no se vuelven a ejecutar: sus resultados se reproducen desde el almacén. Pero **el nodo que fue interrumpido se reejecuta desde el principio, incluido el código anterior a la interrupción.** Así es como `interrupt()` consigue devolver el payload: la ejecución tiene que volver a alcanzarlo.

Léelo con atención, porque tiene un coste real. Si tu nodo llama a un LLM, luego interrumpe y luego se reanuda, **la llamada al LLM se ejecuta otra vez.** Pagas dos veces, esperas dos veces y, por la Sección 1.5, puedes obtener una *respuesta distinta* la segunda vez.

Lo que significa que el humano aprobó una cosa y el flujo de trabajo procede con otra.

Eso no es desperdicio. Es un error de corrección y, en un contexto regulado, un fallo de auditoría. Tiene una solución de una línea.

### memoize()

```php
class InterruptionNode extends Node
{
    public function __invoke(InputEvent $event, WorkflowState $state): InputEvent|OutputEvent
    {
        // The result of this closure is persisted and returned when the node re-runs.
        $sentiment = $this->memoize('agent-1', fn (): SentimentResult => MyAgent::make()->structured(
            new UserMessage($event->review),
            SentimentResult::class
        ));

        if ($sentiment->isNegative()) {
            // Interrupt the workflow and wait for the feedback.
            $payload = $this->interrupt(
                new ApprovalRequest(
                    message: 'Negative review detected. Should I answer it?',
                    actions: [
                        new Action('review_id', 'Answer review', $sentiment->content),
                    ],
                )
            );

            if (($payload['review_id'] ?? null) === 'approve') {
                $state->set('is_sufficient', true);

                return new OutputEvent();
            }
        }

        $state->set('is_sufficient', false);

        return new InputEvent();
    }
}
```

Dos argumentos:

- Un **nombre**, único dentro del nodo
- Una **función anónima** que envuelve el trabajo cuyo resultado debe guardarse

Primera ejecución: la función anónima se ejecuta y su resultado se escribe en el almacén como parte del paso actual. En la reejecución —tras una interrupción o tras una caída— se devuelve el resultado almacenado sin volver a ejecutar la función anónima. El nodo llega al punto de interrupción con los mismos valores que en la ejecución anterior.

El `ApprovalNode` del repositorio complementario lo hace visible: su función anónima memoizada imprime una línea, y entre `start.php` y `resume.php` esa línea aparece exactamente una vez.

**La regla: cualquier llamada a un LLM, cualquier llamada a una API de pago y cualquier cosa no determinista que preceda a un `interrupt()` en el mismo nodo pertenece dentro de un `memoize()`.** No hay excepciones que merezca la pena aprender. La propia función anónima debe ser una función pura del evento y del estado del nodo: `time()`, la aleatoriedad y la E/S van *dentro* de ella, nunca a su alrededor.

Un límite que conviene tener presente. `memoize()` guarda un resultado una vez que la función anónima ha retornado. Si el proceso muere después de un efecto secundario externo pero antes de que se guarde el resultado —el correo salió, la memoización no se confirmó—, la función anónima se ejecuta de nuevo. Donde eso importe, pasa una clave de idempotencia al sistema externo.

En material más antiguo encontrarás `checkpoint()`. Sigue existiendo, obsoleto, y simplemente llama a `memoize()`.

### isResuming() y getResumePayload()

A veces quieres ramificar en la *cabecera* de un nodo según si te estás reanudando:

```php
class InterruptionNode extends Node
{
    public function __invoke(InputEvent $event, WorkflowState $state): InputEvent|OutputEvent
    {
        if ($this->isResuming()) {
            $payload = $this->getResumePayload();

            if (($payload['review_id'] ?? null) === 'approve') {
                $state->set('is_sufficient', true);

                return new OutputEvent();
            }
        }

        $this->interrupt(
            new ApprovalRequest(
                message: 'Should I continue?',
                actions: [
                    new Action('review_id', 'Answer review', $state->get('review')),
                ],
            )
        );

        $state->set('is_sufficient', false);

        return new InputEvent();
    }
}
```

`isResuming()` es verdadero cuando el nodo está despertando con una respuesta; `getResumePayload()` devuelve esa respuesta. Ante un rechazo, el código sigue hasta `interrupt()`, que —al seguir en reanudación— devuelve el payload en lugar de pausar otra vez, y el nodo vuelve atrás. Te permite gestionar el caso de reanudación explícitamente al principio en vez de volver a recorrer el cuerpo entero del nodo: una forma más limpia cuando el nodo hace trabajo sustancial antes de la interrupción.

### interruptIf()

```php
// Conditional interruption
$payload = $this->interruptIf(
    $state->get('is_sufficient') == true,
    new ApprovalRequest(
        message: 'Should I continue?',
        actions: [
            new Action('review_id', 'Answer review', $state->get('review')),
        ],
    )
);

// Or use a callback to evaluate the condition
$payload = $this->interruptIf(
    fn (): bool => $state->get('is_sufficient', false),
    new ApprovalRequest(
        message: 'Should I continue?',
        actions: [
            new Action('review_id', 'Answer review', $state->get('review')),
        ],
    )
);
```

Cuando la condición es falsa, `interruptIf()` devuelve `null` y la ejecución sigue de largo; `null` significa «no se preguntó a ningún humano». La forma con callback difiere la evaluación al momento de la comprobación. Al reanudarse, la condición ni siquiera se vuelve a evaluar: el nodo ya se pausó ahí, así que se devuelve el payload.

**El argumento de producto a favor de la interrupción condicional:** si toda acción necesita aprobación, los humanos dejan de leer y empiezan a pinchar. Interrumpe solo en los casos que lo merecen —por encima de un umbral, por debajo de una puntuación de confianza, fuera de los parámetros normales— y las aprobaciones seguirán significando algo.

### Aprobación de herramientas en los agentes

La misma idea aplicada a las llamadas a herramientas, sin escribir un nodo. Un agente es un flujo de trabajo, y su `ToolNode` comprueba cada herramienta antes de ejecutarla: si la herramienta requiere aprobación, el nodo interrumpe con un `ApprovalRequest` que lleva una `Action` por cada llamada sujeta a aprobación.

Si una herramienta requiere aprobación se declara en la propia herramienta: el Capítulo 5 cubre la API de declaración. Una herramienta puede declarar su propia política, condicionada a sus argumentos; devolver una cadena cuenta como «sí» y es el motivo que se muestra a quien aprueba:

```php
class BuyTicketTool extends Tool
{
    // ...

    protected function approvalPolicy(): bool|string
    {
        return ($this->inputs['amount'] ?? 0) > 100
            ? 'Purchases above €100 need a human sign-off'
            : false;
    }
}
```

O bien el agente la sobrescribe donde adjunta la herramienta: `->requireApproval()`, `->suppressApproval()` o `->withApprovalPolicy(fn (ToolInterface $tool) => ...)`.

Las compras por debajo de 100 € proceden; las mayores esperan a un humano. Esta es la cuarta capa de la Sección 5.10, ahora concreta, y es un producto mucho mejor que permitir siempre o bloquear siempre.

El viaje de ida y vuelta, en dos peticiones:

```php
// Request 1: the model asks to buy a €240 ticket.
$agent = TicketAgent::make(threadId: $threadId)
    ->setChatHistory(new SQLChatHistory($pdo))
    ->setPersistence(new DatabasePersistence($pdo));

$state = $agent->chat(new UserMessage('Buy the concert ticket'));

if ($state->isInterrupted()) {
    $pending = $agent->pendingApprovals();   // Action[]: id is the tool call ID
}

// Request 2: the human approved $callId. Same thread, same persistence.
$state = TicketAgent::make(threadId: $threadId)
    ->setChatHistory(new SQLChatHistory($pdo))
    ->setPersistence(new DatabasePersistence($pdo))
    ->submitApprovalDecisions([$callId => 'approve'])
    ->run();
```

El **ID de hilo es el ID del flujo de trabajo del agente**, así que el punto de conexión de aprobación no necesita más que el hilo para encontrar la ejecución en pausa. Las decisiones tienen como clave el ID de la llamada a herramienta y adoptan las mismas tres formas de antes: `'approve'`, `'reject'`, `['reject', 'reason']`. Una herramienta solo se ejecuta si se aprueba explícitamente; un conjunto parcial de decisiones vuelve a suspender la ejecución hasta que lleguen las demás. Un nuevo `chat()` en el hilo mientras hay una decisión pendiente se rechaza con `RunInFlightException`: bloquea la entrada en tu interfaz hasta que lleguen las decisiones. Aquí un historial de conversación duradero importa tanto como una persistencia duradera: la llamada a herramienta pendiente vive en el hilo.

El Capítulo 22 convierte esto en una pantalla de aprobación real en Laravel.

### ToolSearchMiddleware

```php
$agent->addMiddleware(InferenceNode::class, new ToolSearchMiddleware($toolPool));
```

Para agentes con catálogos de herramientas grandes. En lugar de enviar todos los esquemas en cada petición —el coste acumulativo de la Sección 1.3—, le da al modelo una herramienta `tool_search` y carga bajo demanda las herramientas coincidentes desde el conjunto disponible, cinco como máximo por defecto.

Esta es la respuesta a «¿y si tengo 200 herramientas?», que es la pregunta natural después del Capítulo 5.

Fíjate en la forma: `addMiddleware(InferenceNode::class, ...)`. La Sección 2.3 decía que los nombres de nodo son API pública. Por esto. `InferenceNode` es la base tanto del nodo de chat como del de salida estructurada, así que un solo registro cubre todos los modos.

### Puntos clave

- **Un nodo reanudado se reejecuta desde el principio**, incluidas las llamadas al LLM, con resultados posiblemente distintos.
- `memoize('name', fn)` persiste y reproduce; envuelve todo lo caro o no determinista que preceda a una interrupción.
- `isResuming()` y `getResumePayload()` ramifican según si estás despertando.
- `interruptIf()` mantiene el significado de las aprobaciones y devuelve `null` cuando no se preguntó a nadie.
- La aprobación de herramientas en los agentes se declara en la herramienta y se responde con `submitApprovalDecisions()->run()`; el hilo es el identificador para continuar. `ToolSearchMiddleware` gestiona catálogos grandes.
