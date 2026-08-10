# Capitolo 26 — Strategia sulle versioni, ecosistema e sviluppo assistito dall'AI

Tre cose che nessuno mette nella documentazione, e tutte e tre ti toccheranno entro un mese dal rilascio.

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

Questo capitolo è concettuale e non ha codice a sé stante, ma il repository di accompagnamento [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) contiene le versioni eseguibili di tutto ciò che il libro costruisce.
:::

## 26.1 Strategia sulle versioni

### Il panorama

- **La v3 è la stabile corrente.** L'SDK per Laravel 1.3.0 richiede `neuron-ai: ^3.15`.
- **La v1 e la v2 sono archiviate** ma la loro documentazione resta online su percorsi versionati, e il loro codice è sparso per blog, forum e siti di risposte.

::: {.callout .callout-warning}
[Sulla "v4" di cui potresti aver sentito parlare]{.callout-title}

Circolano programmi di corsi e post nei forum che parlano di una beta di NeuronAI v4. Quella release non è stata verificabile al momento della scrittura: il materiale di aggiornamento pubblicato copre solo v2 → v3, il sito della documentazione mantiene alberi archiviati ai percorsi `/v1/` e `/neuron-v3/` che è facile scambiare per un ramo più recente, e l'attuale SDK per Laravel si aggancia a `^3.15`.

Prima di fare affidamento su qualunque affermazione riguardo alle versioni — inclusa questa — esegui:

```bash
composer show neuron-core/neuron-ai --all
```

e controlla la pagina delle release del progetto. Quel comando è l'autorità. Questo libro no.
:::

### Che cosa è cambiato fra v2 e v3, e perché ti riguarda

Tre rotture compaiono di continuo nel materiale più vecchio, e ciascuna di esse è un errore fatale per chi copia un tutorial:

**1. I namespace si sono spostati.**

| v1 / v2 | v3 |
|---|---|
| `NeuronAI\Agent` | `NeuronAI\Agent\Agent` |
| `NeuronAI\SystemPrompt` | `NeuronAI\Agent\SystemPrompt` |

**2. `chat()` restituisce una risposta, non un messaggio.**

```php
// v2
$message = MyAgent::make()->chat(new UserMessage("Hi, who are you?"));

// v3
$message = MyAgent::make()->chat(new UserMessage("Hi, who are you?"))->getMessage();
```

**3. Gli allegati sono diventati blocchi di contenuto.**

```php
// v2
$message->addAttachment(new Image($url, AttachmentContentType::URL));

// v3
$message = new UserMessage([
    new TextBlock('Analyze this'),
    new ImageBlock($url, SourceType::URL)
]);
```

E il cambiamento architetturale sotto a tutto questo: Agent, RAG e il sistema dei messaggi sono stati **ricostruiti sopra il componente Workflow**, che ora alimenta l'intero framework. Ecco perché la Sezione 2.3 poteva dire "Agent e RAG *sono* workflow" — in v3 è diventato letteralmente vero.

### La diagnostica in quattro controlli

Quando trovi codice di esempio che non funziona:

1. **Controlla le istruzioni `use`.** `NeuronAI\Agent;` senza un secondo segmento significa v2 o precedente.
2. **Cerca `->getMessage()`.** La sua assenza significa v2.
3. **Cerca `Edge` o `addEdges()`.** Quella è v1.
4. **Cerca `->start()->getResult()`.** Quella è l'API dei workflow della v2.

Quattro controlli, e identificano la versione di quasi qualunque snippet in pochi secondi. Vale la pena tenerli da qualche parte dove puoi ritrovarli.

### Sopravvivere a una dipendenza che si muove in fretta

Sei pratiche, tutte applicabili a qualunque libreria che si muova più in fretta del tuo ciclo di release:

**Fissa e committa `composer.lock`.** Non solo nelle applicazioni — in qualunque repository che qualcun altro clonerà aspettandosi che funzioni. Il file di lock è ciò che rende riproducibile il "l'anno scorso funzionava".

**Registra la versione dove vive il codice.** Una riga nel tuo README, una costante, un commento in cima al namespace degli agent. Quando fra diciotto mesi qualcuno che sta debuggando chiederà "contro che cosa eravamo stati scritti?", non dovrebbe doverlo indovinare.

**Tieni un file di errata.** Quando trovi una discrepanza fra la documentazione e il codice rilasciato — e l'Appendice A mostra che ce ne sono almeno quarantaquattro — annotala dove il tuo team la vedrà. Altrimenti la prossima persona che ci incappa passerà lo stesso pomeriggio che hai passato tu.

**Separa la conoscenza durevole da quella deperibile.** I tuoi appunti sul progetto delle descrizioni dei tool, sulla strategia di chunking e sul ciclo dell'agent restano veri attraverso le major. I tuoi appunti sulle firme dei metodi no. Tenerli in documenti diversi significa che un aggiornamento maggiore invalida un file invece di tutti.

**Non inseguire una nuova major immediatamente.** Lascia che l'ecosistema recuperi, poi aggiorna deliberatamente. Il rilascio di una libreria dovrebbe essere una decisione che prendi, non un disservizio che scopri.

**Leggi la guida all'aggiornamento prima del changelog.** Il changelog ti dice che cosa è cambiato; la guida all'aggiornamento ti dice che cosa farci. Per v2 → v3 la guida è breve e le modifiche sono meccaniche — che è il caso migliore, e non uno su cui contare.

### Punti chiave

- La v3 è quella corrente; il codice v1/v2 è ovunque e non compila contro di essa.
- Quattro controlli identificano la versione di uno snippet in pochi secondi.
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

È il Capitolo 15, convalidato da un'applicazione reale. Avendo finito la Parte IV, puoi leggere il sorgente di Maestro e riconoscerci dentro ogni pattern.

**Due funzionalità che vale la pena studiare in particolare:**

**Il sistema di approvazione dei tool** — conferma interattiva prima delle operazioni sensibili. Il `ToolApproval` della Sezione 15.5, in produzione.

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

Il framework è deliberatamente agnostico rispetto al framework, e il pacchetto core richiede solo PHP 8.1.

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

Il corpus pubblico è pieno di codice NeuronAI v1 e v2. Un assistente di codice produrrà con sicurezza `use NeuronAI\Agent;`, `new Edge(NodeA::class, NodeB::class)` e `chat()` senza `getMessage()` — perché è ciò che dice la maggior parte di internet.

Peggio: l'assistente sarà *fluente* nel farlo. Codice sbagliato con una spiegazione sicura di sé è più difficile da cogliere di codice sbagliato che sembra incerto.

### Tre correzioni, in ordine di efficacia

**1. Linee guida di Laravel Boost.** L'SDK per Laravel distribuisce linee guida aggiornate per gli assistenti di codice (Sezione 17.7). Niente da configurare — installa il pacchetto e ci sono.

**2. La documentazione via MCP.** Il framework offre un server MCP per la propria documentazione. Collegalo al tuo assistente e leggerà i documenti correnti invece di richiamare dati di addestramento vecchi.

È un cerchio soddisfacente: **il Capitolo 9 insegnava MCP come modo per dare capacità ai tuoi agent. Qui lo usi per dare al tuo assistente conoscenza sul framework con cui stai costruendo gli agent.**

**3. Un file di regole di progetto.** Qualunque cosa il tuo assistente legga — `CLAUDE.md`, `.cursorrules` o equivalente:

```markdown
# NeuronAI conventions for this project

Target version: neuron-core/neuron-ai ^3.15

## Namespaces (v3 — do not use v1/v2 forms)
- `NeuronAI\Agent\Agent`     NOT `NeuronAI\Agent`
- `NeuronAI\Agent\SystemPrompt`  NOT `NeuronAI\SystemPrompt`

## API
- `chat()` returns a response — always call `->getMessage()`
- `stream()` returns a handler — call `->events()`, chunks are objects (`$chunk->content`)
- Workflows use `init()` / `run()`, NOT `start()` / `getResult()`
- The `Edge` class does not exist — nodes wire via `__invoke` type hints

## Project rules
- Tools are classes, never inline closures
- Toolkits filtered with `only()`, never `exclude()`
- Write tools: `setMaxRuns(1)` + idempotency guard + transaction
- Every pre-interrupt LLM call wrapped in `checkpoint()`
- Tenant scope is a constructor dependency, never read from ambient context
```

Trenta righe, e codificano gran parte delle regole pratiche di questo libro. Scrivi la tua versione e mettila nel repository — è il modo più economico per impedire a un assistente pieno di buone intenzioni di disfare decisioni che hai preso deliberatamente.

### L'avvertenza onesta

L'Appendice A è la prova. **La documentazione ufficiale stessa si è discostata dal codice in quarantaquattro punti** — namespace sbagliati, nomi di classi con refusi, tre diverse firme di costruttore per una sola classe, due diverse API di esecuzione su pagine adiacenti.

Un assistente che legge quella documentazione eredita ciascuno di quegli errori.

La disciplina, che è la stessa che questo libro ha applicato dall'inizio:

**Usa gli assistenti per la forma.** Scaffolding, boilerplate, fixture di test, DTO ripetitivi. In questo sono genuinamente bravi.

**Verifica qualunque cosa tocchi la superficie dell'API** contro la tua versione installata — il "vai alla definizione" del tuo IDE, oppure direttamente `vendor/`.

**Non fidarti mai di un'affermazione sulle versioni.** Se un assistente dice "in NeuronAI v3 fai X", controlla. Non ha alcun modo affidabile di saperlo.

Quell'abitudine si trasferisce ben oltre questo framework, ed è la nota giusta su cui chiudere: **gli strumenti sono utili e non sono autorevoli, e sapere la differenza è ciò che fa di te l'ingegnere nel ciclo.**

### Punti chiave

- Il corpus pubblico è pieno di codice v1/v2; gli assistenti lo riproducono con scioltezza.
- Tre correzioni: linee guida Boost, documentazione via MCP, un file di regole di progetto.
- La documentazione stessa si è discostata — gli assistenti ne ereditano gli errori.
- Usa gli assistenti per la forma, verifica la superficie dell'API, non fidarti mai di un'affermazione sulle versioni.

## Postfazione

Ventisei capitoli fa, il Capitolo 1 disegnava una scala a quattro pioli e faceva una sola domanda: *chi decide che cosa succede dopo?*

Tutto ciò che è venuto dopo è stato il macchinario necessario per lasciare che un modello vi rispondesse in sicurezza. Tool per dargli le mani. Struttura per rendere usabile il suo output. Recupero per dargli conoscenza. Workflow per dargli forma. Interruzione per tenere un essere umano nella decisione. Osservabilità per scoprire che cosa abbia effettivamente fatto.

Niente di tutto questo è specifico di NeuronAI, e ben poco è specifico di PHP. Il framework cambierà — è di questo che parla la Sezione 26.1. L'aritmetica della Sezione 1.4, la descrizione dei tool in quattro parti della Sezione 5.4, la differenza fra filtrare al recupero e filtrare dopo, il fatto che un nodo ripreso si riesegue dall'inizio: quelle sopravvivono al framework, e sono ciò che hai davvero imparato.

Resta una domanda, ed è quella da porsi su ogni agent che distribuirai da qui in avanti:

> **Qual è la cosa peggiore che può fare, e che cosa lo ferma?**

Se sai rispondere, sei pronto.
