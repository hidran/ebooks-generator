# Capitolo 1. Cos'è Claude Code

## Cosa imparerai

Alla fine di questo capitolo hai Claude Code installato e collegato al tuo account, conosci la dozzina di comandi e scorciatoie che userai ogni giorno e hai fatto scrivere e lanciare a Claude un primo programma, guardando ogni passo. In più sai com'è organizzato il resto del libro e da dove conviene partire.

**Prerequisiti**: un computer con macOS 13 o successivo, Windows 10 (1809) o successivo, oppure Linux (Ubuntu 20.04+, Debian 10+), con almeno 4 GB di RAM. Un piano Claude a pagamento (Pro, Max, Team o Enterprise) oppure un account Claude Console. Python 3 per l'esempio della sezione 1.5.

Claude Code è il programma con cui Anthropic mette Claude dentro il tuo progetto. Lo apri in una cartella, gli scrivi cosa vuoi in italiano, e lui legge i file, li modifica, lancia comandi e ti racconta cosa ha fatto. Questo libro parte da qui e arriva, nella Parte VI, a un'applicazione full-stack deployata su AWS. In mezzo c'è un metodo di lavoro che si impara un pezzo alla volta, e il primo pezzo è avere lo strumento installato bene e sapere dove mettere le mani.

## 1.1 Cos'è Claude Code

Claude Code è un agente per lo sviluppo software. È nato come programma da riga di comando e il terminale resta il posto dove dà il meglio, ma oggi lo stesso agente gira anche dentro VS Code e JetBrains, nell'app desktop di Claude e nel browser (ne parlo alla fine della sezione 1.3). In tutti i casi lavora sui file veri del tuo progetto, non su una copia incollata in una chat.

Un agente è un modello linguistico a cui l'harness, cioè il programma che gli sta intorno, mette a disposizione degli strumenti: leggere un file, modificarlo, eseguire un comando. Il modello decide quale strumento gli serve, Claude Code lo esegue e gli rimanda il risultato, e il giro si ripete finché il lavoro è finito o finché serve una tua decisione. Il capitolo 2 smonta questo meccanismo pezzo per pezzo: per ora basta sapere che il modello chiede e Claude Code esegue, sotto il tuo controllo.

### Rispetto agli altri strumenti

Con una chat nel browser, che sia claude.ai o un'altra, il lavoro di contorno lo fai tu. Scegli quali file incollare, copi la risposta nell'editor, lanci i test, torni in chat con l'errore. La qualità della risposta dipende da quanto bene hai scelto cosa far vedere al modello.

Gli assistenti integrati nell'editor, come GitHub Copilot o Cursor, sono nati come completamento del codice mentre scrivi e oggi hanno anche loro modalità agentiche. Sono strumenti seri e molti sviluppatori li usano accanto a Claude Code. La differenza pratica sta nel punto di partenza: Claude Code nasce nel terminale, quindi gira ovunque tu possa aprire una shell (il tuo portatile, un server via SSH, un container, una pipeline di CI) e si può lanciare da uno script senza nessuna interfaccia grafica.

Non c'è uno strumento migliore in assoluto. Claude Code rende di più quando il lavoro è a livello di progetto: un refactoring che tocca dieci file, una feature nuova con i suoi test, un codebase che non conosci e che devi capire in fretta. Per completare una riga mentre scrivi, l'autocompletamento dell'editor resta più comodo.

### Cosa può fare in concreto

Legge qualunque file di testo del progetto, dal codice alla configurazione, e lo modifica. Esegue comandi nel terminale, come `npm install`, `pytest`, `git status` o `docker build`, e ne legge l'output, compresi gli errori. Esplora le cartelle per capire com'è fatto il progetto prima di toccarlo. Lavora con Git: legge lo storico, crea branch, committa, prepara pull request. Con i server MCP (Model Context Protocol) si collega a servizi esterni come GitHub, un database o il tuo calendario: è l'argomento del capitolo 13.

Tutto passa da una conversazione. Scrivi cosa vuoi ottenere, Claude propone e agisce, e per le azioni delicate ti chiede il permesso o le blocca. Quali azioni passano da te lo decide la modalità di permesso (sezione 1.3).

## 1.2 Installazione

L'installazione consigliata è l'installer nativo: un binario unico, senza Node.js, senza diritti di amministratore, che si aggiorna da solo in background.

### L'installer nativo

Su macOS, Linux e WSL:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Su Windows, da PowerShell:

```powershell
irm https://claude.ai/install.ps1 | iex
```

Oppure dal Prompt dei comandi (CMD):

```batch
curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
```

Se sul Mac usi già Homebrew, o su Windows preferisci WinGet, ci sono anche queste strade:

```bash
brew install --cask claude-code
```

```powershell
winget install Anthropic.ClaudeCode
```

Con Homebrew e WinGet gli aggiornamenti non sono automatici: li lanci tu con `brew upgrade claude-code` o `winget upgrade Anthropic.ClaudeCode`. Il cask `claude-code` di Homebrew segue il canale stabile; esiste anche `claude-code@latest` per il canale delle ultime release. Per le distribuzioni Linux ci sono anche repository apt, dnf e apk firmati, che si aggiornano con il gestore di pacchetti del sistema.

### Se installi con npm

La prima edizione di questo libro partiva da `npm install -g`. Il pacchetto npm esiste ancora ed è documentato come opzione avanzata, ma oggi richiede Node.js 22 o successivo e installa lo stesso binario nativo dell'installer: il comando `claude` non usa Node per girare.

```bash
npm install -g @anthropic-ai/claude-code
```

Tre cose da sapere se scegli questa strada. Per aggiornare usa `npm install -g @anthropic-ai/claude-code@latest`, non `npm update -g`. Non usare mai `sudo npm install -g`: crea file di proprietà di root che poi bloccano gli aggiornamenti normali. Se npm risponde con un errore `EACCES` sulla cartella dei pacchetti globali, la soluzione più semplice è lasciar perdere npm e usare l'installer nativo. Con un Node più vecchio della 22 npm mostra solo un avviso `EBADENGINE` e prosegue: controlla `node --version` prima.

### Verifica e aggiornamenti

Apri un terminale nuovo, così la shell rilegge il `PATH`, e controlla:

```bash
claude --version
claude doctor
```

Il primo comando stampa la versione, qualcosa come `2.1.302 (Claude Code)`. Il secondo controlla l'installazione e i file di impostazioni senza avviare una sessione, e ti dice cosa non va e come sistemarlo. È in sola lettura: non modifica niente.

L'installazione nativa si aggiorna da sola. Claude Code controlla all'avvio e periodicamente, e la versione nuova entra in funzione al riavvio successivo. Se vuoi aggiornare subito:

```bash
claude update
```

Puoi scegliere tra due canali di aggiornamento: `latest`, il default, che riceve ogni release, e `stable`, che di solito è indietro di circa una settimana e salta le release con regressioni gravi. Si cambia da `/config`, alla voce Auto-update channel, oppure all'installazione con `curl -fsSL https://claude.ai/install.sh | bash -s stable`. Se usi Claude Code su progetti di lavoro e non ti interessa provare le novità il giorno stesso, `stable` è una scelta sensata.

### Windows

Su Windows l'installer nativo funziona direttamente da PowerShell o da CMD, senza WSL.

Git for Windows non è più obbligatorio. Se è installato, Claude Code usa Git Bash per eseguire i comandi; se manca, usa PowerShell. Conviene installarlo lo stesso, perché Git ti serve comunque e alcune funzioni di Claude Code, come il tool `Bash` e il Monitor per seguire i log, hanno bisogno di Git Bash. Se Claude Code non trova Git Bash, indica il percorso in `%USERPROFILE%\.claude\settings.json`:

```json
{
  "env": {
    "CLAUDE_CODE_GIT_BASH_PATH": "C:\\Program Files\\Git\\bin\\bash.exe"
  }
}
```

C'è un motivo per scegliere comunque WSL 2. Il sandbox dei comandi, che limita file e rete di quello che Claude esegue nel terminale (capitoli 2 e 11), non funziona su Windows nativo e funziona su WSL 2. Se lavori con toolchain Linux o vuoi il sandbox, installa Claude Code dentro WSL 2 con il comando per Linux, quello con `install.sh`. WSL 1 non è supportato.

### Se qualcosa non va

Il caso più comune è `command not found` subito dopo l'installazione. Quasi sempre basta chiudere il terminale e aprirne uno nuovo. Se non basta, controlla che la cartella dove l'installer mette il binario sia nel `PATH`. Su macOS e Linux è `~/.local/bin`:

<!-- VERIFY: percorso del binario nativo su macOS/Linux (~/.local/bin) e su Windows; non è in FACTS.md. -->

```bash
echo $PATH | tr ':' '\n' | grep local
```

Se la cartella non compare, aggiungi `export PATH="$HOME/.local/bin:$PATH"` al tuo `~/.zshrc` o `~/.bashrc` e riapri il terminale.

Se hai installato Claude Code in passato con npm e ora usi l'installer nativo, puoi ritrovarti con due `claude` diversi. `which -a claude` li elenca tutti: quello che conta è il primo. Disinstalla la versione npm con `npm uninstall -g @anthropic-ai/claude-code` per evitare sorprese.

Su Windows, due errori dicono solo che hai incollato il comando nella shell sbagliata. `The token '&&' is not a valid statement separator` significa che sei in PowerShell e hai usato il comando per CMD; `'irm' is not recognized` è il caso opposto.

Per tutto il resto parti da `claude doctor`. Dentro una sessione esiste anche `/doctor`, che fa un controllo più ampio e può applicare le correzioni da solo.

### Account e primo accesso

Claude Code non è incluso nel piano gratuito di claude.ai. Funziona con un abbonamento Pro o Max, con i piani Team ed Enterprise, con un account Claude Console (che paga a consumo, per token) e con i provider cloud: Amazon Bedrock, Google Cloud (Agent Platform, il vecchio Vertex AI) e Microsoft Foundry.

<!-- VERIFY: nome commerciale "Microsoft Foundry" (FACTS.md cita solo CLAUDE_CODE_USE_FOUNDRY). -->

Al primo avvio lanci semplicemente:

```bash
claude
```

Claude Code ti fa scegliere il tema dei colori, poi apre il browser per il login. Scegli il tipo di account (abbonamento Claude, Console oppure piattaforma di terze parti), autorizza l'accesso e torna al terminale. Se il browser non si apre da solo, copia l'URL che compare nel terminale, completa il login a mano e incolla il codice che ricevi. Con un account Console non serve più creare una API key: il login dal browser basta.

Gli altri comandi che riguardano l'account sono `/login`, per accedere o cambiare account, e `/logout`, che oltre a scollegarti azzera le impostazioni del primo avvio. Dalla shell ci sono gli equivalenti `claude auth login`, `claude auth logout` e `claude auth status`.

::: {.callout .callout-warning}
[Attenzione]{.callout-title}

Se nella tua shell è definita la variabile `ANTHROPIC_API_KEY` e la approvi quando Claude Code te lo chiede, quella chiave vince sull'abbonamento: paghi a consumo sulla Console anche se hai un piano Max. Succede spesso a chi esporta la chiave nel `.zshrc` per altri progetti. In modalità `claude -p` la chiave viene usata sempre, senza chiedere. Controlla con `/status` quale metodo di autenticazione è attivo; se non è quello che vuoi, esegui `unset ANTHROPIC_API_KEY` e riavvia Claude Code.
:::

### La prima sessione in una cartella

Claude Code lavora nella cartella da cui lo lanci. Prima di avviarlo, spostati nel progetto:

```bash
mkdir mio-progetto
cd mio-progetto
claude
```

La prima volta che lo apri in una cartella, ti chiede se ti fidi dei file che contiene. Rispondi di sì solo per cartelle che conosci: un progetto scaricato da internet può contenere file di configurazione che Claude Code legge e applica. La prima sessione in auto mode mostra anche un avviso che spiega la modalità (ne parlo tra poco).

Poi compare la schermata di benvenuto, con il modello attivo, il tuo account e la cartella corrente, e sotto il prompt dove scrivere. Per uscire usa `/exit` oppure `Ctrl+C` due volte.

<!-- TODO screenshot: fig-01, schermata di benvenuto della versione corrente (modello Opus 5.5, cartella di prova). Senza email, nome dell'organizzazione o percorsi personali. -->

## 1.3 Comandi base e modalità

Tutto quello che non è un prompt parte con una barra. Scrivi `/` e Claude Code mostra l'elenco dei comandi, che si filtra mentre digiti. Nell'elenco compaiono anche le skill, tue o dei plugin installati, perché si richiamano allo stesso modo. Di comandi ce ne sono decine; quelli che seguono sono quelli che userai dal primo giorno.

`/help` mostra l'aiuto con le scorciatoie principali e l'elenco dei comandi disponibili. La prima volta dedicagli un paio di minuti.

<!-- TODO screenshot: fig-02, scheda general di /help nella versione corrente. La vecchia cattura (v2.1.78, Opus 4.6) mostrava "& for background", che non va presentato. -->

### La conversazione e il contesto

Tutto quello che Claude vede in una sessione sta nella finestra di contesto: le istruzioni di sistema, i file di progetto come `CLAUDE.md`, i file che ha letto, i comandi che ha lanciato e i tuoi messaggi. Con i modelli attuali la finestra arriva a un milione di token, ma più si riempie, più la sessione costa e più aumenta il rischio che Claude perda i dettagli dell'inizio. La regola pratica è un task, una sessione. Con `/context` vedi quanto è piena e cosa la occupa; il capitolo 15 è dedicato a questo.

Quattro comandi gestiscono la conversazione:

```text
/clear                  riparte da zero con il contesto vuoto
/compact [istruzioni]   riassume la conversazione e libera spazio
/resume                 riprende una sessione precedente
/rewind                 torna a un punto precedente della sessione
```

`/clear` è quello da usare quando cambi argomento. La conversazione vecchia non sparisce: la ritrovi in `/resume`, e se scrivi `/clear nome` le dai un'etichetta per riconoscerla. `/compact` invece resta nella stessa sessione e sostituisce i messaggi vecchi con un riassunto; puoi dirgli cosa conservare, per esempio `/compact tieni le decisioni sul formato del CSV e la lista dei file modificati`. `/resume` apre l'elenco delle sessioni passate, oppure riprende direttamente quella che indichi per nome o ID. `/rewind` riporta indietro il codice, la conversazione o entrambi a un checkpoint: lo apri anche premendo due volte `Esc` sul prompt vuoto, ed è il primo comando da ricordare quando Claude imbocca una strada sbagliata.

### Stato, consumi e impostazioni

`/status` apre le impostazioni sulla scheda Status: versione, modello, account e metodo di autenticazione, connessione. È il comando che ti serve quando qualcosa non torna, a cominciare dal caso dell'API key visto sopra.

`/usage` mostra quanto stai consumando. Con un account Console vedi il costo della sessione; con un abbonamento vedi i limiti del piano, quanto ne hai usato e cosa li sta consumando, diviso per skill, subagent, plugin e server MCP. `/cost`, il comando della prima edizione, funziona ancora: oggi è un alias di `/usage`, come `/stats`.

<!-- TODO screenshot: fig-04, output di /usage su un abbonamento (sostituisce la vecchia cattura di /cost). -->

`/model` mostra i modelli disponibili per il tuo piano e quello attivo, e ti permette di cambiarlo. La scelta diventa il default per le sessioni successive; se premi `s` nel selettore vale solo per la sessione corrente, e con le frecce sinistra e destra regoli l'effort. Mentre scrivo il default è Claude Opus 5.5. Gli altri alias sono `sonnet`, più veloce e meno costoso, `haiku`, il più rapido per i lavori ripetitivi, e `fable`, il più capace, che non è mai il default. C'è anche `opusplan`, che usa Opus mentre pianifica e Sonnet mentre esegue. I nomi dei modelli cambiano ogni pochi mesi, quindi non fidarti di quelli stampati qui: controlla `/model`. Modello ed effort sono spiegati nel capitolo 2.

<!-- TODO screenshot: fig-03, selettore di /model nella versione corrente (sostituisce la vecchia cattura con Sonnet 4.6). -->

`/config` apre tutte le impostazioni: tema, canale di aggiornamento, modalità vim dell'editor (il vecchio comando `/vim` non esiste più), uso dell'API key e molto altro. Accetta anche la forma `/config chiave=valore`, per esempio `/config model=sonnet`.

`/init` analizza il progetto e scrive un primo `CLAUDE.md`, il file con le istruzioni che Claude legge a ogni sessione. Su un progetto vuoto non serve; su un progetto vero è una delle prime cose da fare, e il capitolo 7 spiega come rivedere quello che genera.

Infine `/btw` ti permette una domanda al volo, per esempio sul significato di un errore, senza che finisca nella conversazione principale.

### Scorciatoie da tastiera

| Tasto | Cosa fa |
| --- | --- |
| `!` all'inizio del prompt | Modalità shell: esegue il comando, aggiunge l'output alla conversazione e Claude lo commenta |
| `@` | Completa i percorsi dei file, per indicare a Claude un file preciso |
| `?` sul prompt vuoto | Mostra l'aiuto delle scorciatoie |
| `Esc` | Interrompe Claude mentre lavora, o chiude un menu |
| `Esc` due volte | Cancella il testo scritto; sul prompt vuoto apre `/rewind` |
| `Shift+Tab` | Cambia modalità di permesso (su alcuni setup Windows è `Alt+M`) |
| `Ctrl+O` | Mostra la trascrizione dettagliata, con ogni chiamata ai tool |
| `Ctrl+R` | Cerca nella cronologia dei prompt |
| `Ctrl+G` | Apre il prompt nel tuo editor esterno, comodo per i testi lunghi |
| `Ctrl+B` | Manda in background un comando o un agent in esecuzione |
| `Ctrl+T` | Mostra o nasconde la checklist dei passi di Claude |
| `Shift+Enter` | Va a capo senza inviare |
| `Ctrl+V` | Incolla un'immagine, per esempio uno screenshot di un errore |

<!-- VERIFY: Ctrl+V per incollare immagini (su Windows potrebbe essere Alt+V); non è in FACTS.md. -->

`Shift+Enter` funziona da subito in iTerm2, WezTerm, Ghostty, Kitty, Warp, Terminal di macOS e Windows Terminal. Negli altri terminali lancia `/terminal-setup`, oppure usa `\` seguito da Invio, che funziona ovunque. Con la freccia su scorri i prompt precedenti, come in una shell.

Se vieni dalla prima edizione: la scorciatoia `#` per aggiungere una riga alla memoria è stata rimossa. Per salvare un'istruzione chiedi a Claude di aggiungerla a `CLAUDE.md`, oppure usa `/memory` (capitolo 7).

### Interattivo e headless

Finora hai visto la modalità interattiva: scrivi, Claude risponde, la sessione resta aperta. Con il flag `-p` Claude Code esegue un solo prompt, stampa la risposta ed esce:

```bash
claude -p "analizza il file main.py e dimmi quante funzioni contiene"
```

È la modalità per gli script, per la CI e per i lavori pianificati, e accetta anche input da una pipe, come `git diff | claude -p "riassumi queste modifiche"`. In `-p` non c'è nessuno a cui chiedere conferma, quindi le azioni non preapprovate non partono: le autorizzi con `--allowedTools`, per esempio `--allowedTools "Bash(git diff *),Read"`. Negli script conviene aggiungere `--bare`, che salta hook, skill, plugin, server MCP e `CLAUDE.md` e rende il risultato prevedibile, e `--output-format json` quando l'output deve leggerlo un altro programma.

### Le modalità di permesso

La modalità di permesso decide quali azioni Claude può fare senza chiederti conferma, ed è scritta nella barra di stato sotto il prompt. Le sessioni interattive partono in auto mode, dove un classificatore approva le azioni coerenti con la tua richiesta e blocca quelle rischiose, e con `Shift+Tab` passi a Manual, che chiede conferma per quasi tutto, poi ad Accept edits e a Plan. Il capitolo 2 spiega come funzionano e il capitolo 11 come configurarle. Esiste anche il flag `--dangerously-skip-permissions`, che toglie ogni controllo: usalo solo dentro un container o una macchina virtuale usa e getta, mai sul tuo portatile.

### Oltre il terminale

In VS Code (e in Cursor) installa l'estensione `anthropic.claude-code`: è il modo consigliato di usare Claude Code nell'editor, con il piano da rivedere, i diff in linea e i riferimenti ai file con le righe. L'estensione contiene già la sua copia della CLI per il pannello di chat; se vuoi anche il comando `claude` nel terminale integrato, installa la CLI come visto sopra. Per IntelliJ, PyCharm, PhpStorm e gli altri IDE JetBrains c'è il plugin Claude Code [Beta], che invece non include la CLI: va installata prima. L'app desktop di Claude ha una scheda Code (macOS, Windows, Linux in beta), e `/desktop` ci sposta la sessione che hai aperto nel terminale. Infine le sessioni cloud su claude.ai/code girano sui server di Anthropic: le avvii dal browser o dal terminale con `claude --cloud "<task>"` e le riporti in locale con `claude --teleport`. Nel libro lavoriamo quasi sempre nel terminale, dove si vede meglio cosa succede.

### La cartella .claude

Claude Code tiene la sua configurazione in due posti. Nella home, `~/.claude/` contiene le impostazioni personali (`settings.json`), il tuo `CLAUDE.md` personale, le skill e gli agent validi per tutti i progetti, i plugin installati e, sotto `projects/`, le sessioni salvate e la memoria automatica. Nel progetto, `.claude/` contiene impostazioni ed estensioni condivise con il team tramite Git. Ci torniamo nelle parti III e IV.

<!-- VERIFY: elenco del contenuto di ~/.claude/ (plugins/ e sessioni in projects/ non sono in FACTS.md). -->

## 1.4 Un ambiente di lavoro comodo

Passerai molte ore a leggere diff e output di test nel terminale, e uno che gestisce bene scorrimento, ricerca e colori fa una differenza concreta. Niente di questa sezione è obbligatorio.

### Il terminale

Su macOS le scelte più comuni sono due. iTerm2 (iterm2.com) è gratuito e maturo: pannelli divisi, ricerca nella cronologia con le espressioni regolari, profili diversi per ambienti diversi. Warp (warp.dev), gratuito per uso personale, organizza ogni comando con il suo output in un blocco che puoi selezionare, copiare e ritrovare, e quando Claude produce output lunghi è comodo per tornare a una parte precisa senza perdere il filo.

Su Windows usa Windows Terminal, che è già installato su Windows 11 e si scarica gratis dal Microsoft Store su Windows 10. Ha schede, pannelli divisi e un profilo per ogni shell: PowerShell per l'installazione nativa, Ubuntu se lavori in WSL 2.

Su Linux il terminale della distribuzione, GNOME Terminal o Konsole, va benissimo. Se vuoi qualcosa di più veloce, Alacritty e Kitty sono buone alternative.

### Shell e prompt

Su macOS la shell di default è zsh dal 2019. Su Linux è spesso bash; se vuoi zsh, installala con il gestore di pacchetti (`sudo apt install zsh` su Ubuntu) e impostala con `chsh -s $(which zsh)`. oh-my-zsh (ohmyz.sh) aggiunge completamento avanzato e suggerimenti dalla cronologia; fish (fishshell.com) li ha già senza plugin.

Qualunque shell usi, installa Starship (starship.rs), un prompt che funziona con zsh, bash, fish e PowerShell. Mostra il branch Git e lo stato del repository, la versione di Node o il virtualenv Python attivi e il tempo di esecuzione dell'ultimo comando, utile per capire quanto ci mettono i comandi lanciati da Claude.

Su macOS:

```bash
brew install starship
```

Su Linux e WSL:

```bash
curl -sS https://starship.rs/install.sh | sh
```

Poi aggiungi in fondo al tuo `~/.zshrc`, e riavvia il terminale:

```bash
eval "$(starship init zsh)"
```

### Alias

Tre alias che uso ogni giorno, da mettere nel `.zshrc` o nel `.bashrc`:

```bash
alias c='claude'                                # avvio interattivo
alias cm='claude --permission-mode default'     # avvio in Manual
alias cq='claude -p'                            # una domanda al volo, headless
```

`cm` mi serve quando lavoro su un progetto che non conosco e voglio vedere ogni azione prima che parta. `cq` è per le domande veloci: `cq "che versione di Laravel usa questo progetto?"`. Nella prima edizione l'alias headless si chiamava `cp`: era un errore, perché nasconde il comando `cp` per copiare i file. Nella stessa lista c'era un alias per `--dangerously-skip-permissions`, che ho tolto per i motivi visti nella sezione 1.3.

### Dotfiles

Tieni la configurazione del terminale in un repository Git: una cartella `dotfiles/` con almeno `.zshrc`, `.gitconfig` e la configurazione di Starship, più un piccolo `install.sh` che crea i link simbolici nella home. Quando cambi portatile ti ritrovi l'ambiente completo in pochi minuti. La cartella `~/.claude/`, con le tue impostazioni e le tue skill personali, è un ottimo candidato da aggiungere.

## 1.5 Il tuo primo prompt guidato

Questo esempio richiede cinque minuti e una cartella vuota. Lo facciamo in Manual, la modalità che chiede conferma per ogni azione, perché la prima volta vale la pena vedere ogni passo prima che succeda.

```bash
mkdir -p ~/projects/hello-claude && cd ~/projects/hello-claude
claude --permission-mode default
```

Se Claude Code ti chiede se ti fidi della cartella, rispondi di sì. Nella barra di stato deve comparire `manual mode on`. Ora scrivi questo prompt:

```text
Crea un file hello.py che stampa un saluto sul terminale.
Aggiungi un argomento opzionale --name (default "mondo")
e stampa "Ciao <name>". Usa argparse per gestire l'argomento.
```

Claude guarda la cartella, vede che è vuota e decide che serve un solo file. Prima di scriverlo ti mostra il contenuto che vuole creare e ti chiede se procedere. Vedrai qualcosa di simile:

```python
#!/usr/bin/env python3
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="mondo")
    args = parser.parse_args()
    print(f"Ciao {args.name}")


if __name__ == "__main__":
    main()
```

Il codice esatto cambia un po' da un giro all'altro. Leggilo, poi conferma con la prima opzione. Il file compare nella cartella.

Adesso chiedi di provarlo:

```text
Esegui hello.py senza argomenti e poi con --name Hidran.
```

Claude propone il primo comando, `python3 hello.py` (o `python hello.py`, a seconda del sistema), e aspetta la tua conferma. Poi il secondo. L'output è:

```text
Ciao mondo
Ciao Hidran
```

Non hai aperto un editor e non hai copiato codice da nessuna parte.

::: {.callout .callout-tip}
[Suggerimento]{.callout-title}

Per i primi giorni leggi ogni proposta prima di confermare, anche quando è ovvia. È il modo più rapido per capire come ragiona Claude, quali file guarda e quali comandi preferisce. Quando ti sei fatto un'idea, torna all'auto mode con `Shift+Tab` e lascia al classificatore le conferme di routine.
:::

### Cosa è successo

Claude ha raccolto il contesto (la cartella era vuota), ha agito (ha scritto il file) e ha verificato (ha lanciato il programma e letto l'output). Ogni azione è passata da te prima di partire, perché eri in Manual. Questo giro di contesto, azione e verifica è il loop agentico, e lo ritroverai identico sulla Photogallery, con un progetto Laravel e React al posto di un file. Nel capitolo 2 lo guardi dall'interno con `Ctrl+O`.

Puoi cancellare la cartella con `rm -rf ~/projects/hello-claude`, ma ti conviene tenerla: la usi nell'esercizio di fine capitolo, ed è un posto sicuro dove provare i comandi dei prossimi capitoli senza rischiare codice che conta.

::: {.callout .callout-prompt}
[Prompt riusabile]{.callout-title}

Il primo prompt che scrivo su un progetto che non conosco, prima di chiedere qualunque modifica:

```text
Leggi i file nel progetto e dimmi:
1. Quale stack tecnologico vedi
2. Quale parte sembra più recente e quale più vecchia
3. Quale file è il punto di ingresso (entry point)
4. Cosa NON capisci subito guardando i nomi delle cartelle
```

Funziona su qualunque codebase. La quarta domanda è la più utile: ti dice dove Claude farà fatica, e quindi cosa dovrai spiegargli o mettere in `CLAUDE.md`.
:::

## 1.6 La mappa del libro

Il libro è diviso in sei parti. Ognuna usa quello che hai imparato nelle precedenti.

| Parte | Capitoli | Cosa fai |
| --- | --- | --- |
| I. Fondamenta | 1-3 | Installi Claude Code, capisci come funzionano tool, loop agentico, permessi e sandbox, impari a scrivere prompt utili e a usare Plan Mode |
| II. Analisi dati | 4-6 | Parti da un CSV di vendite e arrivi a un report Excel con formule vere, grafici, una dashboard Flask e un PDF |
| III. Estendere Claude Code | 7-10 | Scrivi `CLAUDE.md`, custom command, skill e agent, e provi il plugin Superpowers |
| IV. Controllare e automatizzare | 11-15 | Permessi, modalità e sandbox, hook, server MCP, plugin e marketplace, contesto e memoria |
| V. Landing page | 16 | Il primo progetto completo, dall'idea al deploy su Firebase |
| VI. Photogallery | 17-23 | Un'applicazione full-stack con Spec Driven Development, fino al deploy su AWS |

La Parte IV è nuova in questa edizione. Nasce dal fatto che oggi Claude Code parte in auto mode e lavora per lunghi tratti senza chiederti niente, quindi conviene sapere esattamente dove sono i paletti e come spostarli. Lavora su un piccolo progetto di laboratorio, `cc-advanced-lab`, che crei già nel capitolo 2.

La Parte VI è il cuore del libro. Costruisci la Photogallery: un'API REST in Laravel 13, un pannello admin in Filament v5, un frontend React 19 con Vite 6 e Tailwind CSS v4, autenticazione con token Sanctum e job in coda per ridimensionare le foto e leggere i dati EXIF. Prima scrivi le specifiche e le trasformi in un piano di 124 task in 14 fasi, poi le esegui a wave con una review dopo ognuna, anche in parallelo su worktree separati. Prima del deploy fai QA, una review con `/code-review` e un secondo parere da altri modelli (Gemini, Codex, Kimi). Si chiude con il deploy su AWS con CloudFormation. Il codice è nel repository `github.com/hidran/claude-code-book-photogallery`, con un branch per ogni tappa.

In fondo trovi cinque appendici: glossario, troubleshooting, raccolta di prompt, risorse e changelog.

Non sei obbligato a leggere tutto in ordine, ma la prima volta ti conviene. L'unica eccezione ragionevole è la Parte IV, che puoi leggere anche dopo i progetti delle parti V e VI. Se però lavori su codice che conta, leggila prima.

## Riepilogo

- Installa Claude Code con l'installer nativo, che si aggiorna da solo; Homebrew e WinGet sono alternative con aggiornamento manuale, npm è un'opzione avanzata che richiede Node.js 22+.
- `claude doctor` è il primo controllo quando qualcosa non funziona; `claude update` aggiorna subito.
- Serve un piano a pagamento o un account Console. Una `ANTHROPIC_API_KEY` approvata vince sull'abbonamento: controlla sempre con `/status`.
- I comandi di tutti i giorni sono `/clear`, `/compact`, `/resume`, `/rewind`, `/usage` (che ha assorbito `/cost`), `/model`, `/config` e `/init`.
- Le sessioni partono in auto mode; `Shift+Tab` passa a Manual, Accept edits e Plan. `claude -p` esegue un prompt solo ed esce.
- Su Windows l'installer nativo funziona senza WSL, ma per il sandbox serve WSL 2.

## Esercizio

Primo, verifica il setup. `claude doctor` non deve segnalare errori, e in una sessione `/status` deve mostrare l'account e il metodo di autenticazione che ti aspetti (abbonamento o Console).

Poi torna in `~/projects/hello-claude` e avvia `claude` senza flag, quindi in auto mode. Chiedi:

```text
Aggiungi a hello.py un'opzione --maiuscolo che stampa il saluto in maiuscolo, poi lancialo con e senza l'opzione.
```

Conta quante conferme ti chiede rispetto al giro in Manual della sezione 1.5. Quando ha finito, premi due volte `Esc` sul prompt vuoto e torna al checkpoint precedente alla richiesta, ripristinando il codice. Se Claude ha modificato il file con un comando di shell invece che con il tool `Edit`, il checkpoint non copre quella modifica: in quel caso cancella l'opzione a mano o chiedi a Claude di farlo.

<!-- VERIFY: i checkpoint di /rewind non tracciano le modifiche fatte da comandi Bash (non è in FACTS.md). -->

L'esercizio è finito quando `python3 hello.py --name Hidran` stampa `Ciao Hidran` e `python3 hello.py --maiuscolo` termina con l'errore di argparse `unrecognized arguments: --maiuscolo`, segno che il rewind ha riportato il file alla versione di partenza.

Se vuoi confrontare il tuo `hello.py` con il mio, è nel branch `cap-01-hello-claude` del repository `github.com/hidran/claude-code-book-snippets`.

<!-- VERIFY: il branch cap-01-hello-claude nel repo claude-code-book-snippets esisteva come "sarà disponibile" nella prima edizione; controllare che esista. -->
