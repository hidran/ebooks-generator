# Chapter 7 — Streaming

::: {.callout .callout-tip}
[Code for this chapter]{.callout-title}

The runnable version of every listing below is at [`chapters/Ch07`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch07), in the companion repository. Clone it, run `composer install`, and the examples work against a local Ollama with no API key.
:::

## 7.1 Why Streaming Matters

### The number from Section 1.4

A model call takes 1–4 seconds. A five-iteration agent run with tool execution reaches 10–20 seconds of wall clock. Nobody waits 20 seconds at a blank screen.

### What streaming actually changes

**It does not make anything faster.** The total time is identical. Every token, every tool call, every round trip takes exactly as long.

**It changes when the user sees the first token.** Instead of 12 seconds of nothing followed by a complete answer, they see text appearing after 800 milliseconds and continuing.

Perceived wait is dominated by time-to-first-token, not time-to-completion. A response that streams for 15 seconds feels faster than one that blocks for 8. This is well-established in interface design generally, and it is unusually pronounced with text because the user can start reading while the rest arrives.

### The second benefit, which is underrated

Streaming lets you show **what the agent is doing**, not just what it eventually said.

NeuronAI's chunk types include tool calls and tool results. So you can render:

```
Let me check that for you.
  → Looking up order #4471...
  → Found it. Checking refund eligibility...
The order is eligible for a full refund.
```

That is a completely different product from a spinner. The user sees progress, understands why it is taking time, and — importantly — can tell that the system is working on the right problem before it finishes. Section 7.4 builds this.

### When not to stream

- **Batch and background jobs.** Nobody is watching.
- **Structured output.** You need the complete validated object; a half-parsed one is useless.
- **Very short responses.** Streaming a two-word answer adds complexity for nothing.
- **When you need to post-process the whole answer** before displaying it — filtering, redaction, formatting.

### Key takeaways

- Streaming changes perceived latency, not actual latency.
- Time-to-first-token is what users feel.
- Streaming tool activity is a product feature, not just a progress indicator.
- Not for batch work, structured output, or answers you must post-process.

## 7.2 stream() and Its Chunks

### The API

```php
use App\Neuron\MyAgent;
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\UserMessage;

$stream = MyAgent::make()->stream(new UserMessage('How are you?'));

foreach ($stream as $chunk) {
    if ($chunk instanceof TextChunk) {
        echo $chunk->content;
    }
}

// I'm fine, thank you! How can I assist you today?
```

Three things to notice, and each is a place people go wrong:

**1. `stream()` instead of `chat()`, but the same node.** Both verbs run the same `ChatNode`. `stream()` records a flag on the run that tells the node to call the provider's streaming endpoint instead of the buffered one, and to yield every piece as it arrives. Streaming is a transport choice, not a different execution path — which is why a middleware attached to `ChatNode` covers both, and why everything Chapter 5 said about tools still holds mid-stream.

**2. `stream()` returns the generator.** There is no second call: you iterate what comes back. Its declared return type is `Generator|AgentState`, and the `AgentState` branch only happens when you attach *both* a stream adapter and a channel (Section 7.5), in which case the agent streams eagerly to the channel and hands you the finished state. In the plain case it is always a generator. Static analysis sees the union, so the companion scripts narrow it once with `\assert($stream instanceof Generator)`.

**3. It yields objects, not strings — and not only text.** Filter with `instanceof`. Echoing `$chunk->content` for every item works right up to the first item that is not a text chunk: a tool call, a fragment of tool arguments, or the `InterruptEvent` that marks a paused run. None of those has a `content` property.

::: {.callout .callout-warning}
[Older streaming code]{.callout-title}

Two earlier shapes of this API survive in tutorials and sample repositories:

```php
// v2: plain strings - wrong since v3
foreach (AssistantAgent::make()->stream(new UserMessage($prompt)) as $chunk) {
    echo $chunk;
}

// v3: a handler, then events() - wrong in v4
foreach (AssistantAgent::make()->stream(new UserMessage($prompt))->events() as $chunk) {
    echo $chunk->content;
}
```

The v2 form is the more treacherous of the two, because in v4 its outer shape is right again — you do iterate `stream()` directly — so the broken line looks almost correct. What is wrong is the inside of the loop: every item is an object, and only some of them carry text.
:::

### The chunk types

All under `NeuronAI\Chat\Messages\Stream\Chunks`, all extending `StreamChunk`, all with a `toArray()`:

| Chunk | Contains |
|---|---|
| `TextChunk` | A piece of the response text, in `content` |
| `ReasoningChunk` | Part of the model's reasoning summary — reasoning models only |
| `ToolArgumentChunk` | A fragment of the arguments of a tool call the model is still writing |
| `ToolCallChunk` | A tool call the model decided to make |
| `ToolResultChunk` | The result of that call, once executed |
| `ImageChunk`, `AudioChunk` | Generated media, from models that produce it |

**What you receive depends on your agent and your provider.** No tools attached means no tool chunks — you can iterate expecting only text and reasoning. `ToolArgumentChunk` appears only with providers that stream arguments incrementally; Gemini and Ollama deliver them in one piece and never emit it. That is worth knowing before you write branching logic you do not need.

Besides chunks, the generator can carry two other kinds of object: the `InterruptEvent` that marks a run paused for approval (Chapter 15), and the progress events a workflow node chooses to yield (Chapter 14). A loop that handles the chunk types it cares about and ignores everything else is correct by construction, and stays correct when you add tools next month.

### Getting the final message

When the loop ends, the generator's return value is the finished run:

```php
$stream = MyAgent::make()->stream(...);

foreach ($stream as $chunk) {
    // stream to the user
}

$state = $stream->getReturn();
echo $state->getMessage()?->getContent();
```

`getReturn()` is plain PHP — every generator has one, available once it has finished — and here it returns the same `AgentState` that `chat()` would have returned. `getMessage()` is nullable because a run that paused before any inference completed has no assistant message yet; after an ordinary stream it is the complete reply.

This matters more than it looks. You stream to the user *and* get the complete `AssistantMessage` to persist, log, or run through a moderation check. You do not have to reassemble it from chunks yourself, which is exactly the tedious, error-prone thing everyone does on their first streaming implementation.

### Why chunk objects rather than strings

The framework's upgrade notes explain the reasoning, and it is a good design lesson.

Streaming raw message instances coupled the application to NeuronAI's internal message system. Dedicated chunk classes create a boundary: your UI code depends on a small, stable set of chunk types rather than on internal message plumbing. That separation is what made the stream adapter system possible (Section 7.5), and it means the internals can evolve without breaking your frontend.

It is a textbook case of introducing a DTO at a layer boundary.

### Key takeaways

- `stream()` returns the generator directly; iterate it.
- It yields objects of several kinds — filter with `instanceof TextChunk` before touching `content`.
- Which chunks you get depends on whether the agent has tools and how the provider streams.
- `getReturn()` gives you the final `AgentState`, with the complete assembled message.

## 7.3 Streaming from the CLI

### The example

**`examples/06-streaming.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\AssistantAgent;
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\UserMessage;

$prompt = $argv[1] ?? 'Explain the Repository pattern and when using it is a mistake.';

$start = \microtime(true);
$first = null;

$stream = AssistantAgent::make()->stream(new UserMessage($prompt));

// No adapter and no channel attached, so stream() returned a Generator.
\assert($stream instanceof Generator);

foreach ($stream as $chunk) {
    if (!$chunk instanceof TextChunk) {
        continue;
    }

    $first ??= \microtime(true);

    echo $chunk->content;
    \flush();
}

$end = \microtime(true);

\printf(
    "\n\n[first token: %.2fs | total: %.2fs]\n",
    ($first ?? $end) - $start,
    $end - $start,
);
```

```bash
php examples/06-streaming.php
```

Note where the clock stops: at the first `TextChunk`, not at the first item. A reasoning model may spend seconds yielding reasoning chunks before a word of the answer appears, and it is the answer the user is waiting for.

### The comparison worth measuring

Run the same prompt twice — once with `chat()`, once with `stream()` — and compare the timings.

Total time: roughly identical. Time to first visible output: 4.1 seconds versus 0.7. *The work took the same time; the wait did not.*

Measuring time-to-first-token in the script is worth the four extra lines. It turns an assertion into a number on your own hardware, with your own provider.

### The buffering problem

`flush()` is in there for a reason, and the reason gets much larger in Chapter 21.

PHP buffers output. So does the web server. So does the reverse proxy. Any one of them can hold your carefully streamed tokens and release them in a single block at the end — at which point you have all the complexity of streaming and none of the benefit.

From the CLI, `flush()` is usually enough. In a web context you also need to deal with:

- PHP's `output_buffering` setting
- `ob_end_flush()` if a buffer is already open
- nginx's `proxy_buffering` and `fastcgi_buffering`
- Any CDN or proxy in front of the application

The framework's own AG-UI documentation includes the warning: send the protocol headers and flush after each line, or the stream can get stuck in PHP output buffers or proxies.

It is mentioned here and solved properly in Chapter 21. People who meet it for the first time in production lose a day to it.

### Note on parallel tool calls

Section 5.13 established that `pcntl` is CLI-only. Streaming is one of the few contexts where you have both available at once — a CLI agent can stream *and* run tools in parallel. Worth knowing, because it makes the CLI agent of Capstone A a genuinely capable target rather than a toy.

### Key takeaways

- `flush()` after each chunk.
- Measure time-to-first-token; it is the number that justifies the feature.
- Buffering exists at four layers in a web stack — Chapter 21.

## 7.4 Streaming with Tools

### Tools work inside the stream

Nothing special is required. The agent handles tool calls in the middle of the stream and continues to the final response. You just receive extra chunk types.

### The full pattern

```php
use App\Neuron\MyAgent;
use App\Neuron\Tools\ServerConfigurationTool;
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\Stream\Chunks\ToolCallChunk;
use NeuronAI\Chat\Messages\Stream\Chunks\ToolResultChunk;
use NeuronAI\Chat\Messages\UserMessage;

$stream = MyAgent::make()
    ->addTool(new ServerConfigurationTool())
    ->stream(
        new UserMessage("What's the IP address of the server?")
    );

foreach ($stream as $chunk) {
    if ($chunk instanceof ToolCallChunk) {
        echo "\n- Calling tool: " . $chunk->tool->getName();
        echo "\n- Input: " . json_encode($chunk->tool->getInputs()) . "\n";
        continue;
    }

    if ($chunk instanceof ToolResultChunk) {
        echo "- Tool " . $chunk->tool->getName() . " completed";
        echo "\n- Result: " . $chunk->tool->getResult() . "\n";
        continue;
    }

    if ($chunk instanceof TextChunk) {
        echo $chunk->content;
    }
}
```

`ServerConfigurationTool` is an ordinary `Tool` subclass in the Chapter 5 shape: a `$name` of `get_server_configuration`, a description, and an `__invoke()` that returns the configuration. The companion version answers with a fixed value, so the example needs no network.

Output:

```
- Calling tool: get_server_configuration
- Input: []
- Tool get_server_configuration completed
- Result: {"hostname":"app-01","ip":"192.168.0.10","gateway":"192.168.0.1"}
The IP address of the server is 192.168.0.10.
```

### What the chunks carry

Both tool chunks hold a `ToolCall` in `$chunk->tool` — the record of one invocation, not the executable tool you registered. It is plain data:

- `$chunk->tool->getName()`
- `$chunk->tool->getInputs()` — the arguments the model chose
- `$chunk->tool->getCallId()` — the identifier that pairs a call with its result
- `$chunk->tool->getResult()` — on the result chunk

Having the arguments available is what makes a genuinely informative progress display possible. Not "working…" but "Searching orders for customer 4471". The call ID is what lets a UI turn the "calling" line into a "done" line in place, rather than printing two unrelated rows — and when the model calls the same tool twice in one turn, it is the only thing that tells the two apart.

If your provider streams tool arguments, `ToolArgumentChunk`s arrive before the `ToolCallChunk`, each carrying a `delta` of raw, partial JSON. They exist for a live "the agent is typing a query" preview. Never parse them; wait for the `ToolCallChunk`, which carries the complete inputs.

### The security point, stated firmly

**Do not pipe raw tool inputs and results to end users.**

The CLI example above is a debugging view, and it is perfect for that. In a user-facing product it leaks:

- Internal identifiers and database keys
- SQL queries, revealing your schema
- API endpoints and parameter names
- Anything in an error message

Map to human-readable labels instead:

```php
$labels = [
    'get_order_status'  => 'Looking up your order',
    'search_orders'     => 'Searching your order history',
    'get_refund_policy' => 'Checking the refund policy',
];

foreach ($stream as $chunk) {
    if ($chunk instanceof ToolCallChunk) {
        $name = $chunk->tool->getName();
        echo "\n" . ($labels[$name] ?? 'Working on it') . "...\n";
        continue;
    }

    if ($chunk instanceof ToolResultChunk) {
        continue; // never shown to the user
    }

    if ($chunk instanceof TextChunk) {
        echo $chunk->content;
    }
}
```

The allowlist matters: `$labels[$name] ?? 'Working on it'` means a newly added tool degrades to a generic message rather than leaking its internal name. Same reasoning as `only()` over `exclude()` in Section 5.8 — allowlists fail safe. So does the last branch: anything the loop does not recognise is dropped, not printed.

### The UX principle

A progress line for a tool that takes 200 ms is visual noise. A progress line for one that takes four seconds is essential.

Consider showing tool activity only after a short delay, so fast calls stay invisible and slow ones explain themselves. That is the behaviour of every well-designed loading state, and it applies here directly.

### Key takeaways

- Tools stream automatically; you get `ToolCallChunk` and `ToolResultChunk`, and possibly `ToolArgumentChunk` deltas first.
- The chunks carry a `ToolCall` record: name, arguments, call ID and result.
- Never show raw tool inputs or results to end users — map to labels with a safe fallback.
- Show progress for slow tools only.

## 7.5 Stream Adapters and UI Protocols

### The problem adapters solve

Your agent produces NeuronAI chunks. Your frontend speaks a protocol — Vercel AI SDK's data stream format, or AG-UI. Without adapters you hand-write the translation, including message lifecycle events, event formatting and ID tracking, and you rewrite it whenever the protocol moves.

### The design

An adapter translates NeuronAI's native stream objects into a frontend protocol. You attach it to the agent with `setStreamAdapter()`, and from then on the same `stream()` call yields **protocol events** instead of chunks:

```php
use NeuronAI\Agent\Adapters\AGUIAdapter;
use NeuronAI\Chat\Messages\UserMessage;

$stream = MyAgent::make()
    ->setStreamAdapter(new AGUIAdapter(threadId: 'thread_123'))
    ->stream(new UserMessage('What is the square root of 144?'));

foreach ($stream as $event) {
    echo json_encode($event) . "\n";
}

// {"type":"RUN_STARTED","runId":"run_...","threadId":"thread_123"}
// {"type":"TEXT_MESSAGE_START","messageId":"msg_...","role":"assistant"}
// {"type":"TEXT_MESSAGE_CONTENT","messageId":"msg_...","delta":"The square root"}
// ...
```

Same for Vercel:

```php
use NeuronAI\Agent\Adapters\VercelAIAdapter;

$agent->setStreamAdapter(new VercelAIAdapter());
```

Each item is a `NeuronAI\Workflow\Streaming\ProtocolEvent`: a `type` and a JSON-serialisable `data` array, one object per event on the wire. The built-in adapters live under `NeuronAI\Agent\Adapters`, because they encode agent concepts — tool calls, approvals — while the contract they implement belongs to the workflow layer, where any workflow can use it.

**Your agent code does not change.** The adapter sits at the boundary. This is the same interface-driven design as the provider swap in Section 3.6, applied to the output side — the architecture is consistent rather than incidental.

An adapter is stateful for one stream: it tracks open messages and tool calls. Create a fresh instance per request and never share one between concurrent streams.

### Protocol events, and where the bytes happen

Notice what the adapter does *not* do: it does not produce `data: ...` lines. The protocol decides the shape of each event; the transport decides how that event becomes bytes. For Server-Sent Events, the HTTP edge frames the stream with `SSEEncoder`:

```php
use NeuronAI\Workflow\Streaming\SSEEncoder;

$lines = SSEEncoder::encode($stream);

foreach ($lines as $line) {
    echo $line; // data: {"type":"TEXT_MESSAGE_CONTENT",...}\n\n
    flush();
}

$state = $lines->getReturn(); // the final AgentState, still reachable
```

`encode()` wraps the generator and forwards its return value, so the final state survives the framing. `SSEEncoder::frame($event)` frames a single event when you need that instead.

The split exists because SSE is only one destination. A websocket, a Redis stream or a broadcast channel wants the *event*, not a framed line, and keeping the two concerns apart is what lets the same adapter feed all of them — the channels at the end of this section depend on it.

### A complete AG-UI endpoint

```php
use NeuronAI\Agent\Adapters\AGUIAdapter;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Workflow\Streaming\SSEEncoder;

$input = json_decode(file_get_contents('php://input'), true);

$messages = $input['messages'];
$last = $messages === [] ? null : $messages[array_key_last($messages)];

if (($last['role'] ?? null) !== 'user') {
    http_response_code(400);
    exit('A new turn must end with a user message.');
}

$adapter = new AGUIAdapter(
    threadId: $input['threadId'],
    runId: $input['runId'] ?? null,
    messages: $messages,
    state: $input['state'] ?? [],
);

foreach ($adapter->getHeaders() as $name => $value) {
    header("{$name}: {$value}");
}

$stream = MyAgent::make(threadId: $input['threadId'])
    ->setStreamAdapter($adapter)
    ->stream(new UserMessage((string) $last['content']));

foreach (SSEEncoder::encode($stream) as $line) {
    echo $line;
    flush();
}
```

Five things to notice:

**AG-UI clients POST a `RunAgentInput` payload.** They do not simply open a connection. It carries `threadId`, `runId`, the message history, the tools the client can run, and shared state.

**The thread is the conversation, on both sides.** The adapter requires `threadId` and echoes it in `RUN_STARTED` and `RUN_FINISHED`; the agent receives the same value through `make(threadId:)`, and in v4 that thread *is* the agent run's identity — the key a later continuation uses to find a paused run. `runId` is the client's per-request identifier: pass it and the adapter echoes it back; omit it and the adapter invents one, which is fine for testing and wrong for a real client that expects to correlate the stream with the run it asked for.

**Only the last user message goes to the agent.** The client's copy of the history seeds the adapter's `messages` snapshot; it is not replayed into the model. The agent's own chat history for the thread is the record — which means this endpoint needs a persistent history (Chapter 4) to remember anything between requests. With the default in-memory history, every request is a fresh conversation.

**A request that does not end with a user message is not a new turn.** A trailing tool message or a `resume` array is the client *continuing* a paused run — delivering frontend tool results or an approval decision. That goes through `submitInputs()` with the protocol's input translator, not through `stream()`; Chapter 21 lays out the request shapes and Chapter 22 builds the endpoint that answers approvals. The 400 above is there so a continuation is never silently misread as a fresh question.

**`getHeaders()` gives you the SSE headers, and `flush()` goes after each line.** Section 7.3's warning, and the docs repeat it here for good reason.

In real code, remember that `json_decode()` returns `null` on a malformed body; validate the payload before trusting any of its keys.

### The event mapping

| NeuronAI output | AG-UI events |
|---|---|
| Run lifecycle | `RUN_STARTED`, `RUN_FINISHED` |
| `TextChunk` | `TEXT_MESSAGE_START`, `TEXT_MESSAGE_CONTENT`, `TEXT_MESSAGE_END` |
| `ReasoningChunk` | `REASONING_START`, `REASONING_MESSAGE_START`, `REASONING_MESSAGE_CONTENT`, `REASONING_MESSAGE_END`, `REASONING_END` |
| `ToolCallChunk` + `ToolResultChunk` | `TOOL_CALL_START`, `TOOL_CALL_ARGS`, `TOOL_CALL_END`, `TOOL_CALL_RESULT` |
| Workflow progress events | `STEP_STARTED`, `STEP_FINISHED`, `ACTIVITY_SNAPSHOT`, `CUSTOM` |
| Run paused for approval | `STATE_SNAPSHOT`, `MESSAGES_SNAPSHOT`, then `RUN_FINISHED` with an `interrupt` outcome |
| Run failed | `RUN_ERROR` |

One consequence of the tool row is easy to miss: the adapter buffers a server-side call and publishes all four `TOOL_CALL_*` events together, once the result exists. An AG-UI client learns about a tool when it has finished, not when it starts — so for a slow tool, the "Checking the refund policy…" line from Section 7.4 has to come from somewhere else, such as a progress event.

The other one is the paused run. A suspended stream does not end like a completed one: `RUN_FINISHED` carries `outcome: {type: "interrupt"}` with one `confirmation` interrupt per tool awaiting approval, keyed by the tool call ID. A client that treats every `RUN_FINISHED` as "the answer is complete" will get this wrong. Chapter 15 covers approval itself; Chapter 22 answers these interrupts over HTTP.

Errors reach the wire without their message. `RUN_ERROR` (and the Vercel `error` part) carry a neutral text, never `$exception->getMessage()`, so a stack detail cannot leak to a browser. Override the adapter's protected `errorMessage()` if your clients should know more.

### What the adapter covers, and the gap that remains

**Frontend-defined tools are supported.** The tools a client lists in `RunAgentInput` — executed in the browser, not on your server — can be attached to the agent as deferred tools. When the model calls one, the run suspends, the adapter publishes the call, the client executes it and sends the result back in its next request, and the run continues. That request is a continuation, not a new turn, and Chapter 21 shows how to tell the two apart.

**Shared state is echoed, not synchronised.** The adapter carries the `state` and `messages` the client sent and returns them as `STATE_SNAPSHOT` and `MESSAGES_SNAPSHOT` when a run pauses, so the client's picture stays complete. It never emits `STATE_DELTA`, and nothing in the agent writes into AG-UI state. If your frontend design depends on the agent mutating shared state live, that is the gap.

If you are evaluating CopilotKit or a similar AG-UI frontend, know that boundary before you commit to a design that depends on it.

### Custom adapters

```php
namespace NeuronAI\Workflow\Streaming\Adapter;

interface StreamAdapterInterface
{
    public function reset(): void;
    public function start(): iterable;
    public function transform(object $chunk): iterable;
    public function end(): iterable;
    public function interrupt(InterruptRequest $request): iterable;
    public function error(Throwable $error): iterable;
}
```

Every iterable yields `ProtocolEvent` objects. `transform()` does the work, one native object in, zero or more events out. `start()` opens the protocol. Exactly one terminal closes each segment, and the agent picks it from the outcome, never your code: `end()` on completion, `interrupt()` when the run pauses — so the client learns what it is waiting for — and `error()` on failure. `reset()` is called before every segment, so one instance can serve a paused run and its continuation in the same process. Return an empty iterable from any method your protocol has nothing to say in.

A small one, for a homegrown frontend that wants text and tool progress and nothing else:

```php
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\Stream\Chunks\ToolCallChunk;
use NeuronAI\Workflow\Interrupt\InterruptRequest;
use NeuronAI\Workflow\Streaming\Adapter\StreamAdapterInterface;
use NeuronAI\Workflow\Streaming\ProtocolEvent;

final class ProgressAdapter implements StreamAdapterInterface
{
    public function reset(): void
    {
    }

    public function start(): iterable
    {
        return [];
    }

    public function transform(object $chunk): iterable
    {
        if ($chunk instanceof TextChunk) {
            yield new ProtocolEvent('delta', ['text' => $chunk->content]);
        }

        if ($chunk instanceof ToolCallChunk) {
            yield new ProtocolEvent('progress', ['tool' => $chunk->tool->getName()]);
        }
    }

    public function end(): iterable
    {
        yield new ProtocolEvent('done');
    }

    public function interrupt(InterruptRequest $request): iterable
    {
        yield new ProtocolEvent('paused', ['request' => $request->jsonSerialize()]);
    }

    public function error(Throwable $error): iterable
    {
        yield new ProtocolEvent('error', ['message' => 'Something went wrong.']);
    }
}
```

The same allowlist instinct as Section 7.4, enforced at the protocol boundary: tool results never leave the server because the adapter has no branch for them. HTTP headers are not part of the interface; if your protocol needs some, declare a `getHeaders()` on the adapter yourself, as the built-in ones do.

Before writing your own, check whether `AgentChunkAdapter` already fits. It is NeuronAI's native vocabulary: one event per chunk, named after its kind (`text`, `reasoning`, `tool-call`, `tool-result`, …), with the chunk's `toArray()` as payload. When the consumer is your own frontend and speaks no standard protocol, it is usually all you need.

### The use case worth highlighting

Everything so far assumes the code iterating the generator is also the code talking to the browser — a controller holding the HTTP connection open. Often it is not.

A long agent run belongs on a queue worker (Section 1.4's latency arithmetic, Section 5.13's `pcntl` constraint), and a queue worker has no HTTP connection to the user. Its output would simply be thrown away. **Channels** solve exactly that. The adapter decides the shape of the output; a channel decides where it goes:

```php
use NeuronAI\Agent\Adapters\VercelAIAdapter;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Workflow\Streaming\Channel\PusherChannel;

// Inside a queued job: the HTTP request returned long ago.
$state = MyAgent::make(threadId: $threadId)
    ->setStreamAdapter(new VercelAIAdapter())
    ->setChannel(new PusherChannel(
        client: $pusher,
        channel: "private-chat.{$threadId}",
    ))
    ->stream(new UserMessage($message));
```

With an adapter *and* a channel attached, `stream()` consumes the pipeline itself, delivers each protocol event through the channel as it happens, and returns the final `AgentState` — the second branch of the return type from Section 7.2. No loop in your code at all.

The framework ships three channels under `NeuronAI\Workflow\Streaming\Channel`: `PusherChannel` (it takes a configured client from the optional `pusher/pusher-php-server` package, and works with Pusher-compatible servers such as Reverb and Soketi), `RedisChannel` for Redis Pub/Sub, and `CallbackChannel`, which wraps a closure for anything else — a Laravel broadcast, a log, a test. A channel needs an adapter to have anything to send; attach `AgentChunkAdapter` when the browser speaks no UI protocol.

Two properties to design around. A channel failure never fails the run: the agent carries on and reports the transport error as an event. And streamed output is ephemeral — nothing yielded is stored or replayed, so a browser that reconnects mid-run has missed what it missed. The chat history is the record the UI reconciles from; never make correctness depend on a client receiving a streamed item.

Chapter 21 builds this in Laravel.

### Key takeaways

- `setStreamAdapter()` turns the stream into `ProtocolEvent`s for AG-UI, Vercel AI SDK, or NeuronAI's own vocabulary; your agent code is unchanged.
- Adapters decide shape, not bytes: `SSEEncoder` frames events at the HTTP edge and keeps the final state reachable.
- AG-UI clients POST a payload — the thread is the agent's identity, echo `runId`, and send only the new user message.
- A paused run ends with an `interrupt` outcome, not a normal finish; frontend tools and approvals come back as continuations.
- A channel delivers the same events when nobody is holding the stream — the way a queue worker streams to a browser.

## Chapter Exercises

1. **Measure it.** Convert one agent from Chapter 5 from `chat()` to `stream()`. Measure time-to-first-token both ways and write down both numbers. If the gap is small, ask why — a fast local model on a short answer genuinely does not need streaming, and knowing that is as useful as the feature.

2. **Show the work.** Add tool progress display with a label allowlist and a safe fallback. Then add a new tool without adding its label, and confirm it degrades to the generic message rather than leaking its internal name.

3. **Choose an adapter.** Sketch which adapter you would use for your own frontend stack, and decide whether the AG-UI shared-state gap would affect you. Then decide who holds the stream: the HTTP request, or a queue worker with a channel. If you are not sure, that is the answer to find out before you build, not after.
