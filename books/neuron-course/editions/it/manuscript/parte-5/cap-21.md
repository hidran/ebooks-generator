# Capitolo 21 — Streaming verso il frontend

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

I listati Laravel qui sotto vivono dentro un'applicazione, ma le parti che non ne hanno bisogno sono eseguibili in [`chapters/Ch21`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch21) nel repository di accompagnamento: `sse-frames.php` stampa i frame esatti che invia l'endpoint della Sezione 21.1, `channel.php` stampa le buste che un canale push pubblica nella Sezione 21.5, e `disconnect.php` riproduce il comportamento in caso di disconnessione della Sezione 21.6. Nessuno di essi ha bisogno di un modello.
:::

## 21.1 Server-Sent Events in Laravel

### Perché SSE invece dei WebSocket

Per le risposte di un agent il traffico è unidirezionale: il server manda, il browser riceve. SSE ti dà questo su HTTP ordinario, con la riconnessione automatica integrata nel browser e nessuna infrastruttura aggiuntiva.

I WebSocket sono la scelta giusta quando anche il browser deve spingere — cosa che per un'interfaccia di chat non serve, perché il messaggio successivo è una nuova richiesta.

### Il controller

```php
<?php

declare(strict_types=1);

namespace App\Http\Controllers;

use App\Neuron\Agents\SupportAgent;
use Generator;
use Illuminate\Http\Request;
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Workflow\Streaming\ProtocolEvent;
use NeuronAI\Workflow\Streaming\SSEEncoder;
use Symfony\Component\HttpFoundation\StreamedResponse;

class ChatStreamController extends Controller
{
    public function __construct(
        private readonly SupportAgent $agent,
    ) {}

    public function __invoke(Request $request): StreamedResponse
    {
        $validated = $request->validate([
            'message' => ['required', 'string', 'max:4000'],
        ]);

        return response()->stream(function () use ($validated) {
            $stream = $this->agent->stream(new UserMessage($validated['message']));

            // No adapter or channel attached: stream() returns a Generator of native chunks.
            \assert($stream instanceof Generator);

            foreach ($stream as $chunk) {
                if (! $chunk instanceof TextChunk) {
                    continue;   // tool calls and results stay on the server (Section 7.4)
                }

                echo SSEEncoder::frame(new ProtocolEvent('text', ['content' => $chunk->content]));

                if (\ob_get_level() > 0) {
                    \ob_flush();
                }
                \flush();
            }

            echo "event: done\ndata: {}\n\n";
            \flush();
        }, 200, [
            'Content-Type'      => 'text/event-stream',
            'Cache-Control'     => 'no-cache, no-transform',
            'X-Accel-Buffering' => 'no',
            'Connection'        => 'keep-alive',
        ]);
    }
}
```

### Che cosa fa il ciclo

`stream()` è esso stesso il generator — iteralo direttamente. Senza stream adapter e senza canale agganciati produce i chunk object nativi di NeuronAI, e `TextChunk` è l'unico tipo che questo endpoint lascia passare. Tutto il resto — le tool call con i loro argomenti, i risultati dei tool — viene scartato sul server, che è la regola della Sezione 7.4 applicata al confine HTTP.

`SSEEncoder::frame()` è la formattazione SSE del framework, e l'unico punto in cui vengono prodotti byte. Un `ProtocolEvent` è un tipo più un payload serializzabile in JSON; l'encoder lo scrive come una sola riga `data:`, e sostituisce l'UTF-8 non valido invece di far fallire lo stream. La Sezione 21.4 lascia che sia un adapter a costruire gli eventi per te; qui, costruirne uno a mano mantiene esplicita l'allowlist.

L'evento `done` dopo il ciclo non è una decorazione. Quando una risposta SSE finisce, `EventSource` la tratta come una connessione caduta e programma una riconnessione — che, per questo endpoint, farebbe di nuovo la domanda. L'evento esplicito permette alla pagina di distinguere una risposta conclusa da un fallimento e di chiudere prima che succeda.

### I quattro header, ciascuno con un compito

**`Content-Type: text/event-stream`** — dice al browser che questo è SSE.

**`Cache-Control: no-cache, no-transform`** — `no-transform` conta: alcuni proxy comprimono o riscrivono le risposte, cosa che rompe i confini dei frame.

**`X-Accel-Buffering: no`** — specifico di nginx, e quello che ti salva una giornata. Senza, nginx bufferizza la risposta e la consegna tutta in una volta, momento in cui hai la complessità dello streaming senza nessuno dei suoi benefici.

**`Connection: keep-alive`** — tieni aperta la connessione.

### Il formato dei frame SSE

```
data: {"type":"text","content":"Hello"}\n\n
```

Due a capo terminano un frame. Sbagliane uno e il browser aspetta per sempre un frame che non si completa mai — un fallimento che sembra "lo streaming non funziona" ed è un carattere.

### Il frontend

```javascript
const source = new EventSource('/chat/stream?message=' + encodeURIComponent(text));

source.onmessage = (e) => {
    const chunk = JSON.parse(e.data);

    if (chunk.type === 'text') {
        output.textContent += chunk.content;
    }
};

source.addEventListener('done', () => source.close());

source.onerror = () => source.close();
```

**`EventSource` fa solo GET.** Per un body POST o usi `fetch()` con un reader di `ReadableStream`, o accetti il messaggio come parametro di query — cosa che limita la lunghezza del messaggio e mette contenuto dell'utente nei log di accesso. Per qualunque cosa reale, usa `fetch`.

### Punti chiave

- SSE si adatta all'output di un agent: unidirezionale, HTTP puro, riconnessione automatica.
- Itera direttamente `stream()`; inoltra solo il contenuto dei `TextChunk`, in frame costruiti con `SSEEncoder::frame()`.
- Invia un evento `done` esplicito, altrimenti `EventSource` si riconnette e fa di nuovo la domanda.
- Quattro header; `X-Accel-Buffering: no` è quello che ti salva una giornata.
- I frame finiscono con due a capo.
- `EventSource` fa solo GET — usa `fetch` con un reader di stream per il POST.

## 21.2 Il problema del buffering

### Il sintomo

Hai implementato lo streaming correttamente. Funziona da CLI (Sezione 7.3). Nel browser, non compare nulla per dodici secondi e poi l'intera risposta arriva tutta insieme.

Qualcosa fra il tuo `echo` e il browser sta trattenendo i byte.

### I quattro strati

**Strato 1 — Output buffering di PHP.**

```ini
; php.ini
output_buffering = Off
implicit_flush = On
```

Oppure dentro la callback dello stream:

```php
while (\ob_get_level() > 0) {
    \ob_end_flush();
}
```

Laravel può aprire buffer nei middleware; il ciclo chiude qualunque cosa esista invece di supporne uno solo.

**Strato 2 — PHP-FPM e il web server.**

nginx bufferizza le risposte FastCGI per default:

```nginx
location ~ \.php$ {
    fastcgi_pass   unix:/var/run/php/php8.5-fpm.sock;
    fastcgi_buffering off;
    fastcgi_read_timeout 300s;
    # ...
}
```

`fastcgi_buffering off` per l'intera location, oppure l'header `X-Accel-Buffering: no` per singola risposta. L'header è meglio — limita la modifica agli endpoint che ne hanno bisogno, e il resto del tuo sito mantiene il beneficio prestazionale del buffering.

Conta anche `fastcgi_read_timeout`: i 60 secondi di default taglieranno a metà lo stream di un'esecuzione lunga.

**Strato 3 — Reverse proxy.**

```nginx
location /chat/stream {
    proxy_pass http://app;
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 300s;
    proxy_set_header Connection '';
    proxy_http_version 1.1;
}
```

`proxy_http_version 1.1` più un header `Connection` vuoto tiene viva la connessione verso l'upstream.

**Strato 4 — CDN o WAF.**

Cloudflare, Fastly e simili possono bufferizzare. Cloudflare rispetta `text/event-stream` nella maggior parte delle configurazioni, ma verifica invece di darlo per scontato. Alcune regole WAF ispezionano l'intero body prima di inoltrarlo, che è buffering sotto un altro nome.

### La procedura diagnostica

Fai una bisezione dall'interno verso l'esterno. Questo trasforma un pomeriggio frustrante in cinque minuti:

```bash
# 1. PHP alone. Does it stream?
php -r 'for($i=0;$i<5;$i++){echo "chunk $i\n";flush();sleep(1);}'

# 2. Through PHP-FPM and the web server, bypassing any proxy
curl -N http://127.0.0.1:8080/chat/stream

# 3. Through the full public stack
curl -N https://app.example.com/chat/stream
```

`curl -N` disabilita il buffering di curl stesso. Il primo passo che non riesce a fare streaming è il tuo colpevole — e hai ristretto quattro strati a uno senza toccare un file di configurazione.

### L'avvertimento del framework stesso

La guida allo streaming del framework stesso lo dice direttamente: manda gli header dell'adapter, costruisci il frame di ogni evento con `SSEEncoder` e fai flush dopo ogni riga, o lo stream può restare incastrato nei buffer di output di PHP o nei proxy. Gli adapter di UI integrati mettono perfino `X-Accel-Buffering: no` nel loro `getHeaders()`.

Ne avvertono perché ci sbattono tutti.

### Punti chiave

- Quattro strati di buffering: PHP, FPM/web server, proxy, CDN.
- Preferisci l'header `X-Accel-Buffering` a un `fastcgi_buffering off` globale.
- Alza i timeout di lettura — i 60 s di default tagliano le esecuzioni lunghe.
- Fai la bisezione con `curl -N` dall'interno verso l'esterno.

## 21.3 Streaming con Livewire

### Il componente

```php
<?php

declare(strict_types=1);

namespace App\Livewire;

use App\Neuron\Agents\SupportAgent;
use Generator;
use Livewire\Component;
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\Stream\Chunks\ToolCallChunk;
use NeuronAI\Chat\Messages\UserMessage;

class Chat extends Component
{
    public string $input = '';
    public string $answer = '';
    public ?string $activity = null;
    public array $history = [];

    public function send(SupportAgent $agent): void
    {
        $question = \trim($this->input);

        if ($question === '') {
            return;
        }

        $this->history[] = ['role' => 'user', 'content' => $question];
        $this->input     = '';
        $this->answer    = '';

        $stream = $agent->stream(new UserMessage($question));
        \assert($stream instanceof Generator);

        foreach ($stream as $chunk) {
            if ($chunk instanceof ToolCallChunk) {
                $this->activity = $this->label($chunk->tool->getName());
                $this->stream(to: 'activity', content: $this->activity, replace: true);
                continue;
            }

            if (! $chunk instanceof TextChunk) {
                continue;   // tool results, reasoning: never rendered
            }

            $this->answer .= $chunk->content;
            $this->stream(to: 'answer', content: $chunk->content);
        }

        $this->activity  = null;
        $this->history[] = ['role' => 'assistant', 'content' => $this->answer];
    }

    private function label(string $tool): string
    {
        return [
            'search_orders'     => 'Looking through your orders',
            'get_order_status'  => 'Checking that order',
            'request_refund'    => 'Preparing a refund request',
        ][$tool] ?? 'Working on it';
    }

    public function render()
    {
        return view('livewire.chat');
    }
}
```

### La vista

```blade
<div class="space-y-4">
    @foreach ($history as $message)
        <div @class(['text-right' => $message['role'] === 'user'])>
            {{ $message['content'] }}
        </div>
    @endforeach

    <div wire:stream="activity" class="text-sm text-gray-500 italic">
        {{ $activity }}
    </div>

    <div wire:stream="answer" class="whitespace-pre-wrap">
        {{ $answer }}
    </div>

    <form wire:submit="send" class="flex gap-2">
        <input wire:model="input" class="flex-1 border rounded px-3 py-2" autofocus>
        <button type="submit" class="px-4 py-2 bg-black text-white rounded">Send</button>
    </form>
</div>
```

### Perché per la maggior parte dei team Laravel è il punto ideale

`$this->stream(to: 'answer', content: $chunk->content)` spinge verso `wire:stream="answer"` nella vista. Livewire gestisce il trasporto SSE, la riconnessione e gli aggiornamenti del DOM.

Niente `EventSource`, niente reader di `fetch`, nessun parsing manuale dei frame. Per un team che non vuole mantenere un frontend JavaScript, sono grosso modo trenta righe di PHP per una chat con streaming completa.

**Nota `replace: true` per la riga di attività** e la sua assenza per la risposta. L'attività è uno stato che sovrascrive; la risposta si accumula. Invertirli è il bug di streaming più comune in Livewire.

### L'allowlist delle etichette, di nuovo

`$this->label()` mappa i nomi dei tool su testo rivolto all'utente, con `?? 'Working on it'` come fallback. E il ciclo renderizza esattamente due tipi di chunk: un `ToolCallChunk` diventa un'etichetta, un `TextChunk` diventa testo della risposta, e tutto il resto — risultati dei tool, ragionamento — viene scartato dal controllo `instanceof TextChunk` anziché da un elenco di cose da escludere.

La regola della Sezione 7.4: non mostrare mai nomi o risultati grezzi dei tool. Un tool nuovo aggiunto il mese prossimo degrada al messaggio generico invece di far trapelare `internal_pricing_lookup` a un cliente. Le allowlist falliscono in sicurezza — lo stesso argomento di `only()` contro `exclude()` nella Sezione 5.8.

### La limitazione da conoscere

L'agent gira dentro una richiesta Livewire, quindi si applicano il `max_execution_time` di PHP-FPM e i timeout del web server. Va bene per una risposta di chat da 15 secondi. Non va bene per un workflow multi-agente da due minuti — quello appartiene a una coda con un trasporto diverso, che è la Sezione 21.5.

### Punti chiave

- `$this->stream(to:, content:)` più `wire:stream` — Livewire gestisce il trasporto.
- `replace: true` per lo stato, omesso per il testo che si accumula.
- Mappa i nomi dei tool attraverso un'allowlist con un fallback sicuro.
- Limitato dai timeout delle richieste web; le esecuzioni lunghe hanno bisogno di una coda.

## 21.4 Frontend SPA e adapter di protocollo

### L'endpoint

```php
<?php

declare(strict_types=1);

namespace App\Http\Controllers;

use App\Neuron\SupportAgentFactory;
use Generator;
use Illuminate\Http\Request;
use NeuronAI\Agent\Adapters\AGUIAdapter;
use NeuronAI\Agent\AgentState;
use NeuronAI\Agent\Frontend\AGUIInputTranslator;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Workflow\Streaming\ProtocolEvent;
use NeuronAI\Workflow\Streaming\SSEEncoder;
use Symfony\Component\HttpFoundation\StreamedResponse;

class AgentUiController extends Controller
{
    public function __invoke(Request $request, SupportAgentFactory $agents): StreamedResponse
    {
        $input = $request->validate([
            'threadId'           => ['required', 'string'],
            'runId'              => ['nullable', 'string'],
            'messages'           => ['required', 'array', 'min:1'],
            'messages.*.id'      => ['required', 'string'],
            'messages.*.role'    => ['required', 'string'],
            'messages.*.content' => ['nullable', 'string'],
            'state'              => ['nullable', 'array'],
            'resume'             => ['nullable', 'array'],
        ]);

        // The client names the thread; the server decides whether this user may use it.
        $conversation = $request->user()->conversations()
            ->where('thread_id', $input['threadId'])
            ->firstOrFail();

        $last = \array_last($input['messages']);

        $adapter = new AGUIAdapter(
            threadId: $conversation->thread_id,
            runId: $input['runId'] ?? null,
            messages: $input['messages'],
            state: $input['state'] ?? [],
        );

        $agent = $agents->forThread($conversation->thread_id)->setStreamAdapter($adapter);

        // Answers to a paused run (approvals, browser tool results) continue it;
        // a trailing user message starts a new turn. Nothing else is accepted.
        $continuation = ($input['resume'] ?? []) !== [] || $last['role'] === 'tool';
        abort_unless($continuation || $last['role'] === 'user', 422, 'Nothing to answer and no new message.');

        /** @var Generator<int, ProtocolEvent, mixed, AgentState> $stream */
        $stream = $continuation
            ? $agent->submitInputs($request->all(), new AGUIInputTranslator())->events()
            : $agent->stream(new UserMessage((string) $last['content']));

        return response()->stream(function () use ($stream) {
            foreach (SSEEncoder::encode($stream) as $line) {
                echo $line;
                \flush();
            }
        }, 200, $adapter->getHeaders());
    }
}
```

### Sei cose da segnalare

**L'adapter dà la forma, l'encoder fa i frame.** `setStreamAdapter()` fa sì che `stream()` produca oggetti `ProtocolEvent` — `RUN_STARTED`, `TEXT_MESSAGE_CONTENT` e il resto — invece dei chunk nativi. `SSEEncoder::encode()` trasforma ciascuno in una riga `data:` e inoltra il valore di ritorno del generator, così l'`AgentState` finale è ancora lì se ti serve. L'adapter non sa nulla dei byte, ed è questo che permette allo stesso adapter di alimentare un canale di broadcast nella Sezione 21.5.

**`getHeaders()` fornisce gli header del protocollo — compreso `X-Accel-Buffering: no`.** Gli adapter integrati ora portano con sé la correzione per nginx della Sezione 21.2, quindi non c'è nulla da fondere.

**All'agent va solo l'ultimo messaggio dell'utente.** Un client AG-UI invia l'intera conversazione a ogni turno. L'agent ha già quella conversazione nella sua cronologia della conversazione durevole, indicizzata per thread — passargli la copia del client significa salvare due volte ogni messaggio precedente. I `messages` del client vanno invece all'adapter, che li usa per mantenere completo lo snapshot dei messaggi del protocollo.

**Il thread è l'identità dell'agent — autorizzalo.** Il `threadId` di AG-UI diventa il thread dell'agent, e il thread *è* il workflow ID dell'agent: la chiave sotto cui sono archiviate la sua cronologia e ogni run sospesa. Questo lo rende esattamente il valore che la Sezione 18.2 diceva di non prendere mai dall'input dell'utente. La ricerca tramite `$request->user()->conversations()` è ciò che trasforma una stringa fornita dal client in un thread posseduto da questo utente. Rimanda indietro anche `runId`: è l'identificatore per richiesta del client, e senza di esso il client non può correlare lo stream con la run che ha chiesto.

**La forma della richiesta decide fra nuovo turno e continuazione.** Un messaggio utente in coda è un nuovo turno, e va a `stream()`. Un array `resume` — il client che risponde alle interruzioni — o un messaggio tool in coda è la continuazione di una run in pausa, e va a `submitInputs()` con il translator del protocollo, che la valida rispetto alla richiesta persistita prima che qualunque cosa venga eseguita e lancia `InputTranslationException` per tutto ciò che non corrisponde. Nota che la continuazione chiama `events()`, non `stream()`: `stream()` avvia sempre un nuovo turno. Una continuazione non valida deve essere una risposta di errore, mai un ripiego su un nuovo turno.

**Cambia l'adapter, tieni tutto il resto.** `VercelAIAdapter` al posto di `AGUIAdapter` e lo stesso agent serve un protocollo frontend diverso — con `VercelAIInputTranslator` per le sue continuazioni. L'argomento delle interfacce della Sezione 2.2, applicato sul lato dell'output.

### Quando la run va in pausa

Se un tool del turno richiede approvazione (Capitolo 22), lo stream non finisce come uno completato. Il terminale `interrupt()` dell'adapter sostituisce `end()`: su AG-UI, `RUN_FINISHED` porta `outcome: {type: "interrupt", interrupts: [...]}`, un'interruzione `confirmation` per ogni tool call in sospeso, con l'ID della tool call come suo `id`; su Vercel, una parte `tool-approval-request` per ogni chiamata.

Un frontend che tratta ogni `RUN_FINISHED` come "la risposta è completa" renderizzerà una run in pausa come una conclusa. Controlla `outcome.type` prima di chiudere il turno. Il client risponde con un array `resume` nella richiesta successiva, che l'endpoint qui sopra instrada verso `submitInputs()`. La Sezione 22.5 copre il lato dell'approvazione per i client che non parlano AG-UI.

### Che cosa copre l'adapter, e che cosa no

Dalla Sezione 7.5, perché un team che sceglie un frontend deve saperlo prima di impegnarsi:

**Snapshot alla pausa, non delta.** L'adapter emette `STATE_SNAPSHOT` e `MESSAGES_SNAPSHOT` prima di concludere una run interrotta, inizializzati a partire da `state` e `messages` che hai passato al suo costruttore. Non emette `STATE_DELTA`. Se il tuo progetto dipende da una sincronizzazione fine dello stato condiviso mentre l'agent gira, l'adapter non te la darà.

**I tool definiti dal frontend richiedono un passo in più.** I client AG-UI possono dichiarare tool in `RunAgentInput.tools` perché li esegua il browser. NeuronAI li supporta come tool differiti: la run si sospende quando il modello ne chiama uno, l'adapter pubblica la chiamata e il client rimanda il risultato come messaggio tool in coda — il ramo di continuazione qui sopra. Ciò che l'endpoint non fa ancora è agganciare quei tool all'agent. `AGUIInputTranslator::tools($payload)` li costruisce dalla richiesta; aggiungili nella factory, dopo aver respinto qualunque nome che oscuri uno dei tuoi tool lato server, e applica loro la tua approval policy come a qualunque altro tool.

Se stai valutando CopilotKit o un frontend AG-UI simile, verifica questi due punti rispetto al tuo progetto adesso, non dopo aver costruito il frontend.

### Eventi di avanzamento dai tuoi nodi

I chunk non sono l'unica cosa che uno stream può trasportare. Un nodo — nel tuo workflow, o in un nodo personalizzato di un agent — può fare `yield` di un evento di avanzamento portabile, e ogni adapter lo traduce nel vocabolario del proprio protocollo:

```php
use NeuronAI\Agent\Adapters\Events\ActivityStreamEvent;
use NeuronAI\Agent\Adapters\Events\StepStartedStreamEvent;

yield new StepStartedStreamEvent('checking-stock');

yield new ActivityStreamEvent(
    id: "stock-{$orderId}",
    type: 'stock-check',
    data: ['checked' => 3, 'total' => 5],
);
```

Su AG-UI questi diventano `STEP_STARTED` e `ACTIVITY_SNAPSHOT` — un'attività con lo stesso `id` sostituisce la precedente, che è esattamente la semantica da barra di avanzamento che vuoi. `CustomStreamEvent($name, $value)` diventa l'evento `CUSTOM` di AG-UI. Su Vercel tutti e tre viaggiano come parti `data-*` transitorie, che raggiungono la UI senza entrare nella cronologia dei messaggi.

Se i tuoi nodi producono già oggetti di dominio, mappali invece di riscrivere i nodi:

```php
$adapter->mapEvent(
    StockChecked::class,
    static fn (StockChecked $event): ?ActivityStreamEvent => new ActivityStreamEvent(
        id: "stock-{$event->orderId}",
        type: 'stock-check',
        data: ['checked' => $event->checked, 'total' => $event->total],
    ),
);
```

La corrispondenza è per classe esatta, e restituire `null` sopprime l'evento — il che rende `mapEvent()` il posto giusto per tenere un evento interno fuori dal filo. L'adapter resta l'unico proprietario del vocabolario del protocollo; i tuoi nodi non importano mai un tipo AG-UI.

Una regola per tutto questo: **gli eventi in streaming sono live ed effimeri.** Non vengono persistiti, e una run ripresa non li riproduce. Non far mai dipendere la correttezza dal fatto che il browser ne abbia ricevuto uno.

### Autenticazione

Una SPA manda un token; Sanctum o Passport lo gestiscono come al solito. La parte importante è che l'*agent* venga costruito per l'utente autenticato e per il thread autorizzato. Poiché il thread fa parte dell'identità dell'agent — va al costruttore, non a un setter — una factory si legge meglio di un binding del container:

```php
class SupportAgentFactory
{
    public function __construct(
        private readonly OrderRepository $orders,
        private readonly AuthManager $auth,
    ) {}

    public function forThread(string $threadId): SupportAgent
    {
        return new SupportAgent(
            orders: $this->orders,
            user: $this->auth->user(),
            threadId: $threadId,
        );
    }
}
```

```php
class SupportAgent extends Agent
{
    public function __construct(
        private readonly OrderRepository $orders,
        private readonly User $user,
        string $threadId,
    ) {
        parent::__construct(threadId: $threadId);
    }

    // provider(), tools(), chatHistory() as in Chapter 18
}
```

Visibilità dei tool, cronologia della conversazione e filtri RAG discendono tutti da questi due input. L'argomento della Sezione 18.1, ed è il motivo per cui il controller resta così breve.

### Punti chiave

- `setStreamAdapter()` fa sì che `stream()` produca `ProtocolEvent`; `SSEEncoder::encode()` ne fa i frame; `getHeaders()` include già `X-Accel-Buffering`.
- All'agent manda solo l'ultimo messaggio dell'utente; la cronologia del client inizializza l'adapter.
- Un array `resume` o un messaggio tool in coda è una continuazione: `submitInputs()` con il translator del protocollo, poi `events()`.
- Il `threadId` di AG-UI diventa il workflow ID dell'agent — risolvilo tramite l'utente, non fidarti mai del valore grezzo.
- Una run in pausa finisce con un esito di interruzione, non con una semplice conclusione; controlla prima di chiudere il turno.
- I nodi producono eventi di avanzamento portabili; `mapEvent()` traduce o sopprime i tuoi.

## 21.5 Streaming da una coda

Questa è la sezione in cui le Parti IV e V si incontrano.

### Il problema

La Sezione 16.4 ha stabilito che le esecuzioni lunghe appartengono a una coda. Ma un queue worker non ha alcuna connessione HTTP con l'utente — quindi come arriva l'avanzamento al browser?

La risposta è un **canale di streaming**. Tutto ciò che abbiamo visto finora è streaming *pull*: il codice che itera il generator è il codice che detiene la risposta. Un canale è la metà *push*. Agganciane uno a un workflow o a un agent, insieme a uno stream adapter, e la run consegna al canale ogni evento di protocollo man mano che viene prodotto — a Pusher, a Redis, a un websocket — mentre il worker si limita a chiamare `run()`.

### L'architettura

```
Browser → POST /workflows             → crea il record della run, restituisce { workflowId }
Browser → si iscrive a private-workflows.{workflowId}, attende l'iscrizione
Browser → POST /workflows/{id}/start  → invia il job
Worker  → esegue il workflow; il canale spinge ogni evento, in sequenza
Browser → riordina per sequenza, renderizza l'avanzamento, riconcilia in caso di buco
```

L'ordine delle prime tre righe conta. Pusher e Redis Pub/Sub non riproducono nulla: un evento pubblicato prima che il browser si iscrivesse è perso. Quindi il browser si iscrive per primo, e solo dopo chiede al server di partire.

### Il job

```php
<?php

declare(strict_types=1);

namespace App\Jobs;

use App\Models\WorkflowRun;
use App\Neuron\Workflows\ContentWorkflow;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use NeuronAI\Agent\Adapters\AgentChunkAdapter;
use NeuronAI\Laravel\Models\WorkflowStore;
use NeuronAI\Workflow\Persistence\EloquentPersistence;
use NeuronAI\Workflow\Streaming\Channel\PusherChannel;
use NeuronAI\Workflow\WorkflowState;
use Pusher\Pusher;

class RunContentWorkflow implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $timeout = 600;
    public int $tries = 1;   // agent runs are expensive — do not blind-retry

    public function __construct(
        public readonly WorkflowRun $run,
    ) {}

    public function handle(Pusher $pusher): void
    {
        $state = ContentWorkflow::make(
            workflowId: $this->run->workflow_id,
            state: new WorkflowState(['topic' => $this->run->topic]),
        )
            ->setPersistence(new EloquentPersistence(WorkflowStore::class))
            ->setStreamAdapter(new AgentChunkAdapter())
            ->setChannel(new PusherChannel(
                client: $pusher,
                channel: "private-workflows.{$this->run->workflow_id}",
            ))
            ->run();

        if ($state->isInterrupted()) {
            $this->run->update(['status' => 'awaiting_approval']);

            return;   // Chapter 22 records and routes the approval
        }

        $this->run->update([
            'status' => 'completed',
            'result' => $state->get('final'),
        ]);
    }
}
```

### Quattro cose che questo job fa diversamente da una richiesta web

**`run()`, non un ciclo.** Con un adapter e un canale agganciati, il workflow consuma il proprio stream e consegna ogni evento attraverso il canale nel momento in cui accade. `run()` restituisce lo stato finale quando il segmento si completa o va in pausa. Non c'è alcun generator da iterare e nulla da stampare.

**È ancora l'adapter a decidere la forma.** Un canale trasporta eventi di protocollo, mai oggetti nativi, quindi ha bisogno di un adapter. `AgentChunkAdapter` è il vocabolario proprio di NeuronAI per un consumatore che non parla alcun protocollo di UI: ogni chunk o evento di avanzamento diventa un evento che prende il nome dal suo tipo — `text`, `tool-call`, `activity`, `step-started` — con i campi del chunk stesso come payload. Se il browser esegue un client AG-UI o Vercel, aggancia invece quell'adapter; al canale non importa.

**Il canale riporta il ciclo di vita.** Dopo i frame terminali dell'adapter, il canale invia `stream.completed`, `stream.interrupted` o `stream.failed`, con il solo workflow ID — niente stato, niente dettagli dell'eccezione. Non servono eventi di broadcast tuoi come `WorkflowCompleted` o `WorkflowPaused`: il browser apprende l'esito dallo stream e recupera il risultato dalla tua applicazione, che è il record autorevole.

**La pausa è un valore di ritorno.** Una run interrotta ritorna normalmente con `isInterrupted()` a true — niente da catturare. Il Capitolo 22 prosegue da lì.

`AgentChunkAdapter` inoltra tutto ciò che riceve, compresi gli argomenti delle tool call e i risultati dei tool. Per una schermata di avanzamento mostrata alla persona che ha avviato la run di solito va bene; per qualunque cosa rivolta ai clienti, sopprimi ciò che non deve viaggiare con `mapEvent(ToolResultChunk::class, fn () => null)`, oppure aggancia l'adapter AG-UI e lascia decidere al frontend. La regola della Sezione 7.4 non smette di valere perché è cambiato il trasporto.

### Il client Pusher

`PusherChannel` accetta un client configurato dall'applicazione, dall'SDK ufficiale `pusher/pusher-php-server` — che è anche ciò che parla Laravel Reverb — così cifratura, firma, endpoint e timeout vengono configurati una volta sola, dove devono stare:

```php
// AppServiceProvider::register()
$this->app->singleton(Pusher::class, fn () => new Pusher(
    config('broadcasting.connections.reverb.key'),
    config('broadcasting.connections.reverb.secret'),
    config('broadcasting.connections.reverb.app_id'),
    config('broadcasting.connections.reverb.options', []) + ['timeout' => 5],
));
```

Imposta esplicitamente il `timeout` dell'SDK e usa la versione 7.2.4 o successiva; le release precedenti non lo passano alla richiesta HTTP.

Preferisci Redis? `new RedisChannel($redis, "workflows:{$id}")` pubblica le stesse buste su Redis Pub/Sub per un processo che detiene la connessione del browser. Preferisci il broadcasting di Laravel? `CallbackChannel` avvolge una closure per ogni metodo del ciclo di vita, così `onSend` può chiamare `Broadcast::private(...)->as($event->type)->with($event->data)->sendNow()`. **`sendNow()`, mai un broadcast in coda.** Un broadcast in coda mette in fila i tuoi aggiornamenti di avanzamento dietro al job che li sta producendo — su un solo worker, un deadlock al rallentatore — e con più worker li consegna fuori ordine.

### La busta, e perché il browser ha bisogno di una libreria

`PusherChannel` e `RedisChannel` non inviano eventi di protocollo nudi. Ogni messaggio è una busta:

```json
{"streamId":"81d4f00e881563538f272ca26aa7a8d4","sequence":3,"type":"text","data":{"messageId":"msg_1","content":"The first"}}
```

Dietro quei campi si nascondono tre problemi, e in produzione si presenteranno tutti e tre:

**Ordine.** Pusher garantisce l'ordine all'interno di un batch, non fra batch diversi. `sequence` numera ogni evento logico di un segmento, così il browser può rimetterli in ordine — compreso uno `stream.completed` che arriva prima del testo che lo precede.

**Dimensione.** Pusher limita un evento a 10 KB. Un risultato di tool lungo o un payload di attività voluminoso viene diviso in buste `stream.fragment` che condividono un unico numero di sequenza, e va riassemblato prima di poter essere interpretato.

**Buchi.** Una connessione caduta perde eventi per sempre. Il browser deve accorgersi di un numero di sequenza mancante e ricaricare dall'applicazione invece di renderizzare uno stream con un buco.

Non vuoi scriverlo a mano, e non devi. `@neuron-core/streaming` è la metà browser dello stesso contratto:

```javascript
import { subscribeToPusher } from '@neuron-core/streaming';

const channel = Echo.connector.pusher.subscribe(`private-workflows.${workflowId}`);

channel.bind('pusher:subscription_succeeded', () => {
    fetch(`/workflows/${workflowId}/start`, { method: 'POST', headers: csrfHeaders });
});

const subscription = subscribeToPusher(channel, {
    onEvent: ({ type, data }) => {
        if (type === 'activity') {
            renderProgress(data.id, data.data);
        } else if (type === 'stream.interrupted') {
            showMessage('Waiting for approval.');
        } else if (type === 'stream.completed') {
            loadResult(workflowId);
        }
    },
    onGap: () => loadResult(workflowId),   // reconcile from the server; never guess
});
```

Riordina, riassembla, scarta i duplicati e segnala i buchi; la tua callback vede solo eventi completi, in sequenza. Il riferimento al canale viene dal client Pusher che Echo ha già configurato, quindi l'autenticazione passa per le tue normali route di broadcasting.

### L'autorizzazione del canale

```php
// routes/channels.php
Broadcast::channel('workflows.{workflowId}', function ($user, string $workflowId) {
    return WorkflowRun::where('workflow_id', $workflowId)
        ->where('tenant_id', $user->tenant_id)
        ->exists();
});
```

Senza questo, chiunque indovini un workflow ID guarda il lavoro dell'agent di qualcun altro. I quattro punti di fuga della Sezione 18.3 hanno un quinto parente: il canale di broadcast. Per contenuti che devono restare riservati anche nei confronti del provider di broadcast, usa un canale `private-encrypted-*` con la master key di cifratura dell'SDK; il browser ha bisogno di `pusher-js/with-encryption`, e il consumatore del pacchetto non cambia.

### Che cosa compone

Questo singolo job è gran parte del libro che converge:

- Streaming dei workflow con `yield` ed eventi di avanzamento portabili (14.4, 21.4)
- Interruzione e persistenza (15.4)
- Persistenza Eloquent (18.4)
- Esecuzione asincrona (16.4)
- Adapter che spingono verso un trasporto esterno (7.5)
- `pcntl` disponibile, quindi i tool paralleli funzionano (5.13)
- Inspector registrato sul workflow (23.3)

Quest'ultimo è la misconfigurazione con più probabilità di morderti: nulla viene monitorato se non sottoscrivi il listener, e un worker è esattamente il posto dove nessuno si accorge che manca.

### Punti chiave

- Push, non pull: adapter più canale, e il worker chiama semplicemente `run()`.
- Prima iscriviti, poi avvia la run — Pusher e Redis non riproducono nulla.
- `PusherChannel` invia buste numerate in sequenza e frammentabili; `@neuron-core/streaming` riordina, riassembla e segnala i buchi.
- Il canale riporta completamento, pausa e fallimento; recupera i risultati dall'applicazione.
- Autorizza il canale per tenant; `$tries = 1` sui job degli agent; i ritentativi ciechi rispendono soldi.

## 21.6 Disconnessione e costo orfano

### Il problema che nessuno menziona

Un utente avvia un'esecuzione di 30 secondi. Al quarto secondo chiude la scheda.

Il browser non c'è più. **L'agent continua a girare.** Ogni chiamata al modello che resta viene fatturata. In un workflow multi-agente è una somma sostanziosa spesa per un output che nessuno leggerà mai.

A basso volume è invisibile. Su scala è una voce di bilancio.

### Rilevarlo in una risposta in streaming

```php
return response()->stream(function () use ($agent, $message) {
    $stream = $agent->stream(new UserMessage($message));
    \assert($stream instanceof Generator);

    foreach ($stream as $chunk) {
        if (\connection_aborted()) {
            \Log::info('Client disconnected — stopping agent run');

            try {
                $stream->throw(new ClientDisconnected());
            } catch (ClientDisconnected) {
                // the run is now settled as failed
            }
            break;
        }

        if ($chunk instanceof TextChunk) {
            echo SSEEncoder::frame(new ProtocolEvent('text', ['content' => $chunk->content]));
            \flush();
        }
    }
}, 200, $headers);
```

`connection_aborted()` richiede che tu abbia scritto sulla connessione — PHP rileva la pipe rotta solo su un tentativo di scrittura. Poiché stai facendo streaming, stai scrivendo, quindi funziona. Non funzionerebbe in un endpoint senza streaming.

### Perché `break` da solo non basta

`ClientDisconnected` è una normale classe di eccezione tua. Ciò che conta è lanciarla *dentro* il generator.

Una run di un agent è una run di workflow durevole. Mentre viene eseguita detiene un lease sul suo thread — dieci minuti per default per un agent — così che un secondo processo non possa avviare una run concorrente sulla stessa conversazione. Una conclusione pulita, una pausa o un fallimento catturato rilasciano il lease. Abbandonare semplicemente il generator non fa nulla di tutto ciò: la run resta marcata come in esecuzione finché il lease non scade.

Con la persistenza in memoria predefinita non te ne accorgi mai, perché il record muore con la richiesta. Dai all'agent una persistenza durevole — cosa che fa il Capitolo 22, perché le approvazioni ne hanno bisogno — e un `break` nudo significa che il *prossimo* messaggio dell'utente su quella conversazione viene rifiutato con `RunInFlightException` per un massimo di dieci minuti. `$stream->throw()` consegna l'eccezione nel punto in cui la run è sospesa; il workflow chiude la run come fallita e rilancia, e il messaggio successivo sostituisce normalmente la run fallita.

Il `disconnect.php` del repository di accompagnamento esegue le due versioni fianco a fianco: con il solo `break` il secondo messaggio viene rifiutato; con il `throw()` riceve risposta.

**Un'avvertenza onesta:** fermare il ciclo ferma la *tua* iterazione. Una chiamata al modello già in volo si completa e viene fatturata. Stai limitando il danno, non eliminandolo.

### Per i workflow in coda

Un browser disconnesso non ferma un worker, e non dovrebbe — l'utente potrebbe tornare, e il risultato vale la pena averlo. Ma ci sono casi in cui la cancellazione è giusta. Un worker che gira con un canale non ha alcun ciclo da cui uscire, quindi il controllo va dentro il workflow — nelle prime righe di ogni nodo che avvia uno step costoso:

```php
class ReviewNode extends Node
{
    public function __invoke(DraftReady $event, WorkflowState $state): DraftReviewed|StopEvent
    {
        if (Cache::has("workflow:{$state->getWorkflowId()}:cancelled")) {
            $state->set('cancelled', true);

            return new StopEvent();
        }

        // ... the review itself, as in Chapter 14
    }
}
```

```php
// A cancel endpoint
Cache::put("workflow:{$id}:cancelled", true, now()->addHour());
```

Cancellazione esplicita, non dedotta dalla disconnessione — e chiude la run in modo pulito, così il workflow ID torna libero e il canale riporta `stream.completed` come per qualunque altra conclusione.

### Guardie di budget

Il complemento, e la cosa che davvero mette un tetto all'esposizione:

```php
class BudgetMiddleware
{
    public function handle($request, Closure $next)
    {
        $spent = Cache::get("ai_spend:{$request->user()->id}:" . today()->toDateString(), 0);

        if ($spent > config('neuron.daily_user_budget')) {
            abort(429, 'Daily AI usage limit reached.');
        }

        return $next($request);
    }
}
```

Registra l'uso reale dai conteggi di token di ogni inferenza — la Sezione 23.1 sottoscrive un listener che fa esattamente questo. La Sezione 1.3 diceva di catturare l'uso fin dal primo prototipo; ecco a cosa serve catturarlo.

### Punti chiave

- Una scheda chiusa non ferma un agent — continui a pagare.
- `connection_aborted()` dentro il ciclo dello stream limita il danno.
- Lancia l'eccezione dentro il generator prima del `break`, altrimenti una run durevole tiene bloccato il suo thread finché il lease non scade.
- Il lavoro in coda va cancellato esplicitamente, fra uno step e l'altro, non per deduzione.
- I budget giornalieri per utente mettono un tetto all'esposizione; hanno bisogno dei conteggi di token che stai loggando da un pezzo.

## Laboratorio 15 — L'interfaccia di chat in streaming

**Copre:** SSE o Livewire, visualizzazione dell'attività dei tool, buffering, disconnessione.

### Obiettivo

Un'interfaccia di chat che renderizza la risposta token per token e mostra che cosa sta facendo l'agent mentre lo fa — con i nomi dei tool mappati su un linguaggio che un cliente può leggere.

### Requisiti

1. **Rendering token per token.** Scegli Livewire (Sezione 21.3) o SSE con `fetch` (Sezione 21.1). Livewire ha meno pezzi in movimento; SSE ti insegna di più sul trasporto.
2. **Una riga di attività dei tool** che sostituisce invece di accumulare, guidata da un'allowlist di etichette con un fallback sicuro.
3. **I risultati dei tool non raggiungono mai il browser.** Solo le etichette.
4. **La catena di buffering verificata** con `curl -N` in tutti e tre i punti della Sezione 21.2 — PHP da solo, attraverso il web server, attraverso l'intero stack pubblico. Annota quale strato, se ce n'è uno, ha avuto bisogno di configurazione.
5. **Gestione della disconnessione** con `connection_aborted()`, lanciando l'eccezione dentro lo stream prima di uscire dal ciclo.

### Criteri di accettazione

- Il primo token visibile arriva ben sotto il secondo su un modello locale. Misuralo; non darlo per scontato.
- Fare una domanda che innesca un tool mostra l'etichetta amichevole, poi la risposta.
- Aggiungere un nuovo tool senza aggiungerne l'etichetta mostra "Working on it", non il nome interno del tool. Testalo deliberatamente.
- Chiudere la scheda a metà risposta produce una riga di log e ferma il ciclo — e un nuovo messaggio sulla stessa conversazione, inviato subito dopo, riceve risposta invece di essere rifiutato.
- `curl -N` fa streaming attraverso l'intero stack, non solo in locale.

### La parte che le persone saltano

Il requisito quattro. È allettante dichiarare vittoria quando funziona su `artisan serve`, dove non c'è nginx né proxy. Il primo deploy è il punto in cui lo streaming si rompe, e la bisezione della Sezione 21.2 è la differenza fra cinque minuti e un pomeriggio.

Esegui i tre comandi `curl -N` contro il tuo vero ambiente di staging prima di dichiarare finito questo laboratorio.

### Andare oltre

Aggiungi un pulsante "stop" che interrompe la richiesta dal lato browser, e conferma che `connection_aborted()` scatti. Poi misura che cosa ha risparmiato: esegui lo stesso prompt fino alla fine, annota il conteggio dei token e confronta con un'esecuzione interrotta. Quel numero è l'argomento per costruire il pulsante.
