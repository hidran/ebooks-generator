# 37. Implementar en Heroku

Una aplicación no está completa mientras esté solo en su máquina. La implementación pone el proyecto en línea e introduce nuevas variables: entorno, base de datos remota, configuración, registros, rutas y diferencias entre desarrollo y producción.

## Prepara la aplicación

Antes de la implementación, verifique:

- el punto de entrada público (`public/index.php`);
- Composer configurado;
- sin contraseñas codificadas;
- configuración leída de variables de entorno;
- errores no mostrados en producción;
- archivos innecesarios excluidos de la implementación.

Una configuración mínima puede leer variables:

```php
<?php
$dsn = getenv("DATABASE_DSN");
$user = getenv("DATABASE_USER");
$password = getenv("DATABASE_PASSWORD");
```

Código completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-37/es/parte-10/cap-37/listing-01.php)


## Archivo de perfil

Heroku usa un `Procfile` para saber cómo iniciar la aplicación:

```text
web: vendor/bin/heroku-php-apache2 public/
```

Código completo: [listing-02.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-37/es/parte-10/cap-37/listing-02.txt)


Esto indica que la raíz web es `public/`, no la carpeta del proyecto.

## Composer en producción

Heroku detecta una aplicación PHP por la presencia de `composer.json`. Asegúrese de que esté declarada la versión de PHP requerida:

```json
{
  "require": {
    "php": "^8.5"
  }
}
```

Código completo: [listing-03.json](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-37/es/parte-10/cap-37/listing-03.json)


Durante la implementación, Heroku ejecuta `composer install` y prepara `vendor/`.

## Base de datos remota

La base de datos local no se carga automáticamente. Debe crear una base de datos remota, configurar credenciales y aplicar el esquema.

El principio es el mismo:

```sql
CREATE TABLE users (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(190) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE posts (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NULL,
    title VARCHAR(190) NOT NULL,
    body TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Código completo: [listing-04.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-37/es/parte-10/cap-37/listing-04.sql)


En proyectos reales utilizarás migraciones. Aquí puede ejecutar manualmente el esquema, pero mantenga un archivo SQL versionado para no perderse pasos.

## Carga de archivos en producción

Muchas plataformas, incluido Heroku, tienen sistemas de archivos efímeros: los archivos cargados pueden desaparecer con cada implementación o reinicio. Para avatares e imágenes en producción necesitas almacenamiento externo, como S3 o servicios compatibles.

Este es un punto importante: el código de carga funciona localmente, pero la arquitectura de producción debe decidir dónde guardar los archivos persistentes.

## Iniciar sesión

En producción, no miras la pantalla del navegador para comprender los errores. Usos del registro:

```bash
heroku logs --tail
```

Código completo: [listing-05.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-37/es/parte-10/cap-37/listing-05.sh)


En el código, `error_log()` es el mínimo. Para errores graves, herramientas como Sentry ayudan a ver el seguimiento, la frecuencia y el contexto de la pila.

## Rutas y autoload

Si una ruta funciona "por casualidad" localmente, puede interrumpir la producción. Utilice siempre `__DIR__` y rutas absolutas derivadas de la estructura del proyecto:

```php
<?php
require __DIR__ . "/../vendor/autoload.php";
```

Código completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-37/es/parte-10/cap-37/listing-06.php)


No dependa de la carpeta actual.

## En resumen

La implementación requiere disciplina: configuración fuera de código, raíz pública correcta, Composer, base de datos remota, registros y atención a los archivos persistentes. Heroku simplifica la puesta en marcha, pero no elimina las decisiones arquitectónicas. Aquí comienza la diferencia entre proyecto educativo y aplicación real.
