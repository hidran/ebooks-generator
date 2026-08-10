# Chapter 1 — What "Agentic" Actually Means

::: {.callout .callout-tip}
[Code for this chapter]{.callout-title}

This chapter is conceptual and has no standalone code, but the companion repository at [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) holds runnable versions of everything the book builds.
:::

## 1.1 LLM, Chatbot, Workflow, Agent: The Autonomy Ladder

In 2023 everything was a "chatbot". By 2025 everything is an "agent". The word has been stretched so far that it now means "software that calls an LLM", which is useless as a design category. Before we write a line of PHP we need a definition sharp enough to make architectural decisions with.

The useful distinction is not *what the software does*. It is **who decides what happens next**.

That question produces a four-rung ladder, and by the end of this section you should be able to place any AI feature you are asked to build on it — and explain to a client why the rung matters more than the model.

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

That loop is the whole idea. Everything else in this book — memory, RAG, workflows, human approval, observability — exists to make that loop survivable in production.

### Why the rung matters more than the model

Two teams build the same feature. Team A uses a rung-1 call with a frontier model. Team B uses a rung-4 agent with a mid-tier model.

Team A can unit test their feature, they know exactly what it costs per call, and when it misbehaves they read one prompt.

Team B cannot predict cost per request — the agent might call six tools or one — cannot unit test the flow deterministically, and when it misbehaves they need a trace viewer to find out why the model chose the wrong tool at step four.

Team B has more power. They also have a far harder operational problem. Choosing rung 4 is a commitment to observability, guardrails and evaluation. Choose it deliberately.

::: {.callout .callout-tip}
[In practice]{.callout-title}

Picture the ladder as four horizontal lines with a single marker labelled *who chooses the next step*, sliding from left (your code) to right (the model) as you climb. It is a better design tool than any checklist, because it forces the one question that matters before you have committed to anything.
:::

### Key takeaways

- The dividing line between workflow and agent is **who authors the control flow**.
- Rung 4 buys flexibility and costs you determinism, testability and predictable spend.
- Most business problems are solved at rung 1 or rung 3. Reach for rung 4 when the sequence of steps genuinely cannot be known in advance.

## 1.2 The Agent Loop

Before NeuronAI runs the tool-calling loop for you, it is worth understanding it mechanically — because knowing exactly what is being automated is the difference between configuring a framework and hoping it works.

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

Four things to notice, because each one becomes a chapter of this book:

**1. It is a `while` loop with no guaranteed exit.**
The model decides when to stop. If it keeps deciding to call tools, the loop keeps going. This is why every serious framework has a maximum-runs guard, and why NeuronAI throws an exception when the limit is hit. Section 5.9 covers it.

**2. Every iteration re-sends the entire conversation.**
The model is stateless. Iteration five sends the system prompt, the user message, and all four previous tool calls and results. Token usage grows *quadratically* with loop length. A ten-step agent is not ten times more expensive than a one-step agent — it is considerably worse than that.

**3. Tool results are just text.**
Whatever your PHP function returns is stringified and handed to the model as context. Return a 4 MB JSON blob and you have burned your context window in one call. Tool output design is prompt design.

**4. The model's choice is driven entirely by names and descriptions.**
It has never seen your code. It sees `get_transcription` — "Retrieve the transcription of a YouTube video" — and a parameter schema. That text is the entire interface. Chapter 5 spends significant time here because this is where agents actually fail.

### Worked example: what a two-tool run looks like

The user asks: *"What's the average current temperature between Turin and Milan?"*

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

## 1.3 Anatomy of a Model Call

Every component that goes into a single request corresponds to a knob you will later turn in `SystemPrompt`, `ChatHistory` or a tool definition. Knowing which is which saves a great deal of guessing.

### What is actually on the wire

Strip away the SDK and every provider request is the same four things:

**1. Model identifier.** Which weights answer the question. Model choice is a cost/quality/latency decision, not a taste decision, and it should be configuration, never a hardcoded string.

**2. The message array.** An ordered list of role-tagged messages:

- `system` — the instructions. Sent on every single request. It is not remembered; it is re-transmitted.
- `user` — what the human said.
- `assistant` — what the model said previously, including tool call requests.
- `tool` — the results your code fed back.

The order is the conversation. There is no session on the provider side. This point is worth repeating until it is boring, because almost every confusion about "memory" dissolves once you accept that the model has none.

**3. Tool definitions.** A JSON Schema per tool: name, description, parameter types, which are required. Sent on every request, in full. Fifty tools means the schema for all fifty is re-uploaded every iteration of the loop. That is why NeuronAI ships a `ToolSearchMiddleware` for large catalogues.

**4. Generation parameters.** `max_tokens`, `temperature`, `top_p`, stop sequences. For agentic work you generally want low temperature: you are asking for correct tool selection, not creative writing.

### The system prompt is the product

Junior developers treat the system prompt as a greeting. Senior developers treat it as the specification of the whole system. It defines:

- **Identity** — what the agent is and, importantly, is not
- **Procedure** — the order of operations you want followed
- **Constraints** — what it must never do
- **Output contract** — format, language, length

A useful discipline: write the system prompt as if you were onboarding a contractor who is competent, fast, has no context about your company, will not ask clarifying questions unless told to, and forgets everything between tasks. Because that is exactly what you have.

NeuronAI formalises three of those four sections in its `SystemPrompt` class — `background`, `steps`, `output`. We meet it in Section 3.5, and the reason it exists is that structured prompts are followed more reliably than a wall of prose, and they stay maintainable when six people edit them.

### Reading a response

The response gives you the content, a stop reason, and usage statistics. The usage block — input tokens, output tokens — is your cost meter. Log it from day one. In Chapter 23 we build budgets on top of it, and you cannot budget what you never recorded.

### Key takeaways

- Every request re-sends system prompt, full history and all tool schemas.
- There is no server-side session. "Memory" is a client-side concern and always will be.
- Low temperature for agentic work.
- Capture token usage from the very first prototype.

## 1.4 Context Windows, Cost and Latency

This section is arithmetic. It is also the section most likely to change what you decide to build, because it is the napkin maths that determines whether an architecture is viable — and almost nobody does it in advance.

### Tokens

A token is roughly ¾ of an English word. Italian and Spanish run a little denser; code runs denser still because of punctuation. Useful working figures:

- 1,000 tokens ≈ 750 words ≈ 1.5 pages
- A typical support email ≈ 300 tokens
- A 20-page PDF ≈ 12,000 tokens
- A medium PHP class ≈ 800 tokens

### The context window is a hard ceiling

Every model has a maximum: system prompt + full history + tool schemas + the response, all together. Exceed it and the request is rejected outright — not truncated, rejected.

This creates the single most common production bug in conversational AI: the app works beautifully for twenty messages and then starts throwing 400s. The history grew past the ceiling.

NeuronAI handles this with automatic trimming in the `ChatHistory` component, and the documentation gives specific guidance worth memorising: **configure your context window 5–10 % below the model's real limit.** The trimmer looks for a cut point that loses as little context as possible, and it needs headroom to find a good one. A 200K model should be configured at 180–190K. We implement this in Section 4.4.

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

At 10,000 requests a day that is the difference between $60/day and $700/day. This is the number that decides whether you build rung 3 or rung 4, and it is why Section 1.1 insisted the rung matters more than the model.

### Latency compounds the same way

A model call takes 1–4 seconds. Five iterations, plus tool execution time, and you are at 10–20 seconds of wall clock. No user waits 20 seconds at a blank screen. This is not a nice-to-have argument for streaming (Chapter 7) — it is the reason streaming exists.

### The three levers

When the arithmetic comes out wrong, you have exactly three moves:

1. **Fewer iterations** — sharper prompts, better tool design, fewer tools.
2. **Smaller context** — trim history aggressively, return compact tool results, summarise instead of accumulating.
3. **Cheaper model per step** — a small model for routing and classification, a large one only for the final synthesis. NeuronAI's provider interface makes this trivial, and it is one of the strongest arguments for the framework.

### Exercise

Take a feature from your current job. Estimate the tokens per iteration and the likely number of iterations. Compute the daily cost at your real traffic. Keep the number; it will inform every design decision in Part II.

### Key takeaways

- Context is a hard ceiling; exceeding it fails the request outright.
- Configure the trimmer 5–10 % under the real limit.
- Agent cost grows super-linearly with loop length — model it before you build.
- Three levers: fewer steps, smaller context, cheaper model per step.

## 1.5 Non-Determinism: Prompting Is Not Programming

You are about to work with a component that returns different output for identical input. Some of your engineering instincts survive that; most need adjusting. This section sorts them.

### The property that breaks everything

Run the same code twice, get the same result. That assumption underpins unit testing, debugging, code review and CI. An LLM violates it. Same prompt, same model, same parameters — different output.

Even at temperature zero you do not get true determinism: floating-point non-associativity across GPU batches, provider-side model updates behind a stable alias, load-dependent routing. Treat "temperature 0 means deterministic" as false in production.

### What breaks

**Unit tests as you know them.** `assertEquals($expected, $agent->chat($input))` will never pass twice.

**Bisecting bugs.** You cannot reproduce a failure by re-running with the same input.

**Refactoring confidence.** A "harmless" prompt reword can shift behaviour measurably, and nothing in your toolchain will warn you.

**Semantic versioning of your own system.** Your code did not change and your behaviour did. The provider updated a model behind an alias.

### What survives, and what replaces the rest

**Contract testing instead of output testing.** Do not assert the text. Assert the shape: did it return valid JSON matching the schema, did it call the expected tool, is the required field present. Structured output (Chapter 6) exists largely to make this possible.

**Fake components instead of network calls.** NeuronAI ships fake providers and tools precisely so your CI can be deterministic and free. Chapter 10 builds this suite. This is not optional in a real project.

**Evaluations instead of assertions.** A fixed set of representative inputs, run against expected properties, scored. Not pass/fail on one run — a quality percentage tracked over time, like a performance benchmark. NeuronAI has an `Evals` component; we cover it in Section 10.5.

**Tracing instead of debugging.** You cannot step through the model's reasoning, but you can record every prompt, tool call, argument and token count. That is what Inspector does, and it is why observability appears as a first-class pillar of the framework rather than an add-on.

**Pinning instead of trusting aliases.** Use explicit model versions in production — a dated, fully-qualified model identifier rather than a floating alias — so that a provider update is a deployment you choose rather than an incident you discover.

### The mental shift

Stop thinking "function". Start thinking "a competent but inconsistent junior colleague". You would not unit-test a colleague. You would give clear instructions, constrain their permissions, review their work, and track their error rate. Every architectural pattern in this book is one of those four things.

### Key takeaways

- Assume non-determinism even at temperature 0.
- Test contracts and shapes, not strings.
- Fake components for CI; evals for quality; traces for debugging.
- Pin model versions in production.

## 1.6 The Landscape: Python Frameworks and Where NeuronAI Sits

The vocabulary of this field was invented in Python, and it is worth learning so that Python-centric articles, conference talks and job specifications are readable. It is also worth being honest about what PHP does and does not have.

### The Python incumbents

**LangChain** — the first mover and the largest. Enormous integration surface, historically heavy abstraction. It made "chains" the default vocabulary, and it made a lot of people wary of over-abstraction.

**LangGraph** — LangChain's answer to the limits of linear chains: an explicit graph of nodes and edges, with state, loops, checkpointing and human-in-the-loop interruption. If you read one thing from the Python world to understand NeuronAI's `Workflow`, read LangGraph's documentation. The conceptual overlap is direct and deliberate.

**LlamaIndex** — originated as a RAG-first library: ingestion, indexing, retrieval. Strongest on the data side.

**CrewAI / AutoGen** — role-based multi-agent orchestration. "A researcher agent, a writer agent, a critic agent." Excellent demos; the hard part in production is controlling cost and stopping conditions.

### What all of them assume

They assume your data and your business logic are in Python, or reachable over a network. For a large amount of the world's commerce, they are not. They are in a PHP application with fifteen years of accumulated domain rules in it.

The standard workaround is a Python microservice beside the PHP app. That means a second runtime, second deployment pipeline, second dependency tree, an API boundary you now have to design, authenticate and version — and critically, the agent lives on the wrong side of that boundary from the business rules. Every tool call becomes a network hop into an application that already knew the answer.

### Where NeuronAI sits

NeuronAI is the PHP-native implementation of the same architecture. Concretely it provides:

- An agent loop with tool calling, across many providers behind one interface
- An event-driven `Workflow` engine with state, loops, checkpointing and interruption — the LangGraph-shaped piece
- A RAG pipeline: loaders, embeddings, vector stores, pre/post processors
- MCP client support
- Streaming with UI protocol adapters
- First-class observability via Inspector

The honest comparison: Python has a deeper bench of research-grade tooling and a much larger community. PHP has your data, your domain model, your auth, your queue and your ORM. For a huge class of business applications the second list wins, because most agentic value comes from acting on proprietary data with proprietary rules, not from novel model techniques.

### Being fair to the alternatives

You do not have to use a framework. You can call a provider API with Guzzle and write the tool loop yourself — it is maybe 150 lines. What you then own is: multi-provider abstraction, retries, streaming parsing, schema generation, history trimming, checkpointing, and a trace format. That is the honest scope of what a framework saves you. Judge NeuronAI on that list.

### Key takeaways

- NeuronAI implements the same architecture as LangGraph, in PHP.
- The strategic argument is data locality: put the agent where the business logic already is.
- Frameworks buy you provider abstraction, streaming, schemas, history management, checkpointing and traces.

## 1.7 Choosing the Right Rung: A Decision Framework

The ladder is only useful if it turns into a procedure. Here is one — four questions, asked in order, applied to a real requirement instead of defaulting to "let's build an agent".

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
→ **Rung 4, with tools, RAG, approval gates and full tracing.** This is Capstone B in Chapter 25, and it earns every piece of machinery in this book.

**Case D — "Generate a weekly report from our database."**
Q1 yes, Q2 read, Q3 no, Q4 yes-structured. → **Rung 3.** Fixed query, model formats the prose. The temptation to let an agent explore the database is real; resist it for a scheduled job where the questions never change.

### The escalation principle

Start at the lowest rung that could work. Ship it. Escalate only when you have evidence — real failing cases — that the rung is insufficient. Every rung upward multiplies cost, latency and operational surface.

The reverse path is far more painful: teams that begin at rung 4 rarely descend, because by then the flexibility is load-bearing and nobody knows which parts were actually needed.

### Exercise

Take three features from your own product. For each: run the four questions, state the rung, and justify it in five lines. Find one case where you initially wanted rung 4 and the questions pushed you down to rung 3 — there is almost always one, and noticing it is the skill this chapter is teaching.

### Key takeaways

- If you can draw the flowchart, build the flowchart.
- Irreversible actions require an approval gate designed at the same moment as the tool.
- RAG for prose, database tools for facts — do not confuse the two.
- Start low, escalate on evidence.
