# Capítulo 14 — Bucles, ramas y estado

::: {.callout .callout-tip}
[El código de este capítulo]{.callout-title}

La versión ejecutable de cada listado que sigue está en [`chapters/Ch14`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch14), en el repositorio complementario. Clónalo, ejecuta `composer install` y los ejemplos funcionan contra un Ollama local sin ninguna clave de API.
:::

## 14.1 Bucles

### Un bucle es un tipo de retorno

```php
class NodeOne extends Node
{
    public function __invoke(FirstEvent $event, WorkflowState $state): FirstEvent|SecondEvent
    {
        echo "\n- ".$event->firstMsg;

        if (rand(0, 1) === 1) {
            // Returning FirstEvent triggers another execution of NodeOne
            return new FirstEvent("Running a loop on NodeOne");
        }

        return new SecondEvent("NodeOne complete, move forward");
    }
}
```

El nodo consume `FirstEvent` y también puede *devolver* `FirstEvent`. Devolverlo lo dispara de nuevo a sí mismo.

Salida:

```
- Handling StartEvent
- InitialNode complete
- Running a loop on NodeOne
- Running a loop on NodeOne
- NodeOne complete, move forward
- NodeTwo complete
```

### La regla que no debes olvidar

> Tienes que declarar **todos los eventos de retorno posibles** en la firma del método para que el Workflow pueda construir la cadena de ejecución.

`FirstEvent|SecondEvent`. La unión no es decoración. PHP la hace cumplir: devuelve un evento que no está en la firma y el nodo muere con un `TypeError` —`Return value must be of type FirstEvent, SecondEvent returned`— en el único camino que lo devuelve, que suele ser la rama rara que nadie ejercitó en las pruebas.

El arreglo tentador es ampliar el tipo de retorno a un simple `Event`. Funciona, y te cuesta justo aquello de lo que trataba el Capítulo 13: la firma ya no dice adónde puede ir el flujo, así que tampoco lo sabe un lector, ni `export()`, que dibuja el grafo a partir de esos mismos tipos de retorno.

Este es el error número uno de los flujos de trabajo, y la causa es siempre la misma: un tipo de unión que alguien olvidó ampliar tras añadir una rama.

### Bucle hacia cualquier sitio

> Puedes crear un bucle desde cualquier nodo hacia cualquier otro nodo definiendo los eventos de entrada y retorno apropiados. Un nodo incluso puede devolver un `StartEvent` para saltar directamente al primer nodo del flujo de trabajo.

Devolver `StartEvent` reinicia el flujo desde el principio, dentro de la misma ejecución, así que el estado conserva todo lo escrito hasta ese momento. El `run/loop.php` del repositorio complementario está construido exactamente sobre esto: el revisor devuelve `StartEvent` ante un rechazo, y el nodo redactor que lo consume lee del estado la realimentación del revisor y produce el siguiente borrador.

### La guarda que debes escribir tú

El framework no detendrá un bucle infinito. Si tu condición nunca se vuelve falsa, el flujo de trabajo se ejecuta para siempre.

Usa el estado como contador:

```php
class ReviewNode extends Node
{
    private const MAX_ATTEMPTS = 3;

    public function __invoke(DraftReady $event, WorkflowState $state): DraftReady|ArticleApproved
    {
        $attempts = (int) $state->get('review_attempts', 0);

        $verdict = $this->memoize('verdict', fn (): Verdict => ReviewerAgent::make()
            ->structured(new UserMessage($event->draft), Verdict::class));

        if ($verdict->approved) {
            return new ArticleApproved($event->draft);
        }

        if ($attempts + 1 >= self::MAX_ATTEMPTS) {
            $state->set('escalate_reason', 'review_limit_reached');

            return new ArticleApproved($event->draft); // or an EscalationEvent
        }

        $state->set('review_attempts', $attempts + 1);
        $state->set('last_feedback', $verdict->feedback);

        return new DraftReady($event->draft);
    }
}
```

Tres cosas que esto demuestra más allá del contador:

**Cada iteración es su propio paso duradero.** El motor numera los pasos a medida que recorre el grafo, así que la tercera pasada por `ReviewNode` es un paso distinto de la primera, con el contador del estado confirmado junto a él. Una ejecución que se cae en la tercera revisión y se recupera reproduce las dos primeras desde el almacén y se reanuda en la tercera; y el `memoize()` que envuelve la llamada al revisor (Sección 13.5) está acotado a esa iteración, así que el veredicto ya pagado en una pasada concreta nunca se pide dos veces.

**Cada iteración del bucle cuesta llamadas al LLM.** Esto es la Sección 1.4 otra vez. Un bucle de revisión sin límite es una factura sin límite.

**Ten un plan para cuando se alcance el límite.** Escalar a un humano gana a publicar en silencio el tercer borrador. Ese es el puente natural hacia el Capítulo 15.

### Los bucles son donde los sistemas agénticos se ganan el sueldo

Un bucle con un LLM dentro es *refinamiento iterativo*: redactar, criticar, revisar, repetir hasta que sea suficientemente bueno. Ese patrón —redactor más crítico— es una de las formas multiagente de mayor valor, y es un flujo de trabajo de tres nodos con un tipo de retorno de unión.

### Puntos clave

- Un bucle es un nodo que devuelve un evento que vuelve a disparar un nodo anterior.
- **Declara todos los tipos de retorno posibles en la unión**: el error de flujo de trabajo más común.
- Devolver `StartEvent` reinicia todo el flujo de trabajo.
- El framework no acota los bucles; cuenta en el estado y planifica el límite.
- Cada iteración es un paso duradero independiente; memoiza la llamada al LLM dentro de él.

## 14.2 Ramas, secuenciales y paralelas

### Ramificación condicional

El mismo mecanismo que un bucle —un tipo de retorno de unión—, pero las alternativas llevan a nodos distintos:

```php
class InitialNode extends Node
{
    public function __invoke(StartEvent $event, WorkflowState $state): BranchA1Event|BranchB1Event
    {
        if ($this->shouldTakeA($state)) {
            return new BranchA1Event('Going down branch A');
        }

        return new BranchB1Event('Going down branch B');
    }
}
```

Cada rama continúa entonces por sus propios nodos y finalmente alcanza `StopEvent`, o converge de vuelta en un tipo de evento compartido.

**Un truco de convergencia que conviene conocer:** para reunir dos ramas, haz que el último nodo de cada una devuelva el *mismo* tipo de evento. Sea cual sea la rama que se ejecutó, el mismo nodo aguas abajo lo recoge. Así se construyen formas de rombo sin ninguna sintaxis de unión.

::: {.callout .callout-warning}
[No copies el nombre de clase de los documentos]{.callout-title}

El ejemplo de ramificación de la documentación nombra la clase `BrancheA1Event`, con una `e` de más. Apéndice A, punto 33.
:::

### Ramas paralelas

La ramificación condicional elige un camino. La paralela se bifurca en varios, cada uno ejecutándose hasta su propio final, y une los resultados.

La bifurcación devuelve un `ParallelEvent`. Dale una subclase propia, porque el nodo de unión se encamina precisamente por esa clase —la misma regla de un-evento-un-nodo de siempre—, y una subclase con nombre permite que un flujo de trabajo contenga más de una bifurcación:

```php
use NeuronAI\Workflow\Events\ParallelEvent;

class DocumentProcessingStarted extends ParallelEvent
{
}

class DocumentProcessing extends Node
{
    public function __invoke(StartEvent $event, WorkflowState $state): DocumentProcessingStarted
    {
        return new DocumentProcessingStarted([
            'text'  => new TextProcessEvent(),
            'image' => new ImageProcessEvent(),
        ]);
    }
}
```

Cada rama es una **clave con nombre** que apunta al primer evento de esa rama. Los nombres son obligatorios: una lista simple se rechaza, porque el nombre se convierte en la identidad de la rama. Los nodos que gestionan esos eventos, y todo lo que va aguas abajo en cada rama, se registran en el flujo de trabajo con normalidad:

```php
class MyWorkflow extends Workflow
{
    protected function nodes(): array
    {
        return [
            new DocumentProcessing(),

            // "text" branch
            new DescriptionGenerationNode(),
            new TextRefactorNode(),

            // "image" branch
            new ImageProcessNode(),
            new AddWatermarkNode(),

            new MergeNode(),
        ];
    }
}
```

### Devolver resultados desde una rama

Cada rama termina cuando su último nodo devuelve un `StopEvent`, y **el `StopEvent` lleva el resultado**:

```php
class TextRefactorNode extends Node
{
    public function __invoke(TextProcessEvent $event, WorkflowState $state): StopEvent
    {
        // do the work
        return new StopEvent(result: $refinedText);
    }
}
```

Una vez completadas todas las ramas, la misma instancia de `DocumentProcessingStarted`, que ahora contiene el resultado de cada rama, se encamina al nodo que la acepta. Ese nodo es el punto de fusión, y lee cada resultado por nombre:

```php
class MergeNode extends Node
{
    public function __invoke(DocumentProcessingStarted $event, WorkflowState $state): StopEvent
    {
        $textResult  = $event->getResult('text');
        $imageResult = $event->getResult('image');

        // Combine, persist, return a final event...
        return new StopEvent();
    }
}
```

### La regla de aislamiento: la parte importante

> Cada rama recibe una **copia aislada** del estado del flujo de trabajo. Las ramas parten de la misma instantánea, pero las mutaciones dentro de una rama no se propagan a las ramas hermanas ni al flujo de trabajo principal. **La única forma de devolver datos es a través del resultado del `StopEvent`.**

Esto es intencionado, y el razonamiento es sólido: con estado mutable compartido entre ramas concurrentes obtienes una condición de carrera y, después, una sesión de depuración del tipo «¿quién escribió este valor?» que no le gusta a nadie.

La consecuencia práctica, y es con lo que todo el mundo tropieza: **una rama que escribe en `$state` está escribiendo en una copia que se descartará.** Si quieres sacar datos de una rama, van en el resultado del `StopEvent`. Punto.

### Paralelo no es concurrente hasta que tú lo digas

El ejecutor por defecto ejecuta las ramas **una tras otra**. El aislamiento, los resultados con nombre y la fusión funcionan, pero el tiempo transcurrido es la suma de las ramas. Para concurrencia real, cambia el ejecutor:

```php
use NeuronAI\Workflow\Executor\AsyncExecutor;

$state = MyWorkflow::make()
    ->setExecutor(new AsyncExecutor())
    ->run();
```

`AsyncExecutor` ejecuta cada rama en una fibra de Amp y necesita `amphp/amp` instalado: NeuronAI no lo exige, y sin él la bifurcación falla con `Call to undefined function Amp\async()`. Las fibras solo se solapan mientras una de ellas espera E/S, así que para las ramas que llaman a un modelo el proveedor también necesita el `AmpHttpClient` no bloqueante (de `amphp/http-client`), configurado con `setHttpClient()`. Con ambos, dos llamadas al modelo terminan en el tiempo de la más lenta. Solo con el ejecutor, siguen haciendo cola una detrás de otra.

Los pasos de las ramas son duraderos como cualquier otro: cada nodo dentro de cada rama se confirma como su propio paso, así que una ejecución recuperada no rehace las ramas que ya terminaron. Qué ocurre cuando una rama se pausa a la espera de un humano es asunto del Capítulo 15; en resumen, las ramas se pausan de una en una.

::: {.callout .callout-tip}
[En la práctica]{.callout-title}

Reproduce esto deliberadamente una vez: fija estado en una rama, léelo en el nodo de fusión, míralo ausente, y luego arréglalo con el resultado. Cinco minutos, y la regla se te queda de una forma que leerla no consigue.
:::

### Cuándo salen a cuenta las ramas paralelas

La misma forma que en la Sección 5.13: **trabajo independiente y limitado por E/S**, ejecutado con `AsyncExecutor`. Tres agentes analizando el mismo documento desde ángulos distintos. Dos llamadas a APIs que no dependen entre sí. Procesamiento de texto e imagen de una misma subida.

No es útil para: dependencias secuenciales, ni trabajo trivialmente rápido donde la coordinación cuesta más de lo que ahorra.

### Puntos clave

- La ramificación condicional es un tipo de retorno de unión; converge devolviendo un tipo de evento compartido.
- Una subclase de `ParallelEvent` con ramas con nombre bifurca; el nodo que acepta esa subclase une.
- Las ramas terminan con `StopEvent(result: ...)`; el nodo de fusión lee `getResult('name')`.
- Por defecto las ramas se ejecutan en secuencia; `AsyncExecutor` más `amphp/amp` (y `AmpHttpClient` para los proveedores) las hace concurrentes.
- **El estado de una rama es una copia aislada**: las mutaciones se descartan; devuelve los datos por el resultado.

## 14.3 Gestionar el estado

### El valor por defecto

```php
use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\Events\StartEvent;
use NeuronAI\Workflow\Events\StopEvent;
use NeuronAI\Workflow\WorkflowState;

class InitialNode extends Node
{
    public function __invoke(StartEvent $event, WorkflowState $state): StopEvent
    {
        $state->set('message', 'Hello World!');

        return new StopEvent();
    }
}
```

Un saco con claves de cadena, con `set()` y `get()`. Está bien para flujos de trabajo pequeños y prototipos. También puedes sembrarlo antes de la ejecución: `Workflow::make(state: new WorkflowState(['topic' => $topic]))`.

### Sus debilidades, dichas con claridad

- **Las erratas son silenciosas.** `$state->get('user_id')` frente a `$state->set('userId', ...)` devuelve null sin queja alguna.
- **Sin tipos.** Todo es `mixed`; el análisis estático no ve nada.
- **Sin descubribilidad.** Nada le dice a un desarrollador nuevo qué claves existen. Toca hacer grep.

Para un flujo de trabajo de tres nodos, aceptable. Para un sistema que mantiene un equipo, no.

### CustomState

```php
use App\Models\User;
use NeuronAI\Workflow\WorkflowState;

class CustomState extends WorkflowState
{
    protected User $user;

    public function setUser(User $user): CustomState
    {
        $this->user = $user;
        return $this;
    }

    public function getUser(): User
    {
        return $this->user;
    }
}
```

Los nodos lo aceptan en lugar de `WorkflowState`:

```php
class ExampleNode extends Node
{
    public function __invoke(StartEvent $event, CustomState $state): StopEvent
    {
        // Use state properties in your nodes
        if ($state->getUser()->isAdmin()) {
            //...
        }

        return new StopEvent();
    }
}
```

El segundo parámetro de `__invoke()` puede ser cualquier subclase de `WorkflowState`; el flujo de trabajo lo comprueba al validar el nodo.

Después inyéctalo. El constructor de `Workflow` es `(?string $workflowId, ?WorkflowState $state)`, así que para un flujo de trabajo puntual pásalo por nombre:

```php
$state = Workflow::make(state: (new CustomState())->setUser($user))
    ->addNodes([
        new ExampleNode(),
    ])
    ->run();
```

Para una clase de flujo de trabajo, devuélvelo en cambio desde el hook `state()`, e indica al análisis estático qué estado lleva el flujo de trabajo:

```php
/** @extends Workflow<CustomState> */
class ExampleWorkflow extends Workflow
{
    protected function state(): CustomState
    {
        return new CustomState();
    }

    protected function nodes(): array
    {
        return [
            new ExampleNode(),
        ];
    }
}

$state = ExampleWorkflow::make()->run(); // PHPStan infers CustomState
```

La anotación `@extends` es lo que hace que el tipo de retorno de `run()` sea `CustomState` en lugar de `WorkflowState` para PHPStan y tu IDE: el mismo mecanismo que usa `Agent` para devolver un `AgentState`. Los tutoriales escritos para versiones anteriores inyectan el estado como tercer argumento del constructor, después de la persistencia y un token de reanudación; esa llamada falla. Apéndice A, punto 37.

### Por qué este es el valor por defecto correcto para trabajo real

**Accesores tipados.** `getUser(): User`: autocompletado del IDE, cobertura de PHPStan, soporte de refactorización.

**Autodocumentado.** La clase *es* la lista de lo que lleva este flujo de trabajo. La incorporación se convierte en «lee `OrderWorkflowState`».

**Un sitio para la lógica.** Los valores derivados pertenecen al objeto de estado, no repetidos en cuatro nodos:

```php
class ContentWorkflowState extends WorkflowState
{
    /** @var list<array{draft: string, feedback: string}> */
    protected array $revisions = [];

    public function addRevision(string $draft, string $feedback): self
    {
        $this->revisions[] = ['draft' => $draft, 'feedback' => $feedback];

        return $this;
    }

    public function revisionCount(): int
    {
        return \count($this->revisions);
    }

    // PHP 8.5: #[\NoDiscard] turns a bare `$state->hasReachedLimit();` -
    // a check whose answer nobody reads - into a warning.
    #[\NoDiscard]
    public function hasReachedLimit(int $max = 3): bool
    {
        return $this->revisionCount() >= $max;
    }

    public function lastFeedback(): ?string
    {
        // PHP 8.5: array_last() is null on an empty list and, unlike end(),
        // leaves the array's internal pointer alone.
        return \array_last($this->revisions)['feedback'] ?? null;
    }
}
```

Ahora la guarda de bucle de la Sección 14.1 se lee como `$state->hasReachedLimit()` en cada nodo que la necesita, definida una sola vez.

Dos novedades de PHP 8.5 mantienen honesta la clase. `#[\NoDiscard]` hace que PHP emita un aviso cuando quien llama ignora el valor de retorno de un método, lo que en una comprobación como `hasReachedLimit()` es siempre un error. `array_last()` devuelve el último elemento de un array, o `null` si está vacío, sin mover el puntero interno como hace `end()`.

### La restricción de serialización

Crítica para todo lo duradero, y conviene saberla ya para que no sea una sorpresa:

**El estado se serializa cada vez que se confirma un paso.** No solo cuando un flujo de trabajo se pausa: después de cada nodo, en cada ejecución, incluida una simple en memoria, porque eso es un paso duradero (Sección 13.5). Lo que significa que:

- **Los recursos no se pueden serializar.** Conexiones a base de datos, manejadores de archivo, sockets abiertos. Guarda un identificador y restablece la conexión dentro del nodo que la necesite.
- Lo mismo para las funciones anónimas y cualquier cosa que contenga un recurso o una función anónima de forma indirecta.

Pon un `PDO` en el estado y la ejecución falla en cuanto devuelve el nodo que lo guardó: `Serialization of 'PDO' is not allowed`. Esa es la buena noticia: falla pronto, junto a la línea que lo causó, en lugar de horas después en la frontera de una pausa.

**Guarda IDs, no objetos con conexiones.** `protected int $userId` en lugar de un modelo hidratado que arrastre una conexión viva. Si un objeto de estado necesita de verdad una dependencia viva, el hook `restoreState()` del flujo de trabajo es donde se la vuelves a enganchar al estado leído de nuevo desde el almacén.

**Las ramas paralelas clonan el estado.** El saco `data` que hay detrás de `get()`/`set()` se copia en profundidad para cada rama. Una subclase que guarde *objetos* mutables en sus propias propiedades debe definir `__clone()` para que las copias sean realmente independientes; los escalares y arrays simples, como las revisiones de `ContentWorkflowState`, no necesitan nada.

### Puntos clave

- `WorkflowState` es un saco con claves de cadena: bien en pequeño, débil a escala.
- `CustomState` da accesores tipados, descubribilidad y un hogar para la lógica derivada.
- Inyecta con `Workflow::make(state: ...)`, o con el hook `state()` más `@extends Workflow<CustomState>`.
- **El estado se serializa en cada confirmación de paso**: nada de recursos, conexiones ni funciones anónimas.
- Guarda IDs y rehidrata dentro del nodo.

## 14.4 Transmisión de un flujo de trabajo

### Una palabra clave

Añade `\Generator` al tipo de retorno y usa `yield`:

```php
namespace App\Neuron;

use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\Events\StartEvent;
use NeuronAI\Workflow\Events\StopEvent;
use NeuronAI\Workflow\WorkflowState;

class ProgressEvent
{
    public function __construct(public readonly string $message){}
}

class InitialNode extends Node
{
    public function __invoke(StartEvent $event, WorkflowState $state): \Generator|FirstEvent
    {
        yield new ProgressEvent("Handling StartEvent");

        return new FirstEvent("InitialNode complete");
    }
}

class NodeOne extends Node
{
    public function __invoke(FirstEvent $event, WorkflowState $state): \Generator|SecondEvent
    {
        yield new ProgressEvent($event->firstMsg);

        return new SecondEvent("NodeOne complete");
    }
}

class NodeTwo extends Node
{
    public function __invoke(SecondEvent $event, WorkflowState $state): \Generator|StopEvent
    {
        yield new ProgressEvent($event->secondMsg);
        yield new ProgressEvent("NodeTwo complete");

        $state->set('message', 'Streaming end');

        return new StopEvent();
    }
}
```

> Para transmitir de eventos desde un nodo necesitas añadir `\Generator` como tipo de retorno adicional en `__invoke`.

**`yield` emite progreso. `return` emite el evento de enrutado.** Dos canales desde un mismo método: ese es todo el diseño, y son los generadores de PHP usados exactamente como se pretendía.

Fíjate en que `ProgressEvent` no implementa `Event`. Nunca encamina nada; un nodo puede hacer yield de cualquier objeto. Solo el valor devuelto tiene que ser un `Event`.

La unión `\Generator|FirstEvent` es la forma documentada del framework, y se gana su sitio: PHP la acepta, y `export()` lee la mitad `FirstEvent` para dibujar la arista. PHPStan no la acepta: una función que hace yield solo puede declarar tipos generador, así que informa de `generator.returnType` en cada `yield`. Si tu código base pasa PHPStan, declara solo `\Generator` y lleva el encaminamiento al docblock, `@return \Generator<int, ProgressEvent, mixed, FirstEvent>`. El flujo de trabajo se ejecuta igual; el precio es que `export()` ya no ve adónde lleva el nodo y muestra el nodo siguiente como huérfano.

Para recibir la transmisión, llama a `events()` en lugar de `run()`. Devuelve un generador de todo lo que los nodos emiten con yield, y el estado final es el valor de retorno del generador:

```php
$stream = Workflow::make()
    ->addNodes([
        new InitialNode(),
        new NodeOne(),
        new NodeTwo(),
    ])
    ->events();

foreach ($stream as $item) {
    if ($item instanceof ProgressEvent) {
        echo $item->message . "\n";
    }
}

$state = $stream->getReturn();
```

### El progreso no es duradero

La salida emitida con yield es viva y efímera. No se escribe en el almacén, y cuando una ejecución recuperada reproduce los pasos completados (Sección 13.5), los eventos de progreso de esos pasos **no** se vuelven a emitir: solo el evento devuelto es duradero. Un cliente que se reconecta a mitad de camino se ha perdido lo que se ha perdido.

Así que nunca hagas depender la corrección de que llegue un evento de progreso. Todo lo que la aplicación deba saber va en el estado o en el resultado; el progreso es para el humano que está mirando.

### Por qué esta es una funcionalidad genuinamente fuerte

Compara las dos experiencias de usuario para un flujo de trabajo que tarda 45 segundos.

**Sin transmisión:**

```
[spinner] ......................................... done
```

**Con transmisión:**

```
Researching the topic...
  Found 12 sources
Drafting the article...
  Draft complete: 1,240 words
Reviewing...
  Revision requested: add a counter-argument
Revising...
Done.
```

La segunda no es un spinner más bonito. Es un producto distinto. El usuario sabe que el sistema está trabajando en el problema correcto, entiende por qué va lento y puede abandonar pronto si ha ido mal.

Para los sistemas multiagente esto importa aún más, porque las ejecuciones son más largas. La Sección 1.4 decía que la latencia se acumula; así es como haces tolerable la latencia acumulada.

### Guía de diseño

**Nombra los eventos de progreso para el usuario, no para el desarrollador.** `"Searching the knowledge base"` gana a `"RetrievalNode invoked"`. El mismo principio que la lista de permitidos de etiquetas de herramientas de la Sección 7.4, y la misma preocupación de seguridad: no filtres las tripas del sistema.

**No hagas yield de cada detalle.** Una línea de progreso por documento recuperado es ruido. Una por fase significativa.

**Haz yield antes del trabajo lento, no después.** `yield new ProgressEvent("Researching...")` y luego haz la investigación. Hacer yield después le cuenta al usuario lo que ya terminó, que es la mitad equivocada de la información.

### Conectar con el frontend

Los adaptadores de transmisión de la Sección 7.5 aplican aquí. `setStreamAdapter()` con `AGUIAdapter` o `VercelAIAdapter` convierte la salida de un flujo de trabajo en eventos de protocolo para un navegador. Un adaptador solo codifica lo que entiende: haz yield directamente de los eventos de transmisión portables de NeuronAI (`StepStartedStreamEvent`, `ActivityStreamEvent` y compañía, en `NeuronAI\Agent\Adapters\Events`), o conserva tu propio `ProgressEvent` y registra una traducción con el `mapEvent()` del adaptador. Añade un canal con `setChannel()` —`PusherChannel`, `RedisChannel`— y un flujo de trabajo **en cola** transmite a un cliente con el que no tiene conexión directa.

Esa es la combinación que construye el Capítulo 21: flujo de trabajo largo en un proceso, progreso en vivo en el navegador.

### Puntos clave

- Añade `\Generator` al tipo de retorno; haz `yield` del progreso y `return` del evento de enrutado.
- Dos canales desde un mismo método; consúmelos con `events()` y `getReturn()`.
- El progreso es efímero: nunca se guarda, nunca se reproduce.
- Nombra los eventos de progreso para los usuarios; uno por fase; haz yield antes del trabajo.
- Los adaptadores y los canales llevan el progreso del flujo de trabajo al frontend, incluso desde trabajos en cola.
