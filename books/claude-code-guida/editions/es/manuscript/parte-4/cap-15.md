# Capítulo 15. Contexto y memoria bajo control

::: {.chapter-goals}
[Qué aprenderás]{.callout-title}

- A leer cómo se llena la ventana de contexto con `/context`, `/skill-doctor` y `/usage`.
- Cuándo usar `/compact`, `/rewind`, `/fork` y `/clear` en una conversación larga.
- Qué guarda la memoria automática, dónde la encuentras y cómo la corriges o la apagas.
- A hacer que `/doctor` y `/doctor prompt-audit` revisen tu configuración y tus instrucciones.

[Requisitos previos]{.callout-title}

El proyecto `cc-advanced-lab` del capítulo 11, con lo que le añadieron los capítulos 12-14. Si te saltaste algún capítulo no pasa nada: verás menos entradas en los paneles, pero los comandos funcionan igual.

:::

En los capítulos 11-14 llenaste `cc-advanced-lab` de cosas útiles: reglas de permisos en `.claude/settings.json`, los hooks que formatean el Python y protegen `data/`, los servidores MCP, el plugin `cc-lab-toolkit`. Cada una de estas piezas ocupa algo de espacio en cada sesión, aunque no la uses. Este capítulo cierra la Parte IV con las herramientas para ver cuánto espacio, para manejar una conversación que se ha alargado demasiado y para mantener en orden las instrucciones que Claude lee al arrancar, tanto las que escribes tú como las que escribe él.

## 15.1 Qué hay en la ventana de contexto

La ventana de contexto es todo lo que el modelo ve cuando prepara la siguiente respuesta. Ahí dentro están tus mensajes y bastante más, y conviene saber qué, porque es lo que determina cómo va una sesión larga.

Hay cuatro partes. Está el system prompt, es decir, las instrucciones internas de Claude Code y las definiciones de los tools básicos (`Read`, `Edit`, `Bash`, `Agent` y los demás del capítulo 2). Están las extensiones: skills, agentes, plugins y servidores MCP. De cada una, Claude Code carga siempre el nombre y la descripción, porque es de ahí de donde el modelo saca cuándo usarla; el cuerpo de una skill llega solo cuando hace falta (lo viste en el capítulo 9). Están los archivos de memoria: `CLAUDE.md`, las reglas de `.claude/rules/` y el índice de la memoria automática. Y por último está la conversación: los mensajes, cada archivo que Claude ha leído, la salida de cada comando ejecutado.

Con Claude Opus 5.5 la ventana por defecto es de un millón de tokens, así que espacio hay de sobra (el modelo y su ventana pueden cambiar: revisa `/model`). El límite práctico llega antes que el técnico, por dos motivos. Cada turno procesa todo el contexto, así que una sesión inflada gasta más de los límites de tu plan. Y cuanto más material hay, más compiten las instrucciones y decisiones del principio con lo que llegó después: en una sesión larga y llena de temas distintos, Claude empieza a olvidar convenciones que al principio respetaba.

## 15.2 Medir con /context, /skill-doctor y /usage

Antes de gestionar el contexto conviene mirarlo. Abre `cc-advanced-lab` y ejecuta `claude`. Para que los paneles tengan algo que mostrar, haz tres preguntas de solo lectura:

```text
lee src/report.py y su test y dime qué hacen
```

```text
¿cuántas líneas tiene data/vendite.csv y qué columnas contiene?
```

```text
¿cómo se ejecutan los tests en este proyecto?
```

Son preguntas inofensivas: no modifican nada y en auto mode pasan sin pedir confirmación.

### /context

Escribe `/context`. El panel muestra cómo se reparte la ventana: cuánto ocupan el system prompt y los tools del sistema, los tools de los servidores MCP, los agentes, las skills, los archivos de memoria y los mensajes, además del espacio que queda libre.

<!-- TODO screenshot: /context in cc-advanced-lab dopo le tre domande, con le categorie system prompt, tool, MCP, skill, agent, memory files, messaggi -->

Lo primero que llama la atención es que una parte del contexto ya está ocupada antes de que escribas el primer prompt. Skills, agentes y plugins pesan aunque en esta sesión no los uses, porque el nombre y la descripción siempre están cargados. Para los servidores MCP la cuenta es más baja de lo que esperarías: gracias al tool search del capítulo 13, al arrancar Claude Code carga solo los nombres de los tools y recupera las definiciones completas cuando las necesita.

Lo segundo es la entrada de los mensajes. Después de tres preguntas es pequeña. Después de una hora de trabajo, con algunos archivos grandes leídos enteros y la salida de una suite de tests, se convierte en la entrada principal. Es la que reducen `/compact` y `/clear`.

### /skill-doctor

`/skill-doctor` responde a una pregunta concreta: ¿qué skills compensan lo que cuestan? Para cada skill muestra cuánto contexto ocupa y con qué frecuencia se usa.

Una skill ligera que usas a menudo está perfecta. Una skill con una descripción larguísima que nunca has activado es candidata a desactivarse: si es una skill del proyecto la quitas de `.claude/skills/`, y si viene de un plugin decides desde el gestor `/plugin` (capítulo 14) si todavía necesitas ese plugin. Este mismo panel es un buen motivo para mantener cortas las descripciones de las skills que escribas (capítulo 9).

### /usage

`/usage` mira lo mismo desde otro ángulo: qué gasta los límites de tu plan. El desglose va por skill, subagente, plugin y servidor MCP. Si un subagente que lanzas a menudo se lee medio repositorio en cada vuelta, aquí lo ves.

Los tres paneles se cierran con `Esc`.

## 15.3 Compactar, rebobinar, bifurcar, empezar de nuevo

Para una conversación que se ha alargado tienes cuatro herramientas: `/compact`, `/rewind`, `/fork` y `/clear`. Cada una hace algo distinto, y conviene probarlas en orden en la misma sesión para ver el efecto de cada una.

### /compact con instrucciones

`/compact` resume la conversación y libera espacio. El resumen ocupa el lugar de los mensajes más antiguos: la sesión sigue siendo la misma, pero Claude recuerda los detalles en forma condensada. El comando acepta instrucciones sobre qué conservar, y conviene dárselas siempre:

```text
/compact Conserva la estructura del proyecto, las decisiones tomadas y los tests que fallan
```

Sin instrucciones, el resumen decide por su cuenta qué guardar, y lo que a ti te parece importante (el nombre que elegiste para una función, el test que falla de forma intermitente) puede acabar en una frase genérica o desaparecer. Con instrucciones le dices qué no debe perder. En la Parte VI, cuando una fase del Photogallery se alargue, compactarás justo así: estado de las tareas, decisiones tomadas, findings todavía abiertos (capítulo 19).

Claude Code también compacta por su cuenta cuando la ventana se acerca al límite. Sirve como red de seguridad, pero una compactación automática llega cuando él decide y sin tus instrucciones. Si el proyecto necesita que ciertos datos vuelvan siempre al contexto después de una compactación, usa el hook `SessionStart` con matcher `compact` del capítulo 12.

::: {.callout .callout-tip}
[Consejo]{.callout-title}

Compacta cuando cierres una parte del trabajo, no cuando las respuestas empiecen a empeorar. Cuando una tarea está terminada y los tests pasan sabes exactamente qué merece la pena guardar, y el resumen sale mejor.
:::

### /rewind y el doble Esc

Para tener algo que rebobinar, pídele a Claude un cambio pequeño:

```text
añade al principio de src/report.py un comentario de una línea que explique qué hace el módulo
```

Ahora presiona `Esc` dos veces (o escribe `/rewind`). Se abre un menú con los puntos anteriores de la conversación, uno por cada prompt tuyo. Eliges el punto al que volver y decides qué restaurar: el código, la conversación o ambos. Además hay dos opciones de resumen, que son una compactación dirigida a una sola parte: `Summarize from here` comprime la conversación desde el punto elegido en adelante, y `Summarize up to here` la que va antes, dejando intactos los mensajes posteriores. Ninguna de las dos toca los archivos.

Las tres combinaciones sirven en situaciones distintas:

- Restauras código y conversación cuando Claude se ha ido por un camino equivocado y quieres reintentarlo con un prompt mejor, como si el intento no hubiera existido.
- Restauras solo el código cuando la discusión te sirvió (entendiste por qué el enfoque no funciona) pero los archivos tienen que volver a como estaban.
- Restauras solo la conversación cuando el cambio te vale pero el diálogo que lo produjo se fue por las ramas y ocupa espacio.

En la prueba con el comentario, restaura solo el código y luego ejecuta `git diff`: `src/report.py` ha vuelto a como estaba.

::: {.callout .callout-warning}
[Atención]{.callout-title}

Los checkpoints de `/rewind` registran los cambios hechos con los tools de edición de archivos, como `Edit` y `Write`. Lo que cambie un comando ejecutado con `Bash` (un `rm`, una migración de la base de datos) se queda como está. Las correcciones aplicadas por `/code-review --fix` (capítulo 22) tampoco se deshacen con `/rewind`. Para todo eso la red de seguridad es Git: haz commit antes de dejarle a Claude un trabajo grande.
:::

### /fork

`/fork` copia la conversación en una nueva sesión en segundo plano. La sesión principal se queda donde está, con todo su contexto, y la copia arranca desde el mismo punto. Sirve cuando quieres explorar una alternativa sin perder el hilo, por ejemplo intentar un refactoring del que no estás seguro mientras la sesión principal sigue con el código que funciona.

La copia la encuentras entre las sesiones en segundo plano, en el agent view que abrirás con `claude agents` en el capítulo 20. Recuerda que es una sesión de verdad: gasta del plan como cualquier otra.

### /clear

`/clear` empieza desde cero. La conversación desaparece del contexto y Claude Code vuelve a cargar los archivos de memoria como al arrancar. Los archivos del disco se quedan como están, porque `/clear` solo toca la conversación. Se usa cuando cambias de tema. Los hooks `SessionStart` también se disparan después de un `/clear`, con origen `clear`: un hook sin matcher, o con matcher `clear`, vuelve a meter en el contexto lo que imprime. El del matcher `compact` del capítulo 12 aquí no se ejecuta.

Si vas a hacer `/clear` a mitad de un trabajo, antes pídele a Claude que deje por escrito en un archivo hasta dónde has llegado:

```text
escribe en STATE.md lo que hemos hecho, las decisiones tomadas y lo que queda por hacer
```

Después del `/clear`, retomas con un prompt que le diga que lea `STATE.md`. En el Photogallery, el papel de `STATE.md` lo cumplen las especificaciones y `docs/TASKS.md`: están en el disco, así que entre una fase y la siguiente puedes vaciar el contexto sin perder nada (capítulos 18 y 19).

### Cuál usar

| Situación | Comando |
| --- | --- |
| La tarea sigue, la ventana está llena de detalles que ya no sirven | `/compact` con instrucciones |
| Claude ha tomado un camino equivocado y quieres volver atrás | `Esc Esc` o `/rewind` |
| Quieres probar una alternativa sin tocar la sesión principal | `/fork` |
| La tarea ha terminado y pasas a otro tema | `/clear` |

## 15.4 Una tarea, una sesión

La regla práctica que une todo lo de la sección anterior es esta: una tarea, una sesión. Las conversaciones largas sobre temas distintos son la forma más rápida de empeorar los resultados, porque cada tema deja en el contexto archivos leídos, intentos descartados y decisiones que no tienen nada que ver con la tarea siguiente.

En `cc-advanced-lab` esto significa, por ejemplo, que si acabas de arreglar un test de `src/report.py` y ahora quieres el informe semanal de ventas, haces `/clear` o abres una sesión nueva. El informe no necesita saber cómo depuraste el test, y esa depuración en el contexto solo puede confundir la petición nueva.

Lo que tiene que sobrevivir de una tarea a otra no se deja en la conversación: va a un archivo. Las convenciones estables viven en `CLAUDE.md`, el estado de un trabajo a medias en un archivo como `STATE.md` o en la lista de tareas, y las preferencias personales en la memoria automática.

## 15.5 Las instrucciones que escribes tú, en breve

El capítulo 7 explica `CLAUDE.md` a fondo: los niveles, qué poner y qué no, las reglas por ruta, AGENTS.md. Aquí basta con un recordatorio, porque las secciones siguientes vuelven sobre ello.

Hay cuatro niveles: organización (una ruta gestionada por el equipo de IT), usuario (`~/.claude/CLAUDE.md`), proyecto (`./CLAUDE.md` o `./.claude/CLAUDE.md`, compartido por Git) y local (`./CLAUDE.local.md`, fuera de Git). Mantente por debajo de doscientas líneas y escribe instrucciones verificables: "usa dos espacios de indentación" funciona mejor que "formatea bien el código". Para `cc-advanced-lab` basta con poco:

```markdown
# cc-advanced-lab

## Comandi
- Test: `python -m pytest -q`
- Formattazione: `ruff format src tests`

## Regole
- Non modificare mai i file in `data/`: lavora su copie in `tmp/`
- Ogni nuova funzione in `src/` ha un test in `tests/`

<!-- Nota per i manutentori: le regole Python stanno in .claude/rules/python.md -->
```

Las reglas que solo aplican a los archivos Python van en `.claude/rules/python.md`, con el campo `paths:` en el frontmatter, y se cargan solo cuando Claude trabaja en un archivo que coincide. El comentario HTML del final se elimina antes de llegar a Claude: es una nota para los compañeros que no cuesta contexto.

Las instrucciones se cargan al arrancar, así que después de escribir los dos archivos sal y vuelve a lanzar `claude`. Pide que lea `src/report.py`, para que entre en juego la regla de Python, y luego escribe `/memory`: verás la lista de archivos de instrucciones cargados. En `/context` esos mismos archivos aparecen en la sección Memory files, cada uno con su peso.

Dos cosas que conviene tener presentes también en este capítulo. `CLAUDE.md` orienta a Claude, pero no lo obliga: "no modifiques nunca los archivos de `data/`" es una instrucción que normalmente se respeta, mientras que el hook `protect-files.sh` del capítulo 12 bloquea siempre los cambios hechos con `Edit` y `Write`. Y si un repositorio tiene un `AGENTS.md` y ningún `CLAUDE.md`, Claude Code lee ese.

## 15.6 La memoria automática

Además de `CLAUDE.md`, que escribes tú, está la memoria automática, que escribe Claude. Ahí van tus preferencias, las correcciones que le haces mientras trabajas y el contexto del proyecto que no puede deducir leyendo el código. Claude decide por su cuenta qué merece la pena anotar, y cuando le pides explícitamente que recuerde algo, lo guarda ahí.

Pruébalo en `cc-advanced-lab`:

```text
recuerda que en este proyecto prefiero pytest con la opción -q y los mensajes de commit en español
```

Claude elige dónde escribir, crea los archivos y te avisa con un mensaje de memoria guardada. Si solo responde con palabras sin guardar nada, reformula de forma más directa: "guarda en memoria que...".

<!-- TODO screenshot: messaggio di memoria salvata dopo il prompt "ricorda che..." -->

### Dónde vive

La memoria está en tu home, bajo `~/.claude/projects/`, con una carpeta por proyecto y dentro una carpeta `memory/`. Se comparte entre los worktrees del mismo repositorio: una preferencia guardada en el worktree de una feature vale también en el checkout principal, cosa que te vendrá bien con las oleadas en paralelo del capítulo 20. Como está en tu home y no en el repositorio, tus compañeros no la ven y no te sigue a otra máquina.

El nombre de la carpeta del proyecto sale de la ruta completa del repositorio, con los separadores cambiados por guiones, así que también contiene tu nombre de usuario. Para ver su contenido sin escribir esa ruta, usa un glob desde el prompt de Claude Code (el prefijo `!` ejecuta un comando de shell):

```bash
!cat ~/.claude/projects/*cc-advanced-lab/memory/*.md
```

Verás dos archivos: `MEMORY.md` y el de las preferencias que acabas de guardar. `MEMORY.md` hace de índice. Se carga en cada sesión, hasta doscientas líneas o 25 KB, y apunta a los otros archivos, que Claude lee cuando los necesita. Si el índice supera ese límite, la parte final no entra en el contexto al arrancar.

### Leer, corregir, apagar

Son archivos Markdown normales. Puedes abrirlos con el editor, corregir una preferencia que ya no vale o borrar un archivo entero. Si Claude ha anotado algo equivocado (pasa, por ejemplo, cuando le hiciste una corrección que solo valía para un caso), lo más rápido es corregirlo a mano en el archivo.

`/memory` muestra los archivos de instrucciones cargados y la carpeta de la memoria automática. Desde ese mismo menú activas o desactivas la memoria automática. Apagarla tiene sentido en un repositorio de demostración, durante una grabación o cuando quieres que cada sesión arranque solo con lo que has escrito tú.

El interruptor de `/memory` guarda `autoMemoryEnabled` en `~/.claude/settings.json`, así que vale para todos tus proyectos. Para apagarla en un solo proyecto, escribe `"autoMemoryEnabled": false` en la configuración de ese proyecto. También existe la variable de entorno `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`, cómoda en scripts.

## 15.7 ¿CLAUDE.md o memoria automática?

Los dos mecanismos acaban en el contexto al arrancar, pero tienen un dueño distinto.

| | `CLAUDE.md` | Memoria automática |
| --- | --- | --- |
| Quién lo escribe | Tú | Claude |
| Qué contiene | Comandos, convenciones, reglas | Preferencias, correcciones, contexto |
| Dónde está | En el repositorio (o en tu home, en el nivel de usuario) | `~/.claude/projects/<proyecto>/memory/` |
| Quién lo ve | El equipo, por Git | Solo tú, en esta máquina |
| Cuándo cambia | Cuando lo editas tú | Cuando Claude anota algo o tú dices "recuerda" |

Una regla sencilla para elegir: si la información le sirve a cualquiera que trabaje en el proyecto, va en `CLAUDE.md`. El comando de los tests, la carpeta que no se toca, el formato de los mensajes de commit acordado con el equipo son instrucciones del proyecto. "Prefiero respuestas breves" o "uso pytest con `-q`" son preferencias tuyas, y su sitio es la memoria automática.

De vez en cuando abre la carpeta de la memoria y busca anotaciones que deberían estar en otro sitio. Si Claude ha aprendido de una corrección tuya que "las migraciones nunca se ejecutan contra la base de datos de producción", esa es una regla que el equipo tiene que conocer: muévela a `CLAUDE.md`, pásala por una review y bórrala de la memoria. Y si es una regla que no se debe saltar nunca, ninguno de los dos archivos basta: hace falta una regla de permisos (capítulo 11) o un hook (capítulo 12).

## 15.8 Que revisen la configuración por ti

A estas alturas `cc-advanced-lab` tiene instrucciones repartidas en bastantes sitios: `CLAUDE.md`, la regla de Python, las skills, los agentes, el plugin, la memoria automática. Mantenerlo todo coherente a mano es tedioso, y Claude Code tiene dos comandos que lo hacen por ti.

### /doctor

`/doctor` hace una revisión completa de la configuración y también puede corregir los problemas que encuentra. Entre otras cosas, mira `CLAUDE.md` y te sugiere quitar lo que Claude puede deducir solo leyendo el código, como la lista de carpetas o de dependencias. Es el mismo consejo del capítulo 7, solo que esta vez te lo da la herramienta, línea por línea. El panel se cierra con `Esc`.

### /doctor prompt-audit

`/doctor prompt-audit` profundiza en las instrucciones. Lee `CLAUDE.md`, las reglas, las skills y los agentes, y señala tres tipos de problemas: instrucciones escritas para modelos antiguos (avisos del estilo "acuérdate de leer el archivo antes de modificarlo" que hoy solo son ruido), referencias a archivos que ya no existen e instrucciones que se contradicen entre sí, quizá una en `CLAUDE.md` y la otra en una skill.

El análisis es una pasada del modelo, así que tarda unas decenas de segundos y gasta del plan como un prompt normal. Al final propone los cambios, pero no toca nada hasta que se lo pidas. Puedes comprobarlo con `git status` justo después: el working tree está como estaba.

::: {.callout .callout-example}
[Ejemplo]{.callout-title}

Imagina que en `cc-advanced-lab` el `CLAUDE.md` dice que los tests se ejecutan con `python -m pytest -q`, mientras que un agente o una skill escritos hace meses siguen usando `pytest -v`. Ninguno de los dos está mal por sí solo, pero juntos le dan a Claude dos instrucciones distintas para lo mismo. Es justo el tipo de conflicto que `prompt-audit` saca a la luz.
:::

### claude doctor desde la terminal

El mismo diagnóstico se lanza también fuera de Claude Code, desde la shell:

```bash
claude doctor
```

Muestra el estado de la instalación, los errores en los archivos de configuración y las correcciones sugeridas, sin abrir una sesión. Es el comando que hay que recordar cuando Claude Code no arranca, o arranca e ignora un `settings.json` que acabas de modificar: un JSON mal formado aparece aquí.

::: {.callout .callout-warning}
[Atención]{.callout-title}

La salida de `/doctor` y de `claude doctor` contiene la ruta de la instalación, que incluye tu nombre de usuario, y `/memory` muestra el nombre de la carpeta del proyecto, que también lo contiene. Si haces capturas o grabas la terminal para un compañero, tapa esas líneas.
:::

## 15.9 Referencia rápida de comandos

| Comando | Para qué sirve |
| --- | --- |
| `/context` | Cómo se reparte la ventana de contexto |
| `/skill-doctor` | Coste en contexto y frecuencia de uso de cada skill |
| `/usage` | Qué gasta los límites del plan, por skill, subagente, plugin y servidor MCP |
| `/compact [instrucciones]` | Resume la conversación conservando lo que indiques |
| `/rewind` o `Esc Esc` | Vuelve a un punto anterior: código, conversación o ambos |
| `/fork` | Copia la conversación en una sesión en segundo plano |
| `/clear` | Empieza con una conversación vacía |
| `/memory` | Archivos de instrucciones cargados, carpeta e interruptor de la memoria automática |
| `/doctor` | Revisión completa de la configuración, con correcciones |
| `/doctor prompt-audit` | Instrucciones obsoletas, archivos que faltan, conflictos; propone sin aplicar |
| `claude doctor` | El diagnóstico desde la shell, sin abrir una sesión |

## 15.10 De la Parte IV a los proyectos

Con este capítulo tienes todas las herramientas de la Parte IV: los permisos y el sandbox deciden qué puede hacer Claude, los hooks automatizan los controles que no quieres delegar en el modelo, MCP y los plugins lo conectan con los servicios y con el equipo, y ahora sabes medir cuánto cuesta todo eso en contexto y mantenerlo en orden.

A partir de aquí el libro cambia de ritmo. En la Parte V construyes una landing page desde la idea hasta el deploy en Firebase, y en la Parte VI el Photogallery, una aplicación Laravel y React con 124 tareas repartidas en 14 fases. Son proyectos largos, hechos de muchas sesiones: usarás `/compact` con instrucciones cuando una fase se alargue, `/clear` antes de empezar la siguiente y un `CLAUDE.md` corto que cada sesión nueva vuelve a leer al arrancar.

## Resumen {.unlisted}

- `/context` muestra cómo se reparte la ventana; skills, agentes y plugins ocupan espacio aunque no los uses, porque el nombre y la descripción siempre están cargados.
- `/skill-doctor` te dice qué skills pesan sin que se usen, y `/usage` qué gasta los límites del plan.
- `/compact` con instrucciones cuando la tarea sigue, `Esc Esc` para volver atrás, `/fork` para una alternativa en segundo plano, `/clear` cuando cambias de tema. Los checkpoints no cubren los comandos `Bash`: para eso está Git.
- Una tarea, una sesión: lo que tenga que sobrevivir va a un archivo (`CLAUDE.md`, `STATE.md`, la lista de tareas).
- La memoria automática la escribe Claude en `~/.claude/projects/<proyecto>/memory/`, con `MEMORY.md` como índice cargado hasta doscientas líneas; la corriges a mano y la apagas desde `/memory`.
- `/doctor` y `/doctor prompt-audit` mantienen limpia la configuración; `claude doctor` funciona incluso cuando Claude Code no arranca.

## Ejercicio {.unlisted}

En `cc-advanced-lab`, con el trabajo de los capítulos 11-14 en su sitio:

1. Arranca `claude`, haz las tres preguntas de solo lectura de la sección 15.2 y anota en `/context` cuánto pesan los mensajes, las skills y los archivos de memoria. Ejecuta `/skill-doctor` y apunta la skill que más pesa en relación con su uso.
2. Pídele a Claude que añada un comentario al principio de `src/report.py`, luego usa `Esc Esc` y restaura solo el código. Comprueba que `git status` no muestra cambios en `src/report.py`.
3. Pídele a Claude que recuerde una preferencia tuya (por ejemplo, los mensajes de commit en español). Busca el archivo en la carpeta de la memoria, corrige la preferencia a mano (por ejemplo, añade que el mensaje debe empezar con un verbo en imperativo), haz `/clear` y pídele a Claude un mensaje de commit para un cambio cualquiera.
4. Ejecuta `/doctor prompt-audit` y lee el informe sin aplicar nada.

El ejercicio está completo cuando el mensaje de commit del punto 3 respeta la preferencia que corregiste a mano y `git status`, después del punto 4, muestra el mismo estado que antes de la auditoría.
