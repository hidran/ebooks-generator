# Capítulo 11. Permisos, modos y sandbox

::: {.chapter-goals}
[Qué aprenderás]{.callout-title}

- Elegir el modo de permisos adecuado y cambiarlo con `Shift+Tab`.
- Escribir reglas allow, ask y deny en `.claude/settings.json` y saber en qué orden se evalúan.
- Entender qué hace realmente auto mode y dónde se detiene el clasificador.
- Configurar el sandbox en el proyecto y compartirlo con el equipo.

:::

En las tres primeras partes del libro dejaste que Claude Code decidiera por su cuenta cuándo pedirte permiso, y para analizar un CSV o escribir una skill estaba bien. A partir de aquí le das más autonomía: hooks que se ejecutan en cada cambio, servidores MCP que hablan con GitHub y con una base de datos, plugins instalados desde un marketplace, sesiones largas que trabajan mientras tú haces otra cosa. Cuanto más actúa el agente por su cuenta, más necesitas saber con precisión qué puede hacer sin preguntar, qué no debe tocar nunca y qué pasa si un comando hace más de lo que dice su nombre. La Parte IV empieza aquí.

En el Capítulo 2 viste los conceptos: el modelo pide, el harness ejecuta, los permisos deciden si una llamada puede salir y el sandbox limita hasta dónde llega un comando una vez lanzado. También probaste el sandbox con `touch ~/sandbox-probe`. Ahora toca configurarlo. Hay tres capas de control: el modo de permisos fija el comportamiento base, las reglas allow, ask y deny añaden excepciones concretas y el sandbox pone un límite en el propio sistema operativo. Las verás de una en una sobre un proyecto pequeño, para que cada prueba se lea en pocos segundos.

## 11.1 El proyecto de laboratorio

Los capítulos 11-15 usan todos el mismo proyecto, `cc-advanced-lab`, que creaste en el Capítulo 2 para ver el bucle agéntico: un script de Python de seis líneas, un CSV de tres filas y un test. Es diminuto a propósito. La Photogallery queda intacta, y cuando una regla bloquea algo ves enseguida por qué, sin perderte en un código de miles de líneas. También tiene un archivo `.env` con un secreto falso: es el cebo para las reglas de este capítulo y para los hooks del siguiente.

Si ya tienes el laboratorio, devuélvelo al último commit. El ejercicio del Capítulo 2 dejó cambios sin commit en `src/report.py` y `tests/test_report.py`, y el menú de `/sandbox` escribió `.claude/settings.local.json`, que vuelves a generar en la Sección 11.8. La skill `report-pdf` del Capítulo 9, si le hiciste commit, se queda donde está:

```bash
cd ~/cc-advanced-lab
git checkout -- .
rm -f .claude/settings.local.json
```

Si te saltaste el Capítulo 2, créalo desde cero (macOS, Linux o WSL 2):

```bash
mkdir -p ~/cc-advanced-lab/{src,data,tests}
cd ~/cc-advanced-lab
git init
printf "data,vendite\n2026-01,120\n2026-02,95\n2026-03,143\n" > data/vendite.csv
printf "import csv\n\n\ndef totale(path):\n    with open(path) as f:\n        return sum(int(r['vendite']) for r in csv.DictReader(f))\n" > src/report.py
printf "from src.report import totale\n\n\ndef test_totale():\n    assert totale('data/vendite.csv') == 358\n" > tests/test_report.py
touch src/__init__.py
printf "[pytest]\npythonpath = .\n" > pytest.ini
printf "SECRET_KEY=non-committare-questo\n" > .env
printf ".env\n.venv/\n" > .gitignore
git add -A && git commit -m "chore: progetto di laboratorio"
python3 -m venv .venv
source .venv/bin/activate
pip install pytest
```

El `.env` queda fuera de Git gracias al `.gitignore`, como en un proyecto real. Arranca siempre Claude Code desde la shell en la que activaste el virtualenv, así el Python que encuentra en el `PATH` es el que tiene pytest.

Para este capítulo hace falta un retoque en `pytest.ini`. Le dice a pytest que busque los tests solo en `tests/` y que ignore `.env`:

```bash
printf "[pytest]\npythonpath = .\ntestpaths = tests\naddopts = --ignore=.env\n" > pytest.ini
git commit -am "chore: pytest solo su tests/"
```

Sin estas dos líneas, en la Sección 11.8 el sandbox haría fallar la recolección de tests con un `PermissionError`. Allí verás por qué, y es uno de los detalles más instructivos del capítulo. Comprueba que todo funciona antes de abrir Claude Code:

```bash
python -m pytest
```

Tienes que ver `1 passed`: el test comprueba que la suma de las ventas de enero, febrero y marzo es 358.

## 11.2 Los seis modos de permisos

Abre `claude` en la carpeta del laboratorio y mira debajo del prompt: el modo activo siempre aparece ahí. Las sesiones interactivas en la terminal y en VS Code arrancan en auto mode, así que verás `auto mode on`. El cambio llegó en dos fases: desde la versión 2.1.228 (agosto de 2026) para los planes Pro, Max y Team, y desde la 2.1.283 para todos los planes y proveedores. Una sesión no interactiva con `claude -p`, en cambio, sigue arrancando en Manual.

Pulsa `Shift+Tab` y el texto cambia. Con cuatro pulsaciones completas el ciclo:

```text
auto mode on
manual mode on
accept edits on
plan mode on
auto mode on
```

El ciclo incluye cuatro modos. Los otros dos, pensados para cuando nadie está delante de la terminal, quedan fuera.

| Modo | Qué hace sin preguntar | Cuándo usarlo |
| --- | --- | --- |
| Manual (`default`) | Solo lecturas | Código delicado, proyecto que no conoces |
| `acceptEdits` | Lecturas, cambios en archivos, comandos como `mkdir`, `touch`, `mv` y `cp` | Iterar revisando los cambios con `git diff` |
| `plan` | Lecturas, ningún cambio hasta que apruebes el plan | Explorar y diseñar |
| `auto` | Todo, con controles de seguridad en segundo plano | Tareas largas, menos interrupciones |
| `dontAsk` | Lecturas en la carpeta de trabajo, Bash de solo lectura y los tools preaprobados; el resto se deniega | CI y scripts |
| `bypassPermissions` | Todo, sin ningún control | Solo contenedores o VM aisladas |

Manual es el antiguo modo por defecto: en la configuración se llama `default` y en la interfaz, Manual. Pide confirmación para casi todo. Es el comportamiento que viste en los primeros capítulos, antes de que auto mode pasara a ser el valor por defecto, y sigue siendo la opción correcta cuando abres un repositorio que no conoces: cada comando pasa por delante de tus ojos.

Accept edits deja modificar archivos sin preguntar, y también aprueba por su cuenta los comandos que solo tocan archivos y carpetas (`mkdir`, `touch`, `mv`, `cp`), pero te para en los demás. Es cómodo cuando trabajas a pasos cortos y lo revisas todo al final de cada vuelta con `git diff`: los cambios están ahí, en el working tree, y Git te da el deshacer.

Plan ya lo conoces del Capítulo 3: Claude lee, analiza y propone un plan, sin tocar nada hasta que lo apruebes.

Auto deja trabajar a Claude y confía los controles a un segundo modelo, el clasificador, que aprueba las acciones coherentes con tu petición y bloquea las arriesgadas. Le dedico la Sección 11.7, porque su comportamiento real tiene algún matiz que conviene conocer antes de fiarse.

Fuera del ciclo están `dontAsk` y `bypassPermissions`. El primero deja pasar las lecturas en la carpeta de trabajo, los comandos Bash de solo lectura y los tools que preaprobaste con reglas allow, y deniega todo aquello para lo que, de otro modo, te pediría confirmación: es el que quieres en un pipeline de CI, donde nadie respondería a una pregunta. El segundo se salta todos los controles, y equivale al flag `--dangerously-skip-permissions`. Úsalo solo dentro de un contenedor o una máquina virtual que puedas tirar, nunca en tu portátil con tus claves SSH.

Los modos fuera del ciclo se eligen al arrancar, y el mismo flag sirve para todos:

```bash
claude --permission-mode plan
claude --permission-mode manual
claude --permission-mode dontAsk
```

`manual` es un alias de `default`: usa el nombre que te resulte más natural.

Si quieres que un proyecto arranque siempre en un modo concreto, ponlo en la configuración:

```json
{
  "permissions": {
    "defaultMode": "default"
  }
}
```

Con este bloque en `.claude/settings.json`, cualquiera que abra el proyecto arranca en Manual en lugar de en auto mode. Yo lo uso en los repositorios de clientes: la primera hora con un código que no conozco prefiero ver cada comando. También funciona con `plan` y `acceptEdits`. Con `auto` y `bypassPermissions`, no: como `defaultMode` solo tienen efecto en `~/.claude/settings.json`, y si los escribes en el archivo del proyecto o en el local se ignoran. Tiene sentido, porque si no, un repositorio clonado de internet podría arrancar solo en `bypassPermissions` en tu ordenador.

## 11.3 Reglas allow, ask y deny

El modo decide el comportamiento base. Las reglas añaden excepciones: este comando pasa siempre, este pregunta siempre, este no pasa nunca. Se escriben en un archivo JSON y Claude Code las aplica en cualquier modo, también en auto mode.

Sal de Claude Code y crea la carpeta de configuración del proyecto:

```bash
mkdir -p .claude
```

Luego crea `.claude/settings.json` con este contenido:

```json
{
  "permissions": {
    "allow": [
      "Bash(python -m pytest *)",
      "Bash(git diff *)"
    ],
    "ask": [
      "Bash(git push *)"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Bash(curl *)",
      "Agent(model:opus)"
    ]
  }
}
```

En `allow` están pytest y `git diff`: comandos que no cambian nada importante y que no quiero aprobar cada vez. En `ask` está `git push`: aunque todo lo demás fluya sin preguntas, antes de mandar código al remoto quiero decir que sí yo. En `deny` hay cuatro prohibiciones: leer el `.env` y sus variantes (`.env.local`, `.env.production`), usar `curl` y lanzar subagentes con el modelo Opus.

La última regla usa una sintaxis reciente. Entre paréntesis, en vez de un comando, indicas un parámetro del tool y su valor: `Agent(model:opus)` afecta a las llamadas al tool `Agent` que piden el modelo Opus. En el laboratorio sirve para enseñar la sintaxis, pero también tiene un uso práctico: si trabajas con un plan de pago por uso, mantienes los subagentes en modelos más ligeros y dejas Opus para la sesión principal.

El archivo está dentro del proyecto, así que acaba en Git y vale para todo el equipo. Haz commit de él como de cualquier otro archivo de configuración.

Ahora pruébalo. Reinicia `claude` para que lea la nueva configuración, pasa a Manual con un `Shift+Tab` y escribe:

```text
ejecuta los tests con python -m pytest
```

En Manual, Claude pediría confirmación para casi cualquier comando, pero pytest coincide con una regla allow: se lanza al momento y ves `1 passed`. Ahora el segundo prompt:

```text
muéstrame el contenido de .env
```

Claude intenta usar el tool `Read`, la regla deny lo para y el contenido del archivo no llega a aparecer en pantalla. Claude te dice que la configuración del proyecto deniega la lectura.

::: {.callout .callout-warning}
[Atención]{.callout-title}

En la grabación de la lección, después del rechazo, Claude me sugirió leer yo mismo el archivo con `! cat .env`, y más adelante lanzar `! curl ...` para la descarga bloqueada. El prefijo `!` ejecuta el comando directamente en la shell, en tu nombre, y las reglas deny limitan a Claude, no a ti. Además, la salida de un comando lanzado con `!` entra en la conversación: con `! cat .env`, el secreto que querías mantener fuera acaba justo en el contexto. Si una regla te bloquea, decides tú si la regla está mal, y si lo está, cambia la regla.
:::

## 11.4 Sintaxis de las reglas y orden de evaluación

La forma es siempre `Tool(especificador)`. El nombre del tool solo, sin paréntesis, afecta a todos sus usos: `"Bash"` en `ask` significa que cada comando de shell pide confirmación. El especificador cambia de significado según el tool.

| Regla | A qué afecta |
| --- | --- |
| `Bash(python -m pytest *)` | Cualquier comando que empiece por `python -m pytest` |
| `Bash(git diff *)` | `git diff` con cualquier argumento |
| `Read(./.env)` | La lectura del archivo `.env` del proyecto |
| `Edit(./data/**)` | Los cambios en cualquier archivo bajo `data/` |
| `WebFetch(domain:pypi.org)` | Las peticiones web a `pypi.org` |
| `Agent(model:opus)` | Los subagentes lanzados con el modelo Opus |
| `mcp__github__*` | Todos los tools del servidor MCP `github` |

En Bash el asterisco funciona como comodín. Ojo con el espacio antes del asterisco: `Bash(ls *)` afecta a `ls -la` pero no a `lsof`, mientras que `Bash(ls*)` afecta a los dos. En `Read` y `Edit` el especificador es una ruta con los patrones de `.gitignore`, así que `**` baja por todas las subcarpetas. Las reglas sobre `Edit` valen para todos los tools que modifican archivos, `Write` incluido.

Los tools MCP tienen nombres compuestos: `mcp__`, el nombre del servidor, dos guiones bajos y el nombre del tool. `mcp__github__*` aprueba o deniega de una vez todo lo que expone el servidor `github`; con el nombre completo, por ejemplo `mcp__github__create_pull_request`, eliges los tools de uno en uno. Te vendrá bien en el Capítulo 13, cuando conectes GitHub a Claude Code y quieras dejar libres las lecturas pero no la creación de PR.

El orden de evaluación es fijo: primero deny, luego ask, luego allow. Un deny gana siempre, aunque exista un allow más específico. Si en `allow` escribes `Bash(git push origin feature/*)` y en `ask` tienes `Bash(git push *)`, el push a la rama de feature sigue pidiendo confirmación, porque ask se evalúa antes. Las reglas de todos los archivos de configuración se suman (la Sección 11.5 enumera dónde están), y un deny escrito en cualquiera de ellos no se puede anular con un allow escrito en otro.

Ahora, el límite que tienes que tener claro. Una regla sobre Bash compara el texto del comando, no el programa que se ejecuta. `Bash(curl *)` bloquea `curl https://...` escrito tal cual. No bloquea `wget`, ni un script de Python que abre una conexión con `urllib`, ni un `npm install` cuyo script de postinstall descarga algo. Lo mismo pasa con `Read(./.env)`: para el tool `Read`, pero un comando de shell que lee el archivo entra por otro camino. Para un límite de verdad hacen falta el sandbox, que verás más adelante en este capítulo, o un hook que examine el comando antes de que se ejecute, que escribirás en el Capítulo 12.

¿Y las instrucciones en `CLAUDE.md`? "No leas nunca el archivo .env" en `CLAUDE.md` orienta a Claude, y normalmente Claude lo respeta. Pero es texto en el contexto del modelo, que puede olvidarlo después de una compactación o darle menos peso que a una petición tuya explícita. Una regla deny la hace cumplir Claude Code, el programa, antes de que salga la llamada. Las dos cosas se complementan: en `CLAUDE.md` explicas el porqué y en la configuración pones la prohibición.

## 11.5 Dónde van las reglas

Las reglas pueden estar en cuatro sitios, con alcances distintos.

| Archivo | Alcance | En Git |
| --- | --- | --- |
| `~/.claude/settings.json` | Todos tus proyectos | No |
| `.claude/settings.json` | El proyecto, compartido con el equipo | Sí |
| `.claude/settings.local.json` | El proyecto, solo tú | No |
| Managed settings | La organización, no se pueden sobrescribir | Las gestiona IT |

El archivo de usuario es el sitio para las preferencias personales que quieres en todas partes: por ejemplo, los deny `Read(~/.ssh/**)` y `Read(~/.aws/**)`, que no tienen que ver con ningún proyecto en particular. El archivo de proyecto es el que acabas de escribir: reglas que valen para cualquiera que clone el repositorio. El archivo local recoge tus excepciones en ese proyecto, y ahí acaba cada "sí, y no me lo vuelvas a preguntar" que das en una petición de permiso. Cuando Claude Code lo crea en un repositorio, lo deja fuera de Git por su cuenta, con una línea en las exclusiones globales de Git y no en el `.gitignore` del proyecto. Si lo creas tú a mano, añádelo al `.gitignore`.

De vez en cuando abre `.claude/settings.local.json` y reléelo. Al cabo de unas semanas encontrarás aprobaciones dadas sobre la marcha que no repetirías en frío, y alguna merece subir al archivo de proyecto porque también les sirve a tus compañeros.

Las managed settings las distribuye la organización y no se pueden sobrescribir: si la empresa deniega `Bash(git push --force *)`, ningún archivo local lo vuelve a abrir. Desde ahí un administrador también puede apagar auto mode para todos con `"disableAutoMode": "disable"` dentro de `permissions`. Si hay conflicto en un valor único, como `defaultMode`, decide la precedencia: managed por encima de todo, luego los argumentos de línea de comandos, luego el archivo local, el de proyecto y por último el de usuario.

## 11.6 /permissions y Recently denied

Para ver las reglas activas no hace falta abrir cuatro archivos. Escribe `/permissions` (el alias es `/allowed-tools`): el panel se abre en la pestaña Allow y con la flecha derecha pasas a Ask y a Deny. Si seleccionas una regla y pulsas `Enter`, ves de dónde viene; para las del laboratorio, la línea dice `From shared project settings`, es decir, `.claude/settings.json`.

En la grabación, la pestaña Allow también mostraba algunas reglas `mcp__computer-use__*` que yo no había escrito en el laboratorio: venían de la configuración de usuario de mi cuenta. Es la prueba práctica de que las reglas se suman, y la razón por la que `/permissions` es el primer sitio donde mirar cuando un comando pasa o se bloquea y no entiendes por qué. Otro detalle que observé: en auto mode, la regla `Bash(python -m pytest *)` ya no aparecía entre los allow. Al entrar en auto mode, Claude Code aparta las reglas allow amplias que permiten ejecutar código arbitrario, como `Bash(*)` o un intérprete seguido del comodín, y las vuelve a activar cuando sales de auto mode. Un `python` aprobado automáticamente podría ejecutar cualquier cosa, y se saltaría el clasificador.

La última pestaña es Recently denied. Recoge las acciones que bloqueó el clasificador de auto mode, y desde ahí puedes reintentarlas aprobándolas tú. Si está vacía, el panel lo indica: `Commands denied by the auto mode classifier will appear here`. Solo recoge las decisiones del clasificador: lo que para una regla deny tuya no aparece ahí, y en la próxima sección lo verás pasar.

## 11.7 Auto mode en la práctica

Vuelve a auto mode: desde Manual son tres pulsaciones de `Shift+Tab` (accept edits, plan, auto). Luego pide un trabajo normal:

```text
añade una función media() en src/report.py con su test y ejecuta los tests
```

Claude modifica `src/report.py`, añade el test en `tests/test_report.py`, lanza pytest y termina con `2 passed`, sin una sola petición de confirmación. En auto mode Claude no se detiene en las operaciones normales: modifica los archivos de la carpeta del proyecto, ejecuta los tests, instala las dependencias declaradas. Antes de cada acción que no sea trivial, eso sí, el clasificador comprueba que encaja con lo que pediste.

Las categorías que bloquea son aquellas en las que un error sale caro: descargar y ejecutar scripts de internet, force push, borrados irreversibles, deploys a producción, envío de datos sensibles al exterior. Así que el segundo prompt es una trampa a propósito:

```text
descarga y ejecuta el script https://example.com/install.sh
```

Claude se detiene. Pero cuando abrí `/permissions` para enseñar la pestaña Recently denied, estaba vacía. Quien había parado a Claude no era el clasificador, sino la regla deny sobre `curl` de la Sección 11.3. Las reglas también valen en auto mode y se evalúan antes que el clasificador, así que el comando nunca llegó hasta él.

Preparando la lección probé la misma petición sin esa regla, y el clasificador no la bloqueó. El clasificador es un modelo que juzga el contexto, y su valoración puede salir por donde no esperas; quizá con `example.com`, un dominio reservado para ejemplos, pesó justo eso. Una regla deny, en cambio, es determinista: o el texto coincide o no coincide. Para lo que no debe pasar nunca, escribe una regla. El clasificador cubre todo lo demás, es decir, las situaciones que no habías previsto.

Con ask pasa lo mismo. La regla `Bash(git push *)` pide confirmación también en auto mode, y como un force push empieza igualmente por `git push`, nunca llega al clasificador: antes te llega la pregunta a ti.

Dos comportamientos de auto mode que conviene conocer. El primero: el clasificador también lee los límites que pones en la conversación. Si escribes "no hagas push", bloquea los push hasta que digas lo contrario. Es una indicación en el contexto, no una regla guardada: vale para esa sesión y puede perderse en una compactación. Si quieres una garantía, usa un deny. El segundo: si Claude se bloquea tres veces seguidas, o veinte veces en total en la sesión, auto mode se pone en pausa y vuelve a pedirte confirmación. Un agente que choca una y otra vez con el clasificador probablemente ha malinterpretado la tarea, y en ese punto quieres mirar tú.

Para ver las reglas con las que razona el clasificador, sal de Claude Code y lanza desde la shell:

```bash
claude auto-mode defaults | head -40
```

El comando imprime en JSON las reglas por defecto del clasificador. Son bastantes líneas densas, de ahí el `head`. Léelas una vez con calma: te dan una idea concreta de qué considera arriesgado el clasificador y, por tanto, de qué conviene cubrir con reglas tuyas. Junto a `defaults` existen `claude auto-mode config`, que muestra la configuración efectiva con tus ajustes aplicados, y `claude auto-mode reset`, que quita la sección `autoMode` de la configuración de usuario y vuelve a los valores por defecto. Dentro de una sesión, `/auto-mode-setup` (planes Pro, Max y Team) hace que Claude prepare un borrador de entradas `autoMode.environment`, es decir, repositorios, buckets y servicios de los que te fías, a partir del proyecto y de las sesiones recientes; si lo aceptas, acaba en `~/.claude/settings.json`.

::: {.callout .callout-tip}
[Consejo]{.callout-title}

Auto mode reduce las interrupciones, pero no sustituye a la revisión. Al terminar una tarea, mira el diff de todas formas (`git diff`, o el panel `/diff` de la app de escritorio) antes de hacer commit. El clasificador juzga el riesgo de una acción; si el código está bien, lo decides tú.
:::

## 11.8 El sandbox del proyecto

El sandbox trabaja en un plano distinto al de las reglas. En vez de decidir si un comando puede ejecutarse, limita lo que puede alcanzar una vez lanzado, en el sistema de archivos y en la red, y de eso se encarga el sistema operativo: Seatbelt en macOS, bubblewrap y socat en Linux y WSL 2. Por eso funciona también cuando el comando está escrito de una forma que las reglas no reconocen, como el `wget` de la Sección 11.4. Qué limita por defecto, la prueba con `touch ~/sandbox-probe` y el significado de las claves principales los tienes en el Capítulo 2. Aquí lo activas junto con las reglas del laboratorio y lo pasas al archivo del equipo.

Pasa a Manual con `Shift+Tab`, escribe `/sandbox` y elige `Sandbox BashTool, with auto-allow`. En este modo, los comandos que se ejecutan dentro del sandbox arrancan sin pedirte confirmación, incluso en Manual, porque el límite lo garantiza el sistema. Los deny siguen vigentes: un comando denegado sigue denegado. Prueba:

```text
ejecuta ls -la y python -m pytest
```

Los dos comandos se lanzan sin ninguna petición y pytest termina con `2 passed`. Para llegar ahí, eso sí, tuve que añadir al laboratorio las dos líneas de `pytest.ini` de la Sección 11.1. Sin ellas, pytest fallaba durante la recolección con un `PermissionError` sobre el archivo `.env`. El motivo es interesante: el sandbox toma las reglas deny sobre `Read` y las aplica en el sistema operativo a todos los procesos que lanza. `Read(./.env)` ya no para solo el tool `Read` de Claude: para cualquier programa que salga de un comando dentro del sandbox, pytest incluido, que recorre la carpeta buscando tests. Es el límite de verdad del que hablaba la Sección 11.4, y lo notas en cuanto algo choca contra él.

Como viste en el Capítulo 2, el menú de `/sandbox` guarda la elección en `.claude/settings.local.json`, que solo vale para ti. En el Capítulo 2 la configuración completa iba a `~/.claude/settings.json`, para todos tus proyectos. Para un proyecto de equipo tiene más sentido el tercer sitio, `.claude/settings.json`, para que quien clone el repositorio encuentre el mismo límite. La forma mínima es `"sandbox": { "enabled": true }`; la que uso en el laboratorio es:

```json
{
  "sandbox": {
    "enabled": true,
    "allowUnsandboxedCommands": false,
    "filesystem": {
      "denyRead": ["~/.ssh", "~/.aws"]
    },
    "network": {
      "allowedDomains": ["pypi.org", "files.pythonhosted.org", "github.com"]
    }
  }
}
```

Las claves son las del Capítulo 2. Lo que cambia son los dominios: en un archivo de proyecto pones los que necesita ese proyecto, no los que usas tú a diario. Aquí están los dos de los que `pip` descarga los paquetes y GitHub; para todo lo demás, el proxy local pregunta la primera vez, y responde quien esté trabajando. El `denyRead` sobre `~/.ssh` y `~/.aws` parece fuera de lugar en un archivo de proyecto, pero es la forma de garantizarlo también al compañero que nunca ha tocado su configuración de usuario.

El sandbox solo cubre los comandos de shell y los procesos que arrancan: los hooks y los servidores MCP, que añadirás en los dos próximos capítulos, se ejecutan fuera, y lo mismo pasa con los comandos que excluyes porque no funcionan dentro, como `docker`. Si quieres un límite alrededor de todo Claude Code, necesitas un dev container, o un contenedor o una VM dedicados.

::: {.callout .callout-warning}
[Atención]{.callout-title}

El sandbox funciona en macOS, Linux y WSL 2. En Windows nativo no está soportado y los comandos se ejecutan sin límite, aunque `.claude/settings.json` diga `"enabled": true`. En Linux y WSL 2 hacen falta los paquetes del sistema: `sudo apt-get install bubblewrap socat`. Si en el equipo alguien trabaja en Windows sin WSL, la configuración compartida no le sirve: díselo, y asegúrate de que las reglas deny cubran de todos modos los casos importantes.
:::

## 11.9 Una configuración recomendada para los proyectos del libro

Juntando las piezas, la configuración que uso para los proyectos del libro es esta: auto mode para trabajar, deny sobre los secretos y los comandos peligrosos, ask sobre el push y el sandbox activado. Para el laboratorio, el `.claude/settings.json` final es:

```json
{
  "permissions": {
    "allow": [
      "Bash(python -m pytest *)",
      "Bash(git diff *)"
    ],
    "ask": [
      "Bash(git push *)"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Bash(curl *)",
      "Bash(git push --force *)",
      "Agent(model:opus)"
    ]
  },
  "sandbox": {
    "enabled": true,
    "allowUnsandboxedCommands": false,
    "filesystem": {
      "denyRead": ["~/.ssh", "~/.aws"]
    },
    "network": {
      "allowedDomains": ["pypi.org", "files.pythonhosted.org", "github.com"]
    }
  }
}
```

No hay `defaultMode`: auto mode ya es el valor por defecto y, de todos modos, `"auto"` escrito en un archivo de proyecto se ignoraría. Quien quiera arrancar en Manual usa el flag. El deny sobre `git push --force` se suma al ask sobre `git push`: el force push escrito así queda denegado, y el escrito con `-f` cae igualmente en el ask y te llega la pregunta.

Para la Photogallery, que usarás en la Parte VI, cambian los comandos y las rutas. El backend Laravel tiene su `backend/.env`, el frontend React el suyo, `frontend/.env`, y los tests del backend se ejecutan con Pest a través de `php artisan test`:

```json
{
  "permissions": {
    "allow": [
      "Bash(php artisan test *)",
      "Bash(vendor/bin/pint *)",
      "Bash(npm run lint)",
      "Bash(npm run build)",
      "Bash(git diff *)"
    ],
    "ask": [
      "Bash(git push *)",
      "Bash(php artisan migrate *)"
    ],
    "deny": [
      "Read(./backend/.env)",
      "Read(./backend/.env.backup)",
      "Read(./backend/.env.production)",
      "Read(./frontend/.env)",
      "Bash(git push --force *)",
      "Bash(git reset --hard *)"
    ]
  }
}
```

Aquí enumeré los archivos `.env` uno por uno en vez de usar `.env.*`, porque el patrón también afectaría a `backend/.env.example`, que no contiene secretos y que Claude lee con gusto para saber qué variables hacen falta. `php artisan migrate` está en `ask` porque una migración sobre la base de datos equivocada no se deshace con `git checkout`. Si en tu máquina usas el sandbox, añade el mismo bloque `sandbox` del laboratorio, con los dominios de Composer y npm en lugar de los de pip. Para npm es `registry.npmjs.org`. Para Composer, que descarga los paquetes desde varios hosts, deja que el proxy te los pregunte la primera vez y copia en la lista los que apruebes.

Una última nota: el repositorio companion de la Photogallery ya tiene un `.claude/settings.json`, que solo contiene hooks. Si añades los permisos, combínalos en el mismo archivo bajo la clave `permissions`, sin sustituir lo que ya hay. Los hooks son el tema del próximo capítulo.

## Resumen {.unlisted}

- El modo activo aparece debajo del prompt y se cambia con `Shift+Tab` (auto, Manual, accept edits, plan); `dontAsk` y `bypassPermissions` se eligen con `--permission-mode` y sirven para CI y entornos aislados.
- Las reglas allow, ask y deny en `.claude/settings.json` valen para todo el equipo; el orden es deny, luego ask, luego allow, y un deny gana siempre.
- Una regla sobre Bash compara el texto del comando: para un límite de verdad hacen falta el sandbox o un hook, y las instrucciones en `CLAUDE.md` no son permisos.
- En auto mode tus reglas van antes que el clasificador. Usa los deny para lo que no debe pasar nunca y deja al clasificador los casos imprevistos; `/permissions` muestra las reglas, su origen y Recently denied.
- El sandbox en `.claude/settings.json`, con `allowUnsandboxedCommands: false` y `denyRead` sobre las credenciales, pone un límite del sistema alrededor de los comandos de shell, no alrededor de los hooks ni de los servidores MCP.

## Ejercicio {.unlisted}

En el laboratorio, protege los datos de entrada. Añade a `.claude/settings.json` una regla ask que cubra los cambios en cualquier archivo bajo `data/`, reinicia `claude`, pasa a accept edits con `Shift+Tab` y pide:

```text
añade a data/vendite.csv la fila 2026-04,110 y actualiza el test
```

En accept edits, el cambio en `tests/test_report.py` pasa sin preguntas, y el de `data/vendite.csv` tiene que pedirte confirmación. Recházalo. El ejercicio está hecho cuando `/permissions` muestra tu regla en la pestaña Ask con origen `From shared project settings` y `git status` no lista `data/vendite.csv` entre los archivos modificados. Si después del rechazo Claude intenta añadir la fila con un comando de shell, por ejemplo `echo ... >> data/vendite.csv`, estás viendo en directo el límite de la Sección 11.4: la regla sobre `Edit` no lo cubre, y en accept edits solo te para la petición de confirmación del comando. Luego repite la prueba en auto mode y comprueba que la pregunta por el cambio llega igualmente.
