# 14. cookies

Las cookies son pequeños fragmentos de datos que el servidor solicita al navegador que almacene. Con cada solicitud posterior al mismo dominio, el navegador las envía de regreso al servidor. En PHP los utilizarás para preferencias, consentimiento, seguimiento técnico y, con mucho cuidado, para mecanismos como "recordarme".

## Establecer una cookie

Para enviar una cookie utilice `setcookie()`:

```php
<?php
setcookie("theme", "dark");
```

Código completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-14/es/parte-04/cap-14/listing-01.php)


La cookie no aparece inmediatamente en `$_COOKIE` en la misma solicitud. Se envía en los encabezados de respuesta, el navegador lo guarda y estará disponible en la siguiente solicitud.

Para establecer una fecha límite:

```php
<?php
setcookie("theme", "dark", time() + 60 * 60 * 24 * 30);
```

Código completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-14/es/parte-04/cap-14/listing-02.php)


Aquí la cookie dura treinta días. Sin caducidad, la cookie es de sesión y el navegador puede eliminarla al cerrarla.

## Leer una cookie

Las cookies recibidas están en `$_COOKIE`:

```php
<?php
$theme = $_COOKIE["theme"] ?? "light";
```

Código completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-14/es/parte-04/cap-14/listing-03.php)


Como siempre ocurre con los datos externos, no confíes en el valor. El navegador está controlado por el usuario: una cookie puede modificarse, eliminarse o inventarse.

## Opciones modernas

La forma más legible de `setcookie()` utiliza una variedad de opciones:

```php
<?php
setcookie("theme", "dark", [
    "expires" => time() + 60 * 60 * 24 * 30,
    "path" => "/",
    "secure" => true,
    "httponly" => true,
    "samesite" => "Lax",
]);
```

Código completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-14/es/parte-04/cap-14/listing-04.php)


Las opciones más importantes son:

- `expires`: caducidad de las cookies;
- `path`: ruta para la cual la cookie es válida;
- `secure`: envío solo a través de HTTPS;
- `httponly`: no accesible desde JavaScript;
- `samesite`: reduce algunos riesgos relacionados con las solicitudes entre sitios.

Durante el desarrollo local no puedes utilizar HTTPS. En ese caso, `secure => true` impide que el navegador guarde la cookie. Sin embargo, en producción, las cookies confidenciales solo deben viajar a través de HTTPS.

## Eliminar una cookie

Para eliminar una cookie, vuelva a escribirla con vencimiento en el pasado:

```php
<?php
setcookie("theme", "", time() - 3600, "/");
```

Código completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-14/es/parte-04/cap-14/listing-05.php)


El `path` debe coincidir con el utilizado cuando se creó la cookie. Si no coincide, el navegador puede almacenar una cookie aparentemente idéntica pero asociada a una ruta diferente.

## Encabezados ya enviados

`setcookie()` envía el encabezado HTTP. Los encabezados deben comenzar antes del cuerpo de la respuesta. Este código puede generar error:

```php
<?php
echo "Hola";
setcookie("theme", "dark");
```

Código completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-14/es/parte-04/cap-14/listing-06.php)


El mensaje típico es "encabezados ya enviados". La solución correcta es organizar el código para que las cookies, los redireccionamientos y las sesiones se manejen antes de imprimir HTML.

En desarrollo también puedes encontrar buffering de salida:

```php
<?php
ob_start();

echo "Hola";
setcookie("theme", "dark");

ob_end_flush();
```

Código completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-14/es/parte-04/cap-14/listing-07.php)


El almacenamiento en búfer de salida puede ayudar en casos específicos, pero no debería convertirse en una excusa para mezclar lógica y presentación fuera de orden.

## Cookies y sesiones

Las sesiones PHP normalmente utilizan una cookie con el identificador de sesión. Los datos reales permanecen en el servidor; en el navegador solo hay una clave. Esta es la diferencia clave:

- cookie: el valor está en el navegador;
- sesión: el valor está en el servidor, el navegador conserva el identificador.

Para datos confidenciales, prefiera sesión. Para preferencias no confidenciales, una cookie puede ser suficiente.

## Cookies y seguridad

No guarde contraseñas, roles o datos confidenciales en texto claro en una cookie. Incluso si configura `httponly`, el usuario puede ver y editar la cookie desde el navegador o las herramientas del desarrollador.

Para "recordarme" de forma segura, no guardaremos solo el ID de usuario. Usaremos un token aleatorio, lo guardaremos en la base de datos de forma controlada y lo rotaremos después de su uso.

## En resumen

Las cookies son fáciles de usar, pero fáciles de usar incorrectamente. Configúrelos antes de la salida, léalos siempre con valores predeterminados, elimínelos replicando la ruta y el dominio, y use opciones modernas como `httponly`, `secure` y `samesite`. En los capítulos del proyecto los usaremos para crear un inicio de sesión persistente sin confiar ciegamente en el navegador.
