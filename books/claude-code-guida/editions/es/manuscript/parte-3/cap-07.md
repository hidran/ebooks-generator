# Capítulo 7. CLAUDE.md, la memoria del proyecto

::: {.chapter-goals}
[Qué aprenderás]{.callout-title}

- dónde viven los archivos `CLAUDE.md` y cómo se suman los cuatro niveles;
- qué escribir en ellos para que Claude lo siga, y qué dejar fuera;
- cómo generar el primer archivo con `/init` y mantenerlo por debajo de las doscientas líneas con los imports y las reglas de `.claude/rules/`;
- qué pasa cuando el repositorio ya tiene un `AGENTS.md`.

[Requisitos previos]{.callout-title}

Un proyecto real en el que probar, aunque sea pequeño. Sirve el de análisis de datos de los capítulos 4-6.

:::

Imagina que cada mañana contratas a un desarrollador nuevo. Le explicas el proyecto, qué gestor de paquetes usáis, dónde está la función que gestiona los errores, y durante todo el día trabaja bien. A la mañana siguiente vuelve a ser su primer día: hace las mismas preguntas y aplica las convenciones que conoce él, no las vuestras.

Sin un `CLAUDE.md`, con Claude Code pasa exactamente eso. Cada sesión empieza vacía. Claude no sabe que en tu proyecto se usa pnpm y no npm, que el estado global está en `store/`, que los tests se escriben con Vitest, que los mensajes de error están en español. Así que adivina, y elige la solución más común, que a menudo no es la tuya.

`CLAUDE.md` es un archivo Markdown que Claude Code carga en el contexto al inicio de cada sesión, antes de tu primer prompt. En él escribes lo que, si no, repetirías cada vez: los comandos de build y de test, las convenciones, las reglas del tipo "haz siempre" y "no hagas nunca". En el capítulo 2 lo viste en la tabla de mecanismos, en la entrada "texto cargado en el contexto al inicio de la sesión". Esa definición explica tanto por qué funciona como dónde deja de funcionar.

## 7.1 Qué es CLAUDE.md

No tiene una sintaxis especial ni un esquema obligatorio: es Markdown normal, con títulos y listas. Claude Code lo lee al arrancar y el texto se queda en el contexto durante toda la sesión, así que acompaña a cada mensaje tuyo. Después de `/clear` la conversación vuelve a empezar de cero y `CLAUDE.md` entra de nuevo con la sesión nueva. Después de `/compact` el archivo de la raíz se vuelve a leer del disco, de modo que las instrucciones escritas ahí no dependen del resumen.

### Los cuatro niveles

Claude Code busca instrucciones en cuatro sitios:

| Nivel | Dónde está | Quién lo ve |
|---|---|---|
| Organización | macOS `/Library/Application Support/ClaudeCode/CLAUDE.md`, Linux y WSL `/etc/claude-code/CLAUDE.md`, Windows `C:\Program Files\ClaudeCode\CLAUDE.md` | Todos los usuarios de la máquina, lo gestiona el departamento de IT |
| Usuario | `~/.claude/CLAUDE.md` | Solo tú, en todos los proyectos |
| Proyecto | `./CLAUDE.md` o `./.claude/CLAUDE.md` | El equipo, a través de Git |
| Local | `./CLAUDE.local.md` | Solo tú, en este proyecto |

El nivel de organización (managed policy) lo distribuye el departamento de IT de una empresa, con las reglas que valen para todos.

El archivo de usuario contiene las preferencias que te llevas a cualquier repositorio: el idioma de las respuestas, los mensajes de commit en inglés con Conventional Commits, el hecho de que prefieres respuestas breves. Es opcional, y mucha gente no lo usa.

El archivo de proyecto es el que más cuenta. Está en la raíz, va a Git y quien clona el repositorio hereda las instrucciones junto con el código. Si prefieres una raíz limpia, puedes ponerlo en `.claude/CLAUDE.md`; el resultado es el mismo.

`CLAUDE.local.md` es tu versión privada del archivo de proyecto: la URL de tu entorno de pruebas, la base de datos local con un nombre distinto del de tus compañeros, una nota sobre lo que estás haciendo esta semana. Añádelo a `.gitignore` en cuanto lo crees.

En un monorepo también puedes poner un `CLAUDE.md` en una subcarpeta, por ejemplo `frontend/CLAUDE.md` y `backend/CLAUDE.md`. Los archivos de las carpetas por encima de aquella en la que lanzas `claude` se cargan al arrancar. Los de las subcarpetas entran solo cuando Claude lee un archivo que está dentro: quien trabaja en el frontend no carga con las reglas del backend.

### Cómo se combinan

Claude Code no elige un archivo: los carga todos, del más general al más específico, y el modelo ve un único bloque de instrucciones. Si en el archivo de usuario pone "gráficos siempre con tema oscuro" y en el proyecto de un cliente hace falta el tema claro porque el informe se imprime, escríbelo como una excepción explícita: "en este proyecto usa el tema claro en lugar del oscuro". Dos instrucciones que se contradicen sin explicación dejan que Claude elija por su cuenta, y no siempre elige la que querías. En el capítulo 15 verás `/doctor prompt-audit`, que encuentra estas contradicciones por ti.

### Qué longitud debe tener

La recomendación oficial es quedarse por debajo de las doscientas líneas por archivo. Hay dos motivos. El primero es el coste: ese texto ocupa contexto en cada sesión y se vuelve a leer en cada turno, lo necesites o no. El segundo pesa más: un archivo largo se sigue peor. Con trescientas líneas de instrucciones, las cinco que importan de verdad se pierden entre las demás.

El límite técnico es mucho más alto (los archivos de hasta 4 MiB se cargan enteros, los más grandes se omiten), y hasta la ventana de un millón de tokens tendría sitio. Pero un archivo largo sigue siendo un archivo que se sigue peor. Cuando crezca, mueve las instrucciones que valen para una sola zona del código a reglas que se cargan solo cuando hacen falta (apartado 7.5).

## 7.2 Qué escribir dentro

Parte de una pregunta: ¿qué tiene que saber Claude para no equivocarse en este proyecto? Te lleva a elegir solo lo que cambia el código que produce, en lugar de llenar el archivo con todo lo que sabes.

Después escribe cada instrucción de forma que se pueda comprobar. "Usa dos espacios de sangría" funciona mejor que "formatea bien el código"; "ejecuta `pnpm lint` antes de cada commit" funciona mejor que "mantén el código limpio". Una instrucción verificable la compruebas en el diff, y Claude sabe cuándo la ha cumplido.

La información que tiene sentido en un `CLAUDE.md` cae casi siempre en seis categorías.

### El stack, con las versiones

Claude conoce muchas versiones de muchos frameworks. Sin indicaciones elige la que ha visto más a menudo, que puede no ser la tuya.

```markdown
## Stack

- Runtime: Node.js 22 LTS
- Framework: NestJS 11
- ORM: Prisma 6 (PostgreSQL)
- Frontend: React 19 + TypeScript 5
- Styling: Tailwind CSS 4
- Test: Vitest 3 + Testing Library
- Gestor de paquetes: pnpm (NO uses npm ni yarn)
```

La línea del gestor de paquetes es la que más disgustos te ahorra. Si el repositorio usa pnpm y Claude lanza `npm install`, te encuentras con un `package-lock.json` espurio al lado de `pnpm-lock.yaml` y con versiones distintas de las del equipo.

### Las convenciones que no se ven en el código

Escribe solo las que Claude no deduce por sí mismo. Si `tsconfig.json` tiene `"strict": true`, no hace falta repetirlo.

```markdown
## Convenciones

- Componentes React: function components con TypeScript, nada de class components
- Nombres de archivo: kebab-case; componentes React en PascalCase
- Imports: rutas absolutas desde `src/` con el alias `@/`
- Errores: patrón Result<T, E>, nunca throws sueltos
- Comentarios en español, docstrings en inglés
- Nada de `console.log` en el código con commit: usa `logger` de `src/utils/logger`
```

### Los comandos del proyecto

Aquí se ve la diferencia entre un Claude que lanza el comando correcto a la primera y uno que prueba `npm run build` porque es el default más extendido.

```markdown
## Comandos

- Dev: `pnpm dev` (frontend en el puerto 3000, API en el 4000)
- Build: `pnpm build`
- Test: `pnpm test` (todos) o `pnpm test:unit` (solo unitarios)
- Lint: `pnpm lint && pnpm type-check`, siempre los dos antes del commit
- Migraciones: `pnpm db:migrate` (nunca `prisma migrate deploy` a mano)
- Seed: `pnpm db:seed`, sobrescribe los datos
```

### Lo que no hay que hacer

A menudo es la sección más útil. Claude tiende a hacer lo que parece funcionar, aunque en tu proyecto sea un error, y las prohibiciones explícitas le cierran los caminos que ya has descartado.

```markdown
## NUNCA hagas

- No instales dependencias sin haberlo hablado antes
- No modifiques `src/generated/`: lo genera Prisma
- No uses `fetch` directamente: pasa por `src/lib/api-client.ts`
- No añadas `any` sin un comentario que explique por qué
- No uses `Date.now()` en los tests: usa `vi.setSystemTime()`
```

### Los patrones, con un ejemplo de referencia

Si el proyecto tiene patrones que se repiten y que Claude podría no seguir de forma espontánea, descríbelos e indica el archivo que hay que tomar como modelo. Claude va a leerlo y copia la estructura.

```markdown
## Arquitectura

- Acceso a datos con el repository pattern: modelo en `src/repositories/user.repository.ts`
- Escrituras en `commands/`, lecturas en `queries/`, nunca en el mismo archivo
- Validación de las entradas siempre con un schema de Zod
- Formularios: React Hook Form con zodResolver, nada de useState para el estado del formulario
```

### El vocabulario del dominio

Cada proyecto tiene sus propias palabras, y "cliente" puede significar cosas distintas en la base de datos, en el código y en las reuniones. Fijar los términos evita que un malentendido se convierta en un bug.

```markdown
## Dominio

- "Usuario" = persona registrada (entidad `User`)
- "Cliente" = empresa con un contrato activo (entidad `Organization`)
- Un usuario puede pertenecer a varias organizaciones
- Estado del pedido: DRAFT → PENDING → PROCESSING → COMPLETED | CANCELLED
```

### Notas para los compañeros, a coste cero

Los comentarios HTML a nivel de bloque se eliminan antes de que el texto llegue a Claude. Puedes dejar una nota para quien mantiene el archivo (por qué existe una regla, quién la pidió, dónde está el resto) sin consumir contexto:

```markdown
## Reglas

- No modifiques nunca los archivos de `data/`: trabaja con copias en `tmp/`
- Cada función nueva en `src/` tiene un test en `tests/`

<!-- Nota para quien mantiene el archivo: las reglas de Python están en .claude/rules/python.md -->
```

### Un ejemplo real: el Photogallery

El proyecto de la Parte VI tiene un `CLAUDE.md` escrito en inglés, como el resto de la documentación del repositorio companion. El capítulo 18 lo construye paso a paso (apartado 18.4). Aquí ves un extracto, para fijarte en la forma de las reglas:

```markdown
# CLAUDE.md — PhotoGallery Pro

> The project constitution. Loaded into every Claude Code session.
> Authoritative for HOW we work; defers to `docs/REQUIREMENTS.md` (what to
> build) and `docs/DESIGN.md` (technical blueprint) for content. Atomic work
> lives in `docs/TASKS.md`.

## Critical rules

1. Always read `docs/REQUIREMENTS.md` and `docs/DESIGN.md` before implementing
   tasks. If the task is ambiguous and the docs don't resolve it, stop and ask.
4. One task = one commit. Conventional Commits format: `<type>(<scope>): <subject>`.
5. Tests run before commits. No `--no-verify`, no `.skip`, no "tests later".
7. Every endpoint wraps its payload in `{ "data": ... }`. No exceptions.
8. Every primary key is UUID v7 via the `HasUuidV7` trait. Stored as `CHAR(36)`.
13. Tailwind v4 setup is non-negotiable. No `tailwind.config.js`, no
    `postcss.config.js`, no `autoprefixer`.
```

Casi todas las reglas se comprueban mirando el diff: o el endpoint devuelve `{ "data": ... }` o no, o la clave primaria es un UUID v7 o no. Y muchas remiten a un documento (`DESIGN.md`) en lugar de copiarlo. El archivo completo tiene 391 líneas, casi el doble del objetivo, y buena parte se refiere a una sola zona del código: el estilo PHP vale para `backend/`, las reglas de Tailwind para `frontend/`. En el apartado 7.5 ves cómo lo dividiría yo.

## 7.3 Qué no escribir

Un `CLAUDE.md` inflado es peor que uno escueto: ocupa contexto y diluye las instrucciones que importan. Los errores más comunes son seis.

El primero es la documentación de las APIs: la lista de endpoints, los parámetros, las firmas de los métodos. Eso está en el código, en los comentarios, en un archivo OpenAPI, y Claude lo lee cuando lo necesita.

Lo mismo vale para el inventario de funciones ("el proyecto tiene `getUserById()`, `createUser()`, `deleteUser()`..."). Claude las encuentra solo explorando el código. Si una función hay que usarla de una manera concreta, escríbelo como patrón, con el archivo de referencia.

Luego están las explicaciones didácticas. Claude ya sabe qué es Prisma y cómo funciona un JWT. El "por qué elegimos esta tecnología" le interesa a un compañero nuevo, y para él está el README o un ADR. En `CLAUDE.md` van instrucciones.

Las credenciales no van nunca: claves de API, tokens, contraseñas, cadenas de conexión con usuario y contraseña. El archivo de proyecto va a Git, por tanto al remoto, y de ahí a cualquier sitio donde se clone el repositorio. Los secretos van en el `.env` (fuera de Git) o en un gestor de secretos.

También se quedan fuera las roadmaps y las notas temporales. "En marzo añadiremos X" o "estamos valorando pasar a PostgreSQL" no cambian el código que Claude escribe hoy. Van en el gestor de tareas o en las especificaciones.

El último error son las intenciones sin una regla detrás. "Intentamos escribir código limpio" no orienta ninguna decisión. Si quieres funciones pequeñas, escribe una regla que se pueda verificar: "una función de más de 30 líneas se marca con un `TODO:REFACTOR`".

Para cada sección que estás a punto de añadir, la prueba es esta: sin esta información, ¿escribiría Claude un código distinto y equivocado? Si la respuesta es no, la sección sobra.

::: {.callout .callout-warning}
[Atención]{.callout-title}

`CLAUDE.md` orienta a Claude, pero no lo obliga. Es texto en el contexto: normalmente se sigue, pero en una sesión larga o ante una petición explícita tuya puede perder peso. "No leas nunca el archivo `.env`" escrito aquí es una indicación; una regla deny en `.claude/settings.json` (capítulo 11) o un hook `PreToolUse` (capítulo 12) lo impiden de verdad, porque Claude Code los aplica antes de que salga la llamada. Usa `CLAUDE.md` para explicar cómo trabajar, y los permisos y los hooks para las restricciones.
:::

## 7.4 Generar el primer archivo con /init

Escribir a mano el primer `CLAUDE.md` de un proyecto existente es aburrido, y Claude puede prepararte el borrador. Desde la raíz del proyecto, en una sesión de Claude Code:

```text
/init
```

Claude explora el repositorio: lee `package.json` o `pyproject.toml`, los archivos de configuración (`tsconfig.json`, la configuración de ESLint, la de Vite), la estructura de carpetas y algunos archivos fuente para entender los patrones en uso. Después escribe una primera versión de `CLAUDE.md` con el stack (las versiones las saca de los manifiestos), los comandos que ha encontrado en los scripts, la estructura principal y algunas convenciones deducidas del código. Si ya existe un `CLAUDE.md`, `/init` no lo sobrescribe: te propone mejoras.

![/init en acción: Claude explora el proyecto y prepara CLAUDE.md.](figures/cap-07/fig-01.png)

<!-- TODO screenshot: rifare fig-01 con la UI attuale (barra di stato con il modello di ottobre 2026 e auto mode), a risoluzione più alta e senza nome dell'account e percorso personale nell'intestazione -->

Si quieres más control, lanza Claude Code con la variable `CLAUDE_CODE_NEW_INIT=1`. `/init` pasa a un flujo interactivo: en lugar de escribir el archivo enseguida, te pregunta qué preparar (los archivos `CLAUDE.md`, también el personal `CLAUDE.local.md`, skills y hooks), explora el código con un subagente, te hace preguntas sobre lo que no consigue deducir y te enseña una propuesta para revisar.

```bash
CLAUDE_CODE_NEW_INIT=1 claude
```

### Lo que tienes que añadir tú

El borrador de `/init` es un buen punto de partida, pero casi siempre le faltan tres cosas que no están en el código. Las convenciones semánticas: el código dice que usas TypeScript strict, no que los mensajes de error van en español. Las reglas operativas del equipo: `/init` encuentra `pnpm dev` en los scripts, pero "ejecuta `pnpm lint && pnpm type-check` antes del commit" es una decisión vuestra. Y las prohibiciones, que existen porque alguien se equivocó una vez, una historia que el código no cuenta.

### Modificar el archivo

Puedes abrir `CLAUDE.md` con tu editor, o escribir `/memory` en la sesión: ves la lista de archivos de instrucciones cargados (usuario, proyecto, local, reglas) y abres el que quieras modificar. Desde el mismo menú controlas también la memoria automática, que encontrarás en el apartado 7.5.

![El CLAUDE.md que /init generó para el proyecto de análisis de datos: pipeline de gráficos, paleta de los planes y carpetas de salida.](figures/cap-07/fig-02.png)

En las guías de 2025 todavía aparece el atajo `#`: un mensaje que empezaba por `#` iba directo a `CLAUDE.md`. Se eliminó en diciembre de 2025. Hoy se pide con palabras:

```text
añade a CLAUDE.md, en la sección NUNCA hagas: no modifiques los archivos de src/generated/
```

### El flujo completo

1. Lanza `/init` en la raíz del proyecto.
2. Abre el `CLAUDE.md` generado y léelo entero. Quita las partes obvias o redundantes, como la lista de carpetas que Claude ve por sí mismo.
3. Añade las tres cosas que faltan: convenciones, reglas operativas, prohibiciones.
4. Sal y vuelve a lanzar `claude`, o haz `/clear`, y luego pide algo que debería activar tus convenciones. Si Claude usa pnpm, crea los archivos en las carpetas correctas y sigue el patrón que has indicado, el archivo funciona. Si no, vuelve al paso 3.
5. Haz commit del archivo:

```bash
git add CLAUDE.md
git commit -m "docs: add CLAUDE.md"
```

### Si el repositorio ya tiene un AGENTS.md

Muchos proyectos tienen un `AGENTS.md`, el archivo de instrucciones que leen otros agentes de programación. Desde la versión 2.1.277 (septiembre de 2026) Claude Code lo lee de forma nativa: si en la carpeta de trabajo y en las superiores no hay ni un `CLAUDE.md` ni un `CLAUDE.local.md`, usa `AGENTS.md`. Un repositorio preparado para otro agente funciona a la primera.

El comportamiento se cambia en `/config`, en la opción Project instructions. El valor por defecto es `claude-md-or-agents-md` (el que acabo de describir); `claude-md-and-agents-md` carga los dos, `claude-md` ignora `AGENTS.md`, y `managed-only` carga al arrancar solo el `CLAUDE.md` gestionado por la organización y la memoria automática.

Las variantes `AGENTS.local.md` y `AGENTS.override.md` y la carpeta `.agents/` no se leen.

Si en el proyecto conviven los dos archivos y quieres una única fuente, escribe las instrucciones comunes en `AGENTS.md` e impórtalo desde `CLAUDE.md` con una línea `@AGENTS.md` (los imports están en el apartado siguiente). Debajo añade solo lo que se refiere a Claude Code. Si en cambio vienes de Codex o de Gemini CLI con una configuración ya escrita, `/init` se da cuenta y te propone `/import` para traerla.

## 7.5 Mantenerlo corto y al día

Un `CLAUDE.md` escrito una vez y luego olvidado envejece rápido. A los seis meses describe un stack que has actualizado y comandos que has renombrado, y Claude sigue las instrucciones viejas en lugar de mirar el código tal como es hoy. Para mantenerlo corto, Claude Code te da dos herramientas: los imports y las reglas por ruta. Para mantenerlo al día hace falta un poco de disciplina.

### Los imports con @

Una línea `@ruta/archivo` dentro de `CLAUDE.md` incluye otro archivo. La ruta es relativa al archivo que importa; también valen rutas absolutas y las que empiezan por `~`.

```markdown
# Photogallery

Visión general y comandos: @README.md
Instrucciones compartidas con los demás agentes: @AGENTS.md

## Preferencias personales
- @~/.claude/photogallery-preferenze.md
```

La última línea es una alternativa a `CLAUDE.local.md`: tus preferencias están en un archivo de tu home, y cada worktree del proyecto las encuentra con el mismo import. Los imports se pueden anidar hasta cuatro niveles. Una `@` dentro de un bloque de código o entre comillas invertidas se ignora. Si la ruta tiene espacios, pon delante de cada uno un `\`. Cuando un import apunta fuera del proyecto, la primera vez Claude Code te pide que lo apruebes.

Los imports sirven para organizar el texto. El archivo importado se carga al arrancar como si estuviera escrito ahí y cuesta el mismo contexto: para cargar instrucciones solo cuando hacen falta están las reglas.

### Las reglas en .claude/rules/

La carpeta `.claude/rules/` contiene archivos Markdown, también en subcarpetas, que Claude Code encuentra por sí mismo. Una regla sin frontmatter se carga al arrancar como un trozo más de `CLAUDE.md`. Una regla con el campo `paths:` (una lista YAML de globs) se carga solo cuando Claude lee o modifica un archivo que coincide.

El Photogallery es el caso de manual. El estilo PHP de su `CLAUDE.md` vale solo para `backend/`, así que yo lo movería a `.claude/rules/php.md`:

```markdown
---
paths:
  - "backend/**/*.php"
---

# PHP code style

- Run `vendor/bin/pint --dirty --format agent` before finalizing changes.
- `declare(strict_types=1);` on every file in `app/Services/`, `app/Actions/`,
  `app/Jobs/`, `app/Queries/`.
- Final by default: new classes are `final class Foo` unless explicitly
  designed for inheritance.
- Mass assignment: `$model->fill($request->validated())`, never `$request->all()`.
- Always use curly braces for control structures, even for single-line bodies.
```

Las líneas vienen, apenas recortadas, de la sección Code style del archivo. Lo mismo vale para las reglas de TypeScript y de Tailwind, que irían en `.claude/rules/frontend.md` con `paths: ["frontend/src/**/*.ts", "frontend/src/**/*.tsx"]`. En `CLAUDE.md` se quedan las reglas que valen en todas partes (una tarea, un commit; el envelope `{ "data": ... }`; UUID v7) y el archivo baja hacia las doscientas líneas. En el repositorio companion esta división todavía no existe: es el refactoring que haría hoy.

Para el proyecto de análisis de datos de los capítulos 4-6 basta con una sola regla:

```markdown
---
paths:
  - "**/*.py"
---

# Reglas de Python

- Type hints en todas las funciones públicas
- Docstrings en español, formato Google
- Nada de print: usa el módulo logging
```

Claude Code busca las reglas al arrancar, así que después de escribir una sal y vuelve a lanzar `claude`. Pídele a Claude que lea un archivo Python y luego escribe `/memory`: la regla aparece entre los archivos de instrucciones cargados. En `/context` la encuentras en la sección Memory files, con su peso en tokens. Las reglas personales, válidas en todos los proyectos, van en `~/.claude/rules/`.

### Cuándo actualizarlo

El momento justo es nada más hacer el cambio, mientras lo tienes fresco: una actualización major (de Laravel 12 a 13), un cambio de gestor de paquetes, un patrón nuevo, una librería que Claude tiene que usar de una manera concreta, una carpeta renombrada, algo que habéis decidido dejar de hacer.

En los equipos funciona una casilla en la plantilla de los pull requests:

```markdown
## Checklist del PR

- [ ] Tests en verde (`pnpm test`)
- [ ] Lint limpio (`pnpm lint && pnpm type-check`)
- [ ] CLAUDE.md actualizado si han cambiado el stack o las convenciones
- [ ] Documentación actualizada si ha cambiado una API pública
```

La casilla no garantiza nada, pero la ven tanto quien abre el PR como quien hace la revisión.

Las señales de que el archivo se ha quedado atrás son fáciles de reconocer. Claude sigue creando los componentes con la estructura que tenías antes del refactoring, porque `CLAUDE.md` todavía describe esa. Propone `npm run dev` seis meses después de que pasaras a `pnpm dev`. Respeta una prohibición ("no uses `fetch` directamente") que ya no tiene sentido, porque el api-client ya no existe.

Si quieres llevar un registro de los cambios, añade al final una sección con los últimos tres a cinco, con fecha. Es para ti y para el equipo, no para Claude, así que puedes meterla dentro de un comentario HTML y no cuesta contexto:

```markdown
<!--
## Changelog
- 2026-09-10: paso de React Query a TanStack Query 5 (misma API)
- 2026-07-02: introducido el patrón Result<T, E>, eliminar los try/catch sueltos
- 2026-05-15: generado con /init + convenciones del equipo
-->
```

De vez en cuando, pídele al propio Claude que haga la revisión. Sabe decirte qué instrucciones usa y cuáles son solo ruido.

::: {.callout .callout-prompt}
[Prompt reutilizable]{.callout-title}

```text
Lee el archivo CLAUDE.md de este proyecto y dime:
1. ¿Hay información duplicada respecto a lo que ya puedes deducir del código?
2. ¿Hay secciones demasiado largas que se podrían condensar?
3. ¿Falta información importante que ya te ha causado errores
   o que te habría ayudado en esta sesión?
4. ¿Tiene el archivo secciones obsoletas respecto al stack actual del proyecto?
5. ¿Hay instrucciones que valen solo para una parte del código y que
   estarían mejor en .claude/rules/ con el campo paths?

Propón una versión revisada de 200 líneas como máximo.
```

Lánzalo cada dos o tres meses, o después de un refactoring importante.
:::

La revisión más sistemática la hace `/doctor prompt-audit`, que lee `CLAUDE.md`, reglas, skills y agentes y señala instrucciones escritas para modelos antiguos, referencias a archivos que ya no existen e instrucciones que se contradicen. La encontrarás en el capítulo 15.

### La memoria que escribe Claude

Además de `CLAUDE.md`, que escribes tú, está la memoria automática (auto memory), que escribe Claude y que viene activada por defecto. En ella acaban tus preferencias, las correcciones que le das mientras trabajáis y el contexto que no puede deducir del código. Vive en tu home, en `~/.claude/projects/<proyecto>/memory/`, compartida entre los worktrees del mismo repositorio: un archivo `MEMORY.md` hace de índice y en cada sesión se cargan sus primeras 200 líneas (o 25 KB). Son archivos Markdown que puedes leer y corregir, y `/memory` la activa o la desactiva. La regla para elegir es sencilla: lo que necesita todo el equipo va en `CLAUDE.md`, tus preferencias personales pueden ir en la memoria. El capítulo 15 la trata a fondo.

## 7.6 Tres ejemplos reales

Tres archivos para proyectos de tipos distintos, cada uno con las situaciones en las que te ahorra una corrección.

### A. Frontend con React y Tailwind CSS

```markdown
# CLAUDE.md: Dashboard Frontend

## Stack
- React 19 + TypeScript 5
- Vite 6 (NO Create React App, NO Next.js)
- Tailwind CSS 4 + shadcn/ui
- Estado global: Zustand 5
- Fetching: TanStack Query 5
- Formularios: React Hook Form 7 + Zod
- Test: Vitest + Testing Library
- Gestor de paquetes: pnpm

## Comandos
- Dev: `pnpm dev` (puerto 5173)
- Build: `pnpm build`, vista previa con `pnpm preview`
- Test: `pnpm test`
- Lint: `pnpm lint`

## Convenciones
- Un componente por archivo, nombre en PascalCase, archivo en kebab-case (`gallery-card.tsx`)
- Hooks personalizados con el prefijo `use`, p. ej. `useGalleryList`
- Clases de Tailwind inline en el JSX, nada de CSS aparte
- Nada de `useEffect` para el fetching: usa TanStack Query
- En los stores de Zustand solo estado, nada de lógica de negocio

## NUNCA hagas
- No modifiques `src/components/ui/`: son los componentes de shadcn
- No uses `useState` para el estado de los formularios: React Hook Form
- No importes con rutas relativas: usa el alias `@/`
- No dejes `console.log` en el código con commit
```

Cuándo te salva: Claude no propone `useEffect` más `fetch` para las llamadas a la API, el patrón antiguo que más ha visto, no toca los componentes de shadcn y pasa siempre por TanStack Query. En un frontend que cambia deprisa, solo estas tres reglas ya justifican el archivo.

### B. Backend con NestJS y Prisma

```markdown
# CLAUDE.md: API Backend

## Stack
- NestJS 11 + TypeScript 5 (strict)
- Prisma 6 (PostgreSQL)
- Auth: Passport + JWT (access 15 min, refresh 7 días)
- Test: Jest + Supertest
- Gestor de paquetes: pnpm

## Comandos
- Dev: `pnpm start:dev` (hot reload, puerto 4000)
- Test: `pnpm test` (unitarios), `pnpm test:e2e` (E2E)
- Migraciones en desarrollo: `pnpm db:migrate`
- Migraciones en producción: `pnpm db:deploy` (nunca `migrate dev` en producción)
- Seed: `pnpm db:seed` (sobrescribe todo)

## Arquitectura
- Un módulo NestJS por dominio (users, orders, invoices)
- Repository pattern: cada módulo tiene su `.repository.ts`, modelo en `src/users/users.repository.ts`
- Un DTO por operación (`CreateUserDto`, `UpdateUserDto`)
- `JwtAuthGuard` en cada endpoint protegido

## Convenciones
- Nada de `any`: usa `unknown` y un type guard
- Errores siempre con `HttpException` o sus subclases
- Logs con `Logger` de `@nestjs/common`, nunca `console.log`

## NUNCA hagas
- No modifiques `src/prisma/generated/`: son archivos generados
- No expongas endpoints sin `@UseGuards(JwtAuthGuard)` (salvo `/auth/*`)
- No devuelvas entidades de Prisma desde el controller: siempre un DTO
```

Cuándo te salva: Claude no se olvida del guard JWT en un endpoint nuevo, no devuelve en la response los campos sensibles de una entidad y sigue el repository pattern del modelo. Son errores que cuesta caro encontrar después.

### C. Scripts de Python para análisis de datos

Este es el tipo de archivo que necesitas para el proyecto de los capítulos 4-6.

```markdown
# CLAUDE.md: análisis de métricas SaaS

## Stack
- Python 3.11+
- pandas 2, matplotlib
- Export: openpyxl para Excel, ReportLab para PDF
- Entorno: pip + venv (NO conda), `venv/` en la raíz, ya creado

## Comandos
- Activar el entorno: `source venv/bin/activate`
- Dependencias: `pip install -r requirements.txt`
- Dashboard: `python dashboard.py`
- Excel: `python tools/genera_excel.py`
- Informe PDF: `python tools/genera_report.py`
- Test: `pytest tests/`

## Datos
- Fuente: `saas_metrics.csv` (solo lectura)
- Gráficos en `docs/charts/`, Excel y PDF en `output/` (crea las carpetas si no existen)
- Moneda: euros, nunca dólares
- Fechas en formato dd/mm/aaaa

## Convenciones
- Type hints en los parámetros y en el valor de retorno, docstrings en formato Google
- Paleta de los planes fija: Free, Silver, Gold siempre con los mismos colores
- Gráficos a 150 dpi

## NUNCA hagas
- No uses `print()` para depurar: usa `logging`
- No escribas rutas absolutas: usa `pathlib.Path(__file__).parent`
- No hagas commit de CSV ni de Excel: solo código y `requirements.txt`
- No modifiques el CSV fuente
```

Cuándo te salva: Claude guarda gráficos e informes en las carpetas correctas sin que tengas que repetirlo, usa euros y el formato de fecha dd/mm/aaaa, y no reescribe el CSV para "limpiarlo". En los scripts que se ejecutan solos, como el informe Excel lanzado desde cron en el capítulo 5, la salida se mantiene coherente aunque el prompt sea de una línea.

## Resumen {.unlisted}

- `CLAUDE.md` es texto que Claude Code carga en el contexto en cada sesión. Los niveles son cuatro (organización, usuario, proyecto, local) y se suman; los archivos de las subcarpetas entran cuando Claude trabaja en ellas.
- Escribe instrucciones verificables sobre el stack, los comandos, las convenciones no obvias, las prohibiciones, los patrones y el vocabulario. Deja fuera la documentación, los secretos y las roadmaps.
- Quédate por debajo de las doscientas líneas. Los imports con `@` organizan pero no ahorran contexto; las reglas de `.claude/rules/` con `paths:` se cargan solo para los archivos que coinciden.
- Genera el primer borrador con `/init` y luego añade lo que el código no dice. Para modificarlo usa `/memory` o pídeselo a Claude: el atajo `#` ya no existe.
- Si solo hay un `AGENTS.md`, Claude Code lee ese; si están los dos, importa `@AGENTS.md` desde `CLAUDE.md`.
- `CLAUDE.md` guía pero no obliga: para las restricciones usa los permisos (capítulo 11) y los hooks (capítulo 12).

## Ejercicio {.unlisted}

Elige un proyecto en el que trabajes, aunque sea pequeño. Si no tienes ninguno, usa el del ejercicio del capítulo 1 o el proyecto de análisis de los capítulos 4-6.

1. Lanza `/init` en la raíz y lee el borrador. Quita lo que Claude deduce solo a partir del código.
2. Añade los comandos del proyecto, una sección "NUNCA hagas" con tres a cinco entradas y el vocabulario del dominio, si el proyecto tiene uno.
3. Mueve a `.claude/rules/` al menos una regla que valga solo para un tipo de archivo, con el campo `paths:`.
4. Sal, vuelve a lanzar `claude` y pide algo que debería activar tus convenciones, por ejemplo "añade un módulo para la gestión de pedidos" o "añade al informe un gráfico del churn por plan".

El ejercicio está terminado cuando `CLAUDE.md` tiene menos de doscientas líneas (compruébalo con `wc -l CLAUDE.md`), `/memory` muestra la regla cargada después de que Claude haya leído un archivo que coincide, y el código producido en el paso 4 respeta los comandos, las carpetas y los patrones que has escrito sin que los repitas en el prompt. El prompt de revisión del apartado 7.5 también está en el repositorio `claude-code-book-snippets`, carpeta `cap-06/`.
