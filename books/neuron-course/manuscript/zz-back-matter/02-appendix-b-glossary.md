# Appendix B — Glossary {.unnumbered}

**Agent.** Rung 4 of the autonomy ladder: the model decides which action to take next, and the loop continues until it decides it is done. In NeuronAI, a class extending `Agent` — which is itself a pre-configured Workflow.

**Agent loop.** The cycle of calling the model, executing any tools it requests, feeding the results back, and repeating until the model returns prose instead of a tool call. Unbounded by default; guarded with run limits.

**Approval policy.** A tool's own declaration that a call needs a human: the protected `approvalPolicy()` hook, returning `false`, `true` or a reason string. Overridden per instance with `requireApproval()`, `suppressApproval()` or `withApprovalPolicy()`. Answered on the agent with `submitApprovalDecisions()`.

**Autonomy ladder.** The four rungs from Section 1.1 — bare LLM call, chatbot, workflow, agent — distinguished by *who decides what happens next*.

**BM25.** A classical keyword-ranking function. Hybrid stores such as PHPVector combine it with vector search.

**Checkpoint.** The pre-v4 name for *memoization*. `checkpoint()` still exists, deprecated, and calls `memoize()`.

**Chunk.** A piece of a document, produced by a splitter and embedded independently. Chunk size and separator are the two parameters that most affect retrieval quality.

**Chunk object.** In streaming, an object yielded by `stream()` — `TextChunk`, `ReasoningChunk`, `ToolCallChunk`, `ToolResultChunk` and a few rarer kinds. Only `TextChunk` carries answer text, at `$chunk->content`.

**Content block.** The unit a message is actually made of. A message holds an ordered list of them: `TextContent`, `ReasoningContent`, `ImageContent`, `FileContent`, `AudioContent`, `VideoContent`.

**Context window.** The hard ceiling on system prompt + history + tool schemas + response. Exceeding it fails the request outright. Configure the trimmer 5–10 % below the model's real limit.

**Durable step.** A completed workflow node, committed to the workflow store with its result. After a crash or a pause, completed steps are replayed rather than re-run; only the node that was running re-executes.

**Embedding.** A list of numbers representing the meaning of a piece of text. Model-specific: changing the embeddings model invalidates every vector already stored.

**Eval.** A dataset of representative inputs run against an agent, scored by assertions rather than compared for equality. PHPUnit for a non-deterministic service.

**Event.** In a workflow, a plain class implementing `Event`. Nodes consume and return them, and the type hints on `__invoke` *are* the graph.

**Faithfulness.** Whether an answer is grounded in the retrieved context or invented. Measured with `FaithfulnessJudge`; the single most important assertion for a RAG system.

**HNSW.** Hierarchical Navigable Small World — the approximate nearest-neighbour index PHPVector uses for vector search.

**Human-in-the-loop.** A workflow that pauses mid-node, persists its entire execution state, waits for a human decision, and resumes from exactly where it stopped. NeuronAI's most distinctive capability.

**Hybrid search.** Combining vector similarity with keyword ranking. Not the same as *filtered search*, which restricts a vector search by metadata declared in a `DocumentSchema`.

**Interruption.** The mechanism behind human-in-the-loop. `$this->interrupt($request)` pauses the run; `run()` returns a state whose `isInterrupted()` is true. Nothing is thrown. You answer later with `resume($payload)->run()`, addressed by workflow ID.

**Memoization.** `$this->memoize('name', fn () => ...)` inside a workflow node. Stores the closure's result as part of the current step, so a node that re-executes after a pause or crash gets the stored value instead of running the closure again. Mandatory around any LLM call preceding an `interrupt()`.

**MCP — Model Context Protocol.** An open standard for exposing tools to AI systems. A server publishes tools; any MCP-capable client consumes them. Use `only()` on any server you do not control.

**Middleware.** Code attached to a workflow node class — `addMiddleware(InferenceNode::class, ...)`. Matching is by `instanceof`, which is why node class names are public API. Tool approval is *not* middleware in v4; it lives on the tool.

**Node.** A unit of a workflow: a class with `__invoke(Event, WorkflowState): Event`. Anything from one line of code to a complete agent.

**Non-determinism.** The property that makes the same input produce different output. Assume it even at temperature 0.

**Prompt injection.** Instructions arriving inside data the agent reads — a product description, a support ticket, a retrieved document, a third-party tool result. Defended against by removing capability, never by adding instructions.

**Provider.** An implementation of `AIProviderInterface`: Anthropic, OpenAI, Gemini, Mistral, Ollama and others. Swappable by configuration.

**RAG — retrieval-augmented generation.** Searching a knowledge base for passages relevant to a question and adding them to the prompt. Hands the model the relevant page; teaches it nothing.

**Reranking.** Re-scoring retrieved candidates with a model that reads the query and each document *together*. Retrieve 50, rerank, send 5 — the highest-return improvement to a working RAG system.

**Run ID.** A stamp identifying one generation of a workflow run, used with the execution attempt to fence a resume against stale deliveries. Not the resume handle — that is the *workflow ID*.

**Run limit.** `toolMaxRuns()` on an agent, `setMaxRuns()` on a tool. Defaults to 10 per tool. An exceeded limit is a diagnostic about tool design, not a number to raise.

**Score vs distance.** A similarity *score* of 1 means identical; a *distance* of 0 means identical. They run in opposite directions. Vector stores must return scores.

**Source name.** The `sourceName` metadata that makes `reindexBySource()` work. Must be stable — a record ID, never a title.

**Streaming.** Emitting the response as it is produced. Changes perceived latency, not actual latency, and lets you show what the agent is doing.

**Structured output.** `structured($message, MyClass::class)` — a typed, validated instance of your class rather than prose. Validation failure triggers a retry that tells the model exactly what was wrong.

**System prompt.** The instructions sent on every request. Not a greeting — the specification of the whole system. NeuronAI structures it as `background`, `steps`, `output`.

**Thread ID.** The identity of one conversation, passed as `Agent::make(threadId: ...)`. For an agent, the thread ID *is* the workflow ID, so one thread has at most one run in flight. Untrusted input: authorise it before use.

**Token.** Roughly ¾ of an English word. The unit you are billed in, and the unit your context window is measured in.

**Tool.** A function in your codebase that the model can ask you to run. The registered tool list is your security boundary — the only one you can rely on.

**Toolkit.** A coherent set of tools attached in one line, with a `guidelines()` method describing how they combine. Filter with `only()`.

**Trace.** A timeline of an agent execution: which node ran, which tool with which arguments, what came back, how many tokens, how long. Replaces debugging, which does not work here.

**Vector store.** Storage and similarity search for embeddings. Five methods — including `search(SearchRequest)` and `delete(FilterExpression)`, which is what makes reindexing by source work — and a `DocumentSchema` declaring which metadata can be filtered.

**Visibility.** `visible(false)` removes a tool from the schema entirely. Hiding beats instructing: prompt-based restrictions leak, are probabilistic, and are attackable.

**Workflow.** An event-driven graph of nodes with shared state, loops, branches, durable steps and interruption. The substrate the whole framework is built on — Agent and RAG *are* workflows.

**Workflow ID.** The business key of a workflow run — `refund:42`, or an agent's thread ID. Everything a run persists lives under it, and it is what you pass to resume.

**Workflow state.** The shared bag travelling through a run. Serialised at every step commit, not only on interruption, so it must hold no resources, connections or closures — store IDs and re-hydrate inside the node.
