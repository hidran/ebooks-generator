# Capitolo 20 — RAG sui dati dell'applicazione

## 20.1 Un agent RAG in Laravel

### La classe

```php
namespace App\Neuron\Rag;

use App\Models\Tenant;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Laravel\Facades\AIProvider;
use NeuronAI\Laravel\Facades\EmbeddingProvider;
use NeuronAI\Laravel\Facades\VectorStore;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\RAG\Embeddings\EmbeddingsProviderInterface;
use NeuronAI\RAG\RAG;
use NeuronAI\RAG\VectorStore\VectorStoreInterface;

class KnowledgeBaseAgent extends RAG
{
    protected array $vectorStoreFilters = [];

    public function __construct(
        private readonly Tenant $tenant,
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
        $store = VectorStore::driver();

        return $store->withFilters(\array_merge(
            ['tenant_id' => $this->tenant->id],
            $this->vectorStoreFilters,
        ));
    }

    public function addVectorStoreFilters(array $filters): self
    {
        $this->vectorStoreFilters = $filters;

        return $this;
    }

    public function instructions(): string
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

### Il filtro di tenant non è opzionale

`withFilters(['tenant_id' => $this->tenant->id])` viene applicato incondizionatamente in `vectorStore()`, fuso con eventuali filtri a runtime. Non esiste un percorso di codice che interroghi lo store senza di esso.

La regola della Sezione 12.6: **filtra al recupero, mai dopo.** Un documento recuperato e poi escluso dalla risposta era comunque nel contesto del modello, e i modelli parafrasano. Il filtro di tenant è l'equivalente RAG di un `where tenant_id = ?` su ogni query — e appartiene allo stesso posto, al componente che costruisce la query.

::: {.callout .callout-warning}
[Verifica il nome del metodo e l'elenco dei driver]{.callout-title}

`withFilters()` contro `withFilter()` resta irrisolto nella documentazione (Appendice A, punti 26 e 43), e l'insieme di driver di vector store che `VectorStore::driver()` espone davvero dipende dal tuo `config/neuron.php` pubblicato (punto 44). Conferma entrambe le cose prima di costruirci sopra l'ingestione.
:::

### Scegliere uno store in Laravel

Dalla Sezione 12.5, con la lente di Laravel:

**MariaDB 11.7+** — una tabella nel database che già gestisci. Backup, monitoraggio, transazioni e failover sono già risolti. Per la maggior parte delle applicazioni Laravel è questa la risposta giusta.

**PHPVector** — `neuron-core/php-vector`, PHP puro, HNSW più ricerca ibrida BM25, nessun servizio. Ottimo per deploy self-hosted e clienti che non possono aggiungere infrastruttura.

**Elasticsearch o Meilisearch** — se ne gestisci già uno per la ricerca del sito, usa quello ed evita un secondo sistema.

**Pinecone o Qdrant** — quando la scala richiede davvero un database dedicato.

La regola generale regge: **usa ciò che già gestisci.**

### Punti chiave

- Tre facade, tre chiamate a `driver()`, tutto il resto in configurazione.
- Applica il filtro di tenant dentro `vectorStore()` così che nessun percorso lo scavalchi.
- MariaDB o PHPVector per la maggior parte delle applicazioni Laravel.

## 20.2 Ingestione in coda

### Il job

```php
<?php

declare(strict_types=1);

namespace App\Jobs;

use App\Models\Article;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use NeuronAI\Laravel\Facades\EmbeddingProvider;
use NeuronAI\Laravel\Facades\VectorStore;
use NeuronAI\RAG\DataLoader\StringDataLoader;

class IndexArticle implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $tries = 3;
    public int $backoff = 30;

    public function __construct(
        public readonly Article $article,
    ) {}

    public function handle(): void
    {
        $documents = StringDataLoader::for($this->article->body)
            ->withSplitter(new MarkdownSectionSplitter(maxChars: 2000))
            ->getDocuments();

        foreach ($documents as $document) {
            $document->addMetadata('tenant_id',  $this->article->tenant_id);
            $document->addMetadata('article_id', $this->article->id);
            $document->addMetadata('visibility', $this->article->visibility);
            $document->addMetadata('updated_at', $this->article->updated_at->toDateString());
        }

        $store    = VectorStore::driver();
        $embedder = EmbeddingProvider::driver();

        $store->addDocuments($embedder->embedDocuments($documents));
    }
}
```

Componenti autonomi (Sezione 12.2) invece di un agent RAG — l'ingestione non ha bisogno di un provider di chat, né di istruzioni, né di tool. Tenere il job snello significa che parte più in fretta e ha meno ragioni per fallire.

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

### Reindicizzare invece di aggiungere

```php
class ReindexArticle implements ShouldQueue
{
    public function handle(): void
    {
        $documents = StringDataLoader::for($this->article->body)->getDocuments();

        foreach ($documents as $document) {
            $document->addMetadata('tenant_id', $this->article->tenant_id);
            // sourceName must be stable — the ID, never the title
        }

        (new KnowledgeBaseAgent($this->article->tenant))
            ->reindexBySource($documents);
    }
}
```

Il vincolo della Sezione 12.6, ribadito perché è facile sbagliarlo: **`sourceName` deve essere stabile.** Usa l'ID dell'articolo. Ricavalo dal titolo e una rinomina redazionale lascerà orfani i vecchi chunk — restano nell'indice, non cancellabili per sorgente, e l'agent risponde attingendo a entrambe le versioni.

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

**Backfill a blocchi.** Per l'indicizzazione iniziale, usa `chunkById()` e invia a lotti invece di caricare tutto in memoria.

**Ritentativi con backoff.** `$tries = 3`, `$backoff = 30`. I fallimenti transitori dei provider sono normali.

### Il modo di fallire per cui pianificare

Un job di indicizzazione fallisce silenziosamente e l'articolo non entra mai nell'indice. L'agent poi risponde "la knowledge base non copre questo argomento" per contenuti che esistono — cosa che sembra un problema di qualità del RAG ed è in realtà un problema operativo.

Tienilo tracciato:

```php
$article->update(['indexed_at' => now()]);
```

```php
Article::whereNull('indexed_at')
       ->orWhereColumn('indexed_at', '<', 'updated_at')
       ->count();
```

Un solo numero, su cui puoi mettere un alert. Costruiscilo adesso — è la differenza fra una demo e un sistema, e nessuno ci pensa fino al primo ticket di supporto.

### Punti chiave

- Fai l'ingestione con componenti autonomi dentro un job in coda.
- Metti una guardia su `wasChanged()` — non rifare l'embedding a ogni salvataggio.
- `reindexBySource()` con un ID stabile come `sourceName`.
- Coda dedicata, rate limit, backfill a blocchi, ritentativi.
- Traccia `indexed_at` e metti un alert sullo scarto.

## 20.3 Recupero consapevole dei permessi

### Il problema

La tua knowledge base ha articoli pubblici, articoli riservati ai clienti e runbook interni. Tutti in un solo indice.

Un cliente fa una domanda. Se il recupero pesca un runbook interno e quello entra nel contesto, il modello potrebbe parafrasarlo dentro la risposta. L'utente non ha mai visto il documento, ma ne ha ottenuto il contenuto.

**È una violazione dei dati, e nei tuoi log non sembra tale.** Nessun documento è stato renderizzato, nessun endpoint è stato chiamato — la fuga è avvenuta dentro una parafrasi.

### La correzione

```php
protected function vectorStore(): VectorStoreInterface
{
    return VectorStore::driver()->withFilters([
        'tenant_id'  => $this->tenant->id,
        'visibility' => $this->allowedVisibilities(),
    ]);
}

private function allowedVisibilities(): array
{
    return match (true) {
        $this->user->hasRole('staff')    => ['public', 'customer', 'internal'],
        $this->user->hasRole('customer') => ['public', 'customer'],
        default                          => ['public'],
    };
}
```

Il recupero non restituisce mai ciò che l'utente non può vedere. Il filtro è calcolato a partire dall'attore, applicato allo store.

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

    $answer = (new KnowledgeBaseAgent($tenant, $customerUser))
        ->chat(new UserMessage('What is the emergency override code?'))
        ->getMessage()
        ->getContent();

    $this->assertStringNotContainsString('OMEGA-7', $answer);
}
```

Un token distintivo in un documento riservato, e un'asserzione che non emerga mai. È il testing per contratto della Sezione 1.5 applicato alla sicurezza: non puoi fare asserzioni sulla formulazione della risposta, ma puoi fare asserzioni su ciò che non deve mai comparirvi.

Eseguilo in CI. È uno dei pochi test AI abbastanza deterministico da meritare fiducia e abbastanza importante da bloccare un deploy.

### Filtri di freschezza

Lo stesso meccanismo gestisce i contenuti superati:

```php
->withFilters([
    'tenant_id'  => $this->tenant->id,
    'updated_at' => ['$gte' => now()->subYear()->toDateString()],
])
```

La sintassi dei filtri è specifica dello store — consulta la documentazione del tuo.

Utile quando vecchia e nuova versione di una policy vivono entrambe nell'indice e vuoi che il modello preferisca quella corrente.

### Punti chiave

- Un indice, più livelli di visibilità — o filtri o perdi dati.
- Una fuga per parafrasi è invisibile nei tuoi log.
- Calcola le visibilità permesse a partire dall'attore; applicale allo store.
- Testa con un token distintivo in un documento riservato; eseguilo in CI.

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
        private readonly Tenant $tenant,
        private readonly User $user,
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
        return VectorStore::driver()->withFilters([
            'tenant_id'  => $this->tenant->id,
            'visibility' => $this->allowedVisibilities(),
        ]);
    }

    protected function tools(): array
    {
        return [
            new SearchOrdersTool($this->tenant),
            new GetOrderStatusTool($this->tenant),

            (new RequestRefundTool($this->refunds, $this->user))
                ->visible($this->user->can('create', Refund::class))
                ->setMaxRuns(1),
        ];
    }

    protected function chatHistory(): ChatHistoryInterface
    {
        return new EloquentChatHistory(
            thread_id: "t{$this->tenant->id}:u{$this->user->id}",
            modelClass: ChatMessage::class,
            contextWindow: config('neuron.context_window'),
        );
    }

    public function instructions(): string
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

### L'istruzione che lavora di più

> *"Never state order details you have not retrieved with a tool."*

E la sua sorella più forte:

> *"Never state a monetary amount you did not retrieve from a tool."*

Senza queste, il modello produrrà con sicurezza lo stato di un ordine o l'importo di un rimborso dal nulla, perché in addestramento ha visto migliaia di conversazioni di supporto e sa che aspetto hanno.

**Le istruzioni anti-allucinazione devono essere specifiche sulla classe di fatti.** "Sii accurato" non fa nulla. "Non dichiarare mai un importo monetario che non hai recuperato" è azionabile, verificabile e — con il `FaithfulnessJudge` della Sezione 10.5 — misurabile.

### Una classe, quasi tutto il libro

Conta che cosa c'è dentro: astrazione del provider (3.6), struttura del system prompt (3.5), cronologia chat con isolamento per tenant (4.3, 18.3), tool con dipendenze (5.3), visibilità dei tool (5.10), limiti di esecuzione (5.9), recupero RAG (12.1), filtri di permesso (20.3) e un contratto anti-allucinazione (11.5).

Nove capitoli in quaranta righe. Vale la pena fermarsi un attimo: il libro compone invece di accumulare, e questa classe ne è la prova.

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
3. **`reindexBySource()`** usando l'ID dell'articolo come nome stabile della sorgente. Modificare un articolo deve sostituirne i chunk, non aggiungersi a essi.
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
