# Capitolo 23 — Produzione

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

Questo capitolo è concettuale e non ha codice a sé stante, ma il repository di accompagnamento [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) contiene le versioni eseguibili di tutto ciò che il libro costruisce.
:::

## 23.1 Controllo dei costi

### Prima misura

Non puoi gestire ciò che non registri. Logga l'uso a ogni esecuzione:

```php
class LogUsage
{
    public function handle($event): void
    {
        AiUsage::create([
            'tenant_id'     => $event->tenantId,
            'user_id'       => $event->userId,
            'agent'         => $event->agentClass,
            'provider'      => $event->provider,
            'model'         => $event->model,
            'input_tokens'  => $event->usage->inputTokens,
            'output_tokens' => $event->usage->outputTokens,
            'tool_calls'    => $event->toolCalls,
            'duration_ms'   => $event->durationMs,
        ]);
    }
}
```

Conferma l'accessore dell'uso sull'oggetto risposta nella tua versione installata.

Quattro domande a cui questo risponde e a cui nient'altro risponderà:

- Quale agent costa di più?
- Quale utente o tenant costa di più?
- Il costo per richiesta sta crescendo nel tempo?
- La modifica al prompt della settimana scorsa ha reso le cose più economiche o più care?

### Le tre leve, riviste

La Sezione 1.4 le nominava. In produzione hanno questo aspetto:

**Meno iterazioni.** Descrizioni dei tool più affilate (5.4), meno tool agganciati (5.8), limiti di esecuzione più bassi (5.9). Leggi i trace per trovare gli agent che ciclano.

**Contesto più piccolo.** Sfoltimento aggressivo della cronologia (4.4), output dei tool compatto (19.1), meno chunk RAG, riassunti ai confini fra agent (16.3).

**Modello più economico per passo.** `AIProvider::driver('ollama')` sul classificatore, il default sullo scrittore (17.6).

### Caching

La leva con la maggiore forza e la più trascurata, perché una risposta in cache non costa nulla:

```php
class CachedClassifier
{
    public function classify(string $text): string
    {
        return Cache::remember(
            'classify:' . \hash('xxh128', $text),
            now()->addDays(7),
            fn () => ClassifierAgent::make()
                ->structured(new UserMessage($text), Classification::class)
                ->label
        );
    }
}
```

**Metti in cache i compiti quasi deterministici:** classificazione, estrazione da un documento fisso, embedding di testo invariato, traduzione di una stringa fissa.

**Non mettere in cache le risposte conversazionali.** La stessa domanda in una conversazione diversa merita una risposta diversa.

**Il caching degli embedding è la vittoria più grande nel RAG.** Il testo che non è cambiato non ha bisogno di un nuovo embedding — che è esattamente a cosa serviva la guardia `wasChanged('body')` della Sezione 20.2.

### Budget

```php
// config/neuron.php
'budgets' => [
    'per_user_daily'   => env('AI_BUDGET_USER_DAILY', 2.00),
    'per_tenant_daily' => env('AI_BUDGET_TENANT_DAILY', 50.00),
    'global_daily'     => env('AI_BUDGET_GLOBAL_DAILY', 500.00),
],
```

Tre livelli perché falliscono in modi diversi: un ciclo impazzito per un utente, un'integrazione mal configurata per un tenant, un bug che colpisce tutti. Il tetto globale è la tua ultima linea di difesa.

**Imposta anche un limite di spesa rigido presso il provider.** La Sezione 3.7 lo diceva e vale la pena ripeterlo: i budget a livello applicativo dipendono dal fatto che il tuo codice sia corretto. Il tetto del provider no.

### Punti chiave

- Logga token, modello, agent e durata a ogni esecuzione.
- Tre leve: meno iterazioni, contesto più piccolo, modello più economico per passo.
- Metti in cache i compiti deterministici e gli embedding; non le conversazioni.
- Tre livelli di budget più un tetto rigido presso il provider.

## 23.2 Resilienza

### Rate limiting

I provider impongono i loro; tu dovresti imporre i tuoi per primo, così da ottenere un job in coda invece di una richiesta fallita:

```php
class RunAgent implements ShouldQueue
{
    public function middleware(): array
    {
        return [
            (new RateLimited('anthropic'))->dontRelease(),
        ];
    }
}
```

```php
// AppServiceProvider::boot()
RateLimiter::for('anthropic', fn () => Limit::perMinute(50));
```

### Timeout

```php
'timeout' => env('NEURON_HTTP_TIMEOUT', 60),
```

Impostali deliberatamente. Un agent che fa cinque chiamate con un timeout di 120 secondi può restare appeso per dieci minuti prima di fallire, occupando un worker per tutto il tempo.

### Ritentativi, con l'avvertenza

```php
class RunAgent implements ShouldQueue
{
    public int $tries = 3;
    public array $backoff = [10, 60, 180];

    public function retryUntil(): DateTime
    {
        return now()->addMinutes(15);
    }
}
```

**L'avvertenza conta più della configurazione.** Ritentare l'esecuzione di un agent rispende soldi e, per via del non determinismo, può produrre un risultato diverso. Ritenta il fallimento del *trasporto*, non il *ragionamento*.

La distinzione in pratica:

- Rate limit o errore di connessione prima di qualunque lavoro → sicuro da ritentare
- Fallimento dopo tre chiamate a tool inclusa una scrittura → **non ritentare alla cieca**; potresti duplicare la scrittura

Ecco perché la Sezione 21.5 metteva `$tries = 1` sul job del workflow. Per il lavoro degli agent, l'idempotenza (19.2) più un ritentativo deliberato battono un conteggio generoso di ritentativi.

### Fallback fra provider

Il ritorno più concreto dell'architettura a interfacce:

```php
class ResilientProviderFactory
{
    private const CHAIN = ['anthropic', 'openai', 'gemini'];

    public function make(): AIProviderInterface
    {
        foreach (self::CHAIN as $driver) {
            if (! $this->circuitOpen($driver)) {
                return AIProvider::driver($driver);
            }
        }

        throw new NoProviderAvailable('All configured providers are unavailable.');
    }

    private function circuitOpen(string $driver): bool
    {
        return Cache::get("circuit:{$driver}", 0) >= 5;
    }

    public function recordFailure(string $driver): void
    {
        Cache::increment("circuit:{$driver}");
        Cache::put("circuit:{$driver}:reset", true, now()->addMinutes(5));
    }
}
```

**Due avvertenze, così che questo non sembri un pasto gratis:**

**La qualità varia fra i provider.** Un prompt messo a punto per un modello può comportarsi sensibilmente peggio su un altro. Il fallback ti tiene disponibile; non ti tiene ugualmente bravo. Esegui le tue eval (Capitolo 10) contro ogni provider della catena così da sapere verso che cosa stai degradando.

**Alcune funzionalità non sono portabili.** I tool di provider (5.12) semplicemente svaniscono. Se un agent dipende da uno di essi, non ha fallback.

### Degradare con garbo

A volte la risposta giusta non è un altro provider:

```php
try {
    return $this->agent->chat(new UserMessage($question))->getMessage()->getContent();
} catch (\Throwable $e) {
    \Log::error('Agent unavailable', ['exception' => $e]);

    return $this->fallbackSearch($question);   // plain keyword search over the KB
}
```

Il risultato di una ricerca per parole chiave batte una pagina di errore. Gli utenti notano i disservizi; raramente notano una risposta leggermente peggiore.

### Punti chiave

- Applica un rate limit prima che lo faccia il provider; metti in coda invece di fallire.
- Ritenta i fallimenti di trasporto, non il ragionamento — le scritture possono duplicarsi.
- Le catene di fallback ti tengono disponibile, non ugualmente bravo; fai le eval su ogni provider della catena.
- Degrada verso funzionalità non-AI invece che verso una pagina di errore.

## 23.3 Osservabilità in produzione

### Inspector, con il pacchetto Laravel

```bash
composer require inspector-apm/inspector-laravel
```

L'SDK di NeuronAI lo suggerisce esplicitamente. Aggiungerlo correla il trace dell'agent con la richiesta HTTP, le query e il job in coda che gli stanno attorno — che è ciò che ti serve davvero quando diagnostichi un incidente. Senza, hai una linea temporale dell'agent che fluttua slegata dalla richiesta che l'ha prodotta.

```dotenv
INSPECTOR_INGESTION_KEY=...
```

**E sui worker:**

```php
$this->observe(
    InspectorObserver::instance(
        key: config('inspector.key'),
        autoFlush: true
    )
);
```

L'avvertimento della Sezione 10.2, per la terza e ultima volta: senza `autoFlush`, i trace dai queue worker non arrivano mai.

### Su che cosa mettere alert

Quattro segnali, e nessuno di essi è "si è verificata un'eccezione":

**Limiti di esecuzione dei tool superati.** La Sezione 5.9 diceva che è una diagnostica sul progetto dei tool. Un picco significa che una descrizione ha smesso di funzionare — spesso perché i dati sottostanti hanno cambiato forma.

**Punteggio di fedeltà in calo.** Dalla tua suite di eval (10.5), eseguita ogni notte. Un calo significa che la qualità del recupero è degradata, di solito perché i contenuti sono cambiati e l'indice non ha tenuto il passo.

**Costo per richiesta in crescita.** Cicli che si allungano, contesto che cresce, o una modifica al prompt che ha reso il modello più loquace.

**Arretrato di approvazioni in crescita.** Non è un problema di codice — è un problema di processo, e la tua dashboard lo farà emergere prima che qualcuno si lamenti.

### Che cosa loggare, e che cosa no

**Logga:** classe dell'agent, provider, modello, conteggi di token, durata, nomi dei tool, *forma* degli argomenti dei tool, esito, ID di workflow, ID di utente e tenant.

**Non loggare per default:** prompt completi, risposte complete, *valori* degli argomenti dei tool, contenuto dei documenti recuperati.

La Sezione 3.7 faceva questo punto; merita di essere ribadito qui. I prompt contengono qualunque cosa gli utenti abbiano digitato — nomi, indirizzi, numeri d'ordine, occasionalmente dati di pagamento. Loggare i prompt completi su scala crea un problema di conformità molto più difficile da sbrogliare che da evitare.

Quando ti serve davvero il contenuto per il debug, mettilo dietro un flag esplicito con conservazione breve, e mai attivo per default.

### L'ID di correlazione

```php
Log::withContext([
    'workflow_id' => $this->workflowId,
    'tenant_id'   => $this->tenantId,
    'agent'       => static::class,
]);
```

Una richiesta agentica tocca una richiesta HTTP, diversi job in coda, diverse chiamate al provider e possibilmente una decisione umana giorni dopo. Senza un ID di correlazione, ricostruire ciò che è successo significa tirare a indovinare dai timestamp.

### Punti chiave

- Aggiungi `inspector-laravel` per correlare i trace degli agent con richieste e job.
- `autoFlush: true` sui worker.
- Metti alert su limiti di esecuzione, fedeltà, costo per richiesta e arretrato di approvazioni.
- Logga forme e metadati; non il contenuto dei prompt.
- Correla tutto tramite l'ID di workflow.

## 23.4 Testing e CI

### I tre livelli

**Livello 1 — Test unitari. Veloci, gratuiti, deterministici, eseguiti a ogni commit.**

I tool sono comuni oggetti invocabili (Sezione 5.3):

```php
public function test_it_scopes_orders_to_the_tenant(): void
{
    $tool = new SearchOrdersTool($this->tenantA);

    Order::factory()->for($this->tenantB)->create(['number' => 'B-001']);

    $result = $tool(status: 'shipped');

    $this->assertStringNotContainsString('B-001', $result);
}
```

Nessun LLM. Nessuna rete. È qui che dovrebbe vivere la maggior parte della tua logica legata agli agent, ed è il motivo per cui la Sezione 5.3 argomentava a favore delle classi tool.

**Livello 2 — Test di integrazione con un provider finto.**

```php
$this->app->bind(SupportAgent::class, fn () => new FakeSupportAgent());

$this->postJson('/api/chat', ['message' => 'Where is my order?'])
     ->assertOk()
     ->assertJsonStructure(['answer']);
```

Testa il tuo controller, la tua validazione, la tua autorizzazione, la tua serializzazione. Tutto tranne il modello.

Il framework include utilità di testing — consulta la pagina Testing nella documentazione per i componenti finti attuali e adegua di conseguenza questo livello.

**Livello 3 — Eval. Lente, costano soldi, misurano la qualità (Capitolo 10).**

```bash
vendor/bin/neuron evaluation --path=evaluators
```

### Configurazione della CI

```yaml
jobs:
  test:
    steps:
      - run: composer install --prefer-dist --no-progress
      - run: vendor/bin/phpunit --testsuite=unit,integration
      - run: vendor/bin/phpstan analyse

  evals:
    if: github.event_name == 'schedule' || contains(github.event.head_commit.message, '[evals]')
    steps:
      - run: vendor/bin/neuron evaluation --path=evaluators --concurrency=5
        env:
          ANTHROPIC_KEY: ${{ secrets.ANTHROPIC_KEY }}
```

Tre regole dalla Sezione 10.6, ribadite perché è facile sbagliarle:

**Non subordinare ogni PR all'intera suite di eval.** Costa soldi ed è lenta. Ogni notte, più su richiesta con un tag nel commit.

**Non fallire su un singolo elemento.** Imposta una soglia sul tasso di successo. Su un sistema probabilistico un tasso di superamento del 95 % è una build sana, e trattare un elemento instabile come un fallimento insegna al team a ignorare del tutto il segnale.

**Tieni le chiavi API fuori dai fork.** Le eval sulle PR in un repository pubblico sono un modo per donare il tuo budget a degli sconosciuti.

### I test di sicurezza che devono bloccare i deploy

Due dalla Parte V, entrambi abbastanza deterministici da meritare fiducia:

```php
public function test_tenant_isolation(): void;                   // Section 18.3
public function test_restricted_articles_never_surface(): void;  // Section 20.3
```

Appartengono al livello 1 o 2, girano a ogni commit e bloccano il merge. Sono fra i pochi test attinenti all'AI che siano al tempo stesso affidabili e conseguenti.

### Punti chiave

- Tre livelli: unitari (ogni commit), integrazione con i fake (ogni commit), eval (ogni notte).
- I tool sono testabili senza un LLM — metti lì la logica.
- Soglia sul tasso di successo, non superato/fallito per singolo elemento.
- L'isolamento fra tenant e il recupero filtrato per permessi bloccano ogni deploy.

## 23.5 Sicurezza e privacy

### Il modello a strati, assemblato

| Strato | Meccanismo | Sezione |
|---|---|---|
| Capacità | Registra solo i tool che questo utente può usare | 5.1 |
| Visibilità | `visible()` dalle policy | 5.10, 19.3 |
| Autorizzazione | `Gate::forUser()` dentro il tool | 19.3 |
| Approvazione | `ToolApproval` sulle azioni conseguenti | 15.5 |
| Ambito dei dati | Filtri di tenant su tool e recupero | 18.3, 20.3 |
| Privilegio | Credenziali di database in sola lettura | 19.3 |
| Audit | Una riga per ogni chiamata a un tool conseguente | 19.3 |

**Ogni strato è indipendente.** Un bug in uno non sconfigge gli altri — che è tutto il senso della difesa in profondità, e la risposta a "non basta la visibilità?".

### Prompt injection, ancora una volta

Il principio della Sezione 19.3, che è la tesi di sicurezza dell'intero libro:

> Non cercare di convincere il modello a non fare qualcosa che ha la capacità di fare. Togli la capacità.

Le istruzioni competono con il testo iniettato e a volte perdono. Un tool assente non può essere invocato da nessun prompt, per quanto astuto.

Il testo non fidato entra da più posti di quanti le persone si aspettino: messaggi degli utenti, descrizioni di prodotti, ticket di supporto, documenti caricati, contenuti recuperati dal RAG, risposte di API di terze parti e output di tool MCP (9.4). Trattalo tutto come influenzabile da un attaccante.

### Flusso dei dati

Tre domande a cui rispondere per iscritto prima del lancio:

**Che cosa lascia la tua infrastruttura?** Ogni prompt va al provider. Questo include i documenti recuperati e i risultati dei tool. Se l'indirizzo di un cliente compare nel risultato di un tool, è andato al provider.

**Dove va?** Le regioni dei provider differiscono, e alcuni offrono elaborazione solo UE o in-regione. Per i clienti europei questo è spesso un requisito contrattuale più che una preferenza.

**Che cosa viene conservato?** I provider pubblicano politiche di conservazione; gli accordi enterprise spesso includono opzioni a conservazione zero. Leggile e metti per iscritto ciò che hai trovato.

### Punti di contatto con il GDPR

Cinque pratici, esposti come requisiti ingegneristici:

**Base giuridica.** Mandare dati personali a un responsabile del trattamento terzo ne richiede una. È una determinazione legale, non ingegneristica — coinvolgi un legale invece di deciderlo in fase di pianificazione dello sprint.

**Accordo sul trattamento dei dati.** Con ogni provider che usi.

**Diritto alla cancellazione.** Un utente chiede di essere cancellato. La sua cronologia chat è nella tua tabella `chat_messages` — cancellabile. I suoi dati dentro i log di un provider sono soggetti alla politica di conservazione di quel provider, ed ecco perché la conservazione zero conta.

**Diritto di accesso.** La cronologia chat e qualunque memoria a lungo termine (Sezione 4.5) sono dati personali che l'utente può richiedere.

**Processo decisionale automatizzato.** Se un agent prende una decisione con effetti giuridici o similmente significativi su qualcuno, l'articolo 22 del GDPR è rilevante. È un argomento forte a favore dell'human-in-the-loop sulle azioni conseguenti — il Capitolo 15 è una funzionalità di conformità oltre che di sicurezza.

Niente di tutto questo è consulenza legale; è l'elenco di domande da portare a chi la fornisce.

### La traccia di audit

```php
Schema::create('agent_actions', function (Blueprint $table) {
    $table->id();
    $table->foreignId('user_id')->nullable()->constrained();
    $table->foreignId('tenant_id')->constrained();
    $table->string('agent');
    $table->string('tool');
    $table->json('arguments');
    $table->text('result')->nullable();
    $table->string('workflow_id')->nullable();
    $table->boolean('approved')->default(false);
    $table->foreignId('approved_by')->nullable()->constrained('users');
    $table->timestamps();
});
```

Risponde alla domanda che prima o poi arriva: *"perché il sistema ha rimborsato quel cliente?"*

Senza, hai dei log, un trace che potrebbe essere scaduto e un'alzata di spalle. Con, hai una riga che nomina l'utente, il tool, gli argomenti, chi ha approvato e l'ora. In un ambiente regolamentato è la differenza fra distribuibile e non distribuibile.

### Punti chiave

- Sette strati indipendenti; un bug in uno non sconfigge gli altri.
- Togli la capacità invece di istruire contro di essa.
- Metti per iscritto che cosa esce, dove va e che cosa viene conservato.
- L'human-in-the-loop è una funzionalità di conformità ai sensi dell'articolo 22, non solo di sicurezza.
- Traccia in audit ogni azione conseguente su una tabella interrogabile.

## 23.6 La checklist di deploy

### Configurazione

- [ ] Versioni dei modelli **fissate esplicitamente**, non alias mobili (1.5)
- [ ] Provider impostato per ambiente; modello di embedding **identico ovunque** (12.4, 17.2)
- [ ] Context window ricavata dal provider configurato, non scritta a codice (4.4)
- [ ] Limite di spesa rigido impostato presso il provider (3.7)
- [ ] Chiavi API separate per ambiente
- [ ] Scansione dei segreti in CI

### Agent e tool

- [ ] Ogni tool di scrittura: `setMaxRuns(1)`, guardia di idempotenza, transazione (5.9, 19.2)
- [ ] Ogni tool: insieme di risultati limitato, selezione esplicita delle colonne, output compatto (19.1)
- [ ] Ogni tool: una frase esplicita per il caso vuoto (5.9)
- [ ] Visibilità dei tool calcolata dalle policy dell'attore (5.10, 19.3)
- [ ] `Gate::forUser()` dentro i tool che toccano record specifici (19.3)
- [ ] Gestore d'errore che restituisce istruzioni, non stack trace (5.11)
- [ ] Toolkit filtrati con `only()`, mai con `exclude()` (5.8)

### Dati

- [ ] Filtro di tenant applicato dentro `vectorStore()`, non nel punto di chiamata (20.1)
- [ ] Filtri di permesso applicati **al recupero**, mai dopo (20.3)
- [ ] `sourceName` stabile — ID dei record, mai i titoli (12.6, 20.2)
- [ ] `indexed_at` tracciato; un alert sullo scarto configurato (20.2)
- [ ] Credenziali di database in sola lettura per le query degli agent (19.3)

### Workflow

- [ ] `EloquentPersistence` per qualunque cosa sia interrompibile (18.4)
- [ ] Ogni chiamata a un LLM che precede un'interruzione avvolta in `checkpoint()` (15.5)
- [ ] `lockForUpdate()` alla risoluzione delle approvazioni (22.3)
- [ ] `expires_at` impostato; comando di scadenza schedulato (22.4)
- [ ] Richieste di interruzione piccole, piatte e versionate (22.4)
- [ ] Pulizia delle interruzioni orfane schedulata (22.4)

### Operatività

- [ ] Inspector configurato; `autoFlush: true` sui worker (10.2, 23.3)
- [ ] Uso dei token loggato per esecuzione (23.1)
- [ ] Budget: per utente, per tenant, globale (23.1)
- [ ] Rate limit configurati prima di quelli del provider (23.2)
- [ ] `$tries = 1` sui job degli agent, oppure idempotenza dimostrata (21.5, 23.2)
- [ ] Timeout impostati su PHP, FPM, proxy e provider (21.2, 23.2)
- [ ] Streaming verificato dall'inizio alla fine con `curl -N` attraverso l'intero stack (21.2)
- [ ] Canali di broadcast autorizzati per tenant (21.5)

### Qualità e sicurezza

- [ ] Suite di eval con un dataset costruito da domande reali (10.4)
- [ ] `FaithfulnessJudge` su ogni agent RAG (10.5)
- [ ] Test di isolamento fra tenant che blocca i deploy (18.3)
- [ ] Test di recupero filtrato per permessi che blocca i deploy (20.3)
- [ ] Tabella di audit popolata da ogni tool conseguente (19.3, 23.5)
- [ ] Contenuto dei prompt **non** loggato per default (3.7, 23.3)
- [ ] Accordi sul trattamento dei dati in essere; conservazione compresa (23.5)

### Le cinque domande a cui rispondere ad alta voce

Prima del lancio, devi saper rispondere a queste senza andare a cercare nulla:

1. **Quanto costa questo agent per richiesta, e a quale volume questo diventa un problema?**
2. **Qual è la cosa peggiore che può fare, e che cosa lo ferma?**
3. **Come farei a scoprire che cosa ha fatto, fra tre settimane?**
4. **Che cosa succede quando il provider è giù?**
5. **Quali dati lasciano la mia infrastruttura, e dove vanno?**

Se una qualunque risposta è un'alzata di spalle, quello è il prossimo pezzo di lavoro.

### Chiusura della Parte V

Ventitré capitoli fa il primo disegnava una scala a quattro pioli e chiedeva *chi decide che cosa succede dopo*. Tutto ciò che è venuto dopo è stato il macchinario necessario per lasciare che un modello rispondesse a quella domanda in sicurezza: tool per dargli le mani, struttura per rendere usabile il suo output, recupero per dargli conoscenza, workflow per dargli forma, interruzione per tenere un essere umano nella decisione, e osservabilità per scoprire che cosa abbia effettivamente fatto.

La seconda domanda di quell'elenco è quella con cui lasciarti:

> **Qual è la cosa peggiore che il tuo agent può fare, e che cosa lo ferma?**

Se sai rispondere a questa su un sistema che hai costruito, hai capito questo libro.

### Punti chiave

- Lavora la checklist sezione per sezione; ogni voce riporta a un capitolo.
- Le cinque domande sono il vero esame.
- Se una risposta è un'alzata di spalle, quello è il prossimo compito.
