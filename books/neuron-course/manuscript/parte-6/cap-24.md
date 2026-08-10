# Chapter 24 — Capstone A: The Repo Auditor CLI

**Stack:** Plain PHP + Composer. No framework.
**Covers:** Chapters 3 to 10 — the whole of Part II.

This capstone is specified, not solved. It states requirements and acceptance criteria and leaves the design to you.

::: {.callout .callout-tip}
[Code for this chapter]{.callout-title}

This chapter is conceptual and has no standalone code, but the companion repository at [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) holds runnable versions of everything the book builds.
:::

## What you are building

A command-line agent that audits a PHP repository and produces a structured report:

```bash
php auditor.php /path/to/repo --format=json
```

```
Auditing /home/hidran/projects/shop ...

  Reading composer.json
  Scanning source tree (412 files)
  Checking dependency advisories
  Reading recent commit history
  Analysing test coverage configuration

━━━ Repo Audit: shop ━━━

Health score       62 / 100
PHP constraint     ^8.1  (consider ^8.3)
Dependencies       47 direct, 3 with known advisories
Test setup         PHPUnit present, no coverage threshold configured
Commit cadence     14 commits in the last 30 days, 2 contributors

Findings (7)
  [high]   Package X has advisory CVE-... — upgrade to 2.4.1
  [medium] No CI configuration found
  [medium] 23 files exceed 400 lines
  ...

Written to audit-shop-2026-08-10.json
```

## Why this project

**It has no external dependencies.** No API keys beyond the LLM, no database, no services. You can complete it on a laptop, offline, with Ollama.

**The tools are genuinely useful.** Reading files, running `git log`, parsing `composer.json` — these are the shapes of tool that most real agents need.

**It exercises the full Part II surface** without any Laravel knowledge, which makes it a standalone portfolio piece if you work in Symfony, WordPress or a legacy stack.

## Build order

### Stage 1 — Scaffolding and the first agent

- Project setup from Section 3.1
- `ProviderFactory` from Section 3.6
- `AuditorAgent` with a `SystemPrompt` that establishes it as a code auditor, not a code fixer
- A CLI entry point taking a path argument

### Stage 2 — The file system tools

Attach `FileSystemToolkit` with `only()`, and write two custom tools:

```php
class ComposerManifestTool extends Tool
{
    public function __construct(private readonly string $repoPath)
    {
        parent::__construct(
            'read_composer_manifest',
            'Returns the composer.json of the repository being audited: the PHP version '
            . 'constraint, the direct dependencies with their version constraints, the '
            . 'autoload configuration, and the declared scripts. Use this first, before any '
            . 'other analysis, to understand what kind of project this is. Never guess a '
            . 'dependency version — read it here.'
        );
    }

    protected function properties(): array
    {
        return [];   // no arguments — the path is a constructor dependency
    }

    public function __invoke(): string
    {
        $path = $this->repoPath . '/composer.json';

        if (! \is_file($path)) {
            return 'No composer.json found. This may not be a PHP project.';
        }

        $manifest = \json_decode(\file_get_contents($path), true, 512, JSON_THROW_ON_ERROR);

        return \json_encode([
            'name'        => $manifest['name']      ?? null,
            'php'         => $manifest['require']['php'] ?? null,
            'require'     => $manifest['require']     ?? [],
            'require-dev' => $manifest['require-dev'] ?? [],
            'scripts'     => \array_keys($manifest['scripts'] ?? []),
        ], JSON_THROW_ON_ERROR);
    }
}
```

**Two things to notice.**

The tool takes **no properties** — the repository path is a constructor dependency, not something the model chooses. That is deliberate: a path the model supplies is a path traversal waiting to happen. Section 5.1's principle, applied concretely.

The return value is a **reduced** manifest, not the whole file. Section 19.1's argument about token cost, in a plain-PHP setting.

### Stage 3 — The git tool and safe subprocess execution

```php
class GitHistoryTool extends Tool
{
    public function __construct(private readonly string $repoPath) { /* ... */ }

    protected function properties(): array
    {
        return [
            new ToolProperty(
                name: 'days',
                type: PropertyType::NUMBER,
                description: 'How many days of history to summarise. Example: 30. Maximum 365.',
                required: true,
            ),
        ];
    }

    public function __invoke(int $days): string
    {
        $days = \max(1, \min(365, $days));   // clamp, never trust the model

        $process = new Process(
            ['git', 'log', "--since={$days} days ago", '--pretty=format:%h|%an|%ad|%s', '--date=short'],
            $this->repoPath,
        );

        $process->setTimeout(15);
        $process->run();

        if (! $process->isSuccessful()) {
            return 'Could not read git history. This may not be a git repository.';
        }

        $lines = \array_slice(\explode("\n", \trim($process->getOutput())), 0, 100);

        return $lines === [''] ? 'No commits in this period.' : \implode("\n", $lines);
    }
}
```

**Three things this gets right, and every one of them matters:**

**Argument arrays, never string interpolation.** `['git', 'log', "--since={$days} days ago"]` with Symfony Process passes arguments without a shell. Interpolating a model-supplied value into a shell string is remote code execution with extra steps.

**Clamp the numeric input.** `max(1, min(365, $days))`. The model may send 99999. Validation attributes are for structured output; tool arguments you validate yourself.

**Bound the output.** `array_slice(..., 0, 100)`. A repository with 40,000 commits would otherwise put 40,000 lines into the conversation.

### Stage 4 — Structured output

The `AuditReport` DTO, using everything from Chapter 6:

```php
class Finding
{
    #[SchemaProperty(description: 'Severity: one of high, medium, low.', required: true)]
    #[Regex('/^(high|medium|low)$/')]
    public string $severity;

    #[SchemaProperty(description: 'Category, e.g. dependencies, testing, structure, security.', required: true)]
    #[NotBlank]
    public string $category;

    #[SchemaProperty(description: 'What the issue is, in one sentence. State the fact you observed.', required: true)]
    #[WordsCount(max: 30)]
    public string $description;

    #[SchemaProperty(description: 'The concrete action to take. Start with a verb.', required: true)]
    #[WordsCount(max: 25)]
    public string $recommendation;

    #[SchemaProperty(description: 'The file or package this concerns, if applicable.', required: false)]
    public ?string $subject = null;
}
```

```php
class AuditReport
{
    #[SchemaProperty(description: 'Overall health score from 0 to 100.', required: true)]
    #[GreaterThanEqual(reference: 0)]
    #[LowerThanEqual(reference: 100)]
    public int $score;

    #[SchemaProperty(description: 'Two-sentence summary of the repository state.', required: true)]
    #[WordsCount(min: 15, max: 60)]
    public string $summary;

    #[SchemaProperty(
        description: 'Every issue found, most severe first.',
        required: true,
        anyOf: [Finding::class]
    )]
    public array $findings;
}
```

`#[WordsCount]` is doing real work here — without it the model writes paragraphs where you wanted a line, and your terminal output becomes unreadable.

### Stage 5 — Streaming, error handling and run limits

- `stream()` with tool-activity labels (Section 7.4)
- `toolErrorHandler()` returning instructions (Section 5.11)
- `toolMaxRuns()` tuned per tool: manifest 1, filesystem 15, git 3
- Handle SIGINT gracefully — this is a CLI tool, so `connection_aborted()` does not apply, but a user pressing Ctrl-C still deserves a clean exit

### Stage 6 — Traces, evals and packaging

- Enable Inspector, read a real trace, tune the tool descriptions based on what you see
- A small eval suite: five repositories with known issues, asserting the findings mention them
- Package as a Composer `bin` so it installs globally

## Assessment rubric

| Criterion | Evidence |
|---|---|
| Tool design | Descriptions follow the four-part formula; property descriptions contain examples |
| Safety | No model-supplied paths; process arguments as arrays; numeric inputs clamped |
| Token discipline | Every tool bounds and reduces its output |
| Structure | The report is a validated DTO, not parsed prose |
| Resilience | Error handler returns instructions; run limits set per tool |
| Measurement | An eval suite exists and produces a score |

## Acceptance criteria

- The auditor runs against three repositories of genuinely different shapes — a Laravel app, a library, something legacy — without an exception.
- A repository with no `composer.json` produces a useful message, not a crash.
- A repository with no git history produces a useful message, not a crash.
- The report validates on the first attempt for at least two of the three, and the retry is visible in the trace when it does not.
- Running the same repository twice produces reports that differ in wording and agree on findings. If they disagree on findings, your tool descriptions need work — not your prompt.

That last criterion is the interesting one. It is Section 1.5's non-determinism, measured on your own output, and it is the difference between a tool you would trust and a toy.

## Extensions

1. Add `parallelToolCalls(true)` — this is a CLI tool, so `pcntl` is available (Section 5.13). Measure the wall-clock difference on a large repository.
2. Add an MCP connector to a GitHub server for issue and pull-request context (Chapter 9). Apply the trust tiering from Section 9.4 before you do.
3. Run the audit across three providers and publish the differences. Which findings appear in all three? Those are the ones you can rely on.
