# Capítulo 19. Ejecución y code review, de las primeras tareas a la wave review

::: {.chapter-goals}
[Qué aprenderás]{.callout-title}

Cómo ejecutar las tareas de `docs/TASKS.md` con un commit por tarea, cómo abrir el pull request de fin de fase y someterlo a revisión, cómo organizar una wave review con cuatro subagentes especializados y qué revisar en los controladores, las policies, el manejo de excepciones y el panel de administración Filament del Photogallery.

[Requisitos previos]{.callout-title}

Los capítulos 17 y 18, con `docs/REQUIREMENTS.md`, `docs/DESIGN.md` y `docs/TASKS.md` listos (rama `book/cap-12-sdd-three-files`). La GitHub CLI (`gh`) autenticada y los plugins Superpowers y `commit-commands` instalados (capítulo 8).

:::

Después de dos capítulos de especificaciones, aquí se escribe código. `REQUIREMENTS.md` dice qué tiene que hacer el Photogallery, `DESIGN.md` dice cómo y `TASKS.md` divide el trabajo en tareas de media hora como máximo. Por eso el prompt de ejecución puede ser corto: el contexto ya está en los archivos.

La diferencia con el vibecoding se nota más adelante. Cuando llegas a la tarea 47 y te preguntas por qué las claves primarias son UUID v7 y no auto-increment, la respuesta ya está escrita en la regla 8 del `CLAUDE.md` del proyecto y en `DESIGN.md` §4.

El ciclo es siempre el mismo: ejecutas una tarea, la verificas, haces commit y pasas a la siguiente. Al final de la fase abres un pull request y lo sometes a revisión. La revisión trabaja en tres niveles. La tarea individual, mientras Claude trabaja (diff leído, tests en verde, linter limpio). La fase, con el pull request abierto y revisores automáticos. Y la wave, un grupo de fases que juntas construyen una pieza de la arquitectura, donde se buscan las incoherencias entre módulos que no ves si miras una tarea cada vez.

## 19.1 Ejecutar las primeras tareas

### `TASKS.md` como estado del proyecto

Antes de escribir una sola línea, Claude revisa el entorno: si existe un repositorio Git, si hay un remote `origin`, las versiones de PHP, Composer y Node, las herramientas que necesita el proyecto. Luego lee `docs/TASKS.md`.

Al empezar la ejecución, el archivo del Photogallery tenía 112 tareas en 13 fases, con ID del tipo `T001`. Claude las cuenta, informa del número y propone un alcance realista para la sesión: la Fase 1, de `T001` a `T018`, porque el plan entero no cabe en un solo contexto. En la versión final del repo hay 124 tareas en 14 fases; las que sobran llegan con las features del capítulo 21.

El prompt para arrancar es simple a propósito:

```text
Procede con las tareas de la Fase 1 según docs/TASKS.md.
Un commit por tarea, un pull request por fase.
Usa subagentes donde las tareas sean independientes.
```

No explica nada porque no le hace falta. El prompt da la señal de salida; todo lo demás está escrito en las specs.

### Tareas independientes en paralelo

Cada tarea de `TASKS.md` tiene un campo `Parallel with`. `T001` (el scaffolding del backend Laravel) y `T002` (el scaffolding del frontend con Vite y React) se citan mutuamente, con la nota "different working dir": una trabaja en `backend/` y la otra en `frontend/`. Claude las lanza como dos subagentes, y mientras uno ejecuta `composer create-project` el otro ejecuta `npm create vite@latest`.

No hace falta pedirlo con una instrucción aparte. Las dependencias están en el plan, y la regla 3 del `CLAUDE.md` del Photogallery dice que se usen subagentes para las tareas marcadas como paralelas. Es la misma lógica que los jobs independientes de un pipeline de CI: donde no hay dependencias, todo corre a la vez.

::: {.callout .callout-warning}
[Atención]{.callout-title}

Un subagente aísla el contexto, no los archivos: todos trabajan en el mismo working tree. Con `T001` y `T002` no hay problema, porque las carpetas están separadas. Pero `T004`, `T005`, `T006` y `T017`, paralelas entre sí, tocan el mismo `backend/` y hacen commit en la misma rama. Dos agentes que lanzan `git add` y `git commit` a la vez pueden acabar cada uno en el commit del otro, y si dos tareas tocan el mismo archivo, gana el último que escribe. Por eso el `CLAUDE.md` del proyecto enumera los archivos que nunca se deben modificar en paralelo (`bootstrap/app.php`, las migraciones, `composer.json` y algunos más). Cuando una wave tiene muchas tareas independientes, dale a cada una su propio worktree: el capítulo 20 lo hace con `claude --worktree`, `/goal` y agent view.
:::

### Permisos: menos interrupciones

Hoy las sesiones interactivas arrancan en auto mode (capítulo 11). Un clasificador deja pasar las acciones coherentes con lo que pediste y bloquea las arriesgadas, así que comandos como `composer install` o `php artisan migrate` suelen pasar sin preguntas. Si en cambio trabajas en modo Manual, cada comando nuevo pide confirmación, y en una sesión de ejecución las peticiones se cuentan por decenas. Conviene registrar los comandos de rutina como reglas `allow` en `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(composer *)",
      "Bash(npm install *)",
      "Bash(npm create *)",
      "Bash(php artisan *)",
      "Bash(vendor/bin/pest *)",
      "Bash(vendor/bin/pint *)"
    ]
  }
}
```

Añade una regla cuando toda la familia de comandos sea segura para ese proyecto, y olvídate de `Bash(*)`: quieres quitar ruido, no perder el control. Una regla Bash compara el texto del comando, no el programa (capítulo 11).

### No sigas si algo está roto

Una tarea se marca en `TASKS.md`, de `[ ]` a `[x]`, solo cuando se cumplen sus criterios `Acceptance`: tests en verde (`vendor/bin/pest` en el backend), linter limpio (`vendor/bin/pint --test`, ESLint en el frontend) y el diff leído por ti.

Si un test falla, Claude se detiene: no marca la tarea con la promesa de volver más tarde. El `CLAUDE.md` del proyecto lo dice con todas las letras: nada de `--no-verify`, nada de `.skip`, nada de "tests later". Una tarea rota que se deja atrás vuelve a aparecer justo cuando vas a abrir el pull request de la fase. El diagnóstico se hace en el momento:

```text
El test PhotoObserverTest falla. Analiza el test, encuentra la causa,
propón el fix, aplícalo y verifica que la suite vuelva a estar en verde
antes de seguir.
```

Tenlo a mano, y nunca le pidas a Claude que lo "ignore por ahora".

### Commits atómicos y trazables

Después de las primeras tareas, `git log` muestra mensajes que remiten al plan. Estos son dos commits de la rama `book/cap-13-wave-1-backend`, recortados:

```text
chore(backend): scaffold Laravel 13 with core dependencies

T001 — DESIGN.md §2, CLAUDE.md "Tech stack".

Backend skeleton via composer create-project laravel/laravel ^13.0
(installs Laravel Framework 13.6.0).

chore(backend): publish framework migrations; tokenable_id is CHAR(36)

T003 — DESIGN.md §4.6, §4.7.

- Published Sanctum config and personal_access_tokens migration via
  vendor:publish.
- Edited the published migration to make `tokenable_id` CHAR(36) via
  uuidMorphs() so it can reference UUID v7 user ids (DESIGN.md §4.6).
  Also switched the token PK to uuid for consistency.
```

El asunto en formato Conventional Commits es el que sugiere el campo `Commit` de la tarea, y la primera línea del cuerpo dice qué tarea es y qué secciones de `DESIGN.md` la rigen. Seis meses después, cuando alguien pregunte por qué `tokenable_id` es `CHAR(36)`, buscas `T003` en el log y llegas a `DESIGN.md` §4.6, escrito antes que el código. La trazabilidad sale del proceso, no de la buena voluntad de quien hace commit.

Fíjate en la última línea del segundo commit, "Also switched the token PK to uuid for consistency": la spec no lo pedía. Volveremos a ello en §19.2.

### Las tareas de configuración

Las tareas más pesadas de hacer a mano son las de configuración: instalar un paquete, publicar sus archivos, añadir una clave al `.env`. Piden precisión más que creatividad, y Claude ejecuta los pasos en el orden correcto sin saltarse ninguno.

`T006` configura dos discos en `config/filesystems.php`: `photos` (público, solo las variantes) y `photos_private` (los originales). `T017` crea `config/photogallery.php`, copiado del Apéndice A de `DESIGN.md`:

```php
<?php

declare(strict_types=1);

return [
    'images' => [
        'max_dimension' => env('PHOTOS_MAX_DIMENSION', 8000),
        'max_file_size_kb' => env('PHOTOS_MAX_FILE_SIZE_KB', 10240),
        'variants' => [
            'thumbnail' => ['width' => 300, 'quality' => 80],
            'medium' => ['width' => 800, 'quality' => 85],
            'large' => ['width' => 1600, 'quality' => 90],
        ],
    ],
    'urls' => [
        'original_signed_ttl' => 300,
    ],
    'rate_limits' => [
        'auth_per_ip_per_minute' => 10,
        'api_per_ip_per_minute' => 120,
        'api_per_user_per_minute' => 300,
    ],
];
```

Los límites que cambian entre entornos vienen de variables de entorno; todo lo demás vive en un único sitio. Claude respeta la convención porque el `CLAUDE.md` pide añadir cada variable nueva tanto a `.env.example` como al Apéndice A en el mismo commit. Sin esa línea habría escrito los valores directamente en el código.

También llegan las primeras piezas reutilizables: el trait `App\Concerns\HasUuidV7` (`T004`) y dos enums (`T005`), `ProcessingStatus` (`Pending`, `Processing`, `Completed`, `Failed`) y `TokenAbility` con las abilities de Sanctum `photos:write`, `albums:write` y `admin`. Los enums le dan al código el vocabulario de las specs, y una errata se convierte en un error de tipo en lugar de un bug en tiempo de ejecución.

### El dominio toma forma

Con las migraciones de `T007` a `T012` aparece el dominio: usuarios, álbumes, tags, fotos y la tabla pivote `photo_tag` con clave primaria compuesta. La tabla `photos` tiene `original_path`, las tres rutas de las variantes, `is_favorite`, `exif` en JSON, `processing_status` y los índices compuestos que `DESIGN.md` §4.4 enumera uno por uno. Los modelos de `T013` siguen `DESIGN.md` §5: `Album` tiene `belongsTo(User)`, `hasMany(Photo)` y `belongsTo(Photo::class, 'cover_photo_id')` para la portada.

La portada es el caso interesante. El álbum apunta a una foto y la foto apunta a su álbum: una foreign key circular, con la que ninguna de las dos tablas se puede crear primero. El plan lo resuelve con dos tareas. `T008` crea `albums` con la columna `cover_photo_id` pero sin restricción, y `T011` añade la foreign key cuando `photos` ya existe. Claude no tuvo que inventarse nada, porque el problema se había detectado durante las specs.

### Cuándo parar

En una sesión larga llega un momento en que Claude propone nombres distintos, contradice tareas anteriores y olvida convenciones que respetó en los primeros veinte commits: el contexto está demasiado lleno de detalles viejos. La ventana de 1M tokens del modelo por defecto aleja el límite físico, pero no la deriva. Compruébalo con `/context` y usa las herramientas del capítulo 15. A mitad de una fase, `/compact` resume la conversación, con instrucciones sobre qué conservar:

```text
/compact conserva el estado de las tareas de la Fase 1, las decisiones sobre UUID v7 y Sanctum y los hallazgos todavía abiertos
```

Entre una fase y otra, `/clear` vuelve a empezar de cero y Claude relee desde los archivos el estado actualizado, con las casillas de `TASKS.md` marcadas. Una fase por sesión es un buen ritmo: un reinicio planificado cuesta menos que corregir cinco commits incoherentes.

## 19.2 El pull request de la Fase 1: primera revisión

### Abrir el pull request al final de la fase

Cuando todas las tareas de la Fase 1 están marcadas, la rama `feat/phase-1-backend-foundation` contiene los commits de las 18 tareas, 21 en total contando las limpiezas de Pint y un fix en las migraciones. Es el momento de abrir el pull request y parar.

Con el plugin `commit-commands` basta un comando:

```text
/commit-push-pr
```

El nombre completo es `/commit-commands:commit-push-pr`; el corto sirve mientras ningún otro comando use el mismo nombre. Crea una rama si estás en `main`, hace commit de lo que quede, hace push de la rama y abre el pull request con `gh pr create`. Con la GitHub CLI a mano:

```bash
gh pr create \
  --title "Phase 1: backend foundation (T001-T018)" \
  --body "Fase 1 completa: 18 tareas, limpieza con Pint, migraciones con foreign keys e índices."
gh pr checks   # estado de los checks de la CI
```

### El test plan local antes de cualquier revisión

Antes de llamar a cualquier revisor automático, ejecuta en local el test plan del pull request. Es el control básico: el código tiene que funcionar, no solo estar ahí. Para la Fase 1 los comandos salen de los criterios de `T018`, la tarea de revisión de la fase:

```bash
cd backend
composer install
cp .env.example .env
php artisan key:generate
php artisan migrate:fresh --seed
php artisan migrate:rollback
php artisan migrate
vendor/bin/pest
vendor/bin/pint --test
```

Con Laravel Sail, que veremos enseguida, los mismos comandos pasan por `vendor/bin/sail artisan` y `vendor/bin/sail test`. Si algo no funciona en local, revisar el código en ese estado no tiene sentido.

### Dos revisores independientes

Una vez confirmado que el código funciona, usa dos revisores independientes, porque herramientas distintas tienen puntos ciegos distintos. El primero es Codex de OpenAI conectado al repositorio de GitHub. Comenta los pull requests por su cuenta, en línea sobre las líneas del diff, y se le dan bien los problemas locales, como un índice que falta o un campo de más en `$fillable`.

El segundo es la revisión de Superpowers, la skill `requesting-code-review`. En abril de 2026 lanzaba el subagente `superpowers:code-reviewer`, que es quien firma la revisión del PR #1 en `docs/REVIEW-FIXES.md`; desde la versión 5.1 del plugin, la skill le pasa la misma checklist a un subagente genérico. Compara el código con el plan de la fase y con las reglas del proyecto, no solo con el diff. En la primera edición aquí escribía `/review`. Hoy ese comando es un alias de una revisión integrada en Claude Code y ya no activa Superpowers, así que pido la revisión por su nombre:

```text
Haz la code review del pull request actual con la skill requesting-code-review de Superpowers.
Procesa también los hallazgos de Codex en los comentarios del pull request. Clasifica
todo por severidad (BLOCKER / MAJOR / MINOR) y propón los fixes empezando
por los BLOCKER.
```

### Clasificar los hallazgos e iterar

El revisor no se limita a enumerar problemas: los clasifica. Estos son algunos hallazgos reales del PR #1, tomados de `docs/REVIEW-FIXES.md` y resumidos:

```text
[BLOCKER] photos.user_id sin índice
  foreignUuid('user_id')->constrained() no crea el índice en SQLite
  ni en PostgreSQL. DESIGN.md §4.4 lo pone el primero de la lista. Añadir
  $table->index('user_id') en la migración de photos.

[MAJOR] SANCTUM_TOKEN_EXPIRATION documentada pero no leída
  .env.example declara 1440 (24 horas), config/sanctum.php tiene
  'expiration' => null. Los tokens no caducan nunca.

[MAJOR] falta final en AppServiceProvider, DatabaseSeeder y las factories
  El CLAUDE.md pide clases final por defecto.

[MINOR] processing_status en $fillable
  Es estado interno del job, no input del usuario.
```

La regla de trabajo:

- BLOCKER: rompe una funcionalidad o abre un agujero. Se corrige antes del merge, sin excepciones.
- MAJOR: no bloquea, pero es un problema serio (rendimiento, desviación de la spec, una regla del proyecto incumplida). Se corrige en el mismo pull request si es posible.
- MINOR: estilo, nombres, microoptimizaciones. Se registra y se arregla en un pull request de limpieza.

No todos los hallazgos se corrigen cambiando código. Quitar los campos `processing_*` de `$fillable` habría obligado a usar `forceFill()` en todo el job, y la protección real son las Form Requests, que no aceptan esos campos. El fix fue un comentario en el modelo que explica la decisión (commit `75f93cd`).

Cuando le pasas un hallazgo a Claude, el prompt es directo:

```text
En el pull request hay este hallazgo sobre los personal access tokens de Sanctum:
[texto del hallazgo]. Verifícalo, corrígelo y añade un test que cubra el
caso. No sigas hasta que el test esté en verde.
```

Claude lee el hallazgo, revisa el código, aplica el fix, añade el test y hace commit. Si la revisión ya se había ejecutado, lo dice y no la vuelve a lanzar desde cero.

Resueltos los BLOCKER y los MAJOR, puedes hacer el merge. Luego queda un último paso que parece trivial:

```text
El pull request ya está mergeado.
```

Claude marca la Fase 1 como cerrada y prepara la Fase 2. Sin ese mensaje, sigue considerando que la fase está en revisión.

![Patrones de Eloquent y reglas de validación recopilados durante la revisión](figures/cap-19/fig-02.png)

<!-- TODO screenshot: fig-02 è a bassa risoluzione e il testo non si legge; rifare lo screenshot del documento di regole aperto nell'IDE. -->

### Laravel Sail: un entorno de desarrollo cercano a producción

El BLOCKER del índice tiene una causa más amplia: los tests corren sobre SQLite y producción no. SQLite es menos estricto que MariaDB con las restricciones y se comporta de otra forma con algunas funciones de fecha y hora, y el log de la revisión lo apunta como primera lección: problemas así no hacen fallar los tests en SQLite y solo aparecen en una base de datos de verdad. Por eso, justo después del PR #1, el Photogallery adoptó Laravel Sail (PR #2): Docker con MariaDB, Redis, Mailpit para el correo y MinIO, que emula S3 en local.

```bash
composer require laravel/sail --dev
php artisan sail:install
```

Elige MariaDB, Redis, Mailpit y MinIO. Sail genera `compose.yaml` con los servicios y los volúmenes. Para arrancar:

```bash
vendor/bin/sail up -d
vendor/bin/sail artisan migrate:fresh --seed
```

El `.env` apunta a `DB_CONNECTION=mariadb` y el desarrollo local queda muy cerca de producción. En la misma ronda llegó un MINOR: Filament 5 requiere PHP 8.4, así que `composer.json` pasó a `"php": "^8.4"`, y la CI y staging tienen que seguirlo.

### Cuando la revisión encuentra algo que la spec no dice

Volvamos al commit de `T003`. `DESIGN.md` §4.6 pedía un solo cambio en la tabla de Sanctum: `tokenable_id` como `CHAR(36)`, para apuntar a usuarios con UUID. Claude hizo algo más, "for consistency": convirtió en UUID la clave primaria de la tabla. Pero Sanctum inserta un token sin proporcionar un id, porque espera un auto-increment, y la primera llamada a `$user->createToken()` habría fallado con una violación de NOT NULL. Lo encontré yo antes de que empezara la revisión, y quedó en el log como F0, el primer BLOCKER. El fix (commit `fb39632`) devuelve la clave a `$table->id()` y añade `SanctumTokenTest`, que crea un token para un usuario con UUID y comprueba las abilities.

Aquí la spec era correcta, pero la regla 8 del `CLAUDE.md` ("toda clave primaria es UUID v7") empujaba en la dirección equivocada para una tabla del framework. Las specs nacen buenas pero no perfectas, y la revisión recoge lo que falta antes del deploy. Cuando un hallazgo revela un hueco en la spec, la corrección no se queda en el código: actualiza `DESIGN.md` o `REQUIREMENTS.md`, añade la tarea en `TASKS.md` y cita la sección en el commit. Cuando revela un agente que fue más allá de la spec, como aquí, lo que queda es el test de regresión.

## 19.3 Wave review: varios agentes sobre aspectos distintos

### Qué es una wave

Una wave es un grupo de fases o tareas que comparten un objetivo de arquitectura y que, una vez terminadas, forman una unidad del sistema. En el Photogallery las waves están escritas en el `CLAUDE.md`, en la sección "Parallelization rules". La Wave 0 es secuencial y termina con la Fase 1 que acabamos de cerrar. La Wave 1 tiene tres tracks paralelos: el Track A es la Fase 2, la capa de API, seguida de la Fase 6, el pipeline de imágenes; el Track B es la Fase 3, el panel Filament; el Track C son las Fases 4 y 5, el frontend React.

La Fase 2 por sí sola suma 27 tareas, de `T019` a `T045`, del middleware a los tests. Con ese tamaño, revisar tarea por tarea ya no basta.

En este capítulo cerramos la Wave 0 y, de la Wave 1, solo la Fase 2 del Track A. Las Fases de la 3 a la 6 quedan abiertas: las ejecutas en el capítulo 20, en paralelo. Las ramas del repo de acompañamiento cuentan las waves de otra manera: `book/cap-13-wave-1-backend` es la Wave 0 de `TASKS.md` (el estado al final de la Fase 1) y `book/cap-13-wave-2-api` es el Track A de la Wave 1 hasta la Fase 2. En el texto sigo los nombres de `TASKS.md`.

### Revisión de tarea y wave review

La revisión de la tarea pregunta "¿esta pieza hace lo que tenía que hacer?"; la wave review, "¿las piezas de esta wave encajan de forma coherente?". En este nivel salen los problemas más escurridizos: un controlador usa el query object y otro no, una mutación comprueba la policy y la de al lado no, un endpoint responde a los errores con un formato ligeramente distinto. Ninguno se ve mirando una tarea cada vez.

### Cuatro agentes en paralelo

La wave review lanza varios agentes especializados en paralelo, cada uno sobre un aspecto del código, y luego junta los informes en un solo documento. El prompt para la Fase 2:

```text
Wave review de la Fase 2, capa de API (tareas T019-T045).
Lanza cuatro subagentes en paralelo, en solo lectura (sin modificar
archivos), modelo sonnet:

1. security-auditor
   Busca: auth bypass, falta de validación de input, exposición de datos
   no autorizada, secretos en el código, CORS demasiado permisivo.

2. performance-reviewer
   Busca: consultas N+1, falta de eager loading, índices de BD ausentes en
   las columnas filtradas, operaciones síncronas que deberían ser jobs.

3. api-consistency
   Busca: error envelope no uniforme, status codes incorrectos,
   controladores que no usan el query object, nombres no uniformes.

4. test-coverage
   Busca: rutas críticas sin tests, edge cases que faltan, tests que
   se saltan la policy, N+1 en los tests, factories incompletas.

Para cada hallazgo: archivo, línea, severidad (CRITICAL / HIGH / MAJOR /
MEDIUM / LOW), fix propuesto. Junta los cuatro informes en un único
documento, por orden de prioridad.
```

Los cuatro subagentes arrancan en segundo plano, como todos los subagentes en las sesiones interactivas, y los sigues con `/tasks`. Cada uno lee y busca en el código (en las builds nativas de macOS y Linux la búsqueda pasa por `Bash`) y responde a un conjunto reducido de preguntas; en unos minutos tienes el panorama. Son de solo lectura, así que aquí el working tree compartido no es un problema. Para reutilizar los roles en otros proyectos, escríbelos como subagentes en `.claude/agents/security-auditor.md` y similares (capítulo 10), o pídele a Claude que los cree.

Claude Code también tiene un comando integrado, `/code-review`, que busca bugs de corrección en el diff en segundo plano: lo usamos en el capítulo 22 como pasada previa al deploy.

### Por qué especializar

Un agente generalista delante de un controlador mira todo y nada a fondo. Uno especializado aplica su checklist a todo el código: el security auditor busca cada punto de entrada de datos no fiables y cada campo que sale en la respuesta, y deja los nombres para otro. Hay un segundo motivo, escrito como última lección en `docs/REVIEW-FIXES.md`: la sesión que escribió el código no había visto ninguno de los problemas que luego encontraron los revisores. Un agente nuevo, sin el contexto de los commits, ve el código tal como es.

### Los hallazgos de la Fase 2

En el PR #4, el de la Fase 2, el log registra dos pasadas en paralelo, el code reviewer de Superpowers y un security auditor (las vemos en §19.4). Ordenados por aspecto, esos hallazgos caen en los cuatro roles del prompt.

Seguridad. `PhotoData`, la API resource de las fotos, devolvía `exif` y `processing_error` también a los usuarios anónimos. El EXIF puede contener coordenadas GPS, y el error de procesamiento, fragmentos de rutas internas. El fix aplica a estos campos el control "propietario o admin" que ya protegía `urls.original`, con cuatro tests en `PhotoDataTest` (en `main` el manejo del EXIF cambió otra vez, capítulo 22). El segundo hallazgo: el scaffolding de Laravel 13 no publica `config/cors.php`, así que estaba activa la policy por defecto con orígenes `*`. El fix publica el archivo con el origen leído de `FRONTEND_URL`, más tres tests en `CorsTest`.

Rendimiento. En el `PATCH` de las fotos, la conversión de slug a nombre de los tags hacía una consulta por slug dentro de una transacción, con un fallback que habría usado el slug como nombre. El fix es una sola consulta:

```php
$existingNames = $tags
    ? Tag::query()->whereIn('slug', $tags)->pluck('name')->all()
    : [];
```

El otro N+1 estaba en los tests: `PhotoControllerIndexTest` aceptaba hasta seis consultas, cuando con la paginación por cursor y los tres eager loads de `PhotoData::WITH` bastan cuatro. Un umbral holgado deja pasar un eager load de más, así que se ajustó a cuatro.

Coherencia de la API. `AlbumController@index` construía la consulta a mano en lugar de pasar por un query object como `PhotoQuery`. Ese hallazgo se dejó abierto a propósito: un `AlbumQuery` con un solo usuario es prematuro, y el log lo aplaza hasta que también lo necesite el panel Filament. El segundo pesaba más: `AlbumController@store` comprobaba la ability del token pero no la policy, mientras que todas las demás mutaciones comprueban las dos. Cada controlador por separado parecía correcto; al compararlos salió la carencia.

Tests. `AuthorizationTest` verificaba el bypass de los admins comprobando que el status no fuera ni 403 ni 401, así que un 500 habría pasado como éxito. Ahora la aserción exige 200, 201 o 204.

El commit de fix `3ece74b` lleva la suite de 148 a 158 tests.

### Juntar y priorizar

Con los informes reunidos, construye una lista de prioridades:

- CRITICAL: vulnerabilidad o bug funcional confirmado. Se corrige antes del merge.
- HIGH: agujero de autorización, datos expuestos a quien no debería verlos. Mismo pull request, antes del merge.
- MAJOR: patrones incumplidos, N+1 en producción, incoherencias entre módulos. Mismo pull request.
- MEDIUM: N+1 en los tests, `filename` visible para los anónimos. Pull request de seguimiento.
- LOW: un cast que falta, un `load()` inútil antes de un `fresh()`, `final` ausente en alguna clase. Un pull request de limpieza.

Resuelve CRITICAL, HIGH y MAJOR antes del merge. El resto va al backlog como issues de GitHub, para que no desaparezca; en el log del Photogallery, los hallazgos aplazados tienen una línea "Why deferred" con el motivo.

![Las lecciones aprendidas en las revisiones del PR #1 y del PR #4, al final de docs/REVIEW-FIXES.md](figures/cap-19/fig-01.png)

### Nombres coherentes: el momento es la wave review

Con sesiones separadas o subagentes en paralelo, los nombres derivan: `PhotoData` en un archivo, `PhotoDto` en otro, para lo mismo. El Photogallery tiene la convención en `DESIGN.md` §6.6, pero hay que verificarla antes de que los nombres se propaguen:

```text
Analiza los nombres de todas las API resources, los query objects, las form
requests y los data objects de la Fase 2. Encuentra las incoherencias (el mismo
concepto con nombres distintos en archivos distintos) y propón un plan de
alineación que mantenga la retrocompatibilidad.
```

Una limpieza de nombres durante la wave review lleva pocos minutos. Hecha meses después, cuando el nombre equivocado ha llegado a veinte archivos, es un día entero de refactoring.

### Un pull request para los fixes de la wave

Mantén los fixes separados del trabajo de la fase. En el PR #4 acabaron todos en `3ece74b`, con un mensaje que enumera cada hallazgo con su código (S1, S2, C1...) y los archivos tocados. En una wave más grande, abre un pull request solo para los fixes: el diff sigue siendo legible y quien revisa lo valora en bloque.

Después vuelve a lanzar la suite y comprueba las rutas:

```bash
php artisan migrate:fresh --seed
vendor/bin/pest
php artisan route:list --path=api   # todas las rutas registradas bajo /api/v1
```

Por último, prueba los endpoints con un cliente HTTP, por ejemplo un archivo `.http` en el IDE. Las respuestas esperadas para los álbumes:

```text
GET    /api/v1/albums        200, { "data": [...], "links": {...}, "meta": { "next_cursor": ..., "prev_cursor": ... } }
POST   /api/v1/albums        201 con el recurso creado
PATCH  /api/v1/albums/{id}   200, o 403 si no eres el propietario
DELETE /api/v1/albums/{id}   204, o 403
```

## 19.4 Revisión focalizada: controladores, policies, excepciones

### Por qué una revisión vertical

La wave review es horizontal. También hace falta una revisión vertical, que baja a un solo aspecto de la arquitectura y comprueba que todos los módulos siguen el mismo patrón. En una API REST hay tres aspectos que lo merecen: controladores, policies y manejo de excepciones. La referencia es el Photogallery con Laravel 13, pero los principios se trasladan bien: en NestJS están los Guards en lugar de las policies y los Pipes en lugar de las Form Requests; en Django, Permissions y Serializers.

### Middleware: forzar el JSON

Antes de los controladores hay una capa que a menudo se pasa por alto: el middleware que hace que toda petición a la API se trate como JSON. Sin él, un cliente que olvida `Accept: application/json` recibe una página de error en HTML. Se registra en `bootstrap/app.php` (`T019`):

```php
->withMiddleware(function (Middleware $middleware): void {
    $middleware->api(prepend: [
        ForceJsonResponse::class,
    ]);
})
```

El middleware es corto:

```php
final class ForceJsonResponse
{
    public function handle(Request $request, Closure $next): Response
    {
        $request->headers->set('Accept', 'application/json');

        return $next($request);
    }
}
```

En la revisión comprueba dos cosas. El middleware está en el grupo `api`, no en `web`, donde rompería las páginas Blade y el panel Filament. Y se ejecuta antes de la autenticación, que es la razón de usar `prepend`: si no, el 401 de `auth:sanctum` puede salir sin el content type que espera el cliente.

### Manejo de excepciones

`DESIGN.md` §11.1 define un envelope único para toda respuesta que no sea 2xx bajo `/api/*`. En Laravel 13 se configura en `bootstrap/app.php`, dentro de `withExceptions` (`T020`). Un extracto del código del Photogallery:

```php
->withExceptions(function (Exceptions $exceptions): void {
    $exceptions->shouldRenderJsonWhen(
        fn (Request $request) => $request->is('api/*')
    );

    $exceptions->render(function (AccessDeniedHttpException $e, Request $request) {
        if ($request->is('api/*')) {
            return response()->json(['message' => 'This action is unauthorized.'], 403);
        }
    });

    $exceptions->render(function (ThrottleRequestsException $e, Request $request) {
        if ($request->is('api/*')) {
            $retryAfter = $e->getHeaders()['Retry-After'] ?? 60;

            return response()
                ->json(['message' => 'Too many requests.'], 429)
                ->header('Retry-After', (string) $retryAfter);
        }
    });
})
```

El archivo completo gestiona también el 401, el 404, el 413 y el 415. El 422 sigue siendo el de Laravel, que ya tiene la forma `{ message, errors }`.

El hallazgo más sutil de esta parte acabó entre las lecciones del log: Laravel 13 convierte `AuthorizationException` en `AccessDeniedHttpException` y `ModelNotFoundException` en `NotFoundHttpException` antes de que se ejecuten los callbacks `render`. Si tipas el callback con la excepción original, nunca se dispara, y el cliente recibe el mensaje por defecto en lugar de tu envelope. En el código de arriba los tipos son los ya convertidos, y un test con `assertExactJson` lo verifica. Otras dos cosas que revisar: el 429 debe tener un payload coherente y el header `Retry-After`, y las excepciones 5xx nunca se deben tragar. Si capturas una excepción con un `try/catch` y respondes, regístrala en el log antes o vuelve a lanzarla.

### Controladores: el patrón que no cambia

Todos los controladores de esta API siguen el mismo esquema: return type explícito (`JsonResponse`, `AnonymousResourceCollection`, `Response` para el 204), una Form Request para cada mutación, la salida siempre a través de una API resource y un doble control de autorización. La regla 10 del `CLAUDE.md` pide exactamente eso: cada mutación comprueba la ability del token de Sanctum y la policy. Un extracto de `AlbumController` después del fix del PR #4:

```php
public function store(StoreAlbumRequest $request): JsonResponse
{
    $this->ensureAbility($request, TokenAbility::AlbumsWrite);
    if ($request->user()?->cannot('create', Album::class)) {
        throw new AuthorizationException;
    }

    $album = Album::create([
        ...$request->validated(),
        'user_id' => $request->user()->id,
    ]);

    $album->load(AlbumData::WITH)->loadCount('photos');

    return AlbumData::make($album)->response()->setStatusCode(201);
}

public function destroy(Request $request, Album $album): Response
{
    $this->ensureCan($request, 'delete', $album);

    $album->delete();

    return response()->noContent();
}
```

`ensureCan()` es un método privado que hace los dos controles a la vez. La policy `create` hoy devuelve siempre `true`: existe para que las mutaciones sean simétricas y la regla se pueda endurecer sin tocar el controlador. Cuidado si tu proyecto usa `$this->authorize()`: en Laravel 13 el `Controller` base del scaffolding está vacío, y sin el trait `AuthorizesRequests` ese método no existe.

La checklist para cada controlador de la wave: salida siempre desde una resource (`AlbumData::make()`, nunca `response()->json(['data' => $album->toArray()])`), eager load desde la constante `AlbumData::WITH`, mutaciones con `$request->validated()` y nunca con `$request->all()`, escrituras múltiples dentro de `DB::transaction()` (regla 11).

### Policies: propiedad estricta y bypass para el admin

Las policies deciden quién puede hacer qué. En el Photogallery son planas a propósito, solo la regla de propiedad:

```php
final class AlbumPolicy
{
    public function create(User $user): bool
    {
        return true;
    }

    public function view(User $user, Album $album): bool
    {
        return $album->user_id === $user->id;
    }

    public function update(User $user, Album $album): bool
    {
        return $album->user_id === $user->id;
    }

    public function delete(User $user, Album $album): bool
    {
        return $album->user_id === $user->id;
    }
}
```

El bypass para los admins vive en un solo sitio, `AppServiceProvider::boot()`, y cubre todas las policies:

```php
Gate::before(fn (User $user) => $user->isAdmin() ? true : null);
```

El hallazgo clásico está justo aquí: un `before` (en el Gate o en una policy) que devuelve `false` para quien no es admin. `false` lo deniega todo de inmediato, incluidas las acciones que la policy habría permitido. El contrato correcto es `true` para los admins y `null` para todos los demás, que deja seguir el control normal.

El segundo hallazgo típico es la policy no registrada. Laravel la encuentra solo si se llama `AlbumPolicy` y está en `app/Policies`; si no, hace falta `#[UsePolicy]` en el modelo o `Gate::policy()` en un service provider. Una policy que nunca se llama no bloquea a nadie, y el código parece funcionar. El tercero llega con los recursos hijos: si algún día el Photogallery tiene álbumes privados, la visibilidad de una foto tendrá que subir hasta el álbum, no quedarse en `photo.user_id`.

### Un único formato para todos los errores

Si el manejo de excepciones se hizo al principio de la wave, como aquí con `T020`, todos los errores salen con el mismo formato. La revisión tiene que comprobar que todos los controladores pasan por él. Los formatos esperados, según `DESIGN.md` §11.1:

```text
422  { "message": "The name field is required.", "errors": { "name": ["..."] } }
403  { "message": "This action is unauthorized." }
404  { "message": "Resource not found." }
```

Si un controlador lanza por su cuenta `abort(403, 'Forbidden')`, el frontend tiene que manejar un caso especial: cada excepción al formato es un bug de integración esperando su momento. La comprobación más rápida es una petición no autorizada contra cada endpoint. En el Photogallery lo hace `AuthorizationTest` (`T040`), que recorre todas las mutaciones y verifica un 401 sin token y un 403 con el token de otro usuario.

### Dos agentes sobre el mismo pull request

Una vez entendido el código, el paso práctico es lanzar dos agentes en paralelo sobre el pull request. Es lo que pasó en el PR #4:

```text
Haz una code review del PR #4 que incluya buenas prácticas y controles
de seguridad. Lanza en paralelo el code-reviewer de Superpowers y un
security auditor.
```

El code reviewer mira la calidad, las reglas del proyecto y el ajuste a la spec; el security auditor, las vulnerabilidades, la autorización, el input, CORS y los secretos. Salen dos informes que hay que consolidar, como con dos revisores humanos en un pull request delicado. El security auditor del PR #4 encontró además un problema que ningún test local podía mostrar: sin `trustProxies`, detrás de un balanceador de carga `$request->ip()` devuelve la dirección del proxy, y el límite de 10 logins por minuto por IP se convierte en un único cubo compartido por todos. El fix lee `TRUSTED_PROXIES` del `.env`.

## 19.5 Code review de un panel de administración (Filament)

### Por qué el panel de administración merece su propia revisión

El panel de administración se trata a menudo como "la parte interna", que solo usan los admins y que por tanto es menos crítica. Pero el panel ve todos los datos, ejecuta operaciones masivas sobre miles de registros y suele tener menos tests que la API pública. La revisión dedicada sirve para recuperar los controles que en la API son rutina.

En el Photogallery el panel está construido con Filament 5, un framework para Laravel que te da CRUD, dashboards, widgets y formularios a partir de convenciones y componentes listos para usar. Es la Fase 3, de `T046` a `T054`: el Track B de la Wave 1, que al terminar este capítulo todavía está por ejecutar y que el capítulo 20 hace correr en paralelo con la API y el frontend. Esta sección es la checklist que aplicar cuando el Track B llegue a revisión; el código de los ejemplos viene del repo en `main`. Backend Laravel, API REST, frontend React, admin Filament: la wave review funciona en todas las capas, solo cambia la checklist.

### Comprobar que todo funciona en el navegador

Antes del código, abre el navegador. Claude genera resources, widgets y páginas, pero la integración puede fallar igualmente: llamadas al host equivocado, orígenes CORS que no coinciden, la URL del backend escrita en el código.

En el Photogallery, cuando llegaron el panel y el frontend, la prueba manual encontró enseguida dos problemas:

1. El frontend React llamaba al host del dev server de Vite (puerto 5174) en lugar de al backend en el puerto 80. Ningún error en el código, solo la URL equivocada en el cliente axios.
2. Corregida la URL, aparecía un error de CORS: `FRONTEND_URL` en el `.env` del backend apuntaba a `localhost:5173`, el puerto por defecto de Vite con el que se había inicializado el proyecto, mientras que el dev server corría en el 5174 porque el 5173 estaba ocupado.

La regla que sale de aquí: nada de URLs en el código y nada de dar puertos por supuestos. El cliente lee la base de la API de una variable de entorno:

```bash
# frontend/.env.example
VITE_API_BASE_URL=http://localhost/api/v1
```

```ts
// frontend/src/api/client.ts
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api/v1',
});
```

`.env.example` va al repositorio, el `.env` real se queda en local, y en staging basta con poner el valor correcto. Lo mismo vale para `FRONTEND_URL` en el backend, que alimenta `config/cors.php`.

### La checklist para un panel Filament

Operaciones masivas. Toda acción sobre una selección múltiple tiene que pedir confirmación. En Filament 5 las acciones están en `Filament\Actions` y se enganchan a la tabla con `toolbarActions()`. Un extracto de `PhotosTable`:

```php
->toolbarActions([
    BulkActionGroup::make([
        DeleteBulkAction::make(),
        BulkAction::make('reprocess')
            ->label('Reprocess')
            ->icon('heroicon-o-arrow-path')
            ->color('warning')
            ->requiresConfirmation()
            ->action(function (Collection $records): void {
                $records->each(function (Photo $photo): void {
                    $photo->update([
                        'processing_status' => ProcessingStatus::Pending,
                        'processing_attempts' => 0,
                        'processing_error' => null,
                    ]);
                    ProcessPhoto::dispatch($photo);
                });
                Notification::make()->title('Reprocessing dispatched')->success()->send();
            }),
    ]),
])
```

`DeleteBulkAction` pide confirmación por sí sola; un `BulkAction` escrito a mano no, hasta que añades `requiresConfirmation()`, y un clic equivocado vuelve a poner en cola cientos de jobs. También es útil un audit log de las operaciones masivas (quién, cuándo, sobre qué registros), por ejemplo con `spatie/laravel-activitylog`.

Filtros e índices. Toda columna que se use como filtro debería tener un índice. La revisión compara los `filters()` de la tabla con las migraciones:

```php
// PhotosTable.php
SelectFilter::make('processing_status')
    ->options(ProcessingStatus::class),

// migración de photos
$table->index(['processing_status', 'created_at'], 'photos_status_created_idx');
```

Filament no avisa si falta el índice. Lo descubres bajo carga, con un full table scan.

Validación en dos niveles. En Filament la validación se declara en el campo. `AlbumForm` hace que el nombre sea único por usuario:

```php
TextInput::make('name')
    ->required()
    ->maxLength(255)
    ->unique(
        ignoreRecord: true,
        modifyRuleUsing: fn (Unique $rule) => $rule->where('user_id', auth()->id()),
    ),
```

Esa regla solo vale en el panel. Quien llama a la API pasa por `StoreAlbumRequest`, con la misma unicidad por `user_id` (`T025`). Hacen falta las dos, y la revisión comprueba que digan lo mismo.

Autorización. La primera puerta es el acceso al panel: `User` implementa `FilamentUser` y `canAccessPanel()` devuelve `isAdmin()`, así que un usuario normal que abre `/admin` vuelve al login (`AC-F11-1` en `REQUIREMENTS.md`). La segunda son las policies, que Filament usa (`viewAny`, `create`, `update`, `delete`) para mostrar u ocultar páginas y acciones. El hallazgo más común es una resource sin policy porque "el panel ya está protegido por el login": si un bug en `canAccessPanel()` deja entrar a alguien que no es admin, sin policies puede hacer de todo. Lo mismo vale para un método que falta: Filament 5 permite la operación cuando falta la policy o su método (por ejemplo `deleteAny`, que usan las bulk actions), salvo que un `Gate::before` la deniegue. `->strictAuthorization()` en la configuración del panel convierte cada policy o método que falta en una excepción, y en la revisión conviene activarlo.

Exportación e importación. Si el panel ofrece exportación a CSV o importación por lotes, hace falta un rate limit en la exportación, que si no puede saturar la base de datos y el disco, y validar cada fila importada con las reglas de la Form Request de la API.

### Los componentes del frontend y el pipeline que falta

En la misma Wave 1, el Track C (Fases 4 y 5, también en el capítulo 20) trae los primeros componentes React: la cuadrícula de fotos (`MasonryGrid`, `PhotoCard`), el lightbox, el modal de subida, la barra lateral y los atajos de teclado, de `T063` a `T071`. Los componentes están conectados a los datos de la API, pero las fotos muestran el estado `processing` en lugar de la imagen.

Es lo esperado. El pipeline que genera las variantes es la Fase 6, de `T072` a `T080`, que en el Track A va después de la API; hasta entonces las variantes no existen. Pedirle a Claude que "arregle el estado processing" sería un error, porque se inventaría un atajo fuera del plan. El hallazgo correcto es "esperado, lo resuelve la Fase 6", después de comprobar en `TASKS.md` que la dependencia está escrita: `T077` (el job `ProcessPhoto`) y `T079` (la subida conectada a los jobs reales) están ahí. Si faltaran, el fix de la revisión sería añadir la tarea, no escribir código.

### Reglas válidas para cualquier panel de administración

Lo que salió del panel Filament vale para cualquier admin, sea React Admin, Refine, AdminJS o uno escrito a mano:

1. La autenticación no basta: cada operación comprueba los permisos.
2. Las operaciones masivas siempre piden confirmación, a ser posible mostrando el número de registros afectados.
3. Cada filtro de la interfaz tiene su índice; si no, en producción se convierte en un full table scan.
4. Hosts, puertos y rutas de la API vienen de variables de entorno; el `.env.example` del repositorio es el contrato entre desarrollo y deploy.
5. Las guías del framework se instalan antes de la primera wave. Para Laravel está Laravel Boost (`composer require laravel/boost --dev` y luego `php artisan boost:install`), que trae las convenciones de Laravel y un servidor MCP con tools como `search-docs` y `database-schema`. El `CLAUDE.md` del Photogallery contiene sus guías en la sección "Laravel Boost tools", pero `laravel/boost` no aparece en el `composer.json` del repo: si clonas el proyecto y quieres esas tools, instálalo tú. Si lo instalas después, Claude puede alinear el código ya escrito, pero empezar con las guías te ahorra la limpieza.
6. La revisión del código y la prueba en el navegador encuentran cosas distintas: los agentes y Codex encuentran bugs en el código, el panel abierto con la pestaña Network encuentra bugs de integración. Antes del merge hacen falta las dos, y la segunda te toca a ti.

## Resumen {.unlisted}

- Ejecuta las tareas de `TASKS.md` con un commit por tarea, con el ID de la tarea y las secciones de `DESIGN.md` en el cuerpo del mensaje; marca la tarea solo con los tests en verde, el linter limpio y el diff leído.
- Los subagentes en paralelo comparten el working tree: sirven con carpetas separadas, pero para tareas paralelas sobre el mismo código usa los worktrees del capítulo 20.
- Abre el pull request de la fase después de un test plan local en verde, pon a trabajar a dos revisores independientes y clasifica los hallazgos en BLOCKER, MAJOR y MINOR; cuando un hallazgo revela un hueco en la spec, actualiza la spec además del código.
- La wave review busca las incoherencias entre módulos: cuatro subagentes en solo lectura (seguridad, rendimiento, coherencia de la API, tests) y un único informe ordenado por severidad.
- En los controladores comprueba return types, Form Requests, resources y el doble control de ability más policy en cada mutación; en las policies, `null` y no `false` para quien no es admin.
- El panel de administración es tan crítico como la API pública: confirmación en las acciones masivas, índices en los filtros, validación en dos niveles, una policy para cada resource y la URL de la API en una variable de entorno.

## Ejercicio {.unlisted}

Repite la wave review de la Fase 2 y compara tus hallazgos con los reales.

1. Clona la rama `book/cap-13-wave-2-api` y crea una rama local desde el commit `93f1070` ("chore: Phase 2 review"), el último antes de los fixes: `git switch -c wave-review 93f1070`.
2. Ejecuta el test plan local con Sail (`vendor/bin/sail up -d`, `vendor/bin/sail artisan migrate:fresh --seed`, `vendor/bin/sail test`) y apunta cuántos tests pasan.
3. Lanza la wave review con el prompt de cuatro agentes de §19.3, adaptando el nombre de la wave y el rango de tareas si trabajas en un proyecto propio.
4. Compara el informe conjunto con `docs/REVIEW-FIXES.md` en la punta de la rama `book/cap-13-wave-2-api`, sección "PR #4".
5. Para cada hallazgo CRITICAL o HIGH, pídele a Claude el fix con un test que cubra el caso, y vuelve a lanzar la suite.

El ejercicio está terminado cuando tienes un documento de hallazgos con severidad y estado para cada entrada, la suite está en verde, no quedan hallazgos CRITICAL o HIGH abiertos y has marcado qué hallazgos de `REVIEW-FIXES.md` (de S1 a S5, de C1 a C8) encontraron tus agentes y cuáles no.
