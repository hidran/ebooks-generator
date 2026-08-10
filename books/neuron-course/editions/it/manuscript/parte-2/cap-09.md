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

### L'ecosistema Node

La maggior parte dei server pubblicati sono pacchetti Node, eseguiti con `npx`:

```php
...McpConnector::make([
    'command' => 'npx',
    'args' => ['-y', '@modelcontextprotocol/server-everything'],
])->tools(),
```

`server-everything` è l'implementazione di riferimento e la cosa giusta con cui sperimentare: espone esempi di ogni funzionalità MCP ed è il modo più rapido per vedere la scoperta all'opera.

::: {.callout .callout-warning}
[Prerequisito]{.callout-title}

Richiede Node sulla macchina che esegue l'agent. Uno sviluppatore PHP senza Node installato incontrerà un fallimento confuso e presumerà, ragionevolmente, che il framework sia rotto. Installalo prima di affrontare questa sezione.
:::

### Il modello dei processi, e le sue conseguenze

Il server è un **processo figlio** del tuo processo PHP. Ne seguono tre cose:

**Costo di avvio a ogni esecuzione.** Ogni esecuzione crea il processo, aspetta la scoperta, poi lavora. In uno script CLI va bene. In una richiesta web è latenza su ogni richiesta.

**Eredita il tuo ambiente.** Accesso al file system, variabili d'ambiente, rete. Un server MCP locale gira con i privilegi del tuo processo. Trattalo esattamente come tratteresti qualunque dipendenza che esegui con `exec()`.

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
- Il server è un processo figlio: costo di avvio, privilegi ereditati, inadatto all'uso web per richiesta.
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
                    //'x-cutom-header' => 'value'
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

**Quale usare:** quello che il server documenta. Non è una tua scelta: è una proprietà del server a cui ti stai collegando.

### Imposta il timeout deliberatamente

Il default può essere generoso. Ricorda l'aritmetica della latenza della Sezione 1.4: un agent multi-passo che fa diverse chiamate MCP accumula ogni timeout.

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

### La scoperta avviene alla costruzione

Un dettaglio operativo che sorprende: **`tools()` si collega al server.**

Significa che:

- Costruire l'agent richiede che il server sia raggiungibile
- Un server lento rallenta la costruzione dell'agent, prima di qualunque chiamata al modello
- Un server giù significa che il tuo agent non può proprio essere costruito

Se il tuo metodo `tools()` si collega a tre server MCP remoti, hai tre punti di guasto fra la richiesta di un utente e il primo token della risposta. Mettilo in conto: intercetta i fallimenti in costruzione, degrada a un insieme ridotto di tool e monitora la disponibilità dei server come parte del tuo uptime, non di quello di qualcun altro.

### Punti chiave

- `url` + `token` + `timeout` + `headers` per l'HTTP in streaming; aggiungi `async => true` per SSE.
- Il trasporto è una scelta del server, non tua.
- La scoperta avviene quando costruisci l'agent: i server remoti sono dipendenze di disponibilità.
- Tratta i token come credenziali; imposta i timeout esplicitamente.

## 9.4 Filtraggio e sicurezza

### Filtrare per nome di tool

```php
class MyAgent extends Agent
{
    protected function tools()
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

### Una policy praticabile

**Livello 1 — Server che gestisci tu.** Il tuo server MCP, sulla tua infrastruttura. Stessa fiducia del tuo codice. Usalo liberamente.

**Livello 2 — Server di fornitori di cui ti fidi già.** Il server ufficiale del tuo CRM, dove hai già un contratto, un accordo sul trattamento dati e un canale di supporto. Usalo con `only()`.

**Livello 3 — Tutto il resto.** Server della comunità, voci casuali nei registri, qualunque cosa non manutenuta. Trattali come codice non fidato. Per la produzione: leggi il sorgente, fissa una versione, eseguilo tu invece di collegarti a un'istanza ospitata, e combina `only()` con la tool approval per qualunque cosa abbia effetti collaterali.

Prototipare è diverso: il livello 3 va bene per una prova. La distinzione è fra "provarlo" e "metterlo in produzione".

### Stratifica le difese

I tool MCP sono comunque tool, quindi tutto il Capitolo 5 si applica:

```php
protected function tools(): array
{
    return [
        ...McpConnector::make([
            'url'   => env('CRM_MCP_URL'),
            'token' => env('CRM_MCP_TOKEN'),
        ])->only([
            'search_contacts',
            'get_contact',
        ])->tools(),
    ];
}
```

Nomi di tool in sola lettura nella lista di permessi. Aggiungi il middleware `ToolApproval` (Capitolo 15) per qualunque cosa scriva. E per un'integrazione davvero sensibile, valuta un proxy: avvolgi il server MCP in un tuo tool PHP che valida gli argomenti prima di inoltrarli, così hai un posto dove imporre le tue regole.

### Punti chiave

- I filtri MCP prendono stringhe con i nomi dei tool, non nomi di classe: niente analisi statica, quindi logga il conteggio.
- `only()` è obbligatorio per qualunque server che non controlli; i server guadagnano tool senza un tuo deploy.
- Ti stai fidando di descrizioni che non hai scritto: una superficie di prompt injection.
- Tre livelli di fiducia; sii esplicito su quale stai usando.

## Esercizi del capitolo

1. **Scopri.** Collegati a `server-everything` e logga quali tool vengono scoperti. Annota quanto impiega la costruzione: è latenza che pagheresti a ogni richiesta in contesto web.

2. **Restringi.** Riduci con `only()` a due tool e verifica che l'agent non possa usarne un terzo. Poi introduci un refuso nella lista di permessi e conferma che nulla ti avverte: quel silenzio è il motivo per cui la Sezione 9.4 ti chiede di loggare il conteggio.

3. **Classifica.** Per un'integrazione che costruiresti davvero, colloca il server in un livello di fiducia e metti per iscritto che cosa richiederesti prima di metterla in produzione. Se la risposta è "niente", confrontala con i quattro punti della sezione sulla fiducia.
