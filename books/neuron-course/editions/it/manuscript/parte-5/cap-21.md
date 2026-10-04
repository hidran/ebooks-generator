# Capitolo 21 — Streaming verso il frontend

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

I listati Laravel qui sotto vivono dentro un'applicazione, ma le parti che non ne hanno bisogno sono eseguibili in [`chapters/Ch21`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch21) nel repository di accompagnamento: `sse-frames.php` stampa i frame esatti che invia l'endpoint della Sezione 21.1, `channel.php` stampa le buste che un canale push pubblica nella Sezione 21.5, e `disconnect.php` riproduce il comportamento in caso di disconnessione della Sezione 21.6. Nessuno di essi ha bisogno di un modello.
:::

## 21.1 Server-Sent Events in Laravel

### Perché SSE invece dei WebSocket

Per le risposte di un agent il traffico è unidirezionale: il server manda, il browser riceve. SSE ti dà questo su HTTP ordinario, con un client integrato nel browser e nessuna infrastruttura aggiuntiva.

I WebSocket sono la scelta giusta quando anche il browser deve spingere — cosa che per un'interfaccia di chat non serve, perché il messaggio successivo è una nuova richiesta.

### Il controller

```php
<?php

declare(strict_types=1);

namespace App\Http\Controllers;

use App\Models\Conversation;
use App\Neuron\Agents\SupportAgent;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Gate;
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Workflow\Streaming\ProtocolEvent;
use NeuronAI\Workflow\Streaming\SSEEncoder;
use Symfony\Component\HttpFoundation\StreamedResponse;

class ChatStreamController extends Controller
{
    public function __invoke(
        Request $request,
        Conversation $conversation,
        SupportAgent $agent,
    ): StreamedResponse {
        Gate::authorize('participate', $conversation);

        $validated = $request->validate([
            'message' => ['required', 'string', 'max:4000'],
        ]);

        $agent = $agent->for($conversation->threadId());
        $agent->recoverFailedTurn();

        $stream = $agent->stream(new UserMessage($validated['message']));

        // Lazy until pulled: admit the run now, while a refusal can still be an HTTP status.
        $stream->valid();

        return response()->stream(function () use ($stream) {
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

Prima di un ciclo c'è un agent, e arriva nel modo in cui lo ha costruito la Sezione 18.1. La route nomina la conversazione — `Route::get('/chat/stream/{conversation}', ChatStreamController::class)` — l'azione riceve l'agent per iniezione nel metodo, e `for()` lo lega al thread della conversazione una volta che la policy ha autorizzato l'utente. Un agent senza un thread legato non fa streaming affatto. `recoverFailedTurn()` è la risposta alla quinta domanda della Sezione 18.4, data prima del turno e mai dopo; la Sezione 21.6 mostra perché un endpoint di streaming è il posto in cui si rivela più utile.

`stream()` è esso stesso il generator — iteralo direttamente. È anche lazy: non viene eseguito nulla finché non si estrae il primo elemento, e `$stream->valid()` lo estrae nel controller, prima che esista la risposta. Un thread che non può accettare il turno — un'altra scheda sta ancora facendo streaming su di esso — viene allora rifiutato con uno status HTTP, il 409 a cui lo mappa la Sezione 21.4, invece che con un `200` che finisce senza una parola. Senza stream adapter agganciato il generator produce i chunk object nativi di NeuronAI, e `TextChunk` è l'unico tipo che questo endpoint lascia passare. Tutto il resto — le tool call con i loro argomenti, i risultati dei tool — viene scartato sul server, che è la regola della Sezione 7.4 applicata al confine HTTP.

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
const source = new EventSource(`/chat/stream/${conversationId}?message=` + encodeURIComponent(text));

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

- SSE si adatta all'output di un agent: unidirezionale, HTTP puro, un client integrato nel browser.
- Autorizza, lega con `for()`, recupera e fai avanzare il generator prima che la risposta venga restituita: dopo il primo byte, un fallimento non può più essere uno status.
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

use App\Models\Conversation;
use App\Neuron\Agents\SupportAgent;
use Livewire\Component;
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\Stream\Chunks\ToolCallChunk;
use NeuronAI\Chat\Messages\UserMessage;

class Chat extends Component
{
    public Conversation $conversation;

    public string $input = '';
    public string $answer = '';
    public ?string $activity = null;
    public array $history = [];

    public function send(SupportAgent $agent): void
    {
        $this->authorize('participate', $this->conversation);

        $question = \trim($this->input);

        if ($question === '') {
            return;
        }

        $this->history[] = ['role' => 'user', 'content' => $question];
        $this->input     = '';
        $this->answer    = '';

        $agent = $agent->for($this->conversation->threadId());
        $agent->recoverFailedTurn();

        $stream = $agent->stream(new UserMessage($question));

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

L'agent arriva come in un controller. La pagina monta il componente con la sua conversazione — `<livewire:chat :conversation="$conversation" />` — Livewire risolve `SupportAgent` dal container per l'azione, e `send()` fa ciò che fa ogni endpoint di questo capitolo prima di un turno: autorizza, lega con `for()`, recupera. Livewire protegge l'ID del model dalla manomissione tra una richiesta e l'altra, ma la policy viene eseguita comunque a ogni `send()`: chi può usare una conversazione può cambiare mentre la pagina resta aperta.

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

use App\Models\Conversation;
use App\Neuron\Agents\SupportAgent;
use App\Neuron\ThreadScope;
use Generator;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Gate;
use NeuronAI\Agent\Adapters\AGUIAdapter;
use NeuronAI\Agent\Frontend\AGUIInputTranslator;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Workflow\Streaming\SSEEncoder;
use Symfony\Component\HttpFoundation\StreamedResponse;
use Throwable;

class AgentUiController extends Controller
{
    public function __invoke(Request $request, SupportAgent $agent): StreamedResponse
    {
        $request->validate([
            'threadId'           => ['required', 'string', 'regex:/^t\d+:u\d+:c\d+$/'],
            'runId'              => ['nullable', 'string'],
            'messages'           => ['required', 'array', 'min:1'],
            'messages.*.id'      => ['required', 'string'],
            'messages.*.role'    => ['required', 'string'],
            'messages.*.content' => ['nullable', 'string'],
            'state'              => ['nullable', 'array'],
            'resume'             => ['nullable', 'array'],
        ]);

        // The client names the thread; the server decides whether this user may use it.
        $threadId = $request->input('threadId');
        $conversation = Conversation::findOrFail(ThreadScope::of($threadId)->conversationId);

        Gate::authorize('participate', $conversation);
        abort_unless($conversation->threadId() === $threadId, 403);

        // The messages as posted: validate() returns only the keys its rules name.
        $messages = $request->input('messages');
        $last = \array_last($messages);

        // Answers to a paused run (approvals, browser tool results) continue it;
        // a trailing user message starts a new turn. Nothing else is accepted.
        $continuation = $request->array('resume') !== [] || $last['role'] === 'tool';
        abort_unless($continuation || $last['role'] === 'user', 422, 'Nothing to answer and no new message.');

        // On a copy of its own: the recovered turn must not stream into this response.
        $agent->for($threadId)->recoverFailedTurn();

        $adapter = new AGUIAdapter(
            threadId: $threadId,
            runId: $request->input('runId'),
            messages: $messages,
            state: $request->array('state'),
        );

        $agent = $agent->for($threadId)->setStreamAdapter(fn (): AGUIAdapter => $adapter);

        $events = $continuation
            ? $agent->submitInputs($request->all(), new AGUIInputTranslator())->events()
            : $agent->stream(new UserMessage((string) $last['content']));

        // Admission is lazy: start it now, so a refusal is an HTTP status, not a RUN_ERROR frame.
        $events->valid();

        return response()->stream(function () use ($events, $adapter): Generator {
            try {
                yield from SSEEncoder::encode($events);
            } catch (Throwable $e) {
                report($e);

                foreach ($adapter->error($e) as $event) {
                    yield SSEEncoder::frame($event);
                }
            }
        }, 200, $adapter->getHeaders());
    }
}
```

### Sette cose da segnalare

**L'adapter dà la forma, l'encoder fa i frame.** `setStreamAdapter()` fa sì che `stream()` produca oggetti `ProtocolEvent` — `RUN_STARTED`, `TEXT_MESSAGE_CONTENT` e il resto — invece dei chunk nativi. Accetta una factory, chiamata una volta per segmento di esecuzione (Sezione 7.5); questa richiesta esegue un solo segmento, quindi la closure restituisce l'istanza da cui la risposta prende i propri header. `SSEEncoder::encode()` trasforma ciascun evento in una riga `data:` e inoltra il valore di ritorno del generator, così l'`AgentState` finale è ancora lì — è ciò che `yield from` valuta — se ti serve. La callback è essa stessa un generator: Laravel stampa e fa il flush di ogni frame che essa produce con `yield`. L'adapter non sa nulla dei byte, ed è questo che permette allo stesso adapter di alimentare un canale di broadcast nella Sezione 21.5.

**`getHeaders()` fornisce gli header del protocollo — compreso `X-Accel-Buffering: no`.** Gli adapter integrati portano con sé la correzione per nginx della Sezione 21.2, quindi non c'è nulla da fondere.

**All'agent va solo l'ultimo messaggio dell'utente.** Un client AG-UI invia l'intera conversazione a ogni turno. L'agent ha già quella conversazione nella sua cronologia della conversazione durevole, indicizzata per thread — passargli la copia del client significa salvare due volte ogni messaggio precedente. I `messages` del client vanno invece all'adapter, che li usa per mantenere completo lo snapshot dei messaggi del protocollo. Vanno interi, da `$request->input('messages')`. `validate()` restituisce solo le chiavi che le sue regole nominano, e un adapter inizializzato con quel sottoinsieme ha perso ogni `toolCallId` e `toolCalls`: lancia `InputTranslationException` per qualunque conversazione che contenga un messaggio tool, e una continuazione che consegna un risultato di tool non può mai funzionare.

**Il thread è l'identità dell'agent — autorizzalo.** Il `threadId` di AG-UI diventa il thread dell'agent, e il thread *è* il workflow ID dell'agent: la chiave sotto cui sono archiviate la sua cronologia e ogni run sospesa. Questo lo rende esattamente il valore che la Sezione 18.2 diceva di non prendere mai dall'input dell'utente. Tre passaggi trasformano una stringa fornita dal client in un thread che questo utente può usare: `ThreadScope` (Sezione 18.3) ricava la conversazione dal nome, la policy decide se questo utente può usare quella conversazione, e il nome che il server deriva dal record deve essere quello inviato dal client. Solo allora viene letto o scritto qualcosa sotto di esso. Rimanda indietro anche `runId`: è l'identificatore per richiesta del client, e senza di esso il client non può correlare lo stream con la run che ha chiesto.

**La forma della richiesta decide fra nuovo turno e continuazione.** Un messaggio utente in coda è un nuovo turno, e va a `stream()`. Un array `resume` — il client che risponde alle interruzioni — o un messaggio tool in coda è la continuazione di una run in pausa, e va a `submitInputs()` con il translator del protocollo, che la valida rispetto alla richiesta persistita prima che qualunque cosa venga eseguita e lancia `InputTranslationException` per tutto ciò che non corrisponde. Il test di continuazione viene per primo, come nella Sezione 7.5: dopo una pausa di approvazione la lista del client finisce ancora con la domanda dell'utente. Nota che la continuazione chiama `events()`, non `stream()`: `stream()` avvia sempre un nuovo turno. Una continuazione non valida deve essere una risposta di errore, mai un ripiego su un nuovo turno.

**Fino al primo frame, un fallimento è uno status code.** Prima che la risposta venga restituita succedono due cose. `recoverFailedTurn()` porta a termine un turno fallito (Sezione 18.4) su una copia a sé stante — legata al thread, senza adapter — così la risposta recuperata finisce nella cronologia e non in questo stream. E `$events->valid()` estrae il primo evento. `stream()` e `events()` sono lazy: la run viene ammessa solo quando il generator viene estratto per la prima volta, e, lasciata alla callback, ciò avviene dopo che il `200` è già partito, così un thread che non può accettare il turno — un'approvazione ancora in sospeso, un'altra scheda in streaming — arriva al browser come un frame `RUN_ERROR` sotto uno status di successo. Estratto nel controller, il rifiuto è ancora un'eccezione che Laravel può trasformare in uno status. L'adapter viene costruito lì per lo stesso motivo: il suo costruttore valida i messaggi con cui viene inizializzato. Da quel punto in poi `SSEEncoder::encode()` è l'unica cosa che itera il generator, e un fallimento quando i frame già scorrono è già sul filo come `RUN_ERROR` quando raggiunge il `catch`: `$adapter->error()` allora non produce nulla, e chiude il protocollo solo se non era stato inviato alcun frame. Gli status sono mappati una sola volta per l'intera applicazione, in `bootstrap/app.php`:

```php
// bootstrap/app.php
return Application::configure(basePath: dirname(__DIR__))
    // ->withRouting(...) and ->withMiddleware(...) as the skeleton has them
    ->withExceptions(function (Exceptions $exceptions): void {
        // The first callback whose type matches wins: the most specific class goes first.
        $exceptions->render(fn (InputTranslationException $e) => response()->json(
            ['message' => $e->getMessage()], 400,
        ));
        $exceptions->render(fn (PersistenceException $e) => response()->json(
            ['message' => 'Conversations are unavailable. Retry later.'], 503,
        ));
        $exceptions->render(fn (RunInFlightException $e) => response()->json(
            ['message' => 'The conversation is busy.', 'status' => $e->status->value], 409,
        ));
        $exceptions->render(fn (WorkflowException $e) => response()->json(
            ['message' => 'The conversation changed. Reload it.'], 409,
        ));
    })->create();
```

Tutti e quattro stanno in `NeuronAI\Exceptions`. `PersistenceException` e `RunInFlightException` estendono entrambe `WorkflowException`, ed è per questo che l'ordine conta. Il messaggio di una `InputTranslationException` è scritto per i client; quello di una `WorkflowException` porta dettagli interni, e resta nel log.

**Cambia l'adapter, tieni tutto il resto.** `VercelAIAdapter` al posto di `AGUIAdapter` e lo stesso agent serve un protocollo frontend diverso — con `VercelAIInputTranslator` per le sue continuazioni. L'argomento delle interfacce della Sezione 2.2, applicato sul lato dell'output.

### Quando la run va in pausa

Se un tool del turno richiede approvazione (Capitolo 22), lo stream non finisce come uno completato. Il terminale `interrupt()` dell'adapter sostituisce `end()`: su AG-UI, `RUN_FINISHED` porta `outcome: {type: "interrupt", interrupts: [...]}`, un'interruzione `confirmation` per ogni tool call in sospeso, con l'ID della tool call come suo `id`; su Vercel, una parte `tool-approval-request` per ogni chiamata.

Un frontend che tratta ogni `RUN_FINISHED` come "la risposta è completa" renderizzerà una run in pausa come una conclusa. Controlla `outcome.type` prima di chiudere il turno. Il client risponde con un array `resume` nella richiesta successiva, che l'endpoint qui sopra instrada verso `submitInputs()`. La Sezione 22.5 copre il lato dell'approvazione per i client che non parlano AG-UI.

### Che cosa copre l'adapter, e che cosa no

Dalla Sezione 7.5, perché un team che sceglie un frontend deve saperlo prima di impegnarsi:

**Snapshot alla pausa, non delta.** L'adapter emette `STATE_SNAPSHOT` e `MESSAGES_SNAPSHOT` prima di concludere una run interrotta, inizializzati a partire da `state` e `messages` che hai passato al suo costruttore. Non emette `STATE_DELTA`. Se il tuo progetto dipende da una sincronizzazione fine dello stato condiviso mentre l'agent gira, l'adapter non te la darà.

**I tool definiti dal frontend richiedono un passo in più.** I client AG-UI possono dichiarare tool in `RunAgentInput.tools` perché li esegua il browser. NeuronAI li supporta come tool differiti: la run si sospende quando il modello ne chiama uno, l'adapter pubblica la chiamata e il client rimanda il risultato come messaggio tool in coda — il ramo di continuazione qui sopra. Ciò che l'endpoint non fa ancora è agganciare quei tool all'agent. `(new AGUIInputTranslator())->tools($request->all())` li costruisce dalla richiesta; aggiungili alla copia legata con `addTool()`, dopo aver respinto qualunque nome che oscuri uno dei tuoi tool lato server, e applica loro la tua approval policy come a qualunque altro tool. Esenta anche la route dai middleware `TrimStrings` e `ConvertEmptyStringsToNull` di Laravel: con essi, un risultato di tool che è una stringa vuota raggiunge il translator come `null` e viene rifiutato.

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

Una SPA manda un token; Sanctum o Passport lo gestiscono come al solito. La parte importante è che cosa viene detto all'*agent* sull'utente appena autenticato: nulla. Il container costruisce lo stesso `SupportAgent` privo di contesto per ogni richiesta (Sezione 18.1), l'endpoint autorizza il thread, e `for()` ne lega una copia. Ciò che l'agent fa per questo utente discende allora dal solo thread:

```php
class SupportAgent extends Agent
{
    // constructor, provider(), messageStore(), persistence() as in Chapter 18

    protected function tools(): array
    {
        $scope = ThreadScope::of($this->getThreadId());

        return [
            new SearchOrdersTool($scope->tenantId),
            new GetOrderStatusTool($scope->tenantId),
        ];
    }
}
```

Visibilità dei tool, cronologia della conversazione e filtri RAG discendono tutti da quell'unico input. Nessuna factory, e nessun `auth()` dentro l'agent: la stessa classe gira invariata sul queue worker della Sezione 21.5, dove non c'è alcun utente da interpellare. L'argomento della Sezione 18.3, ed è il motivo per cui il controller resta così breve.

### Punti chiave

- `setStreamAdapter()` accetta una factory e fa sì che `stream()` produca `ProtocolEvent`; `SSEEncoder::encode()` ne fa i frame; `getHeaders()` include già `X-Accel-Buffering`.
- All'agent manda solo l'ultimo messaggio dell'utente; la cronologia del client inizializza l'adapter — intera, da `input()`, non da `validate()`.
- Un array `resume` o un messaggio tool in coda è una continuazione: `submitInputs()` con il translator del protocollo, poi `events()`.
- Il `threadId` di AG-UI diventa il workflow ID dell'agent — autorizzalo rispetto alla conversazione che nomina, non fidarti mai del valore grezzo.
- Recupera un turno fallito e fai avanzare il generator prima di restituire la risposta: fino al primo frame, un rifiuto può ancora essere un 400 o un 409.
- Una run in pausa per un'approvazione finisce con un esito di interruzione, non con una semplice conclusione; controlla prima di chiudere il turno.
- I nodi producono eventi di avanzamento portabili; `mapEvent()` traduce o sopprime i tuoi.

## 21.5 Streaming da una coda

Questa è la sezione in cui le Parti IV e V si incontrano.

### Il problema

La Sezione 16.4 ha stabilito che le esecuzioni lunghe appartengono a una coda. Ma un queue worker non ha alcuna connessione HTTP con l'utente — quindi come arriva l'avanzamento al browser?

La risposta è un **canale di streaming**. Tutto ciò che abbiamo visto finora è streaming *pull*: il codice che itera il generator è il codice che detiene la risposta. Un canale è la metà *push*. Agganciane uno a un workflow o a un agent, insieme a uno stream adapter, e la run consegna al canale ogni evento di protocollo man mano che viene prodotto — a Pusher, a Redis, a un websocket — mentre il worker si limita a chiamare `run()`.

### L'architettura

```
Browser → POST /workflows             → crea il record della run e il suo run ID, restituisce { workflowId }
Browser → si iscrive a private-workflows.{workflowId}, attende l'iscrizione
Browser → POST /workflows/{id}/start  → invia il job
Worker  → esegue il workflow; il canale spinge ogni evento, in sequenza
Browser → riordina per sequenza, renderizza l'avanzamento, riconcilia in caso di buco
```

L'ordine delle prime tre righe conta. Pusher e Redis Pub/Sub non riproducono nulla: un evento pubblicato prima che il browser si iscrivesse è perso. Quindi il browser si iscrive per primo, e solo dopo chiede al server di partire. La prima richiesta fa un'altra cosa: conia il run ID — un UUID in una colonna `run_id` del record — prima che esista qualunque job. Il job qui sotto ne dipende.

### Il job

```php
<?php

declare(strict_types=1);

namespace App\Jobs;

use App\Models\WorkflowRun;
use App\Neuron\Workflows\ContentState;
use App\Neuron\Workflows\ContentWorkflow;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use NeuronAI\Agent\Adapters\AgentChunkAdapter;
use NeuronAI\Exceptions\RunInFlightException;
use NeuronAI\Workflow\Executor\ExecutionRequest;
use NeuronAI\Workflow\Persistence\PersistenceInterface;
use NeuronAI\Workflow\Streaming\Channel\PusherChannel;
use NeuronAI\Workflow\WorkflowStatus;
use Pusher\Pusher;

class RunContentWorkflow implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $tries = 3;

    /** Longer than the longest run, shorter than the queue connection's retry_after (360). */
    public int $timeout = 300;

    public function __construct(
        public readonly WorkflowRun $run,
    ) {}

    public function handle(PersistenceInterface $runs, Pusher $pusher): void
    {
        $workflowId = $this->run->workflow_id;

        $workflow = ContentWorkflow::make(
            workflowId: $workflowId,
            state: new ContentState(['topic' => $this->run->topic]),
        )
            ->setPersistence($runs)
            ->setLeaseTimeout(600)
            ->setStreamAdapter(fn (): AgentChunkAdapter => new AgentChunkAdapter())
            ->setChannel(fn (): PusherChannel => new PusherChannel(
                client: $pusher,
                channel: "private-workflows.{$workflowId}",
                batchSize: 1,
            ));

        try {
            // The run ID was minted with the record: every delivery of this job names the same run.
            $state = $workflow->run(ExecutionRequest::start(
                runId: $this->run->run_id,
                recoverFailed: true,
            ));
        } catch (RunInFlightException $e) {
            if ($e->status !== WorkflowStatus::Running) {
                throw $e;   // paused, not dead: there is nothing to recover
            }

            // A delivery that was killed still holds the lease: come back when it has expired.
            $this->release(\max(1, $e->leaseExpiresAt - \time()));

            return;
        }

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

### Cinque cose che questo job fa diversamente da una richiesta web

**`run()`, non un ciclo.** Con un adapter e un canale agganciati, il workflow consuma il proprio stream e consegna ogni evento attraverso il canale nel momento in cui accade. `run()` restituisce lo stato finale quando il segmento si completa o va in pausa. Non c'è alcun generator da iterare e nulla da stampare. Entrambi i setter accettano una factory, perché un adapter e un canale conservano lo stato dello stream di un segmento: il segmento che va in pausa per un'approvazione e quello che continua dopo ne costruiscono ciascuno uno proprio. Un agent su un worker ha bisogno di un'altra cosa: il suo turno deve essere in streaming — `chat($message, stream: true)`, la forma eager della Sezione 7.5 — perché un semplice `chat()` fa una chiamata al modello con buffer, e nessun testo raggiunge mai il canale.

**È ancora l'adapter a decidere la forma.** Un canale trasporta eventi di protocollo, mai oggetti nativi, quindi ha bisogno di un adapter. `AgentChunkAdapter` è il vocabolario proprio di NeuronAI per un consumatore che non parla alcun protocollo di UI: ogni chunk o evento di avanzamento diventa un evento che prende il nome dal suo tipo — `text`, `tool-call`, `activity`, `step-started` — con i campi del chunk stesso come payload. Se il browser esegue un client AG-UI o Vercel, aggancia invece quell'adapter; al canale non importa.

**Il canale riporta il ciclo di vita.** Dopo i frame terminali dell'adapter, il canale invia `stream.completed`, `stream.interrupted` o `stream.failed`, con il solo workflow ID — niente stato, niente dettagli dell'eccezione. Non servono eventi di broadcast tuoi come `WorkflowCompleted` o `WorkflowPaused`: il browser apprende l'esito dallo stream e recupera il risultato dalla tua applicazione, che è il record autorevole.

**La pausa è un valore di ritorno.** Una run interrotta ritorna normalmente con `isInterrupted()` a true — niente da catturare. Il Capitolo 22 prosegue da lì.

**Una riconsegna porta a termine la stessa run.** Ritentare un job così costoso sembra pagare due volte. Non è così, grazie alla Sezione 13.5: ogni nodo completato è uno step registrato. Il run ID è stato coniato insieme al record, quindi ogni consegna di questo job nomina la stessa run, e `recoverFailed: true` dice a un avvio che trova quella run fallita — o ancora marcata come in esecuzione da un worker che è stato ucciso, una volta scaduto il suo lease — di continuarla invece di ricominciare. Gli step registrati vengono riprodotti dallo store, non eseguiti: la ricerca e la bozza che la prima consegna ha pagato non vengono comprate due volte, e solo il nodo che era in esecuzione quando è morta viene eseguito di nuovo. Anche un semplice `run()` recupera una run fallita, ma sostituisce quella il cui worker è stato ucciso, e riparte dal primo nodo. Finché il lease della consegna morta è ancora valido l'avvio viene rifiutato con `RunInFlightException`, e il job si rilascia da solo finché il lease non è scaduto.

Tre orologi lo rendono sicuro. Il lease — `setLeaseTimeout(600)`: un workflow semplice non ha alcun lease finché non ne imposti uno, un agent ha per default gli stessi dieci minuti — deve durare più del singolo nodo più lungo, così che una run lenta non venga mai scambiata per morta. Il `$timeout` del job deve durare più della run più lunga. E il `retry_after` della connessione di coda deve superare `$timeout`: `DB_QUEUE_RETRY_AFTER=360` per un `$timeout` di 300, `REDIS_QUEUE_RETRY_AFTER` su una coda Redis. Laravel fornisce 90, il che consegna a un secondo worker un job ancora in esecuzione. Ciò che lo store non può fare è ricordare una run che si è completata — i suoi record vengono cancellati — quindi un job consegnato di nuovo dopo il successo avvia una nuova run; sono gli orologi a impedire che accada.

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

Due default di `PusherChannel` vale la pena conoscerli prima della prima run. Invia gli eventi in batch da dieci, e un batch parziale aspetta finché non si riempie o il segmento finisce, quindi una manciata di eventi di avanzamento arriverebbe tutta alla fine: `batchSize: 1` nel job è ciò che fa partire ciascuno non appena viene prodotto. E un nome di canale ammette solo lettere, cifre e `-_=@,.;`. Un workflow ID che ne diventa parte non può contenere i due punti, quindi lo stile `t1:refund:42` della Sezione 18.3 richiede qui un altro separatore — `t1.content.42`.

Preferisci Redis? Una factory che restituisce `new RedisChannel($redis, "workflows:{$id}")` pubblica le stesse buste su Redis Pub/Sub per un processo che detiene la connessione del browser. Preferisci il broadcasting di Laravel? `CallbackChannel` avvolge una closure per ogni metodo del ciclo di vita, così `onSend` può chiamare `Broadcast::private(...)->as($event->type)->with($event->data)->sendNow()`. **`sendNow()`, mai un broadcast in coda.** Un broadcast in coda mette in fila i tuoi aggiornamenti di avanzamento dietro al job che li sta producendo — su un solo worker, un deadlock al rallentatore — e con più worker li consegna fuori ordine.

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

channel.bind('pusher:subscription_succeeded', function once() {
    channel.unbind('pusher:subscription_succeeded', once);   // it fires again on every reconnect
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
- Step durevoli, riprodotti quando un job viene consegnato di nuovo (13.5)
- Interruzione e persistenza (15.4)
- Persistenza su database (18.4)
- Esecuzione asincrona (16.4)
- Adapter che spingono verso un trasporto esterno (7.5)
- `pcntl` disponibile, quindi i tool paralleli funzionano (5.13)
- Inspector registrato sul workflow (23.3)

Quest'ultimo è la misconfigurazione con più probabilità di morderti: nulla viene monitorato se non sottoscrivi il listener, e un worker è esattamente il posto dove nessuno si accorge che manca.

### Punti chiave

- Push, non pull: una factory di adapter più una factory di canale, e il worker chiama semplicemente `run()`.
- Prima iscriviti, poi avvia la run — Pusher e Redis non riproducono nulla.
- `PusherChannel` invia buste numerate in sequenza e frammentabili, in batch da dieci a meno che tu non passi `batchSize: 1`; `@neuron-core/streaming` riordina, riassembla e segnala i buchi.
- Il canale riporta completamento, pausa e fallimento; recupera i risultati dall'applicazione.
- Autorizza il canale per tenant. Riserva il run ID e lascia che il job ritenti: una riconsegna porta a termine la stessa run dal suo ultimo step registrato, purché `retry_after` superi `$timeout`.

## 21.6 Disconnessione e costo orfano

### Il problema che nessuno menziona

Un utente avvia un'esecuzione di 30 secondi. Al quarto secondo chiude la scheda.

Dopodiché dipende da dove vive la run. Su un queue worker non succede proprio nulla: il browser non c'è più e **l'agent continua a girare.** Ogni chiamata al modello che resta viene fatturata. In un workflow multi-agente è una somma sostanziosa spesa per un output che nessuno leggerà mai. In una risposta in streaming succede l'opposto: la run viene troncata a metà turno, e ciò che aveva già scritto decide se il messaggio successivo dell'utente riceverà risposta.

A basso volume entrambi sono invisibili. Su scala il primo è una voce di bilancio e il secondo è un ticket di supporto.

### Che cosa fa una disconnessione a una risposta in streaming

Con l'`ignore_user_abort=0` predefinito di PHP, il tuo ciclo non viene mai a sapere che il client se n'è andato. Lo scopre PHP, alla prima scrittura dopo la disconnessione, e termina lo script lì e subito. Nessuna riga dopo quell'`echo` viene eseguita: un controllo `connection_aborted()` in cima al ciclo non viene mai raggiunto, l'evento `done` non viene mai inviato, il codice dopo il `foreach` non viene mai eseguito.

Il motore se ne accorge. Una run il cui consumatore smette di estrarre prima che si sia conclusa viene registrata come **fallita**, subito, quando la richiesta si chiude e il generator viene distrutto. Non resta marcata come in esecuzione finché non scade il lease di dieci minuti dell'agent, quindi il thread non è bloccato per il messaggio successivo.

Ciò che si perde è la risposta. Se vale la pena averla che qualcuno stia guardando o no, dillo nel controller della Sezione 21.1, prima che la risposta venga restituita:

```php
// The run now completes into the history even if the tab closes.
\ignore_user_abort(true);

return response()->stream(function () use ($stream) {
    foreach ($stream as $chunk) {
        if (! $chunk instanceof TextChunk || \connection_aborted()) {
            continue;   // nobody is reading: keep pulling, stop writing
        }

        // ... frame, echo and flush as in Section 21.1
    }

    // ... the done event
}, 200, [/* ... the same four headers */]);
```

Solo ora `connection_aborted()` significa qualcosa: lo script sopravvive alla scrittura fallita, e la funzione lo segnala dall'iterazione successiva in poi. Il ciclo continua a estrarre, quindi il turno finisce e l'utente trova la risposta completa quando torna. Sostituisci `continue` con `break` e sei tornato al comportamento predefinito, per scelta: il motore fa fallire la run quando la richiesta termina e il generator viene rilasciato.

L'altro modo di conservare la risposta è non legare affatto la run alla richiesta: la run in coda della Sezione 21.5, che nessun browser può interrompere.

**Un'avvertenza onesta:** qualunque cosa tu scelga, i token generati prima della disconnessione vengono fatturati. Terminare la run limita il danno; non lo annulla.

### Perché il messaggio successivo può fallire

La run fallita in sé è innocua: il turno successivo sul thread la sostituisce. Ciò che conta è che cosa il turno fallito aveva già salvato.

Se il client se n'è andato prima che iniziasse la prima risposta, non è stato salvato nulla, e al messaggio successivo si risponde semplicemente. Se se n'è andato dopo uno step di tool, la domanda dell'utente è già nella cronologia. Un secondo messaggio utente subito dopo non è una conversazione valida, quindi il successivo `chat()` o `stream()` lancia `ChatHistoryException: Invalid message sequence` — e a quel punto ha già sostituito la run fallita, l'unica cosa che si sarebbe potuta recuperare.

Quindi porta prima a termine il turno fallito. È `recoverFailedTurn()`, dalla Sezione 18.4: fai `inspect()` della run del thread, e se il suo stato è `Failed`, continuala con `run(ExecutionRequest::resume(expectedRunId: ..., expectedExecutionAttempt: ...))`. La run si completa dai suoi step registrati — un tool che ha già girato non viene rieseguito — la sua risposta finisce nella cronologia, e la nuova domanda segue allora una conversazione valida. È il motivo per cui ogni endpoint di questo capitolo lo chiama prima di avviare un turno. Non è gratis: porta a termine ogni turno fallito, anche quello che non aveva salvato nulla, quindi ogni domanda abbandonata costa una chiamata al modello per una risposta che l'utente non ha aspettato. È il prezzo di un thread che resta utilizzabile.

Il `disconnect.php` del repository di accompagnamento esegue i tre casi fianco a fianco: un client che se ne va prima che sia salvato qualcosa, e al messaggio successivo si risponde; uno che se ne va dopo uno step di tool, e il messaggio successivo viene rifiutato con la `ChatHistoryException`; e lo stesso ancora con il turno fallito portato prima a termine — al messaggio successivo si risponde, e il tool ha girato una sola volta in totale.

Un caso che `recoverFailedTurn()` non può vedere: un processo ucciso di netto — memoria esaurita, il `request_terminate_timeout` di FPM — non esegue alcun distruttore e non registra nulla. La sua run resta `running`, e i nuovi turni sul thread vengono rifiutati con `RunInFlightException` finché il lease non scade. Se la domanda era stata salvata, il turno dopo fallisce come sopra, e il `resetConversation()` della Sezione 18.4 è ciò che resta.

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

- Una scheda chiusa non ferma una run in coda — continui a pagare — e ne tronca una in streaming a metà turno.
- Con l'`ignore_user_abort=0` predefinito PHP termina lo script alla scrittura successiva; il motore fa fallire la run subito, e il thread non resta bloccato.
- `ignore_user_abort(true)`, o una run in coda, conserva la risposta.
- Un turno fallito che aveva salvato la sua domanda blocca il successivo: `recoverFailedTurn()` prima di ogni turno.
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
5. **Gestione della disconnessione.** `recoverFailedTurn()` prima di ogni turno, e una scelta che puoi difendere fra lasciare che una scheda chiusa termini la run e conservarla con `ignore_user_abort(true)`.

### Criteri di accettazione

- Il primo token visibile arriva ben sotto il secondo su un modello locale. Misuralo; non darlo per scontato.
- Fare una domanda che innesca un tool mostra l'etichetta amichevole, poi la risposta.
- Aggiungere un nuovo tool senza aggiungerne l'etichetta mostra "Working on it", non il nome interno del tool. Testalo deliberatamente.
- Chiudere la scheda a metà risposta lascia una run fallita, non un thread bloccato — e un nuovo messaggio sulla stessa conversazione, inviato subito dopo, riceve risposta invece di essere rifiutato. Provalo ancora una volta con una domanda che innesca un tool, chiudendo la scheda dopo che il tool ha girato.
- `curl -N` fa streaming attraverso l'intero stack, non solo in locale.

### La parte che le persone saltano

Il requisito quattro. È allettante dichiarare vittoria quando funziona su `artisan serve`, dove non c'è nginx né proxy. Il primo deploy è il punto in cui lo streaming si rompe, e la bisezione della Sezione 21.2 è la differenza fra cinque minuti e un pomeriggio.

Esegui i tre comandi `curl -N` contro il tuo vero ambiente di staging prima di dichiarare finito questo laboratorio.

### Andare oltre

Aggiungi un pulsante "stop". Interrompere la richiesta dal lato browser è la versione facile, e la Sezione 21.6 dice quanto costa: la run fallisce e la risposta parziale va persa. Quella migliore tiene aperta la connessione: avvolgi il client HTTP del provider in `NeuronAI\HttpClient\StoppableHttpClient` con una closure che legge un flag della cache, alza il flag da un endpoint di stop, e la risposta in streaming termina al suo evento successivo con il testo fin lì raccolto conservato nella cronologia. Poi misura che cosa ha risparmiato: esegui lo stesso prompt fino alla fine, annota il conteggio dei token e confronta con una run fermata. Quel numero è l'argomento per costruire il pulsante.
