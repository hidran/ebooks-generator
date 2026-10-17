# Chapter 15. Keeping context and memory in check

::: {.chapter-goals}
[What you'll learn]{.callout-title}

- How to read what's filling the context window with `/context`, `/skill-doctor` and `/usage`.
- When to use `/compact`, `/rewind`, `/fork` and `/clear` in a long conversation.
- What auto memory saves, where to find it, and how to correct it or turn it off.
- How to have `/doctor` and `/doctor prompt-audit` check your configuration and instructions.

[Prerequisites]{.callout-title}

The `cc-advanced-lab` project from chapter 11, with everything chapters 12-14 added to it. If you skipped a chapter or two, that's fine: you'll see fewer entries in the panels, but the commands work the same.

:::

In chapters 11-14 you loaded `cc-advanced-lab` with useful things: permission rules in `.claude/settings.json`, hooks that format the Python code and protect `data/`, MCP servers, the `cc-lab-toolkit` plugin. Each of those pieces takes up a bit of room in every session, even when you don't use it. This chapter closes Part IV with the tools for seeing how much room, for handling a conversation that has run too long, and for keeping tidy the instructions Claude reads at startup, both the ones you write and the ones it writes itself.

## 15.1 What's in the context window

The context window is everything the model sees when it prepares its next response. Your messages are in there, along with quite a lot more, and it pays to know what, because that's what decides how a long session goes.

There are four parts. First, the system prompt: Claude Code's internal instructions and the definitions of the built-in tools (`Read`, `Edit`, `Bash`, `Agent` and the others from chapter 2). Second, extensions: skills, agents, plugins and MCP servers. For each one Claude Code always loads the name and description, because that's how the model knows when to use it; a skill's body only arrives when it's needed (you saw this in chapter 9). Third, memory files: `CLAUDE.md`, the rules in `.claude/rules/` and the auto memory index. And finally the conversation itself: the messages, every file Claude has read, the output of every command it has run.

With Claude Opus 5.5 the default window is one million tokens, so there's plenty of room (the model and its window can change, so check `/model`). The practical limit shows up before the technical one, for two reasons. Every turn processes the whole context, so a bloated session burns through your plan's limits faster. And the more material there is, the more the instructions and decisions from the start compete with everything that came later: in a long session that wanders across unrelated topics, Claude starts forgetting conventions it followed early on.

## 15.2 Measuring with /context, /skill-doctor and /usage

Before you manage the context, look at it. Open `cc-advanced-lab` and start `claude`. To give the panels something to show, ask three read-only questions:

```text
read src/report.py and its test and tell me what they do
```

```text
how many rows does data/vendite.csv have and which columns does it contain?
```

```text
how do you run the tests in this project?
```

These are harmless questions: they don't change anything, and in auto mode they go through without confirmation prompts.

### /context

Type `/context`. The panel shows how the window is split up: how much the system prompt and system tools take, plus MCP server tools, agents, skills, memory files and messages, and how much space is still free.

<!-- TODO screenshot: /context in cc-advanced-lab dopo le tre domande, con le categorie system prompt, tool, MCP, skill, agent, memory files, messaggi -->

The first thing to notice is that part of the context is taken before you've even typed your first prompt. Skills, agents and plugins cost something even if you don't use them in this session, because their names and descriptions are always loaded. MCP servers cost less than you might expect: thanks to the tool search from chapter 13, Claude Code loads only the tool names at startup and fetches the full definitions when they're needed.

The second thing is the messages entry. After three questions it's small. After an hour of work, with a few big files read in full and the output of a test suite, it becomes the largest entry. That's the one `/compact` and `/clear` shrink.

### /skill-doctor

`/skill-doctor` answers one specific question: which skills are worth what they cost? For each skill it shows how much context it takes and how often it's used.

A lightweight skill that gets used often is fine. A skill with a very long description that you've never triggered is a candidate for removal: if it's a project skill, take it out of `.claude/skills/`; if it comes from a plugin, use the `/plugin` manager (chapter 14) to decide whether you still need that plugin. The same panel is a good reason to keep the descriptions of the skills you write short (chapter 9).

### /usage

`/usage` looks at the same thing from another angle: what's consuming your plan's limits. The breakdown is by skill, subagent, plugin and MCP server. If a subagent you run often reads half the repository on every pass, this is where you'll see it.

All three panels close with `Esc`.

## 15.3 Compact, rewind, fork, start over

For a conversation that has grown long you have four tools: `/compact`, `/rewind`, `/fork` and `/clear`. They do different things, and it's worth trying them in order in the same session so you can see what each one does.

### /compact with instructions

`/compact` summarizes the conversation and frees up space. The summary replaces the older messages: the session stays the same, but Claude keeps the details in condensed form. The command accepts instructions about what to keep, and you should always give them:

```text
/compact Keep the project structure, the decisions we made and the failing tests
```

Without instructions the summary decides on its own what to keep, and what matters to you (the name you picked for a function, the test that fails intermittently) can end up as a vague sentence or disappear entirely. With instructions you tell it what it must not lose. In Part VI, when a Photogallery phase runs long, this is exactly how you'll compact: task status, decisions made, findings still open (chapter 19).

Claude Code also compacts on its own when the window nears its limit. That's fine as a safety net, but an automatic compaction happens when it decides, and without your instructions. If the project needs certain information back in context after every compaction, use the `SessionStart` hook with the `compact` matcher from chapter 12.

::: {.callout .callout-tip}
[Tip]{.callout-title}

Compact when you finish a piece of work, not when the answers start getting worse. Once a task is done and the tests pass, you know exactly what's worth keeping, and the summary comes out better.
:::

### /rewind and double Esc

To have something to rewind, ask Claude for a small change:

```text
add a one-line comment at the top of src/report.py explaining what the module does
```

Now press `Esc` twice (or type `/rewind`). A menu opens with the earlier points in the conversation, one for each of your prompts. Pick the point to go back to and decide what to restore: the code, the conversation, or both. There are also two summary options, which amount to a targeted compaction of just one part: `Summarize from here` condenses the conversation from the chosen point onward, while `Summarize up to here` condenses everything before it and leaves the later messages untouched. Neither one touches your files.

The three combinations fit different situations:

- Restore code and conversation when Claude went down the wrong path and you want to try again with a better prompt, as if the attempt never happened.
- Restore only the code when the discussion was useful (you now understand why the approach doesn't work) but the files need to go back to how they were.
- Restore only the conversation when you're happy with the change but the exchange that produced it went off topic and is taking up space.

In the comment experiment, restore only the code and then run `git diff`: `src/report.py` is back to how it was.

::: {.callout .callout-warning}
[Warning]{.callout-title}

`/rewind` checkpoints track changes made with the file-editing tools, such as `Edit` and `Write`. Whatever a command run through `Bash` changes (an `rm`, a database migration) stays as it is. Fixes applied by `/code-review --fix` (chapter 22) can't be undone with `/rewind` either. For all of that, your safety net is Git: commit before you hand Claude a big job.
:::

### /fork

`/fork` copies the conversation into a new background session. The main session stays where it is, with all its context, and the copy starts from the same point. Use it when you want to explore an alternative without losing your place, for example trying a refactoring you're not sure about while the main session stays on the code that works.

You'll find the copy among your background sessions, in the agent view you'll open with `claude agents` in chapter 20. Keep in mind that it's a real session: it uses your plan like any other.

### /clear

`/clear` starts from scratch. The conversation drops out of context and Claude Code reloads the memory files as it does at startup. Files on disk stay as they are, because `/clear` only touches the conversation. Use it when you switch topics. `SessionStart` hooks fire after a `/clear` too, with source `clear`: a hook with no matcher, or with the `clear` matcher, puts whatever it prints back into context. The one with the `compact` matcher from chapter 12 doesn't run here.

If you're about to `/clear` in the middle of a job, first ask Claude to write down where you've got to:

```text
write in STATE.md what we've done, the decisions we made and what's left to do
```

After the `/clear`, start again with a prompt that tells Claude to read `STATE.md`. In the Photogallery, the specs and `docs/TASKS.md` play the role of `STATE.md`: they live on disk, so between one phase and the next you can wipe the context without losing anything (chapters 18 and 19).

### Which one to use

| Situation | Command |
| --- | --- |
| The task is ongoing, the window is full of details you no longer need | `/compact` with instructions |
| Claude took a wrong turn and you want to go back | `Esc Esc` or `/rewind` |
| You want to try an alternative without touching the main session | `/fork` |
| The task is done and you're moving on to something else | `/clear` |

## 15.4 One task, one session

The practical rule behind the previous section is this: one task, one session. Long conversations that hop between topics are the fastest way to get worse results, because each topic leaves behind files read, abandoned attempts and decisions that have nothing to do with the next task.

In `cc-advanced-lab` that means, for example, that if you've just fixed a test for `src/report.py` and now you want the weekly sales report, you run `/clear` or open a new session. The report doesn't need to know how you debugged the test, and leaving that debugging in context can only muddle the new request.

Whatever needs to survive from one task to the next shouldn't stay in the conversation: it goes in a file. Stable conventions live in `CLAUDE.md`, the state of a half-finished job in a file like `STATE.md` or in the task list, personal preferences in auto memory.

## 15.5 The instructions you write, in brief

Chapter 7 covers `CLAUDE.md` in full: the levels, what to put in it and what to leave out, path-specific rules, AGENTS.md. Here you only need a refresher, because the next sections come back to it.

There are four levels: organization (a path managed by IT), user (`~/.claude/CLAUDE.md`), project (`./CLAUDE.md` or `./.claude/CLAUDE.md`, shared through Git) and local (`./CLAUDE.local.md`, kept out of Git). Stay under two hundred lines and write instructions you can check: "use two-space indentation" works better than "format the code nicely". For `cc-advanced-lab` you don't need much:

```markdown
# cc-advanced-lab

## Comandi
- Test: `python -m pytest -q`
- Formattazione: `ruff format src tests`

## Regole
- Non modificare mai i file in `data/`: lavora su copie in `tmp/`
- Ogni nuova funzione in `src/` ha un test in `tests/`

<!-- Nota per i manutentori: le regole Python stanno in .claude/rules/python.md -->
```

The rules that apply only to Python files live in `.claude/rules/python.md`, with a `paths:` field in the frontmatter, and they load only when Claude works on a matching file. The HTML comment at the bottom is stripped before it reaches Claude: it's a note for your colleagues that costs no context.

Instructions load at startup, so after writing the two files, exit and start `claude` again. Ask it to read `src/report.py` so the Python rule kicks in, then type `/memory`: you'll see the list of instruction files that were loaded. In `/context` the same files show up under Memory files, each with its size.

Two things to keep in mind in this chapter too. `CLAUDE.md` steers Claude but doesn't bind it: "never modify the files in `data/`" is an instruction that usually gets followed, whereas the `protect-files.sh` hook from chapter 12 blocks edits made with `Edit` and `Write` every single time. And if a repository has an `AGENTS.md` and no `CLAUDE.md`, Claude Code reads that instead.

## 15.6 Auto memory

Besides `CLAUDE.md`, which you write, there's auto memory, which Claude writes. It holds your preferences, the corrections you give it while you work, and project context it can't work out by reading the code. Claude decides on its own what's worth noting down, and when you explicitly ask it to remember something, that's where it saves it.

Try it in `cc-advanced-lab`:

```text
remember that in this project I prefer pytest with the -q option and commit messages in English
```

Claude picks where to write, creates the files and lets you know with a memory-saved message. If it just answers in words without saving anything, rephrase more directly: "save to memory that...".

<!-- TODO screenshot: messaggio di memoria salvata dopo il prompt "ricorda che..." -->

### Where it lives

Memory lives in your home directory, under `~/.claude/projects/`, with one folder per project and a `memory/` folder inside it. It's shared across worktrees of the same repository: a preference saved in a feature's worktree also applies in the main checkout, which will come in handy with the parallel waves in chapter 20. Since it lives in your home directory and not in the repository, your colleagues can't see it and it doesn't follow you to another machine.

The project folder name comes from the repository's full path with the separators replaced by dashes, so it includes your username too. To look at its contents without typing that path, use a glob from the Claude Code prompt (the `!` prefix runs a shell command):

```bash
!cat ~/.claude/projects/*cc-advanced-lab/memory/*.md
```

You'll see two files: `MEMORY.md` and the one with the preferences you just saved. `MEMORY.md` is the index. It's loaded in every session, up to two hundred lines or 25 KB, and it points to the other files, which Claude reads when it needs them. If the index goes over that limit, the part at the bottom doesn't make it into context at startup.

### Read, correct, turn off

They're plain Markdown files. You can open them in your editor, fix a preference that no longer holds, or delete a whole file. If Claude noted down something wrong (it happens, for example when you gave a correction that only applied to one case), the quickest fix is to edit the file by hand.

`/memory` shows the loaded instruction files and the auto memory folder. From the same menu you turn auto memory on or off. Turning it off makes sense in a demo repository, during a recording, or when you want every session to start only from what you wrote yourself.

The `/memory` toggle saves `autoMemoryEnabled` to `~/.claude/settings.json`, so it applies to all your projects. To turn it off for a single project, put `"autoMemoryEnabled": false` in that project's settings. There's also the `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` environment variable, which is handy in scripts.

## 15.7 CLAUDE.md or auto memory?

Both mechanisms end up in context at startup, but they have different owners.

| | `CLAUDE.md` | Auto memory |
| --- | --- | --- |
| Who writes it | You | Claude |
| What it holds | Commands, conventions, rules | Preferences, corrections, context |
| Where it lives | In the repository (or in your home directory, at user level) | `~/.claude/projects/<project>/memory/` |
| Who sees it | The team, through Git | Only you, on this machine |
| When it changes | When you edit it | When Claude makes a note or you say "remember" |

A simple rule for choosing: if the information is useful to anyone working on the project, it goes in `CLAUDE.md`. The test command, the folder not to touch, the commit message format agreed with the team are project instructions. "I prefer short answers" or "I use pytest with `-q`" are your own preferences, and auto memory is the right place for them.

Every so often, open the memory folder and look for notes that belong somewhere else. If Claude learned from one of your corrections that "migrations never run against the production database", that's a rule the team needs to know: move it to `CLAUDE.md`, put it through a review, and delete it from memory. And if it's a rule that must never be broken, neither file is enough: you need a permission rule (chapter 11) or a hook (chapter 12).

## 15.8 Getting your configuration checked

By now `cc-advanced-lab` has instructions scattered across quite a few places: `CLAUDE.md`, the Python rule, the skills, the agents, the plugin, auto memory. Keeping them consistent by hand is tedious, and Claude Code has two commands that do it for you.

### /doctor

`/doctor` runs a full check of your configuration and can also fix the problems it finds. Among other things it looks at `CLAUDE.md` and suggests removing what Claude can work out by reading the code, such as a list of folders or dependencies. It's the same advice as in chapter 7, except this time the tool gives it to you, line by line. The panel closes with `Esc`.

### /doctor prompt-audit

`/doctor prompt-audit` digs deeper into the instructions. It reads `CLAUDE.md`, the rules, the skills and the agents, and flags three kinds of problems: instructions written for older models (warnings like "remember to read the file before editing it" that are just noise today), references to files that no longer exist, and instructions that contradict each other, perhaps one in `CLAUDE.md` and the other in a skill.

The analysis is a model pass, so it takes a few tens of seconds and uses your plan like a normal prompt. At the end it proposes changes but doesn't touch anything until you ask. You can confirm this with `git status` right afterward: the working tree is as it was.

::: {.callout .callout-example}
[Example]{.callout-title}

Say that in `cc-advanced-lab` the `CLAUDE.md` says to run the tests with `python -m pytest -q`, while an agent or a skill written months earlier still uses `pytest -v`. Neither is wrong on its own, but together they give Claude two different instructions for the same thing. That's exactly the kind of conflict `prompt-audit` brings to the surface.
:::

### claude doctor from the terminal

You can also run the same diagnosis outside Claude Code, from the shell:

```bash
claude doctor
```

It shows the state of your installation, errors in your settings files and suggested fixes, without starting a session. It's the command to remember when Claude Code won't start, or starts and ignores a `settings.json` you just edited: a malformed JSON file shows up here.

::: {.callout .callout-warning}
[Warning]{.callout-title}

The output of `/doctor` and `claude doctor` includes the installation path, which contains your username, and `/memory` shows the project folder name, which contains it too. If you take screenshots or record your terminal for a colleague, cover those lines.
:::

## 15.9 Command reference

| Command | What it's for |
| --- | --- |
| `/context` | How the context window is split up |
| `/skill-doctor` | Context cost and usage frequency of each skill |
| `/usage` | What's consuming your plan's limits, by skill, subagent, plugin and MCP server |
| `/compact [instructions]` | Summarizes the conversation, keeping what you specify |
| `/rewind` or `Esc Esc` | Goes back to an earlier point: code, conversation or both |
| `/fork` | Copies the conversation into a background session |
| `/clear` | Starts over with an empty conversation |
| `/memory` | Loaded instruction files, auto memory folder and toggle |
| `/doctor` | Full configuration check, with fixes |
| `/doctor prompt-audit` | Outdated instructions, missing files, conflicts; proposes changes without applying them |
| `claude doctor` | The diagnosis from the shell, without starting a session |

## 15.10 From Part IV to the projects

With this chapter you have all the tools from Part IV: permissions and the sandbox decide what Claude can do, hooks automate the checks you don't want to leave to the model, MCP and plugins connect it to services and to your team, and now you know how to measure what all of that costs in context and keep it tidy.

From here the book changes pace. In Part V you build a landing page from idea to deploy on Firebase; in Part VI, the Photogallery, a Laravel and React application with 124 tasks split into 14 phases. These are long projects, spread over many sessions: you'll use `/compact` with instructions when a phase runs long, `/clear` before starting the next one, and a short `CLAUDE.md` that every new session rereads at startup.

## Summary {.unlisted}

- `/context` shows how the window is split up; skills, agents and plugins take up room even when you don't use them, because their names and descriptions are always loaded.
- `/skill-doctor` tells you which skills cost context without getting used, `/usage` what's consuming your plan's limits.
- `/compact` with instructions when the task continues, `Esc Esc` to go back, `/fork` for an alternative in the background, `/clear` when you switch topics. Checkpoints don't cover `Bash` commands: that's what Git is for.
- One task, one session: whatever must survive goes in a file (`CLAUDE.md`, `STATE.md`, the task list).
- Claude writes auto memory in `~/.claude/projects/<project>/memory/`, with `MEMORY.md` as an index loaded up to two hundred lines; you correct it by hand and turn it off from `/memory`.
- `/doctor` and `/doctor prompt-audit` keep your configuration clean; `claude doctor` works even when Claude Code won't start.

## Exercise {.unlisted}

In `cc-advanced-lab`, with the work from chapters 11-14 in place:

1. Start `claude`, ask the three read-only questions from section 15.2, and note from `/context` how much messages, skills and memory files take. Run `/skill-doctor` and write down the skill that costs the most relative to how much it's used.
2. Ask Claude to add a comment at the top of `src/report.py`, then use `Esc Esc` and restore only the code. Check that `git status` shows no changes to `src/report.py`.
3. Ask Claude to remember one of your preferences (for example, commit messages in English). Find the file in the memory folder, edit the preference by hand (for example, add that the message must start with a verb in the imperative mood), run `/clear`, and ask Claude for a commit message for any change.
4. Run `/doctor prompt-audit` and read the report without applying anything.

The exercise is done when the commit message from step 3 follows the preference you edited by hand, and `git status` after step 4 shows the same state as before the audit.
