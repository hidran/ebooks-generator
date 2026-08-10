# Glossary (agentic-ai-php-neuron)

Terms to keep consistent across the EN, IT and ES editions.

## Invariant — never translated, never altered

These are product, package, class, command and vendor names. They appear identically in
every edition, including inside prose.

`NeuronAI` · `neuron-core/neuron-ai` · `neuron-core/neuron-laravel` · `vendor/bin/neuron` ·
Laravel · Composer · Eloquent · Livewire · Ollama · Inspector · MCP · PHPVector · MariaDB ·
Pinecone · Weaviate · Elasticsearch · OpenSearch · Typesense · Qdrant · ChromaDB ·
Meilisearch · OpenAI · Anthropic · Gemini · HNSW · BM25 · SSE · JSON · YAML · HTTP

All PHP identifiers, namespaces, method names, file paths, environment variables, shell
commands and URLs are copied verbatim, in prose as well as in code.

> **Note.** The library is **NeuronAI**. The word "Neuron" alone is never used for it in
> any edition. The Composer package is still `neuron-core/neuron-ai` and the CLI is still
> `vendor/bin/neuron`; those are names, not prose, and stay as they are.

## The two editions borrow differently

Italian technical prose absorbs English vocabulary wholesale; Spanish translates it. The
two editions therefore diverge on purpose, and each is internally consistent rather than
consistent with the other.

**`agent`.** Italian keeps the English word (`l'agent`, `gli agent`); Spanish translates it
(`el agente`, `los agentes`), which is what the ES title and subtitle in `book.yaml`
already use. Likewise `multi-agent` → IT `multi-agente`, ES `multiagente`.

The PHP class `Agent`, the namespace `NeuronAI\Agent\Agent` and every other identifier stay
verbatim in all editions, in prose as well as in code.

## Kept in English — Italian edition

Entrenched industry vocabulary. Translating these makes the text harder to read for an
audience that has to search the documentation afterwards.

prompt · token · tool · tool call · workflow · embedding · chunk · context window ·
streaming · chunk object · checkpoint · human-in-the-loop · deploy · endpoint · provider ·
toolkit · observability · trace · evaluation · retrieval · store · loader · splitter ·
system prompt · structured output · rate limit · queue · worker

These keep the English gender-neutral form and take the article of the grammatical gender
assigned below, used consistently:

| Term | IT |
|---|---|
| agent | l'agent (m.) |
| tool | il tool (m.) |
| workflow | il workflow (m.) |
| prompt | il prompt (m.) |
| token | il token (m.) |
| embedding | l'embedding (m.) |
| chunk | il chunk (m.) |
| checkpoint | il checkpoint (m.) |
| provider | il provider (m.) |
| toolkit | il toolkit (m.) |

## Kept in English — Spanish edition

Only these. Everything else is translated.

`prompt` · `token` · `middleware` · MCP · RAG · LLM · API · SDK

`prompt` and `token` have no settled Spanish equivalent in AI writing. `middleware` is the
Laravel API's own word for the thing, and a reader searching the Laravel documentation in
Spanish will find it under that name. The rest are acronyms.

## Spanish renderings — fixed

Every term below is translated in the ES edition wherever it appears in prose. Inside code,
and inside inline `backticks` naming an identifier, nothing changes.

| EN | ES | gender |
|---|---|---|
| tool | herramienta | f. |
| tool call | llamada a herramienta | f. |
| toolkit | juego de herramientas | m. |
| workflow | flujo de trabajo | m. |
| provider | proveedor | m. |
| chunk | fragmento | m. |
| chunk object | objeto de fragmento | m. |
| embedding | incrustación | f. |
| streaming | transmisión | f. |
| to stream | transmitir | — |
| trace | traza | f. |
| store | almacén | m. |
| vector store | almacén vectorial | m. |
| checkpoint | punto de control | m. |
| handler | gestor | m. |
| splitter | divisor | m. |
| loader | cargador | m. |
| worker | proceso | m. |
| reranking | reordenación | f. |
| context window | ventana de contexto | f. |
| structured output | salida estructurada | f. |
| system prompt | prompt de sistema | m. |
| prompt injection | inyección de prompts | f. |
| endpoint | punto de conexión | m. |
| deploy / deployment | desplegar / despliegue | m. |
| queue | cola | f. |
| observability | observabilidad | f. |
| evaluation | evaluación | f. |
| retrieval | recuperación | f. |
| rate limit | límite de tasa | m. |
| guardrail | salvaguarda | f. |
| fallback | respaldo | m. |
| event-driven | guiado por eventos | — |
| multi-tenancy | multiinquilino | — |
| pre-processor / post-processor | preprocesador / posprocesador | m. |

## Translated — fixed renderings

| EN | IT | ES |
|---|---|---|
| agentic | agentico | agéntico |
| the agent loop | il ciclo dell'agent | el bucle del agente |
| autonomy ladder | scala dell'autonomia | escalera de autonomía |
| control flow | flusso di controllo | flujo de control |
| non-determinism | non determinismo | no determinismo |
| chat history | cronologia della conversazione | historial de conversación |
| long-term memory | memoria a lungo termine | memoria a largo plazo |
| session memory | memoria di sessione | memoria de sesión |
| vector store | vector store | almacén vectorial |
| retrieval-augmented generation | retrieval-augmented generation | generación aumentada por recuperación |
| pre-processor / post-processor | pre-processor / post-processor | preprocesador / posprocesador |
| reindexing | reindicizzazione | reindexación |
| event-driven | event-driven | guiado por eventos |
| branching | diramazione | ramificación |
| state | stato | estado |
| interruption | interruzione | interrupción |
| approval | approvazione | aprobación |
| guardrail | guardrail | salvaguarda |
| multimodality | multimodalità | multimodalidad |
| attachment | allegato | adjunto |
| dependency injection | dependency injection | inyección de dependencias |
| multi-tenancy | multi-tenancy | multiinquilino |
| resilience | resilienza | resiliencia |
| deployment checklist | checklist di deploy | checklist de despliegue |
| capstone | progetto finale | proyecto final |
| lab | laboratorio | laboratorio |
| key takeaways | punti chiave | puntos clave |
| in practice | in pratica | en la práctica |
| Part | Parte | Parte |
| Chapter | Capitolo | Capítulo |
| Appendix | Appendice | Apéndice |
| Preface | Prefazione | Prefacio |
| How to use this book | Come usare questo libro | Cómo usar este libro |
| Glossary | Glossario | Glosario |
| Colophon | Colophon | Colofón |
