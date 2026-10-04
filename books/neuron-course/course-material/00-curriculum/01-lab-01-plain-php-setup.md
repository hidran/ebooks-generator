# Lab 01 — Neuron in PHP puro con Composer

Progetto di partenza per i moduli 3, 4 e 5 del corso. Nessun framework: solo Composer, PHP da CLI e la libreria. Tutto copia-incolla.

Scritto per `neuron-core/neuron-ai` 4.0.3 (PHP 8.5; il codice di questo lab usa solo sintassi che gira anche su PHP 8.3). Nessun esempio usa API di v3: `Tool` è astratta, la memoria è un *message store*, e ogni agente ha bisogno di un thread ID.

---

## 1. Scaffolding del progetto

```bash
mkdir -p neuron-course/01-plain-php && cd neuron-course/01-plain-php

mkdir -p src/Agents src/Tools src/Dto examples storage/chat
touch .env .env.example .gitignore
```

```bash
composer init --name="hidran/neuron-lab" --type=project --no-interaction
composer require neuron-core/neuron-ai vlucas/phpdotenv guzzlehttp/guzzle
```

Struttura risultante:

```
01-plain-php/
├── composer.json
├── .env
├── .env.example
├── bootstrap.php
├── src/
│   ├── Agents/
│   ├── Tools/
│   └── Dto/
├── examples/
└── storage/chat/
```

### `composer.json`

```json
{
    "name": "hidran/neuron-lab",
    "type": "project",
    "require": {
        "php": "^8.5",
        "neuron-core/neuron-ai": "^4.0.3",
        "vlucas/phpdotenv": "^5.6",
        "guzzlehttp/guzzle": "^7.9"
    },
    "autoload": {
        "psr-4": {
            "App\\": "src/"
        }
    },
    "config": {
        "sort-packages": true
    },
    "minimum-stability": "stable",
    "prefer-stable": true
}
```

```bash
composer dump-autoload
```

### `.gitignore`

```gitignore
/vendor/
/storage/chat/*
!/storage/chat/.gitkeep
.env
.phpunit.result.cache
```

```bash
touch storage/chat/.gitkeep
```

### `.env.example`

```dotenv
# anthropic | openai | gemini | ollama | mistral | deepseek
NEURON_PROVIDER=ollama

ANTHROPIC_KEY=
ANTHROPIC_MODEL=claude-sonnet-4-5

OPENAI_KEY=
OPENAI_MODEL=gpt-4.1-mini

GEMINI_KEY=
GEMINI_MODEL=gemini-2.0-flash

MISTRAL_KEY=
MISTRAL_MODEL=mistral-large-latest

# Ollama in locale: nessun costo, ideale per i lab
OLLAMA_URL=http://localhost:11434/api
OLLAMA_MODEL=qwen2.5:7b

# Opzionale: monitoraggio su inspector.dev
INSPECTOR_INGESTION_KEY=
```

```bash
cp .env.example .env
```

> I nomi dei modelli cambiano di continuo. Verifica sempre sul sito del provider quale sia disponibile al momento in cui segui il corso.

---

## 2. Bootstrap e factory dei provider

Il pezzo di codice più utile di tutto il lab: isola la scelta del provider in un unico punto, così ogni esempio successivo può cambiare LLM modificando **una riga del `.env`**. È lo stesso principio che l'SDK Laravel implementa con la facade `AIProvider`.

### `bootstrap.php`

```php
<?php

declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

$dotenv = Dotenv\Dotenv::createImmutable(__DIR__);
$dotenv->safeLoad();

function env(string $key, ?string $default = null): ?string
{
    $value = $_ENV[$key] ?? $_SERVER[$key] ?? getenv($key);

    return ($value === false || $value === '') ? $default : (string) $value;
}
```

### `src/ProviderFactory.php`

```php
<?php

declare(strict_types=1);

namespace App;

use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Providers\Anthropic\Anthropic;
use NeuronAI\Providers\Gemini\Gemini;
use NeuronAI\Providers\Mistral\Mistral;
use NeuronAI\Providers\Ollama\Ollama;
use NeuronAI\Providers\OpenAI\OpenAI;

final class ProviderFactory
{
    /**
     * Restituisce il provider configurato nell'ambiente.
     * Passa un nome esplicito per forzarne uno diverso a runtime.
     */
    public static function make(?string $driver = null): AIProviderInterface
    {
        $driver ??= env('NEURON_PROVIDER', 'ollama');

        return match ($driver) {
            'anthropic' => new Anthropic(
                key: env('ANTHROPIC_KEY') ?? throw new \RuntimeException('ANTHROPIC_KEY mancante'),
                model: env('ANTHROPIC_MODEL', 'claude-sonnet-4-5'),
            ),
            'openai' => new OpenAI(
                key: env('OPENAI_KEY') ?? throw new \RuntimeException('OPENAI_KEY mancante'),
                model: env('OPENAI_MODEL', 'gpt-4.1-mini'),
            ),
            'gemini' => new Gemini(
                key: env('GEMINI_KEY') ?? throw new \RuntimeException('GEMINI_KEY mancante'),
                model: env('GEMINI_MODEL', 'gemini-2.0-flash'),
            ),
            'mistral' => new Mistral(
                key: env('MISTRAL_KEY') ?? throw new \RuntimeException('MISTRAL_KEY mancante'),
                model: env('MISTRAL_MODEL', 'mistral-large-latest'),
            ),
            'ollama' => new Ollama(
                url: env('OLLAMA_URL', 'http://localhost:11434/api'),
                model: env('OLLAMA_MODEL', 'qwen2.5:7b'),
            ),
            default => throw new \InvalidArgumentException("Provider sconosciuto: {$driver}"),
        };
    }
}
```

> **Punto didattico.** Qui c'è tutto il valore dell'architettura a interfacce: `AIProviderInterface` è l'unico tipo che il resto dell'applicazione conosce. Cambiare da Ollama a Claude non tocca una riga di logica di business. Fermati sul video e falla notare, perché è l'argomento con cui gli studenti venderanno Neuron ai loro clienti.

---

## 3. Il primo agente

Puoi generarlo con la CLI del framework:

```bash
./vendor/bin/neuron make:agent App\\Agents\\AssistantAgent
```

Oppure scriverlo a mano.

### `src/Agents/AssistantAgent.php`

```php
<?php

declare(strict_types=1);

namespace App\Agents;

use App\ProviderFactory;
use NeuronAI\Agent\Agent;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Providers\AIProviderInterface;

class AssistantAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return ProviderFactory::make();
    }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: [
                'Sei un assistente tecnico specializzato in sviluppo PHP.',
                'Parli con sviluppatori esperti: niente spiegazioni di base non richieste.',
            ],
            steps: [
                'Analizza la domanda e identifica il problema reale, non solo quello dichiarato.',
                'Se la domanda è ambigua, chiedi il chiarimento minimo indispensabile.',
                'Rispondi con codice quando il codice è la risposta.',
            ],
            output: [
                'Rispondi sempre in italiano.',
                'Usa blocchi di codice con il linguaggio dichiarato.',
                'Niente preamboli del tipo "Certamente!" o "Ottima domanda".',
            ],
        );
    }

    protected function contextWindow(): int
    {
        // Circa il 90% della context window del modello: il trimmer ha bisogno di margine.
        // Senza questo metodo il default è 50.000 token. La memoria è un message store
        // in memoria, finché non ne scegli un altro con messageStore() (sezione 5).
        return 120_000;
    }
}
```

**Perché `SystemPrompt` e non una stringa.** I tre argomenti `background`, `steps` e `output` vengono resi in una struttura che i modelli seguono meglio di un paragrafo continuo. Separare "chi sei", "come procedi" e "come formatti" rende anche il prompt manutenibile: puoi cambiare il formato di output senza toccare la personalità dell'agente.

### `examples/01-first-agent.php`

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\AssistantAgent;
use NeuronAI\Chat\Messages\UserMessage;

$prompt = $argv[1] ?? 'Spiegami in tre righe la differenza tra readonly e final in PHP 8.';

// Un agente gira sempre su un thread, e Neuron non ne inventa mai uno:
// senza setThreadId() la chiamata lancia un'AgentException prima di contattare il modello.
// chat() restituisce lo stato finale (AgentState), non il messaggio.
$state = AssistantAgent::make()
    ->setThreadId('demo')
    ->chat(new UserMessage($prompt));

echo $state->getMessage()?->getContent() . PHP_EOL;
```

```bash
php examples/01-first-agent.php "Come implemento un middleware PSR-15 senza framework?"
```

### Provider swap: l'esperimento da mostrare in video

```bash
NEURON_PROVIDER=ollama    php examples/01-first-agent.php "Cos'è un generator in PHP?"
NEURON_PROVIDER=anthropic php examples/01-first-agent.php "Cos'è un generator in PHP?"
NEURON_PROVIDER=openai    php examples/01-first-agent.php "Cos'è un generator in PHP?"
```

Stesso codice, tre motori. Fai cronometrare la latenza agli studenti: la differenza tra locale e cloud è l'argomento che li aiuta a scegliere in fase di design.

---

## 4. Un tool scritto a mano

In v4 un tool è sempre una classe che estende `Tool`: nome e descrizione sono proprietà, lo schema è in `properties()`, la logica è in `__invoke()`. (In v3 esisteva anche la forma inline `Tool::make('nome', 'descrizione')->addProperty(...)->setCallable(...)`: in v4 `Tool` è astratta e quel codice lancia `Cannot instantiate abstract class NeuronAI\Tools\Tool`.) Comincia dalla classe più piccola possibile, dichiarata nello stesso file dell'esempio, per far capire il meccanismo; poi passa alla classe in `src/Tools/`, con dipendenze iniettate: è la forma che si usa in produzione perché testabile, iniettabile e riusabile.

### 4a. Il tool minimo

### `examples/02-inline-tool.php`

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\ProviderFactory;
use NeuronAI\Agent\Agent;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Tools\PropertyType;
use NeuronAI\Tools\Tool;
use NeuronAI\Tools\ToolProperty;

class ServerLoadTool extends Tool
{
    protected string $name = 'get_server_load';

    protected ?string $description = 'Restituisce il carico medio della CPU del server negli ultimi 1, 5 e 15 minuti.';

    protected function properties(): array
    {
        return [
            new ToolProperty(
                name: 'window',
                type: PropertyType::STRING,
                description: 'Finestra temporale richiesta. Valori ammessi: "1m", "5m", "15m".',
                required: true,
                enum: ['1m', '5m', '15m'],
            ),
        ];
    }

    public function __invoke(string $window): string
    {
        $load = \sys_getloadavg();
        $value = match ($window) {
            '1m' => $load[0],
            '5m' => $load[1],
            '15m' => $load[2],
            default => throw new \InvalidArgumentException("Finestra non valida: {$window}"),
        };

        return \sprintf('Load average (%s): %.2f', $window, $value);
    }
}

$agent = Agent::make()
    ->setAiProvider(ProviderFactory::make())
    ->addTool(ServerLoadTool::make())
    ->setThreadId('demo');

echo $agent->chat(new UserMessage('Il server è sotto stress in questo momento?'))
    ->getMessage()
    ?->getContent() . PHP_EOL;
```

> **Nota sull'API fluente.** Un `Agent` può essere configurato anche dal punto di chiamata: `setAiProvider()`, `setInstructions()`, `addTool()`, `setMessageStore()`, `setThreadId()` sono i setter che sostituiscono i metodi `provider()`, `instructions()`, `tools()`, `messageStore()` della forma per estensione (e hanno la precedenza su di essi). `withProvider()` non esiste in v4. La forma per estensione è comunque quella consigliata nel corso.

### 4b. Tool come classe

Genera lo scheletro:

```bash
./vendor/bin/neuron make:tool App\\Tools\\WeatherTool
```

### `src/Tools/WeatherTool.php`

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
    protected string $name = 'get_current_weather';

    protected ?string $description = 'Restituisce le condizioni meteo attuali di una città: temperatura in gradi Celsius, '
        . 'velocità del vento e codice condizione. Usa questo tool ogni volta che ti viene '
        . 'chiesto il meteo attuale di un luogo. Non inventare mai dati meteo.';

    protected Client $client;

    protected function properties(): array
    {
        return [
            new ToolProperty(
                name: 'latitude',
                type: PropertyType::NUMBER,
                description: 'Latitudine della località in gradi decimali. Esempio: 45.0703 per Torino.',
                required: true,
            ),
            new ToolProperty(
                name: 'longitude',
                type: PropertyType::NUMBER,
                description: 'Longitudine della località in gradi decimali. Esempio: 7.6869 per Torino.',
                required: true,
            ),
        ];
    }

    public function __invoke(float $latitude, float $longitude): string
    {
        $response = $this->getClient()->get('forecast', [
            'query' => [
                'latitude'  => $latitude,
                'longitude' => $longitude,
                'current'   => 'temperature_2m,wind_speed_10m,weather_code',
            ],
        ])->getBody()->getContents();

        $data = \json_decode($response, true, 512, JSON_THROW_ON_ERROR);

        return \json_encode($data['current'] ?? [], JSON_THROW_ON_ERROR);
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

> **Nota v4.** `Tool` non ha più un costruttore: identità e descrizione sono le proprietà `$name` e `$description`, e un `parent::__construct('nome', 'descrizione')` (v3) fallisce con `Cannot call constructor`.

> **Il punto che vale mezza lezione.** La descrizione del tool *è* prompt engineering. Nota le tre parti: cosa fa, quando usarlo, cosa non fare. Registra la stessa domanda con una descrizione povera ("prende il meteo") e con questa: la differenza nel comportamento del modello è visibile e convince più di qualsiasi spiegazione. Lo stesso vale per gli esempi dentro la descrizione delle proprietà.

### `src/Agents/WeatherAgent.php`

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
use NeuronAI\Tools\Toolkits\Calculator\EvaluateTool;
use NeuronAI\Tools\Toolkits\Calculator\MeanTool;

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
                'Sei un assistente meteo. Rispondi solo con dati reali ottenuti dai tuoi strumenti.',
            ],
            steps: [
                'Ricava le coordinate geografiche della località citata dall\'utente.',
                'Chiama lo strumento meteo per ogni località richiesta.',
                'Se serve un confronto o una media, usa gli strumenti di calcolo.',
            ],
            output: [
                'Rispondi in italiano, in due righe al massimo.',
                'Indica sempre la temperatura in gradi Celsius.',
            ],
        );
    }

    protected function tools(): array
    {
        return [
            WeatherTool::make(),
            CalculatorToolkit::make()->only([
                EvaluateTool::class,
                MeanTool::class,
            ]),
        ];
    }
}
```

### `examples/03-weather-agent.php`

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\WeatherAgent;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Tools\ToolCall;

$prompt = $argv[1] ?? 'Che temperatura media c\'è adesso tra Torino e Milano?';

try {
    $response = WeatherAgent::make()
        ->setThreadId('demo')
        ->toolMaxRuns(5)
        ->toolErrorHandler(
            // Il secondo argomento è la ToolCall (nome e argomenti inviati dal modello), non il tool.
            fn (\Throwable $e, ToolCall $call): string =>
                "Lo strumento {$call->getName()} ha fallito: {$e->getMessage()}. "
                . "Informa l'utente che il dato non è disponibile."
        )
        ->chat(new UserMessage($prompt))
        ->getMessage();

    echo $response?->getContent() . PHP_EOL;
} catch (\Throwable $e) {
    \fwrite(STDERR, 'Errore: ' . $e->getMessage() . PHP_EOL);
    exit(1);
}
```

```bash
php examples/03-weather-agent.php
```

Questa singola domanda innesca due chiamate a `get_current_weather` e una al calcolatore (`mean`, oppure `evaluate` con l'intera formula). È l'esempio perfetto per mostrare il loop dell'agente in azione — e per giustificare l'esistenza di Inspector nel modulo 10.

**Da notare nel codice:**

- `toolMaxRuns(5)` — guardrail contro il loop infinito. Il default è 10 per tool.
- `toolErrorHandler()` — restituisce l'errore *al modello* invece di far crollare lo script. Il modello può decidere di riprovare o di dire all'utente che il dato manca. È la differenza tra un prototipo e qualcosa che gira in produzione.
- `only()` sul toolkit — passiamo due tool al posto di quattordici: `evaluate` per qualsiasi formula e `mean` per le medie. Meno token per richiesta, meno probabilità che il modello scelga lo strumento sbagliato.
- `CalculatorToolkit::make()` istanzia tutti i suoi tool, e quelli per interi esatti richiedono `ext-bcmath`: senza l'estensione l'agente fallisce già all'avvio, anche se ne usi solo due. Abilita `bcmath` oppure registra direttamente `EvaluateTool::make()` e `MeanTool::make()`.

---

## 5. Chat CLI multi-turno con memoria persistente

### `src/Agents/PersistentAgent.php`

```php
<?php

declare(strict_types=1);

namespace App\Agents;

use App\ProviderFactory;
use NeuronAI\Agent\Agent;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Chat\History\FileMessageStore;
use NeuronAI\Chat\History\MessageStoreInterface;
use NeuronAI\Providers\AIProviderInterface;

class PersistentAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return ProviderFactory::make();
    }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: ['Sei un assistente tecnico che ricorda il contesto della conversazione.'],
            output: ['Rispondi in italiano, in modo conciso.'],
        );
    }

    protected function messageStore(): MessageStoreInterface
    {
        return new FileMessageStore(
            directory: \dirname(__DIR__, 2) . '/storage/chat',
        );
    }

    protected function contextWindow(): int
    {
        return 120_000;
    }
}
```

Nota cosa la classe *non* contiene: il thread ID. Niente costruttore, niente chiave passata allo store. La classe descrive *dove* vivono le conversazioni; *quale* conversazione è decide chi costruisce l'agente, con `make(workflowId: ...)` o `setThreadId()`. Lo stesso agente serve ogni thread. (In v3 il thread era la `key:` di `FileChatHistory`, passata dal costruttore dell'agente: quel pattern non esiste più.)

### `examples/04-chat-loop.php`

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\PersistentAgent;
use NeuronAI\Chat\Messages\UserMessage;

$threadId = $argv[1] ?? 'default';
$agent = PersistentAgent::make(workflowId: $threadId);

echo "Thread: {$threadId} — digita /exit per uscire, /reset per azzerare la memoria.\n\n";

while (true) {
    $input = \readline('> ');

    if ($input === false || \trim($input) === '') {
        continue;
    }

    $input = \trim($input);
    \readline_add_history($input);

    if ($input === '/exit') {
        break;
    }

    if ($input === '/reset') {
        // Abbandona l'eventuale run non concluso del thread e svuota la sua memoria nello store:
        // per FileMessageStore cancella il file di quel thread e nient'altro.
        $agent->resetConversation();
        echo "Memoria azzerata.\n\n";
        continue;
    }

    try {
        $reply = $agent->chat(new UserMessage($input))->getMessage();
        echo "\n" . $reply?->getContent() . "\n\n";
    } catch (\Throwable $e) {
        \fwrite(STDERR, "Errore: {$e->getMessage()}\n\n");
    }
}
```

```bash
php examples/04-chat-loop.php progetto-alfa
```

Chiudi il terminale, riaprilo, rilancia con lo stesso thread: la conversazione riparte da dove l'avevi lasciata. È la dimostrazione più efficace del concetto di message store: nulla è stato "ricordato", la trascrizione è stata riletta dal disco e rimandata al modello. Ogni thread è un file `neuron_<thread>.chat` in `storage/chat/`.

> **Sul `contextWindow()`.** La documentazione è esplicita: imposta un valore inferiore del 5–10% rispetto al limite reale del modello. Il trimmer cerca un punto di taglio che minimizzi la perdita di contesto e ha bisogno di margine per farlo. Con un modello da 200K, configura 180–190K.

---

## 6. Streaming da terminale

### `examples/05-streaming.php`

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\AssistantAgent;
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\UserMessage;

$prompt = $argv[1] ?? 'Spiegami il pattern Repository e quando è un errore usarlo.';

// stream() restituisce un generatore di oggetti chunk (testo, ragionamento, chiamate di tool…):
// si filtra per TextChunk prima di leggere ->content.
foreach (AssistantAgent::make()->setThreadId('demo')->stream(new UserMessage($prompt)) as $chunk) {
    if ($chunk instanceof TextChunk) {
        echo $chunk->content;
        \flush();
    }
}

echo PHP_EOL;
```

Da CLI la differenza percettiva è già netta. Il tipo di chunk conta: un modello di ragionamento può emettere chunk di ragionamento per secondi prima della prima parola della risposta, e `echo $chunk` su un oggetto non è una stringa. Nel modulo 21 la stessa cosa arriva al browser via SSE, con i problemi di buffering di nginx e PHP-FPM che è bene affrontare in una lezione dedicata.

---

## 7. Esercizi

1. **Provider benchmark.** Estendi `01-first-agent.php` per eseguire lo stesso prompt su tutti i provider configurati e stampare una tabella con risposta, durata e token consumati (`$state->getMessage()?->getUsage()`).
2. **Tool con array.** Scrivi un tool `compare_cities` che accetta un `ArrayProperty` di nomi di città e restituisce un confronto. Osserva come cambia lo schema inviato al modello.
3. **Structured input.** Riscrivi `WeatherTool` usando un `ObjectProperty` con una classe `Coordinates` annotata con `#[SchemaProperty]`.
4. **Guardrail.** Imposta `toolMaxRuns(1)` e chiedi la media tra cinque città. Cattura `NeuronAI\Exceptions\ToolRunsExceededException` (l'unica che esiste: un `catch` su una classe inesistente non fallisce, semplicemente non scatta mai) e gestiscila con un messaggio utile. Discuti quando questo limite è una protezione e quando è un bug di design.
5. **Visibilità.** Aggiungi un tool `delete_cache` disponibile solo se la variabile d'ambiente `APP_ROLE=admin`. Verifica con `visible(false)` che il modello non ne conosca nemmeno l'esistenza.

---

## 8. Verifiche prima della registrazione

- [ ] Confermare i namespace sul codice installato (`vendor/neuron-core/neuron-ai/src`) e sulle guide in `vendor/neuron-core/neuron-ai/upgrade/`: chi viene da v3 trova i nomi cambiati (`*ChatHistory` → `*MessageStore`, `Tool::make()->setCallable()` → classe con `__invoke()`)
- [ ] Verificare la firma esatta di `FileMessageStore` (`directory`, `prefix`, `ext`) e il formato dei file generati (`neuron_<thread>.chat`)
- [ ] Verificare quali metodi fluenti (`setAiProvider`, `addTool`, `toolErrorHandler`, `setThreadId`) esistono nella build usata
- [ ] Verificare il tipo restituito da `stream()` nella versione corrente (oggetti chunk, filtrati con `TextChunk`)
- [ ] Fissare la versione in `composer.json` con un vincolo stretto e committare `composer.lock` nel repo del corso, così gli studenti non trovano un'API diversa fra tre mesi
