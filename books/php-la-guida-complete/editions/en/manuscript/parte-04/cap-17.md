# 17. JSON

JSON is one of the most used formats for exchanging data between servers, browsers and APIs. It is readable, compact, and maps well to arrays and objects. In PHP you will use it for AJAX responses, configurations, integrations with external services and REST APIs.

## What is JSON

JSON represents data with objects, arrays, strings, numbers, booleans, and `null`:

```json
{
  "name": "John",
  "email": "john@example.com",
  "roles": ["admin", "editor"],
  "active": true
}
```

Full source: [listing-01.json](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/en/parte-04/cap-17/listing-01.json)


It resembles JavaScript, but it is a data format, not code. Object keys must be in double quotes, and you cannot insert comments.

## Decode JSON to PHP

To transform JSON into a PHP structure use `json_decode()`:

```php
<?php
$json = '{"name":"John","active":true}';

$data = json_decode($json, true);

echo $data["name"];
```

Full source: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/en/parte-04/cap-17/listing-02.php)


The second argument `true` tells PHP to return associative arrays. Without `true`, PHP returns `stdClass` objects:

```php
<?php
$data = json_decode($json);

echo $data->name;
```

Full source: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/en/parte-04/cap-17/listing-03.php)


Choose a shape and keep it consistent throughout your design. In the first examples we will often use associative arrays because they connect well to what we have already studied.

## Handle parsing errors

Invalid JSON should not be ignored:

```php
<?php
$data = json_decode($json, true);

if (json_last_error() !== JSON_ERROR_NONE) {
    echo json_last_error_msg();
}
```

Full source: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/en/parte-04/cap-17/listing-04.php)


From PHP 7.3 you can ask for exceptions:

```php
<?php
$data = json_decode($json, true, 512, JSON_THROW_ON_ERROR);
```

Full source: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/en/parte-04/cap-17/listing-05.php)


This form is preferable in modern code because errors enter the normal flow `try/catch`.

## Encode PHP data into JSON

To generate JSON:

```php
<?php
$user = [
    "name" => "John",
    "email" => "john@example.com",
];

echo json_encode($user);
```

Full source: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/en/parte-04/cap-17/listing-06.php)


When replying from the server, set the content type:

```php
<?php
header("Content-Type: application/json");

echo json_encode([
    "success" => true,
    "message" => "User saved",
]);
```

Full source: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/en/parte-04/cap-17/listing-07.php)


To avoid problems with accented characters you can use:

```php
<?php
echo json_encode($user, JSON_UNESCAPED_UNICODE);
```

Full source: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/en/parte-04/cap-17/listing-08.php)


## JSON in the browser

Client side, JavaScript uses `JSON.parse()` and `JSON.stringify()`:

```javascript
const user = JSON.parse('{"name":"John"}');
console.log(user.name);

const payload = JSON.stringify({ name: "John" });
```

Full source: [listing-09.js](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/en/parte-04/cap-17/listing-09.js)


When we use AJAX, the browser will send data to the server or receive responses in this format. The PHP server doesn't have to print HTML if the client expects JSON - it just needs to return data.

## A simple PHP endpoint

JSON response example:

```php
<?php
header("Content-Type: application/json");

$users = [
    ["id" => 1, "name" => "John"],
    ["id" => 2, "name" => "Lucy"],
];

echo json_encode([
    "data" => $users,
    "count" => count($users),
], JSON_UNESCAPED_UNICODE);
```

Full source: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/en/parte-04/cap-17/listing-10.php)


The browser receives an object with two properties: `data` and `count`. This structure is more extensible than a bare array, because you can add metadata, pagination, or messages without completely changing the contract.

## Validation of input data

If you receive JSON:

```php
<?php
$raw = file_get_contents("php://input");
$data = json_decode($raw, true, 512, JSON_THROW_ON_ERROR);
```

Full source: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/en/parte-04/cap-17/listing-11.php)


Then valid:

```php
<?php
$email = $data["email"] ?? "";

if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    http_response_code(422);
    echo json_encode(["error" => "Invalid email"]);
    exit;
}
```

Full source: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/en/parte-04/cap-17/listing-12.php)


JSON does not automatically make data secure. It's just the container.

## In summary

JSON is the natural bridge between PHP and JavaScript. Use `json_decode()` to read, `json_encode()` to write, always set `Content-Type: application/json` in replies, and handle parsing errors. In later projects we will use it for login via AJAX, dynamic forms and APIs.
