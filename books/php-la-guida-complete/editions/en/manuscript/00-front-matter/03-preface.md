# Preface {.unnumbered}

## Why This Book Exists

This book is structured as a developer path: first you build solid foundations, then you apply them in real projects, and finally you learn how to organize, protect, and publish code. The structure follows the pattern of strong technical books: each part introduces a problem, explains the required tools, and closes with examples you can run.

PHP is used in many contexts: small sites, business applications, APIs, CMS platforms, and modern frameworks. For that reason, the book alternates foundation chapters, project chapters, and professional-practice chapters. You do not need to know everything before you start; you need to learn it in a useful order.

## Who This Book Is For

This book is for readers who want to learn PHP progressively and for developers who already use PHP but want to align with modern PHP. Basic HTML and CSS knowledge helps. SQL, JavaScript, HTTP, Composer, and deployment tools are introduced when they become necessary.

## How to Read the Examples

The examples target PHP 8.5 and use a style suitable for daily development: explicit types where they help, `declare(strict_types=1)` in application files, prepared statements for database access, escaped output, secure password hashes, tokens generated with `random_bytes()`, and configuration kept outside application logic.

In the early chapters, some examples remain deliberately small because they isolate one concept. In the project chapters, the code moves closer to real application work: validation, redirect-after-POST, CSRF, sessions, PDO, autoloading, dependency injection, and error handling.

## Typographical Conventions

- Function, variable, file, command, and class names appear in `monospace`.
- PHP blocks represent complete files when they begin with `<?php`.
- Terminal blocks show commands to type.
- SQL queries are separated from PHP code so the boundary between database and application remains clear.

## Reference Structure

The book follows common technical-manuscript conventions: front matter with title, copyright, contents, preface, and introduction; body matter divided into parts and chapters; back matter with a checklist, conclusions, and colophon. Each chapter has a practical goal, short sections, executable examples, and a closing summary.
