# Appendice B — Glossario {.unnumbered}

**Agent.** Quarto piolo della scala dell'autonomia: il modello decide quale azione intraprendere dopo, e il ciclo continua finché non decide di aver finito. In NeuronAI, una classe che estende `Agent` — che è a sua volta un Workflow preconfigurato.

**Approval policy.** La dichiarazione con cui è il tool stesso a stabilire che una chiamata richiede un essere umano: l'hook protetto `approvalPolicy()`, che restituisce `false`, `true` o una stringa con il motivo. Sovrascritta per singola istanza con `requireApproval()`, `suppressApproval()` o `withApprovalPolicy()`. Vi si risponde sull'agent con `submitApprovalDecisions()`, che restituisce una pending execution da completare con `->run()`.

**Blocco di contenuto.** L'unità di cui un messaggio è davvero fatto. Un messaggio ne contiene una lista ordinata: `TextContent`, `ReasoningContent`, `ImageContent`, `FileContent`, `AudioContent`, `VideoContent`.

**BM25.** Una funzione classica di ranking per parole chiave: valuta un documento in base a quante volte vi compaiono i termini della query, pesando ciascun termine per la sua rarità. La ricerca ibrida la combina con la ricerca vettoriale.

**Checkpoint.** Il nome precedente alla v4 della *memoizzazione*. `checkpoint()` esiste ancora, deprecato, e chiama `memoize()`.

**Chiave di idempotenza.** Un valore che identifica un singolo effetto voluto, così che ripetere la richiesta non ripeta l'effetto: viene salvato insieme alla scrittura e controllato prima. È ciò che rende sicuro un tool di scrittura rieseguito o rigiocato.

**Chunk.** Un pezzo di documento, prodotto da uno splitter e sottoposto a embedding in modo indipendente. La dimensione del chunk e il separatore sono i due parametri che più influiscono sulla qualità del recupero.

**Ciclo dell'agent.** Il ciclo che chiama il modello, esegue gli eventuali tool che richiede, gli rimanda indietro i risultati e ripete finché il modello non restituisce prosa invece di una chiamata a un tool. Senza limiti per default; protetto con i limiti di esecuzione.

**Context window.** Il tetto rigido su system prompt + cronologia + schemi dei tool + risposta. Superarlo fa fallire la richiesta di netto. Configura il trimmer al 5–10 % sotto il limite reale del modello.

**Embedding.** Una lista di numeri che rappresenta il significato di un pezzo di testo. Specifico del modello: cambiare il modello di embedding invalida ogni vettore già salvato.

**Eval.** Un dataset di input rappresentativi eseguito contro un agent, valutato con asserzioni invece che confrontato per uguaglianza. PHPUnit per un servizio non deterministico.

**Evento.** In un workflow, una semplice classe che implementa `Event`. I nodi li consumano e li restituiscono, e i type hint su `__invoke` *sono* il grafo.

**Fedeltà.** Se una risposta è ancorata al contesto recuperato o inventata. Misurata con `FaithfulnessJudge`; l'asserzione più importante in assoluto per un sistema RAG.

**Fence.** Una guardia che respinge una continuazione non più valida: una ripresa o un segnale porta con sé il run ID (e il tentativo di esecuzione) che si aspetta, e il motore la rifiuta se la run è andata avanti. Un run ID non più valido lancia `StaleWorkflowRunException`; un tentativo non più valido lancia una semplice `WorkflowException`.

**HNSW.** Hierarchical Navigable Small World — un indice a grafo, approssimato, per i vicini più prossimi, che permette a uno store vettoriale di cercare tra gli embedding senza confrontare la query con ogni vettore.

**Human-in-the-loop.** Un workflow che si mette in pausa a metà nodo, persiste tutto il suo stato di esecuzione, aspetta una decisione umana e riprende esattamente da dove si era fermato. La capacità più distintiva di NeuronAI.

**Interruzione.** Il meccanismo dietro all'human-in-the-loop. `$this->interrupt($request)` mette in pausa la run; `run()` restituisce uno stato il cui `isInterrupted()` è true. Non viene lanciato nulla. Rispondi più tardi con `submitInputs($payload)->run()` (o `run(ExecutionRequest::resume($payload))`) sull'istanza associata allo stesso workflow ID.

**Lease.** Un limite di tempo su un tentativo di esecuzione in corso: se non fa progressi entro la scadenza (`setLeaseTimeout()`), la run è considerata abbandonata e una ripresa può rilevarla. Un agent ha per default un lease di dieci minuti; una run in pausa non ne detiene alcuno.

**Limite di esecuzione.** `toolMaxRuns()` su un agent, `setMaxRuns()` su un tool. Per default 10 per tool. Un limite superato è una diagnostica sul progetto dei tool, non un numero da alzare.

**MCP — Model Context Protocol.** Uno standard aperto per esporre tool ai sistemi AI. Un server pubblica tool; qualunque client capace di MCP li consuma. Usa `only()` su qualunque server che non controlli.

**Memoizzazione.** `$this->memoize('name', fn () => ...)` dentro un nodo di workflow. Memorizza il risultato della closure come parte dello step corrente, così un nodo che viene rieseguito dopo una pausa o un crash ottiene il valore memorizzato invece di eseguire di nuovo la closure. Obbligatoria attorno a qualunque chiamata a un LLM che preceda un `interrupt()`.

**Message store.** L'archivio dietro la cronologia di un agent, dietro `MessageStoreInterface`: `InMemoryMessageStore`, `FileMessageStore`, `SQLMessageStore`, `EloquentMessageStore`. Non conosce alcun thread: i messaggi li seleziona il thread ID dell'agent. Il trimming archivia i messaggi vecchi (`archived_at`) invece di cancellarli.

**Middleware.** Codice agganciato a una classe di nodo di workflow — `addMiddleware(InferenceNode::class, ...)`. La corrispondenza avviene tramite `instanceof`, ed è per questo che i nomi delle classi dei nodi sono API pubblica. L'approvazione dei tool *non* è un middleware, qualunque cosa mostrino i tutorial più vecchi; vive sul tool.

**Nodo.** Un'unità di un workflow: una classe con `__invoke(Event, WorkflowState): Event`, più un terzo parametro opzionale `WorkflowResources`. Qualunque cosa, da una riga di codice a un agent completo.

**Nome della sorgente.** Il metadato `sourceName` che fa funzionare `reindexBySource()`. Deve essere stabile — l'ID di un record, mai un titolo.

**Non determinismo.** La proprietà per cui lo stesso input produce output diversi. Dallo per scontato anche a temperatura 0.

**Oggetto chunk.** Nello streaming, un oggetto prodotto da `stream()` — `TextChunk`, `ReasoningChunk`, `ToolCallChunk`, `ToolResultChunk` e alcuni tipi più rari. Solo `TextChunk` porta il testo della risposta, in `$chunk->content`.

**Prompt injection.** Istruzioni che arrivano dentro dati che l'agent legge — la descrizione di un prodotto, un ticket di supporto, un documento recuperato, il risultato di un tool di terze parti. Ci si difende togliendo la capacità, mai aggiungendo istruzioni.

**Provider.** Un'implementazione di `AIProviderInterface`: Anthropic, OpenAI, Gemini, Mistral, Ollama e altri. Sostituibile via configurazione.

**Punteggio contro distanza.** Un *punteggio* di somiglianza pari a 1 significa identico; una *distanza* di 0 significa identico. Corrono in direzioni opposte. I vector store devono restituire punteggi.

**RAG — retrieval-augmented generation.** Cercare in una knowledge base i passaggi rilevanti per una domanda e aggiungerli al prompt. Passa al modello la pagina giusta; non gli insegna nulla.

**Reranking.** Rivalutare i candidati recuperati con un modello che legge la query e ciascun documento *insieme*. Recupera 50, rifai il ranking, mandane 5 — il miglioramento con il maggior ritorno su un sistema RAG funzionante.

**Ricerca ibrida.** Combinare la somiglianza vettoriale con il ranking per parole chiave. Non è la stessa cosa della *ricerca filtrata*, che restringe una ricerca vettoriale in base ai metadati dichiarati in un `DocumentSchema`.

**Run ID.** Un contrassegno che identifica una generazione di una run di workflow, usato insieme al tentativo di esecuzione per fare da fence a una ripresa contro consegne non più valide. Non è l'handle per la ripresa — quello è il *workflow ID*.

**Saga.** Un'operazione di business di lunga durata divisa in passi, ciascuno con un'azione compensativa che lo annulla se un passo successivo fallisce — cancellare l'hotel se il pagamento viene rifiutato.

**Scala dell'autonomia.** I quattro pioli della Sezione 1.1 — chiamata nuda a un LLM, chatbot, workflow, agent — distinti da *chi decide che cosa succede dopo*.

**Stato del workflow.** Il contenitore condiviso che viaggia lungo un'esecuzione. Serializzato a ogni commit di uno step, non solo all'interruzione, quindi non deve contenere risorse, connessioni o closure — salva gli ID e reidrata dentro il nodo.

**Step durevole.** Un nodo di workflow completato, salvato nel workflow store insieme al suo risultato. Dopo un crash o una pausa, gli step completati vengono rigiocati invece che rieseguiti; viene rieseguito solo il nodo che era in esecuzione.

**Streaming.** Emettere la risposta mentre viene prodotta. Cambia la latenza percepita, non quella reale, e ti permette di mostrare che cosa sta facendo l'agent.

**Structured output.** `structured($message, MyClass::class)` — un'istanza tipizzata e validata della tua classe invece che prosa. Il fallimento della validazione innesca un ritentativo che dice al modello esattamente che cosa non andava.

**System prompt.** Le istruzioni inviate a ogni richiesta. Non un saluto — la specifica dell'intero sistema. NeuronAI lo struttura in `background`, `steps`, `output`.

**Thread ID.** L'identità di una conversazione, associata con `setThreadId()` o passata come `Agent::make(workflowId: ...)`; il framework non ne inventa mai uno, e un agent senza thread ID lancia un'eccezione. Per un agent, il thread ID *è* il workflow ID, quindi un thread ha al massimo una run in corso. Input non attendibile: autorizzalo prima di usarlo.

**Token.** Grosso modo tre quarti di una parola inglese. L'unità in cui vieni fatturato, e l'unità in cui si misura la tua context window.

**Tool.** Una funzione nel tuo codebase che il modello può chiederti di eseguire. L'elenco dei tool registrati è il tuo confine di sicurezza — l'unico su cui puoi fare affidamento.

**Toolkit.** Un insieme coerente di tool agganciato in una riga, con un metodo `guidelines()` che descrive come si combinano. Filtralo con `only()`.

**Trace.** La linea temporale dell'esecuzione di un agent: quale nodo è girato, quale tool con quali argomenti, che cosa è tornato indietro, quanti token, quanto tempo. Sostituisce il debug, che qui non funziona.

**Vector store.** Archiviazione e ricerca per somiglianza degli embedding. Cinque metodi — tra cui `search(SearchRequest)` e `delete(FilterExpression)`, che è ciò che fa funzionare la reindicizzazione per sorgente — e un `DocumentSchema` che dichiara quali metadati si possono filtrare.

**Visibilità.** `visible(false)` rimuove del tutto un tool dallo schema. Nascondere batte istruire: le restrizioni basate sul prompt trapelano, sono probabilistiche e sono attaccabili.

**Workflow.** Un grafo di nodi guidato dagli eventi con stato condiviso, cicli, diramazioni, step durevoli e interruzione. Il substrato su cui è costruito l'intero framework — Agent e RAG *sono* workflow.

**Workflow ID.** La chiave di business di una run di workflow — `refund:42`, oppure il thread ID di un agent. Tutto ciò che una run persiste vive sotto di essa, ed è ciò che passi per riprendere.
