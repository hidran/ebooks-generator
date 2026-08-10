# Capítulo 2 — La arquitectura de NeuronAI

## 2.1 Los cuatro pilares

Todo el framework te cabe en la cabeza como cuatro conceptos. Colocarlos ahora hace que cada capítulo posterior tenga dónde engancharse.

### Instalación, a modo de orientación

```bash
composer require neuron-core/neuron-ai
```

Requisitos: PHP 8.1 o posterior para el paquete core. El SDK de Laravel, cubierto en la Parte V, requiere PHP 8.2 y Laravel 10 o posterior.

### Pilar 1 — Agent

El bucle de llamada a tools de la Sección 1.2, implementado y protegido. Extiendes una clase base, declaras qué provider usar, cuáles son las instrucciones y qué tools están disponibles. NeuronAI ejecuta el bucle, gestiona el array de mensajes, maneja el despacho de tools y aplica los límites de ejecución.

Esto es el peldaño 4 de la Sección 1.1, listo para usar.

### Pilar 2 — Workflow

Un grafo event-driven. Defines nodos; cada nodo recibe un evento y devuelve un evento; el tipo de evento devuelto determina qué nodo se ejecuta después. Encima de eso: estado compartido, ramificación, bucles, checkpoints en almacenamiento, interrupción para entrada humana y reanudación, potencialmente días después.

Esto es el peldaño 3 hecho como es debido, y es además el sustrato de los sistemas multiagente.

### Pilar 3 — RAG

El pipeline de recuperación: data loaders para ingerir, un provider de embeddings para vectorizar, un vector store para guardar y buscar, procesadores previos y posteriores para mejorar las consultas y reordenar los resultados, y una clase `RAG` que lo ata todo en un agente que responde a partir de tus documentos.

### Pilar 4 — Observabilidad

Trazado de cada llamada al LLM, invocación de tool y recuperación, entregado a través de Inspector. Dada la Sección 1.5, esto no es un detalle agradable de monitorización. Sin un trace no puedes responder a «¿por qué hizo eso?», y «¿por qué hizo eso?» es la única pregunta que llegarás a hacerte.

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
   Providers      Tools    ChatHistory  VectorStores  Embeddings
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
| `ToolInterface` | Dar una capacidad al agente | Tus clases, toolkits integrados, tools servidos por MCP |
| `ChatHistoryInterface` | Guardar el estado de la conversación | InMemory, File, SQL, Eloquent |
| `EmbeddingsProviderInterface` | Convertir texto en vectores | OpenAI, Voyage, Ollama |
| `VectorStoreInterface` | Guardar y buscar vectores | Memory, File, PHPVector, MariaDB, Pinecone, Weaviate, Elasticsearch, OpenSearch, Typesense, Qdrant, ChromaDB, Meilisearch |

El código de tu aplicación depende de la interfaz. Nunca de la implementación.

::: {.callout .callout-warning}
[Nota de versión]{.callout-title}

Esa lista de vector stores es el conjunto completo de implementaciones de primera parte, y vale la pena leerla con atención porque **NeuronAI no incluye un store pgvector**. Bastante material de terceros —incluidos tutoriales y programas de cursos derivados del ecosistema Python, donde pgvector es omnipresente— da por hecho que sí. Si quieres una ergonomía al estilo Postgres, las respuestas de primera parte más cercanas son **PHPVector** (PHP puro, sin nada de infraestructura) y **MariaDB 11.7+**, que te da búsqueda vectorial en una base de datos que probablemente ya estés ejecutando. El Capítulo 12 usa ambas.
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

No cambia nada más. Ni las instrucciones, ni las tools, ni el historial, ni el código que llama. En la Sección 3.6 llevamos esto más lejos y dirigimos la elección enteramente desde una variable de entorno.

### Por qué esto es una capacidad estratégica y no una comodidad

Cuatro consecuencias que conviene nombrar explícitamente, porque son la forma de justificar el framework ante quien decide:

**Escalonado de costes.** Enruta la clasificación y la extracción a un modelo barato y rápido; enruta la síntesis final a uno caro. Esta es la tercera palanca de la Sección 1.4, y la interfaz es lo que la convierte en un cambio de una línea en lugar de una refactorización.

**Riesgo de provider.** Hay caídas, los precios cambian, las condiciones cambian. Una dependencia rígida del SDK de un solo proveedor es un riesgo de negocio. Una interfaz es una salida.

**Desarrollo local.** Ejecuta Ollama en tu portátil y desarrolla gratis todo lo de este libro. Despliega contra un provider en la nube. El mismo código.

**Residencia de los datos.** Un cliente que no puede enviar datos fuera de la UE, o fuera de su propio edificio, es un cambio de configuración y no una reescritura.

### El compromiso, dicho con honestidad

Una abstracción sobre varios providers converge hacia su subconjunto común. Las funcionalidades específicas de un provider —modos de pensamiento extendido, caché de prompts, tools nativas de búsqueda web, ajustes de seguridad concretos— o se exponen mediante vías de escape o no están disponibles. La respuesta de NeuronAI es `ProviderTool`, que te permite usar las tools integradas de un provider (OpenAI Responses, Gemini y Anthropic las soportan), pero la propia documentación del framework es franca al señalar que las tools de provider introducen restricciones y que el sistema portable de Tools y Toolkits sigue siendo la vía más flexible.

Ten claro qué estás intercambiando. La portabilidad cuesta, durante un tiempo, el acceso a la funcionalidad más nueva de cada proveedor.

### Puntos clave

- Cinco interfaces: provider, tool, historial de conversación, embeddings, vector store.
- Depende de la interfaz; la implementación es configuración.
- La recompensa es el escalonado de costes, el riesgo de proveedor, el desarrollo local gratuito y la residencia de los datos.
- El coste es el acceso diferido a las funcionalidades específicas de cada provider.

## 2.3 La idea clave: Agent y RAG *son* workflows

Esta es la sección más importante del capítulo. Es la idea unificadora central del framework, la documentación oficial la revela tarde, y explica muchísimas cosas que de otro modo parecerían arbitrarias.

### El enunciado

`Agent` y `RAG` no son sistemas aparte que se sientan al lado de `Workflow`. **Son workflows.** Son grafos de nodos preensamblados que implementan los dos patrones agénticos más comunes.

La propia documentación de NeuronAI lo dice directamente: las clases Agent y RAG son workflows en sí mismas, y representan implementaciones listas para usar de los patrones más comunes de llamadas a tools, recuperación y structured output.

### Qué significa eso en concreto

Cuando llamas a `->chat()` en un agente, estás ejecutando un workflow cuyos nodos son aproximadamente:

- `ChatNode` — llama al LLM
- `ToolNode` — ejecuta las tools solicitadas y vuelve atrás
- `StructuredOutputNode` — se usa cuando pides un resultado tipado
- `StreamingNode` — se usa cuando llamas a `->stream()`

Esos nombres de nodo no son trivia interna. Son parte de la superficie pública. En el SDK de Laravel enganchas middleware nombrando el nodo sobre el que debe ejecutarse:

```php
Neuron::middleware(ToolNode::class, new ToolApproval())
    ->chat(new UserMessage('Delete the oldest log file'));
```

No puedes usar esa API sin saber que `chat()` está respaldado por nodos. Precisamente por eso esto pertenece al Capítulo 2 y no al 15.

### Las tres consecuencias

**1. Todo lo que aprendas sobre workflows se aplica a los agentes.**
Middleware, estado, streaming, interrupción, persistencia: son funcionalidades de workflow, y los agentes las heredan todas. Cuando llegues al Capítulo 15 y aprendas el humano en el circuito, no estarás aprendiendo una funcionalidad separada de los agentes. Estarás aprendiendo una funcionalidad de workflow que los agentes obtienen gratis.

**2. No hay un segundo framework cuando el proyecto crece.**
La trayectoria habitual con otros stacks es: prototipar con la abstracción simple, chocar contra su techo y reescribir contra la abstracción de grafo. Aquí, `Agent` *es* la abstracción de grafo con una configuración por defecto. Crecer significa añadir nodos, no migrar.

**3. Puedes usar un Agent como nodo dentro de un Workflow mayor.**
Esta es la historia multiagente, y no necesita ninguna API multiagente especial. Un agente investigador es un nodo. Un agente redactor es un nodo. Un árbitro es un nodo. Compónlos con eventos. El Capítulo 16 hace exactamente esto.

### La regla de decisión

**Extiende `Agent`** cuando tu problema sea «una entidad, un objetivo, algunas tools, iterar hasta terminar». Eso es la mayoría de los asistentes de propósito único.

**Construye un `Workflow`** cuando necesites: control sobre el orden de los pasos, varios agentes especializados, ramificación o bucles escritos por ti, checkpoints, o una pausa para la intervención humana.

**Extiende `RAG`** cuando el trabajo central sea responder a partir de un corpus documental.

Y cuando dudes: empieza con `Agent`. Migrar más adelante a un workflow es aditivo, porque siempre fue un workflow.

::: {.callout .callout-tip}
[En la práctica]{.callout-title}

Si te llevas una sola frase de la Parte I a la Parte IV, llévate esta. Quienes se la saltan viven los workflows como un tema nuevo e inconexo a mitad del libro; quienes la tienen viven los workflows como *«ah, así que esto es lo que había debajo del agente todo el tiempo»*.
:::

### Puntos clave

- `Agent` y `RAG` son workflows configurados, no sistemas paralelos.
- Las clases de nodo (`ChatNode`, `ToolNode`, `StreamingNode`, `StructuredOutputNode`) son API pública: el middleware apunta a ellas.
- Las funcionalidades de workflow las heredan los agentes.
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

    public function instructions(): string
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

Tres métodos plantilla —`provider()`, `instructions()`, `tools()`— más un `chatHistory()` opcional. Todo lo demás se hereda. La clase es una declaración de *qué es este agente*, y se lee como configuración porque lo es.

**Por qué vale la pena defender este patrón.** La clase se convierte en una unidad con nombre, testeable e inyectable. `SupportAgent` puede registrarse en un contenedor de servicios, simularse en tests y razonarse por parte de un colega que nunca ha visto el framework. Ese es un beneficio arquitectónico real frente a esparcir configuración fluida por los controladores.

### Patrón B — Configuración fluida en el punto de llamada

Para ejecuciones puntuales y experimentos:

```php
$response = SupportAgent::make()
    ->toolMaxRuns(5)
    ->addTool(SomeExtraTool::make())
    ->chat(new UserMessage('...'));
```

Úsalo para variaciones por petición sobre una clase ya declarada: una tool que solo aparece para administradores, un límite de ejecuciones más bajo para un endpoint barato. No lo uses como sustituto de tener una clase: la configuración ensamblada en línea dentro de un controlador es configuración que nadie encontrará dentro de seis meses.

### Patrón C — Componer un Workflow a partir de componentes

Cuando quieres un flujo de control escrito por ti, usas los componentes de NeuronAI como piezas autónomas. La documentación es explícita: providers, embeddings, data loaders, historial de conversación y vector stores pueden usarse todos como componentes autónomos para construir entidades agénticas totalmente a medida.

```php
$handler = Workflow::make()
    ->addNodes([
        new ClassifyNode(),
        new RetrieveNode(),
        new AnswerNode(),
    ])
    ->init();

$handler->run();
```

Aquí la secuencia la escribiste *tú*. El modelo rellena los pasos. Esto es el peldaño 3 de la Sección 1.1, con checkpoints e interrupción disponibles cuando hagan falta.

### El camino de migración

La razón por la que esta decisión es de bajo riesgo: pasar del Patrón A al Patrón C es aditivo. Como `SupportAgent` ya es un workflow, promoverlo significa envolverlo como nodo dentro de un grafo mayor, no reescribirlo.

```php
class SupportNode extends Node
{
    public function __invoke(StartEvent $event, WorkflowState $state): ResolvedEvent
    {
        $answer = SupportAgent::make()->chat($event->message)->getMessage();
        return new ResolvedEvent($answer->getContent());
    }
}
```

Tu agente no cambia. Ahora es un componente de algo mayor.

### Puntos clave

- Extiende `Agent` por defecto; la clase es una unidad con nombre, inyectable y testeable.
- Configuración fluida para variaciones por petición, no como sustituto de una clase.
- Compón un `Workflow` cuando escribas tú el flujo de control.
- La promoción de A a C es aditiva: envuelve, no reescribas.

## 2.5 El ecosistema alrededor del framework

Una orientación breve, para que no reconstruyas cosas que ya vienen incluidas y sepas qué piezas usa realmente este libro.

### Inspector

Construido por el mismo equipo, y la razón por la que la observabilidad es un pilar. Define una variable de entorno:

```dotenv
INSPECTOR_INGESTION_KEY=your-key-here
```

y cada ejecución de un agente aparece como una línea temporal: qué nodo se ejecutó, qué tool se llamó con qué argumentos, qué volvió, cuántos tokens, cuánto tiempo.

Lo usamos en el Capítulo 10 y otra vez en el 23. Dada la Sección 1.5, planifica algún tipo de visor de traces desde el principio; este es simplemente el camino de menor resistencia.

### El SDK de Laravel

```bash
composer require neuron-core/neuron-laravel
```

Toda la Parte V. Aporta un archivo de configuración, generadores de artisan (`neuron:agent`, `neuron:rag`, `neuron:tool`, `neuron:workflow`, `neuron:node`, `neuron:middleware`), facades para providers y vector stores, migraciones listas para el historial de chat en Eloquent y una capa de persistencia en Eloquent para las interrupciones de workflow.

Conviene subrayarlo: este paquete añade comodidad, no capacidad. Todo lo que hace podrías hacerlo a mano, que es exactamente por qué lo construimos a mano primero en las Partes II a IV.

### MCP — Model Context Protocol

Un protocolo abierto para exponer tools a sistemas de IA. NeuronAI incluye un conector MCP, de modo que las tools publicadas por cualquier servidor MCP pueden engancharse a un agente de NeuronAI como si fueran nativas. El Capítulo 9 lo cubre. Las implicaciones de seguridad tienen allí su propia discusión: un servidor MCP es código de terceros entrando en el bucle de tu agente.

### Maestro

Un framework de agentes de CLI de código abierto construido sobre NeuronAI, con llamada a tools y aprobaciones con humano en el circuito. Útil como implementación de referencia de una aplicación de producción completa, y buena fuente de ejercicios de lectura de código. Volvemos a él en el Capítulo 26.

### Neuron Hub

Un registro de extensiones y toolkits de la comunidad. Consúltalo antes de escribir una integración, y publica ahí las tuyas.

### Neuron Studio

Un paquete de la comunidad (`digitalelvis/neuronai-studio`) que ofrece un constructor visual de agentes para Laravel y exporta clases PHP reales. Útil para prototipar y para enseñar la arquitectura a quien no programa. Genera código; no sustituye el entenderlo.

### Panorama de versiones

- **v3.x — la estable actual.** Este libro apunta a ella. El SDK de Laravel 1.3.0 requiere `neuron-ai: ^3.15`, que es una cota inferior útil de recordar cuando leas la Parte V.
- **v1 y v2 — heredadas, y todavía por todo internet.** Los namespaces difieren: `NeuronAI\Agent` pasó a ser `NeuronAI\Agent\Agent`, y `NeuronAI\SystemPrompt` pasó a ser `NeuronAI\Agent\SystemPrompt`. Si encuentras una entrada de blog o una página de documentación cuyos imports no coincidan con este libro, comprueba a qué versión apunta antes de depurar ninguna otra cosa. Partes de la documentación oficial todavía llevan imports de la época de la v2.

::: {.callout .callout-warning}
[Sobre la «v4» de la que quizá hayas oído hablar]{.callout-title}

Circulan programas de cursos y mensajes de foro que hablan de una beta de NeuronAI v4, normalmente prometiendo aprobación de tools a alto nivel y evaluaciones ampliadas. Esa versión no pudo verificarse en el momento de escribir esto: el material de actualización publicado cubre solo v2 → v3, y el SDK de Laravel actual se fija a `^3.15`.

En lugar de conjeturar, este libro te da algo más duradero: el Capítulo 26 es un capítulo de **estrategia de versiones** sobre cómo determinar qué tienes instalado realmente, cómo leer un changelog buscando movimientos de namespace que rompan y cómo fijar versiones para que una publicación de la biblioteca sea una decisión y no una caída. Antes de fiarte de cualquier afirmación sobre versiones —incluida esta— ejecuta `composer show neuron-core/neuron-ai --all`.
:::

### Ejercicio

Reproduce de memoria el diagrama de los cuatro pilares. Después, para el Proyecto final A («CLI auditora de repositorios», Capítulo 24) y el Proyecto final B («Servicio de soporte agéntico», Capítulo 25), enumera qué pilares y qué piezas del ecosistema esperas necesitar. Guarda la respuesta y compárala con lo que acabes construyendo; la diferencia es la realimentación más útil que este libro puede darte.

### Puntos clave

- Inspector para los traces; el SDK de Laravel para comodidad, no para capacidad.
- MCP trae tools externas, y con ellas código externo.
- Este libro apunta a la v3.x; los namespaces de v1/v2 difieren y siguen apareciendo en los resultados de búsqueda actuales.
