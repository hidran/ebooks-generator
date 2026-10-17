# Chapter 19. Execution and code review, from the first tasks to the wave review

::: {.chapter-goals}
[What you'll learn]{.callout-title}

How to execute the tasks in `docs/TASKS.md` with one commit per task, how to open the end-of-phase PR and get it reviewed, how to run a wave review with four specialized subagents, and what to check in the controllers, policies, exception handling and Filament admin panel of the Photogallery.

[Prerequisites]{.callout-title}

Chapters 17 and 18, with `docs/REQUIREMENTS.md`, `docs/DESIGN.md` and `docs/TASKS.md` ready (branch `book/cap-12-sdd-three-files`). The GitHub CLI (`gh`) authenticated, and the Superpowers and `commit-commands` plugins installed (chapter 8).

:::

After two chapters of specs, this is where you write code. `REQUIREMENTS.md` says what the Photogallery has to do, `DESIGN.md` says how, and `TASKS.md` splits the work into tasks of half an hour at most. That's why the execution prompt can be short: the context is already in the files.

The difference from vibecoding shows up later. When you reach task 47 and wonder why the primary keys are UUID v7 instead of auto-increment, the answer is already written down in rule 8 of the project's `CLAUDE.md` and in `DESIGN.md` §4.

The loop never changes: run a task, verify it, commit, move on to the next one. At the end of a phase you open a PR and get it reviewed. Review happens at three levels. The single task, while Claude works (diff read, tests green, linter clean). The phase, once the PR is open, with automated reviewers. And the wave, a group of phases that together build one piece of the architecture, where you hunt for inconsistencies between modules that you can't see one task at a time.

## 19.1 Executing the first tasks

### `TASKS.md` as project state

Before writing a single line, Claude checks the environment: whether there's a Git repository, whether there's an `origin` remote, the PHP, Composer and Node versions, and the tools the project needs. Then it reads `docs/TASKS.md`.

When execution started, the Photogallery's file held 112 tasks in 13 phases, with IDs like `T001`. Claude counts them, reports the number and proposes a realistic scope for the session: Phase 1, from `T001` to `T018`, because the whole plan won't fit in one context. In the final version of the repo there are 124 tasks in 14 phases; the extra ones come with the features in chapter 21.

The prompt to get going is deliberately simple:

```text
Proceed with the Phase 1 tasks according to docs/TASKS.md.
One commit per task, one pull request per phase.
Use subagents where tasks are independent.
```

It doesn't explain anything because it doesn't have to. The prompt starts the work; everything else is written in the specs.

### Independent tasks in parallel

Every task in `TASKS.md` has a `Parallel with` field. `T001` (scaffolding the Laravel backend) and `T002` (scaffolding the frontend with Vite and React) point at each other, with the note "different working dir": one works in `backend/`, the other in `frontend/`. Claude launches them as two subagents, and while one runs `composer create-project` the other runs `npm create vite@latest`.

You don't need a dedicated instruction for this. The dependencies are in the plan, and rule 3 of the Photogallery's `CLAUDE.md` says to use subagents for tasks marked as parallel. It's the same logic as independent jobs in a CI pipeline: where there are no dependencies, things run together.

::: {.callout .callout-warning}
[Warning]{.callout-title}

A subagent isolates context, not files: they all work in the same working tree. With `T001` and `T002` that's fine, since the folders are separate. But `T004`, `T005`, `T006` and `T017`, which are parallel with each other, all touch the same `backend/` and commit to the same branch. Two agents running `git add` and `git commit` at the same time can end up in each other's commits, and if two tasks touch the same file, the last one to write wins. That's why the project's `CLAUDE.md` lists the files that must never be modified in parallel (`bootstrap/app.php`, the migrations, `composer.json` and a few others). When a wave has many independent tasks, give each one its own worktree: chapter 20 does this with `claude --worktree`, `/goal` and agent view.
:::

### Permissions: fewer interruptions

Interactive sessions now start in auto mode (chapter 11). A classifier lets through actions consistent with your request and blocks risky ones, so commands like `composer install` or `php artisan migrate` usually go through without a prompt. If you work in Manual mode instead, every new command asks for confirmation, and in an execution session that adds up to dozens of prompts. Register the routine commands as `allow` rules in `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(composer *)",
      "Bash(npm install *)",
      "Bash(npm create *)",
      "Bash(php artisan *)",
      "Bash(vendor/bin/pest *)",
      "Bash(vendor/bin/pint *)"
    ]
  }
}
```

Add a rule when the whole family of commands is safe for that project, and stay away from `Bash(*)`: you want to cut the noise, not give up control. A Bash rule matches the text of the command, not the program (chapter 11).

### Don't move on if something is broken

A task gets checked off in `TASKS.md`, from `[ ]` to `[x]`, only when its `Acceptance` criteria are met: tests green (`vendor/bin/pest` in the backend), linter clean (`vendor/bin/pint --test`, ESLint in the frontend) and the diff read by you.

If a test fails, Claude stops. It doesn't check off the task with a promise to come back later. The project's `CLAUDE.md` spells it out: no `--no-verify`, no `.skip`, no "tests later". A broken task left behind resurfaces right when you're about to open the phase PR. Diagnose it on the spot:

```text
The PhotoObserverTest test is failing. Analyze the test, find the cause,
propose the fix, apply it and verify that the suite is green again before
moving on.
```

Keep that prompt handy, and never ask Claude to "ignore it for now".

### Atomic, traceable commits

After the first few tasks, `git log` shows messages that point back to the plan. Here are two commits from the `book/cap-13-wave-1-backend` branch, trimmed:

```text
chore(backend): scaffold Laravel 13 with core dependencies

T001 — DESIGN.md §2, CLAUDE.md "Tech stack".

Backend skeleton via composer create-project laravel/laravel ^13.0
(installs Laravel Framework 13.6.0).

chore(backend): publish framework migrations; tokenable_id is CHAR(36)

T003 — DESIGN.md §4.6, §4.7.

- Published Sanctum config and personal_access_tokens migration via
  vendor:publish.
- Edited the published migration to make `tokenable_id` CHAR(36) via
  uuidMorphs() so it can reference UUID v7 user ids (DESIGN.md §4.6).
  Also switched the token PK to uuid for consistency.
```

The Conventional Commits subject is the one suggested by the task's `Commit` field, and the first line of the body names the task and the `DESIGN.md` sections that govern it. Six months later, when someone asks why `tokenable_id` is `CHAR(36)`, you search the log for `T003` and land on `DESIGN.md` §4.6, written before the code. The traceability comes from the process, not from the goodwill of whoever commits.

Keep an eye on the last line of the second commit, "Also switched the token PK to uuid for consistency". The spec didn't ask for that. We'll come back to it in §19.2.

### Configuration tasks

The most tedious tasks to do by hand are configuration tasks: install a package, publish its files, add a key to `.env`. They need precision more than creativity, and Claude runs the steps in the right order without skipping any.

`T006` configures two disks in `config/filesystems.php`: `photos` (public, variants only) and `photos_private` (the originals). `T017` creates `config/photogallery.php`, copied from Appendix A of `DESIGN.md`:

```php
<?php

declare(strict_types=1);

return [
    'images' => [
        'max_dimension' => env('PHOTOS_MAX_DIMENSION', 8000),
        'max_file_size_kb' => env('PHOTOS_MAX_FILE_SIZE_KB', 10240),
        'variants' => [
            'thumbnail' => ['width' => 300, 'quality' => 80],
            'medium' => ['width' => 800, 'quality' => 85],
            'large' => ['width' => 1600, 'quality' => 90],
        ],
    ],
    'urls' => [
        'original_signed_ttl' => 300,
    ],
    'rate_limits' => [
        'auth_per_ip_per_minute' => 10,
        'api_per_ip_per_minute' => 120,
        'api_per_user_per_minute' => 300,
    ],
];
```

Limits that change between environments come from environment variables; everything else lives in exactly one place. Claude sticks to the convention because `CLAUDE.md` says to add every new variable to both `.env.example` and Appendix A in the same commit. Without that line it would have hardcoded the values.

The first reusable pieces show up too: the `App\Concerns\HasUuidV7` trait (`T004`) and two enums (`T005`), `ProcessingStatus` (`Pending`, `Processing`, `Completed`, `Failed`) and `TokenAbility` with the Sanctum abilities `photos:write`, `albums:write` and `admin`. The enums give the code the vocabulary of the specs, and a typo becomes a type error instead of a runtime bug.

### The domain takes shape

With the migrations from `T007` to `T012` the domain appears: users, albums, tags, photos and the `photo_tag` pivot with a composite primary key. The `photos` table has `original_path`, the three variant paths, `is_favorite`, `exif` as JSON, `processing_status` and the composite indexes that `DESIGN.md` §4.4 lists one by one. The models in `T013` follow `DESIGN.md` §5: `Album` has `belongsTo(User)`, `hasMany(Photo)` and `belongsTo(Photo::class, 'cover_photo_id')` for the cover.

The cover is the interesting case. The album points to a photo and the photo points to its album: a circular foreign key, which means neither table can be created first. The plan solves it with two tasks. `T008` creates `albums` with the `cover_photo_id` column but no constraint, and `T011` adds the foreign key once `photos` exists. Claude didn't have to invent anything, because the problem had already been spotted while writing the specs.

### When to stop

In a long session there comes a point where Claude proposes different names, contradicts earlier tasks, and forgets conventions it followed in the first twenty commits: the context is too full of stale detail. The default model's 1M-token window pushes the physical limit further out, but it doesn't stop the drift. Check with `/context` and use the tools from chapter 15. In the middle of a phase, `/compact` summarizes the conversation, with instructions on what to keep:

```text
/compact keep the state of the Phase 1 tasks, the decisions on UUID v7 and Sanctum, and the findings still open
```

Between phases, `/clear` starts from scratch and Claude rereads the updated state from the files, with the `TASKS.md` boxes checked. One phase per session is a good rhythm: a planned restart costs less than fixing five inconsistent commits.

## 19.2 The Phase 1 PR: first review

### Opening the PR at the end of the phase

When every Phase 1 task is checked off, the `feat/phase-1-backend-foundation` branch holds the commits for the 18 tasks, 21 in all counting the Pint cleanups and a fix to the migrations. Time to open the PR and stop.

With the `commit-commands` plugin it's a single command:

```text
/commit-push-pr
```

The full name is `/commit-commands:commit-push-pr`; the short one works as long as no other command uses the same name. It creates a branch if you're on `main`, commits whatever is left, pushes the branch and opens the PR with `gh pr create`. With the GitHub CLI by hand:

```bash
gh pr create \
  --title "Phase 1: backend foundation (T001-T018)" \
  --body "Fase 1 completa: 18 task, pulizia Pint, migration con foreign key e indici."
gh pr checks   # status of the CI checks
```

### The local test plan before any review

Before calling any automated reviewer, run the PR's test plan locally. It's the baseline check: the code has to run, not just exist. For Phase 1 the commands come from the criteria of `T018`, the phase's review task:

```bash
cd backend
composer install
cp .env.example .env
php artisan key:generate
php artisan migrate:fresh --seed
php artisan migrate:rollback
php artisan migrate
vendor/bin/pest
vendor/bin/pint --test
```

With Laravel Sail, which we'll get to shortly, the same commands go through `vendor/bin/sail artisan` and `vendor/bin/sail test`. If something doesn't run locally, reviewing the code in that state is pointless.

### Two independent reviewers

Once you know the code runs, use two independent reviewers, because different tools have different blind spots. The first is OpenAI's Codex connected to the GitHub repository. It comments on PRs by itself, inline on the diff lines, and it's good at local problems like a missing index or an extra field in `$fillable`.

The second is the Superpowers review, the `requesting-code-review` skill. In April 2026 it launched the `superpowers:code-reviewer` subagent, which is the one that signs the review of PR #1 in `docs/REVIEW-FIXES.md`; since version 5.1 of the plugin the skill hands the same checklist to a general-purpose subagent. It compares the code against the phase plan and the project rules, not just against the diff. In the first edition I wrote `/review` here. Today that command is an alias for a review built into Claude Code and no longer triggers Superpowers, so I ask for the review by name:

```text
Do the code review of the current PR with the Superpowers requesting-code-review skill.
Also process Codex's findings in the PR comments. Classify
everything by severity (BLOCKER / MAJOR / MINOR) and propose fixes starting
with the BLOCKERs.
```

### Classifying findings and iterating

The reviewer doesn't just list problems, it classifies them. Here are some real findings from PR #1, taken from `docs/REVIEW-FIXES.md` and summarized:

```text
[BLOCKER] photos.user_id has no index
  foreignUuid('user_id')->constrained() doesn't create the index on SQLite
  and PostgreSQL. DESIGN.md §4.4 lists it first. Add
  $table->index('user_id') to the photos migration.

[MAJOR] SANCTUM_TOKEN_EXPIRATION documented but never read
  .env.example declares 1440 (24 hours), config/sanctum.php has
  'expiration' => null. Tokens never expire.

[MAJOR] final missing on AppServiceProvider, DatabaseSeeder and factories
  CLAUDE.md asks for final classes by default.

[MINOR] processing_status in $fillable
  It's internal job state, not user input.
```

The working rule:

- BLOCKER: breaks a feature or opens a hole. Fixed before the merge, no exceptions.
- MAJOR: doesn't block, but it's a serious problem (performance, deviation from the spec, a project rule broken). Fixed in the same PR if possible.
- MINOR: style, naming, micro-optimizations. Tracked and handled in a cleanup PR.

Not every finding is fixed by changing code. Removing the `processing_*` fields from `$fillable` would have forced `forceFill()` throughout the job, and the real protection is the Form Requests, which don't accept those fields. The fix was a comment in the model explaining the choice (commit `75f93cd`).

When you hand a finding to Claude, the prompt is direct:

```text
There's this finding on the PR about Sanctum personal access tokens:
[finding text]. Verify it, fix it and add a test that covers the
case. Don't move on until the test is green.
```

Claude reads the finding, checks the code, applies the fix, adds the test and commits. If the review had already been run, it says so and doesn't start it again from scratch.

Once the BLOCKERs and MAJORs are resolved, you can merge. Then one last step that looks trivial:

```text
The PR has been merged.
```

Claude marks Phase 1 as closed and gets Phase 2 ready. Without that message it keeps treating the phase as in review.

![Eloquent patterns and validation rules collected during the review](figures/cap-19/fig-02.png)

<!-- TODO screenshot: fig-02 è a bassa risoluzione e il testo non si legge; rifare lo screenshot del documento di regole aperto nell'IDE. -->

### Laravel Sail: a dev environment close to production

The missing-index BLOCKER has a broader cause: the tests run on SQLite, production doesn't. SQLite is looser than MariaDB about constraints and behaves differently with some date and time functions, and the review log records this as its first lesson: problems like these don't make tests fail on SQLite and only show up on a real database. That's why, right after PR #1, the Photogallery adopted Laravel Sail (PR #2): Docker with MariaDB, Redis, Mailpit for email and MinIO, which emulates S3 locally.

```bash
composer require laravel/sail --dev
php artisan sail:install
```

Pick MariaDB, Redis, Mailpit and MinIO. Sail generates `compose.yaml` with the services and volumes. To start it:

```bash
vendor/bin/sail up -d
vendor/bin/sail artisan migrate:fresh --seed
```

`.env` points to `DB_CONNECTION=mariadb`, and local development gets very close to production. The same round brought a MINOR: Filament 5 requires PHP 8.4, so `composer.json` moved to `"php": "^8.4"` and CI and staging have to follow.

### When the review finds something the spec doesn't cover

Back to the `T003` commit. `DESIGN.md` §4.6 asked for a single change to the Sanctum table: `tokenable_id` as `CHAR(36)`, so it can point to users with UUIDs. Claude did something else too, "for consistency": it turned the table's primary key into a UUID. But Sanctum inserts a token without supplying an id, because it expects an auto-increment, and the first call to `$user->createToken()` would have failed with a NOT NULL violation. I caught it myself before the review started, and it went into the log as F0, the first BLOCKER. The fix (commit `fb39632`) puts the key back to `$table->id()` and adds `SanctumTokenTest`, which creates a token for a user with a UUID and checks the abilities.

The spec was right here, but rule 8 of `CLAUDE.md` ("every primary key is UUID v7") pushed in the wrong direction for a framework table. Specs start out good but not perfect, and the review catches the rest before deploy. When a finding exposes a gap in the spec, the fix doesn't stop at the code: update `DESIGN.md` or `REQUIREMENTS.md`, add the task to `TASKS.md`, cite the section in the commit. When it exposes an agent that went beyond the spec, as it did here, what you keep is the regression test.

## 19.3 Wave review: several agents on different aspects

### What a wave is

A wave is a group of phases or tasks that share an architectural goal and, once done, form one unit of the system. In the Photogallery the waves are written in `CLAUDE.md`, in the "Parallelization rules" section. Wave 0 is sequential and ends with the Phase 1 we just closed. Wave 1 has three parallel tracks: Track A is Phase 2, the API layer, followed by Phase 6, the image pipeline; Track B is Phase 3, the Filament panel; Track C is Phases 4 and 5, the React frontend.

Phase 2 alone is 27 tasks, from `T019` to `T045`, from middleware to tests. At that size, reviewing one task at a time isn't enough.

In this chapter we close Wave 0 and, of Wave 1, only Phase 2 of Track A. Phases 3 to 6 stay open: you run them in chapter 20, in parallel. The companion branches count waves differently: `book/cap-13-wave-1-backend` is Wave 0 of `TASKS.md` (the state at the end of Phase 1), and `book/cap-13-wave-2-api` is Track A of Wave 1 up to Phase 2. In the text I follow the names in `TASKS.md`.

### Task review and wave review

The task review asks "does this piece do what it was supposed to?", the wave review asks "do the pieces of this wave fit together consistently?". This level is where the sneakiest problems come out: one controller uses the query object and another doesn't, one mutation checks the policy and the one next to it doesn't, one endpoint answers errors in a slightly different format. None of these show up when you look at one task at a time.

### Four agents in parallel

The wave review launches several specialized agents in parallel, each on one aspect of the code, then merges their reports into a single document. The prompt for Phase 2:

```text
Wave review of Phase 2, API layer (tasks T019-T045).
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
   controllers that don't use the query object, inconsistent naming.

4. test-coverage
   Look for: critical paths without tests, missing edge cases, tests that
   bypass the policy, N+1 in tests, incomplete factories.

For each finding: file, line, severity (CRITICAL / HIGH / MAJOR /
MEDIUM / LOW), proposed fix. Merge the four reports into a single
document, in priority order.
```

The four subagents start in the background, like all subagents in interactive sessions, and you follow them with `/tasks`. Each one reads and searches the code (on the native macOS and Linux builds, search goes through `Bash`) and answers a narrow set of questions; within a few minutes you have the picture. They're read-only, so the shared working tree isn't a problem here. To reuse the roles on other projects, write them as subagents in `.claude/agents/security-auditor.md` and so on (chapter 10), or ask Claude to create them.

Claude Code also has a built-in command, `/code-review`, that looks for correctness bugs in the diff in the background. We use it in chapter 22 as a pass before deploy.

### Why specialize

A generalist agent looking at a controller looks at everything and nothing in depth. A specialized one applies its checklist to all the code: the security auditor looks for every entry point for untrusted data and every field that leaves in the response, and leaves naming to someone else. There's a second reason, written down as the last lesson in `docs/REVIEW-FIXES.md`: the session that wrote the code hadn't seen any of the problems the reviewers found later. A fresh agent, without the context of the commits, sees the code for what it is.

### The Phase 2 findings

On PR #4, the Phase 2 PR, the log records two parallel passes, the Superpowers code reviewer and a security auditor (we look at them in §19.4). Sorted by aspect, those findings fall into the four roles of the prompt.

Security. `PhotoData`, the photos API resource, returned `exif` and `processing_error` even to anonymous users. EXIF can contain GPS coordinates, and the processing error can contain fragments of internal paths. The fix applies to these fields the "owner or admin" check that already protected `urls.original`, with four tests in `PhotoDataTest` (on `main` the EXIF handling changed again, chapter 22). The second finding: the Laravel 13 scaffold doesn't publish `config/cors.php`, so the default policy with `*` origins was in effect. The fix publishes the file with the origin read from `FRONTEND_URL`, plus three tests in `CorsTest`.

Performance. In the photos `PATCH`, converting tag slugs to names ran one query per slug inside a transaction, with a fallback that would have used the slug as the name. The fix is a single query:

```php
$existingNames = $tags
    ? Tag::query()->whereIn('slug', $tags)->pluck('name')->all()
    : [];
```

The other N+1 was in the tests: `PhotoControllerIndexTest` allowed up to six queries, while cursor pagination plus the three eager loads in `PhotoData::WITH` need only four. A loose threshold lets an extra eager load slip through, so it was tightened to four.

API consistency. `AlbumController@index` built its query by hand instead of going through a query object like `PhotoQuery`. That finding was left open on purpose: an `AlbumQuery` with a single caller is premature, and the log defers it until the Filament panel needs it too. The second one mattered more: `AlbumController@store` checked the token ability but not the policy, while every other mutation checks both. Each controller looked fine on its own; comparing them is what exposed the gap.

Tests. `AuthorizationTest` verified the admin bypass by checking that the status was neither 403 nor 401, so a 500 would have passed as a success. The assertion now requires 200, 201 or 204.

Fix commit `3ece74b` takes the suite from 148 to 158 tests.

### Merging and prioritizing

Once the reports are in, build a priority list:

- CRITICAL: a confirmed vulnerability or functional bug. Fixed before the merge.
- HIGH: an authorization hole, data exposed to people who shouldn't see it. Same PR, before the merge.
- MAJOR: violated patterns, N+1 in production, inconsistencies between modules. Same PR.
- MEDIUM: N+1 in tests, `filename` visible to anonymous users. Follow-up PR.
- LOW: a missing cast, a useless `load()` before a `fresh()`, `final` missing on a few classes. A cleanup PR.

Resolve CRITICAL, HIGH and MAJOR before the merge. The rest goes into the backlog as GitHub issues so it doesn't disappear; in the Photogallery's log, deferred findings have a "Why deferred" line with the reason.

![The lessons learned from the reviews of PR #1 and PR #4, at the bottom of docs/REVIEW-FIXES.md](figures/cap-19/fig-01.png)

### Consistent naming: the wave review is the right moment

With separate sessions or parallel subagents, names drift: `PhotoData` in one file, `PhotoDto` in another, for the same thing. The Photogallery has the convention in `DESIGN.md` §6.6, but you need to check it before the names spread:

```text
Analyze the naming of all the API resources, query objects, form
requests and data objects in Phase 2. Find the inconsistencies (the same
concept with different names in different files) and propose an
alignment plan that preserves backward compatibility.
```

A naming cleanup during the wave review takes a few minutes. Done months later, when the wrong name has made its way into twenty files, it's a day of refactoring.

### One PR for the wave fixes

Keep the fixes separate from the phase work. On PR #4 they all went into `3ece74b`, with a message that lists every finding with its code (S1, S2, C1...) and the files touched. On a bigger wave, open a PR just for the fixes: the diff stays readable and the reviewer can assess it as a whole.

Then rerun the suite and check the routes:

```bash
php artisan migrate:fresh --seed
vendor/bin/pest
php artisan route:list --path=api   # every route registered under /api/v1
```

Finally, try the endpoints with an HTTP client, for example an `.http` file in the IDE. The expected responses for albums:

```text
GET    /api/v1/albums        200, { "data": [...], "links": {...}, "meta": { "next_cursor": ..., "prev_cursor": ... } }
POST   /api/v1/albums        201 with the created resource
PATCH  /api/v1/albums/{id}   200, or 403 if you're not the owner
DELETE /api/v1/albums/{id}   204, or 403
```

## 19.4 Targeted review: controllers, policies, exceptions

### Why a vertical review

The wave review is horizontal. You also need a vertical review, one that drills into a single aspect of the architecture and checks that every module follows the same pattern. In a REST API three aspects deserve it: controllers, policies and exception handling. The reference here is the Photogallery on Laravel 13, but the principles carry over well: NestJS has Guards instead of policies and Pipes instead of Form Requests, Django has Permissions and Serializers.

### Middleware: forcing JSON

Before the controllers there's a layer people often skip: the middleware that makes every API request get treated as JSON. Without it, a client that forgets `Accept: application/json` gets an HTML error page back. It's registered in `bootstrap/app.php` (`T019`):

```php
->withMiddleware(function (Middleware $middleware): void {
    $middleware->api(prepend: [
        ForceJsonResponse::class,
    ]);
})
```

The middleware is short:

```php
final class ForceJsonResponse
{
    public function handle(Request $request, Closure $next): Response
    {
        $request->headers->set('Accept', 'application/json');

        return $next($request);
    }
}
```

In review, check two things. The middleware sits in the `api` group, not in `web`, where it would break Blade pages and the Filament panel. And it runs before authentication, which is why it uses `prepend`: otherwise the 401 from `auth:sanctum` can go out without the content type the client expects.

### Exception handling

`DESIGN.md` §11.1 defines a single envelope for every non-2xx response under `/api/*`. In Laravel 13 you configure it in `bootstrap/app.php`, inside `withExceptions` (`T020`). An excerpt from the Photogallery code:

```php
->withExceptions(function (Exceptions $exceptions): void {
    $exceptions->shouldRenderJsonWhen(
        fn (Request $request) => $request->is('api/*')
    );

    $exceptions->render(function (AccessDeniedHttpException $e, Request $request) {
        if ($request->is('api/*')) {
            return response()->json(['message' => 'This action is unauthorized.'], 403);
        }
    });

    $exceptions->render(function (ThrottleRequestsException $e, Request $request) {
        if ($request->is('api/*')) {
            $retryAfter = $e->getHeaders()['Retry-After'] ?? 60;

            return response()
                ->json(['message' => 'Too many requests.'], 429)
                ->header('Retry-After', (string) $retryAfter);
        }
    });
})
```

The full file also handles 401, 404, 413 and 415. The 422 stays Laravel's own, which already has the `{ message, errors }` shape.

The subtlest finding in this area ended up among the lessons in the log: Laravel 13 converts `AuthorizationException` to `AccessDeniedHttpException` and `ModelNotFoundException` to `NotFoundHttpException` before the `render` callbacks run. If you type-hint the callback with the original exception it never fires, and the client gets the default message instead of your envelope. In the code above the types are the already-converted ones, and a test with `assertExactJson` verifies it. Two more things to check: the 429 needs a consistent payload and the `Retry-After` header, and 5xx exceptions must never be swallowed. If you catch an exception with a `try/catch` and respond, log it first or rethrow it.

### Controllers: the pattern that doesn't change

Every controller in this API follows the same shape: an explicit return type (`JsonResponse`, `AnonymousResourceCollection`, `Response` for the 204), a Form Request for every mutation, output always through an API resource, and a double authorization check. Rule 10 of `CLAUDE.md` asks for exactly that: every mutation checks the Sanctum token ability and the policy. An excerpt from `AlbumController` after the PR #4 fix:

```php
public function store(StoreAlbumRequest $request): JsonResponse
{
    $this->ensureAbility($request, TokenAbility::AlbumsWrite);
    if ($request->user()?->cannot('create', Album::class)) {
        throw new AuthorizationException;
    }

    $album = Album::create([
        ...$request->validated(),
        'user_id' => $request->user()->id,
    ]);

    $album->load(AlbumData::WITH)->loadCount('photos');

    return AlbumData::make($album)->response()->setStatusCode(201);
}

public function destroy(Request $request, Album $album): Response
{
    $this->ensureCan($request, 'delete', $album);

    $album->delete();

    return response()->noContent();
}
```

`ensureCan()` is a private method that runs both checks together. The `create` policy currently always returns `true`: it exists so that mutations are symmetric and the rule can be tightened without touching the controller. Watch out if your project uses `$this->authorize()`: in Laravel 13 the scaffold's base `Controller` is empty, and without the `AuthorizesRequests` trait that method doesn't exist.

The checklist for each controller in the wave: output always from a resource (`AlbumData::make()`, never `response()->json(['data' => $album->toArray()])`), eager loads from the `AlbumData::WITH` constant, mutations with `$request->validated()` and never `$request->all()`, multiple writes inside `DB::transaction()` (rule 11).

### Policies: strict ownership and an admin bypass

Policies decide who can do what. In the Photogallery they're deliberately flat, just the ownership rule:

```php
final class AlbumPolicy
{
    public function create(User $user): bool
    {
        return true;
    }

    public function view(User $user, Album $album): bool
    {
        return $album->user_id === $user->id;
    }

    public function update(User $user, Album $album): bool
    {
        return $album->user_id === $user->id;
    }

    public function delete(User $user, Album $album): bool
    {
        return $album->user_id === $user->id;
    }
}
```

The admin bypass lives in one place, `AppServiceProvider::boot()`, and covers every policy:

```php
Gate::before(fn (User $user) => $user->isAdmin() ? true : null);
```

This is exactly where the classic finding sits: a `before` (in the Gate or in a policy) that returns `false` for non-admins. `false` denies everything immediately, including actions the policy would have allowed. The correct contract is `true` for admins and `null` for everyone else, which lets the normal check continue.

The second typical finding is an unregistered policy. Laravel finds it by itself if it's called `AlbumPolicy` and lives in `app/Policies`; otherwise you need `#[UsePolicy]` on the model or `Gate::policy()` in a service provider. A policy that's never called blocks nobody, and the code looks like it works. The third comes with child resources: if the Photogallery ever gets private albums, a photo's visibility will have to go up to the album, not stop at `photo.user_id`.

### One format for every error

If exception handling was done at the start of the wave, as it was here with `T020`, every error goes out in the same format. The review has to check that every controller goes through it. The expected formats, from `DESIGN.md` §11.1:

```text
422  { "message": "The name field is required.", "errors": { "name": ["..."] } }
403  { "message": "This action is unauthorized." }
404  { "message": "Resource not found." }
```

If a controller throws its own `abort(403, 'Forbidden')`, the frontend has to handle a special case: every exception to the format is an integration bug waiting to happen. The quickest check is an unauthorized request against every endpoint. In the Photogallery `AuthorizationTest` (`T040`) does this: it goes through every mutation and checks for 401 without a token and 403 with another user's token.

### Two agents on the same PR

Once you understand the code, the practical step is to launch two agents in parallel on the PR. That's what happened on PR #4:

```text
Do a code review of PR #4 that covers best practices and security
checks. Launch the Superpowers code-reviewer and a security auditor
in parallel.
```

The code reviewer looks at quality, project rules and adherence to the spec; the security auditor looks at vulnerabilities, authorization, input, CORS and secrets. You get two reports to consolidate, just as with two human reviewers on a sensitive PR. On PR #4 the security auditor also found a problem no local test could have shown: without `trustProxies`, behind a load balancer `$request->ip()` returns the proxy's address, and the limit of 10 logins per minute per IP turns into a single bucket shared by everyone. The fix reads `TRUSTED_PROXIES` from `.env`.

## 19.5 Code review of an admin panel (Filament)

### Why the admin panel deserves its own review

The admin panel often gets treated as "the internal part", used only by admins and therefore less critical. But the panel sees all the data, runs bulk operations on thousands of records and usually has fewer tests than the public API. A dedicated review puts back the checks that are routine on the API.

In the Photogallery the panel is built with Filament 5, a Laravel framework that gives you CRUD, dashboards, widgets and forms out of conventions and ready-made components. It's Phase 3, from `T046` to `T054`: Track B of Wave 1, which at the end of this chapter still hasn't been run and which chapter 20 runs in parallel with the API and the frontend. This section is the checklist to apply when Track B comes up for review; the code in the examples comes from the repo on `main`. Laravel backend, REST API, React frontend, Filament admin: the wave review works on every layer, only the checklist changes.

### Check that everything works in the browser

Before the code, open the browser. Claude generates resources, widgets and pages, but the integration can still fail: calls to the wrong host, CORS origins that don't match, a backend URL hardcoded in the code.

In the Photogallery, when the panel and the frontend landed, manual testing found two problems right away:

1. The React frontend was calling the Vite dev server host (port 5174) instead of the backend on port 80. No error in the code, just the wrong URL in the axios client.
2. With the URL fixed, a CORS error showed up: `FRONTEND_URL` in the backend's `.env` pointed to `localhost:5173`, the default Vite port the project had been initialized with, while the dev server was running on 5174 because 5173 was taken.

The rule that comes out of it: no URLs in the code and no ports taken for granted. The client reads the API base from an environment variable:

```bash
# frontend/.env.example
VITE_API_BASE_URL=http://localhost/api/v1
```

```ts
// frontend/src/api/client.ts
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api/v1',
});
```

`.env.example` goes in the repository, the real `.env` stays local, and in staging you just set the right value. The same goes for `FRONTEND_URL` in the backend, which feeds `config/cors.php`.

### The checklist for a Filament panel

Bulk operations. Every action on a multiple selection must ask for confirmation. In Filament 5 actions live in `Filament\Actions` and attach to the table with `toolbarActions()`. An excerpt from `PhotosTable`:

```php
->toolbarActions([
    BulkActionGroup::make([
        DeleteBulkAction::make(),
        BulkAction::make('reprocess')
            ->label('Reprocess')
            ->icon('heroicon-o-arrow-path')
            ->color('warning')
            ->requiresConfirmation()
            ->action(function (Collection $records): void {
                $records->each(function (Photo $photo): void {
                    $photo->update([
                        'processing_status' => ProcessingStatus::Pending,
                        'processing_attempts' => 0,
                        'processing_error' => null,
                    ]);
                    ProcessPhoto::dispatch($photo);
                });
                Notification::make()->title('Reprocessing dispatched')->success()->send();
            }),
    ]),
])
```

`DeleteBulkAction` asks for confirmation on its own; a hand-written `BulkAction` doesn't until you add `requiresConfirmation()`, and one wrong click requeues hundreds of jobs. An audit log of bulk operations (who, when, on which records) is useful too, for example with `spatie/laravel-activitylog`.

Filters and indexes. Every column used as a filter should have an index. The review compares the table's `filters()` with the migrations:

```php
// PhotosTable.php
SelectFilter::make('processing_status')
    ->options(ProcessingStatus::class),

// photos migration
$table->index(['processing_status', 'created_at'], 'photos_status_created_idx');
```

Filament doesn't warn you if the index is missing. You find out under load, with a full table scan.

Validation on two levels. In Filament, validation is declared on the field. `AlbumForm` makes the name unique per user:

```php
TextInput::make('name')
    ->required()
    ->maxLength(255)
    ->unique(
        ignoreRecord: true,
        modifyRuleUsing: fn (Unique $rule) => $rule->where('user_id', auth()->id()),
    ),
```

That rule only applies in the panel. Anyone calling the API goes through `StoreAlbumRequest`, with the same per-`user_id` uniqueness (`T025`). You need both, and the review checks that they say the same thing.

Authorization. The first gate is access to the panel: `User` implements `FilamentUser` and `canAccessPanel()` returns `isAdmin()`, so a regular user who opens `/admin` is sent back to the login (`AC-F11-1` in `REQUIREMENTS.md`). The second is the policies, which Filament uses (`viewAny`, `create`, `update`, `delete`) to show or hide pages and actions. The most common finding is a resource with no policy because "the panel is already behind the login": if a bug in `canAccessPanel()` lets a non-admin in, without policies they can do anything. The same goes for a missing method: Filament 5 allows the operation when the policy or its method is missing (for example `deleteAny`, which bulk actions use), unless a `Gate::before` denies it. `->strictAuthorization()` in the panel configuration turns every missing policy or method into an exception, and it's worth turning on for review.

Export and import. If the panel offers CSV export or batch import, you need a rate limit on the export, which could otherwise saturate the database and the disk, and validation of every imported row with the rules of the API's Form Request.

### The frontend components and the missing pipeline

In the same Wave 1, Track C (Phases 4 and 5, also in chapter 20) brings the first React components: the photo grid (`MasonryGrid`, `PhotoCard`), the lightbox, the upload modal, the sidebar and the keyboard shortcuts, from `T063` to `T071`. The components are wired to the API data, but the photos show the `processing` state instead of the image.

That's expected. The pipeline that generates the variants is Phase 6, from `T072` to `T080`, which comes after the API in Track A; until then the variants don't exist. Asking Claude to "fix the processing state" would be a mistake, because it would invent a shortcut outside the plan. The correct finding is "expected, resolved by Phase 6", after checking in `TASKS.md` that the dependency is written down: `T077` (the `ProcessPhoto` job) and `T079` (upload wired to the real jobs) are there. If they were missing, the review's fix would be to add the task, not to write code.

### Rules for any admin panel

What came out of the Filament panel applies to any admin, whether it's React Admin, Refine, AdminJS or a hand-built one:

1. Authentication isn't enough: every operation checks permissions.
2. Bulk operations always ask for confirmation, ideally showing the number of records involved.
3. Every filter in the UI has its own index, otherwise in production it turns into a full table scan.
4. API hosts, ports and paths come from environment variables; the `.env.example` in the repository is the contract between development and deploy.
5. Install the framework's guidelines before the first wave. For Laravel there's Laravel Boost (`composer require laravel/boost --dev`, then `php artisan boost:install`), which brings Laravel's conventions and an MCP server with tools like `search-docs` and `database-schema`. The Photogallery's `CLAUDE.md` contains its guidelines in the "Laravel Boost tools" section, but `laravel/boost` isn't in the repo's `composer.json`: if you clone the project and want those tools, install it yourself. Installed later, Claude can bring the existing code into line, but starting with the guidelines saves you the cleanup.
6. Code review and browser testing find different things: agents and Codex find bugs in the code, the panel open with the Network tab finds integration bugs. You need both before the merge, and the second one is on you.

## Summary {.unlisted}

- Execute the `TASKS.md` tasks one per commit, with the task ID and the `DESIGN.md` sections in the message body; check off a task only with tests green, linter clean and the diff read.
- Parallel subagents share the working tree: fine on separate folders, but for parallel tasks on the same code use the worktrees from chapter 20.
- Open the phase PR after a green local test plan, put two independent reviewers to work and classify findings as BLOCKER, MAJOR and MINOR; when a finding exposes a gap in the spec, update the spec as well as the code.
- The wave review looks for inconsistencies between modules: four read-only subagents (security, performance, API consistency, tests) and a single report sorted by severity.
- In controllers, check return types, Form Requests, resources and the double ability-plus-policy check on every mutation; in policies, `null` and not `false` for non-admins.
- The admin panel is as critical as the public API: confirmation on bulk actions, indexes on filters, validation on two levels, a policy for every resource, the API URL in an environment variable.

## Exercise {.unlisted}

Redo the Phase 2 wave review and compare your findings with the real ones.

1. Clone the `book/cap-13-wave-2-api` branch and create a local branch from commit `93f1070` ("chore: Phase 2 review"), the last one before the fixes: `git switch -c wave-review 93f1070`.
2. Run the local test plan with Sail (`vendor/bin/sail up -d`, `vendor/bin/sail artisan migrate:fresh --seed`, `vendor/bin/sail test`) and note how many tests pass.
3. Launch the wave review with the four-agent prompt from §19.3, adjusting the wave name and task range if you're working on your own project.
4. Compare the merged report with `docs/REVIEW-FIXES.md` at the tip of the `book/cap-13-wave-2-api` branch, section "PR #4".
5. For every CRITICAL or HIGH finding, ask Claude for the fix with a test that covers the case, and rerun the suite.

You're done when you have a findings document with a severity and status for every entry, the suite is green, no CRITICAL or HIGH findings are left open, and you've marked which findings in `REVIEW-FIXES.md` (S1 to S5, C1 to C8) your agents found and which they missed.
