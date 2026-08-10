# Capitolo 3 — Setup e il tuo primo agent

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

La versione eseguibile di ogni listato che segue si trova in [`chapters/Ch03`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch03), nel repository di accompagnamento. Clonalo, esegui `composer install` e gli esempi funzionano su un Ollama locale senza alcuna API key.
:::

## 3.1 Impalcatura del progetto

Costruiremo un progetto pulito in PHP puro che porterà avanti ogni esempio delle Parti II, III e IV. Niente framework, niente magia.

### Perché prima PHP puro

Passerai la Parte V dentro Laravel, dove una facade ti consegna un agent già configurato e un comando artisan genera le tue classi. Quella comodità vale la pena — ma solo dopo aver visto che cosa nasconde. Tutto ciò che fa l'SDK Laravel, l'avrai già fatto a mano.

Conta anche sul piano commerciale: una grossa fetta del lavoro PHP non è Laravel. Symfony, Spryker, WordPress, MVC interni legacy. Un agent costruito sul pacchetto base si inserisce in tutti quanti.

### Creare il progetto

```bash
mkdir -p neuron-course/01-plain-php && cd neuron-course/01-plain-php

mkdir -p src/Agents src/Tools src/Dto examples storage/chat
touch bootstrap.php .env .env.example .gitignore
touch storage/chat/.gitkeep
```

```bash
composer init --name="yourname/neuron-lab" --type=project --no-interaction
```

### composer.json

```json
{
    "name": "yourname/neuron-lab",
    "type": "project",
    "require": {
        "php": "^8.1"
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

Il blocco PSR-4 mappa il namespace `App\` su `src/`. `App\Agents\WeatherAgent` sta in `src/Agents/WeatherAgent.php`. Niente di esotico — ma sbaglialo e ogni esempio successivo fallirà con un errore di classe non trovata, quindi verificalo subito:

```bash
composer dump-autoload
```

### .gitignore

```gitignore
/vendor/
/storage/chat/*
!/storage/chat/.gitkeep
.env
.phpunit.result.cache
```

Due righe qui sono portanti. `/vendor/` perché è rigenerabile. `.env` perché conterrà chiavi API, e una chiave finita su un repository pubblico ti viene addebitata nel giro di ore. La Sezione 3.7 lo tratta come si deve.

### Struttura finale

```
01-plain-php/
├── composer.json
├── bootstrap.php
├── .env                 ← chiavi vere, mai committate
├── .env.example         ← solo la struttura, committato
├── src/
│   ├── Agents/
│   ├── Tools/
│   └── Dto/
├── examples/            ← uno script eseguibile per sezione
└── storage/chat/        ← conversazioni persistite
```

### Punti chiave

- Prima PHP puro; l'SDK del framework aggiunge comodità, non capacità.
- PSR-4 mappa `App\` → `src/`; verifica con `composer dump-autoload` prima di scrivere codice.
- `.env` è in `.gitignore` dal primo minuto.

## 3.2 Installare NeuronAI

### L'installazione

```bash
composer require neuron-core/neuron-ai vlucas/phpdotenv guzzlehttp/guzzle
```

**`neuron-core/neuron-ai`** — il framework. Richiede PHP 8.1 o superiore.

**`vlucas/phpdotenv`** — legge un file `.env` nell'ambiente. Laravel lo include; il PHP puro no. Senza, dovresti scrivere le chiavi API nel codice, cosa che non faremo.

**`guzzlehttp/guzzle`** — un client HTTP. NeuronAI tira dentro ciò che gli serve internamente; lo richiediamo esplicitamente perché i nostri tool chiameranno API esterne nel Capitolo 5, e una dipendenza esplicita è una dipendenza onesta.

### Fissa la versione

```json
"require": {
    "php": "^8.1",
    "neuron-core/neuron-ai": "^3.0",
    "vlucas/phpdotenv": "^5.6",
    "guzzlehttp/guzzle": "^7.9"
}
```

**Committa `composer.lock` in un repository didattico.** Non è il consiglio abituale per le librerie: è deliberato. Chi seguirà questo libro fra un anno deve ottenere la stessa API su cui è stato scritto. Senza il lock file otterrà quello a cui `^3.0` si risolve quel giorno, e se un rilascio minore ha cambiato una firma otterrà un errore su cui nessuno può aiutarlo.

### Verifica

```bash
php -r "require 'vendor/autoload.php'; echo class_exists(NeuronAI\Agent\Agent::class) ? 'OK' : 'FAIL';"
```

Se stampa `FAIL`, sei quasi certamente su una major precedente in cui la classe era `NeuronAI\Agent`. Controlla con:

```bash
composer show neuron-core/neuron-ai | head -5
```

### Due parole su namespace e documentazione

Fra v2 e v3 i namespace si sono spostati:

| v1 / v2 | v3 |
|---|---|
| `NeuronAI\Agent` | `NeuronAI\Agent\Agent` |
| `NeuronAI\SystemPrompt` | `NeuronAI\Agent\SystemPrompt` |

Parti della documentazione ufficiale, diversi articoli di blog e la maggior parte del materiale di terze parti mostrano ancora gli import v2. Quando trovi codice d'esempio le cui istruzioni `use` non corrispondono a questo libro, controlla a quale versione punta prima di dare per scontato che qualcosa sia rotto. È la fonte di confusione più comune per chi arriva dai tutorial.

### Punti chiave

- `composer require neuron-core/neuron-ai`, PHP 8.1+.
- Fissa la versione e committa `composer.lock` nei repository didattici.
- v2 → v3 ha spostato i namespace; i tutorial più vecchi non compilano su v3.

## 3.3 La CLI del framework

I generatori creano componenti del framework con la struttura corretta. Vale la pena sapere che cosa producono, perché queste classi vorrai anche scriverle a mano.

### Il binario

Installare il pacchetto ti dà un eseguibile in `vendor/bin/neuron`.

```bash
./vendor/bin/neuron
```

### I generatori

**Unix / macOS** — nota i doppi backslash, che servono alla shell:

```bash
./vendor/bin/neuron make:agent App\\Agents\\AssistantAgent
./vendor/bin/neuron make:tool App\\Tools\\WeatherTool
./vendor/bin/neuron make:node App\\Workflow\\InitialNode
./vendor/bin/neuron make:event App\\Workflow\\FirstEvent
```

**Windows PowerShell** — backslash singoli:

```powershell
.\vendor\bin\neuron make:agent App\Agents\AssistantAgent
.\vendor\bin\neuron make:tool App\Tools\WeatherTool
.\vendor\bin\neuron make:node App\Workflow\InitialNode
.\vendor\bin\neuron make:event App\Workflow\FirstEvent
```

Quella differenza di backslash fa perdere più tempo di quanto abbia diritto. Se un comando di generazione sembra non fare nulla, conta prima i backslash.

### Che cosa produce ciascuno

| Comando | Produce | Trattato in |
|---|---|---|
| `make:agent` | Classe che estende `Agent` con gli stub `provider()` e `instructions()` | Capitolo 3 |
| `make:tool` | Classe che estende `Tool` con gli stub `properties()` e `__invoke()` | Capitolo 5 |
| `make:node` | Nodo di workflow con lo stub `__invoke(Event, WorkflowState)` | Capitolo 13 |
| `make:event` | Classe evento che implementa `Event` | Capitolo 13 |

I generatori scrivono il file nel percorso implicato dalla tua mappatura PSR-4. `App\Agents\AssistantAgent` finisce in `src/Agents/AssistantAgent.php` per via della mappatura impostata nella Sezione 3.1. Se finisce in un posto inatteso, il tuo blocco di autoload è sbagliato.

### La posizione onesta sui generatori

Risparmiano digitazione e impongono le convenzioni sui nomi. È tutto il beneficio. Ogni classe che producono è normale PHP che potresti scrivere in novanta secondi, e in questo libro le scriviamo spesso a mano — perché chi ha solo generato un agent non sa davvero che cos'è un agent.

Usali quando sei produttivo. Non usarli come sostituto della comprensione della forma della classe.

### Punti chiave

- Quattro generatori: `make:agent`, `make:tool`, `make:node`, `make:event`.
- Unix vuole i backslash doppi; PowerShell no.
- Il percorso di output segue la tua mappatura PSR-4.

## 3.4 Il tuo primo agent

Questo è il primo codice eseguibile del libro.

### I tre metodi template

Una classe agent risponde a tre domande:

- `provider()` — con quale LLM parlo?
- `instructions()` — chi sono e come mi comporto?
- `tools()` — che cosa so davvero fare? *(opzionale; Capitolo 5)*

Tutto il resto — l'array dei messaggi, il ciclo, la cronologia, il dispatch dei tool — è ereditato.

### La classe

**`src/Agents/AssistantAgent.php`**

```php
<?php

declare(strict_types=1);

namespace App\Agents;

use NeuronAI\Agent\Agent;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Providers\Anthropic\Anthropic;

class AssistantAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return new Anthropic(
            key: $_ENV['ANTHROPIC_KEY'],
            model: $_ENV['ANTHROPIC_MODEL'],
        );
    }

    public function instructions(): string
    {
        return (string) new SystemPrompt(
            background: [
                'You are a technical assistant specialised in PHP development.',
                'You are talking to experienced developers. Do not explain basics unless asked.',
            ],
        );
    }
}
```

Questo è un agent completo. Quattro righe di configurazione vera.

::: {.callout .callout-warning}
[Nota sulla visibilità]{.callout-title}

La documentazione ufficiale mostra `instructions()` come `public` in alcuni esempi e `protected` in altri. Entrambe compaiono nella documentazione attuale. Usa quella che corrisponde alla classe base nella versione che installi — verifica con l'IDE o con `composer show` — e resta coerente in tutto il progetto. È il punto 8 dell'Appendice A.
:::

### Eseguirlo

**`examples/01-first-agent.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\AssistantAgent;
use NeuronAI\Chat\Messages\UserMessage;

$prompt = $argv[1] ?? 'Explain the difference between readonly and final in PHP 8, in three lines.';

$response = AssistantAgent::make()
    ->chat(new UserMessage($prompt))
    ->getMessage();

echo $response->getContent() . PHP_EOL;
```

```bash
php examples/01-first-agent.php "How do I implement a PSR-15 middleware without a framework?"
```

### Leggere la catena, pezzo per pezzo

```php
AssistantAgent::make()
```

Factory statica sulla classe base. Equivalente a `new AssistantAgent()` per un costruttore senza argomenti, e si legge meglio in una catena fluente. Quando il tuo agent prende argomenti nel costruttore — come farà `PersistentAgent` nella Sezione 4.3 — usa invece `new`.

```php
->chat(new UserMessage($prompt))
```

Esegue il ciclo della Sezione 1.2. Qui una sola iterazione, perché non ci sono tool. Nota che `chat()` restituisce un **oggetto risposta**, non il messaggio.

```php
->getMessage()
```

Estrae il messaggio dell'assistant dalla risposta.

::: {.callout .callout-warning}
[Cambiamento v2 → v3]{.callout-title}

Nelle versioni precedenti `chat()` restituiva direttamente il messaggio. In v3 devi chiamare `getMessage()`. È il secondo errore più comune quando si adatta codice d'esempio più vecchio, subito dopo i namespace.
:::

```php
$response->getContent()
```

Restituisce tutto il contenuto testuale del messaggio concatenato in un'unica stringa. La Sezione 4.1 spiega perché "concatenato" è la parola giusta: un messaggio può contenere più blocchi di contenuto.

### Due cose che andranno storte

**Undefined array key "ANTHROPIC_KEY"** — il file `.env` manca o non è caricato. La Sezione 3.7 costruisce `bootstrap.php` come si deve; per ora, verifica che il file esista e contenga la chiave.

**Errore 401 / di autenticazione** — la chiave è sbagliata, oppure la fatturazione sul provider è disabilitata. Controlla la console del provider prima di debuggare il codice.

### Punti chiave

- Tre metodi template; il ciclo è ereditato.
- `chat()` restituisce una risposta; `getMessage()` restituisce il messaggio; `getContent()` restituisce il testo.
- `::make()` per gli agent semplici, `new` quando il costruttore prende argomenti.

## 3.5 SystemPrompt: strutturare le istruzioni

Le istruzioni che i modelli seguono davvero hanno una struttura. NeuronAI te ne dà una in tre parti, e vale la pena capire perché esiste prima di usarla.

### Il problema del prompt-come-paragrafo

La maggior parte delle persone scrive il system prompt come un unico blocco di prosa:

```php
public function instructions(): string
{
    return 'You are a support assistant for an e-commerce store. Be polite and '
         . 'always answer in Italian and if you do not know something say so and '
         . 'never invent order numbers and keep answers short and use the tools '
         . 'when you need order data and format prices with the euro symbol.';
}
```

Tre problemi, in ordine crescente di gravità:

1. **Le istruzioni si perdono.** I modelli prestano attenzione in modo disomogeneo lungo un blocco lungo e indifferenziato; il vincolo che sta nel mezzo è quello che salta.
2. **Marcisce.** Sei mesi e quattro contributori dopo, sono 600 parole con tre contraddizioni che nessuno riesce a trovare.
3. **Non puoi cambiare una cosa sola.** Vuoi un formato di output diverso? Stai modificando una frase incastrata fra un'affermazione identitaria e una regola di comportamento.

### La struttura di NeuronAI

`SystemPrompt` accetta tre argomenti nominati e li rende in un prompt strutturato:

```php
use NeuronAI\Agent\SystemPrompt;

new SystemPrompt(
    background: [...],  // chi sei, quale dominio, che cosa non sei
    steps:      [...],  // la procedura da seguire
    output:     [...],  // il contratto per la risposta
);
```

Convertilo a stringa con `(string)` e restituiscilo da `instructions()`.

### Un esempio reale

```php
public function instructions(): string
{
    return (string) new SystemPrompt(
        background: [
            'You are an AI Agent specialised in writing YouTube video summaries.',
        ],
        steps: [
            'Get the URL of a YouTube video, or ask the user to provide one.',
            'Use the tools you have available to retrieve the transcription of the video.',
            'Write the summary.',
        ],
        output: [
            'Write a summary in a paragraph without using lists. Use fluent text only.',
            'After the summary add a list of three sentences as the three most '
            . 'important takeaways from the video.',
        ],
    );
}
```

È la forma della documentazione ufficiale, e vale la pena studiarla perché è corta. Ogni elemento dell'array è un'istruzione. Non un paragrafo: un'istruzione.

### Le tre sezioni, e che cosa va in ciascuna

**`background` — identità e dominio.**
Chi è l'agent, in quale campo opera, con chi sta parlando e — spesso la riga di maggior valore — che cosa *non* è. "Non sei un consulente legale e non devi interpretare clausole contrattuali" previene un'intera classe di fallimenti.

**`steps` — procedura.**
L'ordine delle operazioni. È qui che codifichi "cerca sempre prima di rispondere", che è l'istruzione anti-allucinazione più efficace di cui disponi. Se il tuo agent ha dei tool, la sezione steps è dove gli dici quando ricorrervi.

**`output` — il contratto della risposta.**
Lingua, formato, lunghezza, tono, formulazioni vietate. Tieni questa sezione esclusivamente sulla forma della risposta. La disciplina della separazione è ciò che rende manutenibile il prompt: puoi cambiare il formato di output senza toccare la personalità dell'agent o la sua procedura.

### Il confronto A/B che vale la pena fare da soli

Stesso agent, stessa domanda, due prompt.

**Versione A:**

```php
return 'You are a helpful PHP assistant.';
```

**Versione B:**

```php
return (string) new SystemPrompt(
    background: [
        'You are a technical assistant specialised in PHP development.',
        'You are talking to experienced developers.',
    ],
    steps: [
        'Identify the real problem behind the question, not only the stated one.',
        'If the question is ambiguous, ask the single most useful clarifying question.',
    ],
    output: [
        'Answer in English.',
        'Use fenced code blocks with the language declared.',
        'No preambles such as "Certainly!" or "Great question".',
        'Maximum 200 words unless code requires more.',
    ],
);
```

Chiedi a entrambe: *"How do I handle file uploads?"*

La versione A restituisce 600 parole che iniziano con "Great question!". La versione B chiede quale framework, oppure risponde in modo secco in PHP puro. La differenza è immediata, e arriva più forte di qualsiasi spiegazione: **il system prompt è la specifica, non il saluto.**

### Indicazioni pratiche

- Un'istruzione per elemento dell'array. Se un elemento contiene una "e", valuta di dividerlo.
- Preferisci istruzioni positive. "Rispondi in inglese" batte "non rispondere in italiano".
- I divieti che contano vanno tenuti, ma dichiara il confine, non un elenco di parole proibite.
- Versiona il prompt in Git e tratta le modifiche al prompt come modifiche al codice, con revisione. Vista la Sezione 1.5, un prompt riformulato è un cambiamento di comportamento che non puoi testare in regressione nel modo consueto.

### Punti chiave

- Tre sezioni: `background` (identità), `steps` (procedura), `output` (contratto).
- Un'istruzione per elemento dell'array.
- "Cerca prima di rispondere" appartiene a `steps` ed è il tuo miglior strumento anti-allucinazione.
- Le modifiche al prompt sono modifiche al codice: revisionale.

## 3.6 Cambio di provider: l'interfaccia si ripaga

È la cosa più persuasiva della Parte II: un agent, cinque motori, nessuna modifica al codice.

### La versione ingenua

```php
protected function provider(): AIProviderInterface
{
    return new Anthropic(key: '...', model: '...');
}
```

Funziona, ma ora ogni classe agent conosce il nome di un fornitore. Dieci agent, e cambiare provider è una modifica su dieci file più una code review.

### La factory

**`src/ProviderFactory.php`**

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
    public static function make(?string $driver = null): AIProviderInterface
    {
        $driver ??= env('NEURON_PROVIDER', 'ollama');

        return match ($driver) {
            'anthropic' => new Anthropic(
                key: self::require('ANTHROPIC_KEY'),
                model: env('ANTHROPIC_MODEL', 'claude-sonnet-4-5'),
            ),
            'openai' => new OpenAI(
                key: self::require('OPENAI_KEY'),
                model: env('OPENAI_MODEL', 'gpt-4.1-mini'),
            ),
            'gemini' => new Gemini(
                key: self::require('GEMINI_KEY'),
                model: env('GEMINI_MODEL', 'gemini-2.0-flash'),
            ),
            'mistral' => new Mistral(
                key: self::require('MISTRAL_KEY'),
                model: env('MISTRAL_MODEL', 'mistral-large-latest'),
            ),
            'ollama' => new Ollama(
                url: env('OLLAMA_URL', 'http://localhost:11434/api'),
                model: env('OLLAMA_MODEL', 'qwen2.5:7b'),
            ),
            default => throw new \InvalidArgumentException("Unknown provider: {$driver}"),
        };
    }

    private static function require(string $key): string
    {
        return env($key) ?? throw new \RuntimeException("Missing environment variable: {$key}");
    }
}
```

::: {.callout .callout-warning}
[Verifica l'import di Mistral]{.callout-title}

Una pagina della documentazione ufficiale mostra `use NeuronAI\Providers\Gemini\Mistral;`, che è un artefatto da copia-incolla. Il namespace corretto segue lo schema degli altri. Controlla la tua cartella `vendor/`: è esattamente il tipo di dettaglio su cui inciamperai dandone la colpa a te stesso.
:::

### Usarla

```php
protected function provider(): AIProviderInterface
{
    return ProviderFactory::make();
}
```

Ora ogni agent del progetto dice la stessa cosa: "dammi il provider configurato". I nomi dei fornitori compaiono in esattamente un file.

### L'esperimento

```bash
NEURON_PROVIDER=ollama    php examples/01-first-agent.php "What is a generator in PHP?"
NEURON_PROVIDER=anthropic php examples/01-first-agent.php "What is a generator in PHP?"
NEURON_PROVIDER=openai    php examples/01-first-agent.php "What is a generator in PHP?"
NEURON_PROVIDER=gemini    php examples/01-first-agent.php "What is a generator in PHP?"
```

Stesso codice. Quattro motori. Cronometrali: il divario di latenza fra locale e cloud è il dettaglio che modellerà le tue decisioni di progetto più avanti.

### Perché merita una sezione a sé

Tre argomenti, in ordine crescente di peso aziendale:

**Sviluppo gratuito.** Ollama su un portatile non costa nulla. Puoi completare ogni laboratorio delle Parti II, III e IV senza una carta di credito, che è la differenza fra finire un libro come questo e abbandonarlo al Capitolo 6.

**Stratificazione dei costi.** La Sezione 1.4 ti ha dato tre leve, e la terza era "modello più economico per passo". Un piccolo modello locale per classificazione e instradamento; un modello di frontiera solo per la sintesi finale. Qui è un argomento per chiamata, non un cambio di architettura.

**Rischio fornitore e giurisdizione.** I prezzi cambiano, i termini cambiano, i provider hanno disservizi, e alcuni clienti non possono mandare dati fuori da una certa giurisdizione — o fuori dal proprio edificio. Con una dipendenza rigida da un SDK ognuna di queste è un progetto. Qui ognuna è un valore di configurazione.

### Punti chiave

- Una factory; i nomi dei fornitori vivono in esattamente un file.
- Ollama rende gratuito seguire tutto ciò che c'è in questo libro.
- La scelta del provider diventa strategia di costo, gestione del rischio e conformità sulla residenza dei dati.

## 3.7 Segreti e ambiente

Caricare la configurazione in sicurezza ed evitare l'incidente della chiave trafugata che coglie un numero davvero alto di sviluppatori al primo progetto AI.

### bootstrap.php

**`bootstrap.php`**

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

`safeLoad()` invece di `load()`: non solleva eccezioni quando il file manca, che è ciò che vuoi su un server dove le variabili arrivano dall'ambiente stesso anziché da un file.

L'helper `env()` controlla `$_ENV`, poi `$_SERVER`, poi `getenv()`, e tratta la stringa vuota come assente — così una variabile presente ma vuota ricade sul default invece di produrre un fallimento confuso tre livelli più in basso.

### .env.example — committato

```dotenv
# anthropic | openai | gemini | mistral | ollama
NEURON_PROVIDER=ollama

ANTHROPIC_KEY=
ANTHROPIC_MODEL=claude-sonnet-4-5

OPENAI_KEY=
OPENAI_MODEL=gpt-4.1-mini

GEMINI_KEY=
GEMINI_MODEL=gemini-2.0-flash

MISTRAL_KEY=
MISTRAL_MODEL=mistral-large-latest

# Modelli locali: costo zero, ideali per i laboratori
OLLAMA_URL=http://localhost:11434/api
OLLAMA_MODEL=qwen2.5:7b

# Opzionale: tracing tramite inspector.dev
INSPECTOR_INGESTION_KEY=
```

```bash
cp .env.example .env
```

`.env.example` documenta la struttura e va committato. `.env` contiene i valori e non va committato mai.

### Il problema della chiave trafugata, detto chiaro

Le chiavi dei provider AI sono più pericolose della maggior parte delle credenziali perché sono direttamente monetizzabili. Scraper automatici sorvegliano i commit pubblici, e una chiave pubblicata su un repository pubblico viene tipicamente sfruttata nel giro di minuti o ore, addebitata a te a tariffe da modello di frontiera finché non te ne accorgi.

Quattro difese, tutte economiche:

1. **`.env` in `.gitignore` prima che il file esista.** Non dopo.
2. **Uno scanner di segreti in CI.** `gitleaks` o `trufflehog`, poche righe di configurazione del workflow.
3. **Limiti di spesa sul provider.** Ogni provider importante offre un tetto mensile rigido. Impostalo. Converte una catastrofe in una scocciatura.
4. **Chiavi separate per ambiente.** Dev, staging, produzione — così revocarne una non abbatte le altre.

Se ti capita di trafugare una chiave: revocala prima sul provider, poi ripulisci la cronologia. In quest'ordine. Riscrivere la cronologia Git su una chiave ancora attiva non serve a nulla.

### Non loggare mai il prompt alla cieca

Un dettaglio specifico delle applicazioni AI. I tuoi prompt conterranno qualunque cosa l'utente abbia digitato, che in un'applicazione di assistenza significa nomi, indirizzi, numeri d'ordine e occasionalmente dati di pagamento. Loggare i prompt completi per debugging è enormemente allettante e crea un problema di conformità nel momento in cui lo fai su larga scala.

Logga conteggi di token, modello, latenza, nomi dei tool e un ID di richiesta. Logga il *contenuto* del prompt solo dietro un flag esplicito, con una politica di conservazione, e mai per default in produzione. Ci torniamo nel Capitolo 23.

### I nomi dei modelli invecchiano

Ogni stringa di modello di questo capitolo prima o poi sarà sbagliata. Controlla l'elenco attuale dei modelli del provider invece di fidarti di un libro scritto mesi prima che tu lo legga — incluso questo.

### Punti chiave

- `safeLoad()` più un helper `env()` difensivo.
- `.env.example` committato, `.env` mai.
- Imposta oggi un limite di spesa rigido sul provider.
- Revoca prima di riscrivere la cronologia.
- Non loggare mai i prompt completi per default.

## Laboratorio 1 — Le fondamenta in PHP puro

Tutto ciò che c'è nelle Parti da II a IV gira sul progetto che costruisci qui. Non saltarlo: i laboratori successivi presuppongono esattamente questa struttura.

### Che cosa stai costruendo

Un progetto Composer con una factory di provider, un agent funzionante e uno script di benchmark che esegue lo stesso prompt su ogni provider che hai configurato.

### Passi

1. **Crea l'impalcatura**: la struttura di cartelle e il `composer.json` della Sezione 3.1. Esegui `composer dump-autoload` e conferma che non segnali errori.
2. **Installa** i tre pacchetti della Sezione 3.2. Verifica con la riga `class_exists`; se stampa `FAIL`, fermati e sistema la versione prima di proseguire.
3. **Scrivi `bootstrap.php`** e l'helper `env()` della Sezione 3.7. Copia `.env.example` in `.env`.
4. **Scrivi `src/ProviderFactory.php`** dalla Sezione 3.6.
5. **Scrivi l'agent.** Usa il `SystemPrompt` completo a tre sezioni invece di quello minimo della Sezione 3.4: è la versione su cui costruiscono i capitoli successivi.

```php
<?php

declare(strict_types=1);

namespace App\Agents;

use App\ProviderFactory;
use NeuronAI\Agent\Agent;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Chat\History\ChatHistoryInterface;
use NeuronAI\Chat\History\InMemoryChatHistory;
use NeuronAI\Providers\AIProviderInterface;

class AssistantAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return ProviderFactory::make();
    }

    public function instructions(): string
    {
        return (string) new SystemPrompt(
            background: [
                'You are a technical assistant specialised in PHP development.',
                'You are talking to experienced developers: no unrequested basics.',
            ],
            steps: [
                'Analyse the question and identify the real problem, not only the stated one.',
                'If the question is ambiguous, ask the single most useful clarifying question.',
                'Answer with code when code is the answer.',
            ],
            output: [
                'Answer in English.',
                'Use fenced code blocks with the language declared.',
                'No preambles such as "Certainly!" or "Great question".',
            ],
        );
    }

    protected function chatHistory(): ChatHistoryInterface
    {
        // Roughly 90 % of the model's context window: the trimmer needs headroom.
        return new InMemoryChatHistory(contextWindow: 120_000);
    }
}
```

6. **Eseguilo** con `examples/01-first-agent.php` dalla Sezione 3.4.
7. **Cambia provider** usando la variabile d'ambiente, almeno fra Ollama e un provider cloud.

### Il benchmark

Estendi `01-first-agent.php` perché iteri su ogni provider con credenziali configurate, esegua lo stesso prompt su ciascuno e stampi una tabella con provider, tempo trascorso e lunghezza della risposta. Conserva questo script: nel Capitolo 10 ci aggiungerai i conteggi di token da `$response->getUsage()`, e diventerà uno strumento davvero utile per scegliere un modello.

### Criteri di accettazione

- `composer dump-autoload` non produce avvisi, e `App\Agents\AssistantAgent` si risolve.
- Lo stesso prompt restituisce una risposta sensata con almeno due valori diversi di `NEURON_PROVIDER`, senza modificare alcun file PHP.
- `.env` non è tracciato. Verificalo con `git status --ignored` invece di darlo per scontato.
- Una chiave API mancante produce la tua `RuntimeException` con un messaggio utile, non un fallimento su valore nullo nelle profondità del provider.

### Se non funziona

I tre fallimenti che spiegano quasi tutti i problemi alla prima esecuzione: una mappatura PSR-4 sbagliata (classe non trovata), un namespace v2 in un'istruzione `use` (classe non trovata, ma una classe *del framework*) e un `.env` mai copiato da `.env.example` (chiave mancante). Controllali in quest'ordine.
