# Chapter 6. Charts, dashboards and PDF reports

::: {.chapter-goals}
[What you'll learn]{.callout-title}

From the same CSV as Chapters 4 and 5 you get three different things: a set of matplotlib charts ready for slides, a small web dashboard built with Flask and Chart.js, and a PDF report generated with ReportLab. Then you see how to pick the format based on who reads it, and how the whole pipeline can become a skill, the topic of Chapter 9.

[Prerequisites]{.callout-title}

Chapters 4 and 5 (same project, same `data/saas_metrics.csv`), Python 3 and a browser.

:::

You have a CSV with the monthly metrics of a SaaS product: MRR, churn, plans, regions, feature usage. You did the analysis in Chapter 4 and the Excel workbook in Chapter 5. Now you have to show it to someone, and the format depends on who that someone is.

The manager wants a PDF in their inbox on Friday morning, something to print or attach to a presentation without opening any program. The product team wants a page in the browser where they can hover over data points and hide a plan from the legend. The financial analyst wants the Excel file with the raw data and the pivot table, to run their own numbers.

Claude Code produces all three outputs from the same CSV with a handful of prompts: it installs the libraries, writes the scripts, runs them and fixes the errors. You decide what has to come out and check that the numbers add up.

## 6.1 matplotlib charts, one round at a time

A good chart doesn't come out of the first prompt, and it doesn't need to. It works better one pass at a time: first any chart with the right data, then you make it readable, then you lock down resolution and proportions, and finally you produce it in batches.

The order matters. If on the first pass the columns are swapped or the months are sorted alphabetically, you notice right away, before you've spent time on fonts and colors. With one long prompt you risk getting a beautiful, wrong chart, and not noticing.

### Round 1: the raw chart

Start with the simplest prompt you can write:

```text
Read data/saas_metrics.csv and generate a chart of the monthly
cancellation rates (churn rate) with matplotlib. Save it as
figures/churn_mensile.png.
```

Claude reads the CSV, finds the `churn_rate` column, installs matplotlib if it's missing and writes a Python script. What you get is the default chart: a blue line on a white background, months on the X axis, percentages on the Y axis, no grid, no title. That's fine for checking the data. It's not fine for a presentation.

If the project has a virtualenv, say so in the first prompt ("use `.venv`"), or the libraries end up in the system Python. In auto mode, the default, the classifier normally lets `pip install` through without asking you anything. In manual mode Claude asks for permission.

### Round 2: readability and colors

```text
Improve the chart: add a clear title ("Monthly Churn Rate H1 2025"),
axis labels (Month / Churn Rate %), a light grid (alpha=0.3,
linestyle='--'), a sans-serif font (DejaVu Sans), and use the brand
colors #1f77b4 for the line and #ff7f0e for the markers.
Add a legend.
```

The light grid helps you read values without stealing the show, and the title tells you right away what you're looking at. The two colors in the example are matplotlib's default blue and orange: swap in your brand's colors. This is the minimum before you send a chart to your colleagues.

### Round 3: resolution and proportions

```text
Save the chart as a high-resolution PNG in 16:9 format for
presentations: plt.figure(figsize=(12, 6.75)) and
plt.savefig(..., dpi=150, bbox_inches='tight').
```

At 150 DPI a 12 by 6.75 inch figure comes out at roughly 1800 by 1012 pixels, enough for a full-screen slide. If you need exactly 1200 by 675, use `figsize=(8, 4.5)` with the same DPI. `bbox_inches='tight'` trims the white space and keeps the title and labels from being clipped at the edges, a common defect in script-generated charts. The price is that the final dimensions shift by a few pixels.

### Round 4: batch production

```text
Produce three separate charts from the same CSV:
1. figures/churn_mensile.png: line chart of the churn rate month by month
2. figures/distribuzione_piani.png: pie chart with the percentage
   breakdown of MRR by plan (free, silver, gold)
3. figures/utilizzo_features.png: horizontal bar chart with the
   usage of the main features
Use the same DPI/size/style parameters as the previous rounds.
Save all the files in figures/ with descriptive names.
```

Claude writes a `genera_grafici.py` script that produces all three files in a single run. That's already a small reporting pipeline.

The chart types in the prompt follow the rule people who do dataviz for a living use: lines for churn, because it's a trend over time; a pie for the plans, because they're parts of a whole; horizontal bars for the features, because you're comparing categories with long names. If you leave them out of the prompt, Claude usually lands on the same choices. If one doesn't convince you, spell it out.

One caveat about the features. In the sample CSV `ai_voice_usage` is in minutes and `ai_text_usage` in messages: two bars on the same scale look comparable and aren't. Ask Claude to normalize them (for example, January set to 100) or to draw two separate charts.


![A real session: Claude wrote `dashboard.py`, installed the dependencies and saved five charts in `docs/charts/`](figures/cap-06/fig-01.png)

<!-- TODO screenshot: fig-01, fig-02 e fig-03 sono a 560x315 pixel, troppo pochi per la stampa; rifarle a risoluzione piena. In fig-01 e fig-03 la status line mostra il modello e la modalità di allora. -->

### The script, line by line

The scripts Claude produces for this kind of job almost always have the same shape. You won't write them by hand, but you need to be able to read them to check them:

```python
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# Load the data
df = pd.read_csv("data/saas_metrics.csv")

# Nine rows per month (plan by region): average churn per month.
# churn_rate is already a percentage (4.2 means 4.2%)
churn = df.groupby("month")["churn_rate"].mean()

# Chart 1: churn rate
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

Two details to look for when you review it. The first is the `groupby`: the CSV has 54 rows, six months times three plans times three regions, and if you plot the rows as they are you get a zigzag line that means nothing. The second is the scale: `churn_rate` is already a percentage, so `PercentFormatter()` is used without multiplying by 100. If your CSV stores churn as a fraction (0.03), the script has to multiply, or the chart shows 0.03%. Claude usually catches this by looking at the values, but check it yourself.

![The `dashboard.py` script open in the IDE, with the matplotlib and seaborn imports and the palettes for plans and regions](figures/cap-06/fig-02.png)

In the screenshot the imports are underlined with "could not be resolved", and yet the script runs: the IDE is using a different Python interpreter from the one Claude installed the libraries into. You fix it by pointing the IDE at the project's virtualenv.

### matplotlib, seaborn or plotly

These are the three libraries Claude suggests most often. matplotlib gives you control over every element of the chart: it takes more code, but the result is predictable, and it's the natural choice for PNGs that go into a PDF or a slide. seaborn sits on top of matplotlib and produces statistical charts (distributions, heatmaps, pairplots) in fewer lines, in exchange for less control over the layout. plotly makes interactive charts for the web, with hover and zoom built in; it exports to HTML or to a static image, but it looks worse in PDFs.

In practice: matplotlib for PDF and print, plotly for dashboards, seaborn for exploratory analysis. In the rest of the chapter you use matplotlib for the PDF and Chart.js, served by Flask, for the web app.

## 6.2 A dashboard with Flask and Chart.js

Static charts are fine in a PDF. If you want the team to explore the data on their own instead, hovering over points and reading the exact value without opening Excel, you need a web page.

Flask plus Chart.js is the smallest thing that works. Flask exposes the data as JSON, Chart.js draws the charts in the browser. No React, no bundler: one Python file, one HTML template, one CSS file, and it starts with `python app.py`. You build it in four steps.

### Step 1: the Flask skeleton

```text
Create app.py in the project root. It must have:
- A GET / route that renders templates/index.html
- A GET /api/data route that reads data/saas_metrics.csv with pandas
  and returns a JSON with three aggregated datasets:
  {
    "churn": [{"month": 1, "value": 4.2}, ...],
    "piani": [{"piano": "gold", "pct": 35}, ...],
    "features": [{"feature": "ai_voice_usage", "utilizzo": 0.72}, ...]
  }
- Debug mode on (app.run(debug=True))
Install Flask and pandas if needed.
```

Claude writes `app.py` with the two routes, aggregates the data with pandas and serializes it to JSON. The `/api/data` route keeps the data separate from the presentation: if the CSV changes tomorrow, the HTML template stays as it is.

### Step 2: the template with Chart.js

```text
Create templates/index.html. It must:
- Include Chart.js via CDN (version 4.x)
- Define three canvases: lineChart (monthly churn), pieChart
  (plan breakdown), featuresChart (feature usage, horizontal
  bars)
- On page load, fetch /api/data with fetch() and initialize
  the three charts with the data received
- Add H2 titles above each chart
```

The template loads the data with `fetch('/api/data').then(r => r.json()).then(data => { ... })`, without reloading the page, and Chart.js draws the charts from the arrays it receives. Here Jinja2 only renders the empty page: all the data comes from the API.

### Step 3: layout and style

```text
Create static/style.css with:
- A 2-column grid layout: lineChart spans the whole first row
  (grid-column: 1 / -1), pieChart and featuresChart share
  the second row
- Inter font (via Google Fonts) with a sans-serif fallback
- Generous padding (24px in the cards), light gray background (#f5f5f5),
  white cards with border-radius 8px and a light box-shadow
- Responsive: on mobile (max-width: 768px) a single column
```

A CSS grid is enough for this dashboard: no framework, about twenty lines, and the result is already something you can show.

### Step 4: refreshing the data without reloading

```text
In the template, add a "Refresh data" button (id="refresh-btn")
in the top right corner. On click, re-fetch /api/data and update
the data of the three charts using chart.data.datasets[0].data = newData
followed by chart.update(). Don't reload the page.
```

Without the button, when the CSV changes the user has to reload the page and loses what they'd done: the zoom, the series hidden from the legend. Chart.js exposes `.update()` to redraw a chart without recreating it:

```javascript
document.getElementById("refresh-btn").addEventListener("click", function () {
    fetch("/api/data")
        .then(r => r.json())
        .then(data => {
            // Update the chart datasets
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

You change only `.data` and call `.update()`: Chart.js animates the transition on its own, with no flicker. The same pattern (fetch, update the data, update) works for filters, date pickers and dropdown menus. All that changes is the parameter you pass to the endpoint.

### Running it

```bash
python app.py
```

Open `http://localhost:5000`. Hover over a point on the line and the tooltip shows its value. Click a plan in the pie chart's legend and it disappears. Press "Refresh data" and the charts update without a page reload.

::: {.callout .callout-warning}
[Warning]{.callout-title}

On macOS port 5000 is often taken by the AirPlay Receiver. If the browser answers with a 403 or Flask won't start, turn off AirPlay Receiver in System Settings or ask Claude to start the app on another port, for example `app.run(debug=True, port=5001)`.
:::

Why Flask and not FastAPI or Django? For an internal dashboard with no login and no database, you can read a Flask app in five minutes. With FastAPI the pattern is identical: a route that returns JSON and Chart.js drawing it. Django works, but it brings along an ORM, an admin and authentication you don't need here.

### What a web app adds

Compared with PNGs, the dashboard answers specific questions: March churn is right there in the tooltip. On a server, even an internal one, a link is all it takes for everyone to see the same version. Adding a fourth chart means adding a canvas and a field in `/api/data`. And a "Filter by region" menu is one more parameter in the call: Flask filters the DataFrame before returning the JSON.

The catch is that it needs a running server: you can't attach it to an email and it doesn't work offline. To make it reachable for the team, you put it on any machine that runs Python: an EC2 instance, a Docker container, a service like Render. The code stays the same, and for the rest a prompt like "create a Dockerfile for this Flask web app" is enough.

### The shortcut: the frontend-design skill

The four steps give you a predictable dashboard, because you decided every detail. If looks matter more than control, you can hand the design over to a skill. Anthropic publishes the frontend-design plugin in the official marketplace; it contains a skill with instructions on typography, palette and layout. Claude loads it on its own when you ask for a web interface.

```text
/plugin install frontend-design@claude-plugins-official
```

In the screenshot the prompt was a single line: a local web app to show the charts generated by the Python script. Claude loaded the skill (`Skill(frontend-design)`), looked at the existing charts and picked an aesthetic direction before writing any code: dark background, colored accents, cards with glowing borders.

![Claude loads the frontend-design skill and picks the aesthetic direction before building the web app](figures/cap-06/fig-03.png)

The result is usually more polished than the four-step dashboard, but less predictable: the skill picks the fonts, colors and layout. For an internal dashboard that just has to work, the four steps are enough. For a demo in front of a client, the skill saves you from writing the CSS by hand. Chapter 9 covers how skills work, Chapter 14 plugins and marketplaces.

::: {.callout .callout-prompt}
[Reusable prompt]{.callout-title}

Mini web app dashboard. Replace `<csv_path>`, `<chart1/2/3>` and the chart types with your own data: it works on any tabular CSV.

```text
Starting from <csv_path>, create a mini Flask dashboard:
- app.py with GET / and GET /api/data routes
- templates/index.html with Chart.js from a CDN and three canvases:
  <chart1> (type: <line|bar|pie>),
  <chart2> (type: <line|bar|pie>),
  <chart3> (type: <line|bar|pie>)
- static/style.css with a 2-column grid layout, Inter font,
  white cards on a light gray background, mobile responsive
- A "Refresh data" button that re-fetches /api/data and calls
  chart.update() without a reload
Startup: python app.py → server on http://localhost:5000
```
:::

## 6.3 PDF reports with ReportLab

PDF is the format with no surprises: it doesn't depend on the browser or on the software of whoever opens it, and the layout is the same on every screen. It's right for the external client, for the manager who prints, for the report that lands by email on the first of the month.

ReportLab is the most widely used Python library for generating PDFs from code. It isn't the simplest, but it gives you fine control over every element, native tables, images and typographic styles. The alternatives in two lines: WeasyPrint converts HTML and CSS to PDF, great if you already have an HTML template (Claude can write the HTML and then convert it); fpdf2 is simpler but gives you less control over the layout. ReportLab pays off when you know exactly what the document has to look like and you need to drop in charts generated by code, which is the case in this chapter.

### The full prompt

```text
Write tools/genera_report.py that generates output/report_mensile.pdf.
The PDF must have:

1. Cover page: logo (static/logo.png if it exists, otherwise
   the text "SaaS Co."), title "SaaS Metrics Report H1 2025",
   current month, #1f77b4 background with white text.

2. Executive summary page: the 3 main KPIs in large boxes
   (total MRR, average churn, active plans), the chart
   figures/churn_mensile.png embedded as an image, 3 takeaway
   bullets generated by analyzing the CSV data.

3. Plan detail page: pie chart (figures/distribuzione_piani.png),
   a table with one row per plan (free / silver / gold) and columns
   MRR, New signups, Cancellations, Churn %.

4. Recommendations page: free text (3-5 bullets) suggested by
   Claude after analyzing the trends in the dataset.

Use ReportLab's SimpleDocTemplate, Paragraph with ParagraphStyle, Image,
Table, TableStyle, PageBreak. Install reportlab if needed.
```

Claude installs ReportLab, writes the script and runs it. If there's an error (a wrong import, a missing parenthesis, an argument ReportLab doesn't accept), it reads it from the output and fixes it on its own. This is where you feel the difference from a chat: there you get the code, run it yourself, copy the error, paste it, wait for the fix and start over. Claude Code closes the loop in the same session, and often all you see is the finished PDF.

The takeaways and recommendations on pages 2 and 4 are text Claude wrote about your data. Reread them before you send the PDF: that's the part of the report where a misreading slips through most easily.

### ReportLab's building blocks

You won't write it by hand, but knowing the main pieces helps you write sharper prompts and understand what went wrong when the layout doesn't come out right:

```python
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Image, Table,
    TableStyle, PageBreak, Spacer,
)

# Main container: page size and margins
doc = SimpleDocTemplate("output/report_mensile.pdf",
                        pagesize=A4,
                        topMargin=2*cm, bottomMargin=2*cm,
                        leftMargin=2*cm, rightMargin=2*cm)

# Style for headings
stile_titolo = ParagraphStyle("Titolo",
    fontSize=24, leading=28, textColor=colors.white,
    spaceAfter=12, fontName="Helvetica-Bold")

# A matplotlib chart already saved to disk, in 16:9
img_churn = Image("figures/churn_mensile.png", width=14*cm, height=7.875*cm)

# Plans table
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

# The cover background is drawn on the page, it isn't a flowable
def sfondo_copertina(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#1f77b4"))
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    canvas.restoreState()

# copertina, executive_summary, ... are lists of Paragraph, Image, Table
story = [*copertina, PageBreak(),
         *executive_summary, PageBreak(),
         *dettaglio_piani, PageBreak(),
         *raccomandazioni]
doc.build(story, onFirstPage=sfondo_copertina)
```

The mental model is the `story` list: you put the elements in it in the order they should appear (paragraphs, images, tables, page breaks) and `doc.build(story)` lays them out. The list has to be flat, which is why the sections are expanded with `*`: if you pass `build` a list nested inside another, ReportLab stops with an error. Whatever isn't page content, like the cover's solid background, is drawn on the canvas with the `onFirstPage` and `onLaterPages` functions. If the cover comes out white with a white title, the problem is almost always there: ask Claude to draw the background in `onFirstPage`.

### Charts in memory

If the charts are already on disk, like the ones from section 6.1, you insert them with `Image("percorso/del/file.png")`. If you'd rather not have intermediate files, you can hand ReportLab an in-memory buffer:

```python
import io
import matplotlib.pyplot as plt
from reportlab.lib.units import cm
from reportlab.platypus import Image

# Generate the chart and save it in memory, not on disk
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(mesi, valori_churn, color="#1f77b4", linewidth=2)
# ... styling ...

buffer = io.BytesIO()
plt.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
buffer.seek(0)
plt.close()

# Insert it straight into the PDF
img = Image(buffer, width=14*cm, height=7*cm)
```

`io.BytesIO()` behaves like a file: matplotlib writes the PNG into it, ReportLab reads it from there. No temporary PNGs and no dependency on the order the scripts run in. Use one buffer per chart and don't reuse it: ReportLab reads the image when you call `build`, not when you create the `Image` object.

### Parameterizing the script

As with the web app, the script becomes really useful once it takes parameters:

```text
Change tools/genera_report.py to accept CLI arguments:
--region (e.g. Europe, North America, Asia Pacific)
--months (e.g. 1,2,3)
--output (PDF path, default output/report_mensile.pdf)
Add usage comments and argument validation with argparse.
Example: python tools/genera_report.py --region Europe --months 1,2 --output output/europe_jan_feb.pdf
```

Now anyone on the team can generate the report for their region and the months they care about, without opening the code:

```bash
python tools/genera_report.py --region "North America" --months 4,5,6 --output output/na_q2.pdf
```

The quotes are there because "North America" contains a space.

## 6.4 PDF, web app or Excel

The format depends on who reads it and what they'll do with the numbers.

| Output | When to use it | Pros | Cons |
| :---- | :---- | :---- | :---- |
| PDF | External stakeholders, periodic reports, formal delivery | Opens anywhere, doesn't change, carries your brand, attaches to an email | Static, has to be regenerated when the data changes |
| Web app | Internal team, data that changes often, exploration | Interactive, always up to date, extensible, dynamic filters | Needs a server (even just a local one), doesn't work offline, can't be attached |
| Excel | People who want to rework the numbers, financial analysts | Familiar, editable, live pivots and formulas | Hard to version, no real-time updates, different copies floating around |

You usually combine two or three. For a SaaS monthly report, the PDF goes out on the first of the month to managers and clients, the internal web app stays up for the product team, and you generate the Excel file when the analyst asks for it for the board. For a launch, the monitoring web app plus a wrap-up PDF at the end of the sprint is enough. For an external audit it's the other way around: a signed, dated PDF as the official document, Excel with the raw data for the auditor's checks, no web app.

Before you choose, ask yourself how the person receiving the file will use it. If they open it on their own computer, maybe without a network connection, and want to redo the math, they need the Excel file. If they need to explore the data on their own in the browser, with filters, the web app. If they get it by email, read it and maybe print it, the PDF. When the answer isn't clear, the PDF is the safest choice.

## 6.5 Preview: the pipeline becomes a skill

You now have a script for the charts, a Flask web app with three interactive charts and a PDF generator with parameters. They work on your data, on your machine, in this project.

Next month you have to do the same job for another client, with a CSV whose columns are slightly different. Without any structure you start from scratch: you dig up the prompts, adapt the column names, tweak the parameters. With a Claude Code skill a single command does it.

### What a skill is, briefly

A skill is a folder with a `SKILL.md` file: in `~/.claude/skills/<name>/` it applies to all your projects, in `.claude/skills/<name>/` only to the project, and you share it with the team through Git. The frontmatter holds a name and a description, the body holds the instructions. Claude always reads the descriptions of the installed skills: when a request matches, it loads the skill and follows the instructions. Or you call it by name yourself, like a slash command.

Next to `SKILL.md` the folder can hold scripts and supporting files. For this pipeline it means the three scripts you just wrote can live inside the skill, and `SKILL.md` tells Claude when and how to run them. A sketch:

```markdown
---
name: data-analysis-saas-monthly
description: Generates the monthly SaaS report (PDF, HTML dashboard, Excel) from a metrics CSV. Use it when the user asks for a client's monthly report.
---

Arguments: $0 path to the CSV, $1 client name, $2 month.

1. Check that the CSV has the columns month, plan, region, mrr, churn_rate.
   If any are missing, stop and tell me which ones.
2. Run ${CLAUDE_SKILL_DIR}/scripts/genera_grafici.py on the CSV.
3. Run ${CLAUDE_SKILL_DIR}/scripts/genera_report.py with the client
   name in the title.
4. Generate the static HTML dashboard and the Excel file in output/$1/.
```

Chapter 9 covers how to write, test and distribute a skill. For now the mechanism is all you need.

### The data-analysis-saas-monthly skill

The skill in the sketch takes the CSV, the client name (it ends up in the titles) and the month, and produces three files: the PDF from section 6.3, a static HTML dashboard with the Chart.js charts, which unlike the Flask web app works offline and can be attached to an email, and the Excel file from Chapter 5.

Picture an analytics agency that looks after three SaaS clients, `startup_alpha`, `scaleup_beta` and `enterprise_gamma`, each with its own CSV, its own plans and its own metrics. With the skill installed, the month's work becomes:

```text
Generate the monthly report for startup_alpha using data/alpha_may.csv
```

```text
Generate the monthly report for scaleup_beta using data/beta_may.csv
```

```text
Generate the monthly report for enterprise_gamma using data/gamma_may.csv
```

Three prompts, nine files. You spend the time left over opening the PDFs and checking that the numbers are the right ones.

All of this holds up because no piece of the chapter is tied to one file or one client: the report script takes parameters through argparse, the web app keeps the data (the Flask API) separate from the presentation (Chart.js), and `SimpleDocTemplate` lays out any amount of content.

The next chapter takes you into Part III: CLAUDE.md in Chapter 7, custom commands in 8, skills in 9, agents in 10. That's where the analysis work from this part turns into something you reuse instead of redoing.

## Summary {.unlisted}

- Build a matplotlib chart in passes: first the right data, then readability, then resolution and proportions, and finally batch production.
- When you review the script, check the month order, the row aggregation and the units: those are the places where a chart is wrong without showing it.
- Flask plus Chart.js gives you a dashboard with an `/api/data` endpoint and a button that refreshes the charts with `chart.update()`, without reloading the page.
- ReportLab builds the PDF from a flat list of elements (`story`); page backgrounds and decorations go in the `onFirstPage` and `onLaterPages` functions.
- Pick the format based on who reads it: PDF for people who receive and print, a web app for people who explore, Excel for people who redo the math.
- A script with parameters is already half a skill: in Chapter 9 you package it.

## Exercise {.unlisted}

Take the `saas_metrics.csv` from the previous chapters and produce all three outputs in a single session:

1. Run `genera_grafici.py` and check that the three PNGs are in `figures/`.
2. Start the Flask web app and explore the data in the browser.
3. Run `genera_report.py` and open the PDF in `output/`.

The exercise is done when March churn is identical in the web app's tooltip, in the PDF chart and in the CSV column aggregated by hand. If it isn't, ask Claude to find the difference: it's usually a different aggregation between the two pipelines (mean versus weighted mean, or a region filter left on).

If you need to rebuild the web app from scratch, the mini Flask dashboard prompt is in the `cap-05/` folder of the `github.com/hidran/claude-code-book-snippets` repository (first-edition numbering).
