# 32. Router, PSR-7/15, controllers y views

El router es el punto donde una request HTTP se convierte en código de aplicación: es ahí donde la URL escrita en el navegador se transforma en la decisión "qué pieza de código debe responder". En el estilo antiguo — el del User Management System de la Parte VI — podrías leer `$_SERVER["REQUEST_URI"]` directamente en `index.php` y elegir a mano qué fichero incluir. Funciona, pero no resiste el crecimiento. En el proyecto enterprise seguimos una progresión en dos pasos que conviene notar como *método*, no solo como resultado: primero construimos un router pequeño y testeable, para entender de verdad qué hace un router; luego lo reemplazamos con componentes estándar PSR-7/15, para no reinventar lo que el ecosistema PHP ya ha resuelto. Construir primero, adoptar el estándar después: se aprende mucho más así que partiendo de una librería mágica.

![El proyecto *freeblog* original del curso de Udemy — un MVC escrito a mano, con front controller y un router mínimo. Es la aplicación que la Parte IX reconstruye con una arquitectura enterprise: la misma funcionalidad, con una presentación deliberadamente básica.](figures/cap-32/free-mvc-post-list.png)

## Escribir primero el contrato

En el tag `lesson-1-3` el port no parte del código, sino del **test**. Es una elección deliberada: el test escrito primero define qué debe hacer el router, antes incluso que cómo.

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

Código completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-32/es/parte-09/cap-32/listing-01.php)


Fuente real: [`tests/Unit/Http/RouterTest.php` en `lesson-1-3`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-3/tests/Unit/Http/RouterTest.php).


Lee lo que afirma el test: dado `dispatch('GET', '/posts/42')`, espera de vuelta `['Ctrl', 'show', ['42']]` — es decir, el controller, el método y los parámetros extraídos de la URL. Esto aclara, sin ambigüedad, la **responsabilidad** del router: traducir un par `(método, URI)` en un handler. Y aclara igual de bien lo que el router **no** hace: no renderiza HTML, no lee la base de datos, no construye controllers. Es el principio de responsabilidad única hecho concreto — una clase, un cometido — y el test lo fija como un contrato antes incluso de que el código exista.

## Un router pequeño

La primera implementación satisface ese test con un puñado de líneas y una expresión regular:

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

Código completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-32/es/parte-09/cap-32/listing-02.php)


Fuente real: [`src/Http/Router.php` en `lesson-1-3`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-3/src/Http/Router.php).


Sigue la lógica: por cada ruta registrada bajo ese método HTTP, el router transforma un patrón como `posts/:id` en una expresión regular, sustituyendo `:id` por un grupo de captura `([^/]+)`. Si el URI coincide, extrae los parámetros capturados (el `array_shift` descarta la coincidencia completa, quedándose solo con los grupos) y devuelve la terna `[controller, método, parámetros]`. Si ninguna ruta coincide, lanza `RouteNotFoundException` — que se convertirá en una respuesta 404. Es intencionadamente simple, y la simplicidad es el punto: entender que un router, bajo el capó, es solo emparejamiento de patrones te quita todo temor reverencial hacia las librerías de routing que usarás después.

## Request y Response tipadas

En el tag `lesson-1-9` cambia otro límite importante. La request ya no se lee por todas partes, esparciendo `$_POST` y `$_SERVER` por todo el código: entra una sola vez en una clase que la representa.

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

Código completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-32/es/parte-09/cap-32/listing-03.php)


Fuente real: [`src/Http/Request.php` en `lesson-1-9`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-9/src/Http/Request.php).


Sigue siendo una clase escrita por nosotros, pero dibuja un **límite** correcto. Los superglobales — esos `$_POST`, `$_GET`, `$_SERVER` que en la Parte VI aparecían por todas partes — se leen en un único punto, en la entrada, y se transforman en un objeto explícito e inmutable (fíjate en los `readonly` del Capítulo 25). De ahí en adelante el resto de la aplicación ya no toca los superglobales: recibe un `Request`, con propiedades tipadas y métodos como `postString()` que leen los datos de forma segura, devolviendo un default si la clave falta o no es una cadena. Es la diferencia entre una aplicación donde el input crudo penetra por todas partes y una donde entra por una sola puerta, controlada.

## El salto a PSR-7/15

Construido el concepto con nuestras propias manos, el proyecto da el paso que lo hace profesional: adoptar los estándares compartidos.

```bash
composer require league/route:^6.2 nyholm/psr7:^1.8 nyholm/psr7-server:^1.1
```

Código completo: [listing-04.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-32/es/parte-09/cap-32/listing-04.sh)


Fuente real: [`composer.json` en `lesson-1-15`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-15/composer.json).


Los **PSR** (PHP Standard Recommendations) son interfaces compartidas por toda la comunidad PHP. PSR-7 define cómo deben ser los objetos request y response; PSR-15 define los handlers y los middleware. Al adoptarlos, nuestro `Router` deja de ser un objeto aislado: se convierte en un `RequestHandlerInterface`, un tipo que todo el ecosistema reconoce.

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

Código completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-32/es/parte-09/cap-32/listing-05.php)


Fuente real: [`src/Http/Router.php` en `lesson-1-15`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-15/src/Http/Router.php).


El routing sigue siendo tan legible como antes, pero la ganancia es enorme y quizá no obvia: **interoperabilidad**. Como el router acepta un `ServerRequestInterface` y devuelve una `ResponseInterface` — tipos estándar, no nuestros — cualquier middleware PSR-15 escrito por terceros (para la autenticación, el logging, la gestión de CORS, el rate limiting) puede insertarse en el proyecto sin adaptadores extraños. Programar contra las interfaces estándar, exactamente como predicaba el Capítulo 26 con la "D" de SOLID, te abre el acceso a todo un ecosistema de componentes ya escritos y probados.

## Kernel y container

¿Quién pone en marcha toda esta máquina? El **Kernel**, el punto de arranque de la aplicación:

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

Código completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-32/es/parte-09/cap-32/listing-06.php)


Fuente real: [`src/Kernel.php` en `lesson-1-15`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-15/src/Kernel.php).


El método `handle()` se lee como la secuencia exacta de cada request: carga las variables de entorno desde el `.env` (las credenciales que en la Parte VI estaban en claro en el código, ahora fuera del repositorio), abre la sesión, construye el **container**, crea la request PSR-7, se la pasa al router y finalmente emite la response. La pieza central es el container: un registro que sabe construir y enlazar entre sí `PDO`, repositories, services y views. Es él quien realiza la *dependency injection* de la que hablamos desde el Capítulo 25: cuando hace falta un `Router`, el container lo crea proporcionándole todo lo que necesita, recursivamente. El controller, en consecuencia, ya no construye sus propias dependencias — no hace `new PDO(...)` en su interior — sino que las **recibe** en el constructor, ya listas. Esto es lo que hace cada pieza testeable de forma aislada: puedes pasarle un repository falso y verificar su comportamiento sin una base de datos real.

## Controllers finos

Con las dependencias inyectadas, el controller puede hacer su única cosa: **coordinar**, no contener la lógica.

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

Código completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-32/es/parte-09/cap-32/listing-07.php)


Fuente real: [`src/Controllers/PostController.php` en `lesson-1-15`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-15/src/Controllers/PostController.php).


Observa el flujo, porque es el modelo de casi toda acción MVC: toma el parámetro de la ruta (`id`), pide el dato al repository (`findById`), gestiona el caso "no encontrado" con un 404, si no pide a la view que renderice la página pasándole los datos (`post`, `comments`). El controller no contiene ni una línea de SQL ni una línea de HTML: **coordina** repository y view, y devuelve una response. Es la separación de roles que en la Parte VI vislumbrabas como convención (controller y view en ficheros separados) y que aquí se vuelve arquitectura: nada de SQL en la view, nada de HTML en el repository. Un controller "fino" es fácil de leer porque cuenta *qué* sucede, delegando el *cómo* a las capas de abajo.

## Views con escaping

La última pieza es la view, que sigue siendo un fichero PHP pero se renderiza desde un objeto dedicado:

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

Código completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-32/es/parte-09/cap-32/listing-08.php)


Fuente real: [`src/Support/View.php` en `lesson-1-9`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-9/src/Support/View.php).


El método `render()` hace algo elegante con el *output buffering*: `extract()` convierte las claves del array `$data` en variables locales (así en el template puedes escribir `$post` en lugar de `$data['post']`), `ob_start()` empieza a capturar la salida, `require` ejecuta el template PHP, y `ob_get_clean()` devuelve el HTML producido como cadena en lugar de escupirlo de inmediato. La view se convierte así en un componente que *devuelve* una cadena, componible y testeable. Pero la línea más importante está en su uso: dentro de los templates, cada dato del usuario se imprime con `htmlspecialchars(..., ENT_QUOTES, 'UTF-8')`. Es el vínculo directo con el User Management System y el Capítulo 20: cualquier valor guardado por un usuario — el título de un post, un comentario — puede convertirse en un ataque **XSS** si lo imprimes sin escaping. La arquitectura enterprise no te exime de la seguridad básica: la incorpora, poniendo el escaping en el punto exacto donde la salida llega al navegador.

![La misma lista de posts producida por el blog enterprise: la cadena router → controller → repository → view genera la salida, y la view la renderiza con `htmlspecialchars`. Compara la maquetación con la versión *freeblog* del inicio del capítulo.](figures/cap-32/enterprise-blog-post-list.png)

## En resumen

Este capítulo no enseña solamente "un router": enseña una **progresión**. Primero el comportamiento mínimo definido por un test, luego objetos request/response que disciplinan el límite con el input crudo, y finalmente PSR-7/15 y un container que inyecta las dependencias. En torno a este núcleo, controllers finos que coordinan y views que renderizan con escaping. Es el mismo MVC que vislumbrabas en la Parte VI, pero con los límites correctos — cada capa con una única responsabilidad, cada pieza testeable de forma aislada, cada componente abierto al ecosistema a través de los estándares. Es la forma que toma una aplicación cuando debe no solo funcionar, sino **crecer**.
