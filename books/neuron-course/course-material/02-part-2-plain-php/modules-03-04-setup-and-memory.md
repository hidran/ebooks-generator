# Agentic AI in PHP with Neuron
## PART II — PLAIN PHP + COMPOSER
### Full lesson scripts — Modules 3 and 4

> Copy each lesson block (between the `═══` separators) into its own Google Doc.
> Target version: `neuron-core/neuron-ai` ^3.0, PHP 8.3.

---
═══════════════════════════════════════════════════════════════
# MODULE 3 — SETUP AND YOUR FIRST AGENT
═══════════════════════════════════════════════════════════════
---

## LESSON 3.1 — Project Scaffolding

**Duration:** 10 minutes
**Type:** Hands-on

### Learning objectives

Build a clean plain-PHP project that will carry every example in Parts II, III and IV, with no framework and no magic.

### Why plain PHP first

You are going to spend Part V inside Laravel, where a facade hands you a configured agent and an artisan command generates your classes. That convenience is worth having — but only after you have seen what it is hiding. Everything the Laravel SDK does, you will have already done by hand.

This also matters commercially: a large share of PHP work is not Laravel. Symfony, Spryker, WordPress, legacy in-house MVC. An agent built on the plain package drops into any of them.

### Create the project

```bash
mkdir -p neuron-course/01-plain-php && cd neuron-course/01-plain-php

mkdir -p src/Agents src/Tools src/Dto examples storage/chat
touch bootstrap.php .env .env.example .gitignore
touch storage/chat/.gitkeep
```

```bash
composer init --name="yourname/neuron-lab" --type=project --no-interaction
```

### composer.json

```json
{
    "name": "yourname/neuron-lab",
    "type": "project",
    "require": {
        "php": "^8.1"
    },
    "autoload": {
        "psr-4": {
            "App\\": "src/"
        }
    },
    "config": {
        "sort-packages": true
    },
    "minimum-stability": "stable",
    "prefer-stable": true
}
```

The PSR-4 block maps the `App\` namespace to `src/`. `App\Agents\WeatherAgent` lives at `src/Agents/WeatherAgent.php`. Nothing exotic — but get it wrong and every later example fails with a class-not-found error, so verify it now:

```bash
composer dump-autoload
```

### .gitignore

```gitignore
/vendor/
/storage/chat/*
!/storage/chat/.gitkeep
.env
.phpunit.result.cache
```

Two lines here are load-bearing. `/vendor/` because it is regenerable. `.env` because it will hold API keys, and a leaked key on a public repository is charged to you within hours. Lesson 3.7 covers this properly.

### Final layout

```
01-plain-php/
├── composer.json
├── bootstrap.php
├── .env                 ← real keys, never committed
├── .env.example         ← structure only, committed
├── src/
│   ├── Agents/
│   ├── Tools/
│   └── Dto/
├── examples/            ← one runnable script per lesson
└── storage/chat/        ← persisted conversations
```

### Key takeaways

- Plain PHP first; the framework SDK adds convenience, not capability.
- PSR-4 maps `App\` → `src/`; verify with `composer dump-autoload` before writing code.
- `.env` is in `.gitignore` from minute one.

---
═══════════════════════════════════════════════════════════════

## LESSON 3.2 — Installing Neuron

**Duration:** 8 minutes
**Type:** Hands-on

### Learning objectives

Install the framework and its supporting packages, and understand what each dependency is doing there.

### The install

```bash
composer require neuron-core/neuron-ai vlucas/phpdotenv guzzlehttp/guzzle
```

**`neuron-core/neuron-ai`** — the framework. Requires PHP 8.1 or later.

**`vlucas/phpdotenv`** — reads a `.env` file into the environment. Laravel ships this; plain PHP does not. Without it you would hardcode API keys, which we are not going to do.

**`guzzlehttp/guzzle`** — an HTTP client. Neuron pulls in what it needs internally; we require it explicitly because our own tools will call external APIs in Module 5, and an explicit dependency is an honest dependency.

### Pin the version

```json
"require": {
    "php": "^8.1",
    "neuron-core/neuron-ai": "^3.0",
    "vlucas/phpdotenv": "^5.6",
    "guzzlehttp/guzzle": "^7.9"
}
```

**Commit `composer.lock` in the course repository.** This is not the usual library advice — it is deliberate. A student who follows this course six months from now must get the same API you recorded against. Without the lock file they get whatever `^3.0` resolves to that day, and if a minor release changed a signature, they get an error you never saw and cannot support.

### Verify

```bash
php -r "require 'vendor/autoload.php'; echo class_exists(NeuronAI\Agent\Agent::class) ? 'OK' : 'FAIL';"
```

If that prints `FAIL`, you are almost certainly on an older major version where the class was `NeuronAI\Agent`. Check with:

```bash
composer show neuron-core/neuron-ai | head -5
```

### A word about namespaces and the documentation

Between v2 and v3 the namespaces moved:

| v1 / v2 | v3 |
|---|---|
| `NeuronAI\Agent` | `NeuronAI\Agent\Agent` |
| `NeuronAI\SystemPrompt` | `NeuronAI\Agent\SystemPrompt` |

Parts of the official documentation, several blog posts and most Medium articles still show the v2 imports. When you find sample code whose `use` statements do not match this course, check which version it targets before you assume something is broken. This is the single most common source of confusion for people arriving from tutorials.

### Key takeaways

- `composer require neuron-core/neuron-ai`, PHP 8.1+.
- Pin the version and commit `composer.lock` in teaching repositories.
- v2 → v3 moved the namespaces; older tutorials will not compile against v3.

---
═══════════════════════════════════════════════════════════════

## LESSON 3.3 — The Framework CLI

**Duration:** 9 minutes
**Type:** Hands-on

### Learning objectives

Use the generators to create framework components with correct structure, and know what they generate so you can also write the classes by hand.

### The binary

Installing the package gives you an executable at `vendor/bin/neuron`.

```bash
./vendor/bin/neuron
```

### The generators

**Unix / macOS** — note the doubled backslashes, which the shell needs:

```bash
./vendor/bin/neuron make:agent App\\Agents\\AssistantAgent
./vendor/bin/neuron make:tool App\\Tools\\WeatherTool
./vendor/bin/neuron make:node App\\Workflow\\InitialNode
./vendor/bin/neuron make:event App\\Workflow\\FirstEvent
```

**Windows PowerShell** — single backslashes:

```powershell
.\vendor\bin\neuron make:agent App\Agents\AssistantAgent
.\vendor\bin\neuron make:tool App\Tools\WeatherTool
.\vendor\bin\neuron make:node App\Workflow\InitialNode
.\vendor\bin\neuron make:event App\Workflow\FirstEvent
```

The double-backslash difference trips up a lot of students on a mixed-OS course. Put both forms on screen every time you show a generator command.

### What each one produces

| Command | Produces | Covered in |
|---|---|---|
| `make:agent` | Class extending `Agent` with `provider()` and `instructions()` stubs | Module 3 |
| `make:tool` | Class extending `Tool` with `properties()` and `__invoke()` stubs | Module 5 |
| `make:node` | Workflow node with an `__invoke(Event, WorkflowState)` stub | Module 13 |
| `make:event` | Event class implementing `Event` | Module 13 |

The generators write the file at the path implied by your PSR-4 mapping. `App\Agents\AssistantAgent` lands in `src/Agents/AssistantAgent.php` because of the mapping we set in Lesson 3.1. If it lands somewhere unexpected, your autoload block is wrong.

### The honest position on generators

They save typing and enforce naming. That is the whole benefit. Every class they produce is ordinary PHP you could type yourself in ninety seconds, and in this course we will frequently write them by hand — because a student who has only ever generated an agent does not really know what an agent is.

Use them when you are productive. Do not use them as a substitute for understanding the shape of the class.

### Key takeaways

- Four generators: `make:agent`, `make:tool`, `make:node`, `make:event`.
- Unix needs doubled backslashes; PowerShell does not.
- Output path follows your PSR-4 mapping.

---
═══════════════════════════════════════════════════════════════

## LESSON 3.4 — Your First Agent

**Duration:** 16 minutes
**Type:** Hands-on — the first running code of the course

### Learning objectives

Write, run and understand a working agent end to end.

### The three template methods

An agent class answers three questions:

- `provider()` — which LLM do I talk to?
- `instructions()` — who am I and how do I behave?
- `tools()` — what can I actually do? *(optional; Module 5)*

Everything else — the message array, the loop, the history, the tool dispatch — is inherited.

### The class

**`src/Agents/AssistantAgent.php`**

```php
<?php

declare(strict_types=1);

namespace App\Agents;

use NeuronAI\Agent\Agent;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Providers\Anthropic\Anthropic;

class AssistantAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return new Anthropic(
            key: $_ENV['ANTHROPIC_KEY'],
            model: $_ENV['ANTHROPIC_MODEL'],
        );
    }

    public function instructions(): string
    {
        return (string) new SystemPrompt(
            background: [
                'You are a technical assistant specialised in PHP development.',
                'You are talking to experienced developers. Do not explain basics unless asked.',
            ],
        );
    }
}
```

That is a complete agent. Four lines of actual configuration.

> **Visibility note.** The official documentation shows `instructions()` as `public` in some examples and `protected` in others. Both appear in the current docs. Use whichever matches the base class in the version you install — check with your IDE or `composer show` — and stay consistent across your project.

### Running it

**`examples/01-first-agent.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\AssistantAgent;
use NeuronAI\Chat\Messages\UserMessage;

$prompt = $argv[1] ?? 'Explain the difference between readonly and final in PHP 8, in three lines.';

$response = AssistantAgent::make()
    ->chat(new UserMessage($prompt))
    ->getMessage();

echo $response->getContent() . PHP_EOL;
```

```bash
php examples/01-first-agent.php "How do I implement a PSR-15 middleware without a framework?"
```

### Reading the chain, piece by piece

```php
AssistantAgent::make()
```
Static factory on the base class. Equivalent to `new AssistantAgent()` for a no-argument constructor, and it reads better in a fluent chain. When your agent takes constructor arguments — as `PersistentAgent` will in Lesson 4.3 — use `new` instead.

```php
->chat(new UserMessage($prompt))
```
Runs the loop from Lesson 1.2. One iteration here because there are no tools. Note that `chat()` returns a **response object**, not the message.

```php
->getMessage()
```
Extracts the assistant message from the response.

> **v2 → v3 change worth calling out.** In earlier versions `chat()` returned the message directly. In v3 you must call `getMessage()`. This is the second most common error when adapting older sample code, right after the namespaces.

```php
$response->getContent()
```
Returns all text content of the message concatenated into a single string. Lesson 4.1 explains why "concatenated" is the right word — a message can hold several content blocks.

### Two things that will go wrong

**Undefined array key "ANTHROPIC_KEY"** — the `.env` file is missing or not loaded. Lesson 3.7 builds `bootstrap.php` properly; for now, confirm the file exists and has the key.

**401 / authentication error** — the key is wrong, or you are billing-disabled on the provider. Check the provider console before you debug the code.

### Key takeaways

- Three template methods; the loop is inherited.
- `chat()` returns a response; `getMessage()` returns the message; `getContent()` returns the text.
- `::make()` for simple agents, `new` when the constructor takes arguments.

---
═══════════════════════════════════════════════════════════════

## LESSON 3.5 — SystemPrompt: Structuring Instructions

**Duration:** 18 minutes
**Type:** Hands-on with A/B demonstration

### Learning objectives

Write instructions that models actually follow, using Neuron's three-part structure, and understand why the structure exists.

### The problem with prompt-as-paragraph

Most people write the system prompt as one block of prose:

```php
public function instructions(): string
{
    return 'You are a support assistant for an e-commerce store. Be polite and '
         . 'always answer in Italian and if you do not know something say so and '
         . 'never invent order numbers and keep answers short and use the tools '
         . 'when you need order data and format prices with the euro symbol.';
}
```

Three problems, in ascending order of seriousness:

1. **Instructions get lost.** Models attend unevenly across a long undifferentiated block; the constraint in the middle is the one that gets dropped.
2. **It rots.** Six months and four contributors later, it is 600 words containing three contradictions that nobody can find.
3. **You cannot change one thing.** Want a different output format? You are editing a sentence wedged between an identity claim and a behavioural rule.

### The Neuron structure

`SystemPrompt` takes three named arguments and renders them into a structured prompt:

```php
use NeuronAI\Agent\SystemPrompt;

new SystemPrompt(
    background: [...],  // who you are, what domain, what you are not
    steps:      [...],  // the procedure to follow
    output:     [...],  // the contract for the response
);
```

Cast it to string with `(string)` and return it from `instructions()`.

### A real example

```php
public function instructions(): string
{
    return (string) new SystemPrompt(
        background: [
            'You are an AI Agent specialised in writing YouTube video summaries.',
        ],
        steps: [
            'Get the URL of a YouTube video, or ask the user to provide one.',
            'Use the tools you have available to retrieve the transcription of the video.',
            'Write the summary.',
        ],
        output: [
            'Write a summary in a paragraph without using lists. Use fluent text only.',
            'After the summary add a list of three sentences as the three most '
            . 'important takeaways from the video.',
        ],
    );
}
```

That is the shape from the official documentation, and it is worth studying because it is short. Each array item is one instruction. Not one paragraph — one instruction.

### The three sections, and what belongs in each

**`background` — identity and domain.**
Who the agent is, what field it operates in, who it is talking to, and — often the most valuable line — what it is *not*. "You are not a legal advisor and must not interpret contract terms" prevents an entire class of failure.

**`steps` — procedure.**
The order of operations. This is where you encode "always look it up before you answer", which is the single most effective anti-hallucination instruction available to you. If your agent has tools, the steps section is where you tell it when to reach for them.

**`output` — the response contract.**
Language, format, length, tone, forbidden phrasings. Keep this section purely about the shape of the answer. The discipline of separation is what makes the prompt maintainable: you can change your output format without touching the agent's personality or its procedure.

### The A/B demonstration to record

This is a strong five minutes of video. Same agent, same question, two prompts.

**Version A:**
```php
return 'You are a helpful PHP assistant.';
```

**Version B:**
```php
return (string) new SystemPrompt(
    background: [
        'You are a technical assistant specialised in PHP development.',
        'You are talking to experienced developers.',
    ],
    steps: [
        'Identify the real problem behind the question, not only the stated one.',
        'If the question is ambiguous, ask the single most useful clarifying question.',
    ],
    output: [
        'Answer in English.',
        'Use fenced code blocks with the language declared.',
        'No preambles such as "Certainly!" or "Great question".',
        'Maximum 200 words unless code requires more.',
    ],
);
```

Ask both: *"How do I handle file uploads?"*

Version A returns 600 words starting with "Great question!". Version B asks which framework, or answers tightly in plain PHP. Students see the difference immediately, and the point lands harder than any explanation: **the system prompt is the specification, not the greeting.**

### Practical guidance

- One instruction per array item. If an item contains "and", consider splitting it.
- Prefer positive instructions. "Answer in English" beats "don't answer in Italian".
- Negatives that matter are worth keeping, but state the boundary, not a list of forbidden words.
- Version the prompt in Git and treat prompt changes as code changes — with review. Given Lesson 1.5, a reworded prompt is a behavioural change you cannot regression-test conventionally.

### Key takeaways

- Three sections: `background` (identity), `steps` (procedure), `output` (contract).
- One instruction per array item.
- "Look it up before answering" belongs in `steps` and is your best anti-hallucination tool.
- Prompt changes are code changes; review them.

---
═══════════════════════════════════════════════════════════════

## LESSON 3.6 — Provider Swap: The Interface Pays Off

**Duration:** 16 minutes
**Type:** Hands-on — the most persuasive demo in Part II

### Learning objectives

Drive provider selection entirely from configuration, and run one agent across five engines without touching its code.

### The naive version

```php
protected function provider(): AIProviderInterface
{
    return new Anthropic(key: '...', model: '...');
}
```

Works, but every agent class now knows a vendor name. Ten agents, and switching providers is a ten-file change plus a code review.

### The factory

**`src/ProviderFactory.php`**

```php
<?php

declare(strict_types=1);

namespace App;

use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Providers\Anthropic\Anthropic;
use NeuronAI\Providers\Gemini\Gemini;
use NeuronAI\Providers\Mistral\Mistral;
use NeuronAI\Providers\Ollama\Ollama;
use NeuronAI\Providers\OpenAI\OpenAI;

final class ProviderFactory
{
    public static function make(?string $driver = null): AIProviderInterface
    {
        $driver ??= env('NEURON_PROVIDER', 'ollama');

        return match ($driver) {
            'anthropic' => new Anthropic(
                key: self::require('ANTHROPIC_KEY'),
                model: env('ANTHROPIC_MODEL', 'claude-sonnet-4-5'),
            ),
            'openai' => new OpenAI(
                key: self::require('OPENAI_KEY'),
                model: env('OPENAI_MODEL', 'gpt-4.1-mini'),
            ),
            'gemini' => new Gemini(
                key: self::require('GEMINI_KEY'),
                model: env('GEMINI_MODEL', 'gemini-2.0-flash'),
            ),
            'mistral' => new Mistral(
                key: self::require('MISTRAL_KEY'),
                model: env('MISTRAL_MODEL', 'mistral-large-latest'),
            ),
            'ollama' => new Ollama(
                url: env('OLLAMA_URL', 'http://localhost:11434/api'),
                model: env('OLLAMA_MODEL', 'qwen2.5:7b'),
            ),
            default => throw new \InvalidArgumentException("Unknown provider: {$driver}"),
        };
    }

    private static function require(string $key): string
    {
        return env($key) ?? throw new \RuntimeException("Missing environment variable: {$key}");
    }
}
```

> **Verify the Mistral import.** One page of the official documentation shows `use NeuronAI\Providers\Gemini\Mistral;`, which is a copy-paste artefact. The correct namespace follows the pattern of the others. Check your `vendor/` directory before recording — this is exactly the kind of detail students will hit and blame themselves for.

### Using it

```php
protected function provider(): AIProviderInterface
{
    return ProviderFactory::make();
}
```

Every agent in the project now says the same thing: "give me the configured provider". Vendor names appear in exactly one file.

### The demo to record

```bash
NEURON_PROVIDER=ollama    php examples/01-first-agent.php "What is a generator in PHP?"
NEURON_PROVIDER=anthropic php examples/01-first-agent.php "What is a generator in PHP?"
NEURON_PROVIDER=openai    php examples/01-first-agent.php "What is a generator in PHP?"
NEURON_PROVIDER=gemini    php examples/01-first-agent.php "What is a generator in PHP?"
```

Same code. Four engines. Time each one on screen — the local-versus-cloud latency gap is the detail students remember.

### Why this is worth a full lesson

Three arguments, in increasing order of business weight:

**Free development.** Ollama on a laptop costs nothing. Students complete every lab in Parts II, III and IV without a credit card, which is the difference between finishing a course and abandoning it at module 6.

**Cost tiering.** Lesson 1.4 gave you three levers, and the third was "cheaper model per step". A small local model for classification and routing; a frontier model only for final synthesis. Here that is a per-call argument, not an architecture change.

**Vendor and jurisdiction risk.** Prices change, terms change, providers have outages, and some clients cannot send data outside a specific jurisdiction — or outside their own building. With a hard SDK dependency each of those is a project. Here each is a config value.

### Exercise

Extend `01-first-agent.php` to loop over every configured provider, run the same prompt, and print a table: provider, elapsed time, response length. Keep it — you will extend it with token counts in Module 10.

### Key takeaways

- One factory; vendor names live in exactly one file.
- Ollama makes the whole course free to follow.
- Provider choice becomes cost strategy, risk management and data-residency compliance.

---
═══════════════════════════════════════════════════════════════

## LESSON 3.7 — Secrets and Environment

**Duration:** 11 minutes
**Type:** Hands-on

### Learning objectives

Load configuration safely and avoid the leaked-key incident that catches a genuinely large number of developers building their first AI project.

### bootstrap.php

**`bootstrap.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

$dotenv = Dotenv\Dotenv::createImmutable(__DIR__);
$dotenv->safeLoad();

function env(string $key, ?string $default = null): ?string
{
    $value = $_ENV[$key] ?? $_SERVER[$key] ?? getenv($key);

    return ($value === false || $value === '') ? $default : (string) $value;
}
```

`safeLoad()` rather than `load()`: it does not throw when the file is absent, which is what you want on a server where variables come from the environment itself rather than a file.

The `env()` helper checks `$_ENV`, then `$_SERVER`, then `getenv()`, and treats an empty string as absent — so a variable present but blank falls back to the default instead of producing a confusing failure three layers down.

### .env.example — committed

```dotenv
# anthropic | openai | gemini | mistral | ollama
NEURON_PROVIDER=ollama

ANTHROPIC_KEY=
ANTHROPIC_MODEL=claude-sonnet-4-5

OPENAI_KEY=
OPENAI_MODEL=gpt-4.1-mini

GEMINI_KEY=
GEMINI_MODEL=gemini-2.0-flash

MISTRAL_KEY=
MISTRAL_MODEL=mistral-large-latest

# Local models: no cost, ideal for the labs
OLLAMA_URL=http://localhost:11434/api
OLLAMA_MODEL=qwen2.5:7b

# Optional: tracing via inspector.dev
INSPECTOR_INGESTION_KEY=
```

```bash
cp .env.example .env
```

`.env.example` documents the structure and is committed. `.env` holds the values and never is.

### The leaked-key problem, stated plainly

AI provider keys are more dangerous than most credentials because they are directly monetisable. Automated scrapers watch public commits, and a key pushed to a public repository is typically exploited within minutes to hours, billed to you at frontier-model rates until you notice.

Four defences, all cheap:

1. **`.env` in `.gitignore` before the file exists.** Not after.
2. **A secret scanner in CI.** `gitleaks` or `trufflehog`, a few lines of workflow config.
3. **Spend limits at the provider.** Every major provider offers a hard monthly cap. Set it. It converts a catastrophe into an inconvenience.
4. **Separate keys per environment.** Dev, staging, production — so revoking one does not take down the others.

If you do leak a key: revoke it at the provider first, then clean history. In that order. Rewriting Git history on a key that is still live accomplishes nothing.

### Never log the prompt blindly

A detail specific to AI applications. Your prompts will contain whatever the user typed, which in a support application means names, addresses, order numbers, occasionally payment details. Logging full prompts for debugging is enormously tempting and creates a compliance problem the moment you do it at scale.

Log token counts, model, latency, tool names, and a request ID. Log prompt *content* only behind an explicit flag, with retention, and never in production by default. We return to this in Module 23.

### Model names go stale

Every model string in this file will be wrong eventually. Check the provider's current model list rather than trusting a course recorded months ago — including this one. Put that sentence on screen.

### Key takeaways

- `safeLoad()` plus a defensive `env()` helper.
- `.env.example` committed, `.env` never.
- Set a hard spend limit at the provider today.
- Revoke before rewriting history.
- Never log full prompts by default.

---
═══════════════════════════════════════════════════════════════
# MODULE 4 — MESSAGES AND MEMORY
═══════════════════════════════════════════════════════════════
---

## LESSON 4.1 — The Message Model

**Duration:** 15 minutes
**Type:** Theory with code

### Learning objectives

Understand Neuron's unified message layer — roles, content blocks, metadata — and why it is the piece that makes provider swapping actually work.

### Why a unified message layer exists

Every provider has its own request and response shape. OpenAI, Anthropic, Gemini and Ollama differ in how they represent roles, how they attach images, how they return tool calls, how they surface reasoning traces.

Neuron's answer is a single message abstraction that maps onto all of them. This is what makes Lesson 3.6 more than a party trick: the swap works because the message layer absorbs the differences. Without it, "change one line to change provider" would be false the moment you attached an image or read a tool call.

### What a message is

Three parts:

- **Role** — who is speaking: user, assistant, tool
- **Content blocks** — the actual payload
- **Metadata** — additional information from the provider response

### Content blocks

This is the part most people miss. A message does not hold a string. It holds an ordered **list of content blocks**, each implementing a `ContentBlock` interface. Neuron provides block types for text, reasoning, image, file, audio and video, and maps each one into the correct provider-specific format automatically.

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

Neuron captures the model's reasoning steps as a distinct block automatically. If you only ever call `getContent()`, you never see them. For debugging an agent that made a strange decision, the reasoning block is often the answer.

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

The last message in the array is treated as the most recent. This is the escape hatch for any situation where Neuron's own history component is not where your conversation lives — a legacy schema, another system's export, a reconstructed session.

### Multimodal preview

Attaching a document uses the same mechanism — another content block:

```php
use NeuronAI\Chat\Messages\ContentBlocks\FileContent;

$message = new UserMessage('Summarize this document');

$message->addContent(
    new FileContent(
        source: base64_encode(file_get_contents(__DIR__ . '/invoice.pdf')),
        sourceType: SourceType::BASE64,
        mediaType: 'application/pdf',
    )
);
```

`SourceType` supports `BASE64`, `URL` and `ID`. That third one matters for cost: many providers let you upload a file once to their platform and then reference it by ID, which avoids re-uploading the payload on every iteration of the agent loop. Given the token arithmetic from Lesson 1.4, that is a substantial saving on any multi-step run involving a document. Module 8 covers this properly.

> **v3 change.** Earlier versions used `addAttachment(new Image($url, ...))`. v3 replaced it with the content-block system. Older tutorials show the old call.

### Key takeaways

- A message is role + content blocks + metadata; not a string.
- `getContent()` concatenates text blocks; `getContentBlocks()` gives you everything, including reasoning.
- Pass an array of `Message` objects to seed an existing conversation.
- The unified message layer is why provider swapping survives contact with images, files and tool calls.

---
═══════════════════════════════════════════════════════════════

## LESSON 4.2 — The Model Has No Memory

**Duration:** 12 minutes
**Type:** Theory

### Learning objectives

Internalise statelessness as a design constraint, and understand what "memory" is actually implemented as.

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

The obvious reading — "the agent learned my name" — is wrong, and correcting it is the point of this lesson.

### What actually happened

The second call sent this to the provider:

```
system:    <instructions>
user:      Hi, my name is Valerio!
assistant: Hi Valerio, nice to meet you...
user:      Do you remember my name?
```

The model did not remember. **Your process re-sent the transcript.** There is no session on the provider side, no user record, nothing persisted between requests. The model reads the whole conversation fresh, every time, and answers as if it remembers.

The Neuron component that keeps the transcript and re-sends it is `ChatHistory`. That is the entirety of what "memory" means at this layer.

### Four consequences worth stating

**1. Memory costs money on every turn.**
Turn twenty re-sends nineteen previous exchanges. This is the mechanism behind the cost table in Lesson 1.4, and it is why long conversations get expensive even when the individual messages are short.

**2. Memory is bounded by the context window.**
It is not a database that grows. It is a buffer with a hard ceiling. Something must be discarded eventually, and the only question is what and how — Lesson 4.4.

**3. Memory is entirely under your control.**
Which is liberating once you accept it. You can edit history, inject a summary, drop irrelevant turns, keep a system-level fact permanently pinned. Nothing is sacred; it is your array.

**4. Statelessness is why horizontal scaling is easy.**
Any web server can serve any request, as long as it can load the transcript. There is no session affinity to a provider. Load a `ChatHistory` from shared storage and any node can continue any conversation. This is a genuine architectural advantage and worth pointing out — it is unusual for a stateful-feeling feature to scale this cleanly.

### The mental model to leave students with

The model is a **pure function**: transcript in, next message out. Everything that feels like memory, personality persistence or learning is your code choosing what goes into the transcript.

Every technique in the rest of this course — history trimming, summarisation, RAG, long-term memory stores — is a different answer to one question: **what do we put in the transcript?**

### Key takeaways

- No server-side session; the transcript is re-sent every turn.
- Memory costs tokens on every turn and is capped by the context window.
- History is your array — editable, injectable, replaceable.
- The model is a pure function of the transcript.

---
═══════════════════════════════════════════════════════════════

## LESSON 4.3 — ChatHistory Implementations

**Duration:** 16 minutes
**Type:** Hands-on

### Learning objectives

Choose and configure the right history backend, and build a persistent CLI chat.

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

Covered fully in Module 18, listed here so the map is complete:

```php
new EloquentChatHistory(
    thread_id: 'THREAD_ID',
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

### Lab: a persistent CLI chat

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

    public function instructions(): string
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
            contextWindow: 120_000,
        );
    }
}
```

Note `parent::__construct()`. Forget it and the base class never initialises — a silent, confusing failure. Note also that because this agent takes a constructor argument, we instantiate it with `new`, not `::make()`.

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

Tell it something. Quit. Reopen the terminal. Run the same command again and ask it what you said. **That** is the demo — the transcript came off disk and was re-sent, exactly as Lesson 4.2 described.

> The `/reset` implementation uses a glob because the exact filename produced by `FileChatHistory` is an implementation detail. Check what lands in `storage/chat/` on your version and tighten the pattern before you record.

### Key takeaways

- Four backends: InMemory, File, SQL, Eloquent.
- In a web request, in-memory means no memory between requests.
- `SQLChatHistory` takes a plain PDO and works in any framework.
- Custom constructor means `new`, not `::make()`, and remember `parent::__construct()`.

---
═══════════════════════════════════════════════════════════════

## LESSON 4.4 — Context Window and Trimming

**Duration:** 14 minutes
**Type:** Theory with configuration

### Learning objectives

Configure the trimmer correctly and understand the failure it prevents.

### The bug this prevents

The most common production failure in conversational AI:

> "It works fine, then after about thirty messages it starts throwing errors."

The transcript grew past the model's context limit. The provider rejects the request — it does not truncate for you, it returns an error.

Neuron's `ChatHistory` prevents this by trimming automatically. It tracks token usage from the provider responses and, when the transcript approaches the configured limit, removes messages from the beginning.

### The 5–10 % rule

From the documentation, and worth quoting to students because it is precise and easy to get wrong:

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

This is the mistake to warn against explicitly. If your provider is configurable (Lesson 3.6) then your context limit is too. A value hardcoded for a 200K model becomes wrong the moment someone sets `NEURON_PROVIDER=ollama` and gets a 32K local model.

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

**Summarise instead of dropping.** Neuron ships a summarisation middleware: rather than deleting the oldest turns, compress them into a short summary message that stays in context. Higher fidelity, at the cost of an extra LLM call. Covered with the other middleware in Module 15.

**Move durable facts out of the transcript entirely.** Long-term memory — Lesson 4.5.

### Key takeaways

- Configure 5–10 % under the model's real limit; the trimmer needs headroom.
- Derive the value from the provider, never hardcode it project-wide.
- Trimming drops the oldest messages — durable constraints belong in the system prompt.
- Summarisation preserves more context at the cost of one extra call.

---
═══════════════════════════════════════════════════════════════

## LESSON 4.5 — Session Memory vs Long-Term Memory

**Duration:** 12 minutes
**Type:** Theory

### Learning objectives

Distinguish three different things that all get called "memory", and pick the right one for a given requirement.

### Three mechanisms

**1. Session memory — `ChatHistory`.**
The current conversation. Bounded by the context window, trimmed automatically, scoped to one thread. Answers: "what did we just say?"

**2. Long-term memory — an external fact store.**
Durable facts about a user or entity that persist across conversations. Not bounded by the context window because it is not in the transcript — the agent retrieves from it on demand, through a tool. Answers: "what do I know about this person?"

**3. Knowledge — RAG.**
Your documents, indexed and retrieved by semantic similarity. Not about the user at all; about your domain. Answers: "what does our documentation say?"

The three are constantly conflated in product conversations, and the confusion produces bad architecture. "The bot should remember the customer's preferences" is mechanism 2. "The bot should answer from our manual" is mechanism 3. Building the first with the third — indexing conversations into a vector store — is a design error that produces vague, unreliable recall.

### Long-term memory in Neuron

Neuron ships a toolkit for Zep, a knowledge-graph service designed for exactly this:

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

None of this is a reason to avoid the pattern. It is a reason to design it deliberately rather than discovering it in an audit. Module 23 returns to this.

### Module 4 assessment

For an application you actually work on, list five things it would need to "remember". Classify each into one of the five rows of the decision table above, and justify the ones that were not obvious.

### Key takeaways

- Three distinct mechanisms: session memory, long-term memory, knowledge retrieval.
- Long-term memory is a **toolkit** — consulted deliberately, not injected automatically.
- Countable facts come from the database, never from a vector store.
- Storing derived personal facts is a privacy decision, not just a technical one.

---

**END OF MODULES 3–4**

*Next: Module 5 — Tools. The longest and most important module in the course.*
