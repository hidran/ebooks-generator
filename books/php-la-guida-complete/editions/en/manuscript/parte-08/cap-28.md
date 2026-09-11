# 28. Namespaces and autoload

As long as a project has ten classes, keeping them all in one folder and including them by hand with `require` works. But as soon as it grows — dozens of classes, several third-party libraries — that model crumbles, for two distinct reasons. The first is about **names**: two different classes cannot both be called `User`, yet it happens all the time. The second is about **loading**: listing a `require` by hand for every class becomes unmanageable. Namespaces solve the first problem, autoload the second. They are two independent tools that in modern code always work together, and it is useful to see them separately first and then understand how they fit.

## The problem of names

Imagine using two libraries, each of which defines a `User` class. Without namespaces they live in the same global "name space", and the second one to be loaded causes an error: the name is already taken. Namespaces give each class a **complete name** that avoids the collision, like a logical folder:

```php
<?php
namespace App\Models;

class User
{
}
```

Full source: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-28/en/parte-08/cap-28/listing-01.php)


The line `namespace App\Models` declares that everything that follows lives in that space: the class is no longer just `User`, but in full `App\Models\User`. Another library may have its `Vendor\Auth\User`, and the two will never be confused, because the complete name is different. It is the same principle as paths in a filesystem: two `index.php` files coexist without trouble as long as they are in different folders.

## Use a namespaced class

Writing the full name every time would be inconvenient. The `use` keyword **imports** a name into the current file, so you can then use the short form:

```php
<?php
use App\Models\User;

$user = new User();
```

Full source: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-28/en/parte-08/cap-28/listing-02.php)


The `use` at the top of the file says "when I write `User`, I mean `App\Models\User`". It is the form you will see most often: the imports gathered at the top of the file declare up front where each class comes from. Alternatively, without `use`, you can write the full name directly:

```php
<?php
$user = new \App\Models\User();
```

Full source: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-28/en/parte-08/cap-28/listing-03.php)


Note the leading backslash: it indicates the **global namespace**, the root. It is the equivalent of an absolute path starting from `/`: it tells PHP to look up the name starting from the top, regardless of the namespace you happen to be in at that moment.

## Multiple namespaces in the same file

PHP technically allows declaring multiple namespaces in a single file, but in real code this is best avoided. The universal convention is **one class per file**, with the namespace at the top:

```php
<?php
namespace App\Models;

class User
{
}
```

Full source: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-28/en/parte-08/cap-28/listing-04.php)


And the file should be saved in a path that **mirrors** the namespace:

```text
src/Models/User.php
```

Full source: [listing-05.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-28/en/parte-08/cap-28/listing-05.txt)


This correspondence between name and path is not fussiness: it is the key that makes autoload possible. If `App\Models\User` always lives in `src/Models/User.php`, a machine can compute the path from the name, without you having to tell it. That is why "one class per file" and "the path mirrors the namespace" are the two golden rules from here on.

## Manual `require`

Before we get to autoload, let us look at the direct method, the one you want to move past:

```php
<?php
require __DIR__ . "/src/Models/User.php";
require __DIR__ . "/src/Controllers/UserController.php";
```

Full source: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-28/en/parte-08/cap-28/listing-06.php)


It works, but it does not scale: every new class requires a new `require` line, and in a serious project there are hundreds. Worse still is the **order**: if `UserController` uses `User` but its `require` comes first, the application fails because the dependency is not loaded yet. You end up hand-managing a dependency graph that grows with every class — exactly the kind of tedious, fragile work a machine should be doing for you.

## `spl_autoload_register()`

The idea of autoload is to flip the logic around: instead of loading everything in advance, you register a function that PHP calls **only when needed**, at the exact moment it meets a class not yet loaded.

```php
<?php
spl_autoload_register(function (string $class): void {
    $prefix = "App\\";
    $baseDir = __DIR__ . "/src/";

    if (!str_starts_with($class, $prefix)) {
        return;
    }

    $relativeClass = substr($class, strlen($prefix));
    $file = $baseDir . str_replace("\\", "/", $relativeClass) . ".php";

    if (is_file($file)) {
        require $file;
    }
});
```

Full source: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-28/en/parte-08/cap-28/listing-07.php)


Follow the function's logic, because it is the whole story of autoload in a few lines. When you write `new App\Models\User()` and that class is not loaded, PHP passes the string `"App\Models\User"` to this function. It checks that the name starts with the prefix `App\` (otherwise it is none of its business and returns), strips the prefix, replaces the backslashes with slashes — turning the namespace into a path — and adds `.php`. The result: `App\Models\User` becomes `src/Models/User.php`, which gets included. Classes are thus loaded **on demand**, one at a time, only the ones actually used. And the ordering problem disappears: there is no longer an order to respect, each class arrives the moment you name it. This name-to-path convention is exactly the basis of the **PSR-4** standard that Composer implements (Chapter 29).

## Autoload and paths

A very common mistake in hand-written autoloaders is to build paths relative to the folder from which the script is launched, instead of relative to the autoloader file. The solution is `__DIR__`:

```php
<?php
$baseDir = __DIR__ . "/src/";
```

Full source: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-28/en/parte-08/cap-28/listing-08.php)


`__DIR__` is the magic constant that holds the folder of the file **in which it is written**, not the current execution folder. By anchoring paths to `__DIR__`, the autoloader works the same whether you launch the script from the project root, from a subfolder, or from a cron job: it no longer depends on *where* it is run. It is a small discipline that avoids one of the most common and frustrating causes of "file not found".

## Namespaces and functions

One last pitfall concerns name resolution. When you are inside a namespace, a name without a backslash is looked up **first** in the current namespace. That is fine for your own classes, but PHP's built-in classes (`DateTimeImmutable`, `InvalidArgumentException`) live in the global space: inside `App\Models`, writing `new DateTimeImmutable()` makes PHP look for a nonexistent `App\Models\DateTimeImmutable`. There are two solutions. The first is to import them at the top of the file:

```php
<?php
use DateTimeImmutable;
use InvalidArgumentException;
```

Full source: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-28/en/parte-08/cap-28/listing-09.php)


The second is to prefix them with the backslash that anchors them to the global root:

```php
<?php
$date = new \DateTimeImmutable();
```

Full source: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-28/en/parte-08/cap-28/listing-10.php)


Both work; the first is more readable because it gathers all dependencies, system ones included, at the top of the file. The underlying message is that, inside a namespace, global names must be made explicit — a detail that explains quite a few apparently mysterious "class not found" errors.

## In summary

Namespaces give classes **complete, orderly names**, eliminating collisions between different libraries; autoload eliminates manual `require`s by automatically linking the class name to the path of its file, provided you follow the two conventions — one class per file, a path that mirrors the namespace. In modern projects you will almost never write an autoloader by hand: Composer generates it, and we will see it in the next chapter. But having understood the mechanism here, in a function of a few lines, puts you in a position to resolve "class not found" errors instead of suffering them — because you know exactly from which name PHP computed which path, and where it went looking.
