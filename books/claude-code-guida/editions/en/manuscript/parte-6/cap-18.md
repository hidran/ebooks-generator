# Chapter 18. Spec Driven Development

::: {.chapter-goals}
[What you'll learn]{.callout-title}

- split the specs into `docs/REQUIREMENTS.md`, `docs/DESIGN.md` and `docs/TASKS.md`, and know who reads which
- write a build workflow with a prompt, a verification command and a commit for every phase
- put SOLID, KISS and DRY into `CLAUDE.md` with examples taken from the project's own code
- have a skeptical agent tear the specs apart before the first line of code gets written

[Prerequisites]{.callout-title}

Chapter 17, which produced the Photogallery's `SPEC.md` and refinement documents. The examples use Laravel, but the method works with any backend framework.

:::

Coding with an agent turns into a problem at a specific moment, and it usually comes late: the code works, but you can no longer say why it's written the way it is. One module uses UUIDs and the one next to it uses auto-increment integers. In one controller the business logic sits in the controller, in another it lives in a service. Each choice is defensible on its own. Put together, they aren't.

That's vibecoding: the agent writes code prompt after prompt, with no structure tying the decisions together. Claude writes good code, but when there's no plan it fills the gaps with reasonable choices that nobody checks against yesterday's. And the tech debt stays invisible, because the code arrives already plausible and already compiling. You notice when a change that should have touched three files touches thirty.

Spec Driven Development (SDD) starts from a simple rule: every line of code Claude writes must trace back to a requirement, a task and a written design decision. No commit until the task is verified. Put like that, it sounds like bureaucracy. In practice Claude stops guessing what you had in mind and starts executing a plan, and you spend less time fixing things.

There's also a context reason. By the end of chapter 17 the Photogallery's `SPEC.md` had grown to 2,386 lines. It fits in a one-million-token context window, but loading it for every task means burying the twenty lines you need under two thousand you don't. With separate files, Claude reads the rules (`CLAUDE.md`, loaded automatically), the task it has to execute and the design section that task cites.

Part VI builds the Photogallery with this method. This chapter sets up the files; execution starts in chapter 19.

## 18.1 The three files

Several tools for agent-driven development have reached the same conclusion: for a medium-sized project, a single spec file isn't enough. Kiro calls its files `requirements.md`, `design.md` and `tasks.md`; GitHub's Spec Kit works with a spec, a plan and a task list. The names change, the split doesn't: what to build, how to build it, in what order. In the Photogallery the three files live in `docs/` with uppercase names, and the `CLAUDE.md` at the repository root ties them together.

| File | Who reads it | How often it changes | When it's read |
| :---- | :---- | :---- | :---- |
| `CLAUDE.md` | Every session | Rarely | Always, automatically |
| `docs/REQUIREMENTS.md` | You, a stakeholder, whoever plans | Almost never | During planning and when a task cites a criterion |
| `docs/DESIGN.md` | The implementing agents | Fairly often | When a task cites a section |
| `docs/TASKS.md` | The executing agents | Constantly | On every task, updated each time a task closes |

When Claude works on T031, `PhotoController@index` and `@show`, it reads the task, which points to `DESIGN.md §6.2`, and opens only that section. Whoever decides whether a feature makes it into v1 reads the requirements without wading through table schemas. And since requirements rarely change while tasks change every hour, keeping them apart saves you from rewriting a huge document every time you tick a checkbox.

### `docs/REQUIREMENTS.md`, what to build

The requirements file describes the product in language that people who don't write code can follow. No technologies, no class or endpoint names: vision, personas, user stories, acceptance criteria, constraints, non-functional requirements and what stays out. The file's header says it plainly: "No code, no schemas, no technical decisions".

The Photogallery has three personas (anonymous visitor, registered member, administrator). User stories are numbered `US-01` to `US-40`, features `F1` to `F12`, and every acceptance criterion has an ID like `AC-F4-1`. These IDs hold the method together: tasks cite them, tests verify them, commit messages reference them. The repository files are in English and I quote them as they are. Here's the upload part, trimmed:

```markdown
### Upload & ownership (Member)
- **US-13.** As a member, I want to drag and drop photos onto a target zone to upload them.
[...]
- **US-17.** As a member, I want the upload to fail loudly (with a clear message) if a file is over 10 MB or in an unsupported format — before any bytes leave my browser.

[...]

### F4 — Upload
- AC-F4-1: Dragging a 15 MB JPEG into the dropzone displays inline error "File exceeds 10 MB" and does not initiate the upload.
- AC-F4-3: Submitting 21 files shows "Up to 20 files at once" and refuses to send.
- AC-F4-4: A successful upload of 5 files within 10 seconds returns a batch identifier and a list of 5 photo ids; each photo appears in the gallery with a "processing" overlay.
```

Every criterion has a precise input and an observable result. You can't test "the upload must handle large files well". "A 15 MB JPEG shows `File exceeds 10 MB` and the upload doesn't start" becomes a Vitest test as written.

The "Out of scope" section matters as much as the requirements. The Photogallery's lists fifteen exclusions for v1, from comments to two-factor authentication, from soft deletes to hierarchical tags. Each entry is an argument you won't have again halfway through the project, and a feature Claude won't add because it seemed useful.

### `docs/DESIGN.md`, how to build it

The design file says how to implement the requirements: stack with versions, folders, database schema, API contracts, service interfaces, authentication, errors, image pipeline. It's the file agents open when they implement, "authoritative for code" according to its header. On this chapter's branch it runs to 1,297 lines in twelve sections.

A typical section is the contract for `POST /photos`, shown here with a few fields removed:

```markdown
#### `POST /photos` — single endpoint for 1–20 files
- **Auth:** token (`photos:write`)
- **Content-Type:** `multipart/form-data` (JSON body → 415)
- **Form fields:**

  | Field | Type | Required | Rules |
  |---|---|---|---|
  | `files[]` | File[] | yes | 1–20 items; each `image\|mimes:jpg,jpeg,png,webp\|max:10240` |
  | `album_id` | UUID | no | must exist + be owned by auth user |
  | `new_tags[]` | string[] (names) | no | up to 20; created if missing |

- **Behavior** (wrapped in `DB::transaction`):
  1. Upsert any `new_tags[]` names → tag rows (slug auto-generated, collision-resolved).
  2. Strip GPS EXIF from each file via `ExifExtractor::stripGps`.
  3. `PhotoStorage::storeOriginal(...)` writes to `photos_private` disk.
  4. Insert `Photo` row per file with `user_id = auth()->id()`, `processing_status = 'pending'`.
  5. Attach merged tag set.
  6. Wrap one `ProcessPhoto` per photo in `Bus::batch(...)`.
- **202 Accepted** with `Location: /api/v1/photos/batch/{batch_id}` header
- **Errors:** 403 (album not owned), 413, 415, 422
```

An agent reading this section has nothing left to decide. It knows the body is multipart, that the response is 202 because processing is asynchronous, what order the writes happen in and which errors need a test. The decisions Claude would otherwise make on its own, possibly a different one each session, are already written down.

### `docs/TASKS.md`, the work list

The tasks file is the operational one, and the one that changes most often. Every task is atomic (30 minutes of work at most, says the header) and declares status, owner, dependencies, parallel tasks, sections to read, acceptance criteria and commit message. Two Phase 2 tasks, as they appear on the chapter's branch:

```markdown
### T031 — `PhotoController@index` and `@show`
- **Status:** [ ]
- **Owner:** backend-dev
- **Depends on:** T020, T024, T026, T027
- **Parallel with:** T030, T034, T035, T036
- **Reads:** DESIGN.md §6.2
- **Acceptance:**
  - Index uses `PhotoQuery`; cursor pagination; eager loads; ≤2 SQL queries (n+1 detector enforced).
  - Show: 200 / 304 / 404 covered.
- **Commit:** `feat(api): GET /photos and /photos/{id}`

### T039 — Routes + middleware groups + rate limiters
- **Status:** [ ]
- **Owner:** backend-dev
- **Depends on:** T030–T038
- **Parallel with:** —
- **Magnet:** `routes/api.php`, `bootstrap/app.php`
- **Reads:** DESIGN.md §6.0 (rate limits), §6.1–§6.5
- **Acceptance:**
  - `routes/api.php` declares every endpoint under `/v1` prefix.
  - Auth routes throttled `10,1` per IP; everything else `120,1` per IP and `300,1` per user.
  - Mutating routes wrapped in `auth:sanctum`.
- **Commit:** `feat(api): route definitions with rate limits`
```

The `Depends on` and `Parallel with` lines are the reason this file exists. T030, T031, T034, T035 and T036 are controllers that touch different files, so they can run in parallel. T039 touches `routes/api.php` and `bootstrap/app.php`, two of the files the project calls magnets because they attract merge conflicts: it starts only once the controllers are done, and a single agent runs it. When you ask Claude to execute Phase 2, rule 3 in `CLAUDE.md` tells it to use subagents for the parallel tasks (chapter 10). The specs decide the orchestration, not your memory. In chapter 20 the same idea scales up to groups of phases, each in its own worktree.

On the chapter's branch `TASKS.md` holds 112 tasks in 13 phases. On `main` the summary at the bottom of the file counts 124 in 14 phases, because Phase 14, dedicated to finishing the frontend, was added during execution.

![Dependencies and parallel tasks declared in TASKS.md, on the course slide about the file](figures/cap-18/fig-01.png)

::: {.callout .callout-tip}
[Tip]{.callout-title}

You don't need Notion or Jira for specs. Four Markdown files in the repository, versioned with Git, are enough for an agent-driven project: every change to the specs lands in the history and gets reviewed in a PR, next to the code it changed.
:::

## 18.2 Generating the three files with Claude

Three files instead of one sounds like more work, but you don't write them: Claude generates them from the chapter 17 material, that is `SPEC.md` and the two refinement documents `docs/database-refinement.md` and `docs/api-refinement.md` (branch `book/cap-11-prompts-and-spec` of the companion repository). The prompt used for the Photogallery is the last section of `docs/PROMPT.md`, and it asks for four files: the three SDD files plus `CLAUDE.md`. Here's a version to adapt to your project:

```text
Read SPEC.md, docs/database-refinement.md and docs/api-refinement.md.

Generate three files in the docs/ folder:

1. docs/REQUIREMENTS.md, what to build
   - Vision and what the product is NOT
   - Personas (visitor, member, administrator)
   - User stories per persona, with IDs (US-01, US-02, ...)
   - Testable acceptance criteria, with IDs (AC-F1-1, ...)
   - Constraints (file formats, sizes, naming)
   - Non-functional requirements with numbers (performance, security, scalability)
   - Explicit out of scope
   No technical decisions, no schemas, no code.

2. docs/DESIGN.md, how to build it
   - Stack with exact versions
   - Folder structure of backend/ and frontend/
   - Database schema: tables, columns, types, constraints, indexes, ON DELETE
   - API contracts: verb, URL, body, response shape, status codes
   - Service interfaces (ImageProcessor, PhotoStorage) for DIP
   - Authentication, error handling, image pipeline

3. docs/TASKS.md, the work list
   - Atomic tasks, 30 minutes each at most, grouped into phases
   - For each task: ID (T001, ...), status [ ], owner (backend-dev,
     frontend-dev, code-reviewer), Depends on, Parallel with, Reads
     (sections to read), Acceptance (definition of done), Commit
   - References to DESIGN.md sections and REQUIREMENTS.md IDs

Use the IDs for traceability in both directions: every acceptance
criterion must appear in at least one task.
```

Before you run it, raise the effort with `/effort high`: writing specs is the kind of work where the higher level pays off (chapter 2).

The first pass comes out in a few minutes and needs a review. Three corrections are almost always needed.

The first is granularity. A first-pass `TASKS.md` tends to be either too fine, one task per method, or too vague, one task for the whole frontend. The right size is one file or a group of tightly related files: small enough to fit in a commit, big enough to have a verifiable acceptance criterion. Merge five-minute tasks; split an hours-long task that has no checkpoint.

The second is dependencies. The model is optimistic and often marks a test task as parallel with the task that test verifies. Check every `Parallel with`: two tasks can't run in parallel if one depends on the other, even when the files look separate.

The third is non-functional requirements, which easily sit in `REQUIREMENTS.md` with no task that implements or measures them. "Gallery time-to-first-tile ≤ 1.5 seconds on a 5 Mbps connection" is a real Photogallery requirement, and without a task with a measurable criterion nobody will ever check it. Section 18.6 shows what happened to it.

In the end, the three files on the `book/cap-12-sdd-three-files` branch come to 348, 1,297 and 1,427 lines. They're long, and that's fine: nobody reads them end to end, each task opens one piece.

## 18.3 The build workflow

The three files say what to build and how. The build workflow says in what order, with which verification command and which commit message for each phase. Without it, Claude might start on the frontend before the migrations, or write React components that call endpoints that don't exist yet.

In the Photogallery the workflow is section 13 of `SPEC.md`, "Claude Code Build Workflow". It came from a prompt a few lines long, which you'll find in `docs/claude-code-build-workflow.md`. The gist:

```text
Add a "Claude Code Build Workflow" section to the spec.
List the exact build order, phase by phase:

Phase 1: Backend foundation (models, migrations, seed)
Phase 2: API layer (controllers, routes, resources, form requests)
Phase 3: Filament admin panel (resources, widgets, dashboard)
[...]
Phase 9: Hooks (auto-formatting, automatic tests, security)
[...]
Phase 13: Final spec check and deploy

For each phase, write the exact prompt to give Claude Code.
```

### What a phase looks like

The result is a runbook: each phase has a goal, a prompt to paste, a verification command and a commit message. At the top of the section there's a preamble to put in front of every prompt from Phase 2 on:

```text
You are working inside this repo. The spec is `SPEC.md` at the repo root — it is authoritative. Read the sections referenced in the prompt and follow them literally. Do NOT invent fields, endpoints, or file paths that aren't in the spec. Run verification before claiming completion. Commit at the end with the message specified in the prompt.
```

Phase 1, trimmed:

```markdown
### Phase 1 — Backend foundation (models, migrations, seed)
**Goal:** Laravel 13 project scaffolded, UUID primary keys wired, all five application tables migrated, models with relationships, seeded admin user.

**Prompt:**
Bootstrap the Laravel backend per SPEC.md §3.2 and §4.

1. From repo root, scaffold the Laravel app in backend/:
     composer create-project laravel/laravel backend "^13.0"
[...]
6. Write migrations in this exact order (filenames per SPEC.md §3.2):
   - create_albums_table               — without cover_photo_id FK
   - create_tags_table
   - create_photos_table               — with album_id FK (ON DELETE SET NULL, ON UPDATE CASCADE)
   - add_cover_photo_fk_to_albums      — adds cover_photo_id FK (ON DELETE SET NULL)
   - create_photo_tag_table            — composite PK, both FKs CASCADE
   All column types, nullability, defaults, and indexes MUST match SPEC.md §4 exactly.
[...]
Commit: `feat(backend): database schema, models, and seeders`

**Verify:**
cd backend && php artisan migrate:fresh --seed && php artisan tinker --execute="echo App\Models\Photo::factory()->create()->id;"
```

The detail that matters is the verification: the phase is done when `php artisan migrate:fresh --seed` finishes without errors and the factory returns a row with a UUID. Claude's summary at the end of the work doesn't count as proof, and the preamble reminds it of that.

### The working rules

The workflow also needs rules that apply to every phase. In the Photogallery they're in section 15 of `SPEC.md`, "Test-and-Commit Discipline":

- one task, one commit, in Conventional Commits format with a scope among `backend`, `frontend`, `db`, `filament`, `api`, `pipeline`, `ci` and `spec`
- a test gate for each task type: a migration has to pass `migrate:fresh` and the rollback, an endpoint has a test for every documented status code
- never `--no-verify`, never `.skip`: if an old test breaks, `git bisect`, then fix forward or revert the guilty commit
- one branch per task (`feat/2-api-photos-store`), one PR per task, squash merge

I add three stop signals to these: a task that takes twice the expected time, a verification command that fails twice in a row, and Claude proposing to change the spec so the code passes. The code adapts to the spec. Going the other way takes an explicit decision and a dedicated `spec:` commit.

Another useful rule is a coverage file that has to stay empty: every requirement without a task goes there, and as long as the file has a line in it, the phase is blocked. In the Photogallery the coverage check came at the end, as an audit: `docs/SPEC-COVERAGE.md` maps every subsection of `DESIGN.md` to code and tests, and on April 30 it counted 42 sections, 27 implemented, 11 partial and 4 missing. Done before execution, it costs a lot less.

### The working loop

Once the workflow is approved, execution becomes a loop:

1. Copy the current phase's prompt from the workflow.
2. Paste it into Claude Code, with the preamble in front.
3. Claude works, parallelizing where the tasks allow it.
4. Run the phase's verification command.
5. If it passes, commit with the planned message, and the next phase can start.
6. Before the next phase, if the session is getting heavy, run `/clear` (chapter 15).

The prompts are versioned alongside the code: if you regenerate the project tomorrow, or a colleague walks the same path, they just follow the same list.

## 18.4 The Photogallery's CLAUDE.md

`CLAUDE.md` (chapter 7) is the file Claude Code loads at the start of every session. The Photogallery's calls itself the "project constitution" in its first line. It doesn't say what to build, because for content it defers to `REQUIREMENTS.md` and `DESIGN.md`. It says how the work gets done.

You don't write this one by hand either. The Photogallery prompt generated it together with the other three; if you're doing it separately, start here:

```text
Read docs/REQUIREMENTS.md, docs/DESIGN.md and docs/TASKS.md.
Generate a CLAUDE.md for the Photogallery project that contains:
- Documentation map: which file to read and when
- Project overview (3-4 lines)
- Tech stack with exact versions and install commands
- Non-negotiable rules, split into workflow and architecture
- Quality principles (SOLID, REST, KISS, DRY) with examples taken from
  this project, not generic definitions
- Parallelization rules and files not to modify in parallel
- Code conventions and git rules (branches, commit format)
- The meta-rule: always read docs/REQUIREMENTS.md and docs/DESIGN.md
  before implementing a task, and update the checkboxes in
  docs/TASKS.md as soon as the task is done
```

On the chapter's branch the resulting file is 276 lines long. Here it is trimmed, with the cuts marked `[...]`:

```markdown
# CLAUDE.md — PhotoGallery Pro

> The project constitution. Loaded into every Claude Code session. **Authoritative for HOW we work**; defers to `docs/REQUIREMENTS.md` (what to build) and `docs/DESIGN.md` (technical blueprint) for content. Atomic work lives in `docs/TASKS.md`.

## Documentation map

| File | Purpose | When to read |
|---|---|---|
| `CLAUDE.md` (this file) | How we work — rules, principles, style | Every session, automatic |
| `docs/REQUIREMENTS.md` | What we're building, in plain language | Before starting any task — read the relevant feature |
| `docs/DESIGN.md` | Technical blueprint — schemas, contracts, file paths | Before implementing — read the section the task references |
| `docs/TASKS.md` | 80+ atomic tasks across 13 phases | Pick a task; check it off when done |
| `docs/SPEC-REVIEW.md` | Decision log explaining why architectural choices were made | When you disagree with a rule and want context |

## Project overview

PhotoGallery Pro is a full-stack photo gallery: [...] The backend is a Laravel 13 REST API under `/api/v1` with a Filament v5 admin panel mounted at `/admin`. Image resizing and EXIF extraction run as queued background jobs so uploads return immediately. [...]

## Tech stack (with install commands)

[...] version tables and composer/npm commands for backend/ and frontend/

## Critical rules

These are **non-negotiable**. Violations require an explicit user override.

### Workflow rules

1. **Always read `docs/REQUIREMENTS.md` and `docs/DESIGN.md` before implementing tasks.** [...] If the task is ambiguous and the docs don't resolve it, stop and ask — do not guess.
2. **Always update `docs/TASKS.md` checkboxes after completing work.** [...] Don't batch — checking off six tasks at once means you've drifted.
3. **Use subagents for tasks marked `parallel: true` in `TASKS.md`.** [...]
4. **One task = one commit.** Conventional Commits format: `<type>(<scope>): <subject>`. Reference SPEC sections in the body. See DESIGN.md §15.3.
5. **Tests run before commits.** Test gates per task type live in DESIGN.md §15.2. No `--no-verify`, no `.skip`, no "tests later".

### Architecture rules (cite DESIGN.md sections in PRs)

[...]
8. **Every primary key is UUID v7** via the `HasUuidV7` trait. Stored as `CHAR(36)`. Never auto-increment for application tables.
9. **Two photo disks. All file I/O goes through them.**
   - `Storage::disk('photos')` — public-read; sized variants only
   - `Storage::disk('photos_private')` — private; originals only; signed URLs only

   Never use `File::`, `fopen`, `copy`, or `move_uploaded_file`. (DESIGN.md §11)
10. **Authorization, not just authentication.** Every mutating controller calls `$this->authorize($action, $model)` AND `$request->user()->tokenCan('photos:write'|'albums:write')`. (DESIGN.md §6.4a, §9)
11. **Wrap multi-write operations in `DB::transaction(...)`.** Photo upload (insert + tag attach + dispatch), photo update (update + tag sync), album with cover. (DESIGN.md §6.4a)

[...] rules 12-14: eager loading, Tailwind v4 setup, UI strings in frontend/src/data/

## Engineering principles (project-specific)

Generic principle definitions are useless. Here's how each applies to **this** codebase.

[...] SOLID, REST, KISS and DRY: covered in section 18.5

[...] Parallelization rules and Code style sections

## Before writing any class, ask:

[...]
3. **Does an existing service/contract already cover this?** Check `app/Contracts/`, `app/Services/`, `app/Actions/`, `app/Queries/` before creating new files.
[...]

## When stuck

- **Ambiguity in REQUIREMENTS.md:** ask the user; don't invent acceptance criteria.
- **Conflict between REQUIREMENTS.md and DESIGN.md:** REQUIREMENTS wins; DESIGN gets a `spec:` PR to align.
[...]
```

The rules that work are the ones you can check. "Handle files properly" says nothing; rule 9 says which disks exist, what goes on each and which PHP functions are banned. Rule 10 demands two specific calls in every controller that modifies data, and a review can check line by line whether they're there. "When stuck" covers the moments when an agent without instructions improvises. The references to `DESIGN.md §15` in rules 4 and 5 point to a section that doesn't exist; we come back to that in section 18.6.

An honest note: 276 lines is too many. In chapter 7 we saw that it pays to stay under about 200, because a long file eats context and gets followed less closely, and on `main` this one has grown to 391. The first candidates to move out are the style sections. PHP style, for example, can go into `.claude/rules/php.md` and load only for backend files:

```markdown
---
paths:
  - "backend/**/*.php"
---

# PHP code style
- Pint with Laravel preset; PSR-12 baseline.
- `declare(strict_types=1);` in app/Services, app/Actions, app/Jobs, app/Queries.
- Final by default. Mass assignment only via `$request->validated()`.
```

### Where CLAUDE.md isn't enough

`CLAUDE.md` steers Claude, but it doesn't bind it. "No `--no-verify`" is an instruction Claude follows almost always, and in a project with over a hundred tasks that "almost" shows up sooner or later. The permission rules from chapter 11 block a command no matter what the conversation says: a `deny` on `Bash(git push --force *)` holds even when a long session has lost track of its instructions. The hooks from chapter 12 do the rest. Phase 9 in `TASKS.md` already plans a few: Pint and Prettier after every edit and a block on destructive commands. For SDD the most useful is a `Stop` hook that runs `php artisan test --compact` and, if the tests fail, sends Claude back to work with the error. The harness enforces the definition of done.

`/goal`, which we use in chapter 20, applies the same idea to acceptance criteria: it turns them into a completion condition, and Claude keeps working until a separate evaluator judges it met. The evaluator sees only what Claude shows in the conversation, so the condition has to name a check Claude actually runs:

```text
/goal php artisan test --compact exits with code 0 and tasks T019-T045 in docs/TASKS.md are all marked [x]
```

## 18.5 SOLID, KISS and DRY in the workflow

You know the clean code principles. The hard part is getting them applied consistently by an agent that changes sessions and tends to add layers and abstractions for a future that won't come. That's why the principles live in `CLAUDE.md` and not in the prompt: there they survive `/clear` and new sessions, and every session starts already aligned.

The Photogallery's section opens with a line that sums up the method: "Generic principle definitions are useless. Here's how each applies to this codebase." Claude already knows the definition of SRP. What it doesn't know is which class in your project should have a single responsibility.

### SOLID applied to the specs

SOLID gets concrete results when you ask Claude to review the specs with those principles in hand: the output names files, classes and sections. The review of `SPEC.md`, saved in `docs/SPEC-REVIEW.md`, found among other things that `ImageProcessor` and `ExifExtractor` were concrete classes used directly by whoever needed them, and that all the filtering logic of `GET /photos` (search, AND tags, album, favorites, sorting) lived inside `PhotoController@index`.

The fixes went into the design and then into the code. For Dependency Inversion there are three interfaces in `app/Contracts/`, bound to their implementations in `AppServiceProvider`:

```php
$this->app->bind(ImageProcessor::class, InterventionImageProcessor::class);
$this->app->bind(ExifExtractor::class, PhpExifExtractor::class);
$this->app->bind(PhotoStorage::class, DiskPhotoStorage::class);
```

The job that processes photos receives the abstractions and doesn't know which implementation is behind them:

```php
final class ProcessPhoto implements ShouldQueue
{
    use Batchable, Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $tries = 3;

    /** @var int[] */
    public array $backoff = [10, 30, 60];

    public function __construct(public readonly Photo $photo) {}

    public function handle(ImageProcessor $processor, ExifExtractor $exif): void
    {
        // ...
    }
}
```

In tests you bind a `FakeImageProcessor` and the job doesn't notice: that's Liskov substitution, which `CLAUDE.md` writes down as a rule. The two interfaces are separate on purpose, because resizing an image and extracting its EXIF are two different reasons to change: Interface Segregation. For Single Responsibility, the filters moved out of the controller into `App\Queries\PhotoQuery`, which the Filament panel reuses too. A new sort order becomes a new case in `applySort()` and the controller stays untouched, which is Open/Closed shown with an example.

Then there's a mistake the review corrected that came from the original prompt. The SOLID section of `docs/PROMPT.md` says "PhotoController receives PhotoRepository, not raw queries"; further down, in the KISS section, "Don't create a Repository pattern if you only have one Eloquent model usage". Two conflicting instructions in the same prompt. The final `CLAUDE.md` went with KISS: no repositories, Eloquent used directly, logic in Actions, Services and Queries. When the prompt contradicts itself Claude picks on its own, and there's no guarantee it picks the same thing in two different sessions.

### KISS versus over-engineering

KISS is the hardest principle to get a model to respect. Without an explicit brake, Claude adds factories, builders, abstract base classes and indirection layers just in case, and the resulting code is correct but needlessly complicated.

The Photogallery's KISS section doesn't list virtues, it lists decisions:

```markdown
### KISS

The smallest implementation that meets the acceptance criteria wins.

- One upload endpoint (`POST /photos` accepts 1–20 files), not two. Frontend doesn't branch.
- One polling loop after upload (`GET /photos/batch/{id}` includes per-photo statuses), not two.
- Cursor pagination, not page+offset+`total` (the gallery doesn't need a count).
- Soft deletes are out of scope for v1. Deletes are permanent. We can add `deleted_at` later if undo becomes a requirement.
```

Almost every line comes from a simplification found in review. The original spec had two upload endpoints, `POST /photos` for one photo and `POST /photos/batch` for two or more, and two polling loops after upload. The sort parameter mixed different styles (`newest`, `title_asc`) and was split into `sort` and `order`. Other things Claude often proposes that are worth blocking up front: a filter DSL where URL parameters would do, an abstract base class for controllers, a Strategy pattern for an operation that has only one strategy.

![The KISS and DRY sections of PROMPT.md, the prompt the specs came from, in the IDE's Markdown preview](figures/cap-18/fig-02.png)

One technique that helps: ask for every rejected alternative to stay written down, with the reason. The Photogallery keeps `docs/SPEC-REVIEW.md` as a decision log, and `CLAUDE.md` points to it as the file to read "when you disagree with a rule and want context". A decision with its rationale next to it is hard to overturn mid-execution.

### DRY and the rule of three

DRY applied badly produces premature abstractions, which do more damage than the duplication they were meant to remove. The Photogallery's `CLAUDE.md` settles it in two lines: "DON'T abstract until the second occurrence. The third occurrence is when extraction becomes required." At the second repetition you wait; at the third you extract.

The concrete case: the review found the same tag-upsert-by-name logic in three controllers (photo create, photo update, batch upload). Today it lives in a single service, `App\Services\TagAssigner`, used by the API and by the Filament form:

```php
final class TagAssigner
{
    /**
     * @param  list<string>  $names
     */
    public function syncByNames(Photo $photo, array $names): void
    {
        DB::transaction(function () use ($photo, $names): void {
            $tagIds = [];

            foreach (array_filter(array_map('trim', $names)) as $name) {
                $tagIds[] = $this->resolveTag($name)->id;
            }

            $photo->tags()->sync($tagIds);
        });
    }

    // resolveTag() and uniqueSlugFor(): lookup by name, slug with suffix -2, -3, ...
}
```

The check before writing is in the "Before writing any class, ask" checklist: item 3 asks Claude to look in `app/Contracts/`, `app/Services/`, `app/Actions/` and `app/Queries/` before creating a new file. Claude does that search through the code, but only if a rule tells it to.

### Self-review before the commit

With the principles in `CLAUDE.md` you can ask Claude to review its own work before committing it:

```text
Before committing the current task, do a self-review of the code you
wrote. Check that it follows SRP, KISS and DRY as described in
CLAUDE.md. If you find violations, fix them, rerun the tests and then commit.
```

Self-review works because it has a precise reference point: the question becomes "is this upload inside `DB::transaction` as rule 11 says?". For a more serious review, done by a subagent with a clean context, there's `/code-review`, which also reads `CLAUDE.md`. We use it in chapter 22.

## 18.6 Critical analysis of the specs

First-pass specs are never right. The model produces elegant architectures, but on its own it doesn't check that the tasks cover every requirement or that the criteria can be measured. The step people skip most often is the one between generation and execution: rereading the files looking for ambiguities, risks and uncovered requirements.

### The spec critic

The method that works best is an agent with an adversarial role, in a clean session or as a subagent (chapter 10):

```text
Read docs/REQUIREMENTS.md, docs/DESIGN.md and docs/TASKS.md.
Your role is that of a skeptical senior engineer who has to find
everything that could go wrong before execution starts.

Produce a structured report with:
1. Security vulnerabilities in the specs (not in the code, in the specs)
2. Requirements with no matching task (coverage gaps)
3. Tasks with no matching requirement (potential out of scope)
4. Non-functional requirements with no planned implementation
5. Ambiguities that could lead different agents to different interpretations
6. Effort estimates that are optimistic by more than 50%
7. Circular or badly ordered dependencies in docs/TASKS.md
8. Cross-file references that point to sections that don't exist

For each problem: category, description, impact, suggested fix.
Don't be diplomatic. Your goal is to find problems, not to validate.
```

For each problem in the report, you decide whether it's a fair criticism or nitpicking. The fair ones go back into the specs, and only then do you start executing.

::: {.callout .callout-tip}
[Tip]{.callout-title}

A collaborative review, whether you do it or Claude does, mostly finds what you expect to find. Explicitly asking it to look for problems brings out the implicit assumptions and edge cases nobody had written down. That's what the last line of the prompt is for.
:::

### What changed in the Photogallery specs

On the Photogallery the review produced `docs/SPEC-REVIEW.md`: 272 lines of problems grouped by area (SOLID, REST, KISS, backend, frontend, database), then applied to `SPEC.md` in seven batches. Four changes concern security.

Originals were stored on the public disk. In `docs/SPEC-VALIDATION.md`, the comprehension check run on `SPEC.md` on April 25, the upload flow saved the original with `Storage::disk('photos')`, the same disk as the thumbnails, and the API response already included `urls.original`. The file landed on disk as it was, GPS included: from a photo taken in the backyard you could work out the home address of whoever uploaded it. In the corrected version there are two disks and the GPS data is gone before the file is saved:

```markdown
### 12.1 Two-disk model
- `Storage::disk('photos_private')` — originals only. Local: `storage/app/photos-private/`. Production: private S3 bucket with Block Public Access ON. URLs only via `temporaryUrl(...)` with 5-min TTL.
- `Storage::disk('photos')` — sized variants only. Local: `storage/app/public/photos/` + `php artisan storage:link`. Production: public S3 bucket fronted by CloudFront.
```

The matching requirement is in `REQUIREMENTS.md`, NFR-3: "GPS EXIF must be stripped before originals are stored and before any EXIF JSON is returned by the API."

Sanctum tokens had no abilities: a valid token could do anything the user could do. Now tokens carry abilities such as `photos:write` and `albums:write`, and rule 10 in `CLAUDE.md` requires every controller that modifies data to check both the policy and `tokenCan`.

Rate limits were per IP only, and behind a corporate NAT many legitimate users burned through the same limit together. Now non-auth routes also have a per-user limit, 300 requests per minute, and T039's acceptance criterion checks it.

The mass assignment surface wasn't covered by any rule. Now it is, written in two places in `CLAUDE.md`: `$model->fill($request->validated())`, never `$request->all()`.

You also need to check cross-file references, because splitting a large document breaks them easily. On the chapter's branch, `CLAUDE.md` points to `DESIGN.md §15.2` for test gates, `§15.3` for commits and `§14` for parallelization, and `TASKS.md` cites `DESIGN.md §14.4` for the magnet files and `§13` for hooks. But `DESIGN.md` stops at section 12: those sections exist only in `SPEC.md`, where they stayed after the split. And the documentation map talks about "80+ atomic tasks" while the file contains 112. An agent that follows a reference to a section that isn't there either stops or makes something up. That's why the spec critic prompt has item 8.

### Coverage questions

Beyond security, check coverage in both directions, from requirements to tasks and back. Four questions to ask every time:

```text
For each feature in docs/REQUIREMENTS.md, list the tasks in docs/TASKS.md
that implement it. Flag features with no task.

For each acceptance criterion in docs/REQUIREMENTS.md, tell me which
task has it in its Acceptance section. Flag orphan criteria.

For each NFR (performance, scalability, security), tell me which choice
in docs/DESIGN.md or which task in docs/TASKS.md guarantees it is met.
Flag NFRs with no planned implementation.

Find dependency cycles in docs/TASKS.md. Find tasks that depend on
tasks in later phases.
```

On the chapter's branch these questions find real holes:

- NFR-1 asks for a gallery time-to-first-tile within 1.5 seconds on a 5 Mbps connection, and no task cites it.
- NFR-1 also asks for a Lighthouse score of at least 90 on desktop and 75 on mobile; T108 checks desktop only.
- AC-F1-2 wants 2 columns at 375 px, 3 at 768 and 4 at 1280. `DESIGN.md §8.4` has the right classes (`columns-2 md:columns-3 lg:columns-4`), but T067's criteria don't name the breakpoints, so no test will check them.

GPS stripping, on the other hand, is covered: T074 asks for a test with an image that contains GPS coordinates, and T080 checks it again at the end of Phase 6.

When you find a hole, don't patch it by hand. Ask Claude to insert the missing task in the right phase and update the dependencies:

```text
Based on the gaps you identified, add the missing tasks to the
appropriate phases, update the dependencies and realign CLAUDE.md if
the references change. Don't touch the tasks already defined: only add.
```

### Estimating effort in the risky areas

The model is optimistic about time, too. With 112 tasks of 30 minutes at most, the theoretical total stays under 60 hours; the Photogallery review instead estimated 15-20 days of sequential work and 8-10 with three parallel tracks. Almost all of the difference sits in a few areas, which you should review and split where needed.

The async pipeline. Writing `ProcessPhoto` is easy; handling its failures isn't: retries with 10, 30 and 60 second backoff, a `failed` status, cleanup of already generated variants in the `failed()` method, consistency between the status in the database and the files on the disks.

The upload. Drag and drop and file picking are two interfaces on the same endpoint, with a per-file progress bar, client-side validation and batch polling. What looked like one task often turns into three.

The lightbox. It looks like one component, but it includes keyboard navigation, prefetching, a focus trap and a `?photo=` URL that opens the photo on load.

Local versus production. Locally, SQLite or MySQL, a database queue and the local disk; in production, MySQL or Postgres, SQS and two S3 buckets. The migrations have to stay neutral and the queues need testing in both setups, which is why the move to AWS is a phase of its own in the Photogallery, Phase 8.

### When to stop

One or two review rounds are normal. If you need three or more, the problem is upstream: the requirements were too vague, and you're better off rewriting them before going further.

When the specs convince you, without expecting them to be perfect, commit the four files, run `/clear` (the specs are on disk, there's no need to keep them in the conversation) and go. With a clean context Claude reads `CLAUDE.md`, then `docs/TASKS.md`, picks the first task whose dependencies are satisfied and starts. That's what we do in chapter 19.

## Summary {.unlisted}

- The three files separate what to build (`docs/REQUIREMENTS.md`), how to build it (`docs/DESIGN.md`) and in what order (`docs/TASKS.md`); `CLAUDE.md` says how the work gets done and points to the others.
- Every task declares dependencies, parallelism, sections to read and acceptance criteria: the specs decide what can run in parallel and what can't.
- The build workflow gives each phase a prompt, a verification command and a commit message. A phase is done when the verification passes.
- SOLID, KISS and DRY in `CLAUDE.md` work when they name the project's classes and decisions. Rules that must never be skipped need permissions and hooks (chapters 11 and 12), and acceptance criteria can use `/goal` (chapter 20).
- Before executing, run an adversarial spec critic and the coverage questions: every non-functional requirement needs a task that verifies it, and every cross-file reference has to point to a section that exists.

## Exercise {.unlisted}

Take a project of yours with at least five distinct features, create a branch (for example `sdd-my-project`) and generate the three files with the prompt from section 18.2. Run the spec critic from section 18.6 in a clean session, sort the problems into critical, important and nitpicks, and apply the fixes from the first two groups to the specs. For comparison, the Photogallery result is on the `book/cap-12-sdd-three-files` branch of the companion repository.

The exercise is done when every NFR in `docs/REQUIREMENTS.md` appears in the acceptance criteria of at least one task, the files are committed on your branch, and you've found at least three problems you hadn't seen before the spec critic. If you don't get to three, the review wasn't adversarial enough: run it again and explicitly ask it to be harsher.
