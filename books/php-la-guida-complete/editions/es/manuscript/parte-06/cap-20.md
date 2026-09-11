# 20. CRUD, búsqueda, ordenación y paginación

En `php-user-management-system`, la lista de usuarios crece progresivamente: primero muestra todos los registros, luego añade ordenación, búsqueda, paginación y finalmente las acciones de crear, actualizar y eliminar. Es el capítulo en el que un *script* se convierte en una **aplicación**: ya no una página que imprime una tabla, sino un conjunto de funciones que leen parámetros de la request, los usan para construir queries y devuelven vistas distintas según lo que pida el usuario.

Precisamente porque es la primera pieza que recibe input del exterior y lo convierte en SQL, es también el capítulo donde anidan los primeros riesgos serios. Los afrontaremos con honestidad: muestro el código del proyecto tal cual es — procedural, directo, pensado para dejarte ver el mecanismo — y en los puntos donde toma un atajo que en producción no es aceptable, me detengo a explicar por qué y cómo se corrige.

![La lista de usuarios de UMS: cabeceras de columna ordenables, filtro de búsqueda, selector de registros por página y barra de paginación. Aquí los 47 usuarios de ejemplo se reparten en 5 páginas.](figures/cap-20/user-list-pagination.png)

## Leer usuarios con parámetros

La función `getUsers()` recibe los parámetros de la página y construye la query:

```php
function getUsers(array $params = []): array
{
    $conn = getConnection();

    $records = [];

    $limit = $params['recordsPerPage'] ?? 10;
    $orderBy = $params['orderBy'] ?? 'id';
    $orderDir = $params['orderDir'] ?? 'DESC';
    $search = $params['search'] ?? '';
    $page = $params['page'] ?? 1;
    $start = $limit * ($page - 1);
    $sql = 'SELECT * FROM users';
```

Código completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-20/es/parte-06/cap-20/listing-01.php)

Fuente real: [`functions.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/functions.php).

Cinco parámetros, y cada uno llega de la **request**: `recordsPerPage` y `page` deciden cuántos registros leer y desde qué punto, `orderBy` y `orderDir` la columna y el sentido de la ordenación, `search` el texto a buscar. El operador `??` proporciona un valor por defecto a cada uno, así la función trabaja incluso en la primera visita, cuando la URL todavía no lleva ningún parámetro. Hasta aquí todo bien.

El problema es qué les pasa a estos valores justo después. En el repositorio la query se completa así — y aquí tengo que enseñarte el código real, porque es exactamente el punto sobre el que quiero que razones:

```php
$sql .= " ORDER BY $orderBy $orderDir  LIMIT  $start,$limit ";
```

Esos cuatro valores — `$orderBy`, `$orderDir`, `$start`, `$limit` — acaban **dentro de la cadena SQL por interpolación directa**. Y si `search` tiene valor, también se interpola en el `WHERE`. Cada vez que un dato que llega del usuario entra en una query concatenándolo como texto, debe saltar una alarma en tu cabeza: es la puerta de entrada de la **SQL injection**, la vulnerabilidad más clásica y más extendida de las aplicaciones web.

Vamos con el ejemplo concreto. Imagina que `search` se toma de la URL y se pega dentro de `WHERE username LIKE '%$search%'`. Un usuario normal busca `mario` y la query se convierte en `... LIKE '%mario%'`. Pero un atacante no escribe `mario`: escribe `x' OR '1'='1`. La query resultante ya no busca un nombre, contiene una **condición lógica inyectada** desde fuera que la base de datos ejecuta como si la hubieras escrito tú. Con payloads más elaborados se llega a leer otras tablas, extraer los hashes de las passwords, en algunos casos modificar o borrar datos. No es teoría: es el primer ataque que cualquiera prueba contra un formulario de búsqueda.

"Pero yo filtro el input", podrías pensar. En el proyecto, antes de llegar aquí, `search` pasa por `strip_tags(trim($search))`. Atención: `strip_tags()` elimina las **etiquetas HTML**, no tiene nada que ver con el SQL. Una comilla simple `'` — el carácter que necesita la injection — pasa indemne. Filtrar para un contexto (HTML) no protege de otro (SQL): cada contexto tiene sus propias reglas de *escaping*, y mezclarlas da una falsa sensación de seguridad. Esta, por cierto, es la razón por la que la función gemela `getTotalUserCount()` que veremos enseguida al menos llama a `real_escape_string()` sobre el término de búsqueda, mientras que `getUsers()` ni siquiera lo hace: dos funciones nacidas juntas, con dos niveles de protección distintos. Es exactamente el tipo de incoherencia que un *prepared statement* elimina de raíz.

Veamos entonces la versión correcta. El término de búsqueda debe **vincularse como parámetro**, no concatenarse:

```php
function getUsers(array $params, array $allowedColumns): array
{
    $conn = getConnection();
    $limit   = (int) ($params['recordsPerPage'] ?? 10);
    $page    = max(1, (int) ($params['page'] ?? 1));
    $start   = $limit * ($page - 1);
    $search  = (string) ($params['search'] ?? '');

    // orderBy es un IDENTIFICADOR, no un valor: hay que ponerlo en whitelist
    $want    = $params['orderBy'] ?? 'id';
    $orderBy = in_array($want, $allowedColumns, true) ? $want : 'id';
    $orderDir = ($params['orderDir'] ?? 'DESC') === 'ASC' ? 'ASC' : 'DESC';

    $sql = 'SELECT * FROM users';
    $types = '';
    $values = [];
    if ($search !== '') {
        $sql .= ' WHERE fiscalcode LIKE ? OR email LIKE ? OR username LIKE ?';
        $like = '%' . $search . '%';
        $types = 'sss';
        $values = [$like, $like, $like];
    }
    $sql .= " ORDER BY $orderBy $orderDir LIMIT ?, ?";
    $types .= 'ii';
    $values[] = $start;
    $values[] = $limit;

    $stmt = $conn->prepare($sql);
    $stmt->bind_param($types, ...$values);
    $stmt->execute();
    $result = $stmt->get_result();

    $records = [];
    while ($row = $result->fetch_assoc()) {
        $records[] = $row;
    }
    return $records;
}
```

Mira la diferencia. El texto de búsqueda ya no toca la cadena SQL: en su lugar hay un `?`, un **marcador de posición**, y el valor real viaja por separado mediante `bind_param()`. La base de datos recibe la estructura de la query y los datos por dos canales distintos, y ya no puede confundir un dato con un comando. Si el atacante escribe `x' OR '1'='1`, ese texto se convierte sencillamente en la cadena a buscar — la base de datos intenta encontrar un usuario cuyo username contenga literalmente `x' OR '1'='1`, no encuentra ninguno, y devuelve cero filas. El ataque se apaga sin causar daño. La búsqueda legítima sigue funcionando exactamente como antes.

Un detalle que confunde a todo el mundo, y que merece aclararse de una vez por todas: `$orderBy` y `$orderDir` **no pueden** pasarse como `?`. Los marcadores de los prepared statement vinculan **valores** — un número, una cadena, una fecha — no **identificadores** como los nombres de columna o las palabras clave `ASC`/`DESC`. `ORDER BY ?` no funciona: la base de datos espera ahí un nombre de columna, no un dato. La defensa correcta para los identificadores es distinta y se llama **whitelist**: se compara el valor recibido con una lista cerrada de columnas permitidas (`in_array($want, $allowedColumns, true)`) y, si no está en la lista, se recae en un valor por defecto seguro. La dirección se reduce a solo dos posibilidades, `ASC` o `DESC`, con el mismo principio. Regla general, tenla presente: **los valores se vinculan, los identificadores se ponen en whitelist**. Es la distinción que separa a quien ha entendido la SQL injection de quien solo la conoce de oídas.

En el proyecto enterprise de la Parte IX esta lógica acabará dentro de un *repository* testeable, donde la construcción de la query está aislada y las columnas permitidas se declaran en un único lugar. Pero el principio es idéntico al que acabas de ver: parámetros para los valores, whitelist para los identificadores.

## Búsqueda y paginación

El recuento total usa una función separada. Sirve para calcular cuántas páginas mostrar:

```php
function getTotalUserCount(string $search = ''): int
{
    $conn = getConnection();

    $sql = 'SELECT COUNT(*) as total FROM users';
    if ($search) {
        $sql .= ' WHERE';
        if (is_numeric($search)) {
            $sql .= " id = $search OR age = $search";
        } else {
            $search = $conn->real_escape_string($search);
            $sql .= " fiscalcode like '%$search%' OR email like '%$search%' OR
             username like '%$search%'";
        }
    }
```

Código completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-20/es/parte-06/cap-20/listing-02.php)

Fuente real: [`functions.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/functions.php).

Aquí el proyecto usa `real_escape_string()`, que es un paso adelante respecto a `getUsers()`: la función hace el *escape* de los caracteres especiales — la comilla `'` se convierte en `\'` — así el texto ya no puede cerrar la cadena e inyectar SQL. Funciona, pero vale la pena entender por qué los prepared statement siguen siendo la mejor opción. El *escaping* es una defensa que tienes que acordarte de aplicar **cada vez**, en **cada** variable, con la función correcta para el tipo correcto: basta un `real_escape_string()` olvidado en un punto y la puerta se vuelve a abrir. El prepared statement, en cambio, separa datos y comandos por construcción: no hay nada que acordarse de hacer. La diferencia entre las dos funciones hermanas de este proyecto — una con escape, otra sin él — es la prueba viviente de lo frágil que es fiarse de la memoria. Fíjate también en la rama `is_numeric($search)`: ahí el valor entra en la query sin ni siquiera el escape, sobre el supuesto de que si es numérico no puede hacer daño. Es un supuesto que aguanta para el carácter individual, pero es de nuevo el tipo de razonamiento caso por caso que los prepared statement hacen innecesario.

Más allá de la seguridad, hay una decisión de **diseño** correcta y vale la pena reconocerla: `getTotalUserCount()` es una función aparte, distinta de `getUsers()`. Porque contar las filas y leerlas son dos responsabilidades diferentes. La lista sirve solo los registros de la página actual — diez filas, con `LIMIT` — mientras que el recuento necesita saber cuántos registros existen **en total**, ignorando el `LIMIT`, porque es ese número el que nos dice cuántas páginas hacen falta. Son dos preguntas distintas, por tanto dos queries distintas, por tanto dos funciones. Es una pequeña aplicación del principio de responsabilidad única: si hubieras puesto todo en una sola función, habrías tenido que devolver dos cosas inconexas — las filas *y* el total — y tarde o temprano alguien las habría usado de forma confusa.

Es el recuento el que hace posible la aritmética de la paginación, y es más simple de lo que parece. Con `recordsPerPage` registros por página, la página `page` debe saltar las filas de las páginas anteriores: `start = recordsPerPage * (page - 1)`. La página 1 empieza en 0, la página 2 en 10, la página 3 en 20, y así sucesivamente. La cláusula `LIMIT start, recordsPerPage` le dice a la base de datos "salta `start` filas, luego dame `recordsPerPage`". El número total de páginas es `ceil(total / recordsPerPage)`: con 47 usuarios y 10 por página salen 5 páginas, la última con solo 7 registros. Tres fórmulas, y ahí está toda la paginación que ves al final de la lista.

![La misma lista tras una búsqueda: la cláusula `WHERE` reduce los resultados y los parámetros de búsqueda se mantienen en los enlaces de ordenación y paginación.](figures/cap-20/search-filter.png)

Un detalle de la experiencia de uso visible en la figura: cuando buscas, los parámetros de búsqueda se mantienen en los enlaces de las columnas y en la barra de paginación. No es casualidad — es código que, en cada enlace, reconstruye la *query string* completa. Sin él, cambiar de página o reordenar borraría la búsqueda, y el usuario se encontraría de golpe con todos los registros. Es el tipo de detalle que distingue una aplicación cuidada de un ejercicio.

## Un único form para create y update

La view `userForm.php` decide si el form está creando o actualizando un usuario:

```php
<?php

$action = 'store';
$buttonName = 'SAVE';
$formTile = 'INSERT USER';
if ($user && $user['id']) {
    $action = 'update';
    $buttonName = 'UPDATE';
    $formTile = 'UPDATE USER';
}
foreach ($user as &$value) {
    $value = htmlspecialchars($value ?? '');
}
?>
```

Código completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-20/es/parte-06/cap-20/listing-03.php)

Fuente real: [`view/userForm.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/view/userForm.php).

Un **único** form para dos operaciones. La lógica es simple: si nos llega un `$user` con un `id`, estamos editando y preparamos la acción, la etiqueta del botón y el título en consecuencia; en caso contrario estamos creando. Es una aplicación concreta del principio **DRY** (*Don't Repeat Yourself*): los campos del form — username, email, edad, rol — son idénticos en ambos casos, y mantener dos forms casi iguales significaría aplicar cada cambio en dos sitios, con la certeza estadística de olvidar uno. Un solo form, que cambia solo las pocas cosas que de verdad difieren, es más corto de escribir y más seguro de mantener.

La línea verdaderamente importante es el `foreach` final, y es de nuevo una cuestión de seguridad — esta vez de otra familia. Antes de reinsertar los valores en los campos del form, cada valor pasa por `htmlspecialchars()`. El motivo: estos datos vienen de la **base de datos**, pero acabaron en la base de datos porque *alguien los escribió*. Si un usuario se hubiera registrado con el username `<script>alert(document.cookie)</script>`, imprimirlo tal cual dentro de un atributo `value` del form ejecutaría ese script en el browser de cualquiera que abra la página de edición. Es el ataque **XSS** (*Cross-Site Scripting*), el primo de la SQL injection pero en el lado cliente. `htmlspecialchars()` convierte los caracteres peligrosos en sus entidades HTML — `<` se convierte en `&lt;`, `"` en `&quot;` — así el texto se *muestra* en lugar de *ejecutarse*.

El principio que hay que llevarse a casa es simétrico al del SQL: **haz el escape de los datos en el contexto en el que los insertas**. Hacia la base de datos, parámetros; hacia el HTML, `htmlspecialchars()`. Y sobre todo: no te fíes nunca de un dato solo porque "viene de la base de datos" y no directamente del usuario. A la base de datos llega igualmente cosa escrita por alguien, y ese alguien podría no tener buenas intenciones.

## Guardar un nuevo usuario

`storeUser()` usa prepared statement y guarda la password con `password_hash()`:

```php
function storeUser(array $data): int
{
    $conn = getConnection();
    $sql = 'INSERT INTO users (username,email,fiscalcode,age,avatar, password,role_type) values( ?, ?, ?,?,?,?,?)';
    $stm = $conn->prepare($sql);
    $password = password_hash($data['password'], PASSWORD_DEFAULT);
    $stm->bind_param(
        'sssisss',
        $data['username'],
        $data['email'],
        $data['fiscalcode'],
        $data['age'],
        $data['avatar'],
        $password,
        $data['role_type']

    );
    $stm->execute();
```

Código completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-20/es/parte-06/cap-20/listing-04.php)

Fuente real: [`model/User.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/model/User.php).

Aquí el proyecto hace las cosas bien, y es útil comparar esta función con la `getUsers()` de antes: donde la lectura tomaba el atajo, la escritura usa un prepared statement completo. Siete marcadores `?` en la query, siete valores pasados a `bind_param()`, y ningún dato del usuario que toque la cadena SQL. Un `INSERT` es potencialmente más peligroso que un `SELECT` — escribe en la base de datos — así que es correcto que aquí la disciplina sea rigurosa.

El primer argumento de `bind_param()`, la cadena `'sssisss'`, es la pieza que descoloca a quien la ve por primera vez. Es la declaración de los **tipos**, un carácter por cada marcador, en orden: `s` para *string*, `i` para *integer*, `d` para *double*, `b` para *blob*. Aquí: username string, email string, fiscalcode string, edad **integer**, avatar string, password string, rol string — de ahí `sssisss`. La cadena de tipos y la lista de valores deben corresponderse en número y en orden: si te equivocas y declaras `s` donde el valor es un integer normalmente no es un drama, pero si intercambias el orden de los valores escribes el email en la columna del fiscalcode sin que PHP proteste. Es el único punto frágil de los prepared statement con mysqli, y en la Parte IX veremos que PDO ofrece una alternativa con parámetros **nombrados** (`:username`) que elimina el problema del recuento.

Fíjate también en que la password nunca se guarda tal cual: pasa por `password_hash()` antes de entrar en el `bind_param()`, exactamente como explicamos en el Capítulo 22. En la base de datos acaba el hash, nunca la password en claro.

## Actualizar un usuario

El update construye dinámicamente los campos opcionales para password y rol:

```php
function updateUser(array $data, int $id): bool
{
    $conn = getConnection();
    $types = 'sssis';
    $values = [
        $data['username'],
        $data['email'],
        $data['fiscalcode'],
        $data['age'],
        $data['avatar']
    ];
    $sql = 'UPDATE users SET username = ?, email = ?, fiscalcode = ?, age = ?,avatar=? ';
    if ($data['password']) {
        $sql .= ', password = ? ';
        $types .= 's';
        $values[] = password_hash($data['password'], PASSWORD_DEFAULT);
    }
```

Código completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-20/es/parte-06/cap-20/listing-05.php)

Fuente real: [`model/User.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/model/User.php).

El update tiene un requisito más que el insert: algunos campos son **opcionales**. Si el usuario deja vacío el campo password mientras edita, no queremos sobrescribir el hash existente con una cadena vacía — queremos dejar la password como estaba. Lo mismo vale para el rol. La solución del proyecto es construir la query **pieza a pieza**: se parte de los campos siempre presentes (`username`, `email`, `fiscalcode`, `age`, `avatar`), y solo si `$data['password']` tiene valor se añade `, password = ?` a la query, `s` a la cadena de tipos y el nuevo hash a la lista de valores.

El punto delicado de este esquema es que **tres cosas deben mantenerse alineadas**: el texto SQL, la cadena de tipos y el array de valores. Cada vez que añades un `?` a la query debes añadir el carácter de tipo correspondiente *y* el valor, en el mismo orden. El código lo hace con cuidado — fíjate en cómo las tres actualizaciones (`$sql .=`, `$types .=`, `$values[] =`) viajan siempre juntas, en bloque. Es un patrón que funciona pero exige disciplina: es exactamente la repetitividad que en la Parte IX un *query builder* o un ORM quitan de en medio, generando los marcadores y los tipos automáticamente. Aquí, en el estado procedural, verlo a mano te hace entender qué hacen por ti esas abstracciones.

Una nota de método que vale más allá de esta función: conviene validar bien `$data` *antes* de llegar al model. El model debería recibir datos ya coherentes — una edad que de verdad sea un número, un email que de verdad tenga la forma de un email — y ocuparse solo de guardarlos. Mezclar validación y persistencia en la misma función es otro de esos atajos que parecen inofensivos y luego hacen el código difícil de testear y de reutilizar.

## Controller de acciones

El controller `updateRecord.php` protege las acciones y enruta `store`, `update` y `delete`:

```php
<?php

declare(strict_types=1);
require_once '../includes/session.php';
require '../functions.php';
require_once '../includes/acl.php';
if (!is_user_logged_in() || !user_can_update()) {
    redirect('../login.php');
}

require '../model/User.php';
$action = getParam('action');
switch ($action) {
```

Código completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-20/es/parte-06/cap-20/listing-06.php)

Fuente real: [`controller/updateRecord.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/controller/updateRecord.php).

El controller es la puerta de entrada de las acciones que modifican datos, y lo primero que hace — antes incluso de mirar *qué* acción — es la comprobación de acceso: `is_user_logged_in()` verifica la autenticación, `user_can_update()` la autorización. Si falta una de las dos, `redirect()` y la petición termina ahí. Solo tras pasar esta cancela se carga el model y se despacha la acción con el `switch`.

El orden es lo importante, y es la misma lógica del *fail fast* que vimos en el Capítulo 22: **primero autorizas, luego actúas**. Ni un solo registro se toca antes de que la comprobación haya pasado. Ponerla arriba, y no dispersa dentro de los `case` individuales, garantiza que ninguna rama del `switch` pueda alcanzarse por error sin comprobación.

Y aquí vuelve el punto que anticipé en el capítulo anterior y que vale la pena machacar, porque es el error conceptual más común sobre la autorización: **el controller no debe fiarse de la view**. En el Capítulo 23 veremos que el menú esconde los botones "editar" y "eliminar" a los usuarios sin los permisos. Pero esconder un botón es solo cosmética: la URL `controller/updateRecord.php?action=delete&id=5` existe igualmente, y cualquiera puede escribirla a mano en la barra de direcciones o construirla con `curl`. Si la única defensa fuera el botón escondido, un usuario normal podría eliminar registros simplemente adivinando la URL. Es la comprobación *aquí, en el controller*, en el server, la que hace que la acción esté de verdad protegida. La view mejora la experiencia; el controller garantiza la seguridad. Cuando tengas que elegir solo una, elige siempre el controller.

## En resumen

Este capítulo es el primer salto real de script a aplicación, y pone en fila los temas que nos acompañarán hasta el final del libro. La **lectura paramétrica** (`getUsers`) nos obligó a enfrentarnos a la SQL injection: los valores se vinculan con prepared statements, los identificadores como `ORDER BY` se ponen en whitelist — nunca concatenar input del usuario en la cadena SQL. El **recuento separado** (`getTotalUserCount`) nos dio la aritmética de la paginación y un ejemplo de responsabilidades bien divididas. El **form único** para create y update mostró el principio DRY y el escaping con `htmlspecialchars()` contra el XSS. Las funciones de **escritura** (`storeUser`, `updateUser`) usaron prepared statements como es debido, con la cadena de tipos y la construcción dinámica de los campos opcionales. El **controller** puso la autorización antes de la acción, en el server, sin fiarse de lo que la view muestra o esconde.

El hilo que las une es uno solo: **todo dato que cruza una frontera — de la request a la query, de la base de datos al HTML — debe tratarse según las reglas del contexto en el que entra**. El repositorio UMS lo hace de forma procedural, con algunas incoherencias que preferí mostrarte en lugar de esconder, porque es aprendiendo a reconocerlas como uno se vuelve capaz de corregirlas. En la Parte IX los mismos mecanismos volverán dentro de repositories, query builders y validación centralizada: desaparecerán los atajos, pero los principios seguirán siendo exactamente estos.
