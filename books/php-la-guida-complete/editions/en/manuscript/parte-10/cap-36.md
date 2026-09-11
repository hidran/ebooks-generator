# 36. JSON, AJAX, and Health Checks

In the enterprise blog, not every response has to be HTML. Some endpoints serve the browser, others serve automated tools: health checks, smoke tests, AJAX calls, and small internal APIs. The point is not to "do REST because it is fashionable", but to use JSON when the contract between client and server is data, not a page.

## JSON responses in the base controller

After the move to PSR-7, a controller always returns a `ResponseInterface`. `BaseController` offers a helper:

```php
<?php

declare(strict_types=1);

protected function json(array $data, int $status = 200): ResponseInterface
{
    return new Response(
        $status,
        ['Content-Type' => 'application/json'],
        json_encode($data, JSON_THROW_ON_ERROR)
    );
}
```

Full source: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-36/en/parte-10/cap-36/listing-01.php)


Real source: [`src/Controllers/BaseController.php` at `lesson-1-15`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-15/src/Controllers/BaseController.php).

`JSON_THROW_ON_ERROR` avoids silent failures: if the payload cannot be serialized, you get an exception instead of `false`.

## Health check as an operational contract

`/healthz` is JSON because it is not for a user: it is for Docker, Kubernetes, CI, or a smoke test.

```php
<?php

declare(strict_types=1);

return $this->json([
    'db' => $db,
    'redis' => $redis,
    'version' => Env::string('APP_VERSION', 'dev'),
], $status);
```

Full source: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-36/en/parte-10/cap-36/listing-02.php)


Real source: [`src/Controllers/HealthController.php` at `lesson-4-3`](https://github.com/hidran/phpenterpriseblog/blob/lesson-4-3/src/Controllers/HealthController.php).

A typical response is:

```json
{
  "db": "ok",
  "redis": "ok",
  "version": "dev"
}
```

Full source: [listing-03.json](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-36/en/parte-10/cap-36/listing-03.json)


The HTTP status code matters as much as the body: `200` means ready, `503` means not ready.

## Calling an endpoint with `fetch()`

For an internal endpoint, you can use `fetch()`:

```javascript
async function readHealth() {
  const response = await fetch("/healthz", {
    headers: { "Accept": "application/json" }
  });

  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }

  return response.json();
}
```

Full source: [listing-04.js](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-36/en/parte-10/cap-36/listing-04.js)


This example does not replace server-side tests: it is only the browser side of the contract.

## Reading incoming JSON

If you add a JSON endpoint to create a draft post, read the body once and validate:

```php
<?php

declare(strict_types=1);

$payload = (string) $request->getBody();
$data = json_decode($payload, true, 512, JSON_THROW_ON_ERROR);

$title = trim((string) ($data['title'] ?? ''));
$message = trim((string) ($data['message'] ?? ''));
```

Full source: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-36/en/parte-10/cap-36/listing-05.php)


With PSR-7, the body is a stream. Do not build application logic directly on top of `php://input` when you already have `ServerRequestInterface`.

## Validation responses

A simple structure for errors is:

```php
<?php

declare(strict_types=1);

return $this->json([
    'message' => 'Validation failed',
    'errors' => [
        'title' => 'Title is required',
        'message' => 'Message is required',
    ],
], 422);
```

Full source: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-36/en/parte-10/cap-36/listing-06.php)


For the English edition, keep public payload text in English. For localized products, move user-facing messages into a translation layer instead of mixing languages in the same response.

## Sessions, CSRF, and JSON

If a JSON request comes from the same authenticated site, the same rules as forms apply:

- the user must have a valid session;
- permission must be checked in the controller or middleware;
- data must be validated server-side;
- state-changing actions must have CSRF protection or an equivalent mechanism;
- output must use a stable format.

REST does not remove authentication. It only changes the representation of the response.

## Smoke tests in CI/CD

The release pipeline uses the same principle:

```yaml
for i in $(seq 1 30); do
  if curl -fsS https://staging.phpenterpriseblog.example.com/healthz | grep -q '"db":"ok"'; then
    echo "Smoke passed"; exit 0
  fi
  sleep 5
done
echo "Smoke failed"; exit 1
```

Full source: [listing-07.yml](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-36/en/parte-10/cap-36/listing-07.yml)


Real source: [`.github/workflows/release.yml` at `lesson-7-5`](https://github.com/hidran/phpenterpriseblog/blob/lesson-7-5/.github/workflows/release.yml).

This is not a complete application test, but it blocks a deployment that cannot even connect to the database.

## In summary

JSON is a contract. In the enterprise blog we use it for health checks, smoke tests, and possible internal endpoints. With PSR-7/15 the controller returns explicit responses, `json_encode()` fails with exceptions, HTTP status codes carry meaning, and the security rules remain the same as for HTML pages.
