# Part III — Retrieval

A model knows what was in its training data and what you put in the prompt. Nothing else. It does not know your product catalogue, your internal wiki, your ticket history, or anything that happened after its cutoff.

Retrieval-augmented generation is the standard answer, and it is widely misunderstood as "give the model your documents". What it actually is: a search problem wearing a generation problem's clothes. Almost every disappointing RAG system is disappointing because the retrieval is bad, not because the model is.

Chapter 11 covers the theory and, just as importantly, what retrieval does not solve — the questions it will always answer badly, and the cases where you should be querying a database instead.

Chapter 12 builds the NeuronAI pipeline end to end: loaders, splitters, embedding providers, vector stores, metadata filtering, reindexing when your documents change, and the pre- and post-processors that separate a demo from something you would let a customer use.

Both labs run at zero cost on local embeddings.
