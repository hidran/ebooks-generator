# Part IV — Workflows

An agent decides its own control flow. That is its power, and in production it is also the problem: you cannot promise a customer that an autonomous loop will follow a compliance process.

Workflows are the answer. You author the graph; the model fills in the nodes. The result is deterministic where it must be and intelligent where it helps, which describes most valuable business software.

Chapter 13 introduces the event-driven model NeuronAI uses. Chapter 14 adds loops, branches and typed state. Chapter 15 covers the feature that makes workflows genuinely production-grade: interruption. A workflow can stop mid-execution, persist a checkpoint, wait however long a human needs, and resume.

Chapter 15 also contains the single most important correctness warning in this book. A resumed node re-executes from the top, so an LLM call that was not checkpointed will produce *different content from the one the human approved*. It is a one-line fix and an audit failure if you miss it.

Chapter 16 puts several agents in one system and makes them hand work to each other.
