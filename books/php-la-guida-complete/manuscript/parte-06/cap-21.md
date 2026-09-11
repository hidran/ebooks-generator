# 21. Upload degli avatar con `$_FILES` e GD

L'upload degli avatar rende lo User Management System più realistico: il form deve inviare file, PHP deve validarli, spostarli in una directory controllata, creare immagini derivate e salvare il percorso nel record utente.

Va detto subito, perché è la cosa più importante del capitolo: **l'upload di file è l'input più pericoloso che un'applicazione web possa ricevere**. Un campo di testo, nel peggiore dei casi, ti inietta SQL o HTML — e abbiamo visto come difenderti. Un file, invece, finisce *sul disco del tuo server*, e se un attaccante riesce a caricare un file `.php` in una directory servita dal web server e poi a richiamarlo via URL, quel codice **viene eseguito sul tuo server**. È il salto da "l'attaccante manipola una pagina" a "l'attaccante esegue codice arbitrario", ed è la ragione per cui ogni singola riga di questo capitolo è, in fondo, una misura difensiva. Tienilo a mente mentre leggi: qui non stiamo solo spostando immagini, stiamo chiudendo la porta più larga di un'applicazione web.

## Opzioni di upload

Le impostazioni stanno in `config.php`:

```php
'uploadDir' => 'avatar',
'mimeTypes' => ['image/jpeg', 'image/png', 'image/gif'],
'maxFileSize' => convertMaxUploadSizeToBytes(),
'thumbnailWidth' => 120,
'intermediateWidth' => 800,
```

Codice completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-21/it/parte-06/cap-21/listing-01.php)

Sorgente reale: [`config.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/config.php).

Tre decisioni di sicurezza sono già qui, dichiarate in un punto solo invece che sparse nel codice. `uploadDir` è la directory di destinazione: una sola, controllata, non "dove capita". `mimeTypes` è la **whitelist** dei tipi ammessi — di nuovo il principio del capitolo precedente, elencare ciò che è permesso invece di provare a indovinare ciò che è vietato. `maxFileSize` è il limite di dimensione, letto dalla configurazione PHP tramite `convertMaxUploadSizeToBytes()` così che il form e la validazione lato server parlino la stessa lingua e non si contraddicano. Centralizzare queste tre cose in `config.php` non è solo ordine: significa che, il giorno che vuoi aggiungere `image/webp` o alzare il limite, cambi *un* valore e tutto il resto si adegua.

## Form multipart

Il form deve dichiarare `multipart/form-data` e inviare anche `MAX_FILE_SIZE`:

```php
<form enctype="multipart/form-data" class="mt-4" action="controller/updateRecord.php" method="post">
    <input type="hidden" name="id" value="<?= $user['id'] ?>">
    <input type="hidden" name="action" value="<?= $action ?>">
```

Codice completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-21/it/parte-06/cap-21/listing-02.php)

Sorgente reale: [`view/userForm.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/view/userForm.php).

L'attributo `enctype="multipart/form-data"` è obbligatorio: senza, il browser invia solo il *nome* del file, non il suo contenuto. È il primo errore che fanno tutti quando l'upload "non funziona e non capisco perché" — il file non arriva perché il form non è dichiarato per trasportarlo. Il `multipart` spezza la richiesta in parti separate, una per ogni campo, e i byte del file viaggiano in una di queste.

```php
<input type="hidden" name="MAX_FILE_SIZE" value="<?= getConfig('maxFileSize') ?>">
<input type="file" accept="<?= implode(',', getConfig('mimeTypes')) ?>" id="avatar" class="form-control"
       value="<?= $user['avatar'] ?>" name="avatar">
```

Codice completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-21/it/parte-06/cap-21/listing-03.php)

Sorgente reale: [`view/userForm.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/view/userForm.php).

Qui ci sono due aiuti lato client, ed è fondamentale capire che sono **solo** aiuti. L'attributo `accept` fa sì che la finestra di selezione del sistema operativo mostri per default solo immagini: è comodità per l'utente onesto, niente di più. Il campo nascosto `MAX_FILE_SIZE` chiede al browser di rifiutare file troppo grandi prima ancora di iniziare l'upload, risparmiando banda. Ma entrambi vivono nel browser, e **il browser è sotto il controllo dell'attaccante**. Con un paio di clic negli strumenti per sviluppatori, o con una richiesta costruita a mano con `curl`, l'attributo `accept` sparisce e `MAX_FILE_SIZE` diventa quello che vuole lui. Sono suggerimenti per l'interfaccia, non controlli di sicurezza.

![Il form utente con il campo di caricamento dell'avatar. Il form dichiara `enctype="multipart/form-data"` e mostra la dimensione massima di upload calcolata a partire dal `php.ini`.](figures/cap-21/user-form-upload.png)

La regola, che ormai riconosci perché è la stessa di tutto il libro, è: **la validazione vera sta sul server**. Il client abbellisce l'esperienza; il server decide. Ed è esattamente quello che fa la funzione del prossimo paragrafo.

## Validare il file

`validateFileUpload()` controlla errore di upload, MIME reale e dimensione:

```php
function validateFileUpload(array $file): array
{
    $errors = [];

    if ($file['error'] !== UPLOAD_ERR_OK) {
        $errors[] = getUploadError($file['error']);
        return $errors;
    }
    $config = require 'config.php';

    $fileinfo = new finfo(FILEINFO_MIME_TYPE);
    $mimeType = $fileinfo->file($file['tmp_name']);
```

Codice completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-21/it/parte-06/cap-21/listing-04.php)

Sorgente reale: [`functions.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/functions.php).

La funzione fa tre controlli, in un ordine che non è casuale. Il primo è `$file['error'] !== UPLOAD_ERR_OK`. Quando PHP riceve un upload, popola `$_FILES['avatar']['error']` con un codice: `UPLOAD_ERR_OK` (zero) se è andato tutto bene, oppure una delle costanti che indicano un problema — file troppo grande per il limite del `php.ini`, upload interrotto a metà, cartella temporanea mancante. Controllare questo codice **per primo** è fondamentale: se l'upload è fallito, `tmp_name` può essere vuoto e ogni controllo successivo lavorerebbe sul nulla. È di nuovo il *fail fast*: se non c'è un file valido, inutile proseguire.

Il secondo controllo è il cuore della sicurezza, ed è quello dove quasi tutti sbagliano. Per sapere che tipo di file è, la funzione non guarda `$_FILES['avatar']['type']`, e non guarda nemmeno l'estensione del nome. Usa **`finfo`**, che ispeziona i **byte reali** del file per determinarne il tipo. Perché? Perché `$_FILES['type']` è una stringa che **arriva dal browser**: l'attaccante la scrive come vuole. Può prendere uno script PHP malevolo, chiamarlo `foto.jpg`, e far dichiarare al browser `Content-Type: image/jpeg`. L'estensione dice `.jpg`, il tipo dichiarato dice immagine, ma il contenuto è codice eseguibile. `finfo` non si fa ingannare: apre il file, legge i primi byte (i cosiddetti *magic number*, la firma che identifica il formato) e ti dice cos'è **davvero**. Regola da incidere nella memoria: **il tipo di un file caricato si determina dal contenuto, mai da quello che dichiara chi lo invia**.

Il terzo controllo confronta `$file['size']` con `maxFileSize`, ed è la difesa lato server contro i file enormi — quella vera, che non dipende dal `MAX_FILE_SIZE` del form che l'attaccante può ignorare. La funzione raccoglie tutti gli errori in un array e li restituisce insieme, così l'utente vede in un colpo solo tutto ciò che non va, invece di scoprirlo un problema alla volta.

## Salvare con nome sicuro

`handleAvatarUpload()` genera un nome casuale e usa l'estensione derivata dal MIME:

```php
function handleAvatarUpload(array $file, ?int $userId = null): ?string
{
    $config = require 'config.php';
    $uploadDir = $config['uploadDir'] ?? 'avatar';
    $uploadDirPath = realpath(__DIR__) . '/' . $uploadDir . '/';
    $mimeMap = [
        'image/jpeg' => 'jpg',
        'image/png' => 'png',
        'image/gif' => 'gif'
    ];
    $fileinfo = new finfo(FILEINFO_MIME_TYPE);
    $mimeType = $fileinfo->file($file['tmp_name']);
```

Codice completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-21/it/parte-06/cap-21/listing-05.php)

Sorgente reale: [`functions.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/functions.php).

Guarda come viene costruito il nome con cui il file sarà salvato, perché ogni pezzo evita un attacco. L'estensione **non** viene presa dal nome originale: viene derivata dal MIME verificato con `finfo`, attraverso `$mimeMap`. Se `finfo` dice `image/png`, l'estensione sarà `png`, punto. Il nome originale del file — che è ancora una stringa scelta dall'attaccante — non tocca il nome finale.

```php
$extension = $mimeMap[$mimeType];
$fileName = ($userId ? $userId . '_' : '') . bin2hex(random_bytes(8)) . '.' . $extension;
$res = move_uploaded_file($file['tmp_name'], $uploadDirPath . $fileName);
return $res ? $uploadDir . '/' . $fileName : null;
```

Codice completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-21/it/parte-06/cap-21/listing-06.php)

Sorgente reale: [`functions.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/functions.php).

Il nome finale è un valore casuale, `bin2hex(random_bytes(8))`, eventualmente prefissato dall'id utente. Non usare mai il nome originale inviato dall'utente non è pignoleria: risolve tre problemi in un colpo solo. Primo, la **path traversal**: un nome come `../../index.php` proverebbe a scrivere fuori dalla directory di upload, sovrascrivendo file dell'applicazione — un nome casuale non contiene percorsi. Secondo, la **sovrascrittura**: due utenti che caricano `avatar.jpg` non si calpestano, perché i nomi generati sono unici. Terzo, di nuovo l'**esecuzione**: anche se qualcosa fosse sfuggito ai controlli, il file non porta più un'estensione scelta dall'attaccante.

`move_uploaded_file()` merita una nota a parte: non è un banale sinonimo di `rename()` o `copy()`. Questa funzione **verifica** che `tmp_name` sia davvero un file arrivato tramite un upload HTTP di questa richiesta, e non un percorso qualsiasi del filesystem che un attaccante potrebbe aver iniettato in `$_FILES`. È un controllo in più, gratuito, e non c'è motivo di usare `copy()` al suo posto quando si spostano upload. Nota infine che la funzione restituisce `null` se qualcosa fallisce: chi la chiama deve gestire questo caso e non dare per scontato che un percorso ci sia sempre.

## Thumbnail e immagine intermedia

Il progetto crea due versioni dell'immagine:

```php
function createThumbnailAndIntermediate(string $avatarPath): void
{
    $config = require 'config.php';
    $fileName = basename($avatarPath);
    $uploadDirPath = getUploadDir();
    $thumbnailPath = $uploadDirPath . 'thumbnail_' . $fileName;
    $intermediatePath = $uploadDirPath . 'intermediate_' . $fileName;
    $sourcePath = $uploadDirPath . $fileName;
    $thumbnailWidth = $config['thumbnailWidth'] ?? 120;
    $intermediateWidth = $config['intermediateWidth'] ?? 800;
```

Codice completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-21/it/parte-06/cap-21/listing-07.php)

Sorgente reale: [`functions.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/functions.php).

Creare una thumbnail (120px per l'elenco) e una versione intermedia (800px per la visualizzazione) è anzitutto una scelta di buon senso: servire l'immagine originale a piena risoluzione dentro una tabella di elenco spreca banda e rallenta la pagina. Ma c'è un secondo effetto, meno ovvio e prezioso dal punto di vista della sicurezza. La funzione `resizeImage()`, che usa la libreria **GD**, legge l'immagine originale e ne **ridisegna una nuova** da zero. Questo processo, di fatto, ricodifica i pixel e scarta tutto ciò che non è dato-immagine: eventuali payload nascosti nei metadati o codice appeso in coda a un finto JPEG non sopravvivono alla ri-generazione. Passare un upload attraverso GD è una forma di **sanitizzazione**: quello che esce è un'immagine pulita, costruita da te, non il file che ti è arrivato. `basename()` sul percorso è un ulteriore piccolo presidio: rimuove qualsiasi componente di directory, così nessun nome può far scrivere le versioni derivate fuori dalla cartella prevista.

## Cancellare immagini obsolete

Quando un utente viene eliminato o cambia avatar, anche i file derivati vanno rimossi:

```php
function deleteUserImages(string $avatarPath): void
{
    if (!$avatarPath) {
        return;
    }
    $uploadDir = getUploadDir();
    $fileName = basename($avatarPath);
    $avatarFile = $uploadDir . $fileName;
    $thumbnail = $uploadDir . 'thumbnail_' . $fileName;
    $intermediate = $uploadDir . 'intermediate_' . $fileName;
```

Codice completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-21/it/parte-06/cap-21/listing-08.php)

Sorgente reale: [`functions.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/functions.php).

Questo è il pezzo che, in un tutorial frettoloso, non ci sarebbe. Un upload sembra "finito" quando il file è salvato, ma non lo è: hai creato **tre** file (originale, thumbnail, intermedia) e li hai collegati a un record. Il giorno che l'utente cambia avatar, o viene cancellato, quei tre file vanno rimossi — altrimenti la cartella di upload si riempie all'infinito di immagini orfane che nessuno serve più, occupano spazio e, nel caso di dati personali, restano in giro quando non dovrebbero. Pensare al **ciclo di vita** completo di un file — creazione *e* distruzione — è ciò che distingue chi ha scritto un upload in produzione da chi ne ha copiato uno da un tutorial. `basename()` torna anche qui, con la stessa funzione difensiva di prima.

## In sintesi

L'upload di file è l'input più rischioso di un'applicazione web, e questo capitolo ha messo in fila le difese che lo rendono sicuro. La **configurazione centralizzata** dichiara in un punto solo directory, tipi ammessi e limite di dimensione. Il **form multipart** trasporta i byte, ma i suoi aiuti lato client (`accept`, `MAX_FILE_SIZE`) sono comodità, non sicurezza. La **validazione lato server** controlla il codice di errore, la dimensione e — soprattutto — il MIME reale con `finfo`, mai il tipo dichiarato dal browser. Il **salvataggio** usa un nome casuale con estensione derivata dal MIME verificato, e `move_uploaded_file()` per accertarsi che sia un upload autentico. Le **immagini derivate** create con GD ridimensionano e, come effetto collaterale, sanificano il contenuto. La **cancellazione** chiude il ciclo di vita, rimuovendo i file quando il record cambia o sparisce.

Il filo, ancora una volta, è quello di tutta la Parte VI: non fidarti mai dell'input, e determina la natura di un dato dal suo contenuto, non da ciò che l'utente dichiara. Con l'upload la posta in gioco è solo più alta, perché qui un errore non manipola una pagina — mette codice sul tuo server.
