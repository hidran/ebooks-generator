# Chapter 10 — Observability, Evals and Testing

## 10.1 Why You Cannot Debug an Agent

### The problem, in the framework authors' own words

Inspector's documentation for NeuronAI opens with a passage that is unusually honest for vendor documentation:

Integrating AI agents means you are not only working with functions and deterministic code — you are programming by influencing probability distributions. Same input ≠ output. Reproducibility, versioning and debugging become real problems. Prompting is not programming in the common sense: no static types, small changes break output, long prompts cost latency, and no two models behave the same with the same prompt.

That is Section 1.5, restated by the people who built the tool.

### What breaks

**Breakpoints.** You can step through your PHP. You cannot step through the model's decision. The interesting moment — *why did it choose that tool?* — happens on someone else's GPU.

**Reproduction.** "Steps to reproduce" assumes determinism. Re-running the failing input may work fine.

**Logs as you write them.** A log line saying "agent responded" tells you nothing. You need the prompt, the tools offered, the tool selected, the arguments, the result, the tokens and the timing — for every iteration.

**Your mental model of a stack trace.** An agent run is not a call stack. It is a sequence of decisions, and the failure is usually in the reasoning, not in the code.

### What replaces it

| Classical practice | Agentic equivalent |
|---|---|
| Breakpoints | Execution traces |
| Reproduction steps | A dataset of representative inputs |
| Unit tests | Evals with property-based assertions |
| Error rate | Quality score tracked over time |
| Stack traces | Timeline of nodes, tools and tokens |

Three of those five are covered in this chapter. The other two — datasets and quality tracking — are the same tool viewed over time.

### The one-sentence version

> You cannot debug an agent. You can only observe it and measure it.

Which is why observability was a pillar in Section 2.1 rather than an appendix.

### Key takeaways

- Breakpoints, reproduction and equality assertions all assume determinism.
- Traces replace debugging; evals replace unit tests; quality scores replace error rates.
- This is why observability is architectural, not operational.

## 10.2 Setting Up Inspector

### Install

```bash
composer require inspector-apm/inspector-php
```

Only needed if you are not already using another Inspector library — `inspector-laravel`, `inspector-symfony` and so on already include it.

### The environment variable

```dotenv
INSPECTOR_INGESTION_KEY=nwse877auxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Create a key by registering an app at `app.inspector.dev`.

### Register the observer

```php
use Inspector\Neuron\InspectorObserver;

class MyAgent extends Agent
{
    public function __construct()
    {
        parent::__construct();

        $this->observe(InspectorObserver::instance());
    }

    // ...
}
```

`observe()` works on **Agent, RAG and Workflow** — which is Section 2.3 again: they are all workflows, so they all take observers.

### Automatic instrumentation

If your application already reads environment files, NeuronAI is likely to instrument itself as soon as `INSPECTOR_INGESTION_KEY` is present. Registering the observer explicitly is for when you have no access to environment variables, or want to customise the configuration:

```php
$this->observe(
    InspectorObserver::instance('INSPECTOR_INGESTION_KEY')
);
```

### The setting that will bite you: autoFlush

This is the most operationally important paragraph in the chapter.

If your agent runs in a long-running process — a queue worker, Swoole, RoadRunner — you must explicitly enable auto-flush:

```php
$this->observe(
    InspectorObserver::instance(
        key: 'INSPECTOR_INGESTION_KEY',
        autoFlush: true
    )
);
```

Without it, events accumulate in memory and are flushed at the end of the request. A worker process that runs for hours has no "end of request". Your traces never arrive, memory grows, and you conclude the integration is broken when it is merely mis-configured.

Given that Section 1.4 pushes long agent work onto queues, and Section 5.13 requires CLI for parallel tools, **most serious NeuronAI deployments are exactly the case that needs `autoFlush`.**

### Framework-specific packages

If you are integrating into Laravel or Symfony, add the framework package (`inspector-laravel`, `inspector-symfony`) for better data collection. Not required, but recommended — it correlates the agent trace with the HTTP request, the queries and the queue job around it, which is what you actually want when diagnosing a production incident.

Chapter 23 covers this in the Laravel context.

::: {.callout .callout-warning}
[Namespace drift]{.callout-title}

Three different names for this component appear across the ecosystem:

- `Inspector\Neuron\InspectorObserver` (current Inspector docs)
- `NeuronAI\Observability\InspectorObserver` (NeuronAI-side material)
- `NeuronAI\Observability\AgentMonitoring` (older articles, and still in some structured-output examples)

Confirm which exists in your installed version. This is the single most likely place to copy a `use` statement that does not resolve. Appendix A, item 16.
:::

### Key takeaways

- `composer require inspector-apm/inspector-php`, set the key, call `observe()`.
- Works on Agent, RAG and Workflow.
- `autoFlush: true` for queue workers and long-running runtimes — non-optional.
- Three historical names for the observer class; verify yours.

## 10.3 Reading a Trace

### What a trace shows

Every inference step, every tool call, every retrieval — with arguments, results, token counts and timings.

Run the Lab 3 weather agent with Inspector enabled and you get a timeline:

```
▸ WeatherAgent                                        4.82s   3,412 tokens
  ├─ ChatNode                          1.31s     892 in / 84 out
  ├─ ToolNode: get_current_weather     0.42s
  │    input:  {"latitude": 45.0703, "longitude": 7.6869}
  │    output: {"temperature_2m": 14.2, ...}
  ├─ ToolNode: get_current_weather     0.38s
  │    input:  {"latitude": 45.4642, "longitude": 9.19}
  ├─ ChatNode                          1.44s   1,203 in / 61 out
  ├─ ToolNode: mean                    0.01s
  └─ ChatNode                          1.26s   1,172 in / 91 out
```

### The four questions to answer from a trace

Treat it as a procedure, not as "look around":

**1. How many model calls?**
Three here. Section 1.4's cost model, made visible. If you expected one, you have a design problem.

**2. Which tools, with which arguments?**
This is where wrong-tool and wrong-argument bugs are visible. The model called `get_current_weather` with Turin's coordinates — so it derived them correctly. If it had passed a city name as a string, your property description (Section 5.4) needs the worked example.

**3. Where did the time go?**
Model calls: 4.01s. Tools: 0.81s. The model is the bottleneck, so optimisation means fewer iterations, not faster tools. If the ratio were reversed, you would cache the tool.

**4. Where did the tokens go?**
892 → 1,203 → 1,172 input tokens. Growing, because the conversation grows. Exactly the compounding from Section 1.4, now measured rather than estimated.

### Diagnosing from traces: three patterns

**The same tool called five times with near-identical arguments.**
The model does not believe it got an answer. Your tool's return value is ambiguous, or its description does not match what it does. Fix the tool, not the run limit.

**A long gap before the first tool call.**
The model spent time deciding. Usually too many tools, or overlapping descriptions. Filter (Section 5.8) or add `ToolSearchMiddleware`.

**Input tokens far higher than expected on the first call.**
Your tool schemas are large. Count your attached tools. Each one's full schema is in every request.

### The exercise that teaches this best

Do not just look at a healthy trace. **Break something and read the trace.**

Change `get_current_weather`'s description to `'Gets the weather.'` and re-run. The trace shows the model answering with no tool call at all. The code is identical; the only change is a string; the trace shows the model never even considered the tool.

That is the moment Section 5.4 becomes real.

### Key takeaways

- Four questions: how many calls, which tools with which arguments, where the time went, where the tokens went.
- Repeated identical calls mean an ambiguous tool, not a low limit.
- Read a broken trace, not just a healthy one.

## 10.4 Evals: PHPUnit for Non-Deterministic Systems

### The framing that makes it click

Think of an eval as **PHPUnit for a service that is not deterministic.**

A unit test knows the expected output because the function is deterministic. An agent asked the same question twice may give two answers that are both correct and differently worded. You cannot assert equality.

What you can do: define a dataset of realistic inputs, run the agent against each, and assert that the output meets criteria — contains keywords, stays within a length range, matches a pattern, or passes judgement from another agent acting as reviewer.

### Configure the project

Keep evaluators out of production code:

```json
"autoload-dev": {
    "psr-4": {
        "App\\Evaluators\\": "evaluators/"
    }
},
```

```bash
mkdir -p evaluators/datasets
composer dump-autoload
```

`autoload-dev` is the right choice — evaluation code is for development and QA, and should not ship.

::: {.callout .callout-warning}
[Namespace mismatch in the docs]{.callout-title}

The documentation's `autoload-dev` block maps `App\Evaluators\` to `evaluators/`, but the generator command on the same page creates `App\Neuron\Evaluators\AgentEvaluator`. Those two do not agree. Pick one convention and use it consistently. Appendix A, item 20.
:::

### Generate an evaluator

```bash
# Unix
vendor/bin/neuron make:evaluator App\\Neuron\\Evaluators\\AgentEvaluator

# Windows
.\vendor\bin\neuron make:evaluators App\Neuron\Evaluators\AgentEvaluator
```

Note the singular/plural difference between the two tabs in the official docs — `make:evaluator` vs `make:evaluators`. One is a typo. Appendix A, item 17.

### The three-method structure

```php
namespace App\Neuron\Evaluators;

use NeuronAI\Evaluation\Assertions\StringContains;
use NeuronAI\Evaluation\BaseEvaluator;
use NeuronAI\Evaluation\Contracts\DatasetInterface;
use NeuronAI\Evaluation\Dataset\JsonDataset;

class AgentEvaluator extends BaseEvaluator
{
    /**
     * 1. Get the dataset to evaluate against
     */
    public function getDataset(): DatasetInterface
    {
        return new JsonDataset(__DIR__ . '/datasets/dataset.json');
    }

    /**
     * 2. Run the agent logic being tested
     */
    public function run(array $datasetItem): mixed
    {
        $response = MyAgent::make()->chat(
            new UserMessage($datasetItem['input'])
        )->getMessage();

        return $response->getContent();
    }

    /**
     * 3. Evaluate the output against expected results
     */
    public function evaluate(mixed $output, array $datasetItem): void
    {
        $this->assert(
            new StringContains($datasetItem['reference']),
            $output,
        );
    }
}
```

Load a dataset, run each item, assert on the output. That is the whole model, and its simplicity is a feature — the shape is familiar to anyone who has written a data provider in PHPUnit.

### Datasets

**`ArrayDataset`** — inline, good for a handful of cases:

```php
public function getDataset(): DatasetInterface
{
    return new ArrayDataset([
        [
            'input' => 'Hi',
            'reference' => 'help'
        ]
    ]);
}
```

**`JsonDataset`** — a file, which is what you want in practice:

```php
return new JsonDataset(__DIR__ . '/datasets/dataset.json');
```

**There is no prescribed format.** The evaluator loads a list of test cases; the keys are yours. `input` and `reference` are conventions in the examples, not requirements. You can implement `DatasetInterface` to load from anywhere — a database, a CSV, production logs.

That last option is the one worth highlighting: **build your dataset from real failures.** Every time a user reports a bad answer, add the input to the dataset. Your eval suite becomes a regression suite for exactly the things that actually broke.

### Key takeaways

- Evals are PHPUnit for non-deterministic services.
- Three methods: `getDataset()`, `run()`, `evaluate()`.
- `ArrayDataset` for a few cases, `JsonDataset` for real suites, `DatasetInterface` for anything else.
- Grow the dataset from real reported failures.

## 10.5 Assertions and AI as a Judge

### The built-in assertions

```php
$this->assert(new StringContains('positive'), $output);
$this->assert(new StringContainsAll(['hello', 'world']), $output);
$this->assert(new StringContainsAny(['success', 'completed']), $output);
$this->assert(new StringStartsWith('Hello'), $output);
$this->assert(new StringEndsWith('!'), $output);
$this->assert(new StringLengthBetween(10, 100), $output);
$this->assert(new MatchesRegex('/^\d{3}-\d{2}-\d{4}$/'), $output);
$this->assert(new IsValidJson(), $output);
```

Two more interesting ones:

**`StringDistance`** — Levenshtein similarity:

```php
$this->assert(new StringDistance(
    reference: 'expected text',
    threshold: 0.5,   // minimum similarity score
    maxDistance: 50   // maximum allowed edits
), $output);
```

**`StringSimilarity`** — semantic similarity via embeddings:

```php
use NeuronAI\Evaluation\Assertions\StringSimilarity;
use NeuronAI\RAG\Embeddings\OpenAI\OpenAIEmbeddings;

$this->assert(new StringSimilarity(
    reference: 'The quick brown fox',
    embeddingsProvider: new OpenAIEmbeddings(key: 'YOUR_KEY'),
    threshold: 0.6
), $output);
```

The distinction is worth drawing out. `StringDistance` measures *character* similarity — "colour" and "color" are close. `StringSimilarity` measures *meaning* — "the cat sat on the mat" and "a feline was resting on the rug" are close despite sharing almost no characters.

For evaluating natural-language output, semantic similarity is almost always the one you want. It costs an embedding call per assertion, which is cheap.

This is also the first appearance of the embeddings component, which is the whole of Chapter 12.

### AI as a judge

Some qualities cannot be measured with string operations. Is the answer polite? Helpful? Grounded in the source, or hallucinated?

For these, use another agent as the evaluator:

```php
use NeuronAI\Evaluation\Assertions\AgentJudge;

class AgentJudgeEvaluator extends BaseEvaluator
{
    protected AgentInterface $judge;

    public function setUp(): void
    {
        $this->judge = Agent::make()
            ->setAiProvider(new Anthropic(/* ... */))
            ->setInstructions('You are an expert evaluator for customer support responses.');
    }

    public function getDataset(): DatasetInterface
    {
        return new JsonDataset(/* ... */);
    }

    public function run(array $datasetItem): mixed
    {
        return MyAgent::make()
            ->chat(new UserMessage($datasetItem['input']))
            ->getMessage()
            ->getContent();
    }

    public function evaluate(mixed $output, array $datasetItem): void
    {
        $this->assert(new AgentJudge(
            judge: $this->judge,
            criteria: 'Response should be helpful, polite, and address the customer\'s question directly',
            threshold: $datasetItem['threshold']
        ), $output);
    }
}
```

::: {.callout .callout-warning}
[Two things to verify here]{.callout-title}

The official example for this block misspells `Anthropic` as `Antrhopic`. And the fluent methods `setAiProvider()` / `setInstructions()` appear only in this example — confirm they exist in your version before building on them. Appendix A, item 21.
:::

### The four specialised judges

NeuronAI ships judges for the recurring evaluation questions:

**`FaithfulnessJudge`** — is the output grounded in the provided context, or did it hallucinate?

```php
$this->assert(new FaithfulnessJudge(
    judge: $this->judge,
    context: $retrievedDocuments,
    threshold: 0.7
), $output);
```

**This is the single most important assertion for RAG systems**, and it is the reason evals appear before Part III rather than after. A RAG system that answers fluently from information it invented is worse than one that says "I don't know". Faithfulness is how you measure that, and you cannot measure it with string matching.

**`CorrectnessJudge`** — does it match the expected answer?

```php
$this->assert(new CorrectnessJudge(
    judge: $judge,
    expected: $datasetItem['expected_answer'],
    threshold: 0.7
), $output);
```

**`RelevanceJudge`** — does it actually address the question?

**`HelpfulnessJudge`** — is it useful and actionable?

### Two cautions about judges

**The judge is also non-deterministic.** You are measuring a probabilistic system with a probabilistic instrument. Thresholds absorb this, but do not treat a judge score as ground truth. Track it over time and look for movement, not absolute values.

**Judges cost money.** Every judged assertion is an extra LLM call. A 200-item dataset with three judged assertions is 600 extra calls per run. Use a cheaper model for the judge than for the agent — a good application of the provider-swap argument from Section 3.6.

### Custom assertions

```php
use NeuronAI\Evaluation\Assertions\AbstractAssertion;
use NeuronAI\Evaluation\AssertionResult;

class GreaterThanAssertion extends AbstractAssertion
{
    public function __construct(
        private readonly float $threshold
    ) {}

    public function evaluate(mixed $actual): AssertionResult
    {
        if (!is_numeric($actual)) {
            return AssertionResult::fail(
                0.0,
                'Expected numeric value, got ' . gettype($actual),
            );
        }

        if ($actual > $this->threshold) {
            return AssertionResult::pass(1.0);
        }

        return AssertionResult::fail(
            0.0,
            "Expected {$actual} to be greater than {$this->threshold}",
        );
    }
}
```

Note `AssertionResult::pass(1.0)` and `fail(0.0)` — assertions return a **score**, not a boolean. That is what allows partial credit and threshold-based judging, and it is the design detail that makes this a measurement system rather than a pass/fail gate.

### Key takeaways

- Ten built-in assertions; `StringSimilarity` for meaning, `StringDistance` for characters.
- Four judges: faithfulness, correctness, relevance, helpfulness.
- `FaithfulnessJudge` is the essential one for RAG — have it ready before Part III.
- Judges are non-deterministic and cost money; use a cheaper model.
- Assertions return scores, not booleans.

## 10.6 Running Evals: Output, Parallelism and CI

### Running

```bash
# Unix
vendor/bin/neuron evaluations --path=evaluators

# Windows
.\vendor\bin\neuron evaluations --path=evaluators
```

::: {.callout .callout-warning}
[Verify this command before anything else]{.callout-title}

The parallel-execution section of the same documentation page shows a different invocation: `vendor/bin/neuron evaluation path/to/evaluators --concurrency=3` — singular `evaluation`, and a positional argument rather than `--path=`. Run `vendor/bin/neuron list` on your installed version and use whichever is real. Appendix A, item 18, and the one most likely to make your first eval run fail.
:::

### Output drivers

Create `evaluation.php` in the project root:

```php
<?php

use NeuronAI\Evaluation\OutputDrivers\ConsoleDriver;
use NeuronAI\Evaluation\OutputDrivers\JsonDriver;

return [
    'output' => [
        ConsoleDriver::class => ['verbose' => true],
        JsonDriver::class    => ['path' => 'evaluation-results.json'],
    ],
];
```

Options are passed to each driver's constructor. Multiple drivers run simultaneously — console for the developer, JSON for CI to consume.

Without a config file, the system defaults to console output. (The docs name the default `ConsoleOutputDriver` in prose but `ConsoleDriver` in the config example — Appendix A, item 19.)

### Custom output: the pattern that makes evals a business tool

```php
namespace App\Neuron\Evaluations;

use NeuronAI\Evaluation\Contracts\EvaluationOutputInterface;
use NeuronAI\Evaluation\Runner\EvaluatorSummary;

class DatabaseOutput implements EvaluationOutputInterface
{
    public function __construct(
        private readonly \PDO $pdo,
        private readonly string $table = 'evaluations'
    ) {}

    public function output(EvaluatorSummary $summary): void
    {
        $stmt = $this->pdo->prepare(
            "INSERT INTO {$this->table} (passed, failed, success_rate, total_time, created_at, updated_at)
             VALUES (?, ?, ?, ?, NOW(), NOW())"
        );

        $stmt->execute([
            $summary->getPassedCount(),
            $summary->getFailedCount(),
            $summary->getSuccessRate(),
            $summary->getTotalExecutionTime(),
        ]);
    }
}
```

Register it:

```php
return [
    'output' => [
        ConsoleDriver::class => ['verbose' => true],
        DatabaseOutput::class => [
            'pdo'   => new \PDO(/* ... */),
            'table' => 'evaluations',
        ],
    ],
];
```

**Why this matters beyond engineering.** Persisting the success rate on every run gives you a quality metric over time. You can chart it. You can show it to a stakeholder. You can answer "did last week's prompt change make things better or worse?" with a number instead of an opinion.

That is the transition from evals as a developer convenience to evals as evidence. For anyone selling AI work to a business, it is the difference between "trust me" and a graph.

### Parallel execution

Most eval time is spent waiting on the provider. Run items concurrently:

```bash
vendor/bin/neuron evaluation path/to/evaluators --concurrency=3
```

The documented example: one 2-second LLM call per item over a 100-item dataset drops from roughly 200 seconds to roughly 66.

**Requirements** — the same pair as Section 5.13:

```bash
composer require --dev spatie/fork
```

plus `pcntl` (Linux and macOS; not Windows). If either is missing, the command prints a notice and falls back to sequential, so the same command works everywhere.

**Choosing a level.** Every item in flight is an active provider request. Start at 3–5 and increase while you avoid rate limits. Rate-limit errors show up as test failures, so if failures appear when you raise concurrency, lower it before you go hunting for a bug in your agent.

### Four things to know about parallel runs

**Results are unaffected.** Items are independent, order is preserved, the report is identical.

**State is not shared.** Each item sees the state as of `setUp()`. Side effects from one item are invisible to others. If your evaluator accumulates state across items, run it sequentially.

**Outputs must be serializable.** The return value of `run()` crosses a process boundary via `serialize()`. A closure or an open connection cannot cross; assertion results survive but the reported output becomes a placeholder.

**Timing reads oddly.** Total time is wall clock; average per test is real per-item duration. Under parallelism the average can exceed total ÷ count. Expect it rather than filing a bug.

### In CI

```yaml
- name: Run evaluations
  run: vendor/bin/neuron evaluations --path=evaluators
  env:
    ANTHROPIC_KEY: ${{ secrets.ANTHROPIC_KEY }}
```

Three pieces of practical advice:

**Do not gate every PR on the full suite.** It costs money and it is slow. Run a small smoke set on PRs and the full suite nightly.

**Do not fail the build on a single item.** Set a success-rate threshold. A 95 % pass rate on a probabilistic system is a healthy build, not a broken one — and treating one flaky item as a failure teaches your team to ignore the signal.

**Keep the API keys out of forks.** Eval runs cost real money; a public repository with eval-on-PR is a way to donate your budget to strangers.

### Key takeaways

- Verify the eval command against `vendor/bin/neuron list` before anything else.
- Multiple output drivers run at once; a database driver turns evals into a trend.
- `--concurrency` needs `spatie/fork` and `pcntl`, and degrades gracefully without them.
- In CI: smoke set on PRs, full suite nightly, threshold rather than all-or-nothing.

## Lab 7 — A Deterministic Test Suite

**Covers:** everything in this chapter, plus the testability argument from Section 5.3.

### Goal

A PHPUnit suite over an agent that makes **no network calls at all**. It runs in CI, it runs offline, it runs in milliseconds, and it fails for real reasons rather than flaky ones.

This is the complement to evals, not a replacement. Evals measure quality against a live model. This suite proves your wiring is correct without one.

### What to test without a model

Work outward from the deterministic core:

1. **Tool classes, invoked directly.** `(new WeatherTool())(45.07, 7.69)` — no agent, no provider. Mock the HTTP client. This is where most of your logic lives and all of it is ordinary PHP.
2. **Output DTOs and validation rules.** Feed a hand-written array through your validation and assert which violations appear. A custom rule from Section 6.5 deserves its own test.
3. **Cross-field checks.** The invoice arithmetic check from Lab 6 is pure PHP. Test it with a deliberately inconsistent `Invoice`.
4. **Tool visibility.** Build the agent with an admin user and a non-admin user and assert on the resulting tool list. This is an access-control test, and it belongs in your suite for the same reason your route middleware tests do.
5. **Error handlers.** Invoke `resolveToolErrorHandler()` with a `ConnectException` and assert the returned string contains the retry instruction. Section 5.11 argued that the instruction is load-bearing; this is how you stop someone deleting it.

### The fake provider

NeuronAI ships fakes precisely so CI can be deterministic and free. Use a fake provider to script the agent's side of the conversation — a canned tool call followed by a canned final message — and assert that your tools were invoked with the arguments you expect.

The point is inversion: instead of asking "did the model behave correctly?", you ask "given that the model behaved this way, did *my* code do the right thing?" The second question has a right answer.

### Requirements

- Zero network calls. Enforce it: if your test suite passes with the machine offline, you have succeeded. If it does not, find the call.
- Every test deterministic. Run the suite fifty times in a loop; a single failure means something non-deterministic leaked in.
- Fast enough to run on every save.

### Acceptance criteria

- `phpunit` passes with no `.env`, no API keys and no internet.
- Deleting the retry instruction from your error handler makes a test fail.
- Removing a `visible()` condition makes a test fail.
- The suite runs in under two seconds.

### Then, and separately

Wire the eval suite from Sections 10.4–10.6 into a **nightly** job, not the same one. Keep the two clearly separated in your head and in your CI configuration:

| | Test suite | Eval suite |
|---|---|---|
| Asks | Is my code correct? | Is the output good? |
| Needs a model | No | Yes |
| Deterministic | Yes | No |
| Cost | Free | Real money |
| Runs | Every commit | Nightly |
| Fails on | Any failure | Success rate below threshold |

Conflating them is how teams end up with a CI pipeline that is expensive, slow and flaky, and then learn to ignore it.

## Chapter Exercises

1. **Trace a break.** Enable Inspector on a Chapter 5 agent, break a tool description, and read the trace. Write down which of the four questions from Section 10.3 revealed the problem.
2. **Build an evaluator** with five real inputs and at least one `StringSimilarity` assertion.
3. **Add a `FaithfulnessJudge`** assertion. It will matter in Chapter 11, and having it in place first means you can measure your RAG system from its first day rather than retrofitting the measurement afterwards.
4. **Write a custom output driver** that appends to a CSV, and run the suite three times to produce a trend.
5. **Time the suite** sequentially and at `--concurrency=5`. If the gain is smaller than you expected, check whether you are hitting rate limits.

::: {.callout .callout-tip}
[End of Part II]{.callout-title}

You now have an agent that uses tools, remembers conversations, returns typed data, streams, reads documents, connects to external tool servers, and can be traced and measured. That is a complete system, and everything in Parts III to V is built on it rather than beside it.

Twenty-one of Appendix A's forty-four items are in the material you have just worked through. If you have not run the probe scripts yet, this is the natural moment — the next part builds on all of it.
:::
