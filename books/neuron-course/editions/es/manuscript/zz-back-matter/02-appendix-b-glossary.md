# Apéndice B — Glosario {.unnumbered}

**Agente.** Cuarto peldaño de la escalera de autonomía: el modelo decide qué acción tomar a continuación, y el bucle continúa hasta que decide que ha terminado. En NeuronAI, una clase que extiende `Agent`, que a su vez es un `Workflow` preconfigurado.

**Almacén vectorial.** Almacenamiento y búsqueda por similitud de incrustaciones. Cuatro métodos; `deleteBySource` existe para que la reindexación funcione.

**Bloque de contenido.** La unidad de la que está hecho realmente un mensaje. Un mensaje contiene una lista ordenada de ellos: `TextContent`, `ReasoningContent`, `ImageContent`, `FileContent`, `AudioContent`, `VideoContent`.

**BM25.** Una función clásica de ordenación por palabras clave. PHPVector la combina con la búsqueda vectorial para dar recuperación híbrida.

**Bucle del agente.** El ciclo de llamar al modelo, ejecutar las herramientas que solicite, devolverle los resultados y repetir hasta que el modelo devuelve prosa en lugar de una llamada a herramienta. Sin límite por defecto; protegido con límites de ejecución.

**Búsqueda híbrida.** Combinar la similitud vectorial con la coincidencia por palabras clave, el filtrado por metadatos, o ambos.

**Escalera de autonomía.** Los cuatro peldaños de la Sección 1.1 —llamada desnuda al LLM, chatbot, flujo de trabajo, agente— distinguidos por *quién decide qué pasa a continuación*.

**Estado del flujo de trabajo.** El contenedor compartido que viaja por una ejecución. Se serializa al interrumpirse, así que no debe contener recursos, conexiones ni funciones anónimas: guarda IDs y rehidrata dentro del nodo.

**Evaluación.** Un conjunto de datos de entradas representativas ejecutado contra un agente, puntuado mediante asertos en lugar de comparado por igualdad. PHPUnit para un servicio no determinista.

**Evento.** En un flujo de trabajo, una clase simple que implementa `Event`. Los nodos los consumen y los devuelven, y las declaraciones de tipo de `__invoke` *son* el grafo.

**Fidelidad.** Si una respuesta está anclada en el contexto recuperado o inventada. Se mide con `FaithfulnessJudge`; es el aserto más importante para un sistema RAG.

**Flujo de trabajo.** Un grafo de nodos guiado por eventos con estado compartido, bucles, ramas, puntos de control e interrupción. El sustrato sobre el que está construido todo el framework: `Agent` y `RAG` *son* flujos de trabajo.

**Fragmento.** Un trozo de documento, producido por un divisor e incrustado de forma independiente. El tamaño de fragmento y el separador son los dos parámetros que más afectan a la calidad de la recuperación.

**Herramienta.** Una función de tu código base que el modelo puede pedirte que ejecutes. La lista de herramientas registradas es tu límite de seguridad, el único en el que puedes confiar.

**HNSW.** Hierarchical Navigable Small World: el índice aproximado de vecinos más próximos que PHPVector usa para la búsqueda vectorial.

**Humano en el circuito.** Un flujo de trabajo que se pausa a mitad de nodo, persiste todo su estado de ejecución, espera una decisión humana y se reanuda exactamente donde se detuvo. La capacidad más distintiva de NeuronAI.

**Incrustación.** Una lista de números que representa el significado de un fragmento de texto. Específica de cada modelo: cambiar el modelo de incrustaciones invalida todos los vectores ya almacenados.

**Interrupción.** El mecanismo detrás del humano en el circuito. `$this->interrupt($request)` lanza una `WorkflowInterrupt`, que capturas, persistes y más tarde reanudas.

**Inyección de prompts.** Instrucciones que llegan dentro de datos que el agente lee: la descripción de un producto, un ticket de soporte, un documento recuperado, el resultado de una herramienta de terceros. Se combate quitando la capacidad, nunca añadiendo instrucciones.

**Juego de herramientas.** Un conjunto coherente de herramientas enganchado en una línea, con un método `guidelines()` que describe cómo se combinan. Fíltralo con `only()`.

**Límite de ejecución.** `toolMaxRuns()` en un agente, `setMaxRuns()` en una herramienta. Por defecto 10 por herramienta. Un límite superado es un diagnóstico sobre el diseño de las herramientas, no un número que subir.

**MCP — Model Context Protocol.** Un estándar abierto para exponer herramientas a sistemas de IA. Un servidor publica herramientas; cualquier cliente capaz de MCP las consume. Usa `only()` en cualquier servidor que no controles.

**Middleware.** Código enganchado a un nodo de flujo de trabajo con nombre: `Neuron::middleware(ToolNode::class, ...)`. La razón por la que los nombres de las clases de nodo son API pública.

**No determinismo.** La propiedad que hace que la misma entrada produzca salidas distintas. Da por hecho que existe incluso a temperatura 0.

**Nodo.** Una unidad de un flujo de trabajo: una clase con `__invoke(Event, WorkflowState): Event`. Cualquier cosa, desde una línea de código hasta un agente completo.

**Nombre de fuente.** El metadato `sourceName` que hace funcionar a `reindexBySource()`. Debe ser estable: el ID de un registro, nunca un título.

**Objeto de fragmento.** En transmisión, un objeto producido por `events()`: `TextChunk`, `ReasoningChunk`, `ToolCallChunk`, `ToolResultChunk`. El texto vive en `$chunk->content`, no en el propio fragmento.

**Prompt de sistema.** Las instrucciones enviadas en cada petición. No un saludo, sino la especificación de todo el sistema. NeuronAI lo estructura como `background`, `steps`, `output`.

**Proveedor.** Una implementación de `AIProviderInterface`: Anthropic, OpenAI, Gemini, Mistral, Ollama y otros. Intercambiable por configuración.

**Punto de control.** `$this->checkpoint('name', fn () => ...)` dentro de un nodo de flujo de trabajo. Guarda el resultado de la función anónima para que un nodo reanudado no la reejecute. Obligatorio alrededor de cualquier llamada al LLM que preceda a un `interrupt()`.

**Puntuación frente a distancia.** Una *puntuación* de similitud de 1 significa idéntico; una *distancia* de 0 significa idéntico. Corren en direcciones opuestas. Los almacenes vectoriales deben devolver puntuaciones.

**RAG — generación aumentada por recuperación.** Buscar en una base de conocimiento los pasajes relevantes para una pregunta y añadirlos al prompt. Le entrega al modelo la página relevante; no le enseña nada.

**Reordenación.** Repuntuar los candidatos recuperados con un modelo que lee la consulta y cada documento *juntos*. Recupera 50, reordena, envía 5: la mejora de mayor retorno para un sistema RAG que ya funciona.

**Salida estructurada.** `structured($message, MyClass::class)`: una instancia tipada y validada de tu clase en lugar de prosa. Un fallo de validación dispara un reintento que le dice al modelo exactamente qué estuvo mal.

**Token.** Aproximadamente tres cuartos de una palabra inglesa. La unidad en la que se te factura y la unidad en la que se mide tu ventana de contexto.

**Transmisión.** Emitir la respuesta a medida que se produce. Cambia la latencia percibida, no la real, y te permite mostrar qué está haciendo el agente.

**Traza.** La línea temporal de la ejecución de un agente: qué nodo se ejecutó, qué herramienta con qué argumentos, qué volvió, cuántos tokens, cuánto tiempo. Sustituye a la depuración, que aquí no funciona.

**Ventana de contexto.** El techo rígido sobre prompt de sistema + historial + esquemas de herramientas + respuesta. Superarlo hace fallar la petición de plano. Configura el recortador entre un 5 y un 10 % por debajo del límite real del modelo.

**Visibilidad.** `visible(false)` elimina una herramienta del esquema por completo. Ocultar gana a instruir: las restricciones basadas en prompts se filtran, son probabilísticas y son atacables.
