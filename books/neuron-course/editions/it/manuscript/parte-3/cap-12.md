# Capitolo 12 — La pipeline RAG di NeuronAI

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

La versione eseguibile di ogni listato che segue si trova in [`chapters/Ch12`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch12), nel repository di accompagnamento. Clonalo, esegui `composer install` e gli esempi funzionano su un Ollama locale senza alcuna API key.
:::

## 12.1 La classe RAG

### Generarla

```bash
# Unix
vendor/bin/neuron make:rag App\\Neuron\\MyChatBot

# Windows
.\vendor\bin\neuron make:rag App\Neuron\MyChatBot
```

### La classe

```php
namespace App\Neuron;

use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Providers\Anthropic\Anthropic;
use NeuronAI\RAG\Embeddings\EmbeddingsProviderInterface;
use NeuronAI\RAG\Embeddings\OpenAIEmbeddingsProvider;
use NeuronAI\RAG\RAG;
use NeuronAI\RAG\VectorStore\FileVectorStore;
use NeuronAI\RAG\VectorStore\VectorStoreInterface;

class MyChatBot extends RAG
{
    protected function provider(): AIProviderInterface
    {
        return new Anthropic(
            key: 'ANTHROPIC_API_KEY',
            model: 'ANTHROPIC_MODEL',
        );
    }

    protected function embeddings(): EmbeddingsProviderInterface
    {
        return new OpenAIEmbeddingsProvider(
            key: 'OPENAI_API_KEY',
            model: 'OPENAI_MODEL'
        );
    }

    protected function vectorStore(): VectorStoreInterface
    {
        return new FileVectorStore(
            directory: __DIR__,
            name: 'demo'
        );
    }
}
```

Tre metodi invece dell'unico dell'Agent. Stessa forma, due componenti in più:

- `provider()` — il modello di chat, come prima
- `embeddings()` — trasforma il testo in vettori
- `vectorStore()` — li conserva e li cerca

**Nota che si tratta di due modelli diversi.** Il tuo provider potrebbe essere Claude; il tuo provider di embedding potrebbe essere OpenAI o un modello locale Ollama. Sono scelte indipendenti, e mescolarle è normale, non un errore.

### Usarla

```php
use App\Neuron\MyChatBot;
use NeuronAI\Chat\Messages\UserMessage;

$state = MyChatBot::make()
    ->chat(new UserMessage('I want to know more about Inspector AI Bug Fix.'));

echo $state->getMessage()?->getContent();
```

`chat()` — lo stesso metodo di un agent ordinario, che restituisce lo stesso `AgentState` finale. Il retrieval avviene dentro, automaticamente. Dal lato chiamante, un agent RAG e un agent normale sono indistinguibili. (`getMessage()` è nullable perché una run che si è messa in pausa prima di qualunque inferenza — un tool in attesa di approvazione, per esempio — non ha ancora una risposta; da qui il `?->`.)

### RAG *è* un Agent

È la Sezione 2.3 che arriva per la terza volta, e ha conseguenze pratiche:

> La classe `RAG` di NeuronAI estende la classe base `Agent`. Il tuo RAG è sempre un agent, quindi puoi collegare tool e definire istruzioni di sistema.

Il che significa che un agent RAG eredita, gratis:

- `instructions()` e `SystemPrompt`
- `tools()` e i toolkit
- `chatHistory()`
- `structured()`
- `stream()`
- `subscribe()` per gli eventi di tracing
- identità del thread, persistenza e ripresa
- Tutto ciò che c'è nei Capitoli da 3 a 10

### Il pattern combinato

L'esempio della documentazione è buono — consigli di allenamento da una base di conoscenza, più un tool per lo stato attuale dell'utente:

```php
class WorkoutTipsAgent extends RAG
{
    protected function provider(): AIProviderInterface { /* ... */ }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: ['You are an AI Agent specialized in providing workout tips.'],
        );
    }

    protected function embeddings(): EmbeddingsProviderInterface { /* ... */ }

    protected function vectorStore(): VectorStoreInterface { /* ... */ }

    protected function tools(): array
    {
        return [
            CalculatorToolkit::make(),
        ];
    }
}
```

Conoscenza dal retrieval, fatti dai tool, aritmetica dal toolkit. È il "si compongono" della Sezione 11.4, in una sola classe.

::: {.callout .callout-warning}
[La firma del vector store — controllala prima di scrivere qualunque cosa]{.callout-title}

La documentazione ha mostrato `FileVectorStore` in vari modi su varie pagine — `name:` in una, `topK:` in un'altra, e a un certo punto un argomento `key:` sotto un nome di classe scritto male, `FileVectoreStore`. Lo stesso per `OpenAIEmbeddingsProvider` contro `OpenAIEmbeddingProvider`, e `RAG\Embeddings\` contro `RAG\EmbeddingProvider\`. Appendice A, punti dal 22 al 25.

Il sorgente chiude la questione. Il costruttore è `FileVectorStore(string $directory, int $topK = 4, string $name = 'neuron', string $ext = '.store', ?DocumentSchema $schema = null)` — non esiste `key:` — e le classi di embedding stanno in `NeuronAI\RAG\Embeddings\`, con la `s`. È il codice a più alto traffico della Parte III: apri la classe nel tuo editor e controllala prima di scrivere uno script di ingestion, non dopo.
:::

### Punti chiave

- Tre metodi: `provider()`, `embeddings()`, `vectorStore()`.
- Il modello di chat e quello di embedding sono scelte indipendenti.
- `chat()` restituisce lo stesso `AgentState` di qualunque agent; il retrieval è interno.
- Il RAG eredita ogni funzionalità dell'Agent, tool inclusi.

## 12.2 Data loader e reader

### La riga singola

```php
use App\Neuron\MyRAG;
use NeuronAI\RAG\DataLoader\FileDataLoader;

MyRAG::make()->addDocuments(
    FileDataLoader::for(__DIR__.'/my-article.md')->getDocuments()
);
```

Carica, dividi, calcola gli embedding, conserva — quattro operazioni, un'istruzione.

### FileDataLoader

Puntalo a un file o a una cartella:

```php
// A single file
$documents = FileDataLoader::for(__DIR__.'/my-article.md')->getDocuments();

// Every file in a directory
$documents = FileDataLoader::for(__DIR__)->getDocuments();
```

Per default legge il contenuto dei file come testo semplice. Non tutti i formati sono testo semplice, ed è a questo che servono i reader.

### Reader

**Ogni reader è legato a un'estensione di file.** Il loader sceglie automaticamente quello giusto in base a ciò che trova.

**PDF:**

```php
$documents = FileDataLoader::for(__DIR__)
    ->addReader('pdf', new \NeuronAI\RAG\DataLoader\PdfReader())
    ->getDocuments();
```

Richiede l'utility **poppler** (`pdftotext`) sul sistema. Una dipendenza di sistema, non di Composer — ed è il motivo per cui qui "funziona sulla mia macchina" di solito significa "poppler è installato sulla mia macchina".

```bash
sudo apt install poppler-utils    # Debian/Ubuntu
brew install poppler              # macOS
```

**HTML:**

```php
$documents = FileDataLoader::for(__DIR__)
    ->addReader(['html', 'xhtml'], new \NeuronAI\RAG\DataLoader\HtmlReader())
    ->getDocuments();
```

Richiede `mtibben/html2text`:

```bash
composer require mtibben/html2text
```

Nota che converte l'HTML **in Markdown** invece di rimuovere i tag. Conta: le intestazioni sopravvivono come `##`, il che significa che uno splitter consapevole delle intestazioni (Sezione 12.3) può usarle. Ridurre a testo semplice butterebbe via quella struttura.

Un'estensione può mappare su più reader, o più estensioni su un solo reader — `['html', 'xhtml']` qui sopra.

### StringDataLoader

Per testo che hai già — da un database, un'API, un editor:

```php
use NeuronAI\RAG\DataLoader\StringDataLoader;

$contents = [
    // list of strings (text you want to embed)
];

foreach ($contents as $text) {
    $documents = StringDataLoader::for($text)->getDocuments();

    MyRAG::make()->addDocuments($documents);
}
```

**È il loader che userai di più in un'applicazione reale.** La tua base di conoscenza è probabilmente fatta di righe in una tabella — articoli, descrizioni prodotto, record di policy — non di file su disco. Il file loader si prende lo spazio nella documentazione; lo string loader si prende l'uso in produzione.

Una nota di efficienza su quell'esempio: costruisce l'agent RAG dentro il ciclo. Portalo fuori:

```php
$rag = MyRAG::make();

foreach ($contents as $text) {
    $rag->addDocuments(StringDataLoader::for($text)->getDocuments());
}
```

### Componenti autonomi

Non ti serve un agent RAG per fare ingestion. Il provider di embedding e il vector store funzionano in modo indipendente:

```php
$embedder = new OpenAIEmbeddingsProvider(
    key: 'OPENAI_API_KEY',
    model: 'OPENAI_MODEL'
);

$store = new FileVectorStore(
    directory: __DIR__,
    name: 'demo'
);

$documents = FileDataLoader::for(__DIR__.'/documents')
    ->addReader('pdf', new \NeuronAI\RAG\DataLoader\PdfReader())
    ->getDocuments();

$store->addDocuments(
    $embedder->embedDocuments($documents)
);
```

**Lo store dev'essere lo stesso che usa il tuo agent RAG.** Stessa cartella, stesso indice, stessa collezione. È il bug di ingestion più comune in assoluto: indicizzi in uno store e interroghi un altro, e l'agent dichiara di non sapere nulla.

**Perché usare componenti autonomi?** Perché ingestion e interrogazione sono lavori diversi con cicli di vita diversi. L'ingestion è un processo batch, un cron, un queue worker. Non ha bisogno di un provider di chat configurato, di una chiave API per l'LLM o delle istruzioni dell'agent. Separarli mantiene snello il tuo script di ingestion e lo rende distribuibile in modo indipendente.

È anche il pattern che il Capitolo 20 usa in Laravel, dove l'ingestion gira come job in coda.

### Punti chiave

- `FileDataLoader::for($path)->getDocuments()` per file e cartelle.
- I reader si mappano sulle estensioni; il PDF richiede poppler, l'HTML richiede `mtibben/html2text`.
- L'HTML si converte in Markdown, preservando la struttura per lo splitter.
- `StringDataLoader` è quello che userai davvero: la maggior parte delle basi di conoscenza sono righe di database.
- Fai ingestion con componenti autonomi; lo store dev'essere identico a quello dell'agent.

## 12.3 Splitter

### Collegare uno splitter

```php
$documents = FileDataLoader::for($directory)
    ->withSplitter(new DelimiterTextSplitter())
    ->getDocuments();
```

### DelimiterTextSplitter — il default

È ciò che usa ogni data loader quando non chiami `withSplitter()`:

```php
new DelimiterTextSplitter(
    maxLength: 1000,
    separator: '.',
    wordOverlap: 0
)
```

I tre parametri della Sezione 11.3, in codice:

- **`maxLength`** — chunk non più lunghi di così
- **`separator`** — dove sono ammessi i tagli; i loader passano il punto
- **`wordOverlap`** — parole portate fra i chunk; zero per default

Se costruisci la classe tu stesso, il separatore di default è uno spazio, non un punto — un motivo in più per passare esplicitamente tutti e tre. Un quarto parametro opzionale, `minLength`, unisce al chunk precedente un frammento più corto di quella soglia, così una frase di chiusura isolata non diventa un chunk a sé.

La documentazione è esplicita: ciascuno di questi influisce su prestazioni e accuratezza. Non sono default da accettare; sono decisioni da prendere.

### SentenceTextSplitter

```php
new SentenceTextSplitter(
    maxWords: 200,
    overlapWords: 0
)
```

Divide in frasi, le raggruppa in chunk basati sulle parole e, opzionalmente, sovrappone per parole. Il suo `minWords` svolge lo stesso ruolo di `minLength`.

**Quale usare.** `SentenceTextSplitter` è generalmente migliore per la prosa perché i conteggi di parole seguono i conteggi di token più da vicino di quelli di caratteri, e raggruppare frasi intere evita tagli a metà frase. `DelimiterTextSplitter` è migliore quando il tuo contenuto ha un delimitatore strutturale su cui vale la pena tagliare — il che ci porta alla parte importante.

### Splitter personalizzati: il codice con più leva nel tuo RAG

```php
namespace NeuronAI\RAG\Splitter;

use NeuronAI\RAG\Document;

interface SplitterInterface
{
    /**
     * @return Document[]
     */
    public function splitDocument(Document $document): array;

    /**
     * @param  Document[]  $documents
     * @return Document[]
     */
    public function splitDocuments(array $documents): array;
}
```

Due metodi. Ecco uno splitter per intestazioni Markdown — forse quaranta righe, e batterà qualunque splitter generico sulla documentazione:

```php
<?php

declare(strict_types=1);

namespace App\Rag;

use NeuronAI\RAG\Document;
use NeuronAI\RAG\Splitter\SplitterInterface;

class MarkdownSectionSplitter implements SplitterInterface
{
    public function __construct(
        private readonly int $maxChars = 2000,
    ) {}

    public function splitDocument(Document $document): array
    {
        // Split on level-2 headings, keeping the heading with its section
        $parts = \preg_split(
            '/^(?=##\s)/m',
            $document->getContent(),
            -1,
            PREG_SPLIT_NO_EMPTY
        ) ?: [];

        $chunks = [];

        foreach ($parts as $part) {
            $part = \trim($part);

            if ($part === '') {
                continue;
            }

            // Fall back to paragraph splitting for oversized sections
            if (\mb_strlen($part) > $this->maxChars) {
                foreach ($this->splitLongSection($part) as $piece) {
                    $chunks[] = $piece;
                }
                continue;
            }

            $chunks[] = $part;
        }

        // Each chunk keeps its parent's provenance and metadata
        return \array_map(
            fn (string $text): Document => (new Document($text))
                ->setSourceType($document->getSourceType())
                ->setSourceName($document->getSourceName())
                ->setMetadata($document->getMetadata()),
            $chunks
        );
    }

    public function splitDocuments(array $documents): array
    {
        $result = [];

        foreach ($documents as $document) {
            foreach ($this->splitDocument($document) as $chunk) {
                $result[] = $chunk;
            }
        }

        return $result;
    }

    /**
     * @return string[]
     */
    private function splitLongSection(string $section): array
    {
        $paragraphs = \preg_split('/\n{2,}/', $section) ?: [];

        $chunks  = [];
        $current = '';

        foreach ($paragraphs as $paragraph) {
            if (\mb_strlen($current . "\n\n" . $paragraph) > $this->maxChars && $current !== '') {
                $chunks[] = \trim($current);
                $current  = $paragraph;
                continue;
            }

            $current = $current === '' ? $paragraph : $current . "\n\n" . $paragraph;
        }

        if (\trim($current) !== '') {
            $chunks[] = \trim($current);
        }

        return $chunks;
    }
}
```

```php
$documents = FileDataLoader::for($directory)
    ->withSplitter(new MarkdownSectionSplitter(maxChars: 2000))
    ->getDocuments();
```

::: {.callout .callout-warning}
[Un chunk deve ereditare la provenienza del genitore]{.callout-title}

La documentazione mostra `Document` nelle firme delle interfacce ma non lo mostra mai costruito (Appendice A, punto 29). La classe chiude la questione: `new Document(string $content)`, poi setter fluenti — `setSourceType()`, `setSourceName()`, `setMetadata()` — e un getter per ciascuno. Non ci sono proprietà pubbliche da toccare, e la classe è `final`.

I tre setter in `splitDocument()` non sono decorazione. Un semplice `new Document($text)` viene archiviato con source type e source name `manual`, quindi ogni chunk perderebbe il file da cui proviene, `reindexBySource()` (Sezione 12.6) non potrebbe mai ritrovarlo e qualunque metadato del tenant che avevi allegato prima dello splitting sparirebbe. Gli splitter integrati copiano tutti e tre; uno personalizzato deve fare lo stesso.
:::

### Perché conta così tanto

Ogni chunk che questo produce è una sezione completa e autosufficiente, con la sua intestazione. Un risultato di retrieval riporta un'unità coerente invece di una finestra arbitraria di 1.000 caratteri che inizia a metà frase.

**Anche l'intestazione entra a far parte del testo di cui si calcola l'embedding**, il che significa che una domanda formulata come l'intestazione corrisponde con forza. È un guadagno gratuito di rilevanza, ottenuto solo rispettando la struttura del documento.

Il principio generale: **la migliore strategia di chunking è quella che il tuo documento ha già.** Il Markdown ha le intestazioni. Il codice ha le funzioni. Le trascrizioni hanno i parlanti. Usale.

### Punti chiave

- `withSplitter()` su qualunque data loader.
- `DelimiterTextSplitter` per delimitatori strutturali; `SentenceTextSplitter` per la prosa.
- `SplitterInterface` sono due metodi: uno splitter personalizzato è il lavoro di un pomeriggio. Copia source e metadati su ogni chunk.
- Rispetta la struttura del documento; è la leva di qualità più grande nel RAG.

## 12.4 Provider di embedding

### L'interfaccia

```php
protected function embeddings(): EmbeddingsProviderInterface
{
    return new OpenAIEmbeddingsProvider(
        key: 'OPENAI_API_KEY',
        model: 'OPENAI_MODEL'
    );
}
```

Stessa forma di ogni altro componente. Intercambiabile — con un'unica, enorme avvertenza.

### Embedding locali con Ollama

```php
use NeuronAI\RAG\Embeddings\EmbeddingsProviderInterface;
use NeuronAI\RAG\Embeddings\OllamaEmbeddingsProvider;

class MyRAG extends RAG
{
    protected function embeddings(): EmbeddingsProviderInterface
    {
        return new OllamaEmbeddingsProvider(
            model: 'OLLAMA_EMBEDDINGS_MODEL'
        );
    }
}
```

Nessuna chiave API, nessun costo, nessun dato che lascia la macchina.

```bash
ollama pull nomic-embed-text
```

**Usalo per ogni laboratorio della Parte III.** Combinato con un modello di chat locale della Sezione 3.6, l'intera parte sul RAG non costa nulla da attraversare.

È anche una scelta di produzione legittima. I modelli di embedding sono piccoli e veloci; eseguirne uno in locale è molto diverso dall'eseguire in locale un modello di chat di frontiera.

### Opzioni ospitate

`OpenAIEmbeddingsProvider`, `VoyageEmbeddingsProvider` e altri. Voyage in particolare vale la pena conoscerlo: è specializzato in embedding per il retrieval e spesso batte i modelli generici sui benchmark RAG.

### Provider personalizzati

Estendi `AbstractEmbeddingsProvider`. Stessa storia di estensione di ogni altra parte del framework.

### L'avvertenza che non è come le altre

La Sezione 3.6 insegnava che cambiare provider è una modifica di una riga. **Gli embedding sono l'eccezione.**

Cambia il modello di embedding e ogni vettore nel tuo store diventa privo di significato. Sono coordinate in uno spazio diverso. Il retrieval restituirà risultati — non fallirà rumorosamente — e saranno sbagliati.

**Cambiare il modello di embedding significa ricalcolare gli embedding dell'intero corpus.**

Tre conseguenze pratiche:

- Registra quale modello ha prodotto il tuo indice. Nel nome dello store, in un campo di metadati, in una nota di deploy — da qualche parte.
- Metti in conto il tempo di ricalcolo prima di cambiare. Milioni di chunk sono ore e denaro vero.
- Non rendere mai il modello di embedding una variabile d'ambiente che differisce fra gli ambienti. Sviluppo su `nomic-embed-text` e produzione su `text-embedding-3-large` significa che il tuo indice di sviluppo e quello di produzione sono incompatibili, e il bug sarà sconcertante.

Quest'ultima è una trappola davvero brutta, ed è l'errore naturale per chi ha appena imparato il pattern `ProviderFactory` della Sezione 3.6.

### Dimensioni

Modelli diversi producono vettori di lunghezza diversa — 768, 1024, 1536 e altre. Il tuo vector store dev'essere configurato di conseguenza. `TypesenseVectorStore` prende `vectorDimension: 1024`; `MariaDBVectorStore::setupTable(dimensions: 768)` crea una colonna `VECTOR(768)`, e se non specifichi nulla usa 1536 per default.

Una discrepanza significa o un errore netto o silenziose sciocchezze, a seconda dello store. Controllalo quando fai il setup.

### Punti chiave

- `OllamaEmbeddingsProvider` gira in locale, gratis: usalo per tutti i laboratori.
- Le opzioni ospitate includono OpenAI e Voyage; Voyage è specializzato nel retrieval.
- **Cambiare il modello di embedding invalida il tuo intero indice.**
- Non variare mai il modello di embedding fra gli ambienti.
- Le dimensioni dei vettori devono corrispondere alla configurazione del tuo store.

## 12.5 Vector store

### L'interfaccia

```php
namespace NeuronAI\RAG\VectorStore;

use NeuronAI\RAG\Document;
use NeuronAI\RAG\Schema\DocumentSchema;
use NeuronAI\RAG\VectorStore\Filter\FilterExpression;

interface VectorStoreInterface
{
    public function getSchema(): DocumentSchema;

    public function addDocument(Document $document): VectorStoreInterface;

    /**
     * @param  Document[]  $documents
     */
    public function addDocuments(array $documents): VectorStoreInterface;

    /**
     * Delete every document matching the filters.
     */
    public function delete(FilterExpression $filters): VectorStoreInterface;

    /**
     * Return the documents most similar to the request's embedding.
     *
     * @return iterable<Document>
     */
    public function search(SearchRequest $request): iterable;
}
```

Cinque metodi. Tre di essi dicono qualcosa sulle priorità del framework.

`search()` prende una `SearchRequest` — embedding, filtri opzionali, `topK` opzionale — costruita da zero per ogni chiamata. Uno store non conserva alcuno stato di ricerca, quindi un filtro impostato per una query non può vincolare, o non riuscire a vincolare, silenziosamente la successiva.

`delete()` prende un filtro invece di una coppia di campi fissata nel codice. Esiste per supportare la reindicizzazione (Sezione 12.6), il che ti dice che il framework tratta l'obsolescenza come problema di prima classe e non come ripensamento.

`getSchema()` restituisce il `DocumentSchema` dello store: la dichiarazione di quali campi di metadati esistono, di che tipo sono e su quali puoi filtrare. Configurarlo è facoltativo, ed è centrale per il filtraggio; entrambe le cose sono trattate più avanti.

### Il catalogo

**Memory** — volatile, solo per la sessione corrente. Per test e interazioni usa e getta.

```php
return new MemoryVectorStore();
```

**File** — archiviazione su file system, e progettato meglio di quanto sembri:

```php
return new FileVectorStore(
    directory: storage_path(),
    topK: 4
);
```

La documentazione fa un'osservazione che vale la pena ripetere: usa i **generatori PHP** per leggere i documenti, quindi non tiene mai in memoria più di `topK` elementi pur iterando rapidamente. Puoi conservare migliaia di documenti e l'unico vincolo è quanto può durare una ricerca per similarità. Crea la directory e un file di store vuoto già alla costruzione, quindi uno store appena creato si può interrogare, svuotare o reindicizzare subito.

C'è anche un uso distributivo: distribuire un agent con la conoscenza già cotta dentro un file. È un pattern davvero elegante per uno strumento impacchettato o una demo.

**PHPVector** — PHP puro, nessun servizio esterno. Costruito su `ezimuel/phpvector`, implementa **HNSW** per la ricerca approssimata dei vicini più prossimi e **BM25** per il recupero full-text, e combina i due in una vera pipeline di **ricerca ibrida** — ranking vettoriale e lessicale insieme. Questo ne fa la voce più interessante dell'elenco per un pubblico PHP: retrieval di livello produttivo senza alcun servizio da distribuire.

::: {.callout .callout-warning}
[PHPVector non ha ancora una release per questa versione di NeuronAI]{.callout-title}

`neuron-core/php-vector` viene distribuito separatamente dal framework e, al momento in cui scriviamo, la sua ultima release (1.1.0) richiede ancora `neuron-ai` 3.x. Composer si rifiuterà di installarlo accanto alla versione di questo libro, e comunque la release 3.x implementa la vecchia interfaccia dello store. Tieni d'occhio il pacchetto in attesa di una release che supporti l'interfaccia `search()`/`delete()`/`getSchema()` vista sopra; fino ad allora, i laboratori di questo capitolo usano `FileVectorStore` e `MariaDBVectorStore`, e il repository di accompagnamento non dipende da esso.
:::

**MariaDB** — vettori nativi dalla 11.7:

```php
$store = new MariaDBVectorStore(
    pdo: new \PDO(...), // Or get the PDO instance from the ORM
    tableName: 'rag_documents',
);

$store->setupTable(dimensions: 768); // once, at install time
```

`setupTable()` crea la tabella che lo store si aspetta:

```sql
CREATE TABLE IF NOT EXISTS rag_documents (
    id UUID NOT NULL PRIMARY KEY,
    content TEXT,
    sourceType VARCHAR(255),
    sourceName VARCHAR(255),
    metadata JSON,
    embedding VECTOR(768) NOT NULL,
    VECTOR INDEX (embedding)
)
```

Per un'azienda PHP che già fa girare MariaDB, è la risposta di produzione con meno attrito: una tabella, nessun servizio nuovo, backup e monitoraggio che hai già. Nota lo schema: `sourceType` e `sourceName` sono lì per la reindicizzazione, e `metadata JSON` per il filtraggio.

**Gestiti e dedicati:** Pinecone, Weaviate, Elasticsearch, OpenSearch, Typesense, Qdrant, ChromaDB, Meilisearch e MongoDB Atlas Vector Search. Ciascuno prende la propria configurazione di connessione; diversi richiedono l'installazione del client ufficiale via Composer.

::: {.callout .callout-warning}
[Non esiste uno store pgvector]{.callout-title}

L'elenco qui sopra è completo. Moltissimo materiale di terze parti presume che NeuronAI includa un'integrazione pgvector, perché pgvector è onnipresente nell'ecosistema Python. Non è così. Se sei su Postgres e vuoi supporto di prima parte, le tue opzioni sono uno degli store dedicati — oppure, quando uscirà una release compatibile, PHPVector, a cui non importa quale database fai girare. Uno store personalizzato (più avanti) è la terza strada.
:::

### La tabella decisionale

| Situazione | Store |
|---|---|
| Test unitari | Memory |
| Laboratori, prototipi, corpus piccoli | File |
| Fai già girare MariaDB 11.7+ | **MariaDB** |
| Self-hosted, nessuna nuova infrastruttura, vuoi ricerca ibrida | PHPVector, quando supporterà questa versione |
| Fai già girare Elasticsearch, OpenSearch o MongoDB Atlas | Quello |
| Vuoi un servizio gestito, miliardi di vettori | Pinecone |
| Vuoi open source dedicato | Qdrant, Weaviate, Chroma |

**La regola generale: usa quello che già fai girare.** Un database nuovo è una nuova storia di backup, una nuova storia di monitoraggio e un nuovo modo di guastarsi. MariaDB — e PHPVector, quando si metterà al passo — esistono proprio perché la maggior parte dei team PHP non abbia bisogno di nulla di tutto ciò.

### Ricerca filtrata

Ogni store integrato può restringere una ricerca per similarità ai documenti i cui metadati soddisfano una condizione. Scrivi la condizione una sola volta, in un vocabolario portabile, e ogni store la compila nella propria sintassi nativa: lo stesso filtro gira sul file store in sviluppo e su Pinecone o MariaDB in produzione.

A farlo funzionare sono due pezzi. Lo store viene informato di quali campi di metadati esistono e quali sono filtrabili, tramite un `DocumentSchema`. L'agent dichiara il vincolo obbligatorio per le sue ricerche in `retrievalScope()`:

```php
use NeuronAI\RAG\Schema\DocumentField;
use NeuronAI\RAG\Schema\DocumentSchema;
use NeuronAI\RAG\VectorStore\Filter\Filter;
use NeuronAI\RAG\VectorStore\Filter\FilterExpression;

class MyChatBot extends RAG
{
    protected ?string $tenantId = null;

    public function forTenant(string $tenantId): static
    {
        $this->tenantId = $tenantId;
        return $this;
    }

    protected function vectorStore(): VectorStoreInterface
    {
        return new PineconeVectorStore(
            key: 'PINECONE_API_KEY',
            indexUrl: 'PINECONE_INDEX_URL',
            schema: DocumentSchema::of(
                DocumentField::string('tenant_id')->required()->filterable(),
                DocumentField::string('visibility')->required()->filterable(),
            ),
        );
    }

    protected function retrievalScope(): ?FilterExpression
    {
        if ($this->tenantId === null) {
            // Fail closed: an unscoped search would cross tenants
            throw new \LogicException('Call forTenant() before chatting.');
        }

        return Filter::where('tenant_id', $this->tenantId)
            ->where('visibility', 'public');
    }
}
```

```php
$response = MyChatBot::make()
    ->forTenant($tenant->uuid)
    ->chat(new UserMessage(...))
    ->getMessage();
```

**È il meccanismo per il RAG multi-tenant**, ed è abbastanza importante da segnalarlo ad alta voce. Filtrare per `tenant_id` al momento della query significa che la ricerca dell'utente A non può restituire i documenti dell'utente B. Senza, un vector store condiviso trapela fra i tenant — che è una violazione dei dati, non un bug.

Nota la guardia. Restituire `null` da `retrievalScope()` significa "nessun vincolo", quindi un tenant mancante dev'essere un errore, mai un ripiego silenzioso sulla ricerca fra i documenti di tutti.

Lo scope non è un suggerimento che la pipeline può scavalcare. Qualunque altra cosa aggiunga un filtro durante una run — un middleware, una strategia di retrieval personalizzata — viene combinata con esso in AND, quindi un filtro successivo può restringere la ricerca ma mai allargarla. Quando il valore è noto solo a runtime, `setRetrievalScope()` imposta la stessa cosa dall'esterno della classe.

Il vocabolario copre ciò di cui le applicazioni hanno davvero bisogno — `where()`, `whereNot()`, `whereIn()`, gli intervalli numerici (`whereGreaterThan()`, `whereLessThanOrEqual()` e compagnia), `whereContainsAny()`/`whereContainsAll()` per i campi che sono liste di stringhe — più `FilterGroup::anyOf()` e `allOf()` per la logica OR/AND annidata. Per la rara funzionalità di backend che ne resta fuori, `Filter::raw(PineconeVectorStore::class, $nativeFragment)` passa la sintassi nativa a quello store e fa lanciare un'eccezione a tutti gli altri, così cambiare store fallisce in modo evidente invece di filtrare male in silenzio.

Il Capitolo 20 lo costruisce per bene in Laravel.

::: {.callout .callout-warning}
[Un campo non dichiarato è un errore netto, non un risultato vuoto]{.callout-title}

Filtra su un campo di metadati che lo schema dello store non dichiara filtrabile — un refuso, o un campo che hai dimenticato di dichiarare — e lo store lancia una `DocumentSchemaException` prima di toccare il database. Solo `sourceType`, `sourceName` e i campi dichiarati filtrabili sono destinazioni valide per un filtro. Altre due regole da conoscere prima di progettare lo schema: i valori dei filtri sono scalari (`null` lancia un'eccezione, perché "mancante" e "null" significano cose diverse su database diversi), e `whereNot()` è ammesso solo su un campo `required()`, per lo stesso motivo.

Quella rigidità è il punto. Un filtro che silenziosamente non trovasse nulla — o trovasse tutto — su un backend e non su un altro sarebbe il peggior genere di bug multi-tenant.
:::

### Store personalizzati

Implementa l'interfaccia. Contano quattro dettagli:

**Restituisci punteggi, non distanze.** Converti con `VectorSimilarity::similarityFromDistance()`.

**Rispetta lo schema.** Valida documenti e filtri contro `getSchema()` prima di qualunque I/O sul database; il trait `HasDocumentSchema` usato dagli store integrati ti fornisce l'impianto.

**Compila o valuta i filtri.** Traduci la `FilterExpression` nella sintassi del tuo backend — oppure, per uno store che scandisce in PHP, valutala con `FilterEvaluator`, come fanno il file store e il memory store.

**`addDocument()` può delegare a `addDocuments()`** se il tuo database non ha un'API separata per il singolo elemento. I due metodi esistono perché molti database ce l'hanno.

I manutentori invitano esplicitamente pull request per nuovi store. Se vuoi un contributo open source ben delimitato e genuinamente utile, è uno.

### Punti chiave

- Interfaccia a cinque metodi; `search()` prende una `SearchRequest` nuova a ogni chiamata, e `delete()` prende un filtro.
- `FileVectorStore` usa i generatori e scala più di quanto ci si aspetti.
- **MariaDB 11.7+** è l'opzione di produzione con meno attrito per la maggior parte delle aziende PHP.
- La ricerca ibrida HNSW + BM25 di PHPVector attende una release per questa versione del framework.
- Dichiara i campi filtrabili in un `DocumentSchema`; metti i vincoli obbligatori in `retrievalScope()`.
- I filtri sui metadati sono il modo di fare RAG multi-tenant in sicurezza.
- Usa quello che già fai girare.

## 12.6 Metadati e reindicizzazione

### Metadati

```php
$documents = FileDataLoader::for($directory)->getDocuments();

foreach ($documents as $document) {
    $document->addMetadata('user_id', 1234);
}

MyRAG::make()->addDocuments($documents);
```

Campi personalizzati salvati nello store accanto ai campi di default del documento. Qualunque valore serializzabile in JSON è accettato e fa il giro completo — salvato, poi restituito da `getMetadata()` sul documento recuperato. Una manciata di nomi (`id`, `content`, `embedding`, `score`, `sourceType`, `sourceName`, `metadata` e alcuni interni ai backend) sono riservati, e `addMetadata()` lancia un'eccezione se ne usi uno.

### Che cosa allegare

Pensa ai metadati come alle colonne su cui vorrai filtrare più avanti. Una volta costruito l'indice, aggiungere un campo significa reindicizzare — quindi decidi adesso:

```php
foreach ($documents as $document) {
    $document->addMetadata('tenant_id',   $tenant->uuid);
    $document->addMetadata('visibility',  'internal');
    $document->addMetadata('language',    'en');
    $document->addMetadata('updated_at',  $article->updated_at->getTimestamp());
    $document->addMetadata('category',    $article->category);
}
```

Poi comunica allo store quelli su cui filtrerai:

```php
$schema = DocumentSchema::of(
    DocumentField::string('tenant_id')->required()->filterable(),
    DocumentField::string('visibility')->required()->filterable(),
    DocumentField::string('language')->filterable(),
    DocumentField::integer('updated_at')->filterable(),
);
```

`category` non è dichiarato: viene salvato e restituito, ma non è filtrabile. È una scelta deliberata, non una scappatoia — dichiara un campo quando il database deve conoscerne il tipo, perché dev'essere presente su ogni documento (`required()`) o perché ci filtri sopra (`filterable()`). Nota che `updated_at` è un timestamp intero, non una stringa di data: i filtri per intervallo sono numerici, e un `DateTimeInterface` passato a un filtro per intervallo viene convertito in timestamp al posto tuo.

`RAG::addDocuments()` valida ogni documento contro lo schema *prima* di chiamare il modello di embedding, quindi un chunk a cui manca il `tenant_id` fallisce subito invece di costarti una chiamata di embedding e un batch scritto a metà.

Quattro cose che vale quasi sempre la pena allegare:

**Tenant o proprietario.** Il confine di sicurezza per il retrieval multi-tenant. Non negoziabile se servi più di un cliente da un unico indice.

**Visibilità o livello di permesso.** Così un agent rivolto al pubblico non può recuperare documenti interni.

**Lingua.** Il retrieval cross-lingua funziona per lo più e occasionalmente produce risultati confusi.

**Freschezza.** Una data ti permette di preferire o filtrare i contenuti recenti — utile quando la vecchia e la nuova versione di una policy vivono entrambe nell'indice.

### Filtrare al retrieval

Una volta che i campi sono nello store e dichiarati nel suo schema, ogni store integrato può restringere una ricerca semantica ai record che soddisfano criteri su altri campi, invece di confrontare solo gli embedding vettoriali. La documentazione a volte la chiama ricerca ibrida, ma il vocabolario del framework riserva quel termine alla combinazione di ranking vettoriale e per parole chiave. Questa è ricerca filtrata.

L'inquadratura di sicurezza è quella da mettere per prima: **il filtro dei permessi va applicato al retrieval, non dopo.** Recuperare un documento che l'utente non può vedere e poi escluderlo dalla risposta significa che era nel contesto del modello — e i modelli parafrasano. Il documento è trapelato anche se non è mai stato mostrato.

Filtra allo store. Ogni volta.

### Reindicizzazione

La documentazione è schietta sul fatto che sia un tema caldo nella progettazione RAG: il chunking rende difficile aggiornare singoli pezzi di informazione quando la fonte cambia.

La risposta di NeuronAI sono i metadati che identificano la provenienza. Ogni `Document` porta un `sourceType` e un `sourceName` — `FileDataLoader` li imposta a `files` e al nome del file — e:

```php
$documents = FileDataLoader::for("/path/to/directory")
    ->withSplitter(
        new SentenceTextSplitter(
            maxWords: 200,
            overlapWords: 0
        )
    )
    ->getDocuments();

MyRAG::make()->reindexBySource($documents);
```

`reindexBySource()` raggruppa i nuovi chunk per fonte e, per ogni coppia `sourceType`/`sourceName`, **cancella i documenti esistenti di quella fonte e aggiunge i chunk della nuova versione**. Una fonte non ancora presente nello store viene semplicemente aggiunta.

È l'operazione che risolve il modo di fallire numero 6 della Sezione 11.5, ed è il motivo per cui `delete()` sta nell'interfaccia dello store. Sotto il cofano è un filtro qualunque:

```php
$store->delete(
    Filter::where('sourceType', 'files')
        ->where('sourceName', 'refund-policy.md'),
);
```

Il semplice `addDocuments()` non fa alcun controllo del genere: esegui due volte uno script di ingestion con esso e ogni chunk sarà nello store due volte.

### Il vincolo che frega qualcuno

> La nuova versione del file **deve avere lo stesso percorso e lo stesso nome** dell'originale, altrimenti i documenti vengono aggiunti come nuovi.

Rinomina il file, reindicizza, e ora hai entrambe le versioni nello store: i vecchi chunk orfani sotto un nome di fonte che nulla reindicizzerà mai, i nuovi accanto a loro. L'agent recupererà da entrambi e risponderà da quello che ha corrisposto meglio.

**In pratica:** usa un identificativo stabile, non un nome di file che rifletta il contenuto. `policies/refund-policy.md` sopravvive a una modifica. `policies/refund-policy-v3-final-2026.md` no.

Per l'ingestion da database con `StringDataLoader` vale la stessa logica, con un passo in più: lo string loader archivia tutto con source type e source name `manual`, quindi li imposti entrambi tu — `sourceName` sulla chiave primaria del record, non sul suo titolo.

### Una strategia di ingestion da adottare

```php
// Re-index a single article after it changes
$documents = StringDataLoader::for($article->body)->getDocuments();

foreach ($documents as $document) {
    $document
        ->setSourceType('articles')
        ->setSourceName((string) $article->id) // the ID, never the title
        ->addMetadata('tenant_id', $article->tenant_uuid);
}

$rag->reindexBySource($documents);
```

Agganciala all'evento `saved` del tuo modello e mandala in coda. L'indice resta aggiornato senza cron e senza deriva. Il Capitolo 20 costruisce esattamente questo.

### Punti chiave

- `addMetadata()` prima di `addDocuments()`; i campi sono i tuoi filtri futuri.
- Dichiara nel `DocumentSchema` dello store i campi su cui filtri; i metadati non dichiarati vengono salvati ma non sono filtrabili.
- Allega tenant, visibilità, lingua e freschezza per default.
- Filtra i permessi **al retrieval**: il post-filtraggio è una fuga.
- `reindexBySource()` sostituisce i chunk di una fonte; `sourceName` dev'essere stabile.
- Usa gli ID dei record, non i titoli, come nomi di fonte.

## 12.7 Il workflow RAG: pre- e post-processor

### La pipeline

Quando un `UserMessage` entra in un agent RAG, girano sei nodi in ordine:

```
UserMessage
    │
    ├─ PreProcessNode        ← riscrivi / espandi la query
    ├─ RetrievalNode         ← esegui la strategia di retrieval
    ├─ PostProcessNode       ← riordina / filtra i risultati
    ├─ InstructionsNode      ← inietta i documenti nel system prompt
    ├─ ChatNode              ← esegui l'inferenza
    └─ ToolNode              ← esegui i tool, se ce ne sono
    │
AssistantMessage
```

I primi quattro sostituiscono il nodo iniziale dell'agent semplice; da `ChatNode` in poi è lo stesso ciclo dell'agent visto ovunque nel libro.

**È il ritorno della Sezione 2.3.** Un agent RAG è un workflow, i suoi nodi hanno un nome, e conoscere i nomi ti permette di agganciare il sistema con dei middleware. Tutto ciò che c'è nella Parte IV vale qui.

Si mappa anche precisamente sui modi di fallire della Sezione 11.5:

| Fallimento | Nodo che lo risolve |
|---|---|
| La domanda non assomiglia alla risposta | `PreProcessNode` |
| Simile ma non rilevante | `PostProcessNode` |
| Allucinazione | `InstructionsNode` + istruzioni |
| Risposta distribuita fra chunk | Strategia di retrieval + reranking |

### Pre-processor: sistemare la query

`PreProcessNode` esegue la pipeline di pre-processor. L'esempio integrato è `QueryTransformationPreProcessor`, che chiede a un modello di rimodellare la domanda prima che se ne calcoli l'embedding:

```php
use NeuronAI\RAG\PreProcessor\QueryTransformationPreProcessor;
use NeuronAI\RAG\PreProcessor\QueryTransformationType;

protected function preProcessors(): array
{
    return [
        new QueryTransformationPreProcessor(
            provider: $this->getProvider(),
            transformation: QueryTransformationType::REWRITING,
        ),
    ];
}
```

Perché aiuta: gli utenti fanno domande nel linguaggio dei *problemi*; i documenti sono scritti nel linguaggio delle *soluzioni*. "Perché la mia cosa è rotta?" e "Il codice errore 4021 indica allocazione disco insufficiente" sono semanticamente lontani. Un passo di trasformazione riscrive la domanda in qualcosa di più vicino a come è formulata la risposta prima che avvenga l'embedding. `REWRITING` è il default; `DECOMPOSITION` scompone una domanda composta in domande più semplici, e `HYDE` fa scrivere al modello una risposta ipotetica e calcola l'embedding di quella — una query a forma di risposta trova documenti a forma di risposta.

Il costo è una chiamata al modello in più per query, ed è reale. Misura se si guadagna il posto sul tuo corpus; sulla documentazione tecnica di solito sì, sui contenuti in stile FAQ spesso no. Per la riscrittura di solito basta un provider più economico e veloce del tuo modello di chat principale.

### Post-processor: sistemare i risultati

`PostProcessNode` esegue la pipeline di post-processor, e il reranking è la ragione per cui esiste.

```php
use NeuronAI\RAG\PostProcessor\JinaRerankerPostProcessor;

protected function vectorStore(): VectorStoreInterface
{
    return new FileVectorStore(directory: storage_path('vectors'), topK: 50);
}

protected function postProcessors(): array
{
    return [
        new JinaRerankerPostProcessor(key: 'JINA_API_KEY', topN: 5),
    ];
}
```

Le alternative sono Cohere (`CohereRerankerPostProcessor`) e un reranker LocalAI self-hosted (`LocalAIRerankerPostProcessor`). Due post-processor più economici non richiedono alcun modello: `FixedThresholdPostProcessor` scarta i documenti sotto una soglia di punteggio, e `AdaptiveThresholdPostProcessor` fissa la soglia in base alla distribuzione dei punteggi di ciascun insieme di risultati.

**Perché il reranking funziona, e perché è l'aggiunta con il ritorno più alto a un sistema RAG funzionante:**

La ricerca vettoriale confronta due embedding calcolati *indipendentemente*. La query è stata compressa in un vettore senza sapere nulla dei documenti; ogni documento è stato compresso senza sapere nulla della query. In entrambe le compressioni si perde informazione.

Un reranker legge la query e un documento **insieme** e assegna un punteggio alla loro relazione in modo diretto. È molto più lento per coppia, ed è il motivo per cui non puoi usarlo per cercare fra milioni di documenti — ma su 50 candidati è veloce, e coglie segnali di rilevanza che il confronto vettoriale non poteva rappresentare.

La forma standard della pipeline — ed esattamente ciò che configura il listato qui sopra:

```
Ricerca vettoriale → top 50 candidati → rerank → top 5 → manda al modello
```

Ottieni il richiamo di una ricerca ampia e la precisione di una accurata, e mandi al modello meno chunk e migliori — il che riduce anche i token.

### Strategia di retrieval

`RetrievalNode` esegue la strategia di retrieval, e NeuronAI permette di personalizzarla — incluso il recupero da fonti dati esterne invece che solo dal vector store. Il default, `SimilarityRetrieval`, calcola l'embedding della query ed esegue una sola `search()`; la tua strategia implementa `RetrievalInterface` e la passi a `setRetrieval()` o la restituisci da un override di `retrieval()`.

È il punto di estensione per qualunque cosa inusuale: una ricerca ibrida che combina BM25 e vettori, un retrieval multi-query per domande distribuite fra chunk, o l'attingere a un'API di ricerca accanto al tuo indice.

Con essa arriva un obbligo. `retrieve(Message $query, ?FilterExpression $filters = null)` riceve i filtri in vigore per questa run — incluso il tuo `retrievalScope()`. Una strategia personalizzata deve applicarli, combinati con i propri tramite `FilterScope::merge()`, e non scartarli mai; altrimenti la strategia è il buco nel tuo isolamento fra tenant.

Accanto al default vengono fornite due strategie. `CompositeRetrieval` esegue più strategie in ordine e mette insieme i loro risultati, ed è così che si cerca in due store contemporaneamente. `SemanticMemoryRetrieval` cerca nelle conversazioni passate salvate come documenti, limitandosi ai thread ID che le passi — combina le due e l'agent può ricordare "di cosa abbiamo parlato la settimana scorsa" accanto alla base di conoscenza. Nei termini della Sezione 11.1 è memoria a lungo termine, non retrieval di conoscenza; vale la pena sapere che i pezzi esistono, e la guida del framework sulla memoria conversazionale spiega come collegarli.

### InstructionsNode: dove si combatte l'allucinazione

Questo nodo aggiunge i documenti recuperati al system prompt dell'agent, come blocco separato racchiuso fra tag `<EXTRA-CONTEXT>`, con ogni documento etichettato con il suo source type e il suo source name. Le tue istruzioni restano intatte, prima di esso.

Il che significa che il system prompt è dove vincoli l'uso che il modello ne fa. Combina il meccanismo del nodo con le tue `instructions()`:

```php
protected function instructions(): string
{
    return (string) new SystemPrompt(
        background: [
            'You answer questions using only the documents provided in your context.',
            'You are not a general-purpose assistant. Outside these documents you know nothing.',
        ],
        steps: [
            'Read the provided documents.',
            'If they contain the answer, give it and name the source document.',
            'If they do not, say clearly that the information is not in the knowledge base. '
            . 'Do not answer from general knowledge.',
        ],
        output: [
            'Cite the source of every factual claim.',
            'Never present an inference as something the documents state.',
        ],
    );
}
```

Le etichette di fonte sono ciò che rende possibile "indica il documento di origine" — un motivo in più perché il `sourceName` che imposti all'ingestion significhi qualcosa per un lettore.

Quelle istruzioni più un `FaithfulnessJudge` nella tua suite di eval sono le due metà della storia anti-allucinazione: una la riduce, l'altra ti dice se ha funzionato.

### Middleware sui nodi RAG

Poiché sono nodi di workflow, i middleware li prendono di mira per classe — `$rag->addMiddleware(RetrievalNode::class, new MyMiddleware())`, oppure un override di `middleware()` sull'agent, lo stesso meccanismo che la Sezione 2.3 ha introdotto per `ToolNode`.

Applicazioni utili:

- Logga ogni retrieval: query, documenti restituiti, punteggi. È il tuo strumento di debug per il RAG.
- Inietta un filtro per singola run. Il `before()` di un middleware su `RetrievalNode` riceve il `QueryPreProcessedEvent` e può chiamare `addFilters()` su di esso; il filtro viene messo in AND con lo scope di retrieval e muore con la run.
- Metti in cache i risultati di retrieval per query ripetute.
- Reda i contenuti sensibili dai documenti prima che entrino nel prompt.

Il Capitolo 15 tratta i middleware come si deve.

### Punti chiave

- Sei nodi: pre-processo, retrieval, post-processo, arricchimento delle istruzioni, chat, tool.
- I pre-processor sistemano il disallineamento domanda/risposta al costo di una chiamata al modello.
- **Il reranking è il miglioramento con il ritorno più alto per un sistema RAG funzionante**: recupera 50, riordina, manda 5.
- Una strategia di retrieval personalizzata deve rispettare i filtri che riceve.
- `InstructionsNode` più istruzioni severe è il meccanismo anti-allucinazione.
- I nodi hanno un nome, quindi i middleware possono agganciare ogni stadio.

## Laboratorio 8 — RAG sulla documentazione, a costo zero

**Copre:** classe RAG, file loader, splitter personalizzato, embedding locali, store su file.

### Obiettivo

Fare domande a una cartella di documentazione Markdown, senza chiavi API e senza infrastruttura. Tutto locale, tutto gratis.

### Prerequisiti

```bash
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

### L'agent

**`src/Rag/DocsAgent.php`**

```php
<?php

declare(strict_types=1);

namespace App\Rag;

use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Providers\Ollama\Ollama;
use NeuronAI\RAG\Embeddings\EmbeddingsProviderInterface;
use NeuronAI\RAG\Embeddings\OllamaEmbeddingsProvider;
use NeuronAI\RAG\RAG;
use NeuronAI\RAG\VectorStore\FileVectorStore;
use NeuronAI\RAG\VectorStore\VectorStoreInterface;

class DocsAgent extends RAG
{
    protected function provider(): AIProviderInterface
    {
        return new Ollama(
            url: env('OLLAMA_URL', 'http://localhost:11434/api'),
            model: env('OLLAMA_MODEL', 'qwen2.5:7b'),
        );
    }

    protected function embeddings(): EmbeddingsProviderInterface
    {
        return new OllamaEmbeddingsProvider(
            model: env('OLLAMA_EMBEDDINGS_MODEL', 'nomic-embed-text'),
        );
    }

    protected function vectorStore(): VectorStoreInterface
    {
        return new FileVectorStore(
            directory: \dirname(__DIR__, 2) . '/storage/vectors',
            topK: 5,
        );
    }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: [
                'You answer questions about a software project using only its documentation.',
                'Outside the provided documents you know nothing about this project.',
            ],
            steps: [
                'Read the documents provided in your context.',
                'If they answer the question, answer and name the source.',
                'If they do not, say the documentation does not cover it.',
            ],
            output: [
                'Be concise. Include a short code example when the documents contain one.',
                'Always end with the source section heading you used.',
            ],
        );
    }
}
```

### Lo script di ingestion

**`examples/08-index-docs.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Rag\DocsAgent;
use App\Rag\MarkdownSectionSplitter;
use NeuronAI\RAG\DataLoader\FileDataLoader;

$directory = $argv[1] ?? __DIR__ . '/fixtures/docs';

if (!\is_dir($directory)) {
    \fwrite(STDERR, "Not a directory: {$directory}\n");
    exit(1);
}

$start = \microtime(true);

$documents = FileDataLoader::for($directory)
    ->withSplitter(new MarkdownSectionSplitter(maxChars: 2000))
    ->getDocuments();

\printf("Split into %d chunks.\n", \count($documents));

DocsAgent::make()->addDocuments($documents);

\printf("Indexed in %.1fs.\n", \microtime(true) - $start);
```

### Lo script di interrogazione

**`examples/09-ask-docs.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Rag\DocsAgent;
use NeuronAI\Chat\Messages\UserMessage;

$question = $argv[1] ?? 'How do I configure the vector store?';

echo DocsAgent::make()
    ->chat(new UserMessage($question))
    ->getMessage()
    ?->getContent() . PHP_EOL;
```

```bash
php examples/08-index-docs.php ./docs
php examples/09-ask-docs.php "How do I add a custom tool?"
php examples/09-ask-docs.php "What is the airspeed velocity of an unladen swallow?"
```

### Il test che conta

Quell'ultima domanda è il punto del laboratorio. **L'agent dovrebbe dire che la documentazione non lo copre.**

Se risponde comunque, hai appena riprodotto il modo di fallire numero 5 della Sezione 11.5 sulla tua macchina — e puoi correggerlo rafforzando le sezioni `steps` e `background`. È un risultato molto più utile di una query riuscita.

### Criteri di accettazione

- L'indicizzazione riporta un numero di chunk coerente con il numero di intestazioni `##` nel tuo corpus, non un numero tondo che suggerisce una divisione per conteggio di caratteri.
- Una domanda formulata come un'intestazione restituisce quella sezione.
- Una domanda fuori ambito viene rifiutata, esplicitamente, senza una plausibile risposta inventata.
- Cancellare la cartella del vector store e rilanciare l'indicizzazione produce le stesse risposte.

### Estensioni

1. Confronta `MarkdownSectionSplitter` con il `DelimiterTextSplitter` di default sulle stesse domande.
2. Cambia `topK` da 5 a 2 e a 10. Osserva qualità delle risposte e latenza.
3. Modifica un file sorgente, rilancia l'indicizzazione con `reindexBySource()` e conferma che i vecchi chunk siano spariti.

## Laboratorio 9 — Store di produzione con ricerca filtrata

**Copre:** MariaDB, schema dei documenti, metadati, filtri, valutazione.

### Obiettivo

Spostare il Laboratorio 8 su un database di produzione, aggiungere il filtraggio sui metadati e misurare se ha davvero migliorato qualcosa.

### Installazione

MariaDB 11.7 o successivo, con il suo tipo vettoriale nativo. Se non ne fai già girare uno, basta un container:

```bash
docker run -d --name rag-mariadb -p 3306:3306 \
    -e MARIADB_ROOT_PASSWORD=secret -e MARIADB_DATABASE=rag \
    mariadb:11.8
```

### Scambia lo store

```php
use NeuronAI\RAG\Schema\DocumentField;
use NeuronAI\RAG\Schema\DocumentSchema;
use NeuronAI\RAG\VectorStore\MariaDBVectorStore;

protected function vectorStore(): VectorStoreInterface
{
    return new MariaDBVectorStore(
        pdo: new \PDO(
            env('RAG_DSN', 'mysql:host=127.0.0.1;port=3306;dbname=rag'),
            env('RAG_DB_USER', 'root'),
            env('RAG_DB_PASSWORD', 'secret'),
        ),
        topK: 5,
        schema: DocumentSchema::of(
            DocumentField::string('section')->filterable(),
            DocumentField::string('language')->filterable(),
        ),
    );
}
```

Crea la tabella una volta, dimensionata per le 768 dimensioni di `nomic-embed-text`, con gli stessi dati di connessione:

```php
$pdo = new \PDO(
    env('RAG_DSN', 'mysql:host=127.0.0.1;port=3306;dbname=rag'),
    env('RAG_DB_USER', 'root'),
    env('RAG_DB_PASSWORD', 'secret'),
);

(new MariaDBVectorStore(pdo: $pdo))->setupTable(dimensions: 768);
```

Un metodo cambiato. Tutto il resto — l'agent, il loader, lo splitter, gli script — è intatto. È l'architettura guidata dalle interfacce della Sezione 2.2 che si ripaga sul layer dei dati, ed è più convincente quando lo vedi accadere che quando lo leggi.

I campi dello schema sono opzionali (niente `required()`), quindi i documenti del Laboratorio 8, che non portano metadati, si indicizzano comunque senza problemi; semplicemente non corrisponderanno a un filtro su quei campi.

### Aggiungi metadati durante l'ingestion

```php
$documents = FileDataLoader::for($directory)
    ->withSplitter(new MarkdownSectionSplitter(maxChars: 2000))
    ->getDocuments();

foreach ($documents as $document) {
    // The first line of each chunk is its heading
    $document->addMetadata('section',  \strtok($document->getContent(), "\n") ?: 'untitled');
    $document->addMetadata('language', 'en');
}

DocsAgent::make()->reindexBySource($documents);
```

`reindexBySource()` invece di `addDocuments()`, così rieseguire lo script sostituisce i chunk di ogni file invece di duplicarli — il che funziona solo perché `MarkdownSectionSplitter` passa il source name di ogni file ai suoi chunk.

### Misuralo

Costruisci un evaluator (Capitolo 10) con quindici domande reali sulla tua documentazione:

```php
namespace App\Neuron\Evaluators;

use App\Rag\DocsAgent;
use NeuronAI\Agent\AgentInterface;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Evaluation\Assertions\Judges\FaithfulnessJudge;
use NeuronAI\Evaluation\Assertions\StringContainsAny;
use NeuronAI\Evaluation\BaseEvaluator;
use NeuronAI\Evaluation\Contracts\DatasetInterface;
use NeuronAI\Evaluation\Dataset\JsonDataset;

class DocsRagEvaluator extends BaseEvaluator
{
    protected AgentInterface $judge;

    public function setUp(): void
    {
        $this->judge = /* a cheap judge agent */;
    }

    public function getDataset(): DatasetInterface
    {
        return new JsonDataset(__DIR__ . '/datasets/docs-questions.json');
    }

    public function run(array $item): mixed
    {
        return DocsAgent::make()
            ->chat(new UserMessage($item['question']))
            ->getMessage()
            ?->getContent() ?? '';
    }

    public function evaluate(mixed $output, array $item): void
    {
        $this->assert(new StringContainsAny($item['expected_keywords']), $output);

        $this->assert(new FaithfulnessJudge(
            judge: $this->judge,
            context: $item['source_excerpt'],
            threshold: 0.7,
        ), $output, 'faithfulness');
    }
}
```

Il terzo argomento di `assert()` dà un'etichetta al punteggio, così il report mostra una metrica `faithfulness` invece del nome di classe del judge — comodo quando stai per confrontarne quattro run.

Eseguilo su entrambi gli store ed entrambi gli splitter. Quattro configurazioni, un numero ciascuna.

**Quella tabella è il risultato di questo laboratorio.** Non il codice: la misura. È la differenza fra "abbiamo migliorato il RAG" e "la fedeltà è passata da 0,62 a 0,81 quando abbiamo cambiato splitter, e cambiare store non ha cambiato nulla".

Il secondo risultato vale quanto il primo, ed è il tipo di risultato che tirando a indovinare non otterrai mai. Qui è anche quello probabile: il file store e MariaDB ordinano con la stessa similarità del coseno, quindi passare dall'uno all'altro ti fa guadagnare durabilità, concorrenza e filtraggio su larga scala — non risposte migliori. Le risposte migliori vengono dallo splitter, dal reranker e dalle istruzioni.

### Criteri di accettazione

- Solo `vectorStore()` differisce fra gli agent del Laboratorio 8 e del 9.
- Hai una tabella a quattro righe di punteggi di fedeltà.
- Una query filtrata per metadati dimostrabilmente non può restituire documenti fuori da quel filtro: testalo con i documenti di due tenant in un unico indice. `chapters/Ch12/run/isolation.php` del repository di accompagnamento è un punto di partenza.
- Un filtro su un campo non dichiarato, come `Filter::eq('author', 'me')`, lancia un'eccezione invece di restituire un risultato vuoto.

## Esercizi del capitolo

1. **Confronta gli splitter.** Indicizza un corpus di documentazione reale con lo splitter di default e con uno personalizzato. Confronta su quindici domande, usando l'evaluator invece della tua impressione.
2. **Dimostra l'isolamento.** Aggiungi i metadati di tenant e verifica che una query filtrata non possa restituire i documenti di un altro tenant. È un test di sicurezza; scrivilo come tale.
3. **Reindicizza.** Cambia un file sorgente e reindicizza con `reindexBySource()`. Conferma che i vecchi chunk siano spariti: cerca una frase che hai cancellato.
4. **Riferisci.** Registra il punteggio di fedeltà per ciascuna configurazione e scrivi il riassunto di un paragrafo che manderesti a un cliente. Se il riassunto onesto è "la modifica costosa non ha fatto nulla", quella è la frase più preziosa del rapporto.
