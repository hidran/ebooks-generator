# Appendice A. Glossario

I termini che ricorrono nel libro, in ordine alfabetico. Comandi e file sono ordinati per la prima lettera del nome, senza la barra o il punto iniziale: `/goal` sta sotto la G, `.claude/rules/` sotto la C. Ogni voce rimanda al capitolo, con la numerazione di questa edizione, dove l'argomento è spiegato per esteso. Nomi di modelli e versioni sono quelli di ottobre 2026: per i valori correnti controlla `/model` e l'Appendice E.

## A

`acceptEdits`
:   La modalità Accept edits: Claude modifica i file e lancia i comandi che toccano solo file e cartelle senza chiedere, e ti ferma sul resto. Capitoli 2 e 11.

Agent, subagent
:   Un'istanza di Claude che svolge un solo compito in un contesto suo, con un system prompt dedicato e, se vuoi, tool limitati, e restituisce alla sessione principale solo il rapporto. Si definisce in un file Markdown con `name` e `description` nel frontmatter, in `.claude/agents/`, `~/.claude/agents/` o in un plugin. Il wizard di `/agents` è stato rimosso nel luglio 2026: il file lo scrivi tu o lo chiedi a Claude. Nelle sessioni interattive gira in background per default. Nel libro "agent" e "subagent" sono sinonimi. Capitolo 10.

`Agent` (tool)
:   Il tool che lancia un subagent; fino alla versione 2.1.63 si chiamava `Task`. `Agent(model:opus)` in una regola colpisce i subagent lanciati su Opus. Capitoli 2 e 10.

agent view
:   La schermata di `claude agents`: le sessioni in background raggruppate in Working, Needs input e Completed. `Space` apre l'anteprima e permette di rispondere, `Enter` entra, `←` sul prompt vuoto torna alla lista, `Ctrl+T` fissa una riga in alto. Capitolo 20.

`AGENTS.md`
:   Il file di istruzioni condiviso tra agenti di produttori diversi. Claude Code lo legge quando nel progetto manca `CLAUDE.md`; se ci sono tutti e due, importalo con `@AGENTS.md`. Capitolo 7.

API key
:   La chiave per l'uso a consumo dalla Console. Se `ANTHROPIC_API_KEY` è impostata e approvata, vince sull'abbonamento: controlla con `/status`. Capitolo 1.

auto memory
:   Vedi memoria automatica.

auto mode
:   La modalità di permesso predefinita delle sessioni interattive dalla versione 2.1.283 (dalla 2.1.228 per Pro, Max e Team). Un classificatore approva le azioni coerenti con la richiesta e blocca quelle rischiose; i blocchi finiscono in `/permissions`, scheda Recently denied. Dopo tre blocchi di fila o venti in una sessione torna a chiederti conferma. `claude -p` parte in Manual. Capitoli 2 e 11.

## B

build workflow
:   Il documento che descrive come si esegue il piano del Photogallery: fasi, regole operative e ciclo leggi, implementa, testa, committa, spunta. Capitoli 17 e 18.

`bypassPermissions`
:   La modalità senza controlli, uguale al flag `--dangerously-skip-permissions`. Solo in container o VM usa e getta; un hook che nega blocca anche qui. Capitoli 2 e 11.

## C

change set
:   L'anteprima delle modifiche che CloudFormation farebbe a uno stack. Un `Replacement: True` sull'istanza RDS significa un database nuovo. Capitolo 23.

classificatore
:   Il modello che in auto mode giudica le azioni al posto tuo. Le regole deny e ask vengono valutate prima, e i limiti scritti in chat valgono come indicazioni per quella sessione. `claude auto-mode defaults` stampa le sue regole. Capitoli 2 e 11.

Claude Code
:   L'agente di Anthropic che lavora sui file del tuo progetto. Gira nel terminale, in VS Code, negli IDE JetBrains, nell'app desktop e nel cloud. Non è incluso nel piano gratuito di claude.ai. Capitolo 1.

`.claude/rules/`
:   File Markdown con istruzioni divise per argomento. Senza frontmatter si caricano all'avvio; con `paths:` solo quando Claude legge o modifica un file che corrisponde. Le regole personali stanno in `~/.claude/rules/`. Capitolo 7.

`CLAUDE.md`
:   Le istruzioni che Claude Code carica a ogni sessione, su quattro livelli: organizzazione, utente (`~/.claude/CLAUDE.md`), progetto (`./CLAUDE.md`, in Git) e locale (`./CLAUDE.local.md`, fuori da Git). Meglio sotto le duecento righe; accetta import con `@percorso`; i commenti HTML non arrivano a Claude. Orienta il modello ma non lo vincola. Capitoli 7 e 15.

`/clear`
:   Riparte con una conversazione vuota; la precedente resta in `/resume`. Alias `/reset` e `/new`. Capitolo 15.

CloudFormation, CloudFront
:   Il servizio AWS che crea l'infrastruttura da un template YAML e la CDN che serve la SPA del Photogallery e inoltra `/api/*` all'ALB. Capitolo 23.

Code Review su GitHub
:   La review gestita delle pull request per i piani Team ed Enterprise, pagata per review: commenti inline con gravità Important, Nit o Pre-existing, mai un'approvazione o un blocco. Si rilancia con `@claude review` e si personalizza con `REVIEW.md`. Capitolo 22.

`/code-review`
:   La review locale (alias `/review`) dei commit non pushati e delle modifiche non committate, in un subagent in background. Accetta effort e target (`/code-review high main...feat/albums-api`); senza livello riusa l'ultimo. Le correzioni di `--fix` non si annullano con `/rewind`. Legge `CLAUDE.md`, non `REVIEW.md`. Capitolo 22.

commit atomico
:   Un commit con un solo cambiamento logico completo. Lo produce il comando `/commit` che scrivi nel capitolo 8, sui file in staging; nel Photogallery diventa un task, un commit. Capitoli 8 e 19.

companion repo
:   I repository GitHub del libro. I nomi dei branch, come `book/cap-13-wave-1-backend`, seguono la numerazione della prima edizione. Vedi "Come leggere il libro".

compattazione
:   Il riassunto che sostituisce i messaggi più vecchi e libera contesto. La lanci con `/compact` più le istruzioni su cosa conservare; Claude Code la fa anche da solo vicino al limite. Un hook `SessionStart` con matcher `compact` rimette in contesto ciò che non deve perdersi. Capitoli 12 e 15.

contesto, finestra di contesto
:   Tutto quello che Claude vede: istruzioni di sistema, tool, file di memoria, file letti, output, messaggi. Arriva a un milione di token, ma più è pieno più costa e più si perdono dettagli. Regola pratica: un task, una sessione. Capitoli 1 e 15.

`/context`
:   Mostra come è divisa la finestra: system prompt, tool, MCP, agent, skill, file di memoria, messaggi, spazio libero. Capitolo 15.

custom command
:   Un file Markdown in `.claude/commands/` o `~/.claude/commands/` che diventa un comando: `fix-tests.md` è `/fix-tests`. Oggi fa parte delle skill: funziona ancora, ma per il lavoro nuovo si preferisce una skill, che vince se i nomi coincidono. Capitolo 8.

## D

`/doctor`, `claude doctor`
:   `claude doctor`, dalla shell, controlla installazione e impostazioni senza aprire una sessione e non modifica niente. `/doctor` (alias `/checkup`) fa un controllo più ampio e può correggere; `/doctor prompt-audit` trova istruzioni obsolete o in conflitto e propone le modifiche. Capitoli 1 e 15.

`dontAsk`
:   La modalità per script e CI: passano letture e tool pre-approvati, il resto è negato senza domande. Capitoli 2 e 11.

DRY
:   "Don't Repeat Yourself", applicato con la regola del tre: alla seconda ripetizione aspetti, alla terza estrai. Capitolo 18.

## E

ECS Fargate
:   Il servizio AWS che esegue container senza server da gestire; ci girano l'API e il worker del Photogallery. Capitolo 23.

effort
:   Quanto ragiona il modello. Si sceglie con `/effort` tra `low`, `medium`, `high`, `xhigh` e `max` (solo per la sessione); sui modelli 5.5 il default è `medium`. Per un solo prompt difficile basta `ultrathink`. Capitoli 2 e 3.

Explore
:   Il subagent integrato in sola lettura che esplora il codice. Come Plan, parte senza `CLAUDE.md`. Capitolo 10.

## F

Fable
:   La famiglia di modelli più capace in Claude Code, alias `fable` (Fable 5.1 mentre scrivo). Non è mai il default: la scegli con `/model` o nel campo `model` di un subagent. Capitolo 2.

Filament
:   Il framework Laravel per pannelli di amministrazione, v5 nel Photogallery. Capitolo 19.

Firebase Hosting
:   L'hosting statico di Google su cui pubblichi la landing page, con i preview channel per le anteprime. Capitolo 16.

`/fork`
:   Copia la conversazione in una nuova sessione in background, lasciando dov'è quella principale. Capitoli 15 e 20.

frontmatter
:   Il blocco YAML tra due righe `---` in cima a un file Markdown, usato da command, skill, agent e regole. Capitoli 7-10.

## G

`/goal`
:   Una condizione di completamento: Claude continua turno dopo turno finché un valutatore separato non la giudica soddisfatta. Il valutatore vede solo la conversazione, quindi la condizione deve nominare un controllo che Claude esegue e mostra ("`composer test` esce con codice 0"). `/goal clear` la annulla. Capitolo 20.

## H

harness
:   Il programma intorno al modello: gestisce la conversazione, espone i tool, controlla permessi e hook, esegue le chiamate. Claude Code è un harness. Capitolo 2.

headless
:   L'uso non interattivo con `claude -p "prompt"`, per script e CI. Le azioni ammesse si dichiarano con `--allowedTools`; `--bare` salta hook, skill, plugin, MCP e `CLAUDE.md`. Capitolo 1.

hook
:   Un comando che Claude Code esegue da solo su un evento (`SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop`, `Notification` e altri). Riceve JSON su stdin; exit 0 prosegue, exit 2 blocca e rimanda stderr a Claude, exit 0 con JSON su stdout dà un controllo più fine. Si registra sotto `hooks` nel `settings.json` o in un plugin, gira fuori dalla sandbox e `/hooks` lo mostra. Capitolo 12.

## I

idempotente
:   Che ripetuto dà lo stesso risultato, come il job delle foto che scrive ogni variante in un percorso fisso. Capitolo 21.

`/init`
:   Scrive una prima versione di `CLAUDE.md` analizzando il progetto. Capitolo 7.

## K

KISS
:   "Keep It Simple, Stupid": la soluzione più semplice che soddisfa il requisito, scritta nel `CLAUDE.md` contro l'over-engineering. Capitoli 17 e 18.

## L

Laravel Sail
:   L'ambiente Docker di Laravel; nel Photogallery avvia MariaDB, Redis, Mailpit e MinIO. Capitolo 19.

loop agentico
:   Il ciclo dell'agente: raccoglie il contesto, agisce, verifica, ricomincia finché ha finito o finché ha bisogno di te. Capitolo 2.

Lovable
:   Uno strumento che genera interfacce da un prompt; nel libro è il design da replicare. Capitolo 16.

## M

Manual
:   La modalità che chiede conferma per quasi tutto, il default prima di auto mode. Nelle impostazioni si chiama `default`; il flag accetta `--permission-mode manual`. Capitoli 2 e 11.

marketplace
:   Un repository con `.claude-plugin/marketplace.json` che elenca dei plugin. L'ufficiale `claude-plugins-official` viene aggiunto al primo avvio; `anthropics/claude-code` è solo dimostrativo. Si aggiunge con `/plugin marketplace add`. Capitolo 14.

matcher
:   Il filtro di un gruppo di hook: per gli eventi dei tool il nome del tool (`"Edit|Write"`, sensibile alle maiuscole), per `SessionStart` l'origine (`compact`). Il campo `if` restringe ancora. Capitolo 12.

MCP (Model Context Protocol)
:   Il protocollo con cui Claude Code usa servizi esterni attraverso un server MCP: remoto su `http` (token in un header o OAuth) o locale su `stdio`, avviato da Claude Code. I tool si chiamano `mcp__<server>__<tool>` e seguono le regole di permesso. Si aggiunge con `claude mcp add`, si controlla con `/mcp`. Capitolo 13.

memoria automatica (auto memory)
:   Le annotazioni che Claude scrive da solo (preferenze, correzioni, contesto) in `~/.claude/projects/<progetto>/memory/`, condivise tra i worktree del repository e invisibili ai colleghi. Capitoli 7 e 15.

`MEMORY.md`
:   L'indice della memoria automatica, caricato a ogni sessione fino a duecento righe. Capitolo 15.

`/memory`
:   Elenca i file di istruzioni caricati e accende o spegne la memoria automatica. Sostituisce la vecchia scorciatoia `#`, rimossa. Capitoli 7 e 15.

modalità di permesso
:   Cosa Claude può fare senza chiedere. `Shift+Tab` gira tra auto, Manual, Accept edits e Plan; `dontAsk` e `bypassPermissions` si scelgono con `--permission-mode`. Come `defaultMode`, `auto` e `bypassPermissions` valgono solo in `~/.claude/settings.json`. Capitoli 2 e 11.

`/model`
:   Mostra i modelli del tuo piano e cambia quello attivo. Alias: `opus`, `sonnet`, `haiku`, `fable`, `opusplan`. Capitoli 1 e 2.

## O

openpyxl
:   La libreria Python che scrive file Excel, formule comprese. Capitolo 5.

Opus
:   Claude Opus, alias `opus`; Opus 5.5 è il default da settembre 2026. `opusplan` usa Opus in Plan Mode e Sonnet per eseguire. Capitolo 2.

## P

`/permissions`
:   Le regole attive, con le schede Allow, Ask, Deny e Recently denied; ogni regola mostra il file da cui arriva. Capitolo 11.

Plan Mode
:   Claude legge e propone un piano senza modificare nulla finché non approvi. Ci entri con `Shift+Tab`, `/plan` o `--permission-mode plan`; `Ctrl+G` apre il piano nell'editor. Capitoli 3 e 4.

plugin
:   Una cartella che impacchetta skill, agent, hook e server MCP. In `.claude-plugin/` va solo il manifest `plugin.json`; i componenti stanno nella radice. Il `name` diventa il prefisso (`/cc-lab-toolkit:report-pdf`). Si gestisce con `/plugin`, si prova con `--plugin-dir`, si controlla con `claude plugin validate`, si misura con `claude plugin eval`. Capitolo 14.

prompt injection
:   Istruzioni per il modello nascoste in un contenuto esterno letto da un tool, come una issue o una pagina web. Capitolo 13.

## R

RDS
:   Il database gestito di AWS; il Photogallery usa MariaDB, lo stesso motore di Sail. Capitolo 23.

regole allow, ask e deny
:   Eccezioni alla modalità, con la sintassi `Tool(specificatore)`: `Bash(python -m pytest *)`, `Read(./.env)`, `mcp__github__*`. L'ordine è deny, ask, allow. Una regola `Bash` confronta il testo del comando, non il programma. Capitolo 11.

`REVIEW.md`
:   Le istruzioni per Code Review su GitHub: cosa è Important, quanti Nit, cosa ignorare, cosa controllare sempre. Capitolo 22.

review multi-LLM (cross-LLM review)
:   Lo stesso changeset e lo stesso prompt a modelli diversi (Claude, Gemini, Codex, Kimi), con i risultati aggregati per consenso. Capitolo 22.

`/rewind`
:   Riporta codice, conversazione o entrambi a un punto precedente, anche con `Esc Esc`. Non annulla quello che ha fatto un comando `Bash`. Capitolo 15.

## S

Sanctum
:   Il pacchetto Laravel dei token API; nel Photogallery ogni mutazione controlla l'ability del token e la policy. Capitoli 17 e 19.

sandbox
:   Il limite che il sistema operativo impone ai comandi di shell e ai loro processi: scrittura nella cartella di lavoro, lettura quasi ovunque salvo i percorsi negati, rete attraverso un proxy con una lista di domini. Seatbelt su macOS, bubblewrap e socat su Linux e WSL 2, nessun supporto su Windows nativo. `Read`, `Edit`, hook e server MCP ne restano fuori. Si accende con `/sandbox`. Capitoli 2 e 11.

scope
:   Dove vale una configurazione. Per un server MCP: `local` (default), `project` (`.mcp.json` in Git, da approvare al primo avvio) e `user`. Per un plugin: user, project, local. Capitoli 13 e 14.

SDD (Spec Driven Development)
:   Il metodo del Photogallery: il codice discende da `docs/REQUIREMENTS.md`, `docs/DESIGN.md` e `docs/TASKS.md` (124 task in 14 fasi), scritti e approvati prima. Capitoli 17 e 18.

sessione
:   Una conversazione dall'avvio all'uscita. `/resume` (alias `/continue`) la riprende. Capitoli 1 e 15.

sessione in background
:   Una sessione che lavora senza occupare il terminale: `claude --bg --name <nome> "<prompt>"` o `/background`. Prima di modificare file passa in un worktree, a fine lavoro committa e pusha. Si gestisce dall'agent view e con `claude attach`, `logs`, `stop`, `rm`. Capitolo 20.

`settings.json`
:   Le impostazioni: `~/.claude/settings.json` (tutti i progetti), `.claude/settings.json` (team, in Git), `.claude/settings.local.json` (solo tu, fuori da Git), più le managed settings dell'organizzazione. Capitolo 11.

skill
:   Una cartella con `SKILL.md` ed eventuali script e riferimenti. Nome e descrizione restano sempre in contesto, il corpo si carica quando serve: la richiami con `/nome` o Claude la sceglie dalla descrizione, che va scritta come un trigger. `/skills` le elenca, `/reload-skills` le ricarica. Capitolo 9.

skill-creator
:   La skill che crea altre skill con una conversazione guidata. Capitolo 9.

`/skill-doctor`
:   Quanto contesto occupa e quanto viene usata ogni skill. Capitolo 15.

SOLID
:   I cinque principi della progettazione a oggetti, nel `CLAUDE.md` del Photogallery con esempi presi dal suo codice. Capitolo 18.

Sonnet
:   Claude Sonnet, alias `sonnet`: più veloce e meno costoso di Opus. Capitolo 2.

spec-critic
:   Il subagent che rilegge le spec come un revisore ostile, a caccia di buchi di sicurezza e requisiti senza task. Capitolo 18.

`/subtask`
:   Un subagent che eredita l'intera conversazione. Capitolo 10.

Superpowers
:   Il plugin di Jesse Vincent con skill per brainstorming, sviluppo guidato da subagent, debugging sistematico e TDD. Si installa con `/plugin install superpowers@claude-plugins-official`. Capitoli 8 e 16.

## T

task atomico
:   Un task che porta il progetto da uno stato coerente al successivo e si chiude con un commit. Nel Photogallery ha un ID (`T031`), le sezioni di `DESIGN.md` da leggere e criteri verificabili. Capitoli 16 e 18.

task orfano
:   Una feature spuntata ma rimasta a metà: endpoint vuoto, componente mai importato. Si decide con le tre D: Delete, Complete, Document and defer. Capitolo 22.

`/tasks`
:   I subagent e i lavori in background della sessione; `Ctrl+X Ctrl+K` li ferma tutti. Capitolo 10.

token
:   L'unità di testo dei modelli, più o meno un pezzo di parola. Contesto, limiti e costi si misurano in token. Capitolo 1.

tool
:   Una funzione descritta al modello con nome, descrizione e schema. Il modello chiede la chiamata (`tool_use`), l'harness la esegue e risponde con un `tool_result`. I principali: `Read`, `Edit`, `Write`, `Bash` (che su macOS, Linux e WSL fa anche le ricerche), `WebSearch`, `WebFetch`, `Agent`, i tool MCP. `Ctrl+O` mostra le chiamate. Capitolo 2.

tool search
:   All'avvio Claude Code carica solo i nomi dei tool MCP e recupera le definizioni quando servono. Capitolo 13.

## U

ultrareview
:   La review multi-agent nel cloud, in research preview: `/code-review ultra` o `claude ultrareview`. Serve un account claude.ai; su Pro e Max tre esecuzioni gratuite, poi crediti. Capitolo 22.

`ultrathink`
:   Scritto in un prompt, alza il ragionamento per quel messaggio soltanto. "think hard" non ha effetto speciale. Capitoli 2 e 3.

`/usage`
:   Cosa consuma i limiti del piano, per skill, subagent, plugin e server MCP. `/cost` e `/stats` sono suoi alias. Capitoli 1 e 15.

## V

vibecoding
:   Andare dritti al codice a forza di prompt, senza spec né piano. Capitolo 17.

visual companion
:   La parte della skill di brainstorming di Superpowers che genera mockup HTML e li aggiorna mentre li commenti. Capitolo 16.

## W

wave
:   Un gruppo di fasi del piano eseguibili in parallelo su track che non condividono file. Capitoli 19 e 20.

wave review
:   La review di fine wave fatta da più agent in parallelo, ognuno su un aspetto diverso. Capitolo 19.

worker
:   Il processo che esegue i job di una coda: nel Photogallery la tabella `jobs` in sviluppo, SQS in produzione. Capitoli 21 e 23.

worktree
:   Una seconda cartella di lavoro dello stesso repository, con il suo branch. `claude --worktree <nome>` la crea in `.claude/worktrees/<nome>`; `.worktreeinclude` elenca i file ignorati da copiare; `"baseRef": "head"` fa partire dall'`HEAD` locale; `isolation: worktree` ne dà uno temporaneo a ogni istanza di un subagent. Capitolo 20.

WSL 2
:   Il Linux di Windows, necessario per la sandbox; WSL 1 non è supportato. Capitoli 1 e 2.
