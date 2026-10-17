# How to read this book {.unnumbered}

## In what order

If it's your first time through, read it in order, from chapter 1 to 23. Each part assumes what you saw in the earlier ones: if you reach the Photogallery without ever having used Plan Mode, or without knowing what goes into a CLAUDE.md, some steps will feel like leaps into the dark. At the start of each chapter the prerequisites say which chapters it depends on; if there are none, you can read it on its own.

If you already use Claude Code and care mostly about the method for real projects, there's a shorter route: read chapter 2, then Part III (chapters 7-10), Part IV (chapters 11-15), and jump to the Photogallery (chapter 17). You'll skip the data analysis of Part II and the landing page, which you can come back to later.

After the first read, the book works as a reference. The appendices are built for that: the glossary, troubleshooting, ready-made prompts, resources and changelog aren't meant to be read cover to cover, you go there when you need something.

## Conventions

Text in `monospace` is something to type exactly as shown: a command, a path, a file name, an option, a key. If you see `CLAUDE.md` in this format, I mean that file with that name.

Terminal commands appear in blocks like this one, without the shell prompt in front:

```bash
claude --version
```

Blocks with a different label (`json`, `python`, `markdown`, `text`) contain code, configuration, or the text of a prompt to paste into Claude Code. The prompts are in English in this edition; Claude understands many languages, so feel free to write them in yours.

Here and there you'll find boxes. **Tip** is a shortcut or a habit that saves time. **Warning** flags a common mistake or a concrete risk. **Under the hood** is a technical deep dive you can skip without losing the thread. **Example** shows a case with real input and output. **Reusable prompt** is a prompt ready to adapt to your own projects.

Each chapter opens with what you'll learn and closes with a summary and an exercise. The exercises aren't mandatory, but they're the fastest way to find out what isn't clear yet.

## The companion repositories

The project code is public on GitHub.

`github.com/hidran/claude-code-book-photogallery` holds the Photogallery from Part VI. The `main` branch is the finished project; the `book/...` branches capture the milestones along the way, so you can compare your work or restart from a precise point.

`github.com/hidran/fluentaipro-claude-landingpage` holds the landing page from chapter 16, with a `book/...` branch for each phase.

`github.com/hidran/claude-code-book-snippets` collects the reusable prompts chapter by chapter and the full set from Appendix C as plain text, handy for copy and paste.

::: {.callout .callout-warning}
[Mind the numbers in the branch names]{.callout-title}

The branches were created for the first edition and carry the chapter numbers of that edition. For example, `book/cap-13-wave-1-backend` goes with chapter 19 of this edition and `book/cap-10-3-execution` with chapter 16. The text always gives you the exact branch name to use, so you never have to convert numbers yourself.
:::

To report a mistake, a command that no longer exists or behavior that differs from what the book describes, open an issue in the `claude-code-book-snippets` repository. Verified reports go into the next revision and into the changelog in Appendix E.

## Updates

Claude Code changes fast, and the book gets updated when the changes affect the way you work: renamed commands, removed features, different model behavior. This is the second edition, updated to October 2026. On Kindle you can receive new versions by turning on automatic book updates in your Amazon settings (Manage Your Content and Devices).
