# 35. Docker, cache, CI/CD e operatività

Un'applicazione non finisce quando il codice funziona sul tuo portatile: quello è solo il punto di partenza. Il blog enterprise deve **avviarsi in modo riproducibile** su qualunque macchina, usare servizi esterni (database, cache) in modo controllato, dichiarare se è **in salute**, superare una batteria di controlli automatici prima di ogni rilascio e arrivare in produzione con un deploy tracciabile e reversibile. Questo capitolo copre proprio questo strato — l'**operatività** — ed è ciò che separa un esercizio MVC da un sistema che puoi davvero mandare online e tenere in piedi. Molti dei concetti qui non sono specifici di PHP: sono le pratiche con cui si porta *qualunque* applicazione in produzione.

## Docker runtime con PHP 8.5

Il primo problema è la riproducibilità: far sì che l'applicazione giri identica ovunque, non "dipende da cosa hai installato". La risposta è **Docker**, e il progetto usa PHP 8.5 FPM su Alpine, una distribuzione Linux minima:

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

Codice completo: [listing-01.Dockerfile](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-35/it/parte-09/cap-35/listing-01.Dockerfile)


Sorgente reale: [`deploy/docker/Dockerfile` a `lesson-4-1`](https://github.com/hidran/phpenterpriseblog/blob/lesson-4-1/deploy/docker/Dockerfile).


Un `Dockerfile` è la ricetta dell'ambiente: dice esattamente quale PHP, quali estensioni, quali librerie. Guarda un dettaglio raffinato in quel `RUN`: le librerie servono a compilare le estensioni (`pdo_mysql` per il database, `intl` per l'internazionalizzazione, `redis` per la cache) vengono installate in un pacchetto "virtuale" chiamato `.build` e poi **rimosse** con `apk del .build` alla fine. Perché? Perché gli strumenti di compilazione non servono per *eseguire* l'applicazione, solo per costruirla: tenerli nell'immagine finale la ingrasserebbe e allargherebbe la superficie d'attacco. È la stessa idea del *multi-stage build* con cui le dipendenze Composer vengono preparate in uno stage separato: l'immagine finale contiene **solo** ciò che serve a far girare l'app. Più piccola, più veloce da distribuire, più sicura.

## Ambiente locale con Compose

Un'applicazione reale non è mai sola: ha bisogno di un database, una cache, un server web. **Docker Compose** descrive l'intero stack in un file solo:

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

Codice completo: [listing-02.yml](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-35/it/parte-09/cap-35/listing-02.yml)


Sorgente reale: [`docker-compose.yml` a `lesson-4-2`](https://github.com/hidran/phpenterpriseblog/blob/lesson-4-2/docker-compose.yml).


Il file elenca i **servizi** — qui vedi `app` (PHP-FPM) e `nginx`, mentre lo stack completo aggiunge MySQL, Redis e MailHog per intercettare le email in sviluppo — e li collega tra loro. Nota `DB_HOST: mysql`: dentro Compose i servizi si raggiungono **per nome**, non per indirizzo IP, così l'app parla con il database chiamandolo semplicemente `mysql`. Il risultato pratico è che l'intero ambiente di sviluppo — con le stesse versioni di ogni componente per tutti — si avvia con un comando:

```bash
make up
open http://localhost:8080
```

Codice completo: [listing-03.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-35/it/parte-09/cap-35/listing-03.sh)


Sorgente reale: [`README.md` al commit `eb2e62a`](https://github.com/hidran/phpenterpriseblog/blob/eb2e62a774f6b20539e72f40f7d3fe9205ef4c5d/README.md).


Un solo `make up` riduce l'*onboarding* — il tempo che un nuovo sviluppatore impiega per diventare produttivo — da una giornata di configurazioni a qualche minuto. E siccome l'ambiente locale ha la stessa forma di quello di produzione, sparisce un'intera categoria di problemi: quelli che "in locale funziona".

## Health check

Un'applicazione in produzione deve saper rispondere a una domanda semplice ma cruciale: "sei viva, e riesci a parlare con i servizi da cui dipendi?".

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

Codice completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-35/it/parte-09/cap-35/listing-04.php)


Sorgente reale: [`src/Controllers/HealthController.php` a `lesson-4-3`](https://github.com/hidran/phpenterpriseblog/blob/lesson-4-3/src/Controllers/HealthController.php).


L'endpoint `/healthz` non renderizza una pagina: esegue una prova minima — una `SELECT 1` sul database — e risponde con un codice HTTP che una macchina può leggere: `200` se tutto va, `503` (servizio non disponibile) se il database non risponde. Sembra banale, ma è il pilastro dell'automazione: un orchestratore come Kubernetes interroga di continuo questo endpoint per decidere se instradare traffico verso un'istanza o riavviarla perché malata; il deploy lo usa per capire se la nuova versione è pronta prima di mandarle utenti; i test E2E lo aspettano prima di partire. La salute dell'applicazione smette di essere un'impressione e diventa un dato interrogabile.

## Cache PSR-16 con Redis

Per alleggerire il database, il progetto introduce una cache — ma dietro un'**interfaccia** standard, non legata a una tecnologia specifica:

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

Codice completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-35/it/parte-09/cap-35/listing-05.php)


Sorgente reale: [`src/Cache/RedisCache.php` a `lesson-5-1`](https://github.com/hidran/phpenterpriseblog/blob/lesson-5-1/src/Cache/RedisCache.php).


`RedisCache implements CacheInterface`: quell'interfaccia è **PSR-16**, lo standard PHP per le cache. È la stessa lezione del Capitolo 26 (programmare contro un contratto) applicata qui: il resto dell'applicazione conosce solo `CacheInterface`, non `Redis`. Domani puoi sostituire Redis con una cache in memoria per i test, o con un'altra tecnologia in produzione, e nessuno dei consumatori della cache se ne accorge — perché tutti dipendono dall'interfaccia, non dall'implementazione. Redis, in concreto, è un archivio chiave-valore in memoria: velocissimo, perfetto per tenere a portata di mano dati che costerebbe caro ricalcolare.

## Decorator del repository

Ora la domanda interessante: come si aggiunge la cache al `PostRepository` del Capitolo 33 senza sporcarlo? La risposta è un pattern elegante, il **decorator**:

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

Codice completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-35/it/parte-09/cap-35/listing-06.php)


Sorgente reale: [`src/Cache/CachedPostRepository.php` a `lesson-5-2`](https://github.com/hidran/phpenterpriseblog/blob/lesson-5-2/src/Cache/CachedPostRepository.php).


Segui la logica di `findById()`: prima cerca il post nella cache; se c'è (*cache hit*), lo restituisce senza toccare il database; se non c'è (*cache miss*), chiama `parent::findById()` — cioè la vera query SQL del repository originale — e prima di restituire il risultato lo mette in cache con una scadenza (`TTL_SHOW`). Il bello è cosa **non** è cambiato: `PostRepository`, con la sua SQL, è rimasto identico e ignaro della cache. Il caching è un livello **separato** che avvolge l'originale, aggiungendo comportamento senza modificarlo. È il principio *aperto/chiuso* — aperto all'estensione, chiuso alla modifica — reso concreto, e il vantaggio è che puoi testare la logica di cache in isolamento e attivarla o disattivarla scegliendo quale delle due classi registrare nel container.

## Sessioni Redis

C'è un problema che nasce quando l'applicazione gira su **più istanze** contemporaneamente (più *pod*, in gergo Kubernetes) per reggere il carico. Le sessioni PHP, di default, vivono come file sul disco locale del server; ma se un utente a una richiesta finisce sull'istanza A e alla successiva sull'istanza B, la sua sessione — memorizzata sul disco di A — non c'è più su B, e risulta sloggato. La soluzione è spostare le sessioni in un archivio condiviso, Redis:

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

Codice completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-35/it/parte-09/cap-35/listing-07.php)


Sorgente reale: [`src/Session/RedisSessionHandler.php` a `lesson-5-3`](https://github.com/hidran/phpenterpriseblog/blob/lesson-5-3/src/Session/RedisSessionHandler.php).


Implementando `SessionHandlerInterface`, questa classe dice a PHP di leggere e scrivere le sessioni su Redis invece che su file. Ora tutte le istanze condividono lo stesso archivio di sessioni, e l'utente resta loggato indipendentemente dall'istanza che lo serve. Nota il `setex`: scrive il dato **con una scadenza** (`$this->ttl`), così le sessioni abbandonate si autodistruggono. È lo stesso identico problema concettuale del remember me nello User Management System (Capitolo 24): lo stato dell'utente va gestito con confini chiari, una scadenza e la possibilità di revocarlo. Cambia la tecnologia, non il principio.

## CI con GitHub Actions

Come si garantisce che ogni modifica al codice non rompa nulla, senza affidarsi alla memoria di chi la scrive? Con la **CI** (*continuous integration*): una pipeline che, a ogni push, esegue automaticamente tutti i controlli.

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

Codice completo: [listing-08.yml](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-35/it/parte-09/cap-35/listing-08.yml)


Sorgente reale: [`.github/workflows/ci.yml` a `lesson-6-1`](https://github.com/hidran/phpenterpriseblog/blob/lesson-6-1/.github/workflows/ci.yml).


Questa pipeline GitHub Actions esegue tre controlli in sequenza: `composer cs` verifica lo **stile** del codice (formattazione coerente), `composer stan` lancia l'**analisi statica** con PHPStan (che trova errori di tipo e bug potenziali *senza* eseguire il codice), e `composer test` fa girare la **suite di test**. Il tutto su una `matrix` di due versioni di PHP, 8.4 e 8.5: la stessa pipeline gira due volte, verificando la compatibilità con entrambe (il libro resta comunque orientato a PHP 8.5). Il valore della CI è che questi controlli non dipendono più dalla disciplina del singolo: nessuno può dimenticarsi di lanciarli, perché scattano da soli a ogni push, e un cambiamento che rompe stile, tipi o test viene bloccato prima di entrare nel ramo principale.

## Deploy con Helm

L'ultimo passo è portare l'immagine in produzione. Il progetto usa immagini taggate, un registry (ECR), un cluster Kubernetes (EKS) e **Helm** per orchestrare il rilascio:

```yaml
helm upgrade --install phpenterpriseblog deploy/helm/phpenterpriseblog \
  --namespace phpenterpriseblog-prod \
  --values deploy/helm/phpenterpriseblog/values.prod.yaml \
  --set image.repository="$ECR_REGISTRY/phpenterpriseblog" \
  --set image.tag="$IMAGE_TAG" \
  --wait --timeout 10m --atomic
```

Codice completo: [listing-09.yml](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-35/it/parte-09/cap-35/listing-09.yml)


Sorgente reale: [`.github/workflows/release.yml` a `lesson-7-5`](https://github.com/hidran/phpenterpriseblog/blob/lesson-7-5/.github/workflows/release.yml).


Concentrati sulle due opzioni finali, perché racchiudono la filosofia del deploy sicuro. `--wait` dice a Helm di **aspettare** che il rilascio sia effettivamente sano (usando anche l'health check di prima) invece di dichiarare vittoria appena i comandi sono partiti. `--atomic` fa la cosa più importante: se il rilascio fallisce entro il timeout, torna **automaticamente indietro** alla versione precedente, senza lasciare la produzione in uno stato a metà. È un deploy "tutto o niente" — o la nuova versione entra sana, o non entra affatto — e la scelta è documentata nell'ADR `0004`. L'immagine taggata (`$IMAGE_TAG`) garantisce infine la tracciabilità: sai esattamente quale versione del codice è in produzione, e a quale puoi tornare.

## E2E e ADR

L'ultima rete di sicurezza sono i test **end-to-end**, che con Playwright verificano flussi reali guidando un vero browser:

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

Codice completo: [listing-10.ts](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-35/it/parte-09/cap-35/listing-10.ts)


Sorgente reale: [`tests/E2e/anonymous-can-read.spec.ts` a `lesson-8-2`](https://github.com/hidran/phpenterpriseblog/blob/lesson-8-2/tests/E2e/anonymous-can-read.spec.ts).


Mentre i test unitari verificano un pezzo in isolamento, questo test E2E verifica l'applicazione **intera e assemblata**, dal punto di vista dell'utente: apri la home, trovi il link a un post, clicchi, e devi finire su una pagina il cui URL è `/posts/` seguito da un numero. È la prova che tutti i livelli costruiti nei capitoli precedenti — router, controller, repository, view — funzionano *insieme*. A chiudere il progetto ci sono gli **ADR** (Architecture Decision Record), i documenti che spiegano il *perché* delle scelte importanti — Composer/PSR-4, DTO contro repository, migrazioni forward-only, release Helm atomiche — così che non restino solo nella memoria di chi le ha prese. Un progetto che documenta le proprie decisioni è un progetto che altri possono ereditare e mantenere.

## In sintesi

L'ultimo tratto del progetto mostra che "enterprise" non significa complicare per il gusto di farlo. Significa rendere **riproducibile** ogni cosa: l'ambiente (Docker e Compose), la salute (health check), le prestazioni (cache PSR-16 dietro interfaccia, aggiunta con un decorator), lo stato condiviso (sessioni Redis), la qualità (CI che verifica stile, tipi e test a ogni push) e il rilascio (deploy Helm atomico e reversibile). Il blog resta piccolo come funzionalità, ma ora possiede gli stessi confini operativi di un'applicazione reale — ed è questa, più di ogni singola libreria, la differenza tra scrivere codice e mandare in produzione un sistema.
