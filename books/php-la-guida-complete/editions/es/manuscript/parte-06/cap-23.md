# 23. Navegación protegida y acciones basadas en roles

En `php-user-management-system`, el login no usa AJAX. Las requests son forms POST tradicionales y redirects. Este capítulo se concentra entonces en lo que el código público implementa realmente: páginas protegidas, menú condicional y acciones permitidas por rol.

El tema de fondo es uno solo, y ya lo has encontrado en los capítulos anteriores: la **autorización**. Pero aquí lo vemos desde un ángulo nuevo, el de la **defensa en profundidad**. Verás el mismo permiso — "¿este usuario puede editar? ¿puede eliminar?" — comprobado en varios puntos distintos de la aplicación: cuando se renderiza la página, cuando se construye el menú, cuando se muestran los botones de la lista, y de nuevo dentro del controller. A primera vista parece repetición inútil. No lo es, y ese es exactamente el punto que este capítulo debe dejar claro: **cada capa protege algo distinto, y ninguna por sí sola basta**.

## Proteger la página principal

`index.php` intenta primero el auto-login mediante remember me, luego verifica la sesión:

```php
require_once 'includes/acl.php';
require_once 'includes/auth.php';
tryAutoLogin();
if (!is_user_logged_in()) {
    redirect('login.php');
}
require_once 'includes/csrf.php';
```

Código completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-23/es/parte-06/cap-23/listing-01.php)

Fuente real: [`index.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/index.php).

La primera capa es la más externa: antes incluso de producir una sola línea de HTML, la página decide si el usuario tiene derecho a estar ahí. La secuencia importa. Se intenta el auto-login (que vimos en el Capítulo 24), así un usuario con una cookie de remember me válida es reconocido; luego se comprueba `is_user_logged_in()` y, si no hay sesión, `redirect()` lleva al login y la petición termina ahí. El detalle importante es que esta comprobación va **antes del rendering**. Si el usuario no está autorizado no debe ver ni siquiera la página parcial — nada de header, nada de tabla vacía, nada. Poner la comprobación arriba, y no a mitad de página, garantiza que ningún fragmento confidencial llegue al browser de quien no tiene derecho a verlo.

## Leer los datos del usuario

Las funciones ACL leen el estado de la sesión:

```php
function is_user_logged_in(): bool
{
    return !empty($_SESSION['user_logged_in']);
}

function get_user_login_data(): array
{
    return $_SESSION['user_data'] ?? [];
}

function get_user_role(): string
{
    return get_user_login_data()['role_type'] ?? 'user';
}
```

Código completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-23/es/parte-06/cap-23/listing-02.php)

Fuente real: [`includes/acl.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/acl.php).

Hay un principio en estas tres funciones que vale más de lo que parece: la fuente de la identidad del usuario es **una sola**, la sesión. El rol se lee de `$_SESSION['user_data']['role_type']`, nunca de un parámetro `GET` o `POST`. Es esencial entender por qué. La sesión vive en el **server** y fue poblada en el login, tras la verificación de la password: el usuario no puede modificarla. Un parámetro `GET` o `POST`, en cambio, lo escribe el cliente y el usuario puede poner en él lo que quiera. Si aunque solo fuera en un punto el código decidiera los permisos mirando `$_GET['role']` en lugar de la sesión, cualquiera podría promoverse a administrador añadiendo `?role=admin` a la URL. Una única fuente de verdad para la identidad, y esa fuente está bajo el control del server: es la base sobre la que se apoyan todas las capas posteriores. Fíjate también en el valor por defecto `'user'` en `get_user_role()` — si falta el dato, se asume el rol menos privilegiado, el *fail closed* que ya comentamos en el Capítulo 22.

## Menú condicional

La navbar muestra el menú de la aplicación solo si el usuario está logueado:

```php
<?php
if (is_user_logged_in()): ?>
    <ul class="navbar-nav me-auto mb-2 mb-md-0">
        <li class="nav-item">
            <a class="nav-link <?= $indexActive ?>" aria-current="page" href="<?= $indexPage ?>"><i
                        class="fa-solid fa-users"></i>Users</a>
        </li>
```

Código completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-23/es/parte-06/cap-23/listing-03.php)

Fuente real: [`view/nav.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/view/nav.php).

La segunda capa es el menú. Mostrar las entradas de la aplicación solo a quien está logueado es **usabilidad**: no tiene sentido ofrecer "Users" o "New user" a un visitante que todavía tiene que autenticarse. Pero cuidado con no confundir los planos: esto es un embellecimiento de la interfaz, **no** una medida de seguridad. El menú decide qué *ve* el usuario, no qué *puede hacer* el usuario. Un enlace ausente no impide a nadie escribir a mano la URL correspondiente. La seguridad de verdad no está aquí — está en los controllers, y llegamos allí en dos apartados.

## Acciones en la lista

La lista de usuarios muestra update y delete según el rol:

```php
<?php
if (user_can_update()): ?>
    <div class="row">

        <div class="col-6">
            <a class="btn btn-success" href="?id=<?= $user['id'] ?>&action=edit&<?= $navParams ?>">
                <i class="fa fa-pen"></i>
                UPDATE
            </a>
        </div>
```

Código completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-23/es/parte-06/cap-23/listing-04.php)

Fuente real: [`view/userList.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/view/userList.php).

La tercera capa es más fina que el menú: no decide si mostrar *la aplicación*, sino si mostrar las *acciones* individuales. El botón UPDATE aparece solo si `user_can_update()`, y más abajo en la misma view el botón DELETE aparece solo si `user_can_delete()`. Un usuario con rol `user` ve el listado pero no los botones de acción; un `editor` ve UPDATE; solo un `admin` ve también DELETE. Es exactamente lo que se observa en la figura del Capítulo 20, donde el administrador tiene ambos botones junto a cada fila.

Y vale, por tercera vez, la misma advertencia: esconder el botón es comodidad, no seguridad. No te fíes nunca de que un botón no aparezca. La URL de la acción existe igualmente, y debe protegerse en otro sitio.

## Controller protegido

`controller/updateRecord.php` rechaza a quien no está logueado o no puede actualizar:

```php
require_once '../includes/acl.php';
if (!is_user_logged_in() || !user_can_update()) {
    redirect('../login.php');
}

require '../model/User.php';
$action = getParam('action');
switch ($action) {
```

Código completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-23/es/parte-06/cap-23/listing-05.php)

Fuente real: [`controller/updateRecord.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/controller/updateRecord.php).

Aquí está la capa que de verdad cuenta — la que las tres anteriores *no* pueden sustituir. Aquí, en el controller, en el server, antes de ejecutar cualquier acción, se vuelve a comprobar `is_user_logged_in()` y `user_can_update()`. Esta es la seguridad de verdad. Ahora puedes ver por qué las capas no son redundantes: la comprobación en el menú y en la lista impide al usuario honesto *ver* cosas que no le conciernen, pero es la comprobación en el controller la que impide al usuario malicioso *hacer* cosas a las que no tiene derecho. La primera mejora la experiencia, la segunda protege el dato. Si te pidiera eliminar una, eliminarías las de las views — no esta. Es la regla que repetí en el Capítulo 20 y repito aquí porque es el error conceptual más común sobre la autorización: **el botón escondido es cosmética, la comprobación en el controller es seguridad**.

La eliminación requiere una comprobación aún más estricta:

```php
case 'delete':
    if (!user_can_delete()) {
        redirect('../login.php');
    }

    $id = (int)getParam('id', 0);
    $user = getUserById($id);
```

Código completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-23/es/parte-06/cap-23/listing-06.php)

Fuente real: [`controller/updateRecord.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/controller/updateRecord.php).

Fíjate en la gradación de los permisos. Para entrar en el controller basta `user_can_update()` — que vale para `editor` y `admin`. Pero el `case 'delete'` añade una comprobación **más estricta**, `user_can_delete()`, que vale solo para `admin`. Es el principio del **mínimo privilegio** aplicado a la acción: un editor puede modificar, pero no destruir. La acción más peligrosa requiere el permiso más alto, y la comprobación específica está dentro de la rama que ejecuta esa acción, así no hay forma de llegar a la eliminación solo con los permisos de modificación.

## Logout vía POST

El logout usa POST y CSRF, no un simple enlace GET:

```php
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(419);
    exit('Invalid request method');
}
$fromAll = getParam('fromAll');
if (!csrf_validate(post_string('csrf_token'))) {
    http_response_code(419);
    exit('Invalid token');
}
```

Código completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-23/es/parte-06/cap-23/listing-07.php)

Fuente real: [`controller/logout.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/controller/logout.php).

También el logout, que parece la acción más inocente del mundo, tiene sus reglas. El proyecto rechaza las peticiones que no son POST (`http_response_code(419)`) y valida el token CSRF antes de proceder. ¿Por qué tanta cautela solo para "salir"? Porque el logout **cambia el estado** — termina una sesión — y las acciones que cambian estado no deben nunca exponerse como simples enlaces GET. Si el logout fuera un `<a href="logout.php">`, un atacante podría poner en una página una imagen `<img src="https://nuestrositio/logout.php">` y tu browser, al cargarla, te desconectaría sin que lo supieras. Es un CSRF de logout: molesto más que dañino, pero del mismo molde exacto que el ataque que estudiamos en el Capítulo 22. La regla es tajante y vale para **cada** acción que modifica algo — login, logout, creación, eliminación: se pasa por POST, y se valida el token CSRF. Los GET son para leer, los POST para cambiar.

## En resumen

El proyecto UMS no implementa login AJAX: implementa un flujo clásico y sólido, y su lección más importante es la **defensa en profundidad**. La identidad tiene una **única fuente**, la sesión, nunca un parámetro del cliente. El permiso se comprueba luego en varias capas, y cada una tiene un cometido distinto: la comprobación **antes del rendering** deja fuera a quien no está logueado; el **menú condicional** y los **botones de acción** adaptan la interfaz a lo que el usuario puede hacer, pero son usabilidad; la **comprobación en el controller**, en el server, es la única que protege de verdad el dato, con un requisito **más estricto** para la acción más peligrosa. Por último, las acciones que cambian estado pasan por **POST con CSRF**, logout incluido.

Si tuviera que reducirlo todo a una frase: las capas en las views sirven al usuario honesto, la comprobación en el controller defiende contra el malicioso — y como no sabes de antemano con cuál de los dos estás tratando, las mantienes todas. En la Parte IX esta lógica dispersa en funciones y views se convertirá en un middleware de autorización, un único punto atravesado por cada petición; pero el principio de la defensa en profundidad seguirá siendo exactamente este.
