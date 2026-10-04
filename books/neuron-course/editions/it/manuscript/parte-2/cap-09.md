# Capitolo 9 — MCP: il Model Context Protocol

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

La versione eseguibile di ogni listato che segue si trova in [`chapters/Ch09`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch09), nel repository di accompagnamento. Clonalo, esegui `composer install` e gli esempi funzionano su un Ollama locale senza alcuna API key.
:::

## 9.1 Che cos'è MCP e perché conta

### La definizione

MCP è uno standard aperto, progettato da Anthropic, per collegare gli agent a fornitori di servizi esterni — il database della tua applicazione, API esterne, piattaforme di terze parti.

In pratica: permette a un server di esporre un insieme di tool tramite un protocollo definito, e qualunque client compatibile con MCP può consumarli.

### Il problema che risolve

Prima di MCP ogni integrazione era su misura. Vuoi che il tuo agent usi Slack? Leggi la documentazione dell'API di Slack, scrivi le classi tool, gestisci l'autenticazione, mantienila. Poi fai lo stesso per Jira. Poi per GitHub. Poi per il tuo CRM. E ogni altro framework in ogni altro linguaggio rifà lo stesso lavoro.

MCP inverte la cosa. È il **fornitore** a pubblicare un server. Ogni client — NeuronAI, LangChain, un assistente desktop, un IDE — lo consuma.

Per te che integri, il cambiamento è: *"due giorni di lavoro per integrazione"* diventa *"una riga di configurazione, se un server esiste."*

### In NeuronAI

```php
use NeuronAI\MCP\McpConnector;

class MyAgent extends Agent
{
    protected function tools(): array
    {
        return [
            ...McpConnector::make([
                'command' => 'php',
                'args' => ['/home/code/mcp_server.php'],
            ])->tools(),
        ];
    }
}
```

Tre dettagli su cui vale la pena fermarsi:

**L'operatore di spread.** `...McpConnector::make(...)->tools()` — `tools()` restituisce un array, e lo spread lo fonde nel tuo elenco. Dimentica i `...` e annidi un array dentro l'array dei tool, cosa che fallisce in un modo non ovvio dall'errore.

**Un connettore per server.** Crea un'istanza `McpConnector` separata per ogni server a cui ti colleghi.

**La scoperta è automatica.** NeuronAI scopre i tool che il server espone. Non li elenchi tu. Quando l'agent decide di eseguirne uno, NeuronAI genera la richiesta appropriata, la chiama sul server e restituisce il risultato al modello.

::: {.callout .callout-warning}
[Conversione rigorosa dello schema]{.callout-title}

La scoperta converte lo schema di input di ogni tool nei tipi di proprietà dei tool di NeuronAI, e lo fa in modo rigoroso. Uno schema che usa `anyOf`, `oneOf`, `$ref` o un elenco di tipi fa sollevare a `tools()` una `ToolException` (`JSON Schema keyword 'anyOf' cannot be represented by the tool property types.`), e un solo tool di questo tipo fa fallire la scoperta dell'intero server. Non è un caso esotico: i server Python costruiti con FastMCP descrivono ogni parametro opzionale come `anyOf: [integer, null]`. `only()` filtra prima della conversione, quindi una lista di permessi (Sezione 9.4) tiene fuori anche i tool che non puoi usare.
:::

Il riassunto del framework stesso: *sembra esattamente di usare i tuoi tool definiti a mano, ma puoi accedere a un enorme archivio di azioni predefinite con una riga di codice.*

### Dove trovare i server

- GitHub ufficiale di MCP: `github.com/modelcontextprotocol/servers`
- Registro MCP-GET: `mcp-get.com`

### La valutazione onesta

**Che cosa ti dà davvero MCP:** un catalogo enorme di integrazioni che non hai scritto, un ecosistema che cresce senza il tuo coinvolgimento e uno standard che viene adottato ampiamente invece che da un solo fornitore.

**Che cosa ti costa:** tutte le garanzie della Sezione 5.1. Quei tool non li hai scritti tu. Non li hai revisionati. Non controlli le loro descrizioni, il loro comportamento, la loro gestione degli errori né che cosa fanno con gli argomenti che il modello manda. La Sezione 9.4 lo prende sul serio.

La posizione equilibrata: MCP è eccellente per collegarsi a servizi di cui ti fidi già, e richiede vera diligenza per tutto il resto.

### Punti chiave

- Uno standard aperto: i server espongono tool, qualunque client li consuma.
- Una riga di configurazione sostituisce un'integrazione su misura.
- Fai lo spread del risultato; un connettore per server; la scoperta è automatica.
- Erediti codice che non hai scritto: è tutto il punto e tutto il rischio.

## 9.2 Server locali

### Configurazione a comando

Per un server installato in locale sulla tua macchina o VM:

```php
use NeuronAI\MCP\McpConnector;

class MyAgent extends Agent
{
    protected function tools(): array
    {
        return [
            ...McpConnector::make([
                'command' => 'php',
                'args' => ['/home/code/mcp_server.php'],
            ])->tools(),
        ];
    }
}
```

NeuronAI avvia il processo e comunica con esso tramite standard input e output.

::: {.callout .callout-warning}
[Il comando è un solo percorso di programma]{.callout-title}

`StdioTransport` avvia il server direttamente, con `proc_open([$command, ...$args])`, senza alcuna shell di mezzo. Quindi `command` è esattamente un solo percorso di programma, preso alla lettera, e tutto ciò che viene dopo va in `args`, un elemento per argomento. Un percorso che contiene uno spazio, il caso predefinito su macOS con Laravel Herd, il cui PHP vive sotto `~/Library/Application Support/…`, funziona così com'è:

```php
'command' => PHP_BINARY,
```

Non metterlo tra virgolette e non avvolgerlo in `escapeshellarg()`: le virgolette diventano parte del nome del file e il server non parte mai (`McpException: Failed to start the MCP server "'/…/php'"`). Lo stesso vale per `~`, `$VAR`, i prefissi `VAR=value` e `cd … && …`: una shell li interpreterebbe, questo trasporto no. Metti le variabili in `env` (più avanti) e su Windows usa `npx.cmd` per i server installati con npm, non `npx`.
:::

### L'ecosistema Node

La maggior parte dei server pubblicati sono pacchetti Node, eseguiti con `npx`:

```php
...McpConnector::make([
    'command' => 'npx',
    'args' => ['-y', '@modelcontextprotocol/server-everything'],
])->tools(),
```

`server-everything` è l'implementazione di riferimento e la cosa giusta con cui sperimentare: espone esempi di ogni funzionalità MCP ed è il modo più rapido per vedere la scoperta all'opera. `-y` esegue la versione corrente, qualunque sia; fuori da un esperimento, fissane una dopo il nome del pacchetto (`package@x.y.z`).

::: {.callout .callout-warning}
[Prerequisito]{.callout-title}

Richiede Node sulla macchina che esegue l'agent. Uno sviluppatore PHP senza Node installato incontrerà un fallimento confuso e presumerà, ragionevolmente, che il framework sia rotto. Installalo prima di affrontare questa sezione.
:::

### Il modello dei processi, e le sue conseguenze

Il server è un **processo figlio** del tuo processo PHP. Ne seguono tre cose:

**Costo di avvio a ogni turno.** Ogni turno costruisce il connettore, che crea il processo, aspetta la scoperta, poi lavora. In uno script CLI va bene. In una richiesta web è latenza su ogni richiesta.

**Gira con i tuoi privilegi, ma non con il tuo ambiente.** Accesso al file system e rete sono tuoi: trattalo esattamente come tratteresti qualunque dipendenza che esegui con `exec()`. L'ambiente no. Il server riceve dal tuo processo solo `HOME`, `LOGNAME`, `PATH`, `SHELL`, `TERM` e `USER` (più alcune variabili di Windows), quindi le tue API key non lo raggiungono. Tutto ciò che gli serve passa dalla chiave `env`:

```php
...McpConnector::make([
    'command' => 'php',
    'args' => [__DIR__ . '/crm_mcp_server.php'],
    'env' => ['CRM_API_KEY' => (string) env('CRM_API_KEY')],
])->tools(),
```

`env` ha la precedenza in caso di conflitto di nomi. Le impostazioni del proxy, `LANG` e `TMPDIR` sono nella stessa condizione dei segreti: passale se il server ne ha bisogno.

**Non è per un deploy web tipico.** Creare `npx` a ogni richiesta HTTP non è un pattern di produzione. Per le applicazioni web usa server remoti (Sezione 9.3), oppure fai girare il lavoro dell'agent su un queue worker, dove l'avvio del processo si ammortizza su un job più lungo.

### Il caso genuinamente interessante: il tuo server

Puoi scrivere un server MCP in PHP:

```php
...McpConnector::make([
    'command' => 'php',
    'args' => ['/home/code/mcp_server.php'],
])->tools(),
```

Perché farlo? Perché trasforma le capacità della tua applicazione in qualcosa che **qualunque** agent può consumare: il tuo agent NeuronAI, l'agent Python di un collega, un assistente nell'IDE, un client desktop.

Invece di costruire tool per un agent, pubblichi una superficie di capacità una volta sola. Per un'azienda con un sistema interno di valore, è una mossa strategica più che un dettaglio implementativo.

### Punti chiave

- `command` + `args` per i server locali; comunicazione su stdio.
- La maggior parte dei server sono pacchetti Node: Node è un prerequisito.
- Il server è un processo figlio: costo di avvio, i tuoi privilegi ma un ambiente ridotto, inadatto all'uso web per richiesta.
- Scrivere il proprio server espone il tuo sistema a tutti gli ecosistemi di agent in una volta.

## 9.3 Server remoti

### HTTP in streaming

Il caso normale per i server ospitati:

```php
use NeuronAI\MCP\McpConnector;

class MyAgent extends Agent
{
    protected function tools(): array
    {
        return [
            ...McpConnector::make([
                'url' => 'https://mcp.example.com',
                'token' => 'BEARER_TOKEN',
                'timeout' => 30,
                'headers' => [
                    //'x-custom-header' => 'value'
                ]
            ])->tools(),
        ];
    }
}
```

Quattro chiavi:

- **`url`** — l'endpoint del server
- **`token`** — usato come bearer token di autorizzazione
- **`timeout`** — secondi; impostalo deliberatamente (vedi sotto)
- **`headers`** — qualunque altra cosa richieda il server

La versione del protocollo non la configuri tu. Il client chiede la revisione `2025-11-25` nella sua richiesta `initialize`, accetta la versione su cui il server si assesta, e il trasporto streamable HTTP la rimanda come header `MCP-Protocol-Version` in ogni richiesta successiva, che è ciò che i server attuali si aspettano.

### Trasporto SSE

Imposta `async => true`:

```php
...McpConnector::make([
    'url' => 'https://mcp.example.com',
    'token' => 'BEARER_TOKEN',
    'timeout' => 30,
    'async' => true
])->tools(),
```

I Server-Sent Events mantengono una singola connessione HTTP di lunga durata su cui il server spinge aggiornamenti.

**Quale usare:** quello che il server documenta. Non è una tua scelta: è una proprietà del server a cui ti stai collegando. SSE è il trasporto HTTP+SSE legacy: non recupera una sessione scaduta e non segue i redirect, quindi dove un server offre entrambi, scegli lo streamable HTTP.

### Imposta il timeout deliberatamente

Il default è di 30 secondi per richiesta, che è generoso. Ricorda l'aritmetica della latenza della Sezione 1.4: un agent multi-passo che fa diverse chiamate MCP accumula ogni timeout.

La chiave vale per ogni trasporto, stdio compreso, dove limita ogni attesa di una risposta da un server locale.

Se un server impiega abitualmente 25 secondi, o è inadatto all'uso interattivo o il tuo agent appartiene a una coda. Non scoprirlo in produzione. Misuralo durante l'integrazione e decidi.

### Tratta il token come una credenziale

`'token' => 'BEARER_TOKEN'` nella documentazione è un segnaposto. Nel codice vero:

```php
...McpConnector::make([
    'url'     => env('CRM_MCP_URL'),
    'token'   => env('CRM_MCP_TOKEN'),
    'timeout' => 15,
])->tools(),
```

Tutto ciò che c'è nella Sezione 3.7 si applica. È una credenziale verso un sistema che probabilmente può leggere o modificare dati aziendali.

### La scoperta avviene quando l'agent gira

Un dettaglio operativo che sorprende: **`tools()` si collega al server.** NeuronAI chiama l'hook `tools()` del tuo agent una volta per segmento di esecuzione, non quando chiami `make()`: ogni turno di `chat()` costruisce il connettore ed elenca di nuovo i tool del server.

Significa che:

- Costruire l'agent non si collega a niente; lo fa la prima `chat()`
- Un server lento rallenta ogni turno, prima della chiamata al modello
- Un server giù fa sollevare un'eccezione a `chat()` invece di farla rispondere

Se il tuo metodo `tools()` si collega a tre server MCP remoti, hai tre punti di guasto fra la richiesta di un utente e il primo token della risposta. Mettilo in conto: intercetta i fallimenti dentro `tools()`, degrada a un insieme ridotto di tool e monitora la disponibilità dei server come parte del tuo uptime, non di quello di qualcun altro. Una connessione fallita solleva `McpException`, uno schema che il convertitore rifiuta solleva `ToolException`:

```php
use NeuronAI\Exceptions\ToolException;
use NeuronAI\MCP\McpConnector;
use NeuronAI\MCP\McpException;

protected function tools(): array
{
    try {
        return [
            ...McpConnector::make([
                'url'     => env('CRM_MCP_URL'),
                'token'   => env('CRM_MCP_TOKEN'),
                'timeout' => 10,
            ])->only(['search_contacts'])->tools(),
        ];
    } catch (McpException|ToolException $e) {
        // Degrade to a reduced tool set: the agent still answers, without the CRM.
        \error_log('CRM MCP server unavailable: ' . $e->getMessage());

        return [];
    }
}
```

### Punti chiave

- `url` + `token` + `timeout` + `headers` per l'HTTP in streaming; aggiungi `async => true` per SSE.
- Il trasporto è una scelta del server, non tua.
- La scoperta avviene a ogni turno, quando gira `tools()`: i server remoti sono dipendenze di disponibilità.
- Tratta i token come credenziali; imposta i timeout esplicitamente.

## 9.4 Filtraggio e sicurezza

### Filtrare per nome di tool

```php
class MyAgent extends Agent
{
    protected function tools(): array
    {
        return [
            // EXCLUDE: discard certain tools
            ...McpConnector::make([
                'url' => 'https://mcp.example.com',
            ])->exclude([
                'tool_name_1',
                'tool_name_2',
            ])->tools(),

            // ONLY: select the tools you want to include
            ...McpConnector::make([
                'url' => 'https://mcp.example.com',
            ])->only([
                'tool_name_1',
                'tool_name_2',
            ])->tools(),
        ];
    }
}
```

**Differenza importante rispetto alla Sezione 5.8.** I filtri dei toolkit prendono **nomi di classe** pienamente qualificati. I filtri MCP prendono **stringhe con i nomi dei tool**, perché i tool sono definiti da remoto e dalla tua parte non hanno classi PHP.

Questo ha una conseguenza da dichiarare: non c'è analisi statica, non c'è completamento nell'IDE e non c'è errore di compilazione se un nome cambia. Un refuso in un elenco `only()` produce silenziosamente meno tool di quanti ti aspettassi. Durante lo sviluppo, logga il numero di tool risultante.

### Usa `only()`. Sempre.

La Sezione 5.8 sosteneva che le liste di permessi battono quelle di negazione perché i toolkit guadagnano tool nei rilasci del framework. Con MCP l'argomento è molto più forte:

**Il server può aggiungere tool in qualunque momento, a tua insaputa, senza alcun deploy dalla tua parte.**

Avevi scritto `exclude(['delete_everything'])`. Il mese prossimo il manutentore aggiunge `purge_all`. Ora il tuo agent ce l'ha. Non hai aggiornato una dipendenza, non hai fatto deploy, non hai revisionato un changelog. La capacità è arrivata via rete.

`only()` è l'unica opzione difendibile per qualunque server MCP che non controlli. È uno dei pochi punti di questo libro in cui c'è una risposta genuinamente giusta.

### La questione della fiducia, posta come si deve

Tutti gli argomenti della Sezione 5.1 sull'elenco dei tool come confine di sicurezza presupponevano che i tool li avessi scritti tu. Con MCP non è così.

A che cosa stai estendendo la fiducia:

- **Descrizioni di tool che non hai scritto.** E le descrizioni sono istruzioni che il modello legge. Una descrizione malevola o sciatta è un vettore di prompt injection con un meccanismo di consegna dall'aria legittima.
- **Comportamenti che non puoi ispezionare.** Il tool dice di leggere un calendario. Non puoi verificare che faccia solo quello.
- **Una dipendenza che cambia senza un incremento di versione.** Composer ti dà un lock file. Un server MCP ti dà quello che sta girando oggi.
- **Ovunque vadano i tuoi argomenti.** Se il modello passa dati di clienti a un tool remoto, quei dati hanno lasciato la tua infrastruttura. È una questione GDPR, non una preferenza tecnica.
- **Descrizioni che cambiano sotto un nome consentito.** `only()` fissa i nomi, non le descrizioni né gli schemi. Il tool che hai approvato il lunedì può descriversi in modo diverso il venerdì.
- **I risultati dei tool.** Ciò che un tool restituisce entra nella conversazione come testo che il modello legge. Un risultato può portare istruzioni quanto una descrizione: è anch'esso un canale di prompt injection.
- **Collisioni di nomi.** Due server, o un server e uno dei tuoi tool, che espongono lo stesso nome di tool fanno fallire l'esecuzione con una `ToolException` prima della prima richiesta al provider. Escludine uno con `only()` o `exclude()`.

### Una policy praticabile

**Livello 1 — Server che gestisci tu.** Il tuo server MCP, sulla tua infrastruttura. Stessa fiducia del tuo codice. Usalo liberamente.

**Livello 2 — Server di fornitori di cui ti fidi già.** Il server ufficiale del tuo CRM, dove hai già un contratto, un accordo sul trattamento dati e un canale di supporto. Usalo con `only()`.

**Livello 3 — Tutto il resto.** Server della comunità, voci casuali nei registri, qualunque cosa non manutenuta. Trattali come codice non fidato. Per la produzione: leggi il sorgente, fissa una versione, eseguilo tu invece di collegarti a un'istanza ospitata, e combina `only()` con la tool approval per qualunque cosa abbia effetti collaterali.

Prototipare è diverso: il livello 3 va bene per una prova. La distinzione è fra "provarlo" e "metterlo in produzione".

### Stratifica le difese

I tool MCP sono comunque tool, quindi tutto il Capitolo 5 si applica, compreso il controllo di approvazione. Ogni tool scoperto è un `McpTool`, una normale sottoclasse di `Tool`, e `with()` ti permette di configurarne uno tramite il suo nome lato server prima che il connettore lo consegni all'agent:

```php
use NeuronAI\MCP\McpConnector;
use NeuronAI\MCP\McpTool;

protected function tools(): array
{
    return [
        ...McpConnector::make([
            'url'   => env('CRM_MCP_URL'),
            'token' => env('CRM_MCP_TOKEN'),
        ])->only([
            'search_contacts',
            'get_contact',
            'update_contact',
        ])->with(
            'update_contact',
            fn (McpTool $tool) => $tool->requireApproval(),
        )->tools(),
    ];
}
```

La lista di permessi decide quali tool esistono. `requireApproval()` decide quali di essi possono girare senza un essere umano: l'agent va in pausa prima che `update_contact` venga eseguito e attende una decisione. Metti dietro di esso ogni tool che scrive; il Capitolo 15 spiega che cosa serve all'agent per mettersi in pausa e riprendere. La callback può anche restituire un tool diverso da usare al posto di quello scoperto, ed è il posto naturale per l'ultimo livello di difesa: per un'integrazione davvero sensibile, fai passare la chiamata attraverso un tuo tool PHP che valida gli argomenti prima di inoltrarli, così hai un posto dove imporre le tue regole.

### Punti chiave

- I filtri MCP prendono stringhe con i nomi dei tool, non nomi di classe: niente analisi statica, quindi logga il conteggio.
- `only()` è obbligatorio per qualunque server che non controlli; i server guadagnano tool senza un tuo deploy.
- `with()` configura un tool scoperto tramite il suo nome: usalo per mettere i tool che scrivono dietro `requireApproval()`.
- Ti stai fidando di descrizioni e risultati che non hai scritto: una superficie di prompt injection.
- Tre livelli di fiducia; sii esplicito su quale stai usando.

## Esercizi del capitolo

1. **Scopri.** Collegati a `server-everything` e logga quali tool vengono scoperti. Misura la chiamata a `->tools()`: è latenza che pagheresti a ogni turno in contesto web.

2. **Restringi.** Riduci con `only()` a due tool e verifica che l'agent non possa usarne un terzo. Poi introduci un refuso nella lista di permessi e conferma che nulla ti avverte: quel silenzio è il motivo per cui la Sezione 9.4 ti chiede di loggare il conteggio.

3. **Classifica.** Per un'integrazione che costruiresti davvero, colloca il server in un livello di fiducia e metti per iscritto che cosa richiederesti prima di metterla in produzione. Se la risposta è "niente", confrontala con i punti della sezione sulla fiducia.
