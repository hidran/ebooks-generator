# 6. La sintaxis básica

Con el entorno de desarrollo listo, es hora de escribir las primeras líneas de PHP. En este capítulo aprendemos los elementos fundamentales de la sintaxis: las etiquetas que delimitan el código PHP, el punto y coma que cierra cada declaración, los comentarios y el constructo `echo`. También veremos las dos formas en que podemos ejecutar un script PHP (desde la terminal, como un programa normal, y a través de un servidor web, como una página web) y descubriremos que PHP se comporta de manera ligeramente diferente en los dos casos.

En la segunda parte del capítulo nos centramos en **expresiones** y **literales**: qué sucede cuando escribimos `2 + 2;` en un archivo PHP, dónde termina el resultado y por qué, sin un lugar donde almacenarlo, ese resultado desaparece inmediatamente. Es la premisa perfecta para el próximo capítulo, dedicado a variables, tipos y constantes.

## Organiza el código y crea el primer archivo.

En primer lugar, crea una carpeta en la que recoger todo el código de este libro, y dentro de ella una subcarpeta para cada capítulo o tema: de esta forma siempre tendrás el código organizado y fácil de encontrar. Para este capítulo usaremos una carpeta llamada `intro`.

Abra la carpeta con su editor (en los ejemplos uso Visual Studio Code, pero cualquier editor que prefiera está bien) y cree un archivo dentro llamado `index.php`. VS Code reconoce inmediatamente la extensión `.php` y muestra el icono de PHP junto al nombre del archivo.

Como vimos en el Capítulo 5, lo mejor es instalar algunos componentes desde la vista de extensiones (busca "PHP") que nos acompañarán a lo largo del libro:

- **PHP Debug**, para depurar el código;
- **PHP Intelephense**, para autocompletado inteligente;
- **PHP Extension Pack**, que agrupa casi todos los paquetes útiles de una sola vez;
- **Servidor PHP**, para iniciar un servidor web "sobre la marcha" y probar el código inmediatamente.

### La ruta al ejecutable PHP

Desde VS Code puede abrir la terminal incorporada desde el menú Terminal → Nueva Terminal. Lo primero que debemos comprobar cuando entramos en una terminal es que PHP esté disponible. En macOS y Linux puedes saber dónde está el ejecutable con:

```bash
which php
```

Código completo: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-01.sh)


El comando responde con la ruta completa a PHP, por ejemplo:

```text
/opt/homebrew/bin/php
```

Código completo: [listing-02.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-02.txt)


También necesitas esta ruta en VS Code: si el editor informa que el ejecutable PHP no está instalado, significa que no puede encontrarlo en la configuración. Abra Configuración, busque "PHP" y verá la configuración de las distintas extensiones PHP instaladas: en el campo dedicado a la ruta del ejecutable (por ejemplo `php.validate.executablePath`) ingrese la ruta devuelta por `which php`. Establezca también la misma ruta en las opciones de extensión del servidor PHP, para que el autocompletado y la validación del código funcionen correctamente.

Tenga cuidado si utiliza la sincronización de la configuración de VS Code (la que está conectada a su cuenta de GitHub): puede suceder que el editor herede la ruta de otra máquina. Para mí, por ejemplo, la sincronización había devuelto la ruta de Windows a Mac: en Windows con Laragon PHP se encuentra en una carpeta como `C:\laragon\bin\php\php-8.x\php.exe`, mientras que en este Mac está en `/opt/homebrew/bin/php`. La ruta correcta siempre depende del sistema que esté utilizando.

## etiquetas PHP

Ahora podemos empezar a planificar. Lo primero que debemos hacer en un archivo PHP es declarar que estamos usando PHP. ¿Por qué? Porque PHP, al ser un **lenguaje de scripting**, se puede incluir dentro de una página HTML: cuando el servidor web procesa la página, todo lo que está *fuera* de las etiquetas PHP se deja como está, mientras que solo se interpreta lo que está *dentro* de las etiquetas.

La **etiqueta de apertura**, que le dice al servidor web (o intérprete PHP) "hay código PHP de ahora en adelante", es:

```php
<?php
```

Código completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-03.php)


Con esto podemos empezar a escribir PHP. En muchos ejemplos también verás la **etiqueta de cierre** `?>`, pero esto sólo es necesario si mezclamos PHP con HTML. de hecho, es mejor *no* cerrarlo: después de `?>`, se enviaría a la salida una línea vacía en la parte inferior del archivo, que tal vez ni siquiera veamos, y podría causar errores difíciles de detectar.

Lo primero que podemos hacer para comprobar que PHP funciona es utilizar la función `phpinfo()`:

```php
<?php
phpinfo();
```

Código completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-04.php)


Tenga en cuenta el **punto y coma** al final: PHP lo necesita para comprender dónde termina cada **declaración**. Advertencia: el punto y coma no debe colocarse "en cada línea", sino al final de cada declaración. Más adelante, cuando escribamos por ejemplo un `if` o una función, veremos que una instrucción puede continuar fácilmente en varias líneas.

## Ejecute PHP desde la terminal

Ejecutemos nuestro primer script. Desde la terminal, ingresamos a la carpeta del proyecto:

```bash
cd intro
ls -al
```

Código completo: [listing-05.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-05.sh)


`ls -al` es un comando de Linux (y macOS) que muestra el contenido de una carpeta. Si estás en Windows tienes dos formas de tener los mismos comandos:

- **WSL2** (Subsistema de Windows para Linux), que es a todos los efectos un Linux dentro de Windows;
- **Git Bash**: al buscar "Git para Windows", puedes instalar Git (aunque es conveniente, porque también tendrás una herramienta de control de versiones de código) y juntos obtendrás el shell Bash. Git existe para macOS, Windows y Linux, y en Windows la instalación le brinda solo esa consola.

En VS Code, cuando abres la terminal desde Terminal → Nueva Terminal, puedes hacer clic en la flecha al lado del botón `+` y elegir entre las diferentes consolas disponibles: en Windows verás la terminal clásica, PowerShell, Git Bash, etc. En los ejemplos utilizo Bash, pero el comando para ejecutar PHP es idéntico en cualquier sistema: Linux, Windows o macOS: simplemente escribe `php`, un espacio y el nombre del archivo.

```bash
php index.php
```

Código completo: [listing-06.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-06.sh)


¡Funciona! El resultado, sin embargo, es enorme: `phpinfo()` imprime toda la información sobre la instalación de PHP: la versión, todas las directivas de configuración que se encuentran en el archivo `php.ini` (lo veremos más adelante), las bibliotecas y extensiones instaladas, etc. Es una función valiosa: si tienes un servicio de hosting y quieres comprobar cómo está configurado PHP sin pasar por la interfaz del proveedor, sólo tienes que subir un archivo con este código y tendrás toda la información.

## Ejecutar PHP como página web

Si ejecutamos el mismo `index.php` a través de un servidor web, en lugar de texto sin formato veremos una página web real. Hay dos maneras convenientes de hacer esto.

### La extensión del servidor PHP

Con la extensión del servidor PHP instalada, haga clic derecho en el archivo y elija la entrada del servidor PHP para servir el proyecto. Si la entrada no aparece en el menú contextual, presione Shift+Cmd+P en Mac (Ctrl+Shift+P en Windows) y escriba "servidor": elija **Servidor PHP**, no Live Server: Live Server solo sirve para páginas HTML estáticas. Alternativamente, en la parte superior derecha del editor está el icono de la extensión: un clic y se inicia el servidor.

PHP Server crea automáticamente un servidor web local en un puerto dedicado y abre el navegador en nuestra página `index.php`: esta vez `phpinfo()` aparece como una página formateada, con tablas y colores. Si hacemos clic derecho en el navegador y miramos el código fuente de la página, vemos las etiquetas HTML que no estaban allí desde la terminal. ¿Por qué? Porque PHP *nota* cómo se ejecuta: cuando se ejecuta desde la línea de comandos produce texto sin formato, cuando se ejecuta detrás de un servidor web produce HTML.

### El servidor PHP integrado

También podemos hacer lo que hace VS Code con la extensión desde la línea de comandos: PHP incluye de serie un servidor web de desarrollo. Simplemente tenga instalado PHP y ejecute `php -S` (con S mayúscula) seguido de host y puerto; con la opción `-t` indicamos la carpeta a servir. Por ejemplo, si estamos en la carpeta del proyecto y queremos servir la subcarpeta `intro`:

```bash
php -S localhost:8000 -t intro
```

Código completo: [listing-07.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-07.sh)


Ahora abramos el navegador en `http://localhost:8000` y veamos nuestra página. Un consejo práctico: si el puerto ya está ocupado (me pasó con un proyecto Laravel escuchando en 8000) simplemente detenga el servidor con Ctrl+C y reinícielo en otro puerto, por ejemplo 3000:

```bash
php -S localhost:3000 -t intro
```

Código completo: [listing-08.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-08.sh)


### Los comentarios

Si no queremos que se ejecute una línea de código, podemos **comentarla**. Un comentario de una sola línea se escribe con la doble barra `//`; también está el comentario del bloque, que se abre con `/*` y se cierra con `*/` y puede extenderse a varias líneas; volveremos a él más adelante.

```php
<?php
// phpinfo();  esta línea ahora es un comentario y no se ejecuta

/*
  Este es un comentario
  en varias líneas.
*/
```

Código completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-09.php)


Comentamos la llamada a `phpinfo()` y volvemos a ejecutar el archivo desde la línea de comando: ya no sale nada. Recarguemos la página en el navegador: aquí también, página vacía. El comentario "desactivó" la única declaración en el archivo.

## Mezclar PHP y HTML

Hagamos un experimento: agreguemos, *antes* de la etiqueta PHP, una etiqueta HTML normal.

```php
<h1>Hola Mundo</h1>
<?php
```

Código completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-10.php)


Reiniciamos el servidor web y recargamos la página: aparece el título. Como decíamos, el servidor web sirve el HTML tal cual; sólo se interpreta lo que está dentro de las etiquetas PHP.

¿Y si añadimos algo de PHP? Aprendamos inmediatamente el primer comando PHP: `echo`, que escribe la salida de todo lo que le pasamos. Abrimos las comillas, escribimos una cadena y cerramos con punto y coma, porque ahí termina el enunciado:

```php
<h1>Hola Mundo</h1>
<?php
echo "Me llamo Juan";
```

Código completo: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-11.php)


Recargamos la página: con PHP escribimos esta cadena en la página web. Y eso no es todo: podemos poner algo de HTML *dentro* de la cadena, por ejemplo una etiqueta `<h3>`:

```php
<h1>Hola Mundo</h1>
<?php
echo "<h3>Me llamo Juan</h3>";
```

Código completo: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-12.php)


¿Qué está pasando exactamente? Estamos enviando una página web al navegador, y el navegador interpreta lo que recibe como HTML: al recargar la página, el texto aparece formateado como un título de tercer nivel, y mirando la fuente vemos que hemos *generado* algo de HTML con PHP.

Si ahora lanzamos el mismo archivo desde la terminal, en otra pestaña de la terminal:

```bash
php intro/index.php
```

Código completo: [listing-13.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-13.sh)


```text
<h1>Hola Mundo</h1><h3>Me llamo Juan</h3>
```

Código completo: [listing-14.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-14.txt)


Se hace lo mismo, pero aquí no vemos una página web; no estamos en un navegador, estamos en la línea de comando, por lo que vemos la salida HTML sin formato que genera PHP.

Finalmente, como estaba previsto, también podemos cerrar la etiqueta PHP con `?>` y, tras cerrarla, escribir más HTML:

```php
<h1>Hola Mundo</h1>
<?php
echo "<h3>Me llamo Juan</h3>";
?>
<p>PHP es genial</p>
```

Código completo: [listing-15.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-15.php)


Desde la terminal también vemos el párrafo en la salida; en el navegador, sin tener que mirar la fuente, aparece el párrafo en la página. Pero recuerde la regla: la etiqueta de cierre sólo es útil cuando hay HTML detrás; en un archivo PHP puro es mejor omitirlo.

### PHP más allá de la web

En pocas palabras: podemos ejecutar PHP desde la línea de comandos, por lo que PHP no está necesariamente vinculado a la web. Un script PHP podría realizar una llamada FTP y descargar un archivo de un servidor, copiar archivos de una carpeta a otra, crear carpetas en el sistema de archivos, conectarse a una base de datos, llamar a una API, cualquier cosa, sin HTML involucrado. Y, por supuesto, PHP también puede ejecutarse detrás de un servidor web, como el integrado que acabamos de usar, para servir páginas web. PHP es, a todos los efectos, un lenguaje multipropósito.

## Expresiones y literales

Ahora que sabemos cómo escribir y ejecutar un archivo PHP, veamos cómo PHP maneja los datos que le damos. Esto servirá como introducción a las variables y constantes del próximo capítulo: entenderemos *por qué* las necesitamos.

Creemos una nueva carpeta, la llamaré `variabili`, con un nuevo `index.php` dentro. Una **expresión literal** es una expresión que escribimos tal cual, como en matemáticas. Por ejemplo:

```php
2 + 2;
```

Código completo: [listing-16.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-16.php)


Recuerde el punto y coma: con eso, esta es una declaración PHP correcta. Ejecutemos el archivo desde la terminal; aquí no hay nada "web", ni etiquetas HTML, por lo que la línea de comando es perfecta para verificar si el archivo funciona. Si ha agregado PHP a la RUTA del sistema, cualquier versión de PHP servirá para esta parte básica:

```bash
php variabili/index.php
```

Código completo: [listing-17.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-17.sh)


```text
2 + 2;
```

Código completo: [listing-18.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-18.txt)


Sorpresa: vemos literalmente a `2 + 2`. ¿Lo que está sucediendo? PHP, al no encontrar una etiqueta de apertura dentro del archivo, incluso si el archivo se llama `index.php`, trata todo lo que está fuera de las etiquetas como texto: lo devuelve *tal cual*, tal como está, sin interpretarlo.

### La salida estándar es fwrite

El lugar donde el terminal muestra los resultados se llama **salida estándar** en programación. PHP proporciona una constante (más adelante veremos qué son las constantes) llamada `STDOUT`, que representa la salida estándar: en este caso, nuestra consola. Advertencia: `STDOUT` existe sólo cuando PHP se ejecuta desde la línea de comandos, no cuando se ejecuta detrás de un servidor web.
Para escribir en la salida estándar podemos usar la función `fwrite()`, que significa "escribir" (*escribir*): es una función diseñada para escribir en un archivo, y la salida estándar se comporta exactamente como un archivo al que enviamos datos: `STDOUT` es de hecho un **recurso** de tipo archivo, un "canal" que ya está abierto para nosotros. Estudiaremos estas funciones más adelante; Por ahora sólo lo necesitamos para el experimento:

```php
<?php
fwrite(STDOUT, 2 + 2);
```

Código completo: [listing-19.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-19.php)


Tenga en cuenta que esta vez abrimos la etiqueta `<?php`: sin ella, como acabamos de ver, PHP no interpretaría nada. Relanzamos:

```text
4
```

Código completo: [listing-20.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-20.txt)


Aquí está el número 4: esta vez PHP *evaluó* la expresión `2 + 2` y escribió el resultado en la salida estándar. En lugar del número podríamos escribir una cadena (las veremos en detalle más adelante); por ahora sepa que una **cadena** se escribe entre comillas simples o dobles:

```php
<?php
fwrite(STDOUT, 'Juan');
```

Código completo: [listing-21.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-21.php)


Y veamos el nombre en consola. Pero intentemos servir el mismo archivo con el servidor web integrado:

```bash
php -S localhost:3000 -t variabili
```

Código completo: [listing-22.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-22.sh)


Al abrir `http://localhost:3000` se produce un error: la constante `STDOUT` no está definida. Como dijimos, sólo existe cuando PHP se ejecuta desde la línea de comandos.

### La construcción de eco

Para enviar resultados tanto al navegador como a la consola, la elección correcta es la construcción `echo` que ya hemos encontrado: "sale" cualquier resultado a la salida actual, dondequiera que se esté ejecutando PHP. Comentamos la línea con `fwrite()` usando `//` y probamos:

```php
<?php
// fwrite(STDOUT, 'Juan');
2 + 2;
echo 'Hola Mundo';
```

Código completo: [listing-23.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-23.php)


```text
Hola Mundo
```

Código completo: [listing-24.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-24.txt)


Funciona tanto desde el terminal como desde el navegador. Pero observe algo interesante: la línea `2 + 2;` no produce nada. PHP lo evalúa (la expresión realmente se ejecuta) pero no le sucede nada al resultado: no termina en la salida y no se coloca en un área de memoria que podamos reutilizar. Si queremos verlo, debemos pasárselo a `echo`:

```php
<?php
echo 2 + 2;
echo 'Hola Mundo';
```

Código completo: [listing-25.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-25.php)


```text
4Hola Mundo
```

Código completo: [listing-26.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-26.txt)


El 4 está ahí, pero la cadena aparece adjunta inmediatamente después: no hay ninguna línea nueva. Veremos por qué cuando hablamos de cadenas; por ahora basta con saber que en una cadena entre comillas dobles la secuencia `\n` (barra invertida + n) representa el carácter de nueva línea:

```php
<?php
echo 2 + 2;
echo "\n";
echo 'Hola Mundo';
```

Código completo: [listing-27.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-27.php)


```text
4
Hola Mundo
```

Código completo: [listing-28.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-28.txt)


### ¿Por qué necesitamos variables?

Entonces: si no usamos `echo`, no vemos el resultado de una expresión. Pero hay más. Supongamos que quiero *conservar* el resultado de esa operación para enviarlo por correo electrónico o guardarlo en una base de datos: no puedo. Una vez ejecutada la línea, ese resultado ya no existe.

Y ahí es donde las **variables** entran en juego, permitiéndonos almacenar estos resultados: una cadena, un número, un registro leído de la base de datos; cualquier tipo de valor admitido por PHP puede terminar en una variable. En PHP el nombre de una variable debe ir precedido del signo de dólar `$` (veremos por qué en el próximo capítulo): así es como PHP entiende que es una variable.

```php
<?php
$result = 2 + 2;
echo $result;
```

Código completo: [listing-29.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-29.php)


```text
4
```

Código completo: [listing-30.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-30.txt)


Presta atención al significado del signo `=`: no estamos diciendo que algo "es igual a" dos más dos, como en matemáticas. En programación, y por tanto en PHP, el signo igual es una **asignación**: "ejecutar la operación de la derecha y asignar el resultado a la variable de la izquierda". Y cuando usamos la variable, se requiere el dólar: si escribiéramos `echo result;` PHP pensaría que `result` es una constante.

Lo mismo ocurre con las cuerdas. Si escribo mi nombre entre comillas, solo en una línea:

```php
<?php
'Juan';
```

Código completo: [listing-31.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-31.php)


Ejecuto el código y no veo nada: tengo que hacerlo `echo`, o ponerlo en una variable para poder almacenarlo:

```php
<?php
$name = 'Juan';
```

Código completo: [listing-32.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-32.php)


De ahora en adelante con `$name` puedo hacer lo que quiera: enviarlo por correo electrónico, escribirlo en el sistema de archivos. Por ejemplo, con una función que estudiaremos más adelante (solo te la mostraré como vista previa, no te preocupes) puedo decirle cómo debe llamarse el archivo y qué contenido escribir en él:

```php
<?php
$name = 'Juan';
file_put_contents('text.txt', $name);
```

Código completo: [listing-33.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/es/parte-02/cap-06/listing-33.php)


Ejecutamos el código y buscando en la carpeta PHP ha creado el archivo `text.txt` con el valor de nuestra variable dentro. Veremos todas las funciones para escribir en archivos a su debido tiempo (en el Capítulo 15): aquí solo quería mostrarle la importancia de las variables.
En el próximo capítulo veremos cómo declarar una variable, las convenciones de nomenclatura y los diferentes tipos de datos: las cadenas que ya hemos vislumbrado, números, booleanos, arrays, hasta clases y objetos.

## En resumen

- El código PHP vive entre la etiqueta de apertura `<?php` y la eventual etiqueta de cierre `?>`: todo lo que está fuera se devuelve tal cual. En un archivo PHP puro se debe omitir la etiqueta de cierre.
- Cada **declaración** termina con un punto y coma; el punto y coma cierra la declaración, no la línea.
- `phpinfo()` muestra versión, configuración (`php.ini`) y extensiones de la instalación de PHP: también útil para inspeccionar un hosting.
- Un script PHP se ejecuta desde la terminal con `php nombre-archivo.php` o vía servidor web: con la extensión VS Code PHP Server o con el servidor integrado `php -S localhost:puerto -t carpeta`. PHP adapta la salida al contexto en el que se ejecuta.
- Los comentarios se escriben con `//` (una sola línea) o `/* ... */` (bloque).
- `echo` escribe la salida dondequiera que se esté ejecutando PHP; `STDOUT` y `fwrite()` solo funcionan desde la línea de comando.
- PHP evalúa expresiones como `2 + 2`, pero sin `echo` no se ve el resultado y sin variable se pierde: `$result = 2 + 2;` es una **asignación**, que calcula la parte derecha y la almacena en la variable de la izquierda.
- PHP no es sólo web: desde la línea de comandos puedes copiar archivos, conectarte a bases de datos, llamar a API: es un lenguaje multipropósito.
