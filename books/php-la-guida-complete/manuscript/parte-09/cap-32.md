# 32. Router, PSR-7/15, controller e view

Il router è il punto in cui una richiesta HTTP diventa codice applicativo: è lì che l'URL digitato nel browser si trasforma nella decisione "quale pezzo di codice deve rispondere". Nel vecchio stile — quello dello User Management System della Parte VI — potresti leggere `$_SERVER["REQUEST_URI"]` direttamente in `index.php` e scegliere a mano quale file includere. Funziona, ma non regge la crescita. Nel progetto enterprise seguiamo una progressione in due tempi che vale la pena notare come *metodo*, non solo come risultato: prima costruiamo un router piccolo e testabile, per capire davvero cosa fa un router; poi lo sostituiamo con componenti standard PSR-7/15, per non reinventare ciò che l'ecosistema PHP ha già risolto. Costruire prima, adottare lo standard dopo: si impara molto più così che partendo da una libreria magica.

![Il progetto *freeblog* originale del corso Udemy — un MVC scritto a mano, con front controller e router minimale. È l'applicazione che la Parte IX ricostruisce con un'architettura enterprise: stessa funzionalità, presentazione volutamente essenziale.](figures/cap-32/free-mvc-post-list.png)

## Scrivere prima il contratto

Nel tag `lesson-1-3` il porting non parte dal codice, ma dal **test**. È una scelta precisa: il test scritto per primo definisce cosa il router deve fare, prima ancora di come.

```php
<?php

declare(strict_types=1);

public function testParameterizedMatchExtractsParams(): void
{
    $router = new Router($this->routes());

    $this->assertSame(
        ['Ctrl', 'show', ['42']],
        $router->dispatch('GET', '/posts/42')
    );
}
```

Codice completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-32/it/parte-09/cap-32/listing-01.php)


Sorgente reale: [`tests/Unit/Http/RouterTest.php` a `lesson-1-3`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-3/tests/Unit/Http/RouterTest.php).


Leggi cosa afferma il test: dato `dispatch('GET', '/posts/42')`, si aspetta indietro `['Ctrl', 'show', ['42']]` — cioè il controller, il metodo e i parametri estratti dall'URL. Questo chiarisce, senza ambiguità, la **responsabilità** del router: tradurre una coppia `(metodo, URI)` in un handler. E chiarisce altrettanto bene ciò che il router **non** fa: non renderizza HTML, non legge il database, non costruisce controller. È il principio di singola responsabilità reso concreto — una classe, un compito — e il test lo fissa come un contratto prima ancora che il codice esista.

## Un router piccolo

La prima implementazione soddisfa quel test con una manciata di righe e una espressione regolare:

```php
<?php

declare(strict_types=1);

final class Router
{
    public function dispatch(string $method, string $uri): array
    {
        foreach ($this->routes[$method] ?? [] as $path => $handler) {
            $pattern = '#^' . preg_replace('/:([A-Za-z_][A-Za-z0-9_]*)/', '([^/]+)', trim($path, '/')) . '$#';

            if (preg_match($pattern, trim($uri, '/'), $matches)) {
                array_shift($matches);
                return [$handler[0], $handler[1], $matches];
            }
        }

        throw new RouteNotFoundException("No route for {$method} {$uri}");
    }
}
```

Codice completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-32/it/parte-09/cap-32/listing-02.php)


Sorgente reale: [`src/Http/Router.php` a `lesson-1-3`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-3/src/Http/Router.php).


Segui la logica: per ogni rotta registrata sotto quel metodo HTTP, il router trasforma un pattern come `posts/:id` in un'espressione regolare, sostituendo `:id` con un gruppo di cattura `([^/]+)`. Se l'URI corrisponde, estrae i parametri catturati (l'`array_shift` scarta la corrispondenza completa, tenendo solo i gruppi) e restituisce la terna `[controller, metodo, parametri]`. Se nessuna rotta corrisponde, lancia `RouteNotFoundException` — che diventerà una risposta 404. È intenzionalmente semplice, e la semplicità è il punto: capire che un router, sotto il cofano, è solo un abbinamento di pattern, ti toglie ogni timore reverenziale verso le librerie di routing che userai dopo.

## Request e Response tipizzate

Nel tag `lesson-1-9` cambia un altro confine importante. La richiesta non viene più letta ovunque, sparpagliando `$_POST` e `$_SERVER` per tutto il codice: entra una volta sola in una classe che la rappresenta.

```php
<?php

declare(strict_types=1);

final class Request
{
    public function __construct(
        public readonly string $method,
        public readonly string $uri,
        public readonly array $query,
        public readonly array $post,
        public readonly array $headers,
    ) {
    }

    public function postString(string $key, string $default = ''): string
    {
        $value = $this->post[$key] ?? $default;
        return is_array($value) ? $default : (string) $value;
    }
}
```

Codice completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-32/it/parte-09/cap-32/listing-03.php)


Sorgente reale: [`src/Http/Request.php` a `lesson-1-9`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-9/src/Http/Request.php).


È ancora una classe scritta da noi, ma disegna un **confine** corretto. I superglobali — quei `$_POST`, `$_GET`, `$_SERVER` che nella Parte VI comparivano ovunque — vengono letti in un unico punto, all'ingresso, e trasformati in un oggetto esplicito e immutabile (nota i `readonly` del Capitolo 25). Da lì in poi il resto dell'applicazione non tocca più i superglobali: riceve un `Request`, con proprietà tipizzate e metodi come `postString()` che leggono i dati in modo sicuro, restituendo un default se la chiave manca o non è una stringa. È la differenza tra un'applicazione dove l'input grezzo penetra ovunque e una dove entra da una porta sola, controllata.

## Il salto a PSR-7/15

Costruito il concetto con le nostre mani, il progetto compie il passo che lo rende professionale: adottare gli standard condivisi.

```bash
composer require league/route:^6.2 nyholm/psr7:^1.8 nyholm/psr7-server:^1.1
```

Codice completo: [listing-04.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-32/it/parte-09/cap-32/listing-04.sh)


Sorgente reale: [`composer.json` a `lesson-1-15`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-15/composer.json).


I **PSR** (PHP Standard Recommendations) sono interfacce condivise dall'intera comunità PHP. PSR-7 definisce come devono essere fatti gli oggetti request e response; PSR-15 definisce gli handler e i middleware. Adottandoli, il nostro `Router` non è più un oggetto isolato: diventa un `RequestHandlerInterface`, un tipo che tutto l'ecosistema riconosce.

```php
<?php

declare(strict_types=1);

final class Router implements RequestHandlerInterface
{
    private readonly LeagueRouter $router;

    public function handle(ServerRequestInterface $request): ResponseInterface
    {
        return $this->router->handle($request);
    }
}
```

Codice completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-32/it/parte-09/cap-32/listing-05.php)


Sorgente reale: [`src/Http/Router.php` a `lesson-1-15`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-15/src/Http/Router.php).


Il routing resta leggibile quanto prima, ma il guadagno è enorme e forse non ovvio: **interoperabilità**. Poiché il router accetta un `ServerRequestInterface` e restituisce una `ResponseInterface` — tipi standard, non nostri — qualunque middleware PSR-15 scritto da terzi (per l'autenticazione, il logging, la gestione CORS, il rate limiting) può inserirsi nel progetto senza adattatori strani. Programmare contro le interfacce standard, esattamente come predicava il Capitolo 26 con la "D" di SOLID, ti apre l'accesso a un intero ecosistema di componenti già scritti e testati.

## Kernel e container

Chi mette in moto tutta questa macchina? Il **Kernel**, il punto di avvio dell'applicazione:

```php
<?php

declare(strict_types=1);

public function handle(): void
{
    $this->loadEnv();
    session_start();

    $container = $this->buildContainer();
    $request = $this->buildRequest();

    $response = $container->get(Router::class)->handle($request);

    $this->emit($response);
}
```

Codice completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-32/it/parte-09/cap-32/listing-06.php)


Sorgente reale: [`src/Kernel.php` a `lesson-1-15`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-15/src/Kernel.php).


Il metodo `handle()` si legge come la sequenza esatta di ogni richiesta: carica le variabili d'ambiente dal `.env` (le credenziali che nella Parte VI stavano in chiaro nel codice, ora fuori dal repository), apre la sessione, costruisce il **container**, crea la request PSR-7, la passa al router e infine emette la response. Il pezzo centrale è il container: un registro che sa costruire e collegare tra loro `PDO`, repository, servizi e view. È lui a realizzare la *dependency injection* di cui parliamo dal Capitolo 25: quando serve un `Router`, il container lo crea fornendogli tutto ciò di cui ha bisogno, ricorsivamente. Il controller, di conseguenza, non costruisce più da solo le proprie dipendenze — non fa `new PDO(...)` al suo interno — ma le **riceve** nel costruttore, già pronte. Questo è ciò che rende ogni pezzo testabile in isolamento: puoi passargli un finto repository e verificarne il comportamento senza un database vero.

## Controller sottili

Con le dipendenze iniettate, il controller può fare la sua unica cosa: **coordinare**, non contenere la logica.

```php
<?php

declare(strict_types=1);

public function show(ServerRequestInterface $request, array $args = []): ResponseInterface
{
    $post = $this->posts->findById((int) ($args['id'] ?? 0));

    if ($post === null) {
        return $this->respond($this->view->render('pages/errors/404'), 404);
    }

    return $this->respond($this->view->render('pages/posts/show', [
        'post' => $post,
        'comments' => $this->comments->allForPost($post->id),
    ]));
}
```

Codice completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-32/it/parte-09/cap-32/listing-07.php)


Sorgente reale: [`src/Controllers/PostController.php` a `lesson-1-15`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-15/src/Controllers/PostController.php).


Osserva il flusso, perché è il modello di quasi ogni azione MVC: prendi il parametro dalla rotta (`id`), chiedi il dato al repository (`findById`), gestisci il caso "non trovato" con un 404, altrimenti chiedi alla view di renderizzare la pagina passandole i dati (`post`, `comments`). Il controller non contiene una riga di SQL né una riga di HTML: **coordina** repository e view, e restituisce una response. È la separazione dei ruoli che nella Parte VI intravedevi come convenzione (controller e view in file separati) e che qui diventa architettura: niente SQL nella view, niente HTML nel repository. Un controller "sottile" è facile da leggere perché racconta *cosa* succede, delegando il *come* ai livelli sottostanti.

## View con escaping

L'ultimo tassello è la view, che resta un file PHP ma viene renderizzata da un oggetto dedicato:

```php
<?php

declare(strict_types=1);

final class View
{
    public function render(string $template, array $data = []): string
    {
        $file = $this->viewsDir . '/' . $template . '.tpl.php';
        extract($data, EXTR_OVERWRITE);

        ob_start();
        require $file;

        return (string) ob_get_clean();
    }
}
```

Codice completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-32/it/parte-09/cap-32/listing-08.php)


Sorgente reale: [`src/Support/View.php` a `lesson-1-9`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-9/src/Support/View.php).


Il metodo `render()` fa una cosa elegante con l'*output buffering*: `extract()` trasforma le chiavi dell'array `$data` in variabili locali (così nel template puoi scrivere `$post` invece di `$data['post']`), `ob_start()` inizia a catturare l'output, `require` esegue il template PHP, e `ob_get_clean()` restituisce l'HTML prodotto come stringa invece di sputarlo subito. La view diventa così un componente che *ritorna* una stringa, componibile e testabile. Ma la riga più importante è nell'uso: dentro i template, ogni dato dell'utente si stampa con `htmlspecialchars(..., ENT_QUOTES, 'UTF-8')`. È il collegamento diretto con lo User Management System e il Capitolo 20: qualunque valore salvato da un utente — il titolo di un post, un commento — può diventare un attacco **XSS** se lo stampi senza escaping. L'architettura enterprise non ti dispensa dalla sicurezza di base: la incorpora, mettendo l'escaping nel punto esatto in cui l'output raggiunge il browser.

![La stessa lista di post prodotta dal blog enterprise: la catena router → controller → repository → view genera l'output, e la view lo rende con `htmlspecialchars`. Confronta l'impaginazione con la versione *freeblog* a inizio capitolo.](figures/cap-32/enterprise-blog-post-list.png)

## In sintesi

Questo capitolo non insegna soltanto "un router": insegna una **progressione**. Prima il comportamento minimo definito da un test, poi oggetti request/response che disciplinano il confine con l'input grezzo, infine PSR-7/15 e un container che inietta le dipendenze. Attorno a questo nucleo, controller sottili che coordinano e view che rendono con escaping. È lo stesso MVC che intravedevi nella Parte VI, ma con i confini giusti — ogni livello con una responsabilità sola, ogni pezzo testabile in isolamento, ogni componente aperto all'ecosistema tramite gli standard. È la forma che un'applicazione assume quando deve non solo funzionare, ma **crescere**.
