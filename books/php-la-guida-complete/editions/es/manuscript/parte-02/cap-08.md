# 8. Operadores

Después de aprender a declarar variables y reconocer tipos de datos en el Capítulo 7, es hora de hacer que funcionen juntos. Los **operadores** son los símbolos que nos permiten asignar valores, hacer cálculos y - sobre todo - comparar datos entre sí: son los ladrillos con los que construiremos las condiciones y ciclos del Capítulo 9.

En este capítulo veremos los operadores aritméticos y de asignación, el operador exponencial, toda la familia de operadores de comparación (con un enfoque en cómo PHP compara números y cadenas, un comportamiento que cambió significativamente con PHP 8), el operador de nave espacial, la fusión ternaria y nula, hasta la asignación con fusión nula introducida en PHP 7.4. Son temas que parecen sencillos, pero que esconden algunas de las trampas más clásicas de PHP: conocerlas bien evitará errores difíciles de encontrar.

## El operador de asignación

Cuando escribimos:

```php
<?php

$a = 5;
$b = 8;
```

Código completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-01.php)


parece la matemática habitual: estamos asignando el valor `5` a la variable `$a` y el valor `8` a la variable `$b`. (Recuerde, del Capítulo 7, que los nombres de las variables *distinguen entre mayúsculas y minúsculas*: `$a` y `$A` son dos variables diferentes.)

En realidad el **operador de asignación** `=` hace algo más preciso: toma la **expresión** ubicada a su derecha, la evalúa completamente y solo al final asigna el resultado a la variable de la izquierda. Con un valor literal como `5` no hay nada que calcular, pero mira este caso:

```php
$c = $a + $b;
echo $c; // 13
```

Código completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-02.php)


Algunos podrían pensar "asigno `$a` a `$c` y luego agrego `$b`". No: toda la operación de la derecha (`$a + $b`, es decir, `5 + 8`) se realiza primero y luego el resultado `13` se asigna a `$c`. El concepto debe quedar claro, porque es la base de todo lo referente a la **precedencia de operadores** que veremos en breve.

## Operadores aritméticos

Para los operadores matemáticos, la precedencia es la que estudiamos en la escuela. El operador de **multiplicación** es el asterisco `*`, y la multiplicación y la división tienen prioridad sobre la suma y la resta:

```php
$c = $a + $b * 5;
echo $c; // 45
```

Código completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-03.php)


Primero se calcula `$b * 5` (es decir, `8 * 5 = 40`) y luego se agrega `$a`: `40 + 5 = 45`.

Como en matemáticas, podemos cambiar la precedencia con **paréntesis**:

```php
$c = ($a + $b) * 5;
echo $c; // 65
```

Código completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-04.php)


Ahora primero sumamos `$a + $b` (que es `13`) y luego multiplicamos por `5`, obteniendo `65`.

Para la **división** se aplica lo mismo, pero en lugar del asterisco usamos la barra diagonal `/`:

```php
$c = ($a + $b) / 5;
echo $c; // 2.6
```

Código completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-05.php)


Tenga en cuenta que el resultado es un valor decimal (un valor flotante), aunque los operandos sean números enteros.

### El operador de módulo

Luego hay un operador que no se usa en la escuela con este nombre: el **módulo** `%`, que devuelve el **resto** de la división entre dos números enteros. Si escribo `25 / 8` hago una división normal; si en cambio uso el porcentaje pregunto: "¿cuánto es el resto de esta división?"

```php
$d = 25 % 8;
var_dump($d); // int(1)
```

Código completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-06.php)


El resultado es `1`, porque `8 * 3 = 24` y queda exactamente uno.

En resumen, los operadores aritméticos básicos en PHP son:

| Operador | Operación | Ejemplo |
|---|---|---|
| `+` | Adición | `5 + 8` → `13` |
| `-` | Resta | `8 - 5` → `3` |
| `*` | Multiplicación | `8 * 5` → `40` |
| `/` | División | `13 / 5` → `2.6` |
| `%` | Forma (descanso) | `25 % 8` → `1` |
| `**` | Exponenciación | `2 ** 4` → `16` |

En las bibliotecas matemáticas de PHP encontramos muchas otras funciones (conversiones decimales/binarias, cálculos más precisos, etc.), pero estos son los operadores fundamentales.

## El operador exponencial

Antes de la versión 5.6 de PHP, para elevar un número a una determinada potencia había que usar la función `pow()`, pasando la base y el exponente:

```php
$result = pow(2, 6);
echo $result; // 64
```

Código completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-07.php)


Puedes probarlo inmediatamente desde la consola: si tienes PHP instalado, guarda el código en un archivo y ejecútalo con `php index.php` (o el nombre que le diste al archivo).

A partir de PHP 5.6 existe una forma más sencilla y clara: el **operador exponencial** `**`, es decir, dos asteriscos, también presentes en otros lenguajes:

```php
$result = 2 ** 6;
echo $result; // 64
```

Código completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-08.php)


`2 ** 6` significa "dos elevado a la sexta potencia" y funciona exactamente como `pow(2, 6)`. Por supuesto que podemos seguir usando `pow()`, pero con el operador exponencial la sintaxis es más corta y legible.

### Cuidado con la asociatividad

Sin embargo, hay una cosa a tener en cuenta: el orden de evaluación. El operador `**` es **asociativo por la derecha**, a diferencia de la mayoría de los operadores aritméticos que evalúan de izquierda a derecha. ¿Qué crees que se desprende de esta expresión?

```php
$result = 2 ** 3 ** 2;
echo $result; // 512
```

Código completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-09.php)


Si se evaluara de izquierda a derecha sería `(2 ** 3) ** 2`, es decir `8` al cuadrado: `64`. En cambio, con asociatividad correcta, `3 ** 2` se calcula primero (que es `9`) y luego `2 ** 9`, es decir, `512`.

El consejo, a la hora de combinar `**` con otros operadores, es consultar siempre la tabla de precedencia en el manual de PHP o - mucho mejor - indicar explícitamente el orden entre paréntesis: de esta manera evitas problemas y no tienes que recordar de memoria qué operador tiene mayor prioridad.

### La raíz cuadrada

¿Y si quisiéramos la operación inversa, la raíz cuadrada? En este caso no hay un operador, sino una función: `sqrt()` (de *raíz cuadrada*):

```php
echo sqrt(16); // 4
```

Código completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-10.php)


La raíz cuadrada de `16` es `4`, que es lo opuesto a la exponenciación que acabamos de hacer.

## Operadores de comparación

Los **operadores de comparación** nos permiten comparar dos valores: saber si son iguales, diferentes, si uno es mayor o menor que el otro, un poco como estudiamos en matemáticas. El resultado de una comparación es siempre un valor **booleano**: `true` o `false`.

Sin embargo, hay una característica de PHP que siempre se debe tener en cuenta: cuando compara dos valores, primero puede realizar la **transmisión** (conversión de tipo) de los operandos. Y aquí es donde surgen las sorpresas.

### Igual e idéntico

En PHP hay que distinguir entre "iguales" y "estrictamente iguales" (o **idénticos**, como yo los llamo). Mire estas dos variables, donde `$a` es una cadena y `$b` es un número:

```php
$a = '1';
$b = 1;

$c = $a == $b;

var_dump($a); // string(1) "1"
var_dump($b); // int(1)
var_dump($c); // bool(true)
```

Código completo: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-11.php)


Con doble igual a `==` PHP ve que el primer valor es una cadena y el segundo un entero, convierte la cadena `'1'` en el número `1` (como vimos en el Capítulo 7 hablando de conversiones) y luego compara: son iguales, por lo tanto `true`.

Si en cambio queremos verificar que dos valores son iguales **y también del mismo tipo** — es decir, estrictamente iguales — usamos tres signos de igual `===`:

```php
var_dump($a === $b); // bool(false)
```

Código completo: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-12.php)


El resultado es `false`: tienen el mismo valor, pero no el mismo tipo (uno es una cadena, el otro un número entero). Entonces: tres signos iguales cuando queremos verificar el valor **y** tipo, dos signos iguales cuando solo nos interesa el valor.

### El caso de nulo

Un caso en el que la diferencia se ve aún mejor es `null`. Aquí `$a` no tiene ningún valor, mientras que `$b` es cero:

```php
$a = null;
$b = 0;

var_dump($a == $b);  // bool(true)
var_dump($a === $b); // bool(false)
```

Código completo: [listing-13.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-13.php)


¿Recuerdas la tabla de multiplicar del Capítulo 7? Para PHP, cualquier cosa que sea `0`, `null`, la cadena vacía `''`, `'0'` o una array vacía se convierte a `false`; todo lo demás a `true`. Cuando comparamos `null == 0`, PHP hace la conversión y los considera iguales. Pero `null === 0` es `false`: `null` es `null`, y cero es un número entero; no son idénticos, simplemente tienen el mismo valor.

Otras comparaciones interesantes con dobles iguales:

```php
var_dump(null == false); // bool(true)  — el cast los hace iguales
var_dump(null == '');    // bool(true)  — la cadena vacía "vale" null
var_dump(null == '0');   // bool(false) — la cadena '0' NO es igual a null
```

Código completo: [listing-14.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-14.php)


### Por qué es importante: el ejemplo del precio
Siempre que compares dos valores para determinar la igualdad, utiliza los tres símbolos `===` para comprobar también el tipo: evitarás errores furtivos. Porque tal vez cero sea un valor legítimo (por ejemplo, el precio de un producto) y su código lo descarte sin querer. Imagine tener que actualizar el precio de un artículo en un sitio de comercio electrónico:

```php
$price = 0;

if ($price) {
    // aquí ejecutaríamos la query de actualización
    echo 'Precio actualizado';
} else {
    echo 'Precio no actualizado';
}
// Output: Precio no actualizado
```

Código completo: [listing-15.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-15.php)


El `if` (que estudiaremos en profundidad en el Capítulo 9) evalúa la expresión dentro de él como booleana: `$price` es `0`, la conversión da `false` y la consulta de actualización nunca se ejecutará. Un error agradable y bueno, ¡porque cero es un precio válido!

La solución es comprobar explícitamente que el precio es diferente de `null`, con una comparación cercana:

```php
if ($price !== null) {
    echo 'Precio actualizado';
} else {
    echo 'Precio no actualizado';
}
// Output: Precio actualizado
```

Código completo: [listing-16.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-16.php)


Ahora la condición pasa, porque `0` es un valor presente: es diferente de `null` tanto en valor percibido como en tipo. Tenga mucho cuidado con estos casos: si no verifica con comparación estricta, para PHP cero, `null` y la cadena vacía son equivalentes.

### Diferente y no idéntico

Lo contrario de igualdad se expresa con el signo de exclamación. `!=` significa "diferente" (solo en valor, con conversión), mientras que `!==` significa "no idéntico": diferente en valor **o** en tipo. Tomemos `null` y la cadena vacía:

```php
$a = null;
$b = '';

var_dump($a != $b);  // bool(false) — después del cast resultan iguales
var_dump($a !== $b); // bool(true)  — uno es null, el otro es una cadena
```

Código completo: [listing-17.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-17.php)


Con `!=` el resultado es `false`: PHP hace el casting, los ve como iguales, por lo que "no son diferentes". Con `!==` en su lugar es `true`, porque los tipos son diferentes. También existe la forma alternativa `<>` para "diferente", pero yo siempre uso `!=`.

Aquí está la tabla resumen, que también puedes encontrar en el manual de PHP:

| Ejemplo | Nombre | Resultado |
|---|---|---|
| `$a == $b` | Lo mismo | `true` si `$a` es igual a `$b` después de la conversión de tipo |
| `$a === $b` | Idéntico | `true` si son iguales y del mismo tipo |
| `$a != $b` | Diferente | `true` si es diferente después de convertir los tipos |
| `$a <> $b` | Diferente | Me gusta `!=` |
| `$a !== $b` | No idéntico | `true` si es diferente en valor o tipo |
| `$a < $b` | Menor | `true` si `$a` es estrictamente menor que `$b` |
| `$a > $b` | Mayor | `true` si `$a` es estrictamente mayor que `$b` |
| `$a <= $b` | Menor o igual a | `true` si `$a` es menor o igual que `$b` |
| `$a >= $b` | Mayor o igual a | `true` si `$a` es mayor o igual a `$b` |

### Comparar cadenas

¿Y las cuerdas? Cuando los dos operandos son cadenas, la comparación se produce byte a byte, en el valor ordinal de cada byte:

```php
var_dump('a' != 'b'); // bool(true)  — son diferentes
var_dump('a' == 'b'); // bool(false) — no son iguales
var_dump('a' !== 'b'); // bool(true) — mismo tipo, pero valores diferentes
```

Código completo: [listing-18.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-18.php)


Cuando comparamos cadenas con cadenas no hay problemas: incluso doble igual está bien, porque los tipos ya coinciden. El problema, como hemos visto, es cuando se mezclan los tipos: cadena vacía, cero, `null`.

### Mayor, menor y sus amigos

Para `>`, `<`, `>=` y `<=` se aplica lo que ya sabemos de las matemáticas; Estos operadores también siempre devuelven un valor booleano:

```php
$d = 0;
$e = 1;

$f = $d > $e;
var_dump($f);       // bool(false) — cero no es mayor que uno

var_dump($d < $e);  // bool(true)  — cero es menor que uno
var_dump($d <= $e); // bool(true)  — es menor, así que también es "menor o igual"
var_dump(1 <= 1);   // bool(true)  — no es menor, pero es igual
var_dump(2 <= 1);   // bool(false)
var_dump(2 >= 1);   // bool(true)
```

Código completo: [listing-19.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-19.php)


Depende de lo que quieras comprobar: si sólo necesitas que sea "mayor o igual", utiliza `>=`; si quieres que sea estrictamente mayor, simplemente usa `>`.

¿Para qué sirven estos operadores en la práctica? Para construir condiciones sobre los datos ingresados ​​por el usuario o leídos de la base de datos. Un ejemplo clásico:

```php
$age = 16;

if ($age >= 18) {
    echo 'Eres mayor de edad';
} else {
    echo 'Eres menor de edad';
}
// Output: Eres menor de edad
```

Código completo: [listing-20.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-20.php)


Con `$age = 16` el programa de prensa “Eres menor de edad”; si pones `18`, la condición pasa (gracias al "o igual") e imprime "Eres adulto".

Tenga cuidado con un error tipográfico muy común: escribe **primero** el signo mayor/menor y **luego** el signo igual (`>=`, `<=`). Si escribe `=>` PHP no lo interpreta como una comparación (esa secuencia tiene un significado completamente diferente (la usaremos para arrays)) y obtendrá un error.

## Comparando números y cadenas: qué cambia con PHP 8
Hay un comportamiento muy común de PHP que ha cambiado significativamente entre PHP 7 y PHP 8, y tiene que ver con la comparación débil (`==`) entre una cadena y un número. Si necesita migrar código de PHP 7 a PHP 8, este párrafo le concierne de cerca.

Partamos de un caso que no cambia:

```php
var_dump(0 == '0'); // bool(true) — en todas las versiones
```

Código completo: [listing-21.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-21.php)


`'0'` es una **cadena numérica**: contiene un número. `'0.0'` también lo es. Cuando la cadena es numérica, la comparación con un número funciona como se esperaba, antes y después de PHP 8.

La diferencia es *cómo* PHP hace la comparación cuando la cadena **no** es numérica:

- **Antes de PHP 8**: PHP convertía la cadena en un número y luego comparaba los dos números. Una cadena numérica puede tener espacios delante; PHP lo leyó desde el principio, encontró el número y descartó todo lo que había después (cualquier carácter que no fuera un dígito o punto decimal). Y una cadena que no comenzaba con un número se convirtió... a `0`.
- **Desde PHP 8**: si la cadena no es numérica, PHP hace lo contrario: convierte el *número* en una cadena y compara las dos cadenas.

Las consecuencias se pueden ver inmediatamente en esta tabla:

| Comparación | PHP 7.x | PHP 8+ |
|---|---|---|
| `0 == "0"` | `true` | `true` |
| `0 == "0.0"` | `true` | `true` |
| `0 == "foo"` | `true` | `false` |
| `0 == ""` | `true` | `false` |
| `42 == " 42"` | `true` | `true` |
| `42 == "42abc"` | `true` | `false` |

Antes de PHP 8, `0 == "foo"` era `true`: la cadena `"foo"` no comienza con un número, se convirtió a `0` y cero es igual a cero. No puedo decirte cuántos errores tuve que corregir para este problema. Lo mismo ocurrió con la cadena vacía. Y `42 == "42abc"` era `true` porque PHP leyó `42` y descartó el resto; con PHP 8 es `false`. En lugar de `" 42"` con espacios delante permanece `true` en ambas versiones: se permiten espacios (incluso después del número, desde PHP 8) en una cadena numérica.

### Pruebe comparaciones con diferentes versiones de PHP

Para hacer estas pruebas recomiendo un sandbox en línea como **onlinephpfunctions.com**: puedes pegar algo de código, ejecutarlo y elegir con qué versión de PHP probarlo. Comencemos con algo de `var_dump()`, que muestra el resultado de la operación y el tipo que devuelve:

```php
var_dump(4 == 4);    // bool(true)
var_dump(4 == '4');  // bool(true) — string numérico
var_dump(4 == ' 4'); // bool(true) — y sin warning por el espacio
```

Código completo: [listing-22.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-22.php)


Por supuesto, en el mundo real estos valores vienen en variables. Imaginemos tener un id esperado y un valor que retorna de una llamada o de un formulario: todo lo que llega de la web llega **en forma de cadena** (esto lo veremos bien en el Capítulo 13 sobre superglobals):

```php
$id = 4;       // el valor que esperamos: un integer
$result = '4'; // el valor recibido desde un form: siempre un string

var_dump($result);         // string(1) "4"
var_dump($id == $result);  // bool(true)
var_dump($id === $result); // bool(false) — tipos diferentes
```

Código completo: [listing-23.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-23.php)


Si queremos una comparación estrictamente igual, podemos convertir primero a un número entero, ya que esperamos un número entero:

```php
var_dump($id === (int) $result); // bool(true)
```

Código completo: [listing-24.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-24.php)


Llegados a este punto quizás me digas: "¿pero para qué complicarnos la vida? Siempre hago el casting y lo comparo con `===`, y ya está". El problema es que en PHP hay construcciones y funciones integradas que hacen la comparación débil *por sí solas*, sin que usted tenga otra opción. Un ejemplo es el `switch`, que compara su `case` con la igualdad débil `==`, mientras que el más reciente `match` usa la comparación estricta `===` (veremos ambas en el Capítulo 9). Con `switch`, si el valor es `'4'` como cadena o `4` como número es lo mismo: la conversión ocurre implícitamente.

### El caso de in_array()

Otro caso es la función `in_array()`, que comprueba si existe un valor dentro de una array (la encontraremos nuevamente en el Capítulo 12; mientras tanto, puedes consultarla en el manual de PHP). Acepta tres parámetros: qué buscar, dónde buscarlo y si la comparación debe ser cercana o no (el tercer parámetro es `false` por defecto, por lo que la comparación es débil).

```php
$data = [4, 5, 'php'];

var_dump(in_array('5a', $data)); // PHP 7: bool(true) — PHP 8: bool(false)
var_dump(in_array(' 5', $data)); // bool(true) en ambas (solo espacios)
var_dump(in_array(0, $data));    // PHP 7: bool(true)! — PHP 8: bool(false)
```

Código completo: [listing-25.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-25.php)


El primer caso: en PHP 7 la cadena `'5a'` se convirtió en un número; encontró el `5`, descartó el resto y luego lo "encontró" en la array; en PHP 8 no. Solo con espacios (`' 5'`) funciona en ambas versiones.
Pero el caso realmente complicado es el tercero: buscamos el `0` en una array que, como puedes ver, **no contiene ningún cero**. ¡En PHP 7 el resultado fue `true`! ¿Por qué? PHP comparó `0` con `4`: diferente. Entonces `0` con `5`: diferente. Luego `0` con la cadena `'php'`: y una cadena no numérica, convertida en un número, da `0`. Entonces `0 == 0` → encontrado. Un error terrible, porque PHP nos dijo que sí mientras que el cero en la array no está ahí. A partir de PHP 8 esto ya no sucede.

En cualquier caso, con `in_array()` podemos (y generalmente debemos) pasar el tercer parámetro a `true` para forzar la comparación estricta, que da el resultado correcto en todas las versiones:

```php
var_dump(in_array('5a', $data, true)); // bool(false) en todas partes
var_dump(in_array(0, $data, true));    // bool(false) en todas partes
```

Código completo: [listing-26.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-26.php)


Moraleja: si está migrando código de PHP 7 a PHP 8, verifique todos los lugares donde compara números y cadenas con `==`, `switch` o funciones como `in_array()`. Cuando pueda, emita explícitamente y compare detalladamente; donde no puedas, ten en cuenta esta tabla.

## El operador de la nave espacial

Pasemos ahora a los operadores que ciertamente no hemos estudiado en álgebra elemental, pero que existen en PHP como en otros lenguajes. El primero, introducido con PHP 7, es el operador **nave espacial** `<=>` — la "nave espacial", debido a su forma.

¿Qué él ha hecho? Compara "menor que, igual y mayor" de un solo golpe: tres comparaciones en una. Devoluciones:

- `-1` si el primer operando es **menor** que el segundo;
- `0` si son **iguales**;
- `1` si el primero es **mayor** que el segundo.

Comprobemos:

```php
$g = 0;
$h = 1;

$i = $g <=> $h;
var_dump($i); // int(-1) — el primer valor es menor que el segundo
```

Código completo: [listing-27.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-27.php)


(Si su editor informa `<=>` como un error, verifique que linting esté configurado en PHP 7 o superior: el código es perfectamente válido).

Si los dos valores son iguales obtenemos cero, y si el primero es mayor obtenemos uno:

```php
var_dump(1 <=> 1); // int(0) — son iguales
var_dump(2 <=> 1); // int(1) — el primero es mayor
```

Código completo: [listing-28.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-28.php)


Funciona tanto con variables como con literales. ¿Y para qué sirve? Con una sola expresión obtengo un valor que me dice *qué relación hay* entre los dos operandos, y luego puedo ordenar los tres casos con un `if`/`elseif`/`else` (o con un `switch`, que estudiaremos en el Capítulo 9). Anticipo la estructura porque es muy sencilla de entender:

```php
$g = 2;
$h = 1;

$i = $g <=> $h;

if ($i === 0) {
    echo 'g y h son iguales';
} elseif ($i === -1) {
    echo 'g es menor que h';
} else {
    echo 'g es mayor que h';
}
// Output: g es mayor que h
```

Código completo: [listing-29.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-29.php)


Con `$g = 1` imprimiría "g y h son iguales", con `$g = 0` imprimiría "g es menor que h". Es un operador muy práctico: con una sola condición tengo todo lo que necesito.

## El operador ternario

Otro operador que debes conocer es el **ternario**, que se llama así porque funciona con tres partes:

```text
condicion ? valor1 : valor2
```

Código completo: [listing-30.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-30.txt)


Si la condición es verdadera (`true`), la expresión devuelve `valor1`; de lo contrario devuelve `valor2`. Veámoslo en la práctica:

```php
$val1 = 1;
$val2 = 1;

$ternary = ($val1 === $val2) ? 'son iguales' : 'son diferentes';
echo $ternary; // son iguales
```

Código completo: [listing-31.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-31.php)


Dos consejos de escritura. Primero: cuando la condición es una expresión (como aquí), enciérrela siempre entre corchetes; si es un valor único, también puede omitirlos, pero con corchetes evita cualquier problema de precedencia entre operadores PHP. Segundo: por costumbre y por corrección, uso comillas simples para cadenas que no contienen variables, como les mostré en el Capítulo 6.

El ternario es el equivalente compacto de `if`/`else`:

```php
if ($val1 === $val2) {
    echo 'son iguales';
} else {
    echo 'son diferentes';
}
```

Código completo: [listing-32.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-32.php)


¿Cuál de los dos es mejor? Depende. Para una expresión simple como esta recomiendo el ternario: más corto, más inmediato. Sin embargo, si la lógica se vuelve complicada, un `if`/`else` explícito es mejor, tal vez apoyando el resultado en una variable: es un poco más claro de leer. No es una cuestión de velocidad, sino de legibilidad.

Tenga en cuenta que utilicé tres signos iguales en el ejemplo porque también quiero comprobar el tipo. Intente cambiar los valores: con `$val2 = 20` obtenemos "son diferentes"; con `$val2 = '1'` (cadena) y la comparación cercana `===` obtenemos "son diferentes", pero si cambiamos a doble igual `==` vuelve "son iguales"; sigue siendo la misma historia que el elenco que vimos arriba.

## El operador coalescente nulo
Con PHP 7 también llegó el operador **nucleante** `??`, dos signos de interrogación. Traducido libremente significa: "dame el primero de todos los valores que enumero que no sea `null`". Esto es similar al ternario, pero en lugar de evaluar una condición verdadero/falso, descarta `null`.

Podemos usar valores literales:

```php
$result = null ?? 2 ?? 3;
var_dump($result); // int(2)
```

Código completo: [listing-33.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-33.php)


El primer valor es `null`, por lo que se descarta; el segundo es `2`, que no es `null`: él es el resultado. Si el segundo también fuera `null`, obtendríamos `3`:

```php
$result = null ?? null ?? 3;
var_dump($result); // int(3)
```

Código completo: [listing-34.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-34.php)


Y, por supuesto, también funciona con variables; no importa si son variables o literales:

```php
$val1 = null;
$val2 = 10;

$result = $val1 ?? $val2;
var_dump($result); // int(10)
```

Código completo: [listing-35.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-35.php)


Es el operador perfecto para asignar valores predeterminados, como veremos pronto.

## Asignación con fusión nula (PHP 7.4)

Echemos un vistazo a la fusión nula nuevamente con un caso práctico. Imagine leer el apellido de un usuario de la base de datos y no saber si la columna `last_name` contiene un valor o `null`. Queremos asignar un valor predeterminado en ese caso:

```php
$lastName = null; // simulamos la columna leída desde la base de datos

$lastName = $lastName ?? 'N/A';
echo $lastName; // N/A
```

Código completo: [listing-36.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-36.php)


Estamos diciendo: "`$lastName` será el mismo valor que ya tiene, pero si ese valor es `null`, entonces use `'N/A'`". Funciona, pero hay una repetición: la variable aparece dos veces.

Desde PHP 7.4 hay una forma más corta: el **operador de asignación con fusión nula** `??=`:

```php
$lastName ??= 'N/A';
echo $lastName; // N/A
```

Código completo: [listing-37.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/es/parte-02/cap-08/listing-37.php)


El significado es idéntico: "mantener el valor que ya está en `$lastName`; pero si es `null`, asignar el valor predeterminado". Si la variable ya tiene valor no pasa nada y queda como está; de lo contrario recibe el valor predeterminado.

Este operador es muy conveniente para limpiar valores: cada vez que tememos que un valor pueda ser `null` (una columna de base de datos, un parámetro opcional), le damos un valor predeterminado con una sola línea.

## En resumen

- El operador de asignación `=` **primero** evalúa la expresión completa de la derecha y **luego** asigna el resultado a la variable de la izquierda.
- Los operadores aritméticos son `+`, `-`, `*`, `/`, el módulo `%` (resto de la división) y el exponencial `**`; la multiplicación y la división tienen prioridad sobre la suma y la resta, y los paréntesis cambian el orden de evaluación.
- `**` (desde PHP 5.6, como alternativa a `pow()`) es asociativo derecho: `2 ** 3 ** 2` hace `512`, no `64`. En caso de duda, utilice paréntesis. Para la raíz cuadrada existe la función `sqrt()`.
- `==` compara valores únicamente (con conversión de tipos automática), `===` compara valores **y** tipos; `!=` significa diferente, `!==` no es idéntico. Prefiera siempre comparaciones ajustadas: para PHP `0`, `null` y `''` en comparación débil son equivalentes, y un cero legítimo (¡un precio!) puede hacer que una condición falle.
- Desde PHP 8, la débil comparación entre números y cadenas **no numéricas** ha cambiado: `0 == "foo"` y `0 == ""` ahora son `false` (anteriormente eran `true`), y `42 == "42abc"` es `false`. Tenga cuidado durante la migración, también con `switch` (comparación débil) y funciones como `in_array()` (use el tercer parámetro `true` para una comparación estricta).
- La nave espacial `<=>` (PHP 7) hace tres comparaciones en una: devuelve `-1` si el primer operando es menor, `0` si son iguales, `1` si es mayor.
- El ternario `condicion ? valor1 : valor2` es la forma compacta de `if`/`else`: utilícelo para expresiones simples y ponga la condición entre paréntesis.
- La fusión nula `??` devuelve el primer valor no `null` de la lista; desde PHP 7.4, `$var ??= 'default'` asigna el valor predeterminado solo si la variable es `null`.
Con estos operadores estamos listos para las estructuras de control del próximo capítulo: `if`, `elseif`, `else`, `switch`, `match` y los bucles. Antes de continuar, tómate unos minutos para experimentar en tu editor: compara `null` con `0`, la cadena vacía con `null`, un número con una cadena, y observa los resultados que obtienes.
