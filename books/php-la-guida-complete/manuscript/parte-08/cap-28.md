# 28. Namespace e autoload

Finché un progetto ha dieci classi, tenerle tutte in una cartella e includerle a mano con `require` funziona. Ma appena cresce — decine di classi, più librerie di terze parti — quel modello si sgretola, e per due motivi distinti. Il primo è di **nomi**: due classi diverse non possono chiamarsi entrambe `User`, eppure capita di continuo. Il secondo è di **caricamento**: elencare a mano un `require` per ogni classe diventa ingestibile. I namespace risolvono il primo problema, l'autoload il secondo. Sono due strumenti indipendenti che nel codice moderno lavorano sempre insieme, ed è utile vederli prima separatamente e poi capire come si incastrano.

## Il problema dei nomi

Immagina di usare due librerie, e che ognuna definisca una classe `User`. Senza namespace vivono nello stesso "spazio globale" dei nomi, e la seconda a essere caricata provoca un errore: il nome è già occupato. I namespace danno a ogni classe un **nome completo** che ne evita la collisione, come una cartella logica:

```php
<?php
namespace App\Models;

class User
{
}
```

Codice completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-28/it/parte-08/cap-28/listing-01.php)


La riga `namespace App\Models` dichiara che tutto ciò che segue vive in quello spazio: la classe non si chiama più solo `User`, ma per intero `App\Models\User`. Un'altra libreria potrà avere la sua `Vendor\Auth\User`, e le due non si confonderanno mai, perché il nome completo è diverso. È lo stesso principio dei percorsi in un filesystem: due file `index.php` convivono senza problemi finché stanno in cartelle diverse.

## Usare una classe con namespace

Scrivere ogni volta il nome completo sarebbe scomodo. La parola chiave `use` **importa** un nome nel file corrente, così poi puoi usare la forma breve:

```php
<?php
use App\Models\User;

$user = new User();
```

Codice completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-28/it/parte-08/cap-28/listing-02.php)


L'`use` in cima al file dice "quando scrivo `User`, intendo `App\Models\User`". È la forma che vedrai più spesso: gli import raccolti in testa al file dichiarano subito da dove arriva ogni classe. In alternativa, senza `use`, puoi scrivere il nome completo direttamente:

```php
<?php
$user = new \App\Models\User();
```

Codice completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-28/it/parte-08/cap-28/listing-03.php)


Nota il backslash iniziale: indica lo **spazio dei nomi globale**, la radice. È l'equivalente di un percorso assoluto che parte da `/`: dice a PHP di cercare il nome partendo dalla cima, senza tener conto del namespace in cui ti trovi in quel momento.

## Più namespace nello stesso file

PHP permette tecnicamente di dichiarare più namespace in un unico file, ma in codice reale è meglio evitarlo. La convenzione universale è **una classe per file**, con il namespace all'inizio:

```php
<?php
namespace App\Models;

class User
{
}
```

Codice completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-28/it/parte-08/cap-28/listing-04.php)


E il file va salvato in un percorso che **rispecchia** il namespace:

```text
src/Models/User.php
```

Codice completo: [listing-05.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-28/it/parte-08/cap-28/listing-05.txt)


Questa corrispondenza tra nome e percorso non è pignoleria: è la chiave che rende possibile l'autoload. Se `App\Models\User` sta sempre in `src/Models/User.php`, una macchina può calcolare il percorso a partire dal nome, senza che tu debba dirglielo. Ecco perché "una classe per file" e "il percorso rispecchia il namespace" sono le due regole d'oro da qui in avanti.

## `require` manuale

Prima di arrivare all'autoload, vediamo il metodo diretto, quello che vuoi superare:

```php
<?php
require __DIR__ . "/src/Models/User.php";
require __DIR__ . "/src/Controllers/UserController.php";
```

Codice completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-28/it/parte-08/cap-28/listing-06.php)


Funziona, ma non scala: ogni nuova classe richiede una nuova riga di `require`, e in un progetto serio sono centinaia. Peggio ancora è l'**ordine**: se `UserController` usa `User` ma il suo `require` viene prima, l'applicazione fallisce perché la dipendenza non è ancora caricata. Ti ritrovi a gestire a mano un grafo di dipendenze che cresce a ogni classe — esattamente il genere di lavoro noioso e fragile che una macchina dovrebbe fare al posto tuo.

## `spl_autoload_register()`

L'idea dell'autoload è ribaltare la logica: invece di caricare tutto in anticipo, registri una funzione che PHP chiama **solo quando serve**, nel momento esatto in cui incontra una classe non ancora caricata.

```php
<?php
spl_autoload_register(function (string $class): void {
    $prefix = "App\\";
    $baseDir = __DIR__ . "/src/";

    if (!str_starts_with($class, $prefix)) {
        return;
    }

    $relativeClass = substr($class, strlen($prefix));
    $file = $baseDir . str_replace("\\", "/", $relativeClass) . ".php";

    if (is_file($file)) {
        require $file;
    }
});
```

Codice completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-28/it/parte-08/cap-28/listing-07.php)


Segui la logica della funzione, perché è tutta la storia dell'autoload in poche righe. Quando scrivi `new App\Models\User()` e quella classe non è caricata, PHP passa la stringa `"App\Models\User"` a questa funzione. Lei controlla che il nome inizi col prefisso `App\` (altrimenti non è affar suo e ritorna), toglie il prefisso, sostituisce i backslash con gli slash — trasformando il namespace in un percorso — e aggiunge `.php`. Il risultato: `App\Models\User` diventa `src/Models/User.php`, che viene incluso. Le classi si caricano così **su richiesta**, una alla volta, solo quelle davvero usate. E il problema dell'ordine sparisce: non c'è più un ordine da rispettare, ogni classe arriva nel momento in cui la nomini. Questa convenzione nome-percorso è esattamente la base dello standard **PSR-4** che Composer implementa (Capitolo 29).

## Autoload e percorsi

Un errore frequentissimo negli autoloader scritti a mano è costruire i percorsi rispetto alla cartella da cui si lancia lo script, invece che rispetto al file dell'autoloader. La soluzione è `__DIR__`:

```php
<?php
$baseDir = __DIR__ . "/src/";
```

Codice completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-28/it/parte-08/cap-28/listing-08.php)


`__DIR__` è la costante magica che contiene la cartella del file **in cui è scritta**, non quella corrente di esecuzione. Ancorando i percorsi a `__DIR__`, l'autoloader funziona identico che tu lanci lo script dalla radice del progetto, da una sottocartella o da un cron: non dipende più da *dove* viene eseguito. È una piccola disciplina che evita una delle cause più comuni e frustranti di "file non trovato".

## Namespace e funzioni

Un'ultima insidia riguarda la risoluzione dei nomi. Quando sei dentro un namespace, un nome senza backslash viene cercato **prima** nel namespace corrente. Va benissimo per le tue classi, ma le classi native di PHP (`DateTimeImmutable`, `InvalidArgumentException`) vivono nello spazio globale: dentro `App\Models`, scrivere `new DateTimeImmutable()` fa cercare a PHP un inesistente `App\Models\DateTimeImmutable`. Le soluzioni sono due. La prima è importarle in testa al file:

```php
<?php
use DateTimeImmutable;
use InvalidArgumentException;
```

Codice completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-28/it/parte-08/cap-28/listing-09.php)


La seconda è prefissarle col backslash che le àncora alla radice globale:

```php
<?php
$date = new \DateTimeImmutable();
```

Codice completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-28/it/parte-08/cap-28/listing-10.php)


Entrambe funzionano; la prima è più leggibile perché raccoglie in cima al file tutte le dipendenze, incluse quelle di sistema. Il messaggio di fondo è che, dentro un namespace, i nomi globali vanno resi espliciti — un dettaglio che spiega parecchi errori "classe non trovata" apparentemente misteriosi.

## In sintesi

I namespace danno alle classi **nomi completi e ordinati**, eliminando le collisioni tra librerie diverse; l'autoload elimina i `require` manuali collegando automaticamente il nome della classe al percorso del suo file, purché tu rispetti le due convenzioni — una classe per file, percorso che rispecchia il namespace. Nei progetti moderni non scriverai quasi mai un autoloader a mano: lo genera Composer, che vediamo nel prossimo capitolo. Ma aver capito il meccanismo qui, in una funzione di poche righe, ti mette nelle condizioni di risolvere gli errori di "classe non trovata" invece di subirli — perché sai esattamente da quale nome PHP ha calcolato quale percorso, e dove è andato a cercare.
