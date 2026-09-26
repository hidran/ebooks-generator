# Capítulo 23 — Producción

::: {.callout .callout-tip}
[El código de este capítulo]{.callout-title}

La mayor parte de este capítulo es configuración y checklist, pero el oyente de uso de la Sección 23.1 es ejecutable sin Laravel en [`chapters/Ch23`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch23) del repositorio complementario: `usage.php` registra el recuento de tokens de dos inferencias de un proveedor falso, sin modelo y sin clave de API.
:::

## 23.1 Control de costes

### Mide primero

No puedes gestionar lo que no registras. Registra el uso en cada inferencia:

```php
use NeuronAI\Observability\Events\InferenceStop;

class RecordUsage
{
    public function __construct(
        private readonly string $agent,
        private readonly string $model,
        private readonly ?int $tenantId,
        private readonly ?int $userId,
    ) {}

    public function __invoke(InferenceStop $event): void
    {
        $usage = $event->response->message()->getUsage();

        if ($usage === null) {
            return;   // the provider reported none
        }

        AiUsage::create([
            'tenant_id'     => $this->tenantId,
            'user_id'       => $this->userId,
            'agent'         => $this->agent,
            'model'         => $this->model,
            'input_tokens'  => $usage->inputTokens,
            'output_tokens' => $usage->outputTokens,
            'cached_tokens' => $usage->cachedInputTokens,
        ]);
    }
}
```

```php
$agent->subscribe(InferenceStop::class, new RecordUsage(
    agent: $agent::class,
    model: $agent->getProvider()->getModel(),
    tenantId: $user->tenant_id,
    userId: $user->id,
));
```

La observabilidad en NeuronAI es un despachador de eventos PSR-14 que pertenece a cada instancia de agente (Sección 10.2), e `InferenceStop` se dispara tras cada llamada al modelo, así que esto escribe una fila por inferencia, no por petición. Un agente que recorre tres llamadas a herramienta produce cuatro filas, que es exactamente la granularidad que hace visible a un agente que entra en bucle. Hay dos detalles fáciles de hacer mal: los recuentos de tokens están en el mensaje de la *respuesta del proveedor*, `$event->response->message()->getUsage()` (`$event->message` es el último mensaje *enviado*), y `getUsage()` devuelve `null` cuando un proveedor no informa de nada, así que contempla ese caso. Suscribe el oyente donde construyes el agente: en la factoría o en el enlace del contenedor de la Sección 18.1, para que ningún agente se le escape.

Conserva `cached_tokens` aunque hoy lo ignores. La caché de prompts factura esos tokens a una fracción de la tarifa normal, y si ya están incluidos en `input_tokens` o no varía entre proveedores: un informe de costes que no sepa distinguirlos se equivocará en un sentido o en otro.

Cuatro preguntas que esto responde y que ninguna otra cosa responderá:

- ¿Qué agente cuesta más?
- ¿Qué usuario o inquilino cuesta más?
- ¿Está subiendo el coste por petición con el tiempo?
- ¿El cambio de prompt de la semana pasada abarató o encareció las cosas?

### Las tres palancas, revisitadas

La Sección 1.4 las nombró. En producción tienen este aspecto:

**Menos iteraciones.** Descripciones de herramientas más afiladas (5.4), menos herramientas enganchadas (5.8), límites de ejecución más bajos (5.9). Lee las trazas para encontrar los agentes que iteran de más.

**Contexto más pequeño.** Recorte agresivo del historial (4.4), salida compacta de las herramientas (19.1), menos fragmentos de RAG, resumen en las fronteras entre agentes (16.3).

**Modelo más barato por paso.** `AIProvider::driver('ollama')` en el clasificador, el valor por defecto en el redactor (17.6).

### Caché

La palanca de mayor apalancamiento y la más pasada por alto, porque una respuesta cacheada no cuesta nada:

```php
class CachedClassifier
{
    public function classify(string $text): string
    {
        return Cache::remember(
            'classify:' . \hash('xxh128', $text),
            now()->addDays(7),
            fn () => ClassifierAgent::make()
                ->structured(new UserMessage($text), Classification::class)
                ->label
        );
    }
}
```

**Cachea las tareas casi deterministas:** clasificación, extracción de un documento fijo, incrustación de texto no modificado, traducción de una cadena fija.

**No caches las respuestas conversacionales.** La misma pregunta en otra conversación merece otra respuesta.

**El caché de incrustaciones es la mayor victoria en RAG.** El texto que no ha cambiado no necesita volver a embeberse, que es exactamente para lo que servía la guarda `wasChanged('body')` de la Sección 20.2.

### Presupuestos

```php
// config/neuron.php
'budgets' => [
    'per_user_daily'   => env('AI_BUDGET_USER_DAILY', 2.00),
    'per_tenant_daily' => env('AI_BUDGET_TENANT_DAILY', 50.00),
    'global_daily'     => env('AI_BUDGET_GLOBAL_DAILY', 500.00),
],
```

Tres niveles porque fallan de formas distintas: un bucle desbocado para un usuario, una integración mal configurada para un inquilino, un error que afecta a todos. El tope global es tu última línea de defensa.

**Pon además un límite de gasto duro en el proveedor.** La Sección 3.7 lo decía y merece repetirse: los presupuestos a nivel de aplicación dependen de que tu código sea correcto. El tope del proveedor no.

### Puntos clave

- Registra tokens, modelo, agente y duración en cada ejecución.
- Tres palancas: menos iteraciones, contexto más pequeño, modelo más barato por paso.
- Cachea las tareas deterministas y las incrustaciones; no las conversaciones.
- Tres niveles de presupuesto más un tope duro en el proveedor.

## 23.2 Resiliencia

### Límites de tasa

Los proveedores imponen los suyos; tú deberías imponer los tuyos primero, para obtener un trabajo en cola en lugar de una petición fallida:

```php
class RunAgent implements ShouldQueue
{
    public function middleware(): array
    {
        return [
            (new RateLimited('anthropic'))->dontRelease(),
        ];
    }
}
```

```php
// AppServiceProvider::boot()
RateLimiter::for('anthropic', fn () => Limit::perMinute(50));
```

### Tiempos de espera

Todo proveedor habla HTTP a través de la abstracción de cliente propia de NeuronAI, y el predeterminado es `CurlHttpClient`, que no necesita más que ext-curl: Guzzle no es una dependencia. Su tiempo de espera predeterminado es de **300 segundos** por petición. Fija el tuyo deliberadamente, donde se construye el proveedor:

```php
protected function provider(): AIProviderInterface
{
    return new Anthropic(
        key: config('neuron.provider.anthropic.key'),
        model: config('neuron.provider.anthropic.model'),
        httpClient: new CurlHttpClient(timeout: 60.0, connectTimeout: 5.0),
    );
}
```

Un agente que hace cinco llamadas con el tiempo de espera predeterminado puede quedarse colgado veinticinco minutos antes de fallar, ocupando un proceso todo ese tiempo.

Pasa el cliente al constructor en lugar de llamar a `setHttpClient()` después: el proveedor configura su URL base y sus cabeceras de autenticación en el cliente con el que se construye, y un cliente cambiado más tarde llega sin ellas. Si necesitas middleware de Guzzle (un gestor de reintentos, un proxy, la firma de peticiones), `GuzzleHttpClient` está disponible como adaptador opcional en cuanto requieras tú mismo `guzzlehttp/guzzle`, y `CurlHttpClient` acepta `curlOptions` en bruto para proxies y paquetes de CA.

### Reintentos, con la advertencia

```php
class RunAgent implements ShouldQueue
{
    public int $tries = 3;
    public array $backoff = [10, 60, 180];

    public function retryUntil(): DateTime
    {
        return now()->addMinutes(15);
    }
}
```

**La advertencia importa más que la configuración.** Reintentar la ejecución de un agente vuelve a gastar dinero y, por el no determinismo, puede producir un resultado distinto. Reintenta el fallo de *transporte*, no el *razonamiento*.

La distinción en la práctica:

- Límite de tasa o error de conexión antes de cualquier trabajo → seguro reintentar
- Fallo tras tres llamadas a herramientas incluida una escritura → **no reintentes a ciegas**; podrías duplicar la escritura

Por eso la Sección 21.5 ponía `$tries = 1` en el trabajo del flujo de trabajo. Para el trabajo de agentes, la idempotencia (19.2) más un reintento deliberado ganan a un recuento generoso de reintentos.

### Respaldo entre proveedores

El rédito más concreto de la arquitectura de interfaces:

```php
class ResilientProviderFactory
{
    private const CHAIN = ['anthropic', 'openai', 'gemini'];

    public function make(): AIProviderInterface
    {
        foreach (self::CHAIN as $driver) {
            if (! $this->circuitOpen($driver)) {
                return AIProvider::driver($driver);
            }
        }

        throw new NoProviderAvailable('All configured providers are unavailable.');
    }

    private function circuitOpen(string $driver): bool
    {
        return Cache::get("circuit:{$driver}", 0) >= 5;
    }

    public function recordFailure(string $driver): void
    {
        Cache::increment("circuit:{$driver}");
        Cache::put("circuit:{$driver}:reset", true, now()->addMinutes(5));
    }
}
```

**Dos advertencias, para que esto no parezca una comida gratis:**

**La calidad varía entre proveedores.** Un prompt afinado para un modelo puede comportarse notablemente peor en otro. El respaldo te mantiene disponible; no te mantiene igual de bueno. Ejecuta tus evaluaciones (Capítulo 10) contra cada proveedor de la cadena para saber a qué estás degradando.

**Algunas funcionalidades no son portables.** Las herramientas de proveedor (5.12) sencillamente desaparecen. Si un agente depende de una, no tiene respaldo.

### Degradar con elegancia

A veces la respuesta correcta no es otro proveedor:

```php
try {
    return $this->agent->chat(new UserMessage($question))->getMessage()?->getContent() ?? '';
} catch (\Throwable $e) {
    \Log::error('Agent unavailable', ['exception' => $e]);

    return $this->fallbackSearch($question);   // plain keyword search over the KB
}
```

El resultado de una búsqueda por palabras clave gana a una página de error. Los usuarios notan las caídas; rara vez notan una respuesta ligeramente peor.

### Puntos clave

- Limita la tasa antes de que lo haga el proveedor; encola en lugar de fallar.
- Reintenta los fallos de transporte, no el razonamiento: las escrituras pueden duplicarse.
- Las cadenas de respaldo te mantienen disponible, no igual de bueno; evalúa cada proveedor de la cadena.
- Degrada hacia funcionalidad sin IA en lugar de hacia una página de error.

## 23.3 Observabilidad en producción

### Inspector, con el paquete de Laravel

```bash
composer require inspector-apm/inspector-laravel
```

```dotenv
INSPECTOR_INGESTION_KEY=...
```

Eso monitoriza tus peticiones HTTP y tus trabajos, y ningún agente. NeuronAI no depende de Inspector y no conecta nada por defecto; los tutoriales antiguos que se detienen en la variable de entorno describen una configuración que ya no existe. La Sección 10.2 explica el mecanismo. En Laravel, suscribe el oyente donde se construyen los agentes y pásale la instancia de Inspector que el paquete de Laravel ya posee:

```php
use Inspector\Neuron\V4\InspectorSubscriber;
use NeuronAI\Observability\ObservabilityEvent;

$agent->subscribe(ObservabilityEvent::class, new InspectorSubscriber(app('inspector')));
```

Pasar la instancia del anfitrión es la razón de ser del paquete de Laravel. Los segmentos del agente caen dentro de la transacción que Inspector ya abrió para la petición o el trabajo en cola, lo que correlaciona la traza del agente con las consultas, las llamadas HTTP y el trabajo que la rodean: lo que realmente quieres al diagnosticar un incidente. Sin ello tienes una línea temporal del agente flotando desligada de la petición que la produjo.

Los procesos de cola no necesitan nada más. El suscriptor vacía los datos al final de una ejecución solo cuando abrió la transacción él mismo, y deja una transacción que pertenece al anfitrión (un trabajo monitorizado por el paquete de Laravel) para que la cierre el anfitrión. El paquete de Laravel acepta versiones de `inspector-apm/inspector-php` más antiguas de las que necesita el suscriptor: comprueba que Composer haya resuelto la 3.18.1 o posterior, la primera que incluye el espacio de nombres `Inspector\Neuron\V4`, y requiérela explícitamente si no es así.

El fallo que hay que vigilar es un agente al que nadie suscribió: no produce ningún error ni traza alguna, y un proceso de cola es exactamente donde nadie lo nota. Suscribe en la factoría o en el enlace del contenedor (Sección 18.1), nunca en los puntos de llamada.

### Sobre qué alertar

Cuatro señales, y ninguna de ellas es «ha ocurrido una excepción»:

**Límites de ejecución de herramientas superados.** La Sección 5.9 decía que esto es un diagnóstico sobre el diseño de las herramientas. Un pico significa que una descripción ha dejado de funcionar, a menudo porque los datos subyacentes cambiaron de forma.

**Puntuación de fidelidad cayendo.** De tu suite de evaluación (10.5), ejecutada cada noche. Una caída significa que la calidad de la recuperación se ha degradado, normalmente porque el contenido cambió y el índice no siguió el ritmo.

**Coste por petición subiendo.** Bucles alargándose, contexto creciendo, o un cambio de prompt que hizo al modelo más locuaz.

**Cola de aprobaciones creciendo.** No es un problema de código, es un problema de proceso, y tu panel lo hará aflorar antes de que nadie se queje.

### Qué registrar y qué no

**Registra:** clase del agente, proveedor, modelo, recuentos de tokens, duración, nombres de las herramientas, *forma* de los argumentos de las herramientas, resultado, ID de flujo de trabajo, IDs de usuario y inquilino.

**No registres por defecto:** prompts completos, respuestas completas, *valores* de los argumentos de las herramientas, contenido de los documentos recuperados.

La Sección 3.7 hacía este punto; merece repetirse aquí. Los prompts contienen lo que sea que hayan escrito los usuarios: nombres, direcciones, números de pedido, ocasionalmente datos de pago. Registrar prompts completos a escala crea un problema de cumplimiento mucho más difícil de deshacer que de evitar.

Cuando necesites contenido para depurar, ponlo detrás de una bandera explícita con retención corta, y nunca activo por defecto.

### El ID de correlación

```php
Log::withContext([
    'workflow_id' => $this->workflowId,
    'tenant_id'   => $this->tenantId,
    'agent'       => static::class,
]);
```

Una petición agéntica toca una petición HTTP, varios trabajos en cola, varias llamadas al proveedor y posiblemente una decisión humana días después. Sin un ID de correlación, reconstruir lo que pasó significa adivinar a partir de marcas de tiempo.

### Puntos clave

- Requiere `inspector-laravel` y suscribe `InspectorSubscriber` en cada agente: por defecto no se monitoriza nada.
- Pasa la instancia de Inspector del paquete de Laravel para que los segmentos del agente se unan a la transacción de la petición o del trabajo.
- Alerta sobre límites de ejecución, fidelidad, coste por petición y cola de aprobaciones.
- Registra formas y metadatos; no el contenido de los prompts.
- Correlaciónalo todo por ID de flujo de trabajo.

## 23.4 Pruebas y CI

### Los tres niveles

**Nivel 1 — pruebas unitarias. Rápidos, gratuitos, deterministas, en cada commit.**

Las herramientas son objetos invocables corrientes (Sección 5.3):

```php
public function test_it_scopes_orders_to_the_tenant(): void
{
    $tool = new SearchOrdersTool($this->tenantA);

    Order::factory()->for($this->tenantB)->create(['number' => 'B-001']);

    $result = $tool(status: 'shipped');

    $this->assertStringNotContainsString('B-001', $result);
}
```

Sin LLM. Sin red. Aquí es donde debería vivir la mayor parte de tu lógica relacionada con agentes, y es la razón por la que la Sección 5.3 defendía las clases herramienta.

**Nivel 2 — Pruebas de integración con un proveedor falso.**

```php
$provider = new FakeAIProvider(new AssistantMessage('Your order ships tomorrow.'));

$this->app->resolving(SupportAgent::class, fn (SupportAgent $agent) => $agent->setAiProvider($provider));

$this->postJson('/api/chat', ['message' => 'Where is my order?'])
     ->assertOk()
     ->assertJsonStructure(['answer']);

$provider->assertCallCount(1);
```

Testea tu controlador, tu validación, tu autorización, tu serialización, y el agente real, con sus instrucciones y herramientas reales. Solo se sustituye el modelo.

`FakeAIProvider` implementa la misma interfaz que un proveedor real: encola las respuestas que debe devolver, incluidos mensajes de llamada a herramienta para conducir el bucle del agente, y comprueba lo que se le envió con `assertSent()`. El framework ofrece el mismo patrón para las demás costuras (`FakeEmbeddingsProvider`, `FakeVectorStore`, `FakeChannel` para la salida transmitida), de modo que un punto de conexión RAG o una transmisión en cola se pueden probar de la misma forma.

**Nivel 3 — Evaluaciones. Lentas, cuestan dinero, miden la calidad (Capítulo 10).**

```bash
vendor/bin/neuron evaluation --path=evaluators
```

### Configuración de la CI

```yaml
jobs:
  test:
    steps:
      - run: composer install --prefer-dist --no-progress
      - run: vendor/bin/phpunit --testsuite=unit,integration
      - run: vendor/bin/phpstan analyse

  evals:
    if: github.event_name == 'schedule' || contains(github.event.head_commit.message, '[evals]')
    steps:
      - run: vendor/bin/neuron evaluation --path=evaluators --concurrency=5
        env:
          ANTHROPIC_KEY: ${{ secrets.ANTHROPIC_KEY }}
```

Tres reglas de la Sección 10.6, repetidas porque es fácil equivocarse:

**No subordines cada PR a la suite completa de evaluaciones.** Cuesta dinero y es lenta. Cada noche, más bajo demanda con una etiqueta en el commit.

**No falles por un solo elemento.** Fija un umbral de tasa de éxito. En un sistema probabilístico un 95 % de aprobados es una build sana, y tratar un elemento inestable como fallo le enseña al equipo a ignorar del todo la señal.

**Mantén las claves de API fuera de los forks.** Evaluar en las PR de un repositorio público es una forma de donar tu presupuesto a desconocidos.

### Las pruebas de seguridad que deben condicionar los despliegues

Dos de la Parte V, ambos lo bastante deterministas como para fiarse:

```text
public function test_tenant_isolation(): void;                   // Section 18.3
public function test_restricted_articles_never_surface(): void;  // Section 20.3
```

Pertenecen al nivel 1 o 2, se ejecutan en cada commit y bloquean la fusión. Están entre las pocas pruebas cercanas a la IA que son a la vez fiables y de consecuencias.

### Puntos clave

- Tres niveles: unitarios (cada commit), integración con dobles (cada commit), evaluaciones (cada noche).
- Las herramientas son testeables sin LLM: pon ahí la lógica.
- Umbral sobre la tasa de éxito, no aprobado/fallido por elemento.
- El aislamiento entre inquilinos y la recuperación filtrada por permisos condicionan cada despliegue.

## 23.5 Seguridad y privacidad

### El modelo por capas, ensamblado

| Capa | Mecanismo | Sección |
|---|---|---|
| Capacidad | Registra solo las herramientas que este usuario puede usar | 5.1 |
| Visibilidad | `visible()` desde las policies | 5.10, 19.3 |
| Autorización | `Gate::forUser()` dentro de la herramienta | 19.3 |
| Aprobación | `approvalPolicy()` / `requireApproval()` en las herramientas con consecuencias | 15.5, 22.5 |
| Ámbito de datos | Filtros de inquilino en herramientas y recuperación | 18.3, 20.3 |
| Privilegio | Credenciales de base de datos de solo lectura | 19.3 |
| Auditoría | Una fila por llamada a herramienta con consecuencias | 19.3 |

**Cada capa es independiente.** Un error en una no derrota a las demás, que es todo el sentido de la defensa en profundidad y la respuesta a «¿no basta con la visibilidad?».

### Inyección de prompts, una vez más

El principio de la Sección 19.3, que es la tesis de seguridad de todo este libro:

> No intentes instruir al modelo para que no haga algo que tiene la capacidad de hacer. Quítale la capacidad.

Las instrucciones compiten con el texto inyectado y a veces pierden. Una herramienta ausente no puede invocarla ningún prompt, por astuto que sea.

El texto no fiable entra por más sitios de los que la gente espera: mensajes de usuario, descripciones de productos, tickets de soporte, documentos subidos, contenido recuperado por RAG, respuestas de APIs de terceros y salida de herramientas MCP (9.4). Trátalo todo como influido por un atacante.

### Flujo de datos

Tres preguntas que responder por escrito antes del lanzamiento:

**¿Qué sale de tu infraestructura?** Cada prompt va al proveedor. Eso incluye los documentos recuperados y los resultados de las herramientas. Si la dirección de un cliente aparece en el resultado de una herramienta, fue al proveedor.

**¿Adónde va?** Las regiones de los proveedores difieren, y algunos ofrecen procesamiento solo en la UE o en la región. Para clientes europeos esto suele ser un requisito contractual más que una preferencia.

**¿Qué se conserva?** Los proveedores publican políticas de retención; los acuerdos empresariales a menudo incluyen opciones de retención cero. Léelas y anota lo que encuentres.

### Puntos de contacto con el RGPD

Cinco prácticos, enunciados como requisitos de ingeniería:

**Base jurídica.** Enviar datos personales a un encargado del tratamiento externo requiere una. Es una determinación jurídica, no de ingeniería: implica a asesoría legal en lugar de decidirlo en la planificación del sprint.

**Acuerdo de tratamiento de datos.** Con cada proveedor que uses.

**Derecho de supresión.** Un usuario pide ser borrado. Su historial de chat está en tu tabla `chat_messages`: borrable. Sus datos dentro de los registros de un proveedor están sujetos a la política de retención de ese proveedor, y por eso importa la retención cero.

**Derecho de acceso.** El historial de chat y cualquier memoria a largo plazo (Sección 4.5) son datos personales que el usuario puede solicitar.

**Decisiones automatizadas.** Si un agente toma una decisión con efectos jurídicos o similarmente significativos sobre alguien, el artículo 22 del RGPD es relevante. Es un argumento fuerte a favor del humano en el circuito para las acciones con consecuencias: el Capítulo 15 es una funcionalidad de cumplimiento además de una de seguridad.

Nada de esto es asesoramiento legal; es la lista de preguntas que llevarle a quien lo dé.

### La traza de auditoría

```php
Schema::create('agent_actions', function (Blueprint $table) {
    $table->id();
    $table->foreignId('user_id')->nullable()->constrained();
    $table->foreignId('tenant_id')->constrained();
    $table->string('agent');
    $table->string('tool');
    $table->json('arguments');
    $table->text('result')->nullable();
    $table->string('workflow_id')->nullable();
    $table->boolean('approved')->default(false);
    $table->foreignId('approved_by')->nullable()->constrained('users');
    $table->timestamps();
});
```

Responde a la pregunta que llega tarde o temprano: *«¿por qué el sistema le reembolsó a ese cliente?»*

Sin ella tienes registros, una traza que puede haber caducado y un encogimiento de hombros. Con ella tienes una fila que nombra al usuario, la herramienta, los argumentos, a quien aprobó y la hora. En un entorno regulado esa es la diferencia entre desplegable y no desplegable.

### Puntos clave

- Siete capas independientes; un error en una no derrota al resto.
- Quita la capacidad en lugar de instruir en contra.
- Escribe qué sale, adónde va y qué se conserva.
- El humano en el circuito es una funcionalidad de cumplimiento según el artículo 22, no solo de seguridad.
- Audita cada acción con consecuencias en una tabla consultable.

## 23.6 La lista de comprobación de despliegue

### Configuración

- [ ] Versiones de modelo **fijadas explícitamente**, no alias móviles (1.5)
- [ ] Proveedor fijado por entorno; modelo de incrustaciones **idéntico en todas partes** (12.4, 17.2)
- [ ] Ventana de contexto derivada del proveedor configurado, no escrita a fuego (4.4)
- [ ] Límite de gasto duro fijado en el proveedor (3.7)
- [ ] Claves de API separadas por entorno
- [ ] Escaneo de secretos en CI

### Agentes y herramientas

- [ ] Toda herramienta de escritura: `setMaxRuns(1)`, guarda de idempotencia, transacción (5.9, 19.2)
- [ ] Toda herramienta: conjunto de resultados acotado, selección explícita de columnas, salida compacta (19.1)
- [ ] Toda herramienta: una frase explícita para el caso vacío (5.9)
- [ ] Visibilidad de herramientas calculada a partir de las policies del actor (5.10, 19.3)
- [ ] `Gate::forUser()` dentro de las herramientas que tocan registros concretos (19.3)
- [ ] Gestor de errores que devuelve instrucciones, no trazas de pila (5.11)
- [ ] Juegos de herramientas filtrados con `only()`, nunca con `exclude()` (5.8)

### Datos

- [ ] Filtro de inquilino aplicado dentro de `vectorStore()`, no en el punto de llamada (20.1)
- [ ] Filtros de permisos aplicados **en la recuperación**, nunca después (20.3)
- [ ] `sourceName` estable: IDs de registro, nunca títulos (12.6, 20.2)
- [ ] `indexed_at` seguido; alerta de desfase configurada (20.2)
- [ ] Credenciales de base de datos de solo lectura para las consultas del agente (19.3)

### Flujos de trabajo

- [ ] `EloquentPersistence(WorkflowStore::class)` (o el backend de base de datos o Redis) para cualquier cosa interrumpible, incluidos los agentes con aprobación (18.4, 22.5)
- [ ] Toda llamada al LLM previa a una interrupción envuelta en `memoize()` (15.5)
- [ ] Trabajos de reanudación protegidos con barrera mediante `expectedRunId` y `expectedExecutionAttempt` (22.3)
- [ ] `lockForUpdate()` al resolver aprobaciones (22.3)
- [ ] `expiresAt` en la petición; reanudación sin entrada programada (22.4)
- [ ] Tiempo de espera de la concesión superior al paso silencioso más largo (22.4)
- [ ] Peticiones de interrupción pequeñas, planas y versionadas; propiedades nuevas declaradas con valores por defecto (22.4)
- [ ] Ejecuciones obsoletas abandonadas mediante `abandonRun()`, nunca borradas a mano (22.4)

### Operaciones

- [ ] `InspectorSubscriber` suscrito en cada agente y flujo de trabajo, en la factoría (10.2, 23.3)
- [ ] Uso de tokens registrado por ejecución (23.1)
- [ ] Presupuestos: por usuario, por inquilino, global (23.1)
- [ ] Límites de tasa configurados antes que los del proveedor (23.2)
- [ ] `$tries = 1` en los trabajos de agentes, o idempotencia demostrada (21.5, 23.2)
- [ ] Tiempos de espera fijados en PHP, FPM, proxy y el cliente HTTP del proveedor (21.2, 23.2)
- [ ] Transmisión verificada de extremo a extremo con `curl -N` a través de todo la pila (21.2)
- [ ] Canales de difusión autorizados por inquilino; el navegador se suscribe antes de que empiece la ejecución (21.5)

### Calidad y seguridad

- [ ] Suite de evaluación con un conjunto de datos construido a partir de preguntas reales (10.4)
- [ ] `FaithfulnessJudge` en todo agente RAG (10.5)
- [ ] Prueba de aislamiento entre inquilinos condicionando los despliegues (18.3)
- [ ] Prueba de recuperación filtrada por permisos condicionando los despliegues (20.3)
- [ ] Tabla de auditoría poblada por toda herramienta con consecuencias (19.3, 23.5)
- [ ] Contenido de los prompts **no** registrado por defecto (3.7, 23.3)
- [ ] Acuerdos de tratamiento de datos firmados; retención entendida (23.5)

### Las cinco preguntas que responder en voz alta

Antes del lanzamiento, debes poder responder a estas sin consultar nada:

1. **¿Cuánto cuesta este agente por petición, y a qué volumen eso se convierte en un problema?**
2. **¿Qué es lo peor que puede hacer, y qué lo detiene?**
3. **¿Cómo averiguaría qué hizo, dentro de tres semanas?**
4. **¿Qué pasa cuando el proveedor está caído?**
5. **¿Qué datos salen de mi infraestructura, y adónde van?**

Si alguna respuesta es un encogimiento de hombros, ese es el siguiente trabajo.

### Cierre de la Parte V

Veintitrés capítulos atrás, el primero dibujó una escalera de cuatro peldaños y preguntó *quién decide qué pasa a continuación*. Todo lo que ha venido después ha sido la maquinaria necesaria para dejar que un modelo responda a esa pregunta con seguridad: herramientas para darle manos, estructura para hacer usable su salida, recuperación para darle conocimiento, flujos de trabajo para darle forma, interrupción para mantener a un humano en la decisión y observabilidad para averiguar qué hizo realmente.

La segunda pregunta de esa lista es con la que hay que quedarse:

> **¿Qué es lo peor que puede hacer tu agente, y qué lo detiene?**

Si puedes responder a eso sobre un sistema que construiste, has entendido este libro.

### Puntos clave

- Recorre la lista sección a sección; cada punto remite a un capítulo.
- Las cinco preguntas son el examen de verdad.
- Si una respuesta es un encogimiento de hombros, esa es la siguiente tarea.
