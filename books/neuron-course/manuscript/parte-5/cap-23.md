# Chapter 23 — Production

::: {.callout .callout-tip}
[Code for this chapter]{.callout-title}

Most of this chapter is configuration and checklist, but the usage listener of Section 23.1 is runnable without Laravel at [`chapters/Ch23`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch23) in the companion repository: `usage.php` records the token counts of two inferences from a fake provider, with no model and no API key.
:::

## 23.1 Cost Control

### Measure first

You cannot manage what you do not record. Record usage on every inference:

```php
use NeuronAI\Observability\Events\InferenceStop;

class RecordUsage
{
    public function __construct(
        private readonly string $agent,
        private readonly string $model,
        private readonly ?int $tenantId,
        private readonly ?int $userId,
    ) {}

    public function __invoke(InferenceStop $event): void
    {
        $usage = $event->response->message()->getUsage();

        if ($usage === null) {
            return;   // the provider reported none
        }

        AiUsage::create([
            'tenant_id'     => $this->tenantId,
            'user_id'       => $this->userId,
            'agent'         => $this->agent,
            'model'         => $this->model,
            'input_tokens'  => $usage->inputTokens,
            'output_tokens' => $usage->outputTokens,
            'cached_tokens' => $usage->cachedInputTokens,
        ]);
    }
}
```

```php
$agent->subscribe(InferenceStop::class, new RecordUsage(
    agent: $agent::class,
    model: $agent->getProvider()->getModel(),
    tenantId: $user->tenant_id,
    userId: $user->id,
));
```

Observability in NeuronAI is a PSR-14 event dispatcher owned by each agent instance (Section 10.2), and `InferenceStop` fires after every model call — so this writes one row per inference, not per request. An agent that loops through three tool calls produces four rows, which is exactly the granularity that makes a looping agent visible. Two details are easy to get wrong: the token counts are on the *provider response's* message, `$event->response->message()->getUsage()` — `$event->message` is the last message *sent* — and `getUsage()` returns `null` when a provider reports nothing, so guard for it. Subscribe the listener where you build the agent: in the factory or container binding from Section 18.1, so no agent escapes it.

Keep `cached_tokens` even if you ignore it today. Prompt caching bills those tokens at a fraction of the normal rate, and whether they are already included in `input_tokens` differs between providers — a cost report that cannot tell them apart will be wrong in one direction or the other.

Four questions this answers that nothing else will:

- Which agent costs the most?
- Which user or tenant costs the most?
- Is cost per request rising over time?
- Did last week's prompt change make things cheaper or more expensive?

### The three levers, revisited

Section 1.4 named them. In production they look like this:

**Fewer iterations.** Sharper tool descriptions (5.4), fewer tools attached (5.8), lower run limits (5.9). Read traces to find the agents that loop.

**Smaller context.** Aggressive history trimming (4.4), compact tool output (19.1), fewer RAG chunks, summarisation at agent boundaries (16.3).

**Cheaper model per step.** `AIProvider::driver('ollama')` on the classifier, the default on the writer (17.6).

### Caching

The highest-leverage and most-overlooked lever, because a cached answer costs nothing:

```php
class CachedClassifier
{
    public function classify(string $text): string
    {
        return Cache::remember(
            'classify:' . \hash('xxh128', $text),
            now()->addDays(7),
            fn () => ClassifierAgent::make()
                ->structured(new UserMessage($text), Classification::class)
                ->label
        );
    }
}
```

**Cache deterministic-ish tasks:** classification, extraction from a fixed document, embedding of unchanged text, translation of a fixed string.

**Do not cache conversational answers.** The same question in a different conversation deserves a different answer.

**Embedding caching is the biggest win in RAG.** Text that has not changed does not need re-embedding — which is exactly what the `wasChanged('body')` guard in Section 20.2 was for.

### Budgets

```php
// config/neuron.php
'budgets' => [
    'per_user_daily'   => env('AI_BUDGET_USER_DAILY', 2.00),
    'per_tenant_daily' => env('AI_BUDGET_TENANT_DAILY', 50.00),
    'global_daily'     => env('AI_BUDGET_GLOBAL_DAILY', 500.00),
],
```

Three tiers because they fail differently: a runaway loop for one user, a misconfigured integration for one tenant, a bug affecting everyone. The global cap is your last line of defence.

**Also set a hard spend limit at the provider.** Section 3.7 said it and it bears repeating: application-level budgets depend on your code being correct. The provider's cap does not.

### Key takeaways

- Log tokens, model, agent and duration on every run.
- Three levers: fewer iterations, smaller context, cheaper model per step.
- Cache deterministic tasks and embeddings; not conversations.
- Three budget tiers plus a hard cap at the provider.

## 23.2 Resilience

### Rate limiting

Providers enforce theirs; you should enforce yours first, so you get a queued job rather than a failed request:

```php
class RunAgent implements ShouldQueue
{
    public function middleware(): array
    {
        return [
            (new RateLimited('anthropic'))->dontRelease(),
        ];
    }
}
```

```php
// AppServiceProvider::boot()
RateLimiter::for('anthropic', fn () => Limit::perMinute(50));
```

### Timeouts

Every provider talks HTTP through NeuronAI's own client abstraction, and the default is `CurlHttpClient`, which needs nothing but ext-curl — Guzzle is not a dependency. Its default timeout is **300 seconds** per request. Set yours deliberately, where the provider is built:

```php
protected function provider(): AIProviderInterface
{
    return new Anthropic(
        key: config('neuron.provider.anthropic.key'),
        model: config('neuron.provider.anthropic.model'),
        httpClient: new CurlHttpClient(timeout: 60.0, connectTimeout: 5.0),
    );
}
```

An agent making five calls at the default timeout can hang for twenty-five minutes before failing, occupying a worker the whole time.

Pass the client to the constructor rather than calling `setHttpClient()` afterwards: the provider configures its base URL and authentication headers on the client it is constructed with, and a client swapped in later arrives without them. If you need Guzzle middleware — a retry handler, a proxy, request signing — `GuzzleHttpClient` is available as an opt-in adapter once you require `guzzlehttp/guzzle` yourself, and `CurlHttpClient` accepts raw `curlOptions` for proxies and CA bundles.

### Retries, with the caveat

```php
class RunAgent implements ShouldQueue
{
    public int $tries = 3;
    public array $backoff = [10, 60, 180];

    public function retryUntil(): DateTime
    {
        return now()->addMinutes(15);
    }
}
```

**The caveat matters more than the configuration.** Retrying an agent run re-spends money and, because of non-determinism, may produce a different result. Retry the *transport* failure, not the *reasoning*.

The distinction in practice:

- Rate limit or connection error before any work → safe to retry
- Failure after three tool calls including a write → **do not blind-retry**; you may duplicate the write

This is why Section 21.5 set `$tries = 1` on the workflow job. For agent work, idempotency (19.2) plus deliberate retry beats a generous retry count.

### Provider fallback

The interface architecture's most concrete payoff:

```php
class ResilientProviderFactory
{
    private const CHAIN = ['anthropic', 'openai', 'gemini'];

    public function make(): AIProviderInterface
    {
        foreach (self::CHAIN as $driver) {
            if (! $this->circuitOpen($driver)) {
                return AIProvider::driver($driver);
            }
        }

        throw new NoProviderAvailable('All configured providers are unavailable.');
    }

    private function circuitOpen(string $driver): bool
    {
        return Cache::get("circuit:{$driver}", 0) >= 5;
    }

    public function recordFailure(string $driver): void
    {
        Cache::increment("circuit:{$driver}");
        Cache::put("circuit:{$driver}:reset", true, now()->addMinutes(5));
    }
}
```

**Two caveats, so this does not look like a free lunch:**

**Quality varies across providers.** A prompt tuned for one model may perform noticeably worse on another. Fallback keeps you available; it does not keep you equally good. Run your evals (Chapter 10) against every provider in the chain so you know what you are degrading to.

**Some features are not portable.** Provider tools (5.12) simply vanish. If an agent depends on one, it has no fallback.

### Degrading gracefully

Sometimes the right answer is not another provider:

```php
try {
    return $this->agent->chat(new UserMessage($question))->getMessage()?->getContent() ?? '';
} catch (\Throwable $e) {
    \Log::error('Agent unavailable', ['exception' => $e]);

    return $this->fallbackSearch($question);   // plain keyword search over the KB
}
```

A keyword search result beats an error page. Users notice outages; they rarely notice a slightly worse answer.

### Key takeaways

- Rate limit before the provider does; queue rather than fail.
- Retry transport failures, not reasoning — writes may duplicate.
- Fallback chains keep you available, not equally good; eval every provider in the chain.
- Degrade to non-AI functionality rather than to an error page.

## 23.3 Observability in Production

### Inspector, with the Laravel package

```bash
composer require inspector-apm/inspector-laravel
```

```dotenv
INSPECTOR_INGESTION_KEY=...
```

That monitors your HTTP requests and jobs — and no agent. NeuronAI does not depend on Inspector and attaches nothing by default; older tutorials that stop at the environment variable describe a setup that no longer exists. Section 10.2 covers the mechanism. In Laravel, subscribe the listener where agents are built, and hand it the Inspector instance the Laravel package already owns:

```php
use Inspector\Neuron\V4\InspectorSubscriber;
use NeuronAI\Observability\ObservabilityEvent;

$agent->subscribe(ObservabilityEvent::class, new InspectorSubscriber(app('inspector')));
```

Passing the host's instance is the point of the Laravel package. The agent's segments land inside the transaction Inspector already opened for the request or the queue job, which correlates the agent trace with the queries, HTTP calls and job around it — what you actually want when diagnosing an incident. Without it you have an agent timeline floating unattached to the request that produced it.

Queue workers need nothing extra. The subscriber flushes at the end of a run only when it opened the transaction itself, and leaves a transaction owned by the host — a job monitored by the Laravel package — for the host to close. The Laravel package accepts older versions of `inspector-apm/inspector-php` than the subscriber needs: check that Composer resolved 3.18.1 or later, the first to ship the `Inspector\Neuron\V4` namespace, and require it explicitly if not.

The failure mode to watch for is an agent nobody subscribed: it produces no error and no trace at all, and a worker is exactly where nobody notices. Subscribe in the factory or the container binding (Section 18.1), never at call sites.

### What to alert on

Four signals, and none of them are "an exception occurred":

**Tool run limits exceeded.** Section 5.9 said this is a diagnostic about tool design. A spike means a description has stopped working — often because the underlying data changed shape.

**Faithfulness score dropping.** From your eval suite (10.5), running nightly. A drop means retrieval quality has degraded, usually because content changed and the index did not keep up.

**Cost per request rising.** Loops getting longer, context growing, or a prompt change that made the model chattier.

**Approval backlog growing.** Not a code problem — a process problem, and one your dashboard will surface before anyone complains.

### What to log, and what not to

**Log:** agent class, provider, model, token counts, duration, tool names, tool argument *shapes*, outcome, workflow ID, user and tenant IDs.

**Do not log by default:** full prompts, full responses, tool argument *values*, retrieved document contents.

Section 3.7 made this point; it deserves restating here. Prompts contain whatever users typed — names, addresses, order numbers, occasionally payment details. Full-prompt logging at scale creates a compliance problem that is much harder to unwind than to avoid.

When you do need content for debugging, put it behind an explicit flag with short retention, and never on by default.

### The correlation ID

```php
Log::withContext([
    'workflow_id' => $this->workflowId,
    'tenant_id'   => $this->tenantId,
    'agent'       => static::class,
]);
```

An agentic request touches an HTTP request, several queue jobs, several provider calls and possibly a human decision days later. Without a correlation ID, reconstructing what happened means guessing from timestamps.

### Key takeaways

- Require `inspector-laravel` and subscribe `InspectorSubscriber` on every agent — nothing is monitored by default.
- Pass the Laravel package's Inspector instance so agent segments join the request or job transaction.
- Alert on run limits, faithfulness, cost per request and approval backlog.
- Log shapes and metadata; not prompt content.
- Correlate everything by workflow ID.

## 23.4 Testing and CI

### The three tiers

**Tier 1 — Unit tests. Fast, free, deterministic, run on every commit.**

Tools are ordinary callable objects (Section 5.3):

```php
public function test_it_scopes_orders_to_the_tenant(): void
{
    $tool = new SearchOrdersTool($this->tenantA);

    Order::factory()->for($this->tenantB)->create(['number' => 'B-001']);

    $result = $tool(status: 'shipped');

    $this->assertStringNotContainsString('B-001', $result);
}
```

No LLM. No network. This is where most of your agent-related logic should live, and the reason Section 5.3 argued for tool classes.

**Tier 2 — Integration tests with a fake provider.**

```php
$provider = new FakeAIProvider(new AssistantMessage('Your order ships tomorrow.'));

$this->app->resolving(SupportAgent::class, fn (SupportAgent $agent) => $agent->setAiProvider($provider));

$this->postJson('/api/chat', ['message' => 'Where is my order?'])
     ->assertOk()
     ->assertJsonStructure(['answer']);

$provider->assertCallCount(1);
```

Tests your controller, your validation, your authorisation, your serialisation — and the real agent, with its real instructions and tools. Only the model is replaced.

`FakeAIProvider` implements the same interface as a real provider: queue the responses it should return, including tool-call messages to drive the agent's loop, and assert on what it was sent with `assertSent()`. The framework ships the same pattern for the other seams — `FakeEmbeddingsProvider`, `FakeVectorStore`, `FakeChannel` for streamed output — so a RAG endpoint or a queued stream can be tested the same way.

**Tier 3 — Evals. Slow, costs money, measures quality (Chapter 10).**

```bash
vendor/bin/neuron evaluation --path=evaluators
```

### CI configuration

```yaml
jobs:
  test:
    steps:
      - run: composer install --prefer-dist --no-progress
      - run: vendor/bin/phpunit --testsuite=unit,integration
      - run: vendor/bin/phpstan analyse

  evals:
    if: github.event_name == 'schedule' || contains(github.event.head_commit.message, '[evals]')
    steps:
      - run: vendor/bin/neuron evaluation --path=evaluators --concurrency=5
        env:
          ANTHROPIC_KEY: ${{ secrets.ANTHROPIC_KEY }}
```

Three rules from Section 10.6, restated because they are easy to get wrong:

**Do not gate every PR on the full eval suite.** It costs money and it is slow. Nightly, plus opt-in with a commit tag.

**Do not fail on a single item.** Set a success-rate threshold. On a probabilistic system a 95 % pass rate is a healthy build, and treating one flaky item as failure teaches the team to ignore the signal entirely.

**Keep API keys out of forks.** Eval-on-PR in a public repository is a way to donate your budget to strangers.

### The security tests that must gate deploys

Two from Part V, both deterministic enough to trust:

```php
public function test_tenant_isolation(): void;                   // Section 18.3
public function test_restricted_articles_never_surface(): void;  // Section 20.3
```

These belong in tier 1 or 2, run on every commit, and block the merge. They are among the few AI-adjacent tests that are both reliable and consequential.

### Key takeaways

- Three tiers: unit (every commit), integration with fakes (every commit), evals (nightly).
- Tools are testable without an LLM — put logic there.
- Threshold on success rate, not pass/fail per item.
- Tenant isolation and permission-filtered retrieval gate every deploy.

## 23.5 Security and Privacy

### The layered model, assembled

| Layer | Mechanism | Section |
|---|---|---|
| Capability | Only register tools this user may use | 5.1 |
| Visibility | `visible()` from policies | 5.10, 19.3 |
| Authorisation | `Gate::forUser()` inside the tool | 19.3 |
| Approval | `approvalPolicy()` / `requireApproval()` on consequential tools | 15.5, 22.5 |
| Data scope | Tenant filters on tools and retrieval | 18.3, 20.3 |
| Privilege | Read-only database credentials | 19.3 |
| Audit | A row per consequential tool call | 19.3 |

**Every layer is independent.** A bug in one does not defeat the others — which is the whole point of defence in depth, and the answer to "isn't visibility enough?".

### Prompt injection, one more time

The principle from Section 19.3, which is the security thesis of this entire book:

> Do not try to instruct the model out of doing something it has the capability to do. Remove the capability.

Instructions compete with injected text and sometimes lose. An absent tool cannot be invoked by any prompt, however clever.

Untrusted text enters from more places than people expect: user messages, product descriptions, support tickets, uploaded documents, RAG-retrieved content, third-party API responses, and MCP tool output (9.4). Treat all of it as attacker-influenced.

### Data flow

Three questions to answer in writing before launch:

**What leaves your infrastructure?** Every prompt goes to the provider. That includes retrieved documents and tool results. If a customer's address appears in a tool result, it went to the provider.

**Where does it go?** Provider regions differ, and some offer EU-only or in-region processing. For EU customers this is often a contractual requirement rather than a preference.

**What is retained?** Providers publish retention policies; enterprise agreements often include zero-retention options. Read them and record what you found.

### GDPR touchpoints

Five practical ones, stated as engineering requirements:

**Legal basis.** Sending personal data to a third-party processor needs one. That is a legal determination, not an engineering one — get counsel involved rather than deciding it in sprint planning.

**Data processing agreement.** With each provider you use.

**Right to erasure.** A user asks to be deleted. Their chat history is in your `chat_messages` table — deletable. Their data inside a provider's logs is subject to that provider's retention policy, which is why zero-retention matters.

**Right of access.** Chat history and any long-term memory (Section 4.5) are personal data the user can request.

**Automated decision-making.** If an agent makes a decision with legal or similarly significant effect on someone, GDPR Article 22 is relevant. This is a strong argument for human-in-the-loop on consequential actions — Chapter 15 is a compliance feature as well as a safety one.

None of this is legal advice; it is the list of questions to bring to someone who gives it.

### The audit trail

```php
Schema::create('agent_actions', function (Blueprint $table) {
    $table->id();
    $table->foreignId('user_id')->nullable()->constrained();
    $table->foreignId('tenant_id')->constrained();
    $table->string('agent');
    $table->string('tool');
    $table->json('arguments');
    $table->text('result')->nullable();
    $table->string('workflow_id')->nullable();
    $table->boolean('approved')->default(false);
    $table->foreignId('approved_by')->nullable()->constrained('users');
    $table->timestamps();
});
```

Answers the question that arrives eventually: *"why did the system refund that customer?"*

Without it you have logs, a trace that may have expired, and a shrug. With it you have a row naming the user, the tool, the arguments, the approver and the time. In a regulated environment this is the difference between deployable and not.

### Key takeaways

- Seven independent layers; a bug in one does not defeat the rest.
- Remove capability rather than instructing against it.
- Write down what leaves, where it goes, and what is retained.
- Human-in-the-loop is a compliance feature under Article 22, not just a safety one.
- Audit every consequential action to a queryable table.

## 23.6 The Deployment Checklist

### Configuration

- [ ] Model versions **pinned explicitly**, not floating aliases (1.5)
- [ ] Provider set per environment; embeddings model **identical everywhere** (12.4, 17.2)
- [ ] Context window derived from the configured provider, not hardcoded (4.4)
- [ ] Hard spend limit set at the provider (3.7)
- [ ] Separate API keys per environment
- [ ] Secret scanning in CI

### Agents and tools

- [ ] Every write tool: `setMaxRuns(1)`, idempotency guard, transaction (5.9, 19.2)
- [ ] Every tool: bounded result set, explicit column selection, compact output (19.1)
- [ ] Every tool: an explicit sentence for the empty case (5.9)
- [ ] Tool visibility computed from the actor's policies (5.10, 19.3)
- [ ] `Gate::forUser()` inside tools that touch specific records (19.3)
- [ ] Error handler returning instructions, not stack traces (5.11)
- [ ] Toolkits filtered with `only()`, never `exclude()` (5.8)

### Data

- [ ] Tenant filter applied inside `vectorStore()`, not at the call site (20.1)
- [ ] Permission filters applied **at retrieval**, never after (20.3)
- [ ] `sourceName` stable — record IDs, never titles (12.6, 20.2)
- [ ] `indexed_at` tracked; a gap alert configured (20.2)
- [ ] Read-only database credentials for agent queries (19.3)

### Workflows

- [ ] `EloquentPersistence(WorkflowStore::class)` — or the database or Redis backend — for anything interruptible, including approving agents (18.4, 22.5)
- [ ] Every pre-interrupt LLM call wrapped in `memoize()` (15.5)
- [ ] Resume jobs fenced with `expectedRunId` and `expectedExecutionAttempt` (22.3)
- [ ] `lockForUpdate()` on approval resolution (22.3)
- [ ] `expiresAt` on the request; inputless resume scheduled (22.4)
- [ ] Lease timeout above the longest silent step (22.4)
- [ ] Interrupt requests small, flat and versioned; new properties declared with defaults (22.4)
- [ ] Stale runs abandoned through `abandonRun()`, never deleted by hand (22.4)

### Operations

- [ ] `InspectorSubscriber` subscribed on every agent and workflow, in the factory (10.2, 23.3)
- [ ] Token usage logged per run (23.1)
- [ ] Budgets: per user, per tenant, global (23.1)
- [ ] Rate limits configured before the provider's (23.2)
- [ ] `$tries = 1` on agent jobs, or idempotency proven (21.5, 23.2)
- [ ] Timeouts set at PHP, FPM, proxy and the provider's HTTP client (21.2, 23.2)
- [ ] Streaming verified end to end with `curl -N` through the full stack (21.2)
- [ ] Broadcast channels authorised by tenant; the browser subscribes before the run starts (21.5)

### Quality and safety

- [ ] Eval suite with a dataset built from real questions (10.4)
- [ ] `FaithfulnessJudge` on every RAG agent (10.5)
- [ ] Tenant isolation test gating deploys (18.3)
- [ ] Permission-filtered retrieval test gating deploys (20.3)
- [ ] Audit table populated by every consequential tool (19.3, 23.5)
- [ ] Prompt content **not** logged by default (3.7, 23.3)
- [ ] Data processing agreements in place; retention understood (23.5)

### The five questions to answer out loud

Before launch, be able to answer these without looking anything up:

1. **What does this agent cost per request, and at what volume does that become a problem?**
2. **What is the worst thing it can do, and what stops it?**
3. **How would I find out what it did, three weeks from now?**
4. **What happens when the provider is down?**
5. **What data leaves my infrastructure, and where does it go?**

If any answer is a shrug, that is the next piece of work.

### Closing Part V

Twenty-three chapters ago the first one drew a four-rung ladder and asked *who decides what happens next*. Everything since has been the machinery required to let a model answer that question safely: tools to give it hands, structure to make its output usable, retrieval to give it knowledge, workflows to give it shape, interruption to keep a human in the decision, and observability to find out what it actually did.

The second question on that list is the one to leave with:

> **What is the worst thing your agent can do, and what stops it?**

If you can answer that about a system you built, you have understood this book.

### Key takeaways

- Work the checklist section by section; every item traces back to a chapter.
- The five questions are the real exam.
- If an answer is a shrug, that is the next task.
