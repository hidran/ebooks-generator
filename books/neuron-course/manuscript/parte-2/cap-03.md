# Chapter 3 — Setup and Your First Agent

::: {.callout .callout-tip}
[Code for this chapter]{.callout-title}

The runnable version of every listing below is at [`chapters/Ch03`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch03), in the companion repository. Clone it, run `composer install`, and the examples work against a local Ollama with no API key.
:::

## 3.1 Project Scaffolding

We are going to build a clean plain-PHP project that carries every example in Parts II, III and IV. No framework, no magic.

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

Two lines here are load-bearing. `/vendor/` because it is regenerable. `.env` because it will hold API keys, and a leaked key on a public repository is charged to you within hours. Section 3.7 covers this properly.

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
├── examples/            ← one runnable script per section
└── storage/chat/        ← persisted conversations
```

### Key takeaways

- Plain PHP first; the framework SDK adds convenience, not capability.
- PSR-4 maps `App\` → `src/`; verify with `composer dump-autoload` before writing code.
- `.env` is in `.gitignore` from minute one.

## 3.2 Installing NeuronAI

### The install

```bash
composer require neuron-core/neuron-ai vlucas/phpdotenv guzzlehttp/guzzle
```

**`neuron-core/neuron-ai`** — the framework. Requires PHP 8.1 or later.

**`vlucas/phpdotenv`** — reads a `.env` file into the environment. Laravel ships this; plain PHP does not. Without it you would hardcode API keys, which we are not going to do.

**`guzzlehttp/guzzle`** — an HTTP client. NeuronAI pulls in what it needs internally; we require it explicitly because our own tools will call external APIs in Chapter 5, and an explicit dependency is an honest dependency.

### Pin the version

```json
"require": {
    "php": "^8.1",
    "neuron-core/neuron-ai": "^3.0",
    "vlucas/phpdotenv": "^5.6",
    "guzzlehttp/guzzle": "^7.9"
}
```

**Commit `composer.lock` in a teaching repository.** This is not the usual library advice — it is deliberate. Someone who follows this book a year from now must get the same API it was written against. Without the lock file they get whatever `^3.0` resolves to that day, and if a minor release changed a signature, they get an error that nobody can help them with.

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

Parts of the official documentation, several blog posts and most third-party articles still show the v2 imports. When you find sample code whose `use` statements do not match this book, check which version it targets before you assume something is broken. This is the single most common source of confusion for people arriving from tutorials.

### Key takeaways

- `composer require neuron-core/neuron-ai`, PHP 8.1+.
- Pin the version and commit `composer.lock` in teaching repositories.
- v2 → v3 moved the namespaces; older tutorials will not compile against v3.

## 3.3 The Framework CLI

The generators create framework components with the correct structure. It is worth knowing what they produce, because you will also want to write these classes by hand.

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

That backslash difference causes more lost time than it has any right to. If a generator command appears to do nothing, count your backslashes first.

### What each one produces

| Command | Produces | Covered in |
|---|---|---|
| `make:agent` | Class extending `Agent` with `provider()` and `instructions()` stubs | Chapter 3 |
| `make:tool` | Class extending `Tool` with `properties()` and `__invoke()` stubs | Chapter 5 |
| `make:node` | Workflow node with an `__invoke(Event, WorkflowState)` stub | Chapter 13 |
| `make:event` | Event class implementing `Event` | Chapter 13 |

The generators write the file at the path implied by your PSR-4 mapping. `App\Agents\AssistantAgent` lands in `src/Agents/AssistantAgent.php` because of the mapping we set in Section 3.1. If it lands somewhere unexpected, your autoload block is wrong.

### The honest position on generators

They save typing and enforce naming. That is the whole benefit. Every class they produce is ordinary PHP you could type yourself in ninety seconds, and in this book we frequently write them by hand — because someone who has only ever generated an agent does not really know what an agent is.

Use them when you are productive. Do not use them as a substitute for understanding the shape of the class.

### Key takeaways

- Four generators: `make:agent`, `make:tool`, `make:node`, `make:event`.
- Unix needs doubled backslashes; PowerShell does not.
- Output path follows your PSR-4 mapping.

## 3.4 Your First Agent

This is the first running code in the book.

### The three template methods

An agent class answers three questions:

- `provider()` — which LLM do I talk to?
- `instructions()` — who am I and how do I behave?
- `tools()` — what can I actually do? *(optional; Chapter 5)*

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

::: {.callout .callout-warning}
[Visibility note]{.callout-title}

The official documentation shows `instructions()` as `public` in some examples and `protected` in others. Both appear in the current docs. Use whichever matches the base class in the version you install — check with your IDE or `composer show` — and stay consistent across your project. This is item 8 in Appendix A.
:::

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

Static factory on the base class. Equivalent to `new AssistantAgent()` for a no-argument constructor, and it reads better in a fluent chain. When your agent takes constructor arguments — as `PersistentAgent` will in Section 4.3 — use `new` instead.

```php
->chat(new UserMessage($prompt))
```

Runs the loop from Section 1.2. One iteration here because there are no tools. Note that `chat()` returns a **response object**, not the message.

```php
->getMessage()
```

Extracts the assistant message from the response.

::: {.callout .callout-warning}
[v2 → v3 change]{.callout-title}

In earlier versions `chat()` returned the message directly. In v3 you must call `getMessage()`. This is the second most common error when adapting older sample code, right after the namespaces.
:::

```php
$response->getContent()
```

Returns all text content of the message concatenated into a single string. Section 4.1 explains why "concatenated" is the right word — a message can hold several content blocks.

### Two things that will go wrong

**Undefined array key "ANTHROPIC_KEY"** — the `.env` file is missing or not loaded. Section 3.7 builds `bootstrap.php` properly; for now, confirm the file exists and has the key.

**401 / authentication error** — the key is wrong, or you are billing-disabled on the provider. Check the provider console before you debug the code.

### Key takeaways

- Three template methods; the loop is inherited.
- `chat()` returns a response; `getMessage()` returns the message; `getContent()` returns the text.
- `::make()` for simple agents, `new` when the constructor takes arguments.

## 3.5 SystemPrompt: Structuring Instructions

Instructions that models actually follow have a structure. NeuronAI gives you a three-part one, and the reason it exists is worth understanding before you use it.

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

### The NeuronAI structure

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

### The A/B comparison worth running yourself

Same agent, same question, two prompts.

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

Version A returns 600 words starting with "Great question!". Version B asks which framework, or answers tightly in plain PHP. The difference is immediate, and it lands harder than any explanation: **the system prompt is the specification, not the greeting.**

### Practical guidance

- One instruction per array item. If an item contains "and", consider splitting it.
- Prefer positive instructions. "Answer in English" beats "don't answer in Italian".
- Negatives that matter are worth keeping, but state the boundary, not a list of forbidden words.
- Version the prompt in Git and treat prompt changes as code changes — with review. Given Section 1.5, a reworded prompt is a behavioural change you cannot regression-test conventionally.

### Key takeaways

- Three sections: `background` (identity), `steps` (procedure), `output` (contract).
- One instruction per array item.
- "Look it up before answering" belongs in `steps` and is your best anti-hallucination tool.
- Prompt changes are code changes; review them.

## 3.6 Provider Swap: The Interface Pays Off

This is the most persuasive thing in Part II: one agent, five engines, no code change.

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

::: {.callout .callout-warning}
[Verify the Mistral import]{.callout-title}

One page of the official documentation shows `use NeuronAI\Providers\Gemini\Mistral;`, which is a copy-paste artefact. The correct namespace follows the pattern of the others. Check your `vendor/` directory — this is exactly the kind of detail you will hit and blame yourself for.
:::

### Using it

```php
protected function provider(): AIProviderInterface
{
    return ProviderFactory::make();
}
```

Every agent in the project now says the same thing: "give me the configured provider". Vendor names appear in exactly one file.

### The experiment

```bash
NEURON_PROVIDER=ollama    php examples/01-first-agent.php "What is a generator in PHP?"
NEURON_PROVIDER=anthropic php examples/01-first-agent.php "What is a generator in PHP?"
NEURON_PROVIDER=openai    php examples/01-first-agent.php "What is a generator in PHP?"
NEURON_PROVIDER=gemini    php examples/01-first-agent.php "What is a generator in PHP?"
```

Same code. Four engines. Time each one — the local-versus-cloud latency gap is the detail that will shape your design decisions later.

### Why this deserves a section of its own

Three arguments, in increasing order of business weight:

**Free development.** Ollama on a laptop costs nothing. You can complete every lab in Parts II, III and IV without a credit card, which is the difference between finishing a book like this and abandoning it at Chapter 6.

**Cost tiering.** Section 1.4 gave you three levers, and the third was "cheaper model per step". A small local model for classification and routing; a frontier model only for final synthesis. Here that is a per-call argument, not an architecture change.

**Vendor and jurisdiction risk.** Prices change, terms change, providers have outages, and some clients cannot send data outside a specific jurisdiction — or outside their own building. With a hard SDK dependency each of those is a project. Here each is a config value.

### Key takeaways

- One factory; vendor names live in exactly one file.
- Ollama makes everything in this book free to follow.
- Provider choice becomes cost strategy, risk management and data-residency compliance.

## 3.7 Secrets and Environment

Loading configuration safely, and avoiding the leaked-key incident that catches a genuinely large number of developers on their first AI project.

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

Log token counts, model, latency, tool names, and a request ID. Log prompt *content* only behind an explicit flag, with retention, and never in production by default. We return to this in Chapter 23.

### Model names go stale

Every model string in this chapter will be wrong eventually. Check the provider's current model list rather than trusting a book written months before you read it — including this one.

### Key takeaways

- `safeLoad()` plus a defensive `env()` helper.
- `.env.example` committed, `.env` never.
- Set a hard spend limit at the provider today.
- Revoke before rewriting history.
- Never log full prompts by default.

## Lab 1 — The Plain-PHP Foundation

Everything in Parts II to IV runs on the project you build here. Do not skip it; later labs assume this exact layout.

### What you are building

A Composer project with a provider factory, one working agent, and a benchmark script that runs the same prompt across every provider you have configured.

### Steps

1. **Scaffold** the directory structure and `composer.json` from Section 3.1. Run `composer dump-autoload` and confirm it reports no errors.
2. **Install** the three packages from Section 3.2. Verify with the `class_exists` one-liner; if it prints `FAIL`, stop and fix the version before continuing.
3. **Write `bootstrap.php`** and the `env()` helper from Section 3.7. Copy `.env.example` to `.env`.
4. **Write `src/ProviderFactory.php`** from Section 3.6.
5. **Write the agent.** Use the full three-section `SystemPrompt` rather than the minimal one from Section 3.4 — this is the version later chapters build on:

```php
<?php

declare(strict_types=1);

namespace App\Agents;

use App\ProviderFactory;
use NeuronAI\Agent\Agent;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Chat\History\ChatHistoryInterface;
use NeuronAI\Chat\History\InMemoryChatHistory;
use NeuronAI\Providers\AIProviderInterface;

class AssistantAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return ProviderFactory::make();
    }

    public function instructions(): string
    {
        return (string) new SystemPrompt(
            background: [
                'You are a technical assistant specialised in PHP development.',
                'You are talking to experienced developers: no unrequested basics.',
            ],
            steps: [
                'Analyse the question and identify the real problem, not only the stated one.',
                'If the question is ambiguous, ask the single most useful clarifying question.',
                'Answer with code when code is the answer.',
            ],
            output: [
                'Answer in English.',
                'Use fenced code blocks with the language declared.',
                'No preambles such as "Certainly!" or "Great question".',
            ],
        );
    }

    protected function chatHistory(): ChatHistoryInterface
    {
        // Roughly 90 % of the model's context window: the trimmer needs headroom.
        return new InMemoryChatHistory(contextWindow: 120_000);
    }
}
```

6. **Run it** with `examples/01-first-agent.php` from Section 3.4.
7. **Swap providers** using the environment variable, at minimum between Ollama and one cloud provider.

### The benchmark

Extend `01-first-agent.php` so that it loops over every provider that has credentials configured, runs the same prompt against each, and prints a table of provider, elapsed time and response length. Keep this script — in Chapter 10 you will add token counts from `$response->getUsage()` to it, and it becomes a genuinely useful tool for choosing a model.

### Acceptance criteria

- `composer dump-autoload` produces no warnings, and `App\Agents\AssistantAgent` resolves.
- The same prompt returns a sensible answer under at least two different `NEURON_PROVIDER` values, with no change to any PHP file.
- `.env` is untracked. Verify with `git status --ignored` rather than assuming.
- A missing API key produces your `RuntimeException` with a useful message, not a null-pointer failure deep inside the provider.

### If it does not work

The three failures that account for almost all first-run problems: a wrong PSR-4 mapping (class not found), a v2 namespace in a `use` statement (class not found, but a *framework* class), and a `.env` that was never copied from `.env.example` (missing key). Check them in that order.
