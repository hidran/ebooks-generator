# Chapter 8. Custom commands and the Superpowers plugin

::: {.chapter-goals}
[What you'll learn]{.callout-title}

- When a prompt you keep retyping should become a custom command, and how to write one.
- How to pass arguments and context to the command: `$ARGUMENTS`, `$0`, `` !`command` `` and `@file`.
- Three commands to start using today, plus a `/commit` that keeps your Git history clean.
- What the Superpowers plugin gives you and how to install it from the official marketplace.

[Prerequisites]{.callout-title}

Chapters 1-7, and at least one `CLAUDE.md` you've written (chapter 7).

:::

Think about how many times you've typed "run the tests and tell me which one fails" or "make a commit with a decent message." The wording shifts a little every time: one day you ask Claude to "list the unused imports," the next to "find the useless imports," and it does two slightly different things. Your instructions drift with how rushed you are and what you happen to remember, and the results drift with them.

A custom command fixes this in the most boring way possible: you write the prompt once, carefully, save it in a file, and from then on you call it with a slash. The prompt stays the same, so the behavior stays predictable. My rule: the third time I rewrite the same prompt, I turn it into a command. Not before, because the first two times are how I figure out the right wording.

There's a team angle too. Project commands live in the repository, so anyone who opens Claude Code in that folder (a colleague, a freelancer who just joined, you on another machine) finds them ready to go, each with its description in the menu.

## 8.1 What a custom command is

A custom command is a Markdown file in a specific folder. The file name becomes the command name: `review-types.md` becomes `/review-types`. When you invoke it, Claude Code takes the file's contents and uses them as the prompt, as if you'd just typed them yourself.

::: {.callout .callout-deep-dive}
[Under the hood]{.callout-title}

Custom commands are now part of skills. A `.claude/commands/deploy.md` file and a skill at `.claude/skills/deploy/SKILL.md` both create `/deploy` and behave the same way. Files in `.claude/commands/` are the older format and still work; for new work the docs recommend skills. If a command and a skill share a name, the skill wins. I use `.claude/commands/` here because it's the fastest way to get started. Chapter 9 covers the skill format, which does everything a command does and a few things more (supporting files, automatic invocation, running in a separate context).
:::

### The structure

The minimal format is YAML frontmatter plus a body:

```markdown
---
description: Short description shown in autocomplete
---

Command body: the instructions Claude will carry out.
You can write a structured prompt here, as long as you like,
with lists, conditions, output criteria.
```

Every frontmatter field is optional, but you'll use two of them almost every time. `description` is the line you see in the menu when you press `/`: keep it short and clear, because it's what you and your colleagues read when you're hunting for the right command. Claude reads it too, and section 8.3 explains why that matters. `argument-hint` describes the argument the command expects and shows up in autocomplete after the name.

Command files accept the same frontmatter as skills, except `name` and `paths`. So you can already use `allowed-tools` (the tools Claude may use without asking for permission while the command is active), `model` and `effort`, and `disable-model-invocation`, which you'll meet in section 8.3. Chapter 9 goes through all of them.

### Where to save the files

Commands live in two places: `~/.claude/commands/` for personal ones, available in every project on that machine, and `.claude/commands/` inside the repository for project ones, committed along with the code.

```text
~/.claude/commands/          # personal, always available
├── fix-tests.md
├── clean-imports.md
└── spawn-pr.md

mio-progetto/.claude/commands/   # project, committed to the repo
├── analyze-schema.md
└── deploy-staging.md
```

Here's how I decide: if the command mentions paths, scripts or conventions specific to that project (deploying to staging, a report from the database), it belongs to the project. If it would work on any JavaScript or Python project (reviewing types, cleaning up imports), it goes in your personal folder.

You can organize commands in subfolders. A subfolder adds a prefix to the name: `.claude/commands/frontend/component.md` becomes `/frontend:component`. Once a project has more than ten or so commands, the menu gets much easier to scan.

### A complete example

Here's a full command for TypeScript projects:

```markdown
---
description: Review the types in the current file and suggest improvements
argument-hint: (optional) path of the file to analyze
---

Read the file we're working on (or $ARGUMENTS if given).
Check the quality of the TypeScript types:

- No hidden or implicit `any`
- Explicit return types on every public function
- Generics where they'd be appropriate
- Exhaustive union types with a discriminant when possible

For each problem you find: give the line number, explain why
it's a problem and propose a specific fix. Don't apply
anything, just a report with the proposals.
```

Save it as `~/.claude/commands/review-types.md` and it's available in all your sessions. Next time you're working on a TypeScript file, type `/review-types` and you get a review with the same criteria and the same format as always.

### Why a file instead of a hand-typed prompt

Saving keystrokes is the least interesting part. What matters more is that you and your colleagues use the same prompt with the same output criteria, and that the prompt goes through Git: when you add a criterion to the type review a month from now, the commit `feat: add generics check to review-types` tells everyone when and why the command changed. And a command doesn't have to be three lines long. It can describe a sequence of steps, read files, and stop halfway to ask for confirmation, like the commands in section 8.3.

## 8.2 Writing your first custom command

The most direct route is to start from a prompt you already use. Take it as is, paste it into a Markdown file, add the frontmatter, and you're done.

### Create the folder and the file

Create the folder if it doesn't exist yet, then the file. The file name becomes the command name, so to get `/clean-imports`:

```bash
# personal command
mkdir -p ~/.claude/commands
touch ~/.claude/commands/clean-imports.md

# or project command, from the repository root
mkdir -p .claude/commands
touch .claude/commands/clean-imports.md
```

Open the file and write the frontmatter and body:

```markdown
---
description: Sort and clean up the imports in the current file
---

Read the file we're working on.

Sort the imports into three groups separated by a blank line:
1. Standard libraries and node_modules (e.g. `react`, `lodash`, `fs`)
2. Project aliases (e.g. `@app/`, `@shared/`, `~/`)
3. Relative imports (e.g. `./Component`, `../utils`)

Within each group, sort alphabetically.
Remove imports that aren't used in the file.

Show me the diff before applying any change.
Wait for my confirmation.
```

### Try the command

If Claude Code was already open when you created the file, run `/reload-skills`: it rescans the skill folders and the command folders, so you don't have to quit and restart. Otherwise, close the session and open it again.

Type `/` and start typing `clean`. `/clean-imports` shows up in the menu with the description from the frontmatter. Select it, press `Enter`, and Claude runs the prompt in the file.

### Arguments

Put `$ARGUMENTS` in the body and the command takes a parameter. If you type `/clean-imports src/services/auth.ts`, the text `src/services/auth.ts` replaces `$ARGUMENTS` before the prompt reaches Claude.

Here's a command designed to take an argument:

```markdown
---
description: Analyze the given file and propose refactorings
argument-hint: path of the file to analyze
---

Read the file $ARGUMENTS.

Analyze the code and propose refactorings along these lines:
- Functions that are too long (>30 lines): suggest how to split them
- Duplicated logic: identify repeated patterns
- Non-descriptive names: propose better names for variables and functions
- Cyclomatic complexity: flag functions with more than 4 branches

For each proposal: show the current code, the suggested code,
and the reason in one line.
```

Save it as `~/.claude/commands/refactor-file.md` and use it like this:

```text
/refactor-file src/components/DataTable.tsx
```

When there's more than one argument, you can pick them by position. `$ARGUMENTS[0]`, or the short form `$0`, is the first one, `$1` the second, and so on: numbering starts at zero. With a body that says "Analyze the file $0 and focus on $1," the command `/refactor-file src/api/client.ts duplication` puts the path in `$0` and the word `duplication` in `$1`. The frontmatter also accepts an `arguments` field to name positional arguments; you'll see it in chapter 9.

If the body has no placeholder at all, the arguments don't get lost: Claude Code appends them to the end of the prompt as `ARGUMENTS: <value>`.

### Dynamic context: `` !`command` `` and `@file`

With a static prompt, Claude often makes two or three tool calls before the real work starts: `git status`, the diff, the spec file. You can have that data waiting for it instead.

A shell command written as `` !`command` ``, at the start of a line or after a space, runs before the prompt reaches Claude, and its output takes the placeholder's place. For several lines of shell there's a fenced block that opens with ` ```! `. The timeout is the Bash tool's, two minutes, so no long-running commands.

An `@path/to/file` reference in the body attaches that file to the prompt, just as when you type it by hand in the session.

Here's a project command for the Photogallery that uses both:

```markdown
---
description: Compare the current diff against DESIGN.md
allowed-tools: Bash(git diff *)
---

## Changes in progress

!`git diff --stat`

## Reference spec

@docs/DESIGN.md

Compare the changes against the spec: column types and nullability,
response shapes, validation rules, status codes.
List every deviation with file and line. If you find none, say so.
```

The Photogallery companion repository has a similar command, `.claude/commands/spec-check.md`, which asks Claude to run `git diff` itself and read `docs/DESIGN.md`; with injection, those steps go away.

::: {.callout .callout-warning}
[Warning]{.callout-title}

`` !`...` `` commands run on your machine the moment you invoke the command, before Claude sees anything. If you install commands or skills written by someone else, read the file before you use it. To turn injection off entirely, the setting is `"disableSkillShellExecution": true`.
:::

## 8.3 Three custom commands to use right away

Three everyday situations: failing tests, messy imports, work that needs to go into a PR. Save the commands in `~/.claude/commands/` and adapt them to your stack.

### /fix-tests, a diagnosis and a proposed fix for every broken test

The command runs the suite, and for each failure it reads the code, classifies the cause and proposes a fix. It doesn't apply anything: you get a list to read.

Save it as `~/.claude/commands/fix-tests.md`:

```markdown
---
description: Run the tests, diagnose the failures and propose fixes
---

Run the project's test command. Look at package.json to
figure out which script to use (usually `pnpm test`, `npm test` or
`pytest`). If you can't tell, ask me.

For each failing test:
1. Read the test file and the file under test
2. Identify the cause of the failure from these categories:
   - API change: the function signature has changed
   - Code bug: the code doesn't do what the test expects
   - Obsolete test: the test checks behavior that was removed on purpose
   - Environment problem: missing dependency, unset variable
3. Propose the specific fix with a diff of the needed changes

Don't apply anything. Give me a structured list with:
- Name of the failing test
- Failure category
- Cause identified
- Proposed fix (diff)

At the end, tell me how many tests there are in total, how many pass and how many fail.
```

On a Node project with two broken authentication tests, the output looks something like this:

```text
> /fix-tests

pnpm test
  FAIL  src/auth.test.ts
    x login with wrong credentials → expected 401, received 200
    x expired token → expected 403, received 500

[1] auth.test.ts:42  Obsolete test
    The JWT mock still uses the fixed expiry from before the refactoring
    diff: -Date.now()  +Date.now() - 3600000
[2] auth.test.ts:87  Code bug
    The middleware doesn't handle malformed tokens
    diff: +if (!token) return res.status(403).json(...)

Total: 24 tests, 22 pass, 2 fail
```

The categories are there because an obsolete test and a code bug get fixed in opposite directions: in the first case you change the test, in the second the code. When Claude has to state the category, the decision stays with you, and you don't let it make the test pass whichever way is easiest.

### /clean-imports, the full version

This is the command from section 8.2. The version I keep in `~/.claude/commands/` adds a block of rules before the line about the diff:

```markdown
Rules:
- Alphabetical order within each group
- Remove imports not used in the file (check before removing)
- Keep existing comments next to the imports they refer to
- Don't touch anything else in the file
```

If the project already has a linter that sorts imports (ESLint with `import/order`, Biome), you don't need the command: run the linter.

### /spawn-pr, a PR from your current work

The command gathers the branch's commits, writes a title and description, and opens the pull request on GitHub, but only after you confirm. It uses injection so it starts with the data already in hand.

Save it as `~/.claude/commands/spawn-pr.md`:

````markdown
---
description: Create a GitHub PR with title and description from the current work
disable-model-invocation: true
allowed-tools: Bash(git log *) Bash(git diff *) Bash(git branch *)
---

## Context

- Branch: !`git branch --show-current`
- Commits to include: !`git log --oneline origin/HEAD..HEAD`
- Files touched: !`git diff --stat origin/HEAD...HEAD`

## What to do

Generate:
- PR title: 50 characters max, present tense, no trailing period.
  Examples: "Add user authentication", "Fix null check in DataTable"
- PR description in Markdown with these sections:
  - `## Changes`: what was changed and how
  - `## Motivation`: why these changes were needed
  - `## Testing`: what was tested and how to verify it works

Show me the proposed title and description and wait for my approval.

Only after approval:
1. Run `git push origin HEAD`
2. Run `gh pr create --title "<title>" --body "<description>"`
3. Show me the URL of the opened PR

If `gh` isn't installed, tell me instead of going ahead.
````

Notice what I put in `allowed-tools`: only the Git commands that read. `git push` and `gh pr create` stay out, so they go through the session's normal permissions and, if you're working in Manual mode, you're asked about each one. The permission granted by `allowed-tools` only lasts while the command is active and resets with your next message.

::: {.callout .callout-warning}
[Warning]{.callout-title}

Since commands and skills are the same thing, Claude can decide on its own to use a command when its description matches what it's doing. For a report, that's fine. For a command that pushes, opens PRs or deploys, it isn't: with `disable-model-invocation: true` in the frontmatter, the command only runs when you type it. Put it on everything that has effects outside your editor.
:::

## 8.4 The Superpowers plugin

So far you've written the commands yourself. Superpowers is an open source plugin by Jesse Vincent (`obra/superpowers` on GitHub) that brings an already-codified way of working into Claude Code, written and refined by someone else. A plugin is a package that can contain skills, agents, hooks and MCP servers; you install it once and get the whole bundle.

### What's in it

Superpowers' entry in the official marketplace describes it as brainstorming, subagent-driven development with built-in code review, systematic debugging, red/green TDD, and instructions for writing and testing new skills. In practice it's mostly skills:

- brainstorming before implementing (`brainstorming`): questions, alternatives, and only then a design;
- subagent-driven development (`subagent-driven-development`): each task in the plan goes to a subagent, with a code review before the next task;
- systematic debugging (`systematic-debugging`): reproduce, isolate, form a hypothesis, test it, instead of trying random fixes;
- red/green TDD (`test-driven-development`): first a failing test, then the minimum code that makes it pass;
- writing skills (`writing-skills`): how to design one and how to check that it works.

You don't have to invoke these skills yourself: Claude loads them on its own when the situation matches their description. Ask for a new feature and brainstorming kicks in; report a bug and systematic debugging kicks in. If you want to call one by hand, a plugin's skills carry the plugin's prefix, in the form `/superpowers:<skill-name>`.

You'll find the same rhythm in the Photogallery (Part VI): spec, tasks, execution in waves with a review between one task and the next. You don't need Superpowers to follow the book, but it gets you used to working that way.

### Installing it

Superpowers is in Anthropic's official marketplace, `claude-plugins-official`, which Claude Code adds by itself on your first interactive session. From the prompt:

```text
/plugin install superpowers@claude-plugins-official
```

A plugin installs in one of three scopes: user (all your projects), project (saved in the repository's configuration, so shared with the team) or local (just you, just this project). User is fine for trying it out.

Alternatively, you can go through the author's marketplace:

```text
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```

If you prefer menus, `/plugin` opens the manager with the Discover, Installed, Marketplaces and Errors tabs: search for "superpowers" in Discover and install from there.

After installing, run:

```text
/reload-plugins
```

Without the reload, the current session doesn't see the new skills yet. To check, `/plugin list` shows the installed plugins and `/skills` lists the available skills: the Superpowers ones appear with their prefix.

<!-- TODO screenshot: output di /skills dopo l'installazione di Superpowers, con le skill del plugin elencate -->

### What it costs in context

Each skill's name and description stay in the context window even when you're not using them, because that's how Claude knows when to pull them in. The `/plugin` manager shows an estimate of the cost before you install, and in chapter 15 you'll see `/context` and `/skill-doctor`, which tell you which skills are worth the space they take. With Superpowers the math works out; with ten plugins installed out of curiosity, it doesn't.

How a plugin is built inside (the `.claude-plugin/plugin.json` manifest, the `skills/`, `agents/` and `hooks/` folders) is covered in chapter 14, where you build your own.

## 8.5 The atomic commit pattern with /commit

When you're working with an agent that changes a dozen files in a few minutes, your Git history gets messy fast. At the end of the session you're left with one huge commit, or with four commits called "wip." A well-written `/commit` command fixes that, and once you're in the habit you won't go back.

### The command

A personal `/commit` that always asks for confirmation:

````markdown
---
description: Propose an atomic commit with a Conventional Commits message
disable-model-invocation: true
allowed-tools: Bash(git status *) Bash(git diff *)
---

## Repository status

!`git status --short`

## Staged changes

!`git diff --cached`

## What to do

1. If nothing is staged, tell me and stop.
2. If the staged changes contain more than one logical change,
   tell me and propose how to split them. Don't commit.
3. Pick the type: feat, fix, refactor, test, docs, chore, perf.
4. Write the message in Conventional Commits format: title
   in the imperative, no trailing period, under 72 characters; optional
   body explaining why the change was made.
5. Show me the files included and the proposed message, and wait for my confirmation.
6. Only after confirmation, run `git commit`. Don't push.
````

Save it as `~/.claude/commands/commit.md`. The command works on whatever you've staged, and that's deliberate: you decide what goes into the commit, Claude writes the message and warns you if you've lumped two different things together.

The Photogallery companion repository has a project version at `.claude/commands/commit.md`: it also picks the scope from the files touched (`api`, `backend`, `frontend`, `filament`, `pipeline`, `db`), cites the relevant `DESIGN.md` sections in the body, and commits without asking for confirmation, because there the commit comes at the end of a task that's already been reviewed.

If you'd rather not write it yourself, the official marketplace has a `commit-commands` plugin (`/plugin install commit-commands@claude-plugins-official`) with three ready-made commands: `commit`, `commit-push-pr` (commit, push and PR in one step) and `clean_gone` (cleans up local branches whose remote has been deleted). Like skills, a plugin's commands take the plugin's prefix, so you run them as `/commit-commands:commit` and they don't clash with your own `/commit`.

### What happens when you run it

With three files staged after an authentication fix, the response looks something like this:

```text
> /commit

Staged files (3):
  M  src/auth/middleware.ts     (+12 / -3)
  M  src/auth/auth.test.ts      (+18 / -5)
  M  src/auth/token.service.ts  (+4 / -1)

Proposed message:
  fix: handle expired and malformed tokens

  - middleware returns 403 for malformed tokens
  - JWT mock resets expiry correctly in tests
  - TokenService handles null/undefined edge cases

Confirm, edit it, or cancel?
```

The Conventional Commits format puts a prefix (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`) in front of a short title, followed by an optional body like the one above.

### Why atomic commits

An atomic commit contains a single logical change, one you can describe in a sentence and that stands on its own. Without that discipline, a day with an agent produces a log like this:

```text
a1b2c3d WIP
d4e5f6a still wip
g7h8i9j finally works
j0k1l2m some stuff
```

With `/commit` after each piece of work, the same day turns into:

```text
a3f1c2d feat: add format_values helper for stats output
b7e4d8a feat: add write_markdown_report function
c2b9f1e feat: implement analyze-column python script
d8e3a7c test: add tests for analyze-column
e4c1b9f docs: add slash command analyze with description
```

The difference has practical consequences. `git bisect` works, because every commit is a consistent state of the project. `git revert e4c1b9f` removes only the command's documentation without touching the tests or the implementation. Reviewers read one change at a time instead of a 400-line diff with everything mixed together. And when an agent goes down the wrong path, you know exactly how far back to go.

### Read the message before you confirm

Read the message every time, even when you trust it. It stays in the project's history: `feat: update auth` tells you nothing six months from now, while `feat: add refresh token rotation on expiry` tells you what to look for when the bug shows up in production. And check the type: if Claude proposes `refactor:` while you're adding a feature, change it to `feat:`, otherwise the log gets less useful for anyone (person or changelog tool) who filters commits by type.

### When not to use it

The command works well when what you've staged already hangs together. Sometimes it's better to do it by hand. If you changed two features in the same file, split them first with `git add -p` and run `/commit` for each. If your team uses a convention other than Conventional Commits, change the command (it's a file, you can edit it in a minute) or write the commit by hand. Merge commits, reverts and cherry-picks have their own context: better to handle them by hand.

### A typical day

With `/commit` and `/spawn-pr`, the session settles into a steady rhythm. You work with Claude on feature X, which touches four or five related files; you stage, run `/commit`, read, confirm. You move on to feature Y and repeat. When the branch is ready you run `/spawn-pr`: push, a PR with title and description, the URL in the reply. Three weeks later, `git log --oneline` brings you up to speed before you even open a file.

::: {.callout .callout-prompt}
[Reusable prompt]{.callout-title}

When you have a recurring workflow and don't know where to start, have Claude write the command for you:

```text
Create a custom command in .claude/commands/<name>.md for this
recurring scenario: <describe the workflow you often do by hand>.

The command must:
- Have frontmatter with a clear description (60 characters max)
- Have an argument-hint if it takes parameters
- Structure the instructions as numbered steps
- State explicitly whether to show a diff before applying
- Say whether to wait for confirmation or proceed automatically

Show me the complete file, ready to save.
```
:::

## Summary {.unlisted}

- A custom command is a `.md` file in `~/.claude/commands/` (personal) or `.claude/commands/` (project, to be committed) that becomes `/file-name`; subfolders add a prefix, as in `/frontend:component`.
- Commands have been folded into skills: the `.claude/commands/` format still works, `.claude/skills/<name>/SKILL.md` is the recommended one for new work and wins when names collide. Chapter 9 picks up from here.
- `$ARGUMENTS` receives all the text after the command, `$0` and `$1` the individual arguments; `` !`command` `` injects shell output before Claude reads the prompt, `@file` attaches a file.
- On commands with external effects (push, PR, deploy), set `disable-model-invocation: true`, and put only read-only commands in `allowed-tools`.
- Install Superpowers with `/plugin install superpowers@claude-plugins-official` followed by `/reload-plugins`; it brings skills for brainstorming, subagent-driven development with review, systematic debugging and TDD.
- A `/commit` that works on the staging area, proposes a Conventional Commits message and waits for confirmation gives you a Git history you can actually use with `bisect` and `revert`.

## Exercise {.unlisted}

Estimated time: 25 minutes. You need any Git repository with some pending changes.

1. Install Superpowers with `/plugin install superpowers@claude-plugins-official`, run `/reload-plugins` and check with `/skills` that its skills show up.
2. Save the `/commit` command from section 8.5 in `~/.claude/commands/commit.md`. Make a small change, stage it, run `/commit` and read the proposed message before confirming.
3. Find a prompt you've typed at least three times this week, turn it into a file in `~/.claude/commands/` with a `description` and, if needed, an `argument-hint`, then run `/reload-skills` and try it. If you want a starting point, the prompt in the `cap-07/` folder of the `github.com/hidran/claude-code-book-snippets` repository (first-edition numbering) generates a custom command from a scenario.

You're done when `git log -1` shows a commit with a Conventional Commits message created by `/commit`, and your new command appears in the `/` menu with its description.
