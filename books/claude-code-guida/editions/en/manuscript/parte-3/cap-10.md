# Chapter 10. Agents and subagents, and when to use what

::: {.chapter-goals}
[What you'll learn]{.callout-title}

You'll learn to write a subagent, which is a Markdown file in `.claude/agents/` with its own frontmatter and system prompt, and to have Claude write it for you. You'll see the subagents Claude Code already uses on its own, how they run in the background and how they ask you for permissions. By the end you'll have a practical rule for choosing between CLAUDE.md, custom commands, skills, agents, hooks and MCP servers, and you'll know when it makes sense to have several agents work together.

[Prerequisites]{.callout-title}

Chapters 8 and 9, because this chapter keeps comparing agents with custom commands and skills.

:::

In the previous chapters you added pieces to Claude Code. `CLAUDE.md` remembers the project's conventions (chapter 7), custom commands turn recurring prompts into slash shortcuts (chapter 8), and skills bring reusable procedures into the session (chapter 9). All of these live in the same place: the main session, with its history, the files it has already read and the decisions made an hour ago.

If you ask for a code review while Claude is still in the middle of the implementation, the review drags all of that baggage along. The context is noisy, and Claude already has an opinion about the code because it wrote it. An agent solves exactly this: it's another instance of Claude, with its own context that starts empty. It gets the task, does it on its own and hands you back only the conclusions. If a skill is a manual Claude looks things up in while it works, an agent is a colleague you hand a task to: they do it at their own desk and bring you the result.

## 10.1 What a subagent is

A **subagent** is a specialized Claude Code instance that gets a single task, works on it in a separate context and returns the result to the main session. In chapter 2 you saw it from the loop's side: the `Agent` tool opens a second loop with a context all its own. Here you look at it from the side of the person configuring it. In this book "agent" and "subagent" mean the same thing.

Three traits set it apart from everything you've seen so far.

### Isolated context

The subagent starts from scratch. It hasn't seen the conversation, it hasn't read the files Claude opened in the last hour, and it doesn't know which trade-offs you agreed to. What it knows is the task it receives and whatever it reads on its own.

That's the main advantage. The subagent does its work in its own context, and the main session, already full of files read and errors analyzed, gets a report of a few hundred words instead of thousands of lines of reads.

### Its own system prompt

Every agent has a system prompt that says who it is, what it has to do and how it should answer: a senior code reviewer, a data analyst, a security auditor. A generic Claude you ask the same thing halfway through a conversation starts instead from a context already slanted by the rest of the work.

### Limited tools

An agent can have just a subset of the tools. A reviewer with `Read` but without `Edit`, `Write` and `Bash` can't accidentally modify the files it's analyzing, even if its prompt is badly written or it misreads the task. Fewer tools also means fewer surprises: in the worst case, a read-only agent hands you a wrong report.

### When it pays off

Four situations come up a lot.

The first is code review: an agent that didn't follow the implementation doesn't know how much that function cost you, and has no qualms about telling you it needs a rewrite. The second is searching the codebase: the agent reads dozens of files and you get the summary ("authentication uses Sanctum tokens, the ability is checked in the controller with `tokenCan()`"), not the trail of reads. The third is parallel tasks: security, performance and test coverage in three agents at once, with a total time close to that of the longest analysis. The fourth is noisy tasks, like loading a big CSV or reading dozens of config files: the intermediate output stays in the agent's context.

### Skills and agents compared

| | Skill | Agent |
|---|---|---|
| Where it runs | In the main context | In a separate context |
| What it knows about the session | Everything | Nothing, it starts from scratch |
| Tools | The same as the session | A restricted list, if you write one |
| Typical use | A procedure to follow while you work | A task to delegate |

The two combine. In chapter 9 you saw that a skill with `context: fork` runs in a subagent, and the `agent` field says which one. The other way around, an agent can preload skills with the `skills` field in its frontmatter.

## 10.2 The subagents you already have

Claude Code ships with a few subagents and launches them on its own when they're needed.

| Subagent | What it does | Tools |
|---|---|---|
| `Explore` | Explores the codebase to answer a question | Read-only |
| `Plan` | Researches the code during Plan Mode | Read-only |
| `general-purpose` | Multi-step tasks that also require acting | All |

Explore is the one you'll see most often. It uses the same model as the main session and accepts three depth levels: quick, medium and very thorough. You can ask for it explicitly:

```text
use the Explore agent, very thorough level, to figure out how the Photogallery handles photo uploads: from the controller down to the queued jobs. Give me the files involved and the flow in ten lines
```

Explore and Plan start without `CLAUDE.md`: they get the question and read the code, without your project instructions. If a convention is essential to the answer, put it in the prompt. There are also utility subagents, such as `statusline-setup` and `claude-code-guide`. The environment variable `CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS=1` removes Explore and Plan.

::: {.callout .callout-deep-dive}
[Under the hood]{.callout-title}

Every subagent starts from a call to the `Agent` tool. Up to version 2.1.63 the tool was called `Task`, and you'll still find that name in older articles and configs: `Task(...)` works as an alias in permission rules. Rules can also look at the call's parameters, for example `Agent(model:opus)` for subagents launched on Opus. We use this in chapter 11.
:::

## 10.3 Anatomy of an agent

An agent is a Markdown file with YAML frontmatter. The file name is up to you; the agent's name comes from the `name` field. Claude Code looks for agents in several places, and if two have the same name, the one higher in this list wins:

1. settings managed by your organization;
2. the `--agents` command-line flag, which takes a JSON definition for a single session;
3. `.claude/agents/` in the project, searched in parent folders up to the repository root and in subfolders;
4. `~/.claude/agents/` in your home directory;
5. the `agents/` folder of installed plugins.

In practice you pick between two places. If the agent knows the project's conventions, services and paths, it goes in `.claude/agents/` and you commit it: the whole team gets it with the repository. If it's a cross-cutting skill set, a generic reviewer or a Python expert, it goes in `~/.claude/agents/` and you'll have it in every project. It's the same logic as skills.

A generic reviewer, `~/.claude/agents/code-reviewer.md`, looks like this:

```markdown
---
name: code-reviewer
description: Reviews code for bugs, project conventions and missing tests. Use it after significant changes, before committing.
tools: Read, Grep, Glob
model: sonnet
---

You are a senior code reviewer for this project.

## The task
Review the changes you're pointed to. Focus on:
- bugs and unhandled edge cases
- adherence to the project's conventions (see CLAUDE.md)
- test coverage
- performance problems
- readability

## Response format
- Strengths (three at most)
- Major problems, with file:line and a proposed fix
- Minor suggestions (optional)
- Verdict: APPROVED or NEEDS_CHANGES

## Constraints
- Don't modify files.
- 300 words at most in total.
```

### The frontmatter

Only `name` and `description` are required. Fields made of several words are in camelCase.

`name` is the identifier: lowercase with hyphens, 256 characters at most and no colons. It's the name you use to call the agent: "use the code-reviewer agent on...".

`description` is the field that matters most. Claude reads the description of every available agent and decides from it whether to delegate a task, even when you don't name any agent. Write it like a router rule: what it does and when to use it. "Helps with code" is useless. "Reviews code for bugs, conventions and missing tests. Use it after significant changes, before committing" tells Claude exactly when to bring it in. As with skills, the description stays in every session's context even when the agent isn't working, so keep it short.

`tools` is the list of allowed tools. If you leave it out, the agent inherits all of the session's tools, including those from MCP servers. Setting it is almost always the right call. `disallowedTools` works the other way: you start from everything and take something away, for example `Bash`. In the native builds for macOS, Linux and WSL, `Grep` and `Glob` usually aren't there, because Claude searches files through `Bash`: there, an agent with `Read, Grep, Glob` effectively works with `Read` alone. That's enough to review the files you point it to. Don't add `Bash` just to give it search, because with a shell the agent can also write.

`model` picks the model: `sonnet`, `opus`, `haiku`, `fable`, a full ID like `claude-opus-5-5`, or `inherit` to use the session's model. A technical reviewer does fine on Sonnet, an agent that designs a feature's structure may deserve Opus, and one that summarizes logs goes on Haiku. If you leave the field out, the agent uses the model Claude passes it for that call and, failing that, the session's model (or the one in `CLAUDE_CODE_SUBAGENT_MODEL`, if you've set it).

You'll use the other fields less often:

| Field | What it's for |
|---|---|
| `permissionMode` | The agent's permission mode: `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan`, `manual` (chapter 11) |
| `maxTurns` | The maximum number of loop turns before the agent stops |
| `effort` | The reasoning level, from `low` to `max` |
| `skills` | The skills to preload into the agent's context |
| `mcpServers` | The MCP servers available to the agent (chapter 13) |
| `hooks` | Hooks that apply only while the agent is working (chapter 12) |
| `memory` | A persistent memory for the agent: `user`, `project` or `local` |
| `background` | With `true` the agent always runs in the background |
| `isolation` | With `worktree` the agent works in a temporary Git worktree |
| `color` | The color the agent shows up with in the interface |

`memory` and `isolation` change behavior more than the others. With `memory: project` the agent gets a `.claude/agent-memory/<agent>/` folder where it notes what it learns from one run to the next; with `user` the folder lives in `~/.claude/agent-memory/<agent>/`, and with `local` in `.claude/agent-memory-local/<agent>/`, which you keep out of Git. With `isolation: worktree` the agent starts in a temporary worktree created from the default branch, so its changes don't touch your working copy; if it changes nothing, the worktree is deleted automatically. We come back to this in section 10.8 and in chapter 20.

For agents that come from a plugin, `hooks`, `mcpServers` and `permissionMode` are ignored: a plugin can't raise its own permissions.

### The body, that is, the system prompt

Everything below the frontmatter is the agent's system prompt. A good prompt has four parts: who the agent is, what it has to do when it's called, how it should format the response, and what it must not do. The response format is the part people neglect most, and it's the part you read, or the main session reads: a report with file and line is usable right away, an 800-word essay isn't.

A final checklist, meaning the questions the agent should ask itself before answering, often separates a generic report from a useful one. Claude generates one when you ask it to write the agent: reread it.

## 10.4 Creating an agent with Claude

Up to version 2.1.197 the `/agents` command opened a guided wizard for creating agents. Since 2.1.198, released on July 1, 2026, the wizard is gone: `/agents` only prints a reminder telling you to ask Claude or to edit `.claude/agents/` and `~/.claude/agents/` directly. If you find tutorials with screenshots of the "Create new agent" menu, they predate that version.

The fastest way is to ask Claude to write the file. Describe the agent precisely: what it checks, which tools it needs, which model, where to save it. For the Photogallery, the Part VI project, you'd ask for a reviewer of the Laravel API controllers like this:

```text
create a project subagent called laravel-controller-reviewer in .claude/agents/.
It does the code review of the controllers in backend/app/Http/Controllers/Api/V1/.

For each controller I pass it, it must check that:
1. every endpoint that receives input uses a Form Request in app/Http/Requests/ and reads only $request->validated()
2. there is a Pest test in tests/Feature/Api/V1/ that calls the endpoint
3. actions on a user's resources go through a Policy in app/Policies/
4. endpoints that modify data check the Sanctum token's ability with tokenCan()
5. errors follow the envelope in docs/DESIGN.md §11.1

Tools: only Read, Grep and Glob, it must read and not modify.
Model: sonnet, it's a technical review.
Report: one line per problem with file:line and fix, then the verdict APPROVED or NEEDS_CHANGES. 300 words max.
```

Claude writes `.claude/agents/laravel-controller-reviewer.md` with the frontmatter, the structured system prompt, the checklist and the report format. The result looks something like this:

```markdown
---
name: laravel-controller-reviewer
description: Reviews the Laravel API controllers in backend/app/Http/Controllers/Api/V1/ for validation, tests, policies, Sanctum abilities and the error envelope. Use it after creating or modifying a controller, before committing.
tools: Read, Grep, Glob
model: sonnet
color: orange
---

You are a senior Laravel 13 API reviewer. You receive one or more Photogallery controllers.

For each public method, check that:

1. Input comes from a Form Request in app/Http/Requests/<Resource>/ and the controller uses only $request->validated().
2. There is a Pest test in tests/Feature/Api/V1/ that calls the endpoint, with at least one error case.
3. Actions on a user's resources are authorized by a Policy in app/Policies/.
4. Endpoints that modify data check the token's ability with tokenCan().
5. Responses use an API Resource and errors follow the envelope in docs/DESIGN.md §11.1.

Before answering, ask yourself: did I open the test I'm citing? Does the line I'm pointing to actually exist?

Report format:
- one line per problem: file:line, problem, proposed fix
- at the end, the verdict: APPROVED or NEEDS_CHANGES

Don't modify files. 300 words at most.
```

<!-- TODO screenshot: il file .claude/agents/laravel-controller-reviewer.md aperto nell'editor, con frontmatter e system prompt visibili (sostituisce le vecchie figure del wizard /agents, rimosso in v2.1.198) -->

You can also write it by hand: once you understand the structure, it's quicker to copy an existing one and change it.

### Reviewing the file

The first file Claude generates is a good starting point, almost never the final one.

The paths. Claude sometimes includes files that exist only in the project it started from, or makes them up. Every path in the prompt has to actually exist, or the agent wastes turns looking for it.

The checklist. Add the checks that are missing and make sure the ones you asked for are all there, with the same level of detail. In the Laravel reviewer the tricky one is the fourth: if Claude boils it down to a generic "check authentication," an endpoint protected by `auth:sanctum` but without `tokenCan()` passes the review. In that case, rewrite the item by hand.

The report format. You decide the length: for a controller, a numbered list of problems with file and line plus the verdict is enough.

Once you're happy with the file, commit it. From then on it's part of the repository like `CLAUDE.md`, and `/doctor prompt-audit` checks it along with rules and skills when you're hunting for stale or conflicting instructions.

### Trying it out

Claude Code watches `.claude/agents/` and `~/.claude/agents/`: a file added or changed while the session is open takes effect from the next delegation, no restart needed. The exception is a new folder: if `agents/` didn't exist when you started the session, exit and start again. To find out which agents it sees, ask:

```text
which subagents do you have available in this project?
```

`/context` shows them too, among the items taking up space in the context. Then call the agent by name:

```text
use the laravel-controller-reviewer agent to review backend/app/Http/Controllers/Api/V1/AlbumController.php
```

Claude launches the agent with the `Agent` tool. The agent reads the controller, opens the Form Requests in `app/Http/Requests/Album/`, looks for the tests and returns the report. In the session you see the report, not the reads that produced it; to see those, `Ctrl+O` opens the transcript with the tool calls.

If the agent doesn't kick in when you ask for a review without naming it, the problem is almost always the description: make it more explicit about when to use it.

::: {.callout .callout-prompt}
[Reusable prompt]{.callout-title}

Replace the parts in square brackets and paste the prompt into Claude Code. You get the agent file, ready to review.

```text
I want an agent for [task description].

Persona: [e.g. senior TypeScript code reviewer, SaaS data scientist]
Input: [what the agent receives, e.g. a controller file, a CSV dataset]
Report format: [e.g. problems sorted by severity, with file:line]
Allowed tools: [e.g. Read, Grep, read-only]
Model: [sonnet / opus / haiku / inherit]
Scope: [project / user]

Create the agent in .claude/agents/ (or in ~/.claude/agents/ if it's user-level).
```
:::

## 10.5 Background, permissions and /subtask

In interactive sessions, the subagents Claude launches run in the background by default, and Claude can't ask to run them in the foreground. While the agent works you keep typing; when it finishes, its report lands in the conversation and Claude uses it to carry on. Since October 2026 (version 2.1.302) the same holds in `-p` mode, in the SDK, in the desktop app and in VS Code.

There are three commands to remember. `/tasks` lists what's running in the background, with the status of each job. `Ctrl+X Ctrl+K` stops all background subagents in one go. `Ctrl+B` sends a job that's holding up the turn to the background, for example a long `Bash` command; if you use tmux, press it twice.

A background subagent may need a permission, for example to run a command your rules put under `ask`. The request doesn't get stuck in its context: it shows up in the main session, and you answer there as you would any other confirmation. It works the other way too: the `deny` rules you write in chapter 11 apply to subagents as well, so an agent can't do what you've forbidden the session to do. A `deny` rule blocks in every mode, `bypassPermissions` included.

A subagent can in turn launch other subagents, up to three levels below the main conversation (you change the limit with `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`). In practice two levels, a coordinator that launches reviewers, cover almost everything.

### /subtask, when you need the context

A normal subagent starts from scratch, and that's what you want for a review. Sometimes, though, you want to delegate a piece of work that depends on what the two of you have discussed in the last half hour. That's what `/subtask` is for:

```text
/subtask write the Pest tests for the two upload edge cases we just talked about, without touching the controller
```

`/subtask` launches a subagent that inherits the whole conversation. It works in the background like the others, but it knows everything you know. It's different from a skill with `context: fork` (chapter 9), which starts without the history, and from `/fork`, which copies the conversation into a new background session instead of opening a subagent (chapter 15).

## 10.6 Community agents, through plugins

You don't have to write every agent from scratch. On GitHub you'll find collections of ready-made agents, by language, framework and domain: reviewers, security auditors, database experts, documentation writers.

The first edition suggested cloning these collections into a folder under `~/.claude/`. Today it's better to install them through a plugin: you install it from a marketplace with one command, update and disable it without touching the project's files, and its agents take the plugin's name as a prefix, so they don't collide with yours. The official marketplace is called `claude-plugins-official` and it's already configured. Superpowers, which you installed in chapter 8, uses subagents in its development flow with built-in code review. Chapter 14 explains how plugins work and how to build one.

You can still copy by hand a `.md` file you found in a repository, but you lose updates and any record of where it came from.

### Read before you install

Installing an agent means telling Claude to follow its instructions in your environment, with the tools it declares. It's the same risk as adding an npm dependency without looking at it.

Before you install an agent, or a plugin that contains one, open the file and check three things. The system prompt: does it ask to read files outside the project, contact external addresses, collect credentials? The tools: if `Bash` is there, the agent's instructions can turn into commands on your machine, and there has to be a reason for it. If `tools` is missing altogether, the agent has everything the session has. The source: who maintains the repository, for how long, how active it is. A repository with no history and an unknown author deserves more caution than a well-known project.

::: {.callout .callout-warning}
[Warning]{.callout-title}

A malicious agent can instruct Claude to read `.env`, SSH keys and tokens and slip them into its report under the label of "diagnostics." That's prompt injection, the same class of problem that affects every LLM-based system. Always read the file before installing it, try it in a throwaway project, and keep the `deny` rule on `Read(./.env)` from chapter 11: it applies to subagents too.
:::

For user level versus project level, the rule from section 10.3 applies: an agent you've adapted to your stack goes in `.claude/agents/` and in the repository, so the team works with the same reviewer.

## 10.7 When to use what

At this point you have CLAUDE.md, custom commands, skills and agents. Part IV brings three more tools that solve related problems: permission rules (chapter 11), hooks (chapter 12) and MCP servers (chapter 13).

| Need | Tool | Chapter |
|---|---|---|
| "Always remember this project's conventions" | `CLAUDE.md` | 7 |
| "When I type /X, run this prompt" | Custom command or skill | 8, 9 |
| "A reusable procedure with templates and scripts" | Skill | 9 |
| "Delegate this task to a specialist with its own context" | Agent | 10 |
| "This must never happen" | `deny` rule | 11 |
| "On every change, no exceptions, do Y" | Hook | 12 |
| "Connect to an external system: database, API, GitHub" | MCP server | 13 |
| "Give all of this to the team as one package" | Plugin | 14 |

About the second row: from chapter 8 you know that a file in `.claude/commands/` and a skill in `.claude/skills/` create the same slash command, and that for new work a skill is the better choice.

The decision tree follows the same order:

```text
Do you want to change how Claude behaves?
│
├─ It's "remember X" or "always follow this convention"
│   └─ CLAUDE.md
│
├─ It must always happen, on every event, without the model deciding
│   ├─ it's a simple ban on a tool or a file  → deny rule
│   └─ it needs logic or an action (format, notify, block on a condition)  → hook
│
├─ It's "when I type /X, do Y" (a recurring prompt)
│   └─ custom command or skill
│
├─ The procedure needs supporting files, templates or scripts
│   └─ skill
│
├─ You want to delegate a task with an isolated context and limited tools
│   └─ agent
│
└─ Claude has to talk to an external system (database, REST API, GitHub)
    └─ MCP server
```

### The most common mistakes

Using a skill where you needed an agent. A long task that produces a lot of intermediate output and clutters the main context is almost always a job for an agent. A skill is fine for a light procedure you want to keep in the flow of the conversation.

Using an agent where a command would do. If you're automating a simple, repeated prompt like "add JSDoc comments to this file," a `/jsdoc` is faster and cheaper. An agent starts over from scratch and has to reread everything, so it takes longer.

Putting everything in `CLAUDE.md`. It's fine for permanent conventions, much less so for procedures: a twenty-step sequence in there gets loaded into every session, even when it's not needed, and is better off in a skill or an agent.

Trusting an instruction with a real constraint. "Never touch the migration files" written in `CLAUDE.md` or in an agent's prompt steers Claude, but it doesn't guarantee anything. For a guarantee you need a permission rule or a hook, or an agent without the tools to write.

### Combinations

In real work these tools are used together. A `/review` command that launches the code-reviewer on the files in the last commit: the command is the shortcut, the agent does the work. A performance-analysis skill that, with `context: fork`, runs the analysis in a subagent and returns the report. A review agent that follows the project's conventions because `CLAUDE.md` reaches it anyway: it knows nothing about the main session, but it does know the project's rules. The exceptions are Explore and Plan, which start without it, and agents with `omitClaudeMd` in their frontmatter.

## 10.8 Orchestrating several agents

Agents are at their best when Claude coordinates more than one. You'll use this pattern in full in Part VI, with the Photogallery, but it's worth understanding how it works here.

### The idea

You have to implement a complete feature, from the API to the review. If you do everything in sequence in the main session, the context fills up and quality drops as the conversation grows. With several agents the work splits up like this:

1. an architect agent analyzes the requirements and returns the structure: classes, responsibilities, files to touch;
2. an implementer agent writes the code from that structure, without the discussion that produced it;
3. a test-writer agent writes the tests from the code and the spec, not from the conversation;
4. a code-reviewer agent rereads the finished code on the actual files, without the point of view of whoever wrote it;
5. the main session coordinates, decides when the results conflict and presents the result to you.

The advantage comes from the clean context. The code-reviewer doesn't know you spent three hours on that code, and the test-writer doesn't remember the similar test from half an hour ago. Each agent works with a small, focused context, and quality stays more consistent than in a single session that piles up hours of conversation.

### In parallel

Independent tasks run together. In chapter 19, the review of each Photogallery wave launches four agents in parallel, all read-only: security, performance, API consistency and test coverage. Then the main session merges the four reports in order of severity. Since subagents already run in the background, the session stays free in the meantime, and `/tasks` shows you how far along they are.

### When two agents write to the same files

Four read-only reviewers work on the same code without any trouble. If instead the implementer and the test-writer modify the same working copy at the same time, one overwrites the other's changes, or reads a file halfway through an edit. The result is tests that fail for reasons neither of them caused alone.

There are two fixes. The first is to split the work so two agents never touch the same files at the same time, or to have them work in sequence. The second is to give each one its own copy of the repository with a Git worktree: that's what `isolation: worktree` in the frontmatter does, and chapter 20 uses it to run the Photogallery waves in parallel and then merge the branches.

### A word of caution

More agents means more complexity, and many tasks don't justify it: for a refactoring on one file, a single session is faster. Multi-agent work pays off when the task is big and splits into parts that are largely independent. A rule of thumb: if Claude needs less than five minutes, don't launch an agent; if it needs half an hour, an isolated context almost always repays the setup time. In Part VI these agents work on the Photogallery's implementation waves and, in chapter 22, on hunting down orphan tasks before the deploy.

## Summary {.unlisted}

- A subagent is a Claude instance with a separate context, its own system prompt and, if you choose, limited tools. A skill works in the main context; an agent opens a new one and hands you back only the report.
- An agent is a Markdown file in `.claude/agents/` (project, to commit) or `~/.claude/agents/` (user). Only `name` and `description` are required; `tools`, `model` and the report format in the prompt are the choices that matter most.
- The `/agents` wizard has been gone since version 2.1.198: ask Claude to write the file, then reread paths, checklist and format.
- Subagents run in the background: you follow them with `/tasks`, stop them with `Ctrl+X Ctrl+K`, and their permission requests show up in the main session. `/subtask` delegates a task that needs the whole conversation.
- Community agents are installed through plugins (chapter 14), after you've read their prompt and tools.
- Several agents that read can work in parallel; several agents that write to the same files step on each other's toes and must be kept apart, with `isolation: worktree` or with the worktrees from chapter 20.

## Exercise {.unlisted}

Create your first read-only agent, for your own stack or for the Photogallery.

Pick the check you find yourself repeating most often, the one where you'd like a reviewer who didn't watch the code being born: a code review of the controllers, a security analysis, a test-coverage check. Use the reusable prompt from section 10.4 to have Claude write the file in `.claude/agents/`, with `tools: Read, Grep, Glob`. Reread it and add at least one check specific to your project that Claude didn't think of.

Then try it twice on a real file. The first time, call it by name. The second time, just ask "review this file" without naming it, and see whether Claude picks it on its own; if it doesn't, rewrite the description. Finally, type "use the [name] agent to fix the first problem it found, and don't modify the file yourself."

The exercise is done when the agent shows up in the answer to "which subagents do you have available?", has produced two reports in the format you chose, and answered the fix request by saying it can't modify files, with `git status` showing no changes other than the agent file. Commit the file if you want to share it with the team.

If you want a second prompt template, with persona, input, report format and tools, you'll find it in the `cap-09/` folder of the `github.com/hidran/claude-code-book-snippets` repository (first-edition numbering).
