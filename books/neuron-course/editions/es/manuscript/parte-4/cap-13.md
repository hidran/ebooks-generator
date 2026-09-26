# Capítulo 13 — El modelo guiado por eventos

::: {.callout .callout-warning}
[Antes de escribir código de flujo de trabajo]{.callout-title}

Un flujo de trabajo se ejecuta llamando a `run()` sobre el propio flujo de trabajo, y devuelve el estado final:

```php
$state = Workflow::make()->addNodes($nodes)->run();
```

Los tutoriales escritos para versiones anteriores llaman a `start()` o a `init()` y pasan por un objeto gestor; ninguna de las dos cosas existe en la versión de este libro. El constructor es `(?string $workflowId, ?WorkflowState $state)`, así que el material que le pasa un objeto de persistencia o un argumento `resumeToken:` falla. Y la propia documentación muestra nodos con un tercer parámetro `WorkflowResources $resources` que el código rechaza: el `__invoke()` de un nodo debe recibir exactamente dos parámetros, el evento y el estado.

Apéndice A, puntos 30 a 32.
:::

::: {.callout .callout-tip}
[El código de este capítulo]{.callout-title}

La versión ejecutable de cada listado que sigue está en [`chapters/Ch13`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch13), en el repositorio complementario. Clónalo, ejecuta `composer install` y los ejemplos funcionan contra un Ollama local sin ninguna clave de API.
:::

## 13.1 Qué es un flujo de trabajo

### La definición

Un flujo de trabajo es una forma guiado por eventos y basada en nodos de controlar el flujo de ejecución de una aplicación.

Tu aplicación se divide en **nodos**, que se disparan mediante **eventos** y que a su vez devuelven eventos que disparan más nodos. Combínalos y podrás expresar flujos arbitrariamente complejos.

La documentación ofrece una comparación que merece la pena tomar prestada: **«Es como n8n a nivel de código.»** Si has visto una herramienta visual de automatización, eso cala de inmediato: cajas conectadas por flechas, salvo que las cajas son clases PHP y las flechas son tipos.

### Un nodo puede ser cualquier cosa

Desde una sola línea de código hasta un agente completo. Entradas y salidas arbitrarias, pasadas mediante eventos.

Esa flexibilidad es el objetivo. Un nodo podría:

- Llamar a un LLM
- Consultar tu base de datos
- Ejecutar una recuperación RAG
- Enviar un correo
- Esperar a un humano
- Ser un `Agent` entero haciendo su propio bucle de llamadas a herramientas

### La afirmación de la Sección 2.3, en la fuente

> Las clases Agent y RAG son flujos de trabajo en sí mismas. Representan implementaciones listas para usar de los patrones más comunes de llamadas a herramientas, recuperación y salida estructurada. Workflow te permite programar tu sistema agéntico completamente desde cero. Agent y RAG pueden usarse dentro de un Workflow para completar tareas como cualquier otro componente.

Por eso el Capítulo 2 insistía en ello. La Parte IV no es un tema nuevo: es la capa que estuvo debajo de las Partes II y III todo el tiempo. Esto es literal, no una forma de hablar: `Agent` está declarado como `class Agent extends Workflow`, y el bucle de llamadas a herramientas que usaste en la Parte II es un conjunto de nodos encaminados por el mismo motor que estás a punto de programar directamente.

### Qué hace distintivo al flujo de trabajo de NeuronAI

La documentación nombra dos capacidades, y una tercera se sitúa por debajo de ambas:

**Transmisión** — un sistema multiagente puede empujar actualizaciones a los clientes mientras se ejecuta.

**Interrupción** — el flujo de trabajo puede pausarse a mitad de proceso, pedir intervención humana, esperar y continuar desde el nodo que se pausó, incluso horas o días después, en otro proceso.

**Durabilidad** — cada nodo que termina se confirma en un almacén como un *paso*. Una ejecución que se cae, falla o se pausa no vuelve a empezar desde arriba: los pasos completados se reproducen desde el almacén, y solo se ejecuta el trabajo pendiente.

La tercera es lo que hace posible la segunda. La mayoría de los motores de flujo de trabajo pueden pausar; pocos pueden pausar *dentro* de un nodo, sobrevivir a un reinicio de proceso y continuar con la realimentación humana inyectada en el punto en que se detuvieron, sin rehacer el trabajo caro que vino antes. La Sección 13.5 muestra los pasos duraderos con una caída que puedes ejecutar; el Capítulo 15 construye la interrupción sobre ellos, y es el argumento individual más fuerte a favor del framework.

### Puntos clave

- Nodos disparados por eventos, que devuelven eventos que disparan más nodos.
- Un nodo es cualquier cosa, desde una línea hasta un agente entero.
- Agent y RAG *son* flujos de trabajo; este es el sustrato, no un añadido.
- La transmisión, la interrupción y los pasos duraderos son las capacidades distintivas.

## 13.2 Nodo, evento, estado

### Evento

Una clase PHP simple que implementa `Event`. Puede tener cualquier nombre y cualquier property.

```php
namespace App\Neuron;

use NeuronAI\Workflow\Events\Event;

class FirstEvent implements Event
{
    public function __construct(public readonly string $firstMsg){}
}

class SecondEvent implements Event
{
    public function __construct(public readonly string $secondMsg){}
}
```

Genéralos:

```bash
vendor/bin/neuron make:event App\\Neuron\\FirstEvent
```

El framework incluye dos eventos especiales:

- **`StartEvent`** — con el que empieza el flujo de trabajo
- **`StopEvent`** — el que lo termina

### Nodo

Una clase que extiende `Node` con un solo método:

```php
use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\Events\StartEvent;
use NeuronAI\Workflow\WorkflowState;

class InitialNode extends Node
{
    public function __invoke(StartEvent $event, WorkflowState $state): FirstEvent
    {
        echo "\n- Handling StartEvent";

        return new FirstEvent("InitialNode complete");
    }
}
```

```bash
vendor/bin/neuron make:node App\\Neuron\\InitialNode
```

La firma es estricta: exactamente dos parámetros, primero un evento y después un `WorkflowState` (o una subclase suya), y un tipo de retorno hecho de eventos. El flujo de trabajo valida cada nodo mediante reflexión antes de ejecutar nada, así que una firma mal formada falla de inmediato con el nombre del nodo en el mensaje.

### La idea que lo hace encajar

**La firma del método es el grafo.**

```text
public function __invoke(StartEvent $event, WorkflowState $state): FirstEvent
```

Léela como una declaración de cableado: *este nodo se ejecuta cuando aparece un `StartEvent`, y cuando termina emite un `FirstEvent`.*

No hay definición de aristas aparte, ni archivo de configuración, ni llamada a `addEdge()`. **Las declaraciones de tipo son el cableado.**

Deja que eso repose, porque todo lo demás en la Parte IV se deriva de ello:

- ¿Quieres un bucle? Devuelve el evento que dispara un nodo anterior.
- ¿Quieres una ramificación? Declara un tipo de retorno de unión.
- ¿Quieres conocer el grafo? Lee las firmas.

::: {.callout .callout-warning}
[No hay clase `Edge`]{.callout-title}

No hay clase `Edge` ni `addEdges()`: los tipos de evento son las aristas. Si encuentras un tutorial que use `new Edge(NodeA::class, NodeB::class)`, se escribió para una versión mucho más antigua del framework. Apéndice A, punto 32.
:::

### Estado

`WorkflowState` es el contenedor compartido que viaja por la ejecución:

```php
class InitialNode extends Node
{
    public function __invoke(StartEvent $event, WorkflowState $state): StopEvent
    {
        $state->set('message', 'Hello World!');

        return new StopEvent();
    }
}
```

`set()` y `get()`, más `has()`, `delete()`, `only()` y `all()`. Disponibles para todos los nodos y, como el estado se guarda con cada paso completado (Sección 13.5), tiene que ser serializable. La Sección 14.3 detalla lo que eso descarta.

### Eventos frente a estado: cuándo usar cada uno

Una distinción que la gente confunde de forma consistente, así que aquí va explícitamente:

**Los eventos llevan el mensaje.** Lo que produjo este paso concreto, pasado al siguiente paso concreto. Efímero, direccional, tipado.

**El estado lleva el contexto.** Cosas que necesitan muchos nodos: el usuario, el inquilino, resultados acumulados, configuración. Persistente en toda la ejecución.

La heurística: **si solo lo necesita el nodo siguiente, ponlo en el evento. Si lo necesitan varios nodos, o lo necesitas después de la ejecución, ponlo en el estado.**

Abusar del estado produce un flujo de trabajo donde cada nodo lee y escribe en un saco global, que es un flujo de trabajo solo de nombre, porque el flujo de datos vuelve a ser invisible. Abusar de los eventos produce clases de evento enormes que van pasándolo todo. Ambos extremos son peores que el equilibrio.

### Puntos clave

- Evento = clase simple que implementa `Event`; `StartEvent` y `StopEvent` vienen incluidos.
- Nodo = clase con `__invoke(Event, WorkflowState): Event`, con exactamente dos parámetros.
- **La firma del método es el grafo**: no hay aristas que declarar.
- Eventos para el mensaje entre dos pasos; estado para el contexto compartido.

## 13.3 Un flujo de trabajo de un solo paso

### Todo el asunto

```php
namespace App\Neuron;

use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\Events\StartEvent;
use NeuronAI\Workflow\Events\StopEvent;
use NeuronAI\Workflow\WorkflowState;

class InitialNode extends Node
{
    public function __invoke(StartEvent $event, WorkflowState $state): StopEvent
    {
        $state->set('answer', 'Hello World!');

        return new StopEvent();
    }
}
```

```php
use NeuronAI\Workflow\Workflow;

$state = Workflow::make()
    ->addNodes([
        new InitialNode(),
    ])
    ->run();

echo $state->get('answer'); // Hello World!
```

`StartEvent` entra, `StopEvent` sale. Un nodo. `run()` devuelve el `WorkflowState` final.

### El ciclo de vida

1. `Workflow::make()` construye el flujo de trabajo. Su constructor acepta dos argumentos opcionales, un ID del flujo de trabajo y un estado inicial; todavía no necesitas ninguno.
2. `addNodes()` registra los nodos. **El orden del array no es el orden de ejecución**: eso lo deciden los eventos. El array es un registro, no una secuencia.
3. `run()` ejecuta: da una identidad a la ejecución, emite `StartEvent`, encuentra el nodo cuya firma lo acepta, lo ejecuta, confirma el resultado como un paso, toma el evento devuelto, encuentra el nodo que acepta *ese*, y repite hasta el `StopEvent`. Devuelve el estado final.

No hay ningún objeto intermedio entre construir un flujo de trabajo y ejecutarlo. `run()` y su hermano de transmisión `events()` (Sección 14.4) son las dos únicas formas de ejecutarlo, y ambos se llaman sobre el propio flujo de trabajo.

El punto 2 merece énfasis. Viniendo de pipelines procedimentales, la suposición natural es que el orden del array importa. No importa, y entender por qué es entender el modelo.

### La forma de clase

`addNodes()` es cómodo para un script. En una aplicación, un flujo de trabajo suele ser una clase, y sus nodos vienen del hook `nodes()`:

```php
use NeuronAI\Workflow\Workflow;

class GreetingWorkflow extends Workflow
{
    protected function nodes(): array
    {
        return [
            new InitialNode(),
        ];
    }
}

$state = GreetingWorkflow::make()->run();
```

El motor llama a `nodes()` de nuevo al comienzo de cada segmento de ejecución, así que el grafo siempre se construye a partir de la configuración actual del flujo de trabajo, lo que importa en cuanto una ejecución puede pausarse en un proceso y continuar en otro.

### ¿Es esto útil?

Por sí solo, no. Pero es el sitio correcto por donde empezar porque aísla la mecánica de la complejidad, y porque la sección siguiente solo le añade una idea.

### Puntos clave

- `Workflow::make()->addNodes([...])->run()` devuelve el estado final; no hay gestor.
- `addNodes()` es un registro, no una secuencia: los eventos determinan el orden.
- La ejecución va de `StartEvent` a `StopEvent`.
- En una subclase, el hook `nodes()` proporciona el grafo.

## 13.4 Varios pasos: los eventos como cableado

### Los eventos

```php
namespace App\Neuron;

use NeuronAI\Workflow\Events\Event;

class FirstEvent implements Event
{
    public function __construct(public readonly string $firstMsg){}
}

class SecondEvent implements Event
{
    public function __construct(public readonly string $secondMsg){}
}
```

### Los nodos

```php
use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\Events\StartEvent;
use App\Neuron\FirstEvent;

class InitialNode extends Node
{
    /**
     * Gets the "StartEvent" and returns "FirstEvent"
     */
    public function __invoke(StartEvent $event, WorkflowState $state): FirstEvent
    {
        echo "\n- Handling StartEvent";

        return new FirstEvent("InitialNode complete");
    }
}
```

```php
class NodeOne extends Node
{
    /**
     * Takes "FirstEvent" as input and returns "SecondEvent"
     */
    public function __invoke(FirstEvent $event, WorkflowState $state): SecondEvent
    {
        echo "\n- ".$event->firstMsg;

        return new SecondEvent("NodeOne complete");
    }
}
```

```php
class NodeTwo extends Node
{
    /**
     * Takes "SecondEvent" as input and returns "StopEvent"
     */
    public function __invoke(SecondEvent $event, WorkflowState $state): StopEvent
    {
        echo "\n- ".$event->secondMsg;
        echo "\n- NodeTwo complete";

        return new StopEvent();
    }
}
```

### Ejecutarlo

```php
use NeuronAI\Workflow\Workflow;

$state = Workflow::make()
    ->addNodes([
        new InitialNode(),
        new NodeOne(),
        new NodeTwo(),
    ])
    ->run();
```

```
- Handling StartEvent
- InitialNode complete
- NodeOne complete
- NodeTwo complete
```

### Leer el grafo a partir de las firmas

Quita todo excepto las tres firmas:

```text
__invoke(StartEvent  $e, ...): FirstEvent
__invoke(FirstEvent  $e, ...): SecondEvent
__invoke(SecondEvent $e, ...): StopEvent
```

```
StartEvent → InitialNode → FirstEvent → NodeOne → SecondEvent → NodeTwo → StopEvent
```

El grafo está justo ahí, en las declaraciones de tipo. Ninguna configuración que se desincronice del código, y tu IDE lo navega: pincha en el tipo de evento para encontrar el nodo que lo consume.

El framework también sabe leerlo. `$workflow->export()` recorre las mismas firmas e imprime el grafo —como árbol de consola por defecto, o como diagrama Mermaid con `setExporter(new MermaidExporter())`—, lo que es una forma barata de comprobar que el grafo que querías es el grafo que escribiste.

### Los nombres, que importan más de lo que parece

`FirstEvent` y `SecondEvent` están bien para un tutorial y son terribles para un proyecto real. En producción, nombra los eventos por **lo que ocurrió**:

```text
ArticleDrafted
ResearchCompleted
ReviewRejected
RefundApproved
PaymentFailed
```

Hechos en pasado, no posiciones de secuencia. Entonces la firma se lee como una frase: *este nodo se ejecuta cuando se ha redactado un artículo y produce una petición de revisión*. Quien lea el código seis meses después entenderá el flujo sin un diagrama.

Esto es la denominación ordinaria de eventos de dominio del diseño guiado por eventos, y aplica sin cambios aquí.

### ¿Un campo por evento, o todo el contexto?

Mantén los eventos pequeños. Un evento debería llevar lo que el nodo *siguiente* necesita, no todo lo acumulado hasta ahora. El contexto compartido grande pertenece al estado (Sección 14.3). Un evento que crece hasta quince properties te está diciendo que sus datos pertenecen al estado.

### Puntos clave

- Tres nodos, tres firmas, un grafo.
- Las declaraciones de tipo son el cableado: legible y navegable desde el IDE.
- Nombra los eventos como hechos de dominio en pasado, no `FirstEvent`.
- Mantén los eventos pequeños; pon el contexto compartido en el estado.

## 13.5 Pasos duraderos

### Cada nodo es un paso

Hasta ahora un flujo de trabajo parece una forma ordenada de llamar a funciones en un orden decidido por los tipos. Por debajo, es un pequeño motor de ejecución duradera, y la diferencia se nota la primera vez que algo falla.

Cuando un nodo devuelve, el motor no se limita a entregar el evento al nodo siguiente. **Confirma un paso**: el evento devuelto y el estado tal como está, escritos en la persistencia del flujo de trabajo bajo la identidad de la ejecución. Solo entonces encamina el evento hacia delante. Con la configuración por defecto ese almacén está en memoria y desaparece con el proceso, y por eso no lo has notado. Dale al flujo de trabajo un backend de persistencia que sobreviva al proceso, y cada nodo completado se convierte en un hecho que el motor no volverá a hacer.

La consecuencia: una ejecución que falla en su quinto nodo, y se vuelve a iniciar, **reproduce** los nodos uno a cuatro desde el almacén —sus eventos y su estado se releen, su `__invoke()` no se llama— y ejecuta solo el quinto.

### El ID del flujo de trabajo

Para volver a encontrar una ejecución, el motor necesita un nombre para ella. Ese nombre es el **ID del flujo de trabajo**, y es la partición del almacén donde vive cada registro de la ejecución. Puedes pasar uno explícitamente —`Workflow::make(workflowId: 'report:42')`—, pero el mejor hábito es dejar que el flujo de trabajo declare su propia clave de negocio:

```php
namespace App\Neuron;

use NeuronAI\Workflow\Workflow;

class ReportWorkflow extends Workflow
{
    public function __construct(private readonly int $reportId)
    {
        parent::__construct();
    }

    public function workflowId(): ?string
    {
        return 'report:' . $this->reportId;
    }

    protected function nodes(): array
    {
        return [
            new ResearchNode(),
            new PublishNode(),
        ];
    }
}
```

Cualquier proceso que pueda construir `ReportWorkflow::make(reportId: 42)` y llegar al mismo almacén puede encontrar esta ejecución. No hay ninguna tabla que asocie tus registros con ID generados por el motor, porque la clave de negocio *es* la ubicación en el almacén. Un flujo de trabajo que no declara nada recibe un ID generado, legible con `$state->getWorkflowId()` una vez iniciada la ejecución.

No lo confundas con el **ID de ejecución**. Cada vez que una ejecución arranca bajo un ID del flujo de trabajo, el motor la sella con un ID de ejecución nuevo (`$state->getRunId()`), un marcador de generación que sirve para el trazado y para dejar fuera a los escritores obsoletos. El ID del flujo de trabajo es el asa con la que continúas una ejecución; el ID de ejecución te dice qué intento estás mirando. La regla que se deduce: **una sola ejecución viva por ID del flujo de trabajo**. Iniciar una segunda mientras la primera sigue en pausa o en marcha lanza una `RunInFlightException`.

### Memoizar dentro de un paso

Los pasos tienen el tamaño de un nodo. Un nodo que hace una llamada cara y *luego* falla vuelve a ejecutarse desde su primera línea, y paga la llamada otra vez. `memoize()` cierra ese hueco:

```php
namespace App\Neuron;

use NeuronAI\Workflow\Events\StopEvent;
use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\WorkflowState;
use RuntimeException;

class PublishNode extends Node
{
    /**
     * Stands in for a flaky HTTP endpoint: the first call fails.
     *
     * PHP 8.5: asymmetric visibility on a static property - anyone may read
     * the counter, only this node may change it.
     */
    public private(set) static int $publishCalls = 0;

    public function __invoke(ResearchDone $event, WorkflowState $state): StopEvent
    {
        $draft = $this->memoize('draft', function () use ($event): string {
            echo "- PublishNode: drafting from '{$event->notes}'\n";

            return 'Report based on: ' . $event->notes;
        });

        if (++self::$publishCalls === 1) {
            echo "- PublishNode: publishing... failed\n";
            throw new RuntimeException('Publisher unavailable');
        }

        echo "- PublishNode: publishing... done\n";
        $state->set('published', $draft);

        return new StopEvent();
    }
}
```

El contador se declara `public private(set) static`: PHP 8.5 extiende la visibilidad asimétrica a las propiedades estáticas, así que cualquier código puede leer el contador y solo el propio nodo puede modificarlo, una garantía que un simple `public static` no podía dar.

La closure se ejecuta una sola vez. Su resultado se confirma bajo el nombre `draft` en el momento en que devuelve, y cuando el nodo se vuelve a ejecutar el valor regresa del almacén sin que se llame a la closure. En un flujo de trabajo real la closure es la llamada al LLM, la petición HTTP, la ejecución de la herramienta: cualquier cosa cara o no determinista.

Dos reglas la hacen segura. **La closure debe depender solo del evento y del estado del nodo**, para que el valor registrado siga siendo la respuesta correcta al reproducir. Y **una memoización no es una transacción**: una caída después de la llamada externa pero antes de que se confirme su resultado repite la llamada. Donde una repetición importe —un pago, un correo—, dale al sistema externo una clave de idempotencia.

::: {.callout .callout-warning}
[`checkpoint()` es el nombre antiguo]{.callout-title}

Los tutoriales antiguos usan `checkpoint()`. Sigue existiendo, obsoleto, y se limita a llamar a `memoize()`. Escribe `memoize()`.
:::

### Verlo funcionar

`ResearchNode`, el primer paso, es el nodo evidente de dos líneas: consume `StartEvent`, imprime `- ResearchNode: calling the slow research service` y devuelve un evento `ResearchDone` que lleva sus notas.

El repositorio complementario ejecuta el flujo de trabajo dos veces contra un directorio de `FilePersistence`. El primer intento falla en `PublishNode`; el segundo es un objeto `ReportWorkflow` completamente nuevo que no comparte nada con el primero salvo el directorio y el ID del flujo de trabajo que declara. Podría ser perfectamente otro proceso, otro día:

```php
$storage = \sys_get_temp_dir() . '/neuron-book-ch13';
$persistence = new FilePersistence($storage);

echo "Attempt 1\n";
try {
    ReportWorkflow::make(reportId: 42)->setPersistence($persistence)->run();
} catch (RuntimeException $e) {
    echo "  caught: {$e->getMessage()}\n";
}

echo "\nAttempt 2\n";
$state = ReportWorkflow::make(reportId: 42)->setPersistence($persistence)->run();
```

```
Attempt 1
- ResearchNode: calling the slow research service
- PublishNode: drafting from 'Three sources, one counter-argument'
- PublishNode: publishing... failed
  caught: Publisher unavailable

Attempt 2
- PublishNode: publishing... done

Workflow ID: report:42
Published: 'Report based on: Three sources, one counter-argument'
Status: Completed
```

El segundo `run()` encontró una ejecución *fallida* bajo `report:42` y la recuperó en lugar de empezar de cero. `ResearchNode` no imprimió nada, porque su paso se reprodujo. El borrador no se reescribió, porque estaba memoizado. Solo la llamada de publicación volvió a ejecutarse. Nada en el código que llama decía «recupera»: un simple `run()` recupera automáticamente una ejecución fallida, y habría iniciado una nueva si no hubiera habido nada que recuperar.

Cuando la ejecución termina, el motor borra sus registros. El almacén guarda trabajo en curso, no historial, así que no crece, y el ID del flujo de trabajo queda libre para la siguiente ejecución.

### Dónde viven los registros

`setPersistence()` acepta cualquier backend que implemente `PersistenceInterface`. Los que vienen incluidos:

| Backend | Úsalo para |
|---|---|
| `InMemoryPersistence` | El predeterminado. Reproducción solo dentro de un proceso. |
| `FilePersistence` | Desarrollo, y despliegues de un solo proceso. |
| `DatabasePersistence` | Producción con varios procesos (PDO, una tabla `workflow_store`). |
| `EloquentPersistence` | Lo mismo, a través de un modelo de Laravel. |
| `RedisPersistence` | Producción con varios procesos, sobre Redis. |

Elijas el que elijas, un ID del flujo de trabajo es una partición, y cada escritura es una escritura condicional contra el registro de control de la ejecución, así que dos procesos no pueden hacer avanzar a la vez la misma ejecución. El Capítulo 15 se apoya en todo esto para pausar una ejecución a la espera de un humano; el Capítulo 22 lo lleva a una base de datos real.

### Puntos clave

- Cada nodo completado se confirma como un paso duradero; una ejecución recuperada reproduce los pasos completados en lugar de volver a ejecutarlos.
- El ID del flujo de trabajo nombra la ejecución en el almacén; decláralo con `workflowId()` como clave de negocio. El ID de ejecución es un sello por intento.
- Una sola ejecución viva por ID del flujo de trabajo; un simple `run()` recupera automáticamente una ejecución fallida.
- `memoize('name', fn () => ...)` hace que el trabajo caro dentro de un nodo sea seguro al reproducir. No es exactamente-una-vez: usa claves de idempotencia para los efectos secundarios.
- Por defecto, al completarse se borran los registros de la ejecución.

## 13.6 ¿Por qué no escribir simplemente un script?

### La objeción

La documentación la plantea ella misma, lo cual es buena señal:

> «Esto suena genial, pero ¿por qué no puedo escribir simplemente un script PHP normal con unos cuantos if y funciones?»

Y admite: *«Es una pregunta justa, y una que oí mucho mientras construía Neuron.»*

### La respuesta honesta para los casos simples

**Para un proceso lineal de tres pasos, un script es mejor.** Menos archivos, menos indirección, más fácil de leer. La propia respuesta del framework lo concede: el potencial no es visible cuando el caso de uso es simple, y eso es normal.

No te lo vendas demasiado a ti mismo. Adoptar flujos de trabajo para todo produce un código base donde una llamada a función se convirtió en cuatro clases, y acabarás resintiéndolo.

### Dónde se rompe el script

La respuesta documentada enumera las condiciones, y cada una se corresponde con un coste real:

**Varias ramas ejecutándose concurrentemente.** Hacer esto en un script significa `pcntl_fork` y recogida manual de resultados. La Sección 14.2 lo muestra como un tipo de retorno.

**Varios bucles con puntos de control intermedios.** Se puede hacer con `while`, hasta que necesitas saber en qué iteración estabas después de una caída. En un flujo de trabajo cada iteración es su propio paso duradero, así que el motor ya lo sabe.

**Transmisión de actualizaciones en tiempo real.** Un script puede hacer echo. No puede emitir fácilmente eventos de progreso estructurados desde una profundidad arbitraria sin hilar un callback a través de cada función.

**Pausar, esperar, reanudar.** Esta es la que no es cuestión de esfuerzo. Persistir cada paso completado, detenerse a mitad de un nodo, continuar en otro proceso horas después sin repetir el trabajo ya hecho, y garantizar que dos procesos nunca hagan avanzar la misma ejecución: eso no lo puedes escribir en un script sin construir un motor de flujos de trabajo. Y si construyes uno, has construido la Sección 13.5.

### Los cuatro beneficios de desarrollo

De la documentación:

**Modelar y mantener escenarios complejos.** Desde unos pocos pasos hasta bucles iterativos con puntos de control, usando los mismos bloques de construcción.

**Humano en el circuito.** Desplegar IA en áreas sensibles porque siempre hay un humano en el circuito para las decisiones críticas.

**Transmisión.** Actualizaciones en tiempo real al cliente durante la ejecución.

**Depuración con Inspector.** En lugar de preguntarte por qué el flujo de trabajo tomó una decisión, ves exactamente qué ocurrió en cada nodo.

Esa última conecta con el Capítulo 10. El motor emite un evento cuando cada nodo empieza y termina, y cualquier observador —Inspector incluido— los convierte en una traza de pasos con nombre. Un script muestra una traza de pila.

### La regla de decisión

Escribe un script cuando: lineal, sin ramificación, sin intervención humana, sin necesidad de reanudar, sin transmisión.

Escribe un flujo de trabajo cuando **se cumpla cualquiera de estas**: varios agentes, aprobación humana, reanudable, larga duración, progreso en transmisión, o ramificación y bucles no triviales.

Y el argumento que lo cierra, de los documentos:

> Si las cosas se ponen feas, Neuron ya tiene la arquitectura adecuada para ayudarte a escalar a cualquier nivel.

No migras de framework cuando llega el requisito. Añades un nodo.

### Puntos clave

- Para procesos lineales simples, un script es genuinamente mejor. Dilo.
- La concurrencia, los puntos de control, la transmisión y la reanudación son donde los scripts se rompen.
- Pausar y reanudar no es cuestión de esfuerzo: requiere pasos duraderos, es decir, un motor.
- Un solo desencadenante basta para justificar un flujo de trabajo; no los necesitas todos.
