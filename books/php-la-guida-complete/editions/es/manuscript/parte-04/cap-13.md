# 13. Superglobals

Con este capítulo llegamos al corazón de PHP como lenguaje para la web. Hasta este punto hemos escrito scripts que procesan datos que nosotros mismos ponemos en el código; Ahora veamos cómo PHP recibe los datos que llegan **desde fuera**: los parámetros de una solicitud, los valores de un formulario, información del servidor, archivos cargados por un usuario, datos de la sesión. Todo esto nos llega a través de un grupo especial de arrays que PHP completa automáticamente: los **superglobals**.

Se llaman así porque son variables "súper globals": son accesibles **en cualquier punto** del script (dentro de una función, dentro de un método, en cualquier ámbito) sin necesidad de declararlas con `global` y sin pasarlas como argumentos. PHP los crea y los completa incluso antes de que nuestro código comience a ejecutarse. Los reconoces inmediatamente porque todos tienen un nombre que comienza con `$_` (con la única excepción histórica de `$GLOBALS`): `$GLOBALS`, `$_SERVER`, `$_GET`, `$_POST`, `$_COOKIE`, `$_REQUEST`, `$_FILES`, `$_SESSION`, más `$_ENV`. En este capítulo los vemos uno por uno, con ejemplos concretos, porque son la puerta de entrada de cualquier aplicación web y los usaremos en todos los proyectos del libro.

## $GLOBALS: Acceder a variables globals

Comencemos con `$GLOBALS`, el superglobal menos utilizado pero el más antiguo: siempre ha existido en PHP. `$GLOBALS` es una especie de **caldero** en el que van a parar todas las variables que viven en el **alcance global** del script, es decir, todas aquellas declaradas fuera de una función. Dentro de `$GLOBALS` también encontramos las otras superglobals (`$_GET`, `$_POST`, `$_COOKIE`, `$_SERVER`, `$_FILES`) y todas las variables globals que hemos definido.

La característica interesante es que se puede acceder a `$GLOBALS` desde cualquier lugar, incluso dentro de una función, sin realizar ninguna importación. Comprobémoslo. Declaramos una variable en el alcance global e intentamos leer `$GLOBALS` desde dentro de una función:

```php
<?php

$testGlobal = 'Esta es una variable global';

function test()
{
    var_dump($GLOBALS);
}

test();
```

Código completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/es/parte-04/cap-13/listing-01.php)


Al ejecutar el script vemos que `$GLOBALS` es un array cuyas claves son los **nombres de las variables globals** (sin el signo de dólar) y los nombres de las superglobals. `testGlobal` también aparece al final de la lista: la clave es exactamente el nombre de la variable, `testGlobal`, sin `$`, y su valor es la cadena que le asignamos.

Si estamos interesados en una única variable global, simplemente use su nombre como clave de array:

```php
function test()
{
    echo $GLOBALS['testGlobal'];
}
```

Código completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/es/parte-04/cap-13/listing-02.php)


Dentro de la función tenemos así acceso a la variable global, a pesar de no haberla declarado allí ni haberla recibido como argumento.

### La construcción global

Hay una segunda forma de acceder a una variable global desde una función: la construcción **`global`**. Al escribir `global $testGlobal;` le estamos diciendo a PHP "importe la variable global `$testGlobal` a la función":

```php
function test()
{
    global $testGlobal;
    echo $testGlobal;
}
```

Código completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/es/parte-04/cap-13/listing-03.php)


El resultado es idéntico. Personalmente prefiero la forma `$GLOBALS['testGlobal']`, que deja explícito que estamos extrayendo de la array global, pero ambas funcionan.

Hay un caso en el que `$GLOBALS` es particularmente útil: cuando dentro de la función ya existe una **variable local con el mismo nombre** como variable global. En esa situación, el nombre simple se refiere a la variable local, mientras que `$GLOBALS['...']` continúa apuntando a la global, sin conflictos:

```php
function test()
{
    $testGlobal = 'prueba de función';

    echo $testGlobal;              // "prueba de función"  → variable local
    echo $GLOBALS['testGlobal'];   // "Esta es una variable global" → global
}
```

Código completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/es/parte-04/cap-13/listing-04.php)


Como puede ver, las variables locales y globals coexisten sin sobrescribirse entre sí.

### Un consejo de la experiencia.

Dicho esto, te daré un consejo como regla general: **evita las variables globals**. Son peligrosos porque pueden sobrescribirse en otras partes del programa sin que usted se dé cuenta y, en aplicaciones grandes, se convierten en una fuente inagotable de errores difíciles de localizar. Si necesita compartir valores globalmente, existen alternativas mucho más limpias: incluya un archivo que **devuelva una array** de constantes o configuraciones (el patrón que vimos en el Capítulo 15), o una clase con propiedades y métodos estáticos. Son formas de no "contaminar" el medio ambiente global.
Una última nota. `$GLOBALS` también contiene los otros superglobals, por lo que técnicamente podrías leer `$GLOBALS['_POST']` en lugar de `$_POST`:

```php
print_r($GLOBALS['_POST']);
```

Código completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/es/parte-04/cap-13/listing-05.php)


Pero no hay razón para hacerlo: `$_POST` ya es accesible en todas partes por sí solo. Entonces `$GLOBALS` lo usaremos, si alguna vez, solo para variables de alcance global, mientras que para las superglobals siempre usaremos su nombre directo.

## $_SERVER: Servidor y solicitar información

`$_SERVER` es una array que PHP llena con mucha información sobre el **servidor** y la **solicitud HTTP** en curso. Parte de esta información se refiere a la máquina en la que se ejecuta el servidor y puede cambiar de un servidor a otro; otros se refieren a la única solicitud que acaba de realizar el navegador. La mejor manera de tener una idea de lo que contiene es imprimirlo:

```php
<?php

var_dump($_SERVER);
```

Código completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/es/parte-04/cap-13/listing-06.php)


Entre las muchas voces, estas son las que se utilizan con más frecuencia:

- **`REMOTE_ADDR`** — la dirección IP del usuario que se conectó. Muy útil para rastrear visitas, registrar de dónde vienen los usuarios, aplicar limitaciones.
- **`HTTP_USER_AGENT`**: la cadena que identifica el navegador y el sistema del usuario.
- **`REQUEST_METHOD`** — el método HTTP de la solicitud: `GET`, `POST`, `PUT`, etc.
- **`QUERY_STRING`**: la cadena de parámetros pasada a través de la URL, tal como se envió.
- **`REQUEST_URI`**: la URL solicitada a partir de la raíz del documento, incluidos los parámetros.
- **`SCRIPT_FILENAME`** — la ruta completa al archivo que estamos ejecutando.
- **`PHP_SELF`**: la ruta al script en ejecución relativa a la raíz del documento.
- **`DOCUMENT_ROOT`** — el directorio raíz del sitio, configurado en el servidor web (por ejemplo, la carpeta Apache `htdocs`).
- **`SERVER_PROTOCOL`** — el protocolo y la versión, por ejemplo `HTTP/1.1`.
- **`SERVER_ADDR`** y **`SERVER_NAME`** — la dirección IP y el nombre de nuestro servidor.
- **`SERVER_SOFTWARE`** — el software y la versión del servidor web.

Para leer una sola entrada, se accede a la array como a una array normal, indicando la clave. Por ejemplo, para obtener la IP del usuario:

```php
echo $_SERVER['REMOTE_ADDR'];
```

Código completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/es/parte-04/cap-13/listing-07.php)


Muchas de estas variables provienen de los **encabezados** que el navegador envía al servidor con cada solicitud. Si abre las herramientas de desarrollo del navegador (haga clic derecho, *Inspeccionar*), va a la pestaña *Red* y recarga la página, podrá ver los encabezados de solicitud y respuesta: el método, el estado (`200`), el dominio, el agente de usuario, el idioma aceptado, la codificación, etc. PHP toma mucha de esta información y la pone a nuestra disposición dentro de `$_SERVER`.

### Detectar el navegador desde el agente de usuario (y por qué no es confiable)

Un uso clásico de `HTTP_USER_AGENT` es entender con qué navegador nos visita el usuario, por ejemplo para recopilar algunas estadísticas:

```php
echo $_SERVER['HTTP_USER_AGENT'];
```

Código completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/es/parte-04/cap-13/listing-08.php)


El valor es una cadena larga que normalmente comienza con `Mozilla/5.0` y contiene "pistas" sobre el navegador: la presencia de `Gecko` sugiere Firefox, `Trident` versiones anteriores de Internet Explorer, etc. Con una expresión regular podríamos extraer esta información. Pero tenga cuidado: a lo largo de los años, los navegadores han cambiado la forma en que componen esta cadena varias veces (Internet Explorer, por ejemplo, dejó de escribir de cierta manera y agregó `like Gecko`), por lo que depender del agente de usuario para la detección del navegador se ha vuelto gradualmente menos confiable. Hoy en día existen bibliotecas especiales y, a menudo, es más sólido realizar estas comprobaciones en el lado del cliente. Pero para usos estadísticos o de registro, `HTTP_USER_AGENT` sigue siendo conveniente: podemos guardarlo en una base de datos junto con la IP para saber quién visita nuestras páginas y con qué herramienta.

## $_GET: los datos de la cadena de consulta

Pasemos a los dos superglobals que más utilizaremos: `$_GET` y `$_POST`, los dos canales por los que un usuario nos envía datos. Comencemos con **`$_GET`**.
`$_GET` contiene todos los parámetros que se pasan mediante **cadena de consulta**, es decir, la parte de la URL que sigue al signo de interrogación. Si en el capítulo anterior vimos el `QUERY_STRING` sin formato dentro de `$_SERVER`, aquí lo encontramos ya seccionado: cada parámetro se convierte en una clave del array y su valor se convierte en el valor asociado. Veámoslo ahora. Tomemos una URL con dos parámetros:

```text
index.php?username=John&lastname=Smith
```

Código completo: [listing-09.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/es/parte-04/cap-13/listing-09.txt)


e imprimimos `$_GET`:

```php
<?php

var_dump($_GET);
```

Código completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/es/parte-04/cap-13/listing-10.php)


Obtenemos un array con dos elementos: la clave `username` con valor `John` y la clave `lastname` con valor `Smith`. Las claves son los nombres de los parámetros, los valores son los que pasamos en la URL.

Una cosa a la que hay que prestar atención: si pasamos caracteres "especiales" en la URL, como letras acentuadas, el navegador normalmente los **codifica** (por ejemplo, un espacio se convierte en `%20`). Del lado de PHP, si es necesario, podemos decodificar estos valores con `urldecode()`. Esto es algo a tener en cuenta cuando llegan datos de la web.

### Mostrar todos los errores durante el desarrollo

Antes de seguir adelante, una buena práctica: **durante el desarrollo, mostrar siempre todos los errores de PHP**. Entonces notarás inmediatamente si estás leyendo una clave que no existe. Puedes configurarlo en el archivo `php.ini`, o directamente en el script con `ini_set()` y `error_reporting()`:

```php
<?php

ini_set('display_errors', 1);
error_reporting(E_ALL);
```

Código completo: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/es/parte-04/cap-13/listing-11.php)


Con `display_errors` a `1` PHP muestra los errores en pantalla, y con `error_reporting(E_ALL)` le pedimos que los reporte todos, incluyendo advertencias y avisos.

### Comprobar si existe un parámetro

Y es por eso que necesitas tener errores activos. Los superglobals `$_GET` y `$_POST` **siempre existen**, incluso cuando están vacíos: hacer `var_dump($_GET)` sin parámetros en la URL no genera ningún error, solo muestra una array vacía. El problema surge cuando intentamos leer una **clave** que no ha sido pasada: PHP emite una advertencia ("clave de array no definida"). Por lo tanto, antes de leer un valor de una array (cualquier array, no solo las superglobals) siempre debemos verificar que la clave exista. Disponemos de tres herramientas, con diferentes matices.

El primero es **`isset()`**, que nos dice si la variable (o clave) está configurada:

```php
if (isset($_GET['username'])) {
    var_dump($_GET['username']);
}
```

Código completo: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/es/parte-04/cap-13/listing-12.php)


Atención a una sutileza: `isset()` comprueba que la variable esté configurada, no que tenga un valor "completo". Una **cadena vacía** se considera establecida (`isset()` devuelve `true`), mientras que un valor `null` se considera **no** establecido: para PHP una variable se establece solo si ha sido declarada y su valor no es `null`.

El segundo es **`empty()`**, que comprueba si el valor está "vacío". Debe usarse con precaución, porque para PHP `0` y la cadena `"0"` también se consideran vacías: si esperamos que un parámetro pueda ser legítimamente cero, `empty()` nos engañaría.

La tercera es la función **`array_key_exists()`**, que comprueba exclusivamente la presencia de la **clave**, independientemente del valor:

```php
if (array_key_exists('username', $_GET)) {
    var_dump($_GET['username']);
}
```

Código completo: [listing-13.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/es/parte-04/cap-13/listing-13.php)


La diferencia práctica con `isset()` radica precisamente en `null`: si un valor se ha establecido en `null`, `isset()` lo considera ausente, mientras que `array_key_exists()` confirma que la clave está ahí. Cuál usar depende de lo que desee: si un valor `null` no tiene sentido para usted y debe tratarse como "ausente", `isset()` está bien; Sin embargo, si necesita saber con certeza si la clave existe (lo cual es típico cuando trabaja con registros que provienen de la base de datos y desea saber si una determinada columna está presente), entonces `array_key_exists()` es la opción correcta. Repito: todo esto se aplica a cualquier array PHP, no sólo a las superglobals.

### Pasar datos vía GET: URL, enlace y formulario

Hay varias formas de que los parámetros terminen en la cadena de consulta y, por lo tanto, en `$_GET`:

**Escribiéndolos a mano en la URL**, como hicimos en los ejemplos anteriores.

**Con un formulario que usa el método GET.** Preparemos un formulario HTML simple (aquí uso alguna clase Bootstrap solo para la apariencia) que apunte a la misma página:

```html
<form action="index.php" method="get">
    <input type="text" name="username" id="username" placeholder="Nombre">
    <input type="text" name="lastname" id="lastname" placeholder="Apellido">
    <input type="reset" value="Reset">
    <button type="submit">Enviar</button>
</form>
```

Código completo: [listing-14.html](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/es/parte-04/cap-13/listing-14.html)


El campo `input` de tipo `reset` es un pequeño truco que borra el formulario con un solo clic. Al completar los campos y enviar, los valores aparecen en la cadena de consulta (`?username=...&lastname=...`) y los encontramos en `$_GET`: la clave de cada valor es el atributo `name` del input. Es por eso que el `name` de cada campo es tan importante: es eso, no el `id`, lo que determina la clave dentro de `$_GET`.

**Con un enlace simple.** Incluso una etiqueta `<a>` con parámetros en la URL envía datos vía GET cuando haces clic en ella:

```html
<a href="index.php?username=test&lastname=testLastname" class="btn btn-danger">Test</a>
```

Código completo: [listing-15.html](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/es/parte-04/cap-13/listing-15.html)


Al hacer clic, los parámetros `test` y `testLastname` llegan a la página exactamente como si los hubiéramos escrito a mano.

Precisamente porque es tan fácil construir una cadena de consulta (a mano, con un enlace o con cualquier cliente HTTP), no podemos confiar ciegamente en los datos que llegan a través de GET. No tenemos ninguna garantía de que realmente haya sido el usuario quien los envió a través de nuestro formulario: alguien podría manipular la URL o simular la solicitud. Es un principio de seguridad a tener siempre presente y lo retomaremos en los proyectos.

## $_POST: datos enviados vía POST

Veamos ahora la diferencia con el método **POST** y cómo los datos enviados de esta manera se asignan al superglobal **`$_POST`**.

Si imprimimos `$_POST` sin haber enviado nada vía POST, el array queda vacío: por aquí no llegó ninguna variable. Para enviar datos vía POST todo lo que necesita es un formulario con `method="post"`. Simplemente cambie el atributo `method` del formulario que teníamos antes:

```html
<form action="index.php" method="post">
    <input type="text" name="username" id="username" placeholder="Nombre">
    <input type="text" name="lastname" id="lastname" placeholder="Apellido">
    <button type="submit">Enviar</button>
</form>
```

Código completo: [listing-16.html](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/es/parte-04/cap-13/listing-16.html)


La diferencia más obvia es que con POST las variables **no viajan en texto claro en la URL**: la cadena de consulta permanece limpia y los valores se transmiten en el cuerpo de la solicitud. Al enviar el formulario con `Juan` y `Arias`, `$_GET` permanece vacío mientras que `$_POST` contiene `username` y `lastname` con los valores ingresados.

`$_GET` y `$_POST` son **dos arrays separadas**. Incluso podemos enviar los mismos nombres de parámetros en ambos sentidos al mismo tiempo, por ejemplo, colocando algunos parámetros en `action` del formulario (que viaja en GET) y otros en los campos (que viajan en POST), y cada valor terminará en su propia array, sin mezclarse. Si llega `username` tanto por GET como por POST, lo encontraremos en `$_GET['username']` con el valor de la cadena de consulta y en `$_POST['username']` con el valor del formulario: no hay sobrescritura entre ambos.

Para leer un valor, se aplican las mismas comprobaciones vistas antes. Si queremos leer el nombre de usuario enviado vía POST, y solo eso, revisamos la clave y la leemos:

```php
if (isset($_POST['username'])) {
    echo $_POST['username'];
}
```

Código completo: [listing-17.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/es/parte-04/cap-13/listing-17.php)


La regla general es la siguiente: **lee las variables del mismo canal por el que las enviaste**. Si has decidido que tu formulario sea POST, lee desde `$_POST`; si es GET, lea desde `$_GET`. De esta manera evitas que alguien inyecte variables "sucias" del otro canal y sobrescriba tus datos.

## Resumen: $_GET, $_POST y $_COOKIE

Hagamos un balance de los tres canales por los que llegan a PHP los datos de una solicitud.

- **`$_GET`** contiene las variables pasadas mediante **query string**: escritas a mano en la URL, enviadas desde un formulario con método GET, contenidas en un enlace o colocadas en el `action` de un formulario.
- **`$_POST`** contiene las variables enviadas vía **POST**: desde un formulario con método POST, o desde un cliente HTTP que realiza una solicitud POST a nuestro servidor.
- **`$_COOKIE`** contiene las **cookies** que el navegador nos envía con cada solicitud. Configuramos una cookie con la función `setcookie()`, indicando su nombre, valor, tiempo de vida (expresado en segundos desde la era Unix), la carpeta o dominio para el que es válida y otros parámetros. Una vez configurada, la próxima vez que se recarga la página, el navegador nos la envía y la leemos en `$_COOKIE`. El siguiente capítulo lo dedicamos íntegramente a las cookies, por lo que aquí nos limitamos a colocarlas en el grupo superglobal.
Un detalle importante sobre las cookies, que explica por qué las aislamos del resto: la primera vez que configuras una cookie, **aún** no está en `$_COOKIE`. `$_COOKIE` contiene lo que el navegador está enviando **ahora**, y en ese momento el navegador aún no sabe la cookie que le estamos enviando por primera vez. Lo veremos completado solo en la siguiente solicitud. Volveremos a esta distinción en el capítulo 14.

## $_REQUEST y conclusión

Finalmente, hay un superglobal que une los tres canales que acabamos de ver: **`$_REQUEST`**. `$_REQUEST` es una array que **fusiona** (fusiona) `$_GET`, `$_POST` y, dependiendo de la configuración, `$_COOKIE`. Si llega la misma clave desde varios canales, uno sobrescribe al otro en un orden preciso.

Veámoslo con un ejemplo. Supongamos que pasamos `username=Santos` y `lastname=Smith` mediante una cadena de consulta y simultáneamente enviamos un formulario mediante POST con `username=Juan` y `lastname=Arias`:

```php
var_dump($_GET);      // Santos, Smith
var_dump($_POST);     // Juan, Arias
var_dump($_REQUEST);  // Juan, Arias  ← gana POST
```

Código completo: [listing-18.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/es/parte-04/cap-13/listing-18.php)


En `$_REQUEST` encontramos los valores del POST: en el orden predeterminado, el POST llega después del GET y por tanto lo sobrescribe.

### Quién decide el pedido: request_order

El orden en el que se completa `$_REQUEST` no está escrito en piedra: depende de la configuración **`request_order`** (y secundariamente de `variables_order`) en el archivo `php.ini`. En versiones recientes de PHP, el valor predeterminado es `GP`, es decir, "OBTENER primero, luego POST": POST tiene prioridad y las cookies **no** están incluidas. Personalmente, es la configuración que prefiero: tampoco me gusta tener cookies en `$_REQUEST`. Sin embargo, si cambiamos `request_order` a, por ejemplo, `GPC`, entonces las cookies también entrarían en la fusión y, al ser las últimas, podrían sobrescribir GET y POST. Después de tocar `php.ini`, debe reiniciar el servidor web para que se cargue la nueva configuración.

### ¿Por qué tener cuidado con $_REQUEST?

Precisamente porque el comportamiento de `$_REQUEST` depende de la configuración del servidor, **no te acostumbres a leer siempre desde `$_REQUEST`** sin importarte si los datos llegaron vía GET o vía POST. Mire este caso: si no envía el formulario pero los valores están presentes solo a través de GET, y en la fusión el POST (vacío) todavía "ganó", podría encontrarse con valores vacíos en `$_REQUEST` a pesar de tener datos válidos en `$_GET`. El mensaje es: **sea específico sobre lo que desea de cada canal**. Leer desde `$_REQUEST` es conveniente, pero lo expone a sorpresas y pequeños fallos de seguridad; leer desde el canal correcto es casi siempre la mejor opción.

Cerramos con la observación de la que partimos: todos estos superglobals son realmente *super* porque son accesibles en todas partes, incluso dentro de una función, sin tener que escribir `global` delante de nada. Sólo necesitamos utilizar su nombre y, si es necesario, la clave:

```php
function test()
{
    var_dump($_GET, $_POST, $_SERVER);
}

test(); // funciona: las superglobals también son visibles aquí dentro
```

Código completo: [listing-19.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/es/parte-04/cap-13/listing-19.php)


Nos quedamos con dos superglobals especialmente importantes, que merecen un tratamiento aparte: `$_FILES`, para gestionar la carga de archivos, y `$_SESSION`, para almacenar datos entre una página y otra.

## $_FILES: cargando archivos

El superglobal **`$_FILES`** nos da acceso a los archivos que el usuario ha subido a través de un formulario. Es decir, sólo tenemos acceso a él cuando se ha producido una **carga**.

Para cargar un archivo se necesitan dos condiciones en el lado HTML. El primero es un campo `input` de tipo `file`. La segunda, a menudo olvidada, es que el formulario tiene el atributo **`enctype="multipart/form-data"`**: sin él el archivo no se transmite. Este tipo de codificación le dice al navegador que envíe la solicitud en "múltiples partes", una para los campos clave-valor normales (como `username`) y otra para el contenido binario del archivo. Aquí hay una forma mínima:

```html
<form action="index.php" method="post" enctype="multipart/form-data">
    <input type="text" name="username" placeholder="Nombre">
    <input type="file" name="avatar" id="avatar">
    <button type="submit">Enviar</button>
</form>
```

Código completo: [listing-20.html](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/es/parte-04/cap-13/listing-20.html)


### La estructura de la array $_FILES

Antes de cargar algo, `$_FILES` está vacío. Después de enviar el formulario con un archivo, contiene una array cuya clave es el **nombre del campo** (el atributo `name` de la entrada, aquí `avatar`), y cuyo valor es en sí mismo una array con información sobre el archivo. Comprobémoslo:

```php
var_dump($_FILES);
```

Código completo: [listing-21.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/es/parte-04/cap-13/listing-21.php)


Para cada archivo subido encontramos estas claves:
- **`name`** — el nombre original del archivo tal como estaba en la computadora del usuario (por ejemplo `foto.jpg`).
- **`type`** — el tipo MIME declarado por el navegador (por ejemplo `image/jpeg`).
- **`tmp_name`**: la ruta al archivo **temporal** donde el servidor guardó la carga (en la carpeta temporal del sistema). Desde aquí tendremos que trasladarlo hasta su destino final.
- **`error`** — el código de error de carga: es `0` si todo salió bien.
- **`size`** — el tamaño del archivo en bytes.

Si hubiera dos campos de archivo en el formulario, por ejemplo `avatar` y `avatar2`, entonces `$_FILES` sería una **array de arrays**: una clave para cada campo y, debajo de cada uno, las cinco propiedades que acabamos de enumerar.

### Guarde el archivo cargado de forma segura

Veamos cómo usar estos datos para copiar el archivo de la carpeta temporal a nuestra propia carpeta. Supongamos que tenemos, en el mismo directorio que el script, una carpeta `images` en la que se puede escribir. Pasamos por `$_FILES` y, para cada archivo, hacemos dos comprobaciones fundamentales antes de moverlo:

```php
<?php

if (!empty($_FILES)) {
    foreach ($_FILES as $key => $file) {

        // 1. ¿realmente es un archivo subido por HTTP? (seguridad)
        // 2. ¿la subida se completó correctamente?
        if (is_uploaded_file($file['tmp_name']) && $file['error'] === UPLOAD_ERR_OK) {

            $dir = __DIR__ . '/images';
            $fileName = basename($file['name']);
            $destination = $dir . '/' . $fileName;

            if (move_uploaded_file($file['tmp_name'], $destination)) {
                echo "El archivo {$fileName} se ha subido correctamente.<br>";
            }
        }
    }
}
```

Código completo: [listing-22.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/es/parte-04/cap-13/listing-22.php)


Analicemos los pasos clave:

- **`is_uploaded_file()`** recibe la ruta temporal (`tmp_name`) y devuelve `true` solo si ese archivo realmente se cargó mediante una solicitud HTTP POST. Es un control de seguridad: nos protege de cualquiera que intente obligarnos a procesar un archivo arbitrario del servidor haciéndolo pasar por una carga.
- **`$file['error'] === UPLOAD_ERR_OK`** comprueba que no ha habido errores. `UPLOAD_ERR_OK` es una constante PHP que es `0`; También podríamos escribir `$file['error'] === 0`, pero usar la constante hace que el código sea más legible.
- **`__DIR__`** es una constante mágica que contiene la ruta absoluta a la carpeta donde se encuentra el script actual (el equivalente a `dirname(__FILE__)`). Construir el destino a partir de `__DIR__` es más sólido que escribir una ruta relativa: el script funciona sea cual sea la carpeta actual del proceso. En Linux recuerde que esta carpeta debe tener **permisos de escritura** para el usuario con el que se ejecuta PHP, de lo contrario el movimiento fallará.
- **`basename()`** aplicado a `$file['name']` extrae solo el nombre del archivo, descartando cualquier ruta. Es importante utilizar `name` (el nombre original) y no `tmp_name` para el nombre de destino: si usáramos la ruta temporal, terminaríamos con un nombre incomprensible.
- **`move_uploaded_file()`** mueve el archivo desde la ubicación temporal al destino y devuelve `true` si tiene éxito. Es la función dedicada precisamente a este propósito y debe preferirse a un simple `copy()`, porque también verifica que el archivo proviene de una carga legítima.

### Dos precauciones importantes

Primero: **nunca confíes en el campo `type`**. El tipo MIME declarado en el formulario puede ser falsificado por quien realiza la solicitud. Si necesita asegurarse de que un archivo es realmente una imagen (o un PDF, un documento de Excel, etc.), verifique el tipo real en el lado de PHP, analizando el contenido del archivo con funciones como `finfo` o `mime_content_type()`, sin confiar en `$file['type']`.

Segundo: el **nombre** con el que guardas el archivo. Puede conservar el nombre original, pero a menudo es mejor generar uno único (por ejemplo, anteponiendo una marca de tiempo) para evitar que dos usuarios que cargan archivos con el mismo nombre se sobrescriban entre sí. Una vez que guarda el archivo, normalmente registra su nombre en la base de datos. Y si está administrando imágenes, también puede cambiar su tamaño con las funciones de la biblioteca GD (como `imagecreatefromjpeg()`) o confiar en una biblioteca dedicada.

Finalmente, para administrar múltiples archivos con un solo campo, puede usar la sintaxis `name="avatar[]"` en la entrada y el atributo HTML5 `multiple`: en ese caso `$_FILES` recopila todos los archivos bajo una sola clave, como una array. La lógica de control y movimiento sigue siendo idéntica. Si ya utiliza un marco o biblioteca que administra las cargas por usted, ahora sabe lo que sucede "en la parte inferior" de todos modos: todo gira en torno a esta array global, `$_FILES`.

## $_SESSION: almacenar datos entre páginas

Llegamos al último mecanismo superglobal y uno de los más importantes de PHP para la web: la **sesión**, gestionada a través de `$_SESSION`.
Una sesión es un entorno en el que podemos **almacenar datos que sobreviven de una página a otra**, durante toda la "sesión de trabajo" del usuario. En el caso clásico, en el que la sesión está vinculada a una cookie, los datos permanecen disponibles mientras el usuario mantenga abierto el navegador; cuando se cierra el navegador la sesión desaparece. Ésta es la diferencia con las cookies reales, que, en cambio, como veremos en el próximo capítulo, pueden persistir incluso después de cerrar el navegador. Para identificar a qué usuario pertenece una sesión, PHP a su vez utiliza una cookie: en la primera visita genera un identificador aleatorio, lo envía al navegador y con cada solicitud posterior el navegador lo devuelve, lo que permite a PHP volver a conectar esa solicitud con los datos de sesión correctos.

### Iniciar la sesión con session_start()

Si imprimimos `$_SESSION` sin iniciar nada, no hay sesión activa y el array no existe. El primer paso, siempre, es iniciar la sesión con **`session_start()`**:

```php
<?php

session_start();

$_SESSION['user_id'] = 4;
$_SESSION['logged'] = 1;
```

Código completo: [listing-23.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/es/parte-04/cap-13/listing-23.php)


Con `session_start()` se abre la sesión. A partir de este momento podemos escribir valores dentro de `$_SESSION` como en una array normal: en el ejemplo almacenamos el ID de un usuario y una bandera que indica que ha iniciado sesión.

Si ahora miramos la pestaña *Red* y los encabezados de solicitud en las herramientas de desarrollo del navegador, entre las cookies encontramos una llamada **`PHPSESSID`**: es el identificador de sesión que PHP creó para nosotros. De ahora en adelante, el navegador la enviará con cada solicitud, y cualquier script en nuestro sitio que comparta esa cookie tendrá acceso al mismo `$_SESSION`.

### Leer la sesión en otra página

Y ese es exactamente el punto: los datos colocados en la sesión en una página se pueden leer desde otra página. Sin embargo, hay una condición: **la página de lectura también debe llamar a `session_start()`**. Si en una segunda página intentamos leer `$_SESSION['user_id']` sin iniciar la sesión, obtenemos un error de clave indefinida. Sin embargo, al agregar `session_start()` en la parte superior, encontramos todos los valores:

```php
<?php

session_start();

var_dump($_SESSION['user_id']); // 4
```

Código completo: [listing-24.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/es/parte-04/cap-13/listing-24.php)


Así, cualquier página que comparta la cookie de sesión (porque está en el mismo dominio y carpeta) tiene acceso a las variables de sesión. Profundizaremos en la gestión completa y **seguridad** de las sesiones en un capítulo dedicado, dentro de los proyectos prácticos; Aquí nos centramos en lo superglobal y su funcionamiento básico.

### session_start() antes de cualquier salida

Hay una limitación técnica que respetar. Cuando iniciamos la sesión, PHP envía la cookie `PHPSESSID` al navegador, y las cookies viajan en los **encabezados**, que deben enviarse **antes** de cualquier contenido HTML. Por lo tanto `session_start()` no puede ir precedido de ninguna salida: si antes imprimimos aunque sea una sola etiqueta `<h1>`, o dejamos un espacio antes de la apertura `<?php`, corremos el riesgo del clásico error *"no se puede modificar la información del encabezado - encabezados ya enviados"*.

Por este motivo, la regla general es poner **`session_start()` como la primera instrucción** del archivo. En muchas configuraciones el error no aparece porque el *búfer de salida* está activo (lo que pone el contenido en un búfer y lo envía solo al final), pero no podemos darlo por sentado en todos los servidores. Es un tema que retomaremos y examinaremos al final del próximo capítulo, dedicado precisamente a las cookies y al error de los encabezados ya enviados.

### Liberando el bloqueo: session_write_close()

Un último detalle útil en aplicaciones reales. Cuando la sesión se administra en **archivo** (el valor predeterminado), en el momento en que llamamos a `session_start()` y comenzamos a escribir en él, PHP **bloquea** ese archivo de sesión. Si otro script intenta acceder a la misma sesión, deberá esperar a que finalice el primero. En aplicaciones con muchas solicitudes simultáneas (piense en varias llamadas AJAX que comienzan a la vez), esto puede crear cuellos de botella, ya que las solicitudes se ponen en cola esperando que se libere el bloqueo.

Cuando hayamos terminado de escribir (o leer) la sesión y ya no necesitemos mantenerla abierta, es buena idea cerrarla explícitamente con **`session_write_close()`**:

```php
session_start();

$_SESSION['user_id'] = 4;

// ...terminamos de trabajar con la sesión:
session_write_close();
```

Código completo: [listing-25.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/es/parte-04/cap-13/listing-25.php)


Con esta llamada declaramos que hemos terminado de escribir: PHP guarda los datos, libera el bloqueo y las demás solicitudes concurrentes finalmente pueden acceder a la sesión. Si tiene scripts llamados a través de AJAX que deben ejecutarse en paralelo, recuerde liberar la sesión tan pronto como haya terminado, para no bloquear los otros archivos.

## En resumen

- **superglobals** son arrays que PHP llena automáticamente y que son accesibles en cualquier ámbito, incluso dentro de una función, sin `global`: `$GLOBALS`, `$_SERVER`, `$_GET`, `$_POST`, `$_COOKIE`, `$_REQUEST`, `$_FILES`, `$_SESSION`.
- **`$GLOBALS`** recoge todas las variables del alcance global (clave = nombre sin `$`). También se puede acceder a través de la construcción `global`. Deben evitarse las variables globals: mejor un archivo de configuración que devuelva una array o una clase con miembros estáticos.
- **`$_SERVER`** expone el servidor y solicita información: `REMOTE_ADDR` (IP de usuario), `REQUEST_METHOD`, `QUERY_STRING`, `REQUEST_URI`, `PHP_SELF`, `SCRIPT_FILENAME`, `DOCUMENT_ROOT`, `HTTP_USER_AGENT` y otros. El agente de usuario es conveniente pero poco confiable para detectar el navegador.
- **`$_GET`** contiene los parámetros de la cadena de consulta (URL, enlace, formulario GET); **`$_POST`** los enviados vía POST (los datos no aparecen en la URL). Son arrays separadas y no se sobrescriben entre sí.
- Antes de leer una clave, compruebe siempre que existe: **`isset()`** (el `null` cuenta como no establecido, la cadena vacía sí), **`empty()`** (preste atención a `0` y `"0"`) y **`array_key_exists()`** (verifique sólo la clave, `null` incluida). Esto se aplica a todas las arrays.
- Siempre habilitar errores en desarrollo: `ini_set('display_errors', 1)` y `error_reporting(E_ALL)`. No confíes en los datos que llegan vía GET/POST: pueden ser manipulados.
- **`$_REQUEST`** es la fusión de GET, POST (y cookie, si está configurada); el orden depende de `request_order` en `php.ini` (por defecto `GP`, POST gana). Es mejor leer desde el canal específico que confiar en `$_REQUEST`.
- **`$_FILES`** gestiona la carga: el formulario debe tener `enctype="multipart/form-data"`. Para cada archivo hay `name`, `type`, `tmp_name`, `error`, `size`. Guarde de forma segura con `is_uploaded_file()`, marcando `error === UPLOAD_ERR_OK` y `move_uploaded_file()`; No confíes en `type`, comprueba el tipo real.
- **`$_SESSION`** preservar datos entre páginas: comience siempre con `session_start()` (antes de cada salida, para evitar encontrarse con "encabezados ya enviados") en cada página que necesita acceder a ella. PHP identifica la sesión con la cookie `PHPSESSID`. Con la sesión de archivo, `session_write_close()` libera el bloqueo y evita cuellos de botella con solicitudes simultáneas.
