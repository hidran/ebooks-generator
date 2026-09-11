# 10. Le funzioni

Fino a questo punto abbiamo scritto script che eseguono le istruzioni una dopo l'altra e abbiamo imparato a controllarne il flusso con le condizioni e i cicli. Manca però un ingrediente essenziale di qualunque linguaggio: il modo per **raggruppare un blocco di istruzioni sotto un nome** e riutilizzarlo tutte le volte che serve, senza copiare e incollare lo stesso codice. Questo strumento è la **funzione**, ed è il cuore di questo capitolo.

Le funzioni sono importantissime in PHP come in tanti altri linguaggi. Partiremo dalle basi — che cos'è una funzione, come dichiararla, come passarle dei dati e come farsi restituire un risultato — e arriveremo alle novità del PHP moderno: la dichiarazione dei tipi introdotta con PHP 7, le funzioni anonime e le arrow function, i parametri variabili, i named argument e gli union type di PHP 8. È un capitolo corposo, ma ogni paragrafo aggiunge un tassello: alla fine avrai in mano tutto ciò che serve per scrivere codice riutilizzabile e ben tipizzato. Per gli esempi ti basta una cartella di lavoro con un file (ad esempio `functions.php`) da eseguire dalla riga di comando con `php functions.php`, oppure servito dal server integrato che abbiamo imparato ad avviare nei capitoli precedenti.

## Che cos'è una funzione

Una **funzione** è un costrutto che ci permette di raccogliere al suo interno un blocco di istruzioni per svolgere una determinata operazione. Può ricevere in ingresso uno o più **parametri** e può restituire un valore in uscita, oppure non restituire nulla. In PHP non esiste il concetto separato di "procedura" che troviamo in altri linguaggi: una procedura è semplicemente una funzione che non ritorna alcun valore.

Il nome di una funzione deve seguire le stesse regole dei nomi (le "etichette") in PHP: comincia con una lettera o con un trattino basso, seguito da lettere, numeri o trattini bassi. A differenza dei nomi di variabile, il nome di una funzione **non è case sensitive**. La dichiarazione è sempre preceduta dalla parola chiave `function`.

Vale la pena tenere a mente fin da subito alcune caratteristiche delle funzioni in PHP:

- Possono essere **chiamate anche prima della loro definizione** nel file, tranne quando la definizione è racchiusa dentro una condizione (ad esempio un `if`): in quel caso la funzione esiste solo dopo che quel ramo è stato eseguito.
- Possono essere **annidate**, ma la funzione interna non esiste finché non viene chiamata quella esterna che la contiene.
- Hanno **visibilità globale**: una volta definite, possono essere richiamate da qualunque punto dello script.
- Possono avere parametri variabili e parametri con valore di default, e possono essere chiamate **ricorsivamente** (cioè richiamare sé stesse).

Passiamo subito alla pratica.

## Dichiarare una funzione

Creiamo una funzione quando PHP non ne mette già a disposizione una che risponda alle nostre esigenze. Abbiamo già usato funzioni predefinite come `isset()` per verificare se una variabile è impostata o `empty()` per controllare se è vuota; ora impariamo a scriverne di nostre. Il caso tipico è questo: ci sono righe di codice che ripetiamo di continuo e, invece di fare copia-incolla, le racchiudiamo in una funzione e la eseguiamo ogni volta che ci serve.

### La sintassi di base

Per dichiarare una funzione servono, come minimo, la parola chiave `function`, un **nome**, le parentesi tonde e le parentesi graffe. Il nome è indispensabile: senza di esso non sapremmo come invocare la funzione. Per convenzione — e a seconda del framework con cui si lavora — i nomi di funzione cominciano con la lettera minuscola e, se composti da più parole, usano la notazione **camelCase** (ogni parola successiva inizia con la maiuscola).

Scriviamo una funzione che mostri sempre un saluto:

```php
<?php

function sayHello()
{
    echo 'Hello world';
}
```

Codice completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-01.php)


Tra le graffe c'è il **corpo** della funzione: tutte le istruzioni che vogliamo eseguire, riga per riga. Per eseguire la funzione basta **invocarla**, cioè scrivere il suo nome seguito dalle parentesi tonde (vuote, perché questa funzione non riceve alcun parametro):

```php
sayHello(); // Hello world
```

Codice completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-02.php)


Il corpo potrebbe anche essere vuoto: in quel caso la funzione è del tutto legittima ma non produce alcun effetto quando la chiamiamo.

### Eseguire lo script

Possiamo eseguire lo script in più modi. Il più comodo, quando facciamo output di puro PHP senza HTML, è la **riga di comando**: apriamo il terminale (anche quello integrato nell'editor) e — dato che `php` deve trovarsi nel PATH, come abbiamo configurato nel capitolo sull'installazione — lanciamo:

```bash
php functions.php
```

Codice completo: [listing-03.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-03.sh)


e vediamo comparire `Hello world`. In alternativa, se vogliamo eseguirlo tramite un server nel browser, avviamo il server integrato indicando una porta libera:

```bash
php -S localhost:4000 functions.php
```

Codice completo: [listing-04.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-04.sh)


Editor come Visual Studio Code e PhpStorm offrono anche un pulsante per eseguire lo script o avviare il server integrato senza passare dal terminale: qualunque modo va bene, l'importante è riuscire a eseguire il file. Finché lavoriamo con puro PHP conviene restare sulla riga di comando, così non dobbiamo passare di continuo tra editor e browser.

### Assegnare una funzione a una variabile

Esiste un secondo modo di definire una funzione: **assegnarne il corpo a una variabile**. Invece del nome scriviamo il nome della variabile, l'uguale e poi `function`:

```php
$sayHi = function () {
    echo 'Hey';
};
```

Codice completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-05.php)


Nota il **punto e virgola** finale: qui non stiamo dichiarando una funzione con nome, ma assegnando un valore a una variabile, quindi l'istruzione va chiusa come qualunque altra assegnazione (l'editor ce lo segnala se lo dimentichiamo). Per eseguirla usiamo il nome della variabile seguito dalle parentesi tonde:

```php
$sayHi(); // Hey
```

Codice completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-06.php)


La sintassi è la stessa di una funzione normale, cambia solo il `$` davanti al nome. C'è però una **differenza fondamentale**. Una funzione dichiarata con nome può essere chiamata anche *prima* della sua definizione nel file:

```php
sayHello();      // funziona, anche se sayHello() è definita più sotto

function sayHello()
{
    echo 'Hello world';
}
```

Codice completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-07.php)


Una funzione assegnata a una variabile, invece, **non può essere chiamata prima dell'assegnazione**: se ci proviamo, PHP solleva un errore, perché in quel punto la variabile non esiste ancora. La regola è intuitiva: la funzione con nome viene "vista" da PHP in tutto lo script, mentre la variabile prende vita solo nel momento in cui le assegniamo la funzione.

E allora a cosa serve mettere una funzione in una variabile? Il motivo è che in PHP una funzione è un **cittadino di prima classe**: possiamo passarla come argomento a un'altra funzione ed eseguirla altrove. Le funzioni assegnate a variabili (che sono in realtà istanze di una classe interna, `Closure`) sono lo strumento con cui lo faremo, come vedremo nei paragrafi sulle funzioni anonime.

## Parametri e argomenti

Una funzione diventa davvero utile quando le passiamo dei dati. All'interno delle parentesi tonde possiamo dichiarare uno o più **parametri**: sono come variabili che la funzione si aspetta di ricevere. Modifichiamo il saluto perché accetti un nome:

```php
<?php

function sayHello($name)
{
    echo "Hello $name";
}
```

Codice completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-08.php)


È importante distinguere due termini che spesso si confondono:

- il **parametro** è la variabile che dichiariamo quando *scriviamo* la funzione (`$name` qui sopra);
- l'**argomento** è il valore concreto che passiamo quando *chiamiamo* la funzione.

Quindi, in `sayHello('Idra')`, `$name` è il parametro e `'Idra'` è l'argomento che gli passiamo.

### Parametri con valore di default

Un parametro può avere un **valore di default**, usato quando chi chiama la funzione non passa alcun argomento:

```php
function sayHello($name = 'World')
{
    echo "Hello $name";
}

sayHello();        // Hello World
sayHello('Idra');  // Hello Idra
```

Codice completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-09.php)


Se non passiamo nulla, `$name` vale `'World'`; se passiamo un argomento, quello sostituisce il default.

### Più parametri e l'ordine degli argomenti

Quando i parametri sono più di uno, dobbiamo **rispettare il loro ordine** al momento della chiamata, altrimenti i valori finiscono nei parametri sbagliati. Scriviamo una funzione che mostra il nome completo di una persona:

```php
function getFullName($name, $surname)
{
    echo "Full name is $name $surname";
}

getFullName('Idra', 'Arias'); // Full name is Idra Arias
```

Codice completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-10.php)


Se questi parametri sono **obbligatori** (non hanno un valore di default) e non li passiamo, PHP solleva un `ArgumentCountError`, segnalando che manca un argomento. Ecco già l'utilità delle funzioni: senza di esse, per mostrare più nomi completi dovremmo ripetere lo stesso `echo` per ogni persona; con la funzione richiamiamo lo stesso codice passando dati diversi — comodissimo quando quei dati arrivano, per esempio, da un database.

### Dichiarare il tipo dei parametri e strict_types

L'editor, quando scriviamo una funzione, ci segnala spesso che non stiamo indicando né il tipo dei parametri né il tipo di ritorno. A partire da PHP 7 possiamo dichiararli, e conviene farlo perché rende il codice più sicuro e leggibile. Indichiamo il tipo scrivendolo **prima** del parametro:

```php
function getFullName(string $name, string $surname)
{
    echo "Full name is $name $surname";
}
```

Codice completo: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-11.php)


Attenzione, però: di default PHP applica il cosiddetto **coercive mode**, cioè cerca di *convertire* l'argomento al tipo dichiarato. Se passiamo il numero `44` a un parametro dichiarato `string`, PHP lo trasforma in stringa senza protestare. Se vogliamo che i tipi vengano verificati in modo rigoroso — senza alcuna conversione — dobbiamo mettere in cima al file, **come primissima riga**, la direttiva:

```php
<?php

declare(strict_types=1);
```

Codice completo: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-12.php)


Con `strict_types=1`, passare un numero dove è richiesta una stringa genera un `TypeError`. Il vantaggio è duplice: da un lato PHP blocca l'errore a runtime, dall'altro l'editor ce lo segnala già mentre scriviamo, prima ancora di eseguire il codice. Il mio consiglio, dall'esperienza quotidiana, è di mettere sempre `declare(strict_types=1)` in testa ai file: la tipizzazione ha senso proprio quando i tipi vengono rispettati davvero.

### Named argument e valori di default

Quando i parametri sono tanti, ricordarne l'ordine diventa scomodo e si rischia di sbagliare. PHP 8 ci viene incontro con i **named argument**: possiamo passare gli argomenti indicando il nome del parametro (senza il `$`), seguito dai due punti e dal valore, **in qualunque ordine**. Aggiungiamo alla funzione un terzo parametro, l'età:

```php
function getFullName(string $name, string $surname, int $age)
{
    echo "$name $surname, $age anni";
}

// con i named argument l'ordine non conta:
getFullName(age: 45, name: 'Maria', surname: 'Rossi');
```

Codice completo: [listing-13.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-13.php)


Torneremo sui named argument in un paragrafo dedicato più avanti. Per ora ci servono a chiarire una regola sui valori di default. Se un parametro con valore di default viene *prima* di un parametro obbligatorio, quel default diventa di fatto inutile: dovendo comunque passare l'argomento successivo, siamo costretti a passare anche quello che avrebbe il default. Anzi, PHP 8 segnala come **deprecato** dichiarare un parametro opzionale prima di uno obbligatorio. La regola pratica è chiara: **i parametri con valore di default vanno messi in fondo** all'elenco. I named argument attenuano il problema (permettono di saltare i parametri intermedi che hanno un default), ma la convenzione resta valida.

## Ritornare valori

Finora le nostre funzioni mostravano qualcosa a video ma non restituivano nulla. Il caso più interessante è quello in cui la funzione **calcola un risultato e ce lo consegna**, così possiamo catturarlo, stamparlo o passarlo ad altre operazioni.

### return e il tipo di ritorno

Per restituire un valore usiamo la parola chiave `return`. Scriviamo una semplice funzione che somma due numeri interi:

```php
<?php

declare(strict_types=1);

function somma(int $a, int $b): int
{
    return $a + $b;
}
```

Codice completo: [listing-14.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-14.php)


Due dettagli. Primo: `return` interrompe la funzione e ne restituisce il valore indicato. Secondo: dopo le parentesi tonde abbiamo scritto `: int`, che dichiara il **tipo di ritorno**. Dato che sommiamo due `int`, la funzione ritornerà sempre un `int`; se provassimo a ritornare qualcosa di diverso, PHP genererebbe un errore (e l'editor ce lo segnalerebbe in anticipo).

Come catturiamo il risultato? La funzione, da sola, non stampa nulla: dobbiamo usare il valore che ritorna. Possiamo passarlo direttamente a `echo`, oppure salvarlo in una variabile:

```php
echo somma(4, 5);           // 9

$result = somma(4, 5);
echo $result;               // 9
```

Codice completo: [listing-15.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-15.php)


Salvare il risultato in una variabile è utile quando vogliamo rielaborarlo o passarlo ad altre funzioni, invece di limitarci a mostrarlo. Se all'interno della funzione mettessimo un `return 'una stringa';` prima del `return` corretto, con il tipo di ritorno `int` dichiarato l'editor ci avviserebbe subito dell'incongruenza: ecco perché dichiarare i tipi è così prezioso.

### Ritornare più valori: array e destrutturazione

In PHP una funzione **non può ritornare più di un valore scalare**. Se ci serve restituire più risultati, l'unico modo è racchiuderli in un **array**. Scriviamo una funzione che, dati due lati, calcola area e perimetro di un rettangolo:

```php
function calcAreaPerimetro(int $a, int $b): array
{
    $area = $a * $b;
    $perimetro = 2 * ($a + $b);

    return [$area, $perimetro];
}
```

Codice completo: [listing-16.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-16.php)


Il tipo di ritorno ora è `array`. Possiamo catturare il risultato in una variabile e ispezionarlo con `print_r()`:

```php
$result = calcAreaPerimetro(5, 4);
print_r($result);
// Array ( [0] => 20 [1] => 18 )
```

Codice completo: [listing-17.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-17.php)


Nella posizione `0` c'è l'area (5 × 4 = 20), nella posizione `1` il perimetro (2 × 9 = 18). Ancora più elegante è **destrutturare** l'array restituito direttamente in due variabili distinte:

```php
[$area, $perimetro] = calcAreaPerimetro(5, 6);

echo "$area\n";        // 30
echo "$perimetro\n";   // 22
```

Codice completo: [listing-18.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-18.php)


La stessa cosa si otteneva un tempo con la funzione `list()`, che riceve l'array e le variabili in cui distribuirne i valori:

```php
list($a, $b) = calcAreaPerimetro(5, 6);
echo "$a $b\n"; // 30 22
```

Codice completo: [listing-19.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-19.php)


La sintassi con le parentesi quadre è quella moderna e più leggibile, ma è utile riconoscere anche `list()` perché la incontrerai in molto codice esistente.

## Tipizzare argomenti e ritorno (PHP 7)

Approfondiamo la novità che PHP 7 ha portato: la **dichiarazione dei tipi** sia per i parametri d'ingresso sia per il valore di ritorno. Fino a PHP 5 potevamo dichiarare come tipo di un parametro soltanto una classe, un'interfaccia o `array`. Con PHP 7 possiamo usare anche i **tipi scalari** e altri tipi speciali:

- `int` — un intero;
- `float` — un numero con la virgola;
- `string` — una stringa;
- `bool` — un booleano;
- `array` — un array;
- `callable` — qualcosa che può essere invocato come una funzione (il nome di una funzione, una funzione anonima, un metodo, o un oggetto con il metodo magico `__invoke`);
- una **classe** o un'**interfaccia**.

Attenzione alla nomenclatura: bisogna scrivere esattamente `int`, `bool`, `float`, `string`. Se scrivessimo `integer` o `boolean`, PHP penserebbe che ci riferiamo a una *classe* con quel nome. Riprendiamo la somma:

```php
<?php

function somma(int $a, int $b): int
{
    return $a + $b;
}

echo somma(5, 5); // 10
```

Codice completo: [listing-20.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-20.php)


Come già visto, senza `declare(strict_types=1)` PHP applica la conversione implicita: se passiamo la stringa `'5'`, la trasforma in intero e la somma funziona lo stesso. Va bene per le conversioni semplici (da stringa a numero e viceversa), ma non per i casi ambigui. Se vogliamo che PHP verifichi i tipi senza convertire nulla, mettiamo in testa al file `declare(strict_types=1)`: a quel punto passare `'10'` dove serve un `int` solleva un `TypeError`, e lo stesso vale per il tipo di ritorno.

Vediamo qualche esempio di tipi non scalari. Aggiungiamo un terzo parametro di tipo `array`:

```php
function somma(int $a, int $b, array $c): int
{
    return $a + $b;
}

somma(5, 5, []);          // ok: array vuoto
somma(5, 5, 'non array'); // TypeError: il terzo argomento non è un array
```

Codice completo: [listing-21.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-21.php)


Possiamo anche dichiarare che un parametro sia di un tipo **classe**: in quel caso dobbiamo passargli un'istanza di quella classe (studieremo le classi nella Parte VII), altrimenti otteniamo un errore. E possiamo dichiararlo `callable`, il che ci permette di accettare indifferentemente il nome di una funzione (passato come stringa), una funzione anonima o una variabile che contiene una `Closure`:

```php
function esegui(callable $c): void
{
    $c(); // invochiamo ciò che ci è stato passato
}

function test()
{
    echo "test\n";
}

esegui('test');                       // passiamo il nome come stringa
esegui(function () { echo "anon\n"; }); // passiamo una funzione anonima
```

Codice completo: [listing-22.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-22.php)


Nota il tipo di ritorno `void`: indica che la funzione **non restituisce alcun valore**. Questa possibilità di tipizzare parametri e ritorno — a lungo assente in PHP e presente invece in linguaggi come Java o C# — è una delle novità più importanti di PHP 7, e conviene sfruttarla nei nostri progetti.

## Parametri nullable e ritorno null (PHP 7.1)

Da PHP 7.1 possiamo dichiarare che un parametro (o il valore di ritorno) di un certo tipo possa anche essere **`null`**. Si fa anteponendo un **punto interrogativo** al tipo. Riprendiamo la somma con tipi dichiarati:

```php
function sum(int $a, int $b): int
{
    return $a + $b;
}
```

Codice completo: [listing-23.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-23.php)


Se proviamo a passare `null` a uno dei parametri `int`, otteniamo un `TypeError`: `null` non è un intero. Per permetterlo, anteponiamo il `?`:

```php
function sum(?int $a, ?int $b): int
{
    return $a + $b;
}

$result = sum(null, null);
var_dump($result); // int(0)
```

Codice completo: [listing-24.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-24.php)


Ora possiamo passare `null` senza errori. Nota un dettaglio curioso: la funzione ritorna `int(0)`, perché PHP, sommando due `null`, li tratta come `0`. Il ritorno resta un `int`, quindi il tipo di ritorno `int` è rispettato.

Supponiamo invece di voler ritornare esplicitamente `null` in un certo caso:

```php
function sum(?int $a, ?int $b): int
{
    if ($a === null || $b === null) {
        return null; // ERRORE: il tipo di ritorno è int
    }

    return $a + $b;
}
```

Codice completo: [listing-25.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-25.php)


Questo solleva un errore, perché abbiamo dichiarato che la funzione ritorna `int`, non `null`. La soluzione è rendere **nullable anche il tipo di ritorno**, con lo stesso `?`:

```php
function sum(?int $a, ?int $b): ?int
{
    if ($a === null || $b === null) {
        return null;
    }

    return $a + $b;
}
```

Codice completo: [listing-26.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-26.php)


Un'ultima avvertenza. Dichiarare un parametro `?int` significa che *può* valere `null`, ma non che sia **facoltativo**: se lo omettiamo del tutto nella chiamata, PHP solleva comunque un `ArgumentCountError`. Per renderlo davvero opzionale dobbiamo dargli un valore di default:

```php
function sum(?int $a = null, ?int $b = null): ?int
{
    // ...
}

sum(); // ora è lecito
```

Codice completo: [listing-27.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-27.php)


Riassumendo: il `?` davanti al tipo (di un parametro o del ritorno) autorizza il valore `null`; per rendere un parametro anche omissibile serve un valore di default. Vedremo nel Capitolo 32, con le eccezioni, come catturare errori come `ArgumentCountError` e `TypeError` in un blocco `try`/`catch`.

## Lo scope delle variabili

Un tema centrale nell'uso delle funzioni è la **visibilità** (o *scope*, ambito) delle variabili: quali variabili una funzione può vedere e quali no.

### Le variabili locali

La regola di base è che ogni funzione crea un proprio **ambiente isolato**. Le variabili definite fuori dalla funzione non sono visibili al suo interno, e viceversa le variabili definite dentro la funzione non esistono più una volta usciti da essa. Vediamolo:

```php
<?php

$data = ['name' => 'John Doe'];

function modifica()
{
    var_dump($data); // Warning: $data non è definita qui dentro
}

modifica();
```

Codice completo: [listing-28.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-28.php)


Eseguendo lo script otteniamo un warning: dentro `modifica()` la variabile `$data`, pur esistendo nell'ambiente esterno, semplicemente non è visibile. PHP, all'interno della funzione, crea un suo *scope* dove vivono soltanto le sue variabili locali e non vede nulla di ciò che sta fuori.

### Il costrutto global

Come accediamo, dall'interno di una funzione, a una variabile che vive nell'ambiente globale? L'ambiente globale è tutto ciò che sta fuori dalle funzioni: le variabili scritte direttamente nello script (o in un file incluso), ma non quelle interne ad altre funzioni o oggetti. Il primo modo è il costrutto **`global`**, seguito dal nome della variabile che vogliamo importare:

```php
$object = 'John';

function modifica()
{
    global $object;

    var_dump($object); // ora vediamo 'John'
    $object = 'Idra';  // e possiamo anche modificarla
}

modifica();
var_dump($object); // 'Idra': la modifica si riflette fuori!
```

Codice completo: [listing-29.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-29.php)


Con `global $object` stiamo facendo *riferimento* alla variabile globale: non solo la leggiamo, ma se la modifichiamo all'interno della funzione **modifichiamo anche quella esterna**, perché è la stessa variabile per riferimento. Lo stesso vale per array e valori scalari: importata con `global`, qualunque variabile globale può essere letta e sovrascritta dall'interno della funzione. Tienilo sempre presente, perché è un effetto collaterale facile da dimenticare.

### La superglobale $GLOBALS

Il secondo modo per accedere alle variabili globali è la **superglobale** `$GLOBALS`. Le superglobali sono array speciali che PHP mette a disposizione ovunque nello script — le studieremo in dettaglio nel Capitolo 13 (`$_GET`, `$_POST`, `$_SESSION`, `$_SERVER`, `$_REQUEST` e altri). `$GLOBALS` è un grande array che contiene **tutte le variabili globali**, indicizzate per nome:

```php
$name = 'John Doe';

function modifica()
{
    $GLOBALS['name'] = 'Idra'; // accediamo alla globale tramite la sua chiave
}

modifica();
echo $GLOBALS['name']; // Idra
```

Codice completo: [listing-30.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-30.php)


La chiave dell'array corrisponde al nome della variabile (senza `$`). C'è un punto importante da capire: se dentro una funzione dichiariamo `global $val` e poi proviamo a usare un parametro locale con lo stesso nome, **il riferimento globale ha la precedenza** e il valore locale viene ignorato. Rimuovendo il `global`, tornerebbe visibile la variabile locale. In altre parole, `global` "importa" davvero la variabile esterna nello scope della funzione, mettendola al posto di eventuali omonime locali.

Nella pratica quotidiana l'uso di `global` è sconsigliato — introduce dipendenze nascoste e rende il codice più difficile da seguire — ma è fondamentale conoscerlo per capire come funziona lo scope in PHP. La regola da fissare è questa: dentro una funzione le variabili globali non esistono a meno che non le importiamo esplicitamente (con `global` o attraverso `$GLOBALS`), oppure a meno che non gliele passiamo come argomenti. Quest'ultima strada — passare i dati come parametri — è quasi sempre la scelta migliore.

## Funzioni anonime e funzioni variabili

Abbiamo anticipato che una funzione può essere assegnata a una variabile. Una funzione senza nome si chiama **funzione anonima** (o *closure*), e quando la assegniamo a una variabile parliamo di **funzione variabile**. Internamente PHP crea un'istanza della sua classe `Closure` e la assegna alla variabile.

### Assegnare una funzione anonima a una variabile

```php
<?php

$somma = function ($a, $b) {
    return $a + $b;
};

echo $somma(2, 3); // 5
```

Codice completo: [listing-31.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-31.php)


Ricorda sempre il **punto e virgola** dopo la graffa di chiusura: è un'assegnazione, non una dichiarazione di funzione. Per invocarla usiamo il nome della variabile e le parentesi tonde, esattamente come una funzione normale. Come già visto per le funzioni variabili, non possiamo chiamarla prima di averla definita: la variabile `$somma` non esiste finché non le assegniamo la closure.

### Passare una funzione come argomento

Il bello delle funzioni anonime è che si possono passare come argomento ad altre funzioni. Una funzione che riceve un parametro `callable` può eseguirlo al suo interno:

```php
function test(callable $func)
{
    echo $func(5, 5);
}

test($somma); // 10
```

Codice completo: [listing-32.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-32.php)


Se dichiariamo il parametro `callable` (o, più specificamente, `Closure`) e proviamo a passargli un numero, otteniamo un errore: PHP si aspetta qualcosa di invocabile. Questo meccanismo — passare una funzione a un'altra funzione — è la base di moltissime operazioni sugli array, che vediamo subito.

## Funzioni anonime con gli array

Molte funzioni predefinite di PHP che lavorano sugli array accettano come argomento una **funzione di callback**: la applicano a ogni elemento e restituiscono un risultato. Le più usate sono `array_map`, `array_filter` e `array_walk`. Concentriamoci su `array_map`, che prende un array e una funzione, applica la funzione a ciascun elemento e **restituisce un nuovo array** con i risultati.

### array_map

Supponiamo di avere un elenco di numeri e di volerne una copia con ogni valore raddoppiato. Con un ciclo `foreach` faremmo così:

```php
<?php

$numbers = [1, 2, 3, 4, 5];
$doubleArray = [];

foreach ($numbers as $val) {
    $doubleArray[] = $val * 2;
}

print_r($doubleArray);
// Array ( [0] => 2 [1] => 4 [2] => 6 [3] => 8 [4] => 10 )
```

Codice completo: [listing-33.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-33.php)


Con `array_map` è molto più conciso. Come callback possiamo passare il **nome di una nostra funzione** (come stringa). Creiamo una funzione che raddoppia un valore — la chiamiamo `doubleVal` per non sovrapporci a `doubleval()`, che è una funzione nativa di PHP:

```php
function doubleVal($val)
{
    return $val * 2;
}

$double = array_map('doubleVal', $numbers);
print_r($double);
// Array ( [0] => 2 [1] => 4 [2] => 6 [3] => 8 [4] => 10 )
```

Codice completo: [listing-34.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-34.php)


`array_map` prende ogni elemento di `$numbers`, lo passa a `doubleVal`, raccoglie i valori restituiti in un nuovo array e ce lo consegna. Dato che ritorna un array, ne catturiamo il risultato in una variabile.

### Callback, closure e funzioni native

Il primo argomento di `array_map` può essere qualunque *callable*. Oltre al nome di una nostra funzione, possiamo passare il nome di una **funzione nativa** di PHP. Ad esempio `floor()`, che tronca un numero decimale al suo intero inferiore:

```php
$numbers = [6.4, 3.2, 5.7];
$troncati = array_map('floor', $numbers);
print_r($troncati);
// Array ( [0] => 6 [1] => 3 [2] => 5 )
```

Codice completo: [listing-35.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-35.php)


Ma spesso la funzione ci serve una volta sola, per quell'unica operazione: in questi casi è inutile dichiararla a parte. Possiamo passarla **inline** come funzione anonima:

```php
$double = array_map(function ($val) {
    return $val * 2;
}, $numbers);
```

Codice completo: [listing-36.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-36.php)


La funzione anonima riceve il valore di ogni elemento e restituisce il risultato voluto. È il modo idiomatico quando la logica è specifica per quella chiamata e non verrà riutilizzata altrove. La regola pratica che uso: se la funzione serve solo lì, scrivila anonima inline; se pensi di riutilizzarla in più punti, dichiarala come funzione vera e propria con un nome, così è accessibile ovunque. E se la logica è molto breve — una sola riga — c'è una forma ancora più compatta, che vediamo ora.

## Le arrow function (PHP 7.4)

PHP 7.4 ha introdotto le **arrow function** (o *funzioni freccia*), una sintassi abbreviata per le funzioni anonime che restituiscono il risultato di una sola espressione. Sono comodissime proprio nei casi come `array_map`, dove un parametro è una funzione che deve trasformare un valore.

### La sintassi con fn

Al posto della parola `function` scriviamo **`fn`**, seguito dai parametri tra parentesi, dalla **freccia** `=>` e subito dall'espressione da ritornare. Non ci sono le graffe e **non serve** la parola `return`: il valore dopo la freccia è ciò che viene restituito.

```php
$double = array_map(fn($val) => $val * 2, $numbers);
```

Codice completo: [listing-37.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-37.php)


Questa riga fa esattamente lo stesso della funzione anonima del paragrafo precedente, ma in modo molto più compatto. Vediamola su un array associativo, per portare tutti i valori in maiuscolo con `strtoupper()` mantenendo le chiavi:

```php
<?php

$data = ['name' => 'idra', 'surname' => 'arias', 'city' => 'torino'];

$result = array_map(fn($val) => strtoupper($val), $data);
print_r($result);
// Array ( [name] => IDRA [surname] => ARIAS [city] => TORINO )
```

Codice completo: [listing-38.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-38.php)


Le arrow function devono stare **tutte su una riga**: non possiamo aprire le graffe e andare a capo come in JavaScript. Se ci serve più logica di una singola espressione, dobbiamo tornare alla funzione anonima classica.

### L'ereditarietà dello scope

C'è una differenza importante rispetto alle funzioni anonime tradizionali. Una funzione anonima, come qualunque funzione, crea un proprio ambiente e **non vede** le variabili esterne. Per usarne una dentro una closure classica dobbiamo importarla esplicitamente con la parola chiave **`use`**:

```php
$prefix = 'Mr. ';

$result = array_map(function ($val) use ($prefix) {
    return $prefix . strtoupper($val);
}, $data);
```

Codice completo: [listing-39.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-39.php)


Senza `use ($prefix)`, la variabile `$prefix` non sarebbe visibile dentro la funzione (potremmo elencare più variabili separate da virgola). Le **arrow function**, invece, **ereditano automaticamente** le variabili dell'ambiente in cui sono definite: non serve alcun `use`.

```php
$prefix = 'Mr. ';

$result = array_map(fn($val) => $prefix . strtoupper($val), $data);
```

Codice completo: [listing-40.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-40.php)


L'arrow function vede `$prefix` senza doverla importare: eredita l'intero contesto in cui viene eseguita. È uno dei loro vantaggi più apprezzati, oltre alla brevità.

Riassumendo la scala di scelta: per una trasformazione di una sola riga usa un'arrow function; se serve un po' di logica su più righe, una funzione anonima con `use` dove necessario; se la funzione è complessa o riutilizzabile, estraila in una funzione con nome e passane il nome come callback — il codice risulterà più pulito.

## Le variadic function

Le **variadic function** (o *funzioni con parametri variabili*) sono funzioni che accettano un **numero variabile di argomenti**. Ci permettono di scrivere funzioni più flessibili, che si adattano a quanti argomenti riceviamo.

### Il rest parameter

Il modo moderno è il **rest parameter**: si mettono **tre puntini** (`...`) davanti al nome del parametro, e automaticamente ci ritroviamo un array con tutti gli argomenti passati. Scriviamo una funzione che somma un numero qualsiasi di valori:

```php
<?php

declare(strict_types=1);

function sum(...$values)
{
    $somma = 0;

    foreach ($values as $val) {
        $somma += $val;
    }

    return $somma;
}

echo sum(1, 2, 3);       // 6
echo sum(1, 2, 3, 4, 5); // 15
```

Codice completo: [listing-41.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-41.php)


Dentro la funzione, `$values` è un normale array che contiene tutti gli argomenti. Prima dell'introduzione del rest parameter si otteneva lo stesso risultato con la funzione **`func_get_args()`**, che restituisce l'array degli argomenti ricevuti anche senza dichiarare alcun parametro:

```php
function sumOld()
{
    $somma = 0;

    foreach (func_get_args() as $val) {
        $somma += $val;
    }

    return $somma;
}
```

Codice completo: [listing-42.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-42.php)


È il metodo "vecchio", che mostro solo per completezza: oggi il rest parameter è più chiaro ed esplicito, quindi non c'è più motivo di usare `func_get_args()`.

### Tipizzare e combinare i parametri

Possiamo dichiarare il **tipo** degli argomenti raccolti mettendolo *prima* dei tre puntini:

```php
function sum(float ...$values): float
{
    // ...
}
```

Codice completo: [listing-43.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-43.php)


Con `declare(strict_types=1)` attivo, passare una stringa dove serve un `float` genera un errore; un `int` invece viene accettato perché è convertibile a `float` senza perdita.

Il rest parameter può convivere con **parametri posizionali** all'inizio: i primi argomenti finiscono nei parametri "normali", tutti gli altri vengono catturati dal parametro variadic. Il rest parameter, però, deve essere **l'ultimo**. Scriviamo una funzione che unisce più stringhe con un separatore:

```php
function stringJoin(string $separator, string ...$parts): string
{
    return implode($separator, $parts);
}

echo stringJoin('-', '1', '2', '3', '4'); // 1-2-3-4
echo stringJoin('-', 'a', 'b');            // a-b
```

Codice completo: [listing-44.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-44.php)


Il primo argomento (`$separator`) è obbligatorio; tutti gli altri vengono raccolti in `$parts` e passati a `implode()`, la funzione nativa che unisce gli elementi di un array in una stringa. Nota che PHP 8 permette la **virgola finale** anche nell'elenco dei parametri e degli argomenti: è comoda perché aggiungere un elemento in coda non richiede di toccare la riga precedente.

### Un esempio pratico: una calcolatrice

Mettiamo insieme quanto visto costruendo una piccola calcolatrice: il primo parametro è l'operazione da eseguire, i restanti sono gli operandi.

```php
<?php

declare(strict_types=1);

function calc(string $operation, int ...$values): float
{
    $result = $values[0];
    $total = count($values);

    for ($i = 1; $i < $total; $i++) {
        switch ($operation) {
            case '+':
                $result += $values[$i];
                break;
            case '-':
                $result -= $values[$i];
                break;
            case '*':
                $result *= $values[$i];
                break;
            case '/':
                if ($values[$i] !== 0) {
                    $result /= $values[$i];
                }
                break;
        }
    }

    return $result;
}

echo calc('*', 3, 4, 5); // 60
echo calc('+', 3, 4, 5); // 12
echo calc('/', 3, 4, 5); // 0.15
```

Codice completo: [listing-45.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-45.php)


Qualche scelta degna di nota. Inizializziamo `$result` con il primo valore (`$values[0]`) e facciamo partire il ciclo `for` da `1`, perché il primo operando è già il punto di partenza. Calcoliamo `count($values)` **una sola volta** fuori dal ciclo, salvandolo in `$total`, invece di richiamarlo a ogni giro. Per la divisione controlliamo che il divisore non sia `0`, saltando l'operazione in quel caso (con la moltiplicazione non serve: lo zero è un operando legittimo). Il tipo di ritorno è `float` perché una divisione può produrre un decimale. Usiamo gli **operatori composti** (`+=`, `-=`, `*=`, `/=`) visti nel Capitolo 8 per rendere il codice più conciso.

La cosa più importante da ricordare: i tre puntini catturano tutti i parametri passati; possiamo tipizzarli, e possiamo anteporvi altri parametri posizionali — i primi argomenti finiscono in quei parametri, il resto nel variadic.

## I named argument (PHP 8)

Con PHP 8 possiamo passare gli argomenti di una funzione indicandone il **nome**, come abbiamo anticipato parlando dei parametri. È una delle novità più apprezzate: rende le chiamate più leggibili e ci libera dall'obbligo di ricordare l'ordine esatto dei parametri.

La sintassi è: nome del parametro (senza `$`), due punti, valore. Riprendiamo una funzione con tre parametri:

```php
function somma(int $a, int $b, callable $c)
{
    $c();
    return $a + $b;
}

// passiamo gli argomenti per nome, nell'ordine che preferiamo:
somma(
    b: 5,
    a: 10,
    c: fn() => print("calcolo in corso\n"),
);
```

Codice completo: [listing-46.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-46.php)


Il codice funziona perfettamente, anche se abbiamo passato `b` prima di `a`: con i named argument **l'ordine di dichiarazione non va rispettato**. Restano invece valide le regole sui parametri obbligatori: se ne omettiamo uno che la funzione si aspetta, PHP segnala che manca (`ArgumentCountError`).

I named argument funzionano anche con le **funzioni native**. Ad esempio `strstr($haystack, $needle)`, che cerca una sottostringa e restituisce la porzione a partire dalla prima occorrenza; i suoi parametri si chiamano `$haystack` (la stringa in cui cercare) e `$needle` (cosa cercare):

```php
$result = strstr(needle: 'idra', haystack: 'sono idra arias');
var_dump($result); // string(10) "idra arias"
```

Codice completo: [listing-47.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-47.php)


Possiamo anche **mescolare** argomenti posizionali e per nome, ma con una regola precisa: **un argomento posizionale non può venire dopo uno per nome**. Una volta che iniziamo a usare i nomi, tutti gli argomenti successivi devono avere il nome:

```php
somma(10, c: fn() => null, b: 5);      // ok: il posizionale è il primo
// somma(a: 10, 5, ...);               // ERRORE: posizionale dopo un named
```

Codice completo: [listing-48.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-48.php)


I named argument sono comodissimi quando una funzione ha molti parametri e vogliamo passarne solo alcuni, o quando vogliamo rendere evidente, a colpo d'occhio, il significato di ciascun valore alla chiamata — un po' come fa Python. Non sono obbligatori, ma usarli dove serve chiarezza è un'ottima abitudine: eliminano la classe di bug che nasce dal passare i parametri nell'ordine sbagliato.

## Gli union type (PHP 8)

L'ultima novità di questo capitolo, sempre di PHP 8, sono gli **union type**: la possibilità di specificare **più di un tipo** per un parametro o per il ritorno. Si scrivono elencando i tipi separati dalla **barra verticale** `|` (il carattere *pipe*).

Riprendiamo la somma. Se la dichiariamo con parametri `int` ma vogliamo accettare anche numeri decimali, l'editor ci segnala che passare `5.5` è un errore di tipo. La soluzione è un union type `int|float`, sia per i parametri sia per il ritorno:

```php
<?php

function somma(int|float $a, int|float $b): int|float
{
    return $a + $b;
}

echo somma(5.5, 4); // 9.5
```

Codice completo: [listing-49.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-49.php)


Ora la funzione accetta interi e decimali indifferentemente, e può restituire l'uno o l'altro. Possiamo combinare qualunque dei tipi visti finora: scalari, `array`, classi, interfacce, `callable`. Esiste anche il tipo speciale **`mixed`**, che significa "di qualunque tipo": è il più ampio possibile, e usarlo come tipo equivale a non porre alcun vincolo.

Anche `null` può far parte di un union type:

```php
function somma(int|float $a, int|float $b): int|float|null
{
    // ...
}
```

Codice completo: [listing-50.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-50.php)


Quando però l'unione è tra **un solo tipo e `null`**, la scrittura `?tipo` che abbiamo visto per i parametri nullable è una scorciatoia equivalente: `?float` è esattamente `float|null`. Per unire `null` a più tipi, invece, dobbiamo usare la forma estesa `float|int|null`.

C'è un tipo che **non può** comparire in un union type: **`void`**. `void` indica l'assenza totale di valore di ritorno (la funzione non ritorna nulla), quindi è incompatibile con qualunque altro tipo: se dichiariamo `void`, dobbiamo rimuovere del tutto il `return`, ed è concettualmente diverso dal ritornare `null`.

Gli union type valgono anche per i **metodi** delle classi e, sempre da PHP 8, per la **tipizzazione delle proprietà** — cosa che prima non era possibile. Ne riparleremo nella Parte VII, ma vale la pena anticiparlo:

```php
class Persona
{
    public string|int $name;
}
```

Codice completo: [listing-51.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/it/parte-03/cap-10/listing-51.php)


Un caso interessante è `string|Stringable`: significa che il valore può essere una stringa oppure un **oggetto** che implementa il metodo magico `__toString()` (quindi convertibile a stringa). Vedremo i metodi magici nella parte a oggetti; per ora ci basti sapere che gli union type ci danno un controllo dei tipi molto più espressivo di prima.

## In sintesi

- Una **funzione** raggruppa un blocco di istruzioni sotto un nome e si dichiara con `function`, le parentesi tonde e le graffe; si invoca scrivendo il nome seguito dalle tonde. Il nome non è case sensitive.
- Una funzione può essere **assegnata a una variabile** (`$fn = function () { ... };`): a differenza di quella con nome, non può essere chiamata prima della sua definizione.
- I **parametri** sono le variabili dichiarate nella funzione; gli **argomenti** sono i valori che passiamo alla chiamata. I parametri possono avere un **valore di default**, che va messo in fondo all'elenco.
- Da PHP 7 possiamo dichiarare il **tipo** di parametri e ritorno (`int`, `float`, `string`, `bool`, `array`, `callable`, classi, `void`); con `declare(strict_types=1)` in cima al file PHP verifica i tipi senza conversioni implicite.
- Si restituisce un valore con **`return`**; per ritornarne più di uno si usa un **array**, che possiamo poi **destrutturare** con `[$a, $b] = ...` o con `list()`.
- Da PHP 7.1 il **`?`** davanti al tipo rende un parametro o il ritorno **nullable**; per rendere un parametro anche omissibile serve un valore di default.
- Ogni funzione ha il proprio **scope**: le variabili esterne non sono visibili al suo interno, se non importate con **`global`** o tramite la superglobale **`$GLOBALS`** (o passate come argomenti, scelta preferibile).
- Le **funzioni anonime** (closure) si assegnano a variabili e si passano come `callable` ad altre funzioni; sono la base delle callback per gli array (`array_map`, `array_filter`, `array_walk`).
- Le **arrow function** (PHP 7.4) — `fn($x) => espressione` — sono una forma compatta a riga singola che **eredita automaticamente** lo scope esterno, senza bisogno di `use`.
- Le **variadic function** raccolgono un numero variabile di argomenti con il rest parameter `...$values` (tipizzabile e combinabile con parametri posizionali), sostituendo il vecchio `func_get_args()`.
- I **named argument** (PHP 8) permettono di passare gli argomenti per nome (`nome: valore`) in qualunque ordine; un argomento posizionale non può seguirne uno per nome.
- Gli **union type** (PHP 8) — `int|float`, `float|int|null`, `mixed` — dichiarano più tipi ammessi per un parametro, un ritorno o una proprietà; `void` non può far parte di un'unione.
