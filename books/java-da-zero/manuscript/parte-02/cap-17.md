# Lezione 10b. Membri statici

## Punti chiave

### Di istanza o di classe

- Membro di istanza: una copia per ogni oggetto, come name
- Membro static: una sola copia, della classe
- Si usa con il nome della classe: Product.getCreatedCount()

> Percorso: Classe Product (createdCount), poi Oggetti book e mug (name, priceInCents).

### Costanti e classi di utilità

- static final: un valore unico che non cambia
- Nome in maiuscolo: MAX_PRICE_IN_CENTS
- Classe di utilità: solo metodi static, costruttore private
- Un metodo static non vede i campi di istanza: niente this

### Perché main è static

- All'avvio non esiste ancora nessun oggetto
- La JVM chiama main con il nome della classe, senza new
- Da Java 25 anche void main() senza static: l'oggetto lo crea Java
- La forma classica resta public static void main

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

`count/Product.java`

~~~java
public class Product {
    private static int createdCount = 0;
    private final String name;
    private final int priceInCents;
    public Product(String name, int priceInCents) {
        if (priceInCents < 0) {
            throw new IllegalArgumentException("Price cannot be negative");
        }
        this.name = name;
        this.priceInCents = priceInCents;
        createdCount++;
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

`count/Main.java`

~~~java
public class Main {
    public static void main(String[] args) {
        System.out.println("Products: " + Product.getCreatedCount());
        Product book = new Product("Book", 1500);
        Product mug = new Product("Mug", 850);
        System.out.println(book.getName() + " and " + mug.getName());
        System.out.println("Products: " + Product.getCreatedCount());
    }
}
~~~

`Main.java`

~~~java
public class Main {
    public static void main(String[] args) {
        System.out.println("Products: " + Product.getCreatedCount());
        Product book = new Product("Book", 1500);
        Product mug = new Product("Mug", 850);
        System.out.println(book.getName() + " and " + mug.getName());
        System.out.println("Products: " + Product.getCreatedCount());
        System.out.println("Book: " + PriceFormatter.format(book.getPriceInCents()));
        System.out.println("Mug: " + PriceFormatter.format(mug.getPriceInCents()));
        System.out.println("Max: " + PriceFormatter.format(Product.MAX_PRICE_IN_CENTS));
    }
}
~~~

`count/Main.java`, versione con un errore voluto: non compila o il test fallisce, per leggere il messaggio

~~~java
public class Main {
    public static void main(String[] args) {
        System.out.println("Products: " + Product.getCreatedCount());
        Product book = new Product("Book", 1500);
        Product mug = new Product("Mug", 850);
        System.out.println(book.getName() + " and " + mug.getName());
        System.out.println("Products: " + Product.getCreatedCount());
        System.out.println(Product.getName());
    }
}
~~~

`PriceFormatter.java`

~~~java
public class PriceFormatter {
    private PriceFormatter() {
    }
    public static String format(int cents) {
        int euros = cents / 100;
        int rest = cents % 100;
        if (rest < 10) {
            return euros + ",0" + rest + " euro";
        }
        return euros + "," + rest + " euro";
    }
}
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `start/Product.java`: lezione 10, file `Product.java`

## Esercizio 10b: contatore condiviso e costanti

Obiettivo: Distinguere stato di istanza e stato condiviso della classe.

La validazione con `IllegalArgumentException` è *già fornita*. **Non devi scrivere né modificare** le istruzioni `throw`: le eccezioni saranno spiegate nella lezione 16.

**Completa soltanto i TODO** indicati nei commenti.

La classe contiene `createdCount` *statico* e `MAX_PRICE_IN_CENTS = 100000`.

**Completa il costruttore**:

1. accetta prezzi da `1` alla costante inclusa,
2. salva il prezzo,
3. incrementa `createdCount` **solo per oggetti validi**.

**`getCreatedCount`** deve restituire il numero di oggetti validi creati.

**Non azzerare mai** il contatore nel costruttore.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
public class Exercise {

    public static final int MAX_PRICE_IN_CENTS = 100000;
    private static int createdCount;
    private final int priceInCents;

    public Exercise(int priceInCents) {
        // Controllo già fornito: interrompe la creazione o il calcolo se i dati non sono validi.
        // Lascia questo controllo com’è; studieremo le eccezioni nella lezione 16.
        if (priceInCents < 1 || priceInCents > MAX_PRICE_IN_CENTS) {
            throw new IllegalArgumentException("Invalid price");
        }
        // TODO: completa questo blocco.
        // Suggerimento: La validazione è già pronta. this.priceInCents è il campo del singolo oggetto.
        // Sostituisci il prezzo provvisorio e incrementa createdCount dopo aver salvato il prezzo.
        // createdCount è static: tutti gli oggetti condividono lo stesso contatore.
        this.priceInCents = 0;
    }

    public int getPriceInCents() {
        return priceInCents;
    }

    public static int getCreatedCount() {
        // TODO: completa questo blocco.
        // Suggerimento: Restituisci il campo statico senza modificarlo.
        return 0;
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
public class Exercise {

    public static final int MAX_PRICE_IN_CENTS = 100000;
    private static int createdCount;
    private final int priceInCents;

    public Exercise(int priceInCents) {
        if (priceInCents < 1 || priceInCents > MAX_PRICE_IN_CENTS) {
            throw new IllegalArgumentException("Invalid price");
        }
        this.priceInCents = priceInCents;
        createdCount++;
    }

    public int getPriceInCents() {
        return priceInCents;
    }

    public static int getCreatedCount() {
        return createdCount;
    }
}
~~~

L'obiettivo è contare gli oggetti validi creati, con un contatore che appartiene alla classe e non al singolo oggetto.

Nel costruttore il controllo del prezzo è già fornito: accetta valori da 1 fino a `MAX_PRICE_IN_CENTS` incluso. Dopo il controllo scriviamo `this.priceInCents = priceInCents`, che salva il prezzo nel campo di questo oggetto, e poi `createdCount++`. L'incremento sta dopo il controllo, quindi un prezzo non valido interrompe la creazione prima di arrivarci: il contatore cresce solo per oggetti nati davvero. In `getCreatedCount` restituiamo semplicemente `createdCount`.

Come abbiamo visto nella lezione 10b, `createdCount` è `static`: ne esiste una sola copia, condivisa da tutti gli oggetti. Ogni `new Exercise(...)` incrementa lo stesso numero. Per questo anche `getCreatedCount` è `static` e si chiama sulla classe, `Exercise.getCreatedCount()`. `MAX_PRICE_IN_CENTS` è `static final`: una costante unica, scritta in maiuscolo.

Un errore tipico è azzerare il contatore nel costruttore con `createdCount = 0` prima dell'incremento. Ogni nuovo oggetto ripartirebbe da zero e il contatore varrebbe sempre 1. Il test `sharesCounterAcrossInstances` legge il valore prima, crea due oggetti e si aspetta esattamente due in più. Un altro errore è restituire `createdCount++` dal getter: leggere il contatore lo cambierebbe, e lo stesso test troverebbe un oggetto di troppo. Il test `countsOnlySuccessfulConstruction` prova 0 e 100001 e controlla che il contatore non si muova.

Il test `acceptsMaximum` verifica il confine: 100000 è un prezzo valido.

## Riepilogo

- static: appartiene alla classe, una copia condivisa
- static final per le costanti, metodi static per le utilità
- Membri static con il nome della classe, non con un oggetto
