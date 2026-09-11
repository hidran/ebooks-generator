# Checklist PHP 8.5 y próximos pasos {.unnumbered}

El código de este libro toma PHP 8.5 como versión de referencia. Antes de publicar o desplegar un proyecto real, instale la última patch disponible del ramo 8.5.x y revise las notas oficiales de release.

## Novedades de PHP 8.5 que conviene conocer

- **Extensión URI:** use `Uri\Rfc3986\Uri` y `Uri\WhatWg\Url` cuando necesite parsing o normalización de URL más robustos que `parse_url()`.
- **Pipe operator `|>`:** hace legibles las transformaciones por pasos sin variables temporales innecesarias.
- **`clone()` con override de propiedades:** simplifica los métodos `with...()` en clases `readonly`.
- **Atributo `#[\NoDiscard]`:** advierte cuando se ignora un valor de retorno importante.
- **Closures y callables en expresiones constantes:** útil en atributos, valores por defecto y configuración declarativa.
- **cURL share handles persistentes:** reducen el coste de inicialización en solicitudes repetidas.
- **`array_first()` y `array_last()`:** leen el primer o último valor de un array sin combinar manualmente `array_key_first()` o `array_key_last()`.

## Iniciar un proyecto nuevo

Empiece con restricciones explícitas y autoload PSR-4:

```json
{
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

Código completo: [listing-01.json](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-appendix-php85-checklist/es/zz-back-matter/00-php85-checklist/listing-01.json)


Incluya `strict_types` en los archivos PHP que escriba:

```php
<?php
declare(strict_types=1);

namespace App;
```

Código completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-appendix-php85-checklist/es/zz-back-matter/00-php85-checklist/listing-02.php)


## Checklist de producción

- Use Composer y autoload PSR-4 en lugar de llamadas `require` dispersas.
- Use PDO con `PDO::ERRMODE_EXCEPTION`, charset `utf8mb4` y prepared statements.
- No concatene input del usuario dentro de SQL, HTML, headers HTTP ni rutas de archivos.
- Escape la salida HTML con `htmlspecialchars(..., ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8')`.
- Use `password_hash()` y `password_verify()` para passwords.
- Use `random_bytes()` o `random_int()` para tokens y valores aleatorios sensibles a la seguridad.
- Configure cookies con `secure`, `httponly` y `samesite`.
- Guarde configuración, passwords y tokens en variables de entorno.
- En producción, desactive `display_errors`, escriba logs estructurados y monitoree errores y excepciones.
- Actualice dependencias y runtime con regularidad: la seguridad y la compatibilidad dependen de las patch releases, no solo de la major version.
