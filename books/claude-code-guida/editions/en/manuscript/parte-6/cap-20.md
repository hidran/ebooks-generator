# Chapter 20. Parallel waves with worktrees, /goal and agent view

::: {.chapter-goals}
[What you'll learn]{.callout-title}

How to run the independent tracks of a Photogallery wave in parallel, each in its own git worktree and with a completion condition Claude has to prove it met. Then how to follow several background sessions from a single screen, how to give subagents a worktree too, and how to bring the work back together without leaving stray copies and branches behind.

[Prerequisites]{.callout-title}

The Photogallery repo as it stands at the end of chapter 19 (branch `book/cap-13-wave-2-api` of the companion repo) and the GitHub CLI (`gh`) set up as in chapter 19.

:::

At the end of chapter 19 the Photogallery has Phase 1 (models, migrations, seeders) and Phase 2 (API) merged into `main`. `docs/TASKS.md` still has open Phase 3 (Filament admin, T046 to T054), Phase 4 (React frontend setup, T055 to T062), Phase 5 (React components, T063 to T071) and Phase 6 (image pipeline, T072 to T080), plus three Phase 2 tasks deferred to Phase 6: T029, T032 and T035. That's 38 tasks.

The project's `CLAUDE.md` already says how to run them. Its "Parallelization rules" section groups these phases into Wave 1, split into three tracks: Track A (Phase 2, then Phase 6), Track B (Phase 3), Track C (Phase 4, then Phase 5). And it adds "each in its own git worktree". In chapter 19 we asked Claude to use subagents where the tasks were independent, and for two pieces of scaffolding that was fine. With dozens of tasks across backend and frontend, all in the same folder, sooner or later two agents touch the same file. Here we give each track its own worktree, as the file asks.

A note on names. The companion repo's branches call the first two phases run in chapter 19 "wave 1" and "wave 2". In `docs/TASKS.md` Phase 1 belongs to Wave 0 and the API is Track A of Wave 1. From here on I use the names in the file, because those are the ones Claude will read.

## 20.1 Three ways to work in parallel

Claude Code gives you three tools for doing several things at once, and each one isolates something different.

| Tool | What it isolates | When to use it |
| --- | --- | --- |
| Subagent | The context, inside one session | Research and short subtasks, as in chapters 10 and 19 |
| Worktree (`claude --worktree`) | The files: each session gets its own copy and its own branch | Tasks that change different files at the same time |
| Background session (`claude --bg`, `claude agents`) | The terminal: the session runs without you | Several long tasks to follow from one screen |

A subagent has a context window all to itself, but it reads and writes in the same folder as the session that launched it. If two subagents edit `routes/api.php` at the same moment, one overwrites the other, or one's tests fail because of the other's half-finished changes. A worktree solves the file problem. A background session solves a different one: having to keep five terminals open for five jobs. The three combine: a background session works in a worktree, and a subagent can have its own temporary worktree.

## 20.2 Picking the tracks and preparing the repo

### Hidden dependencies

`CLAUDE.md` says the three tracks "share zero files". Before you launch them together, though, read the tasks and not just the phase titles. T048 asks for a Filament reprocess action that calls `ProcessPhoto::dispatch($record)`, and the `ProcessPhoto` job is created by T077, in Phase 6. T048's `Depends on` field only lists T047, so the problem shows up only in the acceptance criteria. If you launch Track B alongside Phase 6, the admin session finds a class that doesn't exist and either stops or makes one up.

That's why the first round pairs two tracks that really don't touch each other:

- Track A, continued: Phase 6 (T072-T080) plus T029, T032 and T035, all in the backend;
- Track C: Phase 4 (T055-T062), frontend only.

The second round, once the pipeline is in `main`, launches Phase 3 and Phase 5.

There's one file every session touches: `docs/TASKS.md`, because rule 2 in `CLAUDE.md` wants the box checked in the same commit as the task. The sessions edit lines in different sections, though, so Git usually merges them without conflicts. The other "magnet" files listed in `CLAUDE.md` (`composer.json`, `package.json`, `bootstrap/app.php`, `App.tsx`, `main.tsx`) stay with one session at a time. On the chapter 19 branch `composer.json` already contains `filament/filament` and `intervention/image-laravel`, so on paper no first-round track needs to touch it.

### .gitignore, .worktreeinclude and baseRef

Three pieces of setup, to commit on `main` before you open the sessions.

First: Claude Code creates worktrees in `.claude/worktrees/` inside the repo, and that folder must stay out of Git. The Photogallery has no `.gitignore` at the root (there are only the ones in `backend/` and `frontend/`), so you create one:

```text
.claude/worktrees/
```

The second is about ignored files. A worktree is a clean checkout: anything Git ignores isn't there. The backend tests need `backend/.env`, which holds `APP_KEY` (`phpunit.xml` sets up in-memory SQLite but not the key). The `.worktreeinclude` file at the root lists the ignored files Claude Code copies into every new worktree:

```text
backend/.env
```

The frontend has no `.env`: `src/api/client.ts` falls back to `/api/v1` when `VITE_API_BASE_URL` isn't set. If you have one, add `frontend/.env.local` to the list. Leave `vendor/` and `node_modules/` out: reinstalling them is faster than copying them.

The third is the starting point. By default a worktree starts from the remote `main`. If you merged something locally and haven't pushed it yet, new sessions won't see it. To start from your local `HEAD`, add the `worktree` key to `.claude/settings.json`, next to the hooks the file already contains:

```json
{
  "worktree": {
    "baseRef": "head"
  }
}
```

In the first round this changes nothing, because `main` matches the remote. You'll need it in the second round if you decide to merge locally (section 20.5).

```bash
git add .gitignore .worktreeinclude .claude/settings.json
git commit -m "chore: worktree setup for parallel tracks"
git push
```

## 20.3 Two sessions, two worktrees

A worktree is a second working directory of the same repository, with its own files and its own branch but the same Git history. With `--worktree` and a name, Claude Code creates the worktree in `.claude/worktrees/<name>` on a new branch `worktree-<name>` and starts the session inside it.

Open two terminals at the repo root. In the first:

```bash
claude --worktree fase6-pipeline
```

In the second:

```bash
claude --worktree fase4-frontend
```

From either one, check what happened, using the `!` prefix that runs a shell command from the session:

```text
!git worktree list
```

```text
~/projects/photogallery                                  5d1f2a9 [main]
~/projects/photogallery/.claude/worktrees/fase6-pipeline 5d1f2a9 [worktree-fase6-pipeline]
~/projects/photogallery/.claude/worktrees/fase4-frontend 5d1f2a9 [worktree-fase4-frontend]
```

Three folders, three branches, one repository. `backend/.env` is already in place in both worktrees, but the dependencies are missing. In the first session:

```text
install the backend dependencies with composer install
```

In the second:

```text
install the frontend dependencies with npm ci
```

In a real project this is the first step in every worktree, and on a Laravel app with Filament it takes a few minutes.

The copies share the Git history and the auto memory, which Claude Code keeps in `~/.claude/projects/<project>/memory/` for the whole repository. `CLAUDE.md`, on the other hand, is a versioned file: each worktree has its own, identical to the one in `main` when the worktree was created. If you change it in `main` while the sessions are working, they won't see the change until you merge it into their branches.

<!-- TODO screenshot: due terminali affiancati con claude --worktree fase6-pipeline e fase4-frontend, e l'output di git worktree list -->

::: {.callout .callout-warning}
[Warning]{.callout-title}

If you start Laravel Sail in two worktrees at once, the containers fight over the same ports (80, 3306, 6379) and, since the folder is called `backend` in both copies, over the same Docker Compose project name as well. You don't need Sail for this chapter: the tests run on in-memory SQLite with `composer test`. If you need the app running, keep it up in one worktree at a time, or change `APP_PORT` and `FORWARD_DB_PORT` in one of the two `.env` files.
:::

## 20.4 A verifiable goal with /goal

Normally a session works for one turn and then stops to wait for you. With eleven tasks ahead, that means coming back to the terminal every few minutes to type "continue". `/goal` sets a completion condition: Claude keeps working, turn after turn, until the condition is met. A separate evaluator judges it, checking at the end of every turn and sending Claude back to work if something's missing.

### Writing the condition

The evaluator doesn't run commands or open files. It judges what Claude has shown in the conversation. So the condition has to name a check that Claude runs and whose result ends up on screen. Take a condition like this one:

```text
/goal the image pipeline works
```

The evaluator has no way of knowing that. It'll see Claude write that the pipeline works and agree, or it will never agree at all. The same principle applies to the acceptance criteria in chapter 18: "testable, not aspirational", as the header of `docs/TASKS.md` puts it.

In the `fase6-pipeline` session:

```text
/goal tasks T029, T032, T035 and T072 through T079 have Status [x] in docs/TASKS.md (show me the Status lines with grep), "composer test" in the backend folder exits with code 0, and every task has its own commit on the worktree branch (show me git log --oneline)
```

In the `fase4-frontend` session:

```text
/goal tasks T055 through T061 have Status [x] in docs/TASKS.md (show me the Status lines with grep), "npm run build" and "npm run lint" in the frontend folder exit with code 0, and every task has its own commit on the worktree branch (show me git log --oneline)
```

The choices behind these two lines:

- `composer test` is the script in the backend's `composer.json`: it clears the config cache and runs `php artisan test`, that is, Pest;
- in the frontend, on this branch, `package.json` doesn't have a `test` script yet (Vitest is installed, but the first tests arrive with Phase 5), so the check is build and lint, the same ones T062 asks for;
- T080 and T062 stay out. They're the phase review tasks: T080 wants a real upload with the queue worker running, T062 a `curl` against the Vite proxy with Laravel running. You do those yourself, as in chapter 19;
- the "show me" is there for the evaluator: without the `grep` and `git log` output in the conversation, it has no evidence that the tasks are checked off and committed.

The prompt doesn't explain how to work. Reading the `DESIGN.md` sections listed in `Reads`, one commit per task with the message from the `Commit` field, tests before the commit: those are rules 1, 2, 4 and 5 of the project's `CLAUDE.md`, and every session loads them in the worktree too, because the file is versioned.

### The two sessions at work

Once you send the goal, both sessions get going. At the end of a turn, instead of stopping with a summary, Claude picks up again: the evaluator saw that tasks are missing and sent it back to work. `/goal` with no arguments opens the panel with the condition and its status, which you close with `Esc`. `/goal clear` cancels the goal, if you realize the condition was wrong.

`/goal` combines with auto mode, the default permission mode (chapter 11). Auto mode avoids permission prompts within a turn, and `/goal` keeps Claude from stopping between turns. Together they let you look at something else for a while. But if a session asks for something the classifier won't let through, or asks a real question (rule 1 of `CLAUDE.md` says to stop when a task is ambiguous), it waits until you answer.

When the condition is met, the session stops on its own. The work is already committed on the worktree branch:

```bash
git log --oneline -4
```

```text
e41c2d7 feat(pipeline): wire UploadPhotosAction to ProcessPhoto
9b07a15 feat(backend): domain events
3fd8c61 feat(pipeline): ProcessPhoto job
a52e0f9 chore(backend): bind service contracts
```

<!-- TODO screenshot: sessione fase6-pipeline con il pannello di /goal aperto e lo stato della condizione -->

::: {.callout .callout-tip}
[Tip]{.callout-title}

Before you write a long `/goal`, try the check by hand in the worktree: `composer test` in `backend/`, `npm run build` in `frontend/`. If the suite is already red at the start (on the chapter 19 branch T042 and T043 are still `[~]`), the session will spend its time fixing tests that have nothing to do with its phase. In that case, close T042 and T043 on `main` first, then open the worktrees.
:::

## 20.5 Closing the first round

Each track ends in a pull request, as in chapter 19: one PR per phase. From the session:

```text
push the branch and open a pull request against main with gh, titled "Phase 6: image processing pipeline", with the list of completed tasks in the body
```

Then do the two review tasks by hand, T080 in the backend worktree and T062 in the frontend one, and review the PRs. To pick up a PR later without touching your own checkout, `claude --worktree "#12"` (with your PR's number) opens a session in a worktree that starts from that pull request. Review with `/code-review` is the subject of chapter 22. Once both are merged, update `main` locally:

```bash
git switch main
git pull
```

If you'd rather merge locally without going through GitHub, `worktree.baseRef: "head"` becomes necessary: the second-round sessions have to see the pipeline even though you haven't pushed it.

## 20.6 Everything from one screen with agent view

Two terminals are manageable. With four or five sessions it gets awkward, and the second round has at least two: Phase 3 (Filament admin, now that `ProcessPhoto` exists) and Phase 5 (React components).

### Background sessions

`claude --bg` starts a session straight in the background, with a name and a prompt. You don't need to create the worktree by hand: before it edits any file, a background session moves itself into an isolated worktree under `.claude/worktrees/`. `.worktreeinclude` applies to every worktree Claude Code creates with git, so `backend/.env` shows up on its own here too.

```bash
claude --bg --name fase3-admin '/goal tasks T046 through T053 have Status [x] in docs/TASKS.md (show me the Status lines), "composer test" in the backend folder exits with code 0, and every task has its own commit'
claude --bg --name fase5-componenti '/goal tasks T063 through T070 have Status [x] in docs/TASKS.md (show me the Status lines), "npx vitest run" and "npm run build" in the frontend folder exit with code 0, and every task has its own commit'
```

The single quotes are there because the condition contains double quotes. For Phase 5 the check is `npx vitest run` and not `npm test`: Vitest is among the dependencies, but there may not be a `test` script at this point, and `vitest` without `run` would sit there watching for changes. Here too, T054 and T071, the phase reviews, are yours. Each session starts from a worktree with no `vendor/` or `node_modules/` and installs them itself before running the tests.

You can also send a session that's already open to the background. `/background` (alias `/bg`) detaches the current session, and `/fork` (chapter 15) copies its conversation into a new background session while you carry on in the current one.

### Agent view

```bash
claude agents
```

Agent view shows all your background sessions on one screen, grouped by status: Working, Needs input, Completed. The ones that need you are at the top. Each row has the name, a summary of what the session is doing and how long it's been running.

The keys you'll use:

| Key | What it does |
| --- | --- |
| `Space` | Preview of the selected row: the last message or the pending question. You can reply from there without going in |
| `Enter` | Opens the full session |
| `←` on an empty prompt | Back to the list. From any open session, sends the session to the background and opens agent view |
| `Ctrl+T` | Pins the selected session to the top |

In our case the session to keep an eye on is `fase3-admin`: T046 runs `php artisan filament:install --panels`, an installer that asks questions, and that's where the session is most likely to stall. Pin it with `Ctrl+T`. If halfway through it asks whether it can add a package to `composer.json`, you'll see it move to Needs input, answer from the preview with `Space` and go back to the list.

Sessions keep running even if you close the terminal. From the shell you manage them by id:

```bash
claude attach <id>    # reopens the session in this terminal
claude logs <id>      # shows the output without going in
claude stop <id>      # stops the session
claude rm <id>        # removes it from the list
```

<!-- TODO screenshot: agent view con fase3-admin fissata in alto (Working) e fase5-componenti, anteprima aperta con Space -->

### When a session finishes

A background session that's done saves its work: it commits, pushes the branch if the repo has a remote and, when the task calls for it, opens a draft pull request. The PR number appears on the row as a `#N` label, colored by status: yellow while waiting for checks or review, green when ready, purple when merged. On the Photogallery, with the GitHub Actions CI set up in chapter 19, the label stays yellow until the backend and frontend jobs have passed.

<!-- TODO screenshot: riga completata nell'agent view con l'etichetta #N della PR -->

## 20.7 A subagent with its own worktree

If you'd rather stay in a single session, you can give the worktree to subagents instead. Phase 5 is the best fit: `docs/TASKS.md` calls it "heavily parallelizable" and, once T063 is done, tasks T064, T065 and T066 depend only on things already in `main`. This is the alternative to the `fase5-componenti` session from the previous section: pick one of the two routes, not both.

The `/agents` wizard is gone, so you create the subagent by writing the file `.claude/agents/task-executor.md` (or by asking Claude to write it):

```markdown
---
name: task-executor
description: Runs a single task from docs/TASKS.md in an isolated worktree, with tests and a commit. Use it for the independent tasks of a wave.
isolation: worktree
---

You receive the ID of a task in docs/TASKS.md.

1. Read the task and the docs/DESIGN.md sections listed under Reads.
2. Implement only that task, following DESIGN.md and the Acceptance criteria.
3. Install the dependencies if they're missing. Write or update the tests and run
   them until they pass: "composer test" in backend, "npx vitest run" in frontend.
4. Check off the task's Status and commit in the same commit, with the message
   given in the Commit field.
5. If the task requires changing composer.json or package.json, stop and
   report it instead of going ahead.
6. Report: files changed, test results, branch name.
```

`isolation: worktree` gives each instance a temporary worktree, which Claude Code removes if the instance didn't change anything. Step 5 comes from the list of magnet files: three instances adding packages in parallel produce three different `package-lock.json` files to reconcile.

In a normal session at the repo root:

```text
use task-executor in parallel on tasks T064, T065 and T066
```

Subagents run in the background by default: the main session shows that it's waiting on the running agents, `/tasks` lists them and you can keep typing. Each instance works in its own copy and none of them sees the others' half-finished changes. If you run `git worktree list` from another terminal while they work, you'll see one worktree per instance appear, each on its own branch. When they finish, the copies with no changes disappear on their own and the ones with commits stay, with their branches, ready to merge. At that point ask the main session to merge them into `main` and rerun `npx vitest run`, then move on to T067, which depends on T066.

One detail about the starting point: a subagent's worktree follows the same rule as `--worktree`. It starts from the main branch on the remote, or from your local `HEAD` if you set `worktree.baseRef: "head"` as in section 20.2. Either way, T063 has to be there already: if you did it in another worktree and haven't integrated it yet, the three subagents won't find `ErrorBoundary` and `Modal`.

## 20.8 Integrating and cleaning up

When the second-round PRs are ready, review and merge them like the first ones. Merging `docs/TASKS.md` is where a conflict is most likely, because every session changed it. The lines are in different sections, so Git usually merges them on its own. If it can't, the conflict is only about `[ ]` and `[x]` boxes, and you resolve it by keeping the `[x]` ones.

Then clean up. First look at what's left:

```bash
git worktree list
```

When you exit a session started with `--worktree`, Claude Code asks whether to keep or remove the worktree, if it contains work. For background sessions, `claude rm <id>` removes the session from the list along with its worktree, when it's safe to do so. Whatever is left you remove with Git:

```bash
git worktree remove .claude/worktrees/fase6-pipeline
git branch -d worktree-fase6-pipeline
```

`git worktree remove` refuses to delete a worktree with uncommitted changes, and `git branch -d` refuses an unmerged branch. If either one complains, look before you add `--force`: usually there's a commit that never made it to `main`.

### What it costs

Every session uses your plan's quota like a normal session, and the same goes for every subagent instance. Four Opus sessions in parallel burn through it about four times faster than one, and the Photogallery's Wave 1 isn't a five-minute job. `/usage` shows what's eating into your limits, broken down by subagent. Use parallelism for tracks that really don't touch each other, like Phase 4 and Phase 6, and keep the rest sequential: Wave 3 in `docs/TASKS.md` (Phases 12 and 13) is declared sequential precisely because each step depends on the one before.

## 20.9 Command reference

| Command | What it's for |
| --- | --- |
| `claude --worktree <name>` | Session in an isolated worktree in `.claude/worktrees/<name>`, branch `worktree-<name>` |
| `claude --worktree "#123"` | Worktree that starts from a pull request |
| `.worktreeinclude` | Git-ignored files to copy into every new worktree |
| `{"worktree": {"baseRef": "head"}}` | Worktrees start from the local `HEAD` instead of the remote `main` |
| `/goal <condition>`, `/goal`, `/goal clear` | Sets, shows, cancels the goal |
| `claude --bg --name <name> "<prompt>"` | Background session |
| `/background` (`/bg`), `/fork` | Detaches the current session, copies the conversation into the background |
| `claude agents` | Agent view |
| `claude attach`, `logs`, `stop`, `rm <id>` | Manage background sessions from the shell |
| `isolation: worktree` | In a subagent's frontmatter: one temporary worktree per instance |
| `git worktree list`, `git worktree remove <path>` | List and remove worktrees |

## Summary {.unlisted}

- A subagent isolates context, a worktree isolates files and branch, a background session frees up the terminal. For tasks that write code in parallel, you need the worktree.
- Before you parallelize, read the tasks' dependencies and acceptance criteria: T048 depends on `ProcessPhoto` even though its `Depends on` doesn't say so.
- `.claude/worktrees/` goes in `.gitignore`, `.worktreeinclude` copies `backend/.env`, and `worktree.baseRef: "head"` matters when you merge locally without pushing.
- A `/goal` condition works only if it names a check that Claude runs and shows: `composer test` exiting with code 0, the Status lines, the `git log`.
- `claude --bg` and `claude agents` let you follow several sessions from one screen. Each session uses quota like a normal one.

## Exercise {.unlisted}

Start from the `book/cap-13-wave-2-api` branch of the companion repo and run this chapter's first round with the two different tools: commit `.gitignore`, `.worktreeinclude` and `baseRef`, start Track A with `claude --worktree fase6-pipeline` and the `/goal` from section 20.4, and launch Track C as a background session with `claude --bg --name fase4-frontend` and its `/goal`. Follow the second one from agent view until it reaches Completed.

The exercise is done when `git log --oneline` on the pipeline branch shows one commit for each of tasks T029, T032, T035 and T072 through T079, `composer test` passes in that worktree, `npm run build` and `npm run lint` pass on the frontend branch and, after merging and cleaning up, `git worktree list` shows only the main folder.
