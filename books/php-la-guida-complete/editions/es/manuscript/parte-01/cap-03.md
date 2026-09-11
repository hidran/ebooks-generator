# 3. Instale PHP en macOS con Laravel Herd y Homebrew

En macOS, la forma más rápida de empezar a trabajar con PHP es utilizar Laravel Herd. Herd instala PHP, configura un servidor web local y permite cambiar la versión de idioma sin tener que modificar manualmente Apache, Nginx o archivos de configuración dispersos por el sistema.

El objetivo de este capítulo no es crear un entorno perfecto para cada escenario, sino tener una máquina lista para seguir el libro: ejecutar archivos PHP desde la terminal, abrir proyectos en el navegador, usar MySQL o MariaDB y prepararse para la depuración con Xdebug.

## Instalar Laravel Herd

Descargue Herd del sitio web oficial de Laravel e instálelo como una aplicación macOS normal. Una vez iniciado, Herd registra una carpeta de trabajo y pone a disposición sitios locales con dominios convenientes, generalmente usando extensiones como `.test`.

La principal ventaja es que no es necesario recordar la ruta al ejecutable PHP: Herd lo expone en la RUTA y también lo pone a disposición desde la terminal.

Para verificar la instalación abra la terminal y ejecute:

```bash
php -v
```

Código completo: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/es/parte-01/cap-03/listing-01.sh)


Si el comando muestra la versión de PHP, ya puedes crear el primer archivo:

```php
<?php
echo "PHP funciona en macOS";
```

Código completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/es/parte-01/cap-03/listing-02.php)


Guárdelo como `index.php` dentro de una carpeta de proyecto y ábralo con Herd o con el servidor integrado:

```bash
php -S localhost:8000
```

Código completo: [listing-03.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/es/parte-01/cap-03/listing-03.sh)


En su navegador visite `http://localhost:8000`. Si ve el mensaje impreso, el entorno está listo.

## Cambiar versión de PHP

Una razón para usar Herd es la gestión de versiones. A lo largo del libro encontrará características introducidas en PHP 7.4, PHP 8.0, PHP 8.1, PHP 8.2, PHP 8.4 y PHP 8.5. Es útil poder probar los ejemplos con diferentes versiones.

Desde Herd puedes seleccionar la versión global o la asociada a un sitio. Cuando se trabaja en un proyecto real, vale la pena verificar la versión requerida por el proyecto, a menudo declarada en `composer.json`:

```json
{
  "require": {
    "php": "^8.5"
  }
}
```

Código completo: [listing-04.json](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/es/parte-01/cap-03/listing-04.json)


La versión utilizada por el terminal y la utilizada por el servidor web deben coincidir. Muchos errores extraños surgen precisamente de esta diferencia: el comando `php -v` muestra una versión, mientras que el navegador usa otra.

## Instalar Homebrew

Homebrew es el administrador de paquetes más utilizado en macOS. Si bien Herd es suficiente para PHP, Homebrew es útil para instalar bases de datos, utilidades de terminal y herramientas como `wget`, `git`, `composer`, MariaDB o phpMyAdmin.

Compruebe si ya está presente:

```bash
brew --version
```

Código completo: [listing-05.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/es/parte-01/cap-03/listing-05.sh)


Si no está instalado, siga el comando proporcionado por el sitio oficial de Homebrew. Después de la instalación, cierre y vuelva a abrir el terminal, luego repita la verificación.

## Instalar MariaDB o MySQL

Para los capítulos de bases de datos puede utilizar MySQL o MariaDB. Para los propósitos del libro, las diferencias no son importantes: usaremos SQL estándar y funcionalidad común.

Con Homebrew puedes instalar MariaDB así:

```bash
brew install mariadb
brew services start mariadb
```

Código completo: [listing-06.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/es/parte-01/cap-03/listing-06.sh)


Luego ingresa al cliente:

```bash
mariadb
```

Código completo: [listing-07.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/es/parte-01/cap-03/listing-07.sh)


o, si tienes MySQL instalado:

```bash
mysql -u root
```

Código completo: [listing-08.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/es/parte-01/cap-03/listing-08.sh)


La primera comprobación a realizar es crear una base de datos de prueba:

```sql
CREATE DATABASE php_guia;
SHOW DATABASES;
```

Código completo: [listing-09.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/es/parte-01/cap-03/listing-09.sql)


Cuando la base de datos responde, PHP puede conectarse usando PDO, como veremos en capítulos posteriores.

## phpMyAdmin en macOS

phpMyAdmin no es imprescindible, pero ayuda mucho en las primeras etapas porque muestra bases de datos, tablas y registros de forma visual.

Con Homebrew puedes instalarlo:

```bash
brew install phpmyadmin
```

Código completo: [listing-10.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/es/parte-01/cap-03/listing-10.sh)


La configuración precisa depende del servidor web utilizado. Si estás siguiendo el libro para aprender PHP, no pierdas mucho tiempo en este punto: el cliente terminal es suficiente para entender SQL, y en los proyectos usaremos código PHP para leer y escribir datos.

## Configurar Xdebug

La depuración es el salto de calidad en comparación con el `var_dump()` disperso por todo el código. Xdebug le permite detener la ejecución en un punto de interrupción, ver el valor de las variables y avanzar línea por línea.

Con Herd la configuración se simplifica: comprueba en la configuración si Xdebug está disponible para la versión de PHP seleccionada. Desde la terminal puedes consultar los módulos cargados:

```bash
php -m | grep xdebug
```

Código completo: [listing-11.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/es/parte-01/cap-03/listing-11.sh)


Si el módulo está activo, configure el editor para escuchar conexiones de depuración. En Visual Studio Code la extensión típica es "PHP Debug"; El soporte para PhpStorm está integrado.

## Servicio de valet Laravel

Una alternativa a Herd es Laravel Valet. Valet crea dominios locales para las carpetas del proyecto y usa Nginx en segundo plano. Es más manual que Herd, pero sigue siendo muy utilizado.

La instalación pasa por Composer:

```bash
composer global require laravel/valet
valet install
```

Código completo: [listing-12.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/es/parte-01/cap-03/listing-12.sh)


Luego elija una carpeta y grábela:

```bash
cd ~/Sites
valet park
```

Código completo: [listing-13.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/es/parte-01/cap-03/listing-13.sh)


Una carpeta `blog` estará disponible como `http://blog.test`. Si estás empezando ahora, usa Herd; Si desea comprender mejor lo que sucede bajo el capó, Valet es un buen segundo paso.

## En resumen

En macOS puedes seguir el libro completo con Herd, un editor, Composer y MariaDB o MySQL. Homebrew complementa el entorno cuando se necesitan paquetes adicionales. Siempre verifica tres cosas: `php -v` desde la terminal, la versión de PHP utilizada por el navegador y la disponibilidad de la base de datos. Cuando estos tres elementos están alineados, puedes concentrarte en el código.
