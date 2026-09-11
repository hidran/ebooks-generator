# 24. Remember Me

Remember me permite reconocer al usuario incluso después de que expire la sesión PHP: es la casilla "recuérdame" que marcas al hacer login y que te encuentra todavía logueado al día siguiente, sin volver a introducir las credenciales. Parece una comodidad trivial, y es en cambio uno de los mecanismos más delicados de implementar bien, porque mueve una parte de la autenticación **fuera de la sesión**, a una cookie que vive durante semanas en el dispositivo del usuario.

Empecemos por cómo **no** hacerlo, porque es el error que casi todos cometen la primera vez. La tentación es guardar en la cookie el email y la password del usuario, o su id, y releerlos en la siguiente visita. Es un desastre: una cookie se almacena en claro en el disco, viaja en cada petición, y es exactamente el tipo de dato que un ataque XSS o un ordenador compartido exponen. Guardar la password en una cookie significa regalarla. Guardar el id significa que cualquiera que escriba `user_id=1` en su propio browser se convierte en el administrador. Hace falta algo completamente distinto: no una identidad guardada, sino un **protocolo de prueba**. Es el pattern **selector/validator**, y es lo que el repositorio `php-user-management-system` implementa en el commit `8769ecc` — selector, token, hash, cookie `HttpOnly`, auto-login, rotación y revocación. Veámoslo pieza a pieza.

## Tabla de tokens

El token persistente no debe guardarse en claro. La base de datos conserva un selector público y el hash del token secreto:

```sql
create table remember_tokens
(
    id         bigint unsigned auto_increment
        primary key,
    user_id    bigint unsigned                    not null,
    token_hash char(64)                           not null,
    expires_at datetime                           not null,
    created_at datetime default CURRENT_TIMESTAMP not null,
    user_agent varchar(255)                       null,
    ip_address varbinary(16)                      not null,
    selector   char(18)                           not null,
    constraint uk_selector_remember_me
        unique (selector),
    constraint remember_tokens_users_id_fk
        foreign key (user_id) references users (id)
            on delete cascade
);
```

Código completo: [listing-01.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-24/es/parte-06/cap-24/listing-01.sql)

Fuente real: [`data/remember_tokens.sql` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/data/remember_tokens.sql).

La tabla ya cuenta todo el protocolo, si sabes leerla. Hay dos valores separados: el **selector**, con una restricción `unique`, y el **token_hash**. La cookie que acabará en el browser contendrá `selector:token` — dos piezas unidas por dos puntos. El selector sirve para **encontrar la fila** rápidamente (está indexado, es único), el token sirve para **demostrar** que el browser posee el secreto. ¿Por qué dos valores en lugar de uno? Porque separan dos necesidades en conflicto: buscar rápido en la base de datos quiere un valor indexado, pero buscar por un *secreto* indexado abriría una vía a ciertos ataques de temporización sobre el índice. Con la pareja, la búsqueda se hace sobre el selector público y la comparación de seguridad sobre el token.

El detalle crucial es que la base de datos guarda `token_hash`, **no el token**. Exactamente igual que con las passwords del Capítulo 22, el secreto real nunca se conserva en claro: se guarda su huella SHA-256. Así, si un atacante roba la tabla `remember_tokens` entera, no obtiene tokens utilizables — obtiene sus hashes, de los cuales no puede recuperar los tokens originales. Robar la base de datos no basta para suplantar a nadie. Fíjate también en `on delete cascade` en la restricción: cuando un usuario se elimina, sus tokens desaparecen automáticamente, sin código que acordarse de escribir. Y los campos `user_agent`, `ip_address`, `expires_at` sirven para trazabilidad y caducidad: un token no vale para siempre.

## Crear la cookie

`saveRememberMe()` genera selector y token con `random_bytes()`, guarda el hash SHA-256 y envía la cookie:

```php
function saveRememberMe(mysqli $conn, int $userId): bool
{
    $selector = base64url_encode(random_bytes(12));
    $token = base64url_encode(random_bytes(33));
    $tokenHash = hash('sha256', $token);
    $ttl = getConfig('rememberMeTTL');
    $expiresAt = (new DateTimeImmutable('+' . $ttl . ' seconds'))->format('Y-m-d H:i:s');
    $ip = $_SERVER['REMOTE_ADDR'];
    $userAgent = mb_substr($_SERVER['HTTP_USER_AGENT'], 0, 255);
    $sql = 'INSERT INTO remember_tokens (user_id, token_hash, selector, expires_at, ip_address, user_agent) VALUES (?,?,?,?,?,?)';
```

Código completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-24/es/parte-06/cap-24/listing-02.php)

Fuente real: [`includes/auth.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

Selector y token nacen ambos de `random_bytes()`, la misma función criptográficamente segura que el token CSRF del Capítulo 22 — porque también aquí predecir el valor significa poder falsificarlo. Fíjate en qué entra en la base de datos y qué no: se inserta `$tokenHash`, la huella, **no** `$token`. El token en claro, el que hace falta de verdad para el auto-login, existe solo por un instante dentro de esta función, el tiempo de ponerlo en la cookie; luego PHP lo olvida y en la base de datos queda solo el hash. Es la misma asimetría de las passwords: el sistema conserva lo suficiente para **verificar** un secreto, nunca lo suficiente para **reconstruirlo**.

La parte final envía al browser el valor completo:

```php
$value = $selector . ':' . $token;
$cookieName = getConfig('rememberMeCookieName');

$cookieOptions = getRememberCookieOpts();
setcookie($cookieName, $value, $cookieOptions);

return $res;
```

Código completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-24/es/parte-06/cap-24/listing-03.php)

Fuente real: [`includes/auth.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

En la cookie va `selector:token`: el selector que la base de datos conoce, y el token en claro del que la base de datos solo tiene el hash. Es el único momento en el que el token viaja en claro, y es inevitable — el browser tiene que recibirlo de algún modo para poder devolverlo después. De aquí en adelante todo el juego es proteger esta cookie, y es lo que hacen las opciones del próximo apartado.

## Opciones de la cookie

La cookie es `HttpOnly`, `SameSite=Strict` y dura lo mismo que el TTL configurado:

```php
function getRememberCookieOpts(): array
{
    $ttl = getConfig('rememberMeTTL');
    $secure = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off');

    return [

        'expires' => time() + $ttl,
        'path' => '/',
        'domain' => '',
        'secure' => $secure,
        'httponly' => true,
        'samesite' => 'Strict'
    ];
}
```

Código completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-24/es/parte-06/cap-24/listing-04.php)

Fuente real: [`includes/auth.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

Son las mismas defensas que vimos sobre la cookie de sesión en el Capítulo 22, y aquí cuentan todavía más, porque esta cookie vive durante semanas en lugar de durante la vida de una pestaña del browser. `httponly => true` la hace invisible a JavaScript, así un ataque XSS no puede leerla ni exfiltrarla — crucial para una cookie de larga vida. `secure` la confina a HTTPS en producción, donde el valor pasa a `true` por sí solo. Y aquí `samesite => 'Strict'`, más restrictivo que el `'Lax'` de la sesión: la cookie de remember me **nunca** se envía en peticiones que parten de otros sitios, ni siquiera en las navegaciones normales. Tiene sentido — es una cookie que sirve solo para el auto-login al entrar en nuestro propio sitio, no hay motivo para que viaje en ningún otro contexto, y cerrar del todo esa puerta es gratis. Cuanto más vive una cookie, más estricta debe ser su configuración.

## Auto-login

`tryAutoLogin()` se llama en `index.php` antes de la comprobación `is_user_logged_in()`:

```php
function tryAutoLogin(): void
{
    if (!empty($_SESSION['user_logged_in'])) {
        return;
    }
    $cookieName = getConfig('rememberMeCookieName');

    $cookie = $_COOKIE[$cookieName] ?? '';

    if (!$cookie || !str_contains($cookie, ':')) {
        return;
    }
    [$selector, $token] = explode(':', $cookie);
```

Código completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-24/es/parte-06/cap-24/listing-05.php)

Fuente real: [`includes/auth.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

Aquí está el protocolo en acción, corriendo al revés respecto a la creación. La función empieza con un *fail fast*: si ya hay una sesión activa, no hay nada que hacer, sale enseguida. En caso contrario lee la cookie y la parte por los dos puntos en sus dos partes, `$selector` y `$token`. El selector servirá para encontrar la fila, el token para demostrar su posesión.

La query une token y usuario, así el auto-login falla si el usuario ya no existe:

```php
$conn = getConnection();
$st = $conn->prepare(
    'SELECT  t.id,t.expires_at,t.token_hash, u.id as uid, u.email, u.username, u.role_type FROM remember_tokens as t INNER JOIN users as u ON t.user_id=u.id WHERE selector=?'
);
$st->bind_param('s', $selector);
$res = $st->execute();
```

Código completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-24/es/parte-06/cap-24/listing-06.php)

Fuente real: [`includes/auth.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

La búsqueda se hace **sobre el selector**, no sobre el token — es exactamente por esto que el protocolo usa dos valores. El selector está indexado y es único, así que la base de datos encuentra la fila de forma directa y eficiente. Y por supuesto es un prepared statement con el selector vinculado como parámetro: estamos en la Parte VI, la regla del SQL vale también aquí. El `JOIN` con la tabla `users` hace algo inteligente de una vez: recupera los datos del usuario y, si ese usuario mientras tanto ha sido eliminado, no devuelve ninguna fila — el auto-login falla por sí solo, sin comprobaciones adicionales.

La comparación usa el hash del token recibido:

```php
$calcHash = hash('sha256', $token);
if (!hash_equals($row['token_hash'], $calcHash)) {
    deleteRememberTokenById($row['id']);
    clearRememberMe();
    return;
}
```

Código completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-24/es/parte-06/cap-24/listing-07.php)

Fuente real: [`includes/auth.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

Encontrada la fila a través del selector, se verifica el token: se calcula el hash SHA-256 del token recibido de la cookie y se compara con el guardado en la base de datos. La comparación pasa por `hash_equals()`, la función de tiempo constante del Capítulo 22, por el mismo motivo — impedir el timing attack sobre la comparación del secreto. Si los hashes no coinciden, algo va mal: el token está caducado, manipulado, o es un intento de adivinarlo. La reacción es drástica y correcta: se **elimina** la fila (`deleteRememberTokenById`) y se limpia la cookie. Un token sospechoso no solo se rechaza, se destruye — mejor obligar al usuario legítimo a un nuevo login que dejar por ahí un token sobre el que alguien está trabajando.

## Rotación

Después de un auto-login correcto, el token se rota:

```php
function rotateRememberToken(mysqli $conn, int $id): void
{
    $token = base64url_encode(random_bytes(33));
    $tokenHash = hash('sha256', $token);
    $ttl = getConfig('rememberMeTTL');
    $expiresAt = (new DateTimeImmutable('+' . $ttl . ' seconds'))->format('Y-m-d H:i:s');
    $sql = 'SELECT selector FROM remember_tokens WHERE id=?';
```

Código completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-24/es/parte-06/cap-24/listing-08.php)

Fuente real: [`includes/auth.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

Esta es la parte que eleva el mecanismo de "funcional" a "robusto", y es la que los tutoriales casi siempre se saltan. Después de cada auto-login correcto, el token usado se **tira y se sustituye** por uno nuevo: nuevo `random_bytes()`, nuevo hash, nueva caducidad. ¿Por qué? Porque reduce drásticamente la ventana útil de un token robado. Imagina que un atacante consigue copiar la cookie de remember me. Sin rotación, esa cookie vale durante semanas, durante todo el TTL. Con la rotación, en cuanto el propietario legítimo vuelve al sitio y hace auto-login, el token cambia — y la copia en manos del atacante se convierte en papel mojado. Mejor todavía: si es el atacante quien usa primero el token robado, será el propietario *legítimo* quien se encuentre con un token ya no válido, una señal de que algo va mal. La rotación transforma un token persistente de llave permanente en llave de usar y renovar.

## Revocación al logout

El logout borra la cookie, revoca el token del dispositivo actual (o todos los tokens del usuario) y por último destruye la sesión:

```php
clearRememberMe();
if ($fromAll) {
    revokeAllRememberMeTokens(get_user_id());
} else {
    revokeDeviceRememberMeToken(get_user_id());
}
$_SESSION = [];
$p = session_get_cookie_params();
setcookie(session_name(), '', time() - 4200, $p['path'], $p['domain'], $p['secure'], $p['httponly']);
session_destroy();

redirect('/login.php');
```

Atención al orden, porque son tres operaciones distintas y hacen falta las tres. `$_SESSION = []` vacía el array en memoria para la petición actual, pero por sí solo no borra nada en el servidor. La llamada a `setcookie()` con una caducidad en el pasado le dice al navegador que tire la cookie de sesión: sin este paso, el navegador seguiría enviando un ID de sesión que ya no debería existir. Y `session_destroy()` elimina los datos de la sesión en el servidor. Quedarse en `$_SESSION = []` es el error clásico: el usuario parece desconectado, pero el fichero de sesión sigue en el servidor y la cookie sigue en el navegador, así que ese ID todavía se puede usar.

Código completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-24/es/parte-06/cap-24/listing-09.php)

Fuente real: [`controller/logout.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/controller/logout.php).

Hay un detalle de producto, además de seguridad, en ese `if ($fromAll)`. El logout normal revoca solo el token del **dispositivo actual**: si estás logueado en el portátil y en el teléfono, salir del portátil no te echa del teléfono. Pero la opción `fromAll` revoca **todos** los tokens del usuario de una vez — es el clásico "cerrar sesión en todos los dispositivos" que ofreces cuando alguien teme que su cuenta esté comprometida. Poder hacerlo es posible solo porque cada token es una fila separada en la base de datos, vinculada al usuario: revocarlos todos es un `DELETE WHERE user_id=?`. Por eso la revocación es tan explícita:

```php
function revokeAllRememberMeTokens(int $userId): void
{
    $conn = getConnection();
    $st = $conn->prepare('DELETE FROM remember_tokens WHERE user_id=?');
    $st->bind_param('i', $userId);
    $st->execute();
    $st->close();
}
```

Código completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-24/es/parte-06/cap-24/listing-10.php)

Fuente real: [`includes/auth.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

Un `DELETE` con el `user_id` vinculado como parámetro, y todos los tokens del usuario desaparecen. La revocación es posible porque el estado vive en la **base de datos**, no solo en la cookie: pudiendo borrar la fila, puedes invalidar un acceso cuando quieras. Es la diferencia sustancial respecto a guardar las credenciales en la cookie, donde no tendrías ninguna forma de "retirar" un token ya repartido.

## En resumen

Remember me no es una password guardada en una cookie — es un **protocolo**, y ahora sabes por qué existe cada una de sus piezas. El **selector público** encuentra la fila rápido; el **token secreto** demuestra la posesión; el **hash en la base de datos** hace que un robo de la tabla no produzca tokens utilizables; la **caducidad** limita la duración; la **cookie `HttpOnly`, `Secure`, `SameSite=Strict`** protege el secreto en tránsito y en reposo; el **auto-login** verifica con `hash_equals()`; la **rotación** acorta la vida de un token robado; la **revocación** — de un dispositivo o de todos — es posible porque el estado vive en la base de datos. El repositorio UMS muestra el ciclo entero en código procedural: en la Parte IX los mismos principios reaparecen en un servicio dedicado, pero el protocolo es exactamente este. Si has entendido por qué hacen falta dos valores en lugar de uno, y por qué se guarda el hash y no el token, has entendido la parte difícil.
