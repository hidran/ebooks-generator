# Capítulo 2. Del modelo al agente: tools, bucle agéntico, permisos y sandbox

::: {.chapter-goals}
[Qué aprenderás]{.callout-title}

Este capítulo desmonta Claude Code para ver qué pasa entre el prompt que escribes y el archivo que cambia en el disco. Al terminar sabrás:

- qué es un tool y quién lo ejecuta de verdad, el modelo o el harness;
- cómo funciona el bucle agéntico, probado en un proyecto de prueba que montas en cinco minutos;
- qué deciden los modos de permisos y qué limita el sandbox;
- cómo elegir modelo y nivel de effort con `/model` y `/effort`.

[Requisitos previos]{.callout-title}

Claude Code instalado (capítulo 1), Python 3 y Git. Para la prueba del sandbox necesitas macOS, Linux o WSL 2.

:::

En el capítulo 1 viste a Claude Code crear un archivo y ejecutarlo. A partir del capítulo 3 escribirás prompts cada vez más ambiciosos, y antes conviene saber cómo trabaja la máquina que los recibe. Lo que te llevas de aquí es un modelo mental más que un proyecto. Plan Mode, CLAUDE.md, las skills, los agentes, los hooks y los servidores MCP tienen cada uno un sitio concreto en el mecanismo que describo en estas páginas, y cuando te los encuentres en los capítulos siguientes ya sabrás dónde encajan.

## 2.1 Qué sabe hacer un modelo por sí solo

Un LLM es un modelo que, dado un texto, predice el texto que viene después, un token cada vez. Por sí solo hace una única cosa: recibe texto y devuelve texto. No puede abrir un archivo de tu proyecto, no puede ejecutar un test, no sabe qué hora es. Del mundo conoce lo que vio durante el entrenamiento, hasta una fecha de corte, más lo que le escribas en el prompt.

Cuando usas un chat y pegas un trozo de código, el trabajo de alrededor lo haces tú. Eliges qué pegar, copias la respuesta en el editor, la pruebas y vuelves al chat con el stack trace. El modelo razona, pero las manos son tuyas, y la calidad de la respuesta depende de lo bien que hayas elegido qué enseñarle.

Un agente es un LLM al que le damos manos. Le ponemos herramientas a su disposición, lo hacemos trabajar en un bucle, y él decide qué herramientas usar, en qué orden y cuándo ha terminado.

![Un LLM en un chat devuelve texto que tú copias, ejecutas y compruebas; un agente como Claude Code alterna llamadas a herramientas y resultados hasta terminar el trabajo](figures-en/cap-02/fig-01.png)

## 2.2 Qué es un tool

Un tool es una función que le describimos al modelo con tres datos: un nombre, una descripción en lenguaje natural y un esquema de los parámetros que acepta. Esta es la definición de un tool que lee un archivo, en el formato que usa la API de Anthropic:

```json
{
  "name": "read_file",
  "description": "Legge un file del progetto e ne restituisce il contenuto.",
  "input_schema": {
    "type": "object",
    "properties": {
      "path": { "type": "string", "description": "Percorso del file" }
    },
    "required": ["path"]
  }
}
```

El modelo recibe estas definiciones junto con tu petición. La descripción importa tanto como el código: es lo único en lo que se basa el modelo para saber cuándo sirve ese tool y cómo llamarlo.

El detalle que tienes que grabarte es que el modelo nunca ejecuta nada. Cuando decide que necesita leer un archivo, produce un mensaje estructurado que dice, en esencia, "quiero usar `read_file` con esta ruta":

```json
{
  "type": "tool_use",
  "id": "toolu_01",
  "name": "read_file",
  "input": { "path": "src/report.py" }
}
```

Después se detiene y espera. El programa que lo aloja lee la petición, abre el archivo de verdad y devuelve el resultado, ligado a la petición mediante el `id`:

```json
{
  "type": "tool_result",
  "tool_use_id": "toolu_01",
  "content": "import csv\n\n\ndef totale(path): ..."
}
```

En ese momento el modelo retoma el razonamiento con el contenido del archivo delante. Puede pedir otra llamada o dar la respuesta final. Cada llamada repite los mismos pasos.

![Una llamada a un tool, paso a paso: el modelo pide, Claude Code comprueba permisos y hooks, la herramienta se ejecuta y el resultado vuelve al modelo](figures-en/cap-02/fig-02.png)

::: {.callout .callout-deep-dive}
[Bajo el capó]{.callout-title}

`read_file` es un ejemplo simplificado. El tool real de Claude Code se llama `Read` y acepta `file_path` más parámetros opcionales para leer solo una parte del archivo. Las definiciones de todos los tools disponibles viajan con cada petición al modelo y ocupan espacio en la ventana de contexto: lo ves con `/context`, en la entrada dedicada a los tools. Por eso los servidores MCP, que pueden añadir decenas de tools, cargan al arrancar solo los nombres y el resto cuando hace falta. Volvemos a ello en los capítulos 13 y 15.
:::

## 2.3 El harness, o sea, Claude Code

El programa que rodea al modelo se llama **harness**. Claude Code es un harness: gestiona la conversación, expone los tools, ejecuta las llamadas, pide los permisos y aplica las reglas de seguridad. El modelo está en otro sitio (en los servidores de Anthropic o en los de tu proveedor cloud) y solo ve texto: tu prompt, las definiciones de los tools y los resultados que Claude Code le devuelve.

Casi todo lo que configurarás en este libro vive en el harness, no en el modelo. Cada funcionalidad interviene en un punto concreto de la vuelta que acabas de ver:

| Funcionalidad | Dónde interviene | Capítulo |
| --- | --- | --- |
| Plan Mode | Limita el modelo a leer y proponer, sin modificar nada, hasta que apruebas el plan | 3 y 4 |
| CLAUDE.md, memoria automática | Texto que se carga en el contexto al empezar la sesión | 7 y 15 |
| Comandos personalizados, skills | Instrucciones que se añaden al contexto cuando hacen falta | 8 y 9 |
| Agentes, subagentes | El tool `Agent` abre un segundo bucle con un contexto propio | 10 |
| Permisos | Deciden si una llamada puede ejecutarse | 11 |
| Hooks | Scripts que el harness lanza antes o después de una llamada, y que pueden bloquearla | 12 |
| MCP | Añade tools que hablan con servicios externos | 13 |
| Plugins | Empaquetan skills, agentes, hooks y servidores MCP para instalarlos de una vez | 14 |
| `/context`, `/compact`, `/rewind` | Gestionan lo que el modelo ve en cada vuelta | 15 |

Cuando un capítulo te diga "este es un hook que se ejecuta en `PreToolUse`", puedes volver a la figura anterior: es el paso 2, la comprobación que hace Claude Code antes de ejecutar la herramienta.

## 2.4 El bucle agéntico

Un agente no hace una sola llamada, trabaja en un bucle. Primero reúne contexto: lee archivos, busca en el código, quizá consulta la documentación. Luego actúa: modifica un archivo, lanza un comando. Luego verifica: ejecuta los tests, lee la salida. Si algo falla, el resultado de la verificación se convierte en contexto nuevo y el bucle vuelve a empezar. Se detiene cuando considera que el trabajo está completo, o cuando te necesita.

![El bucle agéntico de Claude Code: reunir contexto, actuar, verificar; si el trabajo no ha terminado, los resultados se convierten en contexto nuevo](figures-en/cap-02/fig-03.png)

Nadie le dice al modelo qué tools usar ni en qué orden. Lo decide él, vuelta tras vuelta, según lo que ha leído. Es cómodo, porque no tienes que escribir un procedimiento, pero también significa que el agente toma por su cuenta decenas de pequeñas decisiones: qué archivo abrir, qué test añadir, cuándo dar el trabajo por terminado. Para que no se desvíe hay que darle dos cosas: una petición clara y un criterio de verificación que pueda comprobar solo, como "los tests pasan" o "la build termina con código 0". En la Parte VI esta idea se convierte en un método completo, el Spec Driven Development (capítulo 18), y en el capítulo 20 la vuelves a encontrar en `/goal`, que hace que Claude siga trabajando hasta que se cumple una condición verificable.

## 2.5 El bucle en directo sobre un proyecto minúsculo

Para ver el bucle necesitas un proyecto lo bastante pequeño como para leerlo en un minuto. Es el mismo laboratorio que uso en el curso en vídeo, `cc-advanced-lab`: un script de Python que suma las ventas de un CSV, con un test. Lo volverás a usar en el ejercicio de final de capítulo y cuando hablemos de permisos, hooks y MCP.

Los comandos funcionan en bash y zsh sobre macOS, Linux y WSL. En Windows nativo ejecútalos desde Git Bash, o trabaja en WSL 2, que de todas formas necesitarás para el sandbox.

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
```

El archivo `.env` con un secreto falso no hace falta ahora: lo usaremos en el capítulo 11 para probar las reglas que impiden que Claude lo lea. El `pytest.ini` hace que `from src.report import totale` funcione tanto con `pytest` como con `python -m pytest`: sin él, el comando `pytest` a secas se detiene con `ModuleNotFoundError: No module named 'src'`.

Falta pytest. Las instalaciones recientes de Python en macOS (Homebrew) y en Ubuntu rechazan `pip install` fuera de un entorno virtual, así que crea uno en el proyecto y arranca Claude Code desde la misma shell, para que el Python que encuentre en el `PATH` sea el correcto:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pytest
pytest -q
claude
```

`pytest -q` tiene que responder `1 passed`. Si Claude Code te pregunta si confías en la carpeta, responde que sí. Ahora escribe el prompt:

```text
encuentra la función que calcula el total, añade un test y comprueba que pasa
```

No has nombrado ni el archivo ni la herramienta de tests. Claude tiene que encontrar `totale` en `src/report.py`, entender qué hace, añadir un test en `tests/test_report.py` junto a `test_totale`, ejecutar pytest y leer el resultado. Cuando termine, pulsa `Ctrl+O`: se abre la vista detallada de la conversación, con cada llamada a los tools y su resultado. Vuelve a pulsar `Ctrl+O` para cerrarla.

En una vuelta típica verás un `Bash` que busca la función en los archivos, un `Read` para leerla, un `Edit` para escribir el test y otro `Bash` para ejecutar pytest. En macOS, Linux y WSL, Claude Code ya no ofrece tools de búsqueda separados y busca a través de la shell; en otras instalaciones puedes encontrar en su lugar `Grep` y `Glob`. Cuando grabé esta escena para el curso, la vista mostraba solo llamadas `Bash`, "ran 4 shell commands": Claude había buscado, leído e incluso escrito el archivo con comandos de shell. El primer intento, por cierto, falló con `No module named pytest`, porque el Python del `PATH` de esa shell no tenía pytest instalado. Por eso aquí te hago crear el virtualenv antes de arrancar Claude. La secuencia exacta de llamadas cambia de una vuelta a otra. Lo que se mantiene es la estructura: contexto, acción, verificación.

Antes de seguir, mira el diff con `git diff`. Deberías ver solo el test nuevo. Si quieres empezar de cero, `git checkout -- .` devuelve el proyecto al estado del commit inicial.

## 2.6 Los tools principales de Claude Code

No hace falta aprendérselos de memoria, pero conviene reconocerlos cuando aparecen en la vista de `Ctrl+O` y cuando los escribas en las reglas de permisos del capítulo 11. La lista depende del sistema y del modelo: esta es la que encuentras en macOS, Linux y WSL con los modelos actuales.

| Tool | Para qué sirve | Fase del bucle |
| --- | --- | --- |
| `Read` | Leer un archivo, o solo una parte | Reunir contexto |
| `WebSearch`, `WebFetch` | Buscar y leer páginas web | Reunir contexto |
| `Edit`, `Write` | Modificar y crear archivos | Actuar |
| `Bash` (`PowerShell` en Windows) | Buscar en los archivos, ejecutar comandos: tests, build, Git | Todas |
| `Agent` | Delegar una subtarea en un subagente con su propio contexto | Todas |
| Tools MCP | Cualquier servicio externo conectado: GitHub, bases de datos | Todas |

En algunas instalaciones también encuentras `Grep` y `Glob`, tools dedicados a buscar texto y archivos por nombre: hacen el mismo trabajo que en otros sistemas pasa por `Bash`. Con los modelos menos recientes aparecen además los tools de la lista de tareas (`TaskCreate`, `TodoWrite`), con los que Claude planifica los pasos y los va marcando. Con los modelos actuales no se ofrecen (la variable de entorno `CLAUDE_CODE_ENABLE_TODO_TOOLS=1` los vuelve a activar), mientras que `Ctrl+T` muestra u oculta la checklist de tareas en la interfaz. Los subagentes lanzados con `Agent` se ejecutan en segundo plano por defecto: hablamos de ello en el capítulo 10. Los tools MCP aparecen con un nombre compuesto por prefijo, servidor y tool, por ejemplo `mcp__github__create_pull_request`. Los verás en el capítulo 13.

## 2.7 LLM y agente, frente a frente

Pongamos las dos cosas una al lado de la otra.

| | LLM en un chat | Agente como Claude Code |
| --- | --- | --- |
| Entrada | El texto que le das | Tu petición más todo lo que lee por su cuenta |
| Salida | Texto | Acciones sobre tu proyecto, más un informe |
| Contexto | Solo lo que pegas | Archivos, comandos, web, servicios conectados |
| Quién ejecuta | Tú, copiando y pegando | El harness, llamando a los tools |
| Verificación | La haces tú | La hace el agente: tests, build, salida |
| Duración | Una respuesta | Un bucle de muchos pasos |
| Riesgo | Una respuesta equivocada | Una acción equivocada en tu ordenador |

La última fila es la que más pesa. Con un LLM en un chat, lo peor que puede pasar es una respuesta equivocada, que puedes ignorar. Con un agente, lo peor es una acción equivocada: un archivo borrado, un `git push --force` sobre la rama que no era, un dato enviado adonde no debía ir. Cuanta más autonomía das, más control necesitas. Claude Code lo aborda en dos niveles, y el primero son los modos de permisos.

## 2.8 Los modos de permisos

Un modo de permisos es el ajuste que decide qué acciones puede hacer Claude sin pedirte confirmación. El activo aparece siempre en la barra de estado, debajo del prompt.

Las sesiones interactivas en el terminal y en VS Code arrancan en **auto mode**: para los planes Pro, Max y Team desde la versión 2.1.228 (agosto de 2026), y para todos los planes y proveedores desde la 2.1.283. En auto mode un segundo modelo, el clasificador, examina las acciones en tu lugar: deja pasar las que encajan con tu petición y bloquea las arriesgadas, como descargar y ejecutar scripts de internet, hacer force push, borrar de forma irreversible archivos existentes, hacer deploy en producción o enviar datos sensibles fuera. La primera vez que una sesión arranca en auto mode, Claude Code muestra un aviso. La excepción es el modo no interactivo, `claude -p`, que sigue arrancando en Manual. Si leíste la primera edición de este libro, o has visto vídeos grabados antes de esta versión, este es el motivo por el que Claude te pide confirmación mucho menos de lo que esperas: tu configuración está bien, lo que ha cambiado es el valor por defecto.

Durante la sesión, `Shift+Tab` va pasando por los modos en este orden:

| Modo | Nombre en los ajustes | Barra de estado | Qué hace |
| --- | --- | --- | --- |
| Auto | `auto` | `auto mode on` | El clasificador aprueba o bloquea en tu lugar |
| Manual | `default` (alias `manual`) | `manual mode on` | Pide confirmación para casi todo |
| Accept edits | `acceptEdits` | `accept edits on` | Modifica archivos sin preguntar, pregunta para lo demás |
| Plan | `plan` | `plan mode on` | Analiza y propone un plan, sin modificar nada |

Otro `Shift+Tab` después de Plan te devuelve a auto. Plan Mode lo usas ya desde el capítulo 3, y en el capítulo 4 se convierte en la forma habitual de empezar un análisis.

Fuera del ciclo hay otros dos modos. `dontAsk` deja pasar las lecturas en el directorio de trabajo, los comandos Bash de solo lectura y los tools que hayas aprobado de antemano con una regla, y deniega sin preguntar todo aquello para lo que, si no, te pediría confirmación: sirve para scripts y CI. `bypassPermissions`, lo mismo que el antiguo flag `--dangerously-skip-permissions`, quita cualquier control y solo debe usarse dentro de un contenedor o de una máquina virtual aislada.

Puedes elegir el modo al arrancar con un flag:

```bash
claude --permission-mode manual
claude --permission-mode plan
```

`manual` es un alias de `default`, el nombre técnico del modo Manual.

Si prefieres arrancar siempre en Manual, por ejemplo mientras sigues los primeros capítulos y quieres ver cada paso como en las capturas, añade esto a `~/.claude/settings.json`:

```json
{
  "permissions": {
    "defaultMode": "default"
  }
}
```

Auto mode reduce las peticiones de confirmación, pero no garantiza la seguridad. Hay algunos detalles que conviene saber desde ya. Las acciones bloqueadas acaban en `/permissions`, en la pestaña Recently denied, desde donde puedes reintentarlas. Los límites que escribes en el chat, como "no hagas push", el clasificador los tiene en cuenta como indicaciones, no como reglas guardadas. Tras tres bloqueos seguidos, o veinte en toda la sesión, auto mode se pone en pausa y vuelve a pedirte confirmación. Si quieres leer las reglas que sigue el clasificador, `claude auto-mode defaults` las imprime. Las reglas allow, ask y deny, los archivos de ajustes y su precedencia son materia del capítulo 11.

## 2.9 Permisos y sandbox, dos niveles de control

Claude Code te protege con dos niveles distintos, y conviene no confundirlos.

El primer nivel son los permisos. Antes de que una llamada se ejecute, Claude Code decide si puede ejecutarse: según tus reglas, el modo de permisos elegido, el clasificador si estás en auto mode, o preguntándotelo a ti. Vale para todos los tools, desde `Read` hasta `Bash` y los tools MCP. Los permisos responden a la pregunta "¿se puede ejecutar esta acción?".

El segundo nivel es el **sandbox**. Una vez que un comando de shell ha arrancado, el sandbox limita lo que pueden alcanzar él y cada proceso que lance: en qué carpetas puede escribir, qué archivos puede leer, con qué sitios puede conectarse. Lo aplica el sistema operativo, no el modelo. El sandbox responde a otra pregunta: "aunque este comando haga más de lo que parece, ¿hasta dónde puede llegar?".

![Dos niveles de control: los permisos deciden si una llamada puede ejecutarse y valen para todos los tools; el sandbox limita archivos y red solo para los comandos Bash](figures-en/cap-02/fig-04.png)

Hacen falta los dos porque una regla de permisos mira el texto del comando, y un comando puede hacer cosas que no se deducen de su texto. Toma una regla como esta, que es razonable y que probablemente acabarás escribiendo:

```json
{
  "permissions": {
    "allow": ["Bash(python -m pytest *)"]
  }
}
```

La regla aprueba `python -m pytest tests/`, y es lo correcto. Pero pytest ejecuta todos los `conftest.py` que encuentra, y un `conftest.py` es código Python cualquiera: puede leer `~/.ssh`, descargar un script, escribir fuera del proyecto. Lo mismo vale para una dependencia comprometida instalada con `pip install` o con `npm install`. El permiso dijo que sí al comando correcto, y el comando hizo otra cosa. El sandbox es la red de seguridad que aguanta incluso cuando la decisión sobre los permisos fue equivocada.

## 2.10 El sandbox en detalle

Con el sandbox activo, los valores por defecto son estos:

| Acceso | Por defecto con el sandbox activo | Se cambia con |
| --- | --- | --- |
| Escritura | Solo el directorio de trabajo, una carpeta temporal personal y las carpetas que añadas. Los archivos de configuración de Claude Code siguen protegidos | `filesystem.allowWrite`, `filesystem.denyWrite` |
| Lectura | Casi todo el ordenador, incluidas credenciales como `~/.ssh` | `filesystem.denyRead`, `credentials` |
| Red | Ningún acceso directo: todo pasa por un proxy local que controla cada dominio, y la lista de dominios permitidos empieza vacía | `network.allowedDomains`, `network.deniedDomains` |
| Variables de entorno | Heredadas de Claude Code | `credentials` |

Dos filas merecen un comentario. Los archivos de configuración de Claude Code siguen protegidos incluso dentro de la carpeta del proyecto, así que un comando no puede escribirse a sí mismo un `.claude/settings.json` más permisivo. La lectura, en cambio, es permisiva: por eso conviene denegar de forma explícita las carpetas con credenciales. En cuanto a la red, un comando dentro del sandbox no tiene una vía directa hacia internet. Pasa por un proxy que corre en tu máquina, y la primera vez que hace falta un dominio nuevo Claude Code te pregunta si lo permites.

El mecanismo depende del sistema operativo:

| Sistema | Mecanismo | Notas |
| --- | --- | --- |
| macOS | Seatbelt, integrado en el sistema | No hay que instalar nada |
| Linux | bubblewrap para el sistema de archivos, socat para la red | `sudo apt-get install bubblewrap socat` |
| WSL 2 | Igual que Linux | No funciona en WSL 1 |
| Windows nativo | No soportado | Los comandos se ejecutan sin sandbox: usa WSL 2 |

Si trabajas en Windows, este es uno de los motivos más concretos para instalar Claude Code dentro de WSL 2, como se sugería en el capítulo 1.

### La prueba

En el proyecto `cc-advanced-lab`, con Claude Code arrancado, escribe `/sandbox` y pulsa Intro. Se abre un menú: elige la opción con auto-allow (en la versión con la que escribí el capítulo es `Sandbox BashTool, with auto-allow`). Claude Code responde con `Sandbox enabled with auto-allow for bash commands`. En modo auto-allow, los comandos que se ejecutan dentro del sandbox arrancan sin pedirte confirmación, porque el límite lo garantiza el sistema operativo.

Ahora pídele a Claude que ejecute dos comandos, uno por prompt:

```text
ejecuta en el terminal este comando: touch ~/sandbox-probe
```

```text
ejecuta en el terminal este comando: curl --noproxy '*' https://example.com
```

El primero intenta escribir en tu home, fuera del proyecto, y falla con `Operation not permitted` en macOS o `Read-only file system` en Linux. El segundo intenta salir a internet saltándose el proxy, y falla con `Could not resolve host`.

En este punto Claude puede proponerte reintentar el comando fuera del sandbox. En Manual ves una petición de confirmación: recházala. En auto mode, cuando grabé la lección, Claude reintentó el `touch` fuera del sandbox por iniciativa propia, y el clasificador lo bloqueó con el banner `bash denied by auto mode`. Los dos niveles actuaron uno detrás del otro, tal como en la figura. Al final, comprueba:

```bash
ls ~/sandbox-probe
```

Tiene que responder que el archivo no existe.

El menú de `/sandbox` guarda la elección en el `.claude/settings.local.json` del proyecto, el archivo de ajustes locales que no va a Git. Si quieres el sandbox activo en todos tus proyectos, con algunas reglas más, la configuración equivalente va en `~/.claude/settings.json`:

```json
{
  "sandbox": {
    "enabled": true,
    "allowUnsandboxedCommands": false,
    "filesystem": {
      "denyRead": ["~/.ssh", "~/.aws"]
    },
    "network": {
      "allowedDomains": ["github.com", "*.npmjs.org", "pypi.org"]
    }
  }
}
```

`allowUnsandboxedCommands` a `false` cierra la vía de escape que acabas de ver: si un comando falla dentro del sandbox, Claude no puede pedir reintentarlo fuera. `denyRead` impide que los comandos de shell lean las claves SSH y las credenciales de AWS. `allowedDomains` permite de entrada los dominios que usas a diario, para que no te los pregunte uno por uno.

::: {.callout .callout-warning}
[Atención]{.callout-title}

El sandbox cubre solo los comandos de shell y los procesos que lanzan. `Read` y `Edit` siguen las reglas de permisos, no el sandbox. Los hooks y los servidores MCP se ejecutan fuera del sandbox con tus permisos de usuario. Lo mismo vale para los comandos excluidos: algunas herramientas, como `docker`, no funcionan dentro del sandbox, y puedes listarlas en `sandbox.excludedCommands` (por ejemplo `"docker compose *"`), sabiendo que desde ese momento tienen acceso a todo lo que puedes hacer tú.
:::

### Sandbox, contenedor y máquina virtual

Si quieres un límite alrededor de todo Claude Code, hooks y servidores MCP incluidos, el sandbox no basta: hay que aislar el proceso entero.

| Solución | Qué aísla | Cuándo usarla |
| --- | --- | --- |
| Sandbox de Claude Code | Los comandos de shell y los procesos que lanzan | El trabajo diario en tu ordenador |
| Dev container | Todo Claude Code, dentro de un contenedor con un firewall | Proyectos que no conoces, entornos reproducibles para el equipo |
| Contenedor o VM dedicados | Todo, incluidos hooks y servidores MCP | Ejecuciones autónomas sin supervisión, CI |

`bypassPermissions` solo tiene sentido en la tercera fila. En tu portátil, con tus claves SSH y tu navegador con la sesión iniciada, la combinación razonable es auto mode o Manual con el sandbox activo.

## 2.11 Modelo y effort

La última pieza del modelo mental es el cerebro del bucle. Dos ajustes deciden qué modelo razona y cuánto.

`/model` muestra los modelos disponibles para tu plan y el que está activo. Mientras escribo hay cuatro alias: `opus` (Claude Opus 5.5, el predeterminado), `sonnet` (Claude Sonnet 5.5), `haiku` (Claude Haiku 5.5) y `fable` (Fable 5.1, el más capaz, nunca activo por defecto), todos con una ventana de contexto de un millón de tokens. Los valores por defecto cambian a menudo, y un nombre impreso en un libro envejece rápido: comprueba siempre con `/model` qué estás usando de verdad.

`/effort` regula cuánto razona Claude antes de responder. Se elige con un selector entre `low`, `medium`, `high`, `xhigh` y `max`; en los modelos 5.5 el valor por defecto es `medium`, y `max` solo vale para la sesión en curso. Más alto significa respuestas más precisas en los problemas difíciles, pero también más lentas y con más consumo del plan, y en un bucle agéntico el coste se multiplica por cada vuelta. Una regla práctica:

| Trabajo | Effort |
| --- | --- |
| Preguntas rápidas, cambios pequeños, renombrar una variable | `low` o `medium` |
| Diseño, bugs difíciles, especificaciones SDD | `high` |
| Un único prompt difícil en una sesión normal | `ultrathink` en el mensaje |

Escribir `ultrathink` dentro de un prompt sube el razonamiento solo para ese mensaje, sin tocar el ajuste. Frases como "think hard" o "piénsalo bien" no son palabras clave: el modelo las lee como texto cualquiera. El nivel activo aparece en el logo y en el spinner mientras Claude trabaja.

En el resto del libro no te diré que cambies el effort en cada capítulo. Cuando importa, por ejemplo al escribir las especificaciones de la Photogallery (capítulo 18), lo encontrarás indicado.

## Resumen {.unlisted}

- Un LLM recibe texto y devuelve texto; un agente es un LLM que trabaja en un bucle, usando tools para reunir contexto, actuar y verificar.
- El modelo nunca ejecuta nada: produce un `tool_use`, y el harness, o sea, Claude Code, comprueba permisos y hooks, ejecuta el tool y devuelve un `tool_result`.
- `Ctrl+O` muestra las llamadas una a una: úsalo cuando quieras comprobar qué ha hecho Claude además de lo que te ha contado.
- Las sesiones arrancan en auto mode; `Shift+Tab` pasa a Manual, Accept edits y Plan.
- Los permisos deciden si una acción puede ejecutarse y valen para todos los tools; el sandbox, que se activa con `/sandbox`, limita archivos y red de los comandos de shell, y lo aplica el sistema operativo.
- El modelo se elige con `/model` y el razonamiento con `/effort`; para un solo prompt difícil basta con `ultrathink`.

## Ejercicio {.unlisted}

En el proyecto `cc-advanced-lab`, con el virtualenv activo, arranca Claude Code en Manual:

```bash
claude --permission-mode manual
```

Pide:

```text
añade en src/report.py una función media(path) que devuelva la media de las ventas, con un test, y comprueba que pasan todos los tests
```

Aprueba las peticiones una a una y, para cada una, apunta el tool y la fase del bucle (contexto, acción, verificación). Al terminar, abre `Ctrl+O` y compara tu lista con las llamadas registradas.

Después activa `/sandbox` con auto-allow y pídele a Claude que ejecute `curl -sI https://pypi.org`. Observa qué pasa con la primera petición a un dominio que todavía no está permitido.

El ejercicio está terminado cuando `pytest -q` responde `3 passed`, `git diff` muestra cambios solo en `src/report.py` y `tests/test_report.py`, y tienes una lista ordenada de las llamadas que ha hecho Claude con la fase de cada una.
