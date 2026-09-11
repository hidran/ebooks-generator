# 31. Freeblog MVC step by step

In questa parte il progetto non parte direttamente da `phpenterpriseblog`. Prima costruiamo `freeblog`, un piccolo blog MVC scritto a mano. Questo capitolo segue il flusso naturale del progetto: pattern, database, cartelle, layout, controller, helper, PDO, model, router, CRUD dei post e commenti. Solo dopo ha senso parlare del refactoring enterprise.

Il punto non è presentare `freeblog` come architettura finale. Il punto è vedere nascere il problema. Quando il codice funziona ma comincia a dipendere da include manuali, superglobali, controller pieni e SQL dentro i model, diventa chiaro perché nel capitolo successivo passeremo a Composer, PSR-4, request object, repository, servizi, test e quality gate.

## Passo 1: capire MVC

MVC separa tre responsabilità:

- il model gestisce dati e regole legate allo storage;
- la view genera la rappresentazione, in questo caso HTML;
- il controller riceve la richiesta, coordina model e view, e decide la risposta.

Nel blog questo significa: una richiesta arriva a `/posts/12`, il router capisce che vogliamo il post 12, il controller chiede i dati al model `Post`, poi passa quei dati a una view PHP.

Questa separazione è il primo passo verso codice manutenibile. Non è ancora enterprise PHP, ma impedisce di mettere query SQL, HTML, redirect e regole applicative nello stesso file.

## Passo 2: creare database e tabelle

La prima versione del blog nasce con due tabelle: `posts` e `postscomments`. Nella prima versione chi scrive un post o un commento lascia una email; nelle versioni successive del sorgente locale entrano anche login, utenti e `user_id`.

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

Codice completo: [listing-01.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/it/parte-09/cap-31/listing-01.sql)

La relazione è importante: un commento non vive da solo, appartiene a un post. `ON DELETE CASCADE` dice al database che, se elimini un post, i commenti collegati non devono restare orfani.

## Passo 3: organizzare le cartelle

La struttura iniziale separa ciò che è pubblico dal codice applicativo:

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

Codice completo: [listing-02.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/it/parte-09/cap-31/listing-02.txt)

`public/` è la cartella che il web server deve esporre. Il resto contiene codice PHP, configurazione e template. Questa regola resterà anche nel progetto enterprise: il browser non deve poter scaricare file di configurazione, classi o template interni.

## Passo 4: URL rewriting e front controller

Il blog usa un front controller: tutte le richieste entrano da `public/index.php`. Con Apache puoi usare un `.htaccess` così:

```apache
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^ index.php [QSA,L]
```

Codice completo: [listing-03.apache](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/it/parte-09/cap-31/listing-03.apache)

Questo permette URL come `/posts`, `/posts/12` e `/posts/12/edit`. Non stai più aprendo direttamente un file PHP per ogni pagina; stai chiedendo a un'unica applicazione di interpretare la richiesta.

In locale puoi arrivarci con Apache, XAMPP, Laragon, Valet o con il server integrato di PHP. Il dettaglio operativo cambia, ma l'idea non cambia: il document root deve puntare a `public/`.

## Passo 5: creare il layout

Il layout contiene la cornice comune: HTML, navbar, CSS, JavaScript e footer. La parte dinamica sta in una variabile del controller:

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

Codice completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/it/parte-09/cap-31/listing-04.php)

Il layout non deve sapere se sta mostrando lista, dettaglio, form o commenti. Riceve solo contenuto già renderizzato. Questo è il primo confine tra view principale e view specifiche.

## Passo 6: BaseController e PostController

Il `BaseController` gestisce il layout e il contenuto comune:

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

Codice completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/it/parte-09/cap-31/listing-05.php)

Le proprietà sono `protected` perché devono essere visibili ai controller figli, ma non al codice esterno. `$content` contiene l'HTML della pagina specifica, `$tplDir` indica dove cercare le view e `$layout` indica il template principale. Il metodo `display()` non calcola dati: include il layout finale. Quando il layout usa `$this->content`, legge il contenuto preparato dal controller concreto.

Il controller dei post estende questa base:

```php
<?php

namespace App\Controllers;

final class PostController extends BaseController
{
    public function getPosts(): void
    {
        $this->content = 'Elenco post';
    }

    public function show(int $postId): void
    {
        $this->content = 'Dettaglio post: ' . $postId;
    }
}
```

Codice completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/it/parte-09/cap-31/listing-06.php)

All'inizio il contenuto può essere una stringa. `getPosts()` rappresenta l'azione della lista: per ora scrive direttamente in `$this->content`, quindi il layout può mostrarla. `show()` rappresenta l'azione di dettaglio: riceve `$postId` dal router, lo tratta come identificatore del post e costruisce un contenuto provvisorio. I metodi ritornano `void` perché la risposta non viene restituita come oggetto: viene accumulata nel controller e poi stampata da `display()`. Subito dopo sostituiremo queste stringhe con template reali e dati dal database.

## Passo 7: renderizzare le view con un helper

Quando più metodi devono caricare template, conviene estrarre una funzione:

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

Codice completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/it/parte-09/cap-31/listing-07.php)

La funzione `view()` riceve il nome della view senza estensione, un array di dati e la directory dei template. `extract()` trasforma le chiavi dell'array in variabili locali: `['posts' => $posts]` diventa `$posts` dentro il template. `ob_start()` apre un buffer di output, `require` esegue il template e `ob_get_clean()` restituisce l'HTML generato come stringa. In questo modo il controller può assegnare il risultato a `$this->content` invece di stampare subito. È comodo in un progetto piccolo; nel progetto enterprise useremo view più controllate e dati preparati con più disciplina.

## Passo 8: configurare PDO

La connessione non deve essere scritta in ogni controller. La prima configurazione sta in `config/database.php`:

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

Codice completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/it/parte-09/cap-31/listing-08.php)

PDO è il primo passo verso un accesso al database più portabile. Il progetto non dipende più da funzioni specifiche di `mysqli`; usa un oggetto che può preparare query, eseguire statement e restituire record in formato coerente.

## Passo 9: DbPdo e Singleton didattico

Qui introduciamo un Singleton per evitare di creare più connessioni durante la stessa richiesta:

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

Codice completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/it/parte-09/cap-31/listing-09.php)

Il costruttore `__construct()` è `private`, quindi nessuno può fare `new DbPdo()` dall'esterno. Riceve le opzioni già normalizzate e crea il vero oggetto `PDO`. `getInstance()` è il punto di accesso pubblico: se l'istanza esiste la riusa, altrimenti la crea una volta sola. `getConn()` espone la connessione PDO ai model. È utile per capire il problema, ma nel progetto enterprise non useremo Singleton globali. Una connessione condivisa verrà registrata nel container e iniettata dove serve. Il risultato operativo è simile; il controllo architetturale è migliore.

## Passo 10: DbFactory

La factory costruisce il DSN a partire dalla configurazione:

```php
<?php

namespace App\Db;

use InvalidArgumentException;

final class DbFactory
{
    public static function create(array $options): DbPdo
    {
        if (!isset($options['driver'])) {
            throw new InvalidArgumentException('Driver database non configurato');
        }

        $charset = $options['charset'] ?? 'utf8';
        $dsn = match ($options['driver']) {
            'mysql' => "mysql:host={$options['host']};dbname={$options['database']};charset={$charset}",
            'sqlite' => 'sqlite:' . $options['database'],
            default => throw new InvalidArgumentException('Driver database non supportato'),
        };

        $options['dsn'] = $options['dsn'] ?? $dsn;

        return DbPdo::getInstance($options);
    }
}
```

Codice completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/it/parte-09/cap-31/listing-10.php)

`create()` riceve la configurazione grezza, controlla che esista `driver` e sceglie come costruire il DSN. Il `match` rende espliciti i driver supportati: MySQL richiede host, database e charset; SQLite richiede il path del database. Se il driver manca o non è supportato, l'errore è immediato. Alla fine la factory inserisce `dsn` nelle opzioni e delega a `DbPdo::getInstance()`. Qui compare già un tema enterprise: il controller non deve sapere come si costruisce una stringa DSN. Chiede una connessione e basta.

## Passo 11: creare il model Post

Il primo model legge i post dal database:

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

Codice completo: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/it/parte-09/cap-31/listing-11.php)

Il costruttore del model riceve una `PDO` e la conserva in una proprietà `readonly`: dopo la costruzione non può essere sostituita. `all()` esegue una query senza parametri perché deve leggere tutti i post; ordina per `datecreated DESC`, quindi il post più recente arriva per primo. Se `query()` restituisce uno statement, `fetchAll()` converte le righe in oggetti secondo il fetch mode configurato; se qualcosa non produce uno statement valido, il metodo restituisce un array vuoto. In questa fase il model è anche repository: contiene la SQL e restituisce dati. È accettabile per imparare. Più avanti separeremo il DTO `Post` dal repository `PostRepository`.

## Passo 12: dependency injection nel controller

Il controller riceve la connessione dall'esterno e costruisce il model:

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

Codice completo: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/it/parte-09/cap-31/listing-12.php)

Il costruttore del controller riceve `PDO` e crea il model `Post`. Non è ancora dependency injection completa, perché il controller costruisce comunque il model concreto, ma la connessione non nasce più dentro i metodi. `getPosts()` chiama `$this->post->all()`, mette il risultato in `$posts` e usa `compact('posts')` per passare alla view un array con la chiave `posts`. Il valore ritornato da `view()` finisce in `$this->content`, pronto per il layout. Questa è dependency injection nella forma più semplice. Nel progetto enterprise andremo oltre: il container costruirà controller, repository e servizi.

## Passo 13: front controller reale

`public/index.php` diventa il punto in cui bootstrap, config, router, controller e layout si incontrano:

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

Codice completo: [listing-13.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/it/parte-09/cap-31/listing-13.php)

Questo file è ancora molto attivo: crea connessione, router e controller. `chdir(dirname(__DIR__))` porta l'esecuzione nella radice del progetto, così gli include relativi funzionano in modo prevedibile. Il bootstrap carica classi e helper, i file di configurazione restituiscono array, il router produce classe, metodo e parametri, la factory produce la connessione e il controller viene invocato con lo spread operator `...$params`. Alla fine `display()` stampa il layout solo se l'oggetto è davvero un `BaseController`. Il flusso è finalmente chiaro e unico.

## Passo 14: configurare le rotte

La mappa delle rotte dice quale controller risponde a ogni metodo HTTP e path:

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

Codice completo: [listing-14.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/it/parte-09/cap-31/listing-14.php)

Questo passo è centrale: il comportamento HTTP non è più sparso in `if` casuali. È una tabella leggibile. Ogni voce contiene due informazioni: la classe controller e il metodo da chiamare. Le rotte con `:id` dichiarano un parametro dinamico; il router lo estrarrà e lo passerà al metodo come argomento.

## Passo 15: scrivere il router

Il router legge metodo e URI, poi cerca una route:

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
            ?: throw new Exception('Nessuna rotta trovata');
    }
}
```

Codice completo: [listing-15.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/it/parte-09/cap-31/listing-15.php)

Il costruttore del router riceve la tabella delle rotte e la conserva. `dispatch()` legge `REQUEST_URI`, isola solo il path con `parse_url()`, rimuove gli slash esterni e usa `/` come default per la home. Poi legge `REQUEST_METHOD` e prende solo le rotte di quel metodo HTTP. Se trova una corrispondenza esatta, restituisce `[controller, metodo, parametri]` con parametri vuoti. Se non la trova, passa alle rotte dinamiche con `matchRoute()`. In questo momento il router dipende ancora da `$_SERVER`. Nel progetto enterprise cambieremo questo punto: il router riceverà request object testabili.

## Passo 16: route con parametri

Per gestire URL come `/posts/12`, il router trasforma `posts/:id` in una regular expression:

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

Codice completo: [listing-16.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/it/parte-09/cap-31/listing-16.php)

`matchRoute()` attraversa solo le rotte del metodo HTTP già selezionato. Se una rotta non contiene `:`, la ignora perché non ha parametri. `preg_quote()` protegge i caratteri speciali della rotta, poi `preg_replace()` sostituisce il segnaposto `:id` con un gruppo catturabile. Quando `preg_match()` trova una corrispondenza, `array_shift()` elimina il match completo e lascia solo i parametri estratti. Il metodo restituisce lo stesso formato di `dispatch()`: classe controller, metodo e parametri. Questo passaggio è il momento in cui MVC diventa reale: l'URL non è solo una stringa, è input applicativo.

## Passo 17: lista e dettaglio dei post

La view della lista crea link verso il dettaglio:

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

Codice completo: [listing-17.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/it/parte-09/cap-31/listing-17.php)

La view lavora con gli oggetti restituiti da `Post::all()`. Il `foreach` crea un articolo per ogni post, il link punta a `/posts/{id}` e quindi alimenta la rotta di dettaglio. `htmlentities()` evita che titolo, email o messaggio vengano interpretati come HTML; `nl2br()` conserva le interruzioni di riga del messaggio. Anche in un esempio semplice, l'escaping in output è una regola da non rimandare.

Il dettaglio usa un metodo `findByPostId()`:

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

Codice completo: [listing-18.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/it/parte-09/cap-31/listing-18.php)

`findByPostId()` riceve l'identificatore estratto dall'URL. Non concatena quel valore nella SQL: prepara una query con `:id`, esegue lo statement passando il parametro e ritorna una sola riga con `fetch()`. Il tipo `object|false` dice la verità: se il post esiste otteniamo un oggetto, se non esiste otteniamo `false`. Qui appare la prima prepared statement con parametro. Questo è il modo corretto per leggere dati filtrati dall'URL.

## Passo 18: creare un nuovo post

La route `GET /posts/create` mostra il form:

```php
<form action="/posts" method="POST">
    <div class="mb-3">
        <label for="email" class="form-label">Indirizzo email</label>
        <input required type="email" name="email" class="form-control" id="email">
    </div>
    <div class="mb-3">
        <label for="title" class="form-label">Titolo</label>
        <input required type="text" name="title" class="form-control" id="title">
    </div>
    <div class="mb-3">
        <label for="message" class="form-label">Messaggio</label>
        <textarea required name="message" class="form-control" id="message" rows="3"></textarea>
    </div>
    <button class="btn btn-success">SALVA</button>
</form>
```

Codice completo: [listing-19.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/it/parte-09/cap-31/listing-19.php)

`POST /posts` salva:

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

Codice completo: [listing-20.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/it/parte-09/cap-31/listing-20.php)

`save()` riceve un array con i dati del form. Anche qui la SQL usa placeholder nominati, non concatenazione. Lo statement viene preparato, poi `execute()` riceve solo i valori necessari: titolo, email e messaggio. `NOW()` resta nel database perché la data di creazione appartiene al momento del salvataggio. Il metodo ritorna `rowCount()`, cioè quante righe sono state inserite. La regola è semplice: il controller legge `$_POST`, il model salva con prepared statement, poi il controller fa redirect.

## Passo 19: editare, aggiornare ed eliminare

Nel dettaglio del post aggiungiamo azioni esplicite:

```php
<form action="/posts/<?= $post->id ?>/edit" method="GET">
    <button class="btn btn-success">MODIFICA</button>
</form>

<form action="/posts/<?= $post->id ?>/delete" method="POST">
    <button class="btn btn-danger">ELIMINA</button>
</form>
```

Codice completo: [listing-21.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/it/parte-09/cap-31/listing-21.php)

L'update usa lo stesso `save()` del controller, ma con un ID:

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

Codice completo: [listing-22.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/it/parte-09/cap-31/listing-22.php)

`update()` è simile a `save()`, ma richiede anche `$postId`. I valori modificabili arrivano dall'array `$post`; l'identificatore arriva dalla rotta e finisce nel placeholder `:id`. Questo evita di fidarsi di un campo nascosto per decidere quale riga aggiornare. Il metodo ritorna ancora `rowCount()`, utile per sapere se l'operazione ha toccato una riga.

La cancellazione resta un `POST`, non un link `GET`:

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

Codice completo: [listing-23.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/it/parte-09/cap-31/listing-23.php)

`delete()` prepara una DELETE con un singolo parametro. Qui usiamo `bindValue()` con `PDO::PARAM_INT` per dichiarare esplicitamente che l'id è un intero. Dopo `execute()`, `rowCount()` indica quante righe sono state eliminate. Questa è già una buona abitudine HTTP: leggere con `GET`, cambiare stato con `POST`.

## Passo 20: mostrare e salvare commenti

Il commento è un model separato perché usa una tabella separata:

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

Codice completo: [listing-24.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/it/parte-09/cap-31/listing-24.php)

Il costruttore di `Comment` segue lo stesso schema di `Post`: riceve `PDO` e non crea connessioni da solo. `all()` riceve `$postId`, prepara una query filtrata per `post_id`, ordina i commenti dal più recente e ritorna tutte le righe. `save()` riceve un array già composto dal controller, prepara l'INSERT e lo esegue. Questo model mostra la prima relazione pratica: per leggere o salvare commenti serve sempre sapere a quale post appartengono.

Il controller carica post e commenti insieme:

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

Codice completo: [listing-25.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/it/parte-09/cap-31/listing-25.php)

Il metodo `show()` ora fa due letture coordinate: prima recupera il post, poi crea `Comment` con la stessa connessione e legge i commenti collegati. La view riceve entrambe le variabili con `compact('post', 'comments')`, quindi può mostrare contenuto principale e discussione nella stessa pagina. `saveComment()` riceve `$postId` dalla rotta, compone l'array per il model usando `$_POST` e poi fa redirect al dettaglio del post. Il redirect evita il reinvio del form se l'utente aggiorna la pagina. Costruiamo i commenti dopo il CRUD dei post perché sono il primo caso in cui una risorsa dipende da un'altra risorsa. È lo stesso ragionamento che ritroveremo in API REST, repository e relazioni tra entità.

## Passo 21: cosa abbiamo ottenuto

A questo punto `freeblog` ha:

- front controller;
- URL riscritte verso `public/index.php`;
- layout Bootstrap;
- controller e base controller;
- helper per renderizzare view;
- PDO configurato;
- factory per costruire la connessione;
- model `Post` e `Comment`;
- route GET e POST;
- parametri nell'URL;
- lista, dettaglio, creazione, modifica, eliminazione e commenti.

È un progetto MVC completo, ma non ancora un progetto enterprise. I limiti sono evidenti:

- autoload fatto a mano;
- configurazione sensibile nel codice;
- router legato a `$_SERVER`;
- controller legati a `$_POST`, funzioni helper e model concreti;
- model che mescolano oggetti dati e SQL;
- nessuna suite di test;
- nessuna analisi statica;
- nessun ambiente riproducibile.

Questi non sono fallimenti: sono il motivo per cui il refactoring enterprise ha senso.

## Passaggio a phpenterpriseblog

Il progetto pubblico del refactoring è:

```bash
git clone https://github.com/hidran/phpenterpriseblog.git
cd phpenterpriseblog
git tag -l
```

Codice completo: [listing-26.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v9-chapter-31/it/parte-09/cap-31/listing-26.sh)

Repository pubblico: [phpenterpriseblog](https://github.com/hidran/phpenterpriseblog).

Nel capitolo successivo non ricominciamo da zero. Prendiamo il flusso appena costruito in `freeblog` e lo portiamo verso una forma più professionale: Composer, PSR-4, request e response, router testato, DTO, repository, servizi, dependency injection, PSR-7/15, migrazioni, quality gate, test, Docker, Redis e CI/CD.

## In sintesi

In questo capitolo abbiamo costruito `freeblog` da zero, un passo alla volta: dal front controller e dall'URL rewriting fino al router con parametri, dai controller e dalle view al model `Post` con PDO, passando per `DbPdo`, la factory e la dependency injection nel costruttore del controller. Il risultato non è ancora un framework, ed è giusto così: è il minimo indispensabile per capire *perché* i framework fanno quello che fanno. Alcune scelte di questo capitolo — il Singleton didattico, l'eccezione generica sulle rotte non trovate, la SQL dentro al model — sono volutamente provvisorie: nei prossimi capitoli le sostituiremo con container, eccezioni dedicate e repository. Se il flusso richiesta → router → controller → model → view ti è chiaro, il resto della Parte IX sarà un lavoro di raffinamento, non di riscrittura.
