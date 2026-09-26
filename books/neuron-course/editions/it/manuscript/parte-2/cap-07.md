# Capitolo 7 — Streaming

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

La versione eseguibile di ogni listato che segue si trova in [`chapters/Ch07`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch07), nel repository di accompagnamento. Clonalo, esegui `composer install` e gli esempi funzionano su un Ollama locale senza alcuna API key.
:::

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

## 7.2 stream() e i suoi chunk

### L'API

```php
use App\Neuron\MyAgent;
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\UserMessage;

$stream = MyAgent::make()->stream(new UserMessage('How are you?'));

foreach ($stream as $chunk) {
    if ($chunk instanceof TextChunk) {
        echo $chunk->content;
    }
}

// I'm fine, thank you! How can I assist you today?
```

Tre cose da notare, e ciascuna è un punto in cui si sbaglia:

**1. `stream()` invece di `chat()`, ma lo stesso nodo.** Entrambi i verbi eseguono lo stesso `ChatNode`. `stream()` registra sulla run un flag che dice al nodo di chiamare l'endpoint di streaming del provider invece di quello bufferizzato, e di produrre ogni pezzo man mano che arriva. Lo streaming è una scelta di trasporto, non un percorso di esecuzione diverso — ed è per questo che un middleware collegato a `ChatNode` copre entrambi, e che tutto ciò che il Capitolo 5 ha detto sui tool vale anche a metà stream.

**2. `stream()` restituisce il generatore.** Non c'è una seconda chiamata: iteri ciò che torna indietro. Il tipo di ritorno dichiarato è `Generator|AgentState`, e il ramo `AgentState` si verifica solo quando colleghi *sia* uno stream adapter sia un canale (Sezione 7.5): in quel caso l'agent fa streaming verso il canale in modo eager e ti consegna lo stato finale. Nel caso semplice è sempre un generatore. L'analisi statica vede l'unione, quindi gli script di accompagnamento la restringono una volta con `\assert($stream instanceof Generator)`.

**3. Produce oggetti, non stringhe — e non solo testo.** Filtra con `instanceof`. Fare `echo` di `$chunk->content` per ogni elemento funziona fino al primo elemento che non è un chunk di testo: una tool call, un frammento di argomenti di un tool, oppure l'`InterruptEvent` che segnala una run in pausa. Nessuno di questi ha una proprietà `content`.

::: {.callout .callout-warning}
[Codice di streaming più vecchio]{.callout-title}

Due forme precedenti di questa API sopravvivono in tutorial e repository d'esempio:

```php
// v2: plain strings - wrong since v3
foreach (AssistantAgent::make()->stream(new UserMessage($prompt)) as $chunk) {
    echo $chunk;
}

// v3: a handler, then events() - wrong in v4
foreach (AssistantAgent::make()->stream(new UserMessage($prompt))->events() as $chunk) {
    echo $chunk->content;
}
```

La forma v2 è la più insidiosa delle due, perché in v4 la sua forma esterna è di nuovo giusta — `stream()` lo iteri davvero direttamente — quindi la riga rotta sembra quasi corretta. Quello che è sbagliato è l'interno del ciclo: ogni elemento è un oggetto, e solo alcuni portano testo.
:::

### I tipi di chunk

Tutti sotto `NeuronAI\Chat\Messages\Stream\Chunks`, tutti estendono `StreamChunk`, tutti con un `toArray()`:

| Chunk | Contiene |
|---|---|
| `TextChunk` | Un pezzo del testo di risposta, in `content` |
| `ReasoningChunk` | Parte del riassunto del ragionamento del modello — solo modelli di ragionamento |
| `ToolArgumentChunk` | Un frammento degli argomenti di una tool call che il modello sta ancora scrivendo |
| `ToolCallChunk` | Una tool call che il modello ha deciso di fare |
| `ToolResultChunk` | Il risultato di quella chiamata, una volta eseguita |
| `ImageChunk`, `AudioChunk` | Media generati, dai modelli che li producono |

**Che cosa ricevi dipende dal tuo agent e dal tuo provider.** Nessun tool collegato significa nessun chunk di tool: puoi iterare aspettandoti solo testo e ragionamento. `ToolArgumentChunk` compare solo con i provider che trasmettono gli argomenti in modo incrementale; Gemini e Ollama li consegnano in un unico pezzo e non lo emettono mai. Vale la pena saperlo prima di scrivere logica di ramificazione che non ti serve.

Oltre ai chunk, il generatore può portare altri due tipi di oggetto: l'`InterruptEvent` che segnala una run in pausa per approvazione (Capitolo 15), e gli eventi di avanzamento che un nodo di workflow sceglie di produrre (Capitolo 14). Un ciclo che gestisce i tipi di chunk che gli interessano e ignora tutto il resto è corretto per costruzione, e resta corretto quando il mese prossimo aggiungi dei tool.

### Ottenere il messaggio finale

Quando il ciclo termina, il valore di ritorno del generatore è la run conclusa:

```php
$stream = MyAgent::make()->stream(...);

foreach ($stream as $chunk) {
    // stream to the user
}

$state = $stream->getReturn();
echo $state->getMessage()?->getContent();
```

`getReturn()` è PHP puro — ogni generatore ne ha uno, disponibile una volta terminato — e qui restituisce lo stesso `AgentState` che avrebbe restituito `chat()`. `getMessage()` è nullable perché una run andata in pausa prima che un'inferenza fosse completata non ha ancora un messaggio dell'assistente; dopo uno stream ordinario è la risposta completa.

Conta più di quanto sembri. Fai streaming verso l'utente *e* ottieni l'`AssistantMessage` completo da persistere, loggare o passare a un controllo di moderazione. Non devi riassemblarlo dai chunk da solo, che è esattamente la cosa tediosa e soggetta a errori che tutti fanno alla prima implementazione di streaming.

### Perché oggetti chunk invece di stringhe

Le note di aggiornamento del framework spiegano il ragionamento, ed è una buona lezione di progettazione.

Fare streaming di istanze di messaggio grezze accoppiava l'applicazione al sistema interno dei messaggi di NeuronAI. Le classi di chunk dedicate creano un confine: il codice della tua interfaccia dipende da un insieme piccolo e stabile di tipi di chunk invece che dall'impianto interno dei messaggi. Quella separazione è ciò che ha reso possibile il sistema di adapter dello stream (Sezione 7.5), e significa che gli interni possono evolvere senza rompere il tuo frontend.

È un caso da manuale di introduzione di un DTO su un confine di livello.

### Punti chiave

- `stream()` restituisce direttamente il generatore; iteralo.
- Produce oggetti di diversi tipi — filtra con `instanceof TextChunk` prima di toccare `content`.
- Quali chunk ricevi dipende dal fatto che l'agent abbia tool e da come il provider fa streaming.
- `getReturn()` ti dà l'`AgentState` finale, con il messaggio completo assemblato.

## 7.3 Streaming da CLI

### L'esempio

**`examples/06-streaming.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\AssistantAgent;
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\UserMessage;

$prompt = $argv[1] ?? 'Explain the Repository pattern and when using it is a mistake.';

$start = \microtime(true);
$first = null;

$stream = AssistantAgent::make()->stream(new UserMessage($prompt));

// No adapter and no channel attached, so stream() returned a Generator.
\assert($stream instanceof Generator);

foreach ($stream as $chunk) {
    if (!$chunk instanceof TextChunk) {
        continue;
    }

    $first ??= \microtime(true);

    echo $chunk->content;
    \flush();
}

$end = \microtime(true);

\printf(
    "\n\n[first token: %.2fs | total: %.2fs]\n",
    ($first ?? $end) - $start,
    $end - $start,
);
```

```bash
php examples/06-streaming.php
```

Nota dove si ferma il cronometro: al primo `TextChunk`, non al primo elemento. Un modello di ragionamento può passare secondi a produrre chunk di ragionamento prima che compaia una parola della risposta, ed è la risposta che l'utente sta aspettando.

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
use App\Neuron\Tools\ServerConfigurationTool;
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\Stream\Chunks\ToolCallChunk;
use NeuronAI\Chat\Messages\Stream\Chunks\ToolResultChunk;
use NeuronAI\Chat\Messages\UserMessage;

$stream = MyAgent::make()
    ->addTool(new ServerConfigurationTool())
    ->stream(
        new UserMessage("What's the IP address of the server?")
    );

foreach ($stream as $chunk) {
    if ($chunk instanceof ToolCallChunk) {
        echo "\n- Calling tool: " . $chunk->tool->getName();
        echo "\n- Input: " . json_encode($chunk->tool->getInputs()) . "\n";
        continue;
    }

    if ($chunk instanceof ToolResultChunk) {
        echo "- Tool " . $chunk->tool->getName() . " completed";
        echo "\n- Result: " . $chunk->tool->getResult() . "\n";
        continue;
    }

    if ($chunk instanceof TextChunk) {
        echo $chunk->content;
    }
}
```

`ServerConfigurationTool` è una normale sottoclasse di `Tool` nella forma del Capitolo 5: un `$name` pari a `get_server_configuration`, una descrizione e un `__invoke()` che restituisce la configurazione. La versione di accompagnamento risponde con un valore fisso, così l'esempio non ha bisogno della rete.

Output:

```
- Calling tool: get_server_configuration
- Input: []
- Tool get_server_configuration completed
- Result: {"hostname":"app-01","ip":"192.168.0.10","gateway":"192.168.0.1"}
The IP address of the server is 192.168.0.10.
```

### Che cosa portano i chunk

Entrambi i chunk dei tool contengono un `ToolCall` in `$chunk->tool` — il record di una singola invocazione, non il tool eseguibile che hai registrato. Sono dati semplici:

- `$chunk->tool->getName()`
- `$chunk->tool->getInputs()` — gli argomenti scelti dal modello
- `$chunk->tool->getCallId()` — l'identificativo che abbina una chiamata al suo risultato
- `$chunk->tool->getResult()` — sul chunk del risultato

Avere gli argomenti a disposizione è ciò che rende possibile una visualizzazione dell'avanzamento davvero informativa. Non "sto lavorando…" ma "Cerco gli ordini del cliente 4471". Il call ID è ciò che permette a un'interfaccia di trasformare sul posto la riga "in chiamata" in una riga "fatto", invece di stampare due righe scollegate — e quando il modello chiama lo stesso tool due volte nello stesso turno, è l'unica cosa che distingue le due chiamate.

Se il tuo provider trasmette gli argomenti dei tool, i `ToolArgumentChunk` arrivano prima del `ToolCallChunk`, ciascuno con un `delta` di JSON grezzo e parziale. Esistono per un'anteprima dal vivo del tipo "l'agent sta scrivendo una query". Non farne mai il parsing; aspetta il `ToolCallChunk`, che porta gli input completi.

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

foreach ($stream as $chunk) {
    if ($chunk instanceof ToolCallChunk) {
        $name = $chunk->tool->getName();
        echo "\n" . ($labels[$name] ?? 'Working on it') . "...\n";
        continue;
    }

    if ($chunk instanceof ToolResultChunk) {
        continue; // never shown to the user
    }

    if ($chunk instanceof TextChunk) {
        echo $chunk->content;
    }
}
```

La lista di permessi conta: `$labels[$name] ?? 'Working on it'` significa che un tool appena aggiunto degrada a un messaggio generico invece di far trapelare il suo nome interno. Stesso ragionamento di `only()` invece di `exclude()` nella Sezione 5.8: le liste di permessi falliscono in sicurezza. Lo stesso vale per l'ultimo ramo: tutto ciò che il ciclo non riconosce viene scartato, non stampato.

### Il principio di esperienza utente

Una riga di avanzamento per un tool che impiega 200 ms è rumore visivo. Una riga di avanzamento per uno che impiega quattro secondi è essenziale.

Valuta di mostrare l'attività dei tool solo dopo un breve ritardo, così le chiamate veloci restano invisibili e quelle lente si spiegano da sole. È il comportamento di ogni stato di caricamento ben progettato, e si applica qui direttamente.

### Punti chiave

- I tool fanno streaming automaticamente; ricevi `ToolCallChunk` e `ToolResultChunk`, ed eventualmente prima dei delta `ToolArgumentChunk`.
- I chunk portano un record `ToolCall`: nome, argomenti, call ID e risultato.
- Non mostrare mai input o risultati grezzi dei tool agli utenti finali: mappa su etichette con un fallback sicuro.
- Mostra l'avanzamento solo per i tool lenti.

## 7.5 Adapter dello stream e protocolli di interfaccia

### Il problema che gli adapter risolvono

Il tuo agent produce chunk NeuronAI. Il tuo frontend parla un protocollo — il formato data stream dell'AI SDK di Vercel, oppure AG-UI. Senza adapter scrivi a mano la traduzione, inclusi eventi di ciclo di vita dei messaggi, formattazione degli eventi e tracciamento degli ID, e la riscrivi ogni volta che il protocollo si muove.

### Il progetto

Un adapter traduce gli oggetti di stream nativi di NeuronAI in un protocollo di frontend. Lo colleghi all'agent con `setStreamAdapter()`, e da quel momento la stessa chiamata `stream()` produce **eventi di protocollo** invece di chunk:

```php
use NeuronAI\Agent\Adapters\AGUIAdapter;
use NeuronAI\Chat\Messages\UserMessage;

$stream = MyAgent::make()
    ->setStreamAdapter(new AGUIAdapter(threadId: 'thread_123'))
    ->stream(new UserMessage('What is the square root of 144?'));

foreach ($stream as $event) {
    echo json_encode($event) . "\n";
}

// {"type":"RUN_STARTED","runId":"run_...","threadId":"thread_123"}
// {"type":"TEXT_MESSAGE_START","messageId":"msg_...","role":"assistant"}
// {"type":"TEXT_MESSAGE_CONTENT","messageId":"msg_...","delta":"The square root"}
// ...
```

Lo stesso per Vercel:

```php
use NeuronAI\Agent\Adapters\VercelAIAdapter;

$agent->setStreamAdapter(new VercelAIAdapter());
```

Ogni elemento è un `NeuronAI\Workflow\Streaming\ProtocolEvent`: un `type` e un array `data` serializzabile in JSON, un oggetto per evento sulla rete. Gli adapter integrati stanno sotto `NeuronAI\Agent\Adapters`, perché codificano concetti dell'agent — tool call, approvazioni — mentre il contratto che implementano appartiene al livello dei workflow, dove qualunque workflow può usarlo.

**Il codice del tuo agent non cambia.** L'adapter sta al confine. È lo stesso progetto guidato dalle interfacce dello scambio di provider della Sezione 3.6, applicato al lato output: l'architettura è coerente, non casuale.

Un adapter ha uno stato legato a un singolo stream: tiene traccia dei messaggi e delle tool call aperti. Creane un'istanza nuova per ogni richiesta e non condividerne mai una fra stream concorrenti.

### Eventi di protocollo, e dove nascono i byte

Nota che cosa l'adapter *non* fa: non produce righe `data: ...`. Il protocollo decide la forma di ciascun evento; il trasporto decide come quell'evento diventa byte. Per i Server-Sent Events, è il bordo HTTP a incorniciare lo stream con `SSEEncoder`:

```php
use NeuronAI\Workflow\Streaming\SSEEncoder;

$lines = SSEEncoder::encode($stream);

foreach ($lines as $line) {
    echo $line; // data: {"type":"TEXT_MESSAGE_CONTENT",...}\n\n
    flush();
}

$state = $lines->getReturn(); // the final AgentState, still reachable
```

`encode()` avvolge il generatore e ne inoltra il valore di ritorno, così lo stato finale sopravvive all'incorniciatura. `SSEEncoder::frame($event)` incornicia un singolo evento quando ti serve quello.

La separazione esiste perché SSE è solo una delle destinazioni. Un websocket, uno stream Redis o un canale di broadcast vogliono l'*evento*, non una riga incorniciata, e tenere separate le due responsabilità è ciò che permette allo stesso adapter di alimentarli tutti — i canali alla fine di questa sezione dipendono da questo.

### Un endpoint AG-UI completo

```php
use NeuronAI\Agent\Adapters\AGUIAdapter;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Workflow\Streaming\SSEEncoder;

$input = json_decode(file_get_contents('php://input'), true);

$messages = $input['messages'];
$last = $messages === [] ? null : $messages[array_key_last($messages)];

if (($last['role'] ?? null) !== 'user') {
    http_response_code(400);
    exit('A new turn must end with a user message.');
}

$adapter = new AGUIAdapter(
    threadId: $input['threadId'],
    runId: $input['runId'] ?? null,
    messages: $messages,
    state: $input['state'] ?? [],
);

foreach ($adapter->getHeaders() as $name => $value) {
    header("{$name}: {$value}");
}

$stream = MyAgent::make(threadId: $input['threadId'])
    ->setStreamAdapter($adapter)
    ->stream(new UserMessage((string) $last['content']));

foreach (SSEEncoder::encode($stream) as $line) {
    echo $line;
    flush();
}
```

Cinque cose da notare:

**I client AG-UI inviano in POST un payload `RunAgentInput`.** Non aprono semplicemente una connessione. Porta `threadId`, `runId`, la cronologia dei messaggi, i tool che il client può eseguire e lo stato condiviso.

**Il thread è la conversazione, da entrambi i lati.** L'adapter richiede `threadId` e lo rimanda in `RUN_STARTED` e `RUN_FINISHED`; l'agent riceve lo stesso valore tramite `make(threadId:)`, e in v4 quel thread *è* l'identità della run dell'agent — la chiave con cui una continuazione successiva trova una run in pausa. `runId` è l'identificativo per richiesta del client: passalo e l'adapter lo rimanda indietro; omettilo e l'adapter ne inventa uno, il che va bene per i test ed è sbagliato per un client reale che si aspetta di correlare lo stream con la run che ha richiesto.

**All'agent va solo l'ultimo messaggio dell'utente.** La copia della cronologia del client alimenta lo snapshot `messages` dell'adapter; non viene riproposta al modello. La cronologia della conversazione dell'agent per quel thread è la fonte di verità — il che significa che questo endpoint ha bisogno di una cronologia persistente (Capitolo 4) per ricordare qualcosa fra una richiesta e l'altra. Con la cronologia in memoria predefinita, ogni richiesta è una conversazione nuova.

**Una richiesta che non termina con un messaggio dell'utente non è un nuovo turno.** Un messaggio di tool in coda o un array `resume` è il client che *prosegue* una run in pausa — consegnando i risultati di tool del frontend o una decisione di approvazione. Quello passa per `submitInputs()` con il traduttore di input del protocollo, non per `stream()`; il Capitolo 21 descrive le forme delle richieste e il Capitolo 22 costruisce l'endpoint che risponde alle approvazioni. Il 400 qui sopra c'è perché una continuazione non venga mai scambiata silenziosamente per una domanda nuova.

**`getHeaders()` ti dà gli header SSE, e `flush()` va dopo ogni riga.** L'avvertenza della Sezione 7.3, e i documenti la ripetono qui per una buona ragione.

Nel codice reale, ricorda che `json_decode()` restituisce `null` su un corpo malformato; valida il payload prima di fidarti di una qualunque delle sue chiavi.

### La mappatura degli eventi

| Output NeuronAI | Eventi AG-UI |
|---|---|
| Ciclo di vita della run | `RUN_STARTED`, `RUN_FINISHED` |
| `TextChunk` | `TEXT_MESSAGE_START`, `TEXT_MESSAGE_CONTENT`, `TEXT_MESSAGE_END` |
| `ReasoningChunk` | `REASONING_START`, `REASONING_MESSAGE_START`, `REASONING_MESSAGE_CONTENT`, `REASONING_MESSAGE_END`, `REASONING_END` |
| `ToolCallChunk` + `ToolResultChunk` | `TOOL_CALL_START`, `TOOL_CALL_ARGS`, `TOOL_CALL_END`, `TOOL_CALL_RESULT` |
| Eventi di avanzamento del workflow | `STEP_STARTED`, `STEP_FINISHED`, `ACTIVITY_SNAPSHOT`, `CUSTOM` |
| Run in pausa per approvazione | `STATE_SNAPSHOT`, `MESSAGES_SNAPSHOT`, poi `RUN_FINISHED` con un esito `interrupt` |
| Run fallita | `RUN_ERROR` |

Una conseguenza della riga dei tool è facile da non vedere: l'adapter bufferizza una chiamata lato server e pubblica tutti e quattro gli eventi `TOOL_CALL_*` insieme, una volta che il risultato esiste. Un client AG-UI viene a sapere di un tool quando è finito, non quando inizia — quindi per un tool lento la riga "Checking the refund policy…" della Sezione 7.4 deve venire da un'altra parte, per esempio da un evento di avanzamento.

L'altra è la run in pausa. Uno stream sospeso non termina come uno completato: `RUN_FINISHED` porta `outcome: {type: "interrupt"}` con un interrupt `confirmation` per ogni tool in attesa di approvazione, indicizzato per ID della tool call. Un client che tratta ogni `RUN_FINISHED` come "la risposta è completa" sbaglierà. Il Capitolo 15 tratta l'approvazione in sé; il Capitolo 22 risponde a questi interrupt via HTTP.

Gli errori arrivano sulla rete senza il loro messaggio. `RUN_ERROR` (e la parte `error` di Vercel) portano un testo neutro, mai `$exception->getMessage()`, così un dettaglio dello stack non può trapelare verso un browser. Fai override del metodo protetto `errorMessage()` dell'adapter se i tuoi client devono saperne di più.

### Che cosa copre l'adapter, e la lacuna che resta

**I tool definiti dal frontend sono supportati.** I tool che un client elenca in `RunAgentInput` — eseguiti nel browser, non sul tuo server — possono essere collegati all'agent come tool differiti. Quando il modello ne chiama uno, la run si sospende, l'adapter pubblica la chiamata, il client la esegue e rimanda il risultato nella richiesta successiva, e la run prosegue. Quella richiesta è una continuazione, non un nuovo turno, e il Capitolo 21 mostra come distinguere le due.

**Lo stato condiviso viene rimandato indietro, non sincronizzato.** L'adapter porta lo `state` e i `messages` inviati dal client e li restituisce come `STATE_SNAPSHOT` e `MESSAGES_SNAPSHOT` quando una run va in pausa, così il quadro del client resta completo. Non emette mai `STATE_DELTA`, e nulla nell'agent scrive nello stato AG-UI. Se il progetto del tuo frontend dipende dal fatto che l'agent modifichi lo stato condiviso in tempo reale, quella è la lacuna.

Se stai valutando CopilotKit o un frontend AG-UI simile, conosci questo confine prima di impegnarti in un progetto che ne dipende.

### Adapter personalizzati

```php
namespace NeuronAI\Workflow\Streaming\Adapter;

interface StreamAdapterInterface
{
    public function reset(): void;
    public function start(): iterable;
    public function transform(object $chunk): iterable;
    public function end(): iterable;
    public function interrupt(InterruptRequest $request): iterable;
    public function error(Throwable $error): iterable;
}
```

Ogni iterable produce oggetti `ProtocolEvent`. `transform()` fa il lavoro: un oggetto nativo in ingresso, zero o più eventi in uscita. `start()` apre il protocollo. Esattamente un terminale chiude ogni segmento, ed è l'agent a sceglierlo in base all'esito, mai il tuo codice: `end()` al completamento, `interrupt()` quando la run va in pausa — così il client sa che cosa sta aspettando — ed `error()` in caso di fallimento. `reset()` viene chiamato prima di ogni segmento, così una sola istanza può servire una run in pausa e la sua continuazione nello stesso processo. Restituisci un iterable vuoto da qualunque metodo in cui il tuo protocollo non ha niente da dire.

Uno piccolo, per un frontend fatto in casa che vuole testo e avanzamento dei tool e nient'altro:

```php
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\Stream\Chunks\ToolCallChunk;
use NeuronAI\Workflow\Interrupt\InterruptRequest;
use NeuronAI\Workflow\Streaming\Adapter\StreamAdapterInterface;
use NeuronAI\Workflow\Streaming\ProtocolEvent;

final class ProgressAdapter implements StreamAdapterInterface
{
    public function reset(): void
    {
    }

    public function start(): iterable
    {
        return [];
    }

    public function transform(object $chunk): iterable
    {
        if ($chunk instanceof TextChunk) {
            yield new ProtocolEvent('delta', ['text' => $chunk->content]);
        }

        if ($chunk instanceof ToolCallChunk) {
            yield new ProtocolEvent('progress', ['tool' => $chunk->tool->getName()]);
        }
    }

    public function end(): iterable
    {
        yield new ProtocolEvent('done');
    }

    public function interrupt(InterruptRequest $request): iterable
    {
        yield new ProtocolEvent('paused', ['request' => $request->jsonSerialize()]);
    }

    public function error(Throwable $error): iterable
    {
        yield new ProtocolEvent('error', ['message' => 'Something went wrong.']);
    }
}
```

Lo stesso istinto da lista di permessi della Sezione 7.4, imposto al confine del protocollo: i risultati dei tool non lasciano mai il server perché l'adapter non ha un ramo per loro. Gli header HTTP non fanno parte dell'interfaccia; se il tuo protocollo ne ha bisogno, dichiara tu un `getHeaders()` sull'adapter, come fanno quelli integrati.

Prima di scriverne uno tuo, verifica se `AgentChunkAdapter` va già bene. È il vocabolario nativo di NeuronAI: un evento per chunk, con il nome del suo tipo (`text`, `reasoning`, `tool-call`, `tool-result`, …), e il `toArray()` del chunk come payload. Quando il consumatore è il tuo frontend e non parla alcun protocollo standard, di solito è tutto ciò che ti serve.

### Il caso d'uso da evidenziare

Tutto ciò che abbiamo visto finora presuppone che il codice che itera il generatore sia anche quello che parla con il browser — un controller che tiene aperta la connessione HTTP. Spesso non è così.

Una run lunga di un agent appartiene a un queue worker (l'aritmetica della latenza della Sezione 1.4, il vincolo `pcntl` della Sezione 5.13), e un queue worker non ha alcuna connessione HTTP con l'utente. Il suo output verrebbe semplicemente buttato via. I **canali** risolvono esattamente questo. L'adapter decide la forma dell'output; un canale decide dove va:

```php
use NeuronAI\Agent\Adapters\VercelAIAdapter;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Workflow\Streaming\Channel\PusherChannel;

// Inside a queued job: the HTTP request returned long ago.
$state = MyAgent::make(threadId: $threadId)
    ->setStreamAdapter(new VercelAIAdapter())
    ->setChannel(new PusherChannel(
        client: $pusher,
        channel: "private-chat.{$threadId}",
    ))
    ->stream(new UserMessage($message));
```

Con un adapter *e* un canale collegati, `stream()` consuma da solo la pipeline, consegna ogni evento di protocollo attraverso il canale nel momento in cui avviene, e restituisce l'`AgentState` finale — il secondo ramo del tipo di ritorno della Sezione 7.2. Nessun ciclo nel tuo codice.

Il framework include tre canali sotto `NeuronAI\Workflow\Streaming\Channel`: `PusherChannel` (prende un client configurato dal pacchetto opzionale `pusher/pusher-php-server`, e funziona con server compatibili con Pusher come Reverb e Soketi), `RedisChannel` per Redis Pub/Sub, e `CallbackChannel`, che avvolge una closure per qualunque altra cosa — un broadcast di Laravel, un log, un test. Un canale ha bisogno di un adapter per avere qualcosa da inviare; collega `AgentChunkAdapter` quando il browser non parla alcun protocollo di interfaccia.

Due proprietà attorno a cui progettare. Un guasto del canale non fa mai fallire la run: l'agent prosegue e segnala l'errore di trasporto come evento. E l'output in streaming è effimero — nulla di ciò che viene prodotto è salvato o riproposto, quindi un browser che si riconnette a metà run ha perso ciò che ha perso. La cronologia della conversazione è la fonte di verità con cui l'interfaccia si riallinea; non far mai dipendere la correttezza dal fatto che un client riceva un elemento dello stream.

Il Capitolo 21 lo costruisce in Laravel.

### Punti chiave

- `setStreamAdapter()` trasforma lo stream in `ProtocolEvent` per AG-UI, l'AI SDK di Vercel o il vocabolario proprio di NeuronAI; il codice del tuo agent resta invariato.
- Gli adapter decidono la forma, non i byte: `SSEEncoder` incornicia gli eventi al bordo HTTP e mantiene raggiungibile lo stato finale.
- I client AG-UI inviano un payload in POST: il thread è l'identità dell'agent, rimanda indietro `runId`, e invia solo il nuovo messaggio dell'utente.
- Una run in pausa termina con un esito `interrupt`, non con una conclusione normale; tool del frontend e approvazioni tornano come continuazioni.
- Un canale consegna gli stessi eventi quando nessuno tiene lo stream — il modo in cui un queue worker fa streaming verso un browser.

## Esercizi del capitolo

1. **Misuralo.** Converti un agent del Capitolo 5 da `chat()` a `stream()`. Misura il tempo al primo token in entrambi i modi e annota entrambi i numeri. Se il divario è piccolo, chiediti perché: un modello locale veloce su una risposta breve non ha davvero bisogno di streaming, e saperlo è utile quanto la funzionalità stessa.

2. **Mostra il lavoro.** Aggiungi la visualizzazione dell'avanzamento dei tool con una lista di permessi di etichette e un fallback sicuro. Poi aggiungi un nuovo tool senza aggiungerne l'etichetta e conferma che degrada al messaggio generico invece di far trapelare il suo nome interno.

3. **Scegli un adapter.** Abbozza quale adapter useresti per il tuo stack di frontend e decidi se la lacuna di AG-UI sullo stato condiviso ti riguarderebbe. Poi decidi chi tiene lo stream: la richiesta HTTP, o un queue worker con un canale. Se non ne sei sicuro, quella è la risposta da scoprire prima di costruire, non dopo.
