# Chapter 18 — Agents as First-Class Citizens

::: {.callout .callout-tip}
[Code for this chapter]{.callout-title}

This chapter is conceptual and has no standalone code, but the companion repository at [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) holds runnable versions of everything the book builds.
:::

## 18.1 Agents in the Container

### The problem with `::make()` everywhere

```php
class SupportController extends Controller
{
    public function ask(Request $request)
    {
        return SupportAgent::make()
            ->chat(new UserMessage($request->input('message')))
            ->getMessage()
            ?->getContent();
    }
}
```

Works. But the controller now constructs the agent, which means you cannot swap it in tests, cannot vary it per tenant, and cannot configure it in one place.

### Constructor injection

```php
class SupportAgent extends Agent
{
    public function __construct(
        private readonly OrderRepository $orders,
        private readonly User $user,
    ) {
        parent::__construct();
    }

    protected function provider(): AIProviderInterface
    {
        return AIProvider::driver();
    }

    protected function tools(): array
    {
        return [
            new SearchOrdersTool($this->orders),
            new GetOrderStatusTool($this->orders),
        ];
    }
}
```

Remember `parent::__construct()` (Section 4.3) and that a custom constructor means `new`, not `::make()`. `make()` forwards its arguments to the constructor, so once you own the constructor, `make(threadId: ...)` no longer reaches the parent — Section 18.3 shows how to pass the thread through yourself.

### Binding

```php
// AppServiceProvider::register()

$this->app->bind(SupportAgent::class, function ($app) {
    return new SupportAgent(
        orders: $app->make(OrderRepository::class),
        user: $app->make('auth')->user(),
    );
});
```

```php
class SupportController extends Controller
{
    public function __construct(
        private readonly SupportAgent $agent,
    ) {}

    public function ask(Request $request)
    {
        return $this->agent
            ->chat(new UserMessage($request->input('message')))
            ->getMessage()
            ?->getContent();
    }
}
```

The controller asks for an agent and gets one, correctly configured for the current user.

### Why this is worth the ceremony

**Testability.** Swap the binding in a test and the controller talks to a fake. This is the Section 1.5 problem — you cannot assert on model output, so the boundary you *can* test is the controller's handling of an agent, and dependency injection is what makes that boundary exist.

```php
$this->app->bind(SupportAgent::class, fn () => new FakeSupportAgent());

$this->post('/support/ask', ['message' => 'Where is my order?'])
     ->assertOk();
```

**Per-user configuration.** The binding resolves the current user, so tool visibility (Section 5.10) is computed per request without the controller knowing.

**One place to change.** Provider, tools, history, instructions — all decided in the binding.

**It reads like Laravel.** Which matters for adoption. An agent that arrives by injection is a service like any other, and a team already knows how to reason about services.

### Scoped bindings

For long-running runtimes:

```php
$this->app->scoped(SupportAgent::class, function ($app) {
    return new SupportAgent(/* ... */);
});
```

`scoped()` gives one instance per request and resets between requests under Octane.

::: {.callout .callout-warning}
[Never `singleton()` an agent that holds user context]{.callout-title}

Under Octane that instance persists across requests, and user B inherits user A's tools and history. It is the same class of bug the facade's copy semantics prevent in Section 17.5 — except here it is your responsibility, and it will not appear at all under PHP-FPM.
:::

### Key takeaways

- Constructor injection, then bind in a service provider.
- Testability, per-user configuration, single point of change.
- `scoped()` not `singleton()` for anything holding user context.

## 18.2 EloquentChatHistory

### Publish and migrate

```bash
php artisan vendor:publish --tag=neuron-migrations
php artisan migrate --path=/database/migrations/neuron
```

The migrations land in `database/migrations/neuron` — a subfolder, which is why the `--path` flag is needed. Run both commands together; the second is easy to forget and the failure is silent.

There are three of them in 2.x: the `chat_messages` table, an `archived_at` column added to it, and the `workflow_store` table that Section 18.4 uses. If you published the 1.x migration before, publish again — the other two are new.

### Use it

```php
namespace App\Neuron;

use NeuronAI\Agent\Agent;
use NeuronAI\Chat\History\ChatHistoryInterface;
use NeuronAI\Chat\History\EloquentChatHistory;
use NeuronAI\Laravel\Models\ChatMessage;

class MyAgent extends Agent
{
    protected function chatHistory(): ChatHistoryInterface
    {
        return new EloquentChatHistory(
            modelClass: ChatMessage::class,
            contextWindow: 100000,
        );
    }
}
```

```php
MyAgent::make(threadId: 'THREAD_ID')->chat(new UserMessage('Hello'));
```

`NeuronAI\Laravel\Models\ChatMessage` ships with the package.

Notice what the history does *not* receive: the thread. In v4 the thread belongs to the agent. You declare it once, with `make(threadId: ...)`, and the agent binds it into whatever history `chatHistory()` returns before the first read. The history is constructed without an identity, and the framework never invents one.

The thread is more than a history key. It is also the agent's **workflow ID** — the name under which a paused run is persisted and later found again (Section 18.4). One identifier, declared in one place, names both the conversation and the run.

You *can* still pre-bind a history — `new EloquentChatHistory(ChatMessage::class, 'THREAD_ID')` — and the agent adopts that key. But a key that only appears when the hook runs arrives after the run has started, too late for the run to be findable by its thread. Declare the thread on the agent.

::: {.callout .callout-warning}
[Spelling]{.callout-title}

The documentation writes `ElquentChatHistory` in prose and anchors the section at `#eloquentchathisotry`. The class is `EloquentChatHistory`. Appendix A, item 42 — harmless once you know, and a wasted twenty minutes if you are searching for the misspelling.
:::

### Making thread_id real

`'THREAD_ID'` is a placeholder. In practice it is the isolation boundary, and getting it wrong is a data leak:

```php
class SupportAgent extends Agent
{
    protected function chatHistory(): ChatHistoryInterface
    {
        return new EloquentChatHistory(
            modelClass: ChatMessage::class,
            contextWindow: ProviderContext::window(),
        );
    }
}
```

```php
$this->app->bind(SupportAgent::class, function ($app) {
    $conversation = $app->make(ConversationResolver::class)->current();

    return SupportAgent::make(threadId: "conv:{$conversation->id}");
});
```

The agent needs no constructor of its own: `make(threadId:)` is the framework's front door for identity, and the binding is the one place that decides it.

**Never derive the thread ID from user input.** A request parameter that becomes a thread ID means anyone can read anyone's conversation by changing a number. Derive it server-side from an authenticated, authorised resource.

It is the single most likely security mistake in this chapter.

### The context window, per provider

Section 4.4 said derive it from the model, never hardcode it project-wide. In Laravel:

```php
// config/neuron.php
'context_windows' => [
    'anthropic' => 185_000,
    'openai'    => 118_000,
    'gemini'    => 920_000,
    'ollama'    => 29_000,
],
```

```php
contextWindow: config('neuron.context_windows.' . config('neuron.provider.default'), 29_000),
```

Change provider by environment and the trimmer follows. Hardcode 100,000 and someone running Ollama locally will hit context errors that never appear in production.

### Extending the model

The package's `ChatMessage` is a starting point. A real application usually wants:

- A foreign key to `users`
- Soft deletes for retention policy
- An index on `thread_id` plus a timestamp
- A tenant column

Extend the model and pass your class as `modelClass`. This is also where GDPR lives: conversations contain whatever users typed, which in a support context means personal data. Deletion, export and retention are product requirements, not afterthoughts — Section 3.7's logging warning, made concrete.

One v4 behaviour changes the retention arithmetic. When the history trims messages out of the context window, it no longer deletes them: it stamps them with `archived_at` and loads only the unarchived rows. The model sees the trimmed thread; your table keeps the full transcript. That is good for auditing and for the export below, but it means "the agent forgot it" and "we no longer store it" are now different statements. Your retention job has to delete archived rows explicitly.

### Key takeaways

- Publish and migrate with `--path=/database/migrations/neuron` — three migrations in 2.x.
- Declare the thread on the agent (`make(threadId:)`); construct the history without one.
- The thread ID is the isolation boundary — derive it server-side, never from input.
- Derive `contextWindow` from the configured provider.
- Extend `ChatMessage` for foreign keys, tenancy and retention; trimmed rows are archived, not deleted.

## 18.3 Multi-Tenant Isolation

### The four leak points

An agentic system in a multi-tenant application has four places tenant data can cross:

1. **Chat history** — `thread_id`
2. **Vector store** — the retrieval scope (Section 12.6)
3. **Tools** — the data they query
4. **Workflow persistence** — the workflow ID

Miss any one and you have a breach. Keep the list somewhere you will see it during code review.

For an agent, v4 fuses the first and the last: the thread ID *is* the workflow ID. Get the thread right and the persisted run is scoped with it; get it wrong and both leak together.

### A tenant-aware agent

```php
namespace App\Neuron\Agents;

use App\Models\Tenant;
use NeuronAI\Agent\Agent;
use NeuronAI\Chat\History\ChatHistoryInterface;
use NeuronAI\Chat\History\EloquentChatHistory;
use NeuronAI\Laravel\Facades\AIProvider;
use NeuronAI\Laravel\Models\ChatMessage;
use NeuronAI\Providers\AIProviderInterface;

class TenantSupportAgent extends Agent
{
    public function __construct(
        private readonly Tenant $tenant,
        int $conversationId,
    ) {
        // The thread is the conversation's identity - and the run's workflow ID
        parent::__construct(threadId: "t{$tenant->id}:c{$conversationId}");
    }

    protected function provider(): AIProviderInterface
    {
        return AIProvider::driver();
    }

    protected function chatHistory(): ChatHistoryInterface
    {
        // No thread here: the agent binds its own
        return new EloquentChatHistory(
            modelClass: ChatMessage::class,
            contextWindow: config('neuron.context_window'),
        );
    }

    protected function tools(): array
    {
        return [
            // The tool receives the tenant — it cannot query outside it
            new SearchOrdersTool($this->tenant),
        ];
    }
}
```

This is how an agent with its own constructor declares its thread: it hands it to the parent constructor, not to the history. The composite key is built from two server-side values, never from anything in the request.

### The principle

**Scope at construction, not at query time.**

The tool receives a `Tenant` and builds its queries from it. There is no code path where a tool queries without a tenant scope, because it has no way to.

Compare with the alternative — a tool that reads the current tenant from a global or a facade inside `__invoke()`. That works until something runs outside a request: a queue job, a scheduled command, a resumed workflow. Then the global is empty or, worse, holds the wrong tenant.

**Agentic systems run outside the request cycle more often than normal application code.** Queue workers (Section 16.4), resumed workflows (Section 15.4), scheduled ingestion (Chapter 20). Ambient tenant context is unreliable in all three. Pass it explicitly.

That argument generalises well beyond NeuronAI.

### Workflow IDs

The agent's workflow ID comes free with its thread. Your own workflows declare theirs by overriding `workflowId()`:

```php
class RefundWorkflow extends Workflow
{
    public function __construct(
        private readonly Tenant $tenant,
        private readonly Order $order,
    ) {
        parent::__construct();
    }

    public function workflowId(): ?string
    {
        return "t{$this->tenant->id}:refund:{$this->order->id}";
    }

    // nodes() ...
}
```

Tenant-prefixed, so a resumed workflow cannot be confused with another tenant's, and business-keyed, so a later request holding only the tenant and the order rebuilds the workflow and finds its paused run with a single read. A workflow that declares no ID gets an engine-generated one — continuable, but only by whoever kept the handle.

### Testing isolation

Worth writing as a real test:

```php
public function test_tenant_a_cannot_see_tenant_b_conversation(): void
{
    $agentA = new TenantSupportAgent($tenantA, $conversationId);
    $agentA->chat(new UserMessage('My secret code is ALPHA'));

    $agentB = new TenantSupportAgent($tenantB, $conversationId);
    $reply = $agentB->chat(new UserMessage('What is my secret code?'))->getMessage();

    $this->assertStringNotContainsString('ALPHA', (string) $reply?->getContent());
}
```

Note the deliberately hostile setup: the *same* conversation ID for both tenants. If the tenant prefix is missing, this test fails — which is exactly what you want it to catch.

### Key takeaways

- Four leak points: history, vector store, tools, workflow persistence — for an agent, the thread covers the first and the last.
- Scope at construction; do not read ambient context inside tools.
- Declare business-keyed, tenant-prefixed workflow IDs with `workflowId()`.
- Agentic code runs outside the request cycle often — globals are unreliable there.
- Write an isolation test with a colliding identifier.

## 18.4 Eloquent Workflow Persistence

### The setup

```php
use NeuronAI\Laravel\Models\WorkflowStore;
use NeuronAI\Workflow\Persistence\EloquentPersistence;
use NeuronAI\Workflow\Persistence\PersistenceInterface;

class TenantSupportAgent extends Agent
{
    // ...

    protected function persistence(): PersistenceInterface
    {
        return new EloquentPersistence(WorkflowStore::class);
    }
}
```

`persistence()` is a hook like `provider()` and `chatHistory()`; `setPersistence()` is its setter twin, for a plain `Workflow` or a one-off. The package ships the `WorkflowStore` model, and its migration comes with `--tag=neuron-migrations` alongside the chat history tables. `EloquentPersistence` takes nothing but the model class — it borrows the model's table and connection.

That table, `workflow_store`, is the whole of v4 persistence: one partitioned key-value space. Every record of a run — its ignition, its control record, its step results — lives in the partition named by the **workflow ID**, which for an agent is the thread. That is what lets an approve endpoint rebuild `TenantSupportAgent` from the tenant and the conversation alone and find the paused run with a single read. When a run completes cleanly, its partition is swept; nothing accumulates.

::: {.callout .callout-warning}
[`workflow_store` is not an application table]{.callout-title}

Partition names and keys are hex-encoded and the values are serialised engine records. There is no `tenant_id` to filter on and nothing meant to be read with a `where()`. Treat the table as the engine's private storage: back it up, never query it. On MySQL it also requires strict SQL mode — Laravel's default `'strict' => true` connection setting — and `EloquentPersistence` refuses to start without it rather than risk truncated records.
:::

### Why Eloquent rather than files

Section 15.4 offered `FilePersistence` and `DatabasePersistence`. In Laravel, Eloquent persistence gives you:

**Multi-server safety.** Any worker can resume any workflow. File persistence on local disk means the resume must land on the same machine — which behind a load balancer is a coin flip. The file backend is meant for controlled single-process use.

**Atomic continuation.** Every write is a conditional compare-and-write inside a transaction on the model's connection. Two processes racing to continue the same run cannot both win.

**One connection.** The run lives in the database you already run, on the connection your models use, with no second credential to manage.

**Backups.** In-flight workflows are backed up with everything else, rather than living in a directory nobody remembers to include.

### The pending-approvals screen

The pattern this unlocks, and the one Chapter 22 builds. Because the store is not queryable, the list of waiting conversations is something your application records itself, at the moment it learns about the pause — and in v4 it learns without an exception. `chat()` returns normally, with an interrupted state:

```php
$state = $agent->chat(new UserMessage($input));

if ($state->isInterrupted()) {
    $conversation->update(['awaiting_approval_at' => now()]);
}
```

```php
class ApprovalsController extends Controller
{
    public function index(Request $request)
    {
        $pending = Conversation::query()
            ->where('tenant_id', $request->user()->tenant_id)
            ->whereNotNull('awaiting_approval_at')
            ->latest('awaiting_approval_at')
            ->paginate();

        return view('approvals.index', compact('pending'));
    }
}
```

The detail page asks the agent itself what it is waiting for. Rebuild it for the conversation and read `pendingApprovals()` — one action per gated tool call, with the call ID, the tool name, the arguments and the reason the tool gave for asking:

```php
foreach ($agent->pendingApprovals() as $action) {
    // $action->id, $action->name, $action->inputs, $action->reason
}
```

The same information is also on the thread's last message in chat history, which is what a frontend renders from (Chapter 22).

Because waiting conversations are rows in *your* table, "the AI is waiting for a human" becomes an ordinary index page with ordinary authorisation. That is the moment human-in-the-loop stops being an exotic AI feature and becomes normal application development — which is precisely what makes the pattern deployable.

### Operational reminders from Section 15.4

The four questions still apply, now with Laravel answers:

- **Notification** → dispatch a `Notification` when the returned state `isInterrupted()`; there is no exception to catch
- **Timeout** → a scheduled command over `awaiting_approval_at` that settles stale runs with a rejection, `submitApprovalDecisions([$callId => ['reject', 'Timed out']])->run()` — rejecting is the cancel path
- **Double-resume** → handled by the engine: a second submission for a settled run finds no persisted run and throws, and a new `chat()` on a thread that is still waiting throws `RunInFlightException` — lock the input in the UI until the decision is delivered
- **Deployment compatibility** → keep interrupt requests small and flat; the serialised payload contains your classes. Tools are never serialised in v4, so a tool holding a repository or an HTTP client is safe to persist around

### Key takeaways

- `EloquentPersistence(WorkflowStore::class)`, returned from the agent's `persistence()` hook.
- One `workflow_store` table, partitioned by workflow ID — the thread, for an agent. Back it up; never query it.
- Multi-server safe, atomic, on your existing connection, backed up.
- Record pending approvals on your own model when `isInterrupted()`; read the details with `pendingApprovals()`.
- The four operational questions get ordinary Laravel answers.

## Lab 12 — Persistent Multi-Thread Chat

**Covers:** container bindings, `EloquentChatHistory`, thread isolation, context windows.

### Goal

An authenticated user can hold several independent conversations with the same agent, each one persisted, each one isolated, each one resumable after a full deploy.

### Requirements

1. **A `conversations` table** owned by users, with a title and timestamps. A user may have many.
2. **The agent resolves from the container**, bound with the current conversation, never constructed in a controller.
3. **The thread ID is derived server-side** from the authenticated user and the conversation record — never from a request parameter. Prove this: attempt to read another user's conversation by ID and get a 403 from your policy, not an answer from the agent.
4. **The context window comes from configuration**, keyed by the configured provider, as in Section 18.2.
5. **Extend `ChatMessage`** with a foreign key to `conversations` and a soft delete.

### Acceptance criteria

- Two conversations for one user do not see each other's messages.
- Two users with sequential conversation IDs cannot reach each other's threads — verify with an authorisation test, not by inspection.
- Restarting the application server loses nothing.
- Switching `NEURON_AI_PROVIDER` from `anthropic` to `ollama` changes the trimmer's context window without a code change. Log the configured value to prove it.
- Deleting a conversation soft-deletes its messages, and the agent no longer sees them.

### The interesting part

Write the isolation test from Section 18.3 with a **colliding conversation ID across two tenants or users**. It is the test that catches the missing prefix, and it is the one people skip because the happy path already worked.

### Going further

Add a `/conversations/{id}/export` endpoint that returns the full transcript as JSON. You now have the GDPR export requirement satisfied, and you will discover immediately whether your message model carries enough context to be exportable — most first attempts do not.
