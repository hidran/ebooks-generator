# 6. The basic syntax

With the development environment ready, it's time to write the first few lines of PHP. In this chapter we learn the fundamental elements of the syntax: the tags that delimit the PHP code, the semicolon that closes each statement, the comments and the `echo` construct. We'll also look at the two ways we can run a PHP script — from the terminal, like a normal program, and through a web server, as a web page — and we'll discover that PHP behaves slightly differently in the two cases.

In the second part of the chapter we focus on **expressions** and **literals**: what happens when we write `2 + 2;` in a PHP file, where the result ends up, and why, without a place to store it, that result immediately vanishes. It is the perfect premise for the next chapter, dedicated to variables, types and constants.

## Organize the code and create the first file

First of all, create a folder in which to collect all the code of this book, and inside it a subfolder for each chapter or topic: this way you will always have the code organized and easy to find. For this chapter we will use a folder called `intro`.

Open the folder with your editor — in the examples I use Visual Studio Code, but any editor you prefer is fine — and create a file inside it called `index.php`. VS Code immediately recognizes the `.php` extension and shows the PHP icon next to the file name.

As we saw in Chapter 5, it is best to install some components from the extensions view (search for "PHP") that will accompany us throughout the book:

- **PHP Debug**, for debugging the code;
- **PHP Intelephense**, for intelligent autocompletion;
- **PHP Extension Pack**, which groups together almost all the useful packages in one fell swoop;
- **PHP Server**, to start a web server "on the fly" and test the code immediately.

### The path to the PHP executable

From VS Code you can open the built-in terminal from the Terminal → New Terminal menu. The first thing to check when we enter a terminal is that PHP is available. On macOS and Linux you can find out where the executable is with:

```bash
which php
```

Full source: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-01.sh)


The command responds with the full path to PHP, for example:

```text
/opt/homebrew/bin/php
```

Full source: [listing-02.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-02.txt)


You also need this path in VS Code: if the editor reports that the PHP executable is not installed, it means that it cannot find it in the settings. Open Settings, search for "PHP" and you will see the settings of the various PHP extensions installed: in the field dedicated to the executable path (for example `php.validate.executablePath`) enter the path returned by `which php`. Set the same path in the PHP Server extension options as well, so autocompletion and code validation will work correctly.

Be careful if you use VS Code settings synchronization (the one connected to your GitHub account): it may happen that the editor inherits the path from another machine. For me, for example, the synchronization had brought the Windows path back to the Mac: on Windows with Laragon PHP it is found in a folder like `C:\laragon\bin\php\php-8.x\php.exe`, while on this Mac it is in `/opt/homebrew/bin/php`. The correct path always depends on the system you are using.

## PHP tags

Now we can start planning. The first thing to do in a PHP file is to declare that we are using PHP. Why? Because PHP, being a **scripting language**, can be included within an HTML page: when the web server processes the page, everything that is *outside* the PHP tags is left as it is, while only what is *inside* the tags is interpreted.

The **opening tag**, which tells the web server (or PHP interpreter) "there is PHP code from here on out", is:

```php
<?php
```

Full source: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-03.php)


With this we can start writing PHP. In many examples out there you will also see the **closing tag** `?>`, but this is only necessary if we are mixing PHP with HTML. If the file is pure PHP there is no need to close it — in fact, it is better *not* to close it: after an `?>` an empty line at the bottom of the file, which perhaps we don't even see, would be sent to output and could cause errors that are difficult to detect.

The first thing we can do to verify that PHP works is to use the `phpinfo()` function:

```php
<?php
phpinfo();
```

Full source: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-04.php)


Note the **semicolon** at the end: PHP needs it to understand where each **statement** ends. Warning: the semicolon should not be placed "at every line", but at the end of each statement. Later, when we write for example an `if` or a function, we will see that an instruction can easily continue on multiple lines.

## Run PHP from the terminal

Let's run our first script. From the terminal, we enter the project folder:

```bash
cd intro
ls -al
```

Full source: [listing-05.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-05.sh)


`ls -al` is a Linux (and macOS) command that shows the contents of a folder. If you are on Windows you have two ways to have the same commands:

- **WSL2** (Windows Subsystem for Linux), which is to all intents and purposes a Linux inside Windows;
- **Git Bash**: by searching for "Git for Windows" you can install Git — convenient though, because you will also have a code versioning tool — and together you get the Bash shell. Git exists for macOS, Windows and Linux, and on Windows the installation gives you just that console.

In VS Code, when you open the terminal from Terminal → New Terminal, you can click on the arrow next to the `+` button and choose between the different consoles available: on Windows you will see the classic terminal, PowerShell, Git Bash and so on. In the examples I use Bash, but the command to run PHP is identical on any system — Linux, Windows or macOS: just write `php`, a space and the file name.

```bash
php index.php
```

Full source: [listing-06.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-06.sh)


It works! The output, however, is enormous: `phpinfo()` prints all the information about the PHP installation — the version, all the configuration directives found in the `php.ini` file (we'll see this later), the installed libraries and extensions, and so on. It's a valuable function: if you have a hosting service and want to check how PHP is configured without going through the provider's interface, just upload a file with this code and you'll have all the information.

## Run PHP as a web page

If we run the same `index.php` through a web server, instead of raw text we will see a real web page. There are two convenient ways to do this.

### The PHP Server extension

With the PHP Server extension installed, right-click the file and choose the PHP Server entry to serve the project. If the entry doesn't appear in the context menu, press Shift+Cmd+P on Mac (Ctrl+Shift+P on Windows) and type "server": choose **PHP Server**, not Live Server — Live Server is only good for static HTML pages. Alternatively, at the top right of the editor there is the extension icon: one click and the server starts.

PHP Server automatically creates a local web server on a dedicated port and opens the browser on our `index.php` page: this time `phpinfo()` appears as a formatted page, with tables and colors. If we right-click in the browser and look at the source of the page, we see the HTML tags that were not there from the terminal. Why? Because PHP *notices* how it runs: when it runs from the command line it produces plain text, when it runs behind a web server it produces HTML.

### The integrated PHP server

We can also do what VS Code does with the extension from the command line: PHP includes a development web server as standard. Just have PHP installed and launch `php -S` (with a capital S) followed by host and port; with the `-t` option we indicate the folder to serve. For example, if we are in the project folder and want to serve the `intro` subfolder:

```bash
php -S localhost:8000 -t intro
```

Full source: [listing-07.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-07.sh)


Now let's open the browser to `http://localhost:8000` and see our page. A practical tip: if the port is already busy - it happened to me with a Laravel project listening on 8000 - just stop the server with Ctrl+C and relaunch it on another port, for example 3000:

```bash
php -S localhost:3000 -t intro
```

Full source: [listing-08.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-08.sh)


### The comments

If we don't want a line of code to execute, we can **comment it out**. A comment on a single line is written with the double slash `//`; there is also the block comment, which opens with `/*` and closes with `*/` and can extend over multiple lines — we will return to it later.

```php
<?php
// phpinfo();  this line is now a comment and is not executed

/*
  This is a comment
  over multiple lines.
*/
```

Full source: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-09.php)


We comment out the call to `phpinfo()` and re-execute the file from the command line: nothing comes out anymore. Let's reload the page in the browser: here too, empty page. The comment "turned off" the only statement in the file.

## Mix PHP and HTML

Let's do an experiment: let's add, *before* the PHP tag, a normal HTML tag.

```php
<h1>Hello World</h1>
<?php
```

Full source: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-10.php)


We restart the web server and reload the page: the title appears. As we were saying, the web server serves the HTML as it is; only what is inside the PHP tags is interpreted.

What if we add some PHP? Let's immediately learn the first PHP command: `echo`, which writes output whatever we pass to it. We open the quotes, write a string and close with a semicolon, because that is where the statement ends:

```php
<h1>Hello World</h1>
<?php
echo "My name is John";
```

Full source: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-11.php)


Let's reload the page: with PHP we wrote this string in the web page. And that's not all: we can put some HTML *inside* the string, for example an `<h3>` tag:

```php
<h1>Hello World</h1>
<?php
echo "<h3>My name is John</h3>";
```

Full source: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-12.php)


What exactly is happening? We're sending a web page to the browser, and the browser interprets what it receives as HTML: upon reloading the page the text appears formatted as a third-level title, and looking at the source we see that we have *generated* some HTML with PHP.

If we now launch the same file from the terminal, in another terminal tab:

```bash
php intro/index.php
```

Full source: [listing-13.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-13.sh)


```text
<h1>Hello World</h1><h3>My name is John</h3>
```

Full source: [listing-14.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-14.txt)


the same thing is done, but here we don't see a web page - we're not in a browser, we're in the command line, so we see the raw HTML output that PHP generates.

Finally, as anticipated, we can also close the PHP tag with `?>` and, after closing, write more HTML:

```php
<h1>Hello World</h1>
<?php
echo "<h3>My name is John</h3>";
?>
<p>PHP is great</p>
```

Full source: [listing-15.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-15.php)


From the terminal we also see the paragraph in the output; in the browser, without having to look at the source, the paragraph appears on the page. But remember the rule: the closing tag is only useful when there is HTML after it; in a pure PHP file it is better to omit it.

### PHP beyond the web

Bottom line: we can run PHP from the command line, so PHP isn't necessarily web-bound. A PHP script could make an FTP call and download a file from a server, copy files from one folder to another, create folders in the file system, connect to a database, call an API — anything, without any HTML involved. And of course PHP can also run behind a web server, like the built-in one we just used, to serve web pages. PHP is, to all intents and purposes, a multipurpose language.

## Expressions and literals

Now that we know how to write and execute a PHP file, let's see how PHP handles the data we give it. This will serve as an introduction to the variables and constants of the next chapter: we will understand *why* we need them.

Let's create a new folder — I'll call it `variabili` — with a new `index.php` inside. A **literal expression** is an expression that we write as it is, as in mathematics. For example:

```php
2 + 2;
```

Full source: [listing-16.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-16.php)


Remember the semicolon: with that, this is a correct PHP statement. Let's run the file from the terminal — there's nothing "web" here, no HTML tags, so the command line is perfect for checking if the file works. If you have added PHP to the system PATH, any version of PHP will do for this basic part:

```bash
php variabili/index.php
```

Full source: [listing-17.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-17.sh)


```text
2 + 2;
```

Full source: [listing-18.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-18.txt)


Surprise: we literally see `2 + 2`. What's happening? PHP, not finding an opening tag inside the file — even if the file is called `index.php` — treats everything outside the tags as text: it returns it *as is*, as it is, without interpreting it.

### The standard output is fwrite

The place where the terminal displays the results is called **standard output** in programming. PHP provides a constant - we will see later what constants are - called `STDOUT`, which represents the standard output: in this case, our console. Warning: `STDOUT` exists only when PHP is run from the command line, not when running behind a web server.
To write to the standard output we can use the function `fwrite()`, which means "write" (*write*): it is a function designed to write to a file, and the standard output behaves exactly like a file to which we send data — `STDOUT` is in fact a file-type **resource**, a "channel" already open for us. We will study these functions later; For now we only need it for the experiment:

```php
<?php
fwrite(STDOUT, 2 + 2);
```

Full source: [listing-19.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-19.php)


Note that this time we opened the `<?php` tag: without it, as we have just seen, PHP would not interpret anything. We relaunch:

```text
4
```

Full source: [listing-20.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-20.txt)


Here's number 4: this time PHP *evaluated* the expression `2 + 2` and wrote the result to standard output. Instead of the number we could write a string — we will see them in detail later; for now know that a **string** is written between single quotes or double quotes:

```php
<?php
fwrite(STDOUT, 'John');
```

Full source: [listing-21.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-21.php)


And let's see the name in console. But let's try serving the same file with the integrated web server:

```bash
php -S localhost:3000 -t variabili
```

Full source: [listing-22.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-22.sh)


Opening `http://localhost:3000` results in an error: the constant `STDOUT` is not defined. As we said, it only exists when PHP is run from the command line.

### The echo construct

To send output to both the browser and the console, the right choice is the `echo` construct that we have already encountered: it "exits" any result to the current output, wherever PHP is running. We comment the line with `fwrite()` using `//` and try:

```php
<?php
// fwrite(STDOUT, 'John');
2 + 2;
echo 'Hello World';
```

Full source: [listing-23.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-23.php)


```text
Hello World
```

Full source: [listing-24.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-24.txt)


It works both from the terminal and from the browser. But notice something interesting: the line `2 + 2;` produces nothing. PHP evaluates it — the expression is actually executed — but nothing happens to the result: it doesn't end up in the output and isn't put into an area of ​​memory that we could reuse. If we want to see it, we need to pass it to `echo`:

```php
<?php
echo 2 + 2;
echo 'Hello World';
```

Full source: [listing-25.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-25.php)


```text
4Hello World
```

Full source: [listing-26.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-26.txt)


The 4 is there, but the string appears attached to it immediately after: there is no new line. We'll see why when we talk about strings; for now it is enough to know that in a string between double quotes the sequence `\n` (backslash + n) represents the new line character:

```php
<?php
echo 2 + 2;
echo "\n";
echo 'Hello World';
```

Full source: [listing-27.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-27.php)


```text
4
Hello World
```

Full source: [listing-28.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-28.txt)


### Why do we need variables

So: if we don't use `echo`, we don't see the result of an expression. But there's more. Suppose I want to *keep* the result of that operation to send by email or save to a database: I couldn't. Once the line has been executed, that result no longer exists.

And that's where **variables** come into play, allowing us to store these results: a string, a number, a record read from the database — any type of value supported by PHP can end up in a variable. In PHP the name of a variable must be preceded by the dollar sign `$` (we will see why in the next chapter): this is how PHP understands that it is a variable.

```php
<?php
$result = 2 + 2;
echo $result;
```

Full source: [listing-29.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-29.php)


```text
4
```

Full source: [listing-30.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-30.txt)


Pay attention to the meaning of the `=` sign: we are not saying that something "is equal to" two plus two, as in mathematics. In programming, and therefore in PHP, the equal sign is an **assignment**: "execute the operation on the right and assign the result to the variable on the left". And when we use the variable, the dollar is required: if we wrote `echo result;` PHP would think that `result` is a constant.

The same goes for strings. If I write my name in quotes, alone on one line:

```php
<?php
'John';
```

Full source: [listing-31.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-31.php)


I run the code and I don't see anything: I have to make it `echo`, or put it in a variable to be able to store it:

```php
<?php
$name = 'John';
```

Full source: [listing-32.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-32.php)


From now on with `$name` I can do what I want: send it by email, write it to the file system. For example, with a function that we will study later — I'll only show it to you as a preview, don't worry — I can tell it what the file should be called and what content to write in it:

```php
<?php
$name = 'John';
file_put_contents('text.txt', $name);
```

Full source: [listing-33.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/en/parte-02/cap-06/listing-33.php)


We run the code and, looking in the folder, PHP has created the file `text.txt` with the value of our variable inside. We will see all the functions for writing to files in due course (in Chapter 15): here I just wanted to show you the importance of variables.
In the next chapter we will see how to declare a variable, the naming conventions and the different data types: the strings we have already glimpsed, numbers, Booleans, arrays, up to classes and objects.

## In summary

- The PHP code lives between the opening tag `<?php` and the eventual closing tag `?>`: everything that is outside is returned as it is. In a pure PHP file the closing tag should be omitted.
- Each **statement** ends with a semicolon; the semicolon closes the statement, not the line.
- `phpinfo()` shows version, configuration (`php.ini`) and extensions of the PHP installation: also useful for inspecting a hosting.
- A PHP script is executed from the terminal with `php filename.php` or via web server: with the VS Code PHP Server extension or with the integrated server `php -S localhost:port -t folder`. PHP adapts the output to the context in which it runs.
- Comments are written with `//` (single line) or `/* ... */` (block).
- `echo` writes output wherever PHP is running; `STDOUT` and `fwrite()` only work from the command line.
- PHP evaluates expressions like `2 + 2`, but without `echo` the result is not seen and without a variable it is lost: `$result = 2 + 2;` is an **assignment**, which calculates the right part and stores it in the variable on the left.
- PHP is not just web: from the command line you can copy files, connect to databases, call APIs — it is a multipurpose language.
