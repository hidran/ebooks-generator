# Lezione 10. Incapsulamento e costruttori

## Punti chiave

### Il problema dei campi pubblici

- Chiunque può scrivere qualsiasi valore
- book.priceInCents = -500; compila ed esegue
- Un oggetto può nascere a metà
- Il controllo non ha un posto dove stare

### Incapsulamento

- Campi private: visibili solo dentro la classe
- Il costruttore controlla i dati alla nascita
- Getter per leggere, nessun setter inutile

> Percorso: new Product(...), poi controllo, poi oggetto valido.

### Immutabile quando si può

- final: il campo si assegna una volta sola
- Nessun setter: l'oggetto non cambia dopo la nascita
- Un prezzo diverso? Un nuovo oggetto
- Più facile da capire e da condividere

## Codice della lezione

`Product.java`

~~~java
public class Product {
    private final String name;
    private final int priceInCents;
    public Product(String name, int priceInCents) {
        if (priceInCents < 0) {
            throw new IllegalArgumentException("Price cannot be negative");
        }
        this.name = name;
        this.priceInCents = priceInCents;
    }
    public String getName() {
        return name;
    }
    public int getPriceInCents() {
        return priceInCents;
    }
}
~~~

`Main.java`

~~~java
public class Main {
    public static void main(String[] args) {
        Product book = new Product("Book", 1500);
        Product onSale = new Product("Book", book.getPriceInCents() - 300);
        System.out.println(book.getName() + ": " + book.getPriceInCents());
        System.out.println("On sale: " + onSale.getPriceInCents());
        Product broken = new Product("Broken", -500);
        System.out.println("Never printed: " + broken.getName());
    }
}
~~~

`before/Product.java`

~~~java
public class Product {
    public String name;
    public int priceInCents;
}
~~~

`before/Main.java`

~~~java
public class Main {
    public static void main(String[] args) {
        Product book = new Product();
        book.name = "Book";
        book.priceInCents = 1500;
        System.out.println(book.name + ": " + book.priceInCents);
        book.priceInCents = -500;
        System.out.println(book.name + ": " + book.priceInCents);
    }
}
~~~

## Esercizio 10: un prodotto sempre valido

Obiettivo: Validare nel costruttore e proteggere campi immutabili.

La validazione con `IllegalArgumentException` è *già fornita*. **Non devi scrivere né modificare** le istruzioni `throw`: le eccezioni saranno spiegate nella lezione 16.

**Completa soltanto i TODO** indicati nei commenti.

**Completa il costruttore `Exercise(name, priceInCents)`**.

1. **Rifiuta** un nome `null` o vuoto dopo `trim` e un prezzo minore di `1` con `IllegalArgumentException`.
2. **Salva** il nome *senza spazi esterni* e il prezzo nei campi `private final` già presenti.

I getter sono pronti.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
public class Exercise {

    private final String name;
    private final int priceInCents;

    public Exercise(String name, int priceInCents) {
        // Controllo già fornito: interrompe la creazione o il calcolo se i dati non sono validi.
        // Lascia questo controllo com’è; studieremo le eccezioni nella lezione 16.
        if (name == null || name.trim().isEmpty() || priceInCents < 1) {
            throw new IllegalArgumentException("Invalid product");
        }
        // TODO: completa questo blocco.
        // Suggerimento: La validazione è già pronta: qui ci concentriamo sui campi dell’oggetto.
        // this.name indica il campo; name indica il parametro del costruttore.
        // Sostituisci entrambi i valori provvisori: salva il nome con trim() e il prezzo ricevuto.
        this.name = "";
        this.priceInCents = 0;
    }

    public String getName() {
        return name;
    }

    public int getPriceInCents() {
        return priceInCents;
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
public class Exercise {

    private final String name;
    private final int priceInCents;

    public Exercise(String name, int priceInCents) {
        if (name == null || name.trim().isEmpty() || priceInCents < 1) {
            throw new IllegalArgumentException("Invalid product");
        }
        this.name = name.trim();
        this.priceInCents = priceInCents;
    }

    public String getName() {
        return name;
    }

    public int getPriceInCents() {
        return priceInCents;
    }
}
~~~

L'obiettivo è completare un costruttore che salva nei campi solo dati già controllati, così ogni prodotto nasce valido.

Il controllo iniziale è già fornito: se il nome è `null`, vuoto dopo `trim` o il prezzo è minore di 1, la creazione si interrompe con un'eccezione. Le eccezioni le studieremo nella lezione 16; per ora ti basta sapere che, se il controllo scatta, le righe successive non vengono mai eseguite.

Dopo il controllo scriviamo `this.name = name.trim()` e `this.priceInCents = priceInCents`. Il parametro e il campo hanno lo stesso nome, quindi `this.` indica il campo dell'oggetto, mentre il nome da solo indica il parametro. Salviamo il nome già ripulito: chi chiama `getName()` riceve `Book` e non `" Book "`. Come abbiamo visto nella lezione 10, i campi sono `private final`: nessuno da fuori può cambiarli e vanno assegnati una sola volta, nel costruttore.

Proprio `final` genera l'errore più frequente. Se aggiungi le tue righe e lasci anche quelle provvisorie `this.name = ""` e `this.priceInCents = 0`, il compilatore si ferma, perché un campo `final` verrebbe assegnato due volte. Le righe provvisorie vanno sostituite, non affiancate. Un altro errore è salvare `name` senza `trim()`: il codice compila, ma il test `storesValidValues` crea il prodotto con `" Book "` e si aspetta `"Book"` da `getName()`.

I test `rejectsInvalidNames` e `rejectsNonPositivePrices` verificano il controllo già pronto, con `null`, `"  "`, 0 e -1. Passano finché non lo modifichi.

## Riepilogo

- private protegge i campi
- Il costruttore garantisce uno stato valido
- Getter sì, setter solo se servono davvero
