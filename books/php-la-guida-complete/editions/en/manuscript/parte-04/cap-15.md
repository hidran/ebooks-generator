# 15. The file system, include and require

In this chapter we learn how to make PHP communicate with the **file system**: create a file and write to it, read its contents, add text to the queue, check if a file or folder exists, delete and copy files, and explore the contents of a directory in three different ways. These are operations that every real application must do sooner or later: generate a log, save a document, read a configuration file, clean up temporary files.

In the second part of the chapter we address four fundamental constructs of the language: `include`, `require`, `include_once` and `require_once`. They are the tool with which PHP allows you to break a project into multiple reusable files - common functions, templates, configurations - and they are the basis of everything we will build in the practical projects of the next chapters. Finally, we will see a little-known but very valuable feature: an included file can **return a value**, which we can capture in a variable.

## Create a file and write to it

Let's start from a simple scenario: we have an already existing `docs` folder, which is located in the same directory as the PHP script we are about to execute, and we want to create a `myfile.txt` file inside it. We created the folder in this example by hand, but later we will see that folders can also be created from PHP (with the `mkdir()` function, which I invite you to look for in the manual).

We define two variables: `$dir`, which points to the folder, and `$fileName`, with the complete path of the file to create:

```php
<?php

$dir = 'docs';
$fileName = $dir . '/myfile.txt';
```

Full source: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-01.php)


There are several ways to write a file in PHP. Let's start with the most classic and flexible one: the **`fopen()`** function.

### Opening a file: fopen and opening modes

`fopen()` opens a file and returns a **handle**, that is, a resource through which we can act on the file: write to it, read it, move within it. The function takes two arguments: the name (path) of the file to open and the opening **mode**, which tells PHP what we intend to do with it:

```php
$hd = fopen($fileName, 'w');
```

Full source: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-02.php)


The `'w'` mode stands for *write*: opens the file for writing only. If the file exists, it **truncates** it, that is, it resets everything inside; if it does not exist, it creates it. That's exactly what we need to create `myfile.txt` from scratch.

The first thing to do, immediately afterwards, is to verify that the opening was successful, checking that the handle is valid:

```php
if ($hd) {
    fwrite($hd, 'First write to file');
} else {
    echo 'Unable to create the file';
}
```

Full source: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-03.php)


If we end up in the `else` branch, there are two typical causes: the path we indicated does not exist, or PHP does not have **write permissions** on that folder. This second point deserves attention: when you write a PHP script that must write to disk, you must ensure that the process running PHP — on Linux typically Apache with PHP as a module, or PHP-FPM — has write rights to the destination folder. On Windows the same principle applies: check which user PHP was launched as and that that user has access to the file.

### Write with fwrite and close with fclose

As you have seen in the code above, to write to the file we use **`fwrite()`**: we pass it the handle (in our case `$hd`) and the string to write. Let's run the script and check the `docs` folder: the file `myfile.txt` has appeared and, upon opening it, we find the text "First write to file". We managed to create the file and write in it.

When we have finished working on a file we must **close** it with `fclose()`, passing it the handle:

```php
fclose($hd);
```

Full source: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-04.php)


Always remember to close the files: if another script is waiting to access that file, closing it frees it.

### Read the file: fread and filesize

Now that we have written to the file, let's try to read it. The turn is the same: we open the file with `fopen()`, but this time in `'r'` (*read*) mode, which opens in read-only mode and places the cursor at the beginning of the file:

```php
$hd = fopen($fileName, 'r');
```

Full source: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-05.php)


A note: if the file was binary (an image, a PDF) and we wanted to read it in a *binary safe* way, i.e. with the guarantee that the bytes are read correctly, we should add the letter `b` to the mode (`'rb'`). For a text file like ours, `'r'` alone is enough.

To read we use the **`fread()`** function: we pass it the handle and the number of bytes we want to read. We can indicate any quantity, but if the reading reaches the end of the file it stops there. So, if we want to read the **complete** file, how do we know how many bytes to ask for? The function **`filesize()`** helps us, which receives the path of the file and returns its exact size in bytes:

```php
$content = fread($hd, filesize($fileName));
echo $content;
```

Full source: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-06.php)


Reloading the page we see "First writing to file" on the screen: we managed to read what we had written. Note that `fread()` works on the handle, while `filesize()` wants the file path: they are two different things.

### Read in blocks: feof and rewind

What if we don't want to (or can't) use `filesize()`? In that case we would have to read the file one piece at a time, concatenating the blocks into a variable, until the file is finished. Two important concepts come into play here.

The first is the **cursor**: when we read a file, PHP maintains a current position that advances with each read. In our script we just read the whole file, so the cursor is at the end. If we reread it now, we would get nothing. The **`rewind()`** function, to which we pass the handle, returns the cursor to the beginning of the file — like "rewinding the tape":

```php
rewind($hd);
```

Full source: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-07.php)


The second is the **`feof()`** (*end of file*) function: it receives the handle and tells us if the cursor has reached the end of the file. Combining it with an `while` loop we can read the file in blocks:

```php
rewind($hd);

$content = '';
while (!feof($hd)) {
    $content .= fread($hd, 1024); // read 1 kilobyte at a time
}
fclose($hd);

echo $content;
```

Full source: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-08.php)


Pay attention to the loop logic: `feof($hd)` returns `true` when we are at the end of the file, but we want to continue reading **until** we are at the end — so the condition is negated with `!`. At each turn we concatenate the read block to `$content` (here 1024 bytes, i.e. one kilobyte, but the quantity is of our choice); as soon as `feof()` returns `true`, we exit the loop and do the `echo` of the content. The result is identical to reading "one shot" with `filesize()`: only the strategy changes.

### Add content to the queue: the a mode

There is only one line in the file so far. Let's now try to write **at the end** of the file, without deleting what is already there. The procedure is always the same, but we use another opening mode: `'a'`, which stands for *append*. If the file exists, it opens it and places the writing in the queue; if it doesn't exist, it creates it:

```php
$hd = fopen($fileName, 'a');
fwrite($hd, 'Second write to file');
fclose($hd);
```

Full source: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-09.php)


Rereading the file, however, we discover a detail: the two sentences are attached on the same line, "First writing to fileSecond writing to file". To wrap, we need the **new line** character `"\n"` which, as we saw in Chapter 11 on strings, must be between **double quotes**, otherwise it is not interpreted (on Windows the sequence `"\r\n"` is used, new line plus *carriage return*). The right place to put it is at the end of the first write, concatenating it to the string:

```php
fwrite($hd, 'First write to file' . "\n");
```

Full source: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-10.php)


Now the output is what we wanted, one line below the other:

```text
First write to file
Second write to file
```

Full source: [listing-11.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-11.txt)


To recap the complete tour: we opened the file in `'w'` to create it and write the first line, we closed it, we reopened it in `'a'` to append the second line, we closed it again and finally we opened it in `'r'` to read it.

### The opening methods in summary

Always keep the PHP manual at hand: by searching `fopen` (even simply "php fopen" in a search engine) you will find the complete list of modes. The main ones:
| Mode | Meaning |
|---|---|
| `r` | read-only, cursor at the beginning of the file |
| `r+` | reading and writing, cursor at the beginning |
| `w` | write only: truncate the file if it exists, create it if it does not exist |
| `w+` | like `w`, but also reading |
| `a` | queue write only (append); create file if it does not exist |
| `a+` | read and write queued |
| `b` | flag to add for reading/writing binary safe |

There are also other modes (`x`, `x+`, `c`…) that you can learn more about in the manual, but the most used are `r`, `w` and `a`. There's no need to memorize them: as you use these functions they will stick in your mind on their own.

## Read and write with just one function

The `fopen()` → `fwrite()`/`fread()` → `fclose()` loop is powerful, but when we only need to read or write a file there is a much more convenient way: PHP offers two functions that do everything in one line.

### file_put_contents and file_get_contents

The first is **`file_put_contents()`**: "put this content into this file". Receives the file name and content to write:

```php
<?php

$dir = 'docs';
$fileName = $dir . '/myfile2.txt';

file_put_contents($fileName, 'First content');
```

Full source: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-12.php)


Let's save, reload the page and check the folder `docs`: the file `myfile2.txt` has been created and contains "First content". A single line instead of opening, writing and closing.

Let's now try to write a second piece of content:

```php
file_put_contents($fileName, "\n" . 'Second content');
```

Full source: [listing-13.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-13.php)


We check... and in the file there is only "Second content": the first one has disappeared. Why? Because `file_put_contents()` **truncates the file**: if it doesn't exist it creates it, if it exists it resets it and then writes, exactly like a `fwrite()` on a file opened in `'w'` mode. Be very careful with this behavior, because it is easy to lose data without realizing it.

How can we preserve existing content? Reading it before writing. Two other functions come into play here. The first is **`file_exists()`**, which checks whether a file exists on the file system. The second is the twin of `file_put_contents()`: **`file_get_contents()`**, which reads all the contents of a file and returns it as a string. Let's combine them:

```php
$content = '';

if (file_exists($fileName)) {
    $content = file_get_contents($fileName);
}

file_put_contents($fileName, $content . "\n" . 'Second content');
```

Full source: [listing-14.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-14.php)


We initialize `$content` to an empty string; if the file exists, we load its contents into it; finally we write the old content concatenated to the new line. Now the script no longer truncates anything: every time you reload the page in the browser, a new "Second contents" line is added to the file — each request to the server runs the script again and appends another line. With these two functions, `file_get_contents()` and `file_put_contents()`, we can read and write files with minimal effort.

### Relative paths, absolute paths and permissions

An important observation about the routes. When we pass these functions a **relative** directory (like our `docs`), PHP searches for it relative to the folder where the running `.php` file is located. Alternatively we can always pass an **absolute path**. And what was said for writing applies: PHP must have **read** permission on that file or directory, otherwise `file_exists()` would return `false` even if the file is there — not because the file is missing, but because PHP doesn't have the right to see it.

### Check a folder: is_dir

In addition to checking whether a file exists, we can check whether a path is a **directory** with the **`is_dir()`** function:

```php
if (is_dir($dir)) {
    echo 'The directory exists';
}
```

Full source: [listing-15.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-15.php)


By running the script on our `docs` folder we get confirmation. We'll see shortly how useful this feature is when exploring the contents of a folder.

### Delete, copy and other file system functions

Another very frequent use case: you have created a temporary file - perhaps to generate a PDF - and at the end of the work you want to delete it. Just call **`unlink()`** with the file name:

```php
unlink($fileName);
```

Full source: [listing-16.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-16.php)


Let's reload the page and check: `myfile2.txt` no longer exists, neither in the editor nor in the `docs` folder. Pay attention to the order of the instructions: if in the same script you first write with `file_put_contents()` and then delete with `unlink()`, at each execution the file is recreated and immediately destroyed; put the `unlink()` where it is really needed in the logic of your program.

The file system functions chapter of the PHP manual is very rich: there are dozens of functions for reading, writing and querying file properties. Here I have shown you the ones that are used most often, but it is worth mentioning others:

- **`copy()`** — copies a file from a source to a destination;
- **`file()`** — reads the entire file inside an array, one line per element;
- **`fileatime()`** — returns the date of the last access to the file;
- **`touch()`** — changes the access date of a file, like the Linux command of the same name;
- **`is_writable()`** — tests whether a file is writable.

I'll give you an exercise: next to the `docs` folder, create another one, for example `copia`; create a file inside `docs` and then copy it to the new folder using `copy()`. Try these functions firsthand: only by practicing will you retain what you have learned.

## Read the contents of a folder

Now that we know how to work on individual files, let's see how to read the contents of a **folder**: list the files inside, distinguish files from subdirectories and obtain information on each element. PHP offers us three paths.

### scandir: the folder as an array

The first, very convenient and fast, available from PHP 5, is the **`scandir()`** function: we pass it the name of the directory to be examined and it returns an array with all the entries it contains:

```php
<?php

$dir = 'docs';

$d = scandir($dir);
var_dump($d);
```

Full source: [listing-17.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-17.php)


The `var_dump()` shows something like this (in our `docs` there are three files):

```text
array(5) {
  [0]=> string(1) "."
  [1]=> string(2) ".."
  [2]=> string(10) "myfile.txt"
  [3]=> string(9) "test.html"
  [4]=> string(8) "test.txt"
}
```

Full source: [listing-18.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-18.txt)


Note the first two entries: the dot `.` represents the current folder and the two dots `..` the *parent* folder, i.e. the superior one. They are present in every directory and generally should be skipped when we iterate the contents.

With an `foreach` loop we can scroll through the entries and, for each one, check whether it is a directory or a file with the `is_dir()` and `is_file()` functions:

```php
foreach ($d as $entry) {
    // skip the current and parent folders
    if ($entry == '.' || $entry == '..') {
        continue;
    }

    echo $entry;
    var_dump(is_dir($dir . '/' . $entry));
    var_dump(is_file($dir . '/' . $entry));
    echo '<br>';
}
```

Full source: [listing-19.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-19.php)


There is a detail that is initially misleading: if we passed to `is_dir()` and `is_file()` only `$entry` (for example `myfile.txt`), we would get `false` for everything. Why? Because these functions resolve the path relative to the folder of the running script, not relative to `docs`: we therefore need to concatenate the folder path, `$dir . '/' . $entry`, to give them the right path. Once the correction is made, the output tells us for each entry whether it is a directory (`bool(true)`/`bool(false)`) and whether it is a file. With this verification you can build richer logic: if the entry is a folder, for example, you can recursively call the same function to explore it; if it is a file, read or process it.

### opendir and readdir: the handle approach

The second way is the most "historical" and follows what we saw with `fopen()`: the function **`opendir()`** receives the directory and returns a **handle**, i.e. a resource:

```php
$handle = opendir($dir);
var_dump($handle);
```

Full source: [listing-20.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-20.php)


The `var_dump()` confirms that it is indeed the **resource** type, one of the data types we encountered in Chapter 7: PHP shows us the resource identifier and, by inspecting it, the path `docs`. From this handle we can read the folder entries one at a time with **`readdir()`**, which returns the current entry and advances the cursor, or `false` when the entries are finished:

```php
while (($entry = readdir($handle)) !== false) {
    echo $entry, '<br>';
}
closedir($handle);
```

Full source: [listing-21.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-21.php)


The result is the same as obtained with `scandir()` — dot, two dots and the files — but here, instead of receiving everything in an array, we scroll through the folder using a cursor, exactly as we did with the files. Again, when we are finished we close the resource (`closedir()`).

### DirectoryIterator: the object approach
The third way is in my opinion the most convenient, and it is the one I always use in my scripts: the **`DirectoryIterator`** class, which is part of the **SPL** (Standard PHP Library), the standard library included in PHP since version 5.

`DirectoryIterator` is a **class**. We haven't studied classes yet — we will do so in Chapter 26 — but I'll tell you the bare minimum: to create an instance of a class, use the operator `new` followed by the name of the class, passing any arguments in brackets. In our case, the directory to explore:

```php
$it = new DirectoryIterator($dir);
```

Full source: [listing-22.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-22.php)


An **iterator** is the implementation of a pattern: an object that exposes methods for advancing to the next entry, returning the current entry, rewinding to the beginning, knowing whether a valid element exists. And here's the advantage: wherever there is an iterator, we can iterate through it with a simple `foreach` loop, just like an array:

```php
foreach ($it as $entry) {
    echo $entry->getFilename() . ' - ' . $entry->getSize();
    var_dump($entry->isDir());
    var_dump($entry->isFile());
    echo '<br>';
}
```

Full source: [listing-23.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-23.php)


Each `$entry` is in turn an object that represents an entry in the folder (a file or a subdirectory) and has **already built-in** all the methods we need, without having to concatenate paths or resort to native functions as we did with `scandir()`. The syntax `$entry->metodo()` calls a method on the object; if you write `$entry->` in your editor, autocomplete shows you everything that is available:

- **`isDir()`** — is the entry a directory?
- **`isFile()`** — is the entry a file?
- **`getFilename()`** — the file name;
- **`getBasename()`** — the base name, without the folder path;
- **`getPath()`** — route information;
- **`getSize()`** — the size in bytes;
- and many others: the creation date, the owner of the file, permissions...

By executing the cycle we obtain, for each entry, the name, the size and the two `var_dump()`: the dot `.` is a directory and not a file (`bool(true)` and `bool(false)`), the same for `..`, while `myfile.txt`, `test.html` and `test.txt` are files and not directories. And at the end of each name the size appears: `test.html - 476`, `test.txt - 1`, `myfile.txt - 52` bytes.

In summary, to read a folder we have three tools: `scandir()`, which gives us an array to scroll with `foreach`; the pair `opendir()`/`readdir()`, which works with a handle and a cursor; and `DirectoryIterator`, an implementation of the iterator pattern which, upon receiving a folder, returns a list of objects already equipped with all the methods to query the name, type and size of each item. If you can choose, `DirectoryIterator` is the path I recommend: with a single instruction you have an iterator and each entry brings with it everything you need. Here too, the advice is always the same: create a test folder, put some files in it and experiment with the three techniques.

## include, require, include_once and require_once

Let's now move on to four fundamental PHP constructs: **`include`**, **`require`**, **`include_once`** and **`require_once`**. What are they for? To include the code of a file inside another file, so as not to have to repeat the same code several times: if we have functions common to the whole project, we write them only once and reuse them where they are needed.

### Reuse code with include

Let's create a file `functions.php` with a small utility function inside, `dd()`, which receives any variable, makes it the `var_dump()` and then stops the execution with `die`:

```php
<?php

function dd($data)
{
    var_dump($data);
    die;
}
```

Full source: [listing-24.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-24.php)


Now suppose we want to use this function in another file, `index.php`, where we have an array of data:

```php
<?php

$data = [1, 2, 3];

dd($data);
```

Full source: [listing-25.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-25.php)


It wouldn't make sense to copy the function into `index.php`. But if we run the script as is from the command line…

```bash
php index.php
```

Full source: [listing-26.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-26.sh)


…we get an error:

```text
PHP Fatal error:  Uncaught Error: Call to undefined function dd()
```

Full source: [listing-27.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-27.txt)


PHP doesn't know `dd()`: the function lives in another file. This is where `include` comes in. Before calling the function, we include the file that defines it:

```php
<?php

include 'functions.php';

$data = [1, 2, 3];

dd($data);
```

Full source: [listing-28.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-28.php)


If the file was located in another folder, we would have to indicate the full path. The right way to imagine `include` is this: it's as if PHP took the code of `functions.php` and **copied and pasted** it to the exact point where the statement appears. We relaunch from the terminal: now the function exists, it is executed and we see the `var_dump()` of the array.

### include_once: include once

What happens if we include the same file **twice**? Imagine a long file, with many lines: we don't realize that the `include` is already there and we rewrite it:

```php
include 'functions.php';
include 'functions.php'; // by mistake, later in the file
```

Full source: [listing-29.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-29.php)


Try to imagine the outcome before reading further. If you thought that there will be an error because the function is already defined, you thought well:

```text
PHP Fatal error:  Cannot redeclare dd() (previously declared in functions.php:5)
```

Full source: [listing-30.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-30.txt)


The "copy and paste" logic explains everything: at the second inclusion PHP pastes the code again and therefore **redeclares** the function `dd()`, which is prohibited. For this reason, when we include files that define functions (or classes, as we will see later), it is best to use **`include_once`**:

```php
include_once 'functions.php';
include_once 'functions.php'; // no problem
```

Full source: [listing-31.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-31.php)


As the name implies, "*once*" means "once": if the file has already been included, PHP does not include it again. Rerunning the script there is no error. It is a valuable protection especially in large projects, where we cannot know if another piece of code has already included the same file.

### include or require?

And `require`? The difference between `include` and `require` is how they react when the file to include **does not exist** (or the path is wrong). Let's test it: instead of the `dd()` function we put an `print_r()` which does not stop the execution, and we purposely get the file name wrong:

```php
<?php

include 'functions2.php'; // this file does not exist

print_r($data);
```

Full source: [listing-32.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-32.php)


Running the script, the first thing PHP tells us is a **warning**:

```text
PHP Warning:  include(functions2.php): Failed to open stream:
No such file or directory
```

Full source: [listing-33.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-33.txt)


But it's just a warning: **the code continues execution** and the `print_r()` is executed regularly. (If instead after the failed `include` we called `dd()`, we would still have the fatal error "Call to undefined function", because the function was never loaded.)

Now let's replace `include` with `require`:

```php
require 'functions2.php';

print_r($data); // this line is never reached
```

Full source: [listing-34.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-34.php)


With `require` we are telling PHP that that file is **required*: if it isn't there, the program must stop. And in fact the warning is followed by a **fatal error**:

```text
PHP Fatal error:  Failed opening required 'functions2.php'
```

Full source: [listing-35.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-35.txt)


The execution stops there: the following lines are never reached, because the script already fails at the `require` line.

Which one to use, then? You have to evaluate it yourself, based on the specifications of your code. If the included file is an **essential** part of the application — without which there is no point in continuing — use `require`: better stop now. However, if it's a piece of code that the application can do without — maybe someone removed the file, but the rest can continue running — use `include`, so a missing file doesn't block everything. And of course you can always check the file's existence first with `file_exists()`, as we learned in this same chapter.

There is also **`require_once`**, which combines the two characteristics: mandatory file (fatal error if missing) and inclusion only once. If we write `require_once 'functions.php'` twice, the file is included only once and there are no problems:

```php
require_once 'functions.php';
require_once 'functions.php'; // ignored: already included

dd($data);
```

Full source: [listing-36.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-36.php)


The suffix `_once`, therefore, is valid for both `include` and `require`; the difference between the two families always remains the same: with `include` the code does not stop if the file is missing, with `require` yes.

### A template inside a loop: when _once is bad

At this point you might say: then we always use the `_once` versions and don't worry. A moment of attention: for files that define functions (and later classes) this is fine, but there is a use case in which `_once` is really wrong: the **templates** included inside a loop.

Let's see it with an example. Let's create a file `show_data.php` which must show a list of cities:

```php
<?php

$cities = ['Edinburgh', 'London', 'Manchester'];

echo '<ul>';
foreach ($cities as $data) {
    include 'li.php';
}
echo '</ul>';
```

Full source: [listing-37.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-37.php)


And we create the template `li.php`: a reusable fragment that prints an element of the list. We use the short opening tag `<?=`, which means "open PHP and immediately do the `echo` of what follows", and assume that a variable `$data` exists:

```php
<li class="data"><?= $data ?? '' ?></li>
```

Full source: [listing-38.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-38.php)


The operator `??` (*null coalescing*, available since PHP 7) acts as a safety net here: if `$data` was not passed, we print an empty string instead of generating an error.

How does the whole thing work? At each turn of the `foreach`, the variable `$data` contains a city and the `include` "paste" the template at that point: it is as if we had closed PHP, pasted the HTML of the template and reopened PHP, once for each city. Let's launch from the command line:

```bash
php show_data.php
```

Full source: [listing-39.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-39.sh)


And let's see the list with the three cities. If you prefer to view it in the browser, you can start the integrated PHP web server on a port of your choice:

```bash
php -S localhost:3000
```

Full source: [listing-40.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-40.sh)


and open `http://localhost:3000/show_data.php`: here is our rendered list.

Now the counterproof: let's replace `include` with `include_once` inside the loop. What will it print? **Rome** only: the template is included on the first round and then never again, because `_once` really means "once only". Here is the case where we **cannot** use `include_once`: we want to reuse the template as many times as there is data to show. In templates inside a loop `include` is used (or `require`, if we want the absence of the file to block everything: the logic is identical, only the reaction to the missing file changes).

### Constructs, not functions

One final syntax note. In some older code you may encounter this form, with parentheses:

```php
include('functions.php');
```

Full source: [listing-41.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-41.php)


It works, but the brackets are useless. `include` and `require` are not functions: they are **language constructs**, like `echo`. This is why the idiomatic form, the one I recommend you always use, is without brackets:

```php
include 'functions.php';
require 'config.php';
```

Full source: [listing-42.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-42.php)


### Tip: Don't close the PHP tag

If a file contains **PHP code only** — like ours `functions.php` — don't close the `?>` tag at the end. It's not necessary, and there's a good reason to omit it: if there are spaces or blank lines left after the `?>`, when you include that file inside an HTML page those spaces end up in the output and can create problems that are difficult to diagnose. The rule is simple: pure PHP file, no closing tags.

And a warning for the future: `include` and `require` "paste" code, so if you include two files that both define a function `dd()`, you will have a function conflict with a fatal error. Later, in Chapter 30, we will see that namespaces are used to avoid these conflicts; for now, keep this in mind when organizing your files.

## Return a value from include and require

There's another feature of `include` and `require` that makes them valuable: if the included file **returns a value**, we can capture it in a variable. So far we have used them to bring in functions or to print templates; however, sometimes you need something different: think of the included file as a **data source**. The classic case is a file with database configurations, or with data that we want to have available on all pages.

### The global variable problem

Let's create a file `config.php` and put some configuration data inside an array:

```php
<?php

$config = [
    'ip'       => '127.0.0.1',
    'password' => 'test',
    'email'    => 'test@mail.test',
    'username' => 'test',
];
```

Full source: [listing-43.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-43.php)


In the main file we do the `require` and verify:

```php
<?php

require 'config.php';

var_dump($config);
```

Full source: [listing-44.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-44.php)


Loading the page we see the complete array: IP, password, email, username. This works, because the `require` has "pasted" the code and therefore the `$config` variable exists here too. But this is exactly the problem: `$config` has become a variable **injected into the scope** of the file it includes. Suppose that, later in the file, without knowing that variable exists, we write:

```php
$config = [];
```

Full source: [listing-45.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-45.php)


We just overwrote the entire configuration: the `var_dump()` now shows an empty array. In a large project, this type of variable collision is a sneaky source of bugs. What do we do if we **don't** want to inject global variables into other files when we do an `require`?

### return inside the included file

The solution: instead of defining a variable, the configuration file **returns** the value directly with `return`:

```php
<?php

return [
    'ip'       => '127.0.0.1',
    'password' => 'test',
    'email'    => 'test@mail.test',
    'username' => 'test',
];
```

Full source: [listing-46.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-46.php)


We can return anything: an array, a string, an object. Now in the main file, if we just do `require 'config.php'` and then `var_dump($config)`, PHP tells us that `$config` is *undefined*: the variable no longer exists, and the returned value has been lost. The key point is that **`require` and `include` are expressions that return a value**, and we can assign that value to one of our variables:

```php
<?php

$config = require 'config.php';

var_dump($config);
```

Full source: [listing-47.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-15/en/parte-04/cap-15/listing-47.php)


Let's reload: we've captured the return and the array is all there again. Note that the variable name is completely free — `$config`, `$conf`, whatever you want — and we could also pass the result directly to a function. The advantage is cleanliness: whoever does the `require` of `config.php` receives the data **only if explicitly captures it**; there are no global variables contaminating the scope of the file it includes. If you don't capture the return, that data simply doesn't exist in your scope.

Two details to complete the picture:

- **The default return value.** If the included file does not contain any `return`, `include` and `require` return `1` when the include succeeds. If the file does not exist, the "value" is `false`, accompanied - as we know - by a warning with `include` or by a fatal error with `require`.
- **The file is still executed line by line.** If we put an `echo 'test';` before the `return` in `config.php`, that text is printed regularly, and then the array is returned: the `return` concludes the execution of the included file and returns its value.

Everything we have said applies equally to `include`, `require`, and to the variants `_once`: the choice between them follows the same rules seen in the previous paragraph (obligatory file and single inclusion); the ability to return a value is common to all. This pattern — a configuration file that returns an array, captured with `$config = require 'config.php'` — you will find in the practical projects of the book, starting with the database configuration.

## In summary
- `fopen()` opens a file and returns a **handle**; the main modes are `r` (read), `w` (write with truncation, create file if missing) and `a` (append to queue). It is written with `fwrite()`, it is read with `fread()` and it always ends with `fclose()`.
- `filesize()` gives the size of a file in bytes; `feof()` tells if the cursor is at the end; `rewind()` takes it back to the beginning. The new line `"\n"` (on Windows `"\r\n"`) goes in double quotes.
- `file_put_contents()` and `file_get_contents()` write and read a file in a single line; warning: `file_put_contents()` **truncate** the existing file.
- `file_exists()` checks for the existence of a file, `is_dir()` if a path is a directory, `unlink()` deletes a file, `copy()` copies it. Relative paths resolve to the script folder; PHP must have the necessary read/write permissions.
- To read a folder: `scandir()` (array of entries, with `.` and `..` to skip), `opendir()`/`readdir()` (handle and cursor) and `DirectoryIterator` (SPL), the most convenient: each entry is an object with methods like `isDir()`, `isFile()`, `getFilename()`, `getSize()`.
- `include` embed a file as a "copy and paste"; `require` does the same but generates a **fatal error** if the file is missing (with `include` only a warning and the code continues). The variants `include_once`/`require_once` include the file only once: ideal for functions and classes, to be avoided for templates inside a loop.
- `include` and `require` are **language constructs**, not functions: they are used without brackets. In pure PHP files, do not close the `?>` tag.
- An included file can **return a value** with `return`, captureable with `$config = require 'config.php'`: it's the clean way to load configurations without polluting the scope with global variables. Without `return`, successful inclusion returns `1`.
