# Chapter 22. Pre-deploy QA, /code-review and multi-LLM review

::: {.chapter-goals}
[What you'll learn]{.callout-title}

How to get the Photogallery ready for production with a QA checklist that actually blocks the deploy, how to hunt down the orphan tasks left behind by the waves, how to use Claude Code's built-in review (`/code-review`, `REVIEW.md`, ultrareview), and when you still need a second model such as Gemini, Codex or Kimi. We close with a dedicated security audit: middleware, CSP, HTTPS and secrets.

[Prerequisites]{.callout-title}

The Photogallery as it stands at the end of chapter 21 (branch `book/cap-14-phases-complete`), with passing tests. For ultrareview you need a claude.ai account; for the multi-LLM review, access to at least one second model.

:::

On your machine a bug is an annoyance: you spot it, fix it, push, and nobody notices. In production the same bug can mean one user's photos showing up for another, hijacked sessions, lost data and an apology email to your users. Fixing a problem during development costs an hour. After the deploy you add the incident, the rollback, the communication and the post-mortem, and the hour turns into a few days.

That's why the last 24-48 hours before a release go to QA, in the order I run it on the Photogallery: checklist, orphan tasks, code review and finally the security audit.

## 22.1 The pre-deploy QA checklist

A pre-deploy checklist only makes sense if it's binding: if an item fails, the deploy doesn't go out. A list you can skip when you're in a hurry is a wish list, and on release day you're always in a hurry.

I run it one or two days before the deploy, while there's still time to fix things calmly. The day itself is too late.

### Functional flows

Automated tests check what you thought to test. Manual testing finds the rest. Before the deploy I walk through these flows by hand:

- sign-up, with email verification if there is one
- login and logout
- password reset
- every main CRUD operation (photos, albums, tags, favorite photos)
- upload with valid files, files over 10 MB, files with the wrong extension
- pagination and filters
- the flows in the Filament admin panel

I try every flow three times: as an unauthenticated user, as an authenticated user and as an admin. Authorization bugs almost always surface when a role tries to do something it shouldn't be allowed to do.

Then the errors. Every error path has to produce a sensible UI: no blank screen, no JSON dump, no stack trace in front of the user. Every form validates on the client for UX and on the server for security, because browser validation takes a second to bypass. The 404 and 500 pages have to exist and say something useful. Two quick checks from the terminal:

```bash
# A page that doesn't exist must return 404 (not 200 with a blank page)
curl -s -o /dev/null -w "%{http_code}\n" https://tua-app.dev/pagina-che-non-esiste

# A protected endpoint without a token must return 401 (not 500)
curl -s -o /dev/null -w "%{http_code}\n" https://tua-app.dev/api/v1/auth/me
```

### Performance: numbers, not feelings

"Feels fast" isn't a metric. For the frontend I start with Lighthouse and aim for a score above 85 on the key pages (gallery, album, photo detail). Below 70 users start to leave and Google pushes you down in the rankings.

```bash
# Lighthouse from the command line (requires Chrome)
npx lighthouse https://tua-app.dev/pagina-chiave \
  --output=json \
  --output-path=./lighthouse-report.json \
  --chrome-flags="--headless"
```

For the API I look at the median of the main calls, which has to stay under 200 ms. You optimize the 99th percentile later: the median is what most users experience. This script sends a hundred requests to the photo list and prints the real median, not the mean:

```bash
# Latency of the main endpoint over 100 requests: prints the median
for i in $(seq 1 100); do
  curl -s -o /dev/null -w "%{time_total}\n" https://tua-app.dev/api/v1/photos
done | sort -n | awk '{t[NR]=$1} END {print "Mediana:", t[int((NR+1)/2)] "s"}'
```

The asset rules are few. Images served to users go out as WebP or AVIF, not full-resolution JPEG or PNG. CSS and JavaScript are compressed with gzip or brotli. A 4 MB photo in the gallery grid is a performance bug, even when the thumbnail pipeline exists: all it takes is one component pointing at the original instead of the thumbnail.

On the database side, every frequent query needs its index. If `WHERE user_id = ?` runs on every authenticated request, `user_id` has to be indexed, otherwise the query does a full table scan and gets slower and slower as the data grows. This actually happened on the Photogallery: the `photos` migration used `foreignUuid('user_id')->constrained()`, which on SQLite and PostgreSQL doesn't create the supporting index. The review of the phase 1 PR caught it, and the fix is in `docs/REVIEW-FIXES.md` (item F1).

```sql
-- Check the index (MySQL/MariaDB)
EXPLAIN SELECT * FROM photos WHERE user_id = 'uuid-di-un-utente' ORDER BY created_at DESC LIMIT 20;
-- If the "type" column says "ALL", the index is missing
```

### Basic security

These are the checks you can do in half an hour. The full audit comes in section 22.6.

- Admin routes and mutations: every endpoint that changes data or reads other users' data requires authentication and a permission check. Always, not usually. Hit every admin endpoint with a regular user's token and check that it returns 403.
- Input validation: everything that comes from outside (URL parameters, JSON body, files, headers) goes through a Form Request in Laravel, or a Zod schema on the TypeScript side.
- CSRF: if authentication uses cookies, CSRF is a real risk. The Photogallery uses Sanctum Bearer tokens on the API, but the Filament panel uses the web session: make sure the protection is on there, especially after a refactoring.
- Rate limiting on login and sign-up. Without it, an attacker tries thousands of password combinations in a few hours.

### Data integrity: the backup nobody tests

If the database gets corrupted tonight, can you restore it tomorrow morning? Not "in theory, yes, the backup is automatic": have you ever done a restore from that backup? Before the deploy, do a test restore into a throwaway database. If it doesn't work now, it won't work during an emergency either.

```bash
# Test restore from a backup on S3 (adapt it to your setup)
aws s3 cp s3://tuo-bucket/backup-latest.sql.gz ./restore-test.sql.gz
gunzip restore-test.sql.gz
mysql -u root -p test_restore < restore-test.sql

# Check that the tables exist and hold sensible data
mysql -u root -p test_restore -e "SELECT COUNT(*) FROM users;"
```

Also test the migrations against a copy of the production database, or a recent anonymized dump, not just your local database. On real data, migrations fail in ways you never see in development. And write the rollback plan: if the deploy goes wrong, what you do and how long it takes to get back to the previous version. Put it in writing, don't keep it in your head.

### Observability

Before the deploy I check that these are in place:

- structured JSON logs you can filter, aggregate and alert on (a `console.log("errore!")` in production helps nobody)
- error tracking with Sentry, Bugsnag or similar, so every unhandled exception reaches you before it reaches a user
- a health endpoint that checks the real dependencies
- three basic metrics in CloudWatch or Grafana: request count, error rate, latency; ten seconds is all you need to tell whether the deploy made something worse

The health endpoint is what the load balancer polls to decide whether a container is alive. In the Photogallery it's `GET /api/v1/health` (DESIGN §6.5): it writes, reads back and deletes a marker file on the photo disk, and queries the `failed_jobs` table to check the queue connection. It returns 200 if everything works, 503 with the details if something fails:

```json
{
  "status": "ok",
  "storage": "ok",
  "queue": "ok"
}
```

Claude can generate the full checklist for your stack. I use it as a starting point and then trim it.

::: {.callout .callout-prompt}
[Reusable prompt]{.callout-title}

```text
You are a senior QA engineer. My project is [describe stack and type of app].
Generate a pre-deploy checklist organized by category:
Functional, Performance, Security, Data Integrity, Observability.
For each item specify: what to check, how to check it (command or action),
success criterion. Format: Markdown table.
```
:::

## 22.2 Hunting orphan tasks

Every project built with Spec Driven Development and an agent has the same quiet problem: orphan tasks. Half-built features, endpoints that are registered but empty, components that were created and never imported. Code that exists and passes the tests, because the tests don't check for what you don't know is missing.

They come from two places. The first is a session that stops halfway through a task: a `/clear`, a compaction, a background session closed too early. When you start again, Claude doesn't remember where it got to, and if `docs/TASKS.md` has a task marked in progress it may treat it as done without really finishing it.

The second is subtler: a task gets checked off because the main part works, but some detail never lands (validation for an edge case, handling the 413, the mobile view). With an agent producing code at this speed, these gaps pile up without anyone seeing them.

### Auditing with grep

The first pass is mechanical: search the code for signs of unfinished work. Run these commands from the repository root.

```bash
# TODO, FIXME, HACK, XXX and stubs (excluding node_modules, vendor and build)
grep -rn \
  --include='*.ts' --include='*.tsx' --include='*.js' --include='*.jsx' \
  --include='*.php' --include='*.py' \
  -E "(TODO|FIXME|XXX|HACK|placeholder|implement me|not implemented)" \
  --exclude-dir={node_modules,vendor,.git,dist,build} \
  .
```

Read every hit. Some TODOs are legitimate future optimizations, others are functional gaps, and only the context tells you which is which. Then I look for endpoints that return nothing:

```bash
# Controllers that return null, empty arrays or a TODO
grep -rn "return null" backend/app/Http/Controllers/
grep -rn "return \[\]" backend/app/Http/Controllers/
grep -rn "// TODO: implement" backend/app/
```

For the frontend, a Node script that lists components nobody imports. Run it from the `frontend/` folder; it needs the `glob` package (`npm install -D glob`):

```bash
# Components created but never imported
node -e "
const fs = require('fs');
const glob = require('glob');
const path = require('path');

const components = glob.sync('src/components/**/*.{tsx,jsx}');
const allCode = glob.sync('src/**/*.{tsx,jsx,ts,js}')
  .filter(f => !f.includes('.test.'))
  .map(f => fs.readFileSync(f, 'utf8'))
  .join('\n');

components.forEach(comp => {
  const name = path.basename(comp, path.extname(comp));
  if (!allCode.includes('/' + name) && !allCode.includes(name + \"'\")) {
    console.log('Componente non importato:', comp);
  }
});
"
```

For the backend I look for columns added by migrations that hardly ever show up in the code. From `backend/`:

```bash
# Columns declared in the migrations
grep -hE -e "->(string|integer|boolean|text|json)\(" database/migrations/*.php \
  | grep -oP "\('\K[^']+" | sort -u > migration_columns.txt

# How many times each one appears in app/
while read col; do
  count=$(grep -rn "$col" app/ --include="*.php" | wc -l)
  if [ "$count" -lt 2 ]; then
    echo "Colonna probabilmente orfana: $col (trovata $count volte)"
  fi
done < migration_columns.txt
```

### A subagent that hunts orphans

grep finds text patterns. A subagent (chapter 10) reads the whole project and reasons about context: it notices that an endpoint is called `export` but doesn't export anything, which no grep will tell you. I give it this prompt:

```text
Act as a senior software engineer running a pre-deploy quality
audit. Analyze the entire project (backend + frontend) and look for:

1. Partially implemented features (endpoints that don't do what
   their name suggests, components with commented-out functionality,
   forms without handlers)

2. Orphan code (functions never called, components never imported,
   migrations with unused columns, routes registered but not implemented)

3. Stubs and placeholders (return null, throw new Error("not implemented"),
   TODOs with no date or owner)

For each finding, give:
- File and line number
- Description of the problem
- Likelihood that it needs finishing (high/medium/low)
- Alternative: should it be deleted?

Output: Markdown table sorted by likelihood of completion.
```

On the Photogallery this audit found four things:

- a duplicated Lightbox component, two nearly identical versions, one of them unused
- a `purge` method in the photo service that nobody called
- a `GET /api/v1/photos/export` route registered in the router, with a controller that held nothing but the comment `// TODO: CSV export`
- three Open Graph `<meta>` tags in the HTML template pointing at properties that were never set

### The three D rule

For every orphan I pick one of three fates.

Delete. If the feature isn't part of the MVP and there's no concrete plan to build it, dead code gets deleted. It's code nobody maintains and nobody tests. An empty endpoint that returns 200 is worse than an endpoint that doesn't exist, because it promises functionality that isn't there.

Complete. If the feature is in the MVP but half-built, you finish it now, not after the deploy. An upload without MIME type validation is an open vulnerability, even if everything else works.

Document and defer. If the feature isn't in the MVP but makes sense later, open an issue with all the details and take the skeleton out of the deploy branch.

When there are a lot of orphans, I have Claude propose the decision:

```text
I found these orphan items in the project:
[list of findings]

For each one, give me a recommendation: Delete / Complete / Document and Defer.
Justify the choice based on: impact on the MVP, risk of leaving it as is,
estimated cost of completing it now vs later.
```

## 22.3 Claude Code's built-in review

In chapter 19 we did code review with handwritten prompts and with the Superpowers reviewer. That still works, and it's still the right approach for a spec-driven review. In the meantime, though, Claude Code has picked up review tools of its own: a local command, an in-depth cloud review run by several agents, and automatic pull request review on GitHub. They're the first line of defense, the one you use on every push.

### `/code-review` locally

`/code-review` (alias `/review`) checks the commits on your branch that aren't on the remote yet, plus any uncommitted changes. It looks for correctness bugs, meaning things that break the program, not style. It runs as a background subagent with its own context: it doesn't fill up the conversation, and you can keep working in the meantime. The results arrive when it's done, with file, line and severity for every problem.

To make sure it finds something, on the Photogallery I plant two defects on a test branch: I remove the `$this->authorize('update', $photo)` call from `PhotoController::update` and the `mimes:jpg,jpeg,png,webp` rule from `StorePhotosRequest`. I commit and start the review:

```bash
git switch -c review/demo-bug
# ... introduce the two defects, then:
git commit -am "demo: due difetti per la review"
```

```text
/code-review high main...review/demo-bug
```

The command takes an effort level and a target. Effort goes from `low` to `max` (`low`, `medium`, `high`, `xhigh`, `max`): with `low` it reports only the problems it's most confident about, so few false positives; as you go up, coverage widens and less certain findings come in too. The target can be a file, a PR number, a branch or a range like `main...review/demo-bug`.

```text
/code-review low
/code-review high main...feat/albums-api
/code-review 42
/code-review --max-findings all
```

Watch out for one detail: if you don't give a level, `/code-review` reuses the last one you typed, even in an earlier session. The same goes for `--max-findings`, which stays set until you pass `--max-findings default`.

<!-- TODO screenshot: risultato di /code-review high sul branch review/demo-bug, con i due problemi (autorizzazione mancante e validazione dell'upload) e file, riga e gravità -->

### Applying and publishing the fixes

With `--fix` the review applies its fixes straight to the working tree. With `--comment` it posts the results as comments on the PR, on GitHub or GitLab:

```text
/code-review --fix main...review/demo-bug
/code-review --comment 42
```

::: {.callout .callout-warning}
[Warning]{.callout-title}

Fixes applied in the background by `--fix` aren't undone by `/rewind`. To go back, use Git: commit before you start the review, so `git diff` shows you exactly what it changed and `git restore .` puts you back where you started.
:::

After the fix I look at `git diff --stat` and rerun the tests: if the fix breaks something else, the Pest suite will tell you.

### `REVIEW.md` and Code Review on GitHub

`/code-review` reads `CLAUDE.md` like every Claude Code session. So the Photogallery's conventions apply to the review too: SOLID, transactions around multiple writes, explicit eager loading, a double authorization check on every mutation (token ability plus policy, rule 10 in `CLAUDE.md`).

For pull requests there's Code Review on GitHub, a managed service for Team and Enterprise plans, billed per review. Several agents analyze each PR, a verification pass throws out false positives, and the result arrives as inline comments sorted by severity plus a check run called "Claude Code Review". It never approves or blocks the PR: the decision stays with you. To ask for a fresh review, comment `@claude review` on the PR. It isn't available with Zero Data Retention, HIPAA or CMEK. An Owner of the Claude organization turns it on at claude.ai under Admin settings > Claude Code, in the Code review section: they install the Claude GitHub App and choose the repositories, the review level and when reviews run. You don't need any workflow files in the repository.

You customize Code Review on GitHub with a `REVIEW.md` file at the repository root, next to `CLAUDE.md`; you can add more in subfolders for local rules. In it you write what counts as serious in your project, the maximum number of minor details you want, what to ignore and what to always check. This is the Photogallery's:

```markdown
# Review instructions

## What counts as Important

Reserve Important for problems that break behavior or expose data:
queries not filtered by the photo's owner, uploads without type and
size validation, endpoints without an authorization policy,
non-backward-compatible migrations. Style and naming are Nit at most.

## Limit the Nits

Report at most five Nits per review. If you find more, write
"plus N similar items" in the summary.

## Don't report

- Anything CI already checks: lint, formatting, types
- Generated files and lockfiles

## Always check

- Every new route under /api/v1 has a Pest integration test
- API contracts match docs/DESIGN.md
- Every mutation checks both tokenCan() and the policy
- exif and processing_error are visible only to the owner and to admins
- No log contains emails or tokens
```

The "Always check" section picks up the spec's criteria: API contracts have to match `docs/DESIGN.md`, as we required in chapter 18. The last two items come from real problems found in the wave reviews and recorded in `docs/REVIEW-FIXES.md`: the `AlbumController@store` that checked only the token ability (S3), and the `exif` and `processing_error` fields returned to anonymous users too, GPS coordinates included (S1).

Findings come in three levels. Important must be fixed before the merge. Nit is a minor detail. Pre-existing is a bug that was already there and that the PR didn't introduce: good to know, but no reason to block the merge.

Remember that the local `/code-review` command doesn't read `REVIEW.md`: it reads only `CLAUDE.md`. If you need a rule in both places, put it in `CLAUDE.md`.

### Ultrareview in the cloud

For important PRs there's ultrareview, in research preview. Instead of a single reviewer, a team of specialized agents analyzes the code in the cloud, each one hunting for a different kind of problem, and a verification pass throws out false positives. The results come back to your session when they're ready.

```text
/code-review ultra
/code-review ultra focus on authorization and uploads
/code-review ultra --fix
```

With no arguments it compares the current branch with the main branch, uncommitted changes included. You can pass a branch, or a note in plain language to steer the review, as in the second example. With `--fix` it applies the fixes; for a PR on github.com, the launch window lets you choose to post the results on the PR. `/ultrareview` is an alias.

You need to be logged in with a claude.ai account. On Bedrock, Google Cloud's Agent Platform (formerly Vertex AI) or Foundry, `/code-review ultra` falls back to a local review; with Zero Data Retention or HIPAA it isn't available. Pro and Max plans get three free runs, after that you pay with usage credits: that's why I don't run it on every push.

For scripts and CI there's the `claude ultrareview [target]` command, which waits for the results and prints them. `--json` produces output another program can read, `--timeout` sets the maximum wait in minutes (the default is 45) and `--post` posts the results as a comment on the PR.

```bash
claude ultrareview --json --timeout 30 > ultrareview.json
```

## 22.4 A second model for the critical parts

Claude Code wrote the Photogallery's code with its own patterns and its own idea of the right architecture. When the same model reviews that code, it tends to recognize exactly those patterns as correct. It's the problem of proofreading your own work: you see what you meant to write. The Photogallery's review log has a sentence that says it plainly: the session that wrote the code hadn't spotted any of the problems an independent reviewer found later.

The built-in review softens the problem, because it runs with a clean context and, with ultrareview, with several agents and a verification pass. But it's still one model, and teams have solved this the same way for decades: the reviewer has to be someone other than the author. With LLMs, that means a different model. Gemini, Codex and Kimi are trained on different data, with different techniques, and have different blind spots from Claude's: what one model considers normal, another flags.

Does it still make sense now that `/code-review` exists? Yes, but not everywhere. A second model costs time, because you orchestrate the review by hand. I use it on the critical parts (authentication, uploads, authorization, the photo pipeline) before the deploy, not on every push.

### What they found on the Photogallery

What follows is what I saw on this project, with the model versions available in spring 2026. It isn't a general ranking: models change every few months, and on different code the results may differ.

Claude, used as a reviewer with the prompts from chapter 19, was the most useful on architecture: SOLID violations, circular dependencies, patterns that don't fit the domain. It explains a lot and proposes detailed fixes, but it goes easier on code it wrote itself.

Gemini was the strongest on performance and memory use. It found three problems Claude hadn't flagged:

- a `file_get_contents` (and the same pattern with `Storage::get`) that loaded the whole file into RAM instead of using a stream, with a risk of running out of memory on large photos
- `UploadPhotosAction` writing files to disk inside a transaction: if the transaction rolled back, the files stayed written
- the GPS coordinates in the EXIF metadata served to users, unauthorized third parties included

Codex was precise on types, API contracts and error handling: functions that promise more than they return, overly broad `catch` blocks that swallow real errors, inconsistent responses between endpoints of the same controller. Shorter reports than Claude's, but on target.

Kimi was the pickiest on security edge cases, and found things neither Claude nor Gemini had seen:

- the `is_admin` column among the fillable fields of the `User` model: anyone could send `is_admin: true` in the request and become an admin
- signed URLs generated before the policy check: the URL existed and worked even if the user then failed authorization
- authentication handled by hand instead of with Laravel's `Auth::attempt`
- missing email verification, along with a way to get around the rate limiter
- the Sanctum token stored in `localStorage` instead of an HttpOnly cookie

None of these was a false positive: they were all in the code. The last one is a special case, because it was a trade-off already documented in DESIGN §10.5: v1 kept the Bearer token in `localStorage` and mitigated the risk with a 24-hour TTL, a strict CSP, a ban on raw HTML in the frontend, and token abilities. The review brought it back up, and the fix (commit `9ebef16`) moved the token to `sessionStorage`, which goes away when you close the tab. An injected script can still read it there, so all the mitigations stay. `DESIGN.md` §10.5, on the final branch, still talks about `localStorage`: even a document you keep in sync needs rereading. Today the only fillable fields on `User` are `name`, `email` and `password`.

The consolidated report counted 3 CRITICAL, 7 HIGH, 14 MEDIUM and 7 LOW problems. The most serious, according to the report, was a data leak between users in `BatchController`: photos were associated with an upload batch by timestamp, loaded for all users and filtered by owner in PHP instead of in the query. The fix (commit `5e6c41c`) adds a `batch_id` column to the `photos` table and filters by batch and by user directly in SQL.

![The consolidated pre-deploy review report: the three CRITICAL problems, including the photo leak between users in BatchController](figures/cap-22/fig-01.png)

![Some of the 14 MEDIUM problems: pipeline reliability, admin panel performance, image quality and keyboard accessibility](figures/cap-22/fig-02.png)

![From the report: the drift between the Actions pattern planned in DESIGN.md and the logic that ended up in the controllers, the synchronous GPS stripping during upload, and the trade-off on the token in localStorage](figures/cap-22/fig-03.png)

### The multi-LLM review workflow

The first step is to prepare the changeset:

```bash
# The whole branch diff against main
git diff main...HEAD > changeset.diff

# Or, if the diff is too big, just the critical parts
git diff main...HEAD -- backend/app/Http/Controllers/ backend/app/Actions/ frontend/src/api/ > changeset-critical.diff
```

Then the same prompt to every model. The prompt has to be identical, otherwise you're comparing answers to different questions. I use the one in the box at the end of this section and paste the diff at the bottom.

Once I have the reports, I aggregate them by consensus:

| Found by | Priority |
| :---- | :---- |
| All models | Critical, must be fixed before the deploy |
| Three models | High, fix strongly recommended |
| Two models | Medium, weigh the context |
| One model only | Low, read it and decide |

Consensus tells you where to start. A problem found by only one model isn't necessarily a false positive: only Kimi had caught the fillable `is_admin`.

Finally I hand the findings to Claude for the fixes, in a new session or after a `/clear`:

```text
You have in front of you the results of a cross-LLM review of the project.
These problems were found by Gemini and Kimi and confirmed by Codex:

[paste the critical and high findings]

Organize them into a todo list and fix them one at a time, starting
with the Critical ones. For each fix, explain what you changed and why.
```

The new session matters. The context of the development session pushes Claude to bring back the very patterns that were just flagged as problematic; from a clean context it treats them for what they are, problems to fix. After the fixes I rerun `/code-review high` on the branch, to check that the fixes didn't introduce anything else.

What does it cost? On the Photogallery the four-model review came to around 10-15 dollars in total; it depends on the size of the diff and on your plans. A bug like the photo leak between users, discovered in production, costs days between the incident, telling users and, if personal data is involved, legal obligations.

::: {.callout .callout-prompt}
[Reusable prompt]{.callout-title}

Paste it unchanged into Claude, Gemini, Codex and Kimi.

```text
Act as a senior software engineer with 10+ years of experience.
Do a critical review of the following code.

Evaluate it along these axes:
1. Best practices and language/framework standards
2. SOLID principles and design patterns (SRP, OCP, LSP, ISP, DIP)
3. Security (injection, authentication, authorization, data exposure)
4. Scalability and performance (N+1 queries, memory use, caching)
5. Reliability and error handling (exception handling, rollback)
6. Unhandled edge cases (boundary input, concurrency, intermediate states)

For each problem:
- Severity: Critical / High / Medium / Low
- File and line (if applicable)
- Concise description of the problem
- Recommended fix with a code snippet

Output: Markdown list sorted by descending severity.
No padding: if you find no problems in an area, say so explicitly.

[paste the git diff or the files to review here]
```
:::

### Which review to use, and when

| Approach | Strengths | Limits | When to use it |
| --- | --- | --- | --- |
| Handwritten review prompts (chapter 19) | Full control over what gets checked | Takes time and well-written prompts | Spec-driven reviews |
| `/code-review` | Fast, runs in the background, `--fix` and `--comment` | One model, reads only `CLAUDE.md` | Before every push |
| `/code-review ultra` | Several agents, false-positive verification | Needs a claude.ai account, costs more | Large or critical PRs |
| Code Review on GitHub (Team and Enterprise) | Automatic on every PR, reads `REVIEW.md` | Billed per review, GitHub only | Team workflows |
| Second model (Gemini, Codex, Kimi) | Independent perspective | Orchestrated by hand | Security and performance on critical code |

The workflow I recommend, and the one I use on the Photogallery:

1. `/code-review high` before every push.
2. Ultrareview on PRs that are large or touch authentication, uploads and data.
3. A review with a second model on the critical parts, before the deploy.

## 22.5 Security plugins

There are also dedicated security tools. In the official `claude-plugins-official` marketplace you'll find two plugins from Anthropic: security-guidance, which checks Claude's edits while it works, and Claude Security, which runs a multi-agent vulnerability scan and turns the problems you pick into patches. You'll find them under `/plugin`, Discover tab, by searching for "security", or you can install them by name with `/plugin install security-guidance@claude-plugins-official` and `/plugin install claude-security@claude-plugins-official`; chapter 14 covers installation and scopes.

Then there's the `/security-review` command, which runs a security review of the pending changes on the current branch. On the Photogallery I run it before the final audit in the next section: it's a good filter for the obvious problems, so the audit can focus on configuration.

None of the three replaces the audit, which also checks what isn't in the diff: missing headers, default configurations, secrets in the Git history.

## 22.6 Security audit: middleware, CSP, HTTPS, secrets

The security audit is the last step before the deploy, and it deserves its own session and its own prompt. Security problems don't always show up as bugs during functional testing: an endpoint that doesn't check authorization returns 200 and looks like it works perfectly, until someone sends it another user's token.

The starting point is that framework defaults are designed for development. Laravel's default CORS configuration has `allowed_origins` set to `*`, and the Photogallery fell for it: the Laravel 13 scaffold doesn't publish `config/cors.php`, so `FRONTEND_URL`, documented in `.env.example` for the allowlist, wasn't read by anything and the wildcard was active (REVIEW-FIXES, item S2). No framework turns on a CSP by default, or forces HTTPS or HSTS. Every measure in this section is explicit: if you don't configure it, nobody will.

### Middleware and headers

Middleware is the layer every request passes through before the controller, so it's the right place for security checks: it applies to every route and you can't forget one. In Laravel you add the security headers with a middleware of your own:

```php
<?php

declare(strict_types=1);

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

final class SecurityHeaders
{
    public function handle(Request $request, Closure $next): Response
    {
        $response = $next($request);

        $response->headers->set('X-Frame-Options', 'DENY');
        $response->headers->set('X-Content-Type-Options', 'nosniff');
        $response->headers->set('Referrer-Policy', 'strict-origin-when-cross-origin');
        $response->headers->set('Permissions-Policy', 'geolocation=(), microphone=()');

        if (app()->environment('production')) {
            $response->headers->set(
                'Strict-Transport-Security',
                'max-age=31536000; includeSubDomains'
            );
        }

        return $response;
    }
}
```

and you register it for every request in `bootstrap/app.php`, inside `withMiddleware`:

```php
$middleware->append(\App\Http\Middleware\SecurityHeaders::class);
```

With Node and Express you get the same headers from Helmet in one line, `app.use(helmet())`.

CORS: in production, never `Access-Control-Allow-Origin: *`. The Photogallery now allows only the SPA's origin, read from the environment, and only on the API. The Filament panel on `/admin` stays out of it and keeps its own CSRF rules:

```php
return [
    'paths' => ['api/*'],
    'allowed_methods' => ['*'],
    'allowed_origins' => [
        env('FRONTEND_URL', 'http://localhost:5173'),
    ],
    'allowed_origins_patterns' => [],
    'allowed_headers' => ['*'],
    'exposed_headers' => ['ETag', 'Retry-After'],
    'max_age' => 0,
    // Bearer token in the Authorization header: no CORS with credentials
    'supports_credentials' => false,
];
```

Body limits: without one, an attacker sends a 1 GB body and eats up your server's memory. In PHP the ceiling comes from `post_max_size` and `upload_max_filesize`; on top of that, the Photogallery validates every file with `image|mimes:jpg,jpeg,png,webp|max:10240` (10 MB) and turns `PostTooLargeException` into a 413 response with the standard JSON envelope.

Trusted proxies: behind a load balancer, a CDN or a reverse proxy, you have to tell the framework to trust the proxy's IPs. Without that, `$request->ip()` returns the proxy's IP for everyone, the per-IP rate limiter becomes one shared bucket, and the protection against credential stuffing stops doing anything. On the Photogallery the phase 2 review found this problem (item S4), and the fix in `bootstrap/app.php` reads the configuration from the environment:

```php
$trustedProxies = env('TRUSTED_PROXIES', '');
if ($trustedProxies !== '') {
    $middleware->trustProxies(
        at: $trustedProxies === '*' ? '*' : explode(',', $trustedProxies),
    );
}
```

Locally `TRUSTED_PROXIES` stays empty; behind the ALB from chapter 23 you set it. In Express the equivalent is `app.set('trust proxy', 1)`.

### Content Security Policy

CSP is the most effective defense against Cross-Site Scripting. If an attacker manages to inject JavaScript into your pages, a well-configured CSP makes the browser refuse to run the unauthorized code. A baseline policy that works for most applications:

```text
Content-Security-Policy:
  default-src 'self';
  script-src 'self';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  font-src 'self' https://fonts.gstatic.com;
  connect-src 'self' https://api.tua-app.com;
  frame-ancestors 'none';
  base-uri 'self';
  form-action 'self';
```

`frame-ancestors 'none'` is the modern replacement for `X-Frame-Options: DENY`: it stops the site from being embedded in an iframe on another domain (clickjacking). `'unsafe-inline'` on styles is often needed for CSS-in-JS and inline component styles; avoid it on scripts, and if you have inline scripts you can't do without, use nonces.

The Photogallery has its policy in DESIGN §10.5, and it's one of the mitigations that justify keeping the token in the browser instead of in an HttpOnly cookie:

```text
default-src 'self'; img-src 'self' https://cdn.example.com data:; script-src 'self'; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'self'
```

Don't turn on CSP in blocking mode on the first deploy. Start with `Content-Security-Policy-Report-Only` and a `report-uri`, watch the violations for a few days, and switch to blocking mode only when you're sure it doesn't block anything legitimate:

```text
Content-Security-Policy-Report-Only:
  default-src 'self';
  report-uri https://tua-app.com/api/csp-report;
```

The CSP that matters for the SPA is the one on the SPA's HTML, not the one on the API's JSON responses. The React SPA comes out of the Vite build as static files: the policy goes where they're served (on the CloudFront distribution, in chapter 23) or, as a safety net, in a `<meta>` tag in `index.html`, which applies even when the assets come from the CDN without going through the application server:

```html
<meta
  http-equiv="Content-Security-Policy"
  content="default-src 'self'; frame-ancestors 'none';"
/>
```

One caveat: browsers ignore `frame-ancestors` when it comes from a `<meta>` tag, so the clickjacking protection also has to travel in an HTTP header.

### HTTPS and HSTS

In production HTTPS is mandatory: without it, anyone on the same network can read tokens, session cookies and personal data. Every HTTP request has to be redirected to HTTPS, both at the infrastructure level (load balancer, CloudFront) and in the code. In Laravel you force the scheme of generated URLs in `AppServiceProvider`:

```php
public function boot(): void
{
    if ($this->app->environment('production')) {
        \Illuminate\Support\Facades\URL::forceScheme('https');
    }
}
```

HSTS tells the browser, after the first visit over HTTPS, never to try HTTP again for a set period. With `max-age=31536000` (one year), even if the user types `http://` into the address bar the browser switches to HTTPS on its own, without sending the plaintext request that could be intercepted. The `SecurityHeaders` middleware from earlier sets it in production:

```text
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

Certificates: with Let's Encrypt, check that automatic renewal works (`certbot renew --dry-run`); with AWS Certificate Manager renewal is automatic. Either way, set an alert thirty days before expiry, because an expired certificate locks out every user.

### Managing secrets

A secret that lands in the repository stays in the Git history even if you remove it in the next commit. Before the deploy I run a gitleaks scan, history included:

```bash
# Installation
brew install gitleaks   # macOS
# or: go install github.com/gitleaks/gitleaks/v8@latest

# Full scan, including the Git history
gitleaks detect --source . --verbose
```

If gitleaks finds something, treat that secret as compromised: removing it isn't enough, you have to rotate it.

No sensitive value goes into the code or into committed configuration files: API keys, connection strings and SMTP credentials live in environment variables. Locally and in CI, environment variables are fine; in production use a secret manager (AWS Secrets Manager, GCP Secret Manager, HashiCorp Vault), which gives you a record of who read what and when, automatic rotation, and revocation without touching the code. Rotate keys every ninety days: a key that's never rotated stays valid forever in the hands of whoever found it.

The security audit run on one of the Photogallery's waves (`docs/BATCH-2025-04-28.md`) found two problems of this kind: a hardcoded `'password'` fallback in the admin user seeder, which would have ended up in production if the environment variable was missing, and a `.env` with `APP_DEBUG=true`. You fix the first by making the seeder fail when the variable is missing, and the second with `APP_DEBUG=false` outside the local environment and `.env` in `.gitignore`.

### Authentication

For passwords use argon2id or bcrypt, never SHA-256, SHA-512 or MD5: they have no configurable work factor, and with a database dump and modern hardware they're cracked quickly. Laravel uses bcrypt by default, and the Photogallery sets `BCRYPT_ROUNDS=12` in `.env.example`. To switch to argon2id, `HASH_DRIVER=argon2id` in `.env` is all it takes, as long as your PHP is compiled with argon2 support.

The Photogallery's Sanctum tokens expire after 24 hours (`SANCTUM_TOKEN_EXPIRATION=1440`, read by `config/sanctum.php`: this one had also stayed unwired until the phase 1 review, item F3) and logout deletes the current token with `currentAccessToken()->delete()`. The token abilities (`photos:write`, `albums:write`, `admin`) limit the damage if a token gets stolen. On the choice to keep the token in the browser (now in `sessionStorage`), what I said in section 22.4 applies: it's a documented trade-off; if you want to change it, the way to go is Sanctum's stateful mode with HttpOnly cookies, at the price of a more complex CSRF flow.

### Rate limiting

Rate limiting without numbers protects nothing. The Photogallery has the limits from DESIGN §6.0 in `AppServiceProvider`: 10 requests per minute per IP on the authentication routes, and on the rest of the API two ceilings together, 120 per minute per IP and 300 per minute per authenticated user.

```php
private function configureRateLimiters(): void
{
    $authPerIp = (int) config('photogallery.rate_limits.auth_per_ip_per_minute', 10);
    $apiPerIp = (int) config('photogallery.rate_limits.api_per_ip_per_minute', 120);
    $apiPerUser = (int) config('photogallery.rate_limits.api_per_user_per_minute', 300);

    RateLimiter::for('auth', fn (Request $request) => Limit::perMinute($authPerIp)->by($request->ip()));

    RateLimiter::for('api', function (Request $request) use ($apiPerIp, $apiPerUser) {
        $limits = [Limit::perMinute($apiPerIp)->by($request->ip())];
        if ($request->user()) {
            $limits[] = Limit::perMinute($apiPerUser)->by('user:'.$request->user()->id);
        }

        return $limits;
    });
}
```

The routes use `throttle:auth` and `throttle:api` in `routes/api.php`. The per-user limit is there because behind a NAT or a corporate proxy many users share the same IP, and a per-IP limit alone would block them all at once. The per-IP limit on authentication, on the other hand, only works if the trusted proxies are configured, as we saw above. `/api/v1/health` stays out of the throttling, so the load balancer's probes don't trip the limiter. The same wave audit pointed out that the Filament login had no limit: the admin panel is a way in like any other.

### The final audit prompt

This is the last prompt I run before I call the project ready to deploy, in a dedicated session:

```text
You are a security engineer. Examine the entire project (code,
configuration, dependencies) and run a pre-production audit.

Explicitly verify:
1. Security middleware (security headers, CORS, body limits)
2. Content Security Policy (present, correctly configured)
3. HTTPS enforced and HSTS
4. Secrets management (no secrets in the code, use of env vars)
5. Password hashing (correct algorithm, adequate work factor)
6. Tokens and sessions (expiration, revocability, secure storage)
7. Rate limiting (login, sign-up, general API, admin panel)
8. Trusted proxies configured
9. Complete input validation (every external endpoint)
10. Authorization on every route (no endpoint without an auth check)

For each item:
- Status: OK / PROBLEM / NOT VERIFIABLE
- If PROBLEM: description of the risk and recommended fix
- Priority: Blocking / High / Medium

Keep code problems separate from environment configuration problems
(the latter are solved at deploy time, not in the code).
```

The last instruction splits the work into two different lists. Code problems you close in the repository, now. Configuration problems (`TRUSTED_PROXIES`, `APP_DEBUG`, the CSP on the CloudFront distribution, the secret manager) become provisioning items, and you'll find them again in the CloudFormation template in chapter 23.

## Summary {.unlisted}

- The pre-deploy checklist covers functional flows, performance, basic security, data integrity and observability, and you run it one or two days before the release: if an item fails, the deploy doesn't go out.
- You flush out orphan tasks with grep and a dedicated subagent; for each one you choose between Delete, Complete and Document and defer.
- `/code-review` at high effort before every push, with `--fix` and `--comment` to act on the results; you undo `--fix` changes with Git, not with `/rewind`.
- `REVIEW.md` customizes Code Review on GitHub (Team and Enterprise) but not the local command, which reads only `CLAUDE.md`; ultrareview is for large or critical PRs.
- A second model is still useful on the critical parts before the deploy: on the Photogallery it found the fillable `is_admin` and the signed URLs generated before the policy check.
- The final audit keeps code problems separate from configuration problems, which move on to provisioning.

## Exercise {.unlisted}

Run the full pre-deploy QA on your Photogallery, starting from the `book/cap-14-phases-complete` branch.

1. Create a dedicated branch: `git switch -c cap-22-pre-deploy-qa`.
2. Run the orphan-task grep and the subagent with the prompt from section 22.2, and apply the three D rule to every finding.
3. Add the `REVIEW.md` from section 22.3 and run `/code-review high main...cap-22-pre-deploy-qa`.
4. Send the multi-LLM review prompt to at least one second model (Gemini, Codex or Kimi) on the diff of the controllers and the Actions, and aggregate the findings by consensus.
5. Run `/security-review` and then the final audit prompt from section 22.6.
6. In a new session, fix all the critical and high findings, then rerun `/code-review high` and the test suite.

The exercise is done when `./vendor/bin/sail test` and `pnpm test` pass, the last `/code-review high` reports no Important problems, and the configuration problems are written down in a separate list for chapter 23. It takes 3-4 hours; don't rush the aggregation of the findings, that's where you decide what really gets fixed.

The reference branch is `book/cap-15-post-review-fixes` in the `claude-code-book-photogallery` repository: it holds all the review fixes (3 CRITICAL, 7 HIGH, 14 MEDIUM and 7 LOW, plus the fix for the EXIF data leak with signed routes) and a `docs/DESIGN.md` aligned with the actual implementation.
