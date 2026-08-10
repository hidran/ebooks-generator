# Capítulo 6 — Salida estructurada

::: {.callout .callout-tip}
[El código de este capítulo]{.callout-title}

La versión ejecutable de cada listado que sigue está en [`chapters/Ch06`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch06), en el repositorio complementario. Clónalo, ejecuta `composer install` y los ejemplos funcionan contra un Ollama local sin ninguna clave de API.
:::

## 6.1 Por qué existe la salida estructurada

Sacar objetos tipados de un modelo de lenguaje es la funcionalidad que convierte una demo de IA en una pieza de software.

### El problema

Todo lo anterior ha producido prosa. La prosa está bien cuando la lee una persona. Es inútil cuando el paso siguiente es `$order->save()`.

El enfoque ingenuo es pedir JSON en el prompt y parsearlo:

```php
$response = $agent->chat(new UserMessage(
    'Extract the order details as JSON with keys name, items, total.'
))->getMessage()->getContent();

$data = json_decode($response, true); // 🤞
```

Esto falla de maneras individualmente pequeñas y colectivamente fatales:

- El modelo envuelve el JSON en un bloque de código markdown
- Añade una frase amable antes del JSON
- Usa `total_amount` en lugar de `total` una de cada veinte ejecuciones
- Devuelve una cadena donde esperabas un número
- Omite un campo por completo cuando el texto de origen no lo mencionaba
- Alucina un campo extra que nunca pediste

Cada uno de esos es un incidente de producción, y la Sección 1.5 ya te dijo por qué no puedes salir de esto a base de pruebas: la misma entrada produce salidas distintas.

### Qué hace NeuronAI en su lugar

Dos capas, y la separación entre ellas es la clave del diseño:

**Capa 1 — Esquema.** Defines una clase PHP con declaraciones de tipo estrictas y atributos `#[SchemaProperty]`. NeuronAI genera el JSON Schema correspondiente a partir de tu clase y lo envía al modelo como parte de la petición. Al modelo se le *dice* qué forma debe producir.

**Capa 2 — Validación.** Adjuntas atributos de validación a las properties. NeuronAI parsea la respuesta, la valida contra esas reglas y —crucialmente— **si la validación falla, reintenta, diciéndole al modelo exactamente qué properties estaban mal.**

Recibes de vuelta una instancia de tu clase. Tipada. Validada. Lista para persistir.

> La capa 1 le dice al modelo qué quieres. La capa 2 comprueba si lo obtuviste y vuelve a pedirlo si no.

La mayoría de las implementaciones de «modo JSON» de otros ecosistemas te dan solo la capa 1. El bucle de reintento con violaciones de la capa 2 es lo que marca la diferencia entre «suele funcionar» y «funciona».

### Dónde cambia esto tu arquitectura

La salida estructurada es lo que convierte a un agente en un **componente** en lugar de una funcionalidad de chat. Una vez que la salida es un objeto tipado, puedes:

- Persistirlo directamente
- Pasarlo a servicios de dominio existentes que no saben nada de IA
- Hacer asertos sobre su forma en pruebas: las pruebas por contrato de la Sección 1.5, por fin posible
- Poner un agente en mitad de un proceso de negocio con código determinista a ambos lados

Ese último es el gran desbloqueo arquitectónico. Componente no determinista, frontera determinista.

### Puntos clave

- Pedir y parsear falla de una docena de maneras pequeñas que en conjunto son imposibles de probar.
- Dos capas: generación de esquema a partir de clases PHP y luego validación con reintento.
- Un objeto tipado y validado es lo que permite que un agente viva dentro de un proceso de negocio normal.

## 6.2 Definir la clase de salida

### La forma básica

```php
<?php

namespace App\Neuron\Output;

use NeuronAI\StructuredOutput\SchemaProperty;

class Person
{
    #[SchemaProperty(
        description: 'The user name.',
        required: true
    )]
    public string $name;

    #[SchemaProperty(
        description: 'What the user love to eat.',
        required: false
    )]
    public string $preference;
}
```

Dos cosas generan el esquema:

**La declaración de tipo de PHP.** `public string $name` se convierte en un string en el JSON Schema. Por eso el tipado estricto no es aquí una preferencia de estilo: es el esquema. Una property sin tipo o `mixed` no le da nada al modelo con lo que trabajar.

**El atributo.** `#[SchemaProperty]` añade los metadatos que el tipo no puede expresar.

### La descripción hace el mismo trabajo que la descripción de una herramienta

`description` es lo que el modelo lee para decidir qué va en el campo. `'The user name.'` es aceptable. `'The full name of the person placing the order, as written in the source text. Do not infer or complete partial names.'` es mejor, y elimina toda una clase de alucinaciones.

La fórmula en cuatro partes de la Sección 5.4 aplica, menos la parte del «cuándo usarla»: di qué es el campo, qué formato esperas y qué no hacer.

La propia recomendación de la documentación es definir siempre al menos `description` y `required`. Trátalo como un mínimo, no como un objetivo.

### Restricciones de esquema

`#[SchemaProperty]` acepta restricciones que entran en el propio JSON Schema:

```php
class Person
{
    #[SchemaProperty(
        description: 'The user name.',
        required: true,
        minLength: 3,
        maxLength: 255,
    )]
    public string $name;

    #[SchemaProperty(
        description: 'What the user love to eat.',
        required: false,
        min: 18,
        max: 64,
    )]
    public ?int $age = null;
}
```

`minLength` / `maxLength` para cadenas, `min` / `max` para números.

**Estas son distintas de las reglas de validación, y la distinción importa.** Las restricciones de esquema van *al modelo*: son instrucciones dentro de la petición. Las reglas de validación (Sección 6.5) se ejecutan *sobre la respuesta*: son comprobaciones a posteriori.

Usa ambas. La restricción de esquema reduce la probabilidad de una violación; la regla de validación la caza cuando ocurre de todos modos.

### Properties opcionales

Fíjate en el patrón para los campos opcionales:

```php
#[SchemaProperty(description: '...', required: false)]
public ?int $age = null;
```

Tipo anulable, valor por defecto. Sin el valor por defecto, una property tipada sin inicializar lanza al accederse, lo que convierte «el modelo omitió un campo opcional» en un error fatal justo en el momento en que intentabas ser permisivo.

### Dónde poner estas clases

`App\Neuron\Output` en los ejemplos de la documentación. Cualquier convención sirve; elige una y mantenla, porque estas clases se multiplican deprisa y es fácil confundirlas con tus modelos de dominio.

**No uses tus modelos de Eloquent ni tus entidades de dominio como clases de salida.** Tienen relaciones, casts, ganchos de ciclo de vida y decenas de properties que el modelo no tiene por qué rellenar. Escribe un DTO dedicado y mapéalo en tu propio código. El DTO es un contrato con el modelo; tu entidad es un contrato con tu base de datos. Mantenerlos separados es el mismo instinto que mantiene los objetos de petición fuera de tu capa de persistencia.

### Puntos clave

- La declaración de tipo de PHP *es* el esquema: aquí el tipado estricto es obligatorio.
- `description` merece el mismo cuidado que la descripción de una herramienta.
- Las restricciones de esquema instruyen al modelo; las reglas de validación comprueban la respuesta. Usa ambas.
- Las properties opcionales necesitan un tipo anulable *y* un valor por defecto.
- Nunca uses una entidad de dominio como clase de salida.

## 6.3 Pedir salida estructurada

### Por llamada

```php
use NeuronAI\Chat\Messages\UserMessage;

$person = MyAgent::make()->structured(
    new UserMessage("I'm John and I like pizza!"),
    Person::class
);

echo $person->name . ' like ' . $person->preference;
// John like pizza
```

`structured()` en vez de `chat()`. El segundo argumento es la clase. Lo que vuelve es **una instancia de esa clase**: ni un envoltorio de respuesta, ni un mensaje. No llamas a `getMessage()`.

Esa diferencia en el tipo de retorno merece una pausa, porque acabas de pasar tres capítulos tecleando `->getMessage()->getContent()` y aquí lo buscarás por costumbre.

### Por agente

Cuando un agente produce siempre la misma forma, pon el contrato en la clase:

```php
class MyAgent extends Agent
{
    protected function getOutputClass(): string
    {
        return Person::class;
    }
}
```

```php
$person = MyAgent::make()
    ->structured(new UserMessage("I'm John and I like pizza"));

echo $person->name . ' like ' . $person->preference;
```

**El detalle que pilla a todo el mundo:** sigues teniendo que llamar a `structured()`. `getOutputClass()` fija la forma por defecto; no cambia lo que hace `chat()`. Llamar a `chat()` en un agente con clase de salida sigue devolviendo prosa.

La documentación lo enuncia explícitamente —*siempre necesitas llamar al método `structured()` para exigir salida estricta*— precisamente porque es poco intuitivo.

### Cuál usar

**Por agente (`getOutputClass()`)** cuando el agente tiene un solo trabajo. `InvoiceExtractorAgent` siempre produce un `Invoice`. El contrato pertenece a la clase, donde un lector lo encuentra, y así ningún punto de llamada puede equivocarse.

**Por llamada** cuando el mismo agente sirve varias formas de extracción, o cuando la forma se elige en tiempo de ejecución.

Por defecto, por agente. Un agente con clase de salida declarada se autodocumenta, y compone mejor cuando después lo envuelvas como nodo de flujo de trabajo.

### Las tres formas de ejecutar un agente

| Método | Devuelve | Úsalo para |
|---|---|---|
| `chat()` | Respuesta → `getMessage()` → texto | Conversación |
| `structured()` | Una instancia de tu clase | Extracción de datos |
| `stream()` | Gestor → `events()` → fragmentos | Interfaz en tiempo real |

Mismo agente, mismas herramientas, mismo historial. Tres puntos de entrada, cada uno respaldado por un nodo distinto: `ChatNode`, `StructuredOutputNode`, `StreamingNode`. La Sección 2.3 dijo que las clases de nodo son API pública; este es el primer sitio donde lo notas.

### Puntos clave

- `structured($message, MyClass::class)` devuelve la instancia directamente.
- `getOutputClass()` fija una forma por defecto pero sigues teniendo que llamar a `structured()`.
- Prefiere el contrato por agente.
- Tres puntos de entrada, tres nodos, un agente.

## 6.4 Objetos anidados y arrays tipados

### Clases anidadas

Tipa una property como otra clase estructurada:

```php
<?php

namespace App\Neuron\Output;

use NeuronAI\StructuredOutput\SchemaProperty;
use NeuronAI\StructuredOutput\Validation\Rules\NotBlank;

class Person
{
    #[SchemaProperty(description: 'The user name.', required: true)]
    #[NotBlank]
    public string $name;

    #[SchemaProperty(description: 'What user love to eat.', required: true)]
    public string $preference;

    #[SchemaProperty(description: 'The address to complete the delivery.', required: true)]
    public Address $address;
}
```

```php
<?php

namespace App\Neuron\Output;

use NeuronAI\StructuredOutput\SchemaProperty;
use NeuronAI\StructuredOutput\Validation\Rules\NotBlank;

class Address
{
    #[SchemaProperty(description: 'The name of the street.', required: true)]
    #[NotBlank]
    public string $street;

    #[SchemaProperty(description: 'The name of the city.', required: false)]
    public string $city;

    #[SchemaProperty(description: 'The zip code of the address.', required: true)]
    #[NotBlank]
    public string $zip;
}
```

```php
$person = MyAgent::make()->structured(
    new UserMessage("I'm John and I want a pizza at st. James Street 00560!"),
    Person::class
);

echo $person->address->street;
// st.James Street
```

`$person->address` es una instancia de `Address`. Autocompletado completo del IDE, análisis estático completo, hasta el fondo.

::: {.callout .callout-warning}
[Advertencia sobre la documentación]{.callout-title}

El ejemplo de clases anidadas de la página oficial importa `NeuronAI\StructuredOutput\Property` (debería ser `SchemaProperty`) y `Symfony\Component\Validator\Constraints\NotBlank` / `Valid`, restos de antes de que el framework incluyera su propio componente de validación. El namespace correcto es `NeuronAI\StructuredOutput\Validation\Rules\NotBlank`, como se usa arriba. Copiar ese bloque literalmente no compila. Apéndice A, puntos 12 y 13.
:::

### Arrays de cadenas

Una property `array` simple es por defecto una lista de cadenas:

```php
#[SchemaProperty(description: 'A list of keywords.', required: true)]
public array $keywords;
```

### Arrays de objetos

Usa `anyOf`:

```php
class Person
{
    #[SchemaProperty(description: 'The user name.', required: true)]
    #[NotBlank]
    public string $name;

    #[SchemaProperty(
        description: 'The list of tag for the user profile.',
        required: true,
        anyOf: [Tag::class]
    )]
    public array $tags;
}
```

```php
class Tag
{
    #[SchemaProperty(description: 'The name of the tag', required: true)]
    #[NotBlank]
    public string $name;
}
```

PHP no puede expresar `Tag[]` en una declaración de tipo, así que `anyOf` lleva la información que el sistema de tipos no puede.

### Arrays de tipos mixtos

`anyOf` recibe una lista, y esa lista puede contener varias clases:

```php
class Report
{
    #[SchemaProperty(
        description: 'The content of the report',
        required: true,
        anyOf: [TextBlock::class, TableBlock::class, ImageBlock::class]
    )]
    public array $content;
}
```

NeuronAI mete las tres especificaciones en el esquema, y el modelo elige por elemento.

Esto es más potente de lo que parece a primera vista. Te permite modelar **documentos hechos de bloques heterogéneos**, la forma que hay detrás de todo CMS, constructor de páginas y editor de texto enriquecido modernos. Pedirle a un modelo que convierta un documento no estructurado en una lista ordenada de bloques tipados es uno de los casos de uso genuinamente fuertes de esta funcionalidad.

### Guía de diseño

**La profundidad cuesta precisión.** Cada nivel de anidamiento es otra oportunidad para una forma malformada. Dos niveles resulta cómodo, tres ya aprieta, cuatro significa que deberías extraer por etapas.

**Extrae por etapas cuando el documento sea grande.** Un agente produce la estructura de nivel superior con identificadores; un segundo agente rellena el detalle de cada elemento. Dos llamadas enfocadas ganan a una llamada con un esquema que el modelo satisface a medias. También es más barato, porque la segunda llamada lleva un esquema mucho más pequeño.

**Modela lo que necesitas, no lo que existe.** La factura de origen tiene cuarenta campos. Tu proceso usa seis. Extrae seis. Cada campo del esquema cuesta tokens en la petición y es otra oportunidad para una violación.

### Puntos clave

- Tipa una property como otro DTO para anidar; vuelve como una instancia.
- `anyOf: [Tag::class]` para arrays de objetos; el sistema de tipos de PHP no puede expresarlo solo.
- `anyOf` con varias clases modela documentos de bloques heterogéneos.
- Mantén poca profundidad; extrae por etapas; modela solo los campos que uses.

## 6.5 Validación y reintento

Esta es la sección más valiosa del capítulo. Es lo que hace que la salida estructurada sea fiable en lugar de meramente probable.

### El mecanismo

Los atributos de validación van en las properties de la clase de salida. Cuando el modelo responde, NeuronAI parsea los datos y los comprueba. **Si una o más properties fallan, NeuronAI reenvía la petición al modelo con un informe detallado de qué estaba mal**, y repite hasta que tiene éxito o alcanza el límite de reintentos.

Esa es la parte que hay que subrayar. No es «valida y lanza». Es «valida y dile al modelo en qué se equivocó para que pueda arreglarlo».

Le estás dando al modelo un error de compilación y pidiéndole que lo vuelva a intentar, que es, de hecho, exactamente en lo que es bueno.

### El valor por defecto

Por defecto NeuronAI reintenta **una vez** ante un fallo de validación. Un intento extra, con las violaciones incluidas.

### Configurarlo

```php
$person = MyAgent::make()->structured(
    messages: new UserMessage("I'm John and I like pizza!"),
    class: Person::class,
    maxRetries: 3
);
```

Cero desactiva el reintento: un solo intento.

```php
$person = MyAgent::make()->structured(
    messages: new UserMessage("I'm John and I like pizza!"),
    class: Person::class,
    maxRetries: 0
);
```

La orientación de la documentación es sensata: con un modelo menos capaz, equilibra la probabilidad de una respuesta válida frente al consumo de tokens. Cada reintento es una petición completa —esquema, prompt y el informe de violaciones—, así que los reintentos no son baratos. Esta es la aritmética de la Sección 1.4 apareciendo en un sitio nuevo.

**Valores prácticos:** modelo de frontera con un esquema simple → 1 (el valor por defecto). Modelo local pequeño, o un esquema anidado complejo → 2 o 3. Procesamiento por lotes donde un fallo puede reencolarse → 0, y gestiónalo en tu pipeline en lugar de pagar reintentos en línea.

### El catálogo de reglas

| Regla | Comprueba |
|---|---|
| `#[NotBlank]` | No vacío. Acepta `allowNull` |
| `#[Length]` | Longitud de cadena: `min`, `max`, `exactly` |
| `#[WordsCount]` | Número de palabras: `min`, `max`, `exactly` |
| `#[Count]` | Tamaño de array: `min`, `max`, `exactly` |
| `#[EqualTo]` / `#[NotEqualTo]` | Comparación estricta contra `reference` |
| `#[GreaterThan]` / `#[GreaterThanEqual]` | Cota numérica inferior |
| `#[LowerThan]` / `#[LowerThanEqual]` | Cota numérica superior |
| `#[OutOfRange]` | Número fuera de `min`–`max`; bandera `strict` |
| `#[IsTrue]` / `#[IsFalse]` | Booleano exacto |
| `#[IsNull]` / `#[IsNotNull]` | Anulabilidad |
| `#[Json]` | Cadena JSON válida |
| `#[Url]` | URL válida |
| `#[Email]` | Correo electrónico válido |
| `#[IpAddress]` | IP válida |
| `#[ArrayOf]` | Array de una clase dada |
| `#[Regex]` | Coincide con un patrón |

Todas bajo `NeuronAI\StructuredOutput\Validation\Rules\`.

### Las dos reglas que se ganan el sueldo

**`#[WordsCount]`** es inusual y genuinamente útil. Los límites de longitud en un prompt («no pases de 50 palabras») se siguen de forma laxa. Un atributo `#[WordsCount(min: 1, max: 50)]` se aplica, y una violación dispara un reintento con la queja concreta. Si generas resúmenes, títulos o meta descripciones con límites duros, esto convierte una petición blanda en un contrato.

```php
class Article
{
    #[SchemaProperty(description: 'SEO page title.', required: true)]
    #[WordsCount(max: 10)]
    public string $title;

    #[SchemaProperty(description: 'Meta description.', required: true)]
    #[WordsCount(min: 20, max: 30)]
    public string $description;
}
```

**`#[Regex]`** impone formatos que una restricción de esquema no puede expresar: SKU, referencias de pedido, códigos postales, códigos de cupón.

```php
class Coupon
{
    #[Regex('/^[A-Z]{2}\d{4}$/')]
    public string $code;
}
```

### Reglas propias

Las reglas son atributos PHP que extienden `AbstractValidationRule`:

```php
namespace App\Neuron\Output;

use Attribute;
use NeuronAI\StructuredOutput\Validation\Rules\AbstractValidationRule;

#[Attribute(Attribute::TARGET_PROPERTY)]
class MyFormatRule extends AbstractValidationRule
{
    public function __construct(protected string $format)
    {
    }

    public function validate(string $name, mixed $value, array &$violations): void
    {
        if (!is_string($value)) {
            $violations[] = $this->buildMessage($name, '{name} must be a string.');
            return;
        }

        if (!$this->respectFormat($value)) {
            $violations[] = $this->buildMessage(
                $name,
                '{name} must match the format {format}',
                ['format' => $this->format]
            );
        }
    }

    protected function respectFormat(string $value): bool
    {
        // your check
    }
}
```

```php
class Route
{
    #[MyFormatRule('apps/{id}/show')]
    public string $path;
}
```

::: {.callout .callout-warning}
[Ejemplo corregido]{.callout-title}

El ejemplo oficial de regla propia tiene tres errores pequeños: `respectFormat` se declara con un parámetro pero se llama con dos, se referencia `$this->pattern` donde se definió `$this->format`, y no hay retorno anticipado tras la violación de tipo. La versión de arriba está corregida. Apéndice A, punto 15.
:::

**El mensaje que escribes se le envía al modelo en el reintento.** Así que escríbelo como una instrucción, no como una queja. `'{name} must match the format apps/{id}/show'` le da al modelo algo sobre lo que actuar. `'{name} is invalid'` no.

Ese principio merece enunciarse aparte: **los mensajes de violación son prompts.** Cada uno que escribas es texto que un modelo de lenguaje leerá e intentará satisfacer.

### Reglas de negocio en la capa de validación

Las reglas de validación no tienen por qué ser comprobaciones de formato:

```php
class RefundRequest
{
    #[SchemaProperty(description: 'Refund amount in euros.', required: true)]
    #[GreaterThan(reference: 0)]
    #[LowerThanEqual(reference: 500)]
    public float $amount;

    #[SchemaProperty(description: 'Reason code.', required: true)]
    #[Regex('/^(DAMAGED|WRONG_ITEM|LATE|OTHER)$/')]
    public string $reason;
}
```

El modelo no puede producir un reembolso superior a 500 € ni un código de motivo no reconocido, no porque se lo pidieras educadamente, sino porque el objeto no validará y se le dirá que lo intente de nuevo.

Compara esto con poner «los reembolsos no deben superar los 500 euros» en el prompt de sistema. Una cosa es una petición. La otra es una restricción. Todo lo de la Sección 5.10 sobre ocultar frente a instruir aplica aquí de otra forma.

### Puntos clave

- Un fallo de validación dispara un reintento que le dice al modelo exactamente qué estaba mal.
- El valor por defecto es un reintento; ajústalo con `maxRetries`; `0` lo desactiva.
- Las restricciones de esquema instruyen; las reglas de validación imponen.
- Los mensajes de violación son prompts: escríbelos como instrucciones.
- Las reglas de negocio codificadas como validación son restricciones, no peticiones.

## 6.6 Salida estructurada frente a llamada a herramientas

### La confusión

Ambos implican un JSON Schema. Ambos producen datos estructurados. Ambos usan `#[SchemaProperty]` en la implementación de NeuronAI: la Sección 5.6 usó el mismo atributo para la *entrada* estructurada de herramientas.

Y sin embargo están en extremos opuestos de la interacción.

### La distinción

**La llamada a herramientas es entrada.** El modelo produce una petición estructurada para que *tu código se ejecute*. Los datos entran, tu función se ejecuta y el resultado vuelve al modelo. Es una llamada.

**La salida estructurada es el resultado terminal.** El modelo produce la respuesta final con una forma que *tu código consume*. No vuelve nada al modelo. Es un retorno.

| | Llamada a herramientas | Salida estructurada |
|---|---|---|
| Propósito | Pedirle a tu código que actúe | Entregar la respuesta final |
| Dirección | Modelo → tu función → modelo | Modelo → tu aplicación |
| Posición en el bucle | En medio, repetible | Al final, una vez |
| Método | `chat()` | `structured()` |
| Nodo | `ToolNode` | `StructuredOutputNode` |
| ¿Puede iterar? | Sí | No |

### La regla de decisión

**¿Necesita el modelo el resultado para seguir razonando?**

Sí → herramienta. No → salida estructurada.

*«Busca los pedidos de este cliente y dime si es comprador recurrente.»* El modelo necesita los datos de pedidos antes de poder juzgar. Herramienta.

*«Extrae el nombre, el correo y el total del pedido de este texto.»* No hay nada más sobre lo que razonar. Salida estructurada.

### Se componen

Un agente usa con frecuencia ambos en una sola ejecución, y esta es la forma que adopta la mayoría de los agentes de extracción reales:

```php
$invoice = InvoiceAgent::make()->structured(
    new UserMessage('Process the invoice at /uploads/inv-2291.pdf'),
    Invoice::class
);
```

Internamente: el agente llama a una herramienta `read_file` (llamada a herramientas), quizá llama a una herramienta `lookup_vendor` para resolver un código de proveedor (llamada a herramientas) y luego produce un objeto `Invoice` (salida estructurada). Herramientas en medio, estructura al final.

### El antipatrón

No uses una herramienta como forma de recibir el resultado final: una herramienta `save_result` a la que el modelo llama con los datos extraídos.

Parece funcionar, y es peor en todos los aspectos: sin validación, sin reintento con violaciones, sin valor de retorno tipado, y has convertido una respuesta terminal en un efecto colateral. Cuando el modelo la llame dos veces, tendrás un problema de duplicados que te has inventado tú solo.

Si los datos son la respuesta, usa `structured()`.

### La imagen especular

Merece nombrarse por simetría: la misma clase DTO puede servir en ambas direcciones. El `ObjectProperty(class: Color::class)` de la Sección 5.6 y el `structured($msg, Color::class)` de este capítulo usan la misma clase anotada.

Una sola clase `Address` puede definir qué acepta una herramienta *y* qué devuelve un agente. Ese es un beneficio real del diseño basado en atributos: un contrato, dos direcciones, definido una vez.

### Puntos clave

- Las herramientas son una llamada; la salida estructurada es un retorno.
- Pregúntate si el modelo necesita el resultado para seguir razonando.
- Se componen: herramientas en medio, estructura al final.
- Nunca uses una herramienta para entregar la respuesta final.

## Laboratorio 5 — Extraer pedidos de texto libre

**Cubre:** clases de salida, anidamiento, arrays tipados, validación con reintento.

### Objetivo

Los correos de pedido llegan como prosa no estructurada. Conviértelos en un objeto `Order` con líneas de pedido, totales y dirección de entrega, validado lo bastante bien como para que la siguiente línea de código pueda ser `$repository->save($order)`.

### La entrada

Trabaja con desorden de forma realista. Unos ejemplos contra los que probar:

```
Hi, I'd like to order 3 of the blue widgets (SKU BW-1120) at 12.50 each
and one of the large frames, WF-0080, 45 euros. Ship to 14 St James
Street, Leeds, LS1 4DA. Thanks — Jo Turner
```

```
order: 2x BW-1120, 1x WF-0080. total 70. same address as last time.
```

El segundo es el caso interesante: un total ambiguo, una dirección ausente y una referencia a información que el modelo no tiene. Decide qué debería hacer tu esquema al respecto antes de escribirlo.

### La forma

Tres clases. El esbozo, para que lo completes:

```php
class Order
{
    #[SchemaProperty(description: '...', required: true)]
    #[NotBlank]
    public string $customerName;

    #[SchemaProperty(description: '...', required: true, anyOf: [OrderLine::class])]
    #[Count(min: 1)]
    public array $lines;

    #[SchemaProperty(description: '...', required: true)]
    #[GreaterThan(reference: 0)]
    public float $total;

    #[SchemaProperty(description: '...', required: false)]
    public ?Address $deliveryAddress = null;
}
```

`OrderLine` lleva un SKU, una cantidad y un precio unitario. `Address` ya la tienes de la Sección 6.4.

### Requisitos

1. **El SKU es un formato, no una cadena.** Usa `#[Regex]` para que `BW-1120` valide y `blue widget` no.
2. **Las cantidades son enteros positivos.** A un modelo que lea «unos cuantos» y escriba `0` hay que decirle que lo intente otra vez.
3. **El total debe ser coherente** con las líneas de pedido. Este no es expresable como regla de property: decide si comprobarlo en tu propio código cuando vuelva el objeto o instruir al modelo en la descripción. Prueba ambas cosas y mira cuál falla menos.
4. **Una dirección ausente no debe ser un error fatal.** Opcional, anulable, con valor por defecto.
5. **Las descripciones deben prohibir la invención.** «Do not infer prices that are not stated in the text» pertenece a una `description`, y su ausencia es la causa más común de una extracción plausible y equivocada.

### Criterios de aceptación

- El ejemplo limpio produce un `Order` totalmente rellenado con dos líneas.
- El ejemplo desordenado produce un `Order` con dirección nula y no lanza excepción.
- Una entrada con un SKU malformado dispara un reintento, y el reintento tiene éxito. Registra la violación para demostrar que el reintento ocurrió de verdad y que no fue que el primer intento tuvo suerte.
- Con `maxRetries: 0`, esa misma entrada falla. Si no falla, tu validación no está haciendo nada.

### Ir más allá

Ejecuta todo el laboratorio contra un modelo local pequeño en Ollama y luego contra un modelo de frontera, con `maxRetries: 3` en ambos. Cuenta los reintentos que necesita cada uno. Ese número es el benchmark de selección de modelo más honesto de este libro, porque mide lo que de verdad te importa: con qué frecuencia la salida es utilizable sin una segunda pasada.
