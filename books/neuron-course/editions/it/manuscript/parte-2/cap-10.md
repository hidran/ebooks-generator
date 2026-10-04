# Capitolo 10 — Observability, eval e testing

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

La versione eseguibile di ogni listato che segue si trova in [`chapters/Ch10`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch10), nel repository di accompagnamento. Clonalo, esegui `composer install` e gli esempi funzionano su un Ollama locale senza alcuna API key.
:::

## 10.1 Perché non puoi debuggare un agent

### Il problema, con le parole degli autori del framework

La documentazione di Inspector per NeuronAI si apre con un passaggio insolitamente onesto per una documentazione di prodotto:

Integrare agent AI significa che non stai lavorando solo con funzioni e codice deterministico: stai programmando influenzando distribuzioni di probabilità. Stesso input ≠ stesso output. Riproducibilità, versioning e debugging diventano problemi reali. Il prompting non è programmazione nel senso comune: niente tipi statici, piccole modifiche rompono l'output, i prompt lunghi costano latenza, e non ci sono due modelli che si comportino allo stesso modo con lo stesso prompt.

È la Sezione 1.5, ripetuta dalle persone che hanno costruito lo strumento.

### Che cosa si rompe

**I breakpoint.** Puoi entrare passo passo nel tuo PHP. Non puoi entrare nella decisione del modello. Il momento interessante — *perché ha scelto quel tool?* — accade sulla GPU di qualcun altro.

**La riproduzione.** "Passi per riprodurre" presuppone il determinismo. Rieseguire l'input che fallisce può funzionare benissimo.

**I log come li scrivi tu.** Una riga di log che dice "l'agent ha risposto" non ti dice nulla. Ti serve il prompt, i tool offerti, il tool selezionato, gli argomenti, il risultato, i token e i tempi — per ogni iterazione.

**Il tuo modello mentale di stack trace.** L'esecuzione di un agent non è uno stack di chiamate. È una sequenza di decisioni, e il fallimento di solito sta nel ragionamento, non nel codice.

### Che cosa lo sostituisce

| Pratica classica | Equivalente agentico |
|---|---|
| Breakpoint | Trace di esecuzione |
| Passi per riprodurre | Un dataset di input rappresentativi |
| Test unitari | Eval con asserzioni basate su proprietà |
| Tasso di errore | Punteggio di qualità tracciato nel tempo |
| Stack trace | Linea temporale di nodi, tool e token |

Tre di queste cinque sono trattate in questo capitolo. Le altre due — dataset e tracciamento della qualità — sono lo stesso strumento visto nel tempo.

### La versione in una frase

> Non puoi debuggare un agent. Puoi solo osservarlo e misurarlo.

Ed è per questo che l'observability era un pilastro nella Sezione 2.1 e non un'appendice.

### Punti chiave

- Breakpoint, riproduzione e asserzioni di uguaglianza presuppongono tutti il determinismo.
- I trace sostituiscono il debugging; le eval sostituiscono i test unitari; i punteggi di qualità sostituiscono i tassi di errore.
- Per questo l'observability è architetturale, non operativa.

## 10.2 Configurare l'observability

### Gli eventi, e chi li ascolta

Ogni agent, RAG e workflow emette eventi mentre gira: l'inizio e la fine di ogni nodo, ogni inferenza, ogni tool call, ogni retrieval. Sono eventi PSR-14 — oggetti semplici, una classe per tipo, tutti estensioni di `NeuronAI\Observability\ObservabilityEvent` — e ogni istanza possiede il proprio dispatcher. Non esiste un registro globale. L'observability è ciò che sottoscrivi a quel dispatcher.

`subscribe()` funziona su **Agent, RAG e Workflow** — che è ancora la Sezione 2.3: sono tutti workflow, quindi emettono tutti gli stessi eventi.

### Parti in locale: un logger

```php
use NeuronAI\Agent\Observability\ToolCalled;
use NeuronAI\Observability\LogListener;
use NeuronAI\Observability\ObservabilityEvent;

$agent = WeatherAgent::make()
    ->subscribe(ObservabilityEvent::class, new LogListener($logger))
    ->subscribe(ToolCalled::class, function (ToolCalled $event): void {
        echo $event->tool->getName() . ' ' . json_encode($event->tool->getInputs()) . PHP_EOL;
    });
```

La corrispondenza avviene per classe, con la semantica di `instanceof`. Sottoscrivere `ObservabilityEvent::class` riceve tutto, che è ciò che vuole `LogListener`: scrive il nome e i dati di ogni evento su qualunque logger PSR-3. Sottoscrivere `ToolCalled::class` riceve solo le tool call concluse. I listener appartengono all'istanza, quindi vedono ogni sua run, comprese le run riprese.

Gli eventi vivono nel namespace `Observability` del modulo che li emette: `NeuronAI\Agent\Observability` per gli eventi di inferenza, tool, messaggi e output strutturato, `NeuronAI\Workflow\Observability` per il ciclo di vita del workflow, `NeuronAI\RAG\Observability` per il retrieval. Controlla la riga `use`. `subscribe()` riceve il nome della classe come stringa, quindi un listener registrato su un nome che non esiste — `NeuronAI\Observability\Events\ToolCalled`, come lo stampano gli articoli più vecchi — non genera alcun errore. Semplicemente non scatta mai. Quando un listener resta muto, il primo sospettato è l'import.

Eseguilo e il ciclo appare in ordine: `workflow-start`; poi, con ogni nodo racchiuso fra un `workflow-node-start` e un `workflow-node-end`, `inference-start`, `inference-stop`, `message-saving`, `message-saved`, `tool-calling`, `tool-called`, una seconda inferenza; e infine `workflow-end`. È già più di "l'agent ha risposto", e non costa nulla. Per tempi, conteggi dei token e una timeline in cui cercare fra migliaia di run, ti serve un backend di tracing.

Altre due cose vanno dette qui. Se la tua applicazione ha già un dispatcher PSR-14, `setEventDispatcher()` gli inoltra ogni evento dopo che hanno girato i listener dell'agent. E l'API più vecchia che troverai negli articoli — `observe()` con un `ObserverInterface` o un `LogObserver` — funziona ancora tramite un adapter, ma è deprecata. Scrivi il codice nuovo con `subscribe()`.

### Inspector

Inspector è il backend di tracing accanto al quale NeuronAI è stato costruito. La guida al monitoraggio attuale dei maintainer documenta una seconda opzione, Neuron Cloud, una piattaforma hosted distribuita come `neuron-core/cloud-sdk` per PHP puro, `neuron-core/neuron-cloud-laravel` e `neuron-core/neuron-cloud-symfony`. Quando questo libro è stato verificato nessuno dei tre era su Packagist (Appendice A, punto 55): controlla prima di farci affidamento. Sono lo stesso meccanismo — un listener PSR-14 sottoscritto a `ObservabilityEvent::class` — quindi tutto ciò che segue sulla sottoscrizione vale per entrambi; questo capitolo mostra Inspector. Nessuno dei due è obbligatorio: il framework non dipende da nessuno dei due e non aggancia nulla da solo. Ne installi uno, e lo sottoscrivi.

```bash
composer require "inspector-apm/inspector-php:^3.19"
```

Ti serve la versione 3.19 o successiva per il namespace `Inspector\Neuron\V4`. Le release 3.18.x contengono un subscriber scritto per un namespace di una pre-release: si carica, si sottoscrive senza lamentele e non registra nulla. `inspector-laravel`, `inspector-symfony` e gli altri pacchetti per framework installano il pacchetto per te; richiedilo comunque nel `composer.json` della tua applicazione, e verifica che la versione risolta sia la 3.19 o successiva.

### La variabile d'ambiente

```dotenv
INSPECTOR_INGESTION_KEY=nwse877auxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Crea una chiave registrando un'applicazione su `app.inspector.dev`.

### Sottoscrivere il listener

```php
use Inspector\Neuron\V4\InspectorSubscriber;
use NeuronAI\Observability\ObservabilityEvent;

$agent = MyAgent::make()
    ->subscribe(ObservabilityEvent::class, InspectorSubscriber::instance());
```

`InspectorSubscriber::instance()` legge `INSPECTOR_INGESTION_KEY` dall'ambiente. Quando non hai un ambiente da leggere, passa la chiave come primo argomento:

```php
InspectorSubscriber::instance('your-ingestion-key')
```

Quando il tuo framework possiede già un'istanza di `Inspector`, come fanno Laravel e Symfony, costruisci invece il listener attorno a essa — `new InspectorSubscriber($inspector)` — così i segmenti dell'agent finiscono dentro la transazione che il framework ha aperto per la richiesta o il job.

### L'impostazione che non ti serve, e l'errore da cercare

È la sezione operativamente più importante del capitolo.

**Un agent che non hai sottoscritto non viene tracciato.** Impostare `INSPECTOR_INGESTION_KEY` non basta: la chiave configura un subscriber, non ne aggancia uno. Una sottoscrizione mancante non produce trace né errori, quindi la conclusione naturale — "Inspector è rotto" — è sbagliata.

Per coprire tutti gli agent, sottoscrivi dove gli agent vengono costruiti — una classe base condivisa, una factory, il container — invece che in ogni punto di chiamata:

```php
use Inspector\Neuron\V4\InspectorSubscriber;
use NeuronAI\Agent\Agent;
use NeuronAI\Agent\AgentState;
use NeuronAI\Observability\ObservabilityEvent;

abstract class MonitoredAgent extends Agent
{
    public function __construct(?string $workflowId = null, ?AgentState $state = null)
    {
        parent::__construct($workflowId, $state);

        $this->subscribe(ObservabilityEvent::class, InspectorSubscriber::instance());
    }
}
```

Mantieni la firma a due parametri del genitore e inoltrala. `make()` passa i suoi argomenti direttamente al costruttore, e il workflow ID di un agent è l'ID del thread di conversazione, quindi `MyAgent::make(workflowId: $threadId)` continua a funzionare.

Ciò che non configuri è il flush. Il materiale più vecchio ti dice di abilitare `autoFlush` per i processi a lunga esecuzione — queue worker, Swoole, RoadRunner — dove gli eventi si accumulerebbero in memoria in attesa di una fine della richiesta che non arriva mai. Quell'opzione non esiste. Quando è il subscriber ad aver aperto la transazione, invia il trace non appena il workflow termina, run per run. Quando l'ha aperta l'applicazione ospite, il subscriber lascia il flush all'ospite.

Dato che la Sezione 1.4 spinge il lavoro lungo degli agent sulle code e la Sezione 5.13 richiede CLI per i tool paralleli, **la maggior parte dei deploy seri di NeuronAI gira in worker — e in un worker il guasto da cercare è un agent che non è mai stato sottoscritto.**

### Pacchetti specifici per framework

Se stai integrando in Laravel o Symfony, aggiungi il pacchetto del framework (`inspector-laravel`, `inspector-symfony`) per una raccolta dati migliore. Non è obbligatorio, ma è consigliato: correla il trace dell'agent con la richiesta HTTP, le query e il job in coda attorno, che è ciò che vuoi davvero quando diagnostichi un incidente in produzione. Passa la sua istanza di `Inspector` al subscriber, come mostrato sopra, così i due finiscono nello stesso trace.

Il Capitolo 23 lo tratta nel contesto Laravel.

::: {.callout .callout-warning}
[Deriva dei namespace]{.callout-title}

Nell'ecosistema compaiono quattro nomi per questo componente, e solo il primo funziona con il NeuronAI usato in questo libro:

- `Inspector\Neuron\V4\InspectorSubscriber` — il listener PSR-14 che questo capitolo sottoscrive
- `Inspector\Neuron\InspectorObserver` — stesso pacchetto, ma scritto per l'API observer delle versioni precedenti di NeuronAI
- `NeuronAI\Observability\InspectorObserver` — dalle versioni precedenti del framework; non esiste più
- `NeuronAI\Observability\AgentMonitoring` — articoli più vecchi, e ancora in alcuni esempi di structured output

Il secondo è quello pericoloso: si risolve, e collegarlo tramite il deprecato `observe()` sembra funzionare. È il posto più probabile in cui copiare un'istruzione `use` dalla versione sbagliata. Appendice A, punto 16.
:::

### Punti chiave

- Ogni agent, RAG e workflow emette eventi PSR-14; sottoscrivi un listener con `subscribe()` per vederli.
- `LogListener` per la visibilità in locale, non costa nulla.
- Inspector (o Neuron Cloud) è opzionale: `composer require "inspector-apm/inspector-php:^3.19"`, imposta la chiave, sottoscrivi `InspectorSubscriber`.
- Un listener sottoscritto a una classe che non esiste non scatta mai e non genera errori; gli eventi vivono in `NeuronAI\Agent\Observability`, `NeuronAI\Workflow\Observability` e `NeuronAI\RAG\Observability`.
- Nulla viene agganciato automaticamente. Sottoscrivi in una classe base o in una factory così che nessun agent sfugga.
- Nessun `autoFlush` da impostare: il subscriber invia il trace di ogni run quando il workflow termina.
- Usa `Inspector\Neuron\V4\InspectorSubscriber`; gli altri tre nomi appartengono a versioni precedenti.

## 10.3 Leggere un trace

### Che cosa mostra un trace

Ogni passo di inferenza, ogni chiamata a tool, ogni retrieval — con argomenti, risultati, conteggi di token e tempi.

Esegui l'agent meteo del Laboratorio 3 con Inspector sottoscritto e ottieni una linea temporale:

```
▸ WeatherAgent                                        4.82s   3,641 tokens
  ├─ ChatNode                          1.31s     892 in / 84 out
  ├─ ToolNode: get_current_weather     0.42s
  │    input:  {"latitude": 45.0703, "longitude": 7.6869}
  │    output: {"temperature_2m": 14.2, ...}
  ├─ ToolNode: get_current_weather     0.38s
  │    input:  {"latitude": 45.4642, "longitude": 9.19}
  ├─ ChatNode                          1.44s   1,203 in / 61 out
  ├─ ToolNode: mean                    0.01s
  └─ ChatNode                          1.26s   1,310 in / 91 out
```

### Le quattro domande a cui rispondere da un trace

Trattalo come una procedura, non come un "guarda in giro":

**1. Quante chiamate al modello?**
Tre, qui. Il modello di costo della Sezione 1.4, reso visibile. Se te ne aspettavi una, hai un problema di progetto.

**2. Quali tool, con quali argomenti?**
È qui che i bug di tool sbagliato e argomento sbagliato sono visibili. Il modello ha chiamato `get_current_weather` con le coordinate di Torino, quindi le ha derivate correttamente. Se avesse passato il nome della città come stringa, alla descrizione della tua proprietà (Sezione 5.4) serve l'esempio svolto.

**3. Dov'è finito il tempo?**
Chiamate al modello: 4,01 s. Tool: 0,81 s. Il modello è il collo di bottiglia, quindi ottimizzare significa meno iterazioni, non tool più veloci. Se il rapporto fosse invertito, metteresti in cache il tool.

**4. Dove sono finiti i token?**
892 → 1.203 → 1.310 token in ingresso. Crescono, perché cresce la conversazione. Esattamente l'accumulo della Sezione 1.4, ora misurato invece che stimato.

### Diagnosticare dai trace: tre pattern

**Lo stesso tool chiamato cinque volte con argomenti quasi identici.**
Il modello non crede di aver ottenuto una risposta. Il valore restituito dal tuo tool è ambiguo, oppure la sua descrizione non corrisponde a ciò che fa. Sistema il tool, non il limite di esecuzioni.

**Un lungo intervallo prima della prima chiamata a tool.**
Il modello ha passato tempo a decidere. Di solito troppi tool, o descrizioni sovrapposte. Filtra (Sezione 5.8) o aggiungi `ToolSearchMiddleware`.

**Token in ingresso molto più alti del previsto alla prima chiamata.**
I tuoi schemi dei tool sono grandi. Conta i tool collegati. Lo schema completo di ciascuno è in ogni richiesta.

### L'esercizio che insegna meglio di tutti

Non limitarti a guardare un trace sano. **Rompi qualcosa e leggi il trace.**

Cambia la descrizione di `get_current_weather` in `'Gets the weather.'` e riesegui. Il trace mostra il modello che risponde senza alcuna chiamata a tool. Il codice è identico; l'unico cambiamento è una stringa; il trace mostra che il modello non ha nemmeno preso in considerazione il tool.

È il momento in cui la Sezione 5.4 diventa reale.

### Punti chiave

- Quattro domande: quante chiamate, quali tool con quali argomenti, dov'è finito il tempo, dove sono finiti i token.
- Chiamate identiche ripetute significano un tool ambiguo, non un limite basso.
- Leggi un trace rotto, non solo uno sano.

## 10.4 Eval: PHPUnit per sistemi non deterministici

### L'inquadratura che fa scattare la comprensione

Pensa a una eval come a **PHPUnit per un servizio che non è deterministico.**

Un test unitario conosce l'output atteso perché la funzione è deterministica. A un agent a cui poni due volte la stessa domanda può dare due risposte entrambe corrette e formulate diversamente. Non puoi asserire l'uguaglianza.

Quello che puoi fare: definire un dataset di input realistici, eseguire l'agent su ciascuno e asserire che l'output soddisfi dei criteri — contiene parole chiave, resta entro un intervallo di lunghezza, corrisponde a un pattern, o supera il giudizio di un altro agent nel ruolo di revisore.

### Configurare il progetto

Tieni gli evaluator fuori dal codice di produzione:

```json
"autoload-dev": {
    "psr-4": {
        "App\\Evaluators\\": "evaluators/"
    }
},
```

```bash
mkdir -p evaluators/datasets
composer dump-autoload
```

`autoload-dev` è la scelta giusta: il codice di valutazione è per lo sviluppo e la QA, e non deve finire in produzione.

### Generare un evaluator

```bash
# Unix
vendor/bin/neuron make:evaluators App\\Evaluators\\AgentEvaluator

# Windows
.\vendor\bin\neuron make:evaluators App\Evaluators\AgentEvaluator
```

Il comando è `make:evaluators`, al plurale, su ogni piattaforma. La documentazione ufficiale mostra `make:evaluator` nella scheda Unix; quel comando non esiste. Appendice A, punto 17.

::: {.callout .callout-warning}
[Il generatore ignora `autoload-dev`]{.callout-title}

`make:evaluators` ricava la directory di destinazione solo dalla sezione `autoload` di `composer.json`. In un progetto il cui `autoload` mappa `App\` su `app/` — ogni applicazione Laravel — `App\Evaluators\AgentEvaluator` corrisponde a quel prefisso di produzione e il file finisce in `app/Evaluators/`, non in `evaluators/`. Senza un prefisso corrispondente, il comando emette un avviso e scrive sotto la directory corrente. L'esempio della documentazione stessa, `App\Neuron\Evaluators\AgentEvaluator`, fa la stessa cosa e aggiunge un namespace che non corrisponde a nessuno dei due. Genera, poi sposta il file in `evaluators/`, oppure scrivi gli evaluator a mano: la struttura qui sotto è tutto ciò che li compone. Appendice A, punto 20.
:::

### La struttura a tre metodi

```php
namespace App\Evaluators;

use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Evaluation\Assertions\StringContains;
use NeuronAI\Evaluation\BaseEvaluator;
use NeuronAI\Evaluation\Contracts\DatasetInterface;
use NeuronAI\Evaluation\Dataset\JsonDataset;
use NeuronAI\UniqueIdGenerator;

class AgentEvaluator extends BaseEvaluator
{
    /**
     * 1. Get the dataset to evaluate against
     */
    public function getDataset(): DatasetInterface
    {
        return new JsonDataset(__DIR__ . '/datasets/dataset.json');
    }

    /**
     * 2. Run the agent logic being tested
     */
    public function run(array $datasetItem): mixed
    {
        $state = MyAgent::make()
            ->setThreadId(UniqueIdGenerator::generateId('eval_'))
            ->chat(new UserMessage($datasetItem['input']));

        return $state->getMessage()?->getContent() ?? '';
    }

    /**
     * 3. Evaluate the output against expected results
     */
    public function evaluate(mixed $output, array $datasetItem): void
    {
        $this->assert(
            new StringContains($datasetItem['reference']),
            $output,
        );
    }
}
```

Carica un dataset, esegui ogni elemento, asserisci sull'output. È tutto il modello, e la sua semplicità è una funzionalità: la forma è familiare a chiunque abbia scritto un data provider in PHPUnit.

Due dettagli in `run()`. `chat()` restituisce l'`AgentState` finale, e il suo `getMessage()` può essere null, quindi l'evaluator passa all'asserzione una stringa vuota invece di un null: un'asserzione su stringhe che riceve qualcosa che non è una stringa segnala l'elemento come errore, non come fallimento. E ciò che `run()` restituisce è ciò che `evaluate()` riceve come `$output`: qui una stringa, una traiettoria di conversazione nella Sezione 10.5.

Associa un ID di thread in `run()`, come sopra. Un agent non ha un ID di thread finché non glielo dai, e `chat()` lancia un'eccezione senza; un ID nuovo per ogni elemento fa anche sì che nessun elemento veda la conversazione di un altro.

### Dataset

**`ArrayDataset`** — inline, buono per una manciata di casi:

```php
public function getDataset(): DatasetInterface
{
    return new ArrayDataset([
        [
            'input' => 'Hi',
            'reference' => 'help'
        ]
    ]);
}
```

**`JsonDataset`** — un file, che è ciò che vuoi in pratica:

```php
return new JsonDataset(__DIR__ . '/datasets/dataset.json');
```

**Non c'è un formato prescritto.** L'evaluator carica un elenco di casi di test; le chiavi sono tue. `input` e `reference` sono convenzioni degli esempi, non requisiti. Puoi implementare `DatasetInterface` per caricare da qualunque fonte: un database, un CSV, i log di produzione.

Quest'ultima opzione è quella da evidenziare: **costruisci il tuo dataset dai fallimenti reali.** Ogni volta che un utente segnala una risposta cattiva, aggiungi l'input al dataset. La tua suite di eval diventa una suite di regressione esattamente sulle cose che si sono davvero rotte.

### Punti chiave

- Le eval sono PHPUnit per servizi non deterministici.
- Tre metodi: `getDataset()`, `run()`, `evaluate()`.
- `ArrayDataset` per pochi casi, `JsonDataset` per suite vere, `DatasetInterface` per tutto il resto.
- Fai crescere il dataset dai fallimenti realmente segnalati.

## 10.5 Asserzioni e l'AI come giudice

### Le asserzioni integrate

```php
$this->assert(new StringContains('positive'), $output);
$this->assert(new StringContainsAll(['hello', 'world']), $output);
$this->assert(new StringContainsAny(['success', 'completed']), $output);
$this->assert(new StringStartsWith('Hello'), $output);
$this->assert(new StringEndsWith('!'), $output);
$this->assert(new StringLengthBetween(10, 100), $output);
$this->assert(new MatchesRegex('/^\d{3}-\d{2}-\d{4}$/'), $output);
$this->assert(new IsValidJson(), $output);
```

Altre due più interessanti:

**`StringDistance`** — similarità di Levenshtein:

```php
$this->assert(new StringDistance(
    reference: 'expected text',
    threshold: 0.5,   // minimum similarity score
    maxDistance: 50   // maximum allowed edits
), $output);
```

**`StringSimilarity`** — similarità semantica tramite embedding:

```php
use NeuronAI\Evaluation\Assertions\StringSimilarity;
use NeuronAI\RAG\Embeddings\OpenAIEmbeddingsProvider;

$this->assert(new StringSimilarity(
    reference: 'The quick brown fox',
    embeddingsProvider: new OpenAIEmbeddingsProvider(key: 'YOUR_KEY', model: 'text-embedding-3-small'),
    threshold: 0.6
), $output);
```

Vale la pena esplicitare la distinzione. `StringDistance` misura la similarità fra *caratteri*: "colour" e "color" sono vicini. `StringSimilarity` misura il *significato*: "il gatto stava sul tappeto" e "un felino riposava sulla stuoia" sono vicini pur non condividendo quasi nessun carattere.

Per valutare output in linguaggio naturale, la similarità semantica è quasi sempre quella che vuoi. Costa una chiamata di embedding per asserzione, il che è poco.

È anche la prima comparsa del componente embedding, che è tutto il Capitolo 12.

### L'AI come giudice

Alcune qualità non si misurano con operazioni su stringhe. La risposta è cortese? Utile? Fondata sulla fonte o allucinata?

Per queste, usa un altro agent come valutatore:

```php
use NeuronAI\Evaluation\Assertions\AgentJudge;

class AgentJudgeEvaluator extends BaseEvaluator
{
    protected AgentInterface $judge;

    public function setUp(): void
    {
        $this->judge = Agent::make()
            ->setAiProvider(new Anthropic(/* ... */))
            ->setInstructions('You are an expert evaluator for customer support responses.');
    }

    public function getDataset(): DatasetInterface
    {
        return new JsonDataset(/* ... */);
    }

    public function run(array $datasetItem): mixed
    {
        return MyAgent::make()
            ->setThreadId(UniqueIdGenerator::generateId('eval_'))
            ->chat(new UserMessage($datasetItem['input']))
            ->getMessage()
            ?->getContent() ?? '';
    }

    public function evaluate(mixed $output, array $datasetItem): void
    {
        $this->assert(new AgentJudge(
            judge: $this->judge,
            criteria: 'Response should be helpful, polite, and address the customer\'s question directly',
            threshold: $datasetItem['threshold']
        ), $output);
    }
}
```

Il giudice è un normale agent configurato in modo fluente: `setAiProvider()` e `setInstructions()` fanno parte di `AgentInterface`, quindi funziona su qualunque agent, non solo su un semplice `Agent::make()`. L'asserzione chiede al giudice un punteggio strutturato fra 0 e 1 insieme al suo ragionamento, quindi il modello del giudice deve supportare lo structured output.

::: {.callout .callout-warning}
[Un refuso da evitare]{.callout-title}

L'esempio ufficiale di questo blocco scrive male `Anthropic` come `Antrhopic`. Copialo e la classe non si risolve. Appendice A, punto 21.
:::

### I giudici specializzati

NeuronAI include giudici per le domande di valutazione ricorrenti, in `NeuronAI\Evaluation\Assertions\Judges`:

**`FaithfulnessJudge`** — l'output è fondato sul contesto fornito, o ha allucinato?

```php
$this->assert(new FaithfulnessJudge(
    judge: $this->judge,
    context: $retrievedContext,
    threshold: 0.7
), $output);
```

`context` è una stringa: unisci il contenuto dei documenti recuperati prima di passarlo.

**È l'asserzione più importante in assoluto per i sistemi RAG**, ed è il motivo per cui le eval compaiono prima della Parte III e non dopo. Un sistema RAG che risponde in modo fluente a partire da informazioni che si è inventato è peggio di uno che dice "non lo so". La fedeltà è come lo misuri, e non puoi misurarla con la corrispondenza di stringhe.

**`CorrectnessJudge`** — corrisponde alla risposta attesa?

```php
$this->assert(new CorrectnessJudge(
    judge: $this->judge,
    expected: $datasetItem['expected_answer'],
    threshold: 0.7
), $output);
```

**`RelevanceJudge`** — affronta davvero la domanda? Riceve la `question` originale insieme al giudice.

**`HelpfulnessJudge`** — è utile e azionabile?

**`TaskCompletionJudge`** — l'agent ha raggiunto un `goal` dichiarato nell'arco di un'intera conversazione? Questo legge una traiettoria invece di una singola risposta; la prossima sezione mostra da dove vengono le traiettorie.

### Dai un nome alla metrica

Ogni `assert()` registra un punteggio, e per default il punteggio viene archiviato sotto il nome della classe dell'asserzione. Passa un terzo argomento per dare tu un nome alla metrica:

```php
$this->assert(new FaithfulnessJudge(
    judge: $this->judge,
    context: $retrievedContext,
), $output, 'faithfulness');
```

L'etichetta è ciò su cui il report aggrega: il riepilogo in console e l'output JSON mostrano media, minimo, massimo e conteggio per etichetta. Conta non appena hai due asserzioni della stessa classe che misurano cose diverse — due `AgentJudge`, uno per il tono e uno per l'accuratezza, sono indistinguibili senza di essa — e ti dà nomi di metriche che sopravvivono al refactoring dell'asserzione che le produce.

### Valutare ciò che l'agent ha fatto, non solo ciò che ha detto

Un'asserzione su stringhe vede la risposta finale. Per un agent con dei tool è spesso la parte meno interessante: la domanda è se ha chiamato il tool giusto, con gli argomenti giusti, e se non ha chiamato quello che avrebbe dovuto lasciare stare.

Per questo, `run()` guida l'agent attraverso una `Conversation` e ne restituisce la `Trajectory`, una vista in sola lettura sui messaggi prodotti dalla run:

```php
use NeuronAI\Evaluation\Assertions\StringContains;
use NeuronAI\Evaluation\Assertions\Trajectory\ToolWasCalled;
use NeuronAI\Evaluation\Assertions\Trajectory\ToolWasNotCalled;
use NeuronAI\Evaluation\Conversation\Conversation;

public function run(array $datasetItem): mixed
{
    return Conversation::make(WeatherAgent::make())
        ->withTurns([$datasetItem['input']])
        ->run();
}

public function evaluate(mixed $trajectory, array $datasetItem): void
{
    $this->assert(new ToolWasCalled('get_current_weather', ['latitude' => 45.07]), $trajectory);
    $this->assert(new ToolWasNotCalled('delete_forecast'), $trajectory);
    $this->assert(new StringContains('Turin'), $trajectory->finalAnswer());
}
```

`ToolWasCalled` accetta un vincolo opzionale sugli argomenti: un sottoinsieme degli input, come qui, oppure una closure. `TrajectoryMatches` fa asserzioni sulla sequenza dei nomi dei tool, in modo rigido o lasco. `ToolWasApproved` e `ToolWasRejected` controllano che cosa è successo al controllo di approvazione, e `withApprovals()` sulla conversazione fa la parte dell'essere umano quando l'agent va in pausa (Capitolo 15). Le asserzioni su stringhe si applicano a `finalAnswer()`; ogni giudice accetta la traiettoria stessa e ne legge la trascrizione.

È qui che le eval per gli agent smettono di essere eval per chatbot. Un agent che dà la risposta giusta dopo aver chiamato un tool che non avrebbe mai dovuto toccare ha superato un'asserzione su stringhe e ha tradito te.

### Due cautele sui giudici

**Anche il giudice è non deterministico.** Stai misurando un sistema probabilistico con uno strumento probabilistico. Le soglie assorbono la cosa, ma non trattare il punteggio di un giudice come verità assoluta. Tracciarlo nel tempo e cerca movimenti, non valori assoluti.

**I giudici costano.** Ogni asserzione giudicata è una chiamata LLM extra. Un dataset da 200 elementi con tre asserzioni giudicate sono 600 chiamate extra per esecuzione. Non risparmiare dando al giudice un modello più debole di quello dell'agent: un giudice più debole assegna punteggi più rumorosi, e finisci per tarare il sistema sul rumore. Controlla il costo in altro modo: con `--cache` (Sezione 10.6), con un campione del dataset sulle pull request, e con asserzioni su stringhe o su traiettorie ovunque bastino. Qualunque giudice usi, confronta i suoi punteggi con un pugno di risposte che hai valutato a mano.

### Asserzioni personalizzate

```php
use NeuronAI\Evaluation\Assertions\AbstractAssertion;
use NeuronAI\Evaluation\AssertionResult;

class GreaterThanAssertion extends AbstractAssertion
{
    public function __construct(
        private readonly float $threshold
    ) {}

    public function evaluate(mixed $actual): AssertionResult
    {
        if (!is_numeric($actual)) {
            return AssertionResult::fail(
                0.0,
                'Expected numeric value, got ' . gettype($actual),
            );
        }

        if ($actual > $this->threshold) {
            return AssertionResult::pass(1.0);
        }

        return AssertionResult::fail(
            0.0,
            "Expected {$actual} to be greater than {$this->threshold}",
        );
    }
}
```

Nota `AssertionResult::pass(1.0)` e `fail(0.0)`: le asserzioni restituiscono un **punteggio**, non un booleano. È ciò che permette credito parziale e giudizio a soglia, ed è il dettaglio di progetto che rende questo un sistema di misura invece di un cancello passa/non passa.

### Punti chiave

- Dieci asserzioni integrate su stringhe; `StringSimilarity` per il significato, `StringDistance` per i caratteri.
- Cinque giudici: fedeltà, correttezza, rilevanza, utilità, completamento del compito.
- Dai un nome alla metrica con il terzo argomento di `assert()`; il report aggrega per etichetta.
- Le asserzioni sulla traiettoria verificano quali tool sono stati eseguiti, con quali argomenti: la parte che una risposta finale nasconde.
- `FaithfulnessJudge` è quello essenziale per il RAG: tienilo pronto prima della Parte III.
- I giudici sono non deterministici e costano; controlla il costo con `--cache`, il campionamento e asserzioni più economiche, non con un giudice più debole.
- Le asserzioni restituiscono punteggi, non booleani.

## 10.6 Eseguire le eval: output, parallelismo e CI

### Esecuzione

```bash
# Unix
vendor/bin/neuron evaluation --path=evaluators

# Windows
.\vendor\bin\neuron evaluation --path=evaluators
```

Il comando è `evaluation`, al singolare, e accetta la directory sia come `--path=evaluators` sia come semplice argomento posizionale: entrambe le forme della documentazione ufficiale funzionano. Se i tuoi evaluator vengono caricati tramite qualcosa di diverso dall'autoloader di Composer, aggiungi `--autoload-file=bootstrap.php`. `vendor/bin/neuron --help` elenca tutti i comandi della tua versione installata. Appendice A, punto 18.

Il comando esce con uno stato diverso da zero se un qualunque elemento fallisce. Tienilo a mente per la CI, più sotto.

### Driver di output

Crea `evaluation.php` nella radice del progetto:

```php
<?php

use NeuronAI\Evaluation\Output\ConsoleOutput;
use NeuronAI\Evaluation\Output\JsonOutput;

return [
    'output' => [
        ConsoleOutput::class,
        new JsonOutput(__DIR__ . '/evaluation-results.json'),
    ],
];
```

Nota la forma: `output` è una **lista**, non una mappa da classe a opzioni. `EvaluationOutputResolver` accetta o una stringa-classe o un'istanza già costruita. Non esiste alcun mapping delle opzioni via reflection: un driver che ha bisogno di un'opzione, come il percorso del file di `JsonOutput`, va passato già pronto. Una stringa-classe viene costruita dalla voce opzionale `resolver` di questo file — un `callable(class-string): object`, tipicamente il container dell'applicazione — oppure con un semplice `new` quando non ce n'è una, nel qual caso un driver il cui costruttore richiede argomenti viene rifiutato.

Più driver girano simultaneamente: la console per lo sviluppatore, JSON perché la CI lo consumi.

Senza file di configurazione, il sistema usa per default `[ConsoleOutput::class]`.

### Output personalizzato: il pattern che rende le eval uno strumento aziendale

```php
namespace App\Neuron\Evaluations;

use NeuronAI\Evaluation\Contracts\EvaluationOutputInterface;
use NeuronAI\Evaluation\Runner\EvaluationReport;

class DatabaseOutput implements EvaluationOutputInterface
{
    public function __construct(
        private readonly \PDO $pdo,
        private readonly string $table = 'evaluations'
    ) {}

    public function output(EvaluationReport $report): void
    {
        $results = $report->getResults();

        $stmt = $this->pdo->prepare(
            "INSERT INTO {$this->table} (passed, failed, success_rate, total_time, created_at, updated_at)
             VALUES (?, ?, ?, ?, NOW(), NOW())"
        );

        $stmt->execute([
            $results->getPassedCount(),
            $results->getFailedCount(),
            $results->getSuccessRate(),
            $report->getDuration(),
        ]);
    }
}
```

Un driver riceve l'`EvaluationReport` dell'intera esecuzione: un report per evaluator, gli istanti di inizio e fine, e `getResults()`, che appiattisce gli elementi di tutti gli evaluator in un unico insieme di conteggi. Per lo storico per metrica, `getResults()->getScoreStatisticsByLabel()` restituisce media, minimo, massimo e conteggio per ogni etichetta della Sezione 10.5: una riga per metrica per esecuzione è la tabella che vorrai mettere in grafico.

Registralo per classe e lascia che lo costruisca un resolver:

```php
return [
    'resolver' => fn (string $class): object => match ($class) {
        DatabaseOutput::class => new DatabaseOutput(new \PDO(/* ... */), 'evaluations'),
        default => new $class(),
    },
    'output' => [
        ConsoleOutput::class,
        DatabaseOutput::class,
    ],
];
```

Non scrivere `new DatabaseOutput(new \PDO(...))` nell'elenco. `evaluation.php` viene caricato prima che giri il primo elemento, quindi un driver costruito lì tiene una connessione viva quando `--concurrency` esegue il fork, e ogni figlio la eredita. Il runner costruisce i driver di output solo dopo che tutte le esecuzioni sono terminate, quindi un driver elencato come stringa-classe, con il resolver che ne fornisce la connessione, non ha mai una connessione al momento del fork. Anche connettersi dentro `output()` funziona.

**Perché conta oltre l'ingegneria.** Persistere il tasso di successo a ogni esecuzione ti dà una metrica di qualità nel tempo. Puoi metterla su un grafico. Puoi mostrarla a uno stakeholder. Puoi rispondere a "la modifica al prompt della settimana scorsa ha migliorato o peggiorato le cose?" con un numero invece che con un'opinione.

È il passaggio dalle eval come comodità per sviluppatori alle eval come prova. Per chi vende lavoro AI a un'azienda, è la differenza fra "fidati di me" e un grafico.

### Esecuzione parallela

La maggior parte del tempo di eval si passa ad aspettare il provider. Esegui gli elementi in concorrenza:

```bash
vendor/bin/neuron evaluation path/to/evaluators --concurrency=3
```

L'esempio documentato: una chiamata LLM da 2 secondi per elemento su un dataset da 100 elementi scende da circa 200 secondi a circa 66.

**Requisiti** — la stessa coppia della Sezione 5.13:

```bash
composer require --dev spatie/fork
```

più `pcntl` (Linux e macOS; non Windows). Se manca uno dei due, il comando stampa un avviso e ricade sul sequenziale, così lo stesso comando funziona ovunque.

**Scegliere un livello.** Ogni elemento in volo è una richiesta attiva al provider. Parti da 3–5 e aumenta finché eviti i rate limit. Gli errori di rate limit si presentano come fallimenti dei test, quindi se compaiono fallimenti quando alzi la concorrenza, abbassala prima di andare a caccia di un bug nel tuo agent.

### Quattro cose da sapere sulle esecuzioni parallele

**I risultati non cambiano.** Gli elementi sono indipendenti, l'ordine è preservato, il report è identico.

**Lo stato non è condiviso.** Ogni elemento vede lo stato al momento di `setUp()`. Gli effetti collaterali di un elemento sono invisibili agli altri. Se il tuo evaluator accumula stato fra gli elementi, eseguilo in sequenza.

**Gli output devono essere serializzabili.** Il valore restituito da `run()` attraversa un confine di processo tramite `serialize()`. Una closure o una connessione aperta non possono attraversarlo; i risultati delle asserzioni sopravvivono ma l'output riportato diventa un segnaposto.

**I tempi si leggono in modo strano.** Il tempo totale è tempo reale; la media per test è la durata reale per elemento. In parallelo la media può superare totale ÷ conteggio. Aspettatelo invece di aprire un bug.

### Mettere in cache le esecuzioni, non i verdetti

Buona parte del costo di un'eval è `run()`, e buona parte delle tue iterazioni riguarda `evaluate()`: stringere una soglia, riformulare i criteri di un giudice, aggiungere un'asserzione. `--cache` separa le due cose:

```bash
vendor/bin/neuron evaluation evaluators --cache
```

La prima esecuzione salva l'output di `run()` di ogni elemento sotto `.neuron/cache/evaluation/`. Le esecuzioni successive servono dalla cache gli elementi invariati e **rieseguono sempre le asserzioni**, così puoi iterare su `evaluate()` contro output congelati senza spendere nulla. `--fresh` riesegue tutto e sovrascrive la cache.

La chiave della cache copre il metodo `run()` dell'evaluator, l'elemento del dataset e la versione del framework. Non vede la classe del tuo agent né i tuoi file di prompt a meno che tu non li dichiari:

```php
public function cacheDependencies(): array
{
    return [MyAgent::class, __DIR__ . '/../prompts/support.md'];
}
```

Cambia una dipendenza dichiarata e gli elementi interessati girano di nuovo. Dimentica di dichiararne una e stai misurando l'agent di ieri. E un hit della cache non dice nulla sulla deriva del provider — il modello dietro l'API può cambiare mentre la tua cache no — quindi abbina `--cache` a un'esecuzione periodica con `--fresh`.

### In CI

```yaml
- name: Run evaluations
  run: |
    vendor/bin/neuron evaluation --path=evaluators || true
    php -r '$r = json_decode(file_get_contents("evaluation-results.json"), true, 512, JSON_THROW_ON_ERROR); exit($r["success_rate"] >= 0.95 ? 0 : 1);'
  env:
    ANTHROPIC_KEY: ${{ secrets.ANTHROPIC_KEY }}
```

Tre consigli pratici:

**Non far dipendere ogni PR dalla suite completa.** Costa denaro ed è lenta. Un piccolo insieme di fumo sulle PR e la suite completa di notte.

**Non far fallire la build per un singolo elemento.** Imposta una soglia sul tasso di successo. Su un sistema probabilistico un tasso di superamento del 95 % è una build sana, non una rotta — e trattare un singolo elemento instabile come fallimento insegna al team a ignorare il segnale. Il runner stesso esce con uno stato diverso da zero per qualunque elemento fallito, quindi il comando nudo è un cancello tutto-o-niente e la soglia spetta a te implementarla. Il passo qui sopra ignora il codice di uscita e legge `success_rate`, una frazione fra 0 e 1, dal report JSON che scrive `evaluation.php`. Se l'esecuzione va in crash prima di scrivere il report, il secondo comando fallisce e con lui la build.

**Tieni le chiavi API fuori dai fork.** Le esecuzioni di eval costano denaro vero; un repository pubblico con eval-su-PR è un modo di donare il tuo budget a degli sconosciuti.

### Punti chiave

- `neuron evaluation <dir>` oppure `--path=<dir>`: funzionano entrambi; `--help` elenca ciò che ha la tua versione.
- Più driver di output girano insieme; un driver su database trasforma le eval in una tendenza.
- `--cache` riusa gli output di `run()` e rivaluta sempre; dichiara `cacheDependencies()`.
- `--concurrency` richiede `spatie/fork` e `pcntl`, e degrada con eleganza senza di essi.
- In CI: insieme di fumo sulle PR, suite completa di notte, soglia invece di tutto-o-niente.

## Laboratorio 7 — Una suite di test deterministica

**Copre:** tutto questo capitolo, più l'argomento della testabilità della Sezione 5.3.

### Obiettivo

Una suite PHPUnit su un agent che non fa **alcuna chiamata di rete**. Gira in CI, gira offline, gira in millisecondi, e fallisce per motivi reali invece che per instabilità.

È il complemento delle eval, non un sostituto. Le eval misurano la qualità contro un modello reale. Questa suite dimostra che il tuo cablaggio è corretto senza averne uno.

### Che cosa testare senza un modello

Lavora dall'interno deterministico verso l'esterno:

1. **Classi tool, invocate direttamente.** `(new WeatherTool($client))(45.07, 7.69)` — niente agent, niente provider, e `$client` un client stub di `HttpClientInterface`, come nella Sezione 5.3. È qui che vive la maggior parte della tua logica ed è tutta normale PHP.
2. **DTO di output e regole di validazione.** Passa un array scritto a mano attraverso la tua validazione e asserisci quali violazioni compaiono. Una regola personalizzata della Sezione 6.5 merita un test proprio.
3. **Controlli fra campi.** Il controllo aritmetico della fattura del Laboratorio 6 è PHP puro. Testalo con una `Invoice` volutamente incoerente.
4. **Visibilità dei tool.** Costruisci l'agent con un utente amministratore e con uno non amministratore e asserisci sull'elenco dei tool risultante. È un test di controllo accessi, e appartiene alla tua suite per lo stesso motivo per cui vi appartengono i test dei middleware delle rotte.
5. **Handler degli errori.** `resolveToolErrorHandler()` è un hook protected che restituisce l'handler, quindi raggiungilo con una piccola sottoclasse di test, chiama l'handler con una `Throwable` qualunque e una `ToolCall`, e asserisci che ciò che restituisce contenga l'istruzione sul riprovare. La Sezione 5.11 sosteneva che l'istruzione è portante; questo è il modo per impedire che qualcuno la cancelli.

### Il provider fake

NeuronAI include dei fake in `NeuronAI\Testing` proprio perché la CI possa essere deterministica e gratuita. Usa `FakeAIProvider` per scrivere il copione del lato modello della conversazione — una chiamata a tool preconfezionata seguita da un messaggio finale preconfezionato — e asserisci che i tuoi tool siano stati invocati con gli argomenti che ti aspetti:

```php
use NeuronAI\Agent\Agent;
use NeuronAI\Chat\Messages\AssistantMessage;
use NeuronAI\Chat\Messages\ToolCallMessage;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Testing\FakeAIProvider;
use NeuronAI\Tools\ToolCall;

$provider = new FakeAIProvider(
    new ToolCallMessage(null, [
        ToolCall::make('get_current_weather', 'call_1', ['latitude' => 45.07, 'longitude' => 7.69]),
    ]),
    new AssistantMessage('It is 14 degrees in Turin.'),
);

$calls = new ArrayObject();

$state = Agent::make()
    ->setThreadId('demo')
    ->setAiProvider($provider)
    ->addTool(new RecordingWeatherTool($calls))
    ->chat(new UserMessage('What is the weather in Turin?'));

$provider->assertCallCount(2);
$provider->assertToolsConfigured(['get_current_weather']);
```

`setThreadId()` c'è perché un agent non ha un ID di thread finché non glielo associ. `RecordingWeatherTool` è il tool meteo con la chiamata HTTP sostituita da una riga che accoda i suoi argomenti a `$calls`. La registrazione finisce in un oggetto iniettato di proposito: l'agent esegue un clone nuovo del tool registrato per ogni chiamata, quindi tutto ciò che il tool scrive nelle proprie proprietà sparisce insieme al clone.

Il punto è l'inversione: invece di chiedere "il modello si è comportato correttamente?", chiedi "dato che il modello si è comportato così, il *mio* codice ha fatto la cosa giusta?". La seconda domanda ha una risposta esatta.

I fake sono rigorosi quanto le parti che sostituiscono. `FakeVectorStore` rifiuta un documento senza embedding, esattamente come fa uno store reale, e una coda di risposte esaurita lancia l'eccezione del provider stesso invece di far fallire il test dall'interno dell'agent, dove un handler degli errori dei tool potrebbe inghiottirla.

### Requisiti

- Zero chiamate di rete. Imponilo: se la tua suite passa con la macchina offline, hai vinto. Se no, trova la chiamata.
- Ogni test deterministico. Esegui la suite cinquanta volte in un ciclo; un singolo fallimento significa che è entrato qualcosa di non deterministico.
- Abbastanza veloce da girare a ogni salvataggio.

### Criteri di accettazione

- `phpunit` passa senza `.env`, senza chiavi API e senza internet.
- Cancellare l'istruzione sul riprovare dal tuo handler degli errori fa fallire un test.
- Rimuovere una condizione `visible()` fa fallire un test.
- La suite gira in meno di due secondi.

### Poi, e separatamente

Collega la suite di eval delle Sezioni 10.4–10.6 a un job **notturno**, non allo stesso. Tieni le due cose chiaramente separate nella tua testa e nella tua configurazione di CI:

| | Suite di test | Suite di eval |
|---|---|---|
| Chiede | Il mio codice è corretto? | L'output è buono? |
| Serve un modello | No | Sì |
| Deterministica | Sì | No |
| Costo | Gratis | Denaro vero |
| Gira | A ogni commit | Di notte |
| Fallisce su | Qualunque fallimento | Tasso di successo sotto soglia |

Confonderle è il modo in cui i team finiscono con una pipeline di CI costosa, lenta e instabile, e poi imparano a ignorarla.

## Esercizi del capitolo

1. **Traccia una rottura.** Sottoscrivi Inspector — oppure un `LogListener` — a un agent del Capitolo 5, rompi la descrizione di un tool e leggi il trace. Annota quale delle quattro domande della Sezione 10.3 ha rivelato il problema.
2. **Costruisci un evaluator** con cinque input reali e almeno un'asserzione `StringSimilarity`.
3. **Aggiungi un'asserzione `FaithfulnessJudge`.** Conterà nel Capitolo 11, e averla già a posto significa poter misurare il tuo sistema RAG dal primo giorno invece di aggiungere la misura in seguito.
4. **Scrivi un driver di output personalizzato** che appende a un CSV, ed esegui la suite tre volte per produrre una tendenza.
5. **Cronometra la suite** in sequenza e con `--concurrency=5`. Se il guadagno è minore del previsto, controlla se stai incontrando dei rate limit.

::: {.callout .callout-tip}
[Fine della Parte II]{.callout-title}

Ora hai un agent che usa tool, ricorda le conversazioni, restituisce dati tipizzati, fa streaming, legge documenti, si collega a server di tool esterni e può essere tracciato e misurato. È un sistema completo, e tutto ciò che c'è nelle Parti da III a V è costruito sopra di esso, non accanto.

Quasi la metà dei centotré punti dell'Appendice A sta nel materiale che hai appena attraversato. Se non hai ancora eseguito gli script di verifica, questo è il momento naturale: la parte successiva costruisce su tutto quanto.
:::
