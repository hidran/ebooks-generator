# Capitolo 21. Feature in corsa

## Cosa imparerai

Come aggiungere una feature a un progetto SDD già in esecuzione passando prima dai documenti e poi dal codice, con tre casi presi dal Photogallery: la pipeline di elaborazione batch delle foto su S3, la registrazione utente che il piano aveva perso per strada e le foto preferite rifatte da colonna booleana a tabella pivot. Alla fine vediamo come gestire una PR che tocca backend e frontend insieme.

Prerequisiti: i capitoli 17-20 (specifiche, SDD, esecuzione a wave, worktree) e il repo companion sul branch `book/cap-14-phases-complete`.

Alla fine del capitolo 20 la Wave 1 di `docs/TASKS.md` è mergiata in `main`: admin Filament, setup e componenti del frontend React, pipeline delle immagini (Fasi 3-6). Il piano procede. Poi un martedì alle 17 arriva il messaggio: "Ah, ci serve anche il caricamento di tante foto insieme, c'è chi arriva con 500 foto delle vacanze. E la registrazione? Non l'avevo scritta, ma era ovvia. Già che ci sei, i clienti chiedono sempre di salvare le foto preferite."

Le richieste in corsa arrivano anche con le specifiche migliori. Lo stakeholder vede l'applicazione crescere e si ricorda di cose che dava per scontate, oppure il mercato cambia le priorità. Il caso più insidioso è il terzo: la feature era nei requisiti, ma si è persa quando i requisiti sono diventati task, e nessuno se n'è accorto fino al primo test manuale. Evitarle non si può. Quello che puoi controllare è come entrano nel progetto: senza rompere quello che funziona e senza perdere il filo del piano.

Nel Photogallery i tre casi hanno un indirizzo preciso. Il batch parte dalla pipeline che la Track A ha costruito nel capitolo 20 e la porta verso S3 e SQS, che in `TASKS.md` è la Fase 8, nella Wave 2. La registrazione mancante è la distanza tra la user story US-30 e il task T070 della Fase 5, chiusa più tardi da T121. I preferiti sono la Fase 6.5, una fase inserita a metà percorso con il numero di wave 1.5. Il branch `book/cap-14-phases-complete` (290 file) contiene lo stato del progetto con tutte le fasi dalla 3 alla 14.

## 21.1 Batch processing delle foto su S3

### Il requisito

La regola che regge la pipeline è già in `main`: l'upload risponde subito e l'elaborazione pesante va in coda, dove la fa un worker. Se il backend generasse le varianti dentro la stessa richiesta HTTP, chi carica cinquanta foto guarderebbe uno spinner per minuti e il server si bloccherebbe al primo picco. La richiesta delle 500 foto mette alla prova i limiti scelti, e il passaggio a S3 mette alla prova quello che in locale non si vede: retry, transazioni, permessi sui file.

Questa è la sezione F4 di `docs/REQUIREMENTS.md` sul branch, in inglese come tutti i documenti del repo:

```markdown
### F4 — Upload
- F4.1 Drag-and-drop zone + click-to-browse
- F4.2 Client-side validation: MIME (JPG/PNG/WebP), size (≤ 10 MB)
- F4.3 Up to 20 files per submission
- F4.4 Per-file progress bar
- F4.5 Set album and tags at upload time via UploadModal form (or accept defaults)
- F4.6 Upload returns immediately; processing happens in the background
```

I criteri di accettazione sono ancora più espliciti. AC-F4-3, per esempio, dice che inviare 21 file mostra "Up to 20 files at once" e blocca l'invio. Le 500 foto dello stakeholder diventano quindi 25 invii da 20: un limite deciso a tavolino e scritto nei requisiti, così nessuno lo scopre in produzione.

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

Funziona su qualsiasi progetto con SDD attivo. Il passo che la gente salta è il quarto: senza task nel piano, il lavoro nuovo galleggia senza dipendenze e Claude non sa come incastrarlo in quello che è già fatto.

Per il batch su S3, la proposta di Claude non aggiunge fasi: il lavoro c'è già in `TASKS.md`, ed è la Fase 8, "AWS migration (S3 + SQS via env vars)". Il titolo dice tutto: stesso codice, cambia solo il file `.env`. Quello che va deciso è cosa fare subito e cosa rinviare al deploy.

### Da disco locale a S3

Il motivo per cui S3 è una questione di configurazione sta nel binding dei contratti in `AppServiceProvider`:

```php
public function register(): void
{
    $this->app->bind(ImageProcessor::class, InterventionImageProcessor::class);
    $this->app->bind(ExifExtractor::class, PhpExifExtractor::class);
    $this->app->bind(PhotoStorage::class, DiskPhotoStorage::class);
}
```

Non esiste una classe `S3PhotoStorage`. `DiskPhotoStorage` lavora su due dischi Laravel, `photos_private` per gli originali e `photos` per le varianti, definiti fin dalla Fase 1 (T006), e la variabile `PHOTOS_DRIVER` decide se quei dischi sono cartelle locali o bucket S3. In produzione la coda passa da `database` a SQS con `QUEUE_CONNECTION=sqs`. Il blocco di produzione è scritto in `DESIGN.md` §12.5:

```text
QUEUE_CONNECTION=sqs
SQS_KEY=...
SQS_SECRET=...
SQS_PREFIX=https://sqs.eu-west-1.amazonaws.com/...
SQS_QUEUE=photogallery-pro
SQS_REGION=eu-west-1

FILESYSTEM_DISK=photos
PHOTOS_DRIVER=s3
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=eu-west-1
AWS_BUCKET_PUBLIC=photogallery-pro-prod
AWS_BUCKET_PRIVATE=photogallery-pro-prod-private
AWS_URL=https://cdn.example.com
```

Due bucket: quello privato per gli originali, con Block Public Access attivo e accesso solo tramite `temporaryUrl()` a 5 minuti, e quello pubblico per le varianti, davanti a CloudFront.

Sul branch la Fase 8 è chiusa solo in parte. T089 è fatto: un audit che con `grep` cerca `storage_path`, `storage/app`, `disk('public')` e `file_get_contents` dentro `app/` e non trova niente fuori da `config/`. È il task che conta adesso, perché un solo path locale scritto a mano nel codice romperebbe la pipeline il giorno in cui i dischi diventano bucket. T086 (`.env.production.example`), T087 (`docs/DEPLOY.md`) e T088 (lo script `smoke-aws.php`) restano aperti fino al deploy del capitolo 23.

In sviluppo Sail avvia MinIO, e `backend/.env.example` punta già le variabili `AWS_*` lì, con l'invito a passare `PHOTOS_DRIVER` a `s3` per provare il percorso di produzione in locale. Prima di farlo leggi il ramo `s3` dei dischi `photos` e `photos_private` in `config/filesystems.php`: non legge `AWS_ENDPOINT` né `AWS_USE_PATH_STYLE_ENDPOINT`, e prende i bucket da `AWS_BUCKET_PUBLIC` e `AWS_BUCKET_PRIVATE`, che nel file di esempio sono commentati. Così com'è, il driver `s3` non parla con MinIO. È il genere di dettaglio che salta fuori solo provando, e che conviene trasformare subito in un task.

<!-- VERIFY: provare PHOTOS_DRIVER=s3 contro MinIO sul branch book/cap-14-phases-complete; i dischi photos/photos_private (ramo s3) non hanno 'endpoint' né 'use_path_style_endpoint'. -->

### Il flusso, in breve

Prima di toccare la configurazione conviene avere sotto gli occhi cosa ha lasciato in `main` la Track A del capitolo 20:

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
   |   ogni secondo           |                         |                   |
```

Il frontend manda `POST /api/v1/photos` con un form multipart. `StorePhotosRequest` valida da 1 a 20 file, ciascuno `jpg`, `jpeg`, `png` o `webp` fino a 10 MB. `UploadPhotosAction` toglie i dati GPS, salva l'originale sul disco privato, crea le righe `Photo` con `processing_status` a `pending` e mette in coda un `Bus::batch` di job `ProcessPhoto`. Il controller risponde `202 Accepted` con un header `Location` che punta a `/api/v1/photos/batch/{batchId}`. Da lì `useBatchPoll` interroga l'endpoint ogni `BATCH_MS` (1000 ms in `src/data/polling.ts`) e si ferma quando la risposta dice `finished: true`.

In sviluppo la coda è la tabella `jobs` del database; in produzione è SQS, e il worker gira sotto Supervisor con `php artisan queue:work sqs --queue=photogallery-pro --tries=3 --timeout=180 --sleep=3 --memory=512`, come scritto in `DESIGN.md` §12.6.

### Il dispatch fuori dalla transazione

La regola è una: prima committi, poi fai il dispatch. Se metti in coda il job dentro la transazione, un worker veloce può prenderlo prima del commit, cercare una riga che ancora non esiste e fallire con un errore che non ti fa pensare alla transazione. Con il driver di coda su database il rischio è concreto, perché la coda e le righe vivono nello stesso database.

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
    use Batchable, Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $tries = 3;

    /** @var int[] */
    public array $backoff = [10, 30, 60];

    public function __construct(public readonly Photo $photo) {}

    public function handle(ImageProcessor $processor, ExifExtractor $exif): void
    {
        $this->photo->update(['processing_status' => ProcessingStatus::Processing]);

        $processor->generate($this->photo);

        $absolutePath = Storage::disk('photos_private')->path($this->photo->original_path);
        $exifData = $exif->extract($absolutePath);

        $this->photo->update([
            'exif' => $exifData,
            'processing_status' => ProcessingStatus::Completed,
        ]);

        event(new PhotoProcessed($this->photo));
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

Su SQS i retry sono la normalità: un worker che muore a metà, un timeout, un messaggio che torna visibile. Il job prevede tre tentativi con attese di 10, 30 e 60 secondi. Se anche l'ultimo fallisce, `failed()` registra l'errore e segna la foto come `failed` con un messaggio generico: il testo dell'eccezione, che può contenere path del server, finisce nel log e non nella risposta all'utente (anche questo arriva da un finding di review).

L'idempotenza qui viene da una chiave deterministica. `DiskPhotoStorage::storeVariant()` scrive ogni variante in un path che dipende solo dall'UUID della foto e dal nome della variante:

```php
public function storeVariant(string $photoId, string $variant, string $contents): string
{
    $relativePath = "{$variant}/{$photoId}.jpg";

    Storage::disk('photos')->put($relativePath, $contents);

    return $relativePath;
}
```

Un retry riscrive `thumbnail/<uuid>.jpg` sopra se stesso invece di crearne un secondo. È più semplice del controllo "esiste già? allora salto", e non lascia mezze varianti corrotte da un tentativo interrotto.

C'è una riga del job che in locale funziona e su S3 no: `Storage::disk('photos_private')->path(...)`. Su un disco `local` restituisce un path del filesystem; su un disco `s3` restituisce la chiave dell'oggetto, che `exif_read_data` non può aprire. L'estrattore in caso di errore restituisce un array vuoto, quindi niente eccezioni: le foto escono semplicemente senza EXIF. Sul branch del capitolo 22 l'EXIF si legge al momento dell'upload, dal file temporaneo e prima che `stripGps()` lo cancelli, e nel job resta solo come ripiego.

<!-- VERIFY: comportamento di Storage::disk(...)->path() con driver s3 in Laravel 13 e risultato di PhpExifExtractor::extract() su quel path. -->

<!-- VERIFY: UploadPhotosAction chiama Bus::batch($jobs)->dispatch() senza allowFailures(). Con il comportamento di default di Laravel il primo job fallito marca il batch come cancelled: controllare che le altre foto vengano comunque elaborate e che /photos/batch/{id} arrivi a finished=true, altrimenti useBatchPoll non si ferma. -->

::: {.callout .callout-warning}
[Attenzione]{.callout-title}

Un worker che crea file con nomi nuovi a ogni esecuzione produce duplicati a ogni retry. Con tre tentativi e invii da venti foto, gli oggetti orfani su S3 si moltiplicano in fretta e li paghi tutti. Decidi il path deterministico prima di scrivere la logica di elaborazione.
:::

### Quando il backend diventa il collo di bottiglia

Sul branch i byte delle foto passano ancora dal backend: il server li riceve, toglie i dati GPS e li scrive su `photos_private`. Per 20 file da 10 MB va bene. Se un giorno servisse davvero accettare centinaia di foto alla volta, il passo successivo è l'upload diretto su S3 con presigned URL, e il backend non vedrebbe più i byte:

1. Il frontend chiede al backend un URL firmato per ogni file (nome e MIME type).
2. Il backend genera un presigned URL con scadenza breve, per esempio 15 minuti.
3. Il frontend carica il file su S3 con una `PUT` a quell'URL.
4. Il frontend avvisa il backend che l'upload è finito.
5. Il backend crea la riga `Photo` e mette in coda il job.

La scadenza breve limita i danni di un URL trapelato, e il limite di dimensione va imposto sia nella policy S3 sia nel frontend, che dà un errore immediato senza sprecare banda. Ha un costo: la rimozione dei dati GPS, che oggi avviene prima di salvare l'originale, andrebbe spostata nel worker, e per qualche secondo l'originale con le coordinate starebbe su S3. Per la scala del Photogallery il compromesso non vale, ed è il motivo per cui F4.3 dice 20 file.

### Il 403 sulle varianti

Durante il test end-to-end di T080, l'upload reale con il queue worker acceso che il capitolo 20 lascia da fare a mano, il worker generava le varianti correttamente, ma il browser riceveva `403 Forbidden` sulle immagini `medium` e `large`. Il link simbolico `public/storage` esisteva ed era giusto. Un `curl` diretto sull'URL dava lo stesso 403, quindi il routing dell'applicazione era fuori discussione.

Il colpevole era l'opzione `serve` dei dischi locali. Nelle versioni recenti di Laravel un disco `local` con `'serve' => true` registra una route che serve i file sotto il suo URL, e quella route intercetta le richieste prima del file statico. Il disco `local` di default la portava attiva, e le sue richieste senza firma finivano in 403.

<!-- VERIFY: versione di Laravel che ha introdotto 'serve' sui dischi local e comportamento esatto (route storage/{path}, URL firmati) in Laravel 13. -->

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
    ? [
        'driver' => 's3',
        // credenziali e bucket da AWS_*
        'bucket' => env('AWS_BUCKET_PUBLIC'),
        'visibility' => 'public',
        'throw' => true,
    ]
    : [
        'driver' => 'local',
        'root' => storage_path('app/public/photos'),
        'url' => rtrim(env('APP_URL', 'http://localhost'), '/').'/storage/photos',
        'visibility' => 'public',
        'serve' => true,
        'throw' => true,
    ],
```

Un bug così non lo trova nessun test unitario: serve il giro completo, dall'upload al browser. È anche la ragione per cui nel progetto la review automatica dopo ogni batch la fa almeno un secondo modello, oltre a quello che ha scritto il codice.

### La review della fase

Insieme a T080 è partita la review di fine fase, con Claude e Gemini sulle Fasi 5 e 6. Il report `docs/BATCH-2026-04-29.md` elenca, tra gli altri, questi finding.

Il più grave era un path traversal: i path delle varianti usavano il nome file mandato dal client. Il fix usa l'UUID della foto nel path e `basename()` sul nome salvato. Poi un file temporaneo creato da `PhpExifExtractor::stripGps()` che non veniva mai cancellato, con dentro l'originale completo di GPS; sul branch lo cancella una `register_shutdown_function`. C'era il dispatch dentro la transazione, già descritto sopra. E un finding High che segnalava tutte le foto leggibili senza autenticazione: in questo caso il design lo prevede, perché il visitatore anonimo di `REQUIREMENTS.md` sfoglia la galleria pubblica, quindi la risposta è stata confermare l'intento nel documento invece di cambiare il codice.

I numeri alla fine della fase: 175 test backend verdi, zero errori TypeScript, 110 KB gzip per il bundle principale dopo il code splitting per pagina (il budget è 200 KB).

::: {.callout .callout-deep-dive}
[Sotto il cofano]{.callout-title}

Sul branch `book/cap-14-phases-complete` l'endpoint `GET /photos/batch/{batchId}` trova le foto del batch filtrando per utente e per `created_at` successivo alla creazione del batch: un'approssimazione che due upload ravvicinati possono confondere. Il fix, una colonna `batch_id` su `photos`, arriva con le correzioni post-review del capitolo 22 sul branch `book/cap-15-post-review-fixes`.
:::

## 21.2 La pagina di registrazione che mancava

### Come te ne accorgi

Il login funziona, la galleria funziona, l'upload pure. Rifai il percorso da capo come un utente nuovo, e trovi la pagina di login con validazione ed errori del server gestiti bene. Nessun modo, però, di creare un account: niente link, niente route `/register`. Un utente nuovo non può entrare.

Vai a controllare. In `REQUIREMENTS.md` la registrazione c'è, F9.1 "Email + password registration" e la user story US-30. Nel backend `POST /api/v1/auth/register` esiste ed è coperto da `AuthControllerTest`. In `src/data/copy.ts` le stringhe sono già pronte:

```typescript
auth: {
  login: 'Log in',
  register: 'Create account',
  logout: 'Log out',
  emailLabel: 'Email',
  passwordLabel: 'Password',
  passwordConfirmLabel: 'Confirm password',
  nameLabel: 'Name',
  loginHeading: 'Sign in to your account',
  registerHeading: 'Create a new account',
  noAccount: "Don't have an account?",
  hasAccount: 'Already have an account?',
},
```

Mancava solo l'interfaccia che le usasse.

### Cosa diceva il piano

Apri `TASKS.md` e cerca il task delle pagine frontend:

```markdown
### T070 — Pages: `GalleryPage`, `FavoritesPage`, `AlbumPage`, `LoginPage`, `NotFoundPage`
- **Status:** [x]
- **Owner:** frontend-dev
- **Depends on:** T064, T067, T068
- **Parallel with:** T069
- **Reads:** REQUIREMENTS §3
- **Acceptance:**
  - Each page reads filters from URL search params and feeds them into `usePhotos`.
  - LoginPage uses `useAuth.login`; redirects to intended route.
  - NotFoundPage renders empty state.
- **Commit:** `feat(frontend): page components wired to hooks`
```

Il problema sta nei criteri di accettazione. Chi aveva scritto il requisito pensava "pagina di autenticazione", quindi login e registrazione. Il task però dice solo `useAuth.login`, e Claude ha implementato esattamente quello, con test che lo confermano. Il report del 29 aprile chiude T070 con "LoginPage (form + 422 errors)".

```text
TASKS.md                          Browser
------------------------------    ------------------------------
[x] T070  Pages                   Form di login: OK
    LoginPage uses                Registrazione: MANCANTE
    useAuth.login                 Link "Create account": ASSENTE

US-30: "register with email,      GAP: task chiuso, requisito
name, and password"               non coperto
```

Un `[x]` in `TASKS.md` è una dichiarazione di intento. La garanzia arriva con le prove: un commit, un test che esercita il flusso, uno screenshot del browser. Con un collega umano come con un agent, "è fatto" detto a voce non basta.

### L'audit: cos'altro è chiuso ma non fatto

Se un buco così è passato, ce ne possono essere altri. Prima di correggere la registrazione conviene un audit sistematico, sempre in Plan Mode:

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

Richiede qualche minuto, perché Claude deve leggere il piano e cercare nel codice. Ne vale la pena: alla fine sai dove sei, non dove pensi di essere.

Nel Photogallery questo audit ha un task suo, T107, e un output versionato: `docs/SPEC-COVERAGE.md`. Confronta le 42 sottosezioni di `DESIGN.md` con il codice e i test: 27 implementate, 11 parziali, 4 mancanti. Tra le mancanze ci sono file promessi dal design e mai creati, come `MarkFavoriteAction.php` (la logica è finita nel controller) o il test `BatchProgressTest.php`, e i file di deploy `.env.production.example` e `scripts/smoke-aws.php`. Non tutto va corretto subito, ma ogni voce deve diventare una decisione: si fa, si aggiorna il design, o si dichiara fuori scope.

### Il fix: un componente, due modalità

La registrazione blocca l'onboarding, quindi va per prima. La soluzione sul branch riusa `LoginPage` invece di creare un secondo componente: uno stato `mode` alterna login e registrazione.

```tsx
type AuthMode = 'login' | 'register';

export function LoginPage() {
  const navigate = useNavigate();
  const loginMutation = useLogin();
  const registerMutation = useRegister();

  const [mode, setMode] = useState<AuthMode>('login');
  // name, email, password, passwordConfirmation, errors...

  const isLogin = mode === 'login';
  const mutation = isLogin ? loginMutation : registerMutation;

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

  const toggleMode = () => {
    setMode(isLogin ? 'register' : 'login');
    setErrors({});
    setGeneralError('');
  };
```

In modalità registrazione il form mostra i campi `name` e `password_confirmation`, il bottone e il titolo prendono le stringhe da `copy.auth`, e il link in fondo chiama `toggleMode` senza cambiare pagina. I passi della correzione, nell'ordine:

1. `useRegister` in `src/hooks/useAuth.ts`, accanto a `useLogin`.
2. Lo stato `mode` in `LoginPage`.
3. I campi aggiuntivi nel JSX, visibili solo con `mode === 'register'`.
4. Gli errori 422 mostrati per campo in entrambe le modalità.
5. Il link di switch con le stringhe `noAccount`, `hasAccount`, `register`, `login`.
6. Il test manuale del flusso completo: creazione account, login automatico, redirect alla galleria.
7. Un commit che dichiara che si tratta di un buco di scope e non di una feature nuova.

L'ultimo punto conta. Un messaggio come `fix(frontend): add register mode to LoginPage (scope gap in T070)` spiega a chi legge la history perché un task chiuso è stato riaperto. La route `/register` è arrivata dopo, con T121 della Fase 14 (`feat(frontend): empty state CTA + /register route`), che la fa puntare alla stessa `LoginPage`.

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

Zero gap non lo garantisce nessun prompt. Questo però forza il controllo incrociato tra requisiti e task, che è esattamente il punto dove il flusso normale si rompe.

### Il drift tra requisiti e task

Il caso della registrazione ha un nome: drift tra requisiti e task, la distanza che si accumula tra quello che i requisiti dicono e quello che i task implementano. Nasce quando trasformi un requisito in task e fai scelte implicite su cosa includere. "Auth" può voler dire solo login, login e registrazione, oppure anche il reset della password. Se la scelta non finisce nei criteri di accettazione, il risultato copre meno di quanto il requisito intendeva.

Il drift va anche nell'altra direzione, dal codice verso i documenti. AC-F8-5 dice che `GET /photos?is_favorite=1` restituisce i preferiti dell'utente, ma `IndexPhotosRequest` e il frontend usano il parametro `favorites`. Il codice funziona, i test passano, e il criterio di accettazione descrive un'API che non esiste.

La difesa è scrivere criteri espliciti. Ogni pagina, route ed endpoint citati nel requisito compaiono per nome nel task. "Auth" da solo non dice niente; un criterio verificabile suona così: "pagina `/login` funzionante, form di registrazione raggiungibile da `/register` e dallo switch sulla pagina di login, chiamata a `POST /api/v1/auth/register` con gestione degli errori 422".

## 21.3 Foto preferite, da booleano a tabella pivot

### Il requisito

Gli utenti vogliono salvare le foto preferite e ritrovarle in una vista dedicata. Ognuno ha la sua lista. Si aggiunge e si toglie con un clic. In `REQUIREMENTS.md` è la sezione F8:

```markdown
### F8 — Favorites
- F8.1 Per-member favorites: any authenticated user can favorite any photo (many-to-many `users ↔ photos` via `favorites` pivot table)
- F8.2 One click to mark / unmark
- F8.3 Optimistic UI (heart fills before the request returns)
- F8.4 Dedicated "Favorites" view in the sidebar (shows the current user's favorites only)
- F8.5 Favorite count visible per photo (how many users favorited it)
```

Con criteri come AC-F8-1: `PUT /photos/{id}/favorite` è idempotente, due chiamate consecutive restituiscono entrambe 204 e inseriscono una sola riga nella tabella `favorites`. È una feature piccola e circoscritta, il tipo giusto da aggiungere in corsa se segui il flusso.

### L'errore di modellazione

La prima versione del design aveva la soluzione più ovvia: una colonna booleana `is_favorite` sulla tabella `photos`, con un indice composto su `is_favorite` e `created_at`. Semplice, immediata, e sbagliata appena gli utenti sono più di uno. Una colonna sulla foto rappresenta un preferito globale: o la foto è preferita per tutti, o per nessuno.

La relazione tra utenti e foto preferite è N a M: un utente ha molte foto preferite, una foto può essere preferita da molti utenti. Serve una tabella di relazione. È il momento in cui il tuo ruolo di chi supervisiona fa la differenza: se chiedi a Claude "aggiungi le foto preferite" senza altro contesto, la colonna booleana è una proposta plausibile. Prima di accettarla chiedi: "la relazione utente-foto preferita è 1 a N o N a M?". La risposta decide schema, endpoint e componenti.

### La Fase 6.5

Il correttivo è una fase inserita tra la 6 e la 7, con wave 1.5 nella tabella riassuntiva di `TASKS.md`:

```text
T090  Migration: tabella pivot favorites + drop della colonna is_favorite
T091  Relazioni favoritedBy e favoritePhotos nei modelli Photo e User
T092  PhotoController favorite/unfavorite + PhotoData (is_favorite per utente,
      favorites_count)
T093  Filament PhotoResource: favorites_count al posto del toggle
T094  Hook e componenti frontend per il pivot
T095  Test aggiornati (utente A preferisce la foto di B: compare solo nella
      lista di A)
```

Guarda gli ID. T090-T095 esistevano già: T090-T094 sono gli hook della Fase 9, T095 apre la Fase 10. Chi ha inserito la fase ha riusato la numerazione successiva a T080, e ora `TASKS.md` ha due T090 diversi. Nessun test lo rileva, ma un "fai T092" detto a Claude diventa ambiguo, e lo stesso vale per i messaggi di commit e per il template della PR che chiede di citare gli ID dei task. Quando inserisci una fase in corsa, usa ID nuovi dopo l'ultimo esistente (qui T125 in poi) oppure un prefisso dedicato. Per questo il prompt riusabile di inizio capitolo chiede ID che non collidano.

### La migrazione: crea, travasa, elimina

La colonna `is_favorite` esisteva già e conteneva dati, quindi la migrazione fa tre cose in sequenza: crea la nuova struttura, ci copia i dati esistenti, elimina la vecchia. Questa è `2026_04_30_135152_create_favorites_table.php`:

```php
public function up(): void
{
    Schema::create('favorites', function (Blueprint $table) {
        $table->foreignUuid('user_id')
            ->constrained('users')
            ->cascadeOnUpdate()
            ->cascadeOnDelete();
        $table->foreignUuid('photo_id')
            ->constrained('photos')
            ->cascadeOnUpdate()
            ->cascadeOnDelete();
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

Qualche scelta da notare. Le chiavi sono UUID (`foreignUuid`) perché tutto il progetto usa UUID v7. La chiave primaria composta impedisce i duplicati a livello di database, anche con due richieste in parallelo. `cascadeOnDelete` su entrambe le chiavi esterne fa sparire i preferiti quando sparisce la foto o l'utente. Il `hasColumn` rende la migrazione sicura su un database nuovo, dove `is_favorite` non è mai esistita: il travaso viene saltato senza errori. I preferiti esistenti vanno al proprietario della foto, l'unica attribuzione possibile per un flag globale. Il metodo `down()` fa il percorso inverso e ricrea colonna e indice.

Il pattern crea-travasa-elimina vale per qualsiasi refactoring di schema con dati da conservare.

### Relazioni ed endpoint idempotenti

Con la tabella in posizione, le relazioni nei modelli sono due righe ciascuna:

```php
// Photo
public function favoritedBy(): BelongsToMany
{
    return $this->belongsToMany(User::class, 'favorites')
        ->withPivot('created_at');
}

// User
public function favoritePhotos(): BelongsToMany
{
    return $this->belongsToMany(Photo::class, 'favorites')
        ->withPivot('created_at');
}
```

`withPivot('created_at')` invece di `withTimestamps()`, perché il pivot ha solo `created_at`.

Per l'API la tentazione è un unico endpoint di toggle con `toggle()` di Eloquent. Il progetto usa invece due endpoint idempotenti, come chiede AC-F8-1:

```php
/**
 * PUT /photos/{photo}/favorite — idempotent. Always returns 204
 * (DESIGN.md §6.2 favorite block) regardless of prior state.
 *
 * Any authenticated user can favorite any photo — no ownership check.
 */
public function favorite(Request $request, Photo $photo): Response
{
    if (! $request->user()?->tokenCan(TokenAbility::PhotosWrite->value)) {
        throw new AuthorizationException;
    }

    $request->user()->favoritePhotos()->syncWithoutDetaching([$photo->id]);

    return response()->noContent();
}
```

`unfavorite()` è identico con `detach($photo->id)` su `DELETE`. La differenza con il toggle si vede quando qualcosa va storto. Un toggle ripetuto per un retry di rete, o per un doppio clic, inverte lo stato due volte e ti lascia dove eri partito. `PUT` e `DELETE` dicono lo stato finale che vuoi, e ripeterli non cambia niente. Il controllo `tokenCan` è la regola del progetto per ogni endpoint che modifica dati: il token Sanctum deve avere l'ability `photos:write`, oltre all'autenticazione.

### Il frontend: optimistic UI

Il cuore sulla card deve cambiare al clic, prima che il server risponda (F8.3). È l'**optimistic UI**: aggiorni la cache come se la richiesta fosse già andata a buon fine e torni indietro solo se il server risponde con un errore. Questo è `useToggleFavorite` in `src/hooks/usePhotos.ts`, con l'aggiornamento della cache della singola foto omesso:

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

      // ... stesso aggiornamento sulla cache ['photo', id]

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
                  ? {
                      ...photo,
                      is_favorite: !isFavorite,
                      favorites_count: photo.favorites_count + (isFavorite ? -1 : 1),
                    }
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
      // Refetch lists to restore correct state
      queryClient.invalidateQueries({ queryKey: ['photos'] });
    },
    onSettled: (_data, _error, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['photos'] });
      queryClient.invalidateQueries({ queryKey: ['photo', id] });
    },
  });
}
```

Il dettaglio che la prima versione aveva sbagliato: la galleria è una `useInfiniteQuery`, quindi l'aggiornamento ottimistico deve toccare tutte le pagine di tutte le liste `['photos']`, e non solo la cache della singola foto. Senza questo il cuore si accendeva nel lightbox ma non nella griglia. La review della Fase 5 l'aveva segnalato come High. `mutationFn` sceglie `PUT` o `DELETE` in base allo stato attuale, quindi il toggle esiste solo nell'interfaccia, mentre l'API resta idempotente.

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
  className="pointer-events-auto relative ml-2 shrink-0 rounded-full p-2 transition-all hover:scale-110 hover:bg-white/20"
>
  <Heart
    className={`h-5 w-5 drop-shadow-sm transition-colors ${
      photo.is_favorite ? 'fill-red-500 text-red-500' : 'text-white'
    }`}
  />
  {photo.favorites_count > 0 && (
    <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white shadow-sm">
      {photo.favorites_count}
    </span>
  )}
</button>
```

`stopPropagation()` evita che il clic sul cuore apra anche il lightbox. Il badge mostra `favorites_count` (F8.5), cioè quanti utenti in tutto hanno messo la foto tra i preferiti, mentre `is_favorite` vale solo per chi guarda. La vista dedicata è la route `/favorites`, che monta `FavoritesPage` e chiama l'API con `favorites=1`. Il flusso end-to-end è coperto da `e2e/favorites.spec.ts` in Playwright.

### Quanto ci vuole, e con quanti agent

Nella prima edizione avevo cronometrato una feature di questa dimensione: poco più di due ore in tutto, contando la sezione dei requisiti, i task con i criteri, migrazione, API e test, frontend, test end-to-end, review e merge. La parte più lunga sono i requisiti, una ventina di minuti di discussione con Claude. È tempo speso bene: una modellazione sbagliata, un'API che non combacia con il frontend o un toggle non idempotente costano di più quando li scopri dopo.

Per feature così il flusso migliore è uno sviluppatore con un solo agent, in sequenza, nella stessa sessione. I task dipendono l'uno dall'altro (il frontend non si scrive prima che l'API esista), quindi non c'è niente da parallelizzare e il coordinamento tra agent sarebbe solo costo. Worktree e sessioni in background (capitolo 20) servono quando i task sono davvero indipendenti, come i track A, B e C della Wave 1. Prima di scegliere, chiediti se i task sono parallelizzabili. Se la risposta è no, un agent in sequenza è più veloce e più prevedibile.

## 21.4 PR che toccano backend e frontend

### Una PR o due

Le tre feature del capitolo attraversano lo stesso confine. Il batch ha una action, un job, la configurazione dei dischi e `DropZone`. La registrazione ha un endpoint e `LoginPage`. I preferiti hanno una migrazione, due endpoint, una risorsa Filament e un hook con optimistic UI.

L'ordine ideale è una PR per il backend (migrazione, API, test di integrazione) e, dopo il merge, una PR per il frontend (componenti, hook, test end-to-end). Ogni PR si rivede da sola e il frontend consuma un'API già stabile. Funziona quando il backend è pronto prima, o quando i due lati li seguono persone diverse.

Con Claude Code capita più spesso la PR unica, perché backend e frontend nascono nella stessa sessione e separarli dopo vuol dire riscrivere la history. Se vuoi le due PR senza quel lavoro, imposta la separazione dall'inizio: un worktree per lato, come nel capitolo 20, con il branch del frontend che parte da quello del backend.

La PR unica non è un problema finché la review la tratta per quello che è. Nel progetto ne è passata una molto grande: la PR #5, `feat/phase-2-api-layer` su `main`, squash merge di 203 file.

### Due passate di review sulla stessa PR

Una sola passata su una PR cross-stack tende a mescolare le prospettive e resta in superficie su entrambe. Meglio due passate, ciascuna con un focus dichiarato nel prompt.

La prima guarda il backend: sicurezza delle query, permessi di ogni endpoint (autenticato o pubblico, ability del token), gestione degli errori, idempotenza dei job, transazioni e dispatch, query N+1. La seconda guarda il frontend: accessibilità delle interazioni (`aria-label` sui bottoni, navigazione da tastiera), stati di caricamento ed errore, optimistic UI e rollback, peso aggiunto al bundle, resa su mobile dei componenti nuovi. Lo sforzo totale è lo stesso, la review viene più profonda. Il capitolo 22 mostra come farle con `/code-review` e con un secondo modello.

### L'ordine di deploy

Anche con una PR unica, il deploy segue sempre lo stesso ordine: prima il backend, poi il frontend.

Se arriva prima il frontend, chiama endpoint che non esistono e gli utenti vedono errori. Se arriva prima il backend, il frontend vecchio continua a funzionare perché usa solo endpoint che c'erano già, e quello nuovo, deployato subito dopo, trova le API che si aspetta. Il backend nuovo è compatibile con il frontend vecchio, il contrario no. La sequenza è quindi: deploy del backend, verifica che il frontend attuale funzioni ancora, deploy del frontend, verifica dei flussi nuovi.

Con GitHub Actions o AWS CodePipeline la sequenza diventa un workflow solo che deploya i due lati uno dopo l'altro, con un controllo in mezzo. Il deploy vero del Photogallery su AWS è il capitolo 23.

### Feature flag per le feature grandi

Per una feature grossa come il batch c'è un'opzione in più, il feature flag: deployi tutto il backend, ma la parte nuova del frontend resta nascosta dietro un flag. La vede solo il team, o una parte degli utenti. Raccogli feedback, correggi, allarghi gradualmente. Alla scala del Photogallery è eccessivo. In un'applicazione con molti utenti attivi fa la differenza tra un rilascio controllato e un incendio da spegnere di notte.

### La checklist prima del merge

Il repo ha già un `.github/PULL_REQUEST_TEMPLATE.md` che chiede gli ID dei task di `TASKS.md`, le sezioni di `DESIGN.md` toccate e il test plan (`php artisan test --compact`, `npm test -- --run`, Pint, Prettier, ESLint). Per le PR cross-stack aggiungo questa lista:

```text
Backend
[ ] Test di integrazione verdi, tutti
[ ] Nessuna query N+1 nelle rotte nuove (query log o QueryDetector)
[ ] Permessi corretti su ogni endpoint (autenticato o pubblico, ability del token)
[ ] Migrazione idempotente, provata su DB vuoto e su DB con dati

Frontend
[ ] Build TypeScript senza errori
[ ] Nessun console.error in sviluppo
[ ] Componenti accessibili (aria-label, tastiera)
[ ] Peso aggiunto al bundle accettabile (budget del progetto: 200 KB gzip)

Cross-stack
[ ] Contratto API identico tra frontend e backend (stessi campi, stessi parametri)
[ ] Errori gestiti end-to-end (401, 403, 404, 422, 500 mostrati correttamente)
[ ] Ordine di deploy scritto nella descrizione della PR
```

La riga sul contratto API è quella che avrebbe trovato il `favorites` contro `is_favorite` della sezione 21.2.

## Riepilogo

- Una feature in corsa entra dai documenti: requisiti, design e task approvati prima del codice, con il prompt riusabile della sezione 21.1 in Plan Mode.
- Per il batch su S3 servono un job idempotente (path deterministico per ogni variante), retry con attese crescenti e il dispatch dopo il commit della transazione. S3 e SQS arrivano con il `.env`, non con classi nuove.
- Un task chiuso non dimostra niente: chiedi path, test e screenshot, e chiudi ogni wave con il prompt di verifica. Il drift tra requisiti e task si previene con criteri di accettazione che nominano pagine, route ed endpoint.
- Una relazione N a M vuole una tabella pivot, e un refactoring di schema con dati segue crea, travasa, elimina. Per gli endpoint preferisci `PUT` e `DELETE` idempotenti a un toggle.
- Una fase inserita in corsa prende ID di task nuovi, mai quelli già usati.
- Le PR cross-stack si rivedono in due passate (backend, poi frontend) e si deployano sempre con il backend prima.

## Esercizio

Parti dal branch `book/cap-14-phases-complete` del repo companion e sistema il gap lasciato da T121: la route `/register` monta `LoginPage`, ma il form parte sempre in modalità login.

1. In Plan Mode, lancia il prompt riusabile della sezione 21.1 con la descrizione: "aprendo `/register` il form deve partire in modalità registrazione; aprendo `/login` in modalità login; lo switch continua a funzionare".
2. Fai aggiungere a `TASKS.md` un task con un ID nuovo (T125) e criteri che nominano entrambe le route.
3. Esegui il task con Claude, con un test Playwright in `e2e/auth.spec.ts` che apre `/register` e verifica il titolo "Create a new account".
4. Chiudi con il prompt di verifica della sezione 21.2, poi apri la PR con il template del repo e la checklist cross-stack.

L'esercizio è completo quando il nuovo test passa insieme al resto della suite (`npm run test:e2e` nel frontend) e T125 è marcato `[x]` con il commit che lo implementa. Se preferisci lavorare sul tuo progetto, scegli una feature piccola che hai in backlog, un filtro di ricerca o un export CSV, e segui gli stessi quattro passi: con migrazione, API e frontend conta un paio d'ore.
