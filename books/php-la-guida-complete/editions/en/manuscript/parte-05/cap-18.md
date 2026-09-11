# 18. MySQL, phpMyAdmin and SQL Basics

A dynamic site needs to store data: users, posts, comments, settings, tokens, logs. PHP can read and write files, but for structured data and real queries you need a database. In this book we will use MySQL or MariaDB.

## Connect from the command line

Open the client:

```bash
mysql -u root -p
```

Full source: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/en/parte-05/cap-18/listing-01.sh)


or, with MariaDB:

```bash
mariadb -u root -p
```

Full source: [listing-02.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/en/parte-05/cap-18/listing-02.sh)


In on-premises environments like Laragon or XAMPP the root password may be blank. In production it doesn't have to be.

## Create a database

```sql
CREATE DATABASE php_guide
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

Full source: [listing-03.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/en/parte-05/cap-18/listing-03.sql)


Then select it:

```sql
USE php_guide;
```

Full source: [listing-04.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/en/parte-05/cap-18/listing-04.sql)


`utf8mb4` is the correct choice to support accented characters, emojis and international texts.

## Create a table

A minimal `users` table:

```sql
CREATE TABLE users (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(190) NOT NULL UNIQUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Full source: [listing-05.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/en/parte-05/cap-18/listing-05.sql)


Some important decisions:

- `id` identifies each record;
- `AUTO_INCREMENT` generates the value automatically;
- `PRIMARY KEY` makes the identifier unique;
- `NOT NULL` forces you to insert a value;
- `UNIQUE` prevents duplicate emails.

## Insert record

```sql
INSERT INTO users (first_name, last_name, email)
VALUES ('John', 'Smith', 'john@example.com');
```

Full source: [listing-06.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/en/parte-05/cap-18/listing-06.sql)


You can insert multiple lines:

```sql
INSERT INTO users (first_name, last_name, email)
VALUES
  ('Lucy', 'Brown', 'lucy@example.com'),
  ('Anne', 'Green', 'anne@example.com');
```

Full source: [listing-07.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/en/parte-05/cap-18/listing-07.sql)


## Read records

```sql
SELECT * FROM users;
```

Full source: [listing-08.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/en/parte-05/cap-18/listing-08.sql)


In real applications avoid `SELECT *` when you know which columns are needed:

```sql
SELECT id, first_name, last_name, email
FROM users
ORDER BY last_name ASC;
```

Full source: [listing-09.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/en/parte-05/cap-18/listing-09.sql)


To filter:

```sql
SELECT id, first_name, email
FROM users
WHERE email = 'john@example.com';
```

Full source: [listing-10.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/en/parte-05/cap-18/listing-10.sql)


## Update records

```sql
UPDATE users
SET first_name = 'Marco'
WHERE id = 1;
```

Full source: [listing-11.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/en/parte-05/cap-18/listing-11.sql)


The `WHERE` clause is essential. Without `WHERE`, you update all rows in the table.

## Delete records

```sql
DELETE FROM users
WHERE id = 1;
```

Full source: [listing-12.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/en/parte-05/cap-18/listing-12.sql)


Here too: without `WHERE`, you delete everything. When you are learning, first do an `SELECT` with the same condition:

```sql
SELECT * FROM users WHERE id = 1;
```

Full source: [listing-13.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/en/parte-05/cap-18/listing-13.sql)


If the selection shows the right record, then execute the `DELETE`.

## Add columns and indexes

To add a column:

```sql
ALTER TABLE users
ADD role_type VARCHAR(20) NOT NULL DEFAULT 'user';
```

Full source: [listing-14.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/en/parte-05/cap-18/listing-14.sql)


To add an index:

```sql
CREATE INDEX users_last_name_index ON users (last_name);
```

Full source: [listing-15.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/en/parte-05/cap-18/listing-15.sql)


Indexes speed up searches and sorting, but come at a cost in writing and space. In initial projects we will use them where they make sense: emails, foreign keys, columns often used in filters.

## phpMyAdmin

phpMyAdmin allows you to do the same operations as a browser: create databases, tables, columns, indexes and records. It's useful for seeing structure and checking data while writing PHP.

Use it to explore, but don't forget SQL. In code, you won't click buttons: you'll build queries, use connections, and manage results.

## Connect from PHP with PDO

For new code, this book uses PDO: it works with multiple databases, exposes a consistent interface, and makes prepared statements the default habit. The following minimal example enables exceptions and escapes output before printing HTML:

```php
<?php
declare(strict_types=1);

$pdo = new PDO(
    'mysql:host=localhost;dbname=php_guide;charset=utf8mb4',
    'root',
    '',
    [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    ],
);

$stmt = $pdo->query('SELECT id, first_name, email FROM users');

foreach ($stmt as $user) {
    echo htmlspecialchars($user['first_name'], ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8')
        . ' - '
        . htmlspecialchars($user['email'], ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8')
        . '<br>';
}
```

Full source: [listing-16.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/en/parte-05/cap-18/listing-16.php)


When a query uses user-provided data, never concatenate it into the SQL string. Always use prepared statements:

```php
<?php
declare(strict_types=1);

$stmt = $pdo->prepare(
    'SELECT id, first_name, email FROM users WHERE email = :email',
);

$stmt->execute(['email' => $email]);

$user = $stmt->fetch();
```

Full source: [listing-17.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/en/parte-05/cap-18/listing-17.php)


## In summary

MySQL stores structured data and SQL allows you to create, read, update and delete it. You must be familiar with `CREATE TABLE`, `INSERT`, `SELECT`, `UPDATE`, `DELETE`, `WHERE`, `ORDER BY`, indices and primary keys. From here on these concepts will become PHP code in the User Management System.
