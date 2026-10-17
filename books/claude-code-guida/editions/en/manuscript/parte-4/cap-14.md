# Chapter 14. Plugins and marketplaces, packaging skills, agents and hooks

::: {.chapter-goals}
[What you'll learn]{.callout-title}

You'll learn to install a plugin from the official marketplace knowing what it costs you in context and whom you're trusting, then to build your own: `cc-lab-toolkit`, which bundles the `report-pdf` skill from chapter 9, a Python review agent and the formatting hook from chapter 12. You share it with your team through a marketplace, and at the end you measure whether it actually helps with `claude plugin eval`.

[Prerequisites]{.callout-title}

The `cc-advanced-lab` project from chapters 11-13, with the `.claude/skills/report-pdf/SKILL.md` skill and the `.claude/hooks/format-python.sh` script. Git 2.31 or later, which `claude plugin eval` needs (check with `git --version`). An empty `~/cc-plugins` folder to work in.

:::

## 14.1 Why a plugin

Over the last few chapters you've piled up parts: a skill in `.claude/skills/`, an agent in `.claude/agents/`, a hook registered in `.claude/settings.json` with its script in `.claude/hooks/`, maybe an MCP server in `.mcp.json`. Each one works fine on its own, inside the project where you created it.

The trouble starts the day you want the same things in a second project, or a colleague asks for them. Now you're copying folders by hand and pasting chunks of `settings.json` while trying not to break the JSON that's already there. A month later there are three copies and nobody remembers which one is right.

A **plugin** is Claude Code's answer to that problem. It's a folder holding those components plus a small manifest file, and Claude Code loads it as a single unit. You install it with one command, update it by bumping the version number and disable it without touching the project's files. It can hold everything you've seen in Part III and in this part:

- skills and agents, which take the plugin's name as a prefix;
- hooks, the deterministic automations tied to Claude Code events;
- MCP servers, declared in a `.mcp.json` at the plugin root.

In chapter 8 you already used a plugin as a user: Superpowers. When you installed it you got a whole set of skills in one go, without copying anything. In this chapter you move to the other side of the counter and write one.

## 14.2 The /plugin manager and the official marketplace

Open Claude Code in any project and type:

```text
/plugin
```

The plugin manager opens, with the Discover, Installed and Marketplaces tabs. You move between them with the arrow keys.

- Discover lists the plugins available in the marketplaces you've added.
- Installed shows what you've installed and where it came from; this is where you disable or remove a plugin.
- Marketplaces lists the registered sources: the official one, the ones you added, your team's.

When a plugin won't load, the reason is in the Errors tab of the same manager.

Anthropic's official marketplace, `claude-plugins-official`, is added automatically the first time you start Claude Code: you don't have to register it. There's also a community marketplace, `claude-community`, which you can add when you need something the official one doesn't have. If you follow a tutorial that has you add `anthropics/claude-code` as a marketplace, know that it's only a demo marketplace: fine for poking around, not for real work.

The same Superpowers from chapter 8 now lives in the official marketplace and installs with `/plugin install superpowers@claude-plugins-official`.

<!-- TODO screenshot: gestore /plugin sulla scheda Discover, con il dettaglio di un plugin ufficiale e la stima del costo in contesto -->

### The context cost

Before installing anything, open the plugin's detail page in Discover and look at the estimated context cost. An enabled plugin loads the name and description of every one of its skills and agents into every session, even if you never use them. A skill's body enters the context only when the skill fires, but the descriptions are always there: it's the same mechanism you saw in chapter 9, multiplied by every component in the plugin.

A plugin with two skills weighs very little. A collection of forty skills, of which you use three, takes a slice of your context window in every session and raises the odds of a skill firing when it shouldn't. In chapter 15 you'll see how to read that weight with `/context` and how to work out, with `/skill-doctor` and `/usage`, which skills and plugins are worth what they cost.

### Whom you trust

The second thing I check is who publishes the plugin. A plugin runs code with your permissions: its hooks run commands on your machine every time their event fires, and an MCP server declared in the plugin is a process that starts with the session. As you saw in chapter 11, hooks and MCP servers live outside the command sandbox: only permissions apply to them. A hook in a plugin downloaded from an unknown repository has the same power as a script you run yourself from the terminal.

The official marketplace is a sensible place to start; the community one already calls for a bit more care. For everything else my rule is simple: before installing, I open the repository, read `hooks/hooks.json` and the scripts it calls, and look at the `.mcp.json` if there is one. It's a handful of files and takes five minutes to read.

The official marketplace also has plugins dedicated to security: `security-guidance`, which checks Claude's edits while it works, and Claude Security, which runs a multi-agent vulnerability scan and proposes patches.

### Installing plugin-dev

The first plugin I install is `plugin-dev`, from the official marketplace. It adds skills and agents for writing plugin components (skills, hooks, MCP servers) and for validating the result, and I keep it around as a helper for the rest of the chapter. You can select it in Discover or install it straight from the prompt:

```text
/plugin install plugin-dev@claude-plugins-official
```

Once it's installed, `/plugin-dev:create-plugin` followed by a description of the plugin you want starts a conversation in which Claude designs it, creates it and validates it with you. Here you'll write the plugin by hand, because you need to see every piece.

The syntax is always the same: plugin name, at sign, marketplace name. Claude Code shows you the plugin's components and then asks for the installation scope, with the same logic you saw for MCP servers in chapter 13:

| Scope | Applies to |
|---|---|
| user | all your projects |
| project | the whole team, through the shared `.claude/settings.json` in Git |
| local | only you, in this repository |

For a personal helper like `plugin-dev` I pick user. Project makes sense when you want everyone who clones the repository to get the same plugin, as you'll see in section 14.5. When the installation finishes, check:

```text
/plugin list
```

`plugin-dev@claude-plugins-official` should appear among the installed plugins.

Everything you do from the manager has a terminal equivalent, handy in setup scripts and when you want to check the state without opening a session:

```bash
claude plugin list
claude plugin details plugin-dev@claude-plugins-official
claude plugin disable plugin-dev@claude-plugins-official
claude plugin enable plugin-dev@claude-plugins-official
```

There are also `install`, `uninstall` and `update`, plus the `claude plugin marketplace` group with `add`, `list`, `remove` and `update`.

## 14.3 Building cc-lab-toolkit

Now for your plugin. I call it `cc-lab-toolkit` because it collects the lab's tools: the skill that builds a report from a CSV, an agent that reviews Python code and the hook that formats `.py` files after every edit.

### The layout

A plugin is a folder with a `.claude-plugin/` subfolder that holds only the manifest, `plugin.json`. Everything else sits at the plugin root: `skills/`, `agents/`, `hooks/` with the `hooks.json` file and, if you need it, a `.mcp.json` for MCP servers. Create the folders:

```bash
cd ~/cc-plugins
mkdir -p cc-lab-toolkit/.claude-plugin
mkdir -p cc-lab-toolkit/skills/report-pdf
mkdir -p cc-lab-toolkit/agents
mkdir -p cc-lab-toolkit/hooks/scripts
```

I'd make `~/cc-plugins` a Git repository right away (`git init`): you'll need it to share the plugin in section 14.5 and for the evals in 14.7.

### The manifest

Create `cc-lab-toolkit/.claude-plugin/plugin.json`:

```json
{
  "name": "cc-lab-toolkit",
  "description": "CSV reports, code review and automatic formatting for Python projects",
  "version": "1.0.0",
  "author": {
    "name": "Hidran Arias"
  }
}
```

The only required field is `name`, and it matters more than it looks: it becomes the prefix of every skill and every agent in the plugin. Once the `report-pdf` skill is inside `cc-lab-toolkit`, it's called `/cc-lab-toolkit:report-pdf`. The prefix prevents collisions with skills of the same name in other plugins. So pick a short name, lowercase with hyphens: you'll be typing it a lot.

`version` becomes important once the plugin is distributed, because it's the number that delivers updates to whoever installed it. `description` is what your colleagues read in the manager before deciding whether to install it: write it for them. Put your own name in `author` instead of mine.

### The skill

The skill is the one from chapter 9. Copy it as is into the folder you just created:

```bash
cp ~/cc-advanced-lab/.claude/skills/report-pdf/SKILL.md cc-lab-toolkit/skills/report-pdf/
```

Inside a plugin the skill keeps its format: same folder named after the skill, same `SKILL.md` with its frontmatter. The only change is the name you invoke it with.

If you no longer have the skill because you rebuilt the lab from scratch in chapter 11, write it again from the `SKILL.md` in section 9.3 before going on: it's a single file.

### The agent

Create `cc-lab-toolkit/agents/python-reviewer.md`:

```markdown
---
name: python-reviewer
description: Reviews Python code for correctness, readability and missing tests. Use it after changes to .py files.
tools: Read, Grep, Glob
model: sonnet
---

You are a senior Python code reviewer. For each modified file:

1. Report correctness bugs with file and line.
2. Report functions without tests in tests/.
3. Suggest at most three readability improvements.

Do not modify files: return only the report.
```

It's the same format as the agents in chapter 10: a Markdown file with frontmatter (name, description, tools, model) and the system prompt in the body. The choice that matters is in the `tools` line. The agent has no `Edit`, `Write` or `Bash`: even if the model decided to fix a bug, it wouldn't have the tool to do it. The last line of the prompt says so in words; the tool list guarantees it.

There's one detail you should know. In the native builds for macOS, Linux and WSL, the `Grep` and `Glob` tools usually aren't there: Claude searches files through `Bash`. On those installations the agent effectively works with `Read` alone, which is enough to review the files you name and their tests. Don't add `Bash` just to give it search: with a shell the agent can also write, and the read-only guarantee is gone.

The description follows the rule you saw for skills: it says when to use the agent ("after changes to `.py` files"), so Claude can hand it the review even when you don't name it.

### The hooks

The formatting hook from chapter 12 has two parts: the script and its registration in the project's `settings.json`. In the plugin the script goes in `hooks/scripts/`:

```bash
cp ~/cc-advanced-lab/.claude/hooks/format-python.sh cc-lab-toolkit/hooks/scripts/
```

`cp` keeps the original's executable bit. If you write the script from scratch instead, remember `chmod +x`, or the hook fails without any visible sign. For convenience, here's the script:

```bash
#!/bin/bash
# Format the Python files Claude edited with ruff
FILE_PATH=$(jq -r '.tool_input.file_path // empty')

if [[ "$FILE_PATH" == *.py ]]; then
  ruff format "$FILE_PATH" >/dev/null 2>&1
fi

exit 0
```

The registration goes in `cc-lab-toolkit/hooks/hooks.json`:

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

The format is identical to the `hooks` key in `settings.json`: same `PostToolUse` event, same `Edit|Write` matcher, same `command` type. The only difference is the script path. In chapter 12 you used `$CLAUDE_PROJECT_DIR`, which points at the project's root folder. Here the script lives in the plugin, not in the project, so you use `${CLAUDE_PLUGIN_ROOT}`, which points at the folder where the plugin is installed. The escaped quotes around the variable handle paths with spaces. An absolute path like `/Users/yourname/cc-plugins/...` would only work on your machine and would break for the first colleague who installs the plugin.

::: {.callout .callout-warning}
[Warning]{.callout-title}

If the chapter 12 hook is still in `cc-advanced-lab`'s `.claude/settings.json`, then once you load the plugin `ruff` runs twice after every edit: once for the project hook, once for the plugin's. It does no harm, but it's the kind of duplicate nobody remembers leaving behind. Once the hook lives in the plugin, remove it from the project's `settings.json`.
:::

### The final tree

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

To make sure you haven't forgotten anything:

```bash
find cc-lab-toolkit -type f | sort
```

You should see five files: the manifest, the skill, the agent, `hooks.json` and the script. If you wanted to add an MCP server, say the DBHub from chapter 13, you'd put a `.mcp.json` next to `skills/` and `agents/`, in the same format as the project's `.mcp.json`.

## 14.4 Trying the plugin without installing it

### Validate

Before loading it, have the structure checked:

```bash
claude plugin validate ./cc-lab-toolkit
```

`claude plugin validate` reads the manifest and the skill and agent frontmatter and tells you what's wrong: malformed JSON, a missing `name` field, broken frontmatter. It costs nothing and saves you from finding the problem later, when the plugin simply doesn't show up. `--strict` makes the check stricter, and `--json` prints the result in a format a script or CI job can read.

### Load it for one session

Next, go into the lab project and start Claude Code with the `--plugin-dir` flag:

```bash
cd ~/cc-advanced-lab
claude --plugin-dir ~/cc-plugins/cc-lab-toolkit
```

`--plugin-dir` loads the plugin for this session only, without installing it: no scope, no marketplace, nothing to uninstall afterward. It's the right way to work on a plugin while you write it. When you close the session, the plugin is gone.

Try the skill with its prefix:

```text
/cc-lab-toolkit:report-pdf data/vendite.csv
```

On the lab's CSV, three months of sales, the answer is the table the skill asks for: 3 rows, total 358, minimum 95, maximum 143, average 119.33. The PDF lands in `output/report-vendite.pdf`, as in chapter 9. The total is the same one `tests/test_report.py` checks, so you get a cross-check as well.

Then the agent:

```text
use the cc-lab-toolkit:python-reviewer agent on src/report.py
```

The agent carries the plugin prefix too. Claude launches it as a subagent, which runs in the background in interactive sessions: the agent reads the file and the tests in its own separate context and hands back only the report, as you saw in chapter 10. It takes a little longer than the skill, because a fresh context starts up and has to read everything again.

The hook doesn't need a dedicated prompt: ask Claude for any change to a `.py` file and look at the file afterward. If it's formatted, the plugin's hook worked. `/hooks` also shows you the hook registered under `PostToolUse`, alongside the ones from your settings files, and lists the source next to each one: for this hook, the plugin.

### Edit without restarting

If you fix the skill's description or the agent's prompt while the session is open, you don't need to quit and restart:

```text
/reload-plugins
```

reloads the plugin's files into the current session. If the agent still seems to be the old one, remember that a subagent already running keeps its own prompt: launch it again.

### The most common mistake

The problem I see most often is a plugin that loads without errors but has no skills or agents. Nearly every time, the components ended up inside `.claude-plugin/`:

```text
cc-lab-toolkit/
└── .claude-plugin/
    ├── plugin.json
    ├── skills/          <- not loaded from here
    └── agents/
```

`.claude-plugin/` holds only the manifest. Skills, agents and hooks go at the plugin root, next to `.claude-plugin/`, as in the tree in the previous section. The folder name invites the mistake, because it looks like the place for "the plugin's stuff". If `/cc-lab-toolkit:report-pdf` doesn't appear in the command menu, check this first, then run `claude plugin validate` again.

## 14.5 A marketplace for the team

With `--plugin-dir`, you're the only one using the plugin. To hand it to the team you need a **marketplace**. The name suggests a store, but it's just a repository with a `.claude-plugin/marketplace.json` file that lists the plugins and says where to find them.

Turn `~/cc-plugins` into a marketplace. Create `~/cc-plugins/.claude-plugin/marketplace.json`:

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
      "description": "CSV reports, code review and formatting for Python projects"
    }
  ]
}
```

Don't mix them up: the marketplace's `.claude-plugin/` sits at the root of `~/cc-plugins` and holds `marketplace.json`; the plugin's sits in `~/cc-plugins/cc-lab-toolkit` and holds `plugin.json`. The full repository layout becomes:

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

The marketplace's `name` is what you'll type after the at sign. `source` is the plugin's path, relative to the marketplace folder. When you have a second plugin, add another object to the `plugins` array and a folder next to `cc-lab-toolkit`.

### Add the marketplace and install

Start Claude Code normally, without `--plugin-dir`, and register the marketplace:

```text
/plugin marketplace add ~/cc-plugins
```

The command takes a local folder, as here, or a GitHub repository in `user/repository` form. You do this once. Then you install the plugin by name, at sign, marketplace name:

```text
/plugin install cc-lab-toolkit@cc-corso
```

Claude Code asks for the scope, as it did for `plugin-dev`. From now on `/cc-lab-toolkit:report-pdf` is available in every session in the scope you chose, no flag needed.

### Sharing it for real

The local folder is for trying the marketplace on yourself. For the team, you publish `cc-plugins` on GitHub like any other repository, and your colleagues add it with:

```text
/plugin marketplace add <user>/cc-plugins
/plugin install cc-lab-toolkit@cc-corso
```

If the plugin serves one specific project, install it with project scope in that repository: the choice ends up in the shared `.claude/settings.json`, and whoever clones the project gets the same plugin.

Updates go through the version in the manifest. You fix the skill, bump `version` in `plugin.json` from `1.0.0` to `1.1.0`, commit and push: whoever installed the plugin gets the new version at the next update. If you change the files and forget to change the number, nothing has changed as far as everyone else is concerned. I treat the version bump as part of the change, in the same commit.

By default, auto-update is on only for Anthropic's official marketplaces. For a marketplace like yours it's off: each colleague can turn it on from the Marketplaces tab in `/plugin` (Enable auto-update), and from then on Claude Code checks the marketplace during the session and loads the new version starting with the next session. Otherwise you update by hand, first the marketplace catalog and then the plugin:

```bash
claude plugin marketplace update cc-corso
claude plugin update cc-lab-toolkit@cc-corso
```

To clean up after your experiments, from the terminal:

```bash
claude plugin uninstall cc-lab-toolkit@cc-corso
claude plugin marketplace remove cc-corso
```

## 14.6 A plugin just for you

Not everything deserves a marketplace. If you want a plugin that's always on, just for you, in all your projects, without publishing anything, there's:

```bash
claude plugin init miei-attrezzi
```

`claude plugin init` (alias `claude plugin new`) scaffolds the plugin in `~/.claude/skills/miei-attrezzi/`, which is your personal skills folder, and loads it from there in every session as `miei-attrezzi@skills-dir`. The suffix in place of a marketplace reminds you where it comes from. It's the right home for small personal habits the team doesn't care about: the skill that reformats your meeting notes, the agent that explains a stack trace the way you like.

The rule I use to choose: if a colleague wants it too, it goes in the team marketplace; if I want it only for myself but in every project, `claude plugin init`; if it's needed in one repository only, it stays in that repository's `.claude/`, as in chapters 9-12.

For completeness: since v2.1.287 there are also Claude Mods, hook modules written in JavaScript. They're a different mechanism from plugins, and I don't cover them here.

## 14.7 Measuring the plugin with claude plugin eval

You have a plugin that works. The next question is whether it actually helps. The test you ran in section 14.4 tells you the skill starts when you call it by name. It doesn't tell you whether Claude uses it when a user asks "give me a summary of the sales" without knowing the skill exists, or whether the result beats what Claude would have produced without the plugin.

`claude plugin eval` answers that question. Each test case is a realistic prompt plus one or more **graders**, checks that say whether the result is good. A grader can be a regular expression on the response, a check that a given skill was used, or a criterion judged by a second model ("the response contains a table with the correct total and average").

### Generating the cases with eval init

You don't write the cases by hand. From the plugin folder:

```bash
cd ~/cc-plugins/cc-lab-toolkit
claude plugin eval init
```

First it asks whether you trust the plugin folder: it's yours, so say yes. Then an interview led by Claude starts. It asks what the skill should do and which requests must not trigger it. To the first question I answered:

```text
The report-pdf skill produces a short report from a sales CSV file: rows, total, minimum, maximum and average.
```

and to the second:

```text
It must not trigger on generic questions about Python code, or on files that aren't CSV.
```

The second answer is the one people tend to skip, and it's the most useful. It produces the negative cases, the ones that check the skill doesn't fire when it shouldn't. A skill with an overly broad description passes every positive case while also triggering on requests that have nothing to do with it; without negative cases you won't notice.

The interview proposes the cases and asks for confirmation at each step. For a first run keep them few: I asked for two cases, enough to see how it works. When it confirms it has written them, leave with `/exit`.

At the plugin root you'll find an `evals/` folder with one subfolder per case, named after its prompt. Inside are `prompt.md`, with the prompt and the run limits in the frontmatter, and a `graders/` folder with one Markdown file per check. A case that has to prepare some files before it starts also has a `case.yaml`. Open them. The prompt should look like a real request, not like the skill's description rewritten; if the interview produced a prompt that already contains the description's keywords, the case measures very little and you're better off rewriting it.

```bash
find evals -type f | sort
```

### Running the suite

Still from the plugin folder:

```bash
claude plugin eval .
```

Each case runs three times with the plugin and three times without. With two cases that's twelve runs, plus the calls from graders that use a model. In my test, running the cases in parallel, the suite took a couple of minutes.

For the course recording I ran the command with three extra options:

```bash
claude plugin eval . --trust-plugin --no-publish -j 4
```

`--trust-plugin` skips the folder trust prompt on the first run, and `-j 4` runs four executions in parallel (the default is one at a time), which cuts the wait. `--no-publish` is the one not to forget: if you're on a claude.ai subscription, without this option the report is also published as a private artifact on your account, and the terminal prints a `Published:` line with the address. With `--no-publish` you get only the local file.

### Reading the table

At the end the suite prints a table with one row per case and four columns:

| Column | What it tells you |
|---|---|
| `WITH` | the grader results for the runs with the plugin |
| `W/OUT` | the results for the runs without the plugin |
| `Δ` | the difference between the two: how much the plugin improved the result |
| `COST` | what the case cost |

<!-- TODO screenshot: tabella finale di claude plugin eval con le colonne WITH, W/OUT, Δ, COST -->

The column to watch is `Δ`. A high delta says the plugin makes a difference on that case. A delta close to zero has two possible explanations. The first is that Claude does fine without the plugin too: for a three-row CSV that's plausible, and it means that skill costs you context without giving much back. The second, far more common, is that the skill never fired. In that case the problem is almost always the description, which doesn't match the way the user phrases the request. It's the chapter 9 lesson about the description as a trigger, except that now you have a number telling you. Fix the description, run it again, see whether the delta goes up.

For the details of each run, including the response texts and the grader verdicts, open the `report.html` the suite writes in the results folder.

The results don't belong in the repository. Add the folder to the plugin's `.gitignore`:

```bash
echo 'evals/results/' >> .gitignore
```

The cases in `evals/`, on the other hand, you commit: they're the plugin's tests, and whoever changes it after you runs them again to make sure nothing got worse.

### Iterating without burning through your plan

Every run is a real model call and eats into your plan. A full suite with ten cases is sixty runs: launching it after every tweak to the description is a quick way to hit your weekly limits.

While you iterate, narrow it down:

```bash
claude plugin eval . --case <case-name> --runs 1 --ablation none
```

`--case` runs a single case, `--runs 1` does one run instead of three, and `--ablation none` skips the comparison runs without the plugin; the table then shows `SCORE` and `PASS%` columns in place of `WITH`, `W/OUT` and `Δ`. You're left with a single run, enough to see whether the skill fires now. When you're happy, confirm with the full suite and the standard three runs: one run isn't enough to trust a result, because the same prompt can give different answers.

::: {.callout .callout-tip}
[Tip]{.callout-title}

Keep at least one negative case per skill in the suite. When you broaden a description so the skill fires on a positive case that was failing, the negative case tells you right away whether it now also fires where it shouldn't.
:::

## Summary {.unlisted}

- A plugin is a folder with the manifest in `.claude-plugin/plugin.json` and the components (`skills/`, `agents/`, `hooks/hooks.json`, `.mcp.json`) at the root. The `name` field is required and becomes the prefix: `/cc-lab-toolkit:report-pdf`.
- Before installing a plugin, check its context cost in the `/plugin` manager and read the hooks and MCP servers it brings along: they run with your permissions.
- In a plugin's hooks the script path uses `${CLAUDE_PLUGIN_ROOT}`, not `$CLAUDE_PROJECT_DIR` or an absolute path.
- `claude plugin validate` checks the structure, `claude --plugin-dir` loads the plugin for one session, `/reload-plugins` picks up your changes. If skills and agents are missing, check that they didn't end up inside `.claude-plugin/`.
- A marketplace is a repository with `.claude-plugin/marketplace.json`: you add it with `/plugin marketplace add`, install with `/plugin install <plugin>@<marketplace>` and ship updates by changing `version` in the manifest.
- `claude plugin eval` compares results with and without the plugin: watch the `Δ` column, iterate with `--case`, `--runs 1` and `--ablation none`, and put `evals/results/` in `.gitignore`.

## Exercise {.unlisted}

Add a second skill to `cc-lab-toolkit`, `csv-check`, which checks a CSV file and reports empty rows, missing columns and non-numeric values in the sales column, without modifying the file. Bump the manifest version to `1.1.0`, verify the structure with `claude plugin validate ./cc-lab-toolkit` and try it in `cc-advanced-lab` with `--plugin-dir`. Then run `claude plugin eval init` for the new skill, asking for at least one positive case and one negative case (for example a question about the code in `src/report.py`, which must not trigger it).

The exercise is done when `/cc-lab-toolkit:csv-check data/vendite.csv` replies that the file is clean, the full `claude plugin eval .` suite shows a positive `Δ` on the positive case, and the negative case passes, meaning the skill doesn't fire.
