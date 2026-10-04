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
    public function ask(Request $request, Conversation $conversation)
    {
        return SupportAgent::make(workflowId: $conversation->threadId())
            ->chat(new UserMessage($request->input('message')))
            ->getMessage()
            ?->getContent();
    }
}
```

Funziona. Ma ora il controller costruisce l'agent, il che significa che non puoi sostituirlo nei test, non puoi passargli gli store che il resto dell'applicazione condivide e non puoi configurarlo in un posto solo. (`threadId()` dà il nome al thread della conversazione; la Sezione 18.2 spiega come scegliere bene quel nome.)

### Iniezione dal costruttore

```php
namespace App\Neuron\Agents;

use NeuronAI\Agent\Agent;
use NeuronAI\Chat\History\MessageStoreInterface;
use NeuronAI\Laravel\Facades\AIProvider;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Workflow\Persistence\PersistenceInterface;

class SupportAgent extends Agent
{
    public function __construct(
        protected MessageStoreInterface $conversations,
        protected PersistenceInterface $runs,
    ) {
        parent::__construct();
    }

    protected function provider(): AIProviderInterface
    {
        return AIProvider::driver();
    }

    protected function messageStore(): MessageStoreInterface
    {
        return $this->conversations;
    }

    protected function persistence(): PersistenceInterface
    {
        return $this->runs;
    }

    // contextWindow() arrives in Section 18.2, tools() in Section 18.3
}
```

Il costruttore chiede le due cose che un agent conserva fra una richiesta e l'altra — dove vivono le conversazioni (Sezione 18.2) e dove vivono le run in pausa (Sezione 18.4) — e nulla su chi sta chiedendo. Nessun utente, nessun tenant, nessun thread: la classe descrive un agent, non una conversazione.

Ricorda `parent::__construct()` (Sezione 4.3) e che un costruttore personalizzato cambia ciò che `make()` accetta. `make()` inoltra i suoi argomenti al costruttore, quindi una volta che il costruttore è tuo, `make(workflowId: ...)` è un parametro con nome sconosciuto — il thread arriva per un'altra via, qui sotto. E chiama le proprietà promosse come vuoi, tranne `$messageStore` e `$persistence`: `Agent` le dichiara già entrambe, con tipi nullable, e PHP rifiuta la ridichiarazione con un errore fatale.

### Il binding

```php
namespace App\Providers;

use App\Models\ChatMessage;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\ServiceProvider;
use NeuronAI\Chat\History\EloquentMessageStore;
use NeuronAI\Chat\History\MessageStoreInterface;
use NeuronAI\Workflow\Persistence\DatabasePersistence;
use NeuronAI\Workflow\Persistence\PersistenceInterface;

class NeuronServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        // Stateless: it resolves the model's connection on every call
        $this->app->singleton(
            MessageStoreInterface::class,
            fn () => new EloquentMessageStore(ChatMessage::class),
        );

        // It keeps the PDO it was given, so every resolution takes the current one
        $this->app->bind(
            PersistenceInterface::class,
            fn () => new DatabasePersistence(DB::connection()->getPdo()),
        );
    }
}
```

È un provider tuo — `php artisan make:provider NeuronServiceProvider` lo crea e lo registra — non il `NeuronAIServiceProvider` dell'SDK. Fa il binding dei due store e di nient'altro. L'agent non ha bisogno di alcun binding: Laravel legge il suo costruttore e lo risolve in autowiring.

```php
class SupportController extends Controller
{
    public function ask(
        Request $request,
        Conversation $conversation,
        SupportAgent $agent,
    ) {
        Gate::authorize('participate', $conversation);

        return $agent
            ->for($conversation->threadId())
            ->chat(new UserMessage($request->input('message')))
            ->getMessage()
            ?->getContent();
    }
}
```

**Il container costruisce l'agent; la richiesta lo lega.** Il metodo del controller chiede un agent nella propria firma e ne riceve uno, collegato agli store dell'applicazione. La policy decide se questo utente può usare questa conversazione, e solo allora `for()` restituisce una copia dell'agent legata al thread di quella conversazione; l'istanza costruita dal container non viene mai modificata. Chiedi l'agent nel metodo, non nel costruttore del controller: viene risolto quando il metodo viene eseguito, dopo che il middleware ha autenticato l'utente, e niente lo trattiene più a lungo della chiamata.

### Perché vale la cerimonia

**Testabilità.** Consegna al container un agent il cui provider è un fake e il controller parla con quello; la copia creata da `for()` condivide quel provider. È il problema della Sezione 1.5 — non puoi fare asserzioni sull'output del modello, quindi il confine che *puoi* testare è la gestione di un agent da parte del controller, e l'iniezione delle dipendenze è ciò che fa esistere quel confine.

```php
$provider = new FakeAIProvider(new AssistantMessage('Your order ships tomorrow.'));

$this->app->instance(
    SupportAgent::class,
    $this->app->make(SupportAgent::class)->setAiProvider($provider),
);

$this->actingAs($user)
    ->post("/conversations/{$conversation->id}/messages", [
        'message' => 'Where is my order?',
    ])
    ->assertOk();

$provider->assertCallCount(1);
```

**Configurazione per utente.** Il thread dice di chi è la conversazione, quindi ciò che l'agent costruisce per una run — i suoi tool, e la loro visibilità (Sezione 5.10) — discende dal thread a cui è stato legato, senza che il controller lo sappia. La Sezione 18.3 mostra come.

**Un posto solo da cambiare.** Gli store si decidono nel service provider; provider, tool e istruzioni nella classe. Nessun controller decide nessuna di queste cose.

**Si legge come Laravel.** Il che conta per l'adozione. Un agent che arriva per iniezione è un servizio come un altro, e un team sa già come ragionare sui servizi.

### Cicli di vita

I due binding hanno cicli di vita diversi di proposito, e l'agent ne ha un terzo:

- Il message store è un `singleton()`. `EloquentMessageStore` contiene una classe di model e nient'altro; risolve la connessione del model a ogni chiamata.
- La persistenza è un semplice `bind()`. `DatabasePersistence` conserva il PDO che ha ricevuto, quindi ogni risoluzione deve prendere quello corrente di Laravel. In un worker a lunga vita una riconnessione sostituisce quel PDO, e un singleton continuerebbe a tenere quello vecchio.
- L'agent non è registrato affatto. L'autowiring ne costruisce uno nuovo ogni volta che viene risolto — per richiesta, per job — ed è il ciclo di vita che vuoi.

::: {.callout .callout-warning}
[Mai `singleton()` per un agent]{.callout-title}

Un agent cattura la sua persistenza — e quel PDO — nel momento in cui viene costruito. Registralo come singleton e, sotto Octane o in un queue worker, una sola istanza serve tutte le richieste per l'intera vita del processo: tiene un handle di connessione molto dopo che una riconnessione l'ha sostituito, e qualunque cosa una richiesta le abbia impostato è ancora lì per la successiva. È responsabilità tua, e sotto PHP-FPM non si manifesterà affatto.
:::

### Punti chiave

- Iniezione dal costruttore per gli store, con il binding in un service provider; l'agent stesso è risolto in autowiring.
- Il container costruisce l'agent; la richiesta autorizza la conversazione e ne lega il thread con `for()`.
- Testabilità, configurazione per utente, punto di modifica unico.
- Mai `singleton()` per un agent — risolvilo per richiesta o per job.

## 18.2 EloquentMessageStore

### Una sola migration

```bash
php artisan make:migration create_neuron_tables
php artisan make:model ChatMessage
```

Una sola migration tua crea entrambe le tabelle di cui NeuronAI ha bisogno: `chat_messages` per le conversazioni e `workflow_store` per le run della Sezione 18.4. Sostituisci il corpo del file generato con questo, poi esegui `php artisan migrate`:

```php
use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * The conversations (EloquentMessageStore) and the durable runs (DatabasePersistence) of the Neuron agents.
     */
    public function up(): void
    {
        // MySQL and MariaDB collations ignore case and accents: identifiers must compare byte by byte there.
        $mysql = in_array(Schema::getConnection()->getDriverName(), ['mysql', 'mariadb'], true);

        Schema::create('chat_messages', function (Blueprint $table) use ($mysql) {
            $table->id();
            if ($mysql) {
                $table->binary('thread_id', 255);
                $table->binary('message_id', 64);
            } else {
                $table->string('thread_id', 255);
                $table->string('message_id', 64);
            }
            $table->string('role', 32);
            $table->longText('content')->nullable();
            $table->longText('meta')->nullable();
            $table->timestamp('archived_at')->nullable();
            $table->timestamps();
            $table->unique(['thread_id', 'message_id']);
        });

        Schema::create('workflow_store', function (Blueprint $table) use ($mysql) {
            if ($mysql) {
                $table->string('partition', 510)->charset('ascii')->collation('ascii_bin');
                $table->string('key', 510)->charset('ascii')->collation('ascii_bin');
                $table->longText('value')->charset('ascii');
            } else {
                $table->string('partition', 510);
                $table->string('key', 510);
                $table->longText('value');
            }
            $table->timestamp('updated_at')->useCurrent();
            $table->primary(['partition', 'key']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('workflow_store');
        Schema::dropIfExists('chat_messages');
    }
};
```

È la migration che i maintainer pubblicano nella skill `neuron-laravel-integration` del framework, che dichiara di averla eseguita senza modifiche su SQLite, MySQL 8.4, MariaDB 11.7 e PostgreSQL 17. In `chat_messages` tre cose ci sono per lo store:

- `message_id` è l'identità di un messaggio. Lo store aggiunge per `(thread_id, message_id)`, quindi scrivere due volte lo stesso messaggio lo memorizza una volta sola, e l'indice univoco serve ogni ricerca per thread.
- L'`id` auto-increment ordina il thread. Qualunque chiave usi il tuo model deve seguire l'ordine di inserimento — auto-increment, ULID o UUIDv7, mai UUIDv4.
- `archived_at` marca i messaggi eliminati dalla context window, che vengono conservati anziché cancellati (più sotto).

Le colonne `binary()` sono per MySQL e MariaDB, le cui collation di default ignorano la differenza fra maiuscole e minuscole: con `string()`, due thread i cui nomi differiscono solo per le maiuscole condividerebbero una cronologia.

::: {.callout .callout-warning}
[Non pubblicare le migration dell'SDK]{.callout-title}

neuron-laravel 2.0.0 offre ancora `php artisan vendor:publish --tag=neuron-migrations` e un model `NeuronAI\Laravel\Models\ChatMessage`, e nessuno dei due è adatto a neuron-ai 4.0.2. Lo store identifica ogni messaggio tramite `message_id`; la tabella dell'SDK non ha quella colonna e il suo model non la rende fillable. Su SQLite, dove questo libro l'ha verificato, non fallisce nulla: lo stesso messaggio viene memorizzato due volte e torna indietro con un ID diverso. Usa la migration qui sopra e il model qui sotto.
:::

### Usalo

```php
namespace App\Models;

use Illuminate\Database\Eloquent\Attributes\Fillable;
use Illuminate\Database\Eloquent\Model;

#[Fillable(['thread_id', 'message_id', 'role', 'content', 'meta'])]
class ChatMessage extends Model
{
    protected function casts(): array
    {
        return [
            'content' => 'array',
            'meta' => 'array',
        ];
    }
}
```

Cinque colonne fillable e due cast ad array: è tutto ciò che lo store chiede al model. Lo store, da parte sua, non prende altro che la classe del model — `new EloquentMessageStore(ChatMessage::class)`, la riga che `NeuronServiceProvider` contiene già — e l'agent lo passa al framework attraverso un hook. Un secondo hook dice quanta parte della conversazione può essere inviata al modello:

```php
class SupportAgent extends Agent
{
    // ...

    protected function messageStore(): MessageStoreInterface
    {
        return $this->conversations;
    }

    protected function contextWindow(): int
    {
        return 100_000;
    }
}
```

```php
$agent->for('THREAD_ID')->chat(new UserMessage('Hello'));
```

Nota che cosa lo store *non* riceve: il thread. Lo store è stateless — una sola istanza serve tutte le conversazioni, ed è per questo che può essere un singleton — e ogni lettura e ogni scrittura indica il thread a cui si riferisce. Il thread appartiene all'agent. Lo leghi una volta, con `for()`, e il framework non ne inventa mai uno: un agent senza thread si rifiuta di partire.

Il thread è più di una chiave della cronologia. È anche il **workflow ID** dell'agent — il nome sotto cui una run in pausa viene persistita e poi ritrovata (Sezione 18.4). Un solo identificatore, legato in un solo posto, dà il nome sia alla conversazione sia alla run.

Fra lo store e il modello sta `ChatHistory`, una classe concreta che l'agent si costruisce da sé ogni volta che viene eseguito, a partire esattamente da quelle tre cose: lo store, il thread e la finestra. Carica i messaggi attivi del thread e li mantiene dentro il budget. Tu non la costruisci mai.

::: {.callout .callout-warning}
[Un override di `chatHistory()` non conserva nulla]{.callout-title}

`messageStore()` e `contextWindow()` sono gli unici hook di memoria in neuron-ai 4.0.2. Una classe che sovrascrive invece `chatHistory()` — come mostrano ancora il README di neuron-laravel 2.0.0 e le skill Boost che include — si carica e risponde senza errori, perché nulla chiama quel metodo. L'agent usa silenziosamente lo store in memoria con una finestra di 50.000 token, e la conversazione sparisce quando la richiesta termina. Se un agent dimentica tutto fra due richieste, cerca prima di tutto quel metodo.
:::

### Rendere reale `thread_id`

`'THREAD_ID'` è un segnaposto. In pratica è il confine di isolamento, e sbagliarlo è una fuga di dati. Dai il nome al thread sul server, a partire da un record, e lascia che sia una policy a dire chi può usare quel record:

```php
class Conversation extends Model
{
    /** Named on the server from three columns of this row, never from a request. */
    public function threadId(): string
    {
        return "t{$this->tenant_id}:u{$this->user_id}:c{$this->id}";
    }
}
```

```php
class ConversationPolicy
{
    public function participate(User $user, Conversation $conversation): bool
    {
        return $conversation->user_id === $user->id
            && $conversation->tenant_id === $user->tenant_id;
    }
}
```

È ciò che facevano due righe del controller della Sezione 18.1. La route indica una conversazione; `Gate::authorize('participate', $conversation)` decide se questo utente può usarla; solo allora `for($conversation->threadId())` lega l'agent. Per tutto questo l'agent non ha bisogno di alcun argomento nel costruttore: `for()` è la porta d'ingresso dell'identità per un agent costruito dal container, e il codice che la precede è l'unico posto che decide quale thread una richiesta può toccare.

**Non ricavare mai il thread ID dall'input dell'utente.** Un parametro di richiesta che diventa un thread ID significa che chiunque può leggere la conversazione di chiunque cambiando un numero. Anche l'ID della conversazione nell'URL è input dell'utente; è la policy a trasformarlo in una risorsa che questo utente può usare. Ricava il thread lato server da una risorsa autenticata e autorizzata.

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
protected function contextWindow(): int
{
    return config('neuron.context_windows.' . config('neuron.provider.default'), 29_000);
}
```

Cambia provider per ambiente e il trimmer segue. Scrivi 100.000 a codice e chi esegue Ollama in locale incapperà in errori di contesto che in produzione non compaiono mai.

### Estendere il model

`ChatMessage` è un model tuo, quindi può crescere con l'applicazione. Un'applicazione reale di solito vuole:

- Una chiave esterna verso `conversations` o `users`
- Soft delete per la politica di conservazione
- Un indice su `thread_id` più un timestamp
- Una colonna tenant

Una regola le governa tutte: lo store scrive le sue cinque colonne e non sa nulla delle tue. Una colonna `NOT NULL` che lo store non riempie fa fallire ogni scrittura. Rendi nullable le colonne applicative, oppure riempile in un hook `creating` a partire dall'unica cosa che ogni riga porta con sé, il suo thread:

```php
class ChatMessage extends Model
{
    use SoftDeletes;

    // ...

    protected static function booted(): void
    {
        // The store fills its five columns; the thread says what the others are
        static::creating(function (ChatMessage $message): void {
            $scope = ThreadScope::of($message->thread_id);

            $message->tenant_id = $scope->tenantId;
            $message->conversation_id = $scope->conversationId;
        });
    }
}
```

`ThreadScope` rilegge il nome scritto da `threadId()`; lo trovi nella Sezione 18.3. È anche qui che vive il GDPR: le conversazioni contengono qualunque cosa gli utenti abbiano digitato, il che in un contesto di supporto significa dati personali. Cancellazione, esportazione e conservazione sono requisiti di prodotto, non ripensamenti — l'avvertimento sul logging della Sezione 3.7, reso concreto.

Un comportamento cambia i conti della conservazione. Quando la cronologia elimina messaggi dalla context window, non li cancella: li marca con `archived_at` e carica solo le righe non archiviate. Il modello vede il thread ridotto; la tua tabella conserva la trascrizione completa. È un bene per l'audit e per l'esportazione, ma significa che "l'agent l'ha dimenticato" e "non lo conserviamo più" ora sono affermazioni diverse. Il tuo job di conservazione deve cancellare esplicitamente le righe archiviate.

### Punti chiave

- Una migration e un model tuoi; la tabella pubblicata dall'SDK non è adatta a neuron-ai 4.0.2.
- `messageStore()` restituisce lo store e `contextWindow()` il budget; il thread si lega sull'agent con `for()`, non si passa mai allo store.
- Il thread ID è il confine di isolamento — ricavalo lato server, mai dall'input.
- Ricava la context window dal provider configurato.
- Estendi `ChatMessage` per chiavi esterne, multi-tenancy e conservazione, con colonne nullable o riempite in `creating`; le righe eliminate dalla finestra vengono archiviate, non cancellate.

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
namespace App\Neuron;

use LogicException;

/** Who a thread belongs to, read back from the name Conversation::threadId() gave it. */
final readonly class ThreadScope
{
    private function __construct(
        public int $tenantId,
        public int $userId,
        public int $conversationId,
    ) {}

    public static function of(?string $threadId): self
    {
        if (preg_match('/^t(\d+):u(\d+):c(\d+)$/', (string) $threadId, $match) !== 1) {
            throw new LogicException(
                "Thread '{$threadId}' names no tenant, user and conversation."
            );
        }

        return new self((int) $match[1], (int) $match[2], (int) $match[3]);
    }
}
```

```php
class SupportAgent extends Agent
{
    // ...

    protected function tools(): array
    {
        $scope = ThreadScope::of($this->getThreadId());

        return [
            // The tools receive the tenant - they cannot query outside it
            new SearchOrdersTool($scope->tenantId),
            new GetOrderStatusTool($scope->tenantId),
        ];
    }
}
```

Ecco come un agent costruito senza sapere nulla di chi lo chiama arriva a conoscere il suo tenant: dal thread a cui è stato legato, non da `auth()` e non da un argomento del costruttore. Il nome è stato composto sul server da tre colonne di una riga, mai da qualcosa nella richiesta, e un thread che non le porta tutte e tre viene rifiutato prima che esista un solo tool.

### Il principio

**Delimita alla costruzione, non al momento della query.**

Il tool riceve l'ID di un tenant e costruisce le sue query a partire da quello. Non esiste un percorso di codice in cui un tool interroga senza il vincolo di tenant, perché non ha alcun modo di farlo.

Confronta con l'alternativa — un tool che legge il tenant corrente da una variabile globale o da una facade dentro `__invoke()`. Funziona finché qualcosa non gira fuori da una richiesta: un job in coda, un comando schedulato, un workflow ripreso. Allora la globale è vuota o, peggio, contiene il tenant sbagliato.

**I sistemi agentici girano fuori dal ciclo della richiesta più spesso del normale codice applicativo.** Queue worker (Sezione 16.4), workflow ripresi (Sezione 15.4), ingestione schedulata (Capitolo 20). Il contesto di tenant ambientale è inaffidabile in tutti e tre i casi. Passalo esplicitamente — ed è ciò che fa il thread: lo stesso agent, legato allo stesso thread, costruisce gli stessi tool in un controller e in un queue worker.

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

Con prefisso di tenant, così che un workflow ripreso non possa essere confuso con quello di un altro tenant, e con chiave di business, così che una richiesta successiva che conosce solo il tenant e l'ordine ricostruisca il workflow e trovi la sua run in pausa con una sola lettura. Il workflow di rimborso del Capitolo 22 mantiene il più breve `refund:{orderId}` della Sezione 15.4: la chiave primaria di un ordine è già unica fra i tenant, e il prefisso serve alle chiavi di business che non lo sono. Un workflow senza alcun ID — né dichiarato né assegnato — non parte: il motore non ne inventa mai uno.

### Testare l'isolamento

Vale la pena scriverlo come test vero:

```php
public function test_tenant_a_history_never_reaches_tenant_b(): void
{
    // The hostile part: both tenants hold user 3 and conversation 7
    $a = (new Conversation())->forceFill(['id' => 7, 'tenant_id' => 1, 'user_id' => 3]);
    $b = (new Conversation())->forceFill(['id' => 7, 'tenant_id' => 2, 'user_id' => 3]);

    $modelA = new FakeAIProvider(new AssistantMessage('Noted.'));
    $modelB = new FakeAIProvider(new AssistantMessage('I do not know.'));

    app(SupportAgent::class)->setAiProvider($modelA)
        ->for($a->threadId())
        ->chat(new UserMessage('My secret code is ALPHA'));

    app(SupportAgent::class)->setAiProvider($modelB)
        ->for($b->threadId())
        ->chat(new UserMessage('What is my secret code?'));

    // Assert on what tenant B's model was sent, not on what a model might answer
    $modelB->assertCallCount(1);
    $modelB->assertSent(fn (RequestRecord $request): bool =>
        ! str_contains(json_encode($request->messages), 'ALPHA'));
}
```

Nota l'allestimento deliberatamente ostile: gli *stessi* numeri di utente e di conversazione per entrambi i tenant. Se manca il prefisso di tenant, questo test fallisce — che è esattamente ciò che vuoi che catturi.

Nota anche su che cosa fa l'asserzione. `FakeAIProvider` (Laboratorio 7) registra ogni richiesta, quindi il test ispeziona i messaggi arrivati al modello del tenant B invece di sperare che un modello vero ripeta il segreto. Nessun modello viene chiamato, il risultato è lo stesso a ogni esecuzione, e il test può bloccare un deploy.

### Punti chiave

- Quattro punti di fuga: cronologia, vector store, tool, persistenza dei workflow — per un agent, il thread copre il primo e l'ultimo.
- Delimita alla costruzione; non leggere contesto ambientale dentro i tool.
- Dichiara con `workflowId()` workflow ID con chiave di business e prefisso di tenant.
- Il codice agentico gira spesso fuori dal ciclo della richiesta — lì le globali sono inaffidabili.
- Scrivi un test di isolamento con un identificatore che collide, e fai l'asserzione su ciò che è stato inviato al modello.

## 18.4 Persistenza dei workflow nel database

### L'allestimento

```php
class SupportAgent extends Agent
{
    // ...

    protected function persistence(): PersistenceInterface
    {
        return $this->runs;
    }
}
```

`persistence()` è un hook come `provider()` e `messageStore()`; `setPersistence()` è il suo gemello setter, per un `Workflow` semplice o per un caso isolato. Qui restituisce la `DatabasePersistence` che `NeuronServiceProvider` costruisce sul PDO di Laravel, e la sua tabella è arrivata con la migration della Sezione 18.2.

Quella tabella, `workflow_store`, è l'intera persistenza di NeuronAI: un unico spazio chiave-valore partizionato. Ogni record di una run — la sua accensione, il suo record di controllo, i risultati dei suoi step — vive nella partizione che porta il nome del **workflow ID**, che per un agent è il thread. È ciò che permette a un endpoint di approvazione di legare `SupportAgent` al thread della conversazione e di trovare la run in pausa con una sola lettura. Quando una run si completa senza errori, la sua partizione viene ripulita; non si accumula nulla.

::: {.callout .callout-warning}
[`workflow_store` non è una tabella applicativa]{.callout-title}

Nomi delle partizioni e chiavi sono codificati in esadecimale e i valori sono record del motore codificati in base64. Non c'è alcun `tenant_id` su cui filtrare e niente che sia pensato per essere letto con un `where()`. Tratta la tabella come lo storage privato del motore: fanne il backup, non interrogarla mai. Su MySQL richiede inoltre la modalità SQL strict — l'impostazione di connessione `'strict' => true`, il default di Laravel — e `DatabasePersistence` si rifiuta di scrivere senza, piuttosto che rischiare record troncati.
:::

### Perché il database invece dei file

La Sezione 15.4 elencava i backend. In Laravel, `DatabasePersistence` ti dà:

**Sicurezza su più server.** Qualunque worker può riprendere qualunque workflow. La persistenza su file su disco locale significa che la ripresa deve atterrare sulla stessa macchina — cosa che dietro un load balancer è un lancio di monetina. Il backend su file è pensato per un uso controllato a processo singolo.

**Continuazione atomica.** Ogni scrittura è un compare-and-write condizionale dentro una transazione sulla connessione di Laravel. Due processi in gara per proseguire la stessa run non possono vincere entrambi.

**Una sola connessione.** La run vive nel database che già gestisci, sulla connessione che usano i tuoi model, senza una seconda credenziale da amministrare.

**Backup.** I workflow in volo vengono salvati nei backup insieme a tutto il resto, invece di vivere in una directory che nessuno si ricorda di includere.

`EloquentPersistence` è l'altro backend su database. Prende una classe di model e risolve la connessione del model a ogni operazione, quindi può essere un singleton. Non è un sostituto diretto per questa tabella: gli serve una tabella propria, con una normale chiave primaria `id` e `unique(partition, key)` al posto della chiave composta, e un model tuo — `App\Models\WorkflowRecord`, per esempio — con `partition`, `key` e `value` fillable e senza soft delete.

::: {.callout .callout-warning}
[Non il `WorkflowStore` dell'SDK]{.callout-title}

neuron-laravel 2.0.0 include un model `NeuronAI\Laravel\Models\WorkflowStore` su una tabella `workflow_store` con chiave primaria composta e senza `id`. `new EloquentPersistence(WorkflowStore::class)` non funziona con neuron-ai 4.0.2: il backend indirizza le righe tramite una chiave che la tabella non ha. Su SQLite, dove questo libro l'ha verificato, una run completata non viene mai ripulita, e il messaggio successivo sullo stesso thread viene rifiutato con `RunInFlightException` finché non scade il lease di dieci minuti. Usa `DatabasePersistence`, oppure dai a `EloquentPersistence` una tabella e un model tuoi.
:::

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

La pagina di dettaglio chiede all'agent stesso che cosa sta aspettando. Legalo al thread della conversazione e leggi `pendingApprovals()` — un'azione per ogni chiamata di tool sottoposta ad approvazione, con l'ID della chiamata, il nome del tool, gli argomenti e il motivo che il tool ha dato per chiedere:

```php
foreach ($agent->pendingApprovals() as $action) {
    // $action->id, $action->name, $action->inputs, $action->reason
}
```

La stessa informazione si trova anche sull'ultimo messaggio del thread nella cronologia della conversazione, che è ciò da cui un frontend fa il rendering (Capitolo 22).

Poiché le conversazioni in attesa sono righe della *tua* tabella, "l'AI sta aspettando un essere umano" diventa una comune pagina indice con una comune autorizzazione. È il momento in cui l'human-in-the-loop smette di essere un'esotica funzionalità AI e diventa normale sviluppo applicativo — che è precisamente ciò che rende il pattern distribuibile.

### Promemoria operativi dalla Sezione 15.4

Le quattro domande valgono ancora, ora con risposte Laravel, e gli store durevoli ne aggiungono una quinta:

- **Notifica** → invia una `Notification` quando lo stato restituito risponde `isInterrupted()`; non c'è alcuna eccezione da catturare
- **Timeout** → un comando schedulato su `awaiting_approval_at` che chiude le run ferme con un rifiuto, `submitApprovalDecisions([$callId => ['reject', 'Timed out']])->run()` — rifiutare è la via di annullamento
- **Doppia ripresa** → gestita dal motore: un secondo invio per una run già chiusa non trova alcuna run persistita e lancia `InputTranslationException`, e un nuovo `chat()` su un thread ancora in attesa lancia `RunInFlightException` — rispondi con un 400 e con un 409, e blocca l'input nella UI finché la decisione non è consegnata
- **Compatibilità con i deploy** → tieni le richieste di interruzione piccole e piatte; il payload serializzato contiene le tue classi. I tool non vengono mai serializzati, quindi un tool che contiene un repository o un client HTTP non crea problemi alla persistenza
- **Turni falliti** → un turno che muore dopo aver memorizzato la sua domanda — il provider fallisce dopo uno step di tool, un'eccezione sfugge da un tool — lascia la sua run `failed`, e il successivo `chat()` su quel thread lancia `ChatHistoryException: Invalid message sequence`. Porta a termine il turno fallito prima di iniziare il successivo

```php
class SupportAgent extends Agent
{
    // ...

    /** A failed turn that stored its question blocks the next one: finish it first. */
    public function recoverFailedTurn(): void
    {
        $run = $this->inspect();

        if ($run?->status === WorkflowStatus::Failed) {
            $this->run(ExecutionRequest::resume(
                expectedRunId: $run->runId,
                expectedExecutionAttempt: $run->executionAttempt,
            ));
        }
    }
}
```

```php
$agent = $agent->for($conversation->threadId());
$agent->recoverFailedTurn();

$state = $agent->chat(new UserMessage($request->input('message')));
```

Ogni endpoint che avvia un turno lo chiama per prima cosa; se non c'è nulla da recuperare non fa nulla. Prima, non dopo: una volta che una nuova domanda è stata impilata su un turno fallito, portare a termine quel turno fallisce allo stesso modo, e solo `resetConversation()` — che azzera la cronologia del thread insieme alla sua run — libera il thread.

### Punti chiave

- `DatabasePersistence` sul PDO di Laravel, con il binding nel service provider e restituita dall'hook `persistence()` dell'agent.
- Una sola tabella `workflow_store`, partizionata per workflow ID — il thread, per un agent. Fanne il backup; non interrogarla mai.
- Sicuro su più server, atomico, sulla tua connessione esistente, incluso nei backup.
- Registra le approvazioni pendenti sul tuo model quando `isInterrupted()`; leggi i dettagli con `pendingApprovals()`.
- Le quattro domande operative ricevono comuni risposte Laravel; la quinta è `recoverFailedTurn()` prima di ogni turno.

## Laboratorio 12 — Chat persistente multi-thread

**Copre:** binding nel container, `EloquentMessageStore`, isolamento dei thread, context window.

### Obiettivo

Un utente autenticato può tenere diverse conversazioni indipendenti con lo stesso agent, ciascuna persistita, ciascuna isolata, ciascuna riprendibile dopo un deploy completo.

### Requisiti

1. **Una tabella `conversations`** posseduta dagli utenti, con un tenant, un titolo e timestamp. Un utente può averne molte.
2. **L'agent si risolve dal container**, per iniezione nel metodo, e viene legato alla conversazione corrente con `for()` — mai costruito in un controller.
3. **Il thread ID è ricavato lato server** dal record della conversazione, una volta che la policy ha autorizzato l'utente autenticato a usarla — mai da un parametro di richiesta. Dimostralo: prova a leggere la conversazione di un altro utente per ID e ottieni un 403 dalla tua policy, non una risposta dall'agent.
4. **La context window viene dalla configurazione**, indicizzata sul provider configurato, come nella Sezione 18.2.
5. **Estendi `ChatMessage`** con una chiave esterna verso `conversations`, riempita in un hook `creating`, e un soft delete.

### Criteri di accettazione

- Due conversazioni dello stesso utente non vedono i messaggi l'una dell'altra.
- Due utenti con ID di conversazione consecutivi non possono raggiungere i thread l'uno dell'altro — verificalo con un test di autorizzazione, non a occhio.
- Riavviare il server applicativo non perde nulla.
- Passare `NEURON_AI_PROVIDER` da `anthropic` a `ollama` cambia la context window del trimmer senza modifiche al codice. Logga il valore configurato per dimostrarlo.
- Cancellare una conversazione fa il soft delete dei suoi messaggi, e l'agent non li vede più.
- Un turno che fallisce a metà non blocca la conversazione: il messaggio successivo riceve risposta.

### La parte interessante

Scrivi il test di isolamento della Sezione 18.3 con un **ID di conversazione che collide fra due tenant o due utenti**. È il test che cattura il prefisso mancante, ed è quello che le persone saltano perché il percorso felice già funzionava.

### Andare oltre

Aggiungi un endpoint `/conversations/{id}/export` che restituisce l'intera trascrizione come JSON. Ora hai soddisfatto il requisito GDPR di esportazione, e scoprirai immediatamente se il tuo model dei messaggi porta abbastanza contesto da essere esportabile — la maggior parte dei primi tentativi non lo fa.
