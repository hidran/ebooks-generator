# 27. Modern types, enums and magic methods

Recent versions of PHP have turned a language historically "permissive" about types into a tool capable of expressing precisely what a function accepts and what it returns. Union types, intersection types, nullable, enums, the nullsafe operator, magic methods and property hooks are the pieces of this evolution: they let you say more to the reader and to the PHP engine, and let errors surface sooner. But almost all of them also have a "cunning" side that, used without discipline, hides decisions instead of making them. Let us look at them one by one, always keeping an eye on *when* they are really useful.

## Union type

A **union type** declares that a value may be one of several types:

```php
<?php
function format_id(int|string $id): string
{
    return (string) $id;
}
```

Full source: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/en/parte-07/cap-27/listing-01.php)


`int|string` says that `format_id` accepts an integer **or** a string, and nothing else. It is honest and useful when a function really does receive different forms of the same concept — an id that sometimes arrives as a number and sometimes as a string. But beware of overuse: a type serves to *restrict* what can pass, and it is a promise that whoever reads the signature can trust certain guarantees. If you widen the union until it accepts almost anything, the promise empties out. Do not use union types to avoid a design decision: if a value can be "anything", the type is not helping you, it is only letting you postpone the problem.

## Nullable type

A particular and very frequent case of union is the one with `null`:

```php
<?php
function find_user(int $id): ?array
{
    // returns array or null
}
```

Full source: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/en/parte-07/cap-27/listing-02.php)


The question mark before the type — `?array` — is shorthand for `array|null`. It is the typical signature of `find` functions, where not finding the record **is not an error** but a normal, expected outcome: you look for user 42, and it might not be there. The value of this type is that it makes absence **explicit in the signature**: whoever calls `find_user()` sees immediately that the result may be `null` and knows they must handle it, instead of discovering it with a runtime error when they try to use an array that is not there. The type turns "maybe missing" from a surprise into declared information.

## Intersection type

If the union asks for "one *or* the other", the **intersection type** asks for "one *and* the other together":

```php
<?php
function export(Iterator&Countable $items): void
{
    echo count($items);
}
```

Full source: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/en/parte-07/cap-27/listing-03.php)


`Iterator&Countable` means that `$items` must satisfy **both** contracts: it must be iterable *and* countable. Inside the function you can therefore both loop over it (because it is `Iterator`) and pass it to `count()` (because it is `Countable`), with the guarantee the type gives. It is a rarer tool than the union, but valuable when a function needs several capabilities from an object at once: instead of accepting a specific concrete type, you compose the requirements from interfaces, staying open to any class that implements them.

## Nullsafe operator

Since PHP 8 the `?->` operator walks a chain of objects, stopping at the first `null`:

```php
<?php
$city = $user?->profile?->address?->city;
```

Full source: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/en/parte-07/cap-27/listing-04.php)


Without `?->`, if `$user` has no profile, `$user->profile->address` would blow up with an error on `null`. With the nullsafe, as soon as one link in the chain is `null`, the whole expression returns `null` and stops, without raising errors: `$city` will simply be `null`. It is handy for navigating nested optional structures, but it hides a risk. If that chain contains an object that *should always be there* — a user without a profile is inconsistent data, not a legitimate possibility — the nullsafe turns a bug into a silent `null` that propagates. Use it where absence is genuinely expected, not to silence states that ought to be mandatory.

## Enum

An **enum** represents a **closed** set of named values:

```php
<?php
enum Role
{
    case Admin;
    case User;
}
```

Full source: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/en/parte-07/cap-27/listing-05.php)


In the previous chapter we used class constants to give names to roles; the enum takes a step further and makes them a **type** in their own right. `Role::Admin` and `Role::User` are not strings: they are the only two possible values of `Role`, and PHP knows it. The difference shows in how you can type a function:

```php
<?php
function can_delete(Role $role): bool
{
    return $role === Role::Admin;
}
```

Full source: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/en/parte-07/cap-27/listing-06.php)


`can_delete(Role $role)` accepts **only** a value of `Role`: you cannot pass it a misspelled `"amdin"`, nor an invented `"superuser"`. A whole category of bugs — those where a wrong string slips into a function — simply becomes impossible, because the type blocks it before the code even runs. This is the great advantage of enums over constants: they not only give a name to values, they **restrict the set** of what can circulate.

## Backed enum

A **backed enum** associates a scalar value (a string or an integer) with each case:

```php
<?php
enum Role: string
{
    case Admin = "admin";
    case User = "user";
}
```

Full source: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/en/parte-07/cap-27/listing-07.php)


The "pure" enum of the previous section lives only in memory; but sooner or later a role must be **saved in the database** or sent in a JSON response, and there you need scalar values, not PHP objects. The backed enum acts as a bridge: each case has a `value` (`"admin"`, `"user"`) to persist, and two methods to make the reverse trip, from the value back to the enum:

```php
<?php
$role = Role::from("admin");
echo $role->value;
```

Full source: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/en/parte-07/cap-27/listing-08.php)


The choice between the two conversion methods is a security decision. `from()` throws an exception if the value matches no case: you use it when the value *must* be valid and an out-of-set value is an error to blow up. `tryFrom()`, instead, returns `null` on a failed match: you use it at the boundary with untrusted data — a request parameter, an old database row — where an unexpected value should be handled gracefully, not with a crash. The distinction mirrors exactly the *fail-loud* / *fail-closed* logic seen in the Part VI project.

## Methods in enums

An enum is not only a list of values: it can also have **methods**.

```php
<?php
enum Role: string
{
    case Admin = "admin";
    case User = "user";

    public function label(): string
    {
        return match ($this) {
            self::Admin => "Administrator",
            self::User => "User",
        };
    }
}
```

Full source: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/en/parte-07/cap-27/listing-09.php)


The `label()` method returns the readable label of the role, choosing it with a `match` on the current case. The advantage is not merely aesthetic: this way the **role-related behavior sits next to the possible values**, inside the same type, instead of being scattered across `if`s spread throughout the application. It is the principle of cohesion — what changes together stays together. And there is a bonus from `match`: if tomorrow you add a `case Editor` and forget to give it a label, PHP raises an error because the `match` is no longer exhaustive. The type forces you to leave no gaps.

## Magic method

**Magic methods** are special methods that PHP calls *automatically* in certain situations, without you invoking them explicitly. You recognize them by the two initial underscores. They are powerful precisely because they are implicit — but it is that same implicitness that makes them dangerous, because they hide what actually happens.

### `__get()`

```php
<?php
class Data
{
    private array $values = [];

    public function __get(string $name): mixed
    {
        return $this->values[$name] ?? null;
    }
}
```

Full source: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/en/parte-07/cap-27/listing-10.php)


PHP invokes `__get()` when you access a property that is **inaccessible or nonexistent**: writing `$data->something`, if `something` is not a public property, this method fires with `"something"` as its argument. Here it returns the value from the internal array, effectively realizing an object with "dynamic" properties, decided at runtime. Handy for generic containers, but with a heavy cost: looking at the class you can no longer tell *which* properties really exist, the IDE cannot complete them, and no static analysis tool can check them. You have traded clarity for flexibility.

### `__call()`

```php
<?php
class Proxy
{
    public function __call(string $name, array $arguments): mixed
    {
        throw new BadMethodCallException("Method $name not found");
    }
}
```

Full source: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/en/parte-07/cap-27/listing-11.php)


`__call()` is the equivalent of `__get()` for methods: PHP invokes it when you call an **inaccessible** method, passing it the name and the arguments. Here the class uses it virtuously, to *fail loudly*: instead of silently ignoring a call to a nonexistent method, it throws a clear exception. It is the building block of **proxies** and **decorators**, objects that intercept calls to add behavior to them (logging, caching, permission checks) before forwarding them to the real object.

### `__callStatic()`

```php
<?php
class Facade
{
    public static function __callStatic(string $name, array $arguments): mixed
    {
        // delegates to a real service
    }
}
```

Full source: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/en/parte-07/cap-27/listing-12.php)


`__callStatic()` is the static version of `__call()`: it intercepts calls to nonexistent static methods. It is the mechanism behind the **facades** of some frameworks (Laravel above all), those static-looking APIs — `Cache::get(...)`, `Route::get(...)` — that in reality delegate behind the scenes to a real object taken from the container. They give a convenient syntax, at the price of hiding the underlying object: a trade-off to know before adopting it.

## Property hooks

PHP 8.4 introduces **property hooks**, which allow you to attach read and write logic directly to a property, without writing a separate getter and setter. The concept brings properties and methods closer: from the point of view of whoever uses the object it remains a simple `$object->property` access, but behind it there may be a validation on write or a computation on read.

The idea, in essence, is that a property can control the value assigned to it or compute on the fly the value it returns, reducing the boilerplate of the classic getters/setters of Chapter 25. And the usual caution applies, the same as for magic methods: do not use a hook to hide heavy logic where the reader expects the negligible cost of a simple data access. Surprise, in code, is always a defect.

## In summary

Modern PHP types serve to make code **more explicit**: union and intersection types declare precisely what a function accepts, nullable makes absence visible, enums eliminate magic strings by restricting the set of possible values, and backed enums act as a bridge toward databases and serialization. On the dynamic side, the nullsafe operator simplifies optional chains, and magic methods enable implicit behaviors such as proxies and facades. The thread that ties them all together is discipline: each of these tools should be used when it makes the **model clearer** — not when it serves to amaze or to postpone a design decision.
