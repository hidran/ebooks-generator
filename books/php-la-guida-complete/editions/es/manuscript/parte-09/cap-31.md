# 31. Freeblog MVC paso a paso

En esta parte el proyecto no empieza directamente con `phpenterpriseblog`. Primero construimos `freeblog`, un pequeño blog MVC escrito a mano. Este capítulo sigue el flujo natural del proyecto: patrón, base de datos, carpetas, layout, controller, helpers, PDO, model, router, CRUD de posts y comentarios. Sólo después tiene sentido el refactoring enterprise.

El objetivo no es presentar `freeblog` como arquitectura final. El objetivo es ver aparecer el problema. Cuando el código funciona pero empieza a depender de includes manuales, superglobales, controllers cargados y SQL dentro de los models, queda claro por qué el capítulo siguiente pasa a Composer, PSR-4, request objects, repositories, services, tests y quality gates.

## Paso 1: entender MVC

MVC separa tres responsabilidades:

- el model gestiona datos y reglas relacionadas con el storage;
- la view genera la representación, en este caso HTML;
- el controller recibe la request, coordina model y view, y decide la respuesta.

En el blog esto significa: una request llega a `/posts/12`, el router entiende que queremos el post 12, el controller pide los datos al model `Post` y luego pasa esos datos a una view PHP.

Esta separación es el primer paso hacia código mantenible. Todavía no es enterprise PHP, pero evita poner queries SQL, HTML, redirects y reglas de aplicación en el mismo archivo.

## Paso 2: crear base de datos y tablas

La primera versión del blog nace con dos tablas: `posts` y `postscomments`. En la primera versión, quien escribe un post o un comentario deja un email; en versiones posteriores del código local entran también login, usuarios y `user_id`.

```sql
CREATE TABLE posts (
    id int(10) NOT NULL AUTO_INCREMENT,
    title varchar(255) NOT NULL,
    message text NOT NULL,
    datecreated datetime NOT NULL,
    email varchar(128) NOT NULL,
    PRIMARY KEY (id),
    KEY idx_title (title)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE postscomments (
    id int(12) NOT NULL AUTO_INCREMENT,
    post_id int(10) NOT NULL,
    comment text NOT NULL,
    datecreated datetime NOT NULL,
    email varchar(128) NOT NULL,
    PRIMARY KEY (id),
    KEY idx_post_id (post_id),
    CONSTRAINT fk_post_id
        FOREIGN KEY (post_id) REFERENCES posts (id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
```

Código completo: [listing-01.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/es/parte-09/cap-31/listing-01.sql)

La relación importa: un comentario no vive solo, pertenece a un post. `ON DELETE CASCADE` le dice a la base de datos que, si eliminas un post, sus comentarios no deben quedar huérfanos.

## Paso 3: organizar las carpetas

La estructura inicial separa lo público del código de aplicación:

```text
freeblog/
  public/
    index.php
    css/
    js/
  app/
    controllers/
    models/
    views/
  core/
    bootstrap.php
    Router.php
  config/
    app.config.php
    database.php
  db/
    DbPdo.php
    DbFactory.php
  helpers/
    functions.php
  layout/
    index.tpl.php
```

Código completo: [listing-02.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/es/parte-09/cap-31/listing-02.txt)

`public/` es la carpeta que el web server debe exponer. Todo lo demás contiene código PHP, configuración y templates. Esta regla se mantiene también en el proyecto enterprise: el navegador no debe poder descargar archivos de configuración, clases o templates internos.

## Paso 4: URL rewriting y front controller

El blog usa un front controller: todas las requests entran por `public/index.php`. Con Apache puedes usar un `.htaccess` así:

```apache
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^ index.php [QSA,L]
```

Código completo: [listing-03.apache](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/es/parte-09/cap-31/listing-03.apache)

Esto permite URLs como `/posts`, `/posts/12` y `/posts/12/edit`. Ya no abres directamente un archivo PHP para cada página; le pides a una única aplicación que interprete la request.

En local puedes lograrlo con Apache, XAMPP, Laragon, Valet o con el servidor integrado de PHP. El detalle operativo cambia, pero la idea no cambia: el document root debe apuntar a `public/`.

## Paso 5: crear el layout

El layout contiene el marco común: HTML, navbar, CSS, JavaScript y footer. La parte dinámica vive en una variable del controller:

```php
<!doctype html>
<html lang="en" class="h-100">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Free blog</title>
    <link href="/css/bootstrap.css" rel="stylesheet">
    <link href="/css/style.css" rel="stylesheet">
</head>
<body class="d-flex flex-column h-100">
    <main class="flex-shrink-0 mx-3">
        <?= $this->content ?>
    </main>
</body>
</html>
```

Código completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/es/parte-09/cap-31/listing-04.php)

El layout no debe saber si está mostrando lista, detalle, formulario o comentarios. Sólo recibe contenido ya renderizado. Este es el primer límite entre la view principal y las views específicas.

## Paso 6: BaseController y PostController

`BaseController` gestiona el layout y el contenido común:

```php
<?php

namespace App\Controllers;

abstract class BaseController
{
    protected string $content = '';
    protected string $tplDir = 'app/views/';
    protected string $layout = 'layout/index.tpl.php';

    public function display(): void
    {
        require $this->layout;
    }
}
```

Código completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/es/parte-09/cap-31/listing-05.php)

Las propiedades son `protected` porque los controllers hijos deben poder usarlas, pero el código externo no. `$content` contiene el HTML de la página concreta, `$tplDir` indica dónde buscar las views y `$layout` indica el template principal. `display()` no calcula datos: incluye el layout final. Cuando el layout lee `$this->content`, obtiene el contenido preparado por el controller concreto.

El controller de posts extiende esa base:

```php
<?php

namespace App\Controllers;

final class PostController extends BaseController
{
    public function getPosts(): void
    {
        $this->content = 'Lista de posts';
    }

    public function show(int $postId): void
    {
        $this->content = 'Detalle del post: ' . $postId;
    }
}
```

Código completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/es/parte-09/cap-31/listing-06.php)

Al principio el contenido puede ser una string. `getPosts()` representa la acción de lista: por ahora escribe directamente en `$this->content`, así el layout puede mostrarlo. `show()` representa la acción de detalle: recibe `$postId` desde el router, lo trata como identificador del post y construye un contenido temporal. Los métodos devuelven `void` porque la respuesta no se devuelve como objeto: se acumula en el controller y luego la imprime `display()`. Inmediatamente después sustituimos esas strings por templates reales y datos de la base de datos.

## Paso 7: renderizar views con un helper

Cuando varios métodos necesitan cargar templates, conviene extraer una función:

```php
<?php

function view(string $view, array $data = [], string $viewDir = 'app/views/'): string
{
    extract($data, EXTR_OVERWRITE);

    ob_start();
    require $viewDir . $view . '.tpl.php';
    return (string) ob_get_clean();
}
```

Código completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/es/parte-09/cap-31/listing-07.php)

La función `view()` recibe el nombre de la view sin extensión, un array de datos y la carpeta de templates. `extract()` convierte las claves del array en variables locales: `['posts' => $posts]` se convierte en `$posts` dentro del template. `ob_start()` abre un buffer de salida, `require` ejecuta el template y `ob_get_clean()` devuelve el HTML generado como string. Así el controller puede asignar el resultado a `$this->content` en lugar de imprimirlo inmediatamente. Es cómodo en un proyecto pequeño; en el proyecto enterprise usaremos views más controladas y datos mejor preparados.

## Paso 8: configurar PDO

La conexión no debe escribirse en cada controller. La primera configuración vive en `config/database.php`:

```php
<?php

return [
    'driver' => 'mysql',
    'host' => '127.0.0.1',
    'database' => 'freeblog',
    'user' => 'root',
    'password' => '',
    'charset' => 'utf8',
    'options' => [
        [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION],
        [PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_OBJ],
    ],
];
```

Código completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/es/parte-09/cap-31/listing-08.php)

PDO es el primer paso hacia un acceso a base de datos más portable. El proyecto ya no depende de funciones específicas de `mysqli`; usa un objeto que puede preparar queries, ejecutar statements y devolver records en un formato coherente.

## Paso 9: DbPdo y Singleton didáctico

Aquí introducimos un Singleton para evitar crear varias conexiones durante la misma request:

```php
<?php

namespace App\Db;

use PDO;

final class DbPdo
{
    private static ?self $instance = null;
    private PDO $conn;

    private function __construct(array $options)
    {
        $this->conn = new PDO($options['dsn'], $options['user'], $options['password']);
    }

    public static function getInstance(array $options): self
    {
        return self::$instance ??= new self($options);
    }

    public function getConn(): PDO
    {
        return $this->conn;
    }
}
```

Código completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/es/parte-09/cap-31/listing-09.php)

El método `__construct()` es `private`, así que ningún código externo puede llamar a `new DbPdo()`. Recibe las opciones ya normalizadas y crea el objeto `PDO` real. `getInstance()` es el punto de acceso público: si la instancia ya existe la reutiliza, y si no existe la crea una sola vez. `getConn()` expone la conexión PDO a los models. Es útil para entender el problema, pero en el proyecto enterprise no usaremos Singletons globales. Una conexión compartida se registrará en el container y se inyectará donde haga falta. El resultado operativo es parecido; el control arquitectónico es mejor.

## Paso 10: DbFactory

La factory construye el DSN a partir de la configuración:

```php
<?php

namespace App\Db;

use InvalidArgumentException;

final class DbFactory
{
    public static function create(array $options): DbPdo
    {
        if (!isset($options['driver'])) {
            throw new InvalidArgumentException('Driver de base de datos no configurado');
        }

        $charset = $options['charset'] ?? 'utf8';
        $dsn = match ($options['driver']) {
            'mysql' => "mysql:host={$options['host']};dbname={$options['database']};charset={$charset}",
            'sqlite' => 'sqlite:' . $options['database'],
            default => throw new InvalidArgumentException('Driver de base de datos no soportado'),
        };

        $options['dsn'] = $options['dsn'] ?? $dsn;

        return DbPdo::getInstance($options);
    }
}
```

Código completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/es/parte-09/cap-31/listing-10.php)

`create()` recibe la configuración cruda, comprueba que exista `driver` y decide cómo construir el DSN. La expresión `match` deja explícitos los drivers soportados: MySQL necesita host, database y charset; SQLite necesita el path de la base de datos. Si falta el driver o no está soportado, el error es inmediato. Al final la factory escribe `dsn` en las opciones y delega en `DbPdo::getInstance()`. Aquí aparece ya un tema enterprise: el controller no debe saber cómo se construye una string DSN. Pide una conexión y nada más.

## Paso 11: crear el model Post

El primer model lee posts desde la base de datos:

```php
<?php

namespace App\Models;

use PDO;

final class Post
{
    public function __construct(private readonly PDO $conn)
    {
    }

    public function all(): array
    {
        $sql = 'SELECT * FROM posts ORDER BY datecreated DESC';
        $stmt = $this->conn->query($sql);

        return $stmt ? $stmt->fetchAll() : [];
    }
}
```

Código completo: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/es/parte-09/cap-31/listing-11.php)

El constructor del model recibe un `PDO` y lo guarda en una propiedad `readonly`: después de construir el objeto no puede sustituirse. `all()` ejecuta una query sin parámetros porque debe leer todos los posts; ordena por `datecreated DESC`, así el post más reciente aparece primero. Si `query()` devuelve un statement, `fetchAll()` convierte las filas en objetos según el fetch mode configurado; si no se produce un statement válido, el método devuelve un array vacío. En esta fase el model también es repository: contiene la SQL y devuelve datos. Es aceptable para aprender. Más adelante separaremos el DTO `Post` de `PostRepository`.

## Paso 12: dependency injection en el controller

El controller recibe la conexión desde fuera y construye el model:

```php
<?php

namespace App\Controllers;

use App\Models\Post;
use PDO;

final class PostController extends BaseController
{
    private Post $post;

    public function __construct(private readonly PDO $conn)
    {
        $this->post = new Post($conn);
    }

    public function getPosts(): void
    {
        $posts = $this->post->all();
        $this->content = view('posts', compact('posts'), $this->tplDir);
    }
}
```

Código completo: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/es/parte-09/cap-31/listing-12.php)

El constructor del controller recibe `PDO` y crea el model `Post`. Todavía no es dependency injection completa, porque el controller sigue construyendo el model concreto, pero la conexión ya no nace dentro de los métodos de acción. `getPosts()` llama a `$this->post->all()`, guarda el resultado en `$posts` y usa `compact('posts')` para pasar a la view un array con la clave `posts`. El valor devuelto por `view()` termina en `$this->content`, listo para el layout. Esta es dependency injection en su forma más simple. En el proyecto enterprise iremos más lejos: el container construirá controllers, repositories y services.

## Paso 13: front controller real

`public/index.php` se convierte en el punto donde se encuentran bootstrap, config, router, controller y layout:

```php
<?php

use App\Controllers\BaseController;
use App\Core\Router;
use App\Db\DbFactory;

chdir(dirname(__DIR__));

require_once 'core/bootstrap.php';

$database = require 'config/database.php';
$appConfig = require 'config/app.config.php';

$router = new Router($appConfig['routes']);
[$controllerClass, $method, $params] = $router->dispatch();

$conn = DbFactory::create($database)->getConn();
$controller = new $controllerClass($conn);
$controller->$method(...$params);

if ($controller instanceof BaseController) {
    $controller->display();
}
```

Código completo: [listing-13.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/es/parte-09/cap-31/listing-13.php)

Este archivo todavía está muy activo: crea conexión, router y controller. `chdir(dirname(__DIR__))` mueve la ejecución a la raíz del proyecto, así los includes relativos se comportan de forma previsible. El bootstrap carga clases y helpers, los archivos de configuración devuelven arrays, el router produce clase, método y parámetros, la factory produce la conexión y el controller se invoca con el spread operator `...$params`. Al final, `display()` imprime el layout sólo si el objeto es realmente un `BaseController`. El flujo ya es claro y único.

## Paso 14: configurar las rutas

El mapa de rutas dice qué controller responde a cada método HTTP y path:

```php
<?php

use App\Controllers\PostController;

return [
    'routes' => [
        'GET' => [
            '/' => [PostController::class, 'getPosts'],
            'posts' => [PostController::class, 'getPosts'],
            'posts/create' => [PostController::class, 'create'],
            'posts/:id' => [PostController::class, 'show'],
            'posts/:id/edit' => [PostController::class, 'edit'],
        ],
        'POST' => [
            'posts' => [PostController::class, 'save'],
            'posts/:id' => [PostController::class, 'save'],
            'posts/:id/delete' => [PostController::class, 'delete'],
            'posts/:id/comments' => [PostController::class, 'saveComment'],
        ],
    ],
];
```

Código completo: [listing-14.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/es/parte-09/cap-31/listing-14.php)

Este paso es central: el comportamiento HTTP ya no está repartido en `if` casuales. Es una tabla legible. Cada entrada contiene dos datos: la clase controller y el método a llamar. Las rutas con `:id` declaran un parámetro dinámico; el router lo extraerá y lo pasará al método como argumento.

## Paso 15: escribir el router

El router lee método y URI, luego busca una route:

```php
<?php

namespace App\Core;

use Exception;

final class Router
{
    public function __construct(private array $routes = ['GET' => [], 'POST' => []])
    {
    }

    public function dispatch(): array
    {
        $uri = $_SERVER['REQUEST_URI'] ?? '/';
        $segment = trim(parse_url($uri, PHP_URL_PATH), '/') ?: '/';
        $method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
        $routes = $this->routes[$method] ?? [];

        if (array_key_exists($segment, $routes)) {
            return [$routes[$segment][0], $routes[$segment][1], []];
        }

        return $this->matchRoute($routes, $segment)
            ?: throw new Exception('Ninguna ruta encontrada');
    }
}
```

Código completo: [listing-15.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/es/parte-09/cap-31/listing-15.php)

El constructor del router recibe la tabla de rutas y la guarda. `dispatch()` lee `REQUEST_URI`, aísla sólo el path con `parse_url()`, elimina los slashes externos y usa `/` como valor por defecto para la home. Luego lee `REQUEST_METHOD` y conserva sólo las rutas de ese método HTTP. Si encuentra una coincidencia exacta, devuelve `[controller, método, parámetros]` con una lista de parámetros vacía. Si no la encuentra, prueba las rutas dinámicas mediante `matchRoute()`. En este momento el router todavía depende de `$_SERVER`. En el proyecto enterprise cambiaremos este punto: el router recibirá request objects testeables.

## Paso 16: rutas con parámetros

Para gestionar URLs como `/posts/12`, el router transforma `posts/:id` en una regular expression:

```php
<?php

private function matchRoute(array $routes, string $segment): array
{
    foreach ($routes as $route => $handler) {
        if (!str_contains($route, ':')) {
            continue;
        }

        $quoted = preg_quote($route, '@');
        $pattern = preg_replace('/\\\\:[A-Za-z0-9_-]+/', '([A-Za-z0-9_-]+)', $quoted);

        if (preg_match('@^' . $pattern . '$@', $segment, $matches)) {
            array_shift($matches);
            return [$handler[0], $handler[1], $matches];
        }
    }

    return [];
}
```

Código completo: [listing-16.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/es/parte-09/cap-31/listing-16.php)

`matchRoute()` recorre sólo las rutas del método HTTP ya seleccionado. Si una ruta no contiene `:`, la salta porque no tiene parámetros. `preg_quote()` protege los caracteres especiales de la ruta y después `preg_replace()` sustituye el placeholder `:id` por un grupo capturable. Cuando `preg_match()` encuentra una coincidencia, `array_shift()` elimina el match completo y deja sólo los parámetros extraídos. El método devuelve la misma forma que `dispatch()`: clase controller, método y parámetros. Este es el momento en que MVC se vuelve real: la URL no es sólo una string, es input de la aplicación.

## Paso 17: lista y detalle de posts

La view de la lista crea links hacia el detalle:

```php
<?php foreach ($posts as $post): ?>
    <article>
        <h2>
            <a href="/posts/<?= $post->id ?>">
                <?= htmlentities($post->title) ?>
            </a>
        </h2>
        <p>
            <time datetime="<?= $post->datecreated ?>"><?= $post->datecreated ?></time>
            by <a href="mailto:<?= $post->email ?>"><?= htmlentities($post->email) ?></a>
        </p>
        <?= nl2br(htmlentities($post->message)) ?>
    </article>
<?php endforeach; ?>
```

Código completo: [listing-17.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/es/parte-09/cap-31/listing-17.php)

La view trabaja con los objetos devueltos por `Post::all()`. El `foreach` crea un artículo por cada post, el link apunta a `/posts/{id}` y eso alimenta la ruta de detalle. `htmlentities()` evita que título, email o mensaje se interpreten como HTML; `nl2br()` conserva los saltos de línea del mensaje. Incluso en un ejemplo simple, el escaping de salida no es opcional.

El detalle usa un método `findByPostId()`:

```php
<?php

public function findByPostId(int $postId): object|false
{
    $sql = 'SELECT * FROM posts WHERE id = :id';
    $stmt = $this->conn->prepare($sql);
    $stmt->execute(['id' => $postId]);

    return $stmt->fetch();
}
```

Código completo: [listing-18.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/es/parte-09/cap-31/listing-18.php)

`findByPostId()` recibe el identificador extraído desde la URL. No concatena ese valor en la SQL: prepara una query con `:id`, ejecuta el statement con el parámetro y devuelve una sola fila con `fetch()`. El tipo `object|false` dice la verdad: si el post existe obtenemos un objeto, y si no existe obtenemos `false`. Aquí aparece la primera prepared statement con parámetro. Es la forma correcta de leer datos filtrados desde la URL.

## Paso 18: crear un nuevo post

La route `GET /posts/create` muestra el form:

```php
<form action="/posts" method="POST">
    <div class="mb-3">
        <label for="email" class="form-label">Correo electrónico</label>
        <input required type="email" name="email" class="form-control" id="email">
    </div>
    <div class="mb-3">
        <label for="title" class="form-label">Título</label>
        <input required type="text" name="title" class="form-control" id="title">
    </div>
    <div class="mb-3">
        <label for="message" class="form-label">Mensaje</label>
        <textarea required name="message" class="form-control" id="message" rows="3"></textarea>
    </div>
    <button class="btn btn-success">GUARDAR</button>
</form>
```

Código completo: [listing-19.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/es/parte-09/cap-31/listing-19.php)

`POST /posts` guarda:

```php
<?php

public function save(array $post): int
{
    $sql = 'INSERT INTO posts (title, email, message, datecreated)
            VALUES (:title, :email, :message, NOW())';
    $stmt = $this->conn->prepare($sql);
    $stmt->execute([
        'title' => $post['title'],
        'email' => $post['email'],
        'message' => $post['message'],
    ]);

    return $stmt->rowCount();
}
```

Código completo: [listing-20.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/es/parte-09/cap-31/listing-20.php)

`save()` recibe un array con los datos del form. La SQL usa placeholders con nombre, no concatenación. El statement se prepara y después `execute()` recibe sólo los valores necesarios: title, email y message. `NOW()` se queda en la base de datos porque la fecha de creación pertenece al momento de persistencia. El método devuelve `rowCount()`, es decir, cuántas filas se insertaron. La regla es simple: el controller lee `$_POST`, el model guarda con prepared statement y luego el controller hace redirect.

## Paso 19: editar, actualizar y eliminar

En el detalle del post añadimos acciones explícitas:

```php
<form action="/posts/<?= $post->id ?>/edit" method="GET">
    <button class="btn btn-success">EDITAR</button>
</form>

<form action="/posts/<?= $post->id ?>/delete" method="POST">
    <button class="btn btn-danger">ELIMINAR</button>
</form>
```

Código completo: [listing-21.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/es/parte-09/cap-31/listing-21.php)

El update usa el mismo `save()` del controller, pero con un ID:

```php
<?php

public function update(array $post, int $postId): int
{
    $sql = 'UPDATE posts SET title = :title, email = :email, message = :message
            WHERE id = :id';
    $stmt = $this->conn->prepare($sql);
    $stmt->execute([
        'title' => $post['title'],
        'email' => $post['email'],
        'message' => $post['message'],
        'id' => $postId,
    ]);

    return $stmt->rowCount();
}
```

Código completo: [listing-22.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/es/parte-09/cap-31/listing-22.php)

`update()` es parecido a `save()`, pero también necesita `$postId`. Los valores editables llegan desde el array `$post`; el identificador llega desde la ruta y termina en el placeholder `:id`. Así evitamos confiar en un campo oculto para decidir qué fila actualizar. El método vuelve a devolver `rowCount()`, útil para saber si la operación tocó una fila.

La eliminación sigue siendo un `POST`, no un link `GET`:

```php
<?php

public function delete(int $postId): int
{
    $stmt = $this->conn->prepare('DELETE FROM posts WHERE id = :id');
    $stmt->bindValue('id', $postId, PDO::PARAM_INT);
    $stmt->execute();

    return $stmt->rowCount();
}
```

Código completo: [listing-23.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/es/parte-09/cap-31/listing-23.php)

`delete()` prepara una DELETE con un único parámetro. Aquí usamos `bindValue()` con `PDO::PARAM_INT` para declarar explícitamente que el id es un entero. Después de `execute()`, `rowCount()` indica cuántas filas se eliminaron. Esto ya es un buen hábito HTTP: leer con `GET`, cambiar estado con `POST`.

## Paso 20: mostrar y guardar comentarios

El comentario es un model separado porque usa una tabla separada:

```php
<?php

namespace App\Models;

use PDO;

final class Comment
{
    public function __construct(private readonly PDO $conn)
    {
    }

    public function all(int $postId): array
    {
        $sql = 'SELECT * FROM postscomments
                WHERE post_id = :post_id
                ORDER BY datecreated DESC';
        $stmt = $this->conn->prepare($sql);
        $stmt->execute(['post_id' => $postId]);

        return $stmt->fetchAll();
    }

    public function save(array $comment): int
    {
        $sql = 'INSERT INTO postscomments (post_id, email, comment, datecreated)
                VALUES (:post_id, :email, :comment, NOW())';
        $stmt = $this->conn->prepare($sql);
        $stmt->execute($comment);

        return $stmt->rowCount();
    }
}
```

Código completo: [listing-24.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/es/parte-09/cap-31/listing-24.php)

El constructor de `Comment` sigue el mismo esquema que `Post`: recibe `PDO` y no crea conexiones por su cuenta. `all()` recibe `$postId`, prepara una query filtrada por `post_id`, ordena los comentarios del más reciente al más antiguo y devuelve todas las filas. `save()` recibe un array ya compuesto por el controller, prepara el INSERT y lo ejecuta. Este model muestra la primera relación práctica: para leer o guardar comentarios siempre debemos saber a qué post pertenecen.

El controller carga post y comentarios juntos:

```php
<?php

public function show(int $postId): void
{
    $post = $this->post->findByPostId($postId);
    $commentModel = new Comment($this->conn);
    $comments = $commentModel->all($postId);

    $this->content = view('post', compact('post', 'comments'));
}

public function saveComment(int $postId): void
{
    $commentModel = new Comment($this->conn);
    $commentModel->save([
        'post_id' => $postId,
        'email' => $_POST['email'] ?? '',
        'comment' => $_POST['comment'] ?? '',
    ]);

    redirect('/posts/' . $postId);
}
```

Código completo: [listing-25.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/es/parte-09/cap-31/listing-25.php)

El método `show()` ahora hace dos lecturas coordinadas: primero recupera el post, luego crea `Comment` con la misma conexión y carga los comentarios relacionados. La view recibe ambas variables con `compact('post', 'comments')`, así puede mostrar el contenido principal y la discusión en la misma página. `saveComment()` recibe `$postId` desde la ruta, construye el array para el model desde `$_POST` y redirige al detalle del post. El redirect evita reenviar el form si el usuario refresca la página. Añadimos los comentarios después del CRUD de posts porque son el primer caso en que un recurso depende de otro. Es el mismo razonamiento que volveremos a encontrar en REST APIs, repositories y relaciones entre entidades.

## Paso 21: qué hemos conseguido

En este punto `freeblog` tiene:

- front controller;
- URLs reescritas hacia `public/index.php`;
- layout Bootstrap;
- controllers y base controller;
- helper para renderizar views;
- PDO configurado;
- factory para construir la conexión;
- models `Post` y `Comment`;
- rutas GET y POST;
- parámetros en la URL;
- lista, detalle, creación, edición, eliminación y comentarios.

Es un proyecto MVC completo, pero todavía no es un proyecto enterprise. Los límites son visibles:

- autoload manual;
- configuración sensible en el código;
- router ligado a `$_SERVER`;
- controllers ligados a `$_POST`, funciones helper y models concretos;
- models que mezclan objetos de datos y SQL;
- ninguna suite de tests;
- ningún análisis estático;
- ningún entorno reproducible.

No son fallos: son la razón por la que el refactoring enterprise tiene sentido.

## Paso a phpenterpriseblog

El proyecto público del refactoring es:

```bash
git clone https://github.com/hidran/phpenterpriseblog.git
cd phpenterpriseblog
git tag -l
```

Código completo: [listing-26.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/es/parte-09/cap-31/listing-26.sh)

Repositorio público: [phpenterpriseblog](https://github.com/hidran/phpenterpriseblog).

En el capítulo siguiente no empezamos desde cero. Tomamos el flujo construido en `freeblog` y lo llevamos hacia una forma más profesional: Composer, PSR-4, request y response objects, router testeado, DTO, repositories, services, dependency injection, PSR-7/15, migraciones, quality gates, tests, Docker, Redis y CI/CD.

## En resumen

En este capítulo hemos construido `freeblog` desde cero, paso a paso: del front controller y el URL rewriting hasta el router con parámetros, de los controllers y las views al model `Post` con PDO, pasando por `DbPdo`, la factory y la dependency injection en el constructor del controller. El resultado todavía no es un framework, y está bien así: es el mínimo imprescindible para entender *por qué* los frameworks hacen lo que hacen. Algunas decisiones de este capítulo — el Singleton didáctico, la excepción genérica para las rutas no encontradas, el SQL dentro del model — son deliberadamente provisionales: en los próximos capítulos las sustituiremos por un container, excepciones dedicadas y repositories. Si tienes claro el flujo request → router → controller → model → view, el resto de la Parte IX será trabajo de refinamiento, no de reescritura.
