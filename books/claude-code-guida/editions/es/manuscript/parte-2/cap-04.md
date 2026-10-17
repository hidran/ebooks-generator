# Capítulo 4. Analizar un CSV con Plan Mode

::: {.chapter-goals}
[Qué aprenderás]{.callout-title}

- hacer que Claude Code lea un CSV tal como está, sin prepararlo antes
- escribir prompts que saquen conclusiones de los datos, más allá de medias y desviaciones estándar
- usar Plan Mode para que Claude diseñe un análisis antes de escribir una sola línea de código
- manejar archivos grandes y convertir una sesión exploratoria en un script que puedas volver a ejecutar

[Requisitos previos]{.callout-title}

Capítulos 1-3. Python 3 instalado (lo necesitan los scripts que propone Claude, no hace falta que sepas escribirlos) y un CSV cualquiera, o bien `data/saas_metrics.csv`, que generas con el script del §4.1.

:::

Si buscas un primer trabajo de verdad para encargarle a Claude Code, un CSV es perfecto. Claude lee el archivo directamente del disco con el tool `Read`, así que no hay que copiar y pegar nada en un chat ni subir ningún archivo. Para razonar sobre el contenido usa el conocimiento del dominio que ya tiene: sabe qué es el churn rate y sabe que un aumento de tickets de soporte seguido de más cancelaciones es una señal que conviene mirar. Cuando ya has encontrado lo que buscabas, te escribe el script de Python que repite el mismo análisis el mes que viene con los datos nuevos.

El dataset del capítulo contiene métricas de un producto SaaS: tres planes de suscripción, tres regiones y seis meses de altas, cancelaciones, MRR y tickets. Empezamos abriendo el archivo y terminamos con cuatro gráficos PNG, pasando por Plan Mode. El procedimiento sirve para cualquier CSV.

## 4.1 Hacer que Claude lea el CSV

El primer paso es el más sencillo: arrancas Claude Code en la carpeta que contiene el archivo y le pides que lo lea. No hace falta convertir nada ni preparar scripts de importación.

### Situarte en la carpeta correcta

Abre la terminal y crea una carpeta de trabajo, si todavía no la tienes:

```bash
mkdir -p ~/progetti/analisi-saas
cd ~/progetti/analisi-saas
```

Pon el CSV en una subcarpeta `data/`. En los ejemplos uso `data/saas_metrics.csv`, que vas a generar en un momento con el script de la sección "El dataset de ejemplo". Después arranca Claude:

```bash
claude
```

La primera vez que abres Claude Code en una carpeta nueva te pregunta si confías en su contenido: confirma. Con una versión reciente, en el primer arranque aparece también el aviso de auto mode, el modo de permisos por defecto que viste en el Capítulo 2. Claude ejecuta por su cuenta los comandos coherentes con lo que le has pedido y un clasificador bloquea los arriesgados, así que para leer archivos o lanzar `ls` no te pregunta nada.

### Ver qué hay en la carpeta

Antes de hacerle preguntas al CSV conviene saber qué tiene alrededor. Tienes dos caminos.

El primero es el shell mode: escribes `!` al principio del prompt, seguido del comando.

```text
! ls -al
```

El comando se ejecuta en la terminal, la salida entra en la conversación y Claude la comenta. Si aparece una carpeta `.claude`, ahí dentro está la configuración del proyecto, de la que hablamos en el Capítulo 11.

El segundo es pedirlo con tus palabras:

```text
Lista los archivos que hay en esta carpeta
```

Claude lanza `ls` por su cuenta y te devuelve la lista. El resultado es el mismo: con `!` eliges tú el comando; si lo pides con palabras, lo elige él.

### El primer prompt de lectura

Para mencionar un archivo en el prompt escribe `@` seguido del nombre. Claude Code te propone las rutas que coinciden y `Tab` completa la correcta.

```text
@data/saas_metrics.csv lee el archivo y dime:
- número de filas y columnas
- nombres de las columnas
- primeros 5 valores de las columnas "plan" y "region"
- posibles valores faltantes o anómalos
```

Claude lee el archivo con `Read` y responde algo parecido a esto:

```text
El archivo data/saas_metrics.csv contiene:
- 54 filas, 12 columnas
- Columnas: month, date, plan, region, new_signups,
  cancellations, mrr, churn_rate, ai_voice_usage,
  ai_text_usage, support_tickets, retention_rate
- Valores únicos de "plan": free, silver, gold
- Valores únicos de "region": Europe, North America, Asia Pacific
- Periodo cubierto: enero - junio de 2025
- No se han detectado valores faltantes
```

Con un dataset nuevo esta es la parte más aburrida: averiguar qué columnas hay, de qué tipo son y dónde faltan datos. Normalmente se va una hora entre notebooks y `df.info()`. Aquí te cuesta un prompt, y el tiempo que te queda lo dedicas a pensar qué significan los números.

::: {.callout .callout-deep-dive}
[Bajo el capó]{.callout-title}

Claude no abre el archivo como lo haría Excel. El tool `Read` le devuelve el contenido como texto, que acaba en la ventana de contexto junto con el resto de la conversación. Un CSV de 54 filas cabe entero y ocupa muy poco; con un export de cientos de miles de filas la cosa cambia, y lo vemos en el §4.4. Cuánto contexto estás usando te lo dice `/context`, y el modelo activo lo consultas con `/model`. En octubre de 2026 el modelo por defecto es Claude Opus 5.5, con una ventana de contexto de 1M tokens, pero los valores por defecto cambian a menudo, así que comprueba siempre `/model`.
:::

### El dataset de ejemplo

Todo el capítulo usa `data/saas_metrics.csv`. Simula seis meses de métricas (enero-junio de 2025) de un producto SaaS con tres planes, free, silver y gold, que se vende en tres regiones: Europe, North America y Asia Pacific. Hay una fila por cada combinación de mes, plan y región, de ahí las 54 filas. Los números son sintéticos: para tener exactamente el mismo archivo que yo, guarda este script como `genera_dati.py` en la carpeta de trabajo y ejecútalo con `python3 genera_dati.py`.

```python
"""Genera data/saas_metrics.csv, el dataset de los capítulos 4-6."""
import csv
import random
from pathlib import Path

random.seed(2025)

PIANI = {"free": 0, "silver": 12.99, "gold": 24.99}
REGIONI = {"Europe": 1.0, "North America": 1.3, "Asia Pacific": 0.7}
ABBONATI_INIZIALI = {"free": 4000, "silver": 1200, "gold": 500}

righe = []
for regione, peso in REGIONI.items():
    for piano, prezzo in PIANI.items():
        abbonati = int(ABBONATI_INIZIALI[piano] * peso)
        for mese in range(1, 7):
            iscritti = int(abbonati * random.uniform(0.06, 0.10))
            churn = {"free": 6.0, "silver": 4.0, "gold": 1.5}[piano]
            if piano == "free" and mese == 3:
                churn += 4.0          # en marzo vencen las pruebas gratuitas
            if piano == "silver":
                churn += mese * 0.3   # el silver empeora mes a mes
            churn = round(churn + random.uniform(-0.4, 0.4), 2)
            cancellazioni = int(abbonati * churn / 100)
            ticket = int(abbonati * 0.02 + cancellazioni * (0.8 if piano == "silver" else 0.3))
            abbonati = abbonati + iscritti - cancellazioni
            righe.append({
                "month": mese,
                "date": f"2025-{mese:02d}-01",
                "plan": piano,
                "region": regione,
                "new_signups": iscritti,
                "cancellations": cancellazioni,
                "mrr": round(abbonati * prezzo, 2),
                "churn_rate": churn,
                "ai_voice_usage": int(abbonati * random.uniform(2, 6)),
                "ai_text_usage": int(abbonati * random.uniform(20, 40)),
                "support_tickets": ticket,
                "retention_rate": round(100 - churn, 2),
            })

righe.sort(key=lambda r: (r["month"], r["plan"], r["region"]))
Path("data").mkdir(exist_ok=True)
with open("data/saas_metrics.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=righe[0].keys())
    writer.writeheader()
    writer.writerows(righe)
print(f"Scritte {len(righe)} righe in data/saas_metrics.csv")
```

Vas a necesitar el mismo archivo en los capítulos 5 y 6, así que guárdalo.

Las columnas que más vas a usar:

| Columna | Descripción |
| :---- | :---- |
| `month` | Mes de referencia (1-6) |
| `date` | Fecha de inicio del mes |
| `plan` | Plan: free, silver, gold |
| `region` | Área geográfica |
| `new_signups` | Altas nuevas en el mes |
| `cancellations` | Cancelaciones en el mes |
| `mrr` | Monthly Recurring Revenue (€) |
| `churn_rate` | Tasa de abandono (%) |
| `ai_voice_usage` | Uso de la feature de voz con IA (minutos) |
| `ai_text_usage` | Uso de la feature de texto con IA (mensajes) |
| `support_tickets` | Tickets abiertos en soporte |
| `retention_rate` | Tasa de retención (%) |

Es lo bastante pequeño para caber entero en el contexto y lo bastante rico para todos los análisis de las próximas secciones.

::: {.callout .callout-prompt}
[Prompt reutilizable]{.callout-title}

Primer contacto con un dataset nuevo. Funciona con cualquier CSV, antes de empezar el análisis de verdad.

```text
Lee @<archivo.csv>. Indica:
1. Estructura: número de filas, columnas con nombre y tipo
2. Valores faltantes o anómalos
3. Patrones temporales, si hay columnas de fecha
4. Outliers evidentes en las columnas numéricas

Después dime 3 preguntas de negocio interesantes que se
pueden hacer sobre estos datos: no las respondas todavía,
primero quiero saber si son las correctas.
```
:::

## 4.2 De los números a las conclusiones

Las estadísticas descriptivas de un CSV te las da cualquier herramienta. Lo que quieres de Claude es la interpretación, y eso depende de cómo preguntes. Toma este prompt:

```text
Dame las estadísticas descriptivas del archivo
```

Obtienes una tabla con media, mediana y desviación estándar de cada columna numérica. Sirve como comprobación básica, pero no te ayuda a decidir nada. Compáralo con este:

```text
@data/saas_metrics.csv mira el CSV. ¿Cuáles son los 3 patrones
más importantes para quien gestiona un SaaS? Explícamelo en
español sencillo. Usa los números solo cuando sean lo
principal, no como relleno.
```

Aquí Claude tiene que elegir qué importa y decirlo con palabras sencillas, como haría un analista que presenta los datos a quien los va a usar. Las preguntas que siguen funcionan bien con el mismo dataset y cubren los casos más habituales.

### Tendencias temporales

```text
@data/saas_metrics.csv analiza las tasas de cancelación mes
a mes. ¿Ves una tendencia clara? ¿Hay picos anómalos
respecto a la media? ¿Qué podría explicarlos?
```

Claude busca una tendencia, la compara con la media y propone hipótesis. Con este dataset podría señalarte que el churn del plan free sube en marzo, cuando suelen vencer los periodos de prueba, que el gold se mantiene estable, y sugerirte que mires con más atención el silver, que quizá tiene un problema de propuesta de valor.

### Correlaciones

```text
@data/saas_metrics.csv ¿hay correlación entre el número de
tickets de soporte abiertos y la tasa de abandono del plan?
Si la hay, ¿en qué plan es más fuerte la correlación?
```

Claude cruza dos columnas. La respuesta suele incluir una dirección ("sí, en el plan silver más tickets van de la mano de más cancelaciones") y una hipótesis sobre qué la explica. Ten en cuenta que una correlación sobre 54 filas es un indicio, no una prueba: si la conclusión va a acabar en una decisión, pregúntale a Claude hasta qué punto es sólida y qué haría falta para confirmarla.

### Segmentación por plan

```text
@data/saas_metrics.csv ¿qué plan aporta más al MRR?
¿Hay algún plan que rinda por debajo de lo que corresponde
a su base de usuarios? Descríbelo como lo harías en una
slide para el CEO.
```

La última frase, "como lo harías en una slide para el CEO", es un truco que funciona: obliga a Claude a sintetizar, a quitar el ruido y a cerrar con una conclusión. Muchas veces puedes pegar el texto tal cual en una presentación.

### Anomalías

```text
@data/saas_metrics.csv ¿hay meses con métricas
fuera de escala respecto a la media? Identifica los outliers
y propón 2-3 explicaciones posibles para cada uno.
```

Además de señalar los valores fuera de escala, Claude razona sobre las causas plausibles. Un pico de altas en un mes puede deberse a una campaña de marketing o a un post que se ha hecho viral; un desplome de la retención puede hacer pensar en una caída del servicio o en un cambio de precio. Siguen siendo hipótesis: las compruebas tú, con quien conoce el producto.

### Plan y región a la vez

También funciona muy bien el prompt que cruza dos dimensiones de segmentación:

```text
@data/saas_metrics.csv ¿en qué combinación de plan y región
es más fuerte el crecimiento? ¿Y en cuál es más
preocupante la situación? Describe cada una con una frase
y propón una acción concreta para cada una.
```

Claude construye la matriz de plan por región, localiza las celdas que van mejor y las que van peor, y para cada una propone algo que hacer. Pedirle una acción concreta lo obliga a pasar de la descripción a la recomendación.

### Cómo iterar

La primera respuesta es un punto de partida. La vuelta que mejor funciona es esta:

1. Lanza el prompt orientado a conclusiones.
2. Lee la respuesta y elige el punto más interesante.
3. Profundiza en ese punto con una pregunta concreta: "profundiza en lo del plan silver que has mencionado: ¿tienes datos suficientes para estimar el impacto en el MRR anual?"
4. Cuando tengas algo sobre lo que se pueda actuar, pídele que lo escriba como recomendación: "escribe esta conclusión como aparecería en un informe para la dirección, tres frases como máximo".

## 4.3 Plan Mode: planificar un análisis complejo

Hasta ahora has trabajado a base de preguntas y respuestas, que para explorar va perfecto. Cuando quieres un resultado concreto, como un gráfico, un dashboard o un informe en PDF, primero necesitas un plan.

**Plan Mode** es el modo de permisos que separa la planificación de la ejecución. Claude lee los archivos, lanza los comandos que necesita para explorar y escribe un plan en pasos numerados, pero no modifica nada hasta que lo apruebas. Úsalo siempre que la tarea toque varios archivos, combine varias herramientas o produzca algo que quieres bien hecho a la primera.

### Cómo activar Plan Mode

La forma más rápida es `Shift+Tab`. Cada pulsación pasa al modo siguiente: de auto mode, que es el predeterminado, a manual, luego accept edits, luego plan, y otra vez auto. Paras cuando la línea de estado muestra `plan mode on`.

Si ya sabes que quieres empezar planificando, arranca la sesión directamente en Plan Mode:

```bash
claude --permission-mode plan
```

Desde el prompt también puedes usar el comando `/plan`, que entra en Plan Mode; si le pasas una descripción, el plan empieza enseguida.

![Una sesión que ya está en Plan Mode tras el análisis por región: `/plan` confirma que el modo está activo y que todavía no hay ningún plan](figures/cap-04/fig-01.png)

<!-- TODO screenshot: fig-01 è piccola e la riga di stato mostra il modello di allora; rifarla con la UI attuale (`/plan` in una sessione già in Plan Mode) a risoluzione piena -->

Escribir en el prompt "no escribas código, solo planifica" en una sesión normal suele dar un plan en el chat, pero el modo sigue siendo el de antes. En auto mode, con el siguiente mensaje Claude ya puede ponerse a crear archivos. La garantía de que no toca nada hasta que digas que sí solo te la da Plan Mode.

### Cuándo usarlo

La regla práctica: Plan Mode cuando quieres un resultado concreto (un archivo, un gráfico, un dashboard, un script), no para las preguntas exploratorias sobre los datos. En el ida y vuelta del §4.2 te frena sin aportar nada. Para "construye un dashboard con cuatro gráficos", úsalo siempre.

### Plan Mode en acción: el dashboard SaaS

El objetivo es un dashboard de cuatro gráficos sobre el dataset que acabas de analizar: tendencia del MRR mensual, altas por región, churn rate por plan y un heatmap del uso de las features de IA. Cambia a Plan Mode con `Shift+Tab` y envía este prompt:

```text
Analiza el archivo saas_metrics.csv y propón una estrategia
para construir un dashboard con cuatro gráficos:
- Tendencia mensual del MRR por plan (free, silver, gold)
- Altas por región mes a mes
- Churn rate comparado por plan
- Heatmap del uso de las features de IA (ai_voice_usage, ai_text_usage)

Stack: Python + matplotlib. Quiero imágenes PNG estáticas
guardadas en una carpeta docs/charts/.
No escribas código: solo planifica.
```

Claude lee el CSV, comprueba que existen las columnas que necesita cada gráfico y lanza algunos comandos de solo lectura para explorar. Con auto mode disponible, esos comandos los evalúa el clasificador en lugar de preguntarte a ti. Al cabo de unos segundos llega un plan de este estilo:

```text
Plan de implementación

1. Análisis de la estructura del CSV
   - Verificar columnas: month, plan, region, mrr, new_signups,
     churn_rate, ai_voice_usage, ai_text_usage
   - Confirmar periodo: enero-junio de 2025 (6 meses)

2. Preparación del entorno
   - Crear requirements.txt con: pandas, matplotlib, seaborn
   - Crear estructura de carpetas: data/, docs/charts/

3. Script principal dashboard.py
   - Lectura del CSV con pandas
   - Gráfico 1: tendencia del MRR (line chart, pivot por plan)
   - Gráfico 2: altas por región (grouped bar chart)
   - Gráfico 3: churn rate (line chart, pivot por plan)
   - Gráfico 4: heatmap de uso de IA (seaborn heatmap,
     eje x = meses, eje y = feature, celda = uso medio)
   - Guardado de los PNG en docs/charts/

4. Guardar el plan en docs/plan.md

5. Ejecución:
   - pip install -r requirements.txt
   - python dashboard.py
```

<!-- TODO screenshot: il piano della dashboard in Plan Mode (Python + matplotlib, docs/charts/). Sostituisce la vecchia fig-02, che mostrava un piano HTML + Chart.js + Firebase Hosting in contrasto con il testo -->

### Revisar y modificar el plan

El plan es una propuesta. Antes de aprobarlo léelo con ojo crítico: busca pasos redundantes, cosas que faltan, un stack que no te convence.

En este caso el paso 4, guardar el plan en `docs/plan.md`, es un añadido que merece la pena conservar. Dentro de dos semanas, cuando vuelvas a abrir el proyecto, ese archivo te recordará por qué tomaste ciertas decisiones, como un pequeño ADR (Architecture Decision Record) que no has tenido que escribir tú.

Para cambiar algo, sigues en Plan Mode y lo pides:

```text
En el gráfico 2, añade también una línea con el total
agregado de todas las regiones. Para el gráfico 4, usa
una paleta de colores que vaya del blanco al azul oscuro
(más uso = más oscuro). Actualiza el plan.
```

Claude actualiza el plan sin tocar el código, y puedes repetirlo hasta que te convenza. Si prefieres corregirlo a mano, `Ctrl+G` abre el plan en tu editor.

### Aprobar y ejecutar

Cuando el plan es el que quieres, Claude te pregunta cómo seguir:

- `Yes, and use auto mode`: Claude ejecuta todos los pasos en auto mode. El clasificador deja pasar las acciones coherentes con el plan y detiene las arriesgadas. Para una tarea clara y de bajo riesgo como esta es la opción adecuada. Si auto mode no está disponible, la opción se llama `Yes, auto-accept edits`.
- `Yes, manually approve edits`: Claude te pide confirmación antes de cada cambio en los archivos. Útil cuando toca archivos importantes o cuando quieres revisar las dependencias una por una.
- `No, keep planning`: sigues en Plan Mode y añades restricciones o correcciones antes de empezar.

<!-- TODO screenshot: la richiesta di approvazione del piano con le opzioni attuali (Yes, and use auto mode / Yes, manually approve edits / No, keep planning). Sostituisce la vecchia fig-03, che mostrava un piano Firebase e le opzioni di approvazione precedenti -->

Con la primera opción Claude sigue solo: crea `data/` y mueve ahí el CSV, escribe `docs/plan.md` y `dashboard.py`, lanza `pip install -r requirements.txt` y después el script. Al final tienes cuatro PNG en `docs/charts/`, listos para meterlos en cualquier documento. Si el clasificador bloquea una acción, la encuentras en `/permissions`, en la pestaña Recently denied, y desde ahí puedes volver a intentarla.

::: {.callout .callout-tip}
[Consejo]{.callout-title}

En muchas distribuciones Linux recientes y con el Python de Homebrew, `pip install` fuera de un entorno virtual se rechaza con el error `externally-managed-environment`. Añade al plan un paso que cree el entorno con `python3 -m venv .venv` e instale ahí las dependencias: Claude actualiza también los comandos de ejecución.
:::

## 4.4 Datasets grandes y contexto

El dataset de ejemplo tiene 54 filas y 12 columnas. Los que te encuentras en el trabajo son exports de un CRM, logs de eventos, datos de facturación, y llegan sin problema a cientos de miles de filas.

### El problema del contexto

Todo lo que Claude lee acaba en la ventana de contexto. Con el modelo por defecto es grande, 1M tokens, pero un export de 500.000 filas no cabe igualmente, y aunque fuera solo una parte te llenaría la sesión de números que no sirven. Con un archivo así Claude no lo lee todo de una vez: una llamada a `Read` devuelve como máximo 25.000 tokens, y un archivo de más de 256 KB hay que leerlo por partes. Lo más habitual es que Claude lo explore con `wc -l`, `head` y comandos parecidos. El análisis que obtienes se hace sobre una muestra, que para los patrones generales muchas veces basta. Cuando el detalle importa, pregúntale explícitamente cuántas filas ha leído de verdad.

Para vigilar la situación tienes `/context`, que muestra cómo se reparte la ventana: instrucciones del sistema, tools, servidores MCP, skills, archivos de memoria y mensajes. Cuando la conversación se alarga, `/compact` la resume y libera espacio, y puedes decirle qué conservar:

```text
/compact conserva las conclusiones sobre el plan silver y la estructura de columnas del CSV
```

Además vale la regla práctica de una tarea por sesión. Si después del análisis del churn pasas a una pregunta que no tiene nada que ver, `/clear` y empiezas de cero. El Capítulo 15 entra en detalle en el contexto y la memoria.

### Patrón 1: que Claude escriba el script

Con archivos grandes conviene darle la vuelta al enfoque: en lugar de hacer que Claude lea el archivo, le pides que escriba el código que lo procesa.

```text
Escribe un script de Python analisi_grandi.py que lea
saas_metrics_full.csv (potencialmente muy grande)
y genere: recuento de filas por plan, media mensual
del churn rate por región, los 10 meses con más cancelaciones.
El script tiene que funcionar también con archivos de 500.000 filas.
```

Para un requisito así Claude usa pandas leyendo el archivo por bloques (`chunksize`), declarando los tipos de las columnas (`dtype`) y cargando solo las que hacen falta (`usecols`). El script lo ejecutas tú, miras los resultados y, si alguno te llama la atención, se lo pasas a Claude en el siguiente mensaje. En el contexto entran unas pocas líneas de salida en lugar de medio millón de filas de datos.

### Patrón 2: muestras estratificadas

A veces quieres que Claude vea los datos reales antes de planificar, pero el archivo es demasiado grande para leerlo entero. Pide una muestra estratificada:

```text
Muéstrame 3 filas por cada valor único de la columna
"plan" y 3 filas por cada "region". Quiero entender
la estructura real de los datos antes de seguir.
```

Claude extrae las filas con `head`, `grep` o un par de líneas de pandas. Tienes contexto suficiente para hacer preguntas con sentido sin saturar la ventana.

### Patrón 3: guardar los resultados intermedios

Si el análisis se extiende a varias sesiones, guarda los resultados intermedios en JSON y retoma desde ahí:

```text
Guarda el resumen del análisis que acabamos de hacer
en un archivo analisi_risultati.json. Lo usaré como
punto de partida en la próxima sesión.
```

La sesión siguiente empieza así:

```text
@analisi_risultati.json retomemos el análisis
de ayer. Quiero profundizar en el dato del plan silver.
```

No empiezas de cero y el razonamiento continúa de una sesión a otra. En el Capítulo 7 verás cómo poner en `CLAUDE.md` el contexto estable del proyecto (el stack, el dataset actual, las decisiones ya tomadas), que Claude lee cada vez que arranca.

## 4.5 De conversación a script: cuándo consolidar

Después de media hora de análisis has explorado el dataset, has encontrado los patrones interesantes y quizá has visto algún gráfico. Puedes cerrar la sesión y la próxima vez empezar de cero, o bien consolidar: convertir la exploración en un script reutilizable. Claude lo hace bien porque tiene toda la conversación en el contexto y sabe qué resultados te han parecido útiles.

### El prompt de consolidación

```text
Resume todo el análisis que hemos hecho en un script de
Python analisi.py que, ejecutado sobre un CSV nuevo con la
misma estructura que saas_metrics.csv, genere:
- un informe PDF con los 4 gráficos principales (usa matplotlib
  con backend PDF)
- un CSV agregado saas_aggregato.csv con las métricas
  mensuales por plan y por región
- un archivo de texto riepilogo.txt con los patrones principales
  escritos en español para un manager no técnico

El script tiene que aceptar el nombre del archivo CSV como
argumento: python analisi.py dati_luglio.csv
```

El script que escribe Claude recoge lo que ha salido en la sesión: las agregaciones que te han servido, los gráficos que te has quedado y el nivel de detalle adecuado para el resumen en texto.

Al mes siguiente llega el CSV nuevo y no tienes que volver a abrir Claude ni repetir el análisis:

```bash
python analisi.py dati_luglio.csv
```

En pocos segundos tienes el PDF con los gráficos actualizados, el CSV agregado y el resumen. La sesión de exploración se ha convertido en una herramienta que ejecutas cuando quieras.

### Cuándo consolidar y cuándo no

Consolida si sabes que vas a repetir el mismo análisis sobre datos nuevos con la misma estructura: cada mes, cada trimestre, con archivos distintos. Si exploras un dataset una sola vez, o si las preguntas cambian cada vez, el script no compensa el tiempo que le dedicas. En ese caso basta con un resumen al final de la sesión:

```text
Resume en 5 puntos los principales hallazgos
que hemos encontrado en esta sesión.
```

Pégalo en un documento del proyecto y tendrás constancia del trabajo hecho. En el Capítulo 5 el mismo enfoque produce un informe de Excel con tablas dinámicas, fórmulas y gráficos nativos, generado en Python con openpyxl sin abrir Excel.

## Resumen {.unlisted}

- Claude lee un CSV directamente del disco con `Read`: lo mencionas con `@` y no tienes que prepararlo.
- Los prompts útiles piden patrones y conclusiones ("¿cuáles son los 3 patrones más importantes?"); las estadísticas descriptivas solo sirven como comprobación inicial.
- Para un resultado concreto entra en Plan Mode (`Shift+Tab` hasta `plan mode on`, o `claude --permission-mode plan`): Claude no modifica nada hasta que apruebas el plan.
- El plan se corrige sin salir de Plan Mode o con `Ctrl+G`; después eliges si ejecutarlo en auto mode o aprobando cada cambio.
- Con archivos grandes pide a Claude el script que los procesa, vigila `/context` y usa `/compact` indicando qué conservar.
- Si vas a repetir el análisis, consolídalo en un script que reciba el CSV como argumento.

## Ejercicio {.unlisted}

Cuatro pasos, unos diez minutos en total. Usa `data/saas_metrics.csv` generado con `genera_dati.py`, o un CSV que ya tengas en el ordenador.

1. Estructura. Arranca Claude en la carpeta del CSV y usa el prompt reutilizable de primer contacto del §4.1. Comprueba que la respuesta incluye la estructura completa y tres preguntas de negocio.
2. Conclusiones. Elige una de las tres preguntas y profundiza en ella con un prompt orientado a conclusiones. Haz al menos una vuelta más pidiendo que profundice en el punto más interesante de la respuesta.
3. Plan Mode. Cambia a Plan Mode con `Shift+Tab` y pide a Claude que planifique un gráfico que muestre el patrón encontrado en el paso 2. Modifica al menos un aspecto del plan, luego apruébalo y comprueba que se genera el gráfico.
4. Consolidación. Pide a Claude un script `analisi_rapida.py` que, recibiendo el CSV como argumento, genere el gráfico y un resumen de texto de tres líneas.

El ejercicio está terminado cuando `python analisi_rapida.py <file.csv>`, ejecutado por ti en una terminal fuera de Claude Code, genera el gráfico y las tres líneas de resumen sin errores.
