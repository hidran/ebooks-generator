# 12. Funciones de array

Los arrays son una de las estructuras más utilizadas en PHP. Los usará para listas, configuraciones, resultados de bases de datos, datos de formularios, mensajes de error y colecciones de objetos. Conocer las funciones principales le permite escribir código más corto y claro.

## Agregar y eliminar elementos

Para agregar a la cola:

```php
<?php
$names = ["Juan", "Lucía"];

array_push($names, "Julia");
```

Código completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/es/parte-03/cap-12/listing-01.php)


En PHP es muy común utilizar la sintaxis corta:

```php
<?php
$names[] = "Julia";
```

Código completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/es/parte-03/cap-12/listing-02.php)


Para eliminar el último elemento:

```php
<?php
$last = array_pop($names);
```

Código completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/es/parte-03/cap-12/listing-03.php)


Para trabajar al principio de la array:

```php
<?php
array_unshift($names, "Ana");
$first = array_shift($names);
```

Código completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/es/parte-03/cap-12/listing-04.php)


Estas funciones modifican la array original.

## Ordenar array

`sort()` ordena los valores y vuelve a indexar la array:

```php
<?php
$numbers = [3, 1, 2];
sort($numbers);
```

Código completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/es/parte-03/cap-12/listing-05.php)


Cuando tienes claves asociativas y quieres conservarlas:

```php
<?php
$scores = [
    "juan" => 12,
    "lucia_lopez" => 18,
    "ana" => 15,
];

asort($scores);
```

Código completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/es/parte-03/cap-12/listing-06.php)


`asort()` ordena por valor manteniendo la asociación con la clave. Para ordenar de forma natural, lo cual es útil con cadenas que contienen números, use `natsort()`:

```php
<?php
$files = ["file10.txt", "file2.txt", "file1.txt"];
natsort($files);
```

Código completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/es/parte-03/cap-12/listing-07.php)


## Transformar con `array_map()`

`array_map()` aplica una función a cada elemento y devuelve una nueva array:

```php
<?php
$prices = [10, 20, 30];

$withVat = array_map(function (int $price): float {
    return $price * 1.22;
}, $prices);
```

Código completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/es/parte-03/cap-12/listing-08.php)


Con las funciones de flecha:

```php
<?php
$withVat = array_map(fn (int $price): float => $price * 1.22, $prices);
```

Código completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/es/parte-03/cap-12/listing-09.php)


Es una buena opción cuando desea transformar datos sin cambiar la array original.

## Visita con `array_walk()`

`array_walk()` ejecuta una función en cada elemento. También puedes recibir la clave:

```php
<?php
$user = [
    "name" => "Juan",
    "email" => "juan@example.com",
];

array_walk($user, function ($value, $key) {
    echo "$key: $value" . PHP_EOL;
});
```

Código completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/es/parte-03/cap-12/listing-10.php)


Utilice `array_walk()` cuando desee recorrer una array para producir un efecto, no cuando desee crear una nueva colección. Para transformar, `array_map()` es más claro.

## Filtro

`array_filter()` retiene sólo los elementos que satisfacen una condición:

```php
<?php
$numbers = [1, 2, 3, 4, 5, 6];

$even = array_filter($numbers, fn (int $n): bool => $n % 2 === 0);
```

Código completo: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/es/parte-03/cap-12/listing-11.php)


Atención: `array_filter()` conserva las llaves originales. Si desea volver a indexar:

```php
<?php
$even = array_values($even);
```

Código completo: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/es/parte-03/cap-12/listing-12.php)


## Deconstrucción

La desestructuración le permite asignar elementos de una array a múltiples variables:

```php
<?php
$point = [10, 20];

[$x, $y] = $point;
```

Código completo: [listing-13.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/es/parte-03/cap-12/listing-13.php)


También funciona con claves asociativas:

```php
<?php
$user = [
    "name" => "Juan",
    "email" => "juan@example.com",
];

["name" => $name, "email" => $email] = $user;
```

Código completo: [listing-14.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/es/parte-03/cap-12/listing-14.php)


Es muy legible cuando una función devuelve múltiples valores:

```php
<?php
function split_name(string $fullName): array
{
    return explode(" ", $fullName, 2);
}

[$firstName, $lastName] = split_name("Juan García");
```

Código completo: [listing-15.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/es/parte-03/cap-12/listing-15.php)


## Deconstrucción asimétrica

No siempre necesitas todos los elementos:

```php
<?php
$row = [10, "Juan", "García", "juan@example.com"];

[$id, $name,, $email] = $row;
```

Código completo: [listing-16.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/es/parte-03/cap-12/listing-16.php)


La coma en blanco omite un valor. No abuses: si los elementos se vuelven muchos, es más claro una array asociativa o un objeto.

## En resumen

Las funciones de array le permiten pensar en términos de operaciones: agregar, eliminar, ordenar, transformar, filtrar, desestructurar. En los proyectos de este libro, utilizaremos estas técnicas para manejar resultados de SQL, errores de validación, configuraciones y datos de sesión. La regla general es simple: elija la función que mejor exprese la intención del código.
