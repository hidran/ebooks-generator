# Capitolo 23 — Produzione

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

Gran parte di questo capitolo è configurazione e checklist, ma il listener dell'uso della Sezione 23.1 è eseguibile senza Laravel in [`chapters/Ch23`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch23) nel repository di accompagnamento: `usage.php` registra i conteggi dei token di due inferenze da un fake provider, senza modello e senza API key.
:::

## 23.1 Controllo dei costi

### Prima misura

Non puoi gestire ciò che non registri. Registra l'uso a ogni inferenza:

```php
use NeuronAI\Agent\Agent;
use NeuronAI\Agent\Observability\InferenceStop;

class RecordUsage
{
    public function __construct(
        private readonly Agent $agent,
    ) {}

    public function __invoke(InferenceStop $event): void
    {
        $usage = $event->response->message()->getUsage();

        if ($usage === null) {
            return;   // the provider reported none
        }

        try {
            $scope = ThreadScope::of($event->execution?->workflowId);

            AiUsage::create([
                'tenant_id'     => $scope->tenantId,
                'user_id'       => $scope->userId,
                'agent'         => $this->agent::class,
                'model'         => $this->agent->getProvider()->getModel(),
                'input_tokens'  => $usage->inputTokens,
                'output_tokens' => $usage->outputTokens,
                'cached_tokens' => $usage->cachedInputTokens,
            ]);
        } catch (\Throwable $e) {
            report($e);   // a lost row must not become a failed turn
        }
    }
}
```

```php
// NeuronServiceProvider::register()
$this->app->afterResolving(Agent::class, function (Agent $agent): void {
    $agent->subscribe(InferenceStop::class, new RecordUsage($agent));
});
```

L'osservabilità in NeuronAI è un event dispatcher PSR-14 posseduto da ogni istanza di agent (Sezione 10.2), e `InferenceStop` scatta dopo ogni chiamata al modello — quindi questo scrive una riga per inferenza, non per richiesta. Un agent che cicla attraverso tre tool call produce quattro righe, che è esattamente la granularità che rende visibile un agent in loop. Due dettagli sono facili da sbagliare: i conteggi dei token stanno sul messaggio della *risposta del provider*, `$event->response->message()->getUsage()` — `$event->message` è l'ultimo messaggio *inviato* — e `getUsage()` restituisce `null` quando un provider non riporta nulla, quindi gestisci il caso.

Il listener non sa nulla di chi chiama. L'evento porta il thread a cui la run è associata, e il thread nomina il tenant e l'utente (Sezione 18.3) — la strada che segue il listener di audit della Sezione 19.3. Il modello viene chiesto all'agent quando l'evento scatta, non quando il listener viene costruito: una volta che la factory di fallback della Sezione 23.2 può scambiare i provider, un nome di modello catturato alla sottoscrizione è una congettura. E la scrittura sta dentro un `try`. `InferenceStop` viene emesso dall'interno della run, quindi un'eccezione lanciata da un listener fa fallire il turno; una tabella di uso fuori servizio dovrebbe costarti una riga, non una risposta.

Sottoscrivilo dove vengono costruiti gli agent, così nessun agent gli sfugge. Gli agent del Capitolo 18 sono costruiti dal container, e un callback `afterResolving()` in `NeuronServiceProvider` viene eseguito per ogni sottoclasse di `Agent` che il container risolve; la copia che crea `for()` mantiene il listener. Un agent costruito a mano con `::make()` non passa mai dal container e non viene registrato.

Conserva `cached_tokens` anche se oggi lo ignori. Il prompt caching fattura quei token a una frazione della tariffa normale, e NeuronAI li riporta allo stesso modo per ogni provider: `inputTokens` è l'intero prompt, e `cachedInputTokens` è la parte che è stata letta dalla cache. Se calcoli tutti gli `input_tokens` alla tariffa piena sovrastimi ogni cache hit; se aggiungi `cached_tokens` sopra, li conti due volte. Calcola il prezzo della riga quando la scrivi, così che una modifica successiva dei prezzi non riscriva la storia:

```php
class AiUsage extends Model
{
    // ...

    protected static function booted(): void
    {
        static::creating(function (AiUsage $usage): void {
            // Your own price table in config/neuron.php, per million tokens
            $rate = config("neuron.prices.{$usage->model}")
                ?? throw new LogicException("No price configured for {$usage->model}.");

            $usage->cost = (
                ($usage->input_tokens - $usage->cached_tokens) * $rate['input']
                + $usage->cached_tokens * $rate['cached']
                + $usage->output_tokens * $rate['output']
            ) / 1_000_000;
        });
    }
}
```

Un modello senza prezzo lancia un'eccezione, il listener la segnala, e scopri che un provider di fallback ha risposto senza un prezzo configurato prima che te lo dica la fattura.

Quattro domande a cui questo risponde e a cui nient'altro risponderà:

- Quale agent costa di più?
- Quale utente o tenant costa di più?
- Il costo per richiesta sta crescendo nel tempo?
- La modifica al prompt della settimana scorsa ha reso le cose più economiche o più care?

### Le tre leve, riviste

La Sezione 1.4 le nominava. In produzione hanno questo aspetto:

**Meno iterazioni.** Descrizioni dei tool più affilate (5.4), meno tool agganciati (5.8), limiti di esecuzione più bassi (5.9). Leggi i trace per trovare gli agent che ciclano.

**Contesto più piccolo.** Sfoltimento aggressivo della cronologia (4.4), output dei tool compatto (19.1), meno chunk RAG, riassunti ai confini fra agent (16.3).

**Modello più economico per passo.** `AIProvider::driver('ollama')` sul classificatore, il default sullo scrittore (17.6).

### Caching

La leva con la maggiore forza e la più trascurata, perché una risposta in cache non costa nulla:

```php
class CachedClassifier
{
    public function classify(string $text): string
    {
        $key = 'classify:' . \hash('xxh128', $text);

        return Cache::remember(
            $key,
            now()->addDays(7),
            fn () => ClassifierAgent::make(workflowId: $key)
                ->structured(new UserMessage($text), Classification::class)
                ->label
        );
    }
}
```

La chiave di cache fa anche da thread dell'agent: un agent non gira senza uno, e una classificazione non ha nessuna conversazione a cui appartenere.

**Metti in cache i compiti quasi deterministici:** classificazione, estrazione da un documento fisso, embedding di testo invariato, traduzione di una stringa fissa.

**Non mettere in cache le risposte conversazionali.** La stessa domanda in una conversazione diversa merita una risposta diversa.

**Il caching degli embedding è la vittoria più grande nel RAG.** Il testo che non è cambiato non ha bisogno di un nuovo embedding — che è esattamente a cosa serviva la guardia `wasChanged('body')` della Sezione 20.2.

### Budget

```php
// config/neuron.php
'budgets' => [
    'per_user_daily'   => env('AI_BUDGET_USER_DAILY', 2.00),
    'per_tenant_daily' => env('AI_BUDGET_TENANT_DAILY', 50.00),
    'global_daily'     => env('AI_BUDGET_GLOBAL_DAILY', 500.00),
],
```

Tre livelli perché falliscono in modi diversi: un ciclo impazzito per un utente, un'integrazione mal configurata per un tenant, un bug che colpisce tutti. Il tetto globale è la tua ultima linea di difesa.

Una configurazione non ferma nulla. Il budget è il codice che legge quanto è stato speso e rifiuta il turno successivo:

```php
class Budget
{
    /** Call it before a turn starts: a refusal here stores nothing and spends nothing. */
    public function check(ThreadScope $scope): void
    {
        $today = AiUsage::query()->whereDate('created_at', today());

        $spent = [
            'per_user_daily'   => (clone $today)->where('user_id', $scope->userId)->sum('cost'),
            'per_tenant_daily' => (clone $today)->where('tenant_id', $scope->tenantId)->sum('cost'),
            'global_daily'     => (clone $today)->sum('cost'),
        ];

        foreach (config('neuron.budgets') as $tier => $limit) {
            abort_if($spent[$tier] >= $limit, 429, 'The daily AI budget is used up.');
        }
    }
}
```

Chiamalo dove inizia un turno, prima che l'agent venga associato — `$budget->check(ThreadScope::of($conversation->threadId()))` — e il browser riceve un 429 senza alcuna domanda salvata e senza alcun token speso. Ciò che un controllo prima del turno non può fare è fermare un ciclo dentro un turno già in corso: lo contengono i limiti di esecuzione della Sezione 5.9.

**Imposta anche un limite di spesa rigido presso il provider.** La Sezione 3.7 lo diceva e vale la pena ripeterlo: i budget a livello applicativo dipendono dal fatto che il tuo codice sia corretto. Il tetto del provider no.

### Punti chiave

- Registra token, modello e agent a ogni inferenza, e calcola il prezzo della riga quando la scrivi.
- Tre leve: meno iterazioni, contesto più piccolo, modello più economico per passo.
- Metti in cache i compiti deterministici e gli embedding; non le conversazioni.
- Tre livelli di budget, verificati prima di ogni turno, più un tetto rigido presso il provider.

## 23.2 Resilienza

### Rate limiting

I provider impongono i loro; tu dovresti imporre i tuoi per primo, così da ottenere un job in coda invece di una richiesta fallita:

```php
class RunAgent implements ShouldQueue
{
    public function middleware(): array
    {
        return [new RateLimited('anthropic')];
    }
}
```

```php
// AppServiceProvider::boot()
RateLimiter::for('anthropic', fn () => Limit::perMinute(50));
```

Oltre il limite, il middleware rilascia il job di nuovo in coda finché la finestra non si riapre: il turno è in ritardo, non perso. Non concatenare `->dontRelease()`. Con quel flag un job limitato non viene trattenuto ma scartato — Laravel lo elimina senza eseguirlo e senza errore, e il turno dell'utente è perso. Un rilascio ha un costo, di cui le impostazioni di ritentativo qui sotto devono tenere conto: Laravel lo conta come un tentativo.

### Timeout

Ogni provider parla HTTP attraverso l'astrazione client di NeuronAI, e il default è `CurlHttpClient`, che non richiede altro che ext-curl — Guzzle non è una dipendenza. Il suo timeout predefinito è di **300 secondi** per richiesta. Imposta il tuo deliberatamente, dove il provider viene costruito:

```php
protected function provider(): AIProviderInterface
{
    return new Anthropic(
        key: config('neuron.provider.anthropic.key'),
        model: config('neuron.provider.anthropic.model'),
        httpClient: new CurlHttpClient(timeout: 60.0, connectTimeout: 5.0),
    );
}
```

Un agent che fa cinque chiamate con il timeout predefinito può restare appeso per venticinque minuti prima di fallire, occupando un worker per tutto il tempo.

`timeout` limita l'intero trasferimento, non l'attesa del primo byte, e vale anche per una risposta in streaming: una risposta che sta ancora arrivando dopo sessanta secondi viene troncata a metà frase. Sessanta secondi vanno bene per le chiamate non in streaming. Dai un limite più alto a un agent che fa streaming di risposte lunghe, e tieni breve `connectTimeout` — è quello che si accorge di un provider fuori servizio.

Costruisci il provider nell'hook, come qui, invece di chiamare `setHttpClient()` su ciò che restituisce `AIProvider::driver()`: il manager consegna a ogni agent lo stesso oggetto provider (Sezione 17.6), quindi un client impostato su di esso cambia il timeout per tutti. Se ti serve un middleware di Guzzle — un gestore di retry, un proxy, la firma delle richieste — `GuzzleHttpClient` è disponibile come adapter opzionale una volta che richiedi tu stesso `guzzlehttp/guzzle`, e `CurlHttpClient` accetta `curlOptions` grezze per proxy e bundle di CA.

### Ritentativi, con l'avvertenza

```php
class RunAgent implements ShouldQueue
{
    use Queueable;

    public int $tries = 3;

    /** Longer than the longest turn, shorter than the queue's retry_after (360). */
    public int $timeout = 300;

    public array $backoff = [10, 60, 180];

    public function __construct(
        public string $threadId,
        public string $runId,
        public string $message,
    ) {}

    public function handle(SupportAgent $agent): void
    {
        $agent->for($this->threadId)->run(ExecutionRequest::start(
            new AgentStartEvent([new UserMessage($this->message)]),
            runId: $this->runId,
            recoverFailed: true,
        ));
    }
}
```

```php
RunAgent::dispatch($conversation->threadId(), (string) Str::uuid(), $request->input('message'));
```

**L'avvertenza conta più della configurazione.** Un ritentativo che fa ripartire il turno rispende soldi e, per via del non determinismo, può produrre un risultato diverso. Ritenta il fallimento del *trasporto*, non il *ragionamento*.

La distinzione in pratica:

- Rate limit o errore di connessione prima di qualunque lavoro → sicuro da ritentare
- Fallimento dopo tre chiamate a tool inclusa una scrittura → **non ritentare alla cieca**; potresti duplicare la scrittura

L'ID della run è ciò che rende sicuro un ritentativo in entrambi i casi. Lo conia il controller quando fa il dispatch, così ogni consegna del job nomina la stessa run, e il job avvia il turno con `ExecutionRequest::start()` perché `chat()` non può riservare un ID. La prima consegna avvia quella run. Una riconsegna — dopo un'eccezione, dopo un worker ucciso — la trova, e `recoverFailed: true` le fa terminare la run dall'ultimo step completato invece di ripartire da capo: la domanda non viene salvata due volte, un'inferenza già pagata non viene pagata di nuovo, e un tool che è già stato eseguito non viene eseguito di nuovo. Viene ripetuto solo lo step che era in corso, ed è per questo che un tool di scrittura ha ancora bisogno della chiave di idempotenza della Sezione 19.2.

Tre orologi devono essere in ordine perché tutto questo regga, e i default di Laravel ne sbagliano uno:

- **Il lease della run** — 600 secondi per default per un agent, `setLeaseTimeout()` — più lungo del singolo step più lungo, un'inferenza o un batch di tool. Una run viva non viene così mai scambiata per morta.
- **Il `$timeout` del job** — 300 — più lungo del turno più lungo. Laravel uccide un job che lo supera; la sua run resta `running` finché il lease non scade, e una consegna successiva la termina.
- **Il `retry_after` della queue** — 360 — più lungo di `$timeout`. Laravel include 90, e con quello un secondo worker prende il job mentre il primo sta ancora rispondendo: il turno gira due volte. Imposta `DB_QUEUE_RETRY_AFTER=360` in `.env`, oppure `REDIS_QUEUE_RETRY_AFTER` su una queue Redis.

Finché una run è ancora in lease a un worker morto, il motore rifiuta l'avvio con `RunInFlightException`. Un job completo la cattura e si rilascia fino a `$e->leaseExpiresAt` invece di spendere un tentativo; la skill `neuron-laravel-integration` dei maintainer stampa quel gestore sotto "Background Runs", e le run in coda dei Capitoli 21 e 22 seguono lo stesso schema.

Un'interazione da conoscere: i rilasci del rate limiter attingono agli stessi tre tentativi. Dove il limite è abbastanza stretto da rilasciare un job più di una volta, conta i fallimenti invece delle consegne — `retryUntil()` con `$maxExceptions = 3`, come fanno i job di indicizzazione della Sezione 20.2 — ed elimina `$tries`, che Laravel ignora non appena un job definisce `retryUntil()`.

### Fallback fra provider

Il ritorno più concreto dell'architettura a interfacce:

```php
class ResilientProviderFactory
{
    private const CHAIN = ['anthropic', 'openai', 'gemini'];

    public function make(): AIProviderInterface
    {
        foreach (self::CHAIN as $driver) {
            if (! $this->circuitOpen($driver)) {
                return AIProvider::driver($driver);
            }
        }

        throw new NoProviderAvailable('All configured providers are unavailable.');
    }

    private function circuitOpen(string $driver): bool
    {
        return Cache::get("circuit:{$driver}", 0) >= 5;
    }

    public function recordFailure(string $driver): void
    {
        // add() writes only when the key is missing: the first failure opens a five-minute window
        Cache::add("circuit:{$driver}", 0, now()->addMinutes(5));
        Cache::increment("circuit:{$driver}");
    }
}
```

Cinque fallimenti in cinque minuti tolgono un provider dalla catena, e quando il contatore scade viene riprovato. È l'`add()` a dare al contatore quella scadenza. `increment()` da solo non ne imposta mai una: a seconda del cache store, il contatore vive allora per sempre, e un provider che ha fallito cinque volte resta escluso finché qualcuno non svuota la cache, oppure — sullo store `database` che una nuova applicazione Laravel usa per default — non viene mai creato affatto, e il circuito non si apre mai.

**Due avvertenze, così che questo non sembri un pasto gratis:**

**La qualità varia fra i provider.** Un prompt messo a punto per un modello può comportarsi sensibilmente peggio su un altro. Il fallback ti tiene disponibile; non ti tiene ugualmente bravo. Esegui le tue eval (Capitolo 10) contro ogni provider della catena così da sapere verso che cosa stai degradando.

**Alcune funzionalità non sono portabili.** I tool di provider (5.12) semplicemente svaniscono. Se un agent dipende da uno di essi, non ha fallback.

### Degradare con garbo

A volte la risposta giusta non è un altro provider:

```php
try {
    return $this->agent->chat(new UserMessage($question))->getMessage()?->getContent() ?? '';
} catch (\Throwable $e) {
    \Log::error('Agent unavailable', ['exception' => $e]);

    return $this->fallbackSearch($question);   // plain keyword search over the KB
}
```

Il risultato di una ricerca per parole chiave batte una pagina di errore. Gli utenti notano i disservizi; raramente notano una risposta leggermente peggiore.

### Punti chiave

- Applica un rate limit prima che lo faccia il provider; metti in coda invece di fallire, e mai `dontRelease()`.
- Ritenta i fallimenti di trasporto, non il ragionamento: una run riservata con `recoverFailed: true` permette a una riconsegna di terminare il turno invece di ripeterlo.
- Tre orologi in ordine: lease sopra lo step più lungo, `$timeout` sopra il turno più lungo, `retry_after` sopra `$timeout`.
- Le catene di fallback ti tengono disponibile, non ugualmente bravo; fai le eval su ogni provider della catena.
- Degrada verso funzionalità non-AI invece che verso una pagina di errore.

## 23.3 Osservabilità in produzione

### Inspector, con il pacchetto Laravel

```bash
composer require inspector-apm/inspector-laravel "inspector-apm/inspector-php:^3.19"
```

```dotenv
INSPECTOR_INGESTION_KEY=...
```

Questo monitora le tue richieste HTTP e i tuoi job — e nessun agent. NeuronAI non dipende da Inspector e non aggancia nulla per default; i tutorial più vecchi che si fermano alla variabile d'ambiente descrivono una configurazione che non esiste più. La Sezione 10.2 spiega il meccanismo, e il motivo per cui il comando nomina un secondo pacchetto: il pacchetto Laravel accetta versioni di `inspector-apm/inspector-php` più vecchie di quelle che servono al subscriber, e dalla 3.18.1 alla 3.18.3 includono un subscriber scritto per un namespace di pre-release, che si sottoscrive senza lamentele e non registra nulla. In Laravel, sottoscrivi il listener dove vengono costruiti gli agent — il callback `afterResolving()` della Sezione 23.1 — e passagli l'istanza di Inspector che il pacchetto Laravel possiede già:

```php
use Inspector\Neuron\V4\InspectorSubscriber;
use NeuronAI\Observability\ObservabilityEvent;

$agent->subscribe(ObservabilityEvent::class, new InspectorSubscriber(app('inspector')));
```

Passare l'istanza dell'host è il senso del pacchetto Laravel. I segmenti dell'agent finiscono dentro la transaction che Inspector ha già aperto per la richiesta o per il job in coda, il che correla il trace dell'agent con le query, le chiamate HTTP e il job che gli stanno attorno — ciò che ti serve davvero quando diagnostichi un incidente. Senza, hai una linea temporale dell'agent che fluttua slegata dalla richiesta che l'ha prodotta.

I queue worker non hanno bisogno di nulla in più. Il subscriber fa il flush alla fine di una run solo quando ha aperto la transaction da sé, e lascia una transaction posseduta dall'host — un job monitorato dal pacchetto Laravel — all'host perché la chiuda.

Il guasto da tenere d'occhio è un agent a cui nessuno ha sottoscritto il subscriber: non produce alcun errore e nessun trace, e un worker è esattamente il posto dove nessuno se ne accorge. Sottoscrivilo nel service provider, mai nei punti di chiamata.

Inspector non è l'unico backend. La guida al monitoraggio dei maintainer documenta Neuron Cloud, che ha un proprio pacchetto Laravel, `neuron-core/neuron-cloud-laravel`: lo stesso tipo di listener, sottoscritto nello stesso posto. La Sezione 10.2 dice che cosa controllare prima di farci affidamento.

### Su che cosa mettere alert

Quattro segnali, e nessuno di essi è "si è verificata un'eccezione":

**Limiti di esecuzione dei tool superati.** La Sezione 5.9 diceva che è una diagnostica sul progetto dei tool. Un picco significa che una descrizione ha smesso di funzionare — spesso perché i dati sottostanti hanno cambiato forma.

**Punteggio di fedeltà in calo.** Dalla tua suite di eval (10.5), eseguita ogni notte. Un calo significa che la qualità del recupero è degradata, di solito perché i contenuti sono cambiati e l'indice non ha tenuto il passo.

**Costo per richiesta in crescita.** Cicli che si allungano, contesto che cresce, o una modifica al prompt che ha reso il modello più loquace.

**Arretrato di approvazioni in crescita.** Non è un problema di codice — è un problema di processo, e la tua dashboard lo farà emergere prima che qualcuno si lamenti.

### Che cosa loggare, e che cosa no

**Logga:** classe dell'agent, provider, modello, conteggi di token, durata, nomi dei tool, *forma* degli argomenti dei tool, esito, workflow ID, ID di utente e tenant.

**Non loggare per default:** prompt completi, risposte complete, *valori* degli argomenti dei tool, contenuto dei documenti recuperati.

La Sezione 3.7 faceva questo punto; merita di essere ribadito qui. I prompt contengono qualunque cosa gli utenti abbiano digitato — nomi, indirizzi, numeri d'ordine, occasionalmente dati di pagamento. Loggare i prompt completi su scala crea un problema di conformità molto più difficile da sbrogliare che da evitare.

Quando ti serve davvero il contenuto per il debug, mettilo dietro un flag esplicito con conservazione breve, e mai attivo per default.

### L'ID di correlazione

```php
Context::add([
    'workflow_id' => $this->workflowId,
    'tenant_id'   => $this->tenantId,
    'agent'       => static::class,
]);
```

Una richiesta agentica tocca una richiesta HTTP, diversi job in coda, diverse chiamate al provider e possibilmente una decisione umana giorni dopo. Senza un ID di correlazione, ricostruire ciò che è successo significa tirare a indovinare dai timestamp. Usa `Context`, non `Log::withContext()`: Laravel scrive i dati di contesto in ogni record di log e li porta nei job inviati in seguito, mentre `withContext()` resta nel processo che l'ha chiamato.

### Punti chiave

- Richiedi `inspector-laravel` e `inspector-php` a `^3.19`, e sottoscrivi `InspectorSubscriber` su ogni agent — per default non viene monitorato nulla.
- Passa l'istanza di Inspector del pacchetto Laravel, così i segmenti dell'agent si uniscono alla transaction della richiesta o del job.
- Metti alert su limiti di esecuzione, fedeltà, costo per richiesta e arretrato di approvazioni.
- Logga forme e metadati; non il contenuto dei prompt.
- Correla tutto tramite il workflow ID, in `Context` così che segua il lavoro nei job in coda.

## 23.4 Testing e CI

### I tre livelli

**Livello 1 — Test unitari. Veloci, gratuiti, deterministici, eseguiti a ogni commit.**

I tool sono comuni oggetti invocabili (Sezione 5.3):

```php
public function test_it_scopes_orders_to_the_tenant(): void
{
    Order::factory()->for($this->tenantA)->create(['number' => 'A-001', 'status' => 'shipped']);
    Order::factory()->for($this->tenantB)->create(['number' => 'B-001', 'status' => 'shipped']);

    $result = (string) (new SearchOrdersTool($this->tenantA->id))(status: 'shipped');

    $this->assertStringContainsString('A-001', $result);
    $this->assertStringNotContainsString('B-001', $result);
}
```

Nessun LLM. Nessuna rete. Entrambi gli ordini sono `shipped`, quindi il filtro sullo stato li lascia passare entrambi e solo l'ambito del tenant può tenere fuori `B-001`; la prima asserzione dimostra che la ricerca ha trovato qualcosa. Un test che passa su un risultato vuoto non protegge nulla. È qui che dovrebbe vivere la maggior parte della tua logica legata agli agent, ed è il motivo per cui la Sezione 5.3 argomentava a favore delle classi tool.

**Livello 2 — Test di integrazione con un provider finto.**

```php
$provider = new FakeAIProvider(new AssistantMessage('Your order ships tomorrow.'));

$this->app->instance(
    SupportAgent::class,
    $this->app->make(SupportAgent::class)->setAiProvider($provider),
);

$this->actingAs($user)
    ->postJson("/conversations/{$conversation->id}/messages", ['message' => 'Where is my order?'])
    ->assertOk();

$provider->assertCallCount(1);
```

Testa il tuo controller, la tua validazione, la tua autorizzazione, la tua serializzazione — e l'agent reale, con le sue istruzioni e i suoi tool reali. Viene sostituito solo il modello, attraverso il punto di aggancio della Sezione 18.1: il container consegna un agent il cui provider è il finto, e la copia creata da `for()` lo condivide.

`FakeAIProvider` implementa la stessa interfaccia di un provider reale: metti in coda le risposte che deve restituire, compresi i messaggi di tool call per guidare il ciclo dell'agent, e verifica che cosa gli è stato inviato con `assertSent()`. Il framework offre lo stesso schema per gli altri punti di aggancio — `FakeEmbeddingsProvider`, `FakeVectorStore`, `FakeChannel` per l'output in streaming — così un endpoint RAG o uno stream in coda si possono testare allo stesso modo.

**Livello 3 — Eval. Lente, costano soldi, misurano la qualità (Capitolo 10).**

```bash
php artisan neuron:evaluate --env=evaluation
```

Non `vendor/bin/neuron evaluation`, il comando del Capitolo 10: non avvia Laravel, quindi un evaluator che tocca un modello, una facade o il container fallisce a ogni elemento. `neuron:evaluate` è un comando Artisan tutto tuo che esegue la stessa CLI di evaluation dentro l'applicazione avviata, con il container che costruisce gli evaluator. È una classe breve, che i maintainer stampano nella skill `neuron-laravel-integration` (`references/evaluation.md`): creala con `php artisan make:command NeuronEvaluate` e sostituisci la classe. Le eval eseguono i tool reali — approvare un rimborso rimborsa quell'ordine — quindi hanno un database tutto loro. `--env=evaluation` seleziona `.env.evaluation`, il comando si rifiuta di partire quando quel file non è stato caricato, e un seeder ricostruisce i dati che i dataset nominano prima di ogni run.

### Configurazione della CI

```yaml
jobs:
  test:
    steps:
      - run: composer install --prefer-dist --no-progress
      - run: vendor/bin/phpunit --testsuite=Unit,Feature
      - run: vendor/bin/phpstan analyse

  evals:
    if: github.event_name == 'schedule' || contains(github.event.head_commit.message, '[evals]')
    steps:
      - run: php artisan migrate:fresh --seed --seeder=EvaluationSeeder --env=evaluation
      - run: |
          php artisan neuron:evaluate --env=evaluation --concurrency=5 || true
          php -r '$r = json_decode(file_get_contents("storage/logs/evaluation.json"), true, 512, JSON_THROW_ON_ERROR); exit($r["success_rate"] >= 0.95 ? 0 : 1);'
        env:
          ANTHROPIC_KEY: ${{ secrets.ANTHROPIC_KEY }}
```

Tre regole dalla Sezione 10.6, ribadite perché è facile sbagliarle:

**Non subordinare ogni PR all'intera suite di eval.** Costa soldi ed è lenta. Ogni notte, più su richiesta con un tag nel commit.

**Non fallire su un singolo elemento.** Imposta una soglia sul tasso di successo. Su un sistema probabilistico un tasso di superamento del 95 % è una build sana, e trattare un elemento instabile come un fallimento insegna al team a ignorare del tutto il segnale. Il comando esce con un codice diverso da zero a ogni elemento fallito e non ha un flag per la soglia, quindi lo step ignora il suo codice d'uscita e legge `success_rate` dal report JSON, come faceva la Sezione 10.6; qui `evaluation.php` scrive quel report in `storage/logs/evaluation.json`.

**Tieni le chiavi API fuori dai fork.** Le eval sulle PR in un repository pubblico sono un modo per donare il tuo budget a degli sconosciuti.

### I test di sicurezza che devono bloccare i deploy

Due dalla Parte V, entrambi abbastanza deterministici da meritare fiducia:

```text
public function test_tenant_a_history_never_reaches_tenant_b(): void;      // Section 18.3
public function test_customer_cannot_retrieve_internal_articles(): void;   // Section 20.3
```

Appartengono al livello 1 o 2, girano a ogni commit e bloccano il merge. Eseguili nella forma che verifica che cosa è arrivato al modello, attraverso un fake provider: nessun modello viene chiamato, quindi il risultato è lo stesso a ogni esecuzione. Sono fra i pochi test attinenti all'AI che siano al tempo stesso affidabili e conseguenti.

### Punti chiave

- Tre livelli: unitari (ogni commit), integrazione con i fake (ogni commit), eval (ogni notte).
- I tool sono testabili senza un LLM — metti lì la logica.
- Soglia sul tasso di successo, non superato/fallito per singolo elemento.
- L'isolamento fra tenant e il recupero filtrato per permessi bloccano ogni deploy.

## 23.5 Sicurezza e privacy

### Il modello a strati, assemblato

| Strato | Meccanismo | Sezione |
|---|---|---|
| Capacità | Registra solo i tool che questo utente può usare | 5.1 |
| Visibilità | `visible()` dalle policy | 5.10, 19.3 |
| Autorizzazione | `Gate::forUser()` dentro il tool | 19.3 |
| Approvazione | `approvalPolicy()` / `requireApproval()` sui tool con conseguenze | 15.5, 22.5 |
| Ambito dei dati | Filtri di tenant su tool e recupero | 18.3, 20.3 |
| Privilegio | Credenziali di database in sola lettura | 19.3 |
| Audit | Una riga per ogni chiamata a un tool conseguente | 19.3 |

**Ogni strato è indipendente.** Un bug in uno non sconfigge gli altri — che è tutto il senso della difesa in profondità, e la risposta a "non basta la visibilità?".

### Prompt injection, ancora una volta

Il principio della Sezione 19.3, che è la tesi di sicurezza dell'intero libro:

> Non cercare di convincere il modello a non fare qualcosa che ha la capacità di fare. Togli la capacità.

Le istruzioni competono con il testo iniettato e a volte perdono. Un tool assente non può essere invocato da nessun prompt, per quanto astuto.

Il testo non fidato entra da più posti di quanti le persone si aspettino: messaggi degli utenti, descrizioni di prodotti, ticket di supporto, documenti caricati, contenuti recuperati dal RAG, risposte di API di terze parti e output di tool MCP (9.4). Trattalo tutto come influenzabile da un attaccante.

### Flusso dei dati

Tre domande a cui rispondere per iscritto prima del lancio:

**Che cosa lascia la tua infrastruttura?** Ogni prompt va al provider. Questo include i documenti recuperati e i risultati dei tool. Se l'indirizzo di un cliente compare nel risultato di un tool, è andato al provider.

**Dove va?** Le regioni dei provider differiscono, e alcuni offrono elaborazione solo UE o in-regione. Per i clienti europei questo è spesso un requisito contrattuale più che una preferenza.

**Che cosa viene conservato?** I provider pubblicano politiche di conservazione; gli accordi enterprise spesso includono opzioni a conservazione zero. Leggile e metti per iscritto ciò che hai trovato.

### Punti di contatto con il GDPR

Cinque pratici, esposti come requisiti ingegneristici:

**Base giuridica.** Mandare dati personali a un responsabile del trattamento terzo ne richiede una. È una determinazione legale, non ingegneristica — coinvolgi un legale invece di deciderlo in fase di pianificazione dello sprint.

**Accordo sul trattamento dei dati.** Con ogni provider che usi.

**Diritto alla cancellazione.** Un utente chiede di essere cancellato. La sua cronologia chat è nella tua tabella `chat_messages` — cancellabile, comprese le righe archiviate (Sezione 18.2). Altri due posti custodiscono le sue parole. Una run in pausa per un'approvazione conserva il suo stato serializzato — la domanda, gli argomenti del tool, qualunque testo recuperato — in `workflow_store` finché non viene chiusa; `resetConversation()` sull'agent associato scarta quella run insieme alla cronologia del thread. La memoria a lungo termine (Sezione 4.5) vive in uno store che `resetConversation()` non tocca, quindi cancella separatamente quei documenti. I suoi dati dentro i log di un provider sono soggetti alla politica di conservazione di quel provider, ed ecco perché la conservazione zero conta.

**Diritto di accesso.** La cronologia chat e qualunque memoria a lungo termine (Sezione 4.5) sono dati personali che l'utente può richiedere.

**Processo decisionale automatizzato.** Se un agent prende una decisione con effetti giuridici o similmente significativi su qualcuno, l'articolo 22 del GDPR è rilevante. È un argomento forte a favore dell'human-in-the-loop sulle azioni conseguenti — il Capitolo 15 è una funzionalità di conformità oltre che di sicurezza.

Niente di tutto questo è consulenza legale; è l'elenco di domande da portare a chi la fornisce.

### La traccia di audit

```php
Schema::create('agent_actions', function (Blueprint $table) {
    $table->id();
    $table->string('thread_id');
    $table->string('call_id');
    $table->foreignId('tenant_id')->constrained();
    $table->foreignId('user_id')->constrained();
    $table->string('tool');
    $table->json('arguments');
    $table->string('outcome');
    $table->text('result')->nullable();
    $table->foreignId('approved_by')->nullable()->constrained('users');
    $table->timestamps();
    $table->unique(['thread_id', 'call_id']);
});
```

Risponde alla domanda che prima o poi arriva: *"perché il sistema ha rimborsato quel cliente?"*

Questa è la tabella in cui scrive il listener di `ToolCalled` della Sezione 19.3, una riga per chiamata a un tool, identificata dal thread e dal call ID così che una chiamata riprodotta aggiorna la sua riga invece di aggiungerne una. Senza, hai dei log, un trace che potrebbe essere scaduto e un'alzata di spalle. Con, hai una riga che nomina l'utente, il tool, gli argomenti, l'esito, chi ha approvato e l'ora. In un ambiente regolamentato è la differenza fra distribuibile e non distribuibile.

### Punti chiave

- Sette strati indipendenti; un bug in uno non sconfigge gli altri.
- Togli la capacità invece di istruire contro di essa.
- Metti per iscritto che cosa esce, dove va e che cosa viene conservato.
- L'human-in-the-loop è una funzionalità di conformità ai sensi dell'articolo 22, non solo di sicurezza.
- Traccia in audit ogni azione conseguente su una tabella interrogabile.

## 23.6 La checklist di deploy

### Configurazione

- [ ] Versioni dei modelli **fissate esplicitamente**, non alias mobili (1.5)
- [ ] Provider impostato per ambiente; modello di embedding **identico ovunque** (12.4, 17.2)
- [ ] Context window ricavata dal provider configurato, non scritta a codice (4.4)
- [ ] Limite di spesa rigido impostato presso il provider (3.7)
- [ ] Chiavi API separate per ambiente
- [ ] Scansione dei segreti in CI

### Agent e tool

- [ ] Ogni tool di scrittura: `setMaxRuns(1)`, guardia di idempotenza, transazione (5.9, 19.2)
- [ ] Ogni tool: insieme di risultati limitato, selezione esplicita delle colonne, output compatto (19.1)
- [ ] Ogni tool: una frase esplicita per il caso vuoto (5.9)
- [ ] Visibilità dei tool calcolata dalle policy dell'attore (5.10, 19.3)
- [ ] `Gate::forUser()` dentro i tool che toccano record specifici (19.3)
- [ ] Gestore d'errore che restituisce istruzioni, non stack trace (5.11)
- [ ] Toolkit filtrati con `only()`, mai con `exclude()` (5.8)

### Dati

- [ ] Filtro di tenant restituito da `retrievalScope()`, mai aggiunto nel punto di chiamata né sostituito con `setRetrievalScope()` (20.1)
- [ ] Filtri di permesso applicati **al recupero**, mai dopo (20.3)
- [ ] `sourceName` stabile — ID dei record, mai i titoli (12.6, 20.2)
- [ ] `indexed_at` tracciato; un alert sullo scarto configurato (20.2)
- [ ] Credenziali di database in sola lettura per le query degli agent (19.3)
- [ ] La conservazione copre `workflow_store` oltre a `chat_messages`: una run sospesa vi conserva il suo stato serializzato finché non viene chiusa (18.4, 23.5)

### Workflow

- [ ] `DatabasePersistence` — o `EloquentPersistence` su una tabella tua, o il backend Redis — per qualunque cosa sia interrompibile, compresi gli agent con approvazione (18.4, 22.5)
- [ ] Ogni chiamata a un LLM che precede un'interruzione avvolta in `memoize()` (15.5)
- [ ] Job di ripresa protetti da fence con `expectedRunId` ed `expectedExecutionAttempt` (22.3)
- [ ] `lockForUpdate()` alla risoluzione delle approvazioni (22.3)
- [ ] `expiresAt` sulla richiesta; ripresa senza input schedulata (22.4)
- [ ] Timeout del lease superiore allo step silenzioso più lungo (22.4)
- [ ] Richieste di interruzione piccole, piatte e versionate; nuove proprietà dichiarate con valori di default (22.4)
- [ ] Run di workflow obsolete scartate con `abandon()`, mai cancellate a mano; una run di agent morta viene terminata, non abbandonata (18.4, 22.4)
- [ ] Ogni endpoint che avvia un turno chiama prima `recoverFailedTurn()` (18.4)

### Operatività

- [ ] `InspectorSubscriber` sottoscritto su ogni agent e workflow, dove vengono costruiti (10.2, 23.3)
- [ ] Uso dei token registrato per inferenza (23.1)
- [ ] Budget: per utente, per tenant, globale, verificati prima di ogni turno (23.1)
- [ ] Rate limit configurati prima di quelli del provider (23.2)
- [ ] I turni in coda avviano una run riservata con `recoverFailed: true`, così una riconsegna termina il turno invece di ripeterlo (23.2)
- [ ] Tre orologi in ordine: lease sopra lo step più lungo, `$timeout` del job sopra il turno più lungo, `retry_after` della queue sopra `$timeout` — Laravel include 90 (23.2)
- [ ] Timeout impostati su PHP, FPM, proxy e client HTTP del provider (21.2, 23.2)
- [ ] Streaming verificato dall'inizio alla fine con `curl -N` attraverso l'intero stack (21.2)
- [ ] Canali di broadcast autorizzati per tenant; il browser si iscrive prima che la run parta (21.5)

### Qualità e sicurezza

- [ ] Suite di eval con un dataset costruito da domande reali (10.4)
- [ ] `FaithfulnessJudge` su ogni agent RAG (10.5)
- [ ] Test di isolamento fra tenant che blocca i deploy (18.3)
- [ ] Test di recupero filtrato per permessi che blocca i deploy (20.3)
- [ ] Tabella di audit popolata da ogni tool conseguente (19.3, 23.5)
- [ ] Contenuto dei prompt **non** loggato per default (3.7, 23.3)
- [ ] Accordi sul trattamento dei dati in essere; conservazione compresa (23.5)

### Le cinque domande a cui rispondere ad alta voce

Prima del lancio, devi saper rispondere a queste senza andare a cercare nulla:

1. **Quanto costa questo agent per richiesta, e a quale volume questo diventa un problema?**
2. **Qual è la cosa peggiore che può fare, e che cosa lo ferma?**
3. **Come farei a scoprire che cosa ha fatto, fra tre settimane?**
4. **Che cosa succede quando il provider è giù?**
5. **Quali dati lasciano la mia infrastruttura, e dove vanno?**

Se una qualunque risposta è un'alzata di spalle, quello è il prossimo pezzo di lavoro.

### Chiusura della Parte V

Ventidue capitoli fa il primo disegnava una scala a quattro pioli e chiedeva *chi decide che cosa succede dopo*. Tutto ciò che è venuto dopo è stato il macchinario necessario per lasciare che un modello rispondesse a quella domanda in sicurezza: tool per dargli le mani, struttura per rendere usabile il suo output, recupero per dargli conoscenza, workflow per dargli forma, interruzione per tenere un essere umano nella decisione, e osservabilità per scoprire che cosa abbia effettivamente fatto.

La seconda domanda di quell'elenco è quella con cui lasciarti:

> **Qual è la cosa peggiore che il tuo agent può fare, e che cosa lo ferma?**

Se sai rispondere a questa su un sistema che hai costruito, hai capito questo libro.

### Punti chiave

- Lavora la checklist sezione per sezione; ogni voce riporta a un capitolo.
- Le cinque domande sono il vero esame.
- Se una risposta è un'alzata di spalle, quello è il prossimo compito.
