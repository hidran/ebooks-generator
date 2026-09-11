# 14. Cookie

I cookie sono piccoli dati che il server chiede al browser di conservare. A ogni richiesta successiva verso lo stesso dominio, il browser li rimanda al server. In PHP li userai per preferenze, consenso, tracciamento tecnico e, con molta attenzione, per meccanismi come il "remember me".

## Impostare un cookie

Per inviare un cookie si usa `setcookie()`:

```php
<?php
setcookie("theme", "dark");
```

Codice completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-14/it/parte-04/cap-14/listing-01.php)


Il cookie non compare subito in `$_COOKIE` nella stessa richiesta. Viene inviato negli header della risposta, salvato dal browser e sarà disponibile dalla richiesta successiva.

Per impostare una scadenza:

```php
<?php
setcookie("theme", "dark", time() + 60 * 60 * 24 * 30);
```

Codice completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-14/it/parte-04/cap-14/listing-02.php)


Qui il cookie dura trenta giorni. Senza scadenza, il cookie è di sessione e il browser può eliminarlo alla chiusura.

## Leggere un cookie

I cookie ricevuti sono in `$_COOKIE`:

```php
<?php
$theme = $_COOKIE["theme"] ?? "light";
```

Codice completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-14/it/parte-04/cap-14/listing-03.php)


Come sempre con dati esterni, non fidarti del valore. Il browser è controllato dall'utente: un cookie può essere modificato, cancellato o inventato.

## Opzioni moderne

La forma più leggibile di `setcookie()` usa un array di opzioni:

```php
<?php
setcookie("theme", "dark", [
    "expires" => time() + 60 * 60 * 24 * 30,
    "path" => "/",
    "secure" => true,
    "httponly" => true,
    "samesite" => "Lax",
]);
```

Codice completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-14/it/parte-04/cap-14/listing-04.php)


Le opzioni più importanti sono:

- `expires`: scadenza del cookie;
- `path`: percorso per cui il cookie è valido;
- `secure`: invio solo su HTTPS;
- `httponly`: non accessibile da JavaScript;
- `samesite`: riduce alcuni rischi legati a richieste cross-site.

Durante lo sviluppo locale potresti non usare HTTPS. In quel caso `secure => true` impedisce al browser di salvare il cookie. In produzione, invece, i cookie sensibili devono viaggiare solo su HTTPS.

## Eliminare un cookie

Per eliminare un cookie lo si riscrive con scadenza nel passato:

```php
<?php
setcookie("theme", "", time() - 3600, "/");
```

Codice completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-14/it/parte-04/cap-14/listing-05.php)


Il `path` deve coincidere con quello usato quando il cookie è stato creato. Se non coincide, il browser può conservare un cookie apparentemente identico ma associato a un percorso diverso.

## Header già inviati

`setcookie()` invia header HTTP. Gli header devono partire prima del corpo della risposta. Questo codice può generare errore:

```php
<?php
echo "Ciao";
setcookie("theme", "dark");
```

Codice completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-14/it/parte-04/cap-14/listing-06.php)


Il messaggio tipico è "headers already sent". La soluzione corretta è organizzare il codice in modo che cookie, redirect e sessioni vengano gestiti prima di stampare HTML.

In sviluppo puoi incontrare anche l'output buffering:

```php
<?php
ob_start();

echo "Ciao";
setcookie("theme", "dark");

ob_end_flush();
```

Codice completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-14/it/parte-04/cap-14/listing-07.php)


L'output buffering può aiutare in casi specifici, ma non deve diventare una scusa per mischiare logica e presentazione senza ordine.

## Cookie e sessioni

Le sessioni PHP usano normalmente un cookie con l'identificatore della sessione. Il dato vero resta sul server; nel browser c'è solo una chiave. Questa è la differenza fondamentale:

- cookie: il valore è nel browser;
- sessione: il valore è sul server, il browser conserva l'identificatore.

Per dati sensibili preferisci la sessione. Per preferenze non sensibili può bastare un cookie.

## Cookie e sicurezza

Non salvare password, ruoli o dati riservati in chiaro dentro un cookie. Anche se imposti `httponly`, l'utente può vedere e modificare il cookie dal browser o dagli strumenti di sviluppo.

Per un "remember me" sicuro non salveremo l'ID utente da solo. Useremo un token casuale, lo salveremo nel database in forma controllata e lo ruoteremo dopo l'uso.

## In sintesi

I cookie sono semplici da usare, ma facili da usare male. Impostali prima dell'output, leggili sempre con valori di default, cancellali replicando path e dominio, e usa opzioni moderne come `httponly`, `secure` e `samesite`. Nei capitoli di progetto li useremo per costruire un login persistente senza fidarci ciecamente del browser.
