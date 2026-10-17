# Chapter 9. Skills, from command to reusable capability

::: {.chapter-goals}
[What you'll learn]{.callout-title}

- When a custom command should be promoted to a skill, and what the extra folder buys you.
- How a `SKILL.md` is put together: the frontmatter fields, and a description that triggers the skill at the right moment.
- Two hand-written skills: `report-pdf`, which turns a CSV into a PDF report, and `data-analysis-saas-monthly`, with scripts, references and templates.
- How to use the skill-creator, where to find ready-made skills and how to keep the ones you collect in order.

[Prerequisites]{.callout-title}

Chapter 8 (command files, arguments, `` !`command` ``), the `analisi-saas` project from chapters 4-6 and the `cc-advanced-lab` lab from chapter 2.

:::

In chapter 8 you wrote commands in `.claude/commands/`: one file, one prompt, a slash to call it. They're great as long as the prompt can stand on its own. Once the command needs a style guide, an email template or a Python script that does the math the same way every time, a single file gets cramped. Either you paste everything into it, and every invocation drags along pages you need one time in ten, or you write "find the script somewhere" and hope.

A skill is the same thing with a folder around it. The instructions live in `SKILL.md`, the supporting files sit next to it, and Claude reads or runs them only when they're needed. The description works as the switch: when your request matches it, Claude loads the skill on its own. A new colleague who types "can you put together the June report?" gets the team's procedure without knowing it exists.

## 9.1 Commands and skills, one system

In the first edition, commands and skills were two separate mechanisms, and commands looked like they were on their way out. Today Claude Code has merged them. A `.claude/commands/report.md` file and a `.claude/skills/report/SKILL.md` skill both create `/report` and work the same way. Command files are the older format; they still work and accept the same frontmatter as skills, except `name` and `paths`. For new work the docs recommend skills, and if a command and a skill share a name, the skill wins.

So the choice is about shape: a single file or a folder. Here's how I decide:

| You need | Format |
| :---- | :---- |
| A reusable prompt with no supporting files | A file in `.claude/commands/`, or a skill with just `SKILL.md` |
| A procedure that runs Python or Bash scripts | A skill with `scripts/` |
| Guides, calculation rules or examples to consult only when needed | A skill with `references/` |
| Boilerplate for the output, such as an email or a header | A skill with `templates/` |
| Automatic activation only on certain project files | A skill with `paths` |

Two examples from the book. `/fix-tests` from chapter 8 stays a command: it's a prompt and needs nothing around it. The monthly SaaS report from chapter 6, on the other hand, has three scripts, some calculation rules and a fixed email text, so it becomes the `data-analysis-saas-monthly` skill in section 9.4. Move to a folder when you notice you're pasting resources into the command file just to keep them close to the prompt.

## 9.2 Anatomy of a skill

### The folder

A skill is a folder with a lowercase, hyphenated name, containing at least a `SKILL.md` file. Everything else is optional. This is the layout I use:

```text
.claude/skills/skill-name/
├── SKILL.md          required: frontmatter and instructions
├── references/       guides and rules, read when needed
│   ├── style-guide.md
│   └── business-rules.md
├── scripts/          scripts to run
│   ├── analyze.py
│   └── generate-report.sh
└── templates/        boilerplate for the output
    ├── email-summary.txt
    └── report-header.md
```

The subfolder names are a convention: Claude Code doesn't treat them specially, and Anthropic's skill-creator calls the templates folder `assets/`. What matters is that `SKILL.md` says when to open which file. Claude Code loads a skill in three levels:

1. The name and description are in the context of every session, even when you don't use the skill. That's how Claude figures out when it would help.
2. The body of `SKILL.md` enters the context when the skill triggers or when you invoke it yourself.
3. Supporting files enter only when Claude reads them, following the instructions in the body. Scripts get executed, and only their output reaches the context.

The first level has a cost you always pay, and `/skills` shows it to you skill by skill.

![The /skills list with project and personal skills, each with the token cost of its description](figures/cap-09/fig-02.png)

Each section reads `.claude/skills` and `.claude/commands` together. Keep the second level short: the skill-creator suggests staying under 500 lines and moving the rest into separate files that `SKILL.md` points to.

### The frontmatter

`SKILL.md` starts with a YAML block between two `---` lines, followed by the instructions in Markdown. Every field is optional, but without `description` Claude has no way of knowing when to use the skill. The ones you'll actually need:

| Field | What it does |
| :---- | :---- |
| `name` | The name, and therefore the command: `report-pdf` becomes `/report-pdf`. Lowercase letters, numbers and hyphens. Defaults to the folder name |
| `description` | What the skill does and when to use it. Claude decides from this whether to load it |
| `when_to_use` | More cases in which to use it, appended to the description. Together they're truncated at 1,536 characters |
| `argument-hint` | The argument hint shown in the menu, for example `<file-csv>` |
| `arguments` | Names for the positional arguments, used in the body as `$name` |
| `disable-model-invocation` | With `true`, the skill runs only when you type it |
| `user-invocable` | With `false`, it disappears from the `/` menu and only Claude uses it |
| `allowed-tools` | Tools Claude uses without asking while the skill is active |
| `model`, `effort` | Model and reasoning level for the rest of the turn |
| `context: fork` | Runs the skill in a subagent; the `agent` field says which one |
| `paths` | Globs that limit automatic activation to matching files |

Arguments work the same as in the chapter 8 commands: `$ARGUMENTS` takes everything, `$0`, `$1` and so on take words by position, and `${CLAUDE_SKILL_DIR}` is the path of the skill's folder, handy for running its scripts from any directory. With `arguments` you give the positions names and the body reads better: `$csv` instead of `$0`. You'll use it in section 9.4.

There's a common misunderstanding about `allowed-tools`. The field only adds permissions: the listed tools run without confirmation while the skill is active, up to your next message, and every other tool stays available under the session's normal permissions. To stop a skill from using a tool, the field is `disallowed-tools`.

With `context: fork` the skill runs in a subagent with its own context, which starts empty. It doesn't see the conversation, so the body of `SKILL.md` has to contain everything it needs. Since version 2.1.218 a forked skill runs in the background and your turn doesn't wait for it; to wait for the result, add `background: false`. It's meant for long jobs that would fill the main context with intermediate output (subagents are the subject of chapter 10).

If you also want to upload the skill to claude.ai or use it through the API, the Agent Skills standard accepts only `name`, `description`, `license`, `compatibility`, `metadata` and `allowed-tools`; everything else is a Claude Code extension.

### The description is the trigger

The most common first-time mistake is writing the description as documentation for a colleague. A model reads it, and from those two lines it has to work out whether your request falls within the skill. A vague description gives you a skill that never triggers, or that triggers when it has no business doing so:

```yaml
# too vague
description: Analyzes data.
```

This one says what it does, on what data, and with what words the user will ask for it:

```yaml
# specific
description: Runs a statistical analysis of one column of a CSV file
  (type, count, missing values, mean, standard deviation, min, max,
  quartiles, outliers). Use it when the user asks to analyze,
  describe, profile or inspect a column, including in Spanish
  (describe la columna, perfila la columna).
```

Start with what it does, with a verb. Name the domain (CSV, column, report) and the formats. Add an explicit sentence about when to use it, with the words people will really type in the prompt: if your team works in two languages, put them in both. The skill-creator's instructions add a useful tip. Claude tends to use skills less than it should, so a slightly pushy description ("use it even if the user doesn't explicitly mention the report") works better than a cautious one. The opposite limit is length: the description weighs on every session, and four or five lines are almost always enough.

One last detail explains a lot of "my skill won't run" complaints: Claude consults skills for tasks it can't easily handle on its own. A one-step request like "read this file" may not trigger any skill even with a perfect description, because Claude just does it with the basic tools. Multi-step or domain-specific requests are where the description makes the difference.

## 9.3 The first skill: report-pdf

Start with a small skill, in the chapter 2 lab. `cc-advanced-lab` has a three-row CSV, `data/vendite.csv`, with sales for January, February and March 2026. The `report-pdf` skill turns it into a summary table in the chat and the same report as a PDF, with ReportLab as in chapter 6.

```bash
cd ~/cc-advanced-lab
mkdir -p .claude/skills/report-pdf
```

Create `.claude/skills/report-pdf/SKILL.md`:

```markdown
---
name: report-pdf
description: Builds a sales report from a CSV file, with a summary table in the chat and the same report as a PDF in the output/ folder. Use it when the user asks for a report, a summary, the totals or a PDF from a CSV file.
argument-hint: <file-csv>
allowed-tools: Read Write Bash(python3 *)
---

The file to use is $ARGUMENTS. If it's empty, use the CSV mentioned in
the request; if there isn't one, ask which file to analyze.

1. Read the CSV and find the numeric column.
2. Reply with a Markdown table with the number of rows, the total,
   the minimum, the maximum and the mean of the column, the mean with
   two decimal places.
3. Create output/report-<CSV name without extension>.pdf with ReportLab:
   title "Sales report", today's date, the table from step 2 and,
   below it, every row of the CSV. Use the script output/genera_pdf.py,
   which takes the CSV path as its first argument: if it doesn't exist,
   write it, then run it with python3.
4. If ReportLab isn't installed, stop and suggest
   `pip install reportlab`. Don't install it yourself.

Never modify the input CSV.
```

The description contains the words you'll use to ask for the job: report, summary, totals, PDF, CSV. `allowed-tools` skips the confirmations for the script and for `python3` in Manual mode. Step 3 makes Claude reuse the script if it already exists: the first time Claude writes it, and from the second run on the PDF always comes out the same. The skill fits in one file on purpose, because in chapter 14 you copy it into a plugin with a single `cp` of `SKILL.md`. You do need ReportLab, though: if the lab's Python environment doesn't have it, `pip install reportlab`.

If Claude Code was already open, run `/reload-skills`, which rereads the skill and command folders, then `/skills`: `report-pdf` should show up among the project skills. Now try it without naming it:

```text
can you make me a PDF report of the sales in data/vendite.csv?
```

Claude loads the skill and replies with the table. The numbers should be: 3 rows, total 358, minimum 95, maximum 143, mean 119.33. The total is the same one `tests/test_report.py` checks, so you get an immediate cross-check. The PDF ends up in `output/report-vendite.pdf`. Then try the explicit invocation, which is the one you'll use in scripts and in chapter 14:

```text
/report-pdf data/vendite.csv
```

If Claude answers the natural-language prompt without loading the skill, the problem is almost always the description: it doesn't contain the words you used to ask. Once it works, commit `.claude/skills/report-pdf/`, and if you don't want the PDFs in the repository, add `output/` to `.gitignore`.

## 9.4 A complete skill: data-analysis-saas-monthly

Now for the skill previewed in chapter 6. From a CSV of SaaS metrics like `saas_metrics.csv` it produces three files for a client (the PDF report, a static HTML dashboard with Chart.js that opens without a server, and the Excel file with data and summary) plus the email that goes with them.

I put it in the project because the columns and the calculation rules belong to this project: in `~/.claude/skills/` it would weigh on the context of every session, even where it's useless.

### Step 1: the structure

```bash
cd ~/progetti/analisi-saas
mkdir -p .claude/skills/data-analysis-saas-monthly/{scripts,references,templates}
```

If you'd rather, ask Claude with a one-line prompt: for folders it makes no difference.

### Step 2: SKILL.md

Create `.claude/skills/data-analysis-saas-monthly/SKILL.md`:

```markdown
---
name: data-analysis-saas-monthly
description: Generates a client's monthly SaaS report from a metrics CSV (mrr, churn_rate, plan, region) and produces a PDF, an HTML dashboard and an Excel file. Use it when the user asks for the monthly report, the month's analysis or an MRR and churn summary for a client, even if they don't mention the formats (monthly report, SaaS metrics, MRR report).
argument-hint: <csv> <cliente> <mese>
arguments: [csv, cliente, mese]
allowed-tools: Read Bash(python3 *)
---

# Monthly SaaS report

Input: the CSV $csv, the client $cliente, the month $mese.
If any of the three is missing, ask for it before starting.
All output files go in output/$cliente/.
The references/, scripts/ and templates/ paths are relative to
${CLAUDE_SKILL_DIR}.

## Resources

- references/struttura-csv.md: required and optional columns.
- references/regole-metriche.md: how the derived metrics are calculated.
- templates/email-riepilogo.txt: the email that goes with the files.
- scripts/: run the scripts, no need to read them.

## Phase 1: validation

1. Compare the columns of $csv with references/struttura-csv.md.
   If a required column is missing, stop and tell me which one.
2. Run `python3 ${CLAUDE_SKILL_DIR}/scripts/metriche.py $csv output/$cliente`.
   The script prints the per-month summary and writes metriche.xlsx.

## Phase 2: analysis

3. Apply references/regole-metriche.md to the summary: month-over-month
   change, outliers, trend over the last three months.
4. Don't recalculate by hand the numbers the script has already printed.

## Phase 3: output

5. Run scripts/genera_grafici.py and scripts/genera_report.py with
   `--csv $csv --outdir output/$cliente`; also pass
   `--cliente "$cliente, $mese"` to genera_report.py.
6. Write output/$cliente/dashboard.html: a single page with Chart.js
   from a CDN and the summary data embedded as JSON, no server.
7. Fill in templates/email-riepilogo.txt and save it as
   output/$cliente/email.txt.

## Phase 4: wrap-up

8. List the files produced with their paths.
9. Name the three metrics that deserve attention and why.
10. Suggest one concrete next step.
```

The phases help you too: when something goes wrong, you can see right away whether the work stopped at validation or at output. Step 4 is there because, without it, Claude may redo the math on the CSV by itself and land on a different total from the script's. This way the code computes the numbers and Claude comments on them.

### Step 3: the references

`references/struttura-csv.md` describes the CSV the skill expects, with the columns of the chapter 4 dataset:

```markdown
# Expected CSV structure

Required columns:
- month (int, 1-12)
- plan (string: free | silver | gold)
- region (string: Europe | North America | Asia Pacific)
- new_signups (int)
- cancellations (int)
- mrr (float, euros)
- churn_rate (float, percentage)

Optional columns (if missing, skip the metrics that use them):
- date (YYYY-MM-DD)
- retention_rate
- support_tickets
- ai_voice_usage, ai_text_usage
```

`references/regole-metriche.md` pins down the business rules, the ones Claude would otherwise interpret its own way every time:

```markdown
# Metric rules

- Monthly MRR: sum of mrr over the silver and gold rows. The free plan
  doesn't contribute and must be excluded.
- MoM change: (this month's MRR - last month's MRR) / last month's MRR.
- Monthly churn: mean of churn_rate over the paid rows. In the report
  call it "average churn", because it isn't recalculated per customer.
- Outliers: values more than 2 standard deviations from the mean of the
  same plan and region combination. Flag them, don't remove them.
- Trend: simple linear regression on the MRR of the last three months.
```

### Step 4: the scripts

You already have two of the scripts: `genera_grafici.py` and `tools/genera_report.py` from chapter 6. They work on the project's CSV, so the copies for the skill need a way to specify the input file and the output folder:

```text
Copy tools/genera_grafici.py and tools/genera_report.py into
.claude/skills/data-analysis-saas-monthly/scripts/.
In the copies, add the arguments --csv (input file) and --outdir
(output folder, default output/); to genera_report.py also add
--cliente, to be put in the PDF title.
Leave the originals in tools/ unchanged.
```

The third script is new. It validates the columns, computes the per-month summary and writes the Excel file. Save it as `.claude/skills/data-analysis-saas-monthly/scripts/metriche.py`:

```python
#!/usr/bin/env python3
"""Valida il CSV delle metriche SaaS, stampa il sommario e scrive l'Excel.

Uso: python3 metriche.py <csv> <cartella-output>
"""
import sys
from pathlib import Path

import pandas as pd

RICHIESTE = [
    "month", "plan", "region", "new_signups",
    "cancellations", "mrr", "churn_rate",
]


def carica(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    mancanti = [c for c in RICHIESTE if c not in df.columns]
    if mancanti:
        sys.exit(f"Colonne mancanti: {mancanti}")
    return df


def sommario(df: pd.DataFrame) -> pd.DataFrame:
    pagati = df[df["plan"] != "free"]
    per_mese = pagati.groupby("month").agg(
        mrr=("mrr", "sum"),
        nuovi=("new_signups", "sum"),
        cancellazioni=("cancellations", "sum"),
        churn_medio=("churn_rate", "mean"),
    )
    per_mese["mrr_mom_pct"] = per_mese["mrr"].pct_change() * 100
    return per_mese.round(2).reset_index()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("Uso: python3 metriche.py <csv> <cartella-output>")
    df = carica(sys.argv[1])
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    tabella = sommario(df)
    with pd.ExcelWriter(out / "metriche.xlsx", engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Dati", index=False)
        tabella.to_excel(writer, sheet_name="Sommario", index=False)
    print(tabella.to_string(index=False))
    print(f"Excel scritto in {out / 'metriche.xlsx'}")
```

The script prints the summary to stdout because that's how the numbers reach Claude: what enters the context is the six-row table, not the code and not the CSV's 54 rows. If a required column is missing, it exits with a clear message, and Claude reports that back to you instead of analyzing bad data.

### Step 5: the email template

`templates/email-riepilogo.txt`:

```text
Subject: Monthly SaaS report, [CLIENT] [MONTH]

Hi [NAME],

here's the metrics summary for [CLIENT] for [MONTH].

THIS MONTH'S NUMBERS
Total MRR:         [TOTAL_MRR] EUR
MoM change:        [MOM_DELTA]%
Average churn:     [CHURN]%
New signups:       [NEW]

THREE THINGS TO WATCH
1. [POINT_1]
2. [POINT_2]
3. [POINT_3]

ATTACHED
report.pdf       full report with charts
metriche.xlsx    raw data and per-month summary
dashboard.html   interactive charts, opens in the browser

NEXT STEP
[SUGGESTION]

Generated with Claude Code, skill data-analysis-saas-monthly
```

### Step 6: the test run

Run `/reload-skills` and check with `/skills` that the skill appears among the project skills. Then ask for the job without naming it, the way a colleague would:

```text
I've got the June SaaS metrics in data/saas_metrics.csv.
Can you put together the monthly report for startup_alpha?
```

Claude loads the skill, runs `metriche.py`, reads the rules, generates the files in `output/startup_alpha/` and wraps up with the list of files and the three metrics to watch. The explicit form, useful when you have several clients in a row like the agency in chapter 6, is:

```text
/data-analysis-saas-monthly data/saas_metrics.csv startup_alpha June
```

### Edge cases

After the first few runs you always find some: a client with fewer columns, a CSV exported in latin-1 from an old management system, a month with zero MRR that breaks the month-over-month change. Add a section at the bottom of `SKILL.md`:

```markdown
## Edge cases

- Missing optional columns: skip the metrics that use them and
  say so in the executive summary.
- Previous month's MRR is zero (new client): the MoM change
  is n/a, not an error and not an infinite value.
- CSV not found: ask for the full path before going ahead.
- The script fails with UnicodeDecodeError: save a UTF-8 copy of the
  CSV in output/$cliente/ and rerun on that.
```

Add one rule at a time and test it with a CSV built for the purpose. If a change to `SKILL.md` doesn't seem to have landed, `/reload-skills`.

## 9.5 The skill-creator

Writing `SKILL.md` by hand is how you learn what a skill is made of. For everyday work the skill-creator is faster: a skill from Anthropic that builds other skills through a conversation and then puts them to the test. You install it as a plugin from the official marketplace:

```text
/plugin install skill-creator@claude-plugins-official
```

After `/reload-plugins` you invoke it with the plugin prefix, `/skill-creator:skill-creator`, or you say you want to create or improve a skill and let it trigger on its own. If you sign in with a claude.ai account that has the skill-creator turned on, the skill arrives already synced: `/skills` lists it under `claude.ai sync` and you run it as `/anthropic-skills:skill-creator`, without installing the plugin.

### How it works

The first thing it does is look at the conversation. If you've just done a job by hand, say the charts for a CSV, it offers to turn that into a skill and pulls the steps from the history.

![The skill-creator offers options based on the conversation: improve a skill you just used, create a new one, or turn the chart work into a skill](figures/cap-09/fig-01.png)

If you start from scratch, it asks four questions: what the skill should do, when it should trigger, what format the output has and whether you want test cases. Then it asks about edge cases, input formats and dependencies. For a CSV profiling skill, an answer like this is enough for the question about what to do and when:

```text
Analyzes a CSV file with full profiling to detect anomalies and
outliers. Use it when the user asks to analyze, profile, describe or
check a column or a dataset, or when they ask to find outliers or
statistical anomalies.
```

That answer becomes the frontmatter description, already written to trigger the skill. If you say in the conversation that it can use Python, the skill-creator also writes the script in `scripts/`.

The part that justifies the install is the testing. The skill-creator writes a few test prompts and, for each one, launches two subagents in the same turn, one with the skill and one without. You see the results side by side on a page in the browser, you comment on each output, and it rewrites the skill and runs again. If it notices that every run wrote the same helper script, it suggests putting it in `scripts/` once and for all.

At the end it offers to optimize the description. It prepares about twenty requests, half that should trigger the skill and half that look similar but shouldn't, runs each one three times, tries up to five versions of the description and keeps the one that does best on a held-out set of requests. Every run eats into your plan, so skip this step for a trivial skill.

### When to skip it

The skill-creator pays off when the skill has scripts or when you want to measure the difference with and without the skill before sharing it. I write by hand when I'm editing an existing skill and when the skill is a twenty-line `SKILL.md` like `report-pdf`: there, the interviews and benchmarks cost more than the skill. The two approaches combine well, with scaffolding from the skill-creator and the finishing done by hand. If you installed Superpowers in chapter 8, its `writing-skills` skill covers the same ground with an approach closer to TDD.

::: {.callout .callout-prompt}
[Reusable prompt]{.callout-title}

A sketch of a new skill, to give Claude directly or to sort out your ideas before the skill-creator:

```text
I want to create a Claude Code skill called [SKILL-NAME].

It should trigger when the user asks [DESCRIBE THE TRIGGER IN PLAIN WORDS].
The workflow has these steps:
1. [STEP 1]
2. [STEP 2]
3. [STEP 3]

Does it need [Python scripts / references / templates]? [YES/NO, specify]

Create the folder structure in .claude/skills/[SKILL-NAME]/ (or in
~/.claude/skills/[SKILL-NAME]/ if I need it in all my projects),
write SKILL.md with frontmatter optimized for automatic triggering,
and add any supporting files in the appropriate subfolders.
```
:::

## 9.6 Ready-made skills

Before writing a skill from scratch, check whether someone has already done it. Third-party skills almost always come inside a plugin, from a marketplace. Anthropic's official one, `claude-plugins-official`, is configured on first launch; the community one, `claude-community` (repository `anthropics/claude-plugins-community`), is the one you add when the official marketplace doesn't have what you're looking for. Plenty of vendors publish their skills in the official one: as of October 2026 there were, for example, `duckdb-skills` and `huggingface-skills`, alongside the skill-creator and Superpowers. You browse them in the Discover tab of `/plugin`; chapter 14 explains how to evaluate them.

For a developer, the starting point is still Superpowers, which you installed in chapter 8. Its skills worth knowing right away:

| Skill | What it does |
| :---- | :---- |
| `test-driven-development` | Drives the TDD cycle: first the failing test, then the code |
| `systematic-debugging` | Splits debugging into phases: reproduce, hypothesize, verify, fix |
| `brainstorming` | Explores design alternatives before you write code |
| `verification-before-completion` | Checks that the work is really done before calling it finished |
| `writing-skills` | Designs and tests new skills |

For code review you don't need a plugin: `/code-review` is a skill built into Claude Code, and you use it on the Photogallery in chapter 22.

::: {.callout .callout-warning}
[Warning]{.callout-title}

Before installing a third-party skill, open its `SKILL.md` in the repository and read it. The `` !`command` `` lines run on your machine as soon as the skill activates, before Claude sees anything, and the scripts in `scripts/` run with your permissions. Reading it also tells you what it expects from the project: some skills assume a certain folder layout or tools already installed, such as pytest or eslint. If you don't trust command injection, `"disableSkillShellExecution": true` in the settings turns it off.
:::

To remove one of your own skills, delete its folder. Plugin skills are managed through the plugin: the Installed tab in `/plugin` disables or removes it, and from the terminal there are `claude plugin update` and `claude plugin uninstall`.

## 9.7 Organizing your skills

### Where they live

| Level | Path | Notes |
| :---- | :---- | :---- |
| Personal | `~/.claude/skills/<name>/SKILL.md` | In all your projects, on this machine |
| Project | `.claude/skills/<name>/SKILL.md` | In the repository, anyone who clones it gets it |
| Subfolder | `<folder>/.claude/skills/...` | With duplicate names, invoked as `/apps/web:deploy` |
| `--add-dir` | `.claude/skills/` in the added folders | Handy for testing |
| Plugin | `<plugin>/skills/<name>/SKILL.md` | With the prefix: `/plugin-name:skill-name` |
| claude.ai account | Synced skills | Prefix `anthropic-skills:` |

The rule I follow: generic workflows I use everywhere go in `~/.claude/skills/`, workflows tied to the project's domain go in `.claude/skills/`, like the two skills in this chapter. Project skills get committed, and anyone who runs `git pull` gets them with no setup instructions.

### Names and syncing

After a few months, a list of folders like `report-generator`, `my-skill-v2`, `test-cosa` no longer tells you what's stable and what's an experiment. I use three prefixes:

| Prefix | Meaning | Example |
| :---- | :---- | :---- |
| `personal-` | Personal skills, not to be shared | `personal-daily-standup` |
| `team-` | Team skills, committed to the repo | `team-code-review-checklist` |
| `wip-` | Skills in development, not yet stable | `wip-deploy-to-k8s` |

I keep my personal skills in a dotfiles repository, with a symlink in place of the folder in `~/.claude/`:

```bash
# layout in the dotfiles repo:
#   dotfiles/claude/skills/personal-daily-standup/
#   dotfiles/claude/skills/personal-code-explain/
ln -s ~/dotfiles/claude/skills ~/.claude/skills
```

If `~/.claude/skills` already exists, move its contents into the repository first, otherwise `ln` creates the link inside the folder.

Experimental skills live outside the paths Claude Code reads, in `~/skills-wip/.claude/skills/`, where they don't weigh on any session. To try one, I start `claude --add-dir ~/skills-wip`, which loads them for that session only. Once it's stable, I move it to its final location and drop the `wip-`.

### What they cost

Every skill costs you its description in every session. With three skills you won't notice; with thirty, between yours and the plugins', you're taking up a slice of context and there are more chances of the wrong one triggering. For skills only you launch, like a deploy, `disable-model-invocation: true` also takes the description out of the context: Claude can no longer use the skill on its own, so it doesn't need to see it. With `paths`, on the other hand, you limit automatic activation to the files that matter, for example the CSVs in `data/`.

You can see what each description weighs in `/skills`. In chapter 15 you use `/skill-doctor`, which puts the context cost next to how often each skill is used and tells you which skills are worth the space they take.

### When a skill doesn't show up

If a skill you just created doesn't appear in `/skills`, check these in order:

1. The file is named exactly `SKILL.md` and sits one level below `skills/`, as in `.claude/skills/report-pdf/SKILL.md`.
2. The frontmatter is valid YAML: two `---` lines, spaces and not tabs, closed quotes.
3. `name` is lowercase with hyphens, and it should match the folder name: the Agent Skills standard requires it.
4. You ran `/reload-skills` after creating the folder.
5. There's no other skill with the same name at a different level.

If you can't find the problem, paste the file into Claude and describe what's happening.

## Summary {.unlisted}

- Commands and skills are the same system: a file in `.claude/commands/` is enough for a prompt, the `.claude/skills/<name>/` folder is for scripts, references and templates.
- Claude always sees each skill's name and description; the body arrives when the skill triggers, the supporting files when the instructions call for them.
- The description decides whether the skill runs: what it does, on what data, with what words the user will ask for it.
- Have the scripts compute the numbers and print them, and tell Claude in `SKILL.md` not to redo them by hand.
- The skill-creator, from the official marketplace, writes the skill and compares it against a run without it.
- Domain skills go in the project and get committed, generic ones in `~/.claude/skills/`; `/skills` and `/skill-doctor` tell you how much they weigh.

## Exercise {.unlisted}

Pick a job you do at least once a week: reviewing a PR, writing a release changelog, writing tests for a new function, setting up a development environment.

1. Install the skill-creator and ask it to create a skill for that job.
2. Answer its questions: what it does, when it should trigger, what output it produces, which edge cases you know about.
3. Accept the testing with the test prompts and compare the outputs with and without the skill.
4. Open the generated `SKILL.md` and reread the description: it should contain the words you'd use to ask for that job.
5. In a real project, write a natural-language request without naming the skill.

The exercise is done when the skill appears in `/skills`, triggers at step 5 without you naming it and, in the step 3 comparison, the result with the skill is better than the one without. It takes about half an hour.

If you want to sort out your ideas before opening the skill-creator, start from the prompt in the `cap-08/` folder of the `github.com/hidran/claude-code-book-snippets` repository (first-edition numbering): it has you pin down the skill's name, trigger and steps.
