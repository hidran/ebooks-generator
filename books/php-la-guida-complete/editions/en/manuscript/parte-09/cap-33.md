# 33. Domain models, repositories, PDO and migrations

In the User Management System of Part VI, data access was direct and scattered: `mysqli` called inside functions, SQL mixed into the logic. It worked, but every query was a point where you could go wrong on your own. In the enterprise blog the **data layer** — the layer that talks to the database — is reorganized around three clear boundaries: PDO configured once with safe options, **models** that become typed data objects with not a line of SQL, and **repositories** that are the only ones to own the queries. Each of these boundaries answers a question that Part VI left open, and in this chapter we build them one by one following the project's real code.

Reference UMS repository: [php-user-management-system](https://github.com/hidran/php-user-management-system). The final commit implements remember me with selector, token hash, rotation, and revocation.

## Safe PDO connection

The connection should not be recreated by hand in every controller. The project uses a factory that reads the environment and creates a `PDO` with **non-negotiable** options:

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

Full source: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-33/en/parte-09/cap-33/listing-01.php)


Real source: [`src/Database/PdoConnection.php` at `lesson-1-4`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-4/src/Database/PdoConnection.php).


Those three options are called "non-negotiable" because they set, in a single place, the behavior of **every** query in the application, and each solves a concrete problem. `PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION` makes an SQL error raise an exception instead of failing silently: it is the *fail loud* of Chapter 30 applied to the database, so a broken query is noticed at once and does not let execution carry on with missing data. `PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC` returns rows as clean associative arrays, without the duplicate with numeric indexes that PDO would produce by default. The third is the most important for security: `PDO::ATTR_EMULATE_PREPARES => false` forces PDO to use the driver's **real prepared statements**, instead of simulating them PHP-side by pasting the values into the string. It is the strongest form of the defense against SQL injection you learned the hard way in Chapter 20: here it is no longer a discipline to remember at every query, it is set once and for all at the source.

The factory, for its part, builds the DSN from the environment parameters:

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

Full source: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-33/en/parte-09/cap-33/listing-02.php)


Real source: [`src/Database/ConnectionFactory.php` at `lesson-1-4`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-4/src/Database/ConnectionFactory.php).


Note `charset=utf8mb4`: it is the full Unicode character set, which correctly handles any text (emoji included) and avoids old injection tricks tied to partial encodings. But the most important architectural change is what is **no longer** there: no global Singleton, no `getConnection()` function called everywhere as in Part VI. The connection is created once, registered in the container, and **injected** where needed. Whoever needs the database declares it in the constructor and receives it — they do not reach for it from a global variable.

## Models as DTOs

The `Post` model contains not a line of SQL. It describes only the shape of a post:

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

Full source: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-33/en/parte-09/cap-33/listing-03.php)


Real source: [`src/Models/Post.php` at `lesson-1-5`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-5/src/Models/Post.php).


It is an immutable **DTO**, built with the property promotion and `readonly` of Chapter 25: an object that carries data and nothing else. It does not know how to read from or write to the database, it contains no logic: it is the typed shape of a row of the `posts` table. This separation — the model is the *data*, the repository is the *access to the data* — is not a whim, so much so that the project records it in black and white in an **ADR** (Architecture Decision Record, the document a team uses to register architectural decisions and their reasons). The practical advantage is peace of mind: a `Post` that has no access to the database can never, by carelessness, fire a query in the middle of a view. It is just data flowing, typed, between the layers of the application.

## Repositories for SQL

If the model is the data, the **repository** is the only one that knows how to read and write it. It reads rows from the database and turns them into models:

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

Full source: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-33/en/parte-09/cap-33/listing-04.php)


Real source: [`src/Repositories/PostRepository.php` at `lesson-1-5`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-5/src/Repositories/PostRepository.php).


Look at `findById()`: it prepares the query, executes it **binding** the `id` as a parameter (`:id`) — never concatenated into the string — fetches the row, and turns it into a `Post`, or returns `null` if it does not exist. There are three lessons from the previous chapters condensed here: the prepared statement with a bound value (Chapter 20, against SQL injection), the `?Post` return type that makes absence explicit (Chapter 27), and the row→object conversion that keeps the database's raw data out of the rest of the code. The controller knows neither the table nor the query: it asks `findById()` and receives a `?Post`. If tomorrow you change the database, or move to an ORM, you change only the repository — everything else keeps working, because it depends on the method, not on the SQL behind it.

![A post page from the enterprise blog: the post comes from `findById()` in the `PostRepository`, the comments from a second repository. The controller merely coordinates the two and passes them to the view.](figures/cap-33/enterprise-blog-post-detail.png)

## Saving posts without inherited bugs

The old project contained a didactically precious bug: a column was filled with the wrong field. In the new repository, `save()` makes the shape of the data **explicit**, and that alone makes the bug harder to commit:

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

Full source: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-33/en/parte-09/cap-33/listing-05.php)


Real source: [`src/Repositories/PostRepository.php` at `lesson-1-5`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-5/src/Repositories/PostRepository.php).


The correspondence between columns and parameters is laid out, readable: `title` goes into `title`, `user_id` into `user_id`, `message` into `message`. The insert too uses bound parameters, consistent with `findById()`, and returns the generated id with `lastInsertId()`. But the real defense against the bug's return will come later in the form of a **regression test**: one of those tests that does not verify a new feature, but "locks" a correct behavior so it does not break again. A bug discovered once becomes a test forever — this is how a defect stops being a recurring risk.

## User and Comment

The enterprise blog does not throw away what you built in Part VI: it reuses its security concepts, redistributing them among the right classes. You find everything from the User Management System:

- authenticated user;
- passwords saved with `password_hash()`;
- verification with `password_verify()`;
- roles;
- session;
- CSRF;
- content linked to `user_id`.

The difference is where this logic lives: no longer scattered across includes and functions, but distributed among `UserRepository` (the user data), `AuthService` (the authentication rules), controllers, and views. It is the authentication service that concentrates the logic:

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

Full source: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-33/en/parte-09/cap-33/listing-06.php)


Real source: [`src/Services/AuthService.php` at `lesson-1-8`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-8/src/Services/AuthService.php).


`verifyLogin()` gathers in a single place the rules that in Part VI were distributed: first it compares the CSRF token with `hash_equals()` — the constant-time comparison against the timing attacks of Chapter 22 — then it looks up the user by email, and finally it verifies the password with `password_verify()`. Note that it does not return a plain `true`/`false`: it returns an `AuthResult`, an object that carries both the outcome and the reason (`TOKEN MISMATCH`, `WRONG PASSWORD`, or the user on success). It is authentication treated as a service with a single responsibility, testable in isolation. A practical caveat: those messages are technical strings from the code; in a real application, if they need to be shown to the user, you would move them into a translation layer instead of showing them as they are.

## Forward-only migrations

There is one last boundary to sort out: the database **structure**. It should not be created by hand in phpMyAdmin — a manual ritual no one remembers and no environment reproduces the same — but described in SQL files version-controlled in Git:

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

Full source: [listing-07.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-33/en/parte-09/cap-33/listing-07.sql)


Real source: [`database/migrations/0001_init.sql` at `lesson-1-13`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-13/database/migrations/0001_init.sql).


The `0001_init.sql` file is the first **migration**: a numbered script that describes one step in the schema's evolution. You will find here the good choices of Chapter 19 — the `password` 255 characters wide for the hash, the `roletype` as an `enum`, the `email` `UNIQUE` — but now versioned, so every environment builds the exact same database from the same files. Applying them is a runner that keeps track of which have already been executed and applies only the new ones:

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

Full source: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-33/en/parte-09/cap-33/listing-08.php)


Real source: [`src/Console/MigrateCommand.php` at `lesson-1-14`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-14/src/Console/MigrateCommand.php).


The runner filters the migrations **not yet applied** and runs only those: rerunning it is safe, because it does not reapply what has already been done. And there is an underlying choice, declared in the name: the migrations are **forward-only**, you only go forward. No `down`, no "rollback". In production it is more honest and safer to add a compatible change and, if something goes wrong, fix it with a new forward migration, rather than deluding yourself that a `down` script can bring back data that a `DROP COLUMN` has already erased. Destroyed data does not come back: better a model that acknowledges it.

## In summary

The enterprise data layer has clear boundaries, each the heir to a lesson from the previous chapters: PDO configured once with safe options (real prepared statements against SQL injection), models as immutable DTOs that carry data and nothing more, repositories as the sole keepers of SQL, services like `AuthService` that concentrate the application logic, and versioned, forward-only migrations for the schema. It is the same blog application of the other chapters, but with data access organized so that it is **testable** — each piece isolatable and replaceable with a fake — and **deployable** — each environment rebuildable from the same files. It is the difference between code that works on your laptop and code that works everywhere.
