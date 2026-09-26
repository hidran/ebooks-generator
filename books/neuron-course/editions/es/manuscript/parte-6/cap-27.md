# Capítulo 27 — Estrategia de versiones, ecosistema y desarrollo asistido por IA

Tres cosas que nadie pone en la documentación, y las tres te afectarán en el plazo de un mes desde el lanzamiento.

::: {.callout .callout-tip}
[El código de este capítulo]{.callout-title}

Este capítulo es conceptual y no tiene código propio, pero el repositorio complementario [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) contiene versiones ejecutables de todo lo que el libro construye.
:::

## 27.1 Estrategia de versiones

### El panorama

- **La v4 es la actual.** Este libro se verificó contra la rama 4.x en los días previos a la etiqueta 4.0.0, y contra el SDK de Laravel 2.x que la acompaña. El colofón registra los commits exactos.
- **La v3 es la versión mayor anterior.** Es estable, está muy desplegada y es la versión que dan por supuesta la mayoría de los tutoriales escritos en 2025 y 2026.
- **La v1 y la v2 están archivadas** pero su documentación sigue en línea en rutas versionadas, y su código está por todas partes en blogs, foros y sitios de preguntas y respuestas.

::: {.callout .callout-warning}
[¿Qué versión tienes de verdad?]{.callout-title}

Antes de fiarte de cualquier afirmación sobre versiones —incluidas las de este libro—, ejecuta:

```bash
composer show neuron-core/neuron-ai
```

y consulta la página de versiones publicadas del proyecto. Ese comando es la autoridad. Este libro no. Si desde la publicación ha salido una versión menor 4.x, lee su changelog frente a los capítulos de los que dependes: las pruebas de contrato del repositorio complementario existen precisamente para detectar esa desviación.
:::

### Qué cambió entre v3 y v4, y por qué te importa

v2 → v3 fue mecánico: los namespaces se movieron y cambiaron algunos tipos de retorno. v3 → v4 no lo es. El motor de flujos de trabajo que hay debajo de todo se reconstruyó en torno a la **ejecución duradera**, y varias API cambiaron de forma en consecuencia. Las rupturas con las que te toparás primero:

| v3 | v4 | Dónde en este libro |
|---|---|---|
| `Tool::make($name, $description)->setCallable(...)` | `Tool` es abstracta; el nombre y la descripción son propiedades de la clase | 5.2, 5.3 |
| `chat()` devuelve una respuesta | `chat()` devuelve un `AgentState`; `getMessage()` puede ser `null` | 3.4 |
| `stream()` devuelve un gestor con `events()` | `stream()` *es* el generador; `getReturn()` da el estado | 7.2 |
| `$workflow->init()->run()` | `$workflow->run()` | 13.3 |
| Una interrupción lanza `WorkflowInterrupt` | Una pausa es un resultado: `$state->isInterrupted()` | 15.1 |
| `resume` con un objeto de petición | `resume(array $payload)->run()`, direccionado por el ID del flujo de trabajo | 15.4 |
| `checkpoint()` | `memoize()` — `checkpoint()` sobrevive, obsoleto | 15.5 |
| Middleware `ToolApproval` | `approvalPolicy()` en la herramienta; `submitApprovalDecisions()` en el agente | 5.10, 15.5 |
| Historial transportado en el estado del agente | El historial es un servicio; el ID de hilo *es* el ID del flujo de trabajo | 4.3 |
| `withFilters()` en el almacén | Un `DocumentSchema` más `retrievalScope()` | 12.5, 20.1 |
| `observe(new InspectorObserver(...))` | Eventos PSR-14: suscribir un oyente con `subscribe()` | 10.2 |
| Guzzle incluido | Un cliente cURL integrado; Guzzle opcional | 3.2 |

Y el cambio arquitectónico que hay debajo: cada nodo completado es ahora un **paso duradero**, confirmado en el almacén del flujo de trabajo y reproducido en lugar de reejecutado tras una caída o una pausa. Agent y RAG ya eran flujos de trabajo en la v3 —el «Agent y RAG *son* flujos de trabajo» de la Sección 2.3—, pero en la v4 heredan esa durabilidad, y por eso ahora un chat puede rechazarse con `RunInFlightException` mientras hay una aprobación pendiente en el mismo hilo. El nodo que se *pausó* se sigue reejecutando desde el principio al reanudar; esa parte del Capítulo 15 no cambió.

### El diagnóstico de cinco comprobaciones

Cuando encuentres código de ejemplo que no funciona:

1. **Mira las instrucciones `use`.** `NeuronAI\Agent;` sin un segundo segmento significa v2 o anterior.
2. **Busca `->getMessage()`.** Su ausencia después de `chat()` significa v2.
3. **Busca `Edge` o `addEdges()`.** Eso es v1.
4. **Busca `->start()->getResult()`.** Esa es la API de flujos de trabajo de la v2.
5. **Busca `->init()`, `catch (WorkflowInterrupt`, `ToolApproval` o `setCallable()`.** Cualquiera de ellos significa v3.

Cinco comprobaciones, y identifican la versión de casi cualquier fragmento en segundos. Merece la pena tenerlas en un sitio donde puedas encontrarlas.

### Sobrevivir a una dependencia que se mueve rápido

Seis prácticas, todas aplicables a cualquier biblioteca que se mueva más rápido que tu ciclo de versiones:

**Fija y versiona `composer.lock`.** No solo en aplicaciones, sino en cualquier repositorio que otra persona vaya a clonar esperando que funcione. El archivo de bloqueo es lo que hace reproducible el «el año pasado funcionaba».

**Registra la versión donde vive el código.** Una línea en tu README, una constante, un comentario al principio del namespace de agentes. Cuando dentro de dieciocho meses alguien que esté depurando pregunte «¿contra qué estábamos escritos?», no debería tener que adivinarlo.

**Mantén un archivo de erratas.** Cuando encuentres una discrepancia entre la documentación y el código publicado —y el Apéndice A muestra que hay decenas—, anótala donde tu equipo la vea. Si no, la siguiente persona que choque con ella pasará la misma tarde que tú.

**Separa el conocimiento duradero del perecedero.** Tus notas sobre el diseño de descripciones de herramientas, la estrategia de chunking y el bucle del agente siguen siendo ciertas entre versiones mayores. Tus notas sobre firmas de métodos no. Tenerlas en documentos distintos significa que una actualización mayor invalida un archivo en lugar de todos.

**No persigas una nueva versión mayor de inmediato.** Deja que el ecosistema se ponga al día y luego actualiza deliberadamente. La publicación de una biblioteca debería ser una decisión que tomas, no una caída que descubres.

**Lee la guía de actualización antes del changelog.** El changelog te dice qué cambió; la guía de actualización te dice qué hacer al respecto. Para v2 → v3 la guía era breve y los cambios, mecánicos. Para v3 → v4 son veintisiete pasos numerados, cada uno con patrones de búsqueda y código de antes y después, y se distribuye *dentro del paquete*, en `vendor/neuron-core/neuron-ai/upgrade/`, así que la versión que lees es la versión que instalaste. El sitio web fue por detrás del código durante toda la beta de la v4; la guía del paquete, no.

### Puntos clave

- La v4 es la actual; el código v3 es lo que más encontrarás, y el código v1/v2 sigue por todas partes. Nada de ello compila contra la v4 sin cambios.
- v3 → v4 es conceptual, no mecánico: pasos duraderos, pausas como resultados, aprobación en la herramienta.
- Cinco comprobaciones identifican la versión de un fragmento en segundos.
- La guía de actualización se distribuye en `vendor/`; lee esa, no la del sitio web.
- `composer show --all` es la autoridad sobre lo que realmente tienes.
- Fija el archivo de bloqueo, registra la versión, mantén un archivo de erratas.
- Separa los conceptos duraderos de la API perecedera para que una actualización invalide un documento y no todos.

## 27.2 El ecosistema

### Maestro: una aplicación completa que leer

**Maestro es el primer agente de CLI construido enteramente en PHP con NeuronAI.** Es un asistente de código con la forma de los asistentes de terminal que quizá ya uses, y es de código abierto.

```bash
composer global require neuron-core/maestro
```

En Windows, instálalo y ejecútalo bajo WSL.

Soporta todos los proveedores de NeuronAI —Anthropic, OpenAI, Gemini, Cohere, Mistral, Ollama, Grok, DeepSeek— enrutados mediante una factoría de proveedores, e integra Inspector con una `inspector_key` en `.maestro/settings.json`.

**Por qué está al final de este libro.** La propia valoración del autor es el motivo:

> El framework que aquí hace el trabajo pesado es Neuron AI, en concreto la arquitectura de flujos de trabajo introducida en la v3. Sin la capacidad de interrumpir la ejecución a mitad del bucle del agente y reanudarla según la entrada del usuario, el sistema de aprobación de herramientas requeriría muchísimo más andamiaje para construirse y mantenerse. Este patrón —interrumpir, presentar, reanudar— habría sido doloroso de implementar sin un framework orientado a flujos de trabajo por debajo.

Eso es el Capítulo 15, validado por una aplicación real. Habiendo terminado la Parte IV, puedes leer el código de Maestro y reconocer en él cada patrón. Revisa antes su `composer.json`: la cita describe la arquitectura de la v3, y una aplicación del tamaño de Maestro pasa a una nueva versión mayor a su propio ritmo. Si sigue apuntando a la v3, leerla es además un buen ejercicio del diagnóstico de cinco comprobaciones de más arriba.

**Dos funcionalidades que merece la pena estudiar en concreto:**

**El sistema de aprobación de herramientas**: confirmación interactiva antes de las operaciones sensibles. La aprobación de herramientas de la Sección 15.5, en producción.

**El sistema de extensiones**: clases PHP que implementan `ExtensionInterface`, registradas mediante una `ExtensionApi` inyectada al arrancar. Un `ExtensionLoader` construye registros para herramientas, comandos, renderizadores, eventos, memorias e interfaz. Es una arquitectura de plugins bien diseñada y merece leerse por sus propios méritos, con independencia de la IA.

**Un buen ejercicio:** escribe una extensión de Maestro que añada una herramienta del Proyecto final A. Es el camino más corto de «he construido un agente de CLI» a «he extendido el de otra persona».

### Neuron Hub

Un registro de extensiones y juegos de herramientas de la comunidad. Dos usos:

**Consulta antes de construir.** Puede que alguien ya haya escrito tu integración.

**Publica la tuya.** Un juego de herramientas bien construido —una clase que extiende `AbstractToolkit` con un método `guidelines()` de verdad (Sección 5.7)— es una contribución de código abierto pequeña, alcanzable y con un público claro.

Si estás construyendo un portafolio, esta es mejor primera contribución que una errata en la documentación: acotada, útil y demostrablemente tuya.

### Neuron Studio

`digitalelvis/neuronai-studio`: un paquete de la comunidad que ofrece un constructor visual de agentes para Laravel que **exporta clases PHP reales**.

Útil para prototipar y para enseñar la arquitectura a quien no programa. La advertencia, sin rodeos: genera código, no sustituye entenderlo. Recurrir a Studio antes de terminar la Parte II produce clases que no sabes depurar.

### Más allá de Laravel

El framework es deliberadamente agnóstico respecto al framework, y el paquete core solo necesita PHP 8.1 con `ext-curl`.

**Symfony.** Todo lo de las Partes II a IV aplica directamente. Registra los agentes como servicios; `SQLChatHistory` acepta un PDO simple, que obtienes de una conexión de Doctrine con `getNativeConnection()`. Inspector distribuye `inspector-symfony`.

**Spryker, WordPress, sistemas internos heredados.** La misma historia. El paquete core no tiene dependencias de framework. El SDK de Laravel es, en palabras de sus propios mantenedores, algo que puedes usar *como inspiración para diseñar tu propio patrón de integración a medida.*

El argumento de posicionamiento del framework merece citarse:

> En lugar de fragmentar la innovación en soluciones específicas de cada framework, Neuron permite la colaboración entre desarrolladores de Laravel, colaboradores de Symfony, autores de plugins de WordPress y equipos con frameworks propios.

Si no estás en Laravel, la Parte V de este libro es un caso de estudio más que un requisito previo. Los puntos de integración que describe —un contenedor de servicios, una cola, una base de datos, una capa HTTP— existen en todo framework que merezca la pena usar.

### Puntos clave

- Maestro es una aplicación de código abierto completa construida sobre los patrones de este libro: léela.
- Neuron Hub es una primera contribución de código abierto realista.
- Studio genera código; no sustituye entenderlo.
- El paquete core es agnóstico respecto al framework; la Parte V se transfiere a Symfony, Spryker y cualquier otra cosa.

## 27.3 Desarrollo asistido por IA

### El problema, específico de esta biblioteca

El corpus público está lleno de código NeuronAI de v1, v2 y v3. Un asistente de código producirá con seguridad `use NeuronAI\Agent;`, `new Edge(NodeA::class, NodeB::class)`, `->init()->run()` y un middleware `ToolApproval`, porque es lo que dice la mayor parte de internet.

Peor: el asistente será *fluido* al hacerlo. Código incorrecto con una explicación segura de sí misma es más difícil de cazar que código incorrecto que parece inseguro.

### Tres soluciones, en orden de eficacia

**1. El material para agentes del propio framework.** La v4 distribuye orientación para asistentes de código dentro del paquete: un `AGENTS.md` junto a cada módulo en `vendor/neuron-core/neuron-ai/src/`, un conjunto de skills para agentes y la guía de actualización en `upgrade/`, escrita para que un asistente la ejecute paso a paso. El primer paso de la actualización es reinstalar las skills, porque las de la v3 son incorrectas para la v4. En Laravel, Boost añade las directrices del SDK (Sección 17.7). Trátalo todo como mejor que los datos de entrenamiento y peor que el código: durante la beta, algunas skills seguían mostrando una firma `approvalPolicy(array $inputs)` que el código ya había eliminado.

**2. La documentación por MCP.** El framework ofrece un servidor MCP para su documentación. Conéctalo a tu asistente y leerá los documentos actuales en lugar de recordar datos de entrenamiento caducos.

Es un círculo satisfactorio: **el Capítulo 9 enseñaba MCP como forma de dar capacidades a tus agentes. Aquí lo usas para dar a tu asistente conocimiento sobre el framework con el que estás construyendo agentes.**

**3. Un archivo de reglas del proyecto.** Lo que sea que lea tu asistente: `CLAUDE.md`, `.cursorrules` o equivalente.

```markdown
# NeuronAI conventions for this project

Target version: neuron-core/neuron-ai ^4.0

## Namespaces (do not use v1/v2 forms)
- `NeuronAI\Agent\Agent`     NOT `NeuronAI\Agent`
- `NeuronAI\Agent\SystemPrompt`  NOT `NeuronAI\SystemPrompt`

## API (v4 — do not use v3 forms)
- `chat()` returns `AgentState` — `->getMessage()?->getContent()`
- `stream()` is the generator — iterate it; chunks are objects; `->getReturn()` for the state
- Workflows: `->run()` / `->events()`, NOT `init()`; no `Edge` class
- A pause is a result: check `$state->isInterrupted()`, never catch `WorkflowInterrupt`
- Resume with `resume($payload)->run()`, addressed by workflow ID
- Tools extend `Tool`; `$name` / `$description` are properties, not constructor args
- Approval lives on the tool (`approvalPolicy()`), NOT in a `ToolApproval` middleware

## Project rules
- Tools are classes, never anonymous
- Toolkits filtered with `only()`, never `exclude()`
- Write tools: `setMaxRuns(1)` + idempotency guard + transaction
- Every pre-interrupt LLM call wrapped in `memoize()`
- Tenant scope is a constructor dependency, never read from ambient context
```

Treinta líneas, y codifican la mayoría de las reglas prácticas de este libro. Escribe tu propia versión y ponla en el repositorio: es la forma más barata de impedir que un asistente lleno de buenas intenciones deshaga decisiones que tomaste deliberadamente.

### La advertencia honesta

El Apéndice A es la prueba. **La propia documentación oficial se ha desviado del código en decenas de lugares**: namespaces incorrectos, nombres de clase con erratas, firmas que el código eliminó hace una versión y dos guías de actualización en el mismo paquete que no se ponen de acuerdo sobre qué ID reanuda un flujo de trabajo.

Un asistente que lea esa documentación hereda cada uno de esos errores.

La disciplina, que es la misma que este libro ha aplicado desde el principio:

**Usa los asistentes para la forma.** Andamiaje, boilerplate, fixtures de prueba, DTOs repetitivos. En eso son genuinamente buenos.

**Verifica cualquier cosa que toque la superficie de la API** contra tu versión instalada: el «ir a la definición» de tu IDE, o directamente `vendor/`.

**Nunca te fíes de una afirmación sobre versiones.** Si un asistente dice «en NeuronAI v4 haces X», compruébalo. No tiene forma fiable de saberlo.

Ese hábito se transfiere mucho más allá de este framework, y es la nota adecuada para terminar: **las herramientas son útiles y no son autoritativas, y saber la diferencia es lo que te convierte a ti en el ingeniero del circuito.**

### Puntos clave

- El corpus público está lleno de código v1–v3; los asistentes lo reproducen con soltura.
- Tres soluciones: el material para agentes incluido en el paquete del framework (más Boost en Laravel), documentación por MCP, un archivo de reglas del proyecto.
- La propia documentación se ha desviado: los asistentes heredan sus errores.
- Usa los asistentes para la forma, verifica la superficie de la API, no te fíes nunca de una afirmación sobre versiones.

## Epílogo

Veintisiete capítulos atrás, el Capítulo 1 dibujó una escalera de cuatro peldaños y planteó una pregunta: *¿quién decide qué pasa a continuación?*

Todo lo que ha venido después ha sido la maquinaria necesaria para dejar que un modelo la responda con seguridad. Herramientas para darle manos. Estructura para hacer usable su salida. Recuperación para darle conocimiento. Flujos de trabajo para darle forma. Interrupción para mantener a un humano en la decisión. Observabilidad para averiguar qué hizo realmente.

Nada de eso es específico de NeuronAI, y muy poco es específico de PHP. El framework cambiará: de eso trata la Sección 27.1. La aritmética de la Sección 1.4, la descripción de herramientas en cuatro partes de la Sección 5.4, la diferencia entre filtrar en la recuperación y filtrar después, el hecho de que un nodo reanudado se reejecuta desde el principio: eso sobrevive al framework, y es lo que de verdad aprendiste.

Queda una pregunta, y es la que hay que hacerse sobre cada agente que despliegues a partir de ahora:

> **¿Qué es lo peor que puede hacer, y qué lo detiene?**

Si puedes responderla, estás listo.
