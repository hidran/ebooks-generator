# Capitolo 25 — Progetto finale B: il support desk agentico

**Stack:** Laravel 13 su PHP 8.5 + `neuron-core/neuron-laravel`.
**Copre:** tutto ciò che c'è in questo libro.

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

I listati di questo capitolo sono specifiche da cui partire, non un progetto finito: per questo progetto finale non esiste una directory di accompagnamento. Il repository di accompagnamento [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) contiene le versioni eseguibili dei mattoni che il libro insegna.
:::

## Che cosa stai costruendo

Un'applicazione di assistenza clienti multi-tenant in cui un agent gestisce le richieste dall'inizio alla fine:

- Risponde alle domande sulle politiche attingendo a una knowledge base (RAG)
- Cerca ordini e stato delle spedizioni (tool)
- Prepara rimborsi, che si fermano per l'approvazione umana sopra una soglia (workflow + interruzione)
- Trasmette il proprio lavoro al cliente in tempo reale
- Fa escalation a un essere umano quando non può aiutare
- Registra tutto ai fini dell'audit

È il Caso C della Sezione 1.7 — quello in cui tutte e quattro le domande puntavano al quarto piolo. Si guadagna ogni pezzo del macchinario di questo libro, ed è esattamente per questo che è il progetto finale.

## L'architettura

```
Cliente (chat Livewire)
   │
   ├─ POST del messaggio
   │
SupportAgent (RAG + tool + EloquentMessageStore)
   │
   ├─ domanda sulle policy → recupero, filtrato per tenant + visibilità
   ├─ domanda sugli ordini → SearchOrdersTool / GetOrderStatusTool
   └─ richiesta di rimborso → RefundWorkflow
                          │
                          ├─ EligibilityNode   (structured output)
                          ├─ AmountNode        (tool: calcola il rimborso)
                          ├─ ApprovalNode      (interrompe se > soglia)
                          │      │
                          │      └─ workflow_store (run in pausa) + riga PendingApproval
                          │                                    │
                          │                              Il manager approva
                          │                                    │
                          │                          Job ResumeRefundWorkflow
                          │
                          └─ ExecuteRefundNode (idempotente, tracciato)
```

## Ordine di costruzione

**1 — Impostazione di Laravel.** `composer require`, pubblica la configurazione, una migration applicativa per `chat_messages` e `workflow_store`, i binding di `NeuronServiceProvider` del Capitolo 18, uno smoke test attraverso un agent risolto dal container e legato con `->for('smoke')` (la facade `Neuron` lancia un'eccezione su neuron-laravel 2.0.0, perché nessun ID di thread è legato), la struttura `app/Neuron`.

**2 — Scaffolding di dominio.** Tenant, utenti, ordini, rimborsi, articoli della knowledge base. Factory e seeder. Ancora nessuna AI — deliberatamente, così vedi quanto poco dell'applicazione sia agentico.

**3 — Il primo agent.** `SupportAgent` con iniezione delle dipendenze, `EloquentMessageStore` iniettato nell'agent, con tenant e utente portati nell'ID del thread, un controller, una semplice pagina Blade.

**4 — Ingestione della knowledge base.** Il job `IndexArticle`, uno splitter Markdown personalizzato, metadati per tenant e visibilità, l'alert sullo scarto di `indexed_at`.

**5 — RAG con filtri di permesso.** Un `DocumentSchema` che dichiara tenant e visibilità come filtrabili, `retrievalScope()` che li applica entrambi, il system prompt anti-allucinazione, e il test in CI che afferma che un articolo riservato non emerga mai.

**6 — Tool per gli ordini.** `SearchOrdersTool` e `GetOrderStatusTool` con il tenant come dipendenza del costruttore, selezione delle colonne, risultati limitati, stringhe per il caso vuoto.

**7 — Chat in streaming con Livewire.** `wire:stream`, etichette di attività dei tool attraverso un'allowlist, la checklist del buffering verificata contro lo staging.

**8 — Il workflow di rimborso.** Eventi, nodi, structured output `RefundEligibility`, il ciclo limitato, una sottoclasse di `WorkflowState`.

**9 — Human in the loop.** `interrupt()` con un `RefundApprovalRequest` personalizzato, `memoize()` attorno alla chiamata di idoneità, `DatabasePersistence` sulla tabella `workflow_store`, la tabella `PendingApproval` per la schermata del manager.

**10 — La schermata di approvazione.** Pagine indice e di dettaglio, una policy, risoluzione con `lockForUpdate()`, il job `ResumeRefundWorkflow`, che consegna la decisione con `ExecutionRequest::signal(RefundApprovalRequest::EVENT, $payload, expectedRunId: $runId, expectedExecutionAttempt: $attempt)`, notifiche con scadenza.

**11 — Osservabilità ed eval.** Inspector con il pacchetto Laravel (richiede `inspector-apm/inspector-php ^3.19`), sottoscritto esplicitamente (Sezione 10.2), logging dell'uso, una suite di eval con `FaithfulnessJudge`, i test di isolamento fra tenant e di permessi in CI.

**12 — Irrobustimento per la produzione.** Budget, rate limit, fallback fra provider, la tabella di audit, e la checklist di deploy della Sezione 23.6 percorsa voce per voce.

## Le tre parti più difficili

### 1. Il bug della memoizzazione

Costruiscilo prima sbagliato. Calcola l'idoneità al rimborso dentro `ApprovalNode` senza `memoize()`, interrompi, riprendi — e osserva che l'idoneità ricalcolata differisce da ciò che il manager ha approvato.

Poi avvolgila:

```php
$eligibility = $this->memoize('eligibility', fn () => EligibilityAgent::make()
    ->setThreadId($state->getWorkflowId() . ':eligibility')
    ->structured(
        new UserMessage($this->describeOrder($order)),
        RefundEligibility::class
    ));
```

Stesso contenuto alla ripresa. Il nodo interrotto viene comunque rieseguito dall'inizio — gli step durevoli saltano i nodi *completati*, non quello che si è messo in pausa — quindi il risultato memorizzato della closure è l'unica cosa che si frappone fra la decisione del manager e una generata da capo.

**Sono i venti minuti più preziosi del progetto finale** — un fallimento di correttezza dimostrabile, corretto in una riga, che nessun tutorial copre. In un workflow di rimborso è la differenza fra approvare un importo e pagarne un altro.

### 2. Esecuzione idempotente del rimborso

```php
class ExecuteRefundNode extends Node
{
    public function __invoke(RefundApproved $event, RefundState $state): StopEvent
    {
        $refund = DB::transaction(function () use ($event, $state) {
            $order = Order::where('tenant_id', $state->tenantId())
                ->whereKey($state->orderId())
                ->lockForUpdate()
                ->firstOrFail();

            $existing = $order->refunds()
                ->where('workflow_id', $state->getWorkflowId())
                ->first();

            if ($existing !== null) {
                return $existing;   // this workflow already refunded — return the same record
            }

            $refund = $order->refunds()->create([
                'amount'      => $event->amount,
                'reason'      => $event->reason,
                'workflow_id' => $state->getWorkflowId(),
                'approved_by' => $event->approvedBy,
            ]);

            // same transaction, same workflow ID: a re-run returns above and writes no second audit row
            AgentAction::record($state, 'execute_refund', ['refund_id' => $refund->id]);

            return $refund;
        });

        return new StopEvent(result: $refund->id);
    }
}
```

Il `workflow_id` sul record del rimborso è la chiave di idempotenza. Il motore dei workflow blocca la maggior parte dei duplicati prima che raggiungano questo nodo — una ripresa che porta una run o un tentativo non più validi viene rifiutata (un ID di run non valido lancia `StaleWorkflowRunException`, un tentativo non valido una semplice `WorkflowException`), e uno step completato non viene mai rieseguito — ma il fence protegge la contabilità interna del workflow, non il tuo provider di pagamento. Un job che va in timeout dopo il commit della riga del rimborso e prima di quello dello step eseguirà di nuovo questo nodo, ed è la chiave a far sì che quella seconda esecuzione restituisca il primo rimborso invece di crearne un altro. La riga di audit viene scritta nella stessa transazione, con la stessa chiave dell'ID del workflow, quindi nemmeno la riesecuzione ne scrive una seconda. La ricerca dell'ordine porta con sé il tenant: `RefundState` conserva l'ID del tenant accanto all'ID dell'ordine, e uno scope globale su `Order` svolgerebbe lo stesso compito.

Non è una questione di AI. È ordinaria igiene dei sistemi distribuiti, e conta qui perché i sistemi agentici ritentano e riprendono molto più dei tipici gestori di richieste.

### 3. Il percorso di escalation

Ogni agent ha bisogno di un modo per arrendersi:

```php
class EscalateTool extends Tool
{
    protected string $name = 'escalate_to_human';

    protected ?string $description = 'Hand this conversation to a human support agent. Use this when you cannot answer '
        . 'from the knowledge base, when the customer explicitly asks for a human, when the '
        . 'customer is upset, or when the request is outside what your tools can do. '
        . 'Using this tool is always an acceptable outcome — prefer it over guessing.';

    public function __construct(
        private readonly int $conversationId,
    ) {
    }

    protected function properties(): array
    {
        return [
            new ToolProperty(
                name: 'reason',
                type: PropertyType::STRING,
                description: 'One sentence for the human agent: why you are escalating.',
                required: true,
            ),
        ];
    }

    public function __invoke(string $reason): string
    {
        Conversation::findOrFail($this->conversationId)->escalate($reason);

        return 'This conversation has been passed to a human agent. '
             . 'Tell the customer someone will reply shortly.';
    }
}
```

> **"Using this tool is always an acceptable outcome — prefer it over guessing."**

Quella frase è la stringa più importante dell'applicazione. Senza una via d'uscita esplicita, un modello di fronte a una richiesta impossibile inventerà qualcosa, perché produrre una risposta è ciò che fa. Dargli un modo legittimo di fallire è la misura anti-allucinazione più efficace dell'intero sistema, e costa un tool.

## Griglia di valutazione

| Area | Criterio |
|---|---|
| **Isolamento** | Il test sui tenant passa con ID di conversazione che collidono |
| **Recupero** | Il test sugli articoli riservati passa; filtri dichiarati nel `DocumentSchema` e applicati dentro `retrievalScope()` |
| **Tool** | Delimitati dal costruttore; limitati; `visible()` dalle policy; tool di scrittura con tetto a 1 |
| **Workflow** | Ogni chiamata all'LLM che precede un'interruzione è memoizzata; cicli limitati |
| **Approvazione** | Risoluzione con `lockForUpdate()`; scadenza schedulata; ripresa inviata, non in linea, con i fence di run e di tentativo |
| **Idempotenza** | Il rimborso porta una chiave legata al workflow; la doppia ripresa crea un solo record |
| **Osservabilità** | Inspector registrato esplicitamente, sia sul web sia sui worker delle queue; uso loggato |
| **Qualità** | Suite di eval con `FaithfulnessJudge`; un punteggio di riferimento registrato |
| **Audit** | Ogni tool conseguente scrive una riga in `agent_actions` |
| **Escalation** | L'agent ha, e usa, un modo per arrendersi |

## L'esercizio finale

Rispondi per iscritto alle cinque domande della Sezione 23.6 sul tuo progetto finale:

1. Quanto costa questo agent per richiesta, e a quale volume questo diventa un problema?
2. Qual è la cosa peggiore che può fare, e che cosa lo ferma?
3. Come farei a scoprire che cosa ha fatto, fra tre settimane?
4. Che cosa succede quando il provider è giù?
5. Quali dati lasciano la mia infrastruttura, e dove vanno?

Scrivi le risposte invece di limitarti a pensarle. Quelle difficili da scrivere sono quelle in cui il sistema non è finito.

Chi sa rispondere a tutte e cinque su codice che ha scritto di persona ha finito questo libro nel modo che conta.
