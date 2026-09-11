# 12. Funzioni per gli array

Gli array sono una delle strutture più usate in PHP. Li userai per liste, configurazioni, risultati del database, dati dei form, messaggi di errore e collezioni di oggetti. Conoscere le funzioni principali ti permette di scrivere codice più breve e più chiaro.

## Aggiungere e rimuovere elementi

Per aggiungere in coda:

```php
<?php
$names = ["Mario", "Lucia"];

array_push($names, "Giulia");
```

Codice completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/it/parte-03/cap-12/listing-01.php)


In PHP è molto comune usare la sintassi breve:

```php
<?php
$names[] = "Giulia";
```

Codice completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/it/parte-03/cap-12/listing-02.php)


Per togliere l'ultimo elemento:

```php
<?php
$last = array_pop($names);
```

Codice completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/it/parte-03/cap-12/listing-03.php)


Per lavorare all'inizio dell'array:

```php
<?php
array_unshift($names, "Anna");
$first = array_shift($names);
```

Codice completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/it/parte-03/cap-12/listing-04.php)


Queste funzioni modificano l'array originale.

## Ordinare array

`sort()` ordina i valori e reindicizza l'array:

```php
<?php
$numbers = [3, 1, 2];
sort($numbers);
```

Codice completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/it/parte-03/cap-12/listing-05.php)


Quando hai chiavi associative e vuoi mantenerle:

```php
<?php
$scores = [
    "mario" => 12,
    "lucia" => 18,
    "anna" => 15,
];

asort($scores);
```

Codice completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/it/parte-03/cap-12/listing-06.php)


`asort()` ordina per valore mantenendo l'associazione con la chiave. Per ordinare in modo naturale, utile con stringhe che contengono numeri, usa `natsort()`:

```php
<?php
$files = ["file10.txt", "file2.txt", "file1.txt"];
natsort($files);
```

Codice completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/it/parte-03/cap-12/listing-07.php)


## Trasformare con `array_map()`

`array_map()` applica una funzione a ogni elemento e restituisce un nuovo array:

```php
<?php
$prices = [10, 20, 30];

$withVat = array_map(function (int $price): float {
    return $price * 1.22;
}, $prices);
```

Codice completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/it/parte-03/cap-12/listing-08.php)


Con le arrow function:

```php
<?php
$withVat = array_map(fn (int $price): float => $price * 1.22, $prices);
```

Codice completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/it/parte-03/cap-12/listing-09.php)


È una buona scelta quando vuoi trasformare dati senza modificare l'array originale.

## Visitare con `array_walk()`

`array_walk()` esegue una funzione su ogni elemento. Può ricevere anche la chiave:

```php
<?php
$user = [
    "name" => "Mario",
    "email" => "mario@example.com",
];

array_walk($user, function ($value, $key) {
    echo "$key: $value" . PHP_EOL;
});
```

Codice completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/it/parte-03/cap-12/listing-10.php)


Usa `array_walk()` quando vuoi attraversare un array per produrre un effetto, non quando vuoi costruire una nuova collezione. Per trasformare, `array_map()` è più chiaro.

## Filtrare

`array_filter()` conserva solo gli elementi che soddisfano una condizione:

```php
<?php
$numbers = [1, 2, 3, 4, 5, 6];

$even = array_filter($numbers, fn (int $n): bool => $n % 2 === 0);
```

Codice completo: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/it/parte-03/cap-12/listing-11.php)


Attenzione: `array_filter()` mantiene le chiavi originali. Se vuoi reindicizzare:

```php
<?php
$even = array_values($even);
```

Codice completo: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/it/parte-03/cap-12/listing-12.php)


## Destrutturazione

La destrutturazione permette di assegnare elementi di un array a più variabili:

```php
<?php
$point = [10, 20];

[$x, $y] = $point;
```

Codice completo: [listing-13.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/it/parte-03/cap-12/listing-13.php)


Funziona anche con chiavi associative:

```php
<?php
$user = [
    "name" => "Mario",
    "email" => "mario@example.com",
];

["name" => $name, "email" => $email] = $user;
```

Codice completo: [listing-14.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/it/parte-03/cap-12/listing-14.php)


È molto leggibile quando una funzione ritorna più valori:

```php
<?php
function split_name(string $fullName): array
{
    return explode(" ", $fullName, 2);
}

[$firstName, $lastName] = split_name("Mario Rossi");
```

Codice completo: [listing-15.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/it/parte-03/cap-12/listing-15.php)


## Destrutturazione asimmetrica

Non sempre ti servono tutti gli elementi:

```php
<?php
$row = [10, "Mario", "Rossi", "mario@example.com"];

[$id, $name,, $email] = $row;
```

Codice completo: [listing-16.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/it/parte-03/cap-12/listing-16.php)


La virgola vuota salta un valore. Non abusarne: se gli elementi diventano molti, un array associativo o un oggetto è più chiaro.

## In sintesi

Le funzioni sugli array ti permettono di pensare in termini di operazioni: aggiungere, rimuovere, ordinare, trasformare, filtrare, destrutturare. Nei progetti del libro useremo queste tecniche per gestire risultati SQL, errori di validazione, configurazioni e dati di sessione. La regola pratica è semplice: scegli la funzione che esprime meglio l'intenzione del codice.
