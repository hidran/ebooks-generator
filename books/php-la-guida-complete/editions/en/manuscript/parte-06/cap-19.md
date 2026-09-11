# 19. User Management System: Structure, Data, and Layout

The User Management System is the first complete project in the book. Here we are not using a framework yet, and we are not using Composer yet: the public reference project, [`php-user-management-system`](https://github.com/hidran/php-user-management-system), is a procedural `mysqli` application with explicit includes, PHP templates, and separated controllers.

This choice is deliberate, and it is worth defending openly, because to some it will look like a step backwards. In the rest of the book we talk about *enterprise PHP*: MVC, PSR-4, dependency injection, repositories, tests. So why start over from a procedural application with `mysqli` and hand-written `require`? Because a framework is, at bottom, a set of answers to questions you must first have asked yourself. If you have never felt the pain of including twenty files by hand, Composer's autoload is incomprehensible magic; if you have never mixed logic and HTML in the same file, the controller/view separation is a rule you endure instead of understanding; if you have never written a query by concatenating strings, you do not truly grasp what a query builder saves you. This project makes you live through the most direct flow — configuration, connection, query, template, form, sessions, redirect — so that in Part IX, when the same code becomes classes and services, you know *why*. We first build the version that a framework later improves.

## Repository and Commits

You can read the project's history like this:

```bash
git clone https://github.com/hidran/php-user-management-system.git
cd php-user-management-system
git log --reverse --oneline
```

Full source: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-19/en/parte-06/cap-19/listing-01.sh)

Real source: [`php-user-management-system` repository](https://github.com/hidran/php-user-management-system).

It is worth reading the project **through its history**, not just in its final state. `git log --reverse` shows the commits from first to last, and that order is itself a teaching path: first configuration and MySQL connection, then user list, sorting, search, pagination, CRUD, upload, roles, login, CSRF, sessions, and remember me. Each commit adds a feature on top of the previous one, and reading them in order you see the application **grow** instead of finding it already built. It is a way of studying other people's code that I recommend beyond this book: a good Git history is an explanation written one piece at a time.

## Application Configuration

The `config.php` file holds the central settings. In the final commit it includes the database, pagination, sortable columns, upload, roles, and remember me:

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

Full source: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-19/en/parte-06/cap-19/listing-02.php)

Real source: [`config.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/config.php).

A single file that returns an associative array: it is the simplest way to centralize configuration, and despite its simplicity it applies an important principle. Everything you might want to change without touching the logic — how many records per page, which columns are sortable, which file types to accept, how long remember me lasts — sits **in one place**. It is a preview of the idea of configuration separated from code: the project's functions read from here instead of having "magic" values scattered inside them.

That said, there is a limit worth acknowledging right away, because it is exactly what the enterprise project will fix: here the database password is **written in clear text inside the code**. For a teaching project running locally this is fine, but in production credentials must never sit in a file versioned in Git — they would end up in the repository history, visible to anyone with access. In the enterprise blog of Part IX we will take the next step: moving sensitive values out of the code and reading them from the **environment** (environment variables, the `.env` file). For now keep it in mind as a "to fix" noted in the margin.

## Connecting with `mysqli`

The connection is encapsulated in a function, not rewritten in every file:

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

Full source: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-19/en/parte-06/cap-19/listing-03.php)

Real source: [`connection.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/connection.php).

A single function to establish the connection, called wherever it is needed. It looks trivial, but it is an application of the **DRY** principle: the connection logic — read the config, create the `mysqli` object, handle the error — exists in one place. The day you change database, or add a charset parameter, or want to handle the error differently, you fix it here and the rest of the application benefits. If every file opened its own connection by hand, that same change would have to be repeated in dozens of places. Encapsulating also makes the boundary with MySQL **explicit**: there is a single point where the application touches the database driver, and it is easier to find, understand, and — later — replace. In Part IX this same concept will become a PDO factory registered in the container, but the underlying idea — one place responsible for the connection — is already here.

## Users Table

The `users` table contains personal data, avatar, password hash, and role:

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

Full source: [listing-04.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-19/en/parte-06/cap-19/listing-04.sql)

Real source: [`data/users.sql` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/data/users.sql).

The table schema is not a technical detail to skip over: it is where much of the application's security and correctness is decided, even before writing a line of PHP. Look at a few choices. The `password` column is **255 characters** wide, not 32: because it will not hold a password, but the hash produced by `password_hash()` (Chapter 22), which includes algorithm, cost, and salt. The `role_type` is an `enum` with three fixed values: the database itself rejects a role that is not `user`, `editor`, or `admin` — an integrity constraint that no PHP bug can bypass. The `unique` constraint on `fiscalcode` is the real defence against the duplicates we discussed in Chapter 22: the guarantee is not in an application check, it is here. And the three temporal columns `created_at`, `updated_at`, `deleted_at` tell an intention: `deleted_at` in particular suggests **soft delete**, deleting by marking a date instead of physically removing the row, so a user deleted by mistake is recoverable. The project still handles SQL by hand, and this is valuable precisely because it forces you to see exactly which columns each feature needs.

## Entry Point

`index.php` starts the session, connection, common functions, ACL, and authentication. Then it tries auto-login and protects the main page:

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

Full source: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-19/en/parte-06/cap-19/listing-05.php)

Real source: [`index.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/index.php).

The `index.php` is the **front controller** before the name existed: the single point through which requests to the main page pass. The flow reads top to bottom like a list of priorities: first the dependencies are loaded (session, connection, functions, ACL, auth), then it is established **whether** the user may be here (auto-login, session check, possible redirect), and only afterwards does it move on to building the interface. It is the same order — dependencies, authorization, rendering — that you will find in any framework, only written by hand. That chain of `require_once` at the start is exactly what Composer's autoload, in Part VIII, will make disappear: here you see it bare, and understanding it now turns the autoload into a convenience rather than magic.

## Controller and View

The list controller prepares parameters, count, and records:

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

Full source: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-19/en/parte-06/cap-19/listing-06.php)

Real source: [`controller/displayUsers.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/controller/displayUsers.php).

Here you glimpse, in embryonic form, the **controller/view** separation that will be the heart of Part IX. The controller prints nothing: it gathers the parameters, calls the functions that talk to the database (`getTotalUserCount`, `getUsers`), and prepares the variables that presentation will need. Only at the end does `require 'view/userList.php'` hand over to the file that deals with the HTML. Note the small optimization `$totalRecords ? getUsers($params) : []`: if there is not even one record, the second query is avoided — no point asking for the rows of a page that will be empty.

The view deals with the HTML:

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

Full source: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-19/en/parte-06/cap-19/listing-07.php)

Real source: [`view/userList.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/view/userList.php).

The view is almost only HTML, with a few `<?= ?>` inserting the data prepared by the controller. It is still traditional PHP — no template engine, no classes — but the boundary is already visible and it has concrete value: whoever works on the graphics touches the view without risking breaking the logic, and whoever works on the data touches the controller without getting lost in the HTML. This division of responsibility, achieved here by the simple discipline of keeping the files separate, will in Part IX become a rule imposed by the architecture. Seeing it born by convention, before it is born by constraint, makes you understand *why* the separation pays off.

## In summary

The User Management System starts with direct tools — `config.php`, `connection.php`, common functions, procedural controllers, and PHP templates — and this simple base is not a fallback, it is a teaching choice. Every piece you see here is the "by hand" version of something a framework later automates: the centralized configuration foreshadows environment variables, the connection function foreshadows the factory in the container, the chain of `require_once` foreshadows the autoload, the controller/view separation foreshadows real MVC. Building this version first makes it clear, when we reach Part IX, exactly what the classes, repositories, services, and middleware come to **improve** — and why. A framework understood is far more useful than a framework endured.
