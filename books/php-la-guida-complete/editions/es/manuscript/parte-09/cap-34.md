# 34. Autenticación, tests y quality gates

Un proyecto enterprise no es creíble porque "funciona en mi computadora". Es creíble porque tiene controles repetibles: tests automáticos, style checks, análisis estático y refactoring guiado. En el repositorio `phpenterpriseblog` estos controles llegan justo después de la foundation MVC.

El objetivo no es añadir herramientas para parecer más profesional. El objetivo es construir un sistema donde un cambio pueda hacerse, verificarse y corregirse sin depender de la memoria del desarrollador. En un blog MVC pequeño puedes hacer click en dos páginas y convencerte de que todo va bien. En un proyecto que crece, ese método no escala: olvidas un caso límite, cambias una query y rompes una página lejana, actualizas PHP y descubres demasiado tarde que una firma ya no es coherente. Los quality gates reducen ese riesgo antes del deploy.

Como arquitecto PHP, leo estas herramientas como capas distintas del mismo sistema de control:

- PHPUnit verifica el comportamiento que decidimos proteger;
- PHP_CodeSniffer y Slevomat verifican la disciplina del código;
- PHPStan verifica la coherencia de tipos y contratos;
- Rector aplica refactorings mecánicos de forma repetible;
- Composer pone todo detrás de comandos que también puede ejecutar la CI.

Ninguna de estas herramientas reemplaza el juicio técnico. Juntas, sin embargo, evitan que el proyecto dependa solo de la atención del momento.

## Autenticación como service

En el proyecto UMS la lógica de login crecía dentro de funciones y controllers. En el blog la extraemos a `AuthService`, para poder testearla sin navegador y sin database real:

```php
<?php

declare(strict_types=1);

final class AuthService
{
    public function __construct(private readonly UserRepositoryInterface $users)
    {
    }

    public function verifySignup(
        string $email,
        string $password,
        string $token,
        string $sessionToken
    ): AuthResult {
        if (!hash_equals($sessionToken, $token)) {
            return AuthResult::failure('TOKEN MISMATCH');
        }

        if ($this->users->findByEmail($email) !== null) {
            return AuthResult::failure('USER ALREADY EXISTS');
        }

        return AuthResult::success('SIGNUP OK');
    }
}
```

Código completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-34/es/parte-09/cap-34/listing-01.php)


Fuente real: [`src/Services/AuthService.php` en `lesson-1-8`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-8/src/Services/AuthService.php).

La dependencia es una interfaz (`UserRepositoryInterface`), no una clase concreta. Esto hace que el service sea testeable con mocks.

Esta es una decisión arquitectónica, no solo un truco para PHPUnit. `AuthService` contiene reglas de aplicación: verificar el token CSRF, buscar el usuario, comprobar la password y devolver un resultado explícito. Si esta lógica queda dentro de un controller, para testearla tienes que simular request HTTP, sesión, database y rendering. Si vive en un service, puedes testear la regla directamente.

Un buen application service tiene tres características: recibe dependencias desde fuera, devuelve un resultado comprensible para quien lo llama y no decide detalles de infraestructura como redirects o templates. El controller puede ocuparse de HTTP; el service decide si el login es válido. Esa separación es la razón por la que el unit test se vuelve natural.

## PHPUnit: unit e integration

La configuración separa tests unitarios y de integración:

```xml
<testsuites>
    <testsuite name="unit">
        <directory>tests/Unit</directory>
    </testsuite>
    <testsuite name="integration">
        <directory>tests/Integration</directory>
    </testsuite>
</testsuites>
```

Código completo: [listing-02.xml](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-34/es/parte-09/cap-34/listing-02.xml)


Fuente real: [`phpunit.xml.dist` en `lesson-3-1`](https://github.com/hidran/phpenterpriseblog/blob/lesson-3-1/phpunit.xml.dist).

Los tests unitarios deben ser rápidos y aislados. Los tests de integración pueden tocar MySQL o Redis, pero viven en una suite separada.

La diferencia es práctica. Un unit test verifica una decisión en memoria: dado este input y esta dependencia simulada, el service devuelve este resultado. No debe arrancar MySQL, no debe existir Redis y no debe intervenir un web server. Si falla, quieres entender enseguida qué regla está mal.

Un integration test verifica que dos o más partes reales hablen correctamente entre sí. Un repository con PDO, por ejemplo, no está realmente verificado si solo testeas que llama a `prepare()`: también necesitas saber que la query funciona contra el schema real, que los nombres de columnas son correctos y que el mapping de fila SQL a objeto no pierde datos. Lo mismo vale para Redis, migraciones, session handlers y configuración.

Por eso las suites están separadas. Los tests unitarios deben poder ejecutarse continuamente mientras desarrollas. Los tests de integración pueden ser más lentos y requerir servicios Docker, así que los ejecutas antes de abrir una pull request, en CI, o cuando tocas un límite de infraestructura. Separarlos evita dos errores comunes: hacer que todos los tests sean lentos o llamar "unitario" a un test que en realidad depende de medio sistema.

## Testear autenticación con mocks

Un test no debe crear usuarios reales en el database solo para verificar una password incorrecta:

```php
<?php

declare(strict_types=1);

public function testLoginRejectsUnknownUser(): void
{
    $repo = $this->createMock(UserRepositoryInterface::class);
    $repo->method('findByEmail')->willReturn(null);

    $service = new AuthService($repo);

    self::assertSame(
        'USER NOT FOUND',
        $service->verifyLogin('a@b.co', 'secret123', 't', 't')->message
    );
}
```

Código completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-34/es/parte-09/cap-34/listing-03.php)


Fuente real: [`tests/Unit/Services/AuthServiceTest.php` en `lesson-3-2`](https://github.com/hidran/phpenterpriseblog/blob/lesson-3-2/tests/Unit/Services/AuthServiceTest.php).

Aquí testeamos el contrato del service: cuando el repository no encuentra al usuario, el resultado es un fallo controlado.

Un mock es útil cuando quieres aislar una regla de su límite externo. En este caso no nos interesa si `UserRepository` sabe hablar con MySQL; eso lo cubrirá un test de integración. Aquí nos interesa el comportamiento de `AuthService` cuando el repository responde "no hay usuario".

El riesgo de los mocks es usarlos para testear implementación en lugar de comportamiento. Si un test dice "debe llamar exactamente estos tres métodos en este orden" pero no describe un resultado útil para la aplicación, se vuelve frágil. Un buen unit test habla el lenguaje del dominio: login rechazado, token inválido, usuario existente, password correcta.

## Tests de regresión

Un bug corregido debe convertirse en un test. En el repository hay un caso preciso: `PostRepository::save()` no debe escribir el email en el cuerpo del post.

```php
<?php

declare(strict_types=1);

$stmt->expects($this->once())
    ->method('execute')
    ->with($this->callback(function (array $params): bool {
        self::assertSame('actual message body', $params['message']);
        self::assertArrayNotHasKey('email', $params);

        return true;
    }));
```

Código completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-34/es/parte-09/cap-34/listing-04.php)


Fuente real: [`tests/Unit/Repositories/PostRepositorySaveRegressionTest.php` en `lesson-3-3`](https://github.com/hidran/phpenterpriseblog/blob/lesson-3-3/tests/Unit/Repositories/PostRepositorySaveRegressionTest.php).

El test describe el comportamiento que no debe romperse otra vez.

Ese es el valor de un test de regresión: no demuestra que todo el repository sea perfecto, pero bloquea un error real que ya costó tiempo. Cada vez que corriges un bug, pregúntate qué test lo habría detectado antes. Si puedes escribirlo, ese bug ya no está solo "corregido": queda documentado como comportamiento esperado.

En el blog enterprise esta mentalidad importa más que la cantidad de tests. No necesitas testear cada getter o cada línea. Necesitas proteger las reglas, los bugs ya encontrados y los límites donde una regresión cuesta caro: autenticación, persistencia de posts, escaping de views, migraciones e integración con servicios externos.

## PHP_CodeSniffer y Slevomat

El primer quality gate es mecánico: PSR-12 más reglas Slevomat para tipos y `strict_types`.

```xml
<rule ref="PSR12"/>
<rule ref="SlevomatCodingStandard.TypeHints.ParameterTypeHint"/>
<rule ref="SlevomatCodingStandard.TypeHints.ReturnTypeHint"/>
<rule ref="SlevomatCodingStandard.TypeHints.PropertyTypeHint"/>
<rule ref="SlevomatCodingStandard.TypeHints.DeclareStrictTypes"/>
```

Código completo: [listing-05.xml](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-34/es/parte-09/cap-34/listing-05.xml)


Fuente real: [`phpcs.xml` en `lesson-2-1`](https://github.com/hidran/phpenterpriseblog/blob/lesson-2-1/phpcs.xml).

El objetivo no es discutir espacios o llaves. El objetivo es quitar trabajo mecánico al reviewer y hacer fallar el build cuando faltan tipos.

PHP_CodeSniffer lee el código y verifica que respete un estándar. PSR-12 da una base común: indentación, namespaces, imports, llaves y declaraciones. Slevomat añade reglas más orientadas a la calidad del PHP moderno: parámetros tipados, return types, property types y `declare(strict_types=1)`.

Para un senior developer el valor es muy concreto: la code review debe concentrarse en arquitectura, seguridad, queries, transacciones, error handling y nombres de dominio. Si la mitad de la review trata de formato o tipos ausentes, estás gastando atención humana en problemas que una máquina puede detectar con más consistencia.

PHPCS no sabe si la query es correcta y no sabe si el diseño es bueno. Pero crea una base uniforme. Cuando todos los archivos siguen las mismas reglas, el código se lee mejor, las herramientas trabajan mejor y los diffs de los commits muestran cambios reales, no ruido.

## PHPStan

PHPStan encuentra incoherencias que los tests podrían no recorrer:

```yaml
includes:
  - phpstan-baseline.neon
parameters:
  level: 8
  paths:
    - src
    - bin
    - config
    - public
    - tests
```

Código completo: [listing-06.yml](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-34/es/parte-09/cap-34/listing-06.yml)


Fuente real: [`phpstan.neon` en `lesson-8-3`](https://github.com/hidran/phpenterpriseblog/blob/lesson-8-3/phpstan.neon).

El proyecto empieza con una baseline en nivel 6 y luego sube el listón a nivel 8. Es una migración pragmática: activas el control pronto y luego reduces la deuda de forma explícita.

PHPStan es un analizador estático: no ejecuta el programa, sino que lee el código e intenta entender si los contratos son coherentes. Si una función promete `Post` pero puede devolver `false`, PHPStan lo señala. Si un array se usa como si una clave estuviera siempre presente, pero esa clave no está garantizada, PHPStan te obliga a ser explícito. Si un método recibe `int` y le pasas `string|null`, lo descubres antes de llegar al navegador.

Esto es especialmente importante en PHP porque el lenguaje es flexible. La flexibilidad es útil, pero en proyectos grandes puede esconder errores: formas de array implícitas, valores `mixed`, propiedades inicializadas tarde, retornos distintos en el mismo método. PHPStan reduce esa zona gris.

La baseline no es una excusa para ignorar errores. Es una herramienta de migración. Cuando introduces PHPStan en un proyecto existente, puedes tener demasiados problemas para corregirlos todos de inmediato. La baseline registra la deuda actual e impide añadir más. Luego, commit tras commit, eliminas entradas de la baseline y subes el nivel. Llegar a nivel 8 significa pedir contratos mucho más claros al código.

PHPStan no reemplaza los tests. Un código puede ser estáticamente correcto y aun así violar una regla de negocio. Pero PHPStan encuentra otra clase de problemas: incoherencias que los tests quizá nunca recorran.

## Rector hacia PHP 8.5

Rector ayuda a mantener el código alineado con el lenguaje:

```php
<?php

declare(strict_types=1);

return RectorConfig::configure()
    ->withPaths([__DIR__ . '/src', __DIR__ . '/bin', __DIR__ . '/config', __DIR__ . '/tests'])
    ->withSets([
        LevelSetList::UP_TO_PHP_85,
        SetList::CODE_QUALITY,
        SetList::DEAD_CODE,
        SetList::TYPE_DECLARATION,
    ]);
```

Código completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-34/es/parte-09/cap-34/listing-07.php)


Fuente real: [`rector.php` en `lesson-2-3`](https://github.com/hidran/phpenterpriseblog/blob/lesson-2-3/rector.php).

No reemplaza el juicio humano, pero convierte muchas modernizaciones en trabajo mecánico.

Rector trabaja sobre el árbol sintáctico del código, no sobre simples reemplazos de texto. Eso significa que puede aplicar transformaciones estructurales: añadir tipos cuando son deducibles, reemplazar constructos obsoletos, simplificar código muerto y mover patrones hacia versiones modernas del lenguaje.

El valor arquitectónico de Rector es la repetibilidad. Si decides que el proyecto debe alinearse con PHP 8.5, no quieres hacer cientos de micro-refactors a mano. Quieres una regla ejecutable, un diff legible y una suite de tests que confirme que el comportamiento no cambió.

Rector debe usarse con disciplina: ejecútalo en commits pequeños, lee el diff, no aceptes transformaciones que no entiendes y luego pasa tests y análisis estático. Es un acelerador, no un piloto automático. Si una transformación cambia el significado del código, el problema no es solo de la herramienta: significa que faltaban tests o que el código era ambiguo.

## El comando CI local

El valor de los gates está en poder ejecutarlos siempre de la misma forma:

```bash
composer ci
```

Código completo: [listing-08.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-34/es/parte-09/cap-34/listing-08.sh)


Fuente real: [`composer.json` en el commit `eb2e62a`](https://github.com/hidran/phpenterpriseblog/blob/eb2e62a774f6b20539e72f40f7d3fe9205ef4c5d/composer.json).

Cada bloque de trabajo debe cerrarse con una verificación real. No basta con decir "debería funcionar": ejecuta el comando, lee la salida y solo entonces considera estable ese punto del proyecto.

El orden de los gates importa. Primero quieres fallar en problemas baratos: formato, estándares, tipos obvios. Luego pasas al análisis estático y a los unit tests. Solo después tiene sentido ejecutar integration tests, E2E o pipelines más costosas. Una CI bien organizada no es un único muro final: es una serie de filtros que devuelven feedback lo antes posible.

En un equipo, `composer ci` también es un contrato social. Significa que todos usan el mismo comando, localmente y en CI. No hay instrucciones escondidas en la cabeza de una persona. Si el comando pasa en tu máquina y pasa en CI, el proyecto tiene una definición compartida de "verificado".

## En resumen

Autenticación y quality gates están en el mismo capítulo porque comparten un principio: comportamiento explícito y verificable. `AuthService` hace testeable el login; PHPUnit bloquea regresiones; PHP_CodeSniffer y Slevomat uniforman el estilo y obligan tipos claros; PHPStan controla contratos sin ejecutar la aplicación; Rector automatiza refactorings y upgrades hacia PHP 8.5. Un desarrollador senior pragmático no debe usarlos por moda: debe usarlos porque reducen de forma medible el riesgo de cambiar código.
