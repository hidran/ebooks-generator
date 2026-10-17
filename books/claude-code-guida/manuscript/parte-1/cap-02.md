# Capitolo 2. Dal modello all'agente: tool, loop agentico, permessi e sandbox

::: {.chapter-goals}
[Cosa imparerai]{.callout-title}

Questo capitolo smonta Claude Code per vedere cosa succede tra il prompt che scrivi e il file che cambia sul disco. Alla fine saprai:

- cos'è un tool e chi lo esegue davvero, il modello o l'harness;
- come funziona il loop agentico, provato su un progetto di prova che crei in cinque minuti;
- cosa decidono le modalità di permesso e cosa limita la sandbox;
- come scegliere modello ed effort con `/model` e `/effort`.

[Prerequisiti]{.callout-title}

Claude Code installato (capitolo 1), Python 3 e Git. Per la prova della sandbox serve macOS, Linux o WSL 2.

:::

Nel capitolo 1 hai visto Claude Code creare un file e lanciarlo. Dal capitolo 3 in poi scriverai prompt sempre più ambiziosi, e prima conviene sapere come lavora la macchina che li riceve. Quello che porti a casa è un modello mentale più che un progetto. Plan Mode, CLAUDE.md, le skill, gli agent, gli hook e i server MCP hanno ciascuno un posto preciso nel meccanismo che descrivo in queste pagine, e quando li incontrerai nei capitoli successivi saprai già dove metterli.

## 2.1 Cosa sa fare un modello da solo

Un LLM è un modello che, dato un testo, predice il testo che segue, un token alla volta. Da solo fa una cosa sola: riceve testo e restituisce testo. Non può aprire un file del tuo progetto, non può lanciare un test, non sa che ore sono. Del mondo conosce quello che ha visto in addestramento, fino a una certa data, più quello che gli scrivi nel prompt.

Quando usi una chat e incolli un pezzo di codice, il lavoro di contorno lo fai tu. Scegli cosa incollare, copi la risposta nell'editor, la provi, torni in chat con lo stack trace. Il modello ragiona, ma le mani sono le tue, e la qualità della risposta dipende da quanto bene hai scelto cosa fargli vedere.

Un agente è un LLM a cui diamo le mani. Gli mettiamo a disposizione degli strumenti, lo facciamo lavorare in un ciclo, e lui decide quali strumenti usare, in che ordine e quando ha finito.

![Un LLM in una chat restituisce testo che copi, esegui e verifichi tu; un agente come Claude Code alterna chiamate agli strumenti e risultati finché il lavoro è finito](figures/cap-02/fig-01.png)

## 2.2 Cos'è un tool

Un tool è una funzione che descriviamo al modello con tre informazioni: un nome, una descrizione in linguaggio naturale e uno schema dei parametri che accetta. Questa è la definizione di un tool che legge un file, nel formato che usa l'API di Anthropic:

```json
{
  "name": "read_file",
  "description": "Legge un file del progetto e ne restituisce il contenuto.",
  "input_schema": {
    "type": "object",
    "properties": {
      "path": { "type": "string", "description": "Percorso del file" }
    },
    "required": ["path"]
  }
}
```

Il modello riceve queste definizioni insieme alla tua richiesta. La descrizione conta quanto il codice: è l'unica cosa su cui il modello si basa per capire quando quel tool serve e come chiamarlo.

Il dettaglio da fissare in testa è che il modello non esegue mai niente. Quando decide che gli serve leggere un file, produce un messaggio strutturato che dice, in sostanza, "voglio usare `read_file` con questo percorso":

```json
{
  "type": "tool_use",
  "id": "toolu_01",
  "name": "read_file",
  "input": { "path": "src/report.py" }
}
```

Poi si ferma e aspetta. Il programma che lo ospita legge la richiesta, apre davvero il file e rimanda indietro il risultato, legato alla richiesta tramite l'`id`:

```json
{
  "type": "tool_result",
  "tool_use_id": "toolu_01",
  "content": "import csv\n\n\ndef totale(path): ..."
}
```

A quel punto il modello riprende il ragionamento con il contenuto del file davanti. Può chiedere un'altra chiamata, oppure dare la risposta finale. Ogni chiamata ripete gli stessi passi.

![Una chiamata a un tool, passo per passo: il modello chiede, Claude Code controlla permessi e hook, lo strumento gira, il risultato torna al modello](figures/cap-02/fig-02.png)

::: {.callout .callout-deep-dive}
[Sotto il cofano]{.callout-title}

`read_file` è un esempio semplificato. Il tool vero di Claude Code si chiama `Read` e accetta `file_path` più parametri opzionali per leggere solo una parte del file. Le definizioni di tutti i tool disponibili viaggiano con ogni richiesta al modello e occupano spazio nella finestra di contesto: lo vedi con `/context`, alla voce dedicata ai tool. Per questo i server MCP, che possono aggiungere decine di tool, caricano all'avvio solo i nomi e il resto quando serve. Ne riparliamo nei capitoli 13 e 15.
:::

## 2.3 L'harness, cioè Claude Code

Il programma che sta intorno al modello si chiama **harness**. Claude Code è un harness: gestisce la conversazione, espone i tool, esegue le chiamate, chiede i permessi e applica le regole di sicurezza. Il modello sta altrove (sui server di Anthropic, o del tuo provider cloud) e vede solo testo: il tuo prompt, le definizioni dei tool, i risultati che Claude Code gli rimanda.

Quasi tutto quello che configurerai in questo libro vive nell'harness, non nel modello. Ogni funzionalità interviene in un punto preciso del giro che hai appena visto:

| Funzionalità | Dove interviene | Capitolo |
| --- | --- | --- |
| Plan Mode | Limita il modello a leggere e proporre, senza modificare, finché non approvi il piano | 3 e 4 |
| CLAUDE.md, memoria automatica | Testo caricato nel contesto a inizio sessione | 7 e 15 |
| Custom command, skill | Istruzioni aggiunte al contesto quando servono | 8 e 9 |
| Agent, subagent | Il tool `Agent` apre un secondo loop con un contesto tutto suo | 10 |
| Permessi | Decidono se una chiamata può partire | 11 |
| Hook | Script che l'harness lancia prima o dopo una chiamata, e che possono bloccarla | 12 |
| MCP | Aggiunge tool che parlano con servizi esterni | 13 |
| Plugin | Impacchetta skill, agent, hook e server MCP per installarli in un colpo | 14 |
| `/context`, `/compact`, `/rewind` | Gestiscono quello che il modello vede a ogni giro | 15 |

Quando un capitolo ti dice "questo è un hook che gira su `PreToolUse`", puoi tornare alla figura di prima: è il passo 2, il controllo che Claude Code fa prima di eseguire lo strumento.

## 2.4 Il loop agentico

Un agente non fa una sola chiamata, lavora in un ciclo. Prima raccoglie il contesto: legge i file, cerca nel codice, magari consulta la documentazione. Poi agisce: modifica un file, lancia un comando. Poi verifica: esegue i test, legge l'output. Se qualcosa non va, il risultato della verifica diventa nuovo contesto e il ciclo ricomincia. Si ferma quando ritiene il lavoro completo, oppure quando ha bisogno di te.

![Il loop agentico di Claude Code: raccogliere il contesto, agire, verificare; se il lavoro non è finito i risultati diventano nuovo contesto](figures/cap-02/fig-03.png)

Nessuno dice al modello quali tool usare e in che ordine. Lo decide lui, giro dopo giro, sulla base di quello che ha letto. È comodo, perché non devi scrivere una procedura, ma significa anche che l'agente prende da solo decine di piccole decisioni: quale file aprire, quale test aggiungere, quando considerare finito il lavoro. Il modo per tenerlo in carreggiata è dargli due cose: una richiesta chiara e un criterio di verifica che possa controllare da solo, come "i test passano" o "la build esce con codice 0". Nella Parte VI questa idea diventa un metodo intero, lo Spec Driven Development (capitolo 18), e nel capitolo 20 la ritrovi in `/goal`, che fa continuare Claude finché una condizione verificabile non è soddisfatta.

## 2.5 Il loop dal vivo su un progetto minuscolo

Per vedere il loop serve un progetto abbastanza piccolo da leggerlo in un minuto. Questo è lo stesso laboratorio che uso nel corso video, `cc-advanced-lab`: uno script Python che somma le vendite di un CSV, con un test. Lo riuserai nell'esercizio di fine capitolo e quando parleremo di permessi, hook e MCP.

I comandi funzionano in bash e zsh su macOS, Linux e WSL. Su Windows nativo lanciali da Git Bash, oppure lavora in WSL 2, che ti servirà comunque per la sandbox.

```bash
mkdir -p ~/cc-advanced-lab/{src,data,tests}
cd ~/cc-advanced-lab
git init
printf "data,vendite\n2026-01,120\n2026-02,95\n2026-03,143\n" > data/vendite.csv
printf "import csv\n\n\ndef totale(path):\n    with open(path) as f:\n        return sum(int(r['vendite']) for r in csv.DictReader(f))\n" > src/report.py
printf "from src.report import totale\n\n\ndef test_totale():\n    assert totale('data/vendite.csv') == 358\n" > tests/test_report.py
touch src/__init__.py
printf "[pytest]\npythonpath = .\n" > pytest.ini
printf "SECRET_KEY=non-committare-questo\n" > .env
printf ".env\n.venv/\n" > .gitignore
git add -A && git commit -m "chore: progetto di laboratorio"
```

Il file `.env` con un finto segreto non serve adesso: lo useremo nel capitolo 11 per provare le regole che impediscono a Claude di leggerlo. Il `pytest.ini` fa in modo che `from src.report import totale` funzioni sia con `pytest` sia con `python -m pytest`: senza, il comando `pytest` da solo si ferma con `ModuleNotFoundError: No module named 'src'`.

Manca pytest. Le installazioni recenti di Python su macOS (Homebrew) e su Ubuntu rifiutano `pip install` fuori da un ambiente virtuale, quindi creane uno nel progetto e avvia Claude Code dalla stessa shell, così il Python che trova nel `PATH` è quello giusto:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pytest
pytest -q
claude
```

`pytest -q` deve rispondere `1 passed`. Se Claude Code ti chiede se ti fidi della cartella, rispondi di sì. Ora scrivi il prompt:

```text
trova la funzione che calcola il totale, aggiungi un test e verifica che passi
```

Non hai nominato né il file né lo strumento di test. Claude deve trovare `totale` in `src/report.py`, capire cosa fa, aggiungere un test in `tests/test_report.py` accanto a `test_totale`, lanciare pytest e leggere il risultato. Quando ha finito, premi `Ctrl+O`: si apre la vista dettagliata della conversazione, con ogni singola chiamata ai tool e il suo risultato. Premi di nuovo `Ctrl+O` per chiuderla.

In un giro tipico vedi un `Bash` che cerca la funzione nei file, un `Read` per leggerla, un `Edit` per scrivere il test e un altro `Bash` per lanciare pytest. Su macOS, Linux e WSL Claude Code non offre più tool di ricerca separati e cerca attraverso la shell; su altre installazioni puoi trovare al loro posto `Grep` e `Glob`. Quando ho registrato questa scena per il corso, la vista mostrava solo chiamate `Bash`, "ran 4 shell commands": Claude aveva cercato, letto e perfino scritto il file con comandi di shell. Il primo tentativo, tra l'altro, è fallito con `No module named pytest`, perché il Python nel `PATH` di quella shell non aveva pytest installato. È il motivo per cui qui ti faccio creare il virtualenv prima di avviare Claude. La sequenza esatta di chiamate cambia da un giro all'altro: quello che resta costante è la struttura, contesto, azione, verifica.

Prima di andare avanti guarda il diff con `git diff`. Dovresti trovare solo il test nuovo. Se vuoi ripartire da zero, `git checkout -- .` riporta il progetto allo stato del commit iniziale.

## 2.6 I tool principali di Claude Code

Non serve impararli a memoria, ma conviene riconoscerli quando passano nella vista di `Ctrl+O` e quando li scriverai nelle regole di permesso del capitolo 11. L'elenco dipende dal sistema e dal modello: questo è quello che trovi su macOS, Linux e WSL con i modelli attuali.

| Tool | A cosa serve | Fase del loop |
| --- | --- | --- |
| `Read` | Leggere un file, anche solo una parte | Raccogliere il contesto |
| `WebSearch`, `WebFetch` | Cercare e leggere pagine web | Raccogliere il contesto |
| `Edit`, `Write` | Modificare e creare file | Agire |
| `Bash` (`PowerShell` su Windows) | Cercare nei file, eseguire comandi: test, build, Git | Tutte |
| `Agent` | Delegare un sotto-compito a un subagent con il suo contesto | Tutte |
| Tool MCP | Qualunque servizio esterno collegato: GitHub, database | Tutte |

Su alcune installazioni trovi anche `Grep` e `Glob`, tool dedicati alla ricerca di testo e di file per nome: fanno lo stesso lavoro che altrove passa da `Bash`. Con i modelli meno recenti compaiono anche i tool della task list (`TaskCreate`, `TodoWrite`), con cui Claude pianifica i passi e li spunta. Con i modelli attuali non vengono offerti (la variabile d'ambiente `CLAUDE_CODE_ENABLE_TODO_TOOLS=1` li riattiva), mentre `Ctrl+T` mostra o nasconde la checklist dei task nell'interfaccia. I subagent lanciati con `Agent` girano in background per default: ne parliamo nel capitolo 10. I tool MCP compaiono con un nome composto da prefisso, server e tool, per esempio `mcp__github__create_pull_request`. Li vedrai nel capitolo 13.

## 2.7 LLM e agente a confronto

Mettiamo le due cose una accanto all'altra.

| | LLM in una chat | Agente come Claude Code |
| --- | --- | --- |
| Input | Il testo che gli dai | La tua richiesta più tutto quello che legge da solo |
| Output | Testo | Azioni sul tuo progetto, più un resoconto |
| Contesto | Solo quello che incolli | File, comandi, web, servizi collegati |
| Chi esegue | Tu, con copia e incolla | L'harness, chiamando i tool |
| Verifica | La fai tu | La fa l'agente: test, build, output |
| Durata | Una risposta | Un loop di molti passi |
| Rischio | Una risposta sbagliata | Un'azione sbagliata sul tuo computer |

L'ultima riga è quella che conta di più. Con un LLM in chat, il peggio che può capitare è una risposta sbagliata, che puoi ignorare. Con un agente, il peggio è un'azione sbagliata: un file cancellato, un `git push --force` sul branch sbagliato, un dato mandato dove non doveva andare. Più autonomia dai, più controllo ti serve. Claude Code lo affronta su due livelli, e il primo sono le modalità di permesso.

## 2.8 Le modalità di permesso

Una modalità di permesso è l'impostazione che decide quali azioni Claude può fare senza chiederti conferma. Quella attiva è sempre scritta nella barra di stato sotto il prompt.

Le sessioni interattive nel terminale e in VS Code partono in **auto mode**: per i piani Pro, Max e Team dalla versione 2.1.228 (agosto 2026), per tutti i piani e i provider dalla 2.1.283. In auto mode un secondo modello, il classificatore, esamina le azioni al posto tuo: lascia passare quelle coerenti con la tua richiesta e blocca quelle rischiose, come scaricare ed eseguire script da internet, fare force push, cancellare in modo irreversibile file esistenti, fare il deploy in produzione o mandare dati sensibili all'esterno. La prima volta che una sessione parte in auto mode, Claude Code mostra un avviso. Fa eccezione la modalità non interattiva, `claude -p`, che parte ancora in Manual. Se hai letto la prima edizione di questo libro, o hai visto video registrati prima di questa versione, è il motivo per cui Claude ti chiede conferma molto meno spesso di quanto ti aspetti: la tua configurazione è a posto, è cambiato il default.

Durante la sessione `Shift+Tab` fa girare le modalità in quest'ordine:

| Modalità | Nome nelle impostazioni | Barra di stato | Cosa fa |
| --- | --- | --- | --- |
| Auto | `auto` | `auto mode on` | Il classificatore approva o blocca al posto tuo |
| Manual | `default` (alias `manual`) | `manual mode on` | Chiede conferma per quasi tutto |
| Accept edits | `acceptEdits` | `accept edits on` | Modifica i file senza chiedere, chiede per il resto |
| Plan | `plan` | `plan mode on` | Analizza e propone un piano, senza modificare nulla |

Un altro `Shift+Tab` dopo Plan ti riporta ad auto. Plan Mode la usi già dal capitolo 3, e nel capitolo 4 diventa il modo standard di cominciare un'analisi.

Fuori dal giro ci sono altre due modalità. `dontAsk` lascia passare le letture nella cartella di lavoro, i comandi Bash in sola lettura e i tool che hai preapprovato con una regola, e nega senza domande tutto quello per cui altrimenti ti chiederebbe conferma: serve negli script e in CI. `bypassPermissions`, la stessa cosa del vecchio flag `--dangerously-skip-permissions`, toglie ogni controllo e va usata solo dentro un container o una macchina virtuale isolata.

Puoi scegliere la modalità all'avvio con un flag:

```bash
claude --permission-mode manual
claude --permission-mode plan
```

`manual` è un alias di `default`, il nome tecnico della modalità Manual.

Se preferisci partire sempre in Manual, per esempio mentre segui i primi capitoli e vuoi vedere ogni passo come negli screenshot, aggiungi a `~/.claude/settings.json`:

```json
{
  "permissions": {
    "defaultMode": "default"
  }
}
```

Auto mode riduce le richieste, ma non è una garanzia di sicurezza. Qualche dettaglio da sapere subito. Le azioni bloccate finiscono in `/permissions`, nella scheda Recently denied, da dove puoi riprovarle. I limiti che scrivi in chat, come "non fare push", il classificatore li tiene in conto come indicazioni, non come regole salvate. Dopo tre blocchi consecutivi, o venti in tutta la sessione, auto mode si mette in pausa e torna a chiederti conferma. Se vuoi leggere le regole che segue il classificatore, `claude auto-mode defaults` le stampa. Regole allow, ask e deny, file di impostazioni e loro precedenza sono materia del capitolo 11.

## 2.9 Permessi e sandbox, due livelli di controllo

Claude Code ti protegge con due livelli diversi, e conviene non confonderli.

Il primo livello sono i permessi. Prima che una chiamata parta, Claude Code decide se può partire: in base alle tue regole, alla modalità di permesso scelta, al classificatore se sei in auto mode, oppure chiedendolo a te. Vale per ogni tool, da `Read` a `Bash` ai tool MCP. I permessi rispondono alla domanda "questa azione può essere eseguita?".

Il secondo livello è la **sandbox**. Una volta che un comando di shell è partito, la sandbox limita cosa può raggiungere lui e ogni processo che lancia: quali cartelle può scrivere, quali file può leggere, quali siti può contattare. Lo fa il sistema operativo, non il modello. La sandbox risponde a un'altra domanda: "anche se questo comando fa più di quanto sembra, fin dove può arrivare?".

![Due livelli di controllo: i permessi decidono se una chiamata può partire e valgono per ogni tool; la sandbox limita file e rete dei soli comandi Bash](figures/cap-02/fig-04.png)

Servono entrambi perché una regola di permesso guarda il testo del comando, e un comando può fare cose che dal testo non si capiscono. Prendi una regola come questa, che è ragionevole e che probabilmente scriverai:

```json
{
  "permissions": {
    "allow": ["Bash(python -m pytest *)"]
  }
}
```

La regola approva `python -m pytest tests/`, ed è giusto così. Ma pytest esegue tutti i `conftest.py` che trova, e un `conftest.py` è codice Python qualunque: può leggere `~/.ssh`, scaricare uno script, scrivere fuori dal progetto. Lo stesso vale per una dipendenza compromessa installata da `pip install` o da `npm install`. Il permesso ha detto di sì al comando giusto, e il comando ha fatto altro. La sandbox è la rete di sicurezza che tiene anche quando la decisione sui permessi era sbagliata.

## 2.10 La sandbox in dettaglio

Con la sandbox attiva, i default sono questi:

| Accesso | Default con la sandbox attiva | Si cambia con |
| --- | --- | --- |
| Scrittura | Solo la cartella di lavoro, una cartella temporanea personale e le cartelle che aggiungi. I file di configurazione di Claude Code restano protetti | `filesystem.allowWrite`, `filesystem.denyWrite` |
| Lettura | Quasi tutto il computer, comprese le credenziali come `~/.ssh` | `filesystem.denyRead`, `credentials` |
| Rete | Nessun accesso diretto: tutto passa da un proxy locale che controlla ogni dominio, e la lista dei domini ammessi parte vuota | `network.allowedDomains`, `network.deniedDomains` |
| Variabili d'ambiente | Ereditate da Claude Code | `credentials` |

Due righe meritano un commento. I file di configurazione di Claude Code restano protetti anche dentro la cartella del progetto, così un comando non può scriversi da solo un `.claude/settings.json` più permissivo. La lettura invece è permissiva: per questo conviene negare in modo esplicito le cartelle con le credenziali. Sulla rete, un comando nella sandbox non ha una strada diretta verso internet. Passa da un proxy che gira sulla tua macchina, e la prima volta che serve un dominio nuovo Claude Code ti chiede se ammetterlo.

Il meccanismo dipende dal sistema operativo:

| Sistema | Meccanismo | Note |
| --- | --- | --- |
| macOS | Seatbelt, integrato nel sistema | Nessuna installazione |
| Linux | bubblewrap per il file system, socat per la rete | `sudo apt-get install bubblewrap socat` |
| WSL 2 | Come Linux | Non funziona su WSL 1 |
| Windows nativo | Non supportato | I comandi girano senza sandbox: usa WSL 2 |

Se lavori su Windows, questo è uno dei motivi più concreti per installare Claude Code dentro WSL 2, come suggerito nel capitolo 1.

### La prova

Nel progetto `cc-advanced-lab`, con Claude Code avviato, scrivi `/sandbox` e premi Invio. Si apre un menu: scegli la voce con auto-allow (nella versione su cui ho scritto il capitolo è `Sandbox BashTool, with auto-allow`). Claude Code risponde con `Sandbox enabled with auto-allow for bash commands`. In modalità auto-allow i comandi che girano nella sandbox partono senza chiederti conferma, perché il confine lo garantisce il sistema operativo.

Ora chiedi a Claude di lanciare due comandi, uno per prompt:

```text
esegui nel terminale questo comando: touch ~/sandbox-probe
```

```text
esegui nel terminale questo comando: curl --noproxy '*' https://example.com
```

Il primo prova a scrivere nella tua home, fuori dal progetto, e fallisce con `Operation not permitted` su macOS o `Read-only file system` su Linux. Il secondo prova a uscire su internet aggirando il proxy, e fallisce con `Could not resolve host`.

A questo punto Claude potrebbe proporti di riprovare il comando fuori dalla sandbox. In Manual vedi una richiesta di conferma: rifiuta. In auto mode, quando ho registrato la lezione, Claude ha riprovato il `touch` fuori dalla sandbox di sua iniziativa, e il classificatore l'ha bloccato con il banner `bash denied by auto mode`. I due livelli hanno lavorato uno dopo l'altro, proprio come nella figura. Alla fine controlla:

```bash
ls ~/sandbox-probe
```

Deve rispondere che il file non esiste.

Il menu di `/sandbox` salva la scelta in `.claude/settings.local.json` del progetto, il file delle impostazioni locali che non va in Git. Se vuoi la sandbox attiva in tutti i tuoi progetti, con qualche regola in più, la configurazione equivalente va in `~/.claude/settings.json`:

```json
{
  "sandbox": {
    "enabled": true,
    "allowUnsandboxedCommands": false,
    "filesystem": {
      "denyRead": ["~/.ssh", "~/.aws"]
    },
    "network": {
      "allowedDomains": ["github.com", "*.npmjs.org", "pypi.org"]
    }
  }
}
```

`allowUnsandboxedCommands` a `false` chiude la via di fuga che hai appena visto: se un comando fallisce nella sandbox, Claude non può chiedere di riprovarlo fuori. `denyRead` toglie ai comandi di shell la lettura delle chiavi SSH e delle credenziali AWS. `allowedDomains` ammette in partenza i domini che usi tutti i giorni, così non ti vengono chiesti uno per uno.

::: {.callout .callout-warning}
[Attenzione]{.callout-title}

La sandbox copre solo i comandi di shell e i processi che lanciano. `Read` ed `Edit` seguono le regole di permesso, non la sandbox. Hook e server MCP girano fuori dalla sandbox con i tuoi permessi di utente. Lo stesso vale per i comandi esclusi: alcuni strumenti, come `docker`, non funzionano dentro la sandbox, e puoi elencarli in `sandbox.excludedCommands` (per esempio `"docker compose *"`), sapendo che da quel momento hanno accesso a tutto quello che puoi fare tu.
:::

### Sandbox, container e macchina virtuale

Se vuoi un confine intorno a tutto Claude Code, hook e server MCP compresi, la sandbox non basta: serve isolare l'intero processo.

| Soluzione | Cosa isola | Quando usarla |
| --- | --- | --- |
| Sandbox di Claude Code | I comandi di shell e i processi che lanciano | Il lavoro di tutti i giorni sul tuo computer |
| Dev container | Tutto Claude Code, dentro un container con un firewall | Progetti che non conosci, ambienti riproducibili per il team |
| Container o VM dedicati | Tutto, compresi hook e server MCP | Esecuzioni autonome senza supervisione, CI |

`bypassPermissions` ha senso solo nella terza riga. Sul tuo portatile, con le tue chiavi SSH e il tuo browser loggato, la combinazione ragionevole è auto mode o Manual con la sandbox attiva.

## 2.11 Modello ed effort

L'ultimo pezzo del modello mentale riguarda il cervello del loop. Due impostazioni decidono quale modello ragiona e quanto.

`/model` mostra i modelli disponibili per il tuo piano e quello attivo. Mentre scrivo ci sono quattro alias: `opus` (Claude Opus 5.5, il default), `sonnet` (Claude Sonnet 5.5), `haiku` (Claude Haiku 5.5) e `fable` (Fable 5.1, il più capace, mai attivo per default), tutti con una finestra di contesto da un milione di token. I default cambiano spesso, e un nome stampato in un libro invecchia in fretta: controlla sempre con `/model` cosa stai usando davvero.

`/effort` regola quanto Claude ragiona prima di rispondere. Si sceglie con un selettore tra `low`, `medium`, `high`, `xhigh` e `max`; sui modelli 5.5 il default è `medium`, e `max` vale solo per la sessione in corso. Più alto significa risposte più accurate sui problemi difficili, ma anche più lente e con più consumo del piano, e in un loop agentico il costo si moltiplica per ogni giro. Una regola pratica:

| Lavoro | Effort |
| --- | --- |
| Domande rapide, piccole modifiche, rinominare una variabile | `low` o `medium` |
| Progettazione, bug difficili, specifiche SDD | `high` |
| Un singolo prompt difficile in una sessione normale | `ultrathink` nel messaggio |

Scrivere `ultrathink` dentro un prompt alza il ragionamento solo per quel messaggio, senza toccare l'impostazione. Frasi come "think hard" o "pensaci bene" non sono parole chiave: il modello le legge come testo qualunque. Il livello attivo compare nel logo e nello spinner mentre Claude lavora.

Nel resto del libro non ti dirò di cambiare effort a ogni capitolo. Quando conta, per esempio nella scrittura delle specifiche della Photogallery (capitolo 18), lo trovi indicato.

## Riepilogo {.unlisted}

- Un LLM riceve testo e restituisce testo; un agente è un LLM che lavora in un loop, usando tool per raccogliere contesto, agire e verificare.
- Il modello non esegue mai niente: produce un `tool_use`, e l'harness, cioè Claude Code, controlla permessi e hook, esegue il tool e rimanda un `tool_result`.
- `Ctrl+O` mostra le singole chiamate: usala quando vuoi controllare cosa ha fatto Claude oltre a quello che ti ha raccontato.
- Le sessioni partono in auto mode; `Shift+Tab` passa a Manual, Accept edits e Plan.
- I permessi decidono se un'azione può partire e valgono per ogni tool; la sandbox, attivata con `/sandbox`, limita file e rete dei comandi di shell, e lo applica il sistema operativo.
- Il modello si sceglie con `/model`, il ragionamento con `/effort`; per un solo prompt difficile basta `ultrathink`.

## Esercizio {.unlisted}

Nel progetto `cc-advanced-lab`, con il virtualenv attivo, avvia Claude Code in Manual:

```bash
claude --permission-mode manual
```

Chiedi:

```text
aggiungi in src/report.py una funzione media(path) che restituisce la media delle vendite, con un test, e verifica che tutti i test passino
```

Approva una richiesta alla volta e, per ciascuna, annota il tool e la fase del loop (contesto, azione, verifica). A lavoro finito apri `Ctrl+O` e confronta la tua lista con le chiamate registrate.

Poi attiva `/sandbox` con auto-allow e chiedi a Claude di lanciare `curl -sI https://pypi.org`. Osserva cosa succede alla prima richiesta verso un dominio non ancora ammesso.

L'esercizio è finito quando `pytest -q` risponde `3 passed`, `git diff` mostra modifiche solo in `src/report.py` e `tests/test_report.py`, e hai una lista ordinata delle chiamate fatte da Claude con la fase di ciascuna.
