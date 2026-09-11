# 38. Inviare email con PHPMailer, MailHog e Mailtrap

Molte applicazioni devono inviare email: conferme di registrazione, reset password, notifiche, ricevute. PHP ha una funzione `mail()`, ma in progetti reali è meglio usare SMTP e una libreria come PHPMailer.

## Perché non affidarsi a `mail()`

`mail()` dipende dalla configurazione del server. In locale spesso non funziona; in produzione può inviare messaggi senza autenticazione moderna, con problemi di deliverability.

SMTP è più esplicito: host, porta, username, password, cifratura. PHPMailer gestisce questi dettagli con un'API chiara.

## Installare PHPMailer

```bash
composer require phpmailer/phpmailer
```

Codice completo: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-38/it/parte-10/cap-38/listing-01.sh)


Uso base:

```php
<?php
use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception;

$mail = new PHPMailer(true);

try {
    $mail->isSMTP();
    $mail->Host = "localhost";
    $mail->Port = 1025;

    $mail->setFrom("noreply@example.com", "PHP Guida");
    $mail->addAddress("mario@example.com");

    $mail->Subject = "Benvenuto";
    $mail->Body = "Grazie per la registrazione.";

    $mail->send();
} catch (Exception $e) {
    error_log($e->getMessage());
}
```

Codice completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-38/it/parte-10/cap-38/listing-02.php)


## MailHog in locale

MailHog è un server SMTP finto per sviluppo. L'applicazione invia email a MailHog, MailHog le cattura e tu le vedi in una web UI. Nessun messaggio parte davvero verso utenti reali.

Configurazione tipica:

```text
SMTP host: localhost
SMTP port: 1025
Web UI: http://localhost:8025
```

Codice completo: [listing-03.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-38/it/parte-10/cap-38/listing-03.txt)


Questo è ideale per testare reset password, template e contenuto senza rischiare invii accidentali.

## `mhsendmail`

In alcuni ambienti puoi configurare PHP perché la funzione `mail()` invii a MailHog tramite `mhsendmail`. Nel `php.ini` imposti il percorso del comando sendmail. È utile se devi testare codice legacy che usa `mail()`.

Per codice nuovo, preferisci PHPMailer con SMTP esplicito.

## Mailtrap

Mailtrap offre inbox SMTP di test nel cloud. È comodo quando l'applicazione gira in un ambiente dove MailHog locale non è raggiungibile.

Le credenziali SMTP non vanno scritte nel codice:

```php
<?php
$mail->Host = getenv("SMTP_HOST");
$mail->Port = (int) getenv("SMTP_PORT");
$mail->Username = getenv("SMTP_USER");
$mail->Password = getenv("SMTP_PASSWORD");
```

Codice completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-38/it/parte-10/cap-38/listing-04.php)


In produzione userai un provider reale, ma l'interfaccia resta la stessa.

## Email HTML

```php
<?php
$mail->isHTML(true);
$mail->Subject = "Reset password";
$mail->Body = "<p>Clicca sul link per reimpostare la password.</p>";
$mail->AltBody = "Clicca sul link per reimpostare la password.";
```

Codice completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-38/it/parte-10/cap-38/listing-05.php)


Imposta sempre anche `AltBody`: alcuni client o filtri preferiscono testo semplice.

## Laravel e Mailtrap

Laravel ha un sistema mail integrato. La configurazione vive in `.env`:

```text
MAIL_MAILER=smtp
MAIL_HOST=sandbox.smtp.mailtrap.io
MAIL_PORT=2525
MAIL_USERNAME=your_mailtrap_username
MAIL_PASSWORD=your_mailtrap_password
```

Codice completo: [listing-06.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-38/it/parte-10/cap-38/listing-06.txt)


Anche se questo libro lavora molto senza framework, vedere Laravel aiuta a riconoscere lo stesso concetto in un sistema più strutturato.

## In sintesi

Per inviare email in modo serio usa SMTP, credenziali in variabili d'ambiente e una libreria come PHPMailer. In locale cattura tutto con MailHog; per ambienti condivisi usa Mailtrap; in produzione passa a un provider reale. Non testare mai email su utenti veri finché il flusso non è stato provato in un ambiente sicuro.
