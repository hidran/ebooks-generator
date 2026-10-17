# Appendice E. Changelog

Le modifiche al libro, dalla più recente. La prima voce descrive questa edizione, la seconda riassume cosa è cambiato in Claude Code nei cinque mesi tra le due edizioni, la terza è la scheda della prima edizione. In fondo trovi come segnalare un errore.

## E.1 Seconda edizione, ottobre 2026

Il testo è allineato alla documentazione ufficiale consultata il 17 ottobre 2026, quando l'ultima versione di Claude Code era la 2.1.302 (16 ottobre) e il modello predefinito Claude Opus 5.5.

### Capitoli nuovi

Sei capitoli in più, tutti nati dalle lezioni dell'aggiornamento di ottobre del mio corso su Claude Code:

- Capitolo 2, Dal modello all'agente: tool, loop agentico, permessi e sandbox.
- Capitolo 11, Permessi, modalità e sandbox.
- Capitolo 12, Hook.
- Capitolo 13, MCP. La prima edizione lo prometteva per un aggiornamento successivo.
- Capitolo 14, Plugin e marketplace, compreso `claude plugin eval`.
- Capitolo 15, Contesto e memoria sotto controllo.
- Capitolo 20, Wave in parallelo con worktree, `/goal` e agent view.

I capitoli dall'11 al 15 formano la nuova Parte IV, Controllare e automatizzare, e lavorano tutti sullo stesso progetto di laboratorio.

### Contenuti accorpati

Il capitolo 22 unisce la QA pre-deploy e la review multi-LLM della prima edizione alla review integrata di Claude Code: `/code-review` con i livelli di effort, `--fix` e `--comment`, il file `REVIEW.md` per Code Review su GitHub e ultrareview nel cloud. Il secondo modello resta, ma solo per le parti critiche.

I capitoli 8 e 9 seguono la fusione tra custom command e skill: il capitolo 8 presenta il formato `.claude/commands/`, il 9 parte dal fatto che comandi e skill sono un solo sistema. Nel capitolo 10 gli agent della community arrivano dai plugin invece che da un `git clone` in `~/.claude/`.

### La nuova numerazione

Le parti sono sei. La vecchia Parte IV (landing page) è diventata la Parte V, la vecchia Parte V (Photogallery) la Parte VI. I numeri dei paragrafi seguono il capitolo: il vecchio §13.3 è il §19.3.

| Seconda edizione | Prima edizione | Titolo |
|---|---|---|
| 1 | 1 | Cos'è Claude Code |
| 2 | nuovo | Dal modello all'agente: tool, loop agentico, permessi e sandbox |
| 3 | 2 | I primi prompt utili |
| 4 | 3 | Analizzare un CSV con Plan Mode |
| 5 | 4 | Da CSV a Excel, report tabellari con Python |
| 6 | 5 | Grafici, dashboard e report PDF |
| 7 | 6 | CLAUDE.md, la memoria del progetto |
| 8 | 7 | Custom command e il plugin Superpowers |
| 9 | 8 | Skill, da comando a capacità riusabile |
| 10 | 9 | Agent e subagent, quando usare cosa |
| 11 | nuovo | Permessi, modalità e sandbox |
| 12 | nuovo | Hook, automazioni deterministiche |
| 13 | nuovo | MCP, collegare Claude Code ai servizi esterni |
| 14 | nuovo | Plugin e marketplace, impacchettare skill, agent e hook |
| 15 | nuovo | Contesto e memoria sotto controllo |
| 16 | 10 | Una landing page dall'idea al deploy su Firebase |
| 17 | 11 | Photogallery, dal prompt alle specifiche |
| 18 | 12 | Spec Driven Development |
| 19 | 13 | Esecuzione e code review, dai primi task alla wave review |
| 20 | nuovo | Wave in parallelo con worktree, /goal e agent view |
| 21 | 14 | Feature in corsa |
| 22 | 15 | QA pre-deploy, /code-review e review multi-LLM |
| 23 | 16 | Deploy su AWS con CloudFormation |

Le appendici restano cinque, dalla A alla E, con lo stesso ordine.

### Gli aggiornamenti, capitolo per capitolo

I capitoli nuovi sono scritti per la versione attuale. Negli altri questi sono i cambiamenti che toccano i comandi o il codice.

- Capitolo 1. L'installazione passa dall'installer nativo (`curl -fsSL https://claude.ai/install.sh | bash`, su Windows `irm https://claude.ai/install.ps1 | iex`), che si aggiorna da solo. Homebrew e WinGet sono alternative con aggiornamento manuale; npm è un'opzione avanzata e richiede Node.js 22 o successivo. Entrano `claude doctor` e `claude update`. `/usage` prende il posto di `/cost`, che ne è un alias dalla versione 2.1.118 (aprile 2026), e `/vim` lascia il posto a `/config`, che accetta anche la forma `chiave=valore`. La scorciatoia `#` per la memoria era già stata rimossa nella 2.0.70 (dicembre 2025): la prima edizione la presentava ancora. Le sessioni partono in auto mode.
- Capitolo 3. Plan Mode si attiva con `Shift+Tab`, con `/plan` o con `claude --permission-mode plan`, e l'approvazione offre `Yes, and use auto mode`. `Ctrl+G` apre il piano nell'editor. Per ragionare di più si alza l'effort con `/effort`; "think hard" non è una parola chiave, `ultrathink` vale per un solo prompt.
- Capitolo 4. Stessi aggiornamenti su Plan Mode; per i file grandi entrano `/context` e `/compact` con le istruzioni su cosa conservare.
- Capitoli 5 e 6. Cambia soprattutto la prosa. Nel capitolo 6 la skill frontend-design si installa come plugin dal marketplace ufficiale (`frontend-design@claude-plugins-official`).
- Capitolo 7. I livelli di `CLAUDE.md` sono quattro (organizzazione, utente, progetto, locale). Entrano le regole in `.claude/rules/` con `paths:`, la memoria automatica e la lettura nativa di `AGENTS.md` dalla versione 2.1.277. Il limite consigliato è sotto le duecento righe.
- Capitolo 8. I custom command sono confluiti nelle skill: `.claude/commands/` funziona ancora, ma per il lavoro nuovo si usa `.claude/skills/<nome>/SKILL.md`. Superpowers si installa dal marketplace ufficiale con `/plugin install superpowers@claude-plugins-official`; il repository indicato nella prima edizione non era quello del plugin, che sta in `obra/superpowers`.
- Capitolo 9. La description, insieme a `when_to_use`, viene troncata oltre 1.536 caratteri. Lo skill-creator si installa da `claude-plugins-official`, `/skill-doctor` mostra quanto contesto pesa ogni skill e dalla versione 2.1.218 una skill con `context: fork` gira in background.
- Capitolo 10. La procedura guidata di `/agents` non esiste più dalla versione 2.1.198: l'agent si crea chiedendolo a Claude o scrivendo il file in `.claude/agents/`. L'esempio è diventato `laravel-controller-reviewer`, al posto del `nest-controller-reviewer` della prima edizione. Il tool `Task` si chiama `Agent`. I subagent girano in background, si seguono con `/tasks` e si fermano con `Ctrl+X Ctrl+K`; `/subtask` delega un compito che ha bisogno di tutta la conversazione.
- Capitolo 16. Lo stack è quello reale del repository: React 19, Vite 6, Tailwind CSS 4.2 e Vitest 4, al posto di React 18 e Vite 5.
- Capitolo 17. Lo stack della Photogallery è quello del repository companion: Laravel 13 come API REST sotto `/api/v1`, Filament v5 per l'admin, React 19 con Vite 6 e Tailwind CSS v4 per la SPA, token Sanctum. NestJS resta solo come alternativa scartata durante la scelta dello stack, e la sezione 17.1 spiega perché.
- Capitolo 18. I tre file stanno in `docs/REQUIREMENTS.md`, `docs/DESIGN.md` e `docs/TASKS.md`, non più in `.spec/`, e il `CLAUDE.md` del progetto è quello del repository. Il testo distingue i 112 task in 13 fasi del branch del capitolo dai 124 task in 14 fasi di `main`. I vincoli che non possono saltare passano a permessi, hook e `/goal`.
- Capitolo 19. Gli esempi di review riguardano controller, policy e Form Request di Laravel. I subagent in parallelo condividono il working tree, quindi i task paralleli sullo stesso codice vanno nei worktree del capitolo 20.
- Capitolo 21. I riferimenti a fasi, wave e task (T070, T121, la Fase 6.5) seguono il `docs/TASKS.md` del repository companion.
- Capitolo 22. `/review` è un alias di `/code-review` dalla versione 2.1.223. `REVIEW.md` personalizza Code Review su GitHub (piani Team ed Enterprise) ma non il comando locale, che legge solo `CLAUDE.md`. Ultrareview si lancia con `/code-review ultra` o con `claude ultrareview`.
- Capitolo 23. Il backend in container è Laravel invece di NestJS, con `config:cache` lanciato all'avvio del container, e il database è RDS MariaDB invece di MySQL. I comandi di deploy passano da una regola `ask` in `.claude/settings.json`.

In tutto il libro il modello di riferimento è Claude Opus 5.5 con un milione di token di contesto. Ho tolto le figure con un'interfaccia superata (Sonnet 4.6 in `/model`, `/cost`, il wizard di `/agents`).

### I branch companion tengono i vecchi numeri

I branch dei repository sono stati creati per la prima edizione e non li ho rinominati, per non rompere i link già in giro. Il testo cita sempre il nome esatto; questa è la corrispondenza completa.

| Branch | Repository | Capitolo |
|---|---|---|
| `book/cap-10-1-mockups`, `book/cap-10-2-spec`, `book/cap-10-3-execution`, `book/cap-10-5-deploy-ready` | `fluentaipro-claude-landingpage` | 16 |
| `book/cap-11-prompts-and-spec` | `claude-code-book-photogallery` | 17 |
| `book/cap-12-sdd-three-files` | `claude-code-book-photogallery` | 18 |
| `book/cap-13-wave-1-backend`, `book/cap-13-wave-2-api` | `claude-code-book-photogallery` | 19, punto di partenza del 20 |
| `book/cap-14-phases-complete` | `claude-code-book-photogallery` | 21, punto di partenza del 22 |
| `book/cap-15-post-review-fixes` | `claude-code-book-photogallery` | 22, coincide con `main` |

La prima edizione citava anche branch di partenza per gli esercizi nel repository `claude-code-book-snippets` (`cap-01-hello-claude`, `cap-03-csv-analysis` e altri), che non sono mai stati pubblicati: il repository ha solo `main`, con una cartella di prompt per capitolo. In questa edizione ogni esercizio parte da qualcosa che crei tu, e i dati della Parte II li genera lo script `genera_dati.py` del capitolo 4.

Il capitolo 23 non ha ancora un branch: `book/cap-16-aws-deploy` arriverà quando il deploy su AWS del repository sarà completo.

### Il testo

Ho riscritto la prosa di ogni capitolo, togliendo frasi a effetto, elenchi in grassetto e riepiloghi che ripetevano il capitolo. L'apertura con quello che imparerai e la chiusura con riepilogo ed esercizio restano, più brevi, e ogni esercizio ha una condizione di completamento chiara. I riquadri sono di cinque tipi, descritti in "Come leggere il libro".

Nell'Appendice D ho controllato tutti i link e ho tolto quelli che non potevo verificare: la tabella dei modelli (ora i modelli sono nel capitolo 2), newsletter, libri consigliati, strumenti alternativi e il vecchio indirizzo della documentazione su `docs.anthropic.com`. Al posto dei contatti personali ci sono le issue del repository degli snippet.

## E.2 Cosa è cambiato in Claude Code tra maggio e ottobre 2026

La prima edizione corrisponde più o meno alle versioni 2.1.128-2.1.158 di maggio 2026. Qui sotto ci sono i cambiamenti che toccano il libro e che la prima edizione non trattava, con versione, data e capitolo. Date e versioni vengono da changelog e digest settimanale; dove manca il giorno indico il mese o la settimana del digest.

- Maggio, 2.1.139: `/goal`, Claude continua a lavorare finché una condizione non è vera. Capitolo 20.
- 9 giugno, 2.1.170: arriva Fable 5, il modello più capace, mai attivo per default. Capitolo 2.
- Giugno, settimana 24: un subagent può lanciare altri subagent, fino a cinque livelli nelle catene in background. Capitolo 10.
- Giugno, settimana 25: `/config chiave=valore`, e le regole di permesso che guardano i parametri di un tool, come `Agent(model:opus)`. Capitoli 1 e 11.
- Giugno, settimana 26: la modalità shell `!` riceve una risposta da Claude, le richieste di permesso dei subagent in background compaiono nella sessione principale, arrivano `claude mcp login` e `logout`. Capitoli 1, 10 e 13.
- 30 giugno, 2.1.197: Sonnet 5 diventa per poco il modello predefinito dei piani Pro e Team Standard. Capitolo 2.
- 1 luglio, 2.1.198: rimossa la procedura guidata di `/agents`. Capitolo 10.
- Luglio, settimana 27: i subagent girano in background per default. Capitolo 10.
- Luglio, settimana 28: `/doctor` diventa un controllo del setup che sa anche correggere. Capitolo 15.
- 17 luglio, 2.1.212: `/fork` copia la conversazione in una sessione in background, `/subtask` lancia il subagent con tutta la conversazione, `/background` stacca la sessione; tutto si segue dall'agent view (`claude agents`). Capitoli 10, 15 e 20.
- Luglio, 2.1.218: le skill con `context: fork` girano in background. Capitolo 9.
- 24 luglio, 2.1.219: Opus 5 diventa il modello predefinito. Capitolo 2.
- 4 agosto, 2.1.222: rimosso Ultraplan; per pianificare resta Plan Mode. Capitolo 3.
- 6 agosto, 2.1.223: `/review` diventa un alias di `/code-review`; ultrareview si lancia con `/code-review ultra`. Capitolo 22.
- 11 agosto, 2.1.228: auto mode diventa la modalità iniziale per Pro, Max e Team su macOS, Linux e WSL, e il 14 agosto (2.1.233) su Windows. Capitoli 2 e 11.
- Agosto, settimana 33: nelle sessioni interattive i subagent lanciati da Claude partono in fork mode, in background. Capitolo 10.
- 1 settembre, 2.1.257: Fable 5.1. Capitolo 2.
- 11 settembre, 2.1.269: `claude plugin eval` misura un plugin contro una baseline senza plugin. Capitolo 14.
- 18 settembre, 2.1.277: Claude Code legge `AGENTS.md` quando manca un `CLAUDE.md`. Capitolo 7.
- 22 settembre, 2.1.280: Opus 5.5 diventa il modello predefinito su tutti i piani in abbonamento. Capitolo 2.
- 25 settembre, 2.1.283: auto mode si estende ai provider di terze parti, ed entra `/doctor prompt-audit`. Capitoli 11 e 15.
- 28 settembre, 2.1.284: auto mode per ogni piano e provider, e Sonnet 5.5. Capitoli 2 e 11.
- Inizio ottobre, 2.1.287: le Claude Mods, moduli di hook in JavaScript. Capitolo 14, solo come cenno.
- 7 ottobre, 2.1.293: Haiku 5.5. Capitolo 2.
- 16 ottobre, 2.1.302: i subagent in fork diventano il default anche in `claude -p`, nell'Agent SDK, nell'app desktop e in VS Code. Capitolo 10.

## E.3 Prima edizione, maggio 2026

Prima pubblicazione su Amazon KDP, in eBook e in paperback stampato su richiesta.

Il libro aveva 16 capitoli, circa 90.000 parole, in cinque parti: Fondamenta, Analisi dati, Estendere Claude Code, Landing page e Photogallery. Le appendici erano le stesse cinque di oggi. C'erano più di 50 figure catturate da Claude Code e due repository companion, Photogallery e snippet.

I modelli di riferimento erano Opus 4.7, Sonnet 4.6 e Haiku 4.5; le versioni di Claude Code di quel periodo erano le 2.1.1xx.

La scheda indicava come stack della Photogallery NestJS 10, Prisma 5, MySQL 8, React 18 e TanStack Query. Era l'ipotesi di partenza del capitolo sulle specifiche, non il progetto del repository companion, che usa Laravel 13, Filament v5 e React 19: la seconda edizione ha corretto il testo di conseguenza.

La prima edizione annunciava un aggiornamento con un capitolo su MCP, se la specifica si fosse stabilizzata. Quel capitolo è il 13 di questa edizione.

## E.4 Segnalare un errore

Apri una issue nel repository `github.com/hidran/claude-code-book-snippets` con l'etichetta `errata`, e scrivi:

- la pagina (eBook) o il capitolo e la sezione (paperback);
- cosa dice il libro;
- cosa è successo davvero sulla tua installazione, con l'output di `claude --version`.

Le correzioni verificate entrano nella revisione successiva e in questa appendice. Se sei d'accordo, chi ha fatto la segnalazione compare nei ringraziamenti.

Non inseguo ogni novità minore di Claude Code. Aggiorno il libro quando un cambiamento tocca il modo di lavorare: un comando rinominato o rimosso, un modello nuovo o ritirato, un link rotto, un procedimento che ne ha uno migliore. Le funzioni nuove che non cambiano il flusso restano fuori, fino a quando non lo cambiano. Su Kindle ricevi le nuove versioni attivando gli aggiornamenti automatici dei libri, come spiegato in "Come leggere il libro".
