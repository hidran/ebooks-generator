# Chapter 7. CLAUDE.md, the project's memory

::: {.chapter-goals}
[What you'll learn]{.callout-title}

- Where `CLAUDE.md` files live and how the four levels add up.
- What to put in them so Claude actually follows it, and what to leave out.
- How to generate your first file with `/init` and keep it under two hundred lines with imports and rules in `.claude/rules/`.
- What happens when the repository already has an `AGENTS.md`.

[Prerequisites]{.callout-title}

A real project to try things on, even a small one. The data analysis project from chapters 4-6 works fine.

:::

Picture hiring a new developer every morning. You walk them through the project, which package manager you use, where the error-handling function lives, and they do good work all day. The next morning it's their first day again: they ask the same questions and fall back on the conventions they know, not yours.

That's Claude Code without a `CLAUDE.md`. Every session starts empty. Claude doesn't know that your project uses pnpm and not npm, that global state lives in `store/`, that tests are written with Vitest, that error messages are in Spanish. So it guesses, and it picks the most common solution, which often isn't yours.

`CLAUDE.md` is a Markdown file that Claude Code loads into the context at the start of every session, before your first prompt. You write down what you'd otherwise repeat every time: the build and test commands, the conventions, the "always do this" and "never do that" rules. You met it in chapter 2, in the table of mechanisms, under "text loaded into the context at session start". That definition explains both why it works and where it stops working.

## 7.1 What CLAUDE.md is

There's no special syntax and no required schema: it's plain Markdown, with headings and lists. Claude Code reads it at startup and the text stays in the context for the whole session, so it rides along with every message you send. After `/clear` the conversation starts from scratch and `CLAUDE.md` comes back in with the new session. After `/compact` the root file is re-read from disk, so the instructions written there don't depend on the summary.

### The four levels

Claude Code looks for instructions in four places:

| Level | Where it lives | Who sees it |
|---|---|---|
| Organization | macOS `/Library/Application Support/ClaudeCode/CLAUDE.md`, Linux and WSL `/etc/claude-code/CLAUDE.md`, Windows `C:\Program Files\ClaudeCode\CLAUDE.md` | Every user on the machine, managed by IT |
| User | `~/.claude/CLAUDE.md` | Only you, in every project |
| Project | `./CLAUDE.md` or `./.claude/CLAUDE.md` | The team, through Git |
| Local | `./CLAUDE.local.md` | Only you, in this project |

The organization level (managed policy) is rolled out by a company's IT department, with the rules that apply to everyone.

The user file holds the preferences you carry into every repository: the language Claude answers in, commit messages in English following Conventional Commits, the fact that you like short answers. It's optional, and plenty of people don't use it.

The project file is the one that matters most. It sits in the root, goes into Git, and anyone who clones the repository inherits the instructions along with the code. If you'd rather keep the root clean, put it in `.claude/CLAUDE.md`; the result is the same.

`CLAUDE.local.md` is your private version of the project file: the URL of your test environment, a local database whose name differs from your colleagues', a note on what you're working on this week. Add it to `.gitignore` as soon as you create it.

In a monorepo you can also put a `CLAUDE.md` in a subfolder, for example `frontend/CLAUDE.md` and `backend/CLAUDE.md`. Files in the folders above the one where you launch `claude` load at startup. Files in subfolders come in only when Claude reads a file in there, so whoever works on the frontend doesn't drag the backend rules along.

### How they combine

Claude Code doesn't pick one file: it loads all of them, from the most general to the most specific, and the model sees a single block of instructions. If your user file says "charts always use the dark theme" and a client project needs the light theme because the report gets printed, write it as an explicit exception: "in this project use the light theme instead of the dark one". Two instructions that contradict each other with no explanation leave Claude to choose on its own, and it doesn't always choose the one you meant. In chapter 15 you'll see `/doctor prompt-audit`, which finds these contradictions for you.

### How long it should be

The official recommendation is to stay under two hundred lines per file, for two reasons. The first is cost: that text takes up context in every session and is re-read on every turn, whether you need it or not. The second matters more: a long file gets followed less reliably. With three hundred lines of instructions, the five that really count get lost among the rest.

The technical limit is much higher (files up to 4 MiB load in full, larger ones are skipped), and even the one-million-token window would have room. But a long file is still a file that gets followed worse. When it grows, move the instructions that apply to a single area of the code into rules that load only when needed (section 7.5).

## 7.2 What to write in it

Start from one question: what does Claude need to know so it doesn't get this project wrong? It pushes you to pick only what changes the code Claude produces, instead of filling the file with everything you know.

Then write each instruction so it can be checked. "Use two-space indentation" works better than "format the code nicely"; "run `pnpm lint` before every commit" works better than "keep the code clean". You can check a verifiable instruction in the diff, and Claude knows when it has followed it.

The information that belongs in a `CLAUDE.md` almost always falls into six categories.

### The stack, with versions

Claude knows many versions of many frameworks. Without guidance it picks the one it has seen most often, which may not be yours.

```markdown
## Stack

- Runtime: Node.js 22 LTS
- Framework: NestJS 11
- ORM: Prisma 6 (PostgreSQL)
- Frontend: React 19 + TypeScript 5
- Styling: Tailwind CSS 4
- Test: Vitest 3 + Testing Library
- Package manager: pnpm (do NOT use npm or yarn)
```

The package manager line is the one that saves you the most trouble. If the repository uses pnpm and Claude runs `npm install`, you end up with a stray `package-lock.json` next to `pnpm-lock.yaml` and with versions that differ from the team's.

### Conventions you can't see in the code

Write down only the ones Claude can't work out for itself. If `tsconfig.json` has `"strict": true`, there's no need to repeat it.

```markdown
## Conventions

- React components: function components with TypeScript, no class components
- File names: kebab-case; React components in PascalCase
- Imports: absolute paths from `src/` with the `@/` alias
- Errors: Result<T, E> pattern, never bare throws
- Comments and docstrings in English
- No `console.log` in committed code: use `logger` from `src/utils/logger`
```

### The project's commands

This is where you see the difference between a Claude that runs the right command on the first try and one that tries `npm run build` because it's the most widespread default.

```markdown
## Commands

- Dev: `pnpm dev` (frontend on port 3000, API on 4000)
- Build: `pnpm build`
- Test: `pnpm test` (all) or `pnpm test:unit` (unit only)
- Lint: `pnpm lint && pnpm type-check`, always both before committing
- Migrations: `pnpm db:migrate` (never `prisma migrate deploy` by hand)
- Seed: `pnpm db:seed`, overwrites the data
```

### Things not to do

This is often the most useful section. Claude tends to do whatever looks like it works, even when it's wrong for your project, and explicit prohibitions close off the paths you've already ruled out.

```markdown
## NEVER do

- Don't install dependencies without discussing it first
- Don't edit `src/generated/`: Prisma generates it
- Don't call `fetch` directly: go through `src/lib/api-client.ts`
- Don't add `any` without a comment explaining why
- Don't use `Date.now()` in tests: use `vi.setSystemTime()`
```

### Patterns, with a reference example

If the project has recurring patterns that Claude might not follow on its own, describe them and point to the file to use as the model. Claude goes and reads it and copies the structure.

```markdown
## Architecture

- Data access through the repository pattern: model in `src/repositories/user.repository.ts`
- Writes in `commands/`, reads in `queries/`, never in the same file
- Input validation always with a Zod schema
- Forms: React Hook Form with zodResolver, no useState for form state
```

### The domain vocabulary

Every project has its own words, and "customer" can mean different things in the database, in the code and in meetings. Pinning the terms down keeps a misunderstanding from turning into a bug.

```markdown
## Domain

- "User" = registered person (`User` entity)
- "Customer" = company with an active contract (`Organization` entity)
- A user can belong to several organizations
- Order status: DRAFT → PENDING → PROCESSING → COMPLETED | CANCELLED
```

### Notes for colleagues, at no cost

Block-level HTML comments are stripped before the text reaches Claude. You can leave a note for whoever maintains the file (why a rule exists, who asked for it, where the rest lives) without spending context:

```markdown
## Rules

- Never modify the files in `data/`: work on copies in `tmp/`
- Every new function in `src/` has a test in `tests/`

<!-- Note for maintainers: the Python rules live in .claude/rules/python.md -->
```

### A real example: the Photogallery

The Part VI project has a `CLAUDE.md` written in English, like the rest of the documentation in the companion repository. Chapter 18 builds it step by step (section 18.4). Here's an excerpt, so you can see the shape of the rules:

```markdown
# CLAUDE.md — PhotoGallery Pro

> The project constitution. Loaded into every Claude Code session.
> Authoritative for HOW we work; defers to `docs/REQUIREMENTS.md` (what to
> build) and `docs/DESIGN.md` (technical blueprint) for content. Atomic work
> lives in `docs/TASKS.md`.

## Critical rules

1. Always read `docs/REQUIREMENTS.md` and `docs/DESIGN.md` before implementing
   tasks. If the task is ambiguous and the docs don't resolve it, stop and ask.
4. One task = one commit. Conventional Commits format: `<type>(<scope>): <subject>`.
5. Tests run before commits. No `--no-verify`, no `.skip`, no "tests later".
7. Every endpoint wraps its payload in `{ "data": ... }`. No exceptions.
8. Every primary key is UUID v7 via the `HasUuidV7` trait. Stored as `CHAR(36)`.
13. Tailwind v4 setup is non-negotiable. No `tailwind.config.js`, no
    `postcss.config.js`, no `autoprefixer`.
```

Almost every rule can be checked by looking at the diff: either the endpoint returns `{ "data": ... }` or it doesn't, either the primary key is a UUID v7 or it isn't. And many of them point to a document (`DESIGN.md`) instead of copying it. The full file is 391 lines, almost twice the target, and a good chunk of it concerns a single area of the code: the PHP style applies to `backend/`, the Tailwind rules to `frontend/`. Section 7.5 shows how I'd split it.

## 7.3 What not to write

A bloated `CLAUDE.md` is worse than a sparse one: it takes up context and dilutes the instructions that count. The most common mistakes come to six.

The first is API documentation: lists of endpoints, parameters, method signatures. That belongs in the code, in comments, in an OpenAPI file, and Claude reads it when it needs to.

Same goes for an inventory of functions ("the project has `getUserById()`, `createUser()`, `deleteUser()`..."). Claude finds them on its own by exploring the code. If a function has to be used in a particular way, write that down as a pattern, with the reference file.

Then there are tutorial-style explanations. Claude already knows what Prisma is and how a JWT works. "Why we picked this technology" is interesting to a new colleague, and for them there's the README or an ADR. `CLAUDE.md` is for instructions.

Credentials never go in it: API keys, tokens, passwords, connection strings with a username and password. The project file goes into Git, so onto the remote, and from there anywhere the repository gets cloned. Secrets belong in `.env` (kept out of Git) or in a secrets manager.

Roadmaps and temporary notes stay out too. "In March we'll add X" or "we're thinking about moving to PostgreSQL" don't change the code Claude writes today. They go in the task tracker or in the specs.

The last mistake is intentions with no rule behind them. "We try to write clean code" doesn't drive any decision. If you want small functions, write a rule that can be checked: "a function over 30 lines gets flagged with a `TODO:REFACTOR`".

For every section you're about to add, the test is this: without this information, would Claude write different, wrong code? If the answer is no, you don't need the section.

::: {.callout .callout-warning}
[Warning]{.callout-title}

`CLAUDE.md` steers Claude, but it doesn't bind it. It's text in the context: it usually gets followed, but in a long session or against an explicit request from you it can lose weight. "Never read the `.env` file" written here is guidance; a deny rule in `.claude/settings.json` (chapter 11) or a `PreToolUse` hook (chapter 12) actually prevents it, because Claude Code enforces them before the call goes out. Use `CLAUDE.md` to explain how to work, and permissions and hooks for hard limits.
:::

## 7.4 Generating your first file with /init

Writing the first `CLAUDE.md` for an existing project by hand is tedious, and Claude can draft it for you. From the project root, in a Claude Code session:

```text
/init
```

Claude explores the repository: it reads `package.json` or `pyproject.toml`, the config files (`tsconfig.json`, the ESLint config, the Vite config), the folder structure and a few source files to figure out the patterns in use. Then it writes a first version of `CLAUDE.md` with the stack (it takes the versions from the manifests), the commands it found in the scripts, the main structure and some conventions inferred from the code. If a `CLAUDE.md` already exists, `/init` doesn't overwrite it: it suggests improvements.

![/init at work: Claude explores the project and prepares CLAUDE.md.](figures/cap-07/fig-01.png)

<!-- TODO screenshot: rifare fig-01 con la UI attuale (barra di stato con il modello di ottobre 2026 e auto mode), a risoluzione più alta e senza nome dell'account e percorso personale nell'intestazione -->

If you want more control, start Claude Code with the `CLAUDE_CODE_NEW_INIT=1` variable. `/init` switches to an interactive flow: instead of writing the file right away, it asks what to set up (the `CLAUDE.md` files, including the personal `CLAUDE.local.md`, skills and hooks), explores the code with a subagent, asks you about whatever it can't work out, and shows you a proposal to review.

```bash
CLAUDE_CODE_NEW_INIT=1 claude
```

### What you need to add yourself

The `/init` draft is a good starting point, but it almost always lacks three things that aren't in the code. Semantic conventions: the code says you use strict TypeScript, not that error messages are in Spanish. The team's working rules: `/init` finds `pnpm dev` in the scripts, but "run `pnpm lint && pnpm type-check` before committing" is your team's decision. And the prohibitions, which exist because someone got it wrong once, a story the code doesn't tell.

### Editing the file

You can open `CLAUDE.md` in your editor, or type `/memory` in the session: you'll see the list of loaded instruction files (user, project, local, rules) and you open the one you want to edit. The same menu also controls auto memory, covered in section 7.5.

![The CLAUDE.md that /init generated for the data analysis project: chart pipeline, plan palette and output folders.](figures/cap-07/fig-02.png)

Guides from 2025 still mention the `#` shortcut: a message that started with `#` went straight into `CLAUDE.md`. It was removed in December 2025. Today you just ask in plain words:

```text
add to CLAUDE.md, in the NEVER do section: don't modify the files in src/generated/
```

### The full workflow

1. Run `/init` in the project root.
2. Open the generated `CLAUDE.md` and read all of it. Cut the obvious or redundant parts, like the folder listing Claude can see for itself.
3. Add the three missing things: conventions, working rules, prohibitions.
4. Exit and restart `claude`, or run `/clear`, then ask for something that should trigger your conventions. If Claude uses pnpm, creates files in the right folders and follows the pattern you pointed to, the file works. Otherwise go back to step 3.
5. Commit the file:

```bash
git add CLAUDE.md
git commit -m "docs: add CLAUDE.md"
```

### If the repository already has an AGENTS.md

Many projects have an `AGENTS.md`, the instruction file that other coding agents read. Since version 2.1.277 (September 2026) Claude Code reads it natively: if there's neither a `CLAUDE.md` nor a `CLAUDE.local.md` in the working folder or the folders above it, it uses `AGENTS.md`. A repository set up for another agent works right away.

You change this behavior in `/config`, under Project instructions. The default is `claude-md-or-agents-md` (what I just described); `claude-md-and-agents-md` loads both, `claude-md` ignores `AGENTS.md`, and `managed-only` loads only the organization's managed `CLAUDE.md` and auto memory at startup.

The `AGENTS.local.md` and `AGENTS.override.md` variants and the `.agents/` folder aren't read.

If the project has both files and you want a single source of truth, write the shared instructions in `AGENTS.md` and import it from `CLAUDE.md` with an `@AGENTS.md` line (imports are covered in the next section). Below it, add only what concerns Claude Code. If instead you're coming from Codex or Gemini CLI with a configuration already written, `/init` notices and offers `/import` to bring it in.

## 7.5 Keeping it short and current

A `CLAUDE.md` written once and then forgotten goes stale fast. Six months later it describes a stack you've upgraded and commands you've renamed, and Claude follows the old instructions instead of looking at the code as it is today. To keep it short, Claude Code gives you two tools: imports and path-scoped rules. Keeping it current takes a bit of discipline.

### Imports with @

An `@path/file` line inside `CLAUDE.md` pulls in another file. The path is relative to the importing file; absolute paths and paths starting with `~` work too.

```markdown
# Photogallery

Overview and commands: @README.md
Instructions shared with other agents: @AGENTS.md

## Personal preferences
- @~/.claude/photogallery-preferenze.md
```

The last line is an alternative to `CLAUDE.local.md`: your preferences live in a file in your home directory, and every worktree of the project picks them up through the same import. Imports can nest up to four levels deep. An `@` inside a code block or between backticks is ignored. If the path contains spaces, put a `\` in front of each one. When an import points outside the project, Claude Code asks you to approve it the first time.

Imports are for organizing the text. The imported file loads at startup as if it were written right there and costs the same context: to load instructions only when they're needed, you have rules.

### Rules in .claude/rules/

The `.claude/rules/` folder holds Markdown files, subfolders included, that Claude Code finds on its own. A rule without frontmatter loads at startup like a piece of `CLAUDE.md`. A rule with a `paths:` field (a YAML list of globs) loads only when Claude reads or edits a matching file.

The Photogallery is the textbook case. The PHP style in its `CLAUDE.md` applies only to `backend/`, so I'd move it to `.claude/rules/php.md`:

```markdown
---
paths:
  - "backend/**/*.php"
---

# PHP code style

- Run `vendor/bin/pint --dirty --format agent` before finalizing changes.
- `declare(strict_types=1);` on every file in `app/Services/`, `app/Actions/`,
  `app/Jobs/`, `app/Queries/`.
- Final by default: new classes are `final class Foo` unless explicitly
  designed for inheritance.
- Mass assignment: `$model->fill($request->validated())`, never `$request->all()`.
- Always use curly braces for control structures, even for single-line bodies.
```

These lines come, lightly trimmed, from the file's Code style section. The same goes for the TypeScript and Tailwind rules, which would go in `.claude/rules/frontend.md` with `paths: ["frontend/src/**/*.ts", "frontend/src/**/*.tsx"]`. What stays in `CLAUDE.md` is the rules that apply everywhere (one task, one commit; the `{ "data": ... }` envelope; UUID v7), and the file drops toward two hundred lines. The companion repository doesn't have this split yet: it's the refactoring I'd do today.

For the data analysis project from chapters 4-6, a single rule is enough:

```markdown
---
paths:
  - "**/*.py"
---

# Python rules

- Type hints on all public functions
- Docstrings in English, Google style
- No print: use the logging module
```

Claude Code looks for rules at startup, so after writing one, exit and restart `claude`. Ask Claude to read a Python file, then type `/memory`: the rule shows up among the loaded instruction files. In `/context` you'll find it in the Memory files section, along with its token cost. Personal rules that apply to every project go in `~/.claude/rules/`.

### When to update it

The right moment is right after the change, while the context is fresh in your head: a major upgrade (Laravel 12 to 13), a switch of package manager, a new pattern, a library Claude has to use in a particular way, a renamed folder, something you've decided to stop doing.

On teams, a checkbox in the pull request template works:

```markdown
## PR checklist

- [ ] Tests green (`pnpm test`)
- [ ] Lint clean (`pnpm lint && pnpm type-check`)
- [ ] CLAUDE.md updated if the stack or conventions changed
- [ ] Docs updated if a public API changed
```

The checkbox doesn't guarantee anything, but both the person opening the PR and the reviewer see it.

The signs that the file has fallen behind are easy to spot. Claude keeps creating components with the structure you had before the refactoring, because `CLAUDE.md` still describes it. It suggests `npm run dev` six months after you switched to `pnpm dev`. It obeys a prohibition ("don't call `fetch` directly") that no longer makes sense, because the api-client is gone.

If you want to track changes, add a section at the bottom with the last three to five, dated. It's for you and the team, not for Claude, so you can put it inside an HTML comment and it costs no context:

```markdown
<!--
## Changelog
- 2026-09-10: moved from React Query to TanStack Query 5 (same API)
- 2026-07-02: introduced the Result<T, E> pattern, remove bare try/catch blocks
- 2026-05-15: generated with /init + team conventions
-->
```

Every so often, ask Claude itself to do the review. It can tell you which instructions it uses and which are just noise.

::: {.callout .callout-prompt}
[Reusable prompt]{.callout-title}

```text
Read the CLAUDE.md file in this project and tell me:
1. Is there information that duplicates what you can already infer from the code?
2. Are there overly verbose sections that could be condensed?
3. Is important information missing that has already caused you errors
   or that would have helped you in this session?
4. Does the file have sections that are outdated relative to the project's current stack?
5. Are there instructions that apply only to part of the code and that
   would fit better in .claude/rules/ with the paths field?

Propose a revised version of at most 200 lines.
```

Run it every two or three months, or after a major refactoring.
:::

The more systematic check is `/doctor prompt-audit`, which reads `CLAUDE.md`, rules, skills and agents and flags instructions written for older models, references to files that no longer exist and instructions that contradict each other. It's covered in chapter 15.

### The memory Claude writes

Besides `CLAUDE.md`, which you write, there's auto memory, which Claude writes and which is on by default. It collects your preferences, the corrections you give it while working and the context it can't get from the code. It lives in your home directory, in `~/.claude/projects/<project>/memory/`, shared across the worktrees of the same repository: a `MEMORY.md` file serves as the index, and each session loads its first 200 lines (or 25 KB). They're Markdown files you can read and fix, and `/memory` turns it on or off. The rule for choosing is simple: what the whole team needs goes in `CLAUDE.md`, your personal preferences can live in memory. Chapter 15 covers it in full.

## 7.6 Three real examples

Three files for three different kinds of project, each with the situations where it saves you a correction.

### A. React and Tailwind CSS frontend

```markdown
# CLAUDE.md: Dashboard Frontend

## Stack
- React 19 + TypeScript 5
- Vite 6 (NOT Create React App, NOT Next.js)
- Tailwind CSS 4 + shadcn/ui
- Global state: Zustand 5
- Fetching: TanStack Query 5
- Forms: React Hook Form 7 + Zod
- Test: Vitest + Testing Library
- Package manager: pnpm

## Commands
- Dev: `pnpm dev` (port 5173)
- Build: `pnpm build`, preview with `pnpm preview`
- Test: `pnpm test`
- Lint: `pnpm lint`

## Conventions
- One component per file, name in PascalCase, file in kebab-case (`gallery-card.tsx`)
- Custom hooks prefixed with `use`, e.g. `useGalleryList`
- Tailwind classes inline in the JSX, no separate CSS
- No `useEffect` for fetching: use TanStack Query
- Zustand stores hold state only, no business logic

## NEVER do
- Don't modify `src/components/ui/`: those are the shadcn components
- Don't use `useState` for form state: React Hook Form
- Don't import with relative paths: use the `@/` alias
- Don't leave `console.log` in committed code
```

Where it saves you: Claude doesn't reach for `useEffect` plus `fetch` for API calls, the old pattern it has seen most often, doesn't touch the shadcn components and always goes through TanStack Query. On a frontend that changes fast, those three rules alone are worth the file.

### B. NestJS and Prisma backend

```markdown
# CLAUDE.md: API Backend

## Stack
- NestJS 11 + TypeScript 5 (strict)
- Prisma 6 (PostgreSQL)
- Auth: Passport + JWT (access 15 min, refresh 7 days)
- Test: Jest + Supertest
- Package manager: pnpm

## Commands
- Dev: `pnpm start:dev` (hot reload, port 4000)
- Test: `pnpm test` (unit), `pnpm test:e2e` (E2E)
- Migrations in development: `pnpm db:migrate`
- Migrations in production: `pnpm db:deploy` (never `migrate dev` in production)
- Seed: `pnpm db:seed` (overwrites everything)

## Architecture
- One NestJS module per domain (users, orders, invoices)
- Repository pattern: each module has its own `.repository.ts`, model in `src/users/users.repository.ts`
- One DTO per operation (`CreateUserDto`, `UpdateUserDto`)
- `JwtAuthGuard` on every protected endpoint

## Conventions
- No `any`: use `unknown` and a type guard
- Errors always with `HttpException` or one of its subclasses
- Log with `Logger` from `@nestjs/common`, never `console.log`

## NEVER do
- Don't modify `src/prisma/generated/`: generated files
- Don't expose endpoints without `@UseGuards(JwtAuthGuard)` (except `/auth/*`)
- Don't return Prisma entities from the controller: always a DTO
```

Where it saves you: Claude doesn't forget the JWT guard on a new endpoint, doesn't return an entity's sensitive fields in the response, and follows the repository pattern from the model file. Those are expensive mistakes to find later.

### C. Python data analysis scripts

This is the kind of file you need for the project in chapters 4-6.

```markdown
# CLAUDE.md: SaaS metrics analysis

## Stack
- Python 3.11+
- pandas 2, matplotlib
- Export: openpyxl for Excel, ReportLab for PDF
- Environment: pip + venv (NOT conda), `venv/` in the root, already created

## Commands
- Activate the environment: `source venv/bin/activate`
- Dependencies: `pip install -r requirements.txt`
- Dashboard: `python dashboard.py`
- Excel: `python tools/genera_excel.py`
- PDF report: `python tools/genera_report.py`
- Test: `pytest tests/`

## Data
- Source: `saas_metrics.csv` (read-only)
- Charts in `docs/charts/`, Excel and PDF in `output/` (create the folders if missing)
- Currency: euros, never dollars
- Dates in dd/mm/yyyy format

## Conventions
- Type hints on parameters and return value, Google-style docstrings
- Fixed plan palette: Free, Silver, Gold always in the same colors
- Charts at 150 dpi

## NEVER do
- Don't use `print()` for debugging: use `logging`
- Don't write absolute paths: use `pathlib.Path(__file__).parent`
- Don't commit CSV or Excel files: only code and `requirements.txt`
- Don't modify the source CSV
```

Where it saves you: Claude saves charts and reports in the right folders without you repeating it, uses euros and the dd/mm/yyyy date format, and doesn't rewrite the CSV to "clean it up". On scripts that run unattended, like the Excel report launched from cron in chapter 5, the output stays consistent even when the prompt is a single line.

## Summary {.unlisted}

- `CLAUDE.md` is text that Claude Code loads into the context in every session. There are four levels (organization, user, project, local) and they add up; files in subfolders come in when Claude works there.
- Write verifiable instructions about the stack, commands, non-obvious conventions, prohibitions, patterns and vocabulary. Leave out documentation, secrets and roadmaps.
- Stay under two hundred lines. `@` imports organize the text but don't save context; rules in `.claude/rules/` with `paths:` load only for matching files.
- Generate the first draft with `/init`, then add what the code doesn't say. To edit it, use `/memory` or ask Claude: the `#` shortcut is gone.
- If there's only an `AGENTS.md`, Claude Code reads that; if both exist, import `@AGENTS.md` from `CLAUDE.md`.
- `CLAUDE.md` guides, it doesn't enforce: for hard limits use permissions (chapter 11) and hooks (chapter 12).

## Exercise {.unlisted}

Take a project you work on, even a small one. If you don't have one, use the one from the chapter 1 exercise or the analysis project from chapters 4-6.

1. Run `/init` in the root and read the draft. Cut whatever Claude can work out from the code on its own.
2. Add the project's commands, a "NEVER do" section with three to five items, and the domain vocabulary, if the project has one.
3. Move at least one rule that applies only to one file type into `.claude/rules/`, with the `paths:` field.
4. Exit, restart `claude` and ask for something that should trigger your conventions, for example "add a module for order management" or "add a churn-by-plan chart to the report".

You're done when `CLAUDE.md` is under two hundred lines (check with `wc -l CLAUDE.md`), `/memory` shows the rule loaded after Claude has read a matching file, and the code produced in step 4 follows the commands, folders and patterns you wrote down without you repeating them in the prompt. The review prompt from section 7.5 is also in the `claude-code-book-snippets` repository, in the `cap-06/` folder.
