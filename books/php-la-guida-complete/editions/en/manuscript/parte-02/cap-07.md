# 7. Variables, types and constants

In the previous chapter we saw how PHP executes code and how it mixes with HTML. In this chapter we enter the heart of the language: the **variables**, i.e. the containers with which we store and reuse data, and the fundamental **types** that this data can have — numbers, Booleans, strings and arrays. We will close with **constants**, the values ​​that must not change during execution, and with three native functions — `isset()`, `empty()` and `is_null()` — which we will continuously use to check the state of a variable.

They are the foundation of everything we will build in the rest of the book: the forms, the database queries, the projects of the final parts continuously manipulate variables, strings and arrays. It is worth giving this chapter all the attention it deserves, also because PHP has some behaviors - automatic type conversion, strings as sequences of bytes, truncation of array keys - which surprise those coming from other languages ​​and which are the source of classic bugs.

## What is a variable

### From expressions to variables

In PHP, as in other languages, we can write **literal expressions**. An expression is like when we did math: `2 + 2`. Each statement must be ended with a semicolon, to tell PHP where it ends:

```php
<?php

2 + 2;
```

Full source: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-01.php)


If we run this code from the command line with `php index.php`, nothing appears — but not even an error. PHP evaluates the expression, gets `4`, and throws it away, because we didn't ask it to show it. To output the result to the console we use the `echo` construct, which means "show this expression on the screen (or on the console)":

```php
<?php

echo (2 + 2);   // 4
```

Full source: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-02.php)


The parentheses here only serve to delimit the expression, as in mathematics. A literal expression can also be a **string**, that is, any set of characters — a phrase, a name — or a number:

```php
<?php

'Hello world';   // expression evaluated, but no output
3.1415;          // same

echo 'Hello world';   // Hello world
echo 3.1415;          // 3.1415
```

Full source: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-03.php)


As well as from the console, you can see the result in the browser: if you use VS Code with the PHP Server extension that we configured in Chapter 5, just right-click on the file and "PHP Server: Serve project" to open the page in the browser. In this chapter we will almost always use the console, reserving the browser for cases where the output contains HTML.

Now, suppose you want to use the value 3.1415 — a reduced pi — to calculate the area of ​​a circle or the volume of a cylinder. How do we store it somewhere, so we can reuse it in different expressions? That's exactly what variables are for.

A **variable** is nothing more than an area of ​​memory (in the computer's RAM, or even on disk, depending on how the system manages it) where we store data, with a name that acts as a reference label. The data can be anything: a number, a string, a single character, a list of cities, a record read from the database, the contents of a file, even a resource such as a pointer to an open file or a database connection. We put all this in a variable so we can recycle it as many times as we want.

### Declaring a variable and naming conventions

In PHP a variable always begins with the **dollar** symbol (`$`): it is the standard of the language. After the dollar, the name:

- it can begin with a **letter** or with an **underscore** (`_`, the underscore);
- can continue with letters, numbers and underscores;
- **cannot** start with a number and **cannot** contain spaces.

```php
<?php

$name = 'John';      // valid
$_name = 'John';     // valid
$name2 = 'John';     // valid
// $2name = 'John';  // ERROR: it cannot start with a number
// $last name = '...'; // ERROR: no spaces
```

Full source: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-04.php)


To assign a value we use the **equals** sign (`=`), just like in mathematics we assigned a value to *x* or *y*. Strings must be enclosed in single quotes or quotation marks (we will see the difference shortly), numbers must not:

```php
<?php

$lastName = 'Arias';
$name = 'John';
$age = 50;
$cities = ['Edinburgh', 'London', 'Naples'];   // an array: we will study it shortly
```

Full source: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-05.php)


A few words about conventions. The computer doesn't care what you call a variable: you could call it `$a234` and to it it would just be a pointer to an area of ​​memory. But the code is read by programmers, and whoever reads it must understand what he is doing: always use **talking names**, which give information. I usually use names in English, and I follow the **camelCase** convention: when the name is made up of two words, the second begins with a capital letter, as in `$lastName`. Choose one convention and stick to it throughout the project.

One last important observation: PHP is a **dynamically typing** language. In a variable that contains a number we can easily assign a string after it:

```php
<?php

$r = 20;
$r = 'a letter';   // valid in PHP
```

Full source: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-06.php)


In languages like Java or C# this is not possible: once you declare a numeric variable, you cannot assign a string to it. In PHP yes. From PHP 7 onwards we can still declare the types of function parameters and force PHP to check them — we'll see this in Chapter 10 when we talk about functions.

### A practical example: the area of the circle

Let's put together what we've seen and calculate the area of a circle. We need pi (for now in a variable: later in this chapter we will discover that it is the perfect candidate for a constant) and the radius:

```php
<?php

$pi = 3.1415;
$r = 20;

$area = $pi * $r * $r;

echo "The area is $area\n";
```

Full source: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-07.php)


To multiply, in almost all programming languages the **asterisk** (`*`) is used. There is also a function to square, but for now let's multiply the radius by itself. The advantage is obvious: instead of copying `3.1415` every time, we use `$pi`; and imagine that the ray comes from a form filled out by the user — we receive the data, put it in `$r` and apply the formula.

Notice two things in the final `echo`. First: inside the **quotation marks** we can write the name of the variable directly and PHP replaces it with its value (no with single quotes - we'll come back to it in the paragraph on strings). Second: `\n` is the new line character, used in almost all languages ​​— PHP, Java, C# — to wrap on the console.

However, if you open the same script in your browser, you find that the text does not wrap. Looking at the source of the page (right click → View source) the newline is there, but the browser does not render it: for HTML a newline in the source is just a space. To wrap in the browser you need an HTML tag, such as a paragraph — and we already know from Chapter 6 that we can mix HTML and PHP:

```php
<?php

echo '<p>The perimeter is ' . (2 * $pi * $r) . "</p>\n";
```

Full source: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-08.php)


Here we also reused `$pi` and `$r` a second time, concatenating the result to the string with the **dot** (`.`) — the concatenation operator that we'll learn more about shortly. Variables can be reused as many times as we want, and later we will see how to pass them as parameters to functions.

## Numbers: integer and float

PHP has two numeric types: **integer** (integer numbers) and **float** (floating point numbers). Creating a number is very simple: just assign it to a variable.

```php
<?php

$dec = 255;
var_dump($dec);   // int(255)
```

Full source: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-09.php)


Here we encounter a very precious native function: **`var_dump()`**. We pass her a variable between parentheses and she shows us the **type** and **value**: in this case `int(255)`. We will use it continuously to inspect variables.

### Integers, numeric strings and automatic conversions

What happens if we put the number in quotes?

```php
<?php

$dec = '255';
var_dump($dec);        // string(3) "255"

var_dump($dec * 4);    // int(1020)
var_dump($dec * 4.4);  // float(1122)
```

Full source: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-10.php)


In quotes, `255` is a three-byte **string**. But if we multiply it by 4, we get `int(1020)`: PHP automatically converts — the **casting** — the contents of the string into a number, because the multiplication operator expects numbers. PHP reads the string from the beginning: if it begins with a number (possibly preceded by the sign `+` or `-`), it continues until the number ends and converts that part. With `'255aa' * 4` it would still get `1020`, stopping at 5 — although recent versions of PHP issue a warning when the string is not a "well-formed" number. The same goes if we multiply by a float like `4.4`: the result becomes `float`.
This flexibility is convenient, but a tip from experience: by convention, and for correctness, if you know a priori that a value is a number represent it as a number, without superscripts. We respect types even if PHP does the conversion for us. And remember that from PHP 7 we can declare that a function parameter must be `int`: in that case the verification becomes rigorous.

### Represent integers in other bases

Integers are not just written in base ten. PHP also allows us to represent them in **octal** (base 8), **hexadecimal** (base 16) and **binary** (base 2):

```php
<?php

$oct = 0124;         // octal: 0 prefix
$hex = 0xDE;         // hexadecimal: 0x prefix
$bin = 0b11111111;   // binary: 0b prefix

var_dump($oct);   // int(84)
var_dump($hex);   // int(222)
var_dump($bin);   // int(255)
```

Full source: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-11.php)


Pay attention to the prefixes: a leading **zero** for octal, **`0x`** for hexadecimal, **`0b`** for binary (the zero, not the letter "o": it's a classic typo).

How do you arrive at those decimal values? It's basic math, but let's review it. In base 8 the digits go from 0 to 7, and are added starting from the right, multiplying each digit by the power of 8 corresponding to its position:

```text
0124 (octal) = 4×8⁰ + 2×8¹ + 1×8² = 4 + 16 + 64 = 84
```

Full source: [listing-12.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-12.txt)


In base 16 the digits go from 0 to 9 and then continue with the letters: A is equal to 10, B 11, C 12, D 13, E 14, F 15. The procedure is the same, with the powers of 16:

```text
0xDE = 14×16⁰ + 13×16¹ = 14 + 208 = 222
```

Full source: [listing-13.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-13.txt)


Binary, finally, is the basis of computers: only 0 and 1, and going to the left the weights double — 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024 and so on. Eight digit 1s equals exactly 255.

The important thing to understand is that the base is just a **representation**: internally PHP always uses the same number, and when we display it with `var_dump()` or `echo` it automatically converts it to base ten. We can also mix representations in operations:

```php
<?php

$result = $dec + $hex;   // 255 + 222
echo $result;            // 477
```

Full source: [listing-14.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-14.php)


### Floats and bounds of integers

Normally we will use decimal numbers, positive or negative, and decimal numbers — where the decimal point is the **period**:

```php
<?php

$negative = -255;
$float = 123.45;
var_dump($float);   // float(123.45)
```

Full source: [listing-15.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-15.php)


A peculiarity: when we use **division**, the result is generally a float value; only if both operands are integers and the division is exact does PHP return an integer. For the rest, the same operators of basic algebra apply, which we will study in detail in Chapter 8.

As for limits: the maximum size of an integer depends on the **platform**. On 32-bit systems the maximum is about 2.1 billion (2³¹ − 1); on 64-bit systems — now the standard on modern Linux, macOS, and Windows — it is dramatically larger. We are well covered for everyday mathematical operations. Floats follow the **IEEE 754** standard, with the typical floating point roundings: for the vast majority of cases this is fine, and if you need calculations of arbitrary precision PHP provides dedicated mathematical libraries (such as BCMath), which are outside of this book.

## The boolean type

The **boolean** (or boolean) type comes from Boolean algebra: it can only take two values, **`true`** (true) and **`false`** (false). In PHP these two constants are *case-insensitive* — you can write `true`, `True` or `TRUE` — and their typical use is in checks and loops: "if this condition is true, do this; otherwise, do that".

However, the way PHP handles booleans is different from languages ​​like Java or C#, where the boolean type is rigid and cannot be compared with other types: in PHP **any value can be evaluated as boolean**, via automatic conversion. And this is where you need to be very careful.

### Values considered false

In PHP only these values are considered false (*falsy*):

| Value | Notes |
|---|---|
| `false` | the Boolean constant |
| `0` | the integer zero (also `-0`) |
| `0.0` | the zero float (also `-0.0`) |
| `''` | the empty string |
| `'0'` | the string containing zero — be careful, it confuses many! |
| `[]` | an empty array |
| `null` | the null value |
| empty XML element | a SimpleXML object created from an empty element (we'll look at XML in Chapter 16) |
**Anything else is true**: a non-empty string, a non-zero number, an array with at least one element. I recommend you keep this table for reference — you can also paste it into a comment in your code. By the way: for multi-line comments use `/*` to open and `*/` to close; everything in between is ignored by the interpreter, which doesn't even parse it.

### Boolean in practice: expressions and cast

Declaring a Boolean variable is straightforward. Let's use it immediately in a condition - we will study the construct `if`/`else` in depth in Chapter 9, but the meaning is intuitive: *if* the condition in brackets is true execute the first block between braces, *otherwise* (else) the second:

```php
<?php

$verify = false;

if ($verify == true) {
    echo 'Verify is true';
} else {
    echo 'Verify is false';
}
// Output: Verify is false

var_dump($verify);   // bool(false)
```

Full source: [listing-16.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-16.php)


The comparison can also be shortened: `if ($verify)` means "if `$verify` is true". And a boolean is not born only from the constants `true` and `false`: any **expression that returns true or false** can be assigned to a variable:

```php
<?php

$verify = 4 > 5;    // Is 4 greater than 5? No
var_dump($verify);  // bool(false)

$verify = 4 == 5;   // Is 4 equal to 5? No
var_dump($verify);  // bool(false)
```

Full source: [listing-17.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-17.php)


In Chapter 8 we will see the difference between comparison with two equal signs (`==`) and with three (`===`): the second expects the values to be equal *and of the same type*.

Now the interesting part. Let's assign `$verify` a string:

```php
<?php

$verify = 'Hello world';
var_dump($verify);   // string(11) "Hello world"

if ($verify) {
    echo 'Verify is true';   // is executed!
}
```

Full source: [listing-18.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-18.php)


`$verify` is a string, but the condition passes: a non-empty string, converted to boolean, is `true`. PHP does the conversion automatically, but we can also do it explicitly, putting the type in brackets in front of the value — it's called **cast** — as is done in Java and other languages:

```php
<?php

var_dump((bool) 'Hello world');   // bool(true)
var_dump((bool) '');              // bool(false)
var_dump((bool) '0');             // bool(false) — the string "0"!
```

Full source: [listing-19.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-19.php)


### Be careful of "true" and "false" strings

There's a practical pitfall you'll encounter when working with forms in Part IV. If we send the words `true` or `false` from the browser to PHP, on the server side they arrive as **strings** — and a non-empty string is always true:

```php
<?php

$verify = 'false';   // 5-character string, NOT the Boolean false
var_dump($verify);   // string(5) "false"

if ($verify) {
    echo 'Enters the true branch!';   // yes: a non-empty string is true
}
```

Full source: [listing-20.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-20.php)


The same goes for a checkbox, which itself sends values like `on`/`off`: they arrive as strings, and `'off'` would also be true. For this reason, the standard, on the client side, is to send **`0` and `1`**: the string `'0'` is false and `'1'` is true, so we are sure to get the boolean we expect. In other languages ​​this little game doesn't work: there you need the literal values ​​`true` and `false` or an explicit cast. In PHP, knowing the falsy value table, it works great.

## Introduction to strings

A **string** in PHP is a sequence of characters, where each character is represented by a **byte**: 256 different values are therefore possible for each byte. This detail, which seems academic, is actually very important: internally PHP stores *sequences of bytes*, without knowing anything about the coding. It's up to us — and the functions and libraries we use — to correctly interpret those bytes, both when they arrive from an external source and when we feed them to PHP. We will immediately see the practical consequences.

### Single quotes and quotation marks

There are two basic ways to delimit a string: **single quotes** (`'...'`) and **quotation marks**, or double quotes (`"..."`). The difference is fundamental:

- with **single quotes**, PHP takes the string as it is: no variables are interpreted;
- with **quotation marks**, PHP **parses** the string looking for the variables inside it (everything that starts with `$`, or enclosed in braces, as we will see) and replaces them with their value: this is called **interpolation**.

```php
<?php

$name = 'John';
$address = 'Main Street';

$lastName = "$name Arias";
echo $lastName;          // John Arias

echo 'First name: $name';      // First name: $name  (no parsing!)
echo "First name: $name";      // First name: John
```

Full source: [listing-21.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-21.php)


In the first assignment, inside the quotes PHP finds `$name`, interprets it and produces `John Arias`. Note the space after the variable: it also serves to make it clear where the variable name ends. With single quotes, however, the string `'$address'` literally remains `$address`, including the dollar.
When there is nothing to interpolate, PHP with single quotes completely avoids the parsing step: once it was also measurable in speed, today the difference is negligible. By convention, however, I use **single quotes whenever there are no variables in the string**, and quotation marks only when interpolation is needed: it immediately makes it clear, when reading the code, which strings are "dynamic". I suggest it to you as a habit.

### Escape characters

Inside the quotes PHP also interprets the **special characters** (or escape sequences), which begin with the backslash: the most used are `\n` (new line*), `\t` (tab) and `\f` (line feed). They are the same as Java, C and JavaScript. Inside single quotes, however, they are not interpreted.

```php
<?php

$name = 'John';
$lastName = 'Arias';
$address = 'Main Street';

echo "$name $lastName\n$address";
```

Full source: [listing-22.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-22.php)


On the console the address wraps. In the browser, as we have already seen, no: the newline is present in the source of the page, but it is not rendered. Here, a native PHP function, **`nl2br()`** (*new line to break*), which transforms each `\n` into an `<br>` HTML tag, comes in handy:

```php
<?php

echo nl2br("$name $lastName\n$address");
// Generated source: John Arias<br />
// Main Street
```

Full source: [listing-23.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-23.php)


By reloading the page, the text also wraps in the browser: looking at the source with the browser (for example in Chrome) you will see that the new line has been accompanied by an `<br />`.

## Access and edit a string

Being a sequence of characters, a string in PHP behaves like an **array of characters**: we can access every single character with square brackets and an index that starts from **zero**.

```php
<?php

$name = 'John';
echo $name[0];   // H
echo $name[4];   // a
```

Full source: [listing-24.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-24.php)


We can also *modify* a character by assigning a new value to that position. Suppose I wrote my name without an accent and want to replace the last `a` with an `à`:

```php
<?php

$name = 'John';
$name[4] = 'à';
echo $name;   // Hidr�  ← corrupted character!
```

Full source: [listing-25.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-25.php)


The result is a strange character. Why? Let's go back to what I said at the beginning: for PHP a string is a **sequence of bytes**. In UTF-8 encoding the accented `à` occupies **two bytes**, but by assigning it to position 4 we are replacing **only one byte**. PHP then takes only the first byte of the accented character, and the result is an invalid sequence. Let's check it out:

```php
<?php

$accented = 'à';
var_dump($accented);   // string(2) "à"  ← two bytes!
```

Full source: [listing-26.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-26.php)


The same phenomenon occurs with native string functions. **`strlen()`** returns the length of a string — but in *bytes*, not characters:

```php
<?php

echo strlen('à');      // 2
echo mb_strlen('à');   // 1
```

Full source: [listing-27.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-27.php)


**`mb_strlen()`** instead answers correctly: one character. Functions with the prefix **`mb_`** belong to the **mbstring** (*multibyte string*) library, added to PHP to solve this problem: PHP doesn't have native UTF-8 support, and its native functions don't know whether those bytes represent a UTF-8 character, Latin-1, or something else — to them, they're just bytes. The rule of thumb: When you're working with text that may contain accents or non-ASCII characters and you need lengths, substrings, and the like, use `mb_*` functions — usually just add the prefix `mb_` to the name of the corresponding native function.

I'm telling you this because it's one of the PHP tricks that everyone falls for at first: knowing how strings really work saves you hours of debugging. In Chapter 11 we will delve deeper into string manipulation functions.

One last historical note: in the old code you will also find access to characters with curly braces (`$name{4}`). This syntax was deprecated in PHP 7.4 and **removed in PHP 8**: always use square brackets.

## Convert to string: casting

As with numbers, in PHP there is usually no need to explicitly cast to string: if we `echo` of a number, it is automatically converted. However, there are some values — especially `null` and booleans — for which you need to know *how* the conversion occurs:

| Starting value | Converted to string |
|---|---|
| `null` | empty string `''` |
| `true` | `'1'` |
| `false` | empty string `''` |
| number | the textual representation of the number |
| array | the word `Array` (with a warning) |

Let's check with the explicit cast `(string)`:

```php
<?php

var_dump((string) null);    // string(0) ""
var_dump((string) true);    // string(1) "1"
var_dump((string) false);   // string(0) ""

$bool = true;
echo $bool;   // 1  (automatic conversion, no cast)

$bool = false;
echo $bool;   // (nothing is displayed: empty string)
```

Full source: [listing-28.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-28.php)


Pay attention to the case of the array: if we use an array where PHP expects a string, as in `echo`, we get the word `Array` and PHP signals us that we are doing something incorrect with the warning *Array to string conversion*:

```php
<?php

$ar = [1, 2, 3];
echo $ar;   // Warning: Array to string conversion — output: Array
```

Full source: [listing-29.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-29.php)


I take this opportunity to formalize **concatenation**: a string is concatenated with another string — or with any value, which will be converted into a string — using the **dot** (`.`). Not the `+` like in JavaScript: in PHP the plus is just arithmetic.

```php
<?php

$name = 'John';
$bool = true;

echo $name . ' Arias';   // John Arias
echo $name . $bool;      // John1   (true → '1')

$bool = false;
echo $name . $bool;      // John    (false → empty string)
```

Full source: [listing-30.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-30.php)


As you can see, in the concatenation the boolean is converted into a string automatically, without the need for explicit casting: the rules are always those in the table above.

## Heredoc and nowdoc

In addition to single quotes and single quotes, PHP offers a third way to represent strings: the **heredoc** construct. It is very useful when we have to write long texts, on several lines, with variables inside, without having to manage quotes and concatenations.

### The heredoc syntax

A heredoc opens with **three minor signs** (`<<<`) followed by an **identifier** of our choice — for example `EOD`, *end of data* — and closes by repeating the **same identifier**, followed by the semicolon. The identifier follows the same rules as variable names (must start with a letter or underscore, then letters, numbers, and underscores), without the dollar sign:

```php
<?php

$name = 'John';
$lastName = 'Arias';
$address = 'Main Street';

$data = <<<EOD
My name is $name <br>
My last name is $lastName <br>
My address is $address
EOD;

echo $data;
```

Full source: [listing-31.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-31.php)


Output to browser:

```text
My name is John
My last name is Arias
My address is Main Street
```

Full source: [listing-32.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-32.txt)


Between opening and closing we can put anything we want - even a poem - and the variables are **interpolated** exactly like inside the quotes.

### Arrays and objects inside a heredoc

**arrays** and **objects** can also be interpolated inside quotes and heredocs (we will study them shortly and in Part VII respectively, but an example serves to establish the syntax). With a numeric index there are no problems:

```php
<?php

$accounts = [2, 3];

$data = <<<EOD
The first account is $accounts[0]
EOD;

echo $data;   // The first account is 2
```

Full source: [listing-33.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-33.php)


However, if the key is a string, writing the quotes inside the simple interpolation produces a **syntax error**:

```php
$accounts['accountNumber'] = 223344;

// SYNTAX ERROR:
// $data = <<<EOD
// The account number is $accounts['accountNumber']
// EOD;
```

Full source: [listing-34.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-34.php)


There are two solutions: remove the quotes from the key (it works, but I don't like it), or — and this is what I prefer — keep the quotes and enclose the entire expression in **curly brackets**:

```php
<?php

$accounts = [2, 3];
$accounts['accountNumber'] = 223344;

$data = <<<EOD
The account number is {$accounts['accountNumber']}
EOD;

echo $data;   // The account number is 223344
```

Full source: [listing-35.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-35.php)


Between the braces you can put any valid PHP expression, even a simple variable like `{$address}` (in that case the braces would not be needed, but PHP does the parsing anyway). Just be careful not to nest one variable inside another in the same simple expression: if necessary, close and open a new expression between braces.

With objects the arrow syntax works directly; braces become necessary only for more complex cases, such as calling a method:

```php
<?php

$object = new stdClass();
$object->name = 'Jim';

$data = <<<EOD
The name is $object->name
EOD;

echo $data;   // The name is Jim
```

Full source: [listing-36.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-36.php)


For basic use remember this: simple variable or array with numeric index → the name is enough; array with string key (with quotes) or more complex expressions → curly brackets.

### The nowdoc syntax

The **nowdoc** is identical to the heredoc, with one difference: the opening identifier must be enclosed in **single quotes**. And the difference in behavior is the same as between quotes and single quotes: **nothing** inside is interpreted.

```php
<?php

$name = 'John';

$code = <<<'EOD'
My name is $name <br>
EOD;

echo $code;   // My name is $name <br>   (literal!)
```

Full source: [listing-37.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-37.php)


What is it for? For example, when we want to show **PHP code as text** — in a tutorial, on a page that explains how to create a class — without it being interpreted: dollars, variables and newlines remain exactly as we wrote them.

### What's new in PHP 7.3

Until PHP 7.2 the closing marker had to stand **alone, at the beginning of the line**, without any indentation, under penalty of a syntax error. From **PHP 7.3** onwards we can indent the closing marker, and the marker indentation is removed from all lines of content:

```php
<?php

function getList()
{
    $content = <<<EOD
        <ul>
            <li>one</li>
            <li>two</li>
        </ul>
        EOD;

    return $content;
}

echo getList();
```

Full source: [listing-38.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-38.php)


No more marker stuck to the left margin in the middle of indented code: the editor reports no errors and the `echo` shows the content regularly. The only rule is that the content cannot be indented *less* than the closing marker. This applies to both heredoc and nowdoc.

## Arrays: definition and keys
With this paragraph we begin the study of **arrays**, one of the most important structures in PHP. An array is a set of data that can function as a map of **key-value** pairs, as a list, as a hash table, as a stack, as a queue, as a dictionary. Together with strings, arrays are the part of the language to be mastered perfectly: PHP brings with it **hundreds of native functions** to process them, and when solving real problems we will find ourselves using them continuously (Chapter 12 is dedicated to this).

### Create an array

There are two syntaxes: the **`array()`** construct, which has existed since the origins of the language, and the **short syntax** with square brackets `[]`, which is the one we will use:

```php
<?php

$ar = array('red', 'green', 'blue');   // historical syntax
$ar = ['red', 'green', 'blue'];        // short equivalent syntax
```

Full source: [listing-39.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-39.php)


We can declare the key-value pairs explicitly, but if we do not indicate the keys PHP creates them automatically: **numeric keys starting from zero**. Let's check with `var_dump()`:

```php
<?php

$ar = ['red', 'green', 'blue'];
var_dump($ar);
```

Full source: [listing-40.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-40.php)


```text
array(3) {
  [0]=>
  string(3) "red"
  [1]=>
  string(5) "green"
  [2]=>
  string(4) "blue"
}
```

Full source: [listing-41.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-41.txt)


`var_dump()` tells us everything: the type (array), the size (3), each key and each value with type and length. There is also another very convenient function, **`print_r()`**, which only shows the structure — keys and values — without the types:

```php
<?php

print_r($ar);
```

Full source: [listing-42.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-42.php)


```text
Array
(
    [0] => red
    [1] => green
    [2] => blue
)
```

Full source: [listing-43.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-43.txt)


Sometimes we don't care about the type but only how the array is composed, and `print_r()` is more readable. In the rest of the examples I will use `var_dump()`, which gives the most complete description.

### Add elements and choose indexes

Unlike JavaScript, in PHP to add an element it is not mandatory to indicate the key: just use the **empty square brackets** and PHP takes the highest numerical index already used and increases it by one:

```php
<?php

$ar = ['red', 'green', 'blue'];

$ar[] = 'pink';      // ends at position 3

$ar[9] = 'yellow';   // we can jump directly to position 9
$ar[] = 'magenta';   // the next automatic index is 10!
```

Full source: [listing-44.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-44.php)


As you can see, we can also indicate the position by skipping values: after putting `yellow` at position 9, the internal counter starts again from there, and the next `[]` uses 10. Nothing prevents us from filling a "hole" by explicitly indicating an unused index, for example 4 — and at position 4 we can put any value, even **another array**:

```php
<?php

$ar[4] = [2, 4, 24, 44, 100];
```

Full source: [listing-45.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-45.php)


Here is our first array within an array: we return to it in the paragraph on multidimensional arrays.

### String keys and numeric keys in the same array

PHP lets us use **string keys** and numeric keys in the same array, which makes it a full-fledged map:

```php
<?php

$ar['yellow'] = 'amarillo';   // yellow in Spanish
$ar[] = 'sky';                // goes to position 11: the numeric counter
                              // ignores string keys completely
```

Full source: [listing-46.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-46.php)


The string key has nothing to do with the numeric counter: they each continue on their own. To read a value just use the key with which we entered it:

```php
<?php

echo $ar['yellow'];   // amarillo
```

Full source: [listing-47.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-47.php)


Note that I wrote the key in **single quotes**, following the convention I suggested for strings: single quotes when there is nothing to interpolate.

### Keys always go in quotes

What happens if we don't put superscripts? I see it written in a lot of old and neglected code:

```php
<?php

echo $ar[yellow];   // it works... but it is an error!
```

Full source: [listing-48.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-48.php)


In PHP 7 this code still prints `amarillo`, but PHP reports that it didn't find the **constant** `yellow` and deduced that we meant the string `'yellow'`. It is a warning that does not block the code, but should never be ignored. In **PHP 8 it is no longer tolerated**: using a key without quotes raises a fatal error (*Undefined constant*).

Why was he so dangerous? Because someone could actually define a constant with that name. Let's see what would happen:

```php
<?php

define('yellow', 4);   // a constant named yellow with value 4

print_r($ar[yellow]);
// PHP replaces the constant with its value: $ar[4]
// and at position 4 there is... the array [2, 4, 24, 44, 100]!
```

Full source: [listing-49.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-49.php)


PHP finds the constant `yellow`, sees that it is 4, and reads position 4 — where the nested array is, not `amarillo`. A sneaky and difficult to find bug. Moral: **always place quotes around string keys**.

### How PHP converts keys

The keys of an array can be **only integers or strings**, and PHP applies automatic conversions that are good to know:

```php
<?php

$ar['5'] = 'cinque';   // the string "5" becomes the INTEGER key 5
$ar['5.0'] = 'a';      // "5.0" is NOT an integer: it remains the string "5.0"
$ar['5.2'] = 'b';      // it remains the string "5.2"
$ar[5.2] = 'c';        // float without quotes: TRUNCATED to integer key 5!
```

Full source: [listing-50.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-50.php)


A string containing a "well-formed" integer is converted to the corresponding number; a string like `"5.0"` or `"5.2"` instead remains a string. But a **float used directly as a key is truncated**: only the whole part is taken, without any error. Imagine an array where the key is a price and the value is the list of products of a store with that price: if you use the float `5.2` as the key, everything ends up under the key `5`. If you want to keep the decimal key you must pass it explicitly as a string, in quotes.

Finally, any other type used as a key — an array, an object — produces an error (*Illegal offset type*): the editor warns you about it even before executing.

```php
<?php

// $ar[['a']] = 'x';   // TypeError: Illegal offset type
```

Full source: [listing-51.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-51.php)


## Multidimensional arrays

Our `$ar` is already a **multidimensional** array: at position 4 it contains another array. Let's see how to work with these nested structures.

### Access nested items

To access a nested element, you line up the square brackets, one level after the other. At position 4 we have `[2, 4, 24, 44, 100]`; to read the fourth element (index 3, counting from zero):

```php
<?php

echo $ar[4][3];   // 44
```

Full source: [listing-52.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-52.php)


Be careful when accessing **within a string**. With a simple array direct interpolation works (`"$ar[2]"` print `blue`), but with two levels of indices it doesn't: you need to enclose the expression between **braces**, as we saw for the heredocs:

```php
<?php

echo "{$ar[4][3]} <br>";   // 44 — without braces it would not be interpreted correctly
```

Full source: [listing-53.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-53.php)


Let's now add a string key that contains an array with the days of the week:

```php
<?php

$ar['DAYS'] = ['Monday', 'Tuesday'];

echo "{$ar['DAYS'][1]} <br>";   // Tuesday
```

Full source: [listing-54.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-54.php)


Remember the braces, and remember one more thing: keys are **case-sensitive**. If we search for `days` in lower case, PHP doesn't find the key and reports *Undefined array key "days"*:

```php
<?php

echo $ar['days'][1];   // Warning: key not found! 'days' ≠ 'DAYS'
```

Full source: [listing-55.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-55.php)


### Edit, add and delete items

To **modify** a value simply access its key and assign: for example, let's overwrite the value of `'yellow'`, from `amarillo` to `yellow`:

```php
<?php

$ar['yellow'] = 'yellow';
```

Full source: [listing-56.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-56.php)


To **add an element to a nested array** we can use the native function **`array_push()`**: we pass it the array to modify and the value to append:

```php
<?php

array_push($ar['DAYS'], 'Wednesday');
var_dump($ar['DAYS']);
// Monday, Tuesday, Wednesday — Wednesday went to the next position (2)
```

Full source: [listing-57.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-57.php)


To **delete** a key — and its value — there is **`unset()`**: we pass it the element to remove.

```php
<?php

unset($ar['DAYS']);     // the entire DAYS key disappears from the array
unset($ar[2]);          // we also remove 'blue', at position 2
```

Full source: [listing-58.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-58.php)


Here is an important detail: with numeric keys `unset()` **leaves a hole**. The keys are not rearranged: after removing position 2 we will have 0, 1, 3, 9, 10... Let's see it on a clean array:

```php
<?php

$ar2 = ['a', 'b', 'c', 'd'];
unset($ar2[2]);   // remove 'c'

var_dump($ar2);
```

Full source: [listing-59.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-59.php)


```text
array(3) {
  [0]=>
  string(1) "a"
  [1]=>
  string(1) "b"
  [3]=>
  string(1) "d"
}
```

Full source: [listing-60.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-60.txt)


The keys are 0, 1 and **3**: the 2 is gone and no one has renumbered it. If we want the sorted keys 0, 1, 2 again, we use **`array_values()`**, which returns all the values of an array by reindexing the numeric keys from zero:

```php
<?php

$ar2 = array_values($ar2);
var_dump($ar2);
// now the keys are 0, 1, 2
```

Full source: [listing-61.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-61.php)


`array_values()` is also useful on our mixed array: calling it on `$ar` we get a new array where each element — colors, nested array, everything — receives a progressive numeric key 0, 1, 2, 3... and the string keys disappear. Remember this every time you need a copy of an array with the numeric keys sorted. In Chapter 12 we will see many other functions for manipulating arrays: adding and removing leading and trailing values, sorting them, filtering them, and more.

## The constants: const and define

A **constant**, as the name implies, is a value that does not change. Let's think about pi again: if we put it in a variable, there is nothing to stop us from overwriting it by accident.

```php
<?php

$pi = 3.1415;
echo $pi . PHP_EOL;

$pi = 1.718;          // allowed: it is a variable
echo $pi . PHP_EOL;   // pi is now 1.718...
```

Full source: [listing-62.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-62.php)


(`PHP_EOL` is a predefined PHP constant that contains the correct end-of-line character for the platform on which the script runs — and at the end of the paragraph we will see that it is defined exactly with the tools we are about to study.)

### Declaring a constant with const

To declare a constant, use the keyword **`const`**. The name follows the same rules as variables, with one difference: **no dollar** — if you try to enter it, the editor immediately reports a syntax error. By convention, the names of the constants are written **all in capital letters**, and if they are composed of several words they are separated with the underscore (`TAX_RATE`):

```php
<?php

const PI = 3.1415;

echo PI;      // 3.1415
// PI = 3;    // ERROR: you cannot assign to a constant
```

Full source: [listing-63.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-63.php)


Once assigned, the value can no longer change: the editor already reports the attempt to overwrite, and when running we would get an error. The value of an `const` can be a literal — a number, a string — or a **constant expression**, calculable on the fly at compile time:

```php
<?php

const RESULT = 3 * 5;   // OK: expression can be calculated immediately
```

Full source: [listing-64.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-64.php)


However, it cannot depend on something that is only known at runtime: a function call, a reading from the database. It must be a determinable value at the time we assign it.

Two previews. First: we will find the same syntax `const` **inside classes** in Part VII, where the constants will belong to the class instead of the global scope. Second: when we study visibility we will see that variables are visible only in the context in which they arise — inside a function, an external variable cannot be seen unless imported. **Constants, on the other hand, are global**: once defined, they are visible everywhere, even within functions.

### define and verify it with defined

There is a second, older way of defining a constant: the function **`define()`**, to which we pass the name of the constant as a string and the value:

```php
<?php

define('PI2', 3.1415);
echo PI2;   // 3.1415
```

Full source: [listing-65.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-65.php)


Be careful though: if we try to define the same constant twice, the editor doesn't notice it (for it it's a normal function call) and we only notice it by executing, with the warning *Constant PI2 already defined*:

```php
<?php

define('PI2', 3.1415);
define('PI2', 3);   // Warning: Constant PI2 already defined
```

Full source: [listing-66.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-66.php)


A historical curiosity: `define()` accepted a third parameter to make the name of the constant *case-insensitive*. It was **deprecated in PHP 7.3 and removed in PHP 8**: in addition to no longer working, it was also dangerous. Constant names are always case-sensitive.

The real strength of `define()` is that it is accompanied by the **`defined()`** function, which checks whether a constant has already been defined. We can thus protect the definition:

```php
<?php

if (!defined('PI2')) {
    define('PI2', 3.1415);
}
```

Full source: [listing-67.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-67.php)


The exclamation point negates the condition: "if `PI2` is **not** defined, define it". Running the code a second time, PHP does not go through `define()` and there is no error.

### Arrays as constants

We can also declare an **array** as a constant — something that was not possible in older versions of PHP 5 (it came with PHP 5.6 for `const` and with PHP 7 for `define()`):

```php
<?php

const PROVINCES = ['London', 'Manchester'];

// PROVINCES[2] = 'Edinburgh';   // ERROR: you cannot modify a constant
// const PROVINCES = [];    // ERROR: already defined

define('REGIONS', ['England', 'Scotland']);
var_dump(REGIONS);
```

Full source: [listing-68.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-68.php)


As with any constant, we can neither add elements nor reassign it: the editor tells us this immediately. And be careful about accessing a constant that doesn't exist: in very old versions of PHP the name was silently treated as a string (with a warning), but in modern PHP we get a **fatal error** (*Undefined constant*). One more reason to use `defined()` when in doubt.

In summary, and I'll also give you my personal preference: in my code I almost don't use `define()` anymore — I use **`const`**, which is shorter to write, is understood by the editor (which warns us of overwrites and reassignments before even executing) and leaves less room for typos between parentheses and superscripts. `define()` remains useful when you need the conditional definition with `defined()`. And remember the example of PHP itself: the constant `PHP_EOL` that we used before is defined just like that, name in uppercase with underscore, value equal to the platform end-of-line character.

## Check the variables: isset, empty and is_null

We close the chapter with three native functions that serve to answer three different questions about a variable: has it been set? Is it empty? Is it `null`? They look similar, but the differences are important — and we'll use them again and again when we get data from the forms in Part IV.

### isset: Is the variable set?

**`isset()`** checks if a variable has been set **and** if it has a different value than `null`:

```php
<?php

if (isset($name)) {
    echo "$name exists";
} else {
    echo 'The variable does not exist';
}
// Output: The variable does not exist
```

Full source: [listing-69.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-69.php)


Note that `$name` we didn't even declare it, yet `isset()` doesn't raise any warnings: it simply replies `false`. If we assign any value — even an empty string, even `0` — `isset()` responds `true`. The only value that `false` responds to on a declared variable is `null`.

### empty: Is the variable empty?
**`empty()`** checks if a variable is "empty". But what does empty mean for PHP? A variable is empty when **it has not been declared** or when its value, **converted to boolean, becomes `false`** — exactly the false values we saw when studying the boolean type:

```php
<?php

if (empty($name)) {
    echo 'name is empty';
} else {
    echo "name is not empty and equals $name";
}
```

Full source: [listing-70.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-70.php)


Let's try the various cases:

```php
<?php

// $name never declared     -> empty (and no warning!)
$name = '';       // empty
$name = 'John'; // not empty
$name = 0;        // empty
$name = '0';      // empty — watch out!
$name = 0.0;      // empty
$name = null;     // empty
$name = false;    // empty
$name = [];       // empty (array with no elements)
```

Full source: [listing-71.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-71.php)


Two observations. The first: you have to pay close attention to **zero**. `empty()` considers both the integer `0` and the string `'0'` to be empty: so `isset()` would say the variable is set, but `empty()` gives it as empty. If zero has a meaning for you — for example, you need to be able to set a price to zero — **do not** use `empty()`: rather, check that the value is not `null`, as we will see immediately.

The second: `empty()` on a variable never declared **does not generate any warning**. If instead we tried a simple `if ($name)` on an undeclared variable, PHP would report *Undefined variable* — a notice up to PHP 7.4, a warning from PHP 8. It's not an execution-blocking error, and in a production environment you wouldn't even see it, but it shouldn't be ignored. `empty()` allows us to do the verification cleanly.

### is_null: Is the variable null?

**`is_null()`** checks for only one thing: whether the variable has the value **`null`** — just `null`, not something that looks like it:

```php
<?php

$name = null;

if (is_null($name)) {
    echo 'name is null';
} else {
    echo 'name is not null';
}
// Output: name is null
```

Full source: [listing-72.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-72.php)


Conceptually `is_null()` is almost the opposite of `isset()`: a variable `null` is not set, and `!isset($name)` means "it is `null` or it has never been defined". However, there is a practical difference: if the variable **has never been declared**, `is_null()` returns yes `true`, but PHP also reports the warning *Undefined variable*; `isset()` however it never does. So use `is_null()` when you're sure the variable has been initialized — for example, you declared it yourself and then the value comes from a file or external resource — and you just want to know if it contains `null`.

Be careful not to confuse `null` with the empty string: they are different concepts.

```php
<?php

$name = '';
var_dump(is_null($name));   // bool(false): the empty string is NOT null

var_dump(null == '');       // bool(true)  — weak comparison: both values are falsy
var_dump(null === '');      // bool(false) — different types!
```

Full source: [listing-73.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-7/en/parte-02/cap-07/listing-73.php)


With the two-equal comparison PHP casts and `null` is equal to the empty string; with the comparison of three equals no, because the types are different. PHP can be confusing here: keep the three concepts separate — *set*, *empty*, *null*.

### Which function to use?

Here is the summary table that I use as a rule of thumb:

| Question | Function | Notes |
|---|---|---|
| Does the variable exist and is not `null`? | `isset()` | never warnings; `true` for any value except `null` |
| Is the variable empty (falsy)? | `empty()` | never warnings; but `0` and `'0'` are empty |
| Is the variable exactly `null`? | `is_null()` | warning if variable is not declared |

If you just want to know that the variable is set, use `isset()`. If you care about it being *and* not empty — and for you empty string, `false`, zero and empty array count as "nothing" — feel free to use `empty()`. If zero is a legitimate value in your context, avoid `empty()` and check with `is_null()` or with an explicit comparison.

## In summary
- A **variable** is an area of ​​memory with a name that acts as a label: in PHP it starts with `$`, followed by a letter or underscore, then letters, numbers and underscores. Use talking names and the camelCase convention; PHP is dynamically typed, so the type can change at runtime.
- Numbers are **integer** or **float**; integers can also be written in octal (`0`), hexadecimal (`0x`) and binary (`0b`). PHP automatically converts numeric strings into operations, but it is good practice to respect types.
- Type **boolean** has only `true` and `false`, but any value can be converted: store the list of falsy values (`false`, `0`, `0.0`, `''`, `'0'`, `[]`, `null`) — everything else is true. From the forms send `0`/`1`, not the strings `'true'`/`'false'`.
- **strings** are sequences of bytes: single quotes do not interpolate variables, double quotes do (along with escapes like `\n`). For multibyte characters (accents, UTF-8) use the `mb_*` functions: `strlen()` counts bytes, `mb_strlen()` counts characters.
- When casting to string: `null` and `false` become empty string, `true` becomes `'1'`, an array becomes the word `Array` (with warning). The concatenation is done with the **dot**, not with the `+`.
- **Heredoc** (`<<<EOD`) interpolates variables, arrays and objects (with braces for complex expressions); **nowdoc** (`<<<'EOD'`) does not interpret anything. Since PHP 7.3 the closing marker can be indented.
- **arrays** accept integer and string keys in the same array; `[]` append using the highest numeric index + 1. Always quote string keys; remember that floats as key are truncated and that `unset()` leaves holes in numeric indices — `array_values()` reindexes them.
- **constants** are defined with `const` (preferred) or `define()`; nothing `$`, name capitalized by convention, value immutable and computable at compile time, arrays allowed. `defined()` checks for existence; constants are visible everywhere.
- **`isset()`** says if a variable is set and not `null`; **`empty()`** if it is false (watch out for zero!); **`is_null()`** if exactly `null` is valid. Neither of the first two generates warnings about undeclared variables.
