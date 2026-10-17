# Chapter 1. What Claude Code is

::: {.chapter-goals}
[What you'll learn]{.callout-title}

By the end of this chapter you'll have Claude Code installed and connected to your account, you'll know the dozen or so commands and shortcuts you'll use every day, and you'll have had Claude write and run a first program while you watched every step. You'll also know how the rest of the book is organized and where it makes sense to start.

[Prerequisites]{.callout-title}

A computer running macOS 13 or later, Windows 10 (1809) or later, or Linux (Ubuntu 20.04+, Debian 10+), with at least 4 GB of RAM. A paid Claude plan (Pro, Max, Team or Enterprise) or a Claude Console account. Python 3 for the example in section 1.5.

:::

Claude Code is the program Anthropic uses to put Claude inside your project. You open it in a folder, tell it what you want in plain English, and it reads files, edits them, runs commands and tells you what it did. This book starts here and ends, in Part VI, with a full-stack application deployed on AWS. In between there's a way of working that you pick up one piece at a time, and the first piece is getting the tool properly installed and knowing your way around it.

## 1.1 What Claude Code is

Claude Code is an agent for software development. It started life as a command-line program, and the terminal is still where it works best, but today the same agent also runs inside VS Code and JetBrains, in the Claude desktop app and in the browser (more on that at the end of section 1.3). In every case it works on the real files in your project, not on a copy pasted into a chat.

An agent is a language model that the harness, meaning the program around it, gives a set of tools: read a file, edit it, run a command. The model decides which tool it needs, Claude Code runs it and sends back the result, and the cycle repeats until the job is done or until it needs a decision from you. Chapter 2 takes this mechanism apart piece by piece. For now it's enough to know that the model asks and Claude Code executes, under your control.

### Compared with other tools

With a chat in the browser, whether it's claude.ai or something else, you do all the work around it. You pick which files to paste, copy the answer into your editor, run the tests, and go back to the chat with the error. The quality of the answer depends on how well you chose what to show the model.

Assistants built into the editor, like GitHub Copilot or Cursor, started out as code completion while you type, and today they have agent modes too. They're serious tools, and plenty of developers use them alongside Claude Code. The practical difference is where each one starts from: Claude Code was born in the terminal, so it runs anywhere you can open a shell (your laptop, a server over SSH, a container, a CI pipeline) and you can launch it from a script without any GUI at all.

There's no single best tool. Claude Code pays off most when the work is project-sized: a refactoring that touches ten files, a new feature with its tests, an unfamiliar codebase you need to understand fast. For completing the line you're typing, the editor's autocomplete is still more convenient.

### What it can actually do

It reads any text file in the project, from code to configuration, and edits it. It runs commands in the terminal, such as `npm install`, `pytest`, `git status` or `docker build`, and reads their output, errors included. It explores the folders to figure out how the project is laid out before touching anything. It works with Git: it reads the history, creates branches, commits, and prepares pull requests. Through MCP (Model Context Protocol) servers it connects to external services such as GitHub, a database or your calendar, which is the subject of chapter 13.

Everything goes through a conversation. You write what you want to get done, Claude proposes and acts, and for sensitive actions it asks your permission or blocks them. Which actions go through you is set by the permission mode (section 1.3).

## 1.2 Installation

The recommended install is the native installer: a single binary, no Node.js, no admin rights, and it updates itself in the background.

### The native installer

On macOS, Linux and WSL:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

On Windows, from PowerShell:

```powershell
irm https://claude.ai/install.ps1 | iex
```

Or from Command Prompt (CMD):

```batch
curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
```

If you already use Homebrew on your Mac, or prefer WinGet on Windows, these work too:

```bash
brew install --cask claude-code
```

```powershell
winget install Anthropic.ClaudeCode
```

With Homebrew and WinGet, updates aren't automatic: you run them yourself with `brew upgrade claude-code` or `winget upgrade Anthropic.ClaudeCode`. The Homebrew `claude-code` cask follows the stable channel, and there's also `claude-code@latest` for the channel with the newest releases. For Linux distributions there are also signed apt, dnf and apk repositories, which update through the system package manager.

### If you install with npm

The first edition of this book started with `npm install -g`. The npm package still exists and is documented as an advanced option, but it now requires Node.js 22 or later and installs the same native binary as the installer: the `claude` command doesn't need Node to run.

```bash
npm install -g @anthropic-ai/claude-code
```

Three things to know if you go this way. To update, use `npm install -g @anthropic-ai/claude-code@latest`, not `npm update -g`. Never use `sudo npm install -g`: it creates root-owned files that later block normal updates. If npm fails with an `EACCES` error on the global packages folder, the simplest fix is to give up on npm and use the native installer. With a Node older than 22, npm only shows an `EBADENGINE` warning and carries on, so check `node --version` first.

### Checking the install and updating

Open a new terminal, so the shell re-reads the `PATH`, and check:

```bash
claude --version
claude doctor
```

The first command prints the version, something like `2.1.302 (Claude Code)`. The second checks the installation and the settings files without starting a session, and tells you what's wrong and how to fix it. It's read-only: it doesn't change anything.

The native install updates itself. Claude Code checks at startup and periodically, and the new version kicks in the next time you restart it. If you want to update right away:

```bash
claude update
```

You can choose between two update channels: `latest`, the default, which gets every release, and `stable`, which usually runs about a week behind and skips releases with serious regressions. You switch from `/config`, under Auto-update channel, or at install time with `curl -fsSL https://claude.ai/install.sh | bash -s stable`. If you use Claude Code on work projects and don't care about trying new features the day they ship, `stable` is a sensible choice.

### Windows

On Windows the native installer works straight from PowerShell or CMD, without WSL.

Git for Windows is no longer required. If it's installed, Claude Code uses Git Bash to run commands; if it isn't, it uses PowerShell. It's worth installing anyway, because you need Git regardless, and some Claude Code features, such as the `Bash` tool and the Monitor for following logs, need Git Bash. If Claude Code can't find Git Bash, set the path in `%USERPROFILE%\.claude\settings.json`:

```json
{
  "env": {
    "CLAUDE_CODE_GIT_BASH_PATH": "C:\\Program Files\\Git\\bin\\bash.exe"
  }
}
```

There's still one reason to pick WSL 2. The command sandbox, which restricts the files and network access of whatever Claude runs in the terminal (chapters 2 and 11), doesn't work on native Windows and does work on WSL 2. If you work with Linux toolchains or want the sandbox, install Claude Code inside WSL 2 with the Linux command, the one with `install.sh`. WSL 1 isn't supported.

### If something goes wrong

The most common case is `command not found` right after installing. Nearly always, closing the terminal and opening a new one fixes it. If it doesn't, check that the folder where the installer puts the binary is on your `PATH`. On macOS and Linux that's `~/.local/bin`, on Windows `%USERPROFILE%\.local\bin`:

```bash
echo $PATH | tr ':' '\n' | grep local
```

If the folder isn't listed, add `export PATH="$HOME/.local/bin:$PATH"` to your `~/.zshrc` or `~/.bashrc` and reopen the terminal.

If you installed Claude Code with npm in the past and now use the native installer, you can end up with two different `claude` binaries. `which -a claude` lists them all, and the one that counts is the first. Uninstall the npm version with `npm uninstall -g @anthropic-ai/claude-code` to avoid surprises.

On Windows, two errors just mean you pasted the command into the wrong shell. `The token '&&' is not a valid statement separator` means you're in PowerShell and used the CMD command; `'irm' is not recognized` is the opposite case.

For anything else, start with `claude doctor`. Inside a session there's also `/doctor`, which runs a broader check and can apply the fixes itself.

### Account and first login

Claude Code isn't included in the free claude.ai plan. It works with a Pro or Max subscription, with Team and Enterprise plans, with a Claude Console account (pay as you go, per token) and with the cloud providers: Amazon Bedrock, Google Cloud (Agent Platform, formerly Vertex AI) and Microsoft Foundry.

The first time, you just run:

```bash
claude
```

Claude Code asks you to pick a color theme, then opens the browser for the login. Choose the account type (Claude subscription, Console, or third-party platform), authorize access and go back to the terminal. If the browser doesn't open on its own, copy the URL shown in the terminal, complete the login by hand and paste the code you get back. With a Console account you no longer need to create an API key: the browser login is enough.

The other account commands are `/login`, to sign in or switch accounts, and `/logout`, which signs you out and also resets the first-run settings. From the shell, the equivalents are `claude auth login`, `claude auth logout` and `claude auth status`.

::: {.callout .callout-warning}
[Warning]{.callout-title}

If your shell defines the `ANTHROPIC_API_KEY` variable and you approve it when Claude Code asks, that key wins over your subscription: you pay as you go on the Console even if you have a Max plan. This happens a lot to people who export the key in `.zshrc` for other projects. In `claude -p` mode the key is always used, without asking. Check which authentication method is active with `/status`; if it's not the one you want, run `unset ANTHROPIC_API_KEY` and restart Claude Code.
:::

### Your first session in a folder

Claude Code works in the folder you launch it from. Before starting it, move into the project:

```bash
mkdir mio-progetto
cd mio-progetto
claude
```

The first time you open it in a folder, it asks whether you trust the files in it. Say yes only for folders you know: a project downloaded from the internet can contain configuration files that Claude Code reads and applies. The first session in auto mode also shows a notice explaining the mode (more on that shortly).

Then the welcome screen appears, with the active model, your account and the current folder, and below it the prompt where you type. To quit, use `/exit` or press `Ctrl+C` twice.

<!-- TODO screenshot: fig-01, schermata di benvenuto della versione corrente (modello Opus 5.5, cartella di prova). Senza email, nome dell'organizzazione o percorsi personali. -->

## 1.3 Basic commands and modes

Anything that isn't a prompt starts with a slash. Type `/` and Claude Code shows the list of commands, which filters as you type. The list also includes skills, your own or those from installed plugins, because you invoke them the same way. There are dozens of commands; the ones below are the ones you'll use from day one.

`/help` shows help with the main shortcuts and the list of available commands. Give it a couple of minutes the first time.

<!-- TODO screenshot: fig-02, scheda general di /help nella versione corrente. La vecchia cattura (v2.1.78, Opus 4.6) mostrava "& for background", che non va presentato. -->

### The conversation and the context

Everything Claude sees in a session lives in the context window: the system instructions, project files like `CLAUDE.md`, the files it has read, the commands it has run and your messages. With current models the window goes up to a million tokens, but the fuller it gets, the more the session costs and the more likely Claude is to lose details from the beginning. The rule of thumb is one task, one session. `/context` shows how full it is and what's taking up the space; chapter 15 is all about this.

Four commands manage the conversation:

```text
/clear                    start over with an empty context
/compact [instructions]   summarize the conversation and free up space
/resume                   pick up a previous session
/rewind                   go back to an earlier point in the session
```

`/clear` is the one to use when you switch topics. The old conversation doesn't disappear: you'll find it in `/resume`, and if you type `/clear name` you give it a label so you can recognize it. `/compact`, on the other hand, stays in the same session and replaces old messages with a summary. You can tell it what to keep, for example `/compact keep the decisions about the CSV format and the list of changed files`. `/resume` opens the list of past sessions, or resumes the one you name directly by name or ID. `/rewind` rolls back the code, the conversation or both to a checkpoint. You can also open it by pressing `Esc` twice on an empty prompt, and it's the first command to remember when Claude heads down the wrong path.

### Status, usage and settings

`/status` opens the settings on the Status tab: version, model, account and authentication method, connectivity. It's the command you want when something doesn't add up, starting with the API key case above.

`/usage` shows how much you're using. With a Console account you see the session cost; with a subscription you see your plan limits, how much of them you've used and what's eating into them, broken down by skill, subagent, plugin and MCP server. `/cost`, the first edition's command, still works: it's now an alias of `/usage`, as is `/stats`.

<!-- TODO screenshot: fig-04, output di /usage su un abbonamento (sostituisce la vecchia cattura di /cost). -->

`/model` shows the models available on your plan and the active one, and lets you switch. Your choice becomes the default for later sessions; if you press `s` in the picker it applies only to the current session, and the left and right arrows adjust the effort. As I write, the default is Claude Opus 5.5. The other aliases are `sonnet`, faster and cheaper, `haiku`, the quickest for repetitive work, and `fable`, the most capable, which is never the default. There's also `opusplan`, which uses Opus while planning and Sonnet while executing. Model names change every few months, so don't trust the ones printed here: check `/model`. Models and effort are explained in chapter 2.

<!-- TODO screenshot: fig-03, selettore di /model nella versione corrente (sostituisce la vecchia cattura con Sonnet 4.6). -->

`/config` opens all the settings: theme, update channel, the editor's vim mode (the old `/vim` command is gone), API key usage and a lot more. It also accepts the form `/config key=value`, for example `/config model=sonnet`.

`/init` analyzes the project and writes a first `CLAUDE.md`, the file of instructions Claude reads at every session. On an empty project you don't need it; on a real project it's one of the first things to do, and chapter 7 explains how to review what it generates.

Finally, `/btw` lets you ask a quick side question, for example what an error means, without it ending up in the main conversation.

### Keyboard shortcuts

| Key | What it does |
| --- | --- |
| `!` at the start of the prompt | Shell mode: runs the command, adds the output to the conversation and Claude comments on it |
| `@` | Completes file paths, to point Claude at a specific file |
| `?` on an empty prompt | Shows the shortcuts help |
| `Esc` | Interrupts Claude while it works, or closes a menu |
| `Esc` twice | Clears the text you've typed; on an empty prompt opens `/rewind` |
| `Shift+Tab` | Cycles the permission mode (on some Windows setups it's `Alt+M`) |
| `Ctrl+O` | Shows the detailed transcript, with every tool call |
| `Ctrl+R` | Searches your prompt history |
| `Ctrl+G` | Opens the prompt in your external editor, handy for long texts |
| `Ctrl+B` | Sends a running command or agent to the background |
| `Ctrl+T` | Shows or hides Claude's checklist of steps |
| `Shift+Enter` | Inserts a newline without sending |
| `Ctrl+V` | Pastes an image, for example a screenshot of an error (`Alt+V` on Windows and WSL, `Cmd+V` in iTerm2) |

`Shift+Enter` works out of the box in iTerm2, WezTerm, Ghostty, Kitty, Warp, macOS Terminal and Windows Terminal. In other terminals run `/terminal-setup`, or use `\` followed by Enter, which works everywhere. The up arrow scrolls through previous prompts, as in a shell.

If you're coming from the first edition: the `#` shortcut for adding a line to memory has been removed. To save an instruction, ask Claude to add it to `CLAUDE.md`, or use `/memory` (chapter 7).

### Interactive and headless

So far you've seen interactive mode: you type, Claude answers, the session stays open. With the `-p` flag Claude Code runs a single prompt, prints the answer and exits:

```bash
claude -p "analyze main.py and tell me how many functions it contains"
```

This is the mode for scripts, CI and scheduled jobs, and it also takes input from a pipe, as in `git diff | claude -p "summarize these changes"`. In `-p` there's nobody to ask for confirmation, so actions that aren't pre-approved don't run. You authorize them with `--allowedTools`, for example `--allowedTools "Bash(git diff *),Read"`. In scripts it's a good idea to add `--bare`, which skips hooks, skills, plugins, MCP servers and `CLAUDE.md` and makes the result predictable, plus `--output-format json` when another program has to read the output.

### Permission modes

The permission mode decides which actions Claude can take without asking you, and it's shown in the status bar below the prompt. Interactive sessions start in auto mode, where a classifier approves actions consistent with your request and blocks risky ones. `Shift+Tab` moves you to Manual, which asks for confirmation for almost everything, then to Accept edits and to Plan. Chapter 2 explains how they work and chapter 11 how to configure them. There's also the `--dangerously-skip-permissions` flag, which removes every check: use it only inside a throwaway container or virtual machine, never on your laptop.

### Beyond the terminal

In VS Code (and in Cursor), install the `anthropic.claude-code` extension: it's the recommended way to use Claude Code in the editor, with a plan you can review, inline diffs and file references with line numbers. The extension bundles its own copy of the CLI for the chat panel; if you also want the `claude` command in the integrated terminal, install the CLI as shown above. For IntelliJ, PyCharm, PhpStorm and the other JetBrains IDEs there's the Claude Code [Beta] plugin, which doesn't include the CLI: install that first. The Claude desktop app has a Code tab (macOS, Windows, Linux in beta), and `/desktop` moves the session you have open in the terminal over to it. Finally, cloud sessions on claude.ai/code run on Anthropic's servers: you start them from the browser or from the terminal with `claude --cloud "<task>"` and bring them back to your machine with `claude --teleport`. In this book we work in the terminal almost all the time, because that's where you can see best what's going on.

### The .claude folder

Claude Code keeps its configuration in two places. In your home directory, `~/.claude/` holds your personal settings (`settings.json`), your personal `CLAUDE.md`, the skills and agents that apply to every project, the installed plugins and, under `projects/`, saved sessions and auto memory. In the project, `.claude/` holds settings and extensions shared with the team through Git. We come back to this in Parts III and IV.

## 1.4 A comfortable working setup

You'll spend a lot of hours reading diffs and test output in the terminal, and one that handles scrolling, search and colors well makes a real difference. Nothing in this section is required.

### The terminal

On macOS there are two common choices. iTerm2 (iterm2.com) is free and mature: split panes, regex search through the scrollback, different profiles for different environments. Warp (warp.dev), free for personal use, groups each command with its output into a block you can select, copy and find again, and when Claude produces long output it's a convenient way to jump back to a specific part without losing your place.

On Windows, use Windows Terminal, which comes preinstalled on Windows 11 and is a free download from the Microsoft Store on Windows 10. It has tabs, split panes and a profile for each shell: PowerShell for the native install, Ubuntu if you work in WSL 2.

On Linux, your distribution's terminal, GNOME Terminal or Konsole, is perfectly fine. If you want something faster, Alacritty and Kitty are good alternatives.

### Shell and prompt

On macOS the default shell has been zsh since 2019. On Linux it's often bash; if you want zsh, install it with the package manager (`sudo apt install zsh` on Ubuntu) and set it with `chsh -s $(which zsh)`. oh-my-zsh (ohmyz.sh) adds advanced completion and suggestions from your history; fish (fishshell.com) has them built in, no plugins needed.

Whatever shell you use, install Starship (starship.rs), a prompt that works with zsh, bash, fish and PowerShell. It shows the Git branch and repository status, the active Node version or Python virtualenv, and how long the last command took, which is useful for seeing how long the commands Claude runs take.

On macOS:

```bash
brew install starship
```

On Linux and WSL:

```bash
curl -sS https://starship.rs/install.sh | sh
```

Then add this at the end of your `~/.zshrc` and restart the terminal:

```bash
eval "$(starship init zsh)"
```

### Aliases

Three aliases I use every day, for your `.zshrc` or `.bashrc`:

```bash
alias c='claude'                                # interactive start
alias cm='claude --permission-mode default'     # start in Manual
alias cq='claude -p'                            # quick headless question
```

I reach for `cm` when I'm working on a project I don't know and want to see every action before it runs. `cq` is for quick questions: `cq "which version of Laravel does this project use?"`. In the first edition the headless alias was called `cp`. That was a mistake, because it shadows the `cp` command for copying files. The same list had an alias for `--dangerously-skip-permissions`, which I've dropped for the reasons given in section 1.3.

### Dotfiles

Keep your terminal configuration in a Git repository: a `dotfiles/` folder with at least `.zshrc`, `.gitconfig` and your Starship config, plus a small `install.sh` that creates the symlinks in your home directory. When you switch laptops, you get your whole environment back in a few minutes. The `~/.claude/` folder, with your settings and personal skills, is a great candidate to add.

## 1.5 Your first guided prompt

This example takes five minutes and an empty folder. We'll do it in Manual, the mode that asks for confirmation for every action, because the first time it's worth seeing each step before it happens.

```bash
mkdir -p ~/projects/hello-claude && cd ~/projects/hello-claude
claude --permission-mode default
```

If Claude Code asks whether you trust the folder, say yes. The status bar should show `manual mode on`. Now type this prompt (the Italian strings are on purpose: they match the output shown below and the exercise at the end of the chapter):

```text
Create a hello.py file that prints a greeting to the terminal.
Add an optional --name argument (default "mondo")
and print "Ciao <name>". Use argparse to handle the argument.
```

Claude looks at the folder, sees it's empty and decides it needs just one file. Before writing it, it shows you the content it wants to create and asks whether to go ahead. You'll see something like this:

```python
#!/usr/bin/env python3
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="mondo")
    args = parser.parse_args()
    print(f"Ciao {args.name}")


if __name__ == "__main__":
    main()
```

The exact code varies a bit from one run to the next. Read it, then confirm with the first option. The file shows up in the folder.

Now ask Claude to try it:

```text
Run hello.py with no arguments and then with --name Hidran.
```

Claude proposes the first command, `python3 hello.py` (or `python hello.py`, depending on your system), and waits for your confirmation. Then the second one. The output is:

```text
Ciao mondo
Ciao Hidran
```

You didn't open an editor and you didn't copy code from anywhere.

::: {.callout .callout-tip}
[Tip]{.callout-title}

For the first few days, read every proposal before you confirm it, even when it's obvious. It's the fastest way to learn how Claude reasons, which files it looks at and which commands it prefers. Once you've got a feel for it, go back to auto mode with `Shift+Tab` and leave the routine confirmations to the classifier.
:::

### What just happened

Claude gathered context (the folder was empty), acted (it wrote the file) and verified (it ran the program and read the output). Every action went through you before it ran, because you were in Manual. This cycle of context, action and verification is the agentic loop, and you'll find it unchanged on the Photogallery, with a Laravel and React project in place of a single file. In chapter 2 you look at it from the inside with `Ctrl+O`.

You can delete the folder with `rm -rf ~/projects/hello-claude`, but you're better off keeping it: you'll use it in the end-of-chapter exercise, and it's a safe place to try the commands from the next chapters without putting code that matters at risk.

::: {.callout .callout-prompt}
[Reusable prompt]{.callout-title}

The first prompt I write on a project I don't know, before asking for any change:

```text
Read the files in the project and tell me:
1. What tech stack you see
2. Which part looks most recent and which looks oldest
3. Which file is the entry point
4. What you DON'T understand right away from the folder names
```

It works on any codebase. The fourth question is the most useful one: it tells you where Claude will struggle, and so what you'll need to explain to it or put in `CLAUDE.md`.
:::

## 1.6 Map of the book

The book is split into six parts. Each one builds on what you learned in the earlier ones.

| Part | Chapters | What you do |
| --- | --- | --- |
| I. Foundations | 1-3 | Install Claude Code, learn how tools, the agentic loop, permissions and the sandbox work, learn to write useful prompts and to use Plan Mode |
| II. Data analysis | 4-6 | Start from a CSV of SaaS metrics and end up with an Excel report with real formulas, charts, a Flask dashboard and a PDF |
| III. Extending Claude Code | 7-10 | Write `CLAUDE.md`, custom commands, skills and agents, and try the Superpowers plugin |
| IV. Control and automation | 11-15 | Permissions, modes and the sandbox, hooks, MCP servers, plugins and marketplaces, context and memory |
| V. Landing page | 16 | The first complete project, from idea to deploy on Firebase |
| VI. Photogallery | 17-23 | A full-stack application built with Spec Driven Development, all the way to deploy on AWS |

Part IV is new in this edition. It exists because Claude Code now starts in auto mode and works for long stretches without asking you anything, so you'd better know exactly where the guardrails are and how to move them. It works on a small lab project, `cc-advanced-lab`, which you already create in chapter 2.

Part VI is the heart of the book. You build the Photogallery: a REST API in Laravel 13, an admin panel in Filament v5, a React 19 frontend with Vite 6 and Tailwind CSS v4, authentication with Sanctum tokens, and queued jobs to resize photos and read their EXIF data. First you write the specs and turn them into a plan of 124 tasks in 14 phases, then you execute them in waves with a review after each one, in parallel too, on separate worktrees. Before the deploy you do QA, a review with `/code-review` and a second opinion from other models (Gemini, Codex, Kimi). It wraps up with the deploy to AWS using CloudFormation. The code is in the `github.com/hidran/claude-code-book-photogallery` repository, with a branch for each milestone.

At the end you'll find five appendices: glossary, troubleshooting, a prompt collection, resources and a changelog.

You don't have to read everything in order, but the first time you should. The only reasonable exception is Part IV, which you can also read after the projects in Parts V and VI. If you work on code that matters, though, read it first.

## Summary {.unlisted}

- Install Claude Code with the native installer, which updates itself. Homebrew and WinGet are alternatives with manual updates; npm is an advanced option that requires Node.js 22+.
- `claude doctor` is the first check when something doesn't work; `claude update` updates right away.
- You need a paid plan or a Console account. An approved `ANTHROPIC_API_KEY` wins over your subscription, so always check with `/status`.
- The everyday commands are `/clear`, `/compact`, `/resume`, `/rewind`, `/usage` (which absorbed `/cost`), `/model`, `/config` and `/init`.
- Sessions start in auto mode; `Shift+Tab` cycles to Manual, Accept edits and Plan. `claude -p` runs a single prompt and exits.
- On Windows the native installer works without WSL, but the sandbox needs WSL 2.

## Exercise {.unlisted}

First, check your setup. `claude doctor` should report no errors, and in a session `/status` should show the account and authentication method you expect (subscription or Console).

Then go back to `~/projects/hello-claude` and start `claude` with no flags, so in auto mode. Ask:

```text
Add a --maiuscolo option to hello.py that prints the greeting in uppercase, then run it with and without the option.
```

Count how many confirmations it asks for compared with the Manual run in section 1.5. When it's done, press `Esc` twice on an empty prompt and go back to the checkpoint before the request, restoring the code. If Claude changed the file with a shell command instead of the `Edit` tool, the checkpoint doesn't cover that change: in that case remove the option by hand or ask Claude to do it.

The exercise is done when `python3 hello.py --name Hidran` prints `Ciao Hidran` and `python3 hello.py --maiuscolo` exits with the argparse error `unrecognized arguments: --maiuscolo`, a sign that the rewind took the file back to its starting version.
