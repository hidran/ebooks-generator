# 29. Composer and packages

In the previous chapter you wrote an autoloader by hand; Composer is the tool that relieves you of that work and much more. It is PHP's standard **dependency manager**, and it does two things that in the modern world are inseparable from the very idea of a "project": it installs and keeps third-party libraries up to date, declaring which packages and which versions are needed, and it automatically generates the **PSR-4 autoload** — that is, exactly the name-to-path mechanism of Chapter 28, but written and optimized for you. It is the tool that turns a pile of `.php` files into a manageable project.

## Install Composer

Composer is a command-line program that you install once on your system. To check that it is there:

```bash
composer --version
```

Full source: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-29/en/parte-08/cap-29/listing-01.sh)


If the command responds with a version number, you are ready. Otherwise install it following the official procedure for your operating system: it is a one-time operation, not something you do for every project.

## `composer.json`

The heart of everything is `composer.json`, the project's **manifest**: a single file that declares what is needed.

```json
{
  "name": "hidran/php-guide",
  "require": {
    "php": "^8.5"
  },
  "autoload": {
    "psr-4": {
      "App\\": "src/"
    }
  }
}
```

Full source: [listing-02.json](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-29/en/parte-08/cap-29/listing-02.json)


Read it line by line, because every key matters. `name` is the project's identity in the form `vendor/package`. `require` lists the dependencies: here there is only `php` with the constraint `^8.5`, where the *caret* means "this version or a compatible later one" — it is the syntax with which you declare a range instead of nailing yourself to a single version. And `autoload.psr-4` holds the `App\ → src/` mapping: it is the convention of Chapter 28, now written once in a declarative place. After creating or modifying the file, ask Composer to generate the autoloader:

```bash
composer dump-autoload
```

Full source: [listing-03.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-29/en/parte-08/cap-29/listing-03.sh)


Composer reads the PSR-4 mapping and produces `vendor/autoload.php`: the industrial, already optimized version of the autoloader you wrote by hand in the last chapter.

## Use Composer autoload

At the application's entry point a single line is enough:

```php
<?php
require __DIR__ . "/../vendor/autoload.php";

use App\Controllers\PostController;

$controller = new PostController();
```

Full source: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-29/en/parte-08/cap-29/listing-04.php)


That single `require __DIR__ . "/../vendor/autoload.php"` replaces **all** the manual `require`s of Chapter 28. From now on you name a class of `App\` — `PostController` — and Composer loads it for you, computing the path from the namespace. Note also the path convention: the autoload sits in `vendor/`, the entry point in `public/`, and from there you go up with `../`. It is the organization you will find again in the MVC project of Part IX.

## Install a package

The real power of Composer is giving access to a whole ecosystem of already-written libraries. Instead of reinventing email sending, you install a package that already does it:

```bash
composer require phpmailer/phpmailer
```

Full source: [listing-05.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-29/en/parte-08/cap-29/listing-05.sh)


With one command Composer updates `composer.json` by adding the dependency, creates or modifies `composer.lock` (we get there shortly), and downloads the package's code into `vendor/`. From that moment the library is available through the autoload, without a single extra `require`:

```php
<?php
use PHPMailer\PHPMailer\PHPMailer;

$mail = new PHPMailer(true);
```

Full source: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-29/en/parte-08/cap-29/listing-06.php)


This is the point of a dependency manager: third-party code integrates into yours as naturally as your own classes, and you reuse the maintenance done by others instead of rewriting — and maintaining — complex functionality like an SMTP client.

## `composer.lock`

Here lies a distinction that causes quite a bit of confusion, and it is worth clarifying well. `composer.json` declares version **constraints** — `^8.5` is a range, not a precise number. `composer.lock`, instead, records the **exact** versions actually installed, resolved from those constraints. In an application the lock file **must be version-controlled** in Git, and it is the most important rule of the chapter: committing the lock guarantees that your laptop, a colleague's machine, the CI and production all install the same exact versions, byte for byte. Without it, everyone would resolve the constraints on their own and you would end up with subtly different builds — the classic "it works on my machine". Hence the difference between the two commands:

```bash
composer install
composer update
```

Full source: [listing-07.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-29/en/parte-08/cap-29/listing-07.sh)


`install` reads the lock file and installs **exactly** those versions: it is deterministic, and it is the command to use on deploy. `update`, instead, recalculates the versions allowed by the constraints, downloads the most recent ones and **rewrites** the lock. It is an operation to do consciously, on your development environment, testing what comes out of it: never run `update` blindly in production, or you risk updating half the application without noticing.

## Packages from GitHub

How does Composer find `phpmailer/phpmailer`? Through **Packagist**, the public index of PHP packages, where authors publish their libraries (often hosted on GitHub). That is where `require` fetches from by default:

```bash
composer require vendor/package
```

Full source: [listing-08.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-29/en/parte-08/cap-29/listing-08.sh)


If a package is not on Packagist, you can declare a custom repository inside `composer.json` and point Composer directly at a Git repo. It is possible, but do it only when you really need to: to start, stick to published and actively maintained packages. Every dependency is someone else's code entering your project, and choosing widespread, well-kept libraries is a first, concrete form of *supply chain* security.

## Useful scripts

`composer.json` can also contain **scripts**, that is, shortcuts for the project's recurring commands:

```json
{
  "scripts": {
    "start": "php -S localhost:8000 -t public",
    "autoload": "composer dump-autoload"
  }
}
```

Full source: [listing-09.json](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-29/en/parte-08/cap-29/listing-09.json)


With the `start` script defined, anyone working on the project can start the local server with:

```bash
composer start
```

Full source: [listing-10.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-29/en/parte-08/cap-29/listing-10.sh)


It is a simple but effective way to **document** the project's commands where it is natural to look for them — in `composer.json` — instead of entrusting them to a README that no one reads. A newcomer does not have to guess how the application starts: they just look at the scripts.

## In summary

Composer solves the two problems that, past the handful of files, every PHP project runs into: **dependencies** and **autoload**. With `composer.json` you declare in a single place the packages, the required PHP version and the PSR-4 mapping; with `vendor/autoload.php` you load everything — your code and libraries — consistently and with one line. Remember the `composer.json`/`composer.lock` pair: the first declares the constraints, the second nails down the exact versions, and it must be committed to get reproducible builds everywhere. In the coming chapters Composer will be the basis of the MVC project and the way we integrate external libraries such as PHPMailer: from here on, every serious project starts from a `composer.json`.
