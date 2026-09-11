# 23. Protected Navigation and Role-Based Actions

In `php-user-management-system`, login does not use AJAX. Requests are traditional POST forms and redirects. This chapter therefore focuses on what the public code really implements: protected pages, conditional navigation, and actions allowed by role.

The underlying theme is a single one, and you have already met it in the previous chapters: **authorization**. But here we see it from a new angle, that of **defence in depth**. You will see the same permission — "can this user edit? can they delete?" — checked at several different points in the application: when the page is rendered, when the menu is built, when the list buttons are shown, and again inside the controller. At first glance it looks like pointless repetition. It is not, and that is exactly the point this chapter must make clear: **each layer protects a different thing, and none of them alone is enough**.

## Protecting the Main Page

`index.php` first tries auto-login via remember me, then checks the session:

```php
require_once 'includes/acl.php';
require_once 'includes/auth.php';
tryAutoLogin();
if (!is_user_logged_in()) {
    redirect('login.php');
}
require_once 'includes/csrf.php';
```

Full source: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-23/en/parte-06/cap-23/listing-01.php)

Real source: [`index.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/index.php).

The first layer is the outermost: before producing a single line of HTML, the page decides whether the user has the right to be there. The sequence matters. Auto-login is attempted (which we saw in Chapter 24), so a user with a valid remember-me cookie is recognized; then `is_user_logged_in()` is checked and, if there is no session, `redirect()` sends them to the login and the request ends there. The important detail is that this check comes **before rendering**. If the user is not authorized they must not see even the partial page — no header, no empty table, nothing. Putting the check at the top, and not halfway down the page, guarantees that no confidential fragment reaches the browser of someone who has no right to see it.

## Reading the User's Data

The ACL functions read the state from the session:

```php
function is_user_logged_in(): bool
{
    return !empty($_SESSION['user_logged_in']);
}

function get_user_login_data(): array
{
    return $_SESSION['user_data'] ?? [];
}

function get_user_role(): string
{
    return get_user_login_data()['role_type'] ?? 'user';
}
```

Full source: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-23/en/parte-06/cap-23/listing-02.php)

Real source: [`includes/acl.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/acl.php).

There is a principle in these three functions worth more than it seems: the source of the user's identity is **a single one**, the session. The role is read from `$_SESSION['user_data']['role_type']`, never from a `GET` or `POST` parameter. It is essential to understand why. The session lives on the **server** and was populated at login, after the password check: the user cannot modify it. A `GET` or `POST` parameter, by contrast, is written by the client and the user can put whatever they like in it. If even in one place the code decided permissions by looking at `$_GET['role']` instead of the session, anyone could promote themselves to administrator by adding `?role=admin` to the URL. A single source of truth for identity, and that source is under the server's control: it is the foundation on which all the later layers rest. Note also the `'user'` default in `get_user_role()` — if the data is missing, the least privileged role is assumed, the *fail closed* we already discussed in Chapter 22.

## Conditional Menu

The navbar shows the application menu only if the user is logged in:

```php
<?php
if (is_user_logged_in()): ?>
    <ul class="navbar-nav me-auto mb-2 mb-md-0">
        <li class="nav-item">
            <a class="nav-link <?= $indexActive ?>" aria-current="page" href="<?= $indexPage ?>"><i
                        class="fa-solid fa-users"></i>Users</a>
        </li>
```

Full source: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-23/en/parte-06/cap-23/listing-03.php)

Real source: [`view/nav.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/view/nav.php).

The second layer is the menu. Showing the application entries only to logged-in users is **usability**: there is no point offering "Users" or "New user" to a visitor who still has to authenticate. But be careful not to confuse the planes: this is an interface embellishment, **not** a security measure. The menu decides what the user *sees*, not what the user *can do*. A missing link does not stop anyone from typing the corresponding URL by hand. The real security is not here — it is in the controllers, and we get there in two sections.

## Actions in the List

The user list shows update and delete based on role:

```php
<?php
if (user_can_update()): ?>
    <div class="row">

        <div class="col-6">
            <a class="btn btn-success" href="?id=<?= $user['id'] ?>&action=edit&<?= $navParams ?>">
                <i class="fa fa-pen"></i>
                UPDATE
            </a>
        </div>
```

Full source: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-23/en/parte-06/cap-23/listing-04.php)

Real source: [`view/userList.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/view/userList.php).

The third layer is finer than the menu: it decides not whether to show *the application*, but whether to show the individual *actions*. The UPDATE button appears only if `user_can_update()`, and further down in the same view the DELETE button appears only if `user_can_delete()`. A user with the `user` role sees the list but not the action buttons; an `editor` sees UPDATE; only an `admin` also sees DELETE. It is exactly what you observe in the figure from Chapter 20, where the administrator has both buttons next to every row.

And, for the third time, the same warning applies: hiding the button is convenience, not security. Never trust that a button not appearing is enough. The action's URL exists anyway, and it must be protected elsewhere.

## Protected Controller

`controller/updateRecord.php` rejects anyone not logged in or unable to update:

```php
require_once '../includes/acl.php';
if (!is_user_logged_in() || !user_can_update()) {
    redirect('../login.php');
}

require '../model/User.php';
$action = getParam('action');
switch ($action) {
```

Full source: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-23/en/parte-06/cap-23/listing-05.php)

Real source: [`controller/updateRecord.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/controller/updateRecord.php).

Here is the layer that really counts — the one the previous three *cannot* replace. Here, in the controller, on the server, before executing any action, `is_user_logged_in()` and `user_can_update()` are checked again. This is the real security. Now you can see why the layers are not redundant: the check in the menu and the list stops the honest user from *seeing* things that do not concern them, but it is the check in the controller that stops the malicious user from *doing* things they are not entitled to. The first improves the experience, the second protects the data. If I asked you to remove one, you would remove the ones in the views — not this one. It is the rule I repeated in Chapter 20 and repeat here because it is the most common conceptual mistake about authorization: **the hidden button is cosmetics, the check in the controller is security**.

Deletion requires an even stricter check:

```php
case 'delete':
    if (!user_can_delete()) {
        redirect('../login.php');
    }

    $id = (int)getParam('id', 0);
    $user = getUserById($id);
```

Full source: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-23/en/parte-06/cap-23/listing-06.php)

Real source: [`controller/updateRecord.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/controller/updateRecord.php).

Note the gradation of permissions. To enter the controller, `user_can_update()` is enough — which holds for `editor` and `admin`. But the `case 'delete'` adds a **stricter** check, `user_can_delete()`, which holds only for `admin`. It is the principle of **least privilege** applied to the action: an editor can modify, but not destroy. The most dangerous action requires the highest permission, and the specific check sits inside the branch that performs that action, so there is no way to reach deletion with only edit permissions.

## Logout via POST

Logout uses POST and CSRF, not a simple GET link:

```php
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(419);
    exit('Invalid request method');
}
$fromAll = getParam('fromAll');
if (!csrf_validate(post_string('csrf_token'))) {
    http_response_code(419);
    exit('Invalid token');
}
```

Full source: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-23/en/parte-06/cap-23/listing-07.php)

Real source: [`controller/logout.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/controller/logout.php).

Even logout, which seems the most innocent action in the world, has its rules. The project rejects requests that are not POST (`http_response_code(419)`) and validates the CSRF token before proceeding. Why so much caution just to "log out"? Because logout **changes state** — it ends a session — and actions that change state must never be exposed as plain GET links. If logout were an `<a href="logout.php">`, an attacker could put an image `<img src="https://oursite/logout.php">` on a page, and your browser, loading it, would log you out without your knowledge. It is a logout CSRF: annoying rather than damaging, but of the exact same mould as the attack we studied in Chapter 22. The rule is sharp and holds for **every** action that modifies something — login, logout, create, delete: you go through POST, and you validate the CSRF token. GETs are for reading, POSTs for changing.

## In summary

The UMS project does not implement AJAX login: it implements a classic, solid flow, and its most important lesson is **defence in depth**. Identity has a **single source**, the session, never a client parameter. The permission is then checked at several layers, and each has a different job: the check **before rendering** keeps out anyone not logged in; the **conditional menu** and the **action buttons** adapt the interface to what the user can do, but they are usability; the **check in the controller**, on the server, is the only one that really protects the data, with a **stricter** requirement for the most dangerous action. Finally, state-changing actions go through **POST with CSRF**, logout included.

If I had to reduce it all to one sentence: the layers in the views serve the honest user, the check in the controller defends against the malicious one — and since you cannot know in advance which of the two you are dealing with, you keep them all. In Part IX this logic scattered across functions and views will become an authorization middleware, a single point crossed by every request; but the principle of defence in depth will remain exactly this.
