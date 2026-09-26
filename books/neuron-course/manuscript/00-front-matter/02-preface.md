# Preface {.unnumbered}

## One question

Every idea in this book descends from a single question:

> **Who decides what happens next?**

When you call a language model to summarise a support ticket, your code decides. It decides what to send, when to send it, and what to do with the answer. The model produces text and nothing else.

When you build an agent, you hand that decision to the model. You give it a goal and a set of capabilities, and it chooses which capability to use, sees the result, chooses again, and keeps going until it decides it is finished. You did not write that sequence. It emerged.

That transfer of control is the whole subject. Everything else in this book — memory, tools, structured output, retrieval, workflows, human approval, observability — exists to make that transfer survivable in production. Give a model the ability to act and you inherit a set of problems that ordinary PHP does not have: you cannot predict what a request will cost, you cannot unit test the flow deterministically, and when it misbehaves you need a trace to find out why it chose the wrong tool at step four.

This book is about earning that power deliberately, and about knowing when not to.

## Why PHP

The agentic AI conversation has been conducted almost entirely in Python. That is an accident of research history, not a statement about where the work is. An enormous share of the world's business logic — the CRMs, the invoicing systems, the booking engines, the internal tools that quietly run companies — is written in PHP, and it is already sitting next to the database, the queue, the auth layer and the users who would benefit from an agent.

Bolting a Python microservice onto a Laravel application to call an LLM is a real architectural decision with real costs: another runtime, another deployment, another set of credentials, another network hop, and a copy of your domain model that will drift. Sometimes it is the right call. Often it is not, and the only reason it happens is that nobody showed the PHP team the alternative.

**NeuronAI** is the alternative. It is a PHP framework for building agents — installed as `neuron-core/neuron-ai`, documented at neuron-ai.dev — and it is the subject of this book. It covers the same ground as the well-known Python frameworks: providers, tools, memory, structured output, retrieval-augmented generation, event-driven workflows, human-in-the-loop interruption, observability. It does it with interfaces, dependency injection and typed classes, in a way that will feel unremarkable to anyone who has used a modern PHP framework, which is exactly the point.

A note on the name, because the ecosystem is inconsistent about it. The library is **NeuronAI**. The Composer package is `neuron-core/neuron-ai`, the CLI binary is `vendor/bin/neuron`, and the root namespace is `NeuronAI\`. This book says NeuronAI in prose and leaves every package name, command and namespace exactly as you must type it.

## Who this book is for

You write PHP. You are comfortable with Composer, namespaces, interfaces and a modern IDE. You have probably used Laravel, though Parts I to IV do not require it — they run on plain PHP and a CLI script, deliberately, so that you can see every moving part before a framework hides any of them.

You do not need to know anything about machine learning. There is no maths in this book beyond arithmetic about cost. You do not need to have called an LLM API before. What you do need is the instinct that makes a good backend developer suspicious of magic, because that instinct is the one this book rewards.

If you have already built something with an LLM and found it unreliable, expensive or impossible to debug, you are the reader this book was written for. Those three failures have causes, and the causes have names.

## What you will build

The book alternates theory, plain PHP, and Laravel, in that order, and it builds continuously rather than in disconnected snippets.

By the end of Part II you will have an agent running from a CLI script with tools it wrote no code to invoke, a chat history that survives restarts, typed and validated output, streaming responses, image and document understanding, an MCP connection to external tool servers, and a trace of everything it did.

By the end of Part IV you will have a retrieval pipeline over your own documentation, event-driven workflows that loop and branch, workflows that pause mid-execution for a human to approve an action and resume from a checkpoint afterwards, and a multi-agent system where specialised agents hand work to each other.

By the end of Part V, all of it is inside a Laravel application: facades and dependency injection, conversation history in Eloquent, tools that touch your real models, retrieval over your application's own data, per-tenant isolation, token streaming over SSE and Livewire, approval workflows that queue and notify, cost controls, rate-limit resilience, prompt-injection defences, and a deployment checklist.

Part VI is three capstone projects — a repository auditor as a plain PHP CLI, an agentic support desk in Laravel, and a trip planner that chooses a destination from real weather data and books it with a human approving every step, built in full, one decision at a time — plus three chapters on the things nobody tells you: how to pick a version and survive it, what the ecosystem around the framework actually offers, and how to use AI assistance to write this kind of code without letting it write the parts that matter.

## About the code

Every code sample here was written against **NeuronAI v4** and, for Part V, the **NeuronAI Laravel SDK 2.x** that pairs with it. PHP 8.2 or later is assumed throughout. Every sample was also run: the companion repository executes them in CI, and a contract test suite pins every class and signature the book depends on.

This matters more than usual. v4 is a deep release: the workflow engine underneath everything became durable, a human-approval pause became a return value instead of an exception, and tool approval moved from a middleware onto the tool itself. Most NeuronAI code you will find online was written for v3, and much of it will not run on v4. Earlier still, NeuronAI changed namespaces between v1/v2 and v3 — `NeuronAI\Agent` became `NeuronAI\Agent\Agent`, `NeuronAI\SystemPrompt` became `NeuronAI\Agent\SystemPrompt` — and a great deal of published material, including parts of the official documentation, has not caught up. A tutorial that was correct two years ago will now fail on its first `use` statement.

The official documentation also disagrees with the code, and with itself, in dozens of places: method signatures the code dropped a release ago, three different constructor signatures for the same vector store, three generations of workflow execution API, misspelled class names, and two upgrade guides in the same package that disagree about which ID resumes a workflow. Every one of those produces an error for someone who copies the page.

**Appendix A** is the list. All seventy-six items — including six genuine code defects found while verifying the book — grouped by the chapter they affect, with a set of short probe scripts that settle whole clusters of them at once against the version you actually have installed. Working through it takes an afternoon and it is the single highest-value thing you can do before writing production code with this library. Start there if you are the kind of person who reads appendices first.

Every lab in Parts II through IV is designed to run **free and offline** on Ollama with a local model. You will need paid API credentials only where the exercise genuinely depends on frontier-model quality, and the book says so explicitly each time.

## The question this book is really asking

The last chapter closes with a question you should be able to answer about anything you deploy after reading this:

> **What is the worst thing your agent can do, and what stops it?**

If you cannot answer it, you have not finished building.

*Hidran Arias, 2026*
