# 36. JSON, AJAX e health check

Nel blog enterprise non tutte le risposte devono essere HTML. Alcuni endpoint servono al browser, altri a strumenti automatici: health check, smoke test, chiamate AJAX e piccole API interne. Il punto non è "fare REST perché va di moda", ma usare JSON quando il contratto tra client e server è un dato, non una pagina.

## Response JSON nel controller base

Dopo il passaggio a PSR-7, un controller restituisce sempre una `ResponseInterface`. Il `BaseController` offre un helper:

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

Codice completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-36/it/parte-10/cap-36/listing-01.php)


Sorgente reale: [`src/Controllers/BaseController.php` a `lesson-1-15`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-15/src/Controllers/BaseController.php).

`JSON_THROW_ON_ERROR` evita fallimenti silenziosi: se il payload non è serializzabile, ottieni un'eccezione invece di `false`.

## Health check come contratto operativo

`/healthz` è JSON perché non serve a un utente: serve a Docker, Kubernetes, CI o a uno smoke test.

```php
<?php

declare(strict_types=1);

return $this->json([
    'db' => $db,
    'redis' => $redis,
    'version' => Env::string('APP_VERSION', 'dev'),
], $status);
```

Codice completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-36/it/parte-10/cap-36/listing-02.php)


Sorgente reale: [`src/Controllers/HealthController.php` a `lesson-4-3`](https://github.com/hidran/phpenterpriseblog/blob/lesson-4-3/src/Controllers/HealthController.php).

Una risposta tipica è:

```json
{
  "db": "ok",
  "redis": "ok",
  "version": "dev"
}
```

Codice completo: [listing-03.json](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-36/it/parte-10/cap-36/listing-03.json)


Il codice HTTP conta quanto il body: `200` significa pronto, `503` significa non pronto.

## Chiamare un endpoint con `fetch()`

Per un endpoint interno puoi usare `fetch()`:

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

Codice completo: [listing-04.js](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-36/it/parte-10/cap-36/listing-04.js)


Questo esempio non sostituisce i test server-side: è solo il lato browser del contratto.

## Leggere JSON in ingresso

Se aggiungi un endpoint JSON per creare una bozza di post, leggi il body una volta e valida:

```php
<?php

declare(strict_types=1);

$payload = (string) $request->getBody();
$data = json_decode($payload, true, 512, JSON_THROW_ON_ERROR);

$title = trim((string) ($data['title'] ?? ''));
$message = trim((string) ($data['message'] ?? ''));
```

Codice completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-36/it/parte-10/cap-36/listing-05.php)


Con PSR-7 il body è uno stream. Non costruire logica applicativa direttamente sopra `php://input` quando hai già `ServerRequestInterface`.

## Risposte di validazione

Una struttura semplice per gli errori è:

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

Codice completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-36/it/parte-10/cap-36/listing-06.php)


Per l'edizione italiana puoi mostrare messaggi utente tradotti nella UI, ma nel codice sorgente del repository i messaggi di servizio restano in inglese. L'importante è non mescolare italiano, inglese e spagnolo nello stesso payload pubblico.

## Sessioni, CSRF e JSON

Se una richiesta JSON parte dallo stesso sito autenticato, valgono le stesse regole dei form:

- l'utente deve avere una sessione valida;
- il permesso deve essere controllato nel controller o in middleware;
- i dati devono essere validati server-side;
- le azioni che cambiano stato devono avere protezione CSRF o un altro meccanismo equivalente;
- l'output deve usare un formato stabile.

REST non cancella l'autenticazione. Cambia solo la rappresentazione della risposta.

## Smoke test in CI/CD

La pipeline di release usa lo stesso principio:

```yaml
for i in $(seq 1 30); do
  if curl -fsS https://staging.phpenterpriseblog.example.com/healthz | grep -q '"db":"ok"'; then
    echo "Smoke passed"; exit 0
  fi
  sleep 5
done
echo "Smoke failed"; exit 1
```

Codice completo: [listing-07.yml](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-36/it/parte-10/cap-36/listing-07.yml)


Sorgente reale: [`.github/workflows/release.yml` a `lesson-7-5`](https://github.com/hidran/phpenterpriseblog/blob/lesson-7-5/.github/workflows/release.yml).

Questo non è un test completo dell'applicazione, ma blocca un deploy che non riesce nemmeno a connettersi al database.

## In sintesi

JSON è un contratto. Nel blog enterprise lo usiamo per health check, smoke test e possibili endpoint interni. Con PSR-7/15 il controller restituisce response esplicite, `json_encode()` fallisce con eccezioni, i codici HTTP hanno significato e le regole di sicurezza restano le stesse delle pagine HTML.
