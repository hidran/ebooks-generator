# Part I — Foundations

There is no code in this part.

That is a deliberate cost. Two chapters of theory before the first `composer require` is a long time to ask a working developer to wait, and the payoff has to be worth it. It is, for one reason: almost every expensive mistake in agentic software is made at design time, before anybody opens an editor.

Chapter 1 builds a four-rung ladder of autonomy and puts a single question at the centre of it — who decides what happens next. It then does the arithmetic nobody does in advance, showing why a five-step agent costs roughly twelve times a single model call, and why non-determinism means your usual testing instincts do not transfer.

Chapter 2 opens up NeuronAI itself: the four pillars it is built on, the interfaces that make providers and stores interchangeable, and the structural insight the official documentation reveals far too late — that Agent and RAG *are* Workflows. Knowing that on day one changes how you build everything afterwards.

Read these two chapters properly. They are the ones that will stop you from building the wrong thing.
