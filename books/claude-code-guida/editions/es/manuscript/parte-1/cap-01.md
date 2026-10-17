# Capítulo 1. Qué es Claude Code

::: {.chapter-goals}
[Qué aprenderás]{.callout-title}

Al terminar este capítulo tendrás Claude Code instalado y conectado a tu cuenta, conocerás la docena de comandos y atajos que usarás a diario y habrás hecho que Claude escriba y ejecute un primer programa, mirando cada paso. Además sabrás cómo está organizado el resto del libro y por dónde te conviene empezar.

[Requisitos previos]{.callout-title}

Un ordenador con macOS 13 o posterior, Windows 10 (1809) o posterior, o Linux (Ubuntu 20.04+, Debian 10+), con al menos 4 GB de RAM. Un plan de pago de Claude (Pro, Max, Team o Enterprise) o una cuenta de Claude Console. Python 3 para el ejemplo de la sección 1.5.

:::

Claude Code es el programa con el que Anthropic mete a Claude dentro de tu proyecto. Lo abres en una carpeta, le escribes en español lo que quieres, y él lee los archivos, los modifica, ejecuta comandos y te cuenta lo que ha hecho. Este libro empieza aquí y llega, en la Parte VI, a una aplicación full-stack desplegada en AWS. Entre medias hay un método de trabajo que se aprende pieza a pieza, y la primera pieza es tener la herramienta bien instalada y saber dónde tocar.

## 1.1 Qué es Claude Code

Claude Code es un agente para el desarrollo de software. Nació como programa de línea de comandos, y la terminal sigue siendo donde mejor rinde, pero hoy el mismo agente funciona también dentro de VS Code y JetBrains, en la app de escritorio de Claude y en el navegador (lo cuento al final de la sección 1.3). En todos los casos trabaja sobre los archivos reales de tu proyecto, no sobre una copia pegada en un chat.

Un agente es un modelo de lenguaje al que el harness, es decir, el programa que lo rodea, le pone a disposición unas herramientas: leer un archivo, modificarlo, ejecutar un comando. El modelo decide qué herramienta necesita, Claude Code la ejecuta y le devuelve el resultado, y la vuelta se repite hasta que el trabajo está terminado o hasta que hace falta una decisión tuya. El capítulo 2 desmonta este mecanismo pieza a pieza. Por ahora basta con saber que el modelo pide y Claude Code ejecuta, bajo tu control.

### Frente a otras herramientas

Con un chat en el navegador, sea claude.ai u otro, el trabajo de alrededor lo haces tú. Eliges qué archivos pegar, copias la respuesta en el editor, ejecutas los tests y vuelves al chat con el error. La calidad de la respuesta depende de lo bien que hayas elegido qué enseñarle al modelo.

Los asistentes integrados en el editor, como GitHub Copilot o Cursor, nacieron como autocompletado de código mientras escribes, y hoy también tienen modos agénticos. Son herramientas serias y muchos desarrolladores los usan junto a Claude Code. La diferencia práctica está en el punto de partida: Claude Code nace en la terminal, así que funciona en cualquier sitio donde puedas abrir una shell (tu portátil, un servidor por SSH, un contenedor, un pipeline de CI) y se puede lanzar desde un script sin ninguna interfaz gráfica.

No hay una herramienta mejor en términos absolutos. Claude Code rinde más cuando el trabajo abarca el proyecto entero: un refactoring que toca diez archivos, una feature nueva con sus tests, un codebase que no conoces y que tienes que entender deprisa. Para completar la línea que estás escribiendo, el autocompletado del editor sigue siendo más cómodo.

### Qué puede hacer en la práctica

Lee cualquier archivo de texto del proyecto, del código a la configuración, y lo modifica. Ejecuta comandos en la terminal, como `npm install`, `pytest`, `git status` o `docker build`, y lee su salida, errores incluidos. Explora las carpetas para entender cómo está hecho el proyecto antes de tocarlo. Trabaja con Git: lee el historial, crea ramas, hace commit, prepara pull requests. Con los servidores MCP (Model Context Protocol) se conecta a servicios externos como GitHub, una base de datos o tu calendario, que es el tema del capítulo 13.

Todo pasa por una conversación. Escribes lo que quieres conseguir, Claude propone y actúa, y para las acciones delicadas te pide permiso o las bloquea. Qué acciones pasan por ti lo decide el modo de permisos (sección 1.3).

## 1.2 Instalación

La instalación recomendada es el instalador nativo: un único binario, sin Node.js, sin permisos de administrador, que se actualiza solo en segundo plano.

### El instalador nativo

En macOS, Linux y WSL:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

En Windows, desde PowerShell:

```powershell
irm https://claude.ai/install.ps1 | iex
```

O desde el Símbolo del sistema (CMD):

```batch
curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
```

Si en el Mac ya usas Homebrew, o en Windows prefieres WinGet, también tienes estos caminos:

```bash
brew install --cask claude-code
```

```powershell
winget install Anthropic.ClaudeCode
```

Con Homebrew y WinGet las actualizaciones no son automáticas: las lanzas tú con `brew upgrade claude-code` o `winget upgrade Anthropic.ClaudeCode`. El cask `claude-code` de Homebrew sigue el canal estable, y también existe `claude-code@latest` para el canal de las últimas versiones. Para las distribuciones Linux hay además repositorios apt, dnf y apk firmados, que se actualizan con el gestor de paquetes del sistema.

### Si instalas con npm

La primera edición de este libro empezaba con `npm install -g`. El paquete npm sigue existiendo y está documentado como opción avanzada, pero hoy requiere Node.js 22 o posterior e instala el mismo binario nativo que el instalador: el comando `claude` no necesita Node para funcionar.

```bash
npm install -g @anthropic-ai/claude-code
```

Tres cosas que debes saber si eliges este camino. Para actualizar usa `npm install -g @anthropic-ai/claude-code@latest`, no `npm update -g`. No uses nunca `sudo npm install -g`: crea archivos propiedad de root que luego bloquean las actualizaciones normales. Si npm responde con un error `EACCES` en la carpeta de paquetes globales, la solución más sencilla es olvidarte de npm y usar el instalador nativo. Con un Node anterior al 22, npm solo muestra un aviso `EBADENGINE` y sigue adelante, así que comprueba antes `node --version`.

### Comprobación y actualizaciones

Abre una terminal nueva, para que la shell vuelva a leer el `PATH`, y comprueba:

```bash
claude --version
claude doctor
```

El primer comando imprime la versión, algo como `2.1.302 (Claude Code)`. El segundo revisa la instalación y los archivos de configuración sin iniciar una sesión, y te dice qué falla y cómo arreglarlo. Es de solo lectura: no modifica nada.

La instalación nativa se actualiza sola. Claude Code lo comprueba al arrancar y cada cierto tiempo, y la versión nueva entra en funcionamiento en el siguiente reinicio. Si quieres actualizar ya:

```bash
claude update
```

Puedes elegir entre dos canales de actualización: `latest`, el predeterminado, que recibe todas las versiones, y `stable`, que suele ir una semana por detrás y se salta las versiones con regresiones graves. Se cambia desde `/config`, en la opción Auto-update channel, o al instalar con `curl -fsSL https://claude.ai/install.sh | bash -s stable`. Si usas Claude Code en proyectos de trabajo y no te interesa probar las novedades el mismo día, `stable` es una elección sensata.

### Windows

En Windows el instalador nativo funciona directamente desde PowerShell o desde CMD, sin WSL.

Git for Windows ya no es obligatorio. Si está instalado, Claude Code usa Git Bash para ejecutar los comandos; si falta, usa PowerShell. Conviene instalarlo de todas formas, porque Git lo vas a necesitar igualmente y algunas funciones de Claude Code, como el tool `Bash` y el Monitor para seguir los logs, necesitan Git Bash. Si Claude Code no encuentra Git Bash, indica la ruta en `%USERPROFILE%\.claude\settings.json`:

```json
{
  "env": {
    "CLAUDE_CODE_GIT_BASH_PATH": "C:\\Program Files\\Git\\bin\\bash.exe"
  }
}
```

Aun así, hay un motivo para elegir WSL 2. El sandbox de comandos, que limita los archivos y la red de lo que Claude ejecuta en la terminal (capítulos 2 y 11), no funciona en Windows nativo y sí en WSL 2. Si trabajas con toolchains de Linux o quieres el sandbox, instala Claude Code dentro de WSL 2 con el comando para Linux, el de `install.sh`. WSL 1 no está soportado.

### Si algo falla

El caso más habitual es `command not found` justo después de instalar. Casi siempre basta con cerrar la terminal y abrir una nueva. Si no basta, comprueba que la carpeta donde el instalador pone el binario esté en el `PATH`. En macOS y Linux es `~/.local/bin`, en Windows `%USERPROFILE%\.local\bin`:

```bash
echo $PATH | tr ':' '\n' | grep local
```

Si la carpeta no aparece, añade `export PATH="$HOME/.local/bin:$PATH"` a tu `~/.zshrc` o `~/.bashrc` y vuelve a abrir la terminal.

Si en el pasado instalaste Claude Code con npm y ahora usas el instalador nativo, puedes acabar con dos `claude` distintos. `which -a claude` los lista todos, y el que cuenta es el primero. Desinstala la versión de npm con `npm uninstall -g @anthropic-ai/claude-code` para evitar sorpresas.

En Windows hay dos errores que solo indican que has pegado el comando en la shell equivocada. `The token '&&' is not a valid statement separator` significa que estás en PowerShell y has usado el comando para CMD; `'irm' is not recognized` es el caso contrario.

Para todo lo demás, empieza por `claude doctor`. Dentro de una sesión existe también `/doctor`, que hace una revisión más amplia y puede aplicar las correcciones por su cuenta.

### Cuenta y primer acceso

Claude Code no está incluido en el plan gratuito de claude.ai. Funciona con una suscripción Pro o Max, con los planes Team y Enterprise, con una cuenta de Claude Console (que paga por consumo, por token) y con los proveedores cloud: Amazon Bedrock, Google Cloud (Agent Platform, el antiguo Vertex AI) y Microsoft Foundry.

La primera vez basta con lanzar:

```bash
claude
```

Claude Code te pide que elijas el tema de colores y luego abre el navegador para el login. Elige el tipo de cuenta (suscripción de Claude, Console o plataforma de terceros), autoriza el acceso y vuelve a la terminal. Si el navegador no se abre solo, copia la URL que aparece en la terminal, completa el login a mano y pega el código que recibes. Con una cuenta de Console ya no hace falta crear una API key: basta con el login desde el navegador.

Los otros comandos relacionados con la cuenta son `/login`, para iniciar sesión o cambiar de cuenta, y `/logout`, que además de desconectarte restablece la configuración del primer arranque. Desde la shell tienes los equivalentes `claude auth login`, `claude auth logout` y `claude auth status`.

::: {.callout .callout-warning}
[Atención]{.callout-title}

Si en tu shell está definida la variable `ANTHROPIC_API_KEY` y la apruebas cuando Claude Code te lo pregunta, esa clave tiene prioridad sobre la suscripción: pagas por consumo en la Console aunque tengas un plan Max. Le pasa a menudo a quien exporta la clave en el `.zshrc` para otros proyectos. En modo `claude -p` la clave se usa siempre, sin preguntar. Comprueba con `/status` qué método de autenticación está activo; si no es el que quieres, ejecuta `unset ANTHROPIC_API_KEY` y reinicia Claude Code.
:::

### La primera sesión en una carpeta

Claude Code trabaja en la carpeta desde la que lo lanzas. Antes de arrancarlo, entra en el proyecto:

```bash
mkdir mio-progetto
cd mio-progetto
claude
```

La primera vez que lo abres en una carpeta, te pregunta si confías en los archivos que contiene. Responde que sí solo en carpetas que conoces: un proyecto descargado de internet puede contener archivos de configuración que Claude Code lee y aplica. La primera sesión en auto mode muestra también un aviso que explica el modo (lo cuento en un momento).

Después aparece la pantalla de bienvenida, con el modelo activo, tu cuenta y la carpeta actual, y debajo el prompt donde escribir. Para salir usa `/exit` o pulsa `Ctrl+C` dos veces.

<!-- TODO screenshot: fig-01, schermata di benvenuto della versione corrente (modello Opus 5.5, cartella di prova). Senza email, nome dell'organizzazione o percorsi personali. -->

## 1.3 Comandos básicos y modos

Todo lo que no es un prompt empieza con una barra. Escribe `/` y Claude Code muestra la lista de comandos, que se filtra a medida que tecleas. En la lista aparecen también las skills, tuyas o de los plugins instalados, porque se invocan de la misma manera. Hay decenas de comandos; los que siguen son los que usarás desde el primer día.

`/help` muestra la ayuda con los atajos principales y la lista de comandos disponibles. La primera vez dedícale un par de minutos.

<!-- TODO screenshot: fig-02, scheda general di /help nella versione corrente. La vecchia cattura (v2.1.78, Opus 4.6) mostrava "& for background", che non va presentato. -->

### La conversación y el contexto

Todo lo que Claude ve en una sesión está en la ventana de contexto: las instrucciones de sistema, los archivos del proyecto como `CLAUDE.md`, los archivos que ha leído, los comandos que ha ejecutado y tus mensajes. Con los modelos actuales la ventana llega a un millón de tokens, pero cuanto más se llena, más cuesta la sesión y más aumenta el riesgo de que Claude pierda los detalles del principio. La regla práctica es una tarea, una sesión. Con `/context` ves cuánto está llena y qué la ocupa; el capítulo 15 está dedicado a esto.

Cuatro comandos gestionan la conversación:

```text
/clear                    empieza de cero con el contexto vacío
/compact [instrucciones]  resume la conversación y libera espacio
/resume                   retoma una sesión anterior
/rewind                   vuelve a un punto anterior de la sesión
```

`/clear` es el que debes usar cuando cambias de tema. La conversación antigua no desaparece: la encuentras en `/resume`, y si escribes `/clear nombre` le pones una etiqueta para reconocerla. `/compact`, en cambio, se queda en la misma sesión y sustituye los mensajes antiguos por un resumen. Puedes decirle qué conservar, por ejemplo `/compact conserva las decisiones sobre el formato del CSV y la lista de archivos modificados`. `/resume` abre la lista de sesiones pasadas, o retoma directamente la que indiques por nombre o ID. `/rewind` lleva hacia atrás el código, la conversación o ambos hasta un checkpoint. También lo abres pulsando dos veces `Esc` con el prompt vacío, y es el primer comando que tienes que recordar cuando Claude se mete por un camino equivocado.

### Estado, consumo y configuración

`/status` abre la configuración en la pestaña Status: versión, modelo, cuenta y método de autenticación, conexión. Es el comando que necesitas cuando algo no cuadra, empezando por el caso de la API key de antes.

`/usage` muestra cuánto estás consumiendo. Con una cuenta de Console ves el coste de la sesión; con una suscripción ves los límites del plan, cuánto has usado y qué los está consumiendo, desglosado por skill, subagente, plugin y servidor MCP. `/cost`, el comando de la primera edición, sigue funcionando: hoy es un alias de `/usage`, igual que `/stats`.

<!-- TODO screenshot: fig-04, output di /usage su un abbonamento (sostituisce la vecchia cattura di /cost). -->

`/model` muestra los modelos disponibles en tu plan y el activo, y te permite cambiarlo. La elección pasa a ser el predeterminado para las sesiones siguientes; si pulsas `s` en el selector vale solo para la sesión actual, y con las flechas izquierda y derecha ajustas el effort. Mientras escribo, el predeterminado es Claude Opus 5.5. Los otros alias son `sonnet`, más rápido y más barato, `haiku`, el más ágil para los trabajos repetitivos, y `fable`, el más capaz, que nunca es el predeterminado. También está `opusplan`, que usa Opus mientras planifica y Sonnet mientras ejecuta. Los nombres de los modelos cambian cada pocos meses, así que no te fíes de los que aparecen aquí: consulta `/model`. El modelo y el effort se explican en el capítulo 2.

<!-- TODO screenshot: fig-03, selettore di /model nella versione corrente (sostituisce la vecchia cattura con Sonnet 4.6). -->

`/config` abre toda la configuración: tema, canal de actualización, modo vim del editor (el antiguo comando `/vim` ya no existe), uso de la API key y mucho más. También acepta la forma `/config clave=valor`, por ejemplo `/config model=sonnet`.

`/init` analiza el proyecto y escribe un primer `CLAUDE.md`, el archivo con las instrucciones que Claude lee en cada sesión. En un proyecto vacío no hace falta; en un proyecto real es una de las primeras cosas que hay que hacer, y el capítulo 7 explica cómo revisar lo que genera.

Por último, `/btw` te permite hacer una pregunta rápida, por ejemplo sobre el significado de un error, sin que acabe en la conversación principal.

### Atajos de teclado

| Tecla | Qué hace |
| --- | --- |
| `!` al principio del prompt | Modo shell: ejecuta el comando, añade la salida a la conversación y Claude la comenta |
| `@` | Completa las rutas de archivo, para señalarle a Claude un archivo concreto |
| `?` con el prompt vacío | Muestra la ayuda de los atajos |
| `Esc` | Interrumpe a Claude mientras trabaja, o cierra un menú |
| `Esc` dos veces | Borra el texto escrito; con el prompt vacío abre `/rewind` |
| `Shift+Tab` | Cambia el modo de permisos (en algunas configuraciones de Windows es `Alt+M`) |
| `Ctrl+O` | Muestra la transcripción detallada, con cada llamada a los tools |
| `Ctrl+R` | Busca en el historial de prompts |
| `Ctrl+G` | Abre el prompt en tu editor externo, cómodo para textos largos |
| `Ctrl+B` | Manda a segundo plano un comando o un agente en ejecución |
| `Ctrl+T` | Muestra u oculta la checklist de pasos de Claude |
| `Shift+Enter` | Salta de línea sin enviar |
| `Ctrl+V` | Pega una imagen, por ejemplo una captura de un error (`Alt+V` en Windows y WSL, `Cmd+V` en iTerm2) |

`Shift+Enter` funciona de serie en iTerm2, WezTerm, Ghostty, Kitty, Warp, Terminal de macOS y Windows Terminal. En las demás terminales lanza `/terminal-setup`, o usa `\` seguido de Enter, que funciona en todas partes. Con la flecha arriba recorres los prompts anteriores, como en una shell.

Si vienes de la primera edición: el atajo `#` para añadir una línea a la memoria se ha eliminado. Para guardar una instrucción, pídele a Claude que la añada a `CLAUDE.md`, o usa `/memory` (capítulo 7).

### Interactivo y headless

Hasta ahora has visto el modo interactivo: escribes, Claude responde, la sesión sigue abierta. Con el flag `-p` Claude Code ejecuta un solo prompt, imprime la respuesta y sale:

```bash
claude -p "analiza el archivo main.py y dime cuántas funciones contiene"
```

Es el modo para los scripts, la CI y los trabajos programados, y acepta también entrada desde una tubería, como `git diff | claude -p "resume estos cambios"`. En `-p` no hay nadie a quien pedir confirmación, así que las acciones que no están aprobadas de antemano no se ejecutan. Las autorizas con `--allowedTools`, por ejemplo `--allowedTools "Bash(git diff *),Read"`. En los scripts conviene añadir `--bare`, que se salta hooks, skills, plugins, servidores MCP y `CLAUDE.md` y hace que el resultado sea predecible, y `--output-format json` cuando la salida la tiene que leer otro programa.

### Los modos de permisos

El modo de permisos decide qué acciones puede hacer Claude sin pedirte confirmación, y aparece en la barra de estado debajo del prompt. Las sesiones interactivas arrancan en auto mode, donde un clasificador aprueba las acciones coherentes con tu petición y bloquea las arriesgadas. Con `Shift+Tab` pasas a Manual, que pide confirmación para casi todo, y luego a Accept edits y a Plan. El capítulo 2 explica cómo funcionan y el capítulo 11 cómo configurarlos. Existe también el flag `--dangerously-skip-permissions`, que quita cualquier control: úsalo solo dentro de un contenedor o una máquina virtual desechable, nunca en tu portátil.

### Más allá de la terminal

En VS Code (y en Cursor) instala la extensión `anthropic.claude-code`: es la forma recomendada de usar Claude Code en el editor, con el plan para revisar, los diffs en línea y las referencias a archivos con sus líneas. La extensión ya trae su propia copia de la CLI para el panel de chat; si también quieres el comando `claude` en la terminal integrada, instala la CLI como hemos visto antes. Para IntelliJ, PyCharm, PhpStorm y los demás IDE de JetBrains existe el plugin Claude Code [Beta], que en cambio no incluye la CLI: hay que instalarla antes. La app de escritorio de Claude tiene una pestaña Code (macOS, Windows, Linux en beta), y `/desktop` lleva allí la sesión que tienes abierta en la terminal. Por último, las sesiones cloud en claude.ai/code se ejecutan en los servidores de Anthropic: las inicias desde el navegador o desde la terminal con `claude --cloud "<task>"` y las traes a tu máquina con `claude --teleport`. En el libro trabajamos casi siempre en la terminal, que es donde mejor se ve lo que pasa.

### La carpeta .claude

Claude Code guarda su configuración en dos sitios. En tu directorio personal, `~/.claude/` contiene la configuración personal (`settings.json`), tu `CLAUDE.md` personal, las skills y los agentes válidos para todos los proyectos, los plugins instalados y, bajo `projects/`, las sesiones guardadas y la memoria automática. En el proyecto, `.claude/` contiene configuración y extensiones compartidas con el equipo a través de Git. Volvemos a ello en las partes III y IV.

## 1.4 Un entorno de trabajo cómodo

Vas a pasar muchas horas leyendo diffs y salidas de tests en la terminal, y una que gestione bien el scroll, la búsqueda y los colores marca una diferencia real. Nada de esta sección es obligatorio.

### La terminal

En macOS hay dos opciones habituales. iTerm2 (iterm2.com) es gratuita y madura: paneles divididos, búsqueda en el historial con expresiones regulares, perfiles distintos para entornos distintos. Warp (warp.dev), gratuita para uso personal, agrupa cada comando con su salida en un bloque que puedes seleccionar, copiar y volver a encontrar, y cuando Claude produce salidas largas viene bien para volver a una parte concreta sin perder el hilo.

En Windows usa Windows Terminal, que ya viene instalada en Windows 11 y se descarga gratis desde la Microsoft Store en Windows 10. Tiene pestañas, paneles divididos y un perfil para cada shell: PowerShell para la instalación nativa, Ubuntu si trabajas en WSL 2.

En Linux, la terminal de tu distribución, GNOME Terminal o Konsole, va perfectamente. Si quieres algo más rápido, Alacritty y Kitty son buenas alternativas.

### Shell y prompt

En macOS la shell predeterminada es zsh desde 2019. En Linux suele ser bash; si quieres zsh, instálala con el gestor de paquetes (`sudo apt install zsh` en Ubuntu) y configúrala con `chsh -s $(which zsh)`. oh-my-zsh (ohmyz.sh) añade autocompletado avanzado y sugerencias a partir del historial; fish (fishshell.com) ya los trae sin plugins.

Uses la shell que uses, instala Starship (starship.rs), un prompt que funciona con zsh, bash, fish y PowerShell. Muestra la rama de Git y el estado del repositorio, la versión de Node o el virtualenv de Python activos y el tiempo de ejecución del último comando, útil para ver cuánto tardan los comandos que lanza Claude.

En macOS:

```bash
brew install starship
```

En Linux y WSL:

```bash
curl -sS https://starship.rs/install.sh | sh
```

Después añade al final de tu `~/.zshrc` esta línea y reinicia la terminal:

```bash
eval "$(starship init zsh)"
```

### Alias

Tres alias que uso todos los días, para poner en el `.zshrc` o en el `.bashrc`:

```bash
alias c='claude'                                # arranque interactivo
alias cm='claude --permission-mode default'     # arranque en Manual
alias cq='claude -p'                            # una pregunta rápida, headless
```

`cm` me sirve cuando trabajo en un proyecto que no conozco y quiero ver cada acción antes de que se ejecute. `cq` es para las preguntas rápidas: `cq "¿qué versión de Laravel usa este proyecto?"`. En la primera edición el alias headless se llamaba `cp`. Era un error, porque oculta el comando `cp` para copiar archivos. En la misma lista había un alias para `--dangerously-skip-permissions`, que he quitado por los motivos que vimos en la sección 1.3.

### Dotfiles

Guarda la configuración de la terminal en un repositorio Git: una carpeta `dotfiles/` con al menos `.zshrc`, `.gitconfig` y la configuración de Starship, más un pequeño `install.sh` que crea los enlaces simbólicos en tu directorio personal. Cuando cambies de portátil, recuperas el entorno completo en pocos minutos. La carpeta `~/.claude/`, con tu configuración y tus skills personales, es una muy buena candidata para añadirla.

## 1.5 Tu primer prompt guiado

Este ejemplo lleva cinco minutos y una carpeta vacía. Lo hacemos en Manual, el modo que pide confirmación para cada acción, porque la primera vez merece la pena ver cada paso antes de que ocurra.

```bash
mkdir -p ~/projects/hello-claude && cd ~/projects/hello-claude
claude --permission-mode default
```

Si Claude Code te pregunta si confías en la carpeta, responde que sí. En la barra de estado tiene que aparecer `manual mode on`. Ahora escribe este prompt (las cadenas en italiano son a propósito: coinciden con la salida que verás más abajo y con el ejercicio del final del capítulo):

```text
Crea un archivo hello.py que imprima un saludo en la terminal.
Añade un argumento opcional --name (por defecto "mondo")
e imprime "Ciao <name>". Usa argparse para gestionar el argumento.
```

Claude mira la carpeta, ve que está vacía y decide que hace falta un solo archivo. Antes de escribirlo te enseña el contenido que quiere crear y te pregunta si sigue adelante. Verás algo parecido a esto:

```python
#!/usr/bin/env python3
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="mondo")
    args = parser.parse_args()
    print(f"Ciao {args.name}")


if __name__ == "__main__":
    main()
```

El código exacto cambia un poco de una vez a otra. Léelo y luego confirma con la primera opción. El archivo aparece en la carpeta.

Ahora pídele que lo pruebe:

```text
Ejecuta hello.py sin argumentos y luego con --name Hidran.
```

Claude propone el primer comando, `python3 hello.py` (o `python hello.py`, según el sistema), y espera tu confirmación. Luego el segundo. La salida es:

```text
Ciao mondo
Ciao Hidran
```

No has abierto ningún editor ni has copiado código de ningún sitio.

::: {.callout .callout-tip}
[Consejo]{.callout-title}

Durante los primeros días lee cada propuesta antes de confirmar, aunque sea obvia. Es la forma más rápida de entender cómo razona Claude, qué archivos mira y qué comandos prefiere. Cuando ya te hayas hecho una idea, vuelve al auto mode con `Shift+Tab` y deja al clasificador las confirmaciones rutinarias.
:::

### Qué ha pasado

Claude ha recogido el contexto (la carpeta estaba vacía), ha actuado (ha escrito el archivo) y ha verificado (ha ejecutado el programa y ha leído la salida). Cada acción ha pasado por ti antes de ejecutarse, porque estabas en Manual. Esta vuelta de contexto, acción y verificación es el bucle agéntico, y la encontrarás idéntica en la Photogallery, con un proyecto Laravel y React en lugar de un archivo. En el capítulo 2 lo miras por dentro con `Ctrl+O`.

Puedes borrar la carpeta con `rm -rf ~/projects/hello-claude`, pero te conviene conservarla: la usas en el ejercicio del final del capítulo, y es un sitio seguro donde probar los comandos de los próximos capítulos sin arriesgar código que importa.

::: {.callout .callout-prompt}
[Prompt reutilizable]{.callout-title}

El primer prompt que escribo en un proyecto que no conozco, antes de pedir cualquier cambio:

```text
Lee los archivos del proyecto y dime:
1. Qué stack tecnológico ves
2. Qué parte parece más reciente y cuál más antigua
3. Qué archivo es el punto de entrada (entry point)
4. Qué NO entiendes a primera vista mirando los nombres de las carpetas
```

Funciona en cualquier codebase. La cuarta pregunta es la más útil: te dice dónde le va a costar a Claude, y por tanto qué tendrás que explicarle o poner en `CLAUDE.md`.
:::

## 1.6 El mapa del libro

El libro está dividido en seis partes. Cada una usa lo que has aprendido en las anteriores.

| Parte | Capítulos | Qué haces |
| --- | --- | --- |
| I. Fundamentos | 1-3 | Instalas Claude Code, entiendes cómo funcionan los tools, el bucle agéntico, los permisos y el sandbox, aprendes a escribir prompts útiles y a usar Plan Mode |
| II. Análisis de datos | 4-6 | Partes de un CSV de métricas SaaS y llegas a un informe de Excel con fórmulas de verdad, gráficos, un dashboard en Flask y un PDF |
| III. Ampliar Claude Code | 7-10 | Escribes `CLAUDE.md`, comandos personalizados, skills y agentes, y pruebas el plugin Superpowers |
| IV. Control y automatización | 11-15 | Permisos, modos y sandbox, hooks, servidores MCP, plugins y marketplaces, contexto y memoria |
| V. Landing page | 16 | El primer proyecto completo, de la idea al deploy en Firebase |
| VI. Photogallery | 17-23 | Una aplicación full-stack con Spec Driven Development, hasta el deploy en AWS |

La Parte IV es nueva en esta edición. Nace de que hoy Claude Code arranca en auto mode y trabaja durante largos tramos sin preguntarte nada, así que conviene saber exactamente dónde están los límites y cómo moverlos. Trabaja sobre un pequeño proyecto de laboratorio, `cc-advanced-lab`, que creas ya en el capítulo 2.

La Parte VI es el núcleo del libro. Construyes la Photogallery: una API REST en Laravel 13, un panel de administración en Filament v5, un frontend React 19 con Vite 6 y Tailwind CSS v4, autenticación con tokens de Sanctum y jobs en cola para redimensionar las fotos y leer los datos EXIF. Primero escribes las especificaciones y las conviertes en un plan de 124 tareas en 14 fases, luego las ejecutas por oleadas con una revisión después de cada una, también en paralelo sobre worktrees separados. Antes del deploy haces QA, una revisión con `/code-review` y una segunda opinión de otros modelos (Gemini, Codex, Kimi). Se cierra con el deploy en AWS con CloudFormation. El código está en el repositorio `github.com/hidran/claude-code-book-photogallery`, con una rama para cada etapa.

Al final encontrarás cinco apéndices: glosario, resolución de problemas, recopilación de prompts, recursos y changelog.

No estás obligado a leerlo todo en orden, pero la primera vez te conviene. La única excepción razonable es la Parte IV, que también puedes leer después de los proyectos de las partes V y VI. Pero si trabajas con código que importa, léela antes.

## Resumen {.unlisted}

- Instala Claude Code con el instalador nativo, que se actualiza solo. Homebrew y WinGet son alternativas con actualización manual; npm es una opción avanzada que requiere Node.js 22+.
- `claude doctor` es la primera comprobación cuando algo no funciona; `claude update` actualiza en el momento.
- Necesitas un plan de pago o una cuenta de Console. Una `ANTHROPIC_API_KEY` aprobada tiene prioridad sobre la suscripción: compruébalo siempre con `/status`.
- Los comandos de todos los días son `/clear`, `/compact`, `/resume`, `/rewind`, `/usage` (que ha absorbido `/cost`), `/model`, `/config` y `/init`.
- Las sesiones arrancan en auto mode; `Shift+Tab` pasa a Manual, Accept edits y Plan. `claude -p` ejecuta un solo prompt y sale.
- En Windows el instalador nativo funciona sin WSL, pero para el sandbox hace falta WSL 2.

## Ejercicio {.unlisted}

Primero, comprueba el setup. `claude doctor` no debe señalar errores, y en una sesión `/status` tiene que mostrar la cuenta y el método de autenticación que esperas (suscripción o Console).

Después vuelve a `~/projects/hello-claude` y arranca `claude` sin flags, es decir, en auto mode. Pide:

```text
Añade a hello.py una opción --maiuscolo que imprima el saludo en mayúsculas, y luego ejecútalo con y sin la opción.
```

Cuenta cuántas confirmaciones te pide en comparación con la vuelta en Manual de la sección 1.5. Cuando termine, pulsa dos veces `Esc` con el prompt vacío y vuelve al checkpoint anterior a la petición, restaurando el código. Si Claude ha modificado el archivo con un comando de shell en lugar de con el tool `Edit`, el checkpoint no cubre ese cambio: en ese caso borra la opción a mano o pídele a Claude que lo haga.

El ejercicio está terminado cuando `python3 hello.py --name Hidran` imprime `Ciao Hidran` y `python3 hello.py --maiuscolo` termina con el error de argparse `unrecognized arguments: --maiuscolo`, señal de que el rewind ha devuelto el archivo a su versión inicial.
