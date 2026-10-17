# Apéndice A. Glosario

Los términos que aparecen a lo largo del libro, en orden alfabético. Los comandos y archivos se ordenan por la primera letra del nombre, sin la barra ni el punto inicial: `/goal` está en la G, `.claude/rules/` en la C. Cada entrada remite al capítulo, con la numeración de esta edición, donde el tema se explica a fondo. Los nombres de modelos y las versiones son los de octubre de 2026: para los valores actuales, consulta `/model` y el Apéndice E.

## A

`acceptEdits`
:   El modo Accept edits: Claude modifica archivos y ejecuta los comandos que solo tocan archivos y carpetas sin preguntar, y te para en todo lo demás. Capítulos 2 y 11.

`Agent` (tool)
:   El tool que lanza un subagente; hasta la versión 2.1.63 se llamaba `Task`. `Agent(model:opus)` en una regla afecta a los subagentes lanzados con Opus. Capítulos 2 y 10.

agent view
:   La pantalla de `claude agents`: las sesiones en segundo plano agrupadas en Working, Needs input y Completed. `Space` abre la vista previa y te deja responder, `Enter` entra, `←` con el prompt vacío vuelve a la lista, `Ctrl+T` fija una fila arriba. Capítulo 20.

agente, subagente
:   Una instancia de Claude que hace una sola tarea en su propio contexto, con un system prompt dedicado y, si quieres, tools limitados, y solo devuelve el informe a la sesión principal. Se define en un archivo Markdown con `name` y `description` en el frontmatter, en `.claude/agents/`, `~/.claude/agents/` o en un plugin. El asistente de `/agents` se eliminó en julio de 2026: el archivo lo escribes tú o se lo pides a Claude. En las sesiones interactivas se ejecuta en segundo plano por defecto. En el libro, "agente" y "subagente" son sinónimos. Capítulo 10.

`AGENTS.md`
:   El archivo de instrucciones compartido entre agentes de distintos fabricantes. Claude Code lo lee cuando el proyecto no tiene `CLAUDE.md`; si están los dos, impórtalo con `@AGENTS.md`. Capítulo 7.

API key
:   La clave para el uso de pago por consumo desde la Console. Si `ANTHROPIC_API_KEY` está definida y aprobada, gana sobre la suscripción: compruébalo con `/status`. Capítulo 1.

auto memory
:   Ver memoria automática.

auto mode
:   El modo de permisos por defecto de las sesiones interactivas desde la versión 2.1.283 (desde la 2.1.228 para Pro, Max y Team). Un clasificador aprueba las acciones coherentes con la petición y bloquea las arriesgadas; los bloqueos quedan en `/permissions`, pestaña Recently denied. Tras tres bloqueos seguidos, o veinte en una sesión, vuelve a pedirte confirmación. `claude -p` arranca en Manual. Capítulos 2 y 11.

## B

bucle agéntico
:   El ciclo del agente: reúne contexto, actúa, comprueba y vuelve a empezar hasta que termina o te necesita. Capítulo 2.

build workflow
:   El documento que describe cómo se ejecuta el plan del Photogallery: fases, reglas de trabajo y el ciclo leer, implementar, probar, hacer commit, marcar como hecho. Capítulos 17 y 18.

`bypassPermissions`
:   El modo sin controles, equivalente al flag `--dangerously-skip-permissions`. Solo en un contenedor o una VM desechables; un hook que deniega también bloquea aquí. Capítulos 2 y 11.

## C

change set
:   La vista previa de los cambios que CloudFormation haría en un stack. Un `Replacement: True` en la instancia RDS significa una base de datos nueva. Capítulo 23.

clasificador
:   El modelo que en auto mode juzga las acciones por ti. Las reglas deny y ask se evalúan antes, y los límites que escribes en el chat cuentan como indicaciones para esa sesión. `claude auto-mode defaults` imprime sus reglas. Capítulos 2 y 11.

Claude Code
:   El agente de Anthropic que trabaja sobre los archivos de tu proyecto. Funciona en la terminal, en VS Code, en los IDE de JetBrains, en la app de escritorio y en la nube. No está incluido en el plan gratuito de claude.ai. Capítulo 1.

`.claude/rules/`
:   Archivos Markdown con instrucciones separadas por tema. Sin frontmatter se cargan al arrancar; con `paths:`, solo cuando Claude lee o modifica un archivo que coincide. Las reglas personales van en `~/.claude/rules/`. Capítulo 7.

`CLAUDE.md`
:   Las instrucciones que Claude Code carga en cada sesión, en cuatro niveles: organización, usuario (`~/.claude/CLAUDE.md`), proyecto (`./CLAUDE.md`, en Git) y local (`./CLAUDE.local.md`, fuera de Git). Mejor por debajo de las doscientas líneas; admite imports con `@ruta`; los comentarios HTML no llegan a Claude. Orienta al modelo, pero no lo obliga. Capítulos 7 y 15.

`/clear`
:   Empieza de nuevo con una conversación vacía; la anterior sigue en `/resume`. Alias `/reset` y `/new`. Capítulo 15.

CloudFormation, CloudFront
:   El servicio de AWS que crea la infraestructura a partir de una plantilla YAML, y la CDN que sirve la SPA del Photogallery y reenvía `/api/*` al ALB. Capítulo 23.

Code Review en GitHub
:   La revisión gestionada de los pull requests para los planes Team y Enterprise, de pago por revisión: comentarios en línea con gravedad Important, Nit o Pre-existing, nunca una aprobación ni un bloqueo. Se relanza con `@claude review` y se personaliza con `REVIEW.md`. Capítulo 22.

`/code-review`
:   La revisión local (alias `/review`) de los commits sin push y de los cambios sin commit, en un subagente en segundo plano. Acepta effort y target (`/code-review high main...feat/albums-api`); sin nivel, reutiliza el último. Las correcciones de `--fix` no se deshacen con `/rewind`. Lee `CLAUDE.md`, no `REVIEW.md`. Capítulo 22.

comando personalizado (custom command)
:   Un archivo Markdown en `.claude/commands/` o `~/.claude/commands/` que se convierte en un comando: `fix-tests.md` es `/fix-tests`. Hoy forma parte de las skills: sigue funcionando, pero para trabajo nuevo conviene una skill, que gana si los nombres coinciden. Capítulo 8.

commit atómico
:   Un commit con un único cambio lógico completo. Lo genera el comando `/commit` que escribes en el capítulo 8, sobre los archivos en staging; en el Photogallery se traduce en una tarea, un commit. Capítulos 8 y 19.

compactación
:   El resumen que sustituye a los mensajes más antiguos y libera contexto. La lanzas con `/compact` más instrucciones sobre qué conservar; Claude Code también la hace por su cuenta cerca del límite. Un hook `SessionStart` con matcher `compact` vuelve a meter en el contexto lo que no se debe perder. Capítulos 12 y 15.

`/context`
:   Muestra cómo se reparte la ventana: system prompt, tools, MCP, agentes, skills, archivos de memoria, mensajes, espacio libre. Capítulo 15.

contexto, ventana de contexto
:   Todo lo que Claude ve: instrucciones de sistema, tools, archivos de memoria, archivos leídos, salidas, mensajes. Llega hasta un millón de tokens, pero cuanto más lleno está, más cuesta y más detalles se pierden. Regla práctica: una tarea, una sesión. Capítulos 1 y 15.

## D

`/doctor`, `claude doctor`
:   `claude doctor`, desde la shell, revisa la instalación y la configuración sin abrir una sesión y no modifica nada. `/doctor` (alias `/checkup`) hace una revisión más amplia y puede corregir; `/doctor prompt-audit` encuentra instrucciones obsoletas o en conflicto y propone los cambios. Capítulos 1 y 15.

`dontAsk`
:   El modo para scripts y CI: pasan las lecturas y los tools preaprobados, y todo lo demás se deniega sin preguntar. Capítulos 2 y 11.

DRY
:   "Don't Repeat Yourself", aplicado con la regla de tres: a la segunda repetición esperas, a la tercera extraes. Capítulo 18.

## E

ECS Fargate
:   El servicio de AWS que ejecuta contenedores sin servidores que administrar; ahí corren la API y el worker del Photogallery. Capítulo 23.

effort
:   Cuánto razona el modelo. Se elige con `/effort` entre `low`, `medium`, `high`, `xhigh` y `max` (solo para la sesión); en los modelos 5.5 el valor por defecto es `medium`. Para un único prompt difícil basta con `ultrathink`. Capítulos 2 y 3.

Explore
:   El subagente integrado de solo lectura que explora el código. Igual que Plan, arranca sin `CLAUDE.md`. Capítulo 10.

## F

Fable
:   La familia de modelos más capaz de Claude Code, alias `fable` (Fable 5.1 mientras escribo). Nunca es el valor por defecto: la eliges con `/model` o en el campo `model` de un subagente. Capítulo 2.

Filament
:   El framework de Laravel para paneles de administración, v5 en el Photogallery. Capítulo 19.

Firebase Hosting
:   El hosting estático de Google donde publicas la landing page, con preview channels para las vistas previas. Capítulo 16.

`/fork`
:   Copia la conversación en una nueva sesión en segundo plano y deja la principal donde está. Capítulos 15 y 20.

frontmatter
:   El bloque YAML entre dos líneas `---` al principio de un archivo Markdown, que usan comandos, skills, agentes y reglas. Capítulos 7-10.

## G

`/goal`
:   Una condición de finalización: Claude sigue turno tras turno hasta que un evaluador independiente la da por cumplida. El evaluador solo ve la conversación, así que la condición tiene que nombrar una comprobación que Claude ejecuta y muestra ("`composer test` termina con código 0"). `/goal clear` la cancela. Capítulo 20.

## H

harness
:   El programa que rodea al modelo: gestiona la conversación, expone los tools, controla permisos y hooks, y ejecuta las llamadas. Claude Code es un harness. Capítulo 2.

headless
:   El uso no interactivo con `claude -p "prompt"`, para scripts y CI. Las acciones permitidas se declaran con `--allowedTools`; `--bare` se salta hooks, skills, plugins, MCP y `CLAUDE.md`. Capítulo 1.

hook
:   Un comando que Claude Code ejecuta por su cuenta cuando ocurre un evento (`SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop`, `Notification` y otros). Recibe JSON por stdin; exit 0 continúa, exit 2 bloquea y le devuelve stderr a Claude, exit 0 con JSON en stdout da un control más fino. Se registra bajo `hooks` en `settings.json` o en un plugin, se ejecuta fuera del sandbox y `/hooks` lo muestra. Capítulo 12.

## I

idempotente
:   Que, repetido, da el mismo resultado, como el job de las fotos que escribe cada variante en una ruta fija. Capítulo 21.

`/init`
:   Escribe una primera versión de `CLAUDE.md` analizando el proyecto. Capítulo 7.

## K

KISS
:   "Keep It Simple, Stupid": la solución más sencilla que cumple el requisito, escrita en el `CLAUDE.md` contra la sobreingeniería. Capítulos 17 y 18.

## L

Laravel Sail
:   El entorno Docker de Laravel; en el Photogallery levanta MariaDB, Redis, Mailpit y MinIO. Capítulo 19.

Lovable
:   Una herramienta que genera interfaces a partir de un prompt; en el libro es el diseño que replicas. Capítulo 16.

## M

Manual
:   El modo que pide confirmación para casi todo, el valor por defecto antes de auto mode. En la configuración se llama `default`; el flag acepta `--permission-mode manual`. Capítulos 2 y 11.

marketplace
:   Un repositorio con `.claude-plugin/marketplace.json` que lista plugins. El oficial, `claude-plugins-official`, se añade en el primer arranque; `anthropics/claude-code` es solo de demostración. Se añade con `/plugin marketplace add`. Capítulo 14.

matcher
:   El filtro de un grupo de hooks: para los eventos de tools, el nombre del tool (`"Edit|Write"`, distingue mayúsculas y minúsculas); para `SessionStart`, el origen (`compact`). El campo `if` lo acota todavía más. Capítulo 12.

MCP (Model Context Protocol)
:   El protocolo con el que Claude Code usa servicios externos a través de un servidor MCP: remoto por `http` (token en un header u OAuth) o local por `stdio`, arrancado por Claude Code. Los tools se llaman `mcp__<server>__<tool>` y siguen las reglas de permisos. Se añade con `claude mcp add` y se revisa con `/mcp`. Capítulo 13.

memoria automática (auto memory)
:   Las notas que Claude escribe por su cuenta (preferencias, correcciones, contexto) en `~/.claude/projects/<proyecto>/memory/`, compartidas entre los worktrees del repositorio e invisibles para tus compañeros. Capítulos 7 y 15.

`MEMORY.md`
:   El índice de la memoria automática, que se carga en cada sesión hasta doscientas líneas. Capítulo 15.

`/memory`
:   Lista los archivos de instrucciones cargados y activa o desactiva la memoria automática. Sustituye al antiguo atajo `#`, que se eliminó. Capítulos 7 y 15.

`/model`
:   Muestra los modelos de tu plan y cambia el activo. Alias: `opus`, `sonnet`, `haiku`, `fable`, `opusplan`. Capítulos 1 y 2.

modo de permisos
:   Lo que Claude puede hacer sin preguntar. `Shift+Tab` va pasando por auto, Manual, Accept edits y Plan; `dontAsk` y `bypassPermissions` se eligen con `--permission-mode`. Como `defaultMode`, `auto` y `bypassPermissions` solo valen en `~/.claude/settings.json`. Capítulos 2 y 11.

## O

openpyxl
:   La librería de Python que escribe archivos de Excel, fórmulas incluidas. Capítulo 5.

Opus
:   Claude Opus, alias `opus`; Opus 5.5 es el valor por defecto desde septiembre de 2026. `opusplan` usa Opus en Plan Mode y Sonnet para ejecutar. Capítulo 2.

## P

`/permissions`
:   Las reglas activas, con las pestañas Allow, Ask, Deny y Recently denied; cada regla muestra el archivo del que viene. Capítulo 11.

Plan Mode
:   Claude lee y propone un plan sin modificar nada hasta que lo apruebas. Entras con `Shift+Tab`, `/plan` o `--permission-mode plan`; `Ctrl+G` abre el plan en el editor. Capítulos 3 y 4.

plugin
:   Una carpeta que empaqueta skills, agentes, hooks y servidores MCP. En `.claude-plugin/` solo va el manifiesto `plugin.json`; los componentes van en la raíz. El `name` se convierte en el prefijo (`/cc-lab-toolkit:report-pdf`). Se gestiona con `/plugin`, se prueba con `--plugin-dir`, se valida con `claude plugin validate` y se mide con `claude plugin eval`. Capítulo 14.

prompt injection
:   Instrucciones para el modelo escondidas en un contenido externo que lee un tool, como una issue o una página web. Capítulo 13.

## R

RDS
:   La base de datos gestionada de AWS; el Photogallery usa MariaDB, el mismo motor que Sail. Capítulo 23.

reglas allow, ask y deny
:   Excepciones al modo, con la sintaxis `Tool(especificador)`: `Bash(python -m pytest *)`, `Read(./.env)`, `mcp__github__*`. El orden es deny, ask, allow. Una regla `Bash` compara el texto del comando, no el programa. Capítulo 11.

repositorios de apoyo (companion repo)
:   Los repositorios de GitHub del libro. Los nombres de las ramas, como `book/cap-13-wave-1-backend`, siguen la numeración de la primera edición. Ver "Cómo leer este libro".

`REVIEW.md`
:   Las instrucciones para Code Review en GitHub: qué es Important, cuántos Nit, qué ignorar, qué revisar siempre. Capítulo 22.

revisión multi-LLM (cross-LLM review)
:   El mismo changeset y el mismo prompt enviados a modelos distintos (Claude, Gemini, Codex, Kimi), con los resultados agregados por consenso. Capítulo 22.

`/rewind`
:   Devuelve el código, la conversación o ambos a un punto anterior, también con `Esc Esc`. No deshace lo que haya hecho un comando `Bash`. Capítulo 15.

## S

Sanctum
:   El paquete de Laravel para los tokens de API; en el Photogallery cada mutación comprueba la ability del token y la policy. Capítulos 17 y 19.

sandbox
:   El límite que el sistema operativo impone a los comandos de shell y a sus procesos: escritura en la carpeta de trabajo, lectura casi en todas partes salvo las rutas denegadas, red a través de un proxy con una lista de dominios. Seatbelt en macOS, bubblewrap y socat en Linux y WSL 2, sin soporte en Windows nativo. `Read`, `Edit`, los hooks y los servidores MCP quedan fuera. Se activa con `/sandbox`. Capítulos 2 y 11.

scope
:   Dónde se aplica una configuración. Para un servidor MCP: `local` (por defecto), `project` (`.mcp.json` en Git, que hay que aprobar en el primer arranque) y `user`. Para un plugin: user, project, local. Capítulos 13 y 14.

SDD (Spec Driven Development)
:   El método del Photogallery: el código se deriva de `docs/REQUIREMENTS.md`, `docs/DESIGN.md` y `docs/TASKS.md` (124 tareas en 14 fases), escritos y aprobados antes. Capítulos 17 y 18.

sesión
:   Una conversación desde que arrancas hasta que sales. `/resume` (alias `/continue`) la retoma. Capítulos 1 y 15.

sesión en segundo plano
:   Una sesión que trabaja sin ocupar la terminal: `claude --bg --name <nombre> "<prompt>"` o `/background`. Antes de modificar archivos pasa a un worktree y, al terminar, hace commit y push. Se gestiona desde agent view y con `claude attach`, `logs`, `stop`, `rm`. Capítulo 20.

`settings.json`
:   La configuración: `~/.claude/settings.json` (todos los proyectos), `.claude/settings.json` (equipo, en Git), `.claude/settings.local.json` (solo tú, fuera de Git), más las managed settings de la organización. Capítulo 11.

skill
:   Una carpeta con `SKILL.md` y, si hace falta, scripts y referencias. El nombre y la descripción están siempre en el contexto; el cuerpo se carga cuando se necesita. La invocas con `/nombre` o Claude la elige a partir de la descripción, que hay que escribir como un trigger. `/skills` las lista y `/reload-skills` las recarga. Capítulo 9.

skill-creator
:   La skill que crea otras skills mediante una conversación guiada. Capítulo 9.

`/skill-doctor`
:   Cuánto contexto ocupa cada skill y cuánto se usa. Capítulo 15.

SOLID
:   Los cinco principios del diseño orientado a objetos, en el `CLAUDE.md` del Photogallery con ejemplos sacados de su código. Capítulo 18.

Sonnet
:   Claude Sonnet, alias `sonnet`: más rápido y más barato que Opus. Capítulo 2.

spec-critic
:   El subagente que relee las specs como un revisor hostil, a la caza de agujeros de seguridad y de requisitos sin tarea. Capítulo 18.

`/subtask`
:   Un subagente que hereda toda la conversación. Capítulo 10.

Superpowers
:   El plugin de Jesse Vincent con skills para brainstorming, desarrollo guiado por subagentes, depuración sistemática y TDD. Se instala con `/plugin install superpowers@claude-plugins-official`. Capítulos 8 y 16.

## T

tarea atómica
:   Una tarea que lleva el proyecto de un estado coherente al siguiente y se cierra con un commit. En el Photogallery tiene un ID (`T031`), las secciones de `DESIGN.md` que hay que leer y criterios verificables. Capítulos 16 y 18.

tarea huérfana
:   Una feature marcada como hecha pero que se quedó a medias: un endpoint vacío, un componente que nadie importa. Se resuelve con las tres D: Delete, Complete, Document and defer. Capítulo 22.

`/tasks`
:   Los subagentes y los trabajos en segundo plano de la sesión; `Ctrl+X Ctrl+K` los detiene todos. Capítulo 10.

token
:   La unidad de texto de los modelos, más o menos un trozo de palabra. El contexto, los límites y los costes se miden en tokens. Capítulo 1.

tool
:   Una función que se le describe al modelo con nombre, descripción y esquema. El modelo pide la llamada (`tool_use`), el harness la ejecuta y responde con un `tool_result`. Los principales: `Read`, `Edit`, `Write`, `Bash` (que en macOS, Linux y WSL también hace las búsquedas), `WebSearch`, `WebFetch`, `Agent` y los tools MCP. `Ctrl+O` muestra las llamadas. Capítulo 2.

tool search
:   Al arrancar, Claude Code carga solo los nombres de los tools MCP y recupera sus definiciones cuando hacen falta. Capítulo 13.

## U

ultrareview
:   La revisión multiagente en la nube, en research preview: `/code-review ultra` o `claude ultrareview`. Necesita una cuenta de claude.ai; en Pro y Max hay tres ejecuciones gratuitas y después se usan créditos. Capítulo 22.

`ultrathink`
:   Escrito en un prompt, sube el razonamiento solo para ese mensaje. "think hard" no tiene ningún efecto especial. Capítulos 2 y 3.

`/usage`
:   Qué consume los límites del plan, por skill, subagente, plugin y servidor MCP. `/cost` y `/stats` son alias suyos. Capítulos 1 y 15.

## V

vibecoding
:   Ir directo al código a base de prompts, sin spec ni plan. Capítulo 17.

visual companion
:   La parte de la skill de brainstorming de Superpowers que genera mockups HTML y los actualiza mientras los comentas. Capítulo 16.

## W

wave
:   Un grupo de fases del plan que se pueden ejecutar en paralelo en tracks que no comparten archivos. Capítulos 19 y 20.

wave review
:   La revisión de fin de oleada que hacen varios agentes en paralelo, cada uno sobre un aspecto distinto. Capítulo 19.

worker
:   El proceso que ejecuta los jobs de una cola: en el Photogallery, la tabla `jobs` en desarrollo y SQS en producción. Capítulos 21 y 23.

worktree
:   Una segunda carpeta de trabajo del mismo repositorio, con su propia rama. `claude --worktree <nombre>` la crea en `.claude/worktrees/<nombre>`; `.worktreeinclude` lista los archivos ignorados que hay que copiar; `"baseRef": "head"` hace que parta del `HEAD` local; `isolation: worktree` le da uno temporal a cada instancia de un subagente. Capítulo 20.

WSL 2
:   El Linux de Windows, necesario para el sandbox; WSL 1 no está soportado. Capítulos 1 y 2.
