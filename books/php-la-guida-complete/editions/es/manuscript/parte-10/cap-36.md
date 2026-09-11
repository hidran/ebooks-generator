# 36. JSON, AJAX y health check

En el blog enterprise no todas las respuestas tienen que ser HTML. Algunos endpoints sirven al browser, otros a herramientas automáticas: health checks, smoke tests, llamadas AJAX y pequeñas API internas. El punto no es "hacer REST porque está de moda", sino usar JSON cuando el contrato entre cliente y server son datos, no una página.

## Response JSON en el controller base

Después del paso a PSR-7, un controller siempre devuelve una `ResponseInterface`. `BaseController` ofrece un helper:

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

Código completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-36/es/parte-10/cap-36/listing-01.php)


Fuente real: [`src/Controllers/BaseController.php` en `lesson-1-15`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-15/src/Controllers/BaseController.php).

`JSON_THROW_ON_ERROR` evita fallos silenciosos: si el payload no se puede serializar, obtienes una excepción en lugar de `false`.

## Health check como contrato operativo

`/healthz` es JSON porque no sirve a un usuario: sirve a Docker, Kubernetes, CI o un smoke test.

```php
<?php

declare(strict_types=1);

return $this->json([
    'db' => $db,
    'redis' => $redis,
    'version' => Env::string('APP_VERSION', 'dev'),
], $status);
```

Código completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-36/es/parte-10/cap-36/listing-02.php)


Fuente real: [`src/Controllers/HealthController.php` en `lesson-4-3`](https://github.com/hidran/phpenterpriseblog/blob/lesson-4-3/src/Controllers/HealthController.php).

Una response típica es:

```json
{
  "db": "ok",
  "redis": "ok",
  "version": "dev"
}
```

Código completo: [listing-03.json](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-36/es/parte-10/cap-36/listing-03.json)


El código HTTP importa tanto como el body: `200` significa listo, `503` significa no listo.

## Llamar a un endpoint con `fetch()`

Para un endpoint interno puedes usar `fetch()`:

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

Código completo: [listing-04.js](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-36/es/parte-10/cap-36/listing-04.js)


Este ejemplo no reemplaza los tests server-side: es solo el lado browser del contrato.

## Leer JSON entrante

Si agregas un endpoint JSON para crear un borrador de post, lee el body una vez y valida:

```php
<?php

declare(strict_types=1);

$payload = (string) $request->getBody();
$data = json_decode($payload, true, 512, JSON_THROW_ON_ERROR);

$title = trim((string) ($data['title'] ?? ''));
$message = trim((string) ($data['message'] ?? ''));
```

Código completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-36/es/parte-10/cap-36/listing-05.php)


Con PSR-7 el body es un stream. No construyas lógica de aplicación directamente sobre `php://input` cuando ya tienes `ServerRequestInterface`.

## Responses de validación

Una estructura simple para errores es:

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

Código completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-36/es/parte-10/cap-36/listing-06.php)


Para productos localizados, mueve los mensajes visibles para usuarios a una capa de traducción en lugar de mezclar idiomas en la misma response.

## Sesiones, CSRF y JSON

Si una request JSON parte del mismo sitio autenticado, valen las mismas reglas que para los forms:

- el usuario debe tener una sesión válida;
- el permiso debe comprobarse en el controller o en middleware;
- los datos deben validarse server-side;
- las acciones que cambian estado deben tener protección CSRF u otro mecanismo equivalente;
- la salida debe usar un formato estable.

REST no elimina la autenticación. Solo cambia la representación de la response.

## Smoke tests en CI/CD

La pipeline de release usa el mismo principio:

```yaml
for i in $(seq 1 30); do
  if curl -fsS https://staging.phpenterpriseblog.example.com/healthz | grep -q '"db":"ok"'; then
    echo "Smoke passed"; exit 0
  fi
  sleep 5
done
echo "Smoke failed"; exit 1
```

Código completo: [listing-07.yml](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-36/es/parte-10/cap-36/listing-07.yml)


Fuente real: [`.github/workflows/release.yml` en `lesson-7-5`](https://github.com/hidran/phpenterpriseblog/blob/lesson-7-5/.github/workflows/release.yml).

Esto no es un test completo de la aplicación, pero bloquea un deploy que ni siquiera puede conectarse al database.

## En resumen

JSON es un contrato. En el blog enterprise lo usamos para health checks, smoke tests y posibles endpoints internos. Con PSR-7/15 el controller devuelve responses explícitas, `json_encode()` falla con excepciones, los códigos HTTP tienen significado y las reglas de seguridad siguen siendo las mismas que para las páginas HTML.
