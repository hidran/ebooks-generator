# Capitolo 10 — Observability, eval e testing

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

## 10.2 Configurare Inspector

### Installazione

```bash
composer require inspector-apm/inspector-php
```

Serve solo se non stai già usando un'altra libreria Inspector — `inspector-laravel`, `inspector-symfony` e simili la includono già.

### La variabile d'ambiente

```dotenv
INSPECTOR_INGESTION_KEY=nwse877auxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Crea una chiave registrando un'applicazione su `app.inspector.dev`.

### Registrare l'observer

```php
use Inspector\Neuron\InspectorObserver;

class MyAgent extends Agent
{
    public function __construct()
    {
        parent::__construct();

        $this->observe(InspectorObserver::instance());
    }

    // ...
}
```

`observe()` funziona su **Agent, RAG e Workflow** — che è ancora la Sezione 2.3: sono tutti workflow, quindi accettano tutti degli observer.

### Strumentazione automatica

Se la tua applicazione legge già i file d'ambiente, è probabile che NeuronAI si strumenti da sé non appena `INSPECTOR_INGESTION_KEY` è presente. Registrare l'observer esplicitamente serve quando non hai accesso alle variabili d'ambiente, o vuoi personalizzare la configurazione:

```php
$this->observe(
    InspectorObserver::instance('INSPECTOR_INGESTION_KEY')
);
```

### L'impostazione che ti morderà: autoFlush

È il paragrafo operativamente più importante del capitolo.

Se il tuo agent gira in un processo a lunga esecuzione — un queue worker, Swoole, RoadRunner — devi abilitare esplicitamente l'auto-flush:

```php
$this->observe(
    InspectorObserver::instance(
        key: 'INSPECTOR_INGESTION_KEY',
        autoFlush: true
    )
);
```

Senza, gli eventi si accumulano in memoria e vengono scaricati alla fine della richiesta. Un processo worker che gira per ore non ha una "fine della richiesta". I tuoi trace non arrivano mai, la memoria cresce, e concludi che l'integrazione è rotta quando è semplicemente mal configurata.

Dato che la Sezione 1.4 spinge il lavoro lungo degli agent sulle code e la Sezione 5.13 richiede CLI per i tool paralleli, **la maggior parte dei deploy seri di NeuronAI è esattamente il caso che ha bisogno di `autoFlush`.**

### Pacchetti specifici per framework

Se stai integrando in Laravel o Symfony, aggiungi il pacchetto del framework (`inspector-laravel`, `inspector-symfony`) per una raccolta dati migliore. Non è obbligatorio, ma è consigliato: correla il trace dell'agent con la richiesta HTTP, le query e il job in coda attorno, che è ciò che vuoi davvero quando diagnostichi un incidente in produzione.

Il Capitolo 23 lo tratta nel contesto Laravel.

::: {.callout .callout-warning}
[Deriva dei namespace]{.callout-title}

Nell'ecosistema compaiono tre nomi diversi per questo componente:

- `Inspector\Neuron\InspectorObserver` (documentazione Inspector attuale)
- `NeuronAI\Observability\InspectorObserver` (materiale lato NeuronAI)
- `NeuronAI\Observability\AgentMonitoring` (articoli più vecchi, e ancora in alcuni esempi di structured output)

Conferma quale esiste nella tua versione installata. È il posto più probabile in cui copiare un'istruzione `use` che non si risolve. Appendice A, punto 16.
:::

### Punti chiave

- `composer require inspector-apm/inspector-php`, imposta la chiave, chiama `observe()`.
- Funziona su Agent, RAG e Workflow.
- `autoFlush: true` per i queue worker e i runtime a lunga esecuzione: non è opzionale.
- Tre nomi storici per la classe observer; verifica il tuo.

## 10.3 Leggere un trace

### Che cosa mostra un trace

Ogni passo di inferenza, ogni chiamata a tool, ogni retrieval — con argomenti, risultati, conteggi di token e tempi.

Esegui l'agent meteo del Laboratorio 3 con Inspector abilitato e ottieni una linea temporale:

```
▸ WeatherAgent                                        4.82s   3,412 tokens
  ├─ ChatNode                          1.31s     892 in / 84 out
  ├─ ToolNode: get_current_weather     0.42s
  │    input:  {"latitude": 45.0703, "longitude": 7.6869}
  │    output: {"temperature_2m": 14.2, ...}
  ├─ ToolNode: get_current_weather     0.38s
  │    input:  {"latitude": 45.4642, "longitude": 9.19}
  ├─ ChatNode                          1.44s   1,203 in / 61 out
  ├─ ToolNode: mean                    0.01s
  └─ ChatNode                          1.26s   1,172 in / 91 out
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
892 → 1.203 → 1.172 token in ingresso. Crescono, perché cresce la conversazione. Esattamente l'accumulo della Sezione 1.4, ora misurato invece che stimato.

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

::: {.callout .callout-warning}
[Discrepanza di namespace nei documenti]{.callout-title}

Il blocco `autoload-dev` della documentazione mappa `App\Evaluators\` su `evaluators/`, ma il comando generatore della stessa pagina crea `App\Neuron\Evaluators\AgentEvaluator`. Le due cose non concordano. Scegli una convenzione e usala in modo coerente. Appendice A, punto 20.
:::

### Generare un evaluator

```bash
# Unix
vendor/bin/neuron make:evaluator App\\Neuron\\Evaluators\\AgentEvaluator

# Windows
.\vendor\bin\neuron make:evaluators App\Neuron\Evaluators\AgentEvaluator
```

Nota la differenza singolare/plurale fra le due schede della documentazione ufficiale — `make:evaluator` contro `make:evaluators`. Uno dei due è un refuso. Appendice A, punto 17.

### La struttura a tre metodi

```php
namespace App\Neuron\Evaluators;

use NeuronAI\Evaluation\Assertions\StringContains;
use NeuronAI\Evaluation\BaseEvaluator;
use NeuronAI\Evaluation\Contracts\DatasetInterface;
use NeuronAI\Evaluation\Dataset\JsonDataset;

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
        $response = MyAgent::make()->chat(
            new UserMessage($datasetItem['input'])
        )->getMessage();

        return $response->getContent();
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
use NeuronAI\RAG\Embeddings\OpenAI\OpenAIEmbeddings;

$this->assert(new StringSimilarity(
    reference: 'The quick brown fox',
    embeddingsProvider: new OpenAIEmbeddings(key: 'YOUR_KEY'),
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
            ->chat(new UserMessage($datasetItem['input']))
            ->getMessage()
            ->getContent();
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

::: {.callout .callout-warning}
[Due cose da verificare qui]{.callout-title}

L'esempio ufficiale di questo blocco scrive male `Anthropic` come `Antrhopic`. E i metodi fluenti `setAiProvider()` / `setInstructions()` compaiono solo in questo esempio: conferma che esistano nella tua versione prima di costruirci sopra. Appendice A, punto 21.
:::

### I quattro giudici specializzati

NeuronAI include giudici per le domande di valutazione ricorrenti:

**`FaithfulnessJudge`** — l'output è fondato sul contesto fornito, o ha allucinato?

```php
$this->assert(new FaithfulnessJudge(
    judge: $this->judge,
    context: $retrievedDocuments,
    threshold: 0.7
), $output);
```

**È l'asserzione più importante in assoluto per i sistemi RAG**, ed è il motivo per cui le eval compaiono prima della Parte III e non dopo. Un sistema RAG che risponde in modo fluente a partire da informazioni che si è inventato è peggio di uno che dice "non lo so". La fedeltà è come lo misuri, e non puoi misurarla con la corrispondenza di stringhe.

**`CorrectnessJudge`** — corrisponde alla risposta attesa?

```php
$this->assert(new CorrectnessJudge(
    judge: $judge,
    expected: $datasetItem['expected_answer'],
    threshold: 0.7
), $output);
```

**`RelevanceJudge`** — affronta davvero la domanda?

**`HelpfulnessJudge`** — è utile e azionabile?

### Due cautele sui giudici

**Anche il giudice è non deterministico.** Stai misurando un sistema probabilistico con uno strumento probabilistico. Le soglie assorbono la cosa, ma non trattare il punteggio di un giudice come verità assoluta. Tracciarlo nel tempo e cerca movimenti, non valori assoluti.

**I giudici costano.** Ogni asserzione giudicata è una chiamata LLM extra. Un dataset da 200 elementi con tre asserzioni giudicate sono 600 chiamate extra per esecuzione. Usa un modello più economico per il giudice rispetto all'agent: una buona applicazione dell'argomento sullo scambio di provider della Sezione 3.6.

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

- Dieci asserzioni integrate; `StringSimilarity` per il significato, `StringDistance` per i caratteri.
- Quattro giudici: fedeltà, correttezza, rilevanza, utilità.
- `FaithfulnessJudge` è quello essenziale per il RAG: tienilo pronto prima della Parte III.
- I giudici sono non deterministici e costano; usa un modello più economico.
- Le asserzioni restituiscono punteggi, non booleani.

## 10.6 Eseguire le eval: output, parallelismo e CI

### Esecuzione

```bash
# Unix
vendor/bin/neuron evaluations --path=evaluators

# Windows
.\vendor\bin\neuron evaluations --path=evaluators
```

::: {.callout .callout-warning}
[Verifica questo comando prima di ogni altra cosa]{.callout-title}

La sezione sull'esecuzione parallela della stessa pagina di documentazione mostra un'invocazione diversa: `vendor/bin/neuron evaluation path/to/evaluators --concurrency=3` — `evaluation` al singolare, e un argomento posizionale invece di `--path=`. Esegui `vendor/bin/neuron list` sulla tua versione installata e usa quello vero. Appendice A, punto 18, e quello con più probabilità di far fallire la tua prima esecuzione di eval.
:::

### Driver di output

Crea `evaluation.php` nella radice del progetto:

```php
<?php

use NeuronAI\Evaluation\OutputDrivers\ConsoleDriver;
use NeuronAI\Evaluation\OutputDrivers\JsonDriver;

return [
    'output' => [
        ConsoleDriver::class => ['verbose' => true],
        JsonDriver::class    => ['path' => 'evaluation-results.json'],
    ],
];
```

Le opzioni vengono passate al costruttore di ciascun driver. Più driver girano simultaneamente: la console per lo sviluppatore, JSON perché la CI lo consumi.

Senza file di configurazione, il sistema usa per default l'output su console. (I documenti chiamano il default `ConsoleOutputDriver` nella prosa ma `ConsoleDriver` nell'esempio di configurazione — Appendice A, punto 19.)

### Output personalizzato: il pattern che rende le eval uno strumento aziendale

```php
namespace App\Neuron\Evaluations;

use NeuronAI\Evaluation\Contracts\EvaluationOutputInterface;
use NeuronAI\Evaluation\Runner\EvaluatorSummary;

class DatabaseOutput implements EvaluationOutputInterface
{
    public function __construct(
        private readonly \PDO $pdo,
        private readonly string $table = 'evaluations'
    ) {}

    public function output(EvaluatorSummary $summary): void
    {
        $stmt = $this->pdo->prepare(
            "INSERT INTO {$this->table} (passed, failed, success_rate, total_time, created_at, updated_at)
             VALUES (?, ?, ?, ?, NOW(), NOW())"
        );

        $stmt->execute([
            $summary->getPassedCount(),
            $summary->getFailedCount(),
            $summary->getSuccessRate(),
            $summary->getTotalExecutionTime(),
        ]);
    }
}
```

Registralo:

```php
return [
    'output' => [
        ConsoleDriver::class => ['verbose' => true],
        DatabaseOutput::class => [
            'pdo'   => new \PDO(/* ... */),
            'table' => 'evaluations',
        ],
    ],
];
```

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

### In CI

```yaml
- name: Run evaluations
  run: vendor/bin/neuron evaluations --path=evaluators
  env:
    ANTHROPIC_KEY: ${{ secrets.ANTHROPIC_KEY }}
```

Tre consigli pratici:

**Non far dipendere ogni PR dalla suite completa.** Costa denaro ed è lenta. Un piccolo insieme di fumo sulle PR e la suite completa di notte.

**Non far fallire la build per un singolo elemento.** Imposta una soglia sul tasso di successo. Su un sistema probabilistico un tasso di superamento del 95 % è una build sana, non una rotta — e trattare un singolo elemento instabile come fallimento insegna al team a ignorare il segnale.

**Tieni le chiavi API fuori dai fork.** Le esecuzioni di eval costano denaro vero; un repository pubblico con eval-su-PR è un modo di donare il tuo budget a degli sconosciuti.

### Punti chiave

- Verifica il comando di eval contro `vendor/bin/neuron list` prima di ogni altra cosa.
- Più driver di output girano insieme; un driver su database trasforma le eval in una tendenza.
- `--concurrency` richiede `spatie/fork` e `pcntl`, e degrada con eleganza senza di essi.
- In CI: insieme di fumo sulle PR, suite completa di notte, soglia invece di tutto-o-niente.

## Laboratorio 7 — Una suite di test deterministica

**Copre:** tutto questo capitolo, più l'argomento della testabilità della Sezione 5.3.

### Obiettivo

Una suite PHPUnit su un agent che non fa **alcuna chiamata di rete**. Gira in CI, gira offline, gira in millisecondi, e fallisce per motivi reali invece che per instabilità.

È il complemento delle eval, non un sostituto. Le eval misurano la qualità contro un modello reale. Questa suite dimostra che il tuo cablaggio è corretto senza averne uno.

### Che cosa testare senza un modello

Lavora dall'interno deterministico verso l'esterno:

1. **Classi tool, invocate direttamente.** `(new WeatherTool())(45.07, 7.69)` — niente agent, niente provider. Mocka il client HTTP. È qui che vive la maggior parte della tua logica ed è tutta normale PHP.
2. **DTO di output e regole di validazione.** Passa un array scritto a mano attraverso la tua validazione e asserisci quali violazioni compaiono. Una regola personalizzata della Sezione 6.5 merita un test proprio.
3. **Controlli fra campi.** Il controllo aritmetico della fattura del Laboratorio 6 è PHP puro. Testalo con una `Invoice` volutamente incoerente.
4. **Visibilità dei tool.** Costruisci l'agent con un utente amministratore e con uno non amministratore e asserisci sull'elenco dei tool risultante. È un test di controllo accessi, e appartiene alla tua suite per lo stesso motivo per cui vi appartengono i test dei middleware delle rotte.
5. **Handler degli errori.** Invoca `resolveToolErrorHandler()` con una `ConnectException` e asserisci che la stringa restituita contenga l'istruzione sul riprovare. La Sezione 5.11 sosteneva che l'istruzione è portante; questo è il modo per impedire che qualcuno la cancelli.

### Il provider fake

NeuronAI include dei fake proprio perché la CI possa essere deterministica e gratuita. Usa un provider fake per scrivere il copione del lato modello della conversazione — una chiamata a tool preconfezionata seguita da un messaggio finale preconfezionato — e asserisci che i tuoi tool siano stati invocati con gli argomenti che ti aspetti.

Il punto è l'inversione: invece di chiedere "il modello si è comportato correttamente?", chiedi "dato che il modello si è comportato così, il *mio* codice ha fatto la cosa giusta?". La seconda domanda ha una risposta esatta.

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

1. **Traccia una rottura.** Abilita Inspector su un agent del Capitolo 5, rompi la descrizione di un tool e leggi il trace. Annota quale delle quattro domande della Sezione 10.3 ha rivelato il problema.
2. **Costruisci un evaluator** con cinque input reali e almeno un'asserzione `StringSimilarity`.
3. **Aggiungi un'asserzione `FaithfulnessJudge`.** Conterà nel Capitolo 11, e averla già a posto significa poter misurare il tuo sistema RAG dal primo giorno invece di aggiungere la misura in seguito.
4. **Scrivi un driver di output personalizzato** che appende a un CSV, ed esegui la suite tre volte per produrre una tendenza.
5. **Cronometra la suite** in sequenza e con `--concurrency=5`. Se il guadagno è minore del previsto, controlla se stai incontrando dei rate limit.

::: {.callout .callout-tip}
[Fine della Parte II]{.callout-title}

Ora hai un agent che usa tool, ricorda le conversazioni, restituisce dati tipizzati, fa streaming, legge documenti, si collega a server di tool esterni e può essere tracciato e misurato. È un sistema completo, e tutto ciò che c'è nelle Parti da III a V è costruito sopra di esso, non accanto.

Ventuno dei quarantaquattro punti dell'Appendice A stanno nel materiale che hai appena attraversato. Se non hai ancora eseguito gli script di verifica, questo è il momento naturale: la parte successiva costruisce su tutto quanto.
:::
