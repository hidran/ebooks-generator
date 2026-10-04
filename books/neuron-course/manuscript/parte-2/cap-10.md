# Chapter 10 — Observability, Evals and Testing

::: {.callout .callout-tip}
[Code for this chapter]{.callout-title}

The runnable version of every listing below is at [`chapters/Ch10`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch10), in the companion repository. Clone it, run `composer install`, and the examples work against a local Ollama with no API key.
:::

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

## 10.2 Setting Up Observability

### Events, and who listens to them

Every agent, RAG and workflow dispatches events as it runs: the start and end of each node, every inference, every tool call, every retrieval. They are PSR-14 events — plain objects, one class per kind, all extending `NeuronAI\Observability\ObservabilityEvent` — and each instance owns its own dispatcher. There is no global registry. Observability is whatever you subscribe to that dispatcher.

`subscribe()` works on **Agent, RAG and Workflow** — which is Section 2.3 again: they are all workflows, so they all dispatch the same events.

### Start local: a logger

```php
use NeuronAI\Agent\Observability\ToolCalled;
use NeuronAI\Observability\LogListener;
use NeuronAI\Observability\ObservabilityEvent;

$agent = WeatherAgent::make()
    ->subscribe(ObservabilityEvent::class, new LogListener($logger))
    ->subscribe(ToolCalled::class, function (ToolCalled $event): void {
        echo $event->tool->getName() . ' ' . json_encode($event->tool->getInputs()) . PHP_EOL;
    });
```

Matching is by class, with `instanceof` semantics. Subscribing to `ObservabilityEvent::class` receives everything, which is what `LogListener` wants: it writes every event's name and data to any PSR-3 logger. Subscribing to `ToolCalled::class` receives only finished tool calls. Listeners belong to the instance, so they see every run of it, resumed runs included.

Events live in the `Observability` namespace of the module that emits them: `NeuronAI\Agent\Observability` for inference, tool, message and structured-output events, `NeuronAI\Workflow\Observability` for the workflow lifecycle, `NeuronAI\RAG\Observability` for retrieval. Check the `use` line. `subscribe()` takes the class name as a string, so a listener registered against a name that does not exist — `NeuronAI\Observability\Events\ToolCalled`, as older articles print it — raises no error. It simply never fires. When a listener stays silent, the import is the first suspect.

Run it and the loop appears in order: `workflow-start`; then, each node bracketed by a `workflow-node-start` and a `workflow-node-end`, `inference-start`, `inference-stop`, `message-saving`, `message-saved`, `tool-calling`, `tool-called`, a second inference; and finally `workflow-end`. That is already more than "agent responded", and it costs nothing. For timings, token counts and a timeline you can search across thousands of runs, you want a tracing backend.

Two more things belong here. If your application already has a PSR-14 dispatcher, `setEventDispatcher()` forwards every event to it after the agent's own listeners have run. And the older API you will find in articles — `observe()` with an `ObserverInterface` or a `LogObserver` — still works through an adapter, but it is deprecated. Write new code against `subscribe()`.

### Inspector

Inspector is the tracing backend NeuronAI was built alongside. The maintainers' current monitoring guide documents a second option, Neuron Cloud, a hosted platform that ships as `neuron-core/cloud-sdk` for plain PHP, `neuron-core/neuron-cloud-laravel` and `neuron-core/neuron-cloud-symfony`. When this book was verified none of the three was on Packagist, so check before you plan on it. Both are the same mechanism — a PSR-14 listener subscribed to `ObservabilityEvent::class` — so everything below about subscribing applies to either; this chapter shows Inspector. Neither is required: the framework depends on neither and attaches nothing by itself. You install one, and you subscribe it.

```bash
composer require "inspector-apm/inspector-php:^3.19"
```

You need version 3.19 or later for the `Inspector\Neuron\V4` namespace. The 3.18.x releases contain a subscriber written for a pre-release namespace: it loads, subscribes without complaint and records nothing. `inspector-laravel`, `inspector-symfony` and the other framework packages pull the package in for you; require it in your own `composer.json` anyway, and check that the version that resolves is 3.19 or later.

### The environment variable

```dotenv
INSPECTOR_INGESTION_KEY=nwse877auxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Create a key by registering an app at `app.inspector.dev`.

### Subscribe the listener

```php
use Inspector\Neuron\V4\InspectorSubscriber;
use NeuronAI\Observability\ObservabilityEvent;

$agent = MyAgent::make()
    ->subscribe(ObservabilityEvent::class, InspectorSubscriber::instance());
```

`InspectorSubscriber::instance()` reads `INSPECTOR_INGESTION_KEY` from the environment. When you have no environment to read, pass the key as its first argument:

```php
InspectorSubscriber::instance('your-ingestion-key')
```

When your framework already owns an `Inspector` instance, as Laravel and Symfony do, construct the listener around it instead — `new InspectorSubscriber($inspector)` — so the agent's segments land inside the transaction the framework opened for the request or the job.

### The setting you do not need, and the mistake to look for

This is the most operationally important section in the chapter.

**An agent you did not subscribe is not traced.** Setting `INSPECTOR_INGESTION_KEY` is not enough: the key configures a subscriber, it does not attach one. A missing subscription produces no traces and no error, so the natural conclusion — "Inspector is broken" — is wrong.

To cover every agent, subscribe where agents are built — a shared base class, a factory, the container — rather than at each call site:

```php
use Inspector\Neuron\V4\InspectorSubscriber;
use NeuronAI\Agent\Agent;
use NeuronAI\Agent\AgentState;
use NeuronAI\Observability\ObservabilityEvent;

abstract class MonitoredAgent extends Agent
{
    public function __construct(?string $workflowId = null, ?AgentState $state = null)
    {
        parent::__construct($workflowId, $state);

        $this->subscribe(ObservabilityEvent::class, InspectorSubscriber::instance());
    }
}
```

Keep the parent's two-parameter signature and forward it. `make()` passes its arguments straight to the constructor, and an agent's workflow ID is its conversation thread ID, so `MyAgent::make(workflowId: $threadId)` keeps working.

What you do not configure is flushing. Older material tells you to enable `autoFlush` for long-running processes — queue workers, Swoole, RoadRunner — where events would pile up in memory waiting for an end of request that never comes. There is no such option. When the subscriber opened the transaction itself, it sends the trace as soon as the workflow ends, run by run. When the host application opened it, the subscriber leaves flushing to the host.

Given that Section 1.4 pushes long agent work onto queues, and Section 5.13 requires CLI for parallel tools, **most serious NeuronAI deployments run in workers — and in a worker the failure to look for is an agent that was never subscribed.**

### Framework-specific packages

If you are integrating into Laravel or Symfony, add the framework package (`inspector-laravel`, `inspector-symfony`) for better data collection. Not required, but recommended — it correlates the agent trace with the HTTP request, the queries and the queue job around it, which is what you actually want when diagnosing a production incident. Hand its `Inspector` instance to the subscriber, as shown above, so the two end up in the same trace.

Chapter 23 covers this in the Laravel context.

::: {.callout .callout-warning}
[Namespace drift]{.callout-title}

Four names for this component appear across the ecosystem, and only the first works with the NeuronAI this book uses:

- `Inspector\Neuron\V4\InspectorSubscriber` — the PSR-14 listener this chapter subscribes
- `Inspector\Neuron\InspectorObserver` — same package, but written for the observer API of older NeuronAI versions
- `NeuronAI\Observability\InspectorObserver` — from older versions of the framework; it no longer exists
- `NeuronAI\Observability\AgentMonitoring` — older articles, and still in some structured-output examples

The second is the dangerous one: it resolves, and wiring it through the deprecated `observe()` looks as if it works. This is the single most likely place to copy a `use` statement from the wrong version.
:::

### Key takeaways

- Every agent, RAG and workflow dispatches PSR-14 events; `subscribe()` a listener to see them.
- `LogListener` for local visibility, costs nothing.
- Inspector (or Neuron Cloud) is optional: `composer require "inspector-apm/inspector-php:^3.19"`, set the key, subscribe `InspectorSubscriber`.
- A listener subscribed to a class that does not exist never fires and nothing errors; events live in `NeuronAI\Agent\Observability`, `NeuronAI\Workflow\Observability` and `NeuronAI\RAG\Observability`.
- Nothing is attached automatically. Subscribe in a base class or factory so no agent is missed.
- No `autoFlush` to set: the subscriber sends each run's trace when the workflow ends.
- Use `Inspector\Neuron\V4\InspectorSubscriber`; the other three names belong to older versions.

## 10.3 Reading a Trace

### What a trace shows

Every inference step, every tool call, every retrieval — with arguments, results, token counts and timings.

Run the Lab 3 weather agent with Inspector subscribed and you get a timeline:

```
▸ WeatherAgent                                        4.82s   3,641 tokens
  ├─ ChatNode                          1.31s     892 in / 84 out
  ├─ ToolNode: get_current_weather     0.42s
  │    input:  {"latitude": 45.0703, "longitude": 7.6869}
  │    output: {"temperature_2m": 14.2, ...}
  ├─ ToolNode: get_current_weather     0.38s
  │    input:  {"latitude": 45.4642, "longitude": 9.19}
  ├─ ChatNode                          1.44s   1,203 in / 61 out
  ├─ ToolNode: mean                    0.01s
  └─ ChatNode                          1.26s   1,310 in / 91 out
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
892 → 1,203 → 1,310 input tokens. Growing, because the conversation grows. Exactly the compounding from Section 1.4, now measured rather than estimated.

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

### Generate an evaluator

```bash
# Unix
vendor/bin/neuron make:evaluators App\\Evaluators\\AgentEvaluator

# Windows
.\vendor\bin\neuron make:evaluators App\Evaluators\AgentEvaluator
```

The command is `make:evaluators`, plural, on every platform. The official docs show `make:evaluator` on the Unix tab; that command does not exist.

::: {.callout .callout-warning}
[The generator and `autoload-dev`]{.callout-title}

`make:evaluators` resolves the target directory from the PSR-4 prefixes in `composer.json`. On neuron-ai 4.0.2 it read the `autoload` section only, so in a project whose `autoload` maps `App\` to `app/` — every Laravel application — `App\Evaluators\AgentEvaluator` matched that production prefix and the file landed in `app/Evaluators/`, not in `evaluators/`. Since 4.0.3 it reads `autoload-dev` as well, merged after the production prefixes, and the most specific prefix wins: with `App\` in `autoload` and `App\Evaluators\` in `autoload-dev`, as above, the file lands in `evaluators/`. Pass the fully qualified name, and check where the file landed before you build on it; if no prefix matches, the command warns and writes under the current directory. The docs' own example, `App\Neuron\Evaluators\AgentEvaluator`, adds a namespace that matches neither prefix. If the file lands in the wrong place, move it into `evaluators/`, or write evaluators by hand — the structure below is all there is to them.
:::

### The three-method structure

```php
namespace App\Evaluators;

use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Evaluation\Assertions\StringContains;
use NeuronAI\Evaluation\BaseEvaluator;
use NeuronAI\Evaluation\Contracts\DatasetInterface;
use NeuronAI\Evaluation\Dataset\JsonDataset;
use NeuronAI\UniqueIdGenerator;

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
        $state = MyAgent::make()
            ->setThreadId(UniqueIdGenerator::generateId('eval_'))
            ->chat(new UserMessage($datasetItem['input']));

        return $state->getMessage()?->getContent() ?? '';
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

Two details in `run()`. `chat()` returns the final `AgentState`, and its `getMessage()` is nullable, so the evaluator hands the assertion an empty string rather than a null — a string assertion given anything but a string reports the item as an error, not as a failure. And whatever `run()` returns is what `evaluate()` receives as `$output`: a string here, a conversation trajectory in Section 10.5.

Bind a thread ID in `run()`, as above. An agent has no thread ID until you give it one, and `chat()` throws without it; a fresh ID per item also means no item sees another item's conversation.

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
use NeuronAI\RAG\Embeddings\OpenAIEmbeddingsProvider;

$this->assert(new StringSimilarity(
    reference: 'The quick brown fox',
    embeddingsProvider: new OpenAIEmbeddingsProvider(key: 'YOUR_KEY', model: 'text-embedding-3-small'),
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
            ->setThreadId(UniqueIdGenerator::generateId('eval_'))
            ->chat(new UserMessage($datasetItem['input']))
            ->getMessage()
            ?->getContent() ?? '';
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

The judge is an ordinary agent configured fluently: `setAiProvider()` and `setInstructions()` are part of `AgentInterface`, so this works on any agent, not just a bare `Agent::make()`. The assertion asks the judge for a structured score between 0 and 1 with its reasoning, so the judge's model must support structured output.

::: {.callout .callout-warning}
[A typo to avoid]{.callout-title}

The official example for this block misspells `Anthropic` as `Antrhopic`. Copy it and the class does not resolve.
:::

### The specialised judges

NeuronAI ships judges for the recurring evaluation questions, in `NeuronAI\Evaluation\Assertions\Judges`:

**`FaithfulnessJudge`** — is the output grounded in the provided context, or did it hallucinate?

```php
$this->assert(new FaithfulnessJudge(
    judge: $this->judge,
    context: $retrievedContext,
    threshold: 0.7
), $output);
```

`context` is a string: join the retrieved documents' content before you pass it.

**This is the single most important assertion for RAG systems**, and it is the reason evals appear before Part III rather than after. A RAG system that answers fluently from information it invented is worse than one that says "I don't know". Faithfulness is how you measure that, and you cannot measure it with string matching.

**`CorrectnessJudge`** — does it match the expected answer?

```php
$this->assert(new CorrectnessJudge(
    judge: $this->judge,
    expected: $datasetItem['expected_answer'],
    threshold: 0.7
), $output);
```

**`RelevanceJudge`** — does it actually address the question? It takes the original `question` alongside the judge.

**`HelpfulnessJudge`** — is it useful and actionable?

**`TaskCompletionJudge`** — did the agent accomplish a stated `goal` over a whole conversation? This one reads a trajectory rather than a single answer; the next section shows where trajectories come from.

### Name the metric

Every `assert()` records a score, and by default the score is filed under the assertion's class name. Pass a third argument to name the metric yourself:

```php
$this->assert(new FaithfulnessJudge(
    judge: $this->judge,
    context: $retrievedContext,
), $output, 'faithfulness');
```

The label is what the report aggregates by: the console summary and the JSON output show average, minimum, maximum and count per label. It matters as soon as you have two assertions of the same class measuring different things — two `AgentJudge`s, one for tone and one for accuracy, are indistinguishable without it — and it gives you metric names that survive refactoring the assertion that produces them.

### Evaluating what the agent did, not only what it said

A string assertion sees the final answer. For an agent with tools that is often the least interesting part: the question is whether it called the right tool, with the right arguments, and did not call the one it should have left alone.

For that, `run()` drives the agent through a `Conversation` and returns its `Trajectory` — a read-only view over the messages the run produced:

```php
use NeuronAI\Evaluation\Assertions\StringContains;
use NeuronAI\Evaluation\Assertions\Trajectory\ToolWasCalled;
use NeuronAI\Evaluation\Assertions\Trajectory\ToolWasNotCalled;
use NeuronAI\Evaluation\Conversation\Conversation;

public function run(array $datasetItem): mixed
{
    return Conversation::make(WeatherAgent::make())
        ->withTurns([$datasetItem['input']])
        ->run();
}

public function evaluate(mixed $trajectory, array $datasetItem): void
{
    $this->assert(new ToolWasCalled('get_current_weather', ['latitude' => 45.07]), $trajectory);
    $this->assert(new ToolWasNotCalled('delete_forecast'), $trajectory);
    $this->assert(new StringContains('Turin'), $trajectory->finalAnswer());
}
```

`ToolWasCalled` takes an optional argument constraint — a subset of the inputs, as here, or a closure. `TrajectoryMatches` asserts on the sequence of tool names, strictly or loosely. `ToolWasApproved` and `ToolWasRejected` check what happened at the approval gate, and `withApprovals()` on the conversation plays the human when the agent pauses (Chapter 15). String assertions apply to `finalAnswer()`; every judge accepts the trajectory itself and reads its transcript.

This is where evals for agents stop being evals for chatbots. An agent that gives the right answer after calling a tool it should never have touched has passed a string assertion and failed you.

### Two cautions about judges

**The judge is also non-deterministic.** You are measuring a probabilistic system with a probabilistic instrument. Thresholds absorb this, but do not treat a judge score as ground truth. Track it over time and look for movement, not absolute values.

**Judges cost money.** Every judged assertion is an extra LLM call. A 200-item dataset with three judged assertions is 600 extra calls per run. Do not economise by giving the judge a weaker model than the agent: a weaker judge scores more noisily, and you end up tuning against the noise. Control the cost instead with `--cache` (Section 10.6), with a sample of the dataset on pull requests, and with string or trajectory assertions wherever they are enough. Whatever judge you use, check its scores against a handful of answers you have graded by hand.

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

- Ten built-in string assertions; `StringSimilarity` for meaning, `StringDistance` for characters.
- Five judges: faithfulness, correctness, relevance, helpfulness, task completion.
- Name the metric with `assert()`'s third argument; the report aggregates by label.
- Trajectory assertions check which tools ran, with which arguments — the part a final answer hides.
- `FaithfulnessJudge` is the essential one for RAG — have it ready before Part III.
- Judges are non-deterministic and cost money; control the cost with `--cache`, sampling and cheaper assertions, not with a weaker judge.
- Assertions return scores, not booleans.

## 10.6 Running Evals: Output, Parallelism and CI

### Running

```bash
# Unix
vendor/bin/neuron evaluation --path=evaluators

# Windows
.\vendor\bin\neuron evaluation --path=evaluators
```

The command is `evaluation`, singular, and it accepts the directory either as `--path=evaluators` or as a plain positional argument — both forms in the official docs work. If your evaluators autoload through anything other than Composer's autoloader, add `--autoload-file=bootstrap.php`. `vendor/bin/neuron --help` lists every command your installed version has.

The command exits with a non-zero status if any item fails. Keep that in mind for CI, below.

### Output drivers

Create `evaluation.php` in the project root:

```php
<?php

use NeuronAI\Evaluation\Output\ConsoleOutput;
use NeuronAI\Evaluation\Output\JsonOutput;

return [
    'output' => [
        ConsoleOutput::class,
        new JsonOutput(__DIR__ . '/evaluation-results.json'),
    ],
];
```

Note the shape: `output` is a **list**, not a map of class to options. `EvaluationOutputResolver` accepts either a class-string or an already-constructed instance. There is no reflection-based option mapping: a driver that needs an option, like `JsonOutput`'s file path, is handed over ready-made. A class-string is built by the optional `resolver` entry of this file — a `callable(class-string): object`, typically the application's container — or with a plain `new` when there is none, in which case a driver whose constructor needs arguments is refused.

Multiple drivers run simultaneously — console for the developer, JSON for CI to consume.

Without a config file, the system defaults to `[ConsoleOutput::class]`.

### Custom output: the pattern that makes evals a business tool

```php
namespace App\Neuron\Evaluations;

use NeuronAI\Evaluation\Contracts\EvaluationOutputInterface;
use NeuronAI\Evaluation\Runner\EvaluationReport;

class DatabaseOutput implements EvaluationOutputInterface
{
    public function __construct(
        private readonly \PDO $pdo,
        private readonly string $table = 'evaluations'
    ) {}

    public function output(EvaluationReport $report): void
    {
        $results = $report->getResults();

        $stmt = $this->pdo->prepare(
            "INSERT INTO {$this->table} (passed, failed, success_rate, total_time, created_at, updated_at)
             VALUES (?, ?, ?, ?, NOW(), NOW())"
        );

        $stmt->execute([
            $results->getPassedCount(),
            $results->getFailedCount(),
            $results->getSuccessRate(),
            $report->getDuration(),
        ]);
    }
}
```

A driver receives the `EvaluationReport` for the whole run: one report per evaluator, the start and finish instants, and `getResults()`, which flattens every evaluator's items into one set of counts. For per-metric history, `getResults()->getScoreStatisticsByLabel()` returns the average, minimum, maximum and count for each label from Section 10.5 — one row per metric per run is the table you will want to chart.

Register it by class and let a resolver build it:

```php
return [
    'resolver' => fn (string $class): object => match ($class) {
        DatabaseOutput::class => new DatabaseOutput(new \PDO(/* ... */), 'evaluations'),
        default => new $class(),
    },
    'output' => [
        ConsoleOutput::class,
        DatabaseOutput::class,
    ],
];
```

Do not write `new DatabaseOutput(new \PDO(...))` in the list. `evaluation.php` is loaded before the first item runs, so a driver built there holds a live connection when `--concurrency` forks, and every child inherits it. The runner builds the output drivers only after all runs have finished, so a driver listed as a class-string, with the resolver supplying its connection, never has a connection at fork time. Connecting inside `output()` works as well.

**Why this matters beyond engineering.** Persisting the success rate on every run gives you a quality metric over time. You can chart it. You can show it to a stakeholder. You can answer "did last week's prompt change make things better or worse?" with a number instead of an opinion.

That is the transition from evals as a developer convenience to evals as evidence. For anyone selling AI work to a business, it is the difference between "trust me" and a graph.

### Parallel execution

Most eval time is spent waiting on the provider. Run items concurrently:

```bash
vendor/bin/neuron evaluation path/to/evaluators --concurrency=3
```

The documented example: one 2-second LLM call per item over a 100-item dataset drops from roughly 200 seconds to roughly 66.

**Requirements** — the same set as Section 5.13:

```bash
composer require --dev spatie/fork
```

plus the `pcntl` and `posix` extensions (Linux and macOS; not Windows). If any of them is missing, the command prints a notice and falls back to sequential, so the same command works everywhere.

**Choosing a level.** Every item in flight is an active provider request. Start at 3–5 and increase while you avoid rate limits. Rate-limit errors show up as test failures, so if failures appear when you raise concurrency, lower it before you go hunting for a bug in your agent.

### Four things to know about parallel runs

**Results are unaffected.** Items are independent, order is preserved, the report is identical.

**State is not shared.** Each item sees the state as of `setUp()`. Side effects from one item are invisible to others. If your evaluator accumulates state across items, run it sequentially.

**Outputs must be serializable.** The return value of `run()` crosses a process boundary via `serialize()`. A closure or an open connection cannot cross; assertion results survive but the reported output becomes a placeholder.

**Timing reads oddly.** Total time is wall clock; average per test is real per-item duration. Under parallelism the average can exceed total ÷ count. Expect it rather than filing a bug.

### Caching runs, not verdicts

Much of an eval's cost is `run()`, and much of your iteration is on `evaluate()`: tightening a threshold, rewording a judge's criteria, adding an assertion. `--cache` separates the two:

```bash
vendor/bin/neuron evaluation evaluators --cache
```

The first run stores each item's `run()` output under `.neuron/cache/evaluation/`. Later runs serve unchanged items from the cache and **always re-run the assertions**, so you can iterate on `evaluate()` against frozen outputs for free. `--fresh` re-runs everything and overwrites the cache.

The cache key covers the evaluator's `run()` method, the dataset item and the framework version. It does not see your agent's class or your prompt files unless you declare them:

```php
public function cacheDependencies(): array
{
    return [MyAgent::class, __DIR__ . '/../prompts/support.md'];
}
```

Change a declared dependency and the affected items run again. Forget to declare one and you are measuring yesterday's agent. And a cache hit says nothing about provider drift — the model behind the API can change while your cache does not — so pair `--cache` with a periodic `--fresh` run.

### In CI

```yaml
- name: Run evaluations
  run: |
    vendor/bin/neuron evaluation --path=evaluators || true
    php -r '$r = json_decode(file_get_contents("evaluation-results.json"), true, 512, JSON_THROW_ON_ERROR); exit($r["success_rate"] >= 0.95 ? 0 : 1);'
  env:
    ANTHROPIC_KEY: ${{ secrets.ANTHROPIC_KEY }}
```

Three pieces of practical advice:

**Do not gate every PR on the full suite.** It costs money and it is slow. Run a small smoke set on PRs and the full suite nightly.

**Do not fail the build on a single item.** Set a success-rate threshold. A 95 % pass rate on a probabilistic system is a healthy build, not a broken one — and treating one flaky item as a failure teaches your team to ignore the signal. The runner itself exits non-zero on any failed item, so the bare command is an all-or-nothing gate and the threshold is yours to implement. The step above ignores the exit code and reads `success_rate`, a fraction between 0 and 1, from the JSON report that `evaluation.php` writes. If the run crashes before it writes the report, the second command fails and so does the build.

**Keep the API keys out of forks.** Eval runs cost real money; a public repository with eval-on-PR is a way to donate your budget to strangers.

### Key takeaways

- `neuron evaluation <dir>` or `--path=<dir>` — both work; `--help` lists what your version has.
- Multiple output drivers run at once; a database driver turns evals into a trend.
- `--cache` reuses `run()` outputs and always re-evaluates; declare `cacheDependencies()`.
- `--concurrency` needs `spatie/fork`, `pcntl` and `posix`, and degrades gracefully without them.
- In CI: smoke set on PRs, full suite nightly, threshold rather than all-or-nothing.

## Lab 7 — A Deterministic Test Suite

**Covers:** everything in this chapter, plus the testability argument from Section 5.3.

### Goal

A PHPUnit suite over an agent that makes **no network calls at all**. It runs in CI, it runs offline, it runs in milliseconds, and it fails for real reasons rather than flaky ones.

This is the complement to evals, not a replacement. Evals measure quality against a live model. This suite proves your wiring is correct without one.

### What to test without a model

Work outward from the deterministic core:

1. **Tool classes, invoked directly.** `(new WeatherTool($client))(45.07, 7.69)` — no agent, no provider, and `$client` a stubbed `HttpClientInterface`, as in Section 5.3. This is where most of your logic lives and all of it is ordinary PHP.
2. **Output DTOs and validation rules.** Feed a hand-written array through your validation and assert which violations appear. A custom rule from Section 6.5 deserves its own test.
3. **Cross-field checks.** The invoice arithmetic check from Lab 6 is pure PHP. Test it with a deliberately inconsistent `Invoice`.
4. **Tool visibility.** Build the agent with an admin user and a non-admin user and assert on the resulting tool list. This is an access-control test, and it belongs in your suite for the same reason your route middleware tests do.
5. **Error handlers.** `resolveToolErrorHandler()` is a protected hook that returns the handler, so reach it through a small test subclass, call the handler with any `Throwable` and a `ToolCall`, and assert that what it returns contains the retry instruction. Section 5.11 argued that the instruction is load-bearing; this is how you stop someone deleting it.

### The fake provider

NeuronAI ships fakes in `NeuronAI\Testing` precisely so CI can be deterministic and free. Use `FakeAIProvider` to script the model's side of the conversation — a canned tool call followed by a canned final message — and assert that your tools were invoked with the arguments you expect:

```php
use NeuronAI\Agent\Agent;
use NeuronAI\Chat\Messages\AssistantMessage;
use NeuronAI\Chat\Messages\ToolCallMessage;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Testing\FakeAIProvider;
use NeuronAI\Tools\ToolCall;

$provider = new FakeAIProvider(
    new ToolCallMessage(null, [
        ToolCall::make('get_current_weather', 'call_1', ['latitude' => 45.07, 'longitude' => 7.69]),
    ]),
    new AssistantMessage('It is 14 degrees in Turin.'),
);

$calls = new ArrayObject();

$state = Agent::make()
    ->setThreadId('demo')
    ->setAiProvider($provider)
    ->addTool(new RecordingWeatherTool($calls))
    ->chat(new UserMessage('What is the weather in Turin?'));

$provider->assertCallCount(2);
$provider->assertToolsConfigured(['get_current_weather']);
```

`setThreadId()` is there because an agent has no thread ID until you bind one. `RecordingWeatherTool` is the weather tool with its HTTP call replaced by a line that appends its arguments to `$calls`. The recording goes into an injected object on purpose: the agent executes a fresh clone of the registered tool for every call, so anything the tool writes to its own properties disappears with the clone.

The point is inversion: instead of asking "did the model behave correctly?", you ask "given that the model behaved this way, did *my* code do the right thing?" The second question has a right answer.

The fakes are as strict as the parts they replace. `FakeVectorStore` refuses a document without an embedding, exactly as a real store does, and an exhausted response queue throws the provider's own exception rather than failing the test from inside the agent — where a tool error handler could swallow it.

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

1. **Trace a break.** Subscribe Inspector — or a `LogListener` — to a Chapter 5 agent, break a tool description, and read the trace. Write down which of the four questions from Section 10.3 revealed the problem.
2. **Build an evaluator** with five real inputs and at least one `StringSimilarity` assertion.
3. **Add a `FaithfulnessJudge`** assertion. It will matter in Chapter 11, and having it in place first means you can measure your RAG system from its first day rather than retrofitting the measurement afterwards.
4. **Write a custom output driver** that appends to a CSV, and run the suite three times to produce a trend.
5. **Time the suite** sequentially and at `--concurrency=5`. If the gain is smaller than you expected, check whether you are hitting rate limits.

::: {.callout .callout-tip}
[End of Part II]{.callout-title}

You now have an agent that uses tools, remembers conversations, returns typed data, streams, reads documents, connects to external tool servers, and can be traced and measured. That is a complete system, and everything in Parts III to V is built on it rather than beside it.

Much of what the official documentation gets wrong is in the material you have just worked through, which is why the listings in this part were checked against the source. The next part builds on all of it.
:::
