# 11. Funciones de cadena

Las cadenas están en todas partes: nombres, correos electrónicos, URL, mensajes, plantillas, cadenas de consulta, contenidos leídos de archivos y datos recibidos de formularios. PHP ofrece muchas funciones dedicadas y en este capítulo vemos las que utilizará con más frecuencia.

## Borrar una cadena

Cuando recibe texto desde el exterior, debe esperar espacios, mayúsculas inconsistentes y caracteres inesperados. Las primeras funciones que debemos conocer son `trim()`, `strtolower()` y `strtoupper()`.

```php
<?php
$email = "  JUAN@Example.COM  ";

$email = trim($email);
$email = strtolower($email);

echo $email; // juan@example.com
```

Código completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/es/parte-03/cap-11/listing-01.php)


`trim()` elimina los espacios al principio y al final. No cambia los espacios internos, por lo que `"Juan García"` permanece `"Juan García"`.

## Buscar dentro de una cadena

Durante años, la función más común para buscar una subcadena era `strpos()`:

```php
<?php
$url = "https://example.com/guia/php";

if (strpos($url, "php") !== false) {
    echo "El string contiene php";
}
```

Código completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/es/parte-03/cap-11/listing-02.php)


La comparación debe ser `!== false`, no `!= false`, porque `strpos()` puede devolver `0` cuando el texto buscado está al principio de la cadena. `0` es un valor válido, pero en una comparación débil se interpretaría como `false`.

Desde PHP 8 hay funciones más legibles:

```php
<?php
$name = "index.php";

var_dump(str_contains($name, ".php"));
var_dump(str_starts_with($name, "index"));
var_dump(str_ends_with($name, ".php"));
```

Código completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/es/parte-03/cap-11/listing-03.php)


Cuando pueda usar PHP 8, prefiera estas funciones: comunican la intención del código sin tener que recordar el comportamiento particular de `strpos()`.

## Reemplazar texto

`str_replace()` reemplaza todas las apariciones:

```php
<?php
$title = "Guía básica de PHP";

echo str_replace("básica", "completa", $title);
```

Código completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/es/parte-03/cap-11/listing-04.php)


También puedes pasar array:

```php
<?php
$text = "Hola {name}, bienvenido a {tema}.";

echo str_replace(
    ["{name}", "{tema}"],
    ["Juan", "PHP"],
    $text
);
```

Código completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/es/parte-03/cap-11/listing-05.php)


Esta técnica es útil para plantillas pequeñas, pero no reemplaza un motor de plantillas real a medida que la interfaz crece.

## Dividir y unir

`explode()` divide una cadena en una array:

```php
<?php
$csv = "juan,garcia,juan@example.com";

$parts = explode(",", $csv);
print_r($parts);
```

Código completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/es/parte-03/cap-11/listing-06.php)


`implode()` realiza la operación inversa:

```php
<?php
$tags = ["php", "mysql", "web"];

echo implode(", ", $tags);
```

Código completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/es/parte-03/cap-11/listing-07.php)


`join()` es un alias de `implode()`. En código moderno es mejor usar `implode()` porque es más reconocible.

## Escapar y cortar

`stripslashes()` elimina las barras invertidas agregadas antes de caracteres como comillas simples y comillas:

```php
<?php
$value = "Rock \\'n\\' Roll";
echo stripslashes($value);
```

Código completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/es/parte-03/cap-11/listing-08.php)


Hoy en día no deberías crear consultas SQL agregando barras diagonales manualmente. Para la base de datos usaremos una declaración preparada. Las funciones de cadena sirven para transformar texto, no para inventar protecciones de seguridad endebles.

## Longitud y porciones

Para saber la longitud:

```php
<?php
echo strlen("PHP");
```

Código completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/es/parte-03/cap-11/listing-09.php)


Para extraer una parte:

```php
<?php
$code = "IT-2026-001";

echo substr($code, 0, 2);  // IT
echo substr($code, -3);    // 001
```

Código completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/es/parte-03/cap-11/listing-10.php)


Con texto Unicode, acentuado o multibyte, evalúe las funciones `mb_*`, como `mb_strlen()` y `mb_substr()`. `strlen("è")` no cuenta "caracteres visibles", cuenta bytes.

## Normalizar la entrada del usuario

Un ejemplo completo:

```php
<?php
function normalize_email(string $email): string
{
    return strtolower(trim($email));
}

$email = normalize_email($_POST["email"] ?? "");
```

Código completo: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/es/parte-03/cap-11/listing-11.php)


Normalizar no significa validar. Después de la normalización puedes comprobar:

```php
<?php
if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    echo "Email no válida";
}
```

Código completo: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/es/parte-03/cap-11/listing-12.php)


## En resumen

Las funciones de cadena son pequeñas, pero deciden la calidad de una gran cantidad de código. Utilice `trim()` y `strtolower()` para normalizar, `str_contains()` y funciones similares para leer mejor las condiciones, `str_replace()` para sustituciones simples, `explode()` y `implode()` para cambiar entre cadenas y arrays. Cuando trabaje con datos externos, separe siempre la transformación, la validación y la seguridad.
