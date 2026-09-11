# 2. Instalar PHP en Windows con Laragon

En este capítulo preparamos un entorno de desarrollo PHP completo en Windows usando **Laragon**: instalaremos el servidor web Apache, PHP y MySQL/MariaDB de una sola vez, escribiremos y ejecutaremos nuestro primer archivo PHP tanto desde la línea de comandos como en el navegador, configuraremos Visual Studio Code y Git Bash y aprenderemos a administrar múltiples versiones de PHP y la base de datos en la misma máquina. Al final tendrás una estación de trabajo esencialmente idéntica a la que uso todos los días para desarrollar.

¿Por qué Laragon? Porque es un entorno **portátil**: todo lo instalado reside dentro de una única carpeta, sin tocar los registros del sistema de Windows. Si algún día ya no quieres usarlo, simplemente elimina esa carpeta. Y sobre todo trivializa dos operaciones que resultan tediosas con otras herramientas: cambiar la versión de PHP y crear **hosts virtuales** locales para tus proyectos.

## Instalar Laragon

Laragon es un entorno de desarrollo para Windows que incluye todo lo que necesitamos: en la versión **completa** encontramos Apache 2.4, MySQL, memcached, gestión de registros, npm y Git, todo instalado en una única carpeta. Te aconsejo que descargues la versión completa: npm y Node se pueden usar para el frontend y también para desarrollar en el backend, y tener todo listo inmediatamente no cuesta nada.

### Descargar e instalar

Vaya al sitio web de Laragon, haga clic en **Descargar** y descargue *Laragon Full*. Una vez descargado el ejecutable, haga doble clic y acepte instalar la aplicación. El asistente te pregunta algunas cosas:

1. **El idioma.** Puedes dejar el inglés predeterminado o elegir italiano.
2. **La carpeta de instalación.** Por ejemplo `C:\laragon`; cualquier carpeta donde su usuario tenga permiso de escritura está bien.
3. **Inicio automático.** Puede iniciar Laragon cuando se inicia Windows: es conveniente si lo usará con frecuencia; de lo contrario, deseleccione la opción y ejecútelo manualmente.
4. **Hosts virtuales automáticos.** Dejar activa la opción que crea hosts virtuales para nuestros sitios: es una de las funciones más útiles de Laragon y la veremos en breve.
5. **Los elementos del menú contextual.** Puede agregar los elementos para abrir un archivo de texto con el Bloc de notas y abrir el terminal en una carpeta al botón derecho de Windows. Deja todo seleccionado.

Haga clic en **Siguiente** y luego en **Instalar**, espere unos segundos y la instalación se completará.

### Iniciar los servicios

Busca Laragon en el menú Inicio e inícialo (o, si has elegido el inicio automático, lo encontrarás ya activo: haz clic en la flechita en el área de notificación al lado del reloj y verás su icono). En la ventana principal, haga clic en **Iniciar todo**: Laragon inicia todos los servicios, y en particular Apache en el puerto 80 y MySQL.

Advertencia: si el puerto 80 ya está ocupado por otro sistema, Apache no se iniciará. El caso típico es tener **XAMPP** ya instalado: en este caso abra el panel de control de XAMPP y detenga Apache y MySQL antes de iniciar Laragon (o continúe con XAMPP, pero este capítulo está dedicado a Laragon). Alternativamente puedes cambiar los puertos desde las preferencias, como veremos enseguida.

### Preferencias

Al hacer clic en el ícono de ajustes se abren las preferencias de Laragon. Vale la pena revisarlos:
- **Inicio.** Puedes decidir si iniciar Laragon cuando se inicia Windows, si iniciarlo minimizado y si iniciar los servicios automáticamente.
- **Idioma.** Desde aquí puedes cambiar el idioma de la interfaz.
- **Document Root.** Es la carpeta raíz donde pondremos nuestros proyectos, por defecto `C:\laragon\www`. Si tiene proyectos antiguos en XAMPP, simplemente copie las carpetas de `htdocs` a `www`. Si prefieres guardar los proyectos en otro lugar (por ejemplo en `D:\projects`), puedes cambiar la raíz del documento aquí: a partir de ese momento el servidor web servirá los sitios de esa carpeta.
- **Directorio de datos.** Esta es la carpeta donde terminan los datos, por ejemplo, archivos de bases de datos MySQL.
- **Hosts virtuales automáticos.** Cuando creamos una aplicación en una subcarpeta de `www`, podremos acceder a ella desde el navegador con `nombre-carpeta.test`: Laragon automáticamente agrega el nombre al archivo `hosts` de Windows y crea el host virtual en Apache.
- **Servicios y Puertos.** Desde aquí cambias los puertos de los servicios: si el puerto 80 está ocupado puedes usar, por ejemplo, 8000 o 4000. Puedes habilitar SSL y ver o modificar los puertos nginx, Redis y memcached si los usas. En este libro utilizaremos principalmente Apache y MySQL.
- **Mail catcher.** Cuando utilizamos la función PHP `mail()` sin tener un servidor SMTP configurado, Laragon captura el envío y muestra una ventana con el contenido del correo electrónico: no se envía ningún correo electrónico real, pero podemos verificar que el código funciona. También hay una sección *Remitente de correo* donde puedes configurar una cuenta SMTP real, por ejemplo la de Gmail: lo probé y no funcionó; si quieres intentarlo, adelante, pero en el Capítulo 38 veremos cómo enviar correos electrónicos de manera confiable utilizando servicios dedicados.

### La versión PHP y sus extensiones.

Desde el menú de Laragon (haga clic derecho en el icono en el área de notificación, o en el botón **Menú** en la ventana) encontrará el elemento **PHP**. Aquí ve la versión activa (al momento de escribir, Laragon incluye, por ejemplo, 8.1.10) y más adelante en este capítulo veremos cómo instalar otra: simplemente copie la carpeta de la nueva versión en `bin\php` de Laragon y selecciónela en este mismo menú.

También desde el menú PHP puedes activar **Xdebug**, el depurador de PHP, a través del elemento de instalación rápida. Durante la mayor parte de este libro no los necesitaremos, pero cuando desee realizar una depuración real, encontrará el punto de partida aquí.

En el subelemento **Extensiones** encontrarás las extensiones de PHP que podemos habilitar o deshabilitar: por ejemplo `mbstring` y `pdo_mysql`, que usaremos en los proyectos, `gd` para gestionar imágenes y `fileinfo` para tener información de los archivos, ya seleccionados por defecto. Si necesita una extensión adicional, por ejemplo `opcache`, márquela aquí.

### Terminal Laragon (Cmder)

Una última cosa importante: Laragon incluye una terminal, **Cmder**, que se abre desde el botón **Terminal**. Utilice siempre este terminal cuando trabaje con Laragon, por dos razones. Primero: admite comandos de Linux (`ls`, `pwd`, etc.), los mismos que se usan en macOS y servidores de producción. Segundo: dentro de Cmder automáticamente tienes acceso a la versión de PHP activa en Laragon, sea cual sea. Sin embargo, con cualquier otro terminal, debemos agregar PHP a la variable de entorno `Path` de Windows y actualizarlo cada vez que cambiemos de versión. Lo haremos de todos modos en breve, porque es útil, pero recuerda la regla: en caso de duda, abre la terminal de Laragon y estarás seguro de que estás usando el PHP correcto.

Comprobemos inmediatamente que todo funciona. Abra la terminal y escriba:

```bash
php -v
```

Código completo: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/es/parte-01/cap-02/listing-01.sh)


```text
PHP 8.1.10 (cli) (built: ...)
```

Código completo: [listing-02.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/es/parte-01/cap-02/listing-02.txt)


PHP responde con su versión: el entorno está listo.

## El primer archivo PHP

Ahora que el entorno está instalado, escribamos el primer archivo PHP y aprendamos las dos formas básicas de ejecutarlo: desde la línea de comandos y a través del servidor web.

### Crea la carpeta y el archivo

En la ventana de Laragon haga clic en el botón **Root**: se abre la carpeta raíz `www` que hemos preparado para nuestros sitios, donde ya encontrará un archivo `index.php` predeterminado. Cree una nueva carpeta aquí y asígnele el nombre `test`.
Ingrese a la carpeta `test`, haga clic derecho, **Nuevo → Documento de texto** y cambie el nombre del archivo a `index.php`. Presta mucha atención a la extensión: el archivo debe llamarse exactamente `index.php` y no `index.php.txt`, de lo contrario PHP no lo interpretaría. El nombre no es aleatorio: `index.php` es el **archivo predeterminado** que el servidor web carga y ejecuta cuando visitamos una carpeta sin indicar el nombre de un archivo.

Abre el archivo con cualquier editor (en el siguiente párrafo instalaremos Visual Studio Code, que será nuestro editor para todo el libro) y escribe:

```php
<?php
echo '<h1>Hola mundo</h1>';
?>
<h2>Me llamo Juan</h2>
```

Código completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/es/parte-01/cap-02/listing-03.php)


Analicemos cada línea, porque aquí ya hay mucha sustancia:

- `<?php` es la **etiqueta de apertura** de PHP: indica al servidor web que a partir de este momento hay código PHP para ejecutar. `?>` es la etiqueta de cierre y **no es obligatoria** si el archivo contiene solo PHP y no lo mezclamos con HTML.
- Todo lo que está **fuera** de las etiquetas PHP se envía tal cual, como HTML: este es el caso de nuestro `<h2>` después de la etiqueta de cierre.
- `echo` es una construcción PHP que muestra contenido en la consola de salida: si ejecutamos el archivo desde la línea de comando, la salida termina en la terminal; si lo ejecutamos a través del servidor web, acaba en la página que recibe el navegador. Depende de cómo ejecutemos PHP.
- Cuando queremos mostrar una **cadena**, es decir, un fragmento de texto, la encerramos entre comillas. Y podemos poner HTML fácilmente dentro de una cadena, como la etiqueta `<h1>` en el ejemplo.
- En PHP cada declaración termina con un punto y coma. Cuando hay una sola línea antes de la etiqueta de cierre, se puede omitir el punto y coma, pero es una buena práctica colocarlo siempre.

Estudiaremos toda esta sintaxis en detalle en los próximos capítulos: por ahora sólo necesitamos verificar que PHP funciona. Guarde el archivo.

### Ejecute el archivo desde la línea de comando

Abra la terminal Laragon (botón **Terminal**, o haga clic derecho en el icono y luego en *Terminal*). La terminal se abre en la carpeta `www`: ingresemos a la carpeta de nuestro proyecto y verifiquemos qué contiene:

```bash
cd test
ls -la
```

Código completo: [listing-04.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/es/parte-01/cap-02/listing-04.sh)


`ls -la` es un comando de Linux (Cmder los admite) que enumera los archivos en la carpeta: verifique que `index.php` esté allí y no `index.php.txt`. Ahora ejecutamos el archivo pasando su nombre al comando `php`:

```bash
php index.php
```

Código completo: [listing-05.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/es/parte-01/cap-02/listing-05.sh)


```text
<h1>Hola mundo</h1>
<h2>Me llamo Juan</h2>
```

Código completo: [listing-06.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/es/parte-01/cap-02/listing-06.txt)


La salida aparece directamente en la consola. Tenga en cuenta que las etiquetas HTML **no** se procesan: el terminal no es un navegador, por lo que muestra el texto exactamente como PHP lo produce.

Esta pequeña prueba nos dice algo importante: PHP se puede utilizar **desde la línea de comandos**, como Python o Bash, pero también como **servicio de servidor web**. En ese segundo caso, Apache carga PHP como módulo, ejecuta el código y envía la salida PHP al navegador.

### Ejecute el archivo en el navegador

Volvamos a Laragon y hagamos clic en el botón **Web**: el navegador predeterminado se abre apuntando a `localhost`, es decir, la carpeta `www`. Para ingresar a nuestro proyecto agregamos una barra diagonal y el nombre de la carpeta:

```text
http://localhost/test
```

Código completo: [listing-07.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/es/parte-01/cap-02/listing-07.txt)


Aquí está nuestra página: "Hola mundo" como título grande y "Me llamo Juan" como título más pequeño. Funciona porque en la carpeta `test` está el archivo `index.php`, el cual se ejecuta por defecto cuando no indicamos ningún archivo; de hecho, incluso escribiendo explícitamente `http://localhost/test/index.php` obtenemos el mismo resultado. Si hace clic derecho y elige *Ver código fuente*, verá `<h1>` seguido de `<h2>`: exactamente el mismo resultado que vimos en la terminal, solo que el navegador lo muestra aquí.

Dos aclaraciones prácticas antes de continuar:

- Para ejecutar PHP **desde la línea de comando** el código puede estar en cualquier carpeta del disco: si desea crear sus scripts en `D:\projects`, está bien.
- Para acceder a las carpetas **a través del servidor web Laragon** (`localhost/nombre-carpeta`), las carpetas deben estar dentro de `www` — o debes cambiar la raíz del documento en la configuración, como hemos visto, para que apunte a la carpeta donde guardas los sitios.
Y recuerda: la terminal de Laragon siempre usa PHP activo en Laragon. Sin embargo, si abre el símbolo del sistema de Windows o PowerShell y ejecuta `php -v`, no se garantiza que se encuentre el PHP de Laragon: podría haber otro PHP en el sistema `Path`, o ninguno en absoluto. Arreglemos esto de inmediato.

## Agregar PHP a la RUTA de Windows

Agregar PHP a la variable de entorno **Path** significa poder ejecutar el comando `php` desde cualquier terminal y desde cualquier carpeta, no solo desde Cmder.

Primero busquemos la carpeta correcta. Si ha instalado Laragon en `C:\laragon`, abra la carpeta `C:\laragon\bin`: aquí encontrará todos los programas incluidos: Apache, Cmder, Composer y el resto del software que agregaremos a Laragon. En la subcarpeta `php` se encuentran todas las versiones instaladas de PHP. Si tienes más de una, comprueba cuál está activa: haz clic derecho en el icono de Laragon, **PHP → Versión**, y mira la versión seleccionada. Abra la carpeta de esa versión: contiene el archivo `php.exe`, el ejecutable de PHP. Copie la ruta completa de la carpeta desde la barra de direcciones, por ejemplo:

```text
C:\laragon\bin\php\php-8.1.10-Win32-vs16-x64
```

Código completo: [listing-08.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/es/parte-01/cap-02/listing-08.txt)


Ahora agreguémoslo a `Path`. En Windows 10 y 11:

1. Busque "variables" en el menú Inicio y abra **Editar variables de entorno relacionadas con el sistema**.
2. Haga clic en el botón **Variables de entorno**.
3. Puede agregar la ruta a nivel de usuario o a nivel de sistema: seleccione la variable **Ruta** (por ejemplo, la del usuario), luego **Editar**.
4. Haga clic en **Nuevo**, pegue la ruta de la carpeta donde se encuentra `php.exe` y confirme con **Aceptar** en todas las ventanas.

En este punto, abra cualquier terminal (busque `cmd` y abra el símbolo del sistema) y ejecute:

```bash
php -v
```

Código completo: [listing-09.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/es/parte-01/cap-02/listing-09.sh)


Si responde con la versión PHP, eso es todo: puedes iniciar PHP desde cualquier carpeta de tu sistema. También puedes ejecutar:

```bash
php -i
```

Código completo: [listing-10.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/es/parte-01/cap-02/listing-10.sh)


que imprime toda la información de PHP: al desplazarse por la salida verá la configuración completa y lo que está instalado.

Una advertencia basada en la experiencia: la versión en `Path` y la que está activa en el servidor web pueden diferir. Si activa 8.2 en Laragon pero ha dejado la carpeta 8.1 en `Path`, continuará usando 8.1 desde el símbolo del sistema. Por lo tanto, cada vez que cambia de versión, actualiza `Path` (eliminando la ruta anterior y pegando la nueva) o usa la terminal Laragon, que siempre apunta a la versión activa.

## Código de Visual Studio y Git Bash

Ahora que tenemos un servidor web con PHP incluido y una terminal con comandos de Linux, necesitamos un buen editor. En este libro usaremos **Visual Studio Code** (VS Code): es gratuito, liviano y con las extensiones adecuadas se convierte en un excelente entorno para PHP. Si tu empresa ya utiliza NetBeans o PhpStorm, está bien: lo que veremos aquí es una alternativa. En el Capítulo 5 profundizaremos en VS Code; Aquí hacemos la instalación y configuración mínima para funcionar.

### Instalar VS Code y extensiones para PHP

Vaya al sitio web de Visual Studio Code, haga clic en **Descargar**, descargue la versión de Windows e instálela. Al iniciar por primera vez aparece una ventana de bienvenida: VS Code se puede utilizar para PHP, Python, C#, cualquier idioma; para adaptarlo a PHP necesitamos instalar algunas extensiones.

Haga clic en el ícono **Extensiones** en la barra lateral (o presione `Ctrl+Shift+X`) y busque "PHP". Recomiendo estas extensiones:

- **PHP Intelephense**: proporciona autocompletado de código PHP: sugiere funciones, parámetros y documentación a medida que escribe.
- **PHP Debug**: le permite utilizar Xdebug para depurar código.
- **Paquete de extensión PHP**: un paquete que ya incluye PHP Debug e Intelephense: al instalarlo, obtienes ambos de una sola vez.
- **Servidor PHP**: una extensión muy conveniente que ejecuta un servidor PHP sin abrir la terminal: simplemente haga clic derecho en el archivo y elija servir el proyecto como una página web. Es lo mismo que podemos hacer manualmente desde la línea de comandos, como veremos en breve.

Estos son los mínimos indispensables para PHP. Luego, dependiendo del framework que uses, puedes agregar otros: por ejemplo, si trabajas con Laravel, busca "Laravel" y encontrarás extensiones como *Laravel Extra Intellisense*, *Laravel Artisan* para comandos Artisan y snippets para plantillas Blade.
### El terminal integrado

VS Code incluye una terminal incorporada: abra el menú **Ver → Terminal** (o **Terminal → Nueva terminal**, o el acceso directo `Ctrl+`` con la comilla invertida). De forma predeterminada, en Windows se abre **PowerShell**.

A lo largo del libro usaré comandos de Linux. ¿Por qué? Por qué PHP se usa normalmente en Linux: cuando implementas una aplicación PHP, incluso en Azure o Amazon, casi siempre seleccionarás una máquina Linux. Por tanto, es aconsejable acostumbrarse inmediatamente a los mismos comandos. Para las operaciones más simples, PowerShell es suficiente: si escribes `pwd` te dice en qué carpeta estás y `ls` enumera los archivos, porque muchos comandos de PowerShell son similares a los de Bash. Pero para tener una verdadera terminal estilo Unix en Windows hay dos maneras: instalar **WSL** (Subsistema de Windows para Linux) con una máquina Ubuntu y programar directamente allí, o, mucho más simple, instalar **Git Bash**.

Un par de gestos útiles en el terminal integrado: al pasar el cursor sobre un terminal abierto, puedes cerrarlo haciendo clic en el icono de la papelera; con la flecha al lado del botón `+` elige qué tipo de terminal abrir.

### Instalar Git Bash

Git Bash viene con **Git para Windows**: busque "git bash" en su navegador y abra el sitio oficial, `git-scm.com/downloads`. Hay versiones para macOS, Linux y Windows: haga clic en **Descargar para Windows** y elija la versión de 64 bits (alternativamente, puede instalarla desde PowerShell con `winget install`, o hacer clic directamente en el enlace "Haga clic aquí para descargar la última versión").

Al instalarlo obtienes dos cosas juntas:

1. **Un terminal tipo bash**, como si estuviéramos en Linux o macOS, es decir, en un sistema basado en Unix: puedes usar los mismos comandos que aprendes para Linux aquí, y no tendrás dificultad para ejecutar comandos bash en Windows.
2. **Git**, el sistema de control de versiones: lo necesitarás para guardar cambios de código y, por ejemplo, compartir tus proyectos en GitHub.

Ejecute el archivo descargado, permita que la aplicación realice cambios en el sistema, haga clic en **Siguiente** y luego en **Instalar**. Una vez terminado, puede iniciar Git Bash inmediatamente: la consola se abre con el mensaje que termina con el símbolo `$` (que indica el mensaje de bash: no debe estar escrito en los comandos). Hagamos dos pruebas:

```bash
pwd
ls -l
```

Código completo: [listing-11.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/es/parte-01/cap-02/listing-11.sh)


`pwd` significa *imprimir directorio de trabajo* y le indica en qué carpeta se encuentra; `ls -l` (*lista*) enumera los archivos con sus propiedades; con `cd nombre-carpeta` ingresas a una carpeta. Estos son los comandos que usaremos continuamente: para un programador PHP conocer los principales comandos bash es muy importante.

### Git Bash como terminal VS Code predeterminado

Ahora configuremos Git Bash como la terminal predeterminada para VS Code. El método más rápido: abra la terminal, haga clic en la flecha junto a `+` y elija **Seleccionar perfil predeterminado**; en la lista que aparece, están todos los terminales disponibles: PowerShell, Git Bash y posiblemente Ubuntu si tiene WSL, seleccione **Git Bash**. De ahora en adelante, cada nueva terminal (y cada reinicio de VS Code) se abrirá directamente en bash.

Alternativamente puedes pasar por la configuración: desde la misma flecha elige *Configurar ajustes de terminal* y busca el perfil de terminal para Windows, donde se debe indicar la ruta al ejecutable de bash, que suele ser:

```text
C:\Program Files\Git\bin\bash.exe
```

Código completo: [listing-12.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/es/parte-01/cap-02/listing-12.txt)


Si no lo encuentra allí, abra el Explorador de Windows, vaya a `Program Files\Git`, busque el ejecutable y haga clic derecho → *Propiedades* (o *Copiar como ruta*) para recuperar la ruta exacta para pegar. Cierra y vuelve a abrir VS Code, abre la terminal: se posiciona en Git Bash.

### Un proyecto de prueba con VS Code

Juntémoslo todo con una pequeña prueba. En VS Code, vaya a **Archivo → Abrir carpeta** y cree una carpeta para sus proyectos: por ejemplo, dentro de *Documentos*, haga clic derecho → *Nueva carpeta* y asígnele el nombre `php`. Selecciónelo y confirme que confía en la carpeta (*trust*). Ahora cree un archivo: haga clic en el icono *Nuevo archivo* con el símbolo `+` (o **Archivo → Nuevo archivo**) y asígnele el nombre `index.php`. Como hemos visto, `index.php` suele ser el primer archivo creado en una carpeta, porque es el que ejecuta por defecto el servidor web.

Escribamos dentro:

```php
<?php
phpinfo();
```

Código completo: [listing-13.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/es/parte-01/cap-02/listing-13.php)


`phpinfo()` es una función PHP global que imprime una página con toda la información de instalación. Tenga en cuenta el punto y coma: cada declaración en PHP debe terminar con `;`. Y observe nuevamente la etiqueta `<?php`: PHP se puede usar *incrustado* en una página HTML, es decir, podemos mezclar PHP y HTML en el mismo archivo, por lo que la única forma de decirle al analizador dónde comienza el código PHP es abrir esta etiqueta.

Guarde el archivo y haga clic derecho en el área del editor: gracias a la extensión PHP Server aparece la entrada **PHP Server: Serve project**. Selecciónelo: el navegador se abre automáticamente en `localhost` en el puerto 3000, con `index.php` ejecutado. Veamos la página `phpinfo()` con la versión de PHP —en mi caso 8.3.12— y toda la configuración.

Ahora lo mismo desde la línea de comando. Abra la terminal incorporada; ya se abre en la carpeta del proyecto. Verificamos que PHP esté en `Path` y luego ejecutamos el archivo:

```bash
php -v
php index.php
```

Código completo: [listing-14.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/es/parte-01/cap-02/listing-14.sh)


El primer comando muestra la versión (si responde significa que podemos ejecutar PHP desde cualquier carpeta); el segundo ejecuta el archivo y vierte todo el HTML producido por `phpinfo()` en la terminal.

Hagamos una prueba más clara con un segundo archivo. Crear `test.php`:

```php
<?php
echo 2 + 2;
```

Código completo: [listing-15.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/es/parte-01/cap-02/listing-15.php)


En la terminal, escriba `clear` para borrar la pantalla, luego:

```bash
php test.php
```

Código completo: [listing-16.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/es/parte-01/cap-02/listing-16.sh)


```text
4
```

Código completo: [listing-17.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/es/parte-01/cap-02/listing-17.txt)


Aparece `4`, porque `echo` escribe la salida donde se ejecuta PHP: en la terminal si ejecutamos PHP desde la línea de comandos, en una página web si pasa por un servidor web.

Y hablando de servidores web: PHP tiene uno **integrado**, que podemos ejecutar sin extensiones y sin Apache. La sintaxis es `php -S host:puerto`:

```bash
php -S localhost:4000 index.php
```

Código completo: [listing-18.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/es/parte-01/cap-02/listing-18.sh)


`-S` indica que queremos iniciar un servidor; `localhost` es el host (estamos en nuestra computadora); después de los dos puntos está el puerto en el que queremos servir la página, por ejemplo 4000; finalmente el archivo a servir. Escriba `Ctrl+click` en la URL que se muestra en el terminal (o cópiela en el navegador): funciona exactamente como el servidor web de la extensión PHP Server. Sin embargo, tenga cuidado si abre el archivo directamente desde el Explorador en el navegador: no funcionará, porque el archivo sólo será leído y no ejecutado por PHP.

Finalmente, verifiquemos el autocompletado de Intelephense. Reemplace el contenido de `index.php` con una prueba de cadena: tan pronto como escriba `str` aparece la lista de funciones que comienzan así, incluida `strpos()`. Al seleccionarlo, VS Code nos muestra la firma: el primer parámetro es la cadena a buscar, el segundo es lo que estamos buscando; la función devuelve la **posición** donde se encuentra la subcadena.

```php
<?php
echo strpos('Imparo PHP', 'PHP');
?>
<h2>Test in PHP</h2>
```

Código completo: [listing-19.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/es/parte-01/cap-02/listing-19.php)


Vuelva a cargar la página del servidor web (o vuelva a ejecutar `php index.php` en la terminal): la salida es `7`. Podemos contar: recuerde que **las posiciones comienzan en cero** (cero, uno, dos, tres, cuatro, cinco, seis, siete) y, de hecho, la documentación lo dice explícitamente: *la posición de la cadena comienza en 0, y no en 1*. La función devuelve la posición donde se encuentra lo que buscamos, respecto al inicio de la cadena.

También tenga en cuenta la etiqueta `<h2>` fuera del bloque PHP: en el navegador se representa "Prueba en PHP", y mirando el código fuente de la página lo vemos escrito exactamente como en el archivo. PHP sólo interpreta la parte encerrada en sus etiquetas: envía el resto tal como está.

### Sincroniza tu configuración

Un último consejo sobre VS Code: en las preferencias puedes activar la sincronización de configuraciones iniciando sesión con una cuenta de GitHub o Microsoft. Si no tienes una cuenta de GitHub, te recomiendo crear una: además de usarse para compartir código, te permite sincronizar configuraciones y extensiones, por lo que cuando uses VS Code en otra computadora encontrarás todo el entorno configurado. VS Code ofrece mucho más (extensiones para bases de datos, para llamadas a API REST, para Docker) y las veremos cuando sean necesarias; Mientras tanto, familiarícese con el editor: abra el archivo, guárdelo, pruebe la configuración.

## Instale una nueva versión de PHP y cree hosts virtuales con Apache
Una de las grandes ventajas de Laragon es poder mantener varias versiones de PHP una al lado de la otra y cambiar entre ellas con un solo clic. Veamos cómo instalar una nueva versión y, mientras lo hacemos, descubramos cómo Laragon crea hosts virtuales Apache para nuestros proyectos.

Primero, dos herramientas útiles del menú de Laragon. En **Apache** encontrará el archivo de configuración del servidor web y los comandos para detenerlo y reiniciarlo. En **PHP**, además de las extensiones que ya hemos visto, hay un acceso rápido al archivo `php.ini` con todas las configuraciones de PHP: si por ejemplo buscas `display_errors` lo encontrarás activo, y con razón, cuando desarrollamos está bien que se muestren errores de PHP, porque estamos en desarrollo y no en producción.

### Descargar una nueva versión de PHP

Supongamos que quieres instalar PHP 8.2 (al momento de escribir es el más reciente; si cuando lees hay una versión más nueva, el procedimiento es idéntico). Vaya al sitio web de PHP, `php.net`, y siga el enlace **Descargas de Windows**: verá las diferentes versiones disponibles. Para cada uno hay múltiples variaciones y hay que elegir:

- **La arquitectura.** Comprueba la versión de tu Windows: normalmente es `vs16 x64`, es decir, 64 bits.
- **Thread Safe o Non Thread Safe.** Para el desarrollo no hay diferencia: podemos elegir **Non Thread Safe** (NTS).

Descarga el archivo zip. En la carpeta de descargas, haz clic derecho → **Extraer todo** e indica la carpeta a extraer (si quieres, puedes instalar el programa **7-Zip**, que es más rápido que la extracción integrada de Windows, pero el resultado es el mismo). Obtenga una carpeta descomprimida con PHP dentro: cópiela y péguela en la carpeta de versiones PHP de Laragon:

```text
C:\laragon\bin\php\
```

Código completo: [listing-20.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/es/parte-01/cap-02/listing-20.txt)


Se aplica exactamente el mismo procedimiento si quisiéramos instalar una nueva versión de Apache o MySQL: descargar el zip, extraer y copiar la carpeta en la subcarpeta respectiva de `C:\laragon\bin`.

### Activar la nueva versión

Regrese a Laragon: haga clic derecho en el ícono → **PHP → Versión** y también verá 8.2 en la lista, simplemente porque colocamos la carpeta en el lugar correcto. Selecciónelo para activarlo.

¿Cómo comprobamos que realmente estamos en 8.2? Desde el menú de PHP se selecciona la versión, pero si hacemos clic en **Web** y miramos la página principal de Laragon, la información de PHP sigue diciendo 8.1. ¿Por qué? Porque activamos la nueva versión, pero Apache aún no la ha recogido: necesitamos reiniciarla. Haga clic derecho → **Apache → Recargar** (o *Reiniciar*), luego vuelva a cargar la página: ahora aparece 8.2, y al hacer clic en el enlace de información vemos la configuración completa de la nueva versión.

Dos recordatorios importantes al cambiar de versión:

1. **Las extensiones deben reactivarse.** Cada versión de PHP tiene su propio `php.ini`: después del cambio, regresa a **PHP → Extensiones** y activa las extensiones que necesitas nuevamente (las predeterminadas ya están allí, pero todo lo que agregaste debe volver a habilitarse).
2. **La RUTA debe actualizarse.** Abra la terminal Laragon y ejecute `php -v`: verá 8.2, porque la terminal Laragon siempre apunta a la versión activa. Pero si abre el símbolo del sistema normal de Windows y ejecuta el mismo `php -v`, aún obtendrá 8.1: es el que está en `Path`. Para tener 8.2 en cualquier terminal, regrese a las variables de entorno como lo hicimos la primera vez: busque "variables de entorno", abra **Variables de entorno → Ruta → Editar**, elimine la ruta anterior de PHP y pegue la de la nueva carpeta, luego confirme con **Aceptar** en todas las ventanas. Abra una terminal **nueva** (las que ya están abiertas conservan la configuración anterior) y `php -v` mostrará 8.2.

### Hosts virtuales automáticos Apache

¿Recuerda la carpeta `test` creada en `www`? Laragon ya le ha dedicado un **host virtual** Apache, automáticamente. Vamos a verlo: en el menú, bajo **Apache**, encuentras la entrada con sitios habilitados (`sites-enabled`), y hay un archivo de configuración creado para `test`. Al abrirlo ves la directiva `VirtualHost` con la **raíz del documento** apuntando a `C:/laragon/www/test`, el **nombre del servidor** establecido en `test.test`, y también la sección con los certificados, si queremos conectarnos vía SSL.

¿Qué significa esto en la práctica? Eso si abrimos una pestaña del navegador y escribimos:

```text
http://test.test
```

Código completo: [listing-21.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/es/parte-01/cap-02/listing-21.txt)


vemos nuestra carpeta con el archivo `index.php` ejecutado — lo mismo que sucede cuando visitamos `localhost/test`, porque la carpeta `test` está bajo la raíz de `localhost`. La ventaja es poder darle a nuestros sitios locales un nombre real: el nombre de la carpeta con la extensión `.test`, un dominio ficticio que el navegador no buscará en Internet sino que resolverá localmente. Cada vez que creamos una nueva carpeta en `www`, Laragon creará automáticamente el host virtual correspondiente.

¿Cómo sabe el navegador que `test.test` es local? Gracias al archivo de Windows `hosts`. Abramos:

```text
C:\Windows\System32\drivers\etc\hosts
```

Código completo: [listing-22.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/es/parte-01/cap-02/listing-22.txt)


En este archivo se definen los nombres resueltos localmente: está `127.0.0.1 localhost` (la IP 127.0.0.1 es precisamente la de localhost) y Laragon ha agregado la línea para `test.test`. Cuando visitamos ese nombre, Windows lo resuelve en la IP local y Apache nos sirve la carpeta correspondiente.

Si `test.test` no funciona, casi siempre significa que Laragon no tiene derechos de administrador para escribir en `System32` y actualizar el archivo `hosts`. En ese caso puedes hacer a mano lo que Laragon hace automáticamente: abrir el archivo `hosts` como administrador y agregar la línea:

```text
127.0.0.1 test.test
```

Código completo: [listing-23.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/es/parte-01/cap-02/listing-23.txt)


Si desea definir varios sitios en la misma línea, separe los nombres con un espacio. Pero normalmente no es necesario: Laragon lo hace todo él mismo.

## Instale MySQL o MariaDB y use HeidiSQL

Cerramos el capítulo con la base de datos. **MariaDB** es la bifurcación de código abierto de MySQL, compatible con él: para nuestros propósitos, los dos son intercambiables, y te mostraré cómo instalar la última versión de uno u otro. Cualquier versión de MySQL 8 y superiores funcionará para este libro (entraremos en más detalles sobre MySQL en el Capítulo 18).

### Instalar una nueva versión de la base de datos.

Laragon ya viene con una versión de MySQL: desde el menú, en **MySQL → Versión**, puedes ver la incluida, por ejemplo 8.0.30. En el momento del registro la última versión de MySQL es la 8.4, pero ojo: esa versión **no funciona con Laragon**. No hay problema: instalamos la última versión de MariaDB, exactamente con el mismo procedimiento que usarías para una versión compatible de MySQL.

1. Busque MariaDB en su navegador y vaya a la página de **descarga** del sitio web oficial.
2. Elige la versión: actualmente 11.3.2, o en todo caso la versión estable disponible al leer estas páginas.
3. Seleccione Windows con arquitectura `x86_64` como sistema operativo.
4. **No** elija el instalador como tipo de paquete (el que instala MariaDB directamente en el sistema): para usarlo con Laragon seleccione el **archivo ZIP** y haga clic en descargar.
5. Cuando el archivo esté en la carpeta de descargas, descomprímalo: con 7-Zip elija *Extraer* e indique la carpeta `C:\laragon\bin\mysql` como destino (o su equivalente, si ha instalado Laragon en otro lugar). Alternativamente, extraiga el zip y copie la carpeta descomprimida en `C:\laragon\bin\mysql`.

Al abrir `C:\laragon\bin\mysql` verás las diferentes versiones de MySQL o MariaDB una al lado de la otra, cada una con su propia subcarpeta `bin`; Laragon también crea automáticamente el archivo `my.ini` con la configuración predeterminada.

Ahora activemos la nueva versión: menú → **MySQL** (el elemento se llamará *MariaDB* una vez que se haya seleccionado una versión de MariaDB) → **Versión**, seleccione la versión que acaba de copiar y luego haga clic en **Iniciar todo** para iniciar el servicio. Si necesita cambiar el puerto de la base de datos, puede encontrarlo en las preferencias en *Servicios y puertos*.

### HeidiSQL: crear una base de datos y una tabla

Para trabajar con la base de datos necesitamos un cliente. Laragon incluye **HeidiSQL**: haga clic en el botón **Base de datos** y HeidiSQL se abre con una sesión ya configurada (usuario `root`, sin contraseña predeterminada), luego simplemente haga clic en **Abrir** para conectarse.

Creemos nuestra primera base de datos: haga clic derecho en el panel izquierdo → **Crear nueva → Base de datos**. Le damos el nombre `test` y como *intercalación* elegimos `utf8mb4_general_ci`: de esta manera admitimos caracteres de todos los idiomas. La base de datos `test` aparece en la lista.

Ahora creemos una tabla: haga clic derecho en la base de datos → **Crear nueva → Tabla** y llámela `test_table`. Con el botón **Agregar** agregamos las columnas una a la vez:
- **`name`** — tipo de datos `VARCHAR` (haga doble clic en la celda de tipo para seleccionarla) con longitud `500`. En la columna *Allow NULL* decidimos si, al insertar un registro, el nombre puede quedar vacío: decimos que no, por lo tanto `NOT NULL`.
- **`age`** — para la edad elegimos el tipo correcto: un `TINYINT`, que de *signed* va de -128 a 127 y de *unsigned* va de 0 a 255. Una edad nunca es negativa, así que marcamos **Unsigned**; y permitimos que el campo permanezca vacío, por lo que *Allow NULL* sí.
- **`salary`** — para un salario necesitamos un valor real: seleccionamos `DECIMAL` con precisión 20, de los cuales 6 son decimales.
- **`id`** — la columna de identificación: escriba `INT`, **Unsigned** (será un contador, nunca negativo), `NOT NULL`. Sobre esta columna hacemos clic derecho → **Crear nuevo índice → PRIMARIO**: es decir, la configuramos como **clave principal**, lo que significa que identifica de forma única un registro en nuestra tabla. Finalmente, en la celda de valor predeterminado, elegimos **AUTO_INCREMENT**: el valor se incrementa automáticamente con cada inserción, por lo que nunca tendremos que ingresar el ID manualmente.

Haga clic en **Guardar** y se creará la tabla. En la pestaña de definición, HeidiSQL también muestra el código SQL correspondiente, que es el equivalente a:

```sql
CREATE TABLE test_table (
  name   VARCHAR(500) NOT NULL,
  age    TINYINT UNSIGNED NULL,
  salary DECIMAL(20,6) NULL,
  id     INT UNSIGNED NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (id)
);
```

Código completo: [listing-24.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/es/parte-01/cap-02/listing-24.sql)


Con el clic derecho sobre la tabla tienes las operaciones principales: *Editar* para modificar su estructura, *Soltar* para eliminarla (o vaciarla de todos los registros), exportar datos, etc.

### Ingrese datos y ejecute consultas

Pasemos a la pestaña **Datos** de la tabla: aquí podemos introducir los datos. Haga clic en el signo `+` para agregar una fila y completar los campos: como `name`, pongamos por ejemplo `juan`, y como `salary`… pongamos un buen salario de 100.000, tal vez. Tenga en cuenta que `id` se inserta automáticamente con el valor `1`, gracias al incremento automático. Puedes guardar con el ícono de guardar, pero los datos también se guardan automáticamente cuando sales de la línea.

Ahora la pestaña **Consulta**, donde podemos escribir y ejecutar consultas SQL. Una selección:

```sql
SELECT * FROM test_table;
```

Código completo: [listing-25.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/es/parte-01/cap-02/listing-25.sql)


Haga clic en el icono de ejecución y vea el registro seleccionado. Probemos una actualización:

```sql
UPDATE test_table SET name = 'Juan Arias' WHERE id = 1;
```

Código completo: [listing-26.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/es/parte-01/cap-02/listing-26.sql)


Ejecutémoslo, volvamos a la pestaña *Datos* y hagamos clic en el ícono **actualizar**: el nombre ahora es "Juan Arias". Esta es sólo una descripción general de lo que podemos hacer con HeidiSQL; Aún puedes conectarte a este servidor con cualquier otro cliente, por ejemplo **DBeaver**, que puedes encontrar fácilmente buscándolo y descargándolo desde su sitio.

### El cliente mysql desde la línea de comando

Ciertamente también podemos conectarnos a la base de datos desde la línea de comando. El cliente `mysql` está ubicado en la carpeta `bin` de la versión instalada, por ejemplo `C:\laragon\bin\mysql\<versión>\bin`: abra esa carpeta, haga clic derecho → *Abrir en terminal* y conéctese con:

```bash
mysql -u root
```

Código completo: [listing-27.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/es/parte-01/cap-02/listing-27.sh)


Sin embargo, sólo funciona si estás dentro de esa carpeta `bin`; para usar `mysql` desde cualquier ubicación debemos, como para PHP, agregarlo a las variables de entorno: copie la ruta a la carpeta `bin`, busque "variables de entorno", abra **Variables de entorno**, seleccione **Ruta → Editar → Nuevo** y pegue la ruta (puede hacerlo a nivel de usuario o sistema). Cierra y vuelve a abrir la terminal, y desde cualquier carpeta:

```bash
mysql -u root -p
```

Código completo: [listing-28.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/es/parte-01/cap-02/listing-28.sh)


`-u root` indica el usuario, `-p` pide la contraseña: déjalo en blanco y presiona Enter, porque por defecto no hay contraseña. Una vez dentro podemos explorar el servidor, recordando finalizar cada comando con un punto y coma:

```sql
SHOW DATABASES;
USE test;
SHOW TABLES;
SELECT * FROM test_table;
```

Código completo: [listing-29.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/es/parte-01/cap-02/listing-29.sql)


`SHOW DATABASES` enumera las bases de datos y entre estas vemos `test`; `USE test` lo selecciona; `SHOW TABLES` muestra las tablas, incluida la nuestra `test_table`; y el `SELECT` devuelve los datos ingresados. Interactuar con MySQL desde la línea de comandos es un poco más desafiante, porque debemos tener cuidado con los comandos que escribimos; en la práctica puedes utilizar la línea de comandos, HeidiSQL o cualquier otro cliente que tengas instalado.

## En resumen
- **Laragon** es un entorno de desarrollo portátil para Windows: Apache, PHP, MySQL, npm y Git en una sola carpeta, sin tocar los registros del sistema; para desinstalarlo simplemente elimine la carpeta.
- Los proyectos atendidos por el servidor web se encuentran en la **raíz del documento** `www`; con **Start All** inicias los servicios, y si el puerto 80 está ocupado (por ejemplo por XAMPP) puedes cambiarlo o detener el otro entorno.
- Un archivo PHP comienza con la etiqueta `<?php`; todo lo que esté fuera de las etiquetas se envía como HTML. `echo` escribe la salida en la terminal o página web, dependiendo de cómo ejecute PHP: `php file.php` desde la línea de comando, o a través de Apache visitando `localhost/carpeta` (donde `index.php` es el archivo predeterminado).
- Al agregar la carpeta `php.exe` a la variable de entorno **Ruta**, puede iniciar `php` desde cualquier terminal; la terminal Laragon (Cmder) siempre apunta a la versión activa.
- **VS Code** con las extensiones *PHP Intelephense*, *PHP Debug* y *PHP Server* es un excelente editor para PHP; **Git Bash** te ofrece Git y una terminal bash estilo Linux, que puedes configurar como predeterminada en VS Code. Con `php -S localhost:puerto` inicias el servidor web integrado de PHP.
- Para instalar una **nueva versión de PHP** simplemente descargue el zip (x64, Non Thread Safe) de php.net, extráigalo en `C:\laragon\bin\php` y actívelo desde el menú; luego recuerde reiniciar Apache, reactivar las extensiones y actualizar `Path`.
- Para cada carpeta bajo `www` Laragon crea automáticamente un **host virtual** Apache (`nombre-carpeta.test`) y la entrada correspondiente en el archivo `hosts` de Windows; si no tiene permisos, puede agregar la línea `127.0.0.1 nombre.test` a mano.
- Las nuevas versiones de **MySQL/MariaDB** se instalan copiando el zip extraído en `C:\laragon\bin\mysql` y seleccionándolos en el menú; con **HeidiSQL** creas bases de datos, tablas (columnas, tipos, clave principal, incremento automático) y ejecutas consultas, mientras que el cliente `mysql` hace lo mismo desde la línea de comandos.
