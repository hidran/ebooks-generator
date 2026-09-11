# Checklist PHP 8.5 e prossimi passi {.unnumbered}

Il codice del libro usa PHP 8.5 come versione di riferimento. Prima di pubblicare o distribuire un progetto reale, installa sempre l'ultima patch disponibile del ramo 8.5.x e controlla le note di rilascio ufficiali.

## Novità PHP 8.5 da conoscere

- **Estensione URI:** usa le classi `Uri\Rfc3986\Uri` e `Uri\WhatWg\Url` quando devi analizzare o normalizzare URL in modo più robusto rispetto a `parse_url()`.
- **Pipe operator `|>`:** rende leggibili trasformazioni successive senza variabili intermedie inutili.
- **`clone()` con override di proprietà:** semplifica i metodi `with...()` nelle classi `readonly`.
- **Attributo `#[\NoDiscard]`:** segnala quando il valore restituito da una funzione importante viene ignorato.
- **Closure e callable in espressioni costanti:** utile in attributi, valori di default e configurazioni dichiarative.
- **cURL share persistenti:** riducono il costo di inizializzazione in richieste ripetute.
- **`array_first()` e `array_last()`:** leggono il primo o l'ultimo elemento senza combinare `array_key_first()` o `array_key_last()` a mano.

## Impostare un nuovo progetto

Parti da vincoli espliciti e autoload PSR-4:

```json
{
  "require": {
    "php": "^8.5"
  },
  "autoload": {
    "psr-4": {
      "App\\": "src/"
    }
  }
}
```

Codice completo: [listing-01.json](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-appendix-php85-checklist/it/zz-back-matter/00-php85-checklist/listing-01.json)


Metti `strict_types` nei file PHP che scrivi tu:

```php
<?php
declare(strict_types=1);

namespace App;
```

Codice completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-appendix-php85-checklist/it/zz-back-matter/00-php85-checklist/listing-02.php)


## Checklist di produzione

- Usa Composer e un autoload PSR-4, non `require` sparsi nel progetto.
- Usa PDO con `PDO::ERRMODE_EXCEPTION`, charset `utf8mb4` e prepared statement.
- Non concatenare input utente dentro SQL, HTML, header HTTP o percorsi di file.
- Esegui l'escape dell'output HTML con `htmlspecialchars(..., ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8')`.
- Usa `password_hash()` e `password_verify()` per le password.
- Usa `random_bytes()` o `random_int()` per token e valori casuali di sicurezza.
- Imposta cookie con `secure`, `httponly` e `samesite`.
- Tieni configurazione, password e token in variabili d'ambiente.
- In produzione disattiva `display_errors`, scrivi log strutturati e monitora errori ed eccezioni.
- Aggiorna dipendenze e runtime con regolarità: sicurezza e compatibilità dipendono dalle patch, non solo dalla major version.
