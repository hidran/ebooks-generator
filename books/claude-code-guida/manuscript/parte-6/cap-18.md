# Capitolo 18. Spec Driven Development

**Cosa imparerai**

- dividere le specifiche in `docs/REQUIREMENTS.md`, `docs/DESIGN.md` e `docs/TASKS.md`, e capire chi legge cosa
- scrivere un build workflow con prompt, comando di verifica e commit per ogni fase
- mettere SOLID, KISS e DRY nel `CLAUDE.md` con esempi presi dal codice del progetto
- far criticare le spec da un agente scettico prima di scrivere la prima riga di codice

**Prerequisiti.** Il capitolo 17, da cui arrivano `SPEC.md` e i documenti di rifinitura del Photogallery. Laravel non serve conoscerlo: gli esempi sono in PHP, ma il metodo resta lo stesso con qualsiasi framework backend.

Programmare con un agente diventa un problema in un momento preciso, e di solito arriva tardi: ore o giorni dopo, quando il codice funziona ma non sai più dire perché è scritto così. Un modulo usa UUID e quello accanto interi auto-increment. In un controller la logica di business sta nel controller, in un altro sta in un service. Le stesse cose hanno nomi diversi a seconda della sessione in cui sono nate. Ogni scelta, presa da sola, si difende. Messe insieme, no.

Questo è il vibecoding: lasci che l'agente scriva prompt dopo prompt, senza una struttura che leghi le decisioni. Claude scrive buon codice, ma quando manca un piano riempie i vuoti con scelte ragionevoli che nessuno confronta con quelle del giorno prima. E il debito tecnico non si vede, perché il codice arriva già scritto, plausibile, che compila. La duplicazione qui, l'accoppiamento implicito là, l'interfaccia che manca: te ne accorgi quando una modifica che doveva toccare tre file ne tocca trenta.

Lo Spec Driven Development (SDD) parte da una regola semplice: ogni riga di codice che Claude scrive deve risalire a un requisito, a un task e a una decisione di design scritta. Niente codice senza un requisito che lo giustifichi, niente task senza una sezione di design che lo guidi, niente commit finché il task non è verificato. Detta così sembra burocrazia. In pratica Claude smette di indovinare cosa avevi in mente e comincia a eseguire un piano, e tu passi meno tempo a correggere.

C'è anche una ragione legata al contesto. Il `SPEC.md` del Photogallery, alla fine del capitolo 17, è arrivato a 2.386 righe. In una context window da un milione di token ci sta comodo, ma caricarlo intero per ogni task vuol dire pagare tutto il progetto per scrivere un controller, e annegare le venti righe che servono in duemila che non servono. Con i file separati Claude legge le regole (`CLAUDE.md`, caricato in automatico), il task che deve eseguire e la sezione di design che il task cita.

La Parte VI costruisce il Photogallery con questo metodo. Qui si preparano i file; dal capitolo 19 si esegue.

## 18.1 I tre file

Diversi strumenti di sviluppo con agenti sono arrivati per strade diverse alla stessa conclusione: per un progetto di medie dimensioni un unico file di specifica non basta. Kiro chiama i suoi file `requirements.md`, `design.md` e `tasks.md`; Spec Kit di GitHub lavora con una spec, un piano e una lista di task. I nomi cambiano, la divisione è quella: cosa costruire, come costruirlo, in che ordine. <!-- VERIFY: nomi dei file di Kiro (requirements/design/tasks) e degli artefatti di Spec Kit (spec/plan/tasks) nelle versioni di ottobre 2026 --> Nel Photogallery i tre file stanno in `docs/`, con il nome in maiuscolo, e accanto c'è il `CLAUDE.md` nella radice del repository che li tiene insieme.

| File | Chi lo legge | Quanto cambia | Quando si legge |
| :---- | :---- | :---- | :---- |
| `CLAUDE.md` | Ogni sessione | Poco | Sempre, in automatico |
| `docs/REQUIREMENTS.md` | Tu, uno stakeholder, chi pianifica | Pochissimo | In pianificazione e quando un task cita un criterio |
| `docs/DESIGN.md` | Gli agent che implementano | Abbastanza | Quando un task cita una sezione |
| `docs/TASKS.md` | Gli agent che eseguono | Di continuo | A ogni task, aggiornato a ogni task chiuso |

Quando Claude lavora su T031, `PhotoController@index` e `@show`, non gli serve sapere come funziona il pannello Filament: legge il task, che rimanda a `DESIGN.md §6.2`, e apre quella sezione. Chi deve decidere se una feature entra nella v1 legge i requisiti e non si perde tra gli schemi delle tabelle. Siccome i requisiti cambiano di rado e i task cambiano ogni ora, tenerli in file diversi evita di riscrivere un documento enorme ogni volta che spunti una casella. E le caselle `[ ]` e `[x]` di `TASKS.md` ti dicono a che punto sei senza aprire altro.

### `docs/REQUIREMENTS.md`, cosa costruire

Il file dei requisiti descrive il prodotto in una lingua che capisce anche chi non scrive codice. Niente tecnologie, niente nomi di classi o di endpoint: visione, personas, user story, criteri di accettazione, vincoli, requisiti non funzionali e cosa resta fuori. L'intestazione del file lo dice in chiaro: «No code, no schemas, no technical decisions».

Nel Photogallery le personas sono tre (visitatore anonimo, membro registrato, amministratore). Le user story sono numerate da `US-01` a `US-40`, le feature da `F1` a `F12`, e ogni criterio di accettazione ha un ID come `AC-F4-1`. Questi ID tengono insieme il metodo: i task li citano, i test li verificano, i messaggi di commit li richiamano. I file del repository sono in inglese e li riporto così come sono. La parte sull'upload, accorciata:

```markdown
### Upload & ownership (Member)
- **US-13.** As a member, I want to drag and drop photos onto a target zone to upload them.
- **US-14.** As a member, I want to upload between 1 and 20 photos at once.
- **US-15.** As a member, I want each uploaded photo to show a per-file progress bar.
- **US-17.** As a member, I want the upload to fail loudly (with a clear message) if a file is over 10 MB or in an unsupported format — before any bytes leave my browser.

[...]

### F4 — Upload
- AC-F4-1: Dragging a 15 MB JPEG into the dropzone displays inline error "File exceeds 10 MB" and does not initiate the upload.
- AC-F4-2: Uploading a `.txt` file shows "Only JPG, PNG, or WebP supported" and refuses to send it.
- AC-F4-3: Submitting 21 files shows "Up to 20 files at once" and refuses to send.
- AC-F4-4: A successful upload of 5 files within 10 seconds returns a batch identifier and a list of 5 photo ids; each photo appears in the gallery with a "processing" overlay.
```

Ogni criterio ha un input preciso e un risultato che si osserva. «L'upload deve gestire bene i file grandi» non lo puoi testare; «un JPEG da 15 MB mostra "File exceeds 10 MB" e l'upload non parte» diventa un test Vitest senza bisogno di chiedere niente a nessuno.

La sezione «Out of scope» conta quanto i requisiti. Quella del Photogallery elenca quindici esclusioni per la v1, dai commenti all'autenticazione a due fattori, dal soft delete ai tag gerarchici. Ogni voce è una discussione che non devi rifare a metà progetto, e una feature che Claude non aggiunge perché gli sembrava utile.

I requisiti cambiano poco: una volta concordati con lo stakeholder, o con te stesso se il progetto è tuo, restano fermi per tutto il ciclo.

### `docs/DESIGN.md`, come costruirlo

Il design dice come realizzare i requisiti: stack con le versioni, struttura delle cartelle, schema del database, contratti API, interfacce dei servizi, autenticazione, gestione degli errori, pipeline delle immagini. È il file che gli agent aprono quando implementano, e la sua intestazione lo dichiara «authoritative for code». Nel branch di questo capitolo sono 1.297 righe in dodici sezioni, più un'appendice sulla configurazione.

Una sezione tipica è il contratto di `POST /photos`, qui con qualche campo in meno:

```markdown
#### `POST /photos` — single endpoint for 1–20 files
- **Auth:** token (`photos:write`)
- **Content-Type:** `multipart/form-data` (JSON body → 415)
- **Form fields:**

  | Field | Type | Required | Rules |
  |---|---|---|---|
  | `files[]` | File[] | yes | 1–20 items; each `image\|mimes:jpg,jpeg,png,webp\|max:10240` |
  | `album_id` | UUID | no | must exist + be owned by auth user |
  | `new_tags[]` | string[] (names) | no | up to 20; created if missing |

- **Behavior** (wrapped in `DB::transaction`):
  1. Upsert any `new_tags[]` names → tag rows (slug auto-generated, collision-resolved).
  2. Strip GPS EXIF from each file via `ExifExtractor::stripGps`.
  3. `PhotoStorage::storeOriginal(...)` writes to `photos_private` disk.
  4. Insert `Photo` row per file with `user_id = auth()->id()`, `processing_status = 'pending'`.
  5. Attach merged tag set.
  6. Wrap one `ProcessPhoto` per photo in `Bus::batch(...)`.
- **202 Accepted** with `Location: /api/v1/photos/batch/{batch_id}` header
- **Errors:** 403 (album not owned), 413, 415, 422
```

Un agent che legge questa sezione non deve decidere nulla. Sa che il body è multipart, che la risposta è 202 perché l'elaborazione è asincrona, in che ordine avvengono le scritture dentro la transazione e quali errori deve coprire con un test. Le decisioni che Claude prenderebbe da solo, magari una diversa per sessione, sono già prese e scritte. Se un flusso è difficile da seguire in un elenco, puoi chiedere a Claude di aggiungere un diagramma Mermaid, che GitHub disegna direttamente nella pagina del file.

### `docs/TASKS.md`, la lista di lavoro

Il file dei task è quello operativo, e quello che cambia più spesso. Ogni task è atomico (l'intestazione fissa il limite a 30 minuti di lavoro) e dichiara un ID, uno stato, un owner, le dipendenze, i task con cui può girare in parallelo, le sezioni da leggere, i criteri di accettazione e il messaggio di commit. Due task della Fase 2, come sono nel branch del capitolo:

```markdown
### T031 — `PhotoController@index` and `@show`
- **Status:** [ ]
- **Owner:** backend-dev
- **Depends on:** T020, T024, T026, T027
- **Parallel with:** T030, T034, T035, T036
- **Reads:** DESIGN.md §6.2
- **Acceptance:**
  - Index uses `PhotoQuery`; cursor pagination; eager loads; ≤2 SQL queries (n+1 detector enforced).
  - Show: 200 / 304 / 404 covered.
- **Commit:** `feat(api): GET /photos and /photos/{id}`

### T039 — Routes + middleware groups + rate limiters
- **Status:** [ ]
- **Owner:** backend-dev
- **Depends on:** T030–T038
- **Parallel with:** —
- **Magnet:** `routes/api.php`, `bootstrap/app.php`
- **Reads:** DESIGN.md §6.0 (rate limits), §6.1–§6.5
- **Acceptance:**
  - `routes/api.php` declares every endpoint under `/v1` prefix.
  - Auth routes throttled `10,1` per IP; everything else `120,1` per IP and `300,1` per user.
  - Mutating routes wrapped in `auth:sanctum`.
- **Commit:** `feat(api): route definitions with rate limits`
```

Le righe `Depends on` e `Parallel with` sono il motivo per cui il file esiste. T030, T031, T034, T035 e T036 sono controller diversi che toccano file diversi, quindi possono andare in parallelo. T039 invece tocca `routes/api.php` e `bootstrap/app.php`, due dei file che il progetto chiama magnet perché attirano i conflitti di merge: parte solo quando i controller sono chiusi, e lo esegue un agent solo. Quando chiedi a Claude di eseguire la Fase 2, la regola 3 del `CLAUDE.md` gli dice di usare subagent per i task paralleli (capitolo 10). L'orchestrazione la decidono le spec, e tu non devi tenere a mente quali task possono sovrapporsi. Nel capitolo 20 la stessa idea si allarga a gruppi di fasi interi, ognuno nel suo worktree.

Nel branch del capitolo `TASKS.md` contiene 112 task in 13 fasi. Su `main` il riepilogo in fondo al file ne conta 124 in 14 fasi, perché durante l'esecuzione è arrivata la Fase 14, dedicata al completamento del frontend. Un file di task cresce con il progetto, ed è giusto così.

![Dipendenze e task paralleli dichiarati in TASKS.md, nella slide del corso dedicata al file](figures/cap-18/fig-01.png)

::: {.callout .callout-tip}
[Suggerimento]{.callout-title}

Per le spec non servono Notion, Jira o Confluence. Quattro file Markdown nel repository, versionati con Git, bastano a un progetto guidato da agenti: ogni modifica alle spec finisce nella history, ogni versione si recupera e ogni diff si legge in una PR. E siccome le spec vivono accanto al codice, se il design dice una cosa e il codice ne fa un'altra Git lo registra.
:::

## 18.2 Generare i tre file con Claude

Tre file invece di uno sembrano più lavoro. Non li scrivi tu: li genera Claude dal materiale del capitolo 17, cioè `SPEC.md` e i due documenti di rifinitura `docs/database-refinement.md` e `docs/api-refinement.md` (branch `book/cap-11-prompts-and-spec` del repository companion). Il prompt usato per il Photogallery è la sezione finale di `docs/PROMPT.md`, in inglese, e chiede quattro file: i tre dell'SDD più il `CLAUDE.md`. La versione italiana, da adattare al tuo progetto:

```text
Leggi SPEC.md, docs/database-refinement.md e docs/api-refinement.md.

Genera tre file nella cartella docs/:

1. docs/REQUIREMENTS.md, cosa costruire
   - Vision e cosa il prodotto NON è
   - Personas (visitatore, membro, amministratore)
   - User stories per persona, con ID (US-01, US-02, ...)
   - Criteri di accettazione testabili, con ID (AC-F1-1, ...)
   - Vincoli (formati file, dimensioni, naming)
   - Non-functional requirements con numeri (performance, sicurezza, scalabilità)
   - Out of scope esplicito
   Niente decisioni tecniche, niente schemi, niente codice.

2. docs/DESIGN.md, come costruirlo
   - Stack con versioni precise
   - Struttura delle cartelle di backend/ e frontend/
   - Schema del database: tabelle, colonne, tipi, vincoli, indici, ON DELETE
   - Contratti API: verbo, URL, body, shape della risposta, status code
   - Interfacce dei servizi (ImageProcessor, PhotoStorage) per la DIP
   - Autenticazione, gestione degli errori, pipeline delle immagini

3. docs/TASKS.md, la lista di lavoro
   - Task atomici, al massimo 30 minuti ciascuno, raggruppati in fasi
   - Per ogni task: ID (T001, ...), stato [ ], owner (backend-dev,
     frontend-dev, code-reviewer), Depends on, Parallel with, Reads
     (sezioni da leggere), Acceptance (definition of done), Commit
   - Riferimenti alle sezioni di DESIGN.md e agli ID di REQUIREMENTS.md

Usa gli ID per la tracciabilità nelle due direzioni: ogni criterio di
accettazione deve comparire in almeno un task.
```

Prima di lanciarlo alza l'effort con `/effort high`: scrivere specifiche è il tipo di lavoro per cui il livello alto ripaga (capitolo 2).

Il primo giro esce in pochi minuti e va rivisto. Le correzioni che servono quasi sempre sono tre.

La prima riguarda la granularità. Il `TASKS.md` del primo giro tende a essere troppo fine, con un task per ogni metodo del controller, oppure troppo vago, con un task unico per tutto il frontend. La misura giusta è un file o un gruppo di file strettamente legati: abbastanza piccolo da stare in un commit, abbastanza grande da avere un criterio di accettazione che si verifica. Il Photogallery fissa il tetto a 30 minuti per task. Se vedi task da cinque minuti, accorpali; se ne vedi uno che richiederebbe ore senza un punto di controllo, spezzalo.

La seconda riguarda le dipendenze. Il modello è ottimista e dichiara spesso paralleli un task di test e il task che quel test verifica. Controlla ogni `Parallel with`: due task non possono andare in parallelo se uno dipende dall'altro, anche quando i file sembrano separati. E controlla che nessun task dipenda da un task di una fase successiva, sintomo di una fase ordinata male.

La terza riguarda i requisiti non funzionali. Restano facilmente in `REQUIREMENTS.md` senza che nessun task li implementi o li misuri. «Gallery time-to-first-tile ≤ 1.5 seconds on a 5 Mbps connection» è un requisito vero del Photogallery: deve corrispondere a un task con un criterio misurabile (cache, lazy loading, indici, paginazione a cursore), altrimenti nessuno lo verificherà mai. Nel paragrafo 18.6 vediamo che fine ha fatto.

Alla fine i tre file del branch `book/cap-12-sdd-three-files` misurano 348, 1.297 e 1.427 righe. Sono lunghi, e va bene così: nessuno li legge interi, ogni task ne apre un pezzo.

## 18.3 Il build workflow

I tre file dicono cosa costruire e come. Il build workflow dice in che ordine, con quale comando di verifica e con quale messaggio di commit per ogni fase. Senza, Claude può partire dal frontend prima delle migrazioni, scrivere i controller prima dei modelli o generare componenti React che chiamano endpoint che ancora non esistono. Su un progetto di queste dimensioni un errore di sequenza costa ore.

Nel Photogallery il workflow è la sezione 13 di `SPEC.md`, «Claude Code Build Workflow». È nato da un prompt di poche righe che trovi in `docs/claude-code-build-workflow.md`. In italiano:

```text
Aggiungi alla spec una sezione "Claude Code Build Workflow".
Elenca l'ordine esatto di costruzione, fase per fase:

Fase 1: Backend foundation (modelli, migrazioni, seed)
Fase 2: API layer (controller, rotte, resource, form request)
Fase 3: Pannello admin Filament (resource, widget, dashboard)
[...]
Fase 9: Hook (formattazione automatica, test automatici, sicurezza)
[...]
Fase 13: Spec check finale e deploy

Per ogni fase scrivi il prompt esatto da dare a Claude Code.
```

### Com'è fatta una fase

Il risultato è un runbook: ogni fase ha un obiettivo, un prompt da incollare, un comando di verifica e un messaggio di commit. In testa alla sezione c'è un preambolo da anteporre a ogni prompt dalla Fase 2 in poi:

```text
You are working inside this repo. The spec is `SPEC.md` at the repo root — it is authoritative. Read the sections referenced in the prompt and follow them literally. Do NOT invent fields, endpoints, or file paths that aren't in the spec. Run verification before claiming completion. Commit at the end with the message specified in the prompt.
```

La Fase 1, accorciata:

```markdown
### Phase 1 — Backend foundation (models, migrations, seed)
**Goal:** Laravel 13 project scaffolded, UUID primary keys wired, all five application tables migrated, models with relationships, seeded admin user.

**Prompt:**
Bootstrap the Laravel backend per SPEC.md §3.2 and §4.

1. From repo root, scaffold the Laravel app in backend/:
     composer create-project laravel/laravel backend "^13.0"
[...]
6. Write migrations in this exact order (filenames per SPEC.md §3.2):
   - create_albums_table               — without cover_photo_id FK
   - create_tags_table
   - create_photos_table               — with album_id FK (ON DELETE SET NULL, ON UPDATE CASCADE)
   - add_cover_photo_fk_to_albums      — adds cover_photo_id FK (ON DELETE SET NULL)
   - create_photo_tag_table            — composite PK, both FKs CASCADE
   All column types, nullability, defaults, and indexes MUST match SPEC.md §4 exactly.
[...]
Commit: `feat(backend): database schema, models, and seeders`

**Verify:**
cd backend && php artisan migrate:fresh --seed && php artisan tinker --execute="echo App\Models\Photo::factory()->create()->id;"
```

Il dettaglio che conta è la verifica. La fase è chiusa quando `php artisan migrate:fresh --seed` termina senza errori e la factory restituisce una riga con un UUID. Il riassunto che Claude scrive a fine lavoro non vale come prova, e il preambolo glielo ricorda: «Run verification before claiming completion».

Nota anche l'ordine delle migrazioni. `albums` nasce senza la foreign key verso la foto di copertina perché `photos` ancora non esiste, e la chiave arriva con una migrazione separata dopo. È il tipo di dettaglio che, lasciato all'improvvisazione, produce una migrazione che fallisce al primo `migrate:fresh`.

### Le regole operative

Il workflow ha bisogno anche di regole che valgono per tutte le fasi. Nel Photogallery stanno nella sezione 15 di `SPEC.md`, «Test-and-Commit Discipline»:

- un task, un commit, in formato Conventional Commits con uno scope tra `backend`, `frontend`, `db`, `filament`, `api`, `pipeline`, `ci` e `spec`
- un gate di test per ogni tipo di task: una migrazione deve passare `migrate:fresh` e il rollback, un endpoint ha un test per ogni status code documentato, un job ha un test che lo esegue in modo sincrono e controlla gli effetti
- mai `--no-verify`, mai `.skip`: se un test vecchio si rompe, `git bisect`, poi fix in avanti o revert del commit colpevole
- un branch per task (`feat/2-api-photos-store`), una PR per task, squash merge

A queste aggiungo tre segnali che per me valgono uno stop e una rilettura delle spec: un task che prende il doppio del tempo previsto, un comando di verifica che fallisce due volte di fila, e Claude che propone di modificare la spec per far passare il codice. Il codice si adatta alla spec; il contrario si fa solo con una decisione esplicita e un commit `spec:` dedicato.

Un'altra regola che uso volentieri è un file di copertura che deve restare vuoto: ogni requisito senza un task finisce lì, e finché il file ha una riga la fase corrente è bloccata. Nel Photogallery il controllo di copertura è arrivato a fine lavori, sotto forma di audit: `docs/SPEC-COVERAGE.md` mappa ogni sottosezione di `DESIGN.md` su codice e test, e il 30 aprile contava 42 sezioni, di cui 27 implementate, 11 parziali e 4 mancanti. Fatto prima dell'esecuzione costa molto meno.

### Il ciclo operativo

Approvato il workflow, l'esecuzione diventa ripetitiva, nel senso buono:

1. Copia il prompt della fase corrente dal workflow.
2. Incollalo in Claude Code, con il preambolo davanti.
3. Claude lavora e parallelizza dove i task lo permettono.
4. Lancia il comando di verifica della fase.
5. Se passa, fai il commit con il messaggio previsto e la fase successiva si sblocca.
6. Prima della fase successiva, se la sessione è carica, un `/clear` (capitolo 15).

Il vantaggio è che i prompt sono versionati insieme al codice. Se domani vuoi rigenerare il progetto da zero, o un collega vuole rifare il percorso, segue la stessa lista e passa dagli stessi passaggi, commit compresi. La domanda «cosa avevo chiesto l'altra volta?» non si pone più.

## 18.4 Il CLAUDE.md del Photogallery

Il `CLAUDE.md` l'abbiamo introdotto nel capitolo 7: è il file che Claude Code carica all'inizio di ogni sessione. La prima riga di quello del Photogallery lo chiama «project constitution», e la descrizione è giusta. Non dice cosa costruire, perché per i contenuti rimanda a `REQUIREMENTS.md` e `DESIGN.md`: dice come si lavora.

Anche questo file non si scrive a mano. Il prompt del Photogallery lo generava insieme agli altri tre; se lo fai a parte, parti da qui:

```text
Leggi docs/REQUIREMENTS.md, docs/DESIGN.md e docs/TASKS.md.
Genera un CLAUDE.md per il progetto Photogallery che contenga:
- Mappa della documentazione: quale file leggere e quando
- Project overview (3-4 righe)
- Stack tecnologico con versioni precise e comandi di installazione
- Regole non negoziabili, divise tra workflow e architettura
- Principi di qualità (SOLID, REST, KISS, DRY) con esempi presi da
  questo progetto, non definizioni generiche
- Regole di parallelizzazione e file da non modificare in parallelo
- Convenzioni di codice e regole git (branch, formato dei commit)
- La meta-regola: leggi sempre docs/REQUIREMENTS.md e docs/DESIGN.md
  prima di implementare un task, e aggiorna le caselle di
  docs/TASKS.md appena il task è chiuso
```

Nel branch del capitolo il file risultante è lungo 276 righe. Lo riporto accorciato; le parti tolte sono segnate con `[...]`:

```markdown
# CLAUDE.md — PhotoGallery Pro

> The project constitution. Loaded into every Claude Code session. **Authoritative for HOW we work**; defers to `docs/REQUIREMENTS.md` (what to build) and `docs/DESIGN.md` (technical blueprint) for content. Atomic work lives in `docs/TASKS.md`.

## Documentation map

| File | Purpose | When to read |
|---|---|---|
| `CLAUDE.md` (this file) | How we work — rules, principles, style | Every session, automatic |
| `docs/REQUIREMENTS.md` | What we're building, in plain language | Before starting any task — read the relevant feature |
| `docs/DESIGN.md` | Technical blueprint — schemas, contracts, file paths | Before implementing — read the section the task references |
| `docs/TASKS.md` | 80+ atomic tasks across 13 phases | Pick a task; check it off when done |
| `docs/SPEC-REVIEW.md` | Decision log explaining why architectural choices were made | When you disagree with a rule and want context |

## Project overview

PhotoGallery Pro is a full-stack photo gallery: users upload photos (JPG/PNG/WebP, ≤10 MB each, up to 20 at a time), organize them into albums, tag them, and browse via a masonry-grid React SPA with lightbox + keyboard navigation. The backend is a Laravel 13 REST API under `/api/v1` with a Filament v5 admin panel mounted at `/admin`. Image resizing and EXIF extraction run as queued background jobs so uploads return immediately. Same code runs locally (DB queue + local disk) and in production (SQS + S3) — only env vars change.

## Tech stack (with install commands)

[...] tabelle delle versioni e comandi composer/npm per backend/ e frontend/

## Critical rules

These are **non-negotiable**. Violations require an explicit user override.

### Workflow rules

1. **Always read `docs/REQUIREMENTS.md` and `docs/DESIGN.md` before implementing tasks.** Each task in `TASKS.md` lists which sections to read. If the task is ambiguous and the docs don't resolve it, stop and ask — do not guess.
2. **Always update `docs/TASKS.md` checkboxes after completing work.** Mark `[x]` the moment a task's acceptance criteria are met. Don't batch — checking off six tasks at once means you've drifted.
3. **Use subagents for tasks marked `parallel: true` in `TASKS.md`.** [...]
4. **One task = one commit.** Conventional Commits format: `<type>(<scope>): <subject>`. Reference SPEC sections in the body. See DESIGN.md §15.3.
5. **Tests run before commits.** Test gates per task type live in DESIGN.md §15.2. No `--no-verify`, no `.skip`, no "tests later".

### Architecture rules (cite DESIGN.md sections in PRs)

6. **`docs/DESIGN.md` is authoritative for code.** Column types, response shapes, validation rules, file paths — all defined there. Do NOT invent fields, endpoints, or directories.
[...]
8. **Every primary key is UUID v7** via the `HasUuidV7` trait. Stored as `CHAR(36)`. Never auto-increment for application tables.
9. **Two photo disks. All file I/O goes through them.**
   - `Storage::disk('photos')` — public-read; sized variants only
   - `Storage::disk('photos_private')` — private; originals only; signed URLs only

   Never use `File::`, `fopen`, `copy`, or `move_uploaded_file`. (DESIGN.md §11)
10. **Authorization, not just authentication.** Every mutating controller calls `$this->authorize($action, $model)` AND `$request->user()->tokenCan('photos:write'|'albums:write')`. (DESIGN.md §6.4a, §9)
11. **Wrap multi-write operations in `DB::transaction(...)`.** Photo upload (insert + tag attach + dispatch), photo update (update + tag sync), album with cover. (DESIGN.md §6.4a)

[...] regole 12-14: eager loading, setup di Tailwind v4, stringhe della UI in frontend/src/data/

## Engineering principles (project-specific)

Generic principle definitions are useless. Here's how each applies to **this** codebase.

[...] SOLID, REST, KISS e DRY: li vediamo nel paragrafo 18.5

## Parallelization rules

[...] wave, track paralleli e file "magnet" da non modificare in parallelo

## Code style

[...] Pint, PSR-12, strict types, final by default, Prettier, ESLint, Conventional Commits

## Before writing any class, ask:

[...]
3. **Does an existing service/contract already cover this?** Check `app/Contracts/`, `app/Services/`, `app/Actions/`, `app/Queries/` before creating new files.
[...]

## When stuck

- **Ambiguity in REQUIREMENTS.md:** ask the user; don't invent acceptance criteria.
- **Conflict between REQUIREMENTS.md and DESIGN.md:** REQUIREMENTS wins; DESIGN gets a `spec:` PR to align.
[...]
```

Le regole che funzionano sono quelle che si possono verificare. «Gestisci bene i file» non dice niente a nessuno; la regola 9 dice quali dischi esistono, cosa va su ciascuno e quali funzioni PHP sono vietate. La regola 10 non chiede attenzione alla sicurezza in generale: chiede due chiamate precise in ogni controller che modifica dati, e una review può controllare riga per riga se ci sono. La sezione «When stuck» copre i momenti in cui un agente senza istruzioni improvvisa, come un requisito ambiguo o un design che contraddice i requisiti.

Una nota onesta: 276 righe sono troppe. Nel capitolo 7 abbiamo visto che conviene restare sotto le 200 circa, perché un file lungo consuma contesto e viene seguito peggio, e su `main` questo file è cresciuto fino a 391 righe. I candidati per uscire sono le sezioni di stile, che servono solo quando Claude tocca certi file. Lo stile PHP, per esempio, può andare in `.claude/rules/php.md` e caricarsi solo per i file del backend:

```markdown
---
paths:
  - "backend/**/*.php"
---

# PHP code style
- Pint with Laravel preset; PSR-12 baseline.
- `declare(strict_types=1);` in app/Services, app/Actions, app/Jobs, app/Queries.
- Final by default. Mass assignment only via `$request->validated()`.
```

### Dove il CLAUDE.md non basta

Il `CLAUDE.md` orienta Claude, ma non lo obbliga. «No `--no-verify`» è un'istruzione che Claude segue quasi sempre, e quel quasi in un progetto da cento e passa task prima o poi si presenta. Per le regole che non puoi permetterti di veder saltare ci sono strumenti più forti. Le regole di permesso del capitolo 11 bloccano un comando qualunque cosa dica la conversazione: un `deny` su `Bash(git push --force *)` vale anche quando una sessione lunga ha perso di vista le istruzioni. Gli hook del capitolo 12 fanno il resto. La Fase 9 di `TASKS.md` ne prevede già alcuni, Pint e Prettier dopo ogni modifica e un blocco sui comandi distruttivi. Per l'SDD il più utile è un hook `Stop` che lancia `php artisan test --compact` e, se i test falliscono, rimanda Claude al lavoro con l'errore: la definition of done la fa rispettare il harness.

`/goal`, che usiamo nel capitolo 20, porta la stessa idea sui criteri di accettazione. Trasforma un criterio in una condizione di completamento: Claude continua a lavorare, turno dopo turno, finché un valutatore separato non la giudica soddisfatta. Il valutatore vede solo quello che Claude mostra nella conversazione, quindi la condizione deve nominare un controllo che Claude esegue davvero:

```text
/goal php artisan test --compact termina con exit code 0 e i task T019-T045 in docs/TASKS.md sono tutti segnati [x]
```

## 18.5 SOLID, KISS e DRY nel workflow

I principi del clean code li conosci. Il difficile è farli applicare con coerenza a un agente che cambia sessione, che non ricorda i prompt di ieri e che tende all'ottimismo architetturale, cioè ad aggiungere strati e astrazioni per un futuro che non arriverà. Per questo i principi stanno nel `CLAUDE.md` e non nel prompt: lì sopravvivono a `/clear` e alle sessioni nuove, e ogni sessione parte già allineata.

La sezione del Photogallery si apre con una riga che riassume il metodo: «Generic principle definitions are useless. Here's how each applies to this codebase.» La definizione di SRP Claude la conosce già. Quello che non sa è quale classe del tuo progetto deve avere una sola responsabilità, e cosa invece non deve fare.

### SOLID applicato alle specifiche

SOLID dà risultati concreti quando chiedi a Claude di rivedere le spec con quei principi in mano: l'output nomina file, classi e sezioni. La review di `SPEC.md`, salvata in `docs/SPEC-REVIEW.md`, ha trovato tra l'altro che `ImageProcessor` ed `ExifExtractor` erano classi concrete usate direttamente da chi ne aveva bisogno, e che tutta la logica di filtro di `GET /photos` (ricerca, tag in AND, album, preferite, ordinamento) viveva dentro `PhotoController@index`.

Le correzioni sono passate nel design e poi nel codice. Per la Dependency Inversion ci sono tre interfacce in `app/Contracts/`, collegate alle implementazioni concrete in `AppServiceProvider`:

```php
$this->app->bind(ImageProcessor::class, InterventionImageProcessor::class);
$this->app->bind(ExifExtractor::class, PhpExifExtractor::class);
$this->app->bind(PhotoStorage::class, DiskPhotoStorage::class);
```

Il job che elabora le foto riceve le astrazioni e non sa quale implementazione c'è dietro:

```php
final class ProcessPhoto implements ShouldQueue
{
    use Batchable, Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $tries = 3;

    /** @var int[] */
    public array $backoff = [10, 30, 60];

    public function __construct(public readonly Photo $photo) {}

    public function handle(ImageProcessor $processor, ExifExtractor $exif): void
    {
        // ...
    }
}
```

Nei test si collega un `FakeImageProcessor` e il job non se ne accorge: è la sostituibilità di Liskov, e il `CLAUDE.md` la scrive come regola («Tests must not need to know which is bound»). Le due interfacce sono separate apposta. Ridimensionare un'immagine ed estrarne l'EXIF sono due motivi diversi per cambiare, e chi usa l'una non deve dipendere dall'altra: Interface Segregation. Per la Single Responsibility, i filtri sono usciti dal controller e sono finiti in `App\Queries\PhotoQuery`, che riusa anche il pannello Filament. Un nuovo ordinamento diventa un nuovo caso in `applySort()` e il controller non si tocca, che è l'Open/Closed detto con un esempio.

C'è poi un errore che la review ha corretto e che stava nel prompt iniziale. Nella sezione SOLID di `docs/PROMPT.md` c'è scritto «PhotoController receives PhotoRepository, not raw queries»; poche righe sotto, nella sezione KISS, «Don't create a Repository pattern if you only have one Eloquent model usage». Due istruzioni in conflitto nello stesso prompt. Il `CLAUDE.md` finale ha scelto KISS: niente repository, Eloquent usato direttamente, la logica in Action, Service e Query. Quando il prompt si contraddice Claude sceglie da solo, e non è detto che scelga la stessa cosa in due sessioni diverse. Rileggere il proprio prompt cercando contraddizioni è il primo controllo da fare.

### KISS contro l'over-engineering

KISS è il principio più difficile da far rispettare a un modello. Senza un freno esplicito Claude aggiunge factory, builder, classi base astratte e layer di indirezione nel caso servano, e il codice che ne esce è corretto ma inutilmente complicato.

La sezione KISS del Photogallery non elenca virtù, elenca decisioni:

```markdown
### KISS

The smallest implementation that meets the acceptance criteria wins.

- One upload endpoint (`POST /photos` accepts 1–20 files), not two. Frontend doesn't branch.
- One polling loop after upload (`GET /photos/batch/{id}` includes per-photo statuses), not two.
- Cursor pagination, not page+offset+`total` (the gallery doesn't need a count).
- Tags are a flat global vocabulary, not a hierarchy. v1 has no tag categories, no tag descriptions, no tag colors.
- Soft deletes are out of scope for v1. Deletes are permanent. We can add `deleted_at` later if undo becomes a requirement.
```

Quasi ogni riga viene da una semplificazione trovata in review. La spec iniziale aveva due endpoint di upload, `POST /photos` per una foto e `POST /photos/batch` per almeno due, e il frontend doveva scegliere quale chiamare. Dopo l'upload partivano due loop di polling, uno per foto e uno per il batch. Il parametro di ordinamento mescolava stili diversi (`newest`, `title_asc`, `favorites_first`) ed è stato diviso in `sort` e `order`. Altri casi da bloccare in anticipo, perché Claude li propone spesso: un DSL per i filtri dove bastano parametri URL, una classe base astratta per i controller, un servizio di configurazione che gestisce otto tipi di config che la spec non chiede, uno Strategy pattern per un'operazione che ha una strategia sola.

![Le sezioni KISS e DRY di PROMPT.md, il prompt da cui sono nate le spec, nell'anteprima Markdown dell'IDE](figures/cap-18/fig-02.png)

Una tecnica che aiuta: chiedi che ogni alternativa scartata resti scritta, con il motivo. Il Photogallery tiene `docs/SPEC-REVIEW.md` come registro delle decisioni, e il `CLAUDE.md` lo indica come il file da leggere «when you disagree with a rule and want context». Una decisione con la motivazione accanto è molto più difficile da ribaltare a metà esecuzione, da parte tua come da parte di Claude.

### DRY e la regola del tre

DRY applicato male produce astrazioni premature, che fanno più danni della duplicazione che volevano togliere. Il `CLAUDE.md` del Photogallery lo risolve in due righe: «DON'T abstract until the second occurrence. The third occurrence is when extraction becomes required.» Alla seconda ripetizione aspetti, alla terza estrai.

Il caso concreto: la review ha trovato la stessa logica di upsert dei tag per nome in tre controller (creazione foto, modifica foto, upload batch). Oggi vive in un solo servizio, `App\Services\TagAssigner`, usato dall'API e dal form di Filament:

```php
final class TagAssigner
{
    /**
     * @param  list<string>  $names
     */
    public function syncByNames(Photo $photo, array $names): void
    {
        DB::transaction(function () use ($photo, $names): void {
            $tagIds = [];

            foreach (array_filter(array_map('trim', $names)) as $name) {
                $tagIds[] = $this->resolveTag($name)->id;
            }

            $photo->tags()->sync($tagIds);
        });
    }

    // resolveTag() e uniqueSlugFor(): ricerca per nome, slug con suffisso -2, -3, ...
}
```

Lo stesso vale per le liste di eager loading, che il `CLAUDE.md` vuole come costanti sulla Resource e non ripetute in ogni controller. Il controllo prima di scrivere sta nella checklist «Before writing any class, ask»: il punto 3 chiede di guardare in `app/Contracts/`, `app/Services/`, `app/Actions/` e `app/Queries/` prima di creare un file nuovo. Claude lo fa con `Grep` e `Glob` in pochi secondi, ma solo se una regola glielo chiede; altrimenti tende a scrivere la sua versione da zero.

### La self-review prima del commit

Con i principi nel `CLAUDE.md` puoi chiedere a Claude di rivedere il proprio lavoro prima di committarlo:

```text
Prima di committare il task corrente, fai una self-review del codice che
hai scritto. Verifica che rispetti SRP, KISS e DRY come sono descritti nel
CLAUDE.md. Se trovi violazioni, correggile, rilancia i test e poi committa.
```

La self-review funziona perché ha un riferimento preciso: la domanda non resta astratta, diventa «questo upload è dentro `DB::transaction` come dice la regola 11?». Di solito emergono un metodo che valida, salva e accoda nello stesso blocco, un helper copiato in due service, una classe di configurazione con sezioni che nessuna spec chiede. Per una review più seria, fatta da un subagent con un contesto pulito, c'è `/code-review`, che legge anche il `CLAUDE.md`: la usiamo nel capitolo 22.

## 18.6 Analisi critica delle spec

Le spec del primo giro non sono mai giuste. Il modello produce architetture eleganti e task pieni di verbi d'azione, ma da solo non controlla che i task coprano tutti i requisiti, né che i criteri di accettazione si possano misurare. La fase che si salta più spesso è quella tra la generazione e l'esecuzione: rileggere i file cercando ambiguità, rischi e requisiti rimasti scoperti.

### Lo spec-critic

Il metodo che funziona meglio è un agent con un ruolo avversariale, in una sessione pulita o come subagent (capitolo 10):

```text
Leggi docs/REQUIREMENTS.md, docs/DESIGN.md e docs/TASKS.md.
Il tuo ruolo è quello di un senior engineer scettico che deve trovare
tutto quello che potrebbe andare storto prima che l'esecuzione inizi.

Produci un report strutturato con:
1. Vulnerabilità di sicurezza nelle spec (non nel codice, nelle spec)
2. Requisiti senza task corrispondente (gap di copertura)
3. Task senza requisito corrispondente (potenziale out of scope)
4. Non-functional requirements senza implementazione prevista
5. Ambiguità che potrebbero generare interpretazioni diverse tra agenti
6. Stime di effort ottimistiche di più del 50%
7. Dipendenze circolari o mal ordinate in docs/TASKS.md
8. Rimandi tra file che puntano a sezioni inesistenti

Per ogni problema: categoria, descrizione, impatto, fix suggerito.
Non essere diplomatico. Il tuo obiettivo è trovare problemi, non validare.
```

Il report è una lista di problemi per categoria. Per ciascuno decidi tu se è una critica fondata o una pignoleria. Le critiche fondate tornano nelle spec, e solo dopo parti con l'esecuzione.

::: {.callout .callout-tip}
[Suggerimento]{.callout-title}

Una review collaborativa, che la faccia tu o Claude, trova soprattutto quello che ti aspetti di trovare. Chiedere in modo esplicito di cercare problemi, e di non confermare che va tutto bene, fa emergere le assunzioni implicite e i casi limite che nessuno aveva messo per iscritto. L'ultima riga del prompt serve a questo.
:::

### Cosa è cambiato nelle spec del Photogallery

Sul Photogallery la review ha prodotto `docs/SPEC-REVIEW.md`: 272 righe di problemi raggruppati per area (SOLID, REST, KISS, backend, frontend, database), applicati poi a `SPEC.md` in sette blocchi. Quattro modifiche riguardano la sicurezza e sono un buon esempio di cosa salta fuori.

Gli originali stavano sul disco pubblico. In `docs/SPEC-VALIDATION.md`, il controllo di comprensione fatto su `SPEC.md` il 25 aprile, il flusso di upload salvava l'originale con `Storage::disk('photos')`, lo stesso disco delle miniature, e la risposta dell'API conteneva già `urls.original`. Il file arrivava sul disco così com'era stato caricato, EXIF compreso: con le coordinate GPS di una foto scattata in giardino, chiunque risaliva all'indirizzo di casa di chi l'aveva caricata. Nella versione corretta i dischi sono due e il GPS sparisce prima del salvataggio:

```markdown
### 12.1 Two-disk model
- `Storage::disk('photos_private')` — originals only. Local: `storage/app/photos-private/`. Production: private S3 bucket with Block Public Access ON. URLs only via `temporaryUrl(...)` with 5-min TTL.
- `Storage::disk('photos')` — sized variants only. Local: `storage/app/public/photos/` + `php artisan storage:link`. Production: public S3 bucket fronted by CloudFront.
```

Il requisito corrispondente è in `REQUIREMENTS.md`, NFR-3: «GPS EXIF must be stripped before originals are stored and before any EXIF JSON is returned by the API.»

I token Sanctum non avevano abilities: un token valido poteva fare tutto quello che l'utente poteva fare. Ora i token portano abilities come `photos:write` e `albums:write`, e la regola 10 del `CLAUDE.md` impone a ogni controller che modifica dati sia la policy sia il controllo `tokenCan`.

I rate limit erano solo per IP. Dietro un NAT aziendale o un proxy condiviso, cento utenti legittimi esaurivano insieme lo stesso limite. Ora le rotte non di autenticazione hanno anche un limite per utente, 300 richieste al minuto, e il criterio di accettazione di T039 lo verifica.

La superficie di mass assignment non era coperta da nessuna regola. Ora c'è, scritta in due punti del `CLAUDE.md`: `$model->fill($request->validated())`, mai `$request->all()`.

Il controllo va fatto anche sui rimandi tra file, perché lo split di un documento grande li rompe facilmente. Nel branch del capitolo il `CLAUDE.md` rimanda a `DESIGN.md §15.2` per i gate di test, a `§15.3` per i commit e a `§14` per il piano di parallelizzazione, ma `DESIGN.md` si ferma alla sezione 12: le sezioni 14 e 15 sono rimaste in `SPEC.md`. E la mappa della documentazione parla di «80+ atomic tasks» mentre il file ne contiene 112. Sono errori piccoli, ma un agent che segue un rimando verso una sezione che non c'è o si ferma, o inventa. Per questo nel prompt dello spec-critic c'è il punto 8.

### Domande di copertura

Oltre alla sicurezza, lo spec-critic deve controllare la copertura nelle due direzioni, dai requisiti ai task e dai task ai requisiti. Sono quattro domande da fare ogni volta:

```text
Per ogni feature in docs/REQUIREMENTS.md, elencami i task in docs/TASKS.md
che la implementano. Segnala le feature senza task.

Per ogni criterio di accettazione in docs/REQUIREMENTS.md, dimmi quale
task lo ha nella propria sezione Acceptance. Segnala i criteri orfani.

Per ogni NFR (performance, scalabilità, sicurezza), indicami quale scelta
in docs/DESIGN.md o quale task in docs/TASKS.md ne garantisce il rispetto.
Segnala gli NFR senza implementazione prevista.

Trova cicli di dipendenze in docs/TASKS.md. Trova task che dipendono da
task di fasi successive.
```

Sul branch del capitolo queste domande trovano buchi veri:

- NFR-1 chiede un time-to-first-tile della galleria entro 1,5 secondi su una connessione da 5 Mbps, e nessun task lo cita.
- Sempre NFR-1 chiede un punteggio Lighthouse di almeno 90 su desktop e 75 su mobile; T108 verifica solo il desktop.
- AC-F1-2 vuole 2 colonne a 375 px, 3 a 768 e 4 a 1280. `DESIGN.md §8.4` ha le classi giuste (`columns-2 md:columns-3 lg:columns-4`), ma i criteri di T067 non nominano i breakpoint, quindi nessun test li controllerà.

La rimozione del GPS, al contrario, è coperta bene: T074 chiede un test con un'immagine di prova che contiene coordinate GPS, e la review di fine Fase 6 (T080) lo ricontrolla dopo l'elaborazione completa. Un requisito di sicurezza scritto in modo verificabile tende a ricevere un task; un requisito di performance scritto come numero in un elenco si perde più facilmente.

Quando trovi un buco, non sistemarlo a mano. Chiedi a Claude di inserire il task mancante nella fase giusta e di aggiornare le dipendenze:

```text
Sulla base dei gap identificati, aggiungi i task mancanti nelle fasi
appropriate, aggiorna le dipendenze e riallinea il CLAUDE.md se cambiano
i rimandi. Non toccare i task già definiti: aggiungi soltanto.
```

### Stimare l'effort sulle aree a rischio

Il modello è ottimista anche sui tempi. Con 112 task da 30 minuti al massimo il conto teorico resta sotto le 60 ore; la review del Photogallery stimava invece 15-20 giorni di lavoro in sequenza e 8-10 con tre track in parallelo. La differenza sta quasi tutta in poche aree, che conviene rivedere a una a una e spezzare dove serve.

La pipeline asincrona. Scrivere `ProcessPhoto` è facile, gestirne i fallimenti no: retry con backoff di 10, 30 e 60 secondi, stato `failed`, pulizia delle varianti già generate nel metodo `failed()`, coerenza tra lo stato nel database e i file sui dischi.

L'upload. Drag and drop e selezione dei file sono due interfacce sullo stesso endpoint, con una progress bar per file, la validazione lato client prima che parta un byte e il polling del batch. AC-F4-4 dà la misura: cinque file accettati entro 10 secondi, ognuno visibile in galleria con l'overlay di elaborazione. Spesso quello che sembrava un task ne diventa tre.

Il lightbox. Sembra un componente, ma include navigazione da tastiera, prefetch della foto successiva, focus trap, un URL con `?photo=` che apre la foto al caricamento e si pulisce alla chiusura. Se è un task solo, probabilmente andrebbe diviso.

Locale e produzione. In locale SQLite o MySQL, coda su database e disco locale; in produzione MySQL o Postgres, SQS e due bucket S3. Le migrazioni devono restare neutrali rispetto al database e le code vanno provate in entrambe le configurazioni. Il setup locale e quello di produzione sono due lavori distinti, e infatti nel Photogallery la migrazione verso AWS è una fase a sé, la 8.

### Quando fermarsi

Una o due iterazioni di review sono normali. Se ne servono tre o più, il problema è a monte: i requisiti erano troppo vaghi, e conviene riscriverli prima di andare avanti.

Quando le spec ti convincono, senza pretendere che siano perfette, committa i quattro file, fai `/clear` (le spec sono su disco, non serve tenerle nella conversazione) e parti. A contesto pulito Claude legge il `CLAUDE.md`, poi `docs/TASKS.md`, sceglie il primo task con le dipendenze soddisfatte e comincia. È quello che facciamo nel capitolo 19.

## Riepilogo

- I tre file separano cosa costruire (`docs/REQUIREMENTS.md`), come costruirlo (`docs/DESIGN.md`) e in che ordine (`docs/TASKS.md`); il `CLAUDE.md` dice come si lavora e rimanda agli altri.
- Ogni task dichiara dipendenze, parallelismo, sezioni da leggere e criteri di accettazione: sono le spec a stabilire cosa può girare in parallelo e cosa no.
- Il build workflow dà a ogni fase un prompt, un comando di verifica e un messaggio di commit. La fase è chiusa quando la verifica passa.
- SOLID, KISS e DRY nel `CLAUDE.md` funzionano quando nominano classi e decisioni del progetto. Per le regole che non possono saltare servono permessi e hook (capitoli 11 e 12), e `/goal` (capitolo 20) per i criteri di accettazione.
- Prima di eseguire, uno spec-critic avversariale e le domande di copertura: ogni requisito non funzionale deve avere un task che lo verifica, e ogni rimando tra file deve puntare a una sezione che esiste.

## Esercizio

Prendi un tuo progetto con almeno cinque feature distinte, crea un branch (per esempio `sdd-mio-progetto`) e genera i tre file con il prompt riusabile di questo capitolo. Lancia lo spec-critic del paragrafo 18.6 in una sessione pulita, classifica ogni problema del report come critico, importante o pignoleria, e applica alle spec i fix dei primi due gruppi. Per confronto, il risultato sul Photogallery è nel branch `book/cap-12-sdd-three-files` del repository companion.

L'esercizio è finito quando ogni NFR di `docs/REQUIREMENTS.md` compare nei criteri di accettazione di almeno un task, i file sono committati sul tuo branch e hai trovato almeno tre problemi che prima dello spec-critic non avevi visto. Se non arrivi a tre, la review non era abbastanza avversariale: rilanciala chiedendo esplicitamente di essere più severa.
