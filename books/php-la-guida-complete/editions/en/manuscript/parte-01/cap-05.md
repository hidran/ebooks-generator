# 5. Editor, IDE and debugging

Writing PHP isn't just about knowing the syntax. You also need an environment that helps you read code, find errors, navigate between files, and control execution. You can follow the entire book with Visual Studio Code, PhpStorm or NetBeans; the important thing is to configure PHP, the terminal and Xdebug well.

## Visual Studio Code

Visual Studio Code is lightweight, free and very flexible. For PHP it is best to install some extensions:

- an extension for PHP support and code completion;
- an extension for Xdebug;
- a formatter, if you want to maintain a consistent style;
- Git support, already integrated but can be improved with dedicated extensions.

Open a project folder, not a single file. This way the editor can understand the paths, index the code, and use a built-in terminal in the correct place.

## The integrated terminal

In the integrated terminal try now:

```bash
php -v
```

Full source: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-5/en/parte-01/cap-05/listing-01.sh)


If VS Code doesn't find PHP but the system terminal does, the problem is the PATH with which the application was started. On macOS and Linux it is often enough to reopen VS Code from the terminal:

```bash
code .
```

Full source: [listing-02.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-5/en/parte-01/cap-05/listing-02.sh)


On Windows you can use Git Bash as your default terminal. This is convenient because many commands from the PHP and Composer world are documented with Unix syntax.

## Run a file from the editor

A PHP file can be executed in two different ways:

```bash
php script.php
```

Full source: [listing-03.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-5/en/parte-01/cap-05/listing-03.sh)


or via web server:

```bash
php -S localhost:8000
```

Full source: [listing-04.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-5/en/parte-01/cap-05/listing-04.sh)


The difference is fundamental. From the terminal there are no `$_GET`, `$_POST`, cookies and sessions as in a web request. From the browser, however, PHP works within the request-response cycle.

## Configure Xdebug in VS Code

Debugging with breakpoints requires three things:

- Xdebug installed and active in the PHP version used;
- the editor listening;
- a request to start the debugging session.

An essential `.vscode/launch.json` file can be:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Listen for Xdebug",
      "type": "php",
      "request": "launch",
      "port": 9003
    }
  ]
}
```

Full source: [listing-05.json](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-5/en/parte-01/cap-05/listing-05.json)


Xdebug 3 uses the `9003` port by default. If you find older guides with `9000`, check the version: many configurations don't work just because they mix Xdebug 2 and Xdebug 3 settings.

## `php.ini` and modules loaded

When PHP behaves unexpectedly, ask it what configuration it is using:

```bash
php --ini
```

Full source: [listing-06.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-5/en/parte-01/cap-05/listing-06.sh)


To check modules:

```bash
php -m
```

Full source: [listing-07.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-5/en/parte-01/cap-05/listing-07.sh)


To search for Xdebug:

```bash
php -m | grep xdebug
```

Full source: [listing-08.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-5/en/parte-01/cap-05/listing-08.sh)


Remember that PHP CLI and PHP web server can read different `php.ini` files. If you enable an extension in the CLI but the browser doesn't see it, you're probably editing the wrong file.

## PhpStorm

PhpStorm is a very complete commercial IDE. It offers refactoring, navigation between classes, integration with Composer, database tools, test runners and debugging already designed for PHP.

To use it well:

- sets the project's PHP interpreter;
- configure Composer;
- connect Xdebug;
- register any local servers if you use path mapping.

Path mapping is useful when the file path seen by the browser does not coincide with the local one. This is common with Docker or virtual machines, less so with Herd, Laragon or XAMPP.

## NetBeans

NetBeans is a good alternative when you want a traditional IDE. In PHP projects you need to configure:

- the PHP path;
- the project folder;
- the local URL to run the application;
- any debugger.

If the IDE doesn't run the right file, first check the project root folder and then the launch URL.

## Practical debugging: `var_dump()` or breakpoint?

`var_dump()` remains very useful:

```php
<?php
var_dump($_GET);
```

Full source: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-5/en/parte-01/cap-05/listing-09.php)


You'll often use it to figure out what a variable contains. But when the flow gets longer, a breakpoint is more effective: you can see the state of the program without changing the code and without filling the pages with temporary output.

## In summary

Choose the editor you prefer, but always check that it uses the correct version of PHP. You quickly learn to distinguish between terminal execution and browser execution. When something doesn't add up, check `php -v`, `php --ini`, `php -m` and your Xdebug configuration: in most cases the problem is there.
