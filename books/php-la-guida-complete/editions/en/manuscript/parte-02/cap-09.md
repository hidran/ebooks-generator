# 9. Control structures

Up to this point our scripts have run line by line, top to bottom, never deviating. Real programs, however, must make decisions and perform repeated actions: show a message only if the user is logged in, list all the records returned by a query, repeat a calculation until a condition is satisfied. This is what **control structures** are for, the topic of this chapter.

We will first see the conditional constructs — `if`/`elseif`/`else`, `switch` and the modern `match` introduced by PHP 8 — and then the loops: `while`, `do-while`, `for` and `foreach`. They are constructs that you will find, with almost identical syntax, in C, Java, JavaScript and many other languages: learning them well in PHP means having a solid foundation for all programming. To try the examples, all you need is a workbook (for example `control-structures`) with a file `index.php`, served by the integrated PHP server that we learned to start in the previous chapters:

```bash
php -S localhost:8000
```

Full source: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-01.sh)


## Making decisions: if, elseif, else

### The simplest condition

The `if` structure accepts a **control expression** between round brackets that must return a boolean value: if the expression is `true`, the code block between braces is executed; if `false` is valid, it is skipped.

Here the Boolean rule that we studied in Chapter 7 comes back into play and which is worth repeating: for PHP they are `false` the empty string, the number `0`, the string `"0"`, `null` (and a few other values); **anything else is converted to `true`**. All the control structures we'll see — `if`, `switch` and the others — work on a Boolean expression, and if the expression isn't already a Boolean, PHP does the casting automatically.

Let's start with a variable `$money` and the simplest possible verification:

```php
<?php

$money = 30;

if ($money) {
    echo 'You have money';
}
```

Full source: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-02.php)


Opening the page in the browser we see `You have money`: `30` is not among the "false" values, so the cast to boolean produces `true` and the `echo` is executed. Inside the brackets we can put any expression that returns a Boolean: a comparison like `$money > 100`, `$money <= 50` and so on.

We can also negate the expression with the operator `!` seen in Chapter 8:

```php
if (!$money) {
    echo 'You have no money';
}
```

Full source: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-03.php)


With `$money = 30` this block is not executed: `$money` is `true`, so `!$money` is `false`.

### else: the alternative

If we want to show a result even when the condition is false, we add a branch `else`:

```php
if ($money) {
    echo 'You have money';
} else {
    echo 'You have no money';
}
```

Full source: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-04.php)


With `$money = 30` appears `You have money`; if we assign `$money = 0` `You have no money` appears. The same goes for any value that PHP considers false: the constant `false`, the empty string `''` and the others seen above. Conversely, any value outside that list passes the `if` branch.

How to organize the two branches is a choice of style: we can check the "true" case first and put the "false" case in the `else`, or reverse the condition and swap the branches. The behavior does not change; choose the form that makes the code more readable.

### elseif: cascading multiple conditions

A single `if` with a single `else` is often not enough: we can chain multiple checks on the same variable with `elseif`. PHP accepts both the joined form `elseif` and the separated form `else if`: both are valid.

```php
<?php

$money = 30;

if ($money <= 10) {
    echo 'You can buy a pizza';
} elseif ($money > 10 && $money <= 20) {
    echo 'You can buy a pizza and a beer';
} elseif ($money > 20 && $money <= 30) {
    echo 'You can go to a restaurant';
} else {
    echo 'You can bring a friend to the restaurant';
}
```

Full source: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-05.php)


Conditions are evaluated from top to bottom and **only the first branch** whose condition is true is executed; the final `else` fires as the default option when no conditions pass. With `$money = 30` we get `You can go to a restaurant` (30 is greater than 20 and less than or equal to 30); with `10` we get `You can buy a pizza`; with `35` none of the conditions are true and the `else` is triggered: `You can bring a friend to the restaurant`.
We can use as many `elseif` as we want, or stop at a simple `if`/`else`. A practical tip: when there are a lot of `elseif` in cascade, it is usually best to switch to the `switch` construct, which we will see shortly.

### The alternative syntax for templates

There is a second syntax for `if`, used mostly when we mix PHP and HTML in a template and don't want to fill the markup with curly braces. A **colon** (`:`) is placed in place of the opening brace, and the construct ends with `endif;`. Between one part and the other we can close the PHP tag and write pure HTML:

```php
<?php $money = 35; ?>

<?php if ($money): ?>
    <h2>You have money</h2>
<?php else: ?>
    <h2>You have no money</h2>
<?php endif; ?>
```

Full source: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-06.php)


Opening the page we see the message inside an `<h2>`, exactly as if we had done `echo '<h2>You have money</h2>';` while staying inside PHP. So why use this form? The reason is practical: if the file passes into the hands of a web designer who is not used to PHP, with the brace syntax a deleted `echo` or a lost semicolon is enough to break the page. With the alternative syntax, however, HTML remains HTML: anyone can edit the markup without touching the PHP code. This is why you find it in almost all PHP templates (corresponding forms also exist for loops, such as `endwhile`, `endfor` and `endforeach`).

Two rules to remember. First: there shouldn't be too much logic in a view; if you end up with more than one `if` and one `elseif` inside a template, that logic is better off in a separate PHP file (a controller), not in the view. Second: **the two syntaxes cannot be mixed** — either you use braces or you use colons with `endif;`. Opening with a brace and closing with `endif;` (or vice versa) is a syntax error.

## The switch construct

When a chain of `if`/`elseif`/`elseif` always compares the same expression with different values, we can group it into a more readable `switch`. The `switch` evaluates the expression that we pass to it between brackets and compares it with the values ​​of the various `case`: as soon as it finds a match, it begins to execute the instructions from that point onwards.

However, pay attention to a detail that surprises many beginners: once the match has been found, the `switch` **continues to execute all subsequent lines**, even those of the other `case`, until it encounters an `break`. Let's see it now:

```php
<?php

$money = 1;

switch ($money) {
    case 1:
        echo 'You have 1 euro';
    case 2:
        echo 'You have 2 euros';
}
```

Full source: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-07.php)


What will appear in the browser? The answer would be just `You have 1 euro`, but instead **both** strings appear: `You have 1 euro` and `You have 2 euros`. It is the so-called *fall-through*, and it is a classic source of bugs in many applications. As soon as `switch` matches `1`, it does everything that follows until it finds an `break`.

### break: exit the switch

The `break` immediately exits the `switch`. Let's add it to the first `case`:

```php
switch ($money) {
    case 0:
        echo 'You have no money';
    case 1:
        echo 'You have 1 euro';
        break;
    case 2:
        echo 'You have 2 euros';
}
```

Full source: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-08.php)


With `$money = 1` now only `You have 1 euro` appears: once the match is found, the `echo` is executed, the `break` exits and the `case 2` is never reached. Note that the `case 0` has nothing to do with it: PHP examines it, finds no match, and moves on. If instead we remove the `break` from the `case 1`, the execution continues and two strings are printed. An `break` on the last `case` is technically useless (the `switch` ends anyway), but always be careful **where** you put the `break`: the result can change completely.

### default: when no case matches

As the final `else` in a chain of `if`, the `switch` can have a `default` branch that executes when no `case` is matched:

```php
switch ($money) {
    case 0:
        echo 'You have no money';
    case 1:
        echo 'You have 1 euro';
        break;
    case 2:
        echo 'You have 2 euros';
        break;
    default:
        echo 'Invalid value';
}
```

Full source: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-09.php)


With `$money = 3` `Invalid value` appears: 3 is not equal to 0, nor to 1, nor to 2, so we move on to `default`. With `$money = 0`, however, watch out for fall-through: the `break` is missing after the `case 0`, so we see `You have no money` followed by `You have 1 euro` (execution stops at `break` of `case 1`). If we want it to come out immediately with 0, we need to add the `break` there too. The `default`, however, fires only in the absence of matches: the fall-through from a previous `case` does not reach us if it first encounters a `break`.

### Group the cases

Fall-through is not just a danger: used on purpose, it is the idiomatic way to assign **the same block of statements to multiple values**. Just write some empty `case` one on top of the other:

```php
    case 3:
    case 4:
        echo 'You have 3 or 4 euros';
        break;
```

Full source: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-10.php)


With both `$money = 3` and `$money = 4` `You have 3 or 4 euros` appears: the `case 3` does not contain instructions, so the execution "falls" in the `case 4` and stops at `break`.

Two style notes. If you find a block of large code inside an `case`, it is a sign that the application is not designed well: that code should be in a function, which the `case` simply calls. You can, however, enclose the body of an `case` in braces — it's not required, but it helps the editor (and you) see where each branch begins and ends. Finally, after the value of `case` PHP also accepts the semicolon instead of the colon (`case 1;`), but it is a rarely used form: stick to the colon, which is the convention in PHP as in other languages.

### The weak comparison: an exam pitfall

There is a behavior of `switch` that you absolutely need to know. Let's try:

```php
$money = false;

switch ($money) {
    case 0:
        echo 'You have no money';
        break;
    // ...
    default:
        echo 'Invalid value';
}
```

Full source: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-11.php)


What do you expect? One might say `Invalid value`: `false` is not `0`. And instead `You have no money` appears. Why? Because it compares `switch` with the **weak equality** (`==`), not with the strict one (`===`): when it has to compare `false` with the integer `0`, PHP implicitly casts `false` to an integer, which is `0`, and `0 == 0` is true. If you want the comparison to occur on a "true" integer, you can explicitly cast the value before the `switch` — but always keep in mind that if you don't, PHP does it for you according to its own rules.

These PHP "tricks" need to be learned well: they're exactly the kind of question you might encounter on the **Zend Certified Engineer** exam, the standard PHP certification, and they're also the kind of detail that generates sneaky bugs in production code. With practice they will become natural — and in the next paragraph we see the construct that PHP 8 introduced to eliminate this problem.

## match: The modern PHP 8 switch

From PHP 8 onwards there is a construct called **`match`** which solves both weaknesses of the `switch`: it does the **strict comparison** (value *and* type, like `===`) and it is an **expression**, i.e. it returns a value that we can assign to a variable. An `switch`, on the contrary, returns nothing: writing `$test = switch (...)` is a syntax error, and the editor immediately reports it to us.

### The syntax

`match` evaluates the expression in brackets and compares it with the "keys" of its branches, written with the same `=>` arrow that PHP uses for associative key-value arrays: on the left the value (or values) to compare, on the right the expression to evaluate — and return — in case of match. Unlike `switch` no `break` is needed: once the match has been found, `match` evaluates that branch and exits. The braces here are a mandatory part of the syntax, and the branches are separated by commas.

Let's take the example of the comparison with `false` and compare the two constructs:

```php
<?php

$money = false;

// switch: weak comparison
switch ($money) {
    case 0:
        echo 'You have no money (switch)';
        break;
}

// match: strict comparison
match ($money) {
    1 > 2 => print 'false',
    0     => print 'You have no money',
    1     => print 'You have 1 euro',
    2     => print 'You have 2 euros',
};
```

Full source: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-12.php)


The `switch` prints `You have no money (switch)`: casts and `false == 0`. The `match` instead prints `false`: the comparison is close, therefore `$money` (which is `false`) **does not** correspond to the integer `0`; corresponds instead to the first branch, because the expression `1 > 2` is exactly `false`. Already from this example you see two things: `match` does not do any casting, and as the "key" of a branch we can use any expression, not just literal values.

A curiosity about the example: in the branches we used `print` instead of `echo`. The reason is that each branch of `match` must be an **expression** that produces a value, and `echo` is not; `print` instead prints on screen *and* always returns `1`. In fact, if we capture the result:

```php
$result = match ($money) {
    0 => print 'You have no money',
    // ...
    default => print 'None of the values'
};

var_dump($result); // int(1)
```

Full source: [listing-13.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-13.php)


`var_dump($result)` shows `int(1)`: the value returned by `print`. If, however, we want the branch to return the string without printing it, we could use `print_r($value, true)` — with `true` as the second parameter, `print_r()` does not print but **returns** the string — but in reality there is no need to bother with any function: just put the string directly as the value of the branch. It is the cleanest and most used form:

```php
$result = match ($money) {
    0      => 'You have no money',
    1      => 'You have 1 euro',
    2      => 'You have 2 euros',
    3, 4   => 'You have 3 or 4 euros',
    default => 'None of the values'
};

echo $result;
```

Full source: [listing-14.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-14.php)


Note the branch `3, 4`: to associate multiple values with the same result you don't need the cascading empty `case` of the `switch`, just list the values separated by commas. After the last branch the comma is optional: you can omit it or leave it (leaving it is convenient when adding branches at the end). And remember that `match (...) { ... }` used as an instruction must be closed with a semicolon.

### default is (almost) mandatory

Let's do the strict type comparison test again. If in one `switch` we write `case 3:` and pass the **string** `'3'`, the implicit cast transforms it into a number and the correspondence is triggered. With `match`, the string `'3'` and the integer `3` are values ​​of different types: no match. And if no branch matches and there is no `default`, `match` doesn't stay silent like the `switch`: it throws a fatal error:

```text
PHP Fatal error:  Uncaught UnhandledMatchError:
Unhandled match case of type string
```

Full source: [listing-15.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-15.txt)


So: while in `switch` the `default` is always optional, in a `match` you have to put the branch `default` every time you are not *certain* that the value corresponds to one of the branches — otherwise you have to handle the exception with a block `try`/`catch`, which we will study in Chapter 32.

### switch or match?

Let's summarize the differences:

| | `switch` | `match` |
|---|---|---|
| Returns a value | no | yes (it's an expression) |
| Comparison type | weak (`==`), with implicit cast | narrow (`===`), value and type |
| `break` | necessary to avoid fall-through | no use |
| `default` | optional | necessary if the value may not match (otherwise `UnhandledMatchError`) |
| Body of branches | more instructions for `case` | only one expression per branch |

The last line deserves a clarification: in a branch of `match` you cannot put multiple instructions separated by semicolons — the structure works like an array of key-value pairs. If you need multiple actions in a branch, write a function and call it as the branch value: the call is an expression and its result becomes the return value.

My advice, from PHP 8 onwards: if you need to strictly compare a value and return a result (or call a function), use `match` — the syntax is much simpler and cleaner. However, if for each value you need to perform several actions in sequence, `switch` is still convenient.

## The while and do-while loops

Let's move on to cycles. The **`while`** construct literally translates to "while": *while* the expression in parentheses is true, PHP executes the following statement — or the block of statements between braces. The condition is checked **at the start** of each lap.
The **`do-while`** does the same thing, but checks the condition **at the end**: the block is then executed at least once, and only then is it decided whether to repeat. It's the only difference between the two.

### while: the condition before

Let's start with a loop that prints the numbers 1 through 10:

```php
<?php

$i = 1;

while ($i <= 10) {
    echo $i . '<br>';
    $i++;
}
```

Full source: [listing-16.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-16.php)


The numbers from 1 to 10 appear in the browser, one per line. Let's analyze the pieces. Before the loop we initialize the `$i` counter to 1. The `$i <= 10` condition is checked at each loop; inside the block we print the value and — crucially — we **increment** it with the operator `++` seen in Chapter 8 (the postfix form is fine here, since we are not assigning the result to any variable). Since there are two instructions, the block must be enclosed in braces.

What would happen without the increase? `$i` would remain at 1 forever, always less than or equal to 10, and the loop would run **infinitely**, blocking the script. It's the classic error with `while`: always make sure that something inside the loop sooner or later causes the condition to become false.

What if we initialize `$i = 11`? The browser shows nothing: the condition is false from the first check and the body of the loop is not executed even once.

### do-while: at least one execution

Let's rewrite the same cycle in the variant `do-while`, starting from `$i = 11`:

```php
$i = 11;

do {
    echo $i . '<br>';
    $i++;
} while ($i <= 10);
```

Full source: [listing-17.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-17.php)


This time the browser shows `11`. The `do` block executes immediately: prints 11, increments to 12, and only then checks the condition — 12 is not less than or equal to 10, so the loop doesn't repeat. If instead we start from `$i = 1`, we obtain the numbers from 1 to 10 exactly as with `while`. The rule to remember: **`do-while` executes the body at least once**, `while` can never execute it.

### A practical example: generating an HTML list

Let's use the `while` for something more concrete: iterate through an array of colors and display it as an HTML list. We don't know a priori how many elements the array contains — we could count them by eye, but there's no need: the PHP function `count()` tells us how many elements an array has.

```php
<?php
$ar = ['red', 'blue', 'green', 'yellow'];
$total = count($ar);
?>
<!DOCTYPE html>
<html>
<head>
    <title>while loop</title>
    <style>
        body {
            background: #ccc;
            color: #000;
            font-size: 24px;
        }
    </style>
</head>
<body>
    <ul>
        <?php
        $i = 0;
        while ($i < $total) {
            echo "<li>{$ar[$i]}</li>";
            $i++;
        }
        ?>
    </ul>
</body>
</html>
```

Full source: [listing-18.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-18.php)


We wrote a complete HTML page — doctype, `<head>` with a title (always put one) and a minimum of CSS to make the list readable — and inside the `<ul>` we opened PHP to generate the entries with the loop. `red`, `blue`, `green`, `yellow` appear in a list in the browser: we generated HTML dynamically from PHP.

Two important details. First: the counter starts at **zero**, because arrays in PHP are indexed from position 0. Second: the condition uses `<` and not `<=`, because the last valid index is `$total - 1` — with four colors, the total is 4 but the positions are 0, 1, 2, 3.

And here too, watch out for the increment: while writing this example it is very easy to forget `$i++` and find yourself with the page turning endlessly. If this happens to you, stop the browser, add the increment and reload.

This pattern — a loop that loops through a structure and transforms it into HTML — is exactly what you'll use all the time in PHP, for example to display on screen the list of records that a query returns from a database table. For arrays, however, we will soon see more convenient constructs.

## The for loop

The cycle **`for`** compacts into a single line the three ingredients that we wrote in the `while`: initialization, condition and increment.

```php
for (expression1; expression2; expression3) {
    // loop body
}
```

Full source: [listing-19.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-19.php)


- **expression1** is used to initialize the variables and is executed only once, at the beginning;
- **expression2** is checked at the beginning of each round: if it is `true` the cycle continues, otherwise it exits;
- **expression3** is executed at the end of each round (typically it is the increment of the counter).

None of the three are mandatory: they can be omitted leaving the semicolons.
Let's take the color array again — add a fifth color, `pink` — and redo the list with the `for`. This time for output we use the interpolation in the double quotes that we studied in Chapter 7, with the braces around the array element:

```php
<?php

$ar = ['red', 'blue', 'green', 'yellow', 'pink'];

for ($i = 0; $i < count($ar); $i++) {
    echo "<li>{$ar[$i]}</li>";
}
```

Full source: [listing-20.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-20.php)


It works, but we can improve it. The second expression is reevaluated **every loop**: As it is, `count($ar)` is called for every element of the array, to no avail — the number of elements doesn't change during the loop. It is best to calculate it only once. We can do it before the loop (`$tot = count($ar);`), or take advantage of the fact that in the first expression of the `for` we can put **multiple initializations separated by commas**, executed only the first time:

```php
for ($i = 0, $tot = count($ar); $i < $tot; $i++) {
    echo "<li>{$ar[$i]}</li>";
}
```

Full source: [listing-21.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-21.php)


The result is identical, but `count()` is called only once.

### break and continue

Inside a loop — `for`, `while`, or `do-while` — we can use two flow control statements. We see them on the `for` because that is where they are used most often, but they apply to all cycles.

**`break`** immediately exits the loop, as already seen for the `switch`. Suppose we want to show only the first three colors:

```php
for ($i = 0, $tot = count($ar); $i < $tot; $i++) {
    echo "<li>{$ar[$i]}</li>";

    if ($i == 2) {
        break;
    }
}
```

Full source: [listing-22.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-22.php)


The indices start from zero, so the third element is `$i == 2`: the page shows `red`, `blue`, `green` and then the `break` breaks the loop — `yellow` and `pink` they are never printed. (We could have achieved the same result by changing the `for` condition, but `break` is the right choice when the interrupt depends on an internal loop check.)

**`continue`** however, it does not exit the loop: **jumps to the next round**, ignoring all the instructions that follow in the current block. Suppose we don't want to show `pink`:

```php
for ($i = 0, $tot = count($ar); $i < $tot; $i++) {
    if ($ar[$i] == 'pink') {
        continue;
    }

    echo "<li>{$ar[$i]}</li>";
}
```

Full source: [listing-23.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-23.php)


When the current value is `pink`, the `continue` takes you directly to the next round (the `$i++` increment is still performed) and the `echo` below is not reached: the list stops at `yellow`, without `pink`.

A style note that I will repeat often: in the examples I **always use braces**, even when the block contains only one statement and braces would not be mandatory. It's a question of correctness and clarity of the code: it prevents errors when you add a second statement to the block in the future.

## Nested loops

Loops can be **nested**: one loop inside another. Suppose we want to display our list of colors three times. We wrap the existing `for` into an external `for` with a second counter, `$j`:

```php
for ($j = 0; $j < 3; $j++) {
    for ($i = 0, $tot = count($ar); $i < $tot; $i++) {
        echo "$j {$ar[$i]}<br>";
    }
}
```

Full source: [listing-24.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-24.php)


The internal loop is repeated in full at each turn of the external one: in the browser we see the five colors three times, each preceded by the number of the external loop (0, 1, 2) thanks to the interpolation of `$j` in the string.

To better distinguish one round from another, we add a horizontal line after the last element of each list. The index of the last color (`pink`) is 4 — the positions are 0, 1, 2, 3, 4 — so:

```php
for ($j = 0; $j < 3; $j++) {
    for ($i = 0, $tot = count($ar); $i < $tot; $i++) {
        if ($i == 4) {
            $hr = '<hr>';
        } else {
            $hr = '';
        }

        echo "$j {$ar[$i]}<br>" . $hr;
    }
}
```

Full source: [listing-25.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-25.php)


Now the three blocks (round 0, round 1, round 2) are separated by a horizontal line.

### break and continue with more levels

Here's a detail that few people know: in PHP both `break` and `continue` accept a **numeric argument** that indicates how many nesting levels to exit or which level to continue.

Let's try to stop everything when the outer loop reaches round 1, putting the test **inside the inner loop**:

```php
for ($j = 0; $j < 3; $j++) {
    for ($i = 0, $tot = count($ar); $i < $tot; $i++) {
        if ($j == 1) {
            break; // exits only the inner loop!
        }

        echo "$j {$ar[$i]}<br>";
    }
}
```

Full source: [listing-26.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-26.php)


The result is not what we wanted: we see the colors of lap 0 and **also those of lap 2**. The simple `break` (equivalent to `break 1`) only exits the loop it is in — the inner one; the outer loop continues, and on round 2 the condition `$j == 1` is no longer true. To exit **both** loops we need to write:

```php
        if ($j == 1) {
            break 2; // exits both the inner loop and the outer loop
        }
```

Full source: [listing-27.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-27.php)


Now we only see the colors of lap 0: once we reach `$j == 1`, `break 2` crosses two levels of constructs — and in the counting of levels the `for`, the `while`, the `do-while` and also the `switch` counts — and the execution resumes after the outer loop.

The same numeric argument applies to `continue`. If instead of exiting we just want to **skip round 1** of the outer loop, showing round 0 and round 2:

```php
        if ($j == 1) {
            continue 2; // skips to the next iteration of the OUTER loop
        }
```

Full source: [listing-28.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-28.php)


`continue 2` abandons the current lap of the inner loop *and* of the outer loop, passing directly to `$j = 2`: the lists of laps 0 and 2 appear in the browser, without lap 1. The number after `break` or `continue`, therefore, indicates how many nesting levels the instruction must go through; without number, it acts only on the innermost cycle.

### A practical example: multiplication tables

Let's close the nested loops with a classic example: generating the multiplication tables. We use an outer loop for the multiplicand (from 0 to 10) and an inner loop for the multiplier (we could also do vice versa):

```php
<?php

for ($i = 0; $i <= 10; $i++) {
    for ($j = 0; $j <= 10; $j++) {
        echo "$i x $j = " . ($i * $j) . '<br>';
    }
    echo '<hr>';
}
```

Full source: [listing-29.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-29.php)


For each value of `$i`, the inner loop iterates `$j` from 0 to 10 and prints multiplicand, multiplier, and result; the horizontal line after each internal loop separates one times table from the other. In the browser we see the multiplication table for 0 (all zeros), that for 1, and so on up to that for 10: `0, 10, 20, 30... 100`. It works correctly.

As an exercise, try improving the presentation: display the multiplication tables side by side using HTML tables — an external table with a column for each multiplication table, and inside each column an ​​internal table with multiplication rows. Add some CSS to color the backgrounds – this is a great way to practice nested loops and HTML generation.

## The foreach loop

We scrolled through the arrays with `while` and with `for`, manually managing counter, `count()` and increment. However, PHP has a loop designed specifically for this: **`foreach`**. It's very convenient for iterating through any array — indexed, associative key-value, or multidimensional — and it also works on objects: by iterating an object, `foreach` iterates through its public properties as if they were key-value pairs (protected and private properties are not accessible from the outside; more on that in Part VII).

### The basic shape

The syntax: `foreach`, then in brackets the array (or the variable that contains it), the keyword `as` and a variable that will receive the current value at each turn. You choose the name of the variable:

```php
<?php

$ar = ['red', 'blue', 'green', 'yellow', 'pink'];

foreach ($ar as $val) {
    echo "<h1>$val</h1>";
}
```

Full source: [listing-30.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-30.php)


`red`, `blue`, `green`, `yellow`, `pink` appear in the browser, each in a nice `<h1>`. No counter, no `count()`, no increment: `foreach` scrolls all the elements by itself, from the first to the last.

### Keys and values

If we also need **keys**, we use the arrow form `=>` — the same key-value syntax as associative arrays:

```php
foreach ($ar as $key => $val) {
    echo "<h1>$key -> $val</h1>";
}
```

Full source: [listing-31.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-31.php)


With our indexed array the keys are numeric: `0 -> red`, `1 -> blue`, and so on up to `4 -> pink`.

The great thing is that it works identically with string keys, and even with "mixed" arrays. Let's create a second array in which the first two colors have an Italian key and the others remain without:

```php
$ar2 = ['red' => 'red', 'blue' => 'blue', 'green', 'yellow'];

foreach ($ar2 as $key => $val) {
    echo "<h1>$key -> $val</h1>";
}
```

Full source: [listing-32.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-32.php)


The output shows `red -> red`, `blue -> blue`, `0 -> green`, `1 -> yellow`: for elements without an explicit key PHP automatically assigns numeric keys starting from 0, and `foreach` seamlessly loops through both string and numeric keys in the same array — which not all iteration constructs of other languages, JavaScript in the lead, can do it with the same naturalness.

### Change array: value by reference

Normally `$val` is a **copy** of the current value: modifying it does not affect the array. But if we prepend the ampersand `&`, the variable becomes a **reference** to the array element, and we can modify the array from inside the loop. For example, we make all colors uppercase with the `strtoupper()` function:

```php
foreach ($ar as &$val) {
    $val = strtoupper($val);
}

var_dump($ar);
```

Full source: [listing-33.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-33.php)


The `var_dump()` confirms that the values ​​have changed **within the array**: `RED`, `BLUE`, `GREEN`, `YELLOW`, `PINK`.

Be careful, though: there is a famous trap. After the loop ends, `$val` **continues to be a reference to the last element** of the array. If you reuse that variable later in the script:

```php
$val = 'no value';

var_dump($ar); // the last element is now 'no value'!
```

Full source: [listing-34.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-34.php)


...you're not assigning to just any variable: you're overwriting the last element of the array — instead of `PINK` there's now `no value`. To avoid the problem, **after a `foreach` for reference always make the `unset()` of the variable**:

```php
foreach ($ar as &$val) {
    $val = strtoupper($val);
}
unset($val); // remove the reference

$val = 'no value'; // now it is a regular variable
var_dump($ar);          // the array is intact: PINK is still there
```

Full source: [listing-35.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-35.php)


With `unset($val)` the variable no longer refers to the array, and any subsequent use can no longer corrupt it. I'll tell you from experience: I've had a bug exactly like this — a `foreach` for closed reference without `unset()`, the same variable reused later, and the main array value silently overwritten. Always be careful.

### Multidimensional arrays

What happens if the elements of the array are themselves arrays? Let's build one:

```php
$ar3 = [
    ['a', 'b', 'c'],
    [1, 2, 3],
];
```

Full source: [listing-36.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-36.php)


At position 0 there is an array of letters, at position 1 an array of numbers (remember: PHP automatically increments the key counter). If we try the simple `foreach`:

```php
foreach ($ar3 as $val) {
    echo "<h1>$val</h1>";
}
```

Full source: [listing-37.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-37.php)


PHP warns us with a warning: `Array to string conversion`. Right: each `$val` here is an array, and you can't make the `echo` like it's a string. The solution is to nest a second `foreach` that iterates through the internal array:

```php
foreach ($ar3 as $val) {
    foreach ($val as $v) {
        echo "<h1>$v</h1>";
    }
}
```

Full source: [listing-38.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-9/en/parte-02/cap-09/listing-38.php)


Now it works: the external `foreach` scrolls the main array, the internal one scrolls the array contained in each value, and on the screen appear `a`, `b`, `c`, `1`, `2`, `3`.

With this you already have a lot of firepower: PHP is very strong on arrays and, when you use it together with a database, loops will be the bread and butter — and you will almost always end up using the `foreach`. Study it well and experiment with your own examples.

## In summary
- **`if`/`elseif`/`else`** execute blocks of code based on a Boolean expression; PHP automatically casts to boolean according to its rules (`0`, `''`, `'0'`, `null`, `false` are false). `elseif` and `else if` are equivalent.
- In the templates we use the **alternative syntax** with a colon and `endif;`, which allows you to mix PHP and HTML without braces; the two syntaxes cannot be mixed.
- **`switch`** compares an expression with multiple `case` using **weak** equality (`==`, with implicit cast) and continues execution (*fall-through*) until it finds a **`break`**; `default` handles unmatched values. Cascading `case` voids group multiple values ​​on the same action.
- **`match`** (since PHP 8) is an expression: returns a value, uses **strict** comparison (`===`), does not require `break`, accepts multiple comma-separated values, and throws `UnhandledMatchError` if no branch matches and `default` is missing. Each branch contains only one expression: for multiple actions, call a function.
- **`while`** checks the condition at the beginning (the body may never be executed); **`do-while`** checks it at the end (the body is executed at least once). Always make sure something makes the condition false, or the loop will be infinite.
- **`for`** brings together initialization, condition and increment; the first expression accepts multiple comma-separated initializations — convenient for calculating `count()` only once instead of every round.
- **`break`** exits the loop, **`continue`** jumps to the next round; with a numeric argument (`break 2`, `continue 2`) act on multiple levels of nested loops.
- **`foreach`** is the natural loop for arrays: `foreach ($ar as $val)` for values, `foreach ($ar as $key => $val)` for keys and values; with `&$val` you modify the array by reference — but always remember to do **`unset($val)`** after the loop. For multidimensional arrays multiple `foreach` are nested.
