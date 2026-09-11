# 28. Namespaces y autoload

Mientras un proyecto tiene diez clases, tenerlas todas en una carpeta e incluirlas a mano con `require` funciona. Pero en cuanto crece — decenas de clases, varias librerías de terceros — ese modelo se desmorona, y por dos motivos distintos. El primero es de **nombres**: dos clases distintas no pueden llamarse ambas `User`, y sin embargo ocurre a cada paso. El segundo es de **carga**: enumerar a mano un `require` por cada clase se vuelve inmanejable. Los namespaces resuelven el primer problema, el autoload el segundo. Son dos herramientas independientes que en el código moderno siempre trabajan juntas, y conviene verlas primero por separado y luego entender cómo encajan.

## El problema de los nombres

Imagina usar dos librerías, y que cada una defina una clase `User`. Sin namespaces viven en el mismo "espacio global" de nombres, y la segunda en cargarse provoca un error: el nombre ya está ocupado. Los namespaces dan a cada clase un **nombre completo** que evita la colisión, como una carpeta lógica:

```php
<?php
namespace App\Models;

class User
{
}
```

Código completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-28/es/parte-08/cap-28/listing-01.php)


La línea `namespace App\Models` declara que todo lo que sigue vive en ese espacio: la clase ya no se llama solo `User`, sino por completo `App\Models\User`. Otra librería podrá tener su `Vendor\Auth\User`, y las dos nunca se confundirán, porque el nombre completo es distinto. Es el mismo principio que las rutas en un sistema de archivos: dos ficheros `index.php` conviven sin problemas mientras estén en carpetas distintas.

## Usar una clase con namespace

Escribir cada vez el nombre completo sería incómodo. La palabra clave `use` **importa** un nombre en el fichero actual, de modo que luego puedes usar la forma corta:

```php
<?php
use App\Models\User;

$user = new User();
```

Código completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-28/es/parte-08/cap-28/listing-02.php)


El `use` al principio del fichero dice "cuando escribo `User`, me refiero a `App\Models\User`". Es la forma que verás más a menudo: los imports reunidos al inicio del fichero declaran de entrada de dónde viene cada clase. Como alternativa, sin `use`, puedes escribir el nombre completo directamente:

```php
<?php
$user = new \App\Models\User();
```

Código completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-28/es/parte-08/cap-28/listing-03.php)


Fíjate en la barra invertida inicial: indica el **namespace global**, la raíz. Es el equivalente de una ruta absoluta que arranca desde `/`: le dice a PHP que busque el nombre partiendo de arriba, sin tener en cuenta el namespace en el que te encuentres en ese momento.

## Múltiples namespaces en el mismo fichero

PHP permite técnicamente declarar varios namespaces en un único fichero, pero en código real es mejor evitarlo. La convención universal es **una clase por fichero**, con el namespace al principio:

```php
<?php
namespace App\Models;

class User
{
}
```

Código completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-28/es/parte-08/cap-28/listing-04.php)


Y el fichero debe guardarse en una ruta que **refleje** el namespace:

```text
src/Models/User.php
```

Código completo: [listing-05.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-28/es/parte-08/cap-28/listing-05.txt)


Esta correspondencia entre nombre y ruta no es puntillosidad: es la clave que hace posible el autoload. Si `App\Models\User` está siempre en `src/Models/User.php`, una máquina puede calcular la ruta a partir del nombre, sin que tú tengas que decírselo. Por eso "una clase por fichero" y "la ruta refleja el namespace" son las dos reglas de oro de aquí en adelante.

## `require` manual

Antes de llegar al autoload, veamos el método directo, el que quieres superar:

```php
<?php
require __DIR__ . "/src/Models/User.php";
require __DIR__ . "/src/Controllers/UserController.php";
```

Código completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-28/es/parte-08/cap-28/listing-06.php)


Funciona, pero no escala: cada nueva clase requiere una nueva línea de `require`, y en un proyecto serio son cientos. Peor aún es el **orden**: si `UserController` usa `User` pero su `require` va primero, la aplicación falla porque la dependencia todavía no está cargada. Acabas gestionando a mano un grafo de dependencias que crece con cada clase — exactamente el tipo de trabajo tedioso y frágil que una máquina debería hacer por ti.

## `spl_autoload_register()`

La idea del autoload es darle la vuelta a la lógica: en lugar de cargar todo por adelantado, registras una función que PHP llama **solo cuando hace falta**, en el momento exacto en que encuentra una clase aún no cargada.

```php
<?php
spl_autoload_register(function (string $class): void {
    $prefix = "App\\";
    $baseDir = __DIR__ . "/src/";

    if (!str_starts_with($class, $prefix)) {
        return;
    }

    $relativeClass = substr($class, strlen($prefix));
    $file = $baseDir . str_replace("\\", "/", $relativeClass) . ".php";

    if (is_file($file)) {
        require $file;
    }
});
```

Código completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-28/es/parte-08/cap-28/listing-07.php)


Sigue la lógica de la función, porque es toda la historia del autoload en unas pocas líneas. Cuando escribes `new App\Models\User()` y esa clase no está cargada, PHP le pasa la cadena `"App\Models\User"` a esta función. Ella comprueba que el nombre empiece por el prefijo `App\` (de lo contrario no es asunto suyo y regresa), quita el prefijo, sustituye las barras invertidas por barras normales — convirtiendo el namespace en una ruta — y añade `.php`. El resultado: `App\Models\User` se convierte en `src/Models/User.php`, que se incluye. Las clases se cargan así **bajo demanda**, una a una, solo las que de verdad se usan. Y el problema del orden desaparece: ya no hay un orden que respetar, cada clase llega en el momento en que la nombras. Esta convención nombre-ruta es exactamente la base del estándar **PSR-4** que Composer implementa (Capítulo 29).

## Autoload y rutas

Un error frecuentísimo en los autoloaders escritos a mano es construir las rutas relativas a la carpeta desde la que se lanza el script, en lugar de relativas al fichero del autoloader. La solución es `__DIR__`:

```php
<?php
$baseDir = __DIR__ . "/src/";
```

Código completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-28/es/parte-08/cap-28/listing-08.php)


`__DIR__` es la constante mágica que contiene la carpeta del fichero **en el que está escrita**, no la carpeta actual de ejecución. Anclando las rutas a `__DIR__`, el autoloader funciona igual tanto si lanzas el script desde la raíz del proyecto, desde una subcarpeta o desde un cron: ya no depende de *dónde* se ejecuta. Es una pequeña disciplina que evita una de las causas más comunes y frustrantes de "fichero no encontrado".

## Namespaces y funciones

Una última trampa tiene que ver con la resolución de nombres. Cuando estás dentro de un namespace, un nombre sin barra invertida se busca **primero** en el namespace actual. Va muy bien para tus propias clases, pero las clases nativas de PHP (`DateTimeImmutable`, `InvalidArgumentException`) viven en el espacio global: dentro de `App\Models`, escribir `new DateTimeImmutable()` hace que PHP busque un inexistente `App\Models\DateTimeImmutable`. Hay dos soluciones. La primera es importarlas al principio del fichero:

```php
<?php
use DateTimeImmutable;
use InvalidArgumentException;
```

Código completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-28/es/parte-08/cap-28/listing-09.php)


La segunda es prefijarlas con la barra invertida que las ancla a la raíz global:

```php
<?php
$date = new \DateTimeImmutable();
```

Código completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-28/es/parte-08/cap-28/listing-10.php)


Ambas funcionan; la primera es más legible porque reúne todas las dependencias, incluidas las del sistema, al principio del fichero. El mensaje de fondo es que, dentro de un namespace, los nombres globales hay que hacerlos explícitos — un detalle que explica bastantes errores "clase no encontrada" aparentemente misteriosos.

## En resumen

Los namespaces dan a las clases **nombres completos y ordenados**, eliminando las colisiones entre librerías distintas; el autoload elimina los `require` manuales enlazando automáticamente el nombre de la clase con la ruta de su fichero, siempre que respetes las dos convenciones — una clase por fichero, ruta que refleja el namespace. En los proyectos modernos casi nunca escribirás un autoloader a mano: lo genera Composer, que veremos en el próximo capítulo. Pero haber entendido el mecanismo aquí, en una función de pocas líneas, te pone en condiciones de resolver los errores de "clase no encontrada" en lugar de sufrirlos — porque sabes exactamente a partir de qué nombre PHP calculó qué ruta, y dónde fue a buscar.
