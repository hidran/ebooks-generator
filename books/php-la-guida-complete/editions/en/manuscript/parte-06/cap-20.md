# 20. CRUD, Search, Sorting, and Pagination

In `php-user-management-system`, the user list grows progressively: first it shows all the records, then it adds sorting, search, pagination, and finally create, update, and delete actions. This is the chapter where a *script* becomes an **application**: no longer a page that prints a table, but a set of functions that read parameters from the request, use them to build queries, and return different views depending on what the user asks for.

Precisely because it is the first piece that takes input from the outside and turns it into SQL, it is also the chapter where the first serious risks lurk. We will face them honestly: I show the project's code as it is — procedural, direct, meant to let you see the mechanism — and at the points where it takes a shortcut that is not acceptable in production, I stop to explain why and how to fix it.

![The UMS user list: sortable column headers, search filter, records-per-page selector and pagination bar. Here the 47 sample users are spread over 5 pages.](figures/cap-20/user-list-pagination.png)

## Reading Users with Parameters

The `getUsers()` function receives the page parameters and builds the query:

```php
function getUsers(array $params = []): array
{
    $conn = getConnection();

    $records = [];

    $limit = $params['recordsPerPage'] ?? 10;
    $orderBy = $params['orderBy'] ?? 'id';
    $orderDir = $params['orderDir'] ?? 'DESC';
    $search = $params['search'] ?? '';
    $page = $params['page'] ?? 1;
    $start = $limit * ($page - 1);
    $sql = 'SELECT * FROM users';
```

Full source: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-20/en/parte-06/cap-20/listing-01.php)

Real source: [`functions.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/functions.php).

Five parameters, and each one comes from the **request**: `recordsPerPage` and `page` decide how many records to read and from which point, `orderBy` and `orderDir` the column and the direction of the sort, `search` the text to look for. The `??` operator supplies a default for each, so the function works even on the first visit, when the URL does not yet carry any parameter. So far so good.

The problem is what happens to these values immediately afterwards. In the repository the query is completed like this — and here I have to show you the real code, because it is exactly the point I want you to think about:

```php
$sql .= " ORDER BY $orderBy $orderDir  LIMIT  $start,$limit ";
```

Those four values — `$orderBy`, `$orderDir`, `$start`, `$limit` — end up **inside the SQL string by direct interpolation**. And if `search` has a value, it too is interpolated into the `WHERE`. Every time a piece of data that comes from the user enters a query by being concatenated as text, an alarm should go off in your head: this is the entry point for **SQL injection**, the most classic and most widespread vulnerability in web applications.

Let's make it concrete. Imagine `search` is taken from the URL and pasted into `WHERE username LIKE '%$search%'`. A normal user searches for `mario` and the query becomes `... LIKE '%mario%'`. But an attacker does not type `mario`: they type `x' OR '1'='1`. The resulting query no longer looks for a name, it contains a **logical condition injected** from outside that the database executes as if you had written it. With more elaborate payloads you get to read other tables, extract the password hashes, in some cases modify or delete data. This is not theory: it is the first attack anybody tries against a search form.

"But I filter the input," you might think. In the project, before reaching here, `search` goes through `strip_tags(trim($search))`. Careful: `strip_tags()` removes **HTML tags**, it has nothing to do with SQL. A single quote `'` — the character injection needs — passes through untouched. Filtering for one context (HTML) does not protect against another (SQL): each context has its own *escaping* rules, and mixing them gives a false sense of security. This, incidentally, is the reason the twin function `getTotalUserCount()` we will see shortly at least calls `real_escape_string()` on the search term, while `getUsers()` does not even do that: two functions born together, with two different levels of protection. It is exactly the kind of inconsistency a *prepared statement* removes at the root.

So let's look at the correct version. The search term must be **bound as a parameter**, not concatenated:

```php
function getUsers(array $params, array $allowedColumns): array
{
    $conn = getConnection();
    $limit   = (int) ($params['recordsPerPage'] ?? 10);
    $page    = max(1, (int) ($params['page'] ?? 1));
    $start   = $limit * ($page - 1);
    $search  = (string) ($params['search'] ?? '');

    // orderBy is an IDENTIFIER, not a value: it must be whitelisted
    $want    = $params['orderBy'] ?? 'id';
    $orderBy = in_array($want, $allowedColumns, true) ? $want : 'id';
    $orderDir = ($params['orderDir'] ?? 'DESC') === 'ASC' ? 'ASC' : 'DESC';

    $sql = 'SELECT * FROM users';
    $types = '';
    $values = [];
    if ($search !== '') {
        $sql .= ' WHERE fiscalcode LIKE ? OR email LIKE ? OR username LIKE ?';
        $like = '%' . $search . '%';
        $types = 'sss';
        $values = [$like, $like, $like];
    }
    $sql .= " ORDER BY $orderBy $orderDir LIMIT ?, ?";
    $types .= 'ii';
    $values[] = $start;
    $values[] = $limit;

    $stmt = $conn->prepare($sql);
    $stmt->bind_param($types, ...$values);
    $stmt->execute();
    $result = $stmt->get_result();

    $records = [];
    while ($row = $result->fetch_assoc()) {
        $records[] = $row;
    }
    return $records;
}
```

Look at the difference. The search text no longer touches the SQL string: in its place there is a `?`, a **placeholder**, and the real value travels separately through `bind_param()`. The database receives the query's structure and the data through two distinct channels, and can no longer confuse a piece of data with a command. If the attacker types `x' OR '1'='1`, that text simply becomes the string to search for — the database tries to find a user whose username literally contains `x' OR '1'='1`, finds none, and returns zero rows. The attack fizzles out with no damage. The legitimate search keeps working exactly as before.

A detail that confuses everyone, and that deserves to be cleared up once and for all: `$orderBy` and `$orderDir` **cannot** be passed as a `?`. Prepared-statement placeholders bind **values** — a number, a string, a date — not **identifiers** like column names or the keywords `ASC`/`DESC`. `ORDER BY ?` does not work: the database expects a column name there, not a piece of data. The correct defence for identifiers is different and is called a **whitelist**: you compare the received value against a closed list of allowed columns (`in_array($want, $allowedColumns, true)`) and, if it is not on the list, fall back to a safe default. The direction reduces to two possibilities only, `ASC` or `DESC`, on the same principle. General rule, keep it in mind: **values are bound, identifiers are whitelisted**. It is the distinction that separates those who have understood SQL injection from those who only know it by hearsay.

In the enterprise project of Part IX this logic will end up inside a testable *repository*, where query building is isolated and the allowed columns are declared in a single place. But the principle is identical to what you have just seen: parameters for values, a whitelist for identifiers.

## Search and Pagination

The total count uses a separate function. It is needed to work out how many pages to show:

```php
function getTotalUserCount(string $search = ''): int
{
    $conn = getConnection();

    $sql = 'SELECT COUNT(*) as total FROM users';
    if ($search) {
        $sql .= ' WHERE';
        if (is_numeric($search)) {
            $sql .= " id = $search OR age = $search";
        } else {
            $search = $conn->real_escape_string($search);
            $sql .= " fiscalcode like '%$search%' OR email like '%$search%' OR
             username like '%$search%'";
        }
    }
```

Full source: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-20/en/parte-06/cap-20/listing-02.php)

Real source: [`functions.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/functions.php).

Here the project uses `real_escape_string()`, which is a step up from `getUsers()`: the function escapes the special characters — the quote `'` becomes `\'` — so the text can no longer close the string and inject SQL. It works, but it is worth understanding why prepared statements are still the better choice. *Escaping* is a defence you have to remember to apply **every time**, on **every** variable, with the right function for the right type: one forgotten `real_escape_string()` in one place and the door is open again. A prepared statement, by contrast, separates data and commands by construction: there is nothing to remember to do. The difference between this project's two sibling functions — one with escaping, one without — is living proof of how fragile it is to rely on memory. Note also the `is_numeric($search)` branch: there the value goes into the query without even escaping, on the assumption that if it is numeric it cannot do harm. It is an assumption that holds for a single character, but it is again the kind of case-by-case reasoning that prepared statements make unnecessary.

Beyond security, there is a correct **design** choice here and it is worth recognizing: `getTotalUserCount()` is a separate function, distinct from `getUsers()`. Because counting the rows and reading them are two different responsibilities. The list serves only the records of the current page — ten rows, with `LIMIT` — while the count needs to know how many records exist **in total**, ignoring the `LIMIT`, because it is that number that tells us how many pages are needed. They are two different questions, so two different queries, so two functions. It is a small application of the single-responsibility principle: had you put everything in one function, you would have had to return two unrelated things — the rows *and* the total — and sooner or later someone would have used them in a confusing way.

It is the count that makes the pagination arithmetic possible, and it is simpler than it looks. With `recordsPerPage` records per page, page `page` must skip the rows of the previous pages: `start = recordsPerPage * (page - 1)`. Page 1 starts at 0, page 2 at 10, page 3 at 20, and so on. The `LIMIT start, recordsPerPage` clause tells the database "skip `start` rows, then give me `recordsPerPage`". The total number of pages is `ceil(total / recordsPerPage)`: with 47 users and 10 per page that is 5 pages, the last with only 7 records. Three formulas, and that is the whole of the pagination you see at the bottom of the list.

![The same list after a search: the `WHERE` clause narrows the result set, and the search parameters are preserved in the sorting and pagination links.](figures/cap-20/search-filter.png)

A user-experience detail visible in the figure: when you search, the search parameters are preserved in the column links and in the pagination bar. This is not by accident — it is code that, in every link, rebuilds the complete *query string*. Without it, changing page or re-sorting would reset the search, and the user would suddenly be faced with all the records. It is the kind of detail that distinguishes a polished application from an exercise.

## One Form for Create and Update

The `userForm.php` view decides whether the form is creating or updating a user:

```php
<?php

$action = 'store';
$buttonName = 'SAVE';
$formTile = 'INSERT USER';
if ($user && $user['id']) {
    $action = 'update';
    $buttonName = 'UPDATE';
    $formTile = 'UPDATE USER';
}
foreach ($user as &$value) {
    $value = htmlspecialchars($value ?? '');
}
?>
```

Full source: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-20/en/parte-06/cap-20/listing-03.php)

Real source: [`view/userForm.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/view/userForm.php).

A **single** form for two operations. The logic is simple: if a `$user` reaches us with an `id`, we are editing and we prepare the action, the button label and the title accordingly; otherwise we are creating. It is a concrete application of the **DRY** principle (*Don't Repeat Yourself*): the form's fields — username, email, age, role — are identical in both cases, and maintaining two nearly-identical forms would mean applying every change in two places, with the statistical certainty of forgetting one. A single form, changing only the few things that genuinely differ, is shorter to write and safer to maintain.

The truly important line is the final `foreach`, and it is again a matter of security — this time of a different family. Before re-inserting the values into the form fields, every value passes through `htmlspecialchars()`. The reason: these data come from the **database**, but they got into the database because *somebody typed them*. If a user had registered with the username `<script>alert(document.cookie)</script>`, printing it verbatim inside a `value` attribute of the form would execute that script in the browser of anyone who opens the edit page. This is the **XSS** attack (*Cross-Site Scripting*), SQL injection's cousin but on the client side. `htmlspecialchars()` converts the dangerous characters into their HTML entities — `<` becomes `&lt;`, `"` becomes `&quot;` — so the text is *displayed* rather than *executed*.

The principle to take home is symmetric to the SQL one: **escape data in the context you insert it into**. Towards the database, parameters; towards HTML, `htmlspecialchars()`. And above all: never trust a piece of data just because it "comes from the database" and not directly from the user. What reaches the database was written by somebody anyway, and that somebody might not have good intentions.

## Saving a New User

`storeUser()` uses a prepared statement and stores the password with `password_hash()`:

```php
function storeUser(array $data): int
{
    $conn = getConnection();
    $sql = 'INSERT INTO users (username,email,fiscalcode,age,avatar, password,role_type) values( ?, ?, ?,?,?,?,?)';
    $stm = $conn->prepare($sql);
    $password = password_hash($data['password'], PASSWORD_DEFAULT);
    $stm->bind_param(
        'sssisss',
        $data['username'],
        $data['email'],
        $data['fiscalcode'],
        $data['age'],
        $data['avatar'],
        $password,
        $data['role_type']

    );
    $stm->execute();
```

Full source: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-20/en/parte-06/cap-20/listing-04.php)

Real source: [`model/User.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/model/User.php).

Here the project does things properly, and it is useful to compare this function with the earlier `getUsers()`: where reading took the shortcut, writing uses a full prepared statement. Seven `?` placeholders in the query, seven values passed to `bind_param()`, and no user data touching the SQL string. An `INSERT` is potentially more dangerous than a `SELECT` — it writes to the database — so it is right for the discipline to be rigorous here.

The first argument of `bind_param()`, the string `'sssisss'`, is the piece that throws people the first time they see it. It is the declaration of the **types**, one character per placeholder, in order: `s` for *string*, `i` for *integer*, `d` for *double*, `b` for *blob*. Here: username string, email string, fiscalcode string, age **integer**, avatar string, password string, role string — hence `sssisss`. The type string and the list of values must match in number and in order: if you get it wrong and declare `s` where the value is an integer it is usually no drama, but if you swap the order of the values you write the email into the fiscalcode column without PHP protesting. It is the one fragile spot of prepared statements with mysqli, and in Part IX we will see that PDO offers an alternative with **named** parameters (`:username`) that removes the counting problem.

Note also that the password is never stored as it is: it goes through `password_hash()` before entering `bind_param()`, exactly as we explained in Chapter 22. The hash ends up in the database, never the plaintext password.

## Updating a User

The update dynamically builds the optional fields for password and role:

```php
function updateUser(array $data, int $id): bool
{
    $conn = getConnection();
    $types = 'sssis';
    $values = [
        $data['username'],
        $data['email'],
        $data['fiscalcode'],
        $data['age'],
        $data['avatar']
    ];
    $sql = 'UPDATE users SET username = ?, email = ?, fiscalcode = ?, age = ?,avatar=? ';
    if ($data['password']) {
        $sql .= ', password = ? ';
        $types .= 's';
        $values[] = password_hash($data['password'], PASSWORD_DEFAULT);
    }
```

Full source: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-20/en/parte-06/cap-20/listing-05.php)

Real source: [`model/User.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/model/User.php).

The update has one more requirement than the insert: some fields are **optional**. If the user leaves the password field empty while editing, we do not want to overwrite the existing hash with an empty string — we want to leave the password as it was. The same goes for the role. The project's solution is to build the query **piece by piece**: you start from the always-present fields (`username`, `email`, `fiscalcode`, `age`, `avatar`), and only if `$data['password']` has a value do you add `, password = ?` to the query, `s` to the type string and the new hash to the list of values.

The delicate point of this scheme is that **three things must stay aligned**: the SQL text, the type string and the array of values. Every time you add a `?` to the query you must add the corresponding type character *and* the value, in the same order. The code does it carefully — note how the three updates (`$sql .=`, `$types .=`, `$values[] =`) always travel together, as a block. It is a pattern that works but demands discipline: it is exactly the repetitiveness that in Part IX a *query builder* or an ORM take out of the way, generating placeholders and types automatically. Here, in the procedural state, seeing it by hand makes you understand what those abstractions do for you.

A methodological note that holds beyond this function: it is best to validate `$data` thoroughly *before* reaching the model. The model should receive already-consistent data — an age that really is a number, an email that really has the shape of an email — and concern itself only with storing it. Mixing validation and persistence in the same function is another of those shortcuts that look harmless and then make the code hard to test and to reuse.

## Action Controller

The `updateRecord.php` controller protects the actions and routes `store`, `update`, and `delete`:

```php
<?php

declare(strict_types=1);
require_once '../includes/session.php';
require '../functions.php';
require_once '../includes/acl.php';
if (!is_user_logged_in() || !user_can_update()) {
    redirect('../login.php');
}

require '../model/User.php';
$action = getParam('action');
switch ($action) {
```

Full source: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-20/en/parte-06/cap-20/listing-06.php)

Real source: [`controller/updateRecord.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/controller/updateRecord.php).

The controller is the gateway for the actions that modify data, and the first thing it does — before even looking at *which* action — is the access check: `is_user_logged_in()` verifies authentication, `user_can_update()` authorization. If either is missing, `redirect()` and the request ends there. Only after passing this gate is the model loaded and the action dispatched with the `switch`.

The order is the important thing, and it is the same *fail fast* logic we saw in Chapter 22: **authorize first, then act**. Not a single record is touched before the check has passed. Putting it at the top, and not scattered inside the individual `case` branches, guarantees that no branch of the `switch` can be reached by mistake without a check.

And here returns the point I anticipated in the previous chapter and that is worth hammering home, because it is the most common conceptual mistake about authorization: **the controller must not trust the view**. In Chapter 23 we will see that the menu hides the "edit" and "delete" buttons from users without the permissions. But hiding a button is only cosmetic: the URL `controller/updateRecord.php?action=delete&id=5` exists anyway, and anyone can type it by hand into the address bar or build it with `curl`. If the only defence were the hidden button, a normal user could delete records simply by guessing the URL. It is the check *here, in the controller*, on the server, that makes the action truly protected. The view improves the experience; the controller guarantees security. When you have to choose only one, always choose the controller.

## In summary

This chapter is the first real jump from script to application, and it lines up the themes that will stay with us until the end of the book. **Parametric reading** (`getUsers`) forced us to confront SQL injection: values are bound with prepared statements, identifiers like `ORDER BY` are whitelisted — never concatenate user input into the SQL string. The **separate count** (`getTotalUserCount`) gave us the pagination arithmetic and an example of well-divided responsibilities. The **single form** for create and update showed the DRY principle and escaping with `htmlspecialchars()` against XSS. The **writing** functions (`storeUser`, `updateUser`) used prepared statements properly, with the type string and the dynamic construction of optional fields. The **controller** put authorization before the action, on the server, without trusting what the view shows or hides.

The thread tying them together is a single one: **every piece of data that crosses a boundary — from the request to the query, from the database to the HTML — must be handled by the rules of the context it enters**. The UMS repository does it in procedural form, with a few inconsistencies I preferred to show you rather than hide, because it is by learning to recognize them that you become able to fix them. In Part IX the same mechanisms will come back inside repositories, query builders and centralized validation: the shortcuts will disappear, but the principles will remain exactly these.
