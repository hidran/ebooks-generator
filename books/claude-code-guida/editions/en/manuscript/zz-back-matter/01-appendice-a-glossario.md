# Appendix A. Glossary

The terms that come up throughout the book, in alphabetical order. Commands and files are sorted by the first letter of the name, ignoring the leading slash or dot: `/goal` is under G, `.claude/rules/` under C. Each entry points to the chapter, numbered as in this edition, where the topic is covered in full. Model names and versions are as of October 2026: for current values, check `/model` and Appendix E.

## A

`acceptEdits`
:   The Accept edits mode: Claude edits files and runs commands that only touch files and folders without asking, and stops you on everything else. Chapters 2 and 11.

Agent, subagent
:   An instance of Claude that does a single job in its own context, with a dedicated system prompt and, if you want, a restricted set of tools, and hands only its report back to the main session. You define it in a Markdown file with `name` and `description` in the frontmatter, in `.claude/agents/`, `~/.claude/agents/` or a plugin. The `/agents` wizard was removed in July 2026: you write the file yourself or ask Claude to. In interactive sessions it runs in the background by default. In this book "agent" and "subagent" mean the same thing. Chapter 10.

`Agent` (tool)
:   The tool that launches a subagent; up to version 2.1.63 it was called `Task`. `Agent(model:opus)` in a rule matches subagents launched on Opus. Chapters 2 and 10.

agent view
:   The `claude agents` screen: background sessions grouped into Working, Needs input and Completed. `Space` opens the preview and lets you reply, `Enter` goes in, `←` on an empty prompt takes you back to the list, `Ctrl+T` pins a row to the top. Chapter 20.

agentic loop
:   The agent's cycle: gather context, act, check, start over until the work is done or it needs you. Chapter 2.

`AGENTS.md`
:   The instruction file shared across agents from different vendors. Claude Code reads it when the project has no `CLAUDE.md`; if both exist, import it with `@AGENTS.md`. Chapter 7.

allow, ask and deny rules
:   Exceptions to the mode, written as `Tool(specifier)`: `Bash(python -m pytest *)`, `Read(./.env)`, `mcp__github__*`. They're evaluated in the order deny, ask, allow. A `Bash` rule matches the text of the command, not the program. Chapter 11.

API key
:   The key for pay-as-you-go use from the Console. If `ANTHROPIC_API_KEY` is set and approved, it wins over your subscription: check with `/status`. Chapter 1.

atomic commit
:   A commit that holds one complete logical change. The `/commit` command you write in Chapter 8 produces it from the staged files; in the Photogallery it becomes one task, one commit. Chapters 8 and 19.

atomic task
:   A task that moves the project from one consistent state to the next and ends with a commit. In the Photogallery it has an ID (`T031`), the `DESIGN.md` sections to read and verifiable criteria. Chapters 16 and 18.

auto memory
:   The notes Claude writes on its own (preferences, corrections, context) in `~/.claude/projects/<project>/memory/`, shared across the repository's worktrees and invisible to your colleagues. Chapters 7 and 15.

auto mode
:   The default permission mode for interactive sessions since version 2.1.283 (since 2.1.228 for Pro, Max and Team). A classifier approves actions that fit the request and blocks risky ones; the blocks end up in `/permissions`, on the Recently denied tab. After three blocks in a row, or twenty in one session, it goes back to asking you. `claude -p` starts in Manual. Chapters 2 and 11.

## B

background session
:   A session that works without holding your terminal: `claude --bg --name <name> "<prompt>"` or `/background`. Before it edits files it moves into a worktree, and when it's done it commits and pushes. You manage it from agent view and with `claude attach`, `logs`, `stop`, `rm`. Chapter 20.

build workflow
:   The document that describes how the Photogallery plan gets executed: phases, working rules and the read, implement, test, commit, check off cycle. Chapters 17 and 18.

`bypassPermissions`
:   The mode with no checks, the same as the `--dangerously-skip-permissions` flag. Only in a throwaway container or VM; a hook that denies still blocks here. Chapters 2 and 11.

## C

change set
:   The preview of the changes CloudFormation would make to a stack. A `Replacement: True` on the RDS instance means a brand-new database. Chapter 23.

classifier
:   The model that judges actions on your behalf in auto mode. Deny and ask rules are evaluated first, and limits you state in the chat count as guidance for that session. `claude auto-mode defaults` prints its rules. Chapters 2 and 11.

Claude Code
:   Anthropic's agent that works on your project's files. It runs in the terminal, in VS Code, in JetBrains IDEs, in the desktop app and in the cloud. It isn't included in the claude.ai free plan. Chapter 1.

`.claude/rules/`
:   Markdown files with instructions split by topic. Without frontmatter they load at startup; with `paths:` only when Claude reads or edits a matching file. Personal rules live in `~/.claude/rules/`. Chapter 7.

`CLAUDE.md`
:   The instructions Claude Code loads in every session, on four levels: organization, user (`~/.claude/CLAUDE.md`), project (`./CLAUDE.md`, in Git) and local (`./CLAUDE.local.md`, kept out of Git). Best kept under two hundred lines; supports imports with `@path`; HTML comments never reach Claude. It steers the model but doesn't bind it. Chapters 7 and 15.

`/clear`
:   Starts over with an empty conversation; the previous one stays available in `/resume`. Aliases `/reset` and `/new`. Chapter 15.

CloudFormation, CloudFront
:   The AWS service that builds infrastructure from a YAML template, and the CDN that serves the Photogallery SPA and forwards `/api/*` to the ALB. Chapter 23.

Code Review on GitHub
:   The managed pull request review for Team and Enterprise plans, billed per review: inline comments with Important, Nit or Pre-existing severity, never an approval or a block. You re-run it with `@claude review` and customize it with `REVIEW.md`. Chapter 22.

`/code-review`
:   The local review (alias `/review`) of unpushed commits and uncommitted changes, in a background subagent. It takes an effort level and a target (`/code-review high main...feat/albums-api`); with no level it reuses the last one. Fixes applied by `--fix` can't be undone with `/rewind`. It reads `CLAUDE.md`, not `REVIEW.md`. Chapter 22.

compaction
:   The summary that replaces the oldest messages and frees up context. You start it with `/compact` plus instructions on what to keep; Claude Code also does it on its own near the limit. A `SessionStart` hook with the `compact` matcher puts back into context whatever mustn't be lost. Chapters 12 and 15.

companion repo
:   The book's GitHub repositories. Branch names such as `book/cap-13-wave-1-backend` follow the first edition's chapter numbers. See "How to read this book".

context, context window
:   Everything Claude sees: system instructions, tools, memory files, files it has read, output, messages. It goes up to a million tokens, but the fuller it gets, the more it costs and the more detail gets lost. Rule of thumb: one task, one session. Chapters 1 and 15.

`/context`
:   Shows how the window is split: system prompt, tools, MCP, agents, skills, memory files, messages, free space. Chapter 15.

custom command
:   A Markdown file in `.claude/commands/` or `~/.claude/commands/` that becomes a command: `fix-tests.md` is `/fix-tests`. Custom commands are now part of skills: they still work, but for new work a skill is the better choice, and it wins when the names clash. Chapter 8.

## D

`/doctor`, `claude doctor`
:   `claude doctor`, run from the shell, checks your installation and settings without opening a session and doesn't change anything. `/doctor` (alias `/checkup`) runs a broader check and can fix things; `/doctor prompt-audit` finds stale or conflicting instructions and proposes edits. Chapters 1 and 15.

`dontAsk`
:   The mode for scripts and CI: reads and pre-approved tools go through, everything else is denied without asking. Chapters 2 and 11.

DRY
:   "Don't Repeat Yourself", applied with the rule of three: on the second repetition you wait, on the third you extract. Chapter 18.

## E

ECS Fargate
:   The AWS service that runs containers with no servers to manage; the Photogallery API and worker run on it. Chapter 23.

effort
:   How much the model reasons. You pick it with `/effort` from `low`, `medium`, `high`, `xhigh` and `max` (for the current session only); on the 5.5 models the default is `medium`. For a single hard prompt, `ultrathink` is enough. Chapters 2 and 3.

Explore
:   The built-in read-only subagent that explores the code. Like Plan, it starts without `CLAUDE.md`. Chapter 10.

## F

Fable
:   The most capable model family in Claude Code, alias `fable` (Fable 5.1 as I write this). It's never the default: you pick it with `/model` or in a subagent's `model` field. Chapter 2.

Filament
:   The Laravel framework for admin panels, v5 in the Photogallery. Chapter 19.

Firebase Hosting
:   Google's static hosting, where you publish the landing page, with preview channels for previews. Chapter 16.

`/fork`
:   Copies the conversation into a new background session and leaves the main one where it is. Chapters 15 and 20.

frontmatter
:   The YAML block between two `---` lines at the top of a Markdown file, used by commands, skills, agents and rules. Chapters 7-10.

## G

`/goal`
:   A completion condition: Claude keeps going turn after turn until a separate evaluator judges it met. The evaluator sees only the conversation, so the condition has to name a check that Claude runs and shows ("`composer test` exits with code 0"). `/goal clear` cancels it. Chapter 20.

## H

harness
:   The program around the model: it manages the conversation, exposes the tools, enforces permissions and hooks, and executes the calls. Claude Code is a harness. Chapter 2.

headless
:   Non-interactive use with `claude -p "prompt"`, for scripts and CI. You declare the allowed actions with `--allowedTools`; `--bare` skips hooks, skills, plugins, MCP and `CLAUDE.md`. Chapter 1.

hook
:   A command Claude Code runs on its own when an event fires (`SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop`, `Notification` and others). It receives JSON on stdin; exit 0 continues, exit 2 blocks and sends stderr back to Claude, exit 0 with JSON on stdout gives finer control. You register it under `hooks` in `settings.json` or in a plugin; it runs outside the sandbox, and `/hooks` shows it. Chapter 12.

## I

idempotent
:   Giving the same result however many times you repeat it, like the photo job that writes each variant to a fixed path. Chapter 21.

`/init`
:   Writes a first version of `CLAUDE.md` by analyzing the project. Chapter 7.

## K

KISS
:   "Keep It Simple, Stupid": the simplest solution that meets the requirement, written into `CLAUDE.md` to fend off over-engineering. Chapters 17 and 18.

## L

Laravel Sail
:   Laravel's Docker environment; in the Photogallery it starts MariaDB, Redis, Mailpit and MinIO. Chapter 19.

Lovable
:   A tool that generates interfaces from a prompt; in the book it's the design you replicate. Chapter 16.

## M

Manual
:   The mode that asks for confirmation on almost everything, the default before auto mode. In the settings it's called `default`; the flag accepts `--permission-mode manual`. Chapters 2 and 11.

marketplace
:   A repository with a `.claude-plugin/marketplace.json` that lists plugins. The official `claude-plugins-official` is added on first launch; `anthropics/claude-code` is only a demo. You add one with `/plugin marketplace add`. Chapter 14.

matcher
:   The filter on a hook group: for tool events, the tool name (`"Edit|Write"`, case-sensitive); for `SessionStart`, the source (`compact`). The `if` field narrows it further. Chapter 12.

MCP (Model Context Protocol)
:   The protocol Claude Code uses to reach external services through an MCP server: remote over `http` (a token in a header, or OAuth) or local over `stdio`, started by Claude Code. The tools are named `mcp__<server>__<tool>` and follow the permission rules. You add a server with `claude mcp add` and check it with `/mcp`. Chapter 13.

`MEMORY.md`
:   The auto memory index, loaded in every session up to two hundred lines. Chapter 15.

`/memory`
:   Lists the loaded instruction files and turns auto memory on or off. It replaces the old `#` shortcut, which is gone. Chapters 7 and 15.

`/model`
:   Shows the models on your plan and switches the active one. Aliases: `opus`, `sonnet`, `haiku`, `fable`, `opusplan`. Chapters 1 and 2.

multi-LLM review (cross-LLM review)
:   The same changeset and the same prompt sent to different models (Claude, Gemini, Codex, Kimi), with the results aggregated by consensus. Chapter 22.

## O

openpyxl
:   The Python library that writes Excel files, formulas included. Chapter 5.

Opus
:   Claude Opus, alias `opus`; Opus 5.5 has been the default since September 2026. `opusplan` uses Opus in Plan Mode and Sonnet to execute. Chapter 2.

orphan task
:   A feature that's checked off but only half built: an empty endpoint, a component nobody imports. You deal with it using the three Ds: Delete, Complete, Document and defer. Chapter 22.

## P

permission mode
:   What Claude can do without asking. `Shift+Tab` cycles through auto, Manual, Accept edits and Plan; `dontAsk` and `bypassPermissions` are picked with `--permission-mode`. As a `defaultMode`, `auto` and `bypassPermissions` only take effect in `~/.claude/settings.json`. Chapters 2 and 11.

`/permissions`
:   The active rules, with the Allow, Ask, Deny and Recently denied tabs; each rule shows the file it comes from. Chapter 11.

Plan Mode
:   Claude reads and proposes a plan without changing anything until you approve. You enter it with `Shift+Tab`, `/plan` or `--permission-mode plan`; `Ctrl+G` opens the plan in your editor. Chapters 3 and 4.

plugin
:   A folder that bundles skills, agents, hooks and MCP servers. Only the `plugin.json` manifest goes in `.claude-plugin/`; the components live at the root. The `name` becomes the prefix (`/cc-lab-toolkit:report-pdf`). You manage plugins with `/plugin`, try one with `--plugin-dir`, check it with `claude plugin validate` and measure it with `claude plugin eval`. Chapter 14.

prompt injection
:   Instructions for the model hidden in external content that a tool reads, such as an issue or a web page. Chapter 13.

## R

RDS
:   AWS's managed database; the Photogallery uses MariaDB, the same engine as Sail. Chapter 23.

`REVIEW.md`
:   The instructions for Code Review on GitHub: what counts as Important, how many Nits, what to ignore, what to always check. Chapter 22.

`/rewind`
:   Rolls code, conversation or both back to an earlier point, also with `Esc Esc`. It doesn't undo what a `Bash` command did. Chapter 15.

## S

Sanctum
:   The Laravel package for API tokens; in the Photogallery every mutation checks the token's ability and the policy. Chapters 17 and 19.

sandbox
:   The boundary the operating system puts around shell commands and their child processes: writes in the working folder, reads almost everywhere except denied paths, network through a proxy with a domain list. Seatbelt on macOS, bubblewrap and socat on Linux and WSL 2, no support on native Windows. `Read`, `Edit`, hooks and MCP servers stay outside it. You turn it on with `/sandbox`. Chapters 2 and 11.

scope
:   Where a configuration applies. For an MCP server: `local` (the default), `project` (`.mcp.json` in Git, to be approved on first launch) and `user`. For a plugin: user, project, local. Chapters 13 and 14.

SDD (Spec Driven Development)
:   The Photogallery's method: the code follows from `docs/REQUIREMENTS.md`, `docs/DESIGN.md` and `docs/TASKS.md` (124 tasks in 14 phases), written and approved first. Chapters 17 and 18.

session
:   A conversation from startup to exit. `/resume` (alias `/continue`) picks it back up. Chapters 1 and 15.

`settings.json`
:   The settings: `~/.claude/settings.json` (all projects), `.claude/settings.json` (team, in Git), `.claude/settings.local.json` (just you, kept out of Git), plus the organization's managed settings. Chapter 11.

skill
:   A folder with a `SKILL.md` and any scripts and references it needs. The name and description always stay in context; the body loads when needed. You invoke it with `/name`, or Claude picks it from the description, which should be written as a trigger. `/skills` lists them, `/reload-skills` reloads them. Chapter 9.

skill-creator
:   The skill that creates other skills through a guided conversation. Chapter 9.

`/skill-doctor`
:   How much context each skill takes up and how often it's used. Chapter 15.

SOLID
:   The five principles of object-oriented design, written into the Photogallery's `CLAUDE.md` with examples from its own code. Chapter 18.

Sonnet
:   Claude Sonnet, alias `sonnet`: faster and cheaper than Opus. Chapter 2.

spec-critic
:   The subagent that rereads the specs like a hostile reviewer, hunting for security holes and requirements with no task. Chapter 18.

`/subtask`
:   A subagent that inherits the whole conversation. Chapter 10.

Superpowers
:   Jesse Vincent's plugin with skills for brainstorming, subagent-driven development, systematic debugging and TDD. You install it with `/plugin install superpowers@claude-plugins-official`. Chapters 8 and 16.

## T

`/tasks`
:   The session's subagents and background jobs; `Ctrl+X Ctrl+K` stops them all. Chapter 10.

token
:   The unit of text for models, roughly a piece of a word. Context, limits and costs are measured in tokens. Chapter 1.

tool
:   A function described to the model with a name, a description and a schema. The model asks for the call (`tool_use`), the harness runs it and replies with a `tool_result`. The main ones: `Read`, `Edit`, `Write`, `Bash` (which also handles searches on macOS, Linux and WSL), `WebSearch`, `WebFetch`, `Agent`, and the MCP tools. `Ctrl+O` shows the calls. Chapter 2.

tool search
:   At startup Claude Code loads only the names of the MCP tools and fetches their definitions when they're needed. Chapter 13.

## U

ultrareview
:   The multi-agent review in the cloud, in research preview: `/code-review ultra` or `claude ultrareview`. It needs a claude.ai account; Pro and Max get three free runs, then it uses credits. Chapter 22.

`ultrathink`
:   Written in a prompt, it raises the reasoning for that one message only. "think hard" has no special effect. Chapters 2 and 3.

`/usage`
:   What's eating into your plan limits, broken down by skill, subagent, plugin and MCP server. `/cost` and `/stats` are aliases. Chapters 1 and 15.

## V

vibecoding
:   Going straight to code, prompt after prompt, with no spec and no plan. Chapter 17.

visual companion
:   The part of the Superpowers brainstorming skill that generates HTML mockups and updates them while you comment. Chapter 16.

## W

wave
:   A group of plan phases that can run in parallel on tracks that share no files. Chapters 19 and 20.

wave review
:   The end-of-wave review done by several agents in parallel, each on a different aspect. Chapter 19.

worker
:   The process that runs the jobs in a queue: in the Photogallery, the `jobs` table in development and SQS in production. Chapters 21 and 23.

worktree
:   A second working folder for the same repository, with its own branch. `claude --worktree <name>` creates it in `.claude/worktrees/<name>`; `.worktreeinclude` lists the ignored files to copy; `"baseRef": "head"` starts it from your local `HEAD`; `isolation: worktree` gives every instance of a subagent a temporary one. Chapter 20.

WSL 2
:   Windows' Linux, required for the sandbox; WSL 1 isn't supported. Chapters 1 and 2.
