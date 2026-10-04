# Chapter 21 — Streaming to the Frontend

::: {.callout .callout-tip}
[Code for this chapter]{.callout-title}

The Laravel listings below live inside an application, but the parts that do not need one are runnable at [`chapters/Ch21`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch21) in the companion repository: `sse-frames.php` prints the exact frames Section 21.1's endpoint sends, `channel.php` prints the envelopes a push channel publishes in Section 21.5, and `disconnect.php` reproduces Section 21.6's disconnection behaviour. None of them needs a model.
:::

## 21.1 Server-Sent Events in Laravel

### Why SSE rather than WebSockets

For agent responses the traffic is one-directional: the server sends, the browser receives. SSE gives you that over ordinary HTTP, with a client built into the browser and no extra infrastructure.

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

Before there is a loop there is an agent, and it arrives the way Section 18.1 built it. The route names the conversation — `Route::get('/chat/stream/{conversation}', ChatStreamController::class)` — the action receives the agent by method injection, and `for()` binds it to the conversation's thread once the policy has authorised the user. An agent with no thread bound does not stream at all. `recoverFailedTurn()` is the answer to Section 18.4's fifth question, given before the turn and never after; Section 21.6 shows why a streaming endpoint is where it earns its place.

`stream()` is itself the generator — iterate it directly. It is also lazy: nothing runs until the first item is pulled, and `$stream->valid()` pulls it in the controller, before the response exists. A thread that cannot take the turn — another tab is still streaming on it — is then refused with an HTTP status, the 409 Section 21.4 maps it to, instead of a `200` that ends without a word. With no stream adapter attached the generator yields NeuronAI's native chunk objects, and `TextChunk` is the only kind this endpoint lets through. Everything else — tool calls with their arguments, tool results — is skipped on the server, which is Section 7.4's rule applied at the HTTP boundary.

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

The agent arrives as it does in a controller. The page mounts the component with its conversation — `<livewire:chat :conversation="$conversation" />` — Livewire resolves `SupportAgent` from the container for the action, and `send()` does what every endpoint in this chapter does before a turn: authorise, bind with `for()`, recover. Livewire protects the model's ID from tampering between requests, but the policy still runs on every `send()`: who may use a conversation can change while the page stays open.

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

**The adapter shapes, the encoder frames.** `setStreamAdapter()` makes `stream()` yield `ProtocolEvent` objects — `RUN_STARTED`, `TEXT_MESSAGE_CONTENT` and the rest — instead of native chunks. It takes a factory, called once per execution segment (Section 7.5); this request runs a single segment, so the closure hands back the instance the response takes its headers from. `SSEEncoder::encode()` turns each event into a `data:` line and forwards the generator's return value, so the final `AgentState` is still there — it is what `yield from` evaluates to — if you want it. The callback is itself a generator: Laravel echoes and flushes every frame it yields. The adapter knows nothing about bytes, which is what lets the same adapter feed a broadcast channel in Section 21.5.

**`getHeaders()` supplies the protocol headers — including `X-Accel-Buffering: no`.** The built-in adapters carry Section 21.2's nginx fix themselves, so there is nothing to merge in.

**Only the last user message goes to the agent.** An AG-UI client posts the whole conversation on every turn. The agent already has that conversation in its durable chat history, keyed by the thread — feed it the client's copy and every earlier message is stored twice. The client's `messages` go to the adapter instead, which uses them to keep the protocol's message snapshot complete. They go whole, from `$request->input('messages')`. `validate()` returns only the keys its rules name, and an adapter seeded with that subset has lost every `toolCallId` and `toolCalls`: it throws `InputTranslationException` for any conversation that contains a tool message, and a continuation that delivers a tool result can never work.

**The thread is the agent's identity — authorise it.** AG-UI's `threadId` becomes the agent's thread, and the thread *is* the agent's workflow ID: the key its history and any suspended run are filed under. That makes it exactly the value Section 18.2 said never to take from user input. Three steps turn a client-supplied string into a thread this user may use: `ThreadScope` (Section 18.3) reads the conversation out of the name, the policy decides whether this user may use that conversation, and the name the server derives from the record must be the one the client sent. Only then is anything read or written under it. Echo `runId` back too: it is the client's per-request identifier, and without it the client cannot correlate the stream with the run it asked for.

**The request shape decides new turn versus continuation.** A trailing user message is a new turn, and goes to `stream()`. A `resume` array — the client answering interrupts — or a trailing tool message is a continuation of a paused run, and goes to `submitInputs()` with the protocol's translator, which validates it against the persisted request before anything executes and throws `InputTranslationException` for anything that does not match. The continuation test comes first, as in Section 7.5: after an approval pause the client's list still ends with the user's question. Note that the continuation calls `events()`, not `stream()`: `stream()` always starts a new turn. An invalid continuation must be an error response, never a fallback to a new turn.

**Until the first frame, a failure is a status code.** Two things happen before the response is returned. `recoverFailedTurn()` finishes a failed turn (Section 18.4) on a copy of its own — bound to the thread, with no adapter — so the recovered answer lands in the history and not in this stream. And `$events->valid()` pulls the first event. `stream()` and `events()` are lazy: the run is admitted only when the generator is first pulled, and left to the callback that happens after the `200` has gone out, so a thread that cannot take the turn — an approval still pending, another tab streaming — reaches the browser as a `RUN_ERROR` frame under a successful status. Pulled in the controller, the refusal is still an exception Laravel can turn into a status. The adapter is built there for the same reason: its constructor validates the messages it is seeded with. From that point on `SSEEncoder::encode()` is the only thing that iterates the generator, and a failure once frames are flowing is already on the wire as `RUN_ERROR` when it reaches the `catch`: `$adapter->error()` then yields nothing, and closes the protocol only if no frame had been sent. The statuses are mapped once for the whole application, in `bootstrap/app.php`:

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

**Swap the adapter, keep everything else.** `VercelAIAdapter` in place of `AGUIAdapter` and the same agent serves a different frontend protocol — with `VercelAIInputTranslator` for its continuations. Section 2.2's interface argument, applied on the output side.

### When the run pauses

If a tool in the turn needs approval (Chapter 22), the stream does not end like a completed one. The adapter's `interrupt()` terminal replaces `end()`: on AG-UI, `RUN_FINISHED` carries `outcome: {type: "interrupt", interrupts: [...]}`, one `confirmation` interrupt per pending tool call, with the tool call ID as its `id`; on Vercel, a `tool-approval-request` part per call.

A frontend that treats every `RUN_FINISHED` as "the answer is complete" will render a paused run as a finished one. Check `outcome.type` before you close the turn. The client answers with a `resume` array in its next request, which the endpoint above routes to `submitInputs()`. Section 22.5 covers the approval side for clients that do not speak AG-UI.

### What the adapter covers, and what it does not

From Section 7.5, because a team choosing a frontend needs to know before they commit:

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

An SPA sends a token; Sanctum or Passport handles it as usual. The important part is what the *agent* is told about the user who has just been authenticated: nothing. The container builds the same context-free `SupportAgent` for every request (Section 18.1), the endpoint authorises the thread, and `for()` binds a copy to it. What the agent does for this user then follows from the thread alone:

```php
class SupportAgent extends Agent
{
    // constructor, provider(), messageStore(), persistence() as in Chapter 18

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

Tool visibility, chat history and RAG filters all follow from that one input. No factory, and no `auth()` inside the agent: the same class runs unchanged on Section 21.5's queue worker, where there is no user to ask. Section 18.3's argument, and the reason the controller stays this short.

### Key takeaways

- `setStreamAdapter()` takes a factory and makes `stream()` yield `ProtocolEvent`s; `SSEEncoder::encode()` frames them; `getHeaders()` already includes `X-Accel-Buffering`.
- Send the agent only the last user message; the client's history seeds the adapter — whole, from `input()`, not from `validate()`.
- A `resume` array or trailing tool message is a continuation: `submitInputs()` with the protocol translator, then `events()`.
- The AG-UI `threadId` becomes the agent's workflow ID — authorise it against the conversation it names, never trust it raw.
- Recover a failed turn and prime the generator before returning the response: until the first frame, a refusal can still be a 400 or a 409.
- A run paused for approval ends with an interrupt outcome, not a plain finish; check before closing the turn.
- Nodes yield portable progress events; `mapEvent()` translates or suppresses your own.

## 21.5 Streaming from a Queue

This is the section where Parts IV and V meet.

### The problem

Section 16.4 established that long runs belong on a queue. But a queue worker has no HTTP connection to the user — so how does progress reach the browser?

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

            return;   // Chapter 22 records and routes the approval
        }

        $this->run->update([
            'status' => 'completed',
            'result' => $state->get('final'),
        ]);
    }
}
```

### Five things this job does differently from a web request

**`run()`, not a loop.** With both an adapter and a channel attached, the workflow consumes its own stream and delivers every event through the channel as it happens. `run()` returns the final state when the segment completes or pauses. There is no generator to iterate and nothing to echo. Both setters take a factory, because an adapter and a channel hold the state of one segment's stream: the segment that pauses for an approval and the one that continues after it each build their own. An agent on a worker needs one thing more: its turn has to be a streamed one — `chat($message, stream: true)`, Section 7.5's eager form — because a plain `chat()` makes a buffered model call, and no text ever reaches the channel.

**The adapter still decides the shape.** A channel carries protocol events, never native objects, so it needs an adapter. `AgentChunkAdapter` is NeuronAI's own vocabulary for a consumer that speaks no UI protocol: each chunk or progress event becomes one event named after its kind — `text`, `tool-call`, `activity`, `step-started` — with the chunk's own fields as payload. If the browser runs an AG-UI or Vercel client, attach that adapter instead; the channel does not care.

**The channel reports the lifecycle.** After the adapter's terminal frames, the channel sends `stream.completed`, `stream.interrupted` or `stream.failed`, carrying only the workflow ID — no state, no exception details. There is no need for your own `WorkflowCompleted` or `WorkflowPaused` broadcast events: the browser learns the outcome from the stream and fetches the result from your application, which is the authoritative record.

**The pause is a return value.** An interrupted run returns normally with `isInterrupted()` true — nothing to catch. Chapter 22 takes it from there.

**A redelivery finishes the same run.** Retrying a job this expensive sounds like paying twice. It is not, because of Section 13.5: every completed node is a committed step. The run ID was minted with the record, so every delivery of this job names the same run, and `recoverFailed: true` tells a start that finds that run failed — or still marked as running by a worker that was killed, once its lease has expired — to continue it instead of beginning again. Committed steps are replayed from the store, not executed: the research and the draft the first delivery paid for are not bought twice, and only the node that was running when it died runs again. A plain `run()` also recovers a failed run, but it replaces one whose worker was killed, and starts over from the first node. While the dead delivery's lease is still fresh the start is refused with `RunInFlightException`, and the job releases itself until the lease has expired.

Three clocks make that safe. The lease — `setLeaseTimeout(600)`: a plain workflow has no lease until you set one, an agent defaults to the same ten minutes — must outlast the longest single node, so that a slow run is never taken for a dead one. The job's `$timeout` must outlast the longest run. And the queue connection's `retry_after` must exceed `$timeout`: `DB_QUEUE_RETRY_AFTER=360` for a `$timeout` of 300, `REDIS_QUEUE_RETRY_AFTER` on a Redis queue. Laravel ships 90, which hands a job that is still running to a second worker. What the store cannot do is remember a run that completed — its records are deleted — so a job delivered again after it succeeded starts a new run; the clocks are what keep that from happening.

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

Two defaults of `PusherChannel` are worth knowing before the first run. It sends events in batches of ten, and a partial batch waits until it fills or the segment ends, so a handful of progress events would all arrive at the finish: `batchSize: 1` in the job is what makes each one leave as it is produced. And a channel name admits letters, digits and `-_=@,.;` only. A workflow ID that becomes part of one cannot contain a colon, so Section 18.3's `t1:refund:42` style needs another separator here — `t1.content.42`.

Prefer Redis? A factory returning `new RedisChannel($redis, "workflows:{$id}")` publishes the same envelopes on Redis Pub/Sub for a process that holds the browser's connection. Prefer Laravel's own broadcasting? `CallbackChannel` wraps a closure per lifecycle method, so `onSend` can call `Broadcast::private(...)->as($event->type)->with($event->data)->sendNow()`. **`sendNow()`, never a queued broadcast.** A queued broadcast lines your progress updates up behind the job producing them — on a single worker, a deadlock in slow motion — and with several workers it delivers them out of order.

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

Without this, anyone who guesses a workflow ID watches someone else's agent work. Section 18.3's four leak points have a fifth relative: the broadcast channel. For content that must stay confidential even from the broadcast provider, use a `private-encrypted-*` channel with the SDK's encryption master key; the browser needs `pusher-js/with-encryption`, and the package's consumer is unchanged.

### What this composes

This single job is most of the book converging:

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

## 21.6 Disconnection and Orphaned Cost

### The problem nobody mentions

A user starts a 30-second agent run. At second four they close the tab.

What happens next depends on where the run lives. On a queue worker nothing happens at all: the browser is gone and **the agent keeps running.** Every remaining model call is billed. In a multi-agent workflow that is a substantial amount of money spent on output nobody will ever read. In a streamed response the opposite happens: the run is cut off in mid-turn, and what it had already written decides whether the user's next message gets an answer.

At low volume both are invisible. At scale the first is a line item and the second is a support ticket.

### What a disconnect does to a streamed response

With PHP's default `ignore_user_abort=0`, your loop never learns that the client has gone. PHP learns it, on the first write after the disconnect, and terminates the script there and then. No line after that `echo` runs: a `connection_aborted()` check at the top of the loop is never reached, the `done` event is never sent, the code after the `foreach` never executes.

The engine does notice. A run whose consumer stops pulling before it has settled is recorded as **failed**, at once, as the request shuts down and the generator is destroyed. It does not stay marked as running until the agent's ten-minute lease expires, so the thread is not locked against the next message.

What is lost is the answer. If it is worth having whether or not anyone is watching, say so in Section 21.1's controller, before the response is returned:

```php
// The run now completes into the history even if the tab closes.
\ignore_user_abort(true);

return response()->stream(function () use ($stream) {
    foreach ($stream as $chunk) {
        if (! $chunk instanceof TextChunk || \connection_aborted()) {
            continue;   // nobody is reading: keep pulling, stop writing
        }

        // ... frame, echo and flush as in Section 21.1
    }

    // ... the done event
}, 200, [/* ... the same four headers */]);
```

Only now does `connection_aborted()` mean anything: the script survives the failed write, and the function reports it from the next iteration on. The loop keeps pulling, so the turn finishes and the user finds the complete answer when they come back. Replace `continue` with `break` and you are back to the default behaviour, by choice: the engine fails the run when the request ends and the generator is released.

The other way to keep the answer is not to tie the run to the request at all: Section 21.5's queued run, which no browser can interrupt.

**One honest caveat:** whichever you choose, the tokens generated before the disconnect are billed. Ending the run limits the damage; it does not undo it.

### Why the next message can fail

The failed run itself is harmless: the next turn on the thread replaces it. What matters is what the failed turn had already stored.

If the client left before the first answer began, nothing was stored, and the next message is simply answered. If it left after a tool step, the user's question is already in the history. A second user message straight after it is not a valid conversation, so the next `chat()` or `stream()` throws `ChatHistoryException: Invalid message sequence` — and by then it has replaced the failed run, the one thing that could have been recovered.

So finish the failed turn first. That is `recoverFailedTurn()`, from Section 18.4: `inspect()` the thread's run, and if its status is `Failed`, continue it with `run(ExecutionRequest::resume(expectedRunId: ..., expectedExecutionAttempt: ...))`. The run completes from its committed steps — a tool that already ran is not run again — its answer lands in the history, and the new question then follows a valid conversation. It is why every endpoint in this chapter calls it before starting a turn. It is not free: it finishes every failed turn, the one that had stored nothing included, so each abandoned question costs a model call for an answer the user did not wait for. That is the price of a thread that stays usable.

The companion's `disconnect.php` runs the three cases side by side: a client that leaves before anything is stored, and the next message is answered; one that leaves after a tool step, and the next message is refused with the `ChatHistoryException`; and the same again with the failed turn finished first — the next message is answered, and the tool has run once in total.

One case `recoverFailedTurn()` cannot see: a process killed outright — out of memory, FPM's `request_terminate_timeout` — runs no destructor and records nothing. Its run stays `running`, and new turns on the thread are refused with `RunInFlightException` until the lease expires. If the question had been stored, the turn after that fails as above, and Section 18.4's `resetConversation()` is what is left.

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

- A closed tab does not stop a queued run — you keep paying — and it cuts a streamed one off in mid-turn.
- With the default `ignore_user_abort=0` PHP ends the script on the next write; the engine fails the run at once, and the thread is not left locked.
- `ignore_user_abort(true)`, or a queued run, keeps the answer.
- A failed turn that had stored its question blocks the next one: `recoverFailedTurn()` before every turn.
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
5. **Disconnection handling.** `recoverFailedTurn()` before every turn, and a choice you can defend between letting a closed tab end the run and keeping it with `ignore_user_abort(true)`.

### Acceptance criteria

- First visible token arrives in well under a second on a local model. Measure it; do not assume.
- Asking a question that triggers a tool shows the friendly label, then the answer.
- Adding a new tool without adding its label shows "Working on it", not the tool's internal name. Test this deliberately.
- Closing the tab mid-response leaves a failed run, not a locked thread — and a new message on the same conversation, sent straight afterwards, is answered rather than refused. Test it once more with a question that triggers a tool, closing the tab after the tool has run.
- `curl -N` streams through the full stack, not just locally.

### The part people skip

Requirement four. It is tempting to declare victory when it works on `artisan serve`, where there is no nginx and no proxy. The first deploy is where streaming breaks, and Section 21.2's bisection is the difference between five minutes and an afternoon.

Run the three `curl -N` commands against your actual staging environment before you call this lab done.

### Going further

Add a "stop" button. Aborting the request from the browser side is the easy version, and Section 21.6 says what it costs: the run fails and the partial answer is lost. The better one keeps the connection open: wrap the provider's HTTP client in `NeuronAI\HttpClient\StoppableHttpClient` with a closure that reads a cache flag, raise the flag from a stop endpoint, and the streamed answer ends at its next event with the text so far kept in the history. Then measure what it saved: run the same prompt to completion, note the token count, and compare with a stopped run. That number is the argument for building the button.
