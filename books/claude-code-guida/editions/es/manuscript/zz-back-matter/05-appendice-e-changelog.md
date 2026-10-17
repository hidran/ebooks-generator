# Apéndice E. Changelog

Los cambios del libro, del más reciente al más antiguo. La primera entrada describe esta edición, la segunda resume qué ha cambiado en Claude Code en los cinco meses que separan las dos ediciones y la tercera es la ficha de la primera edición. Al final encontrarás cómo avisar de un error.

## E.1 Segunda edición, octubre de 2026

El texto está alineado con la documentación oficial consultada el 17 de octubre de 2026, cuando la última versión de Claude Code era la 2.1.302 (16 de octubre) y el modelo predeterminado, Claude Opus 5.5.

### Capítulos nuevos

Siete capítulos más, todos nacidos de las lecciones de la actualización de octubre de mi curso sobre Claude Code:

- Capítulo 2, Del modelo al agente: tools, bucle agéntico, permisos y sandbox.
- Capítulo 11, Permisos, modos y sandbox.
- Capítulo 12, Hooks.
- Capítulo 13, MCP. La primera edición lo prometía para una actualización posterior.
- Capítulo 14, Plugins y marketplaces, incluido `claude plugin eval`.
- Capítulo 15, Contexto y memoria bajo control.
- Capítulo 20, Oleadas en paralelo con worktrees, `/goal` y agent view.

Los capítulos del 11 al 15 forman la nueva Parte IV, Control y automatización, y todos trabajan sobre el mismo proyecto de laboratorio.

### Contenidos fusionados

El capítulo 22 une la QA antes del deploy y la revisión multi-LLM de la primera edición con la review integrada de Claude Code: `/code-review` con sus niveles de effort, `--fix` y `--comment`, el archivo `REVIEW.md` para Code Review en GitHub y ultrareview en la nube. El segundo modelo se mantiene, pero solo para las partes críticas.

Los capítulos 8 y 9 siguen la fusión entre comandos personalizados y skills: el capítulo 8 presenta el formato `.claude/commands/` y el 9 parte de que comandos y skills son un único sistema. En el capítulo 10, los agentes de la comunidad llegan a través de plugins en lugar de con un `git clone` en `~/.claude/`.

### La nueva numeración

Las partes son seis. La antigua Parte IV (landing page) es ahora la Parte V, y la antigua Parte V (Photogallery), la Parte VI. Los números de sección siguen al capítulo: el antiguo §13.3 es el §19.3.

| Segunda edición | Primera edición | Título |
|---|---|---|
| 1 | 1 | Qué es Claude Code |
| 2 | nuevo | Del modelo al agente: tools, bucle agéntico, permisos y sandbox |
| 3 | 2 | Los primeros prompts útiles |
| 4 | 3 | Analizar un CSV con Plan Mode |
| 5 | 4 | De CSV a Excel, informes tabulares con Python |
| 6 | 5 | Gráficos, dashboards e informes PDF |
| 7 | 6 | CLAUDE.md, la memoria del proyecto |
| 8 | 7 | Comandos personalizados y el plugin Superpowers |
| 9 | 8 | Skills, de comando a capacidad reutilizable |
| 10 | 9 | Agentes y subagentes, cuándo usar cada cosa |
| 11 | nuevo | Permisos, modos y sandbox |
| 12 | nuevo | Hooks, automatización determinista |
| 13 | nuevo | MCP, conectar Claude Code con servicios externos |
| 14 | nuevo | Plugins y marketplaces, empaquetar skills, agentes y hooks |
| 15 | nuevo | Contexto y memoria bajo control |
| 16 | 10 | Una landing page de la idea al deploy en Firebase |
| 17 | 11 | Photogallery, del prompt a las especificaciones |
| 18 | 12 | Spec Driven Development |
| 19 | 13 | Ejecución y code review, de las primeras tareas a la wave review |
| 20 | nuevo | Oleadas en paralelo con worktrees, /goal y agent view |
| 21 | 14 | Features en marcha |
| 22 | 15 | QA antes del deploy, /code-review y revisión multi-LLM |
| 23 | 16 | Deploy en AWS con CloudFormation |

Los apéndices siguen siendo cinco, de la A a la E, en el mismo orden.

### Las actualizaciones, capítulo a capítulo

Los capítulos nuevos están escritos para la versión actual. En los demás, estos son los cambios que afectan a los comandos o al código.

- Capítulo 1. La instalación pasa por el instalador nativo (`curl -fsSL https://claude.ai/install.sh | bash`, en Windows `irm https://claude.ai/install.ps1 | iex`), que se actualiza solo. Homebrew y WinGet son alternativas con actualización manual; npm es una opción avanzada y requiere Node.js 22 o posterior. Entran `claude doctor` y `claude update`. `/usage` sustituye a `/cost`, que es un alias suyo desde la versión 2.1.118 (abril de 2026), y `/vim` deja paso a `/config`, que también acepta la forma `clave=valor`. El atajo `#` para la memoria ya se había eliminado en la 2.0.70 (diciembre de 2025): la primera edición todavía lo presentaba. Las sesiones arrancan en auto mode.
- Capítulo 3. Plan Mode se activa con `Shift+Tab`, con `/plan` o con `claude --permission-mode plan`, y la aprobación ofrece `Yes, and use auto mode`. `Ctrl+G` abre el plan en el editor. Para razonar más se sube el effort con `/effort`; "think hard" no es una palabra clave, y `ultrathink` vale para un solo prompt.
- Capítulo 4. Las mismas actualizaciones de Plan Mode; para los archivos grandes entran `/context` y `/compact` con las instrucciones sobre qué conservar.
- Capítulos 5 y 6. Cambia sobre todo la prosa. En el capítulo 6 la skill frontend-design se instala como plugin desde el marketplace oficial (`frontend-design@claude-plugins-official`).
- Capítulo 7. Los niveles de `CLAUDE.md` son cuatro (organización, usuario, proyecto, local). Entran las reglas en `.claude/rules/` con `paths:`, la memoria automática y la lectura nativa de `AGENTS.md` desde la versión 2.1.277. El límite recomendado es de menos de doscientas líneas.
- Capítulo 8. Los comandos personalizados se han integrado en las skills: `.claude/commands/` sigue funcionando, pero para el trabajo nuevo se usa `.claude/skills/<nombre>/SKILL.md`. Superpowers se instala desde el marketplace oficial con `/plugin install superpowers@claude-plugins-official`; el repositorio que indicaba la primera edición no era el del plugin, que está en `obra/superpowers`.
- Capítulo 9. La description, junto con `when_to_use`, se trunca a partir de 1.536 caracteres. El skill-creator se instala desde `claude-plugins-official`, `/skill-doctor` muestra cuánto contexto ocupa cada skill y desde la versión 2.1.218 una skill con `context: fork` se ejecuta en segundo plano.
- Capítulo 10. El asistente de `/agents` ya no existe desde la versión 2.1.198: el agente se crea pidiéndoselo a Claude o escribiendo el archivo en `.claude/agents/`. El ejemplo es ahora `laravel-controller-reviewer`, en lugar del `nest-controller-reviewer` de la primera edición. El tool `Task` se llama `Agent`. Los subagentes se ejecutan en segundo plano, se siguen con `/tasks` y se detienen con `Ctrl+X Ctrl+K`; `/subtask` delega una tarea que necesita toda la conversación.
- Capítulo 16. El stack es el real del repositorio: React 19, Vite 6, Tailwind CSS 4.2 y Vitest 4, en lugar de React 18 y Vite 5.
- Capítulo 17. El stack de la Photogallery es el del repositorio companion: Laravel 13 como API REST bajo `/api/v1`, Filament v5 para el admin, React 19 con Vite 6 y Tailwind CSS v4 para la SPA, tokens Sanctum. NestJS queda solo como alternativa descartada durante la elección del stack, y la sección 17.1 explica por qué.
- Capítulo 18. Los tres archivos están en `docs/REQUIREMENTS.md`, `docs/DESIGN.md` y `docs/TASKS.md`, ya no en `.spec/`, y el `CLAUDE.md` del proyecto es el del repositorio. El texto distingue las 112 tareas en 13 fases de la rama del capítulo de las 124 tareas en 14 fases de `main`. Las restricciones que no se pueden saltar pasan a permisos, hooks y `/goal`.
- Capítulo 19. Los ejemplos de review tratan controladores, policies y Form Requests de Laravel. Los subagentes en paralelo comparten el working tree, así que las tareas paralelas sobre el mismo código van en los worktrees del capítulo 20.
- Capítulo 21. Las referencias a fases, waves y tareas (T070, T121, la Fase 6.5) siguen el `docs/TASKS.md` del repositorio companion.
- Capítulo 22. `/review` es un alias de `/code-review` desde la versión 2.1.223. `REVIEW.md` personaliza Code Review en GitHub (planes Team y Enterprise) pero no el comando local, que solo lee `CLAUDE.md`. Ultrareview se lanza con `/code-review ultra` o con `claude ultrareview`.
- Capítulo 23. El backend en contenedor es Laravel en lugar de NestJS, con `config:cache` ejecutado al arrancar el contenedor, y la base de datos es RDS MariaDB en lugar de MySQL. Los comandos de deploy pasan por una regla `ask` en `.claude/settings.json`.

En todo el libro el modelo de referencia es Claude Opus 5.5 con un millón de tokens de contexto. He quitado las figuras con una interfaz superada (Sonnet 4.6 en `/model`, `/cost`, el asistente de `/agents`).

### Las ramas companion conservan los números antiguos

Las ramas de los repositorios se crearon para la primera edición y no las he renombrado, para no romper los enlaces que ya circulan. El texto cita siempre el nombre exacto; esta es la correspondencia completa.

| Rama | Repositorio | Capítulo |
|---|---|---|
| `book/cap-10-1-mockups`, `book/cap-10-2-spec`, `book/cap-10-3-execution`, `book/cap-10-5-deploy-ready` | `fluentaipro-claude-landingpage` | 16 |
| `book/cap-11-prompts-and-spec` | `claude-code-book-photogallery` | 17 |
| `book/cap-12-sdd-three-files` | `claude-code-book-photogallery` | 18 |
| `book/cap-13-wave-1-backend`, `book/cap-13-wave-2-api` | `claude-code-book-photogallery` | 19, punto de partida del 20 |
| `book/cap-14-phases-complete` | `claude-code-book-photogallery` | 21, punto de partida del 22 |
| `book/cap-15-post-review-fixes` | `claude-code-book-photogallery` | 22, coincide con `main` |

La primera edición citaba también ramas de partida para los ejercicios en el repositorio `claude-code-book-snippets` (`cap-01-hello-claude`, `cap-03-csv-analysis` y otras), que nunca se publicaron: el repositorio solo tiene `main`, con una carpeta de prompts por capítulo. En esta edición cada ejercicio parte de algo que creas tú, y los datos de la Parte II los genera el script `genera_dati.py` del capítulo 4.

El capítulo 23 todavía no tiene rama: `book/cap-16-aws-deploy` llegará cuando el deploy en AWS del repositorio esté completo.

### El texto

He reescrito la prosa de cada capítulo, quitando frases efectistas, listas en negrita y resúmenes que repetían el capítulo. La apertura con lo que vas a aprender y el cierre con resumen y ejercicio se mantienen, más breves, y cada ejercicio tiene una condición de finalización clara. Los recuadros son de cinco tipos, descritos en "Cómo leer este libro".

Las ediciones en inglés y en español se han vuelto a traducir a partir del nuevo texto italiano.

En el Apéndice D he revisado todos los enlaces y he quitado los que no podía verificar: la tabla de modelos (ahora los modelos están en el capítulo 2), newsletters, libros recomendados, herramientas alternativas y la antigua dirección de la documentación en `docs.anthropic.com`. En lugar de los contactos personales están las issues del repositorio de los snippets.

## E.2 Qué ha cambiado en Claude Code entre mayo y octubre de 2026

La primera edición corresponde más o menos a las versiones 2.1.128-2.1.158 de mayo de 2026. Aquí abajo están los cambios que afectan al libro y que la primera edición no trataba, con versión, fecha y capítulo. Fechas y versiones vienen del changelog y del resumen semanal; cuando falta el día indico el mes o la semana del resumen.

- Mayo, 2.1.139: `/goal`, Claude sigue trabajando hasta que una condición se cumple. Capítulo 20.
- 9 de junio, 2.1.170: llega Fable 5, el modelo más capaz, nunca activo por defecto. Capítulo 2.
- Junio, semana 24: un subagente puede lanzar otros subagentes, hasta cinco niveles en las cadenas en segundo plano. Capítulo 10.
- Junio, semana 25: `/config clave=valor`, y las reglas de permisos que miran los parámetros de un tool, como `Agent(model:opus)`. Capítulos 1 y 11.
- Junio, semana 26: el modo shell `!` recibe una respuesta de Claude, las solicitudes de permiso de los subagentes en segundo plano aparecen en la sesión principal, y llegan `claude mcp login` y `logout`. Capítulos 1, 10 y 13.
- 30 de junio, 2.1.197: Sonnet 5 pasa a ser durante poco tiempo el modelo predeterminado de los planes Pro y Team Standard. Capítulo 2.
- 1 de julio, 2.1.198: se elimina el asistente de `/agents`. Capítulo 10.
- Julio, semana 27: los subagentes se ejecutan en segundo plano por defecto. Capítulo 10.
- Julio, semana 28: `/doctor` pasa a ser una comprobación del setup que también sabe corregir. Capítulo 15.
- 17 de julio, 2.1.212: `/fork` copia la conversación en una sesión en segundo plano, `/subtask` lanza el subagente con toda la conversación, `/background` separa la sesión; todo se sigue desde el agent view (`claude agents`). Capítulos 10, 15 y 20.
- Julio, 2.1.218: las skills con `context: fork` se ejecutan en segundo plano. Capítulo 9.
- 24 de julio, 2.1.219: Opus 5 pasa a ser el modelo predeterminado. Capítulo 2.
- 4 de agosto, 2.1.222: se elimina Ultraplan; para planificar queda Plan Mode. Capítulo 3.
- 6 de agosto, 2.1.223: `/review` pasa a ser un alias de `/code-review`; ultrareview se lanza con `/code-review ultra`. Capítulo 22.
- 11 de agosto, 2.1.228: auto mode pasa a ser el modo inicial para Pro, Max y Team en macOS, Linux y WSL, y el 14 de agosto (2.1.233) en Windows. Capítulos 2 y 11.
- Agosto, semana 33: en las sesiones interactivas, los subagentes que lanza Claude arrancan en fork mode, en segundo plano. Capítulo 10.
- 1 de septiembre, 2.1.257: Fable 5.1. Capítulo 2.
- 11 de septiembre, 2.1.269: `claude plugin eval` mide un plugin frente a una baseline sin el plugin. Capítulo 14.
- 18 de septiembre, 2.1.277: Claude Code lee `AGENTS.md` cuando no hay un `CLAUDE.md`. Capítulo 7.
- 22 de septiembre, 2.1.280: Opus 5.5 pasa a ser el modelo predeterminado en todos los planes de suscripción. Capítulo 2.
- 25 de septiembre, 2.1.283: auto mode se extiende a los proveedores de terceros, y entra `/doctor prompt-audit`. Capítulos 11 y 15.
- 28 de septiembre, 2.1.284: auto mode para todos los planes y proveedores, y Sonnet 5.5. Capítulos 2 y 11.
- Principios de octubre, 2.1.287: las Claude Mods, módulos de hooks en JavaScript. Capítulo 14, solo como mención.
- 7 de octubre, 2.1.293: Haiku 5.5. Capítulo 2.
- 16 de octubre, 2.1.302: los subagentes en fork pasan a ser el comportamiento predeterminado también en `claude -p`, en el Agent SDK, en la app de escritorio y en VS Code. Capítulo 10.

## E.3 Primera edición, mayo de 2026

Primera publicación en Amazon KDP, en eBook y en paperback impreso bajo demanda.

El libro tenía 16 capítulos, unas 90.000 palabras, en cinco partes: Fundamentos, Análisis de datos, Ampliar Claude Code, Landing page y Photogallery. Los apéndices eran los mismos cinco de hoy. Había más de 50 figuras capturadas de Claude Code y dos repositorios companion, Photogallery y snippets.

Los modelos de referencia eran Opus 4.7, Sonnet 4.6 y Haiku 4.5; las versiones de Claude Code de aquel periodo eran las 2.1.1xx.

La ficha del libro indicaba como stack de la Photogallery NestJS 10, Prisma 5, MySQL 8, React 18 y TanStack Query. Era la hipótesis de partida del capítulo sobre las especificaciones, no el proyecto del repositorio companion, que usa Laravel 13, Filament v5 y React 19: la segunda edición ha corregido el texto en consecuencia.

La primera edición anunciaba una actualización con un capítulo sobre MCP, si la especificación se estabilizaba. Ese capítulo es el 13 de esta edición.

## E.4 Avisar de un error

Abre una issue en el repositorio `github.com/hidran/claude-code-book-snippets` con la etiqueta `errata`, y escribe:

- la página (eBook) o el capítulo y la sección (paperback);
- qué dice el libro;
- qué ha pasado de verdad en tu instalación, con la salida de `claude --version`.

Las correcciones verificadas entran en la revisión siguiente y en este apéndice. Si te parece bien, quien haya enviado el aviso aparecerá en los agradecimientos.

No persigo cada novedad menor de Claude Code. Actualizo el libro cuando un cambio afecta a la forma de trabajar: un comando renombrado o eliminado, un modelo nuevo o retirado, un enlace roto, un procedimiento que tiene uno mejor. Las funciones nuevas que no cambian el flujo de trabajo se quedan fuera, hasta que lo cambien. En Kindle recibes las versiones nuevas activando las actualizaciones automáticas de libros, como se explica en "Cómo leer este libro".
