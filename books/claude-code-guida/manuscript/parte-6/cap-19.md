# Capitolo 19. Esecuzione e code review, dai primi task alla wave review

## Cosa imparerai

Come eseguire i task di `docs/TASKS.md` con un commit per task, come aprire e far revisionare la PR di fine fase, come organizzare una wave review con quattro subagent specializzati e cosa controllare in controller, policy, gestione delle eccezioni e nel pannello admin Filament del Photogallery.

Prerequisiti: i capitoli 17 e 18, con `docs/REQUIREMENTS.md`, `docs/DESIGN.md` e `docs/TASKS.md` pronti (branch `book/cap-12-sdd-three-files`). La GitHub CLI (`gh`) autenticata, i plugin Superpowers e `commit-commands` installati (capitolo 8).

Dopo due capitoli di specifiche, qui si scrive codice. `REQUIREMENTS.md` dice cosa deve fare il Photogallery, `DESIGN.md` dice come, `TASKS.md` divide il lavoro in task da mezz'ora al massimo. Per questo il prompt di esecuzione può essere corto: il contesto è già nei file.

La differenza con il vibecoding si vede dopo. In una sessione improvvisata, dopo un'ora hai codice che sembra funzionare; tre giorni dopo aggiungi una feature, scopri che la struttura non regge e nessuno ricorda perché una scelta è stata fatta. Con le spec, quando al task 47 ti chiedi perché le chiavi primarie sono UUID v7 e non auto-increment, la risposta è scritta: regola 8 del `CLAUDE.md` del progetto e `DESIGN.md` §4, messe lì prima della prima migration.

Il ciclo è sempre lo stesso: esegui un task, verifica, committa, passa al successivo. A fine fase apri una PR e la fai revisionare. La review lavora su tre livelli. Il primo è il singolo task, mentre Claude lavora: diff letto, test verdi, linter pulito. Il secondo è la fase, a PR aperta, con reviewer automatici e finding classificati per severità. Il terzo è la wave, un gruppo di fasi che costruiscono insieme un pezzo di architettura: la wave review cerca le incoerenze tra moduli, come una policy applicata in un controller e dimenticata in quello accanto, che guardando un task alla volta non vedi.

## 19.1 Eseguire i primi task

### `TASKS.md` come stato del progetto

Prima di scrivere una riga, Claude controlla l'ambiente: se esiste un repository Git, se c'è un remote `origin`, le versioni di PHP, Composer e Node, i tool che il progetto richiede. Poi legge `docs/TASKS.md`.

All'inizio dell'esecuzione il file del Photogallery conteneva 112 task in 13 fasi, con ID nella forma `T001`. Claude li conta, riporta il numero e propone un perimetro realistico per la sessione: la Fase 1, da `T001` a `T018`, perché l'intero piano in un solo contesto non ci sta. Nella versione finale del repo i task sono 124 in 14 fasi; quelli in più arrivano con le feature del capitolo 21.

Il prompt per partire è volutamente semplice:

```text
Procedi con i task della Fase 1 secondo docs/TASKS.md.
Un commit per task, una pull request per fase.
Usa subagent dove i task sono indipendenti.
```

Non spiega niente perché non deve: il prompt dà il via, il resto è scritto nelle spec.

### Task indipendenti in parallelo

Ogni task di `TASKS.md` ha un campo `Parallel with`. `T001` (scaffold del backend Laravel) e `T002` (scaffold del frontend con Vite e React) si citano a vicenda, con la nota "different working dir": uno lavora in `backend/`, l'altro in `frontend/`. Claude li lancia come due subagent, e mentre uno esegue `composer create-project` l'altro esegue `npm create vite@latest`.

Non serve chiederlo con un'istruzione dedicata. Le dipendenze sono nel piano, e la regola 3 del `CLAUDE.md` del Photogallery dice di usare i subagent per i task marcati come paralleli. È la stessa logica dei job indipendenti in una pipeline di CI: dove non ci sono dipendenze, si gira insieme.

::: {.callout .callout-warning}
[Attenzione]{.callout-title}

Un subagent isola il contesto, non i file: tutti lavorano nello stesso working tree. Con `T001` e `T002` va bene, le cartelle sono separate. Già `T004`, `T005`, `T006` e `T017`, paralleli tra loro, toccano file diversi dello stesso `backend/` e committano sullo stesso branch: due agent che lanciano `git add` e `git commit` insieme possono finire uno nel commit dell'altro, e se il piano sbaglia e due task toccano lo stesso file, l'ultimo che scrive vince. Per questo il `CLAUDE.md` del progetto elenca i file da non modificare mai in parallelo (`bootstrap/app.php`, le migration, `composer.json` e altri). Il metodo di questo capitolo funziona, ma quando una wave ha molti task indipendenti conviene dare a ciascuno il suo worktree: il capitolo 20 lo fa con `claude --worktree`, `/goal` e l'agent view.
:::

### Permessi: meno interruzioni

Dalla versione 2.1.283 le sessioni interattive partono in auto mode (capitolo 11): un classificatore lascia passare le azioni coerenti con la richiesta e blocca quelle rischiose, quindi comandi come `composer install` o `php artisan migrate` di solito passano senza domande. Se invece lavori in modalità Manual, ogni comando nuovo chiede conferma, e in una sessione di esecuzione le richieste diventano decine. Conviene registrare i comandi di routine come regole `allow` in `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(composer *)",
      "Bash(npm install *)",
      "Bash(npm create *)",
      "Bash(php artisan *)",
      "Bash(vendor/bin/pest *)",
      "Bash(vendor/bin/pint *)"
    ]
  }
}
```

Con queste regole Claude esegue quei comandi senza chiedere, e tu intervieni solo quando qualcosa si rompe. Aggiungi una regola quando l'intera famiglia di comandi è sicura per quel progetto, e lascia stare `Bash(*)`: vuoi togliere il rumore sui comandi che conosci, non il controllo. Ricorda che una regola Bash confronta il testo del comando, non il programma (capitolo 11).

### Non andare avanti se qualcosa è rotto

Un task si spunta in `TASKS.md`, da `[ ]` a `[x]`, solo quando i suoi criteri `Acceptance` sono soddisfatti: test verdi (`vendor/bin/pest` nel backend), linter pulito (`vendor/bin/pint --test`, ESLint nel frontend) e diff letto da te.

Se un test fallisce, Claude si ferma. Non spunta il task con la promessa di tornarci e non passa al successivo. Il `CLAUDE.md` del progetto lo dice in chiaro: niente `--no-verify`, niente `.skip`, niente "tests later". Un task rotto lasciato indietro torna fuori nel momento peggiore, di solito quando stai per aprire la PR di fase. La diagnosi si fa subito:

```text
Il test PhotoObserverTest fallisce. Analizza il test, individua la causa,
proponi il fix, applicalo e verifica che la suite torni verde prima di
andare avanti.
```

Tienilo pronto, e non chiedere mai a Claude di "ignorare per ora". Il ciclo è: task, test, commit se è verde, diagnosi immediata se è rosso, poi commit.

### Commit atomici e tracciabili

Dopo i primi task, `git log` mostra messaggi che puntano al piano. Questi sono due commit del branch `book/cap-13-wave-1-backend`, accorciati:

```text
chore(backend): scaffold Laravel 13 with core dependencies

T001 — DESIGN.md §2, CLAUDE.md "Tech stack".

Backend skeleton via composer create-project laravel/laravel ^13.0
(installs Laravel Framework 13.6.0).

chore(backend): publish framework migrations; tokenable_id is CHAR(36)

T003 — DESIGN.md §4.6, §4.7.

- Published Sanctum config and personal_access_tokens migration via
  vendor:publish.
- Edited the published migration to make `tokenable_id` CHAR(36) via
  uuidMorphs() so it can reference UUID v7 user ids (DESIGN.md §4.6).
  Also switched the token PK to uuid for consistency.
```

Il soggetto è in formato Conventional Commits ed è quello suggerito dal campo `Commit` del task. La prima riga del corpo dice quale task è e quali sezioni di `DESIGN.md` lo governano. Sei mesi dopo, quando qualcuno chiede perché `tokenable_id` è `CHAR(36)`, basta cercare `T003` nel log: si arriva al task in `TASKS.md` e da lì a `DESIGN.md` §4.6, scritto prima del codice. Questa tracciabilità esce dal processo, non dalla buona volontà di chi committa.

Tieni d'occhio l'ultima riga del secondo commit, "Also switched the token PK to uuid for consistency": la spec non lo chiedeva. Ci torniamo in §19.2.

### I task di configurazione

I task più noiosi da fare a mano sono quelli di configurazione: installare un pacchetto, pubblicarne i file, modificare una migration, aggiungere una chiave al `.env`. Serve precisione, non creatività, ed è dove Claude rende meglio, perché esegue i passi nell'ordine giusto senza saltarne.

Nel Photogallery `T006` configura due dischi in `config/filesystems.php`, `photos` (pubblico, solo le varianti ridimensionate) e `photos_private` (gli originali), con il driver scelto da `PHOTOS_DRIVER`. `T017` crea `config/photogallery.php` con i parametri del dominio, copiati dall'Appendice A di `DESIGN.md`:

```php
<?php

declare(strict_types=1);

return [
    'images' => [
        'max_dimension' => env('PHOTOS_MAX_DIMENSION', 8000),
        'max_file_size_kb' => env('PHOTOS_MAX_FILE_SIZE_KB', 10240),
        'variants' => [
            'thumbnail' => ['width' => 300, 'quality' => 80],
            'medium' => ['width' => 800, 'quality' => 85],
            'large' => ['width' => 1600, 'quality' => 90],
        ],
    ],
    'urls' => [
        'original_signed_ttl' => 300,
    ],
    'rate_limits' => [
        'auth_per_ip_per_minute' => 10,
        'api_per_ip_per_minute' => 120,
        'api_per_user_per_minute' => 300,
    ],
];
```

I limiti che cambiano tra ambienti arrivano da variabili d'ambiente, il resto ha un posto solo invece di numeri sparsi nel codice. Claude rispetta la convenzione perché è nelle spec: la regola 10 del `CLAUDE.md` chiede di aggiungere ogni nuova variabile sia a `.env.example` sia all'Appendice A nello stesso commit. Senza quella riga avrebbe scritto i valori nel codice.

Compaiono anche i primi pezzi riutilizzabili: il trait `App\Concerns\HasUuidV7` (`T004`), che genera UUID v7 come chiave primaria, e due enum (`T005`): `ProcessingStatus` con `Pending`, `Processing`, `Completed`, `Failed`, e `TokenAbility` con le ability dei token Sanctum `photos:write`, `albums:write` e `admin`. Gli enum danno al codice lo stesso vocabolario dei documenti di spec, e i typo diventano errori di tipo invece di bug a runtime.

### Il dominio prende forma

Con le migration da `T007` a `T012` emerge il dominio: utenti, album, tag, foto e la pivot `photo_tag`. La tabella `photos` ha `user_id`, `album_id`, `title`, `filename`, `original_path`, i tre percorsi delle varianti (`thumbnail_path`, `medium_path`, `large_path`), `is_favorite`, `exif` in JSON e `processing_status`, più gli indici composti che `DESIGN.md` §4.4 elenca uno per uno. La pivot ha una chiave primaria composta (`photo_id`, `tag_id`).

I model di `T013` seguono le relazioni di `DESIGN.md` §5. `Album` ha `belongsTo(User)`, `hasMany(Photo)` e `belongsTo(Photo::class, 'cover_photo_id')` per la copertina; `Photo` e `Tag` si collegano con `belongsToMany` attraverso la pivot.

La relazione interessante è la copertina. L'album punta a una foto, e la foto punta al suo album: è una foreign key circolare, e nessuna delle due tabelle si può creare per prima con entrambi i vincoli. Il piano la risolve con due task. `T008` crea `albums` con la colonna `cover_photo_id` ma senza vincolo, e `T011` aggiunge la foreign key con una migration separata dopo che `photos` esiste. Claude non ha dovuto inventarsi niente: il problema era già stato visto e diviso in task durante la stesura delle spec.

### Quando fermarsi

In una sessione di esecuzione lunga arriva un momento in cui Claude perde coerenza con le decisioni dell'inizio. Propone nomi diversi, suggerisce strutture che contraddicono i task precedenti, dimentica convenzioni rispettate nei primi venti commit. È il segnale che il contesto è troppo pieno di dettagli vecchi.

Il modello di default ha una finestra da 1M token, quindi il limite fisico arriva tardi, ma la deriva può arrivare prima. Controlla con `/context` quanto sei pieno e usa i due strumenti del capitolo 15. Nel mezzo di una fase, `/compact` riassume la conversazione; dagli istruzioni su cosa conservare:

```text
/compact conserva lo stato dei task della Fase 1, le decisioni su UUID v7 e Sanctum e i finding ancora aperti
```

Tra una fase e l'altra, `/clear` riparte da zero, e Claude rilegge dai file lo stato aggiornato: `CLAUDE.md`, `DESIGN.md`, `TASKS.md` con le caselle spuntate. Una fase per sessione è un buon ritmo. Non aspettare che la qualità peggiori: un riavvio programmato costa molto meno di cinque commit incoerenti da correggere.

## 19.2 La PR della Fase 1: prima review

### Aprire la PR a fine fase

Quando tutti i task della Fase 1 sono spuntati, il branch `feat/phase-1-backend-foundation` contiene i commit dei 18 task, 21 in tutto contando le pulizie di Pint e un fix sulle migration. È il momento di aprire la PR e fermarsi.

Con il plugin `commit-commands` il comando è uno:

```text
/commit-push-pr
```

<!-- VERIFY: la prima edizione attribuiva /commit-push-pr a Superpowers; secondo FACTS-verified è del plugin commit-commands (claude-plugins-official). Allineare con il capitolo 8. -->

Fa il commit di quello che resta, il push del branch e apre la PR con una descrizione generata dai commit. Se preferisci la GitHub CLI:

```bash
gh pr create \
  --title "Phase 1: backend foundation (T001-T018)" \
  --body "Fase 1 completa: 18 task, pulizia Pint, migration con foreign key e indici."
```

Per controllare la PR dal terminale:

```bash
gh pr view --web   # apre la PR nel browser
gh pr checks       # stato dei check della CI
```

### Il test plan locale prima di ogni review

Prima di chiamare qualunque reviewer automatico, esegui in locale il test plan della PR. È il controllo di base: il codice deve girare, non solo esserci. Per la Fase 1 i comandi vengono dai criteri di `T018`, il task di review della fase:

```bash
cd backend
composer install
cp .env.example .env
php artisan key:generate
php artisan migrate:fresh --seed
php artisan migrate:rollback
php artisan migrate
vendor/bin/pest
vendor/bin/pint --test
```

Con Laravel Sail, che vediamo tra poco:

```bash
vendor/bin/sail up -d
vendor/bin/sail artisan migrate:fresh --seed
vendor/bin/sail test
```

Se qualcosa non gira in locale, una review del codice in quello stato non ha senso.

### Due reviewer indipendenti

Confermato che il codice gira, passi alla review vera. Usa due strumenti indipendenti: tool diversi hanno punti ciechi diversi.

Il primo è Codex di OpenAI collegato al repository GitHub, che commenta da solo le PR. Lascia finding inline sulle righe del diff e trova bene i problemi locali: un indice mancante, un campo in `$fillable` che non dovrebbe esserci, una variabile non usata.

Il secondo è la review di Superpowers, che lancia il subagent `superpowers:code-reviewer` (è lui che firma la review della PR #1 in `docs/REVIEW-FIXES.md`). Confronta il codice con il piano della fase e con le regole del progetto: non guarda solo il diff, ma la coerenza con `CLAUDE.md`, `REQUIREMENTS.md`, `DESIGN.md` e `TASKS.md`. Nella prima edizione qui scrivevo `/review`; oggi quel comando è un alias di una review integrata in Claude Code e non attiva più Superpowers, quindi la review la chiedo per nome:

```text
Fai la code review della PR corrente con il code-reviewer di Superpowers.
Processa anche i finding di Codex nei commenti della PR. Classifica
tutto per severità (BLOCKER / MAJOR / MINOR) e proponi i fix partendo
dai BLOCKER.
```

<!-- VERIFY: nome della skill Superpowers che lancia la review (requesting-code-review) e del subagent superpowers:code-reviewer nella versione corrente del plugin. -->

### Classificare i finding e iterare

Il reviewer non si limita a elencare problemi: li classifica. Questi sono alcuni finding reali della PR #1, presi da `docs/REVIEW-FIXES.md` e riassunti:

```text
[BLOCKER] photos.user_id senza indice
  foreignUuid('user_id')->constrained() non crea l'indice su SQLite
  e PostgreSQL. DESIGN.md §4.4 lo elenca per primo. Aggiungere
  $table->index('user_id') nella migration di photos.

[MAJOR] SANCTUM_TOKEN_EXPIRATION documentata ma non letta
  .env.example dichiara 1440 (24 ore), config/sanctum.php ha
  'expiration' => null. I token non scadono mai.

[MAJOR] final mancante su AppServiceProvider, DatabaseSeeder e factory
  Il CLAUDE.md chiede classi final di default.

[MINOR] processing_status in $fillable
  È stato interno del job, non input dell'utente.
```

La regola operativa:

- BLOCKER: rompe una funzionalità o apre un buco. Si corregge prima del merge, senza eccezioni.
- MAJOR: non blocca, ma è un problema serio (performance, deviazione dalla spec, regola del progetto violata). Si corregge nella stessa PR se possibile.
- MINOR: stile, naming, micro ottimizzazioni. Si traccia e si sistema in una PR di pulizia.

Il MINOR su `$fillable` è un buon esempio di finding che non si "corregge" per forza. Togliere i campi `processing_*` da `$fillable` avrebbe costretto a usare `forceFill()` ovunque nel job; la protezione vera sono le Form Request, che non accettano quei campi. Il fix è stato un commento nel model che spiega la scelta (commit `75f93cd`). Anche "non cambio, e scrivo perché" è una risposta valida a un finding.

Quando passi un finding a Claude, il prompt è diretto:

```text
Sulla PR c'è questo finding sui personal access token di Sanctum:
[testo del finding]. Verifica, correggi e aggiungi un test che copra il
caso. Non andare avanti finché il test non è verde.
```

Claude legge il finding, controlla il codice, applica il fix, aggiunge il test e committa. Se la review era già stata eseguita, lo dice e non la rilancia da zero.

Risolti BLOCKER e MAJOR, puoi fare il merge. Poi un ultimo passaggio che sembra banale:

```text
La PR è stata mergeata.
```

Claude segna la Fase 1 come chiusa e prepara la Fase 2. Senza questo messaggio continua a considerare la fase in review.

![Pattern Eloquent e regole di validazione raccolti durante la review](figures/cap-19/fig-02.png)

<!-- TODO screenshot: fig-02 è a bassa risoluzione e il testo non si legge; rifare lo screenshot del documento di regole aperto nell'IDE. -->

### Laravel Sail: un ambiente di sviluppo vicino alla produzione

Il BLOCKER sull'indice ha una causa che va oltre la singola migration: i test girano su SQLite, la produzione no. SQLite non crea da solo gli indici sulle foreign key, è meno rigido di MariaDB e MySQL sui vincoli e si comporta diversamente su alcune funzioni di data e ora. Il log della review lo scrive come prima lezione: problemi del genere non fanno fallire i test su SQLite e si vedono solo su un database vero con volumi veri.

Per questo, subito dopo la PR #1, il Photogallery ha adottato Laravel Sail (PR #2): Docker con MariaDB, Redis, Mailpit per le email e MinIO, che emula S3 in locale.

```bash
composer require laravel/sail --dev
php artisan sail:install
```

Scegli MariaDB, Redis, Mailpit e MinIO. Sail genera `compose.yaml` con i servizi e i volumi. Per avviare:

```bash
vendor/bin/sail up -d
vendor/bin/sail artisan migrate:fresh --seed
```

Il `.env` punta a `DB_CONNECTION=mariadb`, con host e porta definiti dal compose. Da qui lo sviluppo locale è molto vicino alla produzione, e i finding del tipo "in locale funziona, in staging si rompe" diventano rari. Nello stesso giro è arrivato anche un MINOR: Filament 5 richiede PHP 8.4, quindi il `composer.json` è passato a `"php": "^8.4"` e CI e staging devono seguirlo.

### Quando la review trova qualcosa che la spec non dice

Torniamo al commit di `T003`. `DESIGN.md` §4.6 chiedeva una sola modifica alla tabella di Sanctum: `tokenable_id` come `CHAR(36)`, per puntare agli utenti con UUID. Claude ha fatto anche altro, "for consistency": ha trasformato in UUID la chiave primaria della tabella. Sanctum però inserisce un token senza fornire un id, perché si aspetta un auto-increment, e la prima chiamata a `$user->createToken()` sarebbe fallita con una violazione NOT NULL. L'ho trovato io prima che partisse la review, ed è finito nel log come F0, il primo BLOCKER. Il fix (commit `fb39632`) riporta la chiave a `$table->id()` e aggiunge `SanctumTokenTest`, che crea un token per un utente con UUID e controlla le ability.

La spec qui era giusta, ma la regola 8 del `CLAUDE.md` ("ogni chiave primaria è UUID v7") spingeva nella direzione sbagliata per una tabella del framework. Succede: le spec partono buone, ma non perfette, e la review sistematica raccoglie il resto prima del deploy. Quando un finding rivela un buco nella spec, la correzione non si ferma al codice: aggiorna `REQUIREMENTS.md` o `DESIGN.md`, aggiungi o modifica il task in `TASKS.md`, cita la sezione nel messaggio di commit. Quando rivela un agent che è andato oltre la spec, come qui, il test di regressione è la protezione che resta.

## 19.3 Wave review: più agent su aspetti diversi

### Cos'è una wave

Una wave è un gruppo di fasi o task che condividono un obiettivo architetturale e che, finiti, formano un'unità del sistema. Nel Photogallery le wave sono scritte nel `CLAUDE.md`, sezione "Parallelization rules". La Wave 0 è sequenziale e finisce con la Fase 1 che abbiamo appena chiuso. La Wave 1 ha tre track parallele: la Track A è la Fase 2, l'API layer, seguita dalla Fase 6, la pipeline delle immagini; la Track B è la Fase 3, il pannello Filament; la Track C sono le Fasi 4 e 5, il frontend React.

La Fase 2 da sola vale 27 task, da `T019` a `T045`: middleware, gestione delle eccezioni, policy, form request, API resource, query object, controller, rotte con rate limit e test. A questa dimensione la review del singolo task non basta più.

In questo capitolo chiudiamo la Wave 0 e, della Wave 1, solo la Fase 2 della Track A. Le Fasi da 3 a 6 restano aperte: le esegui nel capitolo 20, in parallelo. I branch companion contano le wave in un altro modo: `book/cap-13-wave-1-backend` è la Wave 0 di `TASKS.md` (stato a fine Fase 1), `book/cap-13-wave-2-api` è la Track A della Wave 1 fino alla Fase 2. Nel testo seguo i nomi di `TASKS.md`.

### Task review e wave review

La review del task risponde alla domanda "questo pezzo fa quello che doveva?". La wave review risponde a un'altra: "i pezzi di questa wave si parlano in modo coerente?". È a questo livello che escono i problemi più subdoli. Un controller usa il query object e un altro costruisce la query a mano, e chi manutiene si trova due stili. Una mutazione controlla la policy e la sua vicina no, e il buco di autorizzazione resta invisibile finché qualcuno non lo usa. Un endpoint risponde agli errori con un formato leggermente diverso, e il frontend deve gestire un caso speciale. Nessuno di questi si vede guardando un task alla volta.

### Quattro agent in parallelo

La wave review lancia più agent specializzati in parallelo, ognuno su un aspetto del codice, e poi aggrega i report in un documento solo. Il prompt per la Fase 2:

```text
Wave review della Fase 2, API layer (task T019-T045).
Lancia quattro subagent in parallelo, in sola lettura (nessuna modifica
ai file), modello sonnet:

1. security-auditor
   Cerca: auth bypass, input validation mancante, esposizione di dati
   non autorizzata, segreti nel codice, CORS troppo permissivo.

2. performance-reviewer
   Cerca: query N+1, eager loading mancante, indici DB assenti sulle
   colonne filtrate, operazioni sincrone che dovrebbero essere job.

3. api-consistency
   Cerca: error envelope non uniforme, status code sbagliati,
   controller che non usano il query object, naming non uniforme.

4. test-coverage
   Cerca: percorsi critici senza test, edge case mancanti, test che
   bypassano la policy, N+1 nei test, factory incomplete.

Per ogni finding: file, riga, severità (CRITICAL / HIGH / MAJOR /
MEDIUM / LOW), fix proposto. Aggrega i quattro report in un documento
unico, in ordine di priorità.
```

I quattro subagent partono in background, come tutti i subagent nelle sessioni interattive, e li segui con `/tasks`. Ognuno legge il codice e lo cerca con i tool di ricerca disponibili (sulle build native di macOS e Linux la ricerca passa da `Bash`), e risponde a un insieme ristretto di domande. In qualche minuto hai il quadro completo. Sono in sola lettura, quindi qui il problema del working tree condiviso non si pone: nessuno scrive file. Se vuoi riusare questi ruoli su altri progetti, scrivili come subagent in `.claude/agents/security-auditor.md` e così via (capitolo 10), oppure chiedi a Claude di crearli.

Claude Code ha anche un comando integrato, `/code-review`, che cerca bug di correttezza nel diff in background: lo usiamo nel capitolo 22 come passata prima del deploy.

### Perché specializzare

Un agent generalista divide l'attenzione: davanti a un controller controlla sicurezza, performance, coerenza e test, ma nessuna delle quattro in profondità. Un agent specializzato applica la sua checklist a tutto il codice. Il security auditor cerca ogni punto d'ingresso di dati non fidati, ogni campo che esce dalla risposta, ogni endpoint raggiungibile senza autenticazione, e non si distrae con il naming: quello è compito di un altro. Insieme coprono tutta la superficie con meno punti ciechi sistematici di un passaggio unico.

C'è anche un secondo motivo, scritto come ultima lezione in `docs/REVIEW-FIXES.md`: la sessione che ha scritto il codice ha i suoi bias, e nella PR #4 non aveva visto nessuno dei problemi trovati poi dai reviewer. Un agent nuovo, senza il contesto dei commit, guarda il codice per quello che è.

### I finding della Fase 2

Sulla PR #4, quella della Fase 2, il log registra due passate parallele, il code reviewer di Superpowers e un security auditor (le vediamo in §19.4). Ordinati per aspetto, quei finding cadono nei quattro ruoli del prompt.

Sicurezza. `PhotoData`, la API resource delle foto, restituiva `exif` e `processing_error` a chiunque, anche agli anonimi. L'EXIF può contenere le coordinate GPS e il numero di serie della fotocamera, l'errore di processing frammenti di path interni. Il fix applica a questi campi lo stesso controllo "proprietario o admin" che già proteggeva `urls.original`, con quattro test nuovi in `PhotoDataTest`. Il secondo finding riguardava CORS: lo scaffold di Laravel 13 non pubblica `config/cors.php`, quindi era attiva la policy di default con origini `*`, anche se `.env.example` dichiarava `FRONTEND_URL`. Il fix pubblica `config/cors.php` con l'origine letta da `FRONTEND_URL` e tre test in `CorsTest`. Su `main` la gestione dell'EXIF è cambiata ancora: la vediamo nel capitolo 22.

Performance. Nel `PATCH` delle foto, la conversione da slug a nome dei tag faceva una query per ogni slug, dentro una transazione, e con un fallback che avrebbe usato lo slug come nome se il tag non esisteva. Il fix è una query sola:

```php
$existingNames = $tags
    ? Tag::query()->whereIn('slug', $tags)->pluck('name')->all()
    : [];
```

L'altro N+1 stava nei test: `PhotoControllerIndexTest` accettava fino a sei query per l'indice delle foto, mentre con la paginazione a cursore e i tre eager load di `PhotoData::WITH` ne bastano quattro. Una soglia larga lascia passare un eager load in più senza che nessuno se ne accorga, quindi è stata stretta a quattro. Gli N+1 nei test contano più di quanto sembri: se il test tollera query in più, le tollera anche la produzione.

Coerenza dell'API. `AlbumController@index` costruiva la query a mano invece di passare da un query object come fa `PhotoQuery` per le foto. Il finding è rimasto aperto di proposito: estrarre un `AlbumQuery` con un solo utilizzatore è prematuro, e il log lo rimanda a quando il pannello Filament avrà bisogno della stessa logica. Il secondo finding pesava di più: `AlbumController@store` controllava l'ability del token ma non la policy, mentre tutte le altre mutazioni dei due controller controllano entrambe. Preso da solo, ogni controller sembrava a posto; confrontandoli, la mancanza è saltata fuori. È esattamente l'incoerenza tra moduli che la wave review esiste per trovare.

Test. `AuthorizationTest` verificava il bypass degli admin controllando che lo status non fosse 403 né 401. Un 500 per un'eccezione non gestita sarebbe passato come successo. L'asserzione ora richiede uno status tra 200, 201 e 204. Un test di autorizzazione troppo permissivo può nascondere i bug della policy che dovrebbe proteggere.

Il commit di fix `3ece74b` porta la suite da 148 a 158 test.

### Aggregare e dare priorità

Raccolti i report, costruisci una lista di priorità:

- CRITICAL: vulnerabilità o bug funzionale confermato. Si corregge prima del merge.
- HIGH: falla di autorizzazione, dati esposti a chi non dovrebbe vederli. Stessa PR, prima del merge.
- MAJOR: pattern violati, N+1 in produzione, incoerenze tra moduli. Stessa PR.
- MEDIUM: N+1 nei test, `filename` visibile agli anonimi. PR di follow-up.
- LOW: cast mancante, un `load()` inutile prima di un `fresh()`, `final` mancante su qualche classe. Una PR di pulizia.

Risolvi CRITICAL, HIGH e MAJOR prima del merge. Il resto finisce in backlog come issue GitHub numerata, così non sparisce. Nel log del Photogallery i finding rimandati, come `filename` esposto o il query object degli album, hanno una riga "Why deferred" con il motivo: è la stessa cosa in forma di documento.

![Le lezioni imparate dalle review della PR #1 e della PR #4, in fondo a docs/REVIEW-FIXES.md](figures/cap-19/fig-01.png)

### Naming coerente: il momento giusto è la wave review

Quando i task si sviluppano in sessioni separate o con subagent in parallelo, i nomi derivano: `PhotoData` in un file, `PhotoDto` in un altro, `PhotoResponse` in un terzo, per la stessa cosa. Il Photogallery ha la convenzione scritta in `DESIGN.md` §6.6 (`PhotoData`, `AlbumData`, `TagData`, `UserData`), ma la verifica va fatta lo stesso, prima che i nomi si propaghino:

```text
Analizza il naming di tutte le API resource, i query object, le form
request e i data object della Fase 2. Trova le incoerenze (lo stesso
concetto con nomi diversi in file diversi) e proponi un piano di
allineamento che mantenga la retrocompatibilità.
```

Una pulizia di naming in wave review richiede pochi minuti. Fatta mesi dopo, quando il nome sbagliato è finito in venti file, è una giornata di refactoring.

### Una PR per i fix della wave

Dopo i finding, raccogli i fix in commit dedicati e tienili separati dal lavoro della fase. Sulla PR #4 sono finiti tutti in `3ece74b`, con un messaggio che elenca ogni finding con il suo codice (S1, S2, C1...) e i file toccati. Su una wave più grande apri una PR solo per i fix: il diff resta leggibile perché tutte le modifiche condividono lo stesso contesto, e chi revisiona, persona o agent, le valuta in blocco.

Poi rilancia la suite e controlla le rotte:

```bash
php artisan migrate:fresh --seed
vendor/bin/pest
php artisan route:list --path=api   # tutte le rotte registrate sotto /api/v1
```

Infine prova gli endpoint con un client HTTP, per esempio un file `.http` nell'IDE. Le risposte attese per gli album:

```text
GET    /api/v1/albums        200, { "data": [...], "links": ..., "meta": { "next_cursor": ... } }
POST   /api/v1/albums        201 con la risorsa creata
PATCH  /api/v1/albums/{id}   200, oppure 403 se non sei il proprietario
DELETE /api/v1/albums/{id}   204, oppure 403
```

<!-- VERIFY: forma esatta di links/meta nella risposta paginata a cursore di AlbumData::collection. -->

## 19.4 Review mirata: controller, policy, eccezioni

### Perché una review verticale

La wave review è orizzontale: guarda tutta la wave da angolazioni diverse. Serve anche una review verticale, che scende su un aspetto dell'architettura e verifica che ogni modulo segua lo stesso pattern. In un'API REST gli aspetti che lo meritano sono tre: la struttura dei controller, l'autorizzazione con le policy, la gestione uniforme delle eccezioni. Se uno dei tre è incoerente, il sistema diventa difficile da capire e da testare.

Il riferimento qui è il Photogallery con Laravel 13, ma i principi si spostano bene: in NestJS ci sono i Guard al posto delle policy e le Pipe al posto delle Form Request, in Django Permissions e Serializers.

Nella Fase 2 l'applicazione smette di essere scaffolding e diventa un sistema: rotte versionate sotto `/api/v1`, policy per foto e album, un middleware che forza le risposte JSON, la gestione globale delle eccezioni, resource, form request, query object e i rate limit. I singoli task li ha già guardati la wave review. Qui controlli che l'insieme sia coerente con i pattern di `DESIGN.md`.

### Middleware: forzare il JSON

Prima dei controller c'è un livello che spesso si salta: il middleware che fa sì che ogni richiesta all'API venga trattata come JSON, qualunque header mandi il client. Senza, un client che dimentica `Accept: application/json` riceve una pagina di errore HTML, e in sviluppo anche lo stack trace. In Laravel 13 si registra in `bootstrap/app.php` (`T019`):

```php
->withMiddleware(function (Middleware $middleware): void {
    $middleware->api(prepend: [
        ForceJsonResponse::class,
    ]);
})
```

Il middleware è corto:

```php
final class ForceJsonResponse
{
    public function handle(Request $request, Closure $next): Response
    {
        $request->headers->set('Accept', 'application/json');

        return $next($request);
    }
}
```

In review verifica due cose. Il middleware sta nel gruppo `api`, non in `web`: lì romperebbe le pagine Blade e il pannello Filament. E gira prima dell'autenticazione, ed è per questo che si usa `prepend`: altrimenti il 401 di `auth:sanctum` può uscire senza il content type che il client si aspetta.

### Gestione delle eccezioni

`DESIGN.md` §11.1 definisce un envelope unico per ogni risposta non 2xx sotto `/api/*`. In Laravel 13 si configura in `bootstrap/app.php`, dentro `withExceptions` (`T020`). Un estratto del codice del Photogallery:

```php
->withExceptions(function (Exceptions $exceptions): void {
    $exceptions->shouldRenderJsonWhen(
        fn (Request $request) => $request->is('api/*')
    );

    $exceptions->render(function (AccessDeniedHttpException $e, Request $request) {
        if ($request->is('api/*')) {
            return response()->json(['message' => 'This action is unauthorized.'], 403);
        }
    });

    $exceptions->render(function (NotFoundHttpException $e, Request $request) {
        if ($request->is('api/*')) {
            return response()->json(['message' => 'Resource not found.'], 404);
        }
    });

    $exceptions->render(function (ThrottleRequestsException $e, Request $request) {
        if ($request->is('api/*')) {
            $retryAfter = $e->getHeaders()['Retry-After'] ?? 60;

            return response()
                ->json(['message' => 'Too many requests.'], 429)
                ->header('Retry-After', (string) $retryAfter);
        }
    });
})
```

Il file completo gestisce anche 401, 413 e 415. Il 422 resta quello di Laravel, che ha già la forma `{ message, errors }`.

I finding tipici su questa parte sono tre. Il primo è il più sottile, ed è finito nelle lezioni del log: Laravel 13 converte `AuthorizationException` in `AccessDeniedHttpException` e `ModelNotFoundException` in `NotFoundHttpException` prima che i callback `render` girino. Se tipizzi il callback con l'eccezione originale, non scatta mai, e il client riceve il messaggio di default invece del tuo envelope. Nel codice sopra i tipi sono quelli già convertiti, e un test con `assertExactJson` lo verifica. Il secondo: il 429 senza un payload coerente e senza `Retry-After` confonde il client, quindi va gestito esplicitamente. Il terzo: le eccezioni 5xx non vanno mai inghiottite. Se un callback restituisce `null`, la gestione torna a Laravel, che logga; se catturi un'eccezione con un `try/catch` e rispondi, logga prima, o rilanciala.

### Controller: il pattern che non cambia

Ogni controller di questa API segue lo stesso schema: return type esplicito (`JsonResponse`, `AnonymousResourceCollection`, `Response` per il 204), una Form Request per ogni mutazione, l'output sempre attraverso una API resource, e un doppio controllo di autorizzazione. La regola 10 del `CLAUDE.md` chiede proprio questo: ogni mutazione verifica l'ability del token Sanctum e la policy. Un estratto di `AlbumController` dopo il fix della PR #4:

```php
public function store(StoreAlbumRequest $request): JsonResponse
{
    $this->ensureAbility($request, TokenAbility::AlbumsWrite);
    if ($request->user()?->cannot('create', Album::class)) {
        throw new AuthorizationException;
    }

    $album = Album::create([
        ...$request->validated(),
        'user_id' => $request->user()->id,
    ]);

    $album->load(AlbumData::WITH)->loadCount('photos');

    return AlbumData::make($album)->response()->setStatusCode(201);
}

public function destroy(Request $request, Album $album): Response
{
    $this->ensureCan($request, 'delete', $album);

    $album->delete();

    return response()->noContent();
}
```

`ensureCan()` è un metodo privato del controller che fa i due controlli insieme. La policy `create` di `AlbumPolicy` oggi restituisce sempre `true`: esiste perché tutte le mutazioni siano simmetriche, e perché un domani si possa stringere la regola senza toccare il controller.

Un dettaglio che la review deve conoscere: in Laravel 13 il `Controller` base dello scaffold è vuoto, senza il trait `AuthorizesRequests`, quindi `$this->authorize()` e `authorizeResource()` non ci sono finché non aggiungi il trait. Il Photogallery usa `cannot()` sull'utente; se il tuo progetto usa `authorize()`, controlla che il trait sia davvero lì.

La checklist per ogni controller della wave:

- l'output passa sempre da una resource (`AlbumData::make()`, `AlbumData::collection()`), mai da `response()->json(['data' => $album->toArray()])`;
- gli eager load vengono dalla costante della resource (`AlbumData::WITH`), come chiede il `CLAUDE.md`;
- le mutazioni ricevono `StoreAlbumRequest` o `UpdateAlbumRequest` e usano `$request->validated()`, mai `$request->all()`;
- le scritture multiple stanno in `DB::transaction()` (regola 11);
- nessun metodo restituisce array nudi o stringhe.

### Policy: proprietario stretto e bypass per l'admin

Le policy decidono chi può fare cosa. Nel Photogallery sono volutamente piatte, solo la regola di proprietà:

```php
final class AlbumPolicy
{
    public function create(User $user): bool
    {
        return true;
    }

    public function view(User $user, Album $album): bool
    {
        return $album->user_id === $user->id;
    }

    public function update(User $user, Album $album): bool
    {
        return $album->user_id === $user->id;
    }

    public function delete(User $user, Album $album): bool
    {
        return $album->user_id === $user->id;
    }
}
```

Il bypass per gli admin vive in un posto solo, `AppServiceProvider::boot()`, e copre tutte le policy:

```php
Gate::before(fn (User $user) => $user->isAdmin() ? true : null);
```

Il finding classico è proprio qui: un `before` (nel Gate o in una policy) che restituisce `false` per chi non è admin. `false` nega tutto subito, comprese le azioni che la policy avrebbe permesso. Il contratto corretto è `true` per gli admin e `null` per tutti gli altri, che lascia proseguire il controllo normale.

Il secondo finding tipico è la policy non registrata. Laravel la trova da solo se si chiama `AlbumPolicy` e sta in `app/Policies`; con un nome o una cartella diversi serve l'attributo `#[UsePolicy]` sul model o `Gate::policy()` in un service provider. Una policy che non viene mai chiamata non blocca nessuno, e il codice sembra funzionare.

Il terzo riguarda le risorse figlie. Se un'applicazione ha album privati, la visibilità di una foto deve risalire all'album: chi conosce l'id di una foto in un album privato non deve vederla solo perché il controllo guarda `photo.user_id`. Il Photogallery oggi non ha album privati, ma è la prima domanda da fare quando arrivano.

### Un solo formato per tutti gli errori

Se la gestione delle eccezioni è stata fatta all'inizio della wave, come qui con `T020`, ogni errore esce nello stesso formato. La review deve verificare che tutti i controller ci passino. I formati attesi, da `DESIGN.md` §11.1:

```json
{ "message": "The name field is required.", "errors": { "name": ["The name field is required."] } }
```

```json
{ "message": "This action is unauthorized." }
```

```json
{ "message": "Resource not found." }
```

Il primo è il 422, il secondo il 403, il terzo il 404. Se un controller lancia per conto suo `abort(403, 'Forbidden')` con un messaggio diverso, il frontend deve gestire un caso speciale: ogni eccezione al formato è un bug di integrazione che aspetta il suo momento.

La verifica più rapida è una richiesta non autorizzata su ogni endpoint, confrontando le risposte. Nel Photogallery lo fa già `AuthorizationTest` (`T040`), che passa tutte le mutazioni e verifica 401 senza token e 403 con il token di un altro utente. Se una risposta arriva in HTML o con un formato diverso, hai trovato un buco.

### Due agent sulla stessa PR

Capito il codice, il passo operativo è lanciare due agent in parallelo sulla PR. È quello che è successo sulla PR #4:

```text
Fai una code review della PR #4 che includa best practice e controlli
di sicurezza. Lancia in parallelo il code-reviewer di Superpowers e un
security auditor.
```

Il code reviewer guarda qualità, regole del progetto e aderenza alla spec. Il security auditor guarda vulnerabilità, bypass dell'autorizzazione, validazione dell'input, CORS, gestione dei segreti. Ne escono due report da consolidare, come con due reviewer umani su una PR delicata: le checklist sono diverse e così i punti ciechi. Il security auditor della PR #4 ha trovato anche un problema che nessun test locale poteva mostrare: senza `trustProxies`, dietro un load balancer `$request->ip()` restituisce l'indirizzo del proxy, e il rate limit di 10 tentativi al minuto per IP sul login diventa un secchio unico per tutti. Il fix legge `TRUSTED_PROXIES` dal `.env`.

Una nota sul comportamento degli agent: Claude Code può segnalare che l'ultima review eseguita riguardava una PR precedente e che quella attuale non è ancora stata analizzata. È un'informazione utile, perché non vuoi una conferma di review mai fatta. Appena confermi la PR giusta, la review parte e i due agent lavorano in parallelo sullo stesso diff.

## 19.5 Code review di un pannello admin (Filament)

### Perché il pannello admin merita una review a parte

Il pannello admin è una delle parti più trascurate in review. Lo si tratta come "la parte interna", usata solo dagli admin e quindi meno critica. È il ragionamento sbagliato: il pannello vede tutti i dati, esegue operazioni bulk su migliaia di record e spesso ha meno test delle API pubbliche. L'idea "tanto lo usano solo gli admin" porta a saltare i controlli che sulle API pubbliche sono routine, e la review dedicata serve a rimetterli.

Nel Photogallery il pannello è costruito con Filament 5, un framework per Laravel che dà CRUD, dashboard, widget e form partendo da convenzioni e componenti pronti. È la Fase 3, da `T046` a `T054`: la Track B della Wave 1, che a fine capitolo è ancora da eseguire e che il capitolo 20 fa girare in parallelo all'API e al frontend. Questa sezione è la checklist da applicare quando la Track B arriva in review; il codice degli esempi viene dal repo su `main`. Backend Laravel, API REST, frontend React, admin Filament: la wave review funziona su tutti gli strati, cambia solo la checklist.

### Verificare che tutto funzioni nel browser

Prima del codice, apri il browser. Sempre. Claude genera resource, widget e pagine, ma questo non garantisce che l'integrazione funzioni: le chiamate partono verso l'host sbagliato, le origini CORS non combaciano, l'URL del backend è scritto nel codice invece che in una variabile.

Nel Photogallery, quando pannello e frontend sono arrivati, la prova manuale ha trovato subito due problemi:

1. Il frontend React chiamava l'host del dev server di Vite (porta 5174) invece del backend sulla porta 80. Nessun errore nel codice, solo l'URL sbagliato nel client axios.
2. Corretto l'URL, compariva un errore CORS: `FRONTEND_URL` nel `.env` del backend puntava a `localhost:5173`, la porta di default di Vite con cui era stato inizializzato il progetto, mentre il dev server girava sulla 5174 perché la 5173 era occupata.

La regola che ne esce: niente URL nel codice e niente porte date per scontate. Il client legge la base dell'API da una variabile d'ambiente:

```bash
# frontend/.env.example
VITE_API_BASE_URL=http://localhost/api/v1
```

```ts
// frontend/src/api/client.ts
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api/v1',
});
```

`.env.example` va nel repository e documenta la variabile, il `.env` vero resta in locale. In staging basta impostare il valore giusto, senza toccare il codice. Lo stesso vale per `FRONTEND_URL` nel backend, che alimenta `config/cors.php`.

### La checklist per un pannello Filament

Confermato che il pannello funziona, la review del codice parte da una checklist specifica.

Operazioni bulk. Ogni azione che lavora su una selezione multipla deve chiedere conferma. In Filament 5 le azioni stanno in `Filament\Actions` e si agganciano alla tabella con `toolbarActions()`. Un estratto di `PhotosTable`:

```php
->toolbarActions([
    BulkActionGroup::make([
        DeleteBulkAction::make(),
        BulkAction::make('reprocess')
            ->label('Reprocess')
            ->icon('heroicon-o-arrow-path')
            ->color('warning')
            ->requiresConfirmation()
            ->action(function (Collection $records): void {
                $records->each(function (Photo $photo): void {
                    $photo->update([
                        'processing_status' => ProcessingStatus::Pending,
                        'processing_attempts' => 0,
                        'processing_error' => null,
                    ]);
                    ProcessPhoto::dispatch($photo);
                });
                Notification::make()->title('Reprocessing dispatched')->success()->send();
            }),
    ]),
])
```

`DeleteBulkAction` chiede conferma da sola; un `BulkAction` scritto a mano no, finché non aggiungi `requiresConfirmation()`. Senza, un clic sbagliato rimette in coda centinaia di job o cancella centinaia di foto. Aggiunta consigliata: un audit log delle operazioni bulk, con chi, quando e su quali record. Filament non lo fa da solo, ma si integra con pacchetti come `spatie/laravel-activitylog`.

Filtri e indici. Ogni colonna usata come filtro nella tabella dovrebbe avere un indice. La review confronta i `filters()` della resource con gli indici delle migration:

```php
// PhotosTable.php
SelectFilter::make('processing_status')
    ->options(ProcessingStatus::class),

// migration di photos
$table->index(['processing_status', 'created_at'], 'photos_status_created_idx');
```

Filament non avvisa se l'indice manca. Lo scopri sotto carico, con una full table scan.

Validazione su due livelli. In Filament la validazione si dichiara sul campo. `AlbumForm` rende il nome unico per utente:

```php
TextInput::make('name')
    ->required()
    ->maxLength(255)
    ->unique(
        ignoreRecord: true,
        modifyRuleUsing: fn (Unique $rule) => $rule->where('user_id', auth()->id()),
    ),
```

Questa regola vale solo nel pannello. Chi chiama l'API passa da `StoreAlbumRequest`, che applica la stessa unicità con `Rule::unique` filtrata per `user_id` (`T025`). Servono entrambe: Filament per l'esperienza d'uso, la Form Request per l'integrità dei dati. La review controlla che le due regole dicano la stessa cosa.

Autorizzazione. Il primo cancello è l'accesso al pannello: `User` implementa `FilamentUser` e `canAccessPanel()` restituisce `isAdmin()`, così un utente normale che apre `/admin` torna al login (`AC-F11-1` in `REQUIREMENTS.md`). Il secondo sono le policy. Filament usa le policy registrate per il model di ogni resource (`viewAny`, `create`, `update`, `delete`) per mostrare o nascondere pagine e azioni. Il finding più comune è una resource senza policy perché "il pannello è già protetto dal login". Se domani un bug nel middleware o in `canAccessPanel()` fa entrare un utente non admin, senza policy può fare tutto.

<!-- VERIFY: comportamento di Filament 5 quando la policy esiste ma manca un metodo (es. viewAny), con Gate::before che restituisce true per gli admin. -->

Export e import. Se il pannello offre export CSV o import in batch, aggiungi due controlli. Un rate limit sull'export, perché senza un utente può esportare l'intero database ogni pochi secondi e saturare database e disco. E la validazione di ogni riga importata con le stesse regole della Form Request dell'API, prima di toccare il database.

### I componenti del frontend e la pipeline che manca

Nella stessa Wave 1, la Track C (Fasi 4 e 5, anche loro nel capitolo 20) porta i primi componenti React: la griglia delle foto (`MasonryGrid`, `PhotoCard`), il lightbox, il modale di upload, la sidebar e le scorciatoie da tastiera, da `T063` a `T071`. I componenti sono collegati ai dati dell'API, ma le foto mostrano lo stato `processing` invece dell'immagine.

Non è un bug. La pipeline che genera thumbnail, versione medium e versione large è la Fase 6, da `T072` a `T080`, che nella Track A viene dopo l'API. Fino ad allora gli originali restano nel disco privato e le varianti non esistono. La tentazione è chiedere a Claude di "sistemare lo stato processing", e sarebbe un errore: inventerebbe una scorciatoia fuori dal piano. Il finding corretto è "atteso, risolto dalla Fase 6", con un controllo su `TASKS.md` che la dipendenza sia scritta davvero. `T077`, il job `ProcessPhoto`, e `T079`, che collega l'upload ai job veri, sono lì. Se non ci fossero, il fix della review sarebbe aggiungere il task, non scrivere codice.

Anche questo fa parte della review: distinguere quello che deve funzionare adesso da quello che dipende da una wave successiva, e verificare che la dipendenza sia nel piano.

### Regole valide per qualsiasi pannello admin

Quello che è emerso dal pannello Filament vale per qualunque admin, che sia React Admin, Refine, AdminJS o uno scritto a mano:

1. L'autenticazione non basta: ogni operazione controlla i permessi, anche se l'utente ha già fatto il login.
2. Le operazioni bulk chiedono sempre conferma, possibilmente con il numero di record coinvolti. Non importa quanto è esperto l'admin.
3. Ogni filtro dell'interfaccia ha il suo indice nel database, altrimenti un filtro che "funziona" in sviluppo diventa una full table scan in produzione.
4. La prova nel browser è obbligatoria: apri il pannello, esegui le operazioni principali, guarda la scheda Network. Claude genera il codice, la verifica visiva è compito tuo.
5. Host, porte e path dell'API arrivano da variabili d'ambiente, e il `.env.example` nel repository è il contratto tra sviluppo e deploy.
6. Installa le linee guida del framework prima della prima wave. Per Laravel c'è Laravel Boost, che aggiunge al `CLAUDE.md` le convenzioni di Laravel e un server MCP con tool come `search-docs` e `database-schema` (la sezione "Laravel Boost tools" del `CLAUDE.md` del Photogallery li elenca). Installato dopo, Claude può fare un audit del codice già scritto e allinearlo, ma partire con le linee guida evita la pulizia. Per altri stack cerca l'equivalente ufficiale o della community e collegalo al `CLAUDE.md` prima dei task.
7. Review del codice e verifica manuale trovano cose diverse. Gli agent, Codex e il code reviewer trovano bug nel codice; il browser aperto trova bug di integrazione che il codice da solo non mostra. Prima del merge servono entrambe.

<!-- VERIFY: laravel/boost non compare in backend/composer.json su main, anche se il CLAUDE.md del progetto ha la sezione "Laravel Boost tools"; controllare come era installato. -->

## Riepilogo

- Esegui i task di `TASKS.md` uno per commit, con l'ID del task e le sezioni di `DESIGN.md` nel corpo del messaggio; spunta il task solo con test verdi, linter pulito e diff letto.
- I subagent in parallelo condividono il working tree: vanno bene su cartelle separate, per task paralleli sullo stesso codice usa i worktree del capitolo 20.
- Apri la PR di fase dopo un test plan locale verde, fai lavorare due reviewer indipendenti e classifica i finding in BLOCKER, MAJOR e MINOR; quando un finding rivela un buco nella spec, aggiorna la spec oltre al codice.
- La wave review cerca le incoerenze tra moduli: quattro subagent in sola lettura (sicurezza, performance, coerenza dell'API, test) e un report unico ordinato per severità.
- Nei controller verifica return type, Form Request, resource e doppio controllo ability più policy su ogni mutazione; nelle policy, `null` e non `false` per chi non è admin.
- Il pannello admin è critico quanto l'API pubblica: conferma sulle azioni bulk, indici sui filtri, validazione su due livelli, policy per ogni resource, URL dell'API in una variabile d'ambiente.

## Esercizio

Rifai la wave review della Fase 2 e confronta i tuoi finding con quelli reali.

1. Clona il branch `book/cap-13-wave-2-api` e crea un branch locale dal commit `93f1070` ("chore: Phase 2 review"), l'ultimo prima dei fix: `git switch -c wave-review 93f1070`.
2. Esegui il test plan locale con Sail (`vendor/bin/sail up -d`, `vendor/bin/sail artisan migrate:fresh --seed`, `vendor/bin/sail test`) e annota quanti test passano.
3. Lancia la wave review con il prompt a quattro agent di §19.3, adattando nome della wave e intervallo di task se lavori su un tuo progetto.
4. Confronta il report aggregato con `docs/REVIEW-FIXES.md` sulla punta del branch `book/cap-13-wave-2-api`, sezione "PR #4".
5. Per ogni finding CRITICAL o HIGH chiedi a Claude il fix con un test che copra il caso, e rilancia la suite.

L'esercizio è finito quando hai un documento di finding con severità e stato per ogni voce, la suite è verde, non restano finding CRITICAL o HIGH aperti, e hai segnato quali finding di `REVIEW-FIXES.md` (da S1 a S5, da C1 a C8) i tuoi agent hanno trovato e quali no.
