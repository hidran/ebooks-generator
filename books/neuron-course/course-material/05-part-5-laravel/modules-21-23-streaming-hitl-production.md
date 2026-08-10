# Agentic AI in PHP with Neuron
## PART V — LARAVEL (continued)
### Full lesson scripts — Modules 21, 22 and 23

> Copy each lesson block (between the `═══` separators) into its own Google Doc.
> Target versions: `neuron-core/neuron-laravel` ^1.3, `neuron-core/neuron-ai` ^3.15, PHP 8.2+, Laravel 10–13.
> **This batch closes Part V and the main course.**

---
═══════════════════════════════════════════════════════════════
# MODULE 21 — STREAMING TO THE FRONTEND
═══════════════════════════════════════════════════════════════
---

## LESSON 21.1 — Server-Sent Events in Laravel

**Duration:** 13 minutes
**Type:** Hands-on

### Learning objectives

Stream an agent's response to a browser over SSE.

### Why SSE rather than WebSockets

For agent responses the traffic is one-directional: the server sends, the browser receives. SSE gives you that over ordinary HTTP, with automatic reconnection built into the browser and no extra infrastructure.

WebSockets are the right choice when the browser also needs to push — which for a chat interface it does not, because the next message is a new request.

### The controller

```php
<?php

declare(strict_types=1);

namespace App\Http\Controllers;

use App\Neuron\Agents\SupportAgent;
use Illuminate\Http\Request;
use NeuronAI\Chat\Messages\UserMessage;
use Symfony\Component\HttpFoundation\StreamedResponse;

class ChatStreamController extends Controller
{
    public function __construct(
        private readonly SupportAgent $agent,
    ) {}

    public function __invoke(Request $request): StreamedResponse
    {
        $validated = $request->validate([
            'message' => ['required', 'string', 'max:4000'],
        ]);

        return response()->stream(function () use ($validated) {
            $handler = $this->agent->stream(new UserMessage($validated['message']));

            foreach ($handler->events() as $chunk) {
                echo 'data: ' . \json_encode([
                    'type'    => \class_basename($chunk),
                    'content' => $chunk->content ?? null,
                ]) . "\n\n";

                if (\ob_get_level() > 0) {
                    \ob_flush();
                }
                \flush();
            }

            echo "event: done\ndata: {}\n\n";
            \flush();
        }, 200, [
            'Content-Type'      => 'text/event-stream',
            'Cache-Control'     => 'no-cache, no-transform',
            'X-Accel-Buffering' => 'no',
            'Connection'        => 'keep-alive',
        ]);
    }
}
```

### The four headers, each doing a job

**`Content-Type: text/event-stream`** — tells the browser this is SSE.

**`Cache-Control: no-cache, no-transform`** — `no-transform` matters: some proxies compress or rewrite responses, which breaks the frame boundaries.

**`X-Accel-Buffering: no`** — nginx-specific, and the one that saves you a day. Without it nginx buffers the response and delivers it all at once, at which point you have the complexity of streaming with none of the benefit.

**`Connection: keep-alive`** — hold the connection open.

### The SSE frame format

```
data: {"type":"TextChunk","content":"Hello"}\n\n
```

Two newlines terminate a frame. Miss one and the browser waits forever for a frame that never completes — a failure that looks like "streaming does not work" and is one character.

### The frontend

```javascript
const source = new EventSource('/chat/stream?message=' + encodeURIComponent(text));

source.onmessage = (e) => {
    const chunk = JSON.parse(e.data);

    if (chunk.type === 'TextChunk') {
        output.textContent += chunk.content;
    }
};

source.addEventListener('done', () => source.close());

source.onerror = () => source.close();
```

**`EventSource` only does GET.** For a POST body you either use `fetch()` with a `ReadableStream` reader, or accept the message as a query parameter — which caps your message length and puts user content in access logs. For anything real, use `fetch`.

### Key takeaways

- SSE fits agent output: one-directional, plain HTTP, auto-reconnect.
- Four headers; `X-Accel-Buffering: no` is the one that saves a day.
- Frames end with two newlines.
- `EventSource` is GET-only — use `fetch` with a stream reader for POST.

---
═══════════════════════════════════════════════════════════════

## LESSON 21.2 — The Buffering Problem

**Duration:** 12 minutes
**Type:** Hands-on troubleshooting

### Learning objectives

Diagnose and fix output buffering at every layer of a PHP stack.

### The symptom

You implemented streaming correctly. It works from the CLI (Lesson 7.3). In the browser, nothing appears for twelve seconds and then the entire response arrives at once.

Something between your `echo` and the browser is holding the bytes.

### The four layers

**Layer 1 — PHP output buffering.**

```ini
; php.ini
output_buffering = Off
implicit_flush = On
```

Or in the stream callback:

```php
while (\ob_get_level() > 0) {
    \ob_end_flush();
}
```

Laravel may open buffers in middleware; the loop closes whatever exists rather than assuming one.

**Layer 2 — PHP-FPM / the web server.**

nginx buffers FastCGI responses by default:

```nginx
location ~ \.php$ {
    fastcgi_pass   unix:/var/run/php/php8.3-fpm.sock;
    fastcgi_buffering off;
    fastcgi_read_timeout 300s;
    # ...
}
```

`fastcgi_buffering off` for the whole location, or the `X-Accel-Buffering: no` header per response. The header is better — it scopes the change to the endpoints that need it, and the rest of your site keeps the performance benefit of buffering.

`fastcgi_read_timeout` matters too: the default 60 seconds will cut off a long agent run mid-stream.

**Layer 3 — Reverse proxy.**

```nginx
location /chat/stream {
    proxy_pass http://app;
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 300s;
    proxy_set_header Connection '';
    proxy_http_version 1.1;
}
```

`proxy_http_version 1.1` plus an empty `Connection` header keeps the upstream connection alive.

**Layer 4 — CDN or WAF.**

Cloudflare, Fastly and similar may buffer. Cloudflare respects `text/event-stream` in most configurations, but verify rather than assume. Some WAF rules inspect the full body before forwarding, which is buffering by another name.

### The diagnostic procedure

Bisect from the inside out — this is the part worth recording, because it turns a frustrating afternoon into five minutes:

```bash
# 1. PHP alone. Does it stream?
php -r 'for($i=0;$i<5;$i++){echo "chunk $i\n";flush();sleep(1);}'

# 2. Through PHP-FPM and the web server, bypassing any proxy
curl -N http://127.0.0.1:8080/chat/stream

# 3. Through the full public stack
curl -N https://app.example.com/chat/stream
```

`curl -N` disables curl's own buffering. Whichever step first fails to stream is your culprit — and you have narrowed four layers to one without touching a config file.

### The framework's own warning

The AG-UI documentation says it directly: send the protocol headers and flush after each line, or the stream can get stuck in PHP output buffers or proxies.

They warn about it because everyone hits it.

### Key takeaways

- Four buffering layers: PHP, FPM/web server, proxy, CDN.
- Prefer the `X-Accel-Buffering` header over a global `fastcgi_buffering off`.
- Raise read timeouts — the default 60s cuts long runs.
- Bisect with `curl -N` from inside out.

---
═══════════════════════════════════════════════════════════════

## LESSON 21.3 — Streaming with Livewire

**Duration:** 12 minutes
**Type:** Hands-on

### Learning objectives

Build a streaming chat component without writing JavaScript.

### The component

```php
<?php

declare(strict_types=1);

namespace App\Livewire;

use App\Neuron\Agents\SupportAgent;
use Livewire\Component;
use NeuronAI\Chat\Messages\UserMessage;

class Chat extends Component
{
    public string $input = '';
    public string $answer = '';
    public ?string $activity = null;
    public array $history = [];

    public function send(SupportAgent $agent): void
    {
        $question = \trim($this->input);

        if ($question === '') {
            return;
        }

        $this->history[] = ['role' => 'user', 'content' => $question];
        $this->input     = '';
        $this->answer    = '';

        $handler = $agent->stream(new UserMessage($question));

        foreach ($handler->events() as $chunk) {
            if ($chunk instanceof ToolCallChunk) {
                $this->activity = $this->label($chunk->tool->getName());
                $this->stream(to: 'activity', content: $this->activity, replace: true);
                continue;
            }

            if ($chunk instanceof ToolResultChunk) {
                continue;
            }

            $this->answer .= $chunk->content;
            $this->stream(to: 'answer', content: $chunk->content);
        }

        $this->activity  = null;
        $this->history[] = ['role' => 'assistant', 'content' => $this->answer];
    }

    private function label(string $tool): string
    {
        return [
            'search_orders'     => 'Looking through your orders',
            'get_order_status'  => 'Checking that order',
            'request_refund'    => 'Preparing a refund request',
        ][$tool] ?? 'Working on it';
    }

    public function render()
    {
        return view('livewire.chat');
    }
}
```

### The view

```blade
<div class="space-y-4">
    @foreach ($history as $message)
        <div @class(['text-right' => $message['role'] === 'user'])>
            {{ $message['content'] }}
        </div>
    @endforeach

    <div wire:stream="activity" class="text-sm text-gray-500 italic">
        {{ $activity }}
    </div>

    <div wire:stream="answer" class="whitespace-pre-wrap">
        {{ $answer }}
    </div>

    <form wire:submit="send" class="flex gap-2">
        <input wire:model="input" class="flex-1 border rounded px-3 py-2" autofocus>
        <button type="submit" class="px-4 py-2 bg-black text-white rounded">Send</button>
    </form>
</div>
```

### Why this is the sweet spot for most Laravel teams

`$this->stream(to: 'answer', content: $chunk->content)` pushes to `wire:stream="answer"` in the view. Livewire handles the SSE transport, the reconnection and the DOM updates.

No `EventSource`, no `fetch` reader, no manual frame parsing. For a team that does not want to maintain a JavaScript frontend, this is roughly thirty lines of PHP for a complete streaming chat.

**Note `replace: true` for the activity line** and its absence for the answer. Activity is a status that overwrites; the answer accumulates. Getting these backwards is the most common Livewire streaming bug.

### The label allowlist, again

`$this->label()` maps tool names to user-facing text, with `?? 'Working on it'` as the fallback.

Lesson 7.4's rule: never show raw tool names or results. A new tool added next month degrades to the generic message rather than leaking `internal_pricing_lookup` to a customer. Allowlists fail safe — the same argument as `only()` over `exclude()` in Lesson 5.8.

### The limitation to know

The agent runs inside a Livewire request, so PHP-FPM's `max_execution_time` and the web server's timeouts apply. Fine for a 15-second chat response. Not fine for a two-minute multi-agent workflow — that belongs on a queue with a different transport, which is Lesson 21.5.

### Key takeaways

- `$this->stream(to:, content:)` plus `wire:stream` — Livewire handles the transport.
- `replace: true` for status, omitted for accumulating text.
- Map tool names through an allowlist with a safe fallback.
- Bounded by web request timeouts; long runs need a queue.

---
═══════════════════════════════════════════════════════════════

## LESSON 21.4 — SPA Frontends and Protocol Adapters

**Duration:** 12 minutes
**Type:** Hands-on

### Learning objectives

Connect a React, Vue or Angular frontend using the adapters from Lesson 7.5.

### The endpoint

```php
<?php

declare(strict_types=1);

namespace App\Http\Controllers;

use App\Neuron\Agents\SupportAgent;
use Illuminate\Http\Request;
use NeuronAI\Chat\Messages\Stream\Adapters\AGUIAdapter;
use NeuronAI\Chat\Messages\UserMessage;
use Symfony\Component\HttpFoundation\StreamedResponse;

class AgentUiController extends Controller
{
    public function __invoke(Request $request, SupportAgent $agent): StreamedResponse
    {
        $input = $request->validate([
            'threadId'           => ['required', 'string'],
            'runId'              => ['required', 'string'],
            'messages'           => ['required', 'array'],
            'messages.*.role'    => ['required', 'string'],
            'messages.*.content' => ['required', 'string'],
        ]);

        $messages = \collect($input['messages'])
            ->where('role', 'user')
            ->map(fn (array $m) => new UserMessage($m['content']))
            ->all();

        $adapter = new AGUIAdapter(
            threadId: $input['threadId'],
            runId: $input['runId'],
        );

        return response()->stream(function () use ($agent, $messages, $adapter) {
            foreach ($agent->stream($messages)->events($adapter) as $line) {
                echo $line;
                \flush();
            }
        }, 200, \array_merge($adapter->getHeaders(), [
            'X-Accel-Buffering' => 'no',
        ]));
    }
}
```

### Four things worth pointing out

**`getHeaders()` supplies the protocol headers.** Merge in `X-Accel-Buffering` yourself — Lesson 21.2's nginx fix is not the adapter's concern.

**Echo `threadId` and `runId` back.** Lesson 7.5 established that omitting them makes the adapter invent its own, which means the client cannot correlate the stream with the run it requested.

**Validate the payload.** It arrives from a browser. The `messages` array is user input like any other.

**Swap the adapter, keep everything else.** `VercelAIAdapter` in place of `AGUIAdapter` and the same agent serves a different frontend protocol. Lesson 2.2's interface argument, applied on the output side.

### The two limitations, restated

From Lesson 7.5, because a team choosing a frontend needs to know before they commit:

**Server-side tools only.** Tools attached to your agent run on your server; the client is informed via `TOOL_CALL_*` events. AG-UI's *frontend-defined* tools — declared in the `tools` field of `RunAgentInput` and executed by the client — are not handled.

**No shared-state events.** The adapter does not emit `STATE_SNAPSHOT`, `STATE_DELTA` or `MESSAGES_SNAPSHOT`, so client-side state synchronisation features are unavailable through it.

If you are evaluating CopilotKit or a similar AG-UI frontend, check whether your design depends on either. Better to find out now than after the frontend is built.

### Authentication

An SPA sends a token; Sanctum or Passport handles it as usual. The important part is that the *agent* is resolved for the authenticated user:

```php
$this->app->bind(SupportAgent::class, function ($app) {
    return new SupportAgent(
        tenant: $app['auth']->user()->tenant,
        user:   $app['auth']->user(),
    );
});
```

Tool visibility, chat history and RAG filters all follow from that binding. Lesson 18.1's argument, and the reason the controller stays this short.

### Key takeaways

- `->events($adapter)` plus `$adapter->getHeaders()`; add `X-Accel-Buffering` yourself.
- Echo `threadId` and `runId` so the client can correlate.
- Two AG-UI gaps: no frontend-defined tools, no state-sync events.
- Resolve the agent per authenticated user; everything else follows.

---
═══════════════════════════════════════════════════════════════

## LESSON 21.5 — Streaming from a Queue

**Duration:** 13 minutes
**Type:** Hands-on — the pattern that ties Parts IV and V together

### Learning objectives

Stream progress from a workflow running on a worker, to a browser it has no connection to.

### The problem

Lesson 16.4 established that long runs belong on a queue. But a queue worker has no HTTP connection to the user — so how does progress reach the browser?

### The architecture

```
Browser  → POST /workflows   → dispatch job → returns { workflowId }
Browser  → subscribes to a private channel for that workflowId
Worker   → runs the workflow → broadcasts each progress event
Browser  → renders progress live
Worker   → finishes → broadcasts completion
```

### The job

```php
<?php

declare(strict_types=1);

namespace App\Jobs;

use App\Events\WorkflowProgressed;
use App\Neuron\Workflows\ContentWorkflow;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use NeuronAI\Workflow\Exceptions\WorkflowInterrupt;
use NeuronAI\Workflow\Persistence\EloquentPersistence;
use NeuronAI\Laravel\Models\WorkflowInterrupt as WorkflowInterruptModel;

class RunContentWorkflow implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $timeout = 600;
    public int $tries = 1;   // agent runs are expensive — do not blind-retry

    public function __construct(
        public readonly string $workflowId,
        public readonly int $tenantId,
        public readonly string $topic,
    ) {}

    public function handle(): void
    {
        $workflow = new ContentWorkflow(
            persistence: new EloquentPersistence(WorkflowInterruptModel::class),
            workflowId: $this->workflowId,
        );

        try {
            $handler = $workflow->init();

            foreach ($handler->events() as $event) {
                WorkflowProgressed::dispatch(
                    $this->workflowId,
                    $event->message ?? '',
                );
            }

            WorkflowCompleted::dispatch($this->workflowId, $handler->getResult());

        } catch (WorkflowInterrupt $interrupt) {
            PendingApproval::create([
                'workflow_id' => $interrupt->getWorkflowId(),
                'tenant_id'   => $this->tenantId,
                'request'     => \json_encode($interrupt->getRequest()),
                'status'      => 'pending',
            ]);

            WorkflowPaused::dispatch($this->workflowId);
        }
    }
}
```

### The broadcast event

```php
class WorkflowProgressed implements ShouldBroadcastNow
{
    public function __construct(
        public readonly string $workflowId,
        public readonly string $message,
    ) {}

    public function broadcastOn(): PrivateChannel
    {
        return new PrivateChannel("workflows.{$this->workflowId}");
    }
}
```

**`ShouldBroadcastNow`, not `ShouldBroadcast`.** The latter queues the broadcast, which means your progress updates queue behind the job that is producing them. On a single worker that is a deadlock in slow motion.

### The channel authorisation

```php
// routes/channels.php
Broadcast::channel('workflows.{workflowId}', function ($user, string $workflowId) {
    return WorkflowRun::where('id', $workflowId)
        ->where('tenant_id', $user->tenant_id)
        ->exists();
});
```

Without this, anyone who guesses a workflow ID watches someone else's agent work. Lesson 18.3's four leak points had a fifth cousin: the broadcast channel.

### The frontend

```javascript
Echo.private(`workflows.${workflowId}`)
    .listen('WorkflowProgressed', (e) => {
        progressList.append(`<li>${e.message}</li>`);
    })
    .listen('WorkflowPaused', () => {
        showMessage('Waiting for approval.');
    })
    .listen('WorkflowCompleted', (e) => {
        showResult(e.result);
    });
```

### What this composes

Worth listing on a slide, because this single job is the course converging:

- Workflow streaming with `yield` (14.4)
- Interruption and persistence (15.4)
- Eloquent persistence (18.4)
- Async execution (16.4)
- Adapters pushing to an external transport (7.5)
- `pcntl` available, so parallel tools work (5.13)
- Inspector needs `autoFlush: true` here (10.2)

That last one is the misconfiguration most likely to bite: without it the worker accumulates trace events and never ships them, because there is no end-of-request.

### Key takeaways

- Dispatch, return an ID, subscribe to a private channel, broadcast progress.
- `ShouldBroadcastNow` — queued broadcasts deadlock behind the producing job.
- Authorise the channel by tenant.
- `$tries = 1` on agent jobs; blind retries re-spend money.
- `autoFlush: true` for Inspector on workers.

---
═══════════════════════════════════════════════════════════════

## LESSON 21.6 — Disconnection and Orphaned Cost

**Duration:** 9 minutes
**Type:** Theory with code

### Learning objectives

Stop paying for work nobody is waiting for.

### The problem nobody mentions

A user starts a 30-second agent run. At second four they close the tab.

The browser is gone. **The agent keeps running.** Every remaining model call is billed. In a multi-agent workflow that is a substantial amount of money spent on output nobody will ever read.

At low volume this is invisible. At scale it is a line item.

### Detecting it in a streamed response

```php
return response()->stream(function () use ($agent, $message) {
    $handler = $agent->stream(new UserMessage($message));

    foreach ($handler->events() as $chunk) {
        if (\connection_aborted()) {
            \Log::info('Client disconnected — stopping agent run');
            break;
        }

        echo 'data: ' . \json_encode(['content' => $chunk->content]) . "\n\n";
        \flush();
    }
}, 200, $headers);
```

`connection_aborted()` requires that you have written to the connection — PHP only detects the broken pipe on a write attempt. Since you are streaming, you are writing, so this works. It would not work in a non-streaming endpoint.

**One honest caveat:** breaking out of the loop stops *your* iteration. A model call already in flight completes and is billed. You are limiting the damage, not eliminating it.

### For queued workflows

A disconnected browser does not stop a worker, and it should not — the user may come back, and the result is worth having. But there are cases where cancellation is right:

```php
public function handle(): void
{
    foreach ($handler->events() as $event) {
        if (Cache::has("workflow:{$this->workflowId}:cancelled")) {
            $this->recordCancellation();
            return;
        }

        WorkflowProgressed::dispatch(/* ... */);
    }
}
```

```php
// A cancel endpoint
Cache::put("workflow:{$id}:cancelled", true, now()->addHour());
```

Explicit cancellation, not inferred from disconnection.

### Budget guards

The complement, and the thing that actually caps exposure:

```php
class BudgetMiddleware
{
    public function handle($request, Closure $next)
    {
        $spent = Cache::get("ai_spend:{$request->user()->id}:" . today()->toDateString(), 0);

        if ($spent > config('neuron.daily_user_budget')) {
            abort(429, 'Daily AI usage limit reached.');
        }

        return $next($request);
    }
}
```

Record actual usage from the response's token counts after each run. Lesson 1.3 said capture usage from the first prototype; this is what you capture it for.

### Key takeaways

- A closed tab does not stop an agent — you keep paying.
- `connection_aborted()` inside the stream loop limits the damage.
- Queued work should be cancelled explicitly, not inferred.
- Per-user daily budgets cap exposure; they need the token counts you have been logging.

---
═══════════════════════════════════════════════════════════════
# MODULE 22 — WORKFLOWS AND HUMAN APPROVAL IN PRODUCTION
═══════════════════════════════════════════════════════════════
---

## LESSON 22.1 — The Approval Lifecycle

**Duration:** 12 minutes
**Type:** Theory with schema

### Learning objectives

Design the full lifecycle of a paused workflow as ordinary application state.

### The insight from Lesson 18.4, expanded

Because interrupts are Eloquent rows, "the AI is waiting for a human" is a record in your database. Which means it gets everything database records get: a status, an owner, a deadline, an index page, a policy, an audit trail.

**Human-in-the-loop stops being an AI feature and becomes a workflow feature of your application.** That reframing is the point of this module.

### The supporting table

The package's `WorkflowInterrupt` holds the serialised execution state. You want a companion table holding the *business* view:

```php
Schema::create('pending_approvals', function (Blueprint $table) {
    $table->id();
    $table->string('workflow_id')->unique();
    $table->foreignId('tenant_id')->constrained();
    $table->foreignId('requested_by')->nullable()->constrained('users');
    $table->foreignId('resolved_by')->nullable()->constrained('users');

    $table->string('type');                 // refund, publish, escalation
    $table->string('subject_type')->nullable();
    $table->unsignedBigInteger('subject_id')->nullable();

    $table->json('request');                // the serialised InterruptRequest
    $table->json('response')->nullable();   // what the human decided

    $table->string('status')->default('pending');   // pending|approved|rejected|expired
    $table->timestamp('expires_at')->nullable();
    $table->timestamp('resolved_at')->nullable();

    $table->timestamps();

    $table->index(['tenant_id', 'status']);
    $table->index('expires_at');
});
```

**Why two tables.** The framework's table is a serialised blob — you cannot query it, filter it, or authorise against it. Yours is a normal record you can index, scope and render. Separating them means the framework owns its internals and you own your product.

Also worth noting: `subject_type` / `subject_id` is a morph, so an approval links to the order, article or invoice it concerns. Without it, your approval screen shows an opaque JSON payload and the approver has to go and find the record themselves.

### The states

```
pending ──approve──→ approved ──→ (workflow resumed) ──→ completed
   │
   ├────reject───→ rejected ──→ (workflow resumed with rejection)
   │
   └────timeout──→ expired ──→ (escalated or abandoned)
```

**Rejection resumes the workflow too.** That is the point of Lesson 15.2's loop-back: rejection with feedback is another iteration, not a dead end.

### The four questions, answered

Lesson 15.4 posed them. Here are the Laravel answers, which the next lessons build:

| Question | Answer |
|---|---|
| Who is notified? | A `Notification` dispatched in the catch block (22.2) |
| What if nobody responds? | `expires_at` plus a scheduled command (22.4) |
| How to prevent double-resume? | `lockForUpdate()` on the status column (22.3) |
| What about deployments? | Small, flat, rarely-changed interrupt requests (22.4) |

### Key takeaways

- Interrupts are rows, so approvals are ordinary application state.
- Two tables: the framework's serialised blob and your queryable business record.
- Morph to the subject so approvers see what they are deciding about.
- Rejection resumes the workflow; it is not a terminal state.

---
═══════════════════════════════════════════════════════════════

## LESSON 22.2 — Catching and Notifying

**Duration:** 12 minutes
**Type:** Hands-on

### Learning objectives

Turn a `WorkflowInterrupt` into a decision waiting in someone's inbox.

### The catch block

```php
public function handle(): void
{
    $workflow = new RefundWorkflow(
        persistence: new EloquentPersistence(WorkflowInterrupt::class),
        workflowId: $this->workflowId,
    );

    try {
        $handler = $workflow->init();
        $handler->run();

        $this->recordCompletion($handler->getResult());

    } catch (WorkflowInterrupt $interrupt) {
        $approval = PendingApproval::create([
            'workflow_id'  => $interrupt->getWorkflowId(),
            'tenant_id'    => $this->tenantId,
            'type'         => 'refund',
            'subject_type' => Order::class,
            'subject_id'   => $this->orderId,
            'request'      => \json_encode($interrupt->getRequest()),
            'status'       => 'pending',
            'expires_at'   => now()->addHours(48),
        ]);

        Notification::send(
            $this->approversFor($approval),
            new ApprovalRequired($approval)
        );
    }
}
```

### Who to notify

```php
private function approversFor(PendingApproval $approval): Collection
{
    return User::query()
        ->where('tenant_id', $approval->tenant_id)
        ->whereHas('roles', fn ($q) => $q->where('name', 'approver'))
        ->get();
}
```

Role-based, tenant-scoped. Extend it with thresholds — a €50 refund goes to a supervisor, a €5,000 refund goes to a manager — using the amount already in the request payload.

### The notification

```php
class ApprovalRequired extends Notification implements ShouldQueue
{
    use Queueable;

    public function __construct(
        private readonly PendingApproval $approval,
    ) {}

    public function via(object $notifiable): array
    {
        return ['mail', 'database'];
    }

    public function toMail(object $notifiable): MailMessage
    {
        $request = \json_decode($this->approval->request, true);

        return (new MailMessage())
            ->subject("Approval needed: {$request['message']}")
            ->line($request['message'])
            ->action('Review', route('approvals.show', $this->approval))
            ->line('This request expires ' . $this->approval->expires_at->diffForHumans() . '.');
    }
}
```

### Two design points

**Include enough in the email to decide — but decide in the app.**

The subject line and body should tell the approver what this is about, so they can triage without clicking. The decision itself happens on an authenticated page, because that is where you can authorise it, lock it and audit it.

Resist one-click approve/reject links in email. They are convenient and they are a signed-URL security surface you now have to get right.

**State the expiry.** An approver who knows the request expires in 48 hours behaves differently from one who does not. It also makes Lesson 22.4's timeout policy visible rather than surprising.

### Key takeaways

- Create the business record and notify in the catch block.
- Route approvers by role, tenant and threshold.
- Email for awareness; decide in the authenticated application.
- Tell the approver when it expires.

---
═══════════════════════════════════════════════════════════════

## LESSON 22.3 — The Approval Screen and Safe Resume

**Duration:** 14 minutes
**Type:** Hands-on

### Learning objectives

Build the decision interface and resume the workflow without double-executing.

### The index

```php
class ApprovalsController extends Controller
{
    public function index(Request $request)
    {
        $approvals = PendingApproval::query()
            ->where('tenant_id', $request->user()->tenant_id)
            ->where('status', 'pending')
            ->with('subject')
            ->latest()
            ->paginate(20);

        return view('approvals.index', compact('approvals'));
    }

    public function show(PendingApproval $approval)
    {
        $this->authorize('resolve', $approval);

        return view('approvals.show', [
            'approval' => $approval,
            'request'  => \json_decode($approval->request, true),
        ]);
    }
}
```

An index page with a policy. Nothing exotic — which is the point.

### The resolve action, with the lock

```php
public function resolve(Request $request, PendingApproval $approval)
{
    $this->authorize('resolve', $approval);

    $validated = $request->validate([
        'decision' => ['required', 'in:approve,reject'],
        'feedback' => ['nullable', 'string', 'max:2000'],
        'content'  => ['nullable', 'string'],   // for editable interrupts
    ]);

    $locked = DB::transaction(function () use ($approval, $validated, $request) {
        $fresh = PendingApproval::whereKey($approval->id)
            ->lockForUpdate()
            ->first();

        if ($fresh->status !== 'pending') {
            return null;   // someone else already decided
        }

        $fresh->update([
            'status'      => $validated['decision'] === 'approve' ? 'approved' : 'rejected',
            'response'    => \json_encode($validated),
            'resolved_by' => $request->user()->id,
            'resolved_at' => now(),
        ]);

        return $fresh;
    });

    if ($locked === null) {
        return back()->with('warning', 'This request was already resolved by someone else.');
    }

    ResumeWorkflow::dispatch($locked->workflow_id, $validated);

    return redirect()
        ->route('approvals.index')
        ->with('status', 'Decision recorded. The workflow is continuing.');
}
```

### The three things this gets right

**`lockForUpdate()` inside a transaction.** Two managers open the same email and both click approve. Without the lock, both dispatch a resume job and the workflow runs twice — which for a refund means paying twice.

**Status checked *after* acquiring the lock.** Checking before is a race; the check must happen while holding the lock.

**Resume is dispatched, not executed inline.** The controller records a decision and returns. Resuming may take a minute; the approver should not wait for it, and an HTTP timeout should not orphan the workflow.

That third point is easy to skip and it is the difference between a screen that feels instant and one that hangs.

### The resume job

```php
class ResumeWorkflow implements ShouldQueue
{
    public int $tries = 1;

    public function __construct(
        public readonly string $workflowId,
        public readonly array $decision,
    ) {}

    public function handle(): void
    {
        $workflow = new RefundWorkflow(
            persistence: new EloquentPersistence(WorkflowInterrupt::class),
            workflowId: $this->workflowId,
        );

        $request = RefundApprovalInterrupt::fromArray($this->decision);

        $result = $workflow->init($request)->run();

        WorkflowCompleted::dispatch($this->workflowId, $result);
    }
}
```

Lesson 15.4's three requirements: same persistence, same workflow ID, reconstructed request.

### The editable case

For a `ContentReviewInterrupt` (Lesson 15.3), the screen is a textarea:

```blade
<form method="POST" action="{{ route('approvals.resolve', $approval) }}">
    @csrf

    <p class="mb-3">{{ $request['message'] }}</p>

    <textarea name="content" rows="20" class="w-full border rounded p-3">{{ $request['content'] }}</textarea>

    <div class="mt-4 flex gap-2">
        <button name="decision" value="approve" class="px-4 py-2 bg-black text-white rounded">
            Approve and publish
        </button>
        <button name="decision" value="reject" class="px-4 py-2 border rounded">
            Send back with feedback
        </button>
    </div>
</form>
```

The human edits the content; the edited version goes back into the workflow. Lesson 15.3's collaboration pattern, in a form. This is far more useful than approve/reject for anything the AI drafted — because the common response is "almost".

### Key takeaways

- `lockForUpdate()` in a transaction; check status while holding the lock.
- Record the decision, dispatch the resume — never resume inline.
- Same persistence, same ID, reconstructed request.
- For drafted content, a textarea beats two buttons.

---
═══════════════════════════════════════════════════════════════

## LESSON 22.4 — Timeouts, Zombies and Deployments

**Duration:** 13 minutes
**Type:** Hands-on

### Learning objectives

Keep a system with pausable workflows healthy over months.

### Expiring stale approvals

```php
class ExpireStaleApprovals extends Command
{
    protected $signature = 'approvals:expire';

    public function handle(): int
    {
        PendingApproval::query()
            ->where('status', 'pending')
            ->where('expires_at', '<', now())
            ->chunkById(100, function ($approvals) {
                foreach ($approvals as $approval) {
                    $approval->update([
                        'status'      => 'expired',
                        'resolved_at' => now(),
                    ]);

                    ResumeWorkflow::dispatch($approval->workflow_id, [
                        'decision' => 'reject',
                        'feedback' => 'No response received within the approval window.',
                    ]);
                }
            });

        return self::SUCCESS;
    }
}
```

**Resume with a rejection rather than abandoning.** An abandoned workflow leaves its serialised state in the database forever and never tells anyone what happened. A rejected one completes, notifies, and cleans up.

Schedule it:

```php
Schedule::command('approvals:expire')->hourly();
```

### Escalation before expiry

Better product behaviour than a silent timeout:

```php
Schedule::call(function () {
    PendingApproval::where('status', 'pending')
        ->where('created_at', '<', now()->subHours(24))
        ->whereNull('escalated_at')
        ->each(function ($approval) {
            Notification::send($approval->escalationTargets(), new ApprovalOverdue($approval));
            $approval->update(['escalated_at' => now()]);
        });
})->hourly();
```

Nudge at 24 hours, expire at 48.

### Orphaned interrupt rows

The framework's `workflow_interrupts` table grows. Clean up rows whose business record is resolved:

```php
WorkflowInterrupt::query()
    ->whereNotIn('workflow_id', function ($q) {
        $q->select('workflow_id')
          ->from('pending_approvals')
          ->where('status', 'pending');
    })
    ->where('updated_at', '<', now()->subDays(30))
    ->delete();
```

30 days of grace, then remove. Without this, a busy system accumulates serialised blobs indefinitely.

### The deployment problem, and how to live with it

Lesson 15.4 flagged it; here is the practical handling.

The serialised state contains **your classes**. Rename a node, add a typed property to a state class, change an interrupt request's constructor — and deserialisation of in-flight workflows breaks.

Four mitigations, in order of usefulness:

**1. Keep interrupt requests small and flat.** Strings, numbers, arrays. No models, no connections, no closures. The smaller the surface, the less there is to break.

**2. Version them.**

```php
class RefundApprovalInterrupt extends InterruptRequest
{
    public const VERSION = 2;

    public function jsonSerialize(): array
    {
        return [
            'version' => self::VERSION,
            'message' => $this->message,
            'amount'  => $this->amount,
        ];
    }

    public static function fromArray(array $data): static
    {
        return match ($data['version'] ?? 1) {
            1       => new static($data['message'], (float) $data['amount']),
            default => new static($data['message'], (float) $data['amount']),
        };
    }
}
```

**3. Drain before risky deploys.** For a release that changes workflow classes, stop dispatching new workflows, let pending ones resolve, then deploy.

**4. Fail loudly.** Wrap the resume in a try/catch, log the deserialisation failure with the workflow ID, and mark the approval as `failed` rather than leaving it pending forever. A visible failure is recoverable; a silent one is not.

### Monitoring

Four numbers worth a dashboard:

- Pending approvals, by age
- Approvals expired in the last 7 days *(a rising number means your process is broken, not your code)*
- Failed resumes
- Orphaned interrupt rows

### Key takeaways

- Expire by resuming with a rejection, never by abandoning.
- Escalate before expiring.
- Clean orphaned interrupt rows after a grace period.
- Serialised state contains your classes — keep requests flat, version them, drain before risky deploys.
- Fail loudly on deserialisation errors.

---
═══════════════════════════════════════════════════════════════
# MODULE 23 — PRODUCTION
═══════════════════════════════════════════════════════════════
---

## LESSON 23.1 — Cost Control

**Duration:** 14 minutes
**Type:** Hands-on

### Learning objectives

Measure, cap and reduce AI spend.

### Measure first

You cannot manage what you do not record. Log usage on every run:

```php
class LogUsage
{
    public function handle($event): void
    {
        AiUsage::create([
            'tenant_id'     => $event->tenantId,
            'user_id'       => $event->userId,
            'agent'         => $event->agentClass,
            'provider'      => $event->provider,
            'model'         => $event->model,
            'input_tokens'  => $event->usage->inputTokens,
            'output_tokens' => $event->usage->outputTokens,
            'tool_calls'    => $event->toolCalls,
            'duration_ms'   => $event->durationMs,
        ]);
    }
}
```

*(Confirm the usage accessor on the response object in your installed version.)*

Four questions this answers that nothing else will:

- Which agent costs the most?
- Which user or tenant costs the most?
- Is cost per request rising over time?
- Did last week's prompt change make things cheaper or more expensive?

### The three levers, revisited

Lesson 1.4 named them. In production they look like this:

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

**Embedding caching is the biggest win in RAG.** Text that has not changed does not need re-embedding — which is exactly what the `wasChanged('body')` guard in Lesson 20.2 was for.

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

**Also set a hard spend limit at the provider.** Lesson 3.7 said it and it bears repeating: application-level budgets depend on your code being correct. The provider's cap does not.

### Key takeaways

- Log tokens, model, agent and duration on every run.
- Three levers: fewer iterations, smaller context, cheaper model per step.
- Cache deterministic tasks and embeddings; not conversations.
- Three budget tiers plus a hard cap at the provider.

---
═══════════════════════════════════════════════════════════════

## LESSON 23.2 — Resilience

**Duration:** 13 minutes
**Type:** Hands-on

### Learning objectives

Survive rate limits, timeouts and provider outages.

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

```php
'timeout' => env('NEURON_HTTP_TIMEOUT', 60),
```

Set them deliberately. An agent making five calls at a 120-second timeout can hang for ten minutes before failing, occupying a worker the whole time.

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

This is why Lesson 21.5 set `$tries = 1` on the workflow job. For agent work, idempotency (19.2) plus deliberate retry beats a generous retry count.

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

**Two caveats worth stating so this does not look like a free lunch:**

**Quality varies across providers.** A prompt tuned for one model may perform noticeably worse on another. Fallback keeps you available; it does not keep you equally good. Run your evals (Module 10) against every provider in the chain so you know what you are degrading to.

**Some features are not portable.** Provider tools (5.12) simply vanish. If an agent depends on one, it has no fallback.

### Degrading gracefully

Sometimes the right answer is not another provider:

```php
try {
    return $this->agent->chat(new UserMessage($question))->getMessage()->getContent();
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

---
═══════════════════════════════════════════════════════════════

## LESSON 23.3 — Observability in Production

**Duration:** 12 minutes
**Type:** Hands-on

### Learning objectives

Know what your agents are doing once real users are using them.

### Inspector, with the Laravel package

```bash
composer require inspector-apm/inspector-laravel
```

The Neuron SDK suggests it explicitly. Adding it correlates the agent trace with the HTTP request, the queries and the queue job around it — which is what you actually want when diagnosing an incident. Without it you have an agent timeline floating unattached to the request that produced it.

```dotenv
INSPECTOR_INGESTION_KEY=...
```

**And on workers:**

```php
$this->observe(
    InspectorObserver::instance(
        key: config('inspector.key'),
        autoFlush: true
    )
);
```

Lesson 10.2's warning, for the third and final time: without `autoFlush`, traces from queue workers never arrive.

### What to alert on

Four signals, and none of them are "an exception occurred":

**Tool run limits exceeded.** Lesson 5.9 said this is a diagnostic about tool design. A spike means a description has stopped working — often because the underlying data changed shape.

**Faithfulness score dropping.** From your eval suite (10.5), running nightly. A drop means retrieval quality has degraded, usually because content changed and the index did not keep up.

**Cost per request rising.** Loops getting longer, context growing, or a prompt change that made the model chattier.

**Approval backlog growing.** Not a code problem — a process problem, and one your dashboard will surface before anyone complains.

### What to log, and what not to

**Log:** agent class, provider, model, token counts, duration, tool names, tool argument *shapes*, outcome, workflow ID, user and tenant IDs.

**Do not log by default:** full prompts, full responses, tool argument *values*, retrieved document contents.

Lesson 3.7 made this point; it deserves restating in a production module. Prompts contain whatever users typed — names, addresses, order numbers, occasionally payment details. Full-prompt logging at scale creates a compliance problem that is much harder to unwind than to avoid.

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

- Add `inspector-laravel` to correlate agent traces with requests and jobs.
- `autoFlush: true` on workers.
- Alert on run limits, faithfulness, cost per request and approval backlog.
- Log shapes and metadata; not prompt content.
- Correlate everything by workflow ID.

---
═══════════════════════════════════════════════════════════════

## LESSON 23.4 — Testing and CI

**Duration:** 13 minutes
**Type:** Hands-on

### Learning objectives

Build a test suite that is fast, free and deterministic, plus a slower one that measures quality.

### The three tiers

**Tier 1 — Unit tests. Fast, free, deterministic, run on every commit.**

Tools are ordinary callable objects (Lesson 5.3):

```php
public function test_it_scopes_orders_to_the_tenant(): void
{
    $tool = new SearchOrdersTool($this->tenantA);

    Order::factory()->for($this->tenantB)->create(['number' => 'B-001']);

    $result = $tool(status: 'shipped');

    $this->assertStringNotContainsString('B-001', $result);
}
```

No LLM. No network. This is where most of your agent-related logic should live, and the reason Lesson 5.3 argued for tool classes.

**Tier 2 — Integration tests with a fake provider.**

```php
$this->app->bind(SupportAgent::class, fn () => new FakeSupportAgent());

$this->postJson('/api/chat', ['message' => 'Where is my order?'])
     ->assertOk()
     ->assertJsonStructure(['answer']);
```

Tests your controller, your validation, your authorisation, your serialisation. Everything except the model.

*(The framework ships testing utilities — check the Testing page in the documentation for the current fake components and adjust this tier accordingly.)*

**Tier 3 — Evals. Slow, costs money, measures quality (Module 10).**

```bash
vendor/bin/neuron evaluations --path=evaluators
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
      - run: vendor/bin/neuron evaluations --path=evaluators --concurrency=5
        env:
          ANTHROPIC_KEY: ${{ secrets.ANTHROPIC_KEY }}
```

Three rules from Lesson 10.6, restated because they are easy to get wrong:

**Do not gate every PR on the full eval suite.** It costs money and it is slow. Nightly, plus opt-in with a commit tag.

**Do not fail on a single item.** Set a success-rate threshold. On a probabilistic system a 95% pass rate is a healthy build, and treating one flaky item as failure teaches the team to ignore the signal entirely.

**Keep API keys out of forks.** Eval-on-PR in a public repository is a way to donate your budget to strangers.

### The security tests that must gate deploys

Two from Part V, both deterministic enough to trust:

```php
public function test_tenant_isolation(): void;              // Lesson 18.3
public function test_restricted_articles_never_surface(): void;  // Lesson 20.3
```

These belong in tier 1 or 2, run on every commit, and block the merge. They are among the few AI-adjacent tests that are both reliable and consequential.

### Key takeaways

- Three tiers: unit (every commit), integration with fakes (every commit), evals (nightly).
- Tools are testable without an LLM — put logic there.
- Threshold on success rate, not pass/fail per item.
- Tenant isolation and permission-filtered retrieval gate every deploy.

---
═══════════════════════════════════════════════════════════════

## LESSON 23.5 — Security and Privacy

**Duration:** 14 minutes
**Type:** Theory with checklist

### Learning objectives

Assemble the security posture from everything the course has built, and know which questions need a lawyer rather than an engineer.

### The layered model, assembled

| Layer | Mechanism | Lesson |
|---|---|---|
| Capability | Only register tools this user may use | 5.1 |
| Visibility | `visible()` from policies | 5.10, 19.3 |
| Authorisation | `Gate::forUser()` inside the tool | 19.3 |
| Approval | `ToolApproval` on consequential actions | 15.5 |
| Data scope | Tenant filters on tools and retrieval | 18.3, 20.3 |
| Privilege | Read-only database credentials | 19.3 |
| Audit | A row per consequential tool call | 19.3 |

**Every layer is independent.** A bug in one does not defeat the others — which is the whole point of defence in depth and worth stating explicitly, because students often ask "isn't visibility enough?".

### Prompt injection, one more time

The principle from Lesson 19.3, which is the security thesis of the entire course:

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

**Legal basis.** Sending personal data to a third-party processor needs one. That is a legal determination, not an engineering one — get counsel involved rather than deciding it in a sprint planning session.

**Data processing agreement.** With each provider you use.

**Right to erasure.** A user asks to be deleted. Their chat history is in your `chat_messages` table — deletable. Their data inside a provider's logs is subject to that provider's retention policy, which is why zero-retention matters.

**Right of access.** Chat history and any long-term memory (Lesson 4.5) are personal data the user can request.

**Automated decision-making.** If an agent makes a decision with legal or similarly significant effect on someone, GDPR Article 22 is relevant. This is a strong argument for human-in-the-loop on consequential actions — Module 15 is a compliance feature as well as a safety one.

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

---
═══════════════════════════════════════════════════════════════

## LESSON 23.6 — The Deployment Checklist

**Duration:** 12 minutes
**Type:** Checklist — the closing lesson of the main course

### Learning objectives

Have a concrete list to work through before an agentic feature goes live.

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

- [ ] `EloquentPersistence` for anything interruptible (18.4)
- [ ] Every pre-interrupt LLM call wrapped in `checkpoint()` (15.5)
- [ ] `lockForUpdate()` on approval resolution (22.3)
- [ ] `expires_at` set; expiry command scheduled (22.4)
- [ ] Interrupt requests small, flat and versioned (22.4)
- [ ] Orphaned interrupt cleanup scheduled (22.4)

### Operations

- [ ] Inspector configured; `autoFlush: true` on workers (10.2, 23.3)
- [ ] Token usage logged per run (23.1)
- [ ] Budgets: per user, per tenant, global (23.1)
- [ ] Rate limits configured before the provider's (23.2)
- [ ] `$tries = 1` on agent jobs, or idempotency proven (21.5, 23.2)
- [ ] Timeouts set at PHP, FPM, proxy and provider (21.2, 23.2)
- [ ] Streaming verified end to end with `curl -N` through the full stack (21.2)
- [ ] Broadcast channels authorised by tenant (21.5)

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

### Closing the main course

Twenty-three modules ago the first lesson drew a four-rung ladder and asked *who decides what happens next*. Everything since has been the machinery required to let a model answer that question safely: tools to give it hands, structure to make its output usable, retrieval to give it knowledge, workflows to give it shape, interruption to keep a human in the decision, and observability to find out what it actually did.

The last question on the checklist is the one worth leaving students with: **what is the worst thing it can do, and what stops it?** A developer who can answer that about their own system has understood this course.

### Key takeaways

- Work the checklist section by section; every item traces to a lesson.
- The five questions are the real exam.
- If an answer is a shrug, that is the next task.

---

**END OF PART V — END OF THE MAIN COURSE**

*Remaining: Part VI — Capstone A (Repo Auditor CLI) and Capstone B (Agentic Support Desk),
plus bonus modules B1 (Neuron v4), B2 (ecosystem: Maestro, Neuron Hub, Studio, Symfony/Spryker),
and B3 (AI-assisted development with MCP and Laravel Boost).*
