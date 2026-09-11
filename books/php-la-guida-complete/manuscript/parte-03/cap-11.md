# 11. Funzioni per le stringhe

Le stringhe sono ovunque: nomi, email, URL, messaggi, template, query string, contenuti letti da file e dati ricevuti da form. PHP offre molte funzioni dedicate e in questo capitolo vediamo quelle che userai più spesso.

## Pulire una stringa

Quando ricevi testo dall'esterno devi aspettarti spazi, maiuscole incoerenti e caratteri non previsti. Le prime funzioni da conoscere sono `trim()`, `strtolower()` e `strtoupper()`.

```php
<?php
$email = "  MARIO@Example.COM  ";

$email = trim($email);
$email = strtolower($email);

echo $email; // mario@example.com
```

Codice completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/it/parte-03/cap-11/listing-01.php)


`trim()` elimina gli spazi all'inizio e alla fine. Non modifica gli spazi interni, quindi `"Mario Rossi"` resta `"Mario Rossi"`.

## Cercare dentro una stringa

Per anni la funzione più comune per cercare una sottostringa è stata `strpos()`:

```php
<?php
$url = "https://example.com/manuale/php";

if (strpos($url, "php") !== false) {
    echo "La stringa contiene php";
}
```

Codice completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/it/parte-03/cap-11/listing-02.php)


Il confronto deve essere `!== false`, non `!= false`, perché `strpos()` può restituire `0` quando il testo cercato si trova all'inizio della stringa. `0` è un valore valido, ma in un confronto debole verrebbe interpretato come `false`.

Da PHP 8 esistono funzioni più leggibili:

```php
<?php
$name = "index.php";

var_dump(str_contains($name, ".php"));
var_dump(str_starts_with($name, "index"));
var_dump(str_ends_with($name, ".php"));
```

Codice completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/it/parte-03/cap-11/listing-03.php)


Quando puoi usare PHP 8, preferisci queste funzioni: comunicano l'intenzione del codice senza dover ricordare il comportamento particolare di `strpos()`.

## Sostituire testo

`str_replace()` sostituisce tutte le occorrenze:

```php
<?php
$title = "Manuale PHP base";

echo str_replace("base", "completo", $title);
```

Codice completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/it/parte-03/cap-11/listing-04.php)


Puoi passare anche array:

```php
<?php
$text = "Ciao {name}, benvenuto in {topic}.";

echo str_replace(
    ["{name}", "{topic}"],
    ["Mario", "PHP"],
    $text
);
```

Codice completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/it/parte-03/cap-11/listing-05.php)


Questa tecnica è utile per piccoli template, ma non sostituisce un vero motore di template quando l'interfaccia cresce.

## Dividere e unire

`explode()` divide una stringa in un array:

```php
<?php
$csv = "mario,rossi,mario@example.com";

$parts = explode(",", $csv);
print_r($parts);
```

Codice completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/it/parte-03/cap-11/listing-06.php)


`implode()` fa l'operazione inversa:

```php
<?php
$tags = ["php", "mysql", "web"];

echo implode(", ", $tags);
```

Codice completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/it/parte-03/cap-11/listing-07.php)


`join()` è un alias di `implode()`. Nel codice moderno è meglio usare `implode()` perché è più riconoscibile.

## Escape e slash

`stripslashes()` rimuove backslash aggiunti prima di caratteri come apici e virgolette:

```php
<?php
$value = "L\\'utente";
echo stripslashes($value);
```

Codice completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/it/parte-03/cap-11/listing-08.php)


Oggi non dovresti costruire query SQL aggiungendo slash manualmente. Per il database useremo prepared statement. Le funzioni sulle stringhe servono a trasformare testo, non a inventare protezioni di sicurezza fragili.

## Lunghezza e porzioni

Per conoscere la lunghezza:

```php
<?php
echo strlen("PHP");
```

Codice completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/it/parte-03/cap-11/listing-09.php)


Per estrarre una parte:

```php
<?php
$code = "IT-2026-001";

echo substr($code, 0, 2);  // IT
echo substr($code, -3);    // 001
```

Codice completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/it/parte-03/cap-11/listing-10.php)


Con testo Unicode, accentato o multibyte, valuta le funzioni `mb_*`, come `mb_strlen()` e `mb_substr()`. `strlen("è")` non conta "caratteri visibili", conta byte.

## Normalizzare input utente

Un esempio completo:

```php
<?php
function normalize_email(string $email): string
{
    return strtolower(trim($email));
}

$email = normalize_email($_POST["email"] ?? "");
```

Codice completo: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/it/parte-03/cap-11/listing-11.php)


Normalizzare non significa validare. Dopo la normalizzazione puoi controllare:

```php
<?php
if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    echo "Email non valida";
}
```

Codice completo: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/it/parte-03/cap-11/listing-12.php)


## In sintesi

Le funzioni per le stringhe sono piccole, ma decidono la qualità di moltissimo codice. Usa `trim()` e `strtolower()` per normalizzare, `str_contains()` e funzioni simili per leggere meglio le condizioni, `str_replace()` per sostituzioni semplici, `explode()` e `implode()` per passare da stringhe ad array. Quando lavori con dati esterni, separa sempre trasformazione, validazione e sicurezza.
