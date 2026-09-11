# 9. Le strutture di controllo

Fino a questo punto i nostri script sono stati eseguiti riga per riga, dall'alto verso il basso, senza mai deviare. I programmi reali, però, devono prendere decisioni ed eseguire azioni ripetute: mostrare un messaggio solo se l'utente ha effettuato il login, elencare tutti i record restituiti da una query, ripetere un calcolo finché una condizione non è soddisfatta. A questo servono le **strutture di controllo**, il tema di questo capitolo.

Vedremo prima i costrutti condizionali — `if`/`elseif`/`else`, `switch` e il moderno `match` introdotto da PHP 8 — e poi i cicli: `while`, `do-while`, `for` e `foreach`. Sono costrutti che ritroverai, con sintassi quasi identica, in C, Java, JavaScript e in tanti altri linguaggi: impararli bene in PHP significa avere una base solida per tutta la programmazione. Per provare gli esempi ti basta una cartella di lavoro (ad esempio `control-structures`) con un file `index.php`, servita dal server integrato di PHP che abbiamo imparato ad avviare nei capitoli precedenti:

```bash
php -S localhost:8000
```

Codice completo: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-01.sh)


## Prendere decisioni: if, elseif, else

### La condizione più semplice

La struttura `if` accetta tra parentesi tonde un'**espressione di controllo** che deve restituire un valore booleano: se l'espressione vale `true`, il blocco di codice tra graffe viene eseguito; se vale `false`, viene saltato.

Qui torna in gioco la regola dei booleani che abbiamo studiato nel Capitolo 7 e che vale la pena ripetere: per PHP sono `false` la stringa vuota, il numero `0`, la stringa `"0"`, `null` (e pochi altri valori); **qualunque altra cosa viene convertita a `true`**. Tutte le strutture di controllo che vedremo — `if`, `switch` e le altre — lavorano su un'espressione booleana, e se l'espressione non è già un booleano PHP esegue il cast in automatico.

Partiamo da una variabile `$money` e dalla verifica più semplice possibile:

```php
<?php

$money = 30;

if ($money) {
    echo 'Hai dei soldi';
}
```

Codice completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-02.php)


Aprendo la pagina nel browser vediamo `Hai dei soldi`: `30` non è tra i valori "falsi", quindi il cast a booleano produce `true` e l'`echo` viene eseguito. Dentro le parentesi possiamo mettere qualunque espressione che restituisca un booleano: un confronto come `$money > 100`, `$money <= 50` e così via.

Possiamo anche negare l'espressione con l'operatore `!` visto nel Capitolo 8:

```php
if (!$money) {
    echo 'Non hai dei soldi';
}
```

Codice completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-03.php)


Con `$money = 30` questo blocco non viene eseguito: `$money` è `true`, quindi `!$money` è `false`.

### else: l'alternativa

Se vogliamo mostrare un risultato anche quando la condizione è falsa, aggiungiamo un ramo `else`:

```php
if ($money) {
    echo 'Hai dei soldi';
} else {
    echo 'Non hai dei soldi';
}
```

Codice completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-04.php)


Con `$money = 30` compare `Hai dei soldi`; se assegniamo `$money = 0` compare `Non hai dei soldi`. Vale lo stesso per qualunque valore che PHP consideri falso: la costante `false`, la stringa vuota `''` e gli altri visti sopra. Al contrario, qualunque valore fuori da quella lista fa passare il ramo `if`.

Come organizzare i due rami è una scelta di stile: possiamo verificare prima il caso "vero" e mettere il caso "falso" nell'`else`, o invertire la condizione e scambiare i rami. Il comportamento non cambia; scegli la forma che rende il codice più leggibile.

### elseif: più condizioni in cascata

Un solo `if` con un solo `else` spesso non basta: possiamo concatenare più verifiche sulla stessa variabile con `elseif`. PHP accetta sia la forma unita `elseif` sia quella separata `else if`: sono entrambe valide.

```php
<?php

$money = 30;

if ($money <= 10) {
    echo 'Puoi comprare una pizza';
} elseif ($money > 10 && $money <= 20) {
    echo 'Puoi comprare una pizza e una birra';
} elseif ($money > 20 && $money <= 30) {
    echo 'Puoi andare al ristorante';
} else {
    echo 'Puoi portare un amico al ristorante';
}
```

Codice completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-05.php)


Le condizioni vengono valutate dall'alto verso il basso e viene eseguito **solo il primo ramo** la cui condizione risulta vera; l'`else` finale scatta come opzione di default quando nessuna condizione passa. Con `$money = 30` otteniamo `Puoi andare al ristorante` (30 è maggiore di 20 e minore o uguale a 30); con `10` otteniamo `Puoi comprare una pizza`; con `35` nessuna delle condizioni è vera e scatta l'`else`: `Puoi portare un amico al ristorante`.

Possiamo usare quanti `elseif` vogliamo, oppure fermarci a un semplice `if`/`else`. Un consiglio pratico: quando gli `elseif` in cascata cominciano a essere tanti, di solito conviene passare al costrutto `switch`, che vedremo tra poco.

### La sintassi alternativa per i template

Esiste una seconda sintassi per l'`if`, usata soprattutto quando mescoliamo PHP e HTML in un template e non vogliamo riempire il markup di parentesi graffe. Al posto della graffa di apertura si mettono i **due punti** (`:`), e il costrutto si chiude con `endif;`. Tra una parte e l'altra possiamo chiudere il tag PHP e scrivere HTML puro:

```php
<?php $money = 35; ?>

<?php if ($money): ?>
    <h2>Hai dei soldi</h2>
<?php else: ?>
    <h2>Non hai dei soldi</h2>
<?php endif; ?>
```

Codice completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-06.php)


Aprendo la pagina vediamo il messaggio dentro un `<h2>`, esattamente come se avessimo fatto `echo '<h2>Hai dei soldi</h2>';` restando dentro PHP. E allora perché usare questa forma? Il motivo è pratico: se il file passa nelle mani di un web designer poco abituato a PHP, con la sintassi a graffe basta un `echo` cancellato o un punto e virgola perso per rompere la pagina. Con la sintassi alternativa, invece, l'HTML resta HTML: chiunque può modificare il markup senza toccare il codice PHP. È per questo che la trovi in quasi tutti i template PHP (esistono le forme corrispondenti anche per i cicli, come `endwhile`, `endfor` ed `endforeach`).

Due regole da ricordare. Primo: in una view non dovrebbe esserci troppa logica; se ti ritrovi con più di un `if` e un `elseif` dentro un template, quella logica sta meglio in un file PHP separato (un controller), non nella view. Secondo: **le due sintassi non si possono mescolare** — o usi le graffe o usi i due punti con `endif;`. Aprire con una graffa e chiudere con `endif;` (o viceversa) è un errore di sintassi.

## Il costrutto switch

Quando una catena di `if`/`elseif`/`elseif` confronta sempre la stessa espressione con valori diversi, possiamo raggrupparla in uno `switch`, più leggibile. Lo `switch` valuta l'espressione che gli passiamo tra parentesi e la confronta con i valori dei vari `case`: appena trova una corrispondenza, comincia a eseguire le istruzioni da quel punto in poi.

Attenzione però a un dettaglio che sorprende molti principianti: trovata la corrispondenza, lo `switch` **continua a eseguire tutte le righe successive**, anche quelle degli altri `case`, finché non incontra un `break`. Vediamolo subito:

```php
<?php

$money = 1;

switch ($money) {
    case 1:
        echo 'Hai 1 euro';
    case 2:
        echo 'Hai 2 euro';
}
```

Codice completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-07.php)


Cosa apparirà nel browser? Verrebbe da rispondere solo `Hai 1 euro`, e invece compaiono **entrambe** le stringhe: `Hai 1 euro` e `Hai 2 euro`. È il cosiddetto *fall-through*, ed è una fonte classica di bug in tantissimi applicativi. Appena lo `switch` trova la corrispondenza con `1`, esegue tutto quello che segue finché non trova un `break`.

### break: uscire dallo switch

Il `break` fa uscire immediatamente dallo `switch`. Aggiungiamolo al primo `case`:

```php
switch ($money) {
    case 0:
        echo 'Non hai soldi';
    case 1:
        echo 'Hai 1 euro';
        break;
    case 2:
        echo 'Hai 2 euro';
}
```

Codice completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-08.php)


Con `$money = 1` ora compare solo `Hai 1 euro`: trovata la corrispondenza, l'`echo` viene eseguito, il `break` fa uscire e il `case 2` non viene mai raggiunto. Nota che il `case 0` non c'entra: PHP lo esamina, non trova corrispondenza e passa oltre. Se invece togliamo il `break` dal `case 1`, l'esecuzione prosegue e vengono stampate due stringhe. Un `break` sull'ultimo `case` è tecnicamente inutile (lo `switch` finisce comunque), ma fai sempre attenzione a **dove** metti i `break`: il risultato può cambiare completamente.

### default: quando nessun case corrisponde

Come l'`else` finale di una catena di `if`, lo `switch` può avere un ramo `default` che viene eseguito quando nessun `case` trova corrispondenza:

```php
switch ($money) {
    case 0:
        echo 'Non hai soldi';
    case 1:
        echo 'Hai 1 euro';
        break;
    case 2:
        echo 'Hai 2 euro';
        break;
    default:
        echo 'Valore non valido';
}
```

Codice completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-09.php)


Con `$money = 3` compare `Valore non valido`: 3 non è uguale a 0, né a 1, né a 2, quindi si passa al `default`. Con `$money = 0`, invece, occhio al fall-through: manca il `break` dopo il `case 0`, quindi vediamo `Non hai soldi` seguito da `Hai 1 euro` (l'esecuzione si ferma al `break` del `case 1`). Se vogliamo che con 0 esca subito, dobbiamo aggiungere il `break` anche lì. Il `default`, comunque, scatta solo in assenza di corrispondenze: il fall-through da un `case` precedente non ci arriva se prima incontra un `break`.

### Raggruppare i case

Il fall-through non è solo un pericolo: usato di proposito, è il modo idiomatico per assegnare **lo stesso blocco di istruzioni a più valori**. Basta scrivere dei `case` vuoti uno sopra l'altro:

```php
    case 3:
    case 4:
        echo 'Hai 3 o 4 euro';
        break;
```

Codice completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-10.php)


Sia con `$money = 3` sia con `$money = 4` compare `Hai 3 o 4 euro`: il `case 3` non contiene istruzioni, quindi l'esecuzione "cade" nel `case 4` e si ferma al `break`.

Due note di stile. Se dentro un `case` ti ritrovi un blocco di codice corposo, è un segnale che l'applicazione non è disegnata bene: quel codice dovrebbe stare in una funzione, che il `case` si limita a chiamare. Puoi comunque racchiudere il corpo di un `case` tra graffe — non è obbligatorio, ma aiuta l'editor (e te) a vedere dove inizia e dove finisce ogni ramo. Infine, dopo il valore del `case` PHP accetta anche il punto e virgola al posto dei due punti (`case 1;`), ma è una forma poco usata: attieniti ai due punti, che è la convenzione in PHP come negli altri linguaggi.

### Il confronto debole: un tranello da esame

C'è un comportamento dello `switch` che devi assolutamente conoscere. Proviamo:

```php
$money = false;

switch ($money) {
    case 0:
        echo 'Non hai soldi';
        break;
    // ...
    default:
        echo 'Valore non valido';
}
```

Codice completo: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-11.php)


Cosa ti aspetti? Verrebbe da dire `Valore non valido`: `false` non è `0`. E invece compare `Non hai soldi`. Perché? Perché lo `switch` confronta con l'**uguaglianza debole** (`==`), non con quella stretta (`===`): quando deve confrontare `false` con l'intero `0`, PHP fa il cast implicito di `false` a integer, che vale `0`, e `0 == 0` è vero. Se vuoi che il confronto avvenga su un integer "vero", puoi fare tu il cast esplicito del valore prima dello `switch` — ma tieni sempre presente che, se non lo fai, PHP lo fa per te secondo le sue regole.

Questi "trucchi" di PHP vanno imparati bene: sono esattamente il tipo di domanda che può capitarti nell'esame **Zend Certified Engineer**, la certificazione standard di PHP, e sono anche il tipo di dettaglio che genera bug subdoli nel codice di produzione. Con la pratica diventeranno naturali — e nel prossimo paragrafo vediamo il costrutto che PHP 8 ha introdotto proprio per eliminare questo problema.

## match: lo switch moderno di PHP 8

Da PHP 8 in avanti esiste un costrutto chiamato **`match`** che risolve entrambe le debolezze dello `switch`: fa il **confronto stretto** (valore *e* tipo, come `===`) ed è un'**espressione**, cioè restituisce un valore che possiamo assegnare a una variabile. Uno `switch`, al contrario, non restituisce niente: scrivere `$test = switch (...)` è un errore di sintassi, e l'editor ce lo segnala subito.

### La sintassi

`match` valuta l'espressione tra parentesi e la confronta con le "chiavi" dei suoi rami, scritti con la stessa freccia `=>` che PHP usa per gli array associativi chiave-valore: a sinistra il valore (o i valori) da confrontare, a destra l'espressione da valutare — e restituire — in caso di corrispondenza. A differenza dello `switch` non serve alcun `break`: trovata la corrispondenza, `match` valuta quel ramo ed esce. Le graffe qui sono parte obbligatoria della sintassi, e i rami sono separati da virgole.

Riprendiamo l'esempio del confronto con `false` e mettiamo a confronto i due costrutti:

```php
<?php

$money = false;

// switch: confronto debole
switch ($money) {
    case 0:
        echo 'Non hai soldi (switch)';
        break;
}

// match: confronto stretto
match ($money) {
    1 > 2 => print 'false',
    0     => print 'Non hai soldi',
    1     => print 'Hai 1 euro',
    2     => print 'Hai 2 euro',
};
```

Codice completo: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-12.php)


Lo `switch` stampa `Non hai soldi (switch)`: fa il cast e `false == 0`. Il `match` invece stampa `false`: il confronto è stretto, quindi `$money` (che vale `false`) **non** corrisponde all'intero `0`; corrisponde invece al primo ramo, perché l'espressione `1 > 2` vale esattamente `false`. Già da questo esempio vedi due cose: `match` non fa alcun cast, e come "chiave" di un ramo possiamo usare qualunque espressione, non solo valori letterali.

Una curiosità sull'esempio: nei rami abbiamo usato `print` invece di `echo`. Il motivo è che ogni ramo di `match` deve essere un'**espressione** che produce un valore, e `echo` non lo è; `print` invece stampa a video *e* restituisce sempre `1`. Infatti, se catturiamo il risultato:

```php
$result = match ($money) {
    0 => print 'Non hai soldi',
    // ...
    default => print 'Nessuno dei valori'
};

var_dump($result); // int(1)
```

Codice completo: [listing-13.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-13.php)


`var_dump($result)` mostra `int(1)`: il valore restituito da `print`. Se invece vogliamo che il ramo restituisca la stringa senza stamparla, potremmo usare `print_r($valore, true)` — con `true` come secondo parametro, `print_r()` non stampa ma **restituisce** la stringa — ma in realtà non serve scomodare nessuna funzione: basta mettere direttamente la stringa come valore del ramo. È la forma più pulita e più usata:

```php
$result = match ($money) {
    0      => 'Non hai soldi',
    1      => 'Hai 1 euro',
    2      => 'Hai 2 euro',
    3, 4   => 'Hai 3 o 4 euro',
    default => 'Nessuno dei valori'
};

echo $result;
```

Codice completo: [listing-14.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-14.php)


Nota il ramo `3, 4`: per associare più valori allo stesso risultato non servono i `case` vuoti in cascata dello `switch`, basta elencare i valori separati da virgola. Dopo l'ultimo ramo la virgola è facoltativa: puoi ometterla o lasciarla (lasciarla è comodo quando aggiungi rami in coda). E ricorda che `match (...) { ... }` usato come istruzione va chiuso con il punto e virgola.

### default è (quasi) obbligatorio

Rifacciamo il test del confronto stretto con i tipi. Se in uno `switch` scriviamo `case 3:` e passiamo la **stringa** `'3'`, il cast implicito la trasforma in numero e la corrispondenza scatta. Con `match`, la stringa `'3'` e l'intero `3` sono valori di tipo diverso: nessuna corrispondenza. E se nessun ramo corrisponde e non c'è un `default`, `match` non resta zitto come lo `switch`: lancia un errore fatale:

```text
PHP Fatal error:  Uncaught UnhandledMatchError:
Unhandled match case of type string
```

Codice completo: [listing-15.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-15.txt)


Quindi: mentre nello `switch` il `default` è sempre facoltativo, in un `match` devi mettere il ramo `default` ogni volta che non sei *certo* che il valore corrisponda a uno dei rami — altrimenti devi gestire l'eccezione con un blocco `try`/`catch`, che studieremo nel Capitolo 32.

### switch o match?

Riassumiamo le differenze:

| | `switch` | `match` |
|---|---|---|
| Restituisce un valore | no | sì (è un'espressione) |
| Tipo di confronto | debole (`==`), con cast implicito | stretto (`===`), valore e tipo |
| `break` | necessario per evitare il fall-through | non serve |
| `default` | facoltativo | necessario se il valore può non corrispondere (altrimenti `UnhandledMatchError`) |
| Corpo dei rami | più istruzioni per `case` | una sola espressione per ramo |

L'ultima riga merita una precisazione: in un ramo di `match` non puoi mettere più istruzioni separate da punto e virgola — la struttura funziona come un array di coppie chiave-valore. Se in un ramo ti servono più azioni, scrivi una funzione e chiamala come valore del ramo: la chiamata è un'espressione e il suo risultato diventa il valore restituito.

Il mio consiglio, da PHP 8 in poi: se devi confrontare un valore in modo stretto e restituire un risultato (o chiamare una funzione), usa `match` — la sintassi è molto più semplice e pulita. Se invece per ogni valore devi eseguire diverse azioni in sequenza, conviene ancora lo `switch`.

## I cicli while e do-while

Passiamo ai cicli. Il costrutto **`while`** si traduce letteralmente "mentre": *mentre* l'espressione tra parentesi tonde è vera, PHP esegue l'istruzione che segue — o il blocco di istruzioni tra graffe. La condizione viene verificata **all'inizio** di ogni giro.

Il **`do-while`** fa la stessa cosa, ma verifica la condizione **alla fine**: il blocco viene quindi eseguito almeno una volta, e solo dopo si decide se ripetere. È l'unica differenza tra i due.

### while: la condizione prima

Cominciamo con un ciclo che stampa i numeri da 1 a 10:

```php
<?php

$i = 1;

while ($i <= 10) {
    echo $i . '<br>';
    $i++;
}
```

Codice completo: [listing-16.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-16.php)


Nel browser compaiono i numeri da 1 a 10, uno per riga. Analizziamo i pezzi. Prima del ciclo inizializziamo il contatore `$i` a 1. La condizione `$i <= 10` viene controllata a ogni giro; dentro il blocco stampiamo il valore e — fondamentale — lo **incrementiamo** con l'operatore `++` visto nel Capitolo 8 (qui va bene la forma postfissa, tanto non stiamo assegnando il risultato a nessuna variabile). Visto che le istruzioni sono due, il blocco va racchiuso tra graffe.

Cosa succederebbe senza l'incremento? `$i` resterebbe per sempre a 1, sempre minore o uguale a 10, e il ciclo girerebbe **all'infinito**, bloccando lo script. È l'errore classico con i `while`: assicurati sempre che dentro il ciclo qualcosa faccia prima o poi diventare falsa la condizione.

E se inizializziamo `$i = 11`? Il browser non mostra nulla: la condizione è falsa fin dal primo controllo e il corpo del ciclo non viene eseguito nemmeno una volta.

### do-while: almeno un'esecuzione

Riscriviamo lo stesso ciclo nella variante `do-while`, partendo proprio da `$i = 11`:

```php
$i = 11;

do {
    echo $i . '<br>';
    $i++;
} while ($i <= 10);
```

Codice completo: [listing-17.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-17.php)


Questa volta il browser mostra `11`. Il blocco `do` viene eseguito subito: stampa 11, incrementa a 12, e solo a quel punto verifica la condizione — 12 non è minore o uguale a 10, quindi il ciclo non si ripete. Se invece partiamo da `$i = 1`, otteniamo i numeri da 1 a 10 esattamente come col `while`. La regola da ricordare: **il `do-while` esegue il corpo almeno una volta**, il `while` può non eseguirlo mai.

### Un esempio pratico: generare una lista HTML

Usiamo il `while` per qualcosa di più concreto: scorrere un array di colori e mostrarlo come lista HTML. Non sappiamo a priori quanti elementi contiene l'array — potremmo contarli a occhio, ma non serve: la funzione `count()` di PHP ci dice quanti elementi ha un array.

```php
<?php
$ar = ['red', 'blue', 'green', 'yellow'];
$total = count($ar);
?>
<!DOCTYPE html>
<html>
<head>
    <title>Ciclo while</title>
    <style>
        body {
            background: #ccc;
            color: #000;
            font-size: 24px;
        }
    </style>
</head>
<body>
    <ul>
        <?php
        $i = 0;
        while ($i < $total) {
            echo "<li>{$ar[$i]}</li>";
            $i++;
        }
        ?>
    </ul>
</body>
</html>
```

Codice completo: [listing-18.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-18.php)


Abbiamo scritto una pagina HTML completa — doctype, `<head>` con un titolo (mettine sempre uno) e un minimo di CSS per rendere leggibile la lista — e dentro il `<ul>` abbiamo aperto PHP per generare le voci con il ciclo. Nel browser compaiono `red`, `blue`, `green`, `yellow` in una lista: abbiamo generato HTML dinamicamente da PHP.

Due dettagli importanti. Primo: il contatore parte da **zero**, perché gli array in PHP sono indicizzati dalla posizione 0. Secondo: la condizione usa `<` e non `<=`, perché l'ultimo indice valido è `$total - 1` — con quattro colori, il totale è 4 ma le posizioni sono 0, 1, 2, 3.

E anche qui, occhio all'incremento: durante la stesura di questo esempio è facilissimo dimenticare `$i++` e ritrovarsi con la pagina che gira all'infinito. Se ti succede, ferma il browser, aggiungi l'incremento e ricarica.

Questo schema — un ciclo che scorre una struttura e la trasforma in HTML — è esattamente quello che userai di continuo in PHP, ad esempio per mostrare a video l'elenco di record che una query restituisce da una tabella di un database. Per gli array, comunque, vedremo tra poco costrutti più comodi.

## Il ciclo for

Il ciclo **`for`** compatta in un'unica riga i tre ingredienti che col `while` abbiamo scritto sparsi: inizializzazione, condizione e incremento.

```php
for (espressione1; espressione2; espressione3) {
    // corpo del ciclo
}
```

Codice completo: [listing-19.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-19.php)


- **espressione1** serve per inizializzare le variabili e viene eseguita una sola volta, all'inizio;
- **espressione2** viene verificata all'inizio di ogni giro: se è `true` il ciclo continua, altrimenti si esce;
- **espressione3** viene eseguita alla fine di ogni giro (tipicamente è l'incremento del contatore).

Nessuna delle tre è obbligatoria: si possono omettere lasciando i punti e virgola.

Riprendiamo l'array dei colori — aggiungiamo un quinto colore, `pink` — e rifacciamo la lista con il `for`. Questa volta per l'output usiamo l'interpolazione nelle virgolette doppie che abbiamo studiato nel Capitolo 7, con le graffe intorno all'elemento di array:

```php
<?php

$ar = ['red', 'blue', 'green', 'yellow', 'pink'];

for ($i = 0; $i < count($ar); $i++) {
    echo "<li>{$ar[$i]}</li>";
}
```

Codice completo: [listing-20.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-20.php)


Funziona, ma possiamo migliorarlo. La seconda espressione viene rivalutata **a ogni giro**: così com'è, `count($ar)` viene richiamata per ogni elemento dell'array, inutilmente — il numero di elementi non cambia durante il ciclo. Conviene calcolarla una volta sola. Possiamo farlo prima del ciclo (`$tot = count($ar);`), oppure sfruttare il fatto che nella prima espressione del `for` possiamo mettere **più inizializzazioni separate da virgola**, eseguite solo la prima volta:

```php
for ($i = 0, $tot = count($ar); $i < $tot; $i++) {
    echo "<li>{$ar[$i]}</li>";
}
```

Codice completo: [listing-21.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-21.php)


Il risultato è identico, ma `count()` viene chiamata una sola volta.

### break e continue

Dentro un ciclo — `for`, `while` o `do-while` — possiamo usare due istruzioni di controllo del flusso. Le vediamo sul `for` perché è lì che si usano più spesso, ma valgono per tutti i cicli.

**`break`** esce immediatamente dal ciclo, come già visto per lo `switch`. Supponiamo di voler mostrare solo i primi tre colori:

```php
for ($i = 0, $tot = count($ar); $i < $tot; $i++) {
    echo "<li>{$ar[$i]}</li>";

    if ($i == 2) {
        break;
    }
}
```

Codice completo: [listing-22.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-22.php)


Gli indici partono da zero, quindi il terzo elemento è `$i == 2`: la pagina mostra `red`, `blue`, `green` e poi il `break` interrompe il ciclo — `yellow` e `pink` non vengono mai stampati. (Avremmo potuto ottenere lo stesso risultato cambiando la condizione del `for`, ma il `break` è la scelta giusta quando l'interruzione dipende da una verifica interna al ciclo.)

**`continue`** invece non esce dal ciclo: **salta al giro successivo**, ignorando tutte le istruzioni che seguono nel blocco corrente. Supponiamo di non voler mostrare `pink`:

```php
for ($i = 0, $tot = count($ar); $i < $tot; $i++) {
    if ($ar[$i] == 'pink') {
        continue;
    }

    echo "<li>{$ar[$i]}</li>";
}
```

Codice completo: [listing-23.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-23.php)


Quando il valore corrente è `pink`, il `continue` fa passare direttamente al giro successivo (l'incremento `$i++` viene comunque eseguito) e l'`echo` sotto non viene raggiunto: la lista si ferma a `yellow`, senza `pink`.

Una nota di stile che ripeterò spesso: negli esempi metto **sempre le graffe**, anche quando il blocco contiene una sola istruzione e le graffe non sarebbero obbligatorie. È una questione di correttezza e chiarezza del codice: previene errori quando in futuro aggiungerai una seconda istruzione al blocco.

## Cicli annidati

I cicli possono essere **annidati**: un ciclo dentro un altro. Supponiamo di voler mostrare la nostra lista di colori tre volte. Avvolgiamo il `for` esistente in un `for` esterno con un secondo contatore, `$j`:

```php
for ($j = 0; $j < 3; $j++) {
    for ($i = 0, $tot = count($ar); $i < $tot; $i++) {
        echo "$j {$ar[$i]}<br>";
    }
}
```

Codice completo: [listing-24.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-24.php)


Il ciclo interno viene ripetuto per intero a ogni giro di quello esterno: nel browser vediamo i cinque colori tre volte, ognuno preceduto dal numero del giro esterno (0, 1, 2) grazie all'interpolazione di `$j` nella stringa.

Per distinguere meglio un giro dall'altro, aggiungiamo una linea orizzontale dopo l'ultimo elemento di ogni lista. L'indice dell'ultimo colore (`pink`) è 4 — le posizioni sono 0, 1, 2, 3, 4 — quindi:

```php
for ($j = 0; $j < 3; $j++) {
    for ($i = 0, $tot = count($ar); $i < $tot; $i++) {
        if ($i == 4) {
            $hr = '<hr>';
        } else {
            $hr = '';
        }

        echo "$j {$ar[$i]}<br>" . $hr;
    }
}
```

Codice completo: [listing-25.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-25.php)


Ora i tre blocchi (giro 0, giro 1, giro 2) sono separati da una riga orizzontale.

### break e continue con più livelli

Ecco un dettaglio che pochi conoscono: in PHP sia `break` sia `continue` accettano un **argomento numerico** che indica da quanti livelli di annidamento uscire o quale livello continuare.

Proviamo a interrompere tutto quando il ciclo esterno arriva al giro 1, mettendo la verifica **dentro il ciclo interno**:

```php
for ($j = 0; $j < 3; $j++) {
    for ($i = 0, $tot = count($ar); $i < $tot; $i++) {
        if ($j == 1) {
            break; // esce solo dal ciclo interno!
        }

        echo "$j {$ar[$i]}<br>";
    }
}
```

Codice completo: [listing-26.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-26.php)


Il risultato non è quello che volevamo: vediamo i colori del giro 0 e **anche quelli del giro 2**. Il `break` semplice (equivalente a `break 1`) esce solo dal ciclo in cui si trova — quello interno; il ciclo esterno prosegue, e al giro 2 la condizione `$j == 1` non è più vera. Per uscire da **entrambi** i cicli dobbiamo scrivere:

```php
        if ($j == 1) {
            break 2; // esce dal ciclo interno E da quello esterno
        }
```

Codice completo: [listing-27.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-27.php)


Ora vediamo solo i colori del giro 0: arrivati a `$j == 1`, `break 2` attraversa due livelli di costrutti — e nel conteggio dei livelli valgono i `for`, i `while`, i `do-while` e anche gli `switch` — e l'esecuzione riprende dopo il ciclo esterno.

Lo stesso argomento numerico vale per `continue`. Se al posto di uscire vogliamo solo **saltare il giro 1** del ciclo esterno, mostrando il giro 0 e il giro 2:

```php
        if ($j == 1) {
            continue 2; // salta al prossimo giro del ciclo ESTERNO
        }
```

Codice completo: [listing-28.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-28.php)


`continue 2` abbandona il giro corrente del ciclo interno *e* di quello esterno, passando direttamente a `$j = 2`: nel browser compaiono le liste dei giri 0 e 2, senza il giro 1. Il numero dopo `break` o `continue`, quindi, indica quanti livelli di annidamento l'istruzione deve attraversare; senza numero, agisce solo sul ciclo più interno.

### Un esempio pratico: le tabelline

Chiudiamo i cicli annidati con un esempio classico: generare le tabelline. Usiamo un ciclo esterno per il moltiplicando (da 0 a 10) e uno interno per il moltiplicatore (potremmo anche fare viceversa):

```php
<?php

for ($i = 0; $i <= 10; $i++) {
    for ($j = 0; $j <= 10; $j++) {
        echo "$i x $j = " . ($i * $j) . '<br>';
    }
    echo '<hr>';
}
```

Codice completo: [listing-29.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-29.php)


Per ogni valore di `$i`, il ciclo interno scorre `$j` da 0 a 10 e stampa moltiplicando, moltiplicatore e risultato; la linea orizzontale dopo ogni ciclo interno separa una tabellina dall'altra. Nel browser vediamo la tabellina dello 0 (tutti zeri), quella dell'1, e così via fino a quella del 10: `0, 10, 20, 30... 100`. Funziona correttamente.

Come esercizio, prova a migliorare la presentazione: mostra le tabelline una a fianco all'altra usando le tabelle HTML — una tabella esterna con una colonna per ogni tabellina, e dentro ogni colonna una tabella interna con le righe della moltiplicazione. Aggiungi un po' di CSS per colorare gli sfondi: è un ottimo modo per fare pratica con i cicli annidati e la generazione di HTML.

## Il ciclo foreach

Abbiamo scorso gli array con `while` e con `for`, gestendo a mano contatore, `count()` e incremento. PHP però ha un ciclo pensato apposta per questo: **`foreach`**. È comodissimo per scorrere qualunque array — indicizzato, associativo chiave-valore o multidimensionale — e funziona anche sugli oggetti: iterando un oggetto, `foreach` scorre le sue proprietà pubbliche come se fossero coppie chiave-valore (le proprietà protette e private non sono accessibili dall'esterno; ne riparleremo nella Parte VII).

### La forma di base

La sintassi: `foreach`, poi tra parentesi l'array (o la variabile che lo contiene), la parola chiave `as` e una variabile che a ogni giro riceverà il valore corrente. Il nome della variabile lo scegli tu:

```php
<?php

$ar = ['red', 'blue', 'green', 'yellow', 'pink'];

foreach ($ar as $val) {
    echo "<h1>$val</h1>";
}
```

Codice completo: [listing-30.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-30.php)


Nel browser compaiono `red`, `blue`, `green`, `yellow`, `pink`, ognuno in un bel `<h1>`. Niente contatore, niente `count()`, niente incremento: `foreach` scorre da solo tutti gli elementi, dal primo all'ultimo.

### Chiavi e valori

Se ci servono anche le **chiavi**, usiamo la forma con la freccia `=>` — la stessa sintassi chiave-valore degli array associativi:

```php
foreach ($ar as $key => $val) {
    echo "<h1>$key -> $val</h1>";
}
```

Codice completo: [listing-31.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-31.php)


Con il nostro array indicizzato le chiavi sono numeriche: `0 -> red`, `1 -> blue`, e così via fino a `4 -> pink`.

Il bello è che funziona identico con le chiavi a stringa, e perfino con gli array "misti". Creiamo un secondo array in cui i primi due colori hanno una chiave in italiano e gli altri restano senza:

```php
$ar2 = ['rosso' => 'red', 'blu' => 'blue', 'green', 'yellow'];

foreach ($ar2 as $key => $val) {
    echo "<h1>$key -> $val</h1>";
}
```

Codice completo: [listing-32.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-32.php)


L'output mostra `rosso -> red`, `blu -> blue`, `0 -> green`, `1 -> yellow`: per gli elementi senza chiave esplicita PHP assegna in automatico le chiavi numeriche partendo da 0, e `foreach` scorre senza problemi sia le chiavi a stringa sia quelle numeriche nello stesso array — cosa che non tutti i costrutti di iterazione di altri linguaggi, JavaScript in testa, sanno fare con la stessa naturalezza.

### Modificare l'array: il valore per riferimento

Normalmente `$val` è una **copia** del valore corrente: modificarla non tocca l'array. Ma se anteponiamo la "e commerciale" `&`, la variabile diventa un **riferimento** all'elemento dell'array, e possiamo modificare l'array dall'interno del ciclo. Ad esempio, portiamo tutti i colori in maiuscolo con la funzione `strtoupper()`:

```php
foreach ($ar as &$val) {
    $val = strtoupper($val);
}

var_dump($ar);
```

Codice completo: [listing-33.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-33.php)


Il `var_dump()` conferma che i valori sono cambiati **dentro l'array**: `RED`, `BLUE`, `GREEN`, `YELLOW`, `PINK`.

Attenzione, però: c'è un tranello famoso. Dopo la fine del ciclo, `$val` **continua a essere un riferimento all'ultimo elemento** dell'array. Se più avanti nello script riutilizzi quella variabile:

```php
$val = 'nessun valore';

var_dump($ar); // l'ultimo elemento ora è 'nessun valore'!
```

Codice completo: [listing-34.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-34.php)


...non stai assegnando a una variabile qualunque: stai sovrascrivendo l'ultimo elemento dell'array — al posto di `PINK` ora c'è `nessun valore`. Per evitare il problema, **dopo un `foreach` per riferimento fai sempre l'`unset()` della variabile**:

```php
foreach ($ar as &$val) {
    $val = strtoupper($val);
}
unset($val); // elimina il riferimento

$val = 'nessun valore'; // ora è una variabile qualsiasi
var_dump($ar);          // l'array è intatto: PINK c'è ancora
```

Codice completo: [listing-35.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-35.php)


Con `unset($val)` la variabile non fa più riferimento all'array, e qualunque uso successivo non può più corromperlo. Te lo dico per esperienza: mi è capitato un bug esattamente così — un `foreach` per riferimento chiuso senza `unset()`, la stessa variabile riusata più avanti, e il valore dell'array principale sovrascritto in silenzio. Fai sempre attenzione.

### Array multidimensionali

Che succede se gli elementi dell'array sono a loro volta array? Costruiamone uno:

```php
$ar3 = [
    ['a', 'b', 'c'],
    [1, 2, 3],
];
```

Codice completo: [listing-36.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-36.php)


Alla posizione 0 c'è un array di lettere, alla posizione 1 un array di numeri (ricorda: PHP incrementa in automatico il contatore delle chiavi). Se proviamo il `foreach` semplice:

```php
foreach ($ar3 as $val) {
    echo "<h1>$val</h1>";
}
```

Codice completo: [listing-37.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-37.php)


PHP ci avvisa con un warning: `Array to string conversion`. Giusto: ogni `$val` qui è un array, e non si può farne l'`echo` come fosse una stringa. La soluzione è annidare un secondo `foreach` che scorra l'array interno:

```php
foreach ($ar3 as $val) {
    foreach ($val as $v) {
        echo "<h1>$v</h1>";
    }
}
```

Codice completo: [listing-38.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/it/parte-02/cap-09/listing-38.php)


Ora funziona: il `foreach` esterno scorre l'array principale, quello interno scorre l'array contenuto in ciascun valore, e a video compaiono `a`, `b`, `c`, `1`, `2`, `3`.

Con questo hai già una bella potenza di fuoco: PHP è fortissimo sugli array e, quando lo userai insieme a un database, i cicli saranno il pane quotidiano — e quasi sempre finirai per usare proprio il `foreach`. Studialo bene e sperimenta con esempi tuoi.

## In sintesi

- **`if`/`elseif`/`else`** esegue blocchi di codice in base a un'espressione booleana; PHP fa il cast automatico a booleano secondo le sue regole (sono falsi `0`, `''`, `'0'`, `null`, `false`). `elseif` e `else if` sono equivalenti.
- Nei template si usa la **sintassi alternativa** con i due punti e `endif;`, che permette di mescolare PHP e HTML senza graffe; le due sintassi non si possono mischiare.
- **`switch`** confronta un'espressione con più `case` usando l'uguaglianza **debole** (`==`, con cast implicito) e prosegue l'esecuzione (*fall-through*) finché non trova un **`break`**; `default` gestisce i valori senza corrispondenza. I `case` vuoti in cascata raggruppano più valori sulla stessa azione.
- **`match`** (da PHP 8) è un'espressione: restituisce un valore, usa il confronto **stretto** (`===`), non richiede `break`, accetta più valori separati da virgola e lancia `UnhandledMatchError` se nessun ramo corrisponde e manca `default`. Ogni ramo contiene una sola espressione: per azioni multiple, chiama una funzione.
- **`while`** verifica la condizione all'inizio (il corpo può non essere mai eseguito); **`do-while`** la verifica alla fine (il corpo viene eseguito almeno una volta). Assicurati sempre che qualcosa renda falsa la condizione, o il ciclo sarà infinito.
- **`for`** riunisce inizializzazione, condizione e incremento; la prima espressione accetta più inizializzazioni separate da virgola — comodo per calcolare `count()` una sola volta invece che a ogni giro.
- **`break`** esce dal ciclo, **`continue`** salta al giro successivo; con un argomento numerico (`break 2`, `continue 2`) agiscono su più livelli di cicli annidati.
- **`foreach`** è il ciclo naturale per gli array: `foreach ($ar as $val)` per i valori, `foreach ($ar as $key => $val)` per chiavi e valori; con `&$val` modifichi l'array per riferimento — ma ricordati sempre di fare **`unset($val)`** dopo il ciclo. Per gli array multidimensionali si annidano più `foreach`.
