# Capítulo 16 — Sistemas multiagente

## 16.1 Patrones de orquestación

### Primero, la pregunta escéptica

Los sistemas multiagente se demuestran de maravilla y a menudo son la respuesta equivocada. Antes de adoptar uno, pregúntate: **¿bastaría con un solo agente con más herramientas?**

A menudo sí. Cada agente de más es otro conjunto de llamadas al modelo, otro prompt de sistema que mantener, otro punto donde el contexto se pierde en la traducción. La aritmética de la Sección 1.4 aplica por agente.

Lo multiagente se gana su sitio cuando: las subtareas requieren instrucciones genuinamente distintas, los agentes necesitan conjuntos de herramientas o permisos distintos, o quieres una revisión independiente de la salida de un agente.

El tercero es el caso más fuerte, y no va realmente de capacidades: va de **independencia**. Un agente que revisa su propio trabajo es un pésimo crítico. Un agente aparte con un prompt de sistema de crítico es mejor.

### Los patrones

**Secuencial.** Investigador → Redactor → Editor. La salida de cada etapa alimenta a la siguiente. Simple, predecible, fácil de depurar. El valor por defecto, y a menudo suficiente.

**Supervisor.** Un coordinador decide a qué especialista invocar, recibe el resultado, decide qué viene después. Flexible, y el más caro: el supervisor hace una llamada al modelo por decisión.

**Paralelo.** Varios agentes trabajan simultáneamente en subtareas independientes; un nodo de fusión combina. Rápido para trabajo genuinamente independiente. La Sección 14.2 te da el mecanismo.

**Debate / bucle del crítico.** Un generador produce, un crítico evalúa, el generador revisa. Repite hasta que el crítico quede satisfecho o se alcance el límite. Es el bucle de la Sección 14.1 con dos agentes dentro, y es el patrón con la mejor relación calidad/complejidad de la lista.

### Proyectar los patrones sobre NeuronAI

Cada uno es una forma de flujo de trabajo que ya conoces:

| Patrón | Mecanismo |
|---|---|
| Secuencial | Cadena de nodos, un evento cada uno |
| Supervisor | Un nodo que devuelve una unión de eventos de los especialistas |
| Paralelo | `ParallelEvent` con ramas con nombre |
| Bucle del crítico | Tipo de retorno de unión que vuelve atrás |

**Ninguna API multiagente especial.** Es el punto de la Sección 2.3 llegando por última vez: un agente es un nodo, y componer nodos es lo que hacen los flujos de trabajo.

### Disciplina de costes

Un pipeline secuencial de cuatro agentes son como mínimo cuatro llamadas al modelo, normalmente más si alguno usa herramientas. Un bucle del crítico de tres vueltas son seis o más.

Dos mitigaciones:

**Modelos distintos por agente.** El investigador y el crítico pueden necesitar un modelo potente; el formateador no. El cambio de proveedor de la Sección 3.6 va aquí por nodo, y es uno de los mejores argumentos del framework en un contexto multiagente.

**Acota todos los bucles.** El contador de la Sección 14.1, no negociable.

### Puntos clave

- Pregúntate si bastaría un solo agente con más herramientas; a menudo bastaría.
- La revisión independiente es el argumento más fuerte a favor de lo multiagente.
- Cuatro patrones: secuencial, supervisor, paralelo, bucle del crítico.
- Ninguna API especial: los agentes son nodos.
- Varía el modelo por agente; acota todos los bucles.

## 16.2 Un agente como nodo

### El envoltorio

```php
<?php

declare(strict_types=1);

namespace App\Workflow\Nodes;

use App\Agents\ResearchAgent;
use App\Workflow\Events\ResearchCompleted;
use App\Workflow\Events\TopicRequested;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\WorkflowState;

class ResearchNode extends Node
{
    public function __invoke(TopicRequested $event, WorkflowState $state): \Generator|ResearchCompleted
    {
        yield new ProgressEvent("Researching {$event->topic}...");

        $findings = ResearchAgent::make()
            ->chat(new UserMessage("Research this topic thoroughly: {$event->topic}"))
            ->getMessage()
            ->getContent();

        $state->set('sources_used', $this->countSources($findings));

        return new ResearchCompleted($event->topic, $findings);
    }
}
```

El nodo es un adaptador fino. Toda la inteligencia —proveedor, instrucciones, herramientas— vive en `ResearchAgent`, que no cambia y sigue funcionando por sí solo.

Merece decirse explícitamente: `ResearchAgent` no sabe que está dentro de un flujo de trabajo. Puedes seguir haciéndole pruebas unitarias, llamarlo directamente, reutilizarlo en otro pipeline. El nodo es pegamento.

### Salida estructurada entre agentes

Pasar prosa entre agentes pierde información e invita al error de interpretación. Pasa en su lugar objetos tipados:

```php
class ReviewNode extends Node
{
    public function __invoke(DraftCompleted $event, WorkflowState $state): DraftCompleted|ArticleApproved
    {
        $verdict = ReviewerAgent::make()->structured(
            new UserMessage($event->draft),
            Verdict::class
        );

        if ($verdict->approved) {
            return new ArticleApproved($event->draft);
        }

        $state->set('last_feedback', $verdict->feedback);

        return new DraftCompleted($event->draft, $verdict->feedback);
    }
}
```

```php
class Verdict
{
    #[SchemaProperty(description: 'Whether the draft meets the quality bar.', required: true)]
    public bool $approved;

    #[SchemaProperty(
        description: 'If not approved, the specific changes required. One instruction per sentence.',
        required: true
    )]
    public string $feedback;

    #[SchemaProperty(description: 'Quality score from 0 to 10.', required: true)]
    #[GreaterThanEqual(reference: 0)]
    #[LowerThanEqual(reference: 10)]
    public int $score;
}
```

**Este es el Capítulo 6 haciendo trabajo estructural.** `$verdict->approved` es un booleano sobre el que tu PHP ramifica. Parsear «el borrador me parece bien» para sacar un sí o un no sería lanzar una moneda al aire.

La regla: **salida estructurada en cada frontera entre agentes.** La prosa es para las personas.

### Proveedores distintos por nodo

```php
class DraftNode extends Node
{
    public function __invoke(ResearchCompleted $event, WorkflowState $state): DraftCompleted
    {
        // Strong model — this is the creative work
        $draft = WriterAgent::make()->chat(/* ... */);

        return new DraftCompleted($draft);
    }
}

class FormatNode extends Node
{
    public function __invoke(ArticleApproved $event, WorkflowState $state): StopEvent
    {
        // Cheap model — mechanical transformation
        $formatted = FormatterAgent::make()->chat(/* ... */);

        return new StopEvent(result: $formatted);
    }
}
```

Cada agente declara su propio proveedor. El escalonado de costes en un sistema multiagente es una propiedad de cómo escribiste los agentes, no algo que configures aparte.

### Puntos clave

- El nodo es un adaptador fino; el agente sigue siendo independiente y testeable.
- Usa `structured()` en cada frontera entre agentes: la prosa pierde información.
- Haz yield del progreso desde los nodos-agente; las ejecuciones son lo bastante largas como para necesitarlo.
- La elección de proveedor es por agente, así que el escalonado de costes es gratis.

## 16.3 Contexto sin explosión de tokens

### El modo de fallo

El pipeline multiagente ingenuo acumula. El agente 1 produce 800 palabras. El agente 2 las recibe más el prompt original y produce 1.200. El agente 3 lo recibe todo y produce 1.500. El agente 4 recibe el conjunto.

Para el cuarto agente estás enviando 4.000 palabras de contexto para producir 300 de salida, y la Sección 1.4 ya mostró qué le hace la acumulación a los costes.

### Cuatro técnicas

**1. Pasa el artefacto, no la transcripción.**

El redactor necesita los *resultados* de la investigación. No necesita el razonamiento del investigador, ni sus llamadas a herramientas, ni sus borradores intermedios.

```php
// Bad: the whole conversation
return new ResearchCompleted($agent->getChatHistory()->getMessages());

// Good: just the output
return new ResearchCompleted($event->topic, $findings);
```

**2. Resume en la frontera.**

Cuando la salida de un agente es realmente grande, añade un paso de compresión. Una llamada a un modelo barato para reducir 3.000 palabras a 400 ahorra mucho más de lo que cuesta en cualquier pipeline con dos o más agentes aguas abajo.

**3. Usa el estado para el contexto compartido y los eventos para el relevo.**

La distinción de la Sección 13.2, aplicada. El inquilino, el usuario, el encargo: estado. El artefacto concreto que este nodo produjo para el siguiente: evento.

**4. Dale a cada agente solo lo que necesita.**

```php
class FactCheckNode extends Node
{
    public function __invoke(DraftCompleted $event, WorkflowState $state): FactCheckCompleted
    {
        // The fact-checker gets claims and sources. Not the draft's prose,
        // not the brief, not the research narrative.
        $result = FactCheckAgent::make()->structured(
            new UserMessage(json_encode([
                'claims'  => $event->extractedClaims,
                'sources' => $state->get('sources'),
            ])),
            FactCheckResult::class
        );

        return new FactCheckCompleted($result);
    }
}
```

Es diseño de interfaces ordinario —entradas mínimas y explícitas— aplicado a los agentes. **Cada agente tiene una interfaz, y una interfaz ancha es tan mala aquí como en cualquier otro sitio.**

### Medirlo

Habilita Inspector (Capítulo 10) y lee los tokens de entrada por nodo a lo largo de la ejecución. Si crecen linealmente por el pipeline, estás acumulando. Ese número es tu objetivo de optimización, y es visible en lugar de supuesto.

### Puntos clave

- Pasa artefactos, no transcripciones.
- Resume en las fronteras cuando la salida sea grande.
- Estado para el contexto compartido, eventos para los relevos.
- Trata la entrada de cada agente como una interfaz: mantenla mínima.
- Lee los tokens de entrada por nodo en la traza para encontrar la acumulación.

## 16.4 Ejecución asíncrona

### Por qué no es opcional

Suma lo que ha establecido la Parte IV:

- Una ejecución multiagente son muchas llamadas al modelo (Sección 16.1)
- Cada una dura de 1 a 4 segundos (Sección 1.4)
- Las llamadas a herramientas en paralelo requieren CLI (Sección 5.13)
- El humano en el circuito significa esperar horas o días (Sección 15.1)

Un flujo de trabajo de 60 segundos no puede vivir en una petición HTTP. Cualquier cosa con una interrupción *desde luego* no puede.

**Los flujos de trabajo largos pertenecen a una cola.**

### La arquitectura

```
Petición HTTP   → despacha un trabajo → devuelve enseguida un ID de flujo de trabajo
Proceso de cola → ejecuta el flujo de trabajo → transmite el progreso vía adaptador
                                              → persiste las interrupciones
Humano          → responde por interfaz/correo
Proceso de cola → reanuda el flujo de trabajo → completa
Cliente         → recibe progreso y resultado por el transporte
```

Cuatro piezas que ya tienes:

- **Persistencia** (Sección 15.4) para el estado de interrupción
- **Adaptador de transmisión** (Sección 7.5) para empujar el progreso hacia un transporte
- **ID de flujo de trabajo** como clave de correlación
- **Cola** como contexto de ejecución

### Qué cambia en un proceso

**`pcntl` pasa a estar disponible**, así que las llamadas a herramientas en paralelo (Sección 5.13) y las evaluaciones en paralelo (Sección 10.6) funcionan.

**Inspector necesita `autoFlush: true`** (Sección 10.2). Un proceso no tiene un final de petición, así que sin eso las trazas no llegan nunca. Es la mala configuración más probable en un despliegue asíncrono.

**No hay conexión HTTP con el usuario.** Y por eso importan los adaptadores que empujan hacia un transporte websocket: el proceso transmite hacia Pusher, el navegador escucha.

**Los tiempos de espera son asunto tuyo.** Los procesos de cola tienen límites de tiempo. Un flujo de trabajo que corre diez minutos necesita un proceso configurado para ello, o bien debe interrumpirse y reanudarse entre trabajos distintos.

### El patrón que ata la Parte IV

Para un flujo de trabajo largo y filtrado por humanos, cada segmento entre interrupciones es un trabajo aparte:

```
Trabajo 1: ejecuta hasta la interrupción de aprobación → persiste → notifica al responsable → fin
           (el proceso queda libre)
Trabajo 2: disparado por la aprobación → reanuda → ejecuta hasta completar o hasta la siguiente interrupción
```

El proceso no se queda bloqueado esperando. Entre un segmento y otro no hay ningún proceso: solo una fila en `workflow_interrupts`.

Eso es lo que «reanudar incluso entre sesiones distintas» significa en el plano operativo. Y es además, para un público de PHP acostumbrado a la ejecución ligada a la petición, una resolución muy satisfactoria: la ausencia de estado de PHP deja de ser una limitación y se convierte en el modelo de distribución.

### Puntos clave

- Las ejecuciones multiagente largas pertenecen a una cola; las que tienen una interrupción, con más razón.
- En un proceso: `pcntl` funciona, `autoFlush` es obligatorio, no hay conexión HTTP con el usuario.
- Cada segmento entre interrupciones es un trabajo aparte; nada espera.
- Persistencia, adaptador, ID de flujo de trabajo y cola son las cuatro piezas, y ya las tienes todas.

## Laboratorio 10 — La fábrica de contenidos

**Cubre:** toda la Parte IV.

### Objetivo

Investigación → borrador → bucle de revisión → aprobación humana → publicación. Es el flujo de trabajo multiagente canónico y ejercita bucles, estado, transmisión, interrupción, puntos de control y persistencia en un solo artefacto.

### La forma

```
StartEvent
   ↓
ResearchNode        (juego de herramientas Tavily)
   ↓ ResearchCompleted
DraftNode           (agente redactor)
   ↓ DraftCompleted
ReviewNode          (agente crítico, Verdict estructurado)
   ↓ DraftCompleted (vuelve atrás, máx. 3)  |  ArticleApproved
                                            ↓
ApprovalNode        (interrupción: el humano revisa y edita)
   ↓ ArticleEdited
PublishNode
   ↓ StopEvent
```

### Los eventos

```php
<?php

declare(strict_types=1);

namespace App\Workflow\Events;

use NeuronAI\Workflow\Events\Event;

final class ResearchCompleted implements Event
{
    public function __construct(
        public readonly string $topic,
        public readonly string $findings,
    ) {}
}

final class DraftCompleted implements Event
{
    public function __construct(
        public readonly string $draft,
        public readonly ?string $feedback = null,
    ) {}
}

final class ArticleApproved implements Event
{
    public function __construct(
        public readonly string $draft,
    ) {}
}

final class ArticleEdited implements Event
{
    public function __construct(
        public readonly string $content,
    ) {}
}
```

Fíjate en los nombres: hechos en pasado, según la Sección 13.4. Fíjate también en `readonly`: los eventos son mensajes, no contenedores mutables.

### El estado

```php
<?php

declare(strict_types=1);

namespace App\Workflow;

use NeuronAI\Workflow\WorkflowState;

class ContentState extends WorkflowState
{
    protected int $revisions = 0;
    protected array $feedbackLog = [];

    public function recordRevision(string $feedback): self
    {
        $this->revisions++;
        $this->feedbackLog[] = $feedback;
        return $this;
    }

    public function revisionCount(): int
    {
        return $this->revisions;
    }

    public function hasReachedLimit(int $max = 3): bool
    {
        return $this->revisions >= $max;
    }

    public function feedbackHistory(): array
    {
        return $this->feedbackLog;
    }
}
```

Solo escalares y arrays: sin conexiones, sin recursos. La restricción de serialización de la Sección 14.3, respetada por diseño.

### El nodo de revisión, donde la parte se recompone

```php
<?php

declare(strict_types=1);

namespace App\Workflow\Nodes;

use App\Agents\ReviewerAgent;
use App\Dto\Verdict;
use App\Workflow\ContentState;
use App\Workflow\Events\ArticleApproved;
use App\Workflow\Events\DraftCompleted;
use App\Workflow\Events\ProgressEvent;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Workflow\Node;

class ReviewNode extends Node
{
    public function __invoke(
        DraftCompleted $event,
        ContentState $state
    ): \Generator|DraftCompleted|ArticleApproved {
        yield new ProgressEvent('Reviewing the draft...');

        $verdict = ReviewerAgent::make()->structured(
            new UserMessage($event->draft),
            Verdict::class
        );

        if ($verdict->approved) {
            yield new ProgressEvent("Approved with a score of {$verdict->score}/10.");

            return new ArticleApproved($event->draft);
        }

        if ($state->hasReachedLimit()) {
            yield new ProgressEvent('Revision limit reached — sending to human review as is.');

            return new ArticleApproved($event->draft);
        }

        $state->recordRevision($verdict->feedback);

        yield new ProgressEvent("Revision {$state->revisionCount()}: {$verdict->feedback}");

        return new DraftCompleted($event->draft, $verdict->feedback);
    }
}
```

Todos los conceptos de la Parte IV en una sola clase: un tipo de retorno de unión (14.1), un bucle acotado con un plan para el límite (14.1), estado propio (14.3), progreso en transmisión (14.4) y salida estructurada en una frontera entre agentes (16.2).

### El nodo de aprobación

```php
class ApprovalNode extends Node
{
    public function __invoke(ArticleApproved $event, ContentState $state): ArticleEdited
    {
        $reviewed = $this->interrupt(
            new ContentReviewInterrupt(
                message: \sprintf(
                    'Article ready after %d revision(s). Review and edit before publishing.',
                    $state->revisionCount()
                ),
                content: $event->draft
            )
        );

        return new ArticleEdited($reviewed->getContent());
    }
}
```

El humano edita en lugar de aprobar: el patrón colaborativo de la Sección 15.3.

### La demostración del punto de control

Hazlo deliberadamente. Son los veinte minutos más valiosos de la Parte IV, porque convierten una advertencia abstracta en un error que has causado en persona.

Escribe `ApprovalNode` de forma que el borrador se *genere* dentro de él, sin punto de control:

```php
// DELIBERATELY WRONG — reproduce the bug before fixing it
$draft = WriterAgent::make()->chat(...)->getMessage()->getContent();

$reviewed = $this->interrupt(new ContentReviewInterrupt(/* ... */, $draft));
```

Ejecútalo, interrumpe, reanuda. El borrador se regenera y **la versión reanudada difiere de la que el humano aprobó.**

Después envuélvelo:

```php
$draft = $this->checkpoint('draft', fn () => WriterAgent::make()->chat(...)->getMessage()->getContent());
```

Vuelve a ejecutar. El mismo borrador. El mismo contenido que vio el humano.

No es un argumento de eficiencia. Es un fallo de corrección demostrable con una corrección de una línea, y es el motivo por el que existe la Sección 15.5.

### Ejecutarlo

```php
$workflow = new ContentWorkflow(
    new FilePersistence(__DIR__ . '/../storage/workflows')
);

try {
    $handler = $workflow->init();

    foreach ($handler->streamEvents() as $progress) {
        echo "  {$progress->message}\n";
    }

    echo "\nPublished.\n";
} catch (WorkflowInterrupt $interrupt) {
    $id      = $interrupt->getWorkflowId();
    $request = $interrupt->getRequest();

    \file_put_contents(
        __DIR__ . "/../storage/pending/{$id}.json",
        \json_encode($request, JSON_PRETTY_PRINT)
    );

    echo "\nAwaiting review. Workflow ID: {$id}\n";
    echo "Edit storage/pending/{$id}.json and run: php examples/11-resume.php {$id}\n";
}
```

Confirma el accesor de transmisión del gestor en tu versión instalada: es uno de los puntos de deriva v2/v3 de la advertencia del inicio del Capítulo 13. Apéndice A, punto 38.

Editar un archivo JSON en disco como «interfaz de aprobación» es exactamente lo correcto para un laboratorio de CLI. Hace visible el mecanismo, y el Capítulo 22 lo sustituye por una pantalla de administración de verdad.

### Criterios de aceptación

- El bucle de revisión se ejecuta como máximo tres veces, y alcanzar el límite dispara el escalado en lugar de fallar.
- Matar el proceso PHP tras la interrupción y reanudar desde un proceso nuevo produce el artículo publicado.
- Con el punto de control puesto, el contenido publicado es idéntico byte a byte a lo que la petición de interrupción le mostró al humano. Sin él, no lo es: demuestra ambas cosas.
- Las líneas de progreso aparecen mientras el flujo de trabajo corre, no todas al final.

### Extensiones

1. Añade una rama paralela: la verificación de hechos y el análisis SEO se ejecutan concurrentemente tras la aprobación, y se fusionan antes de publicar.
2. Añade `interruptIf()` para que solo los artículos con puntuación por debajo de 8 requieran revisión humana.
3. Mueve la ejecución a un proceso de cola y haz transmisión del progreso a un websocket.

## Ejercicios del capítulo

1. **Construye el pipeline.** Un flujo de trabajo secuencial de tres agentes con salida estructurada en cada frontera.
2. **Añade un bucle del crítico** con un contador acotado y un plan para cuando se alcance el límite. El plan importa más que el contador.
3. **Interrumpe y reanuda.** Añade una interrupción antes de la acción final; persístela; reanuda desde un script aparte, un proceso genuinamente separado y no una segunda llamada en el mismo.
4. **Pon puntos de control por todas partes.** Envuelve en `checkpoint()` cada llamada al LLM que preceda a una interrupción y verifica que no se reejecuta. Registra dentro de la función anónima para demostrarlo.
5. **Reduce la acumulación.** Mide los tokens de entrada por nodo y baja su crecimiento. Escribe los números de antes y después uno al lado del otro.
