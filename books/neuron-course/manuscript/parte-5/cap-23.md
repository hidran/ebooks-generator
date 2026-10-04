# Chapter 23 — Production

::: {.callout .callout-tip}
[Code for this chapter]{.callout-title}

Most of this chapter is configuration and checklist, but the usage listener of Section 23.1 is runnable without Laravel at [`chapters/Ch23`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch23) in the companion repository: `usage.php` records the token counts of two inferences from a fake provider, with no model and no API key.
:::

## 23.1 Cost Control

### Measure first

You cannot manage what you do not record. Record usage on every inference:

```php
use NeuronAI\Agent\Agent;
use NeuronAI\Agent\Observability\InferenceStop;

class RecordUsage
{
    public function __construct(
        private readonly Agent $agent,
    ) {}

    public function __invoke(InferenceStop $event): void
    {
        $usage = $event->response->message()->getUsage();

        if ($usage === null) {
            return;   // the provider reported none
        }

        try {
            $scope = ThreadScope::of($event->execution?->workflowId);

            AiUsage::create([
                'tenant_id'     => $scope->tenantId,
                'user_id'       => $scope->userId,
                'agent'         => $this->agent::class,
                'model'         => $this->agent->getProvider()->getModel(),
                'input_tokens'  => $usage->inputTokens,
                'output_tokens' => $usage->outputTokens,
                'cached_tokens' => $usage->cachedInputTokens,
            ]);
        } catch (\Throwable $e) {
            report($e);   // a lost row must not become a failed turn
        }
    }
}
```

```php
// NeuronServiceProvider::register()
$this->app->afterResolving(Agent::class, function (Agent $agent): void {
    $agent->subscribe(InferenceStop::class, new RecordUsage($agent));
});
```

Observability in NeuronAI is a PSR-14 event dispatcher owned by each agent instance (Section 10.2), and `InferenceStop` fires after every model call — so this writes one row per inference, not per request. An agent that loops through three tool calls produces four rows, which is exactly the granularity that makes a looping agent visible. Two details are easy to get wrong: the token counts are on the *provider response's* message, `$event->response->message()->getUsage()` — `$event->message` is the last message *sent* — and `getUsage()` returns `null` when a provider reports nothing, so guard for it.

The listener is told nothing about the caller. The event carries the thread the run is bound to, and the thread names the tenant and the user (Section 18.3) — the route the audit listener of Section 19.3 takes. The model is asked of the agent when the event fires, not when the listener is built: once the fallback factory of Section 23.2 can swap providers, a model name captured at subscription is a guess. And the write sits inside a `try`. `InferenceStop` is dispatched from within the run, so an exception thrown by a listener fails the turn; a usage table that is down should cost you a row, not an answer.

Subscribe it where agents are built, so no agent escapes it. Chapter 18's agents are built by the container, and an `afterResolving()` callback in `NeuronServiceProvider` runs for every `Agent` subclass the container resolves; the copy that `for()` makes keeps the listener. An agent constructed by hand with `::make()` never passes through the container, and is not recorded.

Keep `cached_tokens` even if you ignore it today. Prompt caching bills those tokens at a fraction of the normal rate, and NeuronAI reports them the same way for every provider: `inputTokens` is the whole prompt, and `cachedInputTokens` is the part of it that was read from the cache. Price all of `input_tokens` at the full rate and you overstate every cache hit; add `cached_tokens` on top and you count them twice. Price the row when it is written, so that a later change of price does not rewrite history:

```php
class AiUsage extends Model
{
    // ...

    protected static function booted(): void
    {
        static::creating(function (AiUsage $usage): void {
            // Your own price table in config/neuron.php, per million tokens
            $rate = config("neuron.prices.{$usage->model}")
                ?? throw new LogicException("No price configured for {$usage->model}.");

            $usage->cost = (
                ($usage->input_tokens - $usage->cached_tokens) * $rate['input']
                + $usage->cached_tokens * $rate['cached']
                + $usage->output_tokens * $rate['output']
            ) / 1_000_000;
        });
    }
}
```

A model with no price throws, the listener reports it, and you learn that a fallback provider has been answering unpriced before the invoice tells you.

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
        $key = 'classify:' . \hash('xxh128', $text);

        return Cache::remember(
            $key,
            now()->addDays(7),
            fn () => ClassifierAgent::make(workflowId: $key)
                ->structured(new UserMessage($text), Classification::class)
                ->label
        );
    }
}
```

The cache key doubles as the agent's thread: an agent does not run without one, and a classification has no conversation to belong to.

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

A config array stops nothing. The budget is the code that reads what has been spent and refuses the next turn:

```php
class Budget
{
    /** Call it before a turn starts: a refusal here stores nothing and spends nothing. */
    public function check(ThreadScope $scope): void
    {
        $today = AiUsage::query()->whereDate('created_at', today());

        $spent = [
            'per_user_daily'   => (clone $today)->where('user_id', $scope->userId)->sum('cost'),
            'per_tenant_daily' => (clone $today)->where('tenant_id', $scope->tenantId)->sum('cost'),
            'global_daily'     => (clone $today)->sum('cost'),
        ];

        foreach (config('neuron.budgets') as $tier => $limit) {
            abort_if($spent[$tier] >= $limit, 429, 'The daily AI budget is used up.');
        }
    }
}
```

Call it where a turn starts, before the agent is bound — `$budget->check(ThreadScope::of($conversation->threadId()))` — and the browser gets a 429 with no question stored and no token spent. What a check before the turn cannot do is stop a loop inside a turn that is already running: the run limits of Section 5.9 bound that one.

**Also set a hard spend limit at the provider.** Section 3.7 said it and it bears repeating: application-level budgets depend on your code being correct. The provider's cap does not.

### Key takeaways

- Record tokens, model and agent on every inference, and price the row when you write it.
- Three levers: fewer iterations, smaller context, cheaper model per step.
- Cache deterministic tasks and embeddings; not conversations.
- Three budget tiers, checked before every turn, plus a hard cap at the provider.

## 23.2 Resilience

### Rate limiting

Providers enforce theirs; you should enforce yours first, so you get a queued job rather than a failed request:

```php
class RunAgent implements ShouldQueue
{
    public function middleware(): array
    {
        return [new RateLimited('anthropic')];
    }
}
```

```php
// AppServiceProvider::boot()
RateLimiter::for('anthropic', fn () => Limit::perMinute(50));
```

Over the limit, the middleware releases the job back onto the queue until the window reopens: the turn is late, not lost. Do not chain `->dontRelease()` onto it. With that flag a limited job is not held back but dropped — Laravel deletes it without running it and without an error, and the user's turn is gone. A release has one cost, which the retry settings below have to allow for: Laravel counts it as an attempt.

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

`timeout` limits the whole transfer, not the wait for the first byte, and it applies to a streamed response too: an answer still arriving after sixty seconds is cut off mid-sentence. Sixty seconds suits buffered calls. Give an agent that streams long answers a higher limit, and keep `connectTimeout` short — it is the one that notices a provider that is down.

Build the provider in the hook, as here, rather than calling `setHttpClient()` on what `AIProvider::driver()` returns: the manager hands every agent the same provider object (Section 17.6), so a client set on it changes the timeout for all of them. If you need Guzzle middleware — a retry handler, a proxy, request signing — `GuzzleHttpClient` is available as an opt-in adapter once you require `guzzlehttp/guzzle` yourself, and `CurlHttpClient` accepts raw `curlOptions` for proxies and CA bundles.

### Retries, with the caveat

```php
class RunAgent implements ShouldQueue
{
    use Queueable;

    public int $tries = 3;

    /** Longer than the longest turn, shorter than the queue's retry_after (360). */
    public int $timeout = 300;

    public array $backoff = [10, 60, 180];

    public function __construct(
        public string $threadId,
        public string $runId,
        public string $message,
    ) {}

    public function handle(SupportAgent $agent): void
    {
        $agent->for($this->threadId)->run(ExecutionRequest::start(
            new AgentStartEvent([new UserMessage($this->message)]),
            runId: $this->runId,
            recoverFailed: true,
        ));
    }
}
```

```php
RunAgent::dispatch($conversation->threadId(), (string) Str::uuid(), $request->input('message'));
```

**The caveat matters more than the configuration.** A retry that starts the turn again re-spends money and, because of non-determinism, may produce a different result. Retry the *transport* failure, not the *reasoning*.

The distinction in practice:

- Rate limit or connection error before any work → safe to retry
- Failure after three tool calls including a write → **do not blind-retry**; you may duplicate the write

The run ID is what makes a retry safe in both cases. The controller mints it when it dispatches, so every delivery of the job names the same run, and the job starts the turn with `ExecutionRequest::start()` because `chat()` cannot reserve an ID. The first delivery starts that run. A redelivery — after an exception, after a killed worker — finds it, and `recoverFailed: true` makes it finish the run from its last completed step instead of starting over: the question is not stored twice, an inference that was already paid for is not paid for again, and a tool that already ran does not run again. Only the step that was in flight is repeated, which is why a write tool still needs the idempotency key of Section 19.2.

Three clocks have to be in order for that to hold, and Laravel's defaults put one of them wrong:

- **The run's lease** — 600 seconds by default for an agent, `setLeaseTimeout()` — longer than the longest single step, one inference or one batch of tools. A live run is then never taken for a dead one.
- **The job's `$timeout`** — 300 — longer than the longest turn. Laravel kills a job that exceeds it; its run stays `running` until the lease expires, and a later delivery finishes it.
- **The queue's `retry_after`** — 360 — longer than `$timeout`. Laravel ships 90, and with that a second worker takes the job while the first is still answering: the turn runs twice. Set `DB_QUEUE_RETRY_AFTER=360` in `.env`, or `REDIS_QUEUE_RETRY_AFTER` on a Redis queue.

While a run is still leased to a worker that died, the engine refuses the start with `RunInFlightException`. A complete job catches it and releases itself until `$e->leaseExpiresAt` rather than spend an attempt on it; the maintainers' `neuron-laravel-integration` skill prints that handler under "Background Runs", and the queued runs of Chapters 21 and 22 follow the same pattern.

One interaction to know about: the rate limiter's releases come out of the same three attempts. Where the limit is tight enough to release a job more than once, count failures instead of deliveries — `retryUntil()` with `$maxExceptions = 3`, as the indexing jobs of Section 20.2 do — and drop `$tries`, which Laravel ignores as soon as a job defines `retryUntil()`.

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
        // add() writes only when the key is missing: the first failure opens a five-minute window
        Cache::add("circuit:{$driver}", 0, now()->addMinutes(5));
        Cache::increment("circuit:{$driver}");
    }
}
```

Five failures inside five minutes take a provider out of the chain, and when the counter expires it is tried again. The `add()` is what gives the counter that expiry. `increment()` alone never sets one: depending on the cache store, the counter then lives for ever, and a provider that failed five times stays excluded until someone clears the cache, or — on the `database` store a new Laravel application uses by default — it is never created at all, and the circuit never opens.

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

- Rate limit before the provider does; queue rather than fail, and never `dontRelease()`.
- Retry transport failures, not reasoning: a reserved run ID with `recoverFailed: true` lets a redelivery finish the turn instead of repeating it.
- Three clocks in order: lease above the longest step, `$timeout` above the longest turn, `retry_after` above `$timeout`.
- Fallback chains keep you available, not equally good; eval every provider in the chain.
- Degrade to non-AI functionality rather than to an error page.

## 23.3 Observability in Production

### Inspector, with the Laravel package

```bash
composer require inspector-apm/inspector-laravel "inspector-apm/inspector-php:^3.19"
```

```dotenv
INSPECTOR_INGESTION_KEY=...
```

That monitors your HTTP requests and jobs — and no agent. NeuronAI does not depend on Inspector and attaches nothing by default; older tutorials that stop at the environment variable describe a setup that no longer exists. Section 10.2 covers the mechanism, and the reason the command names a second package: the Laravel package accepts older releases of `inspector-apm/inspector-php` than the subscriber needs, and 3.18.1 to 3.18.3 ship a subscriber written for a pre-release namespace, which subscribes without complaint and records nothing. In Laravel, subscribe the listener where agents are built — the `afterResolving()` callback of Section 23.1 — and hand it the Inspector instance the Laravel package already owns:

```php
use Inspector\Neuron\V4\InspectorSubscriber;
use NeuronAI\Observability\ObservabilityEvent;

$agent->subscribe(ObservabilityEvent::class, new InspectorSubscriber(app('inspector')));
```

Passing the host's instance is the point of the Laravel package. The agent's segments land inside the transaction Inspector already opened for the request or the queue job, which correlates the agent trace with the queries, HTTP calls and job around it — what you actually want when diagnosing an incident. Without it you have an agent timeline floating unattached to the request that produced it.

Queue workers need nothing extra. The subscriber flushes at the end of a run only when it opened the transaction itself, and leaves a transaction owned by the host — a job monitored by the Laravel package — for the host to close.

The failure mode to watch for is an agent nobody subscribed: it produces no error and no trace at all, and a worker is exactly where nobody notices. Subscribe in the service provider, never at call sites.

Inspector is not the only backend. The maintainers' monitoring guide documents Neuron Cloud, which has a Laravel package of its own, `neuron-core/neuron-cloud-laravel`: the same kind of listener, subscribed in the same place. Section 10.2 says what to check before you plan on it.

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
Context::add([
    'workflow_id' => $this->workflowId,
    'tenant_id'   => $this->tenantId,
    'agent'       => static::class,
]);
```

An agentic request touches an HTTP request, several queue jobs, several provider calls and possibly a human decision days later. Without a correlation ID, reconstructing what happened means guessing from timestamps. Use `Context`, not `Log::withContext()`: Laravel writes context data into every log record and carries it into the jobs dispatched afterwards, whereas `withContext()` stays in the process that called it.

### Key takeaways

- Require `inspector-laravel` and `inspector-php` at `^3.19`, and subscribe `InspectorSubscriber` on every agent — nothing is monitored by default.
- Pass the Laravel package's Inspector instance so agent segments join the request or job transaction.
- Alert on run limits, faithfulness, cost per request and approval backlog.
- Log shapes and metadata; not prompt content.
- Correlate everything by workflow ID, in `Context` so that it follows the work into queued jobs.

## 23.4 Testing and CI

### The three tiers

**Tier 1 — Unit tests. Fast, free, deterministic, run on every commit.**

Tools are ordinary callable objects (Section 5.3):

```php
public function test_it_scopes_orders_to_the_tenant(): void
{
    Order::factory()->for($this->tenantA)->create(['number' => 'A-001', 'status' => 'shipped']);
    Order::factory()->for($this->tenantB)->create(['number' => 'B-001', 'status' => 'shipped']);

    $result = (string) (new SearchOrdersTool($this->tenantA->id))(status: 'shipped');

    $this->assertStringContainsString('A-001', $result);
    $this->assertStringNotContainsString('B-001', $result);
}
```

No LLM. No network. Both orders are `shipped`, so the status filter lets both through and only the tenant scope can keep `B-001` out; the first assertion proves the search found anything at all. A test that passes on an empty result protects nothing. This is where most of your agent-related logic should live, and the reason Section 5.3 argued for tool classes.

**Tier 2 — Integration tests with a fake provider.**

```php
$provider = new FakeAIProvider(new AssistantMessage('Your order ships tomorrow.'));

$this->app->instance(
    SupportAgent::class,
    $this->app->make(SupportAgent::class)->setAiProvider($provider),
);

$this->actingAs($user)
    ->postJson("/conversations/{$conversation->id}/messages", ['message' => 'Where is my order?'])
    ->assertOk();

$provider->assertCallCount(1);
```

Tests your controller, your validation, your authorisation, your serialisation — and the real agent, with its real instructions and tools. Only the model is replaced, through the seam of Section 18.1: the container hands out an agent whose provider is the fake, and the copy `for()` makes shares it.

`FakeAIProvider` implements the same interface as a real provider: queue the responses it should return, including tool-call messages to drive the agent's loop, and assert on what it was sent with `assertSent()`. The framework ships the same pattern for the other seams — `FakeEmbeddingsProvider`, `FakeVectorStore`, `FakeChannel` for streamed output — so a RAG endpoint or a queued stream can be tested the same way.

**Tier 3 — Evals. Slow, costs money, measures quality (Chapter 10).**

```bash
php artisan neuron:evaluate --env=evaluation
```

Not `vendor/bin/neuron evaluation`, the command of Chapter 10: it does not boot Laravel, so an evaluator that touches a model, a facade or the container fails on every item. `neuron:evaluate` is an Artisan command of your own that runs the same evaluation CLI inside the booted application, with the container building the evaluators. It is one short class, which the maintainers print in the `neuron-laravel-integration` skill (`references/evaluation.md`): create it with `php artisan make:command NeuronEvaluate` and replace the class. Evaluations run the real tools — approving a refund refunds that order — so they get a database of their own. `--env=evaluation` selects `.env.evaluation`, the command refuses to run when that file was not loaded, and a seeder rebuilds the data the datasets name before every run.

### CI configuration

```yaml
jobs:
  test:
    steps:
      - run: composer install --prefer-dist --no-progress
      - run: vendor/bin/phpunit --testsuite=Unit,Feature
      - run: vendor/bin/phpstan analyse

  evals:
    if: github.event_name == 'schedule' || contains(github.event.head_commit.message, '[evals]')
    steps:
      - run: php artisan migrate:fresh --seed --seeder=EvaluationSeeder --env=evaluation
      - run: |
          php artisan neuron:evaluate --env=evaluation --concurrency=5 || true
          php -r '$r = json_decode(file_get_contents("storage/logs/evaluation.json"), true, 512, JSON_THROW_ON_ERROR); exit($r["success_rate"] >= 0.95 ? 0 : 1);'
        env:
          ANTHROPIC_KEY: ${{ secrets.ANTHROPIC_KEY }}
```

Three rules from Section 10.6, restated because they are easy to get wrong:

**Do not gate every PR on the full eval suite.** It costs money and it is slow. Nightly, plus opt-in with a commit tag.

**Do not fail on a single item.** Set a success-rate threshold. On a probabilistic system a 95 % pass rate is a healthy build, and treating one flaky item as failure teaches the team to ignore the signal entirely. The command exits non-zero on any failed item and has no threshold flag, so the step ignores its exit code and reads `success_rate` from the JSON report, as Section 10.6 did; here `evaluation.php` writes that report to `storage/logs/evaluation.json`.

**Keep API keys out of forks.** Eval-on-PR in a public repository is a way to donate your budget to strangers.

### The security tests that must gate deploys

Two from Part V, both deterministic enough to trust:

```text
public function test_tenant_a_history_never_reaches_tenant_b(): void;      // Section 18.3
public function test_customer_cannot_retrieve_internal_articles(): void;   // Section 20.3
```

These belong in tier 1 or 2, run on every commit, and block the merge. Run them in the form that asserts on what reached the model, through a fake provider: no model is called, so the result is the same on every run. They are among the few AI-adjacent tests that are both reliable and consequential.

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

**Right to erasure.** A user asks to be deleted. Their chat history is in your `chat_messages` table — deletable, the archived rows included (Section 18.2). Two more places hold their words. A run paused for an approval keeps its serialised state — the question, the tool arguments, any retrieved text — in `workflow_store` until it is settled; `resetConversation()` on the bound agent discards that run together with the thread's history. Long-term memory (Section 4.5) lives in a store that `resetConversation()` does not touch, so delete those documents separately. Their data inside a provider's logs is subject to that provider's retention policy, which is why zero-retention matters.

**Right of access.** Chat history and any long-term memory (Section 4.5) are personal data the user can request.

**Automated decision-making.** If an agent makes a decision with legal or similarly significant effect on someone, GDPR Article 22 is relevant. This is a strong argument for human-in-the-loop on consequential actions — Chapter 15 is a compliance feature as well as a safety one.

None of this is legal advice; it is the list of questions to bring to someone who gives it.

### The audit trail

```php
Schema::create('agent_actions', function (Blueprint $table) {
    $table->id();
    $table->string('thread_id');
    $table->string('call_id');
    $table->foreignId('tenant_id')->constrained();
    $table->foreignId('user_id')->constrained();
    $table->string('tool');
    $table->json('arguments');
    $table->string('outcome');
    $table->text('result')->nullable();
    $table->foreignId('approved_by')->nullable()->constrained('users');
    $table->timestamps();
    $table->unique(['thread_id', 'call_id']);
});
```

Answers the question that arrives eventually: *"why did the system refund that customer?"*

This is the table the `ToolCalled` listener of Section 19.3 writes to, one row per tool call, keyed by the thread and the call ID so that a replayed call updates its row instead of adding one. Without it you have logs, a trace that may have expired, and a shrug. With it you have a row naming the user, the tool, the arguments, the outcome, the approver and the time. In a regulated environment this is the difference between deployable and not.

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

- [ ] Tenant filter returned by `retrievalScope()`, never added at the call site or replaced with `setRetrievalScope()` (20.1)
- [ ] Permission filters applied **at retrieval**, never after (20.3)
- [ ] `sourceName` stable — record IDs, never titles (12.6, 20.2)
- [ ] `indexed_at` tracked; a gap alert configured (20.2)
- [ ] Read-only database credentials for agent queries (19.3)
- [ ] Retention covers `workflow_store` as well as `chat_messages`: a suspended run keeps its serialised state there until it is settled (18.4, 23.5)

### Workflows

- [ ] `DatabasePersistence` — or `EloquentPersistence` over a table of your own, or the Redis backend — for anything interruptible, including approving agents (18.4, 22.5)
- [ ] Every pre-interrupt LLM call wrapped in `memoize()` (15.5)
- [ ] Resume jobs fenced with `expectedRunId` and `expectedExecutionAttempt` (22.3)
- [ ] `lockForUpdate()` on approval resolution (22.3)
- [ ] `expiresAt` on the request; inputless resume scheduled (22.4)
- [ ] Lease timeout above the longest silent step (22.4)
- [ ] Interrupt requests small, flat and versioned; new properties declared with defaults (22.4)
- [ ] Stale workflow runs discarded with `abandon()`, never deleted by hand; a dead agent run is finished, not abandoned (18.4, 22.4)
- [ ] Every endpoint that starts a turn calls `recoverFailedTurn()` first (18.4)

### Operations

- [ ] `InspectorSubscriber` subscribed on every agent and workflow, where they are built (10.2, 23.3)
- [ ] Token usage recorded per inference (23.1)
- [ ] Budgets: per user, per tenant, global, checked before every turn (23.1)
- [ ] Rate limits configured before the provider's (23.2)
- [ ] Queued turns start a reserved run with `recoverFailed: true`, so a redelivery finishes the turn instead of repeating it (23.2)
- [ ] Three clocks in order: lease above the longest step, job `$timeout` above the longest turn, queue `retry_after` above `$timeout` — Laravel ships 90 (23.2)
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

Twenty-two chapters ago the first one drew a four-rung ladder and asked *who decides what happens next*. Everything since has been the machinery required to let a model answer that question safely: tools to give it hands, structure to make its output usable, retrieval to give it knowledge, workflows to give it shape, interruption to keep a human in the decision, and observability to find out what it actually did.

The second question on that list is the one to leave with:

> **What is the worst thing your agent can do, and what stops it?**

If you can answer that about a system you built, you have understood this book.

### Key takeaways

- Work the checklist section by section; every item traces back to a chapter.
- The five questions are the real exam.
- If an answer is a shrug, that is the next task.
