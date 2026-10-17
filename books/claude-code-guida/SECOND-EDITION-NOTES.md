# Second edition: notes for the author (17 October 2026)

What was done, what needs your decision, and what is wrong in the companion repos.

## What changed

- Source: the Google Doc "manuscript" on Drive (June 2026, Italian). If the Mac copy in
  `~/projects/ebooks/books/claude-code-guida/` has later edits, diff them against this tree
  before publishing.
- Italian rewritten from scratch against `STYLE.md` (no em dashes, arrows, emoji, stock AI
  phrasing; natural dev jargon). `tools/slop-lint.py` checks it: 0 hard findings in all
  three editions.
- Facts updated to Claude Code 2.1.302 (16 October 2026), checked against code.claude.com
  (`FACTS.md`, `FACTS-verified.md`). Seven new chapters (2, 11-15, 20), chapter 22 merged
  with the built-in review lesson. `CHAPTER-MAP.md` has the old-to-new table.
- Every chapter checked against the companion repos; the Photogallery stack is now Laravel
  13 / Filament v5 / React 19 everywhere (the first edition said NestJS in places).
- English and Spanish retranslated from the new Italian.
- Build: all three editions pass epubcheck; paperbacks are exactly 6x9 in (IT 640, EN 641,
  ES 671 pages). Chapters now start on a new page (reference DOCX), author notes are
  stripped from the output (`tools/lib/strip-comments.lua`).

## Decisions for you

1. **Screenshots.** 31 `<!-- TODO screenshot -->` notes mark where a new capture would help.
   The 26 first-edition screenshots kept are 560x315 (Google Docs export), too small for
   print: re-export the originals from the Mac source. `figures/cap-07/fig-01.png` shows an
   account name and a personal path; replace it.
2. **AWS prices** in chapter 23 (one VERIFY note left): check October 2026 eu-west-1 prices.
3. **Exercises** now start from something the reader creates. The snippets repo has only
   `main` with one `prompts.md` per folder: publish starter branches if you want them.
4. **Branch names** in the companion repos keep first-edition chapter numbers
   (`book/cap-13-...` is chapter 19). The book explains it; renaming them is the alternative.
5. **`book/cap-16-aws-deploy`** is announced but not published, and the Photogallery repo
   has no Dockerfile or CloudFormation: chapter 23's deploy code is written for the book
   with the repo's real names but has not been run against the repo.
6. **Italian strings in code** (`hello.py` prints "Ciao mondo", chart titles, file names like
   `vendite.csv`) stay verbatim in EN/ES because readers run the same files.
7. **Contact details**: Appendix D no longer lists your email and LinkedIn; errata go to
   issues on `claude-code-book-snippets`.
8. **Title and subtitle** unchanged (KDP may lock them on a published book). Trim stays 6x9.
9. **Vite**: the Photogallery installs Vite 8, the specs and the book say Vite 6.
10. **Chapter 21** credits Gemini as a reviewer; the repo's review log does not mention it.
11. **KDP listing** (`kdp-listing.md`): descriptions updated with the new Part IV and the
    built-in review, em dashes removed. The back-cover texts were not touched.

## Problems found in the companion repos (not fixed: outside this session)

Photogallery (`hidran/claude-code-book-photogallery`):
- `.claude/settings.json` hooks use a format Claude Code does not recognise (`filePattern`,
  exit 1): they probably never run.
- `CLAUDE.md` is 391 lines (the book recommends under 200), says "80+ tasks", cites
  `DESIGN.md` sections that do not exist (§14, §15) or are wrong (§6.4a, §11).
- `TASKS.md`: header says 13 phases, summary rows add up to 130, IDs T090-T095 used twice.
- T022 mentions an `AuthServiceProvider` the code does not use; AC-F8-5 says `is_favorite=1`,
  the code uses `favorites=1`.
- PHP version differs: 8.3+ (`SPEC.md`), 8.4+ (`README`), 8.5+ (`CLAUDE.md`).
- `BOOK-COMPANION.md` uses first-edition chapter numbers and tells readers to run
  `pnpm test:e2e`, which does not exist on `book/cap-14-phases-complete`.
- `AdminUserSeeder` on `main` falls back to the password `'password'`.

Landing page (`hidran/fluentaipro-claude-landingpage`):
- `BOOK-COMPANION.md` links to `fluentaipro-claude-andingpage` (typo) everywhere.
- `book/cap-10-5-deploy-ready` also deploys to Vercel and its `CLAUDE.md` says Vercel only,
  while the chapter deploys to Firebase.

Snippets (`hidran/claude-code-book-snippets`):
- The README still describes the Photogallery as NestJS + MySQL and uses old chapter numbers.
