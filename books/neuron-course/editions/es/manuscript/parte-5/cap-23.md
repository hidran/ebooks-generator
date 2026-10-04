# Capítulo 23 — Producción

::: {.callout .callout-tip}
[El código de este capítulo]{.callout-title}

La mayor parte de este capítulo es configuración y checklist, pero el oyente de uso de la Sección 23.1 es ejecutable sin Laravel en [`chapters/Ch23`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch23) del repositorio complementario: `usage.php` registra el recuento de tokens de dos inferencias de un proveedor falso, sin modelo y sin clave de API.
:::

## 23.1 Control de costes

### Mide primero

No puedes gestionar lo que no registras. Registra el uso en cada inferencia:

```php
use NeuronAI\Agent\Agent;
use NeuronAI\Agent\Observability\InferenceStop;

class RecordUsage
{
    public function __construct(
        private readonly Agent $agent,
    ) {}

    public function __invoke(InferenceStop $event): void
    {
        $usage = $event->response->message()->getUsage();

        if ($usage === null) {
            return;   // the provider reported none
        }

        try {
            $scope = ThreadScope::of($event->execution?->workflowId);

            AiUsage::create([
                'tenant_id'     => $scope->tenantId,
                'user_id'       => $scope->userId,
                'agent'         => $this->agent::class,
                'model'         => $this->agent->getProvider()->getModel(),
                'input_tokens'  => $usage->inputTokens,
                'output_tokens' => $usage->outputTokens,
                'cached_tokens' => $usage->cachedInputTokens,
            ]);
        } catch (\Throwable $e) {
            report($e);   // a lost row must not become a failed turn
        }
    }
}
```

```php
// NeuronServiceProvider::register()
$this->app->afterResolving(Agent::class, function (Agent $agent): void {
    $agent->subscribe(InferenceStop::class, new RecordUsage($agent));
});
```

La observabilidad en NeuronAI es un despachador de eventos PSR-14 que pertenece a cada instancia de agente (Sección 10.2), e `InferenceStop` se dispara tras cada llamada al modelo, así que esto escribe una fila por inferencia, no por petición. Un agente que recorre tres llamadas a herramienta produce cuatro filas, que es exactamente la granularidad que hace visible a un agente que entra en bucle. Hay dos detalles fáciles de hacer mal: los recuentos de tokens están en el mensaje de la *respuesta del proveedor*, `$event->response->message()->getUsage()` (`$event->message` es el último mensaje *enviado*), y `getUsage()` devuelve `null` cuando un proveedor no informa de nada, así que contempla ese caso.

El oyente no sabe nada de quien llama. El evento lleva el hilo al que está vinculada la ejecución, y el hilo nombra al inquilino y al usuario (Sección 18.3): el camino que sigue el oyente de auditoría de la Sección 19.3. El modelo se le pregunta al agente cuando se dispara el evento, no cuando se construye el oyente: una vez que la factoría de respaldo de la Sección 23.2 puede cambiar de proveedor, un nombre de modelo capturado en la suscripción es una conjetura. Y la escritura va dentro de un `try`. `InferenceStop` se despacha desde dentro de la ejecución, así que una excepción lanzada por un oyente hace fallar el turno; una tabla de uso caída debería costarte una fila, no una respuesta.

Suscríbelo donde se construyen los agentes, para que ningún agente se le escape. Los agentes del Capítulo 18 los construye el contenedor, y un callback `afterResolving()` en `NeuronServiceProvider` se ejecuta para cada subclase de `Agent` que el contenedor resuelve; la copia que crea `for()` conserva el oyente. Un agente construido a mano con `::make()` nunca pasa por el contenedor y no se registra.

Conserva `cached_tokens` aunque hoy lo ignores. La caché de prompts factura esos tokens a una fracción de la tarifa normal, y NeuronAI los informa igual para todos los proveedores: `inputTokens` es el prompt entero, y `cachedInputTokens` es la parte que se leyó de la caché. Si calculas todos los `input_tokens` a tarifa completa, sobreestimas cada acierto de caché; si sumas `cached_tokens` encima, los cuentas dos veces. Calcula el precio de la fila al escribirla, para que un cambio posterior de tarifas no reescriba la historia:

```php
class AiUsage extends Model
{
    // ...

    protected static function booted(): void
    {
        static::creating(function (AiUsage $usage): void {
            // Your own price table in config/neuron.php, per million tokens
            $rate = config("neuron.prices.{$usage->model}")
                ?? throw new LogicException("No price configured for {$usage->model}.");

            $usage->cost = (
                ($usage->input_tokens - $usage->cached_tokens) * $rate['input']
                + $usage->cached_tokens * $rate['cached']
                + $usage->output_tokens * $rate['output']
            ) / 1_000_000;
        });
    }
}
```

Un modelo sin precio lanza una excepción, el oyente la informa, y te enteras de que un proveedor de respaldo ha estado respondiendo sin tarifa antes de que lo diga la factura.

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
        $key = 'classify:' . \hash('xxh128', $text);

        return Cache::remember(
            $key,
            now()->addDays(7),
            fn () => ClassifierAgent::make(workflowId: $key)
                ->structured(new UserMessage($text), Classification::class)
                ->label
        );
    }
}
```

La clave de caché hace también de hilo del agente: un agente no se ejecuta sin uno, y una clasificación no tiene ninguna conversación a la que pertenecer.

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

Un array de configuración no detiene nada. El presupuesto es el código que lee lo gastado y rechaza el turno siguiente:

```php
class Budget
{
    /** Call it before a turn starts: a refusal here stores nothing and spends nothing. */
    public function check(ThreadScope $scope): void
    {
        $today = AiUsage::query()->whereDate('created_at', today());

        $spent = [
            'per_user_daily'   => (clone $today)->where('user_id', $scope->userId)->sum('cost'),
            'per_tenant_daily' => (clone $today)->where('tenant_id', $scope->tenantId)->sum('cost'),
            'global_daily'     => (clone $today)->sum('cost'),
        ];

        foreach (config('neuron.budgets') as $tier => $limit) {
            abort_if($spent[$tier] >= $limit, 429, 'The daily AI budget is used up.');
        }
    }
}
```

Llámalo donde empieza un turno, antes de vincular el agente (`$budget->check(ThreadScope::of($conversation->threadId()))`), y el navegador recibe un 429 sin pregunta almacenada y sin un token gastado. Lo que una comprobación antes del turno no puede hacer es detener un bucle dentro de un turno que ya está en marcha: los límites de ejecución de la Sección 5.9 acotan ese caso.

**Pon además un límite de gasto duro en el proveedor.** La Sección 3.7 lo decía y merece repetirse: los presupuestos a nivel de aplicación dependen de que tu código sea correcto. El tope del proveedor no.

### Puntos clave

- Registra tokens, modelo y agente en cada inferencia, y calcula el precio de la fila al escribirla.
- Tres palancas: menos iteraciones, contexto más pequeño, modelo más barato por paso.
- Cachea las tareas deterministas y las incrustaciones; no las conversaciones.
- Tres niveles de presupuesto, comprobados antes de cada turno, más un tope duro en el proveedor.

## 23.2 Resiliencia

### Límites de tasa

Los proveedores imponen los suyos; tú deberías imponer los tuyos primero, para obtener un trabajo en cola en lugar de una petición fallida:

```php
class RunAgent implements ShouldQueue
{
    public function middleware(): array
    {
        return [new RateLimited('anthropic')];
    }
}
```

```php
// AppServiceProvider::boot()
RateLimiter::for('anthropic', fn () => Limit::perMinute(50));
```

Pasado el límite, el middleware devuelve el trabajo a la cola hasta que la ventana se reabre: el turno llega tarde, no se pierde. No encadenes `->dontRelease()`. Con esa marca un trabajo limitado no se retiene sino que se descarta: Laravel lo elimina sin ejecutarlo y sin error, y el turno del usuario se pierde. Una liberación tiene un coste, que los ajustes de reintento de abajo tienen que prever: Laravel la cuenta como un intento.

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

`timeout` limita la transferencia entera, no la espera del primer byte, y se aplica también a una respuesta transmitida: una respuesta que sigue llegando pasados sesenta segundos se corta a media frase. Sesenta segundos van bien para llamadas sin transmisión. Dale un límite más alto a un agente que transmite respuestas largas, y mantén corto `connectTimeout`: es el que detecta un proveedor caído.

Construye el proveedor en el hook, como aquí, en lugar de llamar a `setHttpClient()` sobre lo que devuelve `AIProvider::driver()`: el gestor entrega a todos los agentes el mismo objeto proveedor (Sección 17.6), así que un cliente fijado en él cambia el tiempo de espera de todos. Si necesitas middleware de Guzzle (un gestor de reintentos, un proxy, la firma de peticiones), `GuzzleHttpClient` está disponible como adaptador opcional en cuanto requieras tú mismo `guzzlehttp/guzzle`, y `CurlHttpClient` acepta `curlOptions` en bruto para proxies y paquetes de CA.

### Reintentos, con la advertencia

```php
class RunAgent implements ShouldQueue
{
    use Queueable;

    public int $tries = 3;

    /** Longer than the longest turn, shorter than the queue's retry_after (360). */
    public int $timeout = 300;

    public array $backoff = [10, 60, 180];

    public function __construct(
        public string $threadId,
        public string $runId,
        public string $message,
    ) {}

    public function handle(SupportAgent $agent): void
    {
        $agent->for($this->threadId)->run(ExecutionRequest::start(
            new AgentStartEvent([new UserMessage($this->message)]),
            runId: $this->runId,
            recoverFailed: true,
        ));
    }
}
```

```php
RunAgent::dispatch($conversation->threadId(), (string) Str::uuid(), $request->input('message'));
```

**La advertencia importa más que la configuración.** Un reintento que vuelve a empezar el turno vuelve a gastar dinero y, por el no determinismo, puede producir un resultado distinto. Reintenta el fallo de *transporte*, no el *razonamiento*.

La distinción en la práctica:

- Límite de tasa o error de conexión antes de cualquier trabajo → seguro reintentar
- Fallo tras tres llamadas a herramientas incluida una escritura → **no reintentes a ciegas**; podrías duplicar la escritura

El ID de ejecución es lo que hace seguro un reintento en ambos casos. Lo acuña el controlador al despachar, de modo que cada entrega del trabajo nombra la misma ejecución, y el trabajo inicia el turno con `ExecutionRequest::start()` porque `chat()` no puede reservar un ID. La primera entrega inicia esa ejecución. Una reentrega (tras una excepción, tras un proceso terminado a la fuerza) la encuentra, y `recoverFailed: true` hace que la termine desde su último paso completado en lugar de empezar de cero: la pregunta no se almacena dos veces, una inferencia ya pagada no se paga otra vez, y una herramienta que ya se ejecutó no se ejecuta de nuevo. Solo se repite el paso que estaba en curso, y por eso una herramienta de escritura sigue necesitando la clave de idempotencia de la Sección 19.2.

Tres relojes tienen que estar en orden para que esto se sostenga, y los valores por defecto de Laravel ponen uno mal:

- **La concesión de la ejecución**: 600 segundos por defecto para un agente, `setLeaseTimeout()`, más larga que el paso individual más largo, una inferencia o un lote de herramientas. Así una ejecución viva nunca se toma por muerta.
- **El `$timeout` del trabajo**: 300, mayor que el turno más largo. Laravel mata un trabajo que lo supera; su ejecución sigue en `running` hasta que expira la concesión, y una entrega posterior la termina.
- **El `retry_after` de la cola**: 360, mayor que `$timeout`. Laravel trae 90, y con eso un segundo proceso toma el trabajo mientras el primero aún está respondiendo: el turno se ejecuta dos veces. Fija `DB_QUEUE_RETRY_AFTER=360` en `.env`, o `REDIS_QUEUE_RETRY_AFTER` en una cola Redis.

Mientras una ejecución sigue concedida a un proceso que murió, el motor rechaza el inicio con `RunInFlightException`. Un trabajo completo la captura y se libera a sí mismo hasta `$e->leaseExpiresAt` en lugar de gastar un intento en ella; la skill `neuron-laravel-integration` de los mantenedores imprime ese gestor bajo «Background Runs», y las ejecuciones en cola de los Capítulos 21 y 22 siguen el mismo patrón.

Una interacción que conviene conocer: las liberaciones del limitador de tasa salen de los mismos tres intentos. Donde el límite es lo bastante estrecho como para liberar un trabajo más de una vez, cuenta los fallos en lugar de las entregas (`retryUntil()` con `$maxExceptions = 3`, como hacen los trabajos de indexación de la Sección 20.2) y elimina `$tries`, que Laravel ignora en cuanto un trabajo define `retryUntil()`.

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
        // add() writes only when the key is missing: the first failure opens a five-minute window
        Cache::add("circuit:{$driver}", 0, now()->addMinutes(5));
        Cache::increment("circuit:{$driver}");
    }
}
```

Cinco fallos en cinco minutos sacan a un proveedor de la cadena, y cuando el contador expira se vuelve a probar. Lo que da esa expiración al contador es `add()`. `increment()` por sí solo nunca la fija: según el almacén de caché, el contador vive entonces para siempre, y un proveedor que falló cinco veces sigue excluido hasta que alguien vacía la caché, o (en el almacén `database` que usa por defecto una aplicación Laravel nueva) nunca llega a crearse, y el circuito nunca se abre.

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

- Limita la tasa antes de que lo haga el proveedor; encola en lugar de fallar, y nunca `dontRelease()`.
- Reintenta los fallos de transporte, no el razonamiento: un ID de ejecución reservado con `recoverFailed: true` deja que una reentrega termine el turno en lugar de repetirlo.
- Tres relojes en orden: concesión por encima del paso más largo, `$timeout` por encima del turno más largo, `retry_after` por encima de `$timeout`.
- Las cadenas de respaldo te mantienen disponible, no igual de bueno; evalúa cada proveedor de la cadena.
- Degrada hacia funcionalidad sin IA en lugar de hacia una página de error.

## 23.3 Observabilidad en producción

### Inspector, con el paquete de Laravel

```bash
composer require inspector-apm/inspector-laravel "inspector-apm/inspector-php:^3.19"
```

```dotenv
INSPECTOR_INGESTION_KEY=...
```

Eso monitoriza tus peticiones HTTP y tus trabajos, y ningún agente. NeuronAI no depende de Inspector y no conecta nada por defecto; los tutoriales antiguos que se detienen en la variable de entorno describen una configuración que ya no existe. La Sección 10.2 explica el mecanismo, y el motivo por el que el comando nombra un segundo paquete: el paquete de Laravel acepta versiones de `inspector-apm/inspector-php` más antiguas de las que necesita el suscriptor, y de la 3.18.1 a la 3.18.3 incluyen un suscriptor escrito para un espacio de nombres de preliminar, que se suscribe sin quejarse y no registra nada. En Laravel, suscribe el oyente donde se construyen los agentes (el callback `afterResolving()` de la Sección 23.1) y pásale la instancia de Inspector que el paquete de Laravel ya posee:

```php
use Inspector\Neuron\V4\InspectorSubscriber;
use NeuronAI\Observability\ObservabilityEvent;

$agent->subscribe(ObservabilityEvent::class, new InspectorSubscriber(app('inspector')));
```

Pasar la instancia del anfitrión es la razón de ser del paquete de Laravel. Los segmentos del agente caen dentro de la transacción que Inspector ya abrió para la petición o el trabajo en cola, lo que correlaciona la traza del agente con las consultas, las llamadas HTTP y el trabajo que la rodean: lo que realmente quieres al diagnosticar un incidente. Sin ello tienes una línea temporal del agente flotando desligada de la petición que la produjo.

Los procesos de cola no necesitan nada más. El suscriptor vacía los datos al final de una ejecución solo cuando abrió la transacción él mismo, y deja una transacción que pertenece al anfitrión (un trabajo monitorizado por el paquete de Laravel) para que la cierre el anfitrión.

El fallo que hay que vigilar es un agente al que nadie suscribió: no produce ningún error ni traza alguna, y un proceso de cola es exactamente donde nadie lo nota. Suscribe en el proveedor de servicios, nunca en los puntos de llamada.

Inspector no es el único backend. La guía de monitorización de los mantenedores documenta Neuron Cloud, que tiene su propio paquete de Laravel, `neuron-core/neuron-cloud-laravel`: el mismo tipo de oyente, suscrito en el mismo sitio. La Sección 10.2 dice qué comprobar antes de contar con ello.

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
Context::add([
    'workflow_id' => $this->workflowId,
    'tenant_id'   => $this->tenantId,
    'agent'       => static::class,
]);
```

Una petición agéntica toca una petición HTTP, varios trabajos en cola, varias llamadas al proveedor y posiblemente una decisión humana días después. Sin un ID de correlación, reconstruir lo que pasó significa adivinar a partir de marcas de tiempo. Usa `Context`, no `Log::withContext()`: Laravel escribe los datos de contexto en cada registro de log y los lleva a los trabajos despachados después, mientras que `withContext()` se queda en el proceso que lo llamó.

### Puntos clave

- Requiere `inspector-laravel` e `inspector-php` en `^3.19`, y suscribe `InspectorSubscriber` en cada agente: por defecto no se monitoriza nada.
- Pasa la instancia de Inspector del paquete de Laravel para que los segmentos del agente se unan a la transacción de la petición o del trabajo.
- Alerta sobre límites de ejecución, fidelidad, coste por petición y cola de aprobaciones.
- Registra formas y metadatos; no el contenido de los prompts.
- Correlaciónalo todo por ID de flujo de trabajo, en `Context` para que siga al trabajo dentro de los trabajos en cola.

## 23.4 Pruebas y CI

### Los tres niveles

**Nivel 1 — pruebas unitarias. Rápidos, gratuitos, deterministas, en cada commit.**

Las herramientas son objetos invocables corrientes (Sección 5.3):

```php
public function test_it_scopes_orders_to_the_tenant(): void
{
    Order::factory()->for($this->tenantA)->create(['number' => 'A-001', 'status' => 'shipped']);
    Order::factory()->for($this->tenantB)->create(['number' => 'B-001', 'status' => 'shipped']);

    $result = (string) (new SearchOrdersTool($this->tenantA->id))(status: 'shipped');

    $this->assertStringContainsString('A-001', $result);
    $this->assertStringNotContainsString('B-001', $result);
}
```

Sin LLM. Sin red. Ambos pedidos están `shipped`, así que el filtro de estado deja pasar a los dos y solo el ámbito del inquilino puede dejar fuera a `B-001`; la primera aserción demuestra que la búsqueda encontró algo. Una prueba que pasa con un resultado vacío no protege nada. Aquí es donde debería vivir la mayor parte de tu lógica relacionada con agentes, y es la razón por la que la Sección 5.3 defendía las clases herramienta.

**Nivel 2 — Pruebas de integración con un proveedor falso.**

```php
$provider = new FakeAIProvider(new AssistantMessage('Your order ships tomorrow.'));

$this->app->instance(
    SupportAgent::class,
    $this->app->make(SupportAgent::class)->setAiProvider($provider),
);

$this->actingAs($user)
    ->postJson("/conversations/{$conversation->id}/messages", ['message' => 'Where is my order?'])
    ->assertOk();

$provider->assertCallCount(1);
```

Testea tu controlador, tu validación, tu autorización, tu serialización, y el agente real, con sus instrucciones y herramientas reales. Solo se sustituye el modelo, a través de la costura de la Sección 18.1: el contenedor entrega un agente cuyo proveedor es el falso, y la copia que crea `for()` lo comparte.

`FakeAIProvider` implementa la misma interfaz que un proveedor real: encola las respuestas que debe devolver, incluidos mensajes de llamada a herramienta para conducir el bucle del agente, y comprueba lo que se le envió con `assertSent()`. El framework ofrece el mismo patrón para las demás costuras (`FakeEmbeddingsProvider`, `FakeVectorStore`, `FakeChannel` para la salida transmitida), de modo que un punto de conexión RAG o una transmisión en cola se pueden probar de la misma forma.

**Nivel 3 — Evaluaciones. Lentas, cuestan dinero, miden la calidad (Capítulo 10).**

```bash
php artisan neuron:evaluate --env=evaluation
```

No `vendor/bin/neuron evaluation`, el comando del Capítulo 10: no arranca Laravel, así que un evaluador que toca un modelo, una facade o el contenedor falla en cada elemento. `neuron:evaluate` es un comando Artisan propio que ejecuta la misma CLI de evaluación dentro de la aplicación arrancada, con el contenedor construyendo los evaluadores. Es una clase corta, que los mantenedores imprimen en la skill `neuron-laravel-integration` (`references/evaluation.md`): créala con `php artisan make:command NeuronEvaluate` y sustituye la clase. Las evaluaciones ejecutan las herramientas reales (aprobar un reembolso reembolsa ese pedido), así que tienen una base de datos propia. `--env=evaluation` selecciona `.env.evaluation`, el comando se niega a ejecutarse cuando ese archivo no se cargó, y un seeder reconstruye los datos que nombran los conjuntos de datos antes de cada ejecución.

### Configuración de la CI

```yaml
jobs:
  test:
    steps:
      - run: composer install --prefer-dist --no-progress
      - run: vendor/bin/phpunit --testsuite=Unit,Feature
      - run: vendor/bin/phpstan analyse

  evals:
    if: github.event_name == 'schedule' || contains(github.event.head_commit.message, '[evals]')
    steps:
      - run: php artisan migrate:fresh --seed --seeder=EvaluationSeeder --env=evaluation
      - run: |
          php artisan neuron:evaluate --env=evaluation --concurrency=5 || true
          php -r '$r = json_decode(file_get_contents("storage/logs/evaluation.json"), true, 512, JSON_THROW_ON_ERROR); exit($r["success_rate"] >= 0.95 ? 0 : 1);'
        env:
          ANTHROPIC_KEY: ${{ secrets.ANTHROPIC_KEY }}
```

Tres reglas de la Sección 10.6, repetidas porque es fácil equivocarse:

**No subordines cada PR a la suite completa de evaluaciones.** Cuesta dinero y es lenta. Cada noche, más bajo demanda con una etiqueta en el commit.

**No falles por un solo elemento.** Fija un umbral de tasa de éxito. En un sistema probabilístico un 95 % de aprobados es una build sana, y tratar un elemento inestable como fallo le enseña al equipo a ignorar del todo la señal. El comando sale con código distinto de cero ante cualquier elemento fallido y no tiene un flag de umbral, así que el paso ignora su código de salida y lee `success_rate` del informe JSON, como hizo la Sección 10.6; aquí `evaluation.php` escribe ese informe en `storage/logs/evaluation.json`.

**Mantén las claves de API fuera de los forks.** Evaluar en las PR de un repositorio público es una forma de donar tu presupuesto a desconocidos.

### Las pruebas de seguridad que deben condicionar los despliegues

Dos de la Parte V, ambos lo bastante deterministas como para fiarse:

```text
public function test_tenant_a_history_never_reaches_tenant_b(): void;      // Section 18.3
public function test_customer_cannot_retrieve_internal_articles(): void;   // Section 20.3
```

Pertenecen al nivel 1 o 2, se ejecutan en cada commit y bloquean la fusión. Ejecútalas en la forma que comprueba lo que llegó al modelo, mediante un proveedor falso: no se llama a ningún modelo, así que el resultado es el mismo en cada ejecución. Están entre las pocas pruebas cercanas a la IA que son a la vez fiables y de consecuencias.

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

**Derecho de supresión.** Un usuario pide ser borrado. Su historial de chat está en tu tabla `chat_messages`: borrable, incluidas las filas archivadas (Sección 18.2). Otros dos lugares guardan sus palabras. Una ejecución en pausa por una aprobación conserva su estado serializado (la pregunta, los argumentos de la herramienta, cualquier texto recuperado) en `workflow_store` hasta que se resuelve; `resetConversation()` sobre el agente vinculado descarta esa ejecución junto con el historial del hilo. La memoria a largo plazo (Sección 4.5) vive en un almacén que `resetConversation()` no toca, así que borra esos documentos por separado. Sus datos dentro de los registros de un proveedor están sujetos a la política de retención de ese proveedor, y por eso importa la retención cero.

**Derecho de acceso.** El historial de chat y cualquier memoria a largo plazo (Sección 4.5) son datos personales que el usuario puede solicitar.

**Decisiones automatizadas.** Si un agente toma una decisión con efectos jurídicos o similarmente significativos sobre alguien, el artículo 22 del RGPD es relevante. Es un argumento fuerte a favor del humano en el circuito para las acciones con consecuencias: el Capítulo 15 es una funcionalidad de cumplimiento además de una de seguridad.

Nada de esto es asesoramiento legal; es la lista de preguntas que llevarle a quien lo dé.

### La traza de auditoría

```php
Schema::create('agent_actions', function (Blueprint $table) {
    $table->id();
    $table->string('thread_id');
    $table->string('call_id');
    $table->foreignId('tenant_id')->constrained();
    $table->foreignId('user_id')->constrained();
    $table->string('tool');
    $table->json('arguments');
    $table->string('outcome');
    $table->text('result')->nullable();
    $table->foreignId('approved_by')->nullable()->constrained('users');
    $table->timestamps();
    $table->unique(['thread_id', 'call_id']);
});
```

Responde a la pregunta que llega tarde o temprano: *«¿por qué el sistema le reembolsó a ese cliente?»*

Esta es la tabla en la que escribe el oyente de `ToolCalled` de la Sección 19.3, una fila por llamada a herramienta, identificada por el hilo y el ID de llamada, de modo que una llamada reproducida actualiza su fila en lugar de añadir otra. Sin ella tienes registros, una traza que puede haber caducado y un encogimiento de hombros. Con ella tienes una fila que nombra al usuario, la herramienta, los argumentos, el resultado, a quien aprobó y la hora. En un entorno regulado esa es la diferencia entre desplegable y no desplegable.

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

- [ ] Filtro de inquilino devuelto por `retrievalScope()`, nunca añadido en el punto de llamada ni sustituido con `setRetrievalScope()` (20.1)
- [ ] Filtros de permisos aplicados **en la recuperación**, nunca después (20.3)
- [ ] `sourceName` estable: IDs de registro, nunca títulos (12.6, 20.2)
- [ ] `indexed_at` seguido; alerta de desfase configurada (20.2)
- [ ] Credenciales de base de datos de solo lectura para las consultas del agente (19.3)
- [ ] La retención cubre `workflow_store` además de `chat_messages`: una ejecución suspendida conserva allí su estado serializado hasta que se resuelve (18.4, 23.5)

### Flujos de trabajo

- [ ] `DatabasePersistence` (o `EloquentPersistence` sobre una tabla propia, o el backend Redis) para cualquier cosa interrumpible, incluidos los agentes con aprobación (18.4, 22.5)
- [ ] Toda llamada al LLM previa a una interrupción envuelta en `memoize()` (15.5)
- [ ] Trabajos de reanudación protegidos con barrera mediante `expectedRunId` y `expectedExecutionAttempt` (22.3)
- [ ] `lockForUpdate()` al resolver aprobaciones (22.3)
- [ ] `expiresAt` en la petición; reanudación sin entrada programada (22.4)
- [ ] Tiempo de espera de la concesión superior al paso silencioso más largo (22.4)
- [ ] Peticiones de interrupción pequeñas, planas y versionadas; propiedades nuevas declaradas con valores por defecto (22.4)
- [ ] Ejecuciones de flujo de trabajo obsoletas descartadas con `abandon()`, nunca borradas a mano; una ejecución de agente muerta se termina, no se abandona (18.4, 22.4)
- [ ] Todo punto de conexión que inicia un turno llama antes a `recoverFailedTurn()` (18.4)

### Operaciones

- [ ] `InspectorSubscriber` suscrito en cada agente y flujo de trabajo, donde se construyen (10.2, 23.3)
- [ ] Uso de tokens registrado por inferencia (23.1)
- [ ] Presupuestos: por usuario, por inquilino, global, comprobados antes de cada turno (23.1)
- [ ] Límites de tasa configurados antes que los del proveedor (23.2)
- [ ] Los turnos en cola inician una ejecución reservada con `recoverFailed: true`, para que una reentrega termine el turno en lugar de repetirlo (23.2)
- [ ] Tres relojes en orden: concesión por encima del paso más largo, `$timeout` del trabajo por encima del turno más largo, `retry_after` de la cola por encima de `$timeout`; Laravel trae 90 (23.2)
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

Veintidós capítulos atrás, el primero dibujó una escalera de cuatro peldaños y preguntó *quién decide qué pasa a continuación*. Todo lo que ha venido después ha sido la maquinaria necesaria para dejar que un modelo responda a esa pregunta con seguridad: herramientas para darle manos, estructura para hacer usable su salida, recuperación para darle conocimiento, flujos de trabajo para darle forma, interrupción para mantener a un humano en la decisión y observabilidad para averiguar qué hizo realmente.

La segunda pregunta de esa lista es con la que hay que quedarse:

> **¿Qué es lo peor que puede hacer tu agente, y qué lo detiene?**

Si puedes responder a eso sobre un sistema que construiste, has entendido este libro.

### Puntos clave

- Recorre la lista sección a sección; cada punto remite a un capítulo.
- Las cinco preguntas son el examen de verdad.
- Si una respuesta es un encogimiento de hombros, esa es la siguiente tarea.
