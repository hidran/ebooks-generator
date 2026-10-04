# Capítulo 2 — La arquitectura de NeuronAI

::: {.callout .callout-tip}
[El código de este capítulo]{.callout-title}

Este capítulo es conceptual y no tiene código propio, pero el repositorio complementario [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) contiene versiones ejecutables de todo lo que el libro construye.
:::

## 2.1 Los cuatro pilares

Todo el framework te cabe en la cabeza como cuatro conceptos. Colocarlos ahora hace que cada capítulo posterior tenga dónde engancharse.

### Instalación, a modo de orientación

```bash
composer require neuron-core/neuron-ai:^4.0.3
```

Requisitos: la extensión `curl`, y muy poco más: el framework habla HTTP a través de su propio cliente basado en curl. El paquete en sí funciona con PHP 8.1 o posterior; el código de este libro necesita PHP 8.5 (el Capítulo 3 explica por qué). El SDK de Laravel se trata en la Parte V, donde el libro usa Laravel 13 sobre PHP 8.5.

### Pilar 1 — Agent

El bucle de llamada a herramientas de la Sección 1.2, implementado y protegido. Extiendes una clase base, declaras qué proveedor usar, cuáles son las instrucciones y qué herramientas están disponibles. NeuronAI ejecuta el bucle, gestiona el array de mensajes, maneja el despacho de herramientas y aplica los límites de ejecución.

Esto es el peldaño 4 de la Sección 1.1, listo para usar.

### Pilar 2 — Workflow

Un grafo guiado por eventos. Defines nodos; cada nodo recibe un evento y devuelve un evento; el tipo de evento devuelto determina qué nodo se ejecuta después. Encima de eso: estado compartido, ramificación, bucles y **ejecución duradera**: con un almacén de persistencia configurado, cada paso completado queda registrado, así que una ejecución puede pausarse a la espera de una entrada humana o de un evento externo y reanudarse días después en otro proceso, y una ejecución cuyo proceso se cayó continúa tras su último paso completado en lugar de empezar de cero.

Esto es el peldaño 3 hecho como es debido, y es además el sustrato de los sistemas multiagente.

### Pilar 3 — RAG

El pipeline de recuperación: cargadores de datos para ingerir, un proveedor de incrustaciones para vectorizar, un almacén vectorial para guardar y buscar, procesadores previos y posteriores para mejorar las consultas y reordenar los resultados, y una clase `RAG` que lo ata todo en un agente que responde a partir de tus documentos.

### Pilar 4 — Observabilidad

Cada agente y cada flujo de trabajo emite un flujo de eventos mientras se ejecuta —un nodo empezó, una inferencia comenzó y terminó, se llamó a una herramienta y respondió, una ejecución se interrumpió— como eventos PSR-14 estándar. Tú te suscribes a ellos: Inspector, construido por el mismo equipo, los convierte en trazas; tu propio logger o el sistema de eventos de tu framework también pueden recibirlos. Dada la Sección 1.5, esto no es un detalle agradable de monitorización. Sin una traza no puedes responder a «¿por qué hizo eso?», y «¿por qué hizo eso?» es la única pregunta que llegarás a hacerte.

### La imagen mental

```
                   ┌─────────────────────────┐
                   │       WORKFLOW          │
                   │  (nodos, eventos,       │
                   │   estado, bucles,       │
                   │   interrupción)         │
                   │                         │
                   │   ┌───────┐  ┌───────┐  │
                   │   │ AGENT │  │  RAG  │  │
                   │   └───────┘  └───────┘  │
                   └─────────────────────────┘
                                │
       ┌────────────┬───────────┼───────────┬────────────┐
  Proveedores Herramientas   Memoria    Almacenes Incrustaciones
                                │
                         OBSERVABILIDAD
```

Workflow es el contenedor exterior. Agent y RAG son configuraciones prefabricadas que viven dentro de él. Por debajo, un conjunto de componentes intercambiables. Transversalmente, el trazado.

### Puntos clave

- Cuatro pilares: Agent, Workflow, RAG, Observabilidad.
- Workflow es el caso general; Agent y RAG son especializaciones.
- La observabilidad es un pilar, no un añadido, a causa del no determinismo.

## 2.2 Todo es una interfaz

Una sola decisión de diseño explica la mayor parte de la forma de NeuronAI, y te da más palanca práctica que ninguna funcionalidad concreta.

### Las cinco interfaces que importan

La arquitectura de NeuronAI es un pequeño conjunto de contratos que toda implementación concreta respeta:

| Interfaz | Responsabilidad | Implementaciones de ejemplo |
|---|---|---|
| `AIProviderInterface` | Hablar con un LLM | Anthropic, OpenAI, Gemini, Mistral, Ollama, DeepSeek, Bedrock, Azure |
| `ToolInterface` | Dar una capacidad al agente | Tus clases, juegos de herramientas integrados, herramientas servidas por MCP |
| `MessageStoreInterface` | Guardar los mensajes de la conversación | InMemory, File, SQL, Eloquent |
| `EmbeddingsProviderInterface` | Convertir texto en vectores | OpenAI, Voyage, Ollama |
| `VectorStoreInterface` | Guardar, filtrar y buscar vectores | Memory, File, MariaDB, MongoDB Atlas, Pinecone, Weaviate, Elasticsearch, OpenSearch, Typesense, Qdrant, ChromaDB, Meilisearch |

El código de tu aplicación depende de la interfaz. Nunca de la implementación.

::: {.callout .callout-warning}
[Nota de versión]{.callout-title}

Esa lista de almacenes vectoriales es el conjunto completo de implementaciones de primera parte, y vale la pena leerla con atención porque **NeuronAI no incluye un almacén pgvector**. Bastante material de terceros —incluidos tutoriales y programas de cursos derivados del ecosistema Python, donde pgvector es omnipresente— da por hecho que sí. Si quieres una ergonomía al estilo Postgres, la respuesta de primera parte más cercana es **MariaDB 11.7+**, que te da búsqueda vectorial en una base de datos que probablemente ya estés ejecutando; el Capítulo 12 se apoya en ella. **PHPVector**, un almacén en PHP puro sin nada de infraestructura, vive en un paquete aparte con su propio ciclo de publicación, y no tenía ninguna versión para NeuronAI v4 cuando este libro entró en imprenta; el Capítulo 12 explica cómo comprobarlo.
:::

### Cómo se ve esto en la práctica

```php
protected function provider(): AIProviderInterface
{
    return new Anthropic(
        key: 'ANTHROPIC_API_KEY',
        model: 'ANTHROPIC_MODEL',
    );
}
```

Cambia a un modelo alojado en local:

```php
protected function provider(): AIProviderInterface
{
    return new Ollama(
        url: 'OLLAMA_URL',
        model: 'OLLAMA_MODEL',
    );
}
```

No cambia nada más. Ni las instrucciones, ni las herramientas, ni el historial, ni el código que llama. En la Sección 3.6 llevamos esto más lejos y dirigimos la elección enteramente desde una variable de entorno.

### Por qué esto es una capacidad estratégica y no una comodidad

Cuatro consecuencias que conviene nombrar explícitamente, porque son la forma de justificar el framework ante quien decide:

**Escalonado de costes.** Enruta la clasificación y la extracción a un modelo barato y rápido; enruta la síntesis final a uno caro. Esta es la tercera palanca de la Sección 1.4, y la interfaz es lo que la convierte en un cambio de una línea en lugar de una refactorización.

**Riesgo de proveedor.** Hay caídas, los precios cambian, las condiciones cambian. Una dependencia rígida del SDK de un solo proveedor es un riesgo de negocio. Una interfaz es una salida.

**Desarrollo local.** Ejecuta Ollama en tu portátil y desarrolla gratis todo lo de este libro. Despliega contra un proveedor en la nube. El mismo código.

**Residencia de los datos.** Un cliente que no puede enviar datos fuera de la UE, o fuera de su propio edificio, es un cambio de configuración y no una reescritura.

### El compromiso, dicho con honestidad

Una abstracción sobre varios proveedores converge hacia su subconjunto común. Las funcionalidades específicas de un proveedor —modos de pensamiento extendido, herramientas nativas de búsqueda web, ajustes de seguridad concretos— o se exponen mediante vías de escape o no están disponibles. La respuesta de NeuronAI es `ProviderTool`, que te permite usar las herramientas integradas de un proveedor (la API OpenAI Responses, Gemini, Anthropic y ZAI las soportan), pero la propia documentación del framework es franca al señalar que las herramientas de proveedor introducen restricciones y que el sistema portable de Herramientas y Juegos de herramientas sigue siendo la vía más flexible.

Ten claro qué estás intercambiando. La portabilidad cuesta, durante un tiempo, el acceso a la funcionalidad más nueva de cada proveedor.

### Puntos clave

- Cinco interfaces: proveedor, herramienta, almacén de mensajes, incrustaciones, almacén vectorial.
- Depende de la interfaz; la implementación es configuración.
- La recompensa es el escalonado de costes, el riesgo de proveedor, el desarrollo local gratuito y la residencia de los datos.
- El coste es el acceso diferido a las funcionalidades específicas de cada proveedor.

## 2.3 La idea clave: Agent y RAG *son* flujos de trabajo

Esta es la sección más importante del capítulo. Es la idea unificadora central del framework, la documentación oficial la revela tarde, y explica muchísimas cosas que de otro modo parecerían arbitrarias.

### El enunciado

`Agent` y `RAG` no son sistemas aparte que se sientan al lado de `Workflow`. **Son flujos de trabajo.** Son grafos de nodos preensamblados que implementan los dos patrones agénticos más comunes.

La propia documentación de NeuronAI lo dice directamente: las clases Agent y RAG son flujos de trabajo en sí mismas, y representan implementaciones listas para usar de los patrones más comunes de llamadas a herramientas, recuperación y salida estructurada.

### Qué significa eso en concreto

`Agent` extiende `Workflow`, literalmente: abre `vendor/neuron-core/neuron-ai/src/Agent/Agent.php` y la declaración de la clase lo dice. Cuando llamas a `->chat()` en un agente, estás ejecutando un flujo de trabajo cuyos nodos son:

- `AgentStartNode` — ensambla la petición: instrucciones, mensajes, opciones de la ejecución
- `ChatNode` — llama al LLM; `->stream()` pasa por el mismo nodo, que simplemente transmite la respuesta
- `StructuredOutputNode` — llama al LLM cuando pides un resultado tipado
- `ToolNode` — ejecuta las herramientas que pidió el modelo, pausándose antes a la espera de una decisión humana cuando una herramienta requiere aprobación, y luego vuelve a la inferencia
- `AgentEndNode` — termina la ejecución cuando el modelo da una respuesta final

`ChatNode` y `StructuredOutputNode` comparten una clase base, `InferenceNode`: «allí donde se llama al modelo».

Esos nombres de nodo no son trivia interna. Son parte de la superficie pública. Enganchas middleware a un agente nombrando la clase de nodo que debe envolver. Aquí un middleware de resumen se ejecuta antes de cada llamada al modelo, de chat o estructurada, y, cuando la conversación supera un presupuesto de tokens, sustituye los turnos más antiguos por un resumen:

```php
$agent = SupportAgent::make(workflowId: $threadId)
    ->addMiddleware(InferenceNode::class, new Summarization(
        provider: $cheapProvider,
        maxTokens: 20_000,
    ));

$state = $agent->chat(new UserMessage('Summarise my last three tickets'));
```

No puedes usar esa API sin saber que `chat()` está respaldado por nodos. Precisamente por eso esto pertenece al Capítulo 2 y no al 15.

El valor de retorno cuenta la misma historia. `chat()` no devuelve un mensaje; ejecuta el flujo de trabajo hasta el final y devuelve su estado final, un `AgentState`, que extiende el `WorkflowState` que devuelve todo flujo de trabajo. La respuesta del asistente es una de las cosas que lees de él (Sección 3.4).

### Las tres consecuencias

**1. Todo lo que aprendas sobre flujos de trabajo se aplica a los agentes.**
Middleware, estado, transmisión, interrupción, persistencia: son funcionalidades de flujo de trabajo, y los agentes las heredan todas. Cuando llegues al Capítulo 15 y aprendas el humano en el circuito, no estarás aprendiendo una funcionalidad separada de los agentes: una herramienta que necesita aprobación hace que `ToolNode` interrumpa la ejecución, exactamente como puede hacerlo cualquier nodo de un flujo de trabajo, y aprobarla reanuda la ejecución. Incluso la identidad de la conversación es un concepto de flujo de trabajo. El ID de hilo que le das a un agente (el argumento `workflowId:` de arriba; Capítulo 4) *es* el ID del flujo de trabajo de la ejecución. El framework nunca inventa uno —un agente sin ID se niega a ejecutarse— y, a cambio, un punto de conexión que no tenga más que el ID de hilo puede encontrar una ejecución en pausa y reanudarla.

**2. No hay un segundo framework cuando el proyecto crece.**
La trayectoria habitual con otras pilas es: prototipar con la abstracción simple, chocar contra su techo y reescribir contra la abstracción de grafo. Aquí, `Agent` *es* la abstracción de grafo con una configuración por defecto. Crecer significa añadir nodos, no migrar.

**3. Puedes usar un Agent como nodo dentro de un Workflow mayor.**
Esta es la historia multiagente, y no necesita ninguna API multiagente especial. Un agente investigador es un nodo. Un agente redactor es un nodo. Un árbitro es un nodo. Compónlos con eventos. El Capítulo 16 hace exactamente esto.

### La regla de decisión

**Extiende `Agent`** cuando tu problema sea «una entidad, un objetivo, algunas herramientas, iterar hasta terminar». Eso es la mayoría de los asistentes de propósito único.

**Construye un `Workflow`** cuando necesites: control sobre el orden de los pasos, varios agentes especializados, ramificación o bucles escritos por ti, puntos de control, o una pausa para la intervención humana.

**Extiende `RAG`** cuando el trabajo central sea responder a partir de un corpus documental.

Y cuando dudes: empieza con `Agent`. Migrar más adelante a un flujo de trabajo es aditivo, porque siempre fue un flujo de trabajo.

::: {.callout .callout-tip}
[En la práctica]{.callout-title}

Si te llevas una sola frase de la Parte I a la Parte IV, llévate esta. Quienes se la saltan viven los flujos de trabajo como un tema nuevo e inconexo a mitad del libro; quienes la tienen viven los flujos de trabajo como *«ah, así que esto es lo que había debajo del agente todo el tiempo»*.
:::

### Puntos clave

- `Agent` y `RAG` son flujos de trabajo configurados, no sistemas paralelos; `chat()` devuelve el estado final del flujo de trabajo.
- Las clases de nodo (`ChatNode`, `StructuredOutputNode`, su base `InferenceNode`, `ToolNode`) son API pública: el middleware apunta a ellas.
- Las funcionalidades de flujo de trabajo —interrupción, persistencia duradera, identidad— las heredan los agentes; el ID de hilo de una conversación es su ID del flujo de trabajo.
- Lo multiagente no necesita API especial: un agente no es más que un nodo.

## 2.4 Extender o componer: elegir tu estructura

Tres patrones estructurales, una regla de decisión y —algo importante— un camino de migración entre ellos que no implica reescribir.

### Patrón A — Extender la clase Agent

El patrón por defecto, y el correcto para la gran mayoría de los casos.

```php
namespace App\Neuron;

use NeuronAI\Agent\Agent;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Providers\Anthropic\Anthropic;

class SupportAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return new Anthropic(key: '...', model: '...');
    }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: ['You are a customer support assistant.'],
        );
    }

    protected function tools(): array
    {
        return [ /* ... */ ];
    }
}
```

Tres métodos plantilla —`provider()`, `instructions()`, `tools()`— más los opcionales `messageStore()` y `contextWindow()`, y cada uno tiene un setter gemelo (`setAiProvider()`, `setInstructions()`, `setTools()`, `setMessageStore()`, `setContextWindow()`) que prevalece sobre el método cuando lo llamas. Todo lo demás se hereda. La clase es una declaración de *qué es este agente*, y se lee como configuración porque lo es.

**Por qué vale la pena defender este patrón.** La clase se convierte en una unidad con nombre, testeable e inyectable. `SupportAgent` puede registrarse en un contenedor de servicios, simularse en pruebas y razonarse por parte de un colega que nunca ha visto el framework. Ese es un beneficio arquitectónico real frente a esparcir configuración fluida por los controladores.

### Patrón B — Configuración fluida en el punto de llamada

Para ejecuciones puntuales y experimentos:

```php
$state = SupportAgent::make(workflowId: $threadId)
    ->toolMaxRuns(5)
    ->addTool(SomeExtraTool::make())
    ->chat(new UserMessage('...'));
```

Úsalo para variaciones por petición sobre una clase ya declarada: una herramienta que solo aparece para administradores, un límite de ejecuciones más bajo para un punto de conexión barato. No lo uses como sustituto de tener una clase: la configuración ensamblada en línea dentro de un controlador es configuración que nadie encontrará dentro de seis meses.

### Patrón C — Componer un Workflow a partir de componentes

Cuando quieres un flujo de control escrito por ti, usas los componentes de NeuronAI como piezas autónomas. La documentación es explícita: proveedores, incrustaciones, cargadores de datos, historial de conversación y almacenes vectoriales pueden usarse todos como componentes autónomos para construir entidades agénticas totalmente a medida.

```php
$state = Workflow::make(workflowId: $runId)
    ->addNodes([
        new ClassifyNode(),
        new RetrieveNode(),
        new AnswerNode(),
    ])
    ->run();
```

Aquí la secuencia la escribiste *tú*. El modelo rellena los pasos. Como un agente, un flujo de trabajo se ejecuta bajo un ID que tú proporcionas: `workflowId:` es la dirección de la ejecución, y el framework nunca inventa uno. `run()` ejecuta el grafo y devuelve el `WorkflowState` final: el mismo verbo y el mismo tipo de resultado que te da un agente, porque un agente es esto. Esto es el peldaño 3 de la Sección 1.1, con persistencia duradera e interrupción disponibles cuando hagan falta.

### El camino de migración

La razón por la que esta decisión es de bajo riesgo: pasar del Patrón A al Patrón C es aditivo. Como `SupportAgent` ya es un flujo de trabajo, promoverlo significa envolverlo como nodo dentro de un grafo mayor, no reescribirlo.

```php
class SupportNode extends Node
{
    public function __invoke(QuestionEvent $event, WorkflowState $state): ResolvedEvent
    {
        $answer = SupportAgent::make(workflowId: $event->threadId)
            ->chat(new UserMessage($event->question))
            ->getMessage();

        return new ResolvedEvent($answer?->getContent());
    }
}
```

`QuestionEvent` y `ResolvedEvent` son tus propias clases de evento; la primera lleva la pregunta y el ID de hilo de la conversación a la que pertenece. Los tipos del parámetro y del valor de retorno del nodo son lo que lo conecta al grafo. Tu agente no cambia. Ahora es un componente de algo mayor.

### Puntos clave

- Extiende `Agent` por defecto; la clase es una unidad con nombre, inyectable y testeable.
- Configuración fluida para variaciones por petición, no como sustituto de una clase.
- Compón un `Workflow` cuando escribas tú el flujo de control.
- La promoción de A a C es aditiva: envuelve, no reescribas.

## 2.5 El ecosistema alrededor del framework

Una orientación breve, para que no reconstruyas cosas que ya vienen incluidas y sepas qué piezas usa realmente este libro.

### Inspector

Construido por el mismo equipo, y la razón por la que la observabilidad es un pilar. No viene incluido: el propio framework no depende de nada más que de las interfaces PSR-14, así que instalas el paquete de Inspector (`inspector-apm/inspector-php`, 3.19 o posterior), defines su clave

```dotenv
INSPECTOR_INGESTION_KEY=your-key-here
```

y suscribes su oyente, `InspectorSubscriber`, a los agentes y flujos de trabajo que quieras trazar. A partir de ahí cada ejecución aparece como una línea temporal: qué nodo se ejecutó, qué herramienta se llamó con qué argumentos, qué volvió, cuántos tokens, cuánto tiempo. Nada se engancha implícitamente: un agente al que no suscribiste es un agente que no puedes ver, y eso merece una línea en tu lista de comprobación de revisión de código.

Lo conectamos en el Capítulo 10 y lo usamos otra vez en el 23. Dada la Sección 1.5, planifica algún tipo de visor de trazas desde el principio.

### Neuron Cloud

La plataforma de observabilidad alojada que el equipo de NeuronAI opera para el framework, y la que hoy recomiendan las propias indicaciones de la librería para el trazado en producción. Consume el mismo flujo de eventos: instalas `neuron-core/cloud-sdk` (o sus envoltorios `neuron-core/neuron-cloud-laravel` y `neuron-core/neuron-cloud-symfony`), le das una clave de API y una clave de firma, y suscribes su oyente exactamente igual que el de Inspector. Cada ejecución llega entonces como una única traza —nodos, inferencias, llamadas a herramientas, recuperación, salida estructurada— cosida a través de las pausas de una ejecución duradera. Elegir entre los dos cambia una llamada a `subscribe()` y nada en tus agentes. La Sección 10.2 dice qué comprobar antes de contar con ello.

### El SDK de Laravel

```bash
composer require neuron-core/neuron-laravel:^2.0 neuron-core/neuron-ai:^4.0.3
```

Toda la Parte V. Aporta un archivo de configuración, generadores de artisan (`neuron:agent`, `neuron:rag`, `neuron:tool`, `neuron:workflow`, `neuron:node`, `neuron:middleware`) y facades para proveedores y almacenes vectoriales. Las dos tablas que necesita un agente en producción —los mensajes del chat y el almacén de flujos de trabajo en el que persisten las ejecuciones duraderas— salen de una migración propia: las que incluye el SDK 2.0.0 no encajan con neuron-ai 4.0.3 (Sección 17.1).

Conviene subrayarlo: este paquete añade comodidad, no capacidad. Todo lo que hace podrías hacerlo a mano, que es exactamente por qué lo construimos a mano primero en las Partes II a IV.

### MCP — Model Context Protocol

Un protocolo abierto para exponer herramientas a sistemas de IA. NeuronAI incluye un conector MCP, de modo que las herramientas publicadas por cualquier servidor MCP pueden engancharse a un agente de NeuronAI como si fueran nativas. El Capítulo 9 lo cubre. Las implicaciones de seguridad tienen allí su propia discusión: un servidor MCP es código de terceros entrando en el bucle de tu agente.

### Maestro

Un framework de agentes de CLI de código abierto construido sobre NeuronAI, con llamada a herramientas y aprobaciones con humano en el circuito. Útil como implementación de referencia de una aplicación de producción completa, y buena fuente de ejercicios de lectura de código. Volvemos a él en el Capítulo 27.

### Neuron Hub

Un registro de extensiones y juegos de herramientas de la comunidad. Consúltalo antes de escribir una integración, y publica ahí las tuyas.

### Neuron Studio

Un paquete de la comunidad (`digitalelvis/neuronai-studio`) que ofrece un constructor visual de agentes para Laravel y exporta clases PHP reales. Útil para prototipar y para enseñar la arquitectura a quien no programa. Genera código; no sustituye el entenderlo.

### Panorama de versiones

Este libro apunta a **NeuronAI 4.0.3** y, para la Parte V, al **SDK de Laravel 2.x**, la línea de versiones construida para NeuronAI v4.

Buena parte del código de ejemplo que encontrarás en internet se escribió para versiones anteriores. Una parte tiene los mismos imports que este libro y falla más tarde, en un método que no existe o que devuelve otra cosa; otra parte usa namespaces antiguos (`NeuronAI\Agent` en lugar de `NeuronAI\Agent\Agent`) y falla en su primera instrucción `use`. Si una entrada de blog o una página de documentación no coincide con este libro, comprueba a qué versión apunta antes de depurar ninguna otra cosa.

::: {.callout .callout-warning}
[Las guías de actualización vienen con el paquete]{.callout-title}

NeuronAI pone sus notas de migración donde tu código puede alcanzarlas: `vendor/neuron-core/neuron-ai/upgrade/` contiene una guía numerada por cada cambio incompatible, cada una con el código de antes y de después y los patrones de `grep` que encuentran los puntos de llamada afectados. Cuando un fragmento de un tutorial antiguo se niega a funcionar, la respuesta suele estar en uno de esos archivos, y están más al día que el sitio de documentación, que va por detrás del código.

El Capítulo 27 convierte esto en una **estrategia de versiones**: cómo determinar qué tienes instalado realmente, cómo leer un changelog y una guía de actualización buscando cambios incompatibles y cómo fijar versiones para que una publicación de la biblioteca sea una decisión y no una caída. Antes de fiarte de cualquier afirmación sobre versiones —incluida esta— ejecuta `composer show neuron-core/neuron-ai --all`.
:::

### Ejercicio

Reproduce de memoria el diagrama de los cuatro pilares. Después, para el Proyecto final A («CLI auditora de repositorios», Capítulo 24) y el Proyecto final B («Servicio de soporte agéntico», Capítulo 25), enumera qué pilares y qué piezas del ecosistema esperas necesitar. Guarda la respuesta y compárala con lo que acabes construyendo; la diferencia es la realimentación más útil que este libro puede darte.

### Puntos clave

- La observabilidad es un flujo de eventos PSR-14; Inspector y Neuron Cloud son oyentes a los que suscribes explícitamente, no algo que se engancha solo.
- El SDK de Laravel para comodidad, no para capacidad.
- MCP trae herramientas externas, y con ellas código externo.
- Este libro apunta a NeuronAI 4.0.3 sobre PHP 8.5. El código escrito para versiones anteriores sigue llenando los resultados de búsqueda; comprueba la versión antes de depurar.
