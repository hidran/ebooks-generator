# Capitolo 24 — Progetto finale A: la CLI che verifica un repository

**Stack:** PHP puro + Composer. Nessun framework.
**Copre:** dai Capitoli 3 al 10 — l'intera Parte II.

Questo progetto finale è specificato, non risolto. Enuncia requisiti e criteri di accettazione e lascia a te il progetto.

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

Questo capitolo è concettuale e non ha codice a sé stante, ma il repository di accompagnamento [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) contiene le versioni eseguibili di tutto ciò che il libro costruisce.
:::

## Che cosa stai costruendo

Un agent da riga di comando che verifica un repository PHP e produce un report strutturato:

```bash
php auditor.php /path/to/repo --format=json
```

```
Auditing /home/hidran/projects/shop ...

  Reading composer.json
  Scanning source tree (412 files)
  Checking dependency advisories
  Reading recent commit history
  Analysing test coverage configuration

━━━ Repo Audit: shop ━━━

Health score       62 / 100
PHP constraint     ^8.1  (consider ^8.3)
Dependencies       47 direct, 3 with known advisories
Test setup         PHPUnit present, no coverage threshold configured
Commit cadence     14 commits in the last 30 days, 2 contributors

Findings (7)
  [high]   Package X has advisory CVE-... — upgrade to 2.4.1
  [medium] No CI configuration found
  [medium] 23 files exceed 400 lines
  ...

Written to audit-shop-2026-08-10.json
```

## Perché questo progetto

**Non ha dipendenze esterne.** Nessuna chiave API oltre a quella dell'LLM, nessun database, nessun servizio. Puoi completarlo su un portatile, offline, con Ollama.

**I tool sono genuinamente utili.** Leggere file, eseguire `git log`, fare il parsing di `composer.json` — sono le forme di tool di cui la maggior parte degli agent reali ha bisogno.

**Esercita l'intera superficie della Parte II** senza alcuna conoscenza di Laravel, il che ne fa un pezzo da portfolio autonomo se lavori in Symfony, WordPress o uno stack legacy.

## Ordine di costruzione

### Fase 1 — Scaffolding e il primo agent

- Impostazione del progetto dalla Sezione 3.1
- `ProviderFactory` dalla Sezione 3.6
- `AuditorAgent` con un `SystemPrompt` che lo stabilisce come revisore di codice, non come correttore di codice
- Un punto d'ingresso CLI che accetta un argomento di percorso

### Fase 2 — I tool per il file system

Aggancia `FileSystemToolkit` con `only()`, e scrivi due tool personalizzati:

```php
class ComposerManifestTool extends Tool
{
    public function __construct(private readonly string $repoPath)
    {
        parent::__construct(
            'read_composer_manifest',
            'Returns the composer.json of the repository being audited: the PHP version '
            . 'constraint, the direct dependencies with their version constraints, the '
            . 'autoload configuration, and the declared scripts. Use this first, before any '
            . 'other analysis, to understand what kind of project this is. Never guess a '
            . 'dependency version — read it here.'
        );
    }

    protected function properties(): array
    {
        return [];   // no arguments — the path is a constructor dependency
    }

    public function __invoke(): string
    {
        $path = $this->repoPath . '/composer.json';

        if (! \is_file($path)) {
            return 'No composer.json found. This may not be a PHP project.';
        }

        $manifest = \json_decode(\file_get_contents($path), true, 512, JSON_THROW_ON_ERROR);

        return \json_encode([
            'name'        => $manifest['name']      ?? null,
            'php'         => $manifest['require']['php'] ?? null,
            'require'     => $manifest['require']     ?? [],
            'require-dev' => $manifest['require-dev'] ?? [],
            'scripts'     => \array_keys($manifest['scripts'] ?? []),
        ], JSON_THROW_ON_ERROR);
    }
}
```

**Due cose da notare.**

Il tool non ha **alcuna property** — il percorso del repository è una dipendenza del costruttore, non qualcosa che il modello sceglie. È deliberato: un percorso fornito dal modello è un path traversal in attesa di accadere. Il principio della Sezione 5.1, applicato concretamente.

Il valore di ritorno è un manifesto **ridotto**, non l'intero file. L'argomento sul costo in token della Sezione 19.1, in un contesto di PHP puro.

### Fase 3 — Il tool git e l'esecuzione sicura di sottoprocessi

```php
class GitHistoryTool extends Tool
{
    public function __construct(private readonly string $repoPath) { /* ... */ }

    protected function properties(): array
    {
        return [
            new ToolProperty(
                name: 'days',
                type: PropertyType::NUMBER,
                description: 'How many days of history to summarise. Example: 30. Maximum 365.',
                required: true,
            ),
        ];
    }

    public function __invoke(int $days): string
    {
        $days = \max(1, \min(365, $days));   // clamp, never trust the model

        $process = new Process(
            ['git', 'log', "--since={$days} days ago", '--pretty=format:%h|%an|%ad|%s', '--date=short'],
            $this->repoPath,
        );

        $process->setTimeout(15);
        $process->run();

        if (! $process->isSuccessful()) {
            return 'Could not read git history. This may not be a git repository.';
        }

        $lines = \array_slice(\explode("\n", \trim($process->getOutput())), 0, 100);

        return $lines === [''] ? 'No commits in this period.' : \implode("\n", $lines);
    }
}
```

**Tre cose che questo fa bene, e ciascuna di esse conta:**

**Array di argomenti, mai interpolazione di stringhe.** `['git', 'log', "--since={$days} days ago"]` con Symfony Process passa gli argomenti senza una shell. Interpolare un valore fornito dal modello dentro una stringa di shell è esecuzione di codice remoto con qualche passaggio in più.

**Limita l'input numerico.** `max(1, min(365, $days))`. Il modello potrebbe mandare 99999. Gli attributi di validazione servono per lo structured output; gli argomenti dei tool li validi tu.

**Metti un limite all'output.** `array_slice(..., 0, 100)`. Un repository con 40.000 commit metterebbe altrimenti 40.000 righe nella conversazione.

### Fase 4 — Structured output

Il DTO `AuditReport`, che usa tutto ciò che viene dal Capitolo 6:

```php
class Finding
{
    #[SchemaProperty(description: 'Severity: one of high, medium, low.', required: true)]
    #[Regex('/^(high|medium|low)$/')]
    public string $severity;

    #[SchemaProperty(description: 'Category, e.g. dependencies, testing, structure, security.', required: true)]
    #[NotBlank]
    public string $category;

    #[SchemaProperty(description: 'What the issue is, in one sentence. State the fact you observed.', required: true)]
    #[WordsCount(max: 30)]
    public string $description;

    #[SchemaProperty(description: 'The concrete action to take. Start with a verb.', required: true)]
    #[WordsCount(max: 25)]
    public string $recommendation;

    #[SchemaProperty(description: 'The file or package this concerns, if applicable.', required: false)]
    public ?string $subject = null;
}
```

```php
class AuditReport
{
    #[SchemaProperty(description: 'Overall health score from 0 to 100.', required: true)]
    #[GreaterThanEqual(reference: 0)]
    #[LowerThanEqual(reference: 100)]
    public int $score;

    #[SchemaProperty(description: 'Two-sentence summary of the repository state.', required: true)]
    #[WordsCount(min: 15, max: 60)]
    public string $summary;

    #[SchemaProperty(
        description: 'Every issue found, most severe first.',
        required: true,
        anyOf: [Finding::class]
    )]
    public array $findings;
}
```

`#[WordsCount]` qui fa lavoro vero — senza, il modello scrive paragrafi dove volevi una riga, e l'output del tuo terminale diventa illeggibile.

### Fase 5 — Streaming, gestione degli errori e limiti di esecuzione

- `stream()` con etichette di attività dei tool (Sezione 7.4)
- `toolErrorHandler()` che restituisce istruzioni (Sezione 5.11)
- `toolMaxRuns()` regolato per tool: manifesto 1, file system 15, git 3
- Gestisci SIGINT con garbo — questo è un tool CLI, quindi `connection_aborted()` non si applica, ma un utente che preme Ctrl-C merita comunque un'uscita pulita

### Fase 6 — Trace, eval e impacchettamento

- Abilita Inspector, leggi un trace vero, regola le descrizioni dei tool in base a ciò che vedi
- Una piccola suite di eval: cinque repository con problemi noti, con l'asserzione che i risultati li menzionino
- Impacchetta come `bin` di Composer così che si installi globalmente

## Griglia di valutazione

| Criterio | Evidenza |
|---|---|
| Progetto dei tool | Le descrizioni seguono la formula in quattro parti; le descrizioni delle property contengono esempi |
| Sicurezza | Nessun percorso fornito dal modello; argomenti di processo come array; input numerici limitati |
| Disciplina sui token | Ogni tool limita e riduce il proprio output |
| Struttura | Il report è un DTO validato, non prosa sottoposta a parsing |
| Resilienza | Il gestore d'errore restituisce istruzioni; limiti di esecuzione impostati per tool |
| Misurazione | Esiste una suite di eval che produce un punteggio |

## Criteri di accettazione

- Il revisore gira su tre repository di forma genuinamente diversa — un'app Laravel, una libreria, qualcosa di legacy — senza eccezioni.
- Un repository senza `composer.json` produce un messaggio utile, non un crash.
- Un repository senza cronologia git produce un messaggio utile, non un crash.
- Il report viene validato al primo tentativo per almeno due dei tre, e il ritentativo è visibile nel trace quando non accade.
- Eseguire due volte lo stesso repository produce report che differiscono nella formulazione e concordano sui risultati. Se non concordano sui risultati, sono le descrizioni dei tool che vanno lavorate — non il tuo prompt.

Quest'ultimo criterio è quello interessante. È il non determinismo della Sezione 1.5, misurato sul tuo stesso output, ed è la differenza fra uno strumento di cui ti fideresti e un giocattolo.

## Estensioni

1. Aggiungi `parallelToolCalls(true)` — questo è un tool CLI, quindi `pcntl` è disponibile (Sezione 5.13). Misura la differenza di tempo effettivo su un repository grande.
2. Aggiungi un connettore MCP verso un server GitHub per il contesto di issue e pull request (Capitolo 9). Applica la stratificazione della fiducia della Sezione 9.4 prima di farlo.
3. Esegui la verifica su tre provider e pubblica le differenze. Quali risultati compaiono in tutti e tre? Quelli sono quelli su cui puoi fare affidamento.
