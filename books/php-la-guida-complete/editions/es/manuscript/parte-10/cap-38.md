# 38. Envía correos electrónicos con PHPMailer, MailHog y Mailtrap

Muchas aplicaciones necesitan enviar correos electrónicos: confirmaciones de registro, restablecimiento de contraseña, notificaciones, recibos. PHP tiene una función `mail()`, pero en proyectos reales es mejor usar SMTP y una biblioteca como PHPMailer.

## ¿Por qué no confiar en `mail()`?

`mail()` depende de la configuración del servidor. A nivel local muchas veces no funciona; en producción puede enviar mensajes sin autenticación moderna, con problemas de entrega.

SMTP es más explícito: host, puerto, nombre de usuario, contraseña, cifrado. PHPMailer maneja estos detalles con una API limpia.

## Instalar PHPMailer

```bash
composer require phpmailer/phpmailer
```

Código completo: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-38/es/parte-10/cap-38/listing-01.sh)


Uso básico:

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
    $mail->addAddress("juan@example.com");

    $mail->Subject = "Bienvenido";
    $mail->Body = "Gracias por registrarte.";

    $mail->send();
} catch (Exception $e) {
    error_log($e->getMessage());
}
```

Código completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-38/es/parte-10/cap-38/listing-02.php)


## MailHog localmente

MailHog es un servidor SMTP simulado para desarrollo. La aplicación envía correos electrónicos a MailHog, MailHog los captura y usted los ve en una interfaz de usuario web. En realidad, no se envían mensajes a usuarios reales.

Configuración típica:

```text
SMTP host: localhost
SMTP port: 1025
Web UI: http://localhost:8025
```

Código completo: [listing-03.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-38/es/parte-10/cap-38/listing-03.txt)


Esto es ideal para probar restablecimientos de contraseñas, plantillas y contenido sin correr el riesgo de envíos accidentales.

## `mhsendmail`

En algunos entornos, puede configurar PHP para que la función `mail()` se envíe a MailHog a través de `mhsendmail`. En `php.ini` estableces la ruta al comando sendmail. Esto es útil si necesita probar código heredado que usa `mail()`.

Para código nuevo, prefiera PHPMailer con SMTP explícito.

## Mailtrap

Mailtrap ofrece bandejas de entrada SMTP de prueba en la nube. Esto es conveniente cuando la aplicación se ejecuta en un entorno donde no se puede acceder a MailHog local.

Las credenciales SMTP no deben escribirse en código:

```php
<?php
$mail->Host = getenv("SMTP_HOST");
$mail->Port = (int) getenv("SMTP_PORT");
$mail->Username = getenv("SMTP_USER");
$mail->Password = getenv("SMTP_PASSWORD");
```

Código completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-38/es/parte-10/cap-38/listing-04.php)


En producción utilizarás un proveedor real, pero la interfaz sigue siendo la misma.

## correos electrónicos HTML

```php
<?php
$mail->isHTML(true);
$mail->Subject = "Reset password";
$mail->Body = "<p>Haz clic en el enlace para restablecer tu contraseña.</p>";
$mail->AltBody = "Haz clic en el enlace para restablecer tu contraseña.";
```

Código completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-38/es/parte-10/cap-38/listing-05.php)


Configure también siempre `AltBody`: algunos clientes o filtros prefieren texto sin formato.

## Laravel y Mailtrap

Laravel tiene un sistema de correo electrónico incorporado. La configuración reside en `.env`:

```text
MAIL_MAILER=smtp
MAIL_HOST=sandbox.smtp.mailtrap.io
MAIL_PORT=2525
MAIL_USERNAME=your_mailtrap_username
MAIL_PASSWORD=your_mailtrap_password
```

Código completo: [listing-06.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-38/es/parte-10/cap-38/listing-06.txt)


Aunque este libro funciona mucho sin frameworks, ver Laravel ayuda a reconocer el mismo concepto en un sistema más estructurado.

## En resumen

Para enviar correo electrónico utilice seriamente SMTP, credenciales en variables de entorno y una biblioteca como PHPMailer. Capture todo localmente con MailHog; para entornos compartidos utilice Mailtrap; en producción cambia a un proveedor real. Nunca pruebe el correo electrónico con usuarios reales hasta que el flujo se haya probado en un entorno seguro.
