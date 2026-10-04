# Agentic AI in PHP with Neuron
## PART II — PLAIN PHP + COMPOSER
### Full lesson scripts — Modules 3 and 4

> Copy each lesson block (between the `═══` separators) into its own Google Doc.
> Target version: `neuron-core/neuron-ai` ^4.0.3 (the release these scripts were run against), PHP 8.5.

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
        "php": "^8.5"
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
composer require neuron-core/neuron-ai:^4.0.3 vlucas/phpdotenv
```

**`neuron-core/neuron-ai`** — the framework. It needs the `curl` extension and very little else: its only Composer dependency is the PSR-14 event-dispatcher interface.

**`vlucas/phpdotenv`** — reads a `.env` file into the environment. Laravel ships this; plain PHP does not. Without it you would hardcode API keys, which we are not going to do.

**PHP 8.5.** Neuron itself runs on PHP 8.1 or later, but this course's code is written and run on PHP 8.5, so check `php -v` before going further. Where an example uses an 8.5-only feature (the pipe operator `|>`, `clone()` with property overrides, `#[\NoDiscard]`) the lesson says so.

Notice what is missing: an HTTP client package. Neuron does not depend on Guzzle or any other: every provider, vector store and toolkit talks HTTP through the framework's own `CurlHttpClient`, which is why `ext-curl` is a hard requirement. When our own tools call external APIs in Module 5, they reuse that same client, so the project needs nothing more. Check the extension first:

```bash
php -m | grep -i curl
```

No output means no `curl`, and the first provider call fails.

> **When you want Guzzle anyway.** If your application already routes outbound HTTP through a Guzzle `HandlerStack` (retries, a corporate proxy, request logging), require `guzzlehttp/guzzle` yourself and hand Neuron's adapter, `NeuronAI\HttpClient\Guzzle\GuzzleHttpClient`, to any provider with `setHttpClient()`. The default needs none of this.

### Pin the version

```json
"require": {
    "php": "^8.5",
    "neuron-core/neuron-ai": "^4.0.3",
    "vlucas/phpdotenv": "^5.6"
}
```

**Commit `composer.lock` in the course repository.** This is not the usual library advice — it is deliberate. A student who follows this course six months from now must get the same API you recorded against. Without the lock file they get whatever `^4.0.3` resolves to that day, and if a minor release changed a signature, they get an error you never saw and cannot support.

### Verify

```bash
php -r "require 'vendor/autoload.php'; echo interface_exists(NeuronAI\Chat\History\MessageStoreInterface::class) ? 'OK' : 'FAIL';"
```

The interface it probes arrived with the 4.0 release, so `OK` means you have the API this course is written against and `FAIL` means an older package. Check with:

```bash
composer show neuron-core/neuron-ai | head -5
```

### A word about versions and the documentation

Sample code on the internet comes from several generations of Neuron, and code written for older versions fails in two different ways.

The oldest code uses namespaces that no longer exist (shown here as old forms, to be recognised and not copied):

| Old (v1 / v2) | Current (v3 and v4) |
|---|---|
| `NeuronAI\Agent` | `NeuronAI\Agent\Agent` |
| `NeuronAI\SystemPrompt` | `NeuronAI\Agent\SystemPrompt` |

and it fails at the `use` statement. More recent code is subtler: the imports resolve, and then a method does not exist or returns something different. The places you will hit this first are what `chat()` returns and how a run gets its thread ID (Lesson 3.4), how conversations are stored (Module 4), how a tool declares its name and description (Module 5), and how a workflow is started (Module 13).

Parts of the official documentation, several blog posts and most Medium articles still show older code. When you find sample code that does not match this course, check which version it targets before you assume something is broken. This is the single most common source of confusion for people arriving from tutorials.

### Key takeaways

- `composer require neuron-core/neuron-ai`, with `ext-curl`; Guzzle is optional. The course code runs on PHP 8.5.
- Pin the version and commit `composer.lock` in teaching repositories.
- Code written for older versions fails on its namespaces or on changed return types and signatures. Check the version before debugging.

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
| `make:agent` | Class extending `Agent` with `provider()`, `instructions()`, `tools()` and `middleware()` stubs | Module 3 |
| `make:tool` | Class extending `Tool` with `$name`/`$description` properties, `properties()` and `__invoke()` | Module 5 |
| `make:rag` | Class extending `RAG` | Module 12 |
| `make:workflow` | Class extending `Workflow` with a `nodes()` stub | Module 13 |
| `make:node` | Workflow node with an `__invoke(StartEvent, WorkflowState)` stub | Module 13 |
| `make:event` | Event class implementing `Event` | Module 13 |
| `make:middleware` | Class implementing `WorkflowMiddleware` with `before()` and `after()` | Module 15 |
| `make:evaluators` | Evaluator class for the `evaluation` runner (note the plural; the binary also has `evaluation` to run them) | Module 10 |

The generators write the file at the path implied by your PSR-4 mapping. `App\Agents\AssistantAgent` lands in `src/Agents/AssistantAgent.php` because of the mapping we set in Lesson 3.1. If it lands somewhere unexpected, your autoload block is wrong.

### The honest position on generators

They save typing and enforce naming. That is the whole benefit. Every class they produce is ordinary PHP you could type yourself in ninety seconds, and in this course we will frequently write them by hand — because a student who has only ever generated an agent does not really know what an agent is.

Read what they produce before you build on it. A generator writes a starting point, not a finished class: the generated agent returns an `Anthropic` provider that reads `$_ENV['ANTHROPIC_API_KEY']` and `$_ENV['ANTHROPIC_MODEL']`. The stub says `ANTHROPIC_API_KEY`, while this course's own listings use `ANTHROPIC_KEY`, so align one with the other before the first run. A generated tool is named after its class until you give it a real name and description.

Use them when you are productive. Do not use them as a substitute for understanding the shape of the class.

### Key takeaways

- The generators follow the framework's building blocks: agent, tool, RAG, workflow, node, event, middleware, evaluators.
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

    protected function instructions(): string
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

> **Signature note.** The base class declares `protected function instructions(): SystemMessage|string`. Returning a plain `string`, as this class does, is a legal narrowing of that return type, and it is what the framework's own generator writes; Lesson 3.5 shows when you would return a `SystemMessage` instead. Some documentation examples declare the method `public`. PHP accepts that too, since an override may widen visibility, but keep it `protected` as the base class does and stay consistent across your project.

### Running it

**`examples/01-first-agent.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\AssistantAgent;
use NeuronAI\Chat\Messages\UserMessage;

$prompt = $argv[1] ?? 'Explain the difference between readonly and final in PHP 8, in three lines.';

// An agent always runs on a conversation thread, and the framework never
// invents one: without setThreadId() the call below throws an AgentException.
$state = AssistantAgent::make()
    ->setThreadId('demo')
    ->chat(new UserMessage($prompt));

echo $state->getMessage()?->getContent() . PHP_EOL;
```

```bash
php examples/01-first-agent.php "How do I implement a PSR-15 middleware without a framework?"
```

### Reading the chain, piece by piece

```php
AssistantAgent::make()
```
Static factory on the base class. Equivalent to `new AssistantAgent()`, and it reads better in a fluent chain. It forwards its arguments to the constructor, whose first is `workflowId:` — the same thread ID the next line sets, for when you know it at construction. Lab 2 in Module 4 passes it that way.

```php
->setThreadId('demo')
```
Says which conversation this run belongs to. Every agent run needs a thread ID, and Neuron never makes one up: leave this line out and `chat()` throws an `AgentException` before any request is sent. A single question has no conversation to come back to, so any fixed string will do here; Module 4 is where the thread starts to matter.

```php
->chat(new UserMessage($prompt))
```
Runs the loop from Lesson 1.2. One iteration here because there are no tools. `chat()` runs the agent's workflow to completion and returns its final **state**, an `AgentState`, not the message. The state is the whole outcome of the run: the provider's response, the messages this run produced, and, when a run pauses to wait for a human (Module 15), the reason it paused.

```php
$state->getMessage()
```
Reads the model's latest message off the state. Its return type is nullable (a run that stops before any inference has produced a response has no message), which is why the chain uses `?->`. A message is not proof of a finished run, though: when a run pauses for a tool approval (Lesson 5.10), `getMessage()` hands back the model's tool-call message, not an answer, and `$state->isInterrupted()` is what tells the two apart. The agent in this lesson never pauses, but the type does not know that, and neither does your static analyser.

> **Adapting older sample code.** `chat()` returns the `AgentState`. Tutorials written for older versions treat its result as the message itself, call `->run()` on it, or type-hint `AgentHandler`; none of that runs here. This is the second most common error when adapting older sample code, right after the namespaces.

```php
->getContent()
```
Returns all text content of the message joined into a single string. Lesson 4.1 explains why "joined" is the right word — a message can hold several content blocks.

### Two things that will go wrong

**Undefined array key "ANTHROPIC_KEY"** — the `.env` file is missing or not loaded. Lesson 3.7 builds `bootstrap.php` properly; for now, confirm the file exists and has the key.

**401 / authentication error** — the key is wrong, or you are billing-disabled on the provider. Check the provider console before you debug the code.

### Key takeaways

- Three template methods; the loop is inherited.
- `chat()` returns the run's final `AgentState`; `getMessage()` returns the message (or `null` when no inference produced one); `getContent()` returns the text.
- Every run needs a thread ID — `setThreadId()`, or `workflowId:` passed through `::make()` — and the framework never invents one. A paused run is detected with `isInterrupted()`, not with a null message.

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
protected function instructions(): string
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

Cast it to string with `(string)` and return it from `instructions()`. Each argument renders as its own headed section of the prompt. There is a fourth, optional one, `toolsUsage:`, for rules about when and how to call tools — useful once the agent has tools to call (Module 5).

### A real example

```php
protected function instructions(): string
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

### Strings are enough — until you want caching

Whatever `instructions()` returns, the agent stores it as a `SystemMessage`: a message whose content blocks are the system prompt. A string becomes one block. That is all this course's agents need, which is why they return strings. When you want the effective instructions back — in a test, or to log which prompt version ran — `$agent->getInstructions()` returns that `SystemMessage`, and `->getContent()` on it renders the text. (Older tutorials call `resolveInstructions()` for this; the method does not exist in v4.)

Return a `SystemMessage` yourself when you want more than one block, and the usual reason is prompt caching. A long, stable prompt is re-sent on every turn and every tool iteration; providers that support caching (Anthropic and the OpenAI Responses API, among Neuron's providers) bill a cached prefix at a fraction of the normal input price. Mark the stable block cached and keep the volatile part in a block of its own:

```php
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Chat\Messages\ContentBlocks\SystemContent;
use NeuronAI\Chat\Messages\SystemMessage;

protected function instructions(): SystemMessage
{
    return new SystemMessage([
        (new SystemContent((string) new SystemPrompt(
            background: ['You are a technical assistant specialised in PHP development.'],
        )))->cache(),
        new SystemContent('Today is ' . date('Y-m-d')),
    ]);
}
```

Providers without caching send the blocks as ordinary text, so the code stays portable. Below a provider's minimum cacheable size the marker is silently ignored, so the two-line prompt above caches nothing: the pattern pays on prompts measured in pages.

### Key takeaways

- Three sections: `background` (identity), `steps` (procedure), `output` (contract).
- One instruction per array item.
- "Look it up before answering" belongs in `steps` and is your best anti-hallucination tool.
- `instructions()` may return a string or a `SystemMessage`; use the latter to split the prompt into blocks and cache the stable one.
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
                // Ollama truncates a prompt to num_ctx instead of rejecting it,
                // and its default is small: ask for the window Lesson 4.4 budgets.
                parameters: ['options' => ['num_ctx' => 32_768]],
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

The `parameters:` argument on the Ollama branch is how any provider receives request options the factory does not model. Here it sets `num_ctx`, Ollama's context size. Left alone, Ollama does not reject a prompt that is too long: it truncates it, quietly, to a default far smaller than the model can handle. Lesson 4.4 returns to that number.

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

- **Role** — who is speaking: user, assistant, or system. The agent's instructions travel as a `SystemMessage`; a tool call is a specialised assistant message (`ToolCallMessage`) and its result a specialised user message (`ToolResultMessage`)
- **Content blocks** — the actual payload
- **Metadata** — additional information from the provider response, such as token usage

### Content blocks

This is the part most people miss. A message does not hold a string. It holds an ordered **list of content blocks**, each implementing `ContentBlockInterface`. Neuron provides block types for text, reasoning, image, file, audio and video — plus the system block that instructions are made of (Lesson 3.5) — and maps each one into the correct provider-specific format automatically.

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

Neuron captures the model's reasoning steps as a distinct block automatically, and `getContent()` deliberately leaves it out. If you only ever call `getContent()`, you never see them; `$response->getReasoning()` is the shortcut when you want just that block. For debugging an agent that made a strange decision, the reasoning block is often the answer.

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

The last message in the array is treated as the most recent. This is the escape hatch for any situation where Neuron's own history component is not where your conversation lives — a legacy schema, another system's export, a reconstructed session.

### Multimodal preview

Attaching a document uses the same mechanism — another content block:

```php
use NeuronAI\Chat\Enums\SourceType;
use NeuronAI\Chat\Messages\ContentBlocks\FileContent;

$message = new UserMessage('Summarize this document');

$message->addContent(
    new FileContent(
        content: base64_encode(file_get_contents(__DIR__ . '/invoice.pdf')),
        sourceType: SourceType::BASE64,
        mediaType: 'application/pdf',
    )
);
```

`SourceType` supports `BASE64`, `URL` and `ID`. That third one matters for cost: many providers let you upload a file once to their platform and then reference it by ID, which avoids re-uploading the payload on every iteration of the agent loop. Given the token arithmetic from Lesson 1.4, that is a substantial saving on any multi-step run involving a document. Module 8 covers this properly.

> **Attachments in older tutorials.** Tutorials written for older versions attach media with `addAttachment(new Image($url, ...))`. That call does not exist here; media is a content block, as above. Related: the documentation is inconsistent about block class names — `TextBlock`/`FileBlock` appear in some places where the shipped classes are `TextContent`/`FileContent`, the payload argument is `content:` (not `source:`) on every block, and one example imports `AudioContent` while instantiating `FileContent`.

### Key takeaways

- A message is role + content blocks + metadata; not a string.
- `getContent()` joins text blocks; `getContentBlocks()` gives you everything, including reasoning.
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

The Neuron component that re-sends the transcript is `ChatHistory`, and it reads it from a *message store* — here the default one, which lives in the memory of that one agent object. That is the entirety of what "memory" means at this layer.

### Four consequences worth stating

**1. Memory costs money on every turn.**
Turn twenty re-sends nineteen previous exchanges. This is the mechanism behind the cost table in Lesson 1.4, and it is why long conversations get expensive even when the individual messages are short.

**2. Memory is bounded by the context window.**
It is not a database that grows. It is a buffer with a hard ceiling. Something must be discarded eventually, and the only question is what and how — Lesson 4.4.

**3. Memory is entirely under your control.**
Which is liberating once you accept it. You can edit history, inject a summary, drop irrelevant turns, keep a system-level fact permanently pinned. Nothing is sacred; it is your array.

**4. Statelessness is why horizontal scaling is easy.**
Any web server can serve any request, as long as it can load the transcript. There is no session affinity to a provider. Keep the messages in shared storage and any node can continue any conversation. This is a genuine architectural advantage and worth pointing out — it is unusual for a stateful-feeling feature to scale this cleanly.

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

## LESSON 4.3 — ChatHistory and Message Stores

**Duration:** 16 minutes
**Type:** Hands-on

### Learning objectives

Choose and configure the right message store, bind the conversation to a thread, and build a persistent CLI chat.

### The interface

```php
NeuronAI\Chat\History\MessageStoreInterface
```

Session memory is two classes with two jobs. `ChatHistory` is concrete, and you never build it yourself: each time a run starts or resumes, the agent opens one for its thread, and that object loads the conversation, keeps it inside the context window and writes new messages through. Where the messages are kept is a **message store** — anything that implements the interface above — and that is the part you choose.

Choose it by implementing `messageStore()` on your agent, or by passing an instance to `setMessageStore()`; size the window with `contextWindow()` or `setContextWindow()` (Lesson 4.4). A setter, once called, wins over the method. The default, if you do none of this, is an in-memory store and a window of 50,000 tokens.

The history is a service the agent's nodes use, not part of the run's state: the transcript is never copied into the `AgentState` that `chat()` returns. That separation matters once runs become durable (Module 15): a paused run's saved state stays small no matter how long the conversation grows, and the conversation lives in exactly one place, the store.

> **History code in older tutorials.** Tutorials written for older versions build the history itself — an `InMemoryChatHistory`, a `FileChatHistory`, an `SQLChatHistory` — in a `chatHistory()` method on the agent. Those classes are gone, and the failure is silent: nothing calls a method named `chatHistory()`, so the agent loads, answers, and keeps the conversation in the default in-memory store. If a conversation does not survive a restart, look for that method first. (`setChatHistory()`, by contrast, fails loudly.)

### Which conversation? The thread ID

A history always belongs to one conversation — a **thread** — and something has to say which. In Neuron that something is the agent, not the store:

```php
$agent = SupportAgent::make(workflowId: $threadId);
```

A store has no thread of its own. Every method on the interface takes the thread ID as an argument, so one store serves every conversation, and the agent supplies the ID: it opens its history over the store *for its own thread*. Identity enters in one place, at the call site that actually knows which conversation this request is about.

It is the same ID Lesson 2.3 talked about: the thread ID is also the agent run's workflow ID, which is why the constructor argument is called `workflowId:`. `setThreadId()`, from Lesson 3.4, sets the same value after construction. (Older material passes it as `make(threadId: ...)`; that argument no longer exists and fails with "Unknown named parameter $threadId".)

Two rules follow, and both are enforced:

- **An agent without a thread refuses to work.** The framework never generates an ID. Call `chat()`, `getChatHistory()` or `resetConversation()` on an unbound agent and you get an `AgentException` — *"This agent has no thread ID: bind one with setThreadId() first."* — rather than a conversation quietly filed under a key nobody chose.
- **An agent is bound once.** Setting the same ID again is harmless; setting a different one throws. To serve another conversation, build another agent, or call `$agent->for($otherThreadId)`, which returns a copy bound to that thread.

An agent class with a constructor of its own must still call `parent::__construct()`: pass the thread ID to it, or bind the thread afterwards with `setThreadId()` or `for()`.

> **The thread ID is user input.** Whatever you pass as `workflowId:` selects which conversation is loaded, extended and resumed. If it arrives in a request — a URL segment, a form field — check that the current user owns that thread before you build the agent with it. The framework does no access control.

### InMemoryMessageStore

```php
use NeuronAI\Chat\History\InMemoryMessageStore;
use NeuronAI\Chat\History\MessageStoreInterface;

protected function messageStore(): MessageStoreInterface
{
    return new InMemoryMessageStore();
}
```

An array per thread, in process memory. It is the default, so the method above only spells out what an agent without a `messageStore()` already does. The store belongs to the agent object that created it: keep the object and the conversation continues, as in Lesson 4.2; build a second agent with the same thread ID and it starts empty, because it has a store of its own. Correct for: single-shot scripts, stateless API endpoints where you hold the conversation yourself, and tests.

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

Because each message is its own row — `role`, the content blocks as JSON in `content`, everything else (usage, tool calls, metadata) as JSON in `meta` — the table is useful to the rest of your application, not just to the agent: per-message reporting, retention jobs, a support dashboard that lists conversations. You can add columns — a foreign key to your users table, for instance — as long as they are nullable and the base structure stays. `archived_at` is explained in Lesson 4.4.

### EloquentMessageStore

Covered fully in Module 18, listed here so the map is complete:

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

### Lab: a persistent CLI chat

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

Notice what the class does *not* contain: a thread ID. There is no constructor, no `$threadId` property, no key passed to `FileMessageStore`. The class describes where conversations are stored; which conversation this run belongs to is decided by whoever builds the agent, through `make(workflowId: ...)`, exactly as described above. The same class serves every thread. (`ProviderFactory::contextWindow()` is added in Lesson 4.4.)

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

Tell it something. Quit. Reopen the terminal. Run the same command again and ask it what you said. **That** is the demo — the transcript came off disk and was re-sent, exactly as Lesson 4.2 described.

> `/reset` does not touch the filesystem. `resetConversation()` asks the agent to forget: it abandons any unfinished run on the thread and calls `flushAll()` on the history, which clears the thread in the store — for `FileMessageStore`, by deleting that thread's file, archived messages included, and nothing else. Deleting files by hand with a glob couples your code to a filename format that is the library's business. Look in `storage/chat/` before and after a reset to see it for yourself.

### Key takeaways

- One concrete `ChatHistory`, four message stores: InMemory, File, SQL, Eloquent.
- A store carries no thread. Give the agent `make(workflowId: ...)` or `setThreadId()`, and it opens the history for that thread; without one it refuses to run. The thread ID is also the run's workflow ID.
- Authorise the thread ID before using it: it selects whose conversation is loaded.
- In a web request, in-memory means no memory between requests.
- `SQLMessageStore` takes a plain PDO, stores one row per message and works in any framework.

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

The transcript grew past the model's context limit. A cloud provider rejects the request — it does not truncate for you, it returns an error. Ollama fails the other way: it truncates the prompt to its `num_ctx` and answers from what is left, with no error at all.

Neuron's `ChatHistory` prevents both by trimming automatically. It tracks token usage from the provider responses and, when the conversation no longer fits the configured window, takes messages off the beginning of what it sends to the model.

"Takes off what it sends" is deliberate wording. Trimming never deletes. The history asks its store to archive what it dropped, and every store does: an `archived_at` timestamp on the row (Lesson 4.3) or on the entry in the file, a counter in memory. The model sees the trimmed thread; `loadAll()` on the store still returns the full transcript, for auditing, analytics, a retention policy or a screen that pages back through the conversation. `flushAll()` is the one operation that really deletes a thread, archived messages included.

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
protected function contextWindow(): int
{
    return ProviderFactory::contextWindow();
}
```

The Ollama figure is the only one that depends on your own configuration. 29,000 assumes a 32K window, and a local model has one only if you ask for it: `parameters: ['options' => ['num_ctx' => 32_768]]` on the Ollama provider, as the factory in Lesson 3.6 does. Without it Ollama truncates at its own default, usually far smaller, long before the trimmer sees any reason to act. Change one number and you must change the other.

### What trimming costs you

Trimming takes the oldest messages out of the model's view. The user established a constraint in message three — "always answer in Spanish", "my account number is X" — and at message forty it is gone. The agent appears to develop amnesia mid-conversation, which reads to users as a bug even though it is working as designed.

Three mitigations, in increasing order of sophistication:

**Restate constants in the system prompt.** The system prompt is re-sent every turn and is not subject to trimming. Anything that must survive belongs there, not in the transcript.

**Summarise instead of dropping.** Neuron ships a summarisation middleware, `Summarization`, which you attach to the agent's inference nodes (Lesson 2.3): once the conversation passes a token budget, it replaces everything but the last few messages with a short summary message that stays in context. The model keeps more of the thread, at the cost of an extra LLM call — and of the transcript. The middleware rewrites the thread through `flushAll()`, so the original messages, archived ones included, are gone from the store; if you need that record, keep a copy of your own. Middleware is covered in Module 15.

**Move durable facts out of the transcript entirely.** Long-term memory — Lesson 4.5.

### Key takeaways

- Configure 5–10 % under the model's real limit; the trimmer needs headroom.
- Derive the value from the provider, never hardcode it project-wide. On Ollama, set `num_ctx` to match: it truncates silently instead of failing.
- Trimming hides the oldest messages from the model — durable constraints belong in the system prompt.
- Every store archives trimmed messages instead of deleting them; the full transcript stays in your storage.
- Summarisation preserves more context at the cost of one extra call — and of the stored transcript, which it replaces.

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

**2. Long-term memory — a store outside the transcript.**
What earlier conversations established about a user or entity, kept beyond any one thread. Not bounded by the context window because it is not in the transcript — only what is relevant to the current question is fetched back in. Answers: "what do I know about this person?"

**3. Knowledge — RAG.**
Your documents, indexed and retrieved by semantic similarity. Not about the user at all; about your domain. Answers: "what does our documentation say?"

The three are constantly conflated in product conversations, and the confusion produces bad architecture. "The bot should remember the customer's preferences" is mechanism 2. "The bot should answer from our manual" is mechanism 3. The two can share machinery — Neuron builds the second from the third's components — but never a store: index conversations into the same vector store as the manual and one customer's words come back as the answer to another customer's question.

### Long-term memory in Neuron

Neuron's conversation memory has two halves, both built from RAG components (Module 12) and each opt-in on its own. The writing half is a node. Return a `ConversationIngestionNode` from the agent's `exitNodes()` method, in place of the default ending, and every completed turn — the user's text and the model's final answer, never the tool calls — is stored as one document in a vector store, labelled with its thread ID. The node needs that store and an embeddings provider, injected here through the constructor:

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

The reading half is a retrieval strategy, `SemanticMemoryRetrieval`. Given the same store and a list of thread IDs, a RAG agent (Lesson 12.7) finds the past exchanges closest in meaning to the current question and adds them to the prompt as extra context.

Note carefully that this is **retrieval**, not a history component. That is the architectural statement: long-term memory is not a longer transcript re-sent on every turn. It is a search, and only what the search returns reaches the model.

The list of thread IDs partitions the store. It is an allowlist, and nothing is added to it for you, not even the current thread: pass exactly the threads this user is entitled to recall. Keep conversations in a vector store of their own, too. Only this strategy applies the allowlist; any other retrieval over the same store returns everyone's conversations.

Older material uses a toolkit for this job, `ZepLongTermMemoryToolkit`. It still ships, but it is deprecated and will be removed in the next major version. Do not build on it.

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

None of this is a reason to avoid the pattern. It is a reason to design it deliberately rather than discovering it in an audit. Module 23 returns to this.

### Module 4 assessment

For an application you actually work on, list five things it would need to "remember". Classify each into one of the five rows of the decision table above, and justify the ones that were not obvious.

### Key takeaways

- Three distinct mechanisms: session memory, long-term memory, knowledge retrieval.
- Long-term memory is **retrieval** over a conversation store of its own, scoped by an explicit list of thread IDs — searched per question, not re-sent every turn.
- Countable facts come from the database, never from a vector store.
- Storing what users said beyond the conversation is a privacy decision, not just a technical one.

---

**END OF MODULES 3–4**


*Next: Module 5 — Tools. The longest and most important module in the course.*
