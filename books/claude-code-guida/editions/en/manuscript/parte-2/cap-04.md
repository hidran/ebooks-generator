# Chapter 4. Analyzing a CSV with Plan Mode

::: {.chapter-goals}
[What you'll learn]{.callout-title}

- have Claude Code read a CSV as it is, with no preparation
- write prompts that produce conclusions about the data, not just means and standard deviations
- use Plan Mode to have an analysis designed before Claude writes a line of code
- handle large files and turn an exploratory session into a script you can rerun

[Prerequisites]{.callout-title}

Chapters 1-3. Python 3 installed (it runs the scripts Claude proposes; you don't need to know how to write them) and any CSV, or `data/saas_metrics.csv`, which you generate with the script in §4.1.

:::

If you're looking for a first real job to hand Claude Code, a CSV is a good pick. Claude reads the file straight from disk with the `Read` tool, so there's no copy and paste into a chat and no upload. It reasons about the contents with the domain knowledge it already has: it knows what churn rate is, and it knows that a rise in support tickets followed by more cancellations is a signal worth a look. Once you've found what you were after, it writes you the Python script that reruns the same analysis next month on fresh data.

The chapter's dataset holds metrics for a SaaS product: three subscription plans, three regions, six months of signups, cancellations, MRR and tickets. You start by opening the file and end with four PNG charts, going through Plan Mode on the way. The same process works on any CSV.

## 4.1 Having Claude read the CSV

The first step is the easiest: start Claude Code in the folder that holds the file and ask it to read it. You don't need to convert anything or write import scripts.

### Starting in the right folder

Open a terminal and create a working folder, if you don't have one yet:

```bash
mkdir -p ~/progetti/analisi-saas
cd ~/progetti/analisi-saas
```

Put the CSV in a `data/` subfolder. The examples use `data/saas_metrics.csv`, which you'll generate in a minute with the script in "The sample dataset". Then start Claude:

```bash
claude
```

The first time you open Claude Code in a new folder, it asks whether you trust its contents: say yes. On the first launch of a recent version you also get the auto mode notice; auto mode is the default permission mode you saw in Chapter 2. Claude runs the commands that fit your request on its own and a classifier blocks the risky ones, so it doesn't ask you anything to read files or run `ls`.

### Looking at what's in the folder

Before you query the CSV, it helps to know what's around it. You have two options.

The first is shell mode: type `!` at the start of the prompt, followed by the command.

```text
! ls -al
```

The command runs in the terminal, its output goes into the conversation and Claude comments on it. If you see a `.claude` folder, it holds the project settings, which Chapter 11 covers.

The second is to ask in plain words:

```text
List the files in this folder
```

Claude runs `ls` on its own and reports the list. The result is the same: with `!` you pick the command, in plain words Claude picks it.

### The first read prompt

To mention a file in the prompt, type `@` followed by its name. Claude Code suggests the matching paths and `Tab` completes the right one.

```text
@data/saas_metrics.csv read the file and tell me:
- number of rows and columns
- column names
- first 5 values for the "plan" and "region" columns
- any missing or anomalous values
```

Claude reads the file with `Read` and replies with something like this:

```text
The file data/saas_metrics.csv contains:
- 54 rows, 12 columns
- Columns: month, date, plan, region, new_signups,
  cancellations, mrr, churn_rate, ai_voice_usage,
  ai_text_usage, support_tickets, retention_rate
- Unique "plan" values: free, silver, gold
- Unique "region" values: Europe, North America, Asia Pacific
- Period covered: January - June 2025
- No missing values found
```

With a new dataset this is the most tedious part: working out which columns exist, what type they are, where data is missing. It usually eats an hour of notebooks and `df.info()`. Here it costs you one prompt, and you spend the time you saved thinking about what the numbers mean.

::: {.callout .callout-deep-dive}
[Under the hood]{.callout-title}

Claude doesn't open the file the way Excel does. The `Read` tool hands it the contents as text, which lands in the context window along with the rest of the conversation. A 54-row CSV fits whole and takes up very little; an export with hundreds of thousands of rows is a different story, covered in §4.4. `/context` tells you how much context you're using, and `/model` shows which model is active. As of October 2026 the default is Claude Opus 5.5 with a 1M-token context window, but defaults change often, so always check `/model`.
:::

### The sample dataset

The whole chapter uses `data/saas_metrics.csv`. It simulates six months of metrics (January-June 2025) for a SaaS product with three plans, free, silver and gold, sold in three regions: Europe, North America and Asia Pacific. There's one row for each combination of month, plan and region, hence the 54 rows. The numbers are synthetic: to get exactly the file I have, save this script as `genera_dati.py` in the working folder and run it with `python3 genera_dati.py`.

```python
"""Generate data/saas_metrics.csv, the dataset for chapters 4-6."""
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
                churn += 4.0          # free trials expire in March
            if piano == "silver":
                churn += mese * 0.3   # silver gets worse month after month
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

You'll need the same file in Chapters 5 and 6, so keep it around.

The columns you'll use most:

| Column | Description |
| :---- | :---- |
| `month` | Reference month (1-6) |
| `date` | First day of the month |
| `plan` | Plan: free, silver, gold |
| `region` | Geographic area |
| `new_signups` | New signups in the month |
| `cancellations` | Cancellations in the month |
| `mrr` | Monthly Recurring Revenue (€) |
| `churn_rate` | Churn rate (%) |
| `ai_voice_usage` | Usage of the AI voice feature (minutes) |
| `ai_text_usage` | Usage of the AI text feature (messages) |
| `support_tickets` | Support tickets opened |
| `retention_rate` | Retention rate (%) |

It's small enough to fit entirely in context and rich enough for every analysis in the next sections.

::: {.callout .callout-prompt}
[Reusable prompt]{.callout-title}

Onboarding onto a new dataset. It works on any CSV as a first pass, before you start the real analysis.

```text
Read @<file.csv>. Report:
1. Structure: number of rows, columns with name and type
2. Missing or anomalous values
3. Time patterns, if there are date columns
4. Any obvious outliers in the numeric columns

Then give me 3 interesting business questions you could
ask about this data: don't answer them yet, I want to
check first that they're the right ones.
```
:::

## 4.2 From numbers to conclusions

Any tool will give you descriptive statistics for a CSV. What you want from Claude is the interpretation, and that depends on how you ask. Take this prompt:

```text
Give me the descriptive statistics for the file
```

You get a table with mean, median and standard deviation for each numeric column. It works as a sanity check, but it doesn't help you decide anything. Compare it with this one:

```text
@data/saas_metrics.csv look at the CSV. What are the 3 most
important patterns for someone running a SaaS? Explain them
in plain English. Use numbers only when they're the main
point, not as filler.
```

Now Claude has to pick what matters and say it in simple words, the way an analyst would when presenting data to the people who have to act on it. The questions below work well on the same dataset and cover the most common cases.

### Trends over time

```text
@data/saas_metrics.csv analyze the cancellation rates month
by month. Do you see a clear trend? Are there unusual spikes
compared to the average? What might explain them?
```

Claude looks for a trend, compares it with the average and suggests hypotheses. On this dataset it might point out that free-plan churn rises in March, when trial periods usually expire, that gold stays stable, and suggest a closer look at silver, which may have a value proposition problem.

### Correlations

```text
@data/saas_metrics.csv is there a correlation between the
number of support tickets opened and the plan's churn rate?
If so, in which plan is the correlation strongest?
```

Claude cross-references two columns. The answer usually includes a direction ("yes, in the silver plan more tickets go along with more cancellations") and a hypothesis about what explains it. Keep in mind that a correlation over 54 rows is a hint, not proof: if the conclusion ends up driving a decision, ask Claude how solid it is and what it would take to confirm it.

### Segmenting by plan

```text
@data/saas_metrics.csv which plan contributes most to MRR?
Is there a plan that's underperforming relative to its
user base? Describe it the way you would on a slide for the CEO.
```

The last sentence, "the way you would on a slide for the CEO", is a trick that works: it forces Claude to summarize, cut the noise and land on a conclusion. You can often paste the text into a presentation as is.

### Anomalies

```text
@data/saas_metrics.csv are there weeks or months with metrics
way out of line with the average? Identify the outliers
and suggest 2-3 possible explanations for each one.
```

Besides flagging the out-of-range values, Claude reasons about plausible causes. A spike in signups in one month could be a marketing campaign or a post that went viral; a drop in retention might point to downtime or a price change. They're still hypotheses: you check them, with someone who knows the product.

### Plan and region together

A prompt that crosses two segmentation dimensions also works very well:

```text
@data/saas_metrics.csv in which combination of plan and region
is growth strongest? And in which is the situation most
worrying? Describe each one in a sentence and suggest
a concrete action for each.
```

Claude builds the plan-by-region matrix, picks out the cells doing best and worst, and suggests something to do about each. Asking for a concrete action forces it to move from description to recommendation.

### How to iterate

The first answer is a starting point. The loop that works best goes like this:

1. Send the conclusion-oriented prompt.
2. Read the answer and pick the most interesting point.
3. Dig into that point with a targeted question: "go deeper on the silver plan issue you mentioned: do you have enough data to estimate the impact on annual MRR?"
4. Once you have something you can act on, have it written up as a recommendation: "write this conclusion the way it might appear in a report for management, three sentences at most."

## 4.3 Plan Mode: planning a complex analysis

So far you've worked in questions and answers, which is fine for exploring. When you want a concrete result, like a chart, a dashboard or a PDF report, you need a plan first.

**Plan Mode** is the permission mode that separates planning from execution. Claude reads files, runs the commands it needs to explore and writes a numbered step-by-step plan, but it doesn't change anything until you approve it. Use it whenever the task touches several files, combines several tools or produces something you want right the first time.

### Turning on Plan Mode

The quickest way is `Shift+Tab`. Each press moves to the next mode: from auto mode, the default, to manual, then accept edits, then plan, and back to auto. Stop when the status line shows `plan mode on`.

If you already know you want to start by planning, launch the session straight in Plan Mode:

```bash
claude --permission-mode plan
```

From the prompt you can also use the `/plan` command, which enters Plan Mode; if you pass it a description, planning starts right away.

![A session already in Plan Mode after the per-region analysis: `/plan` confirms the mode is on and there's no plan yet](figures/cap-04/fig-01.png)

<!-- TODO screenshot: fig-01 è piccola e la riga di stato mostra il modello di allora; rifarla con la UI attuale (`/plan` in una sessione già in Plan Mode) a risoluzione piena -->

Typing "don't write code, just plan" into the prompt of a normal session usually gets you a plan in the chat, but the mode stays what it was. In auto mode, Claude may start creating files on the very next message. Only Plan Mode guarantees it won't touch anything until you say yes.

### When to use it

The rule of thumb: Plan Mode when you want a concrete output (a file, a chart, a dashboard, a script), not for exploratory questions about the data. For the back and forth in §4.2 it slows you down and adds nothing. For "build a dashboard with four charts", always use it.

### Plan Mode in action: the SaaS dashboard

The goal is a four-chart dashboard on the dataset you just analyzed: monthly MRR trend, signups by region, churn rate by plan and a heatmap of AI feature usage. Switch to Plan Mode with `Shift+Tab` and send this prompt:

```text
Analyze the file saas_metrics.csv and propose a strategy
for building a dashboard with four charts:
- Monthly MRR trend by plan (free, silver, gold)
- Signups by region month by month
- Churn rate compared across plans
- Heatmap of AI feature usage (ai_voice_usage, ai_text_usage)

Stack: Python + matplotlib. I want static PNG images
saved in a docs/charts/ folder.
Don't write code: just plan.
```

Claude reads the CSV, checks that the columns each chart needs exist and runs a few read-only commands to explore. With auto mode available, the classifier evaluates those commands instead of asking you. After a few seconds you get a plan along these lines:

```text
Implementation plan

1. CSV structure analysis
   - Check columns: month, plan, region, mrr, new_signups,
     churn_rate, ai_voice_usage, ai_text_usage
   - Confirm period: January-June 2025 (6 months)

2. Environment setup
   - Create requirements.txt with: pandas, matplotlib, seaborn
   - Create folder structure: data/, docs/charts/

3. Main script dashboard.py
   - Read CSV with pandas
   - Chart 1: MRR trend (line chart, pivot by plan)
   - Chart 2: Signups by region (grouped bar chart)
   - Chart 3: Churn rate (line chart, pivot by plan)
   - Chart 4: AI usage heatmap (seaborn heatmap,
     x axis = months, y axis = feature, cell = average usage)
   - Save PNGs to docs/charts/

4. Save plan to docs/plan.md

5. Run:
   - pip install -r requirements.txt
   - python dashboard.py
```

<!-- TODO screenshot: il piano della dashboard in Plan Mode (Python + matplotlib, docs/charts/). Sostituisce la vecchia fig-02, che mostrava un piano HTML + Chart.js + Firebase Hosting in contrasto con il testo -->

### Reviewing and changing the plan

The plan is a proposal. Before you approve it, read it with a critical eye: look for redundant steps, things that are missing, a stack you're not sold on.

In this case step 4, saving the plan to `docs/plan.md`, is an addition worth keeping. Two weeks from now, when you reopen the project, that file reminds you why you made certain choices, like a small ADR (Architecture Decision Record) you didn't have to write yourself.

To change something, stay in Plan Mode and ask:

```text
In chart 2, also add a line with the aggregate total
across all regions. For chart 4, use a color palette
that goes from white to dark blue (more usage = darker).
Update the plan.
```

Claude updates the plan without touching any code, and you can repeat until you're happy with it. If you'd rather fix it by hand, `Ctrl+G` opens the plan in your editor.

### Approving and running

When the plan is right, Claude asks how you want to proceed:

- `Yes, and use auto mode`: Claude runs every step in auto mode. The classifier lets through actions that fit the plan and stops the risky ones. For a clear, low-risk task like this one it's the right choice. If auto mode isn't available, the option is called `Yes, auto-accept edits`.
- `Yes, manually approve edits`: Claude asks for confirmation before every file change. Useful when it touches important files or when you want to look at the dependencies one by one.
- `No, keep planning`: you stay in Plan Mode and add constraints or corrections before starting.

<!-- TODO screenshot: la richiesta di approvazione del piano con le opzioni attuali (Yes, and use auto mode / Yes, manually approve edits / No, keep planning). Sostituisce la vecchia fig-03, che mostrava un piano Firebase e le opzioni di approvazione precedenti -->

With the first option Claude goes ahead on its own: it creates `data/` and moves the CSV there, writes `docs/plan.md` and `dashboard.py`, runs `pip install -r requirements.txt` and then the script. At the end you have four PNGs in `docs/charts/`, ready to drop into any document. If the classifier blocks an action, you'll find it in `/permissions`, on the Recently denied tab, and you can retry it from there.

::: {.callout .callout-tip}
[Tip]{.callout-title}

On many recent Linux distributions and with Homebrew's Python, `pip install` outside a virtual environment is refused with the `externally-managed-environment` error. Add a step to the plan that creates the environment with `python3 -m venv .venv` and installs the dependencies there: Claude updates the run commands too.
:::

## 4.4 Large datasets and context

The sample dataset has 54 rows and 12 columns. The ones you run into at work are CRM exports, event logs, billing data, and they easily reach hundreds of thousands of rows.

### The context problem

Everything Claude reads ends up in the context window. With the default model it's large, 1M tokens, but a 500,000-row export still won't fit, and even part of it would fill your session with numbers you don't need. On a file like that, Claude doesn't read everything in one go: a single `Read` call returns at most 25,000 tokens, and a file over 256 KB has to be read in chunks. More often Claude explores it with `wc -l`, `head` and similar commands. The analysis you get is based on a sample, which is often enough for general patterns. When the detail matters, ask it explicitly how many rows it actually read.

To keep an eye on things you have `/context`, which shows how the window is split: system instructions, tools, MCP servers, skills, memory files and messages. When the conversation gets long, `/compact` summarizes it and frees up space, and you can tell it what to keep:

```text
/compact keep the conclusions about the silver plan and the CSV column structure
```

Then there's the rule of thumb of one task per session. If after the churn analysis you move on to an unrelated question, run `/clear` and start fresh. Chapter 15 goes into the details of context and memory.

### Pattern 1: have Claude write the script

With large files it pays to flip the approach: instead of having Claude read the file, you have it write the code that processes it.

```text
Write a Python script analisi_grandi.py that reads
saas_metrics_full.csv (potentially very large)
and produces: row count by plan, monthly average
churn rate by region, the 10 months with the most cancellations.
The script must also work on 500,000-row files.
```

For a requirement like that, Claude uses pandas, reading the file in chunks (`chunksize`), declaring the column types (`dtype`) and loading only the columns it needs (`usecols`). You run the script yourself, look at the results and, if one catches your eye, bring it back to Claude in the next message. A few lines of output go into the context instead of half a million rows of data.

### Pattern 2: stratified samples

Sometimes you want Claude to see the real data before planning, but the file is too big to read in full. Ask for a stratified sample:

```text
Show me 3 rows for each unique value of the "plan"
column and 3 rows for each "region". I want to understand
the actual structure of the data before going ahead.
```

Claude pulls the rows with `head`, `grep` or a couple of lines of pandas. You have enough context to ask sensible questions without flooding the window.

### Pattern 3: saving intermediate results

If the analysis spans several sessions, save the intermediate results as JSON and pick up from there:

```text
Save the summary of the analysis we just did
to a file analisi_risultati.json. I'll use it as
the starting point in the next session.
```

The next session starts like this:

```text
@analisi_risultati.json let's pick up yesterday's
analysis. I want to dig into the silver plan finding.
```

You don't start from scratch, and the reasoning carries over from one session to the next. In Chapter 7 you'll see how to put the project's stable context (the stack, the current dataset, decisions already made) into `CLAUDE.md`, which Claude reads at every launch.

## 4.5 From conversation to script: when to consolidate

After half an hour of analysis you've explored the dataset, found the interesting patterns and maybe looked at a few charts. You can close the session and start over next time, or you can consolidate: turn the exploration into a reusable script. Claude is good at this because it has the whole conversation in context and knows which results you found useful.

### The consolidation prompt

```text
Sum up all the analysis we've done in a Python script
analisi.py that, when run on a new CSV with the same
structure as saas_metrics.csv, produces:
- a PDF report with the 4 main charts (use matplotlib
  with the PDF backend)
- an aggregated CSV saas_aggregato.csv with the monthly
  metrics by plan and by region
- a text file riepilogo.txt with the main patterns
  written in English for a non-technical manager

The script must take the CSV file name as an
argument: python analisi.py dati_luglio.csv
```

The script Claude writes carries over what came out of the session: the aggregations you needed, the charts you kept, the right level of detail for the text summary.

The next month the new CSV arrives, and you don't need to reopen Claude or redo the analysis:

```bash
python analisi.py dati_luglio.csv
```

In a few seconds you have the PDF with updated charts, the aggregated CSV and the summary. The exploration session has become a tool you can rerun whenever you like.

### When to consolidate and when not to

Consolidate if you know you'll repeat the same analysis on new data with the same structure: every month, every quarter, on different files. If you're exploring a dataset just once, or if the questions change every time, the script won't pay back the time you put into it. In that case a summary at the end of the session is enough:

```text
Summarize in 5 bullet points the main insights
we found in this session.
```

Paste it into a project document and you still have a record of the work. In Chapter 5 the same approach produces an Excel report with pivot tables, formulas and native charts, generated in Python with openpyxl without opening Excel.

## Summary {.unlisted}

- Claude reads a CSV straight from disk with `Read`: you mention it with `@` and don't need to prepare it.
- Useful prompts ask for patterns and conclusions ("what are the 3 most important patterns?"); descriptive statistics are only an initial sanity check.
- For a concrete output, enter Plan Mode (`Shift+Tab` until `plan mode on`, or `claude --permission-mode plan`): Claude changes nothing until you approve the plan.
- You correct the plan by staying in Plan Mode or with `Ctrl+G`; then you choose whether to run it in auto mode or by approving each change.
- With large files, have Claude write the script that processes them, check `/context` and use `/compact` telling it what to keep.
- If you'll repeat the analysis, consolidate it into a script that takes the CSV as an argument.

## Exercise {.unlisted}

Four steps, about ten minutes in all. Use `data/saas_metrics.csv` generated with `genera_dati.py`, or a CSV you already have on your machine.

1. Structure. Start Claude in the CSV's folder and use the reusable onboarding prompt from §4.1. Check that the answer reports the full structure and three business questions.
2. Conclusions. Pick one of the three questions and dig into it with a conclusion-oriented prompt. Do at least one more round, asking it to go deeper on the most interesting point in the answer.
3. Plan Mode. Switch to Plan Mode with `Shift+Tab` and ask Claude to plan a chart that shows the pattern you found in step 2. Change at least one aspect of the plan, then approve it and check that the chart gets produced.
4. Consolidation. Ask Claude for a script `analisi_rapida.py` that takes the CSV as an argument and produces the chart and a three-line text summary.

The exercise is done when `python analisi_rapida.py <file.csv>`, run by you in a terminal outside Claude Code, generates the chart and the three summary lines without errors.
