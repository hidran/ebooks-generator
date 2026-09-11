# 9. Estructuras de control

Hasta este punto, nuestros scripts se han ejecutado línea por línea, de arriba a abajo, sin desviarse nunca. Los programas reales, sin embargo, deben tomar decisiones y realizar acciones repetidas: mostrar un mensaje sólo si el usuario ha iniciado sesión, enumerar todos los registros devueltos por una consulta, repetir un cálculo hasta que se cumpla una condición. Para eso están las **estructuras de control**, el tema de este capítulo.

Primero veremos las construcciones condicionales: `if`/`elseif`/`else`, `switch` y el moderno `match` introducido por PHP 8, y luego los bucles: `while`, `do-while`, `for` y `foreach`. Son constructos que encontrarás, con una sintaxis casi idéntica, en C, Java, JavaScript y muchos otros lenguajes: aprenderlos bien en PHP significa tener una base sólida para toda la programación. Para probar los ejemplos, todo lo que necesita es un libro de trabajo (por ejemplo `control-structures`) con un archivo `index.php`, servido por el servidor PHP integrado que aprendimos a iniciar en los capítulos anteriores:

```bash
php -S localhost:8000
```

Código completo: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-01.sh)


## Tomar decisiones: if, elseif, else

### La condición más simple

La estructura `if` acepta una **expresión de control** entre paréntesis que debe devolver un valor booleano: si la expresión es `true`, el bloque de código entre llaves se ejecuta; si `false` es válido, se omite.

Aquí vuelve a entrar en juego la regla booleana que estudiamos en el Capítulo 7 y que vale la pena repetir: para PHP son `false` la cadena vacía, el número `0`, la cadena `"0"`, `null` (y algunos valores más); **cualquier otra cosa se convierte a `true`**. Todas las estructuras de control que veremos (`if`, `switch` y las demás) funcionan en una expresión booleana, y si la expresión aún no es booleana, PHP realiza la conversión automáticamente.

Comencemos con una variable `$money` y la verificación más simple posible:

```php
<?php

$money = 30;

if ($money) {
    echo 'Tienes dinero';
}
```

Código completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-02.php)


Al abrir la página en el navegador vemos `Tienes dinero`: `30` no está entre los valores "falsos", por lo que la conversión a booleano produce `true` y se ejecuta `echo`. Dentro de los corchetes podemos poner cualquier expresión que devuelva un valor booleano: una comparación como `$money > 100`, `$money <= 50` y así sucesivamente.

También podemos negar la expresión con el operador `!` visto en el Capítulo 8:

```php
if (!$money) {
    echo 'No tienes dinero';
}
```

Código completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-03.php)


Con `$money = 30` este bloque no se ejecuta: `$money` es `true`, entonces `!$money` es `false`.

### más: la alternativa

Si queremos mostrar un resultado incluso cuando la condición es falsa, agregamos una rama `else`:

```php
if ($money) {
    echo 'Tienes dinero';
} else {
    echo 'No tienes dinero';
}
```

Código completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-04.php)


Con `$money = 30` aparece `Tienes dinero`; si asignamos `$money = 0` aparece `No tienes dinero`. Lo mismo ocurre con cualquier valor que PHP considere falso: la constante `false`, la cadena vacía `''` y los demás vistos arriba. Por el contrario, cualquier valor fuera de esa lista pasa por la rama `if`.

Cómo organizar las dos ramas es una elección de estilo: podemos verificar primero el caso "verdadero" y poner el caso "falso" en `else`, o revertir la condición e intercambiar las ramas. El comportamiento no cambia; Elija la forma que haga que el código sea más legible.

### elseif: múltiples condiciones en cascada

Un solo `if` con un solo `else` a menudo no es suficiente: podemos encadenar múltiples comprobaciones en la misma variable con `elseif`. PHP acepta tanto el formulario unido `elseif` como el formulario separado `else if`: ambos son válidos.

```php
<?php

$money = 30;

if ($money <= 10) {
    echo 'Puedes comprar una pizza';
} elseif ($money > 10 && $money <= 20) {
    echo 'Puedes comprar una pizza y una cerveza';
} elseif ($money > 20 && $money <= 30) {
    echo 'Puedes ir al restaurante';
} else {
    echo 'Puedes llevar a un amigo al restaurante';
}
```

Código completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-05.php)


Las condiciones se evalúan de arriba a abajo y **solo se ejecuta la primera rama** cuya condición es verdadera; el `else` final se activa como opción predeterminada cuando no se cumplen ningunas condiciones. Con `$money = 30` obtenemos `Puedes ir al restaurante` (30 es mayor que 20 y menor o igual a 30); con `10` obtenemos `Puedes comprar una pizza`; con `35` ninguna de las condiciones es verdadera y se activa `else`: `Puedes llevar a un amigo al restaurante`.
Podemos usar tantos `elseif` como queramos, o detenernos en un simple `if`/`else`. Un consejo práctico: cuando hay muchos `elseif` en cascada, normalmente es mejor cambiar a la construcción `switch`, que veremos en breve.

### La sintaxis alternativa para las plantillas.

Hay una segunda sintaxis para `if`, que se usa principalmente cuando mezclamos PHP y HTML en una plantilla y no queremos llenar el marcado con llaves. Se colocan **dos puntos** (`:`) en lugar de la llave de apertura y la construcción termina con `endif;`. Entre una parte y otra podemos cerrar la etiqueta PHP y escribir HTML puro:

```php
<?php $money = 35; ?>

<?php if ($money): ?>
    <h2>Tienes dinero</h2>
<?php else: ?>
    <h2>No tienes dinero</h2>
<?php endif; ?>
```

Código completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-06.php)


Al abrir la página vemos el mensaje dentro de un `<h2>`, exactamente como si hubiésemos hecho `echo '<h2>Tienes dinero</h2>';` estando dentro de PHP. Entonces, ¿por qué utilizar este formulario? La razón es práctica: si el archivo pasa a manos de un diseñador web que no está acostumbrado a PHP, con la sintaxis entre llaves basta con un `echo` eliminado o un punto y coma perdido para romper la página. Sin embargo, con la sintaxis alternativa, HTML sigue siendo HTML: cualquiera puede editar el marcado sin tocar el código PHP. Por eso se encuentra en casi todas las plantillas PHP (también existen formularios correspondientes para bucles, como `endwhile`, `endfor` y `endforeach`).

Dos reglas para recordar. Primero: no debería haber demasiada lógica en una vista; Si terminas con más de un `if` y un `elseif` dentro de una plantilla, esa lógica es mejor en un archivo PHP separado (un controlador), no en la vista. Segundo: **las dos sintaxis no se pueden mezclar**: o usa llaves o dos puntos con `endif;`. Abrir con una llave y cerrar con `endif;` (o viceversa) es un error de sintaxis.

## La construcción del interruptor

Cuando una cadena de `if`/`elseif`/`elseif` siempre compara la misma expresión con diferentes valores, podemos agruparla en un `switch` más legible. El `switch` evalúa la expresión que le pasamos entre paréntesis y la compara con los valores de los distintos `case`: tan pronto como encuentra una coincidencia, comienza a ejecutar las instrucciones a partir de ese momento.

Sin embargo, preste atención a un detalle que sorprende a muchos principiantes: una vez encontrada la coincidencia, el `switch` **continúa ejecutando todas las líneas siguientes**, incluso las del otro `case`, hasta encontrar un `break`. Veámoslo ahora:

```php
<?php

$money = 1;

switch ($money) {
    case 1:
        echo 'Tienes 1 euro';
    case 2:
        echo 'Tienes 2 euros';
}
```

Código completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-07.php)


¿Qué aparecerá en el navegador? La respuesta sería simplemente `Tienes 1 euro`, pero en su lugar aparecen **ambas** cadenas: `Tienes 1 euro` y `Tienes 2 euros`. Es el llamado *fall-through*, y es una fuente clásica de errores en muchas aplicaciones. Tan pronto como `switch` coincide con `1`, hace todo lo que sigue hasta que encuentra un `break`.

### descanso: salir del interruptor

El `break` sale inmediatamente del `switch`. Agreguémoslo al primer `case`:

```php
switch ($money) {
    case 0:
        echo 'No tienes dinero';
    case 1:
        echo 'Tienes 1 euro';
        break;
    case 2:
        echo 'Tienes 2 euros';
}
```

Código completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-08.php)


Con `$money = 1` ahora solo aparece `Tienes 1 euro`: una vez que se encuentra la coincidencia, `echo` se ejecuta, `break` sale y `case 2` nunca se alcanza. Tenga en cuenta que `case 0` no tiene nada que ver con eso: PHP lo examina, no encuentra ninguna coincidencia y continúa. Si en cambio eliminamos el `break` del `case 1`, la ejecución continúa y se imprimen dos cadenas. Un `break` en el último `case` es técnicamente inútil (el `switch` termina de todos modos), pero siempre tenga cuidado **dónde** coloca el `break`: el resultado puede cambiar completamente.

### predeterminado: cuando ningún caso coincide

Como `else` final en una cadena de `if`, el `switch` puede tener una rama `default` que se ejecuta cuando no coincide ningún `case`:

```php
switch ($money) {
    case 0:
        echo 'No tienes dinero';
    case 1:
        echo 'Tienes 1 euro';
        break;
    case 2:
        echo 'Tienes 2 euros';
        break;
    default:
        echo 'Valor no válido';
}
```

Código completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-09.php)


Con `$money = 3` aparece `Valor no válido`: 3 no es igual a 0, ni a 1, ni a 2, entonces pasamos a `default`. Sin embargo, con `$money = 0`, tenga cuidado con las fallas: `break` falta después de `case 0`, por lo que vemos `No tienes dinero` seguido de `Tienes 1 euro` (la ejecución se detiene en `break` de `case 1`). Si queremos que salga inmediatamente con 0, debemos agregar `break` allí también. El `default`, sin embargo, se activa solo en ausencia de coincidencias: la falla de un `case` anterior no nos alcanza si primero encuentra un `break`.

### Agrupar los casos

El fracaso no es sólo un peligro: usado intencionalmente, es la forma idiomática de asignar **el mismo bloque de declaraciones a múltiples valores**. Simplemente escribe un `case` vacío uno encima del otro:

```php
    case 3:
    case 4:
        echo 'Tienes 3 o 4 euros';
        break;
```

Código completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-10.php)


Con `$money = 3` y `$money = 4` aparece `Tienes 3 o 4 euros`: el `case 3` no contiene instrucciones, por lo que la ejecución "cae" en el `case 4` y se detiene en `break`.

Dos notas de estilo. Si encuentra un bloque de código grande dentro de un `case`, es una señal de que la aplicación no está bien diseñada: ese código debe estar en una función, que `case` simplemente llama. Sin embargo, puede encerrar el cuerpo de `case` entre llaves; no es obligatorio, pero ayuda al editor (y a usted) a ver dónde comienza y termina cada rama. Finalmente, después del valor de `case` PHP también acepta el punto y coma en lugar de los dos puntos (`case 1;`), pero es una forma poco utilizada: quédese con los dos puntos, que es la convención en PHP como en otros lenguajes.

### La comparación débil: un obstáculo en el examen

Hay un comportamiento de `switch` que es absolutamente necesario conocer. Probemos:

```php
$money = false;

switch ($money) {
    case 0:
        echo 'No tienes dinero';
        break;
    // ...
    default:
        echo 'Valor no válido';
}
```

Código completo: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-11.php)


¿Qué esperas? Se podría decir `Valor no válido`: `false` no es `0`. Y en su lugar aparece `No tienes dinero`. ¿Por qué? Porque compara `switch` con la **igualdad débil** (`==`), no con la estricta (`===`): cuando tiene que comparar `false` con el entero `0`, PHP implícitamente convierte `false` a un entero, que es `0`, y `0 == 0` es verdadero. Si desea que la comparación se realice en un entero "verdadero", puede convertir explícitamente el valor antes de `switch`, pero siempre tenga en cuenta que si no lo hace, PHP lo hace por usted de acuerdo con sus propias reglas.

Estos "trucos" de PHP deben aprenderse bien: son exactamente el tipo de preguntas que puede encontrar en el examen **Zend Certified Engineer**, la certificación PHP estándar, y también son el tipo de detalle que genera errores furtivos en el código de producción. Con la práctica se volverán naturales, y en el siguiente párrafo veremos la construcción que introdujo PHP 8 para eliminar este problema.

## coincidencia: el moderno cambio de PHP 8

Desde PHP 8 en adelante hay una construcción llamada **`match`** que resuelve ambas debilidades del `switch`: hace la **comparación estricta** (valor *y* tipo, como `===`) y es una **expresión**, es decir, devuelve un valor que podemos asignar a una variable. Un `switch`, por el contrario, no devuelve nada: escribir `$test = switch (...)` es un error de sintaxis y el editor nos lo informa inmediatamente.

### La sintaxis

`match` evalúa la expresión entre paréntesis y la compara con las "claves" de sus ramas, escritas con la misma flecha `=>` que PHP usa para arrays asociativas clave-valor: a la izquierda el valor (o valores) a comparar, a la derecha la expresión a evaluar (y devolver) en caso de coincidencia. A diferencia de `switch`, no se necesita `break`: una vez que se ha encontrado la coincidencia, `match` evalúa esa rama y sale. Las llaves aquí son una parte obligatoria de la sintaxis y las ramas están separadas por comas.

Tomemos el ejemplo de la comparación con `false` y comparemos las dos construcciones:

```php
<?php

$money = false;

// switch: comparación débil
switch ($money) {
    case 0:
        echo 'No tienes dinero (switch)';
        break;
}

// match: comparación estricta
match ($money) {
    1 > 2 => print 'false',
    0     => print 'No tienes dinero',
    1     => print 'Tienes 1 euro',
    2     => print 'Tienes 2 euros',
};
```

Código completo: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-12.php)


El `switch` imprime `No tienes dinero (switch)`: elencos y `false == 0`. `match` en su lugar imprime `false`: la comparación es cercana, por lo tanto `$money` (que es `false`) **no** corresponde al número entero `0`; corresponde en cambio a la primera rama, porque la expresión `1 > 2` es exactamente `false`. Ya en este ejemplo se ven dos cosas: `match` no realiza ninguna conversión y, como "clave" de una rama, podemos usar cualquier expresión, no solo valores literales.

Una curiosidad del ejemplo: en las ramas usamos `print` en lugar de `echo`. La razón es que cada rama de `match` debe ser una **expresión** que produce un valor, y `echo` no lo es; `print` en su lugar se imprime en la pantalla *y* siempre devuelve `1`. De hecho, si capturamos el resultado:

```php
$result = match ($money) {
    0 => print 'No tienes dinero',
    // ...
    default => print 'Ninguno de los valores'
};

var_dump($result); // int(1)
```

Código completo: [listing-13.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-13.php)


`var_dump($result)` muestra `int(1)`: el valor devuelto por `print`. Sin embargo, si queremos que la rama devuelva la cadena sin imprimirla, podríamos usar `print_r($valor, true)` — con `true` como segundo parámetro, `print_r()` no imprime pero **devuelve** la cadena — pero en realidad no hay necesidad de molestarse con ninguna función: simplemente coloque la cadena directamente como el valor de la rama. Es la forma más limpia y utilizada:

```php
$result = match ($money) {
    0      => 'No tienes dinero',
    1      => 'Tienes 1 euro',
    2      => 'Tienes 2 euros',
    3, 4   => 'Tienes 3 o 4 euros',
    default => 'Ninguno de los valores'
};

echo $result;
```

Código completo: [listing-14.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-14.php)


Tenga en cuenta la rama `3, 4`: para asociar múltiples valores con el mismo resultado no necesita el `case` vacío en cascada del `switch`, simplemente enumere los valores separados por comas. Después de la última rama la coma es opcional: puedes omitirla o dejarla (dejarla es conveniente al agregar ramas al final). Y recuerda que `match (...) { ... }` utilizado como instrucción debe cerrarse con punto y coma.

### el valor predeterminado es (casi) obligatorio

Hagamos nuevamente la prueba estricta de comparación de tipos. Si en un `switch` escribimos `case 3:` y pasamos la **cadena** `'3'`, la conversión implícita lo transforma en un número y se activa la correspondencia. Con `match`, la cadena `'3'` y el número entero `3` son valores de diferentes tipos: no coinciden. Y si ninguna rama coincide y no hay `default`, `match` no se queda en silencio como `switch`: arroja un error fatal:

```text
PHP Fatal error:  Uncaught UnhandledMatchError:
Unhandled match case of type string
```

Código completo: [listing-15.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-15.txt)


Entonces: mientras en `switch` el `default` siempre es opcional, en un `match` tienes que poner la rama `default` cada vez que no estés *seguro* de que el valor corresponde a una de las ramas — de lo contrario tienes que manejar la excepción con un bloque `try`/`catch`, que estudiaremos en el Capítulo 32.

### ¿cambiar o combinar?

Resumamos las diferencias:

| | `switch` | `match` |
|---|---|---|
| Devuelve un valor | no | sí (es una expresión) |
| Tipo de comparación | débil (`==`), con reparto implícito | estrecho (`===`), valor y tipo |
| `break` | necesario para evitar caídas | sin uso |
| `default` | opcional | necesario si el valor puede no coincidir (de lo contrario `UnhandledMatchError`) |
| Cuerpo de sucursales | más instrucciones para `case` | sólo una expresión por rama |

La última línea merece una aclaración: en una rama de `match` no puedes poner varias instrucciones separadas por punto y coma; la estructura funciona como una array de pares clave-valor. Si necesita varias acciones en una rama, escriba una función y llámela como valor de la rama: la llamada es una expresión y su resultado se convierte en el valor de retorno.

Mi consejo, desde PHP 8 en adelante: si necesita comparar estrictamente un valor y devolver un resultado (o llamar a una función), use `match`: la sintaxis es mucho más simple y limpia. Sin embargo, si para cada valor necesita realizar varias acciones en secuencia, `switch` sigue siendo conveniente.

## Los bucles while y do- while

Pasemos a los ciclos. La construcción **`while`** se traduce literalmente como "mientras": *mientras* la expresión entre paréntesis es verdadera, PHP ejecuta la siguiente declaración, o el bloque de declaraciones entre llaves. El estado se comprueba **al inicio** de cada vuelta.
El **`do-while`** hace lo mismo, pero verifica la condición **al final**: el bloque se ejecuta al menos una vez, y solo entonces se decide si se repite. Es la única diferencia entre los dos.

### mientras: la condición antes

Comencemos con un bucle que imprime los números del 1 al 10:

```php
<?php

$i = 1;

while ($i <= 10) {
    echo $i . '<br>';
    $i++;
}
```

Código completo: [listing-16.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-16.php)


En el navegador aparecen los números del 1 al 10, uno por línea. Analicemos las piezas. Antes del ciclo inicializamos el contador `$i` a 1. La condición `$i <= 10` se verifica en cada ciclo; dentro del bloque imprimimos el valor y, lo más importante, lo **incrementamos** con el operador `++` visto en el Capítulo 8 (la forma de sufijo está bien aquí, ya que no asignamos el resultado a ninguna variable). Como hay dos instrucciones, el bloque debe estar entre llaves.

¿Qué pasaría sin el aumento? `$i` permanecería en 1 para siempre, siempre menor o igual a 10, y el bucle se ejecutaría **infinitamente**, bloqueando el script. Es el error clásico con `while`: asegúrese siempre de que algo dentro del bucle tarde o temprano haga que la condición se vuelva falsa.

¿Qué pasa si inicializamos `$i = 11`? El navegador no muestra nada: la condición es falsa desde la primera comprobación y el cuerpo del bucle no se ejecuta ni una sola vez.

### hacer-mientras: al menos una ejecución

Reescribamos el mismo ciclo en la variante `do-while`, comenzando desde `$i = 11`:

```php
$i = 11;

do {
    echo $i . '<br>';
    $i++;
} while ($i <= 10);
```

Código completo: [listing-17.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-17.php)


Esta vez el navegador muestra `11`. El bloque `do` se ejecuta inmediatamente: imprime 11, aumenta a 12 y solo entonces verifica la condición: 12 no es menor o igual a 10, por lo que el ciclo no se repite. Si en cambio partimos de `$i = 1`, obtenemos los números del 1 al 10 exactamente como con `while`. La regla a recordar: **`do-while` ejecuta el cuerpo al menos una vez**, `while` nunca puede ejecutarlo.

### Un ejemplo práctico: generar una lista HTML

Usemos `while` para algo más concreto: iterar a través de una array de colores y mostrarla como una lista HTML. No sabemos a priori cuántos elementos contiene la array; podríamos contarlos a ojo, pero no es necesario: la función PHP `count()` nos dice cuántos elementos tiene una array.

```php
<?php
$ar = ['red', 'blue', 'green', 'yellow'];
$total = count($ar);
?>
<!DOCTYPE html>
<html>
<head>
    <title>Bucle while</title>
    <style>
        body {
            background: #ccc;
            color: #000;
            font-size: 24px;
        }
    </style>
</head>
<body>
    <ul>
        <?php
        $i = 0;
        while ($i < $total) {
            echo "<li>{$ar[$i]}</li>";
            $i++;
        }
        ?>
    </ul>
</body>
</html>
```

Código completo: [listing-18.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-18.php)


Escribimos una página HTML completa (tipo de documento, `<head>` con un título (siempre ponga uno) y un mínimo de CSS para que la lista sea legible) y dentro de `<ul>` abrimos PHP para generar las entradas con el bucle. `red`, `blue`, `green`, `yellow` aparecen en una lista en el navegador: generamos HTML dinámicamente desde PHP.

Dos detalles importantes. Primero: el contador comienza en **cero**, porque las arrays en PHP se indexan desde la posición 0. Segundo: la condición usa `<` y no `<=`, porque el último índice válido es `$total - 1` — con cuatro colores, el total es 4 pero las posiciones son 0, 1, 2, 3.

Y aquí también, cuidado con el incremento: mientras escribes este ejemplo es muy fácil olvidar a `$i++` y encontrarte con la página pasando sin cesar. Si esto le sucede, detenga el navegador, agregue el incremento y vuelva a cargar.

Este patrón, un bucle que recorre una estructura y la transforma en HTML, es exactamente lo que usará todo el tiempo en PHP, por ejemplo, para mostrar en pantalla la lista de registros que devuelve una consulta de una tabla de base de datos. Sin embargo, para las arrays pronto veremos construcciones más convenientes.

## El bucle for

El ciclo **`for`** compacta en una sola línea los tres ingredientes que escribimos en el `while`: inicialización, condición e incremento.

```php
for (expresion1; expresion2; expresion3) {
    // cuerpo del ciclo
}
```

Código completo: [listing-19.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-19.php)


- **expresión1** se utiliza para inicializar las variables y se ejecuta solo una vez, al principio;
- **expresión2** se marca al inicio de cada ronda: si es `true` el ciclo continúa, en caso contrario sale;
- **expresión3** se ejecuta al final de cada ronda (normalmente es el incremento del contador).

Ninguno de los tres es obligatorio: se pueden omitir dejando el punto y coma.
Tomemos la array de colores nuevamente: agreguemos un quinto color, `pink`, y rehagamos la lista con `for`. Esta vez para la salida usamos la interpolación entre comillas dobles que estudiamos en el Capítulo 7, con las llaves alrededor del elemento de la array:

```php
<?php

$ar = ['red', 'blue', 'green', 'yellow', 'pink'];

for ($i = 0; $i < count($ar); $i++) {
    echo "<li>{$ar[$i]}</li>";
}
```

Código completo: [listing-20.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-20.php)


Funciona, pero podemos mejorarlo. La segunda expresión se reevalúa **en cada bucle**: tal como está, se llama a `count($ar)` para cada elemento de la array, sin éxito: el número de elementos no cambia durante el bucle. Lo mejor es calcularlo solo una vez. Podemos hacerlo antes del bucle (`$tot = count($ar);`), o aprovechar que en la primera expresión del `for` podemos poner **múltiples inicializaciones separadas por comas**, ejecutadas solo la primera vez:

```php
for ($i = 0, $tot = count($ar); $i < $tot; $i++) {
    echo "<li>{$ar[$i]}</li>";
}
```

Código completo: [listing-21.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-21.php)


El resultado es idéntico, pero `count()` se llama solo una vez.

### romper y continuar

Dentro de un bucle (`for`, `while` o `do-while`) podemos usar dos declaraciones de control de flujo. Los vemos en `for` porque es donde se usan con mayor frecuencia, pero se aplican a todos los ciclos.

**`break`** sale inmediatamente del bucle, como ya se vio para `switch`. Supongamos que queremos mostrar solo los primeros tres colores:

```php
for ($i = 0, $tot = count($ar); $i < $tot; $i++) {
    echo "<li>{$ar[$i]}</li>";

    if ($i == 2) {
        break;
    }
}
```

Código completo: [listing-22.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-22.php)


Los índices comienzan desde cero, por lo que el tercer elemento es `$i == 2`: la página muestra `red`, `blue`, `green` y luego `break` rompe el bucle: `yellow` y `pink` nunca se imprimen. (Podríamos haber logrado el mismo resultado cambiando la condición `for`, pero `break` es la opción correcta cuando la interrupción depende de una verificación de bucle interno).

**`continue`** sin embargo, no sale del bucle: **salta a la siguiente ronda**, ignorando todas las instrucciones que siguen en el bloque actual. Supongamos que no queremos mostrar `pink`:

```php
for ($i = 0, $tot = count($ar); $i < $tot; $i++) {
    if ($ar[$i] == 'pink') {
        continue;
    }

    echo "<li>{$ar[$i]}</li>";
}
```

Código completo: [listing-23.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-23.php)


Cuando el valor actual es `pink`, el `continue` lo lleva directamente a la siguiente ronda (el incremento `$i++` aún se realiza) y el `echo` siguiente no se alcanza: la lista se detiene en `yellow`, sin `pink`.

Una nota de estilo que repetiré a menudo: en los ejemplos **siempre uso llaves**, incluso cuando el bloque contiene solo una declaración y las llaves no serían obligatorias. Es una cuestión de corrección y claridad del código: evita errores cuando agregas una segunda declaración al bloque en el futuro.

## Bucles anidados

Los bucles se pueden **anidar**: un bucle dentro de otro. Supongamos que queremos mostrar nuestra lista de colores tres veces. Envolvemos el `for` existente en un `for` externo con un segundo contador, `$j`:

```php
for ($j = 0; $j < 3; $j++) {
    for ($i = 0, $tot = count($ar); $i < $tot; $i++) {
        echo "$j {$ar[$i]}<br>";
    }
}
```

Código completo: [listing-24.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-24.php)


El bucle interno se repite íntegramente en cada vuelta del externo: en el navegador vemos los cinco colores tres veces, cada uno precedido por el número del bucle externo (0, 1, 2) gracias a la interpolación de `$j` en la cadena.

Para distinguir mejor una ronda de otra, agregamos una línea horizontal después del último elemento de cada lista. El índice del último color (`pink`) es 4 (las posiciones son 0, 1, 2, 3, 4), entonces:

```php
for ($j = 0; $j < 3; $j++) {
    for ($i = 0, $tot = count($ar); $i < $tot; $i++) {
        if ($i == 4) {
            $hr = '<hr>';
        } else {
            $hr = '';
        }

        echo "$j {$ar[$i]}<br>" . $hr;
    }
}
```

Código completo: [listing-25.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-25.php)


Ahora los tres bloques (ronda 0, ronda 1, ronda 2) están separados por una línea horizontal.

### descansar y continuar con más niveles

Aquí hay un detalle que pocas personas conocen: en PHP tanto `break` como `continue` aceptan un **argumento numérico** que indica cuántos niveles de anidamiento salir o qué nivel continuar.

Intentemos detener todo cuando el bucle exterior llegue a la ronda 1, poniendo la prueba **dentro del bucle interior**:

```php
for ($j = 0; $j < 3; $j++) {
    for ($i = 0, $tot = count($ar); $i < $tot; $i++) {
        if ($j == 1) {
            break; // sale solo del ciclo interno!
        }

        echo "$j {$ar[$i]}<br>";
    }
}
```

Código completo: [listing-26.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-26.php)


El resultado no es el que queríamos: vemos los colores de la vuelta 0 y **también los de la vuelta 2**. El simple `break` (equivalente a `break 1`) solo sale del bucle en el que se encuentra: el interno; el bucle exterior continúa y en la ronda 2 la condición `$j == 1` ya no es cierta. Para salir de **ambos** bucles necesitamos escribir:

```php
        if ($j == 1) {
            break 2; // sale del ciclo interno y del externo
        }
```

Código completo: [listing-27.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-27.php)


Ahora solo vemos los colores de la vuelta 0: una vez que llegamos a `$j == 1`, `break 2` cruza dos niveles de constructos — y en el conteo de niveles el `for`, el `while`, el `do-while` y también el `switch` cuenta y la ejecución se reanuda después del bucle externo.

El mismo argumento numérico se aplica a `continue`. Si en lugar de salir solo queremos **saltarnos la vuelta 1** del bucle exterior, mostrando la vuelta 0 y la vuelta 2:

```php
        if ($j == 1) {
            continue 2; // salta a la siguiente vuelta del ciclo EXTERNO
        }
```

Código completo: [listing-28.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-28.php)


`continue 2` abandona la vuelta actual del bucle interno *y* del bucle externo, pasando directamente a `$j = 2`: las listas de las vueltas 0 y 2 aparecen en el navegador, sin la vuelta 1. El número después de `break` o `continue`, por lo tanto, indica cuántos niveles de anidamiento debe atravesar la instrucción; sin número, actúa sólo en el ciclo más interno.

### Un ejemplo práctico: tablas de multiplicar

Cerremos los bucles anidados con un ejemplo clásico: generar las tablas de multiplicar. Usamos un bucle exterior para el multiplicando (de 0 a 10) y un bucle interior para el multiplicador (también podríamos hacer al revés):

```php
<?php

for ($i = 0; $i <= 10; $i++) {
    for ($j = 0; $j <= 10; $j++) {
        echo "$i x $j = " . ($i * $j) . '<br>';
    }
    echo '<hr>';
}
```

Código completo: [listing-29.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-29.php)


Para cada valor de `$i`, el bucle interno itera `$j` de 0 a 10 e imprime multiplicando, multiplicador y resultado; la línea horizontal después de cada bucle interno separa una tabla de multiplicar de la otra. En el navegador vemos la tabla de multiplicar del 0 (todos ceros), la del 1, y así hasta la del 10: `0, 10, 20, 30... 100`. Funciona correctamente.

Como ejercicio, intente mejorar la presentación: muestre las tablas de multiplicar una al lado de la otra usando tablas HTML: una tabla externa con una columna para cada tabla de multiplicar y dentro de cada columna una tabla interna con filas de multiplicación. Agregue algo de CSS para colorear los fondos; esta es una excelente manera de practicar bucles anidados y la generación de HTML.

## El bucle foreach

Nos desplazamos por las arrays con `while` y con `for`, administrando manualmente el contador, `count()` y el incremento. Sin embargo, PHP tiene un bucle diseñado específicamente para esto: **`foreach`**. Es muy conveniente para iterar a través de cualquier array (indexada, asociativa clave-valor o multidimensional) y también funciona en objetos: al iterar un objeto, `foreach` itera a través de sus propiedades públicas como si fueran pares clave-valor (las propiedades protegidas y privadas no son accesibles desde el exterior; más sobre esto en la Parte VII).

### La forma básica

La sintaxis: `foreach`, luego entre paréntesis el array (o la variable que lo contiene), la palabra clave `as` y una variable que recibirá el valor actual en cada turno. Tú eliges el nombre de la variable:

```php
<?php

$ar = ['red', 'blue', 'green', 'yellow', 'pink'];

foreach ($ar as $val) {
    echo "<h1>$val</h1>";
}
```

Código completo: [listing-30.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-30.php)


`red`, `blue`, `green`, `yellow`, `pink` aparecen en el navegador, cada uno en un bonito `<h1>`. Sin contador, sin `count()`, sin incremento: `foreach` desplaza todos los elementos por sí mismo, desde el primero hasta el último.

### Claves y valores

Si también necesitamos **claves**, usamos la forma de flecha `=>`: la misma sintaxis clave-valor que las arrays asociativas:

```php
foreach ($ar as $key => $val) {
    echo "<h1>$key -> $val</h1>";
}
```

Código completo: [listing-31.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-31.php)


Con nuestra array indexada las claves son numéricas: `0 -> red`, `1 -> blue`, y así sucesivamente hasta `4 -> pink`.

Lo bueno es que funciona de manera idéntica con claves de cadena e incluso con arrays "mixtas". Creemos una segunda array en la que los dos primeros colores tengan clave italiana y los demás queden sin ella:

```php
$ar2 = ['rojo' => 'red', 'azul' => 'blue', 'green', 'yellow'];

foreach ($ar2 as $key => $val) {
    echo "<h1>$key -> $val</h1>";
}
```

Código completo: [listing-32.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-32.php)


El resultado muestra `rojo -> red`, `azul -> blue`, `0 -> green`, `1 -> yellow`: para elementos sin una clave explícita, PHP asigna automáticamente claves numéricas a partir de 0, y `foreach` recorre sin problemas las claves numéricas y de cadena en la misma array, lo que no todas las construcciones de iteración de otras Los lenguajes, JavaScript a la cabeza, pueden hacerlo con la misma naturalidad.

### Cambiar array: valor por referencia

Normalmente `$val` es una **copia** del valor actual: modificarlo no afecta la array. Pero si anteponemos el signo `&`, la variable se convierte en una **referencia** al elemento de la array y podemos modificar la array desde dentro del bucle. Por ejemplo, ponemos todos los colores en mayúsculas con la función `strtoupper()`:

```php
foreach ($ar as &$val) {
    $val = strtoupper($val);
}

var_dump($ar);
```

Código completo: [listing-33.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-33.php)


El `var_dump()` confirma que los valores han cambiado **dentro de la array**: `RED`, `BLUE`, `GREEN`, `YELLOW`, `PINK`.

Pero ten cuidado: hay una trampa famosa. Una vez finalizado el ciclo, `$val` **continúa siendo una referencia al último elemento** de la array. Si reutiliza esa variable más adelante en el script:

```php
$val = 'sin valor';

var_dump($ar); // el último elemento ahora es 'sin valor'!
```

Código completo: [listing-34.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-34.php)


...no estás asignando a cualquier variable: estás sobrescribiendo el último elemento de la array; en lugar de `PINK` ahora está `sin valor`. Para evitar el problema, **después de un `foreach` como referencia siempre haga el `unset()` de la variable**:

```php
foreach ($ar as &$val) {
    $val = strtoupper($val);
}
unset($val); // elimina la referencia

$val = 'sin valor'; // ahora es una variable normal
var_dump($ar);          // el array está intacto: PINK sigue ahí
```

Código completo: [listing-35.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-35.php)


Con `unset($val)` la variable ya no hace referencia a la array y cualquier uso posterior ya no puede dañarla. Te lo diré por experiencia: tuve un error exactamente como este: un `foreach` para referencia cerrada sin `unset()`, la misma variable reutilizada más tarde y el valor de la array principal sobrescrito silenciosamente. Ten siempre cuidado.

### Arrays multidimensionales

¿Qué sucede si los elementos de la array son en sí mismos arrays? Construyamos uno:

```php
$ar3 = [
    ['a', 'b', 'c'],
    [1, 2, 3],
];
```

Código completo: [listing-36.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-36.php)


En la posición 0 hay una serie de letras, en la posición 1 una serie de números (recuerde: PHP incrementa automáticamente el contador de claves). Si probamos el simple `foreach`:

```php
foreach ($ar3 as $val) {
    echo "<h1>$val</h1>";
}
```

Código completo: [listing-37.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-37.php)


PHP nos avisa con un aviso: `Array to string conversion`. Derecha: cada `$val` aquí es una array, y no puedes hacer que `echo` sea como si fuera una cadena. La solución es anidar un segundo `foreach` que itera a través de la array interna:

```php
foreach ($ar3 as $val) {
    foreach ($val as $v) {
        echo "<h1>$v</h1>";
    }
}
```

Código completo: [listing-38.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/es/parte-02/cap-09/listing-38.php)


Ahora funciona: el `foreach` externo desplaza el array principal, el interno desplaza el array contenido en cada valor, y en pantalla aparecen `a`, `b`, `c`, `1`, `2`, `3`.

Con esto ya tienes mucha potencia de fuego: PHP es muy fuerte en arrays y, cuando lo usas junto con una base de datos, los bucles serán el pan y la mantequilla, y casi siempre terminarás usando `foreach`. Estúdialo bien y experimenta con tus propios ejemplos.

## En resumen
- **`if`/`elseif`/`else`** ejecutar bloques de código basados ​​en una expresión booleana; PHP convierte automáticamente a booleano según sus reglas (`0`, `''`, `'0'`, `null`, `false` son falsas). `elseif` y `else if` son equivalentes.
- En las plantillas utilizamos la **sintaxis alternativa** con dos puntos y `endif;`, que permite mezclar PHP y HTML sin llaves; las dos sintaxis no se pueden mezclar.
- **`switch`** compara una expresión con múltiples `case` usando igualdad **débil** (`==`, con conversión implícita) y continúa la ejecución (*fall-through*) hasta que encuentra un **`break`**; `default` maneja valores inigualables. Los vacíos `case` en cascada agrupan varios valores en la misma acción.
- **`match`** (desde PHP 8) es una expresión: devuelve un valor, usa comparación **estricta** (`===`), no requiere `break`, acepta múltiples valores separados por comas y arroja `UnhandledMatchError` si ninguna rama coincide y falta `default`. Cada rama contiene solo una expresión: para múltiples acciones, llame a una función.
- **`while`** comprueba la condición al principio (es posible que el cuerpo nunca se ejecute); **`do-while`** lo comprueba al final (el cuerpo se ejecuta al menos una vez). Asegúrese siempre de que algo haga que la condición sea falsa o el bucle será infinito.
- **`for`** reúne inicialización, condición e incremento; la primera expresión acepta múltiples inicializaciones separadas por comas, lo que es conveniente para calcular `count()` solo una vez en lugar de cada ronda.
- **`break`** sale del bucle, **`continue`** salta a la siguiente ronda; con un argumento numérico (`break 2`, `continue 2`) actúa en múltiples niveles de bucles anidados.
- **`foreach`** es el bucle natural para arrays: `foreach ($ar as $val)` para valores, `foreach ($ar as $key => $val)` para claves y valores; con `&$val` modificas la array por referencia, pero recuerda siempre hacer **`unset($val)`** después del ciclo. Para arrays multidimensionales, se anidan varios `foreach`.
