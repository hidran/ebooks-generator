# 27. Tipos modernos, enums y métodos mágicos

Las versiones recientes de PHP han convertido un lenguaje históricamente "permisivo" con los tipos en una herramienta capaz de expresar con precisión qué acepta una función y qué devuelve. Union types, intersection types, nullable, enums, operador nullsafe, métodos mágicos y property hooks son las piezas de esta evolución: te permiten decir más al lector y al motor de PHP, y hacen que los errores afloren antes. Pero casi todos tienen también un lado "astuto" que, usado sin disciplina, esconde las decisiones en lugar de tomarlas. Veámoslos uno a uno, siempre con la mirada puesta en *cuándo* son de verdad útiles.

## Union type

Un **union type** declara que un valor puede ser de uno entre varios tipos:

```php
<?php
function format_id(int|string $id): string
{
    return (string) $id;
}
```

Código completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/es/parte-07/cap-27/listing-01.php)


`int|string` dice que `format_id` acepta un entero **o** una cadena, y nada más. Es honesto y útil cuando una función recibe de verdad formas distintas del mismo concepto — un id que a veces llega como número y a veces como cadena. Pero cuidado con el abuso: un tipo sirve para *restringir* lo que puede pasar, y es una promesa de que quien lea la firma puede fiarse de ciertas garantías. Si ensanchas el union hasta que acepta casi todo, la promesa se vacía. No uses los union types para evitar una decisión de diseño: si un valor puede ser "cualquier cosa", el tipo no te está ayudando, solo te está permitiendo aplazar el problema.

## Tipo nullable

Un caso particular y frecuentísimo de union es el que incluye `null`:

```php
<?php
function find_user(int $id): ?array
{
    // devuelve un array o null
}
```

Código completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/es/parte-07/cap-27/listing-02.php)


El signo de interrogación delante del tipo — `?array` — es un atajo para `array|null`. Es la firma típica de las funciones `find`, donde no encontrar el registro **no es un error** sino un resultado normal y previsto: buscas al usuario 42, y podría no estar. El valor de este tipo es que hace la ausencia **explícita en la firma**: quien llama a `find_user()` ve de inmediato que el resultado puede ser `null` y sabe que debe gestionarlo, en lugar de descubrirlo con un error en tiempo de ejecución al intentar usar un array que no está. El tipo convierte el "quizá falta" de sorpresa en información declarada.

## Intersection type

Si el union pide "uno *o* el otro", el **intersection type** pide "el uno *y* el otro juntos":

```php
<?php
function export(Iterator&Countable $items): void
{
    echo count($items);
}
```

Código completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/es/parte-07/cap-27/listing-03.php)


`Iterator&Countable` significa que `$items` debe satisfacer **ambos** contratos: debe ser iterable *y* contable. Dentro de la función puedes, por tanto, tanto recorrerlo con un bucle (porque es `Iterator`) como pasarlo a `count()` (porque es `Countable`), con la garantía que da el tipo. Es una herramienta más rara que el union, pero valiosa cuando una función necesita varias capacidades de un objeto a la vez: en lugar de aceptar un tipo concreto específico, compones los requisitos a partir de las interfaces, quedando así abierto a cualquier clase que las implemente.

## Operador nullsafe

Desde PHP 8 el operador `?->` recorre una cadena de objetos deteniéndose en el primer `null`:

```php
<?php
$city = $user?->profile?->address?->city;
```

Código completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/es/parte-07/cap-27/listing-04.php)


Sin `?->`, si `$user` no tiene un perfil, `$user->profile->address` estallaría con un error sobre `null`. Con el nullsafe, en cuanto un eslabón de la cadena es `null`, la expresión completa devuelve `null` y se detiene, sin lanzar errores: `$city` será simplemente `null`. Es cómodo para navegar estructuras opcionales anidadas, pero esconde un riesgo. Si en esa cadena hay un objeto que *debería estar siempre* — un usuario sin perfil es un dato incoherente, no una posibilidad legítima — el nullsafe convierte un bug en un silencioso `null` que se propaga. Úsalo donde la ausencia esté de verdad prevista, no para callar estados que deberían ser obligatorios.

## Enum

Un **enum** representa un conjunto **cerrado** de valores con un nombre:

```php
<?php
enum Role
{
    case Admin;
    case User;
}
```

Código completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/es/parte-07/cap-27/listing-05.php)


En el capítulo anterior usamos las constantes de clase para dar un nombre a los roles; el enum da un paso más y los convierte en un **tipo** de pleno derecho. `Role::Admin` y `Role::User` no son cadenas: son los dos únicos valores posibles de `Role`, y PHP lo sabe. La diferencia se ve en cómo puedes tipar una función:

```php
<?php
function can_delete(Role $role): bool
{
    return $role === Role::Admin;
}
```

Código completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/es/parte-07/cap-27/listing-06.php)


`can_delete(Role $role)` acepta **solo** un valor de `Role`: no puedes pasarle un `"amdin"` mal escrito, ni un `"superuser"` inventado. Toda una categoría de bugs — aquellos en los que una cadena equivocada se cuela dentro de una función — se vuelve simplemente imposible, porque el tipo la bloquea antes incluso de que el código se ejecute. Esta es la gran ventaja de los enums frente a las constantes: no solo dan un nombre a los valores, sino que **restringen el conjunto** de lo que puede circular.

## Backed enum

Un **backed enum** asocia a cada caso un valor escalar (una cadena o un entero):

```php
<?php
enum Role: string
{
    case Admin = "admin";
    case User = "user";
}
```

Código completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/es/parte-07/cap-27/listing-07.php)


El enum "puro" del apartado anterior vive solo en memoria; pero tarde o temprano un rol hay que **guardarlo en la base de datos** o enviarlo en una respuesta JSON, y ahí hacen falta valores escalares, no objetos PHP. El backed enum hace de puente: cada caso tiene un `value` (`"admin"`, `"user"`) que persistir, y dos métodos para hacer el camino inverso, del valor al enum:

```php
<?php
$role = Role::from("admin");
echo $role->value;
```

Código completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/es/parte-07/cap-27/listing-08.php)


La elección entre los dos métodos de conversión es una decisión de seguridad. `from()` lanza una excepción si el valor no corresponde a ningún caso: lo usas cuando el valor *debe* ser válido y un valor fuera del conjunto es un error que hay que hacer estallar. `tryFrom()`, en cambio, devuelve `null` si no hay correspondencia: lo usas en la frontera con datos no fiables — un parámetro de la petición, una fila vieja de la base de datos — donde un valor inesperado debe gestionarse con elegancia, no con un fallo. La distinción calca exactamente la lógica *fail-loud* / *fail-closed* vista en el proyecto de la Parte VI.

## Métodos en los enums

Un enum no es solo una lista de valores: también puede tener **métodos**.

```php
<?php
enum Role: string
{
    case Admin = "admin";
    case User = "user";

    public function label(): string
    {
        return match ($this) {
            self::Admin => "Administrador",
            self::User => "Usuario",
        };
    }
}
```

Código completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/es/parte-07/cap-27/listing-09.php)


El método `label()` devuelve la etiqueta legible del rol, eligiéndola con un `match` sobre el caso actual. La ventaja no es solo estética: así el **comportamiento ligado al rol está junto a los valores posibles**, dentro del mismo tipo, en lugar de estar disperso en `if` repartidos por la aplicación. Es el principio de cohesión — lo que cambia junto está junto. Y hay un extra que da el `match`: si mañana añades un `case Editor` y olvidas darle una etiqueta, PHP lanza un error porque el `match` ya no es exhaustivo. El tipo te obliga a no dejar huecos.

## Método mágico

Los **métodos mágicos** son métodos especiales que PHP llama *automáticamente* en ciertas situaciones, sin que tú los invoques explícitamente. Los reconoces por los dos guiones bajos iniciales. Son potentes precisamente porque son implícitos — pero es esa misma implicitud la que los hace peligrosos, porque esconden lo que de verdad ocurre.

### `__get()`

```php
<?php
class Data
{
    private array $values = [];

    public function __get(string $name): mixed
    {
        return $this->values[$name] ?? null;
    }
}
```

Código completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/es/parte-07/cap-27/listing-10.php)


PHP invoca `__get()` cuando accedes a una propiedad **inaccesible o inexistente**: al escribir `$data->algo`, si `algo` no es una propiedad pública, arranca este método con `"algo"` como argumento. Aquí devuelve el valor del array interno, realizando de hecho un objeto con propiedades "dinámicas", decididas en tiempo de ejecución. Cómodo para contenedores genéricos, pero con un coste pesado: mirando la clase ya no sabes *qué* propiedades existen de verdad, el IDE no puede autocompletarlas y ninguna herramienta de análisis estático puede comprobarlas. Has cambiado claridad por flexibilidad.

### `__call()`

```php
<?php
class Proxy
{
    public function __call(string $name, array $arguments): mixed
    {
        throw new BadMethodCallException("Método $name no encontrado");
    }
}
```

Código completo: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/es/parte-07/cap-27/listing-11.php)


`__call()` es el equivalente de `__get()` para los métodos: PHP lo invoca cuando llamas a un método **inaccesible**, pasándole el nombre y los argumentos. Aquí la clase lo usa de forma virtuosa, para *fallar en voz alta*: en lugar de ignorar en silencio una llamada a un método inexistente, lanza una excepción clara. Es el ladrillo de los **proxies** y los **decoradores**, objetos que interceptan las llamadas para añadirles comportamiento (logging, caché, control de permisos) antes de reenviarlas al objeto real.

### `__callStatic()`

```php
<?php
class Facade
{
    public static function __callStatic(string $name, array $arguments): mixed
    {
        // delega a un servicio real
    }
}
```

Código completo: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/es/parte-07/cap-27/listing-12.php)


`__callStatic()` es la versión estática de `__call()`: intercepta las llamadas a métodos estáticos inexistentes. Es el mecanismo detrás de las **facades** de algunos frameworks (Laravel el primero), esas API de aspecto estático — `Cache::get(...)`, `Route::get(...)` — que en realidad delegan entre bastidores a un objeto real tomado del container. Dan una sintaxis cómoda, al precio de esconder el objeto subyacente: un compromiso que conviene conocer antes de adoptarlo.

## Property hooks

PHP 8.4 introduce los **property hooks**, que permiten adjuntar lógica de lectura y escritura directamente a una propiedad, sin escribir un getter y un setter separados. El concepto acerca propiedades y métodos: desde el punto de vista de quien usa el objeto sigue siendo un simple acceso `$objeto->propiedad`, pero detrás puede haber una validación en escritura o un cálculo en lectura.

La idea, en esencia, es que una propiedad pueda controlar el valor que se le asigna o calcular al vuelo el valor que devuelve, reduciendo el boilerplate de los clásicos getters/setters del Capítulo 25. Y vale la cautela de siempre, la misma que para los métodos mágicos: no uses un hook para esconder lógica pesada allí donde quien lee espera el coste insignificante de un simple acceso a un dato. La sorpresa, en el código, es siempre un defecto.

## En resumen

Los tipos modernos de PHP sirven para hacer el código **más explícito**: los union e intersection types declaran con precisión qué acepta una función, el nullable hace visible la ausencia, los enums eliminan las cadenas mágicas restringiendo el conjunto de valores posibles, y los backed enums hacen de puente hacia bases de datos y serialización. En el lado dinámico, el operador nullsafe simplifica las cadenas opcionales y los métodos mágicos permiten comportamientos implícitos como proxies y facades. El hilo que los une a todos es la disciplina: cada una de estas herramientas debe usarse cuando hace el **modelo más claro** — no cuando sirve para sorprender o para aplazar una decisión de diseño.
