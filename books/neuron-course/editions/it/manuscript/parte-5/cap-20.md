# Capitolo 20 — RAG sui dati dell'applicazione

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

Questo capitolo è concettuale e non ha codice a sé stante, ma il repository di accompagnamento [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) contiene le versioni eseguibili di tutto ciò che il libro costruisce.
:::

## 20.1 Un agent RAG in Laravel

### Lo store

Una knowledge base condivisa da molti tenant deve filtrare ogni ricerca per tenant, e uno store può filtrare solo sui campi di cui è stato informato. Quindi lo store viene per primo, con un `DocumentSchema` che dichiara i metadati su cui l'applicazione filtrerà:

```php
namespace App\Neuron\Rag;

use NeuronAI\RAG\Schema\DocumentField;
use NeuronAI\RAG\Schema\DocumentSchema;

final class KnowledgeBase
{
    public static function schema(): DocumentSchema
    {
        return DocumentSchema::of(
            DocumentField::integer('tenant_id')->required()->filterable(),
            DocumentField::integer('article_id')->required()->filterable(),
            DocumentField::string('visibility')->required()->filterable(),
            DocumentField::integer('updated_at')->filterable(),
        );
    }
}
```

`required()` fa sì che lo store rifiuti un documento che arriva senza quel campo — il bug di ingestione in cui qualcuno dimentica di marcare il tenant fallisce rumorosamente al momento dell'indicizzazione, invece di produrre un chunk non filtrabile.

La stessa classe costruisce lo store, così nome della tabella, top-K e schema hanno un'unica definizione:

```php
// In KnowledgeBase, which now also imports
// Illuminate\Support\Facades\DB and NeuronAI\RAG\VectorStore\MariaDBVectorStore
public static function store(): MariaDBVectorStore
{
    return new MariaDBVectorStore(
        pdo: DB::connection()->getPdo(),
        tableName: 'knowledge_base',
        topK: 5,
        schema: self::schema(),
    );
}
```

Perché non aggiungere semplicemente una chiave `schema` a `config/neuron.php`? Perché `php artisan config:cache` serializza la configurazione con `var_export()`, e un oggetto `DocumentSchema` non sopravvive al viaggio — il comando fallisce con "Your configuration files are not serializable". Gli oggetti stanno nel codice.

E perché costruire un nuovo store a ogni chiamata invece di registrarne uno come driver con `VectorStore::extend()` e lasciarlo al manager? Perché `MariaDBVectorStore` conserva il PDO che gli viene dato, e un manager conserva ciò che ha costruito per tutta la vita del processo. Un queue worker vive per giorni; quando Laravel si riconnette dopo una connessione caduta, il worker continuerebbe a usare il vecchio PDO, ormai morto. Uno store è un oggetto economico — una connessione, il nome di una tabella, uno schema — quindi l'agent e ogni job chiamano `KnowledgeBase::store()` e ciascuno riceve la connessione che Laravel tiene in quel momento.

::: {.callout .callout-warning}
[`VectorStore::extend()` funziona solo se registri il manager come singleton]{.callout-title}

Per uno store che non tiene alcuna connessione — un `FileVectorStore`, oppure Qdrant e Pinecone, che sono client HTTP — `VectorStore::extend('name', fn () => ...)` in un service provider è il modo Laravel di registrarlo. In neuron-laravel 2.0.0 non fa nulla di utile, in silenzio: l'SDK registra `AIProviderManager` e `EmbeddingProviderManager` come singleton, ma non `VectorStoreManager`. La facade `VectorStore` risolve il manager una volta e lo tiene in cache, quindi `extend()` in `boot()` funziona finché qualcosa non svuota le istanze risolte delle facade — un test, un server a lunga vita fra una richiesta e l'altra — e allora la risoluzione successiva costruisce un manager nuovo che non ha mai sentito parlare del tuo driver ("Driver [name] not supported"). Registra il manager nel tuo provider, quello del Capitolo 18, prima che qualcosa chiami `extend()`:

```php
// NeuronServiceProvider::register()
$this->app->singleton(VectorStoreManager::class);
```
:::

### La tabella

Lo store non crea la propria tabella. Lo fa `MariaDBVectorStore::setupTable()`, e il posto giusto è una migration:

```php
use App\Neuron\Rag\KnowledgeBase;
use Illuminate\Database\Migrations\Migration;

return new class extends Migration
{
    public function up(): void
    {
        KnowledgeBase::store()->setupTable((int) config('neuron.embedding.openai.dimensions'));
    }

    public function down(): void
    {
        KnowledgeBase::store()->dropTable();
    }
};
```

Serve MariaDB 11.7 o successivo, e serve la dimensione dell'embedding, che devi fornire tu. I due lati di quel numero arrivano con valori predefiniti diversi: il `config/neuron.php` dell'SDK configura l'embedder OpenAI per 1024 dimensioni, mentre `setupTable()` crea una colonna `VECTOR(1536)`. Una colonna e un modello in disaccordo sulla lunghezza di un vettore non possono lavorare insieme, quindi fissa il numero una volta sola, in `config/neuron.php`, sotto `embedding.openai` — `'dimensions' => 1536` — e lascia che la migration lo legga da lì. Scegli un valore che il tuo modello di embedding sa produrre e trattalo come parte dello schema: cambiarlo in seguito significa eliminare la tabella e rifare l'embedding di ogni articolo.

All'embedder serve ancora una riga in `.env`. `NEURON_EMBEDDING_PROVIDER` non ha un valore predefinito (l'SDK lo legge senza fallback), ed `EmbeddingProvider::driver()` lancia un `TypeError` quando non è impostato — impostalo a `openai` (oppure `gemini`, `ollama`, `voyage`, `mistral`) insieme alla chiave di quel provider.

Uno store non conserva alcuno stato per ricerca, e ogni ricerca porta con sé i propri filtri in una richiesta immutabile, quindi anche uno store condiviso fra più richieste non può far trapelare il filtro di un tenant in un altro. (I tutorial più vecchi configurano i filtri sullo store stesso con `withFilters()`, il che rendeva un'istanza condivisa una fuga fra tenant; il metodo non esiste più. Appendice A, punti 26 e 43.)

### La classe

```php
namespace App\Neuron\Rag;

use App\Neuron\ThreadScope;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Laravel\Facades\AIProvider;
use NeuronAI\Laravel\Facades\EmbeddingProvider;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\RAG\Embeddings\EmbeddingsProviderInterface;
use NeuronAI\RAG\RAG;
use NeuronAI\RAG\VectorStore\Filter\Filter;
use NeuronAI\RAG\VectorStore\Filter\FilterExpression;
use NeuronAI\RAG\VectorStore\VectorStoreInterface;

class KnowledgeBaseAgent extends RAG
{
    protected function provider(): AIProviderInterface
    {
        return AIProvider::driver();
    }

    protected function embeddings(): EmbeddingsProviderInterface
    {
        return EmbeddingProvider::driver();
    }

    protected function vectorStore(): VectorStoreInterface
    {
        return KnowledgeBase::store();
    }

    protected function retrievalScope(): ?FilterExpression
    {
        return Filter::eq('tenant_id', ThreadScope::of($this->getThreadId())->tenantId);
    }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: [
                'You answer questions using only the knowledge base articles in your context.',
                'You do not have general knowledge about this company beyond those articles.',
            ],
            steps: [
                'Read the provided articles.',
                'If they answer the question, answer and cite the article title.',
                'If they do not, say the knowledge base does not cover it and offer to '
                . 'escalate to a human.',
            ],
            output: [
                'Cite the source article for every factual claim.',
                'Keep answers under 150 words unless the user asks for detail.',
            ],
        );
    }
}
```

L'agent è costruito come il Capitolo 18 costruisce un agent: non sa nulla di chi lo chiama. Nel costruttore non c'è alcun `Tenant`; il tenant è quello indicato dal thread a cui l'agent è associato — `$agent->for($conversation->threadId())` — e `ThreadScope` (Sezione 18.3) lo rilegge. Un agent che non viene mai associato non gira affatto, perché il framework non genera alcun thread ID, quindi non c'è modo di cercare in questo store senza un tenant. La classe non dichiara `messageStore()`: una domanda alla knowledge base trova risposta negli articoli, e la conversazione resta in memoria per la durata della run. La Sezione 20.4 dà all'agent una cronologia persistente.

### Il filtro di tenant non è opzionale

`retrievalScope()` restituisce incondizionatamente il filtro di tenant, calcolato a partire dal thread, e il nodo di retrieval lo applica a ogni ricerca che questo agent esegue. Non esiste un percorso di codice che interroghi lo store senza di esso. Qualunque altra cosa aggiunga un filtro durante una run — un middleware sul nodo di retrieval, una strategia di retrieval personalizzata — viene combinata con l'ambito in AND, quindi può restringere la ricerca ma mai allargarla.

La regola della Sezione 12.6: **filtra al recupero, mai dopo.** Un documento recuperato e poi escluso dalla risposta era comunque nel contesto del modello, e i modelli parafrasano. Il filtro di tenant è l'equivalente RAG di un `where tenant_id = ?` su ogni query — e appartiene allo stesso posto, al componente che costruisce la query.

::: {.callout .callout-warning}
[`setRetrievalScope()` sostituisce l'ambito; non vi aggiunge nulla]{.callout-title}

`RAG` ha anche un setter `setRetrievalScope()`, ed è forte la tentazione di usarlo da un controller per un filtro extra occasionale. Non farlo, su questo agent. Il setter *sostituisce* ciò che restituisce `retrievalScope()` — passagli `Filter::eq('visibility', 'public')` e il filtro di tenant sparisce, e la ricerca gira sugli articoli pubblici di tutti i tenant. Tieni ogni vincolo obbligatorio dentro l'hook, calcolato a partire dal thread a cui l'agent è associato.
:::

### Scegliere uno store in Laravel

Dalla Sezione 12.5, con la lente di Laravel:

**MariaDB 11.7+** — una tabella nel database che già gestisci. Backup, monitoraggio, transazioni e failover sono già risolti. Per la maggior parte delle applicazioni Laravel è questa la risposta giusta, ed è lo store costruito qui sopra.

**Elasticsearch o Meilisearch** — se ne gestisci già uno per la ricerca del sito, usa quello ed evita un secondo sistema.

**Pinecone o Qdrant** — quando la scala richiede davvero un database dedicato.

**PHPVector** — `neuron-core/php-vector`, PHP puro, HNSW più ricerca ibrida BM25, nessun servizio. Interessante per deploy self-hosted e clienti che non possono aggiungere infrastruttura, ma nel momento in cui scriviamo non ha una release per NeuronAI v4 (Sezione 12.5). Verifica prima di contarci.

La regola generale regge: **usa ciò che già gestisci.** Qualunque tu scelga, accetta lo stesso argomento `schema:`, e gli stessi filtri portabili girano su tutti.

### Punti chiave

- Dichiara i metadati filtrabili in un `DocumentSchema`; costruisci lo store nel codice (`KnowledgeBase::store()`), non nella configurazione in cache, e una volta per risoluzione quando tiene un PDO.
- Crea la tabella in una migration con la dimensione dell'embedding fissata da entrambi i lati; imposta `NEURON_EMBEDDING_PROVIDER`.
- Metti il filtro di tenant in `retrievalScope()`, letto dal thread, così che nessun percorso lo scavalchi — e non sostituirlo mai con `setRetrievalScope()`.
- Uno store non conserva alcuno stato per ricerca: i filtri viaggiano con ogni ricerca. Se usi `VectorStore::extend()`, registra prima `VectorStoreManager` come singleton.
- MariaDB per la maggior parte delle applicazioni Laravel.

## 20.2 Ingestione in coda

### Il job

```php
<?php

declare(strict_types=1);

namespace App\Jobs;

use App\Models\Article;
use App\Neuron\Rag\KnowledgeBase;
use App\Neuron\Rag\MarkdownSectionSplitter;
use DateTimeInterface;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Contracts\Queue\ShouldQueueAfterCommit;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use NeuronAI\Laravel\Facades\EmbeddingProvider;
use NeuronAI\RAG\DataLoader\StringDataLoader;

class IndexArticle implements ShouldQueue, ShouldQueueAfterCommit
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $maxExceptions = 3;
    public int $backoff = 30;

    public function retryUntil(): DateTimeInterface
    {
        return now()->addHours(6);
    }

    public function __construct(
        public readonly Article $article,
    ) {}

    public function handle(): void
    {
        $documents = StringDataLoader::for($this->article->body)
            ->withSplitter(new MarkdownSectionSplitter(maxChars: 2000))
            ->getDocuments();

        foreach ($documents as $document) {
            $document->setSourceType('article');
            $document->setSourceName("article-{$this->article->id}");
            $document->addMetadata('tenant_id',  $this->article->tenant_id);
            $document->addMetadata('article_id', $this->article->id);
            $document->addMetadata('visibility', $this->article->visibility);
            $document->addMetadata('updated_at', $this->article->updated_at->getTimestamp());
        }

        $store    = KnowledgeBase::store();
        $embedder = EmbeddingProvider::driver();

        // Fail on a bad document before paying for its embedding
        foreach ($documents as $document) {
            $store->getSchema()->validate($document);
        }

        $store->addDocuments($embedder->embedDocuments($documents));
    }
}
```

Componenti autonomi (Sezione 12.2) invece di un agent RAG — l'ingestione non ha bisogno di un provider di chat, né di istruzioni, né di tool. Tenere il job snello significa che parte più in fretta e ha meno ragioni per fallire. `MarkdownSectionSplitter` è lo splitter della Sezione 12.3, spostato da `App\Rag` a `App\Neuron\Rag`, accanto a `KnowledgeBase`.

`ShouldQueueAfterCommit` trattiene l'invio finché la transazione di database circostante non viene confermata, e lo scarta se la transazione viene annullata. Senza, un job su una coda veloce può partire prima del commit, leggere il vecchio corpo dell'articolo e indicizzare quello, e nulla innesca una seconda esecuzione. Le impostazioni di ritentativo sono spiegate sotto "Configurazione della coda".

I metadati devono corrispondere allo schema della Sezione 20.1, e lo schema è rigoroso sui tipi: `integer` significa un `int` PHP, quindi dai ad `Article` dei cast interi per le colonne ID invece di fidarti del driver. `updated_at` è memorizzato come timestamp Unix perché i filtri di intervallo sono numerici — la Sezione 20.3 filtra su di esso. Lo store valida di nuovo ogni documento in `addDocuments()`, ma a quel punto gli embedding sono già pagati; il ciclo qui sopra fallisce prima, e gratis. (`RAG::addDocuments()` fa lo stesso controllo nello stesso ordine, ed è una delle ragioni per cui il job successivo usa l'agent.)

### Innescarlo

```php
class Article extends Model
{
    protected static function booted(): void
    {
        static::saved(function (Article $article) {
            if ($article->wasChanged('body') || $article->wasRecentlyCreated) {
                ReindexArticle::dispatch($article);
            }
        });

        static::deleted(function (Article $article) {
            RemoveArticleFromIndex::dispatch($article->id, $article->tenant_id);
        });
    }
}
```

La guardia `wasChanged('body')` conta. Senza, ogni salvataggio — l'incremento di un contatore di visualizzazioni, un tocco a un timestamp — rifà l'embedding dell'intero articolo. Sono soldi veri spesi per niente, ripetutamente.

La rimozione è una sola chiamata, perché uno store cancella per qualunque filtro lo schema consenta:

```php
public function handle(): void
{
    KnowledgeBase::store()->delete(
        Filter::where('tenant_id', $this->tenantId)->where('article_id', $this->articleId),
    );
}
```

Delimitare la cancellazione per tenant oltre che per articolo non costa nulla e significa che un bug nel chiamante non può rimuovere i chunk di un altro tenant.

### Reindicizzare invece di aggiungere

```php
class ReindexArticle implements ShouldQueue, ShouldQueueAfterCommit
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    // $maxExceptions, $backoff, retryUntil() and the constructor, as in IndexArticle

    public function handle(): void
    {
        $documents = StringDataLoader::for($this->article->body)
            ->withSplitter(new MarkdownSectionSplitter(maxChars: 2000))
            ->getDocuments();

        foreach ($documents as $document) {
            $document->setSourceType('article');
            $document->setSourceName("article-{$this->article->id}");   // stable — the ID, never the title
            $document->addMetadata('tenant_id',  $this->article->tenant_id);
            $document->addMetadata('article_id', $this->article->id);
            $document->addMetadata('visibility', $this->article->visibility);
            $document->addMetadata('updated_at', $this->article->updated_at->getTimestamp());
        }

        KnowledgeBaseAgent::make()->reindexBySource($documents);
    }
}
```

`reindexBySource()` valida l'intero batch, calcola gli embedding dei chunk di ciascuna sorgente, e solo dopo cancella tutto ciò che è memorizzato sotto il `sourceType` e il `sourceName` di quella sorgente e aggiunge i nuovi chunk. Una validazione fallita o una chiamata di embedding fallita lasciano la vecchia versione nell'indice, intatta. È per via dello schema che ogni riga di metadati viene ripetuta qui: togli la riga `tenant_id` e il job fallisce prima di calcolare qualunque embedding, invece di scrivere chunk che nessun tenant può recuperare.

Il vincolo della Sezione 12.6, ribadito perché è facile sbagliarlo: **`sourceName` deve essere stabile.** Usa l'ID dell'articolo. Ricavalo dal titolo e una rinomina redazionale lascerà orfani i vecchi chunk — restano nell'indice, non cancellabili per sorgente, e l'agent risponde attingendo a entrambe le versioni.

Dagli un prefisso — `article-42` anziché `42`. Un numero nudo funziona, ma il prefisso dice che genere di cosa è la sorgente quando leggi l'indice.

### Configurazione della coda

**Una coda dedicata.** L'embedding è lento; non lasciare che ritardi le email di reimpostazione password.

```php
ReindexArticle::dispatch($article)->onQueue('indexing');
```

**Rate limit.** I provider di embedding ne hanno. Una reindicizzazione massiva di 10.000 articoli ne colpirà uno.

```php
public function middleware(): array
{
    return [new RateLimited('embeddings')];
}
```

(`RateLimited` è `Illuminate\Queue\Middleware\RateLimited`, e il limiter `embeddings` si definisce con `RateLimiter::for()` in un service provider.)

**Backfill a blocchi.** Per l'indicizzazione iniziale, usa `chunkById()` e invia a lotti invece di caricare tutto in memoria.

**Ritentativi.** I fallimenti transitori dei provider sono normali, quindi i job impostano `$backoff = 30` e `$maxExceptions = 3`: tre fallimenti veri chiudono il job. Non contare i tentativi con `$tries = 3` su un job che usa `RateLimited`: ogni volta che il limiter rilascia il job consuma un tentativo, quindi un backfill di 10.000 articoli vedrebbe i suoi job fallire dopo tre rilasci senza un solo errore. `retryUntil()` limita invece il job nel tempo, e `$maxExceptions` conta solo le eccezioni.

### Il modo di fallire per cui pianificare

Un job di indicizzazione fallisce silenziosamente e l'articolo non entra mai nell'indice. L'agent poi risponde "la knowledge base non copre questo argomento" per contenuti che esistono — cosa che sembra un problema di qualità del RAG ed è in realtà un problema operativo.

Tienilo tracciato:

```php
// last lines of handle(), in both jobs
$this->article->timestamps = false;
$this->article->forceFill(['indexed_at' => $this->article->updated_at])->saveQuietly();
```

```php
Article::whereNull('indexed_at')
       ->orWhereColumn('indexed_at', '<', 'updated_at')
       ->count();
```

`indexed_at` registra quale versione dell'articolo è arrivata nell'indice: copia l'`updated_at` che il job ha letto all'inizio. Un semplice `update(['indexed_at' => now()])` sposterebbe anche `updated_at`, e la query dell'alert potrebbe segnalare un articolo sano — oppure nascondere una modifica fatta mentre il job girava; `saveQuietly()` evita inoltre che il salvataggio faccia scattare di nuovo gli eventi del model. Un solo numero, su cui puoi mettere un alert. Costruiscilo adesso — è la differenza fra una demo e un sistema, e nessuno ci pensa fino al primo ticket di supporto.

### Punti chiave

- Fai l'ingestione con componenti autonomi dentro un job in coda, inviato dopo il commit.
- Metti una guardia su `wasChanged()` — non rifare l'embedding a ogni salvataggio.
- Rispetta lo schema: campi obbligatori presenti, interi come `int`, date come timestamp.
- `reindexBySource()` con un ID stabile e prefissato come `sourceName`; cancella per filtro.
- Coda dedicata, rate limit, backfill a blocchi, ritentativi limitati da `retryUntil()` e `$maxExceptions`, non da `$tries`.
- Traccia `indexed_at` e metti un alert sullo scarto.

## 20.3 Recupero consapevole dei permessi

### Il problema

La tua knowledge base ha articoli pubblici, articoli riservati ai clienti e runbook interni. Tutti in un solo indice.

Un cliente fa una domanda. Se il recupero pesca un runbook interno e quello entra nel contesto, il modello potrebbe parafrasarlo dentro la risposta. L'utente non ha mai visto il documento, ma ne ha ottenuto il contenuto.

**È una violazione dei dati, e nei tuoi log non sembra tale.** Nessun documento è stato renderizzato, nessun endpoint è stato chiamato — la fuga è avvenuta dentro una parafrasi.

### La correzione

Il thread nomina già l'utente che fa la richiesta accanto al tenant, quindi l'ambito cresce di una condizione e l'agent continua a non prendere nulla nel costruttore:

```php
protected function retrievalScope(): ?FilterExpression
{
    $scope = ThreadScope::of($this->getThreadId());

    return Filter::where('tenant_id', $scope->tenantId)
        ->whereIn('visibility', $this->allowedVisibilities($scope));
}

private function allowedVisibilities(ThreadScope $scope): array
{
    $user = User::where('tenant_id', $scope->tenantId)->findOrFail($scope->userId);

    return match (true) {
        $user->hasRole('staff')    => ['public', 'customer', 'internal'],
        $user->hasRole('customer') => ['public', 'customer'],
        default                    => ['public'],
    };
}
```

Il ruolo viene letto dal database, per ID, per l'utente che il thread nomina, e l'utente deve appartenere al tenant che il thread nomina. Ciò di cui la richiesta è creduta è il thread stesso: il controller ha autorizzato la conversazione (Sezione 18.2) prima di associarle l'agent.

Il recupero non restituisce mai ciò che l'utente non può vedere. Il filtro è calcolato a partire dall'attore, applicato allo store. `Filter::where()` apre una catena in AND; `whereIn()` corrisponde a uno qualunque dei valori elencati. Entrambi i campi sono dichiarati filtrabili nello schema della Sezione 20.1 — filtra su un campo che lo schema non dichiara e lo store lancia una `DocumentSchemaException` prima di toccare il database, che è esattamente il fallimento che vuoi.

### La regola, ancora una volta

**Filtra al recupero, mai dopo.**

Il post-filtraggio — recupera tutto, poi scarta ciò che l'utente non può vedere prima di mostrarlo — fallisce perché il modello lo ha già letto. L'unico punto sicuro è prima che la ricerca vettoriale restituisca.

È la regola di sicurezza del RAG più conseguente, e non è ovvia.

### Testarla

```php
public function test_customer_cannot_retrieve_internal_articles(): void
{
    $this->indexArticle('Internal escalation runbook', visibility: 'internal',
        body: 'The emergency override code is OMEGA-7.');

    $answer = app(KnowledgeBaseAgent::class)
        ->for($customerConversation->threadId())
        ->chat(new UserMessage('What is the emergency override code?'))
        ->getMessage()
        ?->getContent();

    $this->assertStringNotContainsString('OMEGA-7', (string) $answer);
}
```

(`$customerConversation` è una conversazione di un cliente del tenant, `$staffConversation` una di un membro dello staff.) Un token distintivo in un documento riservato, e un'asserzione che non emerga mai. È il testing per contratto della Sezione 1.5 applicato alla sicurezza: non puoi fare asserzioni sulla formulazione della risposta, ma puoi fare asserzioni su ciò che non deve mai comparirvi.

Eseguilo in CI. È uno dei pochi test AI abbastanza deterministico da meritare fiducia e abbastanza importante da bloccare un deploy.

Puoi renderlo del tutto deterministico facendo l'asserzione un passo prima — su ciò che ha raggiunto il modello, non su ciò che il modello ha detto. I documenti recuperati vengono iniettati nelle istruzioni, quindi dai all'agent dei fake per tutto ciò che uscirebbe dal processo — il `FakeAIProvider` del framework per il modello, `FakeEmbeddingsProvider` per l'embedder e uno store in memoria — e controlla il system prompt che il provider ha registrato:

```php
$embeddings = new FakeEmbeddingsProvider();
$store      = new MemoryVectorStore(schema: KnowledgeBase::schema());

$runbook = new Document('The emergency override code is OMEGA-7.');
$runbook->addMetadata('tenant_id',  $tenant->id);
$runbook->addMetadata('article_id', 1);
$runbook->addMetadata('visibility', 'internal');
$store->addDocuments($embeddings->embedDocuments([$runbook]));

$ask = function (Conversation $conversation) use ($embeddings, $store): FakeAIProvider {
    $provider = new FakeAIProvider(new AssistantMessage('I cannot help with that.'));

    app(KnowledgeBaseAgent::class)
        ->setAiProvider($provider)
        ->setEmbeddingsProvider($embeddings)
        ->setVectorStore($store)
        ->for($conversation->threadId())
        ->chat(new UserMessage('What is the emergency override code?'));

    return $provider;
};

$ask($customerConversation)->assertSent(
    fn (RequestRecord $request): bool => !$request->systemPrompt?->contains('OMEGA-7')
);

// The control: the same store and question for staff does retrieve it
$ask($staffConversation)->assertSent(
    fn (RequestRecord $request): bool => $request->systemPrompt?->contains('OMEGA-7') === true
);
```

Nessun modello, nessuna rete, nessun database per la ricerca, nessuna instabilità: se il chunk riservato è stato recuperato per il cliente, il test fallisce ogni volta. Il controllo con lo staff conta quanto l'asserzione che protegge. Un test che simula solo il provider di chat chiamerebbe comunque il vero embedder e il vero store; e un test che non dimostra mai che il documento *può* essere recuperato passa con la stessa tranquillità quando lo store è vuoto.

### Filtri di freschezza

Lo stesso meccanismo gestisce i contenuti superati:

```php
return Filter::where('tenant_id', ThreadScope::of($this->getThreadId())->tenantId)
    ->whereGreaterThanOrEqual('updated_at', now()->subYear());
```

La sintassi è portabile: la stessa espressione si compila per MariaDB, Meilisearch, Pinecone o qualunque altro store incluso. I filtri di intervallo sono numerici, e una data passata a uno di essi viene normalizzata in un timestamp Unix — ed è per questo che la Sezione 20.2 ha memorizzato `updated_at` con `getTimestamp()`. Una data memorizzata come `'2026-01-31'` non potrebbe proprio essere filtrata per intervallo.

Utile quando vecchia e nuova versione di una policy vivono entrambe nell'indice e vuoi che il modello preferisca quella corrente.

### Punti chiave

- Un indice, più livelli di visibilità — o filtri o perdi dati.
- Una fuga per parafrasi è invisibile nei tuoi log.
- Calcola le visibilità permesse a partire dall'attore; applicale in `retrievalScope()`.
- Testa con un token distintivo in un documento riservato; eseguilo in CI — con il fake provider è del tutto deterministico.
- Filtri portabili: intervalli numerici, date come timestamp, ogni campo dichiarato nello schema.

## 20.4 Combinare RAG e tool

### Le due domande

- *"Qual è la vostra politica di rimborso?"* → prosa in un documento → **RAG**
- *"Il mio ordine #4471 è stato rimborsato?"* → una riga in una tabella → **tool**

La Sezione 11.4 ha fatto la distinzione. Qui diventa una classe sola, perché `RAG` estende `Agent` (Sezione 12.1).

### L'agent

```php
class SupportAgent extends RAG
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

    protected function embeddings(): EmbeddingsProviderInterface
    {
        return EmbeddingProvider::driver();
    }

    protected function vectorStore(): VectorStoreInterface
    {
        return KnowledgeBase::store();
    }

    protected function messageStore(): MessageStoreInterface
    {
        return $this->conversations;
    }

    protected function persistence(): PersistenceInterface
    {
        return $this->runs;
    }

    protected function contextWindow(): int
    {
        return config('neuron.context_windows.' . config('neuron.provider.default'), 29_000);
    }

    protected function retrievalScope(): ?FilterExpression
    {
        $scope = ThreadScope::of($this->getThreadId());

        return Filter::where('tenant_id', $scope->tenantId)
            ->whereIn('visibility', $this->allowedVisibilities($scope));
    }

    protected function tools(): array
    {
        $scope = ThreadScope::of($this->getThreadId());
        $user  = User::where('tenant_id', $scope->tenantId)->findOrFail($scope->userId);

        return [
            new SearchOrdersTool($scope->tenantId),
            new GetOrderStatusTool($scope->tenantId),

            (new RequestRefundTool($scope->tenantId, $scope->userId))
                ->visible(Gate::forUser($user)->allows('create', Refund::class))
                ->setMaxRuns(1),
        ];
    }

    // allowedVisibilities() as in Section 20.3

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: [
                'You are a customer support assistant.',
                'Policy questions are answered from the knowledge base articles in your context.',
                'Questions about specific orders are answered by calling your tools.',
            ],
            steps: [
                'Decide whether the question is about policy or about specific order data.',
                'For policy: answer from the provided articles and cite the article title.',
                'For order data: call the appropriate tool. Never state order details you '
                . 'have not retrieved with a tool.',
                'If neither source answers the question, offer to escalate to a human.',
            ],
            output: [
                'Answer in the user\'s language.',
                'Under 150 words unless detail is requested.',
                'Never state a monetary amount you did not retrieve from a tool.',
            ],
        );
    }
}
```

Questo è il `SupportAgent` del Capitolo 18 con la classe base cambiata da `Agent` a `RAG` e i tre hook RAG aggiunti: gli stessi due store iniettati, lo stesso `ThreadScope`, lo stesso `for($conversation->threadId())` nel controller. L'agent non conosce il contesto; tenant e utente vengono fuori dal thread, e i tool ricevono ID scalari.

### L'istruzione che lavora di più

> *"Never state order details you have not retrieved with a tool."*

E la sua sorella più forte:

> *"Never state a monetary amount you did not retrieve from a tool."*

Senza queste, il modello produrrà con sicurezza lo stato di un ordine o l'importo di un rimborso dal nulla, perché in addestramento ha visto migliaia di conversazioni di supporto e sa che aspetto hanno.

**Le istruzioni anti-allucinazione devono essere specifiche sulla classe di fatti.** "Sii accurato" non fa nulla. "Non dichiarare mai un importo monetario che non hai recuperato" è azionabile, verificabile e — con il `FaithfulnessJudge` della Sezione 10.5 — misurabile.

### Una classe, quasi tutto il libro

Conta che cosa c'è dentro: astrazione del provider (3.6), struttura del system prompt (3.5), un thread che fa da chiave sia per la cronologia della conversazione sia per qualunque approvazione di rimborso in pausa e porta il tenant e l'utente (4.3, 18.2, 18.3), tool con dipendenze (5.3), visibilità dei tool (5.10), limiti di esecuzione (5.9), recupero RAG (12.1), filtri di permesso (20.3) e un contratto anti-allucinazione (11.5).

Sette capitoli in una sola classe. Vale la pena fermarsi un attimo: il libro compone invece di accumulare, e questa classe ne è la prova.

### Punti chiave

- RAG estende Agent, quindi recupero e tool vivono in una classe sola.
- Di' al modello quale sorgente risponde a quale tipo di domanda.
- Le istruzioni anti-allucinazione devono nominare la classe di fatti.
- Tutto ciò che viene dalle Parti da II a IV si compone in un unico agent.

## Laboratorio 14 — La knowledge base aziendale

**Copre:** RAG sui dati dell'applicazione, ingestione in coda, filtri di permesso, citazioni.

### Obiettivo

Gli articoli della knowledge base vivono in Eloquent. Vengono indicizzati automaticamente quando cambiano, risposti con citazioni, e mai recuperabili da chi non dovrebbe vederli.

### Requisiti

1. **Una tabella `articles`** con `body`, `title`, `tenant_id`, `visibility` (`public` / `customer` / `internal`) e `indexed_at`.
2. **Indicizzazione automatica** al salvataggio, protetta da `wasChanged('body')`, inviata a una coda `indexing` dedicata con ritentativi e rate limit.
3. **`reindexBySource()`** usando l'ID prefissato dell'articolo (`article-42`) come nome stabile della sorgente, su uno store il cui `DocumentSchema` dichiara ogni campo su cui filtri e la cui tabella è creata da una migration con la dimensione dell'embedding fissata. Modificare un articolo deve sostituirne i chunk, non aggiungersi a essi.
4. **La cancellazione** rimuove i chunk dell'articolo dall'indice.
5. **Recupero consapevole dei permessi** come nella Sezione 20.3, calcolato dal ruolo dell'utente richiedente.
6. **Citazioni.** Ogni affermazione fattuale in una risposta nomina l'articolo di origine. Se la knowledge base non copre la domanda, l'agent lo dice e offre l'escalation.

### Criteri di accettazione

- Modificare un articolo e chiedere del passaggio cambiato restituisce il nuovo contenuto, e una frase che hai cancellato non è più recuperabile.
- Un cliente non può ottenere il contenuto di un articolo `internal`, testato con un token distintivo come nella Sezione 20.3.
- `Article::whereNull('indexed_at')->orWhereColumn('indexed_at', '<', 'updated_at')->count()` restituisce zero dopo che la coda si è svuotata — e hai un alert per quando non lo fa.
- Toccare un articolo senza cambiarne il corpo non invia alcun job di indicizzazione. Fai l'asserzione sulla coda, non sui log.
- Una domanda fuori ambito produce l'offerta di escalation, non una risposta inventata.

### La misurazione

Costruisci un set di valutazione da quindici domande sui tuoi articoli reali, con un'asserzione `FaithfulnessJudge` (Sezione 10.5). Registra il punteggio prima e dopo il passaggio a uno splitter consapevole delle intestazioni.

Quel numero è ciò che mostri a uno stakeholder. "L'agent della knowledge base risponde in modo fedele nell'0,87 dei casi, misurato su quindici domande rappresentative, ed ecco l'andamento da quando abbiamo cambiato il chunking" è una conversazione fondamentalmente diversa da "sembra abbastanza buono".

### Andare oltre

Aggiungi il percorso di escalation per davvero: quando l'agent offre l'escalation e l'utente accetta, crea un ticket di supporto che contiene la domanda, gli articoli recuperati e la risposta dell'agent. Hai appena costruito la prima metà del Progetto finale B.
