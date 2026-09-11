# 8. Operators

After you learned how to declare variables and recognize data types in Chapter 7, it's time to make them work together. The **operators** are the symbols that allow us to assign values, make calculations and - above all - compare data with each other: they are the bricks with which we will build the conditions and cycles of Chapter 9.

In this chapter we will look at assignment and arithmetic operators, the exponential operator, the entire family of comparison operators (with a focus on how PHP compares numbers and strings, a behavior that changed significantly with PHP 8), the spaceship operator, ternary and null coalescing, up to assignment with null coalescing introduced in PHP 7.4. These are topics that seem simple, but hide some of the most classic traps of PHP: knowing them well will avoid bugs that are difficult to find.

## The assignment operator

When we write:

```php
<?php

$a = 5;
$b = 8;
```

Full source: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-01.php)


it seems like the usual math: we are assigning the value `5` to the variable `$a` and the value `8` to the variable `$b`. (Remember, from Chapter 7, that variable names are *case sensitive*: `$a` and `$A` are two different variables.)

In reality the **assignment operator** `=` does something more precise: it takes the **expression** located on its right, evaluates it completely and only at the end assigns the result to the variable on the left. With a literal value like `5` there is nothing to calculate, but look at this case:

```php
$c = $a + $b;
echo $c; // 13
```

Full source: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-02.php)


Some might think "I assign `$a` to `$c` and then add `$b`". No: the entire operation on the right (`$a + $b`, i.e. `5 + 8`) is performed first, and then the result `13` is assigned to `$c`. The concept must be clear, because it is the basis of everything regarding **operator precedence** which we will see shortly.

## Arithmetic operators

For mathematical operators, precedence is the one we studied at school. The **multiplication** operator is the asterisk `*`, and multiplication and division take precedence over addition and subtraction:

```php
$c = $a + $b * 5;
echo $c; // 45
```

Full source: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-03.php)


First `$b * 5` is calculated (i.e. `8 * 5 = 40`) and then `$a` is added: `40 + 5 = 45`.

As in mathematics, we can change precedence with **round brackets**:

```php
$c = ($a + $b) * 5;
echo $c; // 65
```

Full source: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-04.php)


Now first we add `$a + $b` (which is `13`) and then we multiply by `5`, obtaining `65`.

For the **division** the same applies, but instead of the asterisk we use the slash `/`:

```php
$c = ($a + $b) / 5;
echo $c; // 2.6
```

Full source: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-05.php)


Note that the result is a decimal value (a float), even though the operands were integers.

### The modulus operator

Then there is an operator that is not used at school with this name: the **module** `%`, which returns the **remainder** of the division between two integers. If I write `25 / 8` I do a normal division; if instead I use the percentage I'm asking: "how much is the remainder of this division?"

```php
$d = 25 % 8;
var_dump($d); // int(1)
```

Full source: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-06.php)


The result is `1`, because `8 * 3 = 24` and there is exactly one left.

In summary, the basic arithmetic operators in PHP are:

| Operator | Operation | Example |
|---|---|---|
| `+` | Addition | `5 + 8` → `13` |
| `-` | Subtraction | `8 - 5` → `3` |
| `*` | Multiplication | `8 * 5` → `40` |
| `/` | Division | `13 / 5` → `2.6` |
| `%` | Form (rest) | `25 % 8` → `1` |
| `**` | Exponentiation | `2 ** 4` → `16` |

In the PHP mathematical libraries we find many other functions (decimal/binary conversions, more precise calculations and so on), but these are the fundamental operators.

## The exponential operator

Before PHP version 5.6, to raise a number to a certain power you had to use the `pow()` function, passing the base and exponent:

```php
$result = pow(2, 6);
echo $result; // 64
```

Full source: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-07.php)


You can try it immediately from the console: if you have PHP installed, save the code in a file and launch it with `php index.php` (or the name you gave to the file).

From PHP 5.6 onwards there is a simpler and clearer way: the **exponential operator** `**`, i.e. two asterisks, also present in other languages:

```php
$result = 2 ** 6;
echo $result; // 64
```

Full source: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-08.php)


`2 ** 6` means "two to the sixth power" and works exactly like `pow(2, 6)`. Of course we can continue to use `pow()`, but with the exponential operator the syntax is shorter and more readable.

### Be careful about associativity

However, there is one thing to keep in mind: the order of evaluation. The `**` operator is **right associative**, unlike most arithmetic operators which evaluate from left to right. What do you think comes out of this expression?

```php
$result = 2 ** 3 ** 2;
echo $result; // 512
```

Full source: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-09.php)


If it were evaluated from left to right it would be `(2 ** 3) ** 2`, i.e. `8` squared: `64`. Instead, with right associativity, `3 ** 2` is calculated first (which is `9`) and then `2 ** 9`, i.e. `512`.

The advice, when combining `**` with other operators, is to always consult the precedence table in the PHP manual or - much better - to explicitly indicate the order with round brackets: this way you avoid problems and you don't have to remember by heart which operator has the highest precedence.

### The square root

What if we wanted the inverse operation, the square root? In this case there is not an operator, but a function: `sqrt()` (from *square root*):

```php
echo sqrt(16); // 4
```

Full source: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-10.php)


The square root of `16` is `4`, which is the opposite of the exponentiation we just did.

## Comparison operators

The **comparison operators** allow us to compare two values: to know if they are equal, different, if one is greater or less than the other, a bit like we studied in mathematics. The result of a comparison is always a **boolean** value: `true` or `false`.

However, there is a feature of PHP to always keep in mind: when it compares two values, it can first perform the **cast** (type conversion) of the operands. And this is where the surprises arise.

### Same and identical

In PHP you have to distinguish between "equal" and "strictly equal" (or **identical**, as I call them). Look at these two variables, where `$a` is a string and `$b` is a number:

```php
$a = '1';
$b = 1;

$c = $a == $b;

var_dump($a); // string(1) "1"
var_dump($b); // int(1)
var_dump($c); // bool(true)
```

Full source: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-11.php)


With double equals `==` PHP sees that the first value is a string and the second an integer, converts the string `'1'` into the number `1` (as we saw in Chapter 7 talking about conversions) and then compares: they are equal, therefore `true`.

If instead we want to verify that two values are equal **and also of the same type** — that is, strictly equal — we use three equal signs `===`:

```php
var_dump($a === $b); // bool(false)
```

Full source: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-12.php)


The result is `false`: they have the same value, but not the same type (one is a string, the other an integer). So: three equal signs when we want to check value **and** type, two equal signs when we are only interested in the value.

### The case of null

A case in which the difference is seen even better is `null`. Here `$a` has no value at all, while `$b` is zero:

```php
$a = null;
$b = 0;

var_dump($a == $b);  // bool(true)
var_dump($a === $b); // bool(false)
```

Full source: [listing-13.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-13.php)


Remember the times table from Chapter 7? For PHP anything that is `0`, `null`, the empty string `''`, `'0'` or an empty array is converted to `false`; everything else to `true`. When we compare `null == 0`, PHP does the cast and considers them equal. But `null === 0` is `false`: `null` is `null`, and zero is an integer — they're not identical, they're just equal in value.

Other interesting comparisons with double equals:

```php
var_dump(null == false); // bool(true)  — casting makes them equal
var_dump(null == '');    // bool(true)  — la empty string "vale" null
var_dump(null == '0');   // bool(false) — the string '0' is NOT equal to null
```

Full source: [listing-14.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-14.php)


### Why it matters: The price example
Whenever you compare two values ​​for equality, use the three symbols `===` to also check the type: you will avoid sneaky errors. Because maybe zero is a legitimate value — for example the price of a product — and your code unintentionally discards it. Imagine having to update the price of an item in an e-commerce site:

```php
$price = 0;

if ($price) {
    // here we would execute the update query
    echo 'Price updated';
} else {
    echo 'Price not updated';
}
// Output: Price not updated
```

Full source: [listing-15.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-15.php)


The `if` (which we will study in depth in Chapter 9) evaluates the expression inside it as Boolean: `$price` is `0`, the cast gives `false`, and the update query would never be executed. A nice and good bug, because zero is a valid price!

The solution is to explicitly check that the price is different from `null`, with a close comparison:

```php
if ($price !== null) {
    echo 'Price updated';
} else {
    echo 'Price not updated';
}
// Output: Price updated
```

Full source: [listing-16.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-16.php)


Now the condition passes, because `0` is a present value: it is different from `null` both in perceived value and type. Be very careful with these cases: if you don't check with strict comparison, for PHP zero, `null` and the empty string are equivalent.

### Different and not identical

The opposite of equality is expressed with the exclamation point. `!=` means "different" (only in value, with cast), while `!==` means "not identical": different in value **or** in type. Let's take `null` and the empty string:

```php
$a = null;
$b = '';

var_dump($a != $b);  // bool(false) — after casting they are equal
var_dump($a !== $b); // bool(true)  — one is null, the other is a string
```

Full source: [listing-17.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-17.php)


With `!=` the result is `false`: PHP does the casting, sees them as the same, so "they are not different". With `!==` instead it is `true`, because the types are different. There is also the alternative form `<>` for "different", but I always use `!=`.

Here is the summary table, which you can also find in the PHP manual:

| Example | Name | Result |
|---|---|---|
| `$a == $b` | Same | `true` if `$a` is equal to `$b` after type casting |
| `$a === $b` | Identical | `true` if equal and of the same type |
| `$a != $b` | Different | `true` if different after casting the types |
| `$a <> $b` | Different | Like `!=` |
| `$a !== $b` | Not identical | `true` if different in value or type |
| `$a < $b` | Minor | `true` if `$a` is strictly less than `$b` |
| `$a > $b` | Major | `true` if `$a` is strictly greater than `$b` |
| `$a <= $b` | Less than or equal to | `true` if `$a` is less than or equal to `$b` |
| `$a >= $b` | Greater than or equal to | `true` if `$a` is greater than or equal to `$b` |

### Compare strings

And the strings? When the two operands are both strings, the comparison occurs byte by byte, on the ordinal value of each byte:

```php
var_dump('a' != 'b'); // bool(true)  — they are different
var_dump('a' == 'b'); // bool(false) — they are not equal
var_dump('a' !== 'b'); // bool(true) — same type, different values
```

Full source: [listing-18.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-18.php)


When we compare strings with strings there are no problems: even double equals is fine, because the types already coincide. The problem, as we have seen, is when the types are mixed: empty string, zero, `null`.

### Major, minor and their friends

For `>`, `<`, `>=` and `<=` what we already know from mathematics applies; these operators also always return a boolean:

```php
$d = 0;
$e = 1;

$f = $d > $e;
var_dump($f);       // bool(false) — zero is not greater than one

var_dump($d < $e);  // bool(true)  — zero is less than one
var_dump($d <= $e); // bool(true)  — it is less, so "less than or equal" is also true
var_dump(1 <= 1);   // bool(true)  — it is not less, but it is equal
var_dump(2 <= 1);   // bool(false)
var_dump(2 >= 1);   // bool(true)
```

Full source: [listing-19.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-19.php)


It depends on what you want to check: if you just need it to be "greater than or equal" use `>=`; if you want it to be strictly greater, just use `>`.

What purpose do these operators serve in practice? To build conditions on data entered by the user or read from the database. A classic example:

```php
$age = 16;

if ($age >= 18) {
    echo 'You are an adult';
} else {
    echo 'You are underage';
}
// Output: You are underage
```

Full source: [listing-20.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-20.php)


With `$age = 16` the press program "You are a minor"; if you put `18`, the condition passes (thanks to the "or equal") and prints "You are an adult".

Be careful of a very common typing error: you write **first** the greater/lesser sign and **then** the equal sign (`>=`, `<=`). If you write `=>` PHP doesn't interpret it as a comparison — that sequence has a completely different meaning (we'll use it for arrays) — and you'll get an error.

## Comparing numbers and strings: what changes with PHP 8
There is a very common behavior of PHP that has changed significantly between PHP 7 and PHP 8, and it concerns the weak comparison (`==`) between a string and a number. If you need to migrate code from PHP 7 to PHP 8, this paragraph concerns you closely.

Let's start from a case that does not change:

```php
var_dump(0 == '0'); // bool(true) — in all versions
```

Full source: [listing-21.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-21.php)


`'0'` is a **numeric string**: it contains a number. `'0.0'` is too. When the string is numeric, comparing to a number works as you expect, before and after PHP 8.

The difference is *how* PHP does the comparison when the string is **not** numeric:

- **Before PHP 8**: PHP cast the string to a number and then compared the two numbers. A numeric string can have spaces in front of it; PHP read it from the beginning, found the number, and discarded everything after it (any character other than a digit or decimal point). And a string that didn't start with a number was converted... to `0`.
- **From PHP 8**: If the string is non-numeric, PHP does the opposite — converts the *number* to a string and compares the two strings.

The consequences can be seen immediately in this table:

| Comparison | PHP 7.x | PHP 8+ |
|---|---|---|
| `0 == "0"` | `true` | `true` |
| `0 == "0.0"` | `true` | `true` |
| `0 == "foo"` | `true` | `false` |
| `0 == ""` | `true` | `false` |
| `42 == " 42"` | `true` | `true` |
| `42 == "42abc"` | `true` | `false` |

Before PHP 8, `0 == "foo"` was `true`: the string `"foo"` does not begin with a number, it was converted to `0`, and zero equals zero. I can't tell you how many bugs I had to fix for this problem. The same was true for the empty string. And `42 == "42abc"` was `true` because PHP read `42` and discarded the rest; with PHP 8 it is `false`. Instead `" 42"` with spaces in front remains `true` in both versions: spaces (even after the number, from PHP 8) are allowed in a numeric string.

### Try comparisons with different versions of PHP

To do these tests I recommend an online sandbox like **onlinephpfunctions.com**: you can paste some code, run it and choose which version of PHP to test it with. Let's start with some `var_dump()`, which shows the result of the operation and the type it returns:

```php
var_dump(4 == 4);    // bool(true)
var_dump(4 == '4');  // bool(true) — numeric string
var_dump(4 == ' 4'); // bool(true) — and no warning for the space
```

Full source: [listing-22.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-22.php)


Of course, in the real world these values come in variables. Imagine having an expected id and a value that returns from a call or a form: everything that arrives from the web arrives **in string form** (we will see this well in Chapter 13 on superglobals):

```php
$id = 4;       // the value we expect: an integer
$result = '4'; // the value received from a form: always a string

var_dump($result);         // string(1) "4"
var_dump($id == $result);  // bool(true)
var_dump($id === $result); // bool(false) — different types
```

Full source: [listing-23.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-23.php)


If we want strictly equal comparison, we can cast to integer first, since we expect an integer:

```php
var_dump($id === (int) $result); // bool(true)
```

Full source: [listing-24.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-24.php)


At this point you might say to me: "but why complicate our lives? I always cast and compare with `===`, and that's it". The problem is that in PHP there are built-in constructs and functions that do the weak comparison *on their own*, without you having a choice. An example is the `switch`, which compares its `case` with the weak equality `==`, while the more recent `match` uses the strict comparison `===` (we will see both in Chapter 9). With `switch`, whether the value is `'4'` as a string or `4` as a number is the same: the conversion happens implicitly.

### The case of in_array()

Another case is the `in_array()` function, which checks whether a value exists inside an array (we will encounter it again in Chapter 12; in the meantime you can look at it in the PHP manual). It accepts three parameters: what to look for, where to look for it, and whether the comparison should be close or not (the third parameter is `false` by default, so weak comparison).

```php
$data = [4, 5, 'php'];

var_dump(in_array('5a', $data)); // PHP 7: bool(true) — PHP 8: bool(false)
var_dump(in_array(' 5', $data)); // bool(true) in both (only spaces)
var_dump(in_array(0, $data));    // PHP 7: bool(true)! — PHP 8: bool(false)
```

Full source: [listing-25.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-25.php)


The first case: in PHP 7 the string `'5a'` was converted to a number — it found the `5`, discarded the rest — then "found" it in the array; in PHP 8 no. With spaces only (`' 5'`) it works in both versions.
But the really tricky case is the third: we look for the `0` in an array which, as you can see, **does not contain any zeros**. In PHP 7 the result was `true`! Why? PHP compared `0` to `4`: different. Then `0` with `5`: different. Then `0` with the string `'php'`: and a non-numeric string, converted to a number, gives `0`. So `0 == 0` → found. A terrible bug, because PHP told us yes while the zero in the array is not there. From PHP 8 this no longer happens.

In any case, with `in_array()` we can (and generally must) pass the third parameter to `true` to force the strict comparison, which gives the correct result in all versions:

```php
var_dump(in_array('5a', $data, true)); // bool(false) everywhere
var_dump(in_array(0, $data, true));    // bool(false) everywhere
```

Full source: [listing-26.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-26.php)


Moral: If you are migrating code from PHP 7 to PHP 8, check all the places where you compare numbers and strings with `==`, `switch`, or functions like `in_array()`. Where you can, cast explicitly and compare closely; where you cannot, take this table into account.

## The spaceship operator

Let's now move on to operators that we certainly haven't studied in elementary algebra, but which exist in PHP as in other languages. The first, introduced with PHP 7, is the **spaceship** operator `<=>` — the "spaceship", due to the shape.

What does he do? Compare "less than, equal to, and greater" in one fell swoop: three comparisons in one. Returns:

- `-1` if the first operand is **less** than the second;
- `0` if they are **equal**;
- `1` if the first is **greater** than the second.

Let's check:

```php
$g = 0;
$h = 1;

$i = $g <=> $h;
var_dump($i); // int(-1) — the first value is less than the second
```

Full source: [listing-27.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-27.php)


(If your editor reports `<=>` as an error, check that linting is set to PHP 7 or higher: the code is perfectly valid.)

If the two values are equal we get zero, and if the first is greater we get one:

```php
var_dump(1 <=> 1); // int(0) — they are equal
var_dump(2 <=> 1); // int(1) — the first is greater
```

Full source: [listing-28.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-28.php)


It works with both variables and literals. And what is it for? With a single expression I get a value that tells me *what relationship there is* between the two operands, and I can then sort the three cases with an `if`/`elseif`/`else` (or with an `switch`, which we will study in Chapter 9). I anticipate the structure because it is very simple to understand:

```php
$g = 2;
$h = 1;

$i = $g <=> $h;

if ($i === 0) {
    echo 'g and h are equal';
} elseif ($i === -1) {
    echo 'g is less than h';
} else {
    echo 'g is greater than h';
}
// Output: g is greater than h
```

Full source: [listing-29.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-29.php)


With `$g = 1` it would print "g and h are equal", with `$g = 0` it would print "g is less than h". He is a very convenient operator: with just one condition I have everything I need.

## The ternary operator

Another operator to know is the **ternary**, which is called that because it works with three parts:

```text
condition ? value1 : value2
```

Full source: [listing-30.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-30.txt)


If the condition is true (`true`), the expression returns `value1`; otherwise it returns `value2`. Let's see it in practice:

```php
$val1 = 1;
$val2 = 1;

$ternary = ($val1 === $val2) ? 'they are equal' : 'they are different';
echo $ternary; // they are equal
```

Full source: [listing-31.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-31.php)


Two writing tips. First: when the condition is an expression (like here), always enclose it in round brackets — if it's a single value you can also omit them, but with round brackets you avoid any problems of precedence between PHP operators. Second: out of habit and correctness, I use single quotes for strings that do not contain variables, as I showed you in Chapter 6.

The ternary is the compact equivalent of a `if`/`else`:

```php
if ($val1 === $val2) {
    echo 'they are equal';
} else {
    echo 'they are different';
}
```

Full source: [listing-32.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-32.php)


Which of the two is better? Depends. For a simple expression like this I recommend the ternary: shorter, more immediate. However, if the logic becomes complicated, an explicit `if`/`else` is better, perhaps by supporting the result in a variable: it is a little clearer to read. It's not a question of speed, but of readability.

Note that I used three equal signs in the example, because I also want to check the type. Try changing the values: with `$val2 = 20` we get "they are different"; with `$val2 = '1'` (string) and the close comparison `===` we get "they are different", but if we switch to double equal `==` it comes back "they are the same" — it's still the same story as the cast we saw above.

## The null coalescing operator
With PHP 7 the **null coalescing** operator `??` also arrived, two question marks. Loosely translated it means: "give me the first of all the values ​​I list that is not `null`". This is similar to ternary, but instead of evaluating a true/false condition, it discards `null`.

We can use literal values:

```php
$result = null ?? 2 ?? 3;
var_dump($result); // int(2)
```

Full source: [listing-33.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-33.php)


The first value is `null`, so it is discarded; the second is `2`, which is not `null`: he is the result. If the second one was also `null`, we would get `3`:

```php
$result = null ?? null ?? 3;
var_dump($result); // int(3)
```

Full source: [listing-34.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-34.php)


And of course it works with variables too — it doesn't matter whether they are variables or literals:

```php
$val1 = null;
$val2 = 10;

$result = $val1 ?? $val2;
var_dump($result); // int(10)
```

Full source: [listing-35.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-35.php)


It is the perfect operator for assigning default values, as we will soon see.

## Assignment with null coalescing (PHP 7.4)

Let's take a look at null coalescing again with a practical case. Imagine reading a user's last name from the database, and not knowing whether the `last_name` column contains a value or `null`. We want to assign a default in that case:

```php
$lastName = null; // simulate the column read from the database

$lastName = $lastName ?? 'N/A';
echo $lastName; // N/A
```

Full source: [listing-36.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-36.php)


We're saying, "`$lastName` will be the same as the value it already has, but if that value is `null`, then use `'N/A'`." It works, but there is a repetition: the variable appears twice.

Since PHP 7.4 there is a shorter way: the **assignment operator with null coalescing** `??=`:

```php
$lastName ??= 'N/A';
echo $lastName; // N/A
```

Full source: [listing-37.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-8/en/parte-02/cap-08/listing-37.php)


The meaning is identical: "keep the value that is already in `$lastName`; but if it is `null`, assign the default value". If the variable already has a value, nothing happens and it remains as it is; otherwise it receives the default.

This operator is very convenient for cleaning up values: every time we fear that a value could be `null` — a database column, an optional parameter — we give it a default with a single line.

## In summary

- The `=` assignment operator **first** evaluates the entire expression on the right and **then** assigns the result to the variable on the left.
- The arithmetic operators are `+`, `-`, `*`, `/`, the modulus `%` (remainder of the division) and the exponential `**`; multiplication and division take precedence over addition and subtraction, and parentheses change the order of evaluation.
- `**` (since PHP 5.6, as an alternative to `pow()`) is right associative: `2 ** 3 ** 2` makes `512`, not `64`. When in doubt, use parentheses. For the square root there is the function `sqrt()`.
- `==` compares values ​​only (with automatic type casting), `===` compares values ​​**and** types; `!=` means different, `!==` not identical. Always prefer tight comparisons: for PHP `0`, `null` and `''` in weak comparison are equivalent, and a legitimate zero (a price!) can cause a condition to fail.
- Since PHP 8 the weak comparison between numbers and **non-numeric** strings has changed: `0 == "foo"` and `0 == ""` are now `false` (previously they were `true`), and `42 == "42abc"` is `false`. Be careful during migration, also for `switch` (weak comparison) and functions like `in_array()` (use the third parameter `true` for strict comparison).
- The spaceship `<=>` (PHP 7) does three comparisons in one: returns `-1` if the first operand is less, `0` if they are equal, `1` if it is greater.
- The ternary `condition ? value1 : value2` is the compact form of a `if`/`else`: use it for simple expressions, and put the condition in parentheses.
- Null coalescing `??` returns the first non-`null` value in the list; since PHP 7.4, `$var ??= 'default'` assigns the default only if the variable is `null`.
With these operators we are ready for the control structures of the next chapter: `if`, `elseif`, `else`, `switch`, `match` and the loops. Before continuing, take a few minutes to experiment in your editor: compare `null` with `0`, the empty string with `null`, a number with a string, and see the results you get.
