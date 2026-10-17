# Apéndice B. Solución de problemas

Estos son los problemas que me encontré al escribir el libro y grabar el curso, agrupados por área. Cada entrada parte de lo que ves en pantalla, explica de dónde viene y da la solución, con la referencia al capítulo que lo trata. Cuando le pidas ayuda a Claude con un error, pega la salida exacta: "el deploy no funciona" te da hipótesis; las diez líneas del error, un diagnóstico.

## B.1 Lo primero: claude doctor y /doctor

```bash
claude --version
claude doctor
```

`claude doctor` se ejecuta desde la shell sin abrir una sesión: revisa la instalación y los archivos de configuración (un `settings.json` con el JSON roto aparece aquí) y sugiere las correcciones, sin modificar nada. Dentro de una sesión, `/doctor` (alias `/checkup`) hace una revisión más amplia y puede corregir por su cuenta; `/doctor prompt-audit` busca en las instrucciones archivos que ya no existen y reglas en conflicto, y propone cambios sin aplicarlos (capítulo 15). Si todo sale limpio, mira el panel adecuado:

| Lo que necesitas saber | Dónde mirar |
| --- | --- |
| Cuenta y método de autenticación activos | `/status` |
| Por qué un comando pasa o se bloquea | `/permissions` |
| Hooks registrados y sus matchers | `/hooks` |
| Estado de los servidores MCP | `/mcp`, `claude mcp list` |
| Archivos de instrucciones cargados | `/memory` |
| Qué ocupa el contexto | `/context` |
| Qué consume los límites del plan | `/usage` |
| Plugins instalados y skills disponibles | `/plugin`, `/skills` |
| Trabajos y sesiones en segundo plano | `/tasks`, `claude agents` |

## B.2 Instalación y actualizaciones

### `claude: command not found` justo después de instalar

Casi siempre basta con abrir una terminal nueva, para que la shell vuelva a leer el `PATH`. Si no, la carpeta del binario, `~/.local/bin` en macOS y Linux, no está en el `PATH`:


```bash
echo $PATH | tr ':' '\n' | grep local
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
```

Con bash usa `~/.bashrc` y luego vuelve a abrir la terminal (capítulo 1).

### El `claude` que arranca no es el que instalaste

Instalaste primero con npm y después con el instalador nativo: gana el primer binario del `PATH` (`which -a claude` los lista). Quita la copia de npm con `npm uninstall -g @anthropic-ai/claude-code`.

### `EACCES: permission denied` con npm, o archivos de root en `~/.claude`

npm intenta escribir en una carpeta del sistema: usa el instalador nativo, que no pide permisos de administrador. Si una instalación antigua con `sudo` dejó archivos de root en `~/.claude`, recupéralos:

```bash
sudo chown -R "$(whoami)" ~/.claude
```

::: {.callout .callout-warning}
[Atención]{.callout-title}

No uses nunca `sudo npm install -g`: crea archivos de root que bloquean las actualizaciones posteriores.
:::

### `EBADENGINE` durante `npm install -g`, o npm no actualiza

El paquete requiere Node.js 22 o posterior, y con un Node más antiguo npm avisa y sigue adelante: comprueba `node --version`. Para actualizar usa `npm install -g @anthropic-ai/claude-code@latest`, no `npm update -g`.

### Windows: `The token '&&' is not a valid statement separator` o `'irm' is not recognized`

Shell equivocada: el primer error es PowerShell con el comando para CMD, el segundo es al revés. En PowerShell el comando es `irm https://claude.ai/install.ps1 | iex`.

### Windows: los scripts `.sh` no arrancan o Claude no encuentra Git Bash

Sin Git for Windows, Claude Code usa PowerShell, donde un script `.sh` no se ejecuta. Instálalo; si aun así no encuentra Git Bash, indica la ruta en `%USERPROFILE%\.claude\settings.json`:

```json
{
  "env": {
    "CLAUDE_CODE_GIT_BASH_PATH": "C:\\Program Files\\Git\\bin\\bash.exe"
  }
}
```

### La versión es antigua, o la última trae una regresión

El instalador nativo se actualiza solo en el siguiente arranque; `claude update` actualiza al momento. Homebrew y WinGet hay que actualizarlos a mano (`brew upgrade claude-code`, `winget upgrade Anthropic.ClaudeCode`). Si una regresión te sale cara, elige el canal `stable` en `/config`: llega una semana más tarde, más o menos, y se salta las versiones con problemas graves.

## B.3 Autenticación y cuenta

### Pagas por consumo aunque tienes una suscripción

En la shell hay una `ANTHROPIC_API_KEY`, quizá exportada en el `.zshrc` para otro proyecto, y la aprobaste en el primer arranque: la clave gana sobre la suscripción, y en `claude -p` se usa siempre. `/status` muestra el método activo. Quita la variable y reinicia:

```bash
unset ANTHROPIC_API_KEY
claude
```

### El login no arranca, o estás en la cuenta equivocada

Si el navegador no se abre, copia la URL desde la terminal, completa el login a mano y pega el código. Para cambiar de cuenta, `/logout` y luego `/login`; desde la shell, `claude auth status` te dice con qué cuenta estás conectado. El plan gratuito de claude.ai no incluye Claude Code (capítulo 1). Para la CI, `claude setup-token` genera un token para guardar en los secretos de la pipeline.

### Errores de conexión con la VPN o el proxy de la empresa

Prueba la red fuera de Claude Code:

```bash
curl -I https://api.anthropic.com
```

Si falla, el problema es la VPN, el firewall o el proxy: define `HTTPS_PROXY` (por ejemplo `http://proxy.azienda.it:8080`, y si hace falta `NO_PROXY`) antes de arrancar `claude`; si el proxy inspecciona el TLS con una CA corporativa, apunta `NODE_EXTRA_CA_CERTS` a su certificado. Los proxies SOCKS no están soportados. Con `/status` compruebas que se haya leído el proxy. Si la red funciona, mira `status.anthropic.com`.


## B.4 Permisos y auto mode

### Claude casi nunca pide confirmación

La configuración está bien: desde la 2.1.283 las sesiones interactivas arrancan en auto mode, y el clasificador aprueba por ti. Para ver cada paso usa `claude --permission-mode manual`, o `"defaultMode": "default"` dentro de `permissions` en `~/.claude/settings.json` (capítulo 2). En algunas configuraciones de Windows `Shift+Tab` no cambia de modo: prueba con `Alt+M`.

### `"defaultMode": "auto"` en el archivo del proyecto no tiene efecto

Es intencionado: como `defaultMode`, `auto` y `bypassPermissions` solo valen en `~/.claude/settings.json`; si no, un repositorio clonado podría quitarse los controles él solo (capítulo 11).

### Una regla deny no para el comando que creías haber bloqueado

Una regla sobre `Bash` compara el texto: `Bash(curl *)` bloquea `curl https://...`, pero no `wget` ni un script de Python que descarga. También cuenta el espacio antes del asterisco: `Bash(ls *)` no afecta a `lsof`. En `/permissions` seleccionas la regla y ves de qué archivo viene; las reglas se suman y el orden es deny, ask, allow. Para un límite de verdad hace falta el sandbox o un hook (capítulos 11 y 12).

### Auto mode hace cosas que no esperas

Recently denied está vacía aunque Claude haya sido bloqueado: solo recoge las decisiones del clasificador, y tus reglas deny actúan antes. Auto mode vuelve a pedir confirmación a mitad del trabajo: después de tres bloqueos seguidos, o veinte en la sesión, se pone en pausa, y normalmente significa que Claude ha entendido mal la tarea. Una regla allow sobre `python` desaparece de `/permissions`: auto mode aparca las reglas allow demasiado amplias sobre intérpretes, que se saltarían el clasificador; en Manual vuelve a estar activa.

### Después de un bloqueo, Claude te propone `! cat .env`

El prefijo `!` ejecuta el comando en tu nombre, y las reglas deny limitan a Claude, no a ti; luego la salida entra en la conversación, secreto incluido. Si la regla está mal, cámbiala; si no, recházalo.

## B.5 Sandbox

### `/sandbox` no aísla nada, o no está disponible

El sandbox funciona en macOS, Linux y WSL 2. En Windows nativo y en WSL 1 no está soportado, y los comandos se ejecutan sin límite aunque pongas `"enabled": true`. En Linux y WSL 2 hacen falta dos paquetes:

```bash
sudo apt-get install bubblewrap socat
```

### `Operation not permitted`, `Read-only file system` o `Could not resolve host`

Es el sandbox haciendo su trabajo: el comando intentó escribir fuera de la carpeta o salir a la red sin pasar por el proxy. Si la escritura es necesaria, añade la carpeta a `filesystem.allowWrite`; un dominio que usas a menudo va en `network.allowedDomains`. Si no quieres que Claude proponga reintentar fuera del sandbox, define `"allowUnsandboxedCommands": false` (capítulos 2 y 11).

### pytest se para con un `PermissionError` en `.env`

Con el sandbox activo, las reglas deny sobre `Read`, como `Read(./.env)`, valen también para los procesos que se lanzan: pytest recorre la carpeta y choca con el archivo. En el laboratorio lo resolvió el `pytest.ini` de la sección 11.1, sin quitar la regla.

### `docker` no funciona dentro del sandbox

Puedes excluirlo del sandbox con `sandbox.excludedCommands`, sabiendo que a partir de ese momento se ejecuta con todos tus permisos. Para aislar todo Claude Code, hooks y servidores MCP incluidos, hace falta un dev container o una VM (capítulo 2).


## B.6 Hooks

La tabla del capítulo 12, ampliada:

| Síntoma | Causa y solución |
| --- | --- |
| El hook no se dispara | Revisa evento y matcher con `/hooks`: el matcher distingue mayúsculas y minúsculas, así que `"edit"` no coincide con nada. Los hooks se leen al arrancar: reinicia Claude Code después de cada cambio en `settings.json` |
| El script no arranca | Le falta el permiso de ejecución: `chmod +x .claude/hooks/nombre.sh` |
| `jq: command not found` | Instala `jq` (`brew install jq`, `sudo apt-get install jq`) o reescribe el script en Python |
| El JSON que imprime el hook se ignora | Un `echo` en el perfil de la shell ensucia stdout: muévelo dentro de `if [[ $- == *i* ]]` |
| Claude no se detiene nunca | El Stop hook no comprueba `stop_hook_active` |
| El Stop hook no bloquea con una suite larga | El hook llegó al timeout (por defecto, 600 segundos), y un hook interrumpido no bloquea: sube `timeout` (en segundos) |
| El `PostToolUse` no impide la modificación | No puede: el tool ya actuó. Para bloquear usa `PreToolUse` |
| En Windows el script `.sh` no se ejecuta | Claude Code está usando PowerShell: instala Git for Windows o define `CLAUDE_CODE_GIT_BASH_PATH` |


Prueba el script a mano con un JSON de ejemplo: si falla aquí, `settings.json` no tiene nada que ver. `CLAUDE_PROJECT_DIR` se lo pasas tú:

```bash
echo '{"tool_input":{"file_path":"data/vendite.csv"}}' | .claude/hooks/protect-files.sh; echo "exit: $?"
echo '{"stop_hook_active": false}' | CLAUDE_PROJECT_DIR="$PWD" .claude/hooks/tests-before-stop.sh
```

### El hook de protección está, pero el archivo cambió igualmente

Un matcher `Edit|Write` solo ve esos dos tools. Un `echo ... >> data/vendite.csv` desde `Bash`, o un `UPDATE` a través de un servidor MCP, entran por otro lado. Para los archivos, añade `filesystem.denyWrite` en el sandbox; para una base de datos, un usuario de solo lectura o un hook con matcher `mcp__db__.*` (capítulos 12 y 13).

## B.7 MCP

### El servidor que acabas de añadir aparece con error

`claude mcp add` guarda sin verificar: un token incorrecto o caducado solo falla al conectar, así que el primer sospechoso es la credencial. Compruébalo con `claude mcp list` y `/mcp`, desde donde puedes reconectar. Un servidor OAuth que aparece como pendiente de autenticar necesita el login, desde `/mcp` o con `claude mcp login <nombre>`. Cuidado con `claude mcp get`: imprime el token en claro.

### DBHub: `unable to open database file`

El DSN de SQLite necesita una ruta absoluta; con DBHub 1.5.0 funciona `sqlite://` seguido de la ruta absoluta (que empieza a su vez por `/`):

```bash
claude mcp add --transport stdio db -- npx -y @bytebase/dbhub \
  --dsn "sqlite://$(pwd)/data/vendite.db"
```


En Windows nativo, un servidor que se arranca con `npx` necesita el envoltorio `cmd /c`: `... -- cmd /c npx -y @bytebase/dbhub ...`.

### El servidor de `.mcp.json` no aparece

Los servidores de proyecto hay que aprobarlos en el primer arranque. Si dijiste que no con prisas, reinicia las elecciones y vuelve a arrancar:

```bash
claude mcp reset-project-choices
```

Si Claude Code no consigue leer la configuración, en `.mcp.json` hay un `${VAR}` sin valor ni default. Si el header llega vacío con la variable definida, es una de las que nunca se expanden hacia un servidor remoto (las credenciales de Claude Code y de los proveedores cloud): usa un nombre propio, como `GITHUB_MCP_PAT` (capítulo 13).

### Claude usa `sqlite3` desde `Bash` en lugar del servidor

Si el prompt no lo dice, Claude elige el camino que prefiere: escribe "usando el servidor db".

### En `/mcp` aparecen Gmail o Drive y no los añadiste

Son los conectores de tu cuenta de claude.ai. Donde no los quieras, arranca con `ENABLE_CLAUDEAI_MCP_SERVERS=false claude`.

## B.8 Plugins, skills y agentes

### El plugin se carga pero no tiene skills ni agentes

Los componentes acabaron dentro de `.claude-plugin/`, donde solo va `plugin.json`: `skills/`, `agents/` y `hooks/` van en la raíz del plugin. Después, `claude plugin validate ./nombre-plugin` (capítulo 14).

### Los cambios en el plugin no se ven, o el hook del plugin no encuentra el script

Con la sesión abierta usa `/reload-plugins`, y vuelve a lanzar los subagentes que ya estuvieran en marcha. En los hooks de un plugin la ruta parte de `"${CLAUDE_PLUGIN_ROOT}"`, no de `$CLAUDE_PROJECT_DIR`. Si el formatter se ejecuta dos veces, el hook se quedó también en el `settings.json` del proyecto.

### Tus compañeros no reciben la actualización del plugin

Cambiaste los archivos pero no `version` en `plugin.json`: sube la versión en el mismo commit. Para obtener la versión nueva al momento:

```bash
claude plugin marketplace update cc-corso
claude plugin update cc-lab-toolkit@cc-corso
```

### `claude plugin eval` no arranca, o el delta es cero

Hace falta Git 2.31 o posterior. Con `--no-publish` el informe no se sube a claude.ai. Un `Δ` cercano a cero suele significar que la skill no se activó: el problema está en la description.

### La skill no se activa cuando lo esperas

Claude elige la skill a partir de la description, que hay que escribir como un trigger: cuándo usarla, con las palabras de quien la pide. "Skill para análisis de datos" casi nunca se activa. Después de ampliarla, un caso negativo te dice si también se activa donde no debe (capítulos 9 y 14).

### La skill o el comando personalizado no aparece en el menú

Revisa la ruta (`.claude/skills/<nombre>/SKILL.md` o `.claude/commands/<nombre>.md`), el nombre `SKILL.md` y el frontmatter YAML, porque un error de sintaxis puede silenciar la skill. Después, `/reload-skills` y `/skills`. Si los nombres coinciden, gana la skill; las de los plugins llevan prefijo (`/superpowers:<nombre>`), y después de instalar hace falta `/reload-plugins`.

### `/agents` ya no abre el asistente

El asistente se eliminó en julio de 2026: pídele el subagente a Claude o escribe tú `.claude/agents/<nombre>.md` (capítulo 10).

### El subagente devuelve un muro de texto, o no termina nunca

En el cuerpo del agente falta el formato de la respuesta: pide una estructura y un límite de longitud. Para un agente que lleva demasiado tiempo en marcha, `/tasks` muestra lo que hace y `Ctrl+X Ctrl+K` detiene los subagentes en segundo plano; después divide la tarea en partes verificables.

## B.9 Contexto y memoria

### Claude olvida las decisiones tomadas al principio

En `/context`, los mensajes se han convertido en la partida más grande. Compacta con instrucciones (`/compact conserva las decisiones sobre el formato y los archivos modificados`) o escribe el estado en un archivo y empieza de nuevo:

```text
escribe en STATE.md lo que hemos hecho, las decisiones que tomamos y lo que queda por hacer
```

Después, `/clear` y un prompt que diga que lea `STATE.md`. Para las reglas que tienen que volver después de cada compactación está el hook `SessionStart` con matcher `compact` (capítulos 12 y 15).

### Las respuestas se vuelven lentas y los límites del plan se acaban rápido

`/usage` muestra qué los consume (`/cost` y `/stats` son alias suyos). Suele ser una sesión larga sobre temas distintos, un effort alto para trabajos triviales o demasiadas sesiones en paralelo. Una tarea, una sesión, y `low` o `medium` para los cambios pequeños.

### `CLAUDE.md` parece ignorado

`/memory` muestra los archivos de instrucciones cargados. Si el tuyo no está, revisa el nombre y la ubicación (`./CLAUDE.md` o `./.claude/CLAUDE.md` en la carpeta desde la que lanzas `claude`); `AGENTS.md` solo se lee si falta `CLAUDE.md`, y las reglas con `paths:` solo entran cuando Claude toca un archivo que coincide. Si está pero no se respeta, es largo o vago: por debajo de las doscientas líneas, instrucciones verificables, y `/doctor prompt-audit` para los conflictos. Una prohibición de verdad va en una regla o en un hook (capítulos 7 y 15).

### La memoria automática anotó algo incorrecto, o `#` ya no guarda nada

Son archivos Markdown en `~/.claude/projects/<proyecto>/memory/`: corrígelos a mano. `MEMORY.md` se carga hasta doscientas líneas, y desde `/memory` puedes desactivar la función. El atajo `#` se eliminó: pídele a Claude que modifique `CLAUDE.md`, o usa `/memory`.

### `/rewind` no lo deshizo todo

Los checkpoints siguen a `Edit` y `Write`. Los cambios de un comando `Bash` (un `rm`, una migración) y las correcciones de `/code-review --fix` se quedan: haz commit antes de un trabajo grande.

## B.10 Worktrees y sesiones en segundo plano

### En el worktree los tests fallan por una clave que falta

Un worktree es un checkout limpio, sin los archivos ignorados como `backend/.env`. Lístalos en `.worktreeinclude` en la raíz y Claude Code los copia; `vendor/` y `node_modules/` se reinstalan. Añade también `.claude/worktrees/` al `.gitignore` (capítulo 20).

### Las sesiones nuevas no ven lo que hiciste merge en local

Un worktree parte del main remoto. Haz push, o añade `{"worktree": {"baseRef": "head"}}` a `.claude/settings.json`. Tampoco un subagente con `isolation: worktree` encuentra los archivos de una tarea que todavía no se ha integrado.

### Sail en dos worktrees: puertos ocupados

Los contenedores se pelean por los puertos 80, 3306 y 6379 y por el nombre de proyecto de Compose. Mantén la aplicación encendida en un solo worktree a la vez, o cambia `APP_PORT` y `FORWARD_DB_PORT` en el `.env` de uno de los dos.

### `/goal` no termina nunca, o termina demasiado pronto

El evaluador solo ve la conversación: "la pipeline funciona" no se puede verificar; "`composer test` termina con código 0, muéstrame las líneas Status con grep", sí. `/goal clear` y reescríbela. Y prueba antes la comprobación a mano: con la suite ya en rojo, la sesión acaba trabajando en tests que no tienen nada que ver.

### Una sesión en segundo plano está parada

Abre `claude agents`: si está en Needs input te está esperando, a menudo por un instalador interactivo o un permiso que el clasificador no dejó pasar. Responde desde la vista previa con `Space`; `claude logs <id>` muestra la salida sin entrar.

### `git worktree remove` o `git branch -d` se niegan

El worktree tiene cambios sin commit, o la rama no está mergeada: mira qué falta antes de recurrir a `--force`.

## B.11 Proyectos: Python y Excel

| Síntoma | Causa y solución |
| --- | --- |
| `externally-managed-environment` en `pip install` | Python de Homebrew o de una distribución reciente: `python3 -m venv .venv` y actívalo |
| `No module named pytest` incluso después de instalarlo | `claude` arrancó desde una shell sin el virtualenv: `source .venv/bin/activate` y luego `claude` |
| `ModuleNotFoundError: No module named 'src'` | Falta el `pytest.ini` con `pythonpath = .` (capítulo 2) |
| En Excel las fechas no se filtran y se ordenan al azar | pandas las leyó como texto: pide `parse_dates` (capítulo 5) |
| El total no cambia cuando corriges la hoja Dati | Las fórmulas suman valores que Python escribió en Riepilogo: hacen falta fórmulas que lean la hoja Dati (sección 5.4) |
| El script funciona a mano pero no desde cron | cron arranca desde el home y no carga el perfil: `cd` a la carpeta del proyecto, el Python del virtualenv, las variables desde un `.env` y la salida a un archivo de log |
| Flask no arranca o el navegador responde 403 en macOS | El puerto 5000 es del receptor AirPlay: desactívalo o usa `app.run(debug=True, port=5001)` |
| La portada del PDF sale en blanco | El fondo hay que dibujarlo en `onFirstPage`, no añadirlo a la `story` |
| ReportLab se para en `doc.build` | La `story` contiene una lista dentro de otra: expande las secciones con `*` |
| Un CSV enorme llena el contexto | Pide un script que lo lea por bloques (`chunksize`, `usecols`) y que traiga al chat solo los resultados (capítulo 4) |

## B.12 Proyectos: Laravel y React

### El frontend llama al puerto de Vite en lugar de a la API

La URL del backend está escrita a fuego en el cliente axios. Léela de una variable, con `baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api/v1'` (capítulo 19).

### Error de CORS en el navegador

`FRONTEND_URL` en el `.env` del backend dice `localhost:5173`, pero Vite corre en otro puerto porque el 5173 estaba ocupado. Ajusta la variable, que alimenta `config/cors.php` (Laravel 13 no publica ese archivo: sin él, se acepta cualquier origen).

### Un error de la API llega como página HTML

El cliente no envió `Accept: application/json`. El middleware `ForceJsonResponse` va en el grupo `api` con `prepend`, así también el 401 de `auth:sanctum` sale en JSON.

### `createToken()` falla con una violación NOT NULL

La clave primaria de `personal_access_tokens` se convirtió en UUID. Sanctum espera un autoincremental: vuelve a `$table->id()` y cambia solo `tokenable_id`.

### Tests en verde con SQLite, errores con MariaDB

SQLite es más permisivo con las restricciones y las fechas: ejecuta los tests también con Sail (`vendor/bin/sail up -d`, `vendor/bin/sail test`).

### `403 Forbidden` en las variantes de las fotos

Un disco `local` con `'serve' => true` registra una ruta que intercepta las peticiones antes que el archivo estático. Deja `serve` solo en el disco público de las variantes (capítulo 21).

### El job falla buscando una foto que no existe

El dispatch ocurre dentro de `DB::transaction()` y el worker toma el job antes del commit. Devuelve los jobs desde la closure y ponlos en la cola después.

### En S3 las fotos salen sin EXIF, o el driver `s3` no se entiende con MinIO

`Storage::disk(...)->path()` sobre un disco `s3` devuelve la clave del objeto, que `exif_read_data` no puede abrir: lee el EXIF del archivo temporal en el momento de la subida. Para MinIO, la entrada `s3` de `config/filesystems.php` tiene que leer `AWS_ENDPOINT` y `AWS_USE_PATH_STYLE_ENDPOINT`.

### Detrás del balanceador de carga, el rate limit bloquea a todos a la vez

Sin `trustProxies`, `$request->ip()` es la dirección del proxy y el límite por IP se convierte en un único cubo compartido. Lee `TRUSTED_PROXIES` desde el `.env`.

## B.13 Proyectos: Firebase

### `firebase: command not found`, o el deploy va al proyecto equivocado

Instala la CLI con `npm install -g firebase-tools`, o usa `npx firebase-tools` en lugar de `firebase`. Después, `firebase login` y `firebase projects:list`; el proyecto de la carpeta está en `.firebaserc`.

### El sitio publicado está vacío o es la versión antigua

`firebase deploy` sube `dist/`: ejecuta antes `npm run build` y comprueba que `public` en `firebase.json` sea `dist` (`out/` con Next.js en export estático).

### Al recargar una página interna sale un 404

Falta la reescritura a `index.html`: responde que sí a "Single-page app" en `firebase init hosting`, o añade a `firebase.json` `"rewrites": [{ "source": "**", "destination": "/index.html" }]`.

### El dominio personalizado no responde, o el deploy rompió algo

La propagación DNS puede tardar un día; mientras tanto tienes `.web.app`. Una versión anterior la restauras desde la consola de Hosting.

## B.14 Proyectos: AWS

### El stack termina en `ROLLBACK_COMPLETE`

Los eventos dicen qué recurso falló y por qué, en el campo `ResourceStatusReason`:

```bash
aws cloudformation describe-stack-events \
  --stack-name photogallery-staging \
  --query "StackEvents[?ResourceStatus=='CREATE_FAILED' || ResourceStatus=='UPDATE_FAILED']" \
  --output table
```

Suelen ser permisos de IAM, límites de la cuenta (Service Quotas), un nombre ya usado (los buckets de S3 son únicos en todo AWS) o una dependencia que hay que declarar con `DependsOn`. Con `InsufficientCapabilities` falta `--capabilities CAPABILITY_NAMED_IAM`. Un stack en `ROLLBACK_COMPLETE` hay que borrarlo con `aws cloudformation delete-stack` antes de volver a intentarlo (capítulo 23).

### La tarea de ECS no arranca o se reinicia en bucle

El motivo y el exit code están en las tareas detenidas, en la consola de ECS o con `aws ecs describe-tasks`.

| Síntoma | Causa y solución |
| --- | --- |
| Exit code 1 al arrancar, `FATAL: missing required env var` en los logs | Falta una variable en la task definition |
| Exit code 137 | Sin memoria, típico del worker con fotos grandes: sube `Memory` |
| `CannotPullContainerError` | La execution role no tiene `ecr:GetAuthorizationToken` y `ecr:BatchGetImage`, las subredes privadas no salen por el NAT o el tag no existe en ECR |
| `exec format error` | Imagen ARM construida en un Mac con Apple Silicon: `docker build --platform linux/amd64` |
| La tarea arranca y el ALB la marca como no sana | `/api/v1/health` responde 503: `"storage": "error"` apunta al bucket, `"queue": "error"` a la base de datos |

### La conexión a la base de datos da timeout

El security group de RDS no acepta el tráfico de las tareas. La regla de entrada en el 3306 tiene que tener un `SourceSecurityGroupId` igual al security group de las tareas de ECS.

### CloudFront responde 502 o 504 en `/api/v1`

Consulta el ALB directamente con `curl -v "https://<ALBDnsName>/api/v1/health"`. Si responde, el problema está en el behavior `/api/*` de CloudFront: el origen, el protocolo y el header `Authorization`, sin el cual Sanctum no ve el token. Si también el ALB da 5xx, mira los logs de CloudWatch.

### Las rutas de la SPA dan 404, o faltan assets después de un deploy

Las rutas necesitan las `CustomErrorResponses` que responden con `index.html` y un 200 a los 403 y 404 del bucket. Los assets que faltan vienen casi siempre de un `sync --delete` que se ejecutó también sobre `assets/`: vuelve a subir la build anterior y sigue el orden de la sección 23.4.

### El change set dice `Replacement: True` en la instancia RDS

Detente: significa una base de datos nueva en lugar de la antigua, y sin snapshot pierdes los datos. Llegas ahí con solo cambiar el nombre de la instancia en la plantilla.

## Si tu problema no está aquí

Abre una issue en el repositorio `claude-code-book-snippets` con la salida de `claude --version`, el sistema operativo, el comando que lanzaste y el error completo. Los informes verificados acaban en el changelog del Apéndice E.
