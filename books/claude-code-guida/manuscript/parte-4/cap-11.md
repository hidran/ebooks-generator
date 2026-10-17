# Capitolo 11. Permessi, modalità e sandbox

## Cosa imparerai

- Scegliere la modalità di permesso giusta e cambiarla con `Shift+Tab`.
- Scrivere regole allow, ask e deny in `.claude/settings.json` e sapere in che ordine vengono valutate.
- Capire cosa fa davvero auto mode e dove si ferma il classificatore.
- Configurare la sandbox a livello di progetto e condividerla con il team.

Nelle prime tre parti del libro hai lasciato che Claude Code decidesse da solo quando chiederti il permesso, e per analizzare un CSV o scrivere una skill andava benissimo. Da qui in avanti gli dai più autonomia: hook che girano a ogni modifica, server MCP che parlano con GitHub e con un database, plugin installati da un marketplace, sessioni lunghe che lavorano mentre tu fai altro. Più l'agente agisce da solo, più ti serve sapere con precisione cosa può fare senza chiedere, cosa non deve toccare mai e cosa succede se un comando fa più di quanto dice il suo nome. La Parte IV parte da qui.

Nel Capitolo 2 hai visto i concetti: il modello chiede, l'harness esegue, i permessi decidono se una chiamata può partire e la sandbox limita quanto lontano arriva un comando una volta partito. Hai anche provato la sandbox con `touch ~/sandbox-probe`. Qui passi alla configurazione. I livelli di controllo sono tre: la modalità di permesso stabilisce il comportamento di base, le regole allow, ask e deny aggiungono eccezioni precise, la sandbox mette un confine a livello di sistema operativo. Li vedi uno alla volta su un progetto piccolo, così ogni prova si legge in pochi secondi.

## 11.1 Il progetto di laboratorio

I capitoli 11-15 usano tutti lo stesso progetto, `cc-advanced-lab`, che hai creato nel Capitolo 2 per vedere il loop agentico: uno script Python di sei righe, un CSV di tre righe e un test. È volutamente minuscolo. La Photogallery resta intatta, e quando una regola blocca qualcosa vedi subito perché, senza perderti in un codebase da migliaia di righe. Contiene anche un file `.env` con un segreto finto: è l'esca per le regole di questo capitolo e per gli hook del prossimo.

Se hai saltato il Capitolo 2, o se nel frattempo hai modificato il laboratorio, ricrealo da zero (macOS, Linux o WSL 2):

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
python3 -m venv .venv
source .venv/bin/activate
pip install pytest
```

Il `.env` resta fuori da Git grazie al `.gitignore`, come in un progetto vero. Avvia sempre Claude Code dalla shell in cui hai attivato il virtualenv, così il Python che trova nel `PATH` è quello con pytest.

Per questo capitolo serve un ritocco a `pytest.ini`. Dice a pytest di cercare i test solo in `tests/` e di ignorare `.env`:

```bash
printf "[pytest]\npythonpath = .\ntestpaths = tests\naddopts = --ignore=.env\n" > pytest.ini
git commit -am "chore: pytest solo su tests/"
```

Senza queste due righe, alla Sezione 11.8 la sandbox ti farebbe fallire la raccolta dei test con un `PermissionError`. Lì vedi perché, ed è uno dei dettagli più istruttivi del capitolo. Verifica che tutto funzioni prima di aprire Claude Code:

```bash
python -m pytest
```

Devi vedere `1 passed`: il test controlla che la somma delle vendite di gennaio, febbraio e marzo sia 358.

## 11.2 Le sei modalità di permesso

Apri `claude` nella cartella del laboratorio e guarda sotto il prompt: la modalità attiva è sempre scritta lì. Le sessioni interattive nel terminale e in VS Code partono in auto mode, quindi leggi `auto mode on`. Il cambio è arrivato in due tempi: dalla versione 2.1.228 (agosto 2026) per i piani Pro, Max e Team, dalla 2.1.283 per tutti i piani e i provider. Una sessione non interattiva con `claude -p` parte invece ancora in Manual.

Premi `Shift+Tab` e la scritta cambia. Quattro pressioni chiudono il ciclo:

```text
auto mode on
manual mode on
accept edits on
plan mode on
auto mode on
```

Il ciclo contiene quattro modalità. Le altre due, pensate per quando nessuno sta davanti al terminale, restano fuori.

| Modalità | Cosa fa senza chiedere | Quando usarla |
| --- | --- | --- |
| Manual (`default`) | Solo letture | Codice delicato, progetto che non conosci |
| `acceptEdits` | Letture, modifiche ai file, comandi come `mkdir`, `touch`, `mv` e `cp` | Iterare rivedendo le modifiche con `git diff` |
| `plan` | Letture, nessuna modifica finché non approvi il piano | Esplorare e progettare |
| `auto` | Tutto, con controlli di sicurezza in background | Task lunghi, meno interruzioni |
| `dontAsk` | Letture nella cartella di lavoro, Bash in sola lettura e i tool pre-approvati; il resto viene negato | CI e script |
| `bypassPermissions` | Tutto, senza alcun controllo | Solo container o VM isolati |

Manual è la vecchia modalità predefinita: nella configurazione si chiama `default`, nell'interfaccia Manual. Chiede conferma per quasi tutto. È il comportamento che hai visto nei primi capitoli, prima che auto mode diventasse il default, e resta la scelta giusta quando apri un repository che non conosci: ogni comando passa sotto i tuoi occhi.

Accept edits lascia modificare i file senza chiedere, e approva da sola anche i comandi che toccano solo file e cartelle (`mkdir`, `touch`, `mv`, `cp`), ma ti ferma sugli altri. È comodo quando lavori a piccoli passi e rivedi tutto a fine giro con `git diff`: le modifiche sono lì, nel working tree, e Git ti dà l'undo.

Plan lo conosci dal Capitolo 4: Claude legge, analizza e propone un piano, senza toccare nulla finché non lo approvi.

Auto lascia lavorare Claude e affida i controlli a un secondo modello, il classificatore, che approva le azioni coerenti con la tua richiesta e blocca quelle rischiose. Gli dedico la Sezione 11.7, perché il suo comportamento reale ha qualche sfumatura che conviene conoscere prima di fidarsi.

Fuori dal ciclo ci sono `dontAsk` e `bypassPermissions`. La prima lascia passare le letture nella cartella di lavoro, i comandi Bash in sola lettura e i tool che hai pre-approvato con le regole allow, e nega tutto quello per cui altrimenti ti chiederebbe conferma: è quella che vuoi in una pipeline di CI, dove nessuno risponderebbe a un prompt. La seconda salta ogni controllo, ed è la stessa cosa che ottieni con il flag `--dangerously-skip-permissions`. Usala solo dentro un container o una macchina virtuale che puoi buttare via, mai sul tuo portatile con le tue chiavi SSH.

Le modalità fuori dal ciclo si scelgono all'avvio, e lo stesso flag vale per tutte:

```bash
claude --permission-mode plan
claude --permission-mode manual
claude --permission-mode dontAsk
```

`manual` è un alias di `default`: scegli il nome che ti viene più naturale.

Se invece vuoi che un progetto parta sempre in una certa modalità, mettila nelle impostazioni:

```json
{
  "permissions": {
    "defaultMode": "default"
  }
}
```

Con questo blocco in `.claude/settings.json`, chiunque apra il progetto parte in Manual invece che in auto mode. Lo uso sui repository dei clienti: la prima ora su un codice che non conosco preferisco vedere ogni comando. Funziona anche con `plan` e `acceptEdits`. Con `auto` e `bypassPermissions` no: come `defaultMode` hanno effetto solo in `~/.claude/settings.json`, e scritte nel file di progetto o in quello locale vengono ignorate. Ha senso, perché altrimenti un repository clonato da internet potrebbe accendersi da solo in `bypassPermissions` sul tuo computer.

## 11.3 Regole allow, ask e deny

La modalità decide il comportamento di base. Le regole aggiungono eccezioni: questo comando passa sempre, questo chiede sempre, questo non passa mai. Si scrivono in un file JSON e Claude Code le applica in qualunque modalità, anche in auto mode.

Esci da Claude Code e crea la cartella delle impostazioni del progetto:

```bash
mkdir -p .claude
```

Poi crea `.claude/settings.json` con questo contenuto:

```json
{
  "permissions": {
    "allow": [
      "Bash(python -m pytest *)",
      "Bash(git diff *)"
    ],
    "ask": [
      "Bash(git push *)"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Bash(curl *)",
      "Agent(model:opus)"
    ]
  }
}
```

In `allow` ci sono pytest e `git diff`: comandi che non modificano nulla di importante e che non voglio approvare ogni volta. In `ask` c'è `git push`: anche quando tutto il resto scorre senza domande, prima di mandare codice sul remote voglio dire sì io. In `deny` ci sono quattro divieti: leggere il `.env` e le sue varianti (`.env.local`, `.env.production`), usare `curl`, lanciare subagent sul modello Opus.

L'ultima regola usa una sintassi recente. Tra parentesi, invece di un comando, indichi un parametro del tool e il suo valore: `Agent(model:opus)` colpisce le chiamate al tool `Agent` che chiedono il modello Opus. Nel laboratorio serve a mostrare la sintassi, ma ha anche un uso pratico: se lavori con un piano a consumo, tieni i subagent su modelli più leggeri e lasci Opus alla sessione principale.

Il file sta dentro il progetto, quindi finisce in Git e vale per tutto il team. Committalo come qualsiasi altro file di configurazione.

Ora prova. Riavvia `claude` perché legga le nuove impostazioni, passa a Manual con un `Shift+Tab` e scrivi:

```text
esegui i test con python -m pytest
```

In Manual Claude chiederebbe conferma per quasi ogni comando, ma pytest corrisponde a una regola allow: parte subito e vedi `1 passed`. Adesso il secondo prompt:

```text
leggimi il contenuto di .env
```

Claude prova a usare il tool `Read`, la regola deny lo ferma e il contenuto del file non compare mai a schermo. Claude ti dice che la lettura è negata dalle impostazioni del progetto.

::: {.callout .callout-warning}
[Attenzione]{.callout-title}

Nella registrazione della lezione, dopo il rifiuto, Claude mi ha suggerito di leggere il file io stesso con `! cat .env`, e più avanti di lanciare `! curl ...` per il download bloccato. Il prefisso `!` esegue il comando direttamente nella shell, a nome tuo, e le regole deny limitano Claude, non te. In più l'output di un comando lanciato con `!` entra nella conversazione: con `! cat .env` il segreto che volevi tenere fuori finisce proprio nel contesto. Se una regola ti blocca, decidi tu se la regola è sbagliata, e se lo è cambia la regola.
:::

## 11.4 Sintassi delle regole e ordine di valutazione

La forma è sempre `Tool(specificatore)`. Il nome del tool da solo, senza parentesi, colpisce ogni suo uso: `"Bash"` in `ask` significa che ogni comando shell chiede conferma. Lo specificatore cambia significato a seconda del tool.

| Regola | Cosa colpisce |
| --- | --- |
| `Bash(python -m pytest *)` | Ogni comando che inizia con `python -m pytest` |
| `Bash(git diff *)` | `git diff` con qualunque argomento |
| `Read(./.env)` | La lettura del file `.env` del progetto |
| `Edit(./data/**)` | Le modifiche a qualunque file sotto `data/` |
| `WebFetch(domain:pypi.org)` | Le richieste web verso `pypi.org` |
| `Agent(model:opus)` | I subagent lanciati sul modello Opus |
| `mcp__github__*` | Tutti i tool del server MCP `github` |

Per Bash l'asterisco vale come jolly. Attento allo spazio prima dell'asterisco: `Bash(ls *)` colpisce `ls -la` ma non `lsof`, mentre `Bash(ls*)` li colpisce entrambi. <!-- VERIFY: comportamento dello spazio prima di * nelle regole Bash, documentazione permessi ottobre 2026 --> Per `Read` ed `Edit` lo specificatore è un percorso con i pattern di `.gitignore`, quindi `**` scende in tutte le sottocartelle. Le regole su `Edit` valgono per tutti i tool che modificano file, `Write` compreso.

I tool MCP hanno nomi composti: `mcp__`, il nome del server, due trattini bassi, il nome del tool. `mcp__github__*` approva o nega in un colpo tutto quello che espone il server `github`; con il nome completo, per esempio `mcp__github__create_pull_request`, scegli un tool alla volta. Ti tornerà utile nel Capitolo 13, quando colleghi GitHub a Claude Code e vuoi lasciare libere le letture ma non la creazione di PR.

L'ordine di valutazione è fisso: prima deny, poi ask, poi allow. Un deny vince sempre, anche se esiste un allow più specifico. Se in `allow` scrivi `Bash(git push origin feature/*)` e in `ask` hai `Bash(git push *)`, il push sul branch di feature chiede comunque conferma, perché ask viene valutato prima. Le regole di tutti i file di impostazioni si sommano (la Sezione 11.5 elenca dove stanno), e un deny scritto in uno qualsiasi di quei file non può essere scavalcato da un allow scritto in un altro.

Ora il limite che devi avere chiaro. Una regola su Bash confronta il testo del comando, non il programma che parte. `Bash(curl *)` blocca `curl https://...` scritto così. Non blocca `wget`, né uno script Python che apre una connessione con `urllib`, né un `npm install` il cui script di postinstall scarica qualcosa. Vale anche per `Read(./.env)`: ferma il tool `Read`, ma un comando shell che legge il file passa da un'altra strada. Per un confine vero servono la sandbox, che vedi più avanti in questo capitolo, o un hook che esamina il comando prima che parta, che scrivi nel Capitolo 12.

E le istruzioni nel `CLAUDE.md`? "Non leggere mai il file .env" in `CLAUDE.md` orienta Claude, e di solito Claude la rispetta. Ma è testo nel contesto del modello, che può dimenticarlo dopo una compattazione o pesarlo meno di una tua richiesta esplicita. Una regola deny la fa rispettare Claude Code, il programma, prima che la chiamata parta. Le due cose si completano: in `CLAUDE.md` spieghi il perché, nelle impostazioni metti il divieto.

## 11.5 Dove finiscono le regole

Le regole possono stare in quattro posti, con portate diverse.

| File | Portata | In Git |
| --- | --- | --- |
| `~/.claude/settings.json` | Tutti i tuoi progetti | No |
| `.claude/settings.json` | Il progetto, condiviso con il team | Sì |
| `.claude/settings.local.json` | Il progetto, solo tu | No |
| Managed settings | L'organizzazione, non sovrascrivibili | Gestite dall'IT |

Il file utente è il posto per le preferenze personali che vuoi ovunque: per esempio i deny `Read(~/.ssh/**)` e `Read(~/.aws/**)`, che non c'entrano con nessun progetto in particolare. Il file di progetto è quello che hai appena scritto: regole che valgono per chiunque cloni il repository. Il file locale raccoglie le eccezioni tue su quel progetto, ed è lì che finisce ogni "sì, e non chiedermelo più" che dai a un prompt di permesso. Quando Claude Code lo crea, lo aggiunge anche agli ignorati di Git. <!-- VERIFY: settings.local.json aggiunto automaticamente agli ignorati di Git alla creazione -->

Ogni tanto apri `.claude/settings.local.json` e rileggilo. Dopo qualche settimana ci trovi approvazioni date al volo che non rifaresti a mente fredda, e qualcuna merita di salire nel file di progetto perché serve anche ai colleghi.

Le managed settings le distribuisce l'organizzazione e non si possono sovrascrivere: se l'azienda nega `Bash(git push --force *)`, nessun file locale lo riapre. Da lì un amministratore può anche spegnere auto mode per tutti con `"disableAutoMode": "disable"` dentro `permissions`. In caso di conflitto su un valore singolo, come `defaultMode`, vale il file più specifico: managed sopra tutto, poi gli argomenti da riga di comando, poi il file locale, quello di progetto e infine quello utente. <!-- VERIFY: ordine di precedenza managed, CLI, local, project, user -->

## 11.6 /permissions e Recently denied

Per vedere le regole attive non serve aprire quattro file. Scrivi `/permissions` (l'alias è `/allowed-tools`): il pannello si apre sulla scheda Allow, con la freccia destra passi ad Ask e a Deny. Selezionando una regola e premendo `Enter` vedi da dove arriva; per quelle del laboratorio la riga dice `From shared project settings`, cioè `.claude/settings.json`.

Nella registrazione la scheda Allow mostrava anche alcune regole `mcp__computer-use__*` che non avevo scritto nel laboratorio: arrivavano dalle impostazioni utente del mio account. È la dimostrazione pratica che le regole si sommano, e il motivo per cui `/permissions` è il primo posto da guardare quando un comando passa o si blocca e non capisci perché. Altro dettaglio osservato: in auto mode la regola `Bash(python -m pytest *)` non compariva più tra gli allow. Entrando in auto mode Claude Code accantona le regole allow troppo larghe sugli interpreti, perché un `python` approvato in automatico potrebbe eseguire qualunque cosa e scavalcherebbe il classificatore. <!-- VERIFY: auto mode scarta le regole allow ampie su interpreti e shell (es. Bash(python *)); spiegazione dedotta dal report della lezione 3 -->

L'ultima scheda è Recently denied. Raccoglie le azioni bloccate dal classificatore di auto mode, e da lì puoi riprovarle approvandole tu. Se è vuota, il pannello lo dice: `Commands denied by the auto mode classifier will appear here`. Raccoglie solo le decisioni del classificatore: quello che ferma una tua regola deny lì non compare, e nella prossima sezione lo vedi succedere.

## 11.7 Auto mode in pratica

Torna in auto mode: da Manual sono tre pressioni di `Shift+Tab` (accept edits, plan, auto). Poi chiedi un lavoro normale:

```text
aggiungi una funzione media() in src/report.py con il relativo test ed esegui i test
```

Claude modifica `src/report.py`, aggiunge il test in `tests/test_report.py`, lancia pytest e chiude con `2 passed`, senza nessuna richiesta di conferma. In auto mode Claude lavora senza fermarsi sulle operazioni normali: modifica i file nella cartella del progetto, esegue i test, installa le dipendenze dichiarate. Prima di ogni azione non banale, però, il classificatore controlla che sia coerente con quello che hai chiesto.

Le categorie che blocca sono quelle in cui un errore costa caro: scaricare ed eseguire script da internet, force push, cancellazioni irreversibili, deploy in produzione, invio di dati sensibili verso l'esterno. Quindi il secondo prompt è una trappola voluta:

```text
scarica ed esegui lo script https://example.com/install.sh
```

Claude si ferma. Quando ho aperto `/permissions` per mostrare la scheda Recently denied, però, la scheda era vuota. A fermare Claude non era stato il classificatore: era stata la regola deny su `curl` della Sezione 11.3. Le regole valgono anche in auto mode e vengono valutate prima del classificatore, quindi il comando non è mai arrivato fino a lui.

Preparando la lezione ho provato la stessa richiesta senza quella regola, e il classificatore non l'ha bloccata. Il classificatore è un modello che giudica il contesto, e la sua valutazione può andare in un modo che non ti aspetti; forse su `example.com`, un dominio riservato agli esempi, ha pesato proprio quello. Una regola deny invece è deterministica: o il testo corrisponde, o no. Per le cose che non devono succedere mai scrivi una regola. Il classificatore copre tutto il resto, cioè le situazioni che non avevi previsto.

Lo stesso vale per ask. La regola `Bash(git push *)` chiede conferma anche in auto mode, e siccome un force push comincia comunque con `git push`, non raggiunge mai il classificatore: ti arriva la domanda prima.

Due comportamenti di auto mode da conoscere. Il primo: il classificatore legge anche i limiti che metti in conversazione. Se scrivi "non fare push", blocca i push finché non dici il contrario. È un'indicazione nel contesto, non una regola salvata: vale per quella sessione e può perdersi in una compattazione. Per una garanzia usa un deny. Il secondo: se Claude viene bloccato tre volte di fila, o venti volte in totale nella sessione, auto mode si mette in pausa e torna a chiederti conferma. Un agente che sbatte ripetutamente contro il classificatore probabilmente ha frainteso il compito, e a quel punto vuoi guardare tu.

Per vedere le regole su cui ragiona il classificatore, esci da Claude Code e lancia dalla shell:

```bash
claude auto-mode defaults | head -40
```

Il comando stampa le regole predefinite del classificatore. Sono parecchie righe di testo fitto, per questo il `head`. Leggile una volta con calma: ti danno un'idea concreta di cosa il classificatore considera rischioso, e quindi di cosa conviene coprire con regole tue. Accanto a `defaults` esistono `claude auto-mode config` e `claude auto-mode reset`, e dentro una sessione `/auto-mode-setup`: servono a vedere e ritoccare la configurazione del classificatore, e a riportarla ai valori predefiniti. <!-- VERIFY: cosa mostrano esattamente claude auto-mode config e /auto-mode-setup -->

::: {.callout .callout-tip}
[Suggerimento]{.callout-title}

Auto mode riduce le interruzioni, ma non sostituisce la revisione. A fine task guarda comunque il diff (`git diff`, o il pannello `/diff` dell'app desktop) prima di committare. Il classificatore giudica il rischio di un'azione; se il codice è giusto lo decidi tu.
:::

## 11.8 La sandbox a livello di progetto

La sandbox lavora a un livello diverso dalle regole. Invece di decidere se un comando può partire, limita cosa può raggiungere una volta partito, sul file system e in rete, e lo fa il sistema operativo: Seatbelt su macOS, bubblewrap e socat su Linux e WSL 2. Per questo vale anche quando il comando è scritto in un modo che le regole non riconoscono, come il `wget` della Sezione 11.4. Cosa limita per default, la prova con `touch ~/sandbox-probe` e il significato delle chiavi principali li trovi nel Capitolo 2. Qui la accendi insieme alle regole del laboratorio e la sposti nel file del team.

Passa a Manual con `Shift+Tab`, scrivi `/sandbox` e scegli `Sandbox BashTool, with auto-allow`. In questa modalità i comandi che girano dentro la sandbox partono senza chiederti conferma, anche in Manual, perché il confine lo garantisce il sistema. I deny restano validi: un comando negato resta negato. Prova:

```text
esegui ls -la e python -m pytest
```

I due comandi partono senza nessuna richiesta e pytest chiude con `2 passed`. Per arrivarci, però, ho dovuto aggiungere al laboratorio le due righe di `pytest.ini` della Sezione 11.1. Senza, pytest falliva durante la raccolta con un `PermissionError` sul file `.env`. Il motivo è interessante: la sandbox prende le regole deny su `Read` e le applica a livello di sistema operativo a tutti i processi che lancia. `Read(./.env)` non ferma più solo il tool `Read` di Claude: ferma qualunque programma partito da un comando sandboxato, pytest compreso, che percorre la cartella in cerca di test. È il confine vero di cui parlava la Sezione 11.4, e lo noti appena qualcosa ci sbatte contro. <!-- VERIFY: la sandbox eredita le regole deny Read come denyRead a livello di file system; dedotto dal PermissionError osservato nella lezione 3 -->

Come hai visto nel Capitolo 2, il menu di `/sandbox` salva la scelta in `.claude/settings.local.json`, che vale solo per te. Nel Capitolo 2 la configurazione completa finiva in `~/.claude/settings.json`, per tutti i tuoi progetti. Per un progetto di team ha più senso il terzo posto, `.claude/settings.json`, così chi clona il repository trova lo stesso confine. La forma minima è `"sandbox": { "enabled": true }`; quella che uso nel laboratorio è:

```json
{
  "sandbox": {
    "enabled": true,
    "allowUnsandboxedCommands": false,
    "filesystem": {
      "denyRead": ["~/.ssh", "~/.aws"]
    },
    "network": {
      "allowedDomains": ["pypi.org", "files.pythonhosted.org", "github.com"]
    }
  }
}
```

Le chiavi sono quelle del Capitolo 2. Cambiano i domini: in un file di progetto metti quelli che servono a quel progetto, non quelli che usi tu ogni giorno. Qui ci sono i due da cui `pip` scarica i pacchetti e GitHub; per tutto il resto il proxy locale chiede la prima volta, e la risposta la dà chi sta lavorando. Il `denyRead` su `~/.ssh` e `~/.aws` sembra fuori posto in un file di progetto, ma è il modo per garantirlo anche al collega che non ha mai toccato le sue impostazioni utente.

La sandbox copre solo i comandi shell e i processi che avviano: hook e server MCP, che aggiungi nei prossimi due capitoli, girano fuori, e lo stesso vale per i comandi che escludi perché non ci funzionano dentro, come `docker`. Se vuoi un confine attorno a tutto Claude Code serve un dev container, o un container o una VM dedicati.

::: {.callout .callout-warning}
[Attenzione]{.callout-title}

La sandbox funziona su macOS, Linux e WSL 2. Su Windows nativo non è supportata e i comandi girano senza confine, anche se `.claude/settings.json` dice `"enabled": true`. Su Linux e WSL 2 servono i pacchetti di sistema: `sudo apt-get install bubblewrap socat`. Se nel team qualcuno lavora su Windows senza WSL, la configurazione condivisa per lui non vale: diglielo, e fai in modo che le regole deny coprano comunque i casi importanti.
:::

## 11.9 Una configurazione consigliata per i progetti del libro

Mettendo insieme i pezzi, la configurazione che uso per i progetti del libro è questa: auto mode per lavorare, deny sui segreti e sui comandi pericolosi, ask sul push, sandbox attiva. Per il laboratorio, il `.claude/settings.json` finale è:

```json
{
  "permissions": {
    "allow": [
      "Bash(python -m pytest *)",
      "Bash(git diff *)"
    ],
    "ask": [
      "Bash(git push *)"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Bash(curl *)",
      "Bash(git push --force *)",
      "Agent(model:opus)"
    ]
  },
  "sandbox": {
    "enabled": true,
    "allowUnsandboxedCommands": false,
    "filesystem": {
      "denyRead": ["~/.ssh", "~/.aws"]
    },
    "network": {
      "allowedDomains": ["pypi.org", "files.pythonhosted.org", "github.com"]
    }
  }
}
```

Non c'è `defaultMode`: auto mode è già il default, e comunque `"auto"` scritto in un file di progetto verrebbe ignorato. Chi vuole partire in Manual usa il flag. Il deny su `git push --force` si somma all'ask su `git push`: il force push scritto così è negato, quello scritto con `-f` cade comunque nell'ask e ti arriva la domanda.

Per la Photogallery, che usi nella Parte VI, cambiano i comandi e i percorsi. Il backend Laravel ha il suo `backend/.env`, il frontend React il suo `frontend/.env`, e i test del backend girano con Pest attraverso `php artisan test`:

```json
{
  "permissions": {
    "allow": [
      "Bash(php artisan test *)",
      "Bash(vendor/bin/pint *)",
      "Bash(npm run lint)",
      "Bash(npm run build)",
      "Bash(git diff *)"
    ],
    "ask": [
      "Bash(git push *)",
      "Bash(php artisan migrate *)"
    ],
    "deny": [
      "Read(./backend/.env)",
      "Read(./backend/.env.backup)",
      "Read(./backend/.env.production)",
      "Read(./frontend/.env)",
      "Bash(git push --force *)",
      "Bash(git reset --hard *)"
    ]
  }
}
```

Qui ho elencato i file `.env` uno per uno invece di usare `.env.*`, perché il pattern colpirebbe anche `backend/.env.example`, che non contiene segreti e che Claude legge volentieri per capire quali variabili servono. `php artisan migrate` sta in `ask` perché una migrazione su un database sbagliato non si annulla con `git checkout`. Se sulla tua macchina gira la sandbox, aggiungi lo stesso blocco `sandbox` del laboratorio, con i domini di Composer e npm al posto di quelli di pip.

<!-- VERIFY: domini da aggiungere ad allowedDomains per Composer (packagist.org, repo.packagist.org) e npm (registry.npmjs.org) -->

Un'ultima nota: il repository companion della Photogallery ha già un `.claude/settings.json`, che contiene solo hook. Se aggiungi i permessi, uniscili nello stesso file sotto la chiave `permissions`, senza sostituire quello che c'è. Gli hook sono l'argomento del prossimo capitolo.

## Riepilogo

- La modalità attiva è scritta sotto il prompt e si cambia con `Shift+Tab` (auto, Manual, accept edits, plan); `dontAsk` e `bypassPermissions` si scelgono con `--permission-mode` e servono per CI e ambienti isolati.
- Le regole allow, ask e deny in `.claude/settings.json` valgono per tutto il team; l'ordine è deny, poi ask, poi allow, e un deny vince sempre.
- Una regola su Bash confronta il testo del comando: per un confine vero servono la sandbox o un hook, e le istruzioni in `CLAUDE.md` non sono permessi.
- In auto mode le tue regole vengono prima del classificatore. Usa i deny per quello che non deve succedere mai e lascia al classificatore i casi imprevisti; `/permissions` mostra regole, origine e Recently denied.
- La sandbox in `.claude/settings.json`, con `allowUnsandboxedCommands: false` e `denyRead` sulle credenziali, mette un confine di sistema attorno ai comandi shell, non attorno a hook e server MCP.

## Esercizio

Nel laboratorio, proteggi i dati di input. Aggiungi a `.claude/settings.json` una regola ask che copra le modifiche a qualunque file sotto `data/`, riavvia `claude`, passa ad accept edits con `Shift+Tab` e chiedi:

```text
aggiungi a data/vendite.csv la riga 2026-04,110 e aggiorna il test
```

In accept edits la modifica a `tests/test_report.py` passa senza domande, quella a `data/vendite.csv` deve chiederti conferma. Rifiutala. L'esercizio è fatto quando `/permissions` mostra la tua regola nella scheda Ask con origine `From shared project settings` e `git status` non elenca `data/vendite.csv` tra i file modificati. Se dopo il rifiuto Claude prova ad aggiungere la riga con un comando shell, per esempio `echo ... >> data/vendite.csv`, stai vedendo dal vivo il limite della Sezione 11.4: la regola su `Edit` non lo copre, e in accept edits ti ferma solo la richiesta di conferma per il comando. Poi ripeti la prova in auto mode e controlla che la domanda per la modifica arrivi lo stesso.
