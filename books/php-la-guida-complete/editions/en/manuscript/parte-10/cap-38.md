# 38. Send emails with PHPMailer, MailHog and Mailtrap

Many applications need to send emails: registration confirmations, password resets, notifications, receipts. PHP has a function `mail()`, but in real projects it's better to use SMTP and a library like PHPMailer.

## Why not rely on `mail()`

`mail()` depends on the server configuration. Locally it often doesn't work; in production it can send messages without modern authentication, with deliverability problems.

SMTP is more explicit: host, port, username, password, encryption. PHPMailer handles these details with a clean API.

## Install PHPMailer

```bash
composer require phpmailer/phpmailer
```

Full source: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-38/en/parte-10/cap-38/listing-01.sh)


Basic use:

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
    $mail->addAddress("john@example.com");

    $mail->Subject = "Welcome";
    $mail->Body = "Thank you for registering.";

    $mail->send();
} catch (Exception $e) {
    error_log($e->getMessage());
}
```

Full source: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-38/en/parte-10/cap-38/listing-02.php)


## MailHog locally

MailHog is a mock SMTP server for development. The application sends emails to MailHog, MailHog captures them and you see them in a web UI. No messages actually go out to real users.

Typical configuration:

```text
SMTP host: localhost
SMTP port: 1025
Web UI: http://localhost:8025
```

Full source: [listing-03.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-38/en/parte-10/cap-38/listing-03.txt)


This is ideal for testing password resets, templates and content without risking accidental submissions.

## `mhsendmail`

In some environments you can configure PHP to have the `mail()` function send to MailHog via `mhsendmail`. In `php.ini` you set the path to the sendmail command. This is useful if you need to test legacy code that uses `mail()`.

For new code, prefer PHPMailer with explicit SMTP.

## Mailtrap

Mailtrap offers test SMTP inboxes in the cloud. This is convenient when the application runs in an environment where local MailHog is not reachable.

SMTP credentials should not be written in code:

```php
<?php
$mail->Host = getenv("SMTP_HOST");
$mail->Port = (int) getenv("SMTP_PORT");
$mail->Username = getenv("SMTP_USER");
$mail->Password = getenv("SMTP_PASSWORD");
```

Full source: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-38/en/parte-10/cap-38/listing-04.php)


In production you will use a real provider, but the interface remains the same.

## HTML emails

```php
<?php
$mail->isHTML(true);
$mail->Subject = "Reset password";
$mail->Body = "<p>Click the link to reset your password.</p>";
$mail->AltBody = "Click the link to reset your password.";
```

Full source: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-38/en/parte-10/cap-38/listing-05.php)


Always also set `AltBody`: some clients or filters prefer plain text.

## Laravel and Mailtrap

Laravel has a built-in email system. The configuration lives in `.env`:

```text
MAIL_MAILER=smtp
MAIL_HOST=sandbox.smtp.mailtrap.io
MAIL_PORT=2525
MAIL_USERNAME=your_mailtrap_username
MAIL_PASSWORD=your_mailtrap_password
```

Full source: [listing-06.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-38/en/parte-10/cap-38/listing-06.txt)


Even though this book works a lot without frameworks, seeing Laravel helps to recognize the same concept in a more structured system.

## In summary

To send email seriously use SMTP, credentials in environment variables and a library like PHPMailer. Locally capture everything with MailHog; for shared environments use Mailtrap; in production it switches to a real provider. Never test email on real users until the flow has been tested in a secure environment.
