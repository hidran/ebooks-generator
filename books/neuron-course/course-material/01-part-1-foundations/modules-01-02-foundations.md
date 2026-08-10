# Agentic AI in PHP with Neuron
## PART I — FOUNDATIONS
### Full lesson scripts — Modules 1 and 2

> Copy each lesson block (between the `═══` separators) into its own Google Doc.

---
═══════════════════════════════════════════════════════════════
# MODULE 1 — WHAT "AGENTIC" ACTUALLY MEANS
═══════════════════════════════════════════════════════════════
---

## LESSON 1.1 — LLM, Chatbot, Workflow, Agent: The Autonomy Ladder

**Duration:** 12 minutes
**Type:** Theory, no code

### Learning objectives

By the end of this lesson you will be able to place any AI feature you are asked to build on a four-rung ladder, and explain to a client why the rung matters more than the model.

### The problem with the word "agent"

In 2023 everything was a "chatbot". By 2025 everything is an "agent". The word has been stretched so far that it now means "software that calls an LLM", which is useless as a design category. Before we write a line of PHP we need a definition sharp enough to make architectural decisions with.

The useful distinction is not *what the software does*. It is **who decides what happens next**.

### The four rungs

**Rung 1 — The bare LLM call.**
You send text, you get text back. Your code decides everything: what to send, when to send it, what to do with the answer. The model has zero control over program flow.

```
Your code → prompt → model → text → your code
```

Example: "summarise this support ticket in one sentence". There is one input, one output, one path. Ninety per cent of the AI features shipped in real products are this, and that is fine.

**Rung 2 — The chatbot.**
Same as rung 1, plus conversation state. The model still cannot do anything except produce text, but now the text depends on a growing history. The flow is still fully controlled by your code: receive message, append to history, call model, return answer.

The only new engineering problem is memory management: what do you keep, what do you drop, what happens when the history outgrows the model's context window.

**Rung 3 — The AI workflow.**
You define a fixed sequence of steps and the model fills in some of them. Extract entities → look them up in the database → generate a reply → classify the sentiment. The *graph is written by you*; the model is a component inside it, not the driver.

This is where a lot of production value lives, and it is deeply underrated because it is not glamorous. A five-node deterministic pipeline with three LLM calls is more reliable, cheaper and easier to debug than an autonomous agent, and it solves most business problems.

**Rung 4 — The agent.**
Here is the actual dividing line: **the model decides which action to take next, and the loop continues until the model decides it is done.**

You give the model a goal and a set of capabilities (tools). You do not write the sequence. The model picks tool A, sees the result, decides it now needs tool C, sees that result, decides it has enough and writes the final answer. The control flow is emergent, not authored.

```
Goal → model → "call tool A" → execute → result → model
     → "call tool C" → execute → result → model → final answer
```

That loop is the whole idea. Everything else in this course — memory, RAG, workflows, human approval, observability — exists to make that loop survivable in production.

### Why the rung matters more than the model

Two teams build the same feature. Team A uses a rung-1 call with GPT-5. Team B uses a rung-4 agent with a mid-tier model.

Team A can unit test their feature, they know exactly what it costs per call, and when it misbehaves they read one prompt.

Team B cannot predict cost per request (the agent might call six tools or one), cannot unit test the flow deterministically, and when it misbehaves they need a trace viewer to find out why the model chose the wrong tool at step four.

Team B has more power. They also have a far harder operational problem. Choosing rung 4 is a commitment to observability, guardrails and evaluation. Choose it deliberately.

### Instructor note

Draw the ladder on screen as four horizontal lines and put a marker labelled "who chooses the next step" moving from left (your code) to right (the model) as you climb. Students remember the picture long after they forget the words.

### Key takeaways

- The dividing line between workflow and agent is **who authors the control flow**.
- Rung 4 buys flexibility and costs you determinism, testability and predictable spend.
- Most business problems are solved at rung 1 or rung 3. Reach for rung 4 when the sequence of steps genuinely cannot be known in advance.

---
═══════════════════════════════════════════════════════════════

## LESSON 1.2 — The Agent Loop

**Duration:** 15 minutes
**Type:** Theory with pseudocode

### Learning objectives

Understand the tool-calling loop mechanically, so that later, when Neuron runs it for you, you know exactly what is being automated.

### The uncomfortable truth about tool calling

A language model cannot execute anything. It cannot call an API, read a file or query your database. It only produces tokens.

What actually happens is a convention. You describe your available functions to the model as structured data. The model, instead of producing prose, produces a structured block that says *"I would like to call `get_weather` with `{latitude: 45.07, longitude: 7.69}`"*. Your code sees that block, executes the real PHP function, and sends the result back to the model as a new message. The model continues.

The model never touches your system. **Your code is always the one executing.** This is worth stating loudly, because it is also the security model: an agent can only do what you gave it a tool for.

### The loop, in pseudocode

```
messages = [system_prompt, user_message]
tools    = [tool_definitions...]

loop:
    response = llm.call(messages, tools)

    if response contains tool calls:
        for each tool_call in response:
            result = execute(tool_call.name, tool_call.arguments)
            messages.append(assistant_tool_call_message)
            messages.append(tool_result_message)
        continue loop
    else:
        return response.text
```

Four things to notice, because each one becomes a chapter of this course:

**1. It is a `while` loop with no guaranteed exit.**
The model decides when to stop. If it keeps deciding to call tools, the loop keeps going. This is why every serious framework has a maximum-runs guard, and why Neuron throws `ToolRunsExceededException`. Lesson 5.9 covers it.

**2. Every iteration re-sends the entire conversation.**
The model is stateless. Iteration five sends the system prompt, the user message, and all four previous tool calls and results. Token usage grows *quadratically* with loop length. A ten-step agent is not ten times more expensive than a one-step agent — it is considerably worse than that.

**3. Tool results are just text.**
Whatever your PHP function returns is stringified and handed to the model as context. Return a 4 MB JSON blob and you have burned your context window in one call. Tool output design is prompt design.

**4. The model's choice is driven entirely by names and descriptions.**
It has never seen your code. It sees `get_transcription` — "Retrieve the transcription of a YouTube video" — and a parameter schema. That text is the entire interface. Module 5 spends significant time here because this is where agents actually fail.

### Worked example: what a two-tool run looks like

User asks: *"What's the average current temperature between Turin and Milan?"*

| Step | Who acts | What happens |
|---|---|---|
| 1 | Your code | Sends system prompt + question + 3 tool definitions |
| 2 | Model | Returns two tool calls: `get_weather(45.07, 7.69)`, `get_weather(45.46, 9.19)` |
| 3 | Your code | Executes both, appends both results to messages |
| 4 | Model | Receives 14.2 and 16.8, returns tool call `mean([14.2, 16.8])` |
| 5 | Your code | Executes, appends result 15.5 |
| 6 | Model | Returns prose: "The average is about 15.5 °C." |

Three round trips to the LLM. Three tool executions. One user question. Internalise this table — it is the single best answer to "why is my AI feature slow and expensive?"

### Key takeaways

- The model requests; your code executes. Always.
- The loop is unbounded by default and must be guarded.
- Context grows with every iteration; cost grows faster than linearly.
- Tool names and descriptions are the model's only interface to your system.

---
═══════════════════════════════════════════════════════════════

## LESSON 1.3 — Anatomy of a Model Call

**Duration:** 14 minutes
**Type:** Theory

### Learning objectives

Know every component that goes into a single request so that when you later configure `SystemPrompt`, `ChatHistory` and tools, you know which knob you are turning.

### What is actually on the wire

Strip away the SDK and every provider request is the same four things:

**1. Model identifier.** Which weights answer the question. Model choice is a cost/quality/latency decision, not a taste decision, and it should be configuration, never a hardcoded string.

**2. The message array.** An ordered list of role-tagged messages:

- `system` — the instructions. Sent on every single request. It is not remembered; it is re-transmitted.
- `user` — what the human said.
- `assistant` — what the model said previously, including tool call requests.
- `tool` — the results your code fed back.

The order is the conversation. There is no session on the provider side. This point is worth repeating until it is boring, because almost every confusion about "memory" dissolves once you accept that the model has none.

**3. Tool definitions.** A JSON Schema per tool: name, description, parameter types, which are required. Sent on every request, in full. Fifty tools means the schema for all fifty is re-uploaded every iteration of the loop. That is why Neuron ships a `ToolSearchMiddleware` for large catalogues (Lesson 15.5).

**4. Generation parameters.** `max_tokens`, `temperature`, `top_p`, stop sequences. For agentic work you generally want low temperature: you are asking for correct tool selection, not creative writing.

### The system prompt is the product

Junior developers treat the system prompt as a greeting. Senior developers treat it as the specification of the whole system. It defines:

- **Identity** — what the agent is and, importantly, is not
- **Procedure** — the order of operations you want followed
- **Constraints** — what it must never do
- **Output contract** — format, language, length

A useful discipline: write the system prompt as if you were onboarding a contractor who is competent, fast, has no context about your company, will not ask clarifying questions unless told to, and forgets everything between tasks. Because that is exactly what you have.

Neuron formalises three of those four sections in its `SystemPrompt` class — `background`, `steps`, `output`. We will meet it in Lesson 3.5, and the reason it exists is that structured prompts are followed more reliably than a wall of prose, and they stay maintainable when six people edit them.

### Reading a response

The response gives you the content, a stop reason, and usage statistics. The usage block — input tokens, output tokens — is your cost meter. Log it from day one. In Module 23 we build budgets on top of it, and you cannot budget what you never recorded.

### Key takeaways

- Every request re-sends system prompt, full history and all tool schemas.
- There is no server-side session. "Memory" is a client-side concern and always will be.
- Low temperature for agentic work.
- Capture token usage from the very first prototype.

---
═══════════════════════════════════════════════════════════════

## LESSON 1.4 — Context Windows, Cost and Latency

**Duration:** 13 minutes
**Type:** Theory with arithmetic

### Learning objectives

Do the napkin maths that determines whether your architecture is viable, before you build it.

### Tokens

A token is roughly ¾ of an English word. Italian and Spanish run a little denser; code runs denser still because of punctuation. Useful working figures:

- 1,000 tokens ≈ 750 words ≈ 1.5 pages
- A typical support email ≈ 300 tokens
- A 20-page PDF ≈ 12,000 tokens
- A medium PHP class ≈ 800 tokens

### The context window is a hard ceiling

Every model has a maximum: system prompt + full history + tool schemas + the response, all together. Exceed it and the request is rejected outright — not truncated, rejected.

This creates the single most common production bug in conversational AI: the app works beautifully for twenty messages and then starts throwing 400s. The history grew past the ceiling.

Neuron handles this with automatic trimming in the `ChatHistory` component, and the documentation gives specific guidance worth memorising: **configure your context window 5–10 % below the model's real limit.** The trimmer looks for a cut point that loses as little context as possible, and it needs headroom to find a good one. A 200K model should be configured at 180–190K. We implement this in Lesson 4.4.

### The cost arithmetic that changes designs

Providers price input and output tokens separately, and output is typically several times more expensive. Take a plausible mid-tier rate of $3 per million input tokens and $15 per million output.

A single simple call: 500 in, 300 out ≈ $0.0060.

Now the same feature as a five-step agent. Because every iteration re-sends everything, input tokens are roughly cumulative:

| Iteration | Input | Output |
|---|---|---|
| 1 | 1,500 | 200 |
| 2 | 2,400 | 200 |
| 3 | 3,300 | 250 |
| 4 | 4,300 | 250 |
| 5 | 5,400 | 400 |
| **Total** | **16,900** | **1,300** |

≈ $0.0702. **Almost twelve times the cost of the single call.**

At 10,000 requests a day that is the difference between $60/day and $700/day. This is the number that decides whether you build rung 3 or rung 4, and it is why Lesson 1.1 insisted the rung matters more than the model.

### Latency compounds the same way

A model call takes 1–4 seconds. Five iterations, plus tool execution time, and you are at 10–20 seconds of wall clock. No user waits 20 seconds at a blank screen. This is not a nice-to-have argument for streaming (Module 7) — it is the reason streaming exists.

### The three levers

When the arithmetic comes out wrong, you have exactly three moves:

1. **Fewer iterations** — sharper prompts, better tool design, fewer tools.
2. **Smaller context** — trim history aggressively, return compact tool results, summarise instead of accumulating.
3. **Cheaper model per step** — a small model for routing and classification, a large one only for the final synthesis. Neuron's provider interface makes this trivial, and it is one of the strongest arguments for the framework.

### Exercise

Take a feature from your current job. Estimate the tokens per iteration and the likely number of iterations. Compute the daily cost at your real traffic. Bring the number to the next lesson.

### Key takeaways

- Context is a hard ceiling; exceeding it fails the request outright.
- Configure the trimmer 5–10 % under the real limit.
- Agent cost grows super-linearly with loop length — model it before you build.
- Three levers: fewer steps, smaller context, cheaper model per step.

---
═══════════════════════════════════════════════════════════════

## LESSON 1.5 — Non-Determinism: Prompting Is Not Programming

**Duration:** 12 minutes
**Type:** Theory

### Learning objectives

Adjust your engineering instincts for a component that returns different output for identical input, and understand which classical practices survive.

### The property that breaks everything

Run the same code twice, get the same result. That assumption underpins unit testing, debugging, code review and CI. An LLM violates it. Same prompt, same model, same parameters — different output.

Even at temperature zero you do not get true determinism: floating-point non-associativity across GPU batches, provider-side model updates behind a stable alias, load-dependent routing. Treat "temperature 0 means deterministic" as false in production.

### What breaks

**Unit tests as you know them.** `assertEquals($expected, $agent->chat($input))` will never pass twice.

**Bisecting bugs.** You cannot reproduce a failure by re-running with the same input.

**Refactoring confidence.** A "harmless" prompt reword can shift behaviour measurably, and nothing in your toolchain will warn you.

**Semantic versioning of your own system.** Your code did not change and your behaviour did. The provider updated a model behind an alias.

### What survives, and what replaces the rest

**Contract testing instead of output testing.** Do not assert the text. Assert the shape: did it return valid JSON matching the schema, did it call the expected tool, is the required field present. Structured output (Module 6) exists largely to make this possible.

**Fake components instead of network calls.** Neuron ships fake providers and tools precisely so your CI can be deterministic and free. Module 10 builds this suite. This is not optional in a real project.

**Evaluations instead of assertions.** A fixed set of representative inputs, run against expected properties, scored. Not pass/fail on one run — a quality percentage tracked over time, like a performance benchmark. Neuron has an `Evals` component; we cover it in Lesson 10.5.

**Tracing instead of debugging.** You cannot step through the model's reasoning, but you can record every prompt, tool call, argument and token count. That is what Inspector does, and it is why observability appears as a first-class pillar of the framework rather than an add-on.

**Pinning instead of trusting aliases.** Use explicit model versions in production. `claude-sonnet-4-5-20250929`, not a floating alias, so that a provider update is a deployment you choose rather than an incident you discover.

### The mental shift

Stop thinking "function". Start thinking "a competent but inconsistent junior colleague". You would not unit-test a colleague. You would give clear instructions, constrain their permissions, review their work, and track their error rate. Every architectural pattern in this course is one of those four things.

### Key takeaways

- Assume non-determinism even at temperature 0.
- Test contracts and shapes, not strings.
- Fake components for CI; evals for quality; traces for debugging.
- Pin model versions in production.

---
═══════════════════════════════════════════════════════════════

## LESSON 1.6 — The Landscape: Python Frameworks and Where Neuron Sits

**Duration:** 10 minutes
**Type:** Theory

### Learning objectives

Understand the vocabulary of the wider ecosystem so that Python-centric articles, talks and job specs are readable, and know honestly what PHP does and does not have.

### The Python incumbents

**LangChain** — the first mover and the largest. Enormous integration surface, historically heavy abstraction. It made "chains" the default vocabulary, and it made a lot of people wary of over-abstraction.

**LangGraph** — LangChain's answer to the limits of linear chains: an explicit graph of nodes and edges, with state, loops, checkpointing and human-in-the-loop interruption. If you read one thing from the Python world to understand Neuron's `Workflow`, read LangGraph's documentation. The conceptual overlap is direct and deliberate.

**LlamaIndex** — originated as a RAG-first library: ingestion, indexing, retrieval. Strongest on the data side.

**CrewAI / AutoGen** — role-based multi-agent orchestration. "A researcher agent, a writer agent, a critic agent." Excellent demos; the hard part in production is controlling cost and stopping conditions.

### What all of them assume

They assume your data and your business logic are in Python, or reachable over a network. For a large amount of the world's commerce, they are not. They are in a PHP application with fifteen years of accumulated domain rules in it.

The standard workaround is a Python microservice beside the PHP app. That means a second runtime, second deployment pipeline, second dependency tree, an API boundary you now have to design, authenticate and version — and critically, the agent lives on the wrong side of that boundary from the business rules. Every tool call becomes a network hop into an application that already knew the answer.

### Where Neuron sits

Neuron is the PHP-native implementation of the same architecture. Concretely it provides:

- An agent loop with tool calling, across many providers behind one interface
- An event-driven `Workflow` engine with state, loops, checkpointing and interruption — the LangGraph-shaped piece
- A RAG pipeline: loaders, embeddings, vector stores, pre/post processors
- MCP client support
- Streaming with UI protocol adapters
- First-class observability via Inspector

The honest comparison: Python has a deeper bench of research-grade tooling and a much larger community. PHP has your data, your domain model, your auth, your queue and your ORM. For a huge class of business applications the second list wins, because most agentic value comes from acting on proprietary data with proprietary rules, not from novel model techniques.

### Being fair to the alternatives

You do not have to use a framework. You can call a provider API with Guzzle and write the tool loop yourself — it is maybe 150 lines. What you then own is: multi-provider abstraction, retries, streaming parsing, schema generation, history trimming, checkpointing, and a trace format. That is the honest scope of what a framework saves you. Judge Neuron on that list.

### Key takeaways

- Neuron implements the same architecture as LangGraph, in PHP.
- The strategic argument is data locality: put the agent where the business logic already is.
- Frameworks buy you provider abstraction, streaming, schemas, history management, checkpointing and traces.

---
═══════════════════════════════════════════════════════════════

## LESSON 1.7 — Choosing the Right Rung: A Decision Framework

**Duration:** 12 minutes
**Type:** Theory with case studies

### Learning objectives

Apply a repeatable decision procedure to a real requirement instead of defaulting to "let's build an agent".

### Four questions, in order

**Q1. Is the sequence of steps knowable in advance?**
Yes → rung 1 or 3. No → consider rung 4.
This is the whole question. If you can draw the flowchart, write the flowchart. A workflow that always does the same three things is cheaper, faster, testable and debuggable.

**Q2. Does it need to read or write systems of record?**
No → no tools needed. Yes → tools, and immediately: which permissions, which audit trail, which actions are irreversible.

**Q3. Are any actions irreversible or expensive?**
Yes → human-in-the-loop is mandatory, not a stretch goal. Refunds, emails to customers, deletions, payments. Design the approval gate at the same time as the tool, never afterwards.

**Q4. Does correctness depend on private knowledge?**
Yes → RAG or database tools. Note that these are different answers: RAG for unstructured prose, database tools for structured facts. Using RAG to answer "how many orders did this customer place" is a design error — that is a SQL query, and the model should call it as a tool.

### Case studies

**Case A — "Summarise incoming support tickets."**
Q1 yes, Q2 no, Q3 no, Q4 no. → **Rung 1.** One call, one prompt. Building an agent here is résumé-driven development.

**Case B — "Answer customer questions from our help centre."**
Q1 yes, Q2 read-only, Q3 no, Q4 yes. → **Rung 3 with RAG.** Retrieve, then generate, then cite. A fixed two-step pipeline. No autonomy required.

**Case C — "Handle a customer complaint end to end."**
Q1 no — you do not know in advance whether it needs an order lookup, a policy check, a refund, an escalation, or all four. Q2 yes, read and write. Q3 yes, refunds are irreversible. Q4 yes.
→ **Rung 4, with tools, RAG, approval gates and full tracing.** This is Capstone Project B, and it earns every piece of machinery in this course.

**Case D — "Generate a weekly report from our database."**
Q1 yes, Q2 read, Q3 no, Q4 yes-structured. → **Rung 3.** Fixed query, model formats the prose. The temptation to let an agent explore the database is real; resist it for a scheduled job where the questions never change.

### The escalation principle

Start at the lowest rung that could work. Ship it. Escalate only when you have evidence — real failing cases — that the rung is insufficient. Every rung upward multiplies cost, latency and operational surface.

The reverse path is far more painful: teams that begin at rung 4 rarely descend, because by then the flexibility is load-bearing and nobody knows which parts were actually needed.

### Module 1 assessment

Take three features from your own product. For each: run the four questions, state the rung, and justify it in five lines. Bring one case where you initially wanted rung 4 and the questions pushed you down to rung 3.

### Key takeaways

- If you can draw the flowchart, build the flowchart.
- Irreversible actions require an approval gate designed at the same moment as the tool.
- RAG for prose, database tools for facts — do not confuse the two.
- Start low, escalate on evidence.

---
═══════════════════════════════════════════════════════════════
# MODULE 2 — THE ARCHITECTURE OF NEURON
═══════════════════════════════════════════════════════════════
---

## LESSON 2.1 — The Four Pillars

**Duration:** 12 minutes
**Type:** Theory with diagram

### Learning objectives

Hold the whole framework in your head as four concepts, so that every later lesson has somewhere to attach.

### Installation, for orientation

```bash
composer require neuron-core/neuron-ai
```

Requirements: PHP 8.1 or later for the core package. The Laravel SDK, covered in Part V, requires PHP 8.2 and Laravel 10 or later.

### Pillar 1 — Agent

The tool-calling loop from Lesson 1.2, implemented and guarded. You extend a base class, declare which provider to use, what the instructions are, and which tools are available. Neuron runs the loop, manages the message array, handles the tool dispatch and enforces the run limits.

This is rung 4 from Lesson 1.1, out of the box.

### Pillar 2 — Workflow

An event-driven graph. You define nodes; each node receives an event and returns an event; the returned event type determines which node runs next. On top of that: shared state, branching, loops, checkpointing to storage, interruption for human input, and resumption — potentially days later.

This is rung 3 done properly, and it is also the substrate for multi-agent systems.

### Pillar 3 — RAG

The retrieval pipeline: data loaders to ingest, an embeddings provider to vectorise, a vector store to hold and search, pre/post processors to improve queries and rerank results, and a `RAG` class that ties them together into an agent that answers from your documents.

### Pillar 4 — Observability

Tracing of every LLM call, tool invocation and retrieval, delivered through Inspector. Given Lesson 1.5, this is not a monitoring nicety. Without a trace you cannot answer "why did it do that", and "why did it do that" is the only question you will ever ask.

### The mental picture

```
                   ┌─────────────────────────┐
                   │       WORKFLOW          │
                   │  (nodes, events, state, │
                   │   loops, interruption)  │
                   │                         │
                   │   ┌───────┐  ┌───────┐  │
                   │   │ AGENT │  │  RAG  │  │
                   │   └───────┘  └───────┘  │
                   └─────────────────────────┘
                                │
       ┌────────────┬───────────┼───────────┬────────────┐
   Providers      Tools    ChatHistory  VectorStores  Embeddings
                                │
                          OBSERVABILITY
```

Workflow is the outer container. Agent and RAG are pre-built configurations that live inside it. Underneath, a set of swappable components. Cross-cutting, tracing.

### Key takeaways

- Four pillars: Agent, Workflow, RAG, Observability.
- Workflow is the general case; Agent and RAG are specialisations.
- Observability is a pillar, not an add-on, because of non-determinism.

---
═══════════════════════════════════════════════════════════════

## LESSON 2.2 — Everything Is an Interface

**Duration:** 14 minutes
**Type:** Theory with code

### Learning objectives

Recognise the framework's core design decision and understand the practical leverage it gives you.

### The five interfaces that matter

Neuron's architecture is a small set of contracts that every concrete implementation honours:

| Interface | Responsibility | Example implementations |
|---|---|---|
| `AIProviderInterface` | Talk to an LLM | Anthropic, OpenAI, Gemini, Mistral, Ollama, DeepSeek, Bedrock, Azure |
| `ToolInterface` | Give the agent a capability | Your classes, built-in toolkits, MCP-provided tools |
| `ChatHistoryInterface` | Store conversation state | InMemory, File, SQL, Eloquent |
| `EmbeddingsProviderInterface` | Turn text into vectors | OpenAI, Voyage, Ollama |
| `VectorStoreInterface` | Store and search vectors | File, Memory, Pinecone, Elasticsearch, Qdrant, Chroma, pgvector |

Your application code depends on the interface. Never on the implementation.

### What this looks like in practice

```php
protected function provider(): AIProviderInterface
{
    return new Anthropic(
        key: 'ANTHROPIC_API_KEY',
        model: 'ANTHROPIC_MODEL',
    );
}
```

Switch to a locally hosted model:

```php
protected function provider(): AIProviderInterface
{
    return new Ollama(
        url: 'OLLAMA_URL',
        model: 'OLLAMA_MODEL',
    );
}
```

Nothing else changes. Not the instructions, not the tools, not the history, not the calling code. In Lesson 3.6 we push this further and drive the choice entirely from an environment variable.

### Why this is a strategic capability, not a convenience

Four consequences worth naming explicitly, because they are how you justify the framework to a decision-maker:

**Cost tiering.** Route classification and extraction to a cheap fast model; route final synthesis to an expensive one. This is the third lever from Lesson 1.4, and the interface is what makes it a one-line change instead of a refactor.

**Provider risk.** Outages happen, prices change, terms change. A hard dependency on one vendor's SDK is a business risk. An interface is an exit.

**Local development.** Run Ollama on your laptop and develop the entire course for free. Deploy against a cloud provider. Same code.

**Data residency.** A client who cannot send data outside the EU, or outside their own building, is a configuration change rather than a rewrite.

### The trade-off, stated honestly

An abstraction over multiple providers converges on their common subset. Provider-specific features — extended thinking modes, prompt caching, native web search tools, particular safety settings — are either exposed through escape hatches or not available. Neuron's answer is `ProviderTool`, which lets you use a provider's built-in tools (OpenAI Responses, Gemini and Anthropic support these), but the framework's own documentation is candid that provider tools introduce constraints and that the portable Tools/Toolkits system stays the more flexible route.

Know what you are trading. Portability costs access to the newest vendor-specific feature for a while.

### Key takeaways

- Five interfaces: provider, tool, chat history, embeddings, vector store.
- Depend on the interface; the implementation is configuration.
- The payoff is cost tiering, vendor risk, free local development and data residency.
- The cost is delayed access to provider-specific features.

---
═══════════════════════════════════════════════════════════════

## LESSON 2.3 — The Key Insight: Agent and RAG *Are* Workflows

**Duration:** 15 minutes
**Type:** Theory — the most important lesson in Module 2

### Learning objectives

Understand the framework's central unifying idea, which the documentation reveals late and which explains most of what would otherwise seem arbitrary.

### The statement

`Agent` and `RAG` are not separate systems that sit next to `Workflow`. **They are workflows.** They are pre-assembled graphs of nodes that implement the two most common agentic patterns.

Neuron's own documentation puts it directly: Agent and RAG classes are workflows themselves, representing ready-to-use implementations of the most common patterns for tool calls, retrieval and structured output.

### What that means concretely

When you call `->chat()` on an agent, you are running a workflow whose nodes are roughly:

- `ChatNode` — calls the LLM
- `ToolNode` — executes any requested tools, loops back
- `StructuredOutputNode` — used when you request a typed result
- `StreamingNode` — used when you call `->stream()`

Those node names are not internal trivia. They are part of the public surface. In the Laravel SDK you attach middleware by naming the node it should run on:

```php
Neuron::middleware(ToolNode::class, new ToolApproval())
    ->chat(new UserMessage('Delete the oldest log file'));
```

You cannot use that API without knowing that `chat()` is backed by nodes. This is precisely why we are covering it in Module 2 rather than Module 15.

### The three consequences

**1. Everything you learn about workflows applies to agents.**
Middleware, state, streaming, interruption, persistence — these are workflow features, and agents inherit all of them. When you reach Module 15 and learn human-in-the-loop, you are not learning a separate agent feature. You are learning a workflow feature that agents get for free.

**2. There is no second framework when the project grows.**
The usual trajectory with other stacks is: prototype with the simple abstraction, hit its ceiling, rewrite against the graph abstraction. Here, `Agent` *is* the graph abstraction with a default configuration. Growing means adding nodes, not migrating.

**3. You can use an Agent as a node inside a larger Workflow.**
This is the multi-agent story, and it needs no special multi-agent API. A research agent is a node. A writer agent is a node. An arbiter is a node. Compose them with events. Module 16 does exactly this.

### The decision rule

**Extend `Agent`** when your problem is "one entity, a goal, some tools, loop until done". That is most single-purpose assistants.

**Build a `Workflow`** when you need: control over the order of steps, multiple specialised agents, branching or looping that you author, checkpoints, or a pause for human input.

**Extend `RAG`** when the core job is answering from a document corpus.

And when you are unsure: start with `Agent`. Migrating to a workflow later is additive, because it was a workflow all along.

### Instructor note

This is the lesson to put on a slide and repeat in Module 13. Students who miss it experience Part IV as an unrelated new topic; students who get it experience Part IV as "oh, so that's what was under the agent".

### Key takeaways

- `Agent` and `RAG` are configured workflows, not parallel systems.
- Node classes (`ChatNode`, `ToolNode`, `StreamingNode`, `StructuredOutputNode`) are public API — middleware targets them.
- Workflow features are inherited by agents.
- Multi-agent needs no special API: an agent is just a node.

---
═══════════════════════════════════════════════════════════════

## LESSON 2.4 — Extend or Compose: Choosing Your Structure

**Duration:** 12 minutes
**Type:** Theory with code sketches

### Learning objectives

Pick the right structural pattern for a new piece of agentic work, and know how to move between patterns without rewriting.

### Pattern A — Extend the Agent class

The default, and correct for the large majority of cases.

```php
namespace App\Neuron;

use NeuronAI\Agent\Agent;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Providers\Anthropic\Anthropic;

class SupportAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return new Anthropic(key: '...', model: '...');
    }

    public function instructions(): string
    {
        return (string) new SystemPrompt(
            background: ['You are a customer support assistant.'],
        );
    }

    protected function tools(): array
    {
        return [ /* ... */ ];
    }
}
```

Three template methods — `provider()`, `instructions()`, `tools()` — plus optional `chatHistory()`. Everything else is inherited. The class is a declaration of *what this agent is*, and it reads like configuration because it is.

**Why this pattern is worth defending.** The class becomes a named, testable, injectable unit. `SupportAgent` can be bound in a service container, mocked in tests, and reasoned about by a colleague who has never seen the framework. That is a real architectural benefit over scattering fluent configuration across controllers.

### Pattern B — Fluent configuration at the call site

For one-off runs and experiments:

```php
$response = SupportAgent::make()
    ->toolMaxRuns(5)
    ->addTool(SomeExtraTool::make())
    ->chat(new UserMessage('...'));
```

Use it for per-request variation on top of a declared class: a tool that only appears for admins, a lower run limit for a cheap endpoint. Do not use it as a substitute for having a class — configuration assembled inline in a controller is configuration nobody can find in six months.

### Pattern C — Compose a Workflow from components

When you want authored control flow, you use Neuron's components as standalone parts. The documentation is explicit that providers, embeddings, data loaders, chat history and vector stores can all be used as standalone components to build fully custom agentic entities.

```php
$handler = Workflow::make()
    ->addNodes([
        new ClassifyNode(),
        new RetrieveNode(),
        new AnswerNode(),
    ])
    ->init();

$handler->run();
```

Here *you* wrote the sequence. The model fills in the steps. This is rung 3 from Lesson 1.1, with checkpointing and interruption available when needed.

### The migration path

The reason this decision is low-risk: Pattern A → Pattern C is additive. Because `SupportAgent` is already a workflow, promoting it means wrapping it as a node in a larger graph, not rewriting it.

```php
class SupportNode extends Node
{
    public function __invoke(StartEvent $event, WorkflowState $state): ResolvedEvent
    {
        $answer = SupportAgent::make()->chat($event->message)->getMessage();
        return new ResolvedEvent($answer->getContent());
    }
}
```

Your agent is unchanged. It is now a component of something larger.

### Key takeaways

- Extend `Agent` by default; the class is a named, injectable, testable unit.
- Fluent config for per-request variation, not as a replacement for a class.
- Compose a `Workflow` when you author the control flow.
- Promotion from A to C is additive — wrap, do not rewrite.

---
═══════════════════════════════════════════════════════════════

## LESSON 2.5 — The Ecosystem Around the Framework

**Duration:** 10 minutes
**Type:** Theory / orientation

### Learning objectives

Know what exists around the core package so you do not rebuild things that ship, and know which pieces you will actually use in this course.

### Inspector

Built by the same team, and the reason observability is a pillar. Set one environment variable:

```dotenv
INSPECTOR_INGESTION_KEY=your-key-here
```

and every agent execution appears as a timeline: which node ran, which tool was called with which arguments, what came back, how many tokens, how long.

We use it in Module 10 and again in Module 23. Given Lesson 1.5, plan for a trace viewer of some kind from the start — this one is simply the path of least resistance.

### The Laravel SDK

```bash
composer require neuron-core/neuron-laravel
```

The whole of Part V. It provides a config file, artisan generators (`neuron:agent`, `neuron:rag`, `neuron:tool`, `neuron:workflow`, `neuron:node`, `neuron:middleware`), facades for providers and vector stores, ready-made migrations for Eloquent chat history, and an Eloquent persistence layer for workflow interrupts.

Worth stressing to students: this package adds convenience, not capability. Everything it does you could do by hand — which is exactly why we build it by hand first in Parts II–IV.

### MCP — Model Context Protocol

An open protocol for exposing tools to AI systems. Neuron ships an MCP connector, so tools published by any MCP server can be attached to a Neuron agent like native ones. Module 9. The security implications get their own discussion: an MCP server is third-party code entering your agent's loop.

### Maestro

An open-source CLI agent framework built on Neuron, with tool calling and human-in-the-loop approvals. Useful as a reference implementation of a complete production application, and a good source of code-reading exercises. Bonus module B2.

### Neuron Hub

A registry of community extensions and toolkits. Check it before writing an integration — and publish yours there, which is the topic of a bonus lesson.

### Neuron Studio

A community package (`digitalelvis/neuronai-studio`) offering a visual agent builder for Laravel that exports real PHP classes. Useful for prototyping and for demonstrating architecture to non-developers. It generates code, it does not replace understanding it.

### Version landscape, as of this recording

- **v3.x** — current stable. The course targets this.
- **v4 beta** — adds tool approval as a top-level chapter and extended evaluations. Bonus module B1 covers the upgrade.
- **v1/v2** — legacy. Namespaces differ (`NeuronAI\Agent` vs `NeuronAI\Agent\Agent`, `NeuronAI\SystemPrompt` vs `NeuronAI\Agent\SystemPrompt`). If you find a blog post or a documentation page whose imports do not match this course, check which version it targets first. Parts of the official docs still carry v2-era imports.

### Module 2 assessment

Reproduce the four-pillar diagram from memory. Then, for each of Capstone A ("Repo Auditor CLI") and Capstone B ("Agentic Support Desk"), list which pillars and which ecosystem pieces you expect to need. Keep the answer; we compare against it at the end of the course.

### Key takeaways

- Inspector for traces; Laravel SDK for convenience, not capability.
- MCP brings external tools in — and external code with them.
- Course targets v3.x; v1/v2 namespaces differ and appear in older material.

---

**END OF PART I**

*Next: Module 3 — Setup and Your First Agent (plain PHP + Composer).*
