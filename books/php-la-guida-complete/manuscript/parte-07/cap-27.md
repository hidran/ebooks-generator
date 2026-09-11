# 27. Tipi moderni, enum e magic method

Le versioni recenti di PHP hanno trasformato un linguaggio storicamente "permissivo" sui tipi in uno strumento capace di esprimere con precisione cosa una funzione accetta e cosa restituisce. Union type, intersection type, nullable, enum, nullsafe operator, magic method e property hook sono i pezzi di questa evoluzione: ti permettono di dire di più al lettore e al motore di PHP, e di lasciar emergere prima gli errori. Ma quasi tutti hanno anche un lato "furbo" che, usato senza disciplina, nasconde le decisioni invece di prenderle. Vediamoli uno per uno, con l'occhio sempre puntato su *quando* servono davvero.

## Union type

Un **union type** dichiara che un valore può essere di uno tra più tipi:

```php
<?php
function format_id(int|string $id): string
{
    return (string) $id;
}
```

Codice completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/it/parte-07/cap-27/listing-01.php)


`int|string` dice che `format_id` accetta un intero **oppure** una stringa, e niente altro. È onesto e utile quando una funzione riceve davvero forme diverse dello stesso concetto — un id che a volte arriva come numero e a volte come stringa. Ma attento all'abuso: un tipo serve a *restringere* ciò che può passare, ed è una promessa che chi legge la firma può fidarsi di certe garanzie. Se allarghi l'union finché accetta quasi tutto, la promessa si svuota. Non usare gli union type per evitare una decisione di design: se un valore può essere "qualsiasi cosa", il tipo non ti sta aiutando, ti sta solo permettendo di rimandare il problema.

## Tipo nullable

Un caso particolare e frequentissimo di union è quello con `null`:

```php
<?php
function find_user(int $id): ?array
{
    // ritorna array oppure null
}
```

Codice completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/it/parte-07/cap-27/listing-02.php)


Il punto interrogativo davanti al tipo — `?array` — è una scorciatoia per `array|null`. È la firma tipica delle funzioni `find`, dove non trovare il record **non è un errore** ma un esito normale e previsto: cerchi l'utente 42, potrebbe non esserci. Il valore di questo tipo è che rende l'assenza **esplicita nella firma**: chi chiama `find_user()` vede subito che il risultato può essere `null` e sa di doverlo gestire, invece di scoprirlo con un errore a runtime quando prova a usare un array che non c'è. Il tipo trasforma "forse manca" da sorpresa a informazione dichiarata.

## Intersection type

Se l'union chiede "uno *oppure* l'altro", l'**intersection type** chiede "l'uno *e* l'altro insieme":

```php
<?php
function export(Iterator&Countable $items): void
{
    echo count($items);
}
```

Codice completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/it/parte-07/cap-27/listing-03.php)


`Iterator&Countable` significa che `$items` deve soddisfare **entrambi** i contratti: deve essere iterabile *e* contabile. Dentro la funzione puoi quindi sia scorrerlo con un ciclo (perché è `Iterator`) sia passarlo a `count()` (perché è `Countable`), con la garanzia data dal tipo. È uno strumento più raro dell'union, ma prezioso quando una funzione ha bisogno di più capacità contemporaneamente da un oggetto: invece di accettare un tipo concreto specifico, componi i requisiti dalle interfacce, restando così aperto a qualunque classe le implementi.

## Nullsafe operator

Da PHP 8 l'operatore `?->` percorre una catena di oggetti fermandosi al primo `null`:

```php
<?php
$city = $user?->profile?->address?->city;
```

Codice completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/it/parte-07/cap-27/listing-04.php)


Senza `?->`, se `$user` non ha un profilo, `$user->profile->address` esploderebbe con un errore su `null`. Con il nullsafe, appena un anello della catena è `null`, l'intera espressione restituisce `null` e si ferma, senza sollevare errori: `$city` sarà semplicemente `null`. È comodo per navigare strutture opzionali annidate, ma nasconde un rischio. Se in quella catena c'è un oggetto che *dovrebbe sempre esserci* — un utente senza profilo è un dato incoerente, non una possibilità legittima — il nullsafe trasforma un bug in un silenzioso `null` che si propaga. Usalo dove l'assenza è davvero prevista, non per zittire stati che dovrebbero essere obbligatori.

## Enum

Un **enum** rappresenta un insieme **chiuso** di valori con un nome:

```php
<?php
enum Role
{
    case Admin;
    case User;
}
```

Codice completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/it/parte-07/cap-27/listing-05.php)


Nel capitolo precedente abbiamo usato le costanti di classe per dare un nome ai ruoli; l'enum fa un passo oltre e li rende un **tipo** a tutti gli effetti. `Role::Admin` e `Role::User` non sono stringhe: sono gli unici due valori possibili di `Role`, e PHP lo sa. La differenza si vede nel modo in cui puoi tipizzare una funzione:

```php
<?php
function can_delete(Role $role): bool
{
    return $role === Role::Admin;
}
```

Codice completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/it/parte-07/cap-27/listing-06.php)


`can_delete(Role $role)` accetta **solo** un valore di `Role`: non puoi passargli `"amdin"` scritto male, né `"superuser"` inventato. Un'intera categoria di bug — quelli in cui una stringa sbagliata scivola dentro una funzione — diventa semplicemente impossibile, perché il tipo la blocca prima ancora che il codice giri. Questo è il grande vantaggio degli enum rispetto alle costanti: non solo danno un nome ai valori, ma **restringono l'insieme** di ciò che può circolare.

## Backed enum

Un **backed enum** associa a ogni caso un valore scalare (una stringa o un intero):

```php
<?php
enum Role: string
{
    case Admin = "admin";
    case User = "user";
}
```

Codice completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/it/parte-07/cap-27/listing-07.php)


L'enum "puro" del paragrafo precedente vive solo in memoria; ma prima o poi un ruolo va **salvato nel database** o inviato in una risposta JSON, e lì servono valori scalari, non oggetti PHP. Il backed enum fa da ponte: ogni caso ha un `value` (`"admin"`, `"user"`) da persistere, e due metodi per fare il percorso inverso, dal valore all'enum:

```php
<?php
$role = Role::from("admin");
echo $role->value;
```

Codice completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/it/parte-07/cap-27/listing-08.php)


La scelta tra i due metodi di conversione è una decisione di sicurezza. `from()` lancia un'eccezione se il valore non corrisponde a nessun caso: lo usi quando il valore *deve* essere valido e un valore fuori insieme è un errore da far esplodere. `tryFrom()` invece restituisce `null` in caso di mancata corrispondenza: lo usi al confine con dati non fidati — un parametro della richiesta, una riga vecchia del database — dove un valore inatteso va gestito con grazia, non con un crash. La distinzione ricalca esattamente la logica *fail-loud* / *fail-closed* vista nel progetto della Parte VI.

## Metodi negli enum

Un enum non è solo un elenco di valori: può avere anche dei **metodi**.

```php
<?php
enum Role: string
{
    case Admin = "admin";
    case User = "user";

    public function label(): string
    {
        return match ($this) {
            self::Admin => "Amministratore",
            self::User => "Utente",
        };
    }
}
```

Codice completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/it/parte-07/cap-27/listing-09.php)


Il metodo `label()` restituisce l'etichetta leggibile del ruolo, scegliendola con un `match` sul caso corrente. Il vantaggio non è solo estetico: così il **comportamento legato al ruolo sta vicino ai valori possibili**, dentro lo stesso tipo, invece di essere sparso in `if` disseminati per l'applicazione. È il principio di coesione — ciò che cambia insieme sta insieme. E c'è un bonus dato dal `match`: se un domani aggiungi un `case Editor` e dimentichi di dargli un'etichetta, PHP solleva un errore perché il `match` non è più esaustivo. Il tipo ti costringe a non lasciare buchi.

## Magic method

I **magic method** sono metodi speciali che PHP chiama *automaticamente* in certe situazioni, senza che tu li invochi esplicitamente. Li riconosci dai due underscore iniziali. Sono potenti proprio perché impliciti — ma è la stessa implicitezza a renderli pericolosi, perché nascondono ciò che davvero accade.

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

Codice completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/it/parte-07/cap-27/listing-10.php)


PHP invoca `__get()` quando accedi a una proprietà **non accessibile o inesistente**: scrivendo `$data->qualcosa`, se `qualcosa` non è una proprietà pubblica, parte questo metodo con `"qualcosa"` come argomento. Qui restituisce il valore dall'array interno, realizzando di fatto un oggetto con proprietà "dinamiche", decise a runtime. Comodo per contenitori generici, ma con un costo pesante: guardando la classe non capisci più *quali* proprietà esistano davvero, l'IDE non può completarle e nessuno strumento di analisi statica può controllarle. Hai barattato chiarezza per flessibilità.

### `__call()`

```php
<?php
class Proxy
{
    public function __call(string $name, array $arguments): mixed
    {
        throw new BadMethodCallException("Metodo $name non trovato");
    }
}
```

Codice completo: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/it/parte-07/cap-27/listing-11.php)


`__call()` è l'equivalente di `__get()` per i metodi: PHP lo invoca quando chiami un metodo **non accessibile**, passandogli il nome e gli argomenti. Qui la classe lo usa in modo virtuoso, per *fallire ad alta voce*: invece di ignorare in silenzio una chiamata a un metodo inesistente, lancia un'eccezione chiara. È il mattone dei **proxy** e dei **decoratori**, oggetti che intercettano le chiamate per aggiungervi comportamento (logging, cache, controllo permessi) prima di girarle all'oggetto reale.

### `__callStatic()`

```php
<?php
class Facade
{
    public static function __callStatic(string $name, array $arguments): mixed
    {
        // delega a un servizio reale
    }
}
```

Codice completo: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-27/it/parte-07/cap-27/listing-12.php)


`__callStatic()` è la versione statica di `__call()`: intercetta le chiamate a metodi statici inesistenti. È il meccanismo dietro le **facade** di alcuni framework (Laravel su tutti), quelle API dall'aspetto statico — `Cache::get(...)`, `Route::get(...)` — che in realtà delegano dietro le quinte a un oggetto vero preso dal container. Danno una sintassi comoda, al prezzo di nascondere l'oggetto sottostante: un compromesso da conoscere prima di adottarlo.

## Property hook

PHP 8.4 introduce i **property hook**, che permettono di attaccare logica di lettura e scrittura direttamente a una proprietà, senza scrivere un getter e un setter separati. Il concetto avvicina proprietà e metodi: dal punto di vista di chi usa l'oggetto resta un semplice accesso `$oggetto->proprieta`, ma dietro può esserci una validazione in scrittura o un calcolo in lettura.

L'idea, in sostanza, è che una proprietà possa controllare il valore che le viene assegnato o calcolare al volo il valore che restituisce, riducendo il boilerplate dei classici getter/setter del Capitolo 25. E vale la solita cautela, la stessa dei magic method: non usare un hook per nascondere logica pesante là dove chi legge si aspetta il costo trascurabile di un semplice accesso a un dato. La sorpresa, nel codice, è sempre un difetto.

## In sintesi

I tipi moderni di PHP servono a rendere il codice **più esplicito**: gli union e gli intersection type dichiarano con precisione cosa una funzione accetta, il nullable rende visibile l'assenza, gli enum eliminano le stringhe magiche restringendo l'insieme dei valori possibili, e i backed enum fanno da ponte verso database e serializzazione. Sul versante dinamico, il nullsafe operator semplifica le catene opzionali e i magic method permettono comportamenti impliciti come proxy e facade. Il filo che li lega tutti è la disciplina: ognuno di questi strumenti va usato quando rende il **modello più chiaro** — non quando serve a stupire o a rimandare una decisione di design.
