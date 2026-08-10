# Capitolo 18 — Agent come cittadini di prima classe

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

Questo capitolo è concettuale e non ha codice a sé stante, ma il repository di accompagnamento [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) contiene le versioni eseguibili di tutto ciò che il libro costruisce.
:::

## 18.1 Agent nel container

### Il problema di `::make()` dappertutto

```php
class SupportController extends Controller
{
    public function ask(Request $request)
    {
        return SupportAgent::make()
            ->chat(new UserMessage($request->input('message')))
            ->getMessage()
            ->getContent();
    }
}
```

Funziona. Ma ora il controller costruisce l'agent, il che significa che non puoi sostituirlo nei test, non puoi variarlo per tenant e non puoi configurarlo in un posto solo.

### Iniezione dal costruttore

```php
class SupportAgent extends Agent
{
    public function __construct(
        private readonly OrderRepository $orders,
        private readonly User $user,
    ) {
        parent::__construct();
    }

    protected function provider(): AIProviderInterface
    {
        return AIProvider::driver();
    }

    protected function tools(): array
    {
        return [
            new SearchOrdersTool($this->orders),
            new GetOrderStatusTool($this->orders),
        ];
    }
}
```

Ricorda `parent::__construct()` (Sezione 4.3) e che un costruttore personalizzato significa `new`, non `::make()`.

### Il binding

```php
// AppServiceProvider::register()

$this->app->bind(SupportAgent::class, function ($app) {
    return new SupportAgent(
        orders: $app->make(OrderRepository::class),
        user: $app->make('auth')->user(),
    );
});
```

```php
class SupportController extends Controller
{
    public function __construct(
        private readonly SupportAgent $agent,
    ) {}

    public function ask(Request $request)
    {
        return $this->agent
            ->chat(new UserMessage($request->input('message')))
            ->getMessage()
            ->getContent();
    }
}
```

Il controller chiede un agent e ne riceve uno, configurato correttamente per l'utente corrente.

### Perché vale la cerimonia

**Testabilità.** Sostituisci il binding in un test e il controller parla con un fake. È il problema della Sezione 1.5 — non puoi fare asserzioni sull'output del modello, quindi il confine che *puoi* testare è la gestione di un agent da parte del controller, e l'iniezione delle dipendenze è ciò che fa esistere quel confine.

```php
$this->app->bind(SupportAgent::class, fn () => new FakeSupportAgent());

$this->post('/support/ask', ['message' => 'Where is my order?'])
     ->assertOk();
```

**Configurazione per utente.** Il binding risolve l'utente corrente, quindi la visibilità dei tool (Sezione 5.10) viene calcolata per richiesta senza che il controller lo sappia.

**Un posto solo da cambiare.** Provider, tool, cronologia, istruzioni — tutto deciso nel binding.

**Si legge come Laravel.** Il che conta per l'adozione. Un agent che arriva per iniezione è un servizio come un altro, e un team sa già come ragionare sui servizi.

### Binding con scope

Per i runtime a lunga vita:

```php
$this->app->scoped(SupportAgent::class, function ($app) {
    return new SupportAgent(/* ... */);
});
```

`scoped()` dà un'istanza per richiesta e si azzera fra una richiesta e l'altra sotto Octane.

::: {.callout .callout-warning}
[Mai `singleton()` per un agent che porta contesto utente]{.callout-title}

Sotto Octane quell'istanza persiste fra le richieste, e l'utente B eredita i tool e la cronologia dell'utente A. È la stessa classe di bug che la semantica di copia della facade previene nella Sezione 17.5 — solo che qui è responsabilità tua, e sotto PHP-FPM non si manifesterà affatto.
:::

### Punti chiave

- Iniezione dal costruttore, poi il binding in un service provider.
- Testabilità, configurazione per utente, punto di modifica unico.
- `scoped()` e non `singleton()` per qualunque cosa porti contesto utente.

## 18.2 EloquentChatHistory

### Pubblica e migra

```bash
php artisan vendor:publish --tag=neuron-migrations
php artisan migrate --path=/database/migrations/neuron
```

La migration atterra in `database/migrations/neuron` — una sottocartella, ed è per questo che serve il flag `--path`. Esegui entrambi i comandi insieme; il secondo è facile da dimenticare e il fallimento è silenzioso.

### Usala

```php
namespace App\Neuron;

use NeuronAI\Agent\Agent;
use NeuronAI\Chat\History\ChatHistoryInterface;
use NeuronAI\Chat\History\EloquentChatHistory;
use NeuronAI\Laravel\Models\ChatMessage;

class MyAgent extends Agent
{
    protected function chatHistory(): ChatHistoryInterface
    {
        return new EloquentChatHistory(
            threadId: 'THREAD_ID',
            modelClass: ChatMessage::class,
            contextWindow: 100000
        );
    }
}
```

`NeuronAI\Laravel\Models\ChatMessage` viene fornito con il pacchetto.

::: {.callout .callout-warning}
[Ortografia]{.callout-title}

La documentazione scrive `ElquentChatHistory` nella prosa e ancora la sezione a `#eloquentchathisotry`. La classe è `EloquentChatHistory`. Appendice A, punto 42 — innocuo una volta che lo sai, e venti minuti sprecati se stai cercando la versione sbagliata.
:::

### Rendere reale `thread_id`

`'THREAD_ID'` è un segnaposto. In pratica è il confine di isolamento, e sbagliarlo è una fuga di dati:

```php
class SupportAgent extends Agent
{
    public function __construct(
        private readonly string $threadId,
    ) {
        parent::__construct();
    }

    protected function chatHistory(): ChatHistoryInterface
    {
        return new EloquentChatHistory(
            threadId: $this->threadId,
            modelClass: ChatMessage::class,
            contextWindow: ProviderContext::window(),
        );
    }
}
```

```php
$this->app->bind(SupportAgent::class, function ($app) {
    $conversation = $app->make(ConversationResolver::class)->current();

    return new SupportAgent(threadId: "conv:{$conversation->id}");
});
```

**Non ricavare mai il thread ID dall'input dell'utente.** Un parametro di richiesta che diventa un thread ID significa che chiunque può leggere la conversazione di chiunque cambiando un numero. Ricavalo lato server da una risorsa autenticata e autorizzata.

È l'errore di sicurezza più probabile di questo capitolo.

### La context window, per provider

La Sezione 4.4 diceva di ricavarla dal modello, mai di scriverla a codice per l'intero progetto. In Laravel:

```php
// config/neuron.php
'context_windows' => [
    'anthropic' => 185_000,
    'openai'    => 118_000,
    'gemini'    => 920_000,
    'ollama'    => 29_000,
],
```

```php
contextWindow: config('neuron.context_windows.' . config('neuron.default'), 29_000),
```

Cambia provider per ambiente e il trimmer segue. Scrivi 100.000 a codice e chi esegue Ollama in locale incapperà in errori di contesto che in produzione non compaiono mai.

### Estendere il modello

Il `ChatMessage` del pacchetto è un punto di partenza. Un'applicazione reale di solito vuole:

- Una chiave esterna verso `users`
- Soft delete per la politica di conservazione
- Un indice su `thread_id` più un timestamp
- Una colonna tenant

Estendi il modello e passa la tua classe come `modelClass`. È anche qui che vive il GDPR: le conversazioni contengono qualunque cosa gli utenti abbiano digitato, il che in un contesto di supporto significa dati personali. Cancellazione, esportazione e conservazione sono requisiti di prodotto, non ripensamenti — l'avvertimento sul logging della Sezione 3.7, reso concreto.

### Punti chiave

- Pubblica e migra con `--path=/database/migrations/neuron`.
- `thread_id` è il confine di isolamento — ricavalo lato server, mai dall'input.
- Ricava `contextWindow` dal provider configurato.
- Estendi `ChatMessage` per chiavi esterne, multi-tenancy e conservazione.

## 18.3 Isolamento multi-tenant

### I quattro punti di fuga

Un sistema agentico in un'applicazione multi-tenant ha quattro posti in cui i dati dei tenant possono attraversarsi:

1. **Cronologia della chat** — `thread_id`
2. **Vector store** — filtri sui metadati (Sezione 12.6)
3. **Tool** — i dati che interrogano
4. **Persistenza dei workflow** — l'ID di workflow

Sbagliane uno solo e hai una violazione. Tieni l'elenco in un posto in cui lo vedrai durante la code review.

### Un agent consapevole del tenant

```php
namespace App\Neuron\Agents;

use App\Models\Tenant;
use NeuronAI\Agent\Agent;
use NeuronAI\Chat\History\ChatHistoryInterface;
use NeuronAI\Chat\History\EloquentChatHistory;
use NeuronAI\Laravel\Facades\AIProvider;
use NeuronAI\Laravel\Models\ChatMessage;
use NeuronAI\Providers\AIProviderInterface;

class TenantSupportAgent extends Agent
{
    public function __construct(
        private readonly Tenant $tenant,
        private readonly int $conversationId,
    ) {
        parent::__construct();
    }

    protected function provider(): AIProviderInterface
    {
        return AIProvider::driver();
    }

    protected function chatHistory(): ChatHistoryInterface
    {
        return new EloquentChatHistory(
            threadId: "t{$this->tenant->id}:c{$this->conversationId}",
            modelClass: ChatMessage::class,
            contextWindow: config('neuron.context_window'),
        );
    }

    protected function tools(): array
    {
        return [
            // The tool receives the tenant — it cannot query outside it
            new SearchOrdersTool($this->tenant),
        ];
    }
}
```

### Il principio

**Delimita alla costruzione, non al momento della query.**

Il tool riceve un `Tenant` e costruisce le sue query a partire da quello. Non esiste un percorso di codice in cui un tool interroga senza il vincolo di tenant, perché non ha alcun modo di farlo.

Confronta con l'alternativa — un tool che legge il tenant corrente da una variabile globale o da una facade dentro `__invoke()`. Funziona finché qualcosa non gira fuori da una richiesta: un job in coda, un comando schedulato, un workflow ripreso. Allora la globale è vuota o, peggio, contiene il tenant sbagliato.

**I sistemi agentici girano fuori dal ciclo della richiesta più spesso del normale codice applicativo.** Queue worker (Sezione 16.4), workflow ripresi (Sezione 15.4), ingestione schedulata (Capitolo 20). Il contesto di tenant ambientale è inaffidabile in tutti e tre i casi. Passalo esplicitamente.

Quell'argomento si generalizza ben oltre NeuronAI.

### Gli ID di workflow

```php
$workflowId = "t{$tenant->id}:refund:{$order->id}";
```

Con prefisso di tenant, così che un workflow ripreso non possa essere confuso con quello di un altro tenant, e così che tu possa interrogare le interruzioni pendenti per tenant.

### Testare l'isolamento

Vale la pena scriverlo come test vero:

```php
public function test_tenant_a_cannot_see_tenant_b_conversation(): void
{
    $agentA = new TenantSupportAgent($tenantA, $conversationId);
    $agentA->chat(new UserMessage('My secret code is ALPHA'));

    $agentB = new TenantSupportAgent($tenantB, $conversationId);
    $reply = $agentB->chat(new UserMessage('What is my secret code?'))->getMessage();

    $this->assertStringNotContainsString('ALPHA', $reply->getContent());
}
```

Nota l'allestimento deliberatamente ostile: lo *stesso* ID di conversazione per entrambi i tenant. Se manca il prefisso di tenant, questo test fallisce — che è esattamente ciò che vuoi che catturi.

### Punti chiave

- Quattro punti di fuga: cronologia, vector store, tool, persistenza dei workflow.
- Delimita alla costruzione; non leggere contesto ambientale dentro i tool.
- Il codice agentico gira spesso fuori dal ciclo della richiesta — lì le globali sono inaffidabili.
- Scrivi un test di isolamento con un identificatore che collide.

## 18.4 Persistenza dei workflow con Eloquent

### L'allestimento

```php
use NeuronAI\Laravel\Models\WorkflowInterrupt;
use NeuronAI\Workflow\Persistence\EloquentPersistence;

$workflow = new WorkflowAgent(
    persistence: new EloquentPersistence(WorkflowInterrupt::class)
);
```

Il pacchetto include il model `WorkflowInterrupt`; la migration arriva con `--tag=neuron-migrations` insieme alla tabella della cronologia chat.

::: {.callout .callout-warning}
[`new` mancante nel README]{.callout-title}

L'esempio pubblicato recita `$workflow = WorkflowAgent(persistence: ...)`. Un refuso, ma di quelli che producono un confuso errore "undefined function" invece di qualcosa che indichi la causa. Appendice A, punto 41.
:::

### Perché Eloquent invece dei file

La Sezione 15.4 offriva `FilePersistence` e `DatabasePersistence`. In Laravel, la persistenza Eloquent ti dà:

**Sicurezza su più server.** Qualunque worker può riprendere qualunque workflow. La persistenza su file su disco locale significa che la ripresa deve atterrare sulla stessa macchina — cosa che dietro un load balancer è un lancio di monetina.

**Interrogabilità.** Le approvazioni pendenti diventano un elenco che puoi renderizzare:

```php
$pending = WorkflowInterrupt::query()
    ->where('updated_at', '<', now()->subHours(24))
    ->get();
```

Report sulle approvazioni ferme, dashboard per tenant, job di escalation — tutto ordinario Eloquent.

**Integrazione transazionale.** L'interruzione viene scritta nello stesso database dei tuoi dati di dominio, quindi una ripresa può essere atomica con il record di business che tocca.

**Backup.** I workflow in volo vengono salvati nei backup insieme a tutto il resto, invece di vivere in una directory che nessuno si ricorda di includere.

### La schermata delle approvazioni pendenti

Il pattern che questo sblocca, e quello che il Capitolo 22 costruisce:

```php
class ApprovalsController extends Controller
{
    public function index(Request $request)
    {
        $pending = WorkflowInterrupt::query()
            ->where('tenant_id', $request->user()->tenant_id)
            ->latest()
            ->paginate();

        return view('approvals.index', compact('pending'));
    }
}
```

Poiché le interruzioni sono righe, "l'AI sta aspettando un essere umano" diventa una comune pagina indice con una comune autorizzazione. È il momento in cui l'human-in-the-loop smette di essere un'esotica funzionalità AI e diventa normale sviluppo applicativo — che è precisamente ciò che rende il pattern distribuibile.

### Promemoria operativi dalla Sezione 15.4

Le quattro domande valgono ancora, ora con risposte Laravel:

- **Notifica** → invia una `Notification` nel blocco catch
- **Timeout** → un comando schedulato su `updated_at`
- **Doppia ripresa** → `lockForUpdate()` e una colonna di stato
- **Compatibilità con i deploy** → tieni le richieste di interruzione piccole e piatte; il payload serializzato contiene le tue classi

### Punti chiave

- `EloquentPersistence(WorkflowInterrupt::class)` con il model fornito.
- Sicuro su più server, interrogabile, transazionale, incluso nei backup.
- Le approvazioni pendenti diventano una comune pagina indice.
- Le quattro domande operative ricevono comuni risposte Laravel.

## Laboratorio 12 — Chat persistente multi-thread

**Copre:** binding nel container, `EloquentChatHistory`, isolamento dei thread, context window.

### Obiettivo

Un utente autenticato può tenere diverse conversazioni indipendenti con lo stesso agent, ciascuna persistita, ciascuna isolata, ciascuna riprendibile dopo un deploy completo.

### Requisiti

1. **Una tabella `conversations`** posseduta dagli utenti, con un titolo e timestamp. Un utente può averne molte.
2. **L'agent si risolve dal container**, con il binding che porta la conversazione corrente, mai costruito in un controller.
3. **Il thread ID è ricavato lato server** dall'utente autenticato e dal record della conversazione — mai da un parametro di richiesta. Dimostralo: prova a leggere la conversazione di un altro utente per ID e ottieni un 403 dalla tua policy, non una risposta dall'agent.
4. **La context window viene dalla configurazione**, indicizzata sul provider configurato, come nella Sezione 18.2.
5. **Estendi `ChatMessage`** con una chiave esterna verso `conversations` e un soft delete.

### Criteri di accettazione

- Due conversazioni dello stesso utente non vedono i messaggi l'una dell'altra.
- Due utenti con ID di conversazione consecutivi non possono raggiungere i thread l'uno dell'altro — verificalo con un test di autorizzazione, non a occhio.
- Riavviare il server applicativo non perde nulla.
- Passare `NEURON_AI_PROVIDER` da `anthropic` a `ollama` cambia la context window del trimmer senza modifiche al codice. Logga il valore configurato per dimostrarlo.
- Cancellare una conversazione fa il soft delete dei suoi messaggi, e l'agent non li vede più.

### La parte interessante

Scrivi il test di isolamento della Sezione 18.3 con un **ID di conversazione che collide fra due tenant o due utenti**. È il test che cattura il prefisso mancante, ed è quello che le persone saltano perché il percorso felice già funzionava.

### Andare oltre

Aggiungi un endpoint `/conversations/{id}/export` che restituisce l'intera trascrizione come JSON. Ora hai soddisfatto il requisito GDPR di esportazione, e scoprirai immediatamente se il tuo model dei messaggi porta abbastanza contesto da essere esportabile — la maggior parte dei primi tentativi non lo fa.
