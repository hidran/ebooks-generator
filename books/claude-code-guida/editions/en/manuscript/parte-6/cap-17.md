# Chapter 17. Photogallery, from prompt to specs

::: {.chapter-goals}
[What you'll learn]{.callout-title}

How to get from a ten-line idea to a spec that Claude Code can execute without making anything up: picking the stack from the requirements, iterating a brief until it becomes a megaprompt, generating the spec and reviewing it one area at a time, and knowing when to stop.

[Prerequisites]{.callout-title}

Chapters 1-16 (chapter 7 on `CLAUDE.md` above all) and web basics: REST APIs, relational SQL, token authentication. You'll meet Laravel and React through the specs.

:::

So far you've worked on small, contained projects: a Python script, a data analysis, a landing page. Starting with this chapter we build Photogallery, a full-stack application for managing photos, and take it all the way to a deploy on AWS. It's small enough to keep in your head and rich enough to force the decisions that matter: authentication, file uploads, queues, many-to-many relationships, pagination, search, cloud. You already know the domain, so your attention stays on the technical choices. The features:

- upload of JPEG, PNG and WebP photos up to 10 MB each, 1 to 20 files at a time;
- albums, tags, and search by title, description, tag, album and favorites;
- a masonry grid gallery with a full-screen lightbox and keyboard shortcuts (`←`, `→`, `Escape`, `F`, `Delete`, `/`);
- asynchronous processing: the upload responds right away, then a queued job generates three sizes (300, 800 and 1600 px wide) and extracts the EXIF data;
- the same code locally and in production: local disk and a database queue on your laptop, S3 and SQS on AWS, with only the environment variables changing;
- Sanctum token authentication and a Filament admin panel at `/admin`, with queue monitoring.

Here you pick the stack and write the specs. Chapter 18 turns them into the three canonical Spec Driven Development files, chapter 19 executes the plan with code review, chapter 20 runs the waves in parallel, chapter 21 adds features to a project already under way, chapter 22 does QA before the deploy, and chapter 23 ships everything to AWS with CloudFormation.

The code lives in the companion repo `github.com/hidran/claude-code-book-photogallery`, with one branch per phase. Branch names follow the first edition's numbering (see "How to read this book"): this chapter maps to `book/cap-11-prompts-and-spec`, which holds only prompts and specs.

## 17.1 The base prompt: picking the stack on purpose

The first prompt of a project carries more weight than the rest. If it's wrong, it produces plausible code that turns out to be wrong weeks later, when backing out is expensive.

### Describe the what, not the how

The temptation is to open with a list of technologies. The first prompt should describe the problem instead:

```text
I want to build a full-stack web application for a photo gallery.
Users must be able to:
- upload photos (JPEG, PNG, WebP, max 10 MB) one at a time or in batches
- organize photos into albums
- tag photos with free-form keywords
- search by title, tag, album and favorites
- view photos in a grid with a full-screen lightbox
- navigate with the keyboard arrow keys
- mark photos as favorites
- sign up and log in

There must be an admin panel.
The app must run locally for development and on AWS in production.

Don't pick the stack yet. First tell me which stacks
you'd recommend for this kind of project, with the tradeoffs
of each. I want standard, mature technologies, no hype.
```

The last sentence asks for a comparison before a choice. Instead of going straight to code, as in vibecoding, you use Claude as a consultant for the design phase. Notice what's missing, too: no framework, no database, no library. If you start from the stack, you rule out up front the solutions you hadn't thought of; if you start from the requirements, the stack follows from them.

::: {.callout .callout-tip}
[Tip]{.callout-title}

For design work and for specs, raise the reasoning level with `/effort high` (the selector goes from `low` to `xhigh`). For a single hard question, just write `ultrathink` in the message: it applies to that prompt only.
:::

### The alternatives Claude suggests

Claude answers with two or three candidate stacks, roughly like this.

Stack A: Node.js with Express or Fastify, PostgreSQL, React with Vite. One language, plenty of documentation, a simple deploy. The downside is that Express imposes no structure: you organize modules and layers yourself.

Stack B: NestJS with React, TanStack Query and MySQL. TypeScript everywhere, dependency injection and decorators out of the box, a modular structure that holds up as the project grows. The downside is a steeper learning curve and some boilerplate at the start.

Stack C: Laravel with Filament for the admin panel, and on the frontend either Inertia with React or a separate React SPA consuming a REST API. Fast development and an admin panel that's almost done. The downside is the mixed stack, PHP on the backend and TypeScript on the frontend.

All three are valid. The useful question is which one best fits your requirements, what your team already knows, and where it'll run in production.

### Reading the answer with a critical eye

Don't stop at the pros column. Ask follow-up questions about the requirements that weigh the most:

```text
For Stack B with NestJS: the admin panel needs CRUD,
filters, bulk actions and a widget showing the queue status.
How much of that do I have to write by hand?
```

```text
For Stack C with a separate React SPA: how do I handle
authentication? Sanctum in token mode or cookie mode,
and with what security tradeoffs?
```

These are the questions that surface the hidden tradeoffs. An admin panel with tables, filters, bulk actions and permissions written from scratch is weeks of work, even if it takes up one line in the requirements list.

### The choice: Laravel 13, Filament v5 and React 19

Photogallery uses Stack C in the separate-API variant. A Laravel 13 backend exposes a JSON REST API under `/api/v1`, the Filament v5 panel is mounted in the same application at `/admin`, and a React 19 SPA with Vite 6 and Tailwind CSS v4 consumes the API. The SPA authenticates with Laravel Sanctum tokens. The reasons come from the requirements, one at a time.

The admin panel is a requirement, and Filament covers almost all of it: resources with tables, filters, bulk actions, forms and widgets, inside the same app and on the same Eloquent models. With NestJS you'd have to write that panel.

"Locally and on AWS" translates into two abstractions Laravel already has: the `Storage` facade and the queue drivers. In development the disk is local and the queue runs on the database; in production they become S3 and SQS. The code always calls `Storage::disk('photos')` and only the `.env` file changes. Image processing is a queued job with retries and backoff, batch upload uses queue batching with the `job_batches` table, and Sanctum handles Bearer tokens for the SPA and the web session for Filament in the same project.

The frontend stays a separate SPA, in TypeScript. Inertia would have removed the API, but here a versioned API pays off: the SPA is built and deployed on its own, and the contract between the two sides becomes a document you can check. The database is relational, MySQL or MariaDB, with a FULLTEXT index for search and RDS in production. The last reason is the most practical one: the team knows PHP and Laravel, and the cost of learning a stack is a non-functional requirement like any other.

In the first draft of this project the choice was NestJS, to get TypeScript on both sides. It changed while the specs were being iterated, when the admin panel, queues and storage went from lines in a list to requirements with their own details. The workflow in the next chapters is the same with any stack.

Tell Claude about the choice, together with the constraints:

```text
I'm going with Stack C, in the separate-API variant:
Laravel 13 backend (JSON REST API) + Filament v5 for the admin,
React 19 + Vite 6 + Tailwind CSS v4 frontend as a separate SPA.
Reasons: Filament covers the admin panel; Laravel's Storage and queues
move from local to AWS by changing only the environment variables;
the team knows PHP and Laravel.

Constraints to respect in every spec:
- API under /api/v1
- SPA authentication with Sanctum tokens (Authorization: Bearer header),
  not cookies; Filament uses the standard web session
- Multipart upload to the API, 1 to 20 files per request;
  the response comes back immediately, resize and EXIF run in a queued job
- UUID primary keys on every table
- Tailwind v4 only with the @tailwindcss/vite plugin: no
  tailwind.config.js, no postcss.config.js

Use this choice for the whole project.
```

The constraints are there to prevent drift. Without them, Claude might propose cookie authentication in the specs, a `tailwind.config.js` that Tailwind v4 doesn't use, or the resize inside the controller: plausible choices that contradict what you decided. In the repo these constraints also land in the project's `CLAUDE.md`, among the critical rules. The fifth one reads "Tailwind v4 setup is non-negotiable."

### The anti-pattern of the unjustified choice

"I'm using React because I know it, Express because it's simple and MongoDB because I don't want to think about the schema." For a solo side project that works. For a project that has to hold up in production, or that someone else will maintain, it doesn't. Before the first file, ask yourself whether the stack can handle the non-functional requirements, whether the team knows it or can learn it at an acceptable cost, whether it has documentation and long-term support, and how it behaves in production across deploys, monitoring and debugging. Claude helps with each of these questions, if you ask them. One last useful check before you lock in the stack:

```text
List the three main risks of the stack I picked for Photogallery.
For each one, tell me how I'd see it coming and what I can do now,
during the spec phase, to reduce it.
```

If you can't answer for one of the risks, you're missing information: go back to the follow-up questions before you lock in the stack.

## 17.2 From the base prompt to the technical brief

The next step is the technical brief, a document a developer could use to build the system without asking you anything else. You write it before the code, and it stays the source of truth for the whole project. The difference from the base prompt is concrete:

| Base prompt | Technical brief |
| :---- | :---- |
| "Wants to upload photos" | 1 to 20 files per request, JPEG, PNG or WebP, 10 MB max each. The original is saved right away and the response is immediate; the three sizes and the EXIF are produced by a queued job, with 3 attempts |
| "User authentication" | Sanctum tokens for the SPA with the `Authorization: Bearer` header, web session for Filament. GETs are public; writes require a token and ownership of the resource |
| "Has to go to production" | Same code locally and on AWS: database queue and local disk in development, SQS and S3 in production. Only the environment variables change |
| "Users manage their photos" | Every photo and every album has an owner (`user_id`). In v1 deletion is permanent, with no soft delete; deleting an album leaves its photos without an album |

Every line of the base prompt leaves a decision to Claude, which will pick something reasonable but not necessarily what you had in mind.

### Round 1: the first draft

For the first draft, use a generic prompt that you'll also reuse on future projects. For Photogallery the context is the features from the base prompt, and the stack is the one you just picked, with its reasons.

::: {.callout .callout-prompt}
[Reusable prompt]{.callout-title}

Technical brief in a single session. Replace the fields in square brackets and iterate 2-3 times before you consider the brief ready. Points 5 and 6 are the topics of round 2.

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
:::

In the first draft you'll always find something missing, or something that doesn't match what you have in mind. Your job is to find the gaps and describe them precisely in the following rounds. What to look for:

- Are the features testable? "The user can search photos" isn't. "Search filters by title and description, by one or more tags combined with AND, by album and by favorites, with paginated results" is.
- Do the non-functional requirements describe observable behavior? "The app must be fast" isn't a requirement. "The grid has 2 columns on mobile, 3 on tablet and 4 on desktop" and "the upload response doesn't wait for the resize" are.
- Are the decisions justified? If the brief says Sanctum tokens, it should also say why: the SPA and the API are two separate artifacts, and the `Authorization: Bearer` header avoids the CSRF dance that cookies require.

### Round 2: deciding what stays out

A first draft tends to grow. Per-user storage quotas, audit logs, soft delete with a trash bin, comments under photos: they're sensible ideas, and each one weighs on the schema and the queries. A `deleted_at` column, for example, forces every query to exclude deleted records. Decide now what goes into v1 and write it down:

```text
Add an "Out of scope (v1)" section to the brief. List explicitly
what we won't build in the first version:
- soft delete and restore: deletions are permanent
- per-user quotas (storage, number of photos)
- comments, likes and reactions
- image editing (crop, rotate, filters), except
  EXIF auto-orientation on upload
- native iOS and Android apps
- two-factor authentication
- multilingual interface

For each item, add one line on why we're postponing it.
```

An item written down as out of scope also stops coming back in Claude's answers as an addition "for completeness". In the final project the list lives in `docs/REQUIREMENTS.md`, under "Out of scope (v1)".

### Round 3: upload and image processing

Upload is the most delicate part of the system, and there are two ways to do it.

With S3 presigned URLs, the client asks the backend for a signed URL and uploads the file straight into the bucket. The backend never touches the bytes and scales without effort, but validation happens when the file is already on S3, and in development you need a local S3 just to upload a photo.

With upload through the API, the client sends a multipart request to Laravel. A FormRequest checks type and size before anything is saved, the controller stores the original and responds right away, and the heavy work (resize and EXIF) goes to a queued job. The bytes pass through the backend, but with 10 MB files and at most 20 per request that's a cost v1 can afford, and the same code runs on the local disk.

Photogallery takes the second route. If upload ever becomes the bottleneck, presigned URLs are the natural next step, and the spec is the place to write that down. Round 3 defines the pipeline:

```text
Revise the upload section. Upload goes through the Laravel API
as multipart/form-data, 1 to 20 files per request.

When a photo arrives:
1. Save the original right away
2. Respond right away, without making the user wait
3. Queue a job that generates three sizes:
   - thumbnail: 300 px wide, JPEG quality 80%
   - medium: 800 px, quality 85%
   - large: 1600 px, quality 90%
4. The job also extracts the EXIF data (camera, ISO, aperture, etc.)
5. Track the status in the database: pending, processing, completed, failed
6. If the job fails, retry up to 3 times, then mark the photo as failed

In development: database queue and local filesystem.
In production: AWS SQS queue and S3 storage, same code, only the
environment variables change. For images use Intervention Image v3.

Update the brief with the flow and with the security implications:
who can see the original, and which EXIF data must not be published.
```

In the final spec, the security question produces two separate disks. `photos_private` holds the originals, which are never served publicly and can only be reached through signed URLs valid for 5 minutes. `photos` holds the three generated sizes and is public. GPS coordinates are stripped from the EXIF data before it's saved.

### Round 4: the brief becomes the megaprompt

After three or four rounds the brief contains details you wouldn't have written on the first try. In the repo the final version is `docs/PROMPT.md`, the megaprompt Claude generates the spec from. It describes what the app does, the two-folder architecture (`backend/` and `frontend/`), the database entities with their main fields, the round 3 pipeline, the endpoints under `/api/v1`, the Filament panel, the frontend features (down to the 300 ms debounce on search), authentication, errors, technical details such as Tailwind v4 without config files, the test plan, and finally the engineering principles: SOLID, REST, KISS and DRY, with examples taken from this project.

That last section came in a separate commit ("Adds SOLID, KISS, DRY principles"), and it's what makes the spec opinionated. An excerpt, in the repo's original English:

```text
### KISS (Keep It Simple)
- **No premature abstraction:** Don't create a Repository pattern
  if you only have one Eloquent model usage. Use the model directly.
- **No premature optimization:** Don't add Redis caching before
  measuring if the database is slow.
- **Standard Laravel patterns:** Use Eloquent, Form Requests,
  API Resources, Policies — NOT custom middleware stacks for
  things Laravel already provides.
- **Readable over clever:** A 10-line method that's obvious beats
  a 3-line method using closures within closures.
```

The end of the megaprompt says what to generate. At first it asked for a single file, `SPEC.md`; the latest version asks for four files (`CLAUDE.md`, `docs/REQUIREMENTS.md`, `docs/DESIGN.md`, `docs/TASKS.md`), and it's the bridge to chapter 18. The branch also has `docs/megaprompt-template.md`, the same structure with fields to fill in, ready for your own project.

Rewriting a paragraph of the brief takes minutes. Fixing the same mistake once it has become migrations, controllers and components means touching every file it spread to.

## 17.3 Generating the full specs

The brief says what you're building and why. The spec says how each piece works, in the form of a contract: the schema has those columns or it doesn't, the endpoint responds with that shape or it's wrong.

Take tags. The brief says "users tag photos with free-form keywords." Photogallery's final spec says:

- a `tags` table with a UUID `id`, a unique `name` VARCHAR(100), a unique `slug` VARCHAR(120), and Laravel-managed timestamps;
- the slug is derived from the name with `Str::slug()` in the model's `booted()` hook, and on a collision it gets a numeric suffix (`-2`, `-3`);
- tags are global, with no `user_id`: two users who use "sunset" point to the same record;
- the `photo_tag` pivot has a composite primary key (`photo_id`, `tag_id`), a `created_at` and `ON DELETE CASCADE` on both foreign keys;
- `GET /api/v1/tags` returns every tag with its photo count (`withCount('photos')`), unpaginated because the set is small;
- there's no `POST /tags`: a new tag is created by passing `new_tags[]` when uploading or editing a photo.

None of these lines can be derived from the brief, and with them Claude writes the migration, model, controller and tests without asking you anything.

### From the megaprompt to SPEC.md

The branch has two specs. `SPEC-original.md` is the first one, generated from a shorter prompt: about 13 KB, three application tables plus the pivot, an `is_favorite` flag on the photo, SQLite in development and PostgreSQL in production.

![SPEC-original.md in VS Code at the stack table, with Claude Code in the terminal below](figures/cap-17/fig-01.png)

`SPEC.md` is the final one, generated from the megaprompt and then reviewed: about 123 KB, almost 2,400 lines in 15 sections, from the database schema to the test and commit discipline, plus an appendix on environment variables. Keeping the first version around makes sense: comparing the two shows how much work the iterations do.

![SPEC.md side by side with its Markdown preview: the stack table with separate entries for development and production](figures/cap-17/fig-02.png)

Generating everything in one go from the megaprompt is fine. Reviewing it all in one go isn't: read a document that size end to end and you'll approve inconsistencies you'd spot right away one section at a time. So the review goes area by area, in the order the areas depend on each other: database, API, authentication, admin panel and frontend, build workflow. For each area, write a review prompt, read the diff and approve. One session per area keeps the context clean; use `/clear` between areas. The branch's review prompts are in English (`docs/database-refinement.md`, `docs/api-refinement.md`, `docs/claude-code-build-workflow.md`), and the ones below are the originals, as written.

### DB spec: schema and constraints

```text
Review the database schema in SPEC.md. For each table, make sure:
1. Every column has a type AND constraints (nullable, default, unique, foreign key)
2. Foreign key ON DELETE behavior is specified (cascade, set null, etc.)
3. The pivot table has a composite primary key
4. All timestamp columns are specified

Update the spec with any missing details.
```

Then read the schema like the DBA who has to approve the migrations. The points to check one by one:

- Does `photo_tag` have the composite primary key (`photo_id`, `tag_id`) and no separate `id`? With a generated id the same pair could show up twice; the composite key rules that out by construction.
- Does every foreign key declare `ON DELETE`? In Photogallery, deleting an album sets the `album_id` of its photos to `NULL`, and the photos stay; deleting the photo used as a cover sets the album's `cover_photo_id` to `NULL`; deleting a photo removes its rows in `photo_tag`, while the tags stay.
- Is there an index on every foreign key and on the columns used for filtering and sorting?
- Who writes the timestamps? The final spec says Eloquent manages `created_at` and `updated_at`: nullable columns, with no database-side default. If the spec says nothing, Claude decides for you.
- Are there circular dependencies? `albums.cover_photo_id` points to `photos`, and `photos.album_id` points to `albums`. The spec solves it with three migrations: first `albums` without the cover foreign key, then `photos`, and finally a migration that adds the constraint. Without that note the first `migrate:fresh` fails.

### API spec: endpoints and conventions

```text
Review the API section. For each endpoint, make sure:
1. All query parameters for GET /photos are listed with their types
2. The response format is described (what fields are included, nested relations)
3. Error responses are specified (which status codes, what message format)
4. The file upload endpoint specifies: multipart/form-data, field names

Update the spec.
```

Conventions get written once, at the top of the section, and every endpoint inherits them. In the final spec they're in section 6.0: base URL, content type, the `Authorization: Bearer` header, per-IP and per-user rate limits, the `{ "data": ... }` envelope, ETags on single resources. When you review one domain after another, have Claude reread that section before touching anything else, so the domains don't end up with slightly different conventions:

```text
Read section 6.0 of SPEC.md (envelope, pagination, error format,
rate limits). Then review the album endpoints and align them
with the same conventions as the photo endpoints.
```

### Auth spec: Sanctum tokens and a stated tradeoff

Filament uses Laravel's standard session with the `web` guard. The SPA uses Sanctum in token mode: the endpoints are `register`, `login`, `logout` and `me`, login returns `{ "data": { "token": ..., "expires_at": ..., "user": ... } }`, the token lasts 24 hours, and Axios adds it as an `Authorization: Bearer` header.

The most useful part of the section is a decision written down together with its consequences. The token sits in `localStorage`, under the `pgp_token` key, where any script injected through an XSS attack can read it. The safer alternative is Sanctum's cookie mode, which costs a more complicated CSRF flow. The spec picks the token and puts the mitigations in writing: a 24-hour TTL instead of 30 days, a strict Content Security Policy in production, `dangerouslySetInnerHTML` banned by an ESLint rule, and tokens with limited abilities (`photos:write`, `albums:write`) that never reach admin permissions. It also sets the condition for changing course: if multi-user use becomes the main case, you switch to cookies. Written down like that, the decision doesn't get reopened in every session.

### Admin and frontend spec

Before a single line of React gets written, the spec has to say which pages require login, what the component hierarchy looks like, where server state lives and where local state lives, and how errors and a missing network are handled. The review prompt asks for routes, components with typed props, the main flows step by step and, for each TanStack Query query, the mutations that invalidate it.

The final spec answers with five routes (`/`, `/favorites`, `/albums/:albumId`, `/login` and a 404 page), every page loaded with `React.lazy`, server state only in TanStack Query, and an Axios client with `baseURL: '/api/v1'` that clears the token and redirects to `/login` when it gets a 401.

For Filament the spec goes down to the same level, resource by resource. The `PhotoResource` table shows the thumbnail, title, album, tags as badges, the favorite toggle and the processing status; the filters cover album, tags, favorites, dates and status; the bulk actions delete, assign to an album and rerun processing. The dashboard has three widgets, including the queue monitor.

![The preview of SPEC-original.md at the Filament panel section: resources, filters and bulk actions](figures/cap-17/fig-03.png)

### The build workflow

The last section to ask for is the build order:

```text
Add a section called "Claude Code Build Workflow" to the spec.
List the exact order to build, phase by phase:

Phase 1: Backend foundation (models, migrations, seed)
Phase 2: API layer (controllers, routes, resources, requests)
Phase 3: Filament admin panel (resources, widgets, dashboard)
Phase 4: React frontend setup (scaffold, Tailwind v4, API service)
Phase 5: React components (grid, lightbox, upload, sidebar, keyboard)
Phase 6: Image processing pipeline (job, queue, batch)
[... Phases 7-12: Filament queue monitoring, AWS migration, hooks,
testing, Git + PR, multi-agent parallel development ...]
Phase 13: Final spec check + deploy

For each phase, write the exact prompt to give Claude Code.
```

The result is section 13 of `SPEC.md`, the operator runbook. Each phase has a goal, a prompt to paste into Claude Code, a verification block to run, and the final commit message: Phase 1, for example, closes with `feat(backend): database schema, models, and seeders`. Every prompt from Phase 2 on is preceded by the same preamble, quoted here from the repo:

```text
You are working inside this repo. The spec is `SPEC.md` at the repo root — it
is authoritative. Read the sections referenced in the prompt and follow them
literally. Do NOT invent fields, endpoints, or file paths that aren't in the
spec. Run verification before claiming completion. Commit at the end with the
message specified in the prompt.
```

In chapter 18 these phases become `docs/TASKS.md`: 124 atomic tasks in 14 phases, with dependencies and notes on what can run in parallel.

### What's in the branch

At the end of this phase the `book/cap-11-prompts-and-spec` branch contains ten files:

```text
CLAUDE.md
SPEC-original.md
SPEC.md
docs/
  PROMPT.md
  megaprompt-template.md
  database-refinement.md
  api-refinement.md
  claude-code-build-workflow.md
  SPEC-REVIEW.md
  SPEC-VALIDATION.md
```

`SPEC-REVIEW.md` and `SPEC-VALIDATION.md` are the output of section 17.4. `CLAUDE.md` (chapter 7) says how to work in the repo and points to `SPEC.md` for what to build. One of its critical rules, "Ask before deviating", tells Claude to flag a point in the spec that looks wrong instead of silently fixing it.

## 17.4 Iterating on the specs: a stronger DB and API

Claude's first spec is a good starting point and nothing more. Like an experienced developer on a first pass, it gets the substance right and leaves gaps in the details that come from experience: explicit types, constraints, indexes, one response shape for every endpoint, pagination that holds up as the rows pile up. A reread that ends with "looks fine" only tells you there are no obvious errors. The real problems hide in implicit assumptions, like a column without `NOT NULL` or an endpoint with no 403 case.

### Iteration 1: explicit types and constraints

The quickest way to see what this iteration does is to compare the `photos` table in the two specs on the branch. A few rows from `SPEC-original.md`:

```text
| id          | uuid        | primary key, default uuid() |
| path        | string(255) | not null (storage path)     |
| file_size   | integer     | nullable (bytes)            |
| is_favorite | boolean     | default false               |
```

The matching rows, and the new ones, in `SPEC.md`:

```text
| id                  | CHAR(36)         | NOT NULL | —         | PRIMARY KEY (UUID v7) |
| user_id             | CHAR(36)         | NOT NULL | —         | FK users(id), ON DELETE CASCADE |
| original_path       | VARCHAR(500)     | NOT NULL | —         | private disk, never publicly served |
| thumbnail_path      | VARCHAR(500)     | NULL     | NULL      | populated by ProcessPhoto job |
| file_size           | BIGINT UNSIGNED  | NOT NULL | —         | bytes |
| processing_status   | ENUM('pending','processing','completed','failed') | NOT NULL | 'pending' | |
| processing_attempts | TINYINT UNSIGNED | NOT NULL | 0         | |
| processing_error    | TEXT             | NULL     | NULL      | exception message on failure |
```

The owner has appeared, because the authorization model says everyone can modify only their own photos. The single path has split into the private original and the three public sizes. `file_size` has become required and big enough, and the processing status now has its attempts and its error. Every change comes from a requirement that was already in the brief and hadn't reached the schema yet. After each review prompt, read the diff, not Claude's summary of it.

### Iteration 2: indexes for frequent queries

```text
Reread section 4 of SPEC.md and add the missing indexes for
Photogallery's most frequent queries:
- photos in an album, newest first: INDEX(album_id, created_at)
- sorting with favorites first: INDEX(is_favorite, created_at)
- queue dashboard in Filament: INDEX(processing_status, created_at)
- default sort by date: INDEX(created_at)
- search by title and description: FULLTEXT(title, description),
  queried with MATCH ... AGAINST

Also add the integrity constraints: UNIQUE on users.email,
UNIQUE on tags.name and tags.slug, composite UNIQUE (user_id, name)
on albums.
```

The FULLTEXT index replaces a `LIKE '%word%'`, which means reading the whole table. The album name is unique per user because two different users must both be able to have a "Travel" album.

### Iteration 3: cursor pagination

Offset pagination (`?page=5&per_page=24`) has a well-known problem. To get to the requested page, the database has to scan and discard every row before it:

```sql
SELECT * FROM photos ORDER BY created_at DESC LIMIT 24 OFFSET 100000;
```

This query reads 100,024 rows to return 24, and the Photogallery spec review flags the problem past 10,000 photos already. With cursor pagination the client passes an opaque cursor holding the position of the last item it saw, and the backend turns it into a `WHERE` condition on indexed columns: the cost stays the same anywhere in the collection.

```text
Update the list endpoints in SPEC.md to use cursor pagination
(Laravel's cursorPaginate()) instead of offset pagination.

- The query parameter becomes `cursor` (opaque string, optional)
- `per_page`: default 24, minimum 1, maximum 100
- The response includes `links` (first, next, prev) and `meta` with
  per_page, next_cursor, prev_cursor and path
- No total count: cursors don't need it

Primary keys must be UUID v7, sortable by creation time.
The default HasUuids trait generates v4: it has to be overridden.
```

The UUID v7 constraint is there for the cursors. A v4 UUID is random; a v7 starts with the creation timestamp. With v7, `ORDER BY id` is effectively `ORDER BY created_at`, and cursors stay stable while new photos arrive. Photogallery gets this with a trait, `HasUuidV7`, which overrides `newUniqueId()` and returns `Str::uuid7()`.

### Iteration 4: a uniform REST contract

The shape of the responses looks like a detail until you write the frontend, which turns into a collection of special cases when the envelopes differ. In the early drafts of Photogallery, login and favorites responded without an envelope; the final spec wraps every payload in `{ "data": ... }`, no exceptions.

```text
Review every endpoint in SPEC.md as a REST contract:
1. Every success response is wrapped in { "data": ... }, including login,
   registration and favorites
2. No non-idempotent toggles: favorite becomes
   PUT /photos/{id}/favorite (adds) and DELETE /photos/{id}/favorite
   (removes), both 204 and safe to repeat
3. A single upload endpoint, POST /photos, for 1-20 files: the client
   shouldn't have to choose between single and batch upload
4. Asynchronous operations respond 202 Accepted with a Location header
5. Every endpoint lists its own error codes on top of the
   universal ones (401, 429, 500)
```

For errors the spec keeps Laravel's standard format: a `message` field and, for a 422, an `errors` object with per-field messages. The exception handler in `bootstrap/app.php` produces it, and a middleware forces JSON on `/api/*` so that an HTML error page never reaches the SPA. The error table pins down the cases: 413 above 10 MB, 415 for any format other than JPG, PNG and WebP, 403 when the token's ability or ownership of the resource is missing.

### The full spec review

After the per-area iterations, what's left are the problems that come from sections crossing each other. For those you need a review of the whole document:

```text
Review SPEC.md against the SOLID, REST and KISS principles, plus the
specific best practices for the backend (Laravel), the frontend (React
and TypeScript) and the database (MySQL/Postgres).

For each issue, write an ID, the spec section, the principle
violated and the proposed fix. Group by area.

Add:
- a parallelization plan: dependencies between the build workflow
  phases and what can run in parallel
- a test and commit discipline: what a task is, which test is required
  before the commit for each kind of task, message conventions

Save the result to docs/SPEC-REVIEW.md. Don't modify SPEC.md yet.
```

The review on the branch, dated April 26, 2026, found, among other things:

- Filament's `PhotoResource` and the Laravel API Resource `PhotoResource` had the same name: the API ones become `PhotoData`, `AlbumData` and `TagData`;
- `StorageManager` and `ProcessBatchUpload` appeared in the folder structure without any section using them, and were removed;
- a queue worker with `--timeout=120` risks killing the resize of a large image, so an explicit size budget is needed;
- the lightbox and the modals had no focus trap, and error boundaries were missing.

The fixes went in as seven clusters, each one a separate change to `SPEC.md`. That way the spec stays the single source of truth, and `SPEC-REVIEW.md` stays in the repo as a decision log with the reasoning behind each decision. You don't have to accept everything: for each item, decide whether it happens now, later or never, and write the decision down. The review's parallelization plan, with its waves, comes back in chapter 20.

### When to stop

Specs will never be perfect, and chasing perfection is as much an anti-pattern as skipping them. A practical test: they're ready when you can answer questions like these without opening the file.

- What's the name of the column holding the path to the original? `original_path`, on the private disk.
- What happens to the photos when I delete an album? They stay, with `album_id` set to `NULL`, and the response is a `204`.
- What does the frontend do when it gets a 401? It clears the token and redirects to `/login`.

If an answer forces you to go looking, that section still needs work. You can have Claude take the same test. The branch has `docs/SPEC-VALIDATION.md`, a comprehension check done on April 25, the day before the review: it's worth running it before the review and again after every round of changes. The prompt goes something like this:

```text
Answer these questions using only SPEC.md. For each answer, cite
the section and reread it from the file; don't go from memory.
1. How many tables does the database have, and with which columns?
2. How many API endpoints are there? List them.
3. Which resources and widgets does the Filament panel have?
4. What are the three image sizes, with width and quality?
5. What are the keyboard shortcuts?
6. Which queue driver is used locally and which in production?
7. Describe the complete flow of a photo upload.
8. What happens when I delete an album? And when I delete a photo?
9. How does the monthly/annual pricing toggle work?
```

Claude counted nine tables (five application tables and four framework tables), eighteen endpoints, three resources and three widgets, each with its section. Question 9 is a trick question: Photogallery has no pricing or subscriptions, and the monthly/annual toggle belongs to the landing page from chapter 16. Claude answered that it isn't in the spec and probably belongs to the other project, without mixing the two up. If it makes up an answer instead, it's working from memory or from the wrong context, and you want to know that before execution.

### Saving the specs as a checkpoint

Before moving on to implementation, commit the specs: they're an artifact to share with your colleagues and to reread months later as documentation of the system.

```bash
git init
git add CLAUDE.md SPEC.md SPEC-original.md docs/
git commit -m "docs(spec): reviewed and validated SPEC.md for Photogallery v1"
```

The message follows the conventions the spec itself sets in section 15 (type, scope, subject). From here on, every change to the specs goes through a deliberate review.

## 17.5 Anti-pattern: skipping the specs and going straight to code

You have the stack in your head and you're itching to see something run: you ask Claude for the backend right away and figure you'll sort out the specs later. Try the experiment:

```text
Build a complete Laravel backend for a photo gallery.
Users log in, upload photos, organize them into albums, and tag them.
```

Claude generates code, probably decent code. Twenty minutes later you have models, migrations, a few controllers and login. It looks like a big step forward, until you look at the details.

The schema is a guess: `id`, `filename`, `path`, `user_id`. There's no processing status, because nobody said processing is asynchronous, and there are no paths for the three sizes. The owner column might be there, but the policies that enforce it aren't. The upload is synchronous and the resize sits in the controller: with one small photo it works, with twenty 10 MB photos the request times out.

Pagination is offset-based, because that's the most obvious default, and you notice when the photos pile up. The tests cover the happy path of the endpoints just written: without a spec to compare against, Claude has no way of knowing which error cases matter.

### The cost of rework

The trouble is that the code is flawed consistently: if thousands of lines follow the same wrong architecture, you fix the pattern everywhere it was applied. And the mistakes show up late in the work:

- You build the gallery and find that some endpoints respond with `{ "photo": {...} }`, others with `{ "data": {...} }`, others with a bare array. You either normalize the client or keep a parser per endpoint.
- You get to the deploy on ECS with several tasks behind the load balancer and find that photos land on the local disk of whichever container got the request. The worker that has to process them runs somewhere else and can't find them, and storage has to be rewritten.
- You add per-user favorites and find that `is_favorite` is a column on the photo, which means one favorite shared by everyone.

The last one happened to Photogallery too, specs in hand. `SPEC.md` has `is_favorite` on the `photos` table; later on, favorites become per-user, with a pivot table, and `docs/TASKS.md` has a phase just for it, 6.5 ("Favorites refactor"). Here the change starts from the spec, which says which migrations, endpoints and components to touch. You'll see it in chapter 21.

Without specs, at that point you either push ahead with the wrong architecture and pile up tech debt, or you start over and lose the time of the first attempt plus the time of the refactoring. You avoid both with a day or two of work on the specs before you touch the code.

### Spec Driven Development as the answer

Spec Driven Development, covered in full in chapter 18, tackles the problem in four phases:

1. Specs first, reviewed until they're clear: the phase covered in this chapter.
2. A plan from the specs: small, verifiable tasks, with acceptance criteria taken from the specs.
3. Code from the plan: if a case the specs don't cover turns up, you update the spec first, then the code (chapter 19).
4. Verification against the spec: at every phase the code does what the spec describes, no more and no less (chapter 22).

The result is code you can hand to another developer, or to Claude in a fresh session, knowing the specs are enough to carry on.

### When the specs change

Specs change, and that's normal: a requirement turns out to be ambiguous, a performance constraint comes out of testing, the client changes their mind about albums. With specs, change is deliberate. You update the file, commit with a message that explains why, and you track down the downstream consequences systematically. Without specs, the change stays in a conversation, and three weeks later nobody remembers why that column exists, or dares to touch it. Claude Code's auto memory (chapter 15) keeps preferences and corrections, but the log of design decisions belongs in a file versioned with Git, where everyone reads it: you, the team, and the next Claude session.

## Summary {.unlisted}

- The first prompt describes the problem and asks for alternatives; you pick the stack afterwards, with reasons taken from the requirements.
- Photogallery uses Laravel 13 as a REST API under `/api/v1`, Filament v5 for the admin, React 19 + Vite 6 + Tailwind CSS v4 for the SPA, and Sanctum tokens for authentication.
- You iterate the brief (first draft, out of scope, upload and pipeline), and the final version becomes the megaprompt `docs/PROMPT.md`.
- You can generate the spec all at once, but you review it by area: database, API, authentication, frontend, build workflow.
- A review against SOLID, REST and KISS and a comprehension check with a trick question tell you when the spec is ready.
- Skipping the specs pushes the problems to late in the work, when fixing them means touching every file.

## Exercise {.unlisted}

Pick a small personal project: a reading tracker, a notes manager, a portfolio. Then:

1. Open Claude Code in an empty folder and write the requirements prompt, with no stack.
2. Have Claude propose two or three stacks, ask at least two follow-up questions, and pick one with a written justification.
3. Iterate the brief for at least three rounds, including one on what's out of scope, starting from the reusable prompt in section 17.2 or from `docs/megaprompt-template.md`.
4. Generate the spec and review at least the database and the API, with one review prompt each.
5. Prepare a comprehension check with at least five questions, one of them a trick question.
6. Commit the spec, the prompts and the review.

The exercise is done when the repo has the commit with the spec and Claude, in a fresh session, answers every question citing the right section and says the trick question has no answer in the spec. Estimated time: 60-90 minutes. To compare your work with the book's, clone the companion branch:

```bash
git clone -b book/cap-11-prompts-and-spec https://github.com/hidran/claude-code-book-photogallery.git
```
