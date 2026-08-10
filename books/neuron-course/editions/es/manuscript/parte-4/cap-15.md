# Capítulo 15 — Humano en el circuito

## 15.1 La interrupción: la funcionalidad, no el fallo

### Qué hace

El patrón de interrupción de NeuronAI permite que un flujo de trabajo **pause la ejecución y espere una entrada externa antes de reanudarse.**

No «para y empieza de nuevo». Pausa —en mitad de un nodo—, preservándolo todo, y reanuda desde ese punto exacto con la respuesta del humano inyectada.

### Las cuatro fases

La documentación describe un patrón de petición-respuesta:

1. **Petición** — un nodo identifica algo que requiere intervención humana y crea un `InterruptRequest`.
2. **Pausa** — el flujo de trabajo lanza una excepción `WorkflowInterrupt`, preservando todo el contexto de ejecución.
3. **Decisión** — tu aplicación presenta la petición a un humano, que aprueba, rechaza o edita.
4. **Reanudación** — el flujo de trabajo continúa desde el mismo nodo, con la decisión disponible.

> Este diseño garantiza que un flujo de trabajo pueda pausarse con seguridad en cualquier punto, persistir su estado y reanudarse exactamente donde lo dejó, **incluso entre sesiones distintas.**

### Por qué «incluso entre sesiones distintas» es toda la historia

Léelo literalmente. El proceso PHP termina. La petición web se completa. El servidor se redespliega. Pasan tres días.

Entonces el responsable pincha «aprobar» en un correo, y el flujo de trabajo continúa desde mitad del nodo donde se detuvo, con todo su contexto intacto.

Para un público de PHP esto es genuinamente notable, porque el modelo de ejecución de PHP es célebremente de ámbito de petición. La respuesta del framework es serialización más una capa de persistencia, y convierte «la IA lo hace todo» en «la IA hace el trabajo, un humano toma las decisiones», que es la única forma que la mayoría de las empresas desplegará de verdad para algo con consecuencias.

### La interrupción es una excepción, deliberadamente

`WorkflowInterrupt` se lanza, no se devuelve. Eso parece raro al principio y el razonamiento merece enunciarse.

Significa que la interrupción desenrolla la pila desde donde sea que ocurra —arbitrariamente adentro de un nodo, dentro de un ayudante, dentro de un middleware— sin que cada capa intermedia tenga que saberlo ni hilar un valor de retorno de vuelta. Cualquier nodo o middleware puede interrumpir, desde cualquier sitio.

El coste es que debes capturarla. Un `WorkflowInterrupt` que se escape a tu manejador de errores parece una caída y se registrará como tal. La Sección 15.4 cubre la gestión.

### Dónde cambia esto lo que puedes construir

Las cuatro capas de defensa de la Sección 5.10 incluían «ofrecida, con puerta en ejecución». Esta es esa capa, y desbloquea toda una categoría de aplicación:

- Reembolsos por encima de un umbral
- Correos enviados a clientes en nombre de la empresa
- Cualquier borrado
- Publicar contenido
- Cualquier cosa con un requisito de visto bueno regulatorio

Sin interrupción, estas cosas están o totalmente automatizadas (inaceptable) o no automatizadas (sin valor). Con ella, la IA hace la preparación y un humano decide, lo que es a la vez seguro y útil.

### Puntos clave

- Pausa a mitad de nodo, preserva todo, reanuda con intervención humana.
- Cuatro fases: petición, pausa, decisión, reanudación.
- Sobrevive a la muerte del proceso y a esperas largas: esta es la funcionalidad distintiva.
- Se lanza como excepción para que se pueda interrumpir desde cualquier profundidad; debes capturarla.

## 15.2 interrupt() y ApprovalRequest

### La petición integrada

```php
namespace App\Neuron;

use NeuronAI\Workflow\Events\Event;
use NeuronAI\Workflow\Interrupt\Action;
use NeuronAI\Workflow\Interrupt\ApprovalRequest;
use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\WorkflowState;

class InterruptionNode extends Node
{
    public function __invoke(InputEvent $event, WorkflowState $state): OutputEvent
    {
        // Interrupt the workflow and wait for the feedback.
        $humanResponse = $this->interrupt(
            new ApprovalRequest(
                message: 'Should I continue?',
                actions: [
                    new Action('delete_file', 'Delete File', 'Delete /var/log/old.txt'),
                ],
            )
        );

        $action = $humanResponse->getAction('delete_file');

        if ($action->isApproved()) {
            $state->set('is_sufficient', true);
            $state->set('user_feedback', $action->feedback);

            return new OutputEvent();
        }

        $state->set('is_sufficient', false);

        return new InputEvent();
    }
}
```

### Leerlo

**`$this->interrupt($request)`** — la pausa. La ejecución se detiene aquí en la primera pasada y continúa aquí al reanudarse, con la respuesta del humano como valor de retorno.

**`ApprovalRequest`** — la implementación integrada, que cubre el caso más común: aprobar acciones como llamadas a herramientas.

**`Action`** — un único elemento decidible: un identificador, una etiqueta y una descripción. Varias acciones en una misma petición significa que el humano decide varias cosas en una sola interacción, que es la diferencia entre una pantalla de aprobación y cinco.

**`$humanResponse->getAction('delete_file')`** — recupera la decisión por identificador.

**`isApproved()` y `->feedback`** — aprobado o no, más el texto libre que el humano añadió. Ese campo de realimentación es más útil de lo que parece: un rechazo con motivo puede ir directo a la siguiente llamada del agente como orientación, convirtiendo «no» en «no, porque X» y permitiendo que el bucle mejore de verdad.

**Devolver `InputEvent` al rechazar** — este nodo vuelve atrás. El rechazo no es un fallo; es otra iteración. Esa combinación de interrupción más bucle es el patrón de refinamiento con humano en el circuito, y es lo que construye el Laboratorio 10.

::: {.callout .callout-warning}
[Errores de sintaxis en los ejemplos publicados]{.callout-title}

A varios ejemplos de `ApprovalRequest` de la documentación les falta la coma tras `message:`, y al ejemplo de `ContentReviewInterrupt` de la Sección 15.3 le falta un punto y coma tras `parent::__construct($message)` y pasa un argumento posicional después de uno con nombre. Los tres son fallos de copiar y pegar más que diferencias de API. Apéndice A, puntos 34 a 36.
:::

### Guía de diseño para las peticiones de aprobación

**Escribe el mensaje para quien decide, no para el desarrollador.** Lo están viendo en un correo o en una pantalla de administración, sin contexto. `'Should I continue?'` es un mal mensaje. `'Approve a €240 refund for order #4471 — customer reports item arrived damaged'` permite decidir sin abrir otro sistema.

**Incluye en la descripción lo suficiente para decidir.** El tercer argumento de `Action` es donde va la sustancia.

**Agrupa las decisiones relacionadas en una sola petición.** Cinco acciones en una petición gana a cinco interrupciones sucesivas, cada una de las cuales es un despertar, una notificación y una espera aparte.

### Puntos clave

- `$this->interrupt($request)` pausa y luego devuelve la respuesta del humano.
- `ApprovalRequest` más `Action` cubre aprobar/rechazar con realimentación.
- `isApproved()` y `->feedback`; la realimentación puede guiar la siguiente iteración.
- Escribe los mensajes para quien decide; agrupa las decisiones relacionadas.

## 15.3 Peticiones de interrupción propias

### Por qué aprobar/rechazar no siempre basta

`ApprovalRequest` cubre «¿debería hacer esta acción?». No cubre «aquí tienes un borrador: edítalo antes de que lo guarde», ni «elige una de estas tres opciones», ni «rellena el campo que falta».

La arquitectura es deliberadamente abierta: extiende la clase abstracta `InterruptRequest` para crear experiencias de interrupción a medida.

### La implementación

```php
class ContentReviewInterrupt extends InterruptRequest
{
    public function __construct(
        protected string $message,
        protected string $content
    ) {
        parent::__construct($message);
    }

    public function getContent(): string
    {
        return $this->content;
    }

    public function jsonSerialize(): array
    {
        return [
            'message' => $this->message,
            'content' => $this->content,
        ];
    }

    public static function fromArray(array $data)
    {
        return new static($data['message'], $data['content']);
    }
}
```

Tres responsabilidades:

**Llevar los datos** que el humano necesita para decidir, más lo que vaya a editar.

**`jsonSerialize()`** — para que pueda almacenarse y enviarse a un frontend. Fíjate en la implicación: tu interrupción cruza una frontera JSON. Mantenla serializable y plana.

**`fromArray()`** — reconstruirla a partir de los datos editados en el camino de vuelta.

Ese viaje de ida y vuelta —objeto PHP → JSON → interfaz → JSON editado → objeto PHP— es todo el ciclo de vida, y conocerlo es saber dónde encaja tu frontend.

### Usarla

```php
class InterruptionNode extends Node
{
    public function __invoke(InputEvent $event, WorkflowState $state): OutputEvent
    {
        // Generate an article
        $response = ContentCreatorAgent::make()
            ->chat(new UserMessage($event->prompt))
            ->getMessage();

        // Interrupt the workflow and wait for the feedback.
        $reviewRequest = $this->interrupt(
            new ContentReviewInterrupt(
                message: 'This is the new article. Review the content before saving it to the database.',
                content: $response->getContent()
            )
        );

        // Save the content of the updated interrupt request
        $state->set('content', $reviewRequest->getContent());

        return new InputEvent();
    }
}
```

### El patrón que merece un nombre

El agente generó contenido. El humano lo **editó**. El flujo de trabajo guardó la versión **editada**.

Eso no es aprobación: es colaboración. La IA produce un borrador, el humano lo corrige, el sistema usa la versión corregida. Para generación de contenidos, redacción de documentos, sugerencias de código y extracción de datos, esto es mejor producto que aprobar/rechazar, porque el caso común es «casi bien» y no «sí o no».

Como principio de diseño: **cuando la respuesta humana probable sea «casi, pero cambia esto», construye una interrupción editable en lugar de una aprobación.**

::: {.callout .callout-warning}
[Este ejemplo genera contenido antes de interrumpir]{.callout-title}

Que es exactamente la situación de la que trata la Sección 15.5. Tal y como está escrito, reanudar este nodo vuelve a ejecutar `ContentCreatorAgent` y la edición del humano se aplica a un borrador *distinto*. Lee la Sección 15.5 antes de publicar nada con esta forma.
:::

### Diseño de las peticiones de interrupción

- Incluye todo lo necesario para decidir. El humano no debería tener que abrir otro sistema.
- Mantenla plana y serializable: se convierte en JSON.
- Incluye una referencia estable a lo que se está decidiendo (un ID), para poder detectar una petición obsoleta.
- Considera la caducidad. Una petición de aprobación que aparece tres semanas después puede estar respondiendo a una pregunta que ya no aplica.

### Puntos clave

- Extiende `InterruptRequest` para cualquier cosa más allá de aprobar/rechazar.
- `jsonSerialize()` a la ida, `fromArray()` a la vuelta: la petición cruza una frontera JSON.
- La petición editada es la que recibe el nodo, lo que permite colaboración y no solo control de paso.
- Cuando la respuesta suele ser «casi», hazla editable.

## 15.4 Capturar, persistir y reanudar

### La persistencia es obligatoria

```php
$workflow = new WorkflowAgent(new FilePersistence(__DIR__));
```

> Para poder interrumpir y reanudar un Workflow (también Agent y RAG) necesitas proporcionar la capa de persistencia al crear la instancia del Workflow.

Sin persistencia no hay reanudación. Esto es lo primero que hay que hacer bien.

### Capturar la interrupción

```php
$workflow = new WorkflowAgent(
    new FilePersistence(__DIR__),
);

try {
    return $workflow->init()->run();
} catch (WorkflowInterrupt $interrupt) {
    $request    = $interrupt->getRequest();
    $workflowId = $interrupt->getWorkflowId();

    /*
    * You can store the request as a json object
    * along with the resume token, and ask the user for a feedback.
    */
    $pdo->prepare("INSERT INTO interruption_requests (resume_token, request) VALUES (?, ?)");
    $pdo->execute([
        $workflowId,
        json_encode($request),
    ]);
}
```

De la excepción salen dos cosas:

- **`getRequest()`** — qué mostrarle al humano.
- **`getWorkflowId()`** — el token de reanudación. Sin él no puedes reanudar.

El framework ya ha persistido el estado de ejecución. Lo que almacenas *tú* es la petición y el token, para que tu aplicación pueda encontrar la decisión pendiente, presentarla y reconectar la respuesta.

### Reanudar

```php
$workflow = new WorkflowAgent(
    new FilePersistence(__DIR__),
    $workflowId // <- Use the same ID you got during interruption
);

$request = ContentReviewInterrupt::fromArray($data);

// Resume the Workflow passing the processed request as the feedback
$result = $workflow->init($request)->run();

// Get the final answer
echo $result->get('content');
```

Tres requisitos:

1. **La misma capa de persistencia.**
2. **El mismo ID de flujo de trabajo.**
3. **La petición reconstruida**, que lleva la decisión del humano, pasada a `init()`.

### Persistencia en base de datos

```php
use NeuronAI\Workflow\Persistence\DatabasePersistence;

$workflow = new WorkflowAgent(
    new DatabasePersistence(
        pdo: new \PDO(...),
        table: 'workflow_interrupts'
    ),
    'CUSTOM_ID'
);
```

**MySQL / MariaDB:**

```sql
CREATE TABLE IF NOT EXISTS workflow_interrupts (
    workflow_id VARCHAR(255) PRIMARY KEY,
    data LONGBLOB NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_workflow_id (workflow_id),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**PostgreSQL:**

```sql
CREATE TABLE workflow_interrupts (
    workflow_id VARCHAR(255) PRIMARY KEY,
    data BYTEA NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_workflow_id ON workflow_interrupts(workflow_id);
CREATE INDEX idx_updated_at ON workflow_interrupts(updated_at);
```

Lee el esquema con atención, porque te dice qué está pasando: `LONGBLOB` / `BYTEA` es todo el estado de ejecución serializado, en binario. Y `idx_updated_at` existe para que puedas encontrar interrupciones obsoletas, que es tu historia de limpieza.

Usa `FilePersistence` para CLI y desarrollo. Usa `DatabasePersistence` para cualquier cosa multiservidor o de producción.

### Las cuatro preguntas operativas

Ningún tutorial las cubre y todo sistema de producción las necesita.

**1. ¿A quién se notifica?** La interrupción no envía un correo. Lo hace tu código. Conecta la notificación en el bloque catch.

**2. ¿Y si nadie responde?** Las interrupciones se acumulan. Necesitas una política de tiempo de espera: escalar, hacer caducar o rechazar automáticamente. `idx_updated_at` está ahí para esa consulta.

**3. ¿Cómo evitas la doble reanudación?** Dos responsables abren el mismo enlace de aprobación y ambos pinchan. Marca la petición como resuelta de forma atómica antes de reanudar.

**4. ¿Y si hay un despliegue en medio?** El estado serializado contiene tus clases. Un despliegue que renombre una clase o cambie una property romperá la deserialización de las interrupciones en vuelo. O bien vacías antes de desplegar, o versionas tus peticiones de interrupción.

Esa última es la arista afilada, y merece detenerse en ella. Los objetos PHP serializados de larga vida a través de despliegues son un problema difícil conocido, y la interrupción te mete de lleno en él. La mitigación —mantén las peticiones de interrupción pequeñas, planas y cámbialas rara vez— es una regla de diseño, no algo que descubrir durante un incidente.

### Puntos clave

- La persistencia es obligatoria para la interrupción; `FilePersistence` para CLI, `DatabasePersistence` para producción.
- Captura `WorkflowInterrupt`; almacena `getRequest()` y `getWorkflowId()`.
- Reanuda con la misma persistencia, el mismo ID y la petición reconstruida.
- Cuatro preguntas operativas: notificación, tiempo de espera, doble reanudación, compatibilidad con los despliegues.

## 15.5 Puntos de control, interrupciones condicionales y middleware

### El problema de la reejecución

Esta sección contiene la advertencia de corrección más importante del libro.

> Cuando el Workflow se reanuda, reinicia la ejecución **desde el nodo en el que fue interrumpido. El nodo se reejecutará por completo, incluido el código anterior a la interrupción.**

Léelo con atención, porque tiene un coste real. Si tu nodo llama a un LLM, luego interrumpe y luego se reanuda, **la llamada al LLM se ejecuta otra vez.** Pagas dos veces, esperas dos veces y, por la Sección 1.5, puedes obtener una *respuesta distinta* la segunda vez.

Lo que significa que el humano aprobó una cosa y el flujo de trabajo procede con otra.

Eso no es desperdicio. Es un error de corrección y, en un contexto regulado, un fallo de auditoría. Tiene una solución de una línea.

### Puntos de control

```php
class InterruptionNode extends Node
{
    public function __invoke(InputEvent $event, WorkflowState $state): OutputEvent
    {
        // The result of this code block is saved and returned when the workflow is resumed.
        $sentiment = $this->checkpoint('agent-1', function () {
            return MyAgent::make()->structured(
                new UserMessage(...),
                SentimentResult::class
            );
        });

        // Interrupt the workflow and wait for the feedback.
        if ($sentiment->isNegative()) {
            $feedback = $this->interrupt(
                new ApprovalRequest(
                    message: 'Should I continue?',
                    actions: [
                        new Action('review_id', 'Answer review', $sentiment->content),
                    ],
                )
            );

            if ($feedback->getAction('review_id')->isApproved()) {
                $state->set('is_sufficient', true);
                $state->set('user_feedback', $feedback->getAction('review_id')->feedback);

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

Primera ejecución: la función anónima se ejecuta y su resultado se almacena. Tras la reanudación: se devuelve el resultado almacenado sin reejecutar.

La formulación de la documentación es precisa: el nodo llega al punto de interrupción *con exactamente el mismo estado que en la ejecución anterior*.

**La regla: cualquier llamada a un LLM, cualquier llamada a una API de pago y cualquier cosa no determinista que preceda a un `interrupt()` en el mismo nodo pertenece dentro de un `checkpoint()`.** No hay excepciones que merezca la pena aprender.

### consumeResumeRequest()

A veces quieres ramificar en la *cabecera* de un nodo según si te estás reanudando:

```php
class InterruptionNode extends Node
{
    public function __invoke(InputEvent $event, WorkflowState $state): OutputEvent
    {
        // Ask for the final resume request
        $feedback = $this->consumeResumeRequest();

        // If the request is not there yet, jump to the interruption
        if ($feedback !== null && $feedback->getAction('review_id')->isApproved()) {
            $state->set('is_sufficient', true);
            $state->set('user_feedback', $feedback->getAction('review_id')->feedback);

            return new OutputEvent();
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

Devuelve la realimentación, o `null` si el nodo se está ejecutando con normalidad en lugar de despertando. Te permite gestionar el caso de reanudación explícitamente al principio en vez de volver a recorrer el cuerpo entero del nodo: una forma más limpia cuando el nodo hace trabajo sustancial antes de la interrupción.

### interruptIf()

```php
// Conditional interruption
$this->interruptIf(
    $state->get('is_sufficient') == true,
    new ApprovalRequest(
        message: 'Should I continue?',
        actions: [
            new Action('review_id', 'Answer review', $state->get('review')),
        ],
    )
);

// Or use a callback to evaluate the condition
$this->interruptIf(
    fn() => $state->get('is_sufficient', false),
    new ApprovalRequest(
        message: 'Should I continue?',
        actions: [
            new Action('review_id', 'Answer review', $state->get('review')),
        ],
    )
);
```

La forma con callback importa: difiere la evaluación y evita construir la petición cuando la condición es falsa.

**El argumento de producto a favor de la interrupción condicional:** si toda acción necesita aprobación, los humanos dejan de leer y empiezan a pinchar. Interrumpe solo en los casos que lo merecen —por encima de un umbral, por debajo de una puntuación de confianza, fuera de los parámetros normales— y las aprobaciones seguirán significando algo.

### Middleware ToolApproval

La misma idea aplicada a las llamadas a herramientas, sin escribir un nodo:

```php
Neuron::middleware(ToolNode::class, new ToolApproval())
    ->chat(new UserMessage('Delete the oldest log file'));
```

Condicionado a los argumentos:

```php
new ToolApproval(
    tools: [
        BuyTicketTool::class => function (array $args): bool {
            return $args['amount'] > 100;
        }
    ]
)
```

Las compras por debajo de 100 € proceden; las mayores esperan a un humano. Esta es la cuarta capa de la Sección 5.10, ahora concreta, y es un producto mucho mejor que permitir siempre o bloquear siempre.

Fíjate en la forma: `middleware(ToolNode::class, ...)`. La Sección 2.3 decía que los nombres de nodo son API pública. Por esto.

### ToolSearchMiddleware

```php
new ToolSearchMiddleware([...])
```

Para agentes con catálogos de herramientas grandes. En lugar de enviar todos los esquemas en cada petición —el coste acumulativo de la Sección 1.3—, selecciona dinámicamente las herramientas relevantes.

Esta es la respuesta a «¿y si tengo 200 herramientas?», que es la pregunta natural después del Capítulo 5.

### Puntos clave

- **Un nodo reanudado se reejecuta desde el principio**, incluidas las llamadas al LLM, con resultados posiblemente distintos.
- `checkpoint('name', fn)` guarda y reproduce; envuelve todo lo caro o no determinista que preceda a una interrupción.
- `consumeResumeRequest()` ramifica según si estás despertando.
- `interruptIf()` mantiene el significado de las aprobaciones; la forma con callback difiere la evaluación.
- `ToolApproval` pone puertas a las llamadas a herramientas condicionadas a los argumentos; `ToolSearchMiddleware` gestiona catálogos grandes.
