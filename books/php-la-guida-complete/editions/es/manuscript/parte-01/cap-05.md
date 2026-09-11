# 5. Editor, IDE y depuración.

Escribir PHP no se trata sólo de conocer la sintaxis. También necesita un entorno que le ayude a leer código, encontrar errores, navegar entre archivos y controlar la ejecución. Puedes seguir el libro completo con Visual Studio Code, PhpStorm o NetBeans; lo importante es configurar bien PHP, la terminal y Xdebug.

## Visual Studio Code

Visual Studio Code es liviano, gratuito y muy flexible. Para PHP lo mejor es instalar algunas extensiones:

- una extensión para soporte PHP y finalización de código;
- una extensión para Xdebug;
- un formateador, si desea mantener un estilo coherente;
- Soporte de Git, ya integrado pero se puede mejorar con extensiones dedicadas.

Abra una carpeta de proyecto, no un solo archivo. De esta manera, el editor puede comprender las rutas, indexar el código y utilizar una terminal integrada en el lugar correcto.

## El terminal integrado

En la terminal integrada prueba ahora:

```bash
php -v
```

Código completo: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-5/es/parte-01/cap-05/listing-01.sh)


Si VS Code no encuentra PHP pero la terminal del sistema sí, el problema es la RUTA con la que se inició la aplicación. En macOS y Linux suele ser suficiente volver a abrir VS Code desde la terminal:

```bash
code .
```

Código completo: [listing-02.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-5/es/parte-01/cap-05/listing-02.sh)


En Windows puedes usar Git Bash como tu terminal predeterminado. Esto es conveniente porque muchos comandos del mundo PHP y Composer están documentados con sintaxis Unix.

## Ejecutar un archivo desde el editor

Un archivo PHP se puede ejecutar de dos maneras diferentes:

```bash
php script.php
```

Código completo: [listing-03.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-5/es/parte-01/cap-05/listing-03.sh)


o vía servidor web:

```bash
php -S localhost:8000
```

Código completo: [listing-04.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-5/es/parte-01/cap-05/listing-04.sh)


La diferencia es fundamental. Desde el terminal no hay `$_GET`, `$_POST`, cookies y sesiones como en una petición web. Sin embargo, desde el navegador, PHP funciona dentro del ciclo de solicitud-respuesta.

## Configurar Xdebug en VS Code

La depuración con puntos de interrupción requiere tres cosas:

- Xdebug instalado y activo en la versión PHP utilizada;
- el editor escuchando;
- una solicitud para iniciar la sesión de depuración.

Un archivo `.vscode/launch.json` esencial puede ser:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Listen for Xdebug",
      "type": "php",
      "request": "launch",
      "port": 9003
    }
  ]
}
```

Código completo: [listing-05.json](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-5/es/parte-01/cap-05/listing-05.json)


Xdebug 3 usa el puerto `9003` de forma predeterminada. Si encuentra guías más antiguas con `9000`, verifique la versión: muchas configuraciones no funcionan solo porque combinan las configuraciones de Xdebug 2 y Xdebug 3.

## `php.ini` y módulos cargados

Cuando PHP se comporte inesperadamente, pregúntele qué configuración está usando:

```bash
php --ini
```

Código completo: [listing-06.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-5/es/parte-01/cap-05/listing-06.sh)


Para comprobar los módulos:

```bash
php -m
```

Código completo: [listing-07.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-5/es/parte-01/cap-05/listing-07.sh)


Para buscar Xdebug:

```bash
php -m | grep xdebug
```

Código completo: [listing-08.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-5/es/parte-01/cap-05/listing-08.sh)


Recuerde que PHP CLI y el servidor web PHP pueden leer diferentes archivos `php.ini`. Si habilita una extensión en la CLI pero el navegador no la ve, probablemente esté editando el archivo incorrecto.

## PhpStorm

PhpStorm es un IDE comercial muy completo. Ofrece refactorización, navegación entre clases, integración con Composer, herramientas de bases de datos, ejecutores de pruebas y depuración ya diseñados para PHP.

Para usarlo bien:

- establece el intérprete PHP del proyecto;
- configurar Composer;
- conectar Xdebug;
- registre cualquier servidor local si utiliza el mapeo de rutas.

El mapeo de rutas es útil cuando la ruta del archivo vista por el navegador no coincide con la local. Esto es común con Docker o máquinas virtuales, menos con Herd, Laragon o XAMPP.

## NetBeans

NetBeans es una buena alternativa cuando quieres un IDE tradicional. En proyectos PHP necesitas configurar:

- la ruta PHP;
- la carpeta del proyecto;
- la URL local para ejecutar la aplicación;
- cualquier depurador.

Si el IDE no ejecuta el archivo correcto, primero verifique la carpeta raíz del proyecto y luego la URL de inicio.

## Depuración práctica: `var_dump()` o punto de interrupción?

`var_dump()` sigue siendo muy útil:

```php
<?php
var_dump($_GET);
```

Código completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-5/es/parte-01/cap-05/listing-09.php)


A menudo lo usarás para descubrir qué contiene una variable. Pero cuando el flujo se hace más largo, un punto de interrupción es más efectivo: puedes ver el estado del programa sin cambiar el código y sin llenar las páginas con resultados temporales.

## En resumen

Elige el editor que prefieras, pero comprueba siempre que utilice la versión correcta de PHP. Aprende rápidamente a distinguir entre ejecución de terminal y ejecución de navegador. Cuando algo no cuadra, revisa `php -v`, `php --ini`, `php -m` y tu configuración de Xdebug: en la mayoría de los casos el problema está ahí.
