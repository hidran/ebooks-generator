# Capitolo 16 — Sistemi multi-agente

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

Questo capitolo è concettuale e non ha codice a sé stante, ma il repository di accompagnamento [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) contiene le versioni eseguibili di tutto ciò che il libro costruisce.
:::

## 16.1 Pattern di orchestrazione

### Prima, la domanda scettica

I sistemi multi-agente si dimostrano benissimo e sono spesso la risposta sbagliata. Prima di adottarne uno, chiediti: **un solo agent con più tool basterebbe?**

Spesso sì. Ogni agent in più è un altro insieme di chiamate al modello, un altro system prompt da mantenere, un altro punto in cui il contesto si perde nella traduzione. L'aritmetica della Sezione 1.4 si applica per agent.

Il multi-agente si guadagna il posto quando: i sotto-compiti richiedono istruzioni genuinamente diverse, gli agent hanno bisogno di insiemi di tool o permessi diversi, oppure vuoi una revisione indipendente dell'output di un agent.

Il terzo è il caso più forte, e non riguarda davvero le capacità: riguarda l'**indipendenza**. Un agent che revisiona il proprio lavoro è un pessimo critico. Un agent separato con un system prompt da critico è migliore.

### I pattern

**Sequenziale.** Ricercatore → Scrittore → Editor. L'output di ogni stadio alimenta il successivo. Semplice, prevedibile, facile da debuggare. Il default, e spesso sufficiente.

**Supervisore.** Un coordinatore decide quale specialista invocare, riceve il risultato, decide che cosa viene dopo. Flessibile, e il più costoso: il supervisore fa una chiamata al modello per decisione.

**Parallelo.** Diversi agent lavorano simultaneamente su sotto-compiti indipendenti; un nodo di fusione combina. Veloce per lavoro genuinamente indipendente. La Sezione 14.2 ti dà il meccanismo.

**Dibattito / ciclo del critico.** Un generatore produce, un critico valuta, il generatore rivede. Ripeti finché il critico non è soddisfatto o si raggiunge il limite. È il ciclo della Sezione 14.1 con dentro due agent, ed è il pattern con il miglior rapporto qualità/complessità dell'elenco.

### Mappare i pattern su NeuronAI

Ciascuno è una forma di workflow che conosci già:

| Pattern | Meccanismo |
|---|---|
| Sequenziale | Catena di nodi, un evento ciascuno |
| Supervisore | Un nodo che restituisce un'unione di eventi degli specialisti |
| Parallelo | `ParallelEvent` con diramazioni con nome |
| Ciclo del critico | Tipo di ritorno unione che torna indietro |

**Nessuna API multi-agente speciale.** È il punto della Sezione 2.3 che arriva per l'ultima volta: un agent gira dentro un nodo, e comporre nodi è ciò che fanno i workflow.

### Disciplina sui costi

Una pipeline sequenziale a quattro agent è come minimo quattro chiamate al modello, di solito di più se qualcuno usa dei tool. Un ciclo del critico su tre giri è sei o più.

Due mitigazioni:

**Modelli diversi per agent.** Il ricercatore e il critico possono avere bisogno di un modello forte; il formattatore no. Lo scambio di provider della Sezione 3.6 è qui per nodo, ed è uno degli argomenti migliori del framework in un contesto multi-agente.

**Limita ogni ciclo.** Il contatore della Sezione 14.1, non negoziabile.

### Punti chiave

- Chiediti se basterebbe un solo agent con più tool; spesso basterebbe.
- La revisione indipendente è il caso più forte a favore del multi-agente.
- Quattro pattern: sequenziale, supervisore, parallelo, ciclo del critico.
- Nessuna API speciale: gli agent girano dentro i nodi.
- Varia il modello per agent; limita ogni ciclo.

## 16.2 Un agent come nodo

### L'involucro

```php
<?php

declare(strict_types=1);

namespace App\Workflow\Nodes;

use App\Agents\ResearchAgent;
use App\Workflow\Events\ProgressEvent;
use App\Workflow\Events\ResearchCompleted;
use App\Workflow\Events\TopicRequested;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\WorkflowState;

class ResearchNode extends Node
{
    public function __invoke(TopicRequested $event, WorkflowState $state): \Generator|ResearchCompleted
    {
        yield new ProgressEvent("Researching {$event->topic}...");

        $findings = ResearchAgent::make()
            ->chat(new UserMessage("Research this topic thoroughly: {$event->topic}"))
            ->getMessage()
            ?->getContent() ?? '';

        $state->set('sources_used', $this->countSources($findings));

        return new ResearchCompleted($event->topic, $findings);
    }
}
```

Il nodo è un adattatore sottile. Tutta l'intelligenza — provider, istruzioni, tool — vive in `ResearchAgent`, che è invariato e funziona ancora da solo.

Vale la pena dirlo esplicitamente: `ResearchAgent` non sa di essere dentro un workflow. Puoi ancora testarlo con test unitari, chiamarlo direttamente, riusarlo in un'altra pipeline. Il nodo è colla.

`getMessage()` è nullable — una run che è terminata sospesa, o senza alcuna risposta dell'assistente, non ne ha — da qui il `?->` e il fallback.

### Un agent è un workflow dentro un nodo

`Agent` estende `Workflow`: `chat()` esegue fino al completamento il grafo di nodi dell'agent stesso e restituisce il suo `AgentState`. Quindi un workflow multi-agente è, letteralmente, un insieme di workflow che girano dentro i nodi di un workflow. Ne seguono tre conseguenze.

**L'agent si chiama, non si aggiunge.** Un agent non è un nodo: non puoi passarlo ad `addNodes()`. Il nodo è il punto in cui decidi che cosa entra nell'agent e che cosa ne esce.

**La run interna è separata.** Un sotto-agent creato con `make()` e senza thread ID gira in forma anonima, con persistenza in memoria e cronologia in memoria: non condivide nulla con lo stato o lo store del workflow esterno. Di solito è ciò che vuoi per uno stadio di una pipeline. La durabilità del workflow esterno lo copre comunque a livello di step: una volta completato `ResearchNode`, il suo risultato è registrato, e una ripresa o un recupero lo ripropone invece di chiamare di nuovo l'agent. Ciò che *non* è coperto è il nodo in esecuzione nel momento in cui avviene la pausa o il crash; avvolgi le sue chiamate all'agent in `memoize()` (Sezione 15.5), come fa il Laboratorio 10.

**La pausa di un sotto-agent non si propaga.** Se dai a un sotto-agent un tool soggetto ad approvazione (Sezione 15.5), la sua `chat()` restituisce un `AgentState` interrotto, e il nodo che legge `getMessage()` riceverebbe la chiamata a tool in sospeso invece di una risposta. Tieni i tool soggetti ad approvazione fuori dagli agent di pipeline, oppure controlla `isInterrupted()` nel nodo e porta la domanda al workflow esterno con un suo `interrupt()`.

### Structured output fra agent

Passare prosa fra gli agent perde informazione e invita all'errore di interpretazione. Passa invece oggetti tipizzati:

```php
class ReviewNode extends Node
{
    public function __invoke(DraftCompleted $event, WorkflowState $state): DraftCompleted|ArticleApproved
    {
        $verdict = ReviewerAgent::make()->structured(
            new UserMessage($event->draft),
            Verdict::class
        );

        if ($verdict->approved) {
            return new ArticleApproved($event->draft);
        }

        $state->set('last_feedback', $verdict->feedback);

        return new DraftCompleted($event->draft, $verdict->feedback);
    }
}
```

```php
class Verdict
{
    #[SchemaProperty(description: 'Whether the draft meets the quality bar.', required: true)]
    public bool $approved;

    #[SchemaProperty(
        description: 'If not approved, the specific changes required. One instruction per sentence.',
        required: true
    )]
    public string $feedback;

    #[SchemaProperty(description: 'Quality score from 0 to 10.', required: true)]
    #[GreaterThanEqual(reference: 0)]
    #[LowerThanEqual(reference: 10)]
    public int $score;
}
```

**È il Capitolo 6 che fa lavoro strutturale.** `$verdict->approved` è un booleano su cui il tuo PHP ramifica. Fare il parsing di "la bozza mi sembra buona!" per ricavarne un sì o un no sarebbe un lancio di monetina.

La regola: **structured output a ogni confine fra agent.** La prosa è per gli esseri umani.

### Provider diversi per nodo

```php
class DraftNode extends Node
{
    public function __invoke(ResearchCompleted $event, WorkflowState $state): DraftCompleted
    {
        // Strong model — this is the creative work
        $draft = WriterAgent::make()->chat(/* ... */)->getMessage()?->getContent() ?? '';

        return new DraftCompleted($draft);
    }
}

class FormatNode extends Node
{
    public function __invoke(ArticleApproved $event, WorkflowState $state): StopEvent
    {
        // Cheap model — mechanical transformation
        $formatted = FormatterAgent::make()->chat(/* ... */)->getMessage()?->getContent() ?? '';

        return new StopEvent(result: $formatted);
    }
}
```

Ogni agent dichiara il proprio provider. La stratificazione dei costi in un sistema multi-agente è una proprietà di come hai scritto gli agent, non qualcosa che configuri a parte.

### Punti chiave

- Il nodo è un adattatore sottile; l'agent resta indipendente e testabile.
- Un agent è un workflow: chiamalo da un nodo, memoizza la chiamata se il nodo può andare in pausa, e tieni i tool soggetti ad approvazione fuori dai sotto-agent.
- Usa `structured()` a ogni confine fra agent: la prosa perde informazione.
- Fai yield dell'avanzamento dai nodi-agent; le esecuzioni sono abbastanza lunghe da averne bisogno.
- La scelta del provider è per agent, quindi la stratificazione dei costi è gratuita.

## 16.3 Contesto senza esplosione di token

### Il modo di fallire

La pipeline multi-agente ingenua accumula. L'agent 1 produce 800 parole. L'agent 2 le riceve più il prompt originale e ne produce 1.200. L'agent 3 riceve tutto e produce 1.500. L'agent 4 riceve il tutto.

Al quarto agent stai mandando 4.000 parole di contesto per produrre 300 parole di output — e la Sezione 1.4 ha già mostrato che cosa fa l'accumulo ai costi.

### Quattro tecniche

**1. Passa l'artefatto, non la trascrizione.**

Allo scrittore servono i *risultati* della ricerca. Non gli serve il ragionamento del ricercatore, né le sue chiamate a tool, né le sue bozze intermedie.

```php
// Bad: the whole conversation
return new ResearchCompleted($agent->getChatHistory()->getMessages());

// Good: just the output
return new ResearchCompleted($event->topic, $findings);
```

**2. Riassumi al confine.**

Quando l'output di un agent è davvero grande, aggiungi un passo di compressione. Una chiamata a un modello economico per ridurre 3.000 parole a 400 fa risparmiare molto più di quanto costi su qualunque pipeline con due o più agent a valle.

**3. Usa lo stato per il contesto condiviso, gli eventi per il passaggio di consegne.**

La distinzione della Sezione 13.2, applicata. Il tenant, l'utente, il brief — stato. L'artefatto specifico che questo nodo ha prodotto per il successivo — evento.

**4. Dai a ogni agent solo ciò che gli serve.**

```php
class FactCheckNode extends Node
{
    public function __invoke(DraftCompleted $event, WorkflowState $state): FactCheckCompleted
    {
        // The fact-checker gets claims and sources. Not the draft's prose,
        // not the brief, not the research narrative.
        $result = FactCheckAgent::make()->structured(
            new UserMessage(json_encode([
                'claims'  => $event->extractedClaims,
                'sources' => $state->get('sources'),
            ])),
            FactCheckResult::class
        );

        return new FactCheckCompleted($result);
    }
}
```

È ordinaria progettazione di interfacce — input minimi ed espliciti — applicata agli agent. **Ogni agent ha un'interfaccia, e un'interfaccia larga è cattiva qui come ovunque.**

### Misurarlo

Iscrivi Inspector al workflow e ai suoi agent (Capitolo 10) e leggi i token in ingresso per nodo lungo l'esecuzione. Se crescono linearmente lungo la pipeline, stai accumulando. Quel numero è il tuo obiettivo di ottimizzazione, ed è visibile invece che ipotizzato.

### Punti chiave

- Passa artefatti, non trascrizioni.
- Riassumi ai confini quando l'output è grande.
- Stato per il contesto condiviso, eventi per i passaggi di consegne.
- Tratta l'input di ogni agent come un'interfaccia: tienilo minimo.
- Leggi i token in ingresso per nodo nel trace per trovare l'accumulo.

## 16.4 Esecuzione asincrona

### Perché non è opzionale

Somma quello che la Parte IV ha stabilito:

- Un'esecuzione multi-agente sono molte chiamate al modello (Sezione 16.1)
- Ciascuna dura 1–4 secondi (Sezione 1.4)
- Le chiamate parallele ai tool richiedono la CLI (Sezione 5.13)
- L'human-in-the-loop significa aspettare ore o giorni (Sezione 15.1)

Un workflow da 60 secondi non può vivere in una richiesta HTTP. Qualunque cosa con un'interruzione *certamente* non può.

**I workflow lunghi appartengono a una coda.**

### L'architettura

```
Richiesta HTTP → invia un job → restituisci subito un workflow ID
Queue worker   → esegui il workflow → fai streaming dell'avanzamento su un canale
                                     → persisti eventuali interruzioni
Essere umano   → risponde via interfaccia/email
Queue worker   → riprendi il workflow → completa
Client         → riceve avanzamento e risultato sul trasporto
```

Quattro pezzi che hai già:

- **Persistenza** (Sezione 15.4) per lo stato di interruzione
- **Stream adapter e canali** (Sezione 7.5): l'adapter dà forma agli eventi, il canale (`setChannel()`) li spinge verso un trasporto
- **Workflow ID** come chiave di correlazione
- **Coda** come contesto di esecuzione

### Che cosa cambia su un worker

**`pcntl` diventa disponibile**, quindi le chiamate parallele ai tool (Sezione 5.13) e le eval parallele (Sezione 10.6) funzionano.

**Il monitoraggio va collegato dove il worker costruisce i suoi agent.** Inspector è un listener che sottoscrivi su ogni agent e ogni workflow (Capitolo 10); nulla viene collegato globalmente. Un worker non ha una fine della richiesta, quindi il subscriber invia ogni trace quando termina il workflow che ha avviato. La misconfigurazione più probabile in un deploy asincrono è un worker i cui agent non sono mai stati iscritti, il che non produce alcun trace e nessun errore.

**Nessuna connessione HTTP con l'utente.** Ed è per questo che contano i canali di streaming: collega un `PusherChannel` o un `RedisChannel` con `setChannel()`, il worker pubblica attraverso di esso, il browser ascolta.

**I timeout sono affar tuo.** I queue worker hanno limiti di tempo. Un workflow che gira per dieci minuti ha bisogno di un worker configurato per farlo, oppure deve interrompersi e riprendere fra job diversi. E un worker ucciso a metà run — timeout, limite di memoria — lascia la run marcata come in esecuzione. Un agent detiene per impostazione predefinita un lease di dieci minuti, dopo i quali la run successiva sostituisce quella morta; un workflow semplice lo attiva con `setLeaseTimeout($seconds)`. Scegli un lease più lungo del tuo nodo più lento.

### Il pattern che lega insieme la Parte IV

Per un workflow lungo e filtrato da esseri umani, ogni segmento fra le interruzioni è un job a sé:

```
Job 1: esegui fino all'interruzione di approvazione → persisti → notifica il manager → fine
       (il worker è libero)
Job 2: innescato dall'approvazione → riprendi → esegui fino al completamento o alla prossima interruzione
```

Il worker non resta bloccato ad aspettare. Fra un segmento e l'altro non c'è alcun processo: solo righe in `workflow_store`, sotto il workflow ID della run.

Il Job 2 deve portare con sé il run ID e il tentativo di esecuzione che ha visto quando è stata registrata l'interruzione, e passarli a `resume($payload, expectedRunId: ..., expectedExecutionAttempt: ...)` (Sezione 15.4). Un job ritentato fallisce allora in modo pulito invece di consegnare una risposta obsoleta a una run che è andata avanti.

È ciò che "riprendi anche fra sessioni diverse" significa sul piano operativo. Ed è anche, per un pubblico PHP abituato all'esecuzione legata alla richiesta, una risoluzione davvero soddisfacente: l'assenza di stato di PHP smette di essere una limitazione e diventa il modello di distribuzione.

### Punti chiave

- Le esecuzioni multi-agente lunghe appartengono a una coda; quelle con un'interruzione certamente.
- Su un worker: `pcntl` funziona, il monitoraggio va iscritto esplicitamente, i lease coprono i worker uccisi, e non c'è connessione HTTP con l'utente.
- Ogni segmento fra le interruzioni è un job a sé; nulla aspetta.
- Persistenza, adapter e canali, workflow ID e coda sono i quattro pezzi, e li hai già tutti.

## Laboratorio 10 — La fabbrica di contenuti

**Copre:** tutta la Parte IV.

### Obiettivo

Ricerca → bozza → ciclo di revisione → approvazione umana → pubblicazione. È il workflow multi-agente canonico ed esercita cicli, stato, streaming, interruzione, memoizzazione e persistenza in un unico artefatto.

### La forma

```
StartEvent
   ↓
ResearchNode        (toolkit Tavily)
   ↓ ResearchCompleted
DraftNode           (agent scrittore)
   ↓ DraftCompleted
ReviewNode          (agent critico, Verdict strutturato)
   ↓ DraftCompleted (torna indietro, max 3)  |  ArticleApproved
                                             ↓
ApprovalNode        (interruzione — l'umano revisiona e modifica)
   ↓ ArticleEdited
PublishNode
   ↓ StopEvent
```

### Gli eventi

```php
<?php

declare(strict_types=1);

namespace App\Workflow\Events;

use NeuronAI\Workflow\Events\Event;

final class ResearchCompleted implements Event
{
    public function __construct(
        public readonly string $topic,
        public readonly string $findings,
    ) {}
}

final class DraftCompleted implements Event
{
    public function __construct(
        public readonly string $draft,
        public readonly ?string $feedback = null,
    ) {}
}

final class ArticleApproved implements Event
{
    public function __construct(
        public readonly string $draft,
    ) {}
}

final class ArticleEdited implements Event
{
    public function __construct(
        public readonly string $content,
    ) {}
}
```

Nota i nomi — fatti al passato, secondo la Sezione 13.4. Nota anche `readonly`: gli eventi sono messaggi, non contenitori mutabili.

### Lo stato

```php
<?php

declare(strict_types=1);

namespace App\Workflow;

use NeuronAI\Workflow\WorkflowState;

class ContentState extends WorkflowState
{
    protected int $revisions = 0;
    protected array $feedbackLog = [];

    public function recordRevision(string $feedback): self
    {
        $this->revisions++;
        $this->feedbackLog[] = $feedback;
        return $this;
    }

    public function revisionCount(): int
    {
        return $this->revisions;
    }

    public function hasReachedLimit(int $max = 3): bool
    {
        return $this->revisions >= $max;
    }

    public function feedbackHistory(): array
    {
        return $this->feedbackLog;
    }
}
```

Solo scalari e array — niente connessioni, niente risorse. Il vincolo di serializzazione della Sezione 14.3, rispettato per progetto.

### Il nodo di revisione — dove la parte si ricompone

```php
<?php

declare(strict_types=1);

namespace App\Workflow\Nodes;

use App\Agents\ReviewerAgent;
use App\Dto\Verdict;
use App\Workflow\ContentState;
use App\Workflow\Events\ArticleApproved;
use App\Workflow\Events\DraftCompleted;
use App\Workflow\Events\ProgressEvent;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Workflow\Node;

class ReviewNode extends Node
{
    public function __invoke(
        DraftCompleted $event,
        ContentState $state
    ): \Generator|DraftCompleted|ArticleApproved {
        yield new ProgressEvent('Reviewing the draft...');

        $verdict = ReviewerAgent::make()->structured(
            new UserMessage($event->draft),
            Verdict::class
        );

        if ($verdict->approved) {
            yield new ProgressEvent("Approved with a score of {$verdict->score}/10.");

            return new ArticleApproved($event->draft);
        }

        if ($state->hasReachedLimit()) {
            yield new ProgressEvent('Revision limit reached — sending to human review as is.');

            return new ArticleApproved($event->draft);
        }

        $state->recordRevision($verdict->feedback);

        yield new ProgressEvent("Revision {$state->revisionCount()}: {$verdict->feedback}");

        return new DraftCompleted($event->draft, $verdict->feedback);
    }
}
```

Ogni concetto della Parte IV in una sola classe: un tipo di ritorno unione (14.1), un ciclo limitato con un piano per il limite (14.1), stato personalizzato (14.3), avanzamento in streaming (14.4) e structured output a un confine fra agent (16.2).

### Il nodo di approvazione

```php
class ApprovalNode extends Node
{
    public function __invoke(ArticleApproved $event, ContentState $state): ArticleEdited
    {
        $payload = $this->interrupt(
            new ContentReviewInterrupt(
                message: \sprintf(
                    'Article ready after %d revision(s). Review and edit before publishing.',
                    $state->revisionCount()
                ),
                content: $event->draft
            )
        );

        return new ArticleEdited($payload['content'] ?? $event->draft);
    }
}
```

L'essere umano modifica invece di approvare — il pattern collaborativo della Sezione 15.3. Il testo modificato torna nel payload; se il revisore non manda nulla per `content`, la bozza passa invariata.

### Il workflow

```php
/** @extends Workflow<ContentState> */
class ContentWorkflow extends Workflow
{
    protected function state(): ContentState
    {
        return new ContentState();
    }

    protected function nodes(): array
    {
        return [
            new ResearchNode(),
            new DraftNode(),
            new ReviewNode(),
            new ApprovalNode(),
            new PublishNode(),
        ];
    }
}
```

L'hook `state()` fa partire ogni run con un `ContentState`, e l'annotazione `@extends` dice all'analisi statica che `run()` ne restituisce uno — così `$state->revisionCount()` supera il controllo dei tipi nel punto di chiamata senza bisogno di un cast.

### La dimostrazione della memoizzazione

Fallo deliberatamente. Sono i venti minuti più preziosi della Parte IV, perché trasformano un avvertimento astratto in un bug che hai causato di persona.

Scrivi `ApprovalNode` in modo che la bozza venga *generata* al suo interno, senza memoizzazione:

```php
// DELIBERATELY WRONG — reproduce the bug before fixing it
$draft = WriterAgent::make()->chat(new UserMessage($brief))->getMessage()?->getContent() ?? '';

$payload = $this->interrupt(new ContentReviewInterrupt('Review before publishing.', $draft));
```

Eseguilo, interrompi, riprendi. La bozza viene rigenerata e **la versione ripresa differisce da quella approvata dall'essere umano.**

Poi avvolgila:

```php
$draft = $this->memoize('draft', fn (): string => WriterAgent::make()
    ->chat(new UserMessage($brief))
    ->getMessage()
    ?->getContent() ?? '');
```

Riesegui. Stessa bozza. Lo stesso contenuto che l'essere umano ha visto.

Non è un argomento di efficienza. È un fallimento di correttezza dimostrabile con una correzione di una riga, ed è il motivo per cui esiste la Sezione 15.5.

### Eseguirlo

```php
$workflow = ContentWorkflow::make()
    ->setPersistence(new FilePersistence(__DIR__ . '/../storage/workflows'));

$stream = $workflow->events();

// No adapter and no channel attached, so events() returned a Generator.
\assert($stream instanceof \Generator);

foreach ($stream as $event) {
    if ($event instanceof ProgressEvent) {
        echo "  {$event->message}\n";
    }
}

$state = $stream->getReturn();

if (!$state->isInterrupted()) {
    echo "\nPublished.\n";
    exit(0);
}

$id = $state->getWorkflowId();

\file_put_contents(
    __DIR__ . "/../storage/pending/{$id}.json",
    \json_encode($state->getInterruptRequest(), JSON_PRETTY_PRINT)
);

echo "\nAwaiting review. Workflow ID: {$id}\n";
echo "Edit storage/pending/{$id}.json and run: php examples/11-resume.php {$id}\n";
```

`events()` è il terminale di streaming della Sezione 14.4: un generator che fa yield di ciò di cui fanno yield i nodi, nel momento in cui lo fanno, e restituisce lo stato finale tramite `getReturn()`. Fa yield anche di oggetti del framework — fra cui l'evento che segna la pausa — ed è per questo che il ciclo filtra su `ProgressEvent`. Come con `run()`, la pausa non viene sollevata; la leggi sullo stato restituito.

E lo script di ripresa, in un processo separato:

```php
$edited = \json_decode((string) \file_get_contents(__DIR__ . "/../storage/pending/{$id}.json"), true);

$state = ContentWorkflow::make(workflowId: $id)
    ->setPersistence(new FilePersistence(__DIR__ . '/../storage/workflows'))
    ->signal('content.reviewed', ['content' => $edited['content']])
    ->run();

echo $state->get('published');
```

Gli step già completati di ricerca, bozza e revisione non vengono rieseguiti. Solo `ApprovalNode` si riesegue, riceve il contenuto modificato e lo passa a `PublishNode`.

Modificare un file JSON su disco come "interfaccia di approvazione" è esattamente giusto per un laboratorio CLI. Rende visibile il meccanismo, e il Capitolo 22 lo sostituisce con una vera schermata di amministrazione.

### Criteri di accettazione

- Il ciclo di revisione gira al massimo tre volte, e raggiungere il limite fa scattare l'escalation invece di fallire.
- Uccidere il processo PHP dopo l'interruzione e riprendere da un processo nuovo produce l'articolo pubblicato.
- Con `memoize()` in atto, il contenuto pubblicato è identico byte per byte a ciò che la richiesta di interruzione ha mostrato all'essere umano. Senza, non lo è: dimostra entrambe le cose.
- Le righe di avanzamento compaiono mentre il workflow gira, non tutte alla fine.

### Estensioni

1. Aggiungi una diramazione parallela: verifica dei fatti e analisi SEO girano in concorrenza dopo l'approvazione, fuse prima della pubblicazione.
2. Aggiungi `interruptIf()` così che solo gli articoli con punteggio sotto 8 richiedano revisione umana.
3. Sposta l'esecuzione su un queue worker e fai streaming dell'avanzamento su un websocket.

## Esercizi del capitolo

1. **Costruisci la pipeline.** Un workflow sequenziale a tre agent con structured output a ogni confine.
2. **Aggiungi un ciclo del critico** con un contatore limitato e un piano per il raggiungimento del limite. Il piano conta più del contatore.
3. **Interrompi e riprendi.** Aggiungi un'interruzione prima dell'azione finale; persistila; riprendi da uno script separato — un processo genuinamente separato, non una seconda chiamata nello stesso.
4. **Memoizza tutto.** Avvolgi ogni chiamata all'LLM che precede un'interruzione in un `memoize()` e verifica che non venga rieseguita. Logga dentro la closure per dimostrarlo.
5. **Riduci l'accumulo.** Misura i token in ingresso per nodo e abbassane la crescita. Scrivi i numeri prima e dopo uno accanto all'altro.
