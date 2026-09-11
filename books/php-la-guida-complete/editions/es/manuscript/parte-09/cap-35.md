# 35. Docker, cache, CI/CD y operatividad

Una aplicación no termina cuando el código funciona en tu portátil: eso es solo el punto de partida. El blog enterprise debe **arrancar de forma reproducible** en cualquier máquina, usar servicios externos (base de datos, cache) de forma controlada, declarar si está **sano**, superar una batería de comprobaciones automáticas antes de cada release y llegar a producción con un deploy trazable y reversible. Este capítulo cubre justamente esta capa — la **operatividad** — y es lo que separa un ejercicio MVC de un sistema que de verdad puedes poner online y mantener en pie. Muchos de los conceptos de aquí no son específicos de PHP: son las prácticas con las que se lleva *cualquier* aplicación a producción.

## Runtime Docker con PHP 8.5

El primer problema es la reproducibilidad: hacer que la aplicación funcione idéntica en todas partes, no "depende de lo que tengas instalado". La respuesta es **Docker**, y el proyecto usa PHP 8.5 FPM sobre Alpine, una distribución Linux mínima:

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

Código completo: [listing-01.Dockerfile](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-35/es/parte-09/cap-35/listing-01.Dockerfile)


Fuente real: [`deploy/docker/Dockerfile` en `lesson-4-1`](https://github.com/hidran/phpenterpriseblog/blob/lesson-4-1/deploy/docker/Dockerfile).


Un `Dockerfile` es la receta del entorno: dice exactamente qué PHP, qué extensiones, qué librerías. Fíjate en un detalle refinado de ese `RUN`: las librerías que sirven para compilar las extensiones (`pdo_mysql` para la base de datos, `intl` para la internacionalización, `redis` para la cache) se instalan en un paquete "virtual" llamado `.build` y luego se **eliminan** con `apk del .build` al final. ¿Por qué? Porque las herramientas de compilación no hacen falta para *ejecutar* la aplicación, solo para construirla: mantenerlas en la imagen final la engordaría y ampliaría la superficie de ataque. Es la misma idea del *multi-stage build* con el que las dependencias Composer se preparan en un stage separado: la imagen final contiene **solo** lo que hace falta para ejecutar la app. Más pequeña, más rápida de distribuir, más segura.

## Entorno local con Compose

Una aplicación real nunca está sola: necesita una base de datos, una cache, un servidor web. **Docker Compose** describe todo el stack en un solo fichero:

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

Código completo: [listing-02.yml](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-35/es/parte-09/cap-35/listing-02.yml)


Fuente real: [`docker-compose.yml` en `lesson-4-2`](https://github.com/hidran/phpenterpriseblog/blob/lesson-4-2/docker-compose.yml).


El fichero enumera los **servicios** — aquí ves `app` (PHP-FPM) y `nginx`, mientras que el stack completo añade MySQL, Redis y MailHog para interceptar las emails en desarrollo — y los enlaza entre sí. Fíjate en `DB_HOST: mysql`: dentro de Compose los servicios se alcanzan **por nombre**, no por dirección IP, así la app habla con la base de datos llamándola simplemente `mysql`. El resultado práctico es que todo el entorno de desarrollo — con las mismas versiones de cada componente para todos — arranca con un comando:

```bash
make up
open http://localhost:8080
```

Código completo: [listing-03.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-35/es/parte-09/cap-35/listing-03.sh)


Fuente real: [`README.md` en el commit `eb2e62a`](https://github.com/hidran/phpenterpriseblog/blob/eb2e62a774f6b20539e72f40f7d3fe9205ef4c5d/README.md).


Un solo `make up` reduce el *onboarding* — el tiempo que un nuevo desarrollador tarda en volverse productivo — de un día de configuraciones a unos minutos. Y como el entorno local tiene la misma forma que el de producción, desaparece toda una categoría de problemas: los que "en local funciona".

## Health check

Una aplicación en producción debe saber responder a una pregunta sencilla pero crucial: "¿estás viva y puedes hablar con los servicios de los que dependes?".

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

Código completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-35/es/parte-09/cap-35/listing-04.php)


Fuente real: [`src/Controllers/HealthController.php` en `lesson-4-3`](https://github.com/hidran/phpenterpriseblog/blob/lesson-4-3/src/Controllers/HealthController.php).


El endpoint `/healthz` no renderiza una página: ejecuta una prueba mínima — un `SELECT 1` contra la base de datos — y responde con un código HTTP que una máquina puede leer: `200` si todo va bien, `503` (servicio no disponible) si la base de datos no responde. Parece trivial, pero es el pilar de la automatización: un orquestador como Kubernetes interroga este endpoint de continuo para decidir si enrutar tráfico hacia una instancia o reiniciarla porque está enferma; el deploy lo usa para saber si la nueva versión está lista antes de mandarle usuarios; los tests E2E lo esperan antes de arrancar. La salud de la aplicación deja de ser una impresión y se convierte en un dato consultable.

## Cache PSR-16 con Redis

Para aliviar la base de datos, el proyecto introduce una cache — pero detrás de una **interfaz** estándar, no ligada a una tecnología específica:

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

Código completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-35/es/parte-09/cap-35/listing-05.php)


Fuente real: [`src/Cache/RedisCache.php` en `lesson-5-1`](https://github.com/hidran/phpenterpriseblog/blob/lesson-5-1/src/Cache/RedisCache.php).


`RedisCache implements CacheInterface`: esa interfaz es **PSR-16**, el estándar PHP para las caches. Es la misma lección del Capítulo 26 (programar contra un contrato) aplicada aquí: el resto de la aplicación conoce solo `CacheInterface`, no `Redis`. Mañana puedes reemplazar Redis por una cache en memoria para los tests, o por otra tecnología en producción, y ninguno de los consumidores de la cache se entera — porque todos dependen de la interfaz, no de la implementación. Redis, en concreto, es un almacén clave-valor en memoria: rapidísimo, perfecto para tener a mano datos que costaría caro recalcular.

## Decorator del repository

Ahora la pregunta interesante: ¿cómo se añade la cache al `PostRepository` del Capítulo 33 sin ensuciarlo? La respuesta es un patrón elegante, el **decorator**:

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

Código completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-35/es/parte-09/cap-35/listing-06.php)


Fuente real: [`src/Cache/CachedPostRepository.php` en `lesson-5-2`](https://github.com/hidran/phpenterpriseblog/blob/lesson-5-2/src/Cache/CachedPostRepository.php).


Sigue la lógica de `findById()`: primero busca el post en la cache; si está (*cache hit*), lo devuelve sin tocar la base de datos; si no está (*cache miss*), llama a `parent::findById()` — la verdadera query SQL del repository original — y antes de devolver el resultado lo guarda en la cache con una expiración (`TTL_SHOW`). Lo bonito es lo que **no** cambió: `PostRepository`, con su SQL, quedó idéntico e ignorante de la cache. El caching es una capa **separada** que envuelve al original, añadiendo comportamiento sin modificarlo. Es el principio *abierto/cerrado* — abierto a la extensión, cerrado a la modificación — hecho concreto, y la ventaja es que puedes testear la lógica de cache de forma aislada y activarla o desactivarla eligiendo cuál de las dos clases registrar en el container.

## Sesiones Redis

Hay un problema que surge cuando la aplicación corre sobre **varias instancias** a la vez (varios *pods*, en jerga Kubernetes) para aguantar la carga. Las sesiones PHP, por defecto, viven como ficheros en el disco local del servidor; pero si un usuario en una request acaba en la instancia A y en la siguiente en la instancia B, su sesión — almacenada en el disco de A — no está en B, y aparece deslogueado. La solución es mover las sesiones a un almacén compartido, Redis:

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

Código completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-35/es/parte-09/cap-35/listing-07.php)


Fuente real: [`src/Session/RedisSessionHandler.php` en `lesson-5-3`](https://github.com/hidran/phpenterpriseblog/blob/lesson-5-3/src/Session/RedisSessionHandler.php).


Al implementar `SessionHandlerInterface`, esta clase le dice a PHP que lea y escriba las sesiones en Redis en lugar de en ficheros. Ahora todas las instancias comparten el mismo almacén de sesiones, y el usuario sigue logueado independientemente de la instancia que lo sirva. Fíjate en el `setex`: escribe el dato **con una expiración** (`$this->ttl`), así las sesiones abandonadas se autodestruyen. Es exactamente el mismo problema conceptual que remember me en el User Management System (Capítulo 24): el estado del usuario debe gestionarse con límites claros, una expiración y la posibilidad de revocarlo. Cambia la tecnología, no el principio.

## CI con GitHub Actions

¿Cómo se garantiza que cada cambio en el código no rompe nada, sin fiarse de la memoria de quien lo escribe? Con la **CI** (*continuous integration*): una pipeline que, en cada push, ejecuta automáticamente todas las comprobaciones.

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

Código completo: [listing-08.yml](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-35/es/parte-09/cap-35/listing-08.yml)


Fuente real: [`.github/workflows/ci.yml` en `lesson-6-1`](https://github.com/hidran/phpenterpriseblog/blob/lesson-6-1/.github/workflows/ci.yml).


Esta pipeline de GitHub Actions ejecuta tres comprobaciones en secuencia: `composer cs` verifica el **estilo** del código (formato coherente), `composer stan` lanza el **análisis estático** con PHPStan (que encuentra errores de tipo y bugs potenciales *sin* ejecutar el código), y `composer test` hace correr la **suite de tests**. Todo ello sobre una `matrix` de dos versiones de PHP, 8.4 y 8.5: la misma pipeline corre dos veces, verificando la compatibilidad con ambas (el libro sigue orientado a PHP 8.5). El valor de la CI es que estas comprobaciones ya no dependen de la disciplina del individuo: nadie puede olvidarse de lanzarlas, porque saltan solas en cada push, y un cambio que rompe estilo, tipos o tests se bloquea antes de entrar en la rama principal.

## Deploy con Helm

El último paso es llevar la imagen a producción. El proyecto usa imágenes taggeadas, un registry (ECR), un cluster Kubernetes (EKS) y **Helm** para orquestar el release:

```yaml
helm upgrade --install phpenterpriseblog deploy/helm/phpenterpriseblog \
  --namespace phpenterpriseblog-prod \
  --values deploy/helm/phpenterpriseblog/values.prod.yaml \
  --set image.repository="$ECR_REGISTRY/phpenterpriseblog" \
  --set image.tag="$IMAGE_TAG" \
  --wait --timeout 10m --atomic
```

Código completo: [listing-09.yml](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-35/es/parte-09/cap-35/listing-09.yml)


Fuente real: [`.github/workflows/release.yml` en `lesson-7-5`](https://github.com/hidran/phpenterpriseblog/blob/lesson-7-5/.github/workflows/release.yml).


Concéntrate en las dos opciones finales, porque encierran la filosofía del deploy seguro. `--wait` le dice a Helm que **espere** a que el release esté realmente sano (usando, entre otras cosas, el health check de antes) en lugar de cantar victoria en cuanto los comandos han arrancado. `--atomic` hace lo más importante: si el release falla dentro del timeout, vuelve **atrás automáticamente** a la versión anterior, sin dejar la producción en un estado a medias. Es un deploy "todo o nada" — o la nueva versión entra sana, o no entra en absoluto — y la decisión está documentada en el ADR `0004`. La imagen taggeada (`$IMAGE_TAG`) garantiza, por último, la trazabilidad: sabes exactamente qué versión del código está en producción, y a cuál puedes volver.

## E2E y ADR

La última red de seguridad son los tests **end-to-end**, que con Playwright verifican flujos reales guiando un navegador de verdad:

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

Código completo: [listing-10.ts](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-35/es/parte-09/cap-35/listing-10.ts)


Fuente real: [`tests/E2e/anonymous-can-read.spec.ts` en `lesson-8-2`](https://github.com/hidran/phpenterpriseblog/blob/lesson-8-2/tests/E2e/anonymous-can-read.spec.ts).


Mientras que los tests unitarios verifican una pieza de forma aislada, este test E2E verifica la aplicación **entera y ensamblada**, desde el punto de vista del usuario: abre la home, encuentra el enlace a un post, haz clic, y debes acabar en una página cuya URL es `/posts/` seguido de un número. Es la prueba de que todas las capas construidas en los capítulos anteriores — router, controller, repository, view — funcionan *juntas*. Cerrando el proyecto están los **ADR** (Architecture Decision Record), los documentos que explican el *porqué* de las decisiones importantes — Composer/PSR-4, DTO frente a repository, migraciones forward-only, releases Helm atómicas — para que no vivan solo en la memoria de quien las tomó. Un proyecto que documenta sus decisiones es un proyecto que otros pueden heredar y mantener.

## En resumen

El último tramo del proyecto muestra que "enterprise" no significa complicar por gusto. Significa hacer **reproducible** cada cosa: el entorno (Docker y Compose), la salud (health check), el rendimiento (cache PSR-16 detrás de una interfaz, añadida con un decorator), el estado compartido (sesiones Redis), la calidad (CI que verifica estilo, tipos y tests en cada push) y el release (deploy Helm atómico y reversible). El blog sigue siendo pequeño en funcionalidades, pero ahora posee los mismos límites operativos que una aplicación real — y eso, más que cualquier librería concreta, es la diferencia entre escribir código y poner un sistema en producción.
