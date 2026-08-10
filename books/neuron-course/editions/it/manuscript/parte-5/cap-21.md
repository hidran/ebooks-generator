# Capitolo 21 — Streaming verso il frontend

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

Questo capitolo è concettuale e non ha codice a sé stante, ma il repository di accompagnamento [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) contiene le versioni eseguibili di tutto ciò che il libro costruisce.
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
use Illuminate\Http\Request;
use NeuronAI\Chat\Messages\UserMessage;
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
            $handler = $this->agent->stream(new UserMessage($validated['message']));

            foreach ($handler->events() as $chunk) {
                echo 'data: ' . \json_encode([
                    'type'    => \class_basename($chunk),
                    'content' => $chunk->content ?? null,
                ]) . "\n\n";

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

### I quattro header, ciascuno con un compito

**`Content-Type: text/event-stream`** — dice al browser che questo è SSE.

**`Cache-Control: no-cache, no-transform`** — `no-transform` conta: alcuni proxy comprimono o riscrivono le risposte, cosa che rompe i confini dei frame.

**`X-Accel-Buffering: no`** — specifico di nginx, e quello che ti salva una giornata. Senza, nginx bufferizza la risposta e la consegna tutta in una volta, momento in cui hai la complessità dello streaming senza nessuno dei suoi benefici.

**`Connection: keep-alive`** — tieni aperta la connessione.

### Il formato dei frame SSE

```
data: {"type":"TextChunk","content":"Hello"}\n\n
```

Due a capo terminano un frame. Sbagliane uno e il browser aspetta per sempre un frame che non si completa mai — un fallimento che sembra "lo streaming non funziona" ed è un carattere.

### Il frontend

```javascript
const source = new EventSource('/chat/stream?message=' + encodeURIComponent(text));

source.onmessage = (e) => {
    const chunk = JSON.parse(e.data);

    if (chunk.type === 'TextChunk') {
        output.textContent += chunk.content;
    }
};

source.addEventListener('done', () => source.close());

source.onerror = () => source.close();
```

**`EventSource` fa solo GET.** Per un body POST o usi `fetch()` con un reader di `ReadableStream`, o accetti il messaggio come parametro di query — cosa che limita la lunghezza del messaggio e mette contenuto dell'utente nei log di accesso. Per qualunque cosa reale, usa `fetch`.

### Punti chiave

- SSE si adatta all'output di un agent: unidirezionale, HTTP puro, riconnessione automatica.
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
    fastcgi_pass   unix:/var/run/php/php8.3-fpm.sock;
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

La documentazione di AG-UI lo dice direttamente: manda gli header del protocollo e fai flush dopo ogni riga, o lo stream può restare incastrato nei buffer di output di PHP o nei proxy.

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
use Livewire\Component;
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

        $handler = $agent->stream(new UserMessage($question));

        foreach ($handler->events() as $chunk) {
            if ($chunk instanceof ToolCallChunk) {
                $this->activity = $this->label($chunk->tool->getName());
                $this->stream(to: 'activity', content: $this->activity, replace: true);
                continue;
            }

            if ($chunk instanceof ToolResultChunk) {
                continue;
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

`$this->label()` mappa i nomi dei tool su testo rivolto all'utente, con `?? 'Working on it'` come fallback.

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

use App\Neuron\Agents\SupportAgent;
use Illuminate\Http\Request;
use NeuronAI\Chat\Messages\Stream\Adapters\AGUIAdapter;
use NeuronAI\Chat\Messages\UserMessage;
use Symfony\Component\HttpFoundation\StreamedResponse;

class AgentUiController extends Controller
{
    public function __invoke(Request $request, SupportAgent $agent): StreamedResponse
    {
        $input = $request->validate([
            'threadId'           => ['required', 'string'],
            'runId'              => ['required', 'string'],
            'messages'           => ['required', 'array'],
            'messages.*.role'    => ['required', 'string'],
            'messages.*.content' => ['required', 'string'],
        ]);

        $messages = \collect($input['messages'])
            ->where('role', 'user')
            ->map(fn (array $m) => new UserMessage($m['content']))
            ->all();

        $adapter = new AGUIAdapter(
            threadId: $input['threadId'],
            runId: $input['runId'],
        );

        return response()->stream(function () use ($agent, $messages, $adapter) {
            foreach ($agent->stream($messages)->events($adapter) as $line) {
                echo $line;
                \flush();
            }
        }, 200, \array_merge($adapter->getHeaders(), [
            'X-Accel-Buffering' => 'no',
        ]));
    }
}
```

### Quattro cose da segnalare

**`getHeaders()` fornisce gli header del protocollo.** L'`X-Accel-Buffering` fondilo tu — la correzione per nginx della Sezione 21.2 non è affare dell'adapter.

**Rimanda indietro `threadId` e `runId`.** La Sezione 7.5 ha stabilito che ometterli fa sì che l'adapter se li inventi, il che significa che il client non può correlare lo stream con l'esecuzione che ha richiesto.

**Valida il payload.** Arriva da un browser. L'array `messages` è input utente come qualunque altro.

**Cambia l'adapter, tieni tutto il resto.** `VercelAIAdapter` al posto di `AGUIAdapter` e lo stesso agent serve un protocollo frontend diverso. L'argomento delle interfacce della Sezione 2.2, applicato sul lato dell'output.

### Le due limitazioni, ribadite

Dalla Sezione 7.5, perché un team che sceglie un frontend deve saperlo prima di impegnarsi:

**Solo tool lato server.** I tool agganciati al tuo agent girano sul tuo server; il client viene informato tramite eventi `TOOL_CALL_*`. I tool *definiti dal frontend* di AG-UI — dichiarati nel campo `tools` di `RunAgentInput` ed eseguiti dal client — non sono gestiti.

**Nessun evento di stato condiviso.** L'adapter non emette `STATE_SNAPSHOT`, `STATE_DELTA` o `MESSAGES_SNAPSHOT`, quindi le funzionalità di sincronizzazione dello stato lato client non sono disponibili attraverso di esso.

Se stai valutando CopilotKit o un frontend AG-UI simile, verifica se il tuo progetto dipende da una delle due. Meglio scoprirlo adesso che dopo aver costruito il frontend.

### Autenticazione

Una SPA manda un token; Sanctum o Passport lo gestiscono come al solito. La parte importante è che l'*agent* venga risolto per l'utente autenticato:

```php
$this->app->bind(SupportAgent::class, function ($app) {
    return new SupportAgent(
        tenant: $app['auth']->user()->tenant,
        user:   $app['auth']->user(),
    );
});
```

Visibilità dei tool, cronologia chat e filtri RAG discendono tutti da quel binding. L'argomento della Sezione 18.1, ed è il motivo per cui il controller resta così breve.

### Punti chiave

- `->events($adapter)` più `$adapter->getHeaders()`; l'`X-Accel-Buffering` aggiungilo tu.
- Rimanda indietro `threadId` e `runId` così che il client possa correlare.
- Due lacune di AG-UI: niente tool definiti dal frontend, niente eventi di sincronizzazione dello stato.
- Risolvi l'agent per utente autenticato; tutto il resto discende da lì.

## 21.5 Streaming da una coda

Questa è la sezione in cui le Parti IV e V si incontrano.

### Il problema

La Sezione 16.4 ha stabilito che le esecuzioni lunghe appartengono a una coda. Ma un queue worker non ha alcuna connessione HTTP con l'utente — quindi come arriva l'avanzamento al browser?

### L'architettura

```
Browser  → POST /workflows   → invia il job → restituisce { workflowId }
Browser  → si iscrive a un canale privato per quel workflowId
Worker   → esegue il workflow → trasmette ogni evento di avanzamento
Browser  → renderizza l'avanzamento in tempo reale
Worker   → finisce → trasmette il completamento
```

### Il job

```php
<?php

declare(strict_types=1);

namespace App\Jobs;

use App\Events\WorkflowProgressed;
use App\Neuron\Workflows\ContentWorkflow;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use NeuronAI\Workflow\Interrupt\WorkflowInterrupt;
use NeuronAI\Workflow\Persistence\EloquentPersistence;
use NeuronAI\Laravel\Models\WorkflowInterrupt as WorkflowInterruptModel;

class RunContentWorkflow implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $timeout = 600;
    public int $tries = 1;   // agent runs are expensive — do not blind-retry

    public function __construct(
        public readonly string $workflowId,
        public readonly int $tenantId,
        public readonly string $topic,
    ) {}

    public function handle(): void
    {
        $workflow = new ContentWorkflow(
            persistence: new EloquentPersistence(WorkflowInterruptModel::class),
            workflowId: $this->workflowId,
        );

        try {
            $handler = $workflow->init();

            foreach ($handler->events() as $event) {
                WorkflowProgressed::dispatch(
                    $this->workflowId,
                    $event->message ?? '',
                );
            }

            WorkflowCompleted::dispatch($this->workflowId, $handler->getResult());

        } catch (WorkflowInterrupt $interrupt) {
            PendingApproval::create([
                'workflow_id' => $interrupt->getWorkflowId(),
                'tenant_id'   => $this->tenantId,
                'request'     => \json_encode($interrupt->getRequest()),
                'status'      => 'pending',
            ]);

            WorkflowPaused::dispatch($this->workflowId);
        }
    }
}
```

### L'evento di broadcast

```php
class WorkflowProgressed implements ShouldBroadcastNow
{
    public function __construct(
        public readonly string $workflowId,
        public readonly string $message,
    ) {}

    public function broadcastOn(): PrivateChannel
    {
        return new PrivateChannel("workflows.{$this->workflowId}");
    }
}
```

**`ShouldBroadcastNow`, non `ShouldBroadcast`.** Il secondo mette in coda il broadcast, il che significa che i tuoi aggiornamenti di avanzamento si accodano dietro al job che li sta producendo. Su un solo worker è un deadlock al rallentatore.

### L'autorizzazione del canale

```php
// routes/channels.php
Broadcast::channel('workflows.{workflowId}', function ($user, string $workflowId) {
    return WorkflowRun::where('id', $workflowId)
        ->where('tenant_id', $user->tenant_id)
        ->exists();
});
```

Senza questo, chiunque indovini un ID di workflow guarda il lavoro dell'agent di qualcun altro. I quattro punti di fuga della Sezione 18.3 hanno un quinto parente: il canale di broadcast.

### Il frontend

```javascript
Echo.private(`workflows.${workflowId}`)
    .listen('WorkflowProgressed', (e) => {
        progressList.append(`<li>${e.message}</li>`);
    })
    .listen('WorkflowPaused', () => {
        showMessage('Waiting for approval.');
    })
    .listen('WorkflowCompleted', (e) => {
        showResult(e.result);
    });
```

### Che cosa compone

Questo singolo job è gran parte del libro che converge:

- Streaming dei workflow con `yield` (14.4)
- Interruzione e persistenza (15.4)
- Persistenza Eloquent (18.4)
- Esecuzione asincrona (16.4)
- Adapter che spingono verso un trasporto esterno (7.5)
- `pcntl` disponibile, quindi i tool paralleli funzionano (5.13)
- Inspector qui ha bisogno di `autoFlush: true` (10.2)

Quest'ultimo è la misconfigurazione con più probabilità di morderti: senza, il worker accumula eventi di trace e non li spedisce mai, perché non c'è alcuna fine della richiesta.

### Punti chiave

- Invia il job, restituisci un ID, iscriviti a un canale privato, trasmetti l'avanzamento.
- `ShouldBroadcastNow` — i broadcast in coda vanno in deadlock dietro al job che li produce.
- Autorizza il canale per tenant.
- `$tries = 1` sui job degli agent; i ritentativi ciechi rispendono soldi.
- `autoFlush: true` per Inspector sui worker.

## 21.6 Disconnessione e costo orfano

### Il problema che nessuno menziona

Un utente avvia un'esecuzione di 30 secondi. Al quarto secondo chiude la scheda.

Il browser non c'è più. **L'agent continua a girare.** Ogni chiamata al modello che resta viene fatturata. In un workflow multi-agente è una somma sostanziosa spesa per un output che nessuno leggerà mai.

A basso volume è invisibile. Su scala è una voce di bilancio.

### Rilevarlo in una risposta in streaming

```php
return response()->stream(function () use ($agent, $message) {
    $handler = $agent->stream(new UserMessage($message));

    foreach ($handler->events() as $chunk) {
        if (\connection_aborted()) {
            \Log::info('Client disconnected — stopping agent run');
            break;
        }

        echo 'data: ' . \json_encode(['content' => $chunk->content]) . "\n\n";
        \flush();
    }
}, 200, $headers);
```

`connection_aborted()` richiede che tu abbia scritto sulla connessione — PHP rileva la pipe rotta solo su un tentativo di scrittura. Poiché stai facendo streaming, stai scrivendo, quindi funziona. Non funzionerebbe in un endpoint senza streaming.

**Un'avvertenza onesta:** uscire dal ciclo ferma la *tua* iterazione. Una chiamata al modello già in volo si completa e viene fatturata. Stai limitando il danno, non eliminandolo.

### Per i workflow in coda

Un browser disconnesso non ferma un worker, e non dovrebbe — l'utente potrebbe tornare, e il risultato vale la pena averlo. Ma ci sono casi in cui la cancellazione è giusta:

```php
public function handle(): void
{
    foreach ($handler->events() as $event) {
        if (Cache::has("workflow:{$this->workflowId}:cancelled")) {
            $this->recordCancellation();
            return;
        }

        WorkflowProgressed::dispatch(/* ... */);
    }
}
```

```php
// A cancel endpoint
Cache::put("workflow:{$id}:cancelled", true, now()->addHour());
```

Cancellazione esplicita, non dedotta dalla disconnessione.

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

Registra l'uso reale dai conteggi di token della risposta dopo ogni esecuzione. La Sezione 1.3 diceva di catturare l'uso fin dal primo prototipo; ecco a cosa serve catturarlo.

### Punti chiave

- Una scheda chiusa non ferma un agent — continui a pagare.
- `connection_aborted()` dentro il ciclo dello stream limita il danno.
- Il lavoro in coda va cancellato esplicitamente, non per deduzione.
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
5. **Gestione della disconnessione** con `connection_aborted()`.

### Criteri di accettazione

- Il primo token visibile arriva ben sotto il secondo su un modello locale. Misuralo; non darlo per scontato.
- Fare una domanda che innesca un tool mostra l'etichetta amichevole, poi la risposta.
- Aggiungere un nuovo tool senza aggiungerne l'etichetta mostra "Working on it", non il nome interno del tool. Testalo deliberatamente.
- Chiudere la scheda a metà risposta produce una riga di log e ferma il ciclo.
- `curl -N` fa streaming attraverso l'intero stack, non solo in locale.

### La parte che le persone saltano

Il requisito quattro. È allettante dichiarare vittoria quando funziona su `artisan serve`, dove non c'è nginx né proxy. Il primo deploy è il punto in cui lo streaming si rompe, e la bisezione della Sezione 21.2 è la differenza fra cinque minuti e un pomeriggio.

Esegui i tre comandi `curl -N` contro il tuo vero ambiente di staging prima di dichiarare finito questo laboratorio.

### Andare oltre

Aggiungi un pulsante "stop" che interrompe la richiesta dal lato browser, e conferma che `connection_aborted()` scatti. Poi misura che cosa ha risparmiato: esegui lo stesso prompt fino alla fine, annota il conteggio dei token e confronta con un'esecuzione interrotta. Quel numero è l'argomento per costruire il pulsante.
