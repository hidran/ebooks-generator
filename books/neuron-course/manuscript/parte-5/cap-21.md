# Chapter 21 — Streaming to the Frontend

::: {.callout .callout-tip}
[Code for this chapter]{.callout-title}

The Laravel listings below live inside an application, but the parts that do not need one are runnable at [`chapters/Ch21`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch21) in the companion repository: `sse-frames.php` prints the exact frames Section 21.1's endpoint sends, `channel.php` prints the envelopes a push channel publishes in Section 21.5, and `disconnect.php` reproduces Section 21.6's disconnection behaviour. None of them needs a model.
:::

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
use Generator;
use Illuminate\Http\Request;
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Workflow\Streaming\ProtocolEvent;
use NeuronAI\Workflow\Streaming\SSEEncoder;
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
            $stream = $this->agent->stream(new UserMessage($validated['message']));

            // No adapter or channel attached: stream() returns a Generator of native chunks.
            \assert($stream instanceof Generator);

            foreach ($stream as $chunk) {
                if (! $chunk instanceof TextChunk) {
                    continue;   // tool calls and results stay on the server (Section 7.4)
                }

                echo SSEEncoder::frame(new ProtocolEvent('text', ['content' => $chunk->content]));

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

### What the loop is doing

`stream()` is itself the generator — iterate it directly. With no stream adapter and no channel attached it yields NeuronAI's native chunk objects, and `TextChunk` is the only kind this endpoint lets through. Everything else — tool calls with their arguments, tool results — is skipped on the server, which is Section 7.4's rule applied at the HTTP boundary.

`SSEEncoder::frame()` is the framework's SSE framing, and the only place bytes are produced. A `ProtocolEvent` is a type plus a JSON-serialisable payload; the encoder writes it as one `data:` line, and substitutes invalid UTF-8 rather than failing the stream. Section 21.4 lets an adapter build the events for you; here, building one by hand keeps the allowlist explicit.

The `done` event after the loop is not decoration. When an SSE response ends, `EventSource` treats it as a dropped connection and schedules a reconnect — which, for this endpoint, would ask the question again. The explicit event lets the page tell a finished answer from a failure and close before that happens.

### The four headers, each doing a job

**`Content-Type: text/event-stream`** — tells the browser this is SSE.

**`Cache-Control: no-cache, no-transform`** — `no-transform` matters: some proxies compress or rewrite responses, which breaks the frame boundaries.

**`X-Accel-Buffering: no`** — nginx-specific, and the one that saves you a day. Without it nginx buffers the response and delivers it all at once, at which point you have the complexity of streaming with none of the benefit.

**`Connection: keep-alive`** — hold the connection open.

### The SSE frame format

```
data: {"type":"text","content":"Hello"}\n\n
```

Two newlines terminate a frame. Miss one and the browser waits forever for a frame that never completes — a failure that looks like "streaming does not work" and is one character.

### The frontend

```javascript
const source = new EventSource('/chat/stream?message=' + encodeURIComponent(text));

source.onmessage = (e) => {
    const chunk = JSON.parse(e.data);

    if (chunk.type === 'text') {
        output.textContent += chunk.content;
    }
};

source.addEventListener('done', () => source.close());

source.onerror = () => source.close();
```

**`EventSource` only does GET.** For a POST body you either use `fetch()` with a `ReadableStream` reader, or accept the message as a query parameter — which caps your message length and puts user content in access logs. For anything real, use `fetch`.

### Key takeaways

- SSE fits agent output: one-directional, plain HTTP, auto-reconnect.
- Iterate `stream()` directly; forward only `TextChunk` content, framed with `SSEEncoder::frame()`.
- Send an explicit `done` event, or `EventSource` reconnects and asks again.
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

The framework's own streaming guide says it directly: send the adapter's headers, frame each event with `SSEEncoder`, and flush after every line, or the stream can get stuck in PHP output buffers or proxies. The built-in UI adapters even put `X-Accel-Buffering: no` in their `getHeaders()`.

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
use Generator;
use Livewire\Component;
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\Stream\Chunks\ToolCallChunk;
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

        $stream = $agent->stream(new UserMessage($question));
        \assert($stream instanceof Generator);

        foreach ($stream as $chunk) {
            if ($chunk instanceof ToolCallChunk) {
                $this->activity = $this->label($chunk->tool->getName());
                $this->stream(to: 'activity', content: $this->activity, replace: true);
                continue;
            }

            if (! $chunk instanceof TextChunk) {
                continue;   // tool results, reasoning: never rendered
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

`$this->label()` maps tool names to user-facing text, with `?? 'Working on it'` as the fallback. And the loop renders exactly two kinds of chunk: a `ToolCallChunk` becomes a label, a `TextChunk` becomes answer text, and everything else — tool results, reasoning — is dropped by the `instanceof TextChunk` check rather than by a list of things to exclude.

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

use App\Neuron\SupportAgentFactory;
use Generator;
use Illuminate\Http\Request;
use NeuronAI\Agent\Adapters\AGUIAdapter;
use NeuronAI\Agent\AgentState;
use NeuronAI\Agent\Frontend\AGUIInputTranslator;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Workflow\Streaming\ProtocolEvent;
use NeuronAI\Workflow\Streaming\SSEEncoder;
use Symfony\Component\HttpFoundation\StreamedResponse;

class AgentUiController extends Controller
{
    public function __invoke(Request $request, SupportAgentFactory $agents): StreamedResponse
    {
        $input = $request->validate([
            'threadId'           => ['required', 'string'],
            'runId'              => ['nullable', 'string'],
            'messages'           => ['required', 'array', 'min:1'],
            'messages.*.id'      => ['required', 'string'],
            'messages.*.role'    => ['required', 'string'],
            'messages.*.content' => ['nullable', 'string'],
            'state'              => ['nullable', 'array'],
            'resume'             => ['nullable', 'array'],
        ]);

        // The client names the thread; the server decides whether this user may use it.
        $conversation = $request->user()->conversations()
            ->where('thread_id', $input['threadId'])
            ->firstOrFail();

        $last = $input['messages'][\array_key_last($input['messages'])];

        $adapter = new AGUIAdapter(
            threadId: $conversation->thread_id,
            runId: $input['runId'] ?? null,
            messages: $input['messages'],
            state: $input['state'] ?? [],
        );

        $agent = $agents->forThread($conversation->thread_id)->setStreamAdapter($adapter);

        // Answers to a paused run (approvals, browser tool results) continue it;
        // a trailing user message starts a new turn. Nothing else is accepted.
        $continuation = ($input['resume'] ?? []) !== [] || $last['role'] === 'tool';
        abort_unless($continuation || $last['role'] === 'user', 422, 'Nothing to answer and no new message.');

        /** @var Generator<int, ProtocolEvent, mixed, AgentState> $stream */
        $stream = $continuation
            ? $agent->submitInputs($request->all(), new AGUIInputTranslator())->events()
            : $agent->stream(new UserMessage((string) $last['content']));

        return response()->stream(function () use ($stream) {
            foreach (SSEEncoder::encode($stream) as $line) {
                echo $line;
                \flush();
            }
        }, 200, $adapter->getHeaders());
    }
}
```

### Six things worth pointing out

**The adapter shapes, the encoder frames.** `setStreamAdapter()` makes `stream()` yield `ProtocolEvent` objects — `RUN_STARTED`, `TEXT_MESSAGE_CONTENT` and the rest — instead of native chunks. `SSEEncoder::encode()` turns each into a `data:` line and forwards the generator's return value, so the final `AgentState` is still there if you want it. The adapter knows nothing about bytes, which is what lets the same adapter feed a broadcast channel in Section 21.5.

**`getHeaders()` supplies the protocol headers — including `X-Accel-Buffering: no`.** The built-in adapters now carry Section 21.2's nginx fix themselves, so there is nothing to merge in.

**Only the last user message goes to the agent.** An AG-UI client posts the whole conversation on every turn. The agent already has that conversation in its durable chat history, keyed by the thread — feed it the client's copy and every earlier message is stored twice. The client's `messages` go to the adapter instead, which uses them to keep the protocol's message snapshot complete.

**The thread is the agent's identity — authorise it.** AG-UI's `threadId` becomes the agent's thread, and the thread *is* the agent's workflow ID: the key its history and any suspended run are filed under. That makes it exactly the value Section 18.2 said never to take from user input. The lookup through `$request->user()->conversations()` is what turns a client-supplied string into a thread this user owns. Echo `runId` back too: it is the client's per-request identifier, and without it the client cannot correlate the stream with the run it asked for.

**The request shape decides new turn versus continuation.** A trailing user message is a new turn, and goes to `stream()`. A `resume` array — the client answering interrupts — or a trailing tool message is a continuation of a paused run, and goes to `submitInputs()` with the protocol's translator, which validates it against the persisted request before anything executes and throws `InputTranslationException` for anything that does not match. Note that the continuation calls `events()`, not `stream()`: `stream()` always starts a new turn. An invalid continuation must be an error response, never a fallback to a new turn.

**Swap the adapter, keep everything else.** `VercelAIAdapter` in place of `AGUIAdapter` and the same agent serves a different frontend protocol — with `VercelAIInputTranslator` for its continuations. Section 2.2's interface argument, applied on the output side.

### When the run pauses

If a tool in the turn needs approval (Chapter 22), the stream does not end like a completed one. The adapter's `interrupt()` terminal replaces `end()`: on AG-UI, `RUN_FINISHED` carries `outcome: {type: "interrupt", interrupts: [...]}`, one `confirmation` interrupt per pending tool call, with the tool call ID as its `id`; on Vercel, a `tool-approval-request` part per call.

A frontend that treats every `RUN_FINISHED` as "the answer is complete" will render a paused run as a finished one. Check `outcome.type` before you close the turn. The client answers with a `resume` array in its next request, which the endpoint above routes to `submitInputs()`. Section 22.5 covers the approval side for clients that do not speak AG-UI.

### What the adapter covers, and what it does not

From Section 7.5, because a team choosing a frontend needs to know before they commit:

**Snapshots at the pause, not deltas.** The adapter emits `STATE_SNAPSHOT` and `MESSAGES_SNAPSHOT` before finishing an interrupted run, seeded from the `state` and `messages` you passed to its constructor. It does not emit `STATE_DELTA`. If your design depends on fine-grained shared-state synchronisation while the agent runs, the adapter will not give it to you.

**Frontend-defined tools need one more step.** AG-UI clients can declare tools in `RunAgentInput.tools` for the browser to execute. NeuronAI supports them as deferred tools: the run suspends when the model calls one, the adapter publishes the call, and the client posts the result back as a trailing tool message — the continuation branch above. What the endpoint does not yet do is attach those tools to the agent. `AGUIInputTranslator::tools($payload)` builds them from the request; add them in the factory, after rejecting any name that shadows one of your server-side tools, and apply your approval policy to them like any other tool.

If you are evaluating CopilotKit or a similar AG-UI frontend, check these two against your design now rather than after the frontend is built.

### Progress events from your own nodes

Chunks are not the only thing a stream can carry. A node — in your own workflow, or in an agent's custom node — can `yield` a portable progress event, and each adapter translates it into its protocol's vocabulary:

```php
use NeuronAI\Agent\Adapters\Events\ActivityStreamEvent;
use NeuronAI\Agent\Adapters\Events\StepStartedStreamEvent;

yield new StepStartedStreamEvent('checking-stock');

yield new ActivityStreamEvent(
    id: "stock-{$orderId}",
    type: 'stock-check',
    data: ['checked' => 3, 'total' => 5],
);
```

On AG-UI these become `STEP_STARTED` and `ACTIVITY_SNAPSHOT` — an activity with the same `id` replaces the previous one, which is exactly the progress-bar semantics you want. `CustomStreamEvent($name, $value)` becomes AG-UI's `CUSTOM` event. On Vercel all three travel as transient `data-*` parts, which reach the UI without entering message history.

If your nodes already yield domain objects, map them instead of rewriting the nodes:

```php
$adapter->mapEvent(
    StockChecked::class,
    static fn (StockChecked $event): ?ActivityStreamEvent => new ActivityStreamEvent(
        id: "stock-{$event->orderId}",
        type: 'stock-check',
        data: ['checked' => $event->checked, 'total' => $event->total],
    ),
);
```

Matching is by exact class, and returning `null` suppresses the event — which makes `mapEvent()` the place to keep an internal event off the wire. The adapter stays the single owner of protocol vocabulary; your nodes never import an AG-UI type.

One rule for all of it: **streamed events are live and ephemeral.** They are not persisted, and a resumed run does not replay them. Never make correctness depend on the browser having received one.

### Authentication

An SPA sends a token; Sanctum or Passport handles it as usual. The important part is that the *agent* is built for the authenticated user and the authorised thread. Because the thread is part of the agent's identity — it goes to the constructor, not to a setter — a factory reads better than a container binding:

```php
class SupportAgentFactory
{
    public function __construct(
        private readonly OrderRepository $orders,
        private readonly AuthManager $auth,
    ) {}

    public function forThread(string $threadId): SupportAgent
    {
        return new SupportAgent(
            orders: $this->orders,
            user: $this->auth->user(),
            threadId: $threadId,
        );
    }
}
```

```php
class SupportAgent extends Agent
{
    public function __construct(
        private readonly OrderRepository $orders,
        private readonly User $user,
        string $threadId,
    ) {
        parent::__construct(threadId: $threadId);
    }

    // provider(), tools(), chatHistory() as in Chapter 18
}
```

Tool visibility, chat history and RAG filters all follow from those two inputs. Section 18.1's argument, and the reason the controller stays this short.

### Key takeaways

- `setStreamAdapter()` makes `stream()` yield `ProtocolEvent`s; `SSEEncoder::encode()` frames them; `getHeaders()` already includes `X-Accel-Buffering`.
- Send the agent only the last user message; the client's history seeds the adapter.
- A `resume` array or trailing tool message is a continuation: `submitInputs()` with the protocol translator, then `events()`.
- The AG-UI `threadId` becomes the agent's workflow ID — resolve it through the user, never trust it raw.
- A paused run ends with an interrupt outcome, not a plain finish; check before closing the turn.
- Nodes yield portable progress events; `mapEvent()` translates or suppresses your own.

## 21.5 Streaming from a Queue

This is the section where Parts IV and V meet.

### The problem

Section 16.4 established that long runs belong on a queue. But a queue worker has no HTTP connection to the user — so how does progress reach the browser?

The answer is a **streaming channel**. Everything so far has been *pull* streaming: the code iterating the generator is the code holding the response. A channel is the *push* half. Attach one to a workflow or an agent, together with a stream adapter, and the run delivers each protocol event to the channel as it is produced — to Pusher, to Redis, to a websocket — while the worker simply calls `run()`.

### The architecture

```
Browser → POST /workflows             → creates the run record, returns { workflowId }
Browser → subscribes to private-workflows.{workflowId}, waits for the subscription
Browser → POST /workflows/{id}/start  → dispatches the job
Worker  → runs the workflow; the channel pushes every event, in sequence
Browser → reorders by sequence, renders progress, reconciles on a gap
```

The order of the first three lines matters. Pusher and Redis Pub/Sub do not replay: an event published before the browser subscribed is gone. So the browser subscribes first and only then asks the server to start.

### The job

```php
<?php

declare(strict_types=1);

namespace App\Jobs;

use App\Models\WorkflowRun;
use App\Neuron\Workflows\ContentWorkflow;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use NeuronAI\Agent\Adapters\AgentChunkAdapter;
use NeuronAI\Laravel\Models\WorkflowStore;
use NeuronAI\Workflow\Persistence\EloquentPersistence;
use NeuronAI\Workflow\Streaming\Channel\PusherChannel;
use NeuronAI\Workflow\WorkflowState;
use Pusher\Pusher;

class RunContentWorkflow implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $timeout = 600;
    public int $tries = 1;   // agent runs are expensive — do not blind-retry

    public function __construct(
        public readonly WorkflowRun $run,
    ) {}

    public function handle(Pusher $pusher): void
    {
        $state = ContentWorkflow::make(
            workflowId: $this->run->workflow_id,
            state: new WorkflowState(['topic' => $this->run->topic]),
        )
            ->setPersistence(new EloquentPersistence(WorkflowStore::class))
            ->setStreamAdapter(new AgentChunkAdapter())
            ->setChannel(new PusherChannel(
                client: $pusher,
                channel: "private-workflows.{$this->run->workflow_id}",
            ))
            ->run();

        if ($state->isInterrupted()) {
            $this->run->update(['status' => 'awaiting_approval']);

            return;   // Chapter 22 records and routes the approval
        }

        $this->run->update([
            'status' => 'completed',
            'result' => $state->get('final'),
        ]);
    }
}
```

### Four things this job does differently from a web request

**`run()`, not a loop.** With both an adapter and a channel attached, the workflow consumes its own stream and delivers every event through the channel as it happens. `run()` returns the final state when the segment completes or pauses. There is no generator to iterate and nothing to echo.

**The adapter still decides the shape.** A channel carries protocol events, never native objects, so it needs an adapter. `AgentChunkAdapter` is NeuronAI's own vocabulary for a consumer that speaks no UI protocol: each chunk or progress event becomes one event named after its kind — `text`, `tool-call`, `activity`, `step-started` — with the chunk's own fields as payload. If the browser runs an AG-UI or Vercel client, attach that adapter instead; the channel does not care.

**The channel reports the lifecycle.** After the adapter's terminal frames, the channel sends `stream.completed`, `stream.interrupted` or `stream.failed`, carrying only the workflow ID — no state, no exception details. There is no need for your own `WorkflowCompleted` or `WorkflowPaused` broadcast events: the browser learns the outcome from the stream and fetches the result from your application, which is the authoritative record.

**The pause is a return value.** An interrupted run returns normally with `isInterrupted()` true — nothing to catch. Chapter 22 takes it from there.

`AgentChunkAdapter` forwards everything it is given, including tool call arguments and tool results. For a progress screen shown to the person who started the run that is usually fine; for anything customer-facing, suppress what should not travel with `mapEvent(ToolResultChunk::class, fn () => null)`, or attach the AG-UI adapter and let the frontend decide. Section 7.4's rule does not stop applying because the transport changed.

### The Pusher client

`PusherChannel` takes an application-configured client from the official `pusher/pusher-php-server` SDK — which is also what Laravel Reverb speaks — so encryption, signing, endpoints and timeouts are configured once, where they belong:

```php
// AppServiceProvider::register()
$this->app->singleton(Pusher::class, fn () => new Pusher(
    config('broadcasting.connections.reverb.key'),
    config('broadcasting.connections.reverb.secret'),
    config('broadcasting.connections.reverb.app_id'),
    config('broadcasting.connections.reverb.options', []) + ['timeout' => 5],
));
```

Set the SDK's `timeout` explicitly and use version 7.2.4 or later; earlier releases do not pass it to the HTTP request.

Prefer Redis? `new RedisChannel($redis, "workflows:{$id}")` publishes the same envelopes on Redis Pub/Sub for a process that holds the browser's connection. Prefer Laravel's own broadcasting? `CallbackChannel` wraps a closure per lifecycle method, so `onSend` can call `Broadcast::private(...)->as($event->type)->with($event->data)->sendNow()`. **`sendNow()`, never a queued broadcast.** A queued broadcast lines your progress updates up behind the job producing them — on a single worker, a deadlock in slow motion — and with several workers it delivers them out of order.

### The envelope, and why the browser needs a library

`PusherChannel` and `RedisChannel` do not send bare protocol events. Each message is an envelope:

```json
{"streamId":"81d4f00e881563538f272ca26aa7a8d4","sequence":3,"type":"text","data":{"messageId":"msg_1","content":"The first"}}
```

Three problems hide behind those fields, and all three will happen in production:

**Order.** Pusher guarantees order within a batch, not between batches. `sequence` numbers every logical event in a segment, so the browser can put them back in order — including a `stream.completed` that arrives before the text it follows.

**Size.** Pusher caps an event at 10 KB. A long tool result or a large activity payload is split into `stream.fragment` envelopes sharing one sequence number, and must be reassembled before it can be parsed.

**Gaps.** A dropped connection loses events for good. The browser must notice a missing sequence number and reload from the application rather than render a stream with a hole in it.

You do not want to write that by hand, and you do not have to. `@neuron-core/streaming` is the browser half of the same contract:

```javascript
import { subscribeToPusher } from '@neuron-core/streaming';

const channel = Echo.connector.pusher.subscribe(`private-workflows.${workflowId}`);

channel.bind('pusher:subscription_succeeded', () => {
    fetch(`/workflows/${workflowId}/start`, { method: 'POST', headers: csrfHeaders });
});

const subscription = subscribeToPusher(channel, {
    onEvent: ({ type, data }) => {
        if (type === 'activity') {
            renderProgress(data.id, data.data);
        } else if (type === 'stream.interrupted') {
            showMessage('Waiting for approval.');
        } else if (type === 'stream.completed') {
            loadResult(workflowId);
        }
    },
    onGap: () => loadResult(workflowId),   // reconcile from the server; never guess
});
```

It orders, reassembles, drops duplicates and reports gaps; your callback only ever sees complete events in sequence. The channel reference comes from the Pusher client that Echo already configured, so authentication runs through your normal broadcasting routes.

### The channel authorisation

```php
// routes/channels.php
Broadcast::channel('workflows.{workflowId}', function ($user, string $workflowId) {
    return WorkflowRun::where('workflow_id', $workflowId)
        ->where('tenant_id', $user->tenant_id)
        ->exists();
});
```

Without this, anyone who guesses a workflow ID watches someone else's agent work. Section 18.3's four leak points have a fifth relative: the broadcast channel. For content that must stay confidential even from the broadcast provider, use a `private-encrypted-*` channel with the SDK's encryption master key; the browser needs `pusher-js/with-encryption`, and the package's consumer is unchanged.

### What this composes

This single job is most of the book converging:

- Workflow streaming with `yield` and portable progress events (14.4, 21.4)
- Interruption and persistence (15.4)
- Eloquent persistence (18.4)
- Async execution (16.4)
- Adapters pushing to an external transport (7.5)
- `pcntl` available, so parallel tools work (5.13)
- Inspector subscribed on the workflow (23.3)

That last one is the misconfiguration most likely to bite: nothing is monitored unless you subscribe the listener, and a worker is exactly where nobody notices it is missing.

### Key takeaways

- Push, not pull: adapter plus channel, and the worker just calls `run()`.
- Subscribe first, then start the run — Pusher and Redis do not replay.
- `PusherChannel` sends sequenced, fragmentable envelopes; `@neuron-core/streaming` reorders, reassembles and reports gaps.
- The channel reports completion, pause and failure; fetch results from the application.
- Authorise the channel by tenant; `$tries = 1` on agent jobs; blind retries re-spend money.

## 21.6 Disconnection and Orphaned Cost

### The problem nobody mentions

A user starts a 30-second agent run. At second four they close the tab.

The browser is gone. **The agent keeps running.** Every remaining model call is billed. In a multi-agent workflow that is a substantial amount of money spent on output nobody will ever read.

At low volume this is invisible. At scale it is a line item.

### Detecting it in a streamed response

```php
return response()->stream(function () use ($agent, $message) {
    $stream = $agent->stream(new UserMessage($message));
    \assert($stream instanceof Generator);

    foreach ($stream as $chunk) {
        if (\connection_aborted()) {
            \Log::info('Client disconnected — stopping agent run');

            try {
                $stream->throw(new ClientDisconnected());
            } catch (ClientDisconnected) {
                // the run is now settled as failed
            }
            break;
        }

        if ($chunk instanceof TextChunk) {
            echo SSEEncoder::frame(new ProtocolEvent('text', ['content' => $chunk->content]));
            \flush();
        }
    }
}, 200, $headers);
```

`connection_aborted()` requires that you have written to the connection — PHP only detects the broken pipe on a write attempt. Since you are streaming, you are writing, so this works. It would not work in a non-streaming endpoint.

### Why `break` alone is not enough

`ClientDisconnected` is an ordinary exception class of your own. Throwing it *into* the generator is what matters.

An agent run is a durable workflow run. While it executes it holds a lease on its thread — ten minutes by default for an agent — so that a second process cannot start a competing run on the same conversation. A clean finish, a pause or a caught failure releases the lease. Simply abandoning the generator does none of those: the run stays marked as running until the lease expires.

With the default in-memory persistence you never notice, because the record dies with the request. Give the agent durable persistence — which Chapter 22 does, because approvals need it — and a bare `break` means the user's *next* message on that conversation is refused with `RunInFlightException` for up to ten minutes. `$stream->throw()` delivers the exception at the point where the run is suspended; the workflow settles the run as failed and rethrows, and the next message supersedes the failed run normally.

The companion's `disconnect.php` runs both versions side by side: with `break` alone the second message is refused; with the `throw()` it is answered.

**One honest caveat:** stopping the loop stops *your* iteration. A model call already in flight completes and is billed. You are limiting the damage, not eliminating it.

### For queued workflows

A disconnected browser does not stop a worker, and it should not — the user may come back, and the result is worth having. But there are cases where cancellation is right. A worker running with a channel has no loop to break out of, so the check belongs inside the workflow — in the first lines of any node that starts an expensive step:

```php
class ReviewNode extends Node
{
    public function __invoke(DraftReady $event, WorkflowState $state): DraftReviewed|StopEvent
    {
        if (Cache::has("workflow:{$state->getWorkflowId()}:cancelled")) {
            $state->set('cancelled', true);

            return new StopEvent();
        }

        // ... the review itself, as in Chapter 14
    }
}
```

```php
// A cancel endpoint
Cache::put("workflow:{$id}:cancelled", true, now()->addHour());
```

Explicit cancellation, not inferred from disconnection — and it ends the run cleanly, so the workflow ID is free again and the channel reports `stream.completed` like any other finish.

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

Record actual usage from each inference's token counts — Section 23.1 subscribes a listener that does exactly this. Section 1.3 said capture usage from the first prototype; this is what you capture it for.

### Key takeaways

- A closed tab does not stop an agent — you keep paying.
- `connection_aborted()` inside the stream loop limits the damage.
- Throw into the generator before you break, or a durable run keeps its thread locked until the lease expires.
- Queued work should be cancelled explicitly, between steps, not inferred.
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
5. **Disconnection handling** with `connection_aborted()`, throwing into the stream before breaking out.

### Acceptance criteria

- First visible token arrives in well under a second on a local model. Measure it; do not assume.
- Asking a question that triggers a tool shows the friendly label, then the answer.
- Adding a new tool without adding its label shows "Working on it", not the tool's internal name. Test this deliberately.
- Closing the tab mid-response produces a log line and stops the loop — and a new message on the same conversation, sent straight afterwards, is answered rather than refused.
- `curl -N` streams through the full stack, not just locally.

### The part people skip

Requirement four. It is tempting to declare victory when it works on `artisan serve`, where there is no nginx and no proxy. The first deploy is where streaming breaks, and Section 21.2's bisection is the difference between five minutes and an afternoon.

Run the three `curl -N` commands against your actual staging environment before you call this lab done.

### Going further

Add a "stop" button that aborts the request from the browser side, and confirm that `connection_aborted()` fires. Then measure what it saved: run the same prompt to completion, note the token count, and compare with an aborted run. That number is the argument for building the button.
