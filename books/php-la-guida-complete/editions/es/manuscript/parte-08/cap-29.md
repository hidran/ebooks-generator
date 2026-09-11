# 29. Composer y paquetes

En el capítulo anterior escribiste un autoloader a mano; Composer es la herramienta que te libera de ese trabajo y de mucho más. Es el **gestor de dependencias** estándar de PHP, y hace dos cosas que en el mundo moderno son inseparables de la idea misma de "proyecto": instala y mantiene actualizadas las librerías de terceros, declarando qué paquetes y qué versiones hacen falta, y genera automáticamente el **autoload PSR-4** — es decir, exactamente el mecanismo nombre-ruta del Capítulo 28, pero escrito y optimizado por ti. Es la herramienta que convierte un montón de ficheros `.php` en un proyecto manejable.

## Instalar Composer

Composer es un programa de línea de comandos que instalas una sola vez en el sistema. Para comprobar que está:

```bash
composer --version
```

Código completo: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-29/es/parte-08/cap-29/listing-01.sh)


Si el comando responde con un número de versión, estás listo. De lo contrario instálalo siguiendo el procedimiento oficial para tu sistema operativo: es una operación que se hace una vez, no en cada proyecto.

## `composer.json`

El corazón de todo es `composer.json`, el **manifiesto** del proyecto: un solo fichero que declara lo que hace falta.

```json
{
  "name": "hidran/php-guia",
  "require": {
    "php": "^8.5"
  },
  "autoload": {
    "psr-4": {
      "App\\": "src/"
    }
  }
}
```

Código completo: [listing-02.json](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-29/es/parte-08/cap-29/listing-02.json)


Léelo línea por línea, porque cada clave cuenta. `name` es la identidad del proyecto en la forma `vendor/paquete`. `require` enumera las dependencias: aquí solo está `php` con la restricción `^8.5`, donde el *caret* significa "esta versión o una posterior compatible" — es la sintaxis con la que declaras un rango en lugar de clavarte a una versión única. Y `autoload.psr-4` contiene el mapeo `App\ → src/`: es la convención del Capítulo 28, ahora escrita una sola vez en un sitio declarativo. Después de crear o modificar el fichero, pídele a Composer que genere el autoloader:

```bash
composer dump-autoload
```

Código completo: [listing-03.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-29/es/parte-08/cap-29/listing-03.sh)


Composer lee el mapeo PSR-4 y produce `vendor/autoload.php`: la versión industrial, y ya optimizada, del autoloader que en el capítulo pasado escribiste a mano.

## Usar el autoload de Composer

En el punto de entrada de la aplicación basta una línea:

```php
<?php
require __DIR__ . "/../vendor/autoload.php";

use App\Controllers\PostController;

$controller = new PostController();
```

Código completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-29/es/parte-08/cap-29/listing-04.php)


Ese único `require __DIR__ . "/../vendor/autoload.php"` sustituye **todos** los `require` manuales del Capítulo 28. A partir de ahora nombras una clase de `App\` — `PostController` — y Composer la carga por ti, calculando la ruta a partir del namespace. Fíjate también en la convención de la ruta: el autoload está en `vendor/`, el punto de entrada en `public/`, y desde ahí subes con `../`. Es la organización que reencontrarás en el proyecto MVC de la Parte IX.

## Instalar un paquete

El verdadero poder de Composer es dar acceso a todo un ecosistema de librerías ya escritas. En lugar de reinventar el envío de emails, instalas un paquete que ya lo hace:

```bash
composer require phpmailer/phpmailer
```

Código completo: [listing-05.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-29/es/parte-08/cap-29/listing-05.sh)


Con un comando Composer actualiza `composer.json` añadiendo la dependencia, crea o modifica `composer.lock` (llegamos enseguida) y descarga el código del paquete en `vendor/`. A partir de ese momento la librería está disponible a través del autoload, sin un solo `require` de más:

```php
<?php
use PHPMailer\PHPMailer\PHPMailer;

$mail = new PHPMailer(true);
```

Código completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-29/es/parte-08/cap-29/listing-06.php)


Este es el sentido de un gestor de dependencias: el código de terceros se integra en el tuyo con la misma naturalidad que tus propias clases, y reutilizas el mantenimiento hecho por otros en lugar de reescribir — y mantener — funcionalidades complejas como un cliente SMTP.

## `composer.lock`

Aquí hay una distinción que genera bastante confusión, y vale la pena aclararla bien. `composer.json` declara **restricciones** de versión — `^8.5` es un rango, no un número preciso. `composer.lock`, en cambio, registra las versiones **exactas** realmente instaladas, resueltas a partir de esas restricciones. En una aplicación el lock file **debe versionarse** en Git, y es la regla más importante del capítulo: hacer commit del lock garantiza que tu portátil, la máquina de un compañero, la CI y producción instalen todos las mismas versiones exactas, byte a byte. Sin él, cada uno resolvería las restricciones por su cuenta y acabarías con builds sutilmente distintas — el clásico "en mi máquina funciona". De ahí la diferencia entre los dos comandos:

```bash
composer install
composer update
```

Código completo: [listing-07.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-29/es/parte-08/cap-29/listing-07.sh)


`install` lee el lock file e instala **exactamente** esas versiones: es determinista, y es el comando que hay que usar en el deploy. `update`, en cambio, vuelve a calcular las versiones permitidas por las restricciones, descarga las más recientes y **reescribe** el lock. Es una operación que hay que hacer conscientemente, en tu entorno de desarrollo, probando lo que sale de ella: no lances nunca `update` a ciegas en producción, o corres el riesgo de actualizar media aplicación sin darte cuenta.

## Paquetes de GitHub

¿Cómo hace Composer para encontrar `phpmailer/phpmailer`? A través de **Packagist**, el índice público de los paquetes PHP, donde los autores publican sus librerías (a menudo alojadas en GitHub). Es de ahí de donde `require` toma por defecto:

```bash
composer require vendor/package
```

Código completo: [listing-08.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-29/es/parte-08/cap-29/listing-08.sh)


Si un paquete no está en Packagist, puedes declarar un repositorio personalizado dentro de `composer.json` y apuntar Composer directamente a un repo Git. Es posible, pero hazlo solo cuando de verdad haga falta: para empezar, limítate a los paquetes publicados y activamente mantenidos. Cada dependencia es código ajeno que entra en tu proyecto, y elegir librerías extendidas y cuidadas es una primera, concreta forma de seguridad de la *supply chain*.

## Scripts útiles

`composer.json` también puede contener **scripts**, es decir, atajos para los comandos recurrentes del proyecto:

```json
{
  "scripts": {
    "start": "php -S localhost:8000 -t public",
    "autoload": "composer dump-autoload"
  }
}
```

Código completo: [listing-09.json](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-29/es/parte-08/cap-29/listing-09.json)


Definido el script `start`, cualquiera que trabaje en el proyecto puede arrancar el servidor local con:

```bash
composer start
```

Código completo: [listing-10.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-29/es/parte-08/cap-29/listing-10.sh)


Es una forma simple pero eficaz de **documentar** los comandos del proyecto allí donde es natural buscarlos — en el `composer.json` — en lugar de confiarlos a un README que nadie lee. Quien llega nuevo no tiene que adivinar cómo se arranca la aplicación: le basta mirar los scripts.

## En resumen

Composer resuelve los dos problemas que, pasado el puñado de ficheros, todo proyecto PHP encuentra: las **dependencias** y el **autoload**. Con `composer.json` declaras en un solo sitio los paquetes, la versión de PHP requerida y el mapeo PSR-4; con `vendor/autoload.php` cargas todo — tu código y las librerías — de manera coherente y con una sola línea. Recuerda la pareja `composer.json`/`composer.lock`: el primero declara las restricciones, el segundo clava las versiones exactas, y debe hacerse commit para tener builds reproducibles en todas partes. En los próximos capítulos Composer será la base del proyecto MVC y la forma con la que integraremos librerías externas como PHPMailer: de aquí en adelante, todo proyecto serio parte de un `composer.json`.
