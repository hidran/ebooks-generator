# 8. Gli operatori

Dopo aver imparato a dichiarare variabili e a riconoscere i tipi di dato nel Capitolo 7, è il momento di farli lavorare insieme. Gli **operatori** sono i simboli che ci permettono di assegnare valori, fare calcoli e — soprattutto — confrontare dati tra loro: sono i mattoni con cui costruiremo le condizioni e i cicli del Capitolo 9.

In questo capitolo vedremo gli operatori di assegnamento e quelli aritmetici, l'operatore esponenziale, l'intera famiglia degli operatori di confronto (con un'attenzione particolare a come PHP confronta numeri e stringhe, un comportamento cambiato in modo importante con PHP 8), l'operatore spaceship, il ternario e il null coalescing, fino all'assegnazione con null coalescing introdotta in PHP 7.4. Sono argomenti che sembrano semplici, ma nascondono alcune delle trappole più classiche di PHP: conoscerle bene ti eviterà bug difficili da scovare.

## L'operatore di assegnamento

Quando scriviamo:

```php
<?php

$a = 5;
$b = 8;
```

Codice completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-01.php)


sembra la matematica di sempre: stiamo assegnando il valore `5` alla variabile `$a` e il valore `8` alla variabile `$b`. (Ricorda, dal Capitolo 7, che i nomi delle variabili sono *case sensitive*: `$a` e `$A` sono due variabili diverse.)

In realtà l'**operatore di assegnamento** `=` fa qualcosa di più preciso: prende l'**espressione** che si trova alla sua destra, la valuta completamente e solo alla fine assegna il risultato alla variabile a sinistra. Con un valore letterale come `5` non c'è niente da calcolare, ma guarda questo caso:

```php
$c = $a + $b;
echo $c; // 13
```

Codice completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-02.php)


Qualcuno potrebbe pensare "assegno `$a` a `$c` e poi sommo `$b`". No: prima viene eseguita tutta l'operazione a destra (`$a + $b`, cioè `5 + 8`), e poi il risultato `13` viene assegnato a `$c`. Il concetto deve essere chiaro, perché è alla base di tutto ciò che riguarda la **precedenza degli operatori** che vedremo tra poco.

## Gli operatori aritmetici

Per gli operatori matematici la precedenza è quella che abbiamo studiato a scuola. L'operatore di **moltiplicazione** è l'asterisco `*`, e moltiplicazione e divisione hanno precedenza su addizione e sottrazione:

```php
$c = $a + $b * 5;
echo $c; // 45
```

Codice completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-03.php)


Prima viene calcolato `$b * 5` (cioè `8 * 5 = 40`) e poi viene sommato `$a`: `40 + 5 = 45`.

Come in matematica, possiamo cambiare la precedenza con le **parentesi tonde**:

```php
$c = ($a + $b) * 5;
echo $c; // 65
```

Codice completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-04.php)


Ora prima sommiamo `$a + $b` (che fa `13`) e poi moltiplichiamo per `5`, ottenendo `65`.

Per la **divisione** vale lo stesso discorso, ma al posto dell'asterisco usiamo la barra `/`:

```php
$c = ($a + $b) / 5;
echo $c; // 2.6
```

Codice completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-05.php)


Nota che il risultato è un valore decimale (un float), anche se gli operandi erano interi.

### L'operatore modulo

C'è poi un operatore che a scuola non si usa con questo nome: il **modulo** `%`, che restituisce il **resto** della divisione tra due numeri interi. Se scrivo `25 / 8` faccio una divisione normale; se invece uso la percentuale sto chiedendo: "quanto è il resto di questa divisione?"

```php
$d = 25 % 8;
var_dump($d); // int(1)
```

Codice completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-06.php)


Il risultato è `1`, perché `8 * 3 = 24` e ne rimane appunto uno.

Riassumendo, gli operatori aritmetici di base di PHP sono:

| Operatore | Operazione | Esempio |
|---|---|---|
| `+` | Addizione | `5 + 8` → `13` |
| `-` | Sottrazione | `8 - 5` → `3` |
| `*` | Moltiplicazione | `8 * 5` → `40` |
| `/` | Divisione | `13 / 5` → `2.6` |
| `%` | Modulo (resto) | `25 % 8` → `1` |
| `**` | Elevamento a potenza | `2 ** 4` → `16` |

Nelle librerie matematiche di PHP troviamo molte altre funzioni (conversioni decimale/binario, calcoli più precisi e così via), ma questi sono gli operatori fondamentali.

## L'operatore esponenziale

Prima della versione 5.6 di PHP, per elevare un numero a una certa potenza bisognava usare la funzione `pow()`, passando la base e l'esponente:

```php
$result = pow(2, 6);
echo $result; // 64
```

Codice completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-07.php)


Puoi provarlo subito dalla console: se hai PHP installato, salva il codice in un file e lancialo con `php index.php` (o il nome che hai dato al file).

Da PHP 5.6 in poi esiste un modo più semplice e più chiaro: l'**operatore esponenziale** `**`, cioè due asterischi, presente anche in altri linguaggi:

```php
$result = 2 ** 6;
echo $result; // 64
```

Codice completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-08.php)


`2 ** 6` significa "due alla sesta potenza" e funziona esattamente come `pow(2, 6)`. Certamente possiamo continuare a usare `pow()`, ma con l'operatore esponenziale la sintassi è più corta e leggibile.

### Attenzione all'associatività

C'è però una cosa da tenere presente: l'ordine di valutazione. L'operatore `**` è **associativo a destra**, al contrario della maggior parte degli operatori aritmetici che si valutano da sinistra a destra. Cosa pensi che venga fuori da questa espressione?

```php
$result = 2 ** 3 ** 2;
echo $result; // 512
```

Codice completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-09.php)


Se si valutasse da sinistra a destra sarebbe `(2 ** 3) ** 2`, cioè `8` al quadrato: `64`. Invece, con l'associatività a destra, viene calcolato prima `3 ** 2` (che fa `9`) e poi `2 ** 9`, cioè `512`.

Il consiglio, quando combini `**` con altri operatori, è di consultare sempre la tabella delle precedenze del manuale di PHP oppure — molto meglio — di indicare esplicitamente l'ordine con le parentesi tonde: così eviti i problemi e non devi ricordarti a memoria quale operatore ha la precedenza più alta.

### La radice quadrata

E se volessimo l'operazione inversa, la radice quadrata? In questo caso non c'è un operatore, ma una funzione: `sqrt()` (da *square root*, radice quadrata):

```php
echo sqrt(16); // 4
```

Codice completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-10.php)


La radice quadrata di `16` è `4`, cioè il contrario dell'elevamento a potenza che abbiamo appena fatto.

## Gli operatori di confronto

Gli **operatori di confronto** ci permettono di confrontare due valori: sapere se sono uguali, diversi, se uno è maggiore o minore dell'altro, un po' come abbiamo studiato in matematica. Il risultato di un confronto è sempre un valore **booleano**: `true` o `false`.

C'è però una caratteristica di PHP da tenere sempre presente: quando confronta due valori, può fare prima il **cast** (la conversione di tipo) degli operandi. Ed è qui che nascono le sorprese.

### Uguale e identico

In PHP bisogna distinguere tra "uguali" e "strettamente uguali" (o **identici**, come li chiamo io). Guarda queste due variabili, dove `$a` è una stringa e `$b` è un numero:

```php
$a = '1';
$b = 1;

$c = $a == $b;

var_dump($a); // string(1) "1"
var_dump($b); // int(1)
var_dump($c); // bool(true)
```

Codice completo: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-11.php)


Con il doppio uguale `==` PHP vede che il primo valore è una stringa e il secondo un integer, converte la stringa `'1'` nel numero `1` (come abbiamo visto nel Capitolo 7 parlando di conversioni) e poi confronta: sono uguali, quindi `true`.

Se invece vogliamo verificare che due valori siano uguali **e anche dello stesso tipo** — cioè strettamente uguali — usiamo tre segni uguale `===`:

```php
var_dump($a === $b); // bool(false)
```

Codice completo: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-12.php)


Il risultato è `false`: hanno lo stesso valore, ma non lo stesso tipo (una è una stringa, l'altro un integer). Quindi: tre segni uguale quando vogliamo verificare valore **e** tipo, due segni uguale quando ci interessa solo il valore.

### Il caso di null

Un caso in cui la differenza si vede ancora meglio è `null`. Qui `$a` non ha proprio un valore, mentre `$b` vale zero:

```php
$a = null;
$b = 0;

var_dump($a == $b);  // bool(true)
var_dump($a === $b); // bool(false)
```

Codice completo: [listing-13.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-13.php)


Ricordi la tabellina del Capitolo 7? Per PHP tutto ciò che è `0`, `null`, la stringa vuota `''`, `'0'` o un array vuoto viene convertito a `false`; tutto il resto a `true`. Quando confrontiamo `null == 0`, PHP fa il cast e li considera uguali. Ma `null === 0` è `false`: `null` è `null`, e zero è un integer — non sono identici, sono solo uguali di valore.

Altri confronti interessanti con il doppio uguale:

```php
var_dump(null == false); // bool(true)  — il cast li rende uguali
var_dump(null == '');    // bool(true)  — la stringa vuota "vale" null
var_dump(null == '0');   // bool(false) — la stringa '0' NON è uguale a null
```

Codice completo: [listing-14.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-14.php)


### Perché è importante: l'esempio del prezzo

Ogni volta che confronti due valori in uguaglianza, usa i tre simboli `===` per verificare anche il tipo: eviterai errori subdoli. Perché magari lo zero è un valore legittimo — ad esempio il prezzo di un prodotto — e il tuo codice lo scarta senza volerlo. Immagina di dover aggiornare il prezzo di un articolo in un e-commerce:

```php
$price = 0;

if ($price) {
    // qui eseguiremmo la query di aggiornamento
    echo 'Prezzo aggiornato';
} else {
    echo 'Prezzo non aggiornato';
}
// Output: Prezzo non aggiornato
```

Codice completo: [listing-15.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-15.php)


L'`if` (che studieremo a fondo nel Capitolo 9) valuta l'espressione al suo interno come booleano: `$price` vale `0`, il cast dà `false`, e la query di aggiornamento non verrebbe mai eseguita. Un bug bello e buono, perché zero è un prezzo valido!

La soluzione è verificare esplicitamente che il prezzo sia diverso da `null`, con un confronto stretto:

```php
if ($price !== null) {
    echo 'Prezzo aggiornato';
} else {
    echo 'Prezzo non aggiornato';
}
// Output: Prezzo aggiornato
```

Codice completo: [listing-16.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-16.php)


Ora la condizione passa, perché `0` è un valore presente: è diverso da `null` sia per valore percepito che per tipo. Fai molta attenzione a questi casi: se non verifichi con il confronto stretto, per PHP zero, `null` e la stringa vuota si equivalgono.

### Diverso e non identico

Il contrario dell'uguaglianza si esprime con il punto esclamativo. `!=` significa "diverso" (solo di valore, con cast), mentre `!==` significa "non identico": diverso di valore **o** di tipo. Riprendiamo `null` e la stringa vuota:

```php
$a = null;
$b = '';

var_dump($a != $b);  // bool(false) — dopo il cast risultano uguali
var_dump($a !== $b); // bool(true)  — uno è null, l'altra è una stringa
```

Codice completo: [listing-17.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-17.php)


Con `!=` il risultato è `false`: PHP fa il cast, li vede uguali, quindi "non sono diversi". Con `!==` invece è `true`, perché i tipi sono differenti. Esiste anche la forma alternativa `<>` per "diverso", ma io uso sempre `!=`.

Ecco la tabellina riassuntiva, che trovi anche nel manuale di PHP:

| Esempio | Nome | Risultato |
|---|---|---|
| `$a == $b` | Uguale | `true` se `$a` è uguale a `$b` dopo il cast dei tipi |
| `$a === $b` | Identico | `true` se uguali e dello stesso tipo |
| `$a != $b` | Diverso | `true` se diversi dopo il cast dei tipi |
| `$a <> $b` | Diverso | Come `!=` |
| `$a !== $b` | Non identico | `true` se diversi di valore o di tipo |
| `$a < $b` | Minore | `true` se `$a` è strettamente minore di `$b` |
| `$a > $b` | Maggiore | `true` se `$a` è strettamente maggiore di `$b` |
| `$a <= $b` | Minore o uguale | `true` se `$a` è minore o uguale a `$b` |
| `$a >= $b` | Maggiore o uguale | `true` se `$a` è maggiore o uguale a `$b` |

### Confrontare le stringhe

E le stringhe? Quando i due operandi sono entrambi stringhe, il confronto avviene byte per byte, sul valore ordinale di ciascun byte:

```php
var_dump('a' != 'b'); // bool(true)  — sono diverse
var_dump('a' == 'b'); // bool(false) — non sono uguali
var_dump('a' !== 'b'); // bool(true) — stesso tipo, ma valori diversi
```

Codice completo: [listing-18.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-18.php)


Quando confrontiamo stringhe con stringhe non ci sono problemi: anche il doppio uguale va bene, perché i tipi coincidono già. Il problema, come abbiamo visto, è quando i tipi sono misti: stringa vuota, zero, `null`.

### Maggiore, minore e i loro amici

Per `>`, `<`, `>=` e `<=` vale quanto già sappiamo dalla matematica; anche questi operatori restituiscono sempre un booleano:

```php
$d = 0;
$e = 1;

$f = $d > $e;
var_dump($f);       // bool(false) — zero non è maggiore di uno

var_dump($d < $e);  // bool(true)  — zero è minore di uno
var_dump($d <= $e); // bool(true)  — è minore, quindi anche "minore o uguale"
var_dump(1 <= 1);   // bool(true)  — non è minore, ma è uguale
var_dump(2 <= 1);   // bool(false)
var_dump(2 >= 1);   // bool(true)
```

Codice completo: [listing-19.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-19.php)


Dipende da cosa vuoi verificare: se ti basta che sia "maggiore o uguale" usa `>=`; se vuoi che sia strettamente maggiore, usa solo `>`.

A cosa servono questi operatori nella pratica? A costruire condizioni sui dati immessi dall'utente o letti dal database. Un esempio classico:

```php
$age = 16;

if ($age >= 18) {
    echo 'Sei maggiorenne';
} else {
    echo 'Sei minorenne';
}
// Output: Sei minorenne
```

Codice completo: [listing-20.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-20.php)


Con `$age = 16` il programma stampa "Sei minorenne"; se metti `18`, la condizione passa (proprio grazie all'"o uguale") e stampa "Sei maggiorenne".

Attenzione a un errore di battitura comunissimo: si scrive **prima** il segno di maggiore/minore e **poi** l'uguale (`>=`, `<=`). Se scrivi `=>` PHP non lo interpreta come confronto — quella sequenza ha tutt'altro significato (la usaremo per gli array) — e otterrai un errore.

## Confrontare numeri e stringhe: cosa cambia con PHP 8

C'è un comportamento molto comune di PHP che è cambiato in modo significativo tra PHP 7 e PHP 8, e riguarda proprio il confronto debole (`==`) tra una stringa e un numero. Se devi migrare del codice da PHP 7 a PHP 8, questo paragrafo ti riguarda da vicino.

Partiamo da un caso che non cambia:

```php
var_dump(0 == '0'); // bool(true) — in tutte le versioni
```

Codice completo: [listing-21.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-21.php)


`'0'` è una **stringa numerica**: contiene un numero. Anche `'0.0'` lo è. Quando la stringa è numerica, il confronto con un numero funziona come ti aspetti, prima e dopo PHP 8.

La differenza sta in *come* PHP esegue il confronto quando la stringa **non** è numerica:

- **Prima di PHP 8**: PHP faceva il cast della stringa a numero e poi confrontava i due numeri. Una stringa numerica può avere degli spazi davanti; PHP la leggeva dall'inizio, trovava il numero e scartava tutto quello che seguiva (qualsiasi carattere che non fosse una cifra o il punto decimale). E una stringa che non cominciava con un numero veniva convertita... in `0`.
- **Da PHP 8**: se la stringa non è numerica, PHP fa l'opposto — converte il *numero* in stringa e confronta le due stringhe.

Le conseguenze si vedono subito in questa tabellina:

| Confronto | PHP 7.x | PHP 8+ |
|---|---|---|
| `0 == "0"` | `true` | `true` |
| `0 == "0.0"` | `true` | `true` |
| `0 == "foo"` | `true` | `false` |
| `0 == ""` | `true` | `false` |
| `42 == " 42"` | `true` | `true` |
| `42 == "42abc"` | `true` | `false` |

Prima di PHP 8, `0 == "foo"` era `true`: la stringa `"foo"` non comincia con un numero, veniva convertita a `0`, e zero è uguale a zero. Non ti dico quanti bug ho dovuto risolvere per questo problema. Lo stesso valeva per la stringa vuota. E `42 == "42abc"` era `true` perché PHP leggeva `42` e scartava il resto; con PHP 8 è `false`. Invece `" 42"` con gli spazi davanti resta `true` in entrambe le versioni: gli spazi (anche dopo il numero, da PHP 8) sono ammessi in una stringa numerica.

### Provare i confronti con versioni diverse di PHP

Per fare queste prove ti consiglio un sandbox online come **onlinephpfunctions.com**: puoi incollare del codice, eseguirlo e scegliere con quale versione di PHP provarlo. Iniziamo con qualche `var_dump()`, che mostra il risultato dell'operazione e il tipo che ritorna:

```php
var_dump(4 == 4);    // bool(true)
var_dump(4 == '4');  // bool(true) — stringa numerica
var_dump(4 == ' 4'); // bool(true) — e nessun warning per lo spazio
```

Codice completo: [listing-22.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-22.php)


Certamente, nel mondo reale questi valori arrivano dentro variabili. Immagina di avere un id atteso e un valore che ritorna da una chiamata o da un form: tutto quello che arriva dal web arriva **in forma di stringa** (lo vedremo bene nel Capitolo 13 sulle superglobali):

```php
$id = 4;       // il valore che ci aspettiamo: un integer
$result = '4'; // il valore arrivato da un form: sempre una stringa

var_dump($result);         // string(1) "4"
var_dump($id == $result);  // bool(true)
var_dump($id === $result); // bool(false) — tipi diversi
```

Codice completo: [listing-23.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-23.php)


Se vogliamo il confronto strettamente uguale, possiamo fare prima il cast a integer, visto che ci aspettiamo un integer:

```php
var_dump($id === (int) $result); // bool(true)
```

Codice completo: [listing-24.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-24.php)


A questo punto potresti dirmi: "ma perché complicarci la vita? Faccio sempre il cast e confronto con `===`, e basta". Il problema è che in PHP esistono costrutti e funzioni interne che eseguono il confronto debole *per conto loro*, senza che tu possa scegliere. Un esempio è lo `switch`, che confronta i suoi `case` con l'uguaglianza debole `==`, mentre il più recente `match` usa il confronto stretto `===` (vedremo entrambi nel Capitolo 9). Con lo `switch`, che il valore sia `'4'` come stringa o `4` come numero fa lo stesso: la conversione avviene implicitamente.

### Il caso di in_array()

Un altro caso è la funzione `in_array()`, che verifica se un valore esiste dentro un array (la incontreremo di nuovo nel Capitolo 12; intanto puoi guardarla nel manuale di PHP). Accetta tre parametri: cosa cercare, dove cercarlo, e se il confronto deve essere stretto o no (il terzo parametro è `false` per default, quindi confronto debole).

```php
$data = [4, 5, 'php'];

var_dump(in_array('5a', $data)); // PHP 7: bool(true) — PHP 8: bool(false)
var_dump(in_array(' 5', $data)); // bool(true) in entrambe (solo spazi)
var_dump(in_array(0, $data));    // PHP 7: bool(true)! — PHP 8: bool(false)
```

Codice completo: [listing-25.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-25.php)


Il primo caso: in PHP 7 la stringa `'5a'` veniva convertita a numero — trovava il `5`, scartava il resto — quindi la "trovava" nell'array; in PHP 8 no. Con soli spazi (`' 5'`) funziona in entrambe le versioni.

Ma il caso davvero insidioso è il terzo: cerchiamo lo `0` in un array che, come puoi vedere, **non contiene alcuno zero**. In PHP 7 il risultato era `true`! Perché? PHP confrontava `0` con `4`: diversi. Poi `0` con `5`: diversi. Poi `0` con la stringa `'php'`: e una stringa non numerica, convertita a numero, dà `0`. Quindi `0 == 0` → trovato. Un bug tremendo, perché PHP ci diceva di sì mentre lo zero nell'array non c'è. Da PHP 8 questo non succede più.

In ogni caso, con `in_array()` possiamo (e in genere dobbiamo) passare il terzo parametro a `true` per forzare il confronto stretto, che dà il risultato corretto in tutte le versioni:

```php
var_dump(in_array('5a', $data, true)); // bool(false) ovunque
var_dump(in_array(0, $data, true));    // bool(false) ovunque
```

Codice completo: [listing-26.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-26.php)


Morale: se stai migrando codice da PHP 7 a PHP 8, controlla tutti i punti in cui confronti numeri e stringhe con `==`, `switch` o funzioni come `in_array()`. Dove puoi, fai il cast esplicito e confronta strettamente; dove non puoi, tieni conto di questa tabella.

## L'operatore spaceship

Passiamo ora a operatori che di sicuro non abbiamo studiato in algebra elementare, ma che esistono in PHP come in altri linguaggi. Il primo, introdotto con PHP 7, è l'operatore **spaceship** `<=>` — la "navicella spaziale", per via della forma.

Cosa fa? Confronta "minore, uguale e maggiore" in un colpo solo: tre confronti in uno. Restituisce:

- `-1` se il primo operando è **minore** del secondo;
- `0` se sono **uguali**;
- `1` se il primo è **maggiore** del secondo.

Verifichiamo:

```php
$g = 0;
$h = 1;

$i = $g <=> $h;
var_dump($i); // int(-1) — il primo valore è minore del secondo
```

Codice completo: [listing-27.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-27.php)


(Se il tuo editor segnala `<=>` come errore, controlla che il linting sia impostato su PHP 7 o superiore: il codice è perfettamente valido.)

Se i due valori sono uguali otteniamo zero, e se il primo è maggiore otteniamo uno:

```php
var_dump(1 <=> 1); // int(0) — sono uguali
var_dump(2 <=> 1); // int(1) — il primo è maggiore
```

Codice completo: [listing-28.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-28.php)


Funziona sia con variabili che con valori letterali. E a cosa serve? Con una sola espressione ottengo un valore che mi dice *che relazione c'è* tra i due operandi, e posso poi smistare i tre casi con un `if`/`elseif`/`else` (o con uno `switch`, che studieremo nel Capitolo 9). Anticipo la struttura perché è molto semplice da capire:

```php
$g = 2;
$h = 1;

$i = $g <=> $h;

if ($i === 0) {
    echo 'g e h sono uguali';
} elseif ($i === -1) {
    echo 'g è minore di h';
} else {
    echo 'g è maggiore di h';
}
// Output: g è maggiore di h
```

Codice completo: [listing-29.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-29.php)


Con `$g = 1` stamperebbe "g e h sono uguali", con `$g = 0` stamperebbe "g è minore di h". È un operatore molto comodo: con una sola condizione ho tutto quello che mi serve.

## L'operatore ternario

Un altro operatore da conoscere è il **ternario**, che si chiama così perché lavora con tre parti:

```text
condizione ? valore1 : valore2
```

Codice completo: [listing-30.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-30.txt)


Se la condizione è vera (`true`), l'espressione ritorna `valore1`; altrimenti ritorna `valore2`. Vediamolo in pratica:

```php
$val1 = 1;
$val2 = 1;

$ternary = ($val1 === $val2) ? 'sono uguali' : 'sono diversi';
echo $ternary; // sono uguali
```

Codice completo: [listing-31.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-31.php)


Due consigli di scrittura. Primo: quando la condizione è un'espressione (come qui), racchiudila sempre tra parentesi tonde — se è un singolo valore puoi anche ometterle, ma con le tonde eviti qualsiasi problema di precedenza tra gli operatori di PHP. Secondo: per abitudine e correttezza, uso gli apici singoli per le stringhe che non contengono variabili, come ti ho mostrato nel Capitolo 6.

Il ternario è l'equivalente compatto di un `if`/`else`:

```php
if ($val1 === $val2) {
    echo 'sono uguali';
} else {
    echo 'sono diversi';
}
```

Codice completo: [listing-32.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-32.php)


Quale dei due è meglio? Dipende. Per un'espressione semplice come questa ti consiglio il ternario: più corto, immediato. Se invece la logica si complica, meglio un `if`/`else` esplicito, magari appoggiando il risultato a una variabile: è un pochino più chiaro da leggere. Non è questione di velocità, ma di leggibilità.

Nota che nell'esempio ho usato tre segni uguale, perché voglio verificare anche il tipo. Prova a cambiare i valori: con `$val2 = 20` otteniamo "sono diversi"; con `$val2 = '1'` (stringa) e il confronto stretto `===` otteniamo "sono diversi", ma se passiamo al doppio uguale `==` torna "sono uguali" — è sempre la stessa storia del cast che abbiamo visto sopra.

## L'operatore null coalescing

Con PHP 7 è arrivato anche l'operatore **null coalescing** `??`, due punti interrogativi. Tradotto liberamente significa: "dammi il primo di tutti i valori che ti elenco che non sia `null`". È simile al ternario, ma invece di valutare una condizione vera/falsa, scarta i `null`.

Possiamo usare valori letterali:

```php
$result = null ?? 2 ?? 3;
var_dump($result); // int(2)
```

Codice completo: [listing-33.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-33.php)


Il primo valore è `null`, quindi viene scartato; il secondo è `2`, che non è `null`: è lui il risultato. Se anche il secondo fosse `null`, otterremmo `3`:

```php
$result = null ?? null ?? 3;
var_dump($result); // int(3)
```

Codice completo: [listing-34.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-34.php)


E naturalmente funziona anche con le variabili — non importa che siano variabili o valori letterali:

```php
$val1 = null;
$val2 = 10;

$result = $val1 ?? $val2;
var_dump($result); // int(10)
```

Codice completo: [listing-35.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-35.php)


È l'operatore perfetto per assegnare valori di default, come vedremo subito.

## Assegnazione con null coalescing (PHP 7.4)

Riprendiamo il null coalescing con un caso pratico. Immagina di leggere il cognome di un utente dal database, e di non sapere se la colonna `last_name` contiene un valore oppure `null`. Vogliamo assegnare un default in quel caso:

```php
$lastName = null; // simuliamo la colonna letta dal database

$lastName = $lastName ?? 'N/A';
echo $lastName; // N/A
```

Codice completo: [listing-36.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-36.php)


Stiamo dicendo: "`$lastName` sarà uguale al valore che ha già, ma se quel valore è `null`, allora usa `'N/A'`". Funziona, però c'è una ripetizione: la variabile compare due volte.

Da PHP 7.4 esiste un modo più corto: l'operatore di **assegnazione con null coalescing** `??=`:

```php
$lastName ??= 'N/A';
echo $lastName; // N/A
```

Codice completo: [listing-37.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/it/parte-02/cap-08/listing-37.php)


Il significato è identico: "mantieni il valore che c'è già in `$lastName`; ma se è `null`, assegna il valore di default". Se la variabile ha già un valore, non succede niente e rimane com'è; altrimenti riceve il default.

Questo operatore è comodissimo per fare pulizia sui valori: ogni volta che temiamo che un valore possa essere `null` — una colonna del database, un parametro opzionale — gli diamo un default con una sola riga.

## In sintesi

- L'operatore di assegnamento `=` valuta **prima** tutta l'espressione a destra e **poi** assegna il risultato alla variabile a sinistra.
- Gli operatori aritmetici sono `+`, `-`, `*`, `/`, il modulo `%` (resto della divisione) e l'esponenziale `**`; moltiplicazione e divisione hanno precedenza su addizione e sottrazione, e le parentesi tonde cambiano l'ordine di valutazione.
- `**` (da PHP 5.6, in alternativa a `pow()`) è associativo a destra: `2 ** 3 ** 2` fa `512`, non `64`. Nel dubbio, usa le parentesi. Per la radice quadrata c'è la funzione `sqrt()`.
- `==` confronta solo i valori (con cast automatico dei tipi), `===` confronta valori **e** tipi; `!=` significa diverso, `!==` non identico. Preferisci sempre i confronti stretti: per PHP `0`, `null` e `''` in confronto debole si equivalgono, e uno zero legittimo (un prezzo!) può far fallire una condizione.
- Da PHP 8 il confronto debole tra numeri e stringhe **non numeriche** è cambiato: `0 == "foo"` e `0 == ""` ora sono `false` (prima erano `true`), e `42 == "42abc"` è `false`. Attenzione in fase di migrazione, anche per `switch` (confronto debole) e funzioni come `in_array()` (usa il terzo parametro `true` per il confronto stretto).
- Lo spaceship `<=>` (PHP 7) fa tre confronti in uno: ritorna `-1` se il primo operando è minore, `0` se sono uguali, `1` se è maggiore.
- Il ternario `condizione ? valore1 : valore2` è la forma compatta di un `if`/`else`: usalo per le espressioni semplici, e metti la condizione tra parentesi tonde.
- Il null coalescing `??` ritorna il primo valore non `null` dell'elenco; da PHP 7.4, `$var ??= 'default'` assegna il default solo se la variabile è `null`.

Con questi operatori siamo pronti per le strutture di controllo del prossimo capitolo: `if`, `elseif`, `else`, `switch`, `match` e i cicli. Prima di proseguire, prenditi qualche minuto per sperimentare nel tuo editor: confronta `null` con `0`, la stringa vuota con `null`, un numero con una stringa, e osserva i risultati che ottieni.
