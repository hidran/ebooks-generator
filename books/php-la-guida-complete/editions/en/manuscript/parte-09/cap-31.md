# 31. Freeblog MVC Step by Step

In this part, the project does not start directly from `phpenterpriseblog`. First we build `freeblog`, a small hand-written MVC blog. This chapter follows the natural project flow: pattern, database, folders, layout, controller, helpers, PDO, model, router, post CRUD, and comments. Only after that does the enterprise refactoring make sense.

The goal is not to present `freeblog` as final architecture. The goal is to see the problem appear. When the code works but starts depending on manual includes, superglobals, full controllers, and SQL inside models, it becomes clear why the next chapter moves to Composer, PSR-4, request objects, repositories, services, tests, and quality gates.

## Step 1: Understand MVC

MVC separates three responsibilities:

- the model handles data and storage-related rules;
- the view generates the representation, HTML in this case;
- the controller receives the request, coordinates model and view, and decides the response.

In the blog this means: a request reaches `/posts/12`, the router understands that we want post 12, the controller asks the `Post` model for data, then passes those data to a PHP view.

This separation is the first step toward maintainable code. It is not enterprise PHP yet, but it prevents SQL queries, HTML, redirects, and application rules from living in the same file.

## Step 2: Create Database and Tables

The first blog version starts with two tables: `posts` and `postscomments`. In the first version, whoever writes a post or comment leaves an email; later versions of the local source also introduce login, users, and `user_id`.

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

Full source: [listing-01.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/en/parte-09/cap-31/listing-01.sql)

The relationship matters: a comment does not live alone, it belongs to a post. `ON DELETE CASCADE` tells the database that, if a post is deleted, its comments must not remain orphaned.

## Step 3: Organize Folders

The initial structure separates public files from application code:

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

Full source: [listing-02.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/en/parte-09/cap-31/listing-02.txt)

`public/` is the directory the web server should expose. Everything else contains PHP code, configuration, and templates. This rule remains true in the enterprise project: the browser must not be able to download configuration files, classes, or internal templates.

## Step 4: URL Rewriting and Front Controller

The blog uses a front controller: every request enters through `public/index.php`. With Apache you can use this `.htaccess`:

```apache
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^ index.php [QSA,L]
```

Full source: [listing-03.apache](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/en/parte-09/cap-31/listing-03.apache)

This enables URLs such as `/posts`, `/posts/12`, and `/posts/12/edit`. You are no longer opening a PHP file directly for each page; you are asking one application to interpret the request.

Locally you can get there with Apache, XAMPP, Laragon, Valet, or PHP's built-in server. The operational detail changes, but the idea does not: the document root must point to `public/`.

## Step 5: Create the Layout

The layout contains the shared frame: HTML, navbar, CSS, JavaScript, and footer. The dynamic part lives in a controller variable:

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

Full source: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/en/parte-09/cap-31/listing-04.php)

The layout must not know whether it is showing a list, a detail page, a form, or comments. It only receives already-rendered content. This is the first boundary between the main view and specific views.

## Step 6: BaseController and PostController

`BaseController` handles the layout and common content:

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

Full source: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/en/parte-09/cap-31/listing-05.php)

The properties are `protected` because child controllers must be able to use them, while outside code should not. `$content` holds the HTML for the specific page, `$tplDir` points to the view directory, and `$layout` points to the main template. `display()` does not calculate data: it includes the final layout. When the layout reads `$this->content`, it gets the content prepared by the concrete controller.

The post controller extends that base:

```php
<?php

namespace App\Controllers;

final class PostController extends BaseController
{
    public function getPosts(): void
    {
        $this->content = 'Post list';
    }

    public function show(int $postId): void
    {
        $this->content = 'Post detail: ' . $postId;
    }
}
```

Full source: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/en/parte-09/cap-31/listing-06.php)

At the beginning, content can be a string. `getPosts()` represents the list action: for now it writes directly to `$this->content`, so the layout can display it. `show()` represents the detail action: it receives `$postId` from the router, treats it as the post identifier, and builds temporary content. The methods return `void` because the response is not returned as an object: it is accumulated in the controller and printed later by `display()`. Immediately after, we replace those strings with real templates and database data.

## Step 7: Render Views with a Helper

When multiple methods need to load templates, extracting a function helps:

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

Full source: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/en/parte-09/cap-31/listing-07.php)

The `view()` function receives the view name without extension, a data array, and the template directory. `extract()` turns array keys into local variables: `['posts' => $posts]` becomes `$posts` inside the template. `ob_start()` opens an output buffer, `require` executes the template, and `ob_get_clean()` returns the generated HTML as a string. This lets the controller assign the result to `$this->content` instead of printing immediately. It is convenient in a small project; in the enterprise project we will use more controlled views and better-prepared data.

## Step 8: Configure PDO

The connection should not be written in every controller. The first configuration lives in `config/database.php`:

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

Full source: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/en/parte-09/cap-31/listing-08.php)

PDO is the first step toward more portable database access. The project no longer depends on `mysqli`-specific functions; it uses an object that can prepare queries, execute statements, and return records in a consistent format.

## Step 9: DbPdo and a Teaching Singleton

Here we introduce a Singleton to avoid creating multiple connections during one request:

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

Full source: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/en/parte-09/cap-31/listing-09.php)

The `__construct()` method is `private`, so no outside code can call `new DbPdo()`. It receives already-normalized options and creates the real `PDO` object. `getInstance()` is the public access point: if the instance already exists it reuses it, otherwise it creates it once. `getConn()` exposes the PDO connection to the models. This helps explain the problem, but in the enterprise project we will not use global Singletons. A shared connection will be registered in the container and injected where needed. The operational result is similar; the architectural control is better.

## Step 10: DbFactory

The factory builds the DSN from configuration:

```php
<?php

namespace App\Db;

use InvalidArgumentException;

final class DbFactory
{
    public static function create(array $options): DbPdo
    {
        if (!isset($options['driver'])) {
            throw new InvalidArgumentException('No database driver configured');
        }

        $charset = $options['charset'] ?? 'utf8';
        $dsn = match ($options['driver']) {
            'mysql' => "mysql:host={$options['host']};dbname={$options['database']};charset={$charset}",
            'sqlite' => 'sqlite:' . $options['database'],
            default => throw new InvalidArgumentException('Unsupported database driver'),
        };

        $options['dsn'] = $options['dsn'] ?? $dsn;

        return DbPdo::getInstance($options);
    }
}
```

Full source: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/en/parte-09/cap-31/listing-10.php)

`create()` receives raw configuration, checks that `driver` exists, and chooses how to build the DSN. The `match` expression makes the supported drivers explicit: MySQL needs host, database, and charset; SQLite needs the database path. If the driver is missing or unsupported, the error is immediate. Finally the factory writes `dsn` into the options and delegates to `DbPdo::getInstance()`. Here an enterprise theme already appears: the controller should not know how to build a DSN string. It asks for a connection and nothing more.

## Step 11: Create the Post Model

The first model reads posts from the database:

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

Full source: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/en/parte-09/cap-31/listing-11.php)

The model constructor receives a `PDO` and stores it in a `readonly` property: after construction it cannot be replaced. `all()` runs a query without parameters because it must read every post; it sorts by `datecreated DESC`, so the newest post comes first. If `query()` returns a statement, `fetchAll()` converts rows into objects according to the configured fetch mode; if no valid statement is produced, the method returns an empty array. At this stage the model is also a repository: it contains SQL and returns data. That is acceptable for learning. Later we will separate the `Post` DTO from `PostRepository`.

## Step 12: Dependency Injection in the Controller

The controller receives the connection from the outside and builds the model:

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

Full source: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/en/parte-09/cap-31/listing-12.php)

The controller constructor receives `PDO` and creates the `Post` model. This is not full dependency injection yet, because the controller still builds the concrete model, but the connection is no longer created inside the action methods. `getPosts()` calls `$this->post->all()`, stores the result in `$posts`, and uses `compact('posts')` to pass an array with the `posts` key to the view. The value returned by `view()` goes into `$this->content`, ready for the layout. This is dependency injection in its simplest form. In the enterprise project we go further: the container will build controllers, repositories, and services.

## Step 13: Real Front Controller

`public/index.php` becomes the point where bootstrap, config, router, controller, and layout meet:

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

Full source: [listing-13.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/en/parte-09/cap-31/listing-13.php)

This file is still very active: it creates the connection, router, and controller. `chdir(dirname(__DIR__))` moves execution to the project root, so relative includes behave predictably. The bootstrap loads classes and helpers, configuration files return arrays, the router produces class, method, and parameters, the factory produces the connection, and the controller is invoked with the spread operator `...$params`. At the end, `display()` prints the layout only if the object really is a `BaseController`. The flow is now clear and centralized.

## Step 14: Configure Routes

The route map says which controller answers each HTTP method and path:

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

Full source: [listing-14.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/en/parte-09/cap-31/listing-14.php)

This step is central: HTTP behavior is no longer scattered across random `if` statements. It is a readable table. Each entry contains two pieces of information: the controller class and the method to call. Routes with `:id` declare a dynamic parameter; the router will extract it and pass it to the method as an argument.

## Step 15: Write the Router

The router reads method and URI, then looks for a route:

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
            ?: throw new Exception('No route matched');
    }
}
```

Full source: [listing-15.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/en/parte-09/cap-31/listing-15.php)

The router constructor receives the route table and stores it. `dispatch()` reads `REQUEST_URI`, isolates only the path with `parse_url()`, trims outer slashes, and uses `/` as the home-page default. Then it reads `REQUEST_METHOD` and keeps only the routes for that HTTP method. If it finds an exact match, it returns `[controller, method, parameters]` with an empty parameter list. If it does not, it tries dynamic routes through `matchRoute()`. At this point the router still depends on `$_SERVER`. In the enterprise project we change this: the router will receive testable request objects.

## Step 16: Routes with Parameters

To handle URLs such as `/posts/12`, the router turns `posts/:id` into a regular expression:

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

Full source: [listing-16.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/en/parte-09/cap-31/listing-16.php)

`matchRoute()` iterates only over the routes for the already-selected HTTP method. If a route does not contain `:`, it skips it because it has no parameters. `preg_quote()` protects special characters in the route, then `preg_replace()` replaces the `:id` placeholder with a capture group. When `preg_match()` finds a match, `array_shift()` removes the full match and leaves only the extracted parameters. The method returns the same shape as `dispatch()`: controller class, method, and parameters. This is when MVC becomes real: the URL is not just a string, it is application input.

## Step 17: Post List and Detail

The list view creates links to detail pages:

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

Full source: [listing-17.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/en/parte-09/cap-31/listing-17.php)

The view works with the objects returned by `Post::all()`. The `foreach` creates one article per post, the link points to `/posts/{id}`, and that feeds the detail route. `htmlentities()` prevents the title, email, or message from being interpreted as HTML; `nl2br()` preserves line breaks in the message. Even in a simple example, output escaping is not optional.

The detail page uses a `findByPostId()` method:

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

Full source: [listing-18.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/en/parte-09/cap-31/listing-18.php)

`findByPostId()` receives the identifier extracted from the URL. It does not concatenate that value into SQL: it prepares a query with `:id`, executes the statement with the parameter, and returns one row with `fetch()`. The `object|false` type tells the truth: if the post exists we get an object, and if it does not we get `false`. Here we see the first prepared statement with a parameter. This is the right way to read data filtered by the URL.

## Step 18: Create a New Post

The `GET /posts/create` route shows the form:

```php
<form action="/posts" method="POST">
    <div class="mb-3">
        <label for="email" class="form-label">Email address</label>
        <input required type="email" name="email" class="form-control" id="email">
    </div>
    <div class="mb-3">
        <label for="title" class="form-label">Title</label>
        <input required type="text" name="title" class="form-control" id="title">
    </div>
    <div class="mb-3">
        <label for="message" class="form-label">Message</label>
        <textarea required name="message" class="form-control" id="message" rows="3"></textarea>
    </div>
    <button class="btn btn-success">SAVE</button>
</form>
```

Full source: [listing-19.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/en/parte-09/cap-31/listing-19.php)

`POST /posts` saves:

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

Full source: [listing-20.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/en/parte-09/cap-31/listing-20.php)

`save()` receives an array with form data. The SQL uses named placeholders, not concatenation. The statement is prepared, then `execute()` receives only the required values: title, email, and message. `NOW()` stays in the database because the creation date belongs to the moment of persistence. The method returns `rowCount()`, meaning how many rows were inserted. The rule is simple: the controller reads `$_POST`, the model saves with a prepared statement, then the controller redirects.

## Step 19: Edit, Update, and Delete

On the post detail page, we add explicit actions:

```php
<form action="/posts/<?= $post->id ?>/edit" method="GET">
    <button class="btn btn-success">EDIT</button>
</form>

<form action="/posts/<?= $post->id ?>/delete" method="POST">
    <button class="btn btn-danger">DELETE</button>
</form>
```

Full source: [listing-21.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/en/parte-09/cap-31/listing-21.php)

The update uses the controller's same `save()` method, but with an ID:

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

Full source: [listing-22.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/en/parte-09/cap-31/listing-22.php)

`update()` is similar to `save()`, but it also requires `$postId`. Editable values come from the `$post` array; the identifier comes from the route and goes into the `:id` placeholder. This avoids trusting a hidden form field to decide which row to update. The method again returns `rowCount()`, which is useful for knowing whether the operation touched a row.

Deletion remains a `POST`, not a `GET` link:

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

Full source: [listing-23.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/en/parte-09/cap-31/listing-23.php)

`delete()` prepares a DELETE with a single parameter. Here we use `bindValue()` with `PDO::PARAM_INT` to state explicitly that the id is an integer. After `execute()`, `rowCount()` indicates how many rows were deleted. This is already a good HTTP habit: read with `GET`, change state with `POST`.

## Step 20: Show and Save Comments

A comment is a separate model because it uses a separate table:

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

Full source: [listing-24.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/en/parte-09/cap-31/listing-24.php)

The `Comment` constructor follows the same pattern as `Post`: it receives `PDO` and does not create connections by itself. `all()` receives `$postId`, prepares a query filtered by `post_id`, orders comments from newest to oldest, and returns all rows. `save()` receives an array already assembled by the controller, prepares the INSERT, and executes it. This model shows the first practical relationship: to read or save comments, we must always know which post they belong to.

The controller loads post and comments together:

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

Full source: [listing-25.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/en/parte-09/cap-31/listing-25.php)

The `show()` method now performs two coordinated reads: first it retrieves the post, then it creates `Comment` with the same connection and loads the related comments. The view receives both variables with `compact('post', 'comments')`, so it can show the main content and discussion on the same page. `saveComment()` receives `$postId` from the route, builds the array for the model from `$_POST`, and redirects back to the post detail page. The redirect prevents form resubmission when the user refreshes the page. We add comments after post CRUD because they are the first case where one resource depends on another. The same reasoning returns in REST APIs, repositories, and relationships between entities.

## Step 21: What We Have Built

At this point `freeblog` has:

- a front controller;
- URLs rewritten to `public/index.php`;
- a Bootstrap layout;
- controllers and a base controller;
- a helper for rendering views;
- configured PDO;
- a factory for building the connection;
- `Post` and `Comment` models;
- GET and POST routes;
- URL parameters;
- list, detail, creation, editing, deletion, and comments.

It is a complete MVC project, but not yet an enterprise project. The limits are visible:

- autoloading is manual;
- sensitive configuration is in code;
- the router is tied to `$_SERVER`;
- controllers are tied to `$_POST`, helper functions, and concrete models;
- models mix data objects and SQL;
- there is no test suite;
- there is no static analysis;
- there is no reproducible environment.

These are not failures: they are why the enterprise refactoring makes sense.

## Moving to phpenterpriseblog

The public refactoring project is:

```bash
git clone https://github.com/hidran/phpenterpriseblog.git
cd phpenterpriseblog
git tag -l
```

Full source: [listing-26.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/en/parte-09/cap-31/listing-26.sh)

Public repository: [phpenterpriseblog](https://github.com/hidran/phpenterpriseblog).

In the next chapter we do not start from scratch. We take the flow built in `freeblog` and move it toward a more professional form: Composer, PSR-4, request and response objects, a tested router, DTOs, repositories, services, dependency injection, PSR-7/15, migrations, quality gates, tests, Docker, Redis, and CI/CD.

## In summary

In this chapter we built `freeblog` from scratch, one step at a time: from the front controller and URL rewriting through to the router with parameters, from controllers and views to the `Post` model with PDO, by way of `DbPdo`, the factory, and dependency injection into the controller's constructor. The result is not a framework yet, and that is the point: it is the bare minimum needed to understand *why* frameworks do what they do. Some of the choices in this chapter — the teaching Singleton, the generic exception for unmatched routes, the SQL living inside the model — are deliberately provisional: over the next chapters we replace them with a container, dedicated exceptions, and repositories. If the request → router → controller → model → view flow is clear to you, the rest of Part IX is refinement, not rewriting.
