# Agentic AI in PHP with Neuron
## PART V — LARAVEL (continued)
### Full lesson scripts — Modules 21, 22 and 23

> Copy each lesson block (between the `═══` separators) into its own Google Doc.
> Target versions: `neuron-core/neuron-laravel` 2.0.0, `neuron-core/neuron-ai` ^4.0.3 (verified against 4.0.3), PHP 8.5, Laravel 13. The package itself accepts PHP 8.2+ and Laravel 10–13; the lesson code needs PHP 8.5 (Lesson 22.4 uses `#[\NoDiscard]` and `clone()` with properties, and Lesson 21.4 uses `array_last()`).
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

use App\Models\Conversation;
use App\Neuron\Agents\SupportAgent;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Gate;
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Workflow\Streaming\ProtocolEvent;
use NeuronAI\Workflow\Streaming\SSEEncoder;
use Symfony\Component\HttpFoundation\StreamedResponse;

class ChatStreamController extends Controller
{
    public function __invoke(
        Request $request,
        Conversation $conversation,
        SupportAgent $agent,
    ): StreamedResponse {
        Gate::authorize('participate', $conversation);

        $validated = $request->validate([
            'message' => ['required', 'string', 'max:4000'],
        ]);

        $agent = $agent->for($conversation->threadId());
        $agent->recoverFailedTurn();

        $stream = $agent->stream(new UserMessage($validated['message']));

        // Lazy until pulled: admit the run now, while a refusal can still be an HTTP status.
        $stream->valid();

        return response()->stream(function () use ($stream) {
            foreach ($stream as $chunk) {
                if (! $chunk instanceof TextChunk) {
                    continue;   // tool calls and results stay on the server (Lesson 7.4)
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

Before there is a loop there is an agent, and it arrives the way Lesson 18.1 built it. The route names the conversation — `Route::get('/chat/stream/{conversation}', ChatStreamController::class)` — the action receives the agent by method injection, and `for()` binds it to the conversation's thread once the policy has authorised the user. An agent with no thread bound does not stream at all. `recoverFailedTurn()` is the answer to Lesson 18.4's fifth question, given before the turn and never after; Lesson 21.6 shows why a streaming endpoint is where it earns its place.

`stream()` is itself the generator — iterate it directly. It is also lazy: nothing runs until the first item is pulled, and `$stream->valid()` pulls it in the controller, before the response exists. A thread that cannot take the turn — another tab is still streaming on it — is then refused with an HTTP status, the 409 Lesson 21.4 maps it to, instead of a `200` that ends without a word. With no stream adapter attached the generator yields NeuronAI's native chunk objects, and `TextChunk` is the only kind this endpoint lets through. Everything else — tool calls with their arguments, tool results — is skipped on the server, which is Lesson 7.4's rule applied at the HTTP boundary.

`SSEEncoder::frame()` is the framework's SSE framing, and the only place bytes are produced. A `ProtocolEvent` is a type plus a JSON-serialisable payload; the encoder writes it as one `data:` line, and substitutes invalid UTF-8 rather than failing the stream. Lesson 21.4 lets an adapter build the events for you; here, building one by hand keeps the allowlist explicit.

The `done` event after the loop is not decoration. When an SSE response ends, `EventSource` treats it as a dropped connection and schedules a reconnect — which, for this endpoint, would ask the question again. The explicit event lets the page tell a finished answer from a failure and close before that happens.

Older material (v3, and the SDK README) iterates `$handler->events()` on the object `stream()` returns and reads `$chunk->content` off whatever comes out. Neither works on 4.0.3: there is no handler object, and the generator yields several chunk types, only one of which has text.

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
const source = new EventSource(`/chat/stream/${conversationId}?message=` + encodeURIComponent(text));

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

- SSE fits agent output: one-directional, plain HTTP, a client built into the browser.
- Authorise, bind with `for()`, recover and prime before the response is returned: after the first byte, a failure can no longer be a status.
- Iterate `stream()` directly; forward only `TextChunk` content, framed with `SSEEncoder::frame()`.
- Send an explicit `done` event, or `EventSource` reconnects and asks again.
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
    fastcgi_pass   unix:/var/run/php/php8.5-fpm.sock;
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

The framework's own streaming guide says it directly: send the adapter's headers, frame each event with `SSEEncoder`, and flush after every line, or the stream can get stuck in PHP output buffers or proxies. The built-in UI adapters even put `X-Accel-Buffering: no` in their `getHeaders()`.

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

use App\Models\Conversation;
use App\Neuron\Agents\SupportAgent;
use Livewire\Component;
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\Stream\Chunks\ToolCallChunk;
use NeuronAI\Chat\Messages\UserMessage;

class Chat extends Component
{
    public Conversation $conversation;

    public string $input = '';
    public string $answer = '';
    public ?string $activity = null;
    public array $history = [];

    public function send(SupportAgent $agent): void
    {
        $this->authorize('participate', $this->conversation);

        $question = \trim($this->input);

        if ($question === '') {
            return;
        }

        $this->history[] = ['role' => 'user', 'content' => $question];
        $this->input     = '';
        $this->answer    = '';

        $agent = $agent->for($this->conversation->threadId());
        $agent->recoverFailedTurn();

        $stream = $agent->stream(new UserMessage($question));

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

The agent arrives as it does in a controller. The page mounts the component with its conversation — `<livewire:chat :conversation="$conversation" />` — Livewire resolves `SupportAgent` from the container for the action, and `send()` does what every endpoint in this module does before a turn: authorise, bind with `for()`, recover. Livewire protects the model's ID from tampering between requests, but the policy still runs on every `send()`: who may use a conversation can change while the page stays open.

**Note `replace: true` for the activity line** and its absence for the answer. Activity is a status that overwrites; the answer accumulates. Getting these backwards is the most common Livewire streaming bug.

### The label allowlist, again

`$this->label()` maps tool names to user-facing text, with `?? 'Working on it'` as the fallback. And the loop renders exactly two kinds of chunk: a `ToolCallChunk` becomes a label, a `TextChunk` becomes answer text, and everything else — tool results, reasoning — is dropped by the `instanceof TextChunk` check rather than by a list of things to exclude.

Lesson 7.4's rule: never show raw tool names or results. A new tool added next month degrades to the generic message rather than leaking `internal_pricing_lookup` to a customer. Allowlists fail safe — the same argument as `only()` over `exclude()` in Lesson 5.8.

### The limitation to know

The agent runs inside a Livewire request, so PHP-FPM's `max_execution_time` and the web server's timeouts apply. Fine for a 15-second chat response. Not fine for a two-minute multi-agent workflow — that belongs on a queue with a different transport, which is Lesson 21.5.

### Key takeaways

- `$this->stream(to:, content:)` plus `wire:stream` — Livewire handles the transport.
- `replace: true` for status, omitted for accumulating text.
- Map tool names through an allowlist with a safe fallback; render only the chunk types you list.
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

use App\Models\Conversation;
use App\Neuron\Agents\SupportAgent;
use App\Neuron\ThreadScope;
use Generator;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Gate;
use NeuronAI\Agent\Adapters\AGUIAdapter;
use NeuronAI\Agent\Frontend\AGUIInputTranslator;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Workflow\Streaming\SSEEncoder;
use Symfony\Component\HttpFoundation\StreamedResponse;
use Throwable;

class AgentUiController extends Controller
{
    public function __invoke(Request $request, SupportAgent $agent): StreamedResponse
    {
        $request->validate([
            'threadId'           => ['required', 'string', 'regex:/^t\d+:u\d+:c\d+$/'],
            'runId'              => ['nullable', 'string'],
            'messages'           => ['required', 'array', 'min:1'],
            'messages.*.id'      => ['required', 'string'],
            'messages.*.role'    => ['required', 'string'],
            'messages.*.content' => ['nullable', 'string'],
            'state'              => ['nullable', 'array'],
            'resume'             => ['nullable', 'array'],
        ]);

        // The client names the thread; the server decides whether this user may use it.
        $threadId = $request->input('threadId');
        $conversation = Conversation::findOrFail(ThreadScope::of($threadId)->conversationId);

        Gate::authorize('participate', $conversation);
        abort_unless($conversation->threadId() === $threadId, 403);

        // The messages as posted: validate() returns only the keys its rules name.
        $messages = $request->input('messages');
        $last = \array_last($messages);

        // Answers to a paused run (approvals, browser tool results) continue it;
        // a trailing user message starts a new turn. Nothing else is accepted.
        $continuation = $request->array('resume') !== [] || $last['role'] === 'tool';
        abort_unless($continuation || $last['role'] === 'user', 422, 'Nothing to answer and no new message.');

        // On a copy of its own: the recovered turn must not stream into this response.
        $agent->for($threadId)->recoverFailedTurn();

        $adapter = new AGUIAdapter(
            threadId: $threadId,
            runId: $request->input('runId'),
            messages: $messages,
            state: $request->array('state'),
        );

        $agent = $agent->for($threadId)->setStreamAdapter(fn (): AGUIAdapter => $adapter);

        $events = $continuation
            ? $agent->submitInputs($request->all(), new AGUIInputTranslator())->events()
            : $agent->stream(new UserMessage((string) $last['content']));

        // Admission is lazy: start it now, so a refusal is an HTTP status, not a RUN_ERROR frame.
        $events->valid();

        return response()->stream(function () use ($events, $adapter): Generator {
            try {
                yield from SSEEncoder::encode($events);
            } catch (Throwable $e) {
                report($e);

                foreach ($adapter->error($e) as $event) {
                    yield SSEEncoder::frame($event);
                }
            }
        }, 200, $adapter->getHeaders());
    }
}
```

### Seven things worth pointing out

**The adapter shapes, the encoder frames.** `setStreamAdapter()` makes `stream()` yield `ProtocolEvent` objects — `RUN_STARTED`, `TEXT_MESSAGE_CONTENT` and the rest — instead of native chunks. It takes a factory, called once per execution segment (Lesson 7.5); this request runs a single segment, so the closure hands back the instance the response takes its headers from. `SSEEncoder::encode()` turns each event into a `data:` line and forwards the generator's return value, so the final `AgentState` is still there — it is what `yield from` evaluates to — if you want it. The callback is itself a generator: Laravel echoes and flushes every frame it yields. The adapter knows nothing about bytes, which is what lets the same adapter feed a broadcast channel in Lesson 21.5. (Older code passes an adapter instance, `->events($adapter)`, and builds it from `NeuronAI\Chat\Messages\Stream\Adapters\`; neither works on 4.0.3.)

**`getHeaders()` supplies the protocol headers — including `X-Accel-Buffering: no`.** The built-in adapters carry Lesson 21.2's nginx fix themselves, so there is nothing to merge in.

**Only the last user message goes to the agent.** An AG-UI client posts the whole conversation on every turn. The agent already has that conversation in its durable chat history, keyed by the thread — feed it the client's copy and every earlier message is stored twice. The client's `messages` go to the adapter instead, which uses them to keep the protocol's message snapshot complete. They go whole, from `$request->input('messages')`: `validate()` returns only the keys its rules name, and an adapter seeded with that subset has lost every `toolCallId` and `toolCalls` — it throws `InputTranslationException` for any conversation that contains a tool message.

**The thread is the agent's identity — authorise it.** AG-UI's `threadId` becomes the agent's thread, and the thread *is* the agent's workflow ID: the key its history and any suspended run are filed under. That makes it exactly the value Lesson 18.2 said never to take from user input. Three steps turn a client-supplied string into a thread this user may use: `ThreadScope` (Lesson 18.3) reads the conversation out of the name, the policy decides whether this user may use that conversation, and the name the server derives from the record must be the one the client sent. Only then is anything read or written under it. Echo `runId` back too: it is the client's per-request identifier, and without it the client cannot correlate the stream with the run it asked for.

**The request shape decides new turn versus continuation.** A trailing user message is a new turn, and goes to `stream()`. A `resume` array — the client answering interrupts — or a trailing tool message is a continuation of a paused run, and goes to `submitInputs()` with the protocol's translator, which validates it against the persisted request before anything executes and throws `InputTranslationException` for anything that does not match. The continuation test comes first, as in Lesson 7.5: after an approval pause the client's list still ends with the user's question. Note that the continuation calls `events()`, not `stream()`: `stream()` always starts a new turn. An invalid continuation must be an error response, never a fallback to a new turn.

**Until the first frame, a failure is a status code.** Two things happen before the response is returned. `recoverFailedTurn()` finishes a failed turn (Lesson 18.4) on a copy of its own — bound to the thread, with no adapter — so the recovered answer lands in the history and not in this stream. And `$events->valid()` pulls the first event. `stream()` and `events()` are lazy: the run is admitted only when the generator is first pulled, and left to the callback that happens after the `200` has gone out, so a thread that cannot take the turn — an approval still pending, another tab streaming — reaches the browser as a `RUN_ERROR` frame under a successful status. Pulled in the controller, the refusal is still an exception Laravel can turn into a status. The adapter is built there for the same reason: its constructor validates the messages it is seeded with. The statuses are mapped once for the whole application, in `bootstrap/app.php`:

```php
// bootstrap/app.php
return Application::configure(basePath: dirname(__DIR__))
    // ->withRouting(...) and ->withMiddleware(...) as the skeleton has them
    ->withExceptions(function (Exceptions $exceptions): void {
        // The first callback whose type matches wins: the most specific class goes first.
        $exceptions->render(fn (InputTranslationException $e) => response()->json(
            ['message' => $e->getMessage()], 400,
        ));
        $exceptions->render(fn (PersistenceException $e) => response()->json(
            ['message' => 'Conversations are unavailable. Retry later.'], 503,
        ));
        $exceptions->render(fn (RunInFlightException $e) => response()->json(
            ['message' => 'The conversation is busy.', 'status' => $e->status->value], 409,
        ));
        $exceptions->render(fn (WorkflowException $e) => response()->json(
            ['message' => 'The conversation changed. Reload it.'], 409,
        ));
    })->create();
```

All four live in `NeuronAI\Exceptions`. `PersistenceException` and `RunInFlightException` both extend `WorkflowException`, which is why the order matters. An `InputTranslationException` message is written for clients; a `WorkflowException`'s carries internals, and stays in the log.

**Swap the adapter, keep everything else.** `VercelAIAdapter` in place of `AGUIAdapter` and the same agent serves a different frontend protocol — with `VercelAIInputTranslator` for its continuations. Lesson 2.2's interface argument, applied on the output side.

### When the run pauses

If a tool in the turn needs approval (Module 22), the stream does not end like a completed one. The adapter's `interrupt()` terminal replaces `end()`: on AG-UI, `RUN_FINISHED` carries `outcome: {type: "interrupt", interrupts: [...]}`, one `confirmation` interrupt per pending tool call, with the tool call ID as its `id`; on Vercel, a `tool-approval-request` part per call.

A frontend that treats every `RUN_FINISHED` as "the answer is complete" will render a paused run as a finished one. Check `outcome.type` before you close the turn. The client answers with a `resume` array in its next request, which the endpoint above routes to `submitInputs()`. Lesson 22.5 covers the approval side for clients that do not speak AG-UI.

### What the adapter covers, and what it does not

From Lesson 7.5, because a team choosing a frontend needs to know before they commit:

**Snapshots at the pause, not deltas.** The adapter emits `STATE_SNAPSHOT` and `MESSAGES_SNAPSHOT` before finishing an interrupted run, seeded from the `state` and `messages` you passed to its constructor. It does not emit `STATE_DELTA`. If your design depends on fine-grained shared-state synchronisation while the agent runs, the adapter will not give it to you.

**Frontend-defined tools need one more step.** AG-UI clients can declare tools in `RunAgentInput.tools` for the browser to execute. NeuronAI supports them as deferred tools: the run suspends when the model calls one, the adapter publishes the call, and the client posts the result back as a trailing tool message — the continuation branch above. What the endpoint does not yet do is attach those tools to the agent. `(new AGUIInputTranslator())->tools($request->all())` builds them from the request; add them to the bound copy with `addTool()`, after rejecting any name that shadows one of your server-side tools, and apply your approval policy to them like any other tool. Exempt the route from Laravel's `TrimStrings` and `ConvertEmptyStringsToNull` middleware too: with them, a tool result that is an empty string reaches the translator as `null` and is refused.

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

On AG-UI these become `STEP_STARTED` and `ACTIVITY_SNAPSHOT` — an activity with the same `id` replaces the previous one, which is exactly the progress-bar semantics you want. If your nodes already yield domain objects, map them instead of rewriting the nodes with `$adapter->mapEvent(StockChecked::class, static fn (StockChecked $event): ?ActivityStreamEvent => ...)`; matching is by exact class, and returning `null` suppresses the event. One rule for all of it: **streamed events are live and ephemeral.** They are not persisted, and a resumed run does not replay them. Never make correctness depend on the browser having received one.

### Authentication

An SPA sends a token; Sanctum or Passport handles it as usual. The important part is what the *agent* is told about the user who has just been authenticated: nothing. The container builds the same context-free `SupportAgent` for every request (Lesson 18.1), the endpoint authorises the thread, and `for()` binds a copy to it. What the agent does for this user then follows from the thread alone:

```php
class SupportAgent extends Agent
{
    // constructor, provider(), messageStore(), persistence() as in Module 18

    protected function tools(): array
    {
        $scope = ThreadScope::of($this->getThreadId());

        return [
            new SearchOrdersTool($scope->tenantId),
            new GetOrderStatusTool($scope->tenantId),
        ];
    }
}
```

Tool visibility, chat history and RAG filters all follow from that one input. No factory, and no `auth()` inside the agent: the same class runs unchanged on Lesson 21.5's queue worker, where there is no user to ask. Lesson 18.3's argument, and the reason the controller stays this short.

### Key takeaways

- `setStreamAdapter()` takes a factory and makes `stream()` yield `ProtocolEvent`s; `SSEEncoder::encode()` frames them; `getHeaders()` already includes `X-Accel-Buffering`.
- Send the agent only the last user message; the client's history seeds the adapter — whole, from `input()`, not from `validate()`.
- A `resume` array or trailing tool message is a continuation: `submitInputs()` with the protocol translator, then `events()`.
- The AG-UI `threadId` becomes the agent's workflow ID — authorise it against the conversation it names, never trust it raw.
- Recover a failed turn and prime the generator before returning the response: until the first frame, a refusal can still be a 400 or a 409.
- A run paused for approval ends with an interrupt outcome, not a plain finish; check before closing the turn.
- Nodes yield portable progress events; `mapEvent()` translates or suppresses your own.

---
═══════════════════════════════════════════════════════════════

## LESSON 21.5 — Streaming from a Queue

**Duration:** 13 minutes
**Type:** Hands-on — the pattern that ties Parts IV and V together

### Learning objectives

Stream progress from a workflow running on a worker, to a browser it has no connection to.

### The problem

Lesson 16.4 established that long runs belong on a queue. But a queue worker has no HTTP connection to the user — so how does progress reach the browser?

The answer is a **streaming channel**. Everything so far has been *pull* streaming: the code iterating the generator is the code holding the response. A channel is the *push* half. Attach one to a workflow or an agent, together with a stream adapter, and the run delivers each protocol event to the channel as it is produced — to Pusher, to Redis, to a websocket — while the worker simply calls `run()`.

### The architecture

```
Browser → POST /workflows             → creates the run record and its run ID, returns { workflowId }
Browser → subscribes to private-workflows.{workflowId}, waits for the subscription
Browser → POST /workflows/{id}/start  → dispatches the job
Worker  → runs the workflow; the channel pushes every event, in sequence
Browser → reorders by sequence, renders progress, reconciles on a gap
```

The order of the first three lines matters. Pusher and Redis Pub/Sub do not replay: an event published before the browser subscribed is gone. So the browser subscribes first and only then asks the server to start. The first request does one more thing: it mints the run ID — a UUID in a `run_id` column of the record — before any job exists. The job below depends on it.

### The job

```php
<?php

declare(strict_types=1);

namespace App\Jobs;

use App\Models\WorkflowRun;
use App\Neuron\Workflows\ContentState;
use App\Neuron\Workflows\ContentWorkflow;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use NeuronAI\Agent\Adapters\AgentChunkAdapter;
use NeuronAI\Exceptions\RunInFlightException;
use NeuronAI\Workflow\Executor\ExecutionRequest;
use NeuronAI\Workflow\Persistence\PersistenceInterface;
use NeuronAI\Workflow\Streaming\Channel\PusherChannel;
use NeuronAI\Workflow\WorkflowStatus;
use Pusher\Pusher;

class RunContentWorkflow implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $tries = 3;

    /** Longer than the longest run, shorter than the queue connection's retry_after (360). */
    public int $timeout = 300;

    public function __construct(
        public readonly WorkflowRun $run,
    ) {}

    public function handle(PersistenceInterface $runs, Pusher $pusher): void
    {
        $workflowId = $this->run->workflow_id;

        $workflow = ContentWorkflow::make(
            workflowId: $workflowId,
            state: new ContentState(['topic' => $this->run->topic]),
        )
            ->setPersistence($runs)
            ->setLeaseTimeout(600)
            ->setStreamAdapter(fn (): AgentChunkAdapter => new AgentChunkAdapter())
            ->setChannel(fn (): PusherChannel => new PusherChannel(
                client: $pusher,
                channel: "private-workflows.{$workflowId}",
                batchSize: 1,
            ));

        try {
            // The run ID was minted with the record: every delivery of this job names the same run.
            $state = $workflow->run(ExecutionRequest::start(
                runId: $this->run->run_id,
                recoverFailed: true,
            ));
        } catch (RunInFlightException $e) {
            if ($e->status !== WorkflowStatus::Running) {
                throw $e;   // paused, not dead: there is nothing to recover
            }

            // A delivery that was killed still holds the lease: come back when it has expired.
            $this->release(\max(1, $e->leaseExpiresAt - \time()));

            return;
        }

        if ($state->isInterrupted()) {
            $this->run->update(['status' => 'awaiting_approval']);

            return;   // Module 22 records and routes the approval
        }

        $this->run->update([
            'status' => 'completed',
            'result' => $state->get('final'),
        ]);
    }
}
```

### Five things this job does differently from a web request

**`run()`, not a loop.** With both an adapter and a channel attached, the workflow consumes its own stream and delivers every event through the channel as it happens. `run()` returns the final state when the segment completes or pauses. There is no generator to iterate and nothing to echo. Both setters take a factory, because an adapter and a channel hold the state of one segment's stream: the segment that pauses for an approval and the one that continues after it each build their own. An agent on a worker needs one thing more: its turn has to be a streamed one — `chat($message, stream: true)`, Lesson 7.5's eager form — because a plain `chat()` makes a buffered model call, and no text ever reaches the channel.

**The adapter still decides the shape.** A channel carries protocol events, never native objects, so it needs an adapter. `AgentChunkAdapter` is NeuronAI's own vocabulary for a consumer that speaks no UI protocol: each chunk or progress event becomes one event named after its kind — `text`, `tool-call`, `activity`, `step-started` — with the chunk's own fields as payload. If the browser runs an AG-UI or Vercel client, attach that adapter instead; the channel does not care.

**The channel reports the lifecycle.** After the adapter's terminal frames, the channel sends `stream.completed`, `stream.interrupted` or `stream.failed`, carrying only the workflow ID — no state, no exception details. There is no need for your own `WorkflowProgressed`, `WorkflowCompleted` or `WorkflowPaused` broadcast events: the browser learns the outcome from the stream and fetches the result from your application, which is the authoritative record.

**The pause is a return value.** An interrupted run returns normally with `isInterrupted()` true — nothing to catch. Module 22 takes it from there.

**A redelivery finishes the same run.** Retrying a job this expensive sounds like paying twice. It is not, because of Lesson 13.5: every completed node is a committed step. The run ID was minted with the record, so every delivery of this job names the same run, and `recoverFailed: true` tells a start that finds that run failed — or still marked as running by a worker that was killed, once its lease has expired — to continue it instead of beginning again. Committed steps are replayed from the store, not executed: the research and the draft the first delivery paid for are not bought twice, and only the node that was running when it died runs again. A plain `run()` also recovers a failed run, but it replaces one whose worker was killed, and starts over from the first node. While the dead delivery's lease is still fresh the start is refused with `RunInFlightException`, and the job releases itself until the lease has expired.

Three clocks make that safe. The lease — `setLeaseTimeout(600)`: a plain workflow has no lease until you set one, an agent defaults to the same ten minutes — must outlast the longest single node, so that a slow run is never taken for a dead one. The job's `$timeout` must outlast the longest run. And the queue connection's `retry_after` must exceed `$timeout`: `DB_QUEUE_RETRY_AFTER=360` for a `$timeout` of 300, `REDIS_QUEUE_RETRY_AFTER` on a Redis queue. Laravel ships 90, which hands a job that is still running to a second worker. What the store cannot do is remember a run that completed — its records are deleted — so a job delivered again after it succeeded starts a new run; the clocks are what keep that from happening.

`AgentChunkAdapter` forwards everything it is given, including tool call arguments and tool results. For a progress screen shown to the person who started the run that is usually fine; for anything customer-facing, suppress what should not travel with `mapEvent(ToolResultChunk::class, fn () => null)`, or attach the AG-UI adapter and let the frontend decide. Lesson 7.4's rule does not stop applying because the transport changed.

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

Two defaults of `PusherChannel` are worth knowing before the first run. It sends events in batches of ten, and a partial batch waits until it fills or the segment ends, so a handful of progress events would all arrive at the finish: `batchSize: 1` in the job is what makes each one leave as it is produced. And a channel name admits letters, digits and `-_=@,.;` only. A workflow ID that becomes part of one cannot contain a colon, so Lesson 18.3's `t1:refund:42` style needs another separator here — `t1.content.42`.

Prefer Redis? A factory returning `new RedisChannel($redis, "workflows:{$id}")` publishes the same envelopes on Redis Pub/Sub for a process that holds the browser's connection. Prefer Laravel's own broadcasting? `CallbackChannel` wraps a closure per lifecycle method, so `onSend` can call `Broadcast::private(...)->as($event->type)->with($event->data)->sendNow()`. **`sendNow()`, never a queued broadcast**. A queued broadcast lines your progress updates up behind the job producing them — on a single worker, a deadlock in slow motion — and with several workers it delivers them out of order.

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

channel.bind('pusher:subscription_succeeded', function once() {
    channel.unbind('pusher:subscription_succeeded', once);   // it fires again on every reconnect
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

Without this, anyone who guesses a workflow ID watches someone else's agent work. Lesson 18.3's four leak points had a fifth cousin: the broadcast channel. For content that must stay confidential even from the broadcast provider, use a `private-encrypted-*` channel with the SDK's encryption master key; the browser needs `pusher-js/with-encryption`, and the package's consumer is unchanged.

### What this composes

Worth listing on a slide, because this single job is the course converging:

- Workflow streaming with `yield` and portable progress events (14.4, 21.4)
- Durable steps, replayed when a job is delivered again (13.5)
- Interruption and persistence (15.4)
- Database persistence (18.4)
- Async execution (16.4)
- Adapters pushing to an external transport (7.5)
- `pcntl` and `posix` available, so parallel tools work (5.13)
- Inspector subscribed on the workflow (23.3)

That last one is the misconfiguration most likely to bite: nothing is monitored unless you subscribe the listener, and a worker is exactly where nobody notices it is missing.

### Key takeaways

- Push, not pull: an adapter factory plus a channel factory, and the worker just calls `run()`.
- Subscribe first, then start the run — Pusher and Redis do not replay.
- `PusherChannel` sends sequenced, fragmentable envelopes, in batches of ten unless you pass `batchSize: 1`; `@neuron-core/streaming` reorders, reassembles and reports gaps.
- The channel reports completion, pause and failure; fetch results from the application.
- Authorise the channel by tenant. Reserve the run ID and let the job retry: a redelivery finishes the same run from its last committed step, provided `retry_after` exceeds `$timeout`.

---
═══════════════════════════════════════════════════════════════

## LESSON 21.6 — Disconnection and Orphaned Cost

**Duration:** 9 minutes
**Type:** Theory with code

### Learning objectives

Stop paying for work nobody is waiting for, and keep a cut-off turn from blocking the next one.

### The problem nobody mentions

A user starts a 30-second agent run. At second four they close the tab.

What happens next depends on where the run lives. On a queue worker nothing happens at all: the browser is gone and **the agent keeps running.** Every remaining model call is billed. In a multi-agent workflow that is a substantial amount of money spent on output nobody will ever read. In a streamed response the opposite happens: the run is cut off in mid-turn, and what it had already written decides whether the user's next message gets an answer.

At low volume both are invisible. At scale the first is a line item and the second is a support ticket.

### What a disconnect does to a streamed response

With PHP's default `ignore_user_abort=0`, your loop never learns that the client has gone. PHP learns it, on the first write after the disconnect, and terminates the script there and then. No line after that `echo` runs: a `connection_aborted()` check at the top of the loop is never reached, the `done` event is never sent, the code after the `foreach` never executes.

The engine does notice. A run whose consumer stops pulling before it has settled is recorded as **failed**, at once, as the request shuts down and the generator is destroyed. It does not stay marked as running until the agent's ten-minute lease expires, so the thread is not locked against the next message.

What is lost is the answer. If it is worth having whether or not anyone is watching, say so in Lesson 21.1's controller, before the response is returned:

```php
// The run now completes into the history even if the tab closes.
\ignore_user_abort(true);

return response()->stream(function () use ($stream) {
    foreach ($stream as $chunk) {
        if (! $chunk instanceof TextChunk || \connection_aborted()) {
            continue;   // nobody is reading: keep pulling, stop writing
        }

        // ... frame, echo and flush as in Lesson 21.1
    }

    // ... the done event
}, 200, [/* ... the same four headers */]);
```

Only now does `connection_aborted()` mean anything: the script survives the failed write, and the function reports it from the next iteration on. The loop keeps pulling, so the turn finishes and the user finds the complete answer when they come back. Replace `continue` with `break` and you are back to the default behaviour, by choice: the engine fails the run when the request ends and the generator is released.

The other way to keep the answer is not to tie the run to the request at all: Lesson 21.5's queued run, which no browser can interrupt.

**One honest caveat:** whichever you choose, the tokens generated before the disconnect are billed. Ending the run limits the damage; it does not undo it.

### Why the next message can fail

The failed run itself is harmless: the next turn on the thread replaces it. What matters is what the failed turn had already stored.

If the client left before the first answer began, nothing was stored, and the next message is simply answered. If it left after a tool step, the user's question is already in the history. A second user message straight after it is not a valid conversation, so the next `chat()` or `stream()` throws `ChatHistoryException: Invalid message sequence` — and by then it has replaced the failed run, the one thing that could have been recovered.

So finish the failed turn first. That is `recoverFailedTurn()`, from Lesson 18.4: `inspect()` the thread's run, and if its status is `Failed`, continue it with `run(ExecutionRequest::resume(expectedRunId: ..., expectedExecutionAttempt: ...))`. The run completes from its committed steps — a tool that already ran is not run again — its answer lands in the history, and the new question then follows a valid conversation. It is why every endpoint in this module calls it before starting a turn. It is not free: it finishes every failed turn, the one that had stored nothing included, so each abandoned question costs a model call for an answer the user did not wait for. That is the price of a thread that stays usable.

One case `recoverFailedTurn()` cannot see: a process killed outright — out of memory, FPM's `request_terminate_timeout` — runs no destructor and records nothing. Its run stays `running`, and new turns on the thread are refused with `RunInFlightException` until the lease expires. If the question had been stored, the turn after that fails as above, and Lesson 18.4's `resetConversation()` is what is left.

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

        // ... the review itself, as in Module 14
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

Record actual usage from each inference's token counts — Lesson 23.1 subscribes a listener that does exactly this. Lesson 1.3 said capture usage from the first prototype; this is what you capture it for.

### Key takeaways

- A closed tab does not stop a queued run — you keep paying — and it cuts a streamed one off in mid-turn.
- With the default `ignore_user_abort=0` PHP ends the script on the next write; the engine fails the run at once, and the thread is not left locked.
- `ignore_user_abort(true)`, or a queued run, keeps the answer.
- A failed turn that had stored its question blocks the next one: `recoverFailedTurn()` before every turn.
- Queued work should be cancelled explicitly, between steps, not inferred.
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

Because a suspended run lives in your database, "the AI is waiting for a human" is a fact your application can hold as a record. Which means it gets everything database records get: a status, an owner, a deadline, an index page, a policy, an audit trail.

**Human-in-the-loop stops being an AI feature and becomes a workflow feature of your application.** That reframing is the point of this module.

### The supporting table

The framework's `workflow_store` table holds the run itself: its control record, its completed steps, its suspended state, the pending request. You want a companion table holding the *business* view:

```php
Schema::create('pending_approvals', function (Blueprint $table) {
    $table->id();
    $table->string('workflow_id');          // the continuation handle, e.g. refund:1042
    $table->string('run_id');               // the generation that asked
    $table->unsignedInteger('interrupt_id');        // which of that run's pauses
    $table->unsignedInteger('execution_attempt');   // the attempt that paused
    $table->foreignId('tenant_id')->constrained();
    $table->foreignId('requested_by')->nullable()->constrained('users');
    $table->foreignId('resolved_by')->nullable()->constrained('users');

    $table->string('type');                 // refund, publish, escalation
    $table->string('subject_type')->nullable();
    $table->unsignedBigInteger('subject_id')->nullable();

    $table->json('request');                // the InterruptRequest, as JSON, for rendering
    $table->json('response')->nullable();   // what the human decided

    $table->string('status')->default('pending');   // pending|approved|rejected|expired|failed
    $table->timestamp('expires_at')->nullable();
    $table->timestamp('resolved_at')->nullable();

    $table->timestamps();

    $table->unique(['workflow_id', 'run_id', 'interrupt_id']);
    $table->index(['tenant_id', 'status']);
    $table->index('expires_at');
});
```

**Why two tables.** The framework's table is a set of opaque serialised records keyed by partition — you cannot query it, filter it, or authorise against it, and you should not try: its rows change under conditional writes you do not control. Yours is a normal record you can index, scope and render. Separating them means the framework owns its internals and you own your product.

**What you copy across is a projection, not the request.** The workflow persistence stays authoritative for the pending request. Your table keeps what it needs to route the answer — the workflow ID, the run ID, the interrupt ID and the execution attempt it observed — plus a JSON rendering of the request for the screen. The run ID and attempt are the delivery fences of Lesson 22.3; without them a late or duplicated answer cannot be told apart from a current one. The interrupt ID is there because one run can pause more than once — a rejection that loops back, a node that waits twice — and each pause gets a row of its own; a unique key without it would refuse the second.

Also worth noting: `subject_type` / `subject_id` is a morph, so an approval links to the order, article or invoice it concerns. Without it, your approval screen shows an opaque JSON payload and the approver has to go and find the record themselves.

### The states

```
pending ──approve──→ approved ──→ (workflow resumed) ──→ completed
   │
   ├────reject───→ rejected ──→ (workflow resumed with rejection)
   │
   └────deadline─→ expired ──→ (workflow resumed with no answer; the node takes its timeout branch)
```

**Every path resumes the workflow.** Approval continues it, rejection is another iteration (Lesson 15.2's loop-back), and an expiry is the workflow noticing its own deadline. None of them is a dead end that leaves a suspended run behind.

### The four questions, answered

Lesson 15.4 posed them. Here are the Laravel answers, which the next lessons build:

| Question | Answer |
|---|---|
| Who is notified? | A `Notification` dispatched when the run returns interrupted (22.2) |
| What if nobody responds? | `expiresAt` on the request, plus a scheduled inputless resume (22.4) |
| How to prevent double-resume? | The engine's conditional writes and delivery fences, plus `lockForUpdate()` on your record (22.3) |
| What about deployments? | Small, flat, rarely-changed interrupt requests with defaulted properties (22.4) |

### Key takeaways

- A suspended run is a database fact, so approvals are ordinary application state.
- Two tables: the framework's opaque store and your queryable business record.
- Copy a projection — workflow ID, run ID, interrupt ID, attempt — never treat your copy as the source of truth.
- Morph to the subject so approvers see what they are deciding about.
- Every outcome, including expiry, resumes the workflow.

---
═══════════════════════════════════════════════════════════════

## LESSON 22.2 — Detecting the Pause and Notifying

**Duration:** 12 minutes
**Type:** Hands-on

### Learning objectives

Turn an interrupted result into a decision waiting in someone's inbox.

### The job that starts the run

```php
public function handle(PersistenceInterface $runs): void
{
    try {
        $state = RefundWorkflow::make(orderId: $this->orderId, requestedAmount: $this->amount)
            ->setPersistence($runs)
            ->setLeaseTimeout(600)
            // Minted with the request: every delivery of this job names the same run.
            ->run(ExecutionRequest::start(runId: $this->runId, recoverFailed: true));
    } catch (RunInFlightException $e) {
        if ($e->reservedRunId !== $e->runId) {
            // One live run per workflow ID: another request's refund holds this order.
            $this->recordDuplicateRequest($e->status);
        } elseif ($e->status === WorkflowStatus::Suspended) {
            // An earlier delivery paused this run and died before it recorded the pause.
            $this->recordPause($e->workflowId, $e->runId, $e->executionAttempt, $e->interrupt);
        } else {
            // A killed delivery still holds the lease: come back when it has expired.
            $this->release(\max(1, $e->leaseExpiresAt - \time()));
        }

        return;
    }

    if (! $state->isInterrupted()) {
        $this->recordCompletion($state);

        return;
    }

    $this->recordPause(
        $state->getWorkflowId(),
        $state->getRunId(),
        $state->getExecutionAttempt(),
        $state->getInterruptRequest(),
    );
}

private function recordPause(
    string $workflowId,
    string $runId,
    int $attempt,
    InterruptRequest $request,
): void {
    // Repeatable: a redelivery finds the row, and nobody is notified twice.
    $approval = PendingApproval::firstOrCreate([
        'workflow_id'  => $workflowId,
        'run_id'       => $runId,
        'interrupt_id' => $request->getId(),
    ], [
        'execution_attempt' => $attempt,
        'tenant_id'         => $this->tenantId,
        'type'              => 'refund',
        'subject_type'      => Order::class,
        'subject_id'        => $this->orderId,
        'request'           => \json_encode($request),
        'status'            => 'pending',
        'expires_at'        => $request instanceof RefundApprovalRequest ? $request->getExpiresAt() : null,
    ]);

    if ($approval->wasRecentlyCreated) {
        Notification::send(
            $this->approversFor($approval),
            new ApprovalRequired($approval)
        );
    }
}
```

Nothing is caught for the pause. `run()` returns normally, and the state says whether the run finished or is waiting. The pause is a result, not an exception (Lesson 15.1) — which is why the business record and the notification sit on an ordinary `if`. (The v3 version of this lesson wrapped `$workflow->init()` in a `catch (WorkflowInterrupt $interrupt)` block and read `$handler->getResult()`; none of that exists in 4.0.3.)

**The run ID is reserved, not generated.** The controller that accepts the refund request mints it — `(string) Str::uuid()` — and passes it to the job with the order and the amount, so every delivery of that job names the same run. `ExecutionRequest::start(runId: ..., recoverFailed: true)` then says the same thing each time: start this run or, if an earlier delivery left it failed or its worker was killed, finish it from its last committed step. A plain `run()` cannot say that. It recovers whatever failed run it finds under the workflow ID, so a second request for an order whose first refund failed halfway would silently finish the *first* request — its amount, its case — and report it as the second.

The one exception worth catching is `RunInFlightException`. `RefundWorkflow` declares `refund:{orderId}` as its workflow ID (Lesson 15.4), and a reserved start never replaces a run it did not start, so a second refund request for an order whose first one is still awaiting approval — or failed, and is waiting to be recovered — is refused before anything runs. That is a business rule you get for free; turn it into a message rather than a failed job. `reservedRunId` tells that case from the other two, in which the run in the way is this job's own. Found suspended, it was paused by an earlier delivery that died before it recorded the pause: the exception carries the run ID, the attempt and the request, which is all the record needs. Found still running, the job goes back on the queue until the lease has expired.

`recordPause()` is written to be repeated: `firstOrCreate()` on the table's unique key means a redelivery finds the row an earlier delivery wrote, and only the delivery that created it notifies. The persistence is Module 18's binding — `DatabasePersistence` over Laravel's own connection — injected into `handle()`. The lease, and the `$tries = 3` and `$timeout = 300` this job declares like the next one, are explained in Lessons 22.3 and 22.4.

The deadline comes from the request. `RefundApprovalRequest` is a `WaitForEventRequest` subclass (Lesson 15.3), and the node that raises it sets `expiresAt` — so the 48 hours live in one place, the workflow, and your table merely mirrors them for indexing.

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

`$request['message']` is there because `RefundApprovalRequest::metadata()` puts it there. The JSON form of a request is the framework's fields — `interruptId`, `type`, `eventName`, `expiresAt` — followed by whatever your subclass adds; design `metadata()` for the screen and the email, since they are its only readers.

### Two design points

**Include enough in the email to decide — but decide in the app.**

The subject line and body should tell the approver what this is about, so they can triage without clicking. The decision itself happens on an authenticated page, because that is where you can authorise it, lock it and audit it.

Resist one-click approve/reject links in email. They are convenient, and they are a signed-URL security surface you now have to get right.

**State the expiry.** An approver who knows the request expires in 48 hours behaves differently from one who does not. It also makes Lesson 22.4's timeout policy visible rather than surprising.

### Key takeaways

- `run()` returns; on `isInterrupted()`, record the projection and notify.
- Start with a run ID reserved by the request and `recoverFailed: true`, never with a plain `run()`.
- Catch `RunInFlightException` — one live run per workflow ID is a business rule, and `reservedRunId` tells a second request from a redelivery.
- The deadline lives on the request; your table mirrors it.
- Route approvers by role, tenant and threshold.
- Email for awareness; decide in the authenticated application.

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
        Gate::authorize('resolve', $approval);

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
    Gate::authorize('resolve', $approval);

    $requested = \json_decode($approval->request, true)['amount'];

    $validated = $request->validate([
        'decision' => ['required', 'in:approve,reject'],
        'feedback' => ['nullable', 'string', 'max:2000'],
        // The approver may lower the amount, never raise it.
        'amount'   => ['nullable', 'numeric', 'min:0', "max:{$requested}"],
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

    ResumeRefundWorkflow::dispatch($locked, $validated);

    return redirect()
        ->route('approvals.index')
        ->with('status', 'Decision recorded. The workflow is continuing.');
}
```

### Two layers, two jobs

Two managers open the same email and both click approve. Two things must not happen: the refund must not be paid twice, and your records must not say two people approved it.

**The engine owns the first.** Every mutation of a run is a conditional write against its control record, so only one continuation can be accepted. A second resume of a finished run finds nothing in flight; one racing the first loses the write. For a refund that is the difference between paying once and paying twice, and it holds even if your own code gets the lock wrong.

**Your lock owns the second.** `lockForUpdate()` inside a transaction, with the status checked *after* acquiring the lock — checking before is a race. Without it the engine still pays once, but both managers see "decision recorded", both are stored as the approver, and the audit trail lies. The lock is what turns the second click into "already resolved by someone else".

**Resume is dispatched, not executed inline.** The controller records a decision and returns. Resuming may take a minute; the approver should not wait for it, and an HTTP timeout should not orphan the workflow.

That third point is easy to skip and it is the difference between a screen that feels instant and one that hangs.

### The resume job

```php
class ResumeRefundWorkflow implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $tries = 3;

    /** Longer than the longest continuation, shorter than the queue's retry_after (360). */
    public int $timeout = 300;

    public function __construct(
        public readonly PendingApproval $approval,
        public readonly ?array $decision,   // null: deliver nothing, let the workflow check its deadline
    ) {}

    public function handle(PersistenceInterface $runs): void
    {
        $workflow = RefundWorkflow::make(orderId: $this->approval->subject_id)
            ->setPersistence($runs)
            ->setLeaseTimeout(600);

        try {
            $state = $workflow->run($this->request($workflow->inspect()));
        } catch (StaleWorkflowRunException $e) {
            // The run this answer was meant for is gone or replaced. Nothing was touched.
            Log::info('Stale refund resume ignored', ['approval' => $this->approval->id]);

            return;
        }

        if ($state->isInterrupted()) {
            return;   // still waiting: the deadline is not due yet
        }

        $this->recordOutcome($state);   // audit row, customer notification
    }

    private function request(?WorkflowRunSnapshot $run): ExecutionRequest
    {
        $runId = $this->approval->run_id;

        // A redelivery: the answer is already in and a later step failed. Finish that run.
        if ($run?->runId === $runId && $run->status === WorkflowStatus::Failed) {
            return ExecutionRequest::resume(
                expectedRunId: $runId,
                expectedExecutionAttempt: $run->executionAttempt,   // the attempt it is on now
            );
        }

        $fences = [
            'expectedRunId'            => $runId,
            'expectedExecutionAttempt' => $this->approval->execution_attempt,
        ];

        if ($this->decision === null) {
            // Nothing to deliver: the workflow checks its own deadline.
            return ExecutionRequest::resume(...$fences);
        }

        return ExecutionRequest::signal(
            RefundApprovalRequest::EVENT,
            $this->decision,
            ...$fences,
        );
    }
}
```

Lesson 15.4's requirements, now in a queue job: **the same workflow class**, rebuilt from the order ID alone because the class declares `refund:{orderId}` as its workflow ID; **the same persistence**; and **the payload** — a plain array, which the node reads directly. There is no interrupt request to reconstruct (the v3 job rebuilt one with `RefundApprovalInterrupt::fromArray()` and called `$workflow->init($request)->run()`).

What the job adds is the pair of **fences**. `expectedRunId` and `expectedExecutionAttempt` are the values the run reported when it paused, and the engine refuses to deliver the answer if the run has moved on since — a new generation under the same workflow ID, or another worker that already continued it. Queues redeliver, users double-click, deploys restart workers mid-job: the fences turn every one of those into a refusal instead of an answer applied to the wrong request.

**The first branch of `request()` is the one that gets refunds paid.** The job is retried — `$tries = 3` — because a continuation is safe to run again: completed steps are replayed from the store, not executed (Lesson 13.5). But a retry cannot simply repeat itself. Once the engine has accepted the answer the run is on a later attempt, and if a later step then throws — the payment API is down — the run is `failed` and the attempt in your table is stale for good: delivering the answer again can only be refused. So every delivery reads the run first. A run that is still this one and `Failed` already holds its answer; what it needs is an inputless resume fenced on the attempt it is on *now*, which reuses the committed steps and runs the failed one again. Without that branch an approved refund whose payment step failed once is never paid. With it, that step can run twice, so the payment call inside it must carry an idempotency key built from the workflow ID and the run ID — never from the attempt, which changes with every retry.

Retries need three clocks to agree, the same three as any queued run (Lesson 21.5). The lease — `setLeaseTimeout(600)` — must outlast the run's longest single step. The job's `$timeout` must outlast the longest continuation. And the queue connection's `retry_after` must exceed `$timeout`: `DB_QUEUE_RETRY_AFTER=360` for a `$timeout` of 300, where Laravel ships 90 and hands a job that is still running to a second worker. The start job of Lesson 22.2 declares the same `$tries` and `$timeout`.

> **Two fences, two exception types.** On neuron-ai 4.0.3 only the run-ID fence throws `StaleWorkflowRunException`. A stale *attempt* — the same run, already continued by another worker — throws a plain `WorkflowException` whose message begins *"Stale continuation"*, so the `catch` above lets it through and the job fails. Leave it that way. A stale run ID proves the run is gone or replaced; a stale attempt only says it has moved on, and it may have moved on into a worker that has since died. The retry reads the run again: gone, and the `catch` logs a no-op; failed, and `request()` finishes it; still held, and after the third try the job's `failed()` hook (Lesson 22.4) puts the approval in front of a human. Catch that exception as a no-op and an approved refund that nobody is paying is logged as harmless. Check the engine in your installed version before you rely on either behaviour.

Deliver the answer with `ExecutionRequest::signal()` rather than `ExecutionRequest::resume()`. Both take the two fences; Lesson 15.3's `signal()` also checks the event name, so a decision can only reach a run that is waiting for `refund.decided`. Keep the inputless `resume()` for the two cases with nothing to deliver: a deadline to check, and a failed run to finish.

### The editable case

For a content-review request (Lesson 15.3), the screen is a textarea:

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

The human edits the content; the edited version goes back into the workflow as the `content` key of the payload. Add `'content' => ['nullable', 'string']` to the validation rules and it travels through the same job unchanged. Lesson 15.3's collaboration pattern, in a form. This is far more useful than approve/reject for anything the AI drafted — because the common response is "almost".

### Key takeaways

- The engine prevents a double resume; `lockForUpdate()` keeps your records honest.
- Check status while holding the lock; record the decision, dispatch the resume — never resume inline.
- Rebuild from the business key, deliver the answer with `ExecutionRequest::signal()`, and fence with the run ID and attempt you stored.
- Retry the job, and read the run on every delivery: a run that failed after its answer went in is finished with an inputless resume on its current attempt.
- A stale run ID is a no-op: the run is gone. A stale attempt is not proof of anything — let the job fail and try again.
- For drafted content, a textarea beats two buttons.

---
═══════════════════════════════════════════════════════════════

## LESSON 22.4 — Timeouts, Zombies and Deployments

**Duration:** 13 minutes
**Type:** Hands-on

### Learning objectives

Keep a system with pausable workflows healthy over months.

### Expiring stale approvals

The deadline belongs to the workflow. `RefundApprovalRequest` carries `expiresAt`, and when an inputless `run(ExecutionRequest::resume())` arrives after it, the workflow re-enters the waiting node with no answer; `interruptIf()` returns `null` and the node takes its timeout branch. The node never compares clocks, and nothing in core runs a timer — your scheduler only has to knock:

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
                    ResumeRefundWorkflow::dispatch($approval, null);
                }
            });

        return self::SUCCESS;
    }
}
```

**Deliver nothing; do not manufacture a rejection.** A `null` decision is an inputless resume. Before the deadline — clock skew between servers, a request whose deadline moved — the workflow simply stays suspended and the job returns. After it, the node records an expiry and the run completes, notifies and cleans up. The job's `recordOutcome()` marks the approval `expired` from the state the workflow returned, so the record follows the workflow rather than the other way round.

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

### What is left in the store

A run that completes cleans up after itself: a clean finish conditionally deletes the run's whole partition in `workflow_store`, so completed refunds leave nothing behind. What accumulates is runs that never finish — suspended requests nobody will ever answer, runs whose worker failed and nobody retried.

Do not delete their rows by hand. The store's writes are fenced by its control record, and a raw `DELETE` can race a worker that is recovering the same run. Ask the engine instead:

```php
$engine = app(WorkflowEngine::class);

PendingApproval::query()
    ->where('status', 'failed')
    ->where('updated_at', '<', now()->subDays(30))
    ->each(function (PendingApproval $approval) use ($engine) {
        try {
            $engine->abandon($approval->workflow_id, $approval->run_id);
        } catch (StaleWorkflowRunException) {
            // Nothing of that run is left: it is gone, or a newer run holds the order.
        } catch (WorkflowException $e) {
            // Live under a lease, or a retained completion: not this sweep's to remove.
            report($e);
        }
    });
```

`WorkflowEngine` manages runs by workflow ID without building the workflow — all a sweep needs — and Laravel autowires it over Module 18's persistence binding. Its `abandon()` discards a paused, failed or dead run and frees the workflow ID, fenced by the run ID you pass. Leave the attempt out: the one in your table is the attempt that paused, and a run that failed afterwards has moved past it. When `abandon()` cannot do what you asked it throws, and an exception that escapes `each()` ends the sweep — hence the two catches. `StaleWorkflowRunException` means that run no longer holds the ID: it is already gone, or the order has a newer run. A plain `WorkflowException` is a refusal: a run that is live under a lease, or a retained completion. Thirty days of grace, then remove. (The v3 sweep deleted `workflow_interrupts` rows with a raw query; v4 has no such table.)

### Crashed workers and leases

A worker killed mid-run — the OOM killer, a deploy's `SIGKILL`, a job timeout — has no chance to record anything. Its run stays marked `running`, and the engine cannot tell that apart from a worker that is merely slow.

A **lease** resolves it. With `setLeaseTimeout(600)` the run holds a deadline that every committed step renews; once it lapses, the run counts as dead. A redelivery of the job that started it then recovers it, reusing the committed steps — that is what `recoverFailed: true` on the reserved start is for — and so does an inputless `run(ExecutionRequest::resume())`; a plain `run()` would replace it and begin again. Without a lease only an explicit `run(ExecutionRequest::resume())` can take the run over. An agent holds a ten-minute lease by default; a plain workflow holds none, which is why both jobs set one.

Choose the lease above the longest silent stretch between two steps — one slow provider call, one payment request — and not by the job's `$timeout`: each of Lesson 22.3's three clocks is measured against something different. A lease shorter than a slow provider call revives a run that was not dead — and then two workers are running it.

### Lost completions

One gap remains. The resume job's `run()` completes the refund, and the worker dies before `recordOutcome()` writes the audit row. The workflow is finished and its records are gone; your table still says `approved`, with no refund recorded.

For workflows where that matters, keep the outcome until you have recorded it:

```php
$workflow = RefundWorkflow::make(orderId: $this->approval->subject_id)
    ->setPersistence($runs)
    ->setLeaseTimeout(600)
    ->retainCompletionUntilAcknowledged();

$state = $workflow->run($this->request($workflow->inspect()));

// ...the stale and still-waiting returns, as above

$this->recordOutcome($state);

$workflow->acknowledge($this->approval->run_id);
```

With retention on, completion writes the terminal state into the store instead of deleting everything. If the worker dies before acknowledging, the redelivery finds the run `Completed`, and the answer it carries is stale. What it has to ask for is the outcome: `run(ExecutionRequest::resume(expectedRunId: $runId))`, with no payload, replays the retained outcome without executing any node; you record it, and then acknowledge. In `request()` that is one more status in the first branch — `Completed` next to `Failed`. Until then the workflow ID stays taken — a new start for that order throws `RunInFlightException`, whose message names `acknowledge()` and the run ID — which is exactly the reminder you want.

### The deployment problem, and how to live with it

Lesson 15.4 flagged it; here is the practical handling.

The persisted run contains **your classes**, serialised: the state, the events, the pending interrupt request. Rename a node, change a state class, add a typed property to an interrupt request — and deserialisation of in-flight runs breaks.

Four mitigations, in order of usefulness:

**1. Keep interrupt requests small and flat.** Strings, numbers, arrays. No models, no connections, no closures. The smaller the surface, the less there is to break.

**2. Add properties with defaults, and version the wire shape.**

```php
class RefundApprovalRequest extends WaitForEventRequest
{
    public const EVENT = 'refund.decided';

    public const VERSION = 2;

    // Added in version 2. Declared with a default, so requests suspended
    // by version 1 unserialise with 'EUR' instead of an uninitialised property.
    protected string $currency = 'EUR';

    public function __construct(
        final protected string $message,
        final protected int $orderId,
        final protected float $amount,
        ?DateTimeImmutable $expiresAt = null,
    ) {
        parent::__construct(self::EVENT, $expiresAt);
    }

    /**
     * The version-2 field is set with a wither, in the style of the
     * framework's own withId(): the constructor - and every call site written
     * for version 1 - stays as it was.
     *
     * PHP 8.5: clone() takes the properties to change, and #[\NoDiscard]
     * warns if the caller drops the copy and keeps the unchanged original.
     */
    #[\NoDiscard('withCurrency() returns a copy; the original request is unchanged.')]
    public function withCurrency(string $currency): static
    {
        return clone($this, ['currency' => $currency]);
    }

    public function getMessage(): string
    {
        return $this->message;
    }

    /**
     * @return array<string, mixed>
     */
    protected function metadata(): array
    {
        return [
            'version'  => self::VERSION,
            'message'  => $this->message,
            'orderId'  => $this->orderId,
            'amount'   => $this->amount,
            'currency' => $this->currency,
        ];
    }
}
```

The two halves solve different problems. Unserialising does not run your constructor, so a property that version 1 never wrote is simply missing: if it is declared with a default, the old request comes back with that default; if it is promoted, or typed without a default, the first read of it is a fatal error. The `version` in `metadata()` is for the other readers — the approval screen and whoever builds the resume payload — so a form rendered from a version 1 request can still be answered in the shape the node expects.

Two PHP 8.5 features keep the class honest. The promoted properties are `final`, so a subclass cannot redeclare the fields `metadata()` puts on the wire; and `clone($this, ['currency' => $currency])` copies the object and sets the listed properties in one expression, which is how `withCurrency()` adds the version 2 field without touching the constructor or any call site written for version 1. (Check these two by eye if your own PHP is older: `php -l` on 8.3 cannot parse them.)

**3. Drain before risky deploys.** For a release that changes workflow classes, stop dispatching new workflows, let pending ones resolve, then deploy. Upgrading NeuronAI itself counts as one of these: runs suspended by an older store format cannot be resumed by a newer one.

**4. Fail loudly.** A resume job that cannot deserialise the run throws. Let it: mark the approval as `failed` from the job's `failed()` hook, log the workflow ID and run ID, and leave the run for a human to recover or abandon. A visible failure is recoverable; a silent one is not.

### Monitoring

Four numbers worth a dashboard:

- Pending approvals, by age
- Approvals expired in the last 7 days *(a rising number means your process is broken, not your code)*
- Failed resumes, and stale resumes ignored — a steady trickle of the second is normal, a spike means something is redelivering
- Approvals stuck in `approved` with no recorded outcome — the lost completions of the previous section

### Key takeaways

- Expire with an inputless resume; the workflow checks its own deadline and takes its timeout branch.
- Escalate before expiring.
- Completed runs delete themselves; clean up the rest with `abandon()`, never a raw `DELETE`, and expect it to throw when there is nothing to abandon.
- Set a lease above the longest silent step, `$timeout` above the longest job and `retry_after` above `$timeout`; retain completions you cannot afford to lose.
- Serialised state contains your classes — keep requests flat, give new properties defaults, drain before risky deploys, and fail loudly.

---
═══════════════════════════════════════════════════════════════

## LESSON 22.5 — Agent Tool Approval in Laravel

**Duration:** 13 minutes
**Type:** Hands-on

### Learning objectives

Pause an agent on a gated tool call, show the approver what is waiting, and continue the run from another request.

### The agent

The refund workflow owns its pause: a node decides to interrupt. An agent's pause comes from a tool. Lesson 15.5 showed the mechanism — the tool declares an approval policy, the agent's `ToolNode` interrupts with one action per gated call, and `submitApprovalDecisions()` continues the run. Here is what it takes in a Laravel application:

```php
class SupportAgent extends Agent
{
    public function __construct(
        protected MessageStoreInterface $conversations,
        protected PersistenceInterface $runs,
    ) {
        parent::__construct();
    }

    protected function messageStore(): MessageStoreInterface
    {
        return $this->conversations;   // durable: it holds the pending tool call
    }

    protected function persistence(): PersistenceInterface
    {
        return $this->runs;            // durable: it holds the paused run
    }

    protected function tools(): array
    {
        $scope = ThreadScope::of($this->getThreadId());

        return [
            new SearchOrdersTool($scope->tenantId),
            (new IssueRefundTool($scope->tenantId))->requireApproval(),
        ];
    }

    // provider(), contextWindow() and recoverFailedTurn() as in Module 18
}
```

Two durable collaborators, and both are required. **Workflow persistence** holds the paused run; the default in-memory store would forget it when the request ends. **A durable message store** holds the conversation, including the assistant's pending tool call; without it the thread cannot be continued in another request. They are Module 18's two bindings, injected by the container and returned from the two hooks — and it has to be these hooks. An agent that still overrides `chatHistory()` loads and pauses without an error while its conversation stays in memory (Lesson 18.2). The approval card still renders, because the paused run is durable; approving it fails with `ChatHistoryException`, because the tool call it answers is no longer in any history.

Neither is given the thread ID. The stores are shared services; the thread is bound for each request, with `for()`. More than that: **the thread ID is the agent's workflow ID.** The paused run is filed in `workflow_store` under the thread, so everything that needs to find it — the approval endpoint, the page that reloads — needs the thread and nothing else. There is no run ID to store, which is why routing a decision needs no `pending_approvals` table here. The record of who approved what is still yours to keep: write it in `decide()`.

### One endpoint for a turn, one for the decisions

```php
class ThreadController extends Controller
{
    public function chat(
        Request $request,
        Conversation $conversation,
        SupportAgent $agent,
    ): JsonResponse {
        Gate::authorize('participate', $conversation);

        $validated = $request->validate(['message' => ['required', 'string', 'max:4000']]);

        $agent = $agent->for($conversation->threadId());
        $agent->recoverFailedTurn();

        try {
            $state = $agent->chat(new UserMessage($validated['message']));
        } catch (RunInFlightException $e) {
            // suspended: decisions are pending; running: another request holds the turn
            return response()->json([
                'status'  => $e->status->value,
                'pending' => $agent->pendingApprovals(),
            ], 409);
        }

        return $this->respond($agent, $state);
    }

    public function pending(Conversation $conversation, SupportAgent $agent): JsonResponse
    {
        Gate::authorize('participate', $conversation);

        return response()->json(
            $agent->for($conversation->threadId())->pendingApprovals()
        );
    }

    public function decide(
        Request $request,
        Conversation $conversation,
        SupportAgent $agent,
    ): JsonResponse {
        Gate::authorize('approveTools', $conversation);

        $validated = $request->validate(['decisions' => ['required', 'array']]);

        $agent = $agent->for($conversation->threadId());

        try {
            $state = $agent->submitApprovalDecisions($validated['decisions'])->run();
        } catch (InputTranslationException $e) {
            return response()->json(['error' => $e->getMessage()], 400);
        } catch (WorkflowException $e) {
            // Two approvers at once, and the other one won: send back what is still open.
            return response()->json([
                'status'  => 'conflict',
                'pending' => $agent->pendingApprovals(),
            ], 409);
        }

        return $this->respond($agent, $state);
    }

    private function respond(SupportAgent $agent, AgentState $state): JsonResponse
    {
        return response()->json($state->isInterrupted()
            ? ['status' => 'awaiting_approval', 'pending' => $agent->pendingApprovals()]
            : ['status' => 'completed', 'answer' => $state->getMessage()?->getContent()]);
    }
}
```

### What each piece is doing

**`RunInFlightException` is the lock you forgot to build.** A new message on a thread whose run is waiting for a decision is refused by the engine before anything reaches the model or the store. Map it to HTTP 409 and send the pending actions back, so the client can re-render them. Your UI should lock the input while approvals are open; this is what happens when it does not. The same exception with the status `running` is a second request arriving while a turn is still executing: the same 409, with nothing pending.

**`recoverFailedTurn()` comes before `chat()`.** Lesson 18.4's fifth question bites hardest here. The approver says yes, the refund is issued, and the provider fails on the very next call: the run is `failed` with its question already stored, and every later message on that thread is refused with `ChatHistoryException`. Finishing the failed turn first reuses the committed steps — the refund is not issued a second time — and costs one read when there is nothing to finish.

**`pendingApprovals()` survives a page refresh.** It reads the persisted interruption in a cold process and returns the `Action` objects still awaiting a decision — each with the tool call ID as `id`, the tool name, the reason the tool gave for asking, and its `inputs`. It is what the page calls on mount. It also reflects partial progress: an action already decided is no longer returned.

**Decisions are keyed by tool call ID** and take three forms: `'approve'`, `'reject'`, or `['reject', 'reason']`. Submissions are incremental — a request may carry only the newly decided actions, and the run re-suspends until all of them are in. A tool runs only if explicitly approved; silence is never consent. A decision for a call ID the run is not waiting for is rejected with `InputTranslationException` before anything executes — a 400, not a 500.

**Two approvers can still collide.** Both open the same card and both submit. `submitApprovalDecisions()` captures the run and the attempt it read, so only one continuation is accepted; the other's `run()` throws a `WorkflowException` — `StaleWorkflowRunException` when the winner has already finished the run, a plain one while the winner is still executing. That is a 409 with whatever is still pending, and a page that reloads, not a 500. The statuses are those of the application-wide mapping in `bootstrap/app.php` (Lesson 21.4); the local catches are there to send the pending actions with them.

**The approver need not be the person chatting.** `decide()` authorises a different ability from `chat()`. A customer's refund request can wait in their conversation while a manager, on another screen, calls `pendingApprovals()` for that thread and submits the decision. The thread ID is the only handle either of them needs — which is why it must come from a record the user is authorised for, never straight from the request (Lesson 18.2).

### Expiry for agent approvals

A tool approval carries no deadline of its own: a suspended agent run holds no lease and waits indefinitely. If your product needs one, keep it in your application and cancel by declining:

```php
$agent = app(SupportAgent::class)->for($conversation->threadId());

$agent->submitApprovalDecisions(
    collect($agent->pendingApprovals())
        ->mapWithKeys(fn (Action $action) => [$action->id => ['reject', 'No decision within 48 hours']])
        ->all()
)->run();
```

The model receives the rejection as the tool's result and answers the customer accordingly, and the thread is free again. Do not reach for `abandon()` here: on an agent it throws an `AgentException` while an approval is pending, because it would leave an unanswered tool call in the conversation. `resetConversation()` does free the thread, at the price of wiping its history.

### Key takeaways

- An approving agent needs durable workflow persistence and a durable message store, returned from `persistence()` and `messageStore()`.
- The thread ID is the workflow ID: one handle for the turn, the decisions and the reload.
- `RunInFlightException` means "decisions pending" — return 409 with `pendingApprovals()`; a lost race between two approvers is a 409 too.
- Recover a failed turn before every `chat()`.
- `pendingApprovals()` rebuilds the approval UI after a refresh; decisions are incremental and keyed by tool call ID.
- Agent approvals have no deadline; expire them by submitting rejections.

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

Observability in NeuronAI is a PSR-14 event dispatcher owned by each agent instance (Lesson 10.2), and `InferenceStop` fires after every model call — so this writes one row per inference, not per request. An agent that loops through three tool calls produces four rows, which is exactly the granularity that makes a looping agent visible. Two details are easy to get wrong: the token counts are on the *provider response's* message, `$event->response->message()->getUsage()` — `$event->message` is the last message *sent* — and `getUsage()` returns `null` when a provider reports nothing, so guard for it. (The v3 lesson sketch read `$event->usage->inputTokens` off an event that carried the usage directly; no such event exists in 4.0.3.)

The listener is told nothing about the caller. The event carries the thread the run is bound to, and the thread names the tenant and the user (Lesson 18.3) — the route the audit listener of Lesson 19.3 takes. The model is asked of the agent when the event fires, not when the listener is built: once the fallback factory of Lesson 23.2 can swap providers, a model name captured at subscription is a guess. And the write sits inside a `try`. `InferenceStop` is dispatched from within the run, so an exception thrown by a listener fails the turn; a usage table that is down should cost you a row, not an answer.

Subscribe it where agents are built, so no agent escapes it. Module 18's agents are built by the container, and an `afterResolving()` callback in `NeuronServiceProvider` runs for every `Agent` subclass the container resolves; the copy that `for()` makes keeps the listener. An agent constructed by hand with `::make()` never passes through the container, and is not recorded.

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

Call it where a turn starts, before the agent is bound — `$budget->check(ThreadScope::of($conversation->threadId()))` — and the browser gets a 429 with no question stored and no token spent. What a check before the turn cannot do is stop a loop inside a turn that is already running: the run limits of Lesson 5.9 bound that one.

**Also set a hard spend limit at the provider.** Lesson 3.7 said it and it bears repeating: application-level budgets depend on your code being correct. The provider's cap does not.

### Key takeaways

- Record tokens, model and agent on every inference, and price the row when you write it.
- Three levers: fewer iterations, smaller context, cheaper model per step.
- Cache deterministic tasks and embeddings; not conversations.
- Three budget tiers, checked before every turn, plus a hard cap at the provider.

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
use NeuronAI\HttpClient\Curl\CurlHttpClient;
use NeuronAI\Providers\Anthropic\Anthropic;

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

Build the provider in the hook, as here, rather than calling `setHttpClient()` on what `AIProvider::driver()` returns: the manager hands every agent the same provider object (Lesson 17.6), so a client set on it changes the timeout for all of them. If you need Guzzle middleware — a retry handler, a proxy, request signing — `GuzzleHttpClient` is available as an opt-in adapter once you require `guzzlehttp/guzzle` yourself, and `CurlHttpClient` accepts raw `curlOptions` for proxies and CA bundles. (The `'timeout' => env('NEURON_HTTP_TIMEOUT', 60)` config key of the v3 lesson is not read by anything in the SDK.)

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

The run ID is what makes a retry safe in both cases. The controller mints it when it dispatches, so every delivery of the job names the same run, and the job starts the turn with `ExecutionRequest::start()` because `chat()` cannot reserve an ID. The first delivery starts that run. A redelivery — after an exception, after a killed worker — finds it, and `recoverFailed: true` makes it finish the run from its last completed step instead of starting over: the question is not stored twice, an inference that was already paid for is not paid for again, and a tool that already ran does not run again. Only the step that was in flight is repeated, which is why a write tool still needs the idempotency key of Lesson 19.2.

Three clocks have to be in order for that to hold, and Laravel's defaults put one of them wrong:

- **The run's lease** — 600 seconds by default for an agent, `setLeaseTimeout()` — longer than the longest single step, one inference or one batch of tools. A live run is then never taken for a dead one.
- **The job's `$timeout`** — 300 — longer than the longest turn. Laravel kills a job that exceeds it; its run stays `running` until the lease expires, and a later delivery finishes it.
- **The queue's `retry_after`** — 360 — longer than `$timeout`. Laravel ships 90, and with that a second worker takes the job while the first is still answering: the turn runs twice. Set `DB_QUEUE_RETRY_AFTER=360` in `.env`, or `REDIS_QUEUE_RETRY_AFTER` on a Redis queue.

While a run is still leased to a worker that died, the engine refuses the start with `RunInFlightException`. A complete job catches it and releases itself until `$e->leaseExpiresAt` rather than spend an attempt on it, as Lesson 21.5's job does; the maintainers' `neuron-laravel-integration` skill prints that handler under "Background Runs".

One interaction to know about: the rate limiter's releases come out of the same three attempts. Where the limit is tight enough to release a job more than once, count failures instead of deliveries — `retryUntil()` with `$maxExceptions = 3`, as the indexing jobs of Lesson 20.2 do — and drop `$tries`, which Laravel ignores as soon as a job defines `retryUntil()`.

Lesson 21.5 and Lesson 22.3 declare `$tries = 3` for the same reason this job does. An older version of this lesson set `$tries = 1` on every agent job to avoid blind retries; with a reserved run ID and `recoverFailed: true` a retry resumes instead of repeating, so the blanket `1` is no longer the safe default — provided your write tools carry the idempotency key.

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

**Two caveats worth stating so this does not look like a free lunch:**

**Quality varies across providers.** A prompt tuned for one model may perform noticeably worse on another. Fallback keeps you available; it does not keep you equally good. Run your evals (Module 10) against every provider in the chain so you know what you are degrading to.

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

A keyword search result beats an error page. Users notice outages; they rarely notice a slightly worse answer. (`$this->agent` here is already bound to its thread, as in every endpoint of this part.)

### Key takeaways

- Rate limit before the provider does; queue rather than fail, and never `dontRelease()`.
- Retry transport failures, not reasoning: a reserved run ID with `recoverFailed: true` lets a redelivery finish the turn instead of repeating it.
- Three clocks in order: lease above the longest step, `$timeout` above the longest turn, `retry_after` above `$timeout`.
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
composer require inspector-apm/inspector-laravel "inspector-apm/inspector-php:^3.19"
```

```dotenv
INSPECTOR_INGESTION_KEY=...
```

That monitors your HTTP requests and jobs — and no agent. NeuronAI does not depend on Inspector and attaches nothing by default; older tutorials that stop at the environment variable describe a setup that no longer exists. Lesson 10.2 covers the mechanism, and the reason the command names a second package: the Laravel package accepts older releases of `inspector-apm/inspector-php` than the subscriber needs, and 3.18.1 to 3.18.3 ship a subscriber written for a pre-release namespace, which subscribes without complaint and records nothing. In Laravel, subscribe the listener where agents are built — the `afterResolving()` callback of Lesson 23.1 — and hand it the Inspector instance the Laravel package already owns:

```php
use Inspector\Neuron\V4\InspectorSubscriber;
use NeuronAI\Observability\ObservabilityEvent;

$agent->subscribe(ObservabilityEvent::class, new InspectorSubscriber(app('inspector')));
```

Passing the host's instance is the point of the Laravel package. The agent's segments land inside the transaction Inspector already opened for the request or the queue job, which correlates the agent trace with the queries, HTTP calls and job around it — what you actually want when diagnosing an incident. Without it you have an agent timeline floating unattached to the request that produced it.

Queue workers need nothing extra. The subscriber flushes at the end of a run only when it opened the transaction itself, and leaves a transaction owned by the host — a job monitored by the Laravel package — for the host to close. (The `InspectorObserver::instance(key:, autoFlush: true)` setup and `$this->observe(...)` of the v3 lesson do not exist in 4.0.3.)

The failure mode to watch for is an agent nobody subscribed: it produces no error and no trace at all, and a worker is exactly where nobody notices. Subscribe in the service provider, never at call sites.

Inspector is not the only backend. The maintainers' monitoring guide documents Neuron Cloud, which has a Laravel package of its own, `neuron-core/neuron-cloud-laravel`: the same kind of listener, subscribed in the same place. Lesson 10.2 says what to check before you plan on it.

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
    Order::factory()->for($this->tenantA)->create(['number' => 'A-001', 'status' => 'shipped']);
    Order::factory()->for($this->tenantB)->create(['number' => 'B-001', 'status' => 'shipped']);

    $result = (string) (new SearchOrdersTool($this->tenantA->id))(status: 'shipped');

    $this->assertStringContainsString('A-001', $result);
    $this->assertStringNotContainsString('B-001', $result);
}
```

No LLM. No network. Both orders are `shipped`, so the status filter lets both through and only the tenant scope can keep `B-001` out; the first assertion proves the search found anything at all. A test that passes on an empty result protects nothing. This is where most of your agent-related logic should live, and the reason Lesson 5.3 argued for tool classes.

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

Tests your controller, your validation, your authorisation, your serialisation — and the real agent, with its real instructions and tools. Only the model is replaced, through the seam of Lesson 18.1: the container hands out an agent whose provider is the fake, and the copy `for()` makes shares it.

`FakeAIProvider` implements the same interface as a real provider: queue the responses it should return, including tool-call messages to drive the agent's loop, and assert on what it was sent with `assertSent()`. The framework ships the same pattern for the other seams — `FakeEmbeddingsProvider`, `FakeVectorStore`, `FakeChannel` for streamed output — so a RAG endpoint or a queued stream can be tested the same way.

**Tier 3 — Evals. Slow, costs money, measures quality (Module 10).**

```bash
php artisan neuron:evaluate --env=evaluation
```

Not `vendor/bin/neuron evaluation`, the command of Module 10: it does not boot Laravel, so an evaluator that touches a model, a facade or the container fails on every item. `neuron:evaluate` is an Artisan command of your own that runs the same evaluation CLI inside the booted application, with the container building the evaluators. It is one short class, which the maintainers print in the `neuron-laravel-integration` skill (`references/evaluation.md`): create it with `php artisan make:command NeuronEvaluate` and replace the class. Evaluations run the real tools — approving a refund refunds that order — so they get a database of their own. `--env=evaluation` selects `.env.evaluation`, the command refuses to run when that file was not loaded, and a seeder rebuilds the data the datasets name before every run. (The v3 form, `vendor/bin/neuron evaluations --path=evaluators`, is the plural command of the older CLI.)

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

Three rules from Lesson 10.6, restated because they are easy to get wrong:

**Do not gate every PR on the full eval suite.** It costs money and it is slow. Nightly, plus opt-in with a commit tag.

**Do not fail on a single item.** Set a success-rate threshold. On a probabilistic system a 95 % pass rate is a healthy build, and treating one flaky item as failure teaches the team to ignore the signal entirely. The command exits non-zero on any failed item and has no threshold flag, so the step ignores its exit code and reads `success_rate` from the JSON report, as Lesson 10.6 did; here `evaluation.php` writes that report to `storage/logs/evaluation.json`.

**Keep API keys out of forks.** Eval-on-PR in a public repository is a way to donate your budget to strangers.

### The security tests that must gate deploys

Two from Part V, both deterministic enough to trust:

```text
public function test_tenant_a_history_never_reaches_tenant_b(): void;      // Lesson 18.3
public function test_customer_cannot_retrieve_internal_articles(): void;   // Lesson 20.3
```

These belong in tier 1 or 2, run on every commit, and block the merge. Run them in the form that asserts on what reached the model, through a fake provider: no model is called, so the result is the same on every run. They are among the few AI-adjacent tests that are both reliable and consequential.

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
| Approval | `approvalPolicy()` / `requireApproval()` on consequential tools | 15.5, 22.5 |
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

**Right to erasure.** A user asks to be deleted. Their chat history is in your `chat_messages` table — deletable, the archived rows included (Lesson 18.2). Two more places hold their words. A run paused for an approval keeps its serialised state — the question, the tool arguments, any retrieved text — in `workflow_store` until it is settled; `resetConversation()` on the bound agent discards that run together with the thread's history. Long-term memory (Lesson 4.5) lives in a store that `resetConversation()` does not touch, so delete those documents separately. Their data inside a provider's logs is subject to that provider's retention policy, which is why zero-retention matters.

**Right of access.** Chat history and any long-term memory (Lesson 4.5) are personal data the user can request.

**Automated decision-making.** If an agent makes a decision with legal or similarly significant effect on someone, GDPR Article 22 is relevant. This is a strong argument for human-in-the-loop on consequential actions — Module 15 is a compliance feature as well as a safety one.

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

This is the table the `ToolCalled` listener of Lesson 19.3 writes to, one row per tool call, keyed by the thread and the call ID so that a replayed call updates its row instead of adding one. Without it you have logs, a trace that may have expired, and a shrug. With it you have a row naming the user, the tool, the arguments, the outcome, the approver and the time. In a regulated environment this is the difference between deployable and not.

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
- [ ] `NEURON_AI_PROVIDER` and `NEURON_EMBEDDING_PROVIDER` set in every environment — neither has a default (17.2)
- [ ] Context window derived from the configured provider, not hardcoded (4.4)
- [ ] Hard spend limit set at the provider (3.7)
- [ ] Separate API keys per environment
- [ ] Secret scanning in CI

### Agents and tools

- [ ] Every write tool: `setMaxRuns(1)` with an error handler for the limit, idempotency key (the call ID), transaction (5.9, 19.2)
- [ ] Every tool: bounded result set, explicit column selection, compact output (19.1)
- [ ] Every tool: an explicit sentence for the empty case, `ToolOutput::error()` for refusals — never a thrown exception (5.9, 19.1)
- [ ] Tool visibility computed from the actor's policies (5.10, 19.3)
- [ ] `Gate::forUser()->allows()` inside tools that touch specific records (19.3)
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
- [ ] Queued turns start a reserved run with `recoverFailed: true`, so a redelivery finishes the turn instead of repeating it (21.5, 23.2)
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
