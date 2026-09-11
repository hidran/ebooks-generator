# 7. Variabili, tipi e costanti

Nel capitolo precedente abbiamo visto come PHP esegue il codice e come si mescola con l'HTML. In questo capitolo entriamo nel cuore del linguaggio: le **variabili**, cioè i contenitori con cui immagazziniamo e riutilizziamo i dati, e i **tipi** fondamentali che questi dati possono avere — numeri, boolean, stringhe e array. Chiuderemo con le **costanti**, i valori che non devono cambiare durante l'esecuzione, e con tre funzioni native — `isset()`, `empty()` e `is_null()` — che useremo continuamente per verificare lo stato di una variabile.

Sono le fondamenta di tutto quello che costruiremo nel resto del libro: i form, le query al database, i progetti delle parti finali manipolano in continuazione variabili, stringhe e array. Vale la pena dedicare a questo capitolo tutta l'attenzione che merita, anche perché PHP ha alcuni comportamenti — la conversione automatica dei tipi, le stringhe come sequenze di byte, il troncamento delle chiavi degli array — che sorprendono chi arriva da altri linguaggi e che sono fonte di bug classici.

## Che cos'è una variabile

### Dalle espressioni alle variabili

In PHP, come in altri linguaggi, possiamo scrivere delle **espressioni letterali**. Un'espressione è come quando facevamo matematica: `2 + 2`. Ogni istruzione va terminata con un punto e virgola, per dire a PHP dove finisce:

```php
<?php

2 + 2;
```

Codice completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-01.php)


Se eseguiamo questo codice dalla riga di comando con `php index.php`, non compare niente — ma nemmeno un errore. PHP valuta l'espressione, ottiene `4` e lo butta via, perché non gli abbiamo chiesto di mostrarlo. Per far uscire il risultato sulla console usiamo il costrutto `echo`, che significa "mostra a video (o sulla console) questa espressione":

```php
<?php

echo (2 + 2);   // 4
```

Codice completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-02.php)


Le parentesi tonde qui servono solo a delimitare l'espressione, come in matematica. Un'espressione letterale può essere anche una **stringa**, cioè un insieme di caratteri qualsiasi — una frase, un nome — oppure un numero:

```php
<?php

'Hello world';   // espressione valutata, ma nessun output
3.1415;          // idem

echo 'Hello world';   // Hello world
echo 3.1415;          // 3.1415
```

Codice completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-03.php)


Oltre che dalla console, puoi vedere il risultato nel browser: se usi VS Code con l'estensione PHP Server che abbiamo configurato nel Capitolo 5, basta un clic destro sul file e "PHP Server: Serve project" per aprire la pagina nel browser. In questo capitolo useremo quasi sempre la console, riservando il browser ai casi in cui l'output contiene HTML.

Ora, supponiamo di voler usare il valore 3.1415 — un pi greco ridotto — per calcolare l'area di un cerchio o il volume di un cilindro. Come facciamo a immagazzinarlo da qualche parte, in modo da riutilizzarlo in diverse espressioni? È esattamente a questo che servono le variabili.

Una **variabile** non è altro che un'area di memoria (nella RAM del computer, o anche su disco, dipende da come il sistema la gestisce) dove immagazziniamo un dato, con un nome che fa da etichetta di riferimento. Il dato può essere qualsiasi cosa: un numero, una stringa, un singolo carattere, un elenco di città, un record letto dal database, il contenuto di un file, perfino una risorsa come un puntatore a un file aperto o a una connessione al database. Tutto questo lo mettiamo in una variabile per poterlo riciclare quante volte vogliamo.

### Dichiarare una variabile e le naming convention

In PHP una variabile inizia sempre con il simbolo del **dollaro** (`$`): è lo standard del linguaggio. Dopo il dollaro, il nome:

- può cominciare con una **lettera** o con un **underscore** (`_`, il trattino basso);
- può proseguire con lettere, numeri e underscore;
- **non** può cominciare con un numero e **non** può contenere spazi.

```php
<?php

$name = 'Hidran';      // valido
$_name = 'Hidran';     // valido
$name2 = 'Hidran';     // valido
// $2name = 'Hidran';  // ERRORE: non può iniziare con un numero
// $last name = '...'; // ERRORE: niente spazi
```

Codice completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-04.php)


Per assegnare un valore usiamo il segno **uguale** (`=`), proprio come in matematica assegnavamo un valore a *x* o a *y*. Le stringhe vanno racchiuse tra apici o virgolette (vedremo tra poco la differenza), i numeri no:

```php
<?php

$lastName = 'Arias';
$name = 'Hidran';
$age = 50;
$cities = ['Roma', 'Torino', 'Napoli'];   // un array: lo studieremo tra poco
```

Codice completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-05.php)


Qualche parola sulle convenzioni. Al computer non importa nulla di come chiami una variabile: potresti chiamarla `$a234` e per lui sarebbe solo un puntatore a un'area di memoria. Ma il codice viene letto dai programmatori, e chi legge deve capire che cosa fa: usa sempre **nomi parlanti**, che diano un'informazione. Io per abitudine uso nomi in inglese, e seguo la convenzione **camelCase**: quando il nome è composto da due parole, la seconda inizia con la maiuscola, come in `$lastName`. Scegli una convenzione e mantienila in tutto il progetto.

Un'ultima osservazione importante: PHP è un linguaggio a **tipizzazione dinamica**. In una variabile che contiene un numero possiamo tranquillamente assegnare dopo una stringa:

```php
<?php

$r = 20;
$r = 'una lettera';   // in PHP è lecito
```

Codice completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-06.php)


In linguaggi come Java o C# questo non è possibile: una volta dichiarata una variabile di tipo numerico, non le puoi assegnare una stringa. In PHP sì. Da PHP 7 in poi possiamo comunque dichiarare i tipi dei parametri delle funzioni e forzare PHP a verificarli — lo vedremo nel Capitolo 10 parlando di funzioni.

### Un esempio pratico: l'area del cerchio

Mettiamo insieme quello che abbiamo visto e calcoliamo l'area di un cerchio. Ci servono il pi greco (per ora in una variabile: più avanti in questo capitolo scopriremo che è il candidato perfetto per una costante) e il raggio:

```php
<?php

$pi = 3.1415;
$r = 20;

$area = $pi * $r * $r;

echo "L'area è $area\n";
```

Codice completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-07.php)


Per moltiplicare, in quasi tutti i linguaggi di programmazione si usa l'**asterisco** (`*`). Esiste anche una funzione per elevare al quadrato, ma per ora moltiplichiamo il raggio per se stesso. Il vantaggio è evidente: invece di copiare `3.1415` ogni volta, usiamo `$pi`; e immagina che il raggio arrivi da un form compilato dall'utente — noi riceviamo il dato, lo mettiamo in `$r` e applichiamo la formula.

Nota due cose nell'`echo` finale. Primo: dentro le **virgolette** possiamo scrivere direttamente il nome della variabile e PHP la sostituisce con il suo valore (con gli apici singoli no — ci torniamo nel paragrafo sulle stringhe). Secondo: `\n` è il carattere di **nuova riga** (new line), usato in quasi tutti i linguaggi — PHP, Java, C# — per andare a capo sulla console.

Se però apri lo stesso script nel browser, scopri che il testo non va a capo. Guardando il sorgente della pagina (tasto destro → Visualizza sorgente) l'a capo c'è, ma il browser non lo renderizza: per l'HTML un ritorno a capo nel sorgente è solo uno spazio. Per andare a capo nel browser serve un tag HTML, ad esempio un paragrafo — e sappiamo già dal Capitolo 6 che possiamo mescolare HTML e PHP:

```php
<?php

echo '<p>Il perimetro è ' . (2 * $pi * $r) . "</p>\n";
```

Codice completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-08.php)


Qui abbiamo anche riutilizzato `$pi` e `$r` una seconda volta, concatenando il risultato alla stringa con il **punto** (`.`) — l'operatore di concatenazione che approfondiremo tra poco. Le variabili si possono riusare quante volte vogliamo, e più avanti vedremo come passarle come parametri alle funzioni.

## I numeri: integer e float

PHP ha due tipi numerici: gli **integer** (numeri interi) e i **float** (numeri a virgola mobile, o flottante). Creare un numero è semplicissimo: basta assegnarlo a una variabile.

```php
<?php

$dec = 255;
var_dump($dec);   // int(255)
```

Codice completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-09.php)


Qui incontriamo una funzione nativa preziosissima: **`var_dump()`**. Le passiamo una variabile tra le parentesi tonde e lei ci mostra il **tipo** e il **valore**: in questo caso `int(255)`. La useremo in continuazione per ispezionare le variabili.

### Interi, stringhe numeriche e conversioni automatiche

Cosa succede se mettiamo il numero tra apici?

```php
<?php

$dec = '255';
var_dump($dec);        // string(3) "255"

var_dump($dec * 4);    // int(1020)
var_dump($dec * 4.4);  // float(1122)
```

Codice completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-10.php)


Tra apici, `255` è una **stringa** di tre byte. Ma se la moltiplichiamo per 4, otteniamo `int(1020)`: PHP fa in automatico la conversione — il **casting** — del contenuto della stringa in numero, perché l'operatore di moltiplicazione si aspetta dei numeri. PHP legge la stringa dall'inizio: se comincia con un numero (eventualmente preceduto dal segno `+` o `-`), prosegue finché il numero non finisce e converte quella parte. Con `'255aa' * 4` otterrebbe comunque `1020`, fermandosi al 5 — anche se le versioni recenti di PHP segnalano un avviso quando la stringa non è un numero "ben formato". Lo stesso vale se moltiplichiamo per un float come `4.4`: il risultato diventa `float`.

Questa flessibilità è comoda, ma un consiglio dall'esperienza: per convenzione, e per correttezza, se sai a priori che un valore è un numero rappresentalo come numero, senza apici. Rispettiamo i tipi anche se PHP fa la conversione al posto nostro. E ricorda che da PHP 7 possiamo dichiarare che un parametro di funzione deve essere `int`: in quel caso la verifica diventa rigorosa.

### Rappresentare gli interi in altre basi

I numeri interi non si scrivono solo in base dieci. PHP ci permette di rappresentarli anche in **ottale** (base 8), **esadecimale** (base 16) e **binario** (base 2):

```php
<?php

$oct = 0124;         // ottale: prefisso 0
$hex = 0xDE;         // esadecimale: prefisso 0x
$bin = 0b11111111;   // binario: prefisso 0b

var_dump($oct);   // int(84)
var_dump($hex);   // int(222)
var_dump($bin);   // int(255)
```

Codice completo: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-11.php)


Attenzione ai prefissi: uno **zero** iniziale per l'ottale, **`0x`** per l'esadecimale, **`0b`** per il binario (lo zero, non la lettera "o": è un errore di battitura classico).

Come si arriva a quei valori decimali? È matematica di base, ma ripassiamola. In base 8 le cifre vanno da 0 a 7, e si somma partendo da destra, moltiplicando ogni cifra per la potenza di 8 corrispondente alla sua posizione:

```text
0124 (ottale) = 4×8⁰ + 2×8¹ + 1×8² = 4 + 16 + 64 = 84
```

Codice completo: [listing-12.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-12.txt)


In base 16 le cifre vanno da 0 a 9 e poi proseguono con le lettere: A vale 10, B 11, C 12, D 13, E 14, F 15. Il procedimento è lo stesso, con le potenze di 16:

```text
0xDE = 14×16⁰ + 13×16¹ = 14 + 208 = 222
```

Codice completo: [listing-13.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-13.txt)


Il binario, infine, è la base dei computer: solo 0 e 1, e andando verso sinistra i pesi raddoppiano — 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024 e così via. Otto cifre 1 danno esattamente 255.

La cosa importante da capire è che la base è solo una **rappresentazione**: internamente PHP usa sempre lo stesso numero, e quando lo mostriamo con `var_dump()` o `echo` lo converte automaticamente in base dieci. Possiamo anche mescolare le rappresentazioni nelle operazioni:

```php
<?php

$result = $dec + $hex;   // 255 + 222
echo $result;            // 477
```

Codice completo: [listing-14.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-14.php)


### Float e limiti degli interi

Normalmente useremo numeri decimali, positivi o negativi, e numeri con la virgola — dove il separatore decimale è il **punto**:

```php
<?php

$negative = -255;
$float = 123.45;
var_dump($float);   // float(123.45)
```

Codice completo: [listing-15.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-15.php)


Una particolarità: quando usiamo la **divisione**, il risultato è in generale un valore float; solo se entrambi gli operandi sono interi e la divisione è esatta PHP restituisce un intero. Per il resto valgono gli stessi operatori dell'algebra di base, che studieremo in dettaglio nel Capitolo 8.

Quanto ai limiti: la dimensione massima di un integer dipende dalla **piattaforma**. Sui sistemi a 32 bit il massimo è circa 2,1 miliardi (2³¹ − 1); sui sistemi a 64 bit — ormai lo standard su Linux, macOS e Windows moderni — è enormemente più grande. Per le operazioni matematiche di tutti i giorni siamo copertissimi. I float seguono lo standard **IEEE 754**, con gli arrotondamenti tipici della virgola mobile: per la stragrande maggioranza dei casi va benissimo, e se ti servono calcoli di precisione arbitraria PHP mette a disposizione librerie matematiche dedicate (come BCMath), che esulano da questo libro.

## Il tipo boolean

Il tipo **boolean** (o booleano) viene dall'algebra booleana: può assumere solo due valori, **`true`** (vero) e **`false`** (falso). In PHP queste due costanti sono *case-insensitive* — puoi scrivere `true`, `True` o `TRUE` — e il loro uso tipico è nelle verifiche e nei cicli: "se questa condizione è vera, fai questo; altrimenti, fai quest'altro".

Il modo in cui PHP gestisce i boolean è però diverso da linguaggi come Java o C#, dove il tipo boolean è rigido e non si può confrontare con altri tipi: in PHP **qualsiasi valore può essere valutato come boolean**, tramite conversione automatica. Ed è qui che bisogna fare molta attenzione.

### I valori considerati false

In PHP sono considerati falsi (*falsy*) soltanto questi valori:

| Valore | Note |
|---|---|
| `false` | la costante booleana |
| `0` | l'intero zero (anche `-0`) |
| `0.0` | il float zero (anche `-0.0`) |
| `''` | la stringa vuota |
| `'0'` | la stringa contenente zero — attenzione, confonde molti! |
| `[]` | un array vuoto |
| `null` | il valore nullo |
| elemento XML vuoto | un oggetto SimpleXML creato da un elemento vuoto (vedremo l'XML nel Capitolo 16) |

**Qualsiasi altra cosa è vera**: una stringa non vuota, un numero diverso da zero, un array con almeno un elemento. Ti consiglio di tenere questa tabella come riferimento — puoi anche incollarla in un commento nel codice. A proposito: per i commenti su più righe si usa `/*` per aprire e `*/` per chiudere; tutto quello che sta in mezzo viene ignorato dall'interprete, che non ne fa nemmeno il parsing.

### Boolean nella pratica: espressioni e cast

Dichiarare una variabile booleana è immediato. Usiamola subito in una condizione — il costrutto `if`/`else` lo studieremo a fondo nel Capitolo 9, ma il senso è intuitivo: *se* la condizione tra parentesi è vera esegui il primo blocco tra graffe, *altrimenti* (else) il secondo:

```php
<?php

$verify = false;

if ($verify == true) {
    echo 'Verify is true';
} else {
    echo 'Verify is false';
}
// Output: Verify is false

var_dump($verify);   // bool(false)
```

Codice completo: [listing-16.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-16.php)


Il confronto si può anche abbreviare: `if ($verify)` significa "se `$verify` è vero". E un boolean non nasce solo dalle costanti `true` e `false`: qualunque **espressione che ritorna vero o falso** può essere assegnata a una variabile:

```php
<?php

$verify = 4 > 5;    // 4 è maggiore di 5? No
var_dump($verify);  // bool(false)

$verify = 4 == 5;   // 4 è uguale a 5? No
var_dump($verify);  // bool(false)
```

Codice completo: [listing-17.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-17.php)


Nel Capitolo 8 vedremo la differenza tra il confronto con due segni uguale (`==`) e con tre (`===`): il secondo pretende che i valori siano uguali *e dello stesso tipo*.

Ora la parte interessante. Assegniamo a `$verify` una stringa:

```php
<?php

$verify = 'Hello world';
var_dump($verify);   // string(11) "Hello world"

if ($verify) {
    echo 'Verify is true';   // viene eseguito!
}
```

Codice completo: [listing-18.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-18.php)


`$verify` è una stringa, ma la condizione passa: una stringa non vuota, convertita in boolean, è `true`. La conversione la fa PHP in automatico, ma possiamo farla anche noi esplicitamente, mettendo il tipo tra parentesi davanti al valore — si chiama **cast** — come si fa in Java e in altri linguaggi:

```php
<?php

var_dump((bool) 'Hello world');   // bool(true)
var_dump((bool) '');              // bool(false)
var_dump((bool) '0');             // bool(false) — la stringa "0"!
```

Codice completo: [listing-19.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-19.php)


### Attenzione alle stringhe "true" e "false"

C'è un tranello pratico che incontrerai lavorando con i form nella Parte IV. Se dal browser inviamo a PHP le parole `true` o `false`, lato server arrivano come **stringhe** — e una stringa non vuota è sempre vera:

```php
<?php

$verify = 'false';   // stringa di 5 caratteri, NON il boolean false
var_dump($verify);   // string(5) "false"

if ($verify) {
    echo 'Passa dal ramo true!';   // sì: una stringa non vuota è true
}
```

Codice completo: [listing-20.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-20.php)


Lo stesso vale per una checkbox, che di suo invia valori come `on`/`off`: arrivano come stringhe, e anche `'off'` risulterebbe vero. Per questo lo standard, lato client, è inviare **`0` e `1`**: la stringa `'0'` è falsa e `'1'` è vera, quindi siamo sicuri di ottenere il boolean che ci aspettiamo. In altri linguaggi questo giochino non funziona: lì servono i valori letterali `true` e `false` o un cast esplicito. In PHP, conoscendo la tabella dei valori falsy, funziona benissimo.

## Introduzione alle stringhe

Una **stringa** in PHP è una sequenza di caratteri, dove ogni carattere è rappresentato da un **byte**: sono quindi possibili 256 valori diversi per ciascun byte. Questo dettaglio, che sembra accademico, è in realtà importantissimo: internamente PHP immagazzina *sequenze di byte*, senza sapere nulla della codifica. Sta a noi — e alle funzioni e librerie che usiamo — interpretare correttamente quei byte, sia quando arrivano da una sorgente esterna sia quando li diamo in pasto a PHP. Ne vedremo subito le conseguenze pratiche.

### Apici singoli e virgolette

Ci sono due modi base per delimitare una stringa: gli **apici singoli** (`'...'`) e le **virgolette**, o doppi apici (`"..."`). La differenza è fondamentale:

- con gli **apici singoli**, PHP prende la stringa così com'è: nessuna variabile viene interpretata;
- con le **virgolette**, PHP fa il **parsing** della stringa cercando le variabili al suo interno (tutto ciò che inizia con `$`, o racchiuso tra graffe, come vedremo) e le sostituisce con il loro valore: si parla di **interpolazione**.

```php
<?php

$name = 'Hidran';
$address = 'corso Racconigi';

$lastName = "$name Arias";
echo $lastName;          // Hidran Arias

echo 'Nome: $name';      // Nome: $name  (nessun parsing!)
echo "Nome: $name";      // Nome: Hidran
```

Codice completo: [listing-21.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-21.php)


Nella prima assegnazione, dentro le virgolette PHP trova `$name`, lo interpreta e produce `Hidran Arias`. Nota lo spazio dopo la variabile: serve anche a rendere chiaro dove finisce il nome della variabile. Con gli apici singoli invece la stringa `'$address'` resta letteralmente `$address`, dollaro compreso.

Quando non c'è niente da interpolare, PHP con gli apici singoli evita del tutto il passaggio di parsing: un tempo era anche misurabile in velocità, oggi la differenza è trascurabile. Io per convenzione uso comunque gli **apici singoli ogni volta che nella stringa non ci sono variabili**, e le virgolette solo quando serve l'interpolazione: rende subito evidente, leggendo il codice, quali stringhe sono "dinamiche". Te lo suggerisco come abitudine.

### I caratteri di escape

Dentro le virgolette PHP interpreta anche i **caratteri speciali** (o sequenze di escape), che iniziano con la barra rovesciata: i più usati sono `\n` (nuova riga, *new line*), `\t` (tabulazione) e `\f` (line feed). Sono gli stessi di Java, C e JavaScript. Dentro gli apici singoli, invece, non vengono interpretati.

```php
<?php

$name = 'Hidran';
$lastName = 'Arias';
$address = 'corso Racconigi';

echo "$name $lastName\n$address";
```

Codice completo: [listing-22.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-22.php)


Sulla console l'indirizzo va a capo. Nel browser, come abbiamo già visto, no: l'a capo c'è nel sorgente della pagina, ma non viene renderizzato. Qui torna utile una funzione nativa di PHP, **`nl2br()`** (*new line to break*), che trasforma ogni `\n` in un tag `<br>` HTML:

```php
<?php

echo nl2br("$name $lastName\n$address");
// Sorgente generato: Hidran Arias<br />
// corso Racconigi
```

Codice completo: [listing-23.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-23.php)


Ricaricando la pagina, il testo va a capo anche nel browser: guardando il sorgente con il browser (ad esempio in Chrome) vedrai che la new line è stata affiancata da un `<br />`.

## Accedere e modificare una stringa

Essendo una sequenza di caratteri, una stringa in PHP si comporta come un **array di caratteri**: possiamo accedere a ogni singolo carattere con le parentesi quadre e un indice che parte da **zero**.

```php
<?php

$name = 'Hidra';
echo $name[0];   // H
echo $name[4];   // a
```

Codice completo: [listing-24.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-24.php)


Possiamo anche *modificare* un carattere assegnando un nuovo valore a quella posizione. Supponiamo che io abbia scritto il mio nome senza accento e voglia sostituire l'ultima `a` con una `à`:

```php
<?php

$name = 'Hidra';
$name[4] = 'à';
echo $name;   // Hidr�  ← carattere corrotto!
```

Codice completo: [listing-25.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-25.php)


Il risultato è un carattere strano. Perché? Torniamo a quello che dicevo all'inizio: per PHP una stringa è una **sequenza di byte**. Nella codifica UTF-8 la `à` accentata occupa **due byte**, ma assegnandola alla posizione 4 stiamo sostituendo **un solo byte**. PHP prende quindi solo il primo byte del carattere accentato, e il risultato è una sequenza non valida. Verifichiamolo:

```php
<?php

$accented = 'à';
var_dump($accented);   // string(2) "à"  ← due byte!
```

Codice completo: [listing-26.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-26.php)


Lo stesso fenomeno si presenta con le funzioni di stringa native. **`strlen()`** restituisce la lunghezza di una stringa — ma in *byte*, non in caratteri:

```php
<?php

echo strlen('à');      // 2
echo mb_strlen('à');   // 1
```

Codice completo: [listing-27.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-27.php)


**`mb_strlen()`** invece risponde correttamente: un carattere. Le funzioni con il prefisso **`mb_`** appartengono alla libreria **mbstring** (*multibyte string*), aggiunta a PHP proprio per risolvere questo problema: PHP non ha il supporto UTF-8 nativo, e le sue funzioni native non sanno se quei byte rappresentano un carattere UTF-8, Latin-1 o altro — per loro sono byte e basta. La regola pratica: quando lavori con testo che può contenere accenti o caratteri non ASCII e ti servono lunghezze, sottostringhe e simili, usa le funzioni `mb_*` — di solito basta aggiungere il prefisso `mb_` al nome della funzione nativa corrispondente.

Te lo racconto perché è uno dei trucchi di PHP in cui all'inizio cascano tutti: conoscere come funzionano davvero le stringhe ti risparmia ore di debug. Nel Capitolo 11 approfondiremo le funzioni di manipolazione delle stringhe.

Un'ultima nota storica: nel vecchio codice troverai l'accesso ai caratteri anche con le parentesi graffe (`$name{4}`). Questa sintassi è stata deprecata in PHP 7.4 e **rimossa in PHP 8**: usa sempre le parentesi quadre.

## Convertire in stringa: il casting

Come per i numeri, in PHP di solito non serve fare il cast esplicito verso stringa: se facciamo `echo` di un numero, viene convertito automaticamente. Ci sono però alcuni valori — soprattutto `null` e i boolean — per cui bisogna sapere *come* avviene la conversione:

| Valore di partenza | Convertito in stringa |
|---|---|
| `null` | stringa vuota `''` |
| `true` | `'1'` |
| `false` | stringa vuota `''` |
| numero | la rappresentazione testuale del numero |
| array | la parola `Array` (con un avviso) |

Verifichiamo con il cast esplicito `(string)`:

```php
<?php

var_dump((string) null);    // string(0) ""
var_dump((string) true);    // string(1) "1"
var_dump((string) false);   // string(0) ""

$bool = true;
echo $bool;   // 1  (conversione automatica, senza cast)

$bool = false;
echo $bool;   // (non si vede niente: stringa vuota)
```

Codice completo: [listing-28.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-28.php)


Occhio al caso dell'array: se usiamo un array dove PHP si aspetta una stringa, come in un `echo`, otteniamo la parola `Array` e PHP ci segnala che stiamo facendo qualcosa di scorretto con l'avviso *Array to string conversion*:

```php
<?php

$ar = [1, 2, 3];
echo $ar;   // Warning: Array to string conversion — output: Array
```

Codice completo: [listing-29.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-29.php)


Approfitto per formalizzare la **concatenazione**: una stringa si concatena con un'altra stringa — o con qualsiasi valore, che verrà convertito in stringa — usando il **punto** (`.`). Non il `+` come in JavaScript: in PHP il più è solo aritmetico.

```php
<?php

$name = 'Hidran';
$bool = true;

echo $name . ' Arias';   // Hidran Arias
echo $name . $bool;      // Hidran1   (true → '1')

$bool = false;
echo $name . $bool;      // Hidran    (false → stringa vuota)
```

Codice completo: [listing-30.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-30.php)


Come vedi, nella concatenazione il boolean viene convertito in stringa in automatico, senza bisogno del cast esplicito: le regole sono sempre quelle della tabella qui sopra.

## Heredoc e nowdoc

Oltre ad apici e virgolette, PHP offre un terzo modo di rappresentare le stringhe: il costrutto **heredoc**. È molto utile quando dobbiamo scrivere testi lunghi, su più righe, con delle variabili dentro, senza stare a gestire virgolette e concatenazioni.

### La sintassi heredoc

Una heredoc si apre con **tre segni di minore** (`<<<`) seguiti da un **identificatore** a nostra scelta — ad esempio `EOD`, *end of data* — e si chiude ripetendo lo **stesso identificatore**, seguito dal punto e virgola. L'identificatore segue le stesse regole dei nomi di variabile (deve iniziare con una lettera o un underscore, poi lettere, numeri e underscore), senza il dollaro:

```php
<?php

$name = 'Hidran';
$lastName = 'Arias';
$address = 'corso Racconigi';

$data = <<<EOD
Il mio nome è $name <br>
Il mio cognome è $lastName <br>
Il mio indirizzo è $address
EOD;

echo $data;
```

Codice completo: [listing-31.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-31.php)


Output nel browser:

```text
Il mio nome è Hidran
Il mio cognome è Arias
Il mio indirizzo è corso Racconigi
```

Codice completo: [listing-32.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-32.txt)


Tra apertura e chiusura possiamo mettere tutto quello che vogliamo — anche una poesia — e le variabili vengono **interpolate** esattamente come dentro le virgolette.

### Array e oggetti dentro una heredoc

Dentro le virgolette e le heredoc si possono interpolare anche gli **array** e gli **oggetti** (li studieremo rispettivamente tra poco e nella Parte VII, ma un esempio serve a fissare la sintassi). Con un indice numerico non ci sono problemi:

```php
<?php

$accounts = [2, 3];

$data = <<<EOD
Il primo conto è $accounts[0]
EOD;

echo $data;   // Il primo conto è 2
```

Codice completo: [listing-33.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-33.php)


Se però la chiave è una stringa, scrivere gli apici dentro l'interpolazione semplice produce un **errore di sintassi**:

```php
$accounts['accountNumber'] = 223344;

// ERRORE di sintassi:
// $data = <<<EOD
// Il numero di conto è $accounts['accountNumber']
// EOD;
```

Codice completo: [listing-34.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-34.php)


Le soluzioni sono due: togliere gli apici dalla chiave (funziona, ma non mi piace), oppure — ed è quello che preferisco — mantenere gli apici e racchiudere l'intera espressione tra **parentesi graffe**:

```php
<?php

$accounts = [2, 3];
$accounts['accountNumber'] = 223344;

$data = <<<EOD
Il numero di conto è {$accounts['accountNumber']}
EOD;

echo $data;   // Il numero di conto è 223344
```

Codice completo: [listing-35.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-35.php)


Tra le graffe puoi mettere qualunque espressione valida di PHP, anche una semplice variabile come `{$address}` (in quel caso le graffe non servirebbero, ma PHP ne fa comunque il parsing). Attenzione solo a non annidare una variabile dentro l'altra nella stessa espressione semplice: se serve, chiudi e apri una nuova espressione tra graffe.

Con gli oggetti la sintassi con la freccia funziona direttamente; le graffe diventano necessarie solo per i casi più complessi, come la chiamata di un metodo:

```php
<?php

$object = new stdClass();
$object->name = 'Jim';

$data = <<<EOD
Il nome è $object->name
EOD;

echo $data;   // Il nome è Jim
```

Codice completo: [listing-36.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-36.php)


Per un utilizzo di base ricorda questo: variabile semplice o array con indice numerico → basta il nome; array con chiave stringa (con gli apici) o espressioni più complesse → parentesi graffe.

### La sintassi nowdoc

Il **nowdoc** è identico all'heredoc, con una differenza: l'identificatore di apertura va racchiuso tra **apici singoli**. E la differenza di comportamento è la stessa che c'è tra virgolette e apici singoli: **niente** di ciò che sta dentro viene interpretato.

```php
<?php

$name = 'Hidran';

$code = <<<'EOD'
Il mio nome è $name <br>
EOD;

echo $code;   // Il mio nome è $name <br>   (letterale!)
```

Codice completo: [listing-37.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-37.php)


A cosa serve? Ad esempio quando vogliamo mostrare del **codice PHP come testo** — in un tutorial, in una pagina che spiega come si crea una classe — senza che venga interpretato: dollari, variabili e a capo restano esattamente come li abbiamo scritti.

### Le novità di PHP 7.3

Fino a PHP 7.2 il marcatore di chiusura doveva stare **da solo, a inizio riga**, senza alcuna indentazione, pena un errore di sintassi. Da **PHP 7.3** in poi possiamo indentare il marcatore di chiusura, e l'indentazione del marcatore viene rimossa da tutte le righe del contenuto:

```php
<?php

function getList()
{
    $content = <<<EOD
        <ul>
            <li>uno</li>
            <li>due</li>
        </ul>
        EOD;

    return $content;
}

echo getList();
```

Codice completo: [listing-38.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-38.php)


Niente più marcatore appiccicato al margine sinistro in mezzo a codice indentato: l'editor non segnala errori e l'`echo` mostra regolarmente il contenuto. L'unica regola è che il contenuto non può essere indentato *meno* del marcatore di chiusura. Vale sia per heredoc che per nowdoc.

## Gli array: definizione e chiavi

Con questo paragrafo cominciamo lo studio degli **array**, una delle strutture più importanti di PHP. Un array è un insieme di dati che può funzionare come una mappa di coppie **chiave-valore**, come lista, come hash table, come stack, come coda, come dizionario. Insieme alle stringhe, gli array sono la parte del linguaggio da dominare alla perfezione: PHP porta con sé **centinaia di funzioni native** per processarli, e risolvendo problemi reali ci ritroveremo a usarle di continuo (il Capitolo 12 è dedicato proprio a questo).

### Creare un array

Ci sono due sintassi: il costrutto **`array()`**, che esiste fin dalle origini del linguaggio, e la **sintassi breve** con le parentesi quadre `[]`, che è quella che useremo:

```php
<?php

$ar = array('red', 'green', 'blue');   // sintassi storica
$ar = ['red', 'green', 'blue'];        // sintassi breve, equivalente
```

Codice completo: [listing-39.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-39.php)


Possiamo dichiarare le coppie chiave-valore esplicitamente, ma se non indichiamo le chiavi PHP le crea in automatico: **chiavi numeriche a partire da zero**. Verifichiamo con `var_dump()`:

```php
<?php

$ar = ['red', 'green', 'blue'];
var_dump($ar);
```

Codice completo: [listing-40.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-40.php)


```text
array(3) {
  [0]=>
  string(3) "red"
  [1]=>
  string(5) "green"
  [2]=>
  string(4) "blue"
}
```

Codice completo: [listing-41.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-41.txt)


`var_dump()` ci dice tutto: il tipo (array), la dimensione (3), ogni chiave e ogni valore con tipo e lunghezza. Esiste anche un'altra funzione molto comoda, **`print_r()`**, che mostra solo la struttura — chiavi e valori — senza i tipi:

```php
<?php

print_r($ar);
```

Codice completo: [listing-42.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-42.php)


```text
Array
(
    [0] => red
    [1] => green
    [2] => blue
)
```

Codice completo: [listing-43.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-43.txt)


A volte non ci interessa il tipo ma solo come è composto l'array, e `print_r()` è più leggibile. Nel resto degli esempi userò `var_dump()`, che dà la descrizione più completa.

### Aggiungere elementi e scegliere gli indici

A differenza di JavaScript, in PHP per aggiungere un elemento non è obbligatorio indicare la chiave: basta usare le **parentesi quadre vuote** e PHP prende l'indice numerico più alto già utilizzato e lo aumenta di uno:

```php
<?php

$ar = ['red', 'green', 'blue'];

$ar[] = 'pink';      // finisce alla posizione 3

$ar[9] = 'yellow';   // possiamo saltare direttamente alla posizione 9
$ar[] = 'magenta';   // il prossimo indice automatico è 10!
```

Codice completo: [listing-44.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-44.php)


Come vedi possiamo anche indicare noi la posizione, saltando dei valori: dopo aver messo `yellow` alla posizione 9, il contatore interno riparte da lì, e il successivo `[]` usa 10. Nulla ci vieta poi di riempire un "buco" indicando esplicitamente un indice non utilizzato, per esempio il 4 — e alla posizione 4 possiamo mettere qualsiasi valore, perfino **un altro array**:

```php
<?php

$ar[4] = [2, 4, 24, 44, 100];
```

Codice completo: [listing-45.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-45.php)


Ecco il nostro primo array dentro un array: ci torniamo nel paragrafo sugli array multidimensionali.

### Chiavi stringa e chiavi numeriche nello stesso array

PHP ci lascia usare **chiavi stringa** e chiavi numeriche nello stesso array, cosa che lo rende una mappa a tutti gli effetti:

```php
<?php

$ar['giallo'] = 'amarillo';   // giallo in spagnolo
$ar[] = 'sky';                // va alla posizione 11: il contatore numerico
                              // ignora completamente le chiavi stringa
```

Codice completo: [listing-46.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-46.php)


La chiave stringa non c'entra nulla con il contatore numerico: continuano ciascuno per conto proprio. Per leggere un valore basta usare la chiave con cui l'abbiamo inserito:

```php
<?php

echo $ar['giallo'];   // amarillo
```

Codice completo: [listing-47.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-47.php)


Nota che ho scritto la chiave tra **apici singoli**, seguendo la convenzione che ti ho suggerito per le stringhe: apici semplici quando non c'è nulla da interpolare.

### Le chiavi vanno sempre tra apici

Cosa succede se non mettiamo gli apici? Lo vedo scritto in tanto codice vecchio e trascurato:

```php
<?php

echo $ar[giallo];   // funziona... ma è un errore!
```

Codice completo: [listing-48.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-48.php)


In PHP 7 questo codice stampa comunque `amarillo`, ma PHP segnala di non aver trovato la **costante** `giallo` e di aver dedotto che intendevamo la stringa `'giallo'`. È un avviso che non blocca il codice, ma non va ignorato mai. In **PHP 8 non è più tollerato**: usare una chiave senza apici solleva un errore fatale (*Undefined constant*).

Perché era così pericoloso? Perché qualcuno potrebbe davvero definire una costante con quel nome. Guardiamo cosa succederebbe:

```php
<?php

define('giallo', 4);   // una costante di nome giallo che vale 4

print_r($ar[giallo]);
// PHP sostituisce la costante con il suo valore: $ar[4]
// e alla posizione 4 c'è... l'array [2, 4, 24, 44, 100]!
```

Codice completo: [listing-49.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-49.php)


PHP trova la costante `giallo`, vede che vale 4, e va a leggere la posizione 4 — dove c'è l'array annidato, non `amarillo`. Un bug subdolo e difficile da scovare. Morale: **metti sempre gli apici attorno alle chiavi stringa**.

### Come PHP converte le chiavi

Le chiavi di un array possono essere **soltanto interi o stringhe**, e PHP applica delle conversioni automatiche che è bene conoscere:

```php
<?php

$ar['5'] = 'cinque';   // la stringa "5" diventa la chiave INTERA 5
$ar['5.0'] = 'a';      // "5.0" NON è un intero: resta la stringa "5.0"
$ar['5.2'] = 'b';      // resta la stringa "5.2"
$ar[5.2] = 'c';        // float senza apici: TRONCATO alla chiave intera 5!
```

Codice completo: [listing-50.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-50.php)


Una stringa che contiene un intero "ben formato" viene convertita nel numero corrispondente; una stringa come `"5.0"` o `"5.2"` invece resta stringa. Ma un **float usato direttamente come chiave viene troncato**: si prende solo la parte intera, senza alcun errore. Immagina un array dove la chiave è un prezzo e il valore è la lista dei prodotti di un negozio con quel prezzo: se usi il float `5.2` come chiave, finisce tutto sotto la chiave `5`. Se vuoi mantenere la chiave decimale devi passarla esplicitamente come stringa, tra apici.

Infine, qualunque altro tipo usato come chiave — un array, un oggetto — produce un errore (*Illegal offset type*): l'editor te lo segnala ancora prima di eseguire.

```php
<?php

// $ar[['a']] = 'x';   // TypeError: Illegal offset type
```

Codice completo: [listing-51.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-51.php)


## Array multidimensionali

Il nostro `$ar` è già un array **multidimensionale**: alla posizione 4 contiene un altro array. Vediamo come si lavora con queste strutture annidate.

### Accedere agli elementi annidati

Per accedere a un elemento annidato si mettono in fila le parentesi quadre, un livello dopo l'altro. Alla posizione 4 abbiamo `[2, 4, 24, 44, 100]`; per leggere il quarto elemento (indice 3, contando da zero):

```php
<?php

echo $ar[4][3];   // 44
```

Codice completo: [listing-52.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-52.php)


Attenzione quando l'accesso avviene **dentro una stringa**. Con un array semplice l'interpolazione diretta funziona (`"$ar[2]"` stampa `blue`), ma con due livelli di indici no: serve racchiudere l'espressione tra **graffe**, come abbiamo visto per le heredoc:

```php
<?php

echo "{$ar[4][3]} <br>";   // 44 — senza graffe non verrebbe interpretato correttamente
```

Codice completo: [listing-53.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-53.php)


Aggiungiamo ora una chiave stringa che contiene un array con i giorni della settimana:

```php
<?php

$ar['GIORNI'] = ['lunedì', 'martedì'];

echo "{$ar['GIORNI'][1]} <br>";   // martedì
```

Codice completo: [listing-54.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-54.php)


Ricorda le graffe, e ricorda un'altra cosa: le chiavi sono **case-sensitive**. Se cerchiamo `giorni` in minuscolo, PHP non trova la chiave e segnala *Undefined array key "giorni"*:

```php
<?php

echo $ar['giorni'][1];   // Warning: chiave non trovata! 'giorni' ≠ 'GIORNI'
```

Codice completo: [listing-55.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-55.php)


### Modificare, aggiungere ed eliminare elementi

Per **modificare** un valore basta accedere alla sua chiave e assegnare: sovrascriviamo per esempio il valore di `'giallo'`, da `amarillo` a `yellow`:

```php
<?php

$ar['giallo'] = 'yellow';
```

Codice completo: [listing-56.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-56.php)


Per **aggiungere un elemento a un array annidato** possiamo usare la funzione nativa **`array_push()`**: le passiamo l'array da modificare e il valore da accodare:

```php
<?php

array_push($ar['GIORNI'], 'mercoledì');
var_dump($ar['GIORNI']);
// lunedì, martedì, mercoledì — mercoledì è andato alla posizione successiva (2)
```

Codice completo: [listing-57.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-57.php)


Per **eliminare** una chiave — e il suo valore — c'è **`unset()`**: le passiamo l'elemento da rimuovere.

```php
<?php

unset($ar['GIORNI']);   // l'intera chiave GIORNI sparisce dall'array
unset($ar[2]);          // togliamo anche 'blue', alla posizione 2
```

Codice completo: [listing-58.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-58.php)


Qui c'è un dettaglio importante: con le chiavi numeriche `unset()` **lascia un buco**. Le chiavi non vengono riorganizzate: dopo aver tolto la posizione 2 avremo 0, 1, 3, 9, 10... Vediamolo su un array pulito:

```php
<?php

$ar2 = ['a', 'b', 'c', 'd'];
unset($ar2[2]);   // togliamo 'c'

var_dump($ar2);
```

Codice completo: [listing-59.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-59.php)


```text
array(3) {
  [0]=>
  string(1) "a"
  [1]=>
  string(1) "b"
  [3]=>
  string(1) "d"
}
```

Codice completo: [listing-60.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-60.txt)


Le chiavi sono 0, 1 e **3**: il 2 è sparito e nessuno ha rinumerato. Se vogliamo di nuovo le chiavi ordinate 0, 1, 2, usiamo **`array_values()`**, che restituisce tutti i valori di un array reindicizzando le chiavi numeriche da zero:

```php
<?php

$ar2 = array_values($ar2);
var_dump($ar2);
// ora le chiavi sono 0, 1, 2
```

Codice completo: [listing-61.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-61.php)


`array_values()` è utile anche sul nostro array misto: chiamandola su `$ar` otteniamo un nuovo array dove ogni elemento — colori, array annidato, tutto — riceve una chiave numerica progressiva 0, 1, 2, 3... e le chiavi stringa spariscono. Ricordatela ogni volta che ti serve una copia di un array con le chiavi numeriche ordinate. Nel Capitolo 12 vedremo molte altre funzioni per manipolare gli array: aggiungere e togliere valori in testa e in coda, ordinarli, filtrarli e altro ancora.

## Le costanti: const e define

Una **costante**, come dice il nome, è un valore che non cambia. Pensiamo di nuovo al pi greco: se lo mettiamo in una variabile, nulla impedisce di sovrascriverlo per sbaglio.

```php
<?php

$pi = 3.1415;
echo $pi . PHP_EOL;

$pi = 1.718;          // lecito: è una variabile
echo $pi . PHP_EOL;   // il "pi greco" ora vale 1.718...
```

Codice completo: [listing-62.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-62.php)


(`PHP_EOL` è una costante predefinita di PHP che contiene il carattere di fine riga corretto per la piattaforma su cui gira lo script — e a fine paragrafo vedremo che è definita esattamente con gli strumenti che stiamo per studiare.)

### Dichiarare una costante con const

Per dichiarare una costante si usa la parola chiave **`const`**. Il nome segue le stesse regole delle variabili, con una differenza: **niente dollaro** — se provi a metterlo, l'editor ti segnala subito un errore di sintassi. Per convenzione i nomi delle costanti si scrivono **tutti in maiuscolo**, e se sono composti da più parole si separano con l'underscore (`TAX_RATE`):

```php
<?php

const PI = 3.1415;

echo PI;      // 3.1415
// PI = 3;    // ERRORE: non si può assegnare a una costante
```

Codice completo: [listing-63.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-63.php)


Una volta assegnato, il valore non può più cambiare: già l'editor segnala il tentativo di sovrascrittura, e in esecuzione otterremmo un errore. Il valore di una `const` può essere un letterale — un numero, una stringa — oppure una **espressione costante**, calcolabile al volo in fase di compilazione:

```php
<?php

const RESULT = 3 * 5;   // ok: espressione calcolabile subito
```

Codice completo: [listing-64.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-64.php)


Non può invece dipendere da qualcosa che si conosce solo a runtime: una chiamata a funzione, una lettura dal database. Dev'essere un valore determinabile nel momento in cui lo assegniamo.

Due anticipazioni. Primo: la stessa sintassi `const` la ritroveremo **dentro le classi** nella Parte VII, dove le costanti apparterranno alla classe invece che allo scope globale. Secondo: quando studieremo la visibilità vedremo che le variabili sono visibili solo nel contesto in cui nascono — dentro una funzione, una variabile esterna non si vede se non importata. Le **costanti invece sono globali**: una volta definite, sono visibili ovunque, anche dentro le funzioni.

### define e la verifica con defined

C'è un secondo modo, più vecchio, di definire una costante: la funzione **`define()`**, a cui passiamo il nome della costante come stringa e il valore:

```php
<?php

define('PI2', 3.1415);
echo PI2;   // 3.1415
```

Codice completo: [listing-65.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-65.php)


Attenzione però: se proviamo a definire due volte la stessa costante, l'editor non se ne accorge (per lui è una normale chiamata di funzione) e ce ne accorgiamo solo eseguendo, con il warning *Constant PI2 already defined*:

```php
<?php

define('PI2', 3.1415);
define('PI2', 3);   // Warning: Constant PI2 already defined
```

Codice completo: [listing-66.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-66.php)


Una curiosità storica: `define()` accettava un terzo parametro per rendere il nome della costante *case-insensitive*. È stato **deprecato in PHP 7.3 e rimosso in PHP 8**: oltre a non funzionare più, era anche pericoloso. I nomi delle costanti sono sempre case-sensitive.

Il vero punto di forza di `define()` è che si accompagna alla funzione **`defined()`**, che verifica se una costante è già stata definita. Possiamo così proteggere la definizione:

```php
<?php

if (!defined('PI2')) {
    define('PI2', 3.1415);
}
```

Codice completo: [listing-67.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-67.php)


Il punto esclamativo nega la condizione: "se `PI2` **non** è definita, definiscila". Eseguendo il codice una seconda volta, PHP non passa dalla `define()` e non c'è alcun errore.

### Array come costanti

Possiamo dichiarare come costante anche un **array** — cosa che nelle vecchie versioni di PHP 5 non era possibile (è arrivata con PHP 5.6 per `const` e con PHP 7 per `define()`):

```php
<?php

const PROVINCES = ['Torino', 'Milano'];

// PROVINCES[2] = 'Roma';   // ERRORE: non si può modificare una costante
// const PROVINCES = [];    // ERRORE: già definita

define('REGIONS', ['Piemonte', 'Lombardia']);
var_dump(REGIONS);
```

Codice completo: [listing-68.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-68.php)


Come per ogni costante, non possiamo né aggiungere elementi né riassegnarla: l'editor ce lo segnala subito. E occhio ad accedere a una costante che non esiste: nelle versioni molto vecchie di PHP il nome veniva silenziosamente trattato come stringa (con un avviso), ma nel PHP moderno otteniamo un **errore fatale** (*Undefined constant*). Un motivo in più per usare `defined()` quando c'è il dubbio.

Riassumendo, e ti do anche la mia preferenza personale: nel mio codice non uso quasi più `define()` — uso **`const`**, che è più corta da scrivere, viene capita dall'editor (che ci avvisa di sovrascritture e riassegnazioni prima ancora di eseguire) e lascia meno spazio a errori di battitura tra parentesi e apici. `define()` resta utile quando serve la definizione condizionale con `defined()`. E ricorda l'esempio di PHP stesso: la costante `PHP_EOL` che abbiamo usato prima è definita proprio così, nome in maiuscolo con underscore, valore uguale al carattere di fine riga della piattaforma.

## Verificare le variabili: isset, empty e is_null

Chiudiamo il capitolo con tre funzioni native che servono a rispondere a tre domande diverse su una variabile: è stata impostata? È vuota? È `null`? Sembrano simili, ma le differenze sono importanti — e le useremo in continuazione quando riceveremo dati dai form nella Parte IV.

### isset: la variabile è impostata?

**`isset()`** verifica se una variabile è stata impostata **e** se ha un valore diverso da `null`:

```php
<?php

if (isset($name)) {
    echo "$name esiste";
} else {
    echo 'La variabile non esiste';
}
// Output: La variabile non esiste
```

Codice completo: [listing-69.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-69.php)


Nota che `$name` non l'abbiamo nemmeno dichiarata, eppure `isset()` non solleva nessun avviso: risponde semplicemente `false`. Se assegniamo un valore qualsiasi — anche una stringa vuota, anche `0` — `isset()` risponde `true`. L'unico valore per cui risponde `false` su una variabile dichiarata è `null`.

### empty: la variabile è vuota?

**`empty()`** verifica se una variabile è "vuota". Ma cosa significa vuota per PHP? Una variabile è vuota quando **non è stata dichiarata** oppure quando il suo valore, **convertito in boolean, diventa `false`** — esattamente i valori falsy che abbiamo visto studiando il tipo boolean:

```php
<?php

if (empty($name)) {
    echo 'name è vuota';
} else {
    echo "name non è vuota ed è uguale a $name";
}
```

Codice completo: [listing-70.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-70.php)


Proviamo i vari casi:

```php
<?php

// $name mai dichiarata     → vuota (e nessun warning!)
$name = '';       // vuota
$name = 'Hidran'; // NON vuota
$name = 0;        // vuota
$name = '0';      // vuota — attenzione!
$name = 0.0;      // vuota
$name = null;     // vuota
$name = false;    // vuota
$name = [];       // vuota (array senza elementi)
```

Codice completo: [listing-71.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-71.php)


Due osservazioni. La prima: bisogna fare molta attenzione allo **zero**. `empty()` considera vuoti sia l'intero `0` sia la stringa `'0'`: quindi `isset()` direbbe che la variabile è impostata, ma `empty()` la dà come vuota. Se per te lo zero ha un significato — per esempio devi poter impostare un prezzo a zero — **non** usare `empty()`: verifica piuttosto che il valore non sia `null`, come vedremo subito.

La seconda: `empty()` su una variabile mai dichiarata **non genera nessun avviso**. Se invece provassimo un semplice `if ($name)` su una variabile non dichiarata, PHP segnalerebbe *Undefined variable* — un notice fino a PHP 7.4, un warning da PHP 8. Non è un errore che blocca l'esecuzione, e in un ambiente di produzione non si vedrebbe nemmeno, ma non va ignorato. `empty()` ci permette di fare la verifica in modo pulito.

### is_null: la variabile è null?

**`is_null()`** verifica una cosa sola: se la variabile ha il valore **`null`** — proprio `null`, non qualcosa che gli assomiglia:

```php
<?php

$name = null;

if (is_null($name)) {
    echo 'name è null';
} else {
    echo 'name non è null';
}
// Output: name è null
```

Codice completo: [listing-72.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-72.php)


Concettualmente `is_null()` è quasi il contrario di `isset()`: una variabile `null` non risulta impostata, e `!isset($name)` significa "è `null` oppure non è mai stata definita". C'è però una differenza pratica: se la variabile **non è mai stata dichiarata**, `is_null()` restituisce sì `true`, ma PHP segnala anche l'avviso *Undefined variable*; `isset()` invece non lo fa mai. Quindi usa `is_null()` quando sei sicuro che la variabile sia stata inizializzata — per esempio l'hai dichiarata tu e poi il valore arriva da un file o da una risorsa esterna — e vuoi solo sapere se contiene `null`.

Attenzione a non confondere `null` con la stringa vuota: sono concetti diversi.

```php
<?php

$name = '';
var_dump(is_null($name));   // bool(false): la stringa vuota NON è null

var_dump(null == '');       // bool(true)  — confronto debole: entrambi falsy
var_dump(null === '');      // bool(false) — tipi diversi!
```

Codice completo: [listing-73.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/it/parte-02/cap-07/listing-73.php)


Con il confronto a due uguali PHP fa il cast e `null` risulta uguale alla stringa vuota; con il confronto a tre uguali no, perché i tipi sono diversi. PHP in questo può confondere: tieni separati i tre concetti — *impostata*, *vuota*, *null*.

### Quale funzione usare?

Ecco la tabella riassuntiva che uso come regola pratica:

| Domanda | Funzione | Note |
|---|---|---|
| La variabile esiste e non è `null`? | `isset()` | mai avvisi; `true` per qualsiasi valore tranne `null` |
| La variabile è vuota (falsy)? | `empty()` | mai avvisi; ma `0` e `'0'` risultano vuoti |
| La variabile vale esattamente `null`? | `is_null()` | avviso se la variabile non è dichiarata |

Se ti interessa solo sapere che la variabile è impostata, usa `isset()`. Se ti interessa che sia impostata *e* non vuota — e per te stringa vuota, `false`, zero e array vuoto contano come "niente" — usa tranquillamente `empty()`. Se lo zero è un valore legittimo nel tuo contesto, evita `empty()` e verifica con `is_null()` o con un confronto esplicito.

## In sintesi

- Una **variabile** è un'area di memoria con un nome che fa da etichetta: in PHP inizia con `$`, seguito da una lettera o underscore, poi lettere, numeri e underscore. Usa nomi parlanti e la convenzione camelCase; PHP è a tipizzazione dinamica, quindi il tipo può cambiare a runtime.
- I numeri sono **integer** o **float**; gli interi si possono scrivere anche in ottale (`0`), esadecimale (`0x`) e binario (`0b`). PHP converte automaticamente le stringhe numeriche nelle operazioni, ma è buona pratica rispettare i tipi.
- Il tipo **boolean** ha solo `true` e `false`, ma qualsiasi valore può essere convertito: memorizza la lista dei valori falsy (`false`, `0`, `0.0`, `''`, `'0'`, `[]`, `null`) — tutto il resto è vero. Dai form invia `0`/`1`, non le stringhe `'true'`/`'false'`.
- Le **stringhe** sono sequenze di byte: gli apici singoli non interpolano le variabili, le virgolette sì (insieme agli escape come `\n`). Per i caratteri multibyte (accenti, UTF-8) usa le funzioni `mb_*`: `strlen()` conta i byte, `mb_strlen()` i caratteri.
- Nel casting verso stringa: `null` e `false` diventano stringa vuota, `true` diventa `'1'`, un array diventa la parola `Array` (con avviso). La concatenazione si fa con il **punto**, non con il `+`.
- **Heredoc** (`<<<EOD`) interpola variabili, array e oggetti (con le graffe per le espressioni complesse); **nowdoc** (`<<<'EOD'`) non interpreta nulla. Da PHP 7.3 il marcatore di chiusura può essere indentato.
- Gli **array** accettano chiavi intere e stringa nello stesso array; `[]` accoda usando l'indice numerico più alto + 1. Metti sempre gli apici alle chiavi stringa; ricorda che i float come chiave vengono troncati e che `unset()` lascia buchi negli indici numerici — `array_values()` li reindicizza.
- Le **costanti** si definiscono con `const` (preferibile) o `define()`; niente `$`, nome in maiuscolo per convenzione, valore immutabile e calcolabile in fase di compilazione, array ammessi. `defined()` verifica l'esistenza; le costanti sono visibili ovunque.
- **`isset()`** dice se una variabile è impostata e non `null`; **`empty()`** se è falsy (occhio allo zero!); **`is_null()`** se vale esattamente `null`. Nessuna delle prime due genera avvisi su variabili non dichiarate.
