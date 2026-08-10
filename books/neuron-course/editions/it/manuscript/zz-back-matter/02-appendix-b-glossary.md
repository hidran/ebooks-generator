# Appendice B — Glossario {.unnumbered}

**Agent.** Quarto piolo della scala dell'autonomia: il modello decide quale azione intraprendere dopo, e il ciclo continua finché non decide di aver finito. In NeuronAI, una classe che estende `Agent` — che è a sua volta un Workflow preconfigurato.

**Ciclo dell'agent.** Il ciclo che chiama il modello, esegue gli eventuali tool che richiede, gli rimanda indietro i risultati e ripete finché il modello non restituisce prosa invece di una chiamata a un tool. Senza limiti per default; protetto con i limiti di esecuzione.

**Scala dell'autonomia.** I quattro pioli della Sezione 1.1 — chiamata nuda a un LLM, chatbot, workflow, agent — distinti da *chi decide che cosa succede dopo*.

**BM25.** Una funzione classica di ranking per parole chiave. PHPVector la combina con la ricerca vettoriale per ottenere un recupero ibrido.

**Checkpoint.** `$this->checkpoint('name', fn () => ...)` dentro un nodo di workflow. Salva il risultato della closure così che un nodo ripreso non la riesegua. Obbligatorio attorno a qualunque chiamata a un LLM che preceda un `interrupt()`.

**Chunk.** Un pezzo di documento, prodotto da uno splitter e sottoposto a embedding in modo indipendente. La dimensione del chunk e il separatore sono i due parametri che più influiscono sulla qualità del recupero.

**Oggetto chunk.** Nello streaming, un oggetto prodotto da `events()` — `TextChunk`, `ReasoningChunk`, `ToolCallChunk`, `ToolResultChunk`. Il testo vive in `$chunk->content`, non nel chunk stesso.

**Blocco di contenuto.** L'unità di cui un messaggio è davvero fatto. Un messaggio ne contiene una lista ordinata: `TextContent`, `ReasoningContent`, `ImageContent`, `FileContent`, `AudioContent`, `VideoContent`.

**Context window.** Il tetto rigido su system prompt + cronologia + schemi dei tool + risposta. Superarlo fa fallire la richiesta di netto. Configura il trimmer al 5–10 % sotto il limite reale del modello.

**Embedding.** Una lista di numeri che rappresenta il significato di un pezzo di testo. Specifico del modello: cambiare il modello di embedding invalida ogni vettore già salvato.

**Eval.** Un dataset di input rappresentativi eseguito contro un agent, valutato con asserzioni invece che confrontato per uguaglianza. PHPUnit per un servizio non deterministico.

**Evento.** In un workflow, una semplice classe che implementa `Event`. I nodi li consumano e li restituiscono, e i type hint su `__invoke` *sono* il grafo.

**Fedeltà.** Se una risposta è ancorata al contesto recuperato o inventata. Misurata con `FaithfulnessJudge`; l'asserzione più importante in assoluto per un sistema RAG.

**HNSW.** Hierarchical Navigable Small World — l'indice approssimato per i vicini più prossimi che PHPVector usa per la ricerca vettoriale.

**Human-in-the-loop.** Un workflow che si mette in pausa a metà nodo, persiste tutto il suo stato di esecuzione, aspetta una decisione umana e riprende esattamente da dove si era fermato. La capacità più distintiva di NeuronAI.

**Ricerca ibrida.** Combinare la somiglianza vettoriale con la corrispondenza per parole chiave, il filtraggio sui metadati, o entrambi.

**Interruzione.** Il meccanismo dietro all'human-in-the-loop. `$this->interrupt($request)` lancia una `WorkflowInterrupt`, che tu catturi, persisti e più tardi riprendi.

**MCP — Model Context Protocol.** Uno standard aperto per esporre tool ai sistemi AI. Un server pubblica tool; qualunque client capace di MCP li consuma. Usa `only()` su qualunque server che non controlli.

**Middleware.** Codice agganciato a un nodo di workflow con un nome — `Neuron::middleware(ToolNode::class, ...)`. Il motivo per cui i nomi delle classi dei nodi sono API pubblica.

**Nodo.** Un'unità di un workflow: una classe con `__invoke(Event, WorkflowState): Event`. Qualunque cosa, da una riga di codice a un agent completo.

**Non determinismo.** La proprietà per cui lo stesso input produce output diversi. Dallo per scontato anche a temperatura 0.

**Prompt injection.** Istruzioni che arrivano dentro dati che l'agent legge — la descrizione di un prodotto, un ticket di supporto, un documento recuperato, il risultato di un tool di terze parti. Ci si difende togliendo la capacità, mai aggiungendo istruzioni.

**Provider.** Un'implementazione di `AIProviderInterface`: Anthropic, OpenAI, Gemini, Mistral, Ollama e altri. Sostituibile via configurazione.

**RAG — retrieval-augmented generation.** Cercare in una knowledge base i passaggi rilevanti per una domanda e aggiungerli al prompt. Passa al modello la pagina giusta; non gli insegna nulla.

**Reranking.** Rivalutare i candidati recuperati con un modello che legge la query e ciascun documento *insieme*. Recupera 50, rifai il ranking, mandane 5 — il miglioramento con il maggior ritorno su un sistema RAG funzionante.

**Limite di esecuzione.** `toolMaxRuns()` su un agent, `setMaxRuns()` su un tool. Per default 10 per tool. Un limite superato è una diagnostica sul progetto dei tool, non un numero da alzare.

**Punteggio contro distanza.** Un *punteggio* di somiglianza pari a 1 significa identico; una *distanza* di 0 significa identico. Corrono in direzioni opposte. I vector store devono restituire punteggi.

**Nome della sorgente.** Il metadato `sourceName` che fa funzionare `reindexBySource()`. Deve essere stabile — l'ID di un record, mai un titolo.

**Streaming.** Emettere la risposta mentre viene prodotta. Cambia la latenza percepita, non quella reale, e ti permette di mostrare che cosa sta facendo l'agent.

**Structured output.** `structured($message, MyClass::class)` — un'istanza tipizzata e validata della tua classe invece che prosa. Il fallimento della validazione innesca un ritentativo che dice al modello esattamente che cosa non andava.

**System prompt.** Le istruzioni inviate a ogni richiesta. Non un saluto — la specifica dell'intero sistema. NeuronAI lo struttura in `background`, `steps`, `output`.

**Token.** Grosso modo tre quarti di una parola inglese. L'unità in cui vieni fatturato, e l'unità in cui si misura la tua context window.

**Tool.** Una funzione nel tuo codebase che il modello può chiederti di eseguire. L'elenco dei tool registrati è il tuo confine di sicurezza — l'unico su cui puoi fare affidamento.

**Toolkit.** Un insieme coerente di tool agganciato in una riga, con un metodo `guidelines()` che descrive come si combinano. Filtralo con `only()`.

**Trace.** La linea temporale dell'esecuzione di un agent: quale nodo è girato, quale tool con quali argomenti, che cosa è tornato indietro, quanti token, quanto tempo. Sostituisce il debug, che qui non funziona.

**Vector store.** Archiviazione e ricerca per somiglianza degli embedding. Quattro metodi; `deleteBySource` esiste perché la reindicizzazione funzioni.

**Visibilità.** `visible(false)` rimuove del tutto un tool dallo schema. Nascondere batte istruire: le restrizioni basate sul prompt trapelano, sono probabilistiche e sono attaccabili.

**Workflow.** Un grafo di nodi guidato dagli eventi con stato condiviso, cicli, diramazioni, checkpoint e interruzione. Il substrato su cui è costruito l'intero framework — Agent e RAG *sono* workflow.

**Stato del workflow.** Il contenitore condiviso che viaggia lungo un'esecuzione. Serializzato all'interruzione, quindi non deve contenere risorse, connessioni o closure — salva gli ID e reidrata dentro il nodo.
