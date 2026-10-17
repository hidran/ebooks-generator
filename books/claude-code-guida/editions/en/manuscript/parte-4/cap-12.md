# Chapter 12. Hooks, deterministic automation

::: {.chapter-goals}
[What you'll learn]{.callout-title}

How to write hooks that format code after every edit, block writes to sensitive files, alert you when Claude is waiting on you, and keep Claude from wrapping up while the tests are red. You'll also learn to test them by hand and to figure out why one doesn't fire.

[Prerequisites]{.callout-title}

The `cc-advanced-lab` project from chapter 11, with its `.claude/settings.json`. You need `jq` (`brew install jq` on macOS, `sudo apt-get install jq` on Debian and Ubuntu), plus `ruff` and `pytest` (`pip install ruff pytest`). On Windows the `.sh` scripts run in Git Bash, so install Git for Windows; it doesn't ship `jq`, which you add with `winget install jqlang.jq`.

:::

So far we've asked Claude for things in words: format the code, don't touch the `.env` file, run the tests before you say you're done. We put those requests in prompts, then in `CLAUDE.md` (chapter 7), and they work almost every time. The trouble is that "almost". An instruction in the context is something the model will probably follow; in a long session, or right after a compaction, it can slip. The permission rules from chapter 11 cover part of the problem, because they decide whether an action is allowed to run. What they can't do is run a formatter, kick off the test suite or send you a notification.

That's what hooks are for. They're commands Claude Code runs on its own at specific points in its work cycle, every time, without the model having to remember them. The model doesn't call them and can't skip them: they're launched by the harness, the program around the model that executes the tools (chapter 2).

## 12.1 Events in the work cycle

Every hook is attached to an event. Before Claude uses a tool, `PreToolUse` fires, and it can also block the action. Right after, `PostToolUse` fires. When Claude finishes its response you get `Stop`, when it needs you you get `Notification`, and when the session opens you get `SessionStart`. Add `UserPromptSubmit` and you've covered most practical cases.

| Event | When it fires | Can block |
| --- | --- | --- |
| `SessionStart` | Startup, resume, after `/clear` or a compaction | No |
| `UserPromptSubmit` | When you submit a prompt, before Claude processes it | Yes |
| `PreToolUse` | Before every tool call | Yes |
| `PostToolUse` | After a successful call | No, the tool has already run |
| `Stop` | When Claude finishes responding | Yes, it makes Claude keep going |
| `Notification` | When Claude is waiting for input or a permission | No |

There are quite a few more events: among others, `SubagentStop` when a subagent finishes, `PreCompact` before a compaction and `SessionEnd` when the session closes. The full, current list is in the official documentation, but the six in the table are all you need for this chapter.

Read the "Can block" column carefully. Blocking a `Stop` doesn't stop anything: it prevents Claude from stopping and sends it back to work with a reason. A `PostToolUse`, on the other hand, arrives after the fact. You can react, for example by formatting the file that was just written, but the write has already happened.

## 12.2 How a hook communicates

A `command` hook is an ordinary shell command. Claude Code passes it the event data as JSON on standard input and reads the answer from two channels: the exit code and, when needed, standard output.

For a `PreToolUse` on `Bash`, the input looks like this:

```json
{
  "session_id": "abc123",
  "cwd": "/home/dev/cc-advanced-lab",
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": { "command": "python -m pytest" }
}
```

The `tool_input` field varies by tool. For `Bash` it holds `command`; for `Edit` and `Write` it holds `file_path` (the absolute path) and the content to write. The scripts in this chapter read those fields with `jq`.

There are three possible answers:

| Answer | Meaning |
| --- | --- |
| Exit 0 | No objection, carry on |
| Exit 2 | Block; the text on stderr goes back to Claude as the explanation |
| Exit 0 with JSON on stdout | Finer control, for example `{"decision": "block", "reason": "..."}` for `Stop` |

Be clear about what exit 0 means for a `PreToolUse`: "I have nothing to say", not "I approve". After the hook, the action still goes through the normal permission system, with its allow, ask and deny rules and the active mode. Exit 2 stops the action, and the message on stderr reaches Claude, so it knows why it was stopped and can look for another way. Any other exit code is treated as a hook error that blocks nothing: the action goes ahead.

The JSON on stdout is for when the exit code isn't enough. You'll use it in section 12.7 for `Stop`, where the `reason` field becomes the instruction Claude picks up from. For `PreToolUse`, the same channel lets you return an explicit permission decision instead of a plain block: inside `hookSpecificOutput` you set `permissionDecision` to `allow`, `deny` or `ask`, and put the reason in `permissionDecisionReason`.

### Where hooks are registered

Hooks are configured in `settings.json`, under the `hooks` key, next to `permissions`. The structure has three levels: the event, a list of groups each with its own `matcher`, and inside each group the list of commands to run. The `matcher` filters on the tool name: `"Edit|Write"` makes the group fire only for those two tools, and it's case sensitive, so `"edit"` matches nothing. The files are the same as in chapter 11: `.claude/settings.json` for the project and the team, `.claude/settings.local.json` for just you on that project, `~/.claude/settings.json` for all your projects.

In the examples the script path starts from `$CLAUDE_PROJECT_DIR`, a variable Claude Code sets to the project root. That way the command still works when Claude's shell has moved into a subfolder. The quotes around the variable protect paths with spaces, and inside JSON you write them as `\"`.

## 12.3 Formatting after every edit

The first hook runs `ruff` on every Python file Claude writes or edits. In the lab project, create the scripts folder:

```bash
mkdir -p .claude/hooks
```

Then the file `.claude/hooks/format-python.sh`:

```bash
#!/bin/bash
# Format the Python files Claude edits with ruff
FILE_PATH=$(jq -r '.tool_input.file_path // empty')

if [[ "$FILE_PATH" == *.py ]]; then
  ruff format "$FILE_PATH" >/dev/null 2>&1
fi

exit 0
```

`jq` reads the JSON straight from standard input and pulls out `tool_input.file_path`; the `// empty` returns an empty string when the field is missing, instead of the word `null`. If the file ends in `.py`, the script hands it to `ruff format`, which rewrites it in place. Ruff's output goes to `/dev/null` because nobody needs it here, and the script always exits with 0: a formatter should never block the work.

Make the script executable:

```bash
chmod +x .claude/hooks/format-python.sh
```

Then add the `hooks` block to `.claude/settings.json`, next to the `permissions` from chapter 11:

```json
{
  "permissions": { "...": "as in chapter 11" },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/format-python.sh"
          }
        ]
      }
    ]
  }
}
```

The `"permissions"` line is abbreviated here: your file keeps the allow, ask and deny rules you already wrote, plus the `sandbox` block from section 11.9. The complete file, with every hook in the chapter, is in section 12.7.

Hooks are read at startup, so restart Claude Code after every change to `settings.json`. Then type `/hooks`: under `PostToolUse` you should find the group with matcher `Edit|Write`, the `format-python.sh` command and a note that it comes from the project settings (`[Project]`). If it isn't there, the problem is in the JSON or the event name, and there's no point going further.

<!-- TODO screenshot: pannello /hooks con PostToolUse, matcher Edit|Write e origine [Project] -->

Now a deliberately nasty test:

```text
add to src/report.py a function massimo(path) written all on one line, with no spaces
```

The prompt says nothing about formatting; in fact it asks for the opposite. Claude writes the function on one line, and as soon as the `Edit` tool finishes, Claude Code runs the hook and ruff rewrites the file. Open it from the Claude Code prompt with the `!` prefix, which runs a shell command without going through the model:

```text
!cat src/report.py
```

The function now spans several lines with an indented body, and ruff has also normalized the quotes in the rest of the file. In the lesson recording, Claude then commented on the result unprompted, saying the formatter had split `massimo` across several lines: it can't see the hook, but it notices the file has changed.

Nobody had to remember to format. The same pattern works with any fast formatter or linter: `prettier --write` for a frontend, `php-cs-fixer` for Laravel, `gofmt` for Go. Only the extension you check and the command change.

## 12.4 Protecting sensitive files

The second hook runs before every edit and blocks the ones that touch protected files: `.env`, the `.git/` folder and, in our lab, the source data in `data/`. Create `.claude/hooks/protect-files.sh`:

```bash
#!/bin/bash
# Block edits to sensitive files
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
FILE_PATH="${FILE_PATH//\\//}"   # normalize Windows separators

PROTECTED=(".env" ".git/" "data/")

for pattern in "${PROTECTED[@]}"; do
  if [[ "$FILE_PATH" == *"$pattern"* ]]; then
    echo "Blocked: $FILE_PATH is protected ('$pattern'). Work on a copy." >&2
    exit 2
  fi
done

exit 0
```

This time the script first saves the whole input in `INPUT` with `cat`, then passes it to `jq`. The first hook didn't need this because it read the JSON only once; keeping it in a variable lets you extract several fields without consuming stdin. The next line replaces every backslash with a forward slash: on Windows `file_path` arrives as `C:\Users\...\data\vendite.csv`, and without normalizing it the `data/` pattern would never match. The loop compares the path against each entry in `PROTECTED`; on the first match it writes the reason to stderr and exits with 2.

Make it executable and register it under `PreToolUse`, inside the same `hooks` object that already holds `PostToolUse`:

```bash
chmod +x .claude/hooks/protect-files.sh
```

```json
"PreToolUse": [
  {
    "matcher": "Edit|Write",
    "hooks": [
      {
        "type": "command",
        "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect-files.sh"
      }
    ]
  }
]
```

Restart Claude Code and ask for a change to the data:

```text
add a row for the month 2026-04 to data/vendite.csv
```

Again the prompt says nothing about protection: the rule lives only in the hook. During the recording Claude didn't try to write right away. It first asked, with a multiple-choice question, what sales figure to use for April. Answer with any number. At that point Claude tries the `Edit`, the hook fires and the red line with the block message shows up in the terminal. Claude reads it, explains why it was stopped and suggests an alternative, such as working on a copy of the file. Check with `git status` that `data/vendite.csv` is unchanged.

::: {.callout .callout-tip}
[Tip]{.callout-title}

The block message shows the absolute path, because that's what `Edit` passes to the hook. If you record your screen or paste the logs somewhere, your username ends up in them. To print the path relative to the project, strip the prefix before the `echo`, for example with `REL="${FILE_PATH#"$CLAUDE_PROJECT_DIR"/}"`, and use `$REL` in the message.
:::

### Testing a hook by hand

You can try hook scripts without Claude by piping in a sample JSON with `echo`. Exit Claude Code and run this from the shell, in the project root:

```bash
echo '{"tool_input":{"file_path":"data/vendite.csv"}}' | .claude/hooks/protect-files.sh; echo "exit: $?"
```

The expected output is:

```text
Blocked: data/vendite.csv is protected ('data/'). Work on a copy.
exit: 2
```

The sample JSON holds only the fields the script reads, and that's fine. With an unprotected path, say `src/report.py`, you should see just `exit: 0`. The same trick works for the formatter:

```bash
echo '{"tool_input":{"file_path":"src/report.py"}}' | .claude/hooks/format-python.sh; echo "exit: $?"
```

When a hook doesn't do what you expect, this is the first thing to check. It tells you right away whether the problem is in the script (missing `jq`, a wrong pattern, no execute permission) or in the registration.

## 12.5 Deny rule or hook?

In chapter 11 you already wrote a `deny` rule on `Read(./.env)`. It's natural to wonder why you'd need hooks as well.

A rule matches a pattern against the call: tool name plus specifier, and nothing else. A hook runs your own code, so it can apply any logic you like: look at the content Claude wants to write, check the current branch, read a config file, call another program. And a hook that denies blocks the action in every permission mode, even `bypassPermissions`, where the confirmation prompts go away.

For simple, static rules ("don't read `.env`", "ask before `git push`") a rule in `settings.json` is still the right call: it fits on one line, you can see it in `/permissions` and it has no dependencies. A hook is for when the condition needs reasoning a pattern can't express, or when you want an action and not just a yes or no.

::: {.callout .callout-warning}
[Warning]{.callout-title}

`protect-files.sh` is registered with matcher `Edit|Write`, so it only watches those two tools. If Claude decided to add the row with a shell command, say `echo "2026-04,0" >> data/vendite.csv`, the hook wouldn't fire. A rule on `Bash` matches the command text, and a hook on `Bash` that parses the command has the same limit. For a boundary that actually holds on file writes, use the sandbox with `filesystem.denyWrite` (chapters 2 and 11), and keep hooks as a first filter.
:::

There's a flip side too. Hooks run with your user's permissions and outside the sandbox. A `.claude/settings.json` with hooks in it, in a repository someone else wrote that you've cloned, is code that will run on your machine as soon as you start Claude Code in that folder. Before you work in a repo you don't know, open it and read what's under `hooks`.

## 12.6 A notification when Claude is waiting on you

When you leave Claude working on a long task and switch to another window, you sometimes find out much later that it was sitting on a permission request. The `Notification` event fires at exactly those moments. This hook goes in your user settings, `~/.claude/settings.json`, so it applies to every project:

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "notify-send 'Claude Code' 'Claude is waiting for you'"
          }
        ]
      }
    ]
  }
}
```

The empty matcher applies to every notification. `notify-send` is the standard command on Linux desktops (on Debian and Ubuntu it's in the `libnotify-bin` package). On macOS, replace the command with:

```bash
osascript -e 'display notification "Claude is waiting for you" with title "Claude Code"'
```

Inside the JSON, the double quotes in this command must be written as `\"`. If your `~/.claude/settings.json` already has other keys, add `hooks` alongside them instead of replacing the file.

## 12.7 No stopping with red tests

The third project hook is the one I use most in Spec Driven Development projects (chapters 18 and 19). When Claude is about to stop, the hook runs the tests. If they fail, it returns a JSON with `decision` set to `block` and the test output as the reason. Claude doesn't stop: it reads the reason and keeps working. Create `.claude/hooks/tests-before-stop.sh`:

```bash
#!/bin/bash
# Keep Claude from stopping while the tests fail
INPUT=$(cat)

# Avoid the infinite loop: if we're already continuing because of this hook, let Claude stop
if [ "$(echo "$INPUT" | jq -r '.stop_hook_active')" = "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR" || exit 0
if ! OUTPUT=$(python -m pytest -q 2>&1); then
  jq -n --arg out "$(echo "$OUTPUT" | tail -20)" \
    '{decision: "block", reason: ("Tests are failing, fix them before you stop:\n" + $out)}'
fi

exit 0
```

The `stop_hook_active` check is the most important line in the script. Claude Code sets that field to `true` when Claude is already continuing because a Stop hook sent it back to work. Without the check, a test Claude can't fix would produce an endless loop: stop, red tests, block, another attempt, stop, and so on, burning tokens on every round.

The rest is straightforward. The script moves to the project root, runs `pytest` in quiet mode and captures stdout and stderr in `OUTPUT`. If pytest exits with a nonzero code, `jq -n` builds the JSON from scratch: `--arg out` passes the last twenty lines of output as a string, already properly escaped, and the filter appends them to the message. Using `jq` instead of assembling the JSON by hand with `echo` saves you from trouble with quotes and newlines inside pytest's output. The script always exits with 0, because here the block goes through the JSON.

Make it executable and register it under `Stop`:

```bash
chmod +x .claude/hooks/tests-before-stop.sh
```

```json
"Stop": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/tests-before-stop.sh",
        "timeout": 120
      }
    ]
  }
]
```

`Stop` isn't about a tool, so the group has no `matcher`. The `timeout` is in seconds. For `command` hooks the default is 600, ten minutes: I lower it to 120 here, because if the suite hangs I'd rather not sit there for ten minutes on every stop. On this lab pytest takes under a second. When the timeout expires the hook is killed and it counts as an error that blocks nothing: Claude stops anyway.

At this point the lab's `.claude/settings.json` holds the permissions and sandbox from chapter 11 plus the three project hooks:

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
  },
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{
        "type": "command",
        "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/format-python.sh"
      }]
    }],
    "PreToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{
        "type": "command",
        "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect-files.sh"
      }]
    }],
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/tests-before-stop.sh",
        "timeout": 120
      }]
    }]
  }
}
```

### Trying it out

To see the hook in action you need a red test. With Claude Code closed, break the test on purpose by changing `358` to `359`:

```bash
sed -i 's/358/359/' tests/test_report.py
```

On macOS, `sed` wants an empty argument after `-i`: `sed -i '' 's/358/359/' tests/test_report.py`. You can also change the number by hand in your editor; the result is the same.

Before starting Claude you can try the script with `echo`, as in section 12.4. One catch: `CLAUDE_PROJECT_DIR` is set by Claude Code and doesn't exist in your shell. Pass it yourself on the command line:

```bash
echo '{"stop_hook_active": false}' | CLAUDE_PROJECT_DIR="$PWD" .claude/hooks/tests-before-stop.sh
```

You should see the JSON with `"decision": "block"` and, in the `reason`, the `test_totale` failure. With `"stop_hook_active": true` the script must print nothing.

Now start `claude` and ask for a change that has nothing to do with the tests:

```text
add a docstring to the totale function
```

Claude adds the docstring and tries to stop. The Stop hook doesn't ask the model for permission: it fires on its own, runs pytest, finds the red test and blocks. The terminal shows the hook's feedback, `Stop hook error: Tests are failing, fix them before you stop:` followed by the pytest output. Claude reads the reason, sees that the test expects 359 while the data adds up to 358, restores the correct value and reruns the tests. On the second stop `stop_hook_active` is `true` and the hook lets it stop.

<!-- TODO screenshot: riscontro dello Stop hook con l'output di pytest e Claude che corregge il test -->

With this script the block fires once per response. If the tests were still red after the first round, the hook would let Claude stop on the second attempt anyway: that's the price of the anti-loop check. In practice it's enough, because Claude gets the pytest output and usually fixes the problem on the first try, and either way you see the real state of the tests at the end of the response.

Notice too that in this test Claude fixed the test, not the code. That was the right call here, because we broke the test ourselves. In a real project a red test may mean the implementation is wrong: if you want Claude to leave the tests alone unless it asks first, say so in `CLAUDE.md` or add `tests/` to the list in `protect-files.sh`.

## 12.8 Conditional hooks, SessionStart and the other types

Two useful variants, even though we won't use them in the lab.

The first is the `if` field, which uses the same syntax as permission rules. Here the hook fires only for `git` commands, not for every `Bash` command:

```json
"PreToolUse": [
  {
    "matcher": "Bash",
    "hooks": [
      {
        "type": "command",
        "if": "Bash(git *)",
        "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/check-git-policy.sh"
      }
    ]
  }
]
```

The `matcher` picks the tool, the `if` narrows it down by input. Without `if`, the script would have to read `tool_input.command` and exit right away with 0 for anything that doesn't start with `git`: that works, but every `ls` and every `pytest` would spawn an extra process.

The second uses `SessionStart` with the `compact` matcher. After every context compaction, whatever the hook prints on stdout is added to Claude's context:

```json
"SessionStart": [
  {
    "matcher": "compact",
    "hooks": [
      {
        "type": "command",
        "command": "echo 'Remember: read SPEC.md before implementing. Latest commits:' && git log --oneline -5"
      }
    ]
  }
]
```

For `SessionStart` the matcher filters on how the session started, and `compact` means resuming after a compaction. It's a good way to keep project rules from getting lost, such as reading the spec before implementing, at exactly the moment the summary may have watered them down. Chapter 15 comes back to compaction and what survives it.

Besides `command` there are other hook types. `http` hooks send the event JSON to a URL, handy for an internal service that logs or approves actions. `prompt` and `agent` hooks ask a model to decide, for conditions a script can't evaluate, such as "does this change follow the conventions in `CLAUDE.md`?". `agent` hooks are still experimental. Finally, hooks can ship inside a plugin, in the `hooks/hooks.json` file with paths based on `${CLAUDE_PLUGIN_ROOT}`: we'll see that in chapter 14.

## 12.9 When a hook doesn't work

The most common problems, with their fixes:

| Problem | Fix |
| --- | --- |
| The hook doesn't fire | `/hooks` to check the event and matcher (both case sensitive); restart Claude Code after every change to `settings.json` |
| `jq: command not found` | Install `jq` or rewrite the script in Python |
| The script doesn't run | `chmod +x` on the script |
| The printed JSON is ignored | An `echo` in your shell profile pollutes the output: move it inside `if [[ $- == *i* ]]` |
| Claude never stops | The `stop_hook_active` check is missing |

The fourth row deserves an example. If your `~/.bashrc` prints a welcome message, then when the shell loads to run the hook that text lands on stdout ahead of the JSON, and Claude Code can no longer parse it. The guard makes the message print only in interactive shells:

```bash
if [[ $- == *i* ]]; then
  echo "Welcome"
fi
```

Two more checks that aren't in the table but save time. Before looking at the configuration, run the script by hand with `echo` as in section 12.4: if it fails there, `settings.json` has nothing to do with it. And on Windows, make sure Claude Code is using Git Bash, because a `.sh` script won't run in PowerShell (chapter 1 explains how to set the path with `CLAUDE_CODE_GIT_BASH_PATH`).

## Summary {.unlisted}

- A hook is a command Claude Code runs on its own when an event fires: it turns a recommendation the model follows almost every time into a rule that holds every time.
- You register it in `settings.json` under `hooks`, with an event, a `matcher` and a command; the script path starts from `"$CLAUDE_PROJECT_DIR"`, and changes take effect at the next restart.
- The hook gets JSON on stdin and answers with its exit code: 0 carries on (for `PreToolUse` it isn't an approval), 2 blocks and sends stderr to Claude, 0 plus JSON on stdout for decisions such as the `block` on `Stop`.
- A Stop hook must always check `stop_hook_active`, or you risk an infinite loop.
- A hook that denies blocks in every mode, but it only sees the tools in its matcher: for a real boundary on files you also need the sandbox.
- You test hooks by hand with `echo` and check them with `/hooks`.

## Exercise {.unlisted}

Write `.claude/hooks/check-git-policy.sh`, the script mentioned in section 12.8, and register it under `PreToolUse` with matcher `Bash` and `"if": "Bash(git *)"`. The script reads `tool_input.command` and blocks with exit 2 any `git push` that contains `--force` or `-f`, with a message in English on stderr that suggests `--force-with-lease`. Every other command passes with exit 0, `--force-with-lease` included: watch your pattern, because that string contains `--force`.

You're done when these three manual tests give the expected result:

```bash
echo '{"tool_input":{"command":"git push --force origin main"}}' | .claude/hooks/check-git-policy.sh; echo "exit: $?"
echo '{"tool_input":{"command":"git push --force-with-lease origin main"}}' | .claude/hooks/check-git-policy.sh; echo "exit: $?"
echo '{"tool_input":{"command":"git status"}}' | .claude/hooks/check-git-policy.sh; echo "exit: $?"
```

The first must print your message and `exit: 2`, the other two only `exit: 0`. Then restart Claude Code and check that `/hooks` shows the new group under `PreToolUse`, with the `check-git-policy.sh` command.
