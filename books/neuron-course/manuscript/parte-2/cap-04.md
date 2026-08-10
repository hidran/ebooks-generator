# Chapter 4 — Messages and Memory

::: {.callout .callout-tip}
[Code for this chapter]{.callout-title}

This chapter is conceptual and has no standalone code, but the companion repository at [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) holds runnable versions of everything the book builds.
:::

## 4.1 The Message Model

NeuronAI has a unified message layer — roles, content blocks, metadata — and it is the piece that makes provider swapping actually work rather than merely appear to.

### Why a unified message layer exists

Every provider has its own request and response shape. OpenAI, Anthropic, Gemini and Ollama differ in how they represent roles, how they attach images, how they return tool calls, how they surface reasoning traces.

NeuronAI's answer is a single message abstraction that maps onto all of them. This is what makes Section 3.6 more than a party trick: the swap works because the message layer absorbs the differences. Without it, "change one line to change provider" would be false the moment you attached an image or read a tool call.

### What a message is

Three parts:

- **Role** — who is speaking: user, assistant, tool
- **Content blocks** — the actual payload
- **Metadata** — additional information from the provider response

### Content blocks

This is the part most people miss. A message does not hold a string. It holds an ordered **list of content blocks**, each implementing a `ContentBlock` interface. NeuronAI provides block types for text, reasoning, image, file, audio and video, and maps each one into the correct provider-specific format automatically.

Passing a string to the constructor simply creates the first text block:

```php
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Chat\Messages\ContentBlocks\TextContent;

// A string constructor argument becomes the first TextContent block
$message = new UserMessage('Hi');

$message->addContent(new TextContent('My name is John.'));
$message->addContent(new TextContent('Answer as a professional concierge.'));

echo $message->getContent();
// Hi My name is John. Answer as a professional concierge.

$blocks = $message->getTextBlocks();
```

Now `getContent()` makes sense: it concatenates all text blocks into one string. It is a convenience, not the underlying structure.

### Reading a response properly

```php
$response = MyAgent::make()->chat(new UserMessage('...'))->getMessage();

// Convenience: all text blocks joined
echo $response->getContent();
```

But with a reasoning model, the response carries more than text:

```php
use NeuronAI\Chat\Messages\ContentBlocks\ReasoningContent;
use NeuronAI\Chat\Messages\ContentBlocks\TextContent;

foreach ($response->getContentBlocks() as $block) {
    echo match ($block::class) {
        ReasoningContent::class => "Reasoning: {$block->content}\n\n",
        TextContent::class      => $block->content,
        default                 => '',
    };
}
```

NeuronAI captures the model's reasoning steps as a distinct block automatically. If you only ever call `getContent()`, you never see them. For debugging an agent that made a strange decision, the reasoning block is often the answer.

### Building a conversation by hand

Sometimes you already hold a conversation — from your own database, or an import — and need to seed the agent with it. Pass an array to `chat()`:

```php
use NeuronAI\Chat\Enums\MessageRole;
use NeuronAI\Chat\Messages\Message;

$message = MyAgent::make()
    ->chat([
        new Message(MessageRole::USER, 'Hi, my company is called Inspector.dev'),
        new Message(MessageRole::ASSISTANT, 'Great, how can I assist you today?'),
        new Message(MessageRole::USER, 'What is the name of the company I work for?'),
    ])
    ->getMessage();

echo $message->getContent();
// You work for Inspector.dev
```

The last message in the array is treated as the most recent. This is the escape hatch for any situation where NeuronAI's own history component is not where your conversation lives — a legacy schema, another system's export, a reconstructed session.

### Multimodal preview

Attaching a document uses the same mechanism — another content block:

```php
use NeuronAI\Chat\Messages\ContentBlocks\FileContent;
use NeuronAI\Chat\Enums\SourceType;

$message = new UserMessage('Summarize this document');

$message->addContent(
    new FileContent(
        content: base64_encode(file_get_contents(__DIR__ . '/invoice.pdf')),
        sourceType: SourceType::BASE64,
        mediaType: 'application/pdf',
    )
);
```

`SourceType` supports `BASE64`, `URL` and `ID`. That third one matters for cost: many providers let you upload a file once to their platform and then reference it by ID, which avoids re-uploading the payload on every iteration of the agent loop. Given the token arithmetic from Section 1.4, that is a substantial saving on any multi-step run involving a document. Chapter 8 covers this properly.

::: {.callout .callout-warning}
[v3 change]{.callout-title}

Earlier versions used `addAttachment(new Image($url, ...))`. v3 replaced it with the content-block system. Older tutorials show the old call. Related: the documentation is inconsistent about block class names — `TextBlock`/`FileBlock` appear in some places where the shipped classes are `TextContent`/`FileContent`, and one example imports `AudioContent` while instantiating `FileContent`. See items 10 and 11 in Appendix A.
:::

### Key takeaways

- A message is role + content blocks + metadata; not a string.
- `getContent()` concatenates text blocks; `getContentBlocks()` gives you everything, including reasoning.
- Pass an array of `Message` objects to seed an existing conversation.
- The unified message layer is why provider swapping survives contact with images, files and tool calls.

## 4.2 The Model Has No Memory

Statelessness is a design constraint, not a limitation to work around. This section is about internalising it, because almost every confusion about "memory" dissolves once you do.

### The demonstration

```php
use NeuronAI\Agent\Agent;
use NeuronAI\Chat\Messages\UserMessage;

$message = Agent::make()
    ->chat(new UserMessage("What's my name?"))
    ->getMessage();

echo $message->getContent();
// I'm sorry, I don't know your name.
```

Now hold on to the same instance:

```php
$agent = Agent::make();

$agent->chat(new UserMessage('Hi, my name is Valerio!'));

$message = $agent->chat(new UserMessage('Do you remember my name?'))->getMessage();
echo $message->getContent();
// Sure, your name is Valerio!
```

The obvious reading — "the agent learned my name" — is wrong, and correcting it is the point of this section.

### What actually happened

The second call sent this to the provider:

```
system:    <instructions>
user:      Hi, my name is Valerio!
assistant: Hi Valerio, nice to meet you...
user:      Do you remember my name?
```

The model did not remember. **Your process re-sent the transcript.** There is no session on the provider side, no user record, nothing persisted between requests. The model reads the whole conversation fresh, every time, and answers as if it remembers.

The NeuronAI component that keeps the transcript and re-sends it is `ChatHistory`. That is the entirety of what "memory" means at this layer.

### Four consequences worth stating

**1. Memory costs money on every turn.**
Turn twenty re-sends nineteen previous exchanges. This is the mechanism behind the cost table in Section 1.4, and it is why long conversations get expensive even when the individual messages are short.

**2. Memory is bounded by the context window.**
It is not a database that grows. It is a buffer with a hard ceiling. Something must be discarded eventually, and the only question is what and how — Section 4.4.

**3. Memory is entirely under your control.**
Which is liberating once you accept it. You can edit history, inject a summary, drop irrelevant turns, keep a system-level fact permanently pinned. Nothing is sacred; it is your array.

**4. Statelessness is why horizontal scaling is easy.**
Any web server can serve any request, as long as it can load the transcript. There is no session affinity to a provider. Load a `ChatHistory` from shared storage and any node can continue any conversation. This is a genuine architectural advantage, and it is unusual for a stateful-feeling feature to scale this cleanly.

### The mental model to keep

The model is a **pure function**: transcript in, next message out. Everything that feels like memory, personality persistence or learning is your code choosing what goes into the transcript.

Every technique in the rest of this book — history trimming, summarisation, RAG, long-term memory stores — is a different answer to one question: **what do we put in the transcript?**

### Key takeaways

- No server-side session; the transcript is re-sent every turn.
- Memory costs tokens on every turn and is capped by the context window.
- History is your array — editable, injectable, replaceable.
- The model is a pure function of the transcript.

## 4.3 ChatHistory Implementations

### The interface

```php
NeuronAI\Chat\History\ChatHistoryInterface
```

Register one by implementing `chatHistory()` on your agent. The default, if you implement nothing, is in-memory.

### InMemoryChatHistory

```php
use NeuronAI\Chat\History\ChatHistoryInterface;
use NeuronAI\Chat\History\InMemoryChatHistory;

protected function chatHistory(): ChatHistoryInterface
{
    return new InMemoryChatHistory(contextWindow: 150_000);
}
```

An array. Lives for the current PHP process only. Correct for: single-shot scripts, stateless API endpoints where you hold the conversation yourself, and tests.

Remember that in a normal web request PHP dies at the end of the response. In-memory history in a web context means **no memory between requests**, which is a genuinely common surprise for developers used to long-running runtimes.

### FileChatHistory

```php
use NeuronAI\Chat\History\FileChatHistory;

protected function chatHistory(): ChatHistoryInterface
{
    return new FileChatHistory(
        directory: '/home/app/storage/neuron',
        key: 'THREAD_ID',
        contextWindow: 150_000,
    );
}
```

`directory` is an absolute path; `key` identifies the conversation. Use a user ID for one conversation per user, or a thread ID for many.

Correct for: CLI tools, single-server apps, prototypes. Not correct for: multi-server deployments without shared storage, or high concurrency — two simultaneous writes to the same key will not end well.

### SQLChatHistory

Create the table first:

```sql
CREATE TABLE IF NOT EXISTS chat_history (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  thread_id VARCHAR(255) NOT NULL,
  messages LONGTEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  UNIQUE KEY uk_thread_id (thread_id),
  INDEX idx_thread_id (thread_id)
);
```

```php
use NeuronAI\Chat\History\SQLChatHistory;

protected function chatHistory(): ChatHistoryInterface
{
    return new SQLChatHistory(
        thread_id: 'THREAD_ID',
        pdo: new \PDO('mysql:host=localhost;dbname=DB;charset=utf8mb4', 'user', 'pass'),
        table: 'chat_history',
        contextWindow: 150_000,
    );
}
```

It takes a plain `PDO`, so it works in any PHP application regardless of framework. In Laravel you would pass `\DB::connection()->getPdo()`; in Symfony, `$connection->getNativeConnection()` from a Doctrine connection. You can add columns — a foreign key to your users table, for instance — as long as the base structure stays.

### EloquentChatHistory

Covered fully in Chapter 18, listed here so the map is complete:

```php
new EloquentChatHistory(
    threadId: 'THREAD_ID',
    modelClass: ChatMessage::class,
    contextWindow: 150_000,
);
```

### Choosing

| Backend | Use when | Avoid when |
|---|---|---|
| InMemory | Scripts, stateless endpoints, tests | You need persistence |
| File | CLI tools, single server, prototypes | Multi-server, high concurrency |
| SQL | Any framework, production, multi-server | You have no database |
| Eloquent | Laravel with relations and scopes | You are not on Laravel |

Lab 2, at the end of this chapter, builds a persistent CLI chat on `FileChatHistory`.

### Key takeaways

- Four backends: InMemory, File, SQL, Eloquent.
- In a web request, in-memory means no memory between requests.
- `SQLChatHistory` takes a plain PDO and works in any framework.

## 4.4 Context Window and Trimming

### The bug this prevents

The most common production failure in conversational AI:

> "It works fine, then after about thirty messages it starts throwing errors."

The transcript grew past the model's context limit. The provider rejects the request — it does not truncate for you, it returns an error.

NeuronAI's `ChatHistory` prevents this by trimming automatically. It tracks token usage from the provider responses and, when the transcript approaches the configured limit, removes messages from the beginning.

### The 5–10 % rule

From the documentation, and worth memorising because it is precise and easy to get wrong:

**Configure the context window 5–10 % below the model's actual limit.**

| Model limit | Configure |
|---|---|
| 32K | 29,000 |
| 128K | 118,000 |
| 200K | 185,000 |
| 1M | 920,000 |

### Why the margin is not superstition

The trimmer does not simply chop at the byte where the limit is hit. It looks for a cut point that minimises context loss — the documentation describes it as identifying a cut slightly less aggressive than the one first computed.

That means it needs room to manoeuvre. Configure at exactly the model's limit and the trimmer has nowhere to move its cut point to, and you can still overflow. The margin is what lets it choose a sensible boundary rather than a mechanical one.

### Where it goes

```php
protected function chatHistory(): ChatHistoryInterface
{
    return new InMemoryChatHistory(contextWindow: 185_000);
}
```

Every implementation takes the same argument. Underscores in numeric literals are a PHP 7.4+ feature and make these values far easier to read at a glance — use them.

### Configure it per model, not per project

This is the mistake worth warning against explicitly. If your provider is configurable (Section 3.6) then your context limit is too. A value hardcoded for a 200K model becomes wrong the moment someone sets `NEURON_PROVIDER=ollama` and gets a 32K local model.

Derive it:

```php
// src/ProviderFactory.php
public static function contextWindow(?string $driver = null): int
{
    $driver ??= env('NEURON_PROVIDER', 'ollama');

    return (int) match ($driver) {
        'anthropic' => 185_000,
        'openai'    => 118_000,
        'gemini'    => 920_000,
        'mistral'   => 118_000,
        'ollama'    => 29_000,
        default     => 29_000,
    };
}
```

```php
protected function chatHistory(): ChatHistoryInterface
{
    return new InMemoryChatHistory(
        contextWindow: ProviderFactory::contextWindow()
    );
}
```

### What trimming costs you

Trimming discards the oldest messages. The user established a constraint in message three — "always answer in Spanish", "my account number is X" — and at message forty it is gone. The agent appears to develop amnesia mid-conversation, which reads to users as a bug even though it is working as designed.

Three mitigations, in increasing order of sophistication:

**Restate constants in the system prompt.** The system prompt is re-sent every turn and is not subject to trimming. Anything that must survive belongs there, not in the transcript.

**Summarise instead of dropping.** NeuronAI ships a summarisation middleware: rather than deleting the oldest turns, compress them into a short summary message that stays in context. Higher fidelity, at the cost of an extra LLM call. Covered with the other middleware in Chapter 15.

**Move durable facts out of the transcript entirely.** Long-term memory — Section 4.5.

### Key takeaways

- Configure 5–10 % under the model's real limit; the trimmer needs headroom.
- Derive the value from the provider, never hardcode it project-wide.
- Trimming drops the oldest messages — durable constraints belong in the system prompt.
- Summarisation preserves more context at the cost of one extra call.

## 4.5 Session Memory vs Long-Term Memory

Three different things get called "memory". Picking the wrong one produces architecture that cannot be fixed by tuning.

### Three mechanisms

**1. Session memory — `ChatHistory`.**
The current conversation. Bounded by the context window, trimmed automatically, scoped to one thread. Answers: "what did we just say?"

**2. Long-term memory — an external fact store.**
Durable facts about a user or entity that persist across conversations. Not bounded by the context window because it is not in the transcript — the agent retrieves from it on demand, through a tool. Answers: "what do I know about this person?"

**3. Knowledge — RAG.**
Your documents, indexed and retrieved by semantic similarity. Not about the user at all; about your domain. Answers: "what does our documentation say?"

The three are constantly conflated in product conversations, and the confusion produces bad architecture. "The bot should remember the customer's preferences" is mechanism 2. "The bot should answer from our manual" is mechanism 3. Building the first with the third — indexing conversations into a vector store — is a design error that produces vague, unreliable recall.

### Long-term memory in NeuronAI

NeuronAI ships a toolkit for Zep, a knowledge-graph service designed for exactly this:

```php
use NeuronAI\Tools\Toolkits\Zep\ZepLongTermMemoryToolkit;

protected function tools(): array
{
    return [
        ZepLongTermMemoryToolkit::make(
            key: 'ZEP_API_KEY',
            user_id: 'ID',
        ),
    ];
}
```

Note carefully that this is a **toolkit**, not a history component. That is the architectural statement: long-term memory is something the agent *chooses to consult*, through a tool call, not something automatically injected into every request. The model decides when a fact is worth looking up or worth storing.

The `user_id` argument partitions the store. Use it as the isolation key for whatever entity you are tracking — a user, a company, a project.

### The decision table

| Requirement | Mechanism |
|---|---|
| "Follow up on what I just said" | Session memory |
| "Remember I'm vegetarian, forever" | Long-term memory |
| "Answer from our return policy" | RAG |
| "Never reveal internal pricing" | System prompt |
| "How many orders has this customer placed?" | Database tool |

That last row deserves emphasis, because it is the error people make most often. The number of orders is a **fact in your database**. It is not memory and it is not RAG. Ask it with SQL, through a tool. Reaching for a vector store to answer a countable question is a design smell, and it produces answers that are approximately right — which for a count is the same as wrong.

### The privacy dimension

Long-term memory means storing personal facts, derived by a language model, in a third-party service. That is a GDPR conversation before it is an engineering conversation:

- What is your legal basis for storing it?
- Can the user see what has been stored about them?
- Can they have it deleted, and does deletion propagate?
- Where does the store physically live?

None of this is a reason to avoid the pattern. It is a reason to design it deliberately rather than discovering it in an audit. Chapter 23 returns to this.

### Exercise

For an application you actually work on, list five things it would need to "remember". Classify each into one of the five rows of the decision table above, and justify the ones that were not obvious. The rows that were hard to classify are the ones that will cause you trouble in production.

### Key takeaways

- Three distinct mechanisms: session memory, long-term memory, knowledge retrieval.
- Long-term memory is a **toolkit** — consulted deliberately, not injected automatically.
- Countable facts come from the database, never from a vector store.
- Storing derived personal facts is a privacy decision, not just a technical one.

## Lab 2 — A Persistent CLI Chat

The most convincing demonstration of everything in this chapter: close the terminal, reopen it, and the conversation is still there.

### The agent

**`src/Agents/PersistentAgent.php`**

```php
<?php

declare(strict_types=1);

namespace App\Agents;

use App\ProviderFactory;
use NeuronAI\Agent\Agent;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Chat\History\ChatHistoryInterface;
use NeuronAI\Chat\History\FileChatHistory;
use NeuronAI\Providers\AIProviderInterface;

class PersistentAgent extends Agent
{
    public function __construct(protected string $threadId = 'default')
    {
        parent::__construct();
    }

    protected function provider(): AIProviderInterface
    {
        return ProviderFactory::make();
    }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: ['You are a technical assistant that remembers conversation context.'],
            output: ['Answer concisely.'],
        );
    }

    protected function chatHistory(): ChatHistoryInterface
    {
        return new FileChatHistory(
            directory: \dirname(__DIR__, 2) . '/storage/chat',
            key: $this->threadId,
            contextWindow: ProviderFactory::contextWindow(),
        );
    }
}
```

Two details that cause silent failures. **`parent::__construct()`** — forget it and the base class never initialises, which produces a confusing error a long way from its cause. And because this agent takes a constructor argument, instantiate it with `new`, not `::make()`.

### The loop

**`examples/04-chat-loop.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\PersistentAgent;
use NeuronAI\Chat\Messages\UserMessage;

$threadId = $argv[1] ?? 'default';
$agent = new PersistentAgent($threadId);

echo "Thread: {$threadId} — /exit to quit, /reset to clear memory.\n\n";

while (true) {
    $input = \readline('> ');

    if ($input === false || \trim($input) === '') {
        continue;
    }

    $input = \trim($input);
    \readline_add_history($input);

    if ($input === '/exit') {
        break;
    }

    if ($input === '/reset') {
        foreach (\glob(\dirname(__DIR__) . "/storage/chat/{$threadId}*") ?: [] as $file) {
            \unlink($file);
        }
        $agent = new PersistentAgent($threadId);
        echo "Memory cleared.\n\n";
        continue;
    }

    try {
        $reply = $agent->chat(new UserMessage($input))->getMessage();
        echo "\n" . $reply->getContent() . "\n\n";
    } catch (\Throwable $e) {
        \fwrite(STDERR, "Error: {$e->getMessage()}\n\n");
    }
}
```

```bash
php examples/04-chat-loop.php project-alpha
```

Tell it something. Quit. Reopen the terminal. Run the same command again and ask it what you said. **That** is the demonstration — the transcript came off disk and was re-sent, exactly as Section 4.2 described. Nothing was remembered; something was replayed.

::: {.callout .callout-tip}
[In practice]{.callout-title}

The `/reset` implementation uses a glob because the exact filename produced by `FileChatHistory` is an implementation detail that has moved between versions. Look at what actually lands in `storage/chat/` on your install and tighten the pattern — a stray glob that matches more than you intended is a bad habit to carry into code that deletes files.
:::

### Acceptance criteria

- Two different thread IDs maintain two independent conversations.
- The conversation survives a full process restart.
- `/reset` clears one thread and leaves the other intact.
- A provider error prints to `STDERR` and returns you to the prompt rather than killing the loop.

### Going further

Add a `/history` command that prints the current transcript with roles, and watch what trimming actually removes as the conversation grows past your configured `contextWindow`. Set it deliberately low — 2,000 tokens — to see it happen within a few turns rather than a few hundred.
