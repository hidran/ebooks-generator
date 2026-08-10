# Capítulo 14 — Bucles, ramas y estado

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

`FirstEvent|SecondEvent`. Si devuelves un tipo de evento que no está en la firma, el flujo de trabajo no puede resolver el nodo siguiente.

Este es el error número uno de los flujos de trabajo. Falla en tiempo de ejecución con un mensaje confuso, y la causa es un tipo de unión que alguien olvidó ampliar tras añadir una rama.

### Bucle hacia cualquier sitio

> Puedes crear un bucle desde cualquier nodo hacia cualquier otro nodo definiendo los eventos de entrada y retorno apropiados. Un nodo incluso puede devolver un `StartEvent` para saltar directamente al primer nodo del flujo de trabajo.

Devolver `StartEvent` reinicia todo el flujo: reintento completo desde el principio.

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

        $verdict = ReviewerAgent::make()
            ->structured(new UserMessage($event->draft), Verdict::class);

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

Dos cosas que esto demuestra más allá del contador:

**Cada iteración del bucle cuesta llamadas al LLM.** Esto es la Sección 1.4 otra vez. Un bucle de revisión sin límite es una factura sin límite.

**Ten un plan para cuando se alcance el límite.** Escalar a un humano gana a publicar en silencio el tercer borrador. Ese es el puente natural hacia el Capítulo 15.

### Los bucles son donde los sistemas agénticos se ganan el sueldo

Un bucle con un LLM dentro es *refinamiento iterativo*: redactar, criticar, revisar, repetir hasta que sea suficientemente bueno. Ese patrón —redactor más crítico— es una de las formas multiagente de mayor valor, y es un flujo de trabajo de tres nodos con un tipo de retorno de unión.

### Puntos clave

- Un bucle es un nodo que devuelve un evento que vuelve a disparar un nodo anterior.
- **Declara todos los tipos de retorno posibles en la unión**: el error de flujo de trabajo más común.
- Devolver `StartEvent` reinicia todo el flujo de trabajo.
- El framework no acota los bucles; cuenta en el estado y planifica el límite.

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

La ramificación secuencial elige un camino. La paralela ejecuta varios **concurrentemente**.

```php
use NeuronAI\Workflow\Events\ParallelEvent;

class DocumentProcessing extends Node
{
    public function __invoke(StartEvent $event, WorkflowState $state): ParallelEvent
    {
        return new ParallelEvent([
            'text'  => new TextProcessEvent(),
            'image' => new ImageProcessEvent(),
        ]);
    }
}
```

Cada rama es una **clave con nombre** que apunta al primer evento de esa rama. Los nodos que gestionan esos eventos, y todo lo que va aguas abajo en cada rama, se registran en el flujo de trabajo con normalidad:

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

Una vez completadas todas las ramas, el `ParallelEvent` se reenvía al punto de fusión, que lee cada resultado por nombre:

```php
class MergeNode extends Node
{
    public function __invoke(ParallelEvent $event, WorkflowState $state): StopEvent
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

::: {.callout .callout-tip}
[En la práctica]{.callout-title}

Reproduce esto deliberadamente una vez: fija estado en una rama, léelo en el nodo de fusión, míralo ausente, y luego arréglalo con el resultado. Cinco minutos, y la regla se te queda de una forma que leerla no consigue.
:::

### Cuándo salen a cuenta las ramas paralelas

La misma forma que en la Sección 5.13: **trabajo independiente y limitado por E/S**. Tres agentes analizando el mismo documento desde ángulos distintos. Dos llamadas a APIs que no dependen entre sí. Procesamiento de texto e imagen de una misma subida.

No es útil para: dependencias secuenciales, ni trabajo trivialmente rápido donde la coordinación cuesta más de lo que ahorra.

### Puntos clave

- La ramificación condicional es un tipo de retorno de unión; converge devolviendo un tipo de evento compartido.
- `ParallelEvent(['name' => $event, ...])` ejecuta las ramas concurrentemente.
- Las ramas terminan con `StopEvent(result: ...)`; el nodo de fusión lee `getResult('name')`.
- **El estado de una rama es una copia aislada**: las mutaciones se descartan; devuelve los datos por el resultado.

## 14.3 Gestionar el estado

### El valor por defecto

```php
use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\StartEvent;
use NeuronAI\Workflow\StopEvent;
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

Un saco con claves de cadena, con `set()` y `get()`. Está bien para flujos de trabajo pequeños y prototipos.

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

Después inyéctalo al construir el flujo de trabajo. Confirma la firma de inyección en tu versión: este es uno de los sitios donde se nota la deriva de constructores v2/v3. Apéndice A, punto 37.

### Por qué este es el valor por defecto correcto para trabajo real

**Accesores tipados.** `getUser(): User`: autocompletado del IDE, cobertura de PHPStan, soporte de refactorización.

**Autodocumentado.** La clase *es* la lista de lo que lleva este flujo de trabajo. La incorporación se convierte en «lee `OrderWorkflowState`».

**Un sitio para la lógica.** Los valores derivados pertenecen al objeto de estado, no repetidos en cuatro nodos:

```php
class ContentWorkflowState extends WorkflowState
{
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

    public function hasReachedLimit(int $max = 3): bool
    {
        return $this->revisionCount() >= $max;
    }

    public function lastFeedback(): ?string
    {
        $last = \end($this->revisions);
        return $last === false ? null : $last['feedback'];
    }
}
```

Ahora la guarda de bucle de la Sección 14.1 se lee como `$state->hasReachedLimit()` en cada nodo que la necesita, definida una sola vez.

### La restricción de serialización

Crítica para el Capítulo 15, y conviene saberla ya para que no sea una sorpresa:

**El estado se serializa cuando un flujo de trabajo se interrumpe.** Lo que significa que:

- **Los recursos no se pueden serializar.** Conexiones a base de datos, manejadores de archivo, sockets abiertos. Guarda un identificador y restablece la conexión cuando el nodo se reanude.
- Lo mismo para las funciones anónimas y cualquier cosa que contenga un recurso de forma indirecta.

La propia orientación del framework es explícita en esto. Un `CustomState` que contenga un `PDO` fallará en la frontera de interrupción, y fallará ahí, no donde lo escribiste, lo que lo convierte en un error desagradable de rastrear.

**Guarda IDs, no objetos con conexiones.** `protected int $userId` en lugar de un modelo hidratado que arrastre una conexión viva.

### Puntos clave

- `WorkflowState` es un saco con claves de cadena: bien en pequeño, débil a escala.
- `CustomState` da accesores tipados, descubribilidad y un hogar para la lógica derivada.
- **El estado se serializa al interrumpirse**: nada de recursos, conexiones ni funciones anónimas.
- Guarda IDs y rehidrata dentro del nodo.

## 14.4 Transmisión de un flujo de trabajo

### Una palabra clave

Añade `\Generator` al tipo de retorno y usa `yield`:

```php
namespace App\Neuron;

use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\StartEvent;
use NeuronAI\Workflow\StopEvent;

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

**Nombra los eventos de progreso para el usuario, no para el desarrollador.** `"Searching the knowledge base"` gana a `"RetrieveDocumentsNode invoked"`. El mismo principio que la lista de permitidos de etiquetas de herramientas de la Sección 7.4, y la misma preocupación de seguridad: no filtres las tripas del sistema.

**No hagas yield de cada detalle.** Una línea de progreso por documento recuperado es ruido. Una por fase significativa.

**Haz yield antes del trabajo lento, no después.** `yield new ProgressEvent("Researching...")` y luego haz la investigación. Hacer yield después le cuenta al usuario lo que ya terminó, que es la mitad equivocada de la información.

### Conectar con el frontend

Los adaptadores de transmisión de la Sección 7.5 aplican aquí. Los eventos de progreso de un flujo de trabajo van a través de `AGUIAdapter` o `VercelAIAdapter` hasta un navegador y —como allí se señalaba— un adaptador que empuja hacia un transporte como Pusher permite que un flujo de trabajo **en cola** transmita a un cliente con el que no tiene conexión directa.

Esa es la combinación que construye el Capítulo 21: flujo de trabajo largo en un proceso, progreso en vivo en el navegador.

### Puntos clave

- Añade `\Generator` al tipo de retorno; haz `yield` del progreso y `return` del evento de enrutado.
- Dos canales desde un mismo método.
- Nombra los eventos de progreso para los usuarios; uno por fase; haz yield antes del trabajo.
- Los adaptadores llevan el progreso del flujo de trabajo al frontend, incluso desde trabajos en cola.
