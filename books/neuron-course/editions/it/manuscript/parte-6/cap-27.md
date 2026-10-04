# Capitolo 27 — Strategia sulle versioni, ecosistema e sviluppo assistito dall'AI

Tre cose che nessuno mette nella documentazione, e tutte e tre ti toccheranno entro un mese dal rilascio.

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

Questo capitolo è concettuale e non ha codice a sé stante, ma il repository di accompagnamento [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) contiene le versioni eseguibili di tutto ciò che il libro costruisce.
:::

## 27.1 Strategia sulle versioni

### Il panorama

- **La v4 è quella corrente.** Questo libro è verificato sui tag rilasciati: neuron-ai 4.0.3 e neuron-laravel 2.0.0, su Laravel 13 e PHP 8.5. Il colophon registra le stesse versioni.
- **La pre-release 4.x è ancora in circolazione.** Il ramo 4.x era pubblico prima del tag 4.0.0, e la sua API è cambiata nel passaggio alla release: come si riprende una run, come si associa un thread ID, dove vive la cronologia della chat, dove stanno gli eventi di osservabilità. Tutorial, repository di esempio e qualunque assistente addestrato in quella finestra mostrano questo dialetto. Non è la v3, non è la 4.0.3, e nessuna guida all'aggiornamento lo copre; il sesto controllo qui sotto lo riconosce.
- **La v3 è la major precedente.** È stabile, molto diffusa, ed è la versione che dà per scontata la maggior parte dei tutorial scritti nel 2025 e nel 2026.
- **La v1 e la v2 sono archiviate** ma la loro documentazione resta online su percorsi versionati, e il loro codice è sparso per blog, forum e siti di risposte.

::: {.callout .callout-warning}
[Quale versione hai davvero?]{.callout-title}

Prima di fare affidamento su qualunque affermazione riguardo alle versioni — incluse quelle di questo libro — esegui:

```bash
composer show neuron-core/neuron-ai
```

e controlla la pagina delle release del progetto. Quel comando è l'autorità. Questo libro no. Se dopo la pubblicazione è uscita una minor 4.x, leggi il suo changelog confrontandolo con i capitoli su cui fai affidamento: i test di contratto del repository di accompagnamento esistono proprio per intercettare questa deriva.
:::

### Che cosa è cambiato fra v3 e v4, e perché ti riguarda

La maggior parte del codice NeuronAI che troverai online precede la v4, il cui motore dei workflow è costruito attorno all'**esecuzione durevole** — e diverse API hanno una forma diversa proprio per questo. Le forme più vecchie che incontrerai per prime, e che cosa usa invece questo libro:

| Codice più vecchio (v3) | Questo libro (v4) | Dove in questo libro |
|---|---|---|
| `Tool::make($name, $description)->setCallable(...)` | `Tool` è astratto; nome e descrizione sono proprietà della classe | 5.2, 5.3 |
| `chat()` restituisce una risposta | `chat()` restituisce un `AgentState`; `getMessage()` può essere `null` | 3.4 |
| `stream()` restituisce un handler con `events()` | `stream()` *è* il generatore; `getReturn()` fornisce lo stato | 7.2 |
| `$workflow->init()->run()` | `$workflow->run()` | 13.3 |
| Un'interruzione lancia `WorkflowInterrupt` | Una pausa è un risultato: `$state->isInterrupted()` | 15.1 |
| `resume` con un oggetto di richiesta | `submitInputs($payload)->run()` oppure `run(ExecutionRequest::resume($payload))`, indirizzato tramite workflow ID | 15.4 |
| `MyAgent::make()->chat(...)`, nessun ID necessario | Prima si associa un ID: `make(workflowId: $threadId)` oppure `setThreadId()` | 3.4 |
| `chatHistory()` che restituisce `FileChatHistory`, `SQLChatHistory` o `EloquentChatHistory` | `messageStore()` che restituisce `FileMessageStore`, `SQLMessageStore` o `EloquentMessageStore` | 4.3 |
| `checkpoint()` | `memoize()` — `checkpoint()` sopravvive, deprecato | 15.5 |
| Middleware `ToolApproval` | `approvalPolicy()` sul tool; `submitApprovalDecisions()` sull'agent | 5.10, 15.5 |
| `withFilters()` sullo store | Un `DocumentSchema` più `retrievalScope()` | 12.5, 20.1 |
| `observe(new InspectorObserver(...))` | Eventi PSR-14: `subscribe()` di un listener | 10.2 |

Sotto, ogni nodo completato è uno **step durevole**, salvato nel workflow store e rigiocato invece che rieseguito dopo un crash o una pausa. Agent e RAG sono workflow (Sezione 2.3), quindi ereditano quella durabilità, ed è per questo che una chat può essere rifiutata con `RunInFlightException` mentre un'approvazione è in sospeso sullo stesso thread. Il nodo che si è *messo in pausa* viene comunque rieseguito dall'inizio alla ripresa (Capitolo 15).

### La diagnostica in sei controlli

Quando trovi codice di esempio che non funziona — o che sembra giusto e non ne sei sicuro:

1. **Controlla le istruzioni `use`.** `NeuronAI\Agent;` senza un secondo segmento significa v2 o precedente.
2. **Cerca `->getMessage()`.** La sua assenza dopo `chat()` significa v2.
3. **Cerca `Edge` o `addEdges()`.** Quella è v1.
4. **Cerca `->start()->getResult()`.** Quella è l'API dei workflow della v2.
5. **Cerca `->init()`, `catch (WorkflowInterrupt`, `ToolApproval` o `setCallable()`.** Uno qualunque di questi significa v3.
6. **Cerca il dialetto della pre-release 4.x:** `->resume(`, `make(threadId:`, `setChatHistory(`, qualunque classe `*ChatHistory`, `abandonRun(`, `acknowledgeCompletion(` o `NeuronAI\Observability\Events\`. Uno qualunque di questi significa una pre-release della v4. Sembra attuale e fallisce sulla 4.0.3 — non sempre in modo rumoroso: un agent che sovrascrive ancora `chatHistory()` gira, e tiene in silenzio la conversazione in memoria.

Sei controlli, e identificano la versione di quasi qualunque snippet in pochi secondi. Vale la pena tenerli da qualche parte dove puoi ritrovarli.

### Sopravvivere a una dipendenza che si muove in fretta

Sei pratiche, tutte applicabili a qualunque libreria che si muova più in fretta del tuo ciclo di release:

**Fissa la versione e committa `composer.lock`.** Non solo nelle applicazioni — in qualunque repository che qualcun altro clonerà aspettandosi che funzioni. Il file di lock è ciò che rende riproducibile il "l'anno scorso funzionava", e `composer.json` dovrebbe richiedere la versione esatta che hai verificato (`"neuron-core/neuron-ai": "4.0.3"`), non `^4.0`: un intervallo con il circonflesso significa `>=4.0.0 <5.0.0`, quindi il prossimo `composer update` può portarti a qualunque release 4.x successiva senza che nessuno l'abbia deciso.

**Registra la versione dove vive il codice.** Una riga nel tuo README, una costante, un commento in cima al namespace degli agent. Quando fra diciotto mesi qualcuno che sta debuggando chiederà "contro che cosa eravamo stati scritti?", non dovrebbe doverlo indovinare.

**Tieni un file di errata.** Quando trovi una discrepanza fra la documentazione e il codice rilasciato — e ce ne sono decine — annotala dove il tuo team la vedrà. Altrimenti la prossima persona che ci incappa passerà lo stesso pomeriggio che hai passato tu.

**Separa la conoscenza durevole da quella deperibile.** I tuoi appunti sul progetto delle descrizioni dei tool, sulla strategia di chunking e sul ciclo dell'agent restano veri attraverso le major. I tuoi appunti sulle firme dei metodi no. Tenerli in documenti diversi significa che un aggiornamento maggiore invalida un file invece di tutti.

**Non inseguire una nuova major immediatamente.** Lascia che l'ecosistema recuperi, poi aggiorna deliberatamente. Il rilascio di una libreria dovrebbe essere una decisione che prendi, non un disservizio che scopri. Lo stesso vale per le pre-release: un'API può ancora cambiare fra una pre-release e il suo tag, quindi il codice verificato sull'una non è verificato sull'altro. Gli stessi listati di questo libro erano stati scritti sul ramo 4.x e hanno dovuto essere verificati di nuovo contro la 4.0.3.

**Leggi la guida all'aggiornamento prima del changelog.** Il changelog ti dice che cosa è cambiato; la guida all'aggiornamento ti dice che cosa farci. La guida di NeuronAI alla v4 è fatta di cinquantasette guide numerate più una guida 0, ciascuna con pattern di ricerca e codice prima/dopo — ed è distribuita *dentro il pacchetto*, in `vendor/neuron-core/neuron-ai/upgrade/`, quindi la versione che leggi è la versione che hai installato. Il sito web può restare indietro rispetto al codice; la guida nel pacchetto no. Queste guide migrano dalla 3.x, quindi una pre-release richiede prima il sesto controllo.

Un aggiornamento, dunque, segue quest'ordine. Fallo su un branch. Alza la versione. Esegui prima di tutto l'analisi statica: le classi e i metodi rimossi vi compaiono come errori, prima che giri un solo test. Esegui i test di contratto. Percorri le guide nel pacchetto in ordine, a partire dalla guida 0 (reinstalla le skill per agent), applicando solo ciò che i loro pattern di ricerca trovano nel tuo codice. Esegui gli eval per ultimi, perché sono loro ad accorgersi di un cambiamento di comportamento che continua a passare il controllo dei tipi.

### Punti chiave

- La v4 è quella corrente; il codice v3 è la cosa che troverai più spesso, e il codice v1/v2 è ancora ovunque. Nessuno di questi compila contro la v4 senza modifiche.
- Il codice più vecchio differisce nei concetti, non solo nella sintassi: la v4 ha step durevoli, pause come risultati, approvazione sul tool.
- Sei controlli identificano la versione di uno snippet in pochi secondi, dialetto della pre-release 4.x compreso.
- La guida all'aggiornamento è distribuita in `vendor/`; leggi quella, non quella del sito.
- `composer show neuron-core/neuron-ai` è l'autorità su ciò che hai davvero.
- Fissa la versione esatta e il file di lock, registra la versione, tieni un file di errata.
- Aggiorna su un branch: analisi statica, test di contratto, le guide nel pacchetto a partire dalla guida 0, poi gli eval.
- Separa i concetti durevoli dall'API deperibile così che un aggiornamento invalidi un documento, non tutti.

## 27.2 L'ecosistema

### Maestro — un'applicazione completa da leggere

**Maestro è il primo agent CLI costruito interamente in PHP con NeuronAI.** È un assistente di codice nella forma degli assistenti da terminale che forse già usi, ed è open source.

```bash
composer global require neuron-core/maestro
```

Su Windows, installalo ed eseguilo sotto WSL.

Supporta otto dei provider che NeuronAI distribuisce — Anthropic, OpenAI, Gemini, Cohere, Mistral, Ollama, Grok, DeepSeek — instradati attraverso una factory di provider, e integra Inspector tramite un `inspector_key` in `.maestro/settings.json`.

**Perché sta alla fine di questo libro.** La valutazione dell'autore stesso è il punto:

> Il framework che qui fa il lavoro pesante è Neuron AI, in particolare l'architettura a workflow introdotta in v3. Senza la capacità di interrompere l'esecuzione a metà del ciclo dell'agent e riprenderla in base all'input dell'utente, il sistema di approvazione dei tool richiederebbe molto più impianto da costruire e mantenere. Questo pattern — interrompi, presenta, riprendi — sarebbe stato doloroso da implementare senza un framework orientato ai workflow sotto.

È il Capitolo 15, convalidato da un'applicazione reale. Avendo finito la Parte IV, puoi leggere il sorgente di Maestro e riconoscerci dentro ogni pattern. Controlla prima il suo `composer.json`: la citazione descrive l'architettura della v3, e un'applicazione delle dimensioni di Maestro passa a una nuova major secondo i propri tempi. Se punta ancora alla v3, leggerlo è anche un buon esercizio della diagnostica in sei controlli vista sopra.

**Due funzionalità che vale la pena studiare in particolare:**

**Il sistema di approvazione dei tool** — conferma interattiva prima delle operazioni sensibili. L'approvazione dei tool della Sezione 15.5, in produzione.

**Il sistema di estensioni** — classi PHP che implementano `ExtensionInterface`, registrate attraverso un `ExtensionApi` iniettato all'avvio. Un `ExtensionLoader` costruisce registri per tool, comandi, renderer, eventi, memorie e UI. È un'architettura a plugin ben progettata e vale la pena leggerla per i suoi meriti, indipendentemente dall'AI.

**Un buon esercizio:** scrivi un'estensione di Maestro che aggiunga un tool dal Progetto finale A. È la strada più breve da "ho costruito un agent CLI" a "ho esteso quello di qualcun altro".

### Neuron Hub

Un registro di estensioni e toolkit della community. Due usi:

**Controlla prima di costruire.** Qualcuno potrebbe aver già scritto la tua integrazione.

**Pubblica la tua.** Un toolkit ben costruito — una classe che estende `AbstractToolkit` con un vero metodo `guidelines()` (Sezione 5.7) — è un contributo open source piccolo, alla portata e con un pubblico chiaro.

Se stai costruendo un portfolio, è un primo contributo migliore di un refuso nella documentazione: circoscritto, utile e dimostrabilmente tuo.

### Neuron Studio

`digitalelvis/neuronai-studio` — un pacchetto della community che offre un costruttore visuale di agent per Laravel che **esporta vere classi PHP**.

Utile per prototipare e per mostrare l'architettura a chi non sviluppa. L'avvertenza, detta chiaramente: genera codice, non sostituisce il capirlo. Allungare la mano verso Studio prima di aver finito la Parte II produce classi che non sai debuggare.

### Oltre Laravel

Il framework è deliberatamente agnostico rispetto al framework. Il pacchetto core in sé dichiara PHP 8.1 con `ext-curl`; il codice di questo libro, come il repository di accompagnamento, richiede PHP 8.5.

**Symfony.** Tutto ciò che viene dalle Parti da II a IV si applica direttamente. Registra gli agent come servizi; `SQLMessageStore` accetta un PDO semplice, che ottieni da una connessione Doctrine con `getNativeConnection()`. Inspector distribuisce `inspector-symfony`.

**Spryker, WordPress, sistemi interni legacy.** Stessa storia. Il pacchetto core non ha dipendenze da framework. L'SDK per Laravel è, nelle parole stesse dei manutentori, qualcosa che puoi usare *come ispirazione per progettare il tuo pattern di integrazione personalizzato.*

L'argomento di posizionamento del framework merita di essere citato:

> Invece di frammentare l'innovazione in soluzioni specifiche per framework, Neuron abilita la collaborazione fra sviluppatori Laravel, contributori Symfony, autori di plugin WordPress e team con framework personalizzati.

Se non sei su Laravel, la Parte V di questo libro è un caso di studio più che un prerequisito. I punti di integrazione che descrive — un service container, una coda, un database, uno strato HTTP — esistono in ogni framework che valga la pena usare.

### Punti chiave

- Maestro è un'applicazione open source completa costruita sui pattern di questo libro — leggila.
- Neuron Hub è un primo contributo open source realistico.
- Studio genera codice; non sostituisce il capirlo.
- Il pacchetto core è agnostico rispetto al framework; la Parte V si trasferisce a Symfony, Spryker e a qualunque altra cosa.

## 27.3 Sviluppo assistito dall'AI

### Il problema, specifico di questa libreria

Il corpus pubblico è pieno di codice NeuronAI v1, v2 e v3, e di codice della pre-release 4.x. Un assistente di codice produrrà con sicurezza `use NeuronAI\Agent;`, `new Edge(NodeA::class, NodeB::class)`, `->init()->run()` e un middleware `ToolApproval` — perché è ciò che dice la maggior parte di internet. Uno addestrato sulla pre-release scriverà invece `Agent::make(threadId: $id)` o `->resume($payload)->run()`: sembrano giusti, e falliscono sulla 4.0.3.

Peggio: l'assistente sarà *fluente* nel farlo. Codice sbagliato con una spiegazione sicura di sé è più difficile da cogliere di codice sbagliato che sembra incerto.

### Tre correzioni, in ordine di efficacia

**1. Il materiale per agent del framework stesso.** NeuronAI distribuisce indicazioni per gli assistenti di codice dentro il pacchetto: un `AGENTS.md` accanto a ogni modulo in `vendor/neuron-core/neuron-ai/src/`, un insieme di skill per agent, e la guida all'aggiornamento in `upgrade/`, scritta per essere eseguita passo per passo da un assistente. Su un progetto aggiornato da una versione precedente, reinstalla prima le skill: quelle vecchie descrivono la vecchia API. Su Laravel, fai attenzione (Sezione 17.7): le skill di Boost incluse in neuron-laravel 2.0.0 restano indietro rispetto al pacchetto core e insegnano ancora forme rimosse — `make(threadId:)`, `setChatHistory()`, `resume()`, una firma `approvalPolicy(array $inputs)`. Indirizza invece il tuo assistente alle skill correnti in `vendor/neuron-core/neuron-ai/skills/`, che includono `neuron-laravel-integration`, assente nel pacchetto per Laravel. Considera tutto questo migliore dei dati di addestramento e peggiore del codice.

**2. La documentazione via MCP.** Il framework offre un server MCP per la propria documentazione. Collegalo al tuo assistente e leggerà i documenti correnti invece di richiamare dati di addestramento vecchi.

È un cerchio soddisfacente: **il Capitolo 9 insegnava MCP come modo per dare capacità ai tuoi agent. Qui lo usi per dare al tuo assistente conoscenza sul framework con cui stai costruendo gli agent.**

**3. Un file di regole di progetto.** Qualunque cosa il tuo assistente legga — `CLAUDE.md`, `.cursorrules` o equivalente:

```markdown
# NeuronAI conventions for this project

Verified version: neuron-core/neuron-ai 4.0.3 (Laravel SDK: neuron-core/neuron-laravel 2.0.0)
Require it exactly (`"neuron-core/neuron-ai": "4.0.3"`), never `^4.0`: a caret range accepts every later 4.x
Code from v1-v3 or from a pre-release 4.x is wrong here, even when it looks current

## Namespaces (do not use v1/v2 forms)
- `NeuronAI\Agent\Agent`     NOT `NeuronAI\Agent`
- `NeuronAI\Agent\SystemPrompt`  NOT `NeuronAI\SystemPrompt`
- Observability events: `NeuronAI\Agent\Observability\`, `NeuronAI\Workflow\Observability\`, `NeuronAI\RAG\Observability\`

## API (4.0.3 — do not use v3 or pre-release forms)
- `chat()` returns `AgentState` — `->getMessage()?->getContent()`
- `stream()` is the generator — iterate it; chunks are objects; `->getReturn()` for the state
- Workflows: `->run()` / `->events()`, NOT `init()`; no `Edge` class
- A pause is a result: check `$state->isInterrupted()`, never catch `WorkflowInterrupt`
- Resume with `->run(ExecutionRequest::resume($payload))` or `->submitInputs($payload)->run()`; there is no `resume()` method
- Bind an ID before any run: `make(workflowId: $id)` or `setThreadId($id)`; `make(threadId: ...)` does not exist
- Memory is `messageStore()` returning a `MessageStoreInterface` (`SQLMessageStore`, `EloquentMessageStore`); no `*ChatHistory` classes, no `setChatHistory()`
- Tools extend `Tool`; `$name` / `$description` are properties, not constructor args
- Approval lives on the tool (`approvalPolicy()`), NOT in a `ToolApproval` middleware

## Project rules
- Tools are classes, never anonymous
- Toolkits filtered with `only()`, never `exclude()`
- Write tools: `setMaxRuns(1)` + idempotency guard + transaction
- Every pre-interrupt LLM call wrapped in `memoize()`
- Tenant scope is a constructor dependency, never read from ambient context
- When a snippet, a skill or your memory disagrees with `vendor/neuron-core/neuron-ai/`, the source wins
```

Ventinove righe, e codificano gran parte delle regole pratiche di questo libro. Scrivi la tua versione e mettila nel repository — è il modo più economico per impedire a un assistente pieno di buone intenzioni di disfare decisioni che hai preso deliberatamente.

### L'avvertenza onesta

**La documentazione ufficiale stessa si è discostata dal codice in decine di punti** — namespace sbagliati, nomi di classi con refusi, firme che il codice ha abbandonato una release fa.

Un assistente che legge quella documentazione eredita ciascuno di quegli errori.

La disciplina, che è la stessa che questo libro ha applicato dall'inizio:

**Usa gli assistenti per la forma.** Scaffolding, boilerplate, fixture di test, DTO ripetitivi. In questo sono genuinamente bravi.

**Verifica qualunque cosa tocchi la superficie dell'API** contro la tua versione installata — il "vai alla definizione" del tuo IDE, oppure direttamente `vendor/`.

**Non fidarti mai di un'affermazione sulle versioni.** Se un assistente dice "in NeuronAI v4 fai X", controlla. Non ha alcun modo affidabile di saperlo.

Quell'abitudine si trasferisce ben oltre questo framework, ed è la nota giusta su cui chiudere: **gli strumenti sono utili e non sono autorevoli, e sapere la differenza è ciò che fa di te l'ingegnere nel ciclo.**

### Punti chiave

- Il corpus pubblico è pieno di codice v1–v3 e della pre-release 4.x; gli assistenti lo riproducono con scioltezza.
- Tre correzioni: il materiale per agent incluso nel pacchetto del framework (su Laravel, le skill di neuron-ai anziché quelle di Boost incluse), documentazione via MCP, un file di regole di progetto.
- La documentazione stessa si è discostata — gli assistenti ne ereditano gli errori.
- Usa gli assistenti per la forma, verifica la superficie dell'API, non fidarti mai di un'affermazione sulle versioni.

## Postfazione

Ventisei capitoli fa, il Capitolo 1 disegnava una scala a quattro pioli e faceva una sola domanda: *chi decide che cosa succede dopo?*

Tutto ciò che è venuto dopo è stato il macchinario necessario per lasciare che un modello vi rispondesse in sicurezza. Tool per dargli le mani. Struttura per rendere usabile il suo output. Recupero per dargli conoscenza. Workflow per dargli forma. Interruzione per tenere un essere umano nella decisione. Osservabilità per scoprire che cosa abbia effettivamente fatto.

Niente di tutto questo è specifico di NeuronAI, e ben poco è specifico di PHP. Il framework cambierà — è di questo che parla la Sezione 27.1. L'aritmetica della Sezione 1.4, la descrizione dei tool in quattro parti della Sezione 5.4, la differenza fra filtrare al recupero e filtrare dopo, il fatto che un nodo ripreso si riesegue dall'inizio: quelle sopravvivono al framework, e sono ciò che hai davvero imparato.

Resta una domanda, ed è quella da porsi su ogni agent che distribuirai da qui in avanti:

> **Qual è la cosa peggiore che può fare, e che cosa lo ferma?**

Se sai rispondere, sei pronto.
