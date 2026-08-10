# Capitolo 7 — Streaming

## 7.1 Perché lo streaming conta

### Il numero della Sezione 1.4

Una chiamata al modello richiede 1–4 secondi. Un'esecuzione di agent in cinque iterazioni con esecuzione di tool arriva a 10–20 secondi di tempo reale. Nessuno aspetta 20 secondi davanti a uno schermo vuoto.

### Che cosa cambia davvero lo streaming

**Non rende nulla più veloce.** Il tempo totale è identico. Ogni token, ogni chiamata a tool, ogni andata e ritorno richiede esattamente lo stesso tempo.

**Cambia quando l'utente vede il primo token.** Invece di 12 secondi di nulla seguiti da una risposta completa, vede il testo comparire dopo 800 millisecondi e proseguire.

L'attesa percepita è dominata dal tempo al primo token, non dal tempo al completamento. Una risposta che scorre per 15 secondi sembra più veloce di una che blocca per 8. È un fatto ben noto nella progettazione di interfacce in generale, ed è particolarmente marcato con il testo perché l'utente può iniziare a leggere mentre il resto arriva.

### Il secondo beneficio, sottovalutato

Lo streaming ti permette di mostrare **che cosa sta facendo l'agent**, non solo che cosa ha detto alla fine.

I tipi di chunk di NeuronAI includono chiamate a tool e risultati di tool. Quindi puoi rendere:

```
Vediamo, controllo subito.
  → Cerco l'ordine #4471...
  → Trovato. Verifico l'idoneità al rimborso...
L'ordine è idoneo al rimborso completo.
```

È un prodotto completamente diverso da uno spinner. L'utente vede il progresso, capisce perché ci vuole tempo e — cosa importante — può accorgersi che il sistema sta lavorando sul problema giusto prima che finisca. La Sezione 7.4 lo costruisce.

### Quando non fare streaming

- **Lavori batch e in background.** Nessuno sta guardando.
- **Structured output.** Ti serve l'oggetto completo e validato; uno parsato a metà è inutile.
- **Risposte molto brevi.** Fare streaming di una risposta di due parole aggiunge complessità per nulla.
- **Quando devi post-elaborare l'intera risposta** prima di mostrarla — filtraggio, redazione, formattazione.

### Punti chiave

- Lo streaming cambia la latenza percepita, non quella reale.
- Il tempo al primo token è ciò che gli utenti sentono.
- Fare streaming dell'attività dei tool è una funzionalità di prodotto, non solo un indicatore di avanzamento.
- Non per lavori batch, structured output o risposte che devi post-elaborare.

## 7.2 stream() ed events()

### L'API

```php
use App\Neuron\MyAgent;
use NeuronAI\Chat\Messages\UserMessage;

$handler = MyAgent::make()->stream(new UserMessage('How are you?'));

foreach ($handler->events() as $chunk) {
    echo $chunk->content;
}

// I'm fine, thank you! How can I assist you today?
```

Tre passi, e ciascuno è un punto in cui si sbaglia:

**1. `stream()` invece di `chat()`.** Prepara il workflow dell'agent a usare `StreamingNode` invece di `ChatNode` — il terzo scambio di nodo del libro, dopo `ToolNode`/`ParallelToolNode` nella Sezione 5.13 e `StructuredOutputNode` nella Sezione 6.3.

**2. `stream()` restituisce un handler, non un generatore.** Non puoi iterarlo direttamente.

**3. `events()` restituisce il generatore.** E produce **oggetti**, non stringhe. `$chunk->content`, non `$chunk`.

::: {.callout .callout-warning}
[Cambiamento v2 → v3]{.callout-title}

Le versioni precedenti facevano streaming di stringhe semplici per il testo e di istanze di messaggio per le operazioni sui tool. La v3 ha introdotto classi di chunk dedicate. Ogni tutorial più vecchio che troverai mostrerà la forma a stringhe:

```php
// WRONG for v3
foreach (AssistantAgent::make()->stream(new UserMessage($prompt)) as $chunk) {
    echo $chunk;
}
```

È la terza rottura significativa v2 → v3 del libro, dopo i namespace e `getMessage()`. È anche la più comune a sopravvivere nel codice d'esempio pubblicato, perché la forma rotta *sembra* ancora corretta.
:::

### I tipi di chunk

Quattro classi:

| Chunk | Contiene |
|---|---|
| `TextChunk` | Un pezzo del testo di risposta |
| `ReasoningChunk` | Parte del riassunto del ragionamento del modello — solo modelli di ragionamento |
| `ToolCallChunk` | Il modello che richiede l'esecuzione di un tool |
| `ToolResultChunk` | Il risultato dell'esecuzione di un tool |

**Che cosa ricevi dipende dal tuo agent.** Nessun tool collegato significa nessun `ToolCallChunk` né `ToolResultChunk`: puoi iterare aspettandoti solo testo e ragionamento. Vale la pena saperlo prima di scrivere logica di ramificazione che non ti serve.

### Ottenere il messaggio finale

Al termine dello stream, l'handler conserva comunque il risultato assemblato:

```php
$handler = MyAgent::make()->stream(...);

foreach ($handler->events() as $chunk) {
    // stream to the user
}

$message = $handler->getMessage();
echo $message->getContent();
```

Conta più di quanto sembri. Fai streaming verso l'utente *e* ottieni l'`AssistantMessage` completo da persistere, loggare o passare a un controllo di moderazione. Non devi riassemblarlo dai chunk da solo, che è esattamente la cosa tediosa e soggetta a errori che tutti fanno alla prima implementazione di streaming.

### Perché oggetti chunk invece di stringhe

Le note di aggiornamento del framework spiegano il ragionamento, ed è una buona lezione di progettazione.

Fare streaming di istanze di messaggio grezze accoppiava l'applicazione al sistema interno dei messaggi di NeuronAI. Le classi di chunk dedicate creano un confine: il codice della tua interfaccia dipende da un insieme piccolo e stabile di tipi di chunk invece che dall'impianto interno dei messaggi. Quella separazione è ciò che ha reso possibile il sistema di adapter dello stream (Sezione 7.5), e significa che gli interni possono evolvere senza rompere il tuo frontend.

È un caso da manuale di introduzione di un DTO su un confine di livello.

### Punti chiave

- `stream()` → handler → `events()` → generatore di oggetti chunk.
- `$chunk->content`, non `$chunk`.
- Quattro tipi di chunk; quali ricevi dipende dal fatto che l'agent abbia tool.
- `getMessage()` sull'handler ti dà il messaggio completo assemblato a posteriori.

## 7.3 Streaming da CLI

### L'esempio

**`examples/06-streaming.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\AssistantAgent;
use NeuronAI\Chat\Messages\UserMessage;

$prompt = $argv[1] ?? 'Explain the Repository pattern and when using it is a mistake.';

$start   = \microtime(true);
$first   = null;

$handler = AssistantAgent::make()->stream(new UserMessage($prompt));

foreach ($handler->events() as $chunk) {
    $first ??= \microtime(true);

    echo $chunk->content;
    \flush();
}

$end = \microtime(true);

\printf(
    "\n\n[first token: %.2fs | total: %.2fs]\n",
    $first - $start,
    $end - $start
);
```

```bash
php examples/06-streaming.php
```

### Il confronto che vale la pena misurare

Esegui lo stesso prompt due volte — una con `chat()`, una con `stream()` — e confronta i tempi.

Tempo totale: grosso modo identico. Tempo al primo output visibile: 4,1 secondi contro 0,7. *Il lavoro ha richiesto lo stesso tempo; l'attesa no.*

Misurare il tempo al primo token nello script vale le quattro righe extra. Trasforma un'affermazione in un numero, sul tuo hardware e con il tuo provider.

### Il problema del buffering

`flush()` è lì per un motivo, e il motivo diventa molto più grande nel Capitolo 21.

PHP fa buffering dell'output. Lo fa anche il web server. Lo fa anche il reverse proxy. Uno qualunque di loro può trattenere i token che hai accuratamente inviato in streaming e rilasciarli in un unico blocco alla fine — a quel punto hai tutta la complessità dello streaming e nessuno dei benefici.

Da CLI, `flush()` di solito basta. In contesto web devi occuparti anche di:

- L'impostazione `output_buffering` di PHP
- `ob_end_flush()` se un buffer è già aperto
- `proxy_buffering` e `fastcgi_buffering` di nginx
- Qualunque CDN o proxy davanti all'applicazione

La documentazione AG-UI del framework include l'avvertenza: manda gli header di protocollo e fai flush dopo ogni riga, altrimenti lo stream può restare bloccato nei buffer di output di PHP o nei proxy.

Qui viene menzionato e nel Capitolo 21 viene risolto per bene. Chi lo incontra per la prima volta in produzione ci perde una giornata.

### Nota sulle chiamate parallele ai tool

La Sezione 5.13 ha stabilito che `pcntl` è solo CLI. Lo streaming è uno dei pochi contesti in cui hai entrambe le cose disponibili insieme: un agent CLI può fare streaming *e* eseguire tool in parallelo. Vale la pena saperlo, perché rende l'agent CLI del Progetto finale A un obiettivo davvero capace invece di un giocattolo.

### Punti chiave

- `flush()` dopo ogni chunk.
- Misura il tempo al primo token; è il numero che giustifica la funzionalità.
- Il buffering esiste su quattro livelli in uno stack web — Capitolo 21.

## 7.4 Streaming con i tool

### I tool funzionano dentro lo stream

Non serve nulla di speciale. L'agent gestisce le chiamate a tool in mezzo allo stream e prosegue fino alla risposta finale. Semplicemente ricevi tipi di chunk aggiuntivi.

### Il pattern completo

```php
use App\Neuron\MyAgent;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Tools\Tool;

$handler = MyAgent::make()
    ->addTool(
        Tool::make(
            'get_server_configuration',
            'retrieve the server network configuration'
        )->addProperty(/* ... */)->setCallable(/* ... */)
    )
    ->stream(
        new UserMessage("What's the IP address of the server?")
    );

foreach ($handler->events() as $chunk) {
    if ($chunk instanceof ToolCallChunk) {
        echo "\n- Calling tool: " . $chunk->tool->getName();
        echo "\n- Input: " . json_encode($chunk->tool->getInputs());
        continue;
    }

    if ($chunk instanceof ToolResultChunk) {
        echo "\n- Tool " . $chunk->tool->getName() . " completed";
        echo "\n- Result: " . $chunk->tool->getResult();
        continue;
    }

    echo $chunk->content;
}
```

Output:

```
Let me retrieve the server configuration.
- Calling tool: get_server_configuration
- Tool get_server_configuration completed
The IP address of the server is: 192.168.0.10
```

### Che cosa portano i chunk

Entrambi i chunk dei tool contengono l'**istanza del tool**, che è più di un nome:

- `$chunk->tool->getName()`
- `$chunk->tool->getInputs()` — gli argomenti scelti dal modello
- `$chunk->tool->getResult()` — sul chunk del risultato

Avere gli argomenti a disposizione è ciò che rende possibile una visualizzazione dell'avanzamento davvero informativa. Non "sto lavorando…" ma "Cerco gli ordini del cliente 4471".

### Il punto sulla sicurezza, detto con fermezza

**Non riversare input e risultati grezzi dei tool agli utenti finali.**

L'esempio CLI qui sopra è una vista di debug, e per quello è perfetto. In un prodotto rivolto agli utenti fa trapelare:

- Identificativi interni e chiavi di database
- Query SQL, rivelando il tuo schema
- Endpoint API e nomi di parametri
- Qualunque cosa contenuta in un messaggio d'errore

Mappa invece su etichette leggibili:

```php
$labels = [
    'get_order_status'  => 'Looking up your order',
    'search_orders'     => 'Searching your order history',
    'get_refund_policy' => 'Checking the refund policy',
];

foreach ($handler->events() as $chunk) {
    if ($chunk instanceof ToolCallChunk) {
        $name = $chunk->tool->getName();
        echo "\n" . ($labels[$name] ?? 'Working on it') . "...\n";
        continue;
    }

    if ($chunk instanceof ToolResultChunk) {
        continue; // never shown to the user
    }

    echo $chunk->content;
}
```

La lista di permessi conta: `$labels[$name] ?? 'Working on it'` significa che un tool appena aggiunto degrada a un messaggio generico invece di far trapelare il suo nome interno. Stesso ragionamento di `only()` invece di `exclude()` nella Sezione 5.8: le liste di permessi falliscono in sicurezza.

### Il principio di esperienza utente

Una riga di avanzamento per un tool che impiega 200 ms è rumore visivo. Una riga di avanzamento per uno che impiega quattro secondi è essenziale.

Valuta di mostrare l'attività dei tool solo dopo un breve ritardo, così le chiamate veloci restano invisibili e quelle lente si spiegano da sole. È il comportamento di ogni stato di caricamento ben progettato, e si applica qui direttamente.

### Punti chiave

- I tool fanno streaming automaticamente; ricevi `ToolCallChunk` e `ToolResultChunk`.
- I chunk portano l'istanza del tool, compresi gli argomenti scelti dal modello.
- Non mostrare mai input o risultati grezzi dei tool agli utenti finali: mappa su etichette con un fallback sicuro.
- Mostra l'avanzamento solo per i tool lenti.

## 7.5 Adapter dello stream e protocolli di interfaccia

### Il problema che gli adapter risolvono

Il tuo agent produce chunk NeuronAI. Il tuo frontend parla un protocollo — il formato data stream dell'AI SDK di Vercel, oppure AG-UI. Senza adapter scrivi a mano la traduzione, inclusi eventi di ciclo di vita dei messaggi, formattazione degli eventi e tracciamento degli ID, e la riscrivi ogni volta che il protocollo si muove.

### Il progetto

Gli adapter sono traduttori fra gli eventi di streaming interni di NeuronAI e uno specifico protocollo di frontend. Passane uno a `events()`:

```php
use NeuronAI\Chat\Messages\Stream\Adapters\AGUIAdapter;

$handler = MyAgent::make()->stream(new UserMessage('What is the square root of 144?'));

$stream = $handler->events(new AGUIAdapter());

foreach ($stream as $line) {
    echo $line;
}
```

Lo stesso per Vercel:

```php
use NeuronAI\Chat\Messages\Stream\Adapters\VercelAIAdapter;

$stream = $handler->events(new VercelAIAdapter());
```

**Il codice del tuo agent non cambia.** L'adapter sta al confine. È lo stesso progetto guidato dalle interfacce dello scambio di provider della Sezione 3.6, applicato al lato output: l'architettura è coerente, non casuale.

### Un endpoint AG-UI completo

```php
use NeuronAI\Chat\Messages\Stream\Adapters\AGUIAdapter;
use NeuronAI\Chat\Messages\UserMessage;

$input = json_decode(file_get_contents('php://input'), true);

$messages = [];
foreach ($input['messages'] as $message) {
    if ($message['role'] === 'user') {
        $messages[] = new UserMessage($message['content']);
    }
}

$adapter = new AGUIAdapter(
    threadId: $input['threadId'],
    runId: $input['runId'],
);

foreach ($adapter->getHeaders() as $name => $value) {
    header("{$name}: {$value}");
}

$stream = MyAgent::make()->stream($messages)->events($adapter);

foreach ($stream as $line) {
    echo $line;
    flush();
}
```

Quattro cose da notare:

**I client AG-UI inviano in POST un payload `RunAgentInput`.** Non aprono semplicemente una connessione. Porta `threadId`, `runId`, la cronologia dei messaggi e altro.

**Rimanda indietro gli identificativi.** Passa `threadId` e `runId` al costruttore così che l'adapter li restituisca in `RUN_STARTED` e `RUN_FINISHED`. Ometterli fa sì che l'adapter ne inventi di propri — va bene per i test, sbagliato per un client reale che si aspetta di correlare lo stream con l'esecuzione che ha richiesto.

**`getHeaders()` ti dà gli header SSE.** Mandali.

**`flush()` dopo ogni riga.** L'avvertenza della Sezione 7.3, e i documenti la ripetono qui per una buona ragione.

### La mappatura degli eventi

| Chunk NeuronAI | Eventi AG-UI |
|---|---|
| Ciclo di vita dell'esecuzione | `RUN_STARTED`, `RUN_FINISHED` |
| `TextChunk` | `TEXT_MESSAGE_START`, `TEXT_MESSAGE_CONTENT`, `TEXT_MESSAGE_END` |
| `ReasoningChunk` | `REASONING_START`, `REASONING_MESSAGE_START`, `REASONING_MESSAGE_CONTENT`, `REASONING_MESSAGE_END`, `REASONING_END` |
| `ToolCallChunk` | `TOOL_CALL_START`, `TOOL_CALL_ARGS`, `TOOL_CALL_END` |
| `ToolResultChunk` | `TOOL_CALL_RESULT` |

### Due limitazioni da dichiarare onestamente

**Solo tool lato server.** I tool collegati al tuo agent girano sul tuo server, e il client viene informato tramite gli eventi `TOOL_CALL_*`. I tool *definiti dal frontend* di AG-UI — elencati nel campo `tools` di `RunAgentInput` ed eseguiti dal client — non sono gestiti dall'adapter.

**Nessun evento di stato condiviso.** L'adapter non emette `STATE_SNAPSHOT`, `STATE_DELTA` o `MESSAGES_SNAPSHOT`, quindi le funzionalità di sincronizzazione dello stato dei client AG-UI non sono disponibili attraverso di esso.

Se stai valutando CopilotKit o un frontend AG-UI simile, conosci queste due lacune prima di impegnarti in un progetto che ne dipende.

### Adapter personalizzati

```php
interface StreamAdapterInterface
{
    public function transform(object $chunk): iterable;
    public function getHeaders(): array;
    public function start(): iterable;
    public function end(): iterable;
}
```

Quattro metodi. `transform()` fa il lavoro; `start()` e `end()` gestiscono il ciclo di vita del protocollo; `getHeaders()` fornisce gli header di trasporto.

Puoi anche estendere `SSEAdapter` quando ti serve solo cambiare la trasformazione.

### Il caso d'uso da evidenziare

Gli adapter possono spingere verso un trasporto esterno come Pusher. Significa che un agent in esecuzione **dentro un job in background** può fare streaming del proprio avanzamento verso un browser con cui non ha alcuna connessione diretta.

È la risposta a un problema che altrimenti sembrerebbe irrisolvibile: le esecuzioni lunghe degli agent appartengono a un queue worker (l'aritmetica della latenza della Sezione 1.4, il vincolo `pcntl` della Sezione 5.13), ma un queue worker non ha alcuna connessione HTTP con l'utente. Un adapter che spinge verso un trasporto websocket colma esattamente quel divario.

Il Capitolo 21 lo costruisce in Laravel.

### Punti chiave

- Gli adapter traducono i chunk NeuronAI in un protocollo di frontend; il codice del tuo agent resta invariato.
- I client AG-UI inviano un payload in POST: rimanda indietro `threadId` e `runId`.
- Due lacune: nessun tool definito dal frontend, nessun evento di stato condiviso.
- Un adapter su un trasporto websocket permette a un queue worker di fare streaming verso un browser.

## Esercizi del capitolo

1. **Misuralo.** Converti un agent del Capitolo 5 da `chat()` a `stream()`. Misura il tempo al primo token in entrambi i modi e annota entrambi i numeri. Se il divario è piccolo, chiediti perché: un modello locale veloce su una risposta breve non ha davvero bisogno di streaming, e saperlo è utile quanto la funzionalità stessa.

2. **Mostra il lavoro.** Aggiungi la visualizzazione dell'avanzamento dei tool con una lista di permessi di etichette e un fallback sicuro. Poi aggiungi un nuovo tool senza aggiungerne l'etichetta e conferma che degrada al messaggio generico invece di far trapelare il suo nome interno.

3. **Scegli un adapter.** Abbozza quale adapter useresti per il tuo stack di frontend e decidi se una delle due limitazioni di AG-UI ti riguarderebbe. Se non ne sei sicuro, quella è la risposta da scoprire prima di costruire, non dopo.
