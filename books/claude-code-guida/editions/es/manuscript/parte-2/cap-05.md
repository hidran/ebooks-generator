# Capítulo 5. De CSV a Excel, informes tabulares con Python

::: {.chapter-goals}
[Qué aprenderás]{.callout-title}

En este capítulo tomas el CSV del Capítulo 4 y lo conviertes en un archivo Excel listo para entregar: encabezados con formato, una hoja de resumen con totales en fórmula, un gráfico y un script que lo regenera el mes siguiente con un solo comando. El trabajo lo hace un script de Python con openpyxl, escrito por Claude y pulido en cuatro rondas de prompts.

[Requisitos previos]{.callout-title}

Python 3 con `pip` y el archivo `saas_metrics.csv` del Capítulo 4 en la carpeta `data/` del proyecto. Cualquier CSV con datos estructurados sirve igual, pero tendrás que adaptar los nombres de las columnas en los prompts.

:::

Cada plataforma de Business Intelligence promete jubilar a Excel, y Excel sigue ahí. Tableau, Power BI, Looker y Metabase funcionan bien, pero piden cuentas y configuración. Excel, en cambio, el responsable comercial ya lo tiene abierto en el portátil, y el cliente abre el adjunto sin instalar nada. Si entregas un `.xlsx` bien hecho, no le pides a nadie que cambie de herramienta.

El problema es que un Excel decente cuesta trabajo. El `df.to_excel()` de pandas genera una hoja plana, sin formato ni fórmulas. Un informe para enviar a un cliente tiene encabezados de color, columnas con el ancho justo, filas alternas, una hoja de resumen y otra con los gráficos. A mano son horas, y hacerlo con código significa estudiarse las APIs de openpyxl o xlsxwriter, que no son las más amigables.

Con Claude Code el flujo queda así: describes el informe que quieres, Claude escribe el script, tú lo ejecutas y abres el archivo. Si algo no te convence, escribes otro prompt. Y el script se queda en el repositorio, versionado: el mes siguiente, con un CSV nuevo o para otra región, lo vuelves a ejecutar con otro argumento y tienes el mismo informe actualizado.

## 5.1 Por qué pasar por un script de Python

Excel importa un CSV por sí solo, y medio mundo tiene un botón de "exportar a xlsx". El script de por medio se justifica por tres motivos.

El primero es la repetibilidad. La exportación manual la repites en cada actualización del dataset, siempre con los mismos clics. El script lo escribes una vez y después lo ejecutas.

El segundo es la transformación. Un CSV en bruto casi nunca está listo para un informe: hay columnas que renombrar, fechas que convertir, agregaciones que calcular. pandas hace todo eso en pocas líneas antes incluso de abrir el archivo Excel. La alternativa es repetir los mismos pasos dentro de Excel en cada actualización.

El tercero tiene que ver con el archivo que obtienes. Cuando Excel importa un CSV, obtienes valores. Un script con openpyxl puede escribir fórmulas. Un total calculado en Python es un número fijo; un total escrito como `=SUM(...)` se recalcula cuando alguien cambia los datos. La sección 5.4 está dedicada a esta diferencia.

### La pipeline en cuatro pasos

1. Partes de un CSV con datos en bruto. Aquí usamos `data/saas_metrics.csv`, el mismo dataset del Capítulo 4: seis meses de métricas de un producto SaaS, con las columnas `month` (1-6), `date`, `plan` (free, silver, gold), `region` (Europe, North America, Asia Pacific), `mrr` y las demás que ya exploraste.
2. Le pides a Claude un script de Python. El prompt describe el archivo de entrada, el de salida, las hojas que quieres, el estilo de los encabezados y las agregaciones. Claude escribe el script de una sola vez, con los imports, el manejo de errores y los comentarios.
3. El script usa openpyxl, la biblioteca de Python más extendida para crear y modificar archivos `.xlsx`. No necesitas Excel instalado: openpyxl escribe el formato directamente y funciona igual en macOS, Linux y Windows.
4. Ejecutas el script y abres el archivo con Excel, LibreOffice Calc o Numbers.

```bash
python tools/genera_excel.py
```

### openpyxl o xlsxwriter

Las dos bibliotecas se solapan bastante, pero tienen prioridades distintas. openpyxl lee y modifica archivos existentes además de crear otros nuevos: es la adecuada cuando tienes que actualizar una plantilla, añadir una hoja a un archivo que te enviaron o leer los datos de un Excel recibido. xlsxwriter solo escribe, pero a cambio tiene una API más cómoda para gráficos, formato condicional y tablas de Excel. Ninguna de las dos crea tablas dinámicas nativas de Excel: la tabla dinámica la calculas con pandas y la escribes como una tabla normal, que es lo que haremos.

Si nombras la biblioteca en el prompt, Claude usa esa. Si no la nombras, la elige él. Mejor decirlo y no llevarte sorpresas cuando actualices `requirements.txt`.

## 5.2 El primer prompt

Abre la terminal en la carpeta del proyecto e inicia Claude Code:

```bash
claude
```

El primer prompt tiene que decir tres cosas: dónde están los datos, adónde va la salida y cómo es el archivo. No hace falta ser exhaustivo, porque los detalles llegan con la iteración, pero cuanto más contexto des, mejor será la base de la que partes.

```text
Lee el archivo data/saas_metrics.csv. Escribe un script de Python
tools/genera_excel.py que cree un archivo output/report.xlsx con los datos
como tabla con formato.

Requisitos:
- Una sola hoja "Dati" con todas las columnas del CSV
- Encabezado con fondo azul oscuro (#1F4E78) y texto blanco en negrita
- Ancho de las columnas ajustado automáticamente al contenido
- Primera fila inmovilizada (freeze pane) para el desplazamiento
- Instala pandas y openpyxl si faltan y añádelos a requirements.txt
```

Los nombres de hoja `Dati` (datos) y `Riepilogo` (resumen) vienen del proyecto de acompañamiento. Las fórmulas que verás más adelante en el capítulo las referencian por nombre, así que mantenlos tal cual y el código coincidirá.

Claude lee el CSV, deduce las columnas, los tipos y el número de filas, y luego escribe el script. En auto mode, el modo predeterminado, el clasificador deja pasar las acciones coherentes con la petición, así que Claude crea el archivo e instala las dependencias sin detenerse en cada paso. Si prefieres ver cada diff antes de que se escriba, pasa al modo manual con `Shift+Tab` (el Capítulo 11 describe todos los modos).

Para un prompt de esta longitud también tiene sentido partir de Plan Mode, como hiciste en el Capítulo 4: pulsa `Shift+Tab` hasta que la barra de estado muestre `plan mode on`, escribe `/plan` en el prompt, o inicia la sesión con `claude --permission-mode plan`. Claude explora el CSV, te propone la estructura del script y no toca nada hasta que lo apruebes.

![Plan Mode en una petición similar escrita en inglés: Claude explora el CSV antes de proponer el script con las hojas de datos, resumen y gráficos.](figures/cap-05/fig-02.png)

### Qué sale de la primera ronda

El script está dividido en funciones: una carga el CSV en un DataFrame de pandas, otra crea el workbook y la hoja, otra escribe los encabezados con el estilo pedido, otra escribe los datos y calcula el ancho de las columnas, y una `main()` lo junta todo y guarda el archivo.

La parte que da formato al encabezado tiene este aspecto:

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

header_fill = PatternFill(
    start_color="1F4E78",
    end_color="1F4E78",
    fill_type="solid"
)
header_font = Font(bold=True, color="FFFFFF")

for col_idx, column_name in enumerate(df.columns, start=1):
    cell = ws.cell(row=1, column=col_idx, value=column_name)
    cell.fill = header_fill
    cell.font = header_font
    cell.alignment = Alignment(horizontal="center")
```

Y este es el ancho automático de las columnas:

```python
for col_idx, column in enumerate(df.columns, start=1):
    max_length = max(
        len(str(column)),
        df[column].astype(str).map(len).max()
    )
    ws.column_dimensions[get_column_letter(col_idx)].width = max_length + 4
```

Ejecutas el script y encuentras `report.xlsx` en la carpeta `output/`:

```bash
python tools/genera_excel.py
```

<!-- TODO screenshot: the "Dati" sheet of output/report.xlsx open in LibreOffice Calc or Excel after round 1 (blue header, frozen first row). Old fig-01 dropped: it showed tools/generate_report_pdf.py from the PDF chapter. -->

### Los defectos de la primera pasada

El archivo se abre, los encabezados son azules, las columnas tienen un ancho razonable. Si lo miras con ojo crítico, sin embargo, falta algo.

La columna `date` llega como texto. `2025-01-01` en el CSV es una cadena, pandas la deja así si no le pides `parse_dates`, y Excel la trata como texto: el filtro por fecha no funciona y la ordenación es alfabética.

También hay que revisar los números. Basta un valor sucio en el CSV para que `mrr` se lea como cadena, y entonces Excel no la suma.

Faltan los totales: la hoja muestra los datos en bruto y nada más. Y falta la tabla dinámica: si quieres los ingresos por plan y por mes, te la tienes que montar a mano.

## 5.3 Iterar hasta el informe

El método es sencillo: abres el archivo, miras qué falta o qué está mal, y escribes un prompt que describe solo esos cambios. Cada ronda arregla un aspecto. El primer prompt servía para arrancar y tener algo concreto que corregir, así que no tenía que ser perfecto.

### Ronda 2: la hoja Riepilogo

```text
El script genera la hoja Dati correctamente. Ahora añade:

1. Una segunda hoja "Riepilogo" con una tabla dinámica donde:
   - Las filas son los meses (ordenados cronológicamente)
   - Las columnas son los planes de suscripción (free, silver, gold)
   - Los valores son la suma del MRR (Monthly Recurring Revenue)
   - Última fila: total por columna

2. En la hoja Dati, asegúrate de que la columna mrr se escriba
   como número (float), no como cadena, y de que la columna date
   sea una fecha de Excel de verdad.
```

Claude añade una función `write_summary_sheet()`, calcula la tabla dinámica con `pivot_table()` de pandas y escribe el resultado en la hoja Riepilogo con el mismo estilo de encabezado. Al abrir el archivo ves enseguida cuánto rinde cada plan mes a mes, con el total por plan al final.

### Ronda 3: filtros y totales en fórmula

En la ronda 2 los totales son números calculados por Python. Ahora los quieres como fórmulas.

```text
Ahora quiero filtros automáticos en cada columna de la hoja Dati, y
en la hoja Riepilogo los totales del final tienen que ser fórmulas SUM
en lugar de valores hardcodeados calculados por Python.

La fórmula de la celda B[ultima_fila] de la hoja Riepilogo tiene que sumar
la columna B desde la fila 2 hacia abajo, así: =SUM(B2:B{n}).
```

Claude actualiza el script así:

```python
# Filtros automáticos en la hoja Dati
ws_dati.auto_filter.ref = ws_dati.dimensions

# Fórmulas SUM en la fila de totales de la hoja Riepilogo
last_row = len(pivot_df) + 1  # +1 por el encabezado
for col_idx in range(2, len(pivot_df.columns) + 2):
    col_letter = get_column_letter(col_idx)
    total_cell = ws_riepilogo.cell(row=last_row + 1, column=col_idx)
    total_cell.value = f"=SUM({col_letter}2:{col_letter}{last_row})"
    total_cell.font = Font(bold=True)
```

Ahora cada encabezado de la hoja Dati tiene el icono del filtro, y las celdas de los totales de Riepilogo contienen fórmulas. Ojo con lo que recalculan: suman las celdas de Riepilogo, que siguen siendo valores escritos por Python. Si alguien corrige un valor en Riepilogo, el total se actualiza; si lo corrige en la hoja Dati, no. Para conectar las dos hojas hacen falta fórmulas que lean la hoja Dati, y las encontrarás en la sección 5.4.

El autofiltro no es una Tabla de Excel propiamente dicha, la que tiene nombre y estilo y que encuentras en Insertar, Tabla. Si la necesitas, pídela explícitamente: openpyxl la crea con `openpyxl.worksheet.table.Table`.

### Ronda 4: filas alternas y gráfico circular

```text
En la hoja Dati, colorea las filas pares con un fondo gris muy claro
(#F2F2F2) para el patrón cebra. En la hoja Riepilogo añade un
gráfico circular que muestre la distribución del revenue total por plan.
```

Para las filas alternas Claude añade un bucle sobre las filas de la hoja Dati:

```python
zebra_fill = PatternFill(
    start_color="F2F2F2",
    end_color="F2F2F2",
    fill_type="solid"
)

for row_idx, row in enumerate(ws_dati.iter_rows(min_row=2), start=2):
    if row_idx % 2 == 0:
        for cell in row:
            cell.fill = zebra_fill
```

Para el gráfico circular, los datos correctos están en la fila de totales: una porción por plan.

```python
from openpyxl.chart import PieChart, Reference

total_row = last_row + 1
last_col = len(pivot_df.columns) + 1

pie = PieChart()
labels = Reference(ws_riepilogo, min_col=2, max_col=last_col, min_row=1)
data = Reference(ws_riepilogo, min_col=2, max_col=last_col, min_row=total_row)
pie.add_data(data, from_rows=True, titles_from_data=False)
pie.set_categories(labels)
pie.title = "Revenue per piano"
ws_riepilogo.add_chart(pie, "G2")
```

::: {.callout .callout-tip}
[Consejo]{.callout-title}

Comprueba siempre de dónde saca los datos un gráfico. En Riepilogo los meses están en las filas y los planes en las columnas: un gráfico circular construido sobre una columna muestra cómo se reparte un solo plan a lo largo de los seis meses, que es un gráfico distinto del que pediste. Si ves seis porciones en lugar de tres, Claude tomó la columna: díselo y haz que use la fila de totales con `from_rows=True`.
:::

<!-- TODO screenshot: the "Riepilogo" sheet after round 4, with the SUM totals row and the pie chart with three slices (free, silver, gold). -->

## 5.4 Fórmulas vivas y valores fijos

Cuando generan Excel desde código, muchos desarrolladores no piensan en lo que hará quien reciba el archivo. A simple vista, un informe con valores fijos y uno con fórmulas son idénticos; la diferencia aparece cuando el destinatario modifica una celda.

### El informe con valores fijos

Cada celda contiene un número calculado por Python. Quien abre el archivo ve todo correcto, pero si modifica un valor, el resto no se mueve: los totales siguen igual, las medias también, y el gráfico muestra los números de antes.

Para actualizarlo tienen que volver a ti: corriges el CSV, vuelves a ejecutar el script y envías un archivo nuevo. Y si el destinatario quiere plantear una hipótesis del tipo "¿y si subimos un 10% el precio del plan gold?", no puede hacerlo por su cuenta.

### El informe con fórmulas

Las celdas de los totales no contienen 12500 sino `=SUM(B2:B7)`. Los porcentajes no contienen 0,23 sino `=B8/E8`. Los gráficos están enlazados a las celdas, así que se actualizan cuando cambia un valor.

Quien lo recibe tiene en las manos una herramienta: modifica los datos en la hoja Dati, pasa a Riepilogo y ve cómo cambian los totales. La hipótesis sobre el plan gold la resuelve solo, sin llamarte.

### Cómo pedirle las fórmulas a Claude

Tienes que ser explícito. Si no lo pides, Claude tiende a calcular los valores en Python y escribirlos como números, que es el camino más simple y con menos posibilidades de equivocarse en una referencia. Para tener fórmulas, escríbelo:

```text
En la hoja Riepilogo, usa fórmulas de Excel en lugar de valores calculados en Python.
Las celdas de la tabla dinámica y de los totales tienen que contener fórmulas SUMIFS o SUM
que hagan referencia a las celdas de la hoja Dati. Los valores tienen que actualizarse
automáticamente si el usuario modifica los datos.
```

Con este prompt cada celda de la tabla dinámica se convierte en una `SUMIFS` que lee la hoja Dati: suma `mrr` donde el mes es el de la fila y el plan es el de la columna.

```python
mrr_col = get_column_letter(df.columns.get_loc("mrr") + 1)
plan_col = get_column_letter(df.columns.get_loc("plan") + 1)

# B2: MRR del mes en A2 para el plan en B1
ws_riepilogo["B2"] = (
    f"=SUMIFS(Dati!{mrr_col}:{mrr_col},"
    f"Dati!A:A,$A2,"
    f"Dati!{plan_col}:{plan_col},B$1)"
)
```

La sintaxis `NombreHoja!Columna` es la misma que usarías a mano en Excel. Sacar las letras de `df.columns` evita el error clásico de escribir `Dati!G:G` y descubrir que en el CSV del mes siguiente la columna `mrr` se ha movido. Una suma simple para un solo plan sobre toda la columna se escribe igual:

```python
cell.value = f'=SUMIF(Dati!{plan_col}:{plan_col},"gold",Dati!{mrr_col}:{mrr_col})'
```

### Cuándo usar fórmulas

Las fórmulas no siempre hacen falta. Si el archivo se genera automáticamente y nadie lo abre para modificarlo, el valor fijo va perfecto: es más fácil de escribir y no te arriesgas a referencias equivocadas.

Valen la pena cuando el destinatario se maneja bien con Excel y quiere trabajar sobre los datos, y cuando el informe tiene una vida larga y se actualiza cada mes con datos nuevos. En un informe que se lee una vez y se archiva son trabajo perdido.

Una regla práctica: si el archivo va a un manager o a un cliente que "vive en Excel", pongo fórmulas. Si va a un sistema automático o a un ingeniero que extrae los datos con código, bastan los valores.

### Excel, Google Sheets o una base de datos

Excel es el formato adecuado cuando el destinatario trabaja con adjuntos, quizá sin conexión, y el documento tiene que caber entero en un archivo sin depender de servicios externos. También lo es cuando quien lo recibe conoce Excel y no tiene ganas de aprender otra cosa.

Google Sheets tiene sentido cuando varias personas trabajan en el mismo documento a la vez, o cuando quieres un informe siempre actualizado sin enviar archivos nuevos. Se genera desde código con la API de Google Sheets, con un enfoque parecido al de este capítulo, pero con credenciales (una service account u OAuth) en lugar de una biblioteca que escribe un archivo local.

Una base de datos, o una plataforma de BI, hace falta cuando hay demasiados datos para Excel (el límite es de 1.048.576 filas por hoja, y el archivo se vuelve lento mucho antes), cuando las consultas tienen que ir rápido sobre años de histórico, o cuando varios sistemas leen los mismos datos. En esos casos Excel pasa a ser el lugar donde presentas el resultado de algunas consultas, y los datos viven en otra parte.

Para el caso de este capítulo, un informe periódico sobre datos de la empresa para personas que no escriben código, Excel es la elección correcta. El Capítulo 6 añade gráficos, un dashboard web y un informe PDF, y explica cuándo elegir cada uno.

## 5.5 Parámetros y programación

Un script que solo funciona con un archivo cuyo nombre está escrito en el código sigue siendo un prototipo. Para reutilizarlo tiene que aceptar parámetros.

### Añadir argparse

```text
Añade argparse al script. Los parámetros tienen que ser:
- --input: ruta del CSV (default: data/saas_metrics.csv)
- --output: ruta del archivo Excel de salida (default: output/report.xlsx)
- --region: filtra los datos por región (opcional, si no se indica usa todos los datos)
- --months: lista de meses que incluir, como números del 1 al 6 (opcional, default: todos)

Si el archivo de entrada no existe, el script tiene que salir con un mensaje
de error claro. Si la carpeta de salida no existe, tiene que crearla.
```

Claude añade el bloque argparse de siempre:

```python
import argparse
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Genera un report Excel da un CSV di metriche SaaS"
    )
    parser.add_argument(
        "--input",
        default="data/saas_metrics.csv",
        help="Percorso del file CSV sorgente"
    )
    parser.add_argument(
        "--output",
        default="output/report.xlsx",
        help="Percorso del file Excel di output"
    )
    parser.add_argument(
        "--region",
        default=None,
        help="Filtra per regione (es. Europe, North America)"
    )
    parser.add_argument(
        "--months",
        nargs="+",
        type=int,
        default=None,
        help="Mesi da includere (es. 1 2 3)"
    )
    return parser.parse_args()
```

Ahora el script se ejecuta con parámetros explícitos:

```bash
python tools/genera_excel.py \
  --input data/saas_metrics.csv \
  --output output/report_europe_q1.xlsx \
  --region Europe \
  --months 1 2 3
```

<!-- TODO screenshot: terminal running the command above, plus `python tools/genera_excel.py --help` showing the four options. -->

### Nombre de archivo con la fecha

Para no sobrescribir los informes anteriores, haz que ponga el mes en el nombre del archivo:

```text
Si no se indica --output, usa un nombre automático con el formato
report_YYYY-MM.xlsx basado en el mes actual.
```

Claude cambia el default de `--output` a `None` y añade:

```python
from datetime import datetime

if not args.output:
    timestamp = datetime.now().strftime("%Y-%m")
    output_path = Path(f"output/report_{timestamp}.xlsx")
else:
    output_path = Path(args.output)

output_path.parent.mkdir(parents=True, exist_ok=True)
```

Si dejara `default="output/report.xlsx"`, `args.output` nunca estaría vacío y la rama con la fecha no se ejecutaría nunca: es el tipo de detalle que hay que revisar en el diff.

### Programación con cron (macOS y Linux)

Una vez parametrizado, el script puede ejecutarse solo. En macOS y Linux la forma más sencilla es cron. Para lanzarlo el día 1 de cada mes a las 8:00, abre el crontab:

```bash
crontab -e
```

y añade esta línea:

```text
0 8 1 * * cd /percorso/assoluto/progetto && /usr/bin/python3 tools/genera_excel.py >> /tmp/genera_excel.log 2>&1
```

El `cd` hace falta porque cron arranca en tu carpeta personal, y las rutas por defecto del script (`data/saas_metrics.csv`, `output/`) son relativas a la carpeta del proyecto. Sustituye `/percorso/assoluto/progetto` por la ruta absoluta de tu proyecto. Si usas un virtualenv, cambia `/usr/bin/python3` por el Python del virtualenv, por ejemplo `.venv/bin/python`. `>> /tmp/genera_excel.log 2>&1` manda stdout y stderr a un archivo de log, así que cuando algo falla sabes dónde mirar.

### Programación con el Programador de tareas (Windows)

En Windows el equivalente es el Programador de tareas (Task Scheduler). El cmdlet de PowerShell `New-ScheduledTaskTrigger` no tiene una opción mensual, así que conviene usar `schtasks`. Primero crea en el proyecto un archivo `genera_report.bat` que se mueve a la carpeta correcta:

```bat
@echo off
cd /d C:\percorso\progetto
python tools\genera_excel.py >> output\genera_excel.log 2>&1
```

Después registra la tarea para el día 1 de cada mes a las 8:00:

```powershell
schtasks /Create /SC MONTHLY /D 1 /ST 08:00 /TN "GeneraReportExcel" /TR "C:\percorso\progetto\genera_report.bat"
```

Si el ordenador tiene que quedarse apagado, las rutinas de Claude Code ejecutan un agente en la nube según un calendario o ante un evento de GitHub (`/schedule` las crea con una conversación guiada); para un script determinista como este, de todos modos, cron o el Programador de tareas bastan.

### Envío automático por email

Si quieres que el informe llegue al buzón sin tocar nada, pídele a Claude un flag `--email`:

```text
Añade un parámetro opcional --email. Si se indica, después de generar
el archivo Excel envía un email a la dirección indicada con el archivo adjunto.
Usa smtplib y las variables de entorno SMTP_HOST, SMTP_USER, SMTP_PASSWORD
para las credenciales.
```

::: {.callout .callout-warning}
[Atención]{.callout-title}

cron no carga el perfil de tu shell, así que las variables `SMTP_*` que exportaste en `.zshrc` o `.bashrc` ahí no existen. Haz que el script las lea de un archivo `.env` excluido de Git, o defínelas al principio del crontab. En ningún caso la contraseña va escrita dentro del script.
:::

Para escenarios más elaborados, como una notificación en Slack, la subida a Google Drive o un webhook, conviene un servicio como Make o Zapier que reciba el archivo, en lugar de hacer crecer el script de Python.

::: {.callout .callout-prompt}
[Prompt reutilizable]{.callout-title}

Informe Excel con tabla dinámica y fórmulas. Sustituye los marcadores entre corchetes angulares por los nombres de tu dataset.

```text
Lee <archivo_csv>. Escribe un script de Python tools/genera_excel.py que genere
<output.xlsx> con:

1. Hoja "Dati": todos los datos del CSV como tabla filtrable (auto_filter),
   encabezado con fondo azul oscuro (#1F4E78) y texto blanco en negrita,
   ancho de columnas ajustado al contenido, freeze en la primera fila,
   zebra striping en las filas pares (#F2F2F2).

2. Hoja "Riepilogo": tabla dinámica con <campo_filas> como filas y
   <campo_columnas> como columnas, valores = suma de <métrica>.
   Fila de totales con fórmulas SUM, no valores hardcodeados.

3. Hoja "Grafici": un line chart de <métrica_temporal> a lo largo del tiempo
   desglosado por <segmentación>, un pie chart de la distribución
   total de <métrica> por <segmentación>.

Usa openpyxl. Añade argparse con --input, --output, --region (opcional).
Si no se indica --output, usa report_YYYY-MM.xlsx con timestamp automático.
Instala las dependencias y actualiza requirements.txt.
```
:::

<!-- TODO screenshot: old fig-03 dropped (VS Code with ReportLab PDF code from the PDF chapter). A replacement here could show the finished workbook with its three sheets. -->

## Resumen {.unlisted}

- Para un Excel que tendrás que repetir, haz que Claude escriba un script de Python: lo vuelves a ejecutar, lo parametrizas y lo guardas en Git.
- openpyxl lee y escribe; xlsxwriter solo escribe, pero tiene una API más cómoda para gráficos y formato condicional. En ambos casos la tabla dinámica la calculas con pandas.
- Avanza por rondas: tabla con formato, luego resumen, luego totales en fórmula, luego gráficos y filas alternas. Después de cada ronda abre el archivo y revísalo, gráficos incluidos.
- Las fórmulas solo sirven si apuntan a los datos que modifica el usuario: para un Riepilogo que siga a la hoja Dati, pide `SUMIFS` que la lean.
- Con argparse y un nombre de archivo con la fecha, el script está listo para cron o el Programador de tareas; acuérdate del `cd` a la carpeta del proyecto.

## Ejercicio {.unlisted}

Toma `data/saas_metrics.csv` del Capítulo 4, u otro CSV con datos estructurados, y recorre el capítulo en unos 20 minutos:

1. Lanza el primer prompt de la sección 5.2 y obtén la hoja Dati con formato.
2. Añade la hoja Riepilogo con la tabla dinámica (ronda 2).
3. Sustituye los totales calculados por Python por fórmulas `SUM` (ronda 3).
4. Añade argparse con `--input` y `--output`.

El ejercicio está terminado cuando ejecutas el script sobre un segundo CSV con las mismas columnas, sin tocar el código, y en el archivo nuevo la fila de totales de Riepilogo contiene fórmulas (haz clic en una celda: en la barra de fórmulas tienes que ver `=SUM(...)`).

Rama de referencia: `cap-04-excel-report` en el repositorio claude-code-book-snippets.
