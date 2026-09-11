# 34. Authentication, Tests, and Quality Gates

An enterprise project is not credible because it "works on my machine." It is credible because it has repeatable checks: automated tests, style checks, static analysis, and guided refactoring. In the `phpenterpriseblog` repository these checks arrive right after the MVC foundation.

The point is not to add tools to look more professional. The point is to build a system where a change can be made, verified, and corrected without relying on the developer's memory. In a small MVC blog you can click through two pages and convince yourself everything is fine. In a growing project, that method does not scale: you forget an edge case, change a query and break a distant page, upgrade PHP and discover too late that a signature is no longer coherent. Quality gates reduce that risk before deployment.

As a PHP architect, I read these tools as different layers of the same control system:

- PHPUnit verifies behavior we decided to protect;
- PHP_CodeSniffer and Slevomat verify code discipline;
- PHPStan verifies type and contract coherence;
- Rector applies mechanical refactoring in a repeatable way;
- Composer puts everything behind commands that CI can run too.

None of these tools replaces technical judgment. Together, though, they prevent the project from depending only on attention in the moment.

## Authentication as a service

In the UMS project, login logic grew inside functions and controllers. In the blog we extract it into `AuthService`, so we can test it without a browser and without a real database:

```php
<?php

declare(strict_types=1);

final class AuthService
{
    public function __construct(private readonly UserRepositoryInterface $users)
    {
    }

    public function verifySignup(
        string $email,
        string $password,
        string $token,
        string $sessionToken
    ): AuthResult {
        if (!hash_equals($sessionToken, $token)) {
            return AuthResult::failure('TOKEN MISMATCH');
        }

        if ($this->users->findByEmail($email) !== null) {
            return AuthResult::failure('USER ALREADY EXISTS');
        }

        return AuthResult::success('SIGNUP OK');
    }
}
```

Full source: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-34/en/parte-09/cap-34/listing-01.php)


Real source: [`src/Services/AuthService.php` at `lesson-1-8`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-8/src/Services/AuthService.php).

The dependency is an interface (`UserRepositoryInterface`), not a concrete class. That makes the service testable with mocks.

This is an architectural decision, not just a PHPUnit trick. `AuthService` contains application rules: verify the CSRF token, find the user, check the password, return an explicit result. If this logic stays inside a controller, testing it means simulating an HTTP request, session, database, and rendering. If it lives in a service, you can test the rule directly.

A good application service has three traits: it receives dependencies from the outside, returns a result the caller can understand, and does not decide infrastructure details such as redirects or templates. The controller can deal with HTTP; the service decides whether login is valid. That separation is why the unit test becomes natural.

## PHPUnit: unit and integration

The configuration separates unit and integration tests:

```xml
<testsuites>
    <testsuite name="unit">
        <directory>tests/Unit</directory>
    </testsuite>
    <testsuite name="integration">
        <directory>tests/Integration</directory>
    </testsuite>
</testsuites>
```

Full source: [listing-02.xml](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-34/en/parte-09/cap-34/listing-02.xml)


Real source: [`phpunit.xml.dist` at `lesson-3-1`](https://github.com/hidran/phpenterpriseblog/blob/lesson-3-1/phpunit.xml.dist).

Unit tests should be fast and isolated. Integration tests can touch MySQL or Redis, but they live in a separate suite.

The difference is practical. A unit test verifies an in-memory decision: given this input and this simulated dependency, the service returns this result. MySQL should not start, Redis should not exist, and no web server should be involved. If it fails, you want to understand immediately which rule is wrong.

An integration test verifies that two or more real parts talk to each other correctly. A PDO repository, for example, is not truly verified if you only test that it calls `prepare()`: you also need to know that the query works against the real schema, that column names are correct, and that row-to-object mapping does not lose data. The same applies to Redis, migrations, session handlers, and configuration.

That is why the suites are separated. Unit tests should run constantly while you develop. Integration tests can be slower and may require Docker services, so you run them before opening a pull request, in CI, or when touching an infrastructure boundary. Separation avoids two common mistakes: making every test slow, or calling a test "unit" when it really depends on half the system.

## Testing authentication with mocks

A test should not create real users in the database just to verify a bad password:

```php
<?php

declare(strict_types=1);

public function testLoginRejectsUnknownUser(): void
{
    $repo = $this->createMock(UserRepositoryInterface::class);
    $repo->method('findByEmail')->willReturn(null);

    $service = new AuthService($repo);

    self::assertSame(
        'USER NOT FOUND',
        $service->verifyLogin('a@b.co', 'secret123', 't', 't')->message
    );
}
```

Full source: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-34/en/parte-09/cap-34/listing-03.php)


Real source: [`tests/Unit/Services/AuthServiceTest.php` at `lesson-3-2`](https://github.com/hidran/phpenterpriseblog/blob/lesson-3-2/tests/Unit/Services/AuthServiceTest.php).

Here we test the service contract: when the repository does not find the user, the result is a controlled failure.

A mock is useful when you want to isolate a rule from its external boundary. In this case we do not care whether `UserRepository` can talk to MySQL; an integration test will cover that. Here we care about `AuthService` behavior when the repository answers "no user".

The risk with mocks is using them to test implementation instead of behavior. If a test says "it must call exactly these three methods in this order" but does not describe a useful application result, it becomes fragile. A good unit test speaks the language of the domain: login rejected, invalid token, existing user, correct password.

## Regression tests

A fixed bug should become a test. The repository has a precise case: `PostRepository::save()` must not write the email into the post body.

```php
<?php

declare(strict_types=1);

$stmt->expects($this->once())
    ->method('execute')
    ->with($this->callback(function (array $params): bool {
        self::assertSame('actual message body', $params['message']);
        self::assertArrayNotHasKey('email', $params);

        return true;
    }));
```

Full source: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-34/en/parte-09/cap-34/listing-04.php)


Real source: [`tests/Unit/Repositories/PostRepositorySaveRegressionTest.php` at `lesson-3-3`](https://github.com/hidran/phpenterpriseblog/blob/lesson-3-3/tests/Unit/Repositories/PostRepositorySaveRegressionTest.php).

The test describes behavior that must not break again.

That is the value of a regression test: it does not prove that the whole repository is perfect, but it blocks a real error that already cost time. Every time you fix a bug, ask which test would have caught it earlier. If you can write that test, the bug is no longer merely "fixed"; it is documented as expected behavior.

In the enterprise blog, that mindset matters more than test count. You do not need to test every getter or every line. You need to protect rules, already-found bugs, and boundaries where regression cost is high: authentication, post persistence, view escaping, migrations, and integration with external services.

## PHP_CodeSniffer and Slevomat

The first quality gate is mechanical: PSR-12 plus Slevomat rules for types and `strict_types`.

```xml
<rule ref="PSR12"/>
<rule ref="SlevomatCodingStandard.TypeHints.ParameterTypeHint"/>
<rule ref="SlevomatCodingStandard.TypeHints.ReturnTypeHint"/>
<rule ref="SlevomatCodingStandard.TypeHints.PropertyTypeHint"/>
<rule ref="SlevomatCodingStandard.TypeHints.DeclareStrictTypes"/>
```

Full source: [listing-05.xml](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-34/en/parte-09/cap-34/listing-05.xml)


Real source: [`phpcs.xml` at `lesson-2-1`](https://github.com/hidran/phpenterpriseblog/blob/lesson-2-1/phpcs.xml).

The goal is not to argue about spaces or braces. The goal is to remove mechanical work from review and fail the build when types are missing.

PHP_CodeSniffer reads code and verifies that it follows a standard. PSR-12 gives a shared base: indentation, namespaces, imports, braces, declarations. Slevomat adds rules more oriented toward modern PHP quality: typed parameters, return types, property types, and `declare(strict_types=1)`.

For a senior developer the value is concrete: code review should focus on architecture, security, queries, transactions, error handling, and domain names. If half the review is about formatting or missing types, you are spending human attention on problems a machine can detect more consistently.

PHPCS does not know whether the query is correct and does not know whether the design is good. But it creates a uniform base. When all files follow the same rules, the code becomes easier to read, tools work better, and commit diffs show real changes instead of noise.

## PHPStan

PHPStan finds inconsistencies that tests might not traverse:

```yaml
includes:
  - phpstan-baseline.neon
parameters:
  level: 8
  paths:
    - src
    - bin
    - config
    - public
    - tests
```

Full source: [listing-06.yml](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-34/en/parte-09/cap-34/listing-06.yml)


Real source: [`phpstan.neon` at `lesson-8-3`](https://github.com/hidran/phpenterpriseblog/blob/lesson-8-3/phpstan.neon).

The project starts with a baseline at level 6 and later raises the bar to level 8. It is a pragmatic migration: turn on the check early, then reduce debt explicitly.

PHPStan is a static analyzer: it does not execute the program, but it reads the code and tries to understand whether contracts are coherent. If a function promises `Post` but can return `false`, PHPStan reports it. If an array is used as if a key were always present, but that key is not guaranteed, PHPStan forces you to be explicit. If a method receives `int` and you pass `string|null`, you find out before reaching the browser.

This is especially important in PHP because the language is flexible. Flexibility is useful, but in large projects it can hide errors: implicit array shapes, `mixed` values, properties initialized late, different return types from the same method. PHPStan reduces that gray area.

The baseline is not an excuse to ignore errors. It is a migration tool. When you introduce PHPStan into an existing project, you may have too many issues to fix immediately. The baseline records current debt and prevents adding more. Then, commit by commit, you remove entries from the baseline and raise the level. Reaching level 8 means asking the code for much clearer contracts.

PHPStan does not replace tests. Code can be statically correct and still violate a business rule. But PHPStan finds a different class of problems: inconsistencies tests may never traverse.

## Rector toward PHP 8.5

Rector helps keep the code aligned with the language:

```php
<?php

declare(strict_types=1);

return RectorConfig::configure()
    ->withPaths([__DIR__ . '/src', __DIR__ . '/bin', __DIR__ . '/config', __DIR__ . '/tests'])
    ->withSets([
        LevelSetList::UP_TO_PHP_85,
        SetList::CODE_QUALITY,
        SetList::DEAD_CODE,
        SetList::TYPE_DECLARATION,
    ]);
```

Full source: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-34/en/parte-09/cap-34/listing-07.php)


Real source: [`rector.php` at `lesson-2-3`](https://github.com/hidran/phpenterpriseblog/blob/lesson-2-3/rector.php).

It does not replace human judgment, but it makes many modernization steps mechanical.

Rector works on the code's syntax tree, not on simple text replacements. That means it can apply structural transformations: add types when they are inferable, replace obsolete constructs, simplify dead code, and move patterns toward modern language versions.

Rector's architectural value is repeatability. If you decide the project must align with PHP 8.5, you do not want to perform hundreds of micro-refactors by hand. You want an executable rule, a readable diff, and a test suite confirming that behavior did not change.

Rector must be used with discipline: run it in small commits, read the diff, do not accept transformations you do not understand, then run tests and static analysis. It is an accelerator, not autopilot. If a transformation changes the meaning of the code, the problem is not only the tool; it means tests were missing or the code was ambiguous.

## The local CI command

The value of gates is being able to run them the same way every time:

```bash
composer ci
```

Full source: [listing-08.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-34/en/parte-09/cap-34/listing-08.sh)


Real source: [`composer.json` at commit `eb2e62a`](https://github.com/hidran/phpenterpriseblog/blob/eb2e62a774f6b20539e72f40f7d3fe9205ef4c5d/composer.json).

Every work block should close with a real verification. Do not just say "it should work": run the command, read the output, and only then treat that project point as stable.

Gate order matters. First you want to fail on cheap problems: formatting, standards, obvious type issues. Then you move to static analysis and unit tests. Only after that does it make sense to run integration tests, E2E tests, or more expensive pipelines. A well-organized CI is not one final wall; it is a series of filters that return feedback as early as possible.

In a team, `composer ci` is also a social contract. It means everyone uses the same command, locally and in CI. There are no hidden instructions living in one person's head. If the command passes on your machine and in CI, the project has a shared definition of "verified."

## In summary

Authentication and quality gates belong in the same chapter because they share a principle: explicit, verifiable behavior. `AuthService` makes login testable; PHPUnit blocks regressions; PHP_CodeSniffer and Slevomat make style uniform and force clear types; PHPStan checks contracts without executing the application; Rector automates refactoring and upgrades toward PHP 8.5. An ordinary senior developer should not use them because they are fashionable: they should use them because they measurably reduce the risk of changing code.
