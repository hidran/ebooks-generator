# 17. JSON

JSON è uno dei formati più usati per scambiare dati tra server, browser e API. È leggibile, compatto e si mappa bene su array e oggetti. In PHP lo userai per risposte AJAX, configurazioni, integrazioni con servizi esterni e REST API.

## Che cos'è JSON

JSON rappresenta dati con oggetti, array, stringhe, numeri, boolean e `null`:

```json
{
  "name": "Mario",
  "email": "mario@example.com",
  "roles": ["admin", "editor"],
  "active": true
}
```

Codice completo: [listing-01.json](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/it/parte-04/cap-17/listing-01.json)


Somiglia a JavaScript, ma è un formato dati, non codice. Le chiavi degli oggetti devono essere tra virgolette doppie e non puoi inserire commenti.

## Decodificare JSON in PHP

Per trasformare JSON in una struttura PHP si usa `json_decode()`:

```php
<?php
$json = '{"name":"Mario","active":true}';

$data = json_decode($json, true);

echo $data["name"];
```

Codice completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/it/parte-04/cap-17/listing-02.php)


Il secondo argomento `true` dice a PHP di restituire array associativi. Senza `true`, PHP restituisce oggetti `stdClass`:

```php
<?php
$data = json_decode($json);

echo $data->name;
```

Codice completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/it/parte-04/cap-17/listing-03.php)


Scegli una forma e mantienila coerente nel progetto. Nei primi esempi useremo spesso array associativi perché si collegano bene a ciò che abbiamo già studiato.

## Gestire errori di parsing

Un JSON non valido non deve essere ignorato:

```php
<?php
$data = json_decode($json, true);

if (json_last_error() !== JSON_ERROR_NONE) {
    echo json_last_error_msg();
}
```

Codice completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/it/parte-04/cap-17/listing-04.php)


Da PHP 7.3 puoi chiedere eccezioni:

```php
<?php
$data = json_decode($json, true, 512, JSON_THROW_ON_ERROR);
```

Codice completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/it/parte-04/cap-17/listing-05.php)


Questa forma è preferibile in codice moderno perché gli errori entrano nel normale flusso `try/catch`.

## Codificare dati PHP in JSON

Per generare JSON:

```php
<?php
$user = [
    "name" => "Mario",
    "email" => "mario@example.com",
];

echo json_encode($user);
```

Codice completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/it/parte-04/cap-17/listing-06.php)


Quando rispondi dal server, imposta il content type:

```php
<?php
header("Content-Type: application/json");

echo json_encode([
    "success" => true,
    "message" => "Utente salvato",
]);
```

Codice completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/it/parte-04/cap-17/listing-07.php)


Per evitare problemi con caratteri accentati puoi usare:

```php
<?php
echo json_encode($user, JSON_UNESCAPED_UNICODE);
```

Codice completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/it/parte-04/cap-17/listing-08.php)


## JSON nel browser

Lato client, JavaScript usa `JSON.parse()` e `JSON.stringify()`:

```javascript
const user = JSON.parse('{"name":"Mario"}');
console.log(user.name);

const payload = JSON.stringify({ name: "Mario" });
```

Codice completo: [listing-09.js](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/it/parte-04/cap-17/listing-09.js)


Quando useremo AJAX, il browser invierà dati al server o riceverà risposte in questo formato. Il server PHP non deve stampare HTML se il client si aspetta JSON: deve restituire solo dati.

## Un endpoint PHP semplice

Esempio di risposta JSON:

```php
<?php
header("Content-Type: application/json");

$users = [
    ["id" => 1, "name" => "Mario"],
    ["id" => 2, "name" => "Lucia"],
];

echo json_encode([
    "data" => $users,
    "count" => count($users),
], JSON_UNESCAPED_UNICODE);
```

Codice completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/it/parte-04/cap-17/listing-10.php)


Il browser riceve un oggetto con due proprietà: `data` e `count`. Questa struttura è più estendibile di un array nudo, perché puoi aggiungere metadati, paginazione o messaggi senza cambiare completamente il contratto.

## Validazione dei dati in ingresso

Se ricevi JSON:

```php
<?php
$raw = file_get_contents("php://input");
$data = json_decode($raw, true, 512, JSON_THROW_ON_ERROR);
```

Codice completo: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/it/parte-04/cap-17/listing-11.php)


Poi valida:

```php
<?php
$email = $data["email"] ?? "";

if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    http_response_code(422);
    echo json_encode(["error" => "Email non valida"]);
    exit;
}
```

Codice completo: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/it/parte-04/cap-17/listing-12.php)


JSON non rende i dati automaticamente sicuri. È solo il contenitore.

## In sintesi

JSON è il ponte naturale tra PHP e JavaScript. Usa `json_decode()` per leggere, `json_encode()` per scrivere, imposta sempre `Content-Type: application/json` nelle risposte e gestisci gli errori di parsing. Nei progetti più avanti lo useremo per login via AJAX, form dinamici e API.
