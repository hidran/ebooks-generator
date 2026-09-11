# 35. Docker, cache, CI/CD and operations

An application does not end when the code works on your laptop: that is only the starting point. The enterprise blog must **start reproducibly** on any machine, use external services (database, cache) in a controlled way, declare whether it is **healthy**, pass a battery of automatic checks before every release, and reach production with a traceable, reversible deployment. This chapter covers exactly this layer — **operations** — and it is what separates an MVC exercise from a system you can genuinely put online and keep running. Many of the concepts here are not specific to PHP: they are the practices by which you take *any* application to production.

## Docker runtime with PHP 8.5

The first problem is reproducibility: making the application run identically everywhere, not "it depends on what you have installed". The answer is **Docker**, and the project uses PHP 8.5 FPM on Alpine, a minimal Linux distribution:

```dockerfile
FROM php:8.5-fpm-alpine AS runtime

RUN set -eux; \
    apk add --no-cache icu-libs; \
    apk add --no-cache --virtual .build icu-dev linux-headers $PHPIZE_DEPS; \
    docker-php-ext-install -j"$(nproc)" pdo_mysql intl; \
    pecl install redis; \
    docker-php-ext-enable redis; \
    apk del .build
```

Full source: [listing-01.Dockerfile](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-35/en/parte-09/cap-35/listing-01.Dockerfile)


Real source: [`deploy/docker/Dockerfile` at `lesson-4-1`](https://github.com/hidran/phpenterpriseblog/blob/lesson-4-1/deploy/docker/Dockerfile).


A `Dockerfile` is the recipe for the environment: it says exactly which PHP, which extensions, which libraries. Look at a refined detail in that `RUN`: the libraries needed to compile the extensions (`pdo_mysql` for the database, `intl` for internationalization, `redis` for the cache) are installed in a "virtual" package called `.build` and then **removed** with `apk del .build` at the end. Why? Because the compilation tools are not needed to *run* the application, only to build it: keeping them in the final image would bloat it and widen the attack surface. It is the same idea as the *multi-stage build* by which the Composer dependencies are prepared in a separate stage: the final image contains **only** what is needed to run the app. Smaller, faster to distribute, safer.

## Local environment with Compose

A real application is never alone: it needs a database, a cache, a web server. **Docker Compose** describes the whole stack in a single file:

```yaml
services:
  app:
    build:
      context: .
      dockerfile: deploy/docker/Dockerfile
      target: runtime
    environment:
      APP_ENV: local
      DB_HOST: mysql
      REDIS_DSN: redis://:devpass@redis:6379/0

  nginx:
    image: nginx:1.27-alpine
    ports: ["8080:80"]
```

Full source: [listing-02.yml](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-35/en/parte-09/cap-35/listing-02.yml)


Real source: [`docker-compose.yml` at `lesson-4-2`](https://github.com/hidran/phpenterpriseblog/blob/lesson-4-2/docker-compose.yml).


The file lists the **services** — here you see `app` (PHP-FPM) and `nginx`, while the full stack adds MySQL, Redis and MailHog to catch emails in development — and wires them together. Note `DB_HOST: mysql`: inside Compose the services reach each other **by name**, not by IP address, so the app talks to the database by simply calling it `mysql`. The practical result is that the whole development environment — with the same versions of every component for everyone — starts with one command:

```bash
make up
open http://localhost:8080
```

Full source: [listing-03.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-35/en/parte-09/cap-35/listing-03.sh)


Real source: [`README.md` at commit `eb2e62a`](https://github.com/hidran/phpenterpriseblog/blob/eb2e62a774f6b20539e72f40f7d3fe9205ef4c5d/README.md).


A single `make up` reduces *onboarding* — the time a new developer takes to become productive — from a day of configuration to a few minutes. And because the local environment has the same shape as production, a whole category of problems disappears: the ones that "work locally".

## Health check

A production application must be able to answer a simple but crucial question: "are you alive, and can you talk to the services you depend on?"

```php
<?php

declare(strict_types=1);

public function check(ServerRequestInterface $request, array $args = []): ResponseInterface
{
    $db = $this->probe(function (): bool {
        $stmt = $this->pdo->query('SELECT 1');
        return $stmt !== false && (int) $stmt->fetchColumn() === 1;
    });

    $status = $db === 'ok' ? 200 : 503;

    return $this->json(['db' => $db], $status);
}
```

Full source: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-35/en/parte-09/cap-35/listing-04.php)


Real source: [`src/Controllers/HealthController.php` at `lesson-4-3`](https://github.com/hidran/phpenterpriseblog/blob/lesson-4-3/src/Controllers/HealthController.php).


The `/healthz` endpoint does not render a page: it runs a minimal probe — a `SELECT 1` against the database — and answers with an HTTP code a machine can read: `200` if all is well, `503` (service unavailable) if the database does not respond. It seems trivial, but it is the pillar of automation: an orchestrator like Kubernetes polls this endpoint continuously to decide whether to route traffic to an instance or restart it because it is sick; the deployment uses it to tell whether the new version is ready before sending it users; the E2E tests wait on it before starting. The application's health stops being an impression and becomes a queryable fact.

## PSR-16 cache with Redis

To relieve the database, the project introduces a cache — but behind a standard **interface**, not tied to a specific technology:

```php
<?php

declare(strict_types=1);

final class RedisCache implements CacheInterface
{
    private readonly Psr16Cache $inner;

    public function __construct(string $dsn, string $namespace = 'fb')
    {
        $client = RedisAdapter::createConnection($dsn);
        $adapter = new RedisAdapter($client, $namespace);
        $this->inner = new Psr16Cache($adapter);
    }
}
```

Full source: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-35/en/parte-09/cap-35/listing-05.php)


Real source: [`src/Cache/RedisCache.php` at `lesson-5-1`](https://github.com/hidran/phpenterpriseblog/blob/lesson-5-1/src/Cache/RedisCache.php).


`RedisCache implements CacheInterface`: that interface is **PSR-16**, the PHP standard for caches. It is the same lesson as Chapter 26 (program against a contract) applied here: the rest of the application knows only `CacheInterface`, not `Redis`. Tomorrow you can replace Redis with an in-memory cache for tests, or with another technology in production, and none of the cache's consumers notice — because they all depend on the interface, not on the implementation. Redis, concretely, is an in-memory key-value store: very fast, perfect for keeping close at hand data that would be expensive to recompute.

## Repository decorator

Now the interesting question: how do you add the cache to the `PostRepository` of Chapter 33 without dirtying it? The answer is an elegant pattern, the **decorator**:

```php
<?php

declare(strict_types=1);

final class CachedPostRepository extends PostRepository
{
    public function findById(int $id): ?Post
    {
        $key = self::keyShow($id);
        $cached = $this->cache->get($key);

        if ($cached instanceof Post) {
            return $cached;
        }

        $fresh = parent::findById($id);

        if ($fresh !== null) {
            $this->cache->set($key, $fresh, self::TTL_SHOW);
        }

        return $fresh;
    }
}
```

Full source: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-35/en/parte-09/cap-35/listing-06.php)


Real source: [`src/Cache/CachedPostRepository.php` at `lesson-5-2`](https://github.com/hidran/phpenterpriseblog/blob/lesson-5-2/src/Cache/CachedPostRepository.php).


Follow the logic of `findById()`: first it looks for the post in the cache; if it is there (*cache hit*), it returns it without touching the database; if it is not (*cache miss*), it calls `parent::findById()` — the original repository's real SQL query — and before returning the result it stores it in the cache with an expiry (`TTL_SHOW`). The beautiful part is what did **not** change: `PostRepository`, with its SQL, stayed identical and unaware of the cache. Caching is a **separate** layer that wraps the original, adding behavior without modifying it. It is the *open/closed* principle — open to extension, closed to modification — made concrete, and the advantage is that you can test the caching logic in isolation and turn it on or off by choosing which of the two classes to register in the container.

## Redis sessions

There is a problem that arises when the application runs on **multiple instances** at once (multiple *pods*, in Kubernetes jargon) to handle the load. PHP sessions, by default, live as files on the server's local disk; but if a user lands on instance A for one request and on instance B for the next, their session — stored on A's disk — is not on B, and they appear logged out. The solution is to move sessions to a shared store, Redis:

```php
<?php

declare(strict_types=1);

final class RedisSessionHandler implements SessionHandlerInterface
{
    public function read(string $id): string
    {
        $value = $this->redis->get($this->prefix . $id);

        return is_string($value) ? $value : '';
    }

    public function write(string $id, string $data): bool
    {
        return $this->redis->setex($this->prefix . $id, $this->ttl, $data) === true;
    }
}
```

Full source: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-35/en/parte-09/cap-35/listing-07.php)


Real source: [`src/Session/RedisSessionHandler.php` at `lesson-5-3`](https://github.com/hidran/phpenterpriseblog/blob/lesson-5-3/src/Session/RedisSessionHandler.php).


By implementing `SessionHandlerInterface`, this class tells PHP to read and write sessions to Redis instead of to files. Now all instances share the same session store, and the user stays logged in regardless of which instance serves them. Note the `setex`: it writes the data **with an expiry** (`$this->ttl`), so abandoned sessions self-destruct. It is exactly the same conceptual problem as remember me in the User Management System (Chapter 24): user state must be handled with clear boundaries, an expiry, and the ability to revoke it. The technology changes, not the principle.

## CI with GitHub Actions

How do you guarantee that every change to the code breaks nothing, without relying on the memory of whoever writes it? With **CI** (*continuous integration*): a pipeline that, on every push, automatically runs all the checks.

```yaml
jobs:
  quality:
    strategy:
      matrix:
        php: ["8.4", "8.5"]
    steps:
      - run: composer cs
      - run: composer stan
      - run: composer test
```

Full source: [listing-08.yml](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-35/en/parte-09/cap-35/listing-08.yml)


Real source: [`.github/workflows/ci.yml` at `lesson-6-1`](https://github.com/hidran/phpenterpriseblog/blob/lesson-6-1/.github/workflows/ci.yml).


This GitHub Actions pipeline runs three checks in sequence: `composer cs` checks the code **style** (consistent formatting), `composer stan` runs the **static analysis** with PHPStan (which finds type errors and potential bugs *without* running the code), and `composer test` runs the **test suite**. All of it over a `matrix` of two PHP versions, 8.4 and 8.5: the same pipeline runs twice, verifying compatibility with both (the book stays oriented around PHP 8.5). The value of CI is that these checks no longer depend on an individual's discipline: no one can forget to run them, because they fire on their own at every push, and a change that breaks style, types, or tests is blocked before it enters the main branch.

## Deployment with Helm

The last step is bringing the image to production. The project uses tagged images, a registry (ECR), a Kubernetes cluster (EKS), and **Helm** to orchestrate the release:

```yaml
helm upgrade --install phpenterpriseblog deploy/helm/phpenterpriseblog \
  --namespace phpenterpriseblog-prod \
  --values deploy/helm/phpenterpriseblog/values.prod.yaml \
  --set image.repository="$ECR_REGISTRY/phpenterpriseblog" \
  --set image.tag="$IMAGE_TAG" \
  --wait --timeout 10m --atomic
```

Full source: [listing-09.yml](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-35/en/parte-09/cap-35/listing-09.yml)


Real source: [`.github/workflows/release.yml` at `lesson-7-5`](https://github.com/hidran/phpenterpriseblog/blob/lesson-7-5/.github/workflows/release.yml).


Focus on the two final options, because they hold the philosophy of a safe deployment. `--wait` tells Helm to **wait** for the release to actually become healthy (using, among other things, the health check from earlier) instead of declaring victory as soon as the commands have started. `--atomic` does the most important thing: if the release fails within the timeout, it rolls **back automatically** to the previous version, without leaving production in a half-done state. It is an "all or nothing" deployment — either the new version comes in healthy, or it does not come in at all — and the choice is documented in ADR `0004`. The tagged image (`$IMAGE_TAG`) finally guarantees traceability: you know exactly which version of the code is in production, and which one you can roll back to.

## E2E and ADRs

The last safety net is the **end-to-end** tests, which with Playwright verify real flows by driving an actual browser:

```typescript
import { test, expect } from "@playwright/test";

test("anonymous visitor can read the post list and a post", async ({ page }) => {
  await page.goto("/");
  const postLink = page.locator("main a[href^='/posts/']").first();
  await expect(postLink).toBeVisible();
  await postLink.click();
  await expect(page).toHaveURL(/\/posts\/\d+/);
});
```

Full source: [listing-10.ts](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-35/en/parte-09/cap-35/listing-10.ts)


Real source: [`tests/E2e/anonymous-can-read.spec.ts` at `lesson-8-2`](https://github.com/hidran/phpenterpriseblog/blob/lesson-8-2/tests/E2e/anonymous-can-read.spec.ts).


While unit tests verify a piece in isolation, this E2E test verifies the **whole, assembled** application, from the user's point of view: open the home page, find the link to a post, click it, and you must end up on a page whose URL is `/posts/` followed by a number. It is the proof that all the layers built in the previous chapters — router, controller, repository, view — work *together*. Closing out the project are the **ADRs** (Architecture Decision Records), the documents that explain the *why* of the important choices — Composer/PSR-4, DTO versus repository, forward-only migrations, atomic Helm releases — so that they do not live only in the memory of whoever made them. A project that documents its decisions is a project others can inherit and maintain.

## In summary

The last stretch of the project shows that "enterprise" does not mean complicating for its own sake. It means making everything **reproducible**: the environment (Docker and Compose), the health (health check), the performance (PSR-16 cache behind an interface, added with a decorator), the shared state (Redis sessions), the quality (CI that checks style, types, and tests on every push), and the release (an atomic, reversible Helm deployment). The blog stays small in features, but it now has the same operational boundaries as a real application — and that, more than any single library, is the difference between writing code and putting a system into production.
