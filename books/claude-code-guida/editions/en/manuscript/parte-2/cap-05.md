# Chapter 5. From CSV to Excel, tabular reports with Python

::: {.chapter-goals}
[What you'll learn]{.callout-title}

In this chapter you take the CSV from Chapter 4 and turn it into an Excel file you can hand over: formatted headers, a summary sheet with formula totals, a chart, and a script that regenerates the whole thing next month with one command. The work is done by a Python script built on openpyxl, written by Claude and refined over four rounds of prompts.

[Prerequisites]{.callout-title}

Python 3 with `pip`, and the `saas_metrics.csv` file from Chapter 4 in the project's `data/` folder. Any CSV with structured data works too, but you'll have to adapt the column names in the prompts.

:::

Every Business Intelligence platform promises to retire Excel, and Excel is still there. Tableau, Power BI, Looker and Metabase work well, but they need accounts and configuration. The sales manager already has Excel open on their laptop, and the client opens the attachment without installing anything. Ship a well-made `.xlsx` and nobody has to switch tools.

The catch is that a decent Excel file takes effort. pandas' `df.to_excel()` gives you a flat sheet, with no formatting and no formulas. A report you send to a client has colored headers, columns of the right width, alternating rows, a summary sheet and a sheet with charts. By hand that's hours of work, and doing it in code means learning the openpyxl or xlsxwriter APIs, which aren't the friendliest around.

With Claude Code the flow becomes this: you describe the report you want, Claude writes the script, you run it and open the file. If something's off, you write another prompt. And the script stays in the repository, under version control: next month, with a new CSV or for another region, you rerun it with a different argument and get the same report, updated.

## 5.1 Why go through a Python script

Excel can import a CSV on its own, and half the tools out there have an "export to xlsx" button. Putting a script in between pays off for three reasons.

The first is repeatability. A manual export has to be redone every time the dataset changes, with the same clicks every time. You write the script once and then you run it.

The second is transformation. A raw CSV is almost never ready for a report: there are columns to rename, dates to convert, aggregations to compute. pandas handles all of that in a few lines, before the Excel file is even opened. The alternative is repeating the same steps inside Excel at every update.

The third is about the file you end up with. When Excel imports a CSV, you get values. A script using openpyxl can write formulas. A total computed in Python is a fixed number; a total written as `=SUM(...)` recalculates when someone changes the data. Section 5.4 is all about that difference.

### The pipeline in four steps

1. Start from a CSV of raw data. Here we use `data/saas_metrics.csv`, the same dataset as Chapter 4: six months of metrics for a SaaS product, with the columns `month` (1-6), `date`, `plan` (free, silver, gold), `region` (Europe, North America, Asia Pacific), `mrr` and the others you've already explored.
2. Ask Claude for a Python script. The prompt describes the input file, the output file, the sheets you want, the header style and the aggregations. Claude writes the script in one go, with imports, error handling and comments.
3. The script uses openpyxl, the most widely used Python library for creating and editing `.xlsx` files. You don't need Excel installed: openpyxl writes the format directly and behaves the same on macOS, Linux and Windows.
4. Run the script and open the file with Excel, LibreOffice Calc or Numbers.

```bash
python tools/genera_excel.py
```

### openpyxl or xlsxwriter

The two libraries overlap a lot, but they have different priorities. openpyxl reads and edits existing files as well as creating new ones: it's the right pick when you need to update a template, add a sheet to a file someone sent you, or read data from an Excel file you received. xlsxwriter only writes, but in exchange it has a nicer API for charts, conditional formatting and Excel tables. Neither one creates native Excel pivot tables: you compute the pivot with pandas and write it as a regular table, which is what we'll do.

If you name the library in the prompt, Claude uses that one. If you don't, it picks one itself. Better to say so and avoid surprises when you update `requirements.txt`.

## 5.2 The first prompt

Open a terminal in the project folder and start Claude Code:

```bash
claude
```

The first prompt has to say three things: where the data is, where the output goes, and what the file looks like. You don't need to be exhaustive, since the details come with iteration, but the more context you give, the better the starting point.

```text
Read the file data/saas_metrics.csv. Write a Python script
tools/genera_excel.py that creates a file output/report.xlsx with the data
as a formatted table.

Requirements:
- A single sheet "Dati" with all the columns from the CSV
- Header with a dark blue background (#1F4E78) and bold white text
- Column widths automatically fitted to the content
- First row frozen (freeze pane) for scrolling
- Install pandas and openpyxl if they're missing and add them to requirements.txt
```

The sheet names `Dati` (data) and `Riepilogo` (summary) come from the companion project. The formulas later in the chapter reference them by name, so keep them as they are and the code will match.

Claude reads the CSV, works out the columns, their types and the row count, then writes the script. In auto mode, the default mode, the classifier lets through actions consistent with your request, so Claude creates the file and installs the dependencies without stopping at every step. If you'd rather see each diff before it's written, switch to Manual with `Shift+Tab` (Chapter 11 covers all the modes).

For a prompt this long it also makes sense to start from Plan Mode, as you did in Chapter 4: press `Shift+Tab` until the status bar shows `plan mode on`, type `/plan` at the prompt, or start the session with `claude --permission-mode plan`. Claude explores the CSV, proposes the structure of the script and touches nothing until you approve.

![Plan Mode on a similar request: Claude explores the CSV before proposing the script with the data, summary and chart sheets.](figures/cap-05/fig-02.png)

### What comes out of the first round

The script is split into functions: one loads the CSV into a pandas DataFrame, one creates the workbook and the sheet, one writes the headers in the requested style, one writes the data and computes the column widths, and a `main()` puts it all together and saves the file.

The part that formats the header looks like this:

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

And this is the automatic column width:

```python
for col_idx, column in enumerate(df.columns, start=1):
    max_length = max(
        len(str(column)),
        df[column].astype(str).map(len).max()
    )
    ws.column_dimensions[get_column_letter(col_idx)].width = max_length + 4
```

Run the script and you'll find `report.xlsx` in the `output/` folder:

```bash
python tools/genera_excel.py
```

<!-- TODO screenshot: the "Dati" sheet of output/report.xlsx open in LibreOffice Calc or Excel after round 1 (blue header, frozen first row). Old fig-01 dropped: it showed tools/generate_report_pdf.py from the PDF chapter. -->

### What's wrong with the first pass

The file opens, the headers are blue, the columns have sensible widths. Look at it with a critical eye, though, and some things are missing.

The `date` column comes through as text. `2025-01-01` in the CSV is a string, pandas leaves it that way unless you ask for `parse_dates`, and Excel treats it as text: filtering by date doesn't work and sorting is alphabetical.

The numbers need checking too. A single dirty value in the CSV is enough for `mrr` to be read as a string, and then Excel won't sum it.

There are no totals: the sheet shows the raw data and nothing else. And there's no pivot: if you want revenue by plan and by month, you have to build it yourself.

## 5.3 Iterating up to the report

The method is simple: open the file, see what's missing or wrong, and write a prompt that describes only those changes. Each round fixes one aspect. The first prompt was there to get things moving and give you something concrete to correct, so it didn't need to be perfect.

### Round 2: the Riepilogo sheet

```text
The script generates the Dati sheet correctly. Now add:

1. A second sheet "Riepilogo" with a pivot table where:
   - The rows are the months (sorted chronologically)
   - The columns are the subscription plans (free, silver, gold)
   - The values are the sum of MRR (Monthly Recurring Revenue)
   - Last row: total for each column

2. In the Dati sheet, make sure the mrr column is written
   as a number (float), not as a string, and that the date column
   is a real Excel date.
```

Claude adds a `write_summary_sheet()` function, computes the pivot with pandas' `pivot_table()` and writes the result to the Riepilogo sheet with the same header style. Open the file and you see right away how much each plan brings in month by month, with each plan's total at the bottom.

### Round 3: filters and formula totals

In round 2 the totals are numbers computed by Python. Now you want them as formulas.

```text
Now I want autofilters on every column of the Dati sheet, and
in the Riepilogo sheet the totals at the bottom must be SUM formulas
instead of hardcoded values computed by Python.

The formula in cell B[last_row] of the Riepilogo sheet must sum
column B from row 2 down, like this: =SUM(B2:B{n}).
```

Claude updates the script like this:

```python
# Autofilters on the Dati sheet
ws_dati.auto_filter.ref = ws_dati.dimensions

# SUM formulas in the totals row of the Riepilogo sheet
last_row = len(pivot_df) + 1  # +1 for the header
for col_idx in range(2, len(pivot_df.columns) + 2):
    col_letter = get_column_letter(col_idx)
    total_cell = ws_riepilogo.cell(row=last_row + 1, column=col_idx)
    total_cell.value = f"=SUM({col_letter}2:{col_letter}{last_row})"
    total_cell.font = Font(bold=True)
```

Now every header in the Dati sheet has the filter icon, and the total cells in Riepilogo hold formulas. Be careful about what they recalculate: they sum the Riepilogo cells, which are still values written by Python. If someone corrects a value in Riepilogo, the total updates; if they correct it in the Dati sheet, it doesn't. To link the two sheets you need formulas that read the Dati sheet, and you'll find them in section 5.4.

The autofilter isn't a real Excel Table, the kind with a name and a style that you get from Insert, Table. If you need one, ask for it explicitly: openpyxl creates it with `openpyxl.worksheet.table.Table`.

### Round 4: alternating rows and a pie chart

```text
In the Dati sheet, color the even rows with a very light gray background
(#F2F2F2) for the zebra pattern. In the Riepilogo sheet add a
pie chart showing the distribution of total revenue by plan.
```

For the alternating rows Claude adds a loop over the rows of the Dati sheet:

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

For the pie, the right data is in the totals row: one slice per plan.

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
[Tip]{.callout-title}

Always check where a chart gets its data. In Riepilogo the months are on the rows and the plans on the columns: a pie built on a column shows how a single plan is spread across the six months, which is a different chart from the one you asked for. If you see six slices instead of three, Claude took the column: tell it, and have it use the totals row with `from_rows=True`.
:::

<!-- TODO screenshot: the "Riepilogo" sheet after round 4, with the SUM totals row and the pie chart with three slices (free, silver, gold). -->

## 5.4 Live formulas and fixed values

When they generate Excel from code, a lot of developers don't think about what the person receiving the file will do with it. On screen, a report with fixed values and one with formulas look identical; the difference shows up when the recipient edits a cell.

### The report with fixed values

Every cell holds a number computed by Python. Whoever opens the file sees everything correct, but if they change a value nothing else moves: the totals stay the same, so do the averages, and the chart shows the old numbers.

To update it they have to come back to you: you fix the CSV, rerun the script and send a new file. And if the recipient wants to try a what-if like "what if we raised the gold plan price by 10%?", they can't do it on their own.

### The report with formulas

The total cells don't hold 12500 but `=SUM(B2:B7)`. The percentages don't hold 0.23 but `=B8/E8`. The charts are linked to the cells, so they update when a value changes.

Whoever receives it has a working tool: they edit the data in the Dati sheet, switch to Riepilogo and watch the totals change. They can run the gold plan what-if themselves, without calling you.

### How to ask Claude for formulas

You have to be explicit. If you don't ask, Claude tends to compute the values in Python and write them as numbers, which is the simplest route and the one with the least chance of getting a reference wrong. To get formulas, say so:

```text
In the Riepilogo sheet, use Excel formulas instead of values computed in Python.
The pivot and total cells must contain SUMIFS or SUM formulas that
reference the cells of the Dati sheet. The values must update
automatically if the user edits the data.
```

With this prompt every pivot cell becomes a `SUMIFS` that reads the Dati sheet: it sums `mrr` where the month is the row's month and the plan is the column's plan.

```python
mrr_col = get_column_letter(df.columns.get_loc("mrr") + 1)
plan_col = get_column_letter(df.columns.get_loc("plan") + 1)
month_col = get_column_letter(df.columns.get_loc("month") + 1)

# B2: MRR for the month in A2 and the plan in B1
ws_riepilogo["B2"] = (
    f"=SUMIFS(Dati!{mrr_col}:{mrr_col},"
    f"Dati!{month_col}:{month_col},$A2,"
    f"Dati!{plan_col}:{plan_col},B$1)"
)
```

The `SheetName!Column` syntax is the same one you'd use by hand in Excel. Deriving the letters from `df.columns` avoids the classic mistake of writing `Dati!G:G` and finding out that in next month's CSV the `mrr` column has moved. A simple sum for a single plan over the whole column is written the same way:

```python
cell.value = f'=SUMIF(Dati!{plan_col}:{plan_col},"gold",Dati!{mrr_col}:{mrr_col})'
```

### When to use formulas

You don't always need formulas. If the file is generated automatically and nobody opens it to edit it, a fixed value is perfectly fine: it's easier to write and you don't risk broken references.

They pay off when the recipient is comfortable with Excel and wants to work on the data, and when the report has a long life, updated every month with new data. On a report that's read once and archived, they're wasted work.

A rule of thumb: if the file goes to a manager or a client who "lives in Excel", I put in formulas. If it goes to an automated system or to an engineer who pulls the data out with code, values are enough.

### Excel, Google Sheets or a database

Excel is the right format when the recipient works with attachments, maybe offline, and the document has to fit in a single file without depending on external services. It also holds when the person receiving it knows Excel and has no wish to learn anything else.

Google Sheets makes sense when several people work on the same document at the same time, or when you want a report that's always up to date without sending new files. You generate it from code with the Google Sheets API, with an approach similar to this chapter's, but with credentials (a service account or OAuth) instead of a library that writes a local file.

A database, or a BI platform, is what you need when there's too much data for Excel (the limit is 1,048,576 rows per sheet, and the file gets slow long before that), when queries have to run fast over years of history, or when several systems read the same data. In those cases Excel becomes the place where you present the result of a few queries, and the data lives elsewhere.

For this chapter's case, a periodic report on company data for people who don't write code, Excel is the right choice. Chapter 6 adds charts, a web dashboard and a PDF report, and discusses when to pick each one.

## 5.5 Parameters and scheduling

A script that only works on one file whose name is hardcoded is still a prototype. To reuse it, it has to accept parameters.

### Adding argparse

```text
Add argparse to the script. The parameters must be:
- --input: path to the CSV (default: data/saas_metrics.csv)
- --output: path to the output Excel file (default: output/report.xlsx)
- --region: filter the data by region (optional, if not given use all the data)
- --months: list of months to include, as numbers from 1 to 6 (optional, default: all)

If the input file doesn't exist, the script must exit with a clear error
message. If the output folder doesn't exist, it must create it.
```

Claude adds the classic argparse block:

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

Now the script runs with explicit parameters:

```bash
python tools/genera_excel.py \
  --input data/saas_metrics.csv \
  --output output/report_europe_q1.xlsx \
  --region Europe \
  --months 1 2 3
```

<!-- TODO screenshot: terminal running the command above, plus `python tools/genera_excel.py --help` showing the four options. -->

### A file name with the date

So you don't overwrite earlier reports, have the month put into the file name:

```text
If --output isn't given, use an automatic name in the format
report_YYYY-MM.xlsx based on the current month.
```

Claude changes the `--output` default to `None` and adds:

```python
from datetime import datetime

if not args.output:
    timestamp = datetime.now().strftime("%Y-%m")
    output_path = Path(f"output/report_{timestamp}.xlsx")
else:
    output_path = Path(args.output)

output_path.parent.mkdir(parents=True, exist_ok=True)
```

If it left `default="output/report.xlsx"`, `args.output` would never be empty and the date branch would never fire: that's the kind of detail to check in the diff.

### Scheduling with cron (macOS and Linux)

Once it takes parameters, the script can run on its own. On macOS and Linux the simplest way is cron. To run it on the first of every month at 8:00, open the crontab:

```bash
crontab -e
```

and add this line:

```text
0 8 1 * * cd /percorso/assoluto/progetto && /usr/bin/python3 tools/genera_excel.py >> /tmp/genera_excel.log 2>&1
```

The `cd` is there because cron starts in your home directory, and the script's default paths (`data/saas_metrics.csv`, `output/`) are relative to the project folder. Replace `/percorso/assoluto/progetto` with the absolute path of your project. If you use a virtualenv, replace `/usr/bin/python3` with the virtualenv's Python, for example `.venv/bin/python`. `>> /tmp/genera_excel.log 2>&1` sends stdout and stderr to a log file, so when something goes wrong you know where to look.

### Scheduling with Task Scheduler (Windows)

On Windows the equivalent is Task Scheduler. The PowerShell cmdlet `New-ScheduledTaskTrigger` has no monthly option, so `schtasks` is the better fit. First create a `genera_report.bat` file in the project that moves into the right folder:

```bat
@echo off
cd /d C:\percorso\progetto
python tools\genera_excel.py >> output\genera_excel.log 2>&1
```

Then register the task for the first of every month at 8:00:

```powershell
schtasks /Create /SC MONTHLY /D 1 /ST 08:00 /TN "GeneraReportExcel" /TR "C:\percorso\progetto\genera_report.bat"
```

If the computer has to stay off, Claude Code routines run an agent in the cloud on a schedule or on a GitHub event (`/schedule` creates them through a guided conversation); for a deterministic script like this one, though, cron or Task Scheduler is all you need.

### Sending it by email automatically

If you want the report to land in an inbox without lifting a finger, ask Claude for an `--email` flag:

```text
Add an optional --email parameter. If it's given, after generating
the Excel file send an email to that address with the file attached.
Use smtplib and the SMTP_HOST, SMTP_USER, SMTP_PASSWORD environment
variables for the credentials.
```

::: {.callout .callout-warning}
[Warning]{.callout-title}

cron doesn't load your shell profile, so the `SMTP_*` variables you exported in `.zshrc` or `.bashrc` don't exist there. Have the script read them from a `.env` file excluded from Git, or define them at the top of the crontab. Under no circumstances should the password be written inside the script.
:::

For more involved scenarios, like a Slack notification, uploading to Google Drive or a webhook, you're better off with a service such as Make or Zapier that receives the file than with a Python script that keeps growing.

::: {.callout .callout-prompt}
[Reusable prompt]{.callout-title}

Excel report with pivot and formulas. Replace the placeholders in angle brackets with the names from your dataset.

```text
Read <csv_file>. Write a Python script tools/genera_excel.py that generates
<output.xlsx> with:

1. Sheet "Dati": all the CSV data as a filterable table (auto_filter),
   header with a dark blue background (#1F4E78) and bold white text,
   column widths fitted to the content, freeze on the first row,
   zebra striping on the even rows (#F2F2F2).

2. Sheet "Riepilogo": pivot table with <row_field> as rows and
   <column_field> as columns, values = sum of <metric>.
   Totals row with SUM formulas, not hardcoded values.

3. Sheet "Grafici": a line chart of <time_metric> over time
   broken down by <segment>, a pie chart of the total distribution
   of <metric> by <segment>.

Use openpyxl. Add argparse with --input, --output, --region (optional).
If --output isn't given, use report_YYYY-MM.xlsx with an automatic timestamp.
Install the dependencies and update requirements.txt.
```
:::

<!-- TODO screenshot: old fig-03 dropped (VS Code with ReportLab PDF code from the PDF chapter). A replacement here could show the finished workbook with its three sheets. -->

## Summary {.unlisted}

- For an Excel file you'll have to produce again, have Claude write a Python script: you rerun it, parameterize it and keep it in Git.
- openpyxl reads and writes; xlsxwriter only writes but has a nicer API for charts and conditional formatting. Either way, you compute the pivot with pandas.
- Work in rounds: formatted table, then summary, then formula totals, then charts and alternating rows. After each round open the file and check it, charts included.
- Formulas only help if they point at the data the user edits: for a Riepilogo that follows the Dati sheet, ask for `SUMIFS` that read it.
- With argparse and a dated file name the script is ready for cron or Task Scheduler; don't forget the `cd` into the project folder.

## Exercise {.unlisted}

Take `data/saas_metrics.csv` from Chapter 4, or another CSV with structured data, and work through the chapter in about 20 minutes:

1. Run the first prompt from section 5.2 and get the formatted Dati sheet.
2. Add the Riepilogo sheet with the pivot (round 2).
3. Replace the totals computed by Python with `SUM` formulas (round 3).
4. Add argparse with `--input` and `--output`.

You're done when you run the script on a second CSV with the same columns, without touching the code, and in the new file the Riepilogo totals row contains formulas (click a cell: the formula bar must show `=SUM(...)`).

The chapter's prompts are also in the `cap-04/` folder of the `claude-code-book-snippets` repository.
