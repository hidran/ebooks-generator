# Chapter 9 — MCP: The Model Context Protocol

::: {.callout .callout-tip}
[Code for this chapter]{.callout-title}

The runnable version of every listing below is at [`chapters/Ch09`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch09), in the companion repository. Clone it, run `composer install`, and the examples work against a local Ollama with no API key.
:::

## 9.1 What MCP Is and Why It Matters

### The definition

MCP is an open standard, designed by Anthropic, for connecting agents to external service providers — your application database, external APIs, third-party platforms.

Practically: it lets a server expose a set of tools over a defined protocol, and any MCP-capable client can consume them.

### The problem it solves

Before MCP, every integration was bespoke. Want your agent to use Slack? Read the Slack API docs, write the tool classes, handle the auth, maintain it. Then do the same for Jira. Then GitHub. Then your CRM. And every other framework in every other language does the same work again.

MCP inverts this. The **provider** publishes one server. Every client — NeuronAI, LangChain, a desktop assistant, an IDE — consumes it.

For you as an integrator, the change is: *"two days of work per integration"* becomes *"one line of configuration, if a server exists."*

### In NeuronAI

```php
use NeuronAI\MCP\McpConnector;

class MyAgent extends Agent
{
    protected function tools(): array
    {
        return [
            ...McpConnector::make([
                'command' => 'php',
                'args' => ['/home/code/mcp_server.php'],
            ])->tools(),
        ];
    }
}
```

Three details worth pausing on:

**The spread operator.** `...McpConnector::make(...)->tools()` — `tools()` returns an array, and the spread merges it into your list. Forget the `...` and you nest an array inside the tools array, which fails in a way that is not obvious from the error.

**One connector per server.** Create a separate `McpConnector` instance for each server you connect to.

**Discovery is automatic.** NeuronAI discovers the tools the server exposes. You do not enumerate them. When the agent decides to run one, NeuronAI generates the appropriate request, calls it on the server, and returns the result to the model.

The framework's own summary: *it feels exactly like your own defined tools, but you can access a huge archive of predefined actions with one line of code.*

### Where to find servers

- MCP official GitHub: `github.com/modelcontextprotocol/servers`
- MCP-GET registry: `mcp-get.com`

### The honest assessment

**What MCP genuinely gives you:** an enormous catalogue of integrations you did not write, an ecosystem that grows without your involvement, and a standard that is being adopted broadly rather than by one vendor.

**What it costs you:** every one of Section 5.1's guarantees. You did not write those tools. You did not review them. You do not control their descriptions, their behaviour, their error handling, or what they do with the arguments the model sends. Section 9.4 takes this seriously.

The balanced position: MCP is excellent for connecting to services you already trust, and requires real diligence for anything else.

### Key takeaways

- An open standard: servers expose tools, any client consumes them.
- One line of configuration replaces a bespoke integration.
- Spread the result; one connector per server; discovery is automatic.
- You inherit code you did not write — which is the whole point and the whole risk.

## 9.2 Local Servers

### Command-style configuration

For a server installed locally on your machine or VM:

```php
use NeuronAI\MCP\McpConnector;

class MyAgent extends Agent
{
    protected function tools(): array
    {
        return [
            ...McpConnector::make([
                'command' => 'php',
                'args' => ['/home/code/mcp_server.php'],
            ])->tools(),
        ];
    }
}
```

NeuronAI starts the process and communicates with it over standard input and output.

::: {.callout .callout-warning}
[If your interpreter path contains a space]{.callout-title}

`StdioTransport::connect()` escapes the *arguments* it appends but not the *command* itself:

```php
$commandLine = $command;
foreach ($args as $arg) {
    $commandLine .= ' ' . escapeshellarg((string) $arg);
}
```

So any interpreter path with a space in it gets split by the shell and the child process dies immediately. What you see is `McpException: MCP server process has terminated unexpectedly.` — which points at the server, not at the quoting.

This is the default on macOS with Laravel Herd, whose PHP lives under `~/Library/Application Support/…`. Escape it yourself:

```php
'command' => escapeshellarg(PHP_BINARY),
```

Confirmed against 3.16.4.
:::

### The Node ecosystem

Most published servers are Node packages, run with `npx`:

```php
...McpConnector::make([
    'command' => 'npx',
    'args' => ['-y', '@modelcontextprotocol/server-everything'],
])->tools(),
```

`server-everything` is the reference implementation and the right thing to experiment with — it exposes examples of every MCP feature and is the fastest way to see discovery working.

::: {.callout .callout-warning}
[Prerequisite]{.callout-title}

This requires Node on the machine running the agent. A PHP developer with no Node installed will hit a confusing failure and reasonably assume the framework is broken. Install it before working through this section.
:::

### The process model, and its consequences

The server is a **child process** of your PHP process. Three things follow:

**Startup cost per run.** Each execution spawns the process, waits for discovery, then works. In a CLI script that is fine. In a web request it is latency on every request.

**It inherits your environment.** File system access, environment variables, network. A local MCP server runs with your process's privileges. Treat it exactly as you would treat any dependency you `exec()`.

**It is not for a typical web deployment.** Spawning `npx` per HTTP request is not a production pattern. For web applications, use remote servers (Section 9.3), or run agent work on a queue worker where process startup is amortised over a longer job.

### The genuinely interesting case: your own server

You can write an MCP server in PHP:

```php
...McpConnector::make([
    'command' => 'php',
    'args' => ['/home/code/mcp_server.php'],
])->tools(),
```

Why would you? Because it turns your application's capabilities into something **any** agent can consume — your NeuronAI agent, a colleague's Python agent, an IDE assistant, a desktop client.

Instead of building tools for one agent, you publish a capability surface once. For a company with a valuable internal system, that is a strategic move rather than an implementation detail.

### Key takeaways

- `command` + `args` for local servers; communication over stdio.
- Most servers are Node packages — Node is a prerequisite.
- The server is a child process: startup cost, inherited privileges, unsuitable for per-request web use.
- Writing your own server exposes your system to every agent ecosystem at once.

## 9.3 Remote Servers

### Streamable HTTP

The normal case for hosted servers:

```php
use NeuronAI\MCP\McpConnector;

class MyAgent extends Agent
{
    protected function tools(): array
    {
        return [
            ...McpConnector::make([
                'url' => 'https://mcp.example.com',
                'token' => 'BEARER_TOKEN',
                'timeout' => 30,
                'headers' => [
                    //'x-cutom-header' => 'value'
                ]
            ])->tools(),
        ];
    }
}
```

Four keys:

- **`url`** — the server endpoint
- **`token`** — used as the authorization bearer token
- **`timeout`** — seconds; set it deliberately (see below)
- **`headers`** — anything else the server requires

### SSE transport

Set `async => true`:

```php
...McpConnector::make([
    'url' => 'https://mcp.example.com',
    'token' => 'BEARER_TOKEN',
    'timeout' => 30,
    'async' => true
])->tools(),
```

Server-Sent Events keeps a single long-lived HTTP connection over which the server pushes updates.

**Which to use:** whichever the server documents. This is not your choice — it is a property of the server you are connecting to.

### Set the timeout deliberately

The default may be generous. Recall Section 1.4's latency arithmetic: a multi-step agent making several MCP calls compounds every timeout.

If a server routinely takes 25 seconds, either it is unsuitable for interactive use, or your agent belongs on a queue. Do not discover this in production. Measure it during integration and decide.

### Handle the token like a credential

`'token' => 'BEARER_TOKEN'` in the documentation is a placeholder. In real code:

```php
...McpConnector::make([
    'url'     => env('CRM_MCP_URL'),
    'token'   => env('CRM_MCP_TOKEN'),
    'timeout' => 15,
])->tools(),
```

Everything from Section 3.7 applies. This is a credential to a system that can probably read or modify business data.

### Discovery happens at construction

An operational detail that surprises people: **`tools()` connects to the server.**

That means:

- Building the agent requires the server to be reachable
- A slow server slows agent construction, before any model call
- A server that is down means your agent cannot be constructed at all

If your `tools()` method connects to three remote MCP servers, you have three points of failure between a user's request and the first token of the response. Plan for it: catch failures at construction, degrade to a reduced tool set, and monitor server availability as part of your own uptime rather than someone else's.

### Key takeaways

- `url` + `token` + `timeout` + `headers` for streamable HTTP; add `async => true` for SSE.
- Transport is the server's choice, not yours.
- Discovery happens when you build the agent — remote servers are availability dependencies.
- Treat tokens as credentials; set timeouts explicitly.

## 9.4 Filtering and Security

### Filtering by tool name

```php
class MyAgent extends Agent
{
    protected function tools()
    {
        return [
            // EXCLUDE: discard certain tools
            ...McpConnector::make([
                'url' => 'https://mcp.example.com',
            ])->exclude([
                'tool_name_1',
                'tool_name_2',
            ])->tools(),

            // ONLY: select the tools you want to include
            ...McpConnector::make([
                'url' => 'https://mcp.example.com',
            ])->only([
                'tool_name_1',
                'tool_name_2',
            ])->tools(),
        ];
    }
}
```

**Important difference from Section 5.8.** Toolkit filters take fully qualified **class names**. MCP filters take **tool name strings**, because the tools are defined remotely and have no PHP classes on your side.

This has a consequence worth stating: there is no static analysis, no IDE completion, and no compile-time error if a name changes. A typo in an `only()` list silently yields fewer tools than you expected. Log the resulting tool count during development.

### Use `only()`. Always.

Section 5.8 argued that allowlists beat denylists because toolkits gain tools in framework releases. With MCP the argument is far stronger:

**The server can add tools at any time, without your knowledge, without a deployment on your side.**

You wrote `exclude(['delete_everything'])`. Next month the maintainer adds `purge_all`. Your agent now has it. You did not update a dependency, you did not deploy, you did not review a changelog. The capability arrived over the network.

`only()` is the only defensible option for any MCP server you do not control. This is one of the few places in this book where there is a genuinely right answer.

### The trust question, stated properly

Every argument from Section 5.1 about the tool list being your security boundary assumed you wrote the tools. With MCP you did not.

What you are extending trust to:

- **Tool descriptions you did not write.** And descriptions are instructions the model reads. A malicious or careless description is a prompt injection vector with a legitimate-looking delivery mechanism.
- **Behaviour you cannot inspect.** The tool says it reads a calendar. You cannot verify that is all it does.
- **A dependency that changes without a version bump.** Composer gives you a lock file. An MCP server gives you whatever it is running today.
- **Wherever your arguments go.** If the model passes customer data to a remote tool, that data has left your infrastructure. That is a GDPR question, not a technical preference.

### A workable policy

**Tier 1 — Servers you run.** Your own MCP server, on your infrastructure. Same trust as your own code. Use freely.

**Tier 2 — Servers from vendors you already trust.** Your CRM's official server, where you already have a contract, a DPA and a support channel. Use with `only()`.

**Tier 3 — Everything else.** Community servers, random registry entries, anything unmaintained. Treat as untrusted code. For production: read the source, pin a version, run it yourself rather than connecting to a hosted instance, and combine `only()` with tool approval for anything with side effects.

Prototyping is different — Tier 3 is fine for a spike. The distinction is between "trying it" and "shipping it".

### Layer the defences

MCP tools are still tools, so everything from Chapter 5 applies:

```php
protected function tools(): array
{
    return [
        ...McpConnector::make([
            'url'   => env('CRM_MCP_URL'),
            'token' => env('CRM_MCP_TOKEN'),
        ])->only([
            'search_contacts',
            'get_contact',
        ])->tools(),
    ];
}
```

Read-only tool names in the allowlist. Add `ToolApproval` middleware (Chapter 15) for anything that writes. And for a truly sensitive integration, consider proxying: wrap the MCP server in your own PHP tool that validates arguments before forwarding, so you have a place to enforce your own rules.

### Key takeaways

- MCP filters take tool name strings, not class names — no static analysis, so log the tool count.
- `only()` is mandatory for any server you do not control; servers gain tools without your deployment.
- You are trusting descriptions you did not write — a prompt-injection surface.
- Three trust tiers; be explicit about which one you are in.

## Chapter Exercises

1. **Discover.** Connect to `server-everything` and log which tools are discovered. Note how long construction takes — that is latency you would pay on every request in a web context.

2. **Restrict.** Narrow it with `only()` to two tools, and verify the agent cannot use a third. Then introduce a typo into the allowlist and confirm that nothing warns you — that silence is the reason Section 9.4 asks you to log the count.

3. **Classify.** For an integration you would actually build, place the server in a trust tier and write down what you would require before shipping it. If the answer is "nothing", check that against the four bullets in the trust section.
