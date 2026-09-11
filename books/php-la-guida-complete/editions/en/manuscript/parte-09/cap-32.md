# 32. Router, PSR-7/15, controllers and views

The router is the point where an HTTP request becomes application code: it is there that the URL typed into the browser turns into the decision "which piece of code should answer". In the old style — that of the User Management System of Part VI — you might read `$_SERVER["REQUEST_URI"]` directly in `index.php` and choose by hand which file to include. It works, but it does not withstand growth. In the enterprise project we follow a two-step progression worth noticing as a *method*, not just as a result: first we build a small, testable router, to truly understand what a router does; then we replace it with standard PSR-7/15 components, so as not to reinvent what the PHP ecosystem has already solved. Build first, adopt the standard later: you learn far more this way than by starting from a magic library.

![The original *freeblog* project from the Udemy course — a hand-written MVC with a front controller and a minimal router. It is the application Part IX rebuilds with an enterprise architecture: same features, deliberately plain presentation.](figures/cap-32/free-mvc-post-list.png)

## Write the contract first

At tag `lesson-1-3` the port does not start from the code, but from the **test**. It is a deliberate choice: the test written first defines what the router must do, before even how.

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

Full source: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-32/en/parte-09/cap-32/listing-01.php)


Real source: [`tests/Unit/Http/RouterTest.php` at `lesson-1-3`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-3/tests/Unit/Http/RouterTest.php).


Read what the test asserts: given `dispatch('GET', '/posts/42')`, it expects back `['Ctrl', 'show', ['42']]` — that is, the controller, the method and the parameters extracted from the URL. This clarifies, without ambiguity, the router's **responsibility**: to translate a `(method, URI)` pair into a handler. And it clarifies just as well what the router does **not** do: it does not render HTML, does not read the database, does not build controllers. It is the single responsibility principle made concrete — one class, one job — and the test fixes it as a contract before the code even exists.

## A small router

The first implementation satisfies that test with a handful of lines and a regular expression:

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

Full source: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-32/en/parte-09/cap-32/listing-02.php)


Real source: [`src/Http/Router.php` at `lesson-1-3`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-3/src/Http/Router.php).


Follow the logic: for each route registered under that HTTP method, the router turns a pattern like `posts/:id` into a regular expression, replacing `:id` with a capture group `([^/]+)`. If the URI matches, it extracts the captured parameters (the `array_shift` discards the full match, keeping only the groups) and returns the triple `[controller, method, parameters]`. If no route matches, it throws `RouteNotFoundException` — which will become a 404 response. It is intentionally simple, and the simplicity is the point: understanding that a router, under the hood, is just pattern matching removes any reverential awe of the routing libraries you will use later.

## Typed Request and Response

At tag `lesson-1-9` another important boundary changes. The request is no longer read everywhere, scattering `$_POST` and `$_SERVER` throughout the code: it enters once into a class that represents it.

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

Full source: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-32/en/parte-09/cap-32/listing-03.php)


Real source: [`src/Http/Request.php` at `lesson-1-9`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-9/src/Http/Request.php).


It is still a class written by us, but it draws a correct **boundary**. The superglobals — those `$_POST`, `$_GET`, `$_SERVER` that in Part VI appeared everywhere — are read at a single point, at the entrance, and turned into an explicit, immutable object (note the `readonly` from Chapter 25). From there on the rest of the application no longer touches the superglobals: it receives a `Request`, with typed properties and methods like `postString()` that read the data safely, returning a default if the key is missing or is not a string. It is the difference between an application where raw input penetrates everywhere and one where it enters through a single, controlled door.

## The jump to PSR-7/15

Having built the concept with our own hands, the project takes the step that makes it professional: adopting shared standards.

```bash
composer require league/route:^6.2 nyholm/psr7:^1.8 nyholm/psr7-server:^1.1
```

Full source: [listing-04.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-32/en/parte-09/cap-32/listing-04.sh)


Real source: [`composer.json` at `lesson-1-15`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-15/composer.json).


The **PSRs** (PHP Standard Recommendations) are interfaces shared by the entire PHP community. PSR-7 defines how request and response objects should be shaped; PSR-15 defines handlers and middleware. By adopting them, our `Router` is no longer an isolated object: it becomes a `RequestHandlerInterface`, a type the whole ecosystem recognizes.

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

Full source: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-32/en/parte-09/cap-32/listing-05.php)


Real source: [`src/Http/Router.php` at `lesson-1-15`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-15/src/Http/Router.php).


Routing stays as readable as before, but the gain is enormous and perhaps not obvious: **interoperability**. Because the router accepts a `ServerRequestInterface` and returns a `ResponseInterface` — standard types, not ours — any PSR-15 middleware written by third parties (for authentication, logging, CORS handling, rate limiting) can slot into the project without odd adapters. Programming against standard interfaces, exactly as Chapter 26 preached with the "D" of SOLID, opens you access to a whole ecosystem of already-written and tested components.

## Kernel and container

Who sets this whole machine in motion? The **Kernel**, the application's starting point:

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

Full source: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-32/en/parte-09/cap-32/listing-06.php)


Real source: [`src/Kernel.php` at `lesson-1-15`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-15/src/Kernel.php).


The `handle()` method reads like the exact sequence of every request: it loads the environment variables from `.env` (the credentials that in Part VI sat in clear text in the code, now outside the repository), opens the session, builds the **container**, creates the PSR-7 request, passes it to the router, and finally emits the response. The central piece is the container: a registry that knows how to build and wire together `PDO`, repositories, services and views. It is what realizes the *dependency injection* we have been talking about since Chapter 25: when a `Router` is needed, the container creates it by providing everything it needs, recursively. The controller, as a result, no longer builds its own dependencies — it does not do `new PDO(...)` inside itself — but **receives** them in the constructor, ready-made. This is what makes each piece testable in isolation: you can hand it a fake repository and verify its behavior without a real database.

## Thin controllers

With dependencies injected, the controller can do its one thing: **coordinate**, not hold the logic.

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

Full source: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-32/en/parte-09/cap-32/listing-07.php)


Real source: [`src/Controllers/PostController.php` at `lesson-1-15`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-15/src/Controllers/PostController.php).


Observe the flow, because it is the template of almost every MVC action: take the parameter from the route (`id`), ask the repository for the data (`findById`), handle the "not found" case with a 404, otherwise ask the view to render the page passing it the data (`post`, `comments`). The controller contains not a line of SQL nor a line of HTML: it **coordinates** repository and view, and returns a response. It is the separation of roles that in Part VI you glimpsed as a convention (controller and view in separate files) and that here becomes architecture: no SQL in the view, no HTML in the repository. A "thin" controller is easy to read because it tells *what* happens, delegating the *how* to the layers beneath.

## Views with escaping

The last piece is the view, which remains a PHP file but is rendered by a dedicated object:

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

Full source: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-32/en/parte-09/cap-32/listing-08.php)


Real source: [`src/Support/View.php` at `lesson-1-9`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-9/src/Support/View.php).


The `render()` method does something elegant with *output buffering*: `extract()` turns the keys of the `$data` array into local variables (so in the template you can write `$post` instead of `$data['post']`), `ob_start()` begins capturing the output, `require` runs the PHP template, and `ob_get_clean()` returns the produced HTML as a string instead of spitting it out immediately. The view thus becomes a component that *returns* a string, composable and testable. But the most important line is in its use: inside the templates, every piece of user data is printed with `htmlspecialchars(..., ENT_QUOTES, 'UTF-8')`. It is the direct link with the User Management System and Chapter 20: any value saved by a user — a post's title, a comment — can become an **XSS** attack if you print it without escaping. Enterprise architecture does not exempt you from basic security: it incorporates it, putting the escaping at the exact point where output reaches the browser.

![The same post list produced by the enterprise blog: the router → controller → repository → view chain generates the output, and the view renders it with `htmlspecialchars`. Compare the layout with the *freeblog* version at the start of the chapter.](figures/cap-32/enterprise-blog-post-list.png)

## In summary

This chapter does not teach only "a router": it teaches a **progression**. First the minimum behavior defined by a test, then request/response objects that discipline the boundary with raw input, finally PSR-7/15 and a container that injects the dependencies. Around this core, thin controllers that coordinate and views that render with escaping. It is the same MVC you glimpsed in Part VI, but with the right boundaries — each layer with a single responsibility, each piece testable in isolation, each component open to the ecosystem through the standards. It is the form an application takes when it must not only work, but **grow**.
