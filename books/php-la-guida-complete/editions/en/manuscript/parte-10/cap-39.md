# 39. Advanced environments and tools

In this book we used different tools: Laragon, Herd, XAMPP, Homebrew, Valet, Visual Studio Code, PhpStorm, NetBeans, Xdebug, Apache, phpMyAdmin. You don't have to use them all. You need to understand what problem each solves.

## Choose the environment

To get started:

- Windows: Laragon;
- macOS: Herd;
- Linux: XAMPP or distribution packages.

For professional work you might switch to Docker, Valet, DDEV, Laravel Sail or enterprise environments. The principle remains: PHP, web servers, databases and tools must talk to each other.

## Install PHP 8 manually

When installing PHP manually you need to check:

```bash
php -v
php --ini
php -m
```

Full source: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-39/en/parte-10/cap-39/listing-01.sh)


The version, the file `php.ini` and the loaded modules explain almost all the teething problems.

## Apache and virtual hosts

A virtual host associates a local domain with a folder:

```apache
<VirtualHost *:80>
    ServerName blog.test
    DocumentRoot "/path/to/blog/public"
</VirtualHost>
```

Full source: [listing-02.apache](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-39/en/parte-10/cap-39/listing-02.apache)


The root must point to `public`, not the entire project. This way configuration files, sources and `vendor/` are not directly exposed.

## Homebrew, Apache and MariaDB

On macOS you can also install manual stack:

```bash
brew install php
brew install httpd
brew install mariadb
```

Full source: [listing-03.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-39/en/parte-10/cap-39/listing-03.sh)


Then start services:

```bash
brew services start httpd
brew services start mariadb
```

Full source: [listing-04.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-39/en/parte-10/cap-39/listing-04.sh)


It's a good route if you want to understand each component, but it requires more maintenance than Herd.

## Xdebug on Windows and Linux

Xdebug must be compatible with PHP version, architecture and thread safety. When not charging:

- check `php -v`;
- check `php --ini`;
- check if the file `.dll` or `.so` is in the right path;
- check the port `9003`;
- look at `php -m`.

The modern setup includes:

```ini
xdebug.mode=debug
xdebug.start_with_request=yes
xdebug.client_port=9003
```

Full source: [listing-05.ini](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-39/en/parte-10/cap-39/listing-05.ini)


## Different editors

Visual Studio Code is fast and modular. PhpStorm is more complete and integrated. NetBeans remains useful if you prefer a traditional IDE. The choice doesn't change PHP: it changes productivity.

Whichever editor you choose, it must be able to do three things:

- open the project as a folder;
- use the correct PHP;
- start or listen to Xdebug.

## phpMyAdmin and database tools

phpMyAdmin is good for inspecting data. HeidiSQL, TablePlus, DBeaver, and IDE built-in tools offer alternatives. Learn SQL anyway: the visual interface helps, but it doesn't replace understanding queries.

## In summary

There is no single right environment. There is a coherent, reproducible and understandable environment. When something doesn't work, reduce the problem: Which PHP am I using? Which `php.ini`? Which server? Which database? This diagnostic capability is worth more than the name of the instrument.
