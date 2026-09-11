# 10. las funciones

Hasta este punto hemos escrito scripts que ejecutan declaraciones una tras otra y hemos aprendido a controlar su flujo con condiciones y bucles. Sin embargo, falta un ingrediente esencial de cualquier lenguaje: la forma de **agrupar un bloque de instrucciones bajo un nombre** y reutilizarlo tantas veces como sea necesario, sin copiar y pegar el mismo código. Esta herramienta es la **función** y es el corazón de este capítulo.

Las funciones son muy importantes en PHP como en muchos otros lenguajes. Comenzaremos desde lo básico: qué es una función, cómo declararla, cómo pasarle datos y cómo obtener un resultado, y llegaremos a las nuevas características del PHP moderno: la declaración de tipo introducida con PHP 7, funciones anónimas y funciones de flecha, parámetros variables, argumentos con nombre y tipos de unión de PHP 8. Es un capítulo sustancial, pero cada párrafo agrega una parte: al final tendrás todo lo que necesitas para escribir código reutilizable y bien escrito. Para los ejemplos, solo necesita un libro de trabajo con un archivo (por ejemplo `functions.php`) que se ejecutará desde la línea de comando con `php functions.php`, o que será servido por el servidor integrado que aprendimos a iniciar en los capítulos anteriores.

## ¿Qué es una función?

Una **función** es una construcción que nos permite recopilar en su interior un bloque de instrucciones para realizar una operación específica. Puede recibir uno o más **parámetros** como entrada y puede devolver un valor en la salida o no devolver nada. En PHP no existe un concepto separado de "procedimiento" que encontramos en otros lenguajes: un procedimiento es simplemente una función que no devuelve ningún valor.

El nombre de una función debe seguir las mismas reglas que los nombres (las "etiquetas") en PHP: comienza con una letra o un guión bajo, seguido de letras, números o guiones bajos. A diferencia de los nombres de variables, el nombre de una función **no distingue entre mayúsculas y minúsculas**. La declaración siempre va precedida de la palabra clave `function`.

Vale la pena tener en cuenta de inmediato algunas características de las funciones en PHP:

- Se pueden **llamar incluso antes de su definición** en el archivo, excepto cuando la definición está incluida dentro de una condición (por ejemplo, `if`): en ese caso la función existe solo después de que se haya ejecutado esa rama.
- Pueden estar **anidados**, pero la función interna no existe hasta que se llama a la externa que la contiene.
- Tienen **visibilidad global**: una vez definidos, se pueden llamar desde cualquier parte del script.
- Pueden tener parámetros variables y parámetros de valor predeterminado, y pueden llamarse **recursivamente** (es decir, llamarse a sí mismos).

Vayamos directamente a la práctica.

## Declarar una función

Creamos una función cuando PHP aún no proporciona una que satisfaga nuestras necesidades. Ya hemos utilizado funciones integradas como `isset()` para comprobar si una variable está configurada o `empty()` para comprobar si está vacía; ahora aprendamos a escribir el nuestro. El caso típico es este: hay líneas de código que repetimos continuamente y, en lugar de copiar y pegar, las encerramos en una función y la ejecutamos cada vez que lo necesitamos.

### La sintaxis básica

Para declarar una función necesita, como mínimo, la palabra clave `function`, un **nombre**, paréntesis y llaves. El nombre es fundamental: sin él no sabríamos cómo invocar la función. Por convención, y dependiendo del marco con el que esté trabajando, los nombres de las funciones comienzan con una letra minúscula y, si están compuestos por varias palabras, usan la notación **camelCase** (cada palabra subsiguiente comienza con una letra mayúscula).

Escribamos una función que siempre muestre un saludo:

```php
<?php

function sayHello()
{
    echo 'Hola mundo';
}
```

Código completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-01.php)


Entre llaves está el **cuerpo** de la función: todas las instrucciones que queremos ejecutar, línea por línea. Para ejecutar la función basta con **invocarla**, es decir, escribir su nombre seguido de corchetes (vacíos, porque esta función no recibe ningún parámetro):

```php
sayHello(); // Hola mundo
```

Código completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-02.php)


El cuerpo también podría estar vacío: en ese caso la función es completamente legítima pero no produce ningún efecto cuando la llamamos.

### Ejecute el script
Podemos ejecutar el script de varias formas. Lo más conveniente, cuando generamos PHP puro sin HTML, es la **línea de comando**: abrimos la terminal (incluso la integrada en el editor) y, dado que `php` debe estar en la RUTA, como configuramos en el capítulo de instalación, lanzamos:

```bash
php functions.php
```

Código completo: [listing-03.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-03.sh)


y vemos aparecer `Hola mundo`. Alternativamente, si queremos ejecutarlo a través de un servidor en el navegador, iniciamos el servidor integrado indicando un puerto libre:

```bash
php -S localhost:4000 functions.php
```

Código completo: [listing-04.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-04.sh)


Editores como Visual Studio Code y PhpStorm también ofrecen un botón para ejecutar el script o iniciar el servidor integrado sin pasar por la terminal: cualquier forma está bien, lo importante es poder ejecutar el archivo. Mientras trabajemos con PHP puro es mejor permanecer en la línea de comandos, así no tendremos que cambiar constantemente entre editor y navegador.

### Asignar una función a una variable

Hay una segunda forma de definir una función: **asignar su cuerpo a una variable**. En lugar del nombre escribimos el nombre de la variable, el igual y luego `function`:

```php
$sayHi = function () {
    echo 'Hola';
};
```

Código completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-05.php)


Tenga en cuenta el **punto y coma** final: aquí no estamos declarando una función con nombre, sino asignando un valor a una variable, por lo que la declaración debe cerrarse como cualquier otra asignación (el editor nos avisa si la olvidamos). Para ejecutarlo usamos el nombre de la variable seguido de paréntesis:

```php
$sayHi(); // Hola
```

Código completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-06.php)


La sintaxis es la misma que la de una función normal, solo cambia `$` delante del nombre. Sin embargo, existe una **diferencia fundamental**. Una función con nombre también se puede llamar *antes* de su definición en el archivo:

```php
sayHello();      // funciona, aunque sayHello() está definida más abajo

function sayHello()
{
    echo 'Hola mundo';
}
```

Código completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-07.php)


Una función asignada a una variable, sin embargo, **no puede ser llamada antes de la asignación**: si lo intentamos, PHP genera un error, porque en ese momento la variable aún no existe. La regla es intuitiva: PHP "ve" la función nombrada a lo largo del script, mientras que la variable cobra vida sólo cuando le asignamos la función.

Entonces, ¿cuál es el punto de poner una función en una variable? La razón es que en PHP una función es un **ciudadano de primera clase**: podemos pasarla como argumento a otra función y ejecutarla en otro lugar. Las funciones asignadas a variables (que en realidad son instancias de una clase interna, `Closure`) son la herramienta con la que haremos esto, como veremos en los párrafos de funciones anónimas.

## Parámetros y argumentos

Una función se vuelve realmente útil cuando le pasamos datos. Dentro de los corchetes podemos declarar uno o más **parámetros**: son como variables que la función espera recibir. Cambiemos el saludo para aceptar un nombre:

```php
<?php

function sayHello($name)
{
    echo "Hola $name";
}
```

Código completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-08.php)


Es importante distinguir dos términos que suelen confundirse:

- el **parámetro** es la variable que declaramos cuando *escribimos* la función (`$name` arriba);
- el **argumento** es el valor concreto que pasamos cuando *llamamos* a la función.

Entonces, en `sayHello('Juana')`, `$name` es el parámetro y `'Juana'` es el argumento que le pasamos.

### Parámetros con valor predeterminado

Un parámetro puede tener un **valor predeterminado**, que se usa cuando el llamador de la función no pasa ningún argumento:

```php
function sayHello($name = 'mundo')
{
    echo "Hola $name";
}

sayHello();        // Hola mundo
sayHello('Juana');  // Hello Juana
```

Código completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-09.php)


Si no pasamos nada, `$name` es `'mundo'`; si pasamos un argumento, reemplaza el predeterminado.

### Múltiples parámetros y orden de argumentos

Cuando hay más de un parámetro, debemos **respetar su orden** al llamar, de lo contrario los valores terminarán en parámetros incorrectos. Escribamos una función que muestre el nombre completo de una persona:

```php
function getFullName($name, $surname)
{
    echo "El nombre completo es $name $surname";
}

getFullName('Juana', 'Arias'); // El nombre completo es Juana Arias
```

Código completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-10.php)


Si estos parámetros son **requeridos** (no tienen un valor predeterminado) y no los pasamos, PHP genera un `ArgumentCountError`, indicando que falta un argumento. Aquí ya está la utilidad de las funciones: sin ellas, para mostrar nombres más completos tendríamos que repetir el mismo `echo` para cada persona; con la función llamamos al mismo código pasando datos diferentes, lo que es muy conveniente cuando esos datos llegan, por ejemplo, de una base de datos.

### Declarar el tipo de parámetros y tipos_estrictos
El editor, cuando escribimos una función, muchas veces nos dice que no estamos indicando ni el tipo de parámetros ni el tipo de retorno. A partir de PHP 7 podemos declararlos, y es conveniente hacerlo porque hace que el código sea más seguro y legible. Indicamos el tipo escribiéndolo **antes** del parámetro:

```php
function getFullName(string $name, string $surname)
{
    echo "El nombre completo es $name $surname";
}
```

Código completo: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-11.php)


Pero tenga cuidado: por defecto PHP aplica el llamado **modo coercitivo**, es decir, intenta *convertir* el argumento al tipo declarado. Si pasamos el número `44` a un parámetro declarado `string`, PHP lo convierte en una cadena sin protestar. Si queremos que los tipos se verifiquen rigurosamente, sin ninguna conversión, debemos colocar la directiva en la parte superior del archivo, **como la primera línea**:

```php
<?php

declare(strict_types=1);
```

Código completo: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-12.php)


Con `strict_types=1`, pasar un número donde se requiere una cadena genera un `TypeError`. La ventaja es doble: por un lado PHP bloquea el error en tiempo de ejecución, por otro el editor ya nos lo informa mientras escribimos, incluso antes de ejecutar el código. Mi consejo, por experiencia diaria, es poner siempre `declare(strict_types=1)` al principio de los archivos: escribir tiene sentido precisamente cuando se respetan verdaderamente los tipos.

### Argumento con nombre y valores predeterminados

Cuando hay muchos parámetros, recordar su orden se vuelve inconveniente y se corre el riesgo de cometer errores. PHP 8 viene en nuestra ayuda con **argumentos con nombre**: podemos pasar los argumentos indicando el nombre del parámetro (sin `$`), seguido de los dos puntos y el valor, **en cualquier orden**. Agreguemos un tercer parámetro, edad, a la función:

```php
function getFullName(string $name, string $surname, int $age)
{
    echo "$name $surname, $age años";
}

// con argumentos con nombre, el orden no importa:
getFullName(age: 45, name: 'María', surname: 'García');
```

Código completo: [listing-13.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-13.php)


Volveremos a los argumentos con nombre en un párrafo dedicado más adelante. Por ahora necesitamos aclarar una regla sobre los valores predeterminados. Si un parámetro con un valor predeterminado viene *antes* de un parámetro obligatorio, ese valor predeterminado efectivamente se vuelve inútil: dado que todavía tenemos que pasar el siguiente argumento, nos vemos obligados a pasar también el que tendría el valor predeterminado. De hecho, PHP 8 informa como **obsoleto** declarar un parámetro opcional antes que uno obligatorio. La regla general es clara: **los parámetros con valores predeterminados deben colocarse al final** de la lista. Los argumentos con nombre alivian el problema (le permiten omitir parámetros intermedios que tienen un valor predeterminado), pero la convención sigue siendo válida.

## Valores de retorno

Hasta ahora nuestras funciones mostraban algo en la pantalla pero no devolvían nada. El caso más interesante es aquel en el que la función **calcula un resultado y nos lo entrega**, para que podamos capturarlo, imprimirlo o pasarlo a otras operaciones.

### devolución y tipo de devolución

Para devolver un valor utilizamos la palabra clave `return`. Escribamos una función simple que sume dos números enteros:

```php
<?php

declare(strict_types=1);

function suma(int $a, int $b): int
{
    return $a + $b;
}
```

Código completo: [listing-14.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-14.php)


Dos detalles. Primero: `return` interrumpe la función y devuelve el valor indicado. Segundo: después de los corchetes escribimos `: int`, que declara el **tipo de devolución**. Dado que agregamos dos `int`, la función siempre devolverá un `int`; si intentáramos devolver algo diferente, PHP generaría un error (y el editor nos avisaría con antelación).

¿Cómo capturamos el resultado? La función, por sí sola, no imprime nada: debemos usar el valor que devuelve. Podemos pasarlo directamente a `echo`, o guardarlo en una variable:

```php
echo suma(4, 5);           // 9

$result = suma(4, 5);
echo $result;               // 9
```

Código completo: [listing-15.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-15.php)


Guardar el resultado en una variable es útil cuando queremos reprocesarlo o pasarlo a otras funciones, en lugar de simplemente mostrarlo. Si ponemos un `return 'una cadena';` dentro de la función antes del `return` correcto, con el tipo de retorno `int` declarado, el editor nos advertiría inmediatamente de la inconsistencia: es por eso que declarar tipos es tan valioso.

### Devolver múltiples valores: arrays y desestructuración

En PHP una función **no puede devolver más de un valor escalar**. Si necesitamos devolver varios resultados, la única forma es encerrarlos en una **array**. Escribamos una función que, dados dos lados, calcule el área y el perímetro de un rectángulo:

```php
function calcularAreaPerimetro(int $a, int $b): array
{
    $area = $a * $b;
    $perimetro = 2 * ($a + $b);

    return [$area, $perimetro];
}
```

Código completo: [listing-16.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-16.php)


El tipo de devolución ahora es `array`. Podemos capturar el resultado en una variable e inspeccionarlo con `print_r()`:

```php
$result = calcularAreaPerimetro(5, 4);
print_r($result);
// Array ( [0] => 20 [1] => 18 )
```

Código completo: [listing-17.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-17.php)


En la posición `0` está el área (5 × 4 = 20), en la posición `1` el perímetro (2 × 9 = 18). Aún más elegante es **deestructurar** la array devuelta directamente en dos variables distintas:
```php
[$area, $perimetro] = calcularAreaPerimetro(5, 6);

echo "$area\n";        // 30
echo "$perimetro\n";   // 22
```

Código completo: [listing-18.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-18.php)


Lo mismo se logró una vez con la función `list()`, que recibe el array y las variables en las que distribuir sus valores:

```php
list($a, $b) = calcularAreaPerimetro(5, 6);
echo "$a $b\n"; // 30 22
```

Código completo: [listing-19.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-19.php)


La sintaxis entre corchetes es la más moderna y legible, pero también es útil reconocer `list()` porque la encontrarás en una gran cantidad de código existente.

## Escribir argumentos y devolver (PHP 7)

Profundicemos en la innovación que ha traído PHP 7: la **declaración de tipo** tanto para los parámetros de entrada como para el valor de retorno. Hasta PHP 5 solo podíamos declarar una clase, una interfaz o `array` como tipo de parámetro. Con PHP 7 también podemos usar **tipos escalares** y otros tipos especiales:

- `int` — un número entero;
- `float` — un número con punto decimal;
- `string` — una cadena;
- `bool` — un booleano;
- `array` — una array;
- `callable` — algo que se puede invocar como una función (el nombre de una función, una función anónima, un método o un objeto con el método mágico `__invoke`);
- una **clase** o una **interfaz**.

Presta atención a la nomenclatura: debes escribir exactamente `int`, `bool`, `float`, `string`. Si escribiéramos `integer` o `boolean`, PHP pensaría que nos estamos refiriendo a una *clase* con ese nombre. Tomemos la suma nuevamente:

```php
<?php

function suma(int $a, int $b): int
{
    return $a + $b;
}

echo suma(5, 5); // 10
```

Código completo: [listing-20.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-20.php)


Como ya se vio, sin `declare(strict_types=1)` PHP aplica la conversión implícita: si pasamos la cadena `'5'`, la transforma en un número entero y la suma funciona igual. Esto está bien para conversiones simples (cadena a número y viceversa), pero no para casos ambiguos. Si queremos que PHP verifique los tipos sin convertir nada, ponemos `declare(strict_types=1)` al principio del archivo: en ese punto, pasar `'10'` donde necesitamos un `int` genera un `TypeError`, y lo mismo ocurre con el tipo de retorno.

Veamos algunos ejemplos de tipos no escalares. Agreguemos un tercer parámetro de tipo `array`:

```php
function suma(int $a, int $b, array $c): int
{
    return $a + $b;
}

suma(5, 5, []);          // ok: array vacío
suma(5, 5, 'no es un array'); // TypeError: el tercer argumento no es un array
```

Código completo: [listing-21.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-21.php)


También podemos declarar que un parámetro es de tipo **clase**: en ese caso debemos pasarle una instancia de esa clase (estudiaremos las clases en la Parte VII), de lo contrario obtendremos un error. Y podemos declararlo `callable`, lo que nos permite aceptar el nombre de una función (pasada como una cadena), una función anónima o una variable que contiene un `Closure`:

```php
function ejecutar(callable $c): void
{
    $c(); // invocamos lo que se nos pasó
}

function test()
{
    echo "test\n";
}

ejecutar('test');                       // pasamos el nombre como string
ejecutar(function () { echo "anon\n"; }); // pasamos una función anónima
```

Código completo: [listing-22.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-22.php)


Tenga en cuenta el tipo de retorno `void`: indica que la función **no devuelve ningún valor**. Esta posibilidad de escribir parámetros y devolver, ausente durante mucho tiempo en PHP y presente en lenguajes como Java o C#, es una de las innovaciones más importantes de PHP 7, y es mejor explotarla en nuestros proyectos.

## Parámetros que admiten valores NULL y retorno nulo (PHP 7.1)

Desde PHP 7.1 podemos declarar que un parámetro (o valor de retorno) de un determinado tipo también puede ser **`null`**. Esto se hace colocando un **signo de interrogación** antes del tipo. Reanudemos la suma con los tipos declarados:

```php
function sum(int $a, int $b): int
{
    return $a + $b;
}
```

Código completo: [listing-23.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-23.php)


Si intentamos pasar `null` a uno de los parámetros `int`, obtenemos un `TypeError`: `null` no es un número entero. Para permitir esto, anteponemos `?`:

```php
function sum(?int $a, ?int $b): int
{
    return $a + $b;
}

$result = sum(null, null);
var_dump($result); // int(0)
```

Código completo: [listing-24.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-24.php)


Ahora podemos pasar `null` sin errores. Note un detalle curioso: la función devuelve `int(0)`, porque PHP, sumando dos `null`, los trata como `0`. La devolución sigue siendo `int`, por lo que se respeta el tipo de devolución `int`.

Supongamos en cambio que queremos devolver explícitamente `null` en un caso determinado:

```php
function sum(?int $a, ?int $b): int
{
    if ($a === null || $b === null) {
        return null; // ERROR: el tipo de retorno es int
    }

    return $a + $b;
}
```

Código completo: [listing-25.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-25.php)


Esto genera un error, porque declaramos que la función devuelve `int`, no `null`. La solución es hacer también que el tipo de retorno sea **nullable**, con el mismo `?`:

```php
function sum(?int $a, ?int $b): ?int
{
    if ($a === null || $b === null) {
        return null;
    }

    return $a + $b;
}
```

Código completo: [listing-26.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-26.php)


Una última advertencia. Declarar un parámetro `?int` significa que `null` *puede* ser válido, pero no que sea **opcional**: si lo omitimos por completo en la llamada, PHP aún genera un `ArgumentCountError`. Para que sea realmente opcional debemos darle un valor predeterminado:

```php
function sum(?int $a = null, ?int $b = null): ?int
{
    // ...
}

sum(); // ahora es válido
```

Código completo: [listing-27.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-27.php)


En resumen: el `?` delante del tipo (de un parámetro o retorno) autoriza el valor `null`; Para que un parámetro también sea omitible, necesita un valor predeterminado. Veremos en el Capítulo 32, con excepciones, cómo detectar errores como `ArgumentCountError` y `TypeError` en un bloque `try`/`catch`.

## El alcance de las variables.

Una cuestión central en el uso de funciones es la visibilidad (o alcance) de las variables: qué variables una función puede ver y cuáles no.

### Variables locales

La regla básica es que cada función crea su propio **entorno aislado**. Las variables definidas fuera de la función no son visibles dentro de ella y viceversa, las variables definidas dentro de la función ya no existen una vez que se sale de ella. Veámoslo:

```php
<?php

$data = ['name' => 'John Doe'];

function modificar()
{
    var_dump($data); // Warning: $data no está definida aquí dentro
}

modificar();
```

Código completo: [listing-28.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-28.php)


Al ejecutar el script recibimos una advertencia: dentro de `modificar()` la variable `$data`, aunque existe en el entorno externo, simplemente no es visible. PHP, dentro de la función, crea su propio *alcance* donde solo viven sus variables locales y no ve nada afuera.

### La construcción global

¿Cómo accedemos, desde dentro de una función, a una variable que vive en el entorno global? El entorno global es todo lo que está fuera de las funciones: las variables escritas directamente en el script (o en un archivo incluido), pero no las internas a otras funciones u objetos. La primera forma es la construcción **`global`**, seguida del nombre de la variable que queremos importar:

```php
$object = 'John';

function modificar()
{
    global $object;

    var_dump($object); // ahora vemos 'John'
    $object = 'Juana';  // y también podemos modificarla
}

modificar();
var_dump($object); // 'Juana': la modificación se refleja fuera!
```

Código completo: [listing-29.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-29.php)


Con `global $object` estamos haciendo *referencia* a la variable global: no solo la leemos, sino que si la modificamos dentro de la función **también modificamos la externa**, porque es la misma variable por referencia. Lo mismo ocurre con las arrays y los valores escalares: importadas con `global`, cualquier variable global se puede leer y sobrescribir desde dentro de la función. Ten siempre esto en cuenta, porque es un efecto secundario fácil de olvidar.

### Los $GLOBALS superglobals

La segunda forma de acceder a las variables globals es **superglobal** `$GLOBALS`. Los superglobals son arreglos especiales que PHP pone a disposición en todas partes del script; los estudiaremos en detalle en el Capítulo 13 (`$_GET`, `$_POST`, `$_SESSION`, `$_SERVER`, `$_REQUEST` y otros). `$GLOBALS` es una array grande que contiene **todas las variables globals**, indexadas por nombre:

```php
$name = 'John Doe';

function modificar()
{
    $GLOBALS['name'] = 'Juana'; // accedemos a la global mediante su clave
}

modificar();
echo $GLOBALS['name']; // Juana
```

Código completo: [listing-30.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-30.php)


La clave de la array es el nombre de la variable (sin `$`). Hay un punto importante a entender: si dentro de una función declaramos `global $val` y luego intentamos usar un parámetro local con el mismo nombre, **la referencia global tiene prioridad** y el valor local se ignora. Al eliminar `global`, la variable local volvería a ser visible. En otras palabras, `global` realmente "importa" la variable externa al alcance de la función, colocándola en lugar de cualquier homónimo local.

En la práctica diaria, no se recomienda el uso de `global` (introduce dependencias ocultas y hace que el código sea más difícil de seguir), pero es esencial conocerlo para comprender cómo funciona el alcance en PHP. La regla a establecer es esta: dentro de una función las variables globals no existen a menos que las importemos explícitamente (con `global` o mediante `$GLOBALS`), o a menos que las pasemos como argumentos. Esta última ruta (pasar los datos como parámetros) es casi siempre la mejor opción.

## Funciones anónimas y funciones variables.

Anticipamos que se puede asignar una función a una variable. Una función sin nombre se llama **función anónima** (o *cierre*), y cuando la asignamos a una variable hablamos de una **función variable**. Internamente PHP crea una instancia de su clase `Closure` y la asigna a la variable.

### Asignar una función anónima a una variable

```php
<?php

$suma = function ($a, $b) {
    return $a + $b;
};

echo $suma(2, 3); // 5
```

Código completo: [listing-31.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-31.php)


Recuerde siempre el **punto y coma** después de la llave de cierre: es una asignación, no una declaración de función. Para invocarlo usamos el nombre de la variable y corchetes, exactamente como una función normal. Como ya se vio para las funciones variables, no podemos llamarla antes de haberla definido: la variable `$suma` no existe hasta que le asignamos un cierre.
### Pasar una función como argumento

Lo bueno de las funciones anónimas es que puedes pasarlas como argumentos a otras funciones. Una función que recibe un parámetro `callable` puede ejecutarlo dentro de sí misma:

```php
function test(callable $func)
{
    echo $func(5, 5);
}

test($suma); // 10
```

Código completo: [listing-32.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-32.php)


Si declaramos el parámetro `callable` (o, más específicamente, `Closure`) e intentamos pasarle un número, obtenemos un error: PHP espera algo invocable. Este mecanismo (pasar una función a otra) es la base de muchas operaciones con arrays, que veremos enseguida.

## Funciones anónimas con arrays

Muchas funciones PHP integradas que funcionan en arrays toman una **función de devolución de llamada** como argumento: la aplican a cada elemento y devuelven un resultado. Los más utilizados son `array_map`, `array_filter` y `array_walk`. Centrémonos en `array_map`, que toma una array y una función, aplica la función a cada elemento y **devuelve una nueva array** con los resultados.

### mapa_matriz

Suponga que tiene una lista de números y desea una copia de ellos con cada valor duplicado. Con un bucle `foreach` haríamos esto:

```php
<?php

$numbers = [1, 2, 3, 4, 5];
$doubleArray = [];

foreach ($numbers as $val) {
    $doubleArray[] = $val * 2;
}

print_r($doubleArray);
// Array ( [0] => 2 [1] => 4 [2] => 6 [3] => 8 [4] => 10 )
```

Código completo: [listing-33.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-33.php)


Con `array_map` es mucho más conciso. Como devolución de llamada podemos pasar el **nombre de una de nuestras funciones** (como una cadena). Creemos una función que duplique un valor; la llamamos `doubleVal` para no superponerse con `doubleval()`, que es una función nativa de PHP:

```php
function doubleVal($val)
{
    return $val * 2;
}

$double = array_map('doubleVal', $numbers);
print_r($double);
// Array ( [0] => 2 [1] => 4 [2] => 6 [3] => 8 [4] => 10 )
```

Código completo: [listing-34.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-34.php)


`array_map` toma cada elemento de `$numbers`, lo pasa a `doubleVal`, recopila los valores devueltos en una nueva array y nos lo entrega. Como devuelve una array, capturamos el resultado en una variable.

### Devoluciones de llamada, cierres y funciones nativas

El primer argumento de `array_map` puede ser cualquier *invocable*. Además del nombre de una de nuestras funciones, podemos pasar el nombre de una **función nativa** de PHP. Por ejemplo `floor()`, que trunca un número decimal a su entero inferior:

```php
$numbers = [6.4, 3.2, 5.7];
$truncados = array_map('floor', $numbers);
print_r($truncados);
// Array ( [0] => 6 [1] => 3 [2] => 5 )
```

Código completo: [listing-35.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-35.php)


Pero a menudo sólo necesitamos la función una vez, para esa única operación: en estos casos es inútil declararla por separado. Podemos pasarlo **en línea** como una función anónima:

```php
$double = array_map(function ($val) {
    return $val * 2;
}, $numbers);
```

Código completo: [listing-36.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-36.php)


La función anónima recibe el valor de cada elemento y devuelve el resultado deseado. Es la forma idiomática cuando la lógica es específica de esa llamada y no se reutilizará en ningún otro lugar. La regla general que uso: si la función sólo es necesaria allí, escríbala de forma anónima en línea; Si planeas reutilizarlo en varios lugares, declaralo como una función real con un nombre, para que sea accesible en todas partes. Y si la lógica es muy corta (sólo una línea), hay una forma aún más compacta, que vemos ahora.

## Las funciones de flecha (PHP 7.4)

PHP 7.4 introdujo **funciones de flecha**, una sintaxis abreviada para funciones anónimas que devuelven el resultado de una sola expresión. Son muy convenientes precisamente en casos como `array_map`, donde un parámetro es una función que debe transformar un valor.

### La sintaxis con fn

En lugar de la palabra `function` escribimos **`fn`**, seguido de los parámetros entre paréntesis, la **flecha** `=>` e inmediatamente de la expresión a devolver. No hay llaves y **no necesitas** la palabra `return`: el valor después de la flecha es lo que se devuelve.

```php
$double = array_map(fn($val) => $val * 2, $numbers);
```

Código completo: [listing-37.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-37.php)


Esta línea hace exactamente lo mismo que la función anónima del párrafo anterior, pero de una forma mucho más compacta. Veámoslo en una array asociativa, para poner todos los valores en mayúsculas con `strtoupper()` manteniendo las claves:

```php
<?php

$data = ['name' => 'juan', 'surname' => 'perez', 'city' => 'madrid'];

$result = array_map(fn($val) => strtoupper($val), $data);
print_r($result);
// Array ( [name] => JUAN [surname] => PEREZ [city] => MADRID )
```

Código completo: [listing-38.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-38.php)


Las funciones de flecha deben estar **todas en una línea**: no podemos abrir las llaves y ajustarlas como en JavaScript. Si necesitamos más lógica que una sola expresión, debemos volver a la clásica función anónima.

### Herencia de alcance

Existe una diferencia importante en comparación con las funciones anónimas tradicionales. Una función anónima, como cualquier función, crea su propio entorno y **no ve** variables externas. Para usar uno dentro de un cierre clásico debemos importarlo explícitamente con la palabra clave **`use`**:

```php
$prefix = 'Mr. ';

$result = array_map(function ($val) use ($prefix) {
    return $prefix . strtoupper($val);
}, $data);
```

Código completo: [listing-39.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-39.php)


Sin `use ($prefix)`, la variable `$prefix` no sería visible dentro de la función (podríamos enumerar varias variables separadas por comas). Las **funciones de flecha**, por otro lado, **heredan automáticamente** las variables del entorno en el que están definidas: no se necesita `use`.

```php
$prefix = 'Mr. ';

$result = array_map(fn($val) => $prefix . strtoupper($val), $data);
```

Código completo: [listing-40.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-40.php)


La función de flecha ve `$prefix` sin tener que importarla: hereda todo el contexto en el que se ejecuta. Es una de sus ventajas más populares, además de la brevedad.

Resumiendo la escala de elección: para una transformación de una sola fila, utilice una función de flecha; si necesita algo de lógica multilínea, una función anónima con `use` cuando sea necesario; Si la función es compleja o reutilizable, extráigala en una función con nombre y pase el nombre como una devolución de llamada; el código será más limpio.

## Las funciones variadas

**funciones variables** (o *funciones con parámetros variables*) son funciones que aceptan un **número variable de argumentos**. Nos permiten escribir funciones más flexibles, que se adaptan a la cantidad de argumentos que recibimos.

### El parámetro de descanso

La forma moderna es el **parámetro resto**: pones **tres puntos** (`...`) delante del nombre del parámetro y automáticamente obtenemos una array con todos los argumentos pasados. Escribamos una función que sume cualquier número de valores:

```php
<?php

declare(strict_types=1);

function sum(...$values)
{
    $suma = 0;

    foreach ($values as $val) {
        $suma += $val;
    }

    return $suma;
}

echo sum(1, 2, 3);       // 6
echo sum(1, 2, 3, 4, 5); // 15
```

Código completo: [listing-41.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-41.php)


Dentro de la función, `$values` es una array normal que contiene todos los argumentos. Antes de introducir el parámetro rest, se obtuvo el mismo resultado con la función **`func_get_args()`**, que devuelve el array de argumentos recibidos incluso sin declarar ningún parámetro:

```php
function sumOld()
{
    $suma = 0;

    foreach (func_get_args() as $val) {
        $suma += $val;
    }

    return $suma;
}
```

Código completo: [listing-42.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-42.php)


Es el método "antiguo", que muestro sólo para completar: hoy el parámetro rest es más claro y explícito, por lo que ya no hay ninguna razón para usar `func_get_args()`.

### Escriba y combine parámetros

Podemos declarar el **tipo** de los argumentos recopilados colocándolo *antes* de los tres puntos:

```php
function sum(float ...$values): float
{
    // ...
}
```

Código completo: [listing-43.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-43.php)


Con `declare(strict_types=1)` activo, pasar una cadena donde necesita un `float` genera un error; en cambio, se acepta un `int` porque es convertible a `float` sin pérdida.

El parámetro rest puede coexistir con **parámetros posicionales** al principio: los primeros argumentos terminan en los parámetros "normales", todos los demás son capturados por el parámetro variadic. El parámetro rest, sin embargo, debe ser **el último**. Escribamos una función que una varias cadenas con un separador:

```php
function stringJoin(string $separator, string ...$parts): string
{
    return implode($separator, $parts);
}

echo stringJoin('-', '1', '2', '3', '4'); // 1-2-3-4
echo stringJoin('-', 'a', 'b');            // a-b
```

Código completo: [listing-44.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-44.php)


El primer argumento (`$separator`) es obligatorio; todos los demás se recopilan en `$parts` y se pasan a `implode()`, la función nativa que une los elementos de una array en una cadena. Tenga en cuenta que PHP 8 permite la **coma final** también en la lista de parámetros y argumentos: es conveniente porque agregar un elemento final no requiere tocar la línea anterior.

### Un ejemplo práctico: una calculadora

Juntemos lo que hemos visto construyendo una pequeña calculadora: el primer parámetro es la operación a realizar, los restantes son los operandos.

```php
<?php

declare(strict_types=1);

function calc(string $operation, int ...$values): float
{
    $result = $values[0];
    $total = count($values);

    for ($i = 1; $i < $total; $i++) {
        switch ($operation) {
            case '+':
                $result += $values[$i];
                break;
            case '-':
                $result -= $values[$i];
                break;
            case '*':
                $result *= $values[$i];
                break;
            case '/':
                if ($values[$i] !== 0) {
                    $result /= $values[$i];
                }
                break;
        }
    }

    return $result;
}

echo calc('*', 3, 4, 5); // 60
echo calc('+', 3, 4, 5); // 12
echo calc('/', 3, 4, 5); // 0.15
```

Código completo: [listing-45.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-45.php)


Algunas opciones notables. Inicializamos `$result` con el primer valor (`$values[0]`) e iniciamos el ciclo `for` desde `1`, porque el primer operando ya es el punto de partida. Calculamos `count($values)` **sólo una vez** fuera del bucle, guardándolo en `$total`, en lugar de llamarlo en cada bucle. Para la división comprobamos que el divisor no sea `0`, saltándonos la operación en ese caso (con la multiplicación no es necesaria: el cero es un operando legítimo). El tipo de retorno es `float` porque una división puede producir un decimal. Usamos los **operadores compuestos** (`+=`, `-=`, `*=`, `/=`) vistos en el Capítulo 8 para hacer el código más conciso.

Lo más importante que hay que recordar: los tres puntos capturan todos los parámetros anteriores; podemos escribirlos y podemos anteponer otros parámetros posicionales: los primeros argumentos terminan en esos parámetros, el resto en la variable.

## Argumentos con nombre (PHP 8)
Con PHP 8 podemos pasar los argumentos de una función indicando su **nombre**, como adelantábamos al hablar de parámetros. Es una de las innovaciones más apreciadas: hace más legibles las llamadas y nos libera de la obligación de recordar el orden exacto de los parámetros.

La sintaxis es: nombre del parámetro (sin `$`), dos puntos, valor. Tomemos una función con tres parámetros:

```php
function suma(int $a, int $b, callable $c)
{
    $c();
    return $a + $b;
}

// pasamos los argumentos por nombre, en el orden que prefiramos:
suma(
    b: 5,
    a: 10,
    c: fn() => print("cálculo en curso\n"),
);
```

Código completo: [listing-46.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-46.php)


El código funciona perfectamente, incluso si pasamos `b` antes de `a`: con argumentos con nombre **no se debe respetar el orden de declaración**. Sin embargo, las reglas relativas a los parámetros obligatorios siguen siendo válidas: si omitimos uno que la función espera, PHP informa que falta (`ArgumentCountError`).

Los argumentos con nombre también funcionan con **funciones nativas**. Por ejemplo `strstr($haystack, $needle)`, que busca una subcadena y devuelve la parte a partir de la primera aparición; sus parámetros se llaman `$haystack` (la cadena para buscar) y `$needle` (qué buscar):

```php
$result = strstr(needle: 'juan', haystack: 'sono juan perez');
var_dump($result); // string(10) "juan perez"
```

Código completo: [listing-47.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-47.php)


También podemos **mezclar** argumentos posicionales y sustantivos, pero con una regla precisa: **un argumento posicional no puede ir después de un argumento sustantivo**. Una vez que comenzamos a usar nombres, todos los argumentos posteriores deben tener el nombre:

```php
suma(10, c: fn() => null, b: 5);      // ok: el argumento posicional es el primero
// suma(a: 10, 5, ...);               // ERROR: posicional después de un argumento con nombre
```

Código completo: [listing-48.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-48.php)


Los argumentos con nombre son muy convenientes cuando una función tiene muchos parámetros y queremos pasar solo algunos de ellos, o cuando queremos dejar claro, de un vistazo, el significado de cada valor en la llamada, un poco como lo hace Python. No son obligatorios, pero usarlos cuando se necesita claridad es un buen hábito: eliminan la clase de errores que surgen al pasar parámetros en el orden incorrecto.

## Tipos de unión (PHP 8)

La última innovación en este capítulo, también en PHP 8, son los **tipos de unión**: la posibilidad de especificar **más de un tipo** para un parámetro o para el retorno. Se escriben enumerando los tipos separados por la **barra vertical** `|` (el carácter *tubería*).

Tomemos la suma nuevamente. Si lo declaramos con los parámetros `int` pero también queremos aceptar números decimales, el editor nos dice que pasar `5.5` es un error de tipo. La solución es una unión tipo `int|float`, tanto para los parámetros como para el retorno:

```php
<?php

function suma(int|float $a, int|float $b): int|float
{
    return $a + $b;
}

echo suma(5.5, 4); // 9.5
```

Código completo: [listing-49.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-49.php)


Ahora la función acepta números enteros y decimales indistintamente y puede devolver uno u otro. Podemos combinar cualquiera de los tipos vistos hasta ahora: escalares, `array`, clases, interfaces, `callable`. También existe el tipo especial **`mixed`**, que significa "de cualquier tipo": es el más amplio posible, y usarlo como tipo equivale a no poner ninguna restricción.

`null` también puede ser parte de un tipo de unión:

```php
function suma(int|float $a, int|float $b): int|float|null
{
    // ...
}
```

Código completo: [listing-50.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-50.php)


Sin embargo, cuando la unión es entre **un tipo único y `null`**, la escritura `?tipo` que vimos para los parámetros que aceptan valores NULL es un atajo equivalente: `?float` es exactamente `float|null`. Sin embargo, para unir `null` a varios tipos, debemos usar la forma extendida `float|int|null`.

Hay un tipo que **no puede** aparecer en un tipo de unión: **`void`**. `void` indica la ausencia total de un valor de retorno (la función no devuelve nada), por lo que es incompatible con cualquier otro tipo: si declaramos `void`, debemos eliminar por completo el `return`, y es conceptualmente diferente a devolver `null`.

Los tipos de unión también son válidos para los **métodos** de las clases y, nuevamente desde PHP 8, para la **tipificación de las propiedades**, algo que antes no era posible. Más sobre esto en la Parte VII, pero vale la pena anticiparlo:

```php
class Persona
{
    public string|int $name;
}
```

Código completo: [listing-51.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/es/parte-03/cap-10/listing-51.php)


Un caso interesante es `string|Stringable`: significa que el valor puede ser una cadena o un **objeto** que implementa el método mágico `__toString()` (por lo tanto convertible a una cadena). Veremos los métodos mágicos en la parte de objetos; Por ahora, basta decir que los tipos de unión nos brindan una verificación de tipos mucho más expresiva que antes.

## En resumen
- Una **función** agrupa un bloque de instrucciones bajo un nombre y se declara con `function`, paréntesis y llaves; se invoca escribiendo el nombre seguido de los círculos. El nombre no distingue entre mayúsculas y minúsculas.
- Una función se puede **asignar a una variable** (`$fn = function () { ... };`): a diferencia de la función nombrada, no se puede llamar antes de su definición.
- Los **parámetros** son las variables declaradas en la función; **argumentos** son los valores que pasamos a la llamada. Los parámetros pueden tener un **valor predeterminado**, que debe colocarse al final de la lista.
- Desde PHP 7 podemos declarar el **tipo** de parámetros y devolver (`int`, `float`, `string`, `bool`, `array`, `callable`, clases, `void`); con `declare(strict_types=1)` en la parte superior del archivo PHP verifica los tipos sin conversiones implícitas.
- Se devuelve un valor con **`return`**; para devolver más de uno usamos una **array**, que luego podemos **deestructurar** con `[$a, $b] = ...` o con `list()`.
- Desde PHP 7.1, **`?`** delante del tipo crea un parámetro o devuelve **nullable**; Para que un parámetro también sea omitible, necesita un valor predeterminado.
- Cada función tiene su propio **alcance**: las variables externas no son visibles dentro de ella, a menos que se importen con **`global`** o mediante el superglobal **`$GLOBALS`** (o se pasen como argumentos, opción preferible).
- **funciones anónimas** (cierre) se asignan a variables y se pasan como `callable` a otras funciones; son la base de las devoluciones de llamada para arrays (`array_map`, `array_filter`, `array_walk`).
- **funciones de flecha** (PHP 7.4) — `fn($x) => expresion` — son una forma compacta de una sola línea que **hereda automáticamente** el alcance externo, sin la necesidad de `use`.
- Las **funciones variables** recopilan un número variable de argumentos con el parámetro resto `...$values` (escribible y combinable con parámetros posicionales), reemplazando el antiguo `func_get_args()`.
- **argumentos con nombre** (PHP 8) le permiten pasar argumentos por nombre (`nombre: valor`) en cualquier orden; un argumento posicional no puede seguir a uno por su nombre.
- **tipos de unión** (PHP 8) — `int|float`, `float|int|null`, `mixed` — declara múltiples tipos permitidos para un parámetro, retorno o propiedad; `void` no puede ser parte de un sindicato.
