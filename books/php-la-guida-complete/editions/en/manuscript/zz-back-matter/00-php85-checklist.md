# PHP 8.5 Checklist and Next Steps {.unnumbered}

The code in this book targets PHP 8.5. Before publishing or deploying a real project, install the latest available PHP 8.5.x patch release and review the official release notes.

## PHP 8.5 Features to Know

- **URI extension:** use `Uri\Rfc3986\Uri` and `Uri\WhatWg\Url` when you need more robust URL parsing or normalization than `parse_url()`.
- **Pipe operator `|>`:** makes step-by-step transformations readable without unnecessary temporary variables.
- **`clone()` with property overrides:** simplifies `with...()` methods in `readonly` classes.
- **`#[\NoDiscard]` attribute:** warns when an important return value is ignored.
- **Closures and callables in constant expressions:** useful in attributes, default values, and declarative configuration.
- **Persistent cURL share handles:** reduce initialization cost across repeated requests.
- **`array_first()` and `array_last()`:** read the first or last array value without manually combining `array_key_first()` or `array_key_last()`.

## Starting a New Project

Start with explicit constraints and PSR-4 autoloading:

```json
{
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

Full source: [listing-01.json](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-appendix-php85-checklist/en/zz-back-matter/00-php85-checklist/listing-01.json)


Put `strict_types` in the PHP files you write:

```php
<?php
declare(strict_types=1);

namespace App;
```

Full source: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-appendix-php85-checklist/en/zz-back-matter/00-php85-checklist/listing-02.php)


## Production Checklist

- Use Composer and PSR-4 autoloading instead of scattered `require` calls.
- Use PDO with `PDO::ERRMODE_EXCEPTION`, the `utf8mb4` charset, and prepared statements.
- Do not concatenate user input into SQL, HTML, HTTP headers, or file paths.
- Escape HTML output with `htmlspecialchars(..., ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8')`.
- Use `password_hash()` and `password_verify()` for passwords.
- Use `random_bytes()` or `random_int()` for tokens and security-sensitive randomness.
- Set cookies with `secure`, `httponly`, and `samesite`.
- Keep configuration, passwords, and tokens in environment variables.
- In production, disable `display_errors`, write structured logs, and monitor errors and exceptions.
- Update dependencies and the runtime regularly: security and compatibility depend on patch releases, not only on the major version.
