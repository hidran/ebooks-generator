# Capítulo 14. Plugins y marketplaces, empaquetar skills, agentes y hooks

::: {.chapter-goals}
[Qué aprenderás]{.callout-title}

Aprenderás a instalar un plugin del marketplace oficial sabiendo cuánto te cuesta en contexto y de quién te estás fiando, y después a construir el tuyo: `cc-lab-toolkit`, que reúne la skill `report-pdf` del capítulo 9, un agente de revisión de Python y el hook de formateo del capítulo 12. Lo compartes con tu equipo a través de un marketplace y, al final, mides con `claude plugin eval` si de verdad sirve.

[Requisitos previos]{.callout-title}

El proyecto `cc-advanced-lab` de los capítulos 11-13, con la skill `.claude/skills/report-pdf/SKILL.md` y el script `.claude/hooks/format-python.sh`. Git 2.31 o posterior, que `claude plugin eval` necesita (compruébalo con `git --version`). Una carpeta vacía `~/cc-plugins` en la que trabajar.

:::

## 14.1 Por qué un plugin

En los últimos capítulos has ido acumulando piezas: una skill en `.claude/skills/`, un agente en `.claude/agents/`, un hook registrado en `.claude/settings.json` con su script en `.claude/hooks/`, quizá un servidor MCP en `.mcp.json`. Cada una funciona perfectamente por separado, dentro del proyecto en el que la creaste.

El problema llega el día en que quieres lo mismo en un segundo proyecto, o un compañero te lo pide. Entonces copias carpetas a mano y pegas trozos de `settings.json` intentando no romper el JSON que ya estaba. Al cabo de un mes hay tres copias y nadie sabe cuál es la buena.

Un **plugin** es la respuesta de Claude Code a ese problema. Es una carpeta que contiene esos componentes más un pequeño archivo de manifest, y Claude Code la carga como una sola unidad. Se instala con un comando, se actualiza cambiando el número de versión y se desactiva sin tocar los archivos del proyecto. Dentro cabe todo lo que has visto en la Parte III y en esta parte:

- skills y agentes, que llevan el nombre del plugin como prefijo;
- hooks, es decir, las automatizaciones deterministas ligadas a los eventos de Claude Code;
- servidores MCP, declarados en un `.mcp.json` en la raíz del plugin.

En el capítulo 8 ya usaste un plugin como usuario: Superpowers. Al instalarlo recibiste de una vez un grupo de skills, sin copiar nada. En este capítulo te pasas al otro lado del mostrador y escribes uno.

## 14.2 El gestor /plugin y el marketplace oficial

Abre Claude Code en cualquier proyecto y escribe:

```text
/plugin
```

Se abre el gestor de plugins, con las pestañas Discover, Installed y Marketplaces. Pasas de una a otra con las flechas.

- Discover lista los plugins disponibles en los marketplaces que has añadido.
- Installed muestra lo que tienes instalado y de dónde viene; desde aquí desactivas o eliminas un plugin.
- Marketplaces lista las fuentes registradas: el oficial, los que has añadido tú, el del equipo.

Cuando un plugin no se carga, el motivo aparece en la pestaña Errors del mismo gestor.

El marketplace oficial de Anthropic, `claude-plugins-official`, se añade solo en el primer arranque: no tienes que registrarlo. Existe además un marketplace de la comunidad, `claude-community`, que puedes añadir cuando necesites algo que no encuentras en el oficial. Si sigues un tutorial que te hace añadir `anthropics/claude-code` como marketplace, ten en cuenta que es solo un marketplace de demostración: sirve para curiosear, no para trabajar.

El propio Superpowers del capítulo 8 está hoy en el marketplace oficial y se instala con `/plugin install superpowers@claude-plugins-official`.

<!-- TODO screenshot: gestore /plugin sulla scheda Discover, con il dettaglio di un plugin ufficiale e la stima del costo in contesto -->

### El coste en contexto

Antes de instalar nada, abre el detalle del plugin en Discover y mira la estimación del coste en contexto. Un plugin activo carga en cada sesión el nombre y la descripción de cada una de sus skills y de cada uno de sus agentes, aunque no los uses nunca. El cuerpo de una skill entra en el contexto solo cuando la skill se activa, pero las descripciones están siempre: es el mismo mecanismo que viste en el capítulo 9, multiplicado por todos los componentes del plugin.

Un plugin con dos skills pesa poco. Una colección de cuarenta skills, de las que usas tres, te ocupa un trozo de la ventana de contexto en cada sesión y multiplica las ocasiones en que una skill se activa cuando no debería. En el capítulo 15 verás cómo leer ese peso con `/context` y cómo averiguar, con `/skill-doctor` y `/usage`, qué skills y qué plugins compensan lo que cuestan.

### De quién te fías

Lo segundo que miro es quién publica el plugin. Un plugin ejecuta código con tus permisos: sus hooks lanzan comandos en tu máquina cada vez que se dispara el evento al que están ligados, y un servidor MCP declarado en el plugin es un proceso que arranca con la sesión. Como viste en el capítulo 11, los hooks y los servidores MCP quedan fuera del sandbox de comandos: solo obedecen a los permisos. Un hook dentro de un plugin descargado de un repositorio desconocido tiene el mismo poder que un script que lanzas tú desde la terminal.

El marketplace oficial es el punto de partida razonable; el de la comunidad ya pide algo más de atención. Para todo lo demás sigo una regla sencilla: antes de instalar abro el repositorio, leo `hooks/hooks.json` y los scripts a los que llama, y reviso el `.mcp.json` si lo hay. Son pocos archivos y se leen en cinco minutos.

En el marketplace oficial también encuentras plugins dedicados precisamente a la seguridad: `security-guidance`, que revisa los cambios de Claude mientras trabaja, y Claude Security, que hace un análisis de vulnerabilidades con varios agentes y propone los parches.

### Instalar plugin-dev

El primer plugin que instalo es `plugin-dev`, del marketplace oficial: añade skills y agentes para escribir los componentes de un plugin (skills, hooks, servidores MCP) y para validar el resultado, y lo dejo como ayuda para el resto del capítulo. Puedes seleccionarlo en Discover o instalarlo directamente desde el prompt:

```text
/plugin install plugin-dev@claude-plugins-official
```

Una vez instalado, `/plugin-dev:create-plugin` seguido de la descripción del plugin que quieres inicia una conversación en la que Claude lo diseña, lo crea y lo valida contigo. Aquí vas a escribir el plugin a mano, porque necesitas ver cada pieza.

La sintaxis es siempre la misma: nombre del plugin, arroba, nombre del marketplace. Claude Code te muestra los componentes del plugin y después te pregunta el scope de la instalación, con la misma lógica que viste para los servidores MCP en el capítulo 13:

| Scope | Se aplica a |
|---|---|
| user | todos tus proyectos |
| project | todo el equipo, a través del `.claude/settings.json` compartido en Git |
| local | solo a ti, en este repositorio |

Para un plugin de ayuda personal como `plugin-dev` elijo user. Project tiene sentido cuando quieres que cualquiera que clone el repositorio se encuentre el mismo plugin, como verás en el apartado 14.5. Cuando termine la instalación, compruébalo:

```text
/plugin list
```

`plugin-dev@claude-plugins-official` tiene que aparecer entre los plugins instalados.

Todo lo que haces desde el gestor tiene un equivalente en la terminal, útil en los scripts de setup y cuando quieres consultar el estado sin abrir una sesión:

```bash
claude plugin list
claude plugin details plugin-dev@claude-plugins-official
claude plugin disable plugin-dev@claude-plugins-official
claude plugin enable plugin-dev@claude-plugins-official
```

También están `install`, `uninstall` y `update`, y el grupo `claude plugin marketplace` con `add`, `list`, `remove` y `update`.

## 14.3 Construir cc-lab-toolkit

Ahora, tu plugin. Lo llamo `cc-lab-toolkit` porque reúne las herramientas del laboratorio: la skill que genera un informe a partir de un CSV, un agente que revisa el código Python y el hook que formatea los archivos `.py` después de cada cambio.

### La estructura

Un plugin es una carpeta con una subcarpeta `.claude-plugin/` que contiene solo el manifest, `plugin.json`. Todo lo demás va en la raíz del plugin: `skills/`, `agents/`, `hooks/` con el archivo `hooks.json` y, si hace falta, un `.mcp.json` para los servidores MCP. Crea las carpetas:

```bash
cd ~/cc-plugins
mkdir -p cc-lab-toolkit/.claude-plugin
mkdir -p cc-lab-toolkit/skills/report-pdf
mkdir -p cc-lab-toolkit/agents
mkdir -p cc-lab-toolkit/hooks/scripts
```

Te recomiendo convertir `~/cc-plugins` en un repositorio Git desde el principio (`git init`): lo necesitarás para compartirlo en el apartado 14.5 y para las evals del 14.7.

### El manifest

Crea `cc-lab-toolkit/.claude-plugin/plugin.json`:

```json
{
  "name": "cc-lab-toolkit",
  "description": "Informes a partir de CSV, revisión de código y formateo automático para proyectos Python",
  "version": "1.0.0",
  "author": {
    "name": "Hidran Arias"
  }
}
```

El único campo obligatorio es `name`, y pesa más de lo que parece: se convierte en el prefijo de todas las skills y de todos los agentes del plugin. La skill `report-pdf`, una vez dentro de `cc-lab-toolkit`, se llama `/cc-lab-toolkit:report-pdf`. El prefijo evita colisiones con skills del mismo nombre de otros plugins. Así que elige un nombre corto, en minúsculas y con guiones: lo vas a escribir a menudo.

`version` cobra importancia cuando el plugin se distribuye, porque es el número que hace llegar las actualizaciones a quien lo ha instalado. `description` es lo que tus compañeros leen en el gestor antes de decidir si lo instalan: escríbela pensando en ellos. En `author`, pon tu nombre en lugar del mío.

### La skill

La skill es la del capítulo 9. La copias tal cual en la carpeta que acabas de crear:

```bash
cp ~/cc-advanced-lab/.claude/skills/report-pdf/SKILL.md cc-lab-toolkit/skills/report-pdf/
```

Dentro del plugin la skill no cambia de formato: la misma carpeta con el nombre de la skill, el mismo `SKILL.md` con su frontmatter. Solo cambia el nombre con el que la invocas.

Si ya no tienes la skill, porque en el capítulo 11 rehiciste el laboratorio desde cero, vuelve a escribirla antes de seguir con el `SKILL.md` del apartado 9.3: es un solo archivo.

### El agente

Crea `cc-lab-toolkit/agents/python-reviewer.md`:

```markdown
---
name: python-reviewer
description: Revisa código Python en busca de errores de corrección, problemas de legibilidad y tests que faltan. Úsalo después de cambios en archivos .py.
tools: Read, Grep, Glob
model: sonnet
---

Eres un revisor de código Python senior. Para cada archivo modificado:

1. Señala los bugs de corrección con archivo y línea.
2. Señala las funciones sin tests en tests/.
3. Propón como máximo tres mejoras de legibilidad.

No modifiques archivos: devuelve solo el informe.
```

Es el mismo formato de los agentes del capítulo 10: un archivo Markdown con frontmatter (nombre, descripción, tools, modelo) y el system prompt en el cuerpo. La decisión importante está en la línea `tools`. El agente no tiene `Edit`, `Write` ni `Bash`: aunque el modelo decidiera corregir un bug, no tendría el tool para hacerlo. La última línea del prompt lo dice con palabras; la lista de tools lo garantiza.

Hay un detalle que conviene saber. En las builds nativas para macOS, Linux y WSL los tools `Grep` y `Glob` normalmente no están: Claude busca en los archivos a través de `Bash`. En esas instalaciones el agente trabaja en la práctica solo con `Read`, que basta para revisar los archivos que le nombras y sus tests. No añadas `Bash` solo para darle búsqueda: con una shell el agente también puede escribir, y la garantía de solo lectura desaparece.

La descripción sigue la regla que viste para las skills: dice cuándo usarlo ("después de cambios en archivos `.py`"), de modo que Claude pueda delegarle la revisión aunque no lo nombres.

### Los hooks

El hook de formateo del capítulo 12 tiene dos piezas: el script y su registro en el `settings.json` del proyecto. En el plugin, el script va en `hooks/scripts/`:

```bash
cp ~/cc-advanced-lab/.claude/hooks/format-python.sh cc-lab-toolkit/hooks/scripts/
```

`cp` conserva el bit de ejecución del original. Si en cambio escribes el script desde cero, acuérdate del `chmod +x`, o el hook fallará sin que veas nada. Para tenerlo a mano, el script es este:

```bash
#!/bin/bash
# Formatea con ruff los archivos Python modificados por Claude
FILE_PATH=$(jq -r '.tool_input.file_path // empty')

if [[ "$FILE_PATH" == *.py ]]; then
  ruff format "$FILE_PATH" >/dev/null 2>&1
fi

exit 0
```

El registro va en `cc-lab-toolkit/hooks/hooks.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"${CLAUDE_PLUGIN_ROOT}\"/hooks/scripts/format-python.sh"
          }
        ]
      }
    ]
  }
}
```

El formato es idéntico al de la clave `hooks` de `settings.json`: el mismo evento `PostToolUse`, el mismo matcher `Edit|Write`, el mismo tipo `command`. La única diferencia es la ruta del script. En el capítulo 12 usabas `$CLAUDE_PROJECT_DIR`, que apunta a la carpeta principal del proyecto. Aquí el script no está en el proyecto, está en el plugin, así que usas `${CLAUDE_PLUGIN_ROOT}`, que apunta a la carpeta donde está instalado el plugin. Las comillas escapadas alrededor de la variable sirven para las rutas con espacios. Una ruta absoluta como `/Users/tuonome/cc-plugins/...` solo funcionaría en tu ordenador y se rompería con el primer compañero que instale el plugin.

::: {.callout .callout-warning}
[Atención]{.callout-title}

Si en el `.claude/settings.json` de `cc-advanced-lab` todavía tienes el hook del capítulo 12, al cargar el plugin `ruff` se ejecuta dos veces después de cada cambio: una por el hook del proyecto y otra por el del plugin. No hace daño, pero es el tipo de duplicado que luego nadie recuerda haber dejado. En cuanto el hook viva en el plugin, quítalo del `settings.json` del proyecto.
:::

### El árbol final

```text
cc-lab-toolkit/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── report-pdf/SKILL.md
├── agents/
│   └── python-reviewer.md
└── hooks/
    ├── hooks.json
    └── scripts/format-python.sh
```

Para comprobar que no se te ha olvidado nada:

```bash
find cc-lab-toolkit -type f | sort
```

Tienes que ver cinco archivos: el manifest, la skill, el agente, `hooks.json` y el script. Si quisieras añadir un servidor MCP, por ejemplo el DBHub del capítulo 13, pondrías un `.mcp.json` junto a `skills/` y `agents/`, con el mismo formato que el `.mcp.json` del proyecto.

## 14.4 Probar el plugin sin instalarlo

### Validar

Antes de cargarlo, haz que revise la estructura:

```bash
claude plugin validate ./cc-lab-toolkit
```

`claude plugin validate` lee el manifest y el frontmatter de skills y agentes y te dice qué falla: un JSON mal formado, un campo `name` que falta, un frontmatter roto. No cuesta nada y te ahorra descubrir el problema más tarde, cuando el plugin sencillamente no aparece. Con `--strict` la comprobación es más estricta; con `--json` el resultado sale en un formato que puedes leer desde un script o en CI.

### Cargarlo para una sesión

Después entra en el proyecto del laboratorio y arranca Claude Code con el flag `--plugin-dir`:

```bash
cd ~/cc-advanced-lab
claude --plugin-dir ~/cc-plugins/cc-lab-toolkit
```

`--plugin-dir` carga el plugin solo para esta sesión, sin instalarlo: sin scope, sin marketplace, sin nada que desinstalar después. Es la forma correcta de trabajar con él mientras lo escribes. Cuando cierras la sesión, el plugin desaparece.

Prueba la skill con el prefijo:

```text
/cc-lab-toolkit:report-pdf data/vendite.csv
```

Con el CSV del laboratorio, tres meses de ventas, la respuesta es la tabla que pide la skill: 3 filas, total 358, mínimo 95, máximo 143, media 119,33. El PDF acaba en `output/report-vendite.pdf`, como en el capítulo 9. El total es el mismo que comprueba `tests/test_report.py`, así que además tienes una verificación cruzada.

Luego el agente:

```text
usa el agente cc-lab-toolkit:python-reviewer en src/report.py
```

El agente también lleva el prefijo del plugin. Claude lo lanza como subagente, que en las sesiones interactivas se ejecuta en segundo plano: el agente lee el archivo y los tests en su propio contexto y te devuelve solo el informe, como viste en el capítulo 10. Tarda un poco más que la skill, porque arranca un contexto nuevo que tiene que volver a leerlo todo.

Para el hook no hace falta un prompt específico: pide a Claude cualquier cambio en un archivo `.py` y mira el archivo después. Si está formateado, el hook del plugin ha funcionado. `/hooks` también te muestra el hook registrado bajo `PostToolUse`, junto a los de los archivos de configuración, e indica el origen de cada uno: para este hook, el plugin.

### Cambiar sin reiniciar

Si corriges la descripción de la skill o el prompt del agente con la sesión abierta, no hace falta salir y volver a entrar:

```text
/reload-plugins
```

recarga los archivos del plugin en la sesión actual. Si el agente parece todavía el de antes, recuerda que un subagente ya lanzado conserva su prompt: vuelve a lanzarlo.

### El error más común

El problema que más veo es un plugin que se carga sin errores pero no tiene ni skills ni agentes. Casi siempre es porque los componentes han acabado dentro de `.claude-plugin/`:

```text
cc-lab-toolkit/
└── .claude-plugin/
    ├── plugin.json
    ├── skills/          <- aquí no se cargan
    └── agents/
```

`.claude-plugin/` contiene solo el manifest. Skills, agentes y hooks van en la raíz del plugin, junto a `.claude-plugin/`, como en el árbol del apartado anterior. El nombre de la carpeta invita al error, porque parece el sitio donde meter "las cosas del plugin". Si `/cc-lab-toolkit:report-pdf` no aparece en el menú de comandos, comprueba esto lo primero y luego vuelve a ejecutar `claude plugin validate`.

## 14.5 Un marketplace para el equipo

Con `--plugin-dir` el plugin lo usas tú. Para dárselo al equipo necesitas un **marketplace**. El nombre hace pensar en una tienda, pero es solo un repositorio con un archivo `.claude-plugin/marketplace.json` que lista los plugins e indica dónde encontrarlos.

Convierte `~/cc-plugins` en un marketplace. Crea `~/cc-plugins/.claude-plugin/marketplace.json`:

```json
{
  "name": "cc-corso",
  "owner": {
    "name": "Hidran Arias"
  },
  "plugins": [
    {
      "name": "cc-lab-toolkit",
      "source": "./cc-lab-toolkit",
      "description": "Informes a partir de CSV, revisión y formateo para proyectos Python"
    }
  ]
}
```

Cuidado con no confundirte: el `.claude-plugin/` del marketplace está en la raíz de `~/cc-plugins` y contiene `marketplace.json`; el del plugin está en `~/cc-plugins/cc-lab-toolkit` y contiene `plugin.json`. La estructura completa del repositorio queda así:

```text
cc-plugins/
├── .claude-plugin/
│   └── marketplace.json
└── cc-lab-toolkit/
    ├── .claude-plugin/
    │   └── plugin.json
    ├── skills/
    ├── agents/
    └── hooks/
```

El `name` del marketplace es lo que usarás después de la arroba. `source` es la ruta del plugin, relativa a la carpeta del marketplace. Cuando tengas un segundo plugin, añades otro objeto al array `plugins` y una carpeta junto a `cc-lab-toolkit`.

### Añadir el marketplace e instalar

Arranca Claude Code normalmente, sin `--plugin-dir`, y registra el marketplace:

```text
/plugin marketplace add ~/cc-plugins
```

El comando acepta una carpeta local, como aquí, o un repositorio de GitHub con el formato `usuario/repositorio`. Lo haces una sola vez. Después instalas el plugin por nombre, arroba, nombre del marketplace:

```text
/plugin install cc-lab-toolkit@cc-corso
```

Claude Code te pregunta el scope, igual que con `plugin-dev`. A partir de aquí `/cc-lab-toolkit:report-pdf` está disponible en todas las sesiones del scope que hayas elegido, sin flags.

### Compartirlo de verdad

La carpeta local sirve para probar el marketplace contigo mismo. Para el equipo publicas `cc-plugins` en GitHub, como cualquier otro repositorio, y tus compañeros lo añaden con:

```text
/plugin marketplace add <usuario>/cc-plugins
/plugin install cc-lab-toolkit@cc-corso
```

Si el plugin es para un proyecto concreto, instálalo con scope project en ese repositorio: la elección queda en el `.claude/settings.json` compartido y quien clone el proyecto se encuentra el mismo plugin.

Las actualizaciones pasan por la versión del manifest. Corriges la skill, subes `version` en `plugin.json` de `1.0.0` a `1.1.0`, haces commit y push: quien haya instalado el plugin recibe la versión nueva en la siguiente actualización. Si cambias los archivos y te olvidas de cambiar el número, para los demás no ha cambiado nada. Yo trato el cambio de versión como parte de la modificación, en el mismo commit.

La actualización automática está activada por defecto solo para los marketplaces oficiales de Anthropic. Para un marketplace como el tuyo viene desactivada: cada compañero puede activarla desde la pestaña Marketplaces de `/plugin` (Enable auto-update), y a partir de ahí Claude Code consulta el marketplace durante la sesión y carga la versión nueva en la sesión siguiente. Si no, se actualiza a mano, primero el catálogo del marketplace y después el plugin:

```bash
claude plugin marketplace update cc-corso
claude plugin update cc-lab-toolkit@cc-corso
```

Para limpiar después de las pruebas, desde la terminal:

```bash
claude plugin uninstall cc-lab-toolkit@cc-corso
claude plugin marketplace remove cc-corso
```

## 14.6 Un plugin solo para ti

No todo merece un marketplace. Si quieres un plugin siempre activo solo para ti, en todos tus proyectos, sin publicar nada, tienes esto:

```bash
claude plugin init miei-attrezzi
```

`claude plugin init` (alias `claude plugin new`) crea el scaffolding del plugin en `~/.claude/skills/miei-attrezzi/`, es decir, en la carpeta de tus skills personales, y desde ahí lo carga en cada sesión con el nombre `miei-attrezzi@skills-dir`. El sufijo en lugar del marketplace te recuerda de dónde viene. Es el sitio adecuado para las pequeñas costumbres que al equipo no le interesan: la skill que reformatea tus notas de reuniones, el agente que te explica un stack trace como a ti te gusta.

La regla que uso para decidir: si también lo quiere un compañero, va al marketplace del equipo; si lo quiero solo yo pero en todos los proyectos, `claude plugin init`; si solo sirve en un repositorio, se queda en el `.claude/` de ese repositorio, como en los capítulos 9-12.

Para completar el panorama: desde la v2.1.287 existen también los Claude Mods, módulos de hooks escritos en JavaScript. Son un mecanismo distinto de los plugins y aquí no los trato.

## 14.7 Medir el plugin con claude plugin eval

Tienes un plugin que funciona. La siguiente pregunta es si de verdad ayuda. La prueba del apartado 14.4 te dice que la skill arranca cuando la llamas por su nombre; no te dice si Claude la usa cuando un usuario pide "hazme un resumen de las ventas" sin saber que la skill existe, ni si el resultado es mejor que el que Claude habría dado sin el plugin.

`claude plugin eval` responde a esa pregunta. Cada caso de prueba es un prompt realista más uno o varios **graders**, es decir, comprobaciones que dicen si el resultado es bueno. Un grader puede ser una expresión regular sobre la respuesta, la verificación de que se ha usado una skill concreta o un criterio que evalúa un segundo modelo ("la respuesta contiene una tabla con el total y la media correctos").

### Generar los casos con eval init

Los casos no los escribes a mano. Desde la carpeta del plugin:

```bash
cd ~/cc-plugins/cc-lab-toolkit
claude plugin eval init
```

Lo primero que te pregunta es si confías en la carpeta del plugin: es tuya, así que responde que sí. Después empieza una entrevista que dirige Claude. Te pregunta qué tiene que hacer la skill y qué peticiones no deben activarla. A la primera respondí así:

```text
La skill report-pdf genera un informe resumido a partir de un archivo CSV de ventas: filas, total, mínimo, máximo y media.
```

y a la segunda:

```text
No debe activarse con peticiones genéricas sobre código Python ni con archivos que no sean CSV.
```

La segunda respuesta es la que se suele saltar, y es la más útil. Produce los casos negativos, los que comprueban que la skill no se activa cuando no debe. Una skill con una descripción demasiado amplia pasa todos los casos positivos y, mientras tanto, se activa también con peticiones que no tienen nada que ver; sin casos negativos no te enteras.

La entrevista propone los casos y pide confirmación en cada paso. Para la primera prueba quédate con pocos: yo pedí dos casos, que bastan para ver cómo funciona. Cuando confirme que los ha escrito, sal con `/exit`.

En la raíz del plugin encontrarás una carpeta `evals/` con una subcarpeta por caso, que toma el nombre de su prompt: dentro están `prompt.md`, con el prompt y los límites de la ejecución en el frontmatter, y la carpeta `graders/`, con un archivo Markdown por cada comprobación. Un caso que tiene que preparar archivos antes de empezar tiene también un `case.yaml`. Ábrelos. El prompt tiene que parecerse a una petición real, no a la descripción de la skill reescrita; si la entrevista ha generado un prompt que ya contiene las palabras clave de la descripción, el caso mide poco y conviene reescribirlo.

```bash
find evals -type f | sort
```

### Lanzar la suite

Otra vez desde la carpeta del plugin:

```bash
claude plugin eval .
```

Cada caso se ejecuta tres veces con el plugin y tres veces sin él. Con dos casos son doce ejecuciones, más las llamadas de los graders que usan un modelo. En mi prueba, con los casos en paralelo, la suite tardó un par de minutos.

Para la grabación del curso lancé el comando con tres opciones más:

```bash
claude plugin eval . --trust-plugin --no-publish -j 4
```

`--trust-plugin` evita la pregunta de confianza sobre la carpeta en la primera ejecución, y `-j 4` hace cuatro ejecuciones en paralelo (por defecto va de una en una) y acorta la espera. `--no-publish` es la que no hay que olvidar: si usas una suscripción de claude.ai, sin esta opción el informe se publica también como artifact privado en tu cuenta, y la terminal imprime una línea `Published:` con la dirección. Con `--no-publish` te queda solo el archivo local.

### Leer la tabla

Al final la suite imprime una tabla con una fila por caso y cuatro columnas:

| Columna | Qué indica |
|---|---|
| `WITH` | el resultado de los graders en las ejecuciones con el plugin |
| `W/OUT` | el resultado en las ejecuciones sin el plugin |
| `Δ` | la diferencia entre las dos: cuánto ha mejorado el plugin el resultado |
| `COST` | cuánto ha costado el caso |

<!-- TODO screenshot: tabella finale di claude plugin eval con le colonne WITH, W/OUT, Δ, COST -->

La columna que hay que mirar es `Δ`. Un delta alto indica que el plugin marca la diferencia en ese caso. Un delta cercano a cero tiene dos explicaciones. La primera es que Claude se las arregla bien también sin el plugin: con un CSV de tres filas es plausible, y significa que esa skill ocupa contexto sin devolver gran cosa. La segunda, mucho más frecuente, es que la skill no se ha activado. En ese caso el problema es casi siempre la descripción, que no encaja con la forma en que el usuario formula la petición. Es la lección del capítulo 9 sobre la descripción como disparador, con la diferencia de que ahora tienes un número que te lo dice. Corrige la descripción, vuelve a lanzar la suite y mira si el delta sube.

Para los detalles de cada ejecución, incluidos los textos de las respuestas y los veredictos de los graders, abre el `report.html` que la suite escribe en la carpeta de resultados.

Los resultados no van al repositorio. Añade la carpeta al `.gitignore` del plugin:

```bash
echo 'evals/results/' >> .gitignore
```

Los casos de `evals/`, en cambio, sí los incluyes en el commit: son los tests del plugin, y quien lo modifique después que tú los vuelve a lanzar para comprobar que no ha empeorado nada.

### Iterar sin quemar el plan

Cada ejecución es una llamada real al modelo y consume tu plan. Una suite completa de diez casos son sesenta ejecuciones: lanzarla cada vez que retocas la descripción es una forma rápida de agotar los límites de la semana.

Mientras iteras, acota:

```bash
claude plugin eval . --case <nombre-del-caso> --runs 1 --ablation none
```

`--case` ejecuta un solo caso, `--runs 1` hace una sola ejecución en lugar de tres y `--ablation none` se salta las ejecuciones de comparación sin el plugin; la tabla muestra entonces las columnas `SCORE` y `PASS%` en lugar de `WITH`, `W/OUT` y `Δ`. Te queda una única ejecución, suficiente para ver si la skill ahora se activa. Cuando estés satisfecho, confírmalo con la suite completa y las tres ejecuciones estándar: una sola ejecución no basta para fiarte de un resultado, porque el mismo prompt puede dar respuestas distintas.

::: {.callout .callout-tip}
[Consejo]{.callout-title}

Mantén en la suite al menos un caso negativo por cada skill. Cuando amplías una descripción para que la skill se active en un caso positivo que fallaba, el caso negativo te avisa enseguida si ahora también se activa donde no debe.
:::

## Resumen {.unlisted}

- Un plugin es una carpeta con el manifest en `.claude-plugin/plugin.json` y los componentes (`skills/`, `agents/`, `hooks/hooks.json`, `.mcp.json`) en la raíz. El campo `name` es obligatorio y se convierte en el prefijo: `/cc-lab-toolkit:report-pdf`.
- Antes de instalar un plugin, mira el coste en contexto en el gestor `/plugin` y lee los hooks y los servidores MCP que trae consigo: se ejecutan con tus permisos.
- En los hooks de un plugin, la ruta del script usa `${CLAUDE_PLUGIN_ROOT}`, no `$CLAUDE_PROJECT_DIR` ni una ruta absoluta.
- `claude plugin validate` comprueba la estructura, `claude --plugin-dir` carga el plugin para una sesión y `/reload-plugins` recarga los cambios. Si faltan skills y agentes, comprueba que no hayan acabado dentro de `.claude-plugin/`.
- Un marketplace es un repositorio con `.claude-plugin/marketplace.json`: lo añades con `/plugin marketplace add`, instalas con `/plugin install <plugin>@<marketplace>` y distribuyes las actualizaciones cambiando `version` en el manifest.
- `claude plugin eval` compara los resultados con y sin el plugin: mira la columna `Δ`, itera con `--case`, `--runs 1` y `--ablation none`, y pon `evals/results/` en el `.gitignore`.

## Ejercicio {.unlisted}

Añade a `cc-lab-toolkit` una segunda skill, `csv-check`, que revise un archivo CSV y señale filas vacías, columnas que faltan y valores no numéricos en la columna de ventas, sin modificar el archivo. Sube la versión del manifest a `1.1.0`, verifica la estructura con `claude plugin validate ./cc-lab-toolkit` y pruébala en `cc-advanced-lab` con `--plugin-dir`. Después lanza `claude plugin eval init` para la nueva skill y pide al menos un caso positivo y uno negativo (por ejemplo, una pregunta sobre el código de `src/report.py`, que no debe activarla).

El ejercicio está terminado cuando `/cc-lab-toolkit:csv-check data/vendite.csv` responde que el archivo está limpio, la suite completa `claude plugin eval .` muestra un `Δ` positivo en el caso positivo y el caso negativo pasa, es decir, la skill no se activa.
