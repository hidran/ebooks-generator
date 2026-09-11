# 39. Entornos y herramientas avanzados

En este libro utilizamos diferentes herramientas: Laragon, Herd, XAMPP, Homebrew, Valet, Visual Studio Code, PhpStorm, NetBeans, Xdebug, Apache, phpMyAdmin. No es necesario utilizarlas todas. Es necesario comprender qué problema resuelve cada una.

## Elige el entorno

Para empezar:

- Windows: Laragon;
- macOS: Herd;
- Linux: XAMPP o paquetes de distribución.

Para trabajo profesional, puede cambiar a Docker, Valet, DDEV, Laravel Sail o entornos empresariales. El principio sigue siendo: PHP, servidores web, bases de datos y herramientas deben comunicarse entre sí.

## Instalar PHP 8 manualmente

Al instalar PHP manualmente, debe verificar:

```bash
php -v
php --ini
php -m
```

Código completo: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-39/es/parte-10/cap-39/listing-01.sh)


La versión, el archivo `php.ini` y los módulos cargados explican casi todos los problemas iniciales.

## Apache y hosts virtuales

Un host virtual asocia un dominio local con una carpeta:

```apache
<VirtualHost *:80>
    ServerName blog.test
    DocumentRoot "/path/to/blog/public"
</VirtualHost>
```

Código completo: [listing-02.apache](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-39/es/parte-10/cap-39/listing-02.apache)


La raíz debe apuntar a `public`, no a todo el proyecto. De esta manera los archivos de configuración, las fuentes y `vendor/` no quedan expuestos directamente.

## Homebrew, Apache y MariaDB

En macOS también puedes instalar la pila manual:

```bash
brew install php
brew install httpd
brew install mariadb
```

Código completo: [listing-03.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-39/es/parte-10/cap-39/listing-03.sh)


Luego inicie los servicios:

```bash
brew services start httpd
brew services start mariadb
```

Código completo: [listing-04.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-39/es/parte-10/cap-39/listing-04.sh)


Es una buena ruta si desea comprender cada componente, pero requiere más mantenimiento que Herd.

## Xdebug en Windows y Linux

Xdebug debe ser compatible con la versión, la arquitectura y la seguridad de subprocesos de PHP. Cuando no está cargando:

- marque `php -v`;
- marque `php --ini`;
- comprobar si el archivo `.dll` o `.so` está en la ruta correcta;
- comprobar el puerto `9003`;
- mira `php -m`.

La configuración moderna incluye:

```ini
xdebug.mode=debug
xdebug.start_with_request=yes
xdebug.client_port=9003
```

Código completo: [listing-05.ini](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-39/es/parte-10/cap-39/listing-05.ini)


## Diferentes editores

Visual Studio Code es rápido y modular. PhpStorm es más completo e integrado. NetBeans sigue siendo útil si prefiere un IDE tradicional. La elección no cambia PHP: cambia la productividad.

Cualquiera que sea el editor que elija, debe poder hacer tres cosas:

- abrir el proyecto como una carpeta;
- utilizar el PHP correcto;
- iniciar o escuchar Xdebug.

## phpMyAdmin y herramientas de base de datos

phpMyAdmin es bueno para inspeccionar datos. Las herramientas integradas HeidiSQL, TablePlus, DBeaver e IDE ofrecen alternativas. Aprenda SQL de todos modos: la interfaz visual ayuda, pero no reemplaza la comprensión de las consultas.

## En resumen

No existe un único entorno adecuado. Existe un entorno coherente, reproducible y comprensible. Cuando algo no funciona, reduce el problema: ¿Qué PHP estoy usando? ¿Cuál `php.ini`? ¿Qué servidor? ¿Qué base de datos? Esta capacidad de diagnóstico vale más que el nombre del instrumento.
