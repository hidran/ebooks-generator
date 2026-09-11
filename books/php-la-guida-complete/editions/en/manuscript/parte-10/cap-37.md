# 37. Deploy to Heroku

An application is not complete as long as it is only on your machine. Deployment brings the project online and introduces new variables: environment, remote database, configuration, logs, paths and differences between development and production.

## Prepare the application

Before deployment check:

- the public entry point (`public/index.php`);
- Composer configured;
- no hardcoded passwords;
- configuration read from environment variables;
- errors not shown in production;
- unnecessary files excluded from deployment.

A minimal configuration can read variables:

```php
<?php
$dsn = getenv("DATABASE_DSN");
$user = getenv("DATABASE_USER");
$password = getenv("DATABASE_PASSWORD");
```

Full source: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-37/en/parte-10/cap-37/listing-01.php)


## Procfile

Heroku uses a `Procfile` to know how to launch the app:

```text
web: vendor/bin/heroku-php-apache2 public/
```

Full source: [listing-02.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-37/en/parte-10/cap-37/listing-02.txt)


This indicates that the web root is `public/`, not the project folder.

## Composer in production

Heroku detects a PHP app by the presence of `composer.json`. Make sure the required PHP version is declared:

```json
{
  "require": {
    "php": "^8.5"
  }
}
```

Full source: [listing-03.json](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-37/en/parte-10/cap-37/listing-03.json)


During deployment Heroku runs `composer install` and prepares `vendor/`.

## Remote database

The local database is not loaded automatically. You need to create a remote database, configure credentials, and apply schema.

The principle is the same:

```sql
CREATE TABLE users (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(190) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE posts (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NULL,
    title VARCHAR(190) NOT NULL,
    body TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Full source: [listing-04.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-37/en/parte-10/cap-37/listing-04.sql)


In real projects you will use migrations. Here you can manually run the schema, but keep a versioned SQL file so you don't miss steps.

## File upload in production

Many platforms, Heroku included, have ephemeral filesystems: uploaded files can disappear with each deploy or reboot. For avatars and images in production you need external storage, such as S3 or compatible services.

This is an important point: the upload code works locally, but the production architecture must decide where to keep persistent files.

## Log

In production you don't look at the browser screen to understand errors. Log uses:

```bash
heroku logs --tail
```

Full source: [listing-05.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-37/en/parte-10/cap-37/listing-05.sh)


In the code, `error_log()` is the minimum. For serious errors, tools like Sentry help see stack trace, frequency, and context.

## Routes and autoload

If a route works "by chance" locally, it can break in production. Always use `__DIR__` and absolute paths derived from the project structure:

```php
<?php
require __DIR__ . "/../vendor/autoload.php";
```

Full source: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-37/en/parte-10/cap-37/listing-06.php)


Don't depend on the current folder.

## In summary

Deployment requires discipline: out-of-code configuration, correct public root, Composer, remote database, logs and attention to persistent files. Heroku simplifies startup, but doesn't eliminate architectural decisions. The difference between educational project and real application begins here.
