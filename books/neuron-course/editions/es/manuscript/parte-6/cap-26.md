# Capítulo 26 — Estrategia de versiones, ecosistema y desarrollo asistido por IA

Tres cosas que nadie pone en la documentación, y las tres te afectarán en el plazo de un mes desde el lanzamiento.

## 26.1 Estrategia de versiones

### El panorama

- **La v3 es la estable actual.** El SDK de Laravel 1.3.0 requiere `neuron-ai: ^3.15`.
- **La v1 y la v2 están archivadas** pero su documentación sigue en línea en rutas versionadas, y su código está por blogs, foros y sitios de respuestas.

::: {.callout .callout-warning}
[Sobre la «v4» de la que quizá hayas oído hablar]{.callout-title}

Circulan programas de cursos y mensajes de foro que hablan de una beta de NeuronAI v4. Esa versión no pudo verificarse en el momento de escribir esto: el material de actualización publicado cubre solo v2 → v3, el sitio de la documentación mantiene árboles archivados en rutas `/v1/` y `/neuron-v3/` fáciles de confundir con una rama más nueva, y el SDK de Laravel actual se fija a `^3.15`.

Antes de fiarte de cualquier afirmación sobre versiones —incluida esta— ejecuta:

```bash
composer show neuron-core/neuron-ai --all
```

y consulta la página de versiones del proyecto. Ese comando es la autoridad. Este libro no.
:::

### Qué cambió entre v2 y v3, y por qué te importa

Tres rupturas aparecen constantemente en el material más antiguo, y cada una es un error fatal para quien copia un tutorial:

**1. Los namespaces se movieron.**

| v1 / v2 | v3 |
|---|---|
| `NeuronAI\Agent` | `NeuronAI\Agent\Agent` |
| `NeuronAI\SystemPrompt` | `NeuronAI\Agent\SystemPrompt` |

**2. `chat()` devuelve una respuesta, no un mensaje.**

```php
// v2
$message = MyAgent::make()->chat(new UserMessage("Hi, who are you?"));

// v3
$message = MyAgent::make()->chat(new UserMessage("Hi, who are you?"))->getMessage();
```

**3. Los adjuntos pasaron a ser bloques de contenido.**

```php
// v2
$message->addAttachment(new Image($url, AttachmentContentType::URL));

// v3
$message = new UserMessage([
    new TextBlock('Analyze this'),
    new ImageBlock($url, SourceType::URL)
]);
```

Y el cambio arquitectónico que hay debajo de todo ello: Agent, RAG y el sistema de mensajes se **reconstruyeron sobre el componente Workflow**, que ahora impulsa todo el framework. Por eso la Sección 2.3 podía decir que «Agent y RAG *son* workflows»: en la v3 se volvió literalmente cierto.

### El diagnóstico de cuatro comprobaciones

Cuando encuentres código de ejemplo que no funciona:

1. **Mira las instrucciones `use`.** `NeuronAI\Agent;` sin un segundo segmento significa v2 o anterior.
2. **Busca `->getMessage()`.** Su ausencia significa v2.
3. **Busca `Edge` o `addEdges()`.** Eso es v1.
4. **Busca `->start()->getResult()`.** Esa es la API de workflows de la v2.

Cuatro comprobaciones, y identifican la versión de casi cualquier fragmento en segundos. Merece la pena tenerlas en un sitio donde puedas encontrarlas.

### Sobrevivir a una dependencia que se mueve rápido

Seis prácticas, todas aplicables a cualquier biblioteca que se mueva más rápido que tu ciclo de versiones:

**Fija y versiona `composer.lock`.** No solo en aplicaciones, sino en cualquier repositorio que otra persona vaya a clonar esperando que funcione. El archivo de lock es lo que hace reproducible el «el año pasado funcionaba».

**Registra la versión donde vive el código.** Una línea en tu README, una constante, un comentario al principio del namespace de agentes. Cuando dentro de dieciocho meses alguien que esté depurando pregunte «¿contra qué estábamos escritos?», no debería tener que adivinarlo.

**Mantén un archivo de erratas.** Cuando encuentres una discrepancia entre la documentación y el código publicado —y el Apéndice A muestra que hay al menos cuarenta y cuatro—, anótala donde tu equipo la vea. Si no, la siguiente persona que choque con ella pasará la misma tarde que tú.

**Separa el conocimiento duradero del perecedero.** Tus notas sobre el diseño de descripciones de tools, la estrategia de chunking y el bucle del agente siguen siendo ciertas entre versiones mayores. Tus notas sobre firmas de métodos no. Tenerlas en documentos distintos significa que una actualización mayor invalida un archivo en lugar de todos.

**No persigas una nueva versión mayor de inmediato.** Deja que el ecosistema se ponga al día y luego actualiza deliberadamente. La publicación de una biblioteca debería ser una decisión que tomas, no una caída que descubres.

**Lee la guía de actualización antes del changelog.** El changelog te dice qué cambió; la guía de actualización te dice qué hacer al respecto. Para v2 → v3 la guía es breve y los cambios son mecánicos, que es el mejor caso y no uno con el que contar.

### Puntos clave

- La v3 es la actual; el código v1/v2 está por todas partes y no compila contra ella.
- Cuatro comprobaciones identifican la versión de un fragmento en segundos.
- `composer show --all` es la autoridad sobre lo que realmente tienes.
- Fija el archivo de lock, registra la versión, mantén un archivo de erratas.
- Separa los conceptos duraderos de la API perecedera para que una actualización invalide un documento y no todos.

## 26.2 El ecosistema

### Maestro: una aplicación completa que leer

**Maestro es el primer agente de CLI construido enteramente en PHP con NeuronAI.** Es un asistente de código con la forma de los asistentes de terminal que quizá ya uses, y es de código abierto.

```bash
composer global require neuron-core/maestro
```

En Windows, instálalo y ejecútalo bajo WSL.

Soporta todos los providers de NeuronAI —Anthropic, OpenAI, Gemini, Cohere, Mistral, Ollama, Grok, DeepSeek— enrutados mediante una factoría de providers, e integra Inspector con una `inspector_key` en `.maestro/settings.json`.

**Por qué está al final de este libro.** La propia valoración del autor es el motivo:

> El framework que aquí hace el trabajo pesado es Neuron AI, en concreto la arquitectura de workflows introducida en la v3. Sin la capacidad de interrumpir la ejecución a mitad del bucle del agente y reanudarla según la entrada del usuario, el sistema de aprobación de tools requeriría muchísimo más andamiaje para construirse y mantenerse. Este patrón —interrumpir, presentar, reanudar— habría sido doloroso de implementar sin un framework orientado a workflows por debajo.

Eso es el Capítulo 15, validado por una aplicación real. Habiendo terminado la Parte IV, puedes leer el código de Maestro y reconocer en él cada patrón.

**Dos funcionalidades que merece la pena estudiar en concreto:**

**El sistema de aprobación de tools**: confirmación interactiva antes de las operaciones sensibles. El `ToolApproval` de la Sección 15.5, en producción.

**El sistema de extensiones**: clases PHP que implementan `ExtensionInterface`, registradas mediante una `ExtensionApi` inyectada al arrancar. Un `ExtensionLoader` construye registros para tools, comandos, renderizadores, eventos, memorias e interfaz. Es una arquitectura de plugins bien diseñada y merece leerse por sus propios méritos, con independencia de la IA.

**Un buen ejercicio:** escribe una extensión de Maestro que añada una tool del Proyecto final A. Es el camino más corto de «he construido un agente de CLI» a «he extendido el de otra persona».

### Neuron Hub

Un registro de extensiones y toolkits de la comunidad. Dos usos:

**Consulta antes de construir.** Puede que alguien ya haya escrito tu integración.

**Publica la tuya.** Un toolkit bien construido —una clase que extiende `AbstractToolkit` con un método `guidelines()` de verdad (Sección 5.7)— es una contribución de código abierto pequeña, alcanzable y con un público claro.

Si estás construyendo un portafolio, esta es mejor primera contribución que una errata en la documentación: acotada, útil y demostrablemente tuya.

### Neuron Studio

`digitalelvis/neuronai-studio`: un paquete de la comunidad que ofrece un constructor visual de agentes para Laravel que **exporta clases PHP reales**.

Útil para prototipar y para enseñar la arquitectura a quien no programa. La advertencia, sin rodeos: genera código, no sustituye entenderlo. Recurrir a Studio antes de terminar la Parte II produce clases que no sabes depurar.

### Más allá de Laravel

El framework es deliberadamente agnóstico respecto al framework, y el paquete core solo necesita PHP 8.1.

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

## 26.3 Desarrollo asistido por IA

### El problema, específico de esta biblioteca

El corpus público está lleno de código NeuronAI de v1 y v2. Un asistente de código producirá con seguridad `use NeuronAI\Agent;`, `new Edge(NodeA::class, NodeB::class)` y `chat()` sin `getMessage()`, porque es lo que dice la mayor parte de internet.

Peor: el asistente será *fluido* al hacerlo. Código incorrecto con una explicación segura de sí misma es más difícil de cazar que código incorrecto que parece inseguro.

### Tres soluciones, en orden de eficacia

**1. Directrices de Laravel Boost.** El SDK de Laravel distribuye directrices actuales para asistentes de código (Sección 17.7). Nada que configurar: instala el paquete y ahí están.

**2. La documentación por MCP.** El framework ofrece un servidor MCP para su documentación. Conéctalo a tu asistente y leerá los documentos actuales en lugar de recordar datos de entrenamiento caducos.

Es un círculo satisfactorio: **el Capítulo 9 enseñaba MCP como forma de dar capacidades a tus agentes. Aquí lo usas para dar a tu asistente conocimiento sobre el framework con el que estás construyendo agentes.**

**3. Un archivo de reglas del proyecto.** Lo que sea que lea tu asistente: `CLAUDE.md`, `.cursorrules` o equivalente.

```markdown
# NeuronAI conventions for this project

Target version: neuron-core/neuron-ai ^3.15

## Namespaces (v3 — do not use v1/v2 forms)
- `NeuronAI\Agent\Agent`     NOT `NeuronAI\Agent`
- `NeuronAI\Agent\SystemPrompt`  NOT `NeuronAI\SystemPrompt`

## API
- `chat()` returns a response — always call `->getMessage()`
- `stream()` returns a handler — call `->events()`, chunks are objects (`$chunk->content`)
- Workflows use `init()` / `run()`, NOT `start()` / `getResult()`
- The `Edge` class does not exist — nodes wire via `__invoke` type hints

## Project rules
- Tools are classes, never inline closures
- Toolkits filtered with `only()`, never `exclude()`
- Write tools: `setMaxRuns(1)` + idempotency guard + transaction
- Every pre-interrupt LLM call wrapped in `checkpoint()`
- Tenant scope is a constructor dependency, never read from ambient context
```

Treinta líneas, y codifican la mayoría de las reglas prácticas de este libro. Escribe tu propia versión y ponla en el repositorio: es la forma más barata de impedir que un asistente lleno de buenas intenciones deshaga decisiones que tomaste deliberadamente.

### La advertencia honesta

El Apéndice A es la prueba. **La propia documentación oficial se ha desviado del código en cuarenta y cuatro lugares**: namespaces incorrectos, nombres de clase con erratas, tres firmas de constructor distintas para una misma clase, dos API de ejecución distintas en páginas contiguas.

Un asistente que lea esa documentación hereda cada uno de esos errores.

La disciplina, que es la misma que este libro ha aplicado desde el principio:

**Usa los asistentes para la forma.** Andamiaje, boilerplate, fixtures de test, DTOs repetitivos. En eso son genuinamente buenos.

**Verifica cualquier cosa que toque la superficie de la API** contra tu versión instalada: el «ir a la definición» de tu IDE, o directamente `vendor/`.

**Nunca te fíes de una afirmación sobre versiones.** Si un asistente dice «en NeuronAI v3 haces X», compruébalo. No tiene forma fiable de saberlo.

Ese hábito se transfiere mucho más allá de este framework, y es la nota adecuada para terminar: **las herramientas son útiles y no son autoritativas, y saber la diferencia es lo que te convierte a ti en el ingeniero del circuito.**

### Puntos clave

- El corpus público está lleno de código v1/v2; los asistentes lo reproducen con soltura.
- Tres soluciones: directrices de Boost, documentación por MCP, un archivo de reglas del proyecto.
- La propia documentación se ha desviado: los asistentes heredan sus errores.
- Usa los asistentes para la forma, verifica la superficie de la API, no te fíes nunca de una afirmación sobre versiones.

## Epílogo

Veintiséis capítulos atrás, el Capítulo 1 dibujó una escalera de cuatro peldaños y planteó una pregunta: *¿quién decide qué pasa a continuación?*

Todo lo que ha venido después ha sido la maquinaria necesaria para dejar que un modelo la responda con seguridad. Tools para darle manos. Estructura para hacer usable su salida. Recuperación para darle conocimiento. Workflows para darle forma. Interrupción para mantener a un humano en la decisión. Observabilidad para averiguar qué hizo realmente.

Nada de eso es específico de NeuronAI, y muy poco es específico de PHP. El framework cambiará: de eso trata la Sección 26.1. La aritmética de la Sección 1.4, la descripción de tools en cuatro partes de la Sección 5.4, la diferencia entre filtrar en la recuperación y filtrar después, el hecho de que un nodo reanudado se reejecuta desde el principio: eso sobrevive al framework, y es lo que de verdad aprendiste.

Queda una pregunta, y es la que hay que hacerse sobre cada agente que despliegues a partir de ahora:

> **¿Qué es lo peor que puede hacer, y qué lo detiene?**

Si puedes responderla, estás listo.
