# Capitolo 6 — Structured output

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

La versione eseguibile di ogni listato che segue si trova in [`chapters/Ch06`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch06), nel repository di accompagnamento. Clonalo, esegui `composer install` e gli esempi funzionano su un Ollama locale senza alcuna API key.
:::

## 6.1 Perché esiste lo structured output

Ottenere oggetti tipizzati da un modello linguistico è la funzionalità che trasforma una demo AI in un pezzo di software.

### Il problema

Finora tutto ha prodotto prosa. La prosa va bene quando la legge un essere umano. È inutile quando il passo successivo è `$order->save()`.

L'approccio ingenuo è chiedere JSON nel prompt e farne il parsing:

```php
$response = $agent->chat(new UserMessage(
    'Extract the order details as JSON with keys name, items, total.'
))->getMessage()->getContent();

$data = json_decode($response, true); // 🤞
```

Fallisce in modi individualmente piccoli e collettivamente fatali:

- Il modello avvolge il JSON in un blocco di codice markdown
- Aggiunge una frase cordiale prima del JSON
- Usa `total_amount` invece di `total` una volta su venti
- Restituisce una stringa dove ti aspettavi un numero
- Omette del tutto un campo quando il testo di origine non lo menzionava
- Allucina un campo in più che non avevi chiesto

Ognuno di questi è un incidente di produzione, e la Sezione 1.5 ti ha già detto perché non puoi uscirne con i test: lo stesso input produce output diversi.

### Che cosa fa invece NeuronAI

Due livelli, e la separazione fra loro è l'intuizione di progetto:

**Livello 1 — Schema.** Definisci una classe PHP con type hint stretti e attributi `#[SchemaProperty]`. NeuronAI genera il corrispondente JSON schema dalla tua classe e lo manda al modello come parte della richiesta. Al modello viene *detta* la forma che deve produrre.

**Livello 2 — Validazione.** Attacchi attributi di validazione alle proprietà. NeuronAI fa il parsing della risposta, la valida contro quelle regole e — cosa cruciale — **se la validazione fallisce riprova, dicendo al modello esattamente quali proprietà erano sbagliate.**

Ti torna indietro un'istanza della tua classe. Tipizzata. Validata. Pronta da persistere.

> Il livello 1 dice al modello che cosa vuoi. Il livello 2 verifica se l'hai ottenuto, e lo richiede di nuovo se non è così.

La maggior parte delle implementazioni di "modalità JSON" in altri ecosistemi ti dà solo il livello 1. Il ciclo di riprova-con-violazioni del livello 2 è ciò che fa la differenza fra "di solito funziona" e "funziona".

### Dove questo cambia la tua architettura

Lo structured output è ciò che rende un agent un **componente** invece di una funzionalità di chat. Una volta che l'output è un oggetto tipizzato puoi:

- Persisterlo direttamente
- Passarlo a servizi di dominio esistenti che non sanno nulla di AI
- Asserire sulla sua forma nei test — il contract testing della Sezione 1.5, finalmente possibile
- Mettere un agent in mezzo a un processo aziendale con codice deterministico da entrambi i lati

Quest'ultimo è il grande sblocco architetturale. Componente non deterministico, confine deterministico.

### Punti chiave

- Chiedi-e-fai-parsing fallisce in una dozzina di piccoli modi che nell'insieme non sono testabili.
- Due livelli: generazione dello schema da classi PHP, poi validazione con riprova.
- Un oggetto tipizzato e validato è ciò che permette a un agent di stare dentro un normale processo aziendale.

## 6.2 Definire la classe di output

### La forma di base

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

Due cose generano lo schema:

**Il type hint PHP.** `public string $name` diventa una stringa nel JSON schema. È per questo che la tipizzazione stretta qui non è una preferenza stilistica: *è* lo schema. Una proprietà non tipizzata o `mixed` non dà al modello nulla su cui lavorare.

**L'attributo.** `#[SchemaProperty]` aggiunge i metadati che il tipo non può esprimere.

### La descrizione fa lo stesso lavoro della descrizione di un tool

`description` è ciò che il modello legge per decidere che cosa va nel campo. `'The user name.'` è adeguata. `'Il nome completo della persona che effettua l'ordine, come scritto nel testo di origine. Non dedurre né completare nomi parziali.'` è migliore, ed elimina una classe di allucinazioni.

La formula in quattro parti della Sezione 5.4 si applica, meno la parte "quando usarlo": di' che cos'è il campo, che formato ti aspetti e che cosa non fare.

La raccomandazione della documentazione stessa è di definire sempre almeno `description` e `required`. Trattalo come un minimo, non come un obiettivo.

### Vincoli di schema

`#[SchemaProperty]` accetta vincoli che finiscono nel JSON schema stesso:

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

`minLength` / `maxLength` per le stringhe, `min` / `max` per i numeri.

**Questi sono diversi dalle regole di validazione, e la distinzione conta.** I vincoli di schema vanno *al modello*: sono istruzioni nella richiesta. Le regole di validazione (Sezione 6.5) girano *sulla risposta*: sono controlli a posteriori.

Usa entrambi. Il vincolo di schema riduce la probabilità di una violazione; la regola di validazione la intercetta quando accade comunque.

### Proprietà opzionali

Nota il pattern per i campi opzionali:

```php
#[SchemaProperty(description: '...', required: false)]
public ?int $age = null;
```

Tipo nullable, valore di default. Senza il default, una proprietà tipizzata non inizializzata solleva un'eccezione quando vi accedi — il che trasforma "il modello ha omesso un campo opzionale" in un errore fatale esattamente nel momento in cui stavi cercando di essere indulgente.

### Dove mettere queste classi

`App\Neuron\Output` negli esempi della documentazione. Qualunque convenzione va bene; scegline una e mantienila, perché queste classi si moltiplicano in fretta ed è facile confonderle con i tuoi modelli di dominio.

**Non usare i tuoi modelli Eloquent o le entità di dominio come classi di output.** Hanno relazioni, cast, hook di ciclo di vita e decine di proprietà che il modello non ha alcun titolo a popolare. Scrivi un DTO dedicato e mappalo nel tuo codice. Il DTO è un contratto con il modello; la tua entità è un contratto con il tuo database. Tenerli separati è lo stesso istinto che tiene gli oggetti richiesta fuori dal layer di persistenza.

### Punti chiave

- Il type hint PHP *è* lo schema: qui la tipizzazione stretta è obbligatoria.
- `description` merita la stessa cura della descrizione di un tool.
- I vincoli di schema istruiscono il modello; le regole di validazione controllano la risposta. Usa entrambi.
- Le proprietà opzionali richiedono un tipo nullable *e* un default.
- Non usare mai un'entità di dominio come classe di output.

## 6.3 Richiedere structured output

### Per chiamata

```php
use NeuronAI\Chat\Messages\UserMessage;

$person = MyAgent::make()->structured(
    new UserMessage("I'm John and I like pizza!"),
    Person::class
);

echo $person->name . ' like ' . $person->preference;
// John like pizza
```

`structured()` invece di `chat()`. Il secondo argomento è la classe. Ciò che torna indietro è **un'istanza di quella classe** — non un wrapper di risposta, non un messaggio. Non chiami `getMessage()`.

Vale la pena fermarsi su quella differenza di tipo di ritorno, perché hai appena passato tre capitoli a digitare `->getMessage()->getContent()` e qui lo cercherai per abitudine.

### Per agent

Quando un agent produce sempre la stessa forma, metti il contratto nella classe:

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

**Il dettaglio che frega tutti:** devi comunque chiamare `structured()`. `getOutputClass()` imposta la forma di default; non cambia ciò che fa `chat()`. Chiamare `chat()` su un agent con una classe di output restituisce comunque prosa.

La documentazione lo dichiara esplicitamente — *devi sempre chiamare il metodo `structured()` per richiedere output stretto* — proprio perché è controintuitivo.

### Quale usare

**Per agent (`getOutputClass()`)** quando l'agent ha un solo lavoro. `InvoiceExtractorAgent` produce sempre una `Invoice`. Il contratto appartiene alla classe, dove un lettore lo trova, e nessun punto di chiamata può sbagliarlo.

**Per chiamata** quando lo stesso agent serve più forme di estrazione, o quando la forma viene scelta a runtime.

Per default, usa il contratto per agent. Un agent con una classe di output dichiarata si autodocumenta, e si compone meglio quando più avanti lo avvolgerai come nodo di workflow.

### I tre modi di eseguire un agent

| Metodo | Restituisce | Usalo per |
|---|---|---|
| `chat()` | Risposta → `getMessage()` → testo | Conversazione |
| `structured()` | Un'istanza della tua classe | Estrazione di dati |
| `stream()` | Handler → `events()` → chunk | Interfaccia in tempo reale |

Stesso agent, stessi tool, stessa cronologia. Tre punti d'ingresso, ciascuno servito da un nodo diverso — `ChatNode`, `StructuredOutputNode`, `StreamingNode`. La Sezione 2.3 diceva che le classi dei nodi sono API pubblica; questo è il primo posto in cui lo senti.

### Punti chiave

- `structured($message, MyClass::class)` restituisce direttamente l'istanza.
- `getOutputClass()` imposta una forma di default ma devi comunque chiamare `structured()`.
- Preferisci il contratto per agent.
- Tre punti d'ingresso, tre nodi, un agent.

## 6.4 Oggetti annidati e array tipizzati

### Classi annidate

Tipizza una proprietà come un'altra classe strutturata:

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

`$person->address` è un'istanza di `Address`. Completamento completo nell'IDE, analisi statica completa, fino in fondo.

::: {.callout .callout-warning}
[Avvertenza sulla documentazione]{.callout-title}

L'esempio con classi annidate sulla pagina ufficiale importa `NeuronAI\StructuredOutput\Property` (dovrebbe essere `SchemaProperty`) e `Symfony\Component\Validator\Constraints\NotBlank` / `Valid` — residui di prima che il framework avesse un proprio componente di validazione. Il namespace corretto è `NeuronAI\StructuredOutput\Validation\Rules\NotBlank`, come usato sopra. Copiare quel blocco alla lettera non compila. Appendice A, punti 12 e 13.
:::

### Array di stringhe

Una semplice proprietà `array` è per default un elenco di stringhe:

```php
#[SchemaProperty(description: 'A list of keywords.', required: true)]
public array $keywords;
```

### Array di oggetti

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

PHP non può esprimere `Tag[]` in un type hint, quindi `anyOf` porta l'informazione che il sistema di tipi non può.

### Array di tipi misti

`anyOf` prende un elenco, e quell'elenco può contenere più classi:

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

NeuronAI mette tutte e tre le specifiche nello schema, e il modello sceglie elemento per elemento.

È più potente di quanto sembri a prima vista. Ti permette di modellare **documenti fatti di blocchi eterogenei** — la forma dietro ogni CMS moderno, page builder ed editor di testo ricco. Chiedere a un modello di convertire un documento non strutturato in un elenco ordinato di blocchi tipizzati è uno dei casi d'uso genuinamente forti di questa funzionalità.

### Indicazioni di progetto

**La profondità costa accuratezza.** Ogni livello di annidamento è un'altra occasione per una forma malformata. Due livelli sono comodi, tre stanno tirando, quattro significa che dovresti estrarre a stadi.

**Estrai a stadi quando il documento è grande.** Un agent produce la struttura di primo livello con gli identificativi; un secondo agent riempie il dettaglio per ciascun elemento. Due chiamate focalizzate battono una chiamata con uno schema che il modello soddisfa a metà. È anche più economico, perché la seconda chiamata porta uno schema molto più piccolo.

**Modella ciò che ti serve, non ciò che esiste.** La fattura di origine ha quaranta campi. Il tuo processo ne usa sei. Estraine sei. Ogni campo dello schema costa token nella richiesta ed è un'altra occasione di violazione.

### Punti chiave

- Tipizza una proprietà come un altro DTO per l'annidamento; torna indietro come istanza.
- `anyOf: [Tag::class]` per array di oggetti; il sistema di tipi di PHP non può esprimerlo da solo.
- `anyOf` con più classi modella documenti a blocchi eterogenei.
- Tieni bassa la profondità; estrai a stadi; modella solo i campi che usi.

## 6.5 Validazione e riprova

È la sezione di maggior valore del capitolo. È ciò che rende lo structured output affidabile invece che semplicemente probabile.

### Il meccanismo

Gli attributi di validazione vanno sulle proprietà della classe di output. Quando il modello risponde, NeuronAI fa il parsing dei dati e li verifica. **Se una o più proprietà falliscono, NeuronAI rimanda la richiesta al modello con un rapporto dettagliato di che cosa era sbagliato**, e ripete finché non ha successo o non raggiunge il limite di riprove.

È la parte da enfatizzare. Non è "valida e solleva un'eccezione". È "valida e di' al modello che cosa ha sbagliato perché possa correggerlo".

Stai dando al modello un errore di compilazione e chiedendogli di riprovare — cosa in cui, di fatto, è esattamente bravo.

### Il default

Per default NeuronAI riprova **una volta** in caso di fallimento della validazione. Un tentativo extra, con le violazioni incluse.

### Configurarlo

```php
$person = MyAgent::make()->structured(
    messages: new UserMessage("I'm John and I like pizza!"),
    class: Person::class,
    maxRetries: 3
);
```

Zero disabilita la riprova — un solo tentativo:

```php
$person = MyAgent::make()->structured(
    messages: new UserMessage("I'm John and I like pizza!"),
    class: Person::class,
    maxRetries: 0
);
```

L'indicazione della documentazione è sensata: con un modello meno capace, bilancia la probabilità di una risposta valida contro il consumo di token. Ogni riprova è una richiesta completa — schema, prompt e rapporto delle violazioni — quindi le riprove non sono economiche. È l'aritmetica della Sezione 1.4 che ricompare in un posto nuovo.

**Valori pratici:** modello di frontiera con schema semplice → 1 (il default). Piccolo modello locale, o schema annidato complesso → 2 o 3. Elaborazione batch dove un fallimento può essere rimesso in coda → 0, e gestiscilo nella tua pipeline invece di pagare riprove inline.

### Il catalogo delle regole

| Regola | Verifica |
|---|---|
| `#[NotBlank]` | Non vuoto. Accetta `allowNull` |
| `#[Length]` | Lunghezza stringa: `min`, `max`, `exactly` |
| `#[WordsCount]` | Conteggio parole: `min`, `max`, `exactly` |
| `#[Count]` | Dimensione array: `min`, `max`, `exactly` |
| `#[EqualTo]` / `#[NotEqualTo]` | Confronto stretto con `reference` |
| `#[GreaterThan]` / `#[GreaterThanEqual]` | Limite inferiore numerico |
| `#[LowerThan]` / `#[LowerThanEqual]` | Limite superiore numerico |
| `#[OutOfRange]` | Numero fuori da `min`–`max`; flag `strict` |
| `#[IsTrue]` / `#[IsFalse]` | Booleano esatto |
| `#[IsNull]` / `#[IsNotNull]` | Nullabilità |
| `#[Json]` | Stringa JSON valida |
| `#[Url]` | URL valido |
| `#[Email]` | Email valida |
| `#[IpAddress]` | IP valido |
| `#[ArrayOf]` | Array di una data classe |
| `#[Regex]` | Corrisponde a un pattern |

Tutte sotto `NeuronAI\StructuredOutput\Validation\Rules\`.

### Le due regole che si guadagnano il posto

**`#[WordsCount]`** è insolita e genuinamente utile. I limiti di lunghezza in un prompt ("stai sotto le 50 parole") vengono seguiti alla larga. Un attributo `#[WordsCount(min: 1, max: 50)]` viene imposto, e una violazione innesca una riprova con la lamentela specifica. Se generi riassunti, titoli o meta description con limiti rigidi, questo trasforma una richiesta gentile in un contratto.

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

**`#[Regex]`** impone formati che un vincolo di schema non può esprimere — SKU, riferimenti d'ordine, codici postali, codici sconto:

```php
class Coupon
{
    #[Regex('/^[A-Z]{2}\d{4}$/')]
    public string $code;
}
```

### Regole personalizzate

Le regole sono attributi PHP che estendono `AbstractValidationRule`:

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
[Esempio corretto]{.callout-title}

L'esempio ufficiale di regola personalizzata ha tre piccoli bug: `respectFormat` è dichiarato con un parametro ma chiamato con due, si fa riferimento a `$this->pattern` dove era stato definito `$this->format`, e non c'è un return anticipato dopo la violazione di tipo. La versione qui sopra è corretta. Appendice A, punto 15.
:::

**Il messaggio che scrivi viene mandato al modello alla riprova.** Quindi scrivilo come istruzione, non come lamentela. `'{name} must match the format apps/{id}/show'` dà al modello qualcosa su cui agire. `'{name} is invalid'` no.

Quel principio merita di essere dichiarato a sé: **i messaggi di violazione sono prompt.** Ognuno che scrivi è testo che un modello linguistico leggerà e cercherà di soddisfare.

### Regole di business nel livello di validazione

Le regole di validazione non devono essere per forza controlli di formato:

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

Il modello non può produrre un rimborso oltre i 500 € o un codice motivo non riconosciuto — non perché gliel'hai chiesto gentilmente, ma perché l'oggetto non passerà la validazione e gli verrà detto di riprovare.

Confrontalo con il mettere "i rimborsi non devono superare i 500 euro" nel system prompt. Una è una richiesta. L'altra è un vincolo. Tutto ciò che la Sezione 5.10 diceva su nascondere invece di istruire vale qui in una forma diversa.

### Punti chiave

- Un fallimento di validazione innesca una riprova che dice al modello esattamente che cosa era sbagliato.
- Il default è una riprova; regolalo con `maxRetries`; `0` la disabilita.
- I vincoli di schema istruiscono; le regole di validazione impongono.
- I messaggi di violazione sono prompt: scrivili come istruzioni.
- Le regole di business codificate come validazione sono vincoli, non richieste.

## 6.6 Structured output e tool calling

### La confusione

Entrambi coinvolgono un JSON schema. Entrambi producono dati strutturati. Entrambi usano `#[SchemaProperty]` nell'implementazione NeuronAI — la Sezione 5.6 usava lo stesso attributo per l'*input* strutturato dei tool.

Eppure stanno alle estremità opposte dell'interazione.

### La distinzione

**Il tool calling è input.** Il modello produce una richiesta strutturata perché *il tuo codice possa girare*. I dati entrano, la tua funzione esegue, e il risultato torna al modello. È una chiamata.

**Lo structured output è il risultato terminale.** Il modello produce la risposta finale in una forma che *il tuo codice consuma*. Nulla torna al modello. È un ritorno.

| | Tool calling | Structured output |
|---|---|---|
| Scopo | Chiedere al tuo codice di agire | Consegnare la risposta finale |
| Direzione | Modello → la tua funzione → modello | Modello → la tua applicazione |
| Posizione nel ciclo | In mezzo, ripetibile | Alla fine, una volta |
| Metodo | `chat()` | `structured()` |
| Nodo | `ToolNode` | `StructuredOutputNode` |
| Può ciclare? | Sì | No |

### La regola decisionale

**Il modello ha bisogno del risultato per continuare a ragionare?**

Sì → tool. No → structured output.

*"Cerca gli ordini di questo cliente e dimmi se è un acquirente abituale."* Il modello ha bisogno dei dati d'ordine prima di poter giudicare. Tool.

*"Estrai nome, email e totale dell'ordine da questo testo."* Non c'è altro su cui ragionare. Structured output.

### Si compongono

Un agent usa spesso entrambi in una sola esecuzione, ed è la forma che assumono la maggior parte degli agent di estrazione reali:

```php
$invoice = InvoiceAgent::make()->structured(
    new UserMessage('Process the invoice at /uploads/inv-2291.pdf'),
    Invoice::class
);
```

Internamente: l'agent chiama un tool `read_file` (tool calling), magari chiama un tool `lookup_vendor` per risolvere un codice fornitore (tool calling), poi produce un oggetto `Invoice` (structured output). Tool in mezzo, struttura alla fine.

### L'anti-pattern

Non usare un tool come mezzo per ricevere il risultato finale — un tool `save_result` che il modello chiama con i dati estratti.

Sembra funzionare, ed è peggio sotto ogni aspetto: nessuna validazione, nessuna riprova-con-violazioni, nessun valore di ritorno tipizzato, e hai trasformato una risposta terminale in un effetto collaterale. Quando il modello lo chiama due volte, ora hai un problema di gestione dei duplicati che ti sei inventato da solo.

Se il dato è la risposta, usa `structured()`.

### L'immagine speculare

Vale la pena nominarlo per simmetria: la stessa classe DTO può servire in entrambe le direzioni. L'`ObjectProperty(class: Color::class)` della Sezione 5.6 e lo `structured($msg, Color::class)` di questo capitolo usano la stessa classe annotata.

Una classe `Address` può definire che cosa un tool accetta *e* che cosa un agent restituisce. È un vero vantaggio del progetto basato sugli attributi: un contratto, due direzioni, definito una volta sola.

### Punti chiave

- Il tool calling è una chiamata; lo structured output è un ritorno.
- Chiediti se il modello ha bisogno del risultato per continuare a ragionare.
- Si compongono: tool in mezzo, struttura alla fine.
- Non usare mai un tool per consegnare la risposta finale.

## Laboratorio 5 — Estrarre ordini da testo libero

**Copre:** classi di output, annidamento, array tipizzati, validazione con riprova.

### Obiettivo

Le email d'ordine arrivano come prosa non strutturata. Trasformale in un oggetto `Order` con righe, totali e indirizzo di consegna, validato abbastanza bene perché la riga di codice successiva possa essere `$repository->save($order)`.

### L'input

Lavora con disordine di forma realistica. Qualche esempio su cui provare:

```
Hi, I'd like to order 3 of the blue widgets (SKU BW-1120) at 12.50 each
and one of the large frames, WF-0080, 45 euros. Ship to 14 St James
Street, Leeds, LS1 4DA. Thanks — Jo Turner
```

```
order: 2x BW-1120, 1x WF-0080. total 70. same address as last time.
```

Il secondo è il caso interessante: un totale ambiguo, un indirizzo mancante e un riferimento a informazioni che il modello non ha. Decidi che cosa deve farne il tuo schema prima di scriverlo.

### La forma

Tre classi. Lo schizzo, che completerai tu:

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

`OrderLine` porta uno SKU, una quantità e un prezzo unitario. `Address` ce l'hai già dalla Sezione 6.4.

### Requisiti

1. **Lo SKU è un formato, non una stringa.** Usa `#[Regex]` così che `BW-1120` validi e `blue widget` no.
2. **Le quantità sono interi positivi.** A un modello che legge "qualcuno" e scrive `0` va detto di riprovare.
3. **Il totale deve essere coerente** con le righe. Questo non è esprimibile come regola di proprietà: decidi se verificarlo nel tuo codice dopo che l'oggetto è tornato, o se istruire il modello nella descrizione. Prova entrambe e vedi quale fallisce meno.
4. **Un indirizzo mancante non deve essere un errore fatale.** Opzionale, nullable, con default.
5. **Le descrizioni devono vietare l'invenzione.** "Non dedurre prezzi non dichiarati nel testo" appartiene a una `description`, e la sua assenza è la causa più comune di un'estrazione plausibile e sbagliata.

### Criteri di accettazione

- L'esempio pulito produce un `Order` completamente popolato con due righe.
- L'esempio disordinato produce un `Order` con indirizzo null e non solleva eccezioni.
- Un input con SKU malformato innesca una riprova, e la riprova ha successo. Logga la violazione per dimostrare che la riprova è davvero avvenuta e non che il primo tentativo è stato fortunato.
- Con `maxRetries: 0`, quello stesso input fallisce. Se non fallisce, la tua validazione non sta facendo nulla.

### Andare oltre

Esegui tutto il laboratorio contro un piccolo modello locale su Ollama, poi contro un modello di frontiera, con `maxRetries: 3` su entrambi. Conta le riprove necessarie a ciascuno. Quel numero è il benchmark più onesto di selezione del modello in questo libro, perché misura la cosa che ti interessa davvero: quanto spesso l'output è utilizzabile senza un secondo passaggio.
