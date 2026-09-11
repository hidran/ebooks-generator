# 30. Exceptions, error handlers and Sentry

Not all errors are the same, and knowing how to tell them apart is half the craft. Some are code **bugs** — an oversight to fix. Others are **expected conditions**: a missing file, a record not found, invalid input, an external service momentarily unreachable. They are not the same thing and must not be handled the same way: the former should be made visible as soon as possible so they can be corrected, the latter should be handled gracefully because they are part of normal operation. PHP's **exceptions** and **handlers** are the tools for doing this, and this chapter lines them up all the way to error monitoring in production with Sentry.

## `try`, `catch` and `finally`

The `try/catch/finally` block is the basic structure for handling an operation that can fail:

```php
<?php
try {
    $pdo = new PDO($dsn, $user, $password);
} catch (PDOException $e) {
    echo "Connection failed";
} finally {
    // code executed anyway
}
```

Full source: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-30/en/parte-08/cap-30/listing-01.php)


The three blocks have distinct roles. In the `try` you put the code that *might* fail — here opening the database connection. The `catch` intercepts a specific type of exception, `PDOException`, and decides what to do when that failure happens. The `finally` is the least obvious but often the most useful: it is executed **in any case**, whether the `try` succeeded or the `catch` fired. It is the place to release resources that must be closed anyway — an open file, a lock, a transaction — because it guarantees that code runs whichever path the execution takes.

## Throwing exceptions

You can also **raise** an exception yourself, with `throw`, when you detect a condition the code cannot or should not handle there:

```php
<?php
function divide(float $a, float $b): float
{
    if ($b === 0.0) {
        throw new InvalidArgumentException("Division by zero");
    }

    return $a / $b;
}
```

Full source: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-30/en/parte-08/cap-30/listing-02.php)


The key point is what happens after the `throw`: the exception **interrupts** the normal flow and **travels up** the call chain until it finds a `catch` able to handle it. It is a jump upward, not a return value. And this is exactly the difference from the old error codes returned as a value: a return value the caller can ignore through carelessness and carry on with wrong data; an exception cannot — you cannot pretend nothing happened, either someone catches it or the application stops. Failure becomes impossible to ignore silently. Here I use `InvalidArgumentException`, one of PHP's standard exceptions designed precisely for invalid arguments.

## Custom exceptions

Beyond the standard ones, you can define your **own** exceptions, extending a base class like `RuntimeException`:

```php
<?php
class UserNotFoundException extends RuntimeException
{
}

function find_user(int $id): array
{
    $user = null;

    if (!$user) {
        throw new UserNotFoundException("User $id not found");
    }

    return $user;
}
```

Full source: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-30/en/parte-08/cap-30/listing-03.php)


At first sight an empty class that extends `RuntimeException` looks useless — it adds no code. But it adds the most important thing: a **type**. And the type lets you distinguish errors and catch them selectively:

```php
<?php
try {
    $user = find_user(10);
} catch (UserNotFoundException $e) {
    http_response_code(404);
}
```

Full source: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-30/en/parte-08/cap-30/listing-04.php)


Here the `catch` intercepts **only** `UserNotFoundException` and translates it into a 404, the right HTTP response for "resource not found". Any other exception — a database error, a bug — is not caught by this block and keeps traveling up, where it will be handled differently. This is the value of custom exceptions: giving a precise name to your domain's error conditions, so that each can be treated as it deserves. In the MVC project of Part IX you will see a whole set of domain exceptions built exactly on this principle.

## Error handler

There is a gray zone: besides exceptions, PHP has an old system of **warnings**, **notices** and **deprecations** that are not exceptions and, by default, stop nothing — at most they print a line. You can, however, convert them into exceptions with an error handler:

```php
<?php
set_error_handler(function (int $severity, string $message, string $file, int $line): bool {
    throw new ErrorException($message, 0, $severity, $file, $line);
});
```

Full source: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-30/en/parte-08/cap-30/listing-05.php)


By registering this function, every warning PHP would emit is turned into an `ErrorException` and fed into the exception system, where you can catch it like all the others. In development it is invaluable: instead of ignoring a warning that signals a real problem (a missing array index, an undefined variable), you **fail immediately** and see it. It is again the *fail loud* principle — a problem visible at once costs far less than one that hides and resurfaces days later, far from its cause.

## Global exception handler

And what if an exception is caught by no `catch`? You need a last safety net, the **global exception handler**:

```php
<?php
set_exception_handler(function (Throwable $e): void {
    error_log($e);

    http_response_code(500);
    echo "Internal error";
});
```

Full source: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-30/en/parte-08/cap-30/listing-06.php)


This handler is invoked for any exception that reaches the top without having been handled. It does three sensible things: it logs the error (`error_log`), sets the HTTP status to 500, and shows the user a clean message instead of a stack trace. But be careful not to misunderstand its role: it is the **last** defense, not the strategy. It should not replace the local handling of expected errors — those you catch near where they arise, like the 404 earlier. The global handler is there for what you *did not* foresee, and its job is to prevent an unforeseen event from turning into a technical screen spat in the user's face.

## Development and production environment

And here we reach the most delicate point for security. The behavior of errors must be **opposite** between development and production. In development you want to see everything:

```php
<?php
ini_set("display_errors", "1");
error_reporting(E_ALL);
```

Full source: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-30/en/parte-08/cap-30/listing-07.php)


In production, instead, errors must **never** be shown to the user: they go off on screen and get written to the logs:

```php
<?php
ini_set("display_errors", "0");
ini_set("log_errors", "1");
```

Full source: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-30/en/parte-08/cap-30/listing-08.php)


This is not a matter of tidiness, it is a genuine **vulnerability**. A stack trace shown on the page reveals the server's absolute paths, fragments of SQL queries, variable names, sometimes connection credentials: it is a gold mine for anyone who wants to attack you, handing them the internal map of the application. The rule is sharp: in production the user sees a generic message, you read the details in the log. Never the other way around.

## Logging with Sentry

Writing errors to a log file is fine, but on a serious server those files grow, get lost, and no one looks at them until it is too late. **Sentry** is a service that centralizes the collection of exceptions and errors in production: with Composer you install the package and initialize the client with a DSN, and from there errors arrive at a dashboard where they are grouped, counted and notified. The conceptual flow is "catch, send, rethrow":

```php
<?php
try {
    // application code
} catch (Throwable $e) {
    // send to Sentry
    throw $e;
}
```

Full source: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-30/en/parte-08/cap-30/listing-09.php)


Note the final `throw $e`: after reporting the error to Sentry, it **rethrows** it, because the job here is not to hide it or handle it — the global handler already takes care of that — but to *record* it. And to record it **with context**: Sentry saves not just the message, but the requested URL, the user involved, the environment, the application version. It is the difference between knowing that "something went wrong" and being able to reproduce exactly the bug a user hit three hours ago on a page you, locally, cannot make fail.

## In summary

Exceptions make failures **explicit** and impossible to ignore silently: use custom exceptions to give a name to your domain's error cases and catch them selectively, the error handler to surface warnings immediately in development, and the global exception handler as a last defense for the unforeseen. In production **never** show errors to the user — it would be a security hole — but log them, better still with a service like Sentry that enriches them with context. The thread tying it all together is an idea of professional maturity: a solid application is not one that never fails, but one that can fail in a **controlled and observable** way.
