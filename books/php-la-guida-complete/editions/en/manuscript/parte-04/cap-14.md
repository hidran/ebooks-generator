# 14. Cookies

Cookies are small pieces of data that the server asks the browser to store. With each subsequent request to the same domain, the browser sends them back to the server. In PHP you will use them for preferences, consent, technical tracking and, very carefully, for mechanisms such as "remember me".

## Set a cookie

To send a cookie use `setcookie()`:

```php
<?php
setcookie("theme", "dark");
```

Full source: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-14/en/parte-04/cap-14/listing-01.php)


The cookie does not immediately appear in `$_COOKIE` in the same request. It is sent in the response headers, saved by the browser and will be available from the next request.

To set a deadline:

```php
<?php
setcookie("theme", "dark", time() + 60 * 60 * 24 * 30);
```

Full source: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-14/en/parte-04/cap-14/listing-02.php)


Here the cookie lasts thirty days. Without expiration, the cookie is session and the browser can delete it when closed.

## Read a cookie

The cookies received are in `$_COOKIE`:

```php
<?php
$theme = $_COOKIE["theme"] ?? "light";
```

Full source: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-14/en/parte-04/cap-14/listing-03.php)


As always with external data, don't trust the value. The browser is controlled by the user: a cookie can be modified, deleted or invented.

## Modern options

The more readable form of `setcookie()` uses an array of options:

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

Full source: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-14/en/parte-04/cap-14/listing-04.php)


The most important options are:

- `expires`: cookie expiry;
- `path`: path for which the cookie is valid;
- `secure`: sending only over HTTPS;
- `httponly`: not accessible from JavaScript;
- `samesite`: reduces some risks related to cross-site requests.

During local development you may not use HTTPS. In that case `secure => true` prevents the browser from saving the cookie. In production, however, sensitive cookies must only travel over HTTPS.

## Delete a cookie

To delete a cookie, rewrite it with expiration in the past:

```php
<?php
setcookie("theme", "", time() - 3600, "/");
```

Full source: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-14/en/parte-04/cap-14/listing-05.php)


The `path` must match the one used when the cookie was created. If it does not match, the browser may store an apparently identical cookie but associated with a different path.

## Headers already sent

`setcookie()` send HTTP header. Headers must start before the response body. This code may generate error:

```php
<?php
echo "Hello";
setcookie("theme", "dark");
```

Full source: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-14/en/parte-04/cap-14/listing-06.php)


The typical message is "headers already sent". The correct solution is to organize the code so that cookies, redirects and sessions are handled before printing HTML.

In development you may also encounter output buffering:

```php
<?php
ob_start();

echo "Hello";
setcookie("theme", "dark");

ob_end_flush();
```

Full source: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-14/en/parte-04/cap-14/listing-07.php)


Output buffering can help in specific cases, but it should not become an excuse to mix logic and presentation out of order.

## Cookies and sessions

PHP sessions normally use a cookie with the session identifier. The real data remains on the server; in the browser there is only one key. This is the key difference:

- cookie: the value is in the browser;
- session: the value is on the server, the browser retains the identifier.

For sensitive data, prefer session. For non-sensitive preferences, a cookie may be sufficient.

## Cookies and security

Do not save passwords, roles or confidential data in clear text in a cookie. Even if you set `httponly`, the user can see and edit the cookie from the browser or developer tools.

For safe "remember me" we will not save the user ID alone. We will use a random token, save it to the database in a controlled form, and rotate it after use.

## In summary

Cookies are simple to use, but easy to misuse. Set them before output, always read them with default values, delete them by replicating path and domain, and use modern options like `httponly`, `secure` and `samesite`. In the project chapters we will use them to build a persistent login without blindly trusting the browser.
