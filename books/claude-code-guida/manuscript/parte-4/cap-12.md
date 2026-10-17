# Capitolo 12. Hook, automazioni deterministiche

**Cosa imparerai**

Scrivere hook che formattano il codice dopo ogni modifica, bloccano le scritture sui file sensibili, ti avvisano quando Claude ti aspetta e gli impediscono di chiudere il lavoro con i test rossi. Imparerai anche a testarli a mano e a capire perché non partono.

**Prerequisiti**

Il progetto `cc-advanced-lab` del capitolo 11, con il suo `.claude/settings.json`. Servono `jq` (`brew install jq` su macOS, `sudo apt-get install jq` su Debian e Ubuntu), `ruff` e `pytest` (`pip install ruff pytest`). Su Windows gli script `.sh` girano in Git Bash, quindi installa Git for Windows; `jq` non è incluso, e lo aggiungi con `winget install jqlang.jq`.

Nei capitoli precedenti abbiamo chiesto le cose a Claude a parole: formatta il codice, non toccare il file `.env`, lancia i test prima di dire che hai finito. Le abbiamo scritte nei prompt, poi nel `CLAUDE.md` (capitolo 7), e funzionano quasi sempre. Il guaio sta in quel "quasi". Un'istruzione nel contesto è un'indicazione che il modello segue con buona probabilità; in una sessione lunga, o subito dopo una compattazione, può scivolare via. Le regole di permesso del capitolo 11 coprono una parte del problema, perché decidono se un'azione può partire. Non possono però eseguire un formatter, lanciare la suite di test o mandarti una notifica.

Gli hook servono a questo. Sono comandi che Claude Code esegue da solo in punti precisi del suo ciclo di lavoro, ogni volta, senza che il modello debba ricordarsene. Il modello non li chiama e non può saltarli: li lancia l'harness, il programma che sta intorno al modello e che esegue i tool (capitolo 2).

## 12.1 Gli eventi del ciclo di lavoro

Ogni hook è agganciato a un evento. Prima che Claude usi un tool scatta `PreToolUse`, che può anche bloccare l'azione. Subito dopo scatta `PostToolUse`. Quando Claude finisce di rispondere scatta `Stop`, quando ha bisogno di te scatta `Notification`, all'apertura della sessione `SessionStart`. Con questi, più `UserPromptSubmit`, copri la maggior parte dei casi pratici.

| Evento | Quando scatta | Può bloccare |
| --- | --- | --- |
| `SessionStart` | Avvio, ripresa, dopo `/clear` o una compattazione | No |
| `UserPromptSubmit` | Quando invii un prompt, prima che Claude lo elabori | Sì |
| `PreToolUse` | Prima di ogni chiamata a un tool | Sì |
| `PostToolUse` | Dopo una chiamata riuscita | No, il tool ha già agito |
| `Stop` | Quando Claude finisce di rispondere | Sì, lo fa continuare |
| `Notification` | Quando Claude aspetta un input o un permesso | No |

Gli eventi sono parecchi di più: ci sono, tra gli altri, `SubagentStop` quando un subagent finisce, `PreCompact` prima di una compattazione e `SessionEnd` alla chiusura della sessione. La lista completa e aggiornata è nella documentazione ufficiale, ma per tutto questo capitolo bastano i sei della tabella.

La colonna "Può bloccare" va letta con attenzione. Bloccare un `Stop` non ferma niente: impedisce a Claude di fermarsi e lo rimanda al lavoro con un motivo. Un `PostToolUse` invece arriva a cose fatte; puoi reagire, per esempio formattando il file appena scritto, ma la scrittura è già avvenuta.

## 12.2 Come comunica un hook

Un hook di tipo `command` è un normale comando di shell. Claude Code gli passa i dati dell'evento in JSON sullo standard input e legge la risposta da due canali: il codice di uscita e, se serve, lo standard output.

Per un `PreToolUse` su `Bash`, l'input ha questa forma:

```json
{
  "session_id": "abc123",
  "cwd": "/home/dev/cc-advanced-lab",
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": { "command": "python -m pytest" }
}
```

Il campo `tool_input` cambia da tool a tool. Per `Bash` contiene `command`; per `Edit` e `Write` contiene `file_path` (con il percorso assoluto) e il contenuto da scrivere. Gli script di questo capitolo leggono quei campi con `jq`.

Le risposte possibili sono tre:

| Risposta | Significato |
| --- | --- |
| Exit 0 | Nessuna obiezione, si prosegue |
| Exit 2 | Blocca; il testo su stderr torna a Claude come spiegazione |
| Exit 0 con JSON su stdout | Controllo più fine, per esempio `{"decision": "block", "reason": "..."}` per `Stop` |

L'exit 0 di un `PreToolUse` va capito bene: vuol dire "non ho niente da dire", non "approvo". Dopo l'hook l'azione passa comunque per il normale sistema di permessi, con le regole allow, ask e deny e la modalità attiva. L'exit 2 invece ferma l'azione, e il messaggio su stderr arriva a Claude, che così sa perché è stato fermato e può cercare un'altra strada. Qualunque altro codice di uscita viene trattato come un errore dell'hook che non blocca nulla: l'azione prosegue.

Il JSON su stdout serve quando il codice di uscita non basta. Lo userai nel paragrafo 12.7 per lo `Stop`, dove il campo `reason` diventa l'istruzione con cui Claude riparte. Per `PreToolUse` lo stesso canale permette di restituire una decisione esplicita di permesso al posto del semplice blocco: dentro `hookSpecificOutput` metti `permissionDecision` con `allow`, `deny` o `ask`, e in `permissionDecisionReason` il motivo.

### Dove si registrano

Gli hook si configurano nel `settings.json`, sotto la chiave `hooks`, accanto a `permissions`. La struttura ha tre livelli: l'evento, un elenco di gruppi con il loro `matcher`, e dentro ogni gruppo l'elenco dei comandi da eseguire. Il `matcher` filtra per nome del tool: `"Edit|Write"` fa scattare il gruppo solo per quei due tool, ed è sensibile alle maiuscole, quindi `"edit"` non corrisponde a niente. I file sono gli stessi del capitolo 11: `.claude/settings.json` per il progetto e il team, `.claude/settings.local.json` per te solo su quel progetto, `~/.claude/settings.json` per tutti i tuoi progetti.

Negli esempi il percorso dello script parte da `$CLAUDE_PROJECT_DIR`, una variabile che Claude Code imposta sulla radice del progetto. Così il comando funziona anche quando la shell di Claude si è spostata in una sottocartella. Le virgolette intorno alla variabile proteggono i percorsi con spazi, e nel JSON vanno scritte come `\"`.

## 12.3 Formattare dopo ogni modifica

Il primo hook formatta con `ruff` ogni file Python che Claude scrive o modifica. Nel progetto del laboratorio crea la cartella degli script:

```bash
mkdir -p .claude/hooks
```

Poi il file `.claude/hooks/format-python.sh`:

```bash
#!/bin/bash
# Formatta con ruff i file Python modificati da Claude
FILE_PATH=$(jq -r '.tool_input.file_path // empty')

if [[ "$FILE_PATH" == *.py ]]; then
  ruff format "$FILE_PATH" >/dev/null 2>&1
fi

exit 0
```

`jq` legge il JSON direttamente dallo standard input e ne estrae `tool_input.file_path`; il `// empty` restituisce una stringa vuota quando il campo manca, invece della parola `null`. Se il file finisce in `.py` lo script lo passa a `ruff format`, che lo riscrive in place. L'output di ruff va in `/dev/null` perché qui non interessa a nessuno, e lo script esce sempre con 0: un formatter non deve mai bloccare il lavoro.

Rendi lo script eseguibile:

```bash
chmod +x .claude/hooks/format-python.sh
```

E aggiungi il blocco `hooks` al `.claude/settings.json`, accanto ai `permissions` del capitolo 11:

```json
{
  "permissions": { "...": "come nel capitolo 11" },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/format-python.sh"
          }
        ]
      }
    ]
  }
}
```

La riga `"permissions"` qui è abbreviata: nel tuo file restano le regole allow, ask e deny che hai già scritto, e il blocco `sandbox` del paragrafo 11.9. Il file completo, con tutti gli hook del capitolo, è nel paragrafo 12.7.

Gli hook vengono letti all'avvio, quindi riavvia Claude Code dopo ogni modifica al `settings.json`. Poi digita `/hooks`: sotto `PostToolUse` devi trovare il gruppo con matcher `Edit|Write`, il comando `format-python.sh` e l'indicazione che viene dalle impostazioni di progetto (`[Project]`). Se non c'è, il problema sta nel JSON o nel nome dell'evento, e non ha senso andare avanti.

<!-- TODO screenshot: pannello /hooks con PostToolUse, matcher Edit|Write e origine [Project] -->

Ora una prova cattiva di proposito:

```text
aggiungi a src/report.py una funzione massimo(path) scritta tutta su una riga, senza spazi
```

Nel prompt non c'è nessuna istruzione sul formato, e anzi chiediamo il contrario. Claude scrive la funzione su una riga; appena il tool `Edit` termina, Claude Code lancia l'hook e ruff riscrive il file. Aprilo dal prompt di Claude Code con il prefisso `!`, che esegue un comando di shell senza passare dal modello:

```text
!cat src/report.py
```

La funzione è su più righe, con il corpo indentato, e ruff ha anche normalizzato le virgolette nel resto del file. Nella registrazione della lezione Claude ha poi commentato da solo il risultato, dicendo che il formatter aveva spezzato `massimo` su più righe: non vede l'hook, ma si accorge che il file è cambiato.

Nessuno ha dovuto ricordarsi di formattare. Lo stesso schema funziona con qualunque formatter o linter veloce: `prettier --write` per un frontend, `php-cs-fixer` per Laravel, `gofmt` per Go. Cambia solo l'estensione da controllare e il comando.

## 12.4 Proteggere i file sensibili

Il secondo hook gira prima di ogni modifica e blocca quelle sui file protetti: il `.env`, la cartella `.git/` e, nel nostro laboratorio, i dati di origine in `data/`. Crea `.claude/hooks/protect-files.sh`:

```bash
#!/bin/bash
# Blocca le modifiche ai file sensibili
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
FILE_PATH="${FILE_PATH//\\//}"   # normalizza i separatori di Windows

PROTECTED=(".env" ".git/" "data/")

for pattern in "${PROTECTED[@]}"; do
  if [[ "$FILE_PATH" == *"$pattern"* ]]; then
    echo "Bloccato: $FILE_PATH è protetto ('$pattern'). Lavora su una copia." >&2
    exit 2
  fi
done

exit 0
```

Questa volta lo script salva prima tutto l'input in `INPUT` con `cat`, poi lo passa a `jq`. Nel primo hook non serviva perché il JSON veniva letto una volta sola; tenerlo in una variabile ti permette di estrarre più campi senza consumare lo stdin. La riga successiva sostituisce ogni backslash con una barra: su Windows `file_path` arriva come `C:\Users\...\data\vendite.csv`, e senza normalizzazione il pattern `data/` non corrisponderebbe mai. Il ciclo confronta il percorso con ogni elemento di `PROTECTED`; alla prima corrispondenza scrive il motivo su stderr ed esce con 2.

Rendilo eseguibile e registralo sotto `PreToolUse`, dentro lo stesso oggetto `hooks` che contiene già `PostToolUse`:

```bash
chmod +x .claude/hooks/protect-files.sh
```

```json
"PreToolUse": [
  {
    "matcher": "Edit|Write",
    "hooks": [
      {
        "type": "command",
        "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect-files.sh"
      }
    ]
  }
]
```

Riavvia Claude Code e chiedi una modifica ai dati:

```text
aggiungi una riga con il mese 2026-04 a data/vendite.csv
```

Anche qui il prompt non dice niente sulla protezione: la regola vive solo nell'hook. Durante la registrazione Claude non ha provato subito a scrivere, ma ha chiesto prima quale valore di vendite mettere per aprile, con una domanda a scelta multipla. Rispondi con un numero qualsiasi. A quel punto Claude prova l'`Edit`, l'hook scatta e nel terminale compare la riga rossa con il messaggio di blocco. Claude lo legge, spiega perché è stato fermato e propone un'alternativa, per esempio lavorare su una copia del file. Controlla con `git status` che `data/vendite.csv` sia rimasto com'era.

::: {.callout .callout-tip}
[Suggerimento]{.callout-title}

Il messaggio di blocco mostra il percorso assoluto, perché è quello che `Edit` passa all'hook. Se registri lo schermo o incolli i log da qualche parte, ci finisce dentro il tuo nome utente. Per stampare il percorso relativo al progetto basta togliere il prefisso prima dell'`echo`, per esempio con `REL="${FILE_PATH#"$CLAUDE_PROJECT_DIR"/}"`, e usare `$REL` nel messaggio.
:::

### Testare un hook a mano

Gli script degli hook si provano senza Claude, passando un JSON di esempio con `echo`. Esci da Claude Code e lancia dalla shell, nella radice del progetto:

```bash
echo '{"tool_input":{"file_path":"data/vendite.csv"}}' | .claude/hooks/protect-files.sh; echo "exit: $?"
```

L'output atteso è:

```text
Bloccato: data/vendite.csv è protetto ('data/'). Lavora su una copia.
exit: 2
```

Il JSON di prova contiene solo i campi che lo script legge, e va bene così. Con un percorso non protetto, per esempio `src/report.py`, devi vedere soltanto `exit: 0`. Lo stesso trucco vale per il formatter:

```bash
echo '{"tool_input":{"file_path":"src/report.py"}}' | .claude/hooks/format-python.sh; echo "exit: $?"
```

Quando un hook non fa quello che ti aspetti, questo è il primo controllo da fare. Ti dice subito se il problema è nello script (`jq` che manca, un pattern sbagliato, un permesso di esecuzione assente) o nella registrazione.

## 12.5 Regola deny o hook?

Nel capitolo 11 hai già scritto una regola `deny` su `Read(./.env)`. Viene naturale chiedersi perché servano anche gli hook.

Una regola confronta un pattern con la chiamata: nome del tool più specificatore, e niente altro. Un hook esegue codice tuo, quindi può applicare qualunque logica: guardare il contenuto che Claude vuole scrivere, controllare il branch corrente, leggere un file di configurazione, chiamare un altro programma. E un hook che nega blocca l'azione in ogni modalità di permesso, anche in `bypassPermissions`, dove le richieste di conferma spariscono.

Per regole semplici e statiche ("non leggere `.env`", "chiedi prima di `git push`") la regola nel `settings.json` resta la scelta giusta: si legge in una riga, la vedi in `/permissions` e non ha dipendenze. L'hook serve quando la condizione richiede un ragionamento che un pattern non esprime, o quando vuoi un'azione e non solo un sì o un no.

::: {.callout .callout-warning}
[Attenzione]{.callout-title}

`protect-files.sh` è registrato con matcher `Edit|Write`, quindi guarda solo quei due tool. Se Claude decidesse di aggiungere la riga con un comando di shell, per esempio `echo "2026-04,0" >> data/vendite.csv`, l'hook non scatterebbe. Una regola su `Bash` confronta il testo del comando, e un hook su `Bash` che analizza il comando ha lo stesso limite. Per un confine che regga davvero sulla scrittura dei file usa la sandbox con `filesystem.denyWrite` (capitoli 2 e 11), e tieni gli hook come primo filtro.
:::

C'è anche il rovescio della medaglia. Gli hook girano con i permessi del tuo utente e fuori dalla sandbox. Un `.claude/settings.json` con degli hook, in un repository clonato da qualcun altro, è codice che verrà eseguito sulla tua macchina appena avvii Claude Code in quella cartella. Prima di lavorare su un repo che non conosci, aprilo e leggi cosa c'è sotto `hooks`.

## 12.6 Una notifica quando Claude ti aspetta

Quando lasci Claude a lavorare su un task lungo e passi a un'altra finestra, capita di scoprire molto dopo che era fermo su una richiesta di permesso. L'evento `Notification` scatta proprio in quei momenti. Questo hook va nelle impostazioni utente, `~/.claude/settings.json`, così vale per tutti i progetti:

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "notify-send 'Claude Code' 'Claude ti sta aspettando'"
          }
        ]
      }
    ]
  }
}
```

Il matcher vuoto vale per ogni notifica. `notify-send` è il comando standard dei desktop Linux (su Debian e Ubuntu sta nel pacchetto `libnotify-bin`). Su macOS sostituisci il comando con:

```bash
osascript -e 'display notification "Claude ti sta aspettando" with title "Claude Code"'
```

Dentro il JSON le virgolette doppie di questo comando vanno scritte come `\"`. Se il tuo `~/.claude/settings.json` ha già altre chiavi, aggiungi `hooks` accanto a quelle senza sostituire il file.

## 12.7 Niente stop con i test rossi

Il terzo hook di progetto è quello che uso di più nei progetti Spec Driven Development (capitoli 18 e 19). Quando Claude sta per fermarsi, l'hook lancia i test. Se falliscono, restituisce un JSON con `decision` uguale a `block` e come motivo l'output dei test. Claude non si ferma: legge il motivo e continua a lavorare. Crea `.claude/hooks/tests-before-stop.sh`:

```bash
#!/bin/bash
# Impedisce a Claude di fermarsi se i test falliscono
INPUT=$(cat)

# Evita il ciclo infinito: se stiamo già continuando a causa di questo hook, lascia fermare Claude
if [ "$(echo "$INPUT" | jq -r '.stop_hook_active')" = "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR" || exit 0
if ! OUTPUT=$(python -m pytest -q 2>&1); then
  jq -n --arg out "$(echo "$OUTPUT" | tail -20)" \
    '{decision: "block", reason: ("I test falliscono, correggili prima di chiudere:\n" + $out)}'
fi

exit 0
```

Il controllo su `stop_hook_active` è la riga più importante dello script. Claude Code imposta quel campo a `true` quando Claude sta già continuando perché uno Stop hook l'ha rimandato al lavoro. Senza il controllo, un test che Claude non riesce a sistemare produrrebbe un ciclo senza fine: stop, test rossi, blocco, nuovo tentativo, stop, e così via, consumando token a ogni giro.

Il resto è lineare. Lo script si sposta nella radice del progetto, lancia `pytest` in modalità silenziosa e cattura stdout e stderr in `OUTPUT`. Se pytest esce con un codice diverso da zero, `jq -n` costruisce il JSON da zero: `--arg out` passa le ultime venti righe dell'output come stringa, già correttamente escapata, e il filtro le concatena al messaggio. Usare `jq` invece di comporre il JSON a mano con `echo` evita i guai con le virgolette e gli a capo dentro l'output di pytest. Lo script esce sempre con 0, perché qui il blocco passa dal JSON.

Rendilo eseguibile e registralo sotto `Stop`:

```bash
chmod +x .claude/hooks/tests-before-stop.sh
```

```json
"Stop": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/tests-before-stop.sh",
        "timeout": 120
      }
    ]
  }
]
```

`Stop` non riguarda un tool, quindi il gruppo non ha `matcher`. Il `timeout` è in secondi. Per gli hook `command` il predefinito è 600, dieci minuti: qui lo abbasso a 120, perché se la suite si pianta preferisco non restare appeso dieci minuti a ogni stop. Su questo laboratorio pytest ci mette meno di un secondo. Allo scadere l'hook viene interrotto e conta come un errore che non blocca niente: Claude si ferma comunque.

A questo punto il `.claude/settings.json` del laboratorio contiene i permessi e la sandbox del capitolo 11 e i tre hook di progetto:

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
  },
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{
        "type": "command",
        "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/format-python.sh"
      }]
    }],
    "PreToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{
        "type": "command",
        "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect-files.sh"
      }]
    }],
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/tests-before-stop.sh",
        "timeout": 120
      }]
    }]
  }
}
```

### La prova

Per vedere l'hook al lavoro serve un test rosso. Con Claude Code chiuso, rompi apposta il test cambiando `358` in `359`:

```bash
sed -i 's/358/359/' tests/test_report.py
```

Su macOS la sintassi di `sed` vuole un argomento vuoto dopo `-i`: `sed -i '' 's/358/359/' tests/test_report.py`. Puoi anche correggere il numero a mano nell'editor, il risultato è lo stesso.

Prima di avviare Claude puoi provare lo script con `echo`, come nel paragrafo 12.4. C'è un dettaglio: `CLAUDE_PROJECT_DIR` la imposta Claude Code, nella tua shell non esiste. Passala tu sulla riga di comando:

```bash
echo '{"stop_hook_active": false}' | CLAUDE_PROJECT_DIR="$PWD" .claude/hooks/tests-before-stop.sh
```

Devi vedere il JSON con `"decision": "block"` e, nel `reason`, il fallimento di `test_totale`. Con `"stop_hook_active": true` lo script non deve stampare niente.

Ora avvia `claude` e chiedi una modifica che con i test non c'entra niente:

```text
aggiungi un docstring alla funzione totale
```

Claude aggiunge il docstring e prova a fermarsi. Lo Stop hook non chiede il permesso al modello: parte da solo, lancia pytest, trova il test rosso e blocca. Nel terminale compare il riscontro dell'hook, `Stop hook error: I test falliscono, correggili prima di chiudere:` seguito dall'output di pytest. Claude legge il motivo, vede che il test si aspetta 359 mentre la somma dei dati è 358, riporta il valore corretto e rilancia i test. Al secondo stop `stop_hook_active` è `true` e l'hook lo lascia fermare.

<!-- TODO screenshot: riscontro dello Stop hook con l'output di pytest e Claude che corregge il test -->

Con questo script il blocco scatta una volta per risposta. Se dopo il primo giro i test fossero ancora rossi, al secondo stop l'hook lascerebbe comunque fermare Claude: è il prezzo del controllo anti-loop. Nella pratica basta, perché Claude riceve l'output di pytest e di solito sistema il problema al primo tentativo, e in ogni caso a fine risposta vedi lo stato reale dei test.

Nota anche che in questa prova Claude ha corretto il test, non il codice. Qui era la scelta giusta, perché il test l'avevamo rotto noi. In un progetto vero un test rosso può voler dire che è sbagliata l'implementazione: se vuoi che Claude non tocchi i test senza chiedere, scrivilo nel `CLAUDE.md` o aggiungi `tests/` alla lista di `protect-files.sh`.

## 12.8 Hook condizionali, SessionStart e gli altri tipi

Due varianti utili, anche se nel laboratorio non le useremo.

La prima è il campo `if`, che usa la stessa sintassi delle regole di permesso. Qui l'hook parte solo per i comandi `git`, non per tutti i comandi `Bash`:

```json
"PreToolUse": [
  {
    "matcher": "Bash",
    "hooks": [
      {
        "type": "command",
        "if": "Bash(git *)",
        "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/check-git-policy.sh"
      }
    ]
  }
]
```

Il `matcher` seleziona il tool, l'`if` restringe in base all'input. Senza `if`, lo script dovrebbe leggere `tool_input.command` e uscire subito con 0 per tutto quello che non comincia con `git`: funziona, ma ogni `ls` e ogni `pytest` farebbero partire un processo in più.

La seconda usa `SessionStart` con il matcher `compact`. Dopo ogni compattazione del contesto, quello che l'hook stampa su stdout viene aggiunto al contesto di Claude:

```json
"SessionStart": [
  {
    "matcher": "compact",
    "hooks": [
      {
        "type": "command",
        "command": "echo 'Ricorda: leggi SPEC.md prima di implementare. Ultimi commit:' && git log --oneline -5"
      }
    ]
  }
]
```

Per `SessionStart` il matcher filtra l'origine della sessione, e `compact` indica la ripresa dopo una compattazione. È un buon modo per non perdere per strada le regole del progetto, come leggere la specifica prima di implementare, proprio nel momento in cui il riassunto rischia di averle diluite. Nel capitolo 15 torniamo sulla compattazione e su cosa sopravvive.

Oltre a `command` esistono altri tipi di hook. Quelli di tipo `http` inviano il JSON dell'evento a un URL, utile per un servizio interno che registra o approva le azioni. Quelli di tipo `prompt` e `agent` chiedono a un modello di decidere, per le condizioni che uno script non sa valutare, come "questa modifica rispetta le convenzioni del `CLAUDE.md`?". Gli hook `agent` sono ancora sperimentali. Infine, gli hook possono viaggiare dentro un plugin, nel file `hooks/hooks.json` con i percorsi basati su `${CLAUDE_PLUGIN_ROOT}`: lo vedremo nel capitolo 14.

## 12.9 Quando un hook non funziona

I problemi più comuni, con la soluzione:

| Problema | Soluzione |
| --- | --- |
| L'hook non parte | `/hooks` per controllare evento e matcher (sono sensibili alle maiuscole); riavvia Claude Code dopo ogni modifica al `settings.json` |
| `jq: command not found` | Installa `jq` o riscrivi lo script in Python |
| Lo script non parte | `chmod +x` sullo script |
| Il JSON stampato viene ignorato | Un `echo` nel profilo della shell sporca l'output: spostalo dentro `if [[ $- == *i* ]]` |
| Claude non si ferma mai | Manca il controllo su `stop_hook_active` |

La quarta riga merita un esempio. Se nel tuo `~/.bashrc` c'è un messaggio di benvenuto, quando la shell viene caricata per eseguire l'hook quel testo finisce su stdout prima del JSON, e Claude Code non riesce più a interpretarlo. La guardia fa stampare il messaggio solo nelle shell interattive:

```bash
if [[ $- == *i* ]]; then
  echo "Benvenuto"
fi
```

Due controlli in più, che non stanno in tabella ma fanno risparmiare tempo. Prima di guardare la configurazione, lancia lo script a mano con `echo` come nel paragrafo 12.4: se lì sbaglia, il `settings.json` non c'entra. E su Windows verifica che Claude Code stia usando Git Bash, perché in PowerShell uno script `.sh` non parte (il capitolo 1 spiega come indicare il percorso con `CLAUDE_CODE_GIT_BASH_PATH`).

## Riepilogo

- Un hook è un comando che Claude Code esegue da solo su un evento: trasforma una raccomandazione che il modello segue quasi sempre in una regola che vale ogni volta.
- Si registra nel `settings.json` sotto `hooks`, con evento, `matcher` e comando; il percorso dello script parte da `"$CLAUDE_PROJECT_DIR"` e le modifiche valgono dal riavvio successivo.
- L'hook riceve JSON su stdin e risponde con il codice di uscita: 0 prosegue (per `PreToolUse` non è un'approvazione), 2 blocca e manda stderr a Claude, 0 più JSON su stdout per decisioni come il `block` di `Stop`.
- Uno Stop hook deve sempre controllare `stop_hook_active`, altrimenti rischi un ciclo infinito.
- Un hook che nega blocca in ogni modalità, ma vede solo i tool del suo matcher: per un confine vero sui file serve anche la sandbox.
- Gli hook si provano a mano con `echo` e si controllano con `/hooks`.

## Esercizio

Scrivi `.claude/hooks/check-git-policy.sh`, lo script citato nel paragrafo 12.8, e registralo sotto `PreToolUse` con matcher `Bash` e `"if": "Bash(git *)"`. Lo script legge `tool_input.command` e blocca con exit 2 ogni `git push` che contenga `--force` o `-f`, con un messaggio in italiano su stderr che suggerisca `--force-with-lease`. Tutti gli altri comandi passano con exit 0, compreso proprio `--force-with-lease`: attento al pattern, perché la stringa contiene `--force`.

L'esercizio è finito quando questi tre test a mano danno il risultato atteso:

```bash
echo '{"tool_input":{"command":"git push --force origin main"}}' | .claude/hooks/check-git-policy.sh; echo "exit: $?"
echo '{"tool_input":{"command":"git push --force-with-lease origin main"}}' | .claude/hooks/check-git-policy.sh; echo "exit: $?"
echo '{"tool_input":{"command":"git status"}}' | .claude/hooks/check-git-policy.sh; echo "exit: $?"
```

Il primo deve stampare il tuo messaggio ed `exit: 2`, gli altri due solo `exit: 0`. Poi riavvia Claude Code e controlla che `/hooks` mostri il nuovo gruppo sotto `PreToolUse`, con il comando `check-git-policy.sh`.
