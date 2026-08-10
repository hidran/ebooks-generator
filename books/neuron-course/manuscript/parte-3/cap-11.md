# Chapter 11 — Retrieval Theory

## 11.1 The Problem RAG Solves

### The gap

A language model knows what was in its training data. It does not know your company's return policy, your internal runbooks, last week's board minutes, or the specification of the product you shipped yesterday.

Ask it anyway and one of two things happens. It says it does not know, which is honest but useless. Or it produces something plausible and wrong, which is worse than useless.

### The definition

RAG is the process of providing references to a knowledge base outside the model's training data before generating a response.

The mechanism, at its simplest:

1. The user asks a question.
2. Your system searches a knowledge base for passages relevant to that question.
3. Those passages are added to the prompt.
4. The model answers using them.

The model has not learned anything. It has been handed the relevant page and asked to read it.

### Why this is cost-effective

The documentation makes the economic argument directly: RAG extends the capabilities of an LLM to a specific domain or an organisation's internal knowledge base **without retraining the model.**

That word — retraining — is the alternative, and it is worth quantifying:

| | RAG | Fine-tuning |
|---|---|---|
| Cost to set up | Hours | Days to weeks, plus compute |
| Cost to update | Re-index the changed document | Retrain |
| Update latency | Minutes | Days |
| Can cite sources | Yes | No |
| Works with any model | Yes | No — tied to what you tuned |
| Handles frequently changing data | Yes | No |

For "the model should know our documentation", RAG wins on every row. The interesting cases where fine-tuning wins are about *style and format*, not knowledge — Section 11.4 covers that properly.

### The other use, easy to miss

RAG is usually pitched as private-data access. But the same mechanism supplies **recent** information — current research, this quarter's statistics, today's news. The model's training cutoff is a knowledge boundary, and retrieval crosses it in the same way it crosses the boundary of your firewall.

### What RAG is not for

Worth stating now, because the confusion is expensive and Section 4.5 already set it up:

**Not for facts your database knows.** "How many orders did this customer place?" is SQL. A vector search over prose will give you an approximately right answer, which for a count is simply wrong.

**Not for user memory.** "Remember I'm vegetarian" is long-term memory, not knowledge retrieval.

**Not for reasoning.** RAG supplies facts. It does not make the model better at logic, arithmetic or planning.

**Not for small corpora.** If your entire knowledge base is 3,000 tokens, put it in the system prompt. No embeddings, no vector store, no pipeline. The infrastructure only earns its place when the corpus exceeds what you can afford to send every time.

That last one is the most commonly ignored, and it is the RAG equivalent of Section 1.1's "if you can draw the flowchart, build the flowchart".

### Key takeaways

- RAG hands the model the relevant page; it does not teach it anything.
- Cheaper than fine-tuning on every dimension that matters for knowledge.
- Also crosses the training-cutoff boundary, not just the firewall.
- Not for countable facts, user memory, reasoning, or corpora small enough to inline.

## 11.2 Embeddings and Similarity Search

### The intuition

An embedding is a list of numbers that represents the *meaning* of a piece of text. A typical model produces 768, 1024 or 1536 numbers per text.

The useful property: **texts with similar meaning produce similar number lists.**

"The cat sat on the mat" and "A feline rested on the rug" share almost no words. Their embeddings are close together. "The cat sat on the mat" and "Quarterly revenue increased by 12%" share the word "the". Their embeddings are far apart.

Keyword search sees the words. Embeddings see the meaning.

### Similarity search

Store the embedding of every chunk of your knowledge base. When a question arrives, embed the question and find the stored vectors closest to it.

That operation is what a **vector store** exists to do. NeuronAI's interface is exactly this:

```php
public function similaritySearch(array $embedding, int $k = 4): iterable;
```

Give it a vector, get back the `k` nearest documents. `k` — how many chunks to retrieve — is often called top-K, and it is one of the two knobs that most affect quality. The other is chunk size (Section 11.3).

### Scores, not distances

A detail NeuronAI makes explicit, and it prevents a real bug:

> `similaritySearch` should return documents with a similarity **score**, not a similarity **distance**.

These run in opposite directions. A distance of 0 means identical; a score of 1 means identical. Mix them up and your "best match" logic silently returns the worst results.

When a database returns distance, convert it:

```php
use NeuronAI\RAG\VectorSimilarity;

$document->setScore(
    VectorSimilarity::similarityFromDistance($distance)
);
```

Anyone implementing a custom store needs this. It is also a nice example of a framework encoding a convention to prevent a category of error.

### Three things that surprise people

**Embeddings are model-specific.** Vectors from OpenAI's model cannot be compared with vectors from Voyage's model. They are different coordinate systems. Change your embeddings provider and **you must re-embed your entire corpus.** Treat the embeddings model as part of your data schema, not as a swappable setting.

This is worth stating firmly because it is one of the few places where the interface-swap freedom of Section 3.6 does not apply. The interface swaps; the data does not follow.

**Dimensions must match the store.** If your embeddings model produces 1536 numbers and your vector store column is declared as 1024, nothing works. The MariaDB schema in the docs hardcodes `VECTOR(1536)` for exactly this reason.

**Similarity is not relevance.** Two chunks can be semantically close and only one of them answer the question. This is the gap that reranking exists to close (Section 12.7).

### Cost

Embedding is far cheaper than generation — typically a small fraction of the per-token price of a chat model. But you embed the whole corpus once and every query forever, so at scale it is a real line item.

**Ollama runs embedding models locally, free.** For every lab in this part, and for a great many production systems, a local embedding model is entirely adequate. Given that Section 3.6 already established Ollama, RAG can be learned end to end at zero cost.

### Key takeaways

- An embedding is a numeric representation of meaning; similar meanings sit close together.
- `similaritySearch($embedding, $k)` — top-K is one of the two quality knobs.
- Return scores, not distances; convert with `VectorSimilarity`.
- Embeddings are model-specific: changing the model means re-embedding everything.
- Local embedding models make RAG free to learn.

## 11.3 Chunking: The Decision That Determines Quality

This is the most consequential section in the chapter.

### Why split at all

Two reasons, and both matter:

**Retrieval precision.** If you embed an entire 40-page manual as one vector, that vector represents the average meaning of the whole manual — which is to say, almost nothing. A question about one paragraph will not match it well.

**Context budget.** You retrieve chunks to put in the prompt. A whole manual will not fit, and even if it did, Section 1.4's arithmetic says you would not want to pay for it on every turn.

So: split the document into pieces, embed each piece, retrieve the pieces that match.

### The core trade-off

The documentation states the principle plainly:

> The longer your units of text are, the less accurate the embeddings representation will be.

**Small chunks** — precise embeddings, accurate matching, but each retrieved piece may lack the context needed to be useful. You match the exact sentence and it turns out to be meaningless without the paragraph around it.

**Large chunks** — plenty of context, but blurry embeddings and wasted tokens. You retrieve 800 words to answer a question the model could have answered from 40.

There is no universally correct value. There is a correct value *for your content*, and finding it is empirical.

### The three parameters

**Max length.** How big a chunk can get. NeuronAI's default splitter uses 1,000 characters.

**Separator.** Where it is allowed to cut. The default is the period — sentence boundaries. But if your documents are Markdown with headed sections, cutting on `\n## ` produces chunks that align with the document's own semantic structure, which is almost always better than cutting on sentences.

That is the single most useful practical tip here: **match the separator to your content's structure**, do not accept the default because it is there.

**Overlap.** Words carried from the previous chunk into the next. The default is zero.

### Why overlap exists

The documentation describes it as increasing the semantic connection between adjacent sections. Concretely, it fixes this failure:

> Chunk 1: "...the refund window is 30 days from delivery."
>
> Chunk 2: "After this period, only store credit is available."

Chunk 2 alone is unanswerable — *after what period?* With overlap, chunk 2 begins with the tail of chunk 1 and carries its own context.

Cost: duplicated text means more chunks, more embedding calls, more storage. A reasonable starting point is 10–15 % of chunk size. Zero is right only when your chunks are genuinely independent — a FAQ where each entry stands alone, a product catalogue.

### Structure-aware chunking

The best chunking respects what the document *is*:

| Content | Split on |
|---|---|
| Markdown documentation | Headings (`##`) |
| FAQ | One chunk per question |
| Code | Function or class boundaries |
| Transcript | Speaker turns or timestamps |
| Legal text | Clause or article |
| Prose | Paragraphs, then sentences |

A custom splitter (Section 12.3) is often twenty lines and produces a bigger quality improvement than any amount of prompt tuning. This is the highest-leverage custom code in a RAG system, and it is worth saying explicitly — people expect the leverage to be in the prompt, and it usually is not.

### How to actually choose

Do not guess. Measure — and you already have the tool from Chapter 10.

1. Build a dataset of 20 real questions with known correct answers.
2. Index the corpus at three configurations (say 500/1000/2000 characters, 0/10/20 % overlap).
3. Run the evaluator against each, using `FaithfulnessJudge` and `CorrectnessJudge`.
4. Compare the scores.

This is why evals came before RAG in this book. Chunking is an empirical parameter, and without a measurement harness you are tuning by intuition.

### Key takeaways

- Split for retrieval precision and for context budget.
- Longer chunks mean blurrier embeddings — that is the core trade-off.
- Match the separator to your content's structure; do not accept the default.
- Overlap fixes chunks that are meaningless alone; start at 10–15 %.
- Choose parameters by evaluation, not by intuition.

## 11.4 RAG, Fine-Tuning, Context Stuffing and Tools

### The four options

**1. Context stuffing.** Put everything in the system prompt. Simple, exact, no infrastructure. Limited by the context window and paid for on every single request.

**2. RAG.** Retrieve relevant passages at query time. Scales to any corpus size, supports citation, updates by re-indexing.

**3. Tools.** Let the model query a live system. Exact, current, structured.

**4. Fine-tuning.** Train the model on your data. Expensive, slow to update, but changes the model's default behaviour.

### The decision table

| Situation | Mechanism |
|---|---|
| Under ~2,000 tokens of stable reference | Context stuffing |
| Large unstructured document corpus | RAG |
| Countable or queryable facts | Tools |
| Data that changes minute to minute | Tools |
| Needs to cite a source document | RAG |
| Consistent output style or format | Fine-tuning |
| Domain vocabulary the model misreads | Fine-tuning |
| "The model should know our policies" | RAG |
| "The model should sound like our brand" | Fine-tuning |

### The distinction people get wrong

**Fine-tuning teaches behaviour. RAG supplies facts.**

Fine-tuning a model on your documentation is a common and expensive mistake. The model learns the *shape* of your writing — the vocabulary, the register, the structure — but it does not reliably learn the facts, and when your documentation changes you have to do it all again. Meanwhile you cannot cite anything, because there is nothing to cite.

If someone says "we want the model to know our product", they want RAG. If they say "we want it to write like our support team", that is fine-tuning territory — and even then, a good system prompt with three examples gets most of the way there for a fraction of the cost.

### The other distinction people get wrong

**RAG for prose. Tools for records.**

This is Section 4.5's point, and it deserves repeating here because this is where the mistake is made.

- *"What is our refund policy?"* → RAG. It is written in a document.
- *"Has order 4471 been refunded?"* → Tool. It is a row in a table.
- *"Which customers had a refund last month?"* → Tool. It is a query.

Indexing your orders table into a vector store to answer the second question is a design error that produces confidently approximate answers. Vector search retrieves things that *look similar*; it does not compute.

### They compose

The best systems use several. Section 12.1 shows the framework supports this directly: a `RAG` class **is** an `Agent`, so it can have tools.

The documented example is well chosen — a workout-tips agent with a knowledge base of exercise information (RAG) plus a tool that reads the user's current training status from the database (tool calling). Prose from retrieval, facts from the tool, one answer.

### Key takeaways

- Four mechanisms: stuffing, RAG, tools, fine-tuning.
- Fine-tuning changes behaviour; RAG supplies facts.
- RAG for prose, tools for records — the most common and most expensive confusion.
- Under ~2,000 stable tokens, skip the infrastructure entirely.
- Real systems combine them; NeuronAI's RAG-is-an-Agent design supports that directly.

## 11.5 The Limits of Naive RAG

### Naive RAG

Embed the question, retrieve top-K, stuff into the prompt, generate. It works surprisingly well, and then it fails in specific, recognisable ways. Knowing the six is the difference between diagnosing a problem and concluding "AI does not work".

### Failure 1 — The question does not look like the answer

The user asks *"Why is my thing broken?"* The document says *"Error code 4021 indicates insufficient disk allocation on the primary volume."*

Semantically distant. The retrieval misses.

**Fix:** query transformation. Rewrite or expand the question before embedding it — NeuronAI ships `QueryTransformationPreProcessor` for exactly this, and it runs in `PreProcessQueryNode` (Section 12.7).

### Failure 2 — Similar is not relevant

You retrieve five chunks, all about refunds. Only one covers the 30-day window the user asked about. The other four are noise, and noise costs tokens and can distract the model into answering from the wrong passage.

**Fix:** reranking. Retrieve broadly, then re-score with a model that reads the query and each document together. Section 12.7.

### Failure 3 — The answer spans chunks

*"How do our refund and shipping policies interact for international orders?"* Refunds are in one document, shipping in another, the international exception in a third. Top-K retrieval on one query finds one of them.

**Fix:** multi-query retrieval, or a higher K plus reranking. Genuinely hard — this is where naive RAG shows its edges.

### Failure 4 — Aggregation questions

*"How many articles mention GDPR?"* Vector search retrieves the *most similar* documents, not *all matching* documents. There is no counting operation.

**Fix:** this is not a RAG question. Use a tool, or metadata filtering with a hybrid search. Recognising it is the fix.

### Failure 5 — Confident hallucination

The retrieval returns nothing useful, and the model answers anyway from its general knowledge — fluently, plausibly, wrongly.

**This is the most dangerous failure**, because it looks exactly like success.

**Fix, in three parts:**

1. **Instruct explicitly.** In the `background` section: *"Answer only from the provided documents. If they do not contain the answer, say so."*
2. **Measure it.** `FaithfulnessJudge` from Section 10.5 exists for precisely this. It is the reason evals came first.
3. **Cite.** Require the answer to reference the source document. A citation the user can check converts an invisible failure into a visible one.

### Failure 6 — Stale index

Someone updates the policy document. The vector store still holds last quarter's chunks. The agent answers confidently from outdated information.

**Fix:** reindexing, which NeuronAI addresses with `reindexBySource()` (Section 12.6). Also an operational question: what triggers a re-index, and how do you know it ran?

### The honest summary

Naive RAG gets you perhaps 70 % of the way. The remaining 30 % is query transformation, reranking, metadata filtering, hybrid search and evaluation — which is exactly why NeuronAI's pipeline has pre-processors and post-processors as first-class stages rather than as an afterthought.

Anyone who believes RAG is "embed and retrieve" will ship something that demonstrates beautifully and disappoints in week two. Knowing the six failure modes is what lets you recognise what you are looking at.

### Key takeaways

- Six failure modes: query mismatch, irrelevant-but-similar, cross-chunk answers, aggregation, hallucination, staleness.
- Confident hallucination is the most dangerous because it resembles success.
- Instruct, measure with `FaithfulnessJudge`, and cite.
- Naive RAG is ~70 %; the pipeline stages are the rest.
