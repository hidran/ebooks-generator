# 15. Il file system, include e require

In questo capitolo impariamo a far dialogare PHP con il **file system**: creare un file e scriverci dentro, leggerne il contenuto, aggiungere testo in coda, verificare se un file o una cartella esistono, eliminare e copiare file, ed esplorare il contenuto di una directory in tre modi diversi. Sono operazioni che ogni applicazione reale prima o poi deve fare: generare un log, salvare un documento, leggere un file di configurazione, ripulire file temporanei.

Nella seconda parte del capitolo affrontiamo quattro costrutti fondamentali del linguaggio: `include`, `require`, `include_once` e `require_once`. Sono lo strumento con cui PHP permette di spezzare un progetto in più file riutilizzabili — funzioni comuni, template, configurazioni — e sono alla base di tutto ciò che costruiremo nei progetti pratici dei prossimi capitoli. Vedremo infine una caratteristica poco conosciuta ma preziosissima: un file incluso può **ritornare un valore**, che possiamo catturare in una variabile.

## Creare un file e scriverci dentro

Partiamo da uno scenario semplice: abbiamo una cartella `docs` già esistente, che si trova nella stessa directory dello script PHP che stiamo per eseguire, e vogliamo creare al suo interno un file `myfile.txt`. La cartella in questo esempio l'abbiamo creata a mano, ma più avanti vedremo che anche le cartelle si possono creare da PHP (con la funzione `mkdir()`, che ti invito a cercare nel manuale).

Definiamo due variabili: `$dir`, che punta alla cartella, e `$fileName`, con il percorso completo del file da creare:

```php
<?php

$dir = 'docs';
$fileName = $dir . '/myfile.txt';
```

Codice completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-01.php)


Ci sono diversi modi per scrivere un file in PHP. Cominciamo da quello più classico e più flessibile: la funzione **`fopen()`**.

### Aprire un file: fopen e le modalità di apertura

`fopen()` apre un file e ci ritorna un **handle**, cioè una risorsa attraverso la quale possiamo agire sul file: scriverci, leggerlo, spostarci al suo interno. La funzione vuole due argomenti: il nome (percorso) del file da aprire e la **modalità** di apertura, che dice a PHP che cosa intendiamo farci:

```php
$hd = fopen($fileName, 'w');
```

Codice completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-02.php)


La modalità `'w'` sta per *write*: apre il file in sola scrittura. Se il file esiste, lo **tronca**, cioè azzera tutto quello che c'è dentro; se non esiste, lo crea. È esattamente quello che ci serve per creare `myfile.txt` da zero.

La prima cosa da fare, subito dopo, è verificare che l'apertura sia andata a buon fine, controllando che l'handle sia valido:

```php
if ($hd) {
    fwrite($hd, 'Prima scrittura su file');
} else {
    echo 'Impossibile creare il file';
}
```

Codice completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-03.php)


Se finiamo nel ramo `else`, le cause tipiche sono due: il percorso che abbiamo indicato non esiste, oppure PHP non ha i **permessi di scrittura** su quella cartella. Questo secondo punto merita attenzione: quando scrivi uno script PHP che deve scrivere su disco, devi garantire che il processo che esegue PHP — su Linux tipicamente Apache con PHP come modulo, o PHP-FPM — abbia il diritto di scrittura sulla cartella di destinazione. Su Windows vale lo stesso principio: verifica con quale utente è stato lanciato PHP e che quell'utente abbia accesso al file.

### Scrivere con fwrite e chiudere con fclose

Come hai visto nel codice qui sopra, per scrivere sul file usiamo **`fwrite()`**: le passiamo l'handle (nel nostro caso `$hd`) e la stringa da scrivere. Eseguiamo lo script e andiamo a controllare la cartella `docs`: il file `myfile.txt` è comparso e, aprendolo, troviamo il testo "Prima scrittura su file". Siamo riusciti a creare il file e a scriverci dentro.

Quando abbiamo finito di lavorare su un file dobbiamo **chiuderlo** con `fclose()`, passandole l'handle:

```php
fclose($hd);
```

Codice completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-04.php)


Ricordati sempre di chiudere i file: se un altro script sta aspettando di poter accedere a quel file, chiudendolo lo liberiamo.

### Leggere il file: fread e filesize

Ora che abbiamo scritto sul file, proviamo a leggerlo. Il giro è lo stesso: apriamo il file con `fopen()`, ma questa volta in modalità `'r'` (*read*), che apre in sola lettura e posiziona il cursore all'inizio del file:

```php
$hd = fopen($fileName, 'r');
```

Codice completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-05.php)


Una nota: se il file fosse binario (un'immagine, un PDF) e volessimo leggerlo in modo *binary safe*, cioè con la garanzia che i byte vengano letti correttamente, dovremmo aggiungere la lettera `b` alla modalità (`'rb'`). Per un file di testo come il nostro, la sola `'r'` basta.

Per leggere si usa la funzione **`fread()`**: le passiamo l'handle e il numero di byte che vogliamo leggere. Possiamo indicare una quantità qualunque, ma se la lettura arriva alla fine del file si ferma lì. E allora, se vogliamo leggere il file **completo**, come facciamo a sapere quanti byte chiedere? Ci aiuta la funzione **`filesize()`**, che riceve il percorso del file e ne ritorna la dimensione esatta in byte:

```php
$content = fread($hd, filesize($fileName));
echo $content;
```

Codice completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-06.php)


Ricaricando la pagina vediamo a video "Prima scrittura su file": siamo riusciti a leggere quello che avevamo scritto. Nota che `fread()` lavora sull'handle, mentre `filesize()` vuole il percorso del file: sono due cose diverse.

### Leggere a blocchi: feof e rewind

E se non volessimo (o potessimo) usare `filesize()`? In quel caso dovremmo leggere il file un pezzo alla volta, concatenando i blocchi in una variabile, finché il file non è finito. Qui entrano in gioco due concetti importanti.

Il primo è il **cursore**: quando leggiamo un file, PHP mantiene una posizione corrente che avanza a ogni lettura. Nel nostro script abbiamo appena letto tutto il file, quindi il cursore si trova alla fine. Se rileggessimo adesso, non otterremmo nulla. La funzione **`rewind()`**, a cui passiamo l'handle, riporta il cursore all'inizio del file — come "riavvolgere il nastro":

```php
rewind($hd);
```

Codice completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-07.php)


Il secondo è la funzione **`feof()`** (*end of file*): riceve l'handle e ci dice se il cursore è arrivato alla fine del file. Combinandola con un ciclo `while` possiamo leggere il file a blocchi:

```php
rewind($hd);

$content = '';
while (!feof($hd)) {
    $content .= fread($hd, 1024); // leggiamo 1 kilobyte alla volta
}
fclose($hd);

echo $content;
```

Codice completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-08.php)


Fai attenzione alla logica del ciclo: `feof($hd)` ritorna `true` quando siamo alla fine del file, ma noi vogliamo continuare a leggere **finché non** siamo alla fine — per questo la condizione è negata con `!`. A ogni giro concateniamo a `$content` il blocco letto (qui 1024 byte, cioè un kilobyte, ma la quantità è a nostra scelta); appena `feof()` ritorna `true`, usciamo dal ciclo e facciamo l'`echo` del contenuto. Il risultato è identico alla lettura "di un colpo solo" con `filesize()`: cambia solo la strategia.

### Aggiungere contenuto in coda: la modalità a

Finora sul file c'è una sola riga. Proviamo ora a scrivere **alla fine** del file, senza cancellare quello che c'è già. Il procedimento è sempre lo stesso, ma usiamo un'altra modalità di apertura: `'a'`, che sta per *append*. Se il file esiste lo apre e posiziona la scrittura in coda; se non esiste, lo crea:

```php
$hd = fopen($fileName, 'a');
fwrite($hd, 'Seconda scrittura su file');
fclose($hd);
```

Codice completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-09.php)


Rileggendo il file, però, scopriamo un dettaglio: le due frasi sono attaccate sulla stessa riga, "Prima scrittura su fileSeconda scrittura su file". Per andare a capo ci serve il carattere di **new line** `"\n"` che, come abbiamo visto nel Capitolo 11 sulle stringhe, deve stare tra **virgolette doppie**, altrimenti non viene interpretato (su Windows si usa la sequenza `"\r\n"`, new line più *carriage return*). Il posto giusto dove metterlo è alla fine della prima scrittura, concatenandolo alla stringa:

```php
fwrite($hd, 'Prima scrittura su file' . "\n");
```

Codice completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-10.php)


Ora l'output è quello che volevamo, una riga sotto l'altra:

```text
Prima scrittura su file
Seconda scrittura su file
```

Codice completo: [listing-11.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-11.txt)


Ricapitolando il giro completo: abbiamo aperto il file in `'w'` per crearlo e scrivere la prima riga, lo abbiamo chiuso, lo abbiamo riaperto in `'a'` per appendere la seconda riga, lo abbiamo chiuso di nuovo e infine lo abbiamo aperto in `'r'` per leggerlo.

### Le modalità di apertura in sintesi

Tieni sempre a portata di mano il manuale di PHP: cercando `fopen` (anche semplicemente "php fopen" in un motore di ricerca) trovi la lista completa delle modalità. Le principali:

| Modalità | Significato |
|---|---|
| `r` | sola lettura, cursore all'inizio del file |
| `r+` | lettura e scrittura, cursore all'inizio |
| `w` | sola scrittura: tronca il file se esiste, lo crea se non esiste |
| `w+` | come `w`, ma anche in lettura |
| `a` | sola scrittura in coda (append); crea il file se non esiste |
| `a+` | lettura e scrittura in coda |
| `b` | flag da aggiungere per la lettura/scrittura binary safe |

Esistono anche altre modalità (`x`, `x+`, `c`…) che puoi approfondire sul manuale, ma le più utilizzate sono `r`, `w` e `a`. Non serve impararle a memoria: man mano che userai queste funzioni ti resteranno in mente da sole.

## Leggere e scrivere con una sola funzione

Il giro `fopen()` → `fwrite()`/`fread()` → `fclose()` è potente, ma quando dobbiamo solo leggere o solo scrivere un file esiste una strada molto più comoda: PHP offre due funzioni che fanno tutto in una riga.

### file_put_contents e file_get_contents

La prima è **`file_put_contents()`**: "metti questo contenuto in questo file". Riceve il nome del file e il contenuto da scrivere:

```php
<?php

$dir = 'docs';
$fileName = $dir . '/myfile2.txt';

file_put_contents($fileName, 'Primo contenuto');
```

Codice completo: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-12.php)


Salviamo, ricarichiamo la pagina e controlliamo la cartella `docs`: il file `myfile2.txt` è stato creato e contiene "Primo contenuto". Un'unica riga al posto di apertura, scrittura e chiusura.

Proviamo ora a scrivere un secondo contenuto:

```php
file_put_contents($fileName, "\n" . 'Secondo contenuto');
```

Codice completo: [listing-13.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-13.php)


Verifichiamo… e nel file c'è solo "Secondo contenuto": il primo è sparito. Perché? Perché `file_put_contents()` **tronca il file**: se non esiste lo crea, se esiste lo azzera e poi scrive, esattamente come una `fwrite()` su un file aperto in modalità `'w'`. Fai molta attenzione a questo comportamento, perché è facile perdere dati senza accorgersene.

Come possiamo conservare il contenuto esistente? Leggendolo prima di scrivere. Qui entrano in gioco altre due funzioni. La prima è **`file_exists()`**, che verifica se un file esiste sul file system. La seconda è la gemella di `file_put_contents()`: **`file_get_contents()`**, che legge tutto il contenuto di un file e lo ritorna come stringa. Combiniamole:

```php
$content = '';

if (file_exists($fileName)) {
    $content = file_get_contents($fileName);
}

file_put_contents($fileName, $content . "\n" . 'Secondo contenuto');
```

Codice completo: [listing-14.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-14.php)


Inizializziamo `$content` a stringa vuota; se il file esiste, ci carichiamo dentro il suo contenuto; infine scriviamo il vecchio contenuto concatenato alla nuova riga. Ora lo script non tronca più nulla: ogni volta che ricarichi la pagina nel browser, al file viene aggiunta una nuova riga "Secondo contenuto" — ogni richiesta al server esegue lo script da capo e appende un'altra riga. Con queste due funzioni, `file_get_contents()` e `file_put_contents()`, possiamo leggere e scrivere file con il minimo sforzo.

### Percorsi relativi, percorsi assoluti e permessi

Un'osservazione importante sui percorsi. Quando passiamo a queste funzioni una directory **relativa** (come il nostro `docs`), PHP la cerca relativamente alla cartella in cui si trova il file `.php` in esecuzione. In alternativa possiamo sempre passare un **percorso assoluto**. E vale quanto detto per la scrittura: PHP deve avere il permesso di **lettura** su quel file o su quella directory, altrimenti `file_exists()` ritornerebbe `false` anche se il file c'è — non perché il file manchi, ma perché PHP non ha il diritto di vederlo.

### Verificare una cartella: is_dir

Oltre a verificare se un file esiste, possiamo verificare se un percorso è una **directory** con la funzione **`is_dir()`**:

```php
if (is_dir($dir)) {
    echo 'La directory esiste';
}
```

Codice completo: [listing-15.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-15.php)


Eseguendo lo script sulla nostra cartella `docs` otteniamo la conferma. Vedremo tra poco quanto è utile questa funzione quando esploriamo il contenuto di una cartella.

### Eliminare, copiare e le altre funzioni del file system

Un altro caso d'uso molto frequente: hai creato un file temporaneo — magari per generare un PDF — e a fine lavoro vuoi eliminarlo. Basta chiamare **`unlink()`** con il nome del file:

```php
unlink($fileName);
```

Codice completo: [listing-16.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-16.php)


Ricarichiamo la pagina e verifichiamo: `myfile2.txt` non esiste più, né nell'editor né nella cartella `docs`. Attenzione all'ordine delle istruzioni: se nello stesso script prima scrivi con `file_put_contents()` e poi elimini con `unlink()`, a ogni esecuzione il file viene ricreato e subito distrutto; metti la `unlink()` dove serve davvero nella logica del tuo programma.

Il capitolo delle funzioni sul file system del manuale PHP è ricchissimo: ci sono decine di funzioni per leggere, scrivere e interrogare le proprietà dei file. Qui ti ho mostrato quelle che si usano più spesso, ma vale la pena citarne altre:

- **`copy()`** — copia un file da una sorgente a una destinazione;
- **`file()`** — legge tutto un file dentro un array, una riga per elemento;
- **`fileatime()`** — ritorna la data dell'ultimo accesso al file;
- **`touch()`** — modifica la data di accesso di un file, come l'omonimo comando Linux;
- **`is_writable()`** — verifica se un file è scrivibile.

Ti lascio un esercizio: accanto alla cartella `docs` creane un'altra, per esempio `copia`; crea un file dentro `docs` e poi copialo nella nuova cartella usando `copy()`. Prova queste funzioni con mano: solo praticando fisserai quello che hai imparato.

## Leggere il contenuto di una cartella

Ora che sappiamo lavorare sui singoli file, vediamo come leggere il contenuto di una **cartella**: elencare i file che ci sono dentro, distinguere i file dalle sottodirectory e ricavare informazioni su ciascun elemento. PHP ci offre tre strade.

### scandir: la cartella come array

La prima, molto comoda e veloce, disponibile da PHP 5, è la funzione **`scandir()`**: le passiamo il nome della directory da esaminare e ci ritorna un array con tutte le voci che contiene:

```php
<?php

$dir = 'docs';

$d = scandir($dir);
var_dump($d);
```

Codice completo: [listing-17.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-17.php)


Il `var_dump()` mostra qualcosa di simile (nella nostra `docs` ci sono tre file):

```text
array(5) {
  [0]=> string(1) "."
  [1]=> string(2) ".."
  [2]=> string(10) "myfile.txt"
  [3]=> string(9) "test.html"
  [4]=> string(8) "test.txt"
}
```

Codice completo: [listing-18.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-18.txt)


Nota le prime due voci: il puntino `.` rappresenta la cartella corrente e i due puntini `..` la cartella *parent*, cioè quella superiore. Sono presenti in ogni directory e in genere vanno saltate quando iteriamo il contenuto.

Con un ciclo `foreach` possiamo scorrere le voci e, per ciascuna, verificare se è una directory o un file con le funzioni `is_dir()` e `is_file()`:

```php
foreach ($d as $entry) {
    // saltiamo la cartella corrente e la parent
    if ($entry == '.' || $entry == '..') {
        continue;
    }

    echo $entry;
    var_dump(is_dir($dir . '/' . $entry));
    var_dump(is_file($dir . '/' . $entry));
    echo '<br>';
}
```

Codice completo: [listing-19.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-19.php)


C'è un dettaglio che all'inizio inganna: se passassimo a `is_dir()` e `is_file()` solo `$entry` (per esempio `myfile.txt`), otterremmo `false` per tutto. Perché? Perché queste funzioni risolvono il percorso rispetto alla cartella dello script in esecuzione, non rispetto a `docs`: dobbiamo quindi concatenare il percorso della cartella, `$dir . '/' . $entry`, per dare loro il percorso giusto. Fatta la correzione, l'output ci dice per ogni voce se è una directory (`bool(true)`/`bool(false)`) e se è un file. Con questa verifica puoi costruire logiche più ricche: se la voce è una cartella, per esempio, puoi richiamare ricorsivamente la stessa funzione per esplorarla; se è un file, leggerlo o elaborarlo.

### opendir e readdir: l'approccio con handle

Il secondo modo è il più "storico" e ricalca quanto abbiamo visto con `fopen()`: la funzione **`opendir()`** riceve la directory e ritorna un **handle**, cioè una risorsa:

```php
$handle = opendir($dir);
var_dump($handle);
```

Codice completo: [listing-20.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-20.php)


Il `var_dump()` conferma che si tratta proprio del tipo **resource**, uno dei tipi di dato che abbiamo incontrato nel Capitolo 7: PHP ci mostra l'identificativo della risorsa e, ispezionandola, il percorso `docs`. Da questo handle possiamo leggere le voci della cartella una alla volta con **`readdir()`**, che ritorna la voce corrente e fa avanzare il cursore, oppure `false` quando le voci sono finite:

```php
while (($entry = readdir($handle)) !== false) {
    echo $entry, '<br>';
}
closedir($handle);
```

Codice completo: [listing-21.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-21.php)


Il risultato è lo stesso ottenuto con `scandir()` — puntino, due puntini e i file — ma qui, invece di ricevere tutto in un array, scorriamo la cartella tramite un cursore, esattamente come facevamo con i file. Anche in questo caso, quando abbiamo finito chiudiamo la risorsa (`closedir()`).

### DirectoryIterator: l'approccio a oggetti

Il terzo modo è secondo me il più comodo, ed è quello che uso sempre nei miei script: la classe **`DirectoryIterator`**, che fa parte della **SPL** (Standard PHP Library), la libreria standard inclusa in PHP dalla versione 5.

`DirectoryIterator` è una **classe**. Non abbiamo ancora studiato le classi — lo faremo nel Capitolo 26 — ma ti anticipo il minimo indispensabile: per creare un'istanza di una classe si usa l'operatore `new` seguito dal nome della classe, passando tra parentesi gli eventuali argomenti. Nel nostro caso, la directory da esplorare:

```php
$it = new DirectoryIterator($dir);
```

Codice completo: [listing-22.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-22.php)


Un **iteratore** è l'implementazione di un pattern: un oggetto che espone metodi per avanzare alla voce successiva, ritornare la voce corrente, riavvolgere all'inizio, sapere se esiste un elemento valido. E qui sta il vantaggio: ovunque ci sia un iteratore, possiamo scorrerlo con un semplice ciclo `foreach`, proprio come un array:

```php
foreach ($it as $entry) {
    echo $entry->getFilename() . ' - ' . $entry->getSize();
    var_dump($entry->isDir());
    var_dump($entry->isFile());
    echo '<br>';
}
```

Codice completo: [listing-23.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-23.php)


Ogni `$entry` è a sua volta un oggetto che rappresenta una voce della cartella (un file o una sottodirectory) e ha **già incorporati** tutti i metodi che ci servono, senza dover concatenare percorsi o ricorrere alle funzioni native come facevamo con `scandir()`. La sintassi `$entry->metodo()` chiama un metodo sull'oggetto; se scrivi `$entry->` nel tuo editor, l'autocompletamento ti mostra tutto quello che è disponibile:

- **`isDir()`** — la voce è una directory?
- **`isFile()`** — la voce è un file?
- **`getFilename()`** — il nome del file;
- **`getBasename()`** — il nome base, senza il percorso della cartella;
- **`getPath()`** — informazioni sul percorso;
- **`getSize()`** — la dimensione in byte;
- e molti altri: la data di creazione, il proprietario del file, i permessi…

Eseguendo il ciclo otteniamo, per ogni voce, il nome, la dimensione e i due `var_dump()`: il puntino `.` risulta directory e non file (`bool(true)` e `bool(false)`), lo stesso per `..`, mentre `myfile.txt`, `test.html` e `test.txt` risultano file e non directory. E in coda a ogni nome compare la dimensione: `test.html - 476`, `test.txt - 1`, `myfile.txt - 52` byte.

Ricapitolando, per leggere una cartella abbiamo tre strumenti: `scandir()`, che ci dà un array da scorrere con `foreach`; la coppia `opendir()`/`readdir()`, che lavora con un handle e un cursore; e `DirectoryIterator`, un'implementazione del pattern iterator che, ricevuta una cartella, ci ritorna un elenco di oggetti già dotati di tutti i metodi per interrogare nome, tipo e dimensione di ogni voce. Potendo scegliere, `DirectoryIterator` è la strada che ti consiglio: con una sola istruzione hai un iteratore e ogni voce si porta dietro tutto quello che serve. Anche qui, il consiglio è sempre lo stesso: crea una cartella di prova, mettici dei file e sperimenta le tre tecniche.

## include, require, include_once e require_once

Passiamo ora a quattro costrutti fondamentali di PHP: **`include`**, **`require`**, **`include_once`** e **`require_once`**. A cosa servono? A includere il codice di un file dentro un altro file, in modo da non dover ripetere lo stesso codice più volte: se abbiamo delle funzioni comuni a tutto il progetto, le scriviamo una volta sola e le riutilizziamo dove servono.

### Riutilizzare il codice con include

Creiamo un file `functions.php` con dentro una piccola funzione di utilità, `dd()`, che riceve una variabile qualunque, ne fa il `var_dump()` e poi ferma l'esecuzione con `die`:

```php
<?php

function dd($data)
{
    var_dump($data);
    die;
}
```

Codice completo: [listing-24.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-24.php)


Ora supponiamo di voler usare questa funzione in un altro file, `index.php`, dove abbiamo un array di dati:

```php
<?php

$data = [1, 2, 3];

dd($data);
```

Codice completo: [listing-25.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-25.php)


Non avrebbe senso copiare la funzione dentro `index.php`. Ma se eseguiamo lo script così com'è dalla riga di comando…

```bash
php index.php
```

Codice completo: [listing-26.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-26.sh)


…otteniamo un errore:

```text
PHP Fatal error:  Uncaught Error: Call to undefined function dd()
```

Codice completo: [listing-27.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-27.txt)


PHP non conosce `dd()`: la funzione vive in un altro file. È qui che entra in gioco `include`. Prima di chiamare la funzione, includiamo il file che la definisce:

```php
<?php

include 'functions.php';

$data = [1, 2, 3];

dd($data);
```

Codice completo: [listing-28.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-28.php)


Se il file si trovasse in un'altra cartella, dovremmo indicare il percorso completo. Il modo giusto di immaginare `include` è questo: è come se PHP prendesse il codice di `functions.php` e lo **copiasse e incollasse** nel punto esatto in cui compare l'istruzione. Rilanciamo dal terminale: ora la funzione esiste, viene eseguita e vediamo il `var_dump()` dell'array.

### include_once: includere una sola volta

Cosa succede se includiamo lo stesso file **due volte**? Immagina un file lungo, con tante righe: non ci accorgiamo che l'`include` c'è già e lo riscriviamo:

```php
include 'functions.php';
include 'functions.php'; // per errore, più avanti nel file
```

Codice completo: [listing-29.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-29.php)


Prova a immaginare l'esito prima di leggere oltre. Se hai pensato che ci sarà un errore perché la funzione risulta già definita, hai pensato bene:

```text
PHP Fatal error:  Cannot redeclare dd() (previously declared in functions.php:5)
```

Codice completo: [listing-30.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-30.txt)


La logica del "copia e incolla" spiega tutto: alla seconda inclusione PHP incolla di nuovo il codice e quindi **dichiara di nuovo** la funzione `dd()`, cosa vietata. Per questo, quando includiamo file che definiscono funzioni (o classi, come vedremo più avanti), conviene usare **`include_once`**:

```php
include_once 'functions.php';
include_once 'functions.php'; // nessun problema
```

Codice completo: [listing-31.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-31.php)


Come dice il nome, "*once*" significa "una sola volta": se il file è già stato incluso, PHP non lo include di nuovo. Rilanciando lo script non c'è alcun errore. È una protezione preziosa soprattutto nei progetti grandi, dove non possiamo sapere se un altro pezzo di codice ha già incluso lo stesso file.

### include o require?

E `require`? La differenza tra `include` e `require` sta in come reagiscono quando il file da includere **non esiste** (o il percorso è sbagliato). Facciamo una prova: al posto della funzione `dd()` mettiamo un `print_r()` che non ferma l'esecuzione, e sbagliamo apposta il nome del file:

```php
<?php

include 'functions2.php'; // questo file non esiste

print_r($data);
```

Codice completo: [listing-32.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-32.php)


Eseguendo lo script, la prima cosa che PHP ci dice è un **warning**:

```text
PHP Warning:  include(functions2.php): Failed to open stream:
No such file or directory
```

Codice completo: [listing-33.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-33.txt)


Ma è solo un warning: **il codice continua l'esecuzione** e il `print_r()` viene eseguito regolarmente. (Se invece dopo l'`include` fallito chiamassimo `dd()`, avremmo comunque il fatal error "Call to undefined function", perché la funzione non è mai stata caricata.)

Ora sostituiamo `include` con `require`:

```php
require 'functions2.php';

print_r($data); // questa riga non viene mai raggiunta
```

Codice completo: [listing-34.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-34.php)


Con `require` stiamo dicendo a PHP che quel file è **obbligatorio** (*required*): se non c'è, il programma deve fermarsi. E infatti al warning segue un **fatal error**:

```text
PHP Fatal error:  Failed opening required 'functions2.php'
```

Codice completo: [listing-35.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-35.txt)


L'esecuzione si interrompe lì: le righe successive non vengono mai raggiunte, perché lo script fallisce già alla riga della `require`.

Quale usare, quindi? Devi valutarlo tu, in base alle specifiche del tuo codice. Se il file incluso è una parte **essenziale** dell'applicazione — senza la quale non ha senso proseguire — usa `require`: meglio fermarsi subito. Se invece è un pezzo di codice di cui l'applicazione può fare a meno — magari qualcuno ha rimosso il file, ma il resto può continuare a girare — usa `include`, così un file mancante non blocca tutto. E naturalmente puoi sempre verificare prima l'esistenza del file con `file_exists()`, come abbiamo imparato in questo stesso capitolo.

Esiste anche **`require_once`**, che combina le due caratteristiche: file obbligatorio (fatal error se manca) e inclusione una sola volta. Se scriviamo `require_once 'functions.php'` due volte, il file viene incluso una volta sola e non ci sono problemi:

```php
require_once 'functions.php';
require_once 'functions.php'; // ignorato: già incluso

dd($data);
```

Codice completo: [listing-36.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-36.php)


Il suffisso `_once`, quindi, vale sia per `include` che per `require`; la differenza tra le due famiglie resta sempre la stessa: con `include` il codice non si ferma se il file manca, con `require` sì.

### Un template dentro un ciclo: quando _once non va bene

A questo punto potresti dire: allora usiamo sempre le versioni `_once` e stiamo tranquilli. Un attimo di attenzione: per i file che definiscono funzioni (e più avanti classi) va benissimo, ma c'è un caso d'uso in cui `_once` è proprio sbagliato: i **template** inclusi dentro un ciclo.

Vediamolo con un esempio. Creiamo un file `show_data.php` che deve mostrare una lista di città:

```php
<?php

$cities = ['Roma', 'Torino', 'Milano'];

echo '<ul>';
foreach ($cities as $data) {
    include 'li.php';
}
echo '</ul>';
```

Codice completo: [listing-37.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-37.php)


E creiamo il template `li.php`: un frammento riutilizzabile che stampa un elemento della lista. Usiamo il tag di apertura corto `<?=`, che significa "apri PHP e fai subito l'`echo` di quello che segue", e diamo per scontato che esista una variabile `$data`:

```php
<li class="data"><?= $data ?? '' ?></li>
```

Codice completo: [listing-38.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-38.php)


L'operatore `??` (*null coalescing*, disponibile da PHP 7) qui fa da rete di sicurezza: se `$data` non è stata passata, stampiamo una stringa vuota invece di generare un errore.

Come funziona l'insieme? A ogni giro del `foreach`, la variabile `$data` contiene una città e l'`include` "incolla" il template in quel punto: è come se avessimo chiuso PHP, incollato l'HTML del template e riaperto PHP, una volta per ogni città. Lanciamo dalla riga di comando:

```bash
php show_data.php
```

Codice completo: [listing-39.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-39.sh)


E vediamo la lista con le tre città. Se preferisci vederla nel browser, puoi avviare il web server integrato di PHP su una porta a scelta:

```bash
php -S localhost:3000
```

Codice completo: [listing-40.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-40.sh)


e aprire `http://localhost:3000/show_data.php`: ecco la nostra lista renderizzata.

Ora la controprova: sostituiamo `include` con `include_once` dentro il ciclo. Cosa stamperà? Solo **Roma**: il template viene incluso al primo giro e poi mai più, perché `_once` significa proprio "una sola volta". Ecco il caso in cui **non** possiamo usare `include_once`: vogliamo riutilizzare il template tante volte quanti sono i dati da mostrare. Nei template dentro un ciclo si usa `include` (o `require`, se vogliamo che l'assenza del file blocchi tutto: la logica è identica, cambia solo la reazione al file mancante).

### Costrutti, non funzioni

Un'ultima nota di sintassi. In qualche codice datato potresti incontrare questa forma, con le parentesi tonde:

```php
include('functions.php');
```

Codice completo: [listing-41.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-41.php)


Funziona, ma le parentesi non servono. `include` e `require` non sono funzioni: sono **costrutti del linguaggio**, come `echo`. Per questo la forma idiomatica, quella che ti consiglio di usare sempre, è senza parentesi:

```php
include 'functions.php';
require 'config.php';
```

Codice completo: [listing-42.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-42.php)


### Un consiglio: non chiudere il tag PHP

Se un file contiene **solo codice PHP** — come il nostro `functions.php` — non chiudere il tag `?>` alla fine. Non è necessario, e c'è una buona ragione per ometterlo: se dopo il `?>` restano spazi o righe vuote, quando includi quel file dentro una pagina HTML quegli spazi finiscono nell'output e possono creare problemi difficili da diagnosticare. La regola è semplice: file di puro PHP, niente tag di chiusura.

E un'avvertenza per il futuro: `include` e `require` "incollano" codice, quindi se includi due file che definiscono entrambi una funzione `dd()`, avrai un conflitto di funzioni con relativo fatal error. Più avanti, nel Capitolo 30, vedremo che i namespace servono proprio a evitare questi conflitti; per ora tienine conto quando organizzi i tuoi file.

## Ritornare un valore da include e require

C'è un'altra caratteristica di `include` e `require` che li rende preziosi: se il file incluso **ritorna un valore**, possiamo catturarlo in una variabile. Finora li abbiamo usati per portare dentro funzioni o per stampare template; a volte però serve qualcosa di diverso: pensare al file incluso come a una **fonte di dati**. Il caso classico è un file con le configurazioni del database, o con dati che vogliamo avere a disposizione in tutte le pagine.

### Il problema delle variabili globali

Creiamo un file `config.php` e mettiamoci qualche dato di configurazione dentro un array:

```php
<?php

$config = [
    'ip'       => '127.0.0.1',
    'password' => 'test',
    'email'    => 'test@mail.test',
    'username' => 'test',
];
```

Codice completo: [listing-43.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-43.php)


Nel file principale facciamo la `require` e verifichiamo:

```php
<?php

require 'config.php';

var_dump($config);
```

Codice completo: [listing-44.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-44.php)


Caricando la pagina vediamo l'array completo: IP, password, email, username. Funziona, perché la `require` ha "incollato" il codice e quindi la variabile `$config` esiste anche qui. Ma proprio questo è il problema: `$config` è diventata una variabile **iniettata nello scope** del file che include. Supponiamo che, più avanti nel file, senza sapere che quella variabile esiste, scriviamo:

```php
$config = [];
```

Codice completo: [listing-45.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-45.php)


Abbiamo appena sovrascritto tutta la configurazione: il `var_dump()` ora mostra un array vuoto. In un progetto grande, questo tipo di collisione tra variabili è una fonte di bug subdola. Come facciamo se **non** vogliamo iniettare variabili globali negli altri file quando facciamo una `require`?

### return dentro il file incluso

La soluzione: invece di definire una variabile, il file di configurazione **ritorna** direttamente il valore con `return`:

```php
<?php

return [
    'ip'       => '127.0.0.1',
    'password' => 'test',
    'email'    => 'test@mail.test',
    'username' => 'test',
];
```

Codice completo: [listing-46.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-46.php)


Possiamo ritornare qualunque cosa: un array, una stringa, un oggetto. Ora nel file principale, se facciamo solo `require 'config.php'` e poi `var_dump($config)`, PHP ci dice che `$config` è *undefined*: la variabile non esiste più, e il valore ritornato è andato perso. Il punto chiave è che **`require` e `include` sono espressioni che ritornano un valore**, e quel valore possiamo assegnarlo a una variabile nostra:

```php
<?php

$config = require 'config.php';

var_dump($config);
```

Codice completo: [listing-47.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/it/parte-04/cap-15/listing-47.php)


Ricarichiamo: abbiamo catturato il ritorno e l'array è di nuovo tutto lì. Nota che il nome della variabile è completamente libero — `$config`, `$conf`, quello che vuoi — e potremmo anche passare il risultato direttamente a una funzione. Il vantaggio è pulizia: chi fa la `require` di `config.php` riceve i dati **solo se li cattura esplicitamente**; non ci sono variabili globali che contaminano lo scope del file che include. Se non catturi il ritorno, quei dati semplicemente non esistono nel tuo scope.

Due dettagli per completare il quadro:

- **Il valore di ritorno di default.** Se il file incluso non contiene alcun `return`, `include` e `require` ritornano `1` quando l'inclusione riesce. Se il file non esiste, il "valore" è `false`, accompagnato — come sappiamo — da un warning con `include` o da un fatal error con `require`.
- **Il file viene comunque eseguito riga per riga.** Se prima del `return` in `config.php` mettiamo un `echo 'test';`, quel testo viene stampato regolarmente, e poi l'array viene ritornato: il `return` conclude l'esecuzione del file incluso e ne restituisce il valore.

Tutto quello che abbiamo detto vale allo stesso modo per `include`, `require`, e per le varianti `_once`: la scelta tra loro segue le stesse regole viste nel paragrafo precedente (obbligatorietà del file e inclusione singola); la capacità di ritornare un valore è comune a tutti. Questo pattern — un file di configurazione che ritorna un array, catturato con `$config = require 'config.php'` — lo ritroverai nei progetti pratici del libro, a partire dalla configurazione del database.

## In sintesi

- `fopen()` apre un file e ritorna un **handle**; le modalità principali sono `r` (lettura), `w` (scrittura con troncamento, crea il file se manca) e `a` (append in coda). Si scrive con `fwrite()`, si legge con `fread()` e si chiude sempre con `fclose()`.
- `filesize()` dà la dimensione in byte di un file; `feof()` dice se il cursore è alla fine; `rewind()` lo riporta all'inizio. Il new line `"\n"` (su Windows `"\r\n"`) va tra virgolette doppie.
- `file_put_contents()` e `file_get_contents()` scrivono e leggono un file in una sola riga; attenzione: `file_put_contents()` **tronca** il file esistente.
- `file_exists()` verifica l'esistenza di un file, `is_dir()` se un percorso è una directory, `unlink()` elimina un file, `copy()` lo copia. I percorsi relativi si risolvono rispetto alla cartella dello script; PHP deve avere i permessi di lettura/scrittura necessari.
- Per leggere una cartella: `scandir()` (array di voci, con `.` e `..` da saltare), `opendir()`/`readdir()` (handle e cursore) e `DirectoryIterator` (SPL), il più comodo: ogni voce è un oggetto con metodi come `isDir()`, `isFile()`, `getFilename()`, `getSize()`.
- `include` incorpora un file come un "copia e incolla"; `require` fa lo stesso ma genera un **fatal error** se il file manca (con `include` solo un warning e il codice prosegue). Le varianti `include_once`/`require_once` includono il file una sola volta: ideali per funzioni e classi, da evitare per i template dentro un ciclo.
- `include` e `require` sono **costrutti del linguaggio**, non funzioni: si usano senza parentesi. Nei file di puro PHP non chiudere il tag `?>`.
- Un file incluso può **ritornare un valore** con `return`, catturabile con `$config = require 'config.php'`: è il modo pulito di caricare configurazioni senza inquinare lo scope con variabili globali. Senza `return`, l'inclusione riuscita ritorna `1`.
