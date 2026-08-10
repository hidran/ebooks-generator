# Chapter 7 — Streaming

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

## 7.2 stream() and events()

### The API

```php
use App\Neuron\MyAgent;
use NeuronAI\Chat\Messages\UserMessage;

$handler = MyAgent::make()->stream(new UserMessage('How are you?'));

foreach ($handler->events() as $chunk) {
    echo $chunk->content;
}

// I'm fine, thank you! How can I assist you today?
```

Three steps, and each is a place people go wrong:

**1. `stream()` instead of `chat()`.** This prepares the agent's workflow to use `StreamingNode` rather than `ChatNode` — the third node swap in this book, after `ToolNode`/`ParallelToolNode` in Section 5.13 and `StructuredOutputNode` in Section 6.3.

**2. `stream()` returns a handler, not a generator.** You cannot iterate it directly.

**3. `events()` returns the generator.** And it yields **objects**, not strings. `$chunk->content`, not `$chunk`.

::: {.callout .callout-warning}
[v2 → v3 change]{.callout-title}

Earlier versions streamed plain strings for text and message instances for tool operations. v3 introduced dedicated chunk classes. Every older tutorial you find will show the string form:

```php
// WRONG for v3
foreach (AssistantAgent::make()->stream(new UserMessage($prompt)) as $chunk) {
    echo $chunk;
}
```

This is the third significant v2 → v3 break in the book, after the namespaces and `getMessage()`. It is also the most common one to survive into published sample code, because the broken form still *looks* correct.
:::

### The chunk types

Four classes:

| Chunk | Contains |
|---|---|
| `TextChunk` | A piece of the response text |
| `ReasoningChunk` | Part of the model's reasoning summary — reasoning models only |
| `ToolCallChunk` | The model requesting a tool execution |
| `ToolResultChunk` | The result of a tool execution |

**What you receive depends on your agent.** No tools attached means no `ToolCallChunk` or `ToolResultChunk` — you can iterate expecting only text and reasoning. That is worth knowing before you write branching logic you do not need.

### Getting the final message

After the stream completes, the handler still holds the assembled result:

```php
$handler = MyAgent::make()->stream(...);

foreach ($handler->events() as $chunk) {
    // stream to the user
}

$message = $handler->getMessage();
echo $message->getContent();
```

This matters more than it looks. You stream to the user *and* get the complete `AssistantMessage` to persist, log, or run through a moderation check. You do not have to reassemble it from chunks yourself, which is exactly the tedious, error-prone thing everyone does on their first streaming implementation.

### Why chunk objects rather than strings

The framework's upgrade notes explain the reasoning, and it is a good design lesson.

Streaming raw message instances coupled the application to NeuronAI's internal message system. Dedicated chunk classes create a boundary: your UI code depends on a small, stable set of chunk types rather than on internal message plumbing. That separation is what made the stream adapter system possible (Section 7.5), and it means the internals can evolve without breaking your frontend.

It is a textbook case of introducing a DTO at a layer boundary.

### Key takeaways

- `stream()` → handler → `events()` → generator of chunk objects.
- `$chunk->content`, not `$chunk`.
- Four chunk types; which you get depends on whether the agent has tools.
- `getMessage()` on the handler gives you the complete assembled message afterwards.

## 7.3 Streaming from the CLI

### The example

**`examples/06-streaming.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\AssistantAgent;
use NeuronAI\Chat\Messages\UserMessage;

$prompt = $argv[1] ?? 'Explain the Repository pattern and when using it is a mistake.';

$start   = \microtime(true);
$first   = null;

$handler = AssistantAgent::make()->stream(new UserMessage($prompt));

foreach ($handler->events() as $chunk) {
    $first ??= \microtime(true);

    echo $chunk->content;
    \flush();
}

$end = \microtime(true);

\printf(
    "\n\n[first token: %.2fs | total: %.2fs]\n",
    $first - $start,
    $end - $start
);
```

```bash
php examples/06-streaming.php
```

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
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Tools\Tool;

$handler = MyAgent::make()
    ->addTool(
        Tool::make(
            'get_server_configuration',
            'retrieve the server network configuration'
        )->addProperty(/* ... */)->setCallable(/* ... */)
    )
    ->stream(
        new UserMessage("What's the IP address of the server?")
    );

foreach ($handler->events() as $chunk) {
    if ($chunk instanceof ToolCallChunk) {
        echo "\n- Calling tool: " . $chunk->tool->getName();
        echo "\n- Input: " . json_encode($chunk->tool->getInputs());
        continue;
    }

    if ($chunk instanceof ToolResultChunk) {
        echo "\n- Tool " . $chunk->tool->getName() . " completed";
        echo "\n- Result: " . $chunk->tool->getResult();
        continue;
    }

    echo $chunk->content;
}
```

Output:

```
Let me retrieve the server configuration.
- Calling tool: get_server_configuration
- Tool get_server_configuration completed
The IP address of the server is: 192.168.0.10
```

### What the chunks carry

Both tool chunks hold the **tool instance**, which is more than a name:

- `$chunk->tool->getName()`
- `$chunk->tool->getInputs()` — the arguments the model chose
- `$chunk->tool->getResult()` — on the result chunk

Having the arguments available is what makes a genuinely informative progress display possible. Not "working…" but "Searching orders for customer 4471".

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

foreach ($handler->events() as $chunk) {
    if ($chunk instanceof ToolCallChunk) {
        $name = $chunk->tool->getName();
        echo "\n" . ($labels[$name] ?? 'Working on it') . "...\n";
        continue;
    }

    if ($chunk instanceof ToolResultChunk) {
        continue; // never shown to the user
    }

    echo $chunk->content;
}
```

The allowlist matters: `$labels[$name] ?? 'Working on it'` means a newly added tool degrades to a generic message rather than leaking its internal name. Same reasoning as `only()` over `exclude()` in Section 5.8 — allowlists fail safe.

### The UX principle

A progress line for a tool that takes 200 ms is visual noise. A progress line for one that takes four seconds is essential.

Consider showing tool activity only after a short delay, so fast calls stay invisible and slow ones explain themselves. That is the behaviour of every well-designed loading state, and it applies here directly.

### Key takeaways

- Tools stream automatically; you get `ToolCallChunk` and `ToolResultChunk`.
- Chunks carry the tool instance, including the arguments the model chose.
- Never show raw tool inputs or results to end users — map to labels with a safe fallback.
- Show progress for slow tools only.

## 7.5 Stream Adapters and UI Protocols

### The problem adapters solve

Your agent produces NeuronAI chunks. Your frontend speaks a protocol — Vercel AI SDK's data stream format, or AG-UI. Without adapters you hand-write the translation, including message lifecycle events, event formatting and ID tracking, and you rewrite it whenever the protocol moves.

### The design

Adapters are translators between NeuronAI's internal streaming events and a specific frontend protocol. Pass one to `events()`:

```php
use NeuronAI\Chat\Messages\Stream\Adapters\AGUIAdapter;

$handler = MyAgent::make()->stream(new UserMessage('What is the square root of 144?'));

$stream = $handler->events(new AGUIAdapter());

foreach ($stream as $line) {
    echo $line;
}
```

Same for Vercel:

```php
use NeuronAI\Chat\Messages\Stream\Adapters\VercelAIAdapter;

$stream = $handler->events(new VercelAIAdapter());
```

**Your agent code does not change.** The adapter sits at the boundary. This is the same interface-driven design as the provider swap in Section 3.6, applied to the output side — the architecture is consistent rather than incidental.

### A complete AG-UI endpoint

```php
use NeuronAI\Chat\Messages\Stream\Adapters\AGUIAdapter;
use NeuronAI\Chat\Messages\UserMessage;

$input = json_decode(file_get_contents('php://input'), true);

$messages = [];
foreach ($input['messages'] as $message) {
    if ($message['role'] === 'user') {
        $messages[] = new UserMessage($message['content']);
    }
}

$adapter = new AGUIAdapter(
    threadId: $input['threadId'],
    runId: $input['runId'],
);

foreach ($adapter->getHeaders() as $name => $value) {
    header("{$name}: {$value}");
}

$stream = MyAgent::make()->stream($messages)->events($adapter);

foreach ($stream as $line) {
    echo $line;
    flush();
}
```

Four things to notice:

**AG-UI clients POST a `RunAgentInput` payload.** They do not simply open a connection. It carries `threadId`, `runId`, the message history, and more.

**Echo the identifiers back.** Pass `threadId` and `runId` to the constructor so the adapter returns them in `RUN_STARTED` and `RUN_FINISHED`. Omit them and the adapter invents its own — fine for testing, wrong for a real client that expects to correlate the stream with the run it asked for.

**`getHeaders()` gives you the SSE headers.** Send them.

**`flush()` after each line.** Section 7.3's warning, and the docs repeat it here for good reason.

### The event mapping

| NeuronAI chunk | AG-UI events |
|---|---|
| Run lifecycle | `RUN_STARTED`, `RUN_FINISHED` |
| `TextChunk` | `TEXT_MESSAGE_START`, `TEXT_MESSAGE_CONTENT`, `TEXT_MESSAGE_END` |
| `ReasoningChunk` | `REASONING_START`, `REASONING_MESSAGE_START`, `REASONING_MESSAGE_CONTENT`, `REASONING_MESSAGE_END`, `REASONING_END` |
| `ToolCallChunk` | `TOOL_CALL_START`, `TOOL_CALL_ARGS`, `TOOL_CALL_END` |
| `ToolResultChunk` | `TOOL_CALL_RESULT` |

### Two limitations to state honestly

**Server-side tools only.** Tools attached to your agent run on your server, and the client is informed through the `TOOL_CALL_*` events. AG-UI's *frontend-defined* tools — listed in the `tools` field of `RunAgentInput` and executed by the client — are not handled by the adapter.

**No shared state events.** The adapter does not emit `STATE_SNAPSHOT`, `STATE_DELTA` or `MESSAGES_SNAPSHOT`, so AG-UI clients' state-synchronisation features are unavailable through it.

If you are evaluating CopilotKit or a similar AG-UI frontend, know these two gaps before you commit to a design that depends on them.

### Custom adapters

```php
interface StreamAdapterInterface
{
    public function transform(object $chunk): iterable;
    public function getHeaders(): array;
    public function start(): iterable;
    public function end(): iterable;
}
```

Four methods. `transform()` does the work; `start()` and `end()` handle protocol lifecycle; `getHeaders()` supplies transport headers.

You can also extend `SSEAdapter` when you only need to change the transformation.

### The use case worth highlighting

Adapters can push to an external transport such as Pusher. That means an agent running **in a background job** can stream its progress to a browser it has no direct connection to.

This is the answer to a problem that would otherwise seem intractable: long agent runs belong on a queue worker (Section 1.4's latency arithmetic, Section 5.13's `pcntl` constraint), but a queue worker has no HTTP connection to the user. An adapter pushing to a websocket transport bridges exactly that gap.

Chapter 21 builds this in Laravel.

### Key takeaways

- Adapters translate NeuronAI chunks into a frontend protocol; your agent code is unchanged.
- AG-UI clients POST a payload — echo `threadId` and `runId` back.
- Two gaps: no frontend-defined tools, no shared-state events.
- An adapter over a websocket transport lets a queue worker stream to a browser.

## Chapter Exercises

1. **Measure it.** Convert one agent from Chapter 5 from `chat()` to `stream()`. Measure time-to-first-token both ways and write down both numbers. If the gap is small, ask why — a fast local model on a short answer genuinely does not need streaming, and knowing that is as useful as the feature.

2. **Show the work.** Add tool progress display with a label allowlist and a safe fallback. Then add a new tool without adding its label, and confirm it degrades to the generic message rather than leaking its internal name.

3. **Choose an adapter.** Sketch which adapter you would use for your own frontend stack, and decide whether either AG-UI limitation would affect you. If you are not sure, that is the answer to find out before you build, not after.
