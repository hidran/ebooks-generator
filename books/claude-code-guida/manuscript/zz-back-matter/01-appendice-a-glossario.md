# Appendice A. Glossario

I termini che ricorrono nel libro, in ordine alfabetico. Comandi, file e cartelle sono ordinati per la prima lettera del nome, senza contare la barra o il punto iniziale: `/goal` sta sotto la G, `.claude/rules/` sotto la C. Ogni voce rimanda al capitolo, con la numerazione di questa edizione, dove l'argomento è spiegato per esteso. I nomi dei modelli e i numeri di versione sono quelli di ottobre 2026: per i valori correnti controlla `/model` e il changelog dell'Appendice E.

## A

`acceptEdits`
:   La modalità di permesso Accept edits. Claude modifica i file e lancia i comandi che toccano solo file e cartelle (`mkdir`, `touch`, `mv`, `cp`) senza chiedere, e ti ferma su tutto il resto. Serve quando lavori a piccoli passi e rivedi il risultato con `git diff`. Capitoli 2 e 11.

Agent, subagent
:   Un'istanza di Claude che riceve un solo compito, lo svolge in un contesto tutto suo e restituisce alla sessione principale solo il rapporto finale. Ha un system prompt dedicato e, se vuoi, un elenco ristretto di tool. Si definisce in un file Markdown con frontmatter (`name` e `description` obbligatori) in `.claude/agents/` per il progetto, in `~/.claude/agents/` per te, o dentro un plugin. Il wizard di `/agents` è stato rimosso nel luglio 2026 e il comando oggi stampa solo un promemoria: il file lo scrivi tu o lo chiedi a Claude. Nelle sessioni interattive i subagent girano in background per default. In questo libro "agent" e "subagent" indicano la stessa cosa. Capitolo 10.

`Agent` (tool)
:   Il tool con cui Claude lancia un subagent. Fino alla versione 2.1.63 si chiamava `Task`, nome che trovi ancora in configurazioni vecchie e che funziona come alias nelle regole di permesso. Una regola come `Agent(model:opus)` colpisce i subagent lanciati su Opus. Capitoli 2, 10 e 11.

agent view
:   La schermata che si apre con `claude agents`: tutte le sessioni in background in una lista, raggruppate per stato (Working, Needs input, Completed). `Space` apre l'anteprima e permette di rispondere senza entrare, `Enter` entra nella sessione, `←` sul prompt vuoto torna alla lista, `Ctrl+T` fissa una sessione in alto. Capitolo 20.

`AGENTS.md`
:   Un file di istruzioni per agenti di produttori diversi. Claude Code lo legge da solo quando nel progetto non c'è un `CLAUDE.md`; se ci sono tutti e due, il modo più semplice per non duplicare è importare `@AGENTS.md` dal `CLAUDE.md`. Capitolo 7.

API key
:   La chiave per usare Claude a consumo attraverso la Console. Con un account Console oggi basta il login dal browser. Se la variabile `ANTHROPIC_API_KEY` è impostata e la approvi, vince sull'abbonamento e paghi a token: controlla con `/status`. Capitolo 1.

argparse
:   Il modulo della libreria standard Python per leggere gli argomenti da riga di comando. Nel libro rende parametrico lo script che genera il report Excel. Capitolo 5.

auto memory
:   Vedi memoria automatica.

auto mode
:   La modalità di permesso con cui partono le sessioni interattive nel terminale e in VS Code: dalla versione 2.1.228 per i piani Pro, Max e Team, dalla 2.1.283 per tutti. Un classificatore approva le azioni coerenti con la richiesta e blocca quelle rischiose. Le azioni bloccate finiscono nella scheda Recently denied di `/permissions`. Dopo tre blocchi consecutivi o venti in una sessione, auto mode si mette in pausa e torna a chiederti conferma. `claude -p` parte invece in Manual. Capitoli 2 e 11.

## B

build workflow
:   Il documento che descrive come si esegue il piano del Photogallery: le fasi, le regole operative e il ciclo leggi, implementa, testa, committa, spunta il task. Capitoli 17 e 18.

`bypassPermissions`
:   La modalità senza alcun controllo, la stessa del flag `--dangerously-skip-permissions`. Ha senso solo in un container o in una VM che puoi buttare via. Un hook che nega blocca anche qui. Capitoli 2 e 11.

## C

classificatore
:   Il modello separato che in auto mode esamina le azioni al posto tuo. Le regole deny e ask vengono valutate prima di lui, quindi per ciò che non deve succedere mai serve una regola. I limiti che scrivi in chat ("non fare push") li considera come indicazioni, valide per quella sessione. `claude auto-mode defaults` stampa le sue regole predefinite. Capitoli 2 e 11.

change set
:   L'anteprima delle modifiche che CloudFormation applicherebbe a uno stack, senza applicarle. Va letta prima di ogni aggiornamento: un `Replacement: True` sull'istanza RDS vuol dire un database nuovo, e senza snapshot perdi i dati. Capitolo 23.

`/clear`
:   Riparte con una conversazione vuota e ricarica i file di memoria come all'avvio. La conversazione precedente resta in `/resume`. Gli alias sono `/reset` e `/new`. Capitoli 1 e 15.

Claude Code
:   L'agente di Anthropic che lavora sui file del tuo progetto, oggetto del libro. Gira nel terminale, nell'estensione di VS Code, nel plugin per gli IDE JetBrains, nella scheda Code dell'app desktop e nel cloud su claude.ai/code. Non è incluso nel piano gratuito di claude.ai. Capitolo 1.

`.claude/rules/`
:   Una cartella di file Markdown con istruzioni divise per argomento. Una regola senza frontmatter si carica all'avvio come un pezzo di `CLAUDE.md`; una con `paths:` (un elenco di glob) si carica solo quando Claude legge o modifica un file che corrisponde. Le regole personali stanno in `~/.claude/rules/`. Capitoli 7 e 15.

`CLAUDE.md`
:   Il file di istruzioni che Claude Code carica a ogni sessione: comandi, convenzioni, cose da non fare. Ha quattro livelli: organizzazione, utente (`~/.claude/CLAUDE.md`), progetto (`./CLAUDE.md` o `./.claude/CLAUDE.md`, in Git) e locale (`./CLAUDE.local.md`, fuori da Git). Conviene stare sotto le duecento righe. Accetta import con `@percorso` fino a quattro livelli, e i commenti HTML vengono tolti prima di arrivare a Claude. Orienta il modello ma non lo vincola: per un divieto vero servono una regola di permesso o un hook. Capitoli 7 e 15.

CloudFormation
:   Il servizio AWS che crea e aggiorna l'infrastruttura a partire da un template YAML. Nel libro il template del Photogallery lo scrive Claude e lo rivedi tu. Capitolo 23.

CloudFront
:   La CDN di AWS. Nel Photogallery serve la SPA React e le varianti delle foto, e inoltra `/api/*` all'ALB. Capitolo 23.

Code Review su GitHub
:   Il servizio gestito che revisiona le pull request con più agent, per i piani Team ed Enterprise e pagato per review. Pubblica commenti inline con gravità Important, Nit o Pre-existing e un check run, ma non approva e non blocca mai. Si rilancia con un commento `@claude review` e si personalizza con `REVIEW.md`. Capitolo 22.

`/code-review`
:   La review locale, alias `/review`. Controlla i commit non ancora pushati e le modifiche non committate cercando bug di correttezza, e gira come subagent in background. Accetta un livello di effort e un target (file, PR, branch, intervallo come `main...feat/albums-api`). Senza livello riusa l'ultimo che hai scritto. `--fix` applica le correzioni, che `/rewind` non annulla. Legge `CLAUDE.md`, non `REVIEW.md`. Capitolo 22.

commit atomico
:   Un commit che contiene un solo cambiamento logico, completo. Nel capitolo 8 lo produce il comando `/commit` che scrivi tu, sui file in staging. Nel Photogallery la regola diventa un task, un commit, con la casella di `docs/TASKS.md` spuntata nello stesso commit. Capitoli 8, 18 e 19.

companion repo
:   I repository GitHub del libro: `claude-code-book-photogallery`, `claude-code-book-snippets` e quello della landing page. I nomi dei branch, come `book/cap-13-wave-1-backend`, seguono la numerazione della prima edizione. Vedi "Come leggere il libro".

compattazione
:   Il riassunto della conversazione che prende il posto dei messaggi più vecchi e libera spazio. La lanci con `/compact`, a cui conviene dire cosa conservare; Claude Code la fa anche da solo quando la finestra si avvicina al limite. Un hook `SessionStart` con matcher `compact` rimette in contesto le informazioni che non devono perdersi. Capitoli 12 e 15.

contesto, finestra di contesto
:   Tutto quello che Claude vede in una sessione: istruzioni di sistema, definizioni dei tool, file di memoria, file letti, output dei comandi, messaggi. Con i modelli attuali arriva a un milione di token, ma più si riempie più la sessione costa e più si perdono i dettagli. La regola pratica è un task, una sessione. Capitoli 1 e 15.

`/context`
:   Il pannello che mostra come è divisa la finestra di contesto: system prompt, tool, server MCP, agent, skill, file di memoria, messaggi e spazio libero. Capitolo 15.

CSP (Content Security Policy)
:   L'header HTTP che dice al browser da dove può caricare script, stili e immagini. È la difesa principale contro l'iniezione di JavaScript (XSS) e una delle mitigazioni del token in `localStorage` del Photogallery. Capitolo 22.

custom command
:   Un file Markdown in `.claude/commands/` o `~/.claude/commands/` il cui nome diventa un comando: `fix-tests.md` diventa `/fix-tests`. Oggi i custom command fanno parte delle skill: continuano a funzionare, per il lavoro nuovo si preferiscono le skill, e se i nomi coincidono vince la skill. Le sottocartelle aggiungono un prefisso (`/frontend:component`). Capitolo 8.

## D

dev container
:   Un container di sviluppo che racchiude tutto Claude Code, hook e server MCP compresi. È il passo successivo alla sandbox quando lavori su codice che non conosci. Capitolo 2.

`/doctor`, `claude doctor`
:   I due controlli della configurazione. `claude doctor`, dalla shell, verifica installazione e file di impostazioni senza avviare una sessione ed è in sola lettura. `/doctor` (alias `/checkup`), dentro la sessione, fa un controllo più ampio e può correggere; `/doctor prompt-audit` cerca istruzioni obsolete, riferimenti a file che non esistono e contraddizioni, e propone le modifiche senza applicarle. Capitoli 1 e 15.

`dontAsk`
:   La modalità per script e CI: passano le letture, i comandi in sola lettura e i tool pre-approvati, il resto viene negato senza domande. Capitoli 2 e 11.

dotfiles
:   I file di configurazione della shell e degli strumenti (`.zshrc`, `.gitconfig`) tenuti in un repository per ritrovarli su ogni macchina. `~/.claude/` è un buon candidato da aggiungere. Capitolo 1.

DRY
:   "Don't Repeat Yourself". Nel Photogallery si applica con la regola del tre: si estrae un'astrazione alla terza ripetizione, non alla seconda. Capitolo 18.

## E

ECS Fargate
:   Il servizio AWS che esegue container senza gestire server. Nel Photogallery ci girano l'API Laravel e il worker della coda. Capitolo 23.

effort
:   Quanto ragiona il modello prima di rispondere. Si sceglie con `/effort` tra `low`, `medium`, `high`, `xhigh` e `max` (quest'ultimo vale solo per la sessione); sui modelli 5.5 il default è `medium`. `low` o `medium` per domande e piccole modifiche, `high` per progettazione, bug difficili e specifiche. Capitoli 2 e 3.

Explore
:   Il subagent integrato in sola lettura che esplora il codice per rispondere a una domanda, con tre livelli di profondità. Insieme a Plan parte senza `CLAUDE.md`. Capitolo 10.

## F

Fable
:   La famiglia di modelli più capace tra quelli disponibili in Claude Code, alias `fable` (Fable 5.1 mentre scrivo), con finestra da un milione di token. Non è mai il default: la scegli con `/model` o nel campo `model` di un subagent. Capitolo 2.

Filament
:   Il framework Laravel per pannelli di amministrazione. Il Photogallery usa Filament v5; l'accesso al pannello passa da `canAccessPanel()` e le azioni dalle policy. Capitolo 19.

Firebase Hosting
:   L'hosting statico di Google su cui pubblichi la landing page, con i preview channel per le anteprime. Capitolo 16.

`/fork`
:   Copia la conversazione in una nuova sessione in background, lasciando la principale dov'è. Serve per provare un'alternativa senza perdere il filo. Capitoli 15 e 20.

frontmatter
:   Il blocco YAML tra due righe `---` all'inizio di un file Markdown. Lo usano custom command, skill, agent e regole per dichiarare nome, descrizione, tool ammessi, modello e percorsi. Capitoli 7-10.

## G

`/goal`
:   Imposta una condizione di completamento: Claude continua a lavorare, turno dopo turno, finché un valutatore separato non la giudica soddisfatta. Il valutatore vede solo quello che Claude mostra nella conversazione, quindi la condizione deve nominare un controllo che Claude esegue, come "`composer test` esce con codice 0". `/goal` da solo mostra lo stato, `/goal clear` lo annulla. Capitolo 20.

## H

harness
:   Il programma che sta intorno al modello: gestisce la conversazione, espone i tool, controlla permessi e hook, esegue le chiamate e rimanda i risultati. Claude Code è un harness. Quasi tutto quello che configuri nel libro vive qui. Capitolo 2.

headless
:   L'uso non interattivo con `claude -p "prompt"`: un prompt, una risposta, uscita. Per script e CI, con `--allowedTools` per le azioni ammesse, `--bare` per saltare hook, skill, plugin, server MCP e `CLAUDE.md`, e `--output-format json`. Capitolo 1.

hook
:   Un comando che Claude Code esegue da solo su un evento del ciclo di lavoro (`SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop`, `Notification` e altri). Riceve il JSON dell'evento su stdin; esce con 0 per proseguire, con 2 per bloccare rimandando stderr a Claude, oppure con 0 e un JSON su stdout per decisioni più fini. Si registra sotto `hooks` nel `settings.json` o nel `hooks/hooks.json` di un plugin. Gira fuori dalla sandbox con i tuoi permessi, e `/hooks` elenca quelli attivi. Oltre al tipo `command` esistono `http`, `prompt` e `agent`. Capitolo 12.

HSTS
:   L'header HTTP Strict Transport Security, che obbliga il browser a usare HTTPS per un dominio. Capitolo 22.

## I

idempotente
:   Un'operazione che ripetuta dà lo stesso risultato. Nel Photogallery lo sono il job che elabora le foto, perché scrive le varianti in un percorso che dipende solo dall'UUID, e gli endpoint `PUT` e `DELETE` dei preferiti. Capitolo 21.

`/init`
:   Analizza il progetto e scrive una prima versione di `CLAUDE.md`, da rivedere e completare a mano. Capitolo 7.

## K

KISS
:   "Keep It Simple, Stupid": la soluzione più semplice che soddisfa il requisito. Nel Photogallery è una delle regole del `CLAUDE.md` contro l'over-engineering che un agente tende a produrre. Capitoli 17 e 18.

## L

Laravel Sail
:   L'ambiente Docker di Laravel. Nel Photogallery avvia MariaDB, Redis, Mailpit e MinIO, così i test girano su un database simile a quello di produzione invece che solo su SQLite. Capitolo 19.

Lighthouse
:   Lo strumento di Google che misura prestazioni, accessibilità e SEO di una pagina; si lancia anche da riga di comando. Capitolo 22.

loop agentico
:   Il ciclo con cui lavora un agente: raccoglie il contesto, agisce, verifica, e ricomincia finché il lavoro è finito o finché ha bisogno di te. Capitolo 2.

Lovable
:   Uno strumento visuale che genera interfacce da un prompt. Nel libro è il caso di studio per replicare con Claude Code un design che esiste già. Capitolo 16.

## M

Manual
:   La modalità di permesso che chiede conferma per quasi tutto. Era il default prima di auto mode; nelle impostazioni si chiama `default` e il flag accetta anche `--permission-mode manual`. È la scelta giusta su un repository che non conosci. Capitoli 2 e 11.

marketplace
:   Un repository con un file `.claude-plugin/marketplace.json` che elenca dei plugin e dice dove trovarli. Quello ufficiale, `claude-plugins-official`, viene aggiunto da solo al primo avvio; `claude-community` è quello della community; `anthropics/claude-code` è solo dimostrativo. Si aggiunge con `/plugin marketplace add <percorso|utente/repo>`. Capitolo 14.

matcher
:   Il campo di un gruppo di hook che decide quando il gruppo scatta. Per gli eventi dei tool filtra il nome del tool (`"Edit|Write"`) ed è sensibile alle maiuscole; per `SessionStart` filtra l'origine della sessione, per esempio `compact`. Il campo `if` restringe ancora, con la sintassi delle regole di permesso. Capitolo 12.

MCP (Model Context Protocol)
:   Il protocollo aperto con cui Claude Code parla con servizi esterni attraverso un **server MCP**. I server remoti usano il trasporto `http` e si autenticano con un header o con OAuth; quelli locali usano `stdio` e sono processi avviati da Claude Code. I loro tool compaiono come `mcp__<server>__<tool>` e si governano con le stesse regole di permesso degli altri tool. Ogni server ha uno scope (vedi scope). Si aggiungono con `claude mcp add`, si controllano con `/mcp`. Capitolo 13.

`MEMORY.md`
:   L'indice della memoria automatica di un progetto. Viene caricato a ogni sessione fino a duecento righe e rimanda agli altri file, che Claude legge quando servono. Capitolo 15.

memoria automatica (auto memory)
:   Le annotazioni che Claude scrive da solo: preferenze, correzioni, contesto che non si ricava dal codice. Sono file Markdown in `~/.claude/projects/<progetto>/memory/`, condivisi tra i worktree dello stesso repository e invisibili ai colleghi. `/memory` li elenca e accende o spegne la funzione. Capitoli 7 e 15.

`/memory`
:   Elenca i file di istruzioni caricati e la cartella della memoria automatica, e la attiva o disattiva. La vecchia scorciatoia `#` per aggiungere una riga alla memoria è stata rimossa: chiedi a Claude di modificare `CLAUDE.md` o passa da qui. Capitoli 7 e 15.

modalità di permesso
:   L'impostazione che decide cosa Claude può fare senza chiederti conferma, scritta nella barra di stato. `Shift+Tab` gira tra auto, Manual, Accept edits e Plan (su alcuni setup Windows il tasto è `Alt+M`); `dontAsk` e `bypassPermissions` si scelgono all'avvio con `--permission-mode`. Come default di progetto si imposta `permissions.defaultMode`, ma `auto` e `bypassPermissions` lì hanno effetto solo in `~/.claude/settings.json`. Capitoli 2 e 11.

`/model`
:   Mostra i modelli disponibili per il tuo piano e cambia quello attivo. Gli alias sono `opus`, `sonnet`, `haiku`, `fable` e `opusplan`. Capitoli 1 e 2.

## O

openpyxl
:   La libreria Python che legge e scrive file Excel, formule comprese. Capitolo 5.

Opus
:   Claude Opus, alias `opus`. Claude Opus 5.5 è il modello predefinito da settembre 2026, con finestra da un milione di token. Capitolo 2.

`opusplan`
:   L'alias che usa Opus mentre pianifica in Plan Mode e Sonnet mentre esegue. Capitoli 1 e 3.

## P

Plan Mode
:   La modalità in cui Claude legge, esplora e propone un piano senza modificare nulla finché non approvi. Ci entri con `Shift+Tab`, con `/plan` o con `claude --permission-mode plan`. All'approvazione scegli se proseguire in auto mode o approvando le modifiche una a una, oppure resti a pianificare; `Ctrl+G` apre il piano nel tuo editor. Capitoli 3 e 4.

`/permissions`
:   Il pannello delle regole attive, con le schede Allow, Ask, Deny e Recently denied. Selezionando una regola vedi da quale file arriva. Capitolo 11.

plugin
:   Una cartella che impacchetta skill, agent, hook e server MCP e si installa in un colpo. Il manifest `.claude-plugin/plugin.json` è l'unico file che va in `.claude-plugin/`: i componenti stanno nella radice del plugin. Il campo `name` diventa il prefisso dei comandi (`/cc-lab-toolkit:report-pdf`). Si gestisce con `/plugin`, si prova con `claude --plugin-dir`, si controlla con `claude plugin validate` e si misura con `claude plugin eval`. Superpowers è un plugin. Capitoli 8 e 14.

policy
:   In Laravel, la classe che decide se un utente può compiere un'azione su un modello, per esempio modificare una foto che non è sua. Capitolo 19.

presigned URL
:   Un URL S3 firmato e a scadenza breve che permette a un client di caricare o scaricare un oggetto senza credenziali AWS. Nel Photogallery è il passo successivo se un giorno l'upload dovesse saltare il backend. Capitolo 21.

prompt
:   Il testo che scrivi a Claude. Un prompt utile per Claude Code dice cosa fare, dove, cosa non toccare e come si verifica il risultato. Capitolo 3.

prompt injection
:   Istruzioni rivolte al modello nascoste in un contenuto esterno: una pagina web, una issue, un'email letta da un server MCP. Si contiene con server affidabili, credenziali minime e regole di permesso sui tool. Capitolo 13.

## R

regole allow, ask e deny
:   Le eccezioni alla modalità di permesso, nella chiave `permissions` dei file di impostazioni, con la sintassi `Tool(specificatore)`: `Bash(python -m pytest *)`, `Read(./.env)`, `mcp__github__*`. Si valutano nell'ordine deny, ask, allow, e un deny vince sempre. Una regola su `Bash` confronta il testo del comando, non il programma: per un confine vero servono la sandbox o un hook. Capitolo 11.

RDS
:   Il database relazionale gestito di AWS. Il Photogallery usa MariaDB su RDS, lo stesso motore di Sail, raggiungibile solo dal security group dei task ECS. Capitolo 23.

`REVIEW.md`
:   Il file nella radice del repository che personalizza Code Review su GitHub: cosa conta come Important, quanti Nit al massimo, cosa ignorare, cosa controllare sempre. `/code-review` in locale non lo legge. Capitolo 22.

review multi-LLM (cross-LLM review)
:   Far rivedere lo stesso changeset, con lo stesso prompt, a modelli diversi (Claude, Gemini, Codex, Kimi) e aggregare i risultati per consenso. Ogni modello ha punti ciechi diversi. Capitolo 22.

`/rewind`
:   Riporta codice, conversazione o entrambi a un punto precedente; si apre anche con `Esc` due volte sul prompt vuoto. Tiene traccia delle modifiche fatte con i tool di modifica dei file, non di quelle fatte da un comando `Bash` né delle correzioni di `/code-review --fix`. Capitolo 15.

## S

S3
:   Lo storage a oggetti di AWS. Nel Photogallery contiene originali e varianti delle foto in due bucket, uno privato e uno pubblico, e serve la SPA dietro CloudFront. Capitoli 21 e 23.

Sanctum
:   Il pacchetto Laravel per i token API. Nel Photogallery ogni token ha delle ability (`photos:write`, `albums:write`, `admin`) e ogni mutazione controlla sia l'ability sia la policy. Capitoli 17 e 19.

sandbox
:   Il secondo livello di controllo, accanto ai permessi. Una volta che un comando di shell è partito, la sandbox limita cosa possono raggiungere lui e i processi che lancia: scrittura solo nella cartella di lavoro, lettura quasi ovunque salvo i percorsi che neghi, rete solo attraverso un proxy locale con una lista di domini ammessi. La applica il sistema operativo (Seatbelt su macOS, bubblewrap e socat su Linux e WSL 2); su Windows nativo non è supportata. Si accende con `/sandbox` o con la chiave `sandbox` nel `settings.json`. `Read`, `Edit`, hook e server MCP ne restano fuori. Capitoli 2 e 11.

scope
:   Dove vale e dove viene salvata una configurazione. Per un server MCP: `local` (default, solo tu in questo progetto, in `~/.claude.json`), `project` (`.mcp.json` nel repository, da approvare al primo avvio) e `user` (tutti i tuoi progetti). Per un plugin: user, project (nel `.claude/settings.json` condiviso) e local. Capitoli 13 e 14.

SDD (Spec Driven Development)
:   Il metodo con cui è costruito il Photogallery: ogni riga di codice discende da tre documenti scritti e approvati prima, `docs/REQUIREMENTS.md` (cosa), `docs/DESIGN.md` (come) e `docs/TASKS.md` (124 task in 14 fasi). È la risposta al vibecoding su un progetto vero. Capitoli 17 e 18.

sessione
:   Una conversazione con Claude Code, dall'avvio all'uscita. `/resume` (alias `/continue`) riprende una sessione passata, `/clear` ne inizia una nuova nella stessa finestra. Capitoli 1 e 15.

sessione in background
:   Una sessione che lavora senza tenere occupato il terminale. Si avvia con `claude --bg --name <nome> "<prompt>"` o si stacca con `/background` (`/bg`); prima di modificare file si sposta da sola in un worktree. A lavoro finito committa, pusha il branch e può aprire una PR in bozza. Si segue dall'agent view e si gestisce con `claude attach`, `logs`, `stop` e `rm`. Consuma il piano come una sessione normale. Capitolo 20.

`settings.json`
:   I file di impostazioni: `~/.claude/settings.json` per tutti i tuoi progetti, `.claude/settings.json` per il progetto e il team (in Git), `.claude/settings.local.json` per te su quel progetto (fuori da Git, ci finiscono i "non chiedermelo più"), più le managed settings dell'organizzazione, che non si possono scavalcare. Contengono permessi, hook, sandbox e altro. Capitolo 11.

skill
:   Una cartella con un file `SKILL.md` (frontmatter più istruzioni) ed eventuali script, riferimenti e template. Nome e descrizione restano sempre in contesto; il corpo si carica solo quando la skill serve, perché la richiami con `/nome` o perché Claude riconosce la situazione dalla descrizione, che quindi va scritta come un trigger. Vivono in `.claude/skills/`, `~/.claude/skills/` o in un plugin. `/skills` le elenca, `/reload-skills` le ricarica. Capitolo 9.

skill-creator
:   La skill che crea altre skill con una conversazione guidata, scrive i file e propone come provarle. Capitolo 9.

`/skill-doctor`
:   Mostra per ogni skill quanto contesto occupa e quanto spesso viene usata. Una skill pesante e mai usata è da disattivare. Capitolo 15.

SOLID
:   I cinque principi di progettazione a oggetti (responsabilità singola, aperto/chiuso, sostituzione di Liskov, segregazione delle interfacce, inversione delle dipendenze). Nel Photogallery stanno nel `CLAUDE.md` con esempi presi dal codice del progetto. Capitolo 18.

Sonnet
:   Claude Sonnet, alias `sonnet` (Sonnet 5.5 mentre scrivo): più veloce e meno costoso di Opus, buono per l'esecuzione. Capitolo 2.

spec-critic
:   Il subagent che rilegge le specifiche come un revisore ostile: buchi di sicurezza, requisiti senza task, task senza requisito, rimandi a sezioni che non esistono. Capitolo 18.

`/subtask`
:   Lancia un subagent che eredita l'intera conversazione, per delegare un lavoro che dipende da quello che vi siete detti. Capitolo 10.

Superpowers
:   Il plugin open source di Jesse Vincent con skill per brainstorming, sviluppo guidato da subagent con review fra un task e l'altro, debugging sistematico e TDD. È nel marketplace ufficiale: `/plugin install superpowers@claude-plugins-official`. Capitoli 8 e 16.

## T

task atomico
:   Un task che porta il progetto da uno stato coerente al successivo con il minimo lavoro, e che si chiude con un solo commit. Nel Photogallery ogni task ha un ID (`T031`), le sezioni di `DESIGN.md` da leggere, le dipendenze e criteri di accettazione verificabili. Capitoli 16 e 18.

task orfano
:   Una feature segnata come fatta ma rimasta a metà: un endpoint vuoto, un componente mai importato, una colonna mai usata. Si cerca con un audit prima del deploy e si decide con la regola delle tre D: Delete, Complete, Document and defer. Capitolo 22.

`/tasks`
:   Elenca i subagent e i lavori in background della sessione con il loro stato. `Ctrl+X Ctrl+K` li ferma tutti. Capitolo 10.

token
:   L'unità di testo con cui i modelli leggono e scrivono, più o meno un pezzo di parola. In italiano lo stesso testo richiede in media più token che in inglese. Contesto, limiti del piano e costi si misurano in token. Capitoli 1 e 15.

tool
:   Una funzione descritta al modello con nome, descrizione e schema dei parametri. Il modello non esegue niente: chiede una chiamata (`tool_use`), l'harness la esegue e restituisce un `tool_result`. I tool principali sono `Read`, `Edit`, `Write`, `Bash` (che su macOS, Linux e WSL fa anche le ricerche), `WebSearch`, `WebFetch`, `Agent` e i tool MCP; su alcune installazioni ci sono anche `Grep` e `Glob`. `Ctrl+O` mostra le singole chiamate. Capitolo 2.

tool search
:   Il meccanismo con cui Claude Code carica all'avvio solo i nomi dei tool MCP e recupera la definizione completa quando un tool serve, così più server costano poco contesto. Capitoli 13 e 15.

## U

ultrareview
:   La review approfondita nel cloud, in research preview: più agent specializzati e un passaggio che scarta i falsi positivi. Si lancia con `/code-review ultra` (alias `/ultrareview`) o con `claude ultrareview` negli script. Serve un account claude.ai; sui piani Pro e Max ci sono tre esecuzioni gratuite, poi si paga con i crediti. Capitolo 22.

`ultrathink`
:   La parola chiave che, scritta in un prompt, alza il ragionamento solo per quel messaggio. Frasi come "think hard" non hanno effetto speciale. Capitoli 2 e 3.

`/usage`
:   Mostra cosa consuma i limiti del piano, diviso per skill, subagent, plugin e server MCP, o il costo della sessione con un account Console. `/cost` e `/stats` sono suoi alias. Capitoli 1 e 15.

## V

vibecoding
:   Andare dritti al codice a forza di prompt, senza specifiche né piano. Funziona per una prova di un pomeriggio; su un progetto con decine di task produce rilavoro. Capitolo 17.

visual companion
:   La parte della skill di brainstorming di Superpowers che genera mockup HTML, li serve in locale e li aggiorna mentre li commenti, prima di scrivere il codice React. Capitolo 16.

## W

wave
:   Un gruppo di fasi del piano che insieme formano un pezzo del sistema, eseguibili in parallelo su track che non condividono file. Nel Photogallery la Wave 1 ha tre track: API e pipeline delle immagini, pannello Filament, frontend React. Capitoli 19 e 20.

wave review
:   La review fatta alla fine di una wave da più agent in parallelo, ciascuno su un aspetto (sicurezza, performance, test, coerenza), per trovare i problemi che si vedono solo guardando i pezzi insieme. Capitolo 19.

worker
:   Il processo che prende i job da una coda e li esegue. Nel Photogallery elabora le foto: in sviluppo la coda è la tabella `jobs` del database, in produzione SQS. Capitoli 21 e 23.

worktree
:   Una seconda cartella di lavoro dello stesso repository, con i suoi file e il suo branch ma la stessa storia Git. `claude --worktree <nome>` lo crea in `.claude/worktrees/<nome>` sul branch `worktree-<nome>`. `.worktreeinclude` elenca i file ignorati da copiare (come `backend/.env`), `{"worktree": {"baseRef": "head"}}` fa partire i worktree dall'`HEAD` locale invece che dal main remoto, e `isolation: worktree` nel frontmatter di un subagent dà a ogni istanza un worktree temporaneo. Capitolo 20.

WSL 2
:   Il sottosistema Linux di Windows. Claude Code funziona anche su Windows nativo, ma WSL 2 serve se vuoi la sandbox o una toolchain Linux; WSL 1 non è supportato. Capitoli 1 e 2.
