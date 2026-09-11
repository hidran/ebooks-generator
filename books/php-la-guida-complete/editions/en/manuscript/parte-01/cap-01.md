# 1. Introduction to PHP

Welcome. In this chapter we will get to know PHP: where it comes from, how it has evolved and why, decades after its birth, it is still one of the most used languages ​​in the world for building the web. A little history also serves to dispel a prejudice: some people believe that PHP is not a "real" programming language compared to Java or C#. They are usually people who know the PHP of twenty years ago, not the PHP of today.

In the second part of the chapter we will instead see a complete overview of what this book covers, part by part, and the two practical projects that we will build together: a complete **User Management System** and a blogging platform based on the **MVC** pattern.

## A bit of history: from personal script to web language

PHP didn't start out as a programming language. It was created by **Rasmus Lerdorf**, a Dane who I had the chance to meet in person in 2014, at the PHP Day in Verona. He told us that he created this scripting language, called PHP — at the time the acronym stood for *Personal Home Page* — for a very concrete need: to process the **forms** of HTML pages. The mechanism is the one we will use throughout the book: we have a form, the user fills it in and the data is sent to the server. Lerdorf wrote a series of scripts in C to be called directly from HTML pages, in order to process that data on the server side, and for the syntax he borrowed elements from C, C++ and Perl.

He had created those scripts for himself, for personal use. But people liked the language, other developers started adding new features, and PHP became an **open source** project. At that point **Zeev Suraski** and **Andi Gutmans** entered the scene, rewriting the heart of the language: very little remained of Lerdorf's original code. The new engine, called **Zend Engine**, made PHP much faster.

From there the evolution was continuous:

- **PHP 4** introduced the first object-oriented programming and **session management**;
- **PHP 5** brought, among other things, **namespaces**;
- with **PHP 8**, the version on which this book is based, the language no longer has anything to envy of the others: it offers complete and mature object-oriented programming, functional programming constructs and excellent performance.

Today, among other things, the acronym PHP no longer means "Personal Home Page" but has become recursive: *PHP: Hypertext Preprocessor*. If you are curious about the complete story, you can find all the details on Wikipedia; what matters to us is to understand that modern PHP is a profoundly different language from its origins.

## PHP today: much more than a language for the web

Today's PHP is not just a language for generating web pages. With PHP you can write scripts that run on the server directly from the **command line**: make calls to external services, open sockets, connect via FTP or SSH — you can do almost anything, even desktop applications. It is a very versatile and currently very strong language.

Recent versions have added increasingly modern tools: since 8.1, for example, we have **enumerations** (the *enum*, which we will explore in Chapter 28) and `final` constants in classes. We will cover these features throughout the book, up to the new features in PHP 8.5.

And the numbers speak for themselves: PHP is still going strong. Large e-commerce sites run on platforms written in PHP, such as Magento or PrestaShop, the reference frameworks for creating online stores. There is WordPress, and overall almost 80% of web pages are served by PHP code. If you are here it is because you like PHP or you want to discover it: in both cases you are in the right place.

## What you will find in this book

Let's now get an overview of what we'll study, so you know what to expect from each part of the book and where the hands-on projects fit in.

### From the basics of the language to the web
In **Part I** we prepare the development environment. There are chapters dedicated to each operating system: if you are on Windows follow Chapter 2, where we install PHP with Laragon (in Appendix A you will find the alternatives, such as XAMPP); if you are on macOS follow Chapter 3; if you are on Linux Chapter 4, where we configure a LAMP stack. We close the part by configuring Visual Studio Code for PHP. A practical tip: if you already have a development environment with a recent version of PHP, you're good to go — you can skip the installation chapters that don't apply to you and go straight to Part II.

In **Part II** we cover all the fundamentals of the language: the basic syntax, variables, types and constants, operators and control structures like `if`/`else`, and loops.

**Part III** is dedicated to functions: how to declare them and use them, and then the functions for working with strings and those for working with arrays.

In **Part IV** we enter PHP for the web: **superglobal** variables, cookie management, all the features to access the file system with `include` and `require`, how to process XML and the DOM with PHP, and finally JSON.

In **Part V** we will see how to connect to **MySQL**: what it is, how to use phpMyAdmin and a quick overview of `SELECT`, `INSERT`, `UPDATE` and `DELETE`, so you have everything you need to move on to your first practical project.

### The first project: the User Management System

**Part VI** — the largest part of the book — is entirely dedicated to building, step by step, a **User Management System** (UMS): a complete user management system connected to a database. I'll give you a preview of what the end result is like, so you know where we're going.

The application presents a list of users read from the database, with the possibility of inserting a new user, modifying it and deleting it. There is the search: if you search for "Robert" for example, the list is filtered in real time; and there is **pagination** of the results. We also manage the uploading and image processing for each user's profile. Then we build a complete **login** system, with the "remember me" function created with cookies, and the management of **roles**: an admin user sees the edit and delete buttons, while a normal user would not see them at all.

You can reuse this project in any of your jobs where you need to connect to a database, show data, insert, modify and delete records, plus profile management. We start from scratch, **procedural** style, and gradually evolve it towards an organized structure that separates responsibilities — a sort of mini MVC, even if we don't use classes yet.

### Object-oriented programming and professional PHP

In **Part VII** we cover all object-oriented programming, from scratch to the most advanced aspects: classes and properties, interfaces, abstract classes, enumerations, PHP's **magic methods**, and then namespaces and **autoloading**.

In **Part VIII** we move on to professional PHP tools: **Composer**, to include external packages in our projects, and error and exception management.

### The second project: the enterprise MVC Blog

In **Part IX** we take an MVC blogging platform and move it toward an enterprise structure: Composer, PSR-4, a tested router, thin controllers, models as DTOs, PDO repositories, services, dependency injection, PSR-7/15, migrations, authentication, Docker, Redis, and CI/CD. Every step follows the tags in the `phpenterpriseblog` repository, so you can inspect the code commit by commit.

In the finished blog, a user can register or log in, publish a new article, and — if they are the owner of a post — edit and delete it; you can also add comments. A visitor who is not logged in still sees public blog posts.

**Part X** closes the book, where we take our work toward production: JSON and health checks, deployment, and sending email with PHP.

We need these two projects to put into practice everything we will learn: we will never remain on pure theory. So let's start — from scratch.

## In summary
- PHP was born as a set of C scripts created by Rasmus Lerdorf to process HTML page forms; the syntax borrows elements from C, C++ and Perl.
- Now open source, its heart has been rewritten by Zeev Suraski and Andi Gutmans with the much faster Zend Engine; PHP 4 brought objects and sessions, PHP 5 namespaces, and PHP 8 makes it a modern language in its own right.
- Today's PHP is not just for the web: it is also used on the command line for scripts, sockets, FTP, SSH and even desktop applications.
- PHP is still dominant: WordPress, Magento and most web pages run on PHP.
- The book covers the entire language — from the basics to object-oriented programming, from MySQL to Composer — and puts it into practice with two complete projects: the User Management System (Part VI) and the MVC Blog (Part IX).
