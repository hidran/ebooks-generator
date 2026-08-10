# Chapter 21 — Streaming to the Frontend

## 21.1 Server-Sent Events in Laravel

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

## 21.2 The Buffering Problem

### The symptom

You implemented streaming correctly. It works from the CLI (Section 7.3). In the browser, nothing appears for twelve seconds and then the entire response arrives at once.

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

**Layer 2 — PHP-FPM and the web server.**

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

Bisect from the inside out. This turns a frustrating afternoon into five minutes:

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
- Raise read timeouts — the default 60 s cuts long runs.
- Bisect with `curl -N` from inside out.

## 21.3 Streaming with Livewire

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

Section 7.4's rule: never show raw tool names or results. A new tool added next month degrades to the generic message rather than leaking `internal_pricing_lookup` to a customer. Allowlists fail safe — the same argument as `only()` over `exclude()` in Section 5.8.

### The limitation to know

The agent runs inside a Livewire request, so PHP-FPM's `max_execution_time` and the web server's timeouts apply. Fine for a 15-second chat response. Not fine for a two-minute multi-agent workflow — that belongs on a queue with a different transport, which is Section 21.5.

### Key takeaways

- `$this->stream(to:, content:)` plus `wire:stream` — Livewire handles the transport.
- `replace: true` for status, omitted for accumulating text.
- Map tool names through an allowlist with a safe fallback.
- Bounded by web request timeouts; long runs need a queue.

## 21.4 SPA Frontends and Protocol Adapters

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

**`getHeaders()` supplies the protocol headers.** Merge in `X-Accel-Buffering` yourself — Section 21.2's nginx fix is not the adapter's concern.

**Echo `threadId` and `runId` back.** Section 7.5 established that omitting them makes the adapter invent its own, which means the client cannot correlate the stream with the run it requested.

**Validate the payload.** It arrives from a browser. The `messages` array is user input like any other.

**Swap the adapter, keep everything else.** `VercelAIAdapter` in place of `AGUIAdapter` and the same agent serves a different frontend protocol. Section 2.2's interface argument, applied on the output side.

### The two limitations, restated

From Section 7.5, because a team choosing a frontend needs to know before they commit:

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

Tool visibility, chat history and RAG filters all follow from that binding. Section 18.1's argument, and the reason the controller stays this short.

### Key takeaways

- `->events($adapter)` plus `$adapter->getHeaders()`; add `X-Accel-Buffering` yourself.
- Echo `threadId` and `runId` so the client can correlate.
- Two AG-UI gaps: no frontend-defined tools, no state-sync events.
- Resolve the agent per authenticated user; everything else follows.

## 21.5 Streaming from a Queue

This is the section where Parts IV and V meet.

### The problem

Section 16.4 established that long runs belong on a queue. But a queue worker has no HTTP connection to the user — so how does progress reach the browser?

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

Without this, anyone who guesses a workflow ID watches someone else's agent work. Section 18.3's four leak points have a fifth relative: the broadcast channel.

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

This single job is most of the book converging:

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

## 21.6 Disconnection and Orphaned Cost

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

Record actual usage from the response's token counts after each run. Section 1.3 said capture usage from the first prototype; this is what you capture it for.

### Key takeaways

- A closed tab does not stop an agent — you keep paying.
- `connection_aborted()` inside the stream loop limits the damage.
- Queued work should be cancelled explicitly, not inferred.
- Per-user daily budgets cap exposure; they need the token counts you have been logging.

## Lab 15 — The Streaming Chat Interface

**Covers:** SSE or Livewire, tool-activity display, buffering, disconnection.

### Goal

A chat interface that renders the answer token by token and shows what the agent is doing while it does it — with the tool names mapped to language a customer can read.

### Requirements

1. **Token-by-token rendering.** Pick Livewire (Section 21.3) or SSE with `fetch` (Section 21.1). Livewire is fewer moving parts; SSE teaches you more about the transport.
2. **A tool-activity line** that replaces rather than accumulates, driven by a label allowlist with a safe fallback.
3. **Tool results never reach the browser.** Only labels.
4. **The buffering chain verified** with `curl -N` at all three points from Section 21.2 — PHP alone, through the web server, through the full public stack. Write down which layer, if any, needed configuring.
5. **Disconnection handling** with `connection_aborted()`.

### Acceptance criteria

- First visible token arrives in well under a second on a local model. Measure it; do not assume.
- Asking a question that triggers a tool shows the friendly label, then the answer.
- Adding a new tool without adding its label shows "Working on it", not the tool's internal name. Test this deliberately.
- Closing the tab mid-response produces a log line and stops the loop.
- `curl -N` streams through the full stack, not just locally.

### The part people skip

Requirement four. It is tempting to declare victory when it works on `artisan serve`, where there is no nginx and no proxy. The first deploy is where streaming breaks, and Section 21.2's bisection is the difference between five minutes and an afternoon.

Run the three `curl -N` commands against your actual staging environment before you call this lab done.

### Going further

Add a "stop" button that aborts the request from the browser side, and confirm that `connection_aborted()` fires. Then measure what it saved: run the same prompt to completion, note the token count, and compare with an aborted run. That number is the argument for building the button.
