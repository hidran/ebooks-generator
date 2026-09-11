# 16. XML y DOM

En capítulos anteriores vimos cómo PHP se comunica con el navegador a través de superglobals y cookies, y cómo lee y escribe archivos en el sistema de archivos. En este capítulo damos un paso adelante y abordamos uno de los formatos históricos para el intercambio de datos en la web: **XML**. Aprenderemos a leer un

Estas habilidades resultan útiles con más frecuencia de lo que cree: fuentes de noticias, exportaciones de datos, mapas de sitio, integraciones con sistemas heredados que solo exponen sus datos en XML. Y, como veremos, los métodos DOM que aprendemos aquí en PHP son los mismos que encontrarás en JavaScript, porque son parte de un estándar común.

## XML y el modelo de objetos del documento

Desde la versión 5, PHP ha incluido una biblioteca XML que nos permite manipular archivos XML existentes y crear nuevos documentos XML según el estándar **DOM**. DOM significa **Modelo de objetos de documento**: es la representación en árbol de un documento (por ejemplo, una página web o una fuente de noticias) en la que cada etiqueta es un nodo que puede contener otros nodos.

Para entender cómo se ve un documento XML, tomemos un caso real: el **fuente RSS** de un sitio de artículos técnicos como SitePoint. Si abre el feed en un visor XML (encontrará muchos en línea), verá algo como esto:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>SitePoint</title>
    <link>https://www.sitepoint.com</link>
    <description>Learn HTML, CSS, JavaScript, PHP, Ruby and more</description>
    <item>
      <title>Título del primer artículo</title>
      <link>https://www.sitepoint.com/primer-articulo/</link>
      <description>Resumen del primer artículo…</description>
    </item>
    <item>
      <title>Título del segundo artículo</title>
      <link>https://www.sitepoint.com/segundo-articulo/</link>
      <description>Resumen del segundo artículo…</description>
    </item>
    <!-- …otros elementos… -->
  </channel>
</rss>
```

Código completo: [listing-01.xml](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/es/parte-04/cap-16/listing-01.xml)


Analicemos la estructura:

- La primera línea es la **declaración XML**: indica la versión del formato (aquí `1.0`) y la **codificación** del archivo (aquí `UTF-8`).
- Sigue un único **elemento raíz** que encierra todo el documento. En un feed RSS el elemento raíz es `rss`, que a su vez contiene el elemento `channel`, el "canal" del feed.
- `channel` tiene algunos elementos secundarios descriptivos — `title`, `link`, `description` — y luego una serie de elementos `item`, uno para cada noticia o artículo publicado en el sitio. Cada `item` es hijo de `channel` y, a su vez, contiene sus propios elementos `title`, `link`, `description`.

Los elementos XML se parecen a las etiquetas HTML, pero con una diferencia fundamental: mientras que en HTML las etiquetas están predefinidas (`p`, `div`, `h1`…), **en XML inventas los nombres de las etiquetas**. Por convención se escriben en minúscula, pero nada impide que se escriban en mayúscula; La única regla estricta es que la etiqueta de apertura debe ser idéntica a la etiqueta de cierre. Como en HTML, cada elemento puede tener **atributos** (por ejemplo `version="2.0"` en la etiqueta `rss`).

Un documento XML válido debe tener al menos la declaración y una etiqueta raíz:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<root></root>
```

Código completo: [listing-02.xml](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/es/parte-04/cap-16/listing-02.xml)


Este ya es un documento XML completo, simplemente vacío.

¿Quién genera archivos como el feed de SitePoint? En muchos casos, en realidad se trata de PHP: los sitios creados con WordPress, por ejemplo, crean el feed RSS de forma dinámica a partir de los datos guardados en la base de datos. En este capítulo aprenderemos a hacer ambas cosas: primero leer y procesar XML existente y luego generar el nuestro propio.

## Leer un archivo XML con SimpleXML

Empecemos por la lectura. El objetivo es tomar el feed RSS de un sitio (usaremos SitePoint como ejemplo, pero el proceso funciona con cualquier sitio que exponga un feed) y acceder a sus datos desde PHP.

Si abre la URL del feed en su navegador, verá el feed ya formateado: el navegador reconoce que es un feed y lo presenta de forma legible. Sin embargo, al mirar el código fuente de la página, descubre que es un archivo XML normal. Eso es lo que vamos a leer con PHP.

Lo primero que debemos hacer es copiar la URL del feed y ponerla en una variable:

```php
<?php
$url = 'https://www.sitepoint.com/feed/';
```

Código completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/es/parte-04/cap-16/listing-03.php)


Aquí la URL está escrita directamente en el código, pero imagine un agregador de feeds: el usuario ingresa la URL para leer en un formulario, PHP la recibe mediante solicitud y la procesa. La lógica que estamos a punto de escribir sigue siendo idéntica.

### Descargar contenido con file_get_contents

Para leer el archivo podemos usar `file_get_contents()`, la función que aprendimos en el Capítulo 15. Lo bueno es que acepta no solo rutas locales sino también URL externas:

```php
$content = file_get_contents($url);
echo $content;
```

Código completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/es/parte-04/cap-16/listing-04.php)


Al iniciar el script (tarda unos instantes, porque hay que descargar el feed desde el sitio remoto) recibimos el contenido del archivo: el navegador, al reconocer un feed, lo muestra formateado. Pero ojo: si hacemos un `var_dump($content)` descubrimos que lo que tenemos entre manos es una simple **cadena**. Contiene XML, pero para PHP es solo texto; todavía no podemos navegar por él como un árbol.

### Cadena al objeto: simplexml_load_string

Para procesar realmente el XML entra en juego la extensión **SimpleXML**. Todas sus funciones comienzan con el prefijo `simplexml_`; lo que necesitamos ahora es `simplexml_load_string()`, que toma una cadena XML y la transforma en un objeto:

```php
$xml = simplexml_load_string($content);
var_dump($xml);
```

Código completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/es/parte-04/cap-16/listing-05.php)


El volcado muestra que `$xml` es un objeto de tipo **SimpleXMLElement**, que a su vez contiene otros elementos `SimpleXMLElement`: es el árbol del documento, finalmente navegable.

### Navegar por el árbol

¿Cómo llegamos a los elementos individuales? `SimpleXMLElement` se comporta como un objeto PHP normal: cada elemento secundario se convierte en una propiedad accesible con la flecha `->`. Además, el objeto tiene un iterador interno, por lo que podemos recorrerlo con `foreach` como si fuera una array.

Al observar la estructura del feed, sabemos que dentro de `channel` están `title` y `description`. Para leer el título y descripción del canal solo escribe:

```php
echo $xml->channel->title;       // SitePoint
echo $xml->channel->description; // la descripción del feed
```

Código completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/es/parte-04/cap-16/listing-06.php)


Tenga en cuenta que `$xml` representa el elemento raíz del documento (`rss`), por lo que para descender en el árbol comenzamos desde allí: `$xml->channel->title`, `$xml->channel->description`, y así sucesivamente.

Los artículos, por otro lado, son los muchos elementos `item` dentro de `channel`. `$xml->channel->item` se comporta como una array de elementos, por lo que lo repetimos con `foreach` y para cada artículo imprimimos el título y el enlace:

```php
foreach ($xml->channel->item as $item) {
    echo $item->title;
    echo '<br>';
    echo $item->link;
    echo '<br>';
}
```

Código completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/es/parte-04/cap-16/listing-07.php)


Al iniciar el script, vemos los títulos y enlaces de todos los artículos en el desplazamiento del feed. El resultado todavía no es agradable de ver (no lo hemos formateado en HTML), pero lo esencial está ahí: accedemos a los valores XML desde PHP.

## Creación de una página web a partir de un feed XML

Ahora que la lectura funciona, hagamos un pequeño proyecto: una página HTML que muestre los artículos del feed como un minisitio de noticias real.

Mantenemos el bucle `foreach` que acabamos de escribir, que necesitaremos, y construimos la estructura HTML a su alrededor: el tipo de documento, el encabezado con `head` y la etiqueta `body`. Dentro de `body` ponemos una etiqueta `section` que contendrá todo el feed: el título principal del sitio en un `h1`, la descripción en un `div` con una clase `description` (para que podamos formatearla vía CSS), y luego una etiqueta `article` para cualquier novedad.

Para el bucle es mejor usar la **sintaxis alternativa** de `foreach` (`foreach (…): … endforeach;`), que vimos en el Capítulo 9: cuando mezclas PHP y HTML hace que la plantilla sea mucho más legible. Y para imprimir los valores usamos la **etiqueta de eco corta** `<?= … ?>`, la forma corta de `echo`.

Aquí está la página completa:

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
    <title>El feed de SitePoint</title>
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

Código completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/es/parte-04/cap-16/listing-08.php)


Algunos comentarios sobre el marcado:

- El título de cada artículo va en un `h3` dentro de la etiqueta `article`.
- Los datos del artículo están en una lista desordenada: el primer `li` contiene el enlace. Si simplemente imprimimos `<?= $item->link ?>` tendríamos la URL como texto sin formato; para que se pueda hacer clic en él, lo envolvemos en una etiqueta `a`, usando el mismo valor tanto en el atributo `href` como como texto visible. El atributo `target="_blank"` abre el artículo en otra pestaña.
- El segundo `li` contiene la descripción del artículo. El feed también ofrecería otros campos (fecha de publicación, comentarios) que puede agregar con el mismo patrón.
- Después de cada `article` una `hr` (una línea horizontal) separa visualmente un artículo del otro.

Recargar la página: en unos minutos creamos un mini sitio web con el feed de otro sitio. Está el título principal, la descripción del feed y luego cada artículo con título, enlace en el que se puede hacer clic y texto. De ahora en adelante todo es cuestión de CSS: puedes adjuntar una hoja de estilo y formatear `h1`, `article` y `.description` para hacer la página más agradable: un gran ejercicio si quieres repasar HTML y CSS.
### simplexml_load_file: todo en un solo paso

Hasta ahora hemos realizado dos pasos: primero `file_get_contents()` para leer el contenido, luego `simplexml_load_string()` para interpretarlo. Hay una función más conveniente que los combina: **`simplexml_load_file()`**. Le pasas la ruta del archivo o la URL directamente y PHP hace el resto:

```php
// $content = file_get_contents($url);
// $xml = simplexml_load_string($content);

$xml = simplexml_load_file($url);
```

Código completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/es/parte-04/cap-16/listing-09.php)


El funcionamiento es idéntico, con una única función. Esta es la forma que normalmente utilizará para leer un XML, ya sea que esté fuera de su sitio o en su carpeta local: `simplexml_load_file()` devuelve directamente el `SimpleXMLElement` para que se bucle.

### Las otras funciones de SimpleXML

Si busca "SimpleXML" en el manual de PHP encontrará todas las funciones y métodos disponibles. Además de navegar por el árbol, puedes manipularlo: agregar atributos, leer los atributos de un elemento con el método `attributes()`, recorrer los elementos secundarios con `children()`, obtener el nombre de un elemento con `getName()`, trabajar con namespace.

Un método particularmente útil es `asXML()`, que serializa el elemento (con su subárbol completo) de nuevo a XML. Si le da un nombre de archivo, lo guarda directamente en el disco:

```php
$xml->asXML('sitepoint.xml');
```

Código completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/es/parte-04/cap-16/listing-10.php)


Después de la ejecución, el archivo `sitepoint.xml` aparece en la carpeta del script con toda la estructura del feed: transformamos el objeto `SimpleXMLElement` nuevamente en un archivo XML. En este caso específico podríamos haber obtenido el mismo resultado guardando la cadena `file_get_contents()`, pero `asXML()` se vuelve valioso cuando *modificas* el árbol antes de guardarlo.

### Advertencia: los elementos no son cadenas

Una última cosa importante. Elementos como `$item->title` *parecen* cadenas, pero no lo son: son en sí mismos objetos `SimpleXMLElement`. Intente insertar un `var_dump($item->title)` en el bucle y verá:

```text
object(SimpleXMLElement)#5 (1) {
  [0]=>
  string(28) "Título del primer artículo…"
}
```

Código completo: [listing-11.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/es/parte-04/cap-16/listing-11.txt)


Cuando hacemos `echo`, PHP llama automáticamente al método `__toString()` del objeto y lo convierte en una cadena, por lo que todo funciona sin que nos demos cuenta. Pero si necesita asignar el valor a una variable, guardarlo en una base de datos o pasarlo a una función que espera una cadena, siempre es mejor convertirlo explícitamente a una cadena:

```php
$title = (string) $item->title;
```

Código completo: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/es/parte-04/cap-16/listing-12.php)


Así que está claro que estás guardando una cadena y no un objeto `SimpleXMLElement`, un hábito que te ahorrará más de un error.

## Crear un documento XML con DOM

Pasemos ahora al camino inverso: generar un archivo XML con PHP. El escenario es el siguiente: tenemos una serie de películas (imagínese que simplemente las leemos de la base de datos) y queremos producir un archivo XML para entregárselo a nuestros usuarios o para que lo descarguen.

```php
<?php
$films = [
    [
        'title'    => 'Batman',
        'year'     => 1989,
        'director' => 'Tim Burton',
        'plot'     => 'El Caballero Oscuro defiende Gotham City del Joker.',
    ],
    [
        'title'    => 'Alien',
        'year'     => 1979,
        'director' => 'Ridley Scott',
        'plot'     => "La tripulación del Nostromo se enfrenta a una criatura letal.",
    ],
];
```

Código completo: [listing-13.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/es/parte-04/cap-16/listing-13.php)


### Documento DOM

Lo primero que debemos hacer es crear un documento tipo DOM con la clase **`DOMDocument`**. El primer parámetro del constructor es la versión XML (`1.0`), el segundo el conjunto de caracteres (`utf-8`):

```php
$dom = new DOMDocument('1.0', 'utf-8');
```

Código completo: [listing-14.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/es/parte-04/cap-16/listing-14.php)


Ya con esta única línea tenemos un árbol DOM. Luego, un árbol DOM se puede serializar como XML, HTML o guardar en un archivo. Comprobemos inmediatamente qué contiene con el método `saveXML()`, que genera la cadena XML del documento y la devuelve:

```php
var_dump($dom->saveXML());
```

Código completo: [listing-15.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/es/parte-04/cap-16/listing-15.php)


```text
string(39) "<?xml version="1.0" encoding="utf-8"?>
"
```

Código completo: [listing-16.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/es/parte-04/cap-16/listing-16.txt)


La declaración XML con versión y codificación ya está ahí: el documento existe, pero está vacío. Estamos en un buen punto.

Una nota antes de continuar: los métodos que vamos a utilizar (`createElement()`, `createTextNode()`, `appendChild()`) no son una invención de PHP. Son los métodos del **DOM estándar**, exactamente los mismos que usas en JavaScript para crear o manipular un documento HTML, y que también encuentras en Java. Lo que aprenda aquí lo reutilizará en otros lugares.

### Crea el elemento raíz

Un documento XML debe tener un elemento raíz. Lo creamos con el método `createElement()` del documento, dándole el nombre del elemento; para nuestra colección de películas lo llamamos `movies`:

```php
$root = $dom->createElement('movies');
```

Código completo: [listing-17.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/es/parte-04/cap-16/listing-17.php)


Sin embargo, si ahora reiniciamos el script, la raíz todavía no aparece en el XML. ¿Por qué? Porque lo *creamos*, pero no lo *adjuntamos* al documento. En el DOM, crear un nodo e insertarlo en el árbol son siempre dos operaciones distintas. Para engancharlo usamos `appendChild()` (literalmente "colgar a un niño") en el documento:

```php
$dom->appendChild($root);
```

Código completo: [listing-18.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/es/parte-04/cap-16/listing-18.php)


Ahora sí: la salida muestra el elemento `movies`, vacío, debajo de la declaración.

### Llena el árbol con bucles.
Ahora tenemos que escribir tantos elementos en la raíz como películas haya en la array. El plan es: para cada película creamos un elemento `movie`, y dentro de cada `movie` un elemento para cada campo (`title`, `year`, `director`, `plot`) con su contenido textual.

`$films` es una array de arrays, por lo que necesitamos dos bucles anidados. En el bucle exterior nos desplazamos por las películas; en el bucle interno nos desplazamos por los pares clave/valor de una sola película: en la primera iteración la clave será `title` y el valor `Batman`, luego `year` y `1989`, y así sucesivamente.

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

Código completo: [listing-19.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/es/parte-04/cap-16/listing-19.php)


Sigamos el flujo paso a paso:

1. **`$movie = $dom->createElement('movie')`** — para cada película creamos el elemento contenedor. Podríamos haberlo llamado `item` o `film`: en XML decidimos el nombre.
2. **`$element = $dom->createElement($tag)`** — en el bucle interno creamos un elemento para cada campo. Aquí el nombre es *dinámico*: pasamos la variable `$tag`, que contiene las claves del array (`title`, `year`…).
3. **`$text = $dom->createTextNode($value)`**: el contenido textual de un elemento es en sí mismo un nodo, un **nodo de texto**, y se crea con `createTextNode()` pasando la cadena.
4. **`$element->appendChild($text)`**: agregamos el nodo de texto al elemento: `createElement()` devuelve un objeto de elemento, que también tiene el método `appendChild()`.
5. **`$movie->appendChild($element)`** — adjuntamos el elemento completo (etiqueta más texto) a la película.
6. **`$root->appendChild($movie)`** — al final de cada vuelta del bucle exterior, cuando la película esté completa, la colgamos en la raíz. Si olvida este paso, los nodos existen pero nunca ingresan al árbol del documento.

Un consejo práctico que nace de un error muy fácil de cometer: prestar atención a los nombres de las variables en los bucles anidados. Si llama al elemento contenedor `$film`, el mismo nombre de variable que el `foreach` externo, en cada iteración interna lo sobrescribe y el resultado es un árbol vacío o incorrecto. Por eso el contenedor aquí se llama `$movie`: nombres distintos, sin colisiones.

Hagamos una comprobación `var_dump($dom->saveXML())`: no está bien formateado, pero se puede ver que se ha creado el elemento raíz `movies`, dentro están los elementos `movie`, y dentro de cada uno los elementos `title`, `year`, `director` y `plot`. El árbol está completo.

## Enviar al navegador y guardar el archivo XML

El `var_dump()` está bien para la depuración, pero ahora queremos entregar el XML correctamente.

### Enviar el XML al navegador

Reemplazamos el volcado con un `echo` de la cadena XML, pero primero le decimos al navegador qué le estamos enviando, enviando un encabezado `Content-Type` apropiado:

```php
header('Content-Type: text/xml');
echo $dom->saveXML();
```

Código completo: [listing-20.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/es/parte-04/cap-16/listing-20.php)


Recuerde del Capítulo 6 que `echo` es una construcción del lenguaje y no necesita paréntesis. Con el encabezado configurado, el navegador sabe que está recibiendo XML: lo interpreta y lo formatea como un árbol, exactamente como lo hizo con el feed de SitePoint. El resultado:

```xml
<?xml version="1.0" encoding="utf-8"?>
<movies>
  <movie>
    <title>Batman</title>
    <year>1989</year>
    <director>Tim Burton</director>
    <plot>El Caballero Oscuro defiende Gotham City del Joker.</plot>
  </movie>
  <movie>
    <title>Alien</title>
    <year>1979</year>
    <director>Ridley Scott</director>
    <plot>La tripulación del Nostromo se enfrenta a una criatura letal.</plot>
  </movie>
</movies>
```

Código completo: [listing-21.xml](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/es/parte-04/cap-16/listing-21.xml)


Hay dos elementos `movie`, como los elementos de la array; cada uno contiene su propio `title`, `year`, `director` y `plot`, creados dinámicamente por el bucle interno a partir de las claves de la array. De la array PHP al documento XML: misión cumplida.

### Guardar en archivo: el método de guardar

Para guardar el documento en disco en lugar de (o además de) enviarlo al navegador, existe el método `save()`, al que le pasamos el nombre del archivo:

```php
$dom->save('my_movies.xml');
```

Código completo: [listing-22.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/es/parte-04/cap-16/listing-22.php)


Reiniciamos el script y aparece `my_movies.xml` en la carpeta: al abrirlo en el editor encontramos nuestro XML, listo para ser descargado o distribuido.

En el manual de PHP, en la página `DOMDocument`, encontrará todos los demás métodos disponibles: crear comentarios y referencias, cargar un documento HTML existente en el DOM con `loadHTML()` para manipular su árbol, cargar un archivo XML con `load()` y procesarlo, y luego guardarlo nuevamente. Los métodos que utilizamos (`createElement()`, `createTextNode()`, `appendChild()`, `saveXML()`, `save()`) son los principales: una vez que se entienden, los demás se pueden aprender rápidamente a partir de la documentación.

### Los atributos de los elementos.
Los elementos DOM también tienen sus propios métodos, documentados en la página `DOMElement`: puedes leer un atributo con `getAttribute()`, verificar si existe con `hasAttribute()` y configurarlo con **`setAttribute()`**, que recibe el nombre del atributo y su valor. Por ejemplo, podemos darle a cada elemento `movie` un atributo `id`:

```php
$id = 1;

foreach ($films as $film) {
    $movie = $dom->createElement('movie');
    $movie->setAttribute('id', $id++);
    // …resto del ciclo…
}
```

Código completo: [listing-23.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-16/es/parte-04/cap-16/listing-23.php)


Y en la salida cada película se convierte en `<movie id="1">`, `<movie id="2">` y así sucesivamente. XML es gratuito: puedes poner cualquier nombre de atributo en cualquier elemento.

Esto abre una pregunta *estructural*: ¿el año de una película debería ser un elemento `<year>` o un atributo `year="1989"` de la etiqueta `movie`? No existe una respuesta absolutamente correcta, es una elección de diseño del documento. Mi consejo, después de años de archivos XML: prefiera elementos y reserve atributos para los pocos puntos de datos que son verdaderamente "metadatos" de un elemento (como un `id`). Un XML compuesto de elementos también es más fácil de manipular mediante código que uno cargado de atributos.

Termino con una observación honesta: los archivos XML son un formato que está algo en declive. Hoy en día, casi todas las API (desde las redes sociales hacia abajo) devuelven datos en **JSON**, un formato que ocupa menos espacio y es igualmente multiplataforma: valores clave-valor entre comillas, con llaves en lugar de etiquetas. Sin embargo, XML sigue siendo indispensable para feeds, mapas de sitios y muchos sistemas empresariales. Y JSON es exactamente de lo que trata el próximo capítulo.

## En resumen

- **XML** representa los datos como un árbol de elementos (el **DOM**, modelo de objetos de documento): una declaración `<?xml … ?>`, un único elemento raíz y etiquetas libres, inventadas por quien diseña el documento, con cualquier atributo.
- **SimpleXML** lee un
- Un `SimpleXMLElement` se navega con la flecha (`$xml->channel->title`) y se cicla con `foreach` (`$xml->channel->item`); el método `asXML()` lo vuelve a serializar en XML, incluso en un archivo.
- Los elementos SimpleXML **no son cadenas**: `echo` los convierte automáticamente, pero al guardarlos en variables o bases de datos siempre convierte explícitamente `(string)`.
- Para crear un
- `saveXML()` devuelve la cadena XML (que se enviará al navegador con el encabezado `Content-Type: text/xml`), `save()` escribe el archivo en el disco; `setAttribute()` agrega atributos a los elementos.
- Los métodos DOM son un estándar: los mismos que usas en PHP son idénticos en JavaScript y Java.
