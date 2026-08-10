# Capitolo 4 — Messaggi e memoria

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

Questo capitolo è concettuale e non ha codice a sé stante, ma il repository di accompagnamento [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) contiene le versioni eseguibili di tutto ciò che il libro costruisce.
:::

## 4.1 Il modello dei messaggi

NeuronAI ha un layer unificato per i messaggi — ruoli, blocchi di contenuto, metadati — ed è il pezzo che fa funzionare davvero lo scambio di provider, invece di limitarsi a farlo sembrare possibile.

### Perché esiste un layer unificato

Ogni provider ha la propria forma di richiesta e risposta. OpenAI, Anthropic, Gemini e Ollama differiscono nel modo di rappresentare i ruoli, di allegare immagini, di restituire chiamate a tool, di esporre le tracce di ragionamento.

La risposta di NeuronAI è un'unica astrazione dei messaggi che si mappa su tutti. È ciò che rende la Sezione 3.6 più di un gioco di prestigio: lo scambio funziona perché il layer dei messaggi assorbe le differenze. Senza, "cambia una riga per cambiare provider" sarebbe falso nel momento in cui alleghi un'immagine o leggi una chiamata a tool.

### Che cos'è un messaggio

Tre parti:

- **Ruolo** — chi sta parlando: user, assistant, tool
- **Blocchi di contenuto** — il payload vero e proprio
- **Metadati** — informazioni aggiuntive dalla risposta del provider

### Blocchi di contenuto

È la parte che quasi tutti si perdono. Un messaggio non contiene una stringa. Contiene un **elenco ordinato di blocchi di contenuto**, ciascuno dei quali implementa un'interfaccia `ContentBlock`. NeuronAI fornisce tipi di blocco per testo, ragionamento, immagine, file, audio e video, e mappa automaticamente ciascuno nel formato corretto del provider.

Passare una stringa al costruttore crea semplicemente il primo blocco di testo:

```php
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Chat\Messages\ContentBlocks\TextContent;

// A string constructor argument becomes the first TextContent block
$message = new UserMessage('Hi');

$message->addContent(new TextContent('My name is John.'));
$message->addContent(new TextContent('Answer as a professional concierge.'));

echo $message->getContent();
// Hi My name is John. Answer as a professional concierge.

$blocks = $message->getTextBlocks();
```

Ora `getContent()` ha senso: concatena tutti i blocchi di testo in un'unica stringa. È una comodità, non la struttura sottostante.

### Leggere una risposta come si deve

```php
$response = MyAgent::make()->chat(new UserMessage('...'))->getMessage();

// Convenience: all text blocks joined
echo $response->getContent();
```

Ma con un modello di ragionamento la risposta porta più del semplice testo:

```php
use NeuronAI\Chat\Messages\ContentBlocks\ReasoningContent;
use NeuronAI\Chat\Messages\ContentBlocks\TextContent;

foreach ($response->getContentBlocks() as $block) {
    echo match ($block::class) {
        ReasoningContent::class => "Reasoning: {$block->content}\n\n",
        TextContent::class      => $block->content,
        default                 => '',
    };
}
```

NeuronAI cattura automaticamente i passaggi di ragionamento del modello come blocco distinto. Se chiami solo `getContent()`, non li vedi mai. Per debuggare un agent che ha preso una decisione strana, il blocco di ragionamento è spesso la risposta.

### Costruire una conversazione a mano

A volte hai già una conversazione — dal tuo database, o da un'importazione — e devi inizializzare l'agent con quella. Passa un array a `chat()`:

```php
use NeuronAI\Chat\Enums\MessageRole;
use NeuronAI\Chat\Messages\Message;

$message = MyAgent::make()
    ->chat([
        new Message(MessageRole::USER, 'Hi, my company is called Inspector.dev'),
        new Message(MessageRole::ASSISTANT, 'Great, how can I assist you today?'),
        new Message(MessageRole::USER, 'What is the name of the company I work for?'),
    ])
    ->getMessage();

echo $message->getContent();
// You work for Inspector.dev
```

L'ultimo messaggio dell'array è trattato come il più recente. È la via d'uscita per qualunque situazione in cui la conversazione non vive nel componente di cronologia di NeuronAI: uno schema legacy, l'export di un altro sistema, una sessione ricostruita.

### Anteprima multimodale

Allegare un documento usa lo stesso meccanismo — un altro blocco di contenuto:

```php
use NeuronAI\Chat\Messages\ContentBlocks\FileContent;
use NeuronAI\Chat\Enums\SourceType;

$message = new UserMessage('Summarize this document');

$message->addContent(
    new FileContent(
        content: base64_encode(file_get_contents(__DIR__ . '/invoice.pdf')),
        sourceType: SourceType::BASE64,
        mediaType: 'application/pdf',
    )
);
```

`SourceType` supporta `BASE64`, `URL` e `ID`. Quest'ultimo conta per i costi: molti provider ti permettono di caricare un file una volta sulla loro piattaforma e poi referenziarlo per ID, evitando di ricaricare il payload a ogni iterazione del ciclo dell'agent. Vista l'aritmetica dei token della Sezione 1.4, è un risparmio sostanziale su qualunque esecuzione multi-passo che coinvolga un documento. Il Capitolo 8 lo tratta come si deve.

::: {.callout .callout-warning}
[Cambiamento in v3]{.callout-title}

Le versioni precedenti usavano `addAttachment(new Image($url, ...))`. La v3 l'ha sostituito con il sistema dei blocchi di contenuto. I tutorial più vecchi mostrano la vecchia chiamata. Correlato: la documentazione è incoerente sui nomi delle classi dei blocchi — `TextBlock`/`FileBlock` compaiono in alcuni punti dove le classi distribuite sono `TextContent`/`FileContent`, e un esempio importa `AudioContent` mentre istanzia `FileContent`. Vedi i punti 10 e 11 dell'Appendice A.
:::

### Punti chiave

- Un messaggio è ruolo + blocchi di contenuto + metadati; non una stringa.
- `getContent()` concatena i blocchi di testo; `getContentBlocks()` ti dà tutto, ragionamento incluso.
- Passa un array di oggetti `Message` per inizializzare una conversazione esistente.
- Il layer unificato dei messaggi è il motivo per cui lo scambio di provider sopravvive al contatto con immagini, file e chiamate a tool.

## 4.2 Il modello non ha memoria

L'assenza di stato è un vincolo di progetto, non una limitazione da aggirare. Questa sezione serve a interiorizzarla, perché quasi ogni confusione sulla "memoria" si dissolve quando lo fai.

### La dimostrazione

```php
use NeuronAI\Agent\Agent;
use NeuronAI\Chat\Messages\UserMessage;

$message = Agent::make()
    ->chat(new UserMessage("What's my name?"))
    ->getMessage();

echo $message->getContent();
// I'm sorry, I don't know your name.
```

Ora tieni la stessa istanza:

```php
$agent = Agent::make();

$agent->chat(new UserMessage('Hi, my name is Valerio!'));

$message = $agent->chat(new UserMessage('Do you remember my name?'))->getMessage();
echo $message->getContent();
// Sure, your name is Valerio!
```

La lettura ovvia — "l'agent ha imparato il mio nome" — è sbagliata, e correggerla è il punto di questa sezione.

### Che cosa è successo davvero

La seconda chiamata ha mandato al provider questo:

```
system:    <instructions>
user:      Hi, my name is Valerio!
assistant: Hi Valerio, nice to meet you...
user:      Do you remember my name?
```

Il modello non ha ricordato nulla. **È il tuo processo ad aver rimandato la trascrizione.** Dal lato del provider non c'è alcuna sessione, nessun record utente, nulla di persistito fra una richiesta e l'altra. Il modello legge l'intera conversazione da capo, ogni volta, e risponde come se ricordasse.

Il componente NeuronAI che conserva la trascrizione e la rimanda è `ChatHistory`. È tutto ciò che "memoria" significa a questo livello.

### Quattro conseguenze da dichiarare

**1. La memoria costa denaro a ogni turno.**
Il ventesimo turno rimanda diciannove scambi precedenti. È il meccanismo dietro la tabella dei costi della Sezione 1.4, ed è il motivo per cui le conversazioni lunghe diventano care anche quando i singoli messaggi sono brevi.

**2. La memoria è limitata dalla context window.**
Non è un database che cresce. È un buffer con un tetto rigido. Prima o poi qualcosa va scartato, e l'unica domanda è cosa e come — Sezione 4.4.

**3. La memoria è interamente sotto il tuo controllo.**
Il che è liberatorio, una volta accettato. Puoi modificare la cronologia, iniettare un riassunto, eliminare turni irrilevanti, tenere fissato in modo permanente un fatto di livello sistema. Niente è sacro: è il tuo array.

**4. L'assenza di stato è il motivo per cui la scalabilità orizzontale è facile.**
Qualunque web server può servire qualunque richiesta, purché possa caricare la trascrizione. Non c'è affinità di sessione verso un provider. Carica una `ChatHistory` da uno storage condiviso e qualunque nodo può proseguire qualunque conversazione. È un vantaggio architetturale reale, ed è insolito che una funzionalità dall'aria stateful scali così pulitamente.

### Il modello mentale da tenere

Il modello è una **funzione pura**: trascrizione in ingresso, messaggio successivo in uscita. Tutto ciò che sembra memoria, persistenza della personalità o apprendimento è il tuo codice che sceglie che cosa entra nella trascrizione.

Ogni tecnica nel resto del libro — trimming della cronologia, riassunti, RAG, store di memoria a lungo termine — è una risposta diversa a una sola domanda: **che cosa mettiamo nella trascrizione?**

### Punti chiave

- Nessuna sessione lato server; la trascrizione viene rimandata a ogni turno.
- La memoria costa token a ogni turno ed è limitata dalla context window.
- La cronologia è il tuo array: modificabile, iniettabile, sostituibile.
- Il modello è una funzione pura della trascrizione.

## 4.3 Implementazioni di ChatHistory

### L'interfaccia

```php
NeuronAI\Chat\History\ChatHistoryInterface
```

Ne registri una implementando `chatHistory()` sul tuo agent. Il default, se non implementi nulla, è in memoria.

### InMemoryChatHistory

```php
use NeuronAI\Chat\History\ChatHistoryInterface;
use NeuronAI\Chat\History\InMemoryChatHistory;

protected function chatHistory(): ChatHistoryInterface
{
    return new InMemoryChatHistory(contextWindow: 150_000);
}
```

Un array. Vive solo per il processo PHP corrente. Corretta per: script one-shot, endpoint API stateless in cui la conversazione la tieni tu, e test.

Ricorda che in una normale richiesta web PHP muore alla fine della risposta. La cronologia in memoria in contesto web significa **nessuna memoria fra una richiesta e l'altra**, cosa che sorprende davvero spesso chi è abituato a runtime a lunga esecuzione.

### FileChatHistory

```php
use NeuronAI\Chat\History\FileChatHistory;

protected function chatHistory(): ChatHistoryInterface
{
    return new FileChatHistory(
        directory: '/home/app/storage/neuron',
        key: 'THREAD_ID',
        contextWindow: 150_000,
    );
}
```

`directory` è un percorso assoluto; `key` identifica la conversazione. Usa un ID utente per una conversazione per utente, o un ID di thread per averne molte.

Corretta per: strumenti CLI, applicazioni su singolo server, prototipi. Non corretta per: deploy multi-server senza storage condiviso, o alta concorrenza — due scritture simultanee sulla stessa chiave non finiranno bene.

### SQLChatHistory

Crea prima la tabella:

```sql
CREATE TABLE IF NOT EXISTS chat_history (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  thread_id VARCHAR(255) NOT NULL,
  messages LONGTEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  UNIQUE KEY uk_thread_id (thread_id),
  INDEX idx_thread_id (thread_id)
);
```

```php
use NeuronAI\Chat\History\SQLChatHistory;

protected function chatHistory(): ChatHistoryInterface
{
    return new SQLChatHistory(
        thread_id: 'THREAD_ID',
        pdo: new \PDO('mysql:host=localhost;dbname=DB;charset=utf8mb4', 'user', 'pass'),
        table: 'chat_history',
        contextWindow: 150_000,
    );
}
```

Prende un `PDO` semplice, quindi funziona in qualunque applicazione PHP indipendentemente dal framework. In Laravel passeresti `\DB::connection()->getPdo()`; in Symfony, `$connection->getNativeConnection()` da una connessione Doctrine. Puoi aggiungere colonne — una chiave esterna verso la tua tabella utenti, per esempio — purché la struttura di base resti.

### EloquentChatHistory

Trattata per intero nel Capitolo 18, elencata qui perché la mappa sia completa:

```php
new EloquentChatHistory(
    threadId: 'THREAD_ID',
    modelClass: ChatMessage::class,
    contextWindow: 150_000,
);
```

### Scegliere

| Backend | Usa quando | Evita quando |
|---|---|---|
| InMemory | Script, endpoint stateless, test | Ti serve persistenza |
| File | Strumenti CLI, singolo server, prototipi | Multi-server, alta concorrenza |
| SQL | Qualunque framework, produzione, multi-server | Non hai un database |
| Eloquent | Laravel con relazioni e scope | Non sei su Laravel |

Il Laboratorio 2, alla fine di questo capitolo, costruisce una chat CLI persistente su `FileChatHistory`.

### Punti chiave

- Quattro backend: InMemory, File, SQL, Eloquent.
- In una richiesta web, "in memoria" significa nessuna memoria fra le richieste.
- `SQLChatHistory` prende un PDO semplice e funziona in qualunque framework.

## 4.4 Context window e trimming

### Il bug che questo previene

Il fallimento in produzione più comune nell'AI conversazionale:

> "Funziona bene, poi dopo una trentina di messaggi inizia a dare errore."

La trascrizione ha superato il limite di contesto del modello. Il provider rifiuta la richiesta: non la tronca per te, restituisce un errore.

La `ChatHistory` di NeuronAI lo previene tagliando automaticamente. Tiene traccia del consumo di token dalle risposte del provider e, quando la trascrizione si avvicina al limite configurato, rimuove messaggi dall'inizio.

### La regola del 5–10 %

Dalla documentazione, e vale la pena memorizzarla perché è precisa e facile da sbagliare:

**Configura la context window il 5–10 % sotto il limite reale del modello.**

| Limite del modello | Configura |
|---|---|
| 32K | 29.000 |
| 128K | 118.000 |
| 200K | 185.000 |
| 1M | 920.000 |

### Perché il margine non è superstizione

Il trimmer non taglia semplicemente al byte in cui si raggiunge il limite. Cerca un punto di taglio che minimizzi la perdita di contesto — la documentazione lo descrive come l'individuazione di un taglio leggermente meno aggressivo di quello calcolato inizialmente.

Significa che gli serve spazio di manovra. Configura esattamente al limite del modello e il trimmer non ha dove spostare il punto di taglio, e puoi comunque andare in overflow. Il margine è ciò che gli permette di scegliere un confine sensato invece di uno meccanico.

### Dove va

```php
protected function chatHistory(): ChatHistoryInterface
{
    return new InMemoryChatHistory(contextWindow: 185_000);
}
```

Ogni implementazione prende lo stesso argomento. Gli underscore nei letterali numerici sono una funzionalità di PHP 7.4+ e rendono questi valori molto più leggibili a colpo d'occhio: usali.

### Configuralo per modello, non per progetto

È l'errore contro cui vale la pena mettere esplicitamente in guardia. Se il tuo provider è configurabile (Sezione 3.6), lo è anche il tuo limite di contesto. Un valore hardcoded per un modello da 200K diventa sbagliato nel momento in cui qualcuno imposta `NEURON_PROVIDER=ollama` e ottiene un modello locale da 32K.

Derivalo:

```php
// src/ProviderFactory.php
public static function contextWindow(?string $driver = null): int
{
    $driver ??= env('NEURON_PROVIDER', 'ollama');

    return (int) match ($driver) {
        'anthropic' => 185_000,
        'openai'    => 118_000,
        'gemini'    => 920_000,
        'mistral'   => 118_000,
        'ollama'    => 29_000,
        default     => 29_000,
    };
}
```

```php
protected function chatHistory(): ChatHistoryInterface
{
    return new InMemoryChatHistory(
        contextWindow: ProviderFactory::contextWindow()
    );
}
```

### Che cosa ti costa il trimming

Il trimming scarta i messaggi più vecchi. L'utente ha stabilito un vincolo al terzo messaggio — "rispondi sempre in spagnolo", "il mio numero di conto è X" — e al quarantesimo è sparito. L'agent sembra sviluppare un'amnesia a metà conversazione, cosa che agli utenti appare come un bug anche se funziona come progettato.

Tre mitigazioni, in ordine crescente di raffinatezza:

**Ripeti le costanti nel system prompt.** Il system prompt viene rimandato a ogni turno e non è soggetto a trimming. Tutto ciò che deve sopravvivere appartiene lì, non alla trascrizione.

**Riassumi invece di scartare.** NeuronAI include un middleware di riassunto: invece di cancellare i turni più vecchi, li comprime in un breve messaggio di sintesi che resta nel contesto. Fedeltà maggiore, al costo di una chiamata extra all'LLM. Trattato insieme agli altri middleware nel Capitolo 15.

**Sposta i fatti durevoli fuori dalla trascrizione.** Memoria a lungo termine — Sezione 4.5.

### Punti chiave

- Configura il 5–10 % sotto il limite reale del modello; al trimmer serve margine.
- Deriva il valore dal provider, non hardcodarlo mai a livello di progetto.
- Il trimming scarta i messaggi più vecchi: i vincoli durevoli appartengono al system prompt.
- Il riassunto preserva più contesto al costo di una chiamata extra.

## 4.5 Memoria di sessione e memoria a lungo termine

Tre cose diverse vengono chiamate "memoria". Scegliere quella sbagliata produce un'architettura che non si aggiusta con la messa a punto.

### Tre meccanismi

**1. Memoria di sessione — `ChatHistory`.**
La conversazione corrente. Limitata dalla context window, tagliata automaticamente, circoscritta a un thread. Risponde a: "che cosa ci siamo appena detti?"

**2. Memoria a lungo termine — uno store esterno di fatti.**
Fatti durevoli su un utente o un'entità che persistono fra conversazioni. Non limitata dalla context window, perché non è nella trascrizione: l'agent la interroga su richiesta, tramite un tool. Risponde a: "che cosa so di questa persona?"

**3. Conoscenza — RAG.**
I tuoi documenti, indicizzati e recuperati per somiglianza semantica. Non riguarda affatto l'utente: riguarda il tuo dominio. Risponde a: "che cosa dice la nostra documentazione?"

I tre vengono continuamente confusi nelle discussioni di prodotto, e la confusione produce cattiva architettura. "Il bot dovrebbe ricordare le preferenze del cliente" è il meccanismo 2. "Il bot dovrebbe rispondere dal nostro manuale" è il meccanismo 3. Costruire il primo con il terzo — indicizzare le conversazioni in un vector store — è un errore di progetto che produce un richiamo vago e inaffidabile.

### Memoria a lungo termine in NeuronAI

NeuronAI include un toolkit per Zep, un servizio a grafo di conoscenza progettato esattamente per questo:

```php
use NeuronAI\Tools\Toolkits\Zep\ZepLongTermMemoryToolkit;

protected function tools(): array
{
    return [
        ZepLongTermMemoryToolkit::make(
            key: 'ZEP_API_KEY',
            user_id: 'ID',
        ),
    ];
}
```

Nota bene che è un **toolkit**, non un componente di cronologia. È l'affermazione architetturale: la memoria a lungo termine è qualcosa che l'agent *sceglie di consultare*, tramite una chiamata a tool, non qualcosa iniettato automaticamente in ogni richiesta. È il modello a decidere quando un fatto vale la pena di essere cercato o salvato.

L'argomento `user_id` partiziona lo store. Usalo come chiave di isolamento per qualunque entità stai tracciando: un utente, un'azienda, un progetto.

### La tabella decisionale

| Requisito | Meccanismo |
|---|---|
| "Riprendi da quello che ho appena detto" | Memoria di sessione |
| "Ricorda che sono vegetariano, per sempre" | Memoria a lungo termine |
| "Rispondi in base alla nostra politica di reso" | RAG |
| "Non rivelare mai i prezzi interni" | System prompt |
| "Quanti ordini ha fatto questo cliente?" | Tool di database |

Quest'ultima riga merita enfasi, perché è l'errore che si commette più spesso. Il numero di ordini è un **fatto nel tuo database**. Non è memoria e non è RAG. Chiedilo con SQL, tramite un tool. Ricorrere a un vector store per rispondere a una domanda numerabile è un sintomo di cattivo progetto, e produce risposte approssimativamente giuste — che per un conteggio equivale a sbagliate.

### La dimensione della privacy

La memoria a lungo termine significa conservare fatti personali, derivati da un modello linguistico, in un servizio di terze parti. È una conversazione sul GDPR prima ancora che una conversazione ingegneristica:

- Qual è la base giuridica per conservarli?
- L'utente può vedere che cosa è stato conservato su di lui?
- Può farlo cancellare, e la cancellazione si propaga?
- Dove risiede fisicamente lo store?

Nulla di questo è un motivo per evitare il pattern. È un motivo per progettarlo deliberatamente invece di scoprirlo durante un audit. Il Capitolo 23 ci torna sopra.

### Esercizio

Per un'applicazione su cui lavori davvero, elenca cinque cose che dovrebbe "ricordare". Classifica ciascuna in una delle cinque righe della tabella qui sopra, e giustifica quelle non ovvie. Le righe difficili da classificare sono quelle che ti daranno problemi in produzione.

### Punti chiave

- Tre meccanismi distinti: memoria di sessione, memoria a lungo termine, recupero di conoscenza.
- La memoria a lungo termine è un **toolkit**: consultata deliberatamente, non iniettata automaticamente.
- I fatti numerabili vengono dal database, mai da un vector store.
- Conservare fatti personali derivati è una decisione di privacy, non solo tecnica.

## Laboratorio 2 — Una chat CLI persistente

La dimostrazione più convincente di tutto questo capitolo: chiudi il terminale, riaprilo, e la conversazione è ancora lì.

### L'agent

**`src/Agents/PersistentAgent.php`**

```php
<?php

declare(strict_types=1);

namespace App\Agents;

use App\ProviderFactory;
use NeuronAI\Agent\Agent;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Chat\History\ChatHistoryInterface;
use NeuronAI\Chat\History\FileChatHistory;
use NeuronAI\Providers\AIProviderInterface;

class PersistentAgent extends Agent
{
    public function __construct(protected string $threadId = 'default')
    {
        parent::__construct();
    }

    protected function provider(): AIProviderInterface
    {
        return ProviderFactory::make();
    }

    public function instructions(): string
    {
        return (string) new SystemPrompt(
            background: ['You are a technical assistant that remembers conversation context.'],
            output: ['Answer concisely.'],
        );
    }

    protected function chatHistory(): ChatHistoryInterface
    {
        return new FileChatHistory(
            directory: \dirname(__DIR__, 2) . '/storage/chat',
            key: $this->threadId,
            contextWindow: ProviderFactory::contextWindow(),
        );
    }
}
```

Due dettagli che causano fallimenti silenziosi. **`parent::__construct()`**: dimenticalo e la classe base non si inizializza mai, il che produce un errore confuso molto lontano dalla sua causa. E poiché questo agent prende un argomento nel costruttore, istanzialo con `new`, non con `::make()`.

### Il ciclo

**`examples/04-chat-loop.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\PersistentAgent;
use NeuronAI\Chat\Messages\UserMessage;

$threadId = $argv[1] ?? 'default';
$agent = new PersistentAgent($threadId);

echo "Thread: {$threadId} — /exit to quit, /reset to clear memory.\n\n";

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
        foreach (\glob(\dirname(__DIR__) . "/storage/chat/{$threadId}*") ?: [] as $file) {
            \unlink($file);
        }
        $agent = new PersistentAgent($threadId);
        echo "Memory cleared.\n\n";
        continue;
    }

    try {
        $reply = $agent->chat(new UserMessage($input))->getMessage();
        echo "\n" . $reply->getContent() . "\n\n";
    } catch (\Throwable $e) {
        \fwrite(STDERR, "Error: {$e->getMessage()}\n\n");
    }
}
```

```bash
php examples/04-chat-loop.php project-alpha
```

Digli qualcosa. Esci. Riapri il terminale. Rilancia lo stesso comando e chiedigli che cosa avevi detto. **Quella** è la dimostrazione: la trascrizione è stata letta dal disco e rimandata, esattamente come descriveva la Sezione 4.2. Non è stato ricordato nulla; è stato riprodotto qualcosa.

::: {.callout .callout-tip}
[In pratica]{.callout-title}

L'implementazione di `/reset` usa una glob perché il nome file esatto prodotto da `FileChatHistory` è un dettaglio implementativo che si è spostato fra le versioni. Guarda che cosa finisce davvero in `storage/chat/` sulla tua installazione e restringi il pattern: una glob vagante che corrisponde a più di quanto intendevi è una brutta abitudine da portarsi in codice che cancella file.
:::

### Criteri di accettazione

- Due ID di thread diversi mantengono due conversazioni indipendenti.
- La conversazione sopravvive a un riavvio completo del processo.
- `/reset` azzera un thread e lascia intatto l'altro.
- Un errore del provider stampa su `STDERR` e ti riporta al prompt invece di uccidere il ciclo.

### Andare oltre

Aggiungi un comando `/history` che stampi la trascrizione corrente con i ruoli, e osserva che cosa rimuove davvero il trimming man mano che la conversazione supera la `contextWindow` configurata. Impostala deliberatamente bassa — 2.000 token — per vederlo accadere in pochi turni invece che in qualche centinaio.
