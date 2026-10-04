# Chapter 16 — Multi-Agent Systems

::: {.callout .callout-tip}
[Code for this chapter]{.callout-title}

This chapter is conceptual, and Lab 10 is built from the listings in the chapter itself: there is no standalone code for it. The companion repository at [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) holds runnable versions of the workflow building blocks it relies on (loops, state, interruption and resumption, in the code for Chapters 13 to 15).
:::

## 16.1 Orchestration Patterns

### First, the sceptical question

Multi-agent systems demonstrate beautifully and are frequently the wrong answer. Before adopting one, ask: **would one agent with more tools do this?**

Often yes. Every additional agent is another set of model calls, another system prompt to maintain, another place for context to be lost in translation. Section 1.4's arithmetic applies per agent.

Multi-agent earns its place when: the sub-tasks need genuinely different instructions, the agents need different tool sets or permissions, or you want independent review of one agent's output.

That third one is the strongest case, and it is not really about capability — it is about **independence**. An agent reviewing its own work is a poor critic. A separate agent with a critic's system prompt is a better one.

### The patterns

**Sequential.** Researcher → Writer → Editor. Each stage's output feeds the next. Simple, predictable, easy to debug. The default, and often sufficient.

**Supervisor.** One coordinator decides which specialist to invoke, receives the result, decides what is next. Flexible, and the most expensive — the supervisor makes a model call per decision.

**Parallel.** Several agents work simultaneously on independent sub-tasks; a merge node combines. Fast for genuinely independent work. Section 14.2 gives you the mechanism.

**Debate / critic loop.** A generator produces, a critic evaluates, the generator revises. Repeat until the critic is satisfied or the limit is reached. This is Section 14.1's loop with two agents in it, and it is the highest-quality-per-complexity pattern in the list.

### Mapping patterns to NeuronAI

Each is a workflow shape you already know:

| Pattern | Mechanism |
|---|---|
| Sequential | Chain of nodes, one event each |
| Supervisor | A node returning a union of specialist events |
| Parallel | `ParallelEvent` with named branches |
| Critic loop | Union return type looping back |

**No special multi-agent API.** That is the point of Section 2.3 arriving for the final time: an agent runs inside a node, and composing nodes is what workflows do.

### Cost discipline

A four-agent sequential pipeline is at minimum four model calls, usually more if any of them use tools. A critic loop running three rounds is six or more.

Two mitigations:

**Different models per agent.** The researcher and the critic may need a strong model; the formatter does not. Section 3.6's provider swap is per-node here, and it is one of the framework's better arguments in a multi-agent context.

**Bound every loop.** Section 14.1's counter, non-negotiable.

### Key takeaways

- Ask whether one agent with more tools would do; often it would.
- Independent review is the strongest case for multi-agent.
- Four patterns: sequential, supervisor, parallel, critic loop.
- No special API — agents run inside nodes.
- Vary the model per agent; bound every loop.

## 16.2 An Agent as a Node

### The wrapper

```php
<?php

declare(strict_types=1);

namespace App\Workflow\Nodes;

use App\Agents\ResearchAgent;
use App\Workflow\Events\ProgressEvent;
use App\Workflow\Events\ResearchCompleted;
use App\Workflow\Events\TopicRequested;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\WorkflowState;

class ResearchNode extends Node
{
    public function __invoke(TopicRequested $event, WorkflowState $state): \Generator|ResearchCompleted
    {
        yield new ProgressEvent("Researching {$event->topic}...");

        $findings = ResearchAgent::make()
            ->setThreadId($state->getWorkflowId() . ':research')
            ->chat(new UserMessage("Research this topic thoroughly: {$event->topic}"))
            ->getMessage()
            ?->getContent() ?? '';

        $state->set('sources_used', $this->countSources($findings));

        return new ResearchCompleted($event->topic, $findings);
    }
}
```

The node is a thin adapter. All the intelligence — provider, instructions, tools — lives in `ResearchAgent`, which is unchanged and still works standalone.

That is worth stating explicitly: `ResearchAgent` does not know it is in a workflow. You can still unit-test it, still call it directly, still reuse it in a different pipeline. The node is glue.

`getMessage()` is nullable — it is `null` when the run paused before any inference, or ended with no message at all — hence the `?->` and the fallback.

### An agent is a workflow inside a node

`Agent` extends `Workflow`: `chat()` runs the agent's own graph of nodes to completion and returns its `AgentState`. So a multi-agent workflow is, literally, workflows running inside the nodes of a workflow. Three consequences follow.

**The agent is called, not added.** An agent is not a node — you cannot pass it to `addNodes()`. The node is where you decide what goes into the agent and what comes out.

**The inner run is separate.** A sub-agent has its own identity: an agent's workflow ID is its conversation thread ID, and the framework never makes one up, so a sub-agent with no thread ID throws before it runs. Bind a thread derived from the outer workflow's ID — `->setThreadId($state->getWorkflowId() . ':research')` — and give each sub-agent its own suffix. With no persistence and no message store configured, the sub-agent runs on in-memory persistence and an in-memory history: it shares nothing with the outer workflow's state or store. That is usually what you want for a pipeline stage. Be careful with the one case where the thread is fixed *and* the store is durable: a reviewer inside a loop that always uses the same thread ID and a `messageStore()` backed by a file or a database accumulates every earlier iteration's conversation. A looped sub-agent should keep the default in-memory store, use a thread per iteration (`':review:' . $state->revisionCount()`), or reset its conversation. The outer workflow's durability still covers it at the step level — once `ResearchNode` completes, its result is committed, and a resume or recovery replays it instead of calling the agent again. What is *not* covered is the node that is running when the pause or crash happens; wrap its agent calls in `memoize()` (Section 15.5), as Lab 10 does.

**A sub-agent's pause does not propagate.** If you give a sub-agent an approval-gated tool (Section 15.5), its `chat()` returns an interrupted `AgentState`, and the node reading `getMessage()` would receive the pending tool call rather than an answer. Keep approval-gated tools out of pipeline agents, or check `isInterrupted()` in the node and raise the question to the outer workflow with its own `interrupt()`.

### Structured output between agents

Passing prose between agents loses information and invites misinterpretation. Pass typed objects instead:

```php
class ReviewNode extends Node
{
    public function __invoke(DraftCompleted $event, WorkflowState $state): DraftCompleted|ArticleApproved
    {
        $verdict = ReviewerAgent::make()
            ->setThreadId($state->getWorkflowId() . ':review')
            ->structured(new UserMessage($event->draft), Verdict::class);

        if ($verdict->approved) {
            return new ArticleApproved($event->draft);
        }

        $state->set('last_feedback', $verdict->feedback);

        return new DraftCompleted($event->draft, $verdict->feedback);
    }
}
```

```php
class Verdict
{
    #[SchemaProperty(description: 'Whether the draft meets the quality bar.', required: true)]
    public bool $approved;

    #[SchemaProperty(
        description: 'If not approved, the specific changes required. One instruction per sentence.',
        required: true
    )]
    public string $feedback;

    #[SchemaProperty(description: 'Quality score from 0 to 10.', required: true)]
    #[GreaterThanEqual(reference: 0)]
    #[LowerThanEqual(reference: 10)]
    public int $score;
}
```

**This is Chapter 6 doing structural work.** `$verdict->approved` is a boolean your PHP branches on. Parsing "the draft looks good to me!" for a yes or no would be a coin flip.

The rule: **structured output at every agent-to-agent boundary.** Prose is for humans.

### Different providers per node

```php
class DraftNode extends Node
{
    public function __invoke(ResearchCompleted $event, WorkflowState $state): DraftCompleted
    {
        // Strong model — this is the creative work
        $draft = WriterAgent::make()
            ->setThreadId($state->getWorkflowId() . ':draft')
            ->chat(/* ... */)
            ->getMessage()
            ?->getContent() ?? '';

        return new DraftCompleted($draft);
    }
}

class FormatNode extends Node
{
    public function __invoke(ArticleApproved $event, WorkflowState $state): StopEvent
    {
        // Cheap model — mechanical transformation
        $formatted = FormatterAgent::make()
            ->setThreadId($state->getWorkflowId() . ':format')
            ->chat(/* ... */)
            ->getMessage()
            ?->getContent() ?? '';

        return new StopEvent(result: $formatted);
    }
}
```

Each agent declares its own provider. Cost tiering across a multi-agent system is a property of how you wrote the agents, not something you configure separately.

### Key takeaways

- The node is a thin adapter; the agent stays independent and testable.
- An agent is a workflow: call it from a node, memoize the call if the node can pause, and keep approval-gated tools out of sub-agents.
- Use `structured()` at every agent-to-agent boundary — prose loses information.
- Yield progress from agent nodes; runs are long enough to need it.
- Provider choice is per agent, so cost tiering is free.

## 16.3 Context Without Token Explosion

### The failure mode

The naive multi-agent pipeline accumulates. Agent 1 produces 800 words. Agent 2 receives them plus the original prompt, produces 1,200. Agent 3 receives everything, produces 1,500. Agent 4 receives all of it.

By the fourth agent you are sending 4,000 words of context to produce 300 words of output — and Section 1.4 already showed what accumulation does to cost.

### Four techniques

**1. Pass the artefact, not the transcript.**

The writer needs the research *findings*. It does not need the researcher's reasoning, its tool calls, or its intermediate drafts.

```php
// Bad: the whole conversation
return new ResearchCompleted($agent->getChatHistory()->getMessages());

// Good: just the output
return new ResearchCompleted($event->topic, $findings);
```

**2. Summarise at the boundary.**

When one agent's output is genuinely large, add a compression step. One cheap model call to reduce 3,000 words to 400 saves far more than it costs on any pipeline with two or more downstream agents.

**3. Use state for shared context, events for the handoff.**

Section 13.2's distinction, applied. The tenant, the user, the brief — state. The specific artefact this node produced for the next one — event.

**4. Give each agent only what it needs.**

```php
class FactCheckNode extends Node
{
    public function __invoke(DraftCompleted $event, WorkflowState $state): FactCheckCompleted
    {
        // The fact-checker gets claims and sources. Not the draft's prose,
        // not the brief, not the research narrative.
        $result = FactCheckAgent::make()
            ->setThreadId($state->getWorkflowId() . ':fact-check')
            ->structured(
                new UserMessage(json_encode([
                    'claims'  => $event->extractedClaims,
                    'sources' => $state->get('sources'),
                ])),
                FactCheckResult::class
            );

        return new FactCheckCompleted($result);
    }
}
```

This is ordinary interface design — minimal, explicit inputs — applied to agents. **Each agent has an interface, and a wide interface is as bad here as anywhere else.**

### Measuring it

Subscribe Inspector to the workflow and its agents (Chapter 10) and read input tokens per node across the run. If they grow linearly through the pipeline, you are accumulating. That number is your optimisation target, and it is visible rather than guessed.

### Key takeaways

- Pass artefacts, not transcripts.
- Summarise at boundaries when output is large.
- State for shared context, events for handoffs.
- Treat each agent's input as an interface — keep it minimal.
- Read input tokens per node in the trace to find accumulation.

## 16.4 Asynchronous Execution

### Why this is not optional

Add up what Part IV has established:

- A multi-agent run is many model calls (Section 16.1)
- Each is 1–4 seconds (Section 1.4)
- Parallel tool calls need CLI (Section 5.13)
- Human-in-the-loop means waiting hours or days (Section 15.1)

A 60-second workflow cannot live in an HTTP request. Anything with an interruption *definitely* cannot.

**Long workflows belong on a queue.**

### The architecture

```
HTTP request  → dispatch a job → return a workflow ID immediately
Queue worker  → run the workflow → stream progress over a channel
                                  → persist any interruption
Human         → responds via UI/email
Queue worker  → resume the workflow → complete
Client        → receives progress and the result over the transport
```

Four pieces you already have:

- **Persistence** (Section 15.4) for interruption state
- **Stream adapters and channels** (Section 7.5): the adapter shapes the events, the channel (`setChannel()`) pushes them to a transport
- **Workflow ID** as the correlation key
- **Queue** as the execution context

### What changes on a worker

**`pcntl` and `posix` become available**, so parallel tool calls (Section 5.13) and parallel evals (Section 10.6) work.

**Monitoring must be wired where the worker builds its agents.** Inspector is a listener you subscribe on each agent and workflow (Chapter 10); nothing is attached globally. A worker has no end-of-request, so the subscriber sends each trace when the workflow it started ends. The single most likely misconfiguration in an async deployment is a worker whose agents were never subscribed, which produces no traces at all and no error.

**No HTTP connection to the user.** Which is why streaming channels matter — attach a `PusherChannel` or `RedisChannel` with `setChannel()`, the worker publishes through it, the browser listens.

**Timeouts are yours to manage.** Queue workers have time limits. A workflow that runs for ten minutes needs a worker configured for it, or needs to interrupt and resume across jobs. And a worker killed mid-run — timeout, memory limit — leaves the run marked as running. An agent holds a ten-minute lease by default, after which the next run supersedes the dead one; a plain workflow opts in with `setLeaseTimeout($seconds)`. Pick a lease longer than your slowest node.

### The pattern that ties Part IV together

For a long, human-gated workflow, each segment between interruptions is its own job:

```
Job 1: run until the approval interrupt → persist → notify the manager → end
       (worker is free)
Job 2: triggered by the approval → resume → run to completion or the next interrupt
```

The worker is not blocked waiting. Between segments there is no process at all — only rows in `workflow_store`, under the run's workflow ID.

Job 2 should carry the run ID and execution attempt it saw when the interrupt was recorded, and pass them in `ExecutionRequest::resume($payload, expectedRunId: ..., expectedExecutionAttempt: ...)` to `run()` (Section 15.4). A retried job then fails cleanly instead of delivering a stale answer to a run that has moved on.

That is what "resume even across different sessions" means operationally. It is also, for a PHP audience used to request-scoped execution, a genuinely satisfying resolution: PHP's statelessness stops being a limitation and becomes the deployment model.

### Key takeaways

- Long multi-agent runs belong on a queue; anything with an interruption certainly does.
- On a worker: `pcntl` and `posix` work, monitoring must be subscribed explicitly, leases cover killed workers, and there is no HTTP connection to the user.
- Each segment between interruptions is its own job; nothing waits.
- Persistence, adapters and channels, workflow ID and queue are the four pieces, and you already have all of them.

## Lab 10 — The Content Factory

**Covers:** everything in Part IV.

### Goal

Research → draft → review loop → human approval → publish. It is the canonical multi-agent workflow and it exercises loops, state, streaming, interruption, memoization and persistence in one artefact.

### The shape

```
StartEvent
   ↓
ResearchNode        (Tavily toolkit)
   ↓ ResearchCompleted
DraftNode           (writer agent)
   ↓ DraftCompleted
ReviewNode          (critic agent, structured Verdict)
   ↓ DraftCompleted (loop back, max 3)  |  ArticleApproved
                                        ↓
ApprovalNode        (interrupt — human reviews and edits)
   ↓ ArticleEdited
PublishNode
   ↓ StopEvent
```

### The events

```php
<?php

declare(strict_types=1);

namespace App\Workflow\Events;

use NeuronAI\Workflow\Events\Event;

final class ResearchCompleted implements Event
{
    public function __construct(
        public readonly string $topic,
        public readonly string $findings,
    ) {}
}

final class DraftCompleted implements Event
{
    public function __construct(
        public readonly string $draft,
        public readonly ?string $feedback = null,
    ) {}
}

final class ArticleApproved implements Event
{
    public function __construct(
        public readonly string $draft,
    ) {}
}

final class ArticleEdited implements Event
{
    public function __construct(
        public readonly string $content,
    ) {}
}
```

Note the naming — past-tense facts, per Section 13.4. Note also `readonly`: events are messages, not mutable containers.

### The state

```php
<?php

declare(strict_types=1);

namespace App\Workflow;

use NeuronAI\Workflow\WorkflowState;

class ContentState extends WorkflowState
{
    protected int $revisions = 0;
    protected array $feedbackLog = [];

    public function recordRevision(string $feedback): self
    {
        $this->revisions++;
        $this->feedbackLog[] = $feedback;
        return $this;
    }

    public function revisionCount(): int
    {
        return $this->revisions;
    }

    public function hasReachedLimit(int $max = 3): bool
    {
        return $this->revisions >= $max;
    }

    public function feedbackHistory(): array
    {
        return $this->feedbackLog;
    }
}
```

Scalars and arrays only — no connections, no resources. Section 14.3's serialisation constraint, respected by design.

### The review node — where the part comes together

```php
<?php

declare(strict_types=1);

namespace App\Workflow\Nodes;

use App\Agents\ReviewerAgent;
use App\Dto\Verdict;
use App\Workflow\ContentState;
use App\Workflow\Events\ArticleApproved;
use App\Workflow\Events\DraftCompleted;
use App\Workflow\Events\ProgressEvent;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Workflow\Node;

class ReviewNode extends Node
{
    public function __invoke(
        DraftCompleted $event,
        ContentState $state
    ): \Generator|DraftCompleted|ArticleApproved {
        yield new ProgressEvent('Reviewing the draft...');

        $verdict = $this->memoize('verdict', fn (): Verdict => ReviewerAgent::make()
            ->setThreadId($state->getWorkflowId() . ':review:' . $state->revisionCount())
            ->structured(new UserMessage($event->draft), Verdict::class));

        if ($verdict->approved) {
            yield new ProgressEvent("Approved with a score of {$verdict->score}/10.");

            return new ArticleApproved($event->draft);
        }

        if ($state->hasReachedLimit()) {
            yield new ProgressEvent('Revision limit reached — sending to human review as is.');

            return new ArticleApproved($event->draft);
        }

        $state->recordRevision($verdict->feedback);

        yield new ProgressEvent("Revision {$state->revisionCount()}: {$verdict->feedback}");

        return new DraftCompleted($event->draft, $verdict->feedback);
    }
}
```

Every Part IV concept in one class: a union return type (14.1), a bounded loop with a plan for the limit (14.1), custom state (14.3), streaming progress (14.4), a memoized agent call (13.5), and structured output at an agent boundary (16.2). The reviewer gets a thread per iteration, so each pass starts a fresh conversation.

### The approval node

```php
class ApprovalNode extends Node
{
    public function __invoke(ArticleApproved $event, ContentState $state): ArticleEdited
    {
        $payload = $this->interrupt(
            new ContentReviewInterrupt(
                message: \sprintf(
                    'Article ready after %d revision(s). Review and edit before publishing.',
                    $state->revisionCount()
                ),
                content: $event->draft
            )
        );

        return new ArticleEdited($payload['content'] ?? $event->draft);
    }
}
```

The human edits rather than approves — Section 15.3's collaboration pattern. The edited text comes back in the payload; if the reviewer sends nothing for `content`, the draft goes through unchanged.

### The workflow

```php
/** @extends Workflow<ContentState> */
class ContentWorkflow extends Workflow
{
    protected function state(): ContentState
    {
        return new ContentState();
    }

    protected function nodes(): array
    {
        return [
            new ResearchNode(),
            new DraftNode(),
            new ReviewNode(),
            new ApprovalNode(),
            new PublishNode(),
        ];
    }
}
```

The nodes are typed to `ContentState`, so the workflow must be seeded with that class: the `state()` hook makes every run start with a `ContentState` (seeding it with a plain `WorkflowState` would fail the nodes' type declaration), and the `@extends` annotation tells static analysis that `run()` returns one — so `$state->revisionCount()` type-checks at the call site without a cast.

### The memoization demonstration

Do this deliberately. It is the most valuable twenty minutes in Part IV, because it turns an abstract warning into a bug you have personally caused.

Write `ApprovalNode` so the draft is *generated* inside it, un-memoized:

```php
// DELIBERATELY WRONG — reproduce the bug before fixing it
$draft = WriterAgent::make()
    ->setThreadId($state->getWorkflowId() . ':draft')
    ->chat(new UserMessage($brief))
    ->getMessage()
    ?->getContent() ?? '';

$payload = $this->interrupt(new ContentReviewInterrupt('Review before publishing.', $draft));
```

Run it, interrupt, resume. The draft regenerates and **the resumed version differs from the one the human approved.**

Then wrap it:

```php
$draft = $this->memoize('draft', fn (): string => WriterAgent::make()
    ->setThreadId($state->getWorkflowId() . ':draft')
    ->chat(new UserMessage($brief))
    ->getMessage()
    ?->getContent() ?? '');
```

Re-run. Same draft. Same content the human saw.

That is not an efficiency argument. It is a demonstrable correctness failure with a one-line fix, and it is the reason Section 15.5 exists.

### Running it

```php
// The workflow ID is yours to bind; the framework never generates one.
$workflow = ContentWorkflow::make(workflowId: UniqueIdGenerator::generateId('workflow_'))
    ->setPersistence(new FilePersistence(__DIR__ . '/../storage/workflows'));

$stream = $workflow->events();

foreach ($stream as $event) {
    if ($event instanceof ProgressEvent) {
        echo "  {$event->message}\n";
    }
}

$state = $stream->getReturn();

if (!$state->isInterrupted()) {
    echo "\nPublished.\n";
    exit(0);
}

$id = $state->getWorkflowId();

// The fences travel with the request: the run ID and the execution attempt.
\file_put_contents(
    __DIR__ . "/../storage/pending/{$id}.json",
    \json_encode([
        'run_id' => $state->getRunId(),
        'execution_attempt' => $state->getExecutionAttempt(),
        'request' => $state->getInterruptRequest(),
    ], JSON_PRETTY_PRINT)
);

echo "\nAwaiting review. Workflow ID: {$id}\n";
echo "Edit request.content in storage/pending/{$id}.json and run: php resume.php {$id}\n";
```

`events()` is the streaming terminal from Section 14.4: a generator (it is always a `Generator`) that yields whatever the nodes yield, as they yield it, and returns the final state from `getReturn()`. It yields framework objects too — among them the event that marks the pause — which is why the loop filters on `ProgressEvent`. As with `run()`, the pause is not thrown; you read it off the returned state.

And the resume script, in a separate process:

```php
$pending = \json_decode((string) \file_get_contents(__DIR__ . "/../storage/pending/{$id}.json"), true);

$state = ContentWorkflow::make(workflowId: $id)
    ->setPersistence(new FilePersistence(__DIR__ . '/../storage/workflows'))
    ->run(ExecutionRequest::signal(
        'content.reviewed',
        ['content' => $pending['request']['content']],
        expectedRunId: $pending['run_id'],
        expectedExecutionAttempt: $pending['execution_attempt'],
    ));

echo $state->get('published');
```

The signal carries the run ID and execution attempt recorded at the interrupt, so a duplicated or retried delivery fails instead of answering a run that has moved on. The completed research, draft and review steps are not run again. Only `ApprovalNode` re-executes, receives the edited content, and hands it to `PublishNode`.

Editing a JSON file on disk as the "approval UI" is exactly right for a CLI lab. It makes the mechanism visible, and Chapter 22 replaces it with a real admin screen.

### Acceptance criteria

- The review loop runs at most three times, and hitting the limit escalates rather than failing.
- Killing the PHP process after the interrupt and resuming from a fresh process produces the published article.
- With `memoize()` in place, the published content is byte-identical to what the interrupt request showed the human. Without it, it is not — prove both.
- Progress lines appear as the workflow runs, not all at the end.

### Extensions

1. Add a parallel branch: fact-check and SEO analysis run concurrently after approval, merged before publishing.
2. Add `interruptIf()` so only articles scoring below 8 require human review.
3. Move execution to a queue worker and stream progress over a websocket.

## Chapter Exercises

1. **Build the pipeline.** A three-agent sequential workflow with structured output at each boundary.
2. **Add a critic loop** with a bounded counter and a plan for hitting the limit. The plan matters more than the counter.
3. **Interrupt and resume.** Add an interruption before the final action; persist it; resume from a separate script — a genuinely separate process, not a second call in the same one.
4. **Memoize everything.** Wrap every pre-interrupt LLM call in a `memoize()` and verify it is not re-executed. Log inside the closure to prove it.
5. **Reduce accumulation.** Measure input tokens per node and bring the growth down. Write the before and after numbers next to each other.
