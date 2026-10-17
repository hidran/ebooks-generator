# Appendix D. Resources

These are the links the chapters rely on, checked in October 2026: the official Claude Code documentation split by part of the book, where to follow what's new, the companion repositories, and the documentation for the tools used in the projects. I kept only official pages that I opened and checked. If a link stops working, search for the page title in the documentation index.

## D.1 The official Claude Code documentation

The Claude Code documentation lives on `code.claude.com`. The first edition pointed to `docs.anthropic.com`: if you find that domain in an old tutorial, look for the same page on the new site.

The full index, one line per page, is a text file: <https://code.claude.com/docs/llms.txt>.

Every page also has a Markdown version, which you get by adding `.md` to the address (`https://code.claude.com/docs/en/hooks-guide.md`). That's the one to hand to Claude when you want it to work from the current documentation instead of from what it remembers.

::: {.callout .callout-tip}
[Tip]{.callout-title}

Before you trust a command you read here or anywhere else, open the `commands` or `cli-reference` page for your version. The tables on those two pages often also tell you in which version a command changed.
:::

### Keep these close

- All slash commands: <https://code.claude.com/docs/en/commands>
- Command-line options: <https://code.claude.com/docs/en/cli-reference>
- Keyboard shortcuts and interactive mode: <https://code.claude.com/docs/en/interactive-mode>
- General troubleshooting: <https://code.claude.com/docs/en/troubleshooting>

### Parts I and II, foundations and data analysis (chapters 1-6)

- Installation and update channels: <https://code.claude.com/docs/en/setup>
- Quickstart: <https://code.claude.com/docs/en/quickstart>
- Installation problems: <https://code.claude.com/docs/en/troubleshoot-install>
- Login, API keys and credential order: <https://code.claude.com/docs/en/authentication>
- The tools available to the agent: <https://code.claude.com/docs/en/tools-reference>
- Permission modes, Plan Mode included: <https://code.claude.com/docs/en/permission-modes>
- The sandbox for Bash commands: <https://code.claude.com/docs/en/sandboxing>
- Models, aliases and effort: <https://code.claude.com/docs/en/model-config>
- Headless mode (`claude -p`): <https://code.claude.com/docs/en/headless>
- VS Code extension: <https://code.claude.com/docs/en/vs-code>
- JetBrains plugin: <https://code.claude.com/docs/en/jetbrains>
- Desktop app: <https://code.claude.com/docs/en/desktop>

### Part III, extending Claude Code (chapters 7-10)

- `CLAUDE.md`, `.claude/rules/`, `AGENTS.md` and auto memory: <https://code.claude.com/docs/en/memory>
- Skills and custom commands: <https://code.claude.com/docs/en/skills>
- Subagents: <https://code.claude.com/docs/en/sub-agents>
- The Anthropic marketplaces, where you install Superpowers from: <https://code.claude.com/docs/en/plugins/anthropic-marketplaces>

### Part IV, control and automation (chapters 11-15)

- Allow, ask and deny rules: <https://code.claude.com/docs/en/permissions>
- Permission modes and auto mode: <https://code.claude.com/docs/en/permission-modes>
- Sandbox: <https://code.claude.com/docs/en/sandboxing>
- Hooks: <https://code.claude.com/docs/en/hooks-guide>
- MCP: <https://code.claude.com/docs/en/mcp>
- Plugins overview: <https://code.claude.com/docs/en/plugins/overview>
- Creating a plugin: <https://code.claude.com/docs/en/plugins/create>
- `claude plugin` commands: <https://code.claude.com/docs/en/plugins/cli-reference>
- Plugin evals (`claude plugin eval`): <https://code.claude.com/docs/en/plugin-evals>
- Memory and context, the same page as in chapter 7: <https://code.claude.com/docs/en/memory>

### Parts V and VI, the projects (chapters 16-23)

- Parallel sessions with worktrees: <https://code.claude.com/docs/en/worktrees>
- Agent view and background sessions: <https://code.claude.com/docs/en/agent-view>
- `/goal`: <https://code.claude.com/docs/en/goal>
- Code Review: <https://code.claude.com/docs/en/code-review>
- Customizing the review with `REVIEW.md`: <https://code.claude.com/docs/en/code-review-customize>
- Review on GitHub pull requests: <https://code.claude.com/docs/en/code-review-pull-requests>
- Ultrareview: <https://code.claude.com/docs/en/ultrareview>
- GitHub Actions and `@claude`: <https://code.claude.com/docs/en/github-actions>
- Cloud sessions: <https://code.claude.com/docs/en/claude-code-on-the-web>

## D.2 Keeping up

Claude Code ships a new version almost every day, and you don't need to follow every one. I watch two pages.

The weekly digest collects the changes that affect how you work, with examples and links to the page that covers them: <https://code.claude.com/docs/en/whats-new>. As I close this edition, the latest published digest is week 37 (September 7-11, 2026); for anything released after that there's only the changelog.

The changelog has one entry per version and is generated from the `CHANGELOG.md` in the `anthropics/claude-code` repository: <https://code.claude.com/docs/en/changelog>. I open it when a command from the book behaves differently and I want to know which version changed it.

In the terminal, three commands are all you need:

```bash
claude --version   # the installed version, for example "2.1.302 (Claude Code)"
claude update      # check for and install the latest version right away
claude doctor      # read-only diagnostics, including the result of the last update
```

With the native installer, updates happen on their own in the background and take effect on the next restart. With Homebrew and WinGet they don't: you update yourself with `brew upgrade claude-code` or `winget upgrade Anthropic.ClaudeCode`.

You pick the update channel in `/config`, under Auto-update channel (in the settings file it's `autoUpdatesChannel`). `latest`, the default, gets every version as soon as it ships. `stable` stays about a week behind and skips versions with major regressions: it's the right choice if you'd rather be careful, in a team for example. You can also install a channel directly:

```bash
curl -fsSL https://claude.ai/install.sh | bash -s stable
```

When a new feature you care about lands, try it on its own on a small project before you bring it into real work, and check whether it makes a step in the book obsolete. If it does, a report is welcome (see D.3).

## D.3 The book's repositories

The project code is public on GitHub. The `book/...` branches capture the chapters' milestones and still carry the first edition's numbers: the full mapping is in Appendix E.

- Photogallery, Part VI: <https://github.com/hidran/claude-code-book-photogallery>. The `main` branch is the finished project: Laravel 13 API under `/api/v1`, Filament v5 admin, React 19 SPA with Vite 6 and Tailwind CSS v4, Sanctum tokens, and the `docs/REQUIREMENTS.md`, `docs/DESIGN.md` and `docs/TASKS.md` documents.
- FluentAiPro landing page, chapter 16: <https://github.com/hidran/fluentaipro-claude-landingpage>, with one branch per phase (`book/cap-10-1-mockups`, `book/cap-10-2-spec`, `book/cap-10-3-execution`, `book/cap-10-5-deploy-ready`).
- Snippets and prompts: <https://github.com/hidran/claude-code-book-snippets>. It collects the reusable prompts chapter by chapter and the Appendix C collection in plain text, handy for copy and paste.

The issues on the `claude-code-book-snippets` repository are also the place to report mistakes in the book. Appendix E explains what to put in the report.

## D.4 Plugins and marketplaces

- The official `claude-plugins-official` marketplace, which Claude Code adds by itself at the first interactive session: <https://github.com/anthropics/claude-plugins-official>
- The `claude-community` community marketplace: <https://github.com/anthropics/claude-plugins-community>
- Superpowers by Jesse Vincent, the plugin from chapters 8, 16 and 19: <https://github.com/obra/superpowers>. You install it from the official marketplace with `/plugin install superpowers@claude-plugins-official`.

::: {.callout .callout-warning}
[Warning]{.callout-title}

Older instructions tell you to run `/plugin marketplace add anthropics/claude-code`. That command adds the `claude-code-plugins` demo marketplace, which isn't the official one.
:::

## D.5 The tools in the projects

The official documentation for the tools Claude uses in the chapters. When a library API looks odd, check here before you ask Claude to guess.

| Tool | Chapters | Documentation |
|---|---|---|
| pandas | 4-6 | <https://pandas.pydata.org/docs/> |
| openpyxl | 5 | <https://openpyxl.readthedocs.io/> |
| matplotlib | 6 | <https://matplotlib.org/> |
| ReportLab | 6 | <https://docs.reportlab.com/> |
| React | 16-23 | <https://react.dev/> |
| Vite | 16-23 | <https://vite.dev/> |
| Tailwind CSS | 16-23 | <https://tailwindcss.com/docs> |
| Firebase Hosting | 16 | <https://firebase.google.com/docs/hosting> |
| Laravel | 17-23 | <https://laravel.com/docs> |
| Filament | 17-23 | <https://filamentphp.com/docs> |
| AWS CloudFormation | 23 | <https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/Welcome.html> |

Versions matter more than usual. Photogallery uses Laravel 13 and Filament v5, and many examples online are written for older versions: always state the version in the prompt, or write it in the project's `CLAUDE.md` as in chapter 18.
