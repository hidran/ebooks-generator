# Appendix B. Troubleshooting

These are the problems I ran into while writing the book and recording the course, grouped by area. Each entry starts from what you see on screen, explains where it comes from and gives the fix, with a pointer to the chapter that covers it. When you ask Claude for help with an error, paste the exact output: "the deploy is broken" gets you guesses, the ten lines of the error get you a diagnosis.

## B.1 Start here: claude doctor and /doctor

```bash
claude --version
claude doctor
```

`claude doctor` runs from the shell without opening a session: it checks your installation and settings files (a `settings.json` with broken JSON shows up here) and suggests fixes without changing anything. Inside a session, `/doctor` (alias `/checkup`) runs a broader check and can fix things on its own; `/doctor prompt-audit` scans your instructions for missing files and conflicting rules, and proposes changes without applying them (Chapter 15). If everything comes back clean, look at the right panel:

| What you need to know | Where to look |
| --- | --- |
| Active account and authentication method | `/status` |
| Why a command goes through or gets blocked | `/permissions` |
| Registered hooks and their matchers | `/hooks` |
| MCP server status | `/mcp`, `claude mcp list` |
| Loaded instruction files | `/memory` |
| What's taking up the context | `/context` |
| What's eating into your plan limits | `/usage` |
| Installed plugins and available skills | `/plugin`, `/skills` |
| Background jobs and sessions | `/tasks`, `claude agents` |

## B.2 Installation and updates

### `claude: command not found` right after installing

Opening a new terminal almost always does it, because the shell rereads the `PATH`. Otherwise the binary's folder, `~/.local/bin` on macOS and Linux, isn't in your `PATH`:


```bash
echo $PATH | tr ':' '\n' | grep local
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
```

With bash, use `~/.bashrc`, then reopen the terminal (Chapter 1).

### The `claude` that starts isn't the one you installed

You installed with npm first and then with the native installer: the first binary in the `PATH` wins (`which -a claude` lists them). Remove the npm copy with `npm uninstall -g @anthropic-ai/claude-code`.

### `EACCES: permission denied` with npm, or root-owned files in `~/.claude`

npm is trying to write to a system folder: use the native installer, which doesn't need admin rights. If an old install with `sudo` left root-owned files in `~/.claude`, take them back:

```bash
sudo chown -R "$(whoami)" ~/.claude
```

::: {.callout .callout-warning}
[Warning]{.callout-title}

Never use `sudo npm install -g`: it creates root-owned files that block every later update.
:::

### `EBADENGINE` during `npm install -g`, or npm won't update

The package requires Node.js 22 or later, and with an older Node npm warns and carries on: check `node --version`. To update, use `npm install -g @anthropic-ai/claude-code@latest`, not `npm update -g`.

### Windows: `The token '&&' is not a valid statement separator` or `'irm' is not recognized`

Wrong shell: the first error is PowerShell running the CMD command, the second is the other way around. In PowerShell the command is `irm https://claude.ai/install.ps1 | iex`.

### Windows: `.sh` scripts don't run, or Claude can't find Git Bash

Without Git for Windows, Claude Code uses PowerShell, where a `.sh` script won't run. Install it; if Git Bash still isn't found, set the path in `%USERPROFILE%\.claude\settings.json`:

```json
{
  "env": {
    "CLAUDE_CODE_GIT_BASH_PATH": "C:\\Program Files\\Git\\bin\\bash.exe"
  }
}
```

### Your version is old, or the latest one has a regression

The native installer updates itself on the next restart; `claude update` updates right away. Homebrew and WinGet installs have to be updated by hand (`brew upgrade claude-code`, `winget upgrade Anthropic.ClaudeCode`). If a regression is costing you, pick the `stable` channel in `/config`: it ships about a week later and skips releases with serious problems.

## B.3 Authentication and accounts

### You're paying per use even though you have a subscription

There's an `ANTHROPIC_API_KEY` in your shell, maybe exported in `.zshrc` for another project, and you approved it on first launch: the key wins over the subscription, and `claude -p` always uses it. `/status` shows the active method. Unset the variable and restart:

```bash
unset ANTHROPIC_API_KEY
claude
```

### Login doesn't start, or you're on the wrong account

If the browser doesn't open, copy the URL from the terminal, finish the login by hand and paste the code back. To switch accounts, `/logout` and then `/login`; from the shell, `claude auth status` tells you who you're logged in as. The claude.ai free plan doesn't include Claude Code (Chapter 1). For CI, `claude setup-token` generates a token to put in the pipeline's secrets.

### Connection errors behind a VPN or corporate proxy

Test the network outside Claude Code:

```bash
curl -I https://api.anthropic.com
```

If that fails, the problem is the VPN, the firewall or the proxy: set `HTTPS_PROXY` (for example `http://proxy.azienda.it:8080`, plus `NO_PROXY` if needed) before you start `claude`; if the proxy inspects TLS with a corporate CA, point `NODE_EXTRA_CA_CERTS` at its certificate. SOCKS proxies aren't supported. `/status` tells you whether the proxy was picked up. If the network is fine, check `status.anthropic.com`.


## B.4 Permissions and auto mode

### Claude hardly ever asks for confirmation

Your configuration is fine: since 2.1.283, interactive sessions start in auto mode, and the classifier approves on your behalf. To see every step, use `claude --permission-mode manual`, or `"defaultMode": "default"` under `permissions` in `~/.claude/settings.json` (Chapter 2). On some Windows setups `Shift+Tab` doesn't switch modes: try `Alt+M`.

### `"defaultMode": "auto"` in the project file has no effect

That's by design: as a `defaultMode`, `auto` and `bypassPermissions` only take effect in `~/.claude/settings.json`, otherwise a cloned repository could switch off its own checks (Chapter 11).

### A deny rule doesn't stop the command you thought you'd blocked

A `Bash` rule matches the text: `Bash(curl *)` blocks `curl https://...`, but not `wget` or a Python script that downloads. The space before the asterisk matters too: `Bash(ls *)` doesn't catch `lsof`. In `/permissions`, select the rule to see which file it comes from; rules add up, and the order is deny, ask, allow. For a real boundary you need the sandbox or a hook (Chapters 11 and 12).

### Auto mode does things you don't expect

Recently denied is empty even though Claude was blocked: it only collects the classifier's decisions, and your deny rules come first. Auto mode starts asking for confirmation again halfway through the work: after three consecutive blocks, or twenty in the session, it pauses, and that usually means Claude misunderstood the task. An allow rule on `python` disappears from `/permissions`: auto mode sets aside allow rules that are too broad on interpreters, since they'd bypass the classifier; in Manual the rule is active again.

### After a block, Claude suggests `! cat .env`

The `!` prefix runs the command as you, and deny rules restrict Claude, not you; the output then lands in the conversation, secret included. If the rule is wrong, change it; otherwise, refuse.

## B.5 Sandbox

### `/sandbox` doesn't isolate anything, or isn't available

The sandbox works on macOS, Linux and WSL 2. On native Windows and on WSL 1 it isn't supported, and commands run with no boundary even with `"enabled": true`. On Linux and WSL 2 you need two packages:

```bash
sudo apt-get install bubblewrap socat
```

### `Operation not permitted`, `Read-only file system` or `Could not resolve host`

That's the sandbox doing its job: the command tried to write outside the folder or to reach the network without going through the proxy. If the write is needed, add the folder to `filesystem.allowWrite`; a domain you use often goes in `network.allowedDomains`. If you don't want Claude to offer to retry outside the sandbox, set `"allowUnsandboxedCommands": false` (Chapters 2 and 11).

### pytest stops with a `PermissionError` on `.env`

With the sandbox on, deny rules on `Read`, such as `Read(./.env)`, also apply to the processes it launches: pytest walks the folder and runs into the file. In the lab, the `pytest.ini` from section 11.1 fixed it without removing the rule.

### `docker` doesn't work inside the sandbox

You can exclude it from the sandbox with `sandbox.excludedCommands`, knowing that from then on it runs with all your permissions. To isolate all of Claude Code, hooks and MCP servers included, you need a dev container or a VM (Chapter 2).


## B.6 Hooks

The table from Chapter 12, expanded:

| Symptom | Cause and fix |
| --- | --- |
| The hook doesn't fire | Check the event and matcher with `/hooks`: the matcher is case-sensitive, so `"edit"` matches nothing. Hooks are read at startup: restart Claude Code after every change to `settings.json` |
| The script doesn't run | It's missing the execute permission: `chmod +x .claude/hooks/name.sh` |
| `jq: command not found` | Install `jq` (`brew install jq`, `sudo apt-get install jq`) or rewrite the script in Python |
| The JSON the hook prints is ignored | An `echo` in your shell profile is polluting stdout: move it inside `if [[ $- == *i* ]]` |
| Claude never stops | The Stop hook doesn't check `stop_hook_active` |
| The Stop hook doesn't block with a long test suite | The hook timed out (the default is 600 seconds), and an interrupted hook doesn't block: raise `timeout` (in seconds) |
| `PostToolUse` doesn't prevent the edit | It can't: the tool has already acted. To block, use `PreToolUse` |
| On Windows the `.sh` script doesn't run | Claude Code is using PowerShell: install Git for Windows or set `CLAUDE_CODE_GIT_BASH_PATH` |


Run the script by hand with a sample JSON: if it fails here, `settings.json` has nothing to do with it. You pass `CLAUDE_PROJECT_DIR` yourself:

```bash
echo '{"tool_input":{"file_path":"data/vendite.csv"}}' | .claude/hooks/protect-files.sh; echo "exit: $?"
echo '{"stop_hook_active": false}' | CLAUDE_PROJECT_DIR="$PWD" .claude/hooks/tests-before-stop.sh
```

### The protection hook is there, but the file changed anyway

An `Edit|Write` matcher only sees those two tools. An `echo ... >> data/vendite.csv` from `Bash`, or an `UPDATE` through an MCP server, gets in some other way. For files, add `filesystem.denyWrite` to the sandbox; for a database, use a read-only user or a hook with the `mcp__db__.*` matcher (Chapters 12 and 13).

## B.7 MCP

### The server you just added shows an error

`claude mcp add` saves without verifying: a wrong or expired token only fails when it connects, so the credential is the first suspect. Check with `claude mcp list` and `/mcp`, where you can reconnect. An OAuth server that says it needs authentication wants you to log in, from `/mcp` or with `claude mcp login <name>`. Careful with `claude mcp get`: it prints the token in plain text.

### DBHub: `unable to open database file`

The SQLite DSN needs an absolute path; with DBHub 1.5.0, `sqlite://` followed by the absolute path (which itself starts with `/`) works:

```bash
claude mcp add --transport stdio db -- npx -y @bytebase/dbhub \
  --dsn "sqlite://$(pwd)/data/vendite.db"
```


On native Windows a server started with `npx` needs the `cmd /c` wrapper: `... -- cmd /c npx -y @bytebase/dbhub ...`.

### The server from `.mcp.json` doesn't show up

Project servers have to be approved on first launch. If you said no in a hurry, reset your choices and restart:

```bash
claude mcp reset-project-choices
```

If Claude Code can't read the configuration, there's a `${VAR}` in `.mcp.json` with no value and no default. If the header arrives empty even though the variable is set, it's one of the variables that are never expanded toward a remote server (Claude Code's own credentials and the cloud providers'): use a dedicated name such as `GITHUB_MCP_PAT` (Chapter 13).

### Claude uses `sqlite3` from `Bash` instead of the server

If the prompt doesn't say so, Claude takes whichever route it prefers: write "using the db server".

### Gmail or Drive show up in `/mcp` and you never added them

Those are your claude.ai account's connectors. Where you don't want them, start with `ENABLE_CLAUDEAI_MCP_SERVERS=false claude`.

## B.8 Plugins, skills and agents

### The plugin loads but has no skills or agents

The components ended up inside `.claude-plugin/`, where only `plugin.json` belongs: `skills/`, `agents/` and `hooks/` go at the plugin root. Then run `claude plugin validate ./plugin-name` (Chapter 14).

### Plugin changes don't show up, or the plugin's hook can't find its script

In an open session, use `/reload-plugins`, and relaunch any subagent that was already running. In a plugin's hooks the path starts from `"${CLAUDE_PLUGIN_ROOT}"`, not from `$CLAUDE_PROJECT_DIR`. If the formatter runs twice, the hook is still in the project's `settings.json` as well.

### Your colleagues don't get the plugin update

You changed the files but not `version` in `plugin.json`: bump it in the same commit. To pick up the new version right away:

```bash
claude plugin marketplace update cc-corso
claude plugin update cc-lab-toolkit@cc-corso
```

### `claude plugin eval` won't start, or the delta is zero

You need Git 2.31 or later. With `--no-publish` the report doesn't go to claude.ai. A `Δ` close to zero usually means the skill didn't trigger: the problem is the description.

### The skill doesn't trigger when you expect it to

Claude picks the skill from its description, which should be written as a trigger: when to use it, in the words of whoever asks for it. "Skill for data analysis" almost never triggers. Once you've broadened it, a negative case tells you whether it also fires where it shouldn't (Chapters 9 and 14).

### The skill or custom command doesn't appear in the menu

Check the path (`.claude/skills/<name>/SKILL.md` or `.claude/commands/<name>.md`), the `SKILL.md` file name and the YAML frontmatter, because a syntax error can silence the skill. Then `/reload-skills` and `/skills`. When names clash, the skill wins; plugin skills carry a prefix (`/superpowers:<name>`), and after installing you need `/reload-plugins`.

### `/agents` no longer opens the wizard

The wizard was removed in July 2026: ask Claude for the subagent or write `.claude/agents/<name>.md` yourself (Chapter 10).

### The subagent returns a wall of text, or never finishes

The agent's body doesn't specify a response format: ask for a structure and a length limit. For an agent that has been running too long, `/tasks` shows what it's doing and `Ctrl+X Ctrl+K` stops background subagents; then split the job into pieces you can verify.

## B.9 Context and memory

### Claude forgets decisions made early on

In `/context`, messages have become the biggest item. Compact with instructions (`/compact keep the decisions on the format and the modified files`) or write the state to a file and start over:

```text
write to STATE.md what we've done, the decisions we made and what's left to do
```

Then `/clear` and a prompt that says to read `STATE.md`. For rules that have to come back after every compaction, there's the `SessionStart` hook with the `compact` matcher (Chapters 12 and 15).

### Responses slow down and your plan limits run out fast

`/usage` shows what's consuming them (`/cost` and `/stats` are aliases). It's usually a long session that wanders across unrelated topics, a high effort for trivial work or too many sessions in parallel. One task, one session, and `low` or `medium` for small changes.

### `CLAUDE.md` seems to be ignored

`/memory` shows the loaded instruction files. If yours isn't there, check the name and location (`./CLAUDE.md` or `./.claude/CLAUDE.md` in the folder you launch `claude` from); `AGENTS.md` is only read when there's no `CLAUDE.md`, and rules with `paths:` only come in when Claude touches a matching file. If it's loaded but not followed, it's too long or too vague: stay under two hundred lines, write verifiable instructions, and run `/doctor prompt-audit` for conflicts. A hard prohibition belongs in a rule or a hook (Chapters 7 and 15).

### Auto memory saved something wrong, or `#` no longer saves anything

They're Markdown files in `~/.claude/projects/<project>/memory/`: fix them by hand. `MEMORY.md` loads up to two hundred lines, and you can turn the feature off from `/memory`. The `#` shortcut was removed: ask Claude to edit `CLAUDE.md`, or use `/memory`.

### `/rewind` didn't undo everything

Checkpoints track `Edit` and `Write`. Changes made by a `Bash` command (an `rm`, a migration) and the fixes from `/code-review --fix` stay put: commit before a big job.

## B.10 Worktrees and background sessions

### Tests fail in the worktree because of a missing key

A worktree is a clean checkout, without ignored files such as `backend/.env`. List them in `.worktreeinclude` at the root and Claude Code copies them; `vendor/` and `node_modules/` get reinstalled. Add `.claude/worktrees/` to `.gitignore` too (Chapter 20).

### New sessions don't see what you merged locally

A worktree starts from the remote main. Push, or add `{"worktree": {"baseRef": "head"}}` to `.claude/settings.json`. A subagent with `isolation: worktree` won't find the files of a task that hasn't been merged yet either.

### Sail in two worktrees: ports already in use

The containers fight over ports 80, 3306 and 6379 and over the Compose project name. Keep the application running in one worktree at a time, or change `APP_PORT` and `FORWARD_DB_PORT` in the `.env` of one of the two.

### `/goal` never finishes, or finishes too early

The evaluator sees only the conversation: "the pipeline works" can't be verified, "`composer test` exits with code 0, show me the Status lines with grep" can. Run `/goal clear` and rewrite it. And run the check by hand first: if the suite is already red, the session ends up working on tests that have nothing to do with the task.

### A background session is stuck

Open `claude agents`: if it's in Needs input it's waiting for you, often because of an interactive installer or a permission the classifier didn't let through. Reply from the preview with `Space`; `claude logs <id>` shows the output without going in.

### `git worktree remove` or `git branch -d` refuses

The worktree has uncommitted changes, or the branch isn't merged: look at what's missing before you reach for `--force`.

## B.11 Projects: Python and Excel

| Symptom | Cause and fix |
| --- | --- |
| `externally-managed-environment` on `pip install` | Python from Homebrew or a recent distribution: `python3 -m venv .venv` and activate it |
| `No module named pytest` even after installing it | `claude` started from a shell without the virtualenv: `source .venv/bin/activate`, then `claude` |
| `ModuleNotFoundError: No module named 'src'` | The `pytest.ini` with `pythonpath = .` is missing (Chapter 2) |
| In Excel, dates won't filter and sort in random order | pandas read them as text: ask for `parse_dates` (Chapter 5) |
| The total doesn't change when you fix the Dati sheet | The formulas sum values written by Python into Riepilogo: you need formulas that read the Dati sheet (section 5.4) |
| The script works by hand but not from cron | cron starts from the home folder and doesn't load your profile: `cd` into the project folder, use the virtualenv's Python, load variables from a `.env`, send output to a log file |
| Flask won't start, or the browser gets a 403 on macOS | Port 5000 belongs to the AirPlay receiver: turn it off or use `app.run(debug=True, port=5001)` |
| The PDF cover comes out blank | The background has to be drawn in `onFirstPage`, not added to the `story` |
| ReportLab stops at `doc.build` | The `story` contains a list nested inside another: unpack the sections with `*` |
| A huge CSV fills up the context | Have Claude write a script that reads it in chunks (`chunksize`, `usecols`) and brings only the results into the chat (Chapter 4) |

## B.12 Projects: Laravel and React

### The frontend calls Vite's port instead of the API

The backend URL is hard-coded in the axios client. Read it from a variable, with `baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api/v1'` (Chapter 19).

### CORS error in the browser

`FRONTEND_URL` in the backend's `.env` says `localhost:5173`, but Vite is running on another port because 5173 was taken. Align the variable, which feeds `config/cors.php` (Laravel 13 doesn't publish that file: without it, any origin is accepted).

### An API error comes back as an HTML page

The client didn't send `Accept: application/json`. The `ForceJsonResponse` middleware goes in the `api` group with `prepend`, so the 401 from `auth:sanctum` comes out as JSON too.

### `createToken()` fails with a NOT NULL violation

The primary key of `personal_access_tokens` was turned into a UUID. Sanctum expects an auto-increment: put it back to `$table->id()` and change only `tokenable_id`.

### Green tests on SQLite, errors on MariaDB

SQLite is more lenient about constraints and dates: run the tests with Sail too (`vendor/bin/sail up -d`, `vendor/bin/sail test`).

### `403 Forbidden` on the photo variants

A `local` disk with `'serve' => true` registers a route that intercepts requests before the static file. Keep `serve` only on the public disk for the variants (Chapter 21).

### The job fails looking for a photo that doesn't exist

The dispatch happens inside `DB::transaction()`, and the worker picks up the job before the commit. Return the jobs from the closure and queue them afterward.

### On S3 the photos come out without EXIF, or the `s3` driver won't talk to MinIO

`Storage::disk(...)->path()` on an `s3` disk returns the object key, which `exif_read_data` can't open: read the EXIF from the temporary file at upload time. For MinIO, the `s3` entry in `config/filesystems.php` has to read `AWS_ENDPOINT` and `AWS_USE_PATH_STYLE_ENDPOINT`.

### Behind the load balancer, the rate limit blocks everyone at once

Without `trustProxies`, `$request->ip()` is the proxy's address, and the per-IP limit turns into one shared bucket. Read `TRUSTED_PROXIES` from `.env`.

## B.13 Projects: Firebase

### `firebase: command not found`, or the deploy goes to the wrong project

Install the CLI with `npm install -g firebase-tools`, or use `npx firebase-tools` instead of `firebase`. Then `firebase login` and `firebase projects:list`; the folder's project is in `.firebaserc`.

### The published site is empty or shows the old version

`firebase deploy` uploads `dist/`: run `npm run build` first and check that `public` in `firebase.json` is `dist` (`out/` with Next.js in static export).

### Reloading an inner page gives a 404

The rewrite to `index.html` is missing: answer yes to "Single-page app" in `firebase init hosting`, or add `"rewrites": [{ "source": "**", "destination": "/index.html" }]` to `firebase.json`.

### The custom domain doesn't respond, or the deploy broke something

DNS propagation can take up to a day; in the meantime there's `.web.app`. You can roll back to a previous release from the Hosting console.

## B.14 Projects: AWS

### The stack ends up in `ROLLBACK_COMPLETE`

The events tell you which resource failed and why, in the `ResourceStatusReason` field:

```bash
aws cloudformation describe-stack-events \
  --stack-name photogallery-staging \
  --query "StackEvents[?ResourceStatus=='CREATE_FAILED' || ResourceStatus=='UPDATE_FAILED']" \
  --output table
```

It's usually IAM permissions, account limits (Service Quotas), a name that's already taken (S3 bucket names are unique across all of AWS) or a dependency you have to declare with `DependsOn`. With `InsufficientCapabilities`, you're missing `--capabilities CAPABILITY_NAMED_IAM`. A stack in `ROLLBACK_COMPLETE` has to be deleted with `aws cloudformation delete-stack` before you try again (Chapter 23).

### The ECS task won't start or keeps restarting

The reason and exit code are under the stopped tasks, in the ECS console or with `aws ecs describe-tasks`.

| Symptom | Cause and fix |
| --- | --- |
| Exit code 1 at boot, `FATAL: missing required env var` in the logs | A variable is missing from the task definition |
| Exit code 137 | Out of memory, typical of the worker with large photos: raise `Memory` |
| `CannotPullContainerError` | The execution role lacks `ecr:GetAuthorizationToken` and `ecr:BatchGetImage`, the private subnets don't route through the NAT, or the tag doesn't exist on ECR |
| `exec format error` | ARM image built on an Apple Silicon Mac: `docker build --platform linux/amd64` |
| The task starts and the ALB marks it unhealthy | `/api/v1/health` returns 503: `"storage": "error"` points to the bucket, `"queue": "error"` to the database |

### The database connection times out

The RDS security group isn't accepting traffic from the tasks. The ingress rule on 3306 needs a `SourceSecurityGroupId` equal to the ECS tasks' security group.

### CloudFront returns 502 or 504 on `/api/v1`

Query the ALB directly with `curl -v "https://<ALBDnsName>/api/v1/health"`. If it answers, the problem is CloudFront's `/api/*` behavior: the origin, the protocol and the `Authorization` header, without which Sanctum doesn't see the token. If the ALB returns 5xx too, check the CloudWatch logs.

### SPA routes return 404, or assets go missing after a deploy

The routes need `CustomErrorResponses` that answer the bucket's 403s and 404s with `index.html` and a 200. Missing assets almost always come from a `sync --delete` that also ran on `assets/`: upload the previous build again and follow the order in section 23.4.

### The change set says `Replacement: True` on the RDS instance

Stop: it means a new database in place of the old one, and without a snapshot you lose the data. Just renaming the instance in the template is enough to get there.

## If your problem isn't here

Open an issue in the `claude-code-book-snippets` repository with the output of `claude --version`, your operating system, the command you ran and the full error. Verified reports end up in the changelog in Appendix E.
