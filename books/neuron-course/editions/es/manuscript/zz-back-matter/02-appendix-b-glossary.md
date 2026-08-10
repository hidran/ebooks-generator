# Apéndice B — Glosario {.unnumbered}

**Agente.** Cuarto peldaño de la escalera de autonomía: el modelo decide qué acción tomar a continuación, y el bucle continúa hasta que decide que ha terminado. En NeuronAI, una clase que extiende `Agent`, que a su vez es un Workflow preconfigurado.

**Bucle del agente.** El ciclo de llamar al modelo, ejecutar las tools que solicite, devolverle los resultados y repetir hasta que el modelo devuelve prosa en lugar de una llamada a tool. Sin límite por defecto; protegido con límites de ejecución.

**Escalera de autonomía.** Los cuatro peldaños de la Sección 1.1 —llamada desnuda al LLM, chatbot, workflow, agente— distinguidos por *quién decide qué pasa a continuación*.

**BM25.** Una función clásica de ordenación por palabras clave. PHPVector la combina con la búsqueda vectorial para dar recuperación híbrida.

**Checkpoint.** `$this->checkpoint('name', fn () => ...)` dentro de un nodo de workflow. Guarda el resultado de la closure para que un nodo reanudado no la reejecute. Obligatorio alrededor de cualquier llamada al LLM que preceda a un `interrupt()`.

**Chunk.** Un fragmento de documento, producido por un splitter y embebido de forma independiente. El tamaño de chunk y el separador son los dos parámetros que más afectan a la calidad de la recuperación.

**Objeto chunk.** En streaming, un objeto producido por `events()`: `TextChunk`, `ReasoningChunk`, `ToolCallChunk`, `ToolResultChunk`. El texto vive en `$chunk->content`, no en el propio chunk.

**Bloque de contenido.** La unidad de la que está hecho realmente un mensaje. Un mensaje contiene una lista ordenada de ellos: `TextContent`, `ReasoningContent`, `ImageContent`, `FileContent`, `AudioContent`, `VideoContent`.

**Context window.** El techo rígido sobre system prompt + historial + esquemas de tools + respuesta. Superarlo hace fallar la petición de plano. Configura el recortador entre un 5 y un 10 % por debajo del límite real del modelo.

**Embedding.** Una lista de números que representa el significado de un fragmento de texto. Específico de cada modelo: cambiar el modelo de embeddings invalida todos los vectores ya almacenados.

**Evaluación.** Un dataset de entradas representativas ejecutado contra un agente, puntuado mediante asertos en lugar de comparado por igualdad. PHPUnit para un servicio no determinista.

**Evento.** En un workflow, una clase simple que implementa `Event`. Los nodos los consumen y los devuelven, y los type hints de `__invoke` *son* el grafo.

**Fidelidad.** Si una respuesta está anclada en el contexto recuperado o inventada. Se mide con `FaithfulnessJudge`; es el aserto más importante para un sistema RAG.

**HNSW.** Hierarchical Navigable Small World: el índice aproximado de vecinos más próximos que PHPVector usa para la búsqueda vectorial.

**Humano en el circuito.** Un workflow que se pausa a mitad de nodo, persiste todo su estado de ejecución, espera una decisión humana y se reanuda exactamente donde se detuvo. La capacidad más distintiva de NeuronAI.

**Búsqueda híbrida.** Combinar la similitud vectorial con la coincidencia por palabras clave, el filtrado por metadatos, o ambos.

**Interrupción.** El mecanismo detrás del humano en el circuito. `$this->interrupt($request)` lanza una `WorkflowInterrupt`, que capturas, persistes y más tarde reanudas.

**MCP — Model Context Protocol.** Un estándar abierto para exponer tools a sistemas de IA. Un servidor publica tools; cualquier cliente capaz de MCP las consume. Usa `only()` en cualquier servidor que no controles.

**Middleware.** Código enganchado a un nodo de workflow con nombre: `Neuron::middleware(ToolNode::class, ...)`. La razón por la que los nombres de las clases de nodo son API pública.

**Nodo.** Una unidad de un workflow: una clase con `__invoke(Event, WorkflowState): Event`. Cualquier cosa, desde una línea de código hasta un agente completo.

**No determinismo.** La propiedad que hace que la misma entrada produzca salidas distintas. Da por hecho que existe incluso a temperatura 0.

**Prompt injection.** Instrucciones que llegan dentro de datos que el agente lee: la descripción de un producto, un ticket de soporte, un documento recuperado, el resultado de una tool de terceros. Se combate quitando la capacidad, nunca añadiendo instrucciones.

**Provider.** Una implementación de `AIProviderInterface`: Anthropic, OpenAI, Gemini, Mistral, Ollama y otros. Intercambiable por configuración.

**RAG — retrieval-augmented generation.** Buscar en una base de conocimiento los pasajes relevantes para una pregunta y añadirlos al prompt. Le entrega al modelo la página relevante; no le enseña nada.

**Reranking.** Repuntuar los candidatos recuperados con un modelo que lee la consulta y cada documento *juntos*. Recupera 50, reordena, envía 5: la mejora de mayor retorno para un sistema RAG que ya funciona.

**Límite de ejecución.** `toolMaxRuns()` en un agente, `setMaxRuns()` en una tool. Por defecto 10 por tool. Un límite superado es un diagnóstico sobre el diseño de las tools, no un número que subir.

**Puntuación frente a distancia.** Una *puntuación* de similitud de 1 significa idéntico; una *distancia* de 0 significa idéntico. Corren en direcciones opuestas. Los vector stores deben devolver puntuaciones.

**Nombre de fuente.** El metadato `sourceName` que hace funcionar a `reindexBySource()`. Debe ser estable: el ID de un registro, nunca un título.

**Streaming.** Emitir la respuesta a medida que se produce. Cambia la latencia percibida, no la real, y te permite mostrar qué está haciendo el agente.

**Structured output.** `structured($message, MyClass::class)`: una instancia tipada y validada de tu clase en lugar de prosa. Un fallo de validación dispara un reintento que le dice al modelo exactamente qué estuvo mal.

**System prompt.** Las instrucciones enviadas en cada petición. No un saludo, sino la especificación de todo el sistema. NeuronAI lo estructura como `background`, `steps`, `output`.

**Token.** Aproximadamente tres cuartos de una palabra inglesa. La unidad en la que se te factura y la unidad en la que se mide tu context window.

**Tool.** Una función de tu código base que el modelo puede pedirte que ejecutes. La lista de tools registradas es tu límite de seguridad, el único en el que puedes confiar.

**Toolkit.** Un conjunto coherente de tools enganchado en una línea, con un método `guidelines()` que describe cómo se combinan. Fíltralo con `only()`.

**Trace.** La línea temporal de la ejecución de un agente: qué nodo se ejecutó, qué tool con qué argumentos, qué volvió, cuántos tokens, cuánto tiempo. Sustituye a la depuración, que aquí no funciona.

**Vector store.** Almacenamiento y búsqueda por similitud de embeddings. Cuatro métodos; `deleteBySource` existe para que la reindexación funcione.

**Visibilidad.** `visible(false)` elimina una tool del esquema por completo. Ocultar gana a instruir: las restricciones basadas en prompts se filtran, son probabilísticas y son atacables.

**Workflow.** Un grafo de nodos guiado por eventos con estado compartido, bucles, ramas, checkpoints e interrupción. El sustrato sobre el que está construido todo el framework: Agent y RAG *son* workflows.

**Estado del workflow.** El contenedor compartido que viaja por una ejecución. Se serializa al interrumpirse, así que no debe contener recursos, conexiones ni closures: guarda IDs y rehidrata dentro del nodo.
