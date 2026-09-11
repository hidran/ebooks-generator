# 10. The functions

Up to this point we have written scripts that execute statements one after another, and we have learned to control their flow with conditions and loops. However, an essential ingredient of any language is missing: the way to **group a block of instructions under a name** and reuse it as many times as needed, without copying and pasting the same code. This tool is the **function**, and it is the heart of this chapter.

Functions are very important in PHP as in many other languages. We'll start from the basics - what a function is, how to declare it, how to pass data to it and how to get a result back - and we'll get to the new features of modern PHP: the type declaration introduced with PHP 7, anonymous functions and arrow functions, variable parameters, named arguments and union types of PHP 8. It's a substantial chapter, but each paragraph adds a piece: in the end you'll have everything you need to write reusable and well-typed code. For the examples you just need a workbook with a file (for example `functions.php`) to be executed from the command line with `php functions.php`, or served by the integrated server that we learned to start in the previous chapters.

## What is a function

A **function** is a construct that allows us to collect within it a block of instructions to carry out a specific operation. It can receive one or more **parameters** as input and can return a value on output, or return nothing. In PHP there is no separate concept of "procedure" that we find in other languages: a procedure is simply a function that does not return any value.

The name of a function must follow the same rules as names (the "labels") in PHP: it begins with a letter or an underscore, followed by letters, numbers, or underscores. Unlike variable names, a function name is **not case sensitive**. The declaration is always preceded by the keyword `function`.

It is worth keeping in mind some characteristics of functions in PHP right away:

- They can be **called even before their definition** in the file, except when the definition is enclosed within a condition (for example a `if`): in that case the function exists only after that branch has been executed.
- They can be **nested**, but the internal function does not exist until the external one containing it is called.
- They have **global visibility**: once defined, they can be called from anywhere in the script.
- They can have variable parameters and default value parameters, and can be called **recursively** (i.e. call themselves).

Let's get straight to practice.

## Declare a function

We create a function when PHP does not already provide one that meets our needs. We have already used built-in functions like `isset()` to check if a variable is set or `empty()` to check if it is empty; now let's learn to write our own. The typical case is this: there are lines of code that we repeat continuously and, instead of copying and pasting, we enclose them in a function and execute it every time we need it.

### The basic syntax

To declare a function you need, at a minimum, the keyword `function`, a **name**, parentheses and curly braces. The name is essential: without it we wouldn't know how to invoke the function. By convention — and depending on the framework you are working with — function names begin with a lowercase letter and, if composed of multiple words, use the **camelCase** notation (each subsequent word begins with a capital letter).

Let's write a function that always displays a greeting:

```php
<?php

function sayHello()
{
    echo 'Hello world';
}
```

Full source: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-01.php)


Between the braces is the **body** of the function: all the instructions we want to execute, line by line. To execute the function just **invoke it**, i.e. write its name followed by round brackets (empty, because this function does not receive any parameters):

```php
sayHello(); // Hello world
```

Full source: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-02.php)


The body could also be empty: in that case the function is completely legitimate but it produces no effect when we call it.

### Run the script
We can run the script in multiple ways. The most convenient, when we output pure PHP without HTML, is the **command line**: we open the terminal (even the one integrated into the editor) and — given that `php` must be in the PATH, as we configured in the installation chapter — we launch:

```bash
php functions.php
```

Full source: [listing-03.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-03.sh)


and we see `Hello world` appear. Alternatively, if we want to run it via a server in the browser, we start the integrated server by indicating a free port:

```bash
php -S localhost:4000 functions.php
```

Full source: [listing-04.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-04.sh)


Editors like Visual Studio Code and PhpStorm also offer a button to run the script or start the integrated server without going through the terminal: any way is fine, the important thing is to be able to run the file. As long as we work with pure PHP it is better to stay on the command line, so we don't have to constantly switch between editor and browser.

### Assign a function to a variable

There is a second way to define a function: **assign its body to a variable**. Instead of the name we write the name of the variable, the equal and then `function`:

```php
$sayHi = function () {
    echo 'Hey';
};
```

Full source: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-05.php)


Note the final **semicolon**: here we are not declaring a named function, but assigning a value to a variable, so the statement must be closed like any other assignment (the editor tells us if we forget it). To execute it we use the name of the variable followed by parentheses:

```php
$sayHi(); // Hey
```

Full source: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-06.php)


The syntax is the same as a normal function, only the `$` in front of the name changes. However, there is a **fundamental difference**. A named function can also be called *before* its definition in the file:

```php
sayHello();      // works, even though sayHello() is defined later

function sayHello()
{
    echo 'Hello world';
}
```

Full source: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-07.php)


A function assigned to a variable, however, **cannot be called before the assignment**: if we try, PHP raises an error, because at that point the variable does not yet exist. The rule is intuitive: the named function is "seen" by PHP throughout the script, while the variable comes to life only when we assign the function to it.

So what's the point of putting a function in a variable? The reason is that in PHP a function is a **first class citizen**: we can pass it as an argument to another function and execute it elsewhere. Functions assigned to variables (which are actually instances of an internal class, `Closure`) are the tool with which we will do this, as we will see in the paragraphs on anonymous functions.

## Parameters and arguments

A function becomes really useful when we pass data to it. Inside the round brackets we can declare one or more **parameters**: they are like variables that the function expects to receive. Let's change the greeting to accept a name:

```php
<?php

function sayHello($name)
{
    echo "Hello $name";
}
```

Full source: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-08.php)


It is important to distinguish two terms that are often confused:

- the **parameter** is the variable we declare when we *write* the function (`$name` above);
- the **argument** is the concrete value we pass when we *call* the function.

So, in `sayHello('Jane')`, `$name` is the parameter and `'Jane'` is the argument that we pass to it.

### Parameters with default value

A parameter can have a **default value**, used when the function caller does not pass any arguments:

```php
function sayHello($name = 'World')
{
    echo "Hello $name";
}

sayHello();        // Hello World
sayHello('Jane');  // Hello Jane
```

Full source: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-09.php)


If we pass nothing, `$name` is `'World'`; if we pass an argument, that replaces the default.

### Multiple parameters and argument order

When there are more than one parameters, we must **respect their order** when calling, otherwise the values end up in the wrong parameters. Let's write a function that displays a person's full name:

```php
function getFullName($name, $surname)
{
    echo "Full name is $name $surname";
}

getFullName('Jane', 'Arias'); // Full name is Jane Arias
```

Full source: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-10.php)


If these parameters are **required** (do not have a default value) and we do not pass them, PHP raises an `ArgumentCountError`, signaling that an argument is missing. Here is already the usefulness of the functions: without them, to show more complete names we would have to repeat the same `echo` for each person; with the function we call the same code passing different data — very convenient when that data arrives, for example, from a database.

### Declare the type of parameters and strict_types
The editor, when we write a function, often tells us that we are not indicating either the type of the parameters or the type of return. Starting from PHP 7 we can declare them, and it is convenient to do so because it makes the code more secure and readable. We indicate the type by writing it **before** the parameter:

```php
function getFullName(string $name, string $surname)
{
    echo "Full name is $name $surname";
}
```

Full source: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-11.php)


Be careful, though: by default PHP applies the so-called **coercive mode**, that is, it tries to *convert* the argument to the declared type. If we pass the number `44` to a parameter declared `string`, PHP turns it into a string without protesting. If we want the types to be verified rigorously — without any conversion — we must put the directive at the top of the file, **as the very first line**:

```php
<?php

declare(strict_types=1);
```

Full source: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-12.php)


With `strict_types=1`, passing a number where a string is required generates an `TypeError`. The advantage is twofold: on the one hand PHP blocks the error at runtime, on the other the editor already reports it to us while we write, before even executing the code. My advice, from daily experience, is to always put `declare(strict_types=1)` at the head of the files: typing makes sense precisely when the types are truly respected.

### Named argument and default values

When there are many parameters, remembering their order becomes inconvenient and you risk making mistakes. PHP 8 comes to our aid with **named arguments**: we can pass the arguments by indicating the name of the parameter (without the `$`), followed by the colon and the value, **in any order**. Let's add a third parameter, age, to the function:

```php
function getFullName(string $name, string $surname, int $age)
{
    echo "$name $surname, $age years old";
}

// with named arguments, order does not matter:
getFullName(age: 45, name: 'Mary', surname: 'Smith');
```

Full source: [listing-13.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-13.php)


We will return to named arguments in a dedicated paragraph later. For now we need to clarify a rule about default values. If a parameter with a default value comes *before* a mandatory parameter, that default effectively becomes useless: since we still have to pass the next argument, we are forced to also pass the one that would have the default. Indeed, PHP 8 reports it as **deprecated** to declare an optional parameter before a mandatory one. The rule of thumb is clear: **parameters with default values ​​should be placed at the bottom** of the list. Named arguments alleviate the problem (they allow you to skip intermediate parameters that have a default), but the convention remains valid.

## Return values

Until now our functions showed something on the screen but returned nothing. The most interesting case is the one in which the function **calculates a result and delivers it to us**, so we can capture it, print it or pass it to other operations.

### return and the return type

To return a value we use the `return` keyword. Let's write a simple function that adds two integers:

```php
<?php

declare(strict_types=1);

function sum(int $a, int $b): int
{
    return $a + $b;
}
```

Full source: [listing-14.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-14.php)


Two details. First: `return` interrupts the function and returns the indicated value. Second: after the round brackets we wrote `: int`, which declares the **return type**. Since we add two `int`, the function will always return an `int`; if we tried to return something different, PHP would generate an error (and the editor would warn us about it in advance).

How do we capture the result? The function, by itself, does not print anything: we must use the value it returns. We can pass it directly to `echo`, or save it in a variable:

```php
echo sum(4, 5);           // 9

$result = sum(4, 5);
echo $result;               // 9
```

Full source: [listing-15.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-15.php)


Saving the result in a variable is useful when we want to reprocess it or pass it to other functions, instead of just displaying it. If we put an `return 'a string';` inside the function before the correct `return`, with the return type `int` declared, the editor would immediately warn us of the inconsistency: this is why declaring types is so valuable.

### Returning multiple values: arrays and destructuring

In PHP a function **cannot return more than one scalar value**. If we need to return multiple results, the only way is to enclose them in an **array**. Let's write a function that, given two sides, calculates the area and perimeter of a rectangle:

```php
function calculateAreaPerimeter(int $a, int $b): array
{
    $area = $a * $b;
    $perimeter = 2 * ($a + $b);

    return [$area, $perimeter];
}
```

Full source: [listing-16.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-16.php)


The return type is now `array`. We can capture the result in a variable and inspect it with `print_r()`:

```php
$result = calculateAreaPerimeter(5, 4);
print_r($result);
// Array ( [0] => 20 [1] => 18 )
```

Full source: [listing-17.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-17.php)


In the position `0` there is the area (5 × 4 = 20), in the position `1` the perimeter (2 × 9 = 18). Even more elegant is to **destructure** the returned array directly into two distinct variables:
```php
[$area, $perimeter] = calculateAreaPerimeter(5, 6);

echo "$area\n";        // 30
echo "$perimeter\n";   // 22
```

Full source: [listing-18.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-18.php)


The same thing was once achieved with the `list()` function, which receives the array and the variables into which to distribute its values:

```php
list($a, $b) = calculateAreaPerimeter(5, 6);
echo "$a $b\n"; // 30 22
```

Full source: [listing-19.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-19.php)


The syntax with square brackets is the modern and most readable one, but it is useful to also recognize `list()` because you will encounter it in a lot of existing code.

## Typing arguments and return (PHP 7)

Let's delve deeper into the innovation that PHP 7 has brought: the **type declaration** for both the input parameters and the return value. Until PHP 5 we could only declare a class, an interface or `array` as the type of a parameter. With PHP 7 we can also use **scalar types** and other special types:

- `int` — an integer;
- `float` — a number with a decimal point;
- `string` — a string;
- `bool` — a boolean;
- `array` — an array;
- `callable` — something that can be invoked as a function (the name of a function, an anonymous function, a method, or an object with the magic method `__invoke`);
- a **class** or an **interface**.

Pay attention to the nomenclature: you must write exactly `int`, `bool`, `float`, `string`. If we wrote `integer` or `boolean`, PHP would think we were referring to a *class* with that name. Let's take the sum again:

```php
<?php

function sum(int $a, int $b): int
{
    return $a + $b;
}

echo sum(5, 5); // 10
```

Full source: [listing-20.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-20.php)


As already seen, without `declare(strict_types=1)` PHP applies the implicit conversion: if we pass the string `'5'`, it transforms it into an integer and the sum works the same. This is fine for simple conversions (string to number and vice versa), but not for ambiguous cases. If we want PHP to check the types without converting anything, we put `declare(strict_types=1)` at the head of the file: at that point passing `'10'` where we need an `int` raises an `TypeError`, and the same goes for the return type.

Let's look at some examples of non-scalar types. Let's add a third parameter of type `array`:

```php
function sum(int $a, int $b, array $c): int
{
    return $a + $b;
}

sum(5, 5, []);          // ok: empty array
sum(5, 5, 'not an array'); // TypeError: the third argument is not an array
```

Full source: [listing-21.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-21.php)


We can also declare that a parameter is of type **class**: in that case we must pass it an instance of that class (we will study classes in Part VII), otherwise we get an error. And we can declare it `callable`, which allows us to accept either the name of a function (passed as a string), an anonymous function or a variable containing an `Closure`:

```php
function run(callable $c): void
{
    $c(); // invoke what was passed to us
}

function test()
{
    echo "test\n";
}

run('test');                       // pass the name as a string
run(function () { echo "anon\n"; }); // pass an anonymous function
```

Full source: [listing-22.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-22.php)


Note the return type `void`: it indicates that the function **does not return any value**. This possibility of typing parameters and return — long absent in PHP and instead present in languages ​​such as Java or C# — is one of the most important innovations of PHP 7, and it is best to exploit it in our projects.

## Nullable parameters and null return (PHP 7.1)

Since PHP 7.1 we can declare that a parameter (or return value) of a certain type can also be **`null`**. This is done by placing a **question mark** before the type. Let's resume the sum with declared types:

```php
function sum(int $a, int $b): int
{
    return $a + $b;
}
```

Full source: [listing-23.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-23.php)


If we try to pass `null` to one of the `int` parameters, we get a `TypeError`: `null` is not an integer. To allow this, we prepend the `?`:

```php
function sum(?int $a, ?int $b): int
{
    return $a + $b;
}

$result = sum(null, null);
var_dump($result); // int(0)
```

Full source: [listing-24.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-24.php)


Now we can pass `null` without errors. Note a curious detail: the function returns `int(0)`, because PHP, adding two `null`, treats them as `0`. The return remains an `int`, so the return type `int` is respected.

Suppose instead that we want to explicitly return `null` in a certain case:

```php
function sum(?int $a, ?int $b): int
{
    if ($a === null || $b === null) {
        return null; // ERROR: the return type is int
    }

    return $a + $b;
}
```

Full source: [listing-25.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-25.php)


This raises an error, because we declared that the function returns `int`, not `null`. The solution is to also make the return type **nullable**, with the same `?`:

```php
function sum(?int $a, ?int $b): ?int
{
    if ($a === null || $b === null) {
        return null;
    }

    return $a + $b;
}
```

Full source: [listing-26.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-26.php)


One final warning. Declaring a parameter `?int` means that `null` *may* be valid, but not that it is **optional**: if we omit it altogether in the call, PHP still raises an `ArgumentCountError`. To make it truly optional we need to give it a default value:

```php
function sum(?int $a = null, ?int $b = null): ?int
{
    // ...
}

sum(); // now it is valid
```

Full source: [listing-27.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-27.php)


In summary: the `?` in front of the type (of a parameter or return) authorizes the value `null`; to make a parameter also omissible you need a default value. We will see in Chapter 32, with exceptions, how to catch errors like `ArgumentCountError` and `TypeError` in a block `try`/`catch`.

## The scope of the variables

A central issue in the use of functions is the visibility (or scope) of variables: which variables a function can see and which it cannot.

### Local variables

The basic rule is that each function creates its own **isolated environment**. The variables defined outside the function are not visible inside it, and vice versa the variables defined inside the function no longer exist once exited from it. Let's see it:

```php
<?php

$data = ['name' => 'John Doe'];

function modify()
{
    var_dump($data); // Warning: $data is not defined in here
}

modify();
```

Full source: [listing-28.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-28.php)


By running the script we get a warning: inside `modify()` the variable `$data`, although existing in the external environment, is simply not visible. PHP, inside the function, creates its own *scope* where only its local variables live and does not see anything outside.

### The global construct

How do we access, from inside a function, a variable that lives in the global environment? The global environment is everything outside the functions: the variables written directly in the script (or in an included file), but not those internal to other functions or objects. The first way is the **`global`** construct, followed by the name of the variable we want to import:

```php
$object = 'John';

function modify()
{
    global $object;

    var_dump($object); // now we see 'John'
    $object = 'Jane';  // and we can also modify it
}

modify();
var_dump($object); // 'Jane': the change is reflected outside!
```

Full source: [listing-29.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-29.php)


With `global $object` we are making *reference* to the global variable: not only do we read it, but if we modify it inside the function **we also modify the external one**, because it is the same variable by reference. The same goes for arrays and scalar values: imported with `global`, any global variable can be read and overwritten from within the function. Always keep this in mind, because it is an easy side effect to forget.

### The superglobal $GLOBALS

The second way to access global variables is the **superglobal** `$GLOBALS`. Superglobals are special arrays that PHP makes available everywhere in the script — we'll study them in detail in Chapter 13 (`$_GET`, `$_POST`, `$_SESSION`, `$_SERVER`, `$_REQUEST` and others). `$GLOBALS` is a large array containing **all global variables**, indexed by name:

```php
$name = 'John Doe';

function modify()
{
    $GLOBALS['name'] = 'Jane'; // access the global through its key
}

modify();
echo $GLOBALS['name']; // Jane
```

Full source: [listing-30.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-30.php)


The array key is the variable name (without `$`). There is an important point to understand: if inside a function we declare `global $val` and then try to use a local parameter with the same name, **the global reference takes precedence** and the local value is ignored. By removing the `global`, the local variable would become visible again. In other words, `global` really "imports" the external variable into the scope of the function, putting it in place of any local homonyms.

In daily practice, the use of `global` is not recommended — it introduces hidden dependencies and makes the code more difficult to follow — but it is essential to know it to understand how scope works in PHP. The rule to establish is this: inside a function global variables do not exist unless we import them explicitly (with `global` or through `$GLOBALS`), or unless we pass them as arguments. This last route — passing the data as parameters — is almost always the best choice.

## Anonymous functions and variable functions

We anticipated that a function can be assigned to a variable. An unnamed function is called an **anonymous function** (or *closure*), and when we assign it to a variable we talk about a **variable function**. Internally PHP creates an instance of its class `Closure` and assigns it to the variable.

### Assign an anonymous function to a variable

```php
<?php

$sum = function ($a, $b) {
    return $a + $b;
};

echo $sum(2, 3); // 5
```

Full source: [listing-31.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-31.php)


Always remember the **semicolon** after the closing brace: it's an assignment, not a function declaration. To invoke it we use the variable name and round brackets, exactly like a normal function. As already seen for variable functions, we cannot call it before having defined it: the variable `$sum` does not exist until we assign closure to it.
### Pass a function as an argument

The great thing about anonymous functions is that you can pass them as arguments to other functions. A function that receives an `callable` parameter can execute it inside itself:

```php
function test(callable $func)
{
    echo $func(5, 5);
}

test($sum); // 10
```

Full source: [listing-32.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-32.php)


If we declare the parameter `callable` (or, more specifically, `Closure`) and try to pass it a number, we get an error: PHP is expecting something callable. This mechanism — passing one function to another function — is the basis of many array operations, which we'll see right away.

## Anonymous functions with arrays

Many built-in PHP functions that work on arrays take a **callback function** as an argument: they apply it to each element and return a result. The most used are `array_map`, `array_filter` and `array_walk`. Let's focus on `array_map`, which takes an array and a function, applies the function to each element, and **returns a new array** with the results.

### array_map

Suppose you have a list of numbers and you want a copy of them with each value doubled. With an `foreach` loop we would do this:

```php
<?php

$numbers = [1, 2, 3, 4, 5];
$doubleArray = [];

foreach ($numbers as $val) {
    $doubleArray[] = $val * 2;
}

print_r($doubleArray);
// Array ( [0] => 2 [1] => 4 [2] => 6 [3] => 8 [4] => 10 )
```

Full source: [listing-33.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-33.php)


With `array_map` it is much more concise. As a callback we can pass the **name of one of our functions** (as a string). Let's create a function that doubles a value — we call it `doubleVal` so as not to overlap with `doubleval()`, which is a native PHP function:

```php
function doubleVal($val)
{
    return $val * 2;
}

$double = array_map('doubleVal', $numbers);
print_r($double);
// Array ( [0] => 2 [1] => 4 [2] => 6 [3] => 8 [4] => 10 )
```

Full source: [listing-34.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-34.php)


`array_map` takes each element of `$numbers`, passes it to `doubleVal`, collects the returned values into a new array and delivers it to us. Since it returns an array, we capture the result in a variable.

### Callbacks, closures and native functions

The first argument of `array_map` can be any *callable*. In addition to the name of one of our functions, we can pass the name of a **native function** of PHP. For example `floor()`, which truncates a decimal number to its lower integer:

```php
$numbers = [6.4, 3.2, 5.7];
$truncated = array_map('floor', $numbers);
print_r($truncated);
// Array ( [0] => 6 [1] => 3 [2] => 5 )
```

Full source: [listing-35.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-35.php)


But often we only need the function once, for that one operation: in these cases it is useless to declare it separately. We can pass it **inline** as an anonymous function:

```php
$double = array_map(function ($val) {
    return $val * 2;
}, $numbers);
```

Full source: [listing-36.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-36.php)


The anonymous function receives the value of each element and returns the desired result. It is the idiomatic way when the logic is specific to that call and will not be reused elsewhere. The rule of thumb I use: if the function is only needed there, write it anonymously inline; if you plan to reuse it in multiple places, declare it as an actual function with a name, so it's accessible everywhere. And if the logic is very short — just one line — there is an even more compact form, which we see now.

## The arrow functions (PHP 7.4)

PHP 7.4 introduced **arrow functions**, a shorthand syntax for anonymous functions that return the result of a single expression. They are very convenient precisely in cases like `array_map`, where a parameter is a function that must transform a value.

### The syntax with fn

Instead of the word `function` we write **`fn`**, followed by the parameters in brackets, the **arrow** `=>` and immediately by the expression to return. There are no braces and **you don't need** the word `return`: the value after the arrow is what is returned.

```php
$double = array_map(fn($val) => $val * 2, $numbers);
```

Full source: [listing-37.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-37.php)


This line does exactly the same as the anonymous function in the previous paragraph, but in a much more compact way. Let's see it on an associative array, to make all values uppercase with `strtoupper()` while keeping the keys:

```php
<?php

$data = ['name' => 'john', 'surname' => 'doe', 'city' => 'london'];

$result = array_map(fn($val) => strtoupper($val), $data);
print_r($result);
// Array ( [name] => JOHN [surname] => DOE [city] => LONDON )
```

Full source: [listing-38.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-38.php)


The arrow functions must be **all on one line**: we cannot open the braces and wrap them like in JavaScript. If we need more logic than a single expression, we need to go back to the classic anonymous function.

### Scope inheritance

There is an important difference compared to traditional anonymous functions. An anonymous function, like any function, creates its own environment and **doesn't see** external variables. To use one inside a classic closure we must import it explicitly with the **`use`** keyword:

```php
$prefix = 'Mr. ';

$result = array_map(function ($val) use ($prefix) {
    return $prefix . strtoupper($val);
}, $data);
```

Full source: [listing-39.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-39.php)


Without `use ($prefix)`, the variable `$prefix` would not be visible inside the function (we could list multiple variables separated by commas). The **arrow functions**, on the other hand, **automatically inherit** the variables of the environment in which they are defined: no `use` is needed.

```php
$prefix = 'Mr. ';

$result = array_map(fn($val) => $prefix . strtoupper($val), $data);
```

Full source: [listing-40.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-40.php)


The arrow function sees `$prefix` without having to import it: it inherits the entire context in which it is executed. It's one of their most popular advantages, besides brevity.

Summarizing the scale of choice: for a single row transformation use an arrow function; if you need some multiline logic, an anonymous function with `use` where necessary; if the function is complex or reusable, extract it into a named function and pass the name as a callback — the code will be cleaner.

## The variadic functions

**variadic functions** (or *functions with variable parameters*) are functions that accept a **variable number of arguments**. They allow us to write more flexible functions, which adapt to how many arguments we receive.

### The rest parameter

The modern way is the **rest parameter**: you put **three dots** (`...`) in front of the parameter name, and we automatically get an array with all the arguments passed. Let's write a function that adds any number of values:

```php
<?php

declare(strict_types=1);

function sum(...$values)
{
    $sum = 0;

    foreach ($values as $val) {
        $sum += $val;
    }

    return $sum;
}

echo sum(1, 2, 3);       // 6
echo sum(1, 2, 3, 4, 5); // 15
```

Full source: [listing-41.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-41.php)


Inside the function, `$values` is a normal array that contains all the arguments. Before introducing the rest parameter, the same result was obtained with the **`func_get_args()`** function, which returns the array of received arguments even without declaring any parameters:

```php
function sumOld()
{
    $sum = 0;

    foreach (func_get_args() as $val) {
        $sum += $val;
    }

    return $sum;
}
```

Full source: [listing-42.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-42.php)


It is the "old" method, which I show only for completeness: today the rest parameter is clearer and more explicit, so there is no longer any reason to use `func_get_args()`.

### Type and combine parameters

We can declare the **type** of the collected arguments by placing it *before* the three dots:

```php
function sum(float ...$values): float
{
    // ...
}
```

Full source: [listing-43.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-43.php)


With `declare(strict_types=1)` active, passing a string where you need an `float` generates an error; an `int` instead is accepted because it is convertible to `float` without loss.

The rest parameter can coexist with **positional parameters** at the beginning: the first arguments end up in the "normal" parameters, all the others are captured by the variadic parameter. The rest parameter, however, must be **the last**. Let's write a function that joins multiple strings with a separator:

```php
function stringJoin(string $separator, string ...$parts): string
{
    return implode($separator, $parts);
}

echo stringJoin('-', '1', '2', '3', '4'); // 1-2-3-4
echo stringJoin('-', 'a', 'b');            // a-b
```

Full source: [listing-44.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-44.php)


The first argument (`$separator`) is required; all the others are collected in `$parts` and passed to `implode()`, the native function that joins the elements of an array into a string. Note that PHP 8 allows the **trailing comma** also in the parameter and argument list: it's convenient because adding a trailing element doesn't require touching the previous line.

### A practical example: a calculator

Let's put together what we have seen by building a small calculator: the first parameter is the operation to be performed, the remaining are the operands.

```php
<?php

declare(strict_types=1);

function calc(string $operation, int ...$values): float
{
    $result = $values[0];
    $total = count($values);

    for ($i = 1; $i < $total; $i++) {
        switch ($operation) {
            case '+':
                $result += $values[$i];
                break;
            case '-':
                $result -= $values[$i];
                break;
            case '*':
                $result *= $values[$i];
                break;
            case '/':
                if ($values[$i] !== 0) {
                    $result /= $values[$i];
                }
                break;
        }
    }

    return $result;
}

echo calc('*', 3, 4, 5); // 60
echo calc('+', 3, 4, 5); // 12
echo calc('/', 3, 4, 5); // 0.15
```

Full source: [listing-45.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-45.php)


Some notable choices. We initialize `$result` with the first value (`$values[0]`) and start the loop `for` from `1`, because the first operand is already the starting point. We calculate `count($values)` **only once** outside the loop, saving it in `$total`, instead of calling it every loop. For division we check that the divisor is not `0`, skipping the operation in that case (with multiplication it is not needed: zero is a legitimate operand). The return type is `float` because a division can produce a decimal. We use the **compound operators** (`+=`, `-=`, `*=`, `/=`) seen in Chapter 8 to make the code more concise.

The most important thing to remember: the three dots capture all past parameters; we can type them, and we can prepend other positional parameters — the first arguments end up in those parameters, the rest in the variadic.

## Named arguments (PHP 8)
With PHP 8 we can pass the arguments of a function by indicating its **name**, as we anticipated when talking about parameters. It is one of the most appreciated innovations: it makes calls more readable and frees us from the obligation to remember the exact order of parameters.

The syntax is: parameter name (without `$`), colon, value. Let's take a function with three parameters:

```php
function sum(int $a, int $b, callable $c)
{
    $c();
    return $a + $b;
}

// pass the arguments by name, in the order we prefer:
sum(
    b: 5,
    a: 10,
    c: fn() => print("calculation in progress\n"),
);
```

Full source: [listing-46.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-46.php)


The code works perfectly, even if we passed `b` before `a`: with named arguments **the declaration order must not be respected**. However, the rules regarding mandatory parameters remain valid: if we omit one that the function expects, PHP reports that it is missing (`ArgumentCountError`).

Named arguments also work with **native functions**. For example `strstr($haystack, $needle)`, which searches for a substring and returns the portion starting from the first occurrence; its parameters are called `$haystack` (the string to search in) and `$needle` (what to search for):

```php
$result = strstr(needle: 'john', haystack: 'sono john doe');
var_dump($result); // string(10) "john doe"
```

Full source: [listing-47.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-47.php)


We can also **mix** positional and noun arguments, but with one precise rule: **a positional argument cannot come after a noun argument**. Once we start using names, all subsequent arguments must have the name:

```php
sum(10, c: fn() => null, b: 5);      // ok: the positional argument is first
// sum(a: 10, 5, ...);               // ERROR: positional after a named argument
```

Full source: [listing-48.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-48.php)


Named arguments are very convenient when a function has many parameters and we want to pass only a few of them, or when we want to make clear, at a glance, the meaning of each value in the call — a bit like Python does. They are not mandatory, but using them where clarity is needed is a good habit: they eliminate the class of bugs that arise from passing parameters in the wrong order.

## Union types (PHP 8)

The latest innovation in this chapter, also in PHP 8, are the **union types**: the possibility of specifying **more than one type** for a parameter or for the return. They are written by listing the types separated by the **vertical bar** `|` (the *pipe* character).

Let's take the sum again. If we declare it with parameters `int` but we also want to accept decimal numbers, the editor tells us that passing `5.5` is a type error. The solution is a union type `int|float`, both for the parameters and for the return:

```php
<?php

function sum(int|float $a, int|float $b): int|float
{
    return $a + $b;
}

echo sum(5.5, 4); // 9.5
```

Full source: [listing-49.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-49.php)


Now the function accepts integers and decimals interchangeably, and can return one or the other. We can combine any of the types seen so far: scalars, `array`, classes, interfaces, `callable`. There is also the special type **`mixed`**, which means "of any type": it is the widest possible, and using it as a type is equivalent to not placing any constraints.

`null` can also be part of a union type:

```php
function sum(int|float $a, int|float $b): int|float|null
{
    // ...
}
```

Full source: [listing-50.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-50.php)


However, when the union is between **a single type and `null`**, the writing `?tipo` that we saw for nullable parameters is an equivalent shortcut: `?float` is exactly `float|null`. To join `null` to multiple types, however, we must use the extended form `float|int|null`.

There is one type that **cannot** appear in a union type: **`void`**. `void` indicates the total absence of a return value (the function does not return anything), so it is incompatible with any other type: if we declare `void`, we must completely remove the `return`, and it is conceptually different from returning `null`.

The union types are also valid for the **methods** of the classes and, again from PHP 8, for the **typing of the properties** — something that was not possible before. More on this in Part VII, but it's worth anticipating:

```php
class Persona
{
    public string|int $name;
}
```

Full source: [listing-51.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-10/en/parte-03/cap-10/listing-51.php)


An interesting case is `string|Stringable`: it means that the value can be a string or an **object** that implements the magic method `__toString()` (therefore convertible to a string). We will see the magical methods in the object part; for now, suffice it to say that union types give us much more expressive type checking than before.

## In summary
- A **function** groups a block of instructions under a name and is declared with `function`, parentheses and braces; it is invoked by writing the name followed by the roundels. The name is not case sensitive.
- A function can be **assigned to a variable** (`$fn = function () { ... };`): unlike the named function, it cannot be called before its definition.
- The **parameters** are the variables declared in the function; **arguments** are the values ​​we pass to the call. Parameters can have a **default value**, which should be placed at the bottom of the list.
- From PHP 7 we can declare the **type** of parameters and return (`int`, `float`, `string`, `bool`, `array`, `callable`, classes, `void`); with `declare(strict_types=1)` at the top of the file PHP checks types without implicit conversions.
- A value is returned with **`return`**; to return more than one we use an **array**, which we can then **destructure** with `[$a, $b] = ...` or with `list()`.
- Since PHP 7.1 the **`?`** in front of the type makes a parameter or return **nullable**; to make a parameter also omissible you need a default value.
- Each function has its own **scope**: external variables are not visible inside it, unless imported with **`global`** or via the superglobal **`$GLOBALS`** (or passed as arguments, preferable choice).
- **anonymous functions** (closure) are assigned to variables and passed as `callable` to other functions; they are the basis of callbacks for arrays (`array_map`, `array_filter`, `array_walk`).
- **arrow functions** (PHP 7.4) — `fn($x) => expression` — are a compact single-line form that **automatically inherits** the outer scope, without the need for `use`.
- The **variadic functions** collect a variable number of arguments with the rest parameter `...$values` (typeable and combinable with positional parameters), replacing the old `func_get_args()`.
- **named arguments** (PHP 8) allow you to pass arguments by name (`name: value`) in any order; a positional argument cannot follow one by name.
- **union types** (PHP 8) — `int|float`, `float|int|null`, `mixed` — declare multiple allowed types for a parameter, return, or property; `void` cannot be part of a union.
