# 26. Inheritance, interfaces, traits and static members

After classes and objects, PHP offers a second set of tools, all devoted to a single purpose: **reusing** and **organizing** behavior without rewriting it. Inheritance, abstract classes, interfaces, traits, static members and class constants each solve a piece of this problem. But they should be used with measure, and it is worth saying so before we even begin: these tools help a lot when they *clarify* the model — when they make it more obvious how the things in your domain are shaped — and they complicate everything when you add them just to "do OOP". The criterion, in every section, will be the same: use the tool if it makes the code more understandable, not because it exists.

## Inheritance

One class can **extend** another, inheriting its properties and methods:

```php
<?php
class Animal
{
    public function sleeps(): string
    {
        return "zzz";
    }
}

class Dog extends Animal
{
    public function barks(): string
    {
        return "bau";
    }
}
```

Full source: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/en/parte-07/cap-26/listing-01.php)


`Dog` does not declare `sleeps()`, yet it can use it: it inherited it from `Animal`. The `extends` keyword establishes that every dog *is* also an animal, and this is the key to knowing when to use inheritance: it expresses an **"is a"** relationship. A dog is an animal, an `AdminController` is a `Controller`, a `SqlException` is an `Exception`. Use it only when that sentence is true in your domain. There is, however, a warning to keep in mind from the start: inheritance is the **tightest** bond two classes can have, because the child depends on the internal details of the parent. Changing the base class risks breaking all its children. That is why, when you only need to reuse some code — and there is no genuine "is a" relationship — **composition** (holding an object and delegating work to it) is almost always better than inheritance.

## Overriding methods

A child class can **redefine** an inherited method, giving it different behavior:

```php
<?php
class Cat extends Animal
{
    public function sleeps(): string
    {
        return "the cat sleeps on the sofa";
    }
}
```

Full source: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/en/parte-07/cap-26/listing-02.php)


`Cat` inherits `sleeps()` from `Animal`, but replaces it with its own version: this is the **override**. From now on, calling `sleeps()` on a cat runs the cat's code, not the animal's. There is an unwritten but important rule: an override should honor the "contract" of the original method — if `sleeps()` promises to return a string, the redefined version must keep doing so, otherwise code that uses `Animal` without knowing which concrete type it has in front of it will be caught off guard. Sometimes you do not want to replace the parent's behavior entirely, but to **add** something to it:

```php
<?php
return parent::sleeps() . " on the sofa";
```

Full source: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/en/parte-07/cap-26/listing-03.php)


`parent::` calls the version of the method defined in the parent class. This way you can reuse what the parent already does and then extend it, instead of rewriting it from scratch: it is the clean way to specialize a behavior without duplicating it.

## Final classes and methods

The `final` keyword does the opposite of inheritance: it **prevents** extending a class or overriding a method.

```php
<?php
final class Money
{
}
```

Full source: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/en/parte-07/cap-26/listing-04.php)


A `final` class cannot be extended; alternatively you can seal a single method:

```php
<?php
class Service
{
    final public function execute(): void
    {
    }
}
```

Full source: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/en/parte-07/cap-26/listing-05.php)


Why would you ever want to *prevent* inheritance, having just introduced it? Because every extension point is also a point of **fragility**: if a class can be extended and its methods overridden, you must guarantee it keeps working whatever the children do. `final` removes that worry and stabilizes a behavior that must not be altered — a value object like `Money`, for instance, where the calculation logic must stay exactly as it is. Many experienced developers adopt the "final by default" philosophy: make extendable only what you designed to be extended, and seal the rest.

## Abstract classes

An **abstract class** sits halfway between a normal class and an interface: it cannot be instantiated directly, and it can force its children to implement certain methods.

```php
<?php
abstract class Controller
{
    abstract public function index(): string;

    protected function render(string $view): string
    {
        return "render " . $view;
    }
}
```

Full source: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/en/parte-07/cap-26/listing-06.php)


`Controller` makes no sense on its own — `new Controller()` is an error — because it represents an incomplete concept: it lacks the implementation of `index()`, declared `abstract`, that is, promised but not written. Every concrete controller (a `HomeController`, a `UserController`) will have to extend it and supply its own `index()`. In exchange, though, it already inherits `render()`, which is written in full. This is exactly the strength of the abstract class: it **shares the code common** to all children and at the same time **imposes a partial contract**, the list of methods each one must complete. It is the *template method* pattern: the parent defines the skeleton, the children fill in the gaps. You will recognize this structure in the base `Controller` of Part IX.

## Interfaces

An interface takes the idea of a contract to the extreme: it declares **what** a class must offer, without saying **how**.

```php
<?php
interface Logger
{
    public function info(string $message): void;
}

class FileLogger implements Logger
{
    public function info(string $message): void
    {
        file_put_contents("app.log", $message . PHP_EOL, FILE_APPEND);
    }
}
```

Full source: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/en/parte-07/cap-26/listing-07.php)


The `Logger` interface contains no code: it only says that anyone who wants to be a logger must have an `info(string): void` method. `FileLogger` signs this contract with `implements Logger` and provides its version, which writes to a file. Tomorrow you could write a `DatabaseLogger` or a `NullLogger`: as long as they honor the interface, they are interchangeable for the rest of the code. And here lies the real advantage — programming **against the contract** and not against the implementation:

```php
<?php
function run(Logger $logger): void
{
    $logger->info("Application started");
}
```

Full source: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/en/parte-07/cap-26/listing-08.php)


`run()` does not depend on `FileLogger`: it depends on `Logger`, that is, on "something that knows how to do logging". It does not care which the concrete object is, as long as it honors the contract. This is the **dependency inversion principle** — the "D" of SOLID — and it will be the foundation of the container in Part IX: high-level code depends on abstractions, not on concrete classes. Note also the practical difference from classes: a class can implement **many** interfaces but extend **only one** class, which is why interfaces are the preferred tool for describing an object's capabilities.

## Trait

A **trait** solves a problem that neither inheritance nor interfaces handle well: reusing the same *code* in classes that have no "is a" relationship with one another.

```php
<?php
trait HasTimestamps
{
    public function touch(): void
    {
        $this->updatedAt = new DateTimeImmutable();
    }
}

class Post
{
    use HasTimestamps;
}
```

Full source: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/en/parte-07/cap-26/listing-09.php)


A `Post`, a `Comment` and a `User` are not the same thing, but they might all need a `touch()` method that updates the modification date. Putting it in a common base class would be forced — there is no genuine hierarchy — and repeating it in each would violate DRY. The trait offers the third way: `use HasTimestamps` pastes that method into `Post` as if it were written there. It is a **horizontal** reuse, cutting across hierarchies. Very handy, but with a risk to be aware of: the trait uses `$this->updatedAt`, a property it *does not declare* — it assumes the host class has it. This hidden dependency is the typical flaw of traits: if you overuse them, you end up with classes that expect properties and methods arrived from who-knows-which trait, and the code becomes hard to follow. Use them for small, well-defined behaviors, not as a shortcut to avoid designing.

## Class constants

A class constant is a fixed value, with a name, tied to the class:

```php
<?php
class Role
{
    public const ADMIN = "admin";
    public const USER = "user";
}

if ($role === Role::ADMIN) {
    echo "Access to the admin panel";
}
```

Full source: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/en/parte-07/cap-26/listing-10.php)


The value of constants lies in the comparison between `Role::ADMIN` and the bare string `"admin"`. If you write `"admin"` scattered across twenty places in the code and one day mistype one — `"admni"` — you have a silent bug: the condition is simply false, with no errors. With `Role::ADMIN`, instead, a typo in the constant's name is an immediate error ("undefined constant"), because PHP knows it. Constants give a name to "magic" values, centralize them in a single place, and make them typo-proof — exactly the roles that in the Part VI project appeared scattered as strings.

## Static properties and methods

A **static** member belongs to the class itself, not to individual instances:

```php
<?php
class Counter
{
    private static int $count = 0;

    public static function increment(): int
    {
        return ++self::$count;
    }
}

echo Counter::increment();
```

Full source: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/en/parte-07/cap-26/listing-11.php)


There is a single `$count`, shared by the whole class: you do not need to create an object to use it, you call it directly with `Counter::increment()`, and its value persists from one call to the next. This makes it handy for counters, stateless utilities and simple factories. But precisely because it is shared and always reachable, static state is in effect **global state**, with all of its flaws: it is hard to test (tests influence one another through that shared value), and it hides a dependency, because a function that calls `Counter::increment()` declares nowhere that it depends on `Counter`. Use `static` sparingly: it is fine for pure utilities and factories, much less for domain logic, where it makes tests and dependencies more rigid.

## `self` and `static`

When a static method needs to refer to its own class, you have two keywords, and the difference matters in hierarchies:

```php
<?php
class Model
{
    public static function make(): static
    {
        return new static();
    }
}
```

Full source: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/en/parte-07/cap-26/listing-12.php)


`self` refers to the class **in which the method is written**, and stays fixed there. `static`, by contrast, uses *late static binding*: it refers to the class **actually called** at runtime. The difference shows up with inheritance: if `User extends Model` and you call `User::make()`, the version with `new static()` returns a `User`, whereas `new self()` would always return a `Model`, ignoring the child. That is why `static` is important in factories and hierarchies where the method must produce the instance of the **child** class, not of the parent in which it was written.

## In summary

Inheritance, interfaces, traits and static members are powerful tools, each suited to a different kind of reuse: **inheritance** models the "is a" relationship (but it is the tightest bond, so use it with caution); **interfaces** define contracts and are the basis of dependency inversion; **abstract classes** share structure and impose a partial contract; **traits** reuse small behaviors horizontally; **constants** give a name to magic values; `static` handles functionality tied to the class rather than the instance, with the caution of global state. The right choice, every time, is the one that makes the code more understandable — not the one that crams in as many OOP concepts as possible.
