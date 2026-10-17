# Claude Code: verified facts sheet (state as of 2026-10-17)

How this was verified: every page below was downloaded on 2026-10-17 from the official docs index `https://code.claude.com/docs/llms.txt` (HTTP 200), using the Markdown rendition each index entry links to (`https://code.claude.com/docs/en/<page>.md`). Citations give the human URL (`https://code.claude.com/docs/en/<page>`). The changelog is the docs changelog page, which is generated from `anthropics/claude-code/CHANGELOG.md`. The latest release is **v2.1.302 (October 16, 2026)**. The What's new weekly digest stops at **Week 37 (September 7-11, 2026, v2.1.263-v2.1.269)**. No week 31 digest exists, and nothing has been published after week 37. Changes after September 11 therefore come from the changelog only.

For orientation, a book written in May 2026 matches roughly v2.1.128 (May 4) to v2.1.158 (May 30). Everything from v2.1.159 (May 31) onward is new.

Pages fetched: setup, quickstart, troubleshoot-install, troubleshooting, authentication, google-vertex-ai, commands, skills, sub-agents, permission-modes, headless, cli-reference, tools-reference, interactive-mode, model-config, memory, output-styles, plugins/overview, plugins/anthropic-marketplaces, plugins/cli-reference, github-actions, code-review, code-review-customize, code-review-pull-requests, ultrareview, vs-code, jetbrains, desktop, claude-code-on-the-web, platforms, changelog, whats-new (index + weekly pages w22-w37). Every fetch returned 200, and nothing below is UNVERIFIED except where it is marked so. For question 12 I also used `raw.githubusercontent.com` for obra/superpowers and for anthropics/claude-plugins-official.

---

## 1. Installation

Source: https://code.claude.com/docs/en/setup (unless noted)

- **Recommended: Native Install.**
  - macOS, Linux, WSL: `curl -fsSL https://claude.ai/install.sh | bash`
  - Windows PowerShell: `irm https://claude.ai/install.ps1 | iex`
  - Windows CMD: `curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd`
  - "Native installations automatically update in the background."
- **Other supported methods:**
  - Homebrew: `brew install --cask claude-code`. This cask tracks the stable channel; `claude-code@latest` tracks the latest channel. Homebrew installs do not auto-update. Use `brew upgrade claude-code`.
  - WinGet: `winget install Anthropic.ClaudeCode`. No auto-update; use `winget upgrade Anthropic.ClaudeCode`.
  - Signed apt, dnf, and apk repositories, each with stable and latest channels. Updates come through the system package manager.
  - Opt-in auto-upgrade for Homebrew and WinGet: `CLAUDE_CODE_PACKAGE_MANAGER_AUTO_UPDATE=1`.
- **npm is still documented and is NOT marked deprecated.** It appears under "Advanced installation options > Install with npm":
  - `npm install -g @anthropic-ai/claude-code`. It requires **Node.js 22 or later**. On an older Node.js you get only an `EBADENGINE` warning.
  - The npm package installs the same native binary through per-platform optional dependencies, such as `@anthropic-ai/claude-code-darwin-arm64`. "The installed `claude` binary does not itself invoke Node."
  - Upgrade with `npm install -g @anthropic-ai/claude-code@latest`, not `npm update -g`. Never use `sudo npm install -g`.
  - The word "deprecated" does not occur on setup, troubleshoot-install, or quickstart.
- **Node requirement:** none for the native installer, Homebrew, WinGet, or the package managers. Node 22+ applies to npm only.
- **System requirements:**
  - macOS 13.0+, Windows 10 1809+ / Server 2019+, Ubuntu 20.04+, Debian 10+, Alpine 3.19+.
  - 4 GB+ RAM, x64 or ARM64.
  - Git for Windows is optional. Without it, Claude Code uses the PowerShell tool.
- **Verify:** run `claude --version`, which prints e.g. `2.1.211 (Claude Code)`. Then run `claude doctor`.
- **`claude doctor`** is a CLI subcommand that "prints read-only installation and settings diagnostics without starting a session". It also reports the result of the last auto-update attempt.
  - `/doctor` is different. It is an in-session bundled skill that runs a setup checkup and can apply fixes (alias `/checkup`).
  - Sources: setup; https://code.claude.com/docs/en/troubleshooting; https://code.claude.com/docs/en/cli-reference
- **`claude update`** applies an update immediately. It reports `Successfully updated from <old> to version <new>` or `Claude Code is up to date (<version>)`.
- **`claude install [version|stable|latest]`** installs or reinstalls the native binary. Source: cli-reference.
- **Auto-updates:**
  - Claude Code checks at startup and periodically. An update takes effect on the next start.
  - Disable with `DISABLE_AUTOUPDATER=1` in the settings `env` block. `claude update` still works after that.
  - `DISABLE_UPDATES` blocks all update paths.
- **Release channels:**
  - The setting is `autoUpdatesChannel`: `"latest"` (default) or `"stable"`. Stable is "typically about one week old, skipping releases with major regressions".
  - You can also set it via `/config` > **Auto-update channel**.
  - `minimumVersion` sets a floor for updates.
  - The managed settings `requiredMinimumVersion` and `requiredMaximumVersion` stop Claude Code from starting outside a version range.
  - Install a channel or a version: `curl -fsSL https://claude.ai/install.sh | bash -s stable` or `... | bash -s 2.1.89`.

## 2. Authentication

Source: https://code.claude.com/docs/en/authentication

- **First run:** `claude` opens a browser login. If `ANTHROPIC_API_KEY` is set and you approve it, the login prompt is skipped.
- **Log out:** `/logout`. This also resets first-launch setup state.
- **`/login`** signs in. It is also how you renew a login: a warning appears when the login is within 3 days of expiry.
- **Account types:** Claude Pro/Max subscription, Teams/Enterprise, Claude Console, cloud providers, or a self-hosted "Claude apps gateway" (corporate SSO through `/login`).
  - The free claude.ai plan does not include Claude Code. Source: setup.
  - Console users can now sign in **without creating an API key** (requires v2.1.242+).
- **Shell equivalents** (source: cli-reference):
  - `claude auth login`, with `--email`, `--sso`, and `--console`.
  - `claude auth logout`.
  - `claude auth status`, which prints JSON, or text with `--text`.
- **CI token:** `claude setup-token` creates a one-year OAuth token. Use it as `CLAUDE_CODE_OAUTH_TOKEN`. Bare mode (`--bare`) does not read it.
- **Authentication precedence** (verbatim order):
  1. Cloud provider credentials, when `CLAUDE_CODE_USE_BEDROCK`, `CLAUDE_CODE_USE_VERTEX`, or `CLAUDE_CODE_USE_FOUNDRY` is set.
  2. `ANTHROPIC_AUTH_TOKEN`, sent as a Bearer header for LLM gateways.
  3. `ANTHROPIC_API_KEY`, sent as `X-Api-Key`.
     - In interactive mode you approve it once; the "Use custom API key" toggle in `/config` changes that choice later.
     - In `-p` mode the key is always used.
  4. `apiKeyHelper` script output.
  5. `CLAUDE_CODE_OAUTH_TOKEN`.
  6. Anthropic profile and federation credentials (`ant auth login`, `ANTHROPIC_PROFILE`).
  7. Subscription OAuth credentials from `/login`, which is the default for Pro, Max, Team, and Enterprise.
- **API key vs subscription:** if `ANTHROPIC_API_KEY` is set and approved, it beats your subscription. Run `unset ANTHROPIC_API_KEY`, then check `/status`.
- **Bedrock / Vertex / Foundry:** set the env vars before `claude`, or pick **3rd-party platform** at the login prompt. That option opens a setup wizard for Bedrock and Vertex AI.
  - **Naming change:** the docs now call Vertex AI **"Google Cloud's Agent Platform, formerly Vertex AI"**. The page URL is still `/google-vertex-ai` and the env var is still `CLAUDE_CODE_USE_VERTEX`. Source: https://code.claude.com/docs/en/google-vertex-ai
  - The commands `/setup-bedrock` and `/setup-vertex` exist. Source: commands.

## 3. Slash commands today

Source: https://code.claude.com/docs/en/commands (the "All commands" table). Dates come from https://code.claude.com/docs/en/changelog.

| Command | Status today / what it does |
|---|---|
| `/help` | Show help and available commands |
| `/clear [name]` | New conversation with empty context. A name labels the old one in `/resume`. Aliases `/reset`, `/new` |
| `/compact [instructions]` | Summarize the conversation to free context, with optional focus instructions |
| `/cost` | **Alias for `/usage`.** `/cost` and `/stats` were merged into `/usage` in v2.1.118 (April 2026) |
| `/usage` | Session cost, plan usage limits, and activity stats, including a breakdown of what counts against plan limits. `/cost` and `/stats` are aliases |
| `/status` | Opens Settings on the Status tab: version, model, account, connectivity. Works while Claude is responding |
| `/config [key=value ...]` | Settings UI. `key=value` sets a setting directly, e.g. `/config model=sonnet`, and also works in `-p` mode. Alias `/settings` |
| `/model [model]` | Switch model and save it as the default for new sessions. Left/right arrows adjust effort. `s` switches for this session only |
| `/effort [level\|auto\|status\|ultracode [on\|off]]` | Levels `low` to `xhigh`, plus `max` (session-only) and `auto`. `ultracode` toggles dynamic-workflow orchestration |
| `/init` | Generate a starter `CLAUDE.md`. `CLAUDE_CODE_NEW_INIT=1` gives an interactive flow. Offers `/import` when it finds Codex or Gemini config |
| `/memory` | Edit CLAUDE.md files, toggle auto memory, view auto-memory entries |
| `/context [all]` | Colored-grid view of context usage |
| `/permissions` | Manage allow/ask/deny rules, recent auto-mode denials, and auto-mode classifier rules. Alias `/allowed-tools` |
| `/agents` | **CHANGED: the interactive wizard was REMOVED in v2.1.198 (July 1, 2026).** It now only prints a reminder to ask Claude to create subagents or to edit `.claude/agents/` directly. "On v2.1.197 and earlier, opens an interactive interface" |
| `/hooks` | View hook configurations |
| `/mcp [reconnect\|enable\|disable ...]` | Manage MCP servers and OAuth. `reconnect all` was added in v2.1.284 |
| `/plugin [subcommand]` | Plugin menu, or subcommands such as `list`, `install`, `enable`, `disable` |
| `/skills` | List skills. Filter, sort by tokens (`t`), cycle visibility |
| `/rewind` | Rewind code and/or conversation to a checkpoint, or summarize from a message. Aliases `/checkpoint`, `/undo`. Esc Esc on an empty prompt opens it |
| `/resume [session]` | Resume by ID or name, or open the picker. Background sessions are marked `bg`. Alias `/continue` |
| `/fork [prompt]` | **CHANGED MEANING (v2.1.212, July 17, 2026):** copies the conversation into a new **background session**, and you keep working in the current one. On v2.1.161-v2.1.211, `/fork` started a forked subagent; that behaviour is now `/subtask` |
| `/cd <path>` | **NEW (v2.1.169, June 2026):** move the session to a new working directory and keep the conversation |
| `/goal [condition\|clear]` | Claude keeps working across turns until a condition is met. Added in v2.1.139 (May 2026) |
| `/code-review [low\|medium\|high\|xhigh\|max\|ultra] [--fix] [--comment] [--max-findings n\|all\|default] [pr#\|branch\|path]` | Bundled skill. Reviews the diff or a PR for correctness bugs. `--fix` applies findings, `--comment` posts them to GitHub or GitLab, `ultra` runs a cloud ultrareview |
| `/review` | **Now an alias of `/code-review`** (since v2.1.223, August 6, 2026). Before that it was a separate single-pass PR review |
| `/doctor [prompt-audit [path]]` | **Now a bundled skill:** a setup checkup that diagnoses and fixes, alias `/checkup`. `prompt-audit` (v2.1.283+) audits CLAUDE.md, skills, and agents for outdated prompting |
| `/sandbox` | Toggle sandbox mode (supported platforms only) |
| `/statusline` | Configure the status line. Describe what you want, or auto-configure from your shell prompt |
| `/terminal-setup` | Installs a Shift+Enter newline binding (VS Code, Cursor, Devin Desktop, Alacritty, Zed). Option+Enter setup for Apple Terminal, clipboard access for iTerm2 |
| `/add-dir <path>` | Add a working directory for file access. Most `.claude/` config isn't discovered from it |
| `/export [filename]` | Export the conversation as plain text |
| `/btw [question]` | Side question that is not added to the conversation history |
| `/output-style [style]` | **Re-added in v2.1.269 (September 11, 2026).** It was deprecated in v2.1.73 in favour of `/config`. It lists styles or switches to one. Built-in styles: Default, Proactive, Concise, Explanatory, Learning. Source: https://code.claude.com/docs/en/output-styles |
| `/plan [description]` | Enter plan mode from the prompt. A description starts the plan right away |

**Removed or renamed** (per the commands page and changelog):

- `/agents` wizard: removed in v2.1.198. The leftover menu entry was removed in v2.1.281.
- `/ultraplan`: "Removed. Use plan mode instead". The changelog for v2.1.222 (August 4, 2026) says "Removed ultraplan feature".
- `/vim`: removed in v2.1.92. Use `/config` > Editor mode.
- `/pr-comments`: removed in v2.1.91.
- `/review`: now an alias of `/code-review` (v2.1.223).
- `/ultrareview`: now an alias. "The preferred invocation is `/code-review ultra`".
- `/fork`: semantics changed (v2.1.212). `/subtask` is the new name for the old forked-subagent behaviour.
- `/cost` and `/stats`: aliases of `/usage` (v2.1.118).

**Other notable current commands** (from the same table):

- Session management: `/background` (`/bg`), `/subtask`, `/branch`, `/tasks`, `/schedule` (`/routines`), `/loop`, `/batch`, `/teleport` (`/tp`), `/remote-control` (`/rc`), `/desktop` (`/app`).
- Modes and models: `/fast`, `/advisor`, `/autocompact`, `/tui`, `/focus`.
- Code quality: `/simplify`, `/verify`, `/run`, `/security-review`.
- Workflows and research: `/workflows`, `/deep-research`.
- Other: `/import` (codex, gemini, cursor), `/recap`, `/insights`, `/artifacts`, `/design`, `/list-agents`, `/skill-doctor`, `/radio`.

## 4. Plan Mode

Source: https://code.claude.com/docs/en/permission-modes ("Analyze before you edit with plan mode")

- **How to enter it:**
  - Press `Shift+Tab` (cycle described in section 5).
  - Prefix a prompt with `/plan`.
  - Start in it: `claude --permission-mode plan`.
  - Make it the default: set `permissions.defaultMode: "plan"`. For VS Code, set `claudeCode.initialPermissionMode: "plan"`.
- **What it does:** Claude reads files, runs shell commands to explore, and writes a plan, but does not edit source until you approve.
  - When auto mode is available and `useAutoModeDuringPlan` is on (the default), the auto-mode classifier reviews planning shell commands instead of prompting you.
  - Otherwise, commands outside the read-only set prompt.
  - Research is delegated to the built-in **Plan** subagent.
- **Approval options:**
  - **Yes, and use auto mode** (or "Yes, auto-accept edits" when auto mode is unavailable).
  - **Yes, manually approve edits**.
  - **No, keep planning**.
  - `Ctrl+G` opens the plan in your editor.
  - `showClearContextOnPlanAccept` adds an "approve and clear context" option.
  - Accepting a plan also gives the session a generated title.
- `opusplan` model alias: Opus during plan mode, Sonnet for execution. Source: https://code.claude.com/docs/en/model-config
- **Ultraplan (cloud planning) is gone.** It was removed in v2.1.222. Source: commands, changelog.

## 5. Permission modes

Source: https://code.claude.com/docs/en/permission-modes

| Mode (config value) | Runs without asking |
|---|---|
| `default`, labelled **Manual** in the UI (`manual` is accepted as an alias) | Reads only |
| `acceptEdits` | Reads, file edits, common filesystem commands (`mkdir`, `touch`, `mv`, `cp`) |
| `plan` | Reads, plus classifier-approved commands when auto mode is available |
| `auto` | Everything, with background classifier safety checks |
| `dontAsk` | Reads in working dirs, read-only Bash, and pre-approved tools. Anything that would prompt is denied. Not in the Shift+Tab cycle |
| `bypassPermissions` | Everything (`--dangerously-skip-permissions`). Only for isolated containers or VMs |

- **IS AUTO THE DEFAULT? Yes, for interactive sessions.**
  - "With Claude Code v2.1.283 or later, auto mode is the built-in starting permission mode for interactive terminal and VS Code sessions." It applies on every plan and provider.
  - Timeline from the changelog and permission-modes page:
    - The built-in `auto` default first arrived in **v2.1.228 (August 11, 2026)** on macOS, Linux, and WSL, and in v2.1.233 (August 14) on native Windows, for **Pro, Max, and Team**. The Week 32 digest says "starting August 14".
    - v2.1.283 (September 25) extended it to third-party providers and telemetry-off sessions.
    - v2.1.284 (September 28) made it "every plan and provider".
  - On earlier versions the default was Manual.
  - Exceptions:
    - `claude -p` and the Agent SDK start in `default`. Exception: with v2.1.285+, sessions that don't fetch feature flags start in `auto`. v2.1.302 (October 16, 2026) moved third-party-provider and telemetry-off `-p` runs back to `default`.
    - HIPAA-configured orgs start in `default`.
    - `disableAutoMode: "disable"` forces `default`.
- **Starting-mode precedence:**
  1. The `--permission-mode` flag or `--dangerously-skip-permissions`.
  2. **`permissions.defaultMode`** in settings.
  3. The built-in default.
  - Note: `"auto"` and `"bypassPermissions"` in project `.claude/settings.json` or `.claude/settings.local.json` do NOT take effect. Put them in `~/.claude/settings.json`.
- **Shift+Tab cycle:**
  - From `auto`, the first press goes to `default`. Then `default` > `acceptEdits` > `plan`. Optional modes follow: `bypassPermissions` first, `auto` last.
  - Status bar labels: `⏸ manual mode on`, `⏵⏵ accept edits on`, `⏸ plan mode on`, `⏵⏵ auto mode on`, `⏵⏵ don't ask on`, `⏵⏵ bypass permissions on`.
  - `--allow-dangerously-skip-permissions` adds bypass to the cycle without starting in it.
- **Auto mode requirements:**
  - All plans.
  - Supported models on the Anthropic API: Opus 4.6+, Sonnet 4.6+, Haiku 5.5, or Fable.
  - On Bedrock, Agent Platform, and Foundry: Sonnet 5+, Opus 4.7+, Haiku 5.5, or Fable.
  - Admins can turn it off with `permissions.disableAutoMode: "disable"`.
- The `--enable-auto-mode` flag was removed in v2.1.111. Source: cli-reference.
- `/auto-mode-setup`, `claude auto-mode defaults`, `claude auto-mode config`, and `claude auto-mode reset` exist. Sources: commands, cli-reference.
- From a Bash permission prompt, **"Yes, and switch to auto mode"** is offered (v2.1.247+).

## 6. Custom slash commands vs skills

Source: https://code.claude.com/docs/en/skills

- **Merged:** "**Custom commands have been merged into skills.** A file at `.claude/commands/deploy.md` and a skill at `.claude/skills/deploy/SKILL.md` both create `/deploy` and work the same way. Your existing `.claude/commands/` files keep working."
  - Command files are "the older format and still work". They accept the same frontmatter except `name` and `paths`.
  - "Prefer a skill for new work."
  - When names clash, a skill beats a `.claude/commands/` file.
  - A command file in a subdirectory is namespaced: `.claude/commands/frontend/component.md` becomes `/frontend:component`.
- **Skill locations:**

  | Scope | Path |
  |---|---|
  | Enterprise | managed settings dir `.claude/skills/<name>/SKILL.md` |
  | Personal | `~/.claude/skills/<name>/SKILL.md` |
  | Project | `.claude/skills/<name>/SKILL.md` |
  | Nested | `<subdir>/.claude/skills/...`, invoked as `/apps/web:deploy` on name clash |
  | `--add-dir` directories | `.claude/skills/` inside them |
  | Plugin | `<plugin>/skills/<name>/SKILL.md`, invoked as `/plugin-name:skill-name` |
  | claude.ai account | synced skills, prefixed `anthropic-skills:` |

- **Frontmatter fields** (all optional; `description` recommended):
  - `name`, `description`, `when_to_use` (description plus when_to_use is truncated at 1,536 chars), `argument-hint`, `arguments` (named positional args).
  - `disable-model-invocation`, `user-invocable`.
  - `allowed-tools` (the grant clears at your next message), `disallowed-tools`.
  - `model` (applies for the rest of the turn; `inherit` allowed), `effort` (`low`..`max`).
  - `context: fork`, `agent` (the subagent type for the fork), `background` (with fork; default `true`; v2.1.218+).
  - `hooks`, `paths` (globs), `shell` (`bash` | `powershell`), `metadata`, `license`, `compatibility`.
  - Booleans accept yes/no/on/off/1/0 (v2.1.218+).
  - Only `name`, `description`, `license`, `compatibility`, `metadata`, and `allowed-tools` are valid in the Agent Skills spec used for claude.ai uploads and the Skills API.
- **`context: fork` now runs in the BACKGROUND by default:** "Before v2.1.218, forked skills always blocked the turn until they finished." Set `background: false` to wait. It does NOT inherit conversation history; use `/subtask` or a conversation fork for that.
- **Substitutions:**
  - `$ARGUMENTS`, `$ARGUMENTS[N]`, `$N` (0-based), `$name` (from `arguments`).
  - `${CLAUDE_SESSION_ID}`, `${CLAUDE_EFFORT}`, `${CLAUDE_SKILL_DIR}`, `${CLAUDE_PROJECT_DIR}`, `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}`.
  - If no placeholder takes the arguments, they are appended as `ARGUMENTS: <value>`.
- **`!` bash injection:** inline `` !`command` `` at line start or after whitespace, or a fenced ` ```! ` block for multiple lines.
  - It runs before the content reaches Claude, and the output replaces the placeholder.
  - Disable with `"disableSkillShellExecution": true`.
  - It never runs for skills synced from claude.ai (v2.1.228+).
  - The Bash tool's 2-minute timeout applies.
- **`@file` references:** the skills page confirms that Claude Code attaches the files that `@` references in a local skill name. Synced claude.ai skills don't do this; there `@` references reach Claude as literal text.
- `ultrathink` inside skill content requests deeper reasoning.
- **Bundled skills:**
  - `/doctor`, `/code-review`, `/batch`, `/debug`, `/loop`, `/claude-api`, `/simplify`, `/verify`, `/run`, and others.
  - Turn them off with `disableBundledSkills`.
  - `/reload-skills` rescans skill and command directories.
- `claude plugin init <name>` scaffolds a plugin at `~/.claude/skills/<name>/`. It loads as `<name>@skills-dir`. Source: https://code.claude.com/docs/en/plugins/cli-reference

## 7. Subagents

Source: https://code.claude.com/docs/en/sub-agents

- **Locations and priority:**
  1. Managed settings.
  2. `--agents` CLI JSON.
  3. `.claude/agents/` (project; walks up to the repo root; scanned recursively).
  4. `~/.claude/agents/` (user).
  5. Plugin `agents/`.
- **Frontmatter** (camelCase for multi-word fields; only `name` and `description` are required):
  - `name` (max 256 chars, no `:`), `description`.
  - `tools`, `disallowedTools`.
  - `model` (`sonnet`, `opus`, `haiku`, `fable`, a full ID such as `claude-opus-5-5`, or `inherit`).
  - `permissionMode` (`default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan`, `manual`).
  - `maxTurns`, `autoCompactWindow` (v2.1.296+).
  - `skills` (preload), `mcpServers`, `hooks`.
  - `memory` (`user` → `~/.claude/agent-memory/<agent>/`, `project` → `.claude/agent-memory/<agent>/`, `local` → `.claude/agent-memory-local/<agent>/`).
  - `background`, `omitClaudeMd`, `effort`.
  - `isolation: worktree` (temporary git worktree branched from the default branch; auto-cleaned if there are no changes).
  - `color`, `initialPrompt`, `experimental.cacheTtl`.
  - `hooks`, `mcpServers`, and `permissionMode` are ignored for plugin subagents.
- **`/agents` UI: REMOVED.** "Running `/agents` prints a reminder to ask Claude or edit `.claude/agents/` and `~/.claude/agents/` directly. On Claude Code v2.1.197 and earlier, `/agents` opens an interactive wizard". The changelog for v2.1.198 (July 1, 2026) says "Removed the `/agents` wizard". The documented way to create one now is to ask Claude ("Create a personal code-improver subagent in ~/.claude/agents/ ...") or write the file by hand.
- **Built-in subagents:**
  - **Explore**: read-only, uses the main model. When the main model is Fable, it runs on the Opus alias with a subscription. Thoroughness: quick, medium, very thorough. Starts without CLAUDE.md.
  - **Plan**: read-only research during plan mode. Starts without CLAUDE.md.
  - **General-purpose**: all tools.
  - Others: `claude` (catch-all, and the default for background sessions), `statusline-setup` (Sonnet), `claude-code-guide` (Haiku).
  - `CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS=1` removes Explore and Plan (v2.1.198+).
- **Tool name:** "In version 2.1.63, the Task tool was renamed to Agent." `Task(...)` still works as an alias.
- **Background by default:**
  - In interactive sessions "fork mode" is on by default (Week 33 digest, August 2026). Subagents Claude spawns run in the background, and Claude can't ask for foreground.
  - Background subagents surface permission prompts in the main session.
  - Ctrl+B backgrounds a running task. `/tasks` lists them. `Ctrl+X Ctrl+K` stops all background subagents.
  - v2.1.302 (October 16) turned fork subagents on by default in `-p`, the SDK, Desktop, and VS Code too.
- Subagents can spawn their own subagents. Background chains are capped at five levels (Week 24 digest).
- `/subtask <task>` spawns a forked subagent that inherits the full conversation.
- `/list-agents` (alias `/peers`) lists agents and sessions Claude can message.

## 8. Headless / print mode

Sources: https://code.claude.com/docs/en/headless, https://code.claude.com/docs/en/cli-reference

- `claude -p "query"` (or `--print`). Piping works: `cat logs.txt | claude -p "explain"`.
  - The docs now describe this as "using the Agent SDK via the CLI".
  - Exit code is 0 on success and non-zero on failure.
- `--output-format text|json|stream-json`.
  - `json` includes `result`, `session_id`, `total_cost_usd`, and a per-model cost breakdown.
  - Use `--json-schema '<schema>'` with `--output-format json`; the result appears in `structured_output`.
  - Token streaming: `--output-format stream-json --verbose --include-partial-messages`.
  - `--input-format stream-json` is available for input.
- `--allowedTools` (also `--allowed-tools`) uses permission-rule syntax, e.g. `--allowedTools "Bash(git diff *),Bash(git log *),Read"`. The space before `*` matters.
  - `--disallowedTools` and `--tools` (restrict the built-in set) also exist.
- `--continue` / `-c` continues the most recent conversation in the current directory. With v2.1.257+ it can open a finished background session.
- `--resume` / `-r <id|name>`. Example: `session_id=$(claude -p "Start a review" --output-format json | jq -r '.session_id')`, then `claude -p "Continue that review" --resume "$session_id"`. `--fork-session` gives a new ID when resuming.
- **`--bare`** skips hooks, skills, plugins, MCP, auto memory, and CLAUDE.md for fast scripted runs. It "is the recommended mode for scripted and SDK calls, and will become the default for `-p` in a future release."
- Other print-mode flags:
  - `--max-turns`, `--max-budget-usd`, `--permission-mode dontAsk` (CI allowlists), `--permission-prompt-tool`, `--permission-prompts none`, `--no-session-persistence`.
  - `--safe-mode`: all customizations off, for troubleshooting. Added in the Week 24 digest.
  - `--restricted`: for evaluation harnesses on shared machines. Week 35 digest.
- Default permission mode for `-p`: `default` (see section 5).

## 9. Keyboard shortcuts

Source: https://code.claude.com/docs/en/interactive-mode

- `Shift+Tab` cycles permission modes. On some Windows setups the key is `Alt+M`.
- `Esc` interrupts Claude or closes a dialog.
- `Esc` + `Esc` clears the input draft when there is text. **On an empty prompt it opens the rewind menu** (checkpoints).
- `Ctrl+O` toggles the transcript viewer, which shows tool usage, timestamps, the model per message, and thinking in verbose view.
- `Ctrl+R` runs a reverse search of command history.
- `Ctrl+G` (or `Ctrl+X Ctrl+E`) opens the prompt in your external editor.
- `Ctrl+B` backgrounds running Bash commands and agents. tmux users press it twice.
- `Ctrl+T` toggles Claude's task checklist.
- `Ctrl+S` stashes or restores the prompt.
- `Ctrl+X Ctrl+K` stops all background subagents.
- `Ctrl+Enter` / `Ctrl+X Ctrl+S` sends queued messages now (v2.1.275+).
- `Option/Alt+P` switches model. `Option/Alt+T` toggles thinking, with no effect on Opus 5.5, Sonnet 5.5, Haiku 5.5, or Fable. `Option/Alt+O` toggles fast mode.
- Multiline input: `\`+Enter, `Shift+Enter` (native in iTerm2, WezTerm, Ghostty, Kitty, Warp, Apple Terminal, Windows Terminal), `Ctrl+J`, or `Option+Enter`.
- **`!` prefix** is shell mode. It runs the command, adds the output, **and Claude now responds to it**. Before Week 26 (June 2026) Claude did not reply.
- **`@`** triggers file path autocomplete. With cross-session messaging (v2.1.232+), `@` plus a letter also suggests your other live sessions.
- **`#` memory shortcut: REMOVED.** It was removed in **v2.0.70 (December 15, 2025)**: "Removed # shortcut for quick memory entry (tell Claude to edit your CLAUDE.md instead)". It is absent from the current shortcuts table. Source: changelog.
- **`&` background prefix: not documented on any current page.** The changelog for v2.0.45 (November 18, 2025) added "Send background tasks to Claude Code on the web by starting a message with `&`". The current docs instead document:
  - `claude --cloud "<task>"` (`--remote` is a deprecated alias) to start a cloud session.
  - `/background` (`/bg`) or `claude --bg` for local background agents.
  - UNVERIFIED whether `&` still works. Do not present it as a current feature.
- Other prefixes: `/` for commands and skills; `:` for emoji shortcodes (v2.1.217+); `?` on empty input for shortcut help.
- The `/vim` command was removed. Vim editor mode lives in `/config` > Editor mode. Source: commands.

## 10. Models

Source: https://code.claude.com/docs/en/model-config, plus changelog entries.

- **Current models and aliases (Anthropic API):**
  - `opus` = **Opus 5.5** (`claude-opus-5-5`). Default since v2.1.280, September 22, 2026. 1M context, $4/$20 per MTok.
  - `sonnet` = **Sonnet 5.5** (`claude-sonnet-5-5`). Since v2.1.284, September 28, 2026. 1M context, $2/$10.
  - `haiku` = **Haiku 5.5** (`claude-haiku-5-5`). Since v2.1.293, October 7, 2026. 1M context, $0.10/$0.50, more above 100K-token prompts.
  - `fable` = **Fable 5.1** (`claude-fable-5-1`). Since v2.1.257, September 1, 2026. $10/$50.
  - `best` resolves to Fable where available, otherwise Opus.
  - Also `sonnet[1m]`, `opus[1m]`, `opusplan`, and `default`.
- **Fable models:**
  - Fable 5 was introduced in v2.1.170 (June 9, 2026) as "a Mythos-class model that we've made safe for general use".
  - Fable is "the most capable" model but is never the default. Select it with `/model fable`.
  - It can bill to usage credits.
  - The `/advisor` tool can use Fable as a second-opinion model.
- **Default model (`default`):**
  - **Opus 5.5** for Pro, Max, Team, Enterprise, the Anthropic API, Claude Platform on AWS, Bedrock, and Agent Platform.
  - **Sonnet 4.5** on Microsoft Foundry.
  - v2.1.280 also "Changed the default model on Pro and Team Standard plans from Sonnet to Opus".
  - Earlier defaults during June-September 2026:
    - Opus 4.8 from v2.1.154 (late May).
    - Sonnet 5 for Pro and Team Standard from v2.1.197 (June 30).
    - Opus 5 from v2.1.219 (July 24).
- **Provider differences in alias resolution:**
  - Bedrock and Agent Platform: `opus` → Opus 5.5, `sonnet` → Sonnet 4.5, `haiku` → Haiku 4.5.
  - Foundry: Opus 4.6, Sonnet 4.5, Haiku 4.5.
  - Pin a specific model with `ANTHROPIC_DEFAULT_OPUS_MODEL` and similar variables.
- **Setting the model, in priority order:**
  1. `/model` during the session.
  2. `claude --model` at startup.
  3. `ANTHROPIC_MODEL`.
  4. The `model` setting.
  5. `ANTHROPIC_DEFAULT_MODEL`, the default for new sessions.
  - `fallbackModel` / `--fallback-model` accept chains of up to 3 models.
- **1M context:** Fable 5.1/5, Sonnet 5+, Haiku 5.5, and Opus 4.7+ run with 1M **by default**, with no `[1m]` suffix. Opus 4.6 and Sonnet 4.6 need the `[1m]` variant, and plan rules apply. `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` keeps sessions at 200K.
- **Effort levels:**
  - `low`, `medium`, `high`, `xhigh`, `max` on Fable, Opus 5.5, Sonnet 5.5, Haiku 5.5, Opus 5, Sonnet 5, Opus 4.8, and Opus 4.7.
  - Opus 4.6 and Sonnet 4.6 have no `xhigh`.
  - **Defaults:** `medium` on Opus 5.5, Sonnet 5.5, and Haiku 5.5. `xhigh` on Opus 4.7. `high` on everything else.
  - `max` is session-only.
  - Set effort with `/effort`, the `/model` arrows, `--effort`, `CLAUDE_CODE_EFFORT_LEVEL`, `effortLevel` / `modelSettings` in settings, or skill or subagent `effort` frontmatter.
  - `maxEffortLevel` caps effort.
  - `ultracode` is a separate toggle, not a level: Claude orchestrates dynamic workflows. Set it with `/effort ultracode`, `--effort ultracode`, or the `ultracode` setting.
- **`ultrathink`:** still supported. "Include `ultrathink` anywhere in your prompt to request deeper reasoning on that turn". Claude Code adds an in-context instruction, and the effort sent to the API is unchanged. "think", "think hard", and "think more" are **not** keywords.
- **Thinking:** cannot be turned off on Opus 5.5, Sonnet 5.5, Haiku 5.5, or Fable. They always use adaptive reasoning.
- **Fast mode:** `/fast` or `Option/Alt+O`. Since v2.1.219 it applies to Opus 5 and Opus 4.8. Source: changelog; https://code.claude.com/docs/en/fast-mode

## 11. CLAUDE.md and memory

Source: https://code.claude.com/docs/en/memory

- **Hierarchy (load order, broadest first):**

  | Scope | Location |
  |---|---|
  | Managed policy | macOS `/Library/Application Support/ClaudeCode/CLAUDE.md`; Linux/WSL `/etc/claude-code/CLAUDE.md`; Windows `C:\Program Files\ClaudeCode\CLAUDE.md` |
  | User | `~/.claude/CLAUDE.md` |
  | Project | `./CLAUDE.md` or `./.claude/CLAUDE.md` |
  | Local | `./CLAUDE.local.md` (add it to `.gitignore`) |

  - Files above the working directory load at launch. Subdirectory files load on demand.
- **Imports:** `@path/to/file`, relative to the importing file, or absolute, or `~`.
  - Recursion goes up to **4 hops**.
  - Escape spaces with `\`. Imports inside code spans or blocks are ignored.
  - External imports show a one-time approval dialog.
- **`.claude/rules/`:** `.md` files are discovered recursively.
  - Without `paths:` frontmatter, a rule loads at launch.
  - With `paths:` (a YAML list of globs, e.g. `"src/api/**/*.ts"`), it loads when Claude reads or edits a matching file.
  - User-level rules live in `~/.claude/rules/`.
- **AGENTS.md: now read natively (v2.1.277+, September 18, 2026).**
  - By default (`claude-md-or-agents-md`), Claude reads `AGENTS.md` only when there is no `CLAUDE.md` or `CLAUDE.local.md` in the working dir or above.
  - Change this in `/config` > **Project instructions**: `claude-md-and-agents-md`, `claude-md`, or `managed-only`.
  - The settings file form is `pluginConfigs["cc-plugin-agents-md@builtin"].options.instructionFiles`.
  - Not read: `AGENTS.local.md`, `AGENTS.override.md`, `.agents/`.
  - Importing `@AGENTS.md` from CLAUDE.md still works.
- **Auto memory:** on by default.
  - Stored at `~/.claude/projects/<project>/memory/`, shared across worktrees of one repo. It contains a `MEMORY.md` index plus topic files.
  - Memory types: `user`, `feedback`, `project`, `reference`.
  - Only the first 200 lines or 25KB of MEMORY.md load at session start.
  - Toggle it in `/memory`, with `autoMemoryEnabled`, or with `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`.
  - `autoMemoryDirectory` relocates it.
- **Recommended size:** "target under 200 lines per CLAUDE.md file". CLAUDE.md files up to 4 MiB load in full; larger ones are skipped. Imports do not reduce context cost.
- **Audit:** `/doctor prompt-audit` (v2.1.283+) checks CLAUDE.md, rules, skills, and agents for outdated or conflicting instructions.
- `/init` creates a starter file. `CLAUDE_CODE_NEW_INIT=1` gives the interactive flow.

## 12. Plugins and marketplaces

Sources: https://code.claude.com/docs/en/plugins/overview (the old `/docs/en/plugins` URL serves the same page), https://code.claude.com/docs/en/plugins/anthropic-marketplaces, https://code.claude.com/docs/en/plugins/cli-reference

- **Manifest:** `.claude-plugin/plugin.json` at the plugin root.
  - Components: `skills/`, `agents/`, `hooks/hooks.json`, `.mcp.json`, and a new **hooks module ("mods")**: JavaScript hooks that can draw panes and add commands. "Claude Mods" was added in v2.1.287.
  - Marketplace catalog: `.claude-plugin/marketplace.json`.
- **`/plugin`:** the menu has Discover, Installed, and Marketplaces tabs. Subcommands include `list`, `install`, `enable`, `disable`, and `marketplace add <owner>/<repo>`. `/reload-plugins` reloads them.
- **Shell commands** (`claude plugin`, alias `claude plugins`):
  - `init` (alias `new`), `install` (`--marketplace <source>` since v2.1.292), `uninstall`, `enable`, `disable`, `update`.
  - `list`, `details`, `configure`, `prune`, `eval`, `eval init`, `tag`, `test` (for mods).
  - `validate <path> [--strict] [--json]`: exit 0, 1, or 2.
  - `marketplace add|list|remove|update`.
- **`claude plugin eval`** (v2.1.269+) runs eval cases. By default it also runs a no-plugin baseline. `claude plugin eval init` drafts the cases and graders. Docs: https://code.claude.com/docs/en/plugin-evals
- **Official marketplace:**
  - Name **`claude-plugins-official`**, repo `anthropics/claude-plugins-official`. It is added automatically on the first interactive session.
  - Community: `claude-community` (repo `anthropics/claude-plugins-community`).
  - Demo: `claude-code-plugins` (repo `anthropics/claude-code`). "If a tutorial or an older set of instructions tells you to run `/plugin marketplace add anthropics/claude-code`, that adds the demo marketplace ... It isn't the official marketplace."
  - Install syntax: `/plugin install commit-commands@claude-plugins-official`.
- **Superpowers (obra/superpowers):** not mentioned anywhere in code.claude.com docs. Verified on GitHub:
  - It **is listed in the official marketplace**. `anthropics/claude-plugins-official/.claude-plugin/marketplace.json` has entry `"name": "superpowers"`, sourced from `https://github.com/obra/superpowers.git`, described as "brainstorming, subagent driven development with built in code review, systematic debugging, and red/green TDD ... how to author and test new skills".
  - The README (`https://github.com/obra/superpowers`) gives two install routes:
    - `/plugin install superpowers@claude-plugins-official` (official marketplace).
    - `/plugin marketplace add obra/superpowers-marketplace` then `/plugin install superpowers@superpowers-marketplace`.
- Other session flags: `--plugin-dir` (directories or `.zip` archives) and `--plugin-url`. Source: cli-reference.

## 13. GitHub integration

- **`/install-github-app`** installs the Claude GitHub App, sets the secret (`ANTHROPIC_API_KEY`, or `CLAUDE_CODE_OAUTH_TOKEN` for a subscription token), and opens a PR with the workflow files.
  - Works only with github.com. It needs admin on the repo and the `gh` CLI.
  - Source: https://code.claude.com/docs/en/github-actions, https://code.claude.com/docs/en/commands
- **`@claude` in PRs and issues** goes through the GitHub Action `anthropics/claude-code-action@v1`.
  - With no `prompt` input it runs in interactive mode and responds to the `@claude` trigger phrase in comments, reviews, and new issues. With a `prompt` input it runs in automation mode.
  - Example workflow: `examples/claude.yml`. Source: github-actions.
- **Code Review for GitHub** is a managed service for **Team and Enterprise** plans.
  - Multiple agents review each PR, then a verification step runs, then it posts inline comments ranked by severity and a "Claude Code Review" check run. It never approves or blocks.
  - Request a re-review with a top-level `@claude review` comment.
  - Customize with **`REVIEW.md`** at the repo root, plus optional subdirectory `REVIEW.md` files, along with `CLAUDE.md`.
  - The local `/code-review` command reads CLAUDE.md but **not** REVIEW.md.
  - Not available with ZDR, HIPAA, or CMEK.
  - Sources: https://code.claude.com/docs/en/code-review, https://code.claude.com/docs/en/code-review-customize, https://code.claude.com/docs/en/code-review-pull-requests
- **Ultrareview** (research preview) is a multi-agent cloud review.
  - Interactive: `/code-review ultra` (alias `/ultrareview`).
  - Non-interactive: **`claude ultrareview [target]`**, with `--json`, `--timeout <minutes>` (default 45), and `--post` to post findings as a PR comment.
  - Requires a claude.ai login. Not available on Bedrock, Agent Platform, Foundry, ZDR, or HIPAA.
  - 3 free runs on Pro and Max, then usage credits.
  - Sources: https://code.claude.com/docs/en/ultrareview, https://code.claude.com/docs/en/cli-reference, https://code.claude.com/docs/en/commands
- `/autofix-pr` starts a cloud session that watches the PR and pushes fixes. `--from-pr` filters `/resume` by PR. Sources: commands, cli-reference.

## 14. IDEs, desktop, web

- **VS Code extension** `anthropic.claude-code`, for VS Code 1.94.0+ and Cursor. "This is the recommended way to use Claude Code in VS Code."
  - It **bundles its own CLI** for the chat panel. Install the standalone CLI separately if you want `claude` in the integrated terminal.
  - Features: plan review, inline diffs, @-mentions with line ranges, mode indicator labels (Manual / Edit automatically / Plan / Auto / Bypass permissions), and Focus view (Week 32).
  - `claudeCode.initialPermissionMode` setting.
  - Source: https://code.claude.com/docs/en/vs-code; permission-modes.
- **JetBrains:** the "Claude Code [Beta]" plugin on JetBrains Marketplace (plugin 27310), for IntelliJ, PyCharm, Android Studio, WebStorm, PhpStorm, and GoLand.
  - It **does not bundle the CLI**: install `claude` first.
  - `Cmd/Ctrl+Esc` quick launch. `Cmd+Option+K` / `Alt+Ctrl+K` inserts `@file#L1-99` references. IDE diff viewer, selection sharing, diagnostics via `getDiagnostics`.
  - Source: https://code.claude.com/docs/en/jetbrains
- **Desktop app:** the Claude Desktop app has Chat, Cowork, and **Code** tabs.
  - Platforms: macOS universal, Windows x64 and ARM64, and **Linux beta** (apt/.deb on Ubuntu and Debian, since Week 27).
  - Features: parallel sessions with git isolation, a pane layout, built-in browser (Week 28), iOS Simulator pane (beta, Week 30), computer use, SSH sessions, and Dispatch.
  - `/desktop` (alias `/app`) or `claude --desktop` hands a CLI session to Desktop. Desktop can `/resume` CLI sessions (Week 35).
  - Source: https://code.claude.com/docs/en/desktop; commands; whats-new.
- **Claude Code on the web** is now documented as **"Claude Code in the cloud" / cloud sessions** at claude.ai/code.
  - Plans: Pro, Max, Team, and Enterprise premium or Chat+Claude Code seats.
  - Start from the browser, the mobile Code tab, Desktop (Cloud), the terminal with `claude --cloud "<task>"` (`--remote` is a deprecated alias), or Routines.
  - Pull a session to the terminal with `claude --teleport` or `/teleport` (`/tp`). Handoff from CLI to cloud is one-way.
  - Source: https://code.claude.com/docs/en/claude-code-on-the-web; https://code.claude.com/docs/en/platforms
- **Remote Control** (`/remote-control`, `claude remote-control`, `--rc`) steers a local session from a phone or browser. Source: cli-reference, commands.

## 15. Important changes June to October 2026 (for a practical book)

Sources: https://code.claude.com/docs/en/whats-new (weekly digests through Week 37) and https://code.claude.com/docs/en/changelog (through v2.1.302). Versions and dates are as printed there.

1. **New model generation, with Opus 5.5 as the default.**
   - Fable 5 (v2.1.170, June 9).
   - Sonnet 5, briefly the default (v2.1.197, June 30).
   - Opus 5 (v2.1.219, July 24).
   - Fable 5.1 (v2.1.257, September 1).
   - **Opus 5.5 becomes the default on all subscription plans** (v2.1.280, September 22).
   - Sonnet 5.5 (v2.1.284, September 28).
   - Haiku 5.5 (v2.1.293, October 7).
   - All of these run with 1M context natively, and the 5.5 models default to `medium` effort.
2. **Auto mode is the default permission mode.** Pro, Max, and Team from v2.1.228 (August 11; Windows v2.1.233, August 14). Every plan and provider from v2.1.283/v2.1.284 (September 25/28). The UI calls the old `default` mode "Manual".
3. **`/agents` wizard removed** (v2.1.198, July 1). Subagents are created by asking Claude or by editing `.claude/agents/*.md`.
4. **Subagents run in the background by default.** Background by default from Week 27; fork mode on by default in interactive sessions from Week 33; extended to `-p`, the SDK, Desktop, and VS Code in v2.1.302. Subagents can nest up to 5 levels (Week 24). Permission prompts from background subagents surface in the main session (Week 26).
5. **Session-branching commands reorganized** (v2.1.212, July 17): `/fork` copies to a background session; `/subtask` is a forked subagent; `/branch` switches into a conversation branch; `/background` (`/bg`) detaches the session. All of these feed into **agent view** (`claude agents`), the dashboard for background sessions.
6. **Code review consolidated.** `/code-review` (bundled skill with effort levels, `--fix`, `--comment`, `ultra`). `/review` became its alias (v2.1.223, August 6). `/ultrareview` became `/code-review ultra`, and `claude ultrareview` exists for CI.
7. **Ultraplan removed** (v2.1.222, August 4). Use plan mode.
8. **AGENTS.md read natively** (v2.1.277, September 18), controlled by `/config` > Project instructions.
9. **`/cd`** moves the session to another directory without losing the prompt cache (v2.1.169, Week 24).
10. **`/doctor` turned into a setup checkup that can fix problems** (Week 28, alias `/checkup`). `claude doctor` is the read-only CLI variant. `/doctor prompt-audit` was added in v2.1.283.
11. **Plugins grew up:**
    - `claude plugin eval` and `eval init` (v2.1.269, Week 37).
    - `claude plugin validate --json`.
    - **Claude Mods**, JavaScript hooks modules that can draw panes and add commands (v2.1.287, early October).
    - "You should know", a built-in mod.
    - `/plugin list` inline (Week 23).
12. **`/output-style` command returned** (v2.1.269). New built-in Concise style (Week 34) and Proactive style.
13. **Artifacts:** shareable live pages on claude.ai, in beta for Team and Enterprise (Week 25). They can call MCP connectors (Week 29). `/design` is a research preview (Week 34).
14. **Cross-session messaging:** sessions message each other, and `@` mentions sessions (Week 32/33). Self-hosted environments for cloud sessions are in public beta on Team and Enterprise (Week 32).
15. **Troubleshooting and isolation flags:** `--safe-mode` (Week 24) and `--restricted` (Week 35). `--bare` is recommended for scripts and "will become the default for `-p`".
16. **Smaller but book-relevant changes:**
    - Shell mode `!` now gets a Claude reply (Week 26).
    - `/rewind` can restore a conversation from before `/clear` (Week 26).
    - `claude mcp login` / `logout` (Week 26).
    - `/config key=value` (Week 25).
    - Permission rules match tool parameters, e.g. `Agent(model:opus)` (Week 25).
    - Idle compaction of 200K+ conversations after about 54 minutes idle (v2.1.299).
    - The task-tracking tools (`TaskCreate` etc. / `TodoWrite`) are no longer offered on newer models such as Opus 4.8+, Sonnet 5, and Fable (v2.1.233, refined in v2.1.268). `CLAUDE_CODE_ENABLE_TODO_TOOLS=1` restores them.
    - The `TaskOutput` tool was removed (v2.1.277).
    - Docs rename "Vertex AI" to "Google Cloud's Agent Platform".
    - Standalone Claude Design (claude.ai/design) closes by December 14, 2026 (notice in v2.1.302).

Earlier change worth knowing (April 2026, possibly already in the book): native macOS and Linux builds dropped the `Glob` and `Grep` tools from the default set in favour of embedded `bfs`/`ugrep` called through Bash (v2.1.117). This is still current per https://code.claude.com/docs/en/tools-reference: "Absent by default on macOS, Linux, and WSL".
