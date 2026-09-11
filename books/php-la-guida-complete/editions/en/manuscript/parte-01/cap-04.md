# 4. Install PHP on Linux with XAMPP

On Linux you can install PHP in many ways: distribution packages, Docker, manual compilation, Apache with PHP mods, PHP-FPM with Nginx or integrated environments. To get started quickly, XAMPP remains an easy way to go because it includes Apache, PHP, MariaDB and phpMyAdmin in one package.

In professional work you will often use more specific tools, but XAMPP is convenient while learning locally: you install it, start the services, create a file `index.php`, and immediately see the result in the browser.

## Install XAMPP

Download the Linux package from the Apache Friends site. After downloading, make the file executable:

```bash
chmod +x xampp-linux-*-installer.run
```

Full source: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/en/parte-01/cap-04/listing-01.sh)


Then start the installer with administrative privileges:

```bash
sudo ./xampp-linux-*-installer.run
```

Full source: [listing-02.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/en/parte-01/cap-04/listing-02.sh)


By default XAMPP is installed in `/opt/lampp`. The main sites folder is:

```text
/opt/lampp/htdocs
```

Full source: [listing-03.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/en/parte-01/cap-04/listing-03.txt)


To start services:

```bash
sudo /opt/lampp/lampp start
```

Full source: [listing-04.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/en/parte-01/cap-04/listing-04.sh)


To stop them:

```bash
sudo /opt/lampp/lampp stop
```

Full source: [listing-05.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/en/parte-01/cap-04/listing-05.sh)


## The first PHP file

Create a test folder inside `htdocs`:

```bash
sudo mkdir /opt/lampp/htdocs/php-guide
```

Full source: [listing-06.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/en/parte-01/cap-04/listing-06.sh)


Then create `index.php`:

```php
<?php
echo "PHP works with XAMPP on Linux";
```

Full source: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/en/parte-01/cap-04/listing-07.php)


Open your browser to:

```text
http://localhost/php-guide/
```

Full source: [listing-08.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/en/parte-01/cap-04/listing-08.txt)


If the message appears, Apache is successfully passing the file to PHP.

## Workbook permissions

A common problem on Linux is editing files in `/opt/lampp/htdocs` without permissions. You can change owner of the project folder:

```bash
sudo chown -R "$USER":"$USER" /opt/lampp/htdocs/php-guide
```

Full source: [listing-09.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/en/parte-01/cap-04/listing-09.sh)


Avoid always working with `sudo`: it makes the editor uncomfortable, creates files with different owners and hides problems that will later reappear in production.

## Use PHP from the terminal

XAMPP installs the PHP binary inside `/opt/lampp/bin`. You can run:

```bash
/opt/lampp/bin/php -v
```

Full source: [listing-10.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/en/parte-01/cap-04/listing-10.sh)


If you want to simply invoke it with `php`, add the path to the PATH in the shell configuration file:

```bash
export PATH="/opt/lampp/bin:$PATH"
```

Full source: [listing-11.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/en/parte-01/cap-04/listing-11.sh)


After reopening the terminal:

```bash
php -v
```

Full source: [listing-12.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/en/parte-01/cap-04/listing-12.sh)


The terminal is important because many PHP tools, including Composer, are used from the command line.

## phpMyAdmin and MariaDB

XAMPP includes phpMyAdmin. You can find it in your browser:

```text
http://localhost/phpmyadmin
```

Full source: [listing-13.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/en/parte-01/cap-04/listing-13.txt)


From here you can create databases, tables, columns and records without immediately remembering all the SQL commands. However, don't use phpMyAdmin as a permanent shortcut: in the chapters on MySQL we will look at queries because a PHP application must be able to talk directly to the database.

A quick check from the terminal:

```bash
/opt/lampp/bin/mysql -u root
```

Full source: [listing-14.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/en/parte-01/cap-04/listing-14.sh)


Then:

```sql
SHOW DATABASES;
```

Full source: [listing-15.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/en/parte-01/cap-04/listing-15.sql)


## Alternatives: distribution packages

On Ubuntu and Debian you can install PHP from the repositories:

```bash
sudo apt update
sudo apt install php php-cli php-mysql apache2 mariadb-server
```

Full source: [listing-16.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/en/parte-01/cap-04/listing-16.sh)


This route is closer to a real server, but requires more configuration. For learning the language, XAMPP is fine; when you start deploying, it will be more useful to understand PHP-FPM, web server and environment variables.

## NetBeans on Ubuntu

NetBeans is also useful. It is a historic IDE for PHP: less lightweight than Visual Studio Code, but convenient if you want an already structured environment with projects, execution, completion, and debugging.

The important thing is to configure the PHP path in the IDE preferences. If you use XAMPP, the binary is:

```text
/opt/lampp/bin/php
```

Full source: [listing-17.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/en/parte-01/cap-04/listing-17.txt)


If you use the distribution's packages, it's usually:

```text
/usr/bin/php
```

Full source: [listing-18.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/en/parte-01/cap-04/listing-18.txt)


## In summary

With Linux you have to pay attention to three aspects: starting services, file permissions and path to the PHP binary. XAMPP simplifies the first setup and allows you to focus on the language, database and projects. When everything works, keep one simple rule: the same code must be able to be executed by the browser and the terminal without surprises.
