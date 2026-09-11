# Introduction {.unnumbered}

I am Hidran Arias, and I have been developing with PHP since 2001. This book collects that daily experience and transforms it into a complete path: from the first lines of code up to structured applications ready for production. It is not a reference manual to be consulted in jumps - although you can use it that way - but a progressive path in which each chapter builds on the previous ones.

## Who is it aimed at?

For readers starting from scratch with PHP, but also for developers who already use it and want to fill gaps in modern language features: from PHP 7 up to PHP 8.5, including typed properties, enums, readonly, property hooks, the pipe operator, the URI extension, and much more. A basic understanding of HTML and CSS is helpful; everything else is explained step by step.

## How the book is organized

The route is divided into ten parts. In **Parts I–III** we prepare the development environment on Windows, macOS, and Linux and learn the fundamentals of the language: syntax, variables, types, operators, control structures, and functions. In **Part IV** we bring PHP to the web: superglobals, cookies, file systems, XML and JSON. **Part V** introduces MySQL and phpMyAdmin.

With **Part VI** the first major project of the book begins: a complete User Management System, with a sortable and paginated user list, search, CRUD, image upload, authentication with login, registration, remember me and role management. **Parts VII and VIII** cover object-oriented programming—from the basics to the latest features—along with Composer and exception handling.

In **Part IX** we build the second project: we take the initial MVC blog and move it toward the public `phpenterpriseblog` repository, with Composer, PSR-4, a tested router, PDO, repositories, services, PSR-7/15, migrations, authentication, tests, Docker, Redis, and CI/CD. **Part X** closes the path with JSON and health checks, deployment, email delivery, advanced tooling, and a final PHP 8.5 checklist.

## Conventions

The code appears in blocks like this:

```php
<?php
echo "Hello, PHP!";
```

Full source: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-front-matter-introduction/en/00-front-matter/04-intro/listing-01.php)


The commands to be executed in the terminal are preceded by the context in which they are launched; file, function, and variable names appear in the text in `constant-width text`. Established English technical terms (array, form, query, cookie...) remain in English, as in everyday professional use.

All the code in the book is designed to be written and executed together with the author: the best way to read this book is with the editor open next to it.

Enjoy the journey into PHP.
