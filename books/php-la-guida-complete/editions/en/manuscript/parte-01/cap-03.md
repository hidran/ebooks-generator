# 3. Install PHP on macOS with Laravel Herd and Homebrew

On macOS the quickest way to start working with PHP is to use Laravel Herd. Herd installs PHP, configures a local web server and allows you to change the language version without having to manually modify Apache, Nginx or configuration files scattered throughout the system.

The goal of this chapter is not to build a perfect environment for every scenario, but to have a machine ready to follow the book: run PHP files from the terminal, open projects in the browser, use MySQL or MariaDB, and prepare for debugging with Xdebug.

## Install Laravel Herd

Download Herd from the official Laravel website and install it as a normal macOS application. Once started, Herd registers a working folder and makes available local sites with convenient domains, usually using extensions like `.test`.

The main advantage is that you don't have to remember the path to the PHP executable: Herd exposes it in the PATH and also makes it available from the terminal.

To verify the installation open the terminal and run:

```bash
php -v
```

Full source: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/en/parte-01/cap-03/listing-01.sh)


If the command shows the PHP version, you can already create the first file:

```php
<?php
echo "PHP works on macOS";
```

Full source: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/en/parte-01/cap-03/listing-02.php)


Save it as `index.php` inside a project folder and open it with Herd or with the integrated server:

```bash
php -S localhost:8000
```

Full source: [listing-03.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/en/parte-01/cap-03/listing-03.sh)


In your browser visit `http://localhost:8000`. If you see the message printed, the environment is ready.

## Change PHP version

One reason to use Herd is version management. Throughout the book you will encounter features introduced in PHP 7.4, PHP 8.0, PHP 8.1, PHP 8.2, PHP 8.4, and PHP 8.5. It is useful to be able to test the examples with different versions.

From Herd you can select the global version or the one associated with a site. When working on a real project it is worth checking the version required by the project, often declared in `composer.json`:

```json
{
  "require": {
    "php": "^8.5"
  }
}
```

Full source: [listing-04.json](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/en/parte-01/cap-03/listing-04.json)


The version used by the terminal and the one used by the web server must match. Many strange errors arise precisely from this difference: the command `php -v` shows one version, while the browser uses another.

## Install Homebrew

Homebrew is the most used package manager on macOS. While Herd is enough for PHP, Homebrew is useful for installing databases, terminal utilities, and tools like `wget`, `git`, `composer`, MariaDB, or phpMyAdmin.

Check if it is already present:

```bash
brew --version
```

Full source: [listing-05.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/en/parte-01/cap-03/listing-05.sh)


If it is not installed, follow the command given by the official Homebrew site. After installation, close and reopen the terminal, then repeat the check.

## Install MariaDB or MySQL

For database chapters you can use MySQL or MariaDB. For the purposes of the book, the differences are not important: we will use standard SQL and common functionality.

With Homebrew you can install MariaDB like this:

```bash
brew install mariadb
brew services start mariadb
```

Full source: [listing-06.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/en/parte-01/cap-03/listing-06.sh)


Then enter the client:

```bash
mariadb
```

Full source: [listing-07.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/en/parte-01/cap-03/listing-07.sh)


or, if you have MySQL installed:

```bash
mysql -u root
```

Full source: [listing-08.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/en/parte-01/cap-03/listing-08.sh)


The first check to do is to create a test database:

```sql
CREATE DATABASE php_guide;
SHOW DATABASES;
```

Full source: [listing-09.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/en/parte-01/cap-03/listing-09.sql)


When the database responds, PHP can connect using PDO, as we will see in later chapters.

## phpMyAdmin on macOS

phpMyAdmin is not essential, but it helps a lot in the early stages because it shows databases, tables and records in a visual way.

With Homebrew you can install it:

```bash
brew install phpmyadmin
```

Full source: [listing-10.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/en/parte-01/cap-03/listing-10.sh)


The precise configuration depends on the web server used. If you're following the book to learn PHP, don't waste too much time on this point: the terminal client is enough to understand SQL, and in the projects we will use PHP code to read and write data.

## Configure Xdebug

Debugging is the leap in quality compared to the `var_dump()` scattered throughout the code. Xdebug allows you to stop execution at a breakpoint, see the value of variables and advance line by line.

With Herd the configuration is simplified: check in the settings if Xdebug is available for the selected PHP version. From the terminal you can check the loaded modules:

```bash
php -m | grep xdebug
```

Full source: [listing-11.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/en/parte-01/cap-03/listing-11.sh)


If the module is active, configure the editor to listen for debug connections. In Visual Studio Code the typical extension is "PHP Debug"; PhpStorm support is built-in.

## Laravel Valet

An alternative to Herd is Laravel Valet. Valet creates local domains for project folders and uses Nginx in the background. It is more manual than Herd, but remains widely used.

The installation goes through Composer:

```bash
composer global require laravel/valet
valet install
```

Full source: [listing-12.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/en/parte-01/cap-03/listing-12.sh)


Then choose a folder and record it:

```bash
cd ~/Sites
valet park
```

Full source: [listing-13.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/en/parte-01/cap-03/listing-13.sh)


A folder `blog` will be available as `http://blog.test`. If you're starting now, use Herd; if you want to better understand what's going on under the hood, Valet is a good second step.

## In summary

On macOS you can follow the entire book with Herd, an editor, Composer and MariaDB or MySQL. Homebrew complements the environment when additional packages are needed. Always check three things: `php -v` from the terminal, the PHP version used by the browser and the availability of the database. When these three elements are aligned, you can focus on the code.
