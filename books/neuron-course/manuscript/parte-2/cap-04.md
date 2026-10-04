# Chapter 4 — Messages and Memory

::: {.callout .callout-tip}
[Code for this chapter]{.callout-title}

The persistent CLI chat from Lab 2 is at [`chapters/Ch04`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch04), in the companion repository: `PersistentAgent.php` and `run/chat-loop.php`. Like every example there, it runs against a local Ollama with no API key.
:::

## 4.1 The Message Model

NeuronAI has a unified message layer — roles, content blocks, metadata — and it is the piece that makes provider swapping actually work rather than merely appear to.

### Why a unified message layer exists

Every provider has its own request and response shape. OpenAI, Anthropic, Gemini and Ollama differ in how they represent roles, how they attach images, how they return tool calls, how they surface reasoning traces.

NeuronAI's answer is a single message abstraction that maps onto all of them. This is what makes Section 3.6 more than a party trick: the swap works because the message layer absorbs the differences. Without it, "change one line to change provider" would be false the moment you attached an image or read a tool call.

### What a message is

Three parts:

- **Role** — who is speaking: user, assistant, or system. The agent's instructions travel as a `SystemMessage`; a tool call is a specialised assistant message (`ToolCallMessage`) and its result a specialised user message (`ToolResultMessage`)
- **Content blocks** — the actual payload
- **Metadata** — additional information from the provider response, such as token usage

### Content blocks

This is the part most people miss. A message does not hold a string. It holds an ordered **list of content blocks**, each implementing `ContentBlockInterface`. NeuronAI provides block types for text, reasoning, image, file, audio and video — plus the system block that instructions are made of (Section 3.5) — and maps each one into the correct provider-specific format automatically.

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

Now `getContent()` makes sense: it joins all text blocks into one string, separated by spaces, and returns `null` when the message has no text at all. It is a convenience, not the underlying structure.

### Reading a response properly

```php
$response = MyAgent::make()
    ->setThreadId('demo')
    ->chat(new UserMessage('...'))
    ->getMessage();

// Convenience: all text blocks joined
echo $response?->getContent();
```

But with a reasoning model, the response carries more than text:

```php
use NeuronAI\Chat\Messages\ContentBlocks\ReasoningContent;
use NeuronAI\Chat\Messages\ContentBlocks\TextContent;

foreach ($response?->getContentBlocks() ?? [] as $block) {
    echo match ($block::class) {
        ReasoningContent::class => "Reasoning: {$block->content}\n\n",
        TextContent::class      => $block->content,
        default                 => '',
    };
}
```

NeuronAI captures the model's reasoning steps as a distinct block automatically, and `getContent()` deliberately leaves it out. If you only ever call `getContent()`, you never see them; `$response->getReasoning()` is the shortcut when you want just that block. For debugging an agent that made a strange decision, the reasoning block is often the answer.

### Building a conversation by hand

Sometimes you already hold a conversation — from your own database, or an import — and need to seed the agent with it. Pass an array to `chat()`:

```php
use NeuronAI\Chat\Enums\MessageRole;
use NeuronAI\Chat\Messages\Message;

$message = MyAgent::make()
    ->setThreadId('demo')
    ->chat([
        new Message(MessageRole::USER, 'Hi, my company is called Inspector.dev'),
        new Message(MessageRole::ASSISTANT, 'Great, how can I assist you today?'),
        new Message(MessageRole::USER, 'What is the name of the company I work for?'),
    ])
    ->getMessage();

echo $message?->getContent();
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
[Attachments in older tutorials]{.callout-title}

Tutorials written for older versions attach media with `addAttachment(new Image($url, ...))`. That call does not exist here; media is a content block, as above. Related: the documentation is inconsistent about block class names — `TextBlock`/`FileBlock` appear in some places where the shipped classes are `TextContent`/`FileContent`, and one example imports `AudioContent` while instantiating `FileContent`. See items 10 and 11 in Appendix A.
:::

### Key takeaways

- A message is role + content blocks + metadata; not a string.
- `getContent()` joins text blocks; `getContentBlocks()` gives you everything, including reasoning.
- Pass an array of `Message` objects to seed an existing conversation.
- The unified message layer is why provider swapping survives contact with images, files and tool calls.

## 4.2 The Model Has No Memory

Statelessness is a design constraint, not a limitation to work around. This section is about internalising it, because almost every confusion about "memory" dissolves once you do.

### The demonstration

Take the `AssistantAgent` from Lab 1 and ask it something it cannot know:

```php
use App\Agents\AssistantAgent;
use NeuronAI\Chat\Messages\UserMessage;

$message = AssistantAgent::make()
    ->setThreadId('demo')
    ->chat(new UserMessage("What's my name?"))
    ->getMessage();

echo $message?->getContent();
// I'm sorry, I don't know your name.
```

Now hold on to the same instance:

```php
$agent = AssistantAgent::make()->setThreadId('demo');

$agent->chat(new UserMessage('Hi, my name is Valerio!'));

$message = $agent->chat(new UserMessage('Do you remember my name?'))->getMessage();
echo $message?->getContent();
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

The NeuronAI component that re-sends the transcript is `ChatHistory`, and it reads it from a *message store* — here the default one, which lives in the memory of that one agent object. That is the entirety of what "memory" means at this layer.

### Four consequences worth stating

**1. Memory costs money on every turn.**
Turn twenty re-sends nineteen previous exchanges. This is the mechanism behind the cost table in Section 1.4, and it is why long conversations get expensive even when the individual messages are short.

**2. Memory is bounded by the context window.**
It is not a database that grows. It is a buffer with a hard ceiling. Something must be discarded eventually, and the only question is what and how — Section 4.4.

**3. Memory is entirely under your control.**
Which is liberating once you accept it. You can edit history, inject a summary, drop irrelevant turns, keep a system-level fact permanently pinned. Nothing is sacred; it is your array.

**4. Statelessness is why horizontal scaling is easy.**
Any web server can serve any request, as long as it can load the transcript. There is no session affinity to a provider. Keep the messages in shared storage and any node can continue any conversation. This is a genuine architectural advantage, and it is unusual for a stateful-feeling feature to scale this cleanly.

### The mental model to keep

The model is a **pure function**: transcript in, next message out. Everything that feels like memory, personality persistence or learning is your code choosing what goes into the transcript.

Every technique in the rest of this book — history trimming, summarisation, RAG, long-term memory stores — is a different answer to one question: **what do we put in the transcript?**

### Key takeaways

- No server-side session; the transcript is re-sent every turn.
- Memory costs tokens on every turn and is capped by the context window.
- History is your array — editable, injectable, replaceable.
- The model is a pure function of the transcript.

## 4.3 ChatHistory and Message Stores

### The interface

```php
NeuronAI\Chat\History\MessageStoreInterface
```

Session memory is two classes with two jobs. `ChatHistory` is concrete, and you never build it yourself: each time a run starts or resumes, the agent opens one for its thread, and that object loads the conversation, keeps it inside the context window and writes new messages through. Where the messages are kept is a **message store** — anything that implements the interface above — and that is the part you choose.

Choose it by implementing `messageStore()` on your agent, or by passing an instance to `setMessageStore()`; size the window with `contextWindow()` or `setContextWindow()` (Section 4.4). A setter, once called, wins over the method. The default, if you do none of this, is an in-memory store and a window of 50,000 tokens.

The history is a service the agent's nodes use, not part of the run's state: `ChatNode` reads the transcript from it and appends to it, and the transcript is never copied into the `AgentState` that `chat()` returns. That separation matters once runs become durable (Chapter 15). A paused run's saved state stays small no matter how long the conversation grows, and the conversation lives in exactly one place: the store.

::: {.callout .callout-warning}
[History code in older tutorials]{.callout-title}

Tutorials written for older versions build the history itself — a `FileChatHistory`, an `SQLChatHistory` — in a `chatHistory()` method on the agent. Those classes are gone, and the failure is silent: nothing calls a method named `chatHistory()`, so the agent loads, answers, and keeps the conversation in the default in-memory store. If a conversation does not survive a restart, look for that method first.
:::

### Which conversation? The thread ID

A history always belongs to one conversation — a **thread** — and something has to say which. In NeuronAI that something is the agent, not the store:

```php
$agent = SupportAgent::make(workflowId: $threadId);
```

A store has no thread of its own. Every method on the interface takes the thread ID as an argument, so one store serves every conversation, and the agent supplies the ID: it opens its history over the store *for its own thread*. Identity enters in one place, at the call site that actually knows which conversation this request is about, and never inside the class that merely knows where conversations are stored.

It is the same ID Section 2.3 talked about: the thread ID is also the agent run's workflow ID, which is why the constructor argument is called `workflowId:`. `setThreadId()`, from Section 3.4, sets the same value after construction. When a run pauses for a human approval in Chapter 15, the endpoint that resumes it needs nothing but the thread ID to find it.

Two rules follow, and both are enforced:

- **An agent without a thread refuses to work.** The framework never generates an ID. Call `chat()`, `getChatHistory()` or `resetConversation()` on an unbound agent and you get an `AgentException` — *"This agent has no thread ID: bind one with setThreadId() first."* — rather than a conversation quietly filed under a key nobody chose.
- **An agent is bound once.** Setting the same ID again is harmless; setting a different one throws, rather than silently writing the rest of the conversation to another thread. To serve another conversation, build another agent, or call `$agent->for($otherThreadId)`, which returns a copy bound to that thread.

An agent class with a constructor of its own must still call `parent::__construct()`: pass the thread ID to it, or bind the thread afterwards with `setThreadId()` or `for()`.

::: {.callout .callout-warning}
[The thread ID is user input]{.callout-title}

Whatever you pass as `workflowId:` selects which conversation is loaded, extended and resumed. If it arrives in a request — a URL segment, a form field — check that the current user owns that thread before you build the agent with it. The framework does no access control; one missing ownership check and any user can read any other user's conversation.
:::

### InMemoryMessageStore

```php
use NeuronAI\Chat\History\InMemoryMessageStore;
use NeuronAI\Chat\History\MessageStoreInterface;

protected function messageStore(): MessageStoreInterface
{
    return new InMemoryMessageStore();
}
```

An array per thread, in process memory. It is the default, so the method above only spells out what an agent without a `messageStore()` already does — the `AssistantAgent` of Lab 1, for instance. The store belongs to the agent object that created it: keep the object and the conversation continues, as in Section 4.2; build a second agent with the same thread ID and it starts empty, because it has a store of its own. Correct for: single-shot scripts, stateless API endpoints where you hold the conversation yourself, and tests.

Remember that in a normal web request PHP dies at the end of the response. An in-memory store in a web context means **no memory between requests**, which is a genuinely common surprise for developers used to long-running runtimes.

### FileMessageStore

```php
use NeuronAI\Chat\History\FileMessageStore;

protected function messageStore(): MessageStoreInterface
{
    return new FileMessageStore(directory: '/home/app/storage/neuron');
}
```

`directory` is an absolute path, created on the first write if it does not exist. Each thread is one JSON file in it, `neuron_<thread>.chat`, named after the thread ID the agent passes in — URL-encoded, so that an ID can never name a path outside the directory. Use a user ID as the thread for one conversation per user, or a generated thread ID for many.

Correct for: CLI tools, single-server apps, prototypes. Not correct for: multi-server deployments without shared storage, or concurrent workers — every write replaces the whole file, and two processes writing to the same thread will lose messages. One trap sits closer to home: the file name keeps the thread ID's letter case, so on a case-insensitive filesystem — the macOS and Windows defaults — `user-Alice` and `user-alice` are one file and one conversation.

### SQLMessageStore

Create the table first. One row per message: `id` orders the thread, and `message_id` is the message's own identity, unique within its thread. This is the table for MySQL and MariaDB:

```sql
CREATE TABLE chat_messages (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  thread_id VARBINARY(255) NOT NULL,
  message_id VARBINARY(64) NOT NULL,
  role VARCHAR(32) NOT NULL,
  content LONGTEXT NULL,
  meta LONGTEXT NULL,
  archived_at DATETIME NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  UNIQUE INDEX idx_thread_message (thread_id, message_id)
);
```

`VARBINARY` on the two ID columns is deliberate. Thread and message IDs must compare byte for byte, and the default collations of MySQL and MariaDB ignore case and accents: declare those columns `VARCHAR` and `user-Alice` and `user-alice` read, and clear, each other's messages. PostgreSQL and SQLite compare text exactly, so there both are plain `VARCHAR`, and the rest of the table needs only the usual dialect changes: `BIGSERIAL` or `INTEGER PRIMARY KEY AUTOINCREMENT` for `id`, `TEXT` and `TIMESTAMP` types, no `ON UPDATE` clause, and a plain `UNIQUE (thread_id, message_id)`.

```php
use NeuronAI\Chat\History\SQLMessageStore;

protected function messageStore(): MessageStoreInterface
{
    return new SQLMessageStore(
        pdo: new \PDO('mysql:host=localhost;dbname=DB;charset=utf8mb4', 'user', 'pass'),
        table: 'chat_messages',
    );
}
```

It takes a plain `PDO`, so it works in any PHP application regardless of framework. In Laravel you would pass `\DB::connection()->getPdo()`; in Symfony, `$connection->getNativeConnection()` from a Doctrine connection.

Because each message is its own row — `role`, the content blocks as JSON in `content`, everything else (usage, tool calls, metadata) as JSON in `meta` — the table is useful to the rest of your application, not just to the agent: per-message reporting, retention jobs, a support dashboard that lists conversations. You can add columns — a foreign key to your users table, for instance — as long as they are nullable and the base structure stays. `archived_at` is explained in Section 4.4.

### EloquentMessageStore

Covered fully in Chapter 18, listed here so the map is complete:

```php
new EloquentMessageStore(modelClass: ChatMessage::class);
```

Same table shape as the SQL store, same indifference to threads: the model class is the only thing it needs to know.

### Choosing

| Store | Use when | Avoid when |
|---|---|---|
| InMemory | Scripts, stateless endpoints, tests | You need persistence |
| File | CLI tools, single server, prototypes | Multi-server, concurrent workers |
| SQL | Any framework, production, multi-server | You have no database |
| Eloquent | Laravel with relations and scopes | You are not on Laravel |

Lab 2, at the end of this chapter, builds a persistent CLI chat on `FileMessageStore`.

### Key takeaways

- One concrete `ChatHistory`, four message stores: InMemory, File, SQL, Eloquent.
- A store carries no thread. Give the agent `make(workflowId: ...)` or `setThreadId()`, and it opens the history for that thread; without one it refuses to run. The thread ID is also the run's workflow ID.
- Authorise the thread ID before using it: it selects whose conversation is loaded.
- In a web request, in-memory means no memory between requests.
- `SQLMessageStore` takes a plain PDO, stores one row per message and works in any framework.

## 4.4 Context Window and Trimming

### The bug this prevents

The most common production failure in conversational AI:

> "It works fine, then after about thirty messages it starts throwing errors."

The transcript grew past the model's context limit. A cloud provider rejects the request — it does not truncate for you, it returns an error. Ollama fails the other way: it truncates the prompt to its `num_ctx` and answers from what is left, with no error at all.

NeuronAI's `ChatHistory` prevents both by trimming automatically. It tracks token usage from the provider responses and, when the conversation no longer fits the configured window, takes messages off the beginning of what it sends to the model.

"Takes off what it sends" is deliberate wording. Trimming never deletes. The history asks its store to archive what it dropped, and every store does: an `archived_at` timestamp on the row (Section 4.3) or on the entry in the file, a counter in memory. The model sees the trimmed thread; `loadAll()` on the store still returns the full transcript, for auditing, analytics, a retention policy or a screen that pages back through the conversation. `flushAll()` is the one operation that really deletes a thread, archived messages included.

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

The trimmer does not simply chop at the message where the limit is hit. A history must open with a user message, so a cut can only fall at the start of a turn. When the smallest cut that fits lands inside one, the trimmer keeps that whole turn as long as the result stays within 5 % over the window, and only beyond that cuts at the next turn. The latest turn is kept however large it is.

So the window is a target the trimmer may overshoot a little, rather than drop a long tool exchange to save a few tokens. Configure at exactly the model's limit and that tolerance has nowhere to go, and you can still overflow. The margin is what lets it choose a sensible boundary rather than a mechanical one.

### Where it goes

```php
protected function contextWindow(): int
{
    return 185_000;
}
```

The window belongs to the agent, not to the store: whichever store you chose, this is where it is set, or with `setContextWindow()` from outside. Leave it out and you get 50,000 tokens — more than a 32K local model can take. Underscores in numeric literals are a PHP 7.4+ feature and make these values far easier to read at a glance — use them.

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
protected function contextWindow(): int
{
    return ProviderFactory::contextWindow();
}
```

The Ollama figure is the only one that depends on your own configuration. 29,000 assumes a 32K window, and a local model has one only if you ask for it: `parameters: ['options' => ['num_ctx' => 32_768]]` on the Ollama provider, as the factory in Section 3.6 does. Without it Ollama truncates at its own default, usually far smaller, long before the trimmer sees any reason to act. Change one number and you must change the other.

### What trimming costs you

Trimming takes the oldest messages out of the model's view. The user established a constraint in message three — "always answer in Spanish", "my account number is X" — and at message forty it is gone. The agent appears to develop amnesia mid-conversation, which reads to users as a bug even though it is working as designed.

Three mitigations, in increasing order of sophistication:

**Restate constants in the system prompt.** The system prompt is re-sent every turn and is not subject to trimming. Anything that must survive belongs there, not in the transcript.

**Summarise instead of dropping.** NeuronAI ships a summarisation middleware, `Summarization`, which you attach to the agent's inference nodes (Section 2.3): once the conversation passes a token budget, it replaces everything but the last few messages with a short summary message that stays in context. The model keeps more of the thread, at the cost of an extra LLM call — and of the transcript. The middleware rewrites the thread through `flushAll()`, so the original messages, archived ones included, are gone from the store; if you need that record, keep a copy of your own. Middleware is covered in Chapter 15.

**Move durable facts out of the transcript entirely.** Long-term memory — Section 4.5.

### Key takeaways

- Configure 5–10 % under the model's real limit; the trimmer needs headroom.
- Derive the value from the provider, never hardcode it project-wide. On Ollama, set `num_ctx` to match: it truncates silently instead of failing.
- Trimming hides the oldest messages from the model — durable constraints belong in the system prompt.
- Every store archives trimmed messages instead of deleting them; the full transcript stays in your storage.
- Summarisation preserves more context at the cost of one extra call — and of the stored transcript, which it replaces.

## 4.5 Session Memory vs Long-Term Memory

Three different things get called "memory". Picking the wrong one produces architecture that cannot be fixed by tuning.

### Three mechanisms

**1. Session memory — `ChatHistory`.**
The current conversation. Bounded by the context window, trimmed automatically, scoped to one thread. Answers: "what did we just say?"

**2. Long-term memory — a store outside the transcript.**
What earlier conversations established about a user or entity, kept beyond any one thread. Not bounded by the context window because it is not in the transcript — only what is relevant to the current question is fetched back in. Answers: "what do I know about this person?"

**3. Knowledge — RAG.**
Your documents, indexed and retrieved by semantic similarity. Not about the user at all; about your domain. Answers: "what does our documentation say?"

The three are constantly conflated in product conversations, and the confusion produces bad architecture. "The bot should remember the customer's preferences" is mechanism 2. "The bot should answer from our manual" is mechanism 3. The two can share machinery — NeuronAI builds the second from the third's components — but never a store: index conversations into the same vector store as the manual and one customer's words come back as the answer to another customer's question.

### Long-term memory in NeuronAI

NeuronAI's conversation memory has two halves, both built from RAG components (Chapter 12) and each opt-in on its own. The writing half is a node. Return a `ConversationIngestionNode` from the agent's `exitNodes()` method, in place of the default ending, and every completed turn — the user's text and the model's final answer, never the tool calls — is stored as one document in a vector store, labelled with its thread ID. The node needs that store and an embeddings provider, injected here through the constructor:

```php
use NeuronAI\RAG\Embeddings\EmbeddingsProviderInterface;
use NeuronAI\RAG\Nodes\ConversationIngestionNode;
use NeuronAI\RAG\VectorStore\VectorStoreInterface;

public function __construct(
    protected VectorStoreInterface $conversationStore,
    protected EmbeddingsProviderInterface $embeddings,
) {
    parent::__construct();
}

protected function exitNodes(): array
{
    return [new ConversationIngestionNode(
        vectorStore: $this->conversationStore,
        embeddingProvider: $this->embeddings,
    )];
}
```

The reading half is a retrieval strategy, `SemanticMemoryRetrieval`. Given the same store and a list of thread IDs, a RAG agent (Section 12.7) finds the past exchanges closest in meaning to the current question and adds them to the prompt as extra context.

Note carefully that this is **retrieval**, not a history component. That is the architectural statement: long-term memory is not a longer transcript re-sent on every turn. It is a search, and only what the search returns reaches the model.

The list of thread IDs partitions the store. It is an allowlist, and nothing is added to it for you, not even the current thread: pass exactly the threads this user is entitled to recall. Keep conversations in a vector store of their own, too. Only this strategy applies the allowlist; any other retrieval over the same store returns everyone's conversations.

Older material uses a toolkit for this job, `ZepLongTermMemoryToolkit`. It still ships, but it is deprecated and will be removed in the next major version.

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

Long-term memory means storing what people told your application, and what a language model answered, beyond the conversation it was said in — often in a third-party service. That is a GDPR conversation before it is an engineering conversation:

- What is your legal basis for storing it?
- Can the user see what has been stored about them?
- Can they have it deleted, and does deletion propagate?
- Where does the store physically live?

On the third question: `resetConversation()` clears the chat history and nothing else. The documents in the conversation store have a lifecycle of their own and are deleted separately, through the vector store, thread by thread.

None of this is a reason to avoid the pattern. It is a reason to design it deliberately rather than discovering it in an audit. Chapter 23 returns to this.

### Exercise

For an application you actually work on, list five things it would need to "remember". Classify each into one of the five rows of the decision table above, and justify the ones that were not obvious. The rows that were hard to classify are the ones that will cause you trouble in production.

### Key takeaways

- Three distinct mechanisms: session memory, long-term memory, knowledge retrieval.
- Long-term memory is **retrieval** over a conversation store of its own, scoped by an explicit list of thread IDs — searched per question, not re-sent every turn.
- Countable facts come from the database, never from a vector store.
- Storing what users said beyond the conversation is a privacy decision, not just a technical one.

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
use NeuronAI\Chat\History\FileMessageStore;
use NeuronAI\Chat\History\MessageStoreInterface;
use NeuronAI\Providers\AIProviderInterface;

class PersistentAgent extends Agent
{
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

    protected function messageStore(): MessageStoreInterface
    {
        return new FileMessageStore(
            directory: \dirname(__DIR__, 2) . '/storage/chat',
        );
    }

    protected function contextWindow(): int
    {
        return ProviderFactory::contextWindow();
    }
}
```

Notice what the class does *not* contain: a thread ID. There is no constructor, no `$threadId` property, no key passed to `FileMessageStore`. The class describes where conversations are stored; which conversation this run belongs to is decided by whoever builds the agent, through `make(workflowId: ...)`, exactly as Section 4.3 described. The same class serves every thread.

### The loop

**`examples/04-chat-loop.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\PersistentAgent;
use NeuronAI\Chat\Messages\UserMessage;

$threadId = $argv[1] ?? 'default';
$agent = PersistentAgent::make(workflowId: $threadId);

echo "Thread: {$threadId} — /exit to quit, /reset to clear memory.\n\n";

while (true) {
    $input = \readline('> ');

    if ($input === false) {
        break;
    }

    $input = \trim($input);

    if ($input === '') {
        continue;
    }

    \readline_add_history($input);

    if ($input === '/exit') {
        break;
    }

    if ($input === '/reset') {
        $agent->resetConversation();
        echo "Memory cleared.\n\n";
        continue;
    }

    try {
        $reply = $agent->chat(new UserMessage($input))->getMessage();
        echo "\n" . $reply?->getContent() . "\n\n";
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

`/reset` does not touch the filesystem. `resetConversation()` asks the agent to forget: it abandons any unfinished run on the thread and calls `flushAll()` on the history, which clears the thread in the store — for `FileMessageStore`, by deleting that thread's file, archived messages included, and nothing else. Deleting files by hand with a glob couples your code to a filename format that is the library's business, and a pattern that matches more than you intended is a bad habit to carry into code that deletes things. Look in `storage/chat/` before and after a reset to see it for yourself.
:::

### Acceptance criteria

- Two different thread IDs maintain two independent conversations.
- The conversation survives a full process restart.
- `/reset` clears one thread and leaves the other intact.
- A provider error prints to `STDERR` and returns you to the prompt rather than killing the loop.

### Going further

Add a `/history` command that prints the current transcript with roles — `$agent->getChatHistory()->getMessages()` gives you the `Message` objects, and `getRole()` on each — and watch what trimming takes out of view as the conversation grows past the context window. Set it deliberately low — `->setContextWindow(2_000)` on the agent the loop builds — to see it happen within a few turns rather than a few hundred. Then open the thread's file in `storage/chat/`: the trimmed messages are still there, marked `archived_at`.
