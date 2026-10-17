# Capítulo 20. Oleadas en paralelo con worktrees, /goal y agent view

::: {.chapter-goals}
[Qué aprenderás]{.callout-title}

Cómo ejecutar en paralelo los tracks independientes de una wave de la Photogallery, cada uno en su propio git worktree y con una condición de finalización que Claude tiene que demostrar que ha cumplido. Después, cómo seguir varias sesiones en segundo plano desde una sola pantalla, cómo dar un worktree también a los subagentes y cómo juntar el trabajo sin dejar copias y ramas sueltas.

[Requisitos previos]{.callout-title}

El repo de la Photogallery tal como queda al final del capítulo 19 (rama `book/cap-13-wave-2-api` del companion repo) y la GitHub CLI (`gh`) configurada como en el capítulo 19.

:::

Al final del capítulo 19 la Photogallery tiene la Fase 1 (modelos, migraciones, seeders) y la Fase 2 (API) integradas en `main`. En `docs/TASKS.md` quedan abiertas la Fase 3 (admin con Filament, de T046 a T054), la Fase 4 (setup del frontend React, de T055 a T062), la Fase 5 (componentes React, de T063 a T071) y la Fase 6 (pipeline de imágenes, de T072 a T080), más tres tareas de la Fase 2 aplazadas a la 6: T029, T032 y T035. Son 38 tareas.

El `CLAUDE.md` del proyecto ya dice cómo ejecutarlas. La sección "Parallelization rules" agrupa estas fases en la Wave 1, dividida en tres tracks: Track A (Fase 2 y luego Fase 6), Track B (Fase 3), Track C (Fase 4 y luego Fase 5). Y añade "each in its own git worktree": cada track en su worktree. En el capítulo 19 le pedimos a Claude que usara subagentes donde las tareas eran independientes, y para dos scaffoldings bastaba. Con decenas de tareas entre backend y frontend, todas en la misma carpeta, tarde o temprano dos agentes tocan el mismo archivo. Aquí le damos a cada track su propio worktree, como pide el archivo.

Una nota sobre los nombres. Las ramas del companion repo llaman "wave 1" y "wave 2" a las dos primeras fases ejecutadas en el capítulo 19. En `docs/TASKS.md` la Fase 1 pertenece a la Wave 0 y la API es el Track A de la Wave 1. A partir de aquí uso los nombres del archivo, porque son los que va a leer Claude.

## 20.1 Tres formas de trabajar en paralelo

Claude Code ofrece tres herramientas para hacer varias cosas a la vez, y cada una aísla algo distinto.

| Herramienta | Qué aísla | Cuándo usarla |
| --- | --- | --- |
| Subagente | El contexto, dentro de una sesión | Búsquedas y subtareas cortas, como en los capítulos 10 y 19 |
| Worktree (`claude --worktree`) | Los archivos: cada sesión tiene su copia y su rama | Tareas que modifican archivos distintos al mismo tiempo |
| Sesión en segundo plano (`claude --bg`, `claude agents`) | El terminal: la sesión avanza sin ti | Varias tareas largas que seguir desde una sola pantalla |

Un subagente tiene una ventana de contexto solo para él, pero lee y escribe en la misma carpeta que la sesión que lo lanzó. Si dos subagentes modifican `routes/api.php` a la vez, uno pisa los cambios del otro, o los tests de uno fallan por culpa de los cambios a medias del otro. Un worktree resuelve el problema de los archivos. Una sesión en segundo plano resuelve otro: tener que mantener abiertos cinco terminales para cinco trabajos. Las tres se combinan: una sesión en segundo plano trabaja en un worktree, y un subagente puede tener su propio worktree temporal.

## 20.2 Elegir los tracks y preparar el repo

### Las dependencias ocultas

El `CLAUDE.md` dice que los tres tracks "share zero files", que no comparten archivos. Antes de lanzarlos juntos, sin embargo, lee las tareas y no solo los títulos de las fases. T048 pide una acción de Filament para reprocesar que llama a `ProcessPhoto::dispatch($record)`, y el job `ProcessPhoto` nace con T077, en la Fase 6. El campo `Depends on` de T048 solo cita T047, así que el problema solo se ve en los criterios de aceptación. Si lanzas el Track B junto con la Fase 6, la sesión del admin se encuentra con una clase que no existe y o se detiene o se la inventa.

Por eso la primera tanda junta dos tracks que de verdad no se tocan:

- Track A, continuación: la Fase 6 (T072-T080) más T029, T032 y T035, todo en el backend;
- Track C: la Fase 4 (T055-T062), solo en el frontend.

La segunda tanda, cuando la pipeline ya esté en `main`, lanza la Fase 3 y la Fase 5.

Hay un archivo que tocan todas las sesiones: `docs/TASKS.md`, porque la regla 2 del `CLAUDE.md` quiere la casilla marcada en el mismo commit que la tarea. Pero las sesiones modifican líneas de secciones distintas, así que Git normalmente las une sin conflictos. Los demás archivos "imán" que enumera el `CLAUDE.md` (`composer.json`, `package.json`, `bootstrap/app.php`, `App.tsx`, `main.tsx`) quedan para una sola sesión cada vez. En la rama del capítulo 19 `composer.json` ya contiene `filament/filament` e `intervention/image-laravel`, así que, en teoría, ningún track de la primera tanda tiene que tocarlo.

### .gitignore, .worktreeinclude y baseRef

Tres preparativos, para hacer commit en `main` antes de abrir las sesiones.

El primero: Claude Code crea los worktrees en `.claude/worktrees/` dentro del repo, y esa carpeta no debe acabar en Git. La Photogallery no tiene un `.gitignore` en la raíz (solo están los de `backend/` y `frontend/`), así que lo creas:

```text
.claude/worktrees/
```

El segundo tiene que ver con los archivos ignorados. Un worktree es un checkout limpio: todo lo que Git ignora no está. Los tests del backend necesitan `backend/.env`, que contiene `APP_KEY` (el `phpunit.xml` configura SQLite en memoria, pero no la clave). El archivo `.worktreeinclude` en la raíz enumera los archivos ignorados que Claude Code copia en cada worktree nuevo:

```text
backend/.env
```

El frontend no tiene `.env`: `src/api/client.ts` usa `/api/v1` cuando `VITE_API_BASE_URL` no está definida. Si tú tienes uno, añade `frontend/.env.local` a la lista. `vendor/` y `node_modules/` no van en la lista: se reinstalan, y es más rápido que copiarlos.

El tercero es el punto de partida. Por defecto un worktree parte del `main` remoto. Si hiciste merge de algo en local y todavía no hiciste push, las sesiones nuevas no lo ven. Para partir de tu `HEAD` local, añade la clave `worktree` a `.claude/settings.json`, junto a los hooks que el archivo ya contiene:

```json
{
  "worktree": {
    "baseRef": "head"
  }
}
```

En la primera tanda no cambia nada, porque `main` coincide con el remoto. Te hará falta en la segunda, si decides hacer merge en local (sección 20.5).

```bash
git add .gitignore .worktreeinclude .claude/settings.json
git commit -m "chore: worktree setup for parallel tracks"
git push
```

## 20.3 Dos sesiones, dos worktrees

Un worktree es una segunda carpeta de trabajo del mismo repositorio, con sus propios archivos y su propia rama, pero con la misma historia de Git. Con `--worktree` y un nombre, Claude Code crea el worktree en `.claude/worktrees/<nombre>` sobre una rama nueva `worktree-<nombre>` y arranca la sesión ahí dentro.

Abre dos terminales en la raíz del repo. En el primero:

```bash
claude --worktree fase6-pipeline
```

En el segundo:

```bash
claude --worktree fase4-frontend
```

Desde cualquiera de los dos, comprueba qué ha pasado con el prefijo `!`, que ejecuta un comando de shell desde la sesión:

```text
!git worktree list
```

```text
~/projects/photogallery                                  5d1f2a9 [main]
~/projects/photogallery/.claude/worktrees/fase6-pipeline 5d1f2a9 [worktree-fase6-pipeline]
~/projects/photogallery/.claude/worktrees/fase4-frontend 5d1f2a9 [worktree-fase4-frontend]
```

Tres carpetas, tres ramas, un solo repositorio. `backend/.env` ya está en su sitio en los dos worktrees, pero faltan las dependencias. En la primera sesión:

```text
instala las dependencias del backend con composer install
```

En la segunda:

```text
instala las dependencias del frontend con npm ci
```

En un proyecto real este es el primer paso en cada worktree, y en un Laravel con Filament tarda unos minutos.

Las copias comparten la historia de Git y la memoria automática, que Claude Code guarda en `~/.claude/projects/<proyecto>/memory/` para todo el repositorio. El `CLAUDE.md`, en cambio, es un archivo versionado: cada worktree tiene el suyo, idéntico al de `main` en el momento de crearlo. Si lo modificas en `main` mientras las sesiones trabajan, ellas no ven el cambio hasta que lo integres en sus ramas.

<!-- TODO screenshot: due terminali affiancati con claude --worktree fase6-pipeline e fase4-frontend, e l'output di git worktree list -->

::: {.callout .callout-warning}
[Atención]{.callout-title}

Si arrancas Laravel Sail en dos worktrees a la vez, los contenedores se pelean por los mismos puertos (80, 3306, 6379) y, como en las dos copias la carpeta se llama `backend`, también por el mismo nombre de proyecto de Docker Compose. Para este capítulo no necesitas Sail: los tests corren sobre SQLite en memoria con `composer test`. Si necesitas la aplicación en marcha, tenla levantada en un solo worktree cada vez, o cambia `APP_PORT` y `FORWARD_DB_PORT` en el `.env` de uno de los dos.
:::

## 20.4 Un objetivo verificable con /goal

Normalmente cada sesión trabaja un turno y luego se detiene a esperarte. Con once tareas por delante, eso significa volver al terminal cada pocos minutos a escribir "continúa". `/goal` fija una condición de finalización: Claude sigue trabajando, turno tras turno, hasta que la condición se cumple. Quien la juzga es un evaluador separado, que la comprueba al final de cada turno y, si falta algo, devuelve a Claude al trabajo.

### Escribir la condición

El evaluador no ejecuta comandos ni abre archivos. Juzga lo que Claude ha mostrado en la conversación. Por eso la condición tiene que nombrar una comprobación que Claude ejecuta y cuyo resultado acaba en pantalla. Toma una condición como esta:

```text
/goal la pipeline de imágenes funciona
```

El evaluador no tiene forma de saberlo. Verá a Claude escribir que la pipeline funciona y le dará la razón, o no se la dará nunca. El mismo principio vale para los criterios de aceptación del capítulo 18: "testable, not aspirational", como dice la cabecera de `docs/TASKS.md`.

En la sesión `fase6-pipeline`:

```text
/goal las tareas T029, T032, T035 y de T072 a T079 tienen Status [x] en docs/TASKS.md (muéstrame las líneas Status con grep), "composer test" en la carpeta backend termina con código 0 y cada tarea tiene su commit en la rama del worktree (muéstrame git log --oneline)
```

En la sesión `fase4-frontend`:

```text
/goal las tareas de T055 a T061 tienen Status [x] en docs/TASKS.md (muéstrame las líneas Status con grep), "npm run build" y "npm run lint" en la carpeta frontend terminan con código 0 y cada tarea tiene su commit en la rama del worktree (muéstrame git log --oneline)
```

Las decisiones detrás de estas dos líneas:

- `composer test` es el script del `composer.json` del backend: limpia la caché de configuración y lanza `php artisan test`, es decir, Pest;
- en el frontend, en esta rama, `package.json` todavía no tiene un script `test` (Vitest está instalado, pero los primeros tests llegan con la Fase 5), así que la comprobación son build y lint, los mismos que pide T062;
- T080 y T062 se quedan fuera. Son las tareas de revisión de la fase: T080 requiere una subida real con el queue worker en marcha, T062 un `curl` contra el proxy de Vite con Laravel en ejecución. Esas las haces tú, como en el capítulo 19;
- el "muéstrame" está ahí para el evaluador: sin la salida de `grep` y de `git log` en la conversación, no tiene pruebas de que las tareas estén marcadas y con su commit.

El prompt no explica cómo trabajar. Leer las secciones de `DESIGN.md` indicadas en `Reads`, un commit por tarea con el mensaje del campo `Commit`, tests antes del commit: son las reglas 1, 2, 4 y 5 del `CLAUDE.md` del proyecto, y cada sesión las carga también en el worktree, porque el archivo está versionado.

### Las dos sesiones trabajando

Después de enviarlo, las dos sesiones arrancan. Al final de un turno, en lugar de detenerse con un resumen, Claude sigue: el evaluador ha visto que faltan tareas y lo ha devuelto al trabajo. `/goal` sin argumentos abre el panel con la condición y su estado, que se cierra con `Esc`. `/goal clear` anula el objetivo, si te das cuenta de que la condición estaba mal.

`/goal` se combina con auto mode, el modo de permisos predeterminado (capítulo 11). Auto mode evita las peticiones de permiso dentro del turno, y `/goal` evita que Claude se detenga entre un turno y otro. Juntos te dejan libre para mirar otra cosa durante un rato. Pero si una sesión pide algo que el clasificador no deja pasar, o hace una pregunta de verdad (la regla 1 del `CLAUDE.md` dice que hay que detenerse cuando una tarea es ambigua), se queda esperando hasta que respondas.

Cuando la condición se cumple, la sesión se detiene sola. El trabajo ya tiene su commit en la rama del worktree:

```bash
git log --oneline -4
```

```text
e41c2d7 feat(pipeline): wire UploadPhotosAction to ProcessPhoto
9b07a15 feat(backend): domain events
3fd8c61 feat(pipeline): ProcessPhoto job
a52e0f9 chore(backend): bind service contracts
```

<!-- TODO screenshot: sessione fase6-pipeline con il pannello di /goal aperto e lo stato della condizione -->

::: {.callout .callout-tip}
[Consejo]{.callout-title}

Antes de escribir un `/goal` largo, prueba la comprobación a mano en el worktree: `composer test` en `backend/`, `npm run build` en `frontend/`. Si la suite ya está en rojo al principio (en la rama del capítulo 19 T042 y T043 siguen en `[~]`), la sesión se pasará el tiempo arreglando tests que no tienen nada que ver con su fase. En ese caso, cierra primero T042 y T043 en `main` y luego abre los worktrees.
:::

## 20.5 Cerrar la primera tanda

Cada track termina en un pull request, como en el capítulo 19: un PR por fase. Desde la sesión:

```text
haz push de la rama y abre un pull request contra main con gh, con el título "Phase 6: image processing pipeline" y la lista de tareas cerradas en el cuerpo
```

Después haz a mano las dos tareas de revisión, T080 en el worktree del backend y T062 en el del frontend, y revisa los PRs. Para retomar un PR más adelante sin tocar tu checkout, `claude --worktree "#12"` (con el número de tu PR) abre una sesión en un worktree que parte de ese pull request. La revisión con `/code-review` es el tema del capítulo 22. Cuando los dos estén integrados, actualiza `main` en local:

```bash
git switch main
git pull
```

Si prefieres hacer merge en local sin pasar por GitHub, `worktree.baseRef: "head"` se vuelve necesario: las sesiones de la segunda tanda tienen que ver la pipeline aunque no hayas hecho push.

## 20.6 Todo desde una pantalla con agent view

Dos terminales se manejan bien. Con cuatro o cinco sesiones se vuelve incómodo, y la segunda tanda tiene por lo menos dos: la Fase 3 (admin con Filament, ahora que `ProcessPhoto` existe) y la Fase 5 (componentes React).

### Sesiones en segundo plano

`claude --bg` arranca una sesión directamente en segundo plano, con un nombre y un prompt. No hace falta crear el worktree a mano: antes de modificar archivos, una sesión en segundo plano se mueve sola a un worktree aislado dentro de `.claude/worktrees/`. `.worktreeinclude` vale para todos los worktrees que Claude Code crea con git, así que aquí también `backend/.env` llega solo.

```bash
claude --bg --name fase3-admin '/goal las tareas de T046 a T053 tienen Status [x] en docs/TASKS.md (muéstrame las líneas Status), "composer test" en la carpeta backend termina con código 0 y cada tarea tiene su commit'
claude --bg --name fase5-componenti '/goal las tareas de T063 a T070 tienen Status [x] en docs/TASKS.md (muéstrame las líneas Status), "npx vitest run" y "npm run build" en la carpeta frontend terminan con código 0 y cada tarea tiene su commit'
```

Las comillas simples hacen falta porque la condición contiene comillas dobles. Para la Fase 5 la comprobación es `npx vitest run` y no `npm test`: Vitest está entre las dependencias, pero no es seguro que a estas alturas exista un script `test`, y `vitest` sin `run` se quedaría vigilando los cambios. También aquí T054 y T071, las revisiones de fase, te tocan a ti. Cada sesión parte de un worktree sin `vendor/` ni `node_modules/` y los instala sola antes de ejecutar los tests.

También puedes mandar a segundo plano una sesión que ya tienes abierta. `/background` (alias `/bg`) separa la sesión actual, y `/fork` (capítulo 15) copia su conversación en una nueva sesión en segundo plano mientras tú sigues en la actual.

### Agent view

```bash
claude agents
```

La agent view muestra todas las sesiones en segundo plano en una pantalla, agrupadas por estado: Working, Needs input, Completed. Las que te necesitan están arriba. Cada fila tiene el nombre, un resumen de lo que está haciendo y cuánto tiempo lleva en marcha.

Las teclas que vas a usar:

| Tecla | Qué hace |
| --- | --- |
| `Space` | Vista previa de la fila seleccionada: el último mensaje o la pregunta pendiente. Puedes responder desde ahí sin entrar |
| `Enter` | Entra en la sesión completa |
| `←` con el prompt vacío | Vuelve a la lista. Desde cualquier sesión abierta, manda la sesión a segundo plano y abre la agent view |
| `Ctrl+T` | Fija arriba la sesión seleccionada |

En nuestro caso la sesión que hay que vigilar es `fase3-admin`: T046 lanza `php artisan filament:install --panels`, un instalador que hace preguntas, y ahí es donde la sesión tiene más riesgo de quedarse parada. Fíjala con `Ctrl+T`. Si a mitad del trabajo pregunta si puede añadir un paquete a `composer.json`, la ves pasar a Needs input, respondes desde la vista previa con `Space` y vuelves a la lista.

Las sesiones siguen funcionando aunque cierres el terminal. Desde la shell las gestionas por id:

```bash
claude attach <id>    # vuelve a abrir la sesión en este terminal
claude logs <id>      # muestra la salida sin entrar
claude stop <id>      # detiene la sesión
claude rm <id>        # la quita de la lista
```

<!-- TODO screenshot: agent view con fase3-admin fissata in alto (Working) e fase5-componenti, anteprima aperta con Space -->

### Cuando una sesión termina

Una sesión en segundo plano que ha terminado guarda su trabajo: hace commit, hace push de la rama si el repo tiene un remote y, cuando la tarea lo pide, abre un pull request en borrador. El número del PR aparece en la fila como una etiqueta `#N`, con un color según el estado: amarilla mientras espera los checks o la revisión, verde cuando está listo, morada cuando está integrado. En la Photogallery, con la CI de GitHub Actions configurada en el capítulo 19, la etiqueta sigue amarilla hasta que pasan los jobs de backend y frontend.

<!-- TODO screenshot: riga completata nell'agent view con l'etichetta #N della PR -->

## 20.7 Un subagente con su propio worktree

Si prefieres quedarte en una sola sesión, puedes darles el worktree a los subagentes. La Fase 5 es el caso que mejor encaja: `docs/TASKS.md` la define como "heavily parallelizable" y, una vez completada T063, las tareas T064, T065 y T066 dependen solo de cosas que ya están en `main`. Es la alternativa a la sesión `fase5-componenti` de la sección anterior: elige uno de los dos caminos, no los dos.

El asistente de `/agents` ya no existe, así que el subagente se crea escribiendo el archivo `.claude/agents/task-executor.md` (o pidiéndole a Claude que lo escriba):

```markdown
---
name: task-executor
description: Ejecuta una sola tarea de docs/TASKS.md en un worktree aislado, con tests y commit. Úsalo para las tareas independientes de una wave.
isolation: worktree
---

Recibes el ID de una tarea de docs/TASKS.md.

1. Lee la tarea y las secciones de docs/DESIGN.md indicadas en Reads.
2. Implementa solo esa tarea, respetando DESIGN.md y los criterios de Acceptance.
3. Instala las dependencias si faltan. Escribe o actualiza los tests y ejecútalos
   hasta que pasen: "composer test" en backend, "npx vitest run" en frontend.
4. Marca el Status de la tarea y haz commit en el mismo commit, con el mensaje
   indicado en el campo Commit.
5. Si la tarea requiere modificar composer.json o package.json, detente e
   infórmalo en lugar de seguir.
6. Informa de: archivos modificados, resultado de los tests, nombre de la rama.
```

`isolation: worktree` da a cada instancia un worktree temporal, que Claude Code elimina si la instancia no ha modificado nada. El punto 5 sale de la lista de archivos imán: tres instancias que añaden paquetes en paralelo producen tres `package-lock.json` distintos que hay que conciliar.

En una sesión normal en la raíz del repo:

```text
usa task-executor en paralelo sobre las tareas T064, T065 y T066
```

Los subagentes se ejecutan en segundo plano por defecto: la sesión principal muestra que está esperando a los agentes en curso, `/tasks` los enumera y tú puedes seguir escribiendo. Cada instancia trabaja en su copia y ninguna ve los cambios a medias de las demás. Si desde otro terminal lanzas `git worktree list` mientras trabajan, verás aparecer un worktree por instancia, cada uno en su rama. Cuando terminan, las copias sin cambios desaparecen solas y las que tienen commits se quedan, con su rama, listas para el merge. En ese momento le pides a la sesión principal que las integre en `main` y que vuelva a lanzar `npx vitest run`, y luego pasas a T067, que depende de T066.

Un detalle sobre el punto de partida: el worktree de un subagente sigue la misma regla que `--worktree`. Parte de la rama principal del remote, o de tu `HEAD` local si configuraste `worktree.baseRef: "head"` como en la sección 20.2. En los dos casos T063 tiene que estar ya ahí: si la hiciste en otro worktree y todavía no la has integrado, los tres subagentes no encuentran `ErrorBoundary` ni `Modal`.

## 20.8 Integrar y hacer limpieza

Cuando los PRs de la segunda tanda están listos, los revisas y los integras como los de la primera. El merge de `docs/TASKS.md` es el punto donde un conflicto es más probable, porque todas las sesiones lo han modificado. Las líneas están en secciones distintas, así que normalmente Git las une solo. Si no lo consigue, el conflicto afecta solo a casillas `[ ]` y `[x]` y se resuelve quedándote con las `[x]`.

Luego toca limpiar. Primero mira qué ha quedado:

```bash
git worktree list
```

Cuando sales de una sesión iniciada con `--worktree`, Claude Code te pregunta si quieres conservar o eliminar el worktree, si contiene trabajo. Para las sesiones en segundo plano, `claude rm <id>` quita la sesión de la lista junto con su worktree, cuando es seguro hacerlo. Lo que quede lo quitas con Git:

```bash
git worktree remove .claude/worktrees/fase6-pipeline
git branch -d worktree-fase6-pipeline
```

`git worktree remove` se niega a borrar un worktree con cambios sin commit, y `git branch -d` se niega a borrar una rama sin integrar. Si alguno de los dos protesta, mira antes de añadir `--force`: normalmente hay un commit que no llegó a `main`.

### Cuánto cuesta

Cada sesión consume la cuota de tu plan como una sesión normal, y lo mismo vale para cada instancia de subagente. Cuatro sesiones de Opus en paralelo consumen unas cuatro veces más rápido que una, y la Wave 1 de la Photogallery no es un trabajo de cinco minutos. `/usage` muestra qué está consumiendo los límites, con el detalle por subagente. Usa el paralelo para tracks que de verdad no se tocan, como la Fase 4 y la Fase 6, y deja el resto en secuencia: la Wave 3 de `docs/TASKS.md` (Fases 12 y 13) está declarada secuencial precisamente porque cada paso depende del anterior.

## 20.9 Comandos de referencia

| Comando | Para qué sirve |
| --- | --- |
| `claude --worktree <nombre>` | Sesión en un worktree aislado en `.claude/worktrees/<nombre>`, rama `worktree-<nombre>` |
| `claude --worktree "#123"` | Worktree que parte de un pull request |
| `.worktreeinclude` | Archivos ignorados por Git que se copian en cada worktree nuevo |
| `{"worktree": {"baseRef": "head"}}` | Los worktrees parten del `HEAD` local en lugar del `main` remoto |
| `/goal <condición>`, `/goal`, `/goal clear` | Fija, muestra, anula el objetivo |
| `claude --bg --name <nombre> "<prompt>"` | Sesión en segundo plano |
| `/background` (`/bg`), `/fork` | Separa la sesión actual, copia la conversación en segundo plano |
| `claude agents` | Agent view |
| `claude attach`, `logs`, `stop`, `rm <id>` | Gestionar las sesiones en segundo plano desde la shell |
| `isolation: worktree` | En el frontmatter de un subagente: un worktree temporal por instancia |
| `git worktree list`, `git worktree remove <ruta>` | Ver y eliminar los worktrees |

## Resumen {.unlisted}

- Un subagente aísla el contexto, un worktree aísla archivos y rama, una sesión en segundo plano libera el terminal. Para tareas que escriben código en paralelo necesitas el worktree.
- Antes de paralelizar, lee las dependencias y los criterios de aceptación de las tareas: T048 depende de `ProcessPhoto` aunque su `Depends on` no lo diga.
- `.claude/worktrees/` va en el `.gitignore`, `.worktreeinclude` copia `backend/.env` y `worktree.baseRef: "head"` hace falta cuando haces merge en local sin hacer push.
- Una condición de `/goal` solo funciona si nombra una comprobación que Claude ejecuta y muestra: `composer test` termina con código 0, las líneas Status, el `git log`.
- `claude --bg` y `claude agents` te permiten seguir varias sesiones desde una pantalla. Cada sesión consume cuota como una normal.

## Ejercicio {.unlisted}

Parte de la rama `book/cap-13-wave-2-api` del companion repo y haz la primera tanda de este capítulo con las dos herramientas distintas: haz commit de `.gitignore`, `.worktreeinclude` y `baseRef`, arranca el Track A con `claude --worktree fase6-pipeline` y el `/goal` de la sección 20.4, y lanza el Track C como sesión en segundo plano con `claude --bg --name fase4-frontend` y su `/goal`. Sigue la segunda desde la agent view hasta que llegue a Completed.

El ejercicio está terminado cuando `git log --oneline` en la rama de la pipeline muestra un commit para cada una de las tareas T029, T032, T035 y de T072 a T079, `composer test` pasa en ese worktree, `npm run build` y `npm run lint` pasan en la rama del frontend y, después del merge y la limpieza, `git worktree list` muestra solo la carpeta principal.
