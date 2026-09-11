# 30. Excepciones, error handlers y Sentry

No todos los errores son iguales, y saber distinguirlos es la mitad del oficio. Algunos son **bugs** del código — un descuido que corregir. Otros son **condiciones esperadas**: un fichero que falta, un registro no encontrado, una entrada no válida, un servicio externo momentáneamente inalcanzable. No son lo mismo y no deben tratarse de la misma manera: los primeros hay que hacerlos visibles cuanto antes para corregirlos, los segundos hay que gestionarlos con elegancia porque forman parte del funcionamiento normal. Las **excepciones** y los **handlers** de PHP son las herramientas para hacerlo, y este capítulo los pone en fila hasta llegar a la monitorización de errores en producción con Sentry.

## `try`, `catch` y `finally`

El bloque `try/catch/finally` es la estructura básica para gestionar una operación que puede fallar:

```php
<?php
try {
    $pdo = new PDO($dsn, $user, $password);
} catch (PDOException $e) {
    echo "Conexión fallida";
} finally {
    // código ejecutado de todos modos
}
```

Código completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-30/es/parte-08/cap-30/listing-01.php)


Los tres bloques tienen papeles distintos. En el `try` pones el código que *podría* fallar — aquí abrir la conexión a la base de datos. El `catch` intercepta un tipo específico de excepción, `PDOException`, y decide qué hacer cuando ese fallo ocurre. El `finally` es el menos obvio pero a menudo el más útil: se ejecuta **en todo caso**, tanto si el `try` tuvo éxito como si saltó el `catch`. Es el lugar donde liberar recursos que hay que cerrar de todas formas — un fichero abierto, un lock, una transacción — porque te garantiza que ese código se ejecuta tome el camino que tome la ejecución.

## Lanzar excepciones

Una excepción también puedes **lanzarla** tú, con `throw`, cuando detectas una condición que el código no sabe o no debe gestionar ahí:

```php
<?php
function divide(float $a, float $b): float
{
    if ($b === 0.0) {
        throw new InvalidArgumentException("División por cero");
    }

    return $a / $b;
}
```

Código completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-30/es/parte-08/cap-30/listing-02.php)


El punto clave es qué ocurre tras el `throw`: la excepción **interrumpe** el flujo normal y **sube** por la cadena de llamadas hasta encontrar un `catch` capaz de gestionarla. Es un salto hacia arriba, no un valor de retorno. Y esta es exactamente la diferencia respecto a los viejos códigos de error devueltos como valor: un valor de retorno el llamante puede ignorarlo por descuido y seguir adelante con un dato equivocado; una excepción no — no puedes hacer como si nada, o alguien la captura, o la aplicación se detiene. El fallo se vuelve imposible de ignorar en silencio. Aquí uso `InvalidArgumentException`, una de las excepciones estándar de PHP pensada precisamente para los argumentos no válidos.

## Excepciones personalizadas

Además de las estándar, puedes definir excepciones **tuyas**, extendiendo una clase base como `RuntimeException`:

```php
<?php
class UserNotFoundException extends RuntimeException
{
}

function find_user(int $id): array
{
    $user = null;

    if (!$user) {
        throw new UserNotFoundException("Usuario $id no encontrado");
    }

    return $user;
}
```

Código completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-30/es/parte-08/cap-30/listing-03.php)


A primera vista una clase vacía que extiende `RuntimeException` parece inútil — no añade código. Pero añade lo más importante: un **tipo**. Y el tipo permite distinguir los errores y capturarlos de forma selectiva:

```php
<?php
try {
    $user = find_user(10);
} catch (UserNotFoundException $e) {
    http_response_code(404);
}
```

Código completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-30/es/parte-08/cap-30/listing-04.php)


Aquí el `catch` intercepta **solo** `UserNotFoundException` y la traduce en un 404, la respuesta HTTP correcta para "recurso no encontrado". Cualquier otra excepción — un error de base de datos, un bug — no la captura este bloque y sigue subiendo, donde se gestionará de otro modo. Este es el valor de las excepciones personalizadas: dar un nombre preciso a las condiciones de error de tu dominio, para que cada una pueda tratarse como merece. En el proyecto MVC de la Parte IX verás todo un conjunto de excepciones de dominio construidas exactamente sobre este principio.

## Error handler

Hay una zona de sombra: además de las excepciones, PHP tiene un viejo sistema de **warnings**, **notices** y **deprecations** que no son excepciones y, por defecto, no detienen nada — como mucho imprimen una línea. Puedes, sin embargo, convertirlos en excepciones con un error handler:

```php
<?php
set_error_handler(function (int $severity, string $message, string $file, int $line): bool {
    throw new ErrorException($message, 0, $severity, $file, $line);
});
```

Código completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-30/es/parte-08/cap-30/listing-05.php)


Al registrar esta función, cada warning que PHP emitiría se convierte en una `ErrorException` y se introduce en el sistema de excepciones, donde puedes capturarlo como todos los demás. En desarrollo es valiosísimo: en lugar de ignorar un warning que señala un problema real (un índice de array que falta, una variable no definida), **fallas de inmediato** y lo ves. Es de nuevo el principio del *fail loud* — un problema visible al instante cuesta mucho menos que uno que se esconde y reaparece días después, lejos de su causa.

## Exception handler global

¿Y si una excepción no la captura ningún `catch`? Hace falta una última red de seguridad, el **exception handler global**:

```php
<?php
set_exception_handler(function (Throwable $e): void {
    error_log($e);

    http_response_code(500);
    echo "Error interno";
});
```

Código completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-30/es/parte-08/cap-30/listing-06.php)


Este handler se invoca para cualquier excepción que llegue a la cima sin haber sido gestionada. Hace tres cosas sensatas: registra el error en el log (`error_log`), fija el estado HTTP 500 y muestra al usuario un mensaje limpio en lugar de un stack trace. Pero cuidado con no malinterpretar su papel: es la **última** defensa, no la estrategia. No debe reemplazar la gestión local de los errores esperados — esos los capturas cerca de donde nacen, como el 404 de antes. El handler global está ahí para lo que *no* habías previsto, y su cometido es evitar que un imprevisto se convierta en una pantalla técnica escupida a la cara del usuario.

## Entorno de desarrollo y producción

Y aquí llegamos al punto más delicado para la seguridad. El comportamiento de los errores debe ser **opuesto** entre desarrollo y producción. En desarrollo quieres verlo todo:

```php
<?php
ini_set("display_errors", "1");
error_reporting(E_ALL);
```

Código completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-30/es/parte-08/cap-30/listing-07.php)


En producción, en cambio, los errores no deben mostrarse **nunca** al usuario: hay que apagarlos en pantalla y escribirlos en los logs:

```php
<?php
ini_set("display_errors", "0");
ini_set("log_errors", "1");
```

Código completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-30/es/parte-08/cap-30/listing-08.php)


No es una cuestión de limpieza estética, es una **vulnerabilidad** de verdad. Un stack trace mostrado en la página revela las rutas absolutas del servidor, fragmentos de consultas SQL, nombres de variables, a veces credenciales de conexión: es una mina de oro para quien quiere atacarte, que le regala el mapa interno de la aplicación. La regla es tajante: en producción el usuario ve un mensaje genérico, tú lees los detalles en el log. Nunca al revés.

## Registrar errores con Sentry

Escribir los errores en un fichero de log está bien, pero en un servidor serio esos ficheros crecen, se pierden, y nadie los mira hasta que es demasiado tarde. **Sentry** es un servicio que centraliza la recogida de excepciones y errores en producción: con Composer instalas el paquete e inicializas el cliente con un DSN, y desde ahí los errores llegan a un dashboard donde se agrupan, se cuentan y se notifican. El flujo conceptual es "captura, envía, relanza":

```php
<?php
try {
    // código de aplicación
} catch (Throwable $e) {
    // envía a Sentry
    throw $e;
}
```

Código completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-30/es/parte-08/cap-30/listing-09.php)


Fíjate en el `throw $e` final: tras reportar el error a Sentry, lo **relanza**, porque el cometido aquí no es esconderlo ni gestionarlo — de eso ya se ocupa el handler global — sino *registrarlo*. Y registrarlo **con contexto**: Sentry guarda no solo el mensaje, sino la URL solicitada, el usuario implicado, el entorno, la versión de la aplicación. Es la diferencia entre saber que "algo salió mal" y poder reproducir exactamente el bug que un usuario encontró hace tres horas en una página que tú, en local, no consigues hacer fallar.

## En resumen

Las excepciones hacen los fallos **explícitos** e imposibles de ignorar en silencio: usa las excepciones personalizadas para dar un nombre a los casos de error de tu dominio y capturarlos de forma selectiva, el error handler para hacer emerger de inmediato los warnings en desarrollo, y el exception handler global como última defensa para lo imprevisto. En producción **nunca** muestres los errores al usuario — sería un agujero de seguridad — sino que hay que registrarlos, mejor aún con un servicio como Sentry que los enriquece con contexto. El hilo que lo une todo es una idea de madurez profesional: una aplicación sólida no es la que nunca falla, sino la que sabe fallar de forma **controlada y observable**.
