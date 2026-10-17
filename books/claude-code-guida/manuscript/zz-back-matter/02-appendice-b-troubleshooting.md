# Appendice B. Troubleshooting

I problemi che ho incontrato scrivendo il libro e registrando il corso, divisi per area. Ogni voce parte da quello che vedi a schermo, spiega da dove viene e dà la correzione; il rimando al capitolo porta al contesto completo. Quando chiedi aiuto a Claude su un errore, incolla l'output esatto: "il deploy non va" produce ipotesi, le dieci righe dell'errore una diagnosi.

## B.1 Prima di tutto: claude doctor e /doctor

```bash
claude --version
claude doctor
```

`claude doctor` gira dalla shell senza aprire una sessione: controlla installazione e file di impostazioni (un `settings.json` con il JSON rotto salta fuori qui) e suggerisce le correzioni, senza modificare niente. Dentro una sessione, `/doctor` (alias `/checkup`) fa un controllo più ampio e può correggere da solo; `/doctor prompt-audit` cerca nelle istruzioni file spariti e regole in conflitto, e propone senza applicare (capitolo 15). Se il controllo è pulito, il pannello giusto di solito ti dice il resto:

| Domanda | Dove guardare |
| --- | --- |
| Con quale account e quale metodo di autenticazione sto lavorando? | `/status` |
| Perché questo comando passa, o perché è bloccato? | `/permissions` |
| L'hook è registrato? Con quale matcher? | `/hooks` |
| Il server MCP è connesso? | `/mcp`, `claude mcp list` |
| Quali file di istruzioni sono stati caricati? | `/memory` |
| Cosa occupa il contesto? | `/context` |
| Cosa consuma i limiti del piano? | `/usage` |
| Il plugin è installato? La skill c'è? | `/plugin`, `/skills` |
| Cosa sta girando in background? | `/tasks`, `claude agents` |

## B.2 Installazione e aggiornamenti

### `claude: command not found` subito dopo l'installazione

Quasi sempre basta aprire un terminale nuovo, così la shell rilegge il `PATH`. Altrimenti la cartella del binario, `~/.local/bin` su macOS e Linux, non è nel `PATH`:

<!-- VERIFY: percorso del binario nativo su macOS/Linux (~/.local/bin); non è in FACTS.md, stesso VERIFY del capitolo 1. -->

```bash
echo $PATH | tr ':' '\n' | grep local
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
```

Con bash usa `~/.bashrc`, poi riapri il terminale (capitolo 1).

### Il `claude` che parte non è quello che hai installato

Hai installato prima con npm e poi con l'installer nativo: vince il primo binario nel `PATH`, e `which -a claude` li elenca. Togli la copia npm:

```bash
npm uninstall -g @anthropic-ai/claude-code
```

### `EACCES: permission denied` con npm, o file di root in `~/.claude`

npm prova a scrivere in una cartella di sistema: usa l'installer nativo, che non chiede diritti di amministratore. Se una vecchia installazione con `sudo` ha lasciato in `~/.claude` file di root, riprendili:

```bash
sudo chown -R "$(whoami)" ~/.claude
```

::: {.callout .callout-warning}
[Attenzione]{.callout-title}

Non usare mai `sudo npm install -g`: crea file di root che bloccano gli aggiornamenti successivi.
:::

### `EBADENGINE` durante `npm install -g`, oppure npm non aggiorna

Il pacchetto richiede Node.js 22 o successivo, e con un Node più vecchio npm avvisa e prosegue: controlla `node --version`. Per aggiornare usa `npm install -g @anthropic-ai/claude-code@latest`, non `npm update -g`.

### Windows: `The token '&&' is not a valid statement separator` o `'irm' is not recognized`

Shell sbagliata: il primo errore è PowerShell con il comando per CMD, il secondo il contrario. In PowerShell il comando è `irm https://claude.ai/install.ps1 | iex`.

### Windows: gli script `.sh` non partono o Claude non trova Git Bash

Senza Git for Windows Claude Code usa PowerShell, dove uno script `.sh` non gira. Installalo; se Git Bash non viene trovato, indica il percorso in `%USERPROFILE%\.claude\settings.json`:

```json
{
  "env": {
    "CLAUDE_CODE_GIT_BASH_PATH": "C:\\Program Files\\Git\\bin\\bash.exe"
  }
}
```

### La versione è vecchia, o l'ultima ha una regressione

L'installer nativo si aggiorna da solo al riavvio successivo; `claude update` aggiorna subito. Homebrew e WinGet vanno aggiornati a mano (`brew upgrade claude-code`, `winget upgrade Anthropic.ClaudeCode`). Se una regressione ti costa cara, scegli il canale `stable` da `/config`: arriva circa una settimana dopo e salta le release con problemi gravi.

## B.3 Autenticazione e account

### Paghi a consumo anche se hai un abbonamento

Nella shell c'è `ANTHROPIC_API_KEY`, magari esportata nel `.zshrc` per un altro progetto, e l'hai approvata al primo avvio: la chiave vince sull'abbonamento, e in `claude -p` viene usata sempre. `/status` mostra il metodo attivo. Togli la variabile e riavvia:

```bash
unset ANTHROPIC_API_KEY
claude
```

### Il login non parte, o sei sull'account sbagliato

Se il browser non si apre, copia l'URL dal terminale, completa il login a mano e incolla il codice. Per cambiare account, `/logout` e poi `/login`; dalla shell `claude auth status` dice con chi sei collegato. Il piano gratuito di claude.ai non include Claude Code (capitolo 1). Per la CI, `claude setup-token` genera un token da mettere nei segreti della pipeline.

### Errori di connessione con la VPN o il proxy aziendale

Prova la rete fuori da Claude Code:

```bash
curl -I https://api.anthropic.com
```

Se fallisce anche questo, il problema è VPN, firewall o un proxy che intercetta TLS: imposta il proxy prima di avviare Claude Code. Se invece la rete va, guarda `status.anthropic.com`.

```bash
export HTTPS_PROXY=http://proxy.azienda.it:8080
claude
```

<!-- VERIFY: supporto di HTTPS_PROXY/HTTP_PROXY/NO_PROXY e dei certificati di un proxy aziendale nella versione corrente (non è in FACTS.md). -->

## B.4 Permessi e auto mode

### Claude non chiede quasi mai conferma

La configurazione è a posto: dalla 2.1.283 le sessioni interattive partono in auto mode, e il classificatore approva al posto tuo. Per vedere ogni passo usa `claude --permission-mode manual`, o `"defaultMode": "default"` sotto `permissions` in `~/.claude/settings.json` (capitolo 2). Su alcuni setup Windows `Shift+Tab` non cambia modalità: prova `Alt+M`.

### `"defaultMode": "auto"` nel file di progetto non ha effetto

È voluto: come `defaultMode`, `auto` e `bypassPermissions` valgono solo in `~/.claude/settings.json`, altrimenti un repository clonato potrebbe togliersi i controlli da solo (capitolo 11).

### Una regola deny non ferma il comando che credevi di aver bloccato

Una regola su `Bash` confronta il testo: `Bash(curl *)` blocca `curl https://...`, non `wget` né uno script Python che scarica. Conta anche lo spazio prima dell'asterisco: `Bash(ls *)` non colpisce `lsof`. In `/permissions` selezioni la regola e vedi da quale file arriva; le regole si sommano e l'ordine è deny, ask, allow. Per un confine vero servono la sandbox o un hook (capitoli 11 e 12).

### Auto mode fa cose che non ti aspetti

Recently denied è vuota anche se Claude è stato bloccato: raccoglie solo le decisioni del classificatore, e una tua regola deny viene valutata prima. Auto mode torna a chiedere conferma a metà lavoro: dopo tre blocchi consecutivi, o venti nella sessione, si mette in pausa, e di solito vuol dire che Claude ha frainteso il compito. Una regola allow su `python` sparisce da `/permissions`: auto mode accantona le allow troppo larghe sugli interpreti, che scavalcherebbero il classificatore; in Manual torna attiva.

### Dopo un blocco Claude ti propone `! cat .env`

Il prefisso `!` esegue il comando a nome tuo, e le regole deny limitano Claude, non te. L'output poi entra nella conversazione, segreto compreso. Se la regola è sbagliata cambiala; se è giusta, rifiuta.

## B.5 Sandbox

### `/sandbox` non isola niente, o non è disponibile

La sandbox funziona su macOS, Linux e WSL 2. Su Windows nativo e su WSL 1 non è supportata, e i comandi girano senza confine anche con `"enabled": true`. Su Linux e WSL 2 servono due pacchetti:

```bash
sudo apt-get install bubblewrap socat
```

### `Operation not permitted`, `Read-only file system` o `Could not resolve host`

È la sandbox che lavora: il comando ha provato a scrivere fuori dalla cartella o a uscire senza il proxy. Se la scrittura serve, aggiungi la cartella a `filesystem.allowWrite`; un dominio usato spesso va in `network.allowedDomains`. Se Claude propone di riprovare fuori dalla sandbox e non vuoi nemmeno la domanda, imposta `"allowUnsandboxedCommands": false` (capitoli 2 e 11).

### pytest si ferma con un `PermissionError` su `.env`

Con la sandbox attiva le deny su `Read`, come `Read(./.env)`, valgono anche per i processi lanciati: pytest che percorre la cartella sbatte contro il file. Nel laboratorio l'ha risolto il `pytest.ini` della sezione 11.1, senza togliere la regola.

### `docker` non funziona dentro la sandbox

Puoi escluderlo dalla sandbox, sapendo che da quel momento ha tutti i tuoi permessi. Per isolare tutto Claude Code, hook e server MCP compresi, serve un dev container o una VM (capitolo 2).

<!-- VERIFY: nome della chiave per i comandi esclusi dalla sandbox (stesso VERIFY dei capitoli 2 e 11). -->

## B.6 Hook

La tabella del capitolo 12, con qualche riga in più:

| Sintomo | Causa e soluzione |
| --- | --- |
| L'hook non parte | Controlla evento e matcher con `/hooks`: il matcher è sensibile alle maiuscole, `"edit"` non corrisponde a niente. Gli hook si leggono all'avvio: riavvia Claude Code dopo ogni modifica al `settings.json` |
| Lo script non parte | Manca il permesso di esecuzione: `chmod +x .claude/hooks/nome.sh` |
| `jq: command not found` | Installa `jq` (`brew install jq`, `sudo apt-get install jq`) o riscrivi lo script in Python |
| Il JSON stampato dall'hook viene ignorato | Un `echo` nel profilo della shell sporca lo stdout: spostalo dentro `if [[ $- == *i* ]]` |
| Claude non si ferma mai | Lo Stop hook non controlla `stop_hook_active` |
| Lo Stop hook non blocca con una suite lunga | L'hook è andato in timeout, e un hook interrotto non blocca: alza `timeout` (in secondi) |
| Il `PostToolUse` non impedisce la modifica | Non può: il tool ha già agito. Per bloccare usa `PreToolUse` |
| Su Windows lo script `.sh` non gira | Claude Code sta usando PowerShell: installa Git for Windows o imposta `CLAUDE_CODE_GIT_BASH_PATH` |

Prima della configurazione, prova lo script a mano con un JSON di esempio: se fallisce qui, il `settings.json` non c'entra. `CLAUDE_PROJECT_DIR` in un test manuale la passi tu:

```bash
echo '{"tool_input":{"file_path":"data/vendite.csv"}}' | .claude/hooks/protect-files.sh; echo "exit: $?"
echo '{"stop_hook_active": false}' | CLAUDE_PROJECT_DIR="$PWD" .claude/hooks/tests-before-stop.sh
```

### L'hook di protezione c'è, ma il file è cambiato lo stesso

Un matcher `Edit|Write` vede solo quei due tool. Un `echo ... >> data/vendite.csv` da `Bash`, o un `UPDATE` attraverso un server MCP, passano altrove. Per i file aggiungi `filesystem.denyWrite` nella sandbox; per un database, un utente in sola lettura o un hook con matcher `mcp__db__.*` (capitoli 12 e 13).

## B.7 MCP

### Il server appena aggiunto risulta in errore

`claude mcp add` salva senza verificare: un token sbagliato o scaduto fallisce solo alla connessione, quindi il primo sospettato è la credenziale. Controlla con `claude mcp list` e `/mcp`, da cui puoi riconnettere. Un server OAuth "da autenticare" vuole il login, da `/mcp` o con `claude mcp login <nome>`. Attento a `claude mcp get`: stampa il token in chiaro.

### DBHub: `unable to open database file`

Il DSN SQLite vuole un percorso assoluto; con DBHub 1.5.0 funziona la forma con due barre:

```bash
claude mcp add --transport stdio db -- npx -y @bytebase/dbhub \
  --dsn "sqlite://$(pwd)/data/vendite.db"
```

<!-- VERIFY: forma del DSN SQLite sulla versione corrente di DBHub (stesso VERIFY del capitolo 13). -->

Su Windows nativo un server avviato con `npx` vuole l'involucro `cmd /c`: `... -- cmd /c npx -y @bytebase/dbhub ...`.

### Il server di `.mcp.json` non compare

I server di progetto vanno approvati al primo avvio. Se hai risposto di no in fretta, azzera le scelte e riavvia:

```bash
claude mcp reset-project-choices
```

Se Claude Code non riesce a leggere la configurazione, in `.mcp.json` c'è un `${VAR}` senza valore né default. Se l'header arriva vuoto con la variabile impostata, è una di quelle che non vengono mai espanse verso un server remoto (le credenziali di Claude Code e dei cloud provider): usa un nome dedicato, come `GITHUB_MCP_PAT` (capitolo 13).

### Claude usa `sqlite3` da `Bash` invece del server

Se il prompt non lo dice, Claude sceglie la strada che preferisce: scrivi "usando il server db".

### In `/mcp` compaiono Gmail o Drive che non hai aggiunto

Sono i connettori del tuo account claude.ai. Dove non li vuoi, avvia con `ENABLE_CLAUDEAI_MCP_SERVERS=false claude`.

## B.8 Plugin, skill e agent

### Il plugin si carica ma non ha skill né agent

I componenti sono finiti dentro `.claude-plugin/`. Lì va solo `plugin.json`: `skills/`, `agents/` e `hooks/` stanno nella radice del plugin, accanto. Poi rilancia `claude plugin validate ./nome-plugin` (capitolo 14).

### Le modifiche al plugin non si vedono, o l'hook del plugin non trova lo script

A sessione aperta usa `/reload-plugins`; un subagent già lanciato tiene il prompt vecchio, quindi rilancialo. Negli hook di un plugin il percorso parte da `"${CLAUDE_PLUGIN_ROOT}"`, non da `$CLAUDE_PROJECT_DIR` né da un percorso assoluto. Se il formatter gira due volte dopo ogni modifica, hai lasciato l'hook anche nel `settings.json` del progetto.

### I colleghi non ricevono l'aggiornamento del plugin

Hai cambiato i file ma non `version` in `plugin.json`: per gli altri non è cambiato niente. Fai il bump nello stesso commit. Per prendere subito la versione nuova:

```bash
claude plugin marketplace update cc-corso
claude plugin update cc-lab-toolkit@cc-corso
```

### `claude plugin eval` non parte, o il delta è zero

Serve Git 2.31 o successivo (`git --version`). Aggiungi `--no-publish` se non vuoi il report su claude.ai, e `evals/results/` al `.gitignore`. Un `Δ` vicino a zero di solito vuol dire che la skill non è stata attivata: il problema è la description.

### La skill non scatta quando te lo aspetti

Claude sceglie la skill dalla description, che quindi va scritta come un trigger: quando usarla, con le parole che userebbe chi la chiede. Una description come "Skill per analisi dati" non scatta quasi mai. Dopo averla allargata, verifica con un caso negativo che non scatti anche dove non deve (capitoli 9 e 14).

### La skill o il custom command non compare nel menu

Controlla il percorso (`.claude/skills/<nome>/SKILL.md`, oppure `.claude/commands/<nome>.md`), il nome esatto `SKILL.md` e il frontmatter YAML: un errore di sintassi può silenziare la skill. Poi `/reload-skills` e `/skills`. Se una skill e un comando hanno lo stesso nome vince la skill, e le skill dei plugin hanno il prefisso, come `/superpowers:<nome>`. Dopo aver installato un plugin come Superpowers serve `/reload-plugins` perché la sessione corrente lo veda.

### `/agents` non apre più il wizard

Il wizard è stato rimosso a luglio 2026 e il comando stampa solo un promemoria. Crea il subagent chiedendolo a Claude o scrivendo `.claude/agents/<nome>.md` (capitolo 10).

### Il subagent restituisce un muro di testo, o non finisce mai

Nel corpo dell'agent manca una sezione sul formato della risposta: chiedi una struttura e un limite di lunghezza. Per un agent che gira da troppo, `/tasks` mostra cosa sta facendo e `Ctrl+X Ctrl+K` ferma tutti i subagent in background. Di solito il compito era troppo vago: spezzalo in pezzi con un risultato verificabile.

## B.9 Contesto e memoria

### Claude dimentica le decisioni prese all'inizio

Guarda `/context`: probabilmente la voce dei messaggi è diventata la più grossa. Compatta con istruzioni (`/compact tieni le decisioni sul formato e la lista dei file modificati`) o, se il task è cambiato, scrivi lo stato su file e riparti:

```text
scrivi in STATE.md cosa abbiamo fatto, le decisioni prese e cosa resta da fare
```

Poi `/clear` e un prompt che dice di leggere `STATE.md`. Se certe regole devono tornare in contesto dopo ogni compattazione, usa l'hook `SessionStart` con matcher `compact` (capitoli 12 e 15).

### Le risposte rallentano e i limiti del piano finiscono in fretta

`/usage` mostra cosa li consuma, diviso per skill, subagent, plugin e server MCP (`/cost` e `/stats` sono suoi alias). Le cause tipiche sono una sessione che va avanti da ore su argomenti diversi, un effort alto lasciato acceso per lavori banali, troppe sessioni o subagent in parallelo. Un task, una sessione; `low` o `medium` per le modifiche piccole. Su un account Console imposta un limite di spesa nella Console.

### `CLAUDE.md` sembra ignorato

Scrivi `/memory`: mostra i file di istruzioni caricati. Se il tuo non c'è, controlla il nome esatto e la posizione (`./CLAUDE.md` o `./.claude/CLAUDE.md` nella cartella da cui lanci `claude`). Un `AGENTS.md` viene letto solo se manca `CLAUDE.md`. Le regole in `.claude/rules/` si cercano all'avvio, e quelle con `paths:` entrano solo quando Claude tocca un file che corrisponde. Se il file c'è ma le istruzioni non vengono seguite, è lungo o vago: stai sotto le duecento righe e scrivi istruzioni verificabili. `/doctor prompt-audit` trova quelle in conflitto. Per un divieto che deve valere sempre serve una regola o un hook (capitoli 7 e 15).

### La scorciatoia `#` non salva più niente in memoria

È stata rimossa. Chiedi a Claude di aggiungere la riga a `CLAUDE.md`, oppure usa `/memory`.

### La memoria automatica ha annotato una cosa sbagliata

Sono file Markdown in `~/.claude/projects/<progetto>/memory/`: correggili o cancellali a mano. `MEMORY.md` si carica solo fino a duecento righe, quindi un indice troppo lungo perde la coda. Da `/memory` puoi spegnere la memoria automatica, per esempio durante una registrazione.

### `/rewind` non ha annullato tutto

I checkpoint seguono le modifiche fatte con i tool dei file, come `Edit` e `Write`. Quello che ha cambiato un comando `Bash` (un `rm`, una migrazione) e le correzioni di `/code-review --fix` restano. La rete di sicurezza è Git: committa prima di un lavoro grosso.

## B.10 Worktree e sessioni in background

### Nel worktree i test falliscono per una chiave mancante

Un worktree è un checkout pulito: i file ignorati da Git, come `backend/.env` con `APP_KEY`, non ci sono. Elencali in `.worktreeinclude` nella radice, e Claude Code li copia in ogni worktree nuovo. `vendor/` e `node_modules/` invece si reinstallano (capitolo 20).

### Le nuove sessioni non vedono quello che hai mergiato in locale

Per default un worktree parte dal main remoto. Pusha, oppure fai partire i worktree dall'`HEAD` locale con `{"worktree": {"baseRef": "head"}}` in `.claude/settings.json`. Lo stesso vale per un subagent con `isolation: worktree`: se il task da cui dipende non è ancora integrato, non trova i file.

### `git status` mostra `.claude/worktrees/`

Aggiungi `.claude/worktrees/` al `.gitignore` della radice prima di aprire le sessioni.

### Sail in due worktree: porte occupate

I container si contendono le porte 80, 3306 e 6379 e lo stesso nome di progetto Docker Compose. Tieni l'applicazione accesa in un worktree alla volta, oppure cambia `APP_PORT` e `FORWARD_DB_PORT` nel `.env` di uno dei due.

### `/goal` non finisce mai, o finisce troppo presto

Il valutatore vede solo la conversazione. "La pipeline funziona" non è verificabile; "`composer test` esce con codice 0, mostrami le righe Status con grep" sì. Se la condizione era sbagliata, `/goal clear` e riscrivila. Prova il controllo a mano prima: se la suite è già rossa, la sessione passerà il tempo su test che non c'entrano.

### Una sessione in background è ferma

Apri `claude agents`: se è in Needs input aspetta una risposta, spesso un installer interattivo o un permesso che il classificatore non ha lasciato passare. Rispondi dall'anteprima con `Space`. Dalla shell, `claude logs <id>` mostra l'output senza entrare.

### `git worktree remove` o `git branch -d` rifiutano

Il worktree ha modifiche non committate, o il branch non è mergiato. Guarda cosa manca prima di aggiungere `--force`: di solito è un commit che non è arrivato in `main`.

## B.11 Progetti: Python ed Excel

| Sintomo | Causa e soluzione |
| --- | --- |
| `externally-managed-environment` su `pip install` | Python di Homebrew o di una distribuzione recente: crea un virtualenv con `python3 -m venv .venv` e attivalo |
| `No module named pytest` anche dopo l'installazione | Hai avviato `claude` da una shell senza il virtualenv attivo: `source .venv/bin/activate`, poi `claude` |
| `ModuleNotFoundError: No module named 'src'` | Manca il `pytest.ini` con `pythonpath = .` (capitolo 2) |
| In Excel le date non si filtrano e si ordinano a caso | pandas le ha lette come testo: chiedi `parse_dates` (capitolo 5) |
| Il totale non cambia quando correggi la sheet Dati | Le formule sommano il Riepilogo, che contiene valori: servono formule che leggono la sheet Dati (sezione 5.4) |
| Lo script funziona a mano ma non da cron | cron parte dalla home e non carica il profilo: `cd` nella cartella del progetto, Python del virtualenv, variabili da un `.env`, output in un file di log |
| Flask non parte o il browser risponde 403 su macOS | La porta 5000 è del ricevitore AirPlay: spegnilo o usa `app.run(debug=True, port=5001)` |
| La copertina del PDF esce bianca | Lo sfondo va disegnato in `onFirstPage`, non aggiunto alla `story` |
| ReportLab si ferma su `doc.build` | La `story` contiene una lista dentro l'altra: espandi le sezioni con `*` |
| Un CSV enorme riempie il contesto | Fai scrivere a Claude uno script che legge a blocchi (`chunksize`, `usecols`) e porta in chat solo i risultati (capitolo 4) |

## B.12 Progetti: Laravel e React

### Il frontend chiama la porta di Vite invece dell'API

L'URL del backend era scritto nel client axios. Leggilo da una variabile: `VITE_API_BASE_URL=http://localhost/api/v1` in `frontend/.env` e `baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api/v1'` nel client (capitolo 19).

### Errore CORS nel browser

`FRONTEND_URL` nel `.env` del backend punta a `localhost:5173`, ma il dev server di Vite gira su un'altra porta perché la 5173 era occupata. Allinea la variabile, che alimenta `config/cors.php`. Lo scaffold di Laravel 13 non pubblica quel file: senza, la policy di default accetta qualunque origine.

### Un errore dell'API arriva come pagina HTML

Il client non ha mandato `Accept: application/json`. Il middleware `ForceJsonResponse` del Photogallery risolve: va nel gruppo `api`, non in `web`, e con `prepend`, così anche il 401 di `auth:sanctum` esce in JSON.

### `createToken()` fallisce con una violazione NOT NULL

La chiave primaria di `personal_access_tokens` è stata trasformata in UUID. Sanctum si aspetta un auto-increment: riportala a `$table->id()` e cambia solo `tokenable_id`.

### Test verdi su SQLite, errori su MariaDB

SQLite è più permissivo su vincoli e funzioni di data. Lancia i test anche su un database vero con Sail: `vendor/bin/sail up -d`, poi `vendor/bin/sail test`.

### `403 Forbidden` sulle varianti delle foto

Il link `public/storage` è giusto, ma un disco `local` con `'serve' => true` registra una route che intercetta le richieste prima del file statico. Tieni `serve` solo sul disco pubblico delle varianti (capitolo 21).

### Il job fallisce cercando una foto che non esiste

Il dispatch avviene dentro `DB::transaction()` e il worker prende il job prima del commit. Restituisci i job dalla closure e mettili in coda dopo.

### Su S3 le foto escono senza EXIF, o il driver `s3` non parla con MinIO

`Storage::disk(...)->path()` su un disco `s3` restituisce la chiave dell'oggetto, che `exif_read_data` non apre: leggi l'EXIF dal file temporaneo al momento dell'upload. Per MinIO il ramo `s3` di `config/filesystems.php` deve leggere `AWS_ENDPOINT` e `AWS_USE_PATH_STYLE_ENDPOINT`.

### Dietro il load balancer il rate limit blocca tutti insieme

Senza `trustProxies`, `$request->ip()` è l'indirizzo del proxy e il limite per IP diventa un secchio unico. Leggi `TRUSTED_PROXIES` dal `.env`.

## B.13 Progetti: Firebase

### `firebase: command not found`

Installa la CLI con `npm install -g firebase-tools`, oppure usa `npx firebase-tools` al posto di `firebase` in tutti i comandi.

### Il progetto non compare, o il deploy va sul progetto sbagliato

Rifai `firebase login` e controlla con `firebase projects:list`. Il progetto della cartella è in `.firebaserc`: l'ID è quello assegnato da Firebase, a volte con un suffisso.

### Il sito pubblicato è vuoto o è la versione vecchia

`firebase deploy` carica quello che c'è in `dist/`: lancia `npm run build` prima, e controlla che `public` in `firebase.json` sia `dist` (`out/` se passi a Next.js con export statico). Se `firebase init` ti ha sovrascritto `dist/index.html`, rifai la build.

### Ricaricando una pagina interna arriva un 404

Manca la riscrittura su `index.html`: rispondi sì a "Single-page app" in `firebase init hosting`, o aggiungi a `firebase.json` `"rewrites": [{ "source": "**", "destination": "/index.html" }]`.

### Il dominio personalizzato non risponde, o il deploy ha rotto qualcosa

La propagazione DNS può richiedere fino a un giorno; intanto il sito resta su `.web.app`. Per tornare a un rilascio precedente usa la cronologia nella console di Hosting.

## B.14 Progetti: AWS

### Lo stack finisce in `ROLLBACK_COMPLETE`

Gli eventi dicono quale risorsa ha fallito e perché, nel campo `ResourceStatusReason`:

```bash
aws cloudformation describe-stack-events \
  --stack-name photogallery-staging \
  --query "StackEvents[?ResourceStatus=='CREATE_FAILED' || ResourceStatus=='UPDATE_FAILED']" \
  --output table
```

Le cause più frequenti sono permessi IAM mancanti, limiti dell'account (VPC, Elastic IP, ALB, da alzare in Service Quotas), un nome già usato (i bucket S3 sono unici in tutto AWS) e una dipendenza non dichiarata, da risolvere con `DependsOn`. Con `InsufficientCapabilities` manca solo `--capabilities CAPABILITY_NAMED_IAM`. Uno stack in `ROLLBACK_COMPLETE` non si aggiorna: cancellalo con `aws cloudformation delete-stack` e riprova (capitolo 23).

### Il task ECS non parte o si riavvia in loop

Il motivo e l'exit code li vedi tra i task fermati, nella console ECS o con `aws ecs describe-tasks`.

| Sintomo | Causa e soluzione |
| --- | --- |
| Exit code 1 al boot, `FATAL: missing required env var` nei log | Manca una variabile nella task definition |
| Exit code 137 | Memoria finita, tipico del worker con foto grandi: alza `Memory` |
| `CannotPullContainerError` | La execution role non ha `ecr:GetAuthorizationToken` ed `ecr:BatchGetImage`, le subnet private non passano dal NAT, o il tag non esiste su ECR |
| `exec format error` | Immagine ARM costruita su un Mac Apple Silicon: `docker build --platform linux/amd64` |
| Il task parte e l'ALB lo dichiara non sano | `/api/v1/health` risponde 503: `"storage": "error"` indica il bucket, `"queue": "error"` il database |

### La connessione al database va in timeout

Il security group di RDS non accetta il traffico dei task. L'ingresso sulla 3306 deve avere `SourceSecurityGroupId` uguale al security group dei task ECS.

### CloudFront risponde 502 o 504 su `/api/v1`

Interroga l'ALB direttamente con `curl -v "https://<ALBDnsName>/api/v1/health"`. Se lì funziona, il problema è il behavior `/api/*` di CloudFront: origine, protocollo, e l'header `Authorization`, che deve arrivare a Laravel perché Sanctum veda il token. Se anche l'ALB dà 5xx, guarda i log CloudWatch del container.

### Le route della SPA danno 404, o mancano gli asset dopo un deploy

Per le route servono le `CustomErrorResponses` che rispondono con `index.html` e stato 200 agli errori 403 e 404 del bucket. Gli asset mancanti vengono quasi sempre da un `aws s3 sync --delete` lanciato anche su `assets/`: ricarica la build precedente e segui l'ordine della sezione 23.4, asset prima e `index.html` dopo, poi invalida `/index.html`.

### Il change set dice `Replacement: True` sull'istanza RDS

Fermati. Applicarlo vuol dire cancellare il database e crearne uno nuovo, e senza snapshot perdi i dati. Di solito basta un nome di istanza cambiato nel template per arrivarci.

## Se il tuo problema non è qui

Apri una issue nel repository `claude-code-book-snippets` con la versione di Claude Code (`claude --version`), il sistema operativo, il comando che hai lanciato e l'output completo dell'errore. Le segnalazioni verificate entrano nella revisione successiva e nel changelog dell'Appendice E.
