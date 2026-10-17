# Capítulo 10. Agentes y subagentes, cuándo usar cada cosa

::: {.chapter-goals}
[Qué aprenderás]{.callout-title}

Aprendes a escribir un subagente, es decir, un archivo Markdown en `.claude/agents/` con su frontmatter y su system prompt, y a pedirle a Claude que lo escriba. Ves los subagentes que Claude Code ya usa por su cuenta, cómo se ejecutan en segundo plano y cómo te piden permisos. Al final tienes una regla práctica para elegir entre CLAUDE.md, comandos personalizados, skills, agentes, hooks y servidores MCP, y sabes cuándo tiene sentido poner a trabajar varios agentes juntos.

[Requisitos previos]{.callout-title}

Los capítulos 8 y 9, porque aquí comparo todo el tiempo los agentes con los comandos personalizados y las skills.

:::

En los capítulos anteriores le añadiste piezas a Claude Code. El `CLAUDE.md` recuerda las convenciones del proyecto (capítulo 7), los comandos personalizados convierten los prompts recurrentes en atajos con barra (capítulo 8) y las skills llevan procedimientos reutilizables a la sesión (capítulo 9). Todo eso vive en el mismo sitio: la sesión principal, con su historial, los archivos que ya leyó y las decisiones que se tomaron hace una hora.

Si pides una code review mientras Claude todavía está en mitad de la implementación, la revisión arrastra toda esa carga. El contexto tiene mucho ruido y Claude ya tiene una opinión sobre el código, porque lo escribió él. Un agente resuelve justo esto: es otra instancia de Claude, con un contexto propio que empieza vacío. Recibe la tarea, la hace por su cuenta y te devuelve solo las conclusiones. Si una skill es un manual que Claude consulta mientras trabaja, un agente es un compañero al que le pasas una tarea: la hace en su mesa y te trae el resultado.

## 10.1 Qué es un subagente

Un **subagente** es una instancia especializada de Claude Code que recibe una sola tarea, la resuelve en un contexto separado y devuelve el resultado a la sesión principal. En el capítulo 2 lo viste desde el lado del bucle: el tool `Agent` abre un segundo bucle con un contexto propio. Aquí lo miras desde el lado de quien lo configura. En este libro "agente" y "subagente" significan lo mismo.

Tres características lo distinguen de todo lo que has visto hasta ahora.

### Contexto aislado

El subagente empieza de cero. No ha visto la conversación, no ha leído los archivos que Claude abrió en la última hora, no sabe qué concesiones aceptaron. Lo que sabe es la tarea que le llega y lo que lea por su cuenta.

Esa es la ventaja principal. El subagente hace su trabajo en su contexto, y a la sesión principal, ya llena de archivos leídos y errores analizados, le llega un informe de unos cientos de palabras en lugar de miles de líneas de lecturas.

### Un system prompt propio

Cada agente tiene un system prompt que dice quién es, qué tiene que hacer y cómo debe responder: un revisor de código senior, un analista de datos, un auditor de seguridad. Un Claude genérico al que le pides lo mismo a mitad de conversación parte, en cambio, de un contexto ya condicionado por el resto del trabajo.

### Tools limitados

Un agente puede tener solo una parte de los tools. Un revisor con `Read` pero sin `Edit`, `Write` ni `Bash` no puede modificar por error los archivos que está analizando, aunque su prompt esté mal escrito o entienda mal la tarea. Menos tools también significa menos sorpresas: en el peor de los casos, un agente de solo lectura te devuelve un informe equivocado.

### Cuándo conviene

Hay cuatro situaciones que se repiten a menudo.

La primera es la code review: un agente que no siguió la implementación no sabe cuánto te costó esa función y no tiene reparos en decirte que hay que reescribirla. La segunda es la búsqueda en el codebase: el agente lee decenas de archivos y a ti te llega el resumen ("la autenticación usa tokens de Sanctum, la ability se comprueba en el controlador con `tokenCan()`"), no el rastro de lecturas. La tercera son las tareas en paralelo: seguridad, rendimiento y cobertura de tests en tres agentes a la vez, con un tiempo total cercano al del análisis más largo. La cuarta son las tareas ruidosas, como cargar un CSV grande o leer decenas de archivos de configuración: la salida intermedia se queda en el contexto del agente.

### Skills y agentes, cara a cara

| | Skill | Agente |
|---|---|---|
| Dónde se ejecuta | En el contexto principal | En un contexto separado |
| Qué sabe de la sesión | Todo | Nada, empieza de cero |
| Tools | Los mismos de la sesión | Una lista restringida, si la escribes |
| Uso típico | Un procedimiento que seguir mientras trabajas | Una tarea que delegar |

Las dos cosas se combinan. En el capítulo 9 viste que una skill con `context: fork` se ejecuta en un subagente, y el campo `agent` dice en cuál. Al revés, un agente puede precargar skills con el campo `skills` de su frontmatter.

## 10.2 Los subagentes que ya tienes

Claude Code ya trae algunos subagentes y los lanza por su cuenta cuando hacen falta.

| Subagente | Qué hace | Tools |
|---|---|---|
| `Explore` | Explora el codebase para responder a una pregunta | Solo lectura |
| `Plan` | Investiga el código durante Plan Mode | Solo lectura |
| `general-purpose` | Tareas de varios pasos que también exigen actuar | Todos |

Explore es el que verás más a menudo. Usa el mismo modelo que la sesión principal y acepta tres niveles de profundidad: quick, medium y very thorough. Puedes pedirlo de forma explícita:

```text
usa el agente Explore, nivel very thorough, para entender cómo gestiona la Photogallery la subida de fotos: desde el controlador hasta los jobs en cola. Dame los archivos implicados y el flujo en diez líneas
```

Explore y Plan arrancan sin `CLAUDE.md`: reciben la pregunta y leen el código, sin tus instrucciones de proyecto. Si una convención es imprescindible para responder, escríbela en el prompt. También hay subagentes de servicio, como `statusline-setup` y `claude-code-guide`. La variable de entorno `CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS=1` quita Explore y Plan.

::: {.callout .callout-deep-dive}
[Bajo el capó]{.callout-title}

Cada subagente nace de una llamada al tool `Agent`. Hasta la versión 2.1.63 el tool se llamaba `Task`, y todavía lo encuentras así en artículos y configuraciones antiguas: `Task(...)` funciona como alias en las reglas de permisos. Las reglas también pueden mirar los parámetros de la llamada, por ejemplo `Agent(model:opus)` para los subagentes lanzados con Opus. Lo usamos en el capítulo 11.
:::

## 10.3 Anatomía de un agente

Un agente es un archivo Markdown con un frontmatter YAML. El nombre del archivo es libre; el nombre del agente lo decide el campo `name`. Claude Code los busca en varios sitios, y si dos tienen el mismo nombre gana el que está más arriba en esta lista:

1. la configuración gestionada por la organización;
2. el flag `--agents` de la línea de comandos, que acepta una definición en JSON para una sola sesión;
3. `.claude/agents/` en el proyecto, que se busca en las carpetas superiores hasta la raíz del repositorio y en las subcarpetas;
4. `~/.claude/agents/` en tu home;
5. la carpeta `agents/` de los plugins instalados.

En la práctica eliges entre dos sitios. Si el agente conoce las convenciones, los servicios y las rutas del proyecto, va en `.claude/agents/` y le haces commit: todo el equipo lo recibe con el repositorio. Si es una competencia transversal, un revisor genérico o un experto en Python, va en `~/.claude/agents/` y lo tienes en todos tus proyectos. Es la misma lógica que con las skills.

Un revisor genérico, `~/.claude/agents/code-reviewer.md`, tiene esta forma:

```markdown
---
name: code-reviewer
description: Revisa el código en busca de bugs, convenciones del proyecto y tests que faltan. Úsalo después de cambios importantes, antes del commit.
tools: Read, Grep, Glob
model: sonnet
---

Eres un revisor de código senior para este proyecto.

## La tarea
Revisa los cambios que se te indiquen. Céntrate en:
- bugs y casos límite sin gestionar
- respeto de las convenciones del proyecto (ver CLAUDE.md)
- cobertura de tests
- problemas de rendimiento
- legibilidad

## Formato de la respuesta
- Puntos fuertes (tres como máximo)
- Problemas importantes, con archivo:línea y la corrección propuesta
- Sugerencias menores (opcionales)
- Veredicto: APPROVED o NEEDS_CHANGES

## Restricciones
- No modifiques archivos.
- 300 palabras como máximo en total.
```

### El frontmatter

Solo `name` y `description` son obligatorios. Los campos de varias palabras van en camelCase.

`name` es el identificador: en minúsculas con guiones, 256 caracteres como máximo y sin dos puntos. Es el nombre con el que lo llamas: "usa el agente code-reviewer en...".

`description` es el campo que más importa. Claude lee la description de todos los agentes disponibles y decide a partir de ella si delega una tarea, incluso cuando no nombras ningún agente. Escríbela como la regla de un router: qué hace y cuándo usarlo. "Ayuda con el código" no sirve de nada. "Revisa el código en busca de bugs, convenciones y tests que faltan. Úsalo después de cambios importantes, antes del commit" le dice a Claude exactamente cuándo sacarlo a escena. Como con las skills, la description se queda en el contexto de cada sesión aunque el agente no esté trabajando, así que mantenla corta.

`tools` es la lista de tools permitidos. Si la omites, el agente hereda todos los tools de la sesión, incluidos los de los servidores MCP. Especificarla es casi siempre lo correcto. `disallowedTools` hace lo contrario: partes de todo y quitas algo, por ejemplo `Bash`. En las builds nativas para macOS, Linux y WSL, `Grep` y `Glob` normalmente no están, porque Claude busca en los archivos a través de `Bash`: ahí un agente con `Read, Grep, Glob` trabaja en la práctica solo con `Read`. Basta para revisar los archivos que le indiques. No añadas `Bash` solo para darle búsqueda, porque con una shell el agente también puede escribir.

`model` elige el modelo: `sonnet`, `opus`, `haiku`, `fable`, un ID completo como `claude-opus-5-5`, o `inherit` para usar el mismo modelo que la sesión. Un revisor técnico va bien con Sonnet, un agente que diseña la estructura de una funcionalidad puede merecer Opus y uno que resume logs va con Haiku. Si omites el campo, el agente usa el modelo que Claude le pasa en esa llamada y, si no hay ninguno, el de la sesión (o el de `CLAUDE_CODE_SUBAGENT_MODEL`, si la has definido).

Los demás campos los usarás menos:

| Campo | Para qué sirve |
|---|---|
| `permissionMode` | El modo de permisos del agente: `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan`, `manual` (capítulo 11) |
| `maxTurns` | El número máximo de vueltas del bucle antes de que el agente se detenga |
| `effort` | El nivel de razonamiento, de `low` a `max` |
| `skills` | Las skills que se precargan en el contexto del agente |
| `mcpServers` | Los servidores MCP a disposición del agente (capítulo 13) |
| `hooks` | Hooks que solo valen mientras el agente trabaja (capítulo 12) |
| `memory` | Una memoria persistente del agente: `user`, `project` o `local` |
| `background` | Con `true` el agente siempre se ejecuta en segundo plano |
| `isolation` | Con `worktree` el agente trabaja en un worktree de Git temporal |
| `color` | El color con el que el agente aparece en la interfaz |

`memory` e `isolation` cambian el comportamiento más que los demás. Con `memory: project` el agente tiene una carpeta `.claude/agent-memory/<agent>/` donde anota lo que aprende de una vez para otra; con `user` la carpeta está en `~/.claude/agent-memory/<agent>/`, y con `local` en `.claude/agent-memory-local/<agent>/`, que hay que dejar fuera de Git. Con `isolation: worktree` el agente arranca en un worktree temporal creado a partir de la rama por defecto, así sus cambios no tocan tu copia de trabajo; si no cambia nada, el worktree se elimina solo. Volvemos a esto en la sección 10.8 y en el capítulo 20.

En los agentes que vienen de un plugin, `hooks`, `mcpServers` y `permissionMode` se ignoran: un plugin no puede subirse los permisos solo.

### El cuerpo, es decir, el system prompt

Todo lo que está debajo del frontmatter es el system prompt del agente. Un buen prompt tiene cuatro partes: quién es el agente, qué tiene que hacer cuando lo llaman, cómo debe formatear la respuesta y qué no debe hacer. El formato de la respuesta es la parte que más se descuida, y es la que lees tú o la sesión principal: un informe con archivo y línea se usa enseguida, un ensayo de 800 palabras no.

Una checklist final, es decir, las preguntas que el agente debe hacerse antes de responder, a menudo marca la diferencia entre un informe genérico y uno útil. Claude la genera cuando le pides que escriba el agente: reléela.

## 10.4 Crear un agente con Claude

Hasta la versión 2.1.197 el comando `/agents` abría un asistente guiado para crear agentes. Desde la 2.1.198, publicada el 1 de julio de 2026, el asistente ya no existe: `/agents` solo imprime un recordatorio que te dice que se lo pidas a Claude o que edites directamente `.claude/agents/` y `~/.claude/agents/`. Si encuentras tutoriales con capturas del menú "Create new agent", son de antes de esa versión.

La forma más rápida es pedirle a Claude que escriba el archivo. Describe el agente con precisión: qué comprueba, qué tools necesita, qué modelo, dónde guardarlo. Para la Photogallery, el proyecto de la Parte VI, un revisor de los controladores de la API Laravel se pide así:

```text
crea un subagente de proyecto llamado laravel-controller-reviewer en .claude/agents/.
Hace la code review de los controladores de backend/app/Http/Controllers/Api/V1/.

Para cada controlador que le pase debe comprobar que:
1. cada endpoint que recibe input usa una Form Request en app/Http/Requests/ y solo lee $request->validated()
2. existe un test de Pest en tests/Feature/Api/V1/ que llama al endpoint
3. las acciones sobre los recursos de un usuario pasan por una Policy en app/Policies/
4. los endpoints que modifican datos comprueban la ability del token de Sanctum con tokenCan()
5. los errores siguen el envelope de docs/DESIGN.md §11.1

Tools: solo Read, Grep y Glob, debe leer y no modificar.
Modelo: sonnet, es una revisión técnica.
Informe: una línea por problema con archivo:línea y corrección, después el veredicto APPROVED o NEEDS_CHANGES. Máximo 300 palabras.
```

Claude escribe `.claude/agents/laravel-controller-reviewer.md` con el frontmatter, el system prompt estructurado, la checklist y el formato del informe. El resultado se parece a esto:

```markdown
---
name: laravel-controller-reviewer
description: Revisa los controladores de la API Laravel en backend/app/Http/Controllers/Api/V1/ en cuanto a validación, tests, policies, abilities de Sanctum y envelope de errores. Úsalo después de crear o modificar un controlador, antes del commit.
tools: Read, Grep, Glob
model: sonnet
color: orange
---

Eres un revisor senior de APIs con Laravel 13. Recibes uno o varios controladores de la Photogallery.

Para cada método público comprueba que:

1. El input llega de una Form Request en app/Http/Requests/<Recurso>/ y el controlador solo usa $request->validated().
2. Existe un test de Pest en tests/Feature/Api/V1/ que llama al endpoint, con al menos un caso de error.
3. Las acciones sobre los recursos de un usuario están autorizadas por una Policy en app/Policies/.
4. Los endpoints que modifican datos comprueban la ability del token con tokenCan().
5. Las respuestas usan una API Resource y los errores siguen el envelope de docs/DESIGN.md §11.1.

Antes de responder pregúntate: ¿abrí el test que cito? ¿La línea que indico existe de verdad?

Formato del informe:
- una línea por problema: archivo:línea, problema, corrección propuesta
- al final el veredicto: APPROVED o NEEDS_CHANGES

No modifiques archivos. 300 palabras como máximo.
```

<!-- TODO screenshot: il file .claude/agents/laravel-controller-reviewer.md aperto nell'editor, con frontmatter e system prompt visibili (sostituisce le vecchie figure del wizard /agents, rimosso in v2.1.198) -->

También puedes escribirlo a mano: una vez entendida la estructura, tardas menos en copiar uno existente y cambiarlo.

### Revisar el archivo

El primer archivo que genera Claude es un buen punto de partida, casi nunca el definitivo.

Las rutas. A veces Claude mete archivos que solo existen en el proyecto del que partió, o se los inventa. Cada ruta del prompt tiene que existir de verdad; si no, el agente pierde vueltas buscándola.

La checklist. Añade las comprobaciones que faltan y verifica que estén todas las que pediste, con el mismo nivel de detalle. En el revisor de Laravel el punto delicado es el cuarto: si Claude lo resume en un genérico "comprueba la autenticación", un endpoint protegido con `auth:sanctum` pero sin `tokenCan()` pasa la revisión. En ese caso reescribe el punto a mano.

El formato del informe. La longitud la decides tú: para un controlador bastan una lista numerada de problemas con archivo y línea y el veredicto.

Cuando el archivo te convenza, hazle commit. A partir de ese momento forma parte del repositorio como el `CLAUDE.md`, y `/doctor prompt-audit` lo revisa junto con las reglas y las skills cuando buscas instrucciones antiguas o en conflicto.

### Probarlo

Claude Code vigila `.claude/agents/` y `~/.claude/agents/`: un archivo añadido o modificado con la sesión abierta vale desde la siguiente delegación, sin reiniciar. La excepción es una carpeta nueva: si `agents/` no existía cuando arrancaste la sesión, sal y vuelve a entrar. Para saber qué agentes ve, pregúntaselo:

```text
¿qué subagentes tienes disponibles en este proyecto?
```

`/context` también los muestra, entre los elementos que ocupan espacio en el contexto. Después llama al agente por su nombre:

```text
usa el agente laravel-controller-reviewer para hacer la revisión de backend/app/Http/Controllers/Api/V1/AlbumController.php
```

Claude lanza el agente con el tool `Agent`. El agente lee el controlador, abre las Form Requests de `app/Http/Requests/Album/`, busca los tests y devuelve el informe. En la sesión ves el informe, no las lecturas que lo produjeron; para verlas, `Ctrl+O` abre la transcripción con las llamadas a los tools.

Si el agente no arranca cuando pides una revisión sin nombrarlo, el problema casi siempre es la description: hazla más explícita sobre cuándo usarlo.

::: {.callout .callout-prompt}
[Prompt reutilizable]{.callout-title}

Sustituye las partes entre corchetes y pega el prompt en Claude Code. Obtienes el archivo del agente listo para revisar.

```text
Quiero un agente para [descripción de la tarea].

Persona: [p. ej. senior TypeScript code reviewer, data scientist SaaS]
Input: [qué recibe el agente, p. ej. un archivo de controlador, un dataset CSV]
Formato del informe: [p. ej. problemas ordenados por gravedad, con archivo:línea]
Tools permitidos: [p. ej. Read, Grep, solo lectura]
Modelo: [sonnet / opus / haiku / inherit]
Alcance: [proyecto / usuario]

Crea el agente en .claude/agents/ (o en ~/.claude/agents/ si es de nivel usuario).
```
:::

## 10.5 Segundo plano, permisos y /subtask

En las sesiones interactivas, los subagentes que lanza Claude se ejecutan en segundo plano por defecto, y Claude no puede pedir que se ejecuten en primer plano. Mientras el agente trabaja tú sigues escribiendo; cuando termina, su informe llega a la conversación y Claude lo usa para seguir. Desde octubre de 2026 (versión 2.1.302) pasa lo mismo en el modo `-p`, en el SDK, en la app de escritorio y en VS Code.

Hay tres comandos que recordar. `/tasks` lista lo que se está ejecutando en segundo plano, con el estado de cada trabajo. `Ctrl+X Ctrl+K` detiene de golpe todos los subagentes en segundo plano. `Ctrl+B` manda a segundo plano un trabajo que está ocupando el turno, por ejemplo un comando `Bash` largo; si usas tmux, hay que pulsarlo dos veces.

Un subagente en segundo plano puede necesitar un permiso, por ejemplo para lanzar un comando que tus reglas ponen en `ask`. La petición no se queda bloqueada en su contexto: aparece en la sesión principal, y respondes ahí como a cualquier otra confirmación. También vale al revés: las reglas `deny` que escribes en el capítulo 11 se aplican también a los subagentes, así que un agente no puede hacer lo que le prohibiste a la sesión. Una regla `deny` bloquea en todos los modos, incluso en `bypassPermissions`.

Un subagente puede lanzar a su vez otros subagentes, hasta tres niveles por debajo de la conversación principal (el límite se cambia con `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`). En la práctica, dos niveles, un coordinador que lanza revisores, cubren casi todo.

### /subtask, cuando hace falta el contexto

Un subagente normal empieza de cero, y eso es lo que quieres para una revisión. Pero a veces quieres delegar una parte del trabajo que depende de lo que han hablado en la última media hora. Para eso está `/subtask`:

```text
/subtask escribe los tests de Pest para los dos casos límite de la subida de los que acabamos de hablar, sin tocar el controlador
```

`/subtask` lanza un subagente que hereda toda la conversación. Trabaja en segundo plano como los demás, pero sabe todo lo que sabes tú. Es distinto de una skill con `context: fork` (capítulo 9), que arranca sin el historial, y de `/fork`, que copia la conversación en una nueva sesión en segundo plano en lugar de abrir un subagente (capítulo 15).

## 10.6 Agentes de la comunidad, a través de plugins

No tienes que escribir cada agente desde cero. En GitHub encuentras colecciones de agentes listos para usar, por lenguaje, framework y dominio: revisores, auditores de seguridad, expertos en bases de datos, redactores de documentación.

La primera edición sugería clonar esas colecciones en una carpeta de `~/.claude/`. Hoy conviene instalarlos a través de un plugin: se instala desde un marketplace con un comando, se actualiza y se desactiva sin tocar los archivos del proyecto, y sus agentes llevan el nombre del plugin como prefijo, así no chocan con los tuyos. El marketplace oficial se llama `claude-plugins-official` y ya viene configurado. Superpowers, que instalaste en el capítulo 8, usa subagentes en su flujo de desarrollo con code review integrada. El capítulo 14 explica cómo funcionan los plugins y cómo construir uno.

Copiar a mano un archivo `.md` que encontraste en un repositorio sigue siendo posible, pero pierdes las actualizaciones y el rastro de su procedencia.

### Leer antes de instalar

Instalar un agente significa decirle a Claude que ejecute sus instrucciones en tu entorno, con los tools que declara. Es el mismo riesgo que añadir una dependencia de npm sin mirarla.

Antes de instalar un agente, o un plugin que los contenga, abre el archivo y mira tres cosas. El system prompt: ¿pide leer archivos fuera del proyecto, contactar direcciones externas, recopilar credenciales? Los tools: si está `Bash`, las instrucciones del agente pueden convertirse en comandos en tu máquina, y tiene que haber un motivo. Si falta `tools` por completo, el agente tiene todo lo que tiene la sesión. La fuente: quién mantiene el repositorio, desde hace cuánto, con cuánta actividad. Un repositorio sin historia y con un autor desconocido merece más cautela que un proyecto conocido.

::: {.callout .callout-warning}
[Atención]{.callout-title}

Un agente malicioso puede indicarle a Claude que lea `.env`, claves SSH y tokens y que los cuele en su informe con el nombre de "diagnóstico". Es prompt injection, la misma clase de problemas que afecta a cualquier sistema basado en un LLM. Lee siempre el archivo antes de instalarlo, pruébalo en un proyecto de prueba y mantén la regla `deny` sobre `Read(./.env)` del capítulo 11: también se aplica a los subagentes.
:::

Entre nivel de usuario y de proyecto vale la regla de la sección 10.3: un agente que adaptaste a tu stack va en `.claude/agents/` y en el repositorio, así el equipo trabaja con el mismo revisor.

## 10.7 Cuándo usar cada cosa

A estas alturas tienes CLAUDE.md, comandos personalizados, skills y agentes. En la Parte IV llegan otras tres herramientas que resuelven problemas parecidos: las reglas de permisos (capítulo 11), los hooks (capítulo 12) y los servidores MCP (capítulo 13).

| Necesidad | Herramienta | Capítulo |
|---|---|---|
| "Recuerda siempre las convenciones de este proyecto" | `CLAUDE.md` | 7 |
| "Cuando escriba /X, ejecuta este prompt" | Comando personalizado o skill | 8, 9 |
| "Un procedimiento reutilizable con plantillas y scripts" | Skill | 9 |
| "Delega esta tarea en un especialista con su propio contexto" | Agente | 10 |
| "Esto no debe pasar nunca" | Regla `deny` | 11 |
| "En cada cambio, sin excepciones, haz Y" | Hook | 12 |
| "Conéctate a un sistema externo: base de datos, API, GitHub" | Servidor MCP | 13 |
| "Dale todo esto al equipo en un paquete" | Plugin | 14 |

Sobre la segunda fila: desde el capítulo 8 sabes que un archivo en `.claude/commands/` y una skill en `.claude/skills/` crean el mismo comando con barra, y que para el trabajo nuevo conviene la skill.

El árbol de decisión sigue el mismo orden:

```text
¿Quieres cambiar el comportamiento de Claude?
│
├─ Es "recuerda X" o "sigue siempre esta convención"
│   └─ CLAUDE.md
│
├─ Tiene que pasar siempre, en cada evento, sin que decida el modelo
│   ├─ es una prohibición simple sobre un tool o un archivo  → regla deny
│   └─ hace falta lógica o una acción (formatear, notificar, bloquear según una condición)  → hook
│
├─ Es "cuando escriba /X, haz Y" (un prompt recurrente)
│   └─ comando personalizado o skill
│
├─ El procedimiento necesita archivos de apoyo, plantillas o scripts
│   └─ skill
│
├─ Quieres delegar una tarea con un contexto aislado y tools limitados
│   └─ agente
│
└─ Claude tiene que hablar con un sistema externo (base de datos, API REST, GitHub)
    └─ servidor MCP
```

### Los errores más comunes

Usar una skill donde hacía falta un agente. Una tarea larga, que produce mucha salida intermedia y ensucia el contexto principal, casi siempre es trabajo para un agente. La skill va bien para un procedimiento ligero que quieres mantener dentro del flujo de la conversación.

Usar un agente donde bastaba un comando. Si estás automatizando un prompt simple y repetido, como "añade los comentarios JSDoc a este archivo", un `/jsdoc` es más rápido y cuesta menos. Un agente vuelve a empezar de cero y tiene que releerlo todo, así que tarda más.

Meterlo todo en el `CLAUDE.md`. Va bien para las convenciones permanentes, mucho menos para los procedimientos: una secuencia de veinte pasos ahí dentro se carga en cada sesión, aunque no haga falta, y queda mejor en una skill o en un agente.

Confiarle a una instrucción una restricción de verdad. "No toques nunca los archivos de migración" escrito en el `CLAUDE.md` o en el prompt de un agente orienta a Claude, pero no lo garantiza. Para tener una garantía hace falta una regla de permisos o un hook, o bien un agente sin los tools para escribir.

### Las combinaciones

En el trabajo real estas herramientas se usan juntas. Un comando `/review` que lanza el code-reviewer sobre los archivos del último commit: el comando es el atajo, el agente hace el trabajo. Una skill de análisis de rendimiento que, con `context: fork`, ejecuta el análisis en un subagente y devuelve el informe. Un agente de revisión que respeta las convenciones del proyecto porque el `CLAUDE.md` le llega de todos modos: de la sesión principal no sabe nada, pero las reglas del proyecto sí las conoce. Las excepciones son Explore y Plan, que arrancan sin él, y los agentes con `omitClaudeMd` en el frontmatter.

## 10.8 Orquestar varios agentes

Los agentes dan lo mejor de sí cuando Claude coordina más de uno. Este patrón lo usas a fondo en la Parte VI, con la Photogallery, pero conviene entender aquí cómo funciona.

### La idea

Tienes que implementar una funcionalidad completa, de la API a la revisión. Si lo haces todo en secuencia en la sesión principal, el contexto se llena y la calidad baja a medida que crece la conversación. Con varios agentes el trabajo se reparte así:

1. un agente architect analiza los requisitos y devuelve la estructura: clases, responsabilidades, archivos que tocar;
2. un agente implementer escribe el código a partir de esa estructura, sin la discusión que la produjo;
3. un agente test-writer escribe los tests a partir del código y de la especificación, no de la conversación;
4. un agente code-reviewer relee el código terminado sobre los archivos reales, sin el punto de vista de quien lo escribió;
5. la sesión principal coordina, decide cuando los resultados chocan y te presenta el resultado.

La ventaja viene del contexto limpio. El code-reviewer no sabe que pasaste tres horas con ese código, el test-writer no recuerda el test parecido de hace media hora. Cada agente trabaja con un contexto pequeño y enfocado, y la calidad se mantiene más constante que en una única sesión que acumula horas de conversación.

### En paralelo

Las tareas independientes se ejecutan a la vez. En el capítulo 19, la revisión de cada wave de la Photogallery lanza cuatro agentes en paralelo, todos de solo lectura: seguridad, rendimiento, coherencia de la API y cobertura de tests. Después la sesión principal junta los cuatro informes por orden de gravedad. Como los subagentes ya se ejecutan en segundo plano, la sesión queda libre mientras tanto, y con `/tasks` compruebas cómo van.

### Cuando dos agentes escriben en los mismos archivos

Cuatro revisores de solo lectura trabajan sobre el mismo código sin problemas. En cambio, si el implementer y el test-writer modifican a la vez la misma copia de trabajo, uno sobrescribe los cambios del otro, o lee un archivo a mitad de modificación. El resultado son tests que fallan por motivos que ninguno de los dos causó por sí solo.

Hay dos soluciones. La primera es repartir el trabajo para que dos agentes nunca toquen los mismos archivos al mismo tiempo, o hacer que trabajen en secuencia. La segunda es darle a cada uno su propia copia del repositorio con un worktree de Git: es lo que hace `isolation: worktree` en el frontmatter, y el capítulo 20 lo usa para ejecutar en paralelo las waves de la Photogallery y luego unir las ramas.

### Una advertencia

Más agentes significa más complejidad, y muchas tareas no la justifican: para un refactoring en un solo archivo, una única sesión es más rápida. El trabajo con varios agentes compensa cuando la tarea es grande y se divide en partes bastante independientes. Una regla práctica: si a Claude le bastan menos de cinco minutos, no lances un agente; si necesita media hora, un contexto aislado casi siempre amortiza el tiempo de preparación. En la Parte VI estos agentes trabajan en las waves de implementación de la Photogallery y, en el capítulo 22, en la caza de tareas huérfanas antes del deploy.

## Resumen {.unlisted}

- Un subagente es una instancia de Claude con un contexto separado, un system prompt propio y, si así lo decides, tools limitados. La skill trabaja en el contexto principal; el agente abre uno nuevo y solo te devuelve el informe.
- Un agente es un archivo Markdown en `.claude/agents/` (proyecto, para hacerle commit) o en `~/.claude/agents/` (usuario). Solo hacen falta `name` y `description`; `tools`, `model` y el formato del informe en el prompt son las decisiones que más pesan.
- El asistente guiado de `/agents` ya no existe desde la versión 2.1.198: pídele a Claude que escriba el archivo y después relee rutas, checklist y formato.
- Los subagentes se ejecutan en segundo plano: los sigues con `/tasks`, los detienes con `Ctrl+X Ctrl+K`, y sus peticiones de permiso aparecen en la sesión principal. `/subtask` delega una tarea que necesita toda la conversación.
- Los agentes de la comunidad se instalan con plugins (capítulo 14), después de leer su prompt y sus tools.
- Varios agentes que leen pueden trabajar en paralelo; varios agentes que escriben en los mismos archivos se pisan entre sí y hay que separarlos, con `isolation: worktree` o con los worktrees del capítulo 20.

## Ejercicio {.unlisted}

Crea tu primer agente de solo lectura, para tu stack o para la Photogallery.

Elige el control que más a menudo te toca repetir y para el que te gustaría un revisor que no haya visto nacer el código: una code review de los controladores, un análisis de seguridad, una verificación de la cobertura de tests. Usa el prompt reutilizable de la sección 10.4 para que Claude te escriba el archivo en `.claude/agents/`, con `tools: Read, Grep, Glob`. Reléelo y añade al menos una comprobación específica de tu proyecto que Claude no había previsto.

Después pruébalo dos veces con un archivo real. La primera vez, llámalo por su nombre. La segunda, pide solo "revisa este archivo" sin nombrarlo, y comprueba si Claude lo elige por su cuenta; si no lo hace, reescribe la description. Por último, escribe "usa el agente [nombre] para corregir el primer problema que encontró, y no modifiques tú el archivo".

El ejercicio está terminado cuando el agente aparece en la respuesta a "¿qué subagentes tienes disponibles?", ha producido dos informes en el formato que elegiste y, ante la petición de corrección, ha respondido que no puede modificar archivos, con un `git status` que no muestra cambios aparte del archivo del agente. Hazle commit al archivo si quieres compartirlo con el equipo.

Si quieres un segundo modelo de prompt, con persona, input, formato del informe y tools, lo encuentras en la carpeta `cap-09/` del repositorio `github.com/hidran/claude-code-book-snippets` (numeración de la primera edición).
