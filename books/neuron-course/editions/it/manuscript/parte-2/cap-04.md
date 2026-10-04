# Capitolo 4 — Messaggi e memoria

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

La chat CLI persistente del Laboratorio 2 si trova in [`chapters/Ch04`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch04), nel repository di accompagnamento: `PersistentAgent.php` e `run/chat-loop.php`. Come ogni esempio lì dentro, gira su un Ollama locale senza chiave API.
:::

## 4.1 Il modello dei messaggi

NeuronAI ha un layer unificato per i messaggi — ruoli, blocchi di contenuto, metadati — ed è il pezzo che fa funzionare davvero lo scambio di provider, invece di limitarsi a farlo sembrare possibile.

### Perché esiste un layer unificato

Ogni provider ha la propria forma di richiesta e risposta. OpenAI, Anthropic, Gemini e Ollama differiscono nel modo di rappresentare i ruoli, di allegare immagini, di restituire chiamate a tool, di esporre le tracce di ragionamento.

La risposta di NeuronAI è un'unica astrazione dei messaggi che si mappa su tutti. È ciò che rende la Sezione 3.6 più di un gioco di prestigio: lo scambio funziona perché il layer dei messaggi assorbe le differenze. Senza, "cambia una riga per cambiare provider" sarebbe falso nel momento in cui alleghi un'immagine o leggi una chiamata a tool.

### Che cos'è un messaggio

Tre parti:

- **Ruolo** — chi sta parlando: user, assistant o system. Le istruzioni dell'agent viaggiano come `SystemMessage`; una chiamata a tool è un messaggio assistant specializzato (`ToolCallMessage`) e il suo risultato un messaggio user specializzato (`ToolResultMessage`)
- **Blocchi di contenuto** — il payload vero e proprio
- **Metadati** — informazioni aggiuntive dalla risposta del provider, come il consumo di token

### Blocchi di contenuto

È la parte che quasi tutti si perdono. Un messaggio non contiene una stringa. Contiene un **elenco ordinato di blocchi di contenuto**, ciascuno dei quali implementa `ContentBlockInterface`. NeuronAI fornisce tipi di blocco per testo, ragionamento, immagine, file, audio e video — più il blocco system di cui sono fatte le istruzioni (Sezione 3.5) — e mappa automaticamente ciascuno nel formato corretto del provider.

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

Ora `getContent()` ha senso: unisce tutti i blocchi di testo in un'unica stringa, separati da spazi, e restituisce `null` quando il messaggio non contiene alcun testo. È una comodità, non la struttura sottostante.

### Leggere una risposta come si deve

```php
$response = MyAgent::make()
    ->setThreadId('demo')
    ->chat(new UserMessage('...'))
    ->getMessage();

// Convenience: all text blocks joined
echo $response?->getContent();
```

Ma con un modello di ragionamento la risposta porta più del semplice testo:

```php
use NeuronAI\Chat\Messages\ContentBlocks\ReasoningContent;
use NeuronAI\Chat\Messages\ContentBlocks\TextContent;

foreach ($response?->getContentBlocks() ?? [] as $block) {
    echo match ($block::class) {
        ReasoningContent::class => "Reasoning: {$block->content}\n\n",
        TextContent::class      => $block->content,
        default                 => '',
    };
}
```

NeuronAI cattura automaticamente i passaggi di ragionamento del modello come blocco distinto, e `getContent()` lo lascia fuori deliberatamente. Se chiami solo `getContent()`, non li vedi mai; `$response->getReasoning()` è la scorciatoia quando vuoi solo quel blocco. Per debuggare un agent che ha preso una decisione strana, il blocco di ragionamento è spesso la risposta.

### Costruire una conversazione a mano

A volte hai già una conversazione — dal tuo database, o da un'importazione — e devi inizializzare l'agent con quella. Passa un array a `chat()`:

```php
use NeuronAI\Chat\Enums\MessageRole;
use NeuronAI\Chat\Messages\Message;

$message = MyAgent::make()
    ->setThreadId('demo')
    ->chat([
        new Message(MessageRole::USER, 'Hi, my company is called Inspector.dev'),
        new Message(MessageRole::ASSISTANT, 'Great, how can I assist you today?'),
        new Message(MessageRole::USER, 'What is the name of the company I work for?'),
    ])
    ->getMessage();

echo $message?->getContent();
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
[Gli allegati nei tutorial più vecchi]{.callout-title}

I tutorial scritti per versioni precedenti allegano i media con `addAttachment(new Image($url, ...))`. Qui quella chiamata non esiste; un media è un blocco di contenuto, come sopra. Correlato: la documentazione è incoerente sui nomi delle classi dei blocchi — `TextBlock`/`FileBlock` compaiono in alcuni punti dove le classi distribuite sono `TextContent`/`FileContent`, e un esempio importa `AudioContent` mentre istanzia `FileContent`.
:::

### Punti chiave

- Un messaggio è ruolo + blocchi di contenuto + metadati; non una stringa.
- `getContent()` unisce i blocchi di testo; `getContentBlocks()` ti dà tutto, ragionamento incluso.
- Passa un array di oggetti `Message` per inizializzare una conversazione esistente.
- Il layer unificato dei messaggi è il motivo per cui lo scambio di provider sopravvive al contatto con immagini, file e chiamate a tool.

## 4.2 Il modello non ha memoria

L'assenza di stato è un vincolo di progetto, non una limitazione da aggirare. Questa sezione serve a interiorizzarla, perché quasi ogni confusione sulla "memoria" si dissolve quando lo fai.

### La dimostrazione

Prendi l'`AssistantAgent` del Laboratorio 1 e chiedigli qualcosa che non può sapere:

```php
use App\Agents\AssistantAgent;
use NeuronAI\Chat\Messages\UserMessage;

$message = AssistantAgent::make()
    ->setThreadId('demo')
    ->chat(new UserMessage("What's my name?"))
    ->getMessage();

echo $message?->getContent();
// I'm sorry, I don't know your name.
```

Ora tieni la stessa istanza:

```php
$agent = AssistantAgent::make()->setThreadId('demo');

$agent->chat(new UserMessage('Hi, my name is Valerio!'));

$message = $agent->chat(new UserMessage('Do you remember my name?'))->getMessage();
echo $message?->getContent();
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

Il componente NeuronAI che rimanda la trascrizione è `ChatHistory`, e la legge da un *message store*: qui quello predefinito, che vive nella memoria di quel singolo oggetto agent. È tutto ciò che "memoria" significa a questo livello.

### Quattro conseguenze da dichiarare

**1. La memoria costa denaro a ogni turno.**
Il ventesimo turno rimanda diciannove scambi precedenti. È il meccanismo dietro la tabella dei costi della Sezione 1.4, ed è il motivo per cui le conversazioni lunghe diventano care anche quando i singoli messaggi sono brevi.

**2. La memoria è limitata dalla context window.**
Non è un database che cresce. È un buffer con un tetto rigido. Prima o poi qualcosa va scartato, e l'unica domanda è cosa e come — Sezione 4.4.

**3. La memoria è interamente sotto il tuo controllo.**
Il che è liberatorio, una volta accettato. Puoi modificare la cronologia, iniettare un riassunto, eliminare turni irrilevanti, tenere fissato in modo permanente un fatto di livello sistema. Niente è sacro: è il tuo array.

**4. L'assenza di stato è il motivo per cui la scalabilità orizzontale è facile.**
Qualunque web server può servire qualunque richiesta, purché possa caricare la trascrizione. Non c'è affinità di sessione verso un provider. Tieni i messaggi in uno storage condiviso e qualunque nodo può proseguire qualunque conversazione. È un vantaggio architetturale reale, ed è insolito che una funzionalità dall'aria stateful scali così pulitamente.

### Il modello mentale da tenere

Il modello è una **funzione pura**: trascrizione in ingresso, messaggio successivo in uscita. Tutto ciò che sembra memoria, persistenza della personalità o apprendimento è il tuo codice che sceglie che cosa entra nella trascrizione.

Ogni tecnica nel resto del libro — trimming della cronologia, riassunti, RAG, store di memoria a lungo termine — è una risposta diversa a una sola domanda: **che cosa mettiamo nella trascrizione?**

### Punti chiave

- Nessuna sessione lato server; la trascrizione viene rimandata a ogni turno.
- La memoria costa token a ogni turno ed è limitata dalla context window.
- La cronologia è il tuo array: modificabile, iniettabile, sostituibile.
- Il modello è una funzione pura della trascrizione.

## 4.3 ChatHistory e message store

### L'interfaccia

```php
NeuronAI\Chat\History\MessageStoreInterface
```

La memoria di sessione è fatta di due classi con due compiti. `ChatHistory` è concreta, e non la costruisci mai tu: ogni volta che una run parte o riprende, l'agent ne apre una per il proprio thread, e quell'oggetto carica la conversazione, la tiene dentro la context window e scrive i nuovi messaggi. Il posto in cui i messaggi vengono conservati è un **message store** — qualunque cosa implementi l'interfaccia qui sopra — ed è quella la parte che scegli tu.

Lo scegli implementando `messageStore()` sul tuo agent, oppure passando un'istanza a `setMessageStore()`; la dimensione della finestra la dai con `contextWindow()` o `setContextWindow()` (Sezione 4.4). Un setter, una volta chiamato, prevale sul metodo. Il default, se non fai nulla di tutto questo, è uno store in memoria e una finestra di 50.000 token.

La cronologia è un servizio che i nodi dell'agent usano, non una parte dello stato della run: `ChatNode` legge la trascrizione da essa e vi aggiunge messaggi, e la trascrizione non viene mai copiata nell'`AgentState` restituito da `chat()`. Questa separazione conta quando le run diventano durevoli (Capitolo 15). Lo stato salvato di una run in pausa resta piccolo per quanto lunga diventi la conversazione, e la conversazione vive in un unico posto: lo store.

::: {.callout .callout-warning}
[Il codice della cronologia nei tutorial più vecchi]{.callout-title}

I tutorial scritti per versioni precedenti costruiscono la cronologia stessa — una `FileChatHistory`, una `SQLChatHistory` — in un metodo `chatHistory()` dell'agent. Quelle classi non esistono più, e il fallimento è silenzioso: nulla chiama un metodo di nome `chatHistory()`, quindi l'agent si carica, risponde e tiene la conversazione nello store in memoria predefinito. Se una conversazione non sopravvive a un riavvio, cerca per prima cosa quel metodo.
:::

### Quale conversazione? Il thread ID

Una cronologia appartiene sempre a una conversazione — un **thread** — e qualcosa deve dire quale. In NeuronAI quel qualcosa è l'agent, non lo store:

```php
$agent = SupportAgent::make(workflowId: $threadId);
```

Uno store non ha un thread proprio. Ogni metodo dell'interfaccia riceve il thread ID come argomento, così un solo store serve tutte le conversazioni, ed è l'agent a fornire l'ID: apre la propria cronologia sullo store *per il proprio thread*. L'identità entra in un solo punto, sul punto di chiamata che sa davvero di quale conversazione si tratta in questa richiesta, e mai dentro la classe che sa soltanto dove sono conservate le conversazioni.

È lo stesso ID di cui parlava la Sezione 2.3: il thread ID è anche il workflow ID della run dell'agent, ed è per questo che l'argomento del costruttore si chiama `workflowId:`. `setThreadId()`, dalla Sezione 3.4, imposta lo stesso valore dopo la costruzione. Quando nel Capitolo 15 una run si mette in pausa per un'approvazione umana, l'endpoint che la riprende non ha bisogno di altro che del thread ID per trovarla.

Ne seguono due regole, ed entrambe vengono fatte rispettare:

- **Un agent senza thread si rifiuta di funzionare.** Il framework non genera mai un ID. Chiama `chat()`, `getChatHistory()` o `resetConversation()` su un agent non legato e ottieni una `AgentException` — *"This agent has no thread ID: bind one with setThreadId() first."* — invece di una conversazione salvata in silenzio sotto una chiave che nessuno ha scelto.
- **Un agent si lega una volta sola.** Impostare di nuovo lo stesso ID è innocuo; impostarne uno diverso lancia un'eccezione, invece di scrivere in silenzio il resto della conversazione in un altro thread. Per servire un'altra conversazione costruisci un altro agent, oppure chiama `$agent->for($otherThreadId)`, che restituisce una copia legata a quel thread.

Una classe agent con un costruttore proprio deve comunque chiamare `parent::__construct()`: passagli il thread ID, oppure lega il thread dopo con `setThreadId()` o `for()`.

::: {.callout .callout-warning}
[Il thread ID è input dell'utente]{.callout-title}

Qualunque cosa passi come `workflowId:` seleziona quale conversazione viene caricata, estesa e ripresa. Se arriva in una richiesta — un segmento di URL, un campo di un form — verifica che l'utente corrente sia il proprietario di quel thread prima di costruirci l'agent. Il framework non fa alcun controllo di accesso; basta un controllo di proprietà mancante e qualunque utente può leggere la conversazione di qualunque altro.
:::

### InMemoryMessageStore

```php
use NeuronAI\Chat\History\InMemoryMessageStore;
use NeuronAI\Chat\History\MessageStoreInterface;

protected function messageStore(): MessageStoreInterface
{
    return new InMemoryMessageStore();
}
```

Un array per thread, nella memoria del processo. È il default, quindi il metodo qui sopra non fa che scrivere per esteso ciò che un agent senza `messageStore()` fa già: l'`AssistantAgent` del Laboratorio 1, per esempio. Lo store appartiene all'oggetto agent che l'ha creato: tieni l'oggetto e la conversazione continua, come nella Sezione 4.2; costruisci un secondo agent con lo stesso thread ID e parte da zero, perché ha uno store tutto suo. Corretto per: script one-shot, endpoint API stateless in cui la conversazione la tieni tu, e test.

Ricorda che in una normale richiesta web PHP muore alla fine della risposta. Uno store in memoria in contesto web significa **nessuna memoria fra una richiesta e l'altra**, cosa che sorprende davvero spesso chi è abituato a runtime a lunga esecuzione.

### FileMessageStore

```php
use NeuronAI\Chat\History\FileMessageStore;

protected function messageStore(): MessageStoreInterface
{
    return new FileMessageStore(directory: '/home/app/storage/neuron');
}
```

`directory` è un percorso assoluto, creato alla prima scrittura se non esiste. Ogni thread è un file JSON al suo interno, `neuron_<thread>.chat`, che prende il nome dal thread ID passato dall'agent — codificato come in un URL, così un ID non può mai indicare un percorso fuori dalla directory. Usa un ID utente come thread per una conversazione per utente, o un thread ID generato per averne molte.

Corretto per: strumenti CLI, applicazioni su singolo server, prototipi. Non corretto per: deploy multi-server senza storage condiviso, o worker concorrenti — ogni scrittura sostituisce l'intero file, e due processi che scrivono sullo stesso thread perderanno messaggi. C'è poi una trappola più vicina a casa: il nome del file conserva maiuscole e minuscole del thread ID, quindi su un filesystem che non distingue maiuscole e minuscole — il default di macOS e Windows — `user-Alice` e `user-alice` sono un solo file e una sola conversazione.

### SQLMessageStore

Crea prima la tabella. Una riga per messaggio: `id` ordina il thread, e `message_id` è l'identità propria del messaggio, unica all'interno del suo thread. Questa è la tabella per MySQL e MariaDB:

```sql
CREATE TABLE chat_messages (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  thread_id VARBINARY(255) NOT NULL,
  message_id VARBINARY(64) NOT NULL,
  role VARCHAR(32) NOT NULL,
  content LONGTEXT NULL,
  meta LONGTEXT NULL,
  archived_at DATETIME NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  UNIQUE INDEX idx_thread_message (thread_id, message_id)
);
```

`VARBINARY` sulle due colonne degli ID è voluto. Gli ID di thread e di messaggio devono essere confrontati byte per byte, e le collation predefinite di MySQL e MariaDB ignorano maiuscole e accenti: dichiara quelle colonne `VARCHAR` e `user-Alice` e `user-alice` leggono, e cancellano, l'uno i messaggi dell'altro. PostgreSQL e SQLite confrontano il testo in modo esatto, quindi lì sono entrambe semplici `VARCHAR`, e al resto della tabella bastano i soliti adattamenti di dialetto: `BIGSERIAL` o `INTEGER PRIMARY KEY AUTOINCREMENT` per `id`, tipi `TEXT` e `TIMESTAMP`, nessuna clausola `ON UPDATE`, e un semplice `UNIQUE (thread_id, message_id)`.

```php
use NeuronAI\Chat\History\SQLMessageStore;

protected function messageStore(): MessageStoreInterface
{
    return new SQLMessageStore(
        pdo: new \PDO('mysql:host=localhost;dbname=DB;charset=utf8mb4', 'user', 'pass'),
        table: 'chat_messages',
    );
}
```

Prende un `PDO` semplice, quindi funziona in qualunque applicazione PHP indipendentemente dal framework. In Laravel passeresti `\DB::connection()->getPdo()`; in Symfony, `$connection->getNativeConnection()` da una connessione Doctrine.

Poiché ogni messaggio è una riga a sé — `role`, i blocchi di contenuto come JSON in `content`, tutto il resto (consumo, chiamate a tool, metadati) come JSON in `meta` — la tabella è utile al resto della tua applicazione, non solo all'agent: report per messaggio, job di retention, una dashboard di supporto che elenca le conversazioni. Puoi aggiungere colonne — una chiave esterna verso la tua tabella utenti, per esempio — purché ammettano NULL e la struttura di base resti. `archived_at` è spiegata nella Sezione 4.4.

### EloquentMessageStore

Trattato per intero nel Capitolo 18, elencato qui perché la mappa sia completa:

```php
new EloquentMessageStore(modelClass: ChatMessage::class);
```

Stessa forma della tabella dello store SQL, stessa indifferenza ai thread: la classe del model è l'unica cosa che deve conoscere.

### Scegliere

| Store | Usa quando | Evita quando |
|---|---|---|
| InMemory | Script, endpoint stateless, test | Ti serve persistenza |
| File | Strumenti CLI, singolo server, prototipi | Multi-server, worker concorrenti |
| SQL | Qualunque framework, produzione, multi-server | Non hai un database |
| Eloquent | Laravel con relazioni e scope | Non sei su Laravel |

Il Laboratorio 2, alla fine di questo capitolo, costruisce una chat CLI persistente su `FileMessageStore`.

### Punti chiave

- Una sola `ChatHistory` concreta, quattro message store: InMemory, File, SQL, Eloquent.
- Uno store non porta con sé alcun thread. Dai all'agent `make(workflowId: ...)` o `setThreadId()`, e sarà lui ad aprire la cronologia per quel thread; senza, si rifiuta di girare. Il thread ID è anche il workflow ID della run.
- Autorizza il thread ID prima di usarlo: seleziona di chi è la conversazione caricata.
- In una richiesta web, "in memoria" significa nessuna memoria fra le richieste.
- `SQLMessageStore` prende un PDO semplice, conserva una riga per messaggio e funziona in qualunque framework.

## 4.4 Context window e trimming

### Il bug che questo previene

Il fallimento in produzione più comune nell'AI conversazionale:

> "Funziona bene, poi dopo una trentina di messaggi inizia a dare errore."

La trascrizione ha superato il limite di contesto del modello. Un provider cloud rifiuta la richiesta: non la tronca per te, restituisce un errore. Ollama fallisce nel modo opposto: tronca il prompt al proprio `num_ctx` e risponde con ciò che resta, senza alcun errore.

La `ChatHistory` di NeuronAI previene entrambi tagliando automaticamente. Tiene traccia del consumo di token dalle risposte del provider e, quando la conversazione non entra più nella finestra configurata, toglie messaggi dall'inizio di ciò che invia al modello.

"Toglie da ciò che invia" è una formulazione deliberata. Il trimming non cancella mai. La cronologia chiede al proprio store di archiviare ciò che ha tolto, e ogni store lo fa: un timestamp `archived_at` sulla riga (Sezione 4.3) o sulla voce nel file, un contatore in memoria. Il modello vede il thread tagliato; `loadAll()` sullo store restituisce ancora la trascrizione completa, per audit, analisi, una policy di retention o una schermata che scorre la conversazione all'indietro. `flushAll()` è l'unica operazione che cancella davvero un thread, messaggi archiviati compresi.

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

Il trimmer non taglia semplicemente al messaggio in cui si raggiunge il limite. Una cronologia deve aprirsi con un messaggio dell'utente, quindi un taglio può cadere solo all'inizio di un turno. Quando il taglio più piccolo che basta cade dentro un turno, il trimmer tiene quel turno per intero finché il risultato resta entro il 5 % oltre la finestra, e solo oltre quella soglia taglia al turno successivo. L'ultimo turno viene tenuto per quanto grande sia.

La finestra è quindi un obiettivo che il trimmer può superare di poco, pur di non buttare via un lungo scambio con i tool per risparmiare qualche token. Configura esattamente al limite del modello e quella tolleranza non ha dove andare, e puoi comunque andare in overflow. Il margine è ciò che gli permette di scegliere un confine sensato invece di uno meccanico.

### Dove va

```php
protected function contextWindow(): int
{
    return 185_000;
}
```

La finestra appartiene all'agent, non allo store: qualunque store tu abbia scelto, si imposta qui, oppure con `setContextWindow()` dall'esterno. Se la ometti ottieni 50.000 token: più di quanto un modello locale da 32K possa reggere. Gli underscore nei letterali numerici sono una funzionalità di PHP 7.4+ e rendono questi valori molto più leggibili a colpo d'occhio: usali.

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
protected function contextWindow(): int
{
    return ProviderFactory::contextWindow();
}
```

La cifra di Ollama è l'unica che dipende dalla tua configurazione. 29.000 presuppone una finestra da 32K, e un modello locale ce l'ha solo se la chiedi: `parameters: ['options' => ['num_ctx' => 32_768]]` sul provider Ollama, come fa la factory della Sezione 3.6. Senza, Ollama tronca al proprio valore predefinito, di solito molto più piccolo, ben prima che il trimmer veda un motivo per intervenire. Cambia uno dei due numeri e devi cambiare anche l'altro.

### Che cosa ti costa il trimming

Il trimming toglie i messaggi più vecchi dalla vista del modello. L'utente ha stabilito un vincolo al terzo messaggio — "rispondi sempre in spagnolo", "il mio numero di conto è X" — e al quarantesimo è sparito. L'agent sembra sviluppare un'amnesia a metà conversazione, cosa che agli utenti appare come un bug anche se funziona come progettato.

Tre mitigazioni, in ordine crescente di raffinatezza:

**Ripeti le costanti nel system prompt.** Il system prompt viene rimandato a ogni turno e non è soggetto a trimming. Tutto ciò che deve sopravvivere appartiene lì, non alla trascrizione.

**Riassumi invece di scartare.** NeuronAI include un middleware di riassunto, `Summarization`, che colleghi ai nodi di inferenza dell'agent (Sezione 2.3): quando la conversazione supera un budget di token, sostituisce tutto tranne gli ultimi messaggi con un breve messaggio di sintesi che resta nel contesto. Il modello conserva più del thread, al costo di una chiamata extra all'LLM — e della trascrizione. Il middleware riscrive il thread passando per `flushAll()`, quindi i messaggi originali, archiviati compresi, spariscono dallo store; se quel registro ti serve, tienine una copia tua. I middleware sono trattati nel Capitolo 15.

**Sposta i fatti durevoli fuori dalla trascrizione.** Memoria a lungo termine — Sezione 4.5.

### Punti chiave

- Configura il 5–10 % sotto il limite reale del modello; al trimmer serve margine.
- Deriva il valore dal provider, non hardcodarlo mai a livello di progetto. Con Ollama, imposta `num_ctx` di conseguenza: tronca in silenzio invece di fallire.
- Il trimming nasconde al modello i messaggi più vecchi: i vincoli durevoli appartengono al system prompt.
- Ogni store archivia i messaggi tagliati invece di cancellarli; la trascrizione completa resta nel tuo storage.
- Il riassunto preserva più contesto al costo di una chiamata extra — e della trascrizione conservata, che sostituisce.

## 4.5 Memoria di sessione e memoria a lungo termine

Tre cose diverse vengono chiamate "memoria". Scegliere quella sbagliata produce un'architettura che non si aggiusta con la messa a punto.

### Tre meccanismi

**1. Memoria di sessione — `ChatHistory`.**
La conversazione corrente. Limitata dalla context window, tagliata automaticamente, circoscritta a un thread. Risponde a: "che cosa ci siamo appena detti?"

**2. Memoria a lungo termine — uno store fuori dalla trascrizione.**
Ciò che le conversazioni precedenti hanno stabilito su un utente o un'entità, conservato oltre il singolo thread. Non limitata dalla context window, perché non è nella trascrizione: vi rientra solo ciò che è rilevante per la domanda corrente. Risponde a: "che cosa so di questa persona?"

**3. Conoscenza — RAG.**
I tuoi documenti, indicizzati e recuperati per somiglianza semantica. Non riguarda affatto l'utente: riguarda il tuo dominio. Risponde a: "che cosa dice la nostra documentazione?"

I tre vengono continuamente confusi nelle discussioni di prodotto, e la confusione produce cattiva architettura. "Il bot dovrebbe ricordare le preferenze del cliente" è il meccanismo 2. "Il bot dovrebbe rispondere dal nostro manuale" è il meccanismo 3. I due possono condividere i meccanismi — NeuronAI costruisce il secondo con i componenti del terzo — ma mai uno store: indicizza le conversazioni nello stesso vector store del manuale e le parole di un cliente tornano come risposta alla domanda di un altro.

### Memoria a lungo termine in NeuronAI

La memoria delle conversazioni di NeuronAI ha due metà, entrambe costruite con componenti RAG (Capitolo 12) e ciascuna attivabile per conto suo. La metà che scrive è un nodo. Restituisci un `ConversationIngestionNode` dal metodo `exitNodes()` dell'agent, al posto del finale predefinito, e ogni turno completato — il testo dell'utente e la risposta finale del modello, mai le chiamate a tool — viene salvato come un documento in un vector store, etichettato con il suo thread ID. Al nodo servono quello store e un provider di embedding, iniettati qui tramite il costruttore:

```php
use NeuronAI\RAG\Embeddings\EmbeddingsProviderInterface;
use NeuronAI\RAG\Nodes\ConversationIngestionNode;
use NeuronAI\RAG\VectorStore\VectorStoreInterface;

public function __construct(
    protected VectorStoreInterface $conversationStore,
    protected EmbeddingsProviderInterface $embeddings,
) {
    parent::__construct();
}

protected function exitNodes(): array
{
    return [new ConversationIngestionNode(
        vectorStore: $this->conversationStore,
        embeddingProvider: $this->embeddings,
    )];
}
```

La metà che legge è una strategia di retrieval, `SemanticMemoryRetrieval`. Dati lo stesso store e un elenco di thread ID, un agent RAG (Sezione 12.7) trova gli scambi passati più vicini per significato alla domanda corrente e li aggiunge al prompt come contesto aggiuntivo.

Nota bene che questo è **retrieval**, non un componente di cronologia. È l'affermazione architetturale: la memoria a lungo termine non è una trascrizione più lunga rimandata a ogni turno. È una ricerca, e al modello arriva solo ciò che la ricerca restituisce.

L'elenco dei thread ID partiziona lo store. È un'allowlist, e nulla vi viene aggiunto per te, nemmeno il thread corrente: passa esattamente i thread che questo utente ha diritto di richiamare. Tieni inoltre le conversazioni in un vector store tutto loro. Solo questa strategia applica l'allowlist; qualunque altro retrieval sullo stesso store restituisce le conversazioni di tutti.

Il materiale meno recente usa per questo compito un toolkit, `ZepLongTermMemoryToolkit`. È ancora distribuito, ma è deprecato e verrà rimosso nella prossima major.

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

La memoria a lungo termine significa conservare ciò che le persone hanno detto alla tua applicazione, e ciò che un modello linguistico ha risposto, oltre la conversazione in cui è stato detto — spesso in un servizio di terze parti. È una conversazione sul GDPR prima ancora che una conversazione ingegneristica:

- Qual è la base giuridica per conservarli?
- L'utente può vedere che cosa è stato conservato su di lui?
- Può farlo cancellare, e la cancellazione si propaga?
- Dove risiede fisicamente lo store?

Sulla terza domanda: `resetConversation()` azzera la cronologia della conversazione e nient'altro. I documenti nello store delle conversazioni hanno un ciclo di vita proprio e si cancellano a parte, tramite il vector store, thread per thread.

Nulla di questo è un motivo per evitare il pattern. È un motivo per progettarlo deliberatamente invece di scoprirlo durante un audit. Il Capitolo 23 ci torna sopra.

### Esercizio

Per un'applicazione su cui lavori davvero, elenca cinque cose che dovrebbe "ricordare". Classifica ciascuna in una delle cinque righe della tabella qui sopra, e giustifica quelle non ovvie. Le righe difficili da classificare sono quelle che ti daranno problemi in produzione.

### Punti chiave

- Tre meccanismi distinti: memoria di sessione, memoria a lungo termine, recupero di conoscenza.
- La memoria a lungo termine è **retrieval** su uno store di conversazioni tutto suo, delimitato da un elenco esplicito di thread ID: interrogato a ogni domanda, non rimandato a ogni turno.
- I fatti numerabili vengono dal database, mai da un vector store.
- Conservare ciò che gli utenti hanno detto oltre la conversazione è una decisione di privacy, non solo tecnica.

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
            background: ['You are a technical assistant that remembers conversation context.'],
            output: ['Answer concisely.'],
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
        return ProviderFactory::contextWindow();
    }
}
```

Nota che cosa la classe *non* contiene: un thread ID. Non c'è costruttore, non c'è una proprietà `$threadId`, nessuna chiave passata a `FileMessageStore`. La classe descrive dove sono conservate le conversazioni; a quale conversazione appartiene questa run lo decide chi costruisce l'agent, tramite `make(workflowId: ...)`, esattamente come descritto nella Sezione 4.3. La stessa classe serve ogni thread.

### Il ciclo

**`examples/04-chat-loop.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\PersistentAgent;
use NeuronAI\Chat\Messages\UserMessage;

$threadId = $argv[1] ?? 'default';
$agent = PersistentAgent::make(workflowId: $threadId);

echo "Thread: {$threadId} — /exit to quit, /reset to clear memory.\n\n";

while (true) {
    $input = \readline('> ');

    if ($input === false) {
        break;
    }

    $input = \trim($input);

    if ($input === '') {
        continue;
    }

    \readline_add_history($input);

    if ($input === '/exit') {
        break;
    }

    if ($input === '/reset') {
        $agent->resetConversation();
        echo "Memory cleared.\n\n";
        continue;
    }

    try {
        $reply = $agent->chat(new UserMessage($input))->getMessage();
        echo "\n" . $reply?->getContent() . "\n\n";
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

`/reset` non tocca il filesystem. `resetConversation()` chiede all'agent di dimenticare: abbandona qualunque run non conclusa sul thread e chiama `flushAll()` sulla cronologia, che svuota il thread nello store: per `FileMessageStore`, cancellando il file di quel thread — messaggi archiviati compresi — e nient'altro. Cancellare file a mano con una glob lega il tuo codice a un formato di nome file che è affare della libreria, e un pattern che corrisponde a più di quanto intendevi è una brutta abitudine da portarsi in codice che cancella cose. Guarda in `storage/chat/` prima e dopo un reset per verificarlo di persona.
:::

### Criteri di accettazione

- Due ID di thread diversi mantengono due conversazioni indipendenti.
- La conversazione sopravvive a un riavvio completo del processo.
- `/reset` azzera un thread e lascia intatto l'altro.
- Un errore del provider stampa su `STDERR` e ti riporta al prompt invece di uccidere il ciclo.

### Andare oltre

Aggiungi un comando `/history` che stampi la trascrizione corrente con i ruoli — `$agent->getChatHistory()->getMessages()` ti dà gli oggetti `Message`, e `getRole()` su ciascuno — e osserva che cosa il trimming toglie dalla vista man mano che la conversazione supera la context window. Impostala deliberatamente bassa — `->setContextWindow(2_000)` sull'agent che il ciclo costruisce — per vederlo accadere in pochi turni invece che in qualche centinaio. Poi apri il file del thread in `storage/chat/`: i messaggi tagliati sono ancora lì, marcati `archived_at`.
