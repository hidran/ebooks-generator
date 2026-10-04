# Part V — Laravel

Everything so far has run from a CLI script, by design. Now it moves into an application with users, a database, a queue, an HTTP layer and a bill.

The NeuronAI Laravel SDK supplies part of the plumbing — configuration, component facades, generators — and the application supplies the rest: a service provider, one migration, an Eloquent-backed message store. Chapters 17 and 18 cover both quickly, because the interesting problems are not the plumbing.

The interesting problems are the ones only production has. Tools that touch your real models and must not be tricked into touching the wrong tenant's. Retrieval over data that changes constantly and has to be reindexed without a maintenance window. Streaming tokens to a browser over SSE and Livewire while a queue worker does the actual work. Approval workflows that survive a deploy happening between the request and the manager's decision. Costs that scale with user behaviour rather than user count. Providers that rate-limit you at the worst possible moment. Prompt injection arriving through your own support inbox.

Chapter 23 ends with a deployment checklist and the question this book is really about: what is the worst thing your agent can do, and what stops it?
