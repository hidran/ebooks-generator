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
    public function ask(Request $request, Conversation $conversation)
    {
        return SupportAgent::make(workflowId: $conversation->threadId())
            ->chat(new UserMessage($request->input('message')))
            ->getMessage()
            ?->getContent();
    }
}
```

Works. But the controller now constructs the agent, which means you cannot swap it in tests, cannot hand it the stores the rest of the application shares, and cannot configure it in one place. (`threadId()` names the conversation's thread; Section 18.2 is about getting that name right.)

### Constructor injection

```php
namespace App\Neuron\Agents;

use NeuronAI\Agent\Agent;
use NeuronAI\Chat\History\MessageStoreInterface;
use NeuronAI\Laravel\Facades\AIProvider;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Workflow\Persistence\PersistenceInterface;

class SupportAgent extends Agent
{
    public function __construct(
        protected MessageStoreInterface $conversations,
        protected PersistenceInterface $runs,
    ) {
        parent::__construct();
    }

    protected function provider(): AIProviderInterface
    {
        return AIProvider::driver();
    }

    protected function messageStore(): MessageStoreInterface
    {
        return $this->conversations;
    }

    protected function persistence(): PersistenceInterface
    {
        return $this->runs;
    }

    // contextWindow() arrives in Section 18.2, tools() in Section 18.3
}
```

The constructor asks for the two things an agent keeps between requests — where conversations live (Section 18.2) and where paused runs live (Section 18.4) — and for nothing about who is asking. No user, no tenant, no thread: the class describes an agent, not a conversation.

Remember `parent::__construct()` (Section 4.3) and that a custom constructor changes what `make()` accepts. `make()` forwards its arguments to the constructor, so once you own the constructor, `make(workflowId: ...)` is an unknown named parameter — the thread arrives another way, below. And call the promoted properties anything but `$messageStore` and `$persistence`: `Agent` already declares both, with nullable types, and PHP rejects the redeclaration with a fatal error.

### Binding

```php
namespace App\Providers;

use App\Models\ChatMessage;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\ServiceProvider;
use NeuronAI\Chat\History\EloquentMessageStore;
use NeuronAI\Chat\History\MessageStoreInterface;
use NeuronAI\Workflow\Persistence\DatabasePersistence;
use NeuronAI\Workflow\Persistence\PersistenceInterface;

class NeuronServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        // Stateless: it resolves the model's connection on every call
        $this->app->singleton(
            MessageStoreInterface::class,
            fn () => new EloquentMessageStore(ChatMessage::class),
        );

        // It keeps the PDO it was given, so every resolution takes the current one
        $this->app->bind(
            PersistenceInterface::class,
            fn () => new DatabasePersistence(DB::connection()->getPdo()),
        );
    }
}
```

This is a provider of your own — `php artisan make:provider NeuronServiceProvider` creates and registers it — not the SDK's `NeuronAIServiceProvider`. It binds the two stores and nothing else. The agent needs no binding: Laravel reads its constructor and autowires it.

```php
class SupportController extends Controller
{
    public function ask(
        Request $request,
        Conversation $conversation,
        SupportAgent $agent,
    ) {
        Gate::authorize('participate', $conversation);

        return $agent
            ->for($conversation->threadId())
            ->chat(new UserMessage($request->input('message')))
            ->getMessage()
            ?->getContent();
    }
}
```

**The container builds the agent; the request binds it.** The action asks for an agent in its signature and gets one, wired to the application's stores. The policy decides whether this user may use this conversation, and only then does `for()` return a copy of the agent bound to that conversation's thread; the instance the container built is never modified. Ask for the agent in the action, not in the controller's constructor: it is resolved when the action runs, after the middleware has authenticated the user, and nothing holds it longer than the call.

### Why this is worth the ceremony

**Testability.** Hand the container an agent whose provider is a fake and the controller talks to it; the copy `for()` makes shares that provider. This is the Section 1.5 problem — you cannot assert on model output, so the boundary you *can* test is the controller's handling of an agent, and dependency injection is what makes that boundary exist.

```php
$provider = new FakeAIProvider(new AssistantMessage('Your order ships tomorrow.'));

$this->app->instance(
    SupportAgent::class,
    $this->app->make(SupportAgent::class)->setAiProvider($provider),
);

$this->actingAs($user)
    ->post("/conversations/{$conversation->id}/messages", [
        'message' => 'Where is my order?',
    ])
    ->assertOk();

$provider->assertCallCount(1);
```

**Per-user configuration.** The thread says whose conversation this is, so what the agent builds for a run — its tools, and their visibility (Section 5.10) — follows from the thread it was bound to, without the controller knowing. Section 18.3 shows how.

**One place to change.** The stores are decided in the service provider; provider, tools and instructions in the class. No controller decides any of them.

**It reads like Laravel.** Which matters for adoption. An agent that arrives by injection is a service like any other, and a team already knows how to reason about services.

### Lifetimes

The two bindings have different lifetimes on purpose, and the agent has a third:

- The message store is a `singleton()`. `EloquentMessageStore` holds a model class and nothing else; it resolves the model's connection on every call.
- The persistence is a plain `bind()`. `DatabasePersistence` keeps the PDO it was given, so each resolution has to take Laravel's current one. In a long-lived worker a reconnect replaces that PDO, and a singleton would go on holding the old one.
- The agent is not registered at all. Autowiring builds a new one every time it is resolved — per request, per job — and that is the lifetime you want.

::: {.callout .callout-warning}
[Never `singleton()` an agent]{.callout-title}

An agent captures its persistence — and that PDO — when it is built. Register it as a singleton and, under Octane or in a queue worker, one instance serves every request for the life of the process: it holds a connection handle long after a reconnect has replaced it, and whatever one request set on it is still there for the next. It is your responsibility, and it will not appear at all under PHP-FPM.
:::

### Key takeaways

- Constructor injection for the stores, bound in a service provider; the agent itself is autowired.
- The container builds the agent; the request authorises the conversation and binds its thread with `for()`.
- Testability, per-user configuration, single point of change.
- Never `singleton()` an agent — resolve it per request or per job.

## 18.2 EloquentMessageStore

### One migration

```bash
php artisan make:migration create_neuron_tables
php artisan make:model ChatMessage
```

One migration of your own creates both tables NeuronAI needs: `chat_messages` for the conversations and `workflow_store` for the runs of Section 18.4. Replace the body of the generated file with this, then run `php artisan migrate`:

```php
use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * The conversations (EloquentMessageStore) and the durable runs (DatabasePersistence) of the Neuron agents.
     */
    public function up(): void
    {
        // MySQL and MariaDB collations ignore case and accents: identifiers must compare byte by byte there.
        $mysql = in_array(Schema::getConnection()->getDriverName(), ['mysql', 'mariadb'], true);

        Schema::create('chat_messages', function (Blueprint $table) use ($mysql) {
            $table->id();
            if ($mysql) {
                $table->binary('thread_id', 255);
                $table->binary('message_id', 64);
            } else {
                $table->string('thread_id', 255);
                $table->string('message_id', 64);
            }
            $table->string('role', 32);
            $table->longText('content')->nullable();
            $table->longText('meta')->nullable();
            $table->timestamp('archived_at')->nullable();
            $table->timestamps();
            $table->unique(['thread_id', 'message_id']);
        });

        Schema::create('workflow_store', function (Blueprint $table) use ($mysql) {
            if ($mysql) {
                $table->string('partition', 510)->charset('ascii')->collation('ascii_bin');
                $table->string('key', 510)->charset('ascii')->collation('ascii_bin');
                $table->longText('value')->charset('ascii');
            } else {
                $table->string('partition', 510);
                $table->string('key', 510);
                $table->longText('value');
            }
            $table->timestamp('updated_at')->useCurrent();
            $table->primary(['partition', 'key']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('workflow_store');
        Schema::dropIfExists('chat_messages');
    }
};
```

It is the migration the maintainers publish in the framework's `neuron-laravel-integration` skill, which reports it running unchanged on SQLite, MySQL 8.4, MariaDB 11.7 and PostgreSQL 17. Three things in `chat_messages` are there for the store:

- `message_id` is a message's identity. The store appends by `(thread_id, message_id)`, so writing the same message twice stores it once, and the unique index serves every thread lookup.
- The auto-increment `id` orders the thread. Whatever key your model uses must follow insertion order — auto-increment, ULID or UUIDv7, never UUIDv4.
- `archived_at` marks the messages trimmed out of the context window, which are kept rather than deleted (below).

The `binary()` columns are for MySQL and MariaDB, whose default collations ignore case: with `string()`, two threads whose names differ only by case would share a history.

::: {.callout .callout-warning}
[Do not publish the SDK's migrations]{.callout-title}

neuron-laravel 2.0.0 still offers `php artisan vendor:publish --tag=neuron-migrations` and a `NeuronAI\Laravel\Models\ChatMessage` model, and neither fits neuron-ai 4.0.3. The store identifies every message by `message_id`; the SDK's table has no such column and its model does not make it fillable. On SQLite, where this book probed it, nothing fails: the same message is stored twice and comes back under a different ID. Use the migration above and the model below.
:::

### Use it

```php
namespace App\Models;

use Illuminate\Database\Eloquent\Attributes\Fillable;
use Illuminate\Database\Eloquent\Model;

#[Fillable(['thread_id', 'message_id', 'role', 'content', 'meta'])]
class ChatMessage extends Model
{
    protected function casts(): array
    {
        return [
            'content' => 'array',
            'meta' => 'array',
        ];
    }
}
```

Five fillable columns and two array casts: that is all the store asks of the model. The store itself takes nothing but the model class — `new EloquentMessageStore(ChatMessage::class)`, the line `NeuronServiceProvider` already contains — and the agent hands it to the framework through a hook. A second hook says how much of the conversation the model may be sent:

```php
class SupportAgent extends Agent
{
    // ...

    protected function messageStore(): MessageStoreInterface
    {
        return $this->conversations;
    }

    protected function contextWindow(): int
    {
        return 100_000;
    }
}
```

```php
$agent->for('THREAD_ID')->chat(new UserMessage('Hello'));
```

Notice what the store does *not* receive: the thread. The store is stateless — one instance serves every conversation, which is why it can be a singleton — and every read and write names the thread it is for. The thread belongs to the agent. You bind it once, with `for()`, and the framework never invents one: an agent with no thread refuses to run.

The thread is more than a history key. It is also the agent's **workflow ID** — the name under which a paused run is persisted and later found again (Section 18.4). One identifier, bound in one place, names both the conversation and the run.

Between the store and the model sits `ChatHistory`, a concrete class the agent builds for itself each time it runs, from exactly those three things: the store, the thread and the window. It loads the thread's active messages and keeps them inside the budget. You never construct it.

::: {.callout .callout-warning}
[A `chatHistory()` override keeps nothing]{.callout-title}

`messageStore()` and `contextWindow()` are the only memory hooks in neuron-ai 4.0.3. A class that overrides `chatHistory()` instead — as the README of neuron-laravel 2.0.0 and its bundled Boost skills still show — loads and answers without an error, because nothing calls that method. The agent silently uses the in-memory store with a 50,000-token window, and the conversation is gone when the request ends. If an agent forgets everything between two requests, look for that method first.
:::

### Making thread_id real

`'THREAD_ID'` is a placeholder. In practice it is the isolation boundary, and getting it wrong is a data leak. Name the thread on the server, from a record, and let a policy say who may use that record:

```php
class Conversation extends Model
{
    /** Named on the server from three columns of this row, never from a request. */
    public function threadId(): string
    {
        return "t{$this->tenant_id}:u{$this->user_id}:c{$this->id}";
    }
}
```

```php
class ConversationPolicy
{
    public function participate(User $user, Conversation $conversation): bool
    {
        return $conversation->user_id === $user->id
            && $conversation->tenant_id === $user->tenant_id;
    }
}
```

That is what two lines of Section 18.1's controller were doing. The route names a conversation; `Gate::authorize('participate', $conversation)` decides whether this user may use it; only then does `for($conversation->threadId())` bind the agent. The agent needs no constructor argument for any of it: `for()` is the front door for identity on a container-built agent, and the code in front of it is the one place that decides which thread a request may touch.

**Never derive the thread ID from user input.** A request parameter that becomes a thread ID means anyone can read anyone's conversation by changing a number. The conversation ID in the URL is user input too; it is the policy that turns it into a resource this user may use. Derive the thread server-side from an authenticated, authorised resource.

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
protected function contextWindow(): int
{
    return config('neuron.context_windows.' . config('neuron.provider.default'), 29_000);
}
```

Change provider by environment and the trimmer follows. Hardcode 100,000 and someone running Ollama locally will hit context errors that never appear in production.

### Extending the model

`ChatMessage` is your model, so it can grow with the application. A real application usually wants:

- A foreign key to `conversations` or `users`
- Soft deletes for retention policy
- An index on `thread_id` plus a timestamp
- A tenant column

One rule governs all of them: the store writes its own five columns and knows nothing about yours. A `NOT NULL` column it does not fill fails every append. Make application columns nullable, or fill them in a `creating` hook from the one thing every row carries, its thread:

```php
class ChatMessage extends Model
{
    use SoftDeletes;

    // ...

    protected static function booted(): void
    {
        // The store fills its five columns; the thread says what the others are
        static::creating(function (ChatMessage $message): void {
            $scope = ThreadScope::of($message->thread_id);

            $message->tenant_id = $scope->tenantId;
            $message->conversation_id = $scope->conversationId;
        });
    }
}
```

`ThreadScope` reads back the name `threadId()` wrote; Section 18.3 prints it. This is also where GDPR lives: conversations contain whatever users typed, which in a support context means personal data. Deletion, export and retention are product requirements, not afterthoughts — Section 3.7's logging warning, made concrete.

One behaviour changes the retention arithmetic. When the history trims messages out of the context window, it does not delete them: it stamps them with `archived_at` and loads only the unarchived rows. The model sees the trimmed thread; your table keeps the full transcript. That is good for auditing and for the export below, but it means "the agent forgot it" and "we no longer store it" are now different statements. Your retention job has to delete archived rows explicitly.

### Key takeaways

- One migration and one model of your own; the SDK's published table does not fit neuron-ai 4.0.3.
- `messageStore()` returns the store and `contextWindow()` the budget; the thread is bound on the agent with `for()`, never given to the store.
- The thread ID is the isolation boundary — derive it server-side, never from input.
- Derive the context window from the configured provider.
- Extend `ChatMessage` for foreign keys, tenancy and retention, with columns that are nullable or filled in `creating`; trimmed rows are archived, not deleted.

## 18.3 Multi-Tenant Isolation

### The four leak points

An agentic system in a multi-tenant application has four places tenant data can cross:

1. **Chat history** — `thread_id`
2. **Vector store** — the retrieval scope (Section 12.6)
3. **Tools** — the data they query
4. **Workflow persistence** — the workflow ID

Miss any one and you have a breach. Keep the list somewhere you will see it during code review.

For an agent, the framework fuses the first and the last: the thread ID *is* the workflow ID. Get the thread right and the persisted run is scoped with it; get it wrong and both leak together.

### A tenant-aware agent

```php
namespace App\Neuron;

use LogicException;

/** Who a thread belongs to, read back from the name Conversation::threadId() gave it. */
final readonly class ThreadScope
{
    private function __construct(
        public int $tenantId,
        public int $userId,
        public int $conversationId,
    ) {}

    public static function of(?string $threadId): self
    {
        if (preg_match('/^t(\d+):u(\d+):c(\d+)$/', (string) $threadId, $match) !== 1) {
            throw new LogicException(
                "Thread '{$threadId}' names no tenant, user and conversation."
            );
        }

        return new self((int) $match[1], (int) $match[2], (int) $match[3]);
    }
}
```

```php
class SupportAgent extends Agent
{
    // ...

    protected function tools(): array
    {
        $scope = ThreadScope::of($this->getThreadId());

        return [
            // The tools receive the tenant - they cannot query outside it
            new SearchOrdersTool($scope->tenantId),
            new GetOrderStatusTool($scope->tenantId),
        ];
    }
}
```

This is how an agent that was built knowing nothing about its caller comes to know its tenant: from the thread it was bound to, not from `auth()` and not from a constructor argument. The name was composed on the server from three columns of a row, never from anything in the request, and a thread that does not carry all three is refused before a single tool exists.

### The principle

**Scope at construction, not at query time.**

The tool receives a tenant ID and builds its queries from it. There is no code path where a tool queries without a tenant scope, because it has no way to.

Compare with the alternative — a tool that reads the current tenant from a global or a facade inside `__invoke()`. That works until something runs outside a request: a queue job, a scheduled command, a resumed workflow. Then the global is empty or, worse, holds the wrong tenant.

**Agentic systems run outside the request cycle more often than normal application code.** Queue workers (Section 16.4), resumed workflows (Section 15.4), scheduled ingestion (Chapter 20). Ambient tenant context is unreliable in all three. Pass it explicitly — which is what the thread does: the same agent, bound to the same thread, builds the same tools in a controller and in a queue worker.

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

Tenant-prefixed, so a resumed workflow cannot be confused with another tenant's, and business-keyed, so a later request holding only the tenant and the order rebuilds the workflow and finds its paused run with a single read. Chapter 22's refund workflow keeps Section 15.4's shorter `refund:{orderId}`: an order's primary key is already unique across tenants, and the prefix is for business keys that are not. A workflow with no ID at all — none declared, none given — does not run: the engine never makes one up.

### Testing isolation

Worth writing as a real test:

```php
public function test_tenant_a_history_never_reaches_tenant_b(): void
{
    // The hostile part: both tenants hold user 3 and conversation 7
    $a = (new Conversation())->forceFill(['id' => 7, 'tenant_id' => 1, 'user_id' => 3]);
    $b = (new Conversation())->forceFill(['id' => 7, 'tenant_id' => 2, 'user_id' => 3]);

    $modelA = new FakeAIProvider(new AssistantMessage('Noted.'));
    $modelB = new FakeAIProvider(new AssistantMessage('I do not know.'));

    app(SupportAgent::class)->setAiProvider($modelA)
        ->for($a->threadId())
        ->chat(new UserMessage('My secret code is ALPHA'));

    app(SupportAgent::class)->setAiProvider($modelB)
        ->for($b->threadId())
        ->chat(new UserMessage('What is my secret code?'));

    // Assert on what tenant B's model was sent, not on what a model might answer
    $modelB->assertCallCount(1);
    $modelB->assertSent(fn (RequestRecord $request): bool =>
        ! str_contains(json_encode($request->messages), 'ALPHA'));
}
```

Note the deliberately hostile setup: the *same* user and conversation numbers for both tenants. If the tenant prefix is missing, this test fails — which is exactly what you want it to catch.

Note also what it asserts on. `FakeAIProvider` (Lab 7) records every request, so the test inspects the messages that reached tenant B's model instead of hoping a live model would repeat the secret. No model is called, the result is the same on every run, and the test can gate a deploy.

### Key takeaways

- Four leak points: history, vector store, tools, workflow persistence — for an agent, the thread covers the first and the last.
- Scope at construction; do not read ambient context inside tools.
- Declare business-keyed, tenant-prefixed workflow IDs with `workflowId()`.
- Agentic code runs outside the request cycle often — globals are unreliable there.
- Write an isolation test with a colliding identifier, and assert on what the model was sent.

## 18.4 Database Workflow Persistence

### The setup

```php
class SupportAgent extends Agent
{
    // ...

    protected function persistence(): PersistenceInterface
    {
        return $this->runs;
    }
}
```

`persistence()` is a hook like `provider()` and `messageStore()`; `setPersistence()` is its setter twin, for a plain `Workflow` or a one-off. What it returns here is the `DatabasePersistence` that `NeuronServiceProvider` builds over Laravel's own PDO, and its table came with the migration in Section 18.2.

That table, `workflow_store`, is the whole of NeuronAI's persistence: one partitioned key-value space. Every record of a run — its ignition, its control record, its step results — lives in the partition named by the **workflow ID**, which for an agent is the thread. That is what lets an approve endpoint bind `SupportAgent` to the conversation's thread and find the paused run with a single read. When a run completes cleanly, its partition is swept; nothing accumulates.

::: {.callout .callout-warning}
[`workflow_store` is not an application table]{.callout-title}

Partition names and keys are hex-encoded and the values are base64-encoded engine records. There is no `tenant_id` to filter on and nothing meant to be read with a `where()`. Treat the table as the engine's private storage: back it up, never query it. On MySQL it also requires strict SQL mode — Laravel's default `'strict' => true` connection setting — and `DatabasePersistence` refuses to write without it rather than risk truncated records.
:::

### Why the database rather than files

Section 15.4 listed the backends. In Laravel, `DatabasePersistence` gives you:

**Multi-server safety.** Any worker can resume any workflow. File persistence on local disk means the resume must land on the same machine — which behind a load balancer is a coin flip. The file backend is meant for controlled single-process use.

**Atomic continuation.** Every write is a conditional compare-and-write inside a transaction on Laravel's connection. Two processes racing to continue the same run cannot both win.

**One connection.** The run lives in the database you already run, on the connection your models use, with no second credential to manage.

**Backups.** In-flight workflows are backed up with everything else, rather than living in a directory nobody remembers to include.

`EloquentPersistence` is the other database backend. It takes a model class and resolves the model's connection on every operation, so it can be a singleton. It is not a drop-in for this table: it needs a table of its own with an ordinary `id` primary key and `unique(partition, key)` in place of the composite key, and a model of your own — `App\Models\WorkflowRecord`, say — with `partition`, `key` and `value` fillable and no soft deletes.

::: {.callout .callout-warning}
[Not the SDK's `WorkflowStore`]{.callout-title}

neuron-laravel 2.0.0 ships a `NeuronAI\Laravel\Models\WorkflowStore` model over a `workflow_store` table with a composite primary key and no `id`. `new EloquentPersistence(WorkflowStore::class)` does not work on neuron-ai 4.0.3: the backend addresses rows through a key the table does not have. On SQLite, where this book probed it, a completed run is never swept, and the next message on the same thread is refused with `RunInFlightException` until the ten-minute lease expires. Use `DatabasePersistence`, or give `EloquentPersistence` a table and a model of your own.
:::

### The pending-approvals screen

The pattern this unlocks, and the one Chapter 22 builds. Because the store is not queryable, the list of waiting conversations is something your application records itself, at the moment it learns about the pause — and it learns without an exception. `chat()` returns normally, with an interrupted state:

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

The detail page asks the agent itself what it is waiting for. Bind it to the conversation's thread and read `pendingApprovals()` — one action per gated tool call, with the call ID, the tool name, the arguments and the reason the tool gave for asking:

```php
foreach ($agent->pendingApprovals() as $action) {
    // $action->id, $action->name, $action->inputs, $action->reason
}
```

The same information is also on the thread's last message in chat history, which is what a frontend renders from (Chapter 22).

Because waiting conversations are rows in *your* table, "the AI is waiting for a human" becomes an ordinary index page with ordinary authorisation. That is the moment human-in-the-loop stops being an exotic AI feature and becomes normal application development — which is precisely what makes the pattern deployable.

### Operational reminders from Section 15.4

The four questions still apply, now with Laravel answers, and durable stores add a fifth:

- **Notification** → dispatch a `Notification` when the returned state `isInterrupted()`; there is no exception to catch
- **Timeout** → a scheduled command over `awaiting_approval_at` that settles stale runs with a rejection, `submitApprovalDecisions([$callId => ['reject', 'Timed out']])->run()` — rejecting is the cancel path
- **Double-resume** → handled by the engine: a second submission for a settled run finds no persisted run and throws `InputTranslationException`, and a new `chat()` on a thread that is still waiting throws `RunInFlightException` — answer them with a 400 and a 409, and lock the input in the UI until the decision is delivered
- **Deployment compatibility** → keep interrupt requests small and flat; the serialised payload contains your classes. Tools are never serialised, so a tool holding a repository or an HTTP client is safe to persist around
- **Failed turns** → a turn that dies after it stored its question — the provider fails after a tool step, an exception escapes a tool — leaves its run `failed`, and the next `chat()` on that thread throws `ChatHistoryException: Invalid message sequence`. Finish the failed turn before starting the next one

```php
class SupportAgent extends Agent
{
    // ...

    /** A failed turn that stored its question blocks the next one: finish it first. */
    public function recoverFailedTurn(): void
    {
        $run = $this->inspect();

        if ($run?->status === WorkflowStatus::Failed) {
            $this->run(ExecutionRequest::resume(
                expectedRunId: $run->runId,
                expectedExecutionAttempt: $run->executionAttempt,
            ));
        }
    }
}
```

```php
$agent = $agent->for($conversation->threadId());
$agent->recoverFailedTurn();

$state = $agent->chat(new UserMessage($request->input('message')));
```

Every endpoint that starts a turn calls it first; with nothing to recover it does nothing. Before, not after: once a new question has been stacked on a failed turn, finishing that turn fails the same way, and only `resetConversation()` — which wipes the thread's history along with its run — frees the thread.

### Key takeaways

- `DatabasePersistence` over Laravel's PDO, bound in the service provider and returned from the agent's `persistence()` hook.
- One `workflow_store` table, partitioned by workflow ID — the thread, for an agent. Back it up; never query it.
- Multi-server safe, atomic, on your existing connection, backed up.
- Record pending approvals on your own model when `isInterrupted()`; read the details with `pendingApprovals()`.
- The four operational questions get ordinary Laravel answers; the fifth is `recoverFailedTurn()` before every turn.

## Lab 12 — Persistent Multi-Thread Chat

**Covers:** container bindings, `EloquentMessageStore`, thread isolation, context windows.

### Goal

An authenticated user can hold several independent conversations with the same agent, each one persisted, each one isolated, each one resumable after a full deploy.

### Requirements

1. **A `conversations` table** owned by users, with a tenant, a title and timestamps. A user may have many.
2. **The agent resolves from the container**, by method injection, and is bound to the current conversation with `for()` — never constructed in a controller.
3. **The thread ID is derived server-side** from the conversation record, once the policy has authorised the authenticated user for it — never from a request parameter. Prove this: attempt to read another user's conversation by ID and get a 403 from your policy, not an answer from the agent.
4. **The context window comes from configuration**, keyed by the configured provider, as in Section 18.2.
5. **Extend `ChatMessage`** with a foreign key to `conversations`, filled in a `creating` hook, and a soft delete.

### Acceptance criteria

- Two conversations for one user do not see each other's messages.
- Two users with sequential conversation IDs cannot reach each other's threads — verify with an authorisation test, not by inspection.
- Restarting the application server loses nothing.
- Switching `NEURON_AI_PROVIDER` from `anthropic` to `ollama` changes the trimmer's context window without a code change. Log the configured value to prove it.
- Deleting a conversation soft-deletes its messages, and the agent no longer sees them.
- A turn that fails halfway does not block the conversation: the next message is answered.

### The interesting part

Write the isolation test from Section 18.3 with a **colliding conversation ID across two tenants or users**. It is the test that catches the missing prefix, and it is the one people skip because the happy path already worked.

### Going further

Add a `/conversations/{id}/export` endpoint that returns the full transcript as JSON. You now have the GDPR export requirement satisfied, and you will discover immediately whether your message model carries enough context to be exportable — most first attempts do not.
