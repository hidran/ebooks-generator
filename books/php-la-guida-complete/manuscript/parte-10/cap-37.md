# 37. Deploy su Heroku

Un'applicazione non è completa finché resta solo sulla tua macchina. Il deploy porta il progetto online e introduce nuove variabili: ambiente, database remoto, configurazione, log, percorsi e differenze tra sviluppo e produzione.

## Preparare l'applicazione

Prima del deploy controlla:

- il punto di ingresso pubblico (`public/index.php`);
- Composer configurato;
- nessuna password hardcoded;
- configurazione letta da variabili d'ambiente;
- errori non mostrati in produzione;
- file non necessari esclusi dal deploy.

Una configurazione minima può leggere variabili:

```php
<?php
$dsn = getenv("DATABASE_DSN");
$user = getenv("DATABASE_USER");
$password = getenv("DATABASE_PASSWORD");
```

Codice completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-37/it/parte-10/cap-37/listing-01.php)


## Procfile

Heroku usa un `Procfile` per sapere come avviare l'app:

```text
web: vendor/bin/heroku-php-apache2 public/
```

Codice completo: [listing-02.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-37/it/parte-10/cap-37/listing-02.txt)


Questo indica che la root web è `public/`, non la cartella del progetto.

## Composer in produzione

Heroku rileva un'app PHP dalla presenza di `composer.json`. Assicurati che la versione PHP richiesta sia dichiarata:

```json
{
  "require": {
    "php": "^8.5"
  }
}
```

Codice completo: [listing-03.json](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-37/it/parte-10/cap-37/listing-03.json)


Durante il deploy Heroku esegue `composer install` e prepara `vendor/`.

## Database remoto

Il database locale non viene caricato automaticamente. Devi creare un database remoto, configurare le credenziali e applicare lo schema.

Il principio è lo stesso:

```sql
CREATE TABLE users (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(190) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE posts (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NULL,
    title VARCHAR(190) NOT NULL,
    body TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Codice completo: [listing-04.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-37/it/parte-10/cap-37/listing-04.sql)


In progetti reali userai migrazioni. Qui puoi eseguire manualmente lo schema, ma tieni un file SQL versionato per non perdere i passaggi.

## File upload in produzione

Molte piattaforme, Heroku incluso, hanno filesystem effimero: i file caricati possono sparire a ogni deploy o riavvio. Per avatar e immagini in produzione serve storage esterno, come S3 o servizi compatibili.

Questo è un punto importante: il codice di upload funziona localmente, ma l'architettura di produzione deve decidere dove conservare file persistenti.

## Log

In produzione non guardi lo schermo del browser per capire gli errori. Usi log:

```bash
heroku logs --tail
```

Codice completo: [listing-05.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-37/it/parte-10/cap-37/listing-05.sh)


Nel codice, `error_log()` è il minimo. Per errori seri, strumenti come Sentry aiutano a vedere stack trace, frequenza e contesto.

## Percorsi e autoload

Se in locale un percorso funziona "per caso", in produzione può rompersi. Usa sempre `__DIR__` e percorsi assoluti derivati dalla struttura del progetto:

```php
<?php
require __DIR__ . "/../vendor/autoload.php";
```

Codice completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-37/it/parte-10/cap-37/listing-06.php)


Non dipendere dalla cartella corrente.

## In sintesi

Il deploy richiede disciplina: configurazione fuori dal codice, root pubblica corretta, Composer, database remoto, log e attenzione ai file persistenti. Heroku semplifica l'avvio, ma non elimina le decisioni architetturali. La differenza tra progetto didattico e applicazione reale comincia qui.
