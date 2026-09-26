# Capitolo 26 — Strategia sulle versioni, ecosistema e sviluppo assistito dall'AI

Tre cose che nessuno mette nella documentazione, e tutte e tre ti toccheranno entro un mese dal rilascio.

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

Questo capitolo è concettuale e non ha codice a sé stante, ma il repository di accompagnamento [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) contiene le versioni eseguibili di tutto ciò che il libro costruisce.
:::

## 26.1 Strategia sulle versioni

### Il panorama

- **La v4 è quella corrente.** Questo libro è stato verificato contro il ramo 4.x nei giorni precedenti al tag 4.0.0, e contro l'SDK per Laravel 2.x che l'accompagna. Il colophon registra i commit esatti.
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

v2 → v3 era un passaggio meccanico: i namespace si sono spostati e alcuni tipi di ritorno sono cambiati. v3 → v4 non lo è. Il motore dei workflow che sta sotto a tutto è stato ricostruito attorno all'**esecuzione durevole**, e diverse API hanno cambiato forma di conseguenza. Le rotture che incontrerai per prime:

| v3 | v4 | Dove in questo libro |
|---|---|---|
| `Tool::make($name, $description)->setCallable(...)` | `Tool` è astratto; nome e descrizione sono proprietà della classe | 5.2, 5.3 |
| `chat()` restituisce una risposta | `chat()` restituisce un `AgentState`; `getMessage()` può essere `null` | 3.4 |
| `stream()` restituisce un handler con `events()` | `stream()` *è* il generatore; `getReturn()` fornisce lo stato | 7.2 |
| `$workflow->init()->run()` | `$workflow->run()` | 13.3 |
| Un'interruzione lancia `WorkflowInterrupt` | Una pausa è un risultato: `$state->isInterrupted()` | 15.1 |
| `resume` con un oggetto di richiesta | `resume(array $payload)->run()`, indirizzato tramite workflow ID | 15.4 |
| `checkpoint()` | `memoize()` — `checkpoint()` sopravvive, deprecato | 15.5 |
| Middleware `ToolApproval` | `approvalPolicy()` sul tool; `submitApprovalDecisions()` sull'agent | 5.10, 15.5 |
| Cronologia trasportata nello stato dell'agent | La cronologia è un servizio; il thread ID *è* il workflow ID | 4.3 |
| `withFilters()` sullo store | Un `DocumentSchema` più `retrievalScope()` | 12.5, 20.1 |
| `observe(new InspectorObserver(...))` | Eventi PSR-14: `subscribe()` di un listener | 10.2 |
| Guzzle incluso | Un client cURL integrato; Guzzle opzionale | 3.2 |

E il cambiamento architetturale sottostante: ogni nodo completato è ora uno **step durevole**, salvato nel workflow store e rigiocato invece che rieseguito dopo un crash o una pausa. Agent e RAG erano già workflow in v3 — il "Agent e RAG *sono* workflow" della Sezione 2.3 — ma in v4 ereditano quella durabilità, ed è per questo che una chat può ora essere rifiutata con `RunInFlightException` mentre un'approvazione è in sospeso sullo stesso thread. Il nodo che si è *messo in pausa* viene comunque rieseguito dall'inizio alla ripresa; quella parte del Capitolo 15 non è cambiata.

### La diagnostica in cinque controlli

Quando trovi codice di esempio che non funziona:

1. **Controlla le istruzioni `use`.** `NeuronAI\Agent;` senza un secondo segmento significa v2 o precedente.
2. **Cerca `->getMessage()`.** La sua assenza dopo `chat()` significa v2.
3. **Cerca `Edge` o `addEdges()`.** Quella è v1.
4. **Cerca `->start()->getResult()`.** Quella è l'API dei workflow della v2.
5. **Cerca `->init()`, `catch (WorkflowInterrupt`, `ToolApproval` o `setCallable()`.** Uno qualunque di questi significa v3.

Cinque controlli, e identificano la versione di quasi qualunque snippet in pochi secondi. Vale la pena tenerli da qualche parte dove puoi ritrovarli.

### Sopravvivere a una dipendenza che si muove in fretta

Sei pratiche, tutte applicabili a qualunque libreria che si muova più in fretta del tuo ciclo di release:

**Fissa e committa `composer.lock`.** Non solo nelle applicazioni — in qualunque repository che qualcun altro clonerà aspettandosi che funzioni. Il file di lock è ciò che rende riproducibile il "l'anno scorso funzionava".

**Registra la versione dove vive il codice.** Una riga nel tuo README, una costante, un commento in cima al namespace degli agent. Quando fra diciotto mesi qualcuno che sta debuggando chiederà "contro che cosa eravamo stati scritti?", non dovrebbe doverlo indovinare.

**Tieni un file di errata.** Quando trovi una discrepanza fra la documentazione e il codice rilasciato — e l'Appendice A mostra che ce ne sono decine — annotala dove il tuo team la vedrà. Altrimenti la prossima persona che ci incappa passerà lo stesso pomeriggio che hai passato tu.

**Separa la conoscenza durevole da quella deperibile.** I tuoi appunti sul progetto delle descrizioni dei tool, sulla strategia di chunking e sul ciclo dell'agent restano veri attraverso le major. I tuoi appunti sulle firme dei metodi no. Tenerli in documenti diversi significa che un aggiornamento maggiore invalida un file invece di tutti.

**Non inseguire una nuova major immediatamente.** Lascia che l'ecosistema recuperi, poi aggiorna deliberatamente. Il rilascio di una libreria dovrebbe essere una decisione che prendi, non un disservizio che scopri.

**Leggi la guida all'aggiornamento prima del changelog.** Il changelog ti dice che cosa è cambiato; la guida all'aggiornamento ti dice che cosa farci. Per v2 → v3 la guida era breve e le modifiche meccaniche. Per v3 → v4 sono ventisette passi numerati, ciascuno con pattern di ricerca e codice prima/dopo — ed è distribuita *dentro il pacchetto*, in `vendor/neuron-core/neuron-ai/upgrade/`, quindi la versione che leggi è la versione che hai installato. Il sito web è rimasto indietro rispetto al codice per tutta la beta della v4; la guida nel pacchetto no.

### Punti chiave

- La v4 è quella corrente; il codice v3 è la cosa che troverai più spesso, e il codice v1/v2 è ancora ovunque. Nessuno di questi compila contro la v4 senza modifiche.
- v3 → v4 è un passaggio concettuale, non meccanico: step durevoli, pause come risultati, approvazione sul tool.
- Cinque controlli identificano la versione di uno snippet in pochi secondi.
- La guida all'aggiornamento è distribuita in `vendor/`; leggi quella, non quella del sito.
- `composer show --all` è l'autorità su ciò che hai davvero.
- Fissa il file di lock, registra la versione, tieni un file di errata.
- Separa i concetti durevoli dall'API deperibile così che un aggiornamento invalidi un documento, non tutti.

## 26.2 L'ecosistema

### Maestro — un'applicazione completa da leggere

**Maestro è il primo agent CLI costruito interamente in PHP con NeuronAI.** È un assistente di codice nella forma degli assistenti da terminale che forse già usi, ed è open source.

```bash
composer global require neuron-core/maestro
```

Su Windows, installalo ed eseguilo sotto WSL.

Supporta ogni provider di NeuronAI — Anthropic, OpenAI, Gemini, Cohere, Mistral, Ollama, Grok, DeepSeek — instradati attraverso una factory di provider, e integra Inspector tramite un `inspector_key` in `.maestro/settings.json`.

**Perché sta alla fine di questo libro.** La valutazione dell'autore stesso è il punto:

> Il framework che qui fa il lavoro pesante è Neuron AI, in particolare l'architettura a workflow introdotta in v3. Senza la capacità di interrompere l'esecuzione a metà del ciclo dell'agent e riprenderla in base all'input dell'utente, il sistema di approvazione dei tool richiederebbe molto più impianto da costruire e mantenere. Questo pattern — interrompi, presenta, riprendi — sarebbe stato doloroso da implementare senza un framework orientato ai workflow sotto.

È il Capitolo 15, convalidato da un'applicazione reale. Avendo finito la Parte IV, puoi leggere il sorgente di Maestro e riconoscerci dentro ogni pattern. Controlla prima il suo `composer.json`: la citazione descrive l'architettura della v3, e un'applicazione delle dimensioni di Maestro passa a una nuova major secondo i propri tempi. Se punta ancora alla v3, leggerlo è anche un buon esercizio della diagnostica in cinque controlli vista sopra.

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

Il framework è deliberatamente agnostico rispetto al framework, e il pacchetto core richiede solo PHP 8.1 con `ext-curl`.

**Symfony.** Tutto ciò che viene dalle Parti da II a IV si applica direttamente. Registra gli agent come servizi; `SQLChatHistory` accetta un PDO semplice, che ottieni da una connessione Doctrine con `getNativeConnection()`. Inspector distribuisce `inspector-symfony`.

**Spryker, WordPress, sistemi interni legacy.** Stessa storia. Il pacchetto core non ha dipendenze da framework. L'SDK per Laravel è, nelle parole stesse dei manutentori, qualcosa che puoi usare *come ispirazione per progettare il tuo pattern di integrazione personalizzato.*

L'argomento di posizionamento del framework merita di essere citato:

> Invece di frammentare l'innovazione in soluzioni specifiche per framework, Neuron abilita la collaborazione fra sviluppatori Laravel, contributori Symfony, autori di plugin WordPress e team con framework personalizzati.

Se non sei su Laravel, la Parte V di questo libro è un caso di studio più che un prerequisito. I punti di integrazione che descrive — un service container, una coda, un database, uno strato HTTP — esistono in ogni framework che valga la pena usare.

### Punti chiave

- Maestro è un'applicazione open source completa costruita sui pattern di questo libro — leggila.
- Neuron Hub è un primo contributo open source realistico.
- Studio genera codice; non sostituisce il capirlo.
- Il pacchetto core è agnostico rispetto al framework; la Parte V si trasferisce a Symfony, Spryker e a qualunque altra cosa.

## 26.3 Sviluppo assistito dall'AI

### Il problema, specifico di questa libreria

Il corpus pubblico è pieno di codice NeuronAI v1, v2 e v3. Un assistente di codice produrrà con sicurezza `use NeuronAI\Agent;`, `new Edge(NodeA::class, NodeB::class)`, `->init()->run()` e un middleware `ToolApproval` — perché è ciò che dice la maggior parte di internet.

Peggio: l'assistente sarà *fluente* nel farlo. Codice sbagliato con una spiegazione sicura di sé è più difficile da cogliere di codice sbagliato che sembra incerto.

### Tre correzioni, in ordine di efficacia

**1. Il materiale per agent del framework stesso.** La v4 distribuisce indicazioni per gli assistenti di codice dentro il pacchetto: un `AGENTS.md` accanto a ogni modulo in `vendor/neuron-core/neuron-ai/src/`, un insieme di skill per agent, e la guida all'aggiornamento in `upgrade/`, scritta per essere eseguita passo per passo da un assistente. Il primo passo dell'aggiornamento è reinstallare le skill, perché quelle della v3 sono sbagliate per la v4. Su Laravel, Boost aggiunge le linee guida dell'SDK (Sezione 17.7). Considera tutto questo migliore dei dati di addestramento e peggiore del codice: durante la beta, alcune skill mostravano ancora una firma `approvalPolicy(array $inputs)` che il codice aveva già abbandonato.

**2. La documentazione via MCP.** Il framework offre un server MCP per la propria documentazione. Collegalo al tuo assistente e leggerà i documenti correnti invece di richiamare dati di addestramento vecchi.

È un cerchio soddisfacente: **il Capitolo 9 insegnava MCP come modo per dare capacità ai tuoi agent. Qui lo usi per dare al tuo assistente conoscenza sul framework con cui stai costruendo gli agent.**

**3. Un file di regole di progetto.** Qualunque cosa il tuo assistente legga — `CLAUDE.md`, `.cursorrules` o equivalente:

```markdown
# NeuronAI conventions for this project

Target version: neuron-core/neuron-ai ^4.0

## Namespaces (do not use v1/v2 forms)
- `NeuronAI\Agent\Agent`     NOT `NeuronAI\Agent`
- `NeuronAI\Agent\SystemPrompt`  NOT `NeuronAI\SystemPrompt`

## API (v4 — do not use v3 forms)
- `chat()` returns `AgentState` — `->getMessage()?->getContent()`
- `stream()` is the generator — iterate it; chunks are objects; `->getReturn()` for the state
- Workflows: `->run()` / `->events()`, NOT `init()`; no `Edge` class
- A pause is a result: check `$state->isInterrupted()`, never catch `WorkflowInterrupt`
- Resume with `resume($payload)->run()`, addressed by workflow ID
- Tools extend `Tool`; `$name` / `$description` are properties, not constructor args
- Approval lives on the tool (`approvalPolicy()`), NOT in a `ToolApproval` middleware

## Project rules
- Tools are classes, never anonymous
- Toolkits filtered with `only()`, never `exclude()`
- Write tools: `setMaxRuns(1)` + idempotency guard + transaction
- Every pre-interrupt LLM call wrapped in `memoize()`
- Tenant scope is a constructor dependency, never read from ambient context
```

Trenta righe, e codificano gran parte delle regole pratiche di questo libro. Scrivi la tua versione e mettila nel repository — è il modo più economico per impedire a un assistente pieno di buone intenzioni di disfare decisioni che hai preso deliberatamente.

### L'avvertenza onesta

L'Appendice A è la prova. **La documentazione ufficiale stessa si è discostata dal codice in decine di punti** — namespace sbagliati, nomi di classi con refusi, firme che il codice ha abbandonato una release fa, e due guide all'aggiornamento nello stesso pacchetto che non concordano su quale ID riprenda un workflow.

Un assistente che legge quella documentazione eredita ciascuno di quegli errori.

La disciplina, che è la stessa che questo libro ha applicato dall'inizio:

**Usa gli assistenti per la forma.** Scaffolding, boilerplate, fixture di test, DTO ripetitivi. In questo sono genuinamente bravi.

**Verifica qualunque cosa tocchi la superficie dell'API** contro la tua versione installata — il "vai alla definizione" del tuo IDE, oppure direttamente `vendor/`.

**Non fidarti mai di un'affermazione sulle versioni.** Se un assistente dice "in NeuronAI v4 fai X", controlla. Non ha alcun modo affidabile di saperlo.

Quell'abitudine si trasferisce ben oltre questo framework, ed è la nota giusta su cui chiudere: **gli strumenti sono utili e non sono autorevoli, e sapere la differenza è ciò che fa di te l'ingegnere nel ciclo.**

### Punti chiave

- Il corpus pubblico è pieno di codice v1–v3; gli assistenti lo riproducono con scioltezza.
- Tre correzioni: il materiale per agent incluso nel pacchetto del framework (più Boost su Laravel), documentazione via MCP, un file di regole di progetto.
- La documentazione stessa si è discostata — gli assistenti ne ereditano gli errori.
- Usa gli assistenti per la forma, verifica la superficie dell'API, non fidarti mai di un'affermazione sulle versioni.

## Postfazione

Ventisei capitoli fa, il Capitolo 1 disegnava una scala a quattro pioli e faceva una sola domanda: *chi decide che cosa succede dopo?*

Tutto ciò che è venuto dopo è stato il macchinario necessario per lasciare che un modello vi rispondesse in sicurezza. Tool per dargli le mani. Struttura per rendere usabile il suo output. Recupero per dargli conoscenza. Workflow per dargli forma. Interruzione per tenere un essere umano nella decisione. Osservabilità per scoprire che cosa abbia effettivamente fatto.

Niente di tutto questo è specifico di NeuronAI, e ben poco è specifico di PHP. Il framework cambierà — è di questo che parla la Sezione 26.1. L'aritmetica della Sezione 1.4, la descrizione dei tool in quattro parti della Sezione 5.4, la differenza fra filtrare al recupero e filtrare dopo, il fatto che un nodo ripreso si riesegue dall'inizio: quelle sopravvivono al framework, e sono ciò che hai davvero imparato.

Resta una domanda, ed è quella da porsi su ogni agent che distribuirai da qui in avanti:

> **Qual è la cosa peggiore che può fare, e che cosa lo ferma?**

Se sai rispondere, sei pronto.
