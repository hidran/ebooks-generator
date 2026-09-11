# 26. Herencia, interfaces, traits y miembros estáticos

Después de clases y objetos, PHP ofrece una segunda serie de herramientas, todas dedicadas a un único propósito: **reutilizar** y **organizar** el comportamiento sin reescribirlo. Herencia, clases abstractas, interfaces, traits, miembros estáticos y constantes de clase resuelven cada uno una parte de este problema. Pero hay que usarlos con mesura, y conviene decirlo antes incluso de empezar: estas herramientas ayudan mucho cuando *aclaran* el modelo — cuando hacen más evidente cómo son las cosas de tu dominio — y complican todo cuando las añades solo para "hacer OOP". El criterio, en cada apartado, será el mismo: se usa la herramienta si hace el código más comprensible, no porque exista.

## Herencia

Una clase puede **extender** a otra, heredando sus propiedades y métodos:

```php
<?php
class Animal
{
    public function duerme(): string
    {
        return "zzz";
    }
}

class Perro extends Animal
{
    public function ladra(): string
    {
        return "bau";
    }
}
```

Código completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/es/parte-07/cap-26/listing-01.php)


`Perro` no declara `duerme()`, y sin embargo puede usarlo: lo ha heredado de `Animal`. La palabra clave `extends` establece que todo perro *es* también un animal, y esta es la clave para saber cuándo usar la herencia: expresa una relación **"es un"**. Un perro es un animal, un `AdminController` es un `Controller`, una `SqlException` es una `Exception`. Úsala solo cuando esa frase sea verdadera en tu dominio. Hay, sin embargo, una advertencia que tener presente desde el principio: la herencia es el vínculo **más estrecho** que dos clases pueden tener, porque la hija depende de los detalles internos de la madre. Cambiar la clase base corre el riesgo de romper todas las hijas. Por eso, cuando solo necesitas reutilizar algo de código — y no hay una verdadera relación "es un" — casi siempre es mejor la **composición** (contener un objeto y delegarle el trabajo) que la herencia.

## Sobrescribir métodos

Una clase hija puede **redefinir** un método heredado, dándole un comportamiento distinto:

```php
<?php
class Gato extends Animal
{
    public function duerme(): string
    {
        return "el gato duerme en el sofá";
    }
}
```

Código completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/es/parte-07/cap-26/listing-02.php)


`Gato` hereda `duerme()` de `Animal`, pero lo sustituye por su propia versión: es la **sobrescritura** (override). A partir de ahora, llamar a `duerme()` sobre un gato ejecuta el código del gato, no el del animal. Hay una regla no escrita pero importante: una sobrescritura debería respetar el "contrato" del método original — si `duerme()` promete devolver una cadena, la versión redefinida debe seguir haciéndolo, de lo contrario el código que usa `Animal` sin saber qué tipo concreto tiene delante se quedará desconcertado. A veces no quieres sustituir por completo el comportamiento del padre, sino **añadir** algo al suyo:

```php
<?php
return parent::duerme() . " en el sofá";
```

Código completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/es/parte-07/cap-26/listing-03.php)


`parent::` llama a la versión del método definida en la clase madre. Así puedes reutilizar lo que el padre ya hace y luego extenderlo, en lugar de reescribirlo desde cero: es la forma limpia de especializar un comportamiento sin duplicarlo.

## Clases y métodos final

La palabra clave `final` hace lo contrario de la herencia: **impide** extender una clase o redefinir un método.

```php
<?php
final class Money
{
}
```

Código completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/es/parte-07/cap-26/listing-04.php)


Una clase `final` no se puede extender; como alternativa puedes sellar un solo método:

```php
<?php
class Service
{
    final public function execute(): void
    {
    }
}
```

Código completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/es/parte-07/cap-26/listing-05.php)


¿Por qué querrías *impedir* la herencia, justo después de haberla presentado? Porque cada punto de extensión es también un punto de **fragilidad**: si una clase se puede extender y sus métodos sobrescribir, tienes que garantizar que siga funcionando hagan lo que hagan las hijas. `final` quita esa preocupación y estabiliza un comportamiento que no debe alterarse — un objeto de valor como `Money`, por ejemplo, donde la lógica de los cálculos debe quedar exactamente como es. Muchos desarrolladores experimentados adoptan la filosofía "final por defecto": haz extensible solo lo que has diseñado a propósito para serlo, y sella el resto.

## Clases abstractas

Una **clase abstracta** está a medio camino entre una clase normal y una interfaz: no se puede instanciar directamente, y puede obligar a las hijas a implementar ciertos métodos.

```php
<?php
abstract class Controller
{
    abstract public function index(): string;

    protected function render(string $view): string
    {
        return "render " . $view;
    }
}
```

Código completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/es/parte-07/cap-26/listing-06.php)


`Controller` no tiene sentido por sí solo — `new Controller()` es un error — porque representa un concepto incompleto: falta la implementación de `index()`, declarado `abstract`, es decir, prometido pero no escrito. Cada controller concreto (un `HomeController`, un `UserController`) tendrá que extenderlo y proporcionar su propio `index()`. A cambio, en cambio, ya hereda `render()`, que está escrito por completo. Esta es exactamente la fuerza de la clase abstracta: **comparte el código común** a todas las hijas y al mismo tiempo **impone un contrato parcial**, la lista de métodos que cada una debe completar. Es el esquema del *template method*: el padre define el esqueleto, las hijas rellenan los huecos. Reconocerás esta estructura en el `Controller` base de la Parte IX.

## Interfaces

Una interfaz lleva la idea de contrato al extremo: declara **qué** debe ofrecer una clase, sin decir **cómo**.

```php
<?php
interface Logger
{
    public function info(string $message): void;
}

class FileLogger implements Logger
{
    public function info(string $message): void
    {
        file_put_contents("app.log", $message . PHP_EOL, FILE_APPEND);
    }
}
```

Código completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/es/parte-07/cap-26/listing-07.php)


La interfaz `Logger` no contiene código: solo dice que cualquiera que quiera ser un logger debe tener un método `info(string): void`. `FileLogger` firma este contrato con `implements Logger` y proporciona su versión, que escribe en un fichero. Mañana podrías escribir un `DatabaseLogger` o un `NullLogger`: mientras respeten la interfaz, para el resto del código son intercambiables. Y aquí está la verdadera ventaja — programar **contra el contrato** y no contra la implementación:

```php
<?php
function run(Logger $logger): void
{
    $logger->info("Inicio de la aplicación");
}
```

Código completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/es/parte-07/cap-26/listing-08.php)


`run()` no depende de `FileLogger`: depende de `Logger`, es decir, de "algo que sabe hacer logging". No le importa cuál sea el objeto concreto, mientras respete el contrato. Este es el **principio de inversión de dependencias** — la "D" de SOLID — y será el fundamento del container de la Parte IX: el código de alto nivel depende de abstracciones, no de clases concretas. Fíjate también en la diferencia práctica respecto a las clases: una clase puede implementar **muchas** interfaces pero extender **una sola** clase, y por eso las interfaces son la herramienta preferida para describir las capacidades de un objeto.

## Trait

Un **trait** resuelve un problema que ni la herencia ni las interfaces abordan bien: reutilizar el mismo *código* en clases que no tienen entre sí ninguna relación "es un".

```php
<?php
trait HasTimestamps
{
    public function touch(): void
    {
        $this->updatedAt = new DateTimeImmutable();
    }
}

class Post
{
    use HasTimestamps;
}
```

Código completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/es/parte-07/cap-26/listing-09.php)


Un `Post`, un `Comentario` y un `Usuario` no son lo mismo, pero todos podrían necesitar un método `touch()` que actualice la fecha de modificación. Ponerlo en una clase base común sería forzado — no hay una verdadera jerarquía — y repetirlo en cada una violaría el DRY. El trait ofrece la tercera vía: `use HasTimestamps` pega ese método dentro de `Post` como si estuviera escrito ahí. Es un reuso **horizontal**, que atraviesa las jerarquías. Comodísimo, pero con un riesgo que conviene conocer: el trait usa `$this->updatedAt`, una propiedad que *no declara* — da por hecho que la clase anfitriona la tiene. Esta dependencia oculta es el defecto típico de los traits: si abusas de ellos, acabas con clases que esperan propiedades y métodos llegados de quién sabe qué trait, y el código se vuelve difícil de seguir. Úsalos para pequeños comportamientos bien definidos, no como atajo para evitar diseñar.

## Constantes de clase

Una constante de clase es un valor fijo, con un nombre, ligado a la clase:

```php
<?php
class Role
{
    public const ADMIN = "admin";
    public const USER = "user";
}

if ($role === Role::ADMIN) {
    echo "Acceso al panel de administración";
}
```

Código completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/es/parte-07/cap-26/listing-10.php)


El valor de las constantes está en la comparación entre `Role::ADMIN` y la cadena desnuda `"admin"`. Si escribes `"admin"` esparcido por veinte puntos del código y un día tecleas uno mal — `"admni"` — tienes un bug silencioso: la condición es simplemente falsa, sin errores. Con `Role::ADMIN`, en cambio, una errata en el nombre de la constante es un error inmediato ("constante no definida"), porque PHP la conoce. Las constantes dan un nombre a los valores "mágicos", los centralizan en un solo sitio y los hacen a prueba de erratas — exactamente los roles que en el proyecto de la Parte VI aparecían esparcidos como cadenas.

## Propiedades y métodos estáticos

Un miembro **estático** pertenece a la clase misma, no a las instancias individuales:

```php
<?php
class Counter
{
    private static int $count = 0;

    public static function increment(): int
    {
        return ++self::$count;
    }
}

echo Counter::increment();
```

Código completo: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/es/parte-07/cap-26/listing-11.php)


Hay una sola `$count`, compartida por toda la clase: no necesitas crear un objeto para usarla, la llamas directamente con `Counter::increment()`, y su valor persiste entre una llamada y otra. Esto la hace cómoda para contadores, utilidades sin estado y factories simples. Pero justamente porque es compartida y siempre alcanzable, un estado estático es de hecho un **estado global**, con todos sus defectos: es difícil de testear (los tests se influyen entre sí a través de ese valor compartido), y oculta una dependencia, porque una función que llama a `Counter::increment()` no declara en ninguna parte que depende de `Counter`. Usa `static` con moderación: va muy bien para utilidades puras y factories, mucho menos para la lógica de dominio, donde hace los tests y las dependencias más rígidos.

## `self` y `static`

Cuando un método estático debe referirse a su propia clase, tienes dos palabras clave, y la diferencia cuenta en las jerarquías:

```php
<?php
class Model
{
    public static function make(): static
    {
        return new static();
    }
}
```

Código completo: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/es/parte-07/cap-26/listing-12.php)


`self` se refiere a la clase **en la que está escrito el método**, y se queda fija ahí. `static`, en cambio, usa el *late static binding*: se refiere a la clase **realmente llamada** en tiempo de ejecución. La diferencia aparece con la herencia: si `User extends Model` y llamas a `User::make()`, la versión con `new static()` devuelve un `User`, mientras que `new self()` devolvería siempre un `Model`, ignorando la hija. Por eso `static` es importante en factories y jerarquías donde el método debe producir la instancia de la clase **hija**, no del padre en que se escribió.

## En resumen

Herencia, interfaces, traits y miembros estáticos son herramientas potentes, cada una adecuada a un tipo de reuso distinto: la **herencia** modela la relación "es un" (pero es el vínculo más estrecho, así que úsala con cautela); las **interfaces** definen contratos y son la base de la inversión de dependencias; las **clases abstractas** comparten estructura e imponen un contrato parcial; los **traits** reutilizan pequeños comportamientos en horizontal; las **constantes** dan un nombre a los valores mágicos; `static` gestiona funcionalidad ligada a la clase más que a la instancia, con la cautela del estado global. La elección correcta, cada vez, es la que hace el código más comprensible — no la que mete la mayor cantidad posible de conceptos OOP.
