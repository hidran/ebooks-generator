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
            ?->getContent();
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

Ricorda `parent::__construct()` (Sezione 4.3) e che un costruttore personalizzato significa `new`, non `::make()`. `make()` inoltra i suoi argomenti al costruttore, quindi una volta che il costruttore è tuo, `make(threadId: ...)` non raggiunge più il genitore — la Sezione 18.3 mostra come passare il thread da te.

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
            ?->getContent();
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

Le migration atterrano in `database/migrations/neuron` — una sottocartella, ed è per questo che serve il flag `--path`. Esegui entrambi i comandi insieme; il secondo è facile da dimenticare e il fallimento è silenzioso.

Sono tre: la tabella `chat_messages`, una colonna `archived_at` aggiunta a essa, e la tabella `workflow_store` che usa la Sezione 18.4. Se un progetto esistente ha pubblicato le migration del pacchetto con una release precedente, pubblica di nuovo — le release precedenti includevano solo la prima.

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
            modelClass: ChatMessage::class,
            contextWindow: 100000,
        );
    }
}
```

```php
MyAgent::make(threadId: 'THREAD_ID')->chat(new UserMessage('Hello'));
```

`NeuronAI\Laravel\Models\ChatMessage` viene fornito con il pacchetto.

Nota che cosa la cronologia *non* riceve: il thread. Il thread appartiene all'agent. Lo dichiari una volta, con `make(threadId: ...)`, e l'agent lo lega a qualunque cronologia restituisca `chatHistory()` prima della prima lettura. La cronologia viene costruita senza un'identità, e il framework non ne inventa mai una.

Il thread è più di una chiave della cronologia. È anche il **workflow ID** dell'agent — il nome sotto cui una run in pausa viene persistita e poi ritrovata (Sezione 18.4). Un solo identificatore, dichiarato in un solo posto, dà il nome sia alla conversazione sia alla run.

*Puoi* ancora pre-legare una cronologia — `new EloquentChatHistory(ChatMessage::class, 'THREAD_ID')` — e l'agent adotta quella chiave. Ma una chiave che compare solo quando l'hook viene eseguito arriva dopo che la run è già partita, troppo tardi perché la run sia ritrovabile tramite il suo thread. Dichiara il thread sull'agent.

::: {.callout .callout-warning}
[Ortografia]{.callout-title}

La documentazione scrive `ElquentChatHistory` nella prosa e ancora la sezione a `#eloquentchathisotry`. La classe è `EloquentChatHistory`. Appendice A, punto 42 — innocuo una volta che lo sai, e venti minuti sprecati se stai cercando la versione sbagliata.
:::

### Rendere reale `thread_id`

`'THREAD_ID'` è un segnaposto. In pratica è il confine di isolamento, e sbagliarlo è una fuga di dati:

```php
class SupportAgent extends Agent
{
    protected function chatHistory(): ChatHistoryInterface
    {
        return new EloquentChatHistory(
            modelClass: ChatMessage::class,
            contextWindow: ProviderContext::window(),
        );
    }
}
```

```php
$this->app->bind(SupportAgent::class, function ($app) {
    $conversation = $app->make(ConversationResolver::class)->current();

    return SupportAgent::make(threadId: "conv:{$conversation->id}");
});
```

L'agent non ha bisogno di un costruttore proprio: `make(threadId:)` è la porta d'ingresso del framework per l'identità, e il binding è l'unico posto che la decide.

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
contextWindow: config('neuron.context_windows.' . config('neuron.provider.default'), 29_000),
```

Cambia provider per ambiente e il trimmer segue. Scrivi 100.000 a codice e chi esegue Ollama in locale incapperà in errori di contesto che in produzione non compaiono mai.

### Estendere il modello

Il `ChatMessage` del pacchetto è un punto di partenza. Un'applicazione reale di solito vuole:

- Una chiave esterna verso `users`
- Soft delete per la politica di conservazione
- Un indice su `thread_id` più un timestamp
- Una colonna tenant

Estendi il modello e passa la tua classe come `modelClass`. È anche qui che vive il GDPR: le conversazioni contengono qualunque cosa gli utenti abbiano digitato, il che in un contesto di supporto significa dati personali. Cancellazione, esportazione e conservazione sono requisiti di prodotto, non ripensamenti — l'avvertimento sul logging della Sezione 3.7, reso concreto.

Un comportamento cambia i conti della conservazione. Quando la cronologia elimina messaggi dalla context window, non li cancella: li marca con `archived_at` e carica solo le righe non archiviate. Il modello vede il thread ridotto; la tua tabella conserva la trascrizione completa. È un bene per l'audit e per l'esportazione, ma significa che "l'agent l'ha dimenticato" e "non lo conserviamo più" ora sono affermazioni diverse. Il tuo job di conservazione deve cancellare esplicitamente le righe archiviate.

### Punti chiave

- Pubblica e migra con `--path=/database/migrations/neuron` — tre migration.
- Dichiara il thread sull'agent (`make(threadId:)`); costruisci la cronologia senza.
- Il thread ID è il confine di isolamento — ricavalo lato server, mai dall'input.
- Ricava `contextWindow` dal provider configurato.
- Estendi `ChatMessage` per chiavi esterne, multi-tenancy e conservazione; le righe eliminate dalla finestra vengono archiviate, non cancellate.

## 18.3 Isolamento multi-tenant

### I quattro punti di fuga

Un sistema agentico in un'applicazione multi-tenant ha quattro posti in cui i dati dei tenant possono attraversarsi:

1. **Cronologia della chat** — `thread_id`
2. **Vector store** — l'ambito di retrieval (Sezione 12.6)
3. **Tool** — i dati che interrogano
4. **Persistenza dei workflow** — il workflow ID

Sbagliane uno solo e hai una violazione. Tieni l'elenco in un posto in cui lo vedrai durante la code review.

Per un agent, il framework fonde il primo e l'ultimo: il thread ID *è* il workflow ID. Azzecca il thread e la run persistita viene delimitata con esso; sbaglialo e trapelano entrambi insieme.

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
        int $conversationId,
    ) {
        // The thread is the conversation's identity - and the run's workflow ID
        parent::__construct(threadId: "t{$tenant->id}:c{$conversationId}");
    }

    protected function provider(): AIProviderInterface
    {
        return AIProvider::driver();
    }

    protected function chatHistory(): ChatHistoryInterface
    {
        // No thread here: the agent binds its own
        return new EloquentChatHistory(
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

Ecco come un agent con un costruttore proprio dichiara il suo thread: lo passa al costruttore del genitore, non alla cronologia. La chiave composta è costruita da due valori lato server, mai da qualcosa nella richiesta.

### Il principio

**Delimita alla costruzione, non al momento della query.**

Il tool riceve un `Tenant` e costruisce le sue query a partire da quello. Non esiste un percorso di codice in cui un tool interroga senza il vincolo di tenant, perché non ha alcun modo di farlo.

Confronta con l'alternativa — un tool che legge il tenant corrente da una variabile globale o da una facade dentro `__invoke()`. Funziona finché qualcosa non gira fuori da una richiesta: un job in coda, un comando schedulato, un workflow ripreso. Allora la globale è vuota o, peggio, contiene il tenant sbagliato.

**I sistemi agentici girano fuori dal ciclo della richiesta più spesso del normale codice applicativo.** Queue worker (Sezione 16.4), workflow ripresi (Sezione 15.4), ingestione schedulata (Capitolo 20). Il contesto di tenant ambientale è inaffidabile in tutti e tre i casi. Passalo esplicitamente.

Quell'argomento si generalizza ben oltre NeuronAI.

### I workflow ID

Il workflow ID dell'agent arriva gratis con il suo thread. I tuoi workflow dichiarano il proprio sovrascrivendo `workflowId()`:

```php
class RefundWorkflow extends Workflow
{
    public function __construct(
        private readonly Tenant $tenant,
        private readonly Order $order,
    ) {
        parent::__construct();
    }

    public function workflowId(): ?string
    {
        return "t{$this->tenant->id}:refund:{$this->order->id}";
    }

    // nodes() ...
}
```

Con prefisso di tenant, così che un workflow ripreso non possa essere confuso con quello di un altro tenant, e con chiave di business, così che una richiesta successiva che conosce solo il tenant e l'ordine ricostruisca il workflow e trovi la sua run in pausa con una sola lettura. Un workflow che non dichiara alcun ID ne riceve uno generato dal motore — riprendibile, ma solo da chi ne ha conservato il riferimento.

### Testare l'isolamento

Vale la pena scriverlo come test vero:

```php
public function test_tenant_a_cannot_see_tenant_b_conversation(): void
{
    $agentA = new TenantSupportAgent($tenantA, $conversationId);
    $agentA->chat(new UserMessage('My secret code is ALPHA'));

    $agentB = new TenantSupportAgent($tenantB, $conversationId);
    $reply = $agentB->chat(new UserMessage('What is my secret code?'))->getMessage();

    $this->assertStringNotContainsString('ALPHA', (string) $reply?->getContent());
}
```

Nota l'allestimento deliberatamente ostile: lo *stesso* ID di conversazione per entrambi i tenant. Se manca il prefisso di tenant, questo test fallisce — che è esattamente ciò che vuoi che catturi.

### Punti chiave

- Quattro punti di fuga: cronologia, vector store, tool, persistenza dei workflow — per un agent, il thread copre il primo e l'ultimo.
- Delimita alla costruzione; non leggere contesto ambientale dentro i tool.
- Dichiara con `workflowId()` workflow ID con chiave di business e prefisso di tenant.
- Il codice agentico gira spesso fuori dal ciclo della richiesta — lì le globali sono inaffidabili.
- Scrivi un test di isolamento con un identificatore che collide.

## 18.4 Persistenza dei workflow con Eloquent

### L'allestimento

```php
use NeuronAI\Laravel\Models\WorkflowStore;
use NeuronAI\Workflow\Persistence\EloquentPersistence;
use NeuronAI\Workflow\Persistence\PersistenceInterface;

class TenantSupportAgent extends Agent
{
    // ...

    protected function persistence(): PersistenceInterface
    {
        return new EloquentPersistence(WorkflowStore::class);
    }
}
```

`persistence()` è un hook come `provider()` e `chatHistory()`; `setPersistence()` è il suo gemello setter, per un `Workflow` semplice o per un caso isolato. Il pacchetto include il model `WorkflowStore`, e la sua migration arriva con `--tag=neuron-migrations` insieme alle tabelle della cronologia della conversazione. `EloquentPersistence` non prende altro che la classe del model — ne prende in prestito tabella e connessione.

Quella tabella, `workflow_store`, è l'intera persistenza di NeuronAI: un unico spazio chiave-valore partizionato. Ogni record di una run — la sua accensione, il suo record di controllo, i risultati dei suoi step — vive nella partizione che porta il nome del **workflow ID**, che per un agent è il thread. È ciò che permette a un endpoint di approvazione di ricostruire `TenantSupportAgent` a partire dal solo tenant e dalla conversazione e di trovare la run in pausa con una sola lettura. Quando una run si completa senza errori, la sua partizione viene ripulita; non si accumula nulla.

::: {.callout .callout-warning}
[`workflow_store` non è una tabella applicativa]{.callout-title}

Nomi delle partizioni e chiavi sono codificati in esadecimale e i valori sono record serializzati del motore. Non c'è alcun `tenant_id` su cui filtrare e niente che sia pensato per essere letto con un `where()`. Tratta la tabella come lo storage privato del motore: fanne il backup, non interrogarla mai. Su MySQL richiede inoltre la modalità SQL strict — l'impostazione di connessione `'strict' => true`, il default di Laravel — ed `EloquentPersistence` si rifiuta di partire senza, piuttosto che rischiare record troncati.
:::

### Perché Eloquent invece dei file

La Sezione 15.4 offriva `FilePersistence` e `DatabasePersistence`. In Laravel, la persistenza Eloquent ti dà:

**Sicurezza su più server.** Qualunque worker può riprendere qualunque workflow. La persistenza su file su disco locale significa che la ripresa deve atterrare sulla stessa macchina — cosa che dietro un load balancer è un lancio di monetina. Il backend su file è pensato per un uso controllato a processo singolo.

**Continuazione atomica.** Ogni scrittura è un compare-and-write condizionale dentro una transazione sulla connessione del model. Due processi in gara per proseguire la stessa run non possono vincere entrambi.

**Una sola connessione.** La run vive nel database che già gestisci, sulla connessione che usano i tuoi model, senza una seconda credenziale da amministrare.

**Backup.** I workflow in volo vengono salvati nei backup insieme a tutto il resto, invece di vivere in una directory che nessuno si ricorda di includere.

### La schermata delle approvazioni pendenti

Il pattern che questo sblocca, e quello che il Capitolo 22 costruisce. Poiché lo store non è interrogabile, l'elenco delle conversazioni in attesa è qualcosa che la tua applicazione registra da sé, nel momento in cui viene a sapere della pausa — e lo viene a sapere senza un'eccezione. `chat()` ritorna normalmente, con uno stato interrotto:

```php
$state = $agent->chat(new UserMessage($input));

if ($state->isInterrupted()) {
    $conversation->update(['awaiting_approval_at' => now()]);
}
```

```php
class ApprovalsController extends Controller
{
    public function index(Request $request)
    {
        $pending = Conversation::query()
            ->where('tenant_id', $request->user()->tenant_id)
            ->whereNotNull('awaiting_approval_at')
            ->latest('awaiting_approval_at')
            ->paginate();

        return view('approvals.index', compact('pending'));
    }
}
```

La pagina di dettaglio chiede all'agent stesso che cosa sta aspettando. Ricostruiscilo per la conversazione e leggi `pendingApprovals()` — un'azione per ogni chiamata di tool sottoposta ad approvazione, con l'ID della chiamata, il nome del tool, gli argomenti e il motivo che il tool ha dato per chiedere:

```php
foreach ($agent->pendingApprovals() as $action) {
    // $action->id, $action->name, $action->inputs, $action->reason
}
```

La stessa informazione si trova anche sull'ultimo messaggio del thread nella cronologia della conversazione, che è ciò da cui un frontend fa il rendering (Capitolo 22).

Poiché le conversazioni in attesa sono righe della *tua* tabella, "l'AI sta aspettando un essere umano" diventa una comune pagina indice con una comune autorizzazione. È il momento in cui l'human-in-the-loop smette di essere un'esotica funzionalità AI e diventa normale sviluppo applicativo — che è precisamente ciò che rende il pattern distribuibile.

### Promemoria operativi dalla Sezione 15.4

Le quattro domande valgono ancora, ora con risposte Laravel:

- **Notifica** → invia una `Notification` quando lo stato restituito risponde `isInterrupted()`; non c'è alcuna eccezione da catturare
- **Timeout** → un comando schedulato su `awaiting_approval_at` che chiude le run ferme con un rifiuto, `submitApprovalDecisions([$callId => ['reject', 'Timed out']])->run()` — rifiutare è la via di annullamento
- **Doppia ripresa** → gestita dal motore: un secondo invio per una run già chiusa non trova alcuna run persistita e lancia un'eccezione, e un nuovo `chat()` su un thread ancora in attesa lancia `RunInFlightException` — blocca l'input nella UI finché la decisione non è consegnata
- **Compatibilità con i deploy** → tieni le richieste di interruzione piccole e piatte; il payload serializzato contiene le tue classi. I tool non vengono mai serializzati, quindi un tool che contiene un repository o un client HTTP non crea problemi alla persistenza

### Punti chiave

- `EloquentPersistence(WorkflowStore::class)`, restituito dall'hook `persistence()` dell'agent.
- Una sola tabella `workflow_store`, partizionata per workflow ID — il thread, per un agent. Fanne il backup; non interrogarla mai.
- Sicuro su più server, atomico, sulla tua connessione esistente, incluso nei backup.
- Registra le approvazioni pendenti sul tuo model quando `isInterrupted()`; leggi i dettagli con `pendingApprovals()`.
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
