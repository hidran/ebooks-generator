# 15. El sistema de archivos, incluye y requiere.

En este capítulo aprenderemos cómo hacer que PHP se comunique con el **sistema de archivos**: crear un archivo y escribir en él, leer su contenido, agregar texto a la cola, verificar si existe un archivo o carpeta, eliminar y copiar archivos, y explorar el contenido de un directorio de tres maneras diferentes. Son operaciones que toda aplicación real debe realizar tarde o temprano: generar un registro, guardar un documento, leer un archivo de configuración, limpiar archivos temporales.

En la segunda parte del capítulo abordamos cuatro construcciones fundamentales del lenguaje: `include`, `require`, `include_once` y `require_once`. Son la herramienta con la que PHP le permite dividir un proyecto en múltiples archivos reutilizables (funciones comunes, plantillas, configuraciones) y son la base de todo lo que construiremos en los proyectos prácticos de los próximos capítulos. Finalmente, veremos una característica poco conocida pero muy valiosa: un archivo incluido puede **devolver un valor**, que podemos capturar en una variable.

## Crea un archivo y escríbelo

Comencemos con un escenario simple: ya tenemos una carpeta `docs`, que se encuentra en el mismo directorio que el script PHP que estamos a punto de ejecutar, y queremos crear un archivo `myfile.txt` dentro de ella. La carpeta en este ejemplo la creamos a mano, pero luego veremos que las carpetas también se pueden crear desde PHP (con la función `mkdir()`, que te invito a buscar en el manual).

Definimos dos variables: `$dir`, que apunta a la carpeta, y `$fileName`, con la ruta completa del archivo a crear:

```php
<?php

$dir = 'docs';
$fileName = $dir . '/myfile.txt';
```

Código completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-01.php)


Hay varias formas de escribir un archivo en PHP. Comencemos con la más clásica y flexible: la función **`fopen()`**.

### Abrir un archivo: modos fopen y apertura

`fopen()` abre un archivo y devuelve un **handle**, es decir, un recurso a través del cual podemos actuar sobre el archivo: escribir en él, leerlo, movernos dentro de él. La función toma dos argumentos: el nombre (ruta) del archivo a abrir y el **modo** de apertura, que le dice a PHP qué pretendemos hacer con él:

```php
$hd = fopen($fileName, 'w');
```

Código completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-02.php)


El modo `'w'` significa *escribir*: abre el archivo solo para escritura. Si el archivo existe, lo **trunca**, es decir, restablece todo lo que hay dentro; si no existe, lo crea. Eso es exactamente lo que necesitamos para crear `myfile.txt` desde cero.

Lo primero que debemos hacer, inmediatamente después, es verificar que la apertura haya sido exitosa, comprobando que el handle sea válido:

```php
if ($hd) {
    fwrite($hd, 'Primera escritura en archivo');
} else {
    echo 'No se puede crear el archivo';
}
```

Código completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-03.php)


Si terminamos en la rama `else`, hay dos causas típicas: la ruta que indicamos no existe, o PHP no tiene **permisos de escritura** en esa carpeta. Este segundo punto merece atención: cuando escribe un script PHP que debe escribirse en el disco, debe asegurarse de que el proceso que ejecuta PHP (en Linux normalmente Apache con PHP como módulo, o PHP-FPM) tenga derechos de escritura en la carpeta de destino. En Windows se aplica el mismo principio: verifique con qué usuario se inició PHP y si ese usuario tiene acceso al archivo.

### Escribir con fwrite y cerrar con fclose

Como has visto en el código anterior, para escribir en el archivo usamos **`fwrite()`**: le pasamos el handle (en nuestro caso `$hd`) y la cadena a escribir. Ejecutemos el script y comprobemos la carpeta `docs`: ha aparecido el archivo `myfile.txt` y al abrirlo encontramos el texto "Primero escribir en el archivo". Logramos crear el archivo y escribir en él.

Cuando hayamos terminado de trabajar en un archivo debemos **cerrarlo** con `fclose()`, pasándole el handle:

```php
fclose($hd);
```

Código completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-04.php)


Recuerde siempre cerrar los archivos: si hay otro script esperando para acceder a ese archivo, cerrarlo lo libera.

### Leer el archivo: fread y tamaño de archivo

Ahora que hemos escrito en el archivo, intentemos leerlo. El turno es el mismo: abrimos el archivo con `fopen()`, pero esta vez en modo `'r'` (*read*), que abre en modo de solo lectura y coloca el cursor al principio del archivo:

```php
$hd = fopen($fileName, 'r');
```

Código completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-05.php)


Una nota: si el archivo era binario (una imagen, un PDF) y queríamos leerlo de forma *binaria segura*, es decir, con la garantía de que los bytes se leen correctamente, deberíamos añadir la letra `b` al modo (`'rb'`). Para un archivo de texto como el nuestro, `'r'` es suficiente.

Para leer usamos la función **`fread()`**: le pasamos el identificador y el número de bytes que queremos leer. Podemos indicar cualquier cantidad, pero si la lectura llega al final del archivo se detiene ahí. Entonces, si queremos leer el archivo **completo**, ¿cómo sabemos cuántos bytes pedir? Nos ayuda la función **`filesize()`**, que recibe la ruta del archivo y devuelve su tamaño exacto en bytes:

```php
$content = fread($hd, filesize($fileName));
echo $content;
```

Código completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-06.php)


Al volver a cargar la página vemos en la pantalla "Primera escritura en el archivo": logramos leer lo que habíamos escrito. Tenga en cuenta que `fread()` trabaja en el identificador, mientras que `filesize()` quiere la ruta del archivo: son dos cosas diferentes.

### Leer en bloques: feof y rebobinar

¿Qué pasa si no queremos (o no podemos) usar `filesize()`? En ese caso tendríamos que leer el archivo pieza por pieza, concatenando los bloques en una variable, hasta finalizar el archivo. Aquí entran en juego dos conceptos importantes.

El primero es el **cursor**: cuando leemos un archivo, PHP mantiene una posición actual que avanza con cada lectura. En nuestro script simplemente leemos el archivo completo, por lo que el cursor está al final. Si lo volviéramos a leer ahora, no obtendríamos nada. La función **`rewind()`**, a la que le pasamos el identificador, devuelve el cursor al principio del archivo, como "rebobinar la cinta":

```php
rewind($hd);
```

Código completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-07.php)


La segunda es la función **`feof()`** (*fin de archivo*): recibe el identificador y nos dice si el cursor ha llegado al final del archivo. Combinándolo con un bucle `while` podemos leer el archivo en bloques:

```php
rewind($hd);

$content = '';
while (!feof($hd)) {
    $content .= fread($hd, 1024); // leemos 1 kilobyte a la vez
}
fclose($hd);

echo $content;
```

Código completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-08.php)


Preste atención a la lógica del bucle: `feof($hd)` devuelve `true` cuando estamos al final del archivo, pero queremos continuar leyendo **hasta** que estemos al final, por lo que la condición se niega con `!`. En cada turno concatenamos el bloque de lectura a `$content` (aquí 1024 bytes, es decir un kilobyte, pero la cantidad es a nuestra elección); Tan pronto como `feof()` devuelve `true`, salimos del bucle y hacemos el `echo` del contenido. El resultado es idéntico a leer "one shot" con `filesize()`: solo cambia la estrategia.

### Agregar contenido a la cola: el modo a

Hasta ahora solo hay una línea en el archivo. Intentemos ahora escribir **al final** del archivo, sin borrar lo que ya está ahí. El procedimiento es siempre el mismo, pero utilizamos otro modo de apertura: `'a'`, que significa *append*. Si el archivo existe, lo abre y coloca la escritura en la cola; si no existe, lo crea:

```php
$hd = fopen($fileName, 'a');
fwrite($hd, 'Segunda escritura en archivo');
fclose($hd);
```

Código completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-09.php)


Sin embargo, al releer el expediente descubrimos un detalle: las dos frases están adjuntas en la misma línea, "Primera escritura en el archivo Segunda escritura en el archivo". Para terminar, necesitamos el carácter de **nueva línea** `"\n"` que, como vimos en el Capítulo 11 sobre cadenas, debe estar entre **comillas dobles**, de lo contrario no se interpreta (en Windows se usa la secuencia `"\r\n"`, nueva línea más *retorno de carro*). El lugar correcto para colocarlo es al final de la primera escritura, concatenándolo a la cadena:

```php
fwrite($hd, 'Primera escritura en archivo' . "\n");
```

Código completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-10.php)


Ahora el resultado es el que queríamos, una línea debajo de la otra:

```text
Primera escritura en archivo
Segunda escritura en archivo
```

Código completo: [listing-11.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-11.txt)


Para resumir el recorrido completo: abrimos el archivo en `'w'` para crearlo y escribir la primera línea, lo cerramos, lo volvimos a abrir en `'a'` para agregarle la segunda línea, lo cerramos nuevamente y finalmente lo abrimos en `'r'` para leerlo.

### Los métodos de apertura en resumen.

Ten siempre a mano el manual de PHP: buscando `fopen` (incluso simplemente "php fopen" en un buscador) encontrarás la lista completa de modos. Los principales:
| Modo | Significado |
|---|---|
| `r` | sólo lectura, cursor al principio del archivo |
| `r+` | lectura y escritura, cursor al principio |
| `w` | solo escritura: truncar el archivo si existe, crearlo si no existe |
| `w+` | como `w`, pero también leyendo |
| `a` | cola de escritura solo (añadir); crear archivo si no existe |
| `a+` | lectura y escritura en cola |
| `b` | bandera para agregar para lectura/escritura binaria segura |

También hay otros modos (`x`, `x+`, `c`…) de los que puedes aprender más en el manual, pero los más utilizados son `r`, `w` y `a`. No es necesario memorizarlas: a medida que utilices estas funciones, se quedarán grabadas en tu mente por sí solas.

## Leer y escribir con una sola función

El bucle `fopen()` → `fwrite()`/`fread()` → `fclose()` es poderoso, pero cuando solo necesitamos leer o escribir un archivo hay una forma mucho más conveniente: PHP ofrece dos funciones que hacen todo en una sola línea.

### file_put_contents y file_get_contents

El primero es **`file_put_contents()`**: "poner este contenido en este archivo". Recibe el nombre del archivo y el contenido para escribir:

```php
<?php

$dir = 'docs';
$fileName = $dir . '/myfile2.txt';

file_put_contents($fileName, 'Primer contenido');
```

Código completo: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-12.php)


Guardemos, volvamos a cargar la página y revisemos la carpeta `docs`: el archivo `myfile2.txt` ha sido creado y contiene el "Primer contenido". Una sola línea en lugar de abrir, escribir y cerrar.

Intentemos ahora escribir un segundo contenido:

```php
file_put_contents($fileName, "\n" . 'Segundo contenido');
```

Código completo: [listing-13.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-13.php)


Comprobamos... y en el archivo sólo aparece "Segundo contenido": el primero ha desaparecido. ¿Por qué? Porque `file_put_contents()` **trunca el archivo**: si no existe lo crea, si existe lo restablece y luego escribe, exactamente como un `fwrite()` en un archivo abierto en modo `'w'`. Mucho cuidado con este comportamiento, porque es fácil perder datos sin darnos cuenta.

¿Cómo podemos preservar el contenido existente? Leerlo antes de escribir. Aquí entran en juego otras dos funciones. El primero es **`file_exists()`**, que comprueba si existe un archivo en el sistema de archivos. El segundo es el gemelo de `file_put_contents()`: **`file_get_contents()`**, que lee todo el contenido de un archivo y lo devuelve como una cadena. Combinémoslos:

```php
$content = '';

if (file_exists($fileName)) {
    $content = file_get_contents($fileName);
}

file_put_contents($fileName, $content . "\n" . 'Segundo contenido');
```

Código completo: [listing-14.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-14.php)


Inicializamos `$content` en una cadena vacía; si el archivo existe, cargamos su contenido en él; finalmente escribimos el contenido antiguo concatenado a la nueva línea. Ahora el script ya no trunca nada: cada vez que recargas la página en el navegador, se agrega una nueva línea de "Segundo contenido" al archivo; cada solicitud al servidor ejecuta el script nuevamente y agrega otra línea. Con estas dos funciones, `file_get_contents()` y `file_put_contents()`, podemos leer y escribir archivos con el mínimo esfuerzo.

### Rutas relativas, rutas absolutas y permisos

Una observación importante sobre las rutas. Cuando pasamos a estas funciones un directorio **relativo** (como nuestro `docs`), PHP lo busca en relación con la carpeta donde se encuentra el archivo `.php` en ejecución. Alternativamente, siempre podemos pasar una **ruta absoluta**. Y lo que se dijo para escribir se aplica: PHP debe tener permiso de **lectura** en ese archivo o directorio; de lo contrario, `file_exists()` devolvería `false` incluso si el archivo está allí, no porque falte el archivo, sino porque PHP no tiene derecho a verlo.

### Verificar una carpeta: is_dir

Además de comprobar si un archivo existe, podemos comprobar si una ruta es un **directorio** con la función **`is_dir()`**:

```php
if (is_dir($dir)) {
    echo 'El directorio existe';
}
```

Código completo: [listing-15.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-15.php)


Al ejecutar el script en nuestra carpeta `docs` obtenemos confirmación. En breve veremos qué tan útil es esta función a la hora de explorar el contenido de una carpeta.

### Eliminar, copiar y otras funciones del sistema de archivos

Otro caso de uso muy frecuente: has creado un archivo temporal -quizás para generar un PDF- y al final del trabajo quieres eliminarlo. Simplemente llame a **`unlink()`** con el nombre del archivo:

```php
unlink($fileName);
```

Código completo: [listing-16.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-16.php)


Recargamos la página y comprobamos: `myfile2.txt` ya no existe, ni en el editor ni en la carpeta `docs`. Preste atención al orden de las instrucciones: si en el mismo script primero escribe con `file_put_contents()` y luego borra con `unlink()`, en cada ejecución el archivo se recrea y se destruye inmediatamente; coloque el `unlink()` donde realmente sea necesario en la lógica de su programa.

El capítulo sobre funciones del sistema de archivos del manual de PHP es muy rico: hay docenas de funciones para leer, escribir y consultar propiedades de archivos. Aquí te he mostrado los que más se utilizan, pero vale la pena mencionar otros:

- **`copy()`** — copia un archivo desde un origen a un destino;
- **`file()`** — lee el archivo completo dentro de una array, una línea por elemento;
- **`fileatime()`** — devuelve la fecha del último acceso al archivo;
- **`touch()`** — cambia la fecha de acceso de un archivo, como el comando de Linux del mismo nombre;
- **`is_writable()`**: prueba si se puede escribir en un archivo.

Te hago un ejercicio: al lado de la carpeta `docs`, crea otra, por ejemplo `copia`; cree un archivo dentro de `docs` y luego cópielo a la nueva carpeta usando `copy()`. Prueba estas funciones de primera mano: sólo practicando retendrás lo aprendido.

## Leer el contenido de una carpeta.

Ahora que sabemos cómo trabajar con archivos individuales, veamos cómo leer el contenido de una **carpeta**: enumerar los archivos que contiene, distinguir archivos de subdirectorios y obtener información sobre cada elemento. PHP nos ofrece tres caminos.

### scandir: la carpeta como una array

La primera, muy cómoda y rápida, disponible desde PHP 5, es la función **`scandir()`**: le pasamos el nombre del directorio a examinar y nos devuelve un array con todas las entradas que contiene:

```php
<?php

$dir = 'docs';

$d = scandir($dir);
var_dump($d);
```

Código completo: [listing-17.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-17.php)


El `var_dump()` muestra algo como esto (en nuestro `docs` hay tres archivos):

```text
array(5) {
  [0]=> string(1) "."
  [1]=> string(2) ".."
  [2]=> string(10) "myfile.txt"
  [3]=> string(9) "test.html"
  [4]=> string(8) "test.txt"
}
```

Código completo: [listing-18.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-18.txt)


Tenga en cuenta las dos primeras entradas: el punto `.` representa la carpeta actual y los dos puntos `..` la carpeta *principal*, es decir, la superior. Están presentes en todos los directorios y, por lo general, deben omitirse cuando repetimos el contenido.

Con un bucle `foreach` podemos desplazarnos por las entradas y, para cada una, comprobar si se trata de un directorio o de un archivo con las funciones `is_dir()` y `is_file()`:

```php
foreach ($d as $entry) {
    // omitimos la carpeta actual y la carpeta padre
    if ($entry == '.' || $entry == '..') {
        continue;
    }

    echo $entry;
    var_dump(is_dir($dir . '/' . $entry));
    var_dump(is_file($dir . '/' . $entry));
    echo '<br>';
}
```

Código completo: [listing-19.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-19.php)


Hay un detalle que inicialmente induce a error: si pasáramos a `is_dir()` y a `is_file()` solo `$entry` (por ejemplo `myfile.txt`), obtendríamos `false` para todo. ¿Por qué? Debido a que estas funciones resuelven la ruta relativa a la carpeta del script en ejecución, no relativa a `docs`: necesitamos concatenar la ruta de la carpeta, `$dir . '/' . $entry`, para darles la ruta correcta. Una vez realizada la corrección, la salida nos dice para cada entrada si es un directorio (`bool(true)`/`bool(false)`) y si es un archivo. Con esta verificación puedes construir una lógica más rica: si la entrada es una carpeta, por ejemplo, puedes llamar recursivamente a la misma función para explorarla; si es un archivo, léelo o procéselo.

### opendir y readdir: el enfoque de manejo

La segunda forma es la más "histórica" y sigue lo que vimos con `fopen()`: la función **`opendir()`** recibe el directorio y devuelve un **handle**, es decir, un recurso:

```php
$handle = opendir($dir);
var_dump($handle);
```

Código completo: [listing-20.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-20.php)


El `var_dump()` confirma que efectivamente es el tipo **recurso**, uno de los tipos de datos que encontramos en el Capítulo 7: PHP nos muestra el identificador del recurso y, al inspeccionarlo, la ruta `docs`. Desde este identificador podemos leer las entradas de la carpeta una a la vez con **`readdir()`**, que devuelve la entrada actual y avanza el cursor, o `false` cuando finalizan las entradas:

```php
while (($entry = readdir($handle)) !== false) {
    echo $entry, '<br>';
}
closedir($handle);
```

Código completo: [listing-21.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-21.php)


El resultado es el mismo que se obtuvo con `scandir()` (punto, dos puntos y los archivos), pero aquí, en lugar de recibir todo en una array, nos desplazamos por la carpeta usando un cursor, exactamente como hicimos con los archivos. Nuevamente, cuando hayamos terminado cerramos el recurso (`closedir()`).

### DirectoryIterator: el enfoque de objetos
La tercera forma es en mi opinión la más conveniente, y es la que siempre uso en mis scripts: la clase **`DirectoryIterator`**, que forma parte de la **SPL** (Standard PHP Library), la biblioteca estándar incluida en PHP desde la versión 5.

`DirectoryIterator` es una **clase**. Aún no hemos estudiado las clases (lo haremos en el Capítulo 26), pero le diré lo mínimo: para crear una instancia de una clase, use el operador `new` seguido del nombre de la clase, pasando los argumentos entre paréntesis. En nuestro caso, el directorio a explorar:

```php
$it = new DirectoryIterator($dir);
```

Código completo: [listing-22.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-22.php)


Un **iterador** es la implementación de un patrón: un objeto que expone métodos para avanzar a la siguiente entrada, devolver la entrada actual, rebobinar hasta el principio y saber si existe un elemento válido. Y aquí está la ventaja: dondequiera que haya un iterador, podemos iterarlo con un simple bucle `foreach`, como una array:

```php
foreach ($it as $entry) {
    echo $entry->getFilename() . ' - ' . $entry->getSize();
    var_dump($entry->isDir());
    var_dump($entry->isFile());
    echo '<br>';
}
```

Código completo: [listing-23.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-23.php)


Cada `$entry` es a su vez un objeto que representa una entrada en la carpeta (un archivo o un subdirectorio) y tiene **ya incorporados** todos los métodos que necesitamos, sin tener que concatenar rutas ni recurrir a funciones nativas como hicimos con `scandir()`. La sintaxis `$entry->metodo()` llama a un método en el objeto; si escribes `$entry->` en tu editor, el autocompletado te muestra todo lo que está disponible:

- **`isDir()`** — ¿la entrada es un directorio?
- **`isFile()`** — ¿la entrada es un archivo?
- **`getFilename()`** — el nombre del archivo;
- **`getBasename()`** — el nombre base, sin la ruta de la carpeta;
- **`getPath()`** — información de ruta;
- **`getSize()`** — el tamaño en bytes;
- y muchos otros: la fecha de creación, el propietario del archivo, permisos...

Ejecutando el ciclo obtenemos, para cada entrada, el nombre, el tamaño y los dos `var_dump()`: el punto `.` es un directorio y no un archivo (`bool(true)` y `bool(false)`), lo mismo para `..`, mientras que `myfile.txt`, `test.html` y `test.txt` son archivos y no directorios. Y al final de cada nombre aparece el tamaño: `test.html - 476`, `test.txt - 1`, `myfile.txt - 52` bytes.

En resumen, para leer una carpeta tenemos tres herramientas: `scandir()`, que nos da un array para desplazarnos con `foreach`; el par `opendir()`/`readdir()`, que funciona con un mango y un cursor; y `DirectoryIterator`, una implementación del patrón iterador que, al recibir una carpeta, devuelve una lista de objetos ya equipados con todos los métodos para consultar el nombre, tipo y tamaño de cada elemento. Si puedes elegir, `DirectoryIterator` es el camino que recomiendo: con una sola instrucción tienes un iterador y cada entrada trae consigo todo lo que necesitas. También en este caso el consejo es siempre el mismo: crear una carpeta de prueba, meter en ella algunos archivos y experimentar con las tres técnicas.

## incluir, requerir, incluir_once y requerir_once

Pasemos ahora a cuatro construcciones PHP fundamentales: **`include`**, **`require`**, **`include_once`** y **`require_once`**. ¿Para qué sirven? Incluir el código de un archivo dentro de otro archivo, para no tener que repetir el mismo código varias veces: si tenemos funciones comunes a todo el proyecto, las escribimos una sola vez y las reutilizamos donde sea necesario.

### Reutilizar código con inclusión

Creemos un archivo `functions.php` con una pequeña función de utilidad dentro, `dd()`, que recibe cualquier variable, la convierte en `var_dump()` y luego detiene la ejecución con `die`:

```php
<?php

function dd($data)
{
    var_dump($data);
    die;
}
```

Código completo: [listing-24.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-24.php)


Ahora supongamos que queremos usar esta función en otro archivo, `index.php`, donde tenemos una array de datos:

```php
<?php

$data = [1, 2, 3];

dd($data);
```

Código completo: [listing-25.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-25.php)


No tendría sentido copiar la función en `index.php`. Pero si ejecutamos el script tal cual desde la línea de comando…

```bash
php index.php
```

Código completo: [listing-26.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-26.sh)


… recibimos un error:

```text
PHP Fatal error:  Uncaught Error: Call to undefined function dd()
```

Código completo: [listing-27.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-27.txt)


PHP no conoce `dd()`: la función vive en otro archivo. Aquí es donde entra `include`. Antes de llamar a la función, incluimos el archivo que la define:

```php
<?php

include 'functions.php';

$data = [1, 2, 3];

dd($data);
```

Código completo: [listing-28.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-28.php)


Si el archivo estuviera ubicado en otra carpeta, tendríamos que indicar la ruta completa. La forma correcta de imaginar a `include` es esta: es como si PHP tomara el código de `functions.php` y lo **copiara y pegara** en el punto exacto donde aparece la declaración. Reiniciamos desde la terminal: ahora la función existe, se ejecuta y vemos el `var_dump()` del array.

### include_once: incluir una vez

¿Qué pasa si incluimos el mismo archivo **dos veces**? Imaginemos un archivo largo, con muchas líneas: no nos damos cuenta de que el `include` ya está ahí y lo reescribimos:

```php
include 'functions.php';
include 'functions.php'; // por error, más adelante en el archivo
```

Código completo: [listing-29.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-29.php)


Intente imaginar el resultado antes de seguir leyendo. Si pensabas que habría error porque la función ya está definida, pensaste bien:

```text
PHP Fatal error:  Cannot redeclare dd() (previously declared in functions.php:5)
```

Código completo: [listing-30.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-30.txt)


La lógica de "copiar y pegar" lo explica todo: en la segunda inclusión PHP vuelve a pegar el código y por lo tanto **redeclara** la función `dd()`, que está prohibida. Por este motivo, cuando incluimos archivos que definen funciones (o clases, como veremos más adelante), lo mejor es usar **`include_once`**:

```php
include_once 'functions.php';
include_once 'functions.php'; // sin problema
```

Código completo: [listing-31.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-31.php)


Como su nombre lo indica, "*once*" significa "una vez": si el archivo ya ha sido incluido, PHP no lo vuelve a incluir. Al volver a ejecutar el script no hay ningún error. Es una protección valiosa especialmente en proyectos grandes, donde no podemos saber si otro fragmento de código ya ha incluido el mismo archivo.

### ¿incluir o exigir?

¿Y `require`? La diferencia entre `include` y `require` es cómo reaccionan cuando el archivo a incluir **no existe** (o la ruta es incorrecta). Probémoslo: en lugar de la función `dd()` ponemos una `print_r()` que no detiene la ejecución, y obtenemos un nombre de archivo incorrecto a propósito:

```php
<?php

include 'functions2.php'; // este archivo no existe

print_r($data);
```

Código completo: [listing-32.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-32.php)


Al ejecutar el script, lo primero que nos dice PHP es una **advertencia**:

```text
PHP Warning:  include(functions2.php): Failed to open stream:
No such file or directory
```

Código completo: [listing-33.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-33.txt)


Pero es sólo una advertencia: **el código continúa ejecutándose** y `print_r()` se ejecuta regularmente. (Si, en cambio, después del `include` fallido llamáramos a `dd()`, aún tendríamos el error fatal "Llamada a función no definida", porque la función nunca se cargó).

Ahora reemplacemos `include` con `require`:

```php
require 'functions2.php';

print_r($data); // esta línea nunca se alcanza
```

Código completo: [listing-34.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-34.php)


Con `require` le estamos diciendo a PHP que ese archivo es **obligatorio*: si no está allí, el programa debe detenerse. Y, de hecho, la advertencia va seguida de un **error fatal**:

```text
PHP Fatal error:  Failed opening required 'functions2.php'
```

Código completo: [listing-35.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-35.txt)


La ejecución se detiene allí: las siguientes líneas nunca se alcanzan, porque el script ya falla en la línea `require`.

¿Cuál usar entonces? Tienes que evaluarlo tú mismo, según las especificaciones de tu código. Si el archivo incluido es una parte **esencial** de la aplicación (sin la cual no tiene sentido continuar), use `require`: mejor deténgase ahora. Sin embargo, si se trata de un fragmento de código del que la aplicación puede prescindir (tal vez alguien eliminó el archivo, pero el resto puede continuar ejecutándose), use `include`, para que un archivo faltante no bloquee todo. Y, por supuesto, siempre puedes comprobar primero la existencia del archivo con `file_exists()`, como aprendimos en este mismo capítulo.

También existe **`require_once`**, que combina las dos características: archivo obligatorio (error fatal si falta) e inclusión una sola vez. Si escribimos `require_once 'functions.php'` dos veces, el archivo se incluye una sola vez y no hay problemas:

```php
require_once 'functions.php';
require_once 'functions.php'; // ignorado: ya incluido

dd($data);
```

Código completo: [listing-36.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-36.php)


El sufijo `_once`, por lo tanto, es válido tanto para `include` como para `require`; la diferencia entre las dos familias siempre es la misma: con `include` el código no se detiene si falta el archivo, con `require` sí.

### Una plantilla dentro de un bucle: cuando _once es malo

En este punto podrías decir: entonces siempre usamos las versiones `_once` y no te preocupes. Un momento de atención: para archivos que definen funciones (y clases posteriores) esto está bien, pero hay un caso de uso en el que `_once` está realmente equivocado: las **plantillas** incluidas dentro de un bucle.

Veámoslo con un ejemplo. Creemos un archivo `show_data.php` que debe mostrar una lista de ciudades:

```php
<?php

$cities = ['Sevilla', 'Madrid', 'Barcelona'];

echo '<ul>';
foreach ($cities as $data) {
    include 'li.php';
}
echo '</ul>';
```

Código completo: [listing-37.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-37.php)


Y creamos la plantilla `li.php`: un fragmento reutilizable que imprime un elemento de la lista. Usamos la etiqueta de apertura corta `<?=`, que significa "abre PHP e inmediatamente haz el `echo` de lo que sigue", y asumimos que existe una variable `$data`:

```php
<li class="data"><?= $data ?? '' ?></li>
```

Código completo: [listing-38.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-38.php)


El operador `??` (*fusión nula*, disponible desde PHP 7) actúa como una red de seguridad aquí: si no se pasó `$data`, imprimimos una cadena vacía en lugar de generar un error.

¿Cómo funciona todo? En cada vuelta del `foreach`, la variable `$data` contiene una ciudad y el `include` "pega" la plantilla en ese punto: es como si hubiéramos cerrado PHP, pegado el HTML de la plantilla y reabierto PHP, una vez por cada ciudad. Ejecutemos desde la línea de comando:

```bash
php show_data.php
```

Código completo: [listing-39.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-39.sh)


Y veamos la lista con las tres ciudades. Si prefiere verlo en el navegador, puede iniciar el servidor web PHP integrado en el puerto que elija:

```bash
php -S localhost:3000
```

Código completo: [listing-40.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-40.sh)


y abra `http://localhost:3000/show_data.php`: aquí está nuestra lista renderizada.

Ahora la contraprueba: reemplacemos `include` con `include_once` dentro del bucle. ¿Qué imprimirá? **Solo Roma**: la plantilla se incluye en la primera ronda y luego nunca más, porque `_once` realmente significa "solo una vez". Este es el caso en el que **no podemos** usar `include_once`: queremos reutilizar la plantilla tantas veces como datos haya para mostrar. En las plantillas dentro de un bucle se utiliza `include` (o `require`, si queremos que la ausencia del archivo bloquee todo: la lógica es idéntica, solo cambia la reacción al archivo faltante).

### Construcciones, no funciones

Una última nota de sintaxis. En algún código antiguo puedes encontrar este formulario, entre paréntesis:

```php
include('functions.php');
```

Código completo: [listing-41.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-41.php)


Funciona, pero los soportes son inútiles. `include` y `require` no son funciones: son **construcciones del lenguaje**, como `echo`. Por eso la forma idiomática, la que te recomiendo usar siempre, es sin corchetes:

```php
include 'functions.php';
require 'config.php';
```

Código completo: [listing-42.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-42.php)


### Consejo: no cierres la etiqueta PHP

Si un archivo contiene **solo código PHP**, como el nuestro `functions.php`, no cierre la etiqueta `?>` al final. No es necesario y hay una buena razón para omitirlo: si quedan espacios o líneas en blanco después de `?>`, cuando incluyes ese archivo dentro de una página HTML, esos espacios terminan en la salida y pueden crear problemas que son difíciles de diagnosticar. La regla es simple: archivo PHP puro, sin etiquetas de cierre.

Y una advertencia para el futuro: `include` y `require` "pegan" código, por lo que si incluye dos archivos que definen una función `dd()`, tendrá un conflicto de función con un error fatal. Más adelante, en el Capítulo 30, veremos que se utilizan namespace para evitar estos conflictos; Por ahora, tenga esto en cuenta al organizar sus archivos.

## Devuelve un valor de incluir y requerir

Hay otra característica de `include` y `require` que los hace valiosos: si el archivo incluido **devuelve un valor**, podemos capturarlo en una variable. Hasta ahora los hemos usado para incorporar funciones o imprimir plantillas; sin embargo, a veces necesitas algo diferente: piensa en el archivo incluido como una **fuente de datos**. El caso clásico es un archivo con configuraciones de base de datos, o con datos que queremos tener disponibles en todas las páginas.

### El problema de las variables globals

Creemos un archivo `config.php` y coloquemos algunos datos de configuración dentro de una array:

```php
<?php

$config = [
    'ip'       => '127.0.0.1',
    'password' => 'test',
    'email'    => 'test@mail.test',
    'username' => 'test',
];
```

Código completo: [listing-43.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-43.php)


En el archivo principal hacemos el `require` y verificamos:

```php
<?php

require 'config.php';

var_dump($config);
```

Código completo: [listing-44.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-44.php)


Al cargar la página vemos la array completa: IP, contraseña, correo electrónico, nombre de usuario. Esto funciona porque `require` ha "pegado" el código y, por lo tanto, la variable `$config` también existe aquí. Pero este es exactamente el problema: `$config` se ha convertido en una variable **inyectada en el alcance** del archivo que incluye. Supongamos que, más adelante en el archivo, sin saber que existe esa variable, escribimos:

```php
$config = [];
```

Código completo: [listing-45.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-45.php)


Simplemente sobrescribimos toda la configuración: `var_dump()` ahora muestra una array vacía. En un proyecto grande, este tipo de colisión de variables es una fuente furtiva de errores. ¿Qué hacemos si **no** queremos inyectar variables globals en otros archivos cuando hacemos un `require`?

### regresar dentro del archivo incluido

La solución: en lugar de definir una variable, el archivo de configuración **devuelve** el valor directamente con `return`:

```php
<?php

return [
    'ip'       => '127.0.0.1',
    'password' => 'test',
    'email'    => 'test@mail.test',
    'username' => 'test',
];
```

Código completo: [listing-46.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-46.php)


Podemos devolver cualquier cosa: una array, una cadena, un objeto. Ahora, en el archivo principal, si simplemente hacemos `require 'config.php'` y luego `var_dump($config)`, PHP nos dice que `$config` es *indefinido*: la variable ya no existe y el valor devuelto se ha perdido. El punto clave es que **`require` y `include` son expresiones que devuelven un valor**, y podemos asignar ese valor a una de nuestras variables:

```php
<?php

$config = require 'config.php';

var_dump($config);
```

Código completo: [listing-47.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/es/parte-04/cap-15/listing-47.php)


Recarguemos: hemos capturado el retorno y la array está ahí nuevamente. Tenga en cuenta que el nombre de la variable es completamente gratuito (`$config`, `$conf`, lo que quiera) y también podemos pasar el resultado directamente a una función. La ventaja es la limpieza: quien hace el `require` de `config.php` recibe los datos **sólo si los captura explícitamente**; no hay variables globals que contaminen el alcance del archivo que incluye. Si no captura la devolución, esos datos simplemente no existen en su alcance.

Dos detalles para completar el cuadro:

- **El valor de retorno predeterminado.** Si el archivo incluido no contiene ningún `return`, `include` y `require` devuelve `1` cuando la inclusión se realiza correctamente. Si el archivo no existe, el "valor" es `false`, acompañado - como sabemos - de un aviso con `include` o de un error fatal con `require`.
- **El archivo aún se ejecuta línea por línea.** Si ponemos `echo 'test';` antes de `return` en `config.php`, ese texto se imprime regularmente y luego se devuelve la array: `return` concluye la ejecución del archivo incluido y devuelve su valor.

Todo lo dicho se aplica igualmente a `include`, `require`, y a las variantes `_once`: la elección entre ellas sigue las mismas reglas vistas en el párrafo anterior (archivo obligatorio e inclusión única); la capacidad de devolver un valor es común a todos. Este patrón, un archivo de configuración que devuelve una array, capturado con `$config = require 'config.php'`, lo encontrará en los proyectos prácticos del libro, comenzando con la configuración de la base de datos.

## En resumen
- `fopen()` abre un archivo y devuelve un **identificador**; los modos principales son `r` (leer), `w` (escribir con truncamiento, crear archivo si falta) y `a` (agregar a la cola). Se escribe con `fwrite()`, se lee con `fread()` y siempre termina con `fclose()`.
- `filesize()` da el tamaño de un archivo en bytes; `feof()` indica si el cursor está al final; `rewind()` lo lleva al principio. La nueva línea `"\n"` (en Windows `"\r\n"`) va entre comillas dobles.
- `file_put_contents()` y `file_get_contents()` escriben y leen un archivo en una sola línea; advertencia: `file_put_contents()` **truncar** el archivo existente.
- `file_exists()` comprueba la existencia de un archivo, `is_dir()` si una ruta es un directorio, `unlink()` elimina un archivo, `copy()` lo copia. Las rutas relativas se resuelven en la carpeta del script; PHP debe tener los permisos de lectura/escritura necesarios.
- Para leer una carpeta: `scandir()` (array de entradas, con `.` y `..` para omitir), `opendir()`/`readdir()` (identificador y cursor) y `DirectoryIterator` (SPL), lo más conveniente: cada entrada es un objeto con métodos como `isDir()`, `isFile()`, `getFilename()`, `getSize()`.
- `include` incrustar un archivo como "copiar y pegar"; `require` hace lo mismo pero genera un **error fatal** si falta el archivo (con `include` solo una advertencia y el código continúa). Las variantes `include_once`/`require_once` incluyen el archivo solo una vez: ideal para funciones y clases, debe evitarse para plantillas dentro de un bucle.
- `include` y `require` son **construcciones del lenguaje**, no funciones: se usan sin corchetes. En archivos PHP puros, no cierre la etiqueta `?>`.
- Un archivo incluido puede **devolver un valor** con `return`, capturable con `$config = require 'config.php'`: es la forma limpia de cargar configuraciones sin contaminar el alcance con variables globals. Sin `return`, la inclusión exitosa devuelve `1`.
