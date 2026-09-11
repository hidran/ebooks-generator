# 16. XML and DOM

In previous chapters we saw how PHP communicates with the browser through superglobals and cookies, and how it reads and writes files on the file system. In this chapter we take a step forward and address one of the historical formats for exchanging data on the web: **XML**. We will learn to read an

These skills come in handy more often than you think: news feeds, data exports, sitemaps, integrations with legacy systems that only expose their data in XML. And, as we'll see, the DOM methods we learn here in PHP are the same ones you'll find in JavaScript, because they're part of a common standard.

## XML and the Document Object Model

Since version 5, PHP has included an XML library that allows us to manipulate existing XML files and create new XML documents according to the **DOM** standard. DOM stands for **Document Object Model**: it is the tree representation of a document — for example, a web page or a news feed — in which each tag is a node that can contain other nodes.

To understand what an XML document looks like, let's take a real case: the **RSS feed** of a technical article site like SitePoint. If you open the feed in an XML viewer (you find many online), you see something like this:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>SitePoint</title>
    <link>https://www.sitepoint.com</link>
    <description>Learn HTML, CSS, JavaScript, PHP, Ruby and more</description>
    <item>
      <title>First article title</title>
      <link>https://www.sitepoint.com/first-article/</link>
      <description>First article summary…</description>
    </item>
    <item>
      <title>Second article title</title>
      <link>https://www.sitepoint.com/second-article/</link>
      <description>Second article summary…</description>
    </item>
    <!-- …other items… -->
  </channel>
</rss>
```

Full source: [listing-01.xml](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/en/parte-04/cap-16/listing-01.xml)


Let's analyze the structure:

- The first line is the **XML declaration**: it indicates the format version (here `1.0`) and the **encoding** of the file (here `UTF-8`).
- A single **root element** follows which encloses the entire document. In an RSS feed the root element is `rss`, which in turn contains the `channel` element, the "channel" of the feed.
- `channel` has some descriptive child elements — `title`, `link`, `description` — and then a series of `item` elements, one for each news or article published on the site. Each `item` is a child of `channel`, and in turn contains its own elements `title`, `link`, `description`.

XML elements resemble HTML tags, but with one fundamental difference: while in HTML the tags are predefined (`p`, `div`, `h1`…), **in XML you invent the tag names**. By convention they are written in lower case, but nothing prevents them from being capitalized; the only hard and fast rule is that the opening tag must be identical to the closing tag. As in HTML, each element can have **attributes** (for example `version="2.0"` on the `rss` tag).

A valid XML document must have at least the declaration and a root tag:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<root></root>
```

Full source: [listing-02.xml](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/en/parte-04/cap-16/listing-02.xml)


This is already a complete XML document — just empty.

Who generates files like the SitePoint feed? In many cases it is actually PHP: sites made with WordPress, for example, build the RSS feed dynamically starting from the data saved in the database. In this chapter we will learn to do both: first read and process existing XML, then generate our own.

## Read an XML file with SimpleXML

Let's start with reading. The goal is to take a site's RSS feed — we'll use SitePoint as an example, but the process works with any site that exposes a feed — and access its data from PHP.

If you open the feed URL in your browser, you'll see the feed already formatted: the browser recognizes that it's a feed and presents it in a readable way. Looking at the source of the page, however, you discover that it is a normal XML file. That's what we're going to read with PHP.

The first thing to do is copy the feed URL and put it in a variable:

```php
<?php
$url = 'https://www.sitepoint.com/feed/';
```

Full source: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/en/parte-04/cap-16/listing-03.php)


Here the URL is written directly in the code, but imagine a feed aggregator: the user enters the URL to read in a form, PHP receives it via request and processes it. The logic we are about to write remains identical.

### Download content with file_get_contents

To read the file we can use `file_get_contents()`, the function we learned about in Chapter 15. The great thing is that it accepts not only local paths but also external URLs:

```php
$content = file_get_contents($url);
echo $content;
```

Full source: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/en/parte-04/cap-16/listing-04.php)


By launching the script (it takes a few moments, because it has to download the feed from the remote site) we receive the contents of the file: the browser, recognizing a feed, shows it formatted. But be careful: if we do an `var_dump($content)` we discover that what we have in hand is a simple **string**. It contains XML, but for PHP it's just text - we can't navigate it as a tree yet.

### String to object: simplexml_load_string

To actually process the XML the **SimpleXML** extension comes into play. All its functions begin with the prefix `simplexml_`; what we need now is `simplexml_load_string()`, which takes an XML string and transforms it into an object:

```php
$xml = simplexml_load_string($content);
var_dump($xml);
```

Full source: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/en/parte-04/cap-16/listing-05.php)


The dump shows that `$xml` is an object of type **SimpleXMLElement**, which in turn contains other elements `SimpleXMLElement`: it is the document tree, finally navigable.

### Navigate the tree

How do we get to the individual elements? `SimpleXMLElement` behaves like a normal PHP object: each child element becomes a property reachable with the `->` arrow. Furthermore, the object has an internal iterator, so we can loop through it with `foreach` as if it were an array.

Looking at the structure of the feed we know that inside `channel` there are `title` and `description`. To read the title and description of the channel just write:

```php
echo $xml->channel->title;       // SitePoint
echo $xml->channel->description; // the feed description
```

Full source: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/en/parte-04/cap-16/listing-06.php)


Note that `$xml` represents the root element of the document (`rss`), so to go down the tree we start from there: `$xml->channel->title`, `$xml->channel->description`, and so on.

The articles, on the other hand, are the many elements `item` inside `channel`. `$xml->channel->item` behaves like an array of elements, so we loop it with `foreach` and for each article we print the title and link:

```php
foreach ($xml->channel->item as $item) {
    echo $item->title;
    echo '<br>';
    echo $item->link;
    echo '<br>';
}
```

Full source: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/en/parte-04/cap-16/listing-07.php)


By launching the script we see the titles and links of all the articles in the feed scroll. The result still isn't nice to look at — we haven't formatted it in HTML — but the gist is there: we're accessing the XML values ​​from PHP.

## Building a web page from an XML feed

Now that reading works, let's do a little project: an HTML page that displays the feed articles like a real news mini-site.

We keep the `foreach` loop we just wrote, which we will need, and build the HTML structure around it: the doctype, the header with `head`, and the `body` tag. Inside the `body` we put a tag `section` which will contain the entire feed: the main title of the site in a `h1`, the description in a `div` with a class `description` (so we can format it via CSS), and then a tag `article` for any news.

For the loop it is better to use the **alternative syntax** of `foreach` (`foreach (…): … endforeach;`), which we saw in Chapter 9: when you mix PHP and HTML it makes the template much more readable. And to print the values ​​we use the **short echo tag** `<?= … ?>`, the short form of `echo`.

Here is the full page:

```php
<?php
$url = 'https://www.sitepoint.com/feed/';

$content = file_get_contents($url);
$xml = simplexml_load_string($content);
?>
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <title>The SitePoint feed</title>
</head>
<body>
<section>
    <h1><?= $xml->channel->title ?></h1>
    <div class="description"><?= $xml->channel->description ?></div>

    <?php foreach ($xml->channel->item as $item): ?>
        <article>
            <h3><?= $item->title ?></h3>
            <ul>
                <li>
                    <a href="<?= $item->link ?>" target="_blank"><?= $item->link ?></a>
                </li>
                <li><?= $item->description ?></li>
            </ul>
        </article>
        <hr>
    <?php endforeach; ?>
</section>
</body>
</html>
```

Full source: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/en/parte-04/cap-16/listing-08.php)


Some comments on markup:

- The title of each article goes in an `h3` inside the `article` tag.
- The article data is in an unordered list: the first `li` contains the link. If we just printed `<?= $item->link ?>` we would have the URL as plain text; to make it clickable we wrap it in an `a` tag, using the same value both in the `href` attribute and as visible text. The `target="_blank"` attribute opens the article in another tab.
- The second `li` contains the description of the item. The feed would also offer other fields — date posted, comments — that you can add with the same pattern.
- After each `article` a `hr` (a horizontal line) visually separates one article from the other.

Reload the page: in a few minutes we created a mini website with the feed of another site. There is the main title, the feed description, and then each article with title, clickable link and text. From here on it's all about CSS: you can attach a style sheet and format `h1`, `article`, and `.description` to make the page nicer — a great exercise if you want to brush up on HTML and CSS.
### simplexml_load_file: All in one step

So far we have done two steps: first `file_get_contents()` to read the content, then `simplexml_load_string()` to interpret it. There is a more convenient function that combines them: **`simplexml_load_file()`**. You pass it the file path or URL directly, and PHP does the rest:

```php
// $content = file_get_contents($url);
// $xml = simplexml_load_string($content);

$xml = simplexml_load_file($url);
```

Full source: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/en/parte-04/cap-16/listing-09.php)


Operation is identical, with a single function. This is the way you will normally use to read an XML, whether it is outside your site or in your local folder: `simplexml_load_file()` directly returns the `SimpleXMLElement` to be looped.

### The other functions of SimpleXML

If you search for "SimpleXML" in the PHP manual you will find all the available functions and methods. In addition to navigating the tree you can manipulate it: add attributes, read the attributes of an element with the `attributes()` method, iterate through children with `children()`, get the name of an element with `getName()`, work with namespaces.

A particularly useful method is `asXML()`, which serializes the element — with its entire subtree — back to XML. If you give it a file name, it saves it directly to disk:

```php
$xml->asXML('sitepoint.xml');
```

Full source: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/en/parte-04/cap-16/listing-10.php)


After execution, the file `sitepoint.xml` appears in the script folder with the entire feed structure: we transformed the `SimpleXMLElement` object back into an XML file. In this specific case we could have obtained the same result by saving the `file_get_contents()` string, but `asXML()` becomes valuable when you *modified* the tree before saving.

### Warning: elements are not strings

One last important thing. Elements like `$item->title` *look* like strings, but they aren't: they are themselves `SimpleXMLElement` objects. Try inserting an `var_dump($item->title)` into the loop and you'll see:

```text
object(SimpleXMLElement)#5 (1) {
  [0]=>
  string(28) "First article title…"
}
```

Full source: [listing-11.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/en/parte-04/cap-16/listing-11.txt)


When we do `echo`, PHP automatically calls the object's `__toString()` method and converts it to a string, so everything works without us realizing it. But if you need to assign the value to a variable, save it in a database, or pass it to a function that expects a string, it's always better to explicitly cast it to string:

```php
$title = (string) $item->title;
```

Full source: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/en/parte-04/cap-16/listing-12.php)


So it's clear that you're saving a string and not an `SimpleXMLElement` object — a habit that will save you more than one bug.

## Create an XML document with DOM

Let's now move on to the reverse path: generating an XML file with PHP. The scenario is this: we have an array of movies — imagine we just read it from the database — and we want to produce an XML file to serve to our users or for them to download.

```php
<?php
$films = [
    [
        'title'    => 'Batman',
        'year'     => 1989,
        'director' => 'Tim Burton',
        'plot'     => 'The Dark Knight defends Gotham City from the Joker.',
    ],
    [
        'title'    => 'Alien',
        'year'     => 1979,
        'director' => 'Ridley Scott',
        'plot'     => "The Nostromo crew faces a lethal creature.",
    ],
];
```

Full source: [listing-13.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/en/parte-04/cap-16/listing-13.php)


### DOMDocument

The first thing to do is create a DOM type document with the **`DOMDocument`** class. The first parameter of the constructor is the XML version (`1.0`), the second the charset (`utf-8`):

```php
$dom = new DOMDocument('1.0', 'utf-8');
```

Full source: [listing-14.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/en/parte-04/cap-16/listing-14.php)


Already with this single line we have a DOM tree. A DOM tree can then be serialized as XML, as HTML, or saved to a file. Let's immediately check what it contains with the `saveXML()` method, which generates the XML string of the document and returns it:

```php
var_dump($dom->saveXML());
```

Full source: [listing-15.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/en/parte-04/cap-16/listing-15.php)


```text
string(39) "<?xml version="1.0" encoding="utf-8"?>
"
```

Full source: [listing-16.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/en/parte-04/cap-16/listing-16.txt)


The XML declaration with version and encoding is already there: the document exists, but it is empty. We're at a good point.

A note before continuing: the methods we are about to use — `createElement()`, `createTextNode()`, `appendChild()` — are not an invention of PHP. They are the methods of the **standard DOM**, the exact same ones you use in JavaScript to create or manipulate an HTML document, and which you also find in Java. What you learn here you will reuse elsewhere.

### Create the root element

An XML document must have a root element. We create it with the `createElement()` method of the document, giving it the name of the element — for our movie collection we call it `movies`:

```php
$root = $dom->createElement('movies');
```

Full source: [listing-17.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/en/parte-04/cap-16/listing-17.php)


If we now relaunch the script, however, the root still does not appear in the XML. Why? Because we *created* it, but we didn't *attach* it to the document. In the DOM, creating a node and inserting it into the tree are always two distinct operations. To hook it we use `appendChild()` — literally "hang a child" — on the document:

```php
$dom->appendChild($root);
```

Full source: [listing-18.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/en/parte-04/cap-16/listing-18.php)


Now yes: the output shows the `movies` element, empty, below the declaration.

### Fill the tree with loops
Now we have to write as many elements into the root as there are films in the array. The plan is: for each movie we create an element `movie`, and inside each `movie` an element for each field (`title`, `year`, `director`, `plot`) with its textual content.

`$films` is an array of arrays, so we need two nested loops. In the outer loop we scroll through the films; in the internal loop we scroll through the key/value pairs of the single film: at the first iteration the key will be `title` and the value `Batman`, then `year` and `1989`, and so on.

```php
foreach ($films as $film) {
    $movie = $dom->createElement('movie');

    foreach ($film as $tag => $value) {
        $element = $dom->createElement($tag);
        $text = $dom->createTextNode($value);
        $element->appendChild($text);
        $movie->appendChild($element);
    }

    $root->appendChild($movie);
}
```

Full source: [listing-19.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/en/parte-04/cap-16/listing-19.php)


Let's follow the flow step by step:

1. **`$movie = $dom->createElement('movie')`** — for each movie we create the container element. We could have called it `item` or `film`: in XML we decide the name.
2. **`$element = $dom->createElement($tag)`** — in the inner loop we create an element for each field. Here the name is *dynamic*: we pass the variable `$tag`, which contains the keys of the array (`title`, `year`…).
3. **`$text = $dom->createTextNode($value)`** — the textual content of an element is itself a node, a **text node**, and is created with `createTextNode()` passing the string.
4. **`$element->appendChild($text)`** — we append the text node to the element: `createElement()` returns an element object, which also has the `appendChild()` method.
5. **`$movie->appendChild($element)`** — we attach the complete element (tag plus text) to the film.
6. **`$root->appendChild($movie)`** — at the end of each round of the outer loop, when the film is complete, we hang it at the root. If you forget this step, the nodes exist but never enter the document tree.

A practical tip born from a mistake that is very easy to make: pay attention to the names of the variables in nested loops. If you call the container element `$film`, the same variable name as the external `foreach`, on each internal iteration you overwrite it and the result is an empty or wrong tree. That's why the container here is called `$movie`: distinct names, no collisions.

Let's do a `var_dump($dom->saveXML())` check: it is not formatted well, but you can see that the root element `movies` has been created, inside there are the elements `movie`, and inside each one the elements `title`, `year`, `director` and `plot`. The tree is complete.

## Send to browser and save the XML file

The `var_dump()` is fine for debugging, but now we want to serve the XML properly.

### Send the XML to the browser

We replace the dump with an `echo` of the XML string, but first we tell the browser what we are sending it, by sending an appropriate `Content-Type` header:

```php
header('Content-Type: text/xml');
echo $dom->saveXML();
```

Full source: [listing-20.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/en/parte-04/cap-16/listing-20.php)


Recall from Chapter 6 that `echo` is a language construct and does not need parentheses. With the header set, the browser knows that it is receiving XML: it interprets it and formats it as a tree, exactly as it did with the SitePoint feed. The result:

```xml
<?xml version="1.0" encoding="utf-8"?>
<movies>
  <movie>
    <title>Batman</title>
    <year>1989</year>
    <director>Tim Burton</director>
    <plot>The Dark Knight defends Gotham City from the Joker.</plot>
  </movie>
  <movie>
    <title>Alien</title>
    <year>1979</year>
    <director>Ridley Scott</director>
    <plot>The Nostromo crew faces a lethal creature.</plot>
  </movie>
</movies>
```

Full source: [listing-21.xml](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/en/parte-04/cap-16/listing-21.xml)


There are two elements `movie`, like the elements of the array; each contains its own `title`, `year`, `director` and `plot`, created dynamically by the internal loop starting from the array keys. From PHP array to XML document: mission accomplished.

### Save to file: the save method

To save the document to disk instead of (or in addition to) sending it to the browser, there is the `save()` method, to which we pass the file name:

```php
$dom->save('my_movies.xml');
```

Full source: [listing-22.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/en/parte-04/cap-16/listing-22.php)


We relaunch the script and `my_movies.xml` appears in the folder: by opening it in the editor we find our XML, ready to be downloaded or distributed.

In the PHP manual, on the `DOMDocument` page, you will find all the other available methods: create comments and references, load an existing HTML document into the DOM with `loadHTML()` to manipulate its tree, load an XML file with `load()` and process it, and then save it again. The methods we used — `createElement()`, `createTextNode()`, `appendChild()`, `saveXML()`, `save()` — are the main ones: once these are understood, the others can be learned quickly from the documentation.

### The attributes of the elements
DOM elements also have their own methods, documented on the `DOMElement` page: you can read an attribute with `getAttribute()`, check if it exists with `hasAttribute()`, and set it with **`setAttribute()`**, which receives the attribute name and its value. For example, we can give each `movie` element an `id` attribute:

```php
$id = 1;

foreach ($films as $film) {
    $movie = $dom->createElement('movie');
    $movie->setAttribute('id', $id++);
    // …rest of the loop…
}
```

Full source: [listing-23.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/en/parte-04/cap-16/listing-23.php)


And in the output each movie becomes `<movie id="1">`, `<movie id="2">` and so on. XML is free: you can put any attribute name on any element.

This opens up a *structure* question: should a movie's year be an `<year>` element or an `year="1989"` attribute of the `movie` tag? There is no absolute right answer, it's a document design choice. My advice, after years of XML files: prefer elements, and reserve attributes for the few data points that are truly "metadata" of an element (like an `id`). An XML made up of elements is also easier to manipulate via code than one loaded with attributes.

I close with an honest observation: XML files are a format that is somewhat in decline. Today, almost all APIs — from social networks on down — return data in **JSON**, a format that takes up less space and is equally cross-platform: key-value values ​​in quotes, with braces instead of tags. However, XML remains indispensable for feeds, sitemaps and many enterprise systems. And JSON is exactly what the next chapter is about.

## In summary

- **XML** represents data as a tree of elements (the **DOM**, Document Object Model): a `<?xml … ?>` declaration, a single root element and free tags, invented by whoever designs the document, with any attributes.
- **SimpleXML** reads an
- An `SimpleXMLElement` is navigated with the arrow (`$xml->channel->title`) and cycled with `foreach` (`$xml->channel->item`); the method `asXML()` reserializes it in XML, even on file.
- SimpleXML elements **are not strings**: `echo` automatically converts them, but when saving them in variables or databases always explicitly cast `(string)`.
- To create an
- `saveXML()` returns the XML string (to be sent to the browser with the `Content-Type: text/xml` header), `save()` writes the file to disk; `setAttribute()` adds attributes to elements.
- The DOM methods are a standard: the same ones you use in PHP are identical in JavaScript and Java.
