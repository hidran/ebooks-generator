# 2. Install PHP on Windows with Laragon

In this chapter we prepare a complete PHP development environment on Windows using **Laragon**: we will install the Apache web server, PHP and MySQL/MariaDB in one go, we will write and run our first PHP file both from the command line and in the browser, we will configure Visual Studio Code and Git Bash and we will learn to manage multiple versions of PHP and the database on the same machine. In the end you will have a workstation that is essentially identical to the one I use every day to develop.

Why Laragon? Because it is a **portable** environment: everything installed lives inside a single folder, without touching the Windows system registers. If one day you no longer want to use it, just delete that folder. And above all it makes two operations trivial that are tedious with other tools: changing the PHP version and creating local **virtual hosts** for your projects.

## Install Laragon

Laragon is a development environment for Windows that includes everything we need: in the **full** version we find Apache 2.4, MySQL, memcached, log management, npm and Git, all installed in a single folder. I advise you to download the full version: npm and Node can be used for the frontend and also for developing in the backend, and having everything ready immediately costs nothing.

### Download and install

Go to the Laragon website, click on **Download** and download *Laragon Full*. Once the executable is downloaded, double-click and agree to install the application. The wizard asks you a few things:

1. **The language.** You can leave the default English or choose Italian.
2. **The installation folder.** For example `C:\laragon`; any folder where your user has write permission is fine.
3. **Automatic startup.** You can start Laragon when Windows starts: convenient if you will use it often, otherwise deselect the option and launch it manually.
4. **Automatic virtual hosts.** Leave the option that creates virtual hosts for our sites active: it is one of the most useful functions of Laragon and we will see it shortly.
5. **The context menu items.** You can add the items to open a text file with Notepad and to open the terminal in a folder to the right Windows button. Leave everything selected.

Click **Next** and then **Install**, wait a few seconds and the installation is complete.

### Start the services

Search for Laragon in the Start menu and start it (or, if you have chosen automatic start, you will find it already active: click on the little arrow in the notification area next to the clock and you will see its icon). In the main window click **Start All**: Laragon starts all services, and in particular Apache on port 80 and MySQL.

Warning: if port 80 is already occupied by another system, Apache will not start. The typical case is to have **XAMPP** already installed: in this case open the XAMPP control panel and stop Apache and MySQL before starting Laragon (or continue with XAMPP, but this chapter is dedicated to Laragon). Alternatively you can change the ports from the preferences, as we will see immediately.

### Preferences

Clicking on the gear icon opens Laragon preferences. It's worth reviewing them:
- **Startup.** You can decide whether to launch Laragon when Windows starts, whether to start it minimized and whether to start services automatically.
- **Language.** From here you can change the interface language.
- **Document Root.** It is the root folder where we will put our projects, by default `C:\laragon\www`. If you have old projects in XAMPP, just copy the folders from `htdocs` into `www`. If you prefer to keep the projects elsewhere (for example in `D:\projects`), you can change the document root here: from that moment the web server will serve the sites from that folder.
- **Data directory.** This is the folder where data ends up, for example MySQL database files.
- **Automatic virtual hosts.** When we create an application in a subfolder of `www`, we will be able to access it from the browser with `folder-name.test`: Laragon automatically adds the name to the Windows `hosts` file and creates the virtual host in Apache.
- **Services & Ports.** From here you change the ports of the services: if port 80 is busy you can use for example 8000 or 4000. You can enable SSL, and see or modify the nginx, Redis and memcached ports if you use them. In this book we will mainly use Apache and MySQL.
- **Mail catcher.** When we use the PHP `mail()` function without having a configured SMTP server, Laragon captures the sending and shows a window with the contents of the email: no real email is sent, but we can verify that the code works. There is also a *Mail sender* section where you can set up a real SMTP account, for example the Gmail one: I tried it and it didn't work; if you want to try, go ahead, but in Chapter 38 we will see how to send emails reliably using dedicated services.

### The PHP version and extensions

From the Laragon menu (right click on the icon in the notification area, or the **Menu** button in the window) you will find the **PHP** item. Here you see the active version — at the time of writing Laragon includes for example 8.1.10 — and later in this chapter we will see how to install another one: just copy the new version folder into `bin\php` of Laragon and select it from this same menu.

Also from the PHP menu you can activate **Xdebug**, the PHP debugger, via the quick installation item. For most of this book we won't need them, but when you want to do real debugging you'll find the starting point here.

In the **Extensions** sub-item you will find the PHP extensions that we can enable or disable: for example `mbstring` and `pdo_mysql`, which we will use in the projects, `gd` to manage images and `fileinfo` to have information on the files, already selected by default. If you need an extra extension, for example `opcache`, just tick it here.

### Laragon Terminal (Cmder)

One last important thing: Laragon includes a terminal, **Cmder**, which you open from the **Terminal** button. Always use this terminal when working with Laragon, for two reasons. First: it supports Linux commands (`ls`, `pwd`, and so on), the same ones used on macOS and production servers. Second: inside Cmder you automatically have access to the PHP version active in Laragon, whatever it is. With any other terminal, however, we should add PHP to the `Path` Windows environment variable — and update it every time we change versions. We'll do it anyway shortly, because it's useful, but remember the rule: if in doubt, open the Laragon terminal and you'll be sure you're using the right PHP.

Let's immediately check that everything is working. Open terminal and type:

```bash
php -v
```

Full source: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/en/parte-01/cap-02/listing-01.sh)


```text
PHP 8.1.10 (cli) (built: ...)
```

Full source: [listing-02.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/en/parte-01/cap-02/listing-02.txt)


PHP responds with its version: the environment is ready.

## The first PHP file

Now that the environment is installed, let's write the first PHP file and learn the two basic ways to run it: from the command line and through the web server.

### Create the folder and file

In the Laragon window click on the **Root** button: the root folder `www` that we have prepared for our sites opens, where you already find a default `index.php` file. Create a new folder in here and name it `test`.
Enter the folder `test`, right click, **New → Text Document**, and rename the file to `index.php`. Pay close attention to the extension: the file must be called exactly `index.php` and not `index.php.txt`, otherwise PHP would not interpret it. The name is not random: `index.php` is the **default file** that the web server loads and executes when we visit a folder without indicating the name of a file.

Open the file with any editor (in the next paragraph we will install Visual Studio Code, which will be our editor for the entire book) and write:

```php
<?php
echo '<h1>Hello world</h1>';
?>
<h2>My name is John</h2>
```

Full source: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/en/parte-01/cap-02/listing-03.php)


Let's break down each line, because there's already a lot of substance here:

- `<?php` is the **opening tag** of PHP: it indicates to the web server that from this point onwards there is PHP code to execute. `?>` is the closing tag, and **is not mandatory** if the file contains only PHP and we don't mix it with HTML.
- Everything that is **outside** the PHP tags is sent as it is, as HTML: this is the case with our `<h2>` after the closing tag.
- `echo` is a PHP construct that displays content on the output console: if we execute the file from the command line, the output ends up in the terminal; if we run it through the web server, it ends up on the page that the browser receives. It depends on how we execute PHP.
- When we want to show a **string** — that is, a piece of text — we enclose it in quotes. And we can easily put HTML inside a string, like the `<h1>` tag in the example.
- In PHP every statement ends with a semicolon. When there is a single line before the closing tag, the semicolon can be omitted, but it is good practice to always place it.

We will study all this syntax in detail in the next chapters: for now we just need to verify that PHP works. Save the file.

### Run the file from the command line

Open the Laragon terminal (**Terminal** button, or right-click on the icon and then *Terminal*). The terminal opens in the `www` folder: let's enter the folder of our project and check what it contains:

```bash
cd test
ls -la
```

Full source: [listing-04.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/en/parte-01/cap-02/listing-04.sh)


`ls -la` is a Linux command — Cmder supports them — that lists the files in the folder: check that `index.php` is there and not `index.php.txt`. Now we execute the file passing its name to the command `php`:

```bash
php index.php
```

Full source: [listing-05.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/en/parte-01/cap-02/listing-05.sh)


```text
<h1>Hello world</h1>
<h2>My name is John</h2>
```

Full source: [listing-06.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/en/parte-01/cap-02/listing-06.txt)


The output appears directly in the console. Note that HTML tags are **not** rendered: the terminal is not a browser, so it displays the text exactly as PHP produces it.

This little test tells us something important: PHP can be used **from the command line**, like Python or Bash, but also as a **web server service**. In that second case Apache loads PHP as a module, executes the code and sends the PHP output to the browser.

### Run the file in the browser

Let's go back to Laragon and click on the **Web** button: the default browser opens pointing to `localhost`, i.e. the `www` folder. To enter our project we add a slash and the folder name:

```text
http://localhost/test
```

Full source: [listing-07.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/en/parte-01/cap-02/listing-07.txt)


Here is our page: "Hello world" as a large title and "My name is John" as a smaller title. It works because in the `test` folder there is the file `index.php`, which is executed by default when we do not indicate any file; in fact, even explicitly writing `http://localhost/test/index.php` we obtain the same result. If you right-click and choose *View Source*, you will see `<h1>` followed by `<h2>`: exactly the same output we saw in the terminal, only the browser renders it here.

Two practical clarifications before continuing:

- To run PHP **from the command line** the code can be in any folder on the disk: if you want to create your scripts in `D:\projects` that's fine.
- To access the folders **through the Laragon web server** (`localhost/folder-name`), the folders must instead be inside `www` — or you must change the document root in the settings, as we have seen, so that it points to the folder where you keep the sites.
And remember: the Laragon terminal always uses active PHP in Laragon. However, if you open the Windows or PowerShell command prompt and launch `php -v`, it is not guaranteed that Laragon's PHP will be found: there could be another PHP in the system `Path`, or none at all. Let's fix this right away.

## Add PHP to the Windows PATH

Adding PHP to the **Path** environment variable means being able to launch the `php` command from any terminal and from any folder, not just from Cmder.

Let's find the right folder first. If you have installed Laragon in `C:\laragon`, open the `C:\laragon\bin` folder: here you will find all the programs included — Apache, Cmder, Composer and the other software that we will add to Laragon. In the `php` subfolder there are all the installed versions of PHP. If you have more than one, check which one is active: right click on the Laragon icon, **PHP → Version**, and see the selected version. Open the folder of that version: it contains the file `php.exe`, the PHP executable. Copy the full folder path from the address bar, for example:

```text
C:\laragon\bin\php\php-8.1.10-Win32-vs16-x64
```

Full source: [listing-08.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/en/parte-01/cap-02/listing-08.txt)


Now let's add it to `Path`. On Windows 10 and 11:

1. Search for "variables" in the Start menu and open **Edit system-related environment variables**.
2. Click the **Environment Variables** button.
3. You can add the path at the user level or at the system level: select the **Path** variable (for example the user one), then **Edit**.
4. Click **New**, paste the path of the folder where `php.exe` is located and confirm with **OK** on all windows.

At this point, open any terminal — search for `cmd` and open the command prompt — and run:

```bash
php -v
```

Full source: [listing-09.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/en/parte-01/cap-02/listing-09.sh)


If it replies with the PHP version, that's it: you can launch PHP from any folder on your system. You can also run:

```bash
php -i
```

Full source: [listing-10.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/en/parte-01/cap-02/listing-10.sh)


which prints all the PHP information: scrolling through the output you see the complete configuration and what is installed.

A word of caution from experience: The version in the `Path` and the one active in the web server may differ. If you activate 8.2 in Laragon but have left the 8.1 folder in `Path`, you will continue to use 8.1 from the command prompt. Every time you change version, therefore, you either update the `Path` (removing the old path and pasting the new one) or you use the Laragon terminal, which always points to the active version.

## Visual Studio Code and Git Bash

Now that we have a web server with PHP included and a terminal with Linux commands, we need a good editor. In this book we will use **Visual Studio Code** (VS Code): it is free, lightweight and with the right extensions it becomes an excellent environment for PHP. If your company already uses NetBeans or PhpStorm, that's fine: what we will see here is an alternative. In Chapter 5 we will delve deeper into VS Code; Here we do the installation and minimal configuration to work.

### Install VS Code and extensions for PHP

Go to the Visual Studio Code website, click **Download**, download the Windows version and install. At the first start a welcome window appears: VS Code can be used for PHP, Python, C#, any language; to adapt it to PHP we need to install some extensions.

Click the **Extensions** icon in the sidebar (or press `Ctrl+Shift+X`) and search for "PHP". I recommend these extensions:

- **PHP Intelephense** — provides autocompletion of PHP code: it suggests functions, parameters and documentation as you write.
- **PHP Debug** — allows you to use Xdebug to debug code.
- **PHP Extension Pack** — a package that already includes both PHP Debug and Intelephense: by installing this you get both in one go.
- **PHP Server** — a very convenient extension that runs a PHP server without opening the terminal: just right-click on the file and choose to serve the project as a web page. It's the same thing we can do manually from the command line, as we'll see shortly.

These are the bare minimum for PHP. Then, depending on the framework you use, you can add others: for example, if you work with Laravel, search for "Laravel" and you will find extensions such as *Laravel Extra Intellisense*, *Laravel Artisan* for Artisan commands and snippets for Blade templates.
### The integrated terminal

VS Code includes a built-in terminal: open the **View → Terminal** menu (or **Terminal → New Terminal**, or the `Ctrl+`` shortcut with the backtick). By default on Windows **PowerShell** opens.

Throughout the book I will use Linux commands. Why? Why PHP is normally used on Linux: when you deploy a PHP application, even on Azure or Amazon, you will almost always select a Linux machine. It is therefore advisable to get used to the same commands straight away. For the simplest operations PowerShell is enough: if you type `pwd` it tells you which folder you are in, and `ls` lists the files, because many PowerShell commands are similar to those of Bash. But to have a true Unix-style terminal on Windows there are two ways: install **WSL** (Windows Subsystem for Linux) with an Ubuntu machine and program directly there, or — much simpler — install **Git Bash**.

A couple of useful gestures on the integrated terminal: by hovering over an open terminal you can close it by clicking on the trash can icon; with the arrow next to the `+` button choose which type of terminal to open.

### Install Git Bash

Git Bash comes with **Git for Windows**: search for "git bash" in your browser and open the official site, `git-scm.com/downloads`. There are versions for macOS, Linux and Windows: click **Download for Windows** and choose the 64-bit version (alternatively you can install it from PowerShell with `winget install`, or click directly on the "Click here to download the latest version" link).

By installing it you get two things together:

1. **A bash-type terminal**, as if we were on Linux or macOS, that is, on a Unix-based system: you can use the same commands you learn for Linux here, and you will have no difficulty executing bash commands in Windows.
2. **Git**, the version control system: you will need it to save code changes and, for example, share your projects on GitHub.

Run the downloaded file, allow the app to make changes to the system, click **Next** and then **Install**. Once finished you can immediately launch Git Bash: the console opens with the prompt ending with the symbol `$` (which indicates the bash prompt: it should not be written in the commands). Let's do two tests:

```bash
pwd
ls -l
```

Full source: [listing-11.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/en/parte-01/cap-02/listing-11.sh)


`pwd` stands for *print working directory* and tells you which folder you are in; `ls -l` (*list*) lists the files with their properties; with `cd folder-name` you enter a folder. These are the commands that we will use continuously: for a PHP programmer, knowing the main bash commands is very important.

### Git Bash as the default VS Code terminal

Now let's set Git Bash as the default terminal for VS Code. The quickest method: open the terminal, click on the arrow next to `+` and choose **Select Default Profile**; in the list that appears — there are all available terminals: PowerShell, Git Bash, and possibly Ubuntu if you have WSL — select **Git Bash**. From now on, every new terminal (and every restart of VS Code) will open directly in bash.

Alternatively you can go through the settings: from the same arrow choose *Configure Terminal Settings* and search for the terminal profile for Windows, where the path to the bash executable should be indicated, which is usually:

```text
C:\Program Files\Git\bin\bash.exe
```

Full source: [listing-12.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/en/parte-01/cap-02/listing-12.txt)


If you don't find it there, open Windows Explorer, go to `Program Files\Git`, locate the executable, and right-click → *Properties* (or *Copy as path*) to retrieve the exact path to paste. Close and reopen VS Code, open the terminal: it positions itself in Git Bash.

### A test project with VS Code

Let's put it all together with a little test. In VS Code go to **File → Open Folder** and create a folder for your projects: for example, inside *Documents*, right click → *New Folder* and name it `php`. Select it and confirm that you trust the folder (*trust*). Now create a file: click on the *New File* icon with the symbol `+` (or **File → New File**) and name it `index.php`. As we have seen, `index.php` is usually the first file created in a folder, because it is the one executed by default by the web server.

Let's write inside:

```php
<?php
phpinfo();
```

Full source: [listing-13.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/en/parte-01/cap-02/listing-13.php)


`phpinfo()` is a global PHP function that prints a page with all the installation information. Note the semicolon: every statement in PHP must be ended with `;`. And note the `<?php` tag again: PHP can be used *embedded* in an HTML page, i.e. we can mix PHP and HTML in the same file, so the only way to tell the parser where the PHP code starts is to open this tag.

Save the file and right-click in the editor area: thanks to the PHP Server extension the **PHP Server: Serve project** entry appears. Select it: the browser automatically opens on `localhost` at port 3000, with `index.php` executed. Let's see the `phpinfo()` page with the PHP version — in my case 8.3.12 — and all the configuration.

Now the same thing from the command line. Open the built-in terminal - it already opens in the project folder. We verify that PHP is in `Path` and then execute the file:

```bash
php -v
php index.php
```

Full source: [listing-14.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/en/parte-01/cap-02/listing-14.sh)


The first command shows the version (if it responds, it means we can run PHP from any folder); the second executes the file and pours all the HTML produced by `phpinfo()` into the terminal.

Let's do a clearer test with a second file. Create `test.php`:

```php
<?php
echo 2 + 2;
```

Full source: [listing-15.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/en/parte-01/cap-02/listing-15.php)


In the terminal, type `clear` to clear the screen, then:

```bash
php test.php
```

Full source: [listing-16.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/en/parte-01/cap-02/listing-16.sh)


```text
4
```

Full source: [listing-17.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/en/parte-01/cap-02/listing-17.txt)


`4` appears, because `echo` writes the output where PHP is executed: on the terminal if we launch PHP from the command line, on a web page if it passes through a web server.

And speaking of web servers: PHP has an **integrated** one, which we can launch without extensions and without Apache. The syntax is `php -S host:port`:

```bash
php -S localhost:4000 index.php
```

Full source: [listing-18.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/en/parte-01/cap-02/listing-18.sh)


`-S` indicates that we want to start a server; `localhost` is the host (we are on our computer); after the colon there is the port on which we want to serve the page, for example 4000; finally the file to serve. Do `Ctrl+click` on the URL shown in the terminal (or copy it into the browser): it works exactly like the web server of the PHP Server extension. However, be careful if you open the file directly from Explorer in the browser: it wouldn't work, because the file would only be read and not executed by PHP.

Finally, let's check the autocompletion of Intelephense. Replace the contents of `index.php` with a string test: as soon as you type `str` the list of functions that start like this appears, including `strpos()`. By selecting it, VS Code shows us the signature: the first parameter is the string to search in, the second is what we are looking for; the function returns the **position** where the substring is located.

```php
<?php
echo strpos('Imparo PHP', 'PHP');
?>
<h2>Test in PHP</h2>
```

Full source: [listing-19.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/en/parte-01/cap-02/listing-19.php)


Reload the web server page (or re-run `php index.php` in the terminal): the output is `7`. We can count: remember that **positions start at zero** — zero, one, two, three, four, five, six, seven — and in fact the documentation says so explicitly: *string position starts at 0, and not 1*. The function returns the position where what we are looking for is located, relative to the beginning of the string.

Also note the `<h2>` tag outside the PHP block: in the browser "Test in PHP" is rendered, and looking at the source of the page we see it written exactly as in the file. PHP only interprets the part enclosed in its tags: it sends the rest as it is.

### Sync your settings

One last tip about VS Code: in the preferences you can activate settings synchronization by logging in with a GitHub or Microsoft account. If you don't have a GitHub account, I recommend creating one: in addition to being used to share code, it allows you to synchronize settings and extensions, so when you use VS Code on another computer you will find the entire configured environment. VS Code offers much more — extensions for databases, for REST API calls, for Docker — and we will see them when they are needed; in the meantime, familiarize yourself with the editor: open file, save, test the settings.

## Install a new version of PHP and create virtual hosts with Apache
One of the great conveniences of Laragon is being able to keep multiple versions of PHP side by side and switch between them in one click. Let's see how to install a new version — and while we're at it, let's find out how Laragon creates Apache virtual hosts for our projects.

First, two useful tools from the Laragon menu. Under **Apache** you will find the web server configuration file and the commands to stop and restart it. Under **PHP**, in addition to the extensions we have already seen, there is quick access to the file `php.ini` with all the PHP settings: if for example you search for `display_errors` you will find it active, and rightly so — when we develop it is okay for PHP errors to be shown, because we are in development and not in production.

### Download a new version of PHP

Suppose you want to install PHP 8.2 (at the time of writing it is the most recent; if when you read there is a newer version, the procedure is identical). Go to the PHP website, `php.net`, and follow the **Windows Downloads** link: you will see the different versions available. For each there are multiple variations, and you have to choose:

- **The architecture.** Check the version of your Windows: normally it is `vs16 x64`, i.e. 64 bit.
- **Thread Safe or Non Thread Safe.** For development it makes no difference: we can take **Non Thread Safe** (NTS).

Download the zip file. In the downloads folder, right click → **Extract all** and indicate the folder to extract (if you want, you can install the **7-Zip** program, which is faster than the integrated Windows extraction, but the result is the same). Get an unzipped folder with PHP inside: copy it and paste it into the Laragon PHP versions folder:

```text
C:\laragon\bin\php\
```

Full source: [listing-20.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/en/parte-01/cap-02/listing-20.txt)


The exact same procedure applies if we wanted to install a new version of Apache or MySQL: download the zip, extract and copy the folder into the respective subfolder of `C:\laragon\bin`.

### Activate the new version

Go back to Laragon: right click on the icon → **PHP → Version** and you will also see 8.2 listed, simply because we put the folder in the right place. Select it to activate it.

How do we verify that we are really on 8.2? From the PHP menu the version is selected, but if we click on **Web** and look at the main Laragon page, the information on PHP still says 8.1. Why? Because we activated the new version, but Apache hasn't picked it up yet: we need to restart it. Right click → **Apache → Reload** (or *Restart*), then reload the page: now 8.2 appears, and by clicking on the info link we see the entire configuration of the new version.

Two important reminders when switching versions:

1. **Extensions must be reactivated.** Each version of PHP has its own `php.ini`: after the change, go back to **PHP → Extensions** and activate the extensions you need again (the default ones are already there, but everything you added must be re-enabled).
2. **The PATH must be updated.** Open the Laragon terminal and launch `php -v`: you will see 8.2, because the Laragon terminal always points to the active version. But if you open the normal Windows command prompt and launch the same `php -v`, it will still give you 8.1: it's the one that's in `Path`. To have 8.2 in any terminal, go back to the environment variables as we did the first time: search for "environment variables", open **Environment variables → Path → Edit**, remove the old PHP path and paste that of the new folder, then confirm with **OK** on all windows. Open a **new** terminal (those already open retain the old settings) and `php -v` will show 8.2.

### Apache automatic virtual hosts

Remember the `test` folder created under `www`? Laragon has already dedicated an Apache **virtual host** to it, automatically. Let's go and see it: from the menu, under **Apache**, you find the entry with sites enabled (`sites-enabled`), and there is a configuration file created for `test`. Opening it you see the `VirtualHost` directive with the **document root** pointing to `C:/laragon/www/test`, the **server name** set to `test.test`, and also the section with the certificates, if we want to connect via SSL.

What does this mean in practice? That if we open a browser tab and write:

```text
http://test.test
```

Full source: [listing-21.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/en/parte-01/cap-02/listing-21.txt)


we see our folder with the `index.php` file executed — the same thing that happens when visiting `localhost/test`, because the `test` folder is under the root of `localhost`. The advantage is being able to give our local sites a real name: the name of the folder with the extension `.test`, a fictitious domain that the browser will not search on the internet but will resolve locally. Every time we create a new folder under `www`, Laragon will automatically create the corresponding virtual host.

How does the browser know that `test.test` is local? Thanks to the Windows file `hosts`. Let's open:

```text
C:\Windows\System32\drivers\etc\hosts
```

Full source: [listing-22.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/en/parte-01/cap-02/listing-22.txt)


In this file the locally resolved names are defined: there is `127.0.0.1 localhost` — the IP 127.0.0.1 is precisely that of localhost — and Laragon has added the line for `test.test`. When we visit that name, Windows resolves it to the local IP and Apache serves us the corresponding folder.

If `test.test` doesn't work, it almost always means that Laragon doesn't have administrator rights to write into `System32` and update the `hosts` file. In that case you can do by hand what Laragon does automatically: open the file `hosts` as administrator and add the line:

```text
127.0.0.1 test.test
```

Full source: [listing-23.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/en/parte-01/cap-02/listing-23.txt)


If you want to define multiple sites on the same line, separate the names with a space. But normally there is no need: Laragon does everything himself.

## Install MySQL or MariaDB and use HeidiSQL

We close the chapter with the database. **MariaDB** is the completely open source fork of MySQL, compatible with it: for our purposes the two are interchangeable, and I'll show you how to install the latest version of one or the other. Any version of MySQL 8 and up will work for this book (we'll go into more detail about MySQL in Chapter 18).

### Install a new version of the database

Laragon already comes with a version of MySQL: from the menu, under **MySQL → Version**, you can see the one included, for example 8.0.30. At the time of registration the latest version of MySQL is 8.4, but be careful: that version **does not work with Laragon**. No problem: we install the latest MariaDB, with the exact same procedure you would use for a compatible version of MySQL.

1. Search for MariaDB in your browser and go to the **download** page of the official website.
2. Choose the version: currently 11.3.2, or in any case the stable version available when you read these pages.
3. Select Windows with `x86_64` architecture as the operating system.
4. **Do not** choose the installer as package type (the one installs MariaDB directly on the system): to use it with Laragon select the **ZIP file** and click download.
5. When the file is in the downloads folder, unpack it: with 7-Zip choose *Extract* and indicate the `C:\laragon\bin\mysql` folder as the destination (or the equivalent, if you have installed Laragon elsewhere). Alternatively, extract the zip and copy the unzipped folder into `C:\laragon\bin\mysql`.

By opening `C:\laragon\bin\mysql` you will see the different versions of MySQL or MariaDB next to each other, each with its own `bin` subfolder; Laragon also automatically creates the file `my.ini` with the default configuration.

Now let's activate the new version: menu → **MySQL** (the item will be called *MariaDB* once a MariaDB version has been selected) → **Version**, select the version just copied and then click **Start All** to start the service. If you need to change the database port, you can find it in the preferences under *Services & Ports*.

### HeidiSQL: Create a database and table

To work with the database we need a client. Laragon includes **HeidiSQL**: click the **Database** button and HeidiSQL opens with a session already configured — user `root`, no default password — then just click **Open** to connect.

Let's create our first database: right click in the left panel → **Create new → Database**. Let's give it the name `test` and as *collation* we choose `utf8mb4_general_ci`: this way we support characters from all languages. The database `test` appears in the list.

Now let's create a table: right click on the database → **Create new → Table** and call it `test_table`. With the **Add** button we add the columns one at a time:
- **`name`** — data type `VARCHAR` (double click on the type cell to select it) with length `500`. In the *Allow NULL* column we decide whether, by inserting a record, the name can remain empty: we say no, therefore `NOT NULL`.
- **`age`** — for the age we choose the right type: an `TINYINT`, which from *signed* goes from -128 to 127 and from *unsigned* goes from 0 to 255. An age is never negative, so we tick **Unsigned**; and we allow the field to remain empty, so *Allow NULL* yes.
- **`salary`** — for a salary we need a real value: we select `DECIMAL` with precision 20, of which 6 are decimals.
- **`id`** — the identifying column: type `INT`, **Unsigned** (it will be a counter, never negative), `NOT NULL`. On this column we right-click → **Create new index → ​​PRIMARY**: that is, we set it as **primary key**, which means that it uniquely identifies a record in our table. Finally, in the default value cell, we choose **AUTO_INCREMENT**: the value automatically increments with each insertion, so we never have to enter the ID manually.

Click **Save** and the table is created. In the definition tab HeidiSQL also shows the corresponding SQL code, which is the equivalent of:

```sql
CREATE TABLE test_table (
  name   VARCHAR(500) NOT NULL,
  age    TINYINT UNSIGNED NULL,
  salary DECIMAL(20,6) NULL,
  id     INT UNSIGNED NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (id)
);
```

Full source: [listing-24.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/en/parte-01/cap-02/listing-24.sql)


With the right click on the table you have the main operations: *Edit* to modify its structure, *Drop* to delete it (or empty it of all records), export data, etc.

### Enter data and run queries

Let's move on to the **Data** tab of the table: here we can enter the data. Click on the `+` sign to add a row and fill in the fields: like `name` let's put for example `john`, and like `salary`… let's put a nice salary of 100,000, maybe. Note that the `id` is automatically inserted with the value `1`, thanks to auto increment. You can save with the save icon, but the data is also automatically saved when you exit the line.

Now the **Query** tab, where we can write and execute SQL queries. A select:

```sql
SELECT * FROM test_table;
```

Full source: [listing-25.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/en/parte-01/cap-02/listing-25.sql)


Click the run icon and see the selected record. Let's try an update:

```sql
UPDATE test_table SET name = 'John Arias' WHERE id = 1;
```

Full source: [listing-26.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/en/parte-01/cap-02/listing-26.sql)


Let's run it, go back to the *Data* tab and click the **refresh** icon: the name is now "John Arias". This is just an overview of what we can do with HeidiSQL; You can still connect to this server with any other client — for example **DBeaver**, which you can easily find by searching and downloading it from its site.

### The mysql client from the command line

We can certainly also connect to the database from the command line. The `mysql` client is located in the `bin` folder of the installed version, for example `C:\laragon\bin\mysql\<version>\bin`: open that folder, right click → *Open in terminal* and connect with:

```bash
mysql -u root
```

Full source: [listing-27.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/en/parte-01/cap-02/listing-27.sh)


However, it only works if you are inside that `bin` folder; to use `mysql` from any location we must — as for PHP — add it to the environment variables: copy the path to the `bin` folder, search for "environment variables", open **Environment Variables**, select **Path → Edit → New** and paste the path (you can do it at user or system level). Close and reopen the terminal, and from any folder:

```bash
mysql -u root -p
```

Full source: [listing-28.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/en/parte-01/cap-02/listing-28.sh)


`-u root` indicates the user, `-p` asks for the password: leave it blank and press Enter, because by default there is no password. Once inside we can explore the server — remembering to end each command with a semicolon:

```sql
SHOW DATABASES;
USE test;
SHOW TABLES;
SELECT * FROM test_table;
```

Full source: [listing-29.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/en/parte-01/cap-02/listing-29.sql)


`SHOW DATABASES` lists the databases and among these we see `test`; `USE test` selects it; `SHOW TABLES` shows the tables, including ours `test_table`; and the `SELECT` returns the data entered. Interacting with MySQL from the command line is a little more challenging, because we have to be careful about the commands we write; in practice you can use the command line, HeidiSQL or any other client you have installed.

## In summary
- **Laragon** is a portable development environment for Windows: Apache, PHP, MySQL, npm and Git in a single folder, without touching system registers; to uninstall it just delete the folder.
- The projects served by the web server live under the **document root** `www`; with **Start All** you start the services, and if port 80 is occupied (for example by XAMPP) you can change it or stop the other environment.
- A PHP file begins with the tag `<?php`; anything outside the tags is sent as HTML. `echo` writes the output to the terminal or web page, depending on how you run PHP: `php file.php` from the command line, or via Apache by visiting `localhost/folder` (where `index.php` is the default file).
- By adding the `php.exe` folder to the **Path** environment variable you can launch `php` from any terminal; the Laragon terminal (Cmder) always points to the active version.
- **VS Code** with the extensions *PHP Intelephense*, *PHP Debug* and *PHP Server* is an excellent editor for PHP; **Git Bash** gives you Git and a Linux-style bash terminal, which you can set as default in VS Code. With `php -S localhost:port` you start PHP's built-in web server.
- To install a **new version of PHP** just download the zip (x64, Non Thread Safe) from php.net, extract it in `C:\laragon\bin\php` and activate it from the menu; then remember to restart Apache, reactivate the extensions and update the `Path`.
- For each folder under `www` Laragon automatically creates an Apache **virtual host** (`folder-name.test`) and the corresponding entry in the Windows `hosts` file; if it doesn't have permissions, you can add the line `127.0.0.1 name.test` by hand.
- New versions of **MySQL/MariaDB** are installed by copying the extracted zip in `C:\laragon\bin\mysql` and selecting them from the menu; with **HeidiSQL** you create databases, tables (columns, types, primary key, auto increment) and execute queries, while the `mysql` client does the same from the command line.
