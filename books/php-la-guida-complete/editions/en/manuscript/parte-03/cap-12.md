# 12. Array functions

Arrays are one of the most used structures in PHP. You'll use them for lists, configurations, database results, form data, error messages, and object collections. Knowing the main functions allows you to write shorter and clearer code.

## Add and remove items

To add to queue:

```php
<?php
$names = ["John", "Lucy"];

array_push($names, "Julia");
```

Full source: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/en/parte-03/cap-12/listing-01.php)


In PHP it is very common to use the short syntax:

```php
<?php
$names[] = "Julia";
```

Full source: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/en/parte-03/cap-12/listing-02.php)


To remove the last element:

```php
<?php
$last = array_pop($names);
```

Full source: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/en/parte-03/cap-12/listing-03.php)


To work at the beginning of the array:

```php
<?php
array_unshift($names, "Anne");
$first = array_shift($names);
```

Full source: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/en/parte-03/cap-12/listing-04.php)


These functions modify the original array.

## Sort array

`sort()` sort the values and reindex the array:

```php
<?php
$numbers = [3, 1, 2];
sort($numbers);
```

Full source: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/en/parte-03/cap-12/listing-05.php)


When you have associative keys and want to keep them:

```php
<?php
$scores = [
    "john" => 12,
    "lucy" => 18,
    "anne" => 15,
];

asort($scores);
```

Full source: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/en/parte-03/cap-12/listing-06.php)


`asort()` sorts by value maintaining the association with the key. To sort naturally, which is useful with strings containing numbers, use `natsort()`:

```php
<?php
$files = ["file10.txt", "file2.txt", "file1.txt"];
natsort($files);
```

Full source: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/en/parte-03/cap-12/listing-07.php)


## Transform with `array_map()`

`array_map()` applies a function to each element and returns a new array:

```php
<?php
$prices = [10, 20, 30];

$withVat = array_map(function (int $price): float {
    return $price * 1.22;
}, $prices);
```

Full source: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/en/parte-03/cap-12/listing-08.php)


With the arrow functions:

```php
<?php
$withVat = array_map(fn (int $price): float => $price * 1.22, $prices);
```

Full source: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/en/parte-03/cap-12/listing-09.php)


It's a good choice when you want to transform data without changing the original array.

## Visit with `array_walk()`

`array_walk()` executes a function on each element. You can also receive the key:

```php
<?php
$user = [
    "name" => "John",
    "email" => "john@example.com",
];

array_walk($user, function ($value, $key) {
    echo "$key: $value" . PHP_EOL;
});
```

Full source: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/en/parte-03/cap-12/listing-10.php)


Use `array_walk()` when you want to traverse an array to produce an effect, not when you want to build a new collection. For transform, `array_map()` is clearer.

## Filter

`array_filter()` retains only elements that satisfy a condition:

```php
<?php
$numbers = [1, 2, 3, 4, 5, 6];

$even = array_filter($numbers, fn (int $n): bool => $n % 2 === 0);
```

Full source: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/en/parte-03/cap-12/listing-11.php)


Attention: `array_filter()` keeps the original keys. If you want to reindex:

```php
<?php
$even = array_values($even);
```

Full source: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/en/parte-03/cap-12/listing-12.php)


## Deconstruction

Destructuring allows you to assign elements of an array to multiple variables:

```php
<?php
$point = [10, 20];

[$x, $y] = $point;
```

Full source: [listing-13.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/en/parte-03/cap-12/listing-13.php)


Also works with associative keys:

```php
<?php
$user = [
    "name" => "John",
    "email" => "john@example.com",
];

["name" => $name, "email" => $email] = $user;
```

Full source: [listing-14.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/en/parte-03/cap-12/listing-14.php)


It's very readable when a function returns multiple values:

```php
<?php
function split_name(string $fullName): array
{
    return explode(" ", $fullName, 2);
}

[$firstName, $lastName] = split_name("John Smith");
```

Full source: [listing-15.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/en/parte-03/cap-12/listing-15.php)


## Asymmetric deconstruction

You don't always need all the elements:

```php
<?php
$row = [10, "John", "Smith", "john@example.com"];

[$id, $name,, $email] = $row;
```

Full source: [listing-16.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-12/en/parte-03/cap-12/listing-16.php)


The blank comma skips a value. Don't abuse it: if the elements become many, an associative array or an object is clearer.

## In summary

Array functions allow you to think in terms of operations: add, remove, sort, transform, filter, destructure. In the projects in this book, we will use these techniques to handle SQL results, validation errors, configurations, and session data. The rule of thumb is simple: choose the function that best expresses the intent of the code.
