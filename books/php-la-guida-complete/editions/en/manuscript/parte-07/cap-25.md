# 25. Classes, objects, properties and constructors

So far you have written functions that take data, process it, and return a result. **Object-oriented programming** offers a different way to organize code: instead of keeping data (in variables and arrays) and behavior (in functions) separate, it gathers them together into a single unit. In PHP that unit is the **class**. A class describes a category of things — a car, a user, a bank account — stating what information those things carry and what they know how to do. An **object** is a concrete specimen of that category: the class `Car` is the concept "automobile", the individual object is *that* red car going 50 kph. The distinction between class and object is the same as between the recipe and the cake: there is one recipe, but the cakes that come out of it are many, and each has its own life.

This chapter introduces the basic building blocks: how to define a class, how to create objects, how to describe their state with properties and their behavior with methods, and how to protect that state so it always stays consistent. These are the foundations on which the project of Part VI and the whole enterprise architecture of Part IX rest.

## Define a class

```php
<?php
class Car
{
}
```

Full source: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-25/en/parte-07/cap-25/listing-01.php)


Even empty, this class is already something: you have defined a **new type**, which from now on stands alongside `int`, `string` and `array`. By convention a class name is written in **PascalCase**, with a capital initial and no spaces: `Car`, `RegisteredUser`, `OrderCart`. It is a convention, not a language requirement, but following it makes a class name instantly recognizable against a variable or a function. To create an object from the class you use `new`:

```php
<?php
$car = new Car();
var_dump($car);
```

Full source: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-25/en/parte-07/cap-25/listing-02.php)


The `new` keyword asks PHP to **instantiate** the class: it allocates a new object in memory and returns a reference to it, which here ends up in the variable `$car`. The `var_dump` shows something like `object(Car)#1 (0) { }`: an object of type `Car`, the first created (`#1`), with zero properties. The object exists, but it is an empty shell — it does not yet carry any interesting data. There is a detail worth fixing right away: every `new` produces a **distinct** object. If you wrote `new Car()` twice you would get two separate objects, with independent lives, exactly like two cakes out of the same recipe. And, unlike arrays, objects are passed **by reference**: assigning `$car` to another variable does not copy the object, it creates a second name for the same object. It is a difference that will have important practical consequences later on.

## Properties

**Properties** are the variables that belong to the object: they describe its **state**, that is, the information it carries at a given moment.

```php
<?php
class Car
{
    public string $color;
    public int $speed = 0;
}

$car = new Car();
$car->color = "red";
$car->speed = 50;
```

Full source: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-25/en/parte-07/cap-25/listing-03.php)


Each property is declared with a type (`string`, `int`) and may have an initial value: `$speed = 0` means every car is born stationary, while `$color` has no starting value and must be assigned before you read it. The `->` operator is the access key: `$car->color` reads or writes the `color` property of *that* object. And this is where the point of having distinct objects shows: if I create two cars and give one `color = "red"` and the other `color = "blue"`, the two values do not step on each other, because each property lives inside its own object. State is **per instance**, not shared: the class says *which* properties exist, each object keeps its own copy with its own values.

## Methods

If properties are the state, **methods** are the behavior: functions that live inside the class and can act on the object's state.

```php
<?php
class Car
{
    public int $speed = 0;

    public function accelerate(int $increment): void
    {
        $this->speed += $increment;
    }
}

$car = new Car();
$car->accelerate(20);
```

Full source: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-25/en/parte-07/cap-25/listing-04.php)


The difference between a method and any old function comes down to one word: `$this`. Inside a method, `$this` is **the object on which the method was called** — when you write `$car->accelerate(20)`, inside `accelerate` the variable `$this` *is* `$car`, and so `$this->speed` is the speed of that precise car. A method therefore does not work on data it receives from outside and then forgets: it works on the state of the object it belongs to, and its changes stay. After `accelerate(20)`, the `speed` property of `$car` is 20; calling it again makes it 40. It is this permanent bond between behavior and the data it operates on that sets the object apart from a mere function with parameters.

## Visibility

So far everything has been `public`, that is, accessible to anyone. But the real reason to use objects is being able to **hide** part of the state and control access to it. The keywords that govern visibility are three:

- `public`: accessible from outside;
- `protected`: accessible in the class and in its child classes;
- `private`: accessible only in the class.

```php
<?php
class Conto
{
    private float $saldo = 0;

    public function deposita(float $importo): void
    {
        if ($importo <= 0) {
            return;
        }

        $this->saldo += $importo;
    }

    public function saldo(): float
    {
        return $this->saldo;
    }
}
```

Full source: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-25/en/parte-07/cap-25/listing-05.php)


This example is the heart of the chapter, because it shows what encapsulation is really for. The balance is `private`: from outside you **cannot** write `$conto->saldo = -1000000`, because that property is invisible outside the class. The only way to make the balance grow is to go through `deposita()`, which checks the amount and rejects non-positive values. The result is a **guarantee**: whatever code uses this class, the balance can never be changed to an absurd value, because the rule that protects it lives *inside* the object, together with the data. This is the true promise of object-oriented programming — not "grouping functions", but keeping together a piece of data and the rules that guarantee its consistency, so that state cannot end up in invalid configurations. The conditions that must always hold true (the balance is not negative, the email is valid, the age is positive) are called **invariants**, and `private` is the tool that lets you defend them.

## Constructor

The **constructor** is a special method, `__construct`, that PHP calls automatically at the exact moment you create the object with `new`.

```php
<?php
class User
{
    private string $email;

    public function __construct(string $email)
    {
        $this->email = $email;
    }
}

$user = new User("john@example.com");
```

Full source: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-25/en/parte-07/cap-25/listing-06.php)


The value of the constructor is that it makes it impossible to create an **incomplete** object. Here you cannot obtain a `User` without an email: the signature `__construct(string $email)` forces whoever writes `new User(...)` to supply it up front. It is a subtle but decisive difference from assigning the properties one by one after creation, where nothing stops you from forgetting a piece and ending up with a half-built object. The constructor is therefore the right place for two things: the **mandatory data** without which the object makes no sense, and the **dependencies**, that is, the other objects this one needs to do its work (a database connection, a logger). Asking for dependencies in the constructor is the first step toward the *dependency injection* that will be the linchpin of the architecture in Part IX: an object declares what it needs, and receives it from outside at birth.

## Constructor property promotion

The pattern from the previous section — declare the property, receive it as a parameter, assign it with `$this->` — repeats so often that PHP 8 introduced a shortcut:

```php
<?php
class User
{
    public function __construct(
        private string $email,
        private string $name
    ) {
    }
}
```

Full source: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-25/en/parte-07/cap-25/listing-07.php)


By putting a visibility modifier (`private`, `public`, `protected`) in front of a constructor parameter, you tell PHP to do three things at once: declare the property, receive its value as an argument, and assign it. This code is exactly equivalent to the long version above, but without the triple repetition of each property's name. It is not just about typing less: less repetitive code means fewer places where a refactoring can forget something, and the constructor signature becomes a readable list of everything the object requires. You will see this form everywhere in modern PHP code, and you will use it heavily in Part IX.

## Setters and getters

Sometimes you still need to read or modify a property from outside, but want to keep control over *how*. Enter the **getters** (they read) and the **setters** (they modify):

```php
<?php
class User
{
    private string $email;

    public function setEmail(string $email): void
    {
        if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
            throw new InvalidArgumentException("Invalid email");
        }

        $this->email = $email;
    }

    public function getEmail(): string
    {
        return $this->email;
    }
}
```

Full source: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-25/en/parte-07/cap-25/listing-08.php)


Here the setter does not just copy the value: it **validates** it, and throws an exception if the email is malformed (exceptions are the subject of Chapter 30). This is exactly why keeping `email` private and going through `setEmail` pays off compared to leaving it public: you have a single point of control, and no one can slip an invalid email into the object. But watch out for a very common mistake: do **not** automatically generate getters and setters for every property. A public setter that just does `$this->x = $x`, with no validation, protects nothing — it is a public property with two lines of extra ceremony, and it betrays the whole point of encapsulation. Getters and setters are added when they are actually needed: to validate, to compute a value on the fly, or to preserve a stable interface while the internal implementation changes. If a property needs no protection, either make it public or — better still — pass it in the constructor and leave it read-only, as we will see shortly.

## Typed property

**Typed properties** — properties with a declared type — are a safety net:

```php
<?php
class Post
{
    public int $id;
    public string $title;
}
```

Full source: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-25/en/parte-07/cap-25/listing-09.php)


Declaring `public int $id` means telling PHP that property will always hold an integer. If you try to assign it a string that cannot be converted to a number, PHP raises a `TypeError` on the spot, instead of letting a wrong value in that will blow up who-knows-where later. There is more: a typed property with no initial value starts in an **uninitialized** state, and reading it before you have assigned anything raises an explicit error, not a silent `null`. That is exactly the behavior you want: better a clear error at the first wrong access than an unexpected `null` propagating through half the application before causing a crash far from the real cause. Types turn a class of bugs from "mysteries to debug at runtime" into "errors reported immediately".

## Readonly

Since PHP 8.1 you can declare a property `readonly`, that is, assignable only once:

```php
<?php
class UserId
{
    public function __construct(
        public readonly int $value
    ) {
    }
}
```

Full source: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-25/en/parte-07/cap-25/listing-10.php)


A `readonly` property can be written only once — normally in the constructor — and after that becomes immutable: any attempt to reassign it raises an error. Why want this? Because **immutability** eliminates a whole category of problems. A `UserId` created with value 42 will be 42 for its entire life: you can pass it between functions, share it, keep it in a data structure without fear that someone, somewhere, will change it under your feet. It is the ideal tool for **value objects** — small objects that represent a concept (an identifier, an amount, an email address) and whose identity coincides with their value — and for **DTOs**, the objects that carry data from one layer of the application to another without logic of their own. Combined with constructor property promotion, `readonly` makes defining an immutable object a matter of a few lines.

## In summary

Classes and objects serve to model your application's domain by putting together, in a single unit, the data and the rules that govern it: **properties** hold the state, **methods** define the behavior, **visibility** protects the invariants, the **constructor** guarantees an object is born already valid. Around these basics, modern PHP provides tools that make code more expressive and less verbose — constructor property promotion, typed properties, `readonly` — and that you will use constantly from here on. Keep in mind the central idea, the one that truly sets OOP apart from procedural programming: it is not about gathering functions around data, but about making it impossible, by construction, for that data to end up in an inconsistent state. It is the guarantee you will carry with you into the chapters on inheritance, on traits, and above all into the enterprise project of Part IX.
