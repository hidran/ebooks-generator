# 16. XML e DOM

Nei capitoli precedenti abbiamo visto come PHP dialoga con il browser attraverso le superglobali e i cookie, e come legge e scrive file sul file system. In questo capitolo facciamo un passo avanti e affrontiamo uno dei formati storici per lo scambio di dati sul web: **XML**. Impareremo a leggere un documento XML — per esempio il feed RSS di un sito — con l'estensione **SimpleXML**, a trasformarlo in una pagina web vera e propria, e poi a percorrere la strada inversa: generare un file XML da zero con l'API **DOM**, inviarlo al browser e salvarlo su disco.

Queste competenze tornano utili più spesso di quanto si pensi: feed di notizie, esportazioni di dati, sitemap, integrazioni con sistemi legacy che espongono i loro dati solo in XML. E, come vedremo, i metodi del DOM che impariamo qui in PHP sono gli stessi che ritroverai in JavaScript, perché fanno parte di uno standard comune.

## XML e il Document Object Model

PHP include fin dalla versione 5 una libreria XML che ci permette di manipolare file XML esistenti e di creare nuovi documenti XML secondo lo standard **DOM**. DOM sta per **Document Object Model**: è la rappresentazione ad albero di un documento — per esempio di una pagina web o di un feed di notizie — in cui ogni tag è un nodo che può contenere altri nodi.

Per capire com'è fatto un documento XML, prendiamo un caso reale: il **feed RSS** di un sito di articoli tecnici come SitePoint. Se apri il feed in un visualizzatore XML (ne trovi molti online), vedi qualcosa di simile:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>SitePoint</title>
    <link>https://www.sitepoint.com</link>
    <description>Learn HTML, CSS, JavaScript, PHP, Ruby and more</description>
    <item>
      <title>Titolo del primo articolo</title>
      <link>https://www.sitepoint.com/primo-articolo/</link>
      <description>Il riassunto del primo articolo…</description>
    </item>
    <item>
      <title>Titolo del secondo articolo</title>
      <link>https://www.sitepoint.com/secondo-articolo/</link>
      <description>Il riassunto del secondo articolo…</description>
    </item>
    <!-- …altri item… -->
  </channel>
</rss>
```

Codice completo: [listing-01.xml](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/it/parte-04/cap-16/listing-01.xml)


Analizziamo la struttura:

- La prima riga è la **dichiarazione XML**: indica la versione del formato (qui `1.0`) e la **codifica** del file (qui `UTF-8`).
- Segue un unico **elemento root** (radice) che racchiude tutto il documento. In un feed RSS l'elemento root è `rss`, che contiene a sua volta l'elemento `channel`, il "canale" del feed.
- `channel` ha alcuni elementi figli descrittivi — `title`, `link`, `description` — e poi una serie di elementi `item`, uno per ogni notizia o articolo pubblicato sul sito. Ogni `item` è un figlio di `channel`, e a sua volta contiene i propri elementi `title`, `link`, `description`.

Gli elementi XML assomigliano ai tag HTML, ma con una differenza fondamentale: mentre in HTML i tag sono predefiniti (`p`, `div`, `h1`…), **in XML i nomi dei tag li inventi tu**. Per convenzione si scrivono in minuscolo, ma nulla vieta di usare le maiuscole; l'unica regola ferrea è che il tag di apertura deve essere identico al tag di chiusura. Come in HTML, ogni elemento può avere degli **attributi** (per esempio `version="2.0"` sul tag `rss`).

Un documento XML valido deve avere come minimo la dichiarazione e un tag root:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<root></root>
```

Codice completo: [listing-02.xml](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/it/parte-04/cap-16/listing-02.xml)


Questo è già un documento XML completo — semplicemente vuoto.

Chi genera file come il feed di SitePoint? In moltissimi casi è proprio PHP: i siti fatti con WordPress, per esempio, costruiscono il feed RSS dinamicamente a partire dai dati salvati nel database. In questo capitolo impareremo a fare entrambe le cose: prima leggere e processare un XML esistente, poi generarne uno nostro.

## Leggere un file XML con SimpleXML

Partiamo dalla lettura. L'obiettivo è prendere il feed RSS di un sito — useremo SitePoint come esempio, ma il procedimento funziona con qualunque sito che esponga un feed — e accedere ai suoi dati da PHP.

Se apri l'URL del feed nel browser, vedrai il feed già formattato: il browser riconosce che si tratta di un feed e lo presenta in modo leggibile. Guardando il sorgente della pagina, però, scopri che si tratta di un normale file XML. È quello che andremo a leggere con PHP.

La prima cosa da fare è copiare l'URL del feed e metterlo in una variabile:

```php
<?php
$url = 'https://www.sitepoint.com/feed/';
```

Codice completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/it/parte-04/cap-16/listing-03.php)


Qui l'URL è scritto direttamente nel codice, ma immagina un aggregatore di feed: l'utente inserisce l'URL da leggere in un form, PHP lo riceve via richiesta e lo processa. La logica che stiamo per scrivere resta identica.

### Scaricare il contenuto con file_get_contents

Per leggere il file possiamo usare `file_get_contents()`, la funzione che abbiamo conosciuto nel Capitolo 15. Il bello è che accetta non solo percorsi locali ma anche URL esterni:

```php
$content = file_get_contents($url);
echo $content;
```

Codice completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/it/parte-04/cap-16/listing-04.php)


Lanciando lo script (ci mette qualche istante, perché deve scaricare il feed dal sito remoto) riceviamo il contenuto del file: il browser, riconoscendo un feed, lo mostra formattato. Ma attenzione: se facciamo un `var_dump($content)` scopriamo che quello che abbiamo in mano è una semplice **stringa**. Contiene XML, ma per PHP è solo testo: non possiamo ancora navigarlo come un albero.

### Da stringa a oggetto: simplexml_load_string

Per processare davvero l'XML entra in gioco l'estensione **SimpleXML**. Tutte le sue funzioni iniziano con il prefisso `simplexml_`; quella che ci serve ora è `simplexml_load_string()`, che prende una stringa XML e la trasforma in un oggetto:

```php
$xml = simplexml_load_string($content);
var_dump($xml);
```

Codice completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/it/parte-04/cap-16/listing-05.php)


Il dump mostra che `$xml` è un oggetto di tipo **SimpleXMLElement**, che contiene a sua volta altri elementi `SimpleXMLElement`: è l'albero del documento, finalmente navigabile.

### Navigare l'albero

Come arriviamo ai singoli elementi? `SimpleXMLElement` si comporta come un normale oggetto PHP: ogni elemento figlio diventa una proprietà raggiungibile con la freccia `->`. Inoltre l'oggetto ha un iteratore interno, quindi possiamo ciclarlo con `foreach` come se fosse un array.

Guardando la struttura del feed sappiamo che dentro `channel` ci sono `title` e `description`. Per leggere il titolo e la descrizione del canale basta scrivere:

```php
echo $xml->channel->title;       // SitePoint
echo $xml->channel->description; // la descrizione del feed
```

Codice completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/it/parte-04/cap-16/listing-06.php)


Nota che `$xml` rappresenta l'elemento root del documento (`rss`), quindi per scendere nell'albero partiamo da lì: `$xml->channel->title`, `$xml->channel->description`, e così via.

Gli articoli, invece, sono i tanti elementi `item` dentro `channel`. `$xml->channel->item` si comporta come un array di elementi, quindi lo cicliamo con `foreach` e per ogni articolo stampiamo titolo e link:

```php
foreach ($xml->channel->item as $item) {
    echo $item->title;
    echo '<br>';
    echo $item->link;
    echo '<br>';
}
```

Codice completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/it/parte-04/cap-16/listing-07.php)


Lanciando lo script vediamo scorrere titoli e link di tutti gli articoli del feed. Il risultato non è ancora bello da vedere — non l'abbiamo formattato in HTML — ma la sostanza c'è: stiamo accedendo ai valori dell'XML da PHP.

## Costruire una pagina web da un feed XML

Ora che la lettura funziona, facciamo un piccolo progetto: una pagina HTML che mostri gli articoli del feed come un vero mini-sito di notizie.

Teniamo il ciclo `foreach` appena scritto, che ci servirà, e costruiamo attorno la struttura HTML: il doctype, l'intestazione con `head`, e il tag `body`. Dentro il `body` mettiamo un tag `section` che conterrà tutto il feed: il titolo principale del sito in un `h1`, la descrizione in un `div` con una classe `description` (così potremo formattarla via CSS), e poi un tag `article` per ogni notizia.

Per il ciclo conviene usare la **sintassi alternativa** di `foreach` (`foreach (…): … endforeach;`), che abbiamo visto nel Capitolo 9: quando si mescolano PHP e HTML rende il template molto più leggibile. E per stampare i valori usiamo lo **short echo tag** `<?= … ?>`, la forma abbreviata di `echo`.

Ecco la pagina completa:

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
    <title>Il feed di SitePoint</title>
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

Codice completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/it/parte-04/cap-16/listing-08.php)


Qualche osservazione sul markup:

- Il titolo di ogni articolo va in un `h3` dentro il tag `article`.
- I dati dell'articolo stanno in una lista non ordinata: il primo `li` contiene il link. Se stampassimo solo `<?= $item->link ?>` avremmo l'URL come semplice testo; per renderlo cliccabile lo avvolgiamo in un tag `a`, usando lo stesso valore sia nell'attributo `href` sia come testo visibile. L'attributo `target="_blank"` fa aprire l'articolo in un'altra scheda.
- Il secondo `li` contiene la descrizione dell'articolo. Il feed offrirebbe anche altri campi — la data di pubblicazione, i commenti — che puoi aggiungere con lo stesso schema.
- Dopo ogni `article` un `hr` (una riga orizzontale) separa visivamente un articolo dall'altro.

Ricarica la pagina: in pochi minuti abbiamo creato un mini sito web con il feed di un altro sito. C'è il titolo principale, la descrizione del feed, e poi ogni articolo con titolo, link cliccabile e testo. Da qui in poi è questione di CSS: puoi collegare un foglio di stile e formattare `h1`, `article` e `.description` per rendere la pagina più gradevole — un ottimo esercizio se vuoi ripassare HTML e CSS.

### simplexml_load_file: tutto in un passaggio

Finora abbiamo fatto due passaggi: prima `file_get_contents()` per leggere il contenuto, poi `simplexml_load_string()` per interpretarlo. Esiste una funzione più comoda che li unisce: **`simplexml_load_file()`**. Le passi direttamente il percorso o l'URL del file, e PHP fa il resto:

```php
// $content = file_get_contents($url);
// $xml = simplexml_load_string($content);

$xml = simplexml_load_file($url);
```

Codice completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/it/parte-04/cap-16/listing-09.php)


Il funzionamento è identico, con un'unica funzione. Questo è il modo che userai normalmente per leggere un XML, che si trovi fuori dal tuo sito o in una tua cartella locale: `simplexml_load_file()` ti restituisce direttamente il `SimpleXMLElement` da ciclare.

### Le altre funzioni di SimpleXML

Se cerchi "SimpleXML" nel manuale di PHP trovi tutte le funzioni e i metodi disponibili. Oltre a navigare l'albero puoi manipolarlo: aggiungere attributi, leggere gli attributi di un elemento con il metodo `attributes()`, scorrere i figli con `children()`, ottenere il nome di un elemento con `getName()`, lavorare con i namespace.

Un metodo particolarmente utile è `asXML()`, che serializza l'elemento — con tutto il suo sottoalbero — di nuovo in XML. Se gli passi un nome di file, lo salva direttamente su disco:

```php
$xml->asXML('sitepoint.xml');
```

Codice completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/it/parte-04/cap-16/listing-10.php)


Dopo l'esecuzione, nella cartella dello script compare il file `sitepoint.xml` con l'intera struttura del feed: abbiamo trasformato l'oggetto `SimpleXMLElement` di nuovo in un file XML. In questo caso specifico avremmo potuto ottenere lo stesso risultato salvando la stringa di `file_get_contents()`, ma `asXML()` diventa prezioso quando prima di salvare hai *modificato* l'albero.

### Attenzione: gli elementi non sono stringhe

Un'ultima cosa importante. Gli elementi come `$item->title` *sembrano* stringhe, ma non lo sono: sono a loro volta oggetti `SimpleXMLElement`. Prova a inserire nel ciclo un `var_dump($item->title)` e vedrai:

```text
object(SimpleXMLElement)#5 (1) {
  [0]=>
  string(28) "Titolo del primo articolo…"
}
```

Codice completo: [listing-11.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/it/parte-04/cap-16/listing-11.txt)


Quando facciamo `echo`, PHP chiama automaticamente il metodo `__toString()` dell'oggetto e lo converte in stringa, quindi tutto funziona senza che ce ne accorgiamo. Ma se devi assegnare il valore a una variabile, salvarlo in un database o passarlo a una funzione che si aspetta una stringa, è sempre meglio fare esplicitamente il **cast a stringa**:

```php
$title = (string) $item->title;
```

Codice completo: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/it/parte-04/cap-16/listing-12.php)


Così è chiaro che stai salvando una stringa e non un oggetto `SimpleXMLElement` — un'abitudine che ti eviterà più di un bug.

## Creare un documento XML con DOM

Passiamo ora al percorso inverso: generare un file XML con PHP. Lo scenario è questo: abbiamo un array di film — immagina di averlo appena letto dal database — e vogliamo produrre un file XML da servire ai nostri utenti o da far scaricare.

```php
<?php
$films = [
    [
        'title'    => 'Batman',
        'year'     => 1989,
        'director' => 'Tim Burton',
        'plot'     => 'Il Cavaliere Oscuro difende Gotham City dal Joker.',
    ],
    [
        'title'    => 'Alien',
        'year'     => 1979,
        'director' => 'Ridley Scott',
        'plot'     => "L'equipaggio della Nostromo affronta una creatura letale.",
    ],
];
```

Codice completo: [listing-13.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/it/parte-04/cap-16/listing-13.php)


### DOMDocument

La prima cosa da fare è creare un documento di tipo DOM con la classe **`DOMDocument`**. Il primo parametro del costruttore è la versione XML (`1.0`), il secondo il charset (`utf-8`):

```php
$dom = new DOMDocument('1.0', 'utf-8');
```

Codice completo: [listing-14.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/it/parte-04/cap-16/listing-14.php)


Già con questa sola riga abbiamo un albero DOM. Un albero DOM può poi essere serializzato come XML, come HTML o salvato su file. Verifichiamo subito cosa contiene con il metodo `saveXML()`, che genera la stringa XML del documento e la restituisce:

```php
var_dump($dom->saveXML());
```

Codice completo: [listing-15.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/it/parte-04/cap-16/listing-15.php)


```text
string(39) "<?xml version="1.0" encoding="utf-8"?>
"
```

Codice completo: [listing-16.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/it/parte-04/cap-16/listing-16.txt)


C'è già la dichiarazione XML con versione ed encoding: il documento esiste, ma è vuoto. Siamo a buon punto.

Una nota prima di proseguire: i metodi che stiamo per usare — `createElement()`, `createTextNode()`, `appendChild()` — non sono un'invenzione di PHP. Sono i metodi dello **standard DOM**, gli stessi identici che usi in JavaScript per creare o manipolare un documento HTML, e che ritrovi anche in Java. Quello che impari qui lo riutilizzerai pari pari altrove.

### Creare l'elemento root

Un documento XML deve avere un elemento root. Lo creiamo con il metodo `createElement()` del documento, dandogli il nome dell'elemento — per la nostra collezione di film lo chiamiamo `movies`:

```php
$root = $dom->createElement('movies');
```

Codice completo: [listing-17.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/it/parte-04/cap-16/listing-17.php)


Se ora rilanciamo lo script, però, il root ancora non compare nell'XML. Perché? Perché l'abbiamo *creato*, ma non l'abbiamo *attaccato* al documento. Nel DOM creare un nodo e inserirlo nell'albero sono sempre due operazioni distinte. Per agganciarlo usiamo `appendChild()` — letteralmente "appendi un figlio" — sul documento:

```php
$dom->appendChild($root);
```

Codice completo: [listing-18.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/it/parte-04/cap-16/listing-18.php)


Adesso sì: l'output mostra l'elemento `movies`, vuoto, sotto la dichiarazione.

### Riempire l'albero con i cicli

Ora dobbiamo scrivere dentro il root tanti elementi quanti sono i film nell'array. Il piano è: per ogni film creiamo un elemento `movie`, e dentro ogni `movie` un elemento per ciascun campo (`title`, `year`, `director`, `plot`) con il suo contenuto testuale.

`$films` è un array di array, quindi ci servono due cicli annidati. Nel ciclo esterno scorriamo i film; nel ciclo interno scorriamo le coppie chiave/valore del singolo film: alla prima iterazione la chiave sarà `title` e il valore `Batman`, poi `year` e `1989`, e così via.

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

Codice completo: [listing-19.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/it/parte-04/cap-16/listing-19.php)


Seguiamo il flusso passo per passo:

1. **`$movie = $dom->createElement('movie')`** — per ogni film creiamo l'elemento contenitore. Avremmo potuto chiamarlo `item` o `film`: in XML il nome lo decidiamo noi.
2. **`$element = $dom->createElement($tag)`** — nel ciclo interno creiamo un elemento per ogni campo. Qui il nome è *dinamico*: passiamo la variabile `$tag`, che contiene le chiavi dell'array (`title`, `year`…).
3. **`$text = $dom->createTextNode($value)`** — il contenuto testuale di un elemento è a sua volta un nodo, un **nodo di testo**, e si crea con `createTextNode()` passando la stringa.
4. **`$element->appendChild($text)`** — appendiamo il nodo di testo all'elemento: `createElement()` restituisce un oggetto elemento, che ha anche lui il metodo `appendChild()`.
5. **`$movie->appendChild($element)`** — appendiamo l'elemento completo (tag più testo) al film.
6. **`$root->appendChild($movie)`** — alla fine di ogni giro del ciclo esterno, quando il film è completo, lo appendiamo al root. Se dimentichi questo passaggio, i nodi esistono ma non entrano mai nell'albero del documento.

Un consiglio pratico nato da un errore che è facilissimo commettere: occhio ai nomi delle variabili nei cicli annidati. Se chiami l'elemento contenitore `$film`, lo stesso nome della variabile del `foreach` esterno, a ogni iterazione interna lo sovrascrivi e il risultato è un albero vuoto o sbagliato. Per questo qui il contenitore si chiama `$movie`: nomi distinti, niente collisioni.

Facciamo un `var_dump($dom->saveXML())` di controllo: non è formattato bene, ma si vede che è stato creato l'elemento root `movies`, dentro ci sono gli elementi `movie`, e dentro ognuno gli elementi `title`, `year`, `director` e `plot`. L'albero è completo.

## Inviare al browser e salvare il file XML

Il `var_dump()` va bene per il debug, ma ora vogliamo servire l'XML come si deve.

### Inviare l'XML al browser

Sostituiamo il dump con un `echo` della stringa XML, ma prima diciamo al browser che cosa gli stiamo mandando, inviando un header `Content-Type` appropriato:

```php
header('Content-Type: text/xml');
echo $dom->saveXML();
```

Codice completo: [listing-20.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/it/parte-04/cap-16/listing-20.php)


Ricorda dal Capitolo 6 che `echo` è un costrutto del linguaggio e non ha bisogno delle parentesi tonde. Con l'header impostato, il browser sa che sta ricevendo XML: lo interpreta e ce lo formatta ad albero, esattamente come faceva con il feed di SitePoint. Il risultato:

```xml
<?xml version="1.0" encoding="utf-8"?>
<movies>
  <movie>
    <title>Batman</title>
    <year>1989</year>
    <director>Tim Burton</director>
    <plot>Il Cavaliere Oscuro difende Gotham City dal Joker.</plot>
  </movie>
  <movie>
    <title>Alien</title>
    <year>1979</year>
    <director>Ridley Scott</director>
    <plot>L'equipaggio della Nostromo affronta una creatura letale.</plot>
  </movie>
</movies>
```

Codice completo: [listing-21.xml](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/it/parte-04/cap-16/listing-21.xml)


Gli elementi `movie` sono due, come gli elementi dell'array; ognuno contiene i suoi `title`, `year`, `director` e `plot`, creati dinamicamente dal ciclo interno a partire dalle chiavi dell'array. Da array PHP a documento XML: missione compiuta.

### Salvare su file: il metodo save

Per salvare il documento su disco invece che (o oltre che) inviarlo al browser, c'è il metodo `save()`, a cui passiamo il nome del file:

```php
$dom->save('my_movies.xml');
```

Codice completo: [listing-22.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/it/parte-04/cap-16/listing-22.php)


Rilanciamo lo script e nella cartella compare `my_movies.xml`: aprendolo nell'editor troviamo il nostro XML, pronto per essere scaricato o distribuito.

Nel manuale di PHP, alla pagina di `DOMDocument`, trovi tutti gli altri metodi disponibili: creare commenti e reference, caricare un documento HTML esistente nel DOM con `loadHTML()` per manipolarne l'albero, caricare un file XML con `load()` e processarlo, e poi salvarlo di nuovo. I metodi che abbiamo usato — `createElement()`, `createTextNode()`, `appendChild()`, `saveXML()`, `save()` — sono i principali: una volta capiti questi, gli altri si imparano al volo dalla documentazione.

### Gli attributi degli elementi

Anche gli elementi DOM hanno i loro metodi, documentati alla pagina di `DOMElement`: puoi leggere un attributo con `getAttribute()`, verificare se esiste con `hasAttribute()`, e impostarlo con **`setAttribute()`**, che riceve il nome dell'attributo e il suo valore. Per esempio, possiamo dare a ogni elemento `movie` un attributo `id`:

```php
$id = 1;

foreach ($films as $film) {
    $movie = $dom->createElement('movie');
    $movie->setAttribute('id', $id++);
    // …resto del ciclo…
}
```

Codice completo: [listing-23.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/it/parte-04/cap-16/listing-23.php)


E nell'output ogni film diventa `<movie id="1">`, `<movie id="2">` e così via. XML è libero: puoi mettere qualunque nome di attributo su qualunque elemento.

Questo apre una domanda di *struttura*: l'anno di un film deve essere un elemento `<year>` o un attributo `year="1989"` del tag `movie`? Non c'è una risposta giusta in assoluto, è una scelta di design del documento. Il mio consiglio, dopo anni di file XML: preferisci gli elementi, e riserva gli attributi ai pochi dati che sono davvero "metadati" di un elemento (come un `id`). Un XML fatto di elementi è anche più facile da manipolare via codice rispetto a uno carico di attributi.

Chiudo con un'osservazione onesta: i file XML sono un formato un po' in declino. Oggi quasi tutte le API — da quelle dei social network in giù — restituiscono i dati in **JSON**, un formato che occupa meno spazio ed è altrettanto cross-platform: valori chiave-valore tra virgolette, con le graffe al posto dei tag. XML resta però indispensabile per i feed, le sitemap e tanti sistemi enterprise. E JSON è esattamente l'argomento del prossimo capitolo.

## In sintesi

- **XML** rappresenta i dati come un albero di elementi (il **DOM**, Document Object Model): una dichiarazione `<?xml … ?>`, un unico elemento root e tag liberi, inventati da chi progetta il documento, con eventuali attributi.
- **SimpleXML** legge un XML e lo trasforma in un oggetto navigabile: `simplexml_load_string()` parte da una stringa (per esempio ottenuta con `file_get_contents()`), `simplexml_load_file()` carica direttamente un file o un URL in un solo passaggio.
- Un `SimpleXMLElement` si naviga con la freccia (`$xml->channel->title`) e si cicla con `foreach` (`$xml->channel->item`); il metodo `asXML()` lo riserializza in XML, anche su file.
- Gli elementi SimpleXML **non sono stringhe**: `echo` li converte automaticamente, ma quando li salvi in variabili o database fai sempre il cast esplicito `(string)`.
- Per creare un XML da zero si usa **`DOMDocument`**: `createElement()` crea gli elementi, `createTextNode()` i nodi di testo, `appendChild()` aggancia ogni nodo al suo genitore — creare e appendere sono sempre due passaggi distinti.
- `saveXML()` restituisce la stringa XML (da inviare al browser con l'header `Content-Type: text/xml`), `save()` scrive il file su disco; `setAttribute()` aggiunge attributi agli elementi.
- I metodi del DOM sono uno standard: gli stessi che usi in PHP li ritrovi identici in JavaScript e in Java.
