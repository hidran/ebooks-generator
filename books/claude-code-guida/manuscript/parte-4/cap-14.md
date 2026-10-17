# Capitolo 14. Plugin e marketplace, impacchettare skill, agent e hook

## Cosa imparerai

Impari a installare un plugin dal marketplace ufficiale sapendo cosa ti costa in contesto e di chi ti stai fidando, poi a costruire il tuo: `cc-lab-toolkit`, che mette insieme la skill `report-pdf` del capitolo 9, un agent di revisione Python e l'hook di formattazione del capitolo 12. Lo condividi con il team attraverso un marketplace e alla fine misuri se serve davvero con `claude plugin eval`.

## Prerequisiti

Il progetto `cc-advanced-lab` dei capitoli 11-13, con la skill `.claude/skills/report-pdf/SKILL.md` e lo script `.claude/hooks/format-python.sh`. Git 2.31 o successivo, che serve a `claude plugin eval` (controlla con `git --version`). Una cartella vuota `~/cc-plugins` dove lavorare.

## 14.1 Perché un plugin

Negli ultimi capitoli hai accumulato pezzi: una skill in `.claude/skills/`, un agent in `.claude/agents/`, un hook registrato in `.claude/settings.json` con il suo script in `.claude/hooks/`, magari un server MCP in `.mcp.json`. Ognuno funziona benissimo da solo, dentro il progetto in cui l'hai creato.

Il problema arriva il giorno in cui vuoi le stesse cose in un secondo progetto, o un collega te le chiede. A quel punto copi cartelle a mano e incolli pezzi di `settings.json` cercando di non rompere il JSON che c'è già. Dopo un mese le copie sono tre e nessuno sa più quale sia quella buona.

Un **plugin** è la risposta di Claude Code a questo problema. È una cartella che contiene quei componenti più un piccolo file manifest, e Claude Code la carica come un'unica unità. Si installa con un comando, si aggiorna cambiando il numero di versione e si disattiva senza toccare i file del progetto. Dentro può stare tutto quello che hai visto nella Parte III e in questa parte:

- skill e agent, che prendono il nome del plugin come prefisso;
- hook, cioè le automazioni deterministiche legate agli eventi di Claude Code;
- server MCP, dichiarati in un `.mcp.json` nella radice del plugin.

Nel capitolo 8 hai già usato un plugin da utente: Superpowers. Quando l'hai installato hai ricevuto in un colpo solo un gruppo di skill e comandi, senza copiare niente. In questo capitolo passi dall'altra parte del banco e ne scrivi uno.

## 14.2 Il gestore /plugin e il marketplace ufficiale

Apri Claude Code in qualsiasi progetto e scrivi:

```text
/plugin
```

Si apre il gestore dei plugin, con le schede Discover, Installed e Marketplaces. Ti sposti da una all'altra con le frecce.

- Discover elenca i plugin disponibili nei marketplace che hai aggiunto.
- Installed mostra cosa hai installato e da dove arriva; da qui disattivi o rimuovi un plugin.
- Marketplaces elenca le sorgenti registrate: l'ufficiale, quelle aggiunte da te, quella del team.

<!-- VERIFY: il piano della lezione cita anche una scheda Errors per i plugin che non si caricano; non confermata dalla documentazione né dalla registrazione -->

Il marketplace ufficiale di Anthropic, `claude-plugins-official`, viene aggiunto da solo al primo avvio: non devi registrarlo. C'è poi un marketplace della community, `claude-community`, che puoi aggiungere quando ti serve qualcosa che nell'ufficiale non trovi. Se segui un tutorial che ti fa aggiungere `anthropics/claude-code` come marketplace, sappi che è solo un marketplace dimostrativo: va bene per curiosare, non per lavorare.

Lo stesso Superpowers del capitolo 8 oggi sta nel marketplace ufficiale e si installa con `/plugin install superpowers@claude-plugins-official`.

<!-- TODO screenshot: gestore /plugin sulla scheda Discover, con il dettaglio di un plugin ufficiale e la stima del costo in contesto -->

### Il costo in contesto

Prima di installare qualcosa apri il dettaglio del plugin in Discover e guarda la stima del costo in contesto. Un plugin attivo carica in ogni sessione il nome e la descrizione di ogni sua skill e di ogni suo agent, anche quando non li usi mai. Il corpo di una skill entra nel contesto solo quando la skill scatta, ma le descrizioni ci sono sempre: è lo stesso meccanismo che hai visto nel capitolo 9, moltiplicato per tutti i componenti del plugin.

Un plugin con due skill pesa poco. Una raccolta con quaranta skill, di cui ne usi tre, ti occupa una fetta di finestra di contesto in ogni sessione e aumenta le occasioni in cui una skill scatta quando non dovrebbe. Nel capitolo 15 vedrai come leggere questo peso con `/context` e come capire, con `/skill-doctor` e `/usage`, quali skill e quali plugin valgono quello che costano.

### Di chi ti fidi

La seconda cosa che guardo è chi pubblica il plugin. Un plugin esegue codice con i tuoi permessi: i suoi hook lanciano comandi sulla tua macchina ogni volta che scatta l'evento a cui sono legati, e un server MCP dichiarato nel plugin è un processo che parte con la sessione. Come hai visto nel capitolo 11, hook e server MCP stanno fuori dal sandbox dei comandi: seguono solo i permessi. Un hook in un plugin scaricato da un repository sconosciuto ha lo stesso potere di uno script che lanci tu dal terminale.

Il marketplace ufficiale è il punto di partenza ragionevole, quello della community richiede già un po' più di attenzione. Per tutto il resto la regola che seguo è semplice: prima di installare apro il repository, leggo `hooks/hooks.json` e gli script che richiama, e guardo l'eventuale `.mcp.json`. Sono pochi file e si leggono in cinque minuti.

Nel marketplace ufficiale trovi anche plugin dedicati proprio alla sicurezza: `security-guidance`, che controlla le modifiche di Claude mentre lavora, e Claude Security, che fa una scansione delle vulnerabilità con più agent e propone le patch.

### Installare plugin-dev

Il plugin che installo per primo è `plugin-dev`, dal marketplace ufficiale: è pensato per chi scrive plugin e lo tengo come aiuto per il resto del capitolo. Puoi selezionarlo in Discover oppure installarlo direttamente dal prompt:

```text
/plugin install plugin-dev@claude-plugins-official
```

<!-- VERIFY: contenuto preciso di plugin-dev (skill e agent per creare plugin); il testo lo descrive solo come aiuto per scrivere plugin -->

La sintassi è sempre la stessa: nome del plugin, chiocciola, nome del marketplace. Claude Code ti mostra i componenti del plugin e poi ti chiede lo scope dell'installazione, con la stessa logica che hai visto per i server MCP nel capitolo 13:

| Scope | Si applica a |
|---|---|
| user | tutti i tuoi progetti |
| project | tutto il team, tramite il `.claude/settings.json` condiviso in Git |
| local | solo a te, in questo repository |

Per un plugin di aiuto personale come `plugin-dev` scelgo user. Project ha senso quando vuoi che chiunque cloni il repository si ritrovi lo stesso plugin, come vedrai nel paragrafo 14.5. Finita l'installazione, controlla:

```text
/plugin list
```

`plugin-dev@claude-plugins-official` deve comparire tra i plugin installati.

Tutto quello che fai dal gestore ha un equivalente da terminale, comodo negli script di setup e quando vuoi controllare lo stato senza aprire una sessione:

```bash
claude plugin list
claude plugin details plugin-dev@claude-plugins-official
claude plugin disable plugin-dev@claude-plugins-official
claude plugin enable plugin-dev@claude-plugins-official
```

Ci sono anche `install`, `uninstall` e `update`, e il gruppo `claude plugin marketplace` con `add`, `list`, `remove` e `update`.

## 14.3 Costruire cc-lab-toolkit

Ora il tuo plugin. Lo chiamo `cc-lab-toolkit` perché raccoglie gli attrezzi del laboratorio: la skill che produce un report da un CSV, un agent che revisiona il codice Python e l'hook che formatta i file `.py` dopo ogni modifica.

### La struttura

Un plugin è una cartella con una sottocartella `.claude-plugin/` che contiene solo il manifest, `plugin.json`. Tutto il resto sta nella radice del plugin: `skills/`, `agents/`, `hooks/` con il file `hooks.json` e, se servono, un `.mcp.json` per i server MCP. Crea le cartelle:

```bash
cd ~/cc-plugins
mkdir -p cc-lab-toolkit/.claude-plugin
mkdir -p cc-lab-toolkit/skills/report-pdf
mkdir -p cc-lab-toolkit/agents
mkdir -p cc-lab-toolkit/hooks/scripts
```

Ti consiglio di fare di `~/cc-plugins` un repository Git fin da subito (`git init`): ti servirà per condividerlo nel paragrafo 14.5 e per le eval nel 14.7.

### Il manifest

Crea `cc-lab-toolkit/.claude-plugin/plugin.json`:

```json
{
  "name": "cc-lab-toolkit",
  "description": "Report da CSV, revisione del codice e formattazione automatica per progetti Python",
  "version": "1.0.0",
  "author": {
    "name": "Hidran Arias"
  }
}
```

L'unico campo obbligatorio è `name`, e conta più di quanto sembri: diventa il prefisso di tutte le skill e di tutti gli agent del plugin. La skill `report-pdf`, una volta dentro `cc-lab-toolkit`, si chiama `/cc-lab-toolkit:report-pdf`. Il prefisso evita le collisioni con skill omonime di altri plugin. Scegli quindi un nome corto, in minuscolo con i trattini: lo scriverai spesso.

`version` diventa importante quando il plugin viene distribuito, perché è il numero che fa arrivare gli aggiornamenti a chi l'ha installato. `description` è quello che i colleghi leggono nel gestore prima di decidere se installarlo: scrivila per loro. Al posto del mio nome in `author` metti il tuo.

### La skill

La skill è quella del capitolo 9. La copi così com'è nella cartella che hai appena creato:

```bash
cp ~/cc-advanced-lab/.claude/skills/report-pdf/SKILL.md cc-lab-toolkit/skills/report-pdf/
```

Nel plugin la skill non cambia formato: stessa cartella con il nome della skill, stesso `SKILL.md` con il frontmatter. Cambia solo il nome con cui la invochi.

::: {.callout .callout-example}
[Esempio]{.callout-title}

Se non hai più la skill del capitolo 9, per seguire il capitolo basta una versione minima. Questa legge il CSV e risponde con una tabella, senza scrivere file:

```markdown
---
name: report-pdf
description: Prepara un breve report di vendite da un file CSV, pronto da incollare in un PDF. Usala quando l'utente chiede un report, un riepilogo o i totali di un file CSV.
argument-hint: <file-csv>
allowed-tools: Read
---

Leggi il file CSV passato come argomento.

Rispondi con una tabella Markdown con il numero di righe, il totale,
il minimo, il massimo e la media della colonna numerica.

Non creare e non modificare file.
```
:::

<!-- VERIFY: allineare nome, description e corpo della skill report-pdf con la versione costruita nel capitolo 9 -->

### L'agent

Crea `cc-lab-toolkit/agents/python-reviewer.md`:

```markdown
---
name: python-reviewer
description: Revisiona codice Python per correttezza, leggibilità e test mancanti. Usalo dopo modifiche a file .py.
tools: Read, Grep, Glob
model: sonnet
---

Sei un revisore di codice Python senior. Per ogni file modificato:

1. Segnala bug di correttezza con file e riga.
2. Segnala funzioni senza test in tests/.
3. Proponi al massimo tre miglioramenti di leggibilità.

Non modificare file: restituisci solo il rapporto.
```

È lo stesso formato degli agent del capitolo 10: un file Markdown con il frontmatter (nome, descrizione, tool, modello) e il system prompt nel corpo. La scelta che conta è nella riga `tools`. L'agent non ha `Edit`, `Write` né `Bash`: anche se il modello decidesse di correggere un bug, non avrebbe il tool per farlo. L'ultima riga del prompt lo dice a parole, la lista dei tool lo garantisce.

C'è un dettaglio da sapere. Nelle build native per macOS, Linux e WSL i tool `Grep` e `Glob` di solito non ci sono: Claude cerca nei file attraverso `Bash`. Su queste installazioni l'agent lavora di fatto con il solo `Read`, che basta per revisionare i file che gli nomini e i test corrispondenti. Non aggiungere `Bash` solo per dargli la ricerca: con una shell l'agent può anche scrivere, e la garanzia di sola lettura sparisce.

La description segue la regola che hai visto per le skill: dice quando usarlo ("dopo modifiche a file `.py`"), così Claude può delegargli la revisione anche senza che tu lo nomini.

### Gli hook

L'hook di formattazione del capitolo 12 è fatto di due pezzi: lo script e la sua registrazione nel `settings.json` del progetto. Nel plugin lo script va in `hooks/scripts/`:

```bash
cp ~/cc-advanced-lab/.claude/hooks/format-python.sh cc-lab-toolkit/hooks/scripts/
```

`cp` conserva il bit di esecuzione dell'originale. Se invece scrivi lo script da zero, ricordati `chmod +x`, altrimenti l'hook fallisce senza fare niente di visibile. Per comodità, lo script è questo:

```bash
#!/bin/bash
# Formatta con ruff i file Python modificati da Claude
FILE_PATH=$(jq -r '.tool_input.file_path // empty')

if [[ "$FILE_PATH" == *.py ]]; then
  ruff format "$FILE_PATH" >/dev/null 2>&1
fi

exit 0
```

La registrazione va in `cc-lab-toolkit/hooks/hooks.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"${CLAUDE_PLUGIN_ROOT}\"/hooks/scripts/format-python.sh"
          }
        ]
      }
    ]
  }
}
```

Il formato è identico a quello della chiave `hooks` di `settings.json`: stesso evento `PostToolUse`, stesso matcher `Edit|Write`, stesso tipo `command`. L'unica differenza è il percorso dello script. Nel capitolo 12 usavi `$CLAUDE_PROJECT_DIR`, che punta alla cartella principale del progetto. Qui lo script non sta nel progetto, sta nel plugin, quindi usi `${CLAUDE_PLUGIN_ROOT}`, che punta alla cartella in cui il plugin è installato. Le virgolette escape intorno alla variabile servono per i percorsi con spazi. Un percorso assoluto come `/Users/tuonome/cc-plugins/...` funzionerebbe solo sul tuo computer e si romperebbe al primo collega che installa il plugin.

::: {.callout .callout-warning}
[Attenzione]{.callout-title}

Se nel `.claude/settings.json` di `cc-advanced-lab` hai ancora l'hook del capitolo 12, quando carichi il plugin `ruff` gira due volte dopo ogni modifica: una per l'hook del progetto, una per quello del plugin. Non fa danni, ma è il tipo di doppione che poi nessuno ricorda di aver lasciato. Una volta che l'hook vive nel plugin, toglilo dal `settings.json` del progetto.
:::

### L'albero finale

```text
cc-lab-toolkit/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── report-pdf/SKILL.md
├── agents/
│   └── python-reviewer.md
└── hooks/
    ├── hooks.json
    └── scripts/format-python.sh
```

Per controllare di non aver dimenticato niente:

```bash
find cc-lab-toolkit -type f | sort
```

Devi vedere cinque file: il manifest, la skill, l'agent, `hooks.json` e lo script. Se volessi aggiungere un server MCP, per esempio il DBHub del capitolo 13, metteresti un `.mcp.json` accanto a `skills/` e `agents/`, con lo stesso formato del `.mcp.json` di progetto.

## 14.4 Provare il plugin senza installarlo

### Validare

Prima di caricarlo, fai controllare la struttura:

```bash
claude plugin validate ./cc-lab-toolkit
```

`claude plugin validate` legge il manifest e il frontmatter di skill e agent e ti dice cosa non va: un JSON malformato, un campo `name` mancante, un frontmatter rotto. Costa niente e ti risparmia di scoprire il problema più tardi, quando il plugin semplicemente non compare. Con `--strict` il controllo è più severo, con `--json` l'esito esce in un formato che puoi leggere da uno script o in CI.

### Caricarlo per una sessione

Poi entra nel progetto di laboratorio e avvia Claude Code con il flag `--plugin-dir`:

```bash
cd ~/cc-advanced-lab
claude --plugin-dir ~/cc-plugins/cc-lab-toolkit
```

`--plugin-dir` carica il plugin solo per questa sessione, senza installarlo: niente scope, niente marketplace, niente da disinstallare dopo. È il modo giusto per lavorarci mentre lo scrivi. Quando chiudi la sessione il plugin sparisce.

Prova la skill con il prefisso:

```text
/cc-lab-toolkit:report-pdf data/vendite.csv
```

Sul CSV del laboratorio, tre mesi di vendite, la risposta è la tabella che la skill chiede: 3 righe, totale 358, minimo 95, massimo 143, media 119,33. Il totale è lo stesso che verifica `tests/test_report.py`, quindi hai anche un controllo incrociato.

Poi l'agent:

```text
usa l'agente cc-lab-toolkit:python-reviewer su src/report.py
```

Anche l'agent porta il prefisso del plugin. Claude lo lancia come subagent, che nelle sessioni interattive gira in background: l'agent legge il file e i test nel suo contesto separato e ti restituisce solo il rapporto, come hai visto nel capitolo 10. Ci mette un po' di più della skill, perché parte un contesto nuovo che deve rileggere tutto.

Per l'hook non serve un prompt dedicato: chiedi a Claude una modifica qualsiasi a un file `.py` e guarda il file dopo. Se è formattato, l'hook del plugin ha funzionato. `/hooks` ti mostra anche l'hook registrato sotto `PostToolUse`.

<!-- VERIFY: che /hooks mostri gli hook dei plugin insieme a quelli di settings.json e come li etichetta -->

### Modificare senza riavviare

Se correggi la description della skill o il prompt dell'agent a sessione aperta, non serve uscire e rientrare:

```text
/reload-plugins
```

ricarica i file del plugin nella sessione corrente. Se l'agent sembra ancora quello vecchio, ricordati che un subagent già lanciato ha il suo prompt: rilancialo.

### L'errore più comune

Il problema che vedo più spesso è un plugin che si carica senza errori ma non ha skill né agent. Quasi sempre è perché i componenti sono finiti dentro `.claude-plugin/`:

```text
cc-lab-toolkit/
└── .claude-plugin/
    ├── plugin.json
    ├── skills/          <- qui non vengono caricati
    └── agents/
```

`.claude-plugin/` contiene solo il manifest. Skill, agent e hook vanno nella radice del plugin, accanto a `.claude-plugin/`, come nell'albero del paragrafo precedente. Il nome della cartella invita all'errore, perché sembra il posto dove mettere "le cose del plugin". Se `/cc-lab-toolkit:report-pdf` non compare nel menu dei comandi, controlla questo per primo, poi rilancia `claude plugin validate`.

## 14.5 Un marketplace per il team

Con `--plugin-dir` il plugin lo usi tu. Per darlo al team ti serve un **marketplace**. Il nome fa pensare a un negozio, ma è solo un repository con un file `.claude-plugin/marketplace.json` che elenca i plugin e dice dove trovarli.

Trasforma `~/cc-plugins` in un marketplace. Crea `~/cc-plugins/.claude-plugin/marketplace.json`:

```json
{
  "name": "cc-corso",
  "owner": {
    "name": "Hidran Arias"
  },
  "plugins": [
    {
      "name": "cc-lab-toolkit",
      "source": "./cc-lab-toolkit",
      "description": "Report da CSV, revisione e formattazione per progetti Python"
    }
  ]
}
```

Attenzione a non confonderti: il `.claude-plugin/` del marketplace sta nella radice di `~/cc-plugins` e contiene `marketplace.json`; quello del plugin sta in `~/cc-plugins/cc-lab-toolkit` e contiene `plugin.json`. La struttura completa del repository diventa:

```text
cc-plugins/
├── .claude-plugin/
│   └── marketplace.json
└── cc-lab-toolkit/
    ├── .claude-plugin/
    │   └── plugin.json
    ├── skills/
    ├── agents/
    └── hooks/
```

Il `name` del marketplace è quello che userai dopo la chiocciola. `source` è il percorso del plugin, relativo alla cartella del marketplace. Quando avrai un secondo plugin, aggiungi un altro oggetto all'array `plugins` e una cartella accanto a `cc-lab-toolkit`.

### Aggiungere il marketplace e installare

Avvia Claude Code normalmente, senza `--plugin-dir`, e registra il marketplace:

```text
/plugin marketplace add ~/cc-plugins
```

Il comando accetta una cartella locale, come qui, oppure un repository GitHub nel formato `utente/repository`. Lo fai una volta sola. Poi installi il plugin per nome, chiocciola, nome del marketplace:

```text
/plugin install cc-lab-toolkit@cc-corso
```

Claude Code ti chiede lo scope, come per `plugin-dev`. Da qui in avanti `/cc-lab-toolkit:report-pdf` è disponibile in ogni sessione dello scope che hai scelto, senza flag.

### Condividerlo davvero

La cartella locale serve per provare il marketplace su te stesso. Per il team pubblichi `cc-plugins` su GitHub, come qualsiasi altro repository, e i colleghi lo aggiungono con:

```text
/plugin marketplace add <utente>/cc-plugins
/plugin install cc-lab-toolkit@cc-corso
```

Se il plugin serve a un progetto preciso, installalo con scope project in quel repository: la scelta finisce nel `.claude/settings.json` condiviso e chi clona il progetto si ritrova lo stesso plugin.

Gli aggiornamenti passano dalla versione nel manifest. Correggi la skill, porti `version` in `plugin.json` da `1.0.0` a `1.1.0`, committi e pushi: chi ha installato il plugin riceve la nuova versione. Se modifichi i file e dimentichi di cambiare il numero, per gli altri non è cambiato niente. Io tratto il bump di versione come parte della modifica, nello stesso commit.

Per prendere subito la nuova versione senza aspettare, un collega aggiorna il catalogo del marketplace e poi il plugin:

```bash
claude plugin marketplace update cc-corso
claude plugin update cc-lab-toolkit@cc-corso
```

<!-- VERIFY: quando arriva da solo l'aggiornamento ai colleghi (avvio di sessione o solo con update) e forma esatta dell'argomento di claude plugin update -->

Per ripulire dopo le prove, dal terminale:

```bash
claude plugin uninstall cc-lab-toolkit@cc-corso
claude plugin marketplace remove cc-corso
```

## 14.6 Un plugin solo per te

Non tutto merita un marketplace. Se vuoi un plugin sempre attivo solo per te, in tutti i tuoi progetti, senza pubblicare niente, c'è:

```bash
claude plugin init miei-attrezzi
```

`claude plugin init` (alias `claude plugin new`) crea lo scaffolding del plugin in `~/.claude/skills/miei-attrezzi/`, cioè nella cartella delle tue skill personali, e da lì lo carica in ogni sessione con il nome `miei-attrezzi@skills-dir`. Il suffisso al posto del marketplace ti ricorda da dove arriva. È il posto giusto per le piccole abitudini che non interessano al team: la skill che riformatta le note delle riunioni, l'agent che ti spiega uno stack trace come piace a te.

La regola che uso per scegliere: se lo vuole anche un collega, va nel marketplace del team; se lo voglio solo io ma in ogni progetto, `claude plugin init`; se serve solo in un repository, resta in `.claude/` di quel repository come nei capitoli 9-12.

Per completezza: dalla v2.1.287 esistono anche le Claude Mods, moduli di hook scritti in JavaScript: sono un meccanismo diverso dai plugin e qui non le tratto.

## 14.7 Misurare il plugin con claude plugin eval

Hai un plugin che funziona. La domanda successiva è se aiuta davvero. Il test che hai fatto nel paragrafo 14.4 dice che la skill parte quando la chiami per nome; non dice se Claude la usa quando un utente chiede "fammi un riepilogo delle vendite" senza sapere che la skill esiste, né se il risultato è migliore di quello che Claude avrebbe dato senza plugin.

`claude plugin eval` risponde a questa domanda. Ogni caso di test è un prompt realistico più uno o più **grader**, cioè controlli che dicono se il risultato è buono. Un grader può essere un'espressione regolare sulla risposta, la verifica che una certa skill sia stata usata, oppure un criterio valutato da un secondo modello ("la risposta contiene una tabella con totale e media corretti").

### Generare i casi con eval init

I casi non li scrivi a mano. Dalla cartella del plugin:

```bash
cd ~/cc-plugins/cc-lab-toolkit
claude plugin eval init
```

Per prima cosa ti chiede se ti fidi della cartella del plugin: è la tua, rispondi di sì. Poi parte un'intervista condotta da Claude. Ti chiede cosa deve fare la skill e quali richieste non devono attivarla. Alla prima ho risposto così:

```text
La skill report-pdf produce un report sintetico da un file CSV di vendite: righe, totale, minimo, massimo e media.
```

e alla seconda:

```text
Non deve attivarsi per richieste generiche sul codice Python, né per file che non sono CSV.
```

La seconda risposta è quella che si tende a saltare, ed è la più utile. Produce i casi negativi, quelli che verificano che la skill non scatti quando non deve. Una skill con una description troppo larga passa tutti i casi positivi e intanto si attiva anche su richieste che non c'entrano; senza casi negativi non te ne accorgi.

L'intervista propone i casi e chiede conferma a ogni passo. Per la prima prova tienili pochi: io ho chiesto due casi, che bastano per vedere come funziona. Quando conferma di averli scritti, esci con `/exit`.

Nella radice del plugin trovi una cartella `evals/` con una sottocartella per caso: dentro ci sono il prompt e i grader che lo valutano. Aprili. Il prompt deve somigliare a una richiesta vera, non alla description della skill riscritta; se l'intervista ha prodotto un prompt che contiene già le parole chiave della description, il caso misura poco e conviene riscriverlo.

```bash
find evals -type f | sort
```

<!-- VERIFY: nomi esatti dei file generati da eval init (evals/<caso>/prompt.md e graders/*.md oppure case.yaml) -->

### Lanciare la suite

Sempre dalla cartella del plugin:

```bash
claude plugin eval .
```

Ogni caso gira tre volte con il plugin e tre volte senza. Con due casi sono dodici esecuzioni, più le chiamate dei grader che usano un modello. Nella mia prova, eseguendo i casi in parallelo, la suite ha impiegato un paio di minuti.

Per la registrazione del corso ho lanciato il comando con tre opzioni in più:

```bash
claude plugin eval . --trust-plugin --no-publish -j 4
```

`--trust-plugin` evita la richiesta di fiducia sulla cartella alla prima esecuzione, `-j 4` esegue quattro esecuzioni in parallelo e accorcia l'attesa. `--no-publish` è quella da non dimenticare: senza, il report viene pubblicato su claude.ai. Per un plugin interno del team di solito non è quello che vuoi.

<!-- VERIFY: flag --trust-plugin, --no-publish e -j di claude plugin eval, e che il comportamento predefinito pubblichi il report su claude.ai -->

### Leggere la tabella

Alla fine la suite stampa una tabella con una riga per caso e quattro colonne:

| Colonna | Cosa dice |
|---|---|
| `WITH` | il risultato dei grader nelle esecuzioni con il plugin |
| `W/OUT` | il risultato nelle esecuzioni senza plugin |
| `Δ` | la differenza tra le due: quanto il plugin ha migliorato il risultato |
| `COST` | quanto è costato il caso |

<!-- TODO screenshot: tabella finale di claude plugin eval con le colonne WITH, W/OUT, Δ, COST -->

La colonna da guardare è `Δ`. Un delta alto dice che il plugin fa la differenza su quel caso. Un delta vicino a zero ha due spiegazioni. La prima è che Claude se la cava bene anche senza plugin: per un CSV di tre righe è plausibile, e vuol dire che quella skill pesa sul contesto senza restituire molto. La seconda, molto più frequente, è che la skill non è stata attivata. In quel caso il problema è quasi sempre la description, che non corrisponde al modo in cui l'utente formula la richiesta. È la lezione del capitolo 9 sulla description come trigger, con la differenza che adesso hai un numero che te lo dice. Correggi la description, rilancia, guarda se il delta sale.

Per i dettagli di ogni esecuzione, compresi i testi delle risposte e i verdetti dei grader, apri il `report.html` che la suite scrive nella cartella dei risultati.

I risultati non vanno nel repository. Aggiungi la cartella al `.gitignore` del plugin:

```bash
echo 'evals/results/' >> .gitignore
```

I casi in `evals/` invece li committi: sono i test del plugin, e chi lo modifica dopo di te li rilancia per controllare di non aver peggiorato niente.

### Iterare senza bruciare il piano

Ogni esecuzione è una vera chiamata al modello e consuma il tuo piano. Una suite completa con dieci casi sono sessanta esecuzioni: lanciarla a ogni ritocco della description è un modo rapido di finire i limiti della settimana.

Mentre iteri, restringi:

```bash
claude plugin eval . --case <nome-caso> --runs 1 --ablation none
```

`--case` esegue un solo caso, `--runs 1` una sola esecuzione invece di tre, `--ablation none` salta le esecuzioni di confronto senza plugin. Ti resta una sola chiamata, sufficiente per capire se la skill adesso scatta. Quando sei soddisfatto, confermi con la suite completa e le tre esecuzioni standard: una sola esecuzione non basta per fidarsi di un risultato, perché lo stesso prompt può dare risposte diverse.

<!-- VERIFY: significato esatto di --ablation none (salta le esecuzioni senza plugin) -->

::: {.callout .callout-tip}
[Suggerimento]{.callout-title}

Tieni nella suite almeno un caso negativo per ogni skill. Quando allarghi una description per far scattare la skill su un caso positivo che falliva, il caso negativo ti dice subito se adesso scatta anche dove non deve.
:::

## Riepilogo

- Un plugin è una cartella con il manifest in `.claude-plugin/plugin.json` e i componenti (`skills/`, `agents/`, `hooks/hooks.json`, `.mcp.json`) nella radice. Il campo `name` è obbligatorio e diventa il prefisso: `/cc-lab-toolkit:report-pdf`.
- Prima di installare un plugin guardi il costo in contesto nel gestore `/plugin` e leggi hook e server MCP che porta con sé: girano con i tuoi permessi.
- Negli hook di un plugin il percorso dello script usa `${CLAUDE_PLUGIN_ROOT}`, non `$CLAUDE_PROJECT_DIR` né un percorso assoluto.
- `claude plugin validate` controlla la struttura, `claude --plugin-dir` carica il plugin per una sessione, `/reload-plugins` ricarica le modifiche. Se mancano skill e agent, controlla che non siano finiti dentro `.claude-plugin/`.
- Un marketplace è un repository con `.claude-plugin/marketplace.json`: lo aggiungi con `/plugin marketplace add`, installi con `/plugin install <plugin>@<marketplace>` e distribuisci gli aggiornamenti cambiando `version` nel manifest.
- `claude plugin eval` confronta i risultati con e senza plugin: guarda la colonna `Δ`, itera con `--case`, `--runs 1` e `--ablation none`, e metti `evals/results/` nel `.gitignore`.

## Esercizio

Aggiungi a `cc-lab-toolkit` una seconda skill, `csv-check`, che controlla un file CSV e segnala righe vuote, colonne mancanti e valori non numerici nella colonna delle vendite, senza modificare il file. Porta la versione del manifest a `1.1.0`, verifica la struttura con `claude plugin validate ./cc-lab-toolkit` e provala in `cc-advanced-lab` con `--plugin-dir`. Poi lancia `claude plugin eval init` per la nuova skill, chiedendo almeno un caso positivo e uno negativo (per esempio una domanda sul codice in `src/report.py`, che non deve attivarla).

L'esercizio è finito quando `/cc-lab-toolkit:csv-check data/vendite.csv` risponde che il file è pulito, la suite completa `claude plugin eval .` mostra un `Δ` positivo sul caso positivo e il caso negativo passa, cioè la skill non scatta.
