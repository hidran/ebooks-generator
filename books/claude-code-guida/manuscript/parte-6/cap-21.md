# Capitolo 21. Feature in corsa

::: {.chapter-goals}
[Cosa imparerai]{.callout-title}

Come far entrare una feature in un progetto SDD già avviato, prima nei documenti e poi nel codice, con tre casi del Photogallery: la pipeline batch delle foto verso S3, la registrazione che il piano aveva perso per strada e i preferiti rifatti da colonna booleana a tabella pivot. Poi come gestire una PR che tocca backend e frontend insieme.

[Prerequisiti]{.callout-title}

I capitoli 17-20 (specifiche, SDD, esecuzione a wave, worktree) e il repo companion sul branch `book/cap-14-phases-complete`.

:::

Alla fine del capitolo 20 la Wave 1 di `docs/TASKS.md` è mergiata in `main`: admin Filament, setup e componenti del frontend React, pipeline delle immagini (Fasi 3-6). Il piano procede. Poi un martedì alle 17 arriva il messaggio: "Ah, ci serve anche il caricamento di tante foto insieme, c'è chi arriva con 500 foto delle vacanze. E la registrazione? Non l'avevo scritta, ma era ovvia. Già che ci sei, i clienti chiedono sempre di salvare le foto preferite."

Le richieste in corsa arrivano anche con le specifiche migliori: lo stakeholder vede l'applicazione crescere e si ricorda di cose che dava per scontate, o il mercato cambia le priorità. Il caso più insidioso è un altro: la feature era nei requisiti, ma si è persa quando i requisiti sono diventati task, e nessuno se n'è accorto fino al primo test manuale. Evitarle non si può. Puoi controllare come entrano nel progetto, senza rompere quello che funziona e senza perdere il filo del piano.

Nel Photogallery i tre casi hanno un indirizzo preciso. Il batch parte dalla pipeline che la Track A ha costruito nel capitolo 20 e la porta verso S3 e SQS, che in `TASKS.md` è la Fase 8, nella Wave 2. La registrazione mancante è la distanza tra la user story US-30 e il task T070 della Fase 5, chiusa più tardi da T121. I preferiti sono la Fase 6.5, una fase inserita a metà percorso con il numero di wave 1.5. Il branch `book/cap-14-phases-complete` (290 file) contiene lo stato del progetto con tutte le fasi dalla 3 alla 14.

## 21.1 Batch processing delle foto su S3

### Il requisito

La regola che regge la pipeline è già in `main`: l'upload risponde subito e l'elaborazione pesante la fa un worker dalla coda. La richiesta delle 500 foto mette alla prova i limiti scelti, e il passaggio a S3 mette alla prova quello che in locale non si vede: retry, transazioni, permessi sui file.

Queste sono le righe che contano della sezione F4 di `docs/REQUIREMENTS.md`, in inglese come tutti i documenti del repo:

```markdown
### F4 — Upload
- F4.2 Client-side validation: MIME (JPG/PNG/WebP), size (≤ 10 MB)
- F4.3 Up to 20 files per submission
- F4.6 Upload returns immediately; processing happens in the background
```

Il criterio AC-F4-3 dice che inviare 21 file mostra "Up to 20 files at once" e blocca l'invio. Le 500 foto dello stakeholder diventano quindi 25 invii da 20: un limite deciso a tavolino e scritto nei requisiti, così nessuno lo scopre in produzione.

### Prima i documenti, poi il codice

Ogni feature in corsa parte dallo stesso prompt. Lo uso in Plan Mode (`Shift+Tab` fino a `plan mode on`, oppure `/plan`), così Claude legge e propone senza toccare file:

::: {.callout .callout-prompt}
[Prompt riusabile]{.callout-title}

```text
Ho un progetto con docs/REQUIREMENTS.md, docs/DESIGN.md e docs/TASKS.md
già consolidati. Voglio aggiungere questa feature: [DESCRIZIONE FEATURE].

Esegui questi passi in ordine:

1. Leggi i tre file per capire lo stato attuale
2. Proponi la sezione da aggiungere a REQUIREMENTS.md
   (requisiti, vincoli e criteri di accettazione espliciti)
3. Proponi le modifiche a DESIGN.md (schema, endpoint, componenti)
4. Proponi i task da aggiungere a TASKS.md, con dipendenze, ID nuovi
   che non collidano con quelli esistenti e criteri di completamento
   verificabili
5. Prima di eseguire qualsiasi task, verifica se la feature richiede
   una migrazione DB e se nel codice c'è già qualcosa di simile
   che rischia di confliggere

Non iniziare l'esecuzione finché non ho approvato le modifiche ai tre file.
```
:::

Il passo che la gente salta è il quarto: senza task nel piano, il lavoro nuovo galleggia senza dipendenze e Claude non sa come incastrarlo in quello che è già fatto.

Per il batch su S3 non servono fasi nuove: il lavoro è già in `TASKS.md`, ed è la Fase 8, "AWS migration (S3 + SQS via env vars)". L'intento è nel nome: stesso codice, cambia solo il file `.env`. Va deciso cosa fare subito e cosa rinviare al deploy.

### Da disco locale a S3

Grazie ai contratti della Fase 6, S3 è configurazione. `PhotoStorage` è legato a `DiskPhotoStorage` e non esiste una classe `S3PhotoStorage`: la classe lavora su due dischi Laravel, `photos_private` per gli originali e `photos` per le varianti, definiti fin da T006, e `PHOTOS_DRIVER` decide se sono cartelle locali o bucket S3. Il blocco di produzione è in `DESIGN.md` §12.5:

```text
QUEUE_CONNECTION=sqs
SQS_QUEUE=photogallery-pro
SQS_REGION=eu-west-1

FILESYSTEM_DISK=photos
PHOTOS_DRIVER=s3
AWS_BUCKET_PUBLIC=photogallery-pro-prod
AWS_BUCKET_PRIVATE=photogallery-pro-prod-private
AWS_URL=https://cdn.example.com
```

Più le credenziali `SQS_*` e `AWS_*`, che nel documento sono segnaposto. Il bucket privato tiene gli originali, con Block Public Access attivo e accesso solo tramite `temporaryUrl()` a 5 minuti; quello pubblico tiene le varianti, dietro CloudFront.

Sul branch la Fase 8 è chiusa solo in parte. T089 è fatto: un audit che con `grep` cerca `storage_path`, `storage/app`, `disk('public')` e `file_get_contents` dentro `app/` e non trova niente fuori da `config/`. È il task che conta adesso, perché un path locale scritto a mano romperebbe la pipeline il giorno in cui i dischi diventano bucket. T086 (`.env.production.example`), T087 (`docs/DEPLOY.md`) e T088 (lo script `smoke-aws.php`) restano aperti fino al deploy del capitolo 23.

In sviluppo Sail avvia MinIO, e `backend/.env.example` punta già lì le variabili `AWS_*`, invitando a passare `PHOTOS_DRIVER` a `s3` per provare in locale il percorso di produzione. Prima leggi il ramo `s3` dei dischi `photos` e `photos_private` in `config/filesystems.php`: non legge `AWS_ENDPOINT` né `AWS_USE_PATH_STYLE_ENDPOINT`, e prende i bucket da `AWS_BUCKET_PUBLIC` e `AWS_BUCKET_PRIVATE`, commentati nel file di esempio. Senza `endpoint` l'SDK di AWS punta agli indirizzi veri di S3, quindi così com'è il driver `s3` non parla con MinIO. Il file di esempio non lo dice, e conviene trasformarlo subito in un task.

### Il flusso, in breve

Per ragionare su retry e transazioni serve sotto gli occhi quello che la Track A del capitolo 20 ha lasciato in `main`:

```text
Browser                 Backend Laravel                Coda              Storage
   |                          |                         |                   |
   |-- POST /photos --------->|                         |                   |
   |   (1-20 file)            |-- strip GPS, originale ----------------->  photos_private
   |                          |-- righe Photo (transazione)                 |
   |                          |-- Bus::batch(ProcessPhoto x N) -->|         |
   |<-- 202 + Location -------|                         |                   |
   |                          |                         |-- worker -------> photos
   |-- GET /photos/batch/{id} |                         |   (300/800/1600 px)
```

Il controller risponde `202 Accepted` con un header `Location`, e `useBatchPoll` interroga l'endpoint ogni secondo (`BATCH_MS` in `src/data/polling.ts`) finché la risposta dice `finished: true`. In sviluppo la coda è la tabella `jobs` del database; in produzione è SQS, con il worker sotto Supervisor: `php artisan queue:work sqs --queue=photogallery-pro --tries=3 --timeout=180 --sleep=3 --memory=512` (`DESIGN.md` §12.6).

### Il dispatch fuori dalla transazione

Prima committi, poi fai il dispatch. Se metti in coda il job dentro la transazione, un worker veloce può prenderlo prima del commit, cercare una riga che ancora non esiste e fallire con un errore che non fa pensare alla transazione.

Sul branch la action restituisce i job dalla closure della transazione e li mette in coda dopo:

```php
[$photos, $jobs] = DB::transaction(function () use ($files, $user, $albumId, $tagNames, $titles, $description): array {
    $photos = [];
    $jobs = [];

    foreach ($files as $index => $file) {
        // strip GPS, storeOriginal, Photo::create(...), tag, evento
        $photos[] = $photo;
        $jobs[] = new ProcessPhoto($photo);
    }

    return [$photos, $jobs];
});

$batch = Bus::batch($jobs)->dispatch();
```

Non ci siamo arrivati da soli: la review di fine fase aveva segnalato come High proprio un `Bus::batch()` dentro `DB::transaction()`. Il report è in `docs/BATCH-2026-04-29.md`.

### Il worker e l'idempotenza

Il job deve essere **idempotente**: elaborare due volte la stessa foto deve dare lo stesso risultato, senza file o righe duplicati. È il requisito che si dimentica più facilmente, e senza di lui ogni retry lascia spazzatura su S3.

```php
final class ProcessPhoto implements ShouldQueue
{
    public int $tries = 3;

    /** @var int[] */
    public array $backoff = [10, 30, 60];

    public function handle(ImageProcessor $processor, ExifExtractor $exif): void
    {
        $this->photo->update(['processing_status' => ProcessingStatus::Processing]);
        $processor->generate($this->photo);

        $absolutePath = Storage::disk('photos_private')->path($this->photo->original_path);
        $exifData = $exif->extract($absolutePath);

        // update: exif + processing_status Completed, poi event(PhotoProcessed)
    }

    public function failed(\Throwable $e): void
    {
        report($e);

        $this->photo->update([
            'processing_status' => ProcessingStatus::Failed,
            'processing_error' => 'Processing failed. Please try again or contact support.',
        ]);
    }
}
```

Su SQS i retry sono la normalità: un worker che muore a metà, un timeout, un messaggio che torna visibile. Il job prevede tre tentativi a 10, 30 e 60 secondi. Dopo l'ultimo, `failed()` segna la foto come `failed` con un messaggio generico, e il testo dell'eccezione, che può contenere path del server, resta nel log (anche questo viene da un finding di review).

L'idempotenza qui viene da una chiave deterministica. `DiskPhotoStorage::storeVariant()` scrive ogni variante in un path che dipende solo dall'UUID della foto e dal nome della variante:

```php
public function storeVariant(string $photoId, string $variant, string $contents): string
{
    $relativePath = "{$variant}/{$photoId}.jpg";

    Storage::disk('photos')->put($relativePath, $contents);

    return $relativePath;
}
```

Un retry riscrive `thumbnail/<uuid>.jpg` sopra se stesso invece di crearne un secondo, e non lascia mezze varianti da un tentativo interrotto. Un worker che inventa un nome nuovo a ogni esecuzione, con tre tentativi e invii da venti foto, riempie S3 di oggetti orfani che paghi tutti.

C'è una riga del job che su S3 non può funzionare: `Storage::disk('photos_private')->path(...)`. Su un disco `local` restituisce un path del filesystem; su un disco `s3` restituisce la chiave dell'oggetto, che `exif_read_data` non può aprire. Se il file non esiste l'estrattore restituisce un array vuoto, quindi niente eccezioni: le foto escono semplicemente senza EXIF. A dire il vero su questo branch l'EXIF manca anche in locale, perché `stripGps()` ricodifica l'immagine e insieme al GPS toglie tutti i metadati prima che l'originale venga salvato. Sul branch del capitolo 22 l'EXIF si legge al momento dell'upload, dal file caricato e prima di `stripGps()`, e nel job resta solo come ripiego.

Un'ultima cosa sui batch. `UploadPhotosAction` chiama `Bus::batch($jobs)->dispatch()` senza `allowFailures()`, e con il default di Laravel il primo job fallito cancella il batch, che da quel momento risulta già `finished`. Le altre foto vengono elaborate lo stesso, perché `ProcessPhoto` non controlla se il batch è stato cancellato, ma `useBatchPoll` smette di interrogare prima che abbiano finito. Con `allowFailures()` il problema si rovescia: un batch con un fallimento non arriva mai a `finished`, e il polling non si ferma più. Se ti serve uno stato affidabile, calcolalo dalle righe `Photo` del batch, che l'endpoint restituisce già una per una.

### Quando il backend diventa il collo di bottiglia

Sul branch i byte delle foto passano ancora dal backend, che toglie i dati GPS e li scrive su `photos_private`. Per 20 file da 10 MB va bene. Se servissero centinaia di foto alla volta, il passo successivo è l'upload diretto su S3: il backend firma un presigned URL con scadenza breve (15 minuti limitano i danni di un URL trapelato), il frontend fa la `PUT` direttamente sul bucket e poi avvisa il backend, che crea la riga `Photo` e mette in coda il job. Ha un costo: la rimozione dei dati GPS, che oggi avviene prima di salvare l'originale, andrebbe spostata nel worker, e per qualche secondo l'originale con le coordinate starebbe su S3. Per la scala del Photogallery il compromesso non vale, ed è il motivo per cui F4.3 dice 20 file.

### Il 403 sulle varianti

Durante il test end-to-end di T080, l'upload reale con il queue worker acceso che il capitolo 20 lascia da fare a mano, le varianti venivano generate, ma il browser riceveva `403 Forbidden` sulle immagini `medium` e `large`. Il link simbolico `public/storage` era giusto, e un `curl` diretto dava lo stesso 403.

Il colpevole era l'opzione `serve` dei dischi locali. In Laravel 13 un disco `local` con `'serve' => true` registra una route `GET <url del disco>/{path}` che serve i file passando da PHP, e un disco senza `url` la registra su `/storage`. Il disco `local` dello scaffold ha `serve` attiva, quindi la sua route `/storage/{path}` catturava anche `/storage/photos/...`. Per un disco privato quella route vuole un URL firmato: senza firma risponde 403, o 404 in produzione.

La configurazione sul branch, in `config/filesystems.php`, attiva `serve` solo sul disco pubblico delle varianti e lo toglie dal disco `local`:

```php
'local' => [
    'driver' => 'local',
    'root' => storage_path('app/private'),
    'throw' => false,
    'report' => false,
],

// ...

'photos' => env('PHOTOS_DRIVER', 'local') === 's3'
    ? [ /* driver s3, bucket AWS_BUCKET_PUBLIC */ ]
    : [
        'driver' => 'local',
        'root' => storage_path('app/public/photos'),
        'url' => rtrim(env('APP_URL', 'http://localhost'), '/').'/storage/photos',
        'visibility' => 'public',
        'serve' => true,
        'throw' => true,
    ],
```

Un bug così non lo trova nessun test unitario: serve il giro completo, dall'upload al browser.

### La review della fase

Insieme a T080 è partita la review di fine fase, con Claude e Gemini sulle Fasi 5 e 6. Il report `docs/BATCH-2026-04-29.md` elenca, tra gli altri, questi finding. Il più grave era un path traversal: i path delle varianti usavano il nome file mandato dal client, e il fix usa l'UUID della foto e `basename()` sul nome salvato. Poi un file temporaneo di `PhpExifExtractor::stripGps()`, con dentro l'originale completo di GPS, che non veniva mai cancellato; sul branch lo cancella una `register_shutdown_function`. C'era il dispatch dentro la transazione, già visto. E un High sulle foto leggibili senza autenticazione, che il design prevede per il visitatore anonimo di `REQUIREMENTS.md`: lì la risposta giusta era confermare l'intento, non cambiare il codice.

I numeri alla fine della fase: 175 test backend verdi (più uno saltato e un fallimento sul CORS che c'era già), zero errori TypeScript, 110 KB gzip per il bundle principale dopo il code splitting per pagina (il budget è 200 KB).

::: {.callout .callout-deep-dive}
[Sotto il cofano]{.callout-title}

Su questo branch `GET /photos/batch/{batchId}` trova le foto del batch per utente e per `created_at` successivo alla creazione del batch, un'approssimazione che due upload ravvicinati confondono. La colonna `batch_id` su `photos` arriva con le correzioni del capitolo 22 (`book/cap-15-post-review-fixes`).
:::

## 21.2 La pagina di registrazione che mancava

### Come te ne accorgi

Rifai il percorso da capo come un utente nuovo e trovi una pagina di login fatta bene, con validazione ed errori del server. Nessun modo, però, di creare un account: niente link, niente route `/register`.

Vai a controllare. In `REQUIREMENTS.md` la registrazione c'è, F9.1 "Email + password registration" e la user story US-30. Nel backend `POST /api/v1/auth/register` esiste ed è coperto da `AuthControllerTest`. In `src/data/copy.ts` ci sono perfino le stringhe, da `registerHeading: 'Create a new account'` a `noAccount: "Don't have an account?"`. Mancava solo l'interfaccia che le usasse.

### Cosa diceva il piano

Apri `TASKS.md` e cerca il task delle pagine frontend:

```markdown
### T070 — Pages: `GalleryPage`, `FavoritesPage`, `AlbumPage`, `LoginPage`, `NotFoundPage`
- **Status:** [x]
- **Acceptance:**
  - Each page reads filters from URL search params and feeds them into `usePhotos`.
  - LoginPage uses `useAuth.login`; redirects to intended route.
  - NotFoundPage renders empty state.
- **Commit:** `feat(frontend): page components wired to hooks`
```

Il problema sta nei criteri di accettazione. Chi aveva scritto il requisito pensava "pagina di autenticazione", quindi login e registrazione. Il task però dice solo `useAuth.login`, e Claude ha implementato esattamente quello. Il report del 29 aprile chiude T070 con "LoginPage (form + 422 errors)".

Un `[x]` in `TASKS.md` è una dichiarazione di intento. La garanzia arriva con le prove: un commit, un test che esercita il flusso, uno screenshot del browser. Vale per un collega umano come per un agent.

### L'audit: cos'altro è chiuso ma non fatto

Se un buco così è passato, ce ne sono altri. Prima di correggere conviene un audit, sempre in Plan Mode:

```text
Leggi docs/TASKS.md e per ogni task marcato [x]:
1. Identifica il codice che dovrebbe implementarlo
2. Verifica che quel codice esista davvero nel repository
3. Confronta i criteri di accettazione del task con i requisiti
   di REQUIREMENTS.md che il task dichiara di coprire
4. Segnala ogni caso in cui il task è chiuso ma l'implementazione
   sembra parziale, assente o più stretta del requisito

Non correggere nulla: prima voglio la lista completa dei gap.
```

Nel Photogallery questo audit ha un task suo, T107, e un output versionato: `docs/SPEC-COVERAGE.md`. Confronta le 42 sottosezioni di `DESIGN.md` con il codice e i test: 27 implementate, 11 parziali, 4 mancanti. Tra le mancanze ci sono file promessi dal design e mai creati, come `MarkFavoriteAction.php` (la logica è finita nel controller) o il test `BatchProgressTest.php`. Non tutto va corretto subito, ma ogni voce diventa una decisione: si fa, si aggiorna il design, o si dichiara fuori scope.

### Il fix: un componente, due modalità

La registrazione blocca l'onboarding, quindi va per prima. La soluzione sul branch riusa `LoginPage` invece di creare un secondo componente: uno stato `mode` alterna login e registrazione.

```tsx
type AuthMode = 'login' | 'register';

export function LoginPage() {
  const loginMutation = useLogin();
  const registerMutation = useRegister();
  const [mode, setMode] = useState<AuthMode>('login');
  // name, email, password, passwordConfirmation, errors...
  const isLogin = mode === 'login';

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // onSuccess naviga a '/', onError mostra gli errori 422 per campo
    if (isLogin) {
      loginMutation.mutate({ email, password }, { onSuccess, onError });
    } else {
      registerMutation.mutate(
        { name, email, password, password_confirmation: passwordConfirmation },
        { onSuccess, onError },
      );
    }
  };

  const toggleMode = () => setMode(isLogin ? 'register' : 'login'); // e azzera gli errori
  // ... JSX del form
}
```

In modalità registrazione il form mostra anche i campi `name` e `password_confirmation`, titolo e bottone prendono le stringhe da `copy.auth`, e il link in fondo chiama `toggleMode` senza cambiare pagina. La correzione completa: `useRegister` in `src/hooks/useAuth.ts` accanto a `useLogin`, lo stato `mode`, i campi extra nel JSX, gli errori 422 per campo in entrambe le modalità, il test manuale del flusso (creazione account, login automatico, redirect alla galleria) e un commit che dichiara il buco di scope.

Il commit conta: un messaggio come `fix(frontend): add register mode to LoginPage (scope gap in T070)` spiega a chi legge la history perché un task chiuso è stato riaperto. La route `/register` è arrivata dopo, con T121 della Fase 14 (`feat(frontend): empty state CTA + /register route`), che la fa puntare alla stessa `LoginPage`.

C'è un dettaglio che lo stesso audit avrebbe dovuto trovare, e lo uso per l'esercizio di fine capitolo: `mode` parte sempre da `'login'`, quindi chi apre `/register` vede comunque il form di login.

### Il prompt di chiusura della wave

Per non ripetere l'errore, alla fine di ogni wave uso un prompt di chiusura fisso:

```text
Prima di marcare questa wave come completata, verifica:

1. Per ogni task marcato [x]: esiste nel repository il codice che
   corrisponde ai criteri di accettazione? Voglio il path del file,
   non "dovrebbe esistere".
2. Rileggendo i requisiti che questa wave dichiara di coprire,
   c'è qualcosa che i task non coprono?
3. Esiste almeno un test (automatico, o manuale documentato) che
   esercita ogni flusso utente citato in quei requisiti?

Se trovi gap, elencali. Non chiudere la wave finché la lista non è vuota
o le eccezioni non sono documentate esplicitamente come fuori scope.
```

Zero gap non lo garantisce nessun prompt, ma questo forza il controllo incrociato tra requisiti e task, il punto dove il flusso normale si rompe.

### Il drift tra requisiti e task

Il caso della registrazione ha un nome: drift tra requisiti e task, la distanza che si accumula tra quello che i requisiti dicono e quello che i task implementano. Nasce quando trasformi un requisito in task con scelte implicite: "Auth" può voler dire solo login, login e registrazione, oppure anche il reset della password. Se la scelta non finisce nei criteri di accettazione, il risultato copre meno del requisito.

Il drift va anche nell'altra direzione, dal codice verso i documenti. AC-F8-5 dice che `GET /photos?is_favorite=1` restituisce i preferiti dell'utente, ma `IndexPhotosRequest` e il frontend usano il parametro `favorites`. Il codice funziona, i test passano, e il criterio di accettazione descrive un'API che non esiste.

La difesa sono criteri espliciti: ogni pagina, route ed endpoint del requisito compare per nome nel task. Un criterio verificabile suona così: "pagina `/login` funzionante, form di registrazione raggiungibile da `/register` e dallo switch sulla pagina di login, chiamata a `POST /api/v1/auth/register` con gestione degli errori 422".

## 21.3 Foto preferite, da booleano a tabella pivot

### Il requisito

Ogni utente vuole la sua lista di foto preferite, da gestire con un clic e ritrovare in una vista dedicata. In `REQUIREMENTS.md` è la sezione F8:

```markdown
### F8 — Favorites
- F8.1 Per-member favorites: any authenticated user can favorite any photo (many-to-many `users ↔ photos` via `favorites` pivot table)
- F8.3 Optimistic UI (heart fills before the request returns)
- F8.5 Favorite count visible per photo (how many users favorited it)
```

Con criteri come AC-F8-1: `PUT /photos/{id}/favorite` è idempotente, due chiamate consecutive restituiscono 204 e inseriscono una sola riga in `favorites`. Feature piccola e circoscritta, il tipo giusto da aggiungere in corsa.

### L'errore di modellazione

La prima versione del design aveva la soluzione più ovvia: una colonna booleana `is_favorite` sulla tabella `photos`, con un indice composto su `is_favorite` e `created_at`. Funziona finché l'utente è uno solo. Una colonna sulla foto rappresenta un preferito globale: la foto è preferita per tutti o per nessuno.

La relazione tra utenti e foto preferite è N a M, e vuole una tabella di relazione. Se chiedi a Claude "aggiungi le foto preferite" senza altro contesto, la colonna booleana è una proposta plausibile, ed è qui che serve chi supervisiona. Prima di accettarla chiedi: "la relazione utente-foto preferita è 1 a N o N a M?". La risposta decide schema, endpoint e componenti.

### La Fase 6.5

Il correttivo è una fase inserita tra la 6 e la 7, con wave 1.5 nella tabella riassuntiva di `TASKS.md`:

```text
T090  Migration: pivot favorites, drop di is_favorite
T091  Relazioni favoritedBy e favoritePhotos
T092  PhotoController favorite/unfavorite, PhotoData con favorites_count
T093  Filament PhotoResource: favorites_count al posto del toggle
T094  Hook e componenti frontend
T095  Test (A preferisce la foto di B: compare solo nella lista di A)
```

Guarda gli ID. T090-T095 esistevano già: T090-T094 sono gli hook della Fase 9, T095 apre la Fase 10. La fase inserita ha ripreso la numerazione dopo T080, e ora `TASKS.md` ha due T090 diversi. Nessun test lo rileva, ma "fai T092" detto a Claude diventa ambiguo, e così i messaggi di commit e il template della PR, che chiede di citare gli ID. Quando inserisci una fase in corsa usa ID dopo l'ultimo esistente (qui da T125) o un prefisso dedicato: per questo il prompt riusabile chiede ID che non collidano.

### La migrazione: crea, travasa, elimina

La colonna `is_favorite` esisteva già e conteneva dati, quindi la migrazione fa tre cose in sequenza: crea la nuova struttura, ci copia i dati esistenti, elimina la vecchia. Questa è `2026_04_30_135152_create_favorites_table.php`:

```php
public function up(): void
{
    Schema::create('favorites', function (Blueprint $table) {
        $table->foreignUuid('user_id')->constrained('users')
            ->cascadeOnUpdate()->cascadeOnDelete();
        $table->foreignUuid('photo_id')->constrained('photos')
            ->cascadeOnUpdate()->cascadeOnDelete();
        $table->timestamp('created_at')->useCurrent();

        $table->primary(['user_id', 'photo_id']);
        $table->index('photo_id');
    });

    // Data migration: move existing is_favorite=true to pivot rows
    if (Schema::hasColumn('photos', 'is_favorite')) {
        DB::table('photos')
            ->where('is_favorite', true)
            ->orderBy('id')
            ->each(function (object $photo) {
                DB::table('favorites')->insertOrIgnore([
                    'user_id' => $photo->user_id,
                    'photo_id' => $photo->id,
                    'created_at' => now(),
                ]);
            });

        Schema::table('photos', function (Blueprint $table) {
            $table->dropIndex('photos_favorite_created_idx');
            $table->dropColumn('is_favorite');
        });
    }
}
```

Le chiavi sono UUID (`foreignUuid`) perché tutto il progetto usa UUID v7. La chiave primaria composta impedisce i duplicati a livello di database, anche con due richieste in parallelo, e `cascadeOnDelete` fa sparire i preferiti con la foto o con l'utente. Il `hasColumn` rende la migrazione sicura su un database nuovo, dove `is_favorite` non è mai esistita. I preferiti esistenti vanno al proprietario della foto, l'unica attribuzione possibile per un flag globale, e `down()` fa il percorso inverso. Lo stesso schema in tre tempi vale per qualsiasi refactoring con dati da conservare.

### Relazioni ed endpoint idempotenti

Con la tabella in posizione, le relazioni nei modelli sono due righe ciascuna:

```php
// Photo
public function favoritedBy(): BelongsToMany
{
    return $this->belongsToMany(User::class, 'favorites')
        ->withPivot('created_at');
}
```

`User::favoritePhotos()` è lo specchio, con `Photo::class`. `withPivot('created_at')` al posto di `withTimestamps()`, perché il pivot ha solo `created_at`.

Per l'API la tentazione è un unico endpoint di toggle con `toggle()` di Eloquent. Il progetto usa invece due endpoint idempotenti, come chiede AC-F8-1:

```php
// PUT /photos/{photo}/favorite: idempotente, risponde sempre 204
public function favorite(Request $request, Photo $photo): Response
{
    if (! $request->user()?->tokenCan(TokenAbility::PhotosWrite->value)) {
        throw new AuthorizationException;
    }

    $request->user()->favoritePhotos()->syncWithoutDetaching([$photo->id]);

    return response()->noContent();
}
```

`unfavorite()` è identico con `detach($photo->id)` su `DELETE`. Un toggle ripetuto per un retry di rete, o per un doppio clic, inverte lo stato due volte e ti lascia dove eri partito. `PUT` e `DELETE` dicono lo stato finale che vuoi, e ripeterli non cambia niente. Il controllo `tokenCan` è la regola del progetto per ogni endpoint che modifica dati: il token Sanctum deve avere l'ability `photos:write`.

### Il frontend: optimistic UI

Il cuore sulla card deve cambiare al clic, prima che il server risponda (F8.3). È l'**optimistic UI**: aggiorni la cache come se la richiesta fosse già andata a buon fine e torni indietro solo se il server risponde con un errore. Questo è `useToggleFavorite` in `src/hooks/usePhotos.ts`, con qualche riga omessa:

```typescript
export function useToggleFavorite() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, isFavorite }: { id: string; isFavorite: boolean }) =>
      isFavorite ? removeFavorite(id) : addFavorite(id),
    onMutate: async ({ id, isFavorite }) => {
      await queryClient.cancelQueries({ queryKey: ['photo', id] });
      await queryClient.cancelQueries({ queryKey: ['photos'] });
      const previousPhoto = queryClient.getQueryData<SingleResponse<Photo>>(['photo', id]);
      // ... aggiornamento della cache ['photo', id]

      // Update all infinite list caches (photos list)
      queryClient.setQueriesData<{ pages: PaginatedResponse<Photo>[]; pageParams: unknown[] }>(
        { queryKey: ['photos'] },
        (old) => {
          if (!old) return old;
          return {
            ...old,
            pages: old.pages.map((page) => ({
              ...page,
              data: page.data.map((photo) =>
                photo.id === id
                  ? { ...photo, is_favorite: !isFavorite,
                      favorites_count: photo.favorites_count + (isFavorite ? -1 : 1) }
                  : photo,
              ),
            })),
          };
        },
      );
      return { previousPhoto };
    },
    onError: (_err, { id }, context) => {
      if (context?.previousPhoto) {
        queryClient.setQueryData(['photo', id], context.previousPhoto);
      }
      queryClient.invalidateQueries({ queryKey: ['photos'] });
    },
    // onSettled invalida ['photos'] e ['photo', id]
  });
}
```

La prima versione sbagliava un dettaglio: la galleria è una `useInfiniteQuery`, quindi l'aggiornamento ottimistico deve toccare tutte le pagine delle liste `['photos']`, oltre alla cache della singola foto. Senza, il cuore si accendeva nel lightbox ma non nella griglia; la review della Fase 5 l'aveva segnalato come High. `mutationFn` sceglie `PUT` o `DELETE` in base allo stato attuale, quindi il toggle esiste solo nell'interfaccia, mentre l'API resta idempotente.

Nella card, `PhotoCard.tsx`:

```tsx
const handleFavoriteClick = (e: React.MouseEvent) => {
  e.stopPropagation();
  toggleFavorite.mutate({ id: photo.id, isFavorite: photo.is_favorite });
};

// ...

<button
  type="button"
  onClick={handleFavoriteClick}
  aria-label={photo.is_favorite ? copy.favorites.remove : copy.favorites.add}
  className="..."
>
  <Heart className={photo.is_favorite ? 'fill-red-500 text-red-500' : 'text-white'} />
  {photo.favorites_count > 0 && <span className="...">{photo.favorites_count}</span>}
</button>
```

Le classi Tailwind sono abbreviate; nel file sono molte di più.

`stopPropagation()` evita che il clic sul cuore apra il lightbox. Il badge mostra `favorites_count` (F8.5), il totale di tutti gli utenti, mentre `is_favorite` vale per chi guarda. La vista dedicata è la route `/favorites`, che monta `FavoritesPage` e chiama l'API con `favorites=1`. Il flusso è coperto da `e2e/favorites.spec.ts` in Playwright, con l'API mockata.

### Quanto ci vuole, e con quanti agent

Nella prima edizione avevo cronometrato una feature di questa dimensione: poco più di due ore dai requisiti al merge, test e review compresi. La parte più lunga sono i requisiti, una ventina di minuti di discussione con Claude, ed è tempo che si ripaga: una modellazione sbagliata o un'API che non combacia con il frontend costano di più quando li scopri dopo.

Per feature così basta uno sviluppatore con un solo agent, in sequenza, nella stessa sessione. I task dipendono l'uno dall'altro (il frontend non si scrive prima che l'API esista), quindi non c'è niente da parallelizzare. Worktree e sessioni in background (capitolo 20) servono quando le track sono davvero indipendenti, come la Fase 4 e la Fase 6.

## 21.4 PR che toccano backend e frontend

### Una PR o due

Le tre feature del capitolo attraversano lo stesso confine: i preferiti hanno una migrazione, due endpoint, una risorsa Filament e un hook con optimistic UI. L'ordine ideale è una PR per il backend (migrazione, API, test di integrazione) e, dopo il merge, una per il frontend. Ogni PR si rivede da sola e il frontend consuma un'API già stabile. Con Claude Code capita più spesso la PR unica, perché i due lati nascono nella stessa sessione e separarli dopo vuol dire riscrivere la history. Se vuoi le due PR senza quel lavoro, imposta la separazione dall'inizio: un worktree per lato, come nel capitolo 20, con il branch del frontend che parte da quello del backend.

La PR unica regge finché la review la tratta per quello che è. Nel progetto ne è passata una molto grande: le Fasi 3-14 sono arrivate su `main` con un solo squash merge, il commit `a0a5437`, 171 file cambiati.

### Due passate di review sulla stessa PR

Una sola passata su una PR cross-stack mescola le prospettive e resta in superficie su entrambe. Meglio due passate, ciascuna con un focus dichiarato nel prompt. La prima guarda il backend: query, permessi di ogni endpoint, errori, idempotenza dei job, transazioni e dispatch, N+1. La seconda guarda il frontend: `aria-label` e tastiera, stati di caricamento ed errore, optimistic UI e rollback, peso del bundle, resa su mobile. Il capitolo 22 mostra come farle con `/code-review` e con un secondo modello.

### L'ordine di deploy

Anche con una PR unica, il deploy segue sempre lo stesso ordine: prima il backend, poi il frontend.

Se arriva prima il frontend, chiama endpoint che non esistono e gli utenti vedono errori. Se arriva prima il backend, il frontend vecchio continua a funzionare con gli endpoint che c'erano già, e quello nuovo trova le API che si aspetta. La sequenza è quindi: deploy del backend, verifica che il frontend attuale funzioni ancora, deploy del frontend, verifica dei flussi nuovi.

In GitHub Actions diventa un workflow solo, con un controllo tra i due deploy. Il deploy vero del Photogallery su AWS è il capitolo 23.

### Feature flag per le feature grandi

Per una feature grossa come il batch c'è un'opzione in più, il feature flag: deployi tutto il backend, ma la parte nuova del frontend resta nascosta dietro un flag e la vede solo il team, o una parte degli utenti, finché non la allarghi. Alla scala del Photogallery è eccessivo; con molti utenti attivi fa la differenza tra un rilascio controllato e un incendio da spegnere di notte.

### La checklist prima del merge

Il repo ha già un `.github/PULL_REQUEST_TEMPLATE.md` che chiede gli ID dei task di `TASKS.md`, le sezioni di `DESIGN.md` toccate e il test plan (`php artisan test --compact`, `npm test -- --run`, Pint, Prettier, ESLint). Per le PR cross-stack aggiungo questa lista:

```text
Backend
[ ] Nessuna query N+1 nelle rotte nuove (query log o QueryDetector)
[ ] Permessi su ogni endpoint (autenticato o pubblico, ability del token)
[ ] Migrazione provata su DB vuoto e su DB con dati

Frontend
[ ] Nessun console.error in sviluppo
[ ] Componenti accessibili (aria-label, tastiera)
[ ] Bundle entro il budget del progetto (200 KB gzip)

Cross-stack
[ ] Contratto API identico tra frontend e backend (campi e parametri)
[ ] Errori 401, 403, 404, 422, 500 mostrati correttamente
[ ] Ordine di deploy scritto nella descrizione della PR
```

La riga sul contratto API è quella che avrebbe trovato il `favorites` contro `is_favorite` della sezione 21.2.

## Riepilogo {.unlisted}

- Una feature in corsa entra dai documenti: requisiti, design e task approvati prima del codice, con il prompt riusabile della sezione 21.1 in Plan Mode.
- Per il batch su S3 servono un job idempotente (path deterministico per ogni variante), retry con attese crescenti e il dispatch dopo il commit della transazione. Il passaggio a S3 e SQS è configurazione, purché nessun file in `app/` usi path locali.
- Un task chiuso non dimostra niente: chiedi path, test e screenshot, e chiudi ogni wave con il prompt di verifica. Il drift tra requisiti e task si previene con criteri di accettazione che nominano pagine, route ed endpoint.
- Una relazione N a M vuole una tabella pivot, e un refactoring di schema con dati segue crea, travasa, elimina. Per gli endpoint preferisci `PUT` e `DELETE` idempotenti a un toggle.
- Una fase inserita in corsa prende ID di task nuovi, mai quelli già usati.
- Le PR cross-stack si rivedono in due passate (backend, poi frontend) e si deployano sempre con il backend prima.

## Esercizio {.unlisted}

Parti dal branch `book/cap-14-phases-complete` del repo companion e sistema il gap lasciato da T121: la route `/register` monta `LoginPage`, ma il form parte sempre in modalità login.

1. In Plan Mode, lancia il prompt riusabile della sezione 21.1 con la descrizione: "aprendo `/register` il form deve partire in modalità registrazione; aprendo `/login` in modalità login; lo switch continua a funzionare".
2. Fai aggiungere a `TASKS.md` un task con un ID nuovo (T125) e criteri che nominano entrambe le route.
3. Esegui il task con Claude, con un test Playwright in `e2e/auth.spec.ts` che apre `/register` e verifica il titolo "Create a new account".
4. Chiudi con il prompt di verifica della sezione 21.2, poi apri la PR con il template del repo e la checklist cross-stack.

L'esercizio è completo quando il nuovo test passa insieme al resto della suite (`npx playwright test` nella cartella `frontend`) e T125 è marcato `[x]` con il commit che lo implementa. In alternativa, applica gli stessi quattro passi a una feature piccola del tuo backlog, come un filtro di ricerca o un export CSV.
