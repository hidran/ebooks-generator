# Capitolo 3 — Setup e il tuo primo agent

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

La versione eseguibile di ogni listato che segue si trova in [`chapters/Ch03`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch03), nel repository di accompagnamento. Clonalo, esegui `composer install` e gli esempi funzionano su un Ollama locale senza alcuna API key.
:::

## 3.1 Impalcatura del progetto

Costruiremo un progetto pulito in PHP puro che porterà avanti ogni esempio delle Parti II, III e IV. Niente framework, niente magia.

### Perché prima PHP puro

Passerai la Parte V dentro Laravel, dove il container ti consegna un agent già configurato e un comando artisan genera le tue classi. Quella comodità vale la pena — ma solo dopo aver visto che cosa nasconde. Tutto ciò che fa l'SDK Laravel, l'avrai già fatto a mano.

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
        "php": "^8.5"
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
composer require neuron-core/neuron-ai vlucas/phpdotenv
```

**`neuron-core/neuron-ai`** — il framework. Richiede l'estensione `curl` e ben poco altro: la sua unica dipendenza Composer è l'interfaccia PSR-14 dell'event dispatcher.

**`vlucas/phpdotenv`** — legge un file `.env` nell'ambiente. Laravel lo include; il PHP puro no. Senza, dovresti scrivere le chiavi API nel codice, cosa che non faremo.

**PHP 8.5.** NeuronAI in sé gira su PHP 8.1 o superiore, ma il codice di questo libro richiede PHP 8.5, quindi controlla `php -v` prima di andare avanti. Strada facendo incontrerai una manciata di funzionalità della 8.5: l'operatore pipe `|>`, `clone($object, [...])` per copiare un oggetto readonly cambiando alcune proprietà, l'attributo `#[\NoDiscard]`, `array_first()` e `array_last()`, e l'estensione URI integrata. Sono usate dove rendono il codice più chiaro, non ovunque, e ciascuna è spiegata la prima volta che compare.

Nota che cosa manca: un pacchetto client HTTP. NeuronAI non dipende da Guzzle né da nessun altro: ogni provider, vector store e toolkit parla HTTP attraverso il `CurlHttpClient` del framework, ed è per questo che `ext-curl` è un requisito obbligatorio. Quando i nostri tool chiameranno API esterne nel Capitolo 5, riuseranno lo stesso client, quindi il progetto non ha bisogno di altro.

Controlla l'estensione prima di ogni altra cosa:

```bash
php -m | grep -i curl
```

Nessun output significa niente `curl`, e la prima chiamata a un provider fallisce. Sulla maggior parte delle distribuzioni Linux è un pacchetto separato (`php8.5-curl` o simile); su macOS con il PHP di Homebrew è già incluso.

::: {.callout .callout-tip}
[Quando vuoi comunque Guzzle]{.callout-title}

Se la tua applicazione fa già passare l'HTTP in uscita attraverso un `HandlerStack` di Guzzle — per i retry, un proxy aziendale, il logging delle richieste — puoi far passare dallo stesso stack anche il traffico verso i provider. Richiedi tu stesso `guzzlehttp/guzzle`, poi passa l'adapter di NeuronAI, `NeuronAI\HttpClient\Guzzle\GuzzleHttpClient`, a qualunque provider con `setHttpClient()`. Il default non ha bisogno di nulla di tutto ciò; l'adapter c'è per quando vuoi un'unica policy HTTP per tutta l'applicazione.
:::

### Fissa la versione

```json
"require": {
    "php": "^8.5",
    "neuron-core/neuron-ai": "^4.0.3",
    "vlucas/phpdotenv": "^5.6"
}
```

Il vincolo dice: 4.0.3, la release su cui questo libro è stato scritto ed eseguito, oppure una 4.x successiva. **Committa `composer.lock` in un repository didattico.** Non è il consiglio abituale per le librerie: è deliberato. Chi seguirà questo libro fra un anno deve ottenere la stessa API su cui è stato scritto. Senza il lock file otterrà quello a cui `^4.0.3` si risolve quel giorno, e se un rilascio minore ha cambiato una firma otterrà un errore su cui nessuno può aiutarlo. La Sezione 27.1 fa un passo in più per un'applicazione che metti in produzione: richiedi la versione esatta, così che un aggiornamento non la sposti mai senza una decisione.

### Verifica

```bash
php -r "require 'vendor/autoload.php'; echo interface_exists(NeuronAI\Chat\History\MessageStoreInterface::class) ? 'OK' : 'FAIL';"
```

L'interfaccia che verifica è arrivata con la release 4.0, quindi `OK` significa che hai l'API su cui è scritto questo libro e `FAIL` significa un pacchetto più vecchio. Controlla con:

```bash
composer show neuron-core/neuron-ai | head -5
```

### Due parole su versioni e documentazione

Il codice d'esempio che trovi su internet viene da diverse generazioni di NeuronAI, e il codice scritto per versioni precedenti fallisce in due modi diversi.

Il codice più vecchio usa namespace che non esistono più — `NeuronAI\Agent` dove questo libro ha `NeuronAI\Agent\Agent`, `NeuronAI\SystemPrompt` dove ha `NeuronAI\Agent\SystemPrompt` — e fallisce sull'istruzione `use`. Il codice più recente è più subdolo: gli import si risolvono, e poi un metodo non esiste o restituisce qualcosa di diverso. I punti in cui lo incontrerai per primi sono ciò che restituisce `chat()` e il modo in cui una run riceve il suo thread ID (Sezione 3.4), il modo in cui si conservano le conversazioni (Capitolo 4), il modo in cui un tool dichiara nome e descrizione (Capitolo 5) e il modo in cui si avvia un workflow (Capitolo 13).

Parti della documentazione ufficiale, diversi articoli di blog e la maggior parte del materiale di terze parti mostrano ancora codice più vecchio. Quando trovi codice d'esempio che non corrisponde a questo libro, controlla a quale versione punta prima di dare per scontato che qualcosa sia rotto. È la fonte di confusione più comune per chi arriva dai tutorial.

### Punti chiave

- `composer require neuron-core/neuron-ai` con `ext-curl`; Guzzle è opzionale. Il codice del libro richiede PHP 8.5.
- Fissa la versione e committa `composer.lock` nei repository didattici.
- Il codice scritto per versioni precedenti fallisce sui namespace o su tipi di ritorno e firme cambiati. Controlla la versione prima di debuggare.

## 3.3 La CLI del framework

I generatori creano componenti del framework con la struttura corretta. Vale la pena sapere che cosa producono, perché queste classi vorrai anche scriverle a mano.

### Il binario

Installare il pacchetto ti dà un eseguibile in `vendor/bin/neuron`.

```bash
./vendor/bin/neuron
```

Eseguito senza argomenti, elenca i suoi comandi: una famiglia di generatori `make:*`, più `evaluation`, che esegue le suite di valutazione del Capitolo 10.

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
| `make:agent` | Classe che estende `Agent` con gli stub `provider()`, `instructions()`, `tools()` e `middleware()` | Capitolo 3 |
| `make:tool` | Classe che estende `Tool` con le proprietà `$name`/`$description`, `properties()` e `__invoke()` | Capitolo 5 |
| `make:rag` | Classe che estende `RAG` | Capitolo 11 |
| `make:workflow` | Classe che estende `Workflow` con lo stub `nodes()` | Capitolo 13 |
| `make:node` | Nodo di workflow con lo stub `__invoke(StartEvent, WorkflowState)` | Capitolo 13 |
| `make:event` | Classe evento che implementa `Event` | Capitolo 13 |
| `make:middleware` | Classe che implementa `WorkflowMiddleware` con `before()` e `after()` | Capitolo 15 |
| `make:evaluators` | Classe evaluator per il runner `evaluation` | Capitolo 10 |

I generatori scrivono il file nel percorso implicato dalla tua mappatura PSR-4. `App\Agents\AssistantAgent` finisce in `src/Agents/AssistantAgent.php` per via della mappatura impostata nella Sezione 3.1. Se finisce in un posto inatteso, il tuo blocco di autoload è sbagliato.

### La posizione onesta sui generatori

Risparmiano digitazione e impongono le convenzioni sui nomi. È tutto il beneficio. Ogni classe che producono è normale PHP che potresti scrivere in novanta secondi, e in questo libro le scriviamo spesso a mano — perché chi ha solo generato un agent non sa davvero che cos'è un agent.

Leggi quello che producono prima di costruirci sopra. Un generatore scrive un punto di partenza, non una classe finita: l'agent generato, per esempio, restituisce un provider `Anthropic` con `key: $_ENV['ANTHROPIC_API_KEY']` e `model: $_ENV['ANTHROPIC_MODEL']` là dove deve andare la tua configurazione (allinea il nome della variabile d'ambiente a quello che usa questo libro, `ANTHROPIC_KEY`), e un tool generato porta il nome della sua classe finché non gli dai un nome e una descrizione veri.

Usali quando sei produttivo. Non usarli come sostituto della comprensione della forma della classe.

### Punti chiave

- I generatori seguono i mattoni del framework: agent, tool, RAG, workflow, nodo, evento, middleware, evaluator.
- Unix vuole i backslash doppi; PowerShell no.
- Il percorso di output segue la tua mappatura PSR-4.

## 3.4 Il tuo primo agent

Questo è il primo codice eseguibile del libro.

### I tre metodi template

Una classe agent risponde a tre domande:

- `provider()` — con quale LLM parlo?
- `instructions()` — chi sono e come mi comporto?
- `tools()` — che cosa so davvero fare? *(opzionale; Capitolo 5)*

Tutto il resto — l'array dei messaggi, il ciclo, la cronologia, il dispatch dei tool — è ereditato. La classe base è essa stessa un workflow (Sezione 2.3), e questi tre metodi sono il modo in cui configuri i nodi che contiene già.

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

    protected function instructions(): string
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
[Nota sulla firma]{.callout-title}

La classe base dichiara `protected function instructions(): SystemMessage|string`. Restituire una semplice `string`, come fa questa classe, è un restringimento legittimo di quel tipo di ritorno, ed è ciò che scrive il generatore del framework stesso; la Sezione 3.5 mostra quando restituiresti invece un `SystemMessage`. Alcuni esempi della documentazione dichiarano il metodo `public`. Anche questo PHP lo accetta, perché un override può ampliare la visibilità, ma tienilo `protected` come fa la classe base e resta coerente in tutto il progetto.
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

// An agent always runs on a conversation thread, and the framework never
// invents one: without setThreadId() the call below throws an AgentException.
$state = AssistantAgent::make()
    ->setThreadId('demo')
    ->chat(new UserMessage($prompt));

echo $state->getMessage()?->getContent() . PHP_EOL;
```

```bash
php examples/01-first-agent.php "How do I implement a PSR-15 middleware without a framework?"
```

### Leggere la catena, pezzo per pezzo

```php
AssistantAgent::make()
```

Factory statica sulla classe base. Equivalente a `new AssistantAgent()`, e si legge meglio in una catena fluente. Inoltra i suoi argomenti al costruttore, il primo dei quali è `workflowId:` — lo stesso thread ID che imposta la riga successiva, per quando lo conosci già alla costruzione. Il Laboratorio 2 del Capitolo 4 lo passa così.

```text
->setThreadId('demo')
```

Dice a quale conversazione appartiene questa run. Ogni run di un agent ha bisogno di un thread ID, e NeuronAI non ne inventa mai uno: togli questa riga e `chat()` lancia una `AgentException` prima che parta qualsiasi richiesta. Una singola domanda non ha una conversazione a cui tornare, quindi qui va bene una stringa fissa qualunque; è nel Capitolo 4 che il thread comincia a contare.

```text
->chat(new UserMessage($prompt))
```

Esegue il ciclo della Sezione 1.2. Qui una sola iterazione, perché non ci sono tool. `chat()` esegue il workflow dell'agent fino alla fine e restituisce il suo **stato** finale, un `AgentState`, non il messaggio. Lo stato è l'intero esito della run: la risposta del provider, i messaggi prodotti da questa run e, quando una run si mette in pausa per aspettare un essere umano (Capitolo 15), il motivo della pausa.

```php
$state->getMessage()
```

Legge dallo stato l'ultimo messaggio del modello. Il suo tipo di ritorno è nullable — una run che si ferma prima che una qualunque inferenza abbia prodotto una risposta non ha alcun messaggio — ed è per questo che c'è `?->`. Un messaggio però non è la prova di una run conclusa: quando una run va in pausa per l'approvazione di un tool (Sezione 5.10), `getMessage()` restituisce il messaggio di tool call del modello, non una risposta, ed è `$state->isInterrupted()` a distinguere i due casi. L'agent di questo capitolo non va mai in pausa, ma il tipo non lo sa, e nemmeno il tuo analizzatore statico.

::: {.callout .callout-warning}
[Adattare codice d'esempio più vecchio]{.callout-title}

`chat()` restituisce l'`AgentState`. I tutorial scritti per versioni precedenti trattano il suo risultato come il messaggio stesso, ci chiamano sopra `->run()` o dichiarano il tipo `AgentHandler`; niente di tutto ciò gira qui. È il secondo errore più comune quando si adatta codice d'esempio più vecchio, subito dopo i namespace.
:::

```text
->getContent()
```

Restituisce tutto il contenuto testuale del messaggio unito in un'unica stringa. La Sezione 4.1 spiega perché "unito" è la parola giusta: un messaggio può contenere più blocchi di contenuto.

### Due cose che andranno storte

**Undefined array key "ANTHROPIC_KEY"** — il file `.env` manca o non è caricato. La Sezione 3.7 costruisce `bootstrap.php` come si deve; per ora, verifica che il file esista e contenga la chiave.

**Errore 401 / di autenticazione** — la chiave è sbagliata, oppure la fatturazione sul provider è disabilitata. Controlla la console del provider prima di debuggare il codice.

### Punti chiave

- Tre metodi template; il ciclo è ereditato.
- `chat()` restituisce l'`AgentState` finale della run; `getMessage()` restituisce il messaggio (o `null` quando nessuna inferenza ne ha prodotto uno); `getContent()` restituisce il testo.
- Ogni run ha bisogno di un thread ID — `setThreadId()`, oppure `workflowId:` passato a `::make()` — e il framework non ne inventa mai uno. Una run in pausa si riconosce con `isInterrupted()`, non da un messaggio null.

## 3.5 SystemPrompt: strutturare le istruzioni

Le istruzioni che i modelli seguono davvero hanno una struttura. NeuronAI te ne dà una in tre parti, e vale la pena capire perché esiste prima di usarla.

### Il problema del prompt-come-paragrafo

La maggior parte delle persone scrive il system prompt come un unico blocco di prosa:

```php
protected function instructions(): string
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
    background: ['You are ...'],   // who you are, what domain, what you are not
    steps:      ['First ...'],     // the procedure to follow
    output:     ['Answer in ...'], // the contract for the response
);
```

Convertilo a stringa con `(string)` e restituiscilo da `instructions()`. Ogni argomento viene reso come una sezione del prompt con una propria intestazione. Ce n'è un quarto, opzionale, `toolsUsage:`, per le regole su quando e come chiamare i tool — utile quando l'agent avrà dei tool da chiamare (Capitolo 5).

### Un esempio reale

```php
protected function instructions(): string
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

### Le stringhe bastano — finché non vuoi il caching

Qualunque cosa restituisca `instructions()`, l'agent la conserva come `SystemMessage`: un messaggio i cui blocchi di contenuto sono il system prompt. Una stringa diventa un blocco. È tutto ciò che serve agli agent di questo libro, ed è per questo che restituiscono stringhe. Quando vuoi riavere le istruzioni effettive — in un test, o per registrare nei log quale versione del prompt ha girato — `$agent->getInstructions()` restituisce quel `SystemMessage`, e `->getContent()` su di esso rende il testo. (I tutorial scritti per versioni precedenti chiamano `resolveInstructions()` per questo; il metodo non esiste nella v4.)

Restituisci tu stesso un `SystemMessage` quando vuoi più di un blocco, e il motivo abituale è il prompt caching. Un prompt lungo e stabile viene rispedito a ogni turno e a ogni iterazione dei tool; i provider che supportano il caching (Anthropic e l'API OpenAI Responses, fra i provider di NeuronAI) fatturano un prefisso in cache a una frazione del normale prezzo di input. Marca come cached il blocco stabile e tieni la parte volatile in un blocco a sé:

```php
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Chat\Messages\ContentBlocks\SystemContent;
use NeuronAI\Chat\Messages\SystemMessage;

protected function instructions(): SystemMessage
{
    return new SystemMessage([
        (new SystemContent((string) new SystemPrompt(
            background: ['You are a technical assistant specialised in PHP development.'],
        )))->cache(),
        new SystemContent('Today is ' . date('Y-m-d')),
    ]);
}
```

I provider senza caching inviano i blocchi come testo normale, quindi il codice resta portabile. L'aritmetica della Sezione 1.4 dice quando ne vale la pena: più lungo è il prompt statico e più chiamate ci sono per conversazione, maggiore è il risparmio. Sotto la dimensione minima memorizzabile in cache di un provider — da qualche centinaio a qualche migliaio di token, a seconda del modello — il marcatore viene ignorato in silenzio, quindi il prompt di due righe qui sopra non mette in cache nulla: lo schema ripaga su prompt che si misurano in pagine.

### Punti chiave

- Tre sezioni: `background` (identità), `steps` (procedura), `output` (contratto).
- Un'istruzione per elemento dell'array.
- "Cerca prima di rispondere" appartiene a `steps` ed è il tuo miglior strumento anti-allucinazione.
- `instructions()` può restituire una stringa o un `SystemMessage`; usa il secondo per dividere il prompt in blocchi e mettere in cache quello stabile.
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
use Uri\Rfc3986\Uri;

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
                url: self::ollamaUrl(),
                model: env('OLLAMA_MODEL', 'qwen2.5:7b'),
                // Ollama truncates a prompt to num_ctx instead of rejecting it,
                // and its default is small: ask for the window Section 4.4 budgets.
                parameters: ['options' => ['num_ctx' => 32_768]],
            ),
            default => throw new \InvalidArgumentException("Unknown provider: {$driver}"),
        };
    }

    private static function require(string $key): string
    {
        return env($key) ?? throw new \RuntimeException("Missing environment variable: {$key}");
    }

    private static function ollamaUrl(): string
    {
        $raw = env('OLLAMA_URL', 'http://localhost:11434/api');
        $url = Uri::parse($raw);

        if ($url?->getHost() === null) {
            throw new \InvalidArgumentException("OLLAMA_URL [{$raw}] is not an absolute URL.");
        }

        return $url->toString();
    }
}
```

`ollamaUrl()` usa l'estensione URI integrata di PHP 8.5: `Uri\Rfc3986\Uri::parse()` analizza il valore secondo le regole della RFC 3986 e restituisce `null` quando non ci riesce, così un `OLLAMA_URL` scritto male fallisce qui, con il suo nome nel messaggio, invece di emergere più tardi come un opaco errore cURL.

L'argomento `parameters:` sul ramo Ollama è il modo in cui qualunque provider riceve le opzioni di richiesta che la factory non modella. Qui imposta `num_ctx`, la dimensione del contesto di Ollama. Lasciato a sé stesso, Ollama non rifiuta un prompt troppo lungo: lo tronca, in silenzio, a un valore predefinito molto più piccolo di quello che il modello può gestire. La Sezione 4.4 torna su quel numero.

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

Stesso codice. Quattro dei cinque motori. Cronometrali: il divario di latenza fra locale e cloud è il dettaglio che modellerà le tue decisioni di progetto più avanti.

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

# Local models: no cost, ideal for the labs
OLLAMA_URL=http://localhost:11434/api
OLLAMA_MODEL=qwen2.5:7b

# Optional: tracing via inspector.dev (wired up in Chapter 10)
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
2. **Installa** i due pacchetti della Sezione 3.2, dopo aver controllato che `ext-curl` sia caricata. Verifica con la riga di controllo di quella sezione; se stampa `FAIL`, fermati e sistema la versione prima di proseguire.
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
                'You are a technical assistant specialised in PHP development.',
                'You are talking to experienced developers: no unrequested basics.',
            ],
            steps: [
                'Analyse the question and identify the real problem, not only the stated one.',
                'If the question is ambiguous, ask the single most useful clarifying question.',
            ],
            output: [
                'Answer in English.',
                'Use fenced code blocks with the language declared.',
                'No preambles such as "Certainly!" or "Great question".',
                'Maximum 200 words unless the code requires more.',
            ],
        );
    }

    protected function contextWindow(): int
    {
        // No store is declared, so the agent keeps the conversation in an
        // InMemoryMessageStore of its own: it lasts as long as this instance.
        // Roughly 90 % of a 32K local model's window: the trimmer needs headroom.
        return 29_000;
    }
}
```

6. **Eseguilo** con `examples/01-first-agent.php` dalla Sezione 3.4.
7. **Cambia provider** usando la variabile d'ambiente, almeno fra Ollama e un provider cloud.

### Il benchmark

Estendi `01-first-agent.php` perché iteri su ogni provider con credenziali configurate, esegua lo stesso prompt su ciascuno e stampi una tabella con provider, tempo trascorso e lunghezza della risposta. Conserva questo script: nel Capitolo 10 ci aggiungerai i conteggi di token da `$state->getMessage()?->getUsage()`, e diventerà uno strumento davvero utile per scegliere un modello.

### Criteri di accettazione

- `composer dump-autoload` non produce avvisi, e `App\Agents\AssistantAgent` si risolve.
- Lo stesso prompt restituisce una risposta sensata con almeno due valori diversi di `NEURON_PROVIDER`, senza modificare alcun file PHP.
- `.env` non è tracciato. Verificalo con `git status --ignored` invece di darlo per scontato.
- Una chiave API mancante produce la tua `RuntimeException` con un messaggio utile, non un fallimento su valore nullo nelle profondità del provider.

### Se non funziona

I quattro fallimenti che spiegano quasi tutti i problemi alla prima esecuzione: una mappatura PSR-4 sbagliata (classe non trovata), un namespace di una versione precedente in un'istruzione `use` (classe non trovata, ma una classe *del framework*), una build di PHP senza `ext-curl` (la prima chiamata a un provider fallisce) e un `.env` mai copiato da `.env.example` (chiave mancante). Controllali in quest'ordine.
