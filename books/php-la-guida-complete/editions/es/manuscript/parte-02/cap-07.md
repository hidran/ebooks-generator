# 7. Variables, tipos y constantes.

En el capítulo anterior vimos cómo PHP ejecuta código y cómo lo mezcla con HTML. En este capítulo ingresamos al corazón del lenguaje: las **variables**, es decir, los contenedores con los que almacenamos y reutilizamos datos, y los **tipos** fundamentales que estos datos pueden tener: números, booleanos, cadenas y arrays. Cerraremos con **constantes**, los valores que no deben cambiar durante la ejecución, y con tres funciones nativas: `isset()`, `empty()` y `is_null()`, que usaremos continuamente para verificar el estado de una variable.

Son la base de todo lo que construiremos en el resto del libro: los formularios, las consultas a la base de datos, los proyectos de las partes finales manipulan continuamente variables, cadenas y arrays. Vale la pena prestar a este capítulo toda la atención que merece, también porque PHP tiene algunos comportamientos (conversión automática de tipos, cadenas como secuencias de bytes, truncamiento de claves de array) que sorprenden a quienes provienen de otros lenguajes y que son la fuente de errores clásicos.

## ¿Qué es una variable?

### De expresiones a variables

En PHP, como en otros lenguajes, podemos escribir **expresiones literales**. Una expresión es como cuando hacíamos matemáticas: `2 + 2`. Cada declaración debe terminar con un punto y coma, para indicarle a PHP dónde termina:

```php
<?php

2 + 2;
```

Código completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-01.php)


Si ejecutamos este código desde la línea de comando con `php index.php`, no aparece nada, pero ni siquiera un error. PHP evalúa la expresión, obtiene `4` y la descarta porque no le pedimos que la mostrara. Para enviar el resultado a la consola usamos la construcción `echo`, que significa "mostrar esta expresión en la pantalla (o en la consola)":

```php
<?php

echo (2 + 2);   // 4
```

Código completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-02.php)


Los paréntesis aquí sólo sirven para delimitar la expresión, como en matemáticas. Una expresión literal también puede ser una **cadena**, es decir, cualquier conjunto de caracteres (una frase, un nombre) o un número:

```php
<?php

'Hola mundo';   // expresión evaluada, pero sin output
3.1415;          // igual

echo 'Hola mundo';   // Hola mundo
echo 3.1415;          // 3.1415
```

Código completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-03.php)


Además desde la consola, puedes ver el resultado en el navegador: si usas VS Code con la extensión del Servidor PHP que configuramos en el Capítulo 5, simplemente haz clic derecho en el archivo y en "Servidor PHP: Servir proyecto" para abrir la página en el navegador. En este capítulo casi siempre usaremos la consola, reservando el navegador para los casos en que la salida contenga HTML.

Ahora, supongamos que desea utilizar el valor 3,1415 (un pi reducido) para calcular el área de un círculo o el volumen de un cilindro. ¿Cómo lo almacenamos en algún lugar para poder reutilizarlo en diferentes expresiones? Para eso están exactamente las variables.

Una **variable** no es más que una zona de memoria (en la RAM del ordenador, o incluso en el disco, según cómo la gestione el sistema) donde almacenamos datos, con un nombre que actúa como etiqueta de referencia. Los datos pueden ser cualquier cosa: un número, una cadena, un solo carácter, una lista de ciudades, un registro leído de la base de datos, el contenido de un archivo, incluso un recurso como un puntero a un archivo abierto o una conexión a una base de datos. Todo esto lo ponemos en una variable para poder reciclarlo tantas veces como queramos.

### Declaración de una variable y convenciones de nomenclatura

En PHP una variable siempre comienza con el símbolo **dólar** (`$`): es el estándar del lenguaje. Después del dólar, el nombre:

- puede comenzar con una **letra** o con un **guión bajo** (`_`, el guión bajo);
- puede continuar con letras, números y guiones bajos;
- **no puede** comenzar con un número y **no puede** contener espacios.

```php
<?php

$name = 'Juan';      // válido
$_name = 'Juan';     // válido
$name2 = 'Juan';     // válido
// $2name = 'Juan';  // ERROR: no puede empezar con un número
// $last name = '...'; // ERROR: sin espacios
```

Código completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-04.php)


Para asignar un valor usamos el signo **igual** (`=`), al igual que en matemáticas asignamos un valor a *x* o *y*. Las cadenas deben estar entre comillas simples o comillas (veremos la diferencia en breve), los números no deben:

```php
<?php

$lastName = 'Arias';
$name = 'Juan';
$age = 50;
$cities = ['Sevilla', 'Madrid', 'Nápoles'];   // un array: lo estudiaremos dentro de poco
```

Código completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-05.php)


Algunas palabras sobre las convenciones. A la computadora no le importa cómo llames a una variable: podrías llamarla `$a234` y para ella sería simplemente un puntero a un área de memoria. Pero el código lo leen los programadores, y quien lo lee debe entender lo que está haciendo: utilice siempre **nombres parlantes**, que den información. Normalmente uso nombres en inglés y sigo la convención **camelCase**: cuando el nombre se compone de dos palabras, la segunda comienza con mayúscula, como en `$lastName`. Elija una convención y cúmplala durante todo el proyecto.

Una última observación importante: PHP es un lenguaje de **tipificación dinámica**. En una variable que contiene un número podemos asignar fácilmente una cadena después:

```php
<?php

$r = 20;
$r = 'una letra';   // es válido en PHP
```

Código completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-06.php)


En lenguajes como Java o C# esto no es posible: una vez que declaras una variable numérica, no puedes asignarle una cadena. En PHP si. Desde PHP 7 en adelante todavía podemos declarar los tipos de parámetros de función y forzar a PHP a verificarlos; veremos esto en el Capítulo 10 cuando hablemos de funciones.

### Un ejemplo práctico: el área del círculo

Juntemos lo que hemos visto y calculemos el área de un círculo. Necesitamos pi (por ahora en una variable: más adelante en este capítulo descubriremos que es el candidato perfecto para una constante) y el radio:

```php
<?php

$pi = 3.1415;
$r = 20;

$area = $pi * $r * $r;

echo "El área es $area\n";
```

Código completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-07.php)


Para multiplicar, en casi todos los lenguajes de programación se utiliza el **asterisco** (`*`). También existe una función para elevar al cuadrado, pero por ahora multipliquemos el radio por sí mismo. La ventaja es obvia: en lugar de copiar `3.1415` cada vez, usamos `$pi`; e imagina que el rayo proviene de un formulario completado por el usuario: recibimos los datos, los ponemos en `$r` y aplicamos la fórmula.

Observe dos cosas en el `echo` final. Primero: dentro de las **comillas** podemos escribir el nombre de la variable directamente y PHP lo reemplaza con su valor (no con comillas simples; volveremos a ello en el párrafo sobre cadenas). Segundo: `\n` es el carácter de nueva línea, utilizado en casi todos los lenguajes (PHP, Java, C#) para ajustar en la consola.

Sin embargo, si abre el mismo script en su navegador, encontrará que el texto no se ajusta. Al mirar el código fuente de la página (clic derecho → Ver código fuente), la nueva línea está ahí, pero el navegador no la muestra: para HTML, una nueva línea en el código fuente es solo un espacio. Para incluirlo en el navegador necesita una etiqueta HTML, como un párrafo, y ya sabemos por el Capítulo 6 que podemos mezclar HTML y PHP:

```php
<?php

echo '<p>El perímetro es ' . (2 * $pi * $r) . "</p>\n";
```

Código completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-08.php)


Aquí también reutilizamos `$pi` y `$r` por segunda vez, concatenando el resultado a la cadena con el **punto** (`.`), el operador de concatenación sobre el que aprenderemos más en breve. Las variables se pueden reutilizar tantas veces como queramos, y más adelante veremos cómo pasarlas como parámetros a funciones.

## Números: entero y flotante

PHP tiene dos tipos numéricos: **integer** (números enteros) y **float** (números de punto flotante). Crear un número es muy sencillo: simplemente asígnalo a una variable.

```php
<?php

$dec = 255;
var_dump($dec);   // int(255)
```

Código completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-09.php)


Aquí nos encontramos con una función nativa muy valiosa: **`var_dump()`**. Le pasamos una variable entre paréntesis y nos muestra el **tipo** y el **valor**: en este caso `int(255)`. Lo usaremos continuamente para inspeccionar variables.

### Enteros, cadenas numéricas y conversiones automáticas

¿Qué pasa si ponemos el número entre comillas?

```php
<?php

$dec = '255';
var_dump($dec);        // string(3) "255"

var_dump($dec * 4);    // int(1020)
var_dump($dec * 4.4);  // float(1122)
```

Código completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-10.php)


Entre comillas, `255` es una **cadena** de tres bytes. Pero si lo multiplicamos por 4, obtenemos `int(1020)`: PHP convierte automáticamente (la **conversión**) el contenido de la cadena en un número, porque el operador de multiplicación espera números. PHP lee la cadena desde el principio: si comienza con un número (posiblemente precedido por el signo `+` o `-`), continúa hasta que termina el número y convierte esa parte. Con `'255aa' * 4` aún obtendría `1020`, deteniéndose en 5, aunque las versiones recientes de PHP emiten una advertencia cuando la cadena no es un número "bien formado". Lo mismo ocurre si multiplicamos por un flotante como `4.4`: el resultado se convierte en `float`.
Esta flexibilidad es conveniente, pero un consejo de la experiencia: por convención, y para mayor corrección, si sabes a priori que un valor es un número, represéntalo como un número, sin superíndices. Respetamos los tipos incluso si PHP hace la conversión por nosotros. Y recuerda que desde PHP 7 podemos declarar que un parámetro de función debe ser `int`: en ese caso la verificación se vuelve rigurosa.

### Representar números enteros en otras bases.

Los números enteros no sólo se escriben en base diez. PHP también nos permite representarlos en **octal** (base 8), **hexadecimal** (base 16) y **binario** (base 2):

```php
<?php

$oct = 0124;         // octal: prefijo 0
$hex = 0xDE;         // hexadecimal: prefijo 0x
$bin = 0b11111111;   // binario: prefijo 0b

var_dump($oct);   // int(84)
var_dump($hex);   // int(222)
var_dump($bin);   // int(255)
```

Código completo: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-11.php)


Preste atención a los prefijos: un **cero** inicial para octal, **`0x`** para hexadecimal, **`0b`** para binario (el cero, no la letra "o": es un error tipográfico clásico).

¿Cómo se llega a esos valores decimales? Son matemáticas básicas, pero repasémoslas. En base 8 los dígitos van del 0 al 7, y se suman empezando por la derecha, multiplicando cada dígito por la potencia de 8 correspondiente a su posición:

```text
0124 (octal) = 4×8⁰ + 2×8¹ + 1×8² = 4 + 16 + 64 = 84
```

Código completo: [listing-12.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-12.txt)


En base 16 los dígitos van del 0 al 9 y luego continúan con las letras: A es igual a 10, B 11, C 12, D 13, E 14, F 15. El procedimiento es el mismo, con las potencias de 16:

```text
0xDE = 14×16⁰ + 13×16¹ = 14 + 208 = 222
```

Código completo: [listing-13.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-13.txt)


El binario, finalmente, es la base de las computadoras: solo 0 y 1, y hacia la izquierda los pesos se duplican: 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, etc. Ocho dígitos 1 equivalen exactamente a 255.

Lo importante a entender es que la base es solo una **representación**: internamente PHP siempre usa el mismo número, y cuando lo mostramos con `var_dump()` o `echo` lo convierte automáticamente a base diez. También podemos mezclar representaciones en operaciones:

```php
<?php

$result = $dec + $hex;   // 255 + 222
echo $result;            // 477
```

Código completo: [listing-14.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-14.php)


### Flotadores y límites de números enteros

Normalmente usaremos números decimales, positivos o negativos, y números decimales, donde el punto decimal es el **punto**:

```php
<?php

$negative = -255;
$float = 123.45;
var_dump($float);   // float(123.45)
```

Código completo: [listing-15.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-15.php)


Una peculiaridad: cuando usamos **división**, el resultado generalmente es un valor flotante; Sólo si ambos operandos son números enteros y la división es exacta, PHP devuelve un número entero. Por lo demás, se aplican los mismos operadores del álgebra básica, que estudiaremos en detalle en el Capítulo 8.

En cuanto a los límites: el tamaño máximo de un número entero depende de la **plataforma**. En sistemas de 32 bits, el máximo es de unos 2,1 mil millones (2³¹ − 1); en sistemas de 64 bits (ahora el estándar en Linux, macOS y Windows modernos) es dramáticamente más grande. Estamos bien cubiertos para las operaciones matemáticas cotidianas. Los flotantes siguen el estándar **IEEE 754**, con los típicos redondeos de coma flotante: para la gran mayoría de los casos esto está bien, y si necesita cálculos de precisión arbitraria, PHP proporciona bibliotecas matemáticas dedicadas (como BCMath), que están fuera de este libro.

## El tipo booleano

El tipo **booleano** (o booleano) proviene del álgebra booleana: solo puede tomar dos valores, **`true`** (verdadero) y **`false`** (falso). En PHP, estas dos constantes *no distinguen entre mayúsculas y minúsculas* (puedes escribir `true`, `True` o `TRUE`) y su uso típico es en comprobaciones y bucles: "si esta condición es verdadera, haz esto; de lo contrario, haz aquello".

Sin embargo, la forma en que PHP maneja los booleanos es diferente de lenguajes como Java o C#, donde el tipo booleano es rígido y no se puede comparar con otros tipos: en PHP **cualquier valor puede evaluarse como booleano**, mediante conversión automática. Y aquí es donde hay que tener mucho cuidado.

### Valores considerados falsos

En PHP sólo estos valores se consideran falsos (*falso*):

| Valor | Notas |
|---|---|
| `false` | la constante booleana |
| `0` | el número entero cero (también `-0`) |
| `0.0` | el flotador cero (también `-0.0`) |
| `''` | la cadena vacía |
| `'0'` | la cadena que contiene cero: ¡cuidado, confunde a muchos! |
| `[]` | una array vacía |
| `null` | el valor nulo |
| elemento XML vacío | un objeto SimpleXML creado a partir de un elemento vacío (veremos XML en el Capítulo 16) |
**Todo lo demás es cierto**: una cadena que no esté vacía, un número distinto de cero, una array con al menos un elemento. Le recomiendo que conserve esta tabla como referencia; también puede pegarla en un comentario en su código. Por cierto: para comentarios de varias líneas utilice `/*` para abrir y `*/` para cerrar; todo lo que hay en el medio es ignorado por el intérprete, que ni siquiera lo analiza.

### Booleano en la práctica: expresiones y reparto

Declarar una variable booleana es sencillo. Usémoslo inmediatamente en una condición: estudiaremos la construcción `if`/`else` en profundidad en el Capítulo 9, pero el significado es intuitivo: *si* la condición entre paréntesis es verdadera, ejecute el primer bloque entre llaves, *de lo contrario* (de lo contrario) el segundo:

```php
<?php

$verify = false;

if ($verify == true) {
    echo 'La verificación es verdadera';
} else {
    echo 'La verificación es falsa';
}
// Salida: La verificación es falsa

var_dump($verify);   // bool(false)
```

Código completo: [listing-16.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-16.php)


La comparación también se puede acortar: `if ($verify)` significa "si `$verify` es verdadero". Y un booleano no nace sólo de las constantes `true` y `false`: cualquier **expresión que devuelva verdadero o falso** se puede asignar a una variable:

```php
<?php

$verify = 4 > 5;    // ¿4 es mayor que 5? No
var_dump($verify);  // bool(false)

$verify = 4 == 5;   // ¿4 es igual a 5? No
var_dump($verify);  // bool(false)
```

Código completo: [listing-17.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-17.php)


En el Capítulo 8 veremos la diferencia entre comparación con dos signos iguales (`==`) y con tres (`===`): la segunda espera que los valores sean iguales *y del mismo tipo*.

Ahora la parte interesante. Asignemos a `$verify` una cadena:

```php
<?php

$verify = 'Hola mundo';
var_dump($verify);   // string(10) "Hola mundo"

if ($verify) {
    echo 'La verificación es verdadera';   // se ejecuta!
}
```

Código completo: [listing-18.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-18.php)


`$verify` es una cadena, pero la condición se cumple: una cadena no vacía, convertida a booleana, es `true`. PHP realiza la conversión automáticamente, pero también podemos hacerlo explícitamente, poniendo el tipo entre paréntesis delante del valor (se llama **cast**) como se hace en Java y otros lenguajes:

```php
<?php

var_dump((bool) 'Hola mundo');   // bool(true)
var_dump((bool) '');              // bool(false)
var_dump((bool) '0');             // bool(false) — la cadena "0"!
```

Código completo: [listing-19.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-19.php)


### Tenga cuidado con las cadenas "verdaderas" y "falsas"

Hay un problema práctico que encontrará al trabajar con formularios en la Parte IV. Si enviamos las palabras `true` o `false` desde el navegador a PHP, en el lado del servidor llegan como **cadenas**, y una cadena no vacía siempre es verdadera:

```php
<?php

$verify = 'false';   // cadena de 5 caracteres, NO el booleano false
var_dump($verify);   // string(5) "false"

if ($verify) {
    echo 'Entra en la rama true!';   // sí: una cadena no vacía es true
}
```

Código completo: [listing-20.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-20.php)


Lo mismo ocurre con una casilla de verificación, que a su vez envía valores como `on`/`off`: llegan como cadenas, y `'off'` también sería cierto. Por esta razón, el estándar, en el lado del cliente, es enviar **`0` y `1`**: la cadena `'0'` es falsa y `'1'` es verdadera, por lo que estamos seguros de obtener el booleano que esperamos. En otros idiomas, este pequeño juego no funciona: allí necesitas los valores literales `true` y `false` o una conversión explícita. En PHP, conociendo la tabla de valores falsos, funciona muy bien.

## Introducción a las cadenas

Una **cadena** en PHP es una secuencia de caracteres, donde cada carácter está representado por un **byte**: por lo tanto, son posibles 256 valores diferentes para cada byte. Este detalle, que parece académico, en realidad es muy importante: internamente PHP almacena *secuencias de bytes*, sin saber nada de codificación. Depende de nosotros (y de las funciones y bibliotecas que utilizamos) interpretar correctamente esos bytes, tanto cuando llegan de una fuente externa como cuando los alimentamos a PHP. Inmediatamente veremos las consecuencias prácticas.

### Comillas simples y comillas

Hay dos formas básicas de delimitar una cadena: **comillas simples** (`'...'`) y **comillas**, o comillas dobles (`"..."`). La diferencia es fundamental:

- con **comillas simples**, PHP toma la cadena tal como está: no se interpretan variables;
- con **comillas**, PHP **analiza** la cadena buscando las variables que contiene (todo lo que comienza con `$`, o entre llaves, como veremos) y las reemplaza con su valor: esto se llama **interpolación**.

```php
<?php

$name = 'Juan';
$address = 'Calle Mayor';

$lastName = "$name Arias";
echo $lastName;          // Juan Arias

echo 'Nombre: $name';      // Nombre: $name  (sin parsing!)
echo "Nombre: $name";      // Nombre: Juan
```

Código completo: [listing-21.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-21.php)


En la primera tarea, dentro de las comillas PHP encuentra `$name`, lo interpreta y produce `Juan Arias`. Tenga en cuenta el espacio después de la variable: también sirve para dejar claro dónde termina el nombre de la variable. Sin embargo, entre comillas simples, la cadena `'$address'` permanece literalmente `$address`, incluido el dólar.
Cuando no hay nada que interpolar, PHP con comillas simples evita por completo el paso de análisis: antes también era medible en velocidad, hoy la diferencia es insignificante. Sin embargo, por convención, uso **comillas simples siempre que no hay variables en la cadena**, y comillas sólo cuando se necesita interpolación: inmediatamente deja claro, al leer el código, qué cadenas son "dinámicas". Te lo sugiero como un hábito.

### Caracteres de escape

Dentro de las comillas PHP también interpreta los **caracteres especiales** (o secuencias de escape), que comienzan con la barra invertida: los más utilizados son `\n` (nueva línea*), `\t` (tab) y `\f` (salto de línea). Son los mismos que Java, C y JavaScript. Sin embargo, entre comillas simples no se interpretan.

```php
<?php

$name = 'Juan';
$lastName = 'Arias';
$address = 'Calle Mayor';

echo "$name $lastName\n$address";
```

Código completo: [listing-22.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-22.php)


En la consola la dirección se ajusta. En el navegador, como ya hemos visto, no: la nueva línea está presente en el código fuente de la página, pero no se representa. Aquí, una función PHP nativa, **`nl2br()`** (*nueva línea para romper*), que transforma cada `\n` en una etiqueta HTML `<br>`, resulta útil:

```php
<?php

echo nl2br("$name $lastName\n$address");
// Fuente generada: Juan Arias<br />
// Calle Mayor
```

Código completo: [listing-23.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-23.php)


Al recargar la página, el texto también se ajusta en el navegador: mirando la fuente con el navegador (por ejemplo en Chrome) verás que la nueva línea ha ido acompañada de un `<br />`.

## Acceder y editar una cadena

Al ser una secuencia de caracteres, una cadena en PHP se comporta como una **array de caracteres**: podemos acceder a cada carácter con corchetes y un índice que comienza desde **cero**.

```php
<?php

$name = 'Juan';
echo $name[0];   // H
echo $name[4];   // a
```

Código completo: [listing-24.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-24.php)


También podemos *modificar* un carácter asignando un nuevo valor a esa posición. Supongamos que escribí mi nombre sin acento y quiero reemplazar el último `a` con un `à`:

```php
<?php

$name = 'Juan';
$name[4] = 'à';
echo $name;   // Hidr�  ← carácter corrupto!
```

Código completo: [listing-25.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-25.php)


El resultado es un carácter extraño. ¿Por qué? Volvamos a lo que dije al principio: para PHP una cadena es una **secuencia de bytes**. En codificación UTF-8 el `à` acentuado ocupa **dos bytes**, pero al asignarlo a la posición 4 estamos reemplazando **solo un byte**. Luego, PHP toma solo el primer byte del carácter acentuado y el resultado es una secuencia no válida. Comprobémoslo:

```php
<?php

$accented = 'à';
var_dump($accented);   // string(2) "à"  ← dos bytes!
```

Código completo: [listing-26.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-26.php)


El mismo fenómeno ocurre con las funciones de cadena nativas. **`strlen()`** devuelve la longitud de una cadena, pero en *bytes*, no en caracteres:

```php
<?php

echo strlen('à');      // 2
echo mb_strlen('à');   // 1
```

Código completo: [listing-27.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-27.php)


**`mb_strlen()`** en su lugar responde correctamente: un carácter. Las funciones con el prefijo **`mb_`** pertenecen a la biblioteca **mbstring** (*cadena multibyte*), agregada a PHP para resolver este problema: PHP no tiene soporte nativo para UTF-8, y sus funciones nativas no saben si esos bytes representan un carácter UTF-8, Latin-1 o algo más; para ellos, son solo bytes. La regla general: cuando trabaja con texto que puede contener acentos o caracteres que no son ASCII y necesita longitudes, subcadenas y similares, use funciones `mb_*`; por lo general, simplemente agregue el prefijo `mb_` al nombre de la función nativa correspondiente.

Te digo esto porque es uno de los trucos de PHP en el que todo el mundo cae al principio: saber cómo funcionan realmente las cadenas te ahorra horas de depuración. En el Capítulo 11 profundizaremos en las funciones de manipulación de cadenas.

Una última nota histórica: en el código antiguo también encontrarás acceso a caracteres con llaves (`$name{4}`). Esta sintaxis quedó obsoleta en PHP 7.4 y **eliminada en PHP 8**: utilice siempre corchetes.

## Convertir a cadena: conversión

Al igual que con los números, en PHP generalmente no hay necesidad de convertir explícitamente a una cadena: si usamos `echo` de un número, se convierte automáticamente. Sin embargo, hay algunos valores, especialmente `null` y booleanos, para los cuales necesita saber *cómo* se produce la conversión:

| Valor inicial | Convertido a cadena |
|---|---|
| `null` | cadena vacía `''` |
| `true` | `'1'` |
| `false` | cadena vacía `''` |
| número | la representación textual del número |
| array | la palabra `Array` (con una advertencia) |

Comprobemos con el reparto explícito `(string)`:

```php
<?php

var_dump((string) null);    // string(0) ""
var_dump((string) true);    // string(1) "1"
var_dump((string) false);   // string(0) ""

$bool = true;
echo $bool;   // 1  (conversión automática, sin cast)

$bool = false;
echo $bool;   // (no se muestra nada: cadena vacía)
```

Código completo: [listing-28.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-28.php)


Preste atención al caso del array: si usamos un array donde PHP espera una cadena, como en `echo`, obtenemos la palabra `Array` y PHP nos indica que estamos haciendo algo incorrecto con la advertencia *Conversión de array a cadena*:

```php
<?php

$ar = [1, 2, 3];
echo $ar;   // Warning: Array to string conversion — output: Array
```

Código completo: [listing-29.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-29.php)


Aprovecho esta oportunidad para formalizar la **concatenación**: una cadena se concatena con otra cadena (o con cualquier valor, que se convertirá en una cadena) usando el **punto** (`.`). No el `+` como en JavaScript: en PHP el plus es solo aritmético.

```php
<?php

$name = 'Juan';
$bool = true;

echo $name . ' Arias';   // Juan Arias
echo $name . $bool;      // Juan1   (true → '1')

$bool = false;
echo $name . $bool;      // Juan    (false → cadena vacía)
```

Código completo: [listing-30.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-30.php)


Como puede ver, en la concatenación el booleano se convierte en una cadena automáticamente, sin necesidad de conversión explícita: las reglas son siempre las de la tabla anterior.

## Heredoc y ahoradoc

Además de las comillas simples y las comillas simples, PHP ofrece una tercera forma de representar cadenas: la construcción **heredoc**. Es muy útil cuando tenemos que escribir textos largos, de varias líneas, con variables en su interior, sin tener que gestionar comillas y concatenaciones.

### La sintaxis heredoc

Un heredoc se abre con **tres signos menores** (`<<<`) seguidos de un **identificador** de nuestra elección (por ejemplo, `EOD`, *fin de datos*) y se cierra repitiendo el **mismo identificador**, seguido del punto y coma. El identificador sigue las mismas reglas que los nombres de variables (debe comenzar con una letra o guión bajo, luego letras, números y guiones bajos), sin el signo de dólar:

```php
<?php

$name = 'Juan';
$lastName = 'Arias';
$address = 'Calle Mayor';

$data = <<<EOD
Mi nombre es $name <br>
Mi apellido es $lastName <br>
Mi dirección es $address
EOD;

echo $data;
```

Código completo: [listing-31.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-31.php)


Salida al navegador:

```text
Mi nombre es Juan
Mi apellido es Arias
Mi dirección es Calle Mayor
```

Código completo: [listing-32.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-32.txt)


Entre la apertura y el cierre podemos poner lo que queramos, incluso un poema, y las variables se **interpolan** exactamente como dentro de las comillas.

### Arrays y objetos dentro de un heredoc

**arrays** y **objetos** también se pueden interpolar entre comillas y heredocs (los estudiaremos en breve y en la Parte VII respectivamente, pero un ejemplo sirve para establecer la sintaxis). Con un índice numérico no hay problemas:

```php
<?php

$accounts = [2, 3];

$data = <<<EOD
La primera cuenta es $accounts[0]
EOD;

echo $data;   // La primera cuenta es 2
```

Código completo: [listing-33.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-33.php)


Sin embargo, si la clave es una cadena, escribir las comillas dentro de la interpolación simple produce un **error de sintaxis**:

```php
$accounts['accountNumber'] = 223344;

// ERROR DE SINTAXIS:
// $data = <<<EOD
// El número de cuenta es $accounts['accountNumber']
// EOD;
```

Código completo: [listing-34.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-34.php)


Hay dos soluciones: eliminar las comillas de la clave (funciona, pero no me gusta) o, y esto es lo que prefiero, mantener las comillas y encerrar la expresión completa entre **llaves**:

```php
<?php

$accounts = [2, 3];
$accounts['accountNumber'] = 223344;

$data = <<<EOD
El número de cuenta es {$accounts['accountNumber']}
EOD;

echo $data;   // El número de cuenta es 223344
```

Código completo: [listing-35.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-35.php)


Entre las llaves puedes poner cualquier expresión PHP válida, incluso una variable simple como `{$address}` (en ese caso las llaves no serían necesarias, pero PHP hace el análisis de todos modos). Sólo tenga cuidado de no anidar una variable dentro de otra en la misma expresión simple: si es necesario, cierre y abra una nueva expresión entre llaves.

Con objetos la sintaxis de flechas funciona directamente; Las llaves se vuelven necesarias sólo para casos más complejos, como llamar a un método:

```php
<?php

$object = new stdClass();
$object->name = 'Jim';

$data = <<<EOD
El nombre es $object->name
EOD;

echo $data;   // El nombre es Jim
```

Código completo: [listing-36.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-36.php)


Para uso básico recuerda esto: variable simple o array con índice numérico → el nombre es suficiente; array con clave de cadena (entre comillas) o expresiones más complejas → llaves.

### La sintaxis de Nowdoc

El **nowdoc** es idéntico al heredoc, con una diferencia: el identificador de apertura debe estar entre **comillas simples**. Y la diferencia de comportamiento es la misma que entre comillas y comillas simples: **nada** dentro se interpreta.

```php
<?php

$name = 'Juan';

$code = <<<'EOD'
Mi nombre es $name <br>
EOD;

echo $code;   // Mi nombre es $name <br>   (literal!)
```

Código completo: [listing-37.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-37.php)


¿Para qué es? Por ejemplo, cuando queremos mostrar **código PHP como texto** (en un tutorial, en una página que explica cómo crear una clase) sin que se interprete: los dólares, las variables y las nuevas líneas permanecen exactamente como los escribimos.

### ¿Qué hay de nuevo en PHP 7.3?

Hasta PHP 7.2, el marcador de cierre tenía que estar **solo, al principio de la línea**, sin ninguna sangría, bajo pena de un error de sintaxis. Desde **PHP 7.3** en adelante podemos sangrar el marcador de cierre y la sangría del marcador se elimina de todas las líneas de contenido:

```php
<?php

function getList()
{
    $content = <<<EOD
        <ul>
            <li>uno</li>
            <li>dos</li>
        </ul>
        EOD;

    return $content;
}

echo getList();
```

Código completo: [listing-38.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-38.php)


No más marcadores pegados en el margen izquierdo en medio del código sangrado: el editor no informa errores y `echo` muestra el contenido regularmente. La única regla es que el contenido no puede tener una sangría *menos* que el marcador de cierre. Esto se aplica tanto a heredoc como a nowdoc.

## Arrays: definición y claves
Con este párrafo comenzamos el estudio de los **arrays**, una de las estructuras más importantes en PHP. Una array es un conjunto de datos que puede funcionar como un mapa de pares **clave-valor**, como una lista, como una tabla hash, como una pila, como una cola o como un diccionario. Junto con las cadenas, los arrays son la parte del lenguaje que hay que dominar a la perfección: PHP trae consigo **cientos de funciones nativas** para procesarlos, y a la hora de resolver problemas reales nos encontraremos usándolos continuamente (el Capítulo 12 está dedicado a esto).

### Crear una array

Hay dos sintaxis: la construcción **`array()`**, que existe desde los orígenes del lenguaje, y la **sintaxis corta** entre corchetes `[]`, que es la que usaremos:

```php
<?php

$ar = array('red', 'green', 'blue');   // sintaxis histórica
$ar = ['red', 'green', 'blue'];        // sintaxis corta, equivalente
```

Código completo: [listing-39.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-39.php)


Podemos declarar los pares clave-valor explícitamente, pero si no indicamos las claves PHP las crea automáticamente: **claves numéricas empezando desde cero**. Comprobemos con `var_dump()`:

```php
<?php

$ar = ['red', 'green', 'blue'];
var_dump($ar);
```

Código completo: [listing-40.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-40.php)


```text
array(3) {
  [0]=>
  string(3) "red"
  [1]=>
  string(5) "green"
  [2]=>
  string(4) "blue"
}
```

Código completo: [listing-41.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-41.txt)


`var_dump()` nos dice todo: el tipo (array), el tamaño (3), cada clave y cada valor con tipo y longitud. También hay otra función muy conveniente, **`print_r()`**, que solo muestra la estructura (claves y valores) sin los tipos:

```php
<?php

print_r($ar);
```

Código completo: [listing-42.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-42.php)


```text
Array
(
    [0] => red
    [1] => green
    [2] => blue
)
```

Código completo: [listing-43.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-43.txt)


A veces no nos importa el tipo sino solo cómo está compuesta la array, y `print_r()` es más legible. En el resto de los ejemplos usaré `var_dump()`, que proporciona la descripción más completa.

### Agregar elementos y elegir índices

A diferencia de JavaScript, en PHP para agregar un elemento no es obligatorio indicar la clave: basta con usar los **corchetes vacíos** y PHP toma el índice numérico más alto ya utilizado y lo aumenta en uno:

```php
<?php

$ar = ['red', 'green', 'blue'];

$ar[] = 'pink';      // termina en la posición 3

$ar[9] = 'yellow';   // podemos saltar directamente a la posición 9
$ar[] = 'magenta';   // el siguiente índice automático es 10!
```

Código completo: [listing-44.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-44.php)


Como puede ver, también podemos indicar la posición omitiendo valores: después de poner `yellow` en la posición 9, el contador interno comienza nuevamente desde allí, y el siguiente `[]` usa 10. Nada nos impide llenar un "hueco" indicando explícitamente un índice no utilizado, por ejemplo 4, y en la posición 4 podemos poner cualquier valor, incluso **otra array**:

```php
<?php

$ar[4] = [2, 4, 24, 44, 100];
```

Código completo: [listing-45.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-45.php)


Aquí está nuestra primera array dentro de una array: volvemos a ella en el párrafo sobre arrays multidimensionales.

### Claves de cadena y claves numéricas en la misma array

PHP nos permite usar **claves de cadena** y claves numéricas en la misma array, lo que lo convierte en un mapa completo:

```php
<?php

$ar['amarillo'] = 'amarillo';   // amarillo en español
$ar[] = 'sky';                // va a la posición 11: el contador numérico
                              // ignora por completo las claves de string
```

Código completo: [listing-46.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-46.php)


La clave de cadena no tiene nada que ver con el contador numérico: cada uno continúa por su cuenta. Para leer un valor basta con utilizar la clave con la que lo ingresamos:

```php
<?php

echo $ar['amarillo'];   // amarillo
```

Código completo: [listing-47.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-47.php)


Tenga en cuenta que escribí la clave entre **comillas simples**, siguiendo la convención que sugerí para las cadenas: comillas simples cuando no hay nada que interpolar.

### Las claves siempre van entre comillas

¿Qué pasa si no ponemos superíndices? Lo veo escrito en mucho código antiguo y descuidado:

```php
<?php

echo $ar[amarillo];   // funciona... pero es un error!
```

Código completo: [listing-48.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-48.php)


En PHP 7, este código todavía imprime `amarillo`, pero PHP informa que no encontró la **constante** `amarillo` y dedujo que nos referimos a la cadena `'amarillo'`. Es una advertencia que no bloquea el código, pero que nunca se debe ignorar. En **PHP 8 ya no se tolera**: el uso de una clave sin comillas genera un error fatal (*Constante no definida*).

¿Por qué era tan peligroso? Porque alguien podría definir una constante con ese nombre. Veamos qué pasaría:

```php
<?php

define('amarillo', 4);   // una constante llamada amarillo con valor 4

print_r($ar[amarillo]);
// PHP sustituye la constante por su valor: $ar[4]
// y en la posición 4 está... el array [2, 4, 24, 44, 100]!
```

Código completo: [listing-49.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-49.php)


PHP encuentra la constante `amarillo`, ve que es 4 y lee la posición 4, donde está la array anidada, no `amarillo`. Un error furtivo y difícil de encontrar. Moraleja: **siempre coloque comillas alrededor de las claves de cadena**.

### Cómo PHP convierte claves

Las claves de una array pueden ser **sólo números enteros o cadenas**, y PHP aplica conversiones automáticas que es bueno saber:

```php
<?php

$ar['5'] = 'cinque';   // el string "5" se convierte en la clave ENTERA 5
$ar['5.0'] = 'a';      // "5.0" NO es un entero: se queda como el string "5.0"
$ar['5.2'] = 'b';      // se queda como el string "5.2"
$ar[5.2] = 'c';        // float sin comillas: TRUNCADO a la clave entera 5!
```

Código completo: [listing-50.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-50.php)


Una cadena que contiene un número entero "bien formado" se convierte al número correspondiente; una cadena como `"5.0"` o `"5.2"` sigue siendo una cadena. Pero un **float utilizado directamente como clave se trunca**: solo se toma la parte completa, sin ningún error. Imagina un array donde la clave es un precio y el valor es la lista de productos de una tienda con ese precio: si usas el float `5.2` como clave, todo termina bajo la clave `5`. Si desea conservar la clave decimal, debe pasarla explícitamente como una cadena, entre comillas.

Finalmente, cualquier otro tipo utilizado como clave (una array, un objeto) produce un error (*Tipo de compensación ilegal*): el editor le advierte sobre ello incluso antes de ejecutar.

```php
<?php

// $ar[['a']] = 'x';   // TypeError: Illegal offset type
```

Código completo: [listing-51.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-51.php)


## Arrays multidimensionales

Nuestro `$ar` ya es una array **multidimensional**: en la posición 4 contiene otra array. Veamos cómo trabajar con estas estructuras anidadas.

### Acceder a elementos anidados

Para acceder a un elemento anidado, alinee los corchetes, un nivel tras otro. En la posición 4 tenemos `[2, 4, 24, 44, 100]`; para leer el cuarto elemento (índice 3, contando desde cero):

```php
<?php

echo $ar[4][3];   // 44
```

Código completo: [listing-52.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-52.php)


Tenga cuidado al acceder **dentro de una cadena**. Con una array simple, la interpolación directa funciona (`"$ar[2]"` print `blue`), pero con dos niveles de índices no funciona: es necesario encerrar la expresión entre **llaves**, como vimos en los heredocs:

```php
<?php

echo "{$ar[4][3]} <br>";   // 44 — sin llaves no se interpretaría correctamente
```

Código completo: [listing-53.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-53.php)


Ahora agreguemos una clave de cadena que contenga una array con los días de la semana:

```php
<?php

$ar['DIAS'] = ['lunes', 'martes'];

echo "{$ar['DIAS'][1]} <br>";   // martes
```

Código completo: [listing-54.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-54.php)


Recuerde las llaves y recuerde una cosa más: las claves **distinguen entre mayúsculas y minúsculas**. Si buscamos `dias` en minúsculas, PHP no encuentra la clave y reporta *Clave de array no definida "días"*:

```php
<?php

echo $ar['dias'][1];   // Warning: clave no encontrada! 'dias' ≠ 'DIAS'
```

Código completo: [listing-55.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-55.php)


### Editar, agregar y eliminar elementos

Para **modificar** un valor simplemente acceda a su clave y asigne: por ejemplo, sobrescribamos el valor de `'amarillo'`, de `amarillo` a `yellow`:

```php
<?php

$ar['amarillo'] = 'yellow';
```

Código completo: [listing-56.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-56.php)


Para **agregar un elemento a una array anidada** podemos usar la función nativa **`array_push()`**: le pasamos la array a modificar y el valor a agregar:

```php
<?php

array_push($ar['DIAS'], 'miércoles');
var_dump($ar['DIAS']);
// lunes, martes, miércoles — miércoles ha pasado a la posición siguiente (2)
```

Código completo: [listing-57.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-57.php)


Para **eliminar** una clave (y su valor), existe **`unset()`**: le pasamos el elemento a eliminar.

```php
<?php

unset($ar['DIAS']);     // la clave DIAS desaparece por completo del array
unset($ar[2]);          // también eliminamos 'blue', en la posición 2
```

Código completo: [listing-58.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-58.php)


Aquí hay un detalle importante: con teclas numéricas `unset()` **deja un agujero**. Las claves no están reordenadas: tras quitar la posición 2 tendremos 0, 1, 3, 9, 10... Veámoslo en un array limpio:

```php
<?php

$ar2 = ['a', 'b', 'c', 'd'];
unset($ar2[2]);   // eliminamos 'c'

var_dump($ar2);
```

Código completo: [listing-59.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-59.php)


```text
array(3) {
  [0]=>
  string(1) "a"
  [1]=>
  string(1) "b"
  [3]=>
  string(1) "d"
}
```

Código completo: [listing-60.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-60.txt)


Las claves son 0, 1 y **3**: el 2 desapareció y nadie lo ha renumerado. Si queremos las claves ordenadas 0, 1, 2 nuevamente, usamos **`array_values()`**, que devuelve todos los valores de una array reindexando las claves numéricas desde cero:

```php
<?php

$ar2 = array_values($ar2);
var_dump($ar2);
// ahora las claves son 0, 1, 2
```

Código completo: [listing-61.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-61.php)


`array_values()` también es útil en nuestra array mixta: al llamarlo `$ar` obtenemos una nueva array donde cada elemento (colores, array anidada, todo) recibe una clave numérica progresiva 0, 1, 2, 3... y las claves de cadena desaparecen. Recuerde esto cada vez que necesite una copia de una array con las claves numéricas ordenadas. En el Capítulo 12 veremos muchas otras funciones para manipular arrays: agregar y eliminar valores iniciales y finales, ordenarlos, filtrarlos y más.

## Las constantes: const y define

Una **constante**, como su nombre lo indica, es un valor que no cambia. Pensemos de nuevo en pi: si lo ponemos en una variable, nada nos impide sobrescribirlo por accidente.

```php
<?php

$pi = 3.1415;
echo $pi . PHP_EOL;

$pi = 1.718;          // válido: es una variable
echo $pi . PHP_EOL;   // pi ahora vale 1.718...
```

Código completo: [listing-62.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-62.php)


(`PHP_EOL` es una constante PHP predefinida que contiene el carácter de fin de línea correcto para la plataforma en la que se ejecuta el script, y al final del párrafo veremos que está definido exactamente con las herramientas que estamos a punto de estudiar).

### Declarando una constante con const

Para declarar una constante, utilice la palabra clave **`const`**. El nombre sigue las mismas reglas que las variables, con una diferencia: **sin dólar**: si intenta ingresarlo, el editor informará inmediatamente un error de sintaxis. Por convención, los nombres de las constantes se escriben **todos en mayúsculas**, y si están compuestos por varias palabras se separan con el guión bajo (`TAX_RATE`):

```php
<?php

const PI = 3.1415;

echo PI;      // 3.1415
// PI = 3;    // ERROR: no se puede asignar a una constante
```

Código completo: [listing-63.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-63.php)


Una vez asignado, el valor ya no puede cambiar: el editor ya informa del intento de sobrescritura, y al ejecutarlo obtendríamos un error. El valor de un `const` puede ser un literal (un número, una cadena) o una **expresión constante**, calculable sobre la marcha en el momento de la compilación:

```php
<?php

const RESULT = 3 * 5;   // OK: expresión calculable inmediatamente
```

Código completo: [listing-64.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-64.php)


Sin embargo, no puede depender de algo que sólo se conoce en tiempo de ejecución: una llamada a una función, una lectura de la base de datos. Debe ser un valor determinable en el momento que lo asignamos.

Dos avances. Primero: encontraremos la misma sintaxis `const` **dentro de las clases** en la Parte VII, donde las constantes pertenecerán a la clase en lugar del alcance global. Segundo: cuando estudiemos la visibilidad veremos que las variables son visibles sólo en el contexto en el que surgen; dentro de una función, una variable externa no se puede ver a menos que se importe. **Las constantes, por otro lado, son globals**: una vez definidas, son visibles en todas partes, incluso dentro de las funciones.

### definirlo y verificarlo con definido

Hay una segunda forma, más antigua, de definir una constante: la función **`define()`**, a la que le pasamos el nombre de la constante como una cadena y el valor:

```php
<?php

define('PI2', 3.1415);
echo PI2;   // 3.1415
```

Código completo: [listing-65.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-65.php)


Pero cuidado: si intentamos definir la misma constante dos veces, el editor no lo nota (porque es una llamada de función normal) y nosotros sólo lo notamos ejecutando, con el aviso *Constante PI2 ya definida*:

```php
<?php

define('PI2', 3.1415);
define('PI2', 3);   // Warning: Constant PI2 already defined
```

Código completo: [listing-66.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-66.php)


Una curiosidad histórica: `define()` aceptó un tercer parámetro para hacer que el nombre de la constante *no distinga entre mayúsculas y minúsculas*. Estaba **obsoleto en PHP 7.3 y eliminado en PHP 8**: además de no funcionar, también era peligroso. Los nombres de constantes siempre distinguen entre mayúsculas y minúsculas.

La verdadera ventaja de `define()` es que va acompañada de la función **`defined()`**, que comprueba si ya se ha definido una constante. Así podemos proteger la definición:

```php
<?php

if (!defined('PI2')) {
    define('PI2', 3.1415);
}
```

Código completo: [listing-67.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-67.php)


El signo de exclamación niega la condición: "si `PI2` **no** está definido, defínelo". Al ejecutar el código por segunda vez, PHP no pasa por `define()` y no hay ningún error.

### Arrays como constantes

También podemos declarar una **array** como constante, algo que no era posible en versiones anteriores de PHP 5 (viene con PHP 5.6 para `const` y con PHP 7 para `define()`):

```php
<?php

const PROVINCES = ['Madrid', 'Barcelona'];

// PROVINCES[2] = 'Sevilla';   // ERROR: no se puede modificar una constante
// const PROVINCES = [];    // ERROR: ya definida

define('REGIONS', ['Comunidad de Madrid', 'Cataluña']);
var_dump(REGIONS);
```

Código completo: [listing-68.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-68.php)


Como ocurre con cualquier constante, no podemos ni añadir elementos ni reasignarla: el editor nos lo indica inmediatamente. Y tenga cuidado al acceder a una constante que no existe: en versiones muy antiguas de PHP el nombre se trataba silenciosamente como una cadena (con una advertencia), pero en PHP moderno obtenemos un **error fatal** (*Constante no definida*). Una razón más para utilizar `defined()` en caso de duda.

En resumen, y también les daré mi preferencia personal: en mi código ya casi no uso `define()`; uso **`const`**, que es más corto de escribir, lo entiende el editor (que nos advierte sobre sobrescrituras y reasignaciones incluso antes de ejecutar) y deja menos espacio para errores tipográficos entre paréntesis y superíndices. `define()` sigue siendo útil cuando necesitas la definición condicional con `defined()`. Y recuerda el ejemplo del propio PHP: la constante `PHP_EOL` que usamos antes se define así, nombre en mayúsculas con guión bajo, valor igual al carácter de fin de línea de la plataforma.

## Verifique las variables: isset, vacío e is_null

Cerramos el capítulo con tres funciones nativas que sirven para responder a tres preguntas diferentes sobre una variable: ¿se ha establecido? ¿Está vacío? ¿Es `null`? Parecen similares, pero las diferencias son importantes y los usaremos una y otra vez cuando obtengamos datos de los formularios de la Parte IV.

### isset: ¿Está configurada la variable?

**`isset()`** comprueba si se ha configurado una variable **y** si tiene un valor diferente al de `null`:

```php
<?php

if (isset($name)) {
    echo "$name existe";
} else {
    echo 'La variable no existe';
}
// Output: La variable no existe
```

Código completo: [listing-69.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-69.php)


Tenga en cuenta que `$name` ni siquiera lo declaramos, pero `isset()` no genera ninguna advertencia: simplemente responde `false`. Si asignamos cualquier valor, incluso una cadena vacía, incluso `0`, `isset()` responde `true`. El único valor al que `false` responde en una variable declarada es `null`.

### vacía: ¿Está vacía la variable?
**`empty()`** comprueba si una variable está "vacía". Pero ¿qué significa vacío para PHP? Una variable está vacía cuando **no ha sido declarada** o cuando su valor, **convertido a booleano, se convierte en `false`**: exactamente los valores falsos que vimos al estudiar el tipo booleano:

```php
<?php

if (empty($name)) {
    echo 'name está vacía';
} else {
    echo "name no está vacía y es igual a $name";
}
```

Código completo: [listing-70.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-70.php)


Probemos los distintos casos:

```php
<?php

// $name nunca declarada     -> vacía (y sin warning!)
$name = '';       // vacía
$name = 'Juan'; // no vacía
$name = 0;        // vacía
$name = '0';      // vacía — atención!
$name = 0.0;      // vacía
$name = null;     // vacía
$name = false;    // vacía
$name = [];       // vacía (array sin elementos)
```

Código completo: [listing-71.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-71.php)


Dos observaciones. La primera: hay que prestar mucha atención al **cero**. `empty()` considera que tanto el número entero `0` como la cadena `'0'` están vacíos: entonces `isset()` diría que la variable está configurada, pero `empty()` la da como vacía. Si cero tiene un significado para usted (por ejemplo, necesita poder establecer un precio en cero), **no** use `empty()`: más bien, verifique que el valor no sea `null`, como veremos inmediatamente.

El segundo: `empty()` sobre una variable nunca declarada **no genera ningún aviso**. Si en lugar de eso intentáramos un simple `if ($name)` en una variable no declarada, PHP reportaría *Variable no definida*: un aviso hasta PHP 7.4, una advertencia de PHP 8. No es un error de bloqueo de ejecución, y en un entorno de producción ni siquiera lo verías, pero no deberías ignorarlo. `empty()` nos permite realizar la verificación de forma limpia.

### is_null: ¿La variable es nula?

**`is_null()`** comprueba solo una cosa: si la variable tiene el valor **`null`** — solo `null`, no algo que se parezca a eso:

```php
<?php

$name = null;

if (is_null($name)) {
    echo 'name es null';
} else {
    echo 'name no es null';
}
// Output: name es null
```

Código completo: [listing-72.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-72.php)


Conceptualmente `is_null()` es casi lo opuesto a `isset()`: una variable `null` no está configurada y `!isset($name)` significa "es `null` o nunca se ha definido". Sin embargo, hay una diferencia práctica: si la variable **nunca ha sido declarada**, `is_null()` devuelve sí `true`, pero PHP también informa la advertencia *Variable no definida*; `isset()` sin embargo, nunca lo hace. Por lo tanto, use `is_null()` cuando esté seguro de que la variable se ha inicializado (por ejemplo, la declaró usted mismo y luego el valor proviene de un archivo o recurso externo) y solo desea saber si contiene `null`.

Tenga cuidado de no confundir `null` con la cadena vacía: son conceptos diferentes.

```php
<?php

$name = '';
var_dump(is_null($name));   // bool(false): la cadena vacía NO es null

var_dump(null == '');       // bool(true)  — comparación débil: ambos valores son falsy
var_dump(null === '');      // bool(false) — tipos diferentes!
```

Código completo: [listing-73.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/es/parte-02/cap-07/listing-73.php)


Con la comparación de dos iguales, PHP convierte y `null` es igual a la cadena vacía; con la comparación de tres es igual a no, porque los tipos son diferentes. PHP puede resultar confuso aquí: mantenga los tres conceptos separados: *conjunto*, *vacío*, *nulo*.

### ¿Qué función utilizar?

Aquí está la tabla resumen que uso como regla general:

| Pregunta | Función | Notas |
|---|---|---|
| ¿Existe la variable y no es `null`? | `isset()` | nunca advertencias; `true` para cualquier valor excepto `null` |
| ¿Está la variable vacía (falsa)? | `empty()` | nunca advertencias; pero `0` y `'0'` están vacíos |
| ¿La variable es exactamente `null`? | `is_null()` | advertencia si la variable no está declarada |

Si solo desea saber que la variable está configurada, use `isset()`. Si le importa que esté *y* no vacío, y para su cadena vacía, `false`, cero y array vacía cuentan como "nada", no dude en usar `empty()`. Si cero es un valor legítimo en su contexto, evite `empty()` y verifique con `is_null()` o con una comparación explícita.

## En resumen
- Una **variable** es un área de memoria con un nombre que actúa como etiqueta: en PHP comienza con `$`, seguido de una letra o guión bajo, luego letras, números y guiones bajos. Utilice nombres parlantes y la convención camelCase; PHP se escribe dinámicamente, por lo que el tipo puede cambiar en tiempo de ejecución.
- Los números son **enteros** o **flotantes**; Los números enteros también se pueden escribir en octal (`0`), hexadecimal (`0x`) y binario (`0b`). PHP convierte automáticamente cadenas numéricas en operaciones, pero es una buena práctica respetar los tipos.
- El tipo **booleano** solo tiene `true` y `false`, pero se puede convertir cualquier valor: almacene la lista de valores falsos (`false`, `0`, `0.0`, `''`, `'0'`, `[]`, `null`) — todo lo demás es cierto. Desde los formularios envíe `0`/`1`, no las cadenas `'true'`/`'false'`.
- **cadenas** son secuencias de bytes: las comillas simples no interpolan variables, las comillas dobles sí (junto con escapes como `\n`). Para caracteres multibyte (acentos, UTF-8), utilice las funciones `mb_*`: `strlen()` cuenta bytes, `mb_strlen()` cuenta caracteres.
- Cuando se convierte en una cadena: `null` y `false` se convierten en una cadena vacía, `true` se convierte en `'1'`, una array se convierte en la palabra `Array` (con advertencia). La concatenación se realiza con el **punto**, no con el `+`.
- **Heredoc** (`<<<EOD`) interpola variables, arrays y objetos (con llaves para expresiones complejas); **nowdoc** (`<<<'EOD'`) no interpreta nada. Desde PHP 7.3, el marcador de cierre puede tener sangría.
- **arrays** aceptan claves enteras y de cadena en la misma array; `[]` añade utilizando el índice numérico más alto + 1. Siempre cita las claves de cadena; recuerde que los flotantes como clave se truncan y que `unset()` deja huecos en los índices numéricos: `array_values()` los reindexa.
- **las constantes** se definen con `const` (preferido) o `define()`; nada `$`, nombre en mayúscula por convención, valor inmutable y computable en tiempo de compilación, arrays permitidas. `defined()` comprueba su existencia; Las constantes son visibles en todas partes.
- **`isset()`** dice si se establece una variable y no `null`; **`empty()`** si es falso (¡cuidado con el cero!); **`is_null()`** si exactamente `null` es válido. Ninguno de los dos primeros genera advertencias sobre variables no declaradas.
