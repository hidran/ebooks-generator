# Appendix E. Changelog

Changes to the book, newest first. The first entry describes this edition, the second sums up what changed in Claude Code in the five months between the two editions, and the third is the first edition's record. At the end you'll find how to report a mistake.

## E.1 Second edition, October 2026

The text matches the official documentation as of October 17, 2026, when the latest Claude Code version was 2.1.302 (October 16) and the default model was Claude Opus 5.5.

### New chapters

Seven new chapters, all of them grown out of the lessons in the October update of my Claude Code course:

- Chapter 2, From model to agent: tools, the agentic loop, permissions and the sandbox.
- Chapter 11, Permissions, modes and the sandbox.
- Chapter 12, Hooks.
- Chapter 13, MCP. The first edition promised it for a later update.
- Chapter 14, Plugins and marketplaces, including `claude plugin eval`.
- Chapter 15, Keeping context and memory in check.
- Chapter 20, Parallel waves with worktrees, `/goal` and agent view.

Chapters 11 through 15 make up the new Part IV, Control and automation, and all of them work on the same lab project.

### Merged content

Chapter 22 combines the first edition's pre-deploy QA and multi-LLM review with Claude Code's built-in review: `/code-review` with its effort levels, `--fix` and `--comment`, the `REVIEW.md` file for Code Review on GitHub, and ultrareview in the cloud. The second model is still there, but only for the critical parts.

Chapters 8 and 9 follow the merge of custom commands and skills: chapter 8 introduces the `.claude/commands/` format, and chapter 9 starts from the fact that commands and skills are a single system. In chapter 10, community agents come from plugins instead of a `git clone` into `~/.claude/`.

### The new numbering

There are six parts. The old Part IV (landing page) is now Part V, and the old Part V (Photogallery) is Part VI. Section numbers follow the chapter: the old §13.3 is §19.3.

| Second edition | First edition | Title |
|---|---|---|
| 1 | 1 | What Claude Code is |
| 2 | new | From model to agent: tools, the agentic loop, permissions and the sandbox |
| 3 | 2 | Your first useful prompts |
| 4 | 3 | Analyzing a CSV with Plan Mode |
| 5 | 4 | From CSV to Excel, tabular reports with Python |
| 6 | 5 | Charts, dashboards and PDF reports |
| 7 | 6 | CLAUDE.md, the project's memory |
| 8 | 7 | Custom commands and the Superpowers plugin |
| 9 | 8 | Skills, from command to reusable capability |
| 10 | 9 | Agents and subagents, and when to use what |
| 11 | new | Permissions, modes and the sandbox |
| 12 | new | Hooks, deterministic automation |
| 13 | new | MCP, connecting Claude Code to external services |
| 14 | new | Plugins and marketplaces, packaging skills, agents and hooks |
| 15 | new | Keeping context and memory in check |
| 16 | 10 | A landing page from idea to Firebase deploy |
| 17 | 11 | Photogallery, from prompt to specs |
| 18 | 12 | Spec Driven Development |
| 19 | 13 | Execution and code review, from the first tasks to the wave review |
| 20 | new | Parallel waves with worktrees, /goal and agent view |
| 21 | 14 | Features in flight |
| 22 | 15 | Pre-deploy QA, /code-review and multi-LLM review |
| 23 | 16 | Deploying to AWS with CloudFormation |

There are still five appendices, A through E, in the same order.

### Updates, chapter by chapter

The new chapters are written for the current version. In the others, these are the changes that affect commands or code.

- Chapter 1. Installation goes through the native installer (`curl -fsSL https://claude.ai/install.sh | bash`, on Windows `irm https://claude.ai/install.ps1 | iex`), which updates itself. Homebrew and WinGet are alternatives with manual updates; npm is an advanced option and needs Node.js 22 or later. `claude doctor` and `claude update` come in. `/usage` replaces `/cost`, which has been an alias for it since version 2.1.118 (April 2026), and `/vim` gives way to `/config`, which also accepts the `key=value` form. The `#` memory shortcut had already been removed in 2.0.70 (December 2025): the first edition still presented it. Sessions start in auto mode.
- Chapter 3. Plan Mode is turned on with `Shift+Tab`, with `/plan` or with `claude --permission-mode plan`, and the approval offers `Yes, and use auto mode`. `Ctrl+G` opens the plan in the editor. To get more reasoning you raise the effort with `/effort`; "think hard" isn't a keyword, and `ultrathink` applies to a single prompt.
- Chapter 4. The same Plan Mode updates; for large files, `/context` and `/compact` with instructions on what to keep come in.
- Chapters 5 and 6. Mostly the prose changes. In chapter 6 the frontend-design skill is installed as a plugin from the official marketplace (`frontend-design@claude-plugins-official`).
- Chapter 7. There are four levels of `CLAUDE.md` (organization, user, project, local). Rules in `.claude/rules/` with `paths:`, auto memory, and native reading of `AGENTS.md` from version 2.1.277 come in. The recommended limit is under two hundred lines.
- Chapter 8. Custom commands have been folded into skills: `.claude/commands/` still works, but new work uses `.claude/skills/<name>/SKILL.md`. Superpowers is installed from the official marketplace with `/plugin install superpowers@claude-plugins-official`; the repository given in the first edition wasn't the plugin's, which lives at `obra/superpowers`.
- Chapter 9. The description, together with `when_to_use`, is truncated past 1,536 characters. The skill-creator is installed from `claude-plugins-official`, `/skill-doctor` shows how much context each skill takes, and since version 2.1.218 a skill with `context: fork` runs in the background.
- Chapter 10. The `/agents` wizard has been gone since version 2.1.198: you create an agent by asking Claude or by writing the file in `.claude/agents/`. The example is now `laravel-controller-reviewer`, replacing the first edition's `nest-controller-reviewer`. The `Task` tool is called `Agent`. Subagents run in the background, you follow them with `/tasks` and stop them with `Ctrl+X Ctrl+K`; `/subtask` delegates a job that needs the whole conversation.
- Chapter 16. The stack is the repository's real one: React 19, Vite 6, Tailwind CSS 4.2 and Vitest 4, instead of React 18 and Vite 5.
- Chapter 17. The Photogallery stack is the companion repository's: Laravel 13 as a REST API under `/api/v1`, Filament v5 for the admin, React 19 with Vite 6 and Tailwind CSS v4 for the SPA, Sanctum tokens. NestJS stays only as an alternative rejected during the stack choice, and section 17.1 explains why.
- Chapter 18. The three files live in `docs/REQUIREMENTS.md`, `docs/DESIGN.md` and `docs/TASKS.md`, no longer in `.spec/`, and the project's `CLAUDE.md` is the one from the repository. The text tells apart the 112 tasks in 13 phases on the chapter's branch and the 124 tasks in 14 phases on `main`. Constraints that must never be skipped move to permissions, hooks and `/goal`.
- Chapter 19. The review examples cover Laravel controllers, policies and Form Requests. Parallel subagents share the working tree, so parallel tasks on the same code go into the worktrees from chapter 20.
- Chapter 21. References to phases, waves and tasks (T070, T121, Phase 6.5) follow the companion repository's `docs/TASKS.md`.
- Chapter 22. `/review` has been an alias for `/code-review` since version 2.1.223. `REVIEW.md` customizes Code Review on GitHub (Team and Enterprise plans) but not the local command, which reads only `CLAUDE.md`. You launch ultrareview with `/code-review ultra` or with `claude ultrareview`.
- Chapter 23. The containerized backend is Laravel instead of NestJS, with `config:cache` run at container startup, and the database is RDS MariaDB instead of MySQL. Deploy commands go through an `ask` rule in `.claude/settings.json`.

Throughout the book the reference model is Claude Opus 5.5 with a one-million-token context. I removed the figures showing an outdated interface (Sonnet 4.6 in `/model`, `/cost`, the `/agents` wizard).

### The companion branches keep the old numbers

The repository branches were created for the first edition and I haven't renamed them, so as not to break links already out there. The text always quotes the exact name; this is the full mapping.

| Branch | Repository | Chapter |
|---|---|---|
| `book/cap-10-1-mockups`, `book/cap-10-2-spec`, `book/cap-10-3-execution`, `book/cap-10-5-deploy-ready` | `fluentaipro-claude-landingpage` | 16 |
| `book/cap-11-prompts-and-spec` | `claude-code-book-photogallery` | 17 |
| `book/cap-12-sdd-three-files` | `claude-code-book-photogallery` | 18 |
| `book/cap-13-wave-1-backend`, `book/cap-13-wave-2-api` | `claude-code-book-photogallery` | 19, starting point for 20 |
| `book/cap-14-phases-complete` | `claude-code-book-photogallery` | 21, starting point for 22 |
| `book/cap-15-post-review-fixes` | `claude-code-book-photogallery` | 22, same as `main` |

The first edition also mentioned starting branches for the exercises in the `claude-code-book-snippets` repository (`cap-01-hello-claude`, `cap-03-csv-analysis` and others), which were never published: the repository only has `main`, with one prompt folder per chapter. In this edition every exercise starts from something you create, and the Part II data is generated by the `genera_dati.py` script from chapter 4.

Chapter 23 doesn't have a branch yet: `book/cap-16-aws-deploy` will arrive when the repository's AWS deploy is complete.

### The text

I rewrote the prose of every chapter, cutting the punchlines, the bolded lists and the summaries that repeated the chapter. The opening with what you'll learn and the closing with a summary and an exercise are still there, shorter, and every exercise has a clear done condition. There are five kinds of boxes, described in "How to read this book".

The English and Spanish editions were translated again from the new Italian text.

In Appendix D I checked every link and removed the ones I couldn't verify: the model table (models are now in chapter 2), newsletters, recommended books, alternative tools, and the old documentation address on `docs.anthropic.com`. In place of personal contact details there are the issues on the snippets repository.

## E.2 What changed in Claude Code between May and October 2026

The first edition corresponds roughly to versions 2.1.128-2.1.158 from May 2026. Below are the changes that affect the book and that the first edition didn't cover, with version, date and chapter. Dates and versions come from the changelog and the weekly digest; where the day is missing I give the month or the digest week.

- May, 2.1.139: `/goal`, Claude keeps working until a condition is true. Chapter 20.
- June 9, 2.1.170: Fable 5 arrives, the most capable model, never on by default. Chapter 2.
- June, week 24: a subagent can launch other subagents, up to five levels deep in background chains. Chapter 10.
- June, week 25: `/config key=value`, and permission rules that look at a tool's parameters, such as `Agent(model:opus)`. Chapters 1 and 11.
- June, week 26: the `!` shell mode gets a reply from Claude, permission requests from background subagents show up in the main session, and `claude mcp login` and `logout` arrive. Chapters 1, 10 and 13.
- June 30, 2.1.197: Sonnet 5 briefly becomes the default model on the Pro and Team Standard plans. Chapter 2.
- July 1, 2.1.198: the `/agents` wizard is removed. Chapter 10.
- July, week 27: subagents run in the background by default. Chapter 10.
- July, week 28: `/doctor` becomes a setup check that can also fix things. Chapter 15.
- July 17, 2.1.212: `/fork` copies the conversation into a background session, `/subtask` launches the subagent with the whole conversation, `/background` detaches the session; you follow all of it from agent view (`claude agents`). Chapters 10, 15 and 20.
- July, 2.1.218: skills with `context: fork` run in the background. Chapter 9.
- July 24, 2.1.219: Opus 5 becomes the default model. Chapter 2.
- August 4, 2.1.222: Ultraplan removed; for planning there's still Plan Mode. Chapter 3.
- August 6, 2.1.223: `/review` becomes an alias for `/code-review`; ultrareview is launched with `/code-review ultra`. Chapter 22.
- August 11, 2.1.228: auto mode becomes the starting mode for Pro, Max and Team on macOS, Linux and WSL, and on August 14 (2.1.233) on Windows. Chapters 2 and 11.
- August, week 33: in interactive sessions, subagents launched by Claude start in fork mode, in the background. Chapter 10.
- September 1, 2.1.257: Fable 5.1. Chapter 2.
- September 11, 2.1.269: `claude plugin eval` measures a plugin against a baseline without the plugin. Chapter 14.
- September 18, 2.1.277: Claude Code reads `AGENTS.md` when there's no `CLAUDE.md`. Chapter 7.
- September 22, 2.1.280: Opus 5.5 becomes the default model on every subscription plan. Chapter 2.
- September 25, 2.1.283: auto mode extends to third-party providers, and `/doctor prompt-audit` comes in. Chapters 11 and 15.
- September 28, 2.1.284: auto mode for every plan and provider, and Sonnet 5.5. Chapters 2 and 11.
- Early October, 2.1.287: Claude Mods, hook modules in JavaScript. Chapter 14, only a brief mention.
- October 7, 2.1.293: Haiku 5.5. Chapter 2.
- October 16, 2.1.302: forked subagents become the default in `claude -p`, the Agent SDK, the desktop app and VS Code too. Chapter 10.

## E.3 First edition, May 2026

First published on Amazon KDP, as an ebook and as a print-on-demand paperback.

The book had 16 chapters, about 90,000 words, in five parts: Foundations, Data analysis, Extending Claude Code, Landing page and Photogallery. The appendices were the same five as today. There were more than 50 figures captured from Claude Code and two companion repositories, Photogallery and snippets.

The reference models were Opus 4.7, Sonnet 4.6 and Haiku 4.5; the Claude Code versions of that period were 2.1.1xx.

The book's listing gave the Photogallery stack as NestJS 10, Prisma 5, MySQL 8, React 18 and TanStack Query. That was the starting hypothesis of the specs chapter, not the project in the companion repository, which uses Laravel 13, Filament v5 and React 19: the second edition corrected the text accordingly.

The first edition announced an update with a chapter on MCP, if the specification settled down. That chapter is chapter 13 in this edition.

## E.4 Reporting a mistake

Open an issue on the `github.com/hidran/claude-code-book-snippets` repository with the `errata` label, and write:

- the page (ebook) or the chapter and section (paperback);
- what the book says;
- what actually happened on your installation, with the output of `claude --version`.

Verified corrections go into the next revision and into this appendix. If you agree, whoever sent the report is named in the acknowledgments.

I don't chase every minor Claude Code release. I update the book when a change affects the way you work: a command renamed or removed, a model added or retired, a broken link, a procedure that now has a better one. New features that don't change the workflow stay out until they do. On Kindle you get new versions by turning on automatic book updates, as explained in "How to read this book".
