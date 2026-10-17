# Claude Code facts, October 2026

The single source of truth for the second edition. Part A comes from the author's
course update plan (`claude-course-studio/courses/claude-code/plan/piano-aggiornamento.md`),
checked against the official docs on 10 October 2026 and used in recorded lessons.
Part B was re-verified against code.claude.com on 17 October 2026 (see
`FACTS-verified.md` for sources). When the two disagree, Part B wins.

Book anchor: written against Claude Code 2.1.x in October 2026, default model Claude
Opus 5.5 with a 1M-token context window. Model names and defaults change often: the
text tells the reader to check `/model` rather than trusting a name in print.

## A. From the course update plan

### Install and update
- Native installer, no Node.js needed, no admin rights.
  macOS, Linux, WSL: `curl -fsSL https://claude.ai/install.sh | bash`.
  Windows PowerShell: `irm https://claude.ai/install.ps1 | iex`.
  Windows CMD: `curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd`.
  WinGet: `winget install Anthropic.ClaudeCode` (updates are manual).
- Wrong-shell errors: `The token '&&' is not a valid statement separator` means you are
  in PowerShell with the CMD command; `'irm' is not recognized` is the reverse.
- `claude --version`, `claude doctor` (installation state, settings errors, suggested
  fixes, without starting a session), `claude update` (force an update). Native installs
  update themselves in the background. `/config` chooses the update channel: `latest`
  or `stable` (about a week behind, skips releases with major regressions).
- Windows: Git for Windows is optional now. If present, Claude Code uses Git Bash; if
  not, PowerShell. Still recommended (Bash tool, Monitor). Path override:
  `"env": { "CLAUDE_CODE_GIT_BASH_PATH": "C:\\Program Files\\Git\\bin\\bash.exe" }` in
  `%USERPROFILE%\.claude\settings.json`. The command sandbox does not work on native
  Windows; WSL 2 supports it.

### Agents, tools, harness
- An LLM takes text and returns text. A tool is described with name, description and
  input schema; the model emits a `tool_use` request, the harness (Claude Code) checks
  permissions and hooks, runs the tool, returns a `tool_result`.
- Agentic loop: gather context, act, verify, repeat until done or until it needs you.
- Main tools: `Read` (context); `WebSearch`, `WebFetch`; `Edit`, `Write`; `Bash`
  (`PowerShell` on Windows; on macOS/Linux/WSL native builds it also does the searching,
  since `Grep` and `Glob` are absent by default there, see part B); `Agent` (subagent
  with its own context); MCP tools. The task list tools are not offered on newer models
  (part B). `Ctrl+O` shows the individual tool calls.

### Permission modes (auto is the default)
- Since version 2.1.283 interactive sessions in the terminal and VS Code start in
  **auto mode**: a classifier model reviews actions, lets through those consistent with
  the request, blocks risky ones (download-and-run scripts, force push, irreversible
  deletes, production deploys, sending sensitive data out). First run shows a notice.
- `Shift+Tab` cycles: auto, Manual (`default`), Accept edits (`acceptEdits`), Plan
  (`plan`), back to auto. Status bar shows the mode (`auto mode on`, `manual mode on`,
  `accept edits on`, `plan mode on`).
- Not in the cycle: `dontAsk` (only pre-approved tools, rest denied; CI and scripts),
  `bypassPermissions` (no checks; isolated containers or VMs only).
- Start flag: `claude --permission-mode default` / `plan`. Setting:
  `{"permissions": {"defaultMode": "default"}}`.
- Auto mode: blocked actions appear in `/permissions`, tab **Recently denied**, where you
  can retry them. `claude auto-mode defaults` prints the classifier rules. Limits stated in
  chat ("don't push") are honoured as hints, not saved rules. After 3 consecutive or 20
  total blocks, auto mode pauses and goes back to asking.

### Permission rules
- `.claude/settings.json` with `permissions.allow`, `ask`, `deny`, syntax
  `Tool(specifier)`: `"Bash(python -m pytest *)"`, `"Read(./.env)"`,
  `"Agent(model:opus)"` (parameter:value syntax), `mcp__github__*`.
- Evaluation order: deny, then ask, then allow. A deny always wins.
- A Bash rule matches the command text, not the program; for a real boundary use the
  sandbox or a hook. CLAUDE.md instructions guide but are not permissions.
- Files: `~/.claude/settings.json` (all your projects, not in Git),
  `.claude/settings.json` (project, team, in Git), `.claude/settings.local.json`
  (project, only you; "don't ask again" lands here), managed settings (organisation,
  cannot be overridden).

### Sandbox
- Two levels: permissions decide whether a call may start (every tool); the sandbox
  limits what a shell command and its child processes can reach once started. Read,
  Edit, hooks and MCP servers are outside the sandbox and follow permissions only.
- Defaults with sandbox on: write only in the working folder, a personal temp folder and
  added folders (Claude Code config files stay protected); read almost everything
  (deny `~/.ssh`, `~/.aws` explicitly); network only through a local proxy with an
  initially empty domain allowlist (Claude Code asks the first time a domain is needed).
- Keys: `sandbox.enabled`, `sandbox.allowUnsandboxedCommands` (false closes the
  retry-outside route), `filesystem.allowWrite`, `filesystem.denyWrite`,
  `filesystem.denyRead`, `network.allowedDomains`, `network.deniedDomains`, `credentials`;
  excluded commands (e.g. docker) run outside the sandbox with full permissions.
- macOS: Seatbelt (built in). Linux: bubblewrap + socat
  (`sudo apt-get install bubblewrap socat`). WSL 2 as Linux; WSL 1 not supported.
  Native Windows: not supported.
- `/sandbox` enables it; auto-allow mode runs sandboxed commands without prompts.
- Probe: `touch ~/sandbox-probe` fails (`Operation not permitted` on macOS,
  `Read-only file system` on Linux); `curl --noproxy '*' https://example.com` fails with
  `Could not resolve host`.
- Full isolation of all of Claude Code (hooks, MCP too): dev container or dedicated
  container/VM.

### Models and effort
- `/model` shows models available on your plan. Default: Claude Opus 5.5, 1M context.
- `/effort` chooses a level with a selector, from `low` to `xhigh`. Low/medium for quick
  questions and small edits, high for design, hard bugs, SDD specs. `ultrathink` in a
  single message raises reasoning for that prompt only. The level shows in the logo and
  the spinner.

### Hooks
- Events: `SessionStart` (start, resume, after `/clear` or a compaction; cannot block),
  `UserPromptSubmit` (can block), `PreToolUse` (can block), `PostToolUse` (cannot block,
  tool already ran), `Stop` (can block: makes Claude continue), `Notification` (cannot
  block). There are more events.
- Input: event JSON on stdin (`session_id`, `cwd`, `hook_event_name`, `tool_name`,
  `tool_input`). Exit 0: no objection (for PreToolUse it is not an approval, normal
  permissions apply). Exit 2: block, stderr goes back to Claude. Exit 0 plus JSON on
  stdout for finer control (`{"decision": "block", "reason": "..."}` for Stop).
- Config under `hooks` in settings.json: event, `matcher` (e.g. `"Edit|Write"`, case
  sensitive), `hooks: [{type: "command", command: "...", timeout: 120}]`.
  `$CLAUDE_PROJECT_DIR` points to the project root. `if` field uses permission-rule
  syntax (`"if": "Bash(git *)"`). `SessionStart` with matcher `compact` re-injects context
  after compaction. Stop hooks must check `stop_hook_active` to avoid infinite loops.
- Types: `command`, `http`, `prompt`, `agent` (agent hooks experimental).
- A hook that denies blocks in every mode, even `bypassPermissions`.
- `/hooks` lists registered hooks. Test by piping sample JSON with `echo`. A shell
  profile `echo` can pollute JSON output: guard with `if [[ $- == *i* ]]`.

### MCP
- `claude mcp add --transport http <name> <url> [--header "K: V"] [--scope local|project|user]`;
  `claude mcp add --transport stdio <name> [--env K=V] -- <command> [args]`
  (the `--` separates Claude Code options from the server's); `claude mcp add-json`;
  `claude mcp list | get | remove`; `claude mcp login | logout <name>`;
  `claude mcp reset-project-choices`. `mcp add` saves without checking credentials.
- GitHub remote server: `https://api.githubcopilot.com/mcp/` with a fine-grained PAT in
  the Authorization header. Many remote servers use OAuth: add without headers and log in
  via `/mcp` or `claude mcp login`.
- DBHub local server for SQL databases: `npx -y @bytebase/dbhub --dsn "sqlite:///..."`.
  Use read-only DB users.
- Scopes: `local` (default; this project, only you; `~/.claude.json`), `project`
  (`.mcp.json` in the root, in Git), `user` (all your projects; `~/.claude.json`).
  `.mcp.json` supports `${VAR}` and `${VAR:-default}`. Some credential variables (Claude
  Code's own, cloud providers') are never expanded towards a remote server. Project
  servers need approval on first start.
- Resources via `@`, prompts as `/server:prompt (MCP)`. Tool search: only tool names load
  at startup, full definitions on demand. `/context` shows their cost.
- Prompt injection risk from servers reading external content.

### Plugins
- Folder with `.claude-plugin/plugin.json` (only the manifest goes there; `name` is
  required and becomes the prefix). Components at the plugin root: `skills/`, `agents/`,
  `hooks/hooks.json`, optional `.mcp.json`. Hook scripts use `${CLAUDE_PLUGIN_ROOT}`.
- `/plugin` manager tabs: Discover, Installed, Marketplaces, Errors. Shows context cost.
  Official marketplace `claude-plugins-official`, e.g.
  `/plugin install plugin-dev@claude-plugins-official`. `/plugin list`.
  Install scopes user, project, local.
- `claude plugin validate ./dir`; `claude --plugin-dir <dir>` loads for one session;
  `/reload-plugins` reloads. Skills get the prefix: `/cc-lab-toolkit:report-pdf`.
- Marketplace: repo with `.claude-plugin/marketplace.json` (`name`, `owner`, `plugins`
  with `name`, `source`, `description`). `/plugin marketplace add <path|user/repo>`,
  `/plugin install <plugin>@<marketplace>`. Version bump in the manifest ships updates.
  `claude plugin init` creates a personal always-on plugin.
- Evals: `claude plugin eval init` (interactive, writes `evals/`), `claude plugin eval .`
  (each case 3 runs with and 3 without; columns WITH, W/OUT, Δ, COST; `report.html`);
  `--case <name> --runs 1 --ablation none` to iterate cheaply. Needs Git 2.31+. Add
  `evals/results/` to `.gitignore`. Every run consumes your plan.
- Security plugins in the official marketplace: security-guidance (checks Claude's
  changes while it works), Claude Security (multi-agent vulnerability scan, patches).

### Context and memory
- `/context` (split of the window: system prompt, tools, MCP, skills, memory files,
  messages), `/skill-doctor` (context cost and usage per skill), `/usage` (what consumes
  the plan limits, per skill, subagent, plugin, MCP server).
- `/compact [instructions]`, `/rewind` or `Esc Esc` (restore code, conversation or both;
  "Summarize up to here"), `/fork` (copy the conversation to a background session),
  `/clear`. Rule of thumb: one task, one session.
- CLAUDE.md levels: managed (organisation), `~/.claude/CLAUDE.md` (user),
  `./CLAUDE.md` or `./.claude/CLAUDE.md` (project, Git), `./CLAUDE.local.md` (local,
  gitignored). Stay under about 200 lines; write verifiable instructions. HTML comments
  are stripped before reaching Claude. `.claude/rules/*.md` with `paths:` frontmatter
  load only for matching files. Claude Code reads AGENTS.md if there is no CLAUDE.md.
- Auto memory: Claude saves preferences, corrections, context under
  `~/.claude/projects/<repo>/` (shared across worktrees of the repo); `MEMORY.md` is the
  index, loaded every session up to 200 lines; plain Markdown; `/memory` lists files and
  toggles auto memory.
- `/doctor` (full check, can fix; suggests trimming CLAUDE.md), `/doctor prompt-audit`
  (outdated, missing-file or conflicting instructions; proposes, does not apply),
  `claude doctor` from the shell.

### Parallel work
- Subagent isolates context, same files. Worktree isolates files. Background sessions
  isolate the terminal.
- `claude --worktree <name>`: worktree in `.claude/worktrees/<name>` on branch
  `worktree-<name>`; `claude --worktree "#123"` from a PR. `.worktreeinclude` lists
  gitignored files to copy (`.env`). Worktrees start from the remote main by default;
  `{"worktree": {"baseRef": "head"}}` starts from local HEAD. Add `.claude/worktrees/` to
  `.gitignore`.
- `/goal <condition>`: Claude keeps working turn after turn until a separate evaluator
  judges the condition met; the evaluator only sees what Claude showed in the
  conversation, so the condition must name a check Claude runs ("npm test exits with code
  0"). `/goal` shows state, `/goal clear` cancels.
- `claude --bg --name <name> "<prompt>"`: background session; moves itself into an
  isolated worktree before editing. `claude agents`: agent view grouped by state
  (Working, Needs input, Completed); `Space` preview and answer, `Enter` to open, `←` on
  an empty prompt back to the list (or from any session to background it), `Ctrl+T` pins.
  Finished sessions commit, push the branch and may open a draft PR; the `#N` label on
  the row is coloured by state (yellow checks/review, green ready, purple merged).
  `claude attach | logs | stop | rm <id>`.
- Subagent frontmatter `isolation: worktree` gives each instance a temporary worktree,
  removed if unchanged.
- Each parallel session consumes quota like a normal one.

### Code review
- `/code-review` (alias `/review`): reviews unpushed commits plus uncommitted changes
  for correctness bugs, as a background subagent. Targets: file, PR number, branch,
  range (`main...feat/albums-api`). Effort: `/code-review low|high ...`; without a level
  it reuses the last one typed, even from a previous session. `--fix` applies fixes
  (not undone by `/rewind`, use Git), `--comment <PR>` posts on the PR. Reads CLAUDE.md,
  not REVIEW.md.
- `REVIEW.md` in the repo root customises Code Review on GitHub (Team and Enterprise
  plans, paid per review): what counts as Important, Nit cap, what to skip, what to
  always check. Severities: Important, Nit, Pre-existing. `@claude review` on a PR.
- `/code-review ultra [note|branch]`: multi-agent review in the cloud with a
  false-positive verification pass; default compares current branch with main including
  uncommitted changes; can post on a github.com PR; `--fix`. Needs a claude.ai account
  (on Bedrock, Vertex, Foundry it falls back to a local review). `claude ultrareview`
  for scripts and CI.

### Other news (October 2026)
- `/fork`, `/cd` (move the session to another folder), artifacts and `/design`, desktop
  app (built-in browser, `/diff` panel, `/resume` a CLI session), Claude in Chrome and
  computer use, routines (cloud agents on a schedule or GitHub event), `claude plugin eval`.
- Stay current: `code.claude.com/docs/en/whats-new` (weekly digest),
  `code.claude.com/docs/en/changelog`.

## B. Re-verified on 17 October 2026

Full detail with source URLs: `FACTS-verified.md`. Latest release at the time of
writing: v2.1.302 (16 October 2026). A May 2026 book matches about v2.1.128-v2.1.158.
These points CORRECT or EXTEND part A and the first edition:

- **Install.** Native installer recommended (auto-updates). Also Homebrew
  (`brew install --cask claude-code`, no auto-update, `brew upgrade claude-code`),
  WinGet, signed apt/dnf/apk repos. npm (`npm install -g @anthropic-ai/claude-code`) is
  still documented as an advanced option, not deprecated, and needs **Node.js 22+**; it
  installs the same native binary. Never `sudo npm install -g`. Requirements: macOS 13+,
  Windows 10 1809+, Ubuntu 20.04+, Debian 10+, 4 GB RAM. `claude doctor` is read-only;
  `/doctor` (alias `/checkup`) is an in-session checkup that can fix things. Channel
  setting `autoUpdatesChannel` (`latest` default, `stable`), also in `/config`.
- **Auth.** The free claude.ai plan does not include Claude Code. `/login`, `/logout`;
  shell `claude auth login|logout|status`. A set and approved `ANTHROPIC_API_KEY` beats
  the subscription (check with `/status`). `claude setup-token` for CI. Vertex AI is now
  called "Google Cloud's Agent Platform" in the docs (env var unchanged).
- **Commands.** `/cost` and `/stats` are aliases of `/usage`. `/status` opens Settings on
  the Status tab. `/config key=value` works. `/clear` aliases `/reset`, `/new`.
  `/plan [description]` exists and enters Plan Mode. `/rewind` aliases `/checkpoint`,
  `/undo`. `/resume` alias `/continue`. `/btw` asks a side question outside the history.
  `/output-style` is back (Default, Proactive, Concise, Explanatory, Learning).
  `/review` is an alias of `/code-review`; `/ultrareview` of `/code-review ultra`.
  Removed: Ultraplan (v2.1.222), `/vim` (use `/config` > Editor mode), `/pr-comments`.
- **`/agents` wizard removed (v2.1.198, 1 July 2026).** `/agents` now only prints a
  reminder. Create subagents by asking Claude ("crea un subagent in .claude/agents/...")
  or by writing `.claude/agents/<name>.md` yourself. Screenshots of the old wizard are
  obsolete.
- **Subagents** (`.claude/agents/`, `~/.claude/agents/`, plugin `agents/`). Required
  frontmatter: `name`, `description`. Optional: `tools`, `disallowedTools`, `model`
  (`sonnet`, `opus`, `haiku`, `fable`, full ID, `inherit`), `permissionMode`, `maxTurns`,
  `skills`, `mcpServers`, `hooks`, `memory`, `background`, `effort`, `isolation: worktree`,
  `color`. Built-ins: Explore (read-only), Plan (read-only, used by plan mode),
  general-purpose. The Task tool was renamed `Agent` (v2.1.63). **Subagents run in the
  background by default** in interactive sessions; `Ctrl+B` backgrounds a running task,
  `/tasks` lists them. `/subtask` spawns a forked subagent that inherits the conversation.
  Nesting: by default a subagent can spawn subagents up to **three** layers below the
  main conversation (v2.1.219+; it was five in v2.1.172-v2.1.216);
  `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` changes it, `1` turns nesting off. (Corrects
  FACTS-verified.md section 7, re-checked on sub-agents.md 17 October 2026.)
- **Custom commands merged into skills.** `.claude/commands/deploy.md` and
  `.claude/skills/deploy/SKILL.md` both create `/deploy`; command files keep working,
  skills are preferred for new work; a skill wins a name clash; subfolders namespace
  (`.claude/commands/frontend/component.md` is `/frontend:component`). Skill frontmatter:
  `name`, `description`, `when_to_use`, `argument-hint`, `arguments`,
  `disable-model-invocation`, `user-invocable`, `allowed-tools`, `model`, `effort`,
  `context: fork` (runs in the background by default since v2.1.218), `agent`, `paths`,
  `hooks`. Substitutions `$ARGUMENTS`, `$ARGUMENTS[N]`, `$N`, `${CLAUDE_SKILL_DIR}`.
  `` !`command` `` injects shell output before the prompt reaches Claude. `/skills` lists
  skills, `/reload-skills` rescans. Locations: `~/.claude/skills/`, `.claude/skills/`,
  plugin `skills/`.
- **Plan Mode.** `Shift+Tab`, `/plan`, `claude --permission-mode plan`, or
  `permissions.defaultMode: "plan"`. Claude reads and explores, does not edit until you
  approve; approval options "Yes, and use auto mode", "Yes, manually approve edits",
  "No, keep planning"; `Ctrl+G` opens the plan in your editor. Research goes to the
  built-in Plan subagent. `opusplan` alias: Opus while planning, Sonnet to execute.
- **Permission modes.** Auto default for interactive sessions: Pro/Max/Team since
  v2.1.228 (11 August 2026), every plan and provider since v2.1.283-284 (late
  September). `claude -p` still starts in `default`. The old default is labelled
  **Manual** (`--permission-mode manual` is an alias). `Shift+Tab` from auto goes to
  Manual, then Accept edits, then Plan. `"auto"` and `"bypassPermissions"` as
  `defaultMode` only take effect in `~/.claude/settings.json`, not in project settings.
  `--dangerously-skip-permissions` equals `bypassPermissions`.
- **Tools changed.** On macOS, Linux and WSL native builds the `Glob` and `Grep` tools
  are absent by default: Claude searches through `Bash` (embedded `bfs`/`ugrep`). The task
  list tools (`TaskCreate`, `TodoWrite`) are not offered on newer models (Opus 4.8+,
  Sonnet 5+, Fable); `CLAUDE_CODE_ENABLE_TODO_TOOLS=1` restores them. `Ctrl+T` toggles
  Claude's task checklist in the UI. Write tool tables accordingly: `Read`, `Edit`,
  `Write`, `Bash` (search included), `WebSearch`, `WebFetch`, `Agent`, MCP tools; mention
  `Grep`/`Glob` as present on some setups.
- **Keyboard.** `#` memory shortcut removed (December 2025): ask Claude to edit
  CLAUDE.md, or use `/memory`. The `&` prefix is undocumented: do not present it. Use
  `claude --bg`, `/background` (`/bg`) or `claude --cloud "<task>"` instead. `!` runs a
  shell command and Claude now replies to its output. `Esc Esc` on an empty prompt opens
  rewind. `Ctrl+O` transcript, `Ctrl+R` history search, `Ctrl+G` external editor,
  `Ctrl+B` background, `Shift+Enter` newline in most terminals (`/terminal-setup` for
  the rest).
- **Models.** `opus` = Opus 5.5 (default since v2.1.280, 22 September 2026), `sonnet` =
  Sonnet 5.5, `haiku` = Haiku 5.5, `fable` = Fable 5.1 (most capable, never default),
  all with 1M context. Effort `low`, `medium`, `high`, `xhigh`, `max` (session only);
  **default `medium`** on the 5.5 models; thinking cannot be switched off on them.
  `ultrathink` still works for one turn; "think hard" is not a keyword. `/fast` toggles
  fast mode.
- **CLAUDE.md.** Managed policy paths per OS; `@path` imports (up to 4 hops); `/init`
  generates a starter file; `.claude/rules/` without `paths:` loads at launch, with
  `paths:` when a matching file is read or edited; `~/.claude/rules/` for user rules.
  AGENTS.md is read natively since v2.1.277 when no CLAUDE.md exists (configurable in
  `/config` > Project instructions). Auto memory lives in
  `~/.claude/projects/<project>/memory/` (MEMORY.md index, first 200 lines or 25KB load).
- **Plugins.** Official marketplace `claude-plugins-official` is added automatically on
  first run; community `claude-community`; `anthropics/claude-code` is only a demo
  marketplace. **Superpowers is in the official marketplace:**
  `/plugin install superpowers@claude-plugins-official` (or
  `/plugin marketplace add obra/superpowers-marketplace` then
  `/plugin install superpowers@superpowers-marketplace`). `/plugin` tabs: Discover,
  Installed, Marketplaces. `claude plugin validate`, `claude plugin eval`, `claude plugin
  init`. Claude Mods (JavaScript hook modules, v2.1.287) exist; mention at most.
- **Headless.** `claude -p "query"`, piping, `--output-format text|json|stream-json`,
  `--json-schema`, `--allowedTools "Bash(git diff *),Read"`, `--continue`, `--resume <id>`,
  `--max-turns`, `--max-budget-usd`, `--permission-mode dontAsk`, `--bare` (skips hooks,
  skills, plugins, MCP, memory, CLAUDE.md; recommended for scripts).
- **GitHub.** `/install-github-app` (github.com only, needs repo admin and `gh`);
  `@claude` in PRs and issues via `anthropics/claude-code-action@v1`; Code Review for
  GitHub (Team/Enterprise, posts ranked inline comments and a check run, never approves
  or blocks; `@claude review` re-runs; REVIEW.md); `claude ultrareview [target]` with
  `--json`, `--timeout`, `--post`; ultrareview is a research preview, 3 free runs on
  Pro/Max then usage credits.
- **IDE and apps.** VS Code extension `anthropic.claude-code` (bundles its own CLI;
  recommended in VS Code and Cursor). JetBrains plugin "Claude Code [Beta]" (needs the
  CLI installed). Desktop app with a Code tab (macOS, Windows, Linux beta), `/desktop`
  hands a CLI session over. Cloud sessions at claude.ai/code, `claude --cloud`,
  `claude --teleport`.
