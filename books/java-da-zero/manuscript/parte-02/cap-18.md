# Lezione 10c. Overloading di metodi e costruttori

## Punti chiave

### Stesso nome, parametri diversi

- println(String), println(int), println(boolean): un nome, tante versioni
- Il compilatore sceglie in base a numero e tipo degli argomenti
- Il tipo restituito non basta a distinguere due metodi

> Percorso: chiamata, poi numero e tipo degli argomenti, poi versione scelta.

### Costruttori concatenati

- Più costruttori, purché con parametri diversi
- this(...) chiama un altro costruttore della stessa classe
- Deve essere la prima istruzione
- Controlli in un solo costruttore, gli altri delegano: DRY

### Overloading e overriding

- Overloading: stesso nome, parametri diversi, sceglie il compilatore
- Overriding: stessa firma in una sottoclasse, sceglie l'esecuzione
- L'overriding lo vedremo con l'ereditarietà, nella lezione 12

## Codice della lezione

`Product.java`

~~~java
public class Product {
    public static final int MAX_PRICE_IN_CENTS = 100000;
    private static int createdCount = 0;
    private final String name;
    private final int priceInCents;
    public Product(String name, int priceInCents) {
        if (priceInCents < 0 || priceInCents > MAX_PRICE_IN_CENTS) {
            throw new IllegalArgumentException("Price out of range");
        }
        this.name = name;
        this.priceInCents = priceInCents;
        createdCount++;
    }
    public Product(String name) {
        this(name, 0);
    }
    public String getName() {
        return name;
    }
    public int getPriceInCents() {
        return priceInCents;
    }
    public static int getCreatedCount() {
        return createdCount;
    }
}
~~~

`Order.java`, versione con un errore voluto: non compila o il test fallisce, per leggere il messaggio

~~~java
public class Order {
    private int itemCount;
    private int totalInCents;
    public void add(Product product, int quantity) {
        if (quantity <= 0) {
            throw new IllegalArgumentException("Quantity must be positive");
        }
        itemCount += quantity;
        totalInCents += product.getPriceInCents() * quantity;
    }
    public void add(Product product) {
        add(product, 1);
    }
    public int add(Product product) {
        return totalInCents;
    }
    public int getItemCount() {
        return itemCount;
    }
    public int getTotalInCents() {
        return totalInCents;
    }
}
~~~

`Order.java`

~~~java
public class Order {
    private int itemCount;
    private int totalInCents;
    public void add(Product product, int quantity) {
        if (quantity <= 0) {
            throw new IllegalArgumentException("Quantity must be positive");
        }
        itemCount += quantity;
        totalInCents += product.getPriceInCents() * quantity;
    }
    public void add(Product product) {
        add(product, 1);
    }
    public int getItemCount() {
        return itemCount;
    }
    public int getTotalInCents() {
        return totalInCents;
    }
}
~~~

`Main.java`

~~~java
public class Main {
    public static void main(String[] args) {
        Product book = new Product("Book", 1500);
        Product sticker = new Product("Sticker");
        System.out.println(sticker.getName() + ": " + sticker.getPriceInCents());
        Order order = new Order();
        order.add(book);
        order.add(sticker);
        order.add(new Product("Pen", 200), 3);
        System.out.println("Items: " + order.getItemCount());
        System.out.println("Total: " + order.getTotalInCents());
        System.out.println("Products created: " + Product.getCreatedCount());
    }
}
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `start/Product.java`: lezione 10b, file `Product.java`

## Esercizio 10c: overloading senza duplicazione

Obiettivo: Offrire più costruttori e metodi mantenendo una sola regola di calcolo.

La validazione con `IllegalArgumentException` è *già fornita*. **Non devi scrivere né modificare** le istruzioni `throw`: le eccezioni saranno spiegate nella lezione 16.

**Completa soltanto i TODO** indicati nei commenti.

`Exercise` rappresenta un prodotto con nome e prezzo.

1. Il **costruttore a un argomento** deve *delegare* a quello a due argomenti usando il nome `"Product"`.
2. **`total()`** deve delegare a `total(1)`.
3. **`total(quantity)`** moltiplica il prezzo per la quantità e rifiuta quantità minori di `1` con `IllegalArgumentException`.

**Non cambiare** il costruttore completo già fornito.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
public class Exercise {

    private final String name;
    private final int priceInCents;

    public Exercise(String name, int priceInCents) {
        // Controllo già fornito: lascia questo blocco com’è.
        // Le eccezioni saranno spiegate nella lezione 16.
        if (priceInCents < 1) {
            throw new IllegalArgumentException();
        }
        this.name = name;
        this.priceInCents = priceInCents;
    }

    public Exercise(int priceInCents) {
        // TODO: completa questo blocco.
        // Suggerimento: this(...) chiama un altro costruttore della stessa classe e va come prima istruzione.
        // Sostituisci soltanto il nome provvisorio con quello richiesto.
        this("TODO", priceInCents);
    }

    public String getName() {
        return name;
    }

    public int total() {
        // TODO: completa questo blocco.
        // Suggerimento: Richiama l’altra versione di total passando la quantità di un solo prodotto.
        return 0;
    }

    public int total(int quantity) {
        // Controllo già fornito: lascia questo blocco com’è.
        // Le eccezioni saranno spiegate nella lezione 16.
        if (quantity < 1) {
            throw new IllegalArgumentException("Invalid quantity");
        }
        // TODO: completa questo blocco.
        // Suggerimento: Il controllo della quantità è già pronto.
        // Usa il campo priceInCents e il parametro quantity per calcolare il risultato.
        return 0;
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
        if (priceInCents < 1) {
            throw new IllegalArgumentException();
        }
        this.name = name;
        this.priceInCents = priceInCents;
    }

    public Exercise(int priceInCents) {
        this("Product", priceInCents);
    }

    public String getName() {
        return name;
    }

    public int total() {
        return total(1);
    }

    public int total(int quantity) {
        if (quantity < 1) {
            throw new IllegalArgumentException("Invalid quantity");
        }
        return priceInCents * quantity;
    }
}
~~~

L'obiettivo è offrire versioni più semplici di un costruttore e di un metodo, senza duplicare la regola che sta nella versione completa.

Nel costruttore a un argomento scriviamo `this("Product", priceInCents)`. Come abbiamo visto nella lezione 10c, `this(...)` chiama un altro costruttore della stessa classe e deve essere la prima istruzione. Passiamo il nome predefinito e il prezzo ricevuto: il costruttore completo controlla il prezzo e assegna i campi. Il controllo vive in un posto solo, e anche `new Exercise(0)` viene rifiutato senza che tu scriva nulla.

`total()` senza parametri restituisce `total(1)`. Il compilatore sceglie la versione giusta in base agli argomenti: nessun argomento, la prima; un `int`, la seconda. La versione semplice delega a quella completa, come i costruttori.

In `total(int quantity)` il controllo della quantità è già fornito, e dopo restituiamo `priceInCents * quantity`, usando il campo dell'oggetto e il parametro. Le eccezioni le studieremo nella lezione 16.

Un errore tipico è dimenticare di sostituire `"TODO"` nel costruttore: il codice compila, ma il test `providesDefaultNameAndQuantity` si aspetta `"Product"` da `getName()`. Un altro è far restituire a `total()` direttamente `priceInCents`. Il test darebbe ragione, perché 250 per 1 fa 250, ma la regola del calcolo sarebbe scritta due volte: se un giorno `total(quantity)` applicasse uno sconto, `total()` resterebbe indietro. Il test `rejectsInvalidQuantityAndPrice` controlla invece che `total(0)` sia rifiutato.

Funzionerebbe anche ripetere il controllo del prezzo nel costruttore corto, ma è proprio la duplicazione che `this(...)` evita.

## Riepilogo

- Stesso nome, parametri diversi: sceglie il compilatore
- Il tipo restituito non fa parte della firma
- this(...) concatena i costruttori, la versione semplice delega
