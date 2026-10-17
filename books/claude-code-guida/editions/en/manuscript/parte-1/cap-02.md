# Chapter 2. From model to agent: tools, the agentic loop, permissions and the sandbox

::: {.chapter-goals}
[What you'll learn]{.callout-title}

This chapter takes Claude Code apart to show what happens between the prompt you type and the file that changes on disk. By the end you'll know:

- what a tool is and who actually runs it, the model or the harness;
- how the agentic loop works, tried out on a test project you set up in five minutes;
- what permission modes decide and what the sandbox restricts;
- how to pick a model and an effort level with `/model` and `/effort`.

[Prerequisites]{.callout-title}

Claude Code installed (chapter 1), Python 3 and Git. The sandbox test needs macOS, Linux or WSL 2.

:::

In chapter 1 you watched Claude Code create a file and run it. From chapter 3 on you'll write more and more ambitious prompts, so it pays to know first how the machine that receives them works. What you take away here is a mental model rather than a project. Plan Mode, CLAUDE.md, skills, agents, hooks and MCP servers each have a specific place in the mechanism I describe in these pages, and when you meet them in later chapters you'll already know where they fit.

## 2.1 What a model can do on its own

An LLM is a model that, given some text, predicts the text that comes next, one token at a time. On its own it does exactly one thing: text goes in, text comes out. It can't open a file in your project, it can't run a test, it doesn't know what time it is. What it knows about the world is what it saw in training, up to a cutoff date, plus whatever you put in the prompt.

When you use a chat and paste in some code, you do all the work around it. You pick what to paste, copy the answer into your editor, try it, and go back to the chat with the stack trace. The model does the reasoning, but the hands are yours, and the quality of the answer depends on how well you chose what to show it.

An agent is an LLM that we give hands to. We hand it a set of tools, run it in a loop, and let it decide which tools to use, in what order, and when it's done.

![An LLM in a chat returns text that you copy, run and check yourself; an agent like Claude Code alternates tool calls and results until the job is done](figures-en/cap-02/fig-01.png)

## 2.2 What a tool is

A tool is a function we describe to the model with three pieces of information: a name, a natural-language description and a schema of the parameters it accepts. Here's the definition of a tool that reads a file, in the format the Anthropic API uses:

```json
{
  "name": "read_file",
  "description": "Legge un file del progetto e ne restituisce il contenuto.",
  "input_schema": {
    "type": "object",
    "properties": {
      "path": { "type": "string", "description": "Percorso del file" }
    },
    "required": ["path"]
  }
}
```

The model receives these definitions along with your request. The description matters as much as the code: it's the only thing the model has to go on when working out when the tool is useful and how to call it.

The detail to burn into memory is that the model never runs anything. When it decides it needs to read a file, it produces a structured message that says, in effect, "I want to use `read_file` with this path":

```json
{
  "type": "tool_use",
  "id": "toolu_01",
  "name": "read_file",
  "input": { "path": "src/report.py" }
}
```

Then it stops and waits. The program hosting it reads the request, actually opens the file and sends the result back, tied to the request through the `id`:

```json
{
  "type": "tool_result",
  "tool_use_id": "toolu_01",
  "content": "import csv\n\n\ndef totale(path): ..."
}
```

At that point the model picks up its reasoning with the file contents in front of it. It can ask for another call or give its final answer. Every call goes through the same steps.

![A tool call, step by step: the model asks, Claude Code checks permissions and hooks, the tool runs, the result goes back to the model](figures-en/cap-02/fig-02.png)

::: {.callout .callout-deep-dive}
[Under the hood]{.callout-title}

`read_file` is a simplified example. Claude Code's real tool is called `Read` and takes `file_path` plus optional parameters for reading only part of a file. The definitions of every available tool travel with each request to the model and take up room in the context window: you can see it in `/context`, under the entry for tools. That's why MCP servers, which can add dozens of tools, load only the names at startup and the rest when needed. We'll come back to this in chapters 13 and 15.
:::

## 2.3 The harness, meaning Claude Code

The program around the model is called the **harness**. Claude Code is a harness: it manages the conversation, exposes the tools, runs the calls, asks for permissions and enforces the safety rules. The model lives somewhere else (on Anthropic's servers, or your cloud provider's) and only ever sees text: your prompt, the tool definitions, and the results Claude Code sends back.

Almost everything you'll configure in this book lives in the harness, not in the model. Each feature hooks into a specific point of the round trip you just saw:

| Feature | Where it acts | Chapter |
| --- | --- | --- |
| Plan Mode | Restricts the model to reading and proposing, with no changes, until you approve the plan | 3 and 4 |
| CLAUDE.md, auto memory | Text loaded into the context at the start of the session | 7 and 15 |
| Custom commands, skills | Instructions added to the context when needed | 8 and 9 |
| Agents, subagents | The `Agent` tool opens a second loop with a context of its own | 10 |
| Permissions | Decide whether a call can go ahead | 11 |
| Hooks | Scripts the harness runs before or after a call, which can block it | 12 |
| MCP | Adds tools that talk to external services | 13 |
| Plugins | Bundle skills, agents, hooks and MCP servers so you can install them in one go | 14 |
| `/context`, `/compact`, `/rewind` | Manage what the model sees on each turn | 15 |

When a chapter tells you "this is a hook that runs on `PreToolUse`", you can go back to the previous figure: it's step 2, the check Claude Code does before running the tool.

## 2.4 The agentic loop

An agent doesn't make a single call, it works in a loop. First it gathers context: it reads files, searches the code, maybe looks up the documentation. Then it acts: it edits a file, runs a command. Then it verifies: it runs the tests, reads the output. If something's off, the result of the check becomes new context and the loop starts again. It stops when it considers the job done, or when it needs you.

![Claude Code's agentic loop: gather context, act, verify; if the job isn't done, the results become new context](figures-en/cap-02/fig-03.png)

Nobody tells the model which tools to use or in what order. It decides, turn after turn, based on what it has read. That's convenient, because you don't have to write a procedure, but it also means the agent makes dozens of small decisions on its own: which file to open, which test to add, when to call the job finished. The way to keep it on track is to give it two things: a clear request and a check it can run by itself, like "the tests pass" or "the build exits with code 0". In Part VI this idea grows into a whole method, Spec Driven Development (chapter 18), and in chapter 20 you'll find it again in `/goal`, which keeps Claude going until a verifiable condition is met.

## 2.5 The loop live on a tiny project

To watch the loop you need a project small enough to read in a minute. This is the same lab I use in the video course, `cc-advanced-lab`: a Python script that adds up the sales in a CSV, plus a test. You'll reuse it in the end-of-chapter exercise and when we get to permissions, hooks and MCP.

The commands work in bash and zsh on macOS, Linux and WSL. On native Windows, run them from Git Bash, or work in WSL 2, which you'll need for the sandbox anyway.

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
```

You don't need the `.env` file with its fake secret yet: we'll use it in chapter 11 to test the rules that stop Claude from reading it. The `pytest.ini` makes `from src.report import totale` work with both `pytest` and `python -m pytest`: without it, a bare `pytest` stops with `ModuleNotFoundError: No module named 'src'`.

You still need pytest. Recent Python installs on macOS (Homebrew) and Ubuntu refuse `pip install` outside a virtual environment, so create one in the project and start Claude Code from the same shell, so that the Python it finds on the `PATH` is the right one:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pytest
pytest -q
claude
```

`pytest -q` should print `1 passed`. If Claude Code asks whether you trust the folder, say yes. Now type the prompt:

```text
find the function that computes the total, add a test and check that it passes
```

You didn't name the file or the test tool. Claude has to find `totale` in `src/report.py`, figure out what it does, add a test to `tests/test_report.py` next to `test_totale`, run pytest and read the result. When it's done, press `Ctrl+O`: that opens the detailed view of the conversation, with every single tool call and its result. Press `Ctrl+O` again to close it.

In a typical run you'll see a `Bash` call that searches the files for the function, a `Read` to read it, an `Edit` to write the test and another `Bash` to run pytest. On macOS, Linux and WSL, Claude Code no longer offers separate search tools and searches through the shell instead; on other installs you may find `Grep` and `Glob` in their place. When I recorded this scene for the course, the view showed only `Bash` calls, "ran 4 shell commands": Claude had searched, read and even written the file with shell commands. The first attempt actually failed with `No module named pytest`, because the Python on that shell's `PATH` didn't have pytest installed. That's why I have you create the virtualenv before starting Claude. The exact sequence of calls changes from one run to the next. What stays the same is the structure: context, action, verification.

Before moving on, look at the diff with `git diff`. You should see only the new test. If you want to start over, `git checkout -- .` puts the project back to the state of the initial commit.

## 2.6 Claude Code's main tools

You don't need to memorize them, but it helps to recognize them when they go by in the `Ctrl+O` view and when you write them into the permission rules in chapter 11. The list depends on your system and your model: this is what you get on macOS, Linux and WSL with the current models.

| Tool | What it's for | Loop phase |
| --- | --- | --- |
| `Read` | Read a file, or just part of it | Gather context |
| `WebSearch`, `WebFetch` | Search and read web pages | Gather context |
| `Edit`, `Write` | Edit and create files | Act |
| `Bash` (`PowerShell` on Windows) | Search files, run commands: tests, builds, Git | All |
| `Agent` | Hand a subtask to a subagent with its own context | All |
| MCP tools | Any connected external service: GitHub, databases | All |

On some installs you'll also find `Grep` and `Glob`, dedicated tools for searching text and finding files by name: they do the same job that elsewhere goes through `Bash`. With older models the task list tools show up too (`TaskCreate`, `TodoWrite`), which Claude uses to plan its steps and tick them off. The current models aren't offered them (the environment variable `CLAUDE_CODE_ENABLE_TODO_TOOLS=1` turns them back on), while `Ctrl+T` shows or hides the task checklist in the interface. Subagents launched with `Agent` run in the background by default: more on that in chapter 10. MCP tools show up with a name made of a prefix, the server and the tool, for example `mcp__github__create_pull_request`. You'll see them in chapter 13.

## 2.7 LLM and agent side by side

Let's put the two next to each other.

| | LLM in a chat | Agent like Claude Code |
| --- | --- | --- |
| Input | The text you give it | Your request plus everything it reads on its own |
| Output | Text | Actions on your project, plus a report |
| Context | Only what you paste | Files, commands, the web, connected services |
| Who runs things | You, with copy and paste | The harness, by calling tools |
| Verification | You do it | The agent does it: tests, builds, output |
| Duration | One answer | A loop of many steps |
| Risk | A wrong answer | A wrong action on your computer |

The last row is the one that matters most. With an LLM in a chat, the worst that can happen is a wrong answer, which you can ignore. With an agent, the worst case is a wrong action: a deleted file, a `git push --force` to the wrong branch, data sent somewhere it shouldn't go. The more autonomy you hand over, the more control you need. Claude Code handles this on two levels, and the first is permission modes.

## 2.8 Permission modes

A permission mode is the setting that decides which actions Claude can take without asking you first. The active one is always shown in the status bar below the prompt.

Interactive sessions in the terminal and in VS Code start in **auto mode**: for Pro, Max and Team plans since version 2.1.228 (August 2026), and for every plan and provider since 2.1.283. In auto mode a second model, the classifier, reviews actions on your behalf: it lets through the ones consistent with your request and blocks the risky ones, such as downloading and running scripts from the internet, force pushing, irreversibly deleting existing files, deploying to production or sending sensitive data outside. The first time a session starts in auto mode, Claude Code shows a notice. The exception is non-interactive mode, `claude -p`, which still starts in Manual. If you read the first edition of this book, or watched videos recorded before this version, this is why Claude asks for confirmation much less often than you expect: your setup is fine, the default changed.

During a session, `Shift+Tab` cycles through the modes in this order:

| Mode | Name in settings | Status bar | What it does |
| --- | --- | --- | --- |
| Auto | `auto` | `auto mode on` | The classifier approves or blocks on your behalf |
| Manual | `default` (alias `manual`) | `manual mode on` | Asks for confirmation for almost everything |
| Accept edits | `acceptEdits` | `accept edits on` | Edits files without asking, asks for everything else |
| Plan | `plan` | `plan mode on` | Analyzes and proposes a plan, without changing anything |

One more `Shift+Tab` after Plan takes you back to auto. You'll use Plan Mode from chapter 3 on, and in chapter 4 it becomes the standard way to start an analysis.

Two more modes sit outside the cycle. `dontAsk` lets through reads in the working directory, read-only Bash commands and the tools you've pre-approved with a rule, and silently denies everything it would otherwise ask you about: it's meant for scripts and CI. `bypassPermissions`, the same thing as the old `--dangerously-skip-permissions` flag, removes every check and should only be used inside a container or an isolated virtual machine.

You can pick the mode at startup with a flag:

```bash
claude --permission-mode manual
claude --permission-mode plan
```

`manual` is an alias for `default`, the technical name of Manual mode.

If you'd rather always start in Manual, for example while you work through the first chapters and want to see every step as in the screenshots, add this to `~/.claude/settings.json`:

```json
{
  "permissions": {
    "defaultMode": "default"
  }
}
```

Auto mode cuts down on prompts, but it's no safety guarantee. A few details worth knowing right away. Blocked actions end up in `/permissions`, on the Recently denied tab, where you can retry them. Limits you state in the chat, like "don't push", are taken into account by the classifier as guidance, not as saved rules. After three blocks in a row, or twenty in a whole session, auto mode pauses and goes back to asking you. If you want to read the rules the classifier follows, `claude auto-mode defaults` prints them. Allow, ask and deny rules, settings files and their precedence are the subject of chapter 11.

## 2.9 Permissions and the sandbox, two levels of control

Claude Code protects you on two different levels, and it's worth keeping them apart.

The first level is permissions. Before a call goes ahead, Claude Code decides whether it can: based on your rules, the permission mode you picked, the classifier if you're in auto mode, or by asking you. This applies to every tool, from `Read` to `Bash` to MCP tools. Permissions answer the question "can this action run?".

The second level is the **sandbox**. Once a shell command has started, the sandbox limits what it can reach, along with every process it launches: which folders it can write to, which files it can read, which sites it can contact. The operating system enforces this, not the model. The sandbox answers a different question: "even if this command does more than it seems to, how far can it get?".

![Two levels of control: permissions decide whether a call can go ahead and apply to every tool; the sandbox limits files and network for Bash commands only](figures-en/cap-02/fig-04.png)

You need both because a permission rule looks at the text of the command, and a command can do things you can't tell from its text. Take a rule like this one, which is reasonable and which you'll probably write:

```json
{
  "permissions": {
    "allow": ["Bash(python -m pytest *)"]
  }
}
```

The rule approves `python -m pytest tests/`, and rightly so. But pytest runs every `conftest.py` it finds, and a `conftest.py` is arbitrary Python code: it can read `~/.ssh`, download a script, write outside the project. The same goes for a compromised dependency installed with `pip install` or `npm install`. The permission said yes to the right command, and the command did something else. The sandbox is the safety net that holds even when the permission decision was wrong.

## 2.10 The sandbox in detail

With the sandbox on, these are the defaults:

| Access | Default with the sandbox on | Changed with |
| --- | --- | --- |
| Write | Only the working directory, a personal temp folder and any folders you add. Claude Code's configuration files stay protected | `filesystem.allowWrite`, `filesystem.denyWrite` |
| Read | Almost the whole computer, including credentials like `~/.ssh` | `filesystem.denyRead`, `credentials` |
| Network | No direct access: everything goes through a local proxy that checks every domain, and the list of allowed domains starts out empty | `network.allowedDomains`, `network.deniedDomains` |
| Environment variables | Inherited from Claude Code | `credentials` |

Two rows deserve a comment. Claude Code's configuration files stay protected even inside the project folder, so a command can't write itself a more permissive `.claude/settings.json`. Reading, on the other hand, is permissive: that's why you should explicitly deny the folders that hold credentials. On the network side, a command in the sandbox has no direct route to the internet. It goes through a proxy running on your machine, and the first time a new domain is needed, Claude Code asks you whether to allow it.

The mechanism depends on the operating system:

| System | Mechanism | Notes |
| --- | --- | --- |
| macOS | Seatbelt, built into the system | Nothing to install |
| Linux | bubblewrap for the file system, socat for the network | `sudo apt-get install bubblewrap socat` |
| WSL 2 | Same as Linux | Doesn't work on WSL 1 |
| Native Windows | Not supported | Commands run without a sandbox: use WSL 2 |

If you work on Windows, this is one of the most concrete reasons to install Claude Code inside WSL 2, as suggested in chapter 1.

### Trying it out

In the `cc-advanced-lab` project, with Claude Code running, type `/sandbox` and press Enter. A menu opens: pick the auto-allow option (in the version I wrote this chapter on, it's `Sandbox BashTool, with auto-allow`). Claude Code replies with `Sandbox enabled with auto-allow for bash commands`. In auto-allow mode, commands that run inside the sandbox start without asking you, because the operating system guarantees the boundary.

Now ask Claude to run two commands, one per prompt:

```text
run this command in the terminal: touch ~/sandbox-probe
```

```text
run this command in the terminal: curl --noproxy '*' https://example.com
```

The first tries to write to your home directory, outside the project, and fails with `Operation not permitted` on macOS or `Read-only file system` on Linux. The second tries to reach the internet by going around the proxy, and fails with `Could not resolve host`.

At this point Claude may offer to retry the command outside the sandbox. In Manual you'll see a confirmation prompt: decline it. In auto mode, when I recorded the lesson, Claude retried the `touch` outside the sandbox on its own, and the classifier blocked it with the `bash denied by auto mode` banner. The two levels worked one after the other, exactly as in the figure. Finally, check:

```bash
ls ~/sandbox-probe
```

It should tell you the file doesn't exist.

The `/sandbox` menu saves your choice in the project's `.claude/settings.local.json`, the local settings file that stays out of Git. If you want the sandbox on in all your projects, with a few extra rules, the equivalent configuration goes in `~/.claude/settings.json`:

```json
{
  "sandbox": {
    "enabled": true,
    "allowUnsandboxedCommands": false,
    "filesystem": {
      "denyRead": ["~/.ssh", "~/.aws"]
    },
    "network": {
      "allowedDomains": ["github.com", "*.npmjs.org", "pypi.org"]
    }
  }
}
```

Setting `allowUnsandboxedCommands` to `false` closes the escape hatch you just saw: if a command fails in the sandbox, Claude can't ask to retry it outside. `denyRead` stops shell commands from reading your SSH keys and AWS credentials. `allowedDomains` allows the domains you use every day up front, so you aren't asked about them one at a time.

::: {.callout .callout-warning}
[Warning]{.callout-title}

The sandbox covers only shell commands and the processes they launch. `Read` and `Edit` follow the permission rules, not the sandbox. Hooks and MCP servers run outside the sandbox with your user permissions. The same goes for excluded commands: some tools, like `docker`, don't work inside the sandbox, and you can list them in `sandbox.excludedCommands` (for example `"docker compose *"`), knowing that from then on they can reach everything you can.
:::

### Sandbox, container and virtual machine

If you want a boundary around all of Claude Code, hooks and MCP servers included, the sandbox isn't enough: you need to isolate the whole process.

| Option | What it isolates | When to use it |
| --- | --- | --- |
| Claude Code's sandbox | Shell commands and the processes they launch | Everyday work on your own computer |
| Dev container | All of Claude Code, inside a container with a firewall | Projects you don't know, reproducible environments for the team |
| Dedicated container or VM | Everything, hooks and MCP servers included | Unattended autonomous runs, CI |

`bypassPermissions` only makes sense in the third row. On your laptop, with your SSH keys and your logged-in browser, the sensible combination is auto mode or Manual with the sandbox on.

## 2.11 Model and effort

The last piece of the mental model is the brain of the loop. Two settings decide which model does the reasoning and how much.

`/model` shows the models available on your plan and the active one. As I write there are four aliases: `opus` (Claude Opus 5.5, the default), `sonnet` (Claude Sonnet 5.5), `haiku` (Claude Haiku 5.5) and `fable` (Fable 5.1, the most capable, never on by default), all with a one-million-token context window. Defaults change often, and a name printed in a book ages fast: always check with `/model` what you're really using.

`/effort` sets how much Claude reasons before answering. You pick it from a selector with `low`, `medium`, `high`, `xhigh` and `max`; on the 5.5 models the default is `medium`, and `max` only lasts for the current session. Higher means more accurate answers on hard problems, but also slower ones that eat more of your plan, and in an agentic loop that cost multiplies with every turn. A rule of thumb:

| Work | Effort |
| --- | --- |
| Quick questions, small edits, renaming a variable | `low` or `medium` |
| Design, hard bugs, SDD specs | `high` |
| A single hard prompt in an otherwise normal session | `ultrathink` in the message |

Writing `ultrathink` in a prompt raises the reasoning for that message only, without touching the setting. Phrases like "think hard" or "think it through" aren't keywords: the model reads them as ordinary text. The active level shows up in the logo and in the spinner while Claude works.

In the rest of the book I won't tell you to change the effort in every chapter. Where it matters, for example when writing the Photogallery specs (chapter 18), you'll find it noted.

## Summary {.unlisted}

- An LLM takes text and returns text; an agent is an LLM that works in a loop, using tools to gather context, act and verify.
- The model never runs anything: it produces a `tool_use`, and the harness, meaning Claude Code, checks permissions and hooks, runs the tool and sends back a `tool_result`.
- `Ctrl+O` shows the individual calls: use it when you want to check what Claude actually did, beyond what it told you.
- Sessions start in auto mode; `Shift+Tab` switches to Manual, Accept edits and Plan.
- Permissions decide whether an action can go ahead and apply to every tool; the sandbox, turned on with `/sandbox`, limits files and network for shell commands, and the operating system enforces it.
- You pick the model with `/model` and the reasoning with `/effort`; for a single hard prompt, `ultrathink` is enough.

## Exercise {.unlisted}

In the `cc-advanced-lab` project, with the virtualenv active, start Claude Code in Manual:

```bash
claude --permission-mode manual
```

Ask:

```text
add a function media(path) to src/report.py that returns the average of the sales, with a test, and check that all the tests pass
```

Approve one request at a time and, for each, write down the tool and the loop phase (context, action, verification). When the work is done, open `Ctrl+O` and compare your list with the recorded calls.

Then turn on `/sandbox` with auto-allow and ask Claude to run `curl -sI https://pypi.org`. Watch what happens on the first request to a domain that isn't allowed yet.

The exercise is done when `pytest -q` prints `3 passed`, `git diff` shows changes only in `src/report.py` and `tests/test_report.py`, and you have an ordered list of the calls Claude made with the phase of each.
