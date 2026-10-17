# Capítulo 12. Hooks, automatización determinista

::: {.chapter-goals}
[Qué aprenderás]{.callout-title}

A escribir hooks que formatean el código después de cada cambio, bloquean las escrituras en archivos sensibles, te avisan cuando Claude te está esperando y le impiden dar el trabajo por terminado con los tests en rojo. También aprenderás a probarlos a mano y a averiguar por qué uno no se dispara.

[Requisitos previos]{.callout-title}

El proyecto `cc-advanced-lab` del capítulo 11, con su `.claude/settings.json`. Necesitas `jq` (`brew install jq` en macOS, `sudo apt-get install jq` en Debian y Ubuntu), además de `ruff` y `pytest` (`pip install ruff pytest`). En Windows los scripts `.sh` se ejecutan en Git Bash, así que instala Git for Windows; no trae `jq`, que añades con `winget install jqlang.jq`.

:::

Hasta ahora le hemos pedido las cosas a Claude con palabras: formatea el código, no toques el archivo `.env`, ejecuta los tests antes de decir que has terminado. Lo escribimos en los prompts, luego en el `CLAUDE.md` (capítulo 7), y funciona casi siempre. El problema está en ese "casi". Una instrucción en el contexto es algo que el modelo probablemente seguirá; en una sesión larga, o justo después de una compactación, se le puede escapar. Las reglas de permisos del capítulo 11 cubren parte del problema, porque deciden si una acción puede ejecutarse. Lo que no pueden hacer es lanzar un formatter, ejecutar la suite de tests o mandarte una notificación.

Para eso están los hooks. Son comandos que Claude Code ejecuta por su cuenta en puntos concretos de su ciclo de trabajo, siempre, sin que el modelo tenga que acordarse. El modelo no los llama y no puede saltárselos: los lanza el harness, el programa que rodea al modelo y que ejecuta los tools (capítulo 2).

## 12.1 Los eventos del ciclo de trabajo

Cada hook está asociado a un evento. Antes de que Claude use un tool salta `PreToolUse`, que además puede bloquear la acción. Justo después salta `PostToolUse`. Cuando Claude termina de responder salta `Stop`, cuando te necesita salta `Notification` y al abrir la sesión, `SessionStart`. Con estos, más `UserPromptSubmit`, cubres la mayoría de los casos prácticos.

| Evento | Cuándo salta | Puede bloquear |
| --- | --- | --- |
| `SessionStart` | Al arrancar, al reanudar, después de `/clear` o de una compactación | No |
| `UserPromptSubmit` | Cuando envías un prompt, antes de que Claude lo procese | Sí |
| `PreToolUse` | Antes de cada llamada a un tool | Sí |
| `PostToolUse` | Después de una llamada que ha ido bien | No, el tool ya ha actuado |
| `Stop` | Cuando Claude termina de responder | Sí, hace que siga trabajando |
| `Notification` | Cuando Claude espera una entrada o un permiso | No |

Hay bastantes eventos más: entre otros, `SubagentStop` cuando termina un subagente, `PreCompact` antes de una compactación y `SessionEnd` al cerrar la sesión. La lista completa y actualizada está en la documentación oficial, pero para todo este capítulo bastan los seis de la tabla.

La columna "Puede bloquear" hay que leerla con cuidado. Bloquear un `Stop` no detiene nada: impide que Claude se detenga y lo devuelve al trabajo con un motivo. Un `PostToolUse`, en cambio, llega cuando ya está todo hecho. Puedes reaccionar, por ejemplo formateando el archivo que se acaba de escribir, pero la escritura ya se ha producido.

## 12.2 Cómo se comunica un hook

Un hook de tipo `command` es un comando de shell normal y corriente. Claude Code le pasa los datos del evento en JSON por la entrada estándar y lee la respuesta por dos canales: el código de salida y, si hace falta, la salida estándar.

Para un `PreToolUse` sobre `Bash`, la entrada tiene esta forma:

```json
{
  "session_id": "abc123",
  "cwd": "/home/dev/cc-advanced-lab",
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": { "command": "python -m pytest" }
}
```

El campo `tool_input` cambia de un tool a otro. Para `Bash` contiene `command`; para `Edit` y `Write` contiene `file_path` (con la ruta absoluta) y el contenido que se va a escribir. Los scripts de este capítulo leen esos campos con `jq`.

Hay tres respuestas posibles:

| Respuesta | Significado |
| --- | --- |
| Exit 0 | Ninguna objeción, se sigue adelante |
| Exit 2 | Bloquea; el texto de stderr vuelve a Claude como explicación |
| Exit 0 con JSON en stdout | Control más fino, por ejemplo `{"decision": "block", "reason": "..."}` para `Stop` |

Conviene tener claro qué significa el exit 0 de un `PreToolUse`: "no tengo nada que decir", no "lo apruebo". Después del hook, la acción pasa igualmente por el sistema de permisos normal, con las reglas allow, ask y deny y el modo activo. El exit 2, en cambio, detiene la acción, y el mensaje de stderr le llega a Claude, que así sabe por qué lo han parado y puede buscar otro camino. Cualquier otro código de salida se trata como un error del hook que no bloquea nada: la acción sigue adelante.

El JSON en stdout sirve cuando el código de salida no basta. Lo usarás en la sección 12.7 para el `Stop`, donde el campo `reason` se convierte en la instrucción con la que Claude retoma el trabajo. Para `PreToolUse`, el mismo canal permite devolver una decisión de permisos explícita en lugar de un simple bloqueo: dentro de `hookSpecificOutput` pones `permissionDecision` con `allow`, `deny` o `ask`, y en `permissionDecisionReason` el motivo.

### Dónde se registran

Los hooks se configuran en el `settings.json`, bajo la clave `hooks`, junto a `permissions`. La estructura tiene tres niveles: el evento, una lista de grupos con su `matcher` y, dentro de cada grupo, la lista de comandos que se ejecutan. El `matcher` filtra por nombre de tool: `"Edit|Write"` hace que el grupo salte solo con esos dos tools, y distingue mayúsculas de minúsculas, así que `"edit"` no coincide con nada. Los archivos son los mismos del capítulo 11: `.claude/settings.json` para el proyecto y el equipo, `.claude/settings.local.json` solo para ti en ese proyecto, `~/.claude/settings.json` para todos tus proyectos.

En los ejemplos, la ruta del script parte de `$CLAUDE_PROJECT_DIR`, una variable que Claude Code apunta a la raíz del proyecto. Así el comando funciona aunque la shell de Claude se haya movido a una subcarpeta. Las comillas alrededor de la variable protegen las rutas con espacios, y dentro del JSON se escriben como `\"`.

## 12.3 Formatear después de cada cambio

El primer hook formatea con `ruff` cada archivo de Python que Claude escribe o modifica. En el proyecto del laboratorio, crea la carpeta de los scripts:

```bash
mkdir -p .claude/hooks
```

Luego el archivo `.claude/hooks/format-python.sh`:

```bash
#!/bin/bash
# Formatea con ruff los archivos de Python que modifica Claude
FILE_PATH=$(jq -r '.tool_input.file_path // empty')

if [[ "$FILE_PATH" == *.py ]]; then
  ruff format "$FILE_PATH" >/dev/null 2>&1
fi

exit 0
```

`jq` lee el JSON directamente de la entrada estándar y extrae `tool_input.file_path`; el `// empty` devuelve una cadena vacía cuando falta el campo, en lugar de la palabra `null`. Si el archivo termina en `.py`, el script se lo pasa a `ruff format`, que lo reescribe en el sitio. La salida de ruff va a `/dev/null` porque aquí no le interesa a nadie, y el script siempre sale con 0: un formatter nunca debe bloquear el trabajo.

Haz el script ejecutable:

```bash
chmod +x .claude/hooks/format-python.sh
```

Y añade el bloque `hooks` al `.claude/settings.json`, junto a los `permissions` del capítulo 11:

```json
{
  "permissions": { "...": "como en el capítulo 11" },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/format-python.sh"
          }
        ]
      }
    ]
  }
}
```

Aquí la línea `"permissions"` está abreviada: en tu archivo se quedan las reglas allow, ask y deny que ya escribiste, y el bloque `sandbox` de la sección 11.9. El archivo completo, con todos los hooks del capítulo, está en la sección 12.7.

Los hooks se leen al arrancar, así que reinicia Claude Code después de cada cambio en el `settings.json`. Luego escribe `/hooks`: bajo `PostToolUse` tienes que encontrar el grupo con matcher `Edit|Write`, el comando `format-python.sh` y la indicación de que viene de la configuración del proyecto (`[Project]`). Si no aparece, el problema está en el JSON o en el nombre del evento, y no tiene sentido seguir.

<!-- TODO screenshot: pannello /hooks con PostToolUse, matcher Edit|Write e origine [Project] -->

Ahora, una prueba malintencionada a propósito:

```text
añade a src/report.py una función massimo(path) escrita toda en una sola línea, sin espacios
```

El prompt no dice nada sobre el formato; de hecho, pide lo contrario. Claude escribe la función en una línea y, en cuanto termina el tool `Edit`, Claude Code lanza el hook y ruff reescribe el archivo. Ábrelo desde el prompt de Claude Code con el prefijo `!`, que ejecuta un comando de shell sin pasar por el modelo:

```text
!cat src/report.py
```

La función ocupa ahora varias líneas, con el cuerpo indentado, y ruff ha normalizado también las comillas en el resto del archivo. En la grabación de la lección, Claude comentó después el resultado por su cuenta y dijo que el formatter había repartido `massimo` en varias líneas: no ve el hook, pero se da cuenta de que el archivo ha cambiado.

Nadie tuvo que acordarse de formatear. El mismo esquema funciona con cualquier formatter o linter rápido: `prettier --write` para un frontend, `php-cs-fixer` para Laravel, `gofmt` para Go. Solo cambian la extensión que compruebas y el comando.

## 12.4 Proteger los archivos sensibles

El segundo hook se ejecuta antes de cada cambio y bloquea los que tocan archivos protegidos: el `.env`, la carpeta `.git/` y, en nuestro laboratorio, los datos de origen en `data/`. Crea `.claude/hooks/protect-files.sh`:

```bash
#!/bin/bash
# Bloquea los cambios en archivos sensibles
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
FILE_PATH="${FILE_PATH//\\//}"   # normaliza los separadores de Windows

PROTECTED=(".env" ".git/" "data/")

for pattern in "${PROTECTED[@]}"; do
  if [[ "$FILE_PATH" == *"$pattern"* ]]; then
    echo "Bloqueado: $FILE_PATH está protegido ('$pattern'). Trabaja sobre una copia." >&2
    exit 2
  fi
done

exit 0
```

Esta vez el script guarda primero toda la entrada en `INPUT` con `cat` y luego se la pasa a `jq`. En el primer hook no hacía falta porque el JSON se leía una sola vez; tenerlo en una variable te permite extraer varios campos sin consumir el stdin. La línea siguiente cambia cada barra invertida por una barra normal: en Windows, `file_path` llega como `C:\Users\...\data\vendite.csv` y, sin normalizarlo, el patrón `data/` no coincidiría nunca. El bucle compara la ruta con cada elemento de `PROTECTED`; a la primera coincidencia escribe el motivo en stderr y sale con 2.

Hazlo ejecutable y regístralo bajo `PreToolUse`, dentro del mismo objeto `hooks` que ya contiene `PostToolUse`:

```bash
chmod +x .claude/hooks/protect-files.sh
```

```json
"PreToolUse": [
  {
    "matcher": "Edit|Write",
    "hooks": [
      {
        "type": "command",
        "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect-files.sh"
      }
    ]
  }
]
```

Reinicia Claude Code y pide un cambio en los datos:

```text
añade una fila con el mes 2026-04 a data/vendite.csv
```

Tampoco aquí el prompt dice nada sobre la protección: la regla vive solo en el hook. Durante la grabación, Claude no intentó escribir enseguida. Primero preguntó, con una pregunta de opción múltiple, qué cifra de ventas poner para abril. Responde con cualquier número. En ese momento Claude intenta el `Edit`, el hook salta y en la terminal aparece la línea roja con el mensaje de bloqueo. Claude lo lee, explica por qué lo han parado y propone una alternativa, por ejemplo trabajar sobre una copia del archivo. Comprueba con `git status` que `data/vendite.csv` sigue como estaba.

::: {.callout .callout-tip}
[Consejo]{.callout-title}

El mensaje de bloqueo muestra la ruta absoluta, porque es lo que `Edit` le pasa al hook. Si grabas la pantalla o pegas los logs en algún sitio, tu nombre de usuario acaba dentro. Para mostrar la ruta relativa al proyecto, basta con quitar el prefijo antes del `echo`, por ejemplo con `REL="${FILE_PATH#"$CLAUDE_PROJECT_DIR"/}"`, y usar `$REL` en el mensaje.
:::

### Probar un hook a mano

Los scripts de los hooks se prueban sin Claude, pasándoles un JSON de ejemplo con `echo`. Sal de Claude Code y ejecuta esto desde la shell, en la raíz del proyecto:

```bash
echo '{"tool_input":{"file_path":"data/vendite.csv"}}' | .claude/hooks/protect-files.sh; echo "exit: $?"
```

La salida esperada es:

```text
Bloqueado: data/vendite.csv está protegido ('data/'). Trabaja sobre una copia.
exit: 2
```

El JSON de prueba solo contiene los campos que lee el script, y con eso basta. Con una ruta no protegida, por ejemplo `src/report.py`, solo tienes que ver `exit: 0`. El mismo truco sirve para el formatter:

```bash
echo '{"tool_input":{"file_path":"src/report.py"}}' | .claude/hooks/format-python.sh; echo "exit: $?"
```

Cuando un hook no hace lo que esperas, esta es la primera comprobación. Te dice enseguida si el problema está en el script (falta `jq`, un patrón mal escrito, no tiene permiso de ejecución) o en el registro.

## 12.5 ¿Regla deny o hook?

En el capítulo 11 ya escribiste una regla `deny` sobre `Read(./.env)`. Es normal preguntarse para qué hacen falta también los hooks.

Una regla compara un patrón con la llamada: nombre del tool más especificador, y nada más. Un hook ejecuta código tuyo, así que puede aplicar cualquier lógica: mirar el contenido que Claude quiere escribir, comprobar la rama actual, leer un archivo de configuración, llamar a otro programa. Y un hook que deniega bloquea la acción en cualquier modo de permisos, incluso en `bypassPermissions`, donde desaparecen las peticiones de confirmación.

Para reglas simples y estáticas ("no leas `.env`", "pregunta antes de `git push`"), la regla en el `settings.json` sigue siendo la opción correcta: se lee en una línea, la ves en `/permissions` y no tiene dependencias. El hook sirve cuando la condición requiere un razonamiento que un patrón no puede expresar, o cuando quieres una acción y no solo un sí o un no.

::: {.callout .callout-warning}
[Atención]{.callout-title}

`protect-files.sh` está registrado con matcher `Edit|Write`, así que solo vigila esos dos tools. Si Claude decidiera añadir la fila con un comando de shell, por ejemplo `echo "2026-04,0" >> data/vendite.csv`, el hook no saltaría. Una regla sobre `Bash` compara el texto del comando, y un hook sobre `Bash` que analiza el comando tiene el mismo límite. Para un límite que aguante de verdad en la escritura de archivos, usa el sandbox con `filesystem.denyWrite` (capítulos 2 y 11) y deja los hooks como primer filtro.
:::

La moneda también tiene otra cara. Los hooks se ejecutan con los permisos de tu usuario y fuera del sandbox. Un `.claude/settings.json` con hooks, en un repositorio que ha escrito otra persona y que tú has clonado, es código que se ejecutará en tu máquina en cuanto arranques Claude Code en esa carpeta. Antes de trabajar en un repo que no conoces, ábrelo y lee qué hay bajo `hooks`.

## 12.6 Una notificación cuando Claude te espera

Cuando dejas a Claude trabajando en una tarea larga y pasas a otra ventana, a veces descubres mucho después que estaba parado en una petición de permiso. El evento `Notification` salta justo en esos momentos. Este hook va en la configuración de usuario, `~/.claude/settings.json`, para que valga en todos los proyectos:

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "notify-send 'Claude Code' 'Claude te está esperando'"
          }
        ]
      }
    ]
  }
}
```

El matcher vacío vale para cualquier notificación. `notify-send` es el comando estándar de los escritorios Linux (en Debian y Ubuntu está en el paquete `libnotify-bin`). En macOS, sustituye el comando por:

```bash
osascript -e 'display notification "Claude te está esperando" with title "Claude Code"'
```

Dentro del JSON, las comillas dobles de este comando se escriben como `\"`. Si tu `~/.claude/settings.json` ya tiene otras claves, añade `hooks` junto a ellas en lugar de sustituir el archivo.

## 12.7 Nada de parar con los tests en rojo

El tercer hook de proyecto es el que más uso en los proyectos de Spec Driven Development (capítulos 18 y 19). Cuando Claude está a punto de detenerse, el hook ejecuta los tests. Si fallan, devuelve un JSON con `decision` igual a `block` y la salida de los tests como motivo. Claude no se detiene: lee el motivo y sigue trabajando. Crea `.claude/hooks/tests-before-stop.sh`:

```bash
#!/bin/bash
# Impide que Claude se detenga si los tests fallan
INPUT=$(cat)

# Evita el bucle infinito: si ya estamos continuando por culpa de este hook, deja que Claude se detenga
if [ "$(echo "$INPUT" | jq -r '.stop_hook_active')" = "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR" || exit 0
if ! OUTPUT=$(python -m pytest -q 2>&1); then
  jq -n --arg out "$(echo "$OUTPUT" | tail -20)" \
    '{decision: "block", reason: ("Los tests fallan, corrígelos antes de terminar:\n" + $out)}'
fi

exit 0
```

La comprobación de `stop_hook_active` es la línea más importante del script. Claude Code pone ese campo a `true` cuando Claude ya está continuando porque un Stop hook lo ha devuelto al trabajo. Sin esa comprobación, un test que Claude no consigue arreglar produciría un bucle sin fin: stop, tests en rojo, bloqueo, nuevo intento, stop, y así sucesivamente, gastando tokens en cada vuelta.

El resto es directo. El script se mueve a la raíz del proyecto, ejecuta `pytest` en modo silencioso y captura stdout y stderr en `OUTPUT`. Si pytest sale con un código distinto de cero, `jq -n` construye el JSON desde cero: `--arg out` pasa las últimas veinte líneas de la salida como cadena, ya bien escapada, y el filtro las concatena al mensaje. Usar `jq` en lugar de montar el JSON a mano con `echo` te ahorra problemas con las comillas y los saltos de línea dentro de la salida de pytest. El script siempre sale con 0, porque aquí el bloqueo pasa por el JSON.

Hazlo ejecutable y regístralo bajo `Stop`:

```bash
chmod +x .claude/hooks/tests-before-stop.sh
```

```json
"Stop": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/tests-before-stop.sh",
        "timeout": 120
      }
    ]
  }
]
```

`Stop` no tiene que ver con ningún tool, así que el grupo no lleva `matcher`. El `timeout` va en segundos. Para los hooks `command` el valor por defecto es 600, diez minutos: aquí lo bajo a 120, porque si la suite se cuelga prefiero no quedarme esperando diez minutos en cada stop. En este laboratorio pytest tarda menos de un segundo. Cuando vence el plazo, el hook se interrumpe y cuenta como un error que no bloquea nada: Claude se detiene de todos modos.

Llegados a este punto, el `.claude/settings.json` del laboratorio contiene los permisos y el sandbox del capítulo 11 y los tres hooks de proyecto:

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
  },
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{
        "type": "command",
        "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/format-python.sh"
      }]
    }],
    "PreToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{
        "type": "command",
        "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect-files.sh"
      }]
    }],
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/tests-before-stop.sh",
        "timeout": 120
      }]
    }]
  }
}
```

### La prueba

Para ver el hook en acción hace falta un test en rojo. Con Claude Code cerrado, rompe el test a propósito cambiando `358` por `359`:

```bash
sed -i 's/358/359/' tests/test_report.py
```

En macOS, `sed` exige un argumento vacío después de `-i`: `sed -i '' 's/358/359/' tests/test_report.py`. También puedes cambiar el número a mano en el editor; el resultado es el mismo.

Antes de arrancar Claude puedes probar el script con `echo`, como en la sección 12.4. Hay un detalle: `CLAUDE_PROJECT_DIR` la define Claude Code y en tu shell no existe. Pásala tú en la línea de comandos:

```bash
echo '{"stop_hook_active": false}' | CLAUDE_PROJECT_DIR="$PWD" .claude/hooks/tests-before-stop.sh
```

Tienes que ver el JSON con `"decision": "block"` y, en el `reason`, el fallo de `test_totale`. Con `"stop_hook_active": true` el script no debe imprimir nada.

Ahora arranca `claude` y pide un cambio que no tenga nada que ver con los tests:

```text
añade un docstring a la función totale
```

Claude añade el docstring e intenta detenerse. El Stop hook no le pide permiso al modelo: salta solo, ejecuta pytest, encuentra el test en rojo y bloquea. En la terminal aparece la respuesta del hook, `Stop hook error: Los tests fallan, corrígelos antes de terminar:` seguida de la salida de pytest. Claude lee el motivo, ve que el test espera 359 mientras que la suma de los datos da 358, restaura el valor correcto y vuelve a ejecutar los tests. En el segundo stop `stop_hook_active` vale `true` y el hook lo deja detenerse.

<!-- TODO screenshot: riscontro dello Stop hook con l'output di pytest e Claude che corregge il test -->

Con este script el bloqueo salta una vez por respuesta. Si después de la primera vuelta los tests siguieran en rojo, en el segundo stop el hook dejaría que Claude se detuviera de todos modos: es el precio de la comprobación anti-bucle. En la práctica basta, porque Claude recibe la salida de pytest y normalmente arregla el problema al primer intento, y en cualquier caso al final de la respuesta ves el estado real de los tests.

Fíjate también en que en esta prueba Claude corrigió el test, no el código. Aquí era lo correcto, porque el test lo habíamos roto nosotros. En un proyecto real, un test en rojo puede significar que la implementación está mal: si quieres que Claude no toque los tests sin preguntar, escríbelo en el `CLAUDE.md` o añade `tests/` a la lista de `protect-files.sh`.

## 12.8 Hooks condicionales, SessionStart y los otros tipos

Dos variantes útiles, aunque no las usaremos en el laboratorio.

La primera es el campo `if`, que usa la misma sintaxis que las reglas de permisos. Aquí el hook salta solo con los comandos `git`, no con todos los comandos `Bash`:

```json
"PreToolUse": [
  {
    "matcher": "Bash",
    "hooks": [
      {
        "type": "command",
        "if": "Bash(git *)",
        "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/check-git-policy.sh"
      }
    ]
  }
]
```

El `matcher` selecciona el tool y el `if` acota según la entrada. Sin `if`, el script tendría que leer `tool_input.command` y salir enseguida con 0 para todo lo que no empiece por `git`: funciona, pero cada `ls` y cada `pytest` lanzarían un proceso de más.

La segunda usa `SessionStart` con el matcher `compact`. Después de cada compactación del contexto, lo que el hook imprime en stdout se añade al contexto de Claude:

```json
"SessionStart": [
  {
    "matcher": "compact",
    "hooks": [
      {
        "type": "command",
        "command": "echo 'Recuerda: lee SPEC.md antes de implementar. Últimos commits:' && git log --oneline -5"
      }
    ]
  }
]
```

Para `SessionStart`, el matcher filtra el origen de la sesión, y `compact` indica que se reanuda después de una compactación. Es una buena forma de no perder por el camino las reglas del proyecto, como leer la especificación antes de implementar, justo en el momento en que el resumen puede haberlas diluido. En el capítulo 15 volvemos sobre la compactación y sobre lo que sobrevive a ella.

Además de `command` existen otros tipos de hooks. Los de tipo `http` envían el JSON del evento a una URL, útil para un servicio interno que registra o aprueba las acciones. Los de tipo `prompt` y `agent` le piden a un modelo que decida, para condiciones que un script no sabe evaluar, como "¿este cambio respeta las convenciones del `CLAUDE.md`?". Los hooks `agent` todavía son experimentales. Por último, los hooks pueden viajar dentro de un plugin, en el archivo `hooks/hooks.json`, con rutas basadas en `${CLAUDE_PLUGIN_ROOT}`: lo veremos en el capítulo 14.

## 12.9 Cuando un hook no funciona

Los problemas más comunes, con su solución:

| Problema | Solución |
| --- | --- |
| El hook no salta | `/hooks` para comprobar evento y matcher (distinguen mayúsculas de minúsculas); reinicia Claude Code después de cada cambio en el `settings.json` |
| `jq: command not found` | Instala `jq` o reescribe el script en Python |
| El script no se ejecuta | `chmod +x` sobre el script |
| El JSON impreso se ignora | Un `echo` en el perfil de la shell ensucia la salida: muévelo dentro de `if [[ $- == *i* ]]` |
| Claude no se detiene nunca | Falta la comprobación de `stop_hook_active` |

La cuarta fila merece un ejemplo. Si tu `~/.bashrc` muestra un mensaje de bienvenida, cuando se carga la shell para ejecutar el hook ese texto acaba en stdout delante del JSON, y Claude Code ya no consigue interpretarlo. La guarda hace que el mensaje se imprima solo en las shells interactivas:

```bash
if [[ $- == *i* ]]; then
  echo "Bienvenido"
fi
```

Dos comprobaciones más que no están en la tabla pero ahorran tiempo. Antes de mirar la configuración, lanza el script a mano con `echo` como en la sección 12.4: si ahí falla, el `settings.json` no tiene nada que ver. Y en Windows, comprueba que Claude Code esté usando Git Bash, porque en PowerShell un script `.sh` no arranca (el capítulo 1 explica cómo indicar la ruta con `CLAUDE_CODE_GIT_BASH_PATH`).

## Resumen {.unlisted}

- Un hook es un comando que Claude Code ejecuta por su cuenta cuando ocurre un evento: convierte una recomendación que el modelo sigue casi siempre en una regla que se cumple siempre.
- Se registra en el `settings.json` bajo `hooks`, con evento, `matcher` y comando; la ruta del script parte de `"$CLAUDE_PROJECT_DIR"` y los cambios valen a partir del siguiente reinicio.
- El hook recibe JSON por stdin y responde con el código de salida: 0 sigue adelante (para `PreToolUse` no es una aprobación), 2 bloquea y manda stderr a Claude, 0 más JSON en stdout para decisiones como el `block` de `Stop`.
- Un Stop hook siempre debe comprobar `stop_hook_active`; si no, te arriesgas a un bucle infinito.
- Un hook que deniega bloquea en cualquier modo, pero solo ve los tools de su matcher: para un límite real sobre los archivos también necesitas el sandbox.
- Los hooks se prueban a mano con `echo` y se comprueban con `/hooks`.

## Ejercicio {.unlisted}

Escribe `.claude/hooks/check-git-policy.sh`, el script que aparece en la sección 12.8, y regístralo bajo `PreToolUse` con matcher `Bash` y `"if": "Bash(git *)"`. El script lee `tool_input.command` y bloquea con exit 2 cualquier `git push` que contenga `--force` o `-f`, con un mensaje en español en stderr que sugiera `--force-with-lease`. Todos los demás comandos pasan con exit 0, incluido precisamente `--force-with-lease`: cuidado con el patrón, porque esa cadena contiene `--force`.

El ejercicio está terminado cuando estas tres pruebas a mano dan el resultado esperado:

```bash
echo '{"tool_input":{"command":"git push --force origin main"}}' | .claude/hooks/check-git-policy.sh; echo "exit: $?"
echo '{"tool_input":{"command":"git push --force-with-lease origin main"}}' | .claude/hooks/check-git-policy.sh; echo "exit: $?"
echo '{"tool_input":{"command":"git status"}}' | .claude/hooks/check-git-policy.sh; echo "exit: $?"
```

La primera tiene que imprimir tu mensaje y `exit: 2`; las otras dos, solo `exit: 0`. Luego reinicia Claude Code y comprueba que `/hooks` muestra el nuevo grupo bajo `PreToolUse`, con el comando `check-git-policy.sh`.
