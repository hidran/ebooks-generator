# Apéndice B — Glosario {.unnumbered}

**Agente.** Cuarto peldaño de la escalera de autonomía: el modelo decide qué acción tomar a continuación, y el bucle continúa hasta que decide que ha terminado. En NeuronAI, una clase que extiende `Agent`, que a su vez es un `Workflow` preconfigurado.

**Almacén de mensajes.** El almacenamiento detrás del historial de un agente, tras `MessageStoreInterface`: `InMemoryMessageStore`, `FileMessageStore`, `SQLMessageStore`, `EloquentMessageStore`. No conoce ningún hilo propio: el ID de hilo del agente selecciona los mensajes. El recorte archiva los mensajes antiguos (`archived_at`) en lugar de borrarlos.

**Almacén vectorial.** Almacenamiento y búsqueda por similitud de incrustaciones. Cinco métodos —entre ellos `search(SearchRequest)` y `delete(FilterExpression)`, que es lo que hace funcionar la reindexación por fuente— y un `DocumentSchema` que declara qué metadatos se pueden filtrar.

**Barrera (fence).** Una guarda que rechaza una continuación obsoleta: una reanudación o una señal lleva el ID de ejecución (y el intento de ejecución) que espera, y el motor la rechaza si la ejecución ya avanzó. Un ID de ejecución obsoleto lanza `StaleWorkflowRunException`; un intento obsoleto lanza una simple `WorkflowException`.

**Bloque de contenido.** La unidad de la que está hecho realmente un mensaje. Un mensaje contiene una lista ordenada de ellos: `TextContent`, `ReasoningContent`, `ImageContent`, `FileContent`, `AudioContent`, `VideoContent`.

**BM25.** Una función clásica de ordenación por palabras clave: puntúa un documento según cuántas veces aparecen en él los términos de la consulta, ponderando cada término por su rareza. La búsqueda híbrida la combina con la búsqueda vectorial.

**Bucle del agente.** El ciclo de llamar al modelo, ejecutar las herramientas que solicite, devolverle los resultados y repetir hasta que el modelo devuelve prosa en lugar de una llamada a herramienta. Sin límite por defecto; protegido con límites de ejecución.

**Búsqueda híbrida.** Combinar la similitud vectorial con la ordenación por palabras clave. No es lo mismo que la *búsqueda filtrada*, que restringe una búsqueda vectorial por metadatos declarados en un `DocumentSchema`.

**Clave de idempotencia.** Un valor que identifica un único efecto deseado, de modo que repetir la petición no repita el efecto: se guarda junto con la escritura y se comprueba antes. Es lo que hace segura una herramienta de escritura reintentada o reproducida.

**Concesión (lease).** Un límite de tiempo sobre un intento de ejecución en curso: si no avanza dentro del plazo (`setLeaseTimeout()`), la ejecución se da por abandonada y una reanudación puede hacerse cargo de ella. Un agente tiene por defecto una concesión de diez minutos; una ejecución en pausa no mantiene ninguna.

**Escalera de autonomía.** Los cuatro peldaños de la Sección 1.1 —llamada desnuda al LLM, chatbot, flujo de trabajo, agente— distinguidos por *quién decide qué pasa a continuación*.

**Estado del flujo de trabajo.** El contenedor compartido que viaja por una ejecución. Se serializa en cada confirmación de paso, no solo al interrumpirse, así que no debe contener recursos, conexiones ni funciones anónimas: guarda IDs y rehidrata dentro del nodo.

**Evaluación.** Un conjunto de datos de entradas representativas ejecutado contra un agente, puntuado mediante asertos en lugar de comparado por igualdad. PHPUnit para un servicio no determinista.

**Evento.** En un flujo de trabajo, una clase simple que implementa `Event`. Los nodos los consumen y los devuelven, y las declaraciones de tipo de `__invoke` *son* el grafo.

**Fidelidad.** Si una respuesta está anclada en el contexto recuperado o inventada. Se mide con `FaithfulnessJudge`; es el aserto más importante para un sistema RAG.

**Flujo de trabajo.** Un grafo de nodos guiado por eventos con estado compartido, bucles, ramas, pasos duraderos e interrupción. El sustrato sobre el que está construido todo el framework: `Agent` y `RAG` *son* flujos de trabajo.

**Fragmento.** Un trozo de documento, producido por un divisor e incrustado de forma independiente. El tamaño de fragmento y el separador son los dos parámetros que más afectan a la calidad de la recuperación.

**Herramienta.** Una función de tu código base que el modelo puede pedirte que ejecutes. La lista de herramientas registradas es tu límite de seguridad, el único en el que puedes confiar.

**HNSW.** Hierarchical Navigable Small World: un índice de grafo aproximado de vecinos más próximos que permite a un almacén vectorial buscar entre las incrustaciones sin comparar la consulta con cada vector.

**Humano en el circuito.** Un flujo de trabajo que se pausa a mitad de nodo, persiste todo su estado de ejecución, espera una decisión humana y se reanuda exactamente donde se detuvo. La capacidad más distintiva de NeuronAI.

**ID de ejecución.** Una marca que identifica una generación de una ejecución de flujo de trabajo, usada junto con el intento de ejecución para poner una barrera a una reanudación frente a entregas obsoletas. No es el identificador para reanudar: ese es el *ID del flujo de trabajo*.

**ID de hilo.** La identidad de una conversación, que se vincula con `setThreadId()` o se pasa como `Agent::make(workflowId: ...)`; el framework nunca inventa uno, y un agente sin ID de hilo lanza una excepción. En un agente, el ID de hilo *es* el ID del flujo de trabajo, así que un hilo tiene como mucho una ejecución en curso. Es una entrada no confiable: autorízala antes de usarla.

**ID del flujo de trabajo.** La clave de negocio de una ejecución de flujo de trabajo: `refund:42`, o el ID de hilo de un agente. Todo lo que persiste una ejecución vive bajo ella, y es lo que pasas para reanudar.

**Incrustación.** Una lista de números que representa el significado de un fragmento de texto. Específica de cada modelo: cambiar el modelo de incrustaciones invalida todos los vectores ya almacenados.

**Interrupción.** El mecanismo detrás del humano en el circuito. `$this->interrupt($request)` pausa la ejecución; `run()` devuelve un estado cuyo `isInterrupted()` es verdadero. No se lanza nada. Respondes más tarde con `submitInputs($payload)->run()` (o `run(ExecutionRequest::resume($payload))`) sobre la instancia vinculada al mismo ID del flujo de trabajo.

**Inyección de prompts.** Instrucciones que llegan dentro de datos que el agente lee: la descripción de un producto, un ticket de soporte, un documento recuperado, el resultado de una herramienta de terceros. Se combate quitando la capacidad, nunca añadiendo instrucciones.

**Juego de herramientas.** Un conjunto coherente de herramientas enganchado en una línea, con un método `guidelines()` que describe cómo se combinan. Fíltralo con `only()`.

**Límite de ejecución.** `toolMaxRuns()` en un agente, `setMaxRuns()` en una herramienta. Por defecto 10 por herramienta. Un límite superado es un diagnóstico sobre el diseño de las herramientas, no un número que subir.

**MCP — Model Context Protocol.** Un estándar abierto para exponer herramientas a sistemas de IA. Un servidor publica herramientas; cualquier cliente capaz de MCP las consume. Usa `only()` en cualquier servidor que no controles.

**Memoización.** `$this->memoize('name', fn () => ...)` dentro de un nodo de flujo de trabajo. Almacena el resultado de la función anónima como parte del paso actual, de modo que un nodo que se reejecuta tras una pausa o una caída obtiene el valor almacenado en lugar de volver a ejecutar la función anónima. Obligatoria alrededor de cualquier llamada al LLM que preceda a un `interrupt()`.

**Middleware.** Código enganchado a una clase de nodo de flujo de trabajo: `addMiddleware(InferenceNode::class, ...)`. La coincidencia se hace por `instanceof`, y por eso los nombres de las clases de nodo son API pública. La aprobación de herramientas *no* es un middleware, digan lo que digan los tutoriales antiguos; vive en la herramienta.

**No determinismo.** La propiedad que hace que la misma entrada produzca salidas distintas. Da por hecho que existe incluso a temperatura 0.

**Nodo.** Una unidad de un flujo de trabajo: una clase con `__invoke(Event, WorkflowState): Event`, más un tercer parámetro opcional `WorkflowResources`. Cualquier cosa, desde una línea de código hasta un agente completo.

**Nombre de fuente.** El metadato `sourceName` que hace funcionar a `reindexBySource()`. Debe ser estable: el ID de un registro, nunca un título.

**Objeto de fragmento.** En transmisión, un objeto producido por `stream()`: `TextChunk`, `ReasoningChunk`, `ToolCallChunk`, `ToolResultChunk` y algunos tipos menos frecuentes. Solo `TextChunk` lleva texto de respuesta, en `$chunk->content`.

**Paso duradero.** Un nodo de flujo de trabajo completado, confirmado en el almacén del flujo de trabajo junto con su resultado. Tras una caída o una pausa, los pasos completados se reproducen en lugar de reejecutarse; solo se reejecuta el nodo que estaba en marcha.

**Política de aprobación.** La declaración de la propia herramienta de que una llamada necesita a un humano: el hook protegido `approvalPolicy()`, que devuelve `false`, `true` o una cadena con el motivo. Se sobrescribe por instancia con `requireApproval()`, `suppressApproval()` o `withApprovalPolicy()`. Se responde en el agente con `submitApprovalDecisions()`, que devuelve una ejecución pendiente que se completa con `->run()`.

**Prompt de sistema.** Las instrucciones enviadas en cada petición. No un saludo, sino la especificación de todo el sistema. NeuronAI lo estructura como `background`, `steps`, `output`.

**Proveedor.** Una implementación de `AIProviderInterface`: Anthropic, OpenAI, Gemini, Mistral, Ollama y otros. Intercambiable por configuración.

**Punto de control.** El nombre anterior a la v4 de la *memoización*. `checkpoint()` sigue existiendo, obsoleto, y llama a `memoize()`.

**Puntuación frente a distancia.** Una *puntuación* de similitud de 1 significa idéntico; una *distancia* de 0 significa idéntico. Corren en direcciones opuestas. Los almacenes vectoriales deben devolver puntuaciones.

**RAG — generación aumentada por recuperación.** Buscar en una base de conocimiento los pasajes relevantes para una pregunta y añadirlos al prompt. Le entrega al modelo la página relevante; no le enseña nada.

**Reordenación.** Repuntuar los candidatos recuperados con un modelo que lee la consulta y cada documento *juntos*. Recupera 50, reordena, envía 5: la mejora de mayor retorno para un sistema RAG que ya funciona.

**Saga.** Una operación de negocio de larga duración dividida en pasos, cada uno con una acción compensatoria que lo deshace si falla un paso posterior: cancelar el hotel cuando se rechaza el pago.

**Salida estructurada.** `structured($message, MyClass::class)`: una instancia tipada y validada de tu clase en lugar de prosa. Un fallo de validación dispara un reintento que le dice al modelo exactamente qué estuvo mal.

**Token.** Aproximadamente tres cuartos de una palabra inglesa. La unidad en la que se te factura y la unidad en la que se mide tu ventana de contexto.

**Transmisión.** Emitir la respuesta a medida que se produce. Cambia la latencia percibida, no la real, y te permite mostrar qué está haciendo el agente.

**Traza.** La línea temporal de la ejecución de un agente: qué nodo se ejecutó, qué herramienta con qué argumentos, qué volvió, cuántos tokens, cuánto tiempo. Sustituye a la depuración, que aquí no funciona.

**Ventana de contexto.** El techo rígido sobre prompt de sistema + historial + esquemas de herramientas + respuesta. Superarlo hace fallar la petición de plano. Configura el recortador entre un 5 y un 10 % por debajo del límite real del modelo.

**Visibilidad.** `visible(false)` elimina una herramienta del esquema por completo. Ocultar gana a instruir: las restricciones basadas en prompts se filtran, son probabilísticas y son atacables.
