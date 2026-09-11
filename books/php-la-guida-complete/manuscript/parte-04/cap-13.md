# 13. Le superglobali

Con questo capitolo entriamo nel vivo di PHP come linguaggio per il web. Fino a qui abbiamo scritto script che elaborano dati che noi stessi mettevamo nel codice; ora vediamo come PHP riceve i dati che arrivano **dall'esterno**: i parametri di una richiesta, i valori di un form, le informazioni sul server, i file caricati da un utente, i dati di sessione. Tutto questo ci viene consegnato attraverso un gruppo speciale di array che PHP popola automaticamente per noi: le **superglobali**.

Si chiamano così perché sono variabili "super globali": sono accessibili **in qualunque punto** dello script — dentro una funzione, dentro un metodo, in qualsiasi scope — senza bisogno di dichiararle con `global` e senza passarle come argomento. PHP le crea e le riempie prima ancora che il nostro codice cominci a girare. Le riconosci subito perché hanno tutte un nome che inizia con `$_` (con l'unica eccezione storica di `$GLOBALS`): `$GLOBALS`, `$_SERVER`, `$_GET`, `$_POST`, `$_COOKIE`, `$_REQUEST`, `$_FILES`, `$_SESSION`, più `$_ENV`. In questo capitolo le vediamo una a una, con esempi concreti, perché sono la porta d'ingresso di qualunque applicazione web e le useremo in ogni progetto del libro.

## $GLOBALS: accedere alle variabili globali

Cominciamo da `$GLOBALS`, la superglobale meno usata ma la più antica: esiste in PHP da sempre. `$GLOBALS` è una specie di **calderone** dentro cui finiscono tutte le variabili che vivono nello **scope globale** dello script, cioè tutte quelle dichiarate al di fuori di una funzione. Dentro `$GLOBALS` troviamo anche le altre superglobali (`$_GET`, `$_POST`, `$_COOKIE`, `$_SERVER`, `$_FILES`) e ogni variabile globale che abbiamo definito noi.

La caratteristica interessante è che `$GLOBALS` è accessibile ovunque, anche dentro una funzione, senza fare alcun import. Verifichiamolo. Dichiariamo una variabile nello scope globale e proviamo a leggere `$GLOBALS` dall'interno di una funzione:

```php
<?php

$testGlobal = 'Questa è una variabile globale';

function test()
{
    var_dump($GLOBALS);
}

test();
```

Codice completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/it/parte-04/cap-13/listing-01.php)


Lanciando lo script vediamo che `$GLOBALS` è un array le cui chiavi sono i **nomi delle variabili globali** (senza il segno del dollaro) e i nomi delle superglobali. In fondo all'elenco compare anche `testGlobal`: la chiave è esattamente il nome della variabile, `testGlobal`, senza il `$`, e il suo valore è la stringa che le abbiamo assegnato.

Se ci interessa una singola variabile globale, basta usare il suo nome come chiave dell'array:

```php
function test()
{
    echo $GLOBALS['testGlobal'];
}
```

Codice completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/it/parte-04/cap-13/listing-02.php)


All'interno della funzione abbiamo così accesso alla variabile globale, pur non avendola né dichiarata lì né ricevuta come argomento.

### Il costrutto global

Esiste un secondo modo per accedere a una variabile globale dall'interno di una funzione: il costrutto **`global`**. Scrivendo `global $testGlobal;` stiamo dicendo a PHP "importa nella funzione la variabile globale `$testGlobal`":

```php
function test()
{
    global $testGlobal;
    echo $testGlobal;
}
```

Codice completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/it/parte-04/cap-13/listing-03.php)


Il risultato è identico. Personalmente preferisco la forma `$GLOBALS['testGlobal']`, che rende esplicito che stiamo attingendo dall'array globale, ma entrambe funzionano.

C'è un caso in cui `$GLOBALS` è particolarmente utile: quando dentro la funzione esiste già una **variabile locale con lo stesso nome** di una variabile globale. In quella situazione, il nome nudo si riferisce alla variabile locale, mentre `$GLOBALS['...']` continua a puntare a quella globale, senza conflitti:

```php
function test()
{
    $testGlobal = 'test funzione';

    echo $testGlobal;              // "test funzione"  → variabile locale
    echo $GLOBALS['testGlobal'];   // "Questa è una variabile globale" → globale
}
```

Codice completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/it/parte-04/cap-13/listing-04.php)


Come vedi, la variabile locale e quella globale convivono senza sovrascriversi.

### Un consiglio dall'esperienza

Detto questo, ti do un consiglio che vale come regola generale: **evita le variabili globali**. Sono pericolose perché possono essere sovrascritte in un altro punto del programma senza che tu te ne accorga, e nelle applicazioni grandi diventano una fonte inesauribile di bug difficili da rintracciare. Se hai bisogno di condividere dei valori a livello globale, ci sono alternative molto più pulite: includere un file che **ritorna un array** di costanti o di configurazione (il pattern che abbiamo visto nel Capitolo 15), oppure una classe con proprietà e metodi statici. Sono modi per non "contaminare" l'ambiente globale.

Un'ultima nota. `$GLOBALS` contiene anche le altre superglobali, quindi potresti tecnicamente leggere `$GLOBALS['_POST']` invece di `$_POST`:

```php
print_r($GLOBALS['_POST']);
```

Codice completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/it/parte-04/cap-13/listing-05.php)


Ma non c'è alcun motivo per farlo: `$_POST` è già accessibile ovunque per conto suo. Quindi `$GLOBALS` lo useremo, se mai, soltanto per le variabili dello scope globale, mentre per le superglobali useremo sempre il loro nome diretto.

## $_SERVER: informazioni su server e richiesta

`$_SERVER` è un array che PHP riempie con una gran quantità di informazioni sul **server** e sulla **richiesta HTTP** in corso. Alcune di queste informazioni riguardano la macchina su cui gira il server e possono cambiare da un server all'altro; altre riguardano la singola richiesta che il browser ha appena fatto. Il modo migliore per farsi un'idea di che cosa contiene è stamparlo:

```php
<?php

var_dump($_SERVER);
```

Codice completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/it/parte-04/cap-13/listing-06.php)


Tra le tante voci, queste sono quelle che si usano più spesso:

- **`REMOTE_ADDR`** — l'indirizzo IP dell'utente che si è collegato. Utilissimo per tracciare le visite, registrare da dove arrivano gli utenti, applicare limitazioni.
- **`HTTP_USER_AGENT`** — la stringa che identifica il browser e il sistema dell'utente.
- **`REQUEST_METHOD`** — il metodo HTTP della richiesta: `GET`, `POST`, `PUT`, ecc.
- **`QUERY_STRING`** — la stringa dei parametri passati via URL, così come è stata inviata.
- **`REQUEST_URI`** — l'URL richiesto a partire dalla document root, parametri compresi.
- **`SCRIPT_FILENAME`** — il percorso completo del file che stiamo eseguendo.
- **`PHP_SELF`** — il percorso dello script in esecuzione relativo alla document root.
- **`DOCUMENT_ROOT`** — la directory radice del sito, impostata nel web server (per esempio la cartella `htdocs` di Apache).
- **`SERVER_PROTOCOL`** — il protocollo e la versione, per esempio `HTTP/1.1`.
- **`SERVER_ADDR`** e **`SERVER_NAME`** — l'indirizzo IP e il nome del nostro server.
- **`SERVER_SOFTWARE`** — il software e la versione del web server.

Per leggere una singola voce si accede all'array come a un array normale, indicando la chiave. Per esempio, per ottenere l'IP dell'utente:

```php
echo $_SERVER['REMOTE_ADDR'];
```

Codice completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/it/parte-04/cap-13/listing-07.php)


Molte di queste variabili derivano dagli **header** che il browser invia al server a ogni richiesta. Se apri gli strumenti per sviluppatori del browser (tasto destro, *Ispeziona*), vai alla scheda *Rete* e ricarichi la pagina, puoi vedere gli header della richiesta e della risposta: il metodo, lo stato (`200`), il dominio, l'user agent, la lingua accettata, la codifica, e così via. PHP prende molte di queste informazioni e le mette a nostra disposizione dentro `$_SERVER`.

### Rilevare il browser dall'user agent (e perché è inaffidabile)

Un uso classico di `HTTP_USER_AGENT` è capire con quale browser l'utente ci sta visitando, per esempio per raccogliere qualche statistica:

```php
echo $_SERVER['HTTP_USER_AGENT'];
```

Codice completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/it/parte-04/cap-13/listing-08.php)


Il valore è una stringa lunga che inizia tipicamente con `Mozilla/5.0` e contiene "indizi" sul browser: la presenza di `Gecko` fa pensare a Firefox, `Trident` a vecchie versioni di Internet Explorer, e così via. Con un'espressione regolare potremmo estrarre queste informazioni. Attenzione però: negli anni i browser hanno cambiato più volte il modo in cui compongono questa stringa — Internet Explorer, per esempio, ha smesso di scriversi in un certo modo e ha aggiunto `like Gecko` — quindi affidarsi all'user agent per il rilevamento del browser è diventato via via meno affidabile. Oggi esistono librerie apposite e, spesso, è più solido fare questi controlli lato client. Ma per usi statistici o di logging, `HTTP_USER_AGENT` resta comodo: possiamo salvarlo su database insieme all'IP per sapere chi visita le nostre pagine e con quale strumento.

## $_GET: i dati della query string

Passiamo alle due superglobali che useremo di più: `$_GET` e `$_POST`, i due canali attraverso cui un utente ci manda dei dati. Cominciamo da **`$_GET`**.

`$_GET` contiene tutti i parametri che vengono passati via **query string**, cioè quella parte di URL che segue il punto interrogativo. Se nel capitolo precedente abbiamo visto la `QUERY_STRING` grezza dentro `$_SERVER`, qui la ritroviamo già sezionata: ogni parametro diventa una chiave dell'array e il suo valore diventa il valore associato. Vediamolo subito. Prendiamo un URL con due parametri:

```text
index.php?username=John&lastname=Smith
```

Codice completo: [listing-09.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/it/parte-04/cap-13/listing-09.txt)


e stampiamo `$_GET`:

```php
<?php

var_dump($_GET);
```

Codice completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/it/parte-04/cap-13/listing-10.php)


Otteniamo un array con due elementi: la chiave `username` con valore `John` e la chiave `lastname` con valore `Smith`. Le chiavi sono i nomi dei parametri, i valori sono quelli che abbiamo passato nell'URL.

Una cosa a cui prestare attenzione: se nell'URL passiamo caratteri "particolari", come lettere accentate, il browser normalmente li **codifica** (per esempio uno spazio diventa `%20`). Lato PHP, se necessario, possiamo decodificare questi valori con `urldecode()`. È un aspetto di cui tenere conto quando i dati arrivano dal web.

### Mostrare tutti gli errori durante lo sviluppo

Prima di andare avanti, una buona pratica: **durante lo sviluppo, mostra sempre tutti gli errori di PHP**. Così ti accorgi immediatamente se stai leggendo una chiave che non esiste. Puoi impostarlo nel file `php.ini`, oppure direttamente nello script con `ini_set()` e `error_reporting()`:

```php
<?php

ini_set('display_errors', 1);
error_reporting(E_ALL);
```

Codice completo: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/it/parte-04/cap-13/listing-11.php)


Con `display_errors` a `1` PHP mostra gli errori a video, e con `error_reporting(E_ALL)` gli chiediamo di segnalarli tutti, warning e notice compresi.

### Verificare se un parametro esiste

Ed ecco perché serve avere gli errori attivi. Le superglobali `$_GET` e `$_POST` **esistono sempre**, anche quando sono vuote: fare `var_dump($_GET)` senza parametri nell'URL non dà errore, mostra semplicemente un array vuoto. Il problema nasce quando proviamo a leggere una **chiave** che non è stata passata: PHP emette un warning ("undefined array key"). Perciò, prima di leggere un valore da un array — qualunque array, non solo le superglobali — dobbiamo sempre verificare che la chiave esista. Abbiamo tre strumenti, con sfumature diverse.

Il primo è **`isset()`**, che ci dice se la variabile (o la chiave) è impostata:

```php
if (isset($_GET['username'])) {
    var_dump($_GET['username']);
}
```

Codice completo: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/it/parte-04/cap-13/listing-12.php)


Attenzione a una sottigliezza: `isset()` verifica che la variabile sia impostata, non che abbia un valore "pieno". Una **stringa vuota** è considerata impostata (`isset()` ritorna `true`), mentre un valore `null` è considerato **non** impostato: per PHP una variabile è impostata solo se è stata dichiarata e il suo valore non è `null`.

Il secondo è **`empty()`**, che verifica se il valore è "vuoto". Va usato con cautela, perché per PHP sono considerati vuoti anche lo `0` e la stringa `"0"`: se ci aspettiamo che un parametro possa legittimamente valere zero, `empty()` ci trarrebbe in inganno.

Il terzo è la funzione **`array_key_exists()`**, che verifica esclusivamente la presenza della **chiave**, indipendentemente dal valore:

```php
if (array_key_exists('username', $_GET)) {
    var_dump($_GET['username']);
}
```

Codice completo: [listing-13.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/it/parte-04/cap-13/listing-13.php)


La differenza pratica con `isset()` sta proprio nel `null`: se un valore è stato impostato a `null`, `isset()` lo considera assente, mentre `array_key_exists()` conferma che la chiave c'è. Quale usare dipende da cosa vuoi: se per te un valore `null` non ha senso e va trattato come "assente", `isset()` va benissimo; se invece devi sapere con certezza se la chiave esiste — tipico quando lavori con record che arrivano dal database e vuoi sapere se una certa colonna è presente — allora `array_key_exists()` è la scelta giusta. Ripeto: tutto questo vale per qualsiasi array di PHP, non solo per le superglobali.

### Passare dati via GET: URL, link e form

Ci sono più modi in cui i parametri finiscono nella query string, e quindi in `$_GET`:

**Scrivendoli a mano nell'URL**, come abbiamo fatto negli esempi sopra.

**Con un form che usa il metodo GET.** Prepariamo un semplice form HTML (qui uso qualche classe di Bootstrap solo per l'aspetto) che punta alla stessa pagina:

```html
<form action="index.php" method="get">
    <input type="text" name="username" id="username" placeholder="Nome">
    <input type="text" name="lastname" id="lastname" placeholder="Cognome">
    <input type="reset" value="Reset">
    <button type="submit">Invia</button>
</form>
```

Codice completo: [listing-14.html](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/it/parte-04/cap-13/listing-14.html)


Il campo `input` di tipo `reset` è un piccolo trucco che azzera il form con un solo click. Compilando i campi e inviando, i valori compaiono nella query string (`?username=...&lastname=...`) e li ritroviamo in `$_GET`: la chiave di ogni valore è l'attributo `name` dell'input. Ecco perché il `name` di ogni campo è così importante: è quello, non l'`id`, che determina la chiave dentro `$_GET`.

**Con un semplice link.** Anche un tag `<a>` con parametri nell'URL invia dati via GET quando ci clicchi sopra:

```html
<a href="index.php?username=test&lastname=testLastname" class="btn btn-danger">Test</a>
```

Codice completo: [listing-15.html](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/it/parte-04/cap-13/listing-15.html)


Cliccando, i parametri `test` e `testLastname` arrivano alla pagina esattamente come se li avessimo scritti a mano.

Proprio perché è così facile costruire una query string — a mano, con un link, o con un client HTTP qualunque — **dei dati che arrivano via GET non possiamo fidarci ciecamente**. Non abbiamo alcuna garanzia che sia stato davvero l'utente a inviarli tramite il nostro form: qualcuno potrebbe manipolare l'URL o simulare la richiesta. È un principio di sicurezza da tenere sempre presente, e lo riprenderemo nei progetti.

## $_POST: i dati inviati via POST

Vediamo ora la differenza con il metodo **POST** e come i dati inviati in questo modo vengano mappati nella superglobale **`$_POST`**.

Se stampiamo `$_POST` senza aver inviato nulla via POST, l'array è vuoto: nessuna variabile è arrivata per questa via. Per mandare dati via POST basta un form con `method="post"`. È sufficiente cambiare l'attributo `method` del form che avevamo prima:

```html
<form action="index.php" method="post">
    <input type="text" name="username" id="username" placeholder="Nome">
    <input type="text" name="lastname" id="lastname" placeholder="Cognome">
    <button type="submit">Invia</button>
</form>
```

Codice completo: [listing-16.html](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/it/parte-04/cap-13/listing-16.html)


La differenza più evidente è che con POST le variabili **non viaggiano in chiaro nell'URL**: la query string resta pulita, e i valori vengono trasmessi nel corpo della richiesta. Inviando il form con `Hidran` e `Arias`, `$_GET` resta vuoto mentre `$_POST` contiene `username` e `lastname` con i valori inseriti.

`$_GET` e `$_POST` sono **due array separati**. Possiamo perfino inviare gli stessi nomi di parametro per entrambe le vie contemporaneamente — per esempio mettendo dei parametri nell'`action` del form (che viaggiano in GET) e altri nei campi (che viaggiano in POST) — e ciascun valore finirà nel proprio array, senza mescolarsi. Se `username` arriva sia via GET sia via POST, lo troveremo in `$_GET['username']` con il valore della query string e in `$_POST['username']` con il valore del form: non c'è sovrascrittura tra i due.

Per leggere un valore, valgono le stesse verifiche viste prima. Se vogliamo leggere lo username inviato via POST, e solo quello, controlliamo la chiave e lo leggiamo:

```php
if (isset($_POST['username'])) {
    echo $_POST['username'];
}
```

Codice completo: [listing-17.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/it/parte-04/cap-13/listing-17.php)


La regola pratica è questa: **leggi le variabili dallo stesso canale con cui le hai inviate**. Se hai deciso che il tuo form è POST, leggi da `$_POST`; se è GET, leggi da `$_GET`. Così eviti che qualcuno inietti variabili "sporche" dall'altro canale e ti sovrascriva i dati.

## Riassunto: $_GET, $_POST e $_COOKIE

Facciamo il punto sui tre canali attraverso cui i dati di una richiesta arrivano a PHP.

- **`$_GET`** contiene le variabili passate via **query string**: scritte a mano nell'URL, inviate da un form con metodo GET, contenute in un link o messe nell'`action` di un form.
- **`$_POST`** contiene le variabili inviate via **POST**: da un form con metodo POST, oppure da un client HTTP che fa una richiesta POST al nostro server.
- **`$_COOKIE`** contiene i **cookie** che il browser ci rimanda a ogni richiesta. Un cookie lo impostiamo con la funzione `setcookie()`, indicandone il nome, il valore, il tempo di vita (espresso in secondi dall'epoca di Unix), la cartella o il dominio per cui è valido, e altri parametri. Una volta impostato, dalla ricarica successiva della pagina in poi il browser ce lo rispedisce indietro, e noi lo leggiamo dentro `$_COOKIE`. Ai cookie dedichiamo per intero il prossimo capitolo, quindi qui ci limitiamo a inquadrarli nel gruppo delle superglobali.

Un dettaglio importante sui cookie, che spiega perché li isoliamo dal resto: la prima volta che imposti un cookie, esso **non** è ancora in `$_COOKIE`. `$_COOKIE` contiene ciò che il browser sta inviando **adesso**, e in quel momento il browser non conosce ancora il cookie che gli stiamo mandando per la prima volta. Lo vedremo popolato solo dalla richiesta successiva. Su questa distinzione torneremo nel Capitolo 14.

## $_REQUEST e conclusione

C'è infine una superglobale che unisce i tre canali appena visti: **`$_REQUEST`**. `$_REQUEST` è un array che **fonde** (fa il merge di) `$_GET`, `$_POST` e, a seconda della configurazione, `$_COOKIE`. Se la stessa chiave arriva da più canali, uno sovrascrive l'altro secondo un ordine preciso.

Vediamolo con un esempio. Supponiamo di passare `username=Higuain` e `lastname=Smith` via query string, e contemporaneamente inviare un form via POST con `username=Hidran` e `lastname=Arias`:

```php
var_dump($_GET);      // Higuain, Smith
var_dump($_POST);     // Hidran, Arias
var_dump($_REQUEST);  // Hidran, Arias  ← vince il POST
```

Codice completo: [listing-18.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/it/parte-04/cap-13/listing-18.php)


In `$_REQUEST` troviamo i valori del POST: nell'ordine predefinito, il POST arriva dopo il GET e quindi lo sovrascrive.

### Chi decide l'ordine: request_order

L'ordine con cui `$_REQUEST` viene riempito non è scolpito nella pietra: dipende dall'impostazione **`request_order`** (e in secondo luogo da `variables_order`) nel file `php.ini`. Nelle versioni recenti di PHP il valore predefinito è `GP`, cioè "prima GET, poi POST": il POST ha la priorità e i cookie **non** vengono inclusi. Personalmente è l'impostazione che preferisco: non mi piace avere anche i cookie dentro `$_REQUEST`. Se però modificassimo `request_order` in, per esempio, `GPC`, allora anche i cookie entrerebbero nel merge e, essendo ultimi, potrebbero sovrascrivere GET e POST. Dopo aver toccato `php.ini` bisogna riavviare il web server perché la nuova impostazione venga caricata.

### Perché diffidare di $_REQUEST

Proprio perché il comportamento di `$_REQUEST` dipende dalla configurazione del server, **non abituarti a leggere sempre da `$_REQUEST`** fregandotene di sapere se il dato è arrivato via GET o via POST. Guarda questo caso: se non invii il form ma i valori sono presenti solo via GET, e nel merge il POST (vuoto) ha comunque "vinto", potresti ritrovarti in `$_REQUEST` dei valori vuoti pur avendo dati validi in `$_GET`. Il messaggio è: **sii specifico su che cosa vuoi da ogni canale**. Leggere da `$_REQUEST` è comodo, ma ti espone a sorprese e a piccole falle di sicurezza; leggere dal canale giusto è quasi sempre la scelta migliore.

Chiudiamo con l'osservazione da cui siamo partiti: tutte queste superglobali sono davvero *super* perché sono accessibili ovunque, anche dentro una funzione, senza dover scrivere `global` davanti a nulla. Ci basta usare il loro nome e, se serve, la chiave:

```php
function test()
{
    var_dump($_GET, $_POST, $_SERVER);
}

test(); // funziona: le superglobali sono visibili anche qui dentro
```

Codice completo: [listing-19.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/it/parte-04/cap-13/listing-19.php)


Ci restano due superglobali particolarmente importanti, che meritano una trattazione a parte: `$_FILES`, per gestire l'upload dei file, e `$_SESSION`, per conservare dati tra una pagina e l'altra.

## $_FILES: l'upload dei file

La superglobale **`$_FILES`** ci dà accesso ai file che l'utente ha caricato attraverso un form. Ci abbiamo accesso, cioè, soltanto quando è avvenuto un **upload**.

Per caricare un file servono due condizioni lato HTML. La prima è un campo `input` di tipo `file`. La seconda, spesso dimenticata, è che il form abbia l'attributo **`enctype="multipart/form-data"`**: senza di esso il file non viene trasmesso. Questo tipo di codifica dice al browser di inviare la richiesta in "parti multiple", una per i normali campi chiave-valore (come `username`) e una per il contenuto binario del file. Ecco un form minimo:

```html
<form action="index.php" method="post" enctype="multipart/form-data">
    <input type="text" name="username" placeholder="Nome">
    <input type="file" name="avatar" id="avatar">
    <button type="submit">Invia</button>
</form>
```

Codice completo: [listing-20.html](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/it/parte-04/cap-13/listing-20.html)


### La struttura dell'array $_FILES

Prima di caricare qualcosa, `$_FILES` è vuoto. Dopo l'invio del form con un file, contiene un array la cui chiave è il **nome del campo** (l'attributo `name` dell'input, qui `avatar`), e il cui valore è a sua volta un array con le informazioni sul file. Verifichiamolo:

```php
var_dump($_FILES);
```

Codice completo: [listing-21.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/it/parte-04/cap-13/listing-21.php)


Per ogni file caricato troviamo queste chiavi:

- **`name`** — il nome originale del file così com'era sul computer dell'utente (per esempio `foto.jpg`).
- **`type`** — il MIME type dichiarato dal browser (per esempio `image/jpeg`).
- **`tmp_name`** — il percorso del file **temporaneo** in cui il server ha salvato l'upload (nella cartella temp del sistema). Da qui dovremo spostarlo verso la sua destinazione definitiva.
- **`error`** — il codice di errore dell'upload: vale `0` se è andato tutto bene.
- **`size`** — la dimensione del file in byte.

Se nel form ci fossero due campi file — per esempio `avatar` e `avatar2` — allora `$_FILES` sarebbe un **array di array**: una chiave per ciascun campo, e sotto ciascuna le cinque proprietà appena elencate.

### Salvare il file caricato in modo sicuro

Vediamo come usare questi dati per copiare il file dalla cartella temporanea a una cartella nostra. Supponiamo di avere, nella stessa directory dello script, una cartella `images` scrivibile. Cicliamo su `$_FILES` e, per ogni file, facciamo due controlli fondamentali prima di spostarlo:

```php
<?php

if (!empty($_FILES)) {
    foreach ($_FILES as $key => $file) {

        // 1. è davvero un file caricato via HTTP? (sicurezza)
        // 2. l'upload è andato a buon fine?
        if (is_uploaded_file($file['tmp_name']) && $file['error'] === UPLOAD_ERR_OK) {

            $dir = __DIR__ . '/images';
            $fileName = basename($file['name']);
            $destination = $dir . '/' . $fileName;

            if (move_uploaded_file($file['tmp_name'], $destination)) {
                echo "Il file {$fileName} è stato caricato correttamente.<br>";
            }
        }
    }
}
```

Codice completo: [listing-22.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/it/parte-04/cap-13/listing-22.php)


Analizziamo i passaggi chiave:

- **`is_uploaded_file()`** riceve il percorso temporaneo (`tmp_name`) e ritorna `true` solo se quel file è stato davvero caricato tramite una richiesta HTTP POST. È una verifica di sicurezza: ci protegge da chi provasse a farci elaborare un file arbitrario del server spacciandolo per un upload.
- **`$file['error'] === UPLOAD_ERR_OK`** verifica che non ci siano stati errori. `UPLOAD_ERR_OK` è una costante di PHP che vale `0`; potremmo anche scrivere `$file['error'] === 0`, ma usare la costante rende il codice più leggibile.
- **`__DIR__`** è una costante magica che contiene il percorso assoluto della cartella in cui si trova lo script corrente (l'equivalente di `dirname(__FILE__)`). Costruire la destinazione a partire da `__DIR__` è più robusto che scrivere un percorso relativo: lo script funziona qualunque sia la cartella corrente del processo. Su Linux ricordati che questa cartella deve avere i **permessi di scrittura** per l'utente con cui gira PHP, altrimenti lo spostamento fallisce.
- **`basename()`** applicata a `$file['name']` estrae il solo nome del file, scartando eventuali percorsi. È importante usare `name` (il nome originale) e non `tmp_name` per il nome di destinazione: se usassimo il percorso temporaneo, ci ritroveremmo un nome incomprensibile.
- **`move_uploaded_file()`** sposta il file dalla posizione temporanea alla destinazione e ritorna `true` se ci riesce. È la funzione dedicata proprio a questo scopo e va preferita a una semplice `copy()`, perché verifica anch'essa che il file provenga da un upload legittimo.

### Due accortezze importanti

Primo: **non fidarti mai del campo `type`**. Il MIME type dichiarato nel form può essere falsificato da chi confeziona la richiesta. Se devi accertarti che un file sia davvero un'immagine (o un PDF, un documento Excel, ecc.), verifica il tipo reale lato PHP, analizzando il contenuto del file con funzioni come `finfo` o `mime_content_type()`, non basandoti su `$file['type']`.

Secondo: il **nome** con cui salvi il file. Puoi mantenere il nome originale, ma spesso conviene generarne uno univoco — per esempio anteponendo un timestamp — per evitare che due utenti che caricano file con lo stesso nome si sovrascrivano a vicenda. Una volta salvato il file, tipicamente ne registri il nome sul database. E se stai gestendo immagini, puoi anche ridimensionarle con le funzioni della libreria GD (come `imagecreatefromjpeg()`), o affidarti a una libreria dedicata.

Per gestire più file con un unico campo, infine, puoi usare la sintassi `name="avatar[]"` sull'input e l'attributo HTML5 `multiple`: in quel caso `$_FILES` raccoglie tutti i file sotto un'unica chiave, come array. La logica di controllo e spostamento resta identica. Se già usi un framework o una libreria che gestisce gli upload per te, ora sai comunque che cosa succede "alla base": tutto ruota attorno a questo array globale, `$_FILES`.

## $_SESSION: memorizzare dati tra le pagine

Arriviamo all'ultima superglobale, e a uno dei meccanismi più importanti di PHP per il web: la **sessione**, gestita attraverso `$_SESSION`.

Una sessione è un ambiente in cui possiamo **immagazzinare dati che sopravvivono da una pagina all'altra**, per tutta la "sessione di lavoro" dell'utente. Nel caso classico, in cui la sessione è legata a un cookie, i dati restano disponibili finché l'utente tiene il browser aperto; alla chiusura del browser la sessione svanisce. È qui la differenza con i cookie veri e propri, che invece — come vedremo nel prossimo capitolo — possono persistere anche dopo la chiusura del browser. Per identificare a quale utente appartiene una sessione, PHP usa a sua volta un cookie: alla prima visita genera un identificativo casuale, lo invia al browser, e a ogni richiesta successiva il browser lo rimanda, permettendo a PHP di ricollegare quella richiesta ai dati della sessione giusta.

### Avviare la sessione con session_start()

Se stampiamo `$_SESSION` senza aver avviato nulla, non c'è alcuna sessione attiva e l'array non esiste. Il primo passo, sempre, è avviare la sessione con **`session_start()`**:

```php
<?php

session_start();

$_SESSION['user_id'] = 4;
$_SESSION['logged'] = 1;
```

Codice completo: [listing-23.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/it/parte-04/cap-13/listing-23.php)


Con `session_start()` la sessione si apre. Da questo momento possiamo scrivere valori dentro `$_SESSION` come in un normale array: nell'esempio memorizziamo l'ID di un utente e un flag che indica che è loggato.

Se ora andiamo a guardare, negli strumenti per sviluppatori del browser, la scheda *Rete* e gli header della richiesta, tra i cookie ne troviamo uno chiamato **`PHPSESSID`**: è l'identificativo di sessione che PHP ha creato per noi. Da qui in poi il browser lo invierà a ogni richiesta, e qualunque script del nostro sito che condivida quel cookie avrà accesso allo stesso `$_SESSION`.

### Leggere la sessione in un'altra pagina

Ed è proprio questo il punto: i dati messi in sessione su una pagina sono leggibili da un'altra pagina. C'è però una condizione: **anche la pagina che legge deve chiamare `session_start()`**. Se in una seconda pagina proviamo a leggere `$_SESSION['user_id']` senza avviare la sessione, otteniamo un errore di chiave indefinita. Aggiungendo `session_start()` in cima, invece, ritroviamo tutti i valori:

```php
<?php

session_start();

var_dump($_SESSION['user_id']); // 4
```

Codice completo: [listing-24.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/it/parte-04/cap-13/listing-24.php)


Così, qualunque pagina che condivide il cookie di sessione (perché sta nello stesso dominio e cartella) ha accesso alle variabili di sessione. Approfondiremo la gestione completa e la **sicurezza** delle sessioni in un capitolo dedicato, all'interno dei progetti pratici; qui ci concentriamo sulla superglobale e sul suo funzionamento di base.

### session_start() prima di ogni output

C'è un vincolo tecnico da rispettare. Quando avviamo la sessione, PHP invia al browser il cookie `PHPSESSID`, e i cookie viaggiano negli **header**, che devono essere spediti **prima** di qualsiasi contenuto HTML. Perciò `session_start()` non può essere preceduto da alcun output: se prima di esso stampiamo anche solo un tag `<h1>`, o lasciamo uno spazio prima dell'apertura `<?php`, rischiamo il classico errore *"cannot modify header information - headers already sent"*.

Per questo la regola pratica è mettere **`session_start()` come primissima istruzione** del file. In molte configurazioni l'errore non compare perché è attivo l'*output buffering* (che mette il contenuto in un buffer e lo invia solo alla fine), ma non possiamo darlo per scontato su tutti i server. È un argomento che riprendiamo e sviscereremo alla fine del prossimo capitolo, dedicato proprio ai cookie e all'errore degli header già inviati.

### Liberare il lock: session_write_close()

Un ultimo dettaglio utile nelle applicazioni reali. Quando la sessione è gestita su **file** (l'impostazione predefinita), nel momento in cui chiamiamo `session_start()` e cominciamo a scriverci, PHP **blocca** quel file di sessione. Se un altro script tenta di accedere alla stessa sessione, deve aspettare che il primo abbia finito. Nelle applicazioni con molte richieste concorrenti — pensa a più chiamate AJAX che partono insieme — questo può creare colli di bottiglia, perché le richieste si mettono in coda in attesa del rilascio del lock.

Quando abbiamo finito di scrivere (o leggere) la sessione e non ci serve più tenerla aperta, è buona regola chiuderla esplicitamente con **`session_write_close()`**:

```php
session_start();

$_SESSION['user_id'] = 4;

// ...finito di lavorare sulla sessione:
session_write_close();
```

Codice completo: [listing-25.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/it/parte-04/cap-13/listing-25.php)


Con questa chiamata dichiariamo che abbiamo terminato di scrivere: PHP salva i dati, rilascia il lock e le altre richieste concorrenti possono finalmente accedere alla sessione. Se hai script chiamati via AJAX che devono girare in parallelo, ricordati di rilasciare la sessione appena hai finito, per non bloccare gli altri file.

## In sintesi

- Le **superglobali** sono array che PHP riempie automaticamente e che sono accessibili in qualunque scope — anche dentro una funzione — senza `global`: `$GLOBALS`, `$_SERVER`, `$_GET`, `$_POST`, `$_COOKIE`, `$_REQUEST`, `$_FILES`, `$_SESSION`.
- **`$GLOBALS`** raccoglie tutte le variabili dello scope globale (chiave = nome senza `$`). Vi si accede anche via costrutto `global`. Le variabili globali sono da evitare: meglio un file di configurazione che ritorna un array o una classe con membri statici.
- **`$_SERVER`** espone informazioni su server e richiesta: `REMOTE_ADDR` (IP utente), `REQUEST_METHOD`, `QUERY_STRING`, `REQUEST_URI`, `PHP_SELF`, `SCRIPT_FILENAME`, `DOCUMENT_ROOT`, `HTTP_USER_AGENT`, e altre. L'user agent è comodo ma inaffidabile per rilevare il browser.
- **`$_GET`** contiene i parametri della query string (URL, link, form GET); **`$_POST`** quelli inviati via POST (i dati non compaiono nell'URL). Sono array separati e non si sovrascrivono tra loro.
- Prima di leggere una chiave verifica sempre che esista: **`isset()`** (il `null` conta come non impostato, la stringa vuota sì), **`empty()`** (attenzione a `0` e `"0"`) e **`array_key_exists()`** (verifica solo la chiave, `null` compreso). Vale per ogni array.
- Attiva sempre gli errori in sviluppo: `ini_set('display_errors', 1)` e `error_reporting(E_ALL)`. Dei dati che arrivano via GET/POST non fidarti: possono essere manipolati.
- **`$_REQUEST`** è la fusione di GET, POST (e cookie, se configurato); l'ordine dipende da `request_order` nel `php.ini` (default `GP`, POST vince). Meglio leggere dal canale specifico che affidarsi a `$_REQUEST`.
- **`$_FILES`** gestisce l'upload: il form deve avere `enctype="multipart/form-data"`. Per ogni file ci sono `name`, `type`, `tmp_name`, `error`, `size`. Salva in sicurezza con `is_uploaded_file()`, controllo di `error === UPLOAD_ERR_OK` e `move_uploaded_file()`; non fidarti di `type`, verifica il tipo reale.
- **`$_SESSION`** conserva dati tra le pagine: avvia sempre con `session_start()` (prima di ogni output, per non incorrere in "headers already sent") in ogni pagina che deve accedervi. PHP identifica la sessione con il cookie `PHPSESSID`. Con sessione su file, `session_write_close()` rilascia il lock ed evita colli di bottiglia con le richieste concorrenti.
