# Capítulo 18. Spec Driven Development

::: {.chapter-goals}
[Qué aprenderás]{.callout-title}

- dividir las especificaciones en `docs/REQUIREMENTS.md`, `docs/DESIGN.md` y `docs/TASKS.md`, y saber quién lee cada uno
- escribir un build workflow con un prompt, un comando de verificación y un commit para cada fase
- llevar SOLID, KISS y DRY al `CLAUDE.md` con ejemplos sacados del código del proyecto
- hacer que un agente escéptico critique las specs antes de escribir la primera línea de código

[Requisitos previos]{.callout-title}

El capítulo 17, del que salen el `SPEC.md` y los documentos de refinamiento del Photogallery. Los ejemplos son de Laravel, pero el método sirve con cualquier framework de backend.

:::

Programar con un agente se vuelve un problema en un momento concreto, y suele llegar tarde: cuando el código funciona pero ya no sabes explicar por qué está escrito así. Un módulo usa UUID y el de al lado enteros autoincrementales. En un controlador la lógica de negocio está en el controlador, en otro está en un service. Cada decisión, por separado, se puede defender. Juntas, no.

Eso es el vibecoding: el agente escribe código prompt tras prompt, sin una estructura que conecte las decisiones. Claude escribe buen código, pero cuando no hay un plan rellena los huecos con decisiones razonables que nadie compara con las del día anterior. Y la deuda técnica no se ve, porque el código llega ya verosímil y ya compilado. Te das cuenta cuando un cambio que debía tocar tres archivos toca treinta.

El Spec Driven Development (SDD) parte de una regla sencilla: cada línea de código que escribe Claude tiene que remontarse a un requisito, a una tarea y a una decisión de diseño escrita. Nada de commits hasta que la tarea esté verificada. Dicho así parece burocracia. En la práctica Claude deja de adivinar qué tenías en mente y empieza a ejecutar un plan, y tú pasas menos tiempo corrigiendo.

También hay un motivo de contexto. El `SPEC.md` del Photogallery, al final del capítulo 17, llegó a 2386 líneas. Cabe en una ventana de contexto de un millón de tokens, pero cargarlo en cada tarea significa ahogar las veinte líneas que hacen falta entre dos mil que sobran. Con archivos separados, Claude lee las reglas (`CLAUDE.md`, que se carga solo), la tarea que tiene que ejecutar y la sección de diseño que esa tarea cita.

La Parte VI construye el Photogallery con este método. Aquí se preparan los archivos; a partir del capítulo 19 se ejecuta.

## 18.1 Los tres archivos

Varias herramientas para el desarrollo con agentes han llegado a la misma conclusión: para un proyecto mediano, un único archivo de especificación no basta. Kiro llama a sus archivos `requirements.md`, `design.md` y `tasks.md`; Spec Kit de GitHub trabaja con una spec, un plan y una lista de tareas. Los nombres cambian, la división es la misma: qué construir, cómo construirlo y en qué orden. En el Photogallery los tres archivos están en `docs/`, con el nombre en mayúsculas, y junto a ellos está el `CLAUDE.md` de la raíz del repositorio, que los mantiene unidos.

| Archivo | Quién lo lee | Cuánto cambia | Cuándo se lee |
| :---- | :---- | :---- | :---- |
| `CLAUDE.md` | Cada sesión | Poco | Siempre, de forma automática |
| `docs/REQUIREMENTS.md` | Tú, un stakeholder, quien planifica | Casi nada | Al planificar y cuando una tarea cita un criterio |
| `docs/DESIGN.md` | Los agentes que implementan | Bastante | Cuando una tarea cita una sección |
| `docs/TASKS.md` | Los agentes que ejecutan | Continuamente | En cada tarea, actualizado cada vez que se cierra una |

Cuando Claude trabaja en T031, `PhotoController@index` y `@show`, lee la tarea, que remite a `DESIGN.md §6.2`, y abre solo esa sección. Quien decide si una funcionalidad entra en la v1 lee los requisitos sin perderse entre los esquemas de las tablas. Y como los requisitos cambian poco mientras las tareas cambian cada hora, tenerlos separados te ahorra reescribir un documento enorme cada vez que marcas una casilla.

### `docs/REQUIREMENTS.md`, qué construir

El archivo de requisitos describe el producto en un lenguaje que entiende también quien no escribe código. Nada de tecnologías, nada de nombres de clases ni de endpoints: visión, personas, historias de usuario, criterios de aceptación, restricciones, requisitos no funcionales y lo que queda fuera. La cabecera del archivo lo dice claramente: "No code, no schemas, no technical decisions".

En el Photogallery hay tres personas (visitante anónimo, miembro registrado, administrador). Las historias de usuario van numeradas de `US-01` a `US-40`, las funcionalidades de `F1` a `F12`, y cada criterio de aceptación tiene un ID como `AC-F4-1`. Estos ID sostienen el método: las tareas los citan, los tests los verifican y los mensajes de commit los mencionan. Los archivos del repositorio están en inglés y los cito tal cual. La parte de la subida, recortada:

```markdown
### Upload & ownership (Member)
- **US-13.** As a member, I want to drag and drop photos onto a target zone to upload them.
[...]
- **US-17.** As a member, I want the upload to fail loudly (with a clear message) if a file is over 10 MB or in an unsupported format — before any bytes leave my browser.

[...]

### F4 — Upload
- AC-F4-1: Dragging a 15 MB JPEG into the dropzone displays inline error "File exceeds 10 MB" and does not initiate the upload.
- AC-F4-3: Submitting 21 files shows "Up to 20 files at once" and refuses to send.
- AC-F4-4: A successful upload of 5 files within 10 seconds returns a batch identifier and a list of 5 photo ids; each photo appears in the gallery with a "processing" overlay.
```

Cada criterio tiene una entrada precisa y un resultado observable. "La subida debe gestionar bien los archivos grandes" no se puede probar; "un JPEG de 15 MB muestra `File exceeds 10 MB` y la subida no arranca" se convierte en un test de Vitest tal como está.

La sección "Out of scope" cuenta tanto como los requisitos. La del Photogallery enumera quince exclusiones para la v1, desde los comentarios hasta la autenticación en dos pasos, desde el borrado lógico hasta las etiquetas jerárquicas. Cada entrada es una discusión que no repites a mitad de proyecto, y una funcionalidad que Claude no añade porque le parecía útil.

### `docs/DESIGN.md`, cómo construirlo

El diseño explica cómo implementar los requisitos: stack con versiones, carpetas, esquema de la base de datos, contratos de la API, interfaces de los servicios, autenticación, errores y pipeline de imágenes. Es el archivo que abren los agentes cuando implementan, "authoritative for code" según su cabecera. En la rama de este capítulo son 1297 líneas en doce secciones.

Una sección típica es el contrato de `POST /photos`, aquí con algunos campos menos:

```markdown
#### `POST /photos` — single endpoint for 1–20 files
- **Auth:** token (`photos:write`)
- **Content-Type:** `multipart/form-data` (JSON body → 415)
- **Form fields:**

  | Field | Type | Required | Rules |
  |---|---|---|---|
  | `files[]` | File[] | yes | 1–20 items; each `image\|mimes:jpg,jpeg,png,webp\|max:10240` |
  | `album_id` | UUID | no | must exist + be owned by auth user |
  | `new_tags[]` | string[] (names) | no | up to 20; created if missing |

- **Behavior** (wrapped in `DB::transaction`):
  1. Upsert any `new_tags[]` names → tag rows (slug auto-generated, collision-resolved).
  2. Strip GPS EXIF from each file via `ExifExtractor::stripGps`.
  3. `PhotoStorage::storeOriginal(...)` writes to `photos_private` disk.
  4. Insert `Photo` row per file with `user_id = auth()->id()`, `processing_status = 'pending'`.
  5. Attach merged tag set.
  6. Wrap one `ProcessPhoto` per photo in `Bus::batch(...)`.
- **202 Accepted** with `Location: /api/v1/photos/batch/{batch_id}` header
- **Errors:** 403 (album not owned), 413, 415, 422
```

Un agente que lee esta sección no tiene nada que decidir: sabe que el body es multipart, que la respuesta es 202 porque el procesamiento es asíncrono, en qué orden se hacen las escrituras y qué errores hay que cubrir con un test. Las decisiones que Claude tomaría por su cuenta, quizá una distinta en cada sesión, ya están escritas.

### `docs/TASKS.md`, la lista de trabajo

El archivo de tareas es el operativo, y el que más cambia. Cada tarea es atómica (30 minutos de trabajo como máximo, dice la cabecera) y declara estado, owner, dependencias, tareas paralelas, secciones que leer, criterios de aceptación y mensaje de commit. Dos tareas de la Fase 2, tal como están en la rama del capítulo:

```markdown
### T031 — `PhotoController@index` and `@show`
- **Status:** [ ]
- **Owner:** backend-dev
- **Depends on:** T020, T024, T026, T027
- **Parallel with:** T030, T034, T035, T036
- **Reads:** DESIGN.md §6.2
- **Acceptance:**
  - Index uses `PhotoQuery`; cursor pagination; eager loads; ≤2 SQL queries (n+1 detector enforced).
  - Show: 200 / 304 / 404 covered.
- **Commit:** `feat(api): GET /photos and /photos/{id}`

### T039 — Routes + middleware groups + rate limiters
- **Status:** [ ]
- **Owner:** backend-dev
- **Depends on:** T030–T038
- **Parallel with:** —
- **Magnet:** `routes/api.php`, `bootstrap/app.php`
- **Reads:** DESIGN.md §6.0 (rate limits), §6.1–§6.5
- **Acceptance:**
  - `routes/api.php` declares every endpoint under `/v1` prefix.
  - Auth routes throttled `10,1` per IP; everything else `120,1` per IP and `300,1` per user.
  - Mutating routes wrapped in `auth:sanctum`.
- **Commit:** `feat(api): route definitions with rate limits`
```

Las líneas `Depends on` y `Parallel with` son la razón de ser de este archivo. T030, T031, T034, T035 y T036 son controladores que tocan archivos distintos, así que pueden ir en paralelo. T039 toca `routes/api.php` y `bootstrap/app.php`, dos de los archivos que el proyecto llama magnet porque atraen los conflictos de merge: arranca solo cuando los controladores están terminados, y lo ejecuta un único agente. Cuando le pides a Claude que ejecute la Fase 2, la regla 3 del `CLAUDE.md` le indica que use subagentes para las tareas paralelas (capítulo 10). La orquestación la deciden las specs, no tu memoria. En el capítulo 20 la misma idea se amplía a grupos de fases, cada uno en su worktree.

En la rama del capítulo, `TASKS.md` contiene 112 tareas en 13 fases. En `main` el resumen al final del archivo cuenta 124 en 14 fases, porque durante la ejecución se añadió la Fase 14, dedicada a terminar el frontend.

![Dependencias y tareas paralelas declaradas en TASKS.md, en la diapositiva del curso dedicada al archivo](figures/cap-18/fig-01.png)

::: {.callout .callout-tip}
[Consejo]{.callout-title}

Para las specs no hacen falta Notion ni Jira. Cuatro archivos Markdown en el repositorio, versionados con Git, le bastan a un proyecto guiado por agentes: cada cambio en las specs queda en el historial y se revisa en un PR, junto al código que cambió.
:::

## 18.2 Generar los tres archivos con Claude

Tres archivos en lugar de uno parecen más trabajo, pero no los escribes tú: los genera Claude a partir del material del capítulo 17, es decir, `SPEC.md` y los dos documentos de refinamiento `docs/database-refinement.md` y `docs/api-refinement.md` (rama `book/cap-11-prompts-and-spec` del repositorio companion). El prompt que se usó para el Photogallery es la última sección de `docs/PROMPT.md`, en inglés, y pide cuatro archivos: los tres del SDD más el `CLAUDE.md`. La versión en español, para adaptar a tu proyecto:

```text
Lee SPEC.md, docs/database-refinement.md y docs/api-refinement.md.

Genera tres archivos en la carpeta docs/:

1. docs/REQUIREMENTS.md, qué construir
   - Visión y lo que el producto NO es
   - Personas (visitante, miembro, administrador)
   - Historias de usuario por persona, con ID (US-01, US-02, ...)
   - Criterios de aceptación comprobables, con ID (AC-F1-1, ...)
   - Restricciones (formatos de archivo, tamaños, nomenclatura)
   - Requisitos no funcionales con números (rendimiento, seguridad, escalabilidad)
   - Out of scope explícito
   Nada de decisiones técnicas, nada de esquemas, nada de código.

2. docs/DESIGN.md, cómo construirlo
   - Stack con versiones exactas
   - Estructura de carpetas de backend/ y frontend/
   - Esquema de la base de datos: tablas, columnas, tipos, restricciones, índices, ON DELETE
   - Contratos de la API: verbo, URL, body, forma de la respuesta, códigos de estado
   - Interfaces de los servicios (ImageProcessor, PhotoStorage) para la DIP
   - Autenticación, gestión de errores, pipeline de imágenes

3. docs/TASKS.md, la lista de trabajo
   - Tareas atómicas, de 30 minutos como máximo cada una, agrupadas en fases
   - Para cada tarea: ID (T001, ...), estado [ ], owner (backend-dev,
     frontend-dev, code-reviewer), Depends on, Parallel with, Reads
     (secciones que leer), Acceptance (definition of done), Commit
   - Referencias a las secciones de DESIGN.md y a los ID de REQUIREMENTS.md

Usa los ID para la trazabilidad en las dos direcciones: cada criterio de
aceptación tiene que aparecer en al menos una tarea.
```

Antes de lanzarlo, sube el effort con `/effort high`: escribir especificaciones es el tipo de trabajo en el que el nivel alto compensa (capítulo 2).

La primera pasada sale en pocos minutos y hay que revisarla. Casi siempre hacen falta tres correcciones.

La primera tiene que ver con la granularidad. El `TASKS.md` de la primera pasada tiende a ser demasiado fino, una tarea por método, o demasiado vago, una tarea para todo el frontend. La medida correcta es un archivo o un grupo de archivos muy relacionados: lo bastante pequeño para caber en un commit y lo bastante grande para tener un criterio de aceptación verificable. Las tareas de cinco minutos se fusionan; una tarea de horas sin un punto de control se divide.

La segunda tiene que ver con las dependencias. El modelo es optimista y a menudo declara en paralelo una tarea de tests y la tarea que esos tests verifican. Revisa cada `Parallel with`: dos tareas no van en paralelo si una depende de la otra, aunque los archivos parezcan separados.

La tercera tiene que ver con los requisitos no funcionales, que con facilidad se quedan en `REQUIREMENTS.md` sin una tarea que los implemente o los mida. "Gallery time-to-first-tile ≤ 1.5 seconds on a 5 Mbps connection" es un requisito real del Photogallery, y sin una tarea con un criterio medible nadie lo comprobará nunca. En la sección 18.6 vemos qué fue de él.

Al final, los tres archivos de la rama `book/cap-12-sdd-three-files` miden 348, 1297 y 1427 líneas. Son largos, y está bien así: nadie los lee enteros, cada tarea abre un trozo.

## 18.3 El build workflow

Los tres archivos dicen qué construir y cómo. El build workflow dice en qué orden, con qué comando de verificación y con qué mensaje de commit para cada fase. Sin él, Claude puede empezar por el frontend antes que por las migraciones, o escribir componentes de React que llaman a endpoints que todavía no existen.

En el Photogallery el workflow es la sección 13 de `SPEC.md`, "Claude Code Build Workflow". Nació de un prompt de pocas líneas que encontrarás en `docs/claude-code-build-workflow.md`. En español:

```text
Añade a la spec una sección "Claude Code Build Workflow".
Enumera el orden exacto de construcción, fase por fase:

Fase 1: Backend foundation (modelos, migraciones, seed)
Fase 2: API layer (controladores, rutas, resources, form requests)
Fase 3: Panel de administración de Filament (resources, widgets, dashboard)
[...]
Fase 9: Hooks (formateo automático, tests automáticos, seguridad)
[...]
Fase 13: Spec check final y deploy

Para cada fase escribe el prompt exacto que hay que darle a Claude Code.
```

### Cómo es una fase

El resultado es un runbook: cada fase tiene un objetivo, un prompt para pegar, un comando de verificación y un mensaje de commit. Al principio de la sección hay un preámbulo que se antepone a cada prompt a partir de la Fase 2:

```text
You are working inside this repo. The spec is `SPEC.md` at the repo root — it is authoritative. Read the sections referenced in the prompt and follow them literally. Do NOT invent fields, endpoints, or file paths that aren't in the spec. Run verification before claiming completion. Commit at the end with the message specified in the prompt.
```

La Fase 1, recortada:

```markdown
### Phase 1 — Backend foundation (models, migrations, seed)
**Goal:** Laravel 13 project scaffolded, UUID primary keys wired, all five application tables migrated, models with relationships, seeded admin user.

**Prompt:**
Bootstrap the Laravel backend per SPEC.md §3.2 and §4.

1. From repo root, scaffold the Laravel app in backend/:
     composer create-project laravel/laravel backend "^13.0"
[...]
6. Write migrations in this exact order (filenames per SPEC.md §3.2):
   - create_albums_table               — without cover_photo_id FK
   - create_tags_table
   - create_photos_table               — with album_id FK (ON DELETE SET NULL, ON UPDATE CASCADE)
   - add_cover_photo_fk_to_albums      — adds cover_photo_id FK (ON DELETE SET NULL)
   - create_photo_tag_table            — composite PK, both FKs CASCADE
   All column types, nullability, defaults, and indexes MUST match SPEC.md §4 exactly.
[...]
Commit: `feat(backend): database schema, models, and seeders`

**Verify:**
cd backend && php artisan migrate:fresh --seed && php artisan tinker --execute="echo App\Models\Photo::factory()->create()->id;"
```

El detalle que importa es la verificación: la fase está cerrada cuando `php artisan migrate:fresh --seed` termina sin errores y la factory devuelve una fila con un UUID. El resumen que hace Claude al terminar no vale como prueba, y el preámbulo se lo recuerda.

### Las reglas de trabajo

El workflow también necesita reglas que valgan para todas las fases. En el Photogallery están en la sección 15 de `SPEC.md`, "Test-and-Commit Discipline":

- una tarea, un commit, en formato Conventional Commits con un scope entre `backend`, `frontend`, `db`, `filament`, `api`, `pipeline`, `ci` y `spec`
- un gate de tests para cada tipo de tarea: una migración tiene que pasar `migrate:fresh` y el rollback, un endpoint tiene un test por cada código de estado documentado
- nunca `--no-verify`, nunca `.skip`: si se rompe un test antiguo, `git bisect`, y luego fix hacia delante o revert del commit culpable
- una rama por tarea (`feat/2-api-photos-store`), un PR por tarea, squash merge

A estas les añado tres señales de stop: una tarea que tarda el doble de lo previsto, un comando de verificación que falla dos veces seguidas y Claude proponiendo cambiar la spec para que el código pase. El código se adapta a la spec. Lo contrario solo se hace con una decisión explícita y un commit `spec:` dedicado.

Otra regla útil es un archivo de cobertura que tiene que quedarse vacío: cada requisito sin tarea va ahí, y mientras el archivo tenga una línea la fase está bloqueada. En el Photogallery el control de cobertura llegó al final, como auditoría: `docs/SPEC-COVERAGE.md` mapea cada subsección de `DESIGN.md` con código y tests, y el 30 de abril contaba 42 secciones, de las que 27 estaban implementadas, 11 a medias y 4 sin hacer. Hecho antes de la ejecución, cuesta mucho menos.

### El ciclo de trabajo

Una vez aprobado el workflow, la ejecución se convierte en un ciclo:

1. Copia el prompt de la fase actual desde el workflow.
2. Pégalo en Claude Code, con el preámbulo delante.
3. Claude trabaja y paraleliza donde las tareas lo permiten.
4. Lanza el comando de verificación de la fase.
5. Si pasa, haz commit con el mensaje previsto y ya puedes pasar a la fase siguiente.
6. Antes de la fase siguiente, si la sesión va cargada, un `/clear` (capítulo 15).

Los prompts se versionan junto con el código: si mañana regeneras el proyecto, o un compañero repite el recorrido, basta con seguir la misma lista.

## 18.4 El CLAUDE.md del Photogallery

El `CLAUDE.md` (capítulo 7) es el archivo que Claude Code carga al principio de cada sesión. El del Photogallery se define como "project constitution" en la primera línea. No dice qué construir, porque para el contenido remite a `REQUIREMENTS.md` y `DESIGN.md`: dice cómo se trabaja.

Este archivo tampoco se escribe a mano. El prompt del Photogallery lo generaba junto con los otros tres; si lo haces aparte, parte de aquí:

```text
Lee docs/REQUIREMENTS.md, docs/DESIGN.md y docs/TASKS.md.
Genera un CLAUDE.md para el proyecto Photogallery que contenga:
- Mapa de la documentación: qué archivo leer y cuándo
- Project overview (3-4 líneas)
- Stack tecnológico con versiones exactas y comandos de instalación
- Reglas no negociables, divididas entre workflow y arquitectura
- Principios de calidad (SOLID, REST, KISS, DRY) con ejemplos sacados de
  este proyecto, no definiciones genéricas
- Reglas de paralelización y archivos que no se deben modificar en paralelo
- Convenciones de código y reglas de git (ramas, formato de los commits)
- La meta-regla: lee siempre docs/REQUIREMENTS.md y docs/DESIGN.md
  antes de implementar una tarea, y actualiza las casillas de
  docs/TASKS.md en cuanto la tarea esté cerrada
```

En la rama del capítulo el archivo resultante tiene 276 líneas. Lo reproduzco recortado; las partes quitadas están marcadas con `[...]`:

```markdown
# CLAUDE.md — PhotoGallery Pro

> The project constitution. Loaded into every Claude Code session. **Authoritative for HOW we work**; defers to `docs/REQUIREMENTS.md` (what to build) and `docs/DESIGN.md` (technical blueprint) for content. Atomic work lives in `docs/TASKS.md`.

## Documentation map

| File | Purpose | When to read |
|---|---|---|
| `CLAUDE.md` (this file) | How we work — rules, principles, style | Every session, automatic |
| `docs/REQUIREMENTS.md` | What we're building, in plain language | Before starting any task — read the relevant feature |
| `docs/DESIGN.md` | Technical blueprint — schemas, contracts, file paths | Before implementing — read the section the task references |
| `docs/TASKS.md` | 80+ atomic tasks across 13 phases | Pick a task; check it off when done |
| `docs/SPEC-REVIEW.md` | Decision log explaining why architectural choices were made | When you disagree with a rule and want context |

## Project overview

PhotoGallery Pro is a full-stack photo gallery: [...] The backend is a Laravel 13 REST API under `/api/v1` with a Filament v5 admin panel mounted at `/admin`. Image resizing and EXIF extraction run as queued background jobs so uploads return immediately. [...]

## Tech stack (with install commands)

[...] tablas de versiones y comandos composer/npm para backend/ y frontend/

## Critical rules

These are **non-negotiable**. Violations require an explicit user override.

### Workflow rules

1. **Always read `docs/REQUIREMENTS.md` and `docs/DESIGN.md` before implementing tasks.** [...] If the task is ambiguous and the docs don't resolve it, stop and ask — do not guess.
2. **Always update `docs/TASKS.md` checkboxes after completing work.** [...] Don't batch — checking off six tasks at once means you've drifted.
3. **Use subagents for tasks marked `parallel: true` in `TASKS.md`.** [...]
4. **One task = one commit.** Conventional Commits format: `<type>(<scope>): <subject>`. Reference SPEC sections in the body. See DESIGN.md §15.3.
5. **Tests run before commits.** Test gates per task type live in DESIGN.md §15.2. No `--no-verify`, no `.skip`, no "tests later".

### Architecture rules (cite DESIGN.md sections in PRs)

[...]
8. **Every primary key is UUID v7** via the `HasUuidV7` trait. Stored as `CHAR(36)`. Never auto-increment for application tables.
9. **Two photo disks. All file I/O goes through them.**
   - `Storage::disk('photos')` — public-read; sized variants only
   - `Storage::disk('photos_private')` — private; originals only; signed URLs only

   Never use `File::`, `fopen`, `copy`, or `move_uploaded_file`. (DESIGN.md §11)
10. **Authorization, not just authentication.** Every mutating controller calls `$this->authorize($action, $model)` AND `$request->user()->tokenCan('photos:write'|'albums:write')`. (DESIGN.md §6.4a, §9)
11. **Wrap multi-write operations in `DB::transaction(...)`.** Photo upload (insert + tag attach + dispatch), photo update (update + tag sync), album with cover. (DESIGN.md §6.4a)

[...] reglas 12-14: eager loading, configuración de Tailwind v4, textos de la UI en frontend/src/data/

## Engineering principles (project-specific)

Generic principle definitions are useless. Here's how each applies to **this** codebase.

[...] SOLID, REST, KISS y DRY: los vemos en la sección 18.5

[...] secciones Parallelization rules y Code style

## Before writing any class, ask:

[...]
3. **Does an existing service/contract already cover this?** Check `app/Contracts/`, `app/Services/`, `app/Actions/`, `app/Queries/` before creating new files.
[...]

## When stuck

- **Ambiguity in REQUIREMENTS.md:** ask the user; don't invent acceptance criteria.
- **Conflict between REQUIREMENTS.md and DESIGN.md:** REQUIREMENTS wins; DESIGN gets a `spec:` PR to align.
[...]
```

Las reglas que funcionan son las que se pueden comprobar. "Gestiona bien los archivos" no dice nada; la regla 9 dice qué discos existen, qué va en cada uno y qué funciones de PHP están prohibidas. La regla 10 exige dos llamadas concretas en cada controlador que modifica datos, y una review puede comprobar línea por línea si están. "When stuck" cubre los momentos en los que un agente sin instrucciones improvisa. Las referencias a `DESIGN.md §15` de las reglas 4 y 5 apuntan a una sección que no existe; volvemos a ello en la sección 18.6.

Una nota honesta: 276 líneas son demasiadas. En el capítulo 7 vimos que conviene quedarse por debajo de unas 200, porque un archivo largo consume contexto y se sigue peor, y en `main` este ha llegado a 391. Los primeros candidatos para salir son las secciones de estilo. El estilo de PHP, por ejemplo, puede ir a `.claude/rules/php.md` y cargarse solo para los archivos del backend:

```markdown
---
paths:
  - "backend/**/*.php"
---

# PHP code style
- Pint with Laravel preset; PSR-12 baseline.
- `declare(strict_types=1);` in app/Services, app/Actions, app/Jobs, app/Queries.
- Final by default. Mass assignment only via `$request->validated()`.
```

### Donde el CLAUDE.md no llega

El `CLAUDE.md` orienta a Claude, pero no lo obliga. "No `--no-verify`" es una instrucción que Claude sigue casi siempre, y en un proyecto de más de cien tareas ese "casi" acaba apareciendo. Las reglas de permisos del capítulo 11 bloquean un comando diga lo que diga la conversación: un `deny` sobre `Bash(git push --force *)` se aplica también cuando una sesión larga ha perdido de vista las instrucciones. Los hooks del capítulo 12 hacen el resto. La Fase 9 de `TASKS.md` ya prevé algunos: Pint y Prettier después de cada cambio y un bloqueo de los comandos destructivos. Para el SDD el más útil es un hook `Stop` que lanza `php artisan test --compact` y, si los tests fallan, devuelve a Claude al trabajo con el error. La definition of done la hace cumplir el harness.

`/goal`, que usamos en el capítulo 20, lleva la misma idea a los criterios de aceptación: los convierte en una condición de finalización, y Claude sigue trabajando hasta que un evaluador separado la da por cumplida. El evaluador solo ve lo que Claude muestra en la conversación, así que la condición tiene que nombrar una comprobación que Claude ejecute de verdad:

```text
/goal php artisan test --compact termina con exit code 0 y las tareas T019-T045 de docs/TASKS.md están todas marcadas [x]
```

## 18.5 SOLID, KISS y DRY en el workflow

Los principios del clean code ya los conoces. Lo difícil es que un agente los aplique con coherencia cuando cambia de sesión y tiende a añadir capas y abstracciones para un futuro que no llegará. Por eso los principios van en el `CLAUDE.md` y no en el prompt: ahí sobreviven a `/clear` y a las sesiones nuevas, y cada sesión arranca ya alineada.

La sección del Photogallery empieza con una línea que resume el método: "Generic principle definitions are useless. Here's how each applies to this codebase." La definición de SRP Claude ya la conoce; lo que no sabe es qué clase de tu proyecto tiene que tener una sola responsabilidad.

### SOLID aplicado a las especificaciones

SOLID da resultados concretos cuando le pides a Claude que revise las specs con esos principios en la mano: la salida nombra archivos, clases y secciones. La revisión de `SPEC.md`, guardada en `docs/SPEC-REVIEW.md`, encontró entre otras cosas que `ImageProcessor` y `ExifExtractor` eran clases concretas que usaba directamente quien las necesitaba, y que toda la lógica de filtrado de `GET /photos` (búsqueda, etiquetas en AND, álbum, favoritas, ordenación) vivía dentro de `PhotoController@index`.

Las correcciones pasaron al diseño y luego al código. Para la Dependency Inversion hay tres interfaces en `app/Contracts/`, enlazadas con sus implementaciones en `AppServiceProvider`:

```php
$this->app->bind(ImageProcessor::class, InterventionImageProcessor::class);
$this->app->bind(ExifExtractor::class, PhpExifExtractor::class);
$this->app->bind(PhotoStorage::class, DiskPhotoStorage::class);
```

El job que procesa las fotos recibe las abstracciones y no sabe qué implementación hay detrás:

```php
final class ProcessPhoto implements ShouldQueue
{
    use Batchable, Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $tries = 3;

    /** @var int[] */
    public array $backoff = [10, 30, 60];

    public function __construct(public readonly Photo $photo) {}

    public function handle(ImageProcessor $processor, ExifExtractor $exif): void
    {
        // ...
    }
}
```

En los tests se enlaza un `FakeImageProcessor` y el job ni se entera: es la sustitución de Liskov, que el `CLAUDE.md` deja escrita como regla. Las dos interfaces están separadas a propósito, porque redimensionar una imagen y extraer su EXIF son dos motivos distintos para cambiar: Interface Segregation. Para la Single Responsibility, los filtros salieron del controlador y acabaron en `App\Queries\PhotoQuery`, que reutiliza también el panel de Filament. Una nueva ordenación se convierte en un nuevo caso en `applySort()` y el controlador no se toca, que es el Open/Closed contado con un ejemplo.

Luego hay un error que corrigió la revisión y que venía del prompt inicial. En la sección SOLID de `docs/PROMPT.md` pone "PhotoController receives PhotoRepository, not raw queries"; más abajo, en la sección KISS, "Don't create a Repository pattern if you only have one Eloquent model usage". Dos instrucciones contradictorias en el mismo prompt. El `CLAUDE.md` final eligió KISS: nada de repositorios, Eloquent usado directamente y la lógica en Actions, Services y Queries. Cuando el prompt se contradice, Claude elige por su cuenta, y nada garantiza que elija lo mismo en dos sesiones distintas.

### KISS contra la sobreingeniería

KISS es el principio que más cuesta que un modelo respete. Sin un freno explícito, Claude añade factories, builders, clases base abstractas y capas de indirección por si acaso, y el código que sale es correcto pero innecesariamente complicado.

La sección KISS del Photogallery no enumera virtudes, enumera decisiones:

```markdown
### KISS

The smallest implementation that meets the acceptance criteria wins.

- One upload endpoint (`POST /photos` accepts 1–20 files), not two. Frontend doesn't branch.
- One polling loop after upload (`GET /photos/batch/{id}` includes per-photo statuses), not two.
- Cursor pagination, not page+offset+`total` (the gallery doesn't need a count).
- Soft deletes are out of scope for v1. Deletes are permanent. We can add `deleted_at` later if undo becomes a requirement.
```

Casi cada línea viene de una simplificación encontrada en la revisión. La spec inicial tenía dos endpoints de subida, `POST /photos` para una foto y `POST /photos/batch` para dos o más, y dos bucles de polling después de la subida. El parámetro de ordenación mezclaba estilos distintos (`newest`, `title_asc`) y se dividió en `sort` y `order`. Otros casos que Claude propone a menudo y que conviene bloquear de antemano: un DSL para los filtros donde bastan parámetros en la URL, una clase base abstracta para los controladores, un patrón Strategy para una operación que solo tiene una estrategia.

![Las secciones KISS y DRY de PROMPT.md, el prompt del que nacieron las specs, en la vista previa de Markdown del IDE](figures/cap-18/fig-02.png)

Una técnica que ayuda: pide que cada alternativa descartada quede por escrito, con el motivo. El Photogallery mantiene `docs/SPEC-REVIEW.md` como registro de decisiones, y el `CLAUDE.md` lo señala como el archivo que hay que leer "when you disagree with a rule and want context". Una decisión con su motivación al lado es difícil de revertir a mitad de la ejecución.

### DRY y la regla de tres

DRY mal aplicado produce abstracciones prematuras, que hacen más daño que la duplicación que pretendían quitar. El `CLAUDE.md` del Photogallery lo resuelve en dos líneas: "DON'T abstract until the second occurrence. The third occurrence is when extraction becomes required." A la segunda repetición esperas; a la tercera extraes.

El caso concreto: la revisión encontró la misma lógica de upsert de etiquetas por nombre en tres controladores (creación de foto, edición de foto y subida por lotes). Hoy vive en un único servicio, `App\Services\TagAssigner`, que usan la API y el formulario de Filament:

```php
final class TagAssigner
{
    /**
     * @param  list<string>  $names
     */
    public function syncByNames(Photo $photo, array $names): void
    {
        DB::transaction(function () use ($photo, $names): void {
            $tagIds = [];

            foreach (array_filter(array_map('trim', $names)) as $name) {
                $tagIds[] = $this->resolveTag($name)->id;
            }

            $photo->tags()->sync($tagIds);
        });
    }

    // resolveTag() y uniqueSlugFor(): búsqueda por nombre, slug con sufijo -2, -3, ...
}
```

La comprobación antes de escribir está en la checklist "Before writing any class, ask": el punto 3 pide mirar en `app/Contracts/`, `app/Services/`, `app/Actions/` y `app/Queries/` antes de crear un archivo nuevo. Claude hace esa búsqueda en el código, pero solo si una regla se lo pide.

### La self-review antes del commit

Con los principios en el `CLAUDE.md` puedes pedirle a Claude que revise su propio trabajo antes de hacer commit:

```text
Antes de hacer commit de la tarea actual, haz una self-review del código
que has escrito. Comprueba que respeta SRP, KISS y DRY tal como se
describen en el CLAUDE.md. Si encuentras infracciones, corrígelas, vuelve
a ejecutar los tests y luego haz commit.
```

La self-review funciona porque tiene una referencia precisa: la pregunta pasa a ser "¿esta subida está dentro de `DB::transaction` como dice la regla 11?". Para una revisión más seria, hecha por un subagente con un contexto limpio, está `/code-review`, que también lee el `CLAUDE.md`. La usamos en el capítulo 22.

## 18.6 Análisis crítico de las specs

Las specs de la primera pasada nunca están bien. El modelo produce arquitecturas elegantes, pero por sí solo no comprueba que las tareas cubran todos los requisitos ni que los criterios se puedan medir. El paso que más a menudo se salta es el que hay entre la generación y la ejecución: releer los archivos buscando ambigüedades, riesgos y requisitos sin cubrir.

### El spec-critic

El método que mejor funciona es un agente con un rol adversarial, en una sesión limpia o como subagente (capítulo 10):

```text
Lee docs/REQUIREMENTS.md, docs/DESIGN.md y docs/TASKS.md.
Tu rol es el de un senior engineer escéptico que tiene que encontrar
todo lo que podría salir mal antes de que empiece la ejecución.

Genera un informe estructurado con:
1. Vulnerabilidades de seguridad en las specs (no en el código, en las specs)
2. Requisitos sin tarea correspondiente (huecos de cobertura)
3. Tareas sin requisito correspondiente (posible out of scope)
4. Requisitos no funcionales sin implementación prevista
5. Ambigüedades que podrían llevar a interpretaciones distintas entre agentes
6. Estimaciones de esfuerzo optimistas en más de un 50%
7. Dependencias circulares o mal ordenadas en docs/TASKS.md
8. Referencias entre archivos que apuntan a secciones inexistentes

Para cada problema: categoría, descripción, impacto, fix sugerido.
No seas diplomático. Tu objetivo es encontrar problemas, no validar.
```

Para cada problema del informe decides tú si es una crítica fundada o una minucia. Las fundadas vuelven a las specs, y solo después arrancas con la ejecución.

::: {.callout .callout-tip}
[Consejo]{.callout-title}

Una revisión colaborativa, la hagas tú o la haga Claude, encuentra sobre todo lo que esperas. Pedir de forma explícita que busque problemas saca a la luz las suposiciones implícitas y los casos límite que nadie había escrito. Para eso sirve la última línea del prompt.
:::

### Qué cambió en las specs del Photogallery

En el Photogallery la revisión produjo `docs/SPEC-REVIEW.md`: 272 líneas de problemas agrupados por área (SOLID, REST, KISS, backend, frontend, base de datos), aplicados luego a `SPEC.md` en siete bloques. Cuatro cambios tienen que ver con la seguridad.

Los originales estaban en el disco público. En `docs/SPEC-VALIDATION.md`, la comprobación de comprensión que se hizo sobre `SPEC.md` el 25 de abril, el flujo de subida guardaba el original con `Storage::disk('photos')`, el mismo disco que las miniaturas, y la respuesta de la API ya incluía `urls.original`. El archivo llegaba al disco tal cual, GPS incluido: con una foto hecha en el jardín se podía averiguar la dirección de casa de quien la había subido. En la versión corregida hay dos discos y el GPS desaparece antes de guardar:

```markdown
### 12.1 Two-disk model
- `Storage::disk('photos_private')` — originals only. Local: `storage/app/photos-private/`. Production: private S3 bucket with Block Public Access ON. URLs only via `temporaryUrl(...)` with 5-min TTL.
- `Storage::disk('photos')` — sized variants only. Local: `storage/app/public/photos/` + `php artisan storage:link`. Production: public S3 bucket fronted by CloudFront.
```

El requisito correspondiente está en `REQUIREMENTS.md`, NFR-3: "GPS EXIF must be stripped before originals are stored and before any EXIF JSON is returned by the API."

Los tokens de Sanctum no tenían abilities: un token válido podía hacer todo lo que podía hacer el usuario. Ahora los tokens llevan abilities como `photos:write` y `albums:write`, y la regla 10 del `CLAUDE.md` obliga a cada controlador que modifica datos a comprobar tanto la policy como `tokenCan`.

Los rate limits eran solo por IP, y detrás de un NAT corporativo muchos usuarios legítimos agotaban juntos el mismo límite. Ahora las rutas que no son de autenticación tienen también un límite por usuario, 300 peticiones por minuto, y el criterio de aceptación de T039 lo verifica.

La superficie de mass assignment no estaba cubierta por ninguna regla. Ahora lo está, escrita en dos puntos del `CLAUDE.md`: `$model->fill($request->validated())`, nunca `$request->all()`.

También hay que revisar las referencias entre archivos, porque dividir un documento grande las rompe con facilidad. En la rama del capítulo, el `CLAUDE.md` remite a `DESIGN.md §15.2` para los gates de tests, a `§15.3` para los commits y a `§14` para la paralelización, y `TASKS.md` cita `DESIGN.md §14.4` para los archivos magnet y `§13` para los hooks. Pero `DESIGN.md` se detiene en la sección 12: esas secciones solo existen en `SPEC.md`, donde se quedaron después de la división. Y el mapa de la documentación habla de "80+ atomic tasks" cuando el archivo contiene 112. Un agente que sigue una referencia a una sección que no existe o se para o se inventa algo. Por eso el prompt del spec-critic tiene el punto 8.

### Preguntas de cobertura

Además de la seguridad, hay que revisar la cobertura en las dos direcciones, de los requisitos a las tareas y al revés. Cuatro preguntas que hacer siempre:

```text
Para cada funcionalidad de docs/REQUIREMENTS.md, enumera las tareas de
docs/TASKS.md que la implementan. Señala las funcionalidades sin tarea.

Para cada criterio de aceptación de docs/REQUIREMENTS.md, dime qué tarea
lo tiene en su sección Acceptance. Señala los criterios huérfanos.

Para cada NFR (rendimiento, escalabilidad, seguridad), indícame qué
decisión de docs/DESIGN.md o qué tarea de docs/TASKS.md garantiza que se
cumpla. Señala los NFR sin implementación prevista.

Busca ciclos de dependencias en docs/TASKS.md. Busca tareas que dependan
de tareas de fases posteriores.
```

En la rama del capítulo estas preguntas encuentran huecos reales:

- NFR-1 pide un time-to-first-tile de la galería de 1,5 segundos como máximo con una conexión de 5 Mbps, y ninguna tarea lo cita.
- El mismo NFR-1 pide una puntuación de Lighthouse de al menos 90 en escritorio y 75 en móvil; T108 solo verifica el escritorio.
- AC-F1-2 quiere 2 columnas a 375 px, 3 a 768 y 4 a 1280. `DESIGN.md §8.4` tiene las clases correctas (`columns-2 md:columns-3 lg:columns-4`), pero los criterios de T067 no nombran los breakpoints, así que ningún test los comprobará.

La eliminación del GPS, en cambio, está cubierta: T074 pide un test con una imagen que contiene coordenadas GPS, y T080 lo vuelve a comprobar al final de la Fase 6.

Cuando encuentres un hueco, no lo arregles a mano. Pídele a Claude que inserte la tarea que falta en la fase adecuada y que actualice las dependencias:

```text
A partir de los huecos identificados, añade las tareas que faltan en las
fases adecuadas, actualiza las dependencias y realinea el CLAUDE.md si
cambian las referencias. No toques las tareas ya definidas: solo añade.
```

### Estimar el esfuerzo en las zonas de riesgo

El modelo también es optimista con los tiempos. Con 112 tareas de 30 minutos como máximo, la cuenta teórica se queda por debajo de 60 horas; la revisión del Photogallery, en cambio, estimaba 15-20 días de trabajo en secuencia y 8-10 con tres tracks en paralelo. La diferencia está casi toda en unas pocas zonas, que conviene revisar y dividir donde haga falta.

La pipeline asíncrona. Escribir `ProcessPhoto` es fácil; gestionar sus fallos, no: reintentos con backoff de 10, 30 y 60 segundos, estado `failed`, limpieza de las variantes ya generadas en el método `failed()`, coherencia entre el estado en la base de datos y los archivos en los discos.

La subida. Arrastrar y soltar y seleccionar archivos son dos interfaces sobre el mismo endpoint, con barra de progreso por archivo, validación en el cliente y polling del lote. A menudo lo que parecía una tarea acaba siendo tres.

El lightbox. Parece un componente, pero incluye navegación con teclado, prefetch, focus trap y una URL con `?photo=` que abre la foto al cargar.

Local y producción. En local, SQLite o MySQL, cola en base de datos y disco local; en producción, MySQL o Postgres, SQS y dos buckets de S3. Las migraciones tienen que seguir siendo neutrales y las colas hay que probarlas en las dos configuraciones. De hecho, en el Photogallery la migración a AWS es una fase aparte, la 8.

### Cuándo parar

Una o dos iteraciones de revisión son normales. Si hacen falta tres o más, el problema está antes: los requisitos eran demasiado vagos, y conviene reescribirlos antes de seguir.

Cuando las specs te convenzan, sin exigir que sean perfectas, haz commit de los cuatro archivos, haz `/clear` (las specs están en disco, no hace falta tenerlas en la conversación) y arranca. Con el contexto limpio, Claude lee el `CLAUDE.md`, luego `docs/TASKS.md`, elige la primera tarea con las dependencias satisfechas y empieza. Es lo que hacemos en el capítulo 19.

## Resumen {.unlisted}

- Los tres archivos separan qué construir (`docs/REQUIREMENTS.md`), cómo construirlo (`docs/DESIGN.md`) y en qué orden (`docs/TASKS.md`); el `CLAUDE.md` dice cómo se trabaja y remite a los demás.
- Cada tarea declara dependencias, paralelismo, secciones que leer y criterios de aceptación: son las specs las que deciden qué puede ir en paralelo y qué no.
- El build workflow le da a cada fase un prompt, un comando de verificación y un mensaje de commit. La fase está cerrada cuando la verificación pasa.
- SOLID, KISS y DRY en el `CLAUDE.md` funcionan cuando nombran clases y decisiones del proyecto. Para las reglas que no se pueden saltar hacen falta permisos y hooks (capítulos 11 y 12), y `/goal` (capítulo 20) para los criterios de aceptación.
- Antes de ejecutar, un spec-critic adversarial y las preguntas de cobertura: cada requisito no funcional tiene que tener una tarea que lo verifique, y cada referencia entre archivos tiene que apuntar a una sección que exista.

## Ejercicio {.unlisted}

Toma un proyecto tuyo con al menos cinco funcionalidades distintas, crea una rama (por ejemplo `sdd-mi-proyecto`) y genera los tres archivos con el prompt de la sección 18.2. Lanza el spec-critic de la sección 18.6 en una sesión limpia, clasifica los problemas en críticos, importantes y minucias, y aplica a las specs los fixes de los dos primeros grupos. Para comparar, el resultado del Photogallery está en la rama `book/cap-12-sdd-three-files` del repositorio companion.

El ejercicio está terminado cuando cada NFR de `docs/REQUIREMENTS.md` aparece en los criterios de aceptación de al menos una tarea, los archivos tienen su commit en tu rama y has encontrado al menos tres problemas que antes del spec-critic no habías visto. Si no llegas a tres, la revisión no era lo bastante adversarial: vuelve a lanzarla pidiendo explícitamente que sea más severa.
