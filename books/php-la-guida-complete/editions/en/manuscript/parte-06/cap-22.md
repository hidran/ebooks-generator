# 22. Login, Registration, Sessions, and CSRF

After the CRUD, the User Management System needs to know **who** is using the application. Up to this point every visitor was identical to every other one: anybody could open the user list, edit a record, delete it. Now we introduce two concepts that sound like the same thing but are not at all, and it pays to keep them separate from the very start.

**Authentication** answers the question *"who are you?"*. It is the moment when the user proves their identity, usually with an email and a password. **Authorization** answers *"what are you allowed to do?"*. It is the check that happens afterwards, every time the user tries to perform an action. They are two distinct steps: an authenticated user is not automatically authorized to do everything, and it is precisely the confusion between the two that produces many security holes.

In this chapter we put together four pieces: **sessions** (to remember who the user is between one request and the next), **password hashes** (so that a readable password is never stored), **CSRF tokens** (to be sure a request really came from our own form) and **roles** (to decide who can do what). The public repository implements them in procedural form, with functions collected under `includes/`: it is deliberately the simplest possible version, the one that lets you see the mechanism without a framework's abstraction on top.

![The UMS login form. The "Remember me" checkbox feeds the persistent-token mechanism covered in Chapter 24.](figures/cap-22/login-form.png)

## Session Cookie

First, a refresher on what a session actually is, because it is the piece everything else rests on. HTTP is a **stateless** protocol: every request reaches the server with no memory of the ones before it. If the user logs in and then clicks a link, the second request by itself knows nothing about the first. Sessions solve this in two moves: PHP creates a container of data on the **server**, identified by a random ID, and sends the **browser** a cookie containing only that ID. The email, the role, everything we need stays in the server-side data; only the identifier travels in the cookie. That distinction matters: whoever steals the cookie does not read your data, but they can **impersonate** the user, which is worse.

This is why `includes/session.php` configures the cookie *before* calling `session_start()`:

```php
<?php

declare(strict_types=1);
$secure = !empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off';
session_set_cookie_params([
    'path' => '/',
    'domain' => '',
    'secure' => $secure,
    'httponly' => true,
    'samesite' => 'Lax'
]);
ini_set('session.use_strict_mode', 1);
session_name('ums_sid');
session_start();
```

Full source: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-22/en/parte-06/cap-22/listing-01.php)

Real source: [`includes/session.php` at `0fa560f`](https://github.com/hidran/php-user-management-system/blob/0fa560f/includes/session.php).

The order is not a detail: `session_set_cookie_params()` has to be called before `session_start()`, because it is the latter that emits the cookie. Swapping them means configuring something that has already been sent.

Let's go through the options one at a time, because each closes a specific door:

- **`httponly => true`** stops JavaScript from reading the cookie through `document.cookie`. If an XSS vulnerability ever slips through on a page, the attacker can still inject scripts, but cannot exfiltrate the session ID and comfortably reuse it elsewhere. It is a safety net, not a licence to be sloppy with escaping.
- **`secure => $secure`** tells the browser to send the cookie only over HTTPS. Locally we often work over plain HTTP, so the value is computed dynamically: in production, where the certificate is in place, it becomes `true` on its own. Without this flag a session cookie can travel in clear text over a public Wi-Fi network.
- **`samesite => 'Lax'`** restricts sending the cookie when the request originates from **another site**. It is the first line of defence against the CSRF we discuss in a moment: with `Lax` the cookie travels on ordinary navigation (the user clicks a link and lands on our site) but not on cross-site POST requests. It does not replace the CSRF token — old browsers ignore it and some configurations work around it — but it raises the bar considerably.
- **`session.use_strict_mode = 1`** is the most obscure of the four and deserves a proper explanation. By default PHP accepts whatever session ID the browser hands it: if I send a cookie with the ID `abc123` and that ID does not exist, PHP *creates* it. An attacker can therefore pick the ID themselves, get the victim to use it (a link such as `?PHPSESSID=abc123` is enough on permissive configurations) and then show up with that same ID once the victim has logged in. This is called **session fixation**. With `use_strict_mode` enabled, PHP rejects IDs it did not generate and issues a fresh one.
- **`session_name('ums_sid')`** renames the cookie, which is called `PHPSESSID` by default. It is not real security — anyone looking at the response can tell it is a session ID — but it avoids announcing "PHP runs here" to automated scanners, and on shared hosting it keeps the sessions of different applications apart.

None of these lines makes the login *work*: the login would behave identically without them. They make the difference between a system that survives a trivial attack and one that does not.

## CSRF Token

This is the point where it pays to stop and understand **the attack**, because the defensive code is three lines long and without the context it looks like a magic formula to copy.

**CSRF** stands for *Cross-Site Request Forgery*. Picture this scenario. You are logged into our UMS: the session cookie is in your browser and it is valid. In another tab you open some other site — a forum, a page that arrived by email. That page contains, hidden away, a form like this:

```html
<form action="https://ums.example.com/controller/updateRecord.php" method="POST">
    <input type="hidden" name="action" value="delete">
    <input type="hidden" name="id" value="1">
</form>
<script>document.forms[0].submit();</script>
```

The browser sends the request to our server **and attaches the session cookie**, because cookies are sent based on the destination domain, not based on who originated the request. From the server's point of view it is a perfectly valid POST, from an authenticated user, with the right permissions. The record is deleted. The user never knowingly clicked anything.

Note the key point: the attacker **does not need to read** the cookie, nor to know anything about the session. All they need is for the request to leave the victim's browser. That is why `httponly` does not protect against CSRF, and why a different mechanism is required.

The defence is called the **synchronizer token pattern** and it rests on a simple asymmetry: the victim's browser sends cookies automatically, but it does **not** know the contents of our pages. If every form carries a secret value that only someone who genuinely loaded the page can know, the attacker cannot reproduce it from the outside.

```php
<?php

function csrf_token(): string
{
    return $_SESSION['csrf_token'] ??= bin2hex(random_bytes(32));
}

function csrf_field(): string
{
    return '<input type="hidden" name="csrf_token" value="' . csrf_token() . '">' . "\n";
}

function csrf_validate(string $token): bool
{
    return hash_equals($token, csrf_token());
}
```

Full source: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-22/en/parte-06/cap-22/listing-02.php)

Real source: [`includes/csrf.php` at `bfc58e7`](https://github.com/hidran/php-user-management-system/blob/bfc58e7/includes/csrf.php).

Three functions, three details worth your attention.

**`random_bytes(32)`** generates 32 **cryptographically secure** bytes, meaning unpredictable even to someone who knows the values generated earlier. This is different from `rand()` or `mt_rand()`, which are fast but predictable: given enough output you can reconstruct the generator's state and predict what comes next. For a security token that is fatal, so the rule is blunt: for any secret value — CSRF tokens, password-reset tokens, session identifiers — use `random_bytes()` (or `random_int()` for numbers), never `rand()`. `bin2hex()` then turns the bytes into 64 hexadecimal characters, suitable for dropping into an HTML attribute.

**The `??=` operator** (null coalescing assignment, PHP 7.4, which we saw in Chapter 8) makes sure the token is generated **once per session**: if `$_SESSION['csrf_token']` already exists, that one is returned. This means every form in the session shares the same token. It is a deliberate trade-off: a different token per form would be more robust, but it breaks as soon as the user opens two tabs or presses the back button, because the old page's token is no longer the valid one. For an application like this, one token per session is the right balance between security and usability.

**`hash_equals()`** instead of `===` is the detail almost everyone skips. A normal string comparison stops at the first differing character: comparing `"aaaa"` with `"baaa"` is faster than comparing `"aaaa"` with `"aaab"`, because in the second case the comparison has to run all the way to the end. The difference is nanoseconds, but it is **measurable**, and by repeating the measurement thousands of times an attacker can guess the token one character at a time instead of having to hit the whole thing at once. This is a **timing attack**. `hash_equals()` compares the two strings in a time that does not depend on how many leading characters match, and shuts that door. The practical rule: whenever you compare a secret — a token, a hash, a signature — use `hash_equals()`, not `==` or `===`.

A note on the signature: the PHP manual defines `hash_equals(string $known_string, string $user_string)`, with the known value first. Here the arguments are swapped relative to that convention; the comparison is still constant-time, but it is worth getting used to the documented order, because it makes the code easier for a reviewer to read.

The rest is discipline, and it is the part no function can do for you: **every form that changes something must print `csrf_field()`, and every controller receiving that POST must call `csrf_validate()` before touching the database**. A single forgotten endpoint undoes the work done on all the others.

## Starting the User Session

When the credentials check out, the project does not simply write the data into the session:

```php
function start_session(array $user): void
{
    session_regenerate_id(true);
    $_SESSION['user_data'] = $user;
    $_SESSION['user_logged_in'] = true;
}
```

Full source: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-22/en/parte-06/cap-22/listing-03.php)

Real source: [`includes/auth.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

`session_regenerate_id(true)` is the second defence against the **session fixation** we mentioned earlier, and it works from a different angle than `use_strict_mode`. The reasoning goes like this: even granting that an attacker managed to make the victim use a session ID they know, that ID **is thrown away at the exact moment the login succeeds**. The authenticated user continues with a brand-new ID that the attacker has never seen. The login is the moment when the session changes in value — before it was an anonymous session, now it is a privileged one — and that is precisely where the identifier must be renewed.

The `true` argument tells PHP to **delete** the old session file rather than leave it lying around. Without it, the old ID would stay valid on the server: the attacker could keep using it and we would be back where we started. It is a parameter that is easy to forget and that makes the whole line nearly pointless when omitted.

## Verifying the Login

`verify_login()` lines the checks up, and the order tells a deliberate story:

```php
function verify_login(mysqli $conn, string $email, string $password, string $token): array
{
    $res = ['success' => true, 'message' => ''];
    if (!csrf_validate($token)) {
        $res['success'] = false;
        $res['message'] = 'Invalid token';
        return $res;
    }
    if (!validatePassword($password) || !verifyEmail($email)) {
        $res['success'] = false;
        $res['message'] = 'Invalid email or password';
        return $res;
    }
    $user = find_user_by_email($conn, $email);
```

Full source: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-22/en/parte-06/cap-22/listing-04.php)

Real source: [`includes/auth.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

First the CSRF token, then the shape of the data, and only at the end the database. This is the **fail fast** principle: the checks that cost nothing come first, so a malformed or forged request is rejected without ever having opened a connection or queried a table. Every error branch returns immediately — there are no nested `else` blocks, and you never fall through to the following code by accident.

Look at the message in the second block too: `'Invalid email or password'`, without saying which of the two is wrong. That is not laziness. If the system replied "this email does not exist", an attacker could try thousands of addresses and build a list of registered users — this is called **user enumeration**, and it is the first step towards a targeted attack. Always answering the same way, whether the email does not exist or the password is wrong, gives nothing away for free.

The password comparison is the most important piece in the chapter:

```php
if (!$user || !password_verify($password, $user['password'])) {
    $res['success'] = false;
    $res['message'] = 'Wrong password or user doesn´t exist';
    return $res;
}
if (password_needs_rehash($user['password'], PASSWORD_DEFAULT)) {
    update_password_hash($conn, $user['id'], password_hash($password, PASSWORD_DEFAULT));
}
```

Full source: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-22/en/parte-06/cap-22/listing-05.php)

Real source: [`includes/auth.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

There is **no password** in the database. What is there is the output of `password_hash()`, a one-way function: from the password you get the hash, from the hash you cannot get back. When the user logs in we are not comparing two passwords; we hand `password_verify()` the password just typed and the stored hash, and let it tell us whether they correspond.

Why not a simple `md5($password)`, the way so much PHP code did fifteen years ago? For two reasons. The first is that MD5 and SHA-1 are **fast**, and for password hashing speed is a defect: a modern GPU tries billions of combinations per second, so a stolen database turns into a list of plaintext passwords within hours. `password_hash()` uses bcrypt (or Argon2), algorithms designed to be **slow**, with a configurable cost that can be raised as hardware improves. The second reason is the **salt**: `password_hash()` automatically generates a different random value for each user and embeds it in the resulting hash. Two users with the same password end up with different hashes, and rainbow tables — precomputed tables of common hashes — become useless. You do not have to manage the salt yourself: it is already inside the string you store, together with the algorithm and the cost, which is why the `password` column is 255 characters wide and not 32.

`password_needs_rehash()` is the forward-looking part. Algorithms age: in a few years `PASSWORD_DEFAULT` will point at something stronger, or you will want to raise bcrypt's cost. But the hashes already in the database are still the old ones, and you cannot recompute them because you do not know the passwords. The only moment the password passes in front of you in clear text is the login: so, if the stored hash no longer matches the current parameters, it is recomputed on the fly and updated. The result is that the database upgrades itself, one user at a time, without asking anybody to change their password. Three lines that save you a painful migration five years from now.

## Registration

`verify_signup()` follows the same structure, with the added problem of duplicates:

```php
function verify_signup(mysqli $conn, string $email, string $password, $username, string $token): array
{
    $res = ['success' => true, 'message' => ''];
    if (!csrf_validate($token)) {
        $res['success'] = false;
        $res['message'] = 'Invalid token';
        return $res;
    }
    if (!validateUserName($username)) {
        $res['success'] = false;
        $res['message'] = 'Invalid user name';
        return $res;
    }
```

Full source: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-22/en/parte-06/cap-22/listing-06.php)

Real source: [`includes/auth.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

Here too: token, then format, then database. The function goes on to check that the email is not already registered and that the password meets the minimum requirements defined in `config.php`.

Two observations that hold well beyond this project. The first: the "does a user with this email already exist?" check done in PHP **is not enough on its own**. Between the moment you query the table and the moment you write the row there is an instant, and two simultaneous registrations with the same email can both pass the check. This is a **race condition**, and the only real defence is a `UNIQUE` constraint on the column at the database level — which is indeed present in the `users` table schema. The PHP check exists to produce a friendly error message; the constraint exists to guarantee integrity.

The second: when validation passes, `controller/signup.php` saves the user with the `user` role, **always**. The role never comes from the form. It sounds obvious put that way, but it is exactly the kind of detail that slips: if the role field were a `<select>` submitted by the client, anyone could register as `admin` by editing the HTML with the browser's developer tools. **Everything that decides privileges is settled on the server.**

![The signup form, served from the same page through tabs. Both forms include the hidden CSRF token field.](figures/cap-22/signup-form.png)

## Roles

With authentication in place, we move on to authorization. `includes/acl.php` (from *Access Control List*) holds the roles together with the functions that query them:

```php
<?php

declare(strict_types=1);

const ROLE_USER = 'user';
const ROLE_ADMIN = 'admin';
const ROLE_EDITOR = 'editor';

function get_user_login_data(): array
{
    return $_SESSION['user_data'] ?? [];
}

function get_user_role(): string
{
    return get_user_login_data()['role_type'] ?? 'user';
}

function user_can_update(): bool
{
    return in_array(get_user_role(), [ROLE_ADMIN, ROLE_EDITOR]);
}

function user_can_delete(): bool
{
    return get_user_role() === ROLE_ADMIN;
}
```

Full source: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-22/en/parte-06/cap-22/listing-07.php)

Real source: [`includes/acl.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/acl.php).

The roles are **constants**, not strings scattered through the code: if you type `'admin'` by hand in ten places, the day you mistype one of them the check fails silently and the user simply cannot do something any more. With `ROLE_ADMIN`, a typo becomes a PHP error, which is far easier to find.

Note the default value in `get_user_role()`: if there is nothing in the session, the function returns `'user'`, the **least privileged** role. This is an application of the *fail closed* (or *fail secure*) principle: when something is unclear, the system must deny rather than grant. The opposite — returning `'admin'` when in doubt, or worse an empty string that then slips through a loose comparison — is the kind of choice that turns a trivial bug into an incident.

These functions return a boolean and serve two different purposes, and you need **both**. In the view they decide whether to show a button:

```php
<?php if (user_can_delete()): ?>
    <a class="btn btn-danger" href="...">DELETE</a>
<?php endif; ?>
```

In the controller they decide whether the action may be carried out. And here is the point never to forget: **hiding a button is not security**. A hidden button does not stop anybody from opening the developer tools, reading the action's URL and calling it by hand. The check in the view serves the user experience — don't show users things they cannot do; the check in the controller serves security. If you have to skip one, skip the one in the view. In the next chapter we look at exactly how the project applies these checks to controllers and routes.

## In summary

A login system rests on five pieces working together, and each closes a different door. The **session cookie**, configured with `httponly`, `secure`, `SameSite` and `use_strict_mode`, protects the identifier from theft and from fixation. **Regenerating the ID** at login throws away any session the user might have received from an attacker. The **CSRF token**, compared with `hash_equals()`, guarantees that a POST really came from our form and not from a hostile site. **Password hashes** built with `password_hash()`, `password_verify()` and `password_needs_rehash()` ensure that a stolen database does not turn into a list of credentials. **Roles**, checked on the server and not only in the view, decide who can do what.

None of these pieces is optional, and none compensates for the absence of another: they are defence in depth, designed so that a single mistake does not become a compromise. The UMS repository shows them in procedural form, with global functions and state in `$_SESSION`, and that is the best way to see the mechanism laid bare. In Part IX the same concepts come back as injected services, middleware and container-managed sessions: the packaging changes, not the substance of what we have just seen.
