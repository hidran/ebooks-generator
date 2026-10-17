# Capitolo 7. CLAUDE.md, la memoria del progetto

## Cosa imparerai

- dove vivono i file `CLAUDE.md` e come si sommano i quattro livelli;
- cosa scriverci perché Claude lo segua, e cosa lasciare fuori;
- come generare il primo file con `/init` e tenerlo sotto le duecento righe con gli import e le regole in `.claude/rules/`;
- cosa succede quando il repository ha già un `AGENTS.md`.

Prerequisiti: un progetto vero su cui provare, anche piccolo. Va bene quello di analisi dati dei capitoli 4-6.

Immagina di assumere ogni mattina uno sviluppatore nuovo. Gli spieghi il progetto, quale package manager usate, dove sta la funzione che gestisce gli errori, e per tutto il giorno lavora bene. Il mattino dopo è di nuovo il suo primo giorno: rifà le stesse domande e usa le convenzioni che conosce lui, non le vostre.

Senza un `CLAUDE.md`, con Claude Code va così. Ogni sessione parte vuota. Claude non sa che nel tuo progetto si usa pnpm e non npm, che lo stato globale sta in `store/`, che i test si scrivono con Vitest, che i messaggi di errore sono in italiano. Allora tira a indovinare, e sceglie la soluzione più comune, che spesso non è la tua.

`CLAUDE.md` è un file Markdown che Claude Code carica nel contesto all'inizio di ogni sessione, prima del tuo primo prompt. Ci scrivi quello che altrimenti ripeteresti ogni volta: i comandi di build e di test, le convenzioni, le regole del tipo "fai sempre" e "non fare mai". Nel capitolo 2 l'hai trovato nella tabella dei meccanismi, alla voce "testo caricato nel contesto a inizio sessione". Quella definizione spiega sia perché funziona sia dove si ferma.

## 7.1 Cos'è CLAUDE.md

Non ha una sintassi speciale né uno schema obbligatorio: è Markdown normale, con titoli ed elenchi. Claude Code lo legge all'avvio e il testo resta nel contesto per tutta la sessione, quindi accompagna ogni tuo messaggio. Dopo `/clear` la conversazione riparte da zero e `CLAUDE.md` rientra con la sessione nuova. Dopo `/compact` il file della root viene riletto dal disco, quindi le istruzioni scritte lì non dipendono dal riassunto.

<!-- VERIFY: la pagina memory dice che dopo /compact il CLAUDE.md di progetto viene riletto dal disco e reinserito, mentre quelli delle sottocartelle tornano solo quando Claude rilegge file lì dentro; non è in FACTS.md -->

### I quattro livelli

Claude Code cerca le istruzioni in quattro posti:

| Livello | Dove sta | Chi lo vede |
|---|---|---|
| Organizzazione | macOS `/Library/Application Support/ClaudeCode/CLAUDE.md`, Linux e WSL `/etc/claude-code/CLAUDE.md`, Windows `C:\Program Files\ClaudeCode\CLAUDE.md` | Tutti gli utenti della macchina, lo gestisce l'IT |
| Utente | `~/.claude/CLAUDE.md` | Solo tu, in tutti i progetti |
| Progetto | `./CLAUDE.md` oppure `./.claude/CLAUDE.md` | Il team, via Git |
| Locale | `./CLAUDE.local.md` | Solo tu, in questo progetto |

Il livello organizzazione (managed policy) lo distribuisce l'IT di un'azienda, con le regole che valgono per tutti.

Il file utente contiene le preferenze che ti porti dietro in ogni repository: la lingua delle risposte, i messaggi di commit in inglese con Conventional Commits, il fatto che preferisci risposte brevi. È facoltativo, e molti non lo usano.

Il file di progetto è quello che conta di più. Sta nella root, finisce in Git e chi clona il repository eredita le istruzioni insieme al codice. Se preferisci una root pulita puoi metterlo in `.claude/CLAUDE.md`, il risultato è lo stesso.

`CLAUDE.local.md` è la tua versione privata del file di progetto: l'URL del tuo ambiente di test, il database locale con un nome diverso da quello dei colleghi, una nota su cosa stai facendo questa settimana. Aggiungilo a `.gitignore` appena lo crei.

In un monorepo puoi mettere un `CLAUDE.md` anche in una sottocartella, per esempio `frontend/CLAUDE.md` e `backend/CLAUDE.md`. I file nelle cartelle sopra quella in cui lanci `claude` si caricano all'avvio. Quelli nelle sottocartelle entrano solo quando Claude legge un file lì dentro: chi lavora sul frontend non si porta dietro le regole del backend.

### Come si combinano

Claude Code non sceglie un file: li carica tutti, dal più generale al più specifico, e il modello vede un unico blocco di istruzioni. Se nel file utente c'è "grafici sempre con tema scuro" e nel progetto di un cliente serve il tema chiaro perché il report va stampato, scrivilo come eccezione esplicita: "in questo progetto usa il tema chiaro al posto di quello scuro". Due istruzioni che si contraddicono senza spiegazione lasciano Claude a scegliere da solo, e non sempre sceglie quella che volevi. Nel capitolo 15 vedrai `/doctor prompt-audit`, che queste contraddizioni le trova per te.

### Quanto deve essere lungo

La raccomandazione ufficiale è restare sotto le duecento righe per ogni file. I motivi sono due. Il primo è il costo: quel testo occupa contesto in ogni sessione e viene riletto a ogni turno, che tu ne abbia bisogno o no. Il secondo pesa di più: un file lungo viene seguito peggio. Con trecento righe di istruzioni, le cinque che contano davvero si confondono con le altre.

Il limite tecnico è molto più alto (i file fino a 4 MiB si caricano interi, quelli più grandi vengono saltati), e anche la finestra da un milione di token avrebbe spazio. Ma un file lungo resta un file seguito peggio. Quando cresce, sposta le istruzioni che valgono per una sola zona del codice in regole che si caricano solo quando servono (paragrafo 7.5).

## 7.2 Cosa scrivere dentro

Parti da una domanda: cosa deve sapere Claude per non sbagliare su questo progetto? Ti porta a scegliere solo quello che cambia il codice prodotto, invece di riempire il file con tutto quello che sai.

Poi scrivi ogni istruzione in modo che si possa controllare. "Usa due spazi di indentazione" funziona meglio di "formatta bene il codice"; "lancia `pnpm lint` prima di ogni commit" funziona meglio di "tieni il codice pulito". Un'istruzione verificabile la controlli nel diff, e Claude sa quando l'ha rispettata.

Le informazioni che stanno bene in un `CLAUDE.md` rientrano quasi sempre in sei categorie.

### Lo stack, con le versioni

Claude conosce molte versioni di molti framework. Senza indicazioni sceglie quella che ha visto più spesso, che potrebbe non essere la tua.

```markdown
## Stack

- Runtime: Node.js 22 LTS
- Framework: NestJS 11
- ORM: Prisma 6 (PostgreSQL)
- Frontend: React 19 + TypeScript 5
- Styling: Tailwind CSS 4
- Test: Vitest 3 + Testing Library
- Package manager: pnpm (NON usare npm o yarn)
```

La riga sul package manager è quella che ti risparmia più guai. Se il repository usa pnpm e Claude lancia `npm install`, ti ritrovi con un `package-lock.json` spurio accanto a `pnpm-lock.yaml` e con versioni diverse da quelle del team.

### Le convenzioni che non si vedono nel codice

Scrivi solo quelle che Claude non ricava da solo. Se `tsconfig.json` ha `"strict": true`, non serve ripeterlo.

```markdown
## Convenzioni

- Componenti React: function component con TypeScript, niente class component
- Nomi file: kebab-case; componenti React in PascalCase
- Import: percorsi assoluti da `src/` con l'alias `@/`
- Errori: pattern Result<T, E>, mai throw nudi
- Commenti in italiano, docstring in inglese
- Niente `console.log` nel codice committato: usa `logger` da `src/utils/logger`
```

### I comandi del progetto

Qui si vede la differenza tra un Claude che lancia il comando giusto al primo colpo e uno che prova `npm run build` perché è il default più diffuso.

```markdown
## Comandi

- Dev: `pnpm dev` (frontend sulla porta 3000, API sulla 4000)
- Build: `pnpm build`
- Test: `pnpm test` (tutti) o `pnpm test:unit` (solo unit)
- Lint: `pnpm lint && pnpm type-check`, sempre entrambi prima del commit
- Migrazioni: `pnpm db:migrate` (mai `prisma migrate deploy` a mano)
- Seed: `pnpm db:seed`, sovrascrive i dati
```

### Le cose da non fare

Spesso è la sezione più utile. Claude tende a fare quello che sembra funzionare, anche quando nel tuo progetto è sbagliato, e i divieti espliciti gli tolgono le strade che hai già scartato.

```markdown
## NON fare mai

- Non installare dipendenze senza averne parlato prima
- Non modificare `src/generated/`: lo genera Prisma
- Non usare `fetch` direttamente: passa da `src/lib/api-client.ts`
- Non aggiungere `any` senza un commento che spieghi perché
- Non usare `Date.now()` nei test: usa `vi.setSystemTime()`
```

### I pattern, con un esempio di riferimento

Se il progetto ha pattern che si ripetono e che Claude potrebbe non seguire spontaneamente, descrivili e indica il file da prendere come modello. Claude va a leggerlo e copia la struttura.

```markdown
## Architettura

- Accesso ai dati con il repository pattern: modello in `src/repositories/user.repository.ts`
- Scritture in `commands/`, letture in `queries/`, mai nello stesso file
- Validazione degli input sempre con uno schema Zod
- Form: React Hook Form con zodResolver, niente useState per lo stato del form
```

### Il vocabolario del dominio

Ogni progetto ha parole sue, e "cliente" può voler dire cose diverse nel database, nel codice e nelle riunioni. Fissare i termini evita che un malinteso diventi un bug.

```markdown
## Dominio

- "Utente" = persona registrata (entità `User`)
- "Cliente" = azienda con un contratto attivo (entità `Organization`)
- Un utente può appartenere a più organizzazioni
- Stato ordine: DRAFT → PENDING → PROCESSING → COMPLETED | CANCELLED
```

### Note per i colleghi, a costo zero

I commenti HTML a livello di blocco vengono tolti prima che il testo arrivi a Claude. Puoi lasciare una nota per chi mantiene il file (perché esiste una regola, chi l'ha chiesta, dove sta il resto) senza consumare contesto:

```markdown
## Regole

- Non modificare mai i file in `data/`: lavora su copie in `tmp/`
- Ogni nuova funzione in `src/` ha un test in `tests/`

<!-- Nota per i manutentori: le regole Python stanno in .claude/rules/python.md -->
```

### Un esempio vero: il Photogallery

Il progetto della Parte VI ha un `CLAUDE.md` scritto in inglese, come il resto della documentazione del repository companion. Il capitolo 18 lo costruisce passo per passo (paragrafo 18.4). Qui ne vedi un estratto, per notare la forma delle regole:

```markdown
# CLAUDE.md — PhotoGallery Pro

> The project constitution. Loaded into every Claude Code session.
> Authoritative for HOW we work; defers to `docs/REQUIREMENTS.md` (what to
> build) and `docs/DESIGN.md` (technical blueprint) for content. Atomic work
> lives in `docs/TASKS.md`.

## Critical rules

1. Always read `docs/REQUIREMENTS.md` and `docs/DESIGN.md` before implementing
   tasks. If the task is ambiguous and the docs don't resolve it, stop and ask.
4. One task = one commit. Conventional Commits format: `<type>(<scope>): <subject>`.
5. Tests run before commits. No `--no-verify`, no `.skip`, no "tests later".
7. Every endpoint wraps its payload in `{ "data": ... }`. No exceptions.
8. Every primary key is UUID v7 via the `HasUuidV7` trait. Stored as `CHAR(36)`.
13. Tailwind v4 setup is non-negotiable. No `tailwind.config.js`, no
    `postcss.config.js`, no `autoprefixer`.
```

Quasi ogni regola si controlla guardando il diff: o l'endpoint restituisce `{ "data": ... }` o no, o la chiave primaria è un UUID v7 o no. E molte rimandano a un documento (`DESIGN.md`) invece di ricopiarlo. Il file completo è lungo 391 righe, quasi il doppio del target, e buona parte riguarda una sola zona del codice: lo stile PHP vale per `backend/`, le regole Tailwind per `frontend/`. Nel paragrafo 7.5 vedi come lo spezzerei.

## 7.3 Cosa non scrivere

Un `CLAUDE.md` gonfio è peggio di uno scarno: occupa contesto e diluisce le istruzioni che contano. Gli errori più comuni sono sei.

Il primo è la documentazione delle API: elenco degli endpoint, parametri, firme dei metodi. Quella sta nel codice, nei commenti, in un file OpenAPI, e Claude la legge quando gli serve.

Stesso discorso per l'inventario delle funzioni ("il progetto ha `getUserById()`, `createUser()`, `deleteUser()`..."). Claude le trova da solo esplorando il codice. Se una funzione va usata in un modo particolare, scrivilo come pattern, con il file di riferimento.

Poi le spiegazioni didattiche. Claude sa già cos'è Prisma e come funziona un JWT. Il "perché abbiamo scelto questa tecnologia" interessa a un collega nuovo, e per lui c'è il README o un ADR. Nel `CLAUDE.md` vanno istruzioni.

Le credenziali non ci vanno mai: chiavi API, token, password, stringhe di connessione con utente e password. Il file di progetto finisce in Git, quindi sul remoto, e da lì ovunque il repository venga clonato. I segreti stanno nel `.env` (fuori da Git) o in un secrets manager.

Anche roadmap e note temporanee restano fuori. "A marzo aggiungeremo X" o "stiamo valutando di passare a PostgreSQL" non cambiano il codice che Claude scrive oggi. Vanno nel task manager o nelle specifiche.

L'ultimo errore sono le intenzioni senza una regola dietro. "Cerchiamo di scrivere codice pulito" non guida nessuna scelta. Se vuoi funzioni piccole, scrivi una regola che si possa verificare: "una funzione oltre le 30 righe va segnalata con un `TODO:REFACTOR`".

Per ogni sezione che stai per aggiungere, il test è questo: senza questa informazione, Claude scriverebbe codice diverso e sbagliato? Se la risposta è no, la sezione non serve.

::: {.callout .callout-warning}
[Attenzione]{.callout-title}

`CLAUDE.md` orienta Claude, ma non lo vincola. È testo nel contesto: di solito viene seguito, ma in una sessione lunga o davanti a una tua richiesta esplicita può perdere peso. "Non leggere mai il file `.env`" scritto qui è un'indicazione; una regola deny in `.claude/settings.json` (capitolo 11) o un hook `PreToolUse` (capitolo 12) lo impediscono davvero, perché li applica Claude Code prima che la chiamata parta. Usa `CLAUDE.md` per spiegare come lavorare e i permessi e gli hook per i vincoli.
:::

## 7.4 Generare il primo file con /init

Scrivere a mano il primo `CLAUDE.md` di un progetto esistente è noioso, e Claude può prepararti la bozza. Dalla root del progetto, in una sessione di Claude Code:

```text
/init
```

Claude esplora il repository: legge `package.json` o `pyproject.toml`, i file di configurazione (`tsconfig.json`, la config di ESLint, quella di Vite), la struttura delle cartelle e qualche file sorgente per capire i pattern in uso. Poi scrive una prima versione di `CLAUDE.md` con lo stack (le versioni le prende dai manifest), i comandi trovati negli script, la struttura principale e qualche convenzione dedotta dal codice.

<!-- VERIFY: su un repository che ha già un CLAUDE.md, /init propone miglioramenti al file esistente invece di sovrascriverlo; non è in FACTS.md -->

![/init al lavoro: Claude esplora il progetto e prepara CLAUDE.md.](figures/cap-07/fig-01.png)

<!-- TODO screenshot: rifare fig-01 con la UI attuale (barra di stato con il modello di ottobre 2026 e auto mode), a risoluzione più alta e senza nome dell'account e percorso personale nell'intestazione -->

Se vuoi più controllo, lancia Claude Code con la variabile `CLAUDE_CODE_NEW_INIT=1`. `/init` passa a un flusso interattivo: invece di scrivere subito il file, ti fa domande su cosa configurare e su quello che non riesce a ricavare dal codice.

```bash
CLAUDE_CODE_NEW_INIT=1 claude
```

<!-- VERIFY: dettagli del flusso interattivo di CLAUDE_CODE_NEW_INIT=1 (quali domande fa, quali file propone oltre a CLAUDE.md); FACTS.md dice solo "interactive flow" -->

### Cosa devi aggiungere tu

La bozza di `/init` è un buon punto di partenza, ma le mancano quasi sempre tre cose che nel codice non stanno. Le convenzioni semantiche: il codice dice che usi TypeScript strict, non che i messaggi di errore vanno in italiano. Le regole operative del team: `/init` trova `pnpm dev` negli script, ma "lancia `pnpm lint && pnpm type-check` prima del commit" è una decisione vostra. E i divieti, che esistono perché qualcuno ha sbagliato una volta, una storia che nel codice non c'è.

### Modificare il file

Puoi aprire `CLAUDE.md` con il tuo editor, oppure scrivere `/memory` in sessione: vedi l'elenco dei file di istruzioni caricati (utente, progetto, locale, regole) e apri quello che vuoi modificare. Dallo stesso menu controlli anche la memoria automatica, che trovi nel paragrafo 7.5.

![Il CLAUDE.md generato da /init per il progetto di analisi dati: pipeline dei grafici, palette dei piani e cartelle di output.](figures/cap-07/fig-02.png)

Nelle guide del 2025 trovi ancora la scorciatoia `#`: un messaggio che iniziava con `#` finiva dritto in `CLAUDE.md`. È stata rimossa a dicembre 2025. Oggi lo chiedi a parole:

```text
aggiungi a CLAUDE.md, nella sezione NON fare mai: non modificare i file in src/generated/
```

### Il flusso completo

1. Lancia `/init` nella root del progetto.
2. Apri il `CLAUDE.md` generato e leggilo tutto. Togli le parti ovvie o ridondanti, come l'elenco delle cartelle che Claude vede da solo.
3. Aggiungi le tre cose che mancano: convenzioni, regole operative, divieti.
4. Esci e rilancia `claude`, oppure fai `/clear`, poi chiedi qualcosa che dovrebbe far scattare le tue convenzioni. Se Claude usa pnpm, crea i file nelle cartelle giuste e segue il pattern che hai indicato, il file funziona. Altrimenti torna al punto 3.
5. Committa il file:

```bash
git add CLAUDE.md
git commit -m "docs: add CLAUDE.md"
```

### Se il repository ha già un AGENTS.md

Molti progetti hanno un `AGENTS.md`, il file di istruzioni che leggono altri agenti di programmazione. Dalla versione 2.1.277 (settembre 2026) Claude Code lo legge in modo nativo: se nella cartella di lavoro e in quelle sopra non c'è né un `CLAUDE.md` né un `CLAUDE.local.md`, usa `AGENTS.md`. Un repository preparato per un altro agente funziona subito.

Il comportamento si cambia in `/config`, alla voce Project instructions. Il default è `claude-md-or-agents-md` (quello appena descritto); `claude-md-and-agents-md` li carica entrambi, `claude-md` ignora `AGENTS.md`, `managed-only` tiene solo le istruzioni dell'organizzazione.

<!-- VERIFY: significato esatto di claude-md-and-agents-md, claude-md e managed-only; FACTS.md elenca solo i valori -->

Le varianti `AGENTS.local.md`, `AGENTS.override.md` e la cartella `.agents/` non vengono lette.

Se nel progetto convivono i due file e vuoi un'unica fonte, scrivi le istruzioni comuni in `AGENTS.md` e importalo dal `CLAUDE.md` con una riga `@AGENTS.md` (gli import sono nel paragrafo che segue). Sotto aggiungi solo quello che riguarda Claude Code. Se invece arrivi da Codex o Gemini CLI con una configurazione già scritta, `/init` se ne accorge e ti propone `/import` per portarla dentro.

## 7.5 Tenerlo corto e aggiornato

Un `CLAUDE.md` scritto una volta e poi dimenticato invecchia in fretta. Dopo sei mesi descrive uno stack che hai aggiornato e comandi che hai rinominato, e Claude segue le istruzioni vecchie invece di guardare il codice com'è oggi. Per tenerlo corto Claude Code ti dà due strumenti, gli import e le regole per percorso. Per tenerlo aggiornato serve un po' di disciplina.

### Gli import con @

Una riga `@percorso/file` dentro `CLAUDE.md` include un altro file. Il percorso è relativo al file che importa; vanno bene anche percorsi assoluti e quelli che iniziano con `~`.

```markdown
# Photogallery

Panoramica e comandi: @README.md
Istruzioni condivise con gli altri agenti: @AGENTS.md

## Preferenze personali
- @~/.claude/photogallery-preferenze.md
```

L'ultima riga è un'alternativa a `CLAUDE.local.md`: le tue preferenze stanno in un file nella home, e ogni worktree del progetto le ritrova con lo stesso import. Gli import possono annidarsi fino a quattro livelli. Un `@` dentro un blocco di codice o tra backtick viene ignorato. Se il percorso ha spazi, mettici davanti un `\`. Quando un import punta fuori dal progetto, la prima volta Claude Code ti chiede di approvarlo.

Gli import servono a organizzare il testo. Il file importato si carica all'avvio come se fosse scritto lì e costa lo stesso contesto: per caricare istruzioni solo quando servono ci sono le regole.

### Le regole in .claude/rules/

La cartella `.claude/rules/` contiene file Markdown, anche in sottocartelle, che Claude Code trova da solo. Una regola senza frontmatter si carica all'avvio come un pezzo di `CLAUDE.md`. Una regola con il campo `paths:` (un elenco YAML di glob) si carica solo quando Claude legge o modifica un file che corrisponde.

Il Photogallery è il caso da manuale. Lo stile PHP del suo `CLAUDE.md` vale solo per `backend/`, e così lo sposterei in `.claude/rules/php.md`:

```markdown
---
paths:
  - "backend/**/*.php"
---

# PHP code style

- Run `vendor/bin/pint --dirty --format agent` before finalizing changes.
- `declare(strict_types=1);` on every file in `app/Services/`, `app/Actions/`,
  `app/Jobs/`, `app/Queries/`.
- Final by default: new classes are `final class Foo` unless explicitly
  designed for inheritance.
- Mass assignment: `$model->fill($request->validated())`, never `$request->all()`.
- Always use curly braces for control structures, even for single-line bodies.
```

Le righe vengono, appena accorciate, dalla sezione Code style del file. Lo stesso vale per le regole TypeScript e Tailwind, che andrebbero in `.claude/rules/frontend.md` con `paths: ["frontend/src/**/*.ts", "frontend/src/**/*.tsx"]`. Nel `CLAUDE.md` restano le regole che valgono ovunque (un task, un commit; l'envelope `{ "data": ... }`; UUID v7) e il file scende verso le duecento righe. Nel repository companion questa divisione non c'è ancora: è il refactoring che farei oggi.

Per il progetto di analisi dati dei capitoli 4-6 basta una regola sola:

```markdown
---
paths:
  - "**/*.py"
---

# Regole Python

- Type hint su tutte le funzioni pubbliche
- Docstring in italiano, formato Google
- Niente print: usa il modulo logging
```

Claude Code cerca le regole all'avvio, quindi dopo averne scritta una esci e rilancia `claude`. Chiedi a Claude di leggere un file Python, poi scrivi `/memory`: la regola compare tra i file di istruzioni caricati. In `/context` la trovi nella sezione Memory files, con il suo peso in token. Le regole personali, valide in tutti i progetti, vanno in `~/.claude/rules/`.

### Quando aggiornarlo

Il momento giusto è subito dopo il cambiamento, mentre hai il contesto fresco: un aggiornamento major (Laravel 12 a 13), un cambio di package manager, un pattern nuovo, una libreria che Claude deve usare in un certo modo, una cartella rinominata, una cosa che avete deciso di non fare più.

Nei team funziona una casella nel template delle pull request:

```markdown
## Checklist PR

- [ ] Test verdi (`pnpm test`)
- [ ] Lint pulito (`pnpm lint && pnpm type-check`)
- [ ] CLAUDE.md aggiornato se sono cambiati stack o convenzioni
- [ ] Documentazione aggiornata se è cambiata un'API pubblica
```

La casella non garantisce niente, ma la vedono sia chi apre la PR sia chi fa la review.

I segnali che il file è rimasto indietro sono facili da riconoscere. Claude continua a creare i componenti con la struttura che avevi prima del refactoring, perché `CLAUDE.md` descrive ancora quella. Propone `npm run dev` sei mesi dopo che sei passato a `pnpm dev`. Rispetta un divieto ("non usare `fetch` direttamente") che non ha più senso, perché l'api-client non esiste più.

Se vuoi tenere traccia delle modifiche, aggiungi in fondo una sezione con le ultime tre o cinque, datate. Serve a te e al team, non a Claude, quindi puoi metterla dentro un commento HTML e non costa contesto:

```markdown
<!--
## Changelog
- 2026-09-10: passaggio da React Query a TanStack Query 5 (stessa API)
- 2026-07-02: introdotto il pattern Result<T, E>, eliminare i try/catch nudi
- 2026-05-15: generato con /init + convenzioni del team
-->
```

Ogni tanto chiedi a Claude stesso di fare la revisione. Sa dire quali istruzioni usa e quali sono solo rumore.

::: {.callout .callout-prompt}
[Prompt riusabile]{.callout-title}

```text
Leggi il file CLAUDE.md in questo progetto e dimmi:
1. Ci sono informazioni duplicate con quello che puoi già dedurre dal codice?
2. Ci sono sezioni troppo verbose che potrebbero essere condensate?
3. Mancano informazioni importanti che ti hanno già causato errori
   o che ti avrebbero aiutato in questa sessione?
4. Il file ha sezioni obsolete rispetto allo stack attuale del progetto?
5. Ci sono istruzioni che valgono solo per una parte del codice e che
   starebbero meglio in .claude/rules/ con il campo paths?

Proponi una versione revisionata con al massimo 200 righe.
```

Lancialo ogni due o tre mesi, o dopo un refactoring importante.
:::

Il controllo più sistematico lo fa `/doctor prompt-audit`, che legge `CLAUDE.md`, regole, skill e agent e segnala istruzioni scritte per modelli vecchi, riferimenti a file che non esistono più e istruzioni in contraddizione. Lo trovi nel capitolo 15.

### La memoria che scrive Claude

Oltre a `CLAUDE.md`, che scrivi tu, c'è la memoria automatica (auto memory), che scrive Claude ed è attiva di default. Ci finiscono le tue preferenze, le correzioni che gli dai durante il lavoro e il contesto che non può ricavare dal codice. Vive nella tua home, in `~/.claude/projects/<progetto>/memory/`, condivisa tra i worktree dello stesso repository: un file `MEMORY.md` fa da indice e a ogni sessione se ne caricano le prime 200 righe (o 25 KB). Sono file Markdown che puoi leggere e correggere, e `/memory` la attiva o la spegne. La regola per scegliere è semplice: quello che serve a tutto il team va in `CLAUDE.md`, le tue preferenze personali possono stare nella memoria. Il capitolo 15 la tratta per intero.

## 7.6 Tre esempi reali

Tre file per progetti di tipo diverso, ognuno con le situazioni in cui ti risparmia una correzione.

### A. Frontend React e Tailwind CSS

```markdown
# CLAUDE.md: Dashboard Frontend

## Stack
- React 19 + TypeScript 5
- Vite 6 (NON Create React App, NON Next.js)
- Tailwind CSS 4 + shadcn/ui
- Stato globale: Zustand 5
- Fetching: TanStack Query 5
- Form: React Hook Form 7 + Zod
- Test: Vitest + Testing Library
- Package manager: pnpm

## Comandi
- Dev: `pnpm dev` (porta 5173)
- Build: `pnpm build`, anteprima con `pnpm preview`
- Test: `pnpm test`
- Lint: `pnpm lint`

## Convenzioni
- Un componente per file, nome in PascalCase, file in kebab-case (`gallery-card.tsx`)
- Hook custom con prefisso `use`, es. `useGalleryList`
- Classi Tailwind inline nel JSX, niente CSS separato
- Niente `useEffect` per il fetching: usa TanStack Query
- Negli store Zustand solo stato, nessuna logica di business

## NON fare mai
- Non modificare `src/components/ui/`: sono i componenti shadcn
- Non usare `useState` per lo stato dei form: React Hook Form
- Non importare con percorsi relativi: usa l'alias `@/`
- Non lasciare `console.log` nel codice committato
```

Quando ti salva: Claude non propone `useEffect` più `fetch` per le chiamate API, il pattern vecchio che ha visto più spesso, non tocca i componenti shadcn e passa sempre da TanStack Query. Su un frontend che cambia in fretta, queste tre regole da sole valgono il file.

### B. Backend NestJS e Prisma

```markdown
# CLAUDE.md: API Backend

## Stack
- NestJS 11 + TypeScript 5 (strict)
- Prisma 6 (PostgreSQL)
- Auth: Passport + JWT (access 15 min, refresh 7 giorni)
- Test: Jest + Supertest
- Package manager: pnpm

## Comandi
- Dev: `pnpm start:dev` (hot reload, porta 4000)
- Test: `pnpm test` (unit), `pnpm test:e2e` (E2E)
- Migrazioni in sviluppo: `pnpm db:migrate`
- Migrazioni in produzione: `pnpm db:deploy` (mai `migrate dev` in produzione)
- Seed: `pnpm db:seed` (sovrascrive tutto)

## Architettura
- Un modulo NestJS per dominio (users, orders, invoices)
- Repository pattern: ogni modulo ha il suo `.repository.ts`, modello in `src/users/users.repository.ts`
- Un DTO per operazione (`CreateUserDto`, `UpdateUserDto`)
- `JwtAuthGuard` su ogni endpoint protetto

## Convenzioni
- Niente `any`: usa `unknown` e un type guard
- Errori sempre con `HttpException` o le sue sottoclassi
- Log con `Logger` da `@nestjs/common`, mai `console.log`

## NON fare mai
- Non modificare `src/prisma/generated/`: file generati
- Non esporre endpoint senza `@UseGuards(JwtAuthGuard)` (tranne `/auth/*`)
- Non restituire entità Prisma dal controller: sempre un DTO
```

Quando ti salva: Claude non dimentica il guard JWT su un endpoint nuovo, non restituisce nella response i campi sensibili di un'entità e segue il repository pattern del modello. Sono errori che costa caro trovare dopo.

### C. Script Python di analisi dati

Questo è il genere di file che ti serve per il progetto dei capitoli 4-6.

```markdown
# CLAUDE.md: analisi metriche SaaS

## Stack
- Python 3.11+
- pandas 2, matplotlib
- Export: openpyxl per Excel, ReportLab per PDF
- Ambiente: pip + venv (NON conda), `venv/` nella root, già creato

## Comandi
- Attiva l'ambiente: `source venv/bin/activate`
- Dipendenze: `pip install -r requirements.txt`
- Dashboard: `python dashboard.py`
- Excel: `python tools/genera_excel.py`
- Report PDF: `python tools/genera_report.py`
- Test: `pytest tests/`

## Dati
- Sorgente: `saas_metrics.csv` (sola lettura)
- Grafici in `docs/charts/`, Excel e PDF in `output/` (crea le cartelle se mancano)
- Valuta: euro, mai dollari
- Date nel formato gg/mm/aaaa

## Convenzioni
- Type hint su parametri e valore di ritorno, docstring in formato Google
- Palette dei piani fissa: Free, Silver, Gold sempre con gli stessi colori
- Grafici a 150 dpi

## NON fare mai
- Non usare `print()` per il debug: usa `logging`
- Non scrivere percorsi assoluti: usa `pathlib.Path(__file__).parent`
- Non committare CSV o Excel: solo codice e `requirements.txt`
- Non modificare il CSV sorgente
```

Quando ti salva: Claude salva grafici e report nelle cartelle giuste senza che tu lo ripeta, usa l'euro e il formato data italiano, e non riscrive il CSV per "ripulirlo". Sugli script che girano da soli, come il report Excel lanciato da cron nel capitolo 5, l'output resta coerente anche quando il prompt è di una riga.

## Riepilogo

- `CLAUDE.md` è testo che Claude Code carica nel contesto a ogni sessione. I livelli sono quattro (organizzazione, utente, progetto, locale) e si sommano; i file nelle sottocartelle entrano quando Claude ci lavora.
- Scrivi istruzioni verificabili su stack, comandi, convenzioni non ovvie, divieti, pattern e vocabolario. Lascia fuori documentazione, segreti e roadmap.
- Resta sotto le duecento righe. Gli import con `@` organizzano ma non risparmiano contesto; le regole in `.claude/rules/` con `paths:` si caricano solo per i file che corrispondono.
- Genera la prima bozza con `/init`, poi aggiungi quello che il codice non dice. Per modificarlo usa `/memory` o chiedilo a Claude: la scorciatoia `#` non esiste più.
- Se c'è solo un `AGENTS.md`, Claude Code legge quello; se ci sono entrambi, importa `@AGENTS.md` dal `CLAUDE.md`.
- `CLAUDE.md` guida e non vincola: per i vincoli usa i permessi (capitolo 11) e gli hook (capitolo 12).

## Esercizio

Prendi un progetto su cui lavori, anche piccolo. Se non ne hai uno, usa quello dell'esercizio del capitolo 1 o il progetto di analisi dei capitoli 4-6.

1. Lancia `/init` nella root e leggi la bozza. Togli quello che Claude ricava da solo dal codice.
2. Aggiungi i comandi del progetto, una sezione "NON fare mai" con tre-cinque voci e il vocabolario del dominio, se il progetto ne ha uno.
3. Sposta in `.claude/rules/` almeno una regola che vale solo per un tipo di file, con il campo `paths:`.
4. Esci, rilancia `claude` e chiedi qualcosa che dovrebbe far scattare le tue convenzioni, per esempio "aggiungi un modulo per la gestione degli ordini" oppure "aggiungi al report un grafico del churn per piano".

L'esercizio è finito quando `CLAUDE.md` è sotto le duecento righe (controlla con `wc -l CLAUDE.md`), `/memory` mostra la regola caricata dopo che Claude ha letto un file che corrisponde, e il codice prodotto al punto 4 rispetta comandi, cartelle e pattern che hai scritto senza che tu li ripeta nel prompt. Il prompt di revisione del paragrafo 7.5 è anche nel repository `claude-code-book-snippets`, cartella `cap-06/`.
