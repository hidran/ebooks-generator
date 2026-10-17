# Appendix C. Ready-to-use prompts

This appendix collects the book's reusable prompts, sorted by the job at hand rather than by chapter. The first edition had fifty generic prompts here. What's left are the ones the chapters actually use, in this edition's corrected version, with project names replaced by placeholders in square brackets: `[FILE]`, `[GOAL]`, `[STACK]`. Swap them for real files, commands and checks from your project, and drop the lines you don't need. Each prompt names the chapter that explains it: if the result isn't what you expected, go back there before you rewrite it.

The same prompts are in plain text in the `github.com/hidran/claude-code-book-snippets` repository, handy for copy and paste.

## C.1 Getting to know a project or a dataset

### First look at a project

When you open a repository you don't know, before asking for any change (chapter 1).

```text
Read the files in the project and tell me:
1. What tech stack you see
2. Which part looks most recent and which looks oldest
3. Which file is the entry point
4. What you DON'T understand right away from the folder names
```

### First look at a dataset

On any CSV, before you start the real analysis (chapter 4).

```text
Read @[CSV FILE]. Report:
1. Structure: number of rows, columns with name and type
2. Missing or anomalous values
3. Time patterns, if there are date columns
4. Any obvious outliers in the numeric columns

Then give me 3 interesting business questions you could
ask about this data: don't answer them yet, I want to
check first that they're the right ones.
```

## C.2 Planning with Plan Mode

Run this prompt in Plan Mode, along with the landing page template (C.3) and the new feature template (C.10). You get there with `Shift+Tab` until you see `plan mode on`, or with `/plan`. Claude reads and explores, but changes nothing until you approve the plan.

### The plan before the code

For any task bigger than a few lines (chapter 3).

```text
Plan how you would [GOAL]. Don't write code. Only numbered steps
with: files to create or modify, the reason for each change,
dependencies between steps, likely trouble spots.
```

## C.3 Features and refactoring

### Adding a feature

The basic template for a request Claude should carry out without guessing (chapter 3).

```text
Context: [what exists, which file, which function, why it exists]

Goal: [what must change or be created, in measurable terms]

Constraints:
- Don't modify [file/API/behavior]
- Follow the pattern already used in [reference file]
- [Other limits: Node version, dependencies, compatibility]

Examples: read [existing file] for the pattern to follow

Output: [show me the plan first / create the file / show me only the diff]
```

### Guided refactoring

When you want to change the structure of the code without changing its behavior (chapter 3).

```text
Context: read [file path]. The function/class [name] does [description
of what it does and why it currently exists].

Goal: [what must change, in measurable terms. E.g.: split the
responsibilities into X pure functions / make the class testable with
mocks / remove the dependency on [library]]

Constraints:
- The public signature of [function/interface] must stay identical
- Don't touch [related file or folder]
- The tests in [test path] must keep passing without changes

Target pattern example: look at [file that already has the style you want]

Output: first show me a numbered plan with the steps and affected files.
Don't execute until I approve.
```

### A landing page from brief to deploy

For a new marketing site, with Superpowers installed. With the manual confirmations, budget 60-90 minutes of session time (chapter 16).

```text
I want to build a landing page for [PRODUCT NAME].

Product description:
[2-3 sentences describing the product and its main value]

Audience:
[who the target users are]

Main call to action:
[e.g. "Start for free", "Book a demo", "Download the app"]

Sections to include:
- Hero with headline, subtitle, CTA and image/video
- Features (4-6 main features with icons)
- [optional section, e.g. "How it works" with 3 steps]
- Social proof (testimonials or customer logos)
- Pricing (N plans, with a monthly/yearly toggle if there is one)
- FAQ (6-8 most frequent questions)
- Footer with a final CTA

Style:
[e.g. "dark mode, violet accent, bold type, tech forward"
 or "light, warm colors, friendly, consumer startup"]

Stack:
React + Vite + Tailwind CSS (latest version)

Deploy target:
Firebase Hosting

Workflow:
1. Use the visual companion to show me 3 layout variants
2. Once the layout is approved, generate the specs in docs/SPEC.md
3. Create the plan in docs/PLAN.md with atomic tasks and done criteria
4. Run one task at a time and wait for my confirmation
5. Code review after all the components, before the deploy
6. Build + firebase deploy --only hosting

Start in Plan Mode. Don't write any code until the specs are approved.
```

## C.4 Debugging

### A failing test

Give Claude the test name, the error and the files to read, and keep the decision on the fix for yourself (chapter 3).

```text
The test "[TEST NAME]" in [TEST FILE]
fails with [ERROR].
Read the test and the [FUNCTION] function in [FILE]. Find
the cause and propose a fix, but don't apply it until I've approved it.
```

### An intermittent bug

For hard problems that need more reasoning for a single turn: `ultrathink` applies to that message only (chapter 3).

```text
ultrathink. [SYMPTOM DESCRIPTION, e.g. The orders integration test
fails one time in five, only in CI]. Read [FILES AND FOLDERS] and give
me the three most likely causes, in order, with a way to verify each one.
```

## C.5 Tests

### A function with its tests

The check goes inside the prompt: Claude knows when it's done because you told it (chapter 3).

```text
Write a function [FUNCTION SIGNATURE] with [INPUT AND OUTPUT TYPES].
Also write tests for these cases: [CASES, e.g. empty file, file with
only the header, rows with missing fields, valid rows]. The tests
must pass with [TEST COMMAND].
```

## C.6 Data analysis and reports

### The patterns that matter

To get from descriptive statistics to conclusions that help whoever makes the decisions (chapter 4).

```text
@[CSV FILE] look at the CSV. What are the 3 most
important patterns for [READER, e.g. someone running a SaaS]? Explain them
in plain English. Use numbers only when they're the main
point, not as filler.
```

### Excel report with pivots and formulas

A formatted Excel file, with totals as formulas and command-line parameters (chapter 5).

```text
Read [CSV FILE]. Write a Python script tools/genera_excel.py that generates
[XLSX FILE] with:

1. Sheet "Dati": all the CSV data as a filterable table (auto_filter),
   header with a dark blue background (#1F4E78) and bold white text,
   column widths fitted to the content, freeze on the first row,
   zebra striping on the even rows (#F2F2F2).

2. Sheet "Riepilogo": pivot table with [ROW FIELD] as rows and
   [COLUMN FIELD] as columns, values = sum of [METRIC].
   Totals row with SUM formulas, not hardcoded values.

3. Sheet "Grafici": a line chart of [TIME METRIC] over time
   broken down by [SEGMENT], a pie chart of the total distribution
   of [METRIC] by [SEGMENT].

Use openpyxl. Add argparse with --input, --output, --region (optional).
If --output isn't given, use report_YYYY-MM.xlsx with an automatic timestamp.
Install the dependencies and update requirements.txt.
```

### Mini web dashboard

A Flask web app with Chart.js on top of any tabular CSV (chapter 6).

```text
Starting from [CSV FILE], create a mini Flask dashboard:
- app.py with GET / and GET /api/data routes
- templates/index.html with Chart.js from a CDN and three canvases:
  [CHART 1] (type: [line|bar|pie]),
  [CHART 2] (type: [line|bar|pie]),
  [CHART 3] (type: [line|bar|pie])
- static/style.css with a 2-column grid layout, Inter font,
  white cards on a light gray background, mobile responsive
- A "Refresh data" button that re-fetches /api/data and calls
  chart.update() without a reload
Startup: python app.py, server on http://localhost:5000
```

## C.7 CLAUDE.md, rules and memory

For the first draft of `CLAUDE.md` on an existing project there's `/init` (chapter 7). The prompts below are for later.

### Adding a rule

The `#` shortcut is gone: you ask Claude, or you open the file with `/memory` (chapter 7).

```text
add to CLAUDE.md, in the [SECTION, e.g. NEVER do] section: [RULE]
```

### Periodic CLAUDE.md review

Every two or three months, or after a major refactoring (chapter 7).

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

## C.8 Skills, custom commands and agents

### A custom command for a recurring workflow

When you keep repeating the same sequence by hand and don't know where to start (chapter 8).

```text
Create a custom command in .claude/commands/[NAME].md for this
recurring scenario: [describe the workflow you often do by hand].

The command must:
- Have frontmatter with a clear description (60 characters max)
- Have an argument-hint if it takes parameters
- Structure the instructions as numbered steps
- State explicitly whether to show a diff before applying
- Say whether to wait for confirmation or proceed automatically

Show me the complete file, ready to save.
```

### Sketching a skill

Give it to Claude directly, or use it to get your ideas straight before you reach for the skill-creator (chapter 9).

```text
I want to create a Claude Code skill called [SKILL-NAME].

It should trigger when the user asks [DESCRIBE THE TRIGGER IN PLAIN WORDS].
The workflow has these steps:
1. [STEP 1]
2. [STEP 2]
3. [STEP 3]

Does it need [Python scripts / references / templates]? [YES/NO, specify]

Create the folder structure in .claude/skills/[SKILL-NAME]/ (or in
~/.claude/skills/[SKILL-NAME]/ if I need it in all my projects),
write SKILL.md with frontmatter optimized for automatic triggering,
and add any supporting files in the appropriate subfolders.
```

### Creating an agent

The `/agents` wizard is gone: you describe the agent and Claude writes the file in `.claude/agents/` (chapter 10).

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

## C.9 MCP and context

Permissions, the sandbox, hooks and plugins (chapters 11, 12 and 14) are set up with files and commands, not prompts: the chapters pair each configuration with test prompts that check it. What's left here are the two Part IV prompts I use most.

### Working on GitHub through an MCP server

With the remote GitHub server configured, without leaving the session (chapter 13).

```text
list the 5 most recent open issues in the repository [USER]/[REPOSITORY], number and title only
```

### Compacting without losing the thread

`/compact` takes instructions on what to keep in the summary (chapters 4, 15 and 19).

```text
/compact Keep [WHAT TO KEEP, e.g. the project structure, the decisions we made and the failing tests]
```

## C.10 Specs and Spec Driven Development

### Describing the problem before the stack

The first prompt of a new project says what the application must do and leaves the choice of technologies open (chapter 17).

```text
I want to build [TYPE OF APPLICATION].
Users must be able to:
- [FEATURE 1, with the constraints you know, e.g. formats and sizes]
- [FEATURE 2]
- [FEATURE 3]

[SURROUNDING REQUIREMENTS, e.g. admin panel, environments]

Don't pick the stack yet. First tell me which stacks
you'd recommend for this kind of project, with the tradeoffs
of each. I want standard, mature technologies, no hype.
```

### The technical brief

Iterate on it two or three times before you call it ready (chapter 17).

```text
Context: I'm building [project description in 2-3 sentences].
Tech stack: [the chosen stack, with the reasoning].

Generate a structured technical brief that includes:
1. Functional requirements: features by role (visitor / user / admin)
   with acceptance criteria for each
2. Non-functional requirements: performance, security (authentication,
   authorization, validation), scalability (order of magnitude
   of the expected users and data)
3. Constraints: locked stack, target hosting, rough budget, timeline
4. Key technical decisions: authentication strategy (tokens / sessions),
   upload (through the API / presigned URLs), database approach (migrations /
   ORM / SQL), storage (local / S3 / other)
5. Out of scope: what we won't build in the first version, and why
6. Quotas, limits and audit logging, if they're in scope

Produce a 3-4 page document in Markdown.
After the draft, wait for my review before moving on
to the operational specs.
```

### Requirements, design and tasks

From the spec to the three Spec Driven Development files, with the IDs that link them (chapter 18).

```text
Read SPEC.md[, OTHER REFINEMENT DOCUMENTS].

Generate three files in the docs/ folder:

1. docs/REQUIREMENTS.md, what to build
   - Vision and what the product is NOT
   - Personas ([ROLES])
   - User stories per persona, with IDs (US-01, US-02, ...)
   - Testable acceptance criteria, with IDs (AC-F1-1, ...)
   - Constraints (file formats, sizes, naming)
   - Non-functional requirements with numbers (performance, security, scalability)
   - Explicit out of scope
   No technical decisions, no schemas, no code.

2. docs/DESIGN.md, how to build it
   - Stack with exact versions
   - Folder structure of [PROJECT FOLDERS]
   - Database schema: tables, columns, types, constraints, indexes, ON DELETE
   - API contracts: verb, URL, body, response shape, status codes
   - Service interfaces ([SERVICES]) for DIP
   - Authentication, error handling, [OTHER PIPELINES]

3. docs/TASKS.md, the work list
   - Atomic tasks, 30 minutes each at most, grouped into phases
   - For each task: ID (T001, ...), status [ ], owner (backend-dev,
     frontend-dev, code-reviewer), Depends on, Parallel with, Reads
     (sections to read), Acceptance (definition of done), Commit
   - References to DESIGN.md sections and REQUIREMENTS.md IDs

Use the IDs for traceability in both directions: every acceptance
criterion must appear in at least one task.
```

### A new feature on a project with specs

When requirements, design and tasks are already settled: Claude updates the three documents before it touches the code (chapter 21).

```text
I have a project with docs/REQUIREMENTS.md, docs/DESIGN.md and docs/TASKS.md
already settled. I want to add this feature: [FEATURE DESCRIPTION].

Do these steps in order:

1. Read the three files to understand the current state
2. Propose the section to add to REQUIREMENTS.md
   (requirements, constraints and explicit acceptance criteria)
3. Propose the changes to DESIGN.md (schema, endpoints, components)
4. Propose the tasks to add to TASKS.md, with dependencies, new IDs
   that don't collide with the existing ones, and completion criteria
   that can be verified
5. Before running any task, check whether the feature needs
   a DB migration and whether the code already has something similar
   that could conflict

Don't start execution until I've approved the changes to the three files.
```

## C.11 Wave execution and /goal

### Starting a phase

Deliberately simple: the real work is already written down in `docs/TASKS.md` (chapter 19).

```text
Proceed with the Phase [N] tasks according to docs/TASKS.md.
One commit per task, one pull request per phase.
Use subagents where tasks are independent.
```

### A condition for /goal

The evaluator judges only what Claude shows in the conversation: the condition has to name checks that Claude runs in front of you (chapter 20).

```text
/goal tasks [FIRST ID] through [LAST ID] have Status [x] in docs/TASKS.md (show me the Status lines with grep), "[TEST COMMAND]" in the [FOLDER] folder exits with code 0, and every task has its own commit on the worktree branch (show me git log --oneline)
```

### Closing a wave

The standard end-of-wave prompt (chapter 21).

```text
Before marking this wave as complete, check:

1. For every task marked [x]: does the repository contain the code that
   matches its acceptance criteria? I want the file path,
   not "it should exist".
2. Rereading the requirements this wave claims to cover,
   is there anything the tasks don't cover?
3. Is there at least one test (automated, or manual and documented) that
   exercises every user flow mentioned in those requirements?

If you find gaps, list them. Don't close the wave until the list is empty
or the exceptions are explicitly documented as out of scope.
```

## C.12 Review and QA

### The built-in review

`/code-review` (alias `/review`) runs as a background subagent. With no target it looks at unpushed commits plus uncommitted changes; with no level it reuses the last one you typed (chapter 22).

```text
/code-review high main...[BRANCH]
/code-review [PR NUMBER]
/code-review --fix main...[BRANCH]
/code-review --comment [PR NUMBER]
/code-review ultra [NOTE FOR THE REVIEWERS]
```

### Wave review with four agents

At the end of a phase, several specialized reviewers in parallel and a single report (chapter 19).

```text
Wave review of Phase [N], [PHASE NAME] (tasks [FIRST ID]-[LAST ID]).
Launch four subagents in parallel, read-only (no changes
to files), model sonnet:

1. security-auditor
   Look for: auth bypass, missing input validation, unauthorized
   data exposure, secrets in the code, overly permissive CORS.

2. performance-reviewer
   Look for: N+1 queries, missing eager loading, missing DB indexes on
   filtered columns, synchronous operations that should be jobs.

3. api-consistency
   Look for: inconsistent error envelope, wrong status codes,
   [PROJECT PATTERNS NOT FOLLOWED], inconsistent naming.

4. test-coverage
   Look for: critical paths without tests, missing edge cases, tests that
   bypass the policy, N+1 in tests, incomplete factories.

For each finding: file, line, severity (CRITICAL / HIGH / MAJOR /
MEDIUM / LOW), proposed fix. Merge the four reports into a single
document, in priority order.
```

### The pre-deploy QA checklist

To start from a sensible list instead of from memory (chapter 22).

```text
You're a senior QA engineer. My project is [describe the stack and type of app].
Generate a pre-deploy checklist organized by category:
Functional, Performance, Security, Data Integrity, Observability.
For each item, specify: what to check, how to check it (command or action),
and the success criterion. Format: Markdown table.
```

### Multi-LLM review

Paste it unchanged into Claude, Gemini, Codex and Kimi, then compare the results (chapter 22).

```text
Act as a senior software engineer with 10+ years of experience.
Do a critical review of the following code.

Evaluate it on these axes:
1. Best practices and standards for the language/framework
2. SOLID principles and design patterns (SRP, OCP, LSP, ISP, DIP)
3. Security (injection, authentication, authorization, data exposure)
4. Scalability and performance (N+1 queries, memory use, caching)
5. Reliability and error handling (exception handling, rollback)
6. Unhandled edge cases (boundary input, concurrency, intermediate states)

For each problem:
- Severity: Critical / High / Medium / Low
- File and line (if applicable)
- Short description of the problem
- Recommended fix with a code snippet

Output: Markdown list sorted by descending severity.
No padding: if you find no problems in an area, say so explicitly.

[paste the git diff or the files to review here]
```

## C.13 Deploy

The Firebase deploy of the landing page is already part of the template in section C.3. For AWS, the starting point is the CloudFormation template.

### A CloudFormation template

The generic version of the Photogallery template: adapt the name, stack, database and region (chapter 23).

```text
Generate a CloudFormation YAML template for a [NAME] application with:
- Stack: [backend in Laravel/Node.js/Python] + [frontend in React/Vue/Angular]
- Database: managed [MariaDB/MySQL/PostgreSQL] on RDS
- AWS region: [eu-west-1/us-east-1/...]
- Deployment target: ECS Fargate for the backend, S3 + CloudFront for the frontend
- Environments: staging and production through Parameters

The template must include:
- VPC with 2 public subnets (ALB) and 2 private ones (ECS, RDS) across 2 AZs
- Security groups with least privilege (ECS to RDS only on the DB port)
- IAM execution role for ECS (ECR, Secrets Manager, logs) and task role for the app
- ECR repository for the Docker image
- CloudWatch log group for each container
- Outputs: ALBDnsName, CloudFrontDomainName, EcrRepositoryUri

Output: infra/cloudformation.yaml. Add inline comments for the sections
that aren't obvious (e.g. why that DependsOn, why that IAM policy).
```
