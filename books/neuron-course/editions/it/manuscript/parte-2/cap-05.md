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

Nota che in gioco ci sono due cose diverse, e NeuronAI le tiene separate. Il **tool** è capacità: un oggetto PHP con uno schema, un metodo `__invoke()` e tutte le dipendenze di cui ha bisogno — una connessione PDO, un client HTTP. Vive sull'agent e non lascia mai il tuo processo. La **tool call** è un dato: un value object `ToolCall` che registra una singola invocazione — il nome del tool, l'ID di chiamata assegnato dal modello, gli argomenti e, in seguito, il risultato. I messaggi, la cronologia della conversazione, i chunk di streaming e lo stato persistito trasportano oggetti `ToolCall`, mai tool. Al momento dell'esecuzione il framework risolve ogni chiamata per nome sull'elenco dei tool attivi dell'agent; una chiamata che nomina un tool che l'agent non offre fallisce in modo evidente invece di eseguire qualcosa.

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

**Onesto nel fallimento.** Restituire "Ordine non trovato" è utile al modello. Restituire una stringa vuota lo lascia a indovinare, e un modello che indovina allucina. NeuronAI ti dà una forma dedicata per questo — `ToolOutput::error()` — di cui si occupa la Sezione 5.11.

### Il cambio di mentalità

Smetti di pensare ai tool come a una funzionalità di integrazione. Sono la **superficie di capacità del tuo agent** — un problema di progettazione di API, dove il consumatore è un modello linguistico invece di un altro sviluppatore.

Questa inquadratura spiega perché il resto del capitolo dedica tanto tempo a nomi, descrizioni e schemi. Stai scrivendo documentazione per un consumatore che legge solo la documentazione.

### Punti chiave

- Un tool è la tua funzione; il modello richiede, il tuo codice esegue.
- Il tool è capacità e resta sull'agent; la `ToolCall` è un dato e viaggia nella conversazione.
- L'elenco dei tool registrati è il confine di sicurezza, l'unico su cui puoi contare.
- I buoni tool sono stretti, deterministici, compatti nell'output ed espliciti sul fallimento.
- Progettare tool è progettare API per un lettore che ha solo la documentazione.

## 5.2 Tool inline

### La forma

`Tool` è astratta: ogni tool è una classe che la estende. Quando un tool è piccolo e usato in un solo punto, quella classe non ha bisogno di un file e nemmeno di un nome — dichiarala come classe anonima, direttamente dentro `tools()`:

```php
new class extends Tool {
    protected string $name = 'name';
    protected ?string $description = 'description';
    protected function properties(): array { return [new ToolProperty(/* ... */)]; }
    public function __invoke(string $input): string { /* ... */ }
};
```

Tre pezzi: identità, schema, implementazione. L'identità sono due proprietà della classe, `$name` e `$description`. Lo schema è ciò che restituisce `properties()`. L'implementazione è `__invoke()`.

### L'esempio canonico

È l'agent per i riassunti di YouTube della documentazione ufficiale, con il suo tool dichiarato sul posto. Vale la pena conoscerlo perché incontrerai questo agent ovunque:

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
            new class extends Tool {
                protected string $name = 'get_transcription';

                protected ?string $description = 'Retrieve the transcription of a youtube video.';

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
                    return 'Video transcription...';
                }
            },
        ];
    }
}
```

### La regola su cui inciampano tutti

**Il nome della proprietà deve corrispondere al nome del parametro di `__invoke()`.**

La proprietà si chiama `video_url`. La firma del metodo è `__invoke(string $video_url)`. Non `$url`, non `$videoUrl`. Esattamente `$video_url`.

NeuronAI passa gli argomenti del modello a `__invoke()` come **argomenti con nome**, indicizzati per nome della proprietà. Rinomina un lato e PHP lancia `Error: Unknown named parameter $video_url` la prima volta che il modello chiama il tool — un'eccezione che interrompe la run e che, a prima vista, sembra un errore del modello, mentre in realtà è il tuo cablaggio. È il bug sui tool più comune in assoluto.

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
    ->setThreadId('demo')
    ->chat(new UserMessage($question))
    ->getMessage()
    ?->getContent() . PHP_EOL;
```

È la catena della Sezione 3.4: `setThreadId()` dice a quale conversazione appartiene la run, `chat()` restituisce lo stato finale dell'agent, e `getMessage()` ne legge l'ultimo messaggio del modello. Il suo tipo di ritorno è nullable — una run che si ferma prima che una qualunque inferenza abbia prodotto una risposta non ha alcun messaggio da leggere — da qui il `?->`.

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
use NeuronAI\Tools\ToolOutput;
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
            new class extends Tool {
                protected string $name = 'get_server_load';

                protected ?string $description = 'Returns the average CPU load of this server over a given time window. '
                    . 'Use this whenever asked about current server load, stress, or performance.';

                protected function properties(): array
                {
                    return [
                        new ToolProperty(
                            name: 'window',
                            type: PropertyType::STRING,
                            description: 'The time window to average over.',
                            required: true,
                            enum: ['1m', '5m', '15m'],
                        ),
                    ];
                }

                public function __invoke(string $window): string|ToolOutput
                {
                    $load = \sys_getloadavg();

                    if ($load === false) {
                        return ToolOutput::error('Load average is not available on this platform.');
                    }

                    $value = match ($window) {
                        '1m'  => $load[0],
                        '5m'  => $load[1],
                        '15m' => $load[2],
                        default => throw new \LogicException("Unexpected window \"{$window}\"."),
                    };

                    return \sprintf('Load average over %s: %.2f', $window, $value);
                }
            },
        ];
    }
}
```

```bash
php examples/02-inline-tool.php "How stressed is the server compared to fifteen minutes ago?"
```

Quella domanda forza due chiamate allo stesso tool con argomenti diversi — un primo esperimento migliore di una domanda a chiamata singola, perché vedi il ciclo iterare.

Qui sono possibili due fallimenti, e vengono gestiti in due punti diversi. Una finestra che il modello sbaglia non arriva mai a `__invoke()`: l'`enum:` entra nello schema che il modello legge, e NeuronAI lo fa rispettare al momento del binding degli argomenti. Chiedi `"30m"` e il risultato del tool è `Parameter "window" must be one of "1m", "5m", "15m"; "30m" given.` — una frase su cui il modello può agire, quindi il ciclo continua. Ecco perché il ramo `default` lancia un'eccezione: nessuna chiamata che passa dall'agent può raggiungerlo, quindi arrivarci è un bug del tuo codice, non un errore commesso dal modello. Il fallimento che il tool può incontrare da solo — una piattaforma che non espone il carico medio — lo *restituisce*, con `ToolOutput::error()`, e il modello legge anche quello. La Sezione 5.11 trasforma la distinzione fra restituire e lanciare in una regola.

### Quando inline è la scelta giusta

**Usalo per:** prototipi, script una tantum, tool che davvero non hanno riuso, dimostrazioni didattiche.

**Non usarlo per:** qualunque cosa richieda una dipendenza, qualunque cosa testerai, qualunque cosa compaia in più di un agent, qualunque cosa più lunga di una decina di righe.

Una classe anonima non cattura variabili dallo scope circostante: una dipendenza va passata attraverso un costruttore che scrivi apposta, e a quel punto la classe si è guadagnata un nome. Non può essere mockata né testata in isolamento, perché non c'è un nome di classe da istanziare, e non può essere riusata. La Sezione 5.3 risolve tutti e quattro i problemi.

### Punti chiave

- `Tool` è astratta; il tool più leggero è una classe anonima che la estende dentro `tools()`.
- L'identità sono le proprietà `$name` e `$description`; lo schema è `properties()`; la logica è `__invoke()`.
- I nomi delle proprietà devono corrispondere esattamente ai nomi dei parametri di `__invoke()` — gli argomenti vengono passati per nome.
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

La classe generata ha già le quattro parti che seguono, con valori segnaposto da sostituire.

### Le quattro parti di una classe tool

```php
<?php

namespace App\Neuron\Tools;

use NeuronAI\HttpClient\Curl\CurlHttpClient;
use NeuronAI\HttpClient\HttpClientInterface;
use NeuronAI\HttpClient\HttpRequest;
use NeuronAI\Tools\PropertyType;
use NeuronAI\Tools\Tool;
use NeuronAI\Tools\ToolProperty;

class GetTranscriptionTool extends Tool
{
    private const ENDPOINT = 'https://api.supadata.ai/v1/youtube/transcript';

    protected string $name = 'get_transcription';

    protected ?string $description = 'Retrieve the transcription of a youtube video.';

    protected HttpClientInterface $client;

    public function __construct(protected string $key, ?HttpClientInterface $client = null)
    {
        $this->client = $client ?? new CurlHttpClient(timeout: 10.0);
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
        $response = $this->client
            ->request(HttpRequest::get(
                self::ENDPOINT . '?url=' . \urlencode($video_url) . '&text=true',
                ['x-api-key' => $this->key],
            ))
            ->json();

        return (string) ($response['content'] ?? '');
    }
}
```

**1. Identità** — le proprietà `$name` e `$description`. Sono valori predefiniti di proprietà della classe, non argomenti del costruttore, quindi l'identità è fissata dalla classe e non c'è alcun costruttore padre da chiamare.

**2. Il costruttore** — appartiene interamente alle tue dipendenze. Qui sono una chiave API e un client HTTP; in un'applicazione reale potrebbero essere un repository, una connessione PDO, un mailer.

**3. `properties()`** — lo schema, gli stessi oggetti della versione inline.

**4. `__invoke()`** — l'implementazione. Il metodo magico di PHP, così l'oggetto tool è invocabile. I nomi dei parametri devono corrispondere ai nomi delle proprietà, esattamente come nella Sezione 5.2.

Il secondo argomento del costruttore è opzionale, ed è il punto di aggancio che rende la classe testabile. Omettilo e il tool costruisce il `CurlHttpClient` di NeuronAI — il client che ogni provider e ogni toolkit del framework usa per impostazione predefinita, quindi al tool non serve nulla oltre a `ext-curl`: niente Guzzle, nessun pacchetto Composer in più. Passane uno e il tool usa il tuo, senza toccarlo: la richiesta porta con sé l'URL completo e il proprio header, quindi va bene qualunque `HttpClientInterface`. I toolkit HTTP del framework accettano lo stesso argomento opzionale per lo stesso motivo. Anche il `timeout:` esplicito è voluto: il valore predefinito del client è di cinque minuti, molto più di quanto chiunque dovrebbe aspettare una singola tool call.

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

**Prende dipendenze.** Una classe riceve una connessione PDO, un repository, un mailer — dal costruttore, dal tuo container di DI. E può tenerle senza cerimonie: poiché nei messaggi e nello stato persistito viaggiano solo dati `ToolCall`, un oggetto tool non viene mai serializzato, quindi una connessione attiva o un client HTTP al suo interno funziona con qualunque backend di persistenza. Una cosa da sapere sul suo ciclo di vita: l'istanza che colleghi è un prototipo, e il framework ne esegue un clone nuovo per ogni chiamata. I cloni condividono i servizi che hai iniettato; tutto ciò che una chiamata scrive nelle proprietà del tool sparisce insieme al suo clone.

**È testabile con test unitari senza un LLM.** È l'argomento che conta di più:

```php
public function test_it_returns_the_transcript(): void
{
    $client = $this->createStub(HttpClientInterface::class);
    $client->method('request')->willReturn(
        new HttpResponse(200, '{"content": "Welcome back to the channel."}')
    );

    $tool = new GetTranscriptionTool('fake-key', $client);

    $result = $tool('https://youtube.com/watch?v=xyz');

    $this->assertStringContainsString('Welcome back', $result);
}
```

Il tool è un oggetto invocabile. Lo invochi direttamente, senza agent, senza provider, senza chiamate a un modello — e, poiché il test gli passa un client stub, nemmeno al servizio di trascrizione. Visto il problema del non determinismo della Sezione 1.5, avere gran parte del tuo sistema agentico fatta di normale PHP testabile è una vittoria significativa — e il confine fra "testabile" e "non testabile" corre esattamente lungo questa classe.

Una chiamata diretta salta il passaggio di binding descritto nella Sezione 5.5. Per testare anche quello — i cast, gli argomenti obbligatori — pilota il tool come fa il framework: `$tool->setInputs([...])->execute()`, poi leggi `$tool->getResult()`.

**È riusabile e distribuibile.** I tool implementano `ToolInterface`. Un tool ben costruito può essere pubblicato come pacchetto Composer o contribuito a monte al framework.

**Ha un nome vero.** `GetTranscriptionTool` compare negli stack trace, nel tuo container di DI, nella navigazione del tuo IDE. Una classe anonima compare come `NeuronAI\Tools\Tool@anonymous`.

::: {.callout .callout-tip}
[In pratica]{.callout-title}

Prendi il tool inline `get_server_load` della Sezione 5.2 e convertilo in una classe, poi scrivi un test PHPUnit. Ci vogliono cinque minuti, e rende l'argomento della testabilità molto più efficace di quanto faccia leggerlo.
:::

### Punti chiave

- Proprietà `$name` / `$description` per l'identità, il costruttore solo per le dipendenze, `properties()` per lo schema, `__invoke()` per la logica.
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
protected string $name = 'get_weather';

protected ?string $description = 'Gets the weather.';
```

**Buona:**

```php
protected string $name = 'get_current_weather';

protected ?string $description = 'Returns current weather conditions for a location: temperature in Celsius, '
    . 'wind speed, and a condition code. Use this whenever the user asks about '
    . 'current weather, temperature, or conditions anywhere. Requires latitude '
    . 'and longitude — derive them yourself from the place name. Never invent '
    . 'weather data; always call this tool.';
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

`PropertyType` è un enum con sei casi: `STRING`, `INTEGER`, `NUMBER`, `BOOLEAN`, `ARRAY` e `OBJECT`. I primi quattro sono quelli che usi con `ToolProperty`; array e oggetti hanno le loro classi di proprietà, più avanti. `ToolProperty` accetta anche un array `enum:` quando un valore può essere solo uno fra pochi, come ha fatto `get_server_load` nella Sezione 5.2: l'elenco entra nello schema, e il binding lo fa rispettare.

Due argomenti da distinguere:

- **`required`** — il modello deve fornire affatto questa proprietà?
- **`nullable`** — il valore fornito può essere null?

Non sono la stessa cosa, e confonderli produce schemi che ammettono input che non intendevi. Una proprietà obbligatoria ma nullable deve essere presente e può essere null; una proprietà opzionale può essere del tutto assente.

### Che cosa arriva a `__invoke()`: il binding è un cast

Il tipo che dichiari non è solo schema. Prima che `__invoke()` venga eseguito, NeuronAI passa ogni argomento inviato dal modello attraverso il `cast()` della sua proprietà, e il tuo metodo riceve il valore convertito.

Questo conta perché i modelli sono approssimativi con i tipi JSON. Chiedi un `NUMBER` e riceverai regolarmente `"45.07"` — una stringa. Chiedi un `BOOLEAN` e potresti ricevere `"true"`. Il cast converte ciò che convertirebbe la modalità coercitiva di PHP: `"45.07"` diventa `45.07`, `"5"` diventa `5` per un `INTEGER`, `"true"` diventa `true`, e gli elementi di un array passano attraverso la proprietà `items` dell'array. Quindi un semplice `float $latitude` nella firma è sicuro; non serve allargarlo a `float|int|string` e fare il cast a mano.

Ciò che non si può convertire non arriva mai al tuo codice. Se il modello invia `"north"` per un `NUMBER`, `__invoke()` non viene chiamato affatto: il risultato del tool diventa un errore che il modello può leggere — `Parameter "latitude" must be of type number, string given.` — e il ciclo continua, così il modello può correggere la propria chiamata. Un argomento obbligatorio che il modello omette si risolve allo stesso modo — `Parameter "latitude" is required.` — e così un valore fuori dall'`enum:` di una proprietà. Sono tutti e tre errori del modello da correggere, non bug della tua applicazione: non viene lanciato nulla, e l'handler degli errori della Sezione 5.11 non entra mai in gioco.

Gli stessi valori tipizzati alimentano tutto il resto che giudica la chiamata — le approval policy della Sezione 5.10 e il conteggio delle esecuzioni della Sezione 5.9 — quindi una policy che confronta `amount > 100` non può essere aggirata dal modello che scrive il numero come stringa.

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

Sappi però dove viene applicato. `minItems` e `maxItems` finiscono nello JSON Schema che il modello riceve, e modelli e provider in genere li rispettano — ma il binding di NeuronAI converte gli elementi senza contarli. Se undici elementi farebbero danni reali, controlla `count()` in `__invoke()` e restituisci un errore su cui il modello possa agire.

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

Scrivi un tool `compare_cities` che prende un `ArrayProperty` di nomi di città con `minItems: 2, maxItems: 5` e restituisce un confronto. Poi chiedi all'agent di confrontare otto città. Osserva se il modello rispetta il vincolo e come reagisce all'essere vincolato. Poi aggiungi in `__invoke()` un controllo con `count()` che restituisce `ToolOutput::error()`, e guarda che cosa fa il modello con il feedback.

### Punti chiave

- Tre classi: `ToolProperty`, `ArrayProperty`, `ObjectProperty`.
- `required` e `nullable` sono domande diverse.
- Il binding è un cast: `__invoke()` riceve valori tipizzati, e un argomento mancante, fuori dal suo `enum:` o impossibile da convertire torna al modello come errore invece di raggiungere il tuo codice.
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
    protected string $name = 'my_tool';

    protected ?string $description = 'Describe what the tool does and when to use it.';

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

Nota la firma: `__invoke(Color $color)`. Non un array. Un oggetto tipizzato, con completamento nell'IDE, analisi statica e supporto al refactoring. È la regola del binding come cast della Sezione 5.5 applicata agli oggetti: l'`ObjectProperty` deserializza il JSON del modello nella tua classe prima della chiamata.

### Perché è il default che vale la pena adottare

**Schema e tipo non possono divergere.** Aggiungi un campo al DTO e lo schema si aggiorna. Non c'è un secondo posto da ricordarsi di modificare — che è il modo in cui falliscono gli schemi scritti a mano in una base di codice con più di un contributore.

**L'analisi statica torna a funzionare.** PHPStan o Psalm vedono `$color->r`. Con input a forma di array vedono `mixed`, e i corpi dei tuoi tool diventano un punto cieco per l'analisi.

**Il DTO è riusabile.** La stessa classe annotata funziona per lo structured *output* (Capitolo 6). Una classe `Order` può definire che cosa il modello deve produrre e che cosa un tool accetta — lo stesso contratto in entrambe le direzioni.

**`#[SchemaProperty]` supporta vincoli di validazione.** Oltre a `title`, `description` e `required`, l'attributo accetta `min` e `max`, `minLength` e `maxLength`, e `anyOf`. Spingi la validazione dentro lo schema, così il modello riceve le regole invece che il tuo tool scopra le violazioni a runtime.

::: {.callout .callout-warning}
[Nota sul namespace]{.callout-title}

`SchemaProperty` sta sotto `NeuronAI\StructuredOutput\`, non sotto `NeuronAI\Tools\`. Non è un caso: è lo stesso meccanismo che usa il sistema di structured output, ed è esattamente il motivo per cui il DTO è riusabile in entrambi. La documentazione a volte lo scrive come `NeuronAI\StructuredOutput\Property`, che non esiste.
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

Un agent che ha bisogno di matematica ha bisogno di più di un tool: qualcosa che valuti una formula, aritmetica intera esatta per fattoriali, combinazioni e numeri primi, e statistica — media, mediana, moda, varianza, deviazione standard. Dichiarare quattordici tool singolarmente in ogni agent è rumore.

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

Una riga, quattordici tool.

### Di che cosa è fatto un toolkit

```php
namespace NeuronAI\Tools\Toolkits\Calculator;

use NeuronAI\Tools\Toolkits\AbstractToolkit;

class CalculatorToolkit extends AbstractToolkit
{
    public function guidelines(): ?string
    {
        return <<<TEXT
            This toolkit performs mathematical calculations with precision and determinism.
            For arithmetic, algebra, trigonometry, logarithms or any formula, write the whole expression
            and pass it to the evaluate tool in a single call instead of computing intermediate steps
            yourself; it works in double precision, about 15 significant digits. Use the integer tools
            (factorial, combinations, permutations, gcd, lcm, mod_pow, is_prime, prime_factors) when an
            exact result with large integers is required, and the statistics tools for datasets.
            TEXT;
    }

    public function provide(): array
    {
        return [
            EvaluateTool::make(),
            FactorialTool::make(),
            CombinationsTool::make(),
            PermutationsTool::make(),
            GcdTool::make(),
            LcmTool::make(),
            ModPowTool::make(),
            IsPrimeTool::make(),
            PrimeFactorsTool::make(),
            MeanTool::make(),
            MedianTool::make(),
            ModeTool::make(),
            VarianceTool::make(),
            StandardDeviationTool::make(),
        ];
    }
}
```

Due metodi su `AbstractToolkit`.

**`provide()`** restituisce i tool. Una volta collegati, si comportano esattamente come se fossero dichiarati singolarmente.

**`guidelines()` è quello interessante.** Dà al modello informazioni contestuali su come i tool funzionano *insieme*, cosa che nessuna descrizione di singolo tool può trasmettere. NeuronAI aggiunge al system prompt le guidelines di ogni toolkit collegato, dentro un blocco `<TOOLS-GUIDELINES>`, sotto un'intestazione che elenca i nomi dei tool di quel toolkit.

Guarda che cosa dicono davvero le guidelines della calcolatrice: scrivi l'intera espressione e passala a `evaluate` in una sola chiamata, invece di calcolare tu i passaggi intermedi. Quella singola frase cambia il comportamento. I modelli linguistici sono inaffidabili con l'aritmetica, e lo sono altrettanto nel copiare un lungo risultato intermedio da una tool call alla successiva. Senza la guideline, un modello davanti a un calcolo in più parti o tenta di farlo a mente o concatena una dozzina di piccole chiamate, trascrivendo numeri in virgola mobile dall'una all'altra. Con essa, il modello scrive `(19.3 + 18.6) / 2` una volta sola e un parser deterministico lo calcola.

**Questo è il punto da mettere in evidenza:** la descrizione di un singolo tool dice *che cosa fa questo tool*. Le guidelines dicono *come combinare questi tool in una strategia*. Se costruisci un tuo toolkit, le guidelines sono dove va la strategia, e saltarle spreca gran parte del meccanismo.

::: {.callout .callout-warning}
[La calcolatrice richiede bcmath]{.callout-title}

I tool per l'aritmetica intera esatta calcolano con l'estensione `bcmath` e si rifiutano di essere costruiti senza. Poiché `provide()` istanzia ogni tool, `CalculatorToolkit::make()` fallisce all'avvio dell'agent su una build di PHP senza `ext-bcmath` — anche se volevi solo `evaluate`. Abilita l'estensione ovunque giri l'agent, oppure collega singolarmente `EvaluateTool::make()` e i tool statistici.
:::

### Il catalogo integrato

| Toolkit | Capacità | Richiede |
|---|---|---|
| **Calculator** | 14 tool: valutazione di espressioni, matematica intera esatta (fattoriale, combinazioni, MCD, numeri primi…), media, mediana, moda, varianza, deviazione standard | `ext-bcmath` |
| **Calendar** | 18 tool: ora corrente, formattazione, differenze, conversione fuso orario, giorno della settimana, anno bisestile, periodi | — |
| **MySQL / PGSQL** | Introspezione dello schema, SELECT, operazioni di scrittura | PDO |
| **FileSystem** | leggi, grep, glob, parse — e scrivi, modifica, elimina, e una shell bash | directory di ambito opzionale |
| **Tavily** | ricerca web, estrazione pagine, crawl di siti | Chiave API |
| **Jina** | ricerca web, lettore di URL | Chiave API |
| **TodoPlanning** | un solo tool, `write_todos`: un elenco di attività che il modello tiene e aggiorna mentre porta avanti un lavoro in più passaggi | — |

Altri tre sono inclusi nella 4.0.3 ma marcati `@deprecated`, e saranno rimossi nella prossima major: il toolkit Supadata YouTube, il toolkit Zep per la memoria a lungo termine e `SESTool`, un singolo tool per inviare email tramite AWS SES. Non costruirci sopra.

Rileggi due volte la riga FileSystem. Il toolkit non è in sola lettura: collegato per intero, dà al modello la possibilità di sovrascrivere, eliminare ed eseguire comandi di shell. La sua directory di ambito opzionale (`FileSystemToolkit::make('/path/to/docs')`) confina i tool sui file in un solo albero, ma la shell viene solo avviata lì, non confinata. La Sezione 5.8 mostra come tenere solo i tool che intendi davvero offrire.

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
- `MySQLSelectTool` — legge i dati: un'istruzione per chiamata, eseguita dentro una transazione `READ ONLY` di cui il tool fa sempre il rollback
- `MySQLWriteTool` — INSERT, UPDATE, DELETE

Il consiglio della documentazione stessa vale la pena citarlo: se non sei sicuro del comportamento del tuo agent, puoi semplicemente non fornire il tool di scrittura. Collegare solo i tool di lettura è una mitigazione completa ed efficace, non un compromesso.

Secondo controllo: `MySQLSchemaTool` prende un elenco opzionale di tabelle.

```php
MySQLSchemaTool::make(
    new \PDO($dsn, $user, $password),
    ['users', 'categories', 'articles', 'tags']
)
```

Questo limita ciò che viene mostrato al modello, non ciò che la connessione può leggere. A un agent di contenuti si parla di articoli, categorie e tag; a un agent di amministrazione utenti, di utenti, ruoli e permessi; a nessuno dei due viene detto che esiste una tabella dei pagamenti. Ma una tabella che al modello non è mai stata mostrata resta una tabella che può nominare in una query: tratta quindi l'elenco come un modo per tenere l'agent concentrato e l'output dello schema breve, non come un controllo di accesso.

Terzo controllo, e quello da enfatizzare di più: **l'istanza PDO è una connessione, quindi dai all'agent una connessione sua, con credenziali di database sue.** Un utente MySQL in sola lettura costa una sola istruzione `GRANT` e impone a livello di database ciò che la tua selezione di tool impone a livello applicativo. Difesa in profondità, e l'unico livello con cui un prompt non può discutere. Conta anche che la connessione sia dedicata: il tool di lettura si rifiuta di girare su una connessione che è già dentro una transazione, perché il suo rollback butterebbe via il lavoro della tua applicazione.

### Punti chiave

- Un toolkit collega un insieme coerente di capacità in una riga.
- `guidelines()` trasmette la strategia trasversale ai tool: la parte che cambia il comportamento.
- I toolkit di database separano lettura e scrittura di proposito; omettere il tool di scrittura è un progetto valido.
- Un elenco di tabelle sul tool di schema restringe ciò che viene mostrato al modello, non ciò che può leggere; il controllo di accesso sono le credenziali in sola lettura dell'agent.

## 5.8 Filtri sui toolkit: exclude, only, with

### Perché filtrare non è un vezzo

Un toolkit è un insieme coerente, ma "coerente" non è lo stesso di "appropriato per questo agent". Tre costi concreti del collegarne più del necessario:

**Token.** Nome, descrizione e schema dei parametri di ogni tool vengono trasmessi a **ogni** iterazione del ciclo. Il solo toolkit Calendar è di diciotto tool. A cinque iterazioni hai pagato quello schema cinque volte.

**Errori di tool sbagliato.** L'accuratezza della selezione degrada man mano che il catalogo cresce. Quattordici tool matematici dove ne bastavano due significa dodici occasioni in più di sceglierne uno sbagliato.

**Raggio d'azione.** Ogni tool collegato è raggiungibile da qualunque utente possa parlare con l'agent. È il modello di sicurezza della Sezione 5.1, applicato agli import di comodo.

### exclude()

Collega il toolkit, rimuovi tool specifici:

```php
class DocsAgent extends Agent
{
    protected function tools(): array
    {
        return [
            FileSystemToolkit::make('/srv/docs')->exclude([
                WriteFileTool::class,
                EditFileTool::class,
                DeleteFileTool::class,
                BashTool::class,
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

`exclude()` è una lista di negazione, e le liste di negazione marciscono. Quando il framework aggiunge tool a un toolkit in un nuovo rilascio, il tuo elenco `exclude()` non ne sa nulla — e il tuo agent acquisisce silenziosamente capacità che non hai mai revisionato.

Non è un'ipotesi. Il toolkit FileSystem un tempo offriva solo lettura, ricerca e parsing; ora include anche tool di scrittura, modifica, eliminazione e bash. Un agent scritto come `FileSystemToolkit::make()->exclude([ParseFileTool::class])` sul toolkit precedente, e aggiornato senza una revisione, si è ritrovato con una shell.

`only()` è una lista di permessi. Nuovi tool compaiono nel toolkit e il tuo agent non li riceve finché non lo dici tu. È il default corretto per qualunque cosa tocchi dati o effetti collaterali. Il `DocsAgent` qui sopra è scritto meglio così:

```php
FileSystemToolkit::make('/srv/docs')->only([
    ReadFileTool::class,
    GrepFileContentTool::class,
    GlobPathTool::class,
]),
```

Usa `exclude()` quando vuoi davvero ampiezza e stai potando problemi noti. Usa `only()` in tutti gli altri casi, e specialmente nella Parte V quando i tool arrivano al tuo database.

### with()

Recupera un tool specifico dal toolkit e riconfiguralo:

```php
protected function tools(): array
{
    return [
        MySQLToolkit::make($this->pdo)
            ->with(
                MySQLSchemaTool::class,
                fn (ToolInterface $tool): ToolInterface => $tool->setMaxRuns(1)
            ),
    ];
}
```

Passa il nome della classe e una callback. L'istanza del tool viene iniettata, ne cambi le impostazioni, la restituisci.

Il tool di schema è l'esempio naturale: a un agent serve ispezionare lo schema una volta sola. Limitarlo a una singola esecuzione impedisce a un modello confuso di rileggere l'intera struttura cinque volte, cosa lenta e costosa dato che l'output dello schema è verboso.

`with()` è anche il punto in cui va l'approvazione per singolo tool quando il tool viene da un toolkit — `fn (Tool $tool): ToolInterface => $tool->requireApproval()` su `MySQLWriteTool`, per esempio. Lì il parametro è tipizzato `Tool` perché i metodi di approvazione sono dichiarati sulla classe base, non su `ToolInterface`. La Sezione 5.10 tratta l'approvazione.

::: {.callout .callout-warning}
[Il metodo è setMaxRuns()]{.callout-title}

L'esempio di `with()` nella documentazione chiama `setMaxTries(1)` e non passa al toolkit alcuna connessione PDO. Nessuna delle due cose funziona: `setMaxTries()` non esiste — il setter a livello di tool è `setMaxRuns()` e quello a livello di agent è `toolMaxRuns()` — e `MySQLToolkit` richiede il suo PDO.
:::

### Combinare i filtri

I metodi si concatenano:

```php
CalculatorToolkit::make()
    ->only([EvaluateTool::class, MeanTool::class])
    ->with(EvaluateTool::class, fn (ToolInterface $tool): ToolInterface => $tool->setMaxRuns(3));
```

Due tool, uno dei quali limitato. Leggilo dall'alto in basso: seleziona, poi configura.

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

NeuronAI conta quante volte ogni tool viene invocato durante una run dell'agent — un turno di `chat()`, comprese eventuali pause per l'approvazione umana nel mezzo. Supera il limite e il nodo dei tool lancia `ToolRunsExceededException`. **Il default è 10 chiamate, contate per singolo tool.**

Quel dettaglio "per singolo tool" conta. Cinque tool al limite di default significano fino a cinquanta esecuzioni di tool in una sola chiamata a `chat()` prima che qualcosa si fermi.

### Impostarlo

```php
use NeuronAI\Exceptions\ToolRunsExceededException;

try {
    $message = YouTubeAgent::make()
        ->setThreadId('demo')
        ->toolMaxRuns(5) // Max number of calls for each tool
        ->addTool(
            // Tool level config takes precedence over the global setting
            CustomTool::make()->setMaxRuns(2)
        )
        ->chat(...)
        ->getMessage();

} catch (ToolRunsExceededException $exception) {
    // do something
}
```

Due livelli:

- **`toolMaxRuns(n)`** sull'agent — il default per ogni tool.
- **`setMaxRuns(n)`** su un tool — sovrascrive l'impostazione dell'agent per quel tool.

**Vince il livello del tool.** Quella precedenza è ciò che vuoi: un default globale permissivo con limiti stretti sui tool lenti, costosi o pericolosi.

::: {.callout .callout-warning}
[Intercetta la classe di eccezione giusta]{.callout-title}

La documentazione ha chiamato l'eccezione in due modi: `ToolRunsExceededException` nella prosa, `ToolMaxTriesException` in un esempio di blocco catch. Esiste solo la prima — `NeuronAI\Exceptions\ToolRunsExceededException`. Merita attenzione: PHP non si lamenta di un `catch` che nomina una classe inesistente, semplicemente non corrisponde mai. Un nome di classe sbagliato produce una non-gestione silenziosa invece di un errore evidente, che è il peggior tipo di bug da ereditare.
:::

### Che cosa conta come "lo stesso tool"

Il contatore è indicizzato per *run key* del tool, che per default è il suo nome: ogni chiamata a `get_current_weather` consuma lo stesso budget, quali che siano le coordinate. Per la maggior parte dei tool è giusto, ma non permette di distinguere un modello che controlla legittimamente cinque città da uno che chiede la stessa città cinque volte.

Quando gli argomenti contano, aggiungi il trait `TrackByInputs` alla classe del tool:

```php
use NeuronAI\Tools\Tool;
use NeuronAI\Tools\TrackByInputs;

class WeatherTool extends Tool
{
    use TrackByInputs;

    // ...
}
```

La run key diventa il nome del tool più un hash degli input, quindi `setMaxRuns(1)` ora significa "al massimo una volta *per insieme di argomenti*": cinque città diverse passano, la stessa città due volte no. Per qualunque cosa più sottile — contano solo alcuni parametri — sovrascrivi tu `getRunKey()`.

Altri due dettagli del conteggio. Una chiamata *rifiutata* da un essere umano non consuma alcuno slot. E il conteggio sopravvive alle interruzioni: una pausa per l'approvazione nel mezzo di una run non lo azzera.

### Scegliere i valori

| Carattere del tool | Limite suggerito | Motivo |
|---|---|---|
| Introspezione dello schema | 1 | Si legge una volta; la risposta non cambia a metà esecuzione |
| API esterna costosa | 2–3 | Ogni chiamata costa denaro o quota |
| Calcolo locale economico | 5–10 | Ha davvero bisogno di ripetizione per la matematica multi-passo |
| Operazioni di scrittura | 1 | Due scritture identiche sono quasi sempre un bug |

L'ultima riga è quella importante, e conviene essere precisi su che cosa garantisce. Il limite vale dentro una singola run: un modello che chiama il tool di scrittura una seconda volta nello stesso turno ottiene una `ToolRunsExceededException` invece di un secondo addebito. Non vale da un turno all'altro. Il contatore riparte con il `chat()` successivo, quindi un utente che risponde "riprova" ottiene una seconda scrittura. Ciò che rende sicuro ripetere una scrittura è una chiave di idempotenza: ricavala dall'operazione stessa — il numero d'ordine, il payment intent — e fai in modo che il codice che esegue la scrittura rifiuti un duplicato. Imposta il limite deliberatamente, e costruisci anche la guardia; la Sezione 19.2 lo fa.

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
use NeuronAI\Exceptions\ToolRunsExceededException;

try {
    $answer = $agent->chat(new UserMessage($input))->getMessage()?->getContent();
} catch (ToolRunsExceededException $e) {
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

- Il default è 10 esecuzioni, per tool, per run dell'agent; superarlo lancia `ToolRunsExceededException`.
- `toolMaxRuns()` imposta il default dell'agent; `setMaxRuns()` su un tool lo sovrascrive.
- Le esecuzioni si contano per run key — per default il nome del tool; `TrackByInputs` conta per insieme di argomenti.
- I tool di scrittura vanno limitati a 1 — per run. Da un turno all'altro, solo una guardia di idempotenza impedisce una scrittura duplicata.
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
| Offerto, filtrato a runtime | `approvalPolicy()`, `requireApproval()` | Decisione umana |
| Offerto, verificato all'esecuzione | Controllo di policy dentro `__invoke()` | Il tuo PHP |
| Offerto, ristretto alla fonte | Grant di database, scope delle API | Infrastruttura |

Usane più d'uno. `visible()` è la tua prima linea, non l'unica: un bug nell'espressione di visibilità non dovrebbe essere l'unica cosa fra un utente e un rimborso.

### Visibilità e approvazione

La documentazione traccia bene questa distinzione e vale la pena riprodurla con precisione:

- La **visibilità** è una decisione di *build time*. Il tool è incluso nello schema oppure no. Deciso prima che il modello veda qualunque cosa.
- L'**approvazione** è un guardiano di *runtime*. Il tool viene offerto, il modello lo richiede, e il framework intercetta la chiamata e si ferma per una decisione umana.

L'approvazione si esprime sul tool stesso, e può essere condizionale rispetto agli argomenti:

```php
BuyTicketTool::make()->withApprovalPolicy(
    fn (ToolInterface $tool): bool|string => $tool->getInput('amount') > 100
        ? 'Purchases above 100 need a human sign-off'
        : false
)
```

I piccoli acquisti passano; quelli grandi aspettano un essere umano. È un prodotto molto migliore sia di "consenti sempre" sia di "blocca sempre". Costruiamo il flusso human-in-the-loop completo nel Capitolo 15 e lo colleghiamo a una vera interfaccia nel Capitolo 22; il resto di questa sezione copre ciò che spetta al tool e all'agent, perché la distinzione si fissi mentre la visibilità è fresca.

### L'approvazione vive sul tool

Prima di ogni tool call, il nodo dei tool dell'agent pone al tool una sola domanda: *questa chiamata richiede approvazione?* Il tool risponde con gli argomenti della chiamata già associati — e convertiti, come descritto nella Sezione 5.5. Non c'è alcun middleware da registrare né alcun interruttore a livello di agent; un tool che non chiede mai approvazione non viene mai fermato.

La risposta viene da due punti.

**Chi scrive il tool dichiara il rischio intrinseco del tool** sovrascrivendo `approvalPolicy()`. Il default restituisce `false`. Restituisci `true` per sottoporre il tool ad approvazione — oppure restituisci una stringa, che vale come `true` e fa anche da motivazione mostrata a chi approva:

```php
class TransferMoneyTool extends Tool
{
    protected string $name = 'transfer_money';

    protected ?string $description = 'Transfers money between two accounts of the current customer.';

    protected function approvalPolicy(): bool|string
    {
        return ($this->inputs['amount'] ?? 0) > 100
            ? 'Transfers above $100 require a human sign-off'
            : false;
    }

    // properties(), __invoke() ...
}
```

È il posto giusto per un rischio che è una proprietà del tool: un trasferimento è pericoloso in ogni agent che lo collegherà mai, quindi il tool lo dice una volta per tutte.

::: {.callout .callout-warning}
[approvalPolicy() non accetta argomenti]{.callout-title}

La documentazione mostra `approvalPolicy(array $inputs)`. Il metodo non accetta parametri: gli input sono già associati al tool, quindi leggili da `$this->inputs` o con `$this->getInput('amount')`. Copiare la firma documentata è un errore fatale — PHP rifiuta un override la cui firma è incompatibile con quella del genitore.
:::

**Chi sviluppa l'agent la sovrascrive al momento del collegamento**, in entrambe le direzioni:

```php
protected function tools(): array
{
    return [
        DeleteFileTool::make()->requireApproval(),
        TransferMoneyTool::make()->suppressApproval(),
        BuyTicketTool::make()->withApprovalPolicy(
            fn (ToolInterface $tool): bool|string => $tool->getInput('amount') > 100
                ? 'Purchases above 100 need a human sign-off'
                : false
        ),
    ];
}
```

`requireApproval()` sottopone ad approvazione ogni chiamata. `suppressApproval()` annulla una policy dichiarata dal tool — per un agent batch interno, per esempio, dove non c'è un essere umano disponibile e il rischio è gestito altrove. `withApprovalPolicy()` sostituisce la policy dichiarata con una tua callback, che riceve il tool con gli input della chiamata già associati. Se ne configuri più d'uno, vince l'ultimo override. I tool che provengono da un toolkit ricevono lo stesso trattamento tramite `with()`, dalla Sezione 5.8.

### Che cosa vede il chiamante

Quando arriva una chiamata sottoposta ad approvazione, `chat()` non lancia eccezioni e non aspetta. Restituisce uno stato *interrotto*:

```php
$agent = ShopAgent::make(workflowId: $threadId);

$state = $agent->chat(new UserMessage('Buy two tickets for Saturday'));

if ($state->isInterrupted()) {
    foreach ($agent->pendingApprovals() as $action) {
        // $action->id      the tool call ID to decide on
        // $action->name    the tool name
        // $action->reason  why the tool asked, from its policy
        // $action->inputs  the typed arguments
    }
}
```

`isInterrupted()` è il controllo da usare. Uno stato in pausa ha comunque un messaggio — `getMessage()` restituisce il messaggio di tool call del modello, non una risposta — quindi un controllo su null non ti direbbe nulla. `pendingApprovals()` restituisce un `Action` per ogni chiamata ancora in attesa di una decisione — quanto basta per disegnare una schermata di approvazione. Una decisione torna indicizzata per ID di chiamata, e `run()` prosegue la stessa run:

```php
$state = ShopAgent::make(workflowId: $threadId)
    ->submitApprovalDecisions([
        'call_123' => 'approve',
        'call_456' => ['reject', 'Too expensive, ask the user for a cheaper option'],
    ])
    ->run();
```

Tre regole rendono tutto ciò sicuro. **Un tool viene eseguito solo se è esplicitamente approvato** — il silenzio non è mai consenso, e un payload che lascia una chiamata senza decisione sospende di nuovo la run. **Un rifiuto non è un errore**: il modello riceve un risultato del tool che dice che l'azione non è stata eseguita, insieme alla tua motivazione, e prosegue con quell'informazione. E **le chiamate che non richiedevano approvazione vengono comunque eseguite** — nell'esempio, un acquisto economico richiesto nello stesso turno viene eseguito una volta decisa l'intera tornata.

Finché la decisione è in sospeso, il thread appartiene alla run in pausa: un nuovo `chat()` su quel thread lancia `RunInFlightException` invece di avviare una seconda run accanto alla prima.

Fra due richieste HTTP — l'endpoint di chat, poi quello di approvazione — il thread ID è tutto ciò che la seconda richiesta deve portare con sé: la run in pausa si ritrova tramite quello. Perché funzioni, l'agent ha bisogno di un backend di persistenza del workflow e di un message store durevole (Sezione 4.3), così il secondo processo può caricare ciò che il primo ha salvato. Il Capitolo 15 imposta tutto questo.

### Il pattern da adottare

Calcola la visibilità dall'attore, non da un globale:

```php
class OrderAgent extends Agent
{
    public function __construct(
        private User $user,
        private OrderRepository $orders,
        private RefundService $refunds,
    ) {
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

Un costruttore tuo cambia una cosa nel modo di costruire l'agent: il thread ID non è più il suo primo argomento, quindi la conversazione va associata dopo. `::make()` continua a inoltrare tutto ciò che il costruttore accetta — `OrderAgent::make($user, $orders, $refunds)->setThreadId($threadId)`. Quando invece è un container a costruire l'agent, `->for($threadId)` restituisce una copia associata al thread; la Parte V usa quella forma.

### Esercizio

Aggiungi al tuo agent dimostrativo un tool `delete_cache`, visibile solo quando `APP_ROLE=admin`. Esegui l'agent come non amministratore e chiedigli direttamente: "cancella la cache". Poi chiedi: "quali tool hai?". Verifica che il tool sia assente sia dal comportamento sia dalla risposta.

### Punti chiave

- `visible(false)` rimuove del tutto il tool dallo schema.
- Nascondere batte istruire: le restrizioni basate sul prompt trapelano, sono probabilistiche e sono attaccabili.
- La visibilità è build time; l'approvazione è runtime. Esistono entrambe, per lavori diversi.
- L'approvazione vive sul tool: `approvalPolicy()` la dichiara, `requireApproval()` / `suppressApproval()` / `withApprovalPolicy()` la sovrascrivono al momento del collegamento.
- Una chiamata sottoposta ad approvazione restituisce uno stato interrotto; `pendingApprovals()` elenca che cosa decidere, `submitApprovalDecisions([...])->run()` prosegue. Solo l'approvazione esplicita esegue un tool.
- Deriva la visibilità dall'attore, iniettato nel costruttore dell'agent.

## 5.11 Gestione degli errori dei tool

### Il default

Un tool può finire in due modi: restituisce un valore o lancia un'eccezione. NeuronAI tratta i due casi in modo diverso, di proposito, e la divisione cade sul confine naturale del linguaggio.

**Un valore restituito è un esito della conversazione.** Qualunque cosa restituisca `__invoke()` diventa il risultato del tool che il modello vede, e il ciclo continua.

**Un'eccezione sfuggita è un bug.** Si propaga attraverso `chat()` fino alla tua applicazione e interrompe la run. La cronologia della conversazione resta coerente — la tool call lasciata a metà non viene mai registrata — ma il turno è finito.

È un default ragionevole — un fallimento silenzioso sarebbe peggio — ma significa che la decisione spetta a te, tool per tool: quali fallimenti fanno parte della conversazione, e quali sono difetti?

### L'alternativa: dirlo al modello

È l'idea che vale l'intera sezione. Un fallimento su cui il modello può fare qualcosa non dovrebbe far cadere la run; dovrebbe essere restituito al modello come risultato del tool.

Il modello decide poi che cosa fare: riprovare con argomenti diversi, provare un altro tool, o dire all'utente che il dato non è disponibile. Ottieni degrado elegante senza scrivere logica di recupero, perché la logica di recupero è il modello.

Il modo principale per farlo è **restituire** il fallimento, con `ToolOutput::error()`:

```php
use NeuronAI\Tools\ToolOutput;

public function __invoke(string $order_id): string|ToolOutput
{
    $order = $this->orders->find($order_id);

    if ($order === null) {
        return ToolOutput::error(
            "No order matches \"{$order_id}\". Check the number with the user before trying again."
        );
    }

    return \json_encode([
        'id'     => $order->id,
        'status' => $order->status,
        'eta'    => $order->eta,
    ], \JSON_THROW_ON_ERROR);
}
```

Il testo dell'errore diventa il risultato che il modello legge, contrassegnato come fallimento. I provider con un flag di errore nativo sui risultati dei tool — Anthropic, Bedrock — lo ricevono come tale; gli altri ricevono il testo. Intercetta le tue eccezioni al confine del tool e converti in questo modo quelle recuperabili, in modo visibile, nel codice che sa che cosa è andato storto. I tool integrati di NeuronAI seguono la stessa convenzione: una divisione per zero nell'`evaluate` della calcolatrice restituisce `Division by zero at position 2` come risultato di errore, non come eccezione. E, come ha mostrato la Sezione 5.5, il framework lo fa già per te quando il modello invia un argomento del tipo sbagliato, ne omette uno obbligatorio o sceglie un valore fuori da un `enum:`.

Restano le eccezioni che non avevi previsto — da una libreria, un driver, un client di rete in profondità nella chiamata. Per quelle c'è un override a livello di agent: un **tool error handler**. Riceve ogni eccezione che sfugge a un tool. **Se l'handler restituisce un valore, quel valore viene restituito al modello come risultato del tool**, e il ciclo continua. Se restituisce `null`, declina, e l'eccezione si propaga come prima.

### Definizione fluente

```php
$agent = Agent::make()
    ->toolErrorHandler(
        fn (Throwable $e, ToolCall $call): ToolOutput => ToolOutput::error("Error: {$e->getMessage()}")
    );
```

### Dentro la classe agent

```php
class MyAgent extends Agent
{
    protected function resolveToolErrorHandler(): ?callable
    {
        return fn (Throwable $e, ToolCall $call): ToolOutput => ToolOutput::error("Error: {$e->getMessage()}");
    }
}
```

La callback riceve l'eccezione e la chiamata fallita — la `ToolCall` della Sezione 5.1, con il nome del tool e gli argomenti inviati dal modello. Contano entrambe: la chiamata ti permette di ramificare in base a quale tool ha fallito. Può restituire una stringa, un `ToolOutput` oppure `null`.

Tipizza il secondo parametro come `ToolCall`. La documentazione lo tipizza ancora come `ToolInterface`, e un handler scritto così fallisce con un `TypeError` esattamente nel momento sbagliato — la prima volta che un tool lancia un'eccezione.

### Scrivere un buon handler

La versione ingenua fa trapelare dettagli interni nella conversazione. Uno stack trace da 500 caratteri diventa contesto su cui il modello deve ragionare, ed eventualmente testo che un utente vede.

Scrivi handler che dicano al modello qualcosa di *azionabile*:

```php
protected function resolveToolErrorHandler(): ?callable
{
    return function (\Throwable $e, ToolCall $call): ?ToolOutput {
        $this->logger->error('Tool failure', [
            'tool'      => $call->getName(),
            'inputs'    => $call->getInputs(),
            'exception' => $e::class,
            'message'   => $e->getMessage(),
        ]);

        return match (true) {
            $e instanceof HttpException => ToolOutput::error(
                "The {$call->getName()} service is temporarily unreachable. "
                . "Do not retry more than once. If it fails again, tell the user "
                . "the data is unavailable right now."
            ),

            $e instanceof AuthorizationException => null,

            default => ToolOutput::error(
                "The {$call->getName()} tool failed. Tell the user you could not "
                . "complete this step, and do not retry."
            ),
        };
    };
}
```

Quattro principi visibili in quel codice:

**Logga tutto, di' poco al modello.** I tuoi log ricevono l'eccezione e gli argomenti. Il modello riceve una frase.

**Includi l'istruzione, non solo il fatto.** "Non riprovare più di una volta" sta facendo lavoro vero. Senza, un fallimento transitorio può bruciare il limite di esecuzioni della Sezione 5.9 in pochi secondi.

**Non far mai trapelare dettagli interni nella conversazione.** Stringhe di connessione, percorsi di file, hostname interni, credenziali nei messaggi d'eccezione: tutto finisce nella trascrizione, che può essere conservata, loggata e mostrata all'utente.

**Declina ciò che non va gestito.** Il ramo `null` restituisce il fallimento di permessi alla tua applicazione intatto. Ne parliamo più avanti.

### L'interazione con i max runs

L'handler degli errori intercetta anche l'eccezione del limite di esecuzioni. Ti dà un'uscita elegante al limite invece di un'eccezione al confine:

```php
$e instanceof ToolRunsExceededException => ToolOutput::error(
    "You have used this tool too many times. Stop calling it and answer with "
    . "what you already know, or tell the user you cannot complete the task."
),
```

Il modello riceve un chiaro segnale di stop e scrive un messaggio finale sensato. Molto meglio di un 500.

### Quando lasciarlo esplodere

Non tutto va gestito. Lancia l'eccezione dal tool — e restituisci `null` dall'handler per quell'eccezione — quando:

- Il fallimento indica un bug che devi vedere nel tuo error tracker
- Il fallimento è una violazione di permessi — non lasciare che il modello ci ragioni sopra: fallisci in modo netto e registralo
- Il fallimento lascerebbe i dati in uno stato incoerente

"Restituisci l'errore al modello" è un pattern di resilienza per fallimenti attesi e recuperabili. Non sostituisce la correttezza.

### Punti chiave

- Un valore restituito è un esito della conversazione; un'eccezione sfuggita è un bug che interrompe la run.
- Restituisci dal tool i fallimenti recuperabili con `ToolOutput::error()`.
- L'handler degli errori dell'agent, `fn (Throwable $e, ToolCall $call)`, converte le eccezioni sfuggite: un valore restituito diventa il risultato del tool, `null` lascia propagare l'eccezione.
- Logga tutto, di' poco al modello, e includi un'istruzione sul riprovare.
- Non far mai trapelare dettagli interni nella trascrizione.
- Lascia esplodere violazioni di permessi e bug.

## 5.12 Provider tool

### Che cosa sono

Alcuni provider offrono tool lato server — ricerca web, ricerca su file e altri — che vengono eseguiti nella loro infrastruttura invece che nel tuo processo PHP. Tu li abiliti; il provider li esegue.

### L'API

```php
use NeuronAI\Providers\OpenAI\Responses\OpenAIResponses;
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

**Il supporto è limitato a `OpenAIResponses`, `Gemini`, `Anthropic` e `ZAI`.** Ogni altro provider — Ollama, l'API chat-completions di OpenAI, Mistral, Bedrock — lancia una `ProviderException` quando trova un provider tool nell'elenco.

::: {.callout .callout-warning}
[Refuso nella documentazione]{.callout-title}

Versioni precedenti della documentazione mostrano `ProviderTool:make()` con un solo due punti. È un refuso per `::`.
:::

### Il compromesso, come lo dicono i documenti

La documentazione ufficiale è rinfrescantemente schietta: i provider tool introducono molti vincoli, e il modo più flessibile e affidabile di aggiungere capacità ai tuoi agent resta il sistema di Tool e Toolkit.

Sono gli autori del framework che ti dicono che la loro stessa funzionalità è la seconda scelta. Prendili in parola, e capisci perché:

**Perdi portabilità.** È il punto grosso. La Sezione 3.6 vendeva lo scambio di provider come beneficio centrale del framework. Un provider tool ti ancora: passa da OpenAI a Ollama e l'agent smette di funzionare, perché il provider Ollama rifiuta il tool con un'eccezione alla primissima richiesta. Almeno il fallimento è evidente. Ma l'intero argomento su stratificazione dei costi e rischio fornitore evapora per qualunque agent che ne dipenda.

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

Usa `TavilyToolkit` o `JinaToolkit` per la ricerca web. Entrambi sono portabili, funzionano con qualunque provider, sono testabili e ti permettono di vedere e mettere in cache ciò che torna indietro. Scegline però uno per agent: ciascuno fornisce un tool chiamato `web_search` e un altro chiamato `url_reader`, e i nomi dei tool devono essere univoci, quindi un agent a cui dai entrambi i toolkit lancia una `ToolException` alla prima esecuzione.

Ricorri a un provider tool quando hai una ragione specifica, e mettila per iscritto.

### Punti chiave

- I provider tool girano lato server; supportati solo su OpenAIResponses, Gemini, Anthropic e ZAI — gli altri provider lanciano un'eccezione.
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

**Richiede le estensioni `pcntl` e `posix`, e `pcntl` funziona solo nei processi CLI, non in contesto web.**

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

Il progetto qui è ben pensato: se `pcntl` o `posix` non sono presenti — una macchina di sviluppo Windows, per esempio — o `spatie/fork` non è installato, l'implementazione **ricade automaticamente sull'esecuzione sequenziale**. Fa lo stesso quando il modello ha richiesto un solo tool, che non vale un fork. Nessuna configurazione, nessun rilevamento d'ambiente nel tuo codice, nessun crash.

Sviluppi in locale senza `pcntl`/`posix` e metti in produzione dove è abilitato, senza cambiare una riga. L'agent si adatta a qualunque ambiente si trovi.

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

**Le connessioni al database vanno trattate con cura.** Una connessione PDO ereditata attraverso un fork è una classica fonte di fallimenti strani e intermittenti. Se i tuoi tool toccano il database, apri la connessione dentro il tool invece di condividerne una fra i fork — oppure usa i due hook che `parallelToolCalls()` accetta, eseguiti dentro ogni processo figlio prima e dopo il suo tool:

```php
$this->parallelToolCalls(
    true,
    beforeChild: fn () => DB::purge(),
    afterChild: fn () => DB::purge(),
);
```

È la forma Laravel: scarta la connessione ereditata così il figlio ne apre una propria. Dal figlio torna indietro solo il *risultato* di ogni tool, serializzato; l'oggetto tool e le sue dipendenze non attraversano mai il confine di processo.

### Punti chiave

- `parallelToolCalls(true)` scambia `ToolNode` con `ParallelToolNode`.
- Richiede `spatie/fork`, `pcntl` e `posix`; **solo CLI**, mai in una richiesta web.
- Ricade automaticamente sul sequenziale quando non disponibile, e per i turni con una sola chiamata.
- Gli hook `beforeChild` / `afterChild` reimpostano le risorse per processo, come le connessioni al database.
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

use NeuronAI\Exceptions\HttpException;
use NeuronAI\HttpClient\Curl\CurlHttpClient;
use NeuronAI\HttpClient\HttpClientInterface;
use NeuronAI\HttpClient\HttpRequest;
use NeuronAI\Tools\PropertyType;
use NeuronAI\Tools\Tool;
use NeuronAI\Tools\ToolOutput;
use NeuronAI\Tools\ToolProperty;
use Uri\WhatWg\Url;

class WeatherTool extends Tool
{
    private const BASE_URL = 'https://api.open-meteo.com/v1/';

    protected string $name = 'get_current_weather';

    protected ?string $description = 'Returns current weather conditions for a geographic location: temperature '
        . 'in Celsius, wind speed in km/h, and a numeric weather code. Use this '
        . 'whenever the user asks about current weather, temperature, or conditions '
        . 'anywhere in the world. You must derive latitude and longitude yourself '
        . 'from the place name. Never invent weather data — always call this tool.';

    protected HttpClientInterface $client;

    public function __construct(?HttpClientInterface $client = null)
    {
        // PHP 8.5: Uri\WhatWg\Url parses the endpoint the way a browser would,
        // so a malformed base URL fails here rather than on the first request.
        $this->client = $client ?? (new CurlHttpClient(timeout: 10.0))
            ->withBaseUri(new Url(self::BASE_URL)->toAsciiString());
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

    public function __invoke(float $latitude, float $longitude): string|ToolOutput
    {
        // PHP 8.5: the pipe operator reads top to bottom - the parameters
        // become a query string, and the query string becomes the request.
        $request = [
            'latitude'  => $latitude,
            'longitude' => $longitude,
            'current'   => 'temperature_2m,wind_speed_10m,weather_code',
        ]
            |> \http_build_query(...)
            |> (static fn (string $query): HttpRequest => HttpRequest::get("forecast?{$query}"));

        try {
            $data = $this->client->request($request)->json();
        } catch (HttpException) {
            return ToolOutput::error(
                'The weather service is unreachable right now. Do not retry; '
                . 'tell the user the data is unavailable.'
            );
        }

        if (!isset($data['current'])) {
            return ToolOutput::error('The weather service returned no current conditions for these coordinates.');
        }

        return \json_encode($data['current'], \JSON_THROW_ON_ERROR);
    }
}
```

Open-Meteo non richiede chiavi API, quindi l'intero laboratorio gira gratis — combinato con Ollama, lo completi senza un account da nessuna parte.

Tre cose in questa classe meritano un secondo sguardo. I parametri `float` non richiedono alcun allargamento difensivo, perché il binding converte il `"45.07"` del modello in `45.07` prima della chiamata (Sezione 5.5). Un servizio irraggiungibile viene *restituito* come `ToolOutput::error()` invece di essere lanciato, con un'istruzione allegata (Sezione 5.11). E il client HTTP è il `CurlHttpClient` del framework, quindi il laboratorio non aggiunge dipendenze — mentre l'argomento opzionale del costruttore è il punto di aggancio della Sezione 5.3: un test passa uno stub e non raggiunge mai Open-Meteo.

Qui compaiono due funzionalità di PHP 8.5. L'operatore pipe `|>` passa il valore alla sua sinistra come unico argomento al callable alla sua destra, così la costruzione della richiesta si legge nell'ordine in cui avviene — array, query string, richiesta — invece che dall'interno verso l'esterno. E `Uri\WhatWg\Url`, la metà dell'estensione URI conforme allo standard dei browser vista nella Sezione 3.6, valida l'URL di base quando il tool viene costruito anziché alla prima richiesta.

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
use NeuronAI\Tools\ToolCall;
use NeuronAI\Tools\ToolOutput;
use NeuronAI\Tools\Toolkits\Calculator\CalculatorToolkit;
use NeuronAI\Tools\Toolkits\Calculator\EvaluateTool;
use NeuronAI\Tools\Toolkits\Calculator\MeanTool;
use Throwable;

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
                EvaluateTool::class,
                MeanTool::class,
            ]),
        ];
    }

    protected function resolveToolErrorHandler(): ?callable
    {
        return function (Throwable $e, ToolCall $call): ToolOutput {
            \error_log(\sprintf('[tool:%s] %s: %s', $call->getName(), $e::class, $e->getMessage()));

            return ToolOutput::error(
                "The {$call->getName()} tool failed. Do not retry more than once. "
                . 'If it fails again, tell the user the data is unavailable.'
            );
        };
    }
}
```

Nota che cosa dimostra questa singola classe di tutto il capitolo: un tool come classe (5.3), una descrizione in quattro parti (5.4), esempi nelle descrizioni delle proprietà (5.4), `only()` come lista di permessi (5.8), un limite di esecuzioni per tool (5.9) e un vero handler degli errori (5.11). Dei quattordici tool della calcolatrice l'agent ne tiene due: `evaluate` per qualunque formula e `mean` per le medie.

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
        ->setThreadId('demo')
        ->toolMaxRuns(6)
        ->chat(new UserMessage($prompt))
        ->getMessage()
        ?->getContent() . PHP_EOL;

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

Eseguilo con Inspector collegato, come mostra il Capitolo 10, e apri il trace. Vedi la sequenza reale: due chiamate meteo, una chiamata alla calcolatrice — `mean`, oppure `evaluate` con l'intera formula — e una risposta testuale finale. Quell'immagine è ciò che la tabella della Sezione 1.2 descriveva in astratto, e vederla rende concreta l'aritmetica dei costi della Sezione 1.4.

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
use NeuronAI\Exceptions\ToolRunsExceededException;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Tools\Toolkits\Calculator\CalculatorToolkit;
use NeuronAI\Tools\Toolkits\Calculator\EvaluateTool;
use NeuronAI\Tools\Toolkits\Calculator\MeanTool;
use NeuronAI\Tools\Toolkits\MySQL\MySQLSchemaTool;
use NeuronAI\Tools\Toolkits\MySQL\MySQLSelectTool;
use NeuronAI\Tools\ToolCall;
use NeuronAI\Tools\ToolOutput;

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

            CalculatorToolkit::make()->only([
                EvaluateTool::class,
                MeanTool::class,
            ]),
        ];
    }

    protected function resolveToolErrorHandler(): ?callable
    {
        return function (\Throwable $e, ToolCall $call): ToolOutput {
            if ($e instanceof ToolRunsExceededException) {
                return ToolOutput::error(
                    "You have used {$call->getName()} as often as allowed. "
                    . 'Answer from the results you already have.'
                );
            }

            \error_log(\sprintf('[tool:%s] %s: %s', $call->getName(), $e::class, $e->getMessage()));

            return ToolOutput::error(
                "The {$call->getName()} tool failed. Do not retry; tell the user "
                . 'the data is unavailable right now.'
            );
        };
    }
}
```

L'handler ha meno da fare di quanto ti aspetteresti. Una query che il database respinge — una colonna sconosciuta, una tabella che l'utente non può leggere — non gli arriva mai: `MySQLSelectTool` restituisce al modello il messaggio del database stesso come risultato di errore, ed è questo che permette al modello di correggere il proprio SQL. All'handler arriva il resto. Un limite di esecuzioni riceve una frase che dice al modello di lavorare con ciò che ha. L'imprevisto vero — una connessione persa, un fallimento nel tool di schema — riceve una riga di log per te e una frase fissa per il modello, mai il testo dell'eccezione (Sezione 5.11).

### L'esecutore

**`examples/05-data-analyst.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\DataAnalystAgent;
use NeuronAI\Chat\Messages\UserMessage;

$question = $argv[1] ?? 'How many orders did we receive today?';

echo DataAnalystAgent::make()
    ->setThreadId('demo')
    ->chat(new UserMessage($question))
    ->getMessage()
    ?->getContent() . PHP_EOL;
```

```bash
php examples/05-data-analyst.php "How many orders did we receive today?"
php examples/05-data-analyst.php "What's the average order value this month, by country?"
php examples/05-data-analyst.php "Which three products have the highest revenue?"
```

### Quattro livelli di difesa

1. **`MySQLWriteTool` non è collegato.** L'agent non ha alcun tool che scrive, e quello che legge non si lascia convincere a farlo: `MySQLSelectTool` accetta una singola istruzione che comincia con `SELECT`, `WITH`, `SHOW`, `DESCRIBE` o `EXPLAIN`, e la esegue in una transazione `READ ONLY` di cui fa sempre il rollback.
2. **Il tool di schema descrive tre tabelle.** Al modello non viene mai detto che `payments` o `users` esistono. Questo livello è solo indicativo: restringe ciò che viene mostrato al modello, non ciò che la connessione può leggere, e un modello che indovina il nome di una tabella viene fermato dal livello 4, non da questo.
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

La documentazione sui Tool è la pagina più densa del progetto NeuronAI, ed è stata in disaccordo con sé stessa e con il codice su nomi di eccezioni, nomi di metodi, nomi di classi, namespace, percorsi di import e firme dei metodi. Quasi ognuno di questi casi produce un errore fatale per chi copia la pagina.
:::
