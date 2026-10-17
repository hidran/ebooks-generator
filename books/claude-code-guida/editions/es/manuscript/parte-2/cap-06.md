# Capítulo 6. Gráficos, dashboards e informes PDF

::: {.chapter-goals}
[Qué aprenderás]{.callout-title}

Del mismo CSV de los capítulos 4 y 5 sacas tres cosas distintas: una serie de gráficos de matplotlib listos para las diapositivas, un pequeño dashboard web con Flask y Chart.js, y un informe PDF generado con ReportLab. Después ves cómo elegir el formato según quién lo lea y cómo todo el pipeline puede convertirse en una skill, el tema del capítulo 9.

[Requisitos previos]{.callout-title}

Los capítulos 4 y 5 (mismo proyecto, mismo `data/saas_metrics.csv`), Python 3 y un navegador.

:::

Tienes un CSV con las métricas mensuales de un producto SaaS: MRR, churn, planes, regiones, uso de las funcionalidades. El análisis ya lo hiciste en el capítulo 4 y el Excel en el capítulo 5. Ahora tienes que enseñárselo a alguien, y el formato depende de quién sea ese alguien.

El mánager quiere un PDF en su bandeja de entrada el viernes por la mañana, para imprimirlo o adjuntarlo a una presentación sin abrir ningún programa. El equipo de producto quiere una página en el navegador donde pasar el ratón por los puntos y ocultar un plan desde la leyenda. El analista financiero quiere el Excel con los datos en bruto y la tabla dinámica, para hacer sus propias cuentas.

Claude Code genera las tres salidas a partir del mismo CSV con unos pocos prompts: instala las librerías, escribe los scripts, los ejecuta y corrige los errores. Tú decides qué tiene que salir y compruebas que los números cuadren.

## 6.1 Gráficos con matplotlib, una ronda cada vez

Un buen gráfico no sale con el primer prompt, y no hace falta que salga. Funciona mejor por pasadas: primero un gráfico cualquiera con los datos correctos, luego lo haces legible, luego fijas la resolución y las proporciones y, por último, lo produces en serie.

El orden importa. Si en la primera pasada las columnas están invertidas o los meses salen en orden alfabético, te das cuenta enseguida, antes de dedicar tiempo a fuentes y colores. Con un único prompt largo te arriesgas a obtener un gráfico precioso y equivocado, y a no notarlo.

### Ronda 1: el gráfico en bruto

Empiezas con el prompt más simple posible:

```text
Lee data/saas_metrics.csv y genera un gráfico de las tasas de
cancelación mensuales (churn rate) con matplotlib. Guárdalo como
figures/churn_mensile.png.
```

Claude lee el CSV, encuentra la columna `churn_rate`, instala matplotlib si falta y escribe un script de Python. El resultado es el gráfico por defecto: línea azul sobre fondo blanco, meses en el eje X, porcentajes en el eje Y, sin cuadrícula, sin título. Sirve para comprobar los datos. Para una presentación, no.

Si el proyecto tiene un virtualenv, díselo en el primer prompt ("usa `.venv`"); si no, las librerías acaban en el Python del sistema. En auto mode, el modo por defecto, el clasificador normalmente deja pasar el `pip install` sin preguntarte nada. En modo manual Claude te pide permiso.

### Ronda 2: legibilidad y colores

```text
Mejora el gráfico: añade un título claro ("Churn Rate Mensual
H1 2025"), etiquetas en los ejes (Mes / Churn Rate %), una cuadrícula
suave (alpha=0.3, linestyle='--'), fuente sans-serif (DejaVu Sans),
y usa los colores de marca #1f77b4 para la línea y #ff7f0e para los
marcadores. Añade una leyenda.
```

La cuadrícula suave ayuda a leer los valores sin robar protagonismo, y el título dice de entrada qué estás mirando. Los dos colores del ejemplo son el azul y el naranja por defecto de matplotlib: pon en su lugar los de tu marca. Esto es lo mínimo para mandar un gráfico a tus compañeros.

### Ronda 3: resolución y proporciones

```text
Guarda el gráfico como PNG de alta resolución en formato 16:9 para
presentaciones: plt.figure(figsize=(12, 6.75)) y
plt.savefig(..., dpi=150, bbox_inches='tight').
```

A 150 DPI, una figura de 12 por 6,75 pulgadas queda en unos 1800 por 1012 píxeles, suficiente para una diapositiva a pantalla completa. Si necesitas exactamente 1200 por 675, usa `figsize=(8, 4.5)` con los mismos DPI. `bbox_inches='tight'` recorta el espacio en blanco y evita que el título y las etiquetas queden cortados en los bordes, un defecto frecuente en los gráficos generados por script. El precio es que las dimensiones finales cambian unos pocos píxeles.

### Ronda 4: producción en serie

```text
Genera tres gráficos separados a partir del mismo CSV:
1. figures/churn_mensile.png: línea del churn rate mes a mes
2. figures/distribuzione_piani.png: gráfico de tarta con la
   distribución porcentual del MRR por plan (free, silver, gold)
3. figures/utilizzo_features.png: gráfico de barras horizontales con
   el uso de las funcionalidades principales
Usa los mismos parámetros de DPI/tamaño/estilo de las rondas anteriores.
Guarda todos los archivos en figures/ con nombres descriptivos.
```

Claude escribe un script `genera_grafici.py` que genera los tres archivos en una sola ejecución. Eso ya es un pequeño pipeline de reporting.

Los tipos de gráfico del prompt siguen la regla de quien se dedica a la visualización de datos: líneas para el churn, porque es una evolución en el tiempo; tarta para los planes, porque son partes de un total; barras horizontales para las funcionalidades, porque comparas categorías con nombres largos. Si no los indicas en el prompt, Claude suele llegar a las mismas elecciones. Si alguna no te convence, escríbela.

Un aviso sobre las funcionalidades. En el CSV de ejemplo, `ai_voice_usage` está en minutos y `ai_text_usage` en mensajes: dos barras en la misma escala parecen comparables y no lo son. Pide que las normalice (por ejemplo, con enero igual a 100) o que haga dos gráficos separados.


![Una sesión real: Claude escribió `dashboard.py`, instaló las dependencias y guardó cinco gráficos en `docs/charts/`](figures/cap-06/fig-01.png)

<!-- TODO screenshot: fig-01, fig-02 e fig-03 sono a 560x315 pixel, troppo pochi per la stampa; rifarle a risoluzione piena. In fig-01 e fig-03 la status line mostra il modello e la modalità di allora. -->

### El script, línea a línea

Los scripts que Claude genera para este tipo de trabajo casi siempre tienen la misma forma. No los vas a escribir a mano, pero saber leerlos te sirve para revisarlos:

```python
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# Carga los datos
df = pd.read_csv("data/saas_metrics.csv")

# Nueve filas por mes (plan por región): media del churn por mes.
# churn_rate ya está en porcentaje (4.2 significa 4,2 %)
churn = df.groupby("month")["churn_rate"].mean()

# Gráfico 1: churn rate
fig, ax = plt.subplots(figsize=(12, 6.75))
ax.plot(churn.index.astype(str), churn.values,
        color="#1f77b4", linewidth=2,
        marker="o", markersize=6, markerfacecolor="#ff7f0e")
ax.set_title("Churn Rate Mensile H1 2025", fontsize=16, pad=12)
ax.set_xlabel("Mese", fontsize=12)
ax.set_ylabel("Churn Rate (%)", fontsize=12)
ax.yaxis.set_major_formatter(mtick.PercentFormatter())
ax.grid(axis="y", linestyle="--", alpha=0.3)
ax.tick_params(labelsize=10)
plt.tight_layout()
plt.savefig("figures/churn_mensile.png", dpi=150, bbox_inches="tight")
plt.close()
```

Hay dos detalles que buscar cuando lo revisas. El primero es el `groupby`: el CSV tiene 54 filas, seis meses por tres planes por tres regiones, y si dibujas las filas tal cual obtienes una línea en zigzag que no significa nada. El segundo es la escala: `churn_rate` ya es un porcentaje, así que `PercentFormatter()` se usa sin multiplicar por 100. Si tu CSV guarda el churn como fracción (0.03), el script tiene que multiplicar; si no, el gráfico marca 0,03 %. Claude suele darse cuenta mirando los valores, pero compruébalo tú.

![El script `dashboard.py` abierto en el IDE, con los imports de matplotlib y seaborn y las paletas para planes y regiones](figures/cap-06/fig-02.png)

En la captura los imports aparecen subrayados con "could not be resolved" y, aun así, el script funciona: el IDE usa un intérprete de Python distinto de aquel en el que Claude instaló las librerías. Se arregla apuntando el IDE al virtualenv del proyecto.

### matplotlib, seaborn o plotly

Son las tres librerías que Claude propone más a menudo. matplotlib te da control sobre cada elemento del gráfico: pide más código, pero el resultado es predecible, y es la elección natural para PNG que van dentro de un PDF o de una diapositiva. seaborn funciona sobre matplotlib y genera gráficos estadísticos (distribuciones, heatmaps, pairplots) con menos líneas, a cambio de menos control sobre el layout. plotly hace gráficos interactivos para la web, con hover y zoom incluidos; exporta a HTML o a imagen estática, pero en los PDF queda peor.

En la práctica: matplotlib para PDF e impresión, plotly para dashboards, seaborn para el análisis exploratorio. En el resto del capítulo usas matplotlib para el PDF y Chart.js, servido por Flask, para la webapp.

## 6.2 Un dashboard con Flask y Chart.js

Los gráficos estáticos funcionan bien en un PDF. Si en cambio quieres que el equipo explore los datos por su cuenta, pasando el ratón por los puntos y leyendo el valor exacto sin abrir Excel, necesitas una página web.

Flask más Chart.js es lo mínimo que funciona. Flask expone los datos como JSON y Chart.js dibuja los gráficos en el navegador. Nada de React, nada de bundler: un archivo Python, una plantilla HTML, un CSS, y se arranca con `python app.py`. Lo construyes en cuatro pasos.

### Paso 1: el esqueleto de Flask

```text
Crea app.py en la raíz del proyecto. Debe tener:
- Una ruta GET / que renderiza templates/index.html
- Una ruta GET /api/data que lee data/saas_metrics.csv con pandas
  y devuelve un JSON con tres datasets agregados:
  {
    "churn": [{"month": 1, "value": 4.2}, ...],
    "piani": [{"piano": "gold", "pct": 35}, ...],
    "features": [{"feature": "ai_voice_usage", "utilizzo": 0.72}, ...]
  }
- Modo debug activado (app.run(debug=True))
Instala Flask y pandas si hace falta.
```

Claude escribe `app.py` con las dos rutas, agrega los datos con pandas y los serializa en JSON. La ruta `/api/data` separa los datos de la presentación: si mañana cambia el CSV, la plantilla HTML se queda como está.

### Paso 2: la plantilla con Chart.js

```text
Crea templates/index.html. Debe:
- Incluir Chart.js vía CDN (versión 4.x)
- Definir tres canvas: lineChart (churn mensual), pieChart
  (distribución de planes), featuresChart (uso de funcionalidades,
  barras horizontales)
- Al cargar la página, pedir /api/data con fetch() e
  inicializar los tres gráficos con los datos recibidos
- Añadir títulos H2 encima de cada gráfico
```

La plantilla carga los datos con `fetch('/api/data').then(r => r.json()).then(data => { ... })`, sin recargar la página, y Chart.js dibuja los gráficos a partir de los arrays que recibe. Aquí Jinja2 solo renderiza la página vacía: todos los datos llegan de la API.

### Paso 3: layout y estilo

```text
Crea static/style.css con:
- Layout grid de 2 columnas: lineChart ocupa toda la primera fila
  (grid-column: 1 / -1), pieChart y featuresChart se reparten
  la segunda fila
- Fuente Inter (vía Google Fonts) con fallback sans-serif
- Padding generoso (24px en las tarjetas), fondo gris claro (#f5f5f5),
  tarjetas blancas con border-radius 8px y box-shadow suave
- Responsive: en móvil (max-width: 768px) una sola columna
```

Para este dashboard basta con un CSS grid: sin framework, unas veinte líneas, y el resultado ya se puede enseñar.

### Paso 4: actualizar los datos sin recargar

```text
En la plantilla, añade un botón "Actualizar datos" (id="refresh-btn")
arriba a la derecha. Al hacer clic, vuelve a pedir /api/data y
actualiza los datos de los tres gráficos con
chart.data.datasets[0].data = newData seguido de chart.update().
No recargues la página.
```

Sin el botón, cuando el CSV cambia el usuario tiene que recargar la página y pierde lo que había hecho: el zoom, la serie oculta desde la leyenda. Chart.js expone `.update()` para redibujar un gráfico sin recrearlo:

```javascript
document.getElementById("refresh-btn").addEventListener("click", function () {
    fetch("/api/data")
        .then(r => r.json())
        .then(data => {
            // Actualiza los datasets de los gráficos
            lineChart.data.labels = data.churn.map(d => d.month);
            lineChart.data.datasets[0].data = data.churn.map(d => d.value);
            lineChart.update();

            pieChart.data.datasets[0].data = data.piani.map(d => d.pct);
            pieChart.update();

            featuresChart.data.datasets[0].data = data.features.map(d => d.utilizzo);
            featuresChart.update();
        });
});
```

Cambias solo `.data` y llamas a `.update()`: Chart.js anima la transición por su cuenta, sin parpadeos. El mismo esquema (fetch, actualizar los datos, update) sirve para filtros, selectores de fecha y menús desplegables. Lo único que cambia es el parámetro que pasas al endpoint.

### Arrancar y probar

```bash
python app.py
```

Abre `http://localhost:5000`. Pasas el ratón por un punto de la línea y aparece el tooltip con el valor. Haces clic en un plan de la leyenda de la tarta y lo ocultas. Pulsas "Actualizar datos" y los gráficos se actualizan sin recargar la página.

::: {.callout .callout-warning}
[Atención]{.callout-title}

En macOS el puerto 5000 suele estar ocupado por el receptor AirPlay. Si el navegador te responde con un 403 o Flask no arranca, desactiva el receptor AirPlay en los ajustes del sistema o pide a Claude que arranque la app en otro puerto, por ejemplo `app.run(debug=True, port=5001)`.
:::

¿Por qué Flask y no FastAPI o Django? Para un dashboard interno sin login y sin base de datos, una app Flask se lee en cinco minutos. Con FastAPI el esquema es idéntico: una ruta que devuelve JSON y Chart.js que lo dibuja. Django funciona, pero trae consigo ORM, admin y autenticación que aquí no necesitas.

### Qué te aporta una webapp

Frente a los PNG, el dashboard responde a preguntas concretas: el churn de marzo lo lees en el tooltip. En un servidor, aunque sea interno, basta un enlace para que todos vean la misma versión. Añadir un cuarto gráfico significa añadir un canvas y un campo en `/api/data`. Y un menú "Filtrar por región" es un parámetro más en la llamada: Flask filtra el DataFrame antes de devolver el JSON.

El límite es que necesita un servidor encendido: no la puedes adjuntar a un correo y sin conexión no funciona. Para que el equipo pueda acceder, la pones en cualquier máquina que ejecute Python: una instancia EC2, un contenedor Docker, un servicio como Render. El código es el mismo, y para lo demás basta un prompt como "crea un Dockerfile para esta webapp Flask".

### El atajo: la skill frontend-design

Los cuatro pasos te dan un dashboard predecible, porque cada detalle lo has decidido tú. Si el aspecto importa más que el control, puedes delegar el diseño en una skill. Anthropic publica en el marketplace oficial el plugin frontend-design, que contiene una skill con instrucciones sobre tipografía, paleta y layout. Claude la carga por su cuenta cuando pides una interfaz web.

```text
/plugin install frontend-design@claude-plugins-official
```

En la captura el prompt era una sola línea: una webapp local para mostrar los gráficos generados por el script de Python. Claude cargó la skill (`Skill(frontend-design)`), miró los gráficos existentes y eligió una dirección estética antes de escribir código: fondo oscuro, acentos de color, tarjetas con bordes luminosos.

![Claude carga la skill frontend-design y elige la dirección estética antes de construir la webapp](figures/cap-06/fig-03.png)

El resultado suele estar más cuidado que el dashboard de los cuatro pasos, pero es menos predecible: las fuentes, los colores y el layout los elige la skill. Para un dashboard interno que solo tiene que funcionar, los cuatro pasos bastan. Para una demo delante de un cliente, la skill te ahorra escribir el CSS a mano. Cómo funcionan las skills lo ves en el capítulo 9; los plugins y los marketplaces, en el capítulo 14.

::: {.callout .callout-prompt}
[Prompt reutilizable]{.callout-title}

Mini dashboard webapp. Sustituye `<ruta_csv>`, `<grafico1/2/3>` y los tipos de gráfico por tus datos: funciona con cualquier CSV tabular.

```text
A partir de <ruta_csv>, crea un mini dashboard con Flask:
- app.py con las rutas GET / y GET /api/data
- templates/index.html con Chart.js por CDN y tres canvas:
  <grafico1> (tipo: <line|bar|pie>),
  <grafico2> (tipo: <line|bar|pie>),
  <grafico3> (tipo: <line|bar|pie>)
- static/style.css con layout grid de 2 columnas, fuente Inter,
  tarjetas blancas sobre fondo gris claro, responsive en móvil
- Botón "Actualizar datos" que vuelve a pedir /api/data y llama a
  chart.update() sin recargar
Arranque: python app.py → servidor en http://localhost:5000
```
:::

## 6.3 Informes PDF con ReportLab

El PDF es el formato sin sorpresas: no depende del navegador ni de los programas de quien lo abre, y el layout es el mismo en cualquier pantalla. Sirve para el cliente externo, para el mánager que imprime, para el informe que llega por correo el día 1 de cada mes.

ReportLab es la librería de Python más usada para generar PDF desde código. No es la más sencilla, pero te da un control fino sobre cada elemento, tablas nativas, imágenes y estilos tipográficos. Las alternativas, en dos líneas: WeasyPrint convierte HTML y CSS a PDF, ideal si ya tienes una plantilla HTML (Claude puede escribir el HTML y luego convertirlo); fpdf2 es más sencilla, pero controla menos el layout. ReportLab compensa cuando sabes exactamente cómo tiene que ser el documento y necesitas meter gráficos generados por código, que es el caso de este capítulo.

### El prompt completo

```text
Escribe tools/genera_report.py, que genera output/report_mensile.pdf.
El PDF debe tener:

1. Página de portada: logo (static/logo.png si existe; si no,
   el texto "SaaS Co."), título "Informe de Métricas SaaS H1 2025",
   mes actual, fondo #1f77b4 con texto blanco.

2. Página de executive summary: los 3 KPI principales en cajas grandes
   (MRR total, churn medio, planes activos), el gráfico
   figures/churn_mensile.png incrustado como imagen, 3 viñetas
   de conclusiones generadas analizando los datos del CSV.

3. Página de detalle de planes: gráfico de tarta (figures/distribuzione_piani.png),
   tabla con una fila por plan (free / silver / gold) y columnas
   Plan, MRR, Churn %, Nuevas altas.

4. Página de recomendaciones: texto libre (3-5 viñetas) sugerido por
   Claude a partir de las tendencias del dataset.

Usa SimpleDocTemplate, Paragraph con ParagraphStyle, Image, Table,
TableStyle y PageBreak de ReportLab. Instala reportlab si hace falta.
```

Claude instala ReportLab, escribe el script y lo ejecuta. Si hay un error (un import equivocado, un paréntesis que falta, un argumento que ReportLab no acepta), lo lee en la salida y lo corrige solo. Aquí es donde se nota la diferencia con un chat: allí recibes el código, lo ejecutas tú, copias el error, lo pegas, esperas la corrección y vuelves a empezar. Claude Code cierra el ciclo en la misma sesión, y muchas veces solo ves el PDF terminado.

Las conclusiones y las recomendaciones de las páginas 2 y 4 son texto que Claude escribe sobre tus datos. Reléelas antes de mandar el PDF: es la parte del informe donde un error de interpretación pasa desapercibido con más facilidad.

### Las piezas de ReportLab

No lo vas a escribir a mano, pero conocer las piezas principales te ayuda a escribir prompts más precisos y a entender qué ha fallado cuando el layout no sale como esperabas:

```python
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Image, Table,
    TableStyle, PageBreak, Spacer,
)

# Contenedor principal: tamaño de página y márgenes
doc = SimpleDocTemplate("output/report_mensile.pdf",
                        pagesize=A4,
                        topMargin=2*cm, bottomMargin=2*cm,
                        leftMargin=2*cm, rightMargin=2*cm)

# Estilo para los títulos
stile_titolo = ParagraphStyle("Titolo",
    fontSize=24, leading=28, textColor=colors.white,
    spaceAfter=12, fontName="Helvetica-Bold")

# Un gráfico de matplotlib ya guardado en disco, en 16:9
img_churn = Image("figures/churn_mensile.png", width=14*cm, height=7.875*cm)

# Tabla de planes
dati_tabella = [["Piano", "MRR", "Churn %", "Nuove iscrizioni"],
                ["Gold", "€ 48.200", "1,2%", "1.240"],
                ["Silver", "€ 22.100", "2,8%", "890"],
                ["Free", "€ 0", "6,1%", "3.400"]]
tabella = Table(dati_tabella, colWidths=[4*cm, 4*cm, 3*cm, 4*cm])
tabella.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f77b4")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
]))

# El fondo de la portada se dibuja en la página, no es un flowable
def sfondo_copertina(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#1f77b4"))
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    canvas.restoreState()

# copertina, executive_summary, ... son listas de Paragraph, Image, Table
story = [*copertina, PageBreak(),
         *executive_summary, PageBreak(),
         *dettaglio_piani, PageBreak(),
         *raccomandazioni]
doc.build(story, onFirstPage=sfondo_copertina)
```

El modelo mental es la lista `story`: metes dentro los elementos en el orden en que deben aparecer (párrafos, imágenes, tablas, saltos de página) y `doc.build(story)` los compagina. La lista tiene que ser plana, por eso las secciones se expanden con `*`: si le pasas a `build` una lista dentro de otra, ReportLab se detiene con un error. Lo que no es contenido de la página, como el fondo sólido de la portada, se dibuja en el canvas con las funciones `onFirstPage` y `onLaterPages`. Si la portada sale blanca con el título en blanco, el problema casi siempre está ahí: pide a Claude que dibuje el fondo en `onFirstPage`.

### Los gráficos en memoria

Si los gráficos ya están en disco, como los de la sección 6.1, los insertas con `Image("percorso/del/file.png")`. Si prefieres no tener archivos intermedios, puedes pasarle a ReportLab un buffer en memoria:

```python
import io
import matplotlib.pyplot as plt
from reportlab.lib.units import cm
from reportlab.platypus import Image

# Genera el gráfico y guárdalo en memoria, no en disco
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(mesi, valori_churn, color="#1f77b4", linewidth=2)
# ... estilo ...

buffer = io.BytesIO()
plt.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
buffer.seek(0)
plt.close()

# Insértalo directamente en el PDF
img = Image(buffer, width=14*cm, height=7*cm)
```

`io.BytesIO()` se comporta como un archivo: matplotlib escribe el PNG en él y ReportLab lo lee de ahí. Sin PNG temporales y sin depender del orden en que se ejecutan los scripts. Usa un buffer por gráfico y no lo reutilices: ReportLab lee la imagen en el momento del `build`, no cuando creas el objeto `Image`.

### Parametrizar el script

Igual que con la webapp, el script empieza a ser útil de verdad cuando acepta parámetros:

```text
Modifica tools/genera_report.py para que acepte argumentos de CLI:
--region (p. ej. Europe, North America, Asia Pacific)
--months (p. ej. 1,2,3)
--output (ruta del PDF, por defecto output/report_mensile.pdf)
Añade comentarios de uso y validación de los argumentos con argparse.
Ejemplo: python tools/genera_report.py --region Europe --months 1,2 --output output/europe_jan_feb.pdf
```

A partir de aquí cualquiera del equipo genera el informe de su región y de los meses que le interesan, sin abrir el código:

```bash
python tools/genera_report.py --region "North America" --months 4,5,6 --output output/na_q2.pdf
```

Las comillas hacen falta porque "North America" contiene un espacio.

## 6.4 PDF, webapp o Excel

El formato lo decide quien lee, y lo que va a hacer con los números.

| Salida | Cuándo usarla | Ventajas | Inconvenientes |
| :---- | :---- | :---- | :---- |
| PDF | Stakeholders externos, informe periódico, entrega formal | Se abre en cualquier sitio, no cambia, lleva tu marca, se adjunta a un correo | Estático, hay que regenerarlo cuando cambian los datos |
| Webapp | Equipo interno, datos que cambian a menudo, exploración | Interactiva, siempre actualizada, ampliable, filtros dinámicos | Necesita un servidor (aunque sea local), sin conexión no funciona, no se adjunta |
| Excel | Quien quiere reelaborar los números, analistas financieros | Familiar, editable, tablas dinámicas y fórmulas vivas | Difícil de versionar, sin actualización en tiempo real, copias distintas circulando |

Lo normal es combinar dos o tres. Para el informe mensual de un SaaS, el PDF sale el día 1 hacia mánagers y clientes, la webapp interna se queda encendida para el equipo de producto y el Excel lo generas cuando el analista lo pide para el consejo. Para un lanzamiento basta la webapp de monitorización más un PDF de cierre al final del sprint. Para una auditoría externa es al revés: PDF firmado y fechado como documento oficial, Excel con los datos en bruto para las comprobaciones del auditor, ninguna webapp.

Antes de elegir, pregúntate cómo va a usar el archivo quien lo recibe. Si lo abre en su ordenador, quizá sin conexión, y quiere rehacer las cuentas, necesita el Excel. Si tiene que explorar los datos por su cuenta en el navegador, con filtros, la webapp. Si lo recibe por correo, lo lee y quizá lo imprime, el PDF. Cuando la respuesta no está clara, el PDF es la opción más segura.

## 6.5 Adelanto: el pipeline se convierte en una skill

Ahora tienes un script para los gráficos, una webapp Flask con tres gráficos interactivos y un generador de PDF con parámetros. Funcionan con tus datos, en tu máquina, en este proyecto.

El mes que viene tienes que repetir el mismo trabajo para otro cliente, con un CSV cuyas columnas son un poco distintas. Sin ninguna estructura empiezas de cero: recuperas los prompts, adaptas los nombres de las columnas, ajustas los parámetros. Con una skill de Claude Code te basta un comando.

### Qué es una skill, en breve

Una skill es una carpeta con un archivo `SKILL.md`: en `~/.claude/skills/<nombre>/` vale para todos tus proyectos, en `.claude/skills/<nombre>/` solo para el proyecto, y la compartes con el equipo a través de Git. El frontmatter contiene un nombre y una descripción; el cuerpo, las instrucciones. Claude lee siempre las descripciones de las skills instaladas: cuando una petición encaja, carga la skill y sigue las instrucciones. O la llamas tú por su nombre, como un slash command.

Junto a `SKILL.md`, la carpeta puede contener scripts y archivos de apoyo. Para este pipeline significa que los tres scripts que acabas de escribir pueden vivir dentro de la skill, y `SKILL.md` le explica a Claude cuándo y cómo ejecutarlos. Un esbozo:

```markdown
---
name: data-analysis-saas-monthly
description: Genera el informe mensual SaaS (PDF, dashboard HTML, Excel) a partir de un CSV de métricas. Úsala cuando el usuario pida el informe mensual de un cliente.
---

Argumentos: $0 ruta del CSV, $1 nombre del cliente, $2 mes.

1. Comprueba que el CSV tenga las columnas month, plan, region, mrr, churn_rate.
   Si falta alguna, detente y dime cuáles.
2. Ejecuta ${CLAUDE_SKILL_DIR}/scripts/genera_grafici.py sobre el CSV.
3. Ejecuta ${CLAUDE_SKILL_DIR}/scripts/genera_report.py con el nombre
   del cliente en el título.
4. Genera el dashboard HTML estático y el Excel en output/$1/.
```

Cómo se escribe, se prueba y se distribuye una skill lo ves en el capítulo 9. Por ahora te basta con el mecanismo.

### La skill data-analysis-saas-monthly

La skill del esbozo recibe el CSV, el nombre del cliente (acaba en los títulos) y el mes, y genera tres archivos: el PDF de la sección 6.3, un dashboard HTML estático con los gráficos de Chart.js, que a diferencia de la webapp Flask funciona sin conexión y se puede adjuntar a un correo, y el Excel del capítulo 5.

Imagina una agencia de analítica que lleva tres clientes SaaS, `startup_alpha`, `scaleup_beta` y `enterprise_gamma`, cada uno con su CSV, sus planes y sus métricas. Con la skill instalada, el trabajo del mes queda así:

```text
Genera el informe mensual de startup_alpha usando data/alpha_may.csv
```

```text
Genera el informe mensual de scaleup_beta usando data/beta_may.csv
```

```text
Genera el informe mensual de enterprise_gamma usando data/gamma_may.csv
```

Tres prompts, nueve archivos. El tiempo que te sobra lo dedicas a abrir los PDF y comprobar que los números son los correctos.

Todo esto se sostiene porque ninguna pieza del capítulo está atada a un archivo o a un cliente: el script del informe acepta parámetros con argparse, la webapp separa los datos (la API de Flask) de la presentación (Chart.js) y `SimpleDocTemplate` compagina cualquier cantidad de contenido.

Con el próximo capítulo entras en la Parte III: CLAUDE.md en el capítulo 7, comandos personalizados en el 8, skills en el 9, agentes en el 10. Ahí el trabajo de análisis de esta parte se convierte en algo que reutilizas en lugar de rehacerlo.

## Resumen {.unlisted}

- Construye un gráfico de matplotlib por pasadas: primero los datos correctos, luego la legibilidad, luego la resolución y las proporciones y, por último, la producción en serie.
- Cuando revises el script, comprueba el orden de los meses, la agregación de las filas y las unidades de medida: son los puntos donde un gráfico se equivoca sin que se note.
- Flask más Chart.js te da un dashboard con un endpoint `/api/data` y un botón que actualiza los gráficos con `chart.update()`, sin recargar la página.
- ReportLab construye el PDF a partir de una lista plana de elementos (`story`); los fondos y adornos de página van en las funciones `onFirstPage` y `onLaterPages`.
- Elige el formato según quién lee: PDF para quien recibe e imprime, webapp para quien explora, Excel para quien rehace las cuentas.
- Un script con parámetros ya es media skill: en el capítulo 9 lo empaquetas.

## Ejercicio {.unlisted}

Toma el `saas_metrics.csv` de los capítulos anteriores y genera las tres salidas en una única sesión:

1. Ejecuta `genera_grafici.py` y comprueba que en `figures/` están los tres PNG.
2. Arranca la webapp Flask y explora los datos en el navegador.
3. Ejecuta `genera_report.py` y abre el PDF en `output/`.

El ejercicio está terminado cuando el churn de marzo es idéntico en el tooltip de la webapp, en el gráfico del PDF y en la columna del CSV agregada a mano. Si no lo es, pide a Claude que encuentre la diferencia: suele ser una agregación distinta entre los dos pipelines (media frente a media ponderada, o un filtro por región que se quedó activo).

Si tienes que rehacer la webapp desde cero, el prompt del mini dashboard Flask está en la carpeta `cap-05/` del repositorio `github.com/hidran/claude-code-book-snippets` (numeración de la primera edición).
