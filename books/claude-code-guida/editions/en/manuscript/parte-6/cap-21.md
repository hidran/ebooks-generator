# Chapter 21. Features that show up mid-project

::: {.chapter-goals}
[What you'll learn]{.callout-title}

How to bring a feature into an SDD project that's already under way, first into the documents and then into the code, through three Photogallery cases: the batch photo pipeline moving to S3, the registration page the plan lost along the way, and favorites rebuilt from a boolean column into a pivot table. Then how to handle a PR that touches backend and frontend at the same time.

[Prerequisites]{.callout-title}

Chapters 17-20 (specs, SDD, wave execution, worktrees) and the companion repo on the `book/cap-14-phases-complete` branch.

:::

At the end of chapter 20, Wave 1 of `docs/TASKS.md` is merged into `main`: the Filament admin, the React frontend setup and components, and the image pipeline (Phases 3-6). The plan is moving along. Then one Tuesday at 5 p.m. the message arrives: "Oh, we also need a way to upload lots of photos at once, some people come back with 500 vacation photos. And registration? I didn't write it down, but it was obvious. And while you're at it, customers keep asking to save their favorite photos."

Mid-project requests show up even with the best specs. The stakeholder watches the application grow and remembers things they took for granted, or the market shifts the priorities. The sneakiest case is a different one: the feature was in the requirements, but it got lost when the requirements became tasks, and nobody noticed until the first manual test. You can't prevent these requests. What you can control is how they enter the project, without breaking what works and without losing track of the plan.

In the Photogallery, each of the three cases has a specific home. The batch work starts from the pipeline Track A built in chapter 20 and takes it to S3 and SQS, which in `TASKS.md` is Phase 8, in Wave 2. The missing registration is the gap between user story US-30 and task T070 in Phase 5, closed later by T121. Favorites are Phase 6.5, a phase inserted halfway through with wave number 1.5. The `book/cap-14-phases-complete` branch (290 files) holds the project with every phase from 3 to 14.

## 21.1 Batch photo processing on S3

### The requirement

The rule the pipeline rests on is already in `main`: the upload responds right away, and a worker pulls the heavy processing off the queue. The 500-photo request tests the limits that were chosen, and the move to S3 tests what you don't see locally: retries, transactions, file permissions.

These are the lines that matter from section F4 of `docs/REQUIREMENTS.md`:

```markdown
### F4 — Upload
- F4.2 Client-side validation: MIME (JPG/PNG/WebP), size (≤ 10 MB)
- F4.3 Up to 20 files per submission
- F4.6 Upload returns immediately; processing happens in the background
```

Acceptance criterion AC-F4-3 says that submitting 21 files shows "Up to 20 files at once" and blocks the submission. So the stakeholder's 500 photos become 25 submissions of 20: a limit decided up front and written into the requirements, so nobody discovers it in production.

### Documents first, then code

Every mid-project feature starts from the same prompt. I run it in Plan Mode (`Shift+Tab` until you see `plan mode on`, or `/plan`), so Claude reads and proposes without touching any files:

::: {.callout .callout-prompt}
[Reusable prompt]{.callout-title}

```text
I have a project with docs/REQUIREMENTS.md, docs/DESIGN.md and docs/TASKS.md
already in place. I want to add this feature: [FEATURE DESCRIPTION].

Do these steps in order:

1. Read the three files to understand the current state
2. Propose the section to add to REQUIREMENTS.md
   (requirements, constraints and explicit acceptance criteria)
3. Propose the changes to DESIGN.md (schema, endpoints, components)
4. Propose the tasks to add to TASKS.md, with dependencies, new IDs
   that don't collide with existing ones, and verifiable completion
   criteria
5. Before running any task, check whether the feature needs
   a DB migration and whether the code already has something similar
   that could conflict with it

Don't start executing until I've approved the changes to the three files.
```
:::

The step people skip is the fourth one. Without tasks in the plan, the new work floats free of dependencies, and Claude has no idea how to fit it into what's already done.

The S3 batch work doesn't need new phases: it's already in `TASKS.md` as Phase 8, "AWS migration (S3 + SQS via env vars)". The name states the intent: same code, only the `.env` file changes. What you have to decide is what to do now and what to leave for the deploy.

### From local disk to S3

Thanks to the Phase 6 contracts, S3 is a matter of configuration. `PhotoStorage` is bound to `DiskPhotoStorage`, and there is no `S3PhotoStorage` class: the class works on two Laravel disks, `photos_private` for originals and `photos` for variants, defined back in T006, and `PHOTOS_DRIVER` decides whether they're local folders or S3 buckets. The production block is in `DESIGN.md` §12.5:

```text
QUEUE_CONNECTION=sqs
SQS_QUEUE=photogallery-pro
SQS_REGION=eu-west-1

FILESYSTEM_DISK=photos
PHOTOS_DRIVER=s3
AWS_BUCKET_PUBLIC=photogallery-pro-prod
AWS_BUCKET_PRIVATE=photogallery-pro-prod-private
AWS_URL=https://cdn.example.com
```

Plus the `SQS_*` and `AWS_*` credentials, which are placeholders in the document. The private bucket holds the originals, with Block Public Access on and access only through 5-minute `temporaryUrl()` links. The public one holds the variants, behind CloudFront.

On the branch, Phase 8 is only partly done. T089 is complete: an audit that uses `grep` to look for `storage_path`, `storage/app`, `disk('public')` and `file_get_contents` inside `app/` and finds nothing outside `config/`. That's the task that matters right now, because a hand-written local path would break the pipeline the day the disks become buckets. T086 (`.env.production.example`), T087 (`docs/DEPLOY.md`) and T088 (the `smoke-aws.php` script) stay open until the deploy in chapter 23.

In development, Sail starts MinIO, and `backend/.env.example` already points the `AWS_*` variables there, suggesting you switch `PHOTOS_DRIVER` to `s3` to try the production path locally. First read the `s3` branch of the `photos` and `photos_private` disks in `config/filesystems.php`: it doesn't read `AWS_ENDPOINT` or `AWS_USE_PATH_STYLE_ENDPOINT`, and it takes the buckets from `AWS_BUCKET_PUBLIC` and `AWS_BUCKET_PRIVATE`, which are commented out in the example file. Without an `endpoint`, the AWS SDK goes to the real S3 addresses, so as it stands the `s3` driver doesn't talk to MinIO. The example file doesn't mention this, and it's worth turning into a task right away.

### The flow, briefly

To reason about retries and transactions you need to have in front of you what chapter 20's Track A left in `main`:

```text
Browser                 Laravel backend                Queue             Storage
   |                          |                         |                   |
   |-- POST /photos --------->|                         |                   |
   |   (1-20 files)           |-- strip GPS, original ------------------>  photos_private
   |                          |-- Photo rows (transaction)                  |
   |                          |-- Bus::batch(ProcessPhoto x N) -->|         |
   |<-- 202 + Location -------|                         |                   |
   |                          |                         |-- worker -------> photos
   |-- GET /photos/batch/{id} |                         |   (300/800/1600 px)
```

The controller responds `202 Accepted` with a `Location` header, and `useBatchPoll` polls the endpoint every second (`BATCH_MS` in `src/data/polling.ts`) until the response says `finished: true`. In development the queue is the database's `jobs` table. In production it's SQS, with the worker under Supervisor: `php artisan queue:work sqs --queue=photogallery-pro --tries=3 --timeout=180 --sleep=3 --memory=512` (`DESIGN.md` §12.6).

### Dispatching outside the transaction

Commit first, then dispatch. If you queue the job inside the transaction, a fast worker can pick it up before the commit, look for a row that doesn't exist yet, and fail with an error that doesn't point anywhere near the transaction.

On the branch, the action returns the jobs from the transaction closure and queues them afterwards:

```php
[$photos, $jobs] = DB::transaction(function () use ($files, $user, $albumId, $tagNames, $titles, $description): array {
    $photos = [];
    $jobs = [];

    foreach ($files as $index => $file) {
        // strip GPS, storeOriginal, Photo::create(...), tags, event
        $photos[] = $photo;
        $jobs[] = new ProcessPhoto($photo);
    }

    return [$photos, $jobs];
});

$batch = Bus::batch($jobs)->dispatch();
```

We didn't get there on our own: the end-of-phase review had flagged exactly this, a `Bus::batch()` inside `DB::transaction()`, as High. The report is in `docs/BATCH-2026-04-29.md`.

### The worker and idempotency

The job has to be **idempotent**: processing the same photo twice must give the same result, with no duplicate files or rows. It's the requirement people forget most easily, and without it every retry leaves garbage on S3.

```php
final class ProcessPhoto implements ShouldQueue
{
    public int $tries = 3;

    /** @var int[] */
    public array $backoff = [10, 30, 60];

    public function handle(ImageProcessor $processor, ExifExtractor $exif): void
    {
        $this->photo->update(['processing_status' => ProcessingStatus::Processing]);
        $processor->generate($this->photo);

        $absolutePath = Storage::disk('photos_private')->path($this->photo->original_path);
        $exifData = $exif->extract($absolutePath);

        // update: exif + processing_status Completed, then event(PhotoProcessed)
    }

    public function failed(\Throwable $e): void
    {
        report($e);

        $this->photo->update([
            'processing_status' => ProcessingStatus::Failed,
            'processing_error' => 'Processing failed. Please try again or contact support.',
        ]);
    }
}
```

On SQS, retries are business as usual: a worker that dies halfway, a timeout, a message that becomes visible again. The job allows three attempts, with waits of 10, 30 and 60 seconds. After the last one, `failed()` marks the photo as `failed` with a generic message, and the exception text, which can contain server paths, stays in the log (that came out of a review finding too).

Here idempotency comes from a deterministic key. `DiskPhotoStorage::storeVariant()` writes each variant to a path that depends only on the photo's UUID and the variant name:

```php
public function storeVariant(string $photoId, string $variant, string $contents): string
{
    $relativePath = "{$variant}/{$photoId}.jpg";

    Storage::disk('photos')->put($relativePath, $contents);

    return $relativePath;
}
```

A retry overwrites `thumbnail/<uuid>.jpg` in place instead of creating a second one, and an interrupted attempt doesn't leave half-written variants behind. A worker that makes up a new name on every run, with three attempts and submissions of twenty photos, fills S3 with orphaned objects, and you pay for every one of them.

There's one line in the job that can't work on S3: `Storage::disk('photos_private')->path(...)`. On a `local` disk it returns a filesystem path. On an `s3` disk it returns the object key, which `exif_read_data` can't open. If the file doesn't exist the extractor returns an empty array, so there's no exception: the photos just come out without EXIF. To be fair, on this branch EXIF is missing locally too, because `stripGps()` re-encodes the image and strips all the metadata along with the GPS before the original is saved. On the chapter 22 branch, EXIF is read at upload time, from the uploaded file and before `stripGps()`, and the job keeps it only as a fallback.

One last thing about batches. `UploadPhotosAction` calls `Bus::batch($jobs)->dispatch()` without `allowFailures()`, and with Laravel's default the first failed job cancels the batch, which from then on already counts as `finished`. The other photos still get processed, because `ProcessPhoto` doesn't check whether the batch was cancelled, but `useBatchPoll` stops polling before they're done. With `allowFailures()` the problem flips: a batch with one failure never reaches `finished`, and the polling never stops. If you need a reliable status, compute it from the batch's `Photo` rows, which the endpoint already returns one by one.

### When the backend becomes the bottleneck

On the branch, the photo bytes still go through the backend, which strips the GPS data and writes them to `photos_private`. For 20 files of 10 MB that's fine. If you needed hundreds of photos at a time, the next step would be direct upload to S3: the backend signs a short-lived presigned URL (15 minutes limits the damage of a leaked URL), the frontend does the `PUT` straight to the bucket and then notifies the backend, which creates the `Photo` row and queues the job. It comes at a cost: GPS stripping, which today happens before the original is saved, would have to move into the worker, and for a few seconds the original with its coordinates would sit on S3. At the Photogallery's scale the trade-off isn't worth it, and that's why F4.3 says 20 files.

### The 403 on the variants

During the T080 end-to-end test, the real upload with the queue worker running that chapter 20 leaves for you to do by hand, the variants were being generated, but the browser got `403 Forbidden` on the `medium` and `large` images. The `public/storage` symlink was correct, and a direct `curl` returned the same 403.

The culprit was the `serve` option on local disks. In Laravel 13, a `local` disk with `'serve' => true` registers a `GET <disk url>/{path}` route that serves the files through PHP, and a disk without a `url` registers it on `/storage`. The scaffold's `local` disk has `serve` turned on, so its `/storage/{path}` route was catching `/storage/photos/...` as well. For a private disk that route wants a signed URL: without a signature it answers 403, or 404 in production.

The configuration on the branch, in `config/filesystems.php`, turns `serve` on only for the public variants disk and removes it from the `local` disk:

```php
'local' => [
    'driver' => 'local',
    'root' => storage_path('app/private'),
    'throw' => false,
    'report' => false,
],

// ...

'photos' => env('PHOTOS_DRIVER', 'local') === 's3'
    ? [ /* s3 driver, bucket AWS_BUCKET_PUBLIC */ ]
    : [
        'driver' => 'local',
        'root' => storage_path('app/public/photos'),
        'url' => rtrim(env('APP_URL', 'http://localhost'), '/').'/storage/photos',
        'visibility' => 'public',
        'serve' => true,
        'throw' => true,
    ],
```

No unit test catches a bug like this. You need the full round trip, from the upload to the browser.

### The phase review

Alongside T080, the end-of-phase review kicked off, with Claude and Gemini on Phases 5 and 6. The `docs/BATCH-2026-04-29.md` report lists these findings, among others. The most serious was a path traversal: the variant paths used the file name sent by the client, and the fix uses the photo's UUID and `basename()` on the stored name. Then a temporary file from `PhpExifExtractor::stripGps()`, holding the full original with GPS, that was never deleted; on the branch a `register_shutdown_function` deletes it. There was the dispatch inside the transaction, covered above. And a High about photos being readable without authentication, which the design intends for the anonymous visitor in `REQUIREMENTS.md`: there the right answer was to confirm the intent, not to change the code.

The numbers at the end of the phase: 175 green backend tests (plus one skipped and a CORS failure that was already there), zero TypeScript errors, 110 KB gzipped for the main bundle after per-page code splitting (the budget is 200 KB).

::: {.callout .callout-deep-dive}
[Under the hood]{.callout-title}

On this branch, `GET /photos/batch/{batchId}` finds the batch's photos by user and by a `created_at` later than the batch's creation time, an approximation that two uploads close together will mix up. The `batch_id` column on `photos` arrives with the chapter 22 fixes (`book/cap-15-post-review-fixes`).
:::

## 21.2 The missing registration page

### How you find out

Walk through the app from scratch as a new user and you'll find a well-built login page, with validation and server errors. But no way to create an account: no link, no `/register` route.

So you go and check. Registration is in `REQUIREMENTS.md`: F9.1 "Email + password registration" and user story US-30. In the backend, `POST /api/v1/auth/register` exists and is covered by `AuthControllerTest`. `src/data/copy.ts` even has the strings, from `registerHeading: 'Create a new account'` to `noAccount: "Don't have an account?"`. The only thing missing was the UI to use them.

### What the plan said

Open `TASKS.md` and look for the frontend pages task:

```markdown
### T070 — Pages: `GalleryPage`, `FavoritesPage`, `AlbumPage`, `LoginPage`, `NotFoundPage`
- **Status:** [x]
- **Acceptance:**
  - Each page reads filters from URL search params and feeds them into `usePhotos`.
  - LoginPage uses `useAuth.login`; redirects to intended route.
  - NotFoundPage renders empty state.
- **Commit:** `feat(frontend): page components wired to hooks`
```

The problem is in the acceptance criteria. Whoever wrote the requirement was thinking "authentication page", so login and registration. But the task only says `useAuth.login`, and Claude implemented exactly that. The April 29 report closes T070 with "LoginPage (form + 422 errors)".

An `[x]` in `TASKS.md` is a statement of intent. The guarantee comes with evidence: a commit, a test that exercises the flow, a browser screenshot. That goes for a human colleague as much as for an agent.

### The audit: what else is closed but not done

If one hole like this got through, there are others. Before fixing anything, run an audit, again in Plan Mode:

```text
Read docs/TASKS.md and for every task marked [x]:
1. Identify the code that should implement it
2. Verify that this code actually exists in the repository
3. Compare the task's acceptance criteria with the requirements
   in REQUIREMENTS.md that the task claims to cover
4. Flag every case where the task is closed but the implementation
   looks partial, missing, or narrower than the requirement

Don't fix anything: first I want the complete list of gaps.
```

In the Photogallery this audit has a task of its own, T107, and a versioned output: `docs/SPEC-COVERAGE.md`. It compares the 42 subsections of `DESIGN.md` with the code and the tests: 27 implemented, 11 partial, 4 missing. The missing items include files the design promised and nobody created, such as `MarkFavoriteAction.php` (the logic ended up in the controller) or the `BatchProgressTest.php` test. Not everything needs fixing right away, but each entry becomes a decision: build it, update the design, or declare it out of scope.

### The fix: one component, two modes

Registration blocks onboarding, so it goes first. The solution on the branch reuses `LoginPage` instead of creating a second component: a `mode` state switches between login and registration.

```tsx
type AuthMode = 'login' | 'register';

export function LoginPage() {
  const loginMutation = useLogin();
  const registerMutation = useRegister();
  const [mode, setMode] = useState<AuthMode>('login');
  // name, email, password, passwordConfirmation, errors...
  const isLogin = mode === 'login';

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // onSuccess navigates to '/', onError shows the 422 errors per field
    if (isLogin) {
      loginMutation.mutate({ email, password }, { onSuccess, onError });
    } else {
      registerMutation.mutate(
        { name, email, password, password_confirmation: passwordConfirmation },
        { onSuccess, onError },
      );
    }
  };

  const toggleMode = () => setMode(isLogin ? 'register' : 'login'); // and clears the errors
  // ... form JSX
}
```

In registration mode the form also shows the `name` and `password_confirmation` fields, the title and button take their strings from `copy.auth`, and the link at the bottom calls `toggleMode` without changing page. The full fix: `useRegister` in `src/hooks/useAuth.ts` next to `useLogin`, the `mode` state, the extra fields in the JSX, per-field 422 errors in both modes, a manual test of the flow (account creation, automatic login, redirect to the gallery), and a commit that names the scope gap.

The commit matters: a message like `fix(frontend): add register mode to LoginPage (scope gap in T070)` tells whoever reads the history why a closed task was reopened. The `/register` route came later, with T121 in Phase 14 (`feat(frontend): empty state CTA + /register route`), which points it at the same `LoginPage`.

There's a detail the same audit should have caught, and I use it for the exercise at the end of the chapter: `mode` always starts at `'login'`, so anyone who opens `/register` still sees the login form.

### The wave closing prompt

To avoid repeating the mistake, I end every wave with a fixed closing prompt:

```text
Before marking this wave as complete, check:

1. For every task marked [x]: does the repository contain code that
   matches the acceptance criteria? I want the file path,
   not "it should exist".
2. Rereading the requirements this wave claims to cover,
   is there anything the tasks don't cover?
3. Is there at least one test (automated, or a documented manual one) that
   exercises every user flow mentioned in those requirements?

If you find gaps, list them. Don't close the wave until the list is empty
or the exceptions are explicitly documented as out of scope.
```

No prompt guarantees zero gaps, but this one forces the cross-check between requirements and tasks, which is exactly where the normal flow breaks down.

### Drift between requirements and tasks

The registration case has a name: requirements-to-tasks drift, the gap that builds up between what the requirements say and what the tasks implement. It starts when you turn a requirement into tasks with implicit choices: "Auth" can mean just login, login and registration, or password reset as well. If the choice doesn't make it into the acceptance criteria, the result covers less than the requirement.

Drift runs the other way too, from the code back to the documents. AC-F8-5 says `GET /photos?is_favorite=1` returns the user's favorites, but `IndexPhotosRequest` and the frontend use the `favorites` parameter. The code works, the tests pass, and the acceptance criterion describes an API that doesn't exist.

The defense is explicit criteria: every page, route and endpoint in the requirement appears by name in the task. A verifiable criterion sounds like this: "working `/login` page, registration form reachable from `/register` and from the switch on the login page, call to `POST /api/v1/auth/register` with 422 error handling".

## 21.3 Favorite photos, from a boolean to a pivot table

### The requirement

Every user wants their own list of favorite photos, toggled with one click and found again in a dedicated view. In `REQUIREMENTS.md` it's section F8:

```markdown
### F8 — Favorites
- F8.1 Per-member favorites: any authenticated user can favorite any photo (many-to-many `users ↔ photos` via `favorites` pivot table)
- F8.3 Optimistic UI (heart fills before the request returns)
- F8.5 Favorite count visible per photo (how many users favorited it)
```

With criteria such as AC-F8-1: `PUT /photos/{id}/favorite` is idempotent, two consecutive calls return 204 and insert a single row into `favorites`. A small, well-bounded feature, the right kind to add mid-project.

### The modeling mistake

The first version of the design had the most obvious solution: a boolean `is_favorite` column on the `photos` table, with a composite index on `is_favorite` and `created_at`. It works as long as there's only one user. A column on the photo represents a global favorite: the photo is a favorite for everyone or for no one.

The relationship between users and favorite photos is many-to-many, and it needs a join table. If you ask Claude to "add favorite photos" with no other context, the boolean column is a plausible proposal, and this is where the person supervising earns their keep. Before accepting it, ask: "is the user-to-favorite-photo relationship one-to-many or many-to-many?" The answer decides the schema, the endpoints and the components.

### Phase 6.5

The correction is a phase inserted between 6 and 7, with wave 1.5 in the summary table of `TASKS.md`:

```text
T090  Migration: favorites pivot, drop is_favorite
T091  favoritedBy and favoritePhotos relationships
T092  PhotoController favorite/unfavorite, PhotoData with favorites_count
T093  Filament PhotoResource: favorites_count instead of the toggle
T094  Frontend hooks and components
T095  Tests (A favorites B's photo: it shows up only in A's list)
```

Look at the IDs. T090-T095 already existed: T090-T094 are the Phase 9 hooks, and T095 opens Phase 10. The inserted phase picked up the numbering after T080, and now `TASKS.md` has two different T090s. No test catches it, but "do T092" said to Claude becomes ambiguous, and so do the commit messages and the PR template, which asks you to cite the IDs. When you insert a phase mid-project, use IDs after the last existing one (here, from T125 on) or a dedicated prefix. That's why the reusable prompt asks for IDs that don't collide.

### The migration: create, copy over, drop

The `is_favorite` column already existed and held data, so the migration does three things in sequence: it creates the new structure, copies the existing data into it, and drops the old one. This is `2026_04_30_135152_create_favorites_table.php`:

```php
public function up(): void
{
    Schema::create('favorites', function (Blueprint $table) {
        $table->foreignUuid('user_id')->constrained('users')
            ->cascadeOnUpdate()->cascadeOnDelete();
        $table->foreignUuid('photo_id')->constrained('photos')
            ->cascadeOnUpdate()->cascadeOnDelete();
        $table->timestamp('created_at')->useCurrent();

        $table->primary(['user_id', 'photo_id']);
        $table->index('photo_id');
    });

    // Data migration: move existing is_favorite=true to pivot rows
    if (Schema::hasColumn('photos', 'is_favorite')) {
        DB::table('photos')
            ->where('is_favorite', true)
            ->orderBy('id')
            ->each(function (object $photo) {
                DB::table('favorites')->insertOrIgnore([
                    'user_id' => $photo->user_id,
                    'photo_id' => $photo->id,
                    'created_at' => now(),
                ]);
            });

        Schema::table('photos', function (Blueprint $table) {
            $table->dropIndex('photos_favorite_created_idx');
            $table->dropColumn('is_favorite');
        });
    }
}
```

The keys are UUIDs (`foreignUuid`) because the whole project uses UUID v7. The composite primary key prevents duplicates at the database level, even with two requests in parallel, and `cascadeOnDelete` makes the favorites go away with the photo or with the user. The `hasColumn` check makes the migration safe on a fresh database, where `is_favorite` never existed. Existing favorites go to the photo's owner, the only possible attribution for a global flag, and `down()` does the reverse. The same three-step pattern applies to any refactoring with data you need to keep.

### Relationships and idempotent endpoints

With the table in place, the model relationships are a couple of lines each:

```php
// Photo
public function favoritedBy(): BelongsToMany
{
    return $this->belongsToMany(User::class, 'favorites')
        ->withPivot('created_at');
}
```

`User::favoritePhotos()` is the mirror image, with `Photo::class`. It's `withPivot('created_at')` rather than `withTimestamps()`, because the pivot only has `created_at`.

For the API, the temptation is a single toggle endpoint using Eloquent's `toggle()`. The project uses two idempotent endpoints instead, as AC-F8-1 requires:

```php
// PUT /photos/{photo}/favorite: idempotent, always responds 204
public function favorite(Request $request, Photo $photo): Response
{
    if (! $request->user()?->tokenCan(TokenAbility::PhotosWrite->value)) {
        throw new AuthorizationException;
    }

    $request->user()->favoritePhotos()->syncWithoutDetaching([$photo->id]);

    return response()->noContent();
}
```

`unfavorite()` is identical, with `detach($photo->id)` on `DELETE`. A toggle repeated because of a network retry, or a double click, flips the state twice and leaves you where you started. `PUT` and `DELETE` state the final state you want, and repeating them changes nothing. The `tokenCan` check is the project's rule for every endpoint that modifies data: the Sanctum token must have the `photos:write` ability.

### The frontend: optimistic UI

The heart on the card has to change on click, before the server responds (F8.3). That's **optimistic UI**: you update the cache as if the request had already succeeded and roll back only if the server responds with an error. This is `useToggleFavorite` in `src/hooks/usePhotos.ts`, with a few lines left out:

```typescript
export function useToggleFavorite() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, isFavorite }: { id: string; isFavorite: boolean }) =>
      isFavorite ? removeFavorite(id) : addFavorite(id),
    onMutate: async ({ id, isFavorite }) => {
      await queryClient.cancelQueries({ queryKey: ['photo', id] });
      await queryClient.cancelQueries({ queryKey: ['photos'] });
      const previousPhoto = queryClient.getQueryData<SingleResponse<Photo>>(['photo', id]);
      // ... update of the ['photo', id] cache

      // Update all infinite list caches (photos list)
      queryClient.setQueriesData<{ pages: PaginatedResponse<Photo>[]; pageParams: unknown[] }>(
        { queryKey: ['photos'] },
        (old) => {
          if (!old) return old;
          return {
            ...old,
            pages: old.pages.map((page) => ({
              ...page,
              data: page.data.map((photo) =>
                photo.id === id
                  ? { ...photo, is_favorite: !isFavorite,
                      favorites_count: photo.favorites_count + (isFavorite ? -1 : 1) }
                  : photo,
              ),
            })),
          };
        },
      );
      return { previousPhoto };
    },
    onError: (_err, { id }, context) => {
      if (context?.previousPhoto) {
        queryClient.setQueryData(['photo', id], context.previousPhoto);
      }
      queryClient.invalidateQueries({ queryKey: ['photos'] });
    },
    // onSettled invalidates ['photos'] and ['photo', id]
  });
}
```

The first version got one detail wrong: the gallery is a `useInfiniteQuery`, so the optimistic update has to touch every page of the `['photos']` lists, not just the single photo's cache. Without that, the heart lit up in the lightbox but not in the grid; the Phase 5 review had flagged it as High. `mutationFn` picks `PUT` or `DELETE` based on the current state, so the toggle exists only in the UI, while the API stays idempotent.

In the card, `PhotoCard.tsx`:

```tsx
const handleFavoriteClick = (e: React.MouseEvent) => {
  e.stopPropagation();
  toggleFavorite.mutate({ id: photo.id, isFavorite: photo.is_favorite });
};

// ...

<button
  type="button"
  onClick={handleFavoriteClick}
  aria-label={photo.is_favorite ? copy.favorites.remove : copy.favorites.add}
  className="..."
>
  <Heart className={photo.is_favorite ? 'fill-red-500 text-red-500' : 'text-white'} />
  {photo.favorites_count > 0 && <span className="...">{photo.favorites_count}</span>}
</button>
```

The Tailwind classes are abbreviated; the file has a lot more of them.

`stopPropagation()` keeps a click on the heart from opening the lightbox. The badge shows `favorites_count` (F8.5), the total across all users, while `is_favorite` applies to whoever is looking. The dedicated view is the `/favorites` route, which mounts `FavoritesPage` and calls the API with `favorites=1`. The flow is covered by `e2e/favorites.spec.ts` in Playwright, with the API mocked.

### How long it takes, and with how many agents

In the first edition I timed a feature this size: a little over two hours from requirements to merge, tests and review included. The longest part is the requirements, about twenty minutes of discussion with Claude, and that time pays for itself: a wrong data model or an API that doesn't match the frontend costs more when you find it later.

For features like this, one developer with a single agent is enough, working in sequence in the same session. The tasks depend on each other (you don't write the frontend before the API exists), so there's nothing to parallelize. Worktrees and background sessions (chapter 20) are for when the tracks really are independent, like Phase 4 and Phase 6.

## 21.4 PRs that touch backend and frontend

### One PR or two

The three features in this chapter cross the same boundary: favorites have a migration, two endpoints, a Filament resource and a hook with optimistic UI. The ideal order is one PR for the backend (migration, API, integration tests) and, after the merge, one for the frontend. Each PR gets reviewed on its own, and the frontend consumes an API that's already stable. With Claude Code you more often end up with a single PR, because both sides are born in the same session and splitting them afterwards means rewriting history. If you want two PRs without that work, set up the split from the start: one worktree per side, as in chapter 20, with the frontend branch starting from the backend one.

A single PR holds up as long as the review treats it for what it is. The project let a very large one through: Phases 3-14 landed on `main` in a single squash merge, commit `a0a5437`, 171 files changed.

### Two review passes on the same PR

A single pass over a cross-stack PR mixes the perspectives and stays shallow on both. Two passes work better, each with a focus stated in the prompt. The first looks at the backend: queries, permissions on every endpoint, errors, job idempotency, transactions and dispatch, N+1. The second looks at the frontend: `aria-label` and keyboard, loading and error states, optimistic UI and rollback, bundle size, mobile rendering. Chapter 22 shows how to run them with `/code-review` and with a second model.

### Deploy order

Even with a single PR, the deploy always follows the same order: backend first, then frontend.

If the frontend goes out first, it calls endpoints that don't exist and users see errors. If the backend goes out first, the old frontend keeps working with the endpoints that were already there, and the new one finds the APIs it expects. So the sequence is: deploy the backend, check that the current frontend still works, deploy the frontend, check the new flows.

In GitHub Actions this becomes a single workflow, with a check between the two deploys. The real deploy of the Photogallery to AWS is chapter 23.

### Feature flags for big features

For a feature as big as the batch work there's one more option, the feature flag: you deploy the whole backend, but the new part of the frontend stays hidden behind a flag, and only the team or a slice of users sees it until you widen it. At the Photogallery's scale that's overkill. With lots of active users it's the difference between a controlled rollout and a fire to put out in the middle of the night.

### The pre-merge checklist

The repo already has a `.github/PULL_REQUEST_TEMPLATE.md` that asks for the `TASKS.md` task IDs, the `DESIGN.md` sections touched and the test plan (`php artisan test --compact`, `npm test -- --run`, Pint, Prettier, ESLint). For cross-stack PRs I add this list:

```text
Backend
[ ] No N+1 queries in the new routes (query log or QueryDetector)
[ ] Permissions on every endpoint (authenticated or public, token ability)
[ ] Migration tested on an empty DB and on a DB with data

Frontend
[ ] No console.error in development
[ ] Accessible components (aria-label, keyboard)
[ ] Bundle within the project budget (200 KB gzip)

Cross-stack
[ ] API contract identical between frontend and backend (fields and parameters)
[ ] 401, 403, 404, 422, 500 errors shown correctly
[ ] Deploy order written in the PR description
```

The API contract line is the one that would have caught the `favorites` versus `is_favorite` mismatch from section 21.2.

## Summary {.unlisted}

- A mid-project feature comes in through the documents: requirements, design and tasks approved before the code, using the reusable prompt from section 21.1 in Plan Mode.
- Batch processing on S3 needs an idempotent job (a deterministic path for each variant), retries with increasing waits, and dispatch after the transaction commits. Moving to S3 and SQS is configuration, as long as no file in `app/` uses local paths.
- A closed task proves nothing: ask for paths, tests and screenshots, and close every wave with the verification prompt. You prevent requirements-to-tasks drift with acceptance criteria that name pages, routes and endpoints.
- A many-to-many relationship needs a pivot table, and a schema refactoring with data follows create, copy over, drop. For endpoints, prefer idempotent `PUT` and `DELETE` over a toggle.
- A phase inserted mid-project gets new task IDs, never ones already in use.
- Cross-stack PRs get reviewed in two passes (backend, then frontend) and always deploy with the backend first.

## Exercise {.unlisted}

Start from the companion repo's `book/cap-14-phases-complete` branch and fix the gap T121 left behind: the `/register` route mounts `LoginPage`, but the form always starts in login mode.

1. In Plan Mode, run the reusable prompt from section 21.1 with this description: "opening `/register` should start the form in registration mode; opening `/login` in login mode; the switch keeps working".
2. Have Claude add a task to `TASKS.md` with a new ID (T125) and criteria that name both routes.
3. Run the task with Claude, with a Playwright test in `e2e/auth.spec.ts` that opens `/register` and checks for the "Create a new account" heading.
4. Finish with the verification prompt from section 21.2, then open the PR with the repo's template and the cross-stack checklist.

The exercise is done when the new test passes along with the rest of the suite (`npx playwright test` in the `frontend` folder) and T125 is marked `[x]` with the commit that implements it. Alternatively, apply the same four steps to a small feature from your own backlog, such as a search filter or a CSV export.
