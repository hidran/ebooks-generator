# Capitolo 10. Agent e subagent, quando usare cosa

## Cosa imparerai

Impari a scrivere un subagent, cioè un file Markdown in `.claude/agents/` con il suo frontmatter e il suo system prompt, e a farlo scrivere a Claude. Vedi i subagent che Claude Code usa già da solo, come girano in background e come ti chiedono i permessi. Alla fine hai una regola pratica per scegliere tra CLAUDE.md, custom command, skill, agent, hook e server MCP, e sai quando ha senso far lavorare più agent insieme.

**Prerequisiti**: i capitoli 8 e 9, perché qui confronto continuamente gli agent con custom command e skill.

Nei capitoli precedenti hai aggiunto pezzi a Claude Code. Il `CLAUDE.md` ricorda le convenzioni del progetto (capitolo 7), i custom command trasformano i prompt ricorrenti in scorciatoie con la barra (capitolo 8), le skill portano procedure riutilizzabili dentro la sessione (capitolo 9). Tutte queste cose vivono nello stesso posto: la sessione principale, con la sua cronologia, i file già letti, le decisioni prese un'ora fa.

Se chiedi una code review mentre Claude è ancora in mezzo all'implementazione, la review si porta dietro tutto quel carico. Il contesto è rumoroso e Claude ha già un'opinione sul codice, perché l'ha scritto lui. Un agent risolve proprio questo: è un'altra istanza di Claude, con un contesto suo che parte vuoto. Riceve il compito, lo esegue per conto suo e ti restituisce solo le conclusioni. Se una skill è un manuale che Claude consulta mentre lavora, un agent è un collega a cui passi un compito: lo fa alla sua scrivania e ti riporta il risultato.

## 10.1 Cos'è un subagent

Un **subagent** è un'istanza di Claude Code specializzata che riceve un solo compito, lo svolge in un contesto separato e restituisce il risultato alla sessione principale. Nel capitolo 2 l'hai visto dal lato del loop: il tool `Agent` apre un secondo loop con un contesto tutto suo. Qui lo guardi dal lato di chi lo configura. Nella documentazione e nel libro "agent" e "subagent" indicano la stessa cosa; uso "subagent" quando conta il rapporto con la sessione che lo lancia.

Tre caratteristiche lo distinguono da tutto quello che hai visto finora.

### Contesto isolato

Il subagent parte da zero. Non ha visto la conversazione, non ha letto i file che Claude ha aperto nell'ultima ora, non sa quali compromessi avete accettato. Quello che sa è il compito che gli arriva e quello che legge da solo.

È questo il vantaggio principale. Quando la sessione principale è piena di file letti, codice scritto ed errori analizzati, aggiungere una review o un'analisi lunga significa mescolare tutto. Il subagent fa il suo lavoro nel suo contesto, e alla sessione principale arriva un rapporto di qualche centinaio di parole invece di migliaia di righe di letture.

### Un system prompt suo

Ogni agent ha un system prompt che dice chi è, cosa deve fare e come deve rispondere: un revisore di codice senior, un analista di dati, un auditor di sicurezza. Un Claude generico a cui chiedi la stessa cosa a metà conversazione parte da un contesto diverso, già orientato dal resto del lavoro. L'agent parte dal suo ruolo e basta.

### Tool limitati

Un agent può avere solo una parte dei tool. Un revisore con `Read` ma senza `Edit`, `Write` e `Bash` non può modificare per sbaglio i file che sta analizzando, nemmeno se il suo prompt è scritto male o se fraintende il compito. Meno tool significa anche meno sorprese: un agent di sola lettura, nel peggiore dei casi, ti restituisce un rapporto sbagliato.

### Quando conviene

Quattro situazioni tornano spesso.

La prima è la code review: un agent che non ha seguito l'implementazione non sa quanto ti è costata quella funzione, e non ha remore a dirti che va riscritta. La seconda è la ricerca nel codebase: l'agent legge decine di file e a te arriva il riassunto ("l'autenticazione usa token Sanctum, l'ability si controlla nel controller con `tokenCan()`"), non il tracciato delle letture. La terza sono i compiti paralleli: sicurezza, performance e copertura dei test in tre agent contemporaneamente, con un tempo totale vicino a quello dell'analisi più lunga. La quarta sono i compiti rumorosi, come caricare un CSV grande o leggere decine di file di configurazione: l'output intermedio resta nel contesto dell'agent.

### Skill e agent a confronto

| | Skill | Agent |
|---|---|---|
| Dove gira | Nel contesto principale | In un contesto separato |
| Cosa sa della sessione | Tutto | Niente, parte da zero |
| Tool | Gli stessi della sessione | Una lista ristretta, se la scrivi |
| Uso tipico | Una procedura da seguire mentre lavori | Un compito da delegare |

Le due cose si combinano. Nel capitolo 9 hai visto che una skill con `context: fork` gira in un subagent, e il campo `agent` dice quale. Al contrario, un agent può precaricare delle skill con il campo `skills` del suo frontmatter.

## 10.2 I subagent che hai già

Prima di scriverne uno tuo, sappi che Claude Code ne usa già alcuni, e li lancia da solo quando servono.

| Subagent | Cosa fa | Tool |
|---|---|---|
| `Explore` | Esplora il codebase per rispondere a una domanda | Sola lettura |
| `Plan` | Fa ricerca nel codice durante Plan Mode | Sola lettura |
| `general-purpose` | Compiti di più passi che richiedono anche di agire | Tutti |

Explore è quello che vedrai più spesso. Usa lo stesso modello della sessione principale e accetta tre livelli di profondità: quick, medium e very thorough. Puoi chiederlo esplicitamente:

```text
usa l'agent Explore, livello very thorough, per capire come la Photogallery gestisce il caricamento delle foto: dal controller fino ai job in coda. Riportami i file coinvolti e il flusso in dieci righe
```

Explore e Plan partono senza `CLAUDE.md`: ricevono la domanda e leggono il codice, senza le tue istruzioni di progetto. Se una convenzione è indispensabile per rispondere, scrivila nel prompt. Ci sono anche subagent di servizio come `statusline-setup` e `claude-code-guide`, che Claude usa per configurare la status line e per rispondere a domande su Claude Code stesso. Se vuoi togliere Explore e Plan, la variabile d'ambiente `CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS=1` li rimuove.

::: {.callout .callout-deep-dive}
[Sotto il cofano]{.callout-title}

Ogni subagent parte da una chiamata al tool `Agent`. Fino alla versione 2.1.63 il tool si chiamava `Task`, e lo trovi ancora così in articoli e configurazioni vecchie: `Task(...)` funziona come alias nelle regole di permesso. Le regole possono anche guardare i parametri della chiamata, per esempio `Agent(model:opus)` per i subagent lanciati su Opus. Lo usiamo nel capitolo 11.
:::

## 10.3 Anatomia di un agent

Un agent è un file Markdown con un frontmatter YAML. Il nome del file è libero, il nome dell'agent lo decide il campo `name`. Claude Code li cerca in più posti, e se due hanno lo stesso nome vince quello più in alto in questa lista:

1. le impostazioni gestite dall'organizzazione;
2. il flag `--agents` della riga di comando, che accetta una definizione in JSON per una sola sessione;
3. `.claude/agents/` nel progetto, cercata nelle cartelle superiori fino all'inizio del repository e nelle sottocartelle;
4. `~/.claude/agents/` nella tua home;
5. la cartella `agents/` dei plugin installati.

Nella pratica scegli tra due posti. Se l'agent conosce le convenzioni, i servizi e i percorsi del progetto, va in `.claude/agents/` e lo committi: tutto il team lo riceve con il repository. Se è una competenza trasversale, un revisore generico o un esperto di Python, va in `~/.claude/agents/` e lo ritrovi in ogni progetto. È la stessa logica delle skill.

Un revisore generico, `~/.claude/agents/code-reviewer.md`, ha questa forma:

```markdown
---
name: code-reviewer
description: Revisiona il codice per bug, convenzioni del progetto e test mancanti. Usalo dopo modifiche significative, prima del commit.
tools: Read, Grep, Glob
model: sonnet
---

Sei un revisore di codice senior per questo progetto.

## Il compito
Revisiona le modifiche che ti vengono indicate. Concentrati su:
- bug e casi limite non gestiti
- rispetto delle convenzioni del progetto (vedi CLAUDE.md)
- copertura dei test
- problemi di performance
- leggibilità

## Formato della risposta
- Punti di forza (al massimo tre)
- Problemi importanti, con file:riga e correzione proposta
- Suggerimenti minori (facoltativi)
- Verdetto: APPROVED oppure NEEDS_CHANGES

## Vincoli
- Non modificare file.
- Al massimo 300 parole in tutto.
```

### Il frontmatter

Solo `name` e `description` sono obbligatori. I campi composti da più parole sono in camelCase.

`name` è l'identificativo, in minuscolo con i trattini, al massimo 256 caratteri e senza i due punti. È il nome che usi per chiamarlo: "usa l'agent code-reviewer su...".

`description` è il campo che conta di più. Claude legge la description di tutti gli agent disponibili e decide da quella se delegare un compito, anche quando non nomini nessun agent. Scrivila come la regola di un router: cosa fa e quando usarlo. "Aiuta con il codice" non serve a niente. "Revisiona il codice per bug, convenzioni e test mancanti. Usalo dopo modifiche significative, prima del commit" dice a Claude esattamente quando tirarlo in ballo. Come per le skill, la description resta nel contesto di ogni sessione anche quando l'agent non lavora, quindi tienila corta.

`tools` è la lista dei tool permessi. Se la ometti, l'agent eredita tutti i tool della sessione, compresi quelli dei server MCP. Specificarla è quasi sempre la scelta giusta. `disallowedTools` fa il contrario: parti da tutto e togli qualcosa, per esempio `Bash`. Nelle build native per macOS, Linux e WSL `Grep` e `Glob` di solito non ci sono, perché Claude cerca nei file attraverso `Bash`: lì un agent con `Read, Grep, Glob` lavora di fatto con il solo `Read`. Basta per revisionare i file che gli indichi. Non aggiungere `Bash` solo per dargli la ricerca, perché con una shell l'agent può anche scrivere.

`model` sceglie il modello: `sonnet`, `opus`, `haiku`, `fable`, un ID completo come `claude-opus-5-5`, oppure `inherit` per usare lo stesso modello della sessione. Un revisore tecnico sta bene su Sonnet, un agent che progetta la struttura di una feature può meritare Opus, uno che riassume log va su Haiku. <!-- VERIFY: valore di default di model quando il campo è omesso (inherit?) -->

Gli altri campi li userai meno spesso, ma conviene sapere che esistono:

| Campo | A cosa serve |
|---|---|
| `permissionMode` | La modalità di permesso dell'agent: `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan`, `manual` (capitolo 11) |
| `maxTurns` | Il numero massimo di giri del loop prima che l'agent si fermi |
| `effort` | Il livello di ragionamento, da `low` a `max` |
| `skills` | Le skill da precaricare nel contesto dell'agent |
| `mcpServers` | I server MCP a disposizione dell'agent (capitolo 13) |
| `hooks` | Hook che valgono solo mentre l'agent lavora (capitolo 12) |
| `memory` | Una memoria persistente dell'agent: `user`, `project` o `local` |
| `background` | Con `true` l'agent gira sempre in background |
| `isolation` | Con `worktree` l'agent lavora in un worktree Git temporaneo |
| `color` | Il colore con cui l'agent compare nell'interfaccia |

Due righe su `memory` e `isolation`, perché cambiano il comportamento più degli altri. Con `memory: project` l'agent ha una cartella `.claude/agent-memory/<agent>/` in cui annotare quello che impara da una volta all'altra; con `user` la cartella sta in `~/.claude/agent-memory/<agent>/`, con `local` in `.claude/agent-memory-local/<agent>/`, da tenere fuori da Git. Con `isolation: worktree` l'agent parte in un worktree temporaneo creato dal branch di default, così le sue modifiche non toccano la tua copia di lavoro; se non cambia niente, il worktree viene eliminato da solo. Lo riprendiamo nel paragrafo 10.8 e nel capitolo 20.

Per gli agent che arrivano da un plugin, `hooks`, `mcpServers` e `permissionMode` vengono ignorati: un plugin non può alzarsi i permessi da solo.

### Il corpo, cioè il system prompt

Tutto quello che sta sotto il frontmatter è il system prompt dell'agent. Un buon prompt ha quattro parti: chi è l'agent, cosa deve fare quando viene chiamato, come deve formattare la risposta, cosa non deve fare. Il formato della risposta è la parte che si trascura di più ed è quella che leggi tu, o che legge la sessione principale: un rapporto con file e riga si usa subito, un saggio di 800 parole no.

Una checklist finale, cioè le domande che l'agent deve farsi prima di rispondere, spesso separa un rapporto generico da uno utile. Claude la genera quando gli chiedi di scrivere l'agent: rileggila.

## 10.4 Creare un agent con Claude

Fino alla versione 2.1.197 il comando `/agents` apriva una procedura guidata per creare gli agent. Dalla 2.1.198, uscita il 1 luglio 2026, la procedura non c'è più: `/agents` stampa solo un promemoria che ti dice di chiedere a Claude o di modificare direttamente `.claude/agents/` e `~/.claude/agents/`. Se trovi tutorial con le schermate del menu "Create new agent", sono di prima di quella versione.

Il modo più veloce è chiedere a Claude di scrivere il file. Descrivi l'agent con precisione: cosa controlla, quali tool gli servono, quale modello, dove salvarlo. Per la Photogallery, il progetto della Parte VI, un revisore dei controller API Laravel si chiede così:

```text
crea un subagent di progetto chiamato laravel-controller-reviewer in .claude/agents/.
Fa la code review dei controller in backend/app/Http/Controllers/Api/V1/.

Per ogni controller che gli passo deve verificare:
1. ogni endpoint che riceve input usa una Form Request in app/Http/Requests/ e legge solo $request->validated()
2. esiste un test Pest in tests/Feature/Api/V1/ che chiama l'endpoint
3. le azioni sulle risorse di un utente passano da una Policy in app/Policies/
4. gli endpoint che modificano dati controllano l'ability del token Sanctum con tokenCan()
5. gli errori seguono l'envelope di docs/DESIGN.md §11.1

Tool: solo Read, Grep e Glob, deve leggere e non modificare.
Modello: sonnet, è una review tecnica.
Rapporto: una riga per problema con file:riga e correzione, poi il verdetto APPROVED o NEEDS_CHANGES. Massimo 300 parole.
```

Claude scrive `.claude/agents/laravel-controller-reviewer.md` con il frontmatter, il system prompt strutturato, la checklist e il formato del rapporto. Il risultato somiglia a questo:

```markdown
---
name: laravel-controller-reviewer
description: Revisiona i controller API Laravel in backend/app/Http/Controllers/Api/V1/ per validazione, test, policy, ability Sanctum ed envelope degli errori. Usalo dopo aver creato o modificato un controller, prima del commit.
tools: Read, Grep, Glob
model: sonnet
color: orange
---

Sei un revisore senior di API Laravel 13. Ricevi uno o più controller della Photogallery.

Per ogni metodo pubblico verifica:

1. L'input arriva da una Form Request in app/Http/Requests/<Risorsa>/ e il controller usa solo $request->validated().
2. Esiste un test Pest in tests/Feature/Api/V1/ che chiama l'endpoint, con almeno un caso di errore.
3. Le azioni sulle risorse di un utente sono autorizzate da una Policy in app/Policies/.
4. Gli endpoint che modificano dati controllano l'ability del token con tokenCan().
5. Le risposte usano una API Resource e gli errori seguono l'envelope di docs/DESIGN.md §11.1.

Prima di rispondere chiediti: ho aperto il test che cito? La riga che indico esiste davvero?

Formato del rapporto:
- una riga per problema: file:riga, problema, correzione proposta
- in fondo il verdetto: APPROVED oppure NEEDS_CHANGES

Non modificare file. Al massimo 300 parole.
```

<!-- TODO screenshot: il file .claude/agents/laravel-controller-reviewer.md aperto nell'editor, con frontmatter e system prompt visibili (sostituisce le vecchie figure del wizard /agents, rimosso in v2.1.198) -->

Puoi anche scriverlo a mano: una volta capita la struttura, fai prima a copiarne uno esistente e cambiarlo.

### Rivedere il file

Il primo file che Claude genera è un buon punto di partenza, quasi mai quello definitivo. Tre cose da controllare.

I percorsi. Claude a volte inserisce file che esistono solo nel progetto da cui è partito, o li inventa. Ogni percorso nel prompt deve esistere davvero, altrimenti l'agent perde giri a cercarlo.

La checklist. Aggiungi le verifiche che mancano e controlla che quelle che hai chiesto ci siano tutte, con lo stesso dettaglio. Nel revisore Laravel il punto delicato è il quarto: se Claude lo riassume in un generico "verifica l'autenticazione", un endpoint protetto da `auth:sanctum` ma senza `tokenCan()` passa la review. In quel caso riscrivi il punto a mano.

Il formato del rapporto. Decidi tu quanto deve essere lungo. Un rapporto di 500 parole per ogni controller non lo legge nessuno, una lista numerata di problemi con file e riga sì.

Se l'agent è di progetto, quando ti va bene committalo. Da quel momento è parte del repository come il `CLAUDE.md`, e `/doctor prompt-audit` lo controlla insieme a regole e skill quando cerchi istruzioni vecchie o in conflitto.

### Provarlo

Claude Code legge gli agent all'avvio della sessione. Se l'hai creato tu a mano a sessione aperta e Claude non lo trova, esci e rientra. <!-- VERIFY: se un file aggiunto in .claude/agents/ a sessione aperta viene caricato senza riavvio, ora che /agents non ricarica più nulla --> Per sapere quali agent vede, chiedilo:

```text
quali subagent hai a disposizione in questo progetto?
```

Anche `/context` li mostra, tra le voci che occupano spazio nel contesto. Poi chiama l'agent per nome:

```text
usa l'agent laravel-controller-reviewer per fare la review di backend/app/Http/Controllers/Api/V1/AlbumController.php
```

Claude lancia l'agent con il tool `Agent`. L'agent legge il controller, apre le Form Request in `app/Http/Requests/Album/`, cerca i test, e restituisce il rapporto alla sessione principale. Nella sessione vedi il rapporto, non le decine di letture che l'hanno prodotto; se vuoi vederle, `Ctrl+O` apre la trascrizione con le chiamate ai tool.

Se l'agent non parte quando chiedi una review senza nominarlo, il problema è quasi sempre la description: rendila più esplicita su quando usarlo.

::: {.callout .callout-prompt}
[Prompt riusabile]{.callout-title}

Sostituisci le parti tra parentesi quadre e incolla il prompt in Claude Code. Ottieni il file dell'agent pronto da rivedere.

```text
Voglio un agent per [descrizione del compito].

Persona: [es. senior TypeScript code reviewer, data scientist SaaS]
Input: [cosa riceve l'agent, es. un file controller, un dataset CSV]
Formato del rapporto: [es. problemi ordinati per gravità, con file:riga]
Tool consentiti: [es. Read, Grep, solo lettura]
Modello: [sonnet / opus / haiku / inherit]
Scope: [progetto / utente]

Crea l'agent in .claude/agents/ (o in ~/.claude/agents/ se è di livello utente).
```
:::

## 10.5 Background, permessi e /subtask

Nelle sessioni interattive i subagent che Claude lancia girano in background per default, e Claude non può chiedere di farli girare in primo piano. Mentre l'agent lavora, tu continui a scrivere nella sessione principale. Quando finisce, il suo rapporto arriva nella conversazione e Claude lo usa per proseguire. Da ottobre 2026 (versione 2.1.302) vale lo stesso anche in modalità `-p`, nell'SDK, nell'app desktop e in VS Code.

I comandi da ricordare sono tre. `/tasks` elenca quello che sta girando in background, con lo stato di ciascun lavoro. `Ctrl+X Ctrl+K` ferma tutti i subagent in background in un colpo. `Ctrl+B` manda in background un lavoro che sta occupando il turno, per esempio un comando `Bash` lungo; se usi tmux va premuto due volte.

Un subagent in background può avere bisogno di un permesso, per esempio per lanciare un comando che le tue regole mettono in `ask`. La richiesta non resta bloccata nel suo contesto: compare nella sessione principale, e rispondi lì come per qualunque altra conferma. Vale anche il contrario: le regole `deny` che scrivi nel capitolo 11 valgono anche per i subagent, quindi un agent non può fare quello che hai vietato alla sessione. <!-- VERIFY: le regole deny di settings.json si applicano ai subagent anche quando il loro permissionMode è bypassPermissions -->

Un subagent può lanciare a sua volta altri subagent. Le catene in background arrivano al massimo a cinque livelli, un limite che nella pratica non raggiungi: due livelli, un coordinatore che lancia dei revisori, coprono quasi tutti i casi utili.

### /subtask, quando serve il contesto

Un subagent normale parte da zero, ed è quello che vuoi per una review. A volte però vuoi delegare un pezzo di lavoro che dipende da quello che vi siete detti nell'ultima mezz'ora. Per questo c'è `/subtask`:

```text
/subtask scrivi i test Pest per i due casi limite di cui abbiamo appena parlato sull'upload, senza toccare il controller
```

`/subtask` lancia un subagent che eredita l'intera conversazione. Lavora in background come gli altri, ma sa tutto quello che sai tu. È diverso da una skill con `context: fork` (capitolo 9), che parte senza la cronologia, e da `/fork`, che copia la conversazione in una nuova sessione in background invece di aprire un subagent (capitolo 15).

## 10.6 Agent della community, attraverso i plugin

Non devi scrivere ogni agent da zero. Su GitHub trovi collezioni di agent pronti, per linguaggio, framework e dominio: revisori, auditor di sicurezza, esperti di database, scrittori di documentazione.

La prima edizione suggeriva di clonare queste collezioni in una cartella di `~/.claude/`. Oggi la strada da preferire è un'altra: installarli attraverso un plugin. Un plugin impacchetta skill, agent, hook e server MCP, si installa da un marketplace con un comando, si aggiorna e si disattiva senza toccare i file del progetto, e i suoi agent prendono il nome del plugin come prefisso, così non entrano in collisione con i tuoi. Il marketplace ufficiale si chiama `claude-plugins-official` ed è già configurato. Superpowers, che hai installato nel capitolo 8, usa i subagent nel suo flusso di sviluppo con code review integrata. Il capitolo 14 spiega come funzionano i plugin e come costruirne uno.

Copiare a mano un file `.md` trovato in un repository resta possibile, ma perdi gli aggiornamenti e la traccia di dove arriva.

### Leggere prima di installare

Un agent è un file di istruzioni in linguaggio naturale. Installarlo significa dire a Claude di eseguire quelle istruzioni nel tuo ambiente, con i tool che l'agent dichiara. È lo stesso rischio di aggiungere una dipendenza npm senza guardarla.

Prima di installare un agent, o un plugin che ne contiene, apri il file e guarda tre cose. Il system prompt: chiede di leggere file fuori dal progetto, di contattare indirizzi esterni, di raccogliere credenziali? I tool: se c'è `Bash`, le istruzioni dell'agent possono diventare comandi sulla tua macchina, e deve esserci un motivo. Se `tools` manca del tutto, l'agent ha tutto quello che ha la sessione. La fonte: chi mantiene il repository, da quanto tempo, con quanta attività. Un repository senza storia e con un autore sconosciuto merita più cautela di un progetto noto.

::: {.callout .callout-warning}
[Attenzione]{.callout-title}

Un agent malevolo può istruire Claude a leggere `.env`, chiavi SSH e token e a infilarli nel suo rapporto con il nome di "diagnostica". È prompt injection, la stessa classe di problemi che riguarda ogni sistema basato su un LLM. Leggi sempre il file prima di installarlo, provalo in un progetto di prova, e tieni la regola `deny` su `Read(./.env)` del capitolo 11: vale anche per i subagent.
:::

Per la scelta tra livello utente e progetto vale la regola del paragrafo 10.3. Gli agent generici vanno in `~/.claude/agents/` o in un plugin installato per l'utente. Quelli che hai adattato al tuo stack vanno in `.claude/agents/` e nel repository, così il team lavora con lo stesso revisore.

## 10.7 Quando usare cosa

A questo punto hai CLAUDE.md, custom command, skill e agent. Nella Parte IV arrivano altri tre strumenti che risolvono problemi vicini: le regole di permesso (capitolo 11), gli hook (capitolo 12) e i server MCP (capitolo 13). Saper scegliere è metà del lavoro di configurazione.

| Bisogno | Strumento | Capitolo |
|---|---|---|
| "Ricordati sempre le convenzioni di questo progetto" | `CLAUDE.md` | 7 |
| "Quando scrivo /X, esegui questo prompt" | Custom command o skill | 8, 9 |
| "Una procedura riutilizzabile con template e script" | Skill | 9 |
| "Delega questo compito a uno specialista con il suo contesto" | Agent | 10 |
| "Questa cosa non deve succedere mai" | Regola `deny` | 11 |
| "A ogni modifica, senza eccezioni, fai Y" | Hook | 12 |
| "Collegati a un sistema esterno: database, API, GitHub" | Server MCP | 13 |
| "Dai tutto questo al team in un pacchetto" | Plugin | 14 |

Sulla seconda riga: dal capitolo 8 sai che un file in `.claude/commands/` e una skill in `.claude/skills/` creano lo stesso comando con la barra, e che per il lavoro nuovo conviene la skill.

L'albero di decisione segue lo stesso ordine:

```text
Vuoi cambiare il comportamento di Claude?
│
├─ È "ricordati X" o "segui sempre questa convenzione"
│   └─ CLAUDE.md
│
├─ Deve succedere sempre, a ogni evento, senza che il modello decida
│   ├─ è un divieto semplice su un tool o un file  → regola deny
│   └─ serve logica o un'azione (formattare, notificare, bloccare a condizione)  → hook
│
├─ È "quando scrivo /X, fai Y" (un prompt ricorrente)
│   └─ custom command o skill
│
├─ La procedura ha bisogno di file di supporto, template o script
│   └─ skill
│
├─ Vuoi delegare un compito con un contesto isolato e tool limitati
│   └─ agent
│
└─ Claude deve parlare con un sistema esterno (database, API REST, GitHub)
    └─ server MCP
```

### Gli errori più comuni

Usare una skill dove serviva un agent. Se il compito è lungo, produce molto output intermedio e sporca il contesto principale, quasi sempre è un lavoro da agent. La skill ha senso quando la procedura è leggera e vuoi che resti nel flusso della conversazione.

Usare un agent dove bastava un comando. Se stai automatizzando un prompt semplice e ripetuto, come "aggiungi i commenti JSDoc a questo file", un `/jsdoc` è più veloce e costa meno. Un agent riparte da zero e deve rileggere tutto, quindi impiega di più.

Mettere tutto nel `CLAUDE.md`. Il `CLAUDE.md` va bene per le convenzioni permanenti, molto meno per le procedure: una sequenza di venti passi lì dentro viene caricata in ogni sessione, anche quando non serve. Quella procedura sta meglio in una skill o in un agent.

Affidare a un'istruzione un vincolo vero. "Non toccare mai i file di migrazione" scritto nel `CLAUDE.md` o nel prompt di un agent orienta Claude, ma non lo garantisce. Per una garanzia servono una regola di permesso o un hook, oppure un agent senza i tool per scrivere.

### Le combinazioni

Nel lavoro vero questi strumenti si usano insieme. Un comando `/review` che lancia il code-reviewer sui file dell'ultimo commit: il comando è la scorciatoia, l'agent fa il lavoro. Una skill di analisi delle performance che, con `context: fork`, fa girare l'analisi in un subagent e restituisce il rapporto. Un agent di review che rispetta le convenzioni del progetto perché il `CLAUDE.md` gli arriva comunque: della sessione principale non sa niente, ma le regole del progetto le conosce. Fanno eccezione Explore e Plan, che partono senza, e gli agent con `omitClaudeMd` nel frontmatter.

## 10.8 Orchestrare più agent

Gli agent danno il meglio quando Claude ne coordina più d'uno. Questo pattern lo usi in pieno nella Parte VI, con la Photogallery, ma conviene capire qui come funziona.

### L'idea

Devi implementare una feature completa, dalle API alla review. Se fai tutto in sequenza nella sessione principale, il contesto si riempie e la qualità cala man mano che la conversazione cresce. Con più agent il lavoro si divide così:

1. un agent architect analizza i requisiti e restituisce la struttura: classi, responsabilità, file da toccare;
2. un agent implementer scrive il codice a partire da quella struttura, senza la discussione che l'ha prodotta;
3. un agent test-writer scrive i test partendo dal codice e dalla specifica, non dalla conversazione;
4. un agent code-reviewer rilegge il codice finito sui file reali, senza il punto di vista di chi l'ha scritto;
5. la sessione principale coordina, decide quando i risultati sono in conflitto e ti presenta il risultato.

Il vantaggio viene dal contesto pulito. Il code-reviewer non sa che hai passato tre ore su quel codice, il test-writer non ricorda il test simile di mezz'ora fa. Ogni agent lavora con un contesto piccolo e mirato, e la qualità resta più costante di quella di un'unica sessione che accumula ore di conversazione.

### In parallelo

I compiti indipendenti girano insieme. Nel capitolo 19 la review di ogni wave della Photogallery lancia quattro agent in parallelo, tutti in sola lettura: sicurezza, performance, coerenza delle API e copertura dei test. Poi la sessione principale mette insieme i quattro rapporti in ordine di gravità. Visto che i subagent girano già in background, intanto la sessione resta libera, e con `/tasks` controlli a che punto sono.

### Quando due agent scrivono sugli stessi file

Quattro revisori in sola lettura possono lavorare sullo stesso codice senza problemi. Due agent che scrivono no. Se l'implementer e il test-writer modificano insieme la stessa copia di lavoro, uno sovrascrive le modifiche dell'altro, oppure legge un file a metà della modifica e lavora su uno stato che non esiste più. Il risultato sono test che falliscono per motivi che nessuno dei due ha causato da solo.

Le soluzioni sono due. La prima è dividere il lavoro in modo che due agent non tocchino mai gli stessi file nello stesso momento, oppure farli lavorare in sequenza. La seconda è dare a ciascuno una copia sua del repository con un worktree Git: è quello che fa `isolation: worktree` nel frontmatter, e il capitolo 20 lo usa per far correre in parallelo le wave della Photogallery e poi riunire i branch.

### Un avvertimento

Più agent significa più complessità, e molti compiti non la giustificano: per un refactoring su un file, una sola sessione è più veloce. Il lavoro con più agent rende quando il compito è grande e si divide in parti in buona misura indipendenti. Una regola pratica: se a Claude basta meno di cinque minuti, non lanciare un agent; se serve mezz'ora, un contesto isolato quasi sempre ripaga il tempo di preparazione. Nella Parte VI questi agent lavorano sulle wave di implementazione della Photogallery e, nel capitolo 22, sulla review multi-LLM.

## Riepilogo

- Un subagent è un'istanza di Claude con contesto separato, system prompt suo e, se lo decidi, tool limitati. La skill lavora nel contesto principale, l'agent ne apre uno nuovo e ti restituisce solo il rapporto.
- Un agent è un file Markdown in `.claude/agents/` (progetto, da committare) o `~/.claude/agents/` (utente). Servono solo `name` e `description`; `tools`, `model` e il formato del rapporto nel prompt sono le scelte che contano di più.
- La procedura guidata di `/agents` non esiste più dalla versione 2.1.198: chiedi a Claude di scrivere il file, poi rileggi percorsi, checklist e formato.
- I subagent girano in background: li segui con `/tasks`, li fermi con `Ctrl+X Ctrl+K`, e le loro richieste di permesso compaiono nella sessione principale. `/subtask` delega un compito che ha bisogno di tutta la conversazione.
- Gli agent della community si installano con i plugin (capitolo 14), dopo aver letto prompt e tool.
- Più agent che leggono possono lavorare in parallelo; più agent che scrivono sugli stessi file si pestano i piedi e vanno separati, con `isolation: worktree` o con i worktree del capitolo 20.

## Esercizio

Crea il tuo primo agent di sola lettura, per il tuo stack o per la Photogallery.

Scegli il controllo che ti capita di ripetere più spesso e per cui vorresti un revisore che non ha visto il codice nascere: una code review dei controller, un'analisi di sicurezza, una verifica della copertura dei test. Usa il prompt riusabile del paragrafo 10.4 per farti scrivere il file in `.claude/agents/`, con `tools: Read, Grep, Glob`. Rileggilo e aggiungi almeno una verifica specifica del tuo progetto che Claude non aveva previsto.

Poi provalo due volte su un file reale. La prima volta chiamalo per nome. La seconda volta chiedi solo "fai la review di questo file" senza nominarlo, e controlla se Claude lo sceglie da solo; se non lo fa, riscrivi la description. Infine chiedigli esplicitamente di correggere uno dei problemi che ha trovato.

L'esercizio è finito quando l'agent compare nella risposta a "quali subagent hai a disposizione?", ha prodotto due rapporti nel formato che hai scelto, e alla richiesta di correzione ha risposto che non può modificare file, con `git status` che non mostra modifiche oltre al file dell'agent. Committa il file se vuoi darlo al team.

Branch GitHub di partenza: `cap-09-my-first-agent` nel repo `claude-code-book-snippets`. <!-- VERIFY: il branch cap-09-my-first-agent non risulta nel repo claude-code-book-snippets (solo main) -->
