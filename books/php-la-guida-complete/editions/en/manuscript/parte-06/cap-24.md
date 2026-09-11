# 24. Remember Me

Remember me lets the user be recognized even after the PHP session expires: it is the "remember me" box you tick at login that finds you still logged in the next day, without re-entering your credentials. It sounds like a trivial convenience, and it is instead one of the trickiest mechanisms to get right, because it moves a piece of authentication **out of the session**, into a cookie that lives for weeks on the user's device.

Let's start with how **not** to do it, because it is the mistake almost everyone makes the first time. The temptation is to store the user's email and password in the cookie, or their id, and read them back on the next visit. It is a disaster: a cookie is stored in clear text on disk, travels on every request, and is exactly the kind of data an XSS attack or a shared computer exposes. Storing the password in a cookie means giving it away. Storing the id means anyone who writes `user_id=1` in their own browser becomes the administrator. You need something completely different: not a stored identity, but a **proof protocol**. It is the **selector/validator** pattern, and it is what the `php-user-management-system` repository implements in commit `8769ecc` — selector, token, hash, `HttpOnly` cookie, auto-login, rotation, and revocation. Let's go through it piece by piece.

## Token Table

The persistent token must not be stored in clear text. The database keeps a public selector and the hash of the secret token:

```sql
create table remember_tokens
(
    id         bigint unsigned auto_increment
        primary key,
    user_id    bigint unsigned                    not null,
    token_hash char(64)                           not null,
    expires_at datetime                           not null,
    created_at datetime default CURRENT_TIMESTAMP not null,
    user_agent varchar(255)                       null,
    ip_address varbinary(16)                      not null,
    selector   char(18)                           not null,
    constraint uk_selector_remember_me
        unique (selector),
    constraint remember_tokens_users_id_fk
        foreign key (user_id) references users (id)
            on delete cascade
);
```

Full source: [listing-01.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-24/en/parte-06/cap-24/listing-01.sql)

Real source: [`data/remember_tokens.sql` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/data/remember_tokens.sql).

The table already tells the whole protocol, if you know how to read it. There are two separate values: the **selector**, with a `unique` constraint, and the **token_hash**. The cookie that ends up in the browser will contain `selector:token` — two pieces joined by a colon. The selector serves to **find the row** quickly (it is indexed, unique), the token serves to **prove** that the browser possesses the secret. Why two values instead of one? Because they separate two conflicting needs: searching the database quickly wants an indexed value, but searching by an indexed *secret* would open a path to certain timing attacks on the index. With the pair, the lookup happens on the public selector and the security comparison on the token.

The crucial detail is that the database stores `token_hash`, **not the token**. Exactly as with the passwords in Chapter 22, the real secret is never kept in clear: its SHA-256 fingerprint is stored. So if an attacker steals the whole `remember_tokens` table, they do not get spendable tokens — they get their hashes, from which they cannot recover the original tokens. Stealing the database is not enough to impersonate anyone. Note also `on delete cascade` on the constraint: when a user is deleted, their tokens disappear automatically, with no code to remember to write. And the `user_agent`, `ip_address`, `expires_at` fields serve for traceability and expiry: a token is not valid forever.

## Creating the Cookie

`saveRememberMe()` generates a selector and a token with `random_bytes()`, stores the SHA-256 hash, and sends the cookie:

```php
function saveRememberMe(mysqli $conn, int $userId): bool
{
    $selector = base64url_encode(random_bytes(12));
    $token = base64url_encode(random_bytes(33));
    $tokenHash = hash('sha256', $token);
    $ttl = getConfig('rememberMeTTL');
    $expiresAt = (new DateTimeImmutable('+' . $ttl . ' seconds'))->format('Y-m-d H:i:s');
    $ip = $_SERVER['REMOTE_ADDR'];
    $userAgent = mb_substr($_SERVER['HTTP_USER_AGENT'], 0, 255);
    $sql = 'INSERT INTO remember_tokens (user_id, token_hash, selector, expires_at, ip_address, user_agent) VALUES (?,?,?,?,?,?)';
```

Full source: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-24/en/parte-06/cap-24/listing-02.php)

Real source: [`includes/auth.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

Selector and token are both born from `random_bytes()`, the same cryptographically secure function as the CSRF token in Chapter 22 — because here too, predicting the value means being able to forge it. Look at what goes into the database and what does not: `$tokenHash`, the fingerprint, is inserted, **not** `$token`. The plaintext token, the one actually needed for auto-login, exists only for an instant inside this function, long enough to put it in the cookie; then PHP forgets it and only the hash remains in the database. It is the same asymmetry as passwords: the system keeps enough to **verify** a secret, never enough to **reconstruct** it.

The final part sends the full value to the browser:

```php
$value = $selector . ':' . $token;
$cookieName = getConfig('rememberMeCookieName');

$cookieOptions = getRememberCookieOpts();
setcookie($cookieName, $value, $cookieOptions);

return $res;
```

Full source: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-24/en/parte-06/cap-24/listing-03.php)

Real source: [`includes/auth.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

Into the cookie goes `selector:token`: the selector the database knows, and the plaintext token of which the database has only the hash. It is the only moment the token travels in clear text, and it is unavoidable — the browser has to receive it somehow in order to return it later. From here on the whole game is protecting this cookie, and that is what the options in the next section do.

## Cookie Options

The cookie is `HttpOnly`, `SameSite=Strict`, and lasts as long as the configured TTL:

```php
function getRememberCookieOpts(): array
{
    $ttl = getConfig('rememberMeTTL');
    $secure = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off');

    return [

        'expires' => time() + $ttl,
        'path' => '/',
        'domain' => '',
        'secure' => $secure,
        'httponly' => true,
        'samesite' => 'Strict'
    ];
}
```

Full source: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-24/en/parte-06/cap-24/listing-04.php)

Real source: [`includes/auth.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

These are the same defences we saw on the session cookie in Chapter 22, and here they matter even more, because this cookie lives for weeks instead of for the lifetime of a browser tab. `httponly => true` makes it invisible to JavaScript, so an XSS attack cannot read it and exfiltrate it — crucial for a long-lived cookie. `secure` confines it to HTTPS in production, where the value becomes `true` on its own. And here `samesite => 'Strict'`, more restrictive than the session's `'Lax'`: the remember-me cookie is **never** sent on requests originating from other sites, not even on ordinary navigation. It makes sense — it is a cookie needed only for auto-login on entering our own site, there is no reason for it to travel in any other context, and closing that door entirely is free. The longer a cookie lives, the tighter its configuration must be.

## Auto-Login

`tryAutoLogin()` is called in `index.php` before the `is_user_logged_in()` check:

```php
function tryAutoLogin(): void
{
    if (!empty($_SESSION['user_logged_in'])) {
        return;
    }
    $cookieName = getConfig('rememberMeCookieName');

    $cookie = $_COOKIE[$cookieName] ?? '';

    if (!$cookie || !str_contains($cookie, ':')) {
        return;
    }
    [$selector, $token] = explode(':', $cookie);
```

Full source: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-24/en/parte-06/cap-24/listing-05.php)

Real source: [`includes/auth.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

Here is the protocol in action, running in reverse from creation. The function starts with a *fail fast*: if a session is already active, there is nothing to do, it exits at once. Otherwise it reads the cookie and splits it on the colon into its two parts, `$selector` and `$token`. The selector will find the row, the token will prove possession of it.

The query joins token and user, so auto-login fails if the user no longer exists:

```php
$conn = getConnection();
$st = $conn->prepare(
    'SELECT  t.id,t.expires_at,t.token_hash, u.id as uid, u.email, u.username, u.role_type FROM remember_tokens as t INNER JOIN users as u ON t.user_id=u.id WHERE selector=?'
);
$st->bind_param('s', $selector);
$res = $st->execute();
```

Full source: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-24/en/parte-06/cap-24/listing-06.php)

Real source: [`includes/auth.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

The lookup happens **on the selector**, not on the token — this is exactly why the protocol uses two values. The selector is indexed and unique, so the database finds the row directly and efficiently. And of course it is a prepared statement with the selector bound as a parameter: we are in Part VI, the SQL rule applies here too. The `JOIN` with the `users` table does something clever in one shot: it retrieves the user's data and, if that user has meanwhile been deleted, returns no row — auto-login fails by itself, with no extra checks.

The comparison uses the hash of the received token:

```php
$calcHash = hash('sha256', $token);
if (!hash_equals($row['token_hash'], $calcHash)) {
    deleteRememberTokenById($row['id']);
    clearRememberMe();
    return;
}
```

Full source: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-24/en/parte-06/cap-24/listing-07.php)

Real source: [`includes/auth.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

Having found the row via the selector, the token is verified: you compute the SHA-256 hash of the token received from the cookie and compare it with the one stored in the database. The comparison goes through `hash_equals()`, the constant-time function from Chapter 22, for the same reason — to prevent a timing attack on the secret comparison. If the hashes do not match, something is wrong: the token is expired, tampered with, or a guessing attempt. The reaction is drastic and correct: the row is **deleted** (`deleteRememberTokenById`) and the cookie is cleared. A suspicious token is not merely rejected, it is destroyed — better to force the legitimate user into a fresh login than to leave a token lying around that someone is working on.

## Rotation

After a successful auto-login, the token is rotated:

```php
function rotateRememberToken(mysqli $conn, int $id): void
{
    $token = base64url_encode(random_bytes(33));
    $tokenHash = hash('sha256', $token);
    $ttl = getConfig('rememberMeTTL');
    $expiresAt = (new DateTimeImmutable('+' . $ttl . ' seconds'))->format('Y-m-d H:i:s');
    $sql = 'SELECT selector FROM remember_tokens WHERE id=?';
```

Full source: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-24/en/parte-06/cap-24/listing-08.php)

Real source: [`includes/auth.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

This is the part that lifts the mechanism from "working" to "robust", and it is the one tutorials almost always skip. After every successful auto-login, the used token is **thrown away and replaced** with a new one: new `random_bytes()`, new hash, new expiry. Why? Because it drastically shrinks the useful window of a stolen token. Imagine an attacker manages to copy the remember-me cookie. Without rotation, that cookie is valid for weeks, for the whole TTL. With rotation, as soon as the legitimate owner returns to the site and auto-logs in, the token changes — and the attacker's copy becomes waste paper. Better still: if it is the attacker who uses the stolen token first, it will be the *legitimate* owner who finds themselves with an invalid token, a signal that something is wrong. Rotation turns a persistent token from a permanent key into a use-and-renew one.

## Revocation on Logout

Logout clears the cookie, revokes either the current device token or all user tokens, and finally destroys the session:

```php
clearRememberMe();
if ($fromAll) {
    revokeAllRememberMeTokens(get_user_id());
} else {
    revokeDeviceRememberMeToken(get_user_id());
}
$_SESSION = [];
$p = session_get_cookie_params();
setcookie(session_name(), '', time() - 4200, $p['path'], $p['domain'], $p['secure'], $p['httponly']);
session_destroy();

redirect('/login.php');
```

Mind the order here, because these are three distinct operations and you need all three. `$_SESSION = []` empties the in-memory array for the current request, but on its own it deletes nothing on the server. The `setcookie()` call with an expiry in the past tells the browser to throw the session cookie away: without it, the browser keeps sending a session ID that should no longer exist. And `session_destroy()` removes the session data on the server. Stopping at `$_SESSION = []` is the classic mistake: the user looks logged out, but the session file is still on the server and the cookie is still in the browser, so that ID is still spendable.

Full source: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-24/en/parte-06/cap-24/listing-09.php)

Real source: [`controller/logout.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/controller/logout.php).

There is a product detail, as well as a security one, in that `if ($fromAll)`. The normal logout revokes only the **current device's** token: if you are logged in on the laptop and the phone, logging out on the laptop does not throw you off the phone. But the `fromAll` option revokes **all** of the user's tokens in one shot — it is the classic "log out all devices" you offer when someone fears their account is compromised. Being able to do this is possible only because each token is a separate row in the database, linked to the user: revoking them all is a `DELETE WHERE user_id=?`. That is why the revocation is so explicit:

```php
function revokeAllRememberMeTokens(int $userId): void
{
    $conn = getConnection();
    $st = $conn->prepare('DELETE FROM remember_tokens WHERE user_id=?');
    $st->bind_param('i', $userId);
    $st->execute();
    $st->close();
}
```

Full source: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-24/en/parte-06/cap-24/listing-10.php)

Real source: [`includes/auth.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

A `DELETE` with the `user_id` bound as a parameter, and all of the user's tokens disappear. Revocation is possible because the state lives in the **database**, not only in the cookie: being able to delete the row, you can invalidate an access whenever you want. It is the substantial difference from storing credentials in the cookie, where you would have no way to "recall" a token already handed out.

## In summary

Remember me is not a password saved in a cookie — it is a **protocol**, and now you know why each of its pieces exists. The **public selector** finds the row quickly; the **secret token** proves possession; the **hash in the database** ensures that a theft of the table produces no spendable tokens; the **expiry** limits the duration; the **`HttpOnly`, `Secure`, `SameSite=Strict` cookie** protects the secret in transit and at rest; the **auto-login** verifies with `hash_equals()`; the **rotation** shortens the life of a stolen token; the **revocation** — of one device or all — is possible because the state lives in the database. The UMS repository shows the whole cycle in procedural code: in Part IX the same principles reappear in a dedicated service, but the protocol is exactly this. If you have understood why two values are needed instead of one, and why the hash is stored and not the token, you have understood the hard part.
