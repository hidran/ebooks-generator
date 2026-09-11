# 22. Login, registro, sesiones y CSRF

Después del CRUD, el User Management System necesita saber **quién** está usando la aplicación. Hasta aquí todos los visitantes eran iguales: cualquiera podía abrir la lista de usuarios, modificar un registro, borrarlo. Ahora introducimos dos conceptos que parecen lo mismo pero no lo son en absoluto, y conviene mantenerlos separados desde el principio.

La **autenticación** responde a la pregunta *"¿quién eres?"*. Es el momento en el que el usuario demuestra su identidad, normalmente con un email y una password. La **autorización** responde a *"¿qué puedes hacer?"*. Es la comprobación que ocurre después, cada vez que el usuario intenta realizar una acción. Son dos pasos distintos: un usuario autenticado no está automáticamente autorizado a hacerlo todo, y es precisamente de la confusión entre ambos de donde nacen muchos agujeros de seguridad.

En este capítulo juntamos cuatro piezas: las **sesiones** (para recordar quién es el usuario entre una petición y la siguiente), los **hashes de password** (para no guardar nunca una password legible), los **tokens CSRF** (para asegurarnos de que una petición viene realmente de nuestro form) y los **roles** (para decidir quién puede hacer qué). El repositorio público los implementa de forma procedural, con funciones agrupadas en `includes/`: es deliberadamente la versión más simple posible, la que te deja ver el mecanismo sin la abstracción de un framework por encima.

![El formulario de login de UMS. La casilla "Remember me" alimenta el mecanismo de token persistente que veremos en el capítulo 24.](figures/cap-22/login-form.png)

## Cookie de sesión

Primero, un repaso de qué es realmente una sesión, porque es la pieza sobre la que se apoya todo lo demás. HTTP es un protocolo **sin estado**: cada petición llega al server sin memoria de las anteriores. Si el usuario hace login y luego pulsa un enlace, la segunda petición por sí sola no sabe nada de la primera. La sesión resuelve el problema en dos tiempos: PHP crea en el **server** un contenedor de datos identificado por un ID aleatorio, y envía al **browser** una cookie que contiene solo ese ID. El email, el rol, todo lo que necesitamos se queda en los datos del server; en la cookie viaja únicamente el identificador. Es una distinción importante: quien roba la cookie no lee tus datos, pero puede **suplantar** al usuario, que es todavía peor.

Por eso `includes/session.php` configura la cookie *antes* de llamar a `session_start()`:

```php
<?php

declare(strict_types=1);
$secure = !empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off';
session_set_cookie_params([
    'path' => '/',
    'domain' => '',
    'secure' => $secure,
    'httponly' => true,
    'samesite' => 'Lax'
]);
ini_set('session.use_strict_mode', 1);
session_name('ums_sid');
session_start();
```

Código completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-22/es/parte-06/cap-22/listing-01.php)

Fuente real: [`includes/session.php` en `0fa560f`](https://github.com/hidran/php-user-management-system/blob/0fa560f/includes/session.php).

El orden no es un detalle: `session_set_cookie_params()` debe llamarse antes de `session_start()`, porque es esta última la que emite la cookie. Invertirlas significa configurar algo que ya se ha enviado.

Veamos las opciones una por una, porque cada una cierra una puerta concreta:

- **`httponly => true`** impide que JavaScript lea la cookie mediante `document.cookie`. Si el día de mañana se te escapa una vulnerabilidad XSS en alguna página, el atacante podrá inyectar scripts, pero no podrá exfiltrar el ID de sesión y reutilizarlo cómodamente en otro sitio. Es una red de seguridad, no un permiso para descuidar el escaping.
- **`secure => $secure`** le dice al browser que envíe la cookie solo por HTTPS. En local solemos trabajar en HTTP, así que el valor se calcula dinámicamente: en producción, donde está el certificado, pasa a `true` por sí solo. Sin este flag, una cookie de sesión puede viajar en claro por una red Wi-Fi pública.
- **`samesite => 'Lax'`** limita el envío de la cookie cuando la petición parte de **otro sitio**. Es la primera línea de defensa contra el CSRF del que hablamos enseguida: con `Lax` la cookie viaja en las navegaciones normales (el usuario pulsa un enlace y llega a nuestro sitio) pero no en las peticiones POST cross-site. No sustituye al token CSRF — los browsers antiguos no lo respetan y algunas configuraciones lo sortean — pero sube bastante el listón.
- **`session.use_strict_mode = 1`** es el más oscuro de los cuatro y merece una explicación como es debido. Por defecto PHP acepta cualquier ID de sesión que le llegue del browser: si le mando una cookie con el ID `abc123` y ese ID no existe, PHP lo *crea*. Un atacante puede entonces elegir él mismo el ID, conseguir que la víctima lo use (basta un enlace tipo `?PHPSESSID=abc123` en configuraciones permisivas) y luego presentarse con ese mismo ID una vez que la víctima ha hecho login. Se llama **session fixation**. Con `use_strict_mode` activado, PHP rechaza los ID que no ha generado él y emite uno nuevo.
- **`session_name('ums_sid')`** renombra la cookie, que por defecto se llama `PHPSESSID`. No es seguridad de verdad — cualquiera que mire la respuesta se da cuenta de que es un ID de sesión — pero evita anunciar "aquí corre PHP" a los escáneres automáticos, y en un hosting compartido mantiene separadas las sesiones de aplicaciones distintas.

Ninguna de estas líneas hace que el login *funcione*: el login se comportaría igual sin ellas. Marcan la diferencia entre un sistema que aguanta un ataque trivial y uno que no.

## Token CSRF

Este es el punto en el que conviene parar y entender **el ataque**, porque el código de la defensa son tres líneas y sin el contexto parece una fórmula mágica para copiar.

**CSRF** significa *Cross-Site Request Forgery*, en español "falsificación de petición entre sitios". Imagina esta situación. Estás logueado en nuestro UMS: tienes la cookie de sesión en el browser y es válida. En otra pestaña abres un sitio cualquiera — un foro, una página que te ha llegado por email. Esa página contiene, oculto, un form como este:

```html
<form action="https://ums.example.com/controller/updateRecord.php" method="POST">
    <input type="hidden" name="action" value="delete">
    <input type="hidden" name="id" value="1">
</form>
<script>document.forms[0].submit();</script>
```

El browser envía la petición a nuestro server **y adjunta la cookie de sesión**, porque las cookies se envían en función del dominio de destino, no en función de quién ha originado la petición. Desde el punto de vista del server es una POST perfectamente válida, de un usuario autenticado, con los permisos correctos. El registro se borra. El usuario no ha pulsado nada de forma consciente.

Fíjate en el punto clave: el atacante **no necesita leer** la cookie, ni conocer la sesión. Le basta con que la petición salga del browser de la víctima. Por eso `httponly` no protege del CSRF, y por eso hace falta un mecanismo distinto.

La defensa se llama **synchronizer token pattern** y se apoya en una asimetría sencilla: el browser de la víctima envía las cookies automáticamente, pero **no** conoce el contenido de nuestras páginas. Si cada form lleva un valor secreto que solo puede conocer quien ha cargado realmente la página, el atacante no puede reproducirlo desde fuera.

```php
<?php

function csrf_token(): string
{
    return $_SESSION['csrf_token'] ??= bin2hex(random_bytes(32));
}

function csrf_field(): string
{
    return '<input type="hidden" name="csrf_token" value="' . csrf_token() . '">' . "\n";
}

function csrf_validate(string $token): bool
{
    return hash_equals($token, csrf_token());
}
```

Código completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-22/es/parte-06/cap-22/listing-02.php)

Fuente real: [`includes/csrf.php` en `bfc58e7`](https://github.com/hidran/php-user-management-system/blob/bfc58e7/includes/csrf.php).

Tres funciones, tres detalles que merecen atención.

**`random_bytes(32)`** genera 32 bytes **criptográficamente seguros**, es decir, impredecibles incluso conociendo los valores generados antes. Es distinto de `rand()` o `mt_rand()`, que son rápidos pero predecibles: con suficientes salidas se puede reconstruir el estado del generador y predecir las siguientes. Para un token de seguridad eso es fatal, así que la regla es tajante: para cualquier valor secreto — tokens CSRF, tokens de reseteo de password, identificadores de sesión — se usa `random_bytes()` (o `random_int()` para los números), nunca `rand()`. `bin2hex()` convierte después los bytes en 64 caracteres hexadecimales, aptos para acabar en un atributo HTML.

**El operador `??=`** (null coalescing assignment, PHP 7.4, que vimos en el capítulo 8) hace que el token se genere **una sola vez por sesión**: si `$_SESSION['csrf_token']` ya existe, se devuelve ese. Esto significa que todos los forms de la sesión comparten el mismo token. Es un compromiso consciente: un token distinto para cada form sería más robusto, pero se rompe en cuanto el usuario abre dos pestañas o usa el botón "atrás", porque el token de la página vieja ya no es el válido. Para una aplicación como esta, un token por sesión es el equilibrio adecuado entre seguridad y usabilidad.

**`hash_equals()`** en lugar de `===` es el detalle que casi todo el mundo se salta. Una comparación normal de cadenas se detiene en el primer carácter distinto: comparar `"aaaa"` con `"baaa"` es más rápido que comparar `"aaaa"` con `"aaab"`, porque en el segundo caso la comparación tiene que llegar hasta el final. La diferencia es de nanosegundos, pero es **medible**, y repitiendo la medición miles de veces un atacante puede adivinar el token carácter a carácter en lugar de tener que acertarlo entero de golpe. Se llama **timing attack**. `hash_equals()` compara las dos cadenas en un tiempo que no depende de cuántos caracteres iniciales coinciden, y cierra esa puerta. La regla práctica: siempre que compares un secreto — un token, un hash, una firma — usa `hash_equals()`, no `==` ni `===`.

Una nota sobre la firma: el manual de PHP define `hash_equals(string $known_string, string $user_string)`, con el valor conocido primero. Aquí los argumentos están invertidos respecto a esa convención; la comparación sigue siendo de tiempo constante, pero conviene acostumbrarse al orden documentado, porque hace el código más legible para quien lo revise.

El resto es disciplina, y es la parte que ninguna función puede hacer por ti: **todo form que modifique algo debe imprimir `csrf_field()`, y todo controller que reciba esa POST debe llamar a `csrf_validate()` antes de tocar la base de datos**. Un solo endpoint olvidado anula el trabajo hecho en todos los demás.

## Iniciar la sesión del usuario

Cuando las credenciales resultan correctas, el proyecto no se limita a escribir los datos en la sesión:

```php
function start_session(array $user): void
{
    session_regenerate_id(true);
    $_SESSION['user_data'] = $user;
    $_SESSION['user_logged_in'] = true;
}
```

Código completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-22/es/parte-06/cap-22/listing-03.php)

Fuente real: [`includes/auth.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

`session_regenerate_id(true)` es la segunda defensa contra la **session fixation** de la que hablábamos antes, y actúa desde un ángulo distinto que `use_strict_mode`. El razonamiento es este: aun admitiendo que un atacante haya conseguido que la víctima use un ID de sesión que él conoce, ese ID **se tira justo en el momento en que el login tiene éxito**. El usuario autenticado continúa con un ID nuevo que el atacante no ha visto nunca. El login es el momento en el que la sesión cambia de valor — antes era una sesión anónima, ahora es una sesión con privilegios — y es exactamente ahí donde hay que renovar el identificador.

El argumento `true` le dice a PHP que **elimine** el fichero de la sesión antigua en lugar de dejarlo ahí. Sin él, el ID viejo seguiría siendo válido en el server: el atacante podría seguir usándolo y volveríamos al punto de partida. Es un parámetro que se olvida con facilidad y que deja la línea casi inútil si se omite.

## Verificar el login

`verify_login()` pone las comprobaciones en fila, y el orden cuenta una lógica precisa:

```php
function verify_login(mysqli $conn, string $email, string $password, string $token): array
{
    $res = ['success' => true, 'message' => ''];
    if (!csrf_validate($token)) {
        $res['success'] = false;
        $res['message'] = 'Invalid token';
        return $res;
    }
    if (!validatePassword($password) || !verifyEmail($email)) {
        $res['success'] = false;
        $res['message'] = 'Invalid email or password';
        return $res;
    }
    $user = find_user_by_email($conn, $email);
```

Código completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-22/es/parte-06/cap-22/listing-04.php)

Fuente real: [`includes/auth.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

Primero el token CSRF, luego la forma de los datos, y solo al final la base de datos. Es el principio del **fail fast**: las comprobaciones que no cuestan nada van primero, así una petición malformada o falsificada se rechaza sin haber abierto nunca una conexión ni consultado una tabla. Cada rama de error hace `return` inmediato — no hay `else` anidados, y nunca se llega al código siguiente por descuido.

Fíjate también en el mensaje del segundo bloque: `'Invalid email or password'`, sin decir cuál de los dos está mal. No es pereza. Si el sistema respondiera "este email no existe", un atacante podría probar miles de direcciones y construirse la lista de usuarios registrados — se llama **user enumeration**, y es el primer paso hacia un ataque dirigido. Responder siempre igual, tanto si el email no existe como si la password es incorrecta, no regala información.

La comparación de la password es la pieza más importante del capítulo:

```php
if (!$user || !password_verify($password, $user['password'])) {
    $res['success'] = false;
    $res['message'] = 'Wrong password or user doesn´t exist';
    return $res;
}
if (password_needs_rehash($user['password'], PASSWORD_DEFAULT)) {
    update_password_hash($conn, $user['id'], password_hash($password, PASSWORD_DEFAULT));
}
```

Código completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-22/es/parte-06/cap-22/listing-05.php)

Fuente real: [`includes/auth.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

En la base de datos **no hay ninguna password**. Lo que hay es el resultado de `password_hash()`, una función de un solo sentido: de la password se obtiene el hash, del hash no se vuelve atrás. Cuando el usuario hace login no comparamos dos passwords, sino que le damos a `password_verify()` la password recién escrita y el hash guardado, y dejamos que sea ella quien diga si se corresponden.

¿Por qué no un simple `md5($password)`, como se veía en tanto código PHP de hace quince años? Por dos motivos. El primero es que MD5 y SHA-1 son **rápidos**, y para los hashes de password la velocidad es un defecto: una GPU moderna prueba miles de millones de combinaciones por segundo, así que una base de datos robada se convierte en una lista de passwords en claro en cuestión de horas. `password_hash()` usa bcrypt (o Argon2), algoritmos diseñados para ser **lentos** y con un coste configurable que se puede subir a medida que mejora el hardware. El segundo motivo es el **salt**: `password_hash()` genera automáticamente un valor aleatorio distinto para cada usuario y lo incorpora en el hash resultante. Dos usuarios con la misma password obtienen hashes distintos, y las rainbow tables — tablas precalculadas de hashes comunes — dejan de servir. No tienes que gestionar tú el salt: ya está dentro de la cadena que guardas, junto con el algoritmo y el coste, y por eso la columna `password` mide 255 caracteres y no 32.

`password_needs_rehash()` es la parte con visión de futuro. Los algoritmos envejecen: dentro de unos años `PASSWORD_DEFAULT` apuntará a algo más robusto, o querrás subir el coste de bcrypt. Pero los hashes que ya están en la base de datos siguen siendo los viejos, y no puedes recalcularlos porque no conoces las passwords. El único momento en el que la password te pasa por delante en claro es el login: entonces, si el hash guardado ya no respeta los parámetros actuales, se recalcula al vuelo y se actualiza. El resultado es que la base de datos se actualiza sola, un usuario cada vez, sin pedirle a nadie que cambie su password. Tres líneas que te ahorran una migración dolorosa dentro de cinco años.

## Registro

`verify_signup()` sigue la misma estructura, con el añadido del problema de los duplicados:

```php
function verify_signup(mysqli $conn, string $email, string $password, $username, string $token): array
{
    $res = ['success' => true, 'message' => ''];
    if (!csrf_validate($token)) {
        $res['success'] = false;
        $res['message'] = 'Invalid token';
        return $res;
    }
    if (!validateUserName($username)) {
        $res['success'] = false;
        $res['message'] = 'Invalid user name';
        return $res;
    }
```

Código completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-22/es/parte-06/cap-22/listing-06.php)

Fuente real: [`includes/auth.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

Aquí también: token, luego formato, luego base de datos. La función continúa comprobando que el email no esté ya registrado y que la password cumpla los requisitos mínimos definidos en `config.php`.

Dos observaciones que valen más allá de este proyecto. La primera: la comprobación "¿ya existe un usuario con este email?" hecha en PHP **no basta por sí sola**. Entre el momento en que consultas la tabla y el momento en que escribes la fila pasa un instante, y dos registros simultáneos con el mismo email pueden pasar ambos la comprobación. Es una **race condition**, y la única defensa real es la restricción `UNIQUE` sobre la columna a nivel de base de datos — que de hecho está en el esquema de la tabla `users`. La comprobación en PHP sirve para dar un mensaje de error amable; la restricción sirve para garantizar la integridad.

La segunda: cuando la validación pasa, `controller/signup.php` guarda el usuario con el rol `user`, **siempre**. El rol no llega nunca del form. Dicho así parece obvio, pero es exactamente el tipo de detalle que se escapa: si el campo del rol fuera un `<select>` enviado por el cliente, cualquiera podría registrarse como `admin` modificando el HTML con las herramientas de desarrollo del browser. **Todo lo que decide sobre privilegios se establece en el server.**

![El formulario de registro, servido desde la misma página mediante pestañas. Ambos formularios incluyen el campo oculto con el token CSRF.](figures/cap-22/signup-form.png)

## Roles

Con la autenticación en su sitio, pasamos a la autorización. `includes/acl.php` (de *Access Control List*) mantiene juntos los roles y las funciones que los consultan:

```php
<?php

declare(strict_types=1);

const ROLE_USER = 'user';
const ROLE_ADMIN = 'admin';
const ROLE_EDITOR = 'editor';

function get_user_login_data(): array
{
    return $_SESSION['user_data'] ?? [];
}

function get_user_role(): string
{
    return get_user_login_data()['role_type'] ?? 'user';
}

function user_can_update(): bool
{
    return in_array(get_user_role(), [ROLE_ADMIN, ROLE_EDITOR]);
}

function user_can_delete(): bool
{
    return get_user_role() === ROLE_ADMIN;
}
```

Código completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-22/es/parte-06/cap-22/listing-07.php)

Fuente real: [`includes/acl.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/acl.php).

Los roles son **constantes** y no cadenas repartidas por el código: si escribes `'admin'` a mano en diez sitios, el día que te equivoques al teclear uno de ellos la comprobación falla en silencio y el usuario simplemente deja de poder hacer algo. Con `ROLE_ADMIN`, una errata se convierte en un error de PHP, que es mucho más fácil de encontrar.

Fíjate en el valor por defecto de `get_user_role()`: si en la sesión no hay nada, la función devuelve `'user'`, es decir, el rol **menos privilegiado**. Es una aplicación del principio *fail closed* (o *fail secure*): cuando algo no está claro, el sistema debe denegar, no conceder. Lo contrario — devolver `'admin'` en caso de duda, o peor una cadena vacía que luego pasa una comparación laxa — es el tipo de decisión que convierte un bug trivial en un incidente.

Estas funciones devuelven un booleano y sirven para dos propósitos distintos, y hay que usar **los dos**. En la view deciden si mostrar o no un botón:

```php
<?php if (user_can_delete()): ?>
    <a class="btn btn-danger" href="...">DELETE</a>
<?php endif; ?>
```

En el controller deciden si la acción puede ejecutarse. Y aquí está el punto que nunca hay que olvidar: **esconder un botón no es seguridad**. El botón escondido no impide a nadie abrir las herramientas de desarrollo, leer la URL de la acción y llamarla a mano. La comprobación en la view sirve para la experiencia de uso — no mostrar al usuario cosas que no puede hacer; la comprobación en el controller sirve para la seguridad. Si tienes que saltarte una, sáltate la de la view. En el próximo capítulo vemos precisamente cómo aplica el proyecto estas comprobaciones a los controllers y a las rutas.

## En resumen

Un sistema de login se apoya en cinco piezas que trabajan juntas, y cada una cierra una puerta distinta. La **cookie de sesión** configurada con `httponly`, `secure`, `SameSite` y `use_strict_mode` protege el identificador del robo y de la fijación. La **regeneración del ID** en el login tira cualquier sesión que el usuario pudiera haber recibido de un atacante. El **token CSRF**, comparado con `hash_equals()`, garantiza que una POST venga realmente de nuestro form y no de un sitio hostil. Los **hashes de password** con `password_hash()`, `password_verify()` y `password_needs_rehash()` hacen que una base de datos robada no se convierta en una lista de credenciales. Los **roles**, verificados en el server y no solo en la view, deciden quién puede hacer qué.

Ninguna de estas piezas es opcional, y ninguna compensa la ausencia de otra: son defensa en profundidad, pensadas para que un único error no se convierta en un compromiso. El repositorio UMS las muestra de forma procedural, con funciones globales y estado en `$_SESSION`, y es la mejor manera de ver el mecanismo al desnudo. En la Parte IX los mismos conceptos volverán en forma de servicios inyectados, middleware y sesiones gestionadas por el container: cambiará el empaquetado, no la sustancia de lo que acabamos de ver.
