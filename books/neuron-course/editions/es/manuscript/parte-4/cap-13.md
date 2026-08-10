# Capítulo 13 — El modelo event-driven

::: {.callout .callout-warning}
[Antes de escribir código de workflow]{.callout-title}

La documentación de workflows contiene **dos API de ejecución distintas** en sus propias páginas:

```php
// v3 style — Multi Step Workflow page
$handler = Workflow::make()->addNodes([...])->init();
$handler->run();

// v2 style — Loops & Branches page, and most blog posts
$state = Workflow::make()->addNodes([...])->start()->getResult();
```

El estilo v2 muestra además `Workflow::make(new WorkflowState(), $persistence, 'id')` y una clase `Edge` que **ya no existe en v3**: el modelo event-driven la sustituyó por completo.

Ejecuta un workflow mínimo contra tu versión instalada y resuelve dos cosas: `init()`/`run()` frente a `start()`/`getResult()`, y la firma del constructor de `Workflow`. Esta parte usa la forma v3 `init()`/`run()` en todo momento. Casi todas las entradas de blog que encuentres usarán la otra. Apéndice A, puntos 30 a 32.
:::

## 13.1 Qué es un workflow

### La definición

Un workflow es una forma event-driven y basada en nodos de controlar el flujo de ejecución de una aplicación.

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
- Ser un `Agent` entero haciendo su propio bucle de llamadas a tools

### La afirmación de la Sección 2.3, en la fuente

> Las clases Agent y RAG son workflows en sí mismas. Representan implementaciones listas para usar de los patrones más comunes de llamadas a tools, recuperación y structured output. Workflow te permite programar tu sistema agéntico completamente desde cero. Agent y RAG pueden usarse dentro de un Workflow para completar tareas como cualquier otro componente.

Por eso el Capítulo 2 insistía en ello. La Parte IV no es un tema nuevo: es la capa que estuvo debajo de las Partes II y III todo el tiempo.

### Qué hace distintivo al workflow de NeuronAI

La documentación nombra dos capacidades:

**Streaming** — un sistema multiagente puede empujar actualizaciones a los clientes mientras se ejecuta.

**Interrupción** — el workflow puede pausarse a mitad de proceso, pedir intervención humana, esperar y continuar exactamente donde lo dejó, incluso horas o días después.

La segunda es inusual. La mayoría de los motores de workflow pueden pausar; pocos pueden pausar *dentro* de un nodo, serializar todo el contexto de ejecución, sobrevivir a un reinicio de proceso y reanudarse con la realimentación humana inyectada en el punto exacto en que se detuvieron. Eso es el Capítulo 15, y es el argumento individual más fuerte a favor del framework.

### Puntos clave

- Nodos disparados por eventos, que devuelven eventos que disparan más nodos.
- Un nodo es cualquier cosa, desde una línea hasta un agente entero.
- Agent y RAG *son* workflows; este es el sustrato, no un añadido.
- El streaming y la interrupción son las capacidades distintivas.

## 13.2 Nodo, evento, estado

### Evento

Una clase PHP simple que implementa `Event`. Puede tener cualquier nombre y cualquier property.

```php
namespace App\Neuron;

class FirstEvent implements Event
{
    public function __construct(protected string $firstMsg){}
}

class SecondEvent implements Event
{
    public function __construct(protected string $secondMsg){}
}
```

Genéralos:

```bash
vendor/bin/neuron make:event App\\Neuron\\FirstEvent
```

El framework incluye dos eventos especiales:

- **`StartEvent`** — con el que empieza el workflow
- **`StopEvent`** — el que lo termina

### Nodo

Una clase que extiende `Node` con un solo método:

```php
use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\StartEvent;
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

### La idea que lo hace encajar

**La firma del método es el grafo.**

```php
public function __invoke(StartEvent $event, WorkflowState $state): FirstEvent
```

Léela como una declaración de cableado: *este nodo se ejecuta cuando aparece un `StartEvent`, y cuando termina emite un `FirstEvent`.*

No hay definición de aristas aparte, ni archivo de configuración, ni llamada a `addEdge()`. **Los type hints son el cableado.**

Deja que eso repose, porque todo lo demás en la Parte IV se deriva de ello:

- ¿Quieres un bucle? Devuelve el evento que dispara un nodo anterior.
- ¿Quieres una ramificación? Declara un tipo de retorno de unión.
- ¿Quieres conocer el grafo? Lee las firmas.

::: {.callout .callout-warning}
[Nota histórica]{.callout-title}

La versión 1 tenía una clase `Edge` explícita y `addEdges()`. La v2 la eliminó en favor del modelo de eventos. Si encuentras un tutorial que use `new Edge(NodeA::class, NodeB::class)`, es anterior a la arquitectura actual por dos versiones mayores. Apéndice A, punto 32.
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

`set()` y `get()`. Disponibles para todos los nodos.

### Eventos frente a estado: cuándo usar cada uno

Una distinción que la gente confunde de forma consistente, así que aquí va explícitamente:

**Los eventos llevan el mensaje.** Lo que produjo este paso concreto, pasado al siguiente paso concreto. Efímero, direccional, tipado.

**El estado lleva el contexto.** Cosas que necesitan muchos nodos: el usuario, el tenant, resultados acumulados, configuración. Persistente en toda la ejecución.

La heurística: **si solo lo necesita el nodo siguiente, ponlo en el evento. Si lo necesitan varios nodos, o lo necesitas después de la ejecución, ponlo en el estado.**

Abusar del estado produce un workflow donde cada nodo lee y escribe en un saco global, que es un workflow solo de nombre, porque el flujo de datos vuelve a ser invisible. Abusar de los eventos produce clases de evento enormes que van pasándolo todo. Ambos extremos son peores que el equilibrio.

### Puntos clave

- Evento = clase simple que implementa `Event`; `StartEvent` y `StopEvent` vienen incluidos.
- Nodo = clase con `__invoke(Event, WorkflowState): Event`.
- **La firma del método es el grafo**: no hay aristas que declarar.
- Eventos para el mensaje entre dos pasos; estado para el contexto compartido.

## 13.3 Un workflow de un solo paso

### Todo el asunto

```php
namespace App\Neuron;

use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\StartEvent;
use NeuronAI\Workflow\StopEvent;
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

$handler = Workflow::make()
    ->addNodes([
        new InitialNode(),
    ])
    ->init();

$handler->run();
```

`StartEvent` entra, `StopEvent` sale. Un nodo.

### El ciclo de vida

1. `Workflow::make()` construye el workflow.
2. `addNodes()` registra los nodos. **El orden del array no es el orden de ejecución**: eso lo deciden los eventos. El array es un registro, no una secuencia.
3. `init()` prepara la ejecución y devuelve un handler.
4. `run()` ejecuta: emite `StartEvent`, encuentra el nodo cuya firma lo acepta, lo ejecuta, toma el evento devuelto, encuentra el nodo que acepta *ese*, y repite hasta el `StopEvent`.

El punto 2 merece énfasis. Viniendo de pipelines procedimentales, la suposición natural es que el orden del array importa. No importa, y entender por qué es entender el modelo.

### ¿Es esto útil?

Por sí solo, no. Pero es el sitio correcto por donde empezar porque aísla la mecánica de la complejidad, y porque la sección siguiente solo le añade una idea.

### Puntos clave

- `Workflow::make()->addNodes([...])->init()` y luego `run()`.
- `addNodes()` es un registro, no una secuencia: los eventos determinan el orden.
- La ejecución va de `StartEvent` a `StopEvent`.

## 13.4 Varios pasos: los eventos como cableado

### Los eventos

```php
namespace App\Neuron;

class FirstEvent implements Event
{
    public function __construct(protected string $firstMsg){}
}

class SecondEvent implements Event
{
    public function __construct(protected string $secondMsg){}
}
```

### Los nodos

```php
use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\StartEvent;
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

$handler = Workflow::make()
    ->addNodes([
        new InitialNode(),
        new NodeOne(),
        new NodeTwo(),
    ])
    ->init();

$handler->run();
```

```
- Handling StartEvent
- InitialNode complete
- NodeOne complete
- NodeTwo complete
```

### Leer el grafo a partir de las firmas

Quita todo excepto las tres firmas:

```php
__invoke(StartEvent  $e, ...): FirstEvent
__invoke(FirstEvent  $e, ...): SecondEvent
__invoke(SecondEvent $e, ...): StopEvent
```

```
StartEvent → InitialNode → FirstEvent → NodeOne → SecondEvent → NodeTwo → StopEvent
```

El grafo está justo ahí, en las declaraciones de tipo. Ninguna configuración que se desincronice del código, y tu IDE lo navega: pincha en el tipo de evento para encontrar el nodo que lo consume.

### Los nombres, que importan más de lo que parece

`FirstEvent` y `SecondEvent` están bien para un tutorial y son terribles para un proyecto real. En producción, nombra los eventos por **lo que ocurrió**:

```php
ArticleDrafted
ResearchCompleted
ReviewRejected
RefundApproved
PaymentFailed
```

Hechos en pasado, no posiciones de secuencia. Entonces la firma se lee como una frase: *este nodo se ejecuta cuando se ha redactado un artículo y produce una petición de revisión*. Quien lea el código seis meses después entenderá el flujo sin un diagrama.

Esto es la denominación ordinaria de eventos de dominio del diseño event-driven, y aplica sin cambios aquí.

### ¿Un campo por evento, o todo el contexto?

Mantén los eventos pequeños. Un evento debería llevar lo que el nodo *siguiente* necesita, no todo lo acumulado hasta ahora. El contexto compartido grande pertenece al estado (Sección 14.3). Un evento que crece hasta quince properties te está diciendo que sus datos pertenecen al estado.

### Puntos clave

- Tres nodos, tres firmas, un grafo.
- Las declaraciones de tipo son el cableado: legible y navegable desde el IDE.
- Nombra los eventos como hechos de dominio en pasado, no `FirstEvent`.
- Mantén los eventos pequeños; pon el contexto compartido en el estado.

## 13.5 ¿Por qué no escribir simplemente un script?

### La objeción

La documentación la plantea ella misma, lo cual es buena señal:

> «Esto suena genial, pero ¿por qué no puedo escribir simplemente un script PHP normal con unos cuantos if y funciones?»

Y admite: *«Es una pregunta justa, y una que oí mucho mientras construía Neuron.»*

### La respuesta honesta para los casos simples

**Para un proceso lineal de tres pasos, un script es mejor.** Menos archivos, menos indirección, más fácil de leer. La propia respuesta del framework lo concede: el potencial no es visible cuando el caso de uso es simple, y eso es normal.

No te lo vendas demasiado a ti mismo. Adoptar workflows para todo produce un código base donde una llamada a función se convirtió en cuatro clases, y acabarás resintiéndolo.

### Dónde se rompe el script

La respuesta documentada enumera las condiciones, y cada una se corresponde con un coste real:

**Varias ramas ejecutándose concurrentemente.** Hacer esto en un script significa `pcntl_fork` y recogida manual de resultados. La Sección 14.2 lo muestra como un tipo de retorno.

**Varios bucles con checkpoints intermedios.** Se puede hacer con `while`, hasta que necesitas saber en qué iteración estabas después de una caída.

**Streaming de actualizaciones en tiempo real.** Un script puede hacer echo. No puede emitir fácilmente eventos de progreso estructurados desde una profundidad arbitraria sin hilar un callback a través de cada función.

**Pausar, esperar, reanudar.** Esta es la que no es cuestión de esfuerzo. Serializar todo el estado de ejecución a mitad de una función, persistirlo, reanudarlo en otro proceso horas después: eso no lo puedes escribir en un script sin construir un motor de workflows. Y si construyes uno, has construido esto.

### Los cuatro beneficios de desarrollo

De la documentación:

**Modelar y mantener escenarios complejos.** Desde unos pocos pasos hasta bucles iterativos con checkpoints, usando los mismos bloques de construcción.

**Humano en el circuito.** Desplegar IA en áreas sensibles porque siempre hay un humano en el circuito para las decisiones críticas.

**Streaming.** Actualizaciones en tiempo real al cliente durante la ejecución.

**Depuración con Inspector.** En lugar de preguntarte por qué el workflow tomó una decisión, ves exactamente qué ocurrió en cada nodo.

Esa última conecta con el Capítulo 10. Los nodos son unidades con nombre, así que un trace muestra pasos con nombre. Un script muestra una traza de pila.

### La regla de decisión

Escribe un script cuando: lineal, sin ramificación, sin intervención humana, sin necesidad de reanudar, sin streaming.

Escribe un workflow cuando **se cumpla cualquiera de estas**: varios agentes, aprobación humana, reanudable, larga duración, progreso en streaming, o ramificación y bucles no triviales.

Y el argumento que lo cierra, de los documentos:

> Si las cosas se ponen feas, Neuron ya tiene la arquitectura adecuada para ayudarte a escalar a cualquier nivel.

No migras de framework cuando llega el requisito. Añades un nodo.

### Puntos clave

- Para procesos lineales simples, un script es genuinamente mejor. Dilo.
- La concurrencia, los checkpoints, el streaming y la reanudación son donde los scripts se rompen.
- Pausar y reanudar no es cuestión de esfuerzo: requiere un motor.
- Un solo desencadenante basta para justificar un workflow; no los necesitas todos.
