# 17. JSON

JSON es uno de los formatos más utilizados para intercambiar datos entre servidores, navegadores y API. Es legible, compacto y se asigna bien a arrays y objetos. En PHP lo usarás para respuestas AJAX, configuraciones, integraciones con servicios externos y API REST.

## ¿Qué es JSON?

JSON representa datos con objetos, arrays, cadenas, números, valores booleanos y `null`:

```json
{
  "name": "Juan",
  "email": "juan@example.com",
  "roles": ["admin", "editor"],
  "active": true
}
```

Código completo: [listing-01.json](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/es/parte-04/cap-17/listing-01.json)


Se parece a JavaScript, pero es un formato de datos, no código. Las claves de objeto deben estar entre comillas dobles y no se pueden insertar comentarios.

## Decodificar JSON a PHP

Para transformar JSON en una estructura PHP use `json_decode()`:

```php
<?php
$json = '{"name":"Juan","active":true}';

$data = json_decode($json, true);

echo $data["name"];
```

Código completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/es/parte-04/cap-17/listing-02.php)


El segundo argumento `true` le dice a PHP que devuelva arrays asociativas. Sin `true`, PHP devuelve objetos `stdClass`:

```php
<?php
$data = json_decode($json);

echo $data->name;
```

Código completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/es/parte-04/cap-17/listing-03.php)


Elija una forma y manténgala consistente en todo su diseño. En los primeros ejemplos usaremos a menudo arrays asociativas porque se conectan bien con lo que ya hemos estudiado.

## Manejar errores de análisis

No se debe ignorar el JSON no válido:

```php
<?php
$data = json_decode($json, true);

if (json_last_error() !== JSON_ERROR_NONE) {
    echo json_last_error_msg();
}
```

Código completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/es/parte-04/cap-17/listing-04.php)


Desde PHP 7.3 puedes solicitar excepciones:

```php
<?php
$data = json_decode($json, true, 512, JSON_THROW_ON_ERROR);
```

Código completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/es/parte-04/cap-17/listing-05.php)


Esta forma es preferible en el código moderno porque los errores ingresan al flujo normal `try/catch`.

## Codificar datos PHP en JSON

Para generar JSON:

```php
<?php
$user = [
    "name" => "Juan",
    "email" => "juan@example.com",
];

echo json_encode($user);
```

Código completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/es/parte-04/cap-17/listing-06.php)


Al responder desde el servidor, configure el tipo de contenido:

```php
<?php
header("Content-Type: application/json");

echo json_encode([
    "success" => true,
    "message" => "Usuario guardado",
]);
```

Código completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/es/parte-04/cap-17/listing-07.php)


Para evitar problemas con caracteres acentuados puedes utilizar:

```php
<?php
echo json_encode($user, JSON_UNESCAPED_UNICODE);
```

Código completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/es/parte-04/cap-17/listing-08.php)


## JSON en el navegador

Del lado del cliente, JavaScript usa `JSON.parse()` y `JSON.stringify()`:

```javascript
const user = JSON.parse('{"name":"Juan"}');
console.log(user.name);

const payload = JSON.stringify({ name: "Juan" });
```

Código completo: [listing-09.js](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/es/parte-04/cap-17/listing-09.js)


Cuando utilizamos AJAX, el navegador enviará datos al servidor o recibirá respuestas en este formato. El servidor PHP no tiene que imprimir HTML si el cliente espera JSON; solo necesita devolver datos.

## Un punto final PHP simple

Ejemplo de respuesta JSON:

```php
<?php
header("Content-Type: application/json");

$users = [
    ["id" => 1, "name" => "Juan"],
    ["id" => 2, "name" => "Lucía"],
];

echo json_encode([
    "data" => $users,
    "count" => count($users),
], JSON_UNESCAPED_UNICODE);
```

Código completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/es/parte-04/cap-17/listing-10.php)


El navegador recibe un objeto con dos propiedades: `data` y `count`. Esta estructura es más extensible que una array simple, porque puede agregar metadatos, paginación o mensajes sin cambiar completamente el contrato.

## Validación de datos de entrada

Si recibe JSON:

```php
<?php
$raw = file_get_contents("php://input");
$data = json_decode($raw, true, 512, JSON_THROW_ON_ERROR);
```

Código completo: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/es/parte-04/cap-17/listing-11.php)


Entonces válido:

```php
<?php
$email = $data["email"] ?? "";

if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    http_response_code(422);
    echo json_encode(["error" => "Email no válida"]);
    exit;
}
```

Código completo: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-17/es/parte-04/cap-17/listing-12.php)


JSON no protege automáticamente los datos. Es solo el contenedor.

## En resumen

JSON es el puente natural entre PHP y JavaScript. Utilice `json_decode()` para leer, `json_encode()` para escribir, establezca siempre `Content-Type: application/json` en las respuestas y controle los errores de análisis. En proyectos posteriores lo usaremos para iniciar sesión a través de AJAX, formularios dinámicos y API.
