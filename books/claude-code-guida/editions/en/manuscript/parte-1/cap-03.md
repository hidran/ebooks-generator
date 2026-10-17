# Chapter 3. Your first useful prompts

::: {.chapter-goals}
[What you'll learn]{.callout-title}

How to write a prompt that Claude Code carries through without surprises: what goes into it, which mistakes cost the most on a real project, three patterns to use every day, and how to review the work in Plan Mode before it touches your files. At the end you'll also see how to control how much the model reasons, with effort and `ultrathink`.

[Prerequisites]{.callout-title}

Claude Code installed and working (chapter 1). Chapter 2, on the agentic loop, explains why the advice that follows works.

:::

Claude Code's commands are quick to learn: in an afternoon you'll know the slash commands and shortcuts you actually need. Writing prompts that get the right result on the first pass takes more practice, and that's almost always where a productive session and a frustrating one part ways.

In chapter 2 you saw how an agent works: it gathers context, acts, checks the result, and repeats until the job is done or it needs you. Seen from there, a good prompt does two things. It gives the loop a clear goal, so Claude knows where it's headed, and it gives it a way to check, so Claude knows when it has arrived. Most of this chapter is a variation on those two points.

You won't find generic prompt engineering here, or tricks for getting better answers out of a chatbot. These techniques are for when the model writes code in your project, inside a repo with its own conventions and its own history. Claude Code reads files and runs commands on its own, so you don't have to bring the code into the conversation. For the same reason, a vague prompt costs more than it would in a chat: Claude fills the gaps with whatever it finds in the repo, and it may fill them differently from what you had in mind.

## 3.1 What makes a prompt useful in Claude Code

Three things about Claude Code change how you write a prompt compared with a chat.

### Three differences from a chat

First, it reads files by itself. There's no need to paste code. Write "read `src/services/userService.ts`" and Claude opens the file and sees the exact text. You can also type `@` followed by the path, and autocomplete helps you find it. Pasting a hundred lines when you could point to the file makes the prompt longer and noisier, and a single copy mistake is enough to send Claude down the wrong path.

Second, it runs commands, so it can check your assumptions instead of taking them on faith. "Before you change the router, read every file in `routes/` and tell me how many routes there are and how they validate their parameters." Claude lists the folder, opens the files, and answers with what it found. The prompt becomes a preliminary investigation, and the real change starts from real data.

Third, Claude builds itself a plan before it acts, even when it doesn't show it to you. That plan is only as good as the information you give it. A prompt with a goal, constraints, and examples produces a plan you can review before a single line of code gets written; section 3.5 shows how to make it explicit with Plan Mode.

### The context Claude already has

At startup Claude Code loads the project's `CLAUDE.md`, the instructions file covered in chapter 7. If you've written down the stack, the build and test commands, and the team's conventions there, you don't need to repeat them in every prompt. Everything else Claude doesn't know in advance: it doesn't explore the repo before you type, it reads what it needs when it needs it. So the prompt focuses on what's specific to this request and points to where to look when the starting point isn't obvious.

### Vague prompt, useful prompt: three examples

The first case is a refactoring. The vague prompt:

```text
Make this better.
```

The useful one:

```text
Read src/utils/csvParser.ts. The parseCsv function mixes file reading,
parsing, and validation in a single 80-line block. Split it into three
functions (readFile, parseRaw, validateRows), with parsing and
validation as pure functions, without changing the external behavior:
the public signature must stay identical and the existing tests must
keep passing.
```

With the first one Claude will do something, but you don't know what: it might rename variables, add comments, or rewrite the logic. With the second one it knows what to do and where to stop, and it already has a check at hand: the existing tests.

The second case is a bug. The vague prompt is "Fix this bug." The useful one:

```text
The test "rejects login with wrong password" in tests/auth.test.ts
fails with TypeError: Cannot read properties of null (reading 'id').
Read the test and the loginUser function in src/auth/service.ts. Find
the cause and propose a fix, but don't apply it until I've approved it.
```

The first one doesn't say which bug, where, or under what conditions it shows up. The second gives the coordinates: the test, the error message, the two files to read. And it asks Claude to stop before touching the code. Keep in mind that with auto mode on, that request is an instruction Claude follows, not a hard stop: if you want the guarantee, use Plan Mode (section 3.5).

The third case is a new feature. The vague prompt is "Add pagination." The useful one:

```text
Add server-side pagination to the GET /api/users and GET /api/products
endpoints. Parameters: limit (default 20, maximum 100) and offset
(default 0). The response must have the shape
{ data: [], total: number, limit: number, offset: number }.
Look at how the controllers in src/controllers/ are written and follow
the same conventions. Also update the React pages
src/pages/UsersPage.tsx and src/pages/ProductsPage.tsx. Write tests
for the new behavior.
```

The second prompt is longer, but what matters is the precision: parameters, response format, where to find the conventions, which files to update, what to test. Claude doesn't have to invent any of these choices, because you've already made them.

<!-- TODO screenshot: la vecchia fig-01 (Claude Code appena avviato con `! ls -al`) è stata rimossa perché banner e barra di stato mostrano Sonnet 4.6. Se serve un'immagine qui: sessione appena avviata con Opus 5.5 nel banner e un prompt che usa `@` per indicare un file. -->

## 3.2 Anatomy of a prompt that works

The examples suggest a pattern. Prompts that work with Claude Code almost always contain five elements. You don't need all of them every time, but each one you add removes an assumption Claude would otherwise make on its own.

The context is the current situation: what exists, where it lives, why it's there. You don't have to explain the project, just point Claude at the part you care about. "The `calculateDiscount` function in `src/pricing/engine.ts` applies discounts to B2B orders" is enough; Claude reads the rest from the file.

The goal is what should be different after the change, stated so it can be checked. Not "improve it" but "split it into three functions". Not "fix it" but "the `test_discount_negative` test must pass". This is the part that lets Claude, and then you, tell whether the work is done.

The constraints say what must not change. They're the element people forget most often, and their absence is behind a good share of the mistakes in the next section: "don't touch the public API", "stay compatible with Node 18", "no new dependencies", "follow the pattern already used in `userService.ts`".

The examples are files already written the way you want. "Look at how `src/services/userService.ts` is structured and follow the same pattern" is worth more than a paragraph of explanation: Claude reads the file and picks up the conventions nobody ever wrote down, from function names to error handling.

The desired output is the shape of the result: "show me only the diff", "create the complete file", "first a numbered plan, don't run anything", "list the files you'd touch". That way Claude knows whether to act right away or wait for you, and you know what you're going to get.

::: {.callout .callout-prompt}
[Reusable prompt]{.callout-title}

Template for adding a feature:

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
:::

The template is a starting point. For a small task two lines are enough; for a big one, every missing element should be missing for a specific reason.

### How long should a prompt be

As long as it takes to remove the ambiguity, and no longer. Three precise lines beat twenty lines full of repetition and the odd contradiction. A practical test: reread the prompt and ask yourself whether, knowing nothing about the project, you'd have everything you need to do the task. If the answer is yes, it's long enough.

## 3.3 Five prompting mistakes to avoid

These are the mistakes you pay for on a real project, one with history, dependencies, and parts that can't be touched. In an empty test folder you won't even notice them. Each one has a simple fix.

### Mistake 1: asking without giving context

You write "add logging to the main functions" and that's it. Claude doesn't know which logging library you use, so it picks one. It doesn't know which functions you consider the main ones, so it picks those too. The code you get works but doesn't fit your project: it uses winston where you use pino, writes JSON where the team reads plain text, and touches the wrong functions.

The fix is to point to the context that already exists: "Read `src/logger.ts` to see the library and format we use, and `src/api/` for the functions I care about." If it's information you need often, write it once in `CLAUDE.md` (chapter 7) and stop repeating it.

### Mistake 2: one prompt for five tasks

You put everything into one request: "Refactor the User class, add unit tests, update the documentation, fix the bug in email validation, and prepare a commit with a conventional message." Claude gets going, but it's easy for one of the five things to fall behind, or for two goals to step on each other. The refactoring, for example, breaks tests that target the current implementation, and Claude has to decide on its own which of the two is right.

Split it into successive prompts. First the refactoring, and you check it. Then the tests, and you check them. Then the bug, and finally the commit. Each prompt has a single goal and a result you verify before moving on. Writing four prompts instead of one costs a few minutes; untangling a mistake that has spread across three changes costs a lot more.

### Mistake 3: not saying what to leave alone

You ask Claude to "clean up the orders controller". Claude reads the file, sees functions written in different styles, and decides to make them consistent. Along the way it also changes parts that worked, that your colleagues know by heart, and that an external integration expects in a precise format.

Always add the constraints: "don't change the public signature of the functions", "don't touch `src/legacy/`", "the response format stays as it is, there are clients in production reading it". That's two lines, and they're the difference between a controlled refactoring and a change you find out about when a client stops working.

### Mistake 4: skipping the plan on complex tasks

You need to add OAuth login to an app that doesn't have it. You write the prompt and let Claude work: it creates files, modifies others, adds dependencies. Halfway through, a conflict surfaces between the new session system and the existing middleware, and by then ten files have already been changed.

For work like this, start in Plan Mode. Claude explores the code and writes a plan without changing anything: you see the steps, the files involved, the possible conflicts. You ask questions, request changes, and approve only when the plan convinces you. Section 3.5 explains how.

### Mistake 5: not reading the diff

Claude is done, you take a quick look, it seems fine, and you move on. Three hours later, during integration tests, you discover it also modified a shared utility function to fit the new case, changing an intended behavior that nobody had documented.

In auto mode, the default mode for interactive sessions (chapter 2), Claude doesn't ask you to confirm each file change: when it tells you it's done, the changes are already on disk, and you read the diff afterward with `git diff`, before you commit. In Manual mode, on the other hand, every change reaches you as a diff to approve. Either way, the review is the one you'd do on a colleague's pull request: new files first, since they're less risky, then changes to existing files, with extra attention to functions and interfaces used by other modules. If something's wrong, `/rewind` (or `Esc` twice with an empty prompt) rolls the code back to an earlier checkpoint.

::: {.callout .callout-warning}
[Warning]{.callout-title}

The time you skip the diff because you trust it is almost always the time Claude touched a file you didn't expect. Reading the diff is part of normal code review, just as it is for code written by anyone else. New files are quick to scan; changes to code that's already in production deserve your full attention.
:::

## 3.4 Recurring patterns: plan, examples, verification

Beyond the structure and the mistakes, there are three habits that apply to almost any task, whatever its kind. They complement the five elements from section 3.2.

### Ask for the plan before the code

For any task that goes beyond a few lines, the first prompt asks for a plan, not code:

```text
Plan how you would [goal]. Don't write code. Only numbered steps
with: files to create or modify, the reason for each change,
dependencies between steps, likely trouble spots.
```

You get two things out of it. You can correct the plan before Claude touches any files, and fixing ten lines of plan is much cheaper than repairing fifty lines of code. And the plan sticks around as a document: you can show it to a colleague, paste it into a ticket, or base the commit message on it.

Once you've read the plan, you reply in one of three ways. "Looks good, go ahead", and Claude executes. "Change step 3 like this: ...", and Claude updates the plan and waits. "Step 2 can't touch that file, propose an alternative", and Claude looks for another route. Plan Mode (section 3.5) does the same thing with one extra guarantee: until you approve, the files don't change.

### Show an example

Style instructions written in words stay vague. "Use dependency injection" can be done in plenty of ways, and "follow the project's conventions" says nothing if Claude doesn't know what they are. An example works better:

```text
Read src/services/userService.ts. Create src/services/productService.ts
with the same pattern: dependency injection in the constructor, public
methods that validate input with Zod before calling the database,
errors handled with the custom classes in src/errors/.
```

Claude reads `userService.ts`, picks up the class structure, the naming, the way it handles types and errors, and applies all of it to the new file. You get a file that looks like the rest of the project, instead of one that's correct but written with an approach different from all the others. The pattern works for tests, React components, REST controllers, SQL queries, Terraform configurations: when you want something new in the style of something that exists, point to the file that shows that style best.

### Define how to verify

A prompt that says what to do is fine. One that also says how to check it was done right closes the agentic loop, because Claude has a criterion for knowing when it's finished.

Without a criterion: "Write a function that reads the CSV." With one:

```text
Write a function parseCsv(path: string): Promise<Row[]> with
Row = { date: Date, amount: number, currency: string }. Also write
tests for these cases: empty file, file with only the header, rows with
missing fields, rows with badly formatted dates, valid rows. The tests
must pass with pnpm test.
```

In the second version the criterion is measurable: `pnpm test` either passes or it doesn't. Claude runs the tests, sees what fails, and goes back at it until they're green, which is exactly the verification step of the loop. You can check too without reading every line, because running the tests is enough. The criteria that work best are of this kind:

- specific tests that must pass;
- commands that must produce a given result, such as `pnpm build` with no errors or a `curl` against the endpoint that returns 200;
- measurable thresholds, such as no TypeScript warnings or test coverage of at least 80%.

In chapter 20 you'll find `/goal`, which takes this idea all the way: Claude keeps working, turn after turn, until a separate evaluator judges that a condition such as "`npm test` exits with code 0" is met.

The three patterns combine well in a single prompt. For a refactoring you can put them together like this:

::: {.callout .callout-prompt}
[Reusable prompt]{.callout-title}

Guided refactoring:

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
:::

Replace the parts in square brackets with your own case. The template works for any refactoring, from separating two responsibilities to rewriting an entire module.

## 3.5 Plan Mode, the most important prompt of all

Plan Mode deserves a section of its own. It takes a second to turn on, and on complex tasks it affects the result more than any other technique in this chapter.

### What Plan Mode is

Plan Mode is one of Claude Code's permission modes, all of which are covered in chapter 11. In this mode Claude reads files and runs commands to explore the project, but it doesn't modify the code until you approve. At the end it presents you with a plan. It hands the research off to the built-in Plan subagent, which works read-only with a context of its own.

The difference from writing "don't write code" in the prompt is who enforces the rule. The sentence in the prompt is an instruction the model follows almost always. Plan Mode is a limit enforced by the harness, the program around the model: file changes don't go through until you say yes.

Exploration also depends on the mode you start from. If auto mode is available, the commands run during planning are evaluated by the classifier, and you don't get a confirmation request for every `ls` or `grep`. Otherwise, commands that aren't read-only ask for permission.

### How to get in

You have four ways:

- `Shift+Tab` cycles through the modes (on some Windows setups the key is `Alt+M`). Starting from auto mode, the first press takes you to Manual, the second to Accept edits, the third to Plan. The status bar shows `⏸ plan mode on`.
- `/plan` at the prompt enters Plan Mode. If you add a description, for example `/plan aggiungi la paginazione agli endpoint degli utenti`, Claude starts planning right away.
- `claude --permission-mode plan` starts the session already in Plan Mode.
- In `settings.json`, `"permissions": {"defaultMode": "plan"}` makes it the starting mode. In VS Code the equivalent setting is `claudeCode.initialPermissionMode: "plan"`.

### When to use it

Almost always, except for small, obvious fixes. If you're adding a parameter to a function you know well, you can skip it. Do use it when you:

- add a feature that touches more than three files;
- change a public interface used in several places;
- introduce a new dependency;
- change the authentication or authorization flow;
- work on code you don't know.

In these cases the plan saves you from undoing changes across ten files because, halfway through, a conflict showed up that you'd have spotted right away.

### What you get back

A useful plan contains:

1. numbered steps, in the order they'll be executed;
2. for each step, the files to create or modify and the reason;
3. the dependencies between steps (step 3 uses what step 1 produces);
4. trouble spots and open questions, for example "I can't find the database configuration, where is it?".

If one of these parts is missing, ask for it before approving.

### Approve, correct, start over

When the plan is ready, Claude Code asks how you want to proceed. There are three options, shown here with the interface's own text:

- `Yes, and use auto mode`: you approve and leave Plan Mode in auto mode. If auto mode isn't available, you'll find `Yes, auto-accept edits` in its place.
- `Yes, manually approve edits`: you approve, but every file change comes to you for confirmation.
- `No, keep planning`: you stay in Plan Mode and write what to change, for example "Step 2 can't modify `authMiddleware.ts`, other teams use it. Propose an approach that doesn't touch it." Claude redoes the plan.

`Ctrl+G` opens the plan in your editor so you can fix it by hand before approving. It's worth doing when there are many corrections, or when they involve details that are faster to write than to explain.

<!-- TODO screenshot: piano completato in Plan Mode con il menu di approvazione (Yes, and use auto mode / Yes, manually approve edits / No, keep planning), Opus 5.5 nella barra di stato. -->

Make sure you understand the first option. With auto mode as the default mode, approving with `Yes, and use auto mode` means Claude executes the whole plan without asking you to confirm each change. The classifier still blocks risky actions, such as a force push, an irreversible deletion, or a production deploy, but file changes go through. So the plan becomes your review point: read it the way you'd read a PR, because after approval your next chance to look at the work is the final diff. If you'd rather see each change as it happens, choose `Yes, manually approve edits`.

Sometimes the plan tells you the request itself was wrong. If getting the result takes thirty files, choose to keep planning and rephrase: "This touches thirty files. Find an approach that gets the same result while changing fewer than five." As long as you're working on the plan, every correction costs one message.

### A complete example

With Plan Mode on:

```text
Plan how to add a POST /api/orders endpoint to the NestJS backend.

Specs:
- validate the body with a DTO and class-validator (orderId, items[], total)
- save to Postgres with Prisma (orders table, relation to users)
- respond 201 with the created order
- handle errors: 400 for an invalid body, 404 if the user doesn't
  exist, 500 for database errors

Don't write code. Only numbered steps with:
- files to create (name and type)
- files to modify (name and what changes)
- tests to write (what they must cover)
- dependencies to install, if any
```

In Plan Mode the "Don't write code" line is redundant, but I leave it in so the prompt still works if you paste it into a session in a different mode. The plan you get takes a couple of minutes to read, and when you approve it you know what's about to happen in the project. In chapter 4 you'll use the same flow on a real case, analyzing a CSV.

### How much Claude reasons: effort and ultrathink

How much reasoning the model puts into a task is set by the effort. The levels are `low`, `medium`, `high`, `xhigh`, and `max`. On Opus 5.5, the default model, the starting effort is `medium`. You change it with `/effort`, which opens a picker, or with the left and right arrows inside `/model`. The active level shows in the logo and the spinner; `max` applies only to the current session.

`medium` is fine for quick questions and small changes. For design work, a hard bug, or writing a specification, raise it to `high` before asking for the plan: you spend more tokens, but the plan is better thought through. On the 5.5 models reasoning can't be turned off; the model decides for itself how much to think within the level you've chosen. If you want to keep costs down, the `opusplan` alias uses Opus while you plan and Sonnet when you execute (`/model opusplan`).

If you need more reasoning for a single prompt, write `ultrathink` anywhere in the message. Claude Code adds an instruction to that turn and the model reasons more deeply, while the session's effort stays where it was. Other phrases such as "think hard" or "think it through" aren't keywords: the model reads them as ordinary prompt text.

```text
ultrathink. The orders integration test fails one time in five, only
in CI. Read tests/orders.e2e-spec.ts and src/orders/ and give me the
three most likely causes, in order, with a way to verify each one.
```

## Summary {.unlisted}

- A useful prompt gives the agentic loop a checkable goal and a way to verify it; context, constraints, examples, and output format remove the remaining guesswork.
- Point to files instead of pasting them, and put in `CLAUDE.md` whatever you'd otherwise repeat in every session.
- One task per prompt, with explicit constraints on what not to touch.
- For complex tasks, enter Plan Mode (`Shift+Tab`, `/plan`, or `claude --permission-mode plan`) and review the plan before approving: with `Yes, and use auto mode` it's the last check before the final diff, which you still read before committing.
- Raise the effort to `high` for design work and hard bugs; `ultrathink` applies to a single prompt, and "think hard" does nothing special.

## Exercise {.unlisted}

You need a small codebase where mistakes cost nothing. Have Claude write it in a new folder:

```bash
mkdir -p ~/projects/prompts-lab && cd ~/projects/prompts-lab
git init
claude
```

```text
Create a small Node.js project with three files: src/csv-parser.js, a
minimal CSV parser; src/products-controller.js, a REST controller with
Express and the routes GET /products and GET /products/:id over an
in-memory array; tests/parser.test.js, with two passing tests and three
tests left empty with a TODO comment. Add a package.json with an npm
test script that uses node --test. Don't write anything else.
```

Once the files are there, exit, run `npm install`, and commit everything (`git add -A && git commit -m "punto di partenza"`), so every later diff starts from there. For the precise version in step 1 you can start from the guided refactoring template in the `cap-02/` folder of the `github.com/hidran/claude-code-book-snippets` repository, which follows the first edition's numbering. The exercise takes about 15 minutes.

1. Ask Claude to improve the parser with a vague prompt ("make it better") and watch what it does, then read the result with `git diff`. Undo with `/rewind`, write the version with the five elements from section 3.2, and compare the two diffs.
2. Enter Plan Mode and ask for a plan for a search endpoint in the controller. Choose `No, keep planning` and ask for a change, for example "step 3 must use query parameters, not the body". Approve the revised version.
3. Ask Claude to complete the half-written tests, with the explicit condition that they pass with `npm test`.

You're done when `npm test` exits with code 0, the endpoint plan has been corrected at least once before approval, and you've saved the two prompts from step 1, the vague one and the precise one, so you can compare them when you reread this chapter.
