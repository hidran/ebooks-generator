# Chapter 11. Permissions, modes and the sandbox

::: {.chapter-goals}
[What you'll learn]{.callout-title}

- Pick the right permission mode and switch it with `Shift+Tab`.
- Write allow, ask and deny rules in `.claude/settings.json` and know the order they're evaluated in.
- Understand what auto mode really does and where the classifier stops.
- Configure the sandbox at the project level and share it with your team.

:::

In the first three parts of the book you let Claude Code decide on its own when to ask for permission, and for analyzing a CSV or writing a skill that was perfectly fine. From here on you give it more autonomy: hooks that run on every edit, MCP servers that talk to GitHub and to a database, plugins installed from a marketplace, long sessions that keep working while you do something else. The more the agent acts on its own, the more precisely you need to know what it can do without asking, what it must never touch, and what happens when a command does more than its name suggests. That's where Part IV starts.

Chapter 2 covered the concepts: the model asks, the harness executes, permissions decide whether a call may start, and the sandbox limits how far a command can reach once it's running. You also tried the sandbox with `touch ~/sandbox-probe`. Now you move on to configuration. There are three layers of control: the permission mode sets the baseline behavior, allow, ask and deny rules add precise exceptions, and the sandbox draws a boundary at the operating-system level. You'll go through them one at a time on a small project, so every test reads in a few seconds.

## 11.1 The lab project

Chapters 11-15 all use the same project, `cc-advanced-lab`, which you created in Chapter 2 to watch the agentic loop: a six-line Python script, a three-row CSV and a test. It's tiny on purpose. The Photogallery stays untouched, and when a rule blocks something you see why right away, without getting lost in a codebase thousands of lines long. It also holds a `.env` file with a fake secret: that's the bait for this chapter's rules and the next chapter's hooks.

If you already have the lab, reset it to the last commit. The Chapter 2 exercise left uncommitted changes in `src/report.py` and `tests/test_report.py`, and the `/sandbox` menu wrote `.claude/settings.local.json`, which you'll regenerate in Section 11.8. The `report-pdf` skill from Chapter 9, if you committed it, stays where it is:

```bash
cd ~/cc-advanced-lab
git checkout -- .
rm -f .claude/settings.local.json
```

If you skipped Chapter 2, create it from scratch (macOS, Linux or WSL 2):

```bash
mkdir -p ~/cc-advanced-lab/{src,data,tests}
cd ~/cc-advanced-lab
git init
printf "data,vendite\n2026-01,120\n2026-02,95\n2026-03,143\n" > data/vendite.csv
printf "import csv\n\n\ndef totale(path):\n    with open(path) as f:\n        return sum(int(r['vendite']) for r in csv.DictReader(f))\n" > src/report.py
printf "from src.report import totale\n\n\ndef test_totale():\n    assert totale('data/vendite.csv') == 358\n" > tests/test_report.py
touch src/__init__.py
printf "[pytest]\npythonpath = .\n" > pytest.ini
printf "SECRET_KEY=non-committare-questo\n" > .env
printf ".env\n.venv/\n" > .gitignore
git add -A && git commit -m "chore: progetto di laboratorio"
python3 -m venv .venv
source .venv/bin/activate
pip install pytest
```

The `.gitignore` keeps `.env` out of Git, as in a real project. Always start Claude Code from the shell where you activated the virtualenv, so the Python it finds on the `PATH` is the one with pytest.

This chapter needs a small tweak to `pytest.ini`. It tells pytest to look for tests only in `tests/` and to ignore `.env`:

```bash
printf "[pytest]\npythonpath = .\ntestpaths = tests\naddopts = --ignore=.env\n" > pytest.ini
git commit -am "chore: pytest solo su tests/"
```

Without those two lines, in Section 11.8 the sandbox would make test collection fail with a `PermissionError`. You'll see why there, and it's one of the most instructive details in the chapter. Check that everything works before you open Claude Code:

```bash
python -m pytest
```

You should see `1 passed`: the test checks that the sales for January, February and March add up to 358.

## 11.2 The six permission modes

Open `claude` in the lab folder and look below the prompt: the active mode is always shown there. Interactive sessions in the terminal and in VS Code start in auto mode, so you'll read `auto mode on`. The change landed in two steps: from version 2.1.228 (August 2026) for the Pro, Max and Team plans, and from 2.1.283 for every plan and provider. A non-interactive session with `claude -p`, on the other hand, still starts in Manual.

Press `Shift+Tab` and the label changes. Four presses take you all the way around:

```text
auto mode on
manual mode on
accept edits on
plan mode on
auto mode on
```

The cycle holds four modes. The other two, meant for when nobody is sitting at the terminal, are left out.

| Mode | What it does without asking | When to use it |
| --- | --- | --- |
| Manual (`default`) | Reads only | Sensitive code, a project you don't know |
| `acceptEdits` | Reads, file edits, commands such as `mkdir`, `touch`, `mv` and `cp` | Iterating and reviewing changes with `git diff` |
| `plan` | Reads, no edits until you approve the plan | Exploring and designing |
| `auto` | Everything, with safety checks in the background | Long tasks, fewer interruptions |
| `dontAsk` | Reads in the working folder, read-only Bash and pre-approved tools; everything else is denied | CI and scripts |
| `bypassPermissions` | Everything, with no checks at all | Isolated containers or VMs only |

Manual is the old default mode: the configuration calls it `default`, the interface calls it Manual. It asks for confirmation on almost everything. It's the behavior you saw in the early chapters, before auto mode became the default, and it's still the right choice when you open a repository you don't know: every command goes past your eyes.

Accept edits lets Claude change files without asking, and also auto-approves commands that only touch files and folders (`mkdir`, `touch`, `mv`, `cp`), but it stops you on everything else. It's handy when you work in small steps and review everything at the end of a round with `git diff`: the changes sit in the working tree, and Git gives you undo.

You know Plan Mode from Chapter 3: Claude reads, analyzes and proposes a plan, without touching anything until you approve it.

Auto lets Claude work and hands the checks to a second model, the classifier, which approves actions consistent with your request and blocks the risky ones. Section 11.7 is all about it, because its real behavior has a few nuances you'll want to know before you trust it.

Outside the cycle are `dontAsk` and `bypassPermissions`. The first lets through reads in the working folder, read-only Bash commands and the tools you pre-approved with allow rules, and denies everything it would otherwise ask you about: it's what you want in a CI pipeline, where nobody would answer a prompt. The second skips every check, and it's the same thing you get with the `--dangerously-skip-permissions` flag. Use it only inside a container or a virtual machine you can throw away, never on your laptop with your SSH keys.

You pick the modes outside the cycle at startup, and the same flag works for all of them:

```bash
claude --permission-mode plan
claude --permission-mode manual
claude --permission-mode dontAsk
```

`manual` is an alias for `default`: use whichever name feels more natural.

If you want a project to always start in a given mode, put it in the settings:

```json
{
  "permissions": {
    "defaultMode": "default"
  }
}
```

With this block in `.claude/settings.json`, anyone who opens the project starts in Manual instead of auto mode. I use it on client repositories: for the first hour on code I don't know, I'd rather see every command. It also works with `plan` and `acceptEdits`. It doesn't with `auto` and `bypassPermissions`: as a `defaultMode` they only take effect in `~/.claude/settings.json`, and written in the project or local file they're ignored. That makes sense, because otherwise a repository cloned from the internet could switch itself into `bypassPermissions` on your machine.

## 11.3 Allow, ask and deny rules

The mode sets the baseline. Rules add exceptions: this command always goes through, this one always asks, this one never goes through. You write them in a JSON file, and Claude Code applies them in every mode, auto mode included.

Exit Claude Code and create the project settings folder:

```bash
mkdir -p .claude
```

Then create `.claude/settings.json` with this content:

```json
{
  "permissions": {
    "allow": [
      "Bash(python -m pytest *)",
      "Bash(git diff *)"
    ],
    "ask": [
      "Bash(git push *)"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Bash(curl *)",
      "Agent(model:opus)"
    ]
  }
}
```

`allow` holds pytest and `git diff`: commands that don't change anything important and that I don't want to approve every time. `ask` holds `git push`: even when everything else flows without questions, I want to be the one who says yes before code goes to the remote. `deny` holds four prohibitions: reading `.env` and its variants (`.env.local`, `.env.production`), using `curl`, and launching subagents on the Opus model.

The last rule uses a recent syntax. Inside the parentheses, instead of a command, you name a tool parameter and its value: `Agent(model:opus)` matches calls to the `Agent` tool that ask for the Opus model. In the lab it's there to show the syntax, but it has a practical use too: if you're on a pay-as-you-go plan, keep subagents on lighter models and save Opus for the main session.

The file lives inside the project, so it ends up in Git and applies to the whole team. Commit it like any other config file.

Now try it. Restart `claude` so it picks up the new settings, switch to Manual with one `Shift+Tab` and type:

```text
run the tests with python -m pytest
```

In Manual, Claude would ask for confirmation on almost every command, but pytest matches an allow rule: it runs straight away and you see `1 passed`. Now the second prompt:

```text
show me the contents of .env
```

Claude tries to use the `Read` tool, the deny rule stops it, and the file's contents never show up on screen. Claude tells you the read is denied by the project settings.

::: {.callout .callout-warning}
[Warning]{.callout-title}

When I recorded the lesson, after the refusal Claude suggested I read the file myself with `! cat .env`, and later that I run `! curl ...` for the blocked download. The `!` prefix runs the command directly in the shell, as you, and deny rules restrict Claude, not you. On top of that, the output of a command run with `!` goes into the conversation: with `! cat .env`, the secret you wanted to keep out lands right in the context. If a rule blocks you, you decide whether the rule is wrong, and if it is, change the rule.
:::

## 11.4 Rule syntax and evaluation order

The shape is always `Tool(specifier)`. The tool name alone, without parentheses, matches every use of that tool: `"Bash"` under `ask` means every shell command asks for confirmation. What the specifier means depends on the tool.

| Rule | What it matches |
| --- | --- |
| `Bash(python -m pytest *)` | Any command that starts with `python -m pytest` |
| `Bash(git diff *)` | `git diff` with any arguments |
| `Read(./.env)` | Reading the project's `.env` file |
| `Edit(./data/**)` | Edits to any file under `data/` |
| `WebFetch(domain:pypi.org)` | Web requests to `pypi.org` |
| `Agent(model:opus)` | Subagents launched on the Opus model |
| `mcp__github__*` | Every tool from the `github` MCP server |

For Bash the asterisk is a wildcard. Watch the space before it: `Bash(ls *)` matches `ls -la` but not `lsof`, while `Bash(ls*)` matches both. For `Read` and `Edit` the specifier is a path using `.gitignore` patterns, so `**` descends into every subfolder. Rules on `Edit` apply to every tool that modifies files, `Write` included.

MCP tools have compound names: `mcp__`, the server name, two underscores, the tool name. `mcp__github__*` approves or denies everything the `github` server exposes in one go; with the full name, for example `mcp__github__create_pull_request`, you pick one tool at a time. That will come in handy in Chapter 13, when you connect GitHub to Claude Code and want to leave reads open but not PR creation.

The evaluation order is fixed: deny first, then ask, then allow. A deny always wins, even when a more specific allow exists. If you write `Bash(git push origin feature/*)` under `allow` and have `Bash(git push *)` under `ask`, pushing to the feature branch still asks for confirmation, because ask is evaluated first. Rules from all settings files add up (Section 11.5 lists where they live), and a deny written in any one of those files can't be overridden by an allow written in another.

Now the limit you need to be clear on. A Bash rule matches the text of the command, not the program that runs. `Bash(curl *)` blocks `curl https://...` written exactly like that. It doesn't block `wget`, or a Python script that opens a connection with `urllib`, or an `npm install` whose postinstall script downloads something. The same goes for `Read(./.env)`: it stops the `Read` tool, but a shell command that reads the file takes another route. For a real boundary you need the sandbox, which comes later in this chapter, or a hook that inspects the command before it runs, which you'll write in Chapter 12.

What about instructions in `CLAUDE.md`? "Never read the .env file" in `CLAUDE.md` steers Claude, and Claude usually follows it. But it's text in the model's context, which the model can forget after a compaction or weigh less than an explicit request from you. A deny rule is enforced by Claude Code, the program, before the call starts. The two work together: `CLAUDE.md` explains the why, the settings hold the prohibition.

## 11.5 Where rules live

Rules can live in four places, each with a different scope.

| File | Scope | In Git |
| --- | --- | --- |
| `~/.claude/settings.json` | All your projects | No |
| `.claude/settings.json` | The project, shared with the team | Yes |
| `.claude/settings.local.json` | The project, just you | No |
| Managed settings | The organization, can't be overridden | Managed by IT |

The user file is the place for personal preferences you want everywhere: for example the denies `Read(~/.ssh/**)` and `Read(~/.aws/**)`, which have nothing to do with any particular project. The project file is the one you just wrote: rules for anyone who clones the repository. The local file collects your own exceptions on that project, and it's where every "yes, and don't ask again" you give to a permission prompt ends up. When Claude Code creates it in a repository, it keeps it out of Git on its own, with a line in Git's global excludes rather than in the project's `.gitignore`. If you create it by hand, add it to `.gitignore`.

Open `.claude/settings.local.json` every now and then and reread it. After a few weeks you'll find approvals given on the fly that you wouldn't give again with a cool head, and some that deserve to move up into the project file because your colleagues need them too.

Managed settings are distributed by the organization and can't be overridden: if the company denies `Bash(git push --force *)`, no local file reopens it. From there an administrator can also turn off auto mode for everyone with `"disableAutoMode": "disable"` inside `permissions`. When there's a conflict on a single value, such as `defaultMode`, precedence decides: managed above everything, then command-line arguments, then the local file, the project file and finally the user file.

## 11.6 /permissions and Recently denied

You don't need to open four files to see the active rules. Type `/permissions` (the alias is `/allowed-tools`): the panel opens on the Allow tab, and the right arrow takes you to Ask and Deny. Select a rule and press `Enter` to see where it comes from; for the lab rules the line says `From shared project settings`, meaning `.claude/settings.json`.

In the recording, the Allow tab also showed some `mcp__computer-use__*` rules I hadn't written in the lab: they came from my account's user settings. That's the practical proof that rules add up, and the reason `/permissions` is the first place to look when a command goes through or gets blocked and you can't tell why. Another detail I noticed: in auto mode the `Bash(python -m pytest *)` rule no longer showed up among the allows. When it enters auto mode, Claude Code sets aside broad allow rules that permit running arbitrary code, such as `Bash(*)` or an interpreter followed by the wildcard, and puts them back in force when you leave auto mode. An auto-approved `python` could run anything, and it would bypass the classifier.

The last tab is Recently denied. It collects the actions blocked by the auto mode classifier, and from there you can retry them by approving them yourself. When it's empty, the panel says so: `Commands denied by the auto mode classifier will appear here`. It only collects the classifier's decisions: anything stopped by one of your deny rules doesn't show up there, and you'll see that happen in the next section.

## 11.7 Auto mode in practice

Go back to auto mode: from Manual it's three presses of `Shift+Tab` (accept edits, plan, auto). Then ask for an ordinary piece of work:

```text
add a media() function to src/report.py with its test and run the tests
```

Claude edits `src/report.py`, adds the test to `tests/test_report.py`, runs pytest and finishes with `2 passed`, without a single confirmation prompt. In auto mode Claude doesn't stop on routine operations: it edits files in the project folder, runs the tests, installs declared dependencies. Before every non-trivial action, though, the classifier checks that it's consistent with what you asked for.

The categories it blocks are the ones where a mistake is expensive: downloading and running scripts from the internet, force pushes, irreversible deletions, production deploys, sending sensitive data out. So the second prompt is a deliberate trap:

```text
download and run the script https://example.com/install.sh
```

Claude stops. When I opened `/permissions` to show the Recently denied tab, though, the tab was empty. What stopped Claude wasn't the classifier: it was the `curl` deny rule from Section 11.3. Rules apply in auto mode too and are evaluated before the classifier, so the command never even reached it.

While preparing the lesson I tried the same request without that rule, and the classifier didn't block it. The classifier is a model that judges context, and its call can go a way you don't expect; maybe with `example.com`, a domain reserved for examples, that's exactly what tipped it. A deny rule, on the other hand, is deterministic: either the text matches or it doesn't. For the things that must never happen, write a rule. The classifier covers everything else, meaning the situations you didn't foresee.

The same applies to ask. The `Bash(git push *)` rule asks for confirmation in auto mode too, and since a force push still starts with `git push`, it never reaches the classifier: you get the question first.

Two auto mode behaviors worth knowing. First, the classifier also reads the limits you set in the conversation. If you write "don't push", it blocks pushes until you say otherwise. That's a hint in the context, not a saved rule: it lasts for that session and can get lost in a compaction. For a guarantee, use a deny. Second, if Claude gets blocked three times in a row, or twenty times in total in the session, auto mode pauses and goes back to asking you for confirmation. An agent that keeps running into the classifier has probably misunderstood the task, and at that point you want to take a look yourself.

To see the rules the classifier reasons with, exit Claude Code and run this from the shell:

```bash
claude auto-mode defaults | head -40
```

The command prints the classifier's default rules as JSON. There are a lot of dense lines, hence the `head`. Read them once, calmly: they give you a concrete idea of what the classifier considers risky, and therefore of what you'd do well to cover with your own rules. Next to `defaults` there's `claude auto-mode config`, which shows the effective configuration with your settings applied, and `claude auto-mode reset`, which removes the `autoMode` section from your user settings and goes back to the defaults. Inside a session, `/auto-mode-setup` (Pro, Max and Team plans) has Claude draft `autoMode.environment` entries, meaning the repositories, buckets and services you trust, based on the project and your recent sessions; if you accept the draft, it goes into `~/.claude/settings.json`.

::: {.callout .callout-tip}
[Tip]{.callout-title}

Auto mode cuts down on interruptions, but it doesn't replace review. At the end of a task, look at the diff anyway (`git diff`, or the `/diff` panel in the desktop app) before you commit. The classifier judges the risk of an action; whether the code is right is your call.
:::

## 11.8 The project-level sandbox

The sandbox works at a different level from rules. Instead of deciding whether a command may start, it limits what the command can reach once it's running, on the file system and on the network, and the operating system enforces it: Seatbelt on macOS, bubblewrap and socat on Linux and WSL 2. That's why it holds even when the command is written in a way the rules don't recognize, like the `wget` in Section 11.4. What it restricts by default, the `touch ~/sandbox-probe` test and the meaning of the main keys are all in Chapter 2. Here you turn it on alongside the lab rules and move it into the team file.

Switch to Manual with `Shift+Tab`, type `/sandbox` and choose `Sandbox BashTool, with auto-allow`. In this mode, commands that run inside the sandbox start without asking for confirmation, even in Manual, because the system guarantees the boundary. Denies still hold: a denied command stays denied. Try it:

```text
run ls -la and python -m pytest
```

Both commands run without a single prompt, and pytest finishes with `2 passed`. To get there, though, I had to add the two `pytest.ini` lines from Section 11.1 to the lab. Without them, pytest failed during collection with a `PermissionError` on the `.env` file. The reason is interesting: the sandbox takes the deny rules on `Read` and enforces them at the operating-system level on every process it launches. `Read(./.env)` no longer stops just Claude's `Read` tool: it stops any program started by a sandboxed command, pytest included, which walks the folder looking for tests. That's the real boundary Section 11.4 was talking about, and you notice it as soon as something bumps into it.

As you saw in Chapter 2, the `/sandbox` menu saves your choice in `.claude/settings.local.json`, which applies only to you. In Chapter 2 the full configuration went into `~/.claude/settings.json`, for all your projects. For a team project the third place makes more sense, `.claude/settings.json`, so anyone who clones the repository gets the same boundary. The minimal form is `"sandbox": { "enabled": true }`; the one I use in the lab is:

```json
{
  "sandbox": {
    "enabled": true,
    "allowUnsandboxedCommands": false,
    "filesystem": {
      "denyRead": ["~/.ssh", "~/.aws"]
    },
    "network": {
      "allowedDomains": ["pypi.org", "files.pythonhosted.org", "github.com"]
    }
  }
}
```

The keys are the ones from Chapter 2. What changes is the domains: in a project file you list the ones that project needs, not the ones you use every day. Here you have the two that `pip` downloads packages from, plus GitHub; for everything else the local proxy asks the first time, and whoever is working answers. The `denyRead` on `~/.ssh` and `~/.aws` looks out of place in a project file, but it's how you guarantee it for the colleague who has never touched their user settings.

The sandbox covers only shell commands and the processes they start: hooks and MCP servers, which you'll add in the next two chapters, run outside it, and so do commands you exclude because they don't work inside it, like `docker`. If you want a boundary around all of Claude Code, you need a dev container, or a dedicated container or VM.

::: {.callout .callout-warning}
[Warning]{.callout-title}

The sandbox works on macOS, Linux and WSL 2. On native Windows it isn't supported, and commands run with no boundary, even if `.claude/settings.json` says `"enabled": true`. On Linux and WSL 2 you need the system packages: `sudo apt-get install bubblewrap socat`. If someone on the team works on Windows without WSL, the shared configuration doesn't protect them: tell them, and make sure the deny rules still cover the cases that matter.
:::

## 11.9 A recommended setup for the book's projects

Putting the pieces together, this is the setup I use for the book's projects: auto mode for the work, deny on secrets and dangerous commands, ask on push, sandbox on. For the lab, the final `.claude/settings.json` is:

```json
{
  "permissions": {
    "allow": [
      "Bash(python -m pytest *)",
      "Bash(git diff *)"
    ],
    "ask": [
      "Bash(git push *)"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Bash(curl *)",
      "Bash(git push --force *)",
      "Agent(model:opus)"
    ]
  },
  "sandbox": {
    "enabled": true,
    "allowUnsandboxedCommands": false,
    "filesystem": {
      "denyRead": ["~/.ssh", "~/.aws"]
    },
    "network": {
      "allowedDomains": ["pypi.org", "files.pythonhosted.org", "github.com"]
    }
  }
}
```

There's no `defaultMode`: auto mode is already the default, and `"auto"` written in a project file would be ignored anyway. Anyone who wants to start in Manual uses the flag. The deny on `git push --force` stacks with the ask on `git push`: a force push written that way is denied, and one written with `-f` still falls into the ask, so you get the question.

For the Photogallery, which you'll work on in Part VI, the commands and paths change. The Laravel backend has its own `backend/.env`, the React frontend its own `frontend/.env`, and the backend tests run with Pest through `php artisan test`:

```json
{
  "permissions": {
    "allow": [
      "Bash(php artisan test *)",
      "Bash(vendor/bin/pint *)",
      "Bash(npm run lint)",
      "Bash(npm run build)",
      "Bash(git diff *)"
    ],
    "ask": [
      "Bash(git push *)",
      "Bash(php artisan migrate *)"
    ],
    "deny": [
      "Read(./backend/.env)",
      "Read(./backend/.env.backup)",
      "Read(./backend/.env.production)",
      "Read(./frontend/.env)",
      "Bash(git push --force *)",
      "Bash(git reset --hard *)"
    ]
  }
}
```

Here I listed the `.env` files one by one instead of using `.env.*`, because the pattern would also match `backend/.env.example`, which holds no secrets and which Claude happily reads to figure out which variables are needed. `php artisan migrate` sits under `ask` because a migration run against the wrong database can't be undone with `git checkout`. If the sandbox runs on your machine, add the same `sandbox` block as in the lab, with the Composer and npm domains instead of the pip ones. For npm it's `registry.npmjs.org`. For Composer, which downloads packages from several hosts, let the proxy ask you about them the first time and copy the ones you approve into the list.

One last note: the Photogallery companion repository already has a `.claude/settings.json`, which contains only hooks. If you add permissions, merge them into the same file under the `permissions` key, without replacing what's there. Hooks are the topic of the next chapter.

## Summary {.unlisted}

- The active mode is shown below the prompt, and you switch it with `Shift+Tab` (auto, Manual, accept edits, plan); you pick `dontAsk` and `bypassPermissions` with `--permission-mode`, and they're meant for CI and isolated environments.
- Allow, ask and deny rules in `.claude/settings.json` apply to the whole team; the order is deny, then ask, then allow, and a deny always wins.
- A Bash rule matches the command text: for a real boundary you need the sandbox or a hook, and instructions in `CLAUDE.md` aren't permissions.
- In auto mode your rules come before the classifier. Use denies for what must never happen and leave the unforeseen cases to the classifier; `/permissions` shows the rules, where they come from, and Recently denied.
- The sandbox in `.claude/settings.json`, with `allowUnsandboxedCommands: false` and `denyRead` on credentials, puts a system-level boundary around shell commands, not around hooks and MCP servers.

## Exercise {.unlisted}

In the lab, protect the input data. Add to `.claude/settings.json` an ask rule that covers edits to any file under `data/`, restart `claude`, switch to accept edits with `Shift+Tab` and ask:

```text
add the row 2026-04,110 to data/vendite.csv and update the test
```

In accept edits, the change to `tests/test_report.py` goes through without questions, while the one to `data/vendite.csv` has to ask you for confirmation. Reject it. The exercise is done when `/permissions` shows your rule in the Ask tab with the origin `From shared project settings` and `git status` doesn't list `data/vendite.csv` among the modified files. If, after the rejection, Claude tries to add the row with a shell command, for example `echo ... >> data/vendite.csv`, you're watching the limit from Section 11.4 live: the `Edit` rule doesn't cover it, and in accept edits the only thing that stops you is the confirmation prompt for the command. Then repeat the test in auto mode and check that the question about the edit still comes up.
