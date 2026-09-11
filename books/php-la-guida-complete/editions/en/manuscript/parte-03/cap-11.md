# 11. String functions

Strings are everywhere: names, emails, URLs, messages, templates, query strings, contents read from files and data received from forms. PHP offers many dedicated functions and in this chapter we see the ones you will use most often.

## Clear a string

When you receive text from outside you should expect spaces, inconsistent capitalization, and unexpected characters. The first functions to know are `trim()`, `strtolower()` and `strtoupper()`.

```php
<?php
$email = "  JOHN@Example.COM  ";

$email = trim($email);
$email = strtolower($email);

echo $email; // john@example.com
```

Full source: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/en/parte-03/cap-11/listing-01.php)


`trim()` eliminate spaces at the beginning and at the end. It doesn't change the internal spaces, so `"John Smith"` remains `"John Smith"`.

## Search inside a string

For years the most common function to search for a substring was `strpos()`:

```php
<?php
$url = "https://example.com/docs/php";

if (strpos($url, "php") !== false) {
    echo "The string contains php";
}
```

Full source: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/en/parte-03/cap-11/listing-02.php)


The comparison must be `!== false`, not `!= false`, because `strpos()` can return `0` when the searched text is at the beginning of the string. `0` is a valid value, but in a weak comparison it would be interpreted as `false`.

Since PHP 8 there are more readable functions:

```php
<?php
$name = "index.php";

var_dump(str_contains($name, ".php"));
var_dump(str_starts_with($name, "index"));
var_dump(str_ends_with($name, ".php"));
```

Full source: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/en/parte-03/cap-11/listing-03.php)


When you can use PHP 8, prefer these functions: they communicate the intent of the code without having to remember the particular behavior of `strpos()`.

## Replace text

`str_replace()` replaces all occurrences:

```php
<?php
$title = "Basic PHP guide";

echo str_replace("Basic", "Complete", $title);
```

Full source: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/en/parte-03/cap-11/listing-04.php)


You can also pass array:

```php
<?php
$text = "Hello {name}, welcome to {topic}.";

echo str_replace(
    ["{name}", "{topic}"],
    ["John", "PHP"],
    $text
);
```

Full source: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/en/parte-03/cap-11/listing-05.php)


This technique is useful for small templates, but does not replace a real templating engine as the interface grows.

## Divide and unite

`explode()` divide a string into an array:

```php
<?php
$csv = "john,smith,john@example.com";

$parts = explode(",", $csv);
print_r($parts);
```

Full source: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/en/parte-03/cap-11/listing-06.php)


`implode()` does the reverse operation:

```php
<?php
$tags = ["php", "mysql", "web"];

echo implode(", ", $tags);
```

Full source: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/en/parte-03/cap-11/listing-07.php)


`join()` is an alias of `implode()`. In modern code it is better to use `implode()` because it is more recognizable.

## Escape and slash

`stripslashes()` removes backslashes added before characters such as single quotes and quotes:

```php
<?php
$value = "Rock \\'n\\' Roll";
echo stripslashes($value);
```

Full source: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/en/parte-03/cap-11/listing-08.php)


Today you shouldn't build SQL queries by adding slashes manually. For the database we will use prepared statement. String functions are for transforming text, not inventing flimsy security protections.

## Length and portions

To know the length:

```php
<?php
echo strlen("PHP");
```

Full source: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/en/parte-03/cap-11/listing-09.php)


To extract a part:

```php
<?php
$code = "IT-2026-001";

echo substr($code, 0, 2);  // IT
echo substr($code, -3);    // 001
```

Full source: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/en/parte-03/cap-11/listing-10.php)


With Unicode, accented, or multibyte text, evaluate the `mb_*` functions, such as `mb_strlen()` and `mb_substr()`. `strlen("è")` doesn't count "visible characters", it counts bytes.

## Normalize user input

A complete example:

```php
<?php
function normalize_email(string $email): string
{
    return strtolower(trim($email));
}

$email = normalize_email($_POST["email"] ?? "");
```

Full source: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/en/parte-03/cap-11/listing-11.php)


Normalizing does not mean validating. After normalization you can check:

```php
<?php
if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    echo "Invalid email";
}
```

Full source: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v5-chapter-11/en/parte-03/cap-11/listing-12.php)


## In summary

String functions are small, but they decide the quality of a lot of code. Use `trim()` and `strtolower()` to normalize, `str_contains()` and similar functions to read conditions better, `str_replace()` for simple substitutions, `explode()` and `implode()` to switch between strings and arrays. When working with external data, always separate transformation, validation and security.
