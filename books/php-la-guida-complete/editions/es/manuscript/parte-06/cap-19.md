# 19. User Management System: estructura, datos y layout

El User Management System es el primer proyecto completo del libro. Aquí todavía no usamos framework ni Composer: el proyecto público de referencia, [`php-user-management-system`](https://github.com/hidran/php-user-management-system), es una aplicación procedural con `mysqli`, includes explícitos, templates PHP y controllers separados.

Esta elección es deliberada, y vale la pena defenderla abiertamente, porque a algunos les parecerá un paso atrás. En el resto del libro hablamos de *enterprise PHP*: MVC, PSR-4, dependency injection, repositories, tests. ¿Por qué entonces empezar de nuevo desde una aplicación procedural con `mysqli` y `require` a mano? Porque un framework es, en el fondo, un conjunto de respuestas a preguntas que primero debes haberte hecho. Si nunca has sentido el dolor de incluir veinte archivos a mano, el autoload de Composer es magia incomprensible; si nunca has mezclado lógica y HTML en el mismo archivo, la separación controller/view es una regla que sufres en lugar de entender; si nunca has escrito una query concatenando cadenas, no captas de verdad lo que te ahorra un query builder. Este proyecto te hace vivir el flujo más directo — configuración, conexión, query, template, form, sesiones, redirect — para que en la Parte IX, cuando el mismo código se convierta en clases y servicios, sepas *por qué*. Primero construimos la versión que un framework luego mejora.

## Repositorio y commits

Puedes leer la historia del proyecto así:

```bash
git clone https://github.com/hidran/php-user-management-system.git
cd php-user-management-system
git log --reverse --oneline
```

Código completo: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-19/es/parte-06/cap-19/listing-01.sh)

Fuente real: [repositorio `php-user-management-system`](https://github.com/hidran/php-user-management-system).

Vale la pena leer el proyecto **a través de su historia**, no solo en su estado final. `git log --reverse` muestra los commits del primero al último, y ese orden es en sí mismo un recorrido didáctico: primero configuración y conexión MySQL, luego lista de usuarios, ordenación, búsqueda, paginación, CRUD, upload, roles, login, CSRF, sesiones y remember me. Cada commit añade una funcionalidad sobre la anterior, y leyéndolos en orden ves la aplicación **crecer** en lugar de encontrártela ya hecha. Es una forma de estudiar código ajeno que te recomiendo más allá de este libro: un buen historial de Git es una explicación escrita pieza a pieza.

## Configuración de la aplicación

El archivo `config.php` contiene los ajustes centrales. En el commit final incluye base de datos, paginación, columnas ordenables, upload, roles y remember me:

```php
<?php

return [
    'mysql_host' => 'db',
    'mysql_user' => 'root',
    'mysql_password' => 'hidran',
    'mysql_db' => 'corsophp',
    'recordsPerPage' => 10,
    'maxLinks' => 10,
    'orderByColumns' =>
        ['id', 'username', 'fiscalcode', 'age', 'email', 'role_type'],
    'uploadDir' => 'avatar',
    'mimeTypes' => ['image/jpeg', 'image/png', 'image/gif'],
    'roleTypes' => ['user', 'admin', 'editor'],
    'rememberMeTTL' => 60 * 60 * 24 * 30,
    'rememberMeCookieName' => 'ums_remember_token'
];
```

Código completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-19/es/parte-06/cap-19/listing-02.php)

Fuente real: [`config.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/config.php).

Un único archivo que devuelve un array asociativo: es la forma más simple de centralizar la configuración, y a pesar de su simplicidad aplica un principio importante. Todo lo que podrías querer cambiar sin tocar la lógica — cuántos registros por página, qué columnas son ordenables, qué tipos de archivo aceptar, cuánto dura el remember me — está **en un único sitio**. Es un anticipo de la idea de configuración separada del código: las funciones del proyecto leen de aquí en lugar de tener valores "mágicos" dispersos en su interior.

Dicho esto, hay un límite que conviene reconocer enseguida, porque es exactamente lo que el proyecto enterprise corregirá: aquí la password de la base de datos está **escrita en claro dentro del código**. Para un proyecto didáctico que corre en local está bien, pero en producción las credenciales no deben estar nunca en un archivo versionado en Git — acabarían en el historial del repositorio, visibles para cualquiera que acceda a él. En el blog enterprise de la Parte IX daremos el paso siguiente: mover los valores sensibles fuera del código y leerlos del **entorno** (las variables de entorno, el archivo `.env`). Por ahora tenlo presente como un "por corregir" anotado al margen.

## Conexión con `mysqli`

La conexión se encapsula en una función, no se reescribe en cada archivo:

```php
<?php

declare(strict_types=1);
function getConnection(): mysqli
{
    $config = require 'config.php';

    $mysqli = new mysqli(
        $config['mysql_host'],
        $config['mysql_user'],
        $config['mysql_password'],
        $config['mysql_db']
    );

    if ($mysqli->connect_error) {
        die($mysqli->connect_error);
    }
    return $mysqli;
}
```

Código completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-19/es/parte-06/cap-19/listing-03.php)

Fuente real: [`connection.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/connection.php).

Una única función para establecer la conexión, invocada allí donde haga falta. Parece trivial, pero es una aplicación del principio **DRY**: la lógica de conexión — leer la config, crear el objeto `mysqli`, gestionar el error — existe en un único sitio. El día que cambies de base de datos, o añadas un parámetro de charset, o quieras gestionar el error de otra forma, lo corriges aquí y el resto de la aplicación se beneficia. Si cada archivo abriera su propia conexión a mano, ese mismo cambio habría que repetirlo en decenas de sitios. Encapsular también hace **explícita la frontera** con MySQL: hay un único punto en el que la aplicación toca el driver de la base de datos, y es más fácil de encontrar, entender y — más adelante — sustituir. En la Parte IX este mismo concepto se convertirá en una factory PDO registrada en el container, pero la idea de fondo — un único sitio responsable de la conexión — ya está aquí.

## Tabla de usuarios

La tabla `users` contiene datos personales, avatar, hash de password y rol:

```sql
create table users
(
    id         bigint unsigned auto_increment
        primary key,
    username   varchar(64)                                                not null,
    email      varchar(64)                                                not null,
    fiscalcode char(16)                                                   not null,
    age        smallint unsigned                                          not null,
    avatar     varchar(255)                                               not null,
    password   varchar(255)                                               not null,
    role_type  enum ('user', 'editor', 'admin') default 'user'            not null,
    created_at datetime                         default CURRENT_TIMESTAMP not null on update CURRENT_TIMESTAMP,
    updated_at datetime                         default CURRENT_TIMESTAMP null,
    deleted_at datetime                                                   null,
    constraint u_fiscalcode
        unique (fiscalcode)
)
    collate = utf8mb3_unicode_ci;
```

Código completo: [listing-04.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-19/es/parte-06/cap-19/listing-04.sql)

Fuente real: [`data/users.sql` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/data/users.sql).

El esquema de la tabla no es un detalle técnico que sobrevolar: es donde se decide buena parte de la seguridad y la corrección de la aplicación, antes incluso de escribir una línea de PHP. Fíjate en algunas decisiones. La columna `password` mide **255 caracteres**, no 32: porque no contendrá una password, sino el hash producido por `password_hash()` (Capítulo 22), que incluye algoritmo, coste y salt. El `role_type` es un `enum` con tres valores fijos: la propia base de datos rechaza un rol que no sea `user`, `editor` o `admin` — una restricción de integridad que ningún error de PHP puede saltarse. La restricción `unique` sobre `fiscalcode` es la defensa real contra los duplicados de los que hablábamos en el Capítulo 22: la garantía no está en una comprobación de la aplicación, está aquí. Y las tres columnas temporales `created_at`, `updated_at`, `deleted_at` cuentan una intención: `deleted_at` en particular sugiere el **soft delete**, eliminar marcando una fecha en lugar de quitar físicamente la fila, así un usuario eliminado por error es recuperable. El proyecto todavía gestiona el SQL a mano, y esto es valioso precisamente porque te obliga a ver exactamente qué columnas necesita cada funcionalidad.

## Entry point

`index.php` arranca sesión, conexión, funciones comunes, ACL y autenticación. Luego intenta el auto-login y protege la página principal:

```php
<?php

require_once 'includes/session.php';
require_once 'connection.php';
require_once 'functions.php';
require_once 'includes/acl.php';
require_once 'includes/auth.php';
tryAutoLogin();
if (!is_user_logged_in()) {
    redirect('login.php');
}
require_once 'includes/csrf.php';
```

Código completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-19/es/parte-06/cap-19/listing-05.php)

Fuente real: [`index.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/index.php).

El `index.php` es el **front controller** antes de que existiera el nombre: el punto único por el que pasan las peticiones a la página principal. El flujo se lee de arriba abajo como una lista de prioridades: primero se cargan las dependencias (sesión, conexión, funciones, ACL, auth), luego se establece **si** el usuario puede estar aquí (auto-login, comprobación de la sesión, posible redirect), y solo después se pasa a construir la interfaz. Es el mismo orden — dependencias, autorización, rendering — que encontrarás en cualquier framework, solo que escrito a mano. Esa cadena de `require_once` al principio es exactamente lo que el autoload de Composer, en la Parte VIII, hará desaparecer: aquí la ves desnuda, y entenderla ahora convierte el autoload en una comodidad en lugar de una magia.

## Controller y view

El controller de la lista prepara parámetros, recuento y registros:

```php
<?php

declare(strict_types=1);
$orderBy = $orderBy ?? 'ASC';
$recordsPerPage = $recordsPerPage ?? 10;
$search = $search ?? '';
$currentPage = $currentPage ?? 1;
$currentOrderDir = $currentOrderDir ?? 'DESC';
$params = [
    'orderBy' => $orderBy,
    'recordsPerPage' => $recordsPerPage,
    'orderDir' => $currentOrderDir,
    'search' => $search,
    'page' => $currentPage
];
$totalRecords = getTotalUserCount($search);

$users = $totalRecords ? getUsers($params) : [];

require 'view/userList.php';
```

Código completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-19/es/parte-06/cap-19/listing-06.php)

Fuente real: [`controller/displayUsers.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/controller/displayUsers.php).

Aquí se vislumbra, en forma embrionaria, la separación **controller/view** que será el corazón de la Parte IX. El controller no imprime nada: recoge los parámetros, llama a las funciones que hablan con la base de datos (`getTotalUserCount`, `getUsers`) y prepara las variables que necesitará la presentación. Solo al final `require 'view/userList.php'` pasa el testigo al archivo que se ocupa del HTML. Fíjate en la pequeña optimización `$totalRecords ? getUsers($params) : []`: si no hay ni un registro, se evita la segunda query — no tiene sentido pedir las filas de una página que estará vacía.

La view se ocupa del HTML:

```php
<table class="table table-dark table-striped">
    <caption>USERS LIST</caption>
    <thead>
    <tr>
        <th colspan="8" class="text-center text-bg-dark">
            <?= $totalRecords ?> RECORDS FOUND.
            PAGE <?= $currentPage ?> of <?= $totalPages ?>
        </th>
    </tr>
```

Código completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-19/es/parte-06/cap-19/listing-07.php)

Fuente real: [`view/userList.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/view/userList.php).

La view es casi solo HTML, con algún `<?= ?>` que inserta los datos preparados por el controller. Sigue siendo PHP tradicional — ningún motor de templates, ninguna clase — pero la frontera ya es visible y tiene un valor concreto: quien trabaja en el diseño toca la view sin arriesgarse a romper la lógica, y quien trabaja en los datos toca el controller sin perderse en el HTML. Esta división de responsabilidades, lograda aquí con la simple disciplina de mantener los archivos separados, en la Parte IX se convertirá en una regla impuesta por la arquitectura. Verla nacer por convención, antes que por obligación, te hace entender *por qué* la separación conviene.

## En resumen

El User Management System arranca con herramientas directas — `config.php`, `connection.php`, funciones comunes, controllers procedurales y templates PHP — y esta base simple no es un recurso de último momento, es una elección didáctica. Cada pieza que ves aquí es la versión "a mano" de algo que un framework luego automatiza: la configuración centralizada anticipa las variables de entorno, la función de conexión anticipa la factory en el container, la cadena de `require_once` anticipa el autoload, la separación controller/view anticipa el MVC de verdad. Construir primero esta versión deja claro, cuando lleguemos a la Parte IX, qué exactamente vienen a **mejorar** las clases, los repositories, los servicios y los middleware — y por qué. Un framework entendido es mucho más útil que un framework sufrido.
