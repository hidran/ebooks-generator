# Come usare questo libro {.unnumbered}

## La struttura in tre tempi

Quasi ogni argomento di questo libro viene presentato tre volte, con un livello di comfort crescente.

**Prima la teoria.** Cosa succede davvero sotto il cofano — il ciclo dell'agent, i token e i costi, gli embedding, il modello event-driven. Niente codice. Queste sezioni esistono perché, quando un framework fa qualcosa al posto tuo, tu sappia esattamente cosa sta facendo.

**Poi PHP puro.** La stessa idea implementata con Composer e uno script CLI: niente framework, niente magia, niente service container. Vedi ogni oggetto costruito e ogni chiamata eseguita.

**Poi Laravel.** Di nuovo la stessa idea, integrata in un'applicazione vera: dependency injection, Eloquent, code, HTTP, un'interfaccia che un utente può guardare.

Quest'ordine — "prima nudo, poi vestito" — è deliberato. Gli sviluppatori PHP tendono a diffidare della magia, e fanno bene: il modo più rapido per rendere credibile un framework è mostrare che cosa ha sostituito. Se conosci già bene Laravel puoi attraversare in fretta le implementazioni in PHP puro, ma non saltarle: le Parti da II a IV sono dove i concetti vengono davvero insegnati, e la Parte V li dà tutti per acquisiti.

## Le sei parti

**Parte I — Fondamenta** (Capitoli 1–2). Nessun codice. La scala dell'autonomia, il ciclo dell'agent, l'anatomia di una chiamata al modello, quanto costa una context window, perché il prompting non è programmazione, dove si colloca NeuronAI fra i framework Python e com'è fatto NeuronAI. Due capitoli, e sono quelli che cambiano il modo in cui progetti.

**Parte II — PHP puro e Composer** (Capitoli 3–10). Setup e il tuo primo agent, messaggi e memoria, i tool in profondità, structured output con validazione, streaming, multimodalità, MCP e observability con valutazione in CI. È la parte più lunga del libro e il suo nucleo.

**Parte III — Retrieval** (Capitoli 11–12). Perché il retrieval esiste e che cosa non risolve, poi la pipeline NeuronAI dall'inizio alla fine: loader, splitter, embedding, vector store, filtri sui metadati, reindicizzazione e pre- e post-processor.

**Parte IV — Workflow** (Capitoli 13–16). Il modello event-driven, cicli e diramazioni, stato tipizzato, streaming dall'interno di un workflow, human-in-the-loop con checkpoint e ripresa, e orchestrazione multi-agente.

**Parte V — Laravel** (Capitoli 17–23). L'SDK, facade e dependency injection, cronologia in Eloquent, multi-tenancy, tool sui tuoi modelli veri, retrieval sui dati dell'applicazione, streaming SSE e Livewire, workflow di approvazione in produzione, controllo dei costi, resilienza, sicurezza e una checklist di deploy.

**Parte VI — Progetti finali** (Capitoli 24–26). Due progetti completi, poi strategia di versione, l'ecosistema circostante e lo sviluppo assistito dall'AI.

## Eseguire il codice

### Il repository di accompagnamento

Gli esempi sono pensati per essere digitati, ma esistono anche, pronti da eseguire, su **[github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book)**:

```
neuronai-php-book/
├── composer.json
├── phpstan.neon           # level 8, run over every example
├── evaluation.php         # eval output config (Chapter 10)
├── .env.example
├── chapters/
│   ├── Support/           # ProviderFactory and Env, shared by every chapter
│   ├── Ch03/ … Ch15/      # one directory per chapter
│   │   └── run/           # scripts you execute
└── tests/                 # API contract suite
```

```bash
git clone https://github.com/hidran/neuronai-php-book.git
cd neuronai-php-book && composer install
cp .env.example .env
php chapters/Ch03/run/chat.php "Explain readonly vs final in PHP 8"
```

Il riquadro all'inizio di ogni capitolo rimanda direttamente alla sua cartella. Il repository include un `composer.lock` committato, quindi l'API che ottieni è l'API su cui questo libro è stato scritto, anche fra anni: se un listato non concorda con la libreria che hai installato oggi, il lock file è l'arbitro di ciò che il testo intendeva.

Include anche una suite di test che fissa ogni classe, metodo e argomento con nome da cui il libro dipende. Esegui `composer check` e ti dirà, capitolo per capitolo, che cosa ha cambiato la release corrente. È una garanzia più onesta di quella che una pagina stampata può offrire da sola.

### Provider, e come non spendere soldi

Il costo delle API è la ragione numero uno per cui si abbandona a metà un progetto come questo. I laboratori sono strutturati perché non sia un fattore.

**Installa Ollama e scarica due modelli.** Tutto quello che c'è nelle Parti da II a IV è pensato per girare in locale, gratis e offline:

```bash
ollama pull qwen2.5:7b        # chat, tool calling, structured output
ollama pull nomic-embed-text  # embedding per la Parte III
```

`qwen2.5:7b` è il modello locale consigliato perché gestisce con competenza il tool calling e lo structured output, cosa che molti modelli piccoli non fanno. Se la tua macchina fatica, una quantizzazione più piccola completa comunque ogni laboratorio, solo in modo meno affidabile — e osservare un modello più debole sbagliare la scelta del tool è genuinamente istruttivo.

**Usa un provider a pagamento solo dove la qualità è il punto.** Anthropic, OpenAI e Gemini compaiono negli esercizi che dipendono dalla qualità di tool calling o structured output di un modello di frontiera, e nella Parte V dove l'argomento è il comportamento in produzione. Ognuno di questi esercizi lo dichiara in apertura.

Il Capitolo 3 dedica un'intera sezione allo scambio di provider, perché un cambio di provider su una riga è la funzionalità di NeuronAI di valore più immediato, ed è quella che ti impedisce di restare bloccato mentre stai ancora imparando.

## Convenzioni

**Codice.** PHP 8.2+, `declare(strict_types=1)` nei file applicativi, tipi espliciti dove aiutano e segreti nell'ambiente invece che nel sorgente. I blocchi di codice sono completi abbastanza da girare, salvo diversa indicazione; quando uno snippet è un frammento, la classe o funzione circostante è mostrata nel blocco immediatamente precedente.

**Nomi.** Ogni nome di classe, namespace, metodo, pacchetto, comando, percorso e variabile d'ambiente è scritto esattamente come devi digitarlo. Dove la documentazione ufficiale mostra un nome diverso da quello che funziona, il libro usa quello che funziona e l'Appendice A registra la discrepanza.

**Note di versione.** Dove un'API è cambiata fra major, o dove il materiale pubblicato mostra ancora la forma vecchia, il testo lo segnala nel punto d'uso. Non sono digressioni: sono la differenza fra codice che gira e codice che no.

**In pratica.** Brevi riquadri marcati *In pratica* portano tecnica che non rientra nella linea principale del discorso — quello che ti direbbe un collega guardando lo schermo insieme a te.

**Punti chiave.** Ogni sezione si chiude con le tre o quattro affermazioni che vale la pena ricordare. Se stai ripassando invece di leggere, sono un indice utilizzabile dell'argomentazione del libro.

## Laboratori e progetti finali

Sedici laboratori sono distribuiti nel libro, ciascuno nel capitolo di cui esercita il materiale:

| Lab | Capitolo | Cosa costruisci |
|---|---|---|
| 1 | 3 | Lo scheletro del progetto in PHP puro e il tuo primo agent funzionante, commutabile su tre provider |
| 2 | 4 | Una chat CLI interattiva multi-turno con cronologia su disco e un comando `/reset` |
| 3 | 5 | Un agent meteo e calcolatrice — un tool custom su un'API pubblica più `CalculatorToolkit` |
| 4 | 5 | Un agent analista di database su uno schema reale, in sola lettura, con lo schema ristretto alle tabelle rilevanti |
| 5 | 6 | Estrazione tipizzata e validata: email d'ordine in testo libero verso un DTO `Order` con righe e totali |
| 6 | 8 | Un agent che legge lo screenshot di una fattura e restituisce un DTO strutturato |
| 7 | 10 | Una suite PHPUnit su un agent con provider e tool fake — nessuna rete, completamente deterministica |
| 8 | 12 | Retrieval sulla documentazione a costo zero: ingestion di Markdown, `FileVectorStore`, embedding Ollama |
| 9 | 12 | Lo stesso retrieval su uno store di produzione con ricerca ibrida |
| 10 | 16 | La fabbrica di contenuti — ricercatore, scrittore, revisore con ciclo di correzione, approvazione umana, publisher |
| 11 | 17 | `POST /api/ask` risposto tramite la facade: cinque minuti dal `composer require` alla prima risposta |
| 12 | 18 | Chat persistente per utente con più thread e cronologia su database |
| 13 | 19 | Un agent e-commerce con `search_orders`, `get_order_status` e `request_refund` — i rimborsi richiedono approvazione |
| 14 | 20 | Una knowledge base aziendale: articoli Eloquent, indicizzati via coda, con citazione della fonte |
| 15 | 21 | Un'interfaccia di chat in streaming token per token, con indicatore "sto usando il tool X" |
| 16 | 22 | Approvazione rimborsi end to end: l'agent prepara la pratica, si ferma, un manager approva, il workflow riprende |

Alcuni laboratori sono svolti dall'inizio alla fine, codice compreso. Altri sono specificati anziché risolti — requisiti, criteri di accettazione e i suggerimenti che servono, con l'implementazione lasciata a te. La proporzione si sposta deliberatamente man mano che il libro avanza: alla Parte V hai già visto ogni pattern che il laboratorio richiede, e ricevere la risposta pronta sprecherebbe l'esercizio.

I laboratori *sono* il libro. Leggere un capitolo sui tool ti insegna cos'è un tool; scriverne uno ti insegna perché le descrizioni dei tool sono prompt engineering. Prevedi tempo vero per loro.

I due progetti finali della Parte VI sono deliberatamente più grandi e deliberatamente sotto-specificati: dichiarano requisiti, non passi, perché a quel punto decidere i passi è proprio l'abilità sotto esame.

## Le appendici

**Appendice A — Dove la documentazione diverge dal codice.** Quarantaquattro discrepanze verificate fra la documentazione ufficiale di NeuronAI e la libreria distribuita, raggruppate per capitolo, con script di verifica che le risolvono in blocco sulla versione che hai installato. Leggila prima di scrivere codice di produzione.

**Appendice B — Glossario.** Il vocabolario, definito una volta sola.

## Se hai fretta

Se ti serve qualcosa che funzioni questa settimana invece di capire il campo, leggi il Capitolo 1 (cambierà quello che deciderai di costruire), il Capitolo 3 (setup e primo agent), il Capitolo 5 (tool) e il Capitolo 6 (structured output). Basta per mettere in produzione una funzionalità utile di livello 3.

Poi torna al Capitolo 10, perché la differenza fra una demo e un prodotto è sapere che cosa ha fatto davvero il tuo agent.
