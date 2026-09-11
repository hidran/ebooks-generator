# 33. Domain models, repositories, PDO y migraciones

En el User Management System de la Parte VI el acceso a los datos era directo y disperso: `mysqli` llamado dentro de las funciones, la SQL mezclada con la lógica. Funcionaba, pero cada query era un punto donde podías equivocarte por tu cuenta. En el blog enterprise el **data layer** — la capa que habla con la base de datos — se reorganiza en torno a tres límites claros: PDO configurado una sola vez con opciones seguras, los **models** que se convierten en objetos de datos tipados sin una línea de SQL, y los **repositories** que son los únicos en poseer las queries. Cada uno de estos límites responde a una pregunta que la Parte VI dejaba abierta, y en este capítulo los construimos uno a uno siguiendo el código real del proyecto.

Repositorio UMS de referencia: [php-user-management-system](https://github.com/hidran/php-user-management-system). El commit final implementa remember me con selector, token hash, rotación y revocación.

## Conexión PDO segura

La conexión no debe recrearse a mano en cada controller. El proyecto usa una factory que lee el entorno y crea un `PDO` con opciones **no negociables**:

```php
<?php

declare(strict_types=1);

final class PdoConnection
{
    public function __construct(array $options)
    {
        $defaultOptions = [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
        ];

        $this->pdo = new PDO(
            $options['dsn'],
            $options['user'],
            $options['password'],
            $defaultOptions,
        );
    }
}
```

Código completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-33/es/parte-09/cap-33/listing-01.php)


Fuente real: [`src/Database/PdoConnection.php` en `lesson-1-4`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-4/src/Database/PdoConnection.php).


Esas tres opciones se llaman "no negociables" porque establecen, en un solo sitio, el comportamiento de **cada** query de la aplicación, y cada una resuelve un problema concreto. `PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION` hace que un error SQL lance una excepción en lugar de fallar en silencio: es el *fail loud* del Capítulo 30 aplicado a la base de datos, para que una query rota se note de inmediato y no deje seguir con datos que faltan. `PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC` devuelve las filas como arrays asociativos limpios, sin el duplicado con índices numéricos que PDO produciría por defecto. La tercera es la más importante para la seguridad: `PDO::ATTR_EMULATE_PREPARES => false` obliga a PDO a usar los **prepared statements reales** del driver, en lugar de simularlos del lado de PHP pegando los valores en la cadena. Es la forma más sólida de la defensa contra la SQL injection que aprendiste a las malas en el Capítulo 20: aquí ya no es una disciplina que recordar en cada query, está fijada de una vez por todas en el origen.

La factory, por su parte, construye el DSN a partir de los parámetros de entorno:

```php
<?php

declare(strict_types=1);

$dsn = sprintf(
    '%s:host=%s;port=%d;dbname=%s;charset=utf8mb4',
    $driver,
    $host,
    $port,
    $database,
);
```

Código completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-33/es/parte-09/cap-33/listing-02.php)


Fuente real: [`src/Database/ConnectionFactory.php` en `lesson-1-4`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-4/src/Database/ConnectionFactory.php).


Fíjate en `charset=utf8mb4`: es el conjunto de caracteres Unicode completo, que maneja correctamente cualquier texto (emoji incluidos) y evita viejos trucos de injection ligados a codificaciones parciales. Pero el cambio arquitectónico más importante es lo que **ya no** está: ningún Singleton global, ninguna función `getConnection()` invocada por todas partes como en la Parte VI. La conexión se crea una vez, se registra en el container y se **inyecta** donde hace falta. Quien necesita la base de datos la declara en el constructor y la recibe — no va a buscarla a una variable global.

## Models como DTO

El model `Post` no contiene ni una línea de SQL. Describe solo la forma de un post:

```php
<?php

declare(strict_types=1);

final class Post
{
    public function __construct(
        public readonly int $id,
        public readonly string $title,
        public readonly string $message,
        public readonly int $userId,
        public readonly string $datecreated,
        public readonly string $email,
    ) {
    }
}
```

Código completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-33/es/parte-09/cap-33/listing-03.php)


Fuente real: [`src/Models/Post.php` en `lesson-1-5`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-5/src/Models/Post.php).


Es un **DTO** inmutable, construido con la property promotion y los `readonly` del Capítulo 25: un objeto que transporta datos y nada más. No sabe cómo se lee ni se escribe en la base de datos, no contiene lógica: es la forma tipada de una fila de la tabla `posts`. Esta separación — el model es el *dato*, el repository es el *acceso al dato* — no es un capricho, tanto que en el proyecto está puesta por escrito en un **ADR** (Architecture Decision Record, el documento con el que un equipo registra las decisiones de arquitectura y su porqué). La ventaja práctica es la tranquilidad: un `Post` que no tiene acceso a la base de datos no podrá nunca, por descuido, lanzar una query en medio de una view. Es solo datos que fluyen, tipados, entre las capas de la aplicación.

## Repositories para la SQL

Si el model es el dato, el **repository** es el único que sabe cómo leerlo y escribirlo. Lee filas de la base de datos y las transforma en models:

```php
<?php

declare(strict_types=1);

class PostRepository
{
    public function __construct(protected readonly PDO $pdo)
    {
    }

    public function findById(int $id): ?Post
    {
        $sql = 'SELECT p.*, u.email FROM posts p '
             . 'INNER JOIN users u ON u.id = p.user_id '
             . 'WHERE p.id = :id';

        $stmt = $this->pdo->prepare($sql);
        $stmt->execute(['id' => $id]);

        $row = $stmt->fetch();

        return $row === false ? null : Post::fromRow($row);
    }
}
```

Código completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-33/es/parte-09/cap-33/listing-04.php)


Fuente real: [`src/Repositories/PostRepository.php` en `lesson-1-5`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-5/src/Repositories/PostRepository.php).


Mira `findById()`: prepara la query, la ejecuta **ligando** el `id` como parámetro (`:id`) — nunca concatenado en la cadena — recupera la fila y la transforma en un `Post`, o devuelve `null` si no existe. Hay tres lecciones de los capítulos anteriores condensadas aquí: el prepared statement con valor ligado (Capítulo 20, contra la SQL injection), el tipo de retorno `?Post` que hace explícita la ausencia (Capítulo 27), y la conversión fila→objeto que mantiene los datos crudos de la base de datos fuera del resto del código. El controller no conoce ni la tabla ni la query: pide `findById()` y recibe un `?Post`. Si mañana cambias la base de datos, o pasas a un ORM, cambias solo el repository — todo lo demás sigue funcionando, porque depende del método, no de la SQL que hay detrás.

![Una página de post del blog enterprise: el post llega de `findById()` en el `PostRepository`, los comentarios de un segundo repository. El controller se limita a coordinarlos y pasarlos a la view.](figures/cap-33/enterprise-blog-post-detail.png)

## Guardar posts sin bugs heredados

El proyecto antiguo contenía un bug didácticamente valioso: una columna se llenaba con el campo equivocado. En el nuevo repository el método `save()` hace **explícita** la forma de los datos, y eso por sí solo hace el bug más difícil de cometer:

```php
<?php

declare(strict_types=1);

public function save(array $data): int
{
    $sql = 'INSERT INTO posts (title, user_id, message, datecreated) '
         . 'VALUES (:title, :user_id, :message, NOW())';

    $stmt = $this->pdo->prepare($sql);
    $stmt->execute([
        'title' => $data['title'],
        'user_id' => $data['user_id'],
        'message' => $data['message'],
    ]);

    return (int) $this->pdo->lastInsertId();
}
```

Código completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-33/es/parte-09/cap-33/listing-05.php)


Fuente real: [`src/Repositories/PostRepository.php` en `lesson-1-5`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-5/src/Repositories/PostRepository.php).


La correspondencia entre columnas y parámetros está puesta en fila, legible: `title` va a `title`, `user_id` a `user_id`, `message` a `message`. La inserción también usa parámetros ligados, coherente con `findById()`, y devuelve el id generado con `lastInsertId()`. Pero la verdadera defensa contra el regreso del bug llegará más adelante en forma de **test de regresión**: uno de esos tests que no verifica una feature nueva, sino que "bloquea" un comportamiento correcto para que no vuelva a romperse. El bug descubierto una vez se convierte en un test para siempre — así es como un defecto deja de ser un riesgo recurrente.

## User y Comment

El blog enterprise no tira lo que construiste en la Parte VI: reutiliza sus conceptos de seguridad, redistribuyéndolos entre las clases adecuadas. Reencuentras todo lo del User Management System:

- usuario autenticado;
- passwords guardadas con `password_hash()`;
- verificación con `password_verify()`;
- roles;
- sesión;
- CSRF;
- contenido vinculado a `user_id`.

La diferencia es dónde vive esta lógica: ya no dispersa entre includes y funciones, sino distribuida entre `UserRepository` (los datos de usuario), `AuthService` (las reglas de autenticación), controllers y views. Es el servicio de autenticación el que concentra la lógica:

```php
<?php

declare(strict_types=1);

public function verifyLogin(
    string $email,
    string $password,
    string $token,
    string $sessionToken
): AuthResult {
    if (!hash_equals($sessionToken, $token)) {
        return AuthResult::failure('TOKEN MISMATCH');
    }

    $user = $this->users->findByEmail($email);

    if ($user === null || !password_verify($password, $user->password)) {
        return AuthResult::failure('WRONG PASSWORD');
    }

    return AuthResult::success('LOGGED IN', $user);
}
```

Código completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-33/es/parte-09/cap-33/listing-06.php)


Fuente real: [`src/Services/AuthService.php` en `lesson-1-8`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-8/src/Services/AuthService.php).


`verifyLogin()` reúne en un solo sitio las reglas que en la Parte VI estaban distribuidas: primero compara el token CSRF con `hash_equals()` — la comparación en tiempo constante contra los timing attacks del Capítulo 22 — luego busca al usuario por email, y finalmente verifica la password con `password_verify()`. Fíjate en que no devuelve un simple `true`/`false`: devuelve un `AuthResult`, un objeto que lleva consigo tanto el resultado como el motivo (`TOKEN MISMATCH`, `WRONG PASSWORD`, o el usuario en caso de éxito). Es la autenticación tratada como un servicio con una única responsabilidad, testeable de forma aislada. Una advertencia práctica: esos mensajes son strings técnicos del código; en una aplicación real, si deben mostrarse al usuario, los llevarías a una capa de traducción en lugar de mostrarlos así.

## Migraciones forward-only

Queda un último límite por resolver: la **estructura** de la base de datos. No hay que crearla a mano en phpMyAdmin — un rito manual que nadie recuerda y que ningún entorno reproduce igual — sino describirla en ficheros SQL versionados en Git:

```sql
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS users (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    username VARCHAR(64) NOT NULL,
    email VARCHAR(128) NOT NULL,
    password VARCHAR(255) NOT NULL,
    roletype ENUM('admin','editor','user') NOT NULL DEFAULT 'user',
    PRIMARY KEY (id),
    UNIQUE KEY uniq_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

Código completo: [listing-07.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-33/es/parte-09/cap-33/listing-07.sql)


Fuente real: [`database/migrations/0001_init.sql` en `lesson-1-13`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-13/database/migrations/0001_init.sql).


El fichero `0001_init.sql` es la primera **migración**: un script numerado que describe un paso de la evolución del esquema. Reencontrarás aquí las buenas decisiones del Capítulo 19 — el `password` de 255 caracteres de ancho para el hash, el `roletype` como `enum`, el `email` `UNIQUE` — pero ahora versionadas, para que cada entorno construya la misma base de datos exacta a partir de los mismos ficheros. Quien las aplica es un runner que lleva la cuenta de cuáles ya se han ejecutado y aplica solo las nuevas:

```php
<?php

declare(strict_types=1);

$pending = array_filter(
    $files,
    static fn(string $file): bool => !isset($applied[basename($file)])
);

foreach ($pending as $file) {
    $this->apply($file);
}
```

Código completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-33/es/parte-09/cap-33/listing-08.php)


Fuente real: [`src/Console/MigrateCommand.php` en `lesson-1-14`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-14/src/Console/MigrateCommand.php).


El runner filtra las migraciones **aún no aplicadas** y ejecuta solo esas: relanzarlo es seguro, porque no reaplica lo que ya se ha hecho. Y hay una decisión de fondo, declarada en el nombre: las migraciones son **forward-only**, solo se va hacia adelante. Nada de `down`, nada de "rollback". En producción es más honesto y más seguro añadir un cambio compatible y, si algo sale mal, corregir con una nueva migración hacia adelante, en lugar de ilusionarse con que un script de `down` pueda devolver datos que un `DROP COLUMN` ya ha borrado. Los datos destruidos no vuelven: mejor un modelo que lo reconoce.

## En resumen

El data layer enterprise tiene límites claros, cada uno heredero de una lección de los capítulos anteriores: PDO configurado una vez con opciones seguras (prepared statements reales contra la SQL injection), models como DTO inmutables que transportan datos y nada más, repositories como únicos guardianes de la SQL, services como `AuthService` que concentran la lógica de aplicación, y migraciones versionadas y forward-only para el esquema. Es la misma aplicación de blog de los otros capítulos, pero con el acceso a los datos organizado de modo que sea **testeable** — cada pieza aislable y reemplazable por un falso — y **deployable** — cada entorno reconstruible a partir de los mismos ficheros. Es la diferencia entre código que funciona en tu portátil y código que funciona en todas partes.
