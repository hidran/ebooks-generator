# 26. Ereditarietà, interfacce, trait e membri statici

Dopo classi e oggetti, PHP offre una seconda serie di strumenti, tutti dedicati a un unico scopo: **riutilizzare** e **organizzare** il comportamento senza riscriverlo. Ereditarietà, classi astratte, interfacce, trait, membri statici e costanti di classe risolvono ciascuno un pezzo di questo problema. Ma vanno usati con misura, e vale la pena dirlo prima ancora di iniziare: questi strumenti aiutano molto quando *chiariscono* il modello — quando rendono più evidente come sono fatte le cose del tuo dominio — e complicano tutto quando li aggiungi solo per "fare OOP". Il criterio, in ogni paragrafo, sarà lo stesso: si usa lo strumento se rende il codice più comprensibile, non perché esiste.

## Ereditarietà

Una classe può **estenderne** un'altra, ereditandone proprietà e metodi:

```php
<?php
class Animale
{
    public function dorme(): string
    {
        return "zzz";
    }
}

class Cane extends Animale
{
    public function abbaia(): string
    {
        return "bau";
    }
}
```

Codice completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/it/parte-07/cap-26/listing-01.php)


`Cane` non dichiara `dorme()`, eppure può usarlo: lo ha ereditato da `Animale`. La parola chiave `extends` stabilisce che ogni cane *è* anche un animale, e questa è la chiave per capire quando usare l'ereditarietà: esprime una relazione **"è un"**. Un cane è un animale, un `AdminController` è un `Controller`, una `SqlException` è un'`Exception`. Usala solo quando questa frase è vera nel tuo dominio. C'è però un avvertimento da tenere presente fin da subito: l'ereditarietà è il legame **più stretto** che due classi possano avere, perché la figlia dipende dai dettagli interni della madre. Cambiare la classe base rischia di rompere tutte le figlie. Per questo, quando ti serve solo riusare del codice — e non c'è una vera relazione "è un" — è quasi sempre meglio la **composizione** (contenere un oggetto e delegargli il lavoro) che l'ereditarietà.

## Override dei metodi

Una classe figlia può **ridefinire** un metodo ereditato, dandogli un comportamento diverso:

```php
<?php
class Gatto extends Animale
{
    public function dorme(): string
    {
        return "il gatto dorme sul divano";
    }
}
```

Codice completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/it/parte-07/cap-26/listing-02.php)


`Gatto` eredita `dorme()` da `Animale`, ma lo sostituisce con la propria versione: è l'**override**. Da questo momento, chiamare `dorme()` su un gatto esegue il codice del gatto, non quello dell'animale. C'è una regola non scritta ma importante: un override dovrebbe rispettare il "contratto" del metodo originale — se `dorme()` promette di restituire una stringa, la versione ridefinita deve continuare a farlo, altrimenti il codice che usa `Animale` senza sapere che tipo concreto ha davanti si troverà spiazzato. A volte non vuoi sostituire del tutto il comportamento del genitore, ma **aggiungere** qualcosa al suo:

```php
<?php
return parent::dorme() . " sul divano";
```

Codice completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/it/parte-07/cap-26/listing-03.php)


`parent::` chiama la versione del metodo definita nella classe madre. Così puoi riusare quello che il genitore fa già e poi estenderlo, invece di riscriverlo da capo: è il modo pulito di specializzare un comportamento senza duplicarlo.

## Classi e metodi final

La parola chiave `final` fa il contrario dell'ereditarietà: **impedisce** di estendere una classe o di ridefinire un metodo.

```php
<?php
final class Money
{
}
```

Codice completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/it/parte-07/cap-26/listing-04.php)


Una classe `final` non può essere estesa; in alternativa puoi sigillare un singolo metodo:

```php
<?php
class Service
{
    final public function execute(): void
    {
    }
}
```

Codice completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/it/parte-07/cap-26/listing-05.php)


Perché mai vorresti *impedire* l'ereditarietà, dopo averla appena introdotta? Perché ogni punto di estensione è anche un punto di **fragilità**: se una classe può essere estesa e i suoi metodi sovrascritti, devi garantire che continui a funzionare qualunque cosa facciano le figlie. `final` toglie questa preoccupazione e stabilizza un comportamento che non deve essere alterato — un oggetto valore come `Money`, per esempio, dove la logica dei calcoli deve restare esattamente quella. Molti sviluppatori esperti adottano la filosofia "final di default": rendi estendibile solo ciò che hai progettato apposta per esserlo, e sigilla il resto.

## Classi astratte

Una **classe astratta** sta a metà tra una classe normale e un'interfaccia: non può essere istanziata direttamente, e può obbligare le figlie a implementare certi metodi.

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

Codice completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/it/parte-07/cap-26/listing-06.php)


`Controller` non ha senso da solo — `new Controller()` è un errore — perché rappresenta un concetto incompleto: manca l'implementazione di `index()`, dichiarato `abstract`, cioè promesso ma non scritto. Ogni controller concreto (un `HomeController`, un `UserController`) dovrà estenderlo e fornire il proprio `index()`. In cambio, però, eredita già `render()`, che è scritto per intero. È esattamente questa la forza della classe astratta: **condivide il codice comune** a tutte le figlie e nello stesso tempo **impone un contratto parziale**, la lista dei metodi che ognuna deve completare. È lo schema del *template method*: il genitore definisce lo scheletro, le figlie riempiono i buchi. Riconoscerai questa struttura nel `Controller` base della Parte IX.

## Interfacce

Un'interfaccia porta l'idea di contratto all'estremo: dichiara **cosa** una classe deve offrire, senza dire **come**.

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

Codice completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/it/parte-07/cap-26/listing-07.php)


L'interfaccia `Logger` non contiene codice: dice soltanto che chiunque voglia essere un logger deve avere un metodo `info(string): void`. `FileLogger` firma questo contratto con `implements Logger` e ne fornisce la sua versione, che scrive su file. Domani potresti scrivere un `DatabaseLogger` o un `NullLogger`: purché rispettino l'interfaccia, per il resto del codice sono intercambiabili. Ed è qui che sta il vero vantaggio — programmare **contro il contratto** e non contro l'implementazione:

```php
<?php
function run(Logger $logger): void
{
    $logger->info("Avvio applicazione");
}
```

Codice completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/it/parte-07/cap-26/listing-08.php)


`run()` non dipende da `FileLogger`: dipende da `Logger`, cioè da "qualcosa che sa fare logging". Non gli importa quale sia l'oggetto concreto, purché rispetti il contratto. Questo è il **principio di inversione delle dipendenze** — la "D" di SOLID — e sarà il fondamento del container della Parte IX: il codice di alto livello dipende da astrazioni, non da classi concrete. Nota anche la differenza pratica rispetto alle classi: una classe può implementare **molte** interfacce ma estendere **una sola** classe, ed è per questo che le interfacce sono lo strumento preferito per descrivere le capacità di un oggetto.

## Trait

Un **trait** risolve un problema che né l'ereditarietà né le interfacce affrontano bene: riusare lo stesso *codice* in classi che non hanno tra loro alcuna relazione "è un".

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

Codice completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/it/parte-07/cap-26/listing-09.php)


Un `Post`, un `Commento` e un `Utente` non sono la stessa cosa, ma potrebbero tutti aver bisogno di un metodo `touch()` che aggiorni la data di modifica. Metterlo in una classe base comune sarebbe forzato — non c'è una vera gerarchia — e ripeterlo in ognuna violerebbe il DRY. Il trait offre la terza via: `use HasTimestamps` incolla quel metodo dentro `Post` come se fosse scritto lì. È un riuso **orizzontale**, che taglia attraverso le gerarchie. Comodissimo, ma con un rischio da conoscere: il trait usa `$this->updatedAt`, una proprietà che *non dichiara* — dà per scontato che la classe ospite ce l'abbia. Questa dipendenza nascosta è il difetto tipico dei trait: se ne abusi, ti ritrovi con classi che si aspettano proprietà e metodi arrivati da chissà quale trait, e il codice diventa difficile da seguire. Usali per piccoli comportamenti ben definiti, non come scorciatoia per evitare di progettare.

## Costanti di classe

Una costante di classe è un valore fisso, con un nome, legato alla classe:

```php
<?php
class Role
{
    public const ADMIN = "admin";
    public const USER = "user";
}

if ($role === Role::ADMIN) {
    echo "Accesso al pannello amministratore";
}
```

Codice completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/it/parte-07/cap-26/listing-10.php)


Il valore delle costanti sta nel confronto tra `Role::ADMIN` e la stringa nuda `"admin"`. Se scrivi `"admin"` sparso in venti punti del codice e un giorno ne batti uno sbagliato — `"admni"` — hai un bug silenzioso: la condizione è semplicemente falsa, senza errori. Con `Role::ADMIN`, invece, un refuso nel nome della costante è un errore immediato ("costante non definita"), perché PHP la conosce. Le costanti danno un nome ai valori "magici", li centralizzano in un posto solo e li rendono a prova di refuso — esattamente i ruoli che nel progetto della Parte VI comparivano sparsi come stringhe.

## Proprietà e metodi statici

Un membro **statico** appartiene alla classe stessa, non alle singole istanze:

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

Codice completo: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/it/parte-07/cap-26/listing-11.php)


C'è una sola `$count`, condivisa da tutta la classe: non serve creare un oggetto per usarla, la chiami direttamente con `Counter::increment()`, e il suo valore persiste tra una chiamata e l'altra. Questo la rende comoda per contatori, utility senza stato e semplici factory. Ma proprio perché è condivisa e sempre raggiungibile, uno stato statico è di fatto uno **stato globale**, con tutti i suoi difetti: è difficile da testare (i test si influenzano a vicenda tramite quel valore condiviso), e nasconde una dipendenza, perché una funzione che chiama `Counter::increment()` non dichiara da nessuna parte di dipendere da `Counter`. Usa `static` con parsimonia: va benissimo per utility pure e factory, molto meno per la logica di dominio, dove rende test e dipendenze più rigidi.

## `self` e `static`

Quando un metodo statico deve riferirsi alla propria classe, hai due parole chiave, e la differenza conta nelle gerarchie:

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

Codice completo: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-26/it/parte-07/cap-26/listing-12.php)


`self` fa riferimento alla classe **in cui il metodo è scritto**, e resta fissa lì. `static`, invece, usa il *late static binding*: si riferisce alla classe **effettivamente chiamata** a runtime. La differenza salta fuori con l'ereditarietà: se `User extends Model` e chiami `User::make()`, la versione con `new static()` restituisce un `User`, mentre `new self()` restituirebbe sempre un `Model`, ignorando la figlia. Ecco perché `static` è importante nelle factory e nelle gerarchie dove il metodo deve produrre l'istanza della classe **figlia**, non del genitore in cui è stato scritto.

## In sintesi

Ereditarietà, interfacce, trait e membri statici sono strumenti potenti, ciascuno adatto a un tipo di riuso diverso: l'**ereditarietà** modella la relazione "è un" (ma è il legame più stretto, quindi usala con cautela); le **interfacce** definiscono contratti e sono la base dell'inversione delle dipendenze; le **classi astratte** condividono struttura e impongono un contratto parziale; i **trait** riusano piccoli comportamenti in orizzontale; le **costanti** danno un nome ai valori magici; `static` gestisce funzionalità legate alla classe più che all'istanza, con la cautela dello stato globale. La scelta giusta, ogni volta, è quella che rende il codice più comprensibile — non quella che infila il maggior numero possibile di concetti OOP.
