# 13. Superglobals

With this chapter we get to the heart of PHP as a language for the web. Up to this point we have written scripts that process data that we ourselves put into the code; now let's see how PHP receives data arriving **from outside**: the parameters of a request, the values ​​of a form, server information, files uploaded by a user, session data. All of this is delivered to us through a special group of arrays that PHP automatically populates for us: the **superglobals**.

They are called this because they are "super global" variables: they are accessible **at any point** of the script — inside a function, inside a method, in any scope — without needing to declare them with `global` and without passing them as arguments. PHP creates and fills them before our code even starts running. You recognize them immediately because they all have a name that begins with `$_` (with the only historical exception of `$GLOBALS`): `$GLOBALS`, `$_SERVER`, `$_GET`, `$_POST`, `$_COOKIE`, `$_REQUEST`, `$_FILES`, `$_SESSION`, plus `$_ENV`. In this chapter we see them one by one, with concrete examples, because they are the front door of any web application and we will use them in every project in the book.

## $GLOBALS: Access global variables

Let's start with `$GLOBALS`, the least used but the oldest superglobal: it has always existed in PHP. `$GLOBALS` is a kind of **cauldron** in which all the variables that live in the **global scope** of the script end up, i.e. all those declared outside of a function. Inside `$GLOBALS` we also find the other superglobals (`$_GET`, `$_POST`, `$_COOKIE`, `$_SERVER`, `$_FILES`) and every global variable that we have defined.

The interesting feature is that `$GLOBALS` is accessible everywhere, even inside a function, without doing any import. Let's check it out. We declare a variable in the global scope and try to read `$GLOBALS` from inside a function:

```php
<?php

$testGlobal = 'This is a global variable';

function test()
{
    var_dump($GLOBALS);
}

test();
```

Full source: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/en/parte-04/cap-13/listing-01.php)


Running the script we see that `$GLOBALS` is an array whose keys are the **names of the global variables** (without the dollar sign) and the names of the superglobals. `testGlobal` also appears at the bottom of the list: the key is exactly the name of the variable, `testGlobal`, without the `$`, and its value is the string we assigned to it.

If we are interested in a single global variable, just use its name as the array key:

```php
function test()
{
    echo $GLOBALS['testGlobal'];
}
```

Full source: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/en/parte-04/cap-13/listing-02.php)


Inside the function we thus have access to the global variable, despite having neither declared it there nor received it as an argument.

### The global construct

There is a second way to access a global variable from within a function: the **`global`** construct. By writing `global $testGlobal;` we are telling PHP "import the global variable `$testGlobal` into the function":

```php
function test()
{
    global $testGlobal;
    echo $testGlobal;
}
```

Full source: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/en/parte-04/cap-13/listing-03.php)


The result is identical. Personally I prefer the form `$GLOBALS['testGlobal']`, which makes it explicit that we are drawing from the global array, but both work.

There is a case in which `$GLOBALS` is particularly useful: when inside the function there already exists a **local variable with the same name** as a global variable. In that situation, the bare name refers to the local variable, while `$GLOBALS['...']` continues to point to the global one, without conflicts:

```php
function test()
{
    $testGlobal = 'function test';

    echo $testGlobal;              // "function test"  → local variable
    echo $GLOBALS['testGlobal'];   // "This is a global variable" → global
}
```

Full source: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/en/parte-04/cap-13/listing-04.php)


As you can see, the local and global variables coexist without overwriting each other.

### A tip from experience

Having said that, I'll give you some advice as a general rule: **avoid global variables**. They are dangerous because they can be overwritten elsewhere in the program without you realizing it, and in large applications they become an inexhaustible source of bugs that are difficult to track down. If you need to share values ​​globally, there are much cleaner alternatives: include a file that **returns an array** of constants or configurations (the pattern we saw in Chapter 15), or a class with static properties and methods. They are ways to not "contaminate" the global environment.
One last note. `$GLOBALS` also contains the other superglobals, so you could technically read `$GLOBALS['_POST']` instead of `$_POST`:

```php
print_r($GLOBALS['_POST']);
```

Full source: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/en/parte-04/cap-13/listing-05.php)


But there is no reason to do so: `$_POST` is already accessible everywhere on its own. So `$GLOBALS` we will use it, if ever, only for global scope variables, while for superglobals we will always use their direct name.

## $_SERVER: Server and request information

`$_SERVER` is an array that PHP fills with a lot of information about the **server** and the **HTTP request** in progress. Some of this information concerns the machine on which the server runs and can change from one server to another; others concern the single request that the browser has just made. The best way to get an idea of what's in it is to print it out:

```php
<?php

var_dump($_SERVER);
```

Full source: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/en/parte-04/cap-13/listing-06.php)


Among the many voices, these are the ones that are used most often:

- **`REMOTE_ADDR`** — the IP address of the user who connected. Very useful for tracking visits, recording where users come from, applying limitations.
- **`HTTP_USER_AGENT`** — the string that identifies the user's browser and system.
- **`REQUEST_METHOD`** — the HTTP method of the request: `GET`, `POST`, `PUT`, etc.
- **`QUERY_STRING`** — the string of parameters passed via URL, as it was sent.
- **`REQUEST_URI`** — the URL requested starting from the document root, including parameters.
- **`SCRIPT_FILENAME`** — the full path to the file we are executing.
- **`PHP_SELF`** — the path to the running script relative to the document root.
- **`DOCUMENT_ROOT`** — the root directory of the site, set in the web server (for example the Apache `htdocs` folder).
- **`SERVER_PROTOCOL`** — the protocol and version, for example `HTTP/1.1`.
- **`SERVER_ADDR`** and **`SERVER_NAME`** — the IP address and name of our server.
- **`SERVER_SOFTWARE`** — the software and version of the web server.

To read a single entry, you access the array like a normal array, indicating the key. For example, to get the user's IP:

```php
echo $_SERVER['REMOTE_ADDR'];
```

Full source: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/en/parte-04/cap-13/listing-07.php)


Many of these variables come from the **headers** that the browser sends to the server with each request. If you open the browser's developer tools (right click, *Inspect*), go to the *Network* tab and reload the page, you can see the request and response headers: the method, the state (`200`), the domain, the user agent, the accepted language, the encoding, and so on. PHP takes a lot of this information and makes it available to us inside `$_SERVER`.

### Detecting the browser from the user agent (and why it's unreliable)

A classic use of `HTTP_USER_AGENT` is to understand which browser the user is visiting us with, for example to collect some statistics:

```php
echo $_SERVER['HTTP_USER_AGENT'];
```

Full source: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/en/parte-04/cap-13/listing-08.php)


The value is a long string that typically starts with `Mozilla/5.0` and contains "clues" about the browser: the presence of `Gecko` suggests Firefox, `Trident` older versions of Internet Explorer, and so on. With a regular expression we could extract this information. But be careful: over the years, browsers have changed the way they compose this string several times — Internet Explorer, for example, stopped writing in a certain way and added `like Gecko` — so relying on the user agent for browser detection has gradually become less reliable. Today there are special libraries and, often, it is more robust to do these checks on the client side. But for statistical or logging uses, `HTTP_USER_AGENT` remains convenient: we can save it in a database together with the IP to know who visits our pages and with which tool.

## $_GET: the query string data

Let's move on to the two superglobals that we will use the most: `$_GET` and `$_POST`, the two channels through which a user sends us data. Let's start with **`$_GET`**.
`$_GET` contains all the parameters that are passed via **query string**, i.e. that part of the URL that follows the question mark. If in the previous chapter we saw the raw `QUERY_STRING` inside `$_SERVER`, here we find it already sectioned: each parameter becomes a key of the array and its value becomes the associated value. Let's see it now. Let's take a URL with two parameters:

```text
index.php?username=John&lastname=Smith
```

Full source: [listing-09.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/en/parte-04/cap-13/listing-09.txt)


and we print `$_GET`:

```php
<?php

var_dump($_GET);
```

Full source: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/en/parte-04/cap-13/listing-10.php)


We obtain an array with two elements: the key `username` with value `John` and the key `lastname` with value `Smith`. The keys are the names of the parameters, the values ​​are the ones we passed in the URL.

One thing to pay attention to: if we pass "special" characters in the URL, such as accented letters, the browser normally **encodes** them (for example a space becomes `%20`). On the PHP side, if necessary, we can decode these values ​​with `urldecode()`. This is something to take into account when data arrives from the web.

### Show all errors during development

Before we move forward, a good practice: **during development, always show all PHP errors**. So you immediately notice if you are reading a key that doesn't exist. You can set it in the file `php.ini`, or directly in the script with `ini_set()` and `error_reporting()`:

```php
<?php

ini_set('display_errors', 1);
error_reporting(E_ALL);
```

Full source: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/en/parte-04/cap-13/listing-11.php)


With `display_errors` to `1` PHP shows the errors on the screen, and with `error_reporting(E_ALL)` we ask it to report them all, including warnings and notices.

### Check if a parameter exists

And that's why you need to have active errors. The superglobals `$_GET` and `$_POST` **always exist**, even when they are empty: doing `var_dump($_GET)` with no parameters in the URL gives no error, it just shows an empty array. The problem arises when we try to read a **key** that has not been passed: PHP issues a warning ("undefined array key"). Therefore, before reading a value from an array — any array, not just superglobals — we must always verify that the key exists. We have three tools, with different nuances.

The first is **`isset()`**, which tells us if the variable (or key) is set:

```php
if (isset($_GET['username'])) {
    var_dump($_GET['username']);
}
```

Full source: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/en/parte-04/cap-13/listing-12.php)


Attention to one subtlety: `isset()` checks that the variable is set, not that it has a "full" value. An **empty string** is considered set (`isset()` returns `true`), while a value `null` is considered **not** set: for PHP a variable is set only if it has been declared and its value is not `null`.

The second is **`empty()`**, which checks whether the value is "empty". It should be used with caution, because for PHP the `0` and the string `"0"` are also considered empty: if we expect that a parameter can legitimately be zero, `empty()` would mislead us.

The third is the **`array_key_exists()`** function, which exclusively checks the presence of the **key**, regardless of the value:

```php
if (array_key_exists('username', $_GET)) {
    var_dump($_GET['username']);
}
```

Full source: [listing-13.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/en/parte-04/cap-13/listing-13.php)


The practical difference with `isset()` lies precisely in `null`: if a value has been set to `null`, `isset()` considers it absent, while `array_key_exists()` confirms that the key is there. Which one to use depends on what you want: if a value `null` makes no sense to you and should be treated as "absent", `isset()` is fine; if, however, you need to know for sure whether the key exists - typical when you work with records that come from the database and you want to know if a certain column is present - then `array_key_exists()` is the right choice. I repeat: all this applies to any PHP array, not just superglobals.

### Pass data via GET: URL, link and form

There are multiple ways for parameters to end up in the query string, and therefore in `$_GET`:

**By handwriting them in the URL**, as we did in the examples above.

**With a form that uses the GET method.** Let's prepare a simple HTML form (here I use some Bootstrap class just for the appearance) that points to the same page:

```html
<form action="index.php" method="get">
    <input type="text" name="username" id="username" placeholder="First name">
    <input type="text" name="lastname" id="lastname" placeholder="Last name">
    <input type="reset" value="Reset">
    <button type="submit">Send</button>
</form>
```

Full source: [listing-14.html](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/en/parte-04/cap-13/listing-14.html)


The `input` field of type `reset` is a little trick that clears the form with just one click. By filling in the fields and sending, the values ​​appear in the query string (`?username=...&lastname=...`) and we find them in `$_GET`: the key of each value is the `name` attribute of the input. That's why the `name` of each field is so important: it's that, not the `id`, that determines the key inside `$_GET`.

**With a simple link.** Even a `<a>` tag with parameters in the URL sends data via GET when you click on it:

```html
<a href="index.php?username=test&lastname=testLastname" class="btn btn-danger">Test</a>
```

Full source: [listing-15.html](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/en/parte-04/cap-13/listing-15.html)


By clicking, the parameters `test` and `testLastname` arrive on the page exactly as if we had written them by hand.

Precisely because it is so easy to construct a query string — by hand, with a link, or with any HTTP client — we cannot blindly trust the data arriving via GET. We have no guarantee that it was really the user who sent them via our form: someone could manipulate the URL or simulate the request. It is a safety principle to always keep in mind, and we will take it up again in the projects.

## $_POST: data sent via POST

Let's now see the difference with the **POST** method and how the data sent in this way is mapped into the superglobal **`$_POST`**.

If we print `$_POST` without having sent anything via POST, the array is empty: no variable arrived this way. To send data via POST all you need is a form with `method="post"`. Simply change the `method` attribute of the form we had before:

```html
<form action="index.php" method="post">
    <input type="text" name="username" id="username" placeholder="First name">
    <input type="text" name="lastname" id="lastname" placeholder="Last name">
    <button type="submit">Send</button>
</form>
```

Full source: [listing-16.html](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/en/parte-04/cap-13/listing-16.html)


The most obvious difference is that with POST the variables **do not travel in clear text in the URL**: the query string remains clean, and the values are transmitted in the body of the request. By submitting the form with `John` and `Arias`, `$_GET` remains empty while `$_POST` contains `username` and `lastname` with the values ​​entered.

`$_GET` and `$_POST` are **two separate arrays**. We can even send the same parameter names both ways at the same time — for example, by putting some parameters in the `action` of the form (which travels in GET) and others in the fields (which travels in POST) — and each value will end up in its own array, without mixing. If `username` arrives via both GET and POST, we will find it in `$_GET['username']` with the value of the query string and in `$_POST['username']` with the value of the form: there is no overwriting between the two.

To read a value, the same checks seen before apply. If we want to read the username sent via POST, and only that, we check the key and read it:

```php
if (isset($_POST['username'])) {
    echo $_POST['username'];
}
```

Full source: [listing-17.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/en/parte-04/cap-13/listing-17.php)


The rule of thumb is this: **read variables from the same channel you sent them through**. If you have decided that your form is POST, read from `$_POST`; if it is GET, read from `$_GET`. This way you avoid someone injecting "dirty" variables from the other channel and overwriting your data.

## Summary: $_GET, $_POST and $_COOKIE

Let's take stock of the three channels through which the data of a request reaches PHP.

- **`$_GET`** contains the variables passed via **query string**: written by hand in the URL, sent from a form with GET method, contained in a link or placed in the `action` of a form.
- **`$_POST`** contains the variables sent via **POST**: from a form with POST method, or from an HTTP client that makes a POST request to our server.
- **`$_COOKIE`** contains the **cookies** that the browser sends back to us with each request. We set a cookie with the `setcookie()` function, indicating its name, value, life time (expressed in seconds since the Unix era), the folder or domain for which it is valid, and other parameters. Once set, the next time the page is reloaded the browser sends it back to us, and we read it in `$_COOKIE`. We dedicate the next chapter entirely to cookies, so here we limit ourselves to placing them in the superglobal group.
An important detail about cookies, which explains why we isolate them from the rest: the first time you set a cookie, it is **not** yet in `$_COOKIE`. `$_COOKIE` contains what the browser is sending **now**, and at that moment the browser does not yet know the cookie we are sending it for the first time. We will see it populated only by the next request. We will return to this distinction in Chapter 14.

## $_REQUEST and conclusion

Finally, there is a superglobal that unites the three channels just seen: **`$_REQUEST`**. `$_REQUEST` is an array that **fuses** (merges) `$_GET`, `$_POST` and, depending on the configuration, `$_COOKIE`. If the same key arrives from multiple channels, one overwrites the other in a precise order.

Let's see it with an example. Suppose we pass `username=Taylor` and `lastname=Smith` via query string, and simultaneously send a form via POST with `username=John` and `lastname=Arias`:

```php
var_dump($_GET);      // Taylor, Smith
var_dump($_POST);     // John, Arias
var_dump($_REQUEST);  // John, Arias  ← POST wins
```

Full source: [listing-18.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/en/parte-04/cap-13/listing-18.php)


In `$_REQUEST` we find the values of the POST: in the default order, the POST arrives after the GET and therefore overwrites it.

### Who decides the order: request_order

The order in which `$_REQUEST` is filled is not set in stone: it depends on the **`request_order`** setting (and secondarily on `variables_order`) in the `php.ini` file. In recent versions of PHP the default value is `GP`, i.e. "GET first, then POST": POST has priority and cookies are **not** included. Personally, it's the setting I prefer: I don't like having cookies in `$_REQUEST` too. However, if we changed `request_order` to, for example, `GPC`, then the cookies would also enter the merge and, being last, could overwrite GET and POST. After tapping `php.ini` you must restart the web server for the new setting to be loaded.

### Why be wary of $_REQUEST

Precisely because the behavior of `$_REQUEST` depends on the server configuration, **don't get used to always reading from `$_REQUEST`** without caring whether the data arrived via GET or via POST. Look at this case: if you don't send the form but the values ​​are present only via GET, and in the merge the (empty) POST still "won", you could find yourself with empty values ​​in `$_REQUEST` despite having valid data in `$_GET`. The message is: **be specific about what you want from each channel**. Reading from `$_REQUEST` is convenient, but it exposes you to surprises and small security flaws; reading from the right channel is almost always the best choice.

We close with the observation from which we started: all these superglobals are really *super* because they are accessible everywhere, even inside a function, without having to write `global` in front of anything. We just need to use their name and, if necessary, the key:

```php
function test()
{
    var_dump($_GET, $_POST, $_SERVER);
}

test(); // works: superglobals are visible in here too
```

Full source: [listing-19.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/en/parte-04/cap-13/listing-19.php)


We are left with two particularly important superglobals, which deserve separate treatment: `$_FILES`, to manage the uploading of files, and `$_SESSION`, to store data between one page and another.

## $_FILES: uploading files

The superglobal **`$_FILES`** gives us access to the files that the user has uploaded through a form. That is, we only have access to it when an **upload** has occurred.

To upload a file two conditions are needed on the HTML side. The first is a field `input` of type `file`. The second, often forgotten, is that the form has the **`enctype="multipart/form-data"`** attribute: without it the file is not transmitted. This type of encoding tells the browser to send the request in "multiple parts", one for the normal key-value fields (like `username`) and one for the binary contents of the file. Here is a minimal form:

```html
<form action="index.php" method="post" enctype="multipart/form-data">
    <input type="text" name="username" placeholder="First name">
    <input type="file" name="avatar" id="avatar">
    <button type="submit">Send</button>
</form>
```

Full source: [listing-20.html](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/en/parte-04/cap-13/listing-20.html)


### The structure of the $_FILES array

Before loading anything, `$_FILES` is empty. After submitting the form with a file, it contains an array whose key is the **field name** (the `name` attribute of the input, here `avatar`), and whose value is itself an array with information about the file. Let's check it out:

```php
var_dump($_FILES);
```

Full source: [listing-21.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/en/parte-04/cap-13/listing-21.php)


For each uploaded file we find these keys:
- **`name`** — the original name of the file as it was on the user's computer (for example `foto.jpg`).
- **`type`** — the MIME type declared by the browser (for example `image/jpeg`).
- **`tmp_name`** — the path to the **temporary** file where the server saved the upload (in the system temp folder). From here we will have to move it to its final destination.
- **`error`** — the upload error code: it is `0` if everything went well.
- **`size`** — the size of the file in bytes.

If there were two file fields in the form — for example `avatar` and `avatar2` — then `$_FILES` would be an **array of arrays**: a key for each field, and under each the five properties just listed.

### Save the uploaded file safely

Let's see how to use this data to copy the file from the temporary folder to our own folder. Suppose we have, in the same directory as the script, a writable `images` folder. We cycle on `$_FILES` and, for each file, we do two fundamental checks before moving it:

```php
<?php

if (!empty($_FILES)) {
    foreach ($_FILES as $key => $file) {

        // 1. is it really a file uploaded via HTTP? (security)
        // 2. did the upload complete successfully?
        if (is_uploaded_file($file['tmp_name']) && $file['error'] === UPLOAD_ERR_OK) {

            $dir = __DIR__ . '/images';
            $fileName = basename($file['name']);
            $destination = $dir . '/' . $fileName;

            if (move_uploaded_file($file['tmp_name'], $destination)) {
                echo "The file {$fileName} was uploaded successfully.<br>";
            }
        }
    }
}
```

Full source: [listing-22.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/en/parte-04/cap-13/listing-22.php)


Let's analyze the key steps:

- **`is_uploaded_file()`** receives the temporary path (`tmp_name`) and returns `true` only if that file was actually loaded via an HTTP POST request. It is a security check: it protects us from anyone who tries to make us process an arbitrary server file by passing it off as an upload.
- **`$file['error'] === UPLOAD_ERR_OK`** check that there have been no errors. `UPLOAD_ERR_OK` is a PHP constant that is `0`; we could also write `$file['error'] === 0`, but using the constant makes the code more readable.
- **`__DIR__`** is a magic constant that contains the absolute path to the folder where the current script is located (the equivalent of `dirname(__FILE__)`). Building the destination starting from `__DIR__` is more robust than writing a relative path: the script works whatever the current folder of the process. On Linux remember that this folder must have **write permissions** for the user with whom PHP runs, otherwise the move will fail.
- **`basename()`** applied to `$file['name']` extracts only the file name, discarding any paths. It is important to use `name` (the original name) and not `tmp_name` for the destination name: if we used the temporary path, we would end up with an incomprehensible name.
- **`move_uploaded_file()`** moves the file from the temporary location to the destination and returns `true` if successful. It is the function dedicated precisely to this purpose and should be preferred to a simple `copy()`, because it also verifies that the file comes from a legitimate upload.

### Two important precautions

First: **never trust the `type`** field. The MIME type declared in the form can be falsified by the person making the request. If you need to make sure that a file is really an image (or a PDF, an Excel document, etc.), check the actual type on the PHP side, analyzing the contents of the file with functions like `finfo` or `mime_content_type()`, not relying on `$file['type']`.

Second: the **name** you save the file with. You can keep the original name, but it is often better to generate a unique one — for example by prefixing a timestamp — to prevent two users uploading files with the same name from overwriting each other. Once you save the file, you typically record its name in the database. And if you're managing images, you can also resize them with GD library functions (like `imagecreatefromjpeg()`), or rely on a dedicated library.

Finally, to manage multiple files with a single field, you can use the syntax `name="avatar[]"` on the input and the HTML5 attribute `multiple`: in that case `$_FILES` collects all the files under a single key, as an array. The control and movement logic remains identical. If you already use a framework or library that manages uploads for you, now you know what happens "at the bottom" anyway: everything revolves around this global array, `$_FILES`.

## $_SESSION: Store data between pages

We arrive at the last superglobal, and one of the most important mechanisms of PHP for the web: the **session**, managed through `$_SESSION`.
A session is an environment in which we can **store data that survives from page to page**, throughout the user's "work session". In the classic case, in which the session is linked to a cookie, the data remains available as long as the user keeps the browser open; when the browser is closed the session disappears. This is the difference with actual cookies, which instead - as we will see in the next chapter - can persist even after the browser is closed. To identify which user a session belongs to, PHP in turn uses a cookie: on the first visit it generates a random identifier, sends it to the browser, and with each subsequent request the browser sends it back, allowing PHP to reconnect that request to the correct session data.

### Start the session with session_start()

If we print `$_SESSION` without starting anything, there is no active session and the array does not exist. The first step, always, is to start the session with **`session_start()`**:

```php
<?php

session_start();

$_SESSION['user_id'] = 4;
$_SESSION['logged'] = 1;
```

Full source: [listing-23.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/en/parte-04/cap-13/listing-23.php)


With `session_start()` the session opens. From this moment we can write values ​​inside `$_SESSION` as in a normal array: in the example we store the ID of a user and a flag indicating that he is logged in.

If we now look at the *Network* tab and the request headers in the browser developer tools, among the cookies we find one called **`PHPSESSID`**: it is the session identifier that PHP created for us. From here on, the browser will send it with every request, and any script on our site that shares that cookie will have access to the same `$_SESSION`.

### Read the session on another page

And that's exactly the point: data placed in session on one page is readable from another page. However, there is one condition: **the reading page must also call `session_start()`**. If on a second page we try to read `$_SESSION['user_id']` without starting the session, we get an undefined key error. By adding `session_start()` at the top, however, we find all the values:

```php
<?php

session_start();

var_dump($_SESSION['user_id']); // 4
```

Full source: [listing-24.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/en/parte-04/cap-13/listing-24.php)


Thus, any page that shares the session cookie (because it is in the same domain and folder) has access to the session variables. We will delve into the complete management and **security** of the sessions in a dedicated chapter, within the practical projects; Here we focus on the superglobal and its basic functioning.

### session_start() before any output

There is a technical constraint to respect. When we start the session, PHP sends the cookie `PHPSESSID` to the browser, and the cookies travel in the **headers**, which must be sent **before** any HTML content. Therefore `session_start()` cannot be preceded by any output: if before it we print even just one tag `<h1>`, or leave a space before the opening `<?php`, we risk the classic error *"cannot modify header information - headers already sent"*.

For this reason the rule of thumb is to put **`session_start()` as the very first instruction** of the file. In many configurations the error does not appear because *output buffering* is active (which puts the content in a buffer and sends it only at the end), but we cannot take it for granted on all servers. It is a topic that we will take up again and examine at the end of the next chapter, dedicated precisely to cookies and the error of headers already sent.

### Freeing the lock: session_write_close()

One last detail useful in real applications. When the session is managed on **file** (the default), the moment we call `session_start()` and start writing to it, PHP **locks** that session file. If another script tries to access the same session, it must wait for the first one to finish. In applications with many concurrent requests — think multiple AJAX calls starting at once — this can create bottlenecks, as requests queue up waiting for the lock to be released.

When we have finished writing (or reading) the session and we no longer need to keep it open, it is a good idea to close it explicitly with **`session_write_close()`**:

```php
session_start();

$_SESSION['user_id'] = 4;

// ...finished working with the session:
session_write_close();
```

Full source: [listing-25.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-13/en/parte-04/cap-13/listing-25.php)


With this call we declare that we have finished writing: PHP saves the data, releases the lock and the other concurrent requests can finally access the session. If you have scripts called via AJAX that need to run in parallel, remember to release the session as soon as you're done, so as not to lock the other files.

## In summary

- **superglobals** are arrays that PHP fills automatically and that are accessible in any scope — even inside a function — without `global`: `$GLOBALS`, `$_SERVER`, `$_GET`, `$_POST`, `$_COOKIE`, `$_REQUEST`, `$_FILES`, `$_SESSION`.
- **`$GLOBALS`** collects all the variables of the global scope (key = name without `$`). It can also be accessed via the `global` construct. Global variables are to be avoided: better a configuration file that returns an array or a class with static members.
- **`$_SERVER`** exposes server and request information: `REMOTE_ADDR` (user IP), `REQUEST_METHOD`, `QUERY_STRING`, `REQUEST_URI`, `PHP_SELF`, `SCRIPT_FILENAME`, `DOCUMENT_ROOT`, `HTTP_USER_AGENT`, and others. The user agent is convenient but unreliable for detecting the browser.
- **`$_GET`** contains the query string parameters (URL, link, form GET); **`$_POST`** those sent via POST (the data does not appear in the URL). They are separate arrays and do not overwrite each other.
- Before reading a key always check that it exists: **`isset()`** (the `null` counts as not set, the empty string does), **`empty()`** (pay attention to `0` and `"0"`) and **`array_key_exists()`** (check only the key, `null` included). This applies to every array.
- Always enable errors in development: `ini_set('display_errors', 1)` and `error_reporting(E_ALL)`. Don't trust the data arriving via GET/POST: it can be manipulated.
- **`$_REQUEST`** is the fusion of GET, POST (and cookie, if configured); the order depends on `request_order` in `php.ini` (default `GP`, POST wins). Better to read from the specific channel than to rely on `$_REQUEST`.
- **`$_FILES`** manages the upload: the form must have `enctype="multipart/form-data"`. For each file there are `name`, `type`, `tmp_name`, `error`, `size`. Save safely with `is_uploaded_file()`, checking `error === UPLOAD_ERR_OK` and `move_uploaded_file()`; don't trust `type`, check the real type.
- **`$_SESSION`** preserve data between pages: always start with `session_start()` (before each output, to avoid running into "headers already sent") in each page that needs to access it. PHP identifies the session with the `PHPSESSID` cookie. With file session, `session_write_close()` releases the lock and avoids bottlenecks with concurrent requests.
