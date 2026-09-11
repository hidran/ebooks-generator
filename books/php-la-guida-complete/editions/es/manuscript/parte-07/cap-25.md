# 25. Clases, objetos, propiedades y constructores

Hasta aquí has escrito funciones que reciben datos, los procesan y devuelven un resultado. La **programación orientada a objetos** propone una forma distinta de organizar el código: en lugar de mantener separados los datos (en variables y arrays) y los comportamientos (en funciones), los reúne en una única unidad. En PHP esa unidad es la **clase**. Una clase describe una categoría de cosas — un coche, un usuario, una cuenta bancaria — indicando qué información llevan esas cosas consigo y qué saben hacer. Un **objeto** es un ejemplar concreto de esa categoría: la clase `Auto` es el concepto "automóvil", el objeto concreto es *aquel* coche rojo que va a 50 por hora. La distinción entre clase y objeto es la misma que hay entre la receta y la tarta: la receta es una sola, pero las tartas que salen de ella son muchas y cada una con su propia vida.

Este capítulo introduce los ladrillos básicos: cómo se define una clase, cómo se crean objetos, cómo se describe su estado con las propiedades y su comportamiento con los métodos, y cómo se protege ese estado para que se mantenga siempre coherente. Son los cimientos sobre los que se apoyan el proyecto de la Parte VI y toda la arquitectura enterprise de la Parte IX.

## Definir una clase

```php
<?php
class Auto
{
}
```

Código completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-25/es/parte-07/cap-25/listing-01.php)


Aunque esté vacía, esta clase ya es algo: has definido un **nuevo tipo**, que desde ahora se suma a `int`, `string` y `array`. Por convención, el nombre de una clase se escribe en **PascalCase**, con la inicial en mayúscula y sin espacios: `Auto`, `UsuarioRegistrado`, `CarritoPedido`. Es una convención, no una obligación del lenguaje, pero seguirla hace que un nombre de clase se reconozca de inmediato frente a una variable o una función. Para crear un objeto a partir de la clase se usa `new`:

```php
<?php
$auto = new Auto();
var_dump($auto);
```

Código completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-25/es/parte-07/cap-25/listing-02.php)


La palabra clave `new` pide a PHP que **instancie** la clase: reserva en memoria un nuevo objeto y devuelve una referencia a él, que aquí acaba en la variable `$auto`. El `var_dump` muestra algo como `object(Auto)#1 (0) { }`: un objeto de tipo `Auto`, el primero creado (`#1`), con cero propiedades. El objeto existe, pero es un cascarón vacío — todavía no lleva ningún dato interesante. Hay un detalle que conviene fijar de inmediato: cada `new` produce un objeto **distinto**. Si escribieras `new Auto()` dos veces obtendrías dos objetos separados, con vidas independientes, exactamente como dos tartas salidas de la misma receta. Y, a diferencia de los arrays, los objetos se pasan **por referencia**: asignar `$auto` a otra variable no copia el objeto, sino que crea un segundo nombre para el mismo objeto. Es una diferencia que tendrá consecuencias prácticas importantes más adelante.

## Propiedades

Las **propiedades** son las variables que pertenecen al objeto: describen su **estado**, es decir, la información que lleva consigo en un momento dado.

```php
<?php
class Auto
{
    public string $color;
    public int $velocidad = 0;
}

$auto = new Auto();
$auto->color = "rojo";
$auto->velocidad = 50;
```

Código completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-25/es/parte-07/cap-25/listing-03.php)


Cada propiedad se declara con un tipo (`string`, `int`) y puede tener un valor inicial: `$velocidad = 0` significa que todo coche nace parado, mientras que `$color` no tiene valor de partida y hay que asignarlo antes de leerlo. El operador `->` es la llave de acceso: `$auto->color` lee o escribe la propiedad `color` de *ese* objeto. Y aquí se ve el sentido de tener objetos distintos: si creo dos coches y doy a uno `color = "rojo"` y al otro `color = "azul"`, los dos valores no se pisan, porque cada propiedad vive dentro de su objeto. El estado es **por instancia**, no compartido: la clase dice *qué* propiedades existen, cada objeto guarda su propia copia con sus propios valores.

## Métodos

Si las propiedades son el estado, los **métodos** son el comportamiento: funciones que viven dentro de la clase y pueden actuar sobre el estado del objeto.

```php
<?php
class Auto
{
    public int $velocidad = 0;

    public function acelerar(int $incremento): void
    {
        $this->velocidad += $incremento;
    }
}

$auto = new Auto();
$auto->acelerar(20);
```

Código completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-25/es/parte-07/cap-25/listing-04.php)


La diferencia entre un método y una función cualquiera está toda en una palabra: `$this`. Dentro de un método, `$this` es **el objeto sobre el que se llamó al método** — cuando escribes `$auto->acelerar(20)`, dentro de `acelerar` la variable `$this` *es* `$auto`, y por tanto `$this->velocidad` es la velocidad de ese coche concreto. Un método, por tanto, no trabaja sobre datos que recibe de fuera y luego olvida: trabaja sobre el estado del objeto al que pertenece, y sus cambios permanecen. Después de `acelerar(20)`, la propiedad `velocidad` de `$auto` vale 20; llamándolo de nuevo pasa a 40. Es ese vínculo permanente entre el comportamiento y los datos sobre los que opera lo que distingue al objeto de una simple función con parámetros.

## Visibilidad

Hasta ahora todo ha sido `public`, es decir, accesible para cualquiera. Pero la verdadera razón para usar objetos es poder **ocultar** parte del estado y controlar su acceso. Las palabras clave que regulan la visibilidad son tres:

- `public`: accesible desde el exterior;
- `protected`: accesible en la clase y en sus clases hijas;
- `private`: accesible sólo en la clase.

```php
<?php
class Conto
{
    private float $saldo = 0;

    public function deposita(float $importo): void
    {
        if ($importo <= 0) {
            return;
        }

        $this->saldo += $importo;
    }

    public function saldo(): float
    {
        return $this->saldo;
    }
}
```

Código completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-25/es/parte-07/cap-25/listing-05.php)


Este ejemplo es el corazón del capítulo, porque muestra para qué sirve de verdad el encapsulamiento. El saldo es `private`: desde fuera **no puedes** escribir `$conto->saldo = -1000000`, porque esa propiedad es invisible fuera de la clase. La única forma de hacer crecer el saldo es pasar por `deposita()`, que comprueba el importe y rechaza los valores no positivos. El resultado es una **garantía**: cualquiera que sea el código que use esta clase, el saldo no podrá cambiarse nunca a un valor absurdo, porque la regla que lo protege vive *dentro* del objeto, junto al dato. Esta es la verdadera promesa de la programación orientada a objetos — no "agrupar funciones", sino mantener juntos un dato y las reglas que garantizan su coherencia, de modo que el estado no pueda acabar en configuraciones inválidas. Las condiciones que deben mantenerse siempre verdaderas (el saldo no es negativo, la email es válida, la edad es positiva) se llaman **invariantes**, y `private` es la herramienta que te permite defenderlas.

## Constructor

El **constructor** es un método especial, `__construct`, que PHP llama automáticamente en el momento exacto en que creas el objeto con `new`.

```php
<?php
class Usuario
{
    private string $email;

    public function __construct(string $email)
    {
        $this->email = $email;
    }
}

$usuario = new Usuario("juan@example.com");
```

Código completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-25/es/parte-07/cap-25/listing-06.php)


El valor del constructor es que hace imposible crear un objeto **incompleto**. Aquí no puedes obtener un `Usuario` sin email: la firma `__construct(string $email)` obliga a quien escribe `new Usuario(...)` a proporcionarla de entrada. Es una diferencia sutil pero decisiva respecto a asignar las propiedades una a una tras la creación, donde nada te impide olvidar una parte y quedarte con un objeto a medias. El constructor es, por tanto, el lugar adecuado para dos cosas: los **datos obligatorios** sin los cuales el objeto no tiene sentido, y las **dependencias**, es decir, los otros objetos que este necesita para trabajar (una conexión a la base de datos, un logger). Pedir las dependencias en el constructor es el primer paso hacia la *dependency injection* que será el eje de la arquitectura de la Parte IX: un objeto declara qué necesita, y lo recibe desde fuera al nacer.

## Promoción de propiedades de constructor

El patrón del apartado anterior — declarar la propiedad, recibirla como parámetro, asignarla con `$this->` — se repite tan a menudo que PHP 8 introdujo un atajo:

```php
<?php
class Usuario
{
    public function __construct(
        private string $email,
        private string $name
    ) {
    }
}
```

Código completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-25/es/parte-07/cap-25/listing-07.php)


Poniendo un modificador de visibilidad (`private`, `public`, `protected`) delante de un parámetro del constructor, le dices a PHP que haga tres cosas de una vez: declarar la propiedad, recibir su valor como argumento y asignarlo. Este código es exactamente equivalente a la versión larga de antes, pero sin la triple repetición del nombre de cada propiedad. No es solo cuestión de teclear menos: menos código repetitivo significa menos sitios donde un refactor puede olvidar algo, y la firma del constructor se convierte en una lista legible de todo lo que el objeto requiere. Verás esta forma por todas partes en el código PHP moderno, y la usarás mucho en la Parte IX.

## Setters y getters

A veces necesitas de todos modos leer o modificar una propiedad desde fuera, pero manteniendo el control sobre *cómo*. Entran en juego los **getters** (leen) y los **setters** (modifican):

```php
<?php
class Usuario
{
    private string $email;

    public function setEmail(string $email): void
    {
        if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
            throw new InvalidArgumentException("Email no válida");
        }

        $this->email = $email;
    }

    public function getEmail(): string
    {
        return $this->email;
    }
}
```

Código completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-25/es/parte-07/cap-25/listing-08.php)


Aquí el setter no se limita a copiar el valor: lo **valida**, y lanza una excepción si la email está mal formada (las excepciones son el tema del Capítulo 30). Por eso mantener `email` privada y pasar por `setEmail` conviene frente a dejarla pública: tienes un único punto de control, y nadie puede colar una email inválida en el objeto. Pero cuidado con un error muy común: **no** generes automáticamente getters y setters para cada propiedad. Un setter público que se limita a `$this->x = $x`, sin ninguna validación, no protege nada — es una propiedad pública con dos líneas de ceremonia de más, y traiciona el sentido mismo del encapsulamiento. Los getters y los setters se añaden cuando de verdad hacen falta: para validar, para calcular un valor al vuelo, o para conservar una interfaz estable mientras cambia la implementación interna. Si una propiedad no necesita protección, o la haces pública o — mejor aún — la pasas en el constructor y la dejas de sólo lectura, como veremos enseguida.

## Propiedades tipadas

Las **propiedades tipadas** — las propiedades con un tipo declarado — son una red de seguridad:

```php
<?php
class Post
{
    public int $id;
    public string $title;
}
```

Código completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-25/es/parte-07/cap-25/listing-09.php)


Declarar `public int $id` significa decirle a PHP que esa propiedad contendrá siempre un entero. Si intentas asignarle una cadena no convertible a número, PHP lanza un `TypeError` en el acto, en lugar de dejar entrar un valor equivocado que estallará quién sabe dónde más tarde. Y hay más: una propiedad tipada sin valor inicial arranca en estado **no inicializado**, y leerla antes de haberle asignado algo provoca un error explícito, no un silencioso `null`. Es exactamente el comportamiento que quieres: mejor un error claro en el primer acceso equivocado que un `null` inesperado propagándose por media aplicación antes de causar un fallo lejos de la verdadera causa. Los tipos convierten una clase de errores de "misterios que depurar en tiempo de ejecución" en "errores señalados de inmediato".

## Sólo lectura

Desde PHP 8.1 puedes declarar una propiedad `readonly`, es decir, asignable una sola vez:

```php
<?php
class UserId
{
    public function __construct(
        public readonly int $value
    ) {
    }
}
```

Código completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-25/es/parte-07/cap-25/listing-10.php)


Una propiedad `readonly` se puede escribir una sola vez — normalmente en el constructor — y después se vuelve inmodificable: cualquier intento de reasignarla provoca un error. ¿Por qué querer esto? Porque la **inmutabilidad** elimina toda una categoría de problemas. Un `UserId` creado con valor 42 será 42 durante toda su vida: puedes pasarlo entre funciones, compartirlo, guardarlo en una estructura de datos sin temer que alguien, en algún sitio, lo cambie bajo tus pies. Es la herramienta ideal para los **objetos de valor** — pequeños objetos que representan un concepto (un identificador, un importe, una dirección de email) y cuya identidad coincide con su valor — y para los **DTO**, los objetos que transportan datos de una capa de la aplicación a otra sin lógica propia. Combinada con la promoción de propiedades de constructor, `readonly` hace que definir un objeto inmutable sea cuestión de pocas líneas.

## En resumen

Las clases y los objetos sirven para modelar el dominio de tu aplicación poniendo juntos, en una única unidad, los datos y las reglas que los gobiernan: las **propiedades** guardan el estado, los **métodos** definen el comportamiento, la **visibilidad** protege los invariantes, el **constructor** garantiza que un objeto nazca ya válido. En torno a estas bases, el PHP moderno pone a disposición herramientas que hacen el código más expresivo y menos verboso — promoción de propiedades de constructor, propiedades tipadas, `readonly` — y que usarás constantemente de aquí en adelante. Ten presente la idea central, la que distingue de verdad la OOP de la programación procedimental: no se trata de reunir funciones alrededor de unos datos, sino de hacer imposible, por construcción, que esos datos acaben en un estado incoherente. Es la garantía que llevarás contigo a los capítulos sobre la herencia, sobre los traits y, sobre todo, al proyecto enterprise de la Parte IX.
