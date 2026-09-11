# 25. Classi, oggetti, proprietà e costruttori

Fino a qui hai scritto funzioni che ricevono dati, li elaborano e restituiscono un risultato. La **programmazione orientata agli oggetti** propone un modo diverso di organizzare il codice: invece di tenere separati i dati (in variabili e array) e i comportamenti (in funzioni), li raccoglie insieme in un'unica unità. In PHP questa unità è la **classe**. Una classe descrive una categoria di cose — un'auto, un utente, un conto bancario — dicendo quali informazioni quelle cose portano con sé e cosa sanno fare. Un **oggetto** è un esemplare concreto di quella categoria: la classe `Auto` è il concetto "automobile", il singolo oggetto è *quella* automobile rossa che va a 50 all'ora. La distinzione tra classe e oggetto è la stessa che c'è tra la ricetta e la torta: la ricetta è una, le torte che ne sbucano sono molte e ciascuna con la sua vita.

Questo capitolo introduce i mattoni di base: come si definisce una classe, come si creano oggetti, come si descrive il loro stato con le proprietà e il loro comportamento con i metodi, e come si protegge quello stato perché resti sempre coerente. Sono le fondamenta su cui poggiano il progetto della Parte VI e l'intera architettura enterprise della Parte IX.

## Definire una classe

```php
<?php
class Auto
{
}
```

Codice completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-25/it/parte-07/cap-25/listing-01.php)


Anche vuota, questa classe è già qualcosa: hai definito un **nuovo tipo**, che d'ora in poi si affianca a `int`, `string` e `array`. Per convenzione il nome di una classe si scrive in **PascalCase**, con l'iniziale maiuscola e senza spazi: `Auto`, `UtenteRegistrato`, `CarrelloOrdine`. È una convenzione, non un obbligo del linguaggio, ma seguirla rende immediatamente riconoscibile un nome di classe rispetto a una variabile o a una funzione. Per creare un oggetto a partire dalla classe si usa `new`:

```php
<?php
$auto = new Auto();
var_dump($auto);
```

Codice completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-25/it/parte-07/cap-25/listing-02.php)


La parola chiave `new` chiede a PHP di **istanziare** la classe: alloca in memoria un nuovo oggetto e ne restituisce un riferimento, che qui finisce nella variabile `$auto`. Il `var_dump` mostra qualcosa come `object(Auto)#1 (0) { }`: un oggetto di tipo `Auto`, il primo creato (`#1`), con zero proprietà. L'oggetto esiste, ma è un guscio vuoto — non porta ancora nessun dato interessante. C'è un dettaglio che conviene fissare subito: ogni `new` produce un oggetto **distinto**. Se scrivessi `new Auto()` due volte otterresti due oggetti separati, con vite indipendenti, esattamente come due torte uscite dalla stessa ricetta. E, a differenza degli array, gli oggetti si passano **per riferimento**: assegnare `$auto` a un'altra variabile non copia l'oggetto, ma crea un secondo nome per lo stesso oggetto. È una differenza che avrà conseguenze pratiche importanti più avanti.

## Proprietà

Le **proprietà** sono le variabili che appartengono all'oggetto: descrivono il suo **stato**, cioè le informazioni che porta con sé in un dato momento.

```php
<?php
class Auto
{
    public string $colore;
    public int $velocita = 0;
}

$auto = new Auto();
$auto->colore = "rosso";
$auto->velocita = 50;
```

Codice completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-25/it/parte-07/cap-25/listing-03.php)


Ogni proprietà è dichiarata con un tipo (`string`, `int`) e può avere un valore iniziale: `$velocita = 0` significa che ogni auto nasce ferma, mentre `$colore` non ha un valore di partenza e va assegnato prima di leggerlo. L'operatore `->` è la chiave d'accesso: `$auto->colore` legge o scrive la proprietà `colore` di *quell'* oggetto. Ed è qui che si vede il senso di avere oggetti distinti: se creo due auto e do a una `colore = "rosso"` e all'altra `colore = "blu"`, i due valori non si pestano i piedi, perché ciascuna proprietà vive dentro il suo oggetto. Lo stato è **per istanza**, non condiviso: la classe dice *quali* proprietà esistono, ogni oggetto ne tiene la propria copia con i propri valori.

## Metodi

Se le proprietà sono lo stato, i **metodi** sono il comportamento: funzioni che vivono dentro la classe e possono agire sullo stato dell'oggetto.

```php
<?php
class Auto
{
    public int $velocita = 0;

    public function accelera(int $incremento): void
    {
        $this->velocita += $incremento;
    }
}

$auto = new Auto();
$auto->accelera(20);
```

Codice completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-25/it/parte-07/cap-25/listing-04.php)


La differenza tra un metodo e una funzione qualunque sta tutta in una parola: `$this`. Dentro un metodo, `$this` è **l'oggetto su cui il metodo è stato chiamato** — quando scrivi `$auto->accelera(20)`, dentro `accelera` la variabile `$this` *è* `$auto`, e quindi `$this->velocita` è la velocità di quella precisa auto. Un metodo non lavora quindi su dati che riceve da fuori e poi dimentica: lavora sullo stato dell'oggetto a cui appartiene, e le sue modifiche restano. Dopo `accelera(20)`, la proprietà `velocita` di `$auto` vale 20; chiamandolo di nuovo diventa 40. È questo legame permanente tra il comportamento e i dati su cui opera che distingue l'oggetto da una semplice funzione con dei parametri.

## Visibilità

Finora tutto è stato `public`, cioè accessibile da chiunque. Ma il vero motivo per cui si usano gli oggetti è poter **nascondere** parte dello stato e controllarne l'accesso. Le parole chiave che regolano la visibilità sono tre:

- `public`: accessibile da fuori;
- `protected`: accessibile nella classe e nelle classi figlie;
- `private`: accessibile solo nella classe.

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

Codice completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-25/it/parte-07/cap-25/listing-05.php)


Questo esempio è il cuore del capitolo, perché mostra a cosa serve davvero l'incapsulamento. Il saldo è `private`: dall'esterno **non puoi** scrivere `$conto->saldo = -1000000`, perché quella proprietà è invisibile fuori dalla classe. L'unico modo per far crescere il saldo è passare da `deposita()`, che controlla l'importo e rifiuta i valori non positivi. Il risultato è una **garanzia**: qualunque codice usi questa classe, il saldo non potrà mai essere modificato con un valore assurdo, perché la regola che lo protegge vive *dentro* l'oggetto, insieme al dato. Questa è la vera promessa della programmazione a oggetti — non "raggruppare le funzioni", ma tenere insieme un dato e le regole che ne garantiscono la coerenza, così che lo stato non possa finire in configurazioni invalide. Le condizioni che devono restare sempre vere (il saldo non è negativo, l'email è valida, l'età è positiva) si chiamano **invarianti**, e `private` è lo strumento che ti permette di difenderle.

## Costruttore

Il **costruttore** è un metodo speciale, `__construct`, che PHP chiama automaticamente nel momento esatto in cui crei l'oggetto con `new`.

```php
<?php
class Utente
{
    private string $email;

    public function __construct(string $email)
    {
        $this->email = $email;
    }
}

$utente = new Utente("mario@example.com");
```

Codice completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-25/it/parte-07/cap-25/listing-06.php)


Il valore del costruttore è che rende impossibile creare un oggetto **incompleto**. Qui non puoi ottenere un `Utente` senza email: la firma `__construct(string $email)` obbliga chi scrive `new Utente(...)` a fornirla subito. È una differenza sottile ma decisiva rispetto ad assegnare le proprietà una a una dopo la creazione, dove nulla ti impedisce di dimenticare un pezzo e ritrovarti con un oggetto a metà. Il costruttore è quindi il posto giusto per due cose: i **dati obbligatori** senza cui l'oggetto non ha senso, e le **dipendenze**, cioè gli altri oggetti di cui questo ha bisogno per lavorare (una connessione al database, un logger). Chiedere le dipendenze nel costruttore è il primo passo verso la *dependency injection* che sarà il fulcro dell'architettura della Parte IX: un oggetto dichiara di cosa ha bisogno, e lo riceve dall'esterno alla nascita.

## Constructor property promotion

Il pattern del paragrafo precedente — dichiarare la proprietà, riceverla come parametro, assegnarla con `$this->` — si ripete così spesso che PHP 8 ha introdotto una scorciatoia:

```php
<?php
class Utente
{
    public function __construct(
        private string $email,
        private string $name
    ) {
    }
}
```

Codice completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-25/it/parte-07/cap-25/listing-07.php)


Mettendo un modificatore di visibilità (`private`, `public`, `protected`) davanti a un parametro del costruttore, dici a PHP di fare tre cose in un colpo solo: dichiarare la proprietà, riceverne il valore come argomento e assegnarlo. Questo codice è esattamente equivalente alla versione lunga di prima, ma senza la tripla ripetizione del nome di ogni proprietà. Non è solo questione di battere meno tasti: meno codice ripetitivo significa meno posti in cui un refactoring può dimenticare qualcosa, e la firma del costruttore diventa un elenco leggibile di tutto ciò che l'oggetto richiede. Vedrai questa forma ovunque nel codice PHP moderno, e la userai molto nella Parte IX.

## Setter e getter

A volte serve comunque leggere o modificare una proprietà dall'esterno, ma volendo mantenere il controllo su *come*. Entrano in gioco i **getter** (leggono) e i **setter** (modificano):

```php
<?php
class Utente
{
    private string $email;

    public function setEmail(string $email): void
    {
        if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
            throw new InvalidArgumentException("Email non valida");
        }

        $this->email = $email;
    }

    public function getEmail(): string
    {
        return $this->email;
    }
}
```

Codice completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-25/it/parte-07/cap-25/listing-08.php)


Qui il setter non si limita a copiare il valore: lo **valida**, e lancia un'eccezione se l'email è malformata (le eccezioni sono il tema del Capitolo 30). Ecco perché tenere `email` privata e passare da `setEmail` conviene rispetto a lasciarla pubblica: hai un unico punto di controllo, e nessuno può infilare un'email invalida nell'oggetto. Ma attenzione a un errore diffusissimo: **non** generare automaticamente getter e setter per ogni proprietà. Un setter pubblico che si limita a `$this->x = $x`, senza alcuna validazione, non protegge niente — è una proprietà pubblica con due righe di cerimonia in più, e tradisce il senso stesso dell'incapsulamento. I getter e i setter si aggiungono quando servono davvero: per validare, per calcolare un valore al volo, o per conservare un'interfaccia stabile mentre cambia l'implementazione interna. Se una proprietà non ha bisogno di protezione, o la rendi pubblica, o — meglio ancora — la passi nel costruttore e la lasci in sola lettura, come vedremo tra poco.

## Typed property

Le **typed property** — le proprietà con un tipo dichiarato — sono una rete di sicurezza:

```php
<?php
class Post
{
    public int $id;
    public string $title;
}
```

Codice completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-25/it/parte-07/cap-25/listing-09.php)


Dichiarare `public int $id` significa dire a PHP che quella proprietà conterrà sempre un intero. Se provi ad assegnarle una stringa non convertibile a numero, PHP solleva un `TypeError` sul posto, invece di lasciar entrare un valore sbagliato che esploderà chissà dove più tardi. C'è di più: una typed property senza valore iniziale parte in stato **non inizializzato**, e leggerla prima di averle assegnato qualcosa provoca un errore esplicito, non un silenzioso `null`. È esattamente il comportamento che vuoi: meglio un errore chiaro al primo accesso sbagliato che un `null` inatteso che si propaga per mezza applicazione prima di causare un crash lontano dalla vera causa. I tipi trasformano una classe di bug da "misteri da debuggare a runtime" in "errori segnalati subito".

## Readonly

Da PHP 8.1 puoi dichiarare una proprietà `readonly`, cioè assegnabile una sola volta:

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

Codice completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-25/it/parte-07/cap-25/listing-10.php)


Una proprietà `readonly` si può scrivere una volta sola — di norma nel costruttore — e dopo diventa immodificabile: qualunque tentativo di riassegnarla provoca un errore. Perché volerlo? Perché l'**immutabilità** elimina un'intera categoria di problemi. Un `UserId` creato con valore 42 sarà 42 per tutta la sua vita: puoi passarlo tra funzioni, condividerlo, tenerlo in una struttura dati senza il timore che qualcuno, da qualche parte, lo cambi sotto i tuoi piedi. È lo strumento ideale per gli **oggetti valore** — piccoli oggetti che rappresentano un concetto (un identificatore, un importo, un indirizzo email) e la cui identità coincide col loro valore — e per i **DTO**, gli oggetti che trasportano dati da un livello all'altro dell'applicazione senza logica propria. Combinata con la constructor property promotion, `readonly` rende la definizione di un oggetto immutabile una faccenda di poche righe.

## In sintesi

Classi e oggetti servono a modellare il dominio della tua applicazione mettendo insieme, in un'unica unità, i dati e le regole che li governano: le **proprietà** tengono lo stato, i **metodi** definiscono il comportamento, la **visibilità** protegge gli invarianti, il **costruttore** garantisce che un oggetto nasca già valido. Attorno a queste basi, PHP moderno mette a disposizione strumenti che rendono il codice più espressivo e meno verboso — constructor property promotion, typed property, `readonly` — e che userai costantemente da qui in avanti. Tieni a mente l'idea centrale, quella che distingue davvero l'OOP dalla programmazione procedurale: non si tratta di raccogliere funzioni attorno a dei dati, ma di rendere impossibile, per costruzione, che quei dati finiscano in uno stato incoerente. È la garanzia che porterai con te nei capitoli sull'ereditarietà, sui trait e, soprattutto, nel progetto enterprise della Parte IX.
