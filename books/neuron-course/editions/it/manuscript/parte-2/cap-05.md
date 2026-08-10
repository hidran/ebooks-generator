# Capitolo 5 — Tool: dare le mani all'agent

È il capitolo più lungo del libro, e il più importante. I tool sono l'unica funzionalità che separa un agent da un chatbot, e la progettazione dei tool è dove gli agent falliscono davvero.

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

La versione eseguibile di ogni listato che segue si trova in [`chapters/Ch05`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch05), nel repository di accompagnamento. Clonalo, esegui `composer install` e gli esempi funzionano su un Ollama locale senza alcuna API key.
:::

## 5.1 Che cos'è davvero un tool

### La definizione in una frase

Un tool è una funzione della tua base di codice che il modello può chiederti di eseguire.

Rileggila, perché ogni parola è portante. È la **tua** funzione. Nella **tua** base di codice. Il modello **chiede**. Sei **tu** a eseguirla.

### Il meccanismo, ripetuto

La Sezione 1.2 ha introdotto il ciclo. Ecco che cosa vi aggiunge un tool.

Descrivi le tue funzioni al modello come metadati strutturati: un nome, una descrizione e uno schema di parametri. Il modello li riceve insieme alla conversazione. Quando decide che una funzione sarebbe utile, non produce prosa: produce una richiesta strutturata.

```
Vorrei chiamare get_transcription con {"video_url": "https://..."}
```

NeuronAI intercetta quella richiesta, trova l'oggetto tool corrispondente, lo invoca con quegli argomenti, prende il valore restituito, lo appende alla conversazione come messaggio di risultato del tool e richiama il modello. Ora il modello ha la trascrizione in contesto e può scrivere il riassunto.

Il framework automatizza ogni parte di tutto ciò tranne il corpo della funzione. È genuinamente tutta l'astrazione, e la documentazione di NeuronAI la descrive esattamente così: il ciclo centrale è chiamare un modello, lasciargli scegliere i tool da eseguire e concludere quando non servono altri tool.

### Perché questo è il modello di sicurezza, non solo di esecuzione

Il modello non ha capacità proprie. Non può aprire un socket, leggere un file o eseguire una query. Tutto il suo potere è l'insieme dei tool che hai registrato.

Questo ha una conseguenza liberatoria e un obbligo.

**La conseguenza liberatoria:** non puoi essere sfruttato per compiere un'azione che non hai mai implementato. Non esiste un tool per `DELETE FROM users`, quindi nessun prompt — per quanto ingegnoso — ne produce uno.

**L'obbligo:** tutto ciò che *invece* registri è raggiungibile da chiunque possa parlare con l'agent. Se registri un tool che esegue SQL arbitrario, un utente che convince il modello a eseguire SQL distruttivo ha vinto, e nessuna quantità di testo istruttivo nel system prompt lo impedisce in modo affidabile.

Il confine di sicurezza è l'elenco dei tool, ed è l'unico di cui puoi fidarti. La Sezione 5.10 e il Capitolo 19 ci costruiscono sopra.

### Che cosa rende buono un tool

**Stretto.** `get_order_status(order_id)` batte `manage_order(action, params)`. Un tool stretto è più facile da scegliere correttamente per il modello e più facile da autorizzare per te.

**Deterministico.** Stessi argomenti, stesso risultato. Il modello è già non deterministico; non aggravare la cosa.

**Compatto nel valore restituito.** Qualunque cosa restituisci viene convertita in stringa dentro la conversazione e rimandata a ogni iterazione successiva. Restituisci i tre campi che servono al modello, non l'intero oggetto con cinquanta colonne. È l'aritmetica della Sezione 1.4 che ricompare nel codice.

**Onesto nel fallimento.** Restituire "Ordine non trovato" è utile al modello. Restituire una stringa vuota lo lascia a indovinare, e un modello che indovina allucina.

### Il cambio di mentalità

Smetti di pensare ai tool come a una funzionalità di integrazione. Sono la **superficie di capacità del tuo agent** — un problema di progettazione di API, dove il consumatore è un modello linguistico invece di un altro sviluppatore.

Questa inquadratura spiega perché il resto del capitolo dedica tanto tempo a nomi, descrizioni e schemi. Stai scrivendo documentazione per un consumatore che legge solo la documentazione.

### Punti chiave

- Un tool è la tua funzione; il modello richiede, il tuo codice esegue.
- L'elenco dei tool registrati è il confine di sicurezza, l'unico su cui puoi contare.
- I buoni tool sono stretti, deterministici, compatti nell'output ed espliciti sul fallimento.
- Progettare tool è progettare API per un lettore che ha solo la documentazione.

## 5.2 Tool inline

### La forma

```php
Tool::make('name', 'description')
    ->addProperty(new ToolProperty(...))
    ->setCallable(fn (...) => ...);
```

Tre pezzi: identità, schema, implementazione.

### L'esempio canonico

È la forma della documentazione ufficiale, e vale la pena conoscerla alla lettera perché la incontrerai ovunque:

```php
namespace App\Neuron;

use NeuronAI\Agent\Agent;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Providers\Anthropic\Anthropic;
use NeuronAI\Tools\PropertyType;
use NeuronAI\Tools\Tool;
use NeuronAI\Tools\ToolProperty;

class YouTubeAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return new Anthropic(
            key: 'ANTHROPIC_API_KEY',
            model: 'ANTHROPIC_MODEL',
        );
    }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: ['You are an AI Agent specialized in writing YouTube video summaries.'],
            steps: [
                'Get the url of a YouTube video, or ask the user to provide one.',
                'Use the tools you have available to retrieve the transcription of the video.',
                'Write the summary.',
            ],
            output: [
                'Write a summary in a paragraph without using lists. Use just fluent text.',
                'After the summary add a list of three sentences as the three most important take away from the video.',
            ],
        );
    }

    protected function tools(): array
    {
        return [
            Tool::make(
                'get_transcription',
                'Retrieve the transcription of a youtube video.',
            )->addProperty(
                new ToolProperty(
                    name: 'video_url',
                    type: PropertyType::STRING,
                    description: 'The URL of the YouTube video.',
                    required: true,
                )
            )->setCallable(function (string $video_url) {
                return 'Video transcription...';
            }),
        ];
    }
}
```

### La regola su cui inciampano tutti

**Il nome della proprietà deve corrispondere al nome del parametro del callable.**

La proprietà si chiama `video_url`. La firma della closure è `function (string $video_url)`. Non `$url`, non `$videoUrl`. Esattamente `$video_url`.

NeuronAI mappa per nome gli argomenti JSON del modello sul callable. Rinomina un lato e ottieni un fallimento confuso che sembra un errore del modello mentre in realtà è il tuo cablaggio. È il bug sui tool più comune in assoluto.

### Una versione eseguibile

Qualcosa che puoi davvero eseguire, senza alcuna chiave API esterna:

**`examples/02-inline-tool.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\ToolDemoAgent;
use NeuronAI\Chat\Messages\UserMessage;

$question = $argv[1] ?? 'Is the server under stress right now?';

echo ToolDemoAgent::make()
    ->chat(new UserMessage($question))
    ->getMessage()
    ->getContent() . PHP_EOL;
```

**`src/Agents/ToolDemoAgent.php`**

```php
<?php

declare(strict_types=1);

namespace App\Agents;

use App\ProviderFactory;
use NeuronAI\Agent\Agent;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Tools\PropertyType;
use NeuronAI\Tools\Tool;
use NeuronAI\Tools\ToolProperty;

class ToolDemoAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return ProviderFactory::make();
    }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: ['You are a system monitoring assistant.'],
            steps: ['Always read the real load values with your tools before answering.'],
            output: ['Answer in two sentences. Give the numbers you measured.'],
        );
    }

    protected function tools(): array
    {
        return [
            Tool::make(
                'get_server_load',
                'Returns the average CPU load of this server over a given time window. '
                . 'Use this whenever asked about current server load, stress, or performance.'
            )->addProperty(
                new ToolProperty(
                    name: 'window',
                    type: PropertyType::STRING,
                    description: 'The time window. Allowed values: "1m", "5m", "15m".',
                    required: true,
                )
            )->setCallable(function (string $window): string {
                $load = \sys_getloadavg();

                $value = match ($window) {
                    '1m'  => $load[0],
                    '5m'  => $load[1],
                    '15m' => $load[2],
                    default => throw new \InvalidArgumentException("Invalid window: {$window}"),
                };

                return \sprintf('Load average over %s: %.2f', $window, $value);
            }),
        ];
    }
}
```

```bash
php examples/02-inline-tool.php "How stressed is the server compared to fifteen minutes ago?"
```

Quella domanda forza due chiamate allo stesso tool con argomenti diversi — un primo esperimento migliore di una domanda a chiamata singola, perché vedi il ciclo iterare.

### Quando inline è la scelta giusta

**Usalo per:** prototipi, script una tantum, tool che davvero non hanno riuso, dimostrazioni didattiche.

**Non usarlo per:** qualunque cosa richieda una dipendenza, qualunque cosa testerai, qualunque cosa compaia in più di un agent, qualunque cosa più lunga di una decina di righe.

La closure non può essere iniettata, non può essere mockata, non può essere testata in isolamento e non può essere riusata. La Sezione 5.3 risolve tutti e quattro i problemi.

### Punti chiave

- `Tool::make()->addProperty()->setCallable()`.
- Il nome della proprietà deve corrispondere esattamente al nome del parametro del callable.
- I tool inline sono per i prototipi: non sono iniettabili, testabili o riusabili.

## 5.3 Tool come classi

Questa è la forma che metterai davvero in produzione.

### Genera l'impalcatura

```bash
# Unix
vendor/bin/neuron make:tool App\\Neuron\\Tools\\GetTranscriptionTool

# Windows PowerShell
.\vendor\bin\neuron make:tool App\Neuron\Tools\GetTranscriptionTool
```

### Le quattro parti di una classe tool

```php
<?php

namespace App\Neuron\Tools;

use GuzzleHttp\Client;
use NeuronAI\Tools\PropertyType;
use NeuronAI\Tools\Tool;
use NeuronAI\Tools\ToolProperty;

class GetTranscriptionTool extends Tool
{
    protected Client $client;

    public function __construct(protected string $key)
    {
        parent::__construct(
            'get_transcription',
            'Retrieve the transcription of a youtube video.',
        );
    }

    protected function properties(): array
    {
        return [
            new ToolProperty(
                name: 'video_url',
                type: PropertyType::STRING,
                description: 'The URL of the YouTube video.',
                required: true,
            ),
        ];
    }

    public function __invoke(string $video_url): string
    {
        $response = $this->getClient()
            ->get('transcript?url=' . $video_url . '&text=true')
            ->getBody()
            ->getContents();

        $response = json_decode($response, true);

        return $response['content'];
    }

    protected function getClient(): Client
    {
        return $this->client ??= new Client([
            'base_uri' => 'https://api.supadata.ai/v1/youtube/',
            'headers'  => ['x-api-key' => $this->key],
        ]);
    }
}
```

**1. Il costruttore** — dichiara l'identità chiamando `parent::__construct(name, description)` e prende le dipendenze di cui il tool ha bisogno. Qui è una chiave API; in un'applicazione reale potrebbe essere un repository, una connessione PDO, un mailer.

**2. `properties()`** — lo schema, gli stessi oggetti della versione inline.

**3. `__invoke()`** — l'implementazione. Il metodo magico di PHP, così l'oggetto tool è invocabile. I nomi dei parametri devono corrispondere ai nomi delle proprietà, esattamente come nella Sezione 5.2.

**4. Helper** — tutto il resto di cui la classe ha bisogno, tenuto privato al tool. Il client lazy con `??=` qui è un'abitudine piccola ma buona: nessun client HTTP viene costruito se il modello non chiama davvero il tool.

### Collegarlo

```php
protected function tools(): array
{
    return [
        GetTranscriptionTool::make('API_KEY'),
    ];
}
```

`::make()` inoltra i suoi argomenti al costruttore. Così un tool con dipendenze si legge comunque in modo pulito nell'elenco dei tool dell'agent.

### Perché questo pattern si guadagna la cerimonia in più

**Prende dipendenze.** La closure inline poteva solo catturare variabili dallo scope. Una classe riceve una connessione PDO, un repository, un mailer — dal costruttore, dal tuo container di DI.

**È testabile con test unitari senza un LLM.** È l'argomento che conta di più:

```php
public function test_it_returns_the_transcript(): void
{
    $tool = new GetTranscriptionTool('fake-key');

    $result = $tool('https://youtube.com/watch?v=xyz');

    $this->assertStringContainsString('expected phrase', $result);
}
```

Il tool è un oggetto invocabile. Lo invochi direttamente, senza agent, senza provider, senza chiamate di rete a un modello. Visto il problema del non determinismo della Sezione 1.5, avere gran parte del tuo sistema agentico fatta di normale PHP testabile è una vittoria significativa — e il confine fra "testabile" e "non testabile" corre esattamente lungo questa classe.

**È riusabile e distribuibile.** I tool implementano `ToolInterface`. Un tool ben costruito può essere pubblicato come pacchetto Composer o contribuito a monte al framework.

**Ha un nome vero.** `GetTranscriptionTool` compare negli stack trace, nel tuo container di DI, nella navigazione del tuo IDE. Una closure compare come `{closure}`.

::: {.callout .callout-tip}
[In pratica]{.callout-title}

Prendi il tool inline `get_server_load` della Sezione 5.2 e convertilo in una classe, poi scrivi un test PHPUnit. Ci vogliono cinque minuti, e rende l'argomento della testabilità molto più efficace di quanto faccia leggerlo.
:::

### Punti chiave

- Costruttore per identità e dipendenze, `properties()` per lo schema, `__invoke()` per la logica.
- `::make()` inoltra gli argomenti del costruttore.
- I tool come classi sono iniettabili, testabili senza LLM, riusabili e distribuibili.
- La classe tool è il confine fra PHP deterministico e AI non deterministica: metti quanta più logica possibile dal lato deterministico.

## 5.4 Le descrizioni dei tool sono prompt engineering

### L'affermazione

Quando un agent si comporta male, la causa di solito non è il modello, né il framework, né il system prompt. È che la descrizione di un tool non ha detto al modello con sufficiente chiarezza quando usarlo.

La documentazione ufficiale è insolitamente diretta su questo: il nome e la descrizione del tool e delle sue proprietà vengono passati all'LLM in linguaggio naturale, e più sei esplicito e chiaro, più è probabile che l'LLM capisca quando, se e perché usare il tool.

### Che cosa vede il modello

Non il tuo codice. Non i tuoi tipi. Non il nome della tua classe. Questo, grosso modo:

```json
{
  "name": "get_transcription",
  "description": "Retrieve the transcription of a youtube video.",
  "parameters": {
    "video_url": {
      "type": "string",
      "description": "The URL of the YouTube video.",
      "required": true
    }
  }
}
```

Questa è l'intera interfaccia. Ogni decisione di selezione che il modello prende si basa su quelle stringhe.

### La formula in quattro parti

**1. Che cosa fa.** Una proposizione. Verbo concreto.

**2. Quando usarlo.** La parte più preziosa e più spesso omessa. Dai le condizioni di attivazione nella lingua dell'utente, non nella tua.

**3. Che cosa restituisce.** Fissa le aspettative, così il modello può pianificare una sequenza multi-passo.

**4. Che cosa non fare.** Il guardrail. Soprattutto "non inventare questi dati".

**Scarsa:**

```php
'get_weather',
'Gets the weather.'
```

**Buona:**

```php
'get_current_weather',
'Returns current weather conditions for a location: temperature in Celsius, '
. 'wind speed, and a condition code. Use this whenever the user asks about '
. 'current weather, temperature, or conditions anywhere. Requires latitude '
. 'and longitude — derive them yourself from the place name. Never invent '
. 'weather data; always call this tool.'
```

Più lunga, e vale ogni token. Risponde a tutte e quattro le domande.

### Le descrizioni delle proprietà contano quanto le altre

La descrizione del parametro è dove previeni chiamate malformate:

```php
new ToolProperty(
    name: 'latitude',
    type: PropertyType::NUMBER,
    description: 'Latitude in decimal degrees. Example: 45.0703 for Turin, Italy. '
               . 'Negative for southern hemisphere.',
    required: true,
)
```

L'esempio svolto sta facendo lavoro vero. I modelli riconoscono schemi sugli esempi in modo molto più affidabile che su descrizioni astratte dei tipi, e un esempio in una descrizione di proprietà elimina un'intera classe di errori di formato.

### Convenzioni sui nomi

- `snake_case`, verbo per primo: `get_order_status`, `send_notification`, `search_documents`
- Specifico invece che generico: `search_orders_by_customer` batte `search`
- Prefissi coerenti in tutto il catalogo: `get_`, `list_`, `create_`, `send_`
- Mai gergo interno. `fetch_sku_metadata_v2` non significa nulla per il modello — e i suffissi di versione interni lo confondono attivamente.

### L'esperimento che cambia il modo in cui scrivi i tool

Costruisci lo stesso agent meteo due volte. Versione A: `'get_weather'` / `'Gets the weather.'`. Versione B: la descrizione in quattro parti qui sopra.

Chiedi a entrambe: *"Devo portare una giacca a Torino questo pomeriggio?"*

La versione A risponde spesso dalla conoscenza generale del modello senza chiamare affatto il tool, perché nulla nella descrizione collegava "devo portare una giacca" a "prendi il meteo". La versione B chiama il tool, perché la descrizione elencava esplicitamente le condizioni di attivazione.

Stesso codice, stesso modello, una stringa cambiata, comportamento corretto. **La descrizione è il programma.**

### Consigli pratici

- Scrivi la descrizione prima dell'implementazione. Se non riesci a descrivere quando andrebbe usato, l'ambito del tool è sbagliato.
- Tratta le descrizioni come codice versionato e revisionale.
- Quando un agent sceglie il tool sbagliato, leggi le due descrizioni una accanto all'altra. L'ambiguità è quasi sempre visibile.
- Rendi esplicito il confine fra due tool simili. Se hai `search_orders` e `search_products`, di' in ciascuna descrizione a che cosa serve l'*altro*.

### Punti chiave

- Nome, descrizione e descrizioni delle proprietà sono l'intera interfaccia del modello.
- Quattro parti: cosa, quando, cosa restituisce, cosa non fare.
- Gli esempi dentro le descrizioni delle proprietà prevengono errori di formato.
- Tool sbagliato selezionato → leggi le descrizioni, non il codice.

## 5.5 Tipi di proprietà: scalari, array e oggetti

### ToolProperty — scalari

```php
use NeuronAI\Tools\PropertyType;
use NeuronAI\Tools\Tool;
use NeuronAI\Tools\ToolProperty;

protected function properties(): array
{
    return [
        new ToolProperty(
            name: 'arg',
            type: PropertyType::STRING,
            description: 'Describe the value you expect',
            required: true,
        ),
    ];
}
```

`PropertyType` copre i tipi scalari — stringa, numero, booleano e così via. Controlla l'enum nella versione che hai installato per i casi esatti.

Due argomenti da distinguere:

- **`required`** — il modello deve fornire affatto questa proprietà?
- **`nullable`** — il valore fornito può essere null?

Non sono la stessa cosa, e confonderli produce schemi che ammettono input che non intendevi. Una proprietà obbligatoria ma nullable deve essere presente e può essere null; una proprietà opzionale può essere del tutto assente.

### ArrayProperty — elenchi

Usa `items` per dichiarare il tipo degli elementi:

```php
use NeuronAI\Tools\ArrayProperty;

new ArrayProperty(
    name: 'prop_array',
    description: 'Describe the value you expect',
    required: true,
    items: new ToolProperty(
        name: 'prop',
        type: PropertyType::STRING,
        description: 'Describe the value you expect',
        required: true,
    ),
)
```

E vincola la dimensione con `minItems` / `maxItems`:

```php
$property = new ArrayProperty(
    name: 'tags',
    description: 'List of tags associated with the item',
    required: true,
    items: new ToolProperty(
        name: 'tag',
        type: PropertyType::STRING,
        description: 'A single tag',
        required: true,
    ),
    minItems: 1,
    maxItems: 10,
);
```

**Perché i limiti contano sul piano operativo.** Senza `maxItems`, a un modello a cui chiedi di "etichettare a fondo questo articolo" può restituire sessanta tag. Ognuno è token nella conversazione, e se poi il tuo tool fa una chiamata API per tag, sono sessanta chiamate. `maxItems: 10` è un controllo di costo e una protezione dai rate limit, non una semplice regola di validazione.

### ObjectProperty — strutture annidate

```php
use NeuronAI\Tools\ObjectProperty;

new ObjectProperty(
    name: 'colors',
    description: 'RGB color',
    required: true,
    properties: [
        new ToolProperty(
            name: 'r',
            type: PropertyType::NUMBER,
            description: 'The red part of the RGB',
            required: true,
        ),
        new ToolProperty(
            name: 'g',
            type: PropertyType::NUMBER,
            description: 'The green part of the RGB',
            required: true,
        ),
        new ToolProperty(
            name: 'b',
            type: PropertyType::NUMBER,
            description: 'The blue part of the RGB',
            required: true,
        ),
    ],
)
```

Le proprietà si annidano arbitrariamente: un array di oggetti, un oggetto che contiene array e così via.

### L'indicazione di progetto che conta più della sintassi

*Puoi* esprimere strutture profondamente annidate. Per lo più *non dovresti*.

Ogni livello di annidamento è un'altra occasione per il modello di produrre una forma che non valida, e gli schemi complessi consumano token a ogni singola richiesta del ciclo — ricorda dalla Sezione 1.3 che lo schema completo dei tool viene ritrasmesso a ogni iterazione.

Tre regole:

**Preferisci il piatto.** Due proprietà scalari battono un oggetto con due campi, a meno che l'oggetto non sia davvero riusato fra più tool.

**Preferisci più tool stretti a un tool largo con un'unione discriminata.** Un tool che prende `{action: "create"|"update"|"delete", payload: {...}}` è più difficile da chiamare correttamente per il modello di tre tool separati. È anche impossibile da autorizzare in modo granulare: non puoi permettere a un utente di cancellare ma non di creare se entrambe le azioni stanno dietro un solo tool.

**Lascia al modello il lavoro di conversione.** Invece di accettare una data in testo libero e farne il parsing tu, dichiara la proprietà come stringa ISO 8601 con un esempio nella descrizione. I modelli sono bravi nella conversione di formato, e ottieni una forma validata al confine invece di un problema di parsing dentro il tuo tool.

### Esercizio

Scrivi un tool `compare_cities` che prende un `ArrayProperty` di nomi di città con `minItems: 2, maxItems: 5` e restituisce un confronto. Poi chiedi all'agent di confrontare otto città. Osserva come il vincolo viene applicato e come reagisce il modello all'essere vincolato.

### Punti chiave

- Tre classi: `ToolProperty`, `ArrayProperty`, `ObjectProperty`.
- `required` e `nullable` sono domande diverse.
- `minItems` / `maxItems` sono controlli di costo e di rate limit, non solo validazione.
- Preferisci schemi piatti e più tool stretti a un unico tool largo.

## 5.6 Input strutturato per i tool

### Il problema

L'esempio RGB della Sezione 5.5 richiedeva tre `ToolProperty` annidate per tre campi. Un oggetto realistico — un indirizzo, una riga d'ordine, un filtro di ricerca — ne ha otto o dodici. Scrivere quello schema a mano è verboso e, peggio, lo schema e la cosa che descrive divergono nel tempo.

### La soluzione

Passa una classe PHP a `ObjectProperty` tramite l'argomento `class`. NeuronAI genera lo schema dalla classe e consegna al tuo tool un'**istanza** di essa.

**Il DTO:**

```php
<?php

namespace App\Neuron\Dto;

use NeuronAI\StructuredOutput\SchemaProperty;

class Color
{
    #[SchemaProperty(description: "The RED part of the RGB", required: true)]
    public float $r;

    #[SchemaProperty(description: "The GREEN part of the RGB", required: true)]
    public float $g;

    #[SchemaProperty(description: "The BLUE part of the RGB", required: true)]
    public float $b;
}
```

**Il tool:**

```php
<?php

namespace App\Neuron\Tools;

use App\Neuron\Dto\Color;
use NeuronAI\Tools\ObjectProperty;
use NeuronAI\Tools\Tool;

class MyTool extends Tool
{
    public function __construct() { /* ... */ }

    protected function properties(): array
    {
        return [
            new ObjectProperty(
                name: 'color',
                description: 'Combination of colors',
                required: true,
                class: Color::class,
            ),
        ];
    }

    public function __invoke(Color $color) { /* ... */ }
}
```

Nota la firma: `__invoke(Color $color)`. Non un array. Un oggetto tipizzato, con completamento nell'IDE, analisi statica e supporto al refactoring.

### Perché è il default che vale la pena adottare

**Schema e tipo non possono divergere.** Aggiungi un campo al DTO e lo schema si aggiorna. Non c'è un secondo posto da ricordarsi di modificare — che è il modo in cui falliscono gli schemi scritti a mano in una base di codice con più di un contributore.

**L'analisi statica torna a funzionare.** PHPStan o Psalm vedono `$color->r`. Con input a forma di array vedono `mixed`, e i corpi dei tuoi tool diventano un punto cieco per l'analisi.

**Il DTO è riusabile.** La stessa classe annotata funziona per lo structured *output* (Capitolo 6). Una classe `Order` può definire che cosa il modello deve produrre e che cosa un tool accetta — lo stesso contratto in entrambe le direzioni.

**`#[SchemaProperty]` supporta vincoli di validazione.** Oltre a `description` e `required`, l'attributo accetta vincoli come `minLength` e `maxLength`. Spingi la validazione dentro lo schema, così il modello riceve le regole invece che il tuo tool scopra le violazioni a runtime. Controlla la firma dell'attributo nella versione che hai installato per l'insieme completo.

::: {.callout .callout-warning}
[Nota sul namespace]{.callout-title}

`SchemaProperty` sta sotto `NeuronAI\StructuredOutput\`, non sotto `NeuronAI\Tools\`. Non è un caso: è lo stesso meccanismo che usa il sistema di structured output, ed è esattamente il motivo per cui il DTO è riusabile in entrambi. La documentazione a volte lo scrive come `NeuronAI\StructuredOutput\Property`, che non esiste; vedi il punto 12 dell'Appendice A.
:::

### Esercizio

Riscrivi il `WeatherTool` del Laboratorio 3 perché prenda un DTO `Coordinates` con `latitude` e `longitude` annotati con `#[SchemaProperty]`. Metti le due versioni una accanto all'altra e decidi quale preferiresti mantenere con quattro contributori.

### Punti chiave

- `ObjectProperty(class: MyDto::class)` genera lo schema da una classe PHP annotata.
- `__invoke()` riceve un'istanza tipizzata, non un array.
- Schema e tipo non possono divergere; l'analisi statica continua a funzionare.
- Lo stesso DTO serve per input e output strutturati.

## 5.7 Toolkit

### Il problema che i toolkit risolvono

Un agent che ha bisogno di aritmetica ha bisogno di somma, sottrazione, moltiplicazione, divisione, elevamento a potenza, radice quadrata, media, mediana, moda, deviazione standard e varianza. Dichiarare undici tool singolarmente in ogni agent è rumore.

### Collegarne uno

```php
<?php

namespace App\Neuron;

use NeuronAI\Agent\Agent;
use NeuronAI\Tools\Toolkits\Calculator\CalculatorToolkit;

class MyAgent extends Agent
{
    protected function tools(): array
    {
        return [
            CalculatorToolkit::make(),
        ];
    }
}
```

Una riga, dodici tool.

### Di che cosa è fatto un toolkit

```php
namespace NeuronAI\Tools\Toolkits\Calculator;

use NeuronAI\Tools\Toolkits\AbstractToolkit;

class CalculatorToolkit extends AbstractToolkit
{
    public function guidelines(): ?string
    {
        return "This toolkit allows you to perform mathematical operations. You can also use this functions to solve
        mathematical expressions executing smaller operations step by step to calculate the final result.";
    }

    public function provide(): array
    {
        return [
            SumTool::make(),
            SubtractTool::make(),
            MultiplyTool::make(),
            DivideTool::make(),
            ExponentiateTool::make(),
        ];
    }
}
```

Due metodi su `AbstractToolkit`.

**`provide()`** restituisce i tool. Una volta collegati, si comportano esattamente come se fossero dichiarati singolarmente.

**`guidelines()` è quello interessante.** Dà al modello informazioni contestuali su come i tool funzionano *insieme*, cosa che nessuna descrizione di singolo tool può trasmettere.

Guarda che cosa dicono davvero le guidelines della calcolatrice: le espressioni complesse si possono risolvere eseguendo operazioni più piccole passo dopo passo. Quella singola frase cambia il comportamento. Senza, un modello davanti a un calcolo in più parti può tentare di farlo a mente — e i modelli linguistici sono inaffidabili con l'aritmetica. Con essa, il modello scompone il problema in chiamate a tool e ottiene la risposta giusta.

**Questo è il punto da mettere in evidenza:** la descrizione di un singolo tool dice *che cosa fa questo tool*. Le guidelines dicono *come combinare questi tool in una strategia*. Se costruisci un tuo toolkit, le guidelines sono dove va la strategia, e saltarle spreca gran parte del meccanismo.

### Il catalogo integrato

| Toolkit | Capacità | Richiede |
|---|---|---|
| **Calculator** | 12 tool: aritmetica, radici, media, mediana, moda, deviazione standard, varianza | — |
| **Calendar** | 18 tool: ora corrente, formattazione, differenze, conversione fuso orario, giorno della settimana, anno bisestile, periodi | — |
| **MySQL / PGSQL** | Introspezione dello schema, SELECT, operazioni di scrittura | PDO |
| **FileSystem** | descrivi directory, leggi, grep, glob, anteprima, parse | — |
| **Tavily** | ricerca web, estrazione pagine, crawl di siti | Chiave API |
| **Jina** | ricerca web, lettore di URL | Chiave API |
| **Supadata YouTube** | trascrizione video, metadati video, canale, playlist | Chiave API |
| **Zep** | memoria a lungo termine: salvataggio e recupero | Chiave API |
| **AWS SES** | invio email | `aws/aws-sdk-php` |

### I toolkit di database meritano attenzione particolare

`MySQLToolkit` dà a un agent accesso genuino ai tuoi dati. Chiedi "quanti ordini abbiamo ricevuto oggi?" e introspeziona lo schema, scrive una query e restituisce il numero vero — nessuna allucinazione.

```php
use NeuronAI\Tools\Toolkits\MySQL\MySQLToolkit;

protected function tools(): array
{
    return [
        MySQLToolkit::make(
            new \PDO("mysql:host=localhost;dbname=DB_NAME;charset=utf8mb4", "DB_USER", "DB_PASS"),
        ),
    ];
}
```

Il toolkit si divide in tool separati per capacità, e **la divisione è il controllo di sicurezza**:

- `MySQLSchemaTool` — legge la struttura
- `MySQLSelectTool` — legge i dati
- `MySQLWriteTool` — INSERT, UPDATE, DELETE

Il consiglio della documentazione stessa vale la pena citarlo: se non sei sicuro del comportamento del tuo agent, puoi semplicemente non fornire il tool di scrittura. Collegare solo i tool di lettura è una mitigazione completa ed efficace, non un compromesso.

Secondo controllo: `MySQLSchemaTool` prende un elenco opzionale di tabelle.

```php
MySQLSchemaTool::make(
    new \PDO(...),
    ['users', 'categories', 'articles', 'tags']
)
```

Questo limita ciò che l'agent può vedere, il che limita ciò che può interrogare. Un agent di contenuti vede articoli, categorie e tag. Un agent di amministrazione utenti vede utenti, ruoli e permessi. Nessuno dei due vede i pagamenti.

Terzo controllo, e quello da enfatizzare di più: **l'istanza PDO è una connessione, quindi dai all'agent credenziali di database sue.** Un utente MySQL in sola lettura costa una sola istruzione `GRANT` e impone a livello di database ciò che la tua selezione di tool impone a livello applicativo. Difesa in profondità, e l'unico livello con cui un prompt non può discutere.

### Punti chiave

- Un toolkit collega un insieme coerente di capacità in una riga.
- `guidelines()` trasmette la strategia trasversale ai tool: la parte che cambia il comportamento.
- I toolkit di database separano lettura e scrittura di proposito; omettere il tool di scrittura è un progetto valido.
- Limita l'ambito dello schema per tabella e dai all'agent credenziali proprie in sola lettura.

## 5.8 Filtri sui toolkit: exclude, only, with

### Perché filtrare non è un vezzo

Un toolkit è un insieme coerente, ma "coerente" non è lo stesso di "appropriato per questo agent". Tre costi concreti del collegarne più del necessario:

**Token.** Nome, descrizione e schema dei parametri di ogni tool vengono trasmessi a **ogni** iterazione del ciclo. Il solo toolkit Calendar è di diciotto tool. A cinque iterazioni hai pagato quello schema cinque volte.

**Errori di tool sbagliato.** L'accuratezza della selezione degrada man mano che il catalogo cresce. Dodici tool aritmetici dove ne bastavano tre significa nove occasioni in più di sceglierne uno sbagliato.

**Raggio d'azione.** Ogni tool collegato è raggiungibile da qualunque utente possa parlare con l'agent. È il modello di sicurezza della Sezione 5.1, applicato agli import di comodo.

### exclude()

Collega il toolkit, rimuovi tool specifici:

```php
class MyAgent extends Agent
{
    protected function tools(): array
    {
        return [
            CalculatorToolkit::make()->exclude([
                DivideTool::class,
                ExponentiateTool::class,
                MultiplyTool::class,
            ]),
        ];
    }
}
```

L'esclusione lavora su nomi di classe pienamente qualificati. Usala quando vuoi la maggior parte di un toolkit e stai rimuovendo alcuni problemi noti.

### only()

Collega il toolkit, tieni un sottoinsieme:

```php
protected function tools(): array
{
    return [
        CalculatorToolkit::make()->only([
            StandardDeviationTool::class,
            MedianTool::class,
        ]),
    ];
}
```

Usala quando vuoi una fetta piccola e specifica di un toolkit grande.

### exclude o only? Una regola che invecchia bene

**Preferisci `only()`.**

`exclude()` è una lista di negazione, e le liste di negazione marciscono. Quando il framework aggiunge tre tool a un toolkit in un rilascio minore, il tuo elenco `exclude()` non ne sa nulla — e il tuo agent acquisisce silenziosamente capacità che non hai mai revisionato.

`only()` è una lista di permessi. Nuovi tool compaiono nel toolkit e il tuo agent non li riceve finché non lo dici tu. È il default corretto per qualunque cosa tocchi dati o effetti collaterali.

Usa `exclude()` quando vuoi davvero ampiezza e stai potando problemi noti. Usa `only()` in tutti gli altri casi, e specialmente nella Parte V quando i tool arrivano al tuo database.

### with()

Recupera un tool specifico dal toolkit e riconfiguralo:

```php
protected function tools(): array
{
    return [
        MySQLToolkit::make()
            ->with(
                MySQLSchemaTool::class,
                fn (ToolInterface $tool) => $tool->setMaxTries(1)
            ),
    ];
}
```

Passa il nome della classe e una callback. L'istanza del tool viene iniettata, ne cambi le impostazioni, la restituisci.

Il tool di schema è l'esempio naturale: a un agent serve ispezionare lo schema una volta sola. Limitarlo a una singola esecuzione impedisce a un modello confuso di rileggere l'intera struttura cinque volte, cosa lenta e costosa dato che l'output dello schema è verboso.

::: {.callout .callout-warning}
[Verifica il nome del metodo]{.callout-title}

L'esempio di `with()` nella documentazione chiama `setMaxTries(1)`, mentre la sezione sui Max Runs usa `setMaxRuns()`. È il punto 2 dell'Appendice A: controlla quale dei due esiste nella versione installata prima di scrivere l'uno o l'altro.
:::

### Combinare i filtri

I metodi si concatenano:

```php
CalculatorToolkit::make()
    ->only([SumTool::class, MeanTool::class, DivideTool::class])
    ->with(DivideTool::class, fn (ToolInterface $tool) => $tool->setMaxRuns(3));
```

Tre tool, uno dei quali limitato. Leggilo dall'alto in basso: seleziona, poi configura.

### Punti chiave

- Filtrare riduce token, errori di tool sbagliato e raggio d'azione.
- Preferisci `only()`: le liste di permessi sopravvivono agli aggiornamenti del framework, quelle di negazione no.
- `with()` riconfigura un singolo tool dentro un toolkit.
- I filtri si concatenano.

## 5.9 Max Runs: proteggere il ciclo

### Il ciclo illimitato, di nuovo

La Sezione 1.2 ha stabilito che il ciclo dell'agent è un `while` senza uscita garantita. Il modello continua a richiedere tool finché non decide di aver finito. Se non decide mai, il ciclo non finisce mai.

Non è ipotetico. Tre modi in cui accade in pratica:

- Il tool restituisce qualcosa che il modello interpreta come fallimento, quindi riprova. All'infinito.
- Il compito è davvero impossibile con i tool disponibili, e il modello continua a provare alternative.
- Due tool si alimentano a vicenda in un ciclo: la ricerca restituisce un riferimento, il recupero restituisce qualcosa che richiede un'altra ricerca.

Ogni iterazione costa una chiamata al modello e fa crescere il contesto. Senza limiti, è una fattura fuori controllo.

### La protezione

NeuronAI tiene traccia di quante volte ogni tool viene invocato durante una sessione di esecuzione. Supera il limite e l'esecuzione viene interrotta con un'eccezione. **Il default è 10 chiamate, contate per singolo tool.**

Quel dettaglio "per singolo tool" conta. Cinque tool al limite di default significano fino a cinquanta esecuzioni di tool in una sola chiamata a `chat()` prima che qualcosa si fermi.

### Impostarlo

```php
try {
    $response = YouTubeAgent::make()
        ->toolMaxRuns(5) // Max number of calls for each tool
        ->addTool(
            // Tool level config takes precedence over the global setting
            CustomTool::make()->setMaxRuns(2)
        )
        ->chat(...)
        ->getMessage();

} catch (ToolMaxTriesException $exception) {
    // do something
}
```

Due livelli:

- **`toolMaxRuns(n)`** sull'agent — il default per ogni tool.
- **`setMaxRuns(n)`** su un tool — sovrascrive l'impostazione dell'agent per quel tool.

**Vince il livello del tool.** Quella precedenza è ciò che vuoi: un default globale permissivo con limiti stretti sui tool lenti, costosi o pericolosi.

::: {.callout .callout-warning}
[Verifica la classe dell'eccezione]{.callout-title}

La prosa della documentazione nomina `ToolRunsExceededException`; l'esempio del blocco catch nomina `ToolMaxTriesException`. È il punto 1 dell'Appendice A. Controlla che cosa solleva davvero la tua versione prima di scrivere un blocco catch: un nome di classe sbagliato in un `catch` produce una non-gestione silenziosa invece di un errore evidente, che è il peggior tipo di bug da ereditare.
:::

### Scegliere i valori

| Carattere del tool | Limite suggerito | Motivo |
|---|---|---|
| Introspezione dello schema | 1 | Si legge una volta; la risposta non cambia a metà esecuzione |
| API esterna costosa | 2–3 | Ogni chiamata costa denaro o quota |
| Calcolo locale economico | 5–10 | Ha davvero bisogno di ripetizione per la matematica multi-passo |
| Operazioni di scrittura | 1 | Due scritture identiche sono quasi sempre un bug |

L'ultima riga è quella importante. Un tool di scrittura con limite 1 significa che un modello che riprova non può addebitare due volte a un cliente. Impostalo deliberatamente.

### Che cosa ti sta dicendo un limite superato

È la parte che sfugge. Un limite di esecuzioni superato di solito non è un limite impostato troppo basso. È una **diagnosi**, e quasi sempre significa una di tre cose:

1. **La descrizione del tuo tool non è chiara**, quindi il modello continua a provare varianti. Torna alla Sezione 5.4.
2. **Il tuo tool restituisce qualcosa di ambiguo** — una stringa vuota, un errore poco utile — quindi il modello non distingue successo da fallimento.
3. **Il compito è impossibile con i tool forniti**, e il modello brancola. Dagli un tool che possa dire "non disponibile" come risposta legittima.

Alzare il limite "per farlo funzionare" cura il sintomo. Quando incontri questa eccezione, leggi il trace e scopri che cosa stava cercando di fare il modello all'ottavo tentativo.

### Gestirlo con eleganza

Un'eccezione che arriva all'utente come un 500 è un male. Intercettala e degrada:

```php
use NeuronAI\Chat\Messages\UserMessage;

try {
    $answer = $agent->chat(new UserMessage($input))->getMessage()->getContent();
} catch (\Throwable $e) {
    // Log the full trace for diagnosis
    $logger->warning('Agent exceeded tool run limit', [
        'input'     => $input,
        'exception' => $e::class,
        'message'   => $e->getMessage(),
    ]);

    $answer = "I couldn't complete that request. Could you rephrase it, "
            . "or would you like me to pass it to a human?";
}
```

La Sezione 5.11 copre un'opzione più sofisticata: restituire l'errore al modello perché possa recuperare da solo.

### Punti chiave

- Il default è 10 esecuzioni, per tool, per sessione di esecuzione.
- `toolMaxRuns()` imposta il default dell'agent; `setMaxRuns()` su un tool lo sovrascrive.
- I tool di scrittura vanno limitati a 1.
- Un limite superato è una diagnosi sulla progettazione del tool, non un limite da alzare.

## 5.10 Visibilità: disponibilità condizionale dei tool

### L'API

```php
class YouTubeAgent extends Agent
{
    protected function tools(): array
    {
        return [
            GetTranscriptionTool::make('API_KEY')->visible(
                auth()->user()->can(...)
            ),
        ];
    }
}
```

`visible(false)` e il tool non è disponibile durante l'esecuzione dell'agent. Non è nello schema mandato al modello. Per quanto riguarda il modello, non esiste.

### Perché nascondere batte istruire

L'alternativa allettante è mettere la regola nel system prompt:

> "Usa il tool di rimborso solo se l'utente è un amministratore."

Non farlo. Tre motivi, in ordine crescente di gravità:

**Trapela.** Il modello sa che il tool esiste e lo menzionerà. "Potrei elaborare un rimborso, ma non hai i permessi" dice all'utente esattamente quale capacità andare a cercare.

**È inaffidabile.** Le istruzioni vengono seguite in modo probabilistico. La Sezione 1.5 diceva di presumere il non determinismo, e una regola di controllo accessi che funziona il novantotto per cento delle volte non è controllo accessi.

**È attaccabile.** Le istruzioni nel system prompt competono con le istruzioni nel messaggio dell'utente. La prompt injection è una tecnica reale; uno schema che non ha mai incluso il tool non è vulnerabile.

`visible(false)` rimuove la capacità invece di vietarne l'uso. Il modello non può richiedere un tool di cui non gli è mai stato detto nulla.

### Dove si colloca la visibilità fra i livelli

Quattro meccanismi indipendenti, e capire che cosa fa ciascuno è il punto di questa sezione:

| Livello | Meccanismo | Imposto da |
|---|---|---|
| Non offerto | `visible(false)` | Costruzione dello schema |
| Offerto, filtrato a runtime | Middleware `ToolApproval` | Decisione umana |
| Offerto, verificato all'esecuzione | Controllo di policy dentro `__invoke()` | Il tuo PHP |
| Offerto, ristretto alla fonte | Grant di database, scope delle API | Infrastruttura |

Usane più d'uno. `visible()` è la tua prima linea, non l'unica: un bug nell'espressione di visibilità non dovrebbe essere l'unica cosa fra un utente e un rimborso.

### Visibilità e approvazione

La documentazione traccia bene questa distinzione e vale la pena riprodurla con precisione:

- La **visibilità** è una decisione di *build time*. Il tool è incluso nello schema oppure no. Deciso prima che il modello veda qualunque cosa.
- L'**approvazione** è un guardiano di *runtime*. Il tool viene offerto, il modello lo richiede, e il framework intercetta la chiamata e si ferma per una decisione umana.

L'approvazione si esprime con il middleware `ToolApproval`, e può essere condizionale rispetto agli argomenti:

```php
new ToolApproval(
    tools: [
        BuyTicketTool::class => function (array $args): bool {
            return $args['amount'] > 100;
        }
    ]
)
```

I piccoli acquisti passano; quelli grandi aspettano un essere umano. È un prodotto molto migliore sia di "consenti sempre" sia di "blocca sempre". Lo costruiamo per bene nel Capitolo 15 e lo colleghiamo a una vera interfaccia nel Capitolo 22 — menzionato qui perché la distinzione si fissi mentre la visibilità è fresca.

### Il pattern da adottare

Calcola la visibilità dall'attore, non da un globale:

```php
class OrderAgent extends Agent
{
    public function __construct(private User $user)
    {
        parent::__construct();
    }

    protected function tools(): array
    {
        return [
            SearchOrdersTool::make($this->orders),

            GetOrderStatusTool::make($this->orders),

            RequestRefundTool::make($this->refunds)
                ->visible($this->user->can('refund.create')),

            DeleteOrderTool::make($this->orders)
                ->visible($this->user->hasRole('admin')),
        ];
    }
}
```

L'agent prende l'utente come dipendenza del costruttore e deriva la propria superficie di capacità. Due utenti che parlano con "lo stesso agent" stanno parlando con agent che hanno elenchi di tool diversi.

Nota che questo richiede `new OrderAgent($user)` invece di `::make()`, come stabilito nella Sezione 4.3.

### Esercizio

Aggiungi al tuo agent dimostrativo un tool `delete_cache`, visibile solo quando `APP_ROLE=admin`. Esegui l'agent come non amministratore e chiedigli direttamente: "cancella la cache". Poi chiedi: "quali tool hai?". Verifica che il tool sia assente sia dal comportamento sia dalla risposta.

### Punti chiave

- `visible(false)` rimuove del tutto il tool dallo schema.
- Nascondere batte istruire: le restrizioni basate sul prompt trapelano, sono probabilistiche e sono attaccabili.
- La visibilità è build time; l'approvazione è runtime. Esistono entrambe, per lavori diversi.
- Deriva la visibilità dall'attore, iniettato nel costruttore dell'agent.

## 5.11 Gestione degli errori dei tool

### Il default

`ToolNode` accetta un argomento `$errorHandler`. **Per default rilancia gli errori di esecuzione.** Il tuo tool solleva un'eccezione, e questa si propaga attraverso `chat()` fino alla tua applicazione.

È un default ragionevole — un fallimento silenzioso sarebbe peggio — ma raramente è ciò che vuoi in produzione. Un timeout transitorio su una chiamata a tool, e una conversazione che stava andando bene muore.

### L'alternativa: dirlo al modello

È l'idea che vale l'intera sezione. Invece di andare in crash, restituisci l'errore al modello come risultato del tool.

**Se l'handler restituisce un valore, quel valore viene restituito al modello come risultato del tool.**

Il modello decide poi che cosa fare: riprovare con argomenti diversi, provare un altro tool, o dire all'utente che il dato non è disponibile. Ottieni degrado elegante senza scrivere logica di recupero, perché la logica di recupero è il modello.

### Definizione fluente

```php
$agent = Agent::make()
    ->toolErrorHandler(
        fn (Throwable $e, ToolInterface $tool): string => "Error: {$e->getMessage()}"
    );
```

### Dentro la classe agent

```php
class MyAgent extends Agent
{
    protected function resolveToolErrorHandler(): ?callable
    {
        return fn (Throwable $e, ToolInterface $tool): string => "Error: {$e->getMessage()}";
    }
}
```

La callback riceve l'eccezione e l'istanza del tool fallito. Contano entrambe: l'istanza del tool ti permette di ramificare in base a quale tool ha fallito.

### Scrivere un buon handler

La versione ingenua fa trapelare dettagli interni nella conversazione. Uno stack trace da 500 caratteri diventa contesto su cui il modello deve ragionare, ed eventualmente testo che un utente vede.

Scrivi handler che dicano al modello qualcosa di *azionabile*:

```php
protected function resolveToolErrorHandler(): ?callable
{
    return function (\Throwable $e, ToolInterface $tool): string {
        $this->logger->error('Tool failure', [
            'tool'      => $tool->getName(),
            'exception' => $e::class,
            'message'   => $e->getMessage(),
        ]);

        return match (true) {
            $e instanceof ConnectException =>
                "The {$tool->getName()} service is temporarily unreachable. "
                . "Do not retry more than once. If it fails again, tell the user "
                . "the data is unavailable right now.",

            $e instanceof NotFoundException =>
                "No record matched those arguments. Check the values with the user "
                . "before trying again.",

            $e instanceof \InvalidArgumentException =>
                "Invalid arguments: {$e->getMessage()}. Correct them and retry once.",

            default =>
                "The {$tool->getName()} tool failed. Tell the user you could not "
                . "complete this step, and do not retry.",
        };
    };
}
```

Tre principi visibili in quel codice:

**Logga tutto, di' poco al modello.** I tuoi log ricevono lo stack trace. Il modello riceve una frase.

**Includi l'istruzione, non solo il fatto.** "Non riprovare più di una volta" sta facendo lavoro vero. Senza, un fallimento transitorio può bruciare il limite di esecuzioni della Sezione 5.9 in pochi secondi.

**Non far mai trapelare dettagli interni nella conversazione.** Stringhe di connessione, percorsi di file, hostname interni, credenziali nei messaggi d'eccezione: tutto finisce nella trascrizione, che può essere conservata, loggata e mostrata all'utente.

### L'interazione con i max runs

L'handler degli errori intercetta anche l'eccezione del limite di esecuzioni. Ti dà un'uscita elegante al limite invece di un'eccezione al confine:

```php
$e instanceof ToolRunsExceededException =>
    "You have used this tool too many times. Stop calling it and answer with "
    . "what you already know, or tell the user you cannot complete the task.",
```

Il modello riceve un chiaro segnale di stop e scrive un messaggio finale sensato. Molto meglio di un 500. Il punto 1 dell'Appendice A vale anche qui: conferma il nome della classe dell'eccezione prima di scrivere questo ramo.

### Quando lasciarlo esplodere

Non tutto va gestito. Lascia propagare quando:

- Il fallimento indica un bug che devi vedere nel tuo error tracker
- Il fallimento è una violazione di permessi — non lasciare che il modello ci ragioni sopra: fallisci in modo netto e registralo
- Il fallimento lascerebbe i dati in uno stato incoerente

"Restituisci l'errore al modello" è un pattern di resilienza per fallimenti attesi e recuperabili. Non sostituisce la correttezza.

### Punti chiave

- Il comportamento di default è rilanciare; configura un handler per la produzione.
- Un valore restituito diventa il risultato del tool che il modello vede.
- Logga tutto, di' poco al modello, e includi un'istruzione sul riprovare.
- Non far mai trapelare dettagli interni nella trascrizione.
- Lascia esplodere violazioni di permessi e bug.

## 5.12 Provider tool

### Che cosa sono

Alcuni provider offrono tool lato server — ricerca web, ricerca su file e altri — che vengono eseguiti nella loro infrastruttura invece che nel tuo processo PHP. Tu li abiliti; il provider li esegue.

### L'API

```php
use NeuronAI\Tools\ProviderTool;

class MyAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return new OpenAIResponses(
            key: 'OPENAI_API_KEY',
            model: 'OPENAI_MODEL',
        );
    }

    protected function tools(): array
    {
        return [
            ProviderTool::make(
                type: 'web_search'
            )->setOptions([/* ... */]),
        ];
    }
}
```

Stanno nello stesso array `tools()` di tutto il resto, che è un bel pezzo di progettazione di API: l'astrazione tiene.

**Il supporto è limitato a `OpenAIResponses`, `Gemini` e `Anthropic`.**

::: {.callout .callout-warning}
[Refuso nella documentazione]{.callout-title}

La documentazione mostra `ProviderTool:make()` con un solo due punti. È un refuso per `::`. Punto 6 dell'Appendice A.
:::

### Il compromesso, come lo dicono i documenti

La documentazione ufficiale è rinfrescantemente schietta: i provider tool introducono molti vincoli, e il modo più flessibile e affidabile di aggiungere capacità ai tuoi agent resta il sistema di Tool e Toolkit.

Sono gli autori del framework che ti dicono che la loro stessa funzionalità è la seconda scelta. Prendili in parola, e capisci perché:

**Perdi portabilità.** È il punto grosso. La Sezione 3.6 vendeva lo scambio di provider come beneficio centrale del framework. Un provider tool ti ancora: passa da OpenAI a Ollama e quella capacità sparisce silenziosamente. L'intero argomento su stratificazione dei costi e rischio fornitore evapora per qualunque agent che ne dipenda.

**Perdi controllo.** Non puoi vedere la query, filtrare le fonti, mettere in cache il risultato, applicargli un rate limit o loggare che cosa è stato recuperato. Per un ambiente regolamentato, "non sappiamo che cosa ha cercato" non è una risposta accettabile.

**Perdi testabilità.** Nessun fake, nessuno stub, nessuna CI offline. La Sezione 5.3 faceva della testabilità l'argomento a favore delle classi tool; i provider tool la restituiscono.

**Erediti i loro vincoli.** Rate limit, disponibilità regionale, prezzi e comportamento sono tutti fuori dal tuo controllo e possono cambiare senza un deploy da parte tua.

### Quando sono la scelta giusta

Non mai. I provider tool sono genuinamente buoni quando:

- Stai prototipando e vuoi la ricerca web funzionante in trenta secondi
- L'implementazione del provider è materialmente migliore di quella che costruiresti (il loro indice di ricerca, la loro gestione dei documenti)
- Sei già legato a quel provider per altri motivi
- La capacità è periferica: bella da avere, non portante

### Il default consigliato

Usa `TavilyToolkit` o `JinaToolkit` per la ricerca web. Entrambi sono portabili, funzionano con qualunque provider, sono testabili e ti permettono di vedere e mettere in cache ciò che torna indietro.

Ricorri a un provider tool quando hai una ragione specifica, e mettila per iscritto.

### Punti chiave

- I provider tool girano lato server; supportati solo su OpenAIResponses, Gemini e Anthropic.
- Ti costano portabilità, controllo, testabilità e indipendenza.
- La documentazione del framework stesso consiglia il sistema portabile Tool/Toolkit.
- Buoni per prototipi e capacità periferiche; cattivi per qualunque cosa portante.

## 5.13 Chiamate parallele ai tool

### Il problema

Quando il modello richiede tre tool in un solo turno, il comportamento di default è sequenziale:

```
1. Chiama il tool A → aspetta il risultato
2. Chiama il tool B → aspetta il risultato
3. Chiama il tool C → aspetta il risultato

Tempo totale: Tempo(A) + Tempo(B) + Tempo(C)
```

Tre chiamate API da 800 ms ciascuna sono 2,4 secondi in cui l'utente fissa il nulla — e questa è una sola iterazione del ciclo.

Con l'esecuzione parallela:

```
1. Chiama i tool A, B e C tutti insieme
2. Aspetta che finiscano tutti

Tempo totale: Max(Tempo(A), Tempo(B), Tempo(C))
```

800 ms. Un terzo del tempo, per un booleano.

### Abilitarla

```bash
composer require spatie/fork
```

```php
class DemoAgent extends Agent
{
    public function __construct()
    {
        parent::__construct();
        $this->parallelToolCalls(true);
    }

    protected function provider(): AIProviderInterface
    {
        // ...
    }

    protected function tools(): array
    {
        return [
            CalculatorToolkit::make(),
        ];
    }
}
```

Sotto il cofano il framework inserisce un `ParallelToolNode` al posto dello `ToolNode` standard. È la Sezione 2.3 che diventa concreta: un agent è un workflow, e "abilita i tool paralleli" significa *scambiare un nodo con un altro*. È la prima volta in questo libro che il substrato dei workflow fa qualcosa di visibile.

### Il vincolo che decide tutto

**Richiede l'estensione `pcntl`, e `pcntl` funziona solo nei processi CLI, non in contesto web.**

Rileggilo due volte prima di progettare intorno a questa funzionalità. Significa:

| Contesto | Tool paralleli |
|---|---|
| Script CLI | ✅ Sì |
| Comando artisan | ✅ Sì |
| Queue worker (CLI) | ✅ Sì |
| Richiesta HTTP via PHP-FPM | ❌ No |
| Richiesta web in qualunque SAPI | ❌ No |

Per un'applicazione web la via pratica è: spingi l'esecuzione dell'agent su un queue worker, che è un processo CLI. È lì che si applicano i tool paralleli — e guarda caso è dove volevi comunque il lavoro agentico a lunga esecuzione, per le ragioni di latenza della Sezione 1.4. Il Capitolo 22 lo costruisce per bene.

### Degrado elegante

Il progetto qui è ben pensato: se `pcntl` non è presente — una macchina di sviluppo Windows, per esempio — l'implementazione **ricade automaticamente sull'esecuzione sequenziale**. Nessuna configurazione, nessun rilevamento d'ambiente nel tuo codice, nessun crash.

Sviluppi in locale senza `pcntl` e metti in produzione dove è abilitato, senza cambiare una riga. L'agent si adatta a qualunque ambiente si trovi.

È un buon esempio di framework che assorbe la variazione ambientale invece di scaricarla sullo sviluppatore, e vale la pena rubarlo come pattern di progetto anziché usarlo solo come funzionalità.

### Quando aiuta davvero

L'esecuzione parallela aiuta solo quando il modello richiede **più tool in un singolo turno**. Non fa nulla per:

- Dipendenze sequenziali — B ha bisogno dell'output di A, quindi non possono sovrapporsi
- Turni con un solo tool
- Tool locali veloci, dove il costo del fork supera il lavoro

Aiuta soprattutto con più chiamate indipendenti legate all'I/O: tre ricerche meteo, quattro query API, cinque letture di file. Se il tuo agent non è affamato di tool in questo modo specifico, abilitarla non cambia nulla.

### Cautele

**I processi forkati non condividono lo stato.** Ogni fork è un processo separato. I tool che mutano stato condiviso in memoria, tengono aperta una transazione o presumono un singleton si comporteranno diversamente. Tieni i tool stateless e autosufficienti — cosa che la Sezione 5.1 raccomandava comunque, per altri motivi.

**Il debugging è più difficile.** Gli errori in un processo forkato sono meno piacevoli da tracciare. Sviluppa con la funzionalità disattivata, abilitala quando l'insieme dei tool è stabile.

**Le connessioni al database vanno trattate con cura.** Una connessione PDO ereditata attraverso un fork è una classica fonte di fallimenti strani e intermittenti. Se i tuoi tool toccano il database, apri la connessione dentro il tool invece di condividerne una fra i fork.

### Punti chiave

- `parallelToolCalls(true)` scambia `ToolNode` con `ParallelToolNode`.
- Richiede `spatie/fork` e `pcntl`; **solo CLI**, mai in una richiesta web.
- Ricade automaticamente sul sequenziale quando non disponibile.
- Aiuta solo con più chiamate indipendenti legate all'I/O in un singolo turno.
- Tieni i tool stateless; attenzione alle connessioni al database fra i fork.

## Laboratorio 3 — Agent meteo e calcolatrice

**Copre:** classe tool custom, toolkit, filtri, max runs, gestione degli errori.

### Obiettivo

Un agent che risponde a *"Che temperatura media c'è adesso fra Torino e Milano?"* chiamando due volte un tool meteo e una volta un tool di calcolo. Tre andate e ritorno verso il modello — la dimostrazione più chiara del ciclo dell'agent in tutto il libro.

### Il tool

**`src/Tools/WeatherTool.php`**

```php
<?php

declare(strict_types=1);

namespace App\Tools;

use GuzzleHttp\Client;
use NeuronAI\Tools\PropertyType;
use NeuronAI\Tools\Tool;
use NeuronAI\Tools\ToolProperty;

class WeatherTool extends Tool
{
    protected Client $client;

    public function __construct()
    {
        parent::__construct(
            'get_current_weather',
            'Returns current weather conditions for a geographic location: temperature '
            . 'in Celsius, wind speed in km/h, and a numeric weather code. Use this '
            . 'whenever the user asks about current weather, temperature, or conditions '
            . 'anywhere in the world. You must derive latitude and longitude yourself '
            . 'from the place name. Never invent weather data — always call this tool.'
        );
    }

    protected function properties(): array
    {
        return [
            new ToolProperty(
                name: 'latitude',
                type: PropertyType::NUMBER,
                description: 'Latitude in decimal degrees. Example: 45.0703 for Turin, Italy. '
                           . 'Negative values for the southern hemisphere.',
                required: true,
            ),
            new ToolProperty(
                name: 'longitude',
                type: PropertyType::NUMBER,
                description: 'Longitude in decimal degrees. Example: 7.6869 for Turin, Italy. '
                           . 'Negative values for the western hemisphere.',
                required: true,
            ),
        ];
    }

    public function __invoke(float $latitude, float $longitude): string
    {
        $body = $this->getClient()->get('forecast', [
            'query' => [
                'latitude'  => $latitude,
                'longitude' => $longitude,
                'current'   => 'temperature_2m,wind_speed_10m,weather_code',
            ],
        ])->getBody()->getContents();

        $data = \json_decode($body, true, 512, JSON_THROW_ON_ERROR);

        if (!isset($data['current'])) {
            throw new \RuntimeException('No current weather data in the API response.');
        }

        return \json_encode($data['current'], JSON_THROW_ON_ERROR);
    }

    protected function getClient(): Client
    {
        return $this->client ??= new Client([
            'base_uri' => 'https://api.open-meteo.com/v1/',
            'timeout'  => 10,
        ]);
    }
}
```

Open-Meteo non richiede chiavi API, quindi l'intero laboratorio gira gratis — combinato con Ollama, lo completi senza un account da nessuna parte.

### L'agent

**`src/Agents/WeatherAgent.php`**

```php
<?php

declare(strict_types=1);

namespace App\Agents;

use App\ProviderFactory;
use App\Tools\WeatherTool;
use NeuronAI\Agent\Agent;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Tools\Toolkits\Calculator\CalculatorToolkit;
use NeuronAI\Tools\Toolkits\Calculator\DivideTool;
use NeuronAI\Tools\Toolkits\Calculator\MeanTool;
use NeuronAI\Tools\Toolkits\Calculator\SumTool;
use NeuronAI\Tools\ToolInterface;

class WeatherAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return ProviderFactory::make();
    }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: [
                'You are a weather assistant. You only report real data obtained from your tools.',
            ],
            steps: [
                'Derive the geographic coordinates of every location mentioned by the user.',
                'Call the weather tool once for each location.',
                'If a comparison or an average is requested, use the calculator tools.',
            ],
            output: [
                'Answer in English, in two sentences at most.',
                'Always state temperatures in degrees Celsius.',
            ],
        );
    }

    protected function tools(): array
    {
        return [
            WeatherTool::make()->setMaxRuns(4),

            CalculatorToolkit::make()->only([
                SumTool::class,
                DivideTool::class,
                MeanTool::class,
            ]),
        ];
    }

    protected function resolveToolErrorHandler(): ?callable
    {
        return function (\Throwable $e, ToolInterface $tool): string {
            $class = $e::class;

            \error_log("[tool:{$tool->getName()}] {$class}: {$e->getMessage()}");

            return "The {$tool->getName()} tool failed: {$e->getMessage()}. "
                 . "Do not retry more than once. If it fails again, tell the user "
                 . "the data is unavailable.";
        };
    }
}
```

Nota che cosa dimostra questa singola classe di tutto il capitolo: un tool come classe (5.3), una descrizione in quattro parti (5.4), esempi nelle descrizioni delle proprietà (5.4), `only()` come lista di permessi (5.8), un limite di esecuzioni per tool (5.9) e un vero handler degli errori (5.11).

### L'esecutore

**`examples/03-weather-agent.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\WeatherAgent;
use NeuronAI\Chat\Messages\UserMessage;

$prompt = $argv[1] ?? "What's the average current temperature between Turin and Milan?";

$start = \microtime(true);

try {
    echo WeatherAgent::make()
        ->toolMaxRuns(6)
        ->chat(new UserMessage($prompt))
        ->getMessage()
        ->getContent() . PHP_EOL;

    \printf("\n[%.2fs]\n", \microtime(true) - $start);
} catch (\Throwable $e) {
    \fwrite(STDERR, "Failed: {$e->getMessage()}\n");
    exit(1);
}
```

```bash
php examples/03-weather-agent.php
php examples/03-weather-agent.php "Compare Turin, Milan, Rome and Palermo. Which is warmest?"
```

### Due cose da osservare

Eseguilo con `INSPECTOR_INGESTION_KEY` impostata e apri il trace. Vedi la sequenza reale: due chiamate meteo, una chiamata alla media, una risposta testuale finale. Quell'immagine è ciò che la tabella della Sezione 1.2 descriveva in astratto, e vederla rende concreta l'aritmetica dei costi della Sezione 1.4.

Poi rompilo deliberatamente: cambia la descrizione del tool in `'Gets the weather.'` e rilancia. Spesso il modello risponde dalla conoscenza generale senza chiamare affatto il tool. Rimettila come prima. Una stringa, comportamento completamente diverso — l'affermazione della Sezione 5.4, dimostrata sulla tua macchina.

## Laboratorio 4 — Agent analista di database

**Copre:** toolkit MySQL, restrizione dello schema, minimo privilegio, progetto in sola lettura.

### Obiettivo

Un agent che risponde a domande vere su un database vero senza allucinare numeri.

### Prepara un utente di database ristretto

Prima di qualunque PHP, questo:

```sql
CREATE USER 'agent_ro'@'localhost' IDENTIFIED BY 'a-strong-password';

GRANT SELECT ON shop.orders     TO 'agent_ro'@'localhost';
GRANT SELECT ON shop.customers  TO 'agent_ro'@'localhost';
GRANT SELECT ON shop.products   TO 'agent_ro'@'localhost';

FLUSH PRIVILEGES;
```

**Fallo per primo.** Tutto il resto di questo laboratorio è controllo a livello applicativo che un prompt sufficientemente ingegnoso potrebbe aggirare. Questa concessione è imposta da MySQL. È l'unico livello che non si può convincere a cambiare posizione.

### L'agent

**`src/Agents/DataAnalystAgent.php`**

```php
<?php

declare(strict_types=1);

namespace App\Agents;

use App\ProviderFactory;
use NeuronAI\Agent\Agent;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Tools\Toolkits\Calculator\CalculatorToolkit;
use NeuronAI\Tools\Toolkits\MySQL\MySQLSchemaTool;
use NeuronAI\Tools\Toolkits\MySQL\MySQLSelectTool;
use NeuronAI\Tools\ToolInterface;

class DataAnalystAgent extends Agent
{
    private \PDO $pdo;

    public function __construct()
    {
        parent::__construct();

        $this->pdo = new \PDO(
            \sprintf(
                'mysql:host=%s;dbname=%s;charset=utf8mb4',
                env('DB_HOST', '127.0.0.1'),
                env('DB_NAME', 'shop'),
            ),
            env('DB_USER', 'agent_ro'),
            env('DB_PASS', ''),
            [\PDO::ATTR_ERRMODE => \PDO::ERRMODE_EXCEPTION],
        );
    }

    protected function provider(): AIProviderInterface
    {
        return ProviderFactory::make();
    }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: [
                'You are a data analyst working with a read-only e-commerce database.',
                'You never estimate or guess numbers. Every figure you report comes from a query.',
            ],
            steps: [
                'Inspect the database schema first, once, to understand the available tables.',
                'Write a SELECT query that answers the question.',
                'Use the calculator tools for any derived statistics.',
            ],
            output: [
                'State the number, then the query you ran, in a fenced sql block.',
                'If a question cannot be answered with the available tables, say so plainly.',
            ],
        );
    }

    protected function tools(): array
    {
        return [
            MySQLSchemaTool::make(
                $this->pdo,
                ['orders', 'customers', 'products'],
            )->setMaxRuns(1),

            MySQLSelectTool::make($this->pdo)->setMaxRuns(5),

            CalculatorToolkit::make(),
        ];
    }

    protected function resolveToolErrorHandler(): ?callable
    {
        return fn (\Throwable $e, ToolInterface $tool): string =>
            "Query failed: {$e->getMessage()}. Check the schema and correct the SQL. "
            . "Do not retry more than twice.";
    }
}
```

### L'esecutore

**`examples/05-data-analyst.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\DataAnalystAgent;
use NeuronAI\Chat\Messages\UserMessage;

$question = $argv[1] ?? 'How many orders did we receive today?';

echo (new DataAnalystAgent())
    ->chat(new UserMessage($question))
    ->getMessage()
    ->getContent() . PHP_EOL;
```

```bash
php examples/05-data-analyst.php "How many orders did we receive today?"
php examples/05-data-analyst.php "What's the average order value this month, by country?"
php examples/05-data-analyst.php "Which three products have the highest revenue?"
```

### Quattro livelli di difesa

1. **`MySQLWriteTool` non è collegato.** L'agent non ha modo di scrivere.
2. **Lo schema è ristretto a tre tabelle.** L'agent non può vedere `payments` o `users`.
3. **`MySQLSchemaTool` è limitato a una esecuzione.** Nessuna introspezione costosa ripetuta.
4. **L'utente di database ha solo SELECT su tre tabelle.** Imposto da MySQL.

Poi esegui la dimostrazione che rende il punto:

```bash
php examples/05-data-analyst.php "Delete all orders from last year."
```

L'agent spiega che non può. Non perché il prompt gli abbia detto di non farlo — perché **non esiste un tool che scrive.** Quella distinzione è l'intera lezione di sicurezza di questo capitolo, e arriva molto meglio come qualcosa che esegui che come qualcosa che leggi.

## Esercizi del capitolo

1. **Progetta.** Prendi una funzionalità della tua applicazione e progetta tre tool per essa. Scrivi le descrizioni prima delle implementazioni. Per ciascuna, rispondi alle quattro domande della Sezione 5.4.

2. **Converti.** Prendi un tool inline e convertilo in una classe. Scrivi un test PHPUnit che lo invochi direttamente senza alcun agent coinvolto.

3. **Vincola.** Collega un toolkit con `only()`, imposta un limite di esecuzioni per tool e aggiungi un handler degli errori che restituisca un'istruzione invece di uno stack trace.

4. **Rompilo.** Scrivi deliberatamente una descrizione vaga e osserva il fallimento. Correggilo cambiando una stringa. Annota che cosa è cambiato nel comportamento del modello.

5. **Metti in sicurezza.** Per un agent con accesso al database, elenca i tuoi livelli di difesa e individua quello che un attaccante non potrebbe sconfiggere con un prompt.

::: {.callout .callout-warning}
[Prima di mettere in produzione qualcosa da questo capitolo]{.callout-title}

La documentazione sui Tool è la pagina più densa del progetto NeuronAI ed è in disaccordo con sé stessa in nove punti: nomi di eccezioni, nomi di metodi, nomi di classi, namespace e percorsi di import. Ognuno produce un errore fatale per chi copia la pagina. Sono i punti da 1 a 9 dell'Appendice A, con script di verifica che li risolvono tutti sulla tua versione installata in pochi minuti.
:::
