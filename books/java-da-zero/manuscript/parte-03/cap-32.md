# Lezione 22. Optional e assenza di valore

## Punti chiave

### Il problema di null

- null vuol dire "nessun oggetto", ma il tipo non lo dice
- La firma Product findByName(...) non avvisa che può mancare
- Metodo chiamato su null: NullPointerException
- Tony Hoare: "il mio errore da un miliardo di dollari"

### Optional: una scatola piena o vuota

- Optional&lt;Product&gt;: la firma dice che il valore può mancare
- Optional.of(valore): piena, null vietato
- Optional.ofNullable(valore): piena o vuota
- Optional.empty(): vuota

### Niente get() senza controllo

- get() su un Optional vuoto: NoSuchElementException
- Meglio ifPresent, orElse, orElseGet, orElseThrow
- orElse calcola sempre il valore di riserva
- orElseGet lo calcola solo se serve

### Dove usare Optional

- Sì: tipo di ritorno di un metodo che può non trovare
- No: campi e parametri
- No: collezioni, si restituisce una lista vuota
- Un Optional non vale mai null

## Codice della lezione

`Catalog.java`

~~~java
import java.util.List;
import java.util.Optional;
public class Catalog {
    private final List<Product> products;
    public Catalog(List<Product> products) {
        this.products = List.copyOf(products);
    }
    public Optional<Product> findByName(String name) {
        for (Product product : products) {
            if (product.name().equals(name)) {
                return Optional.of(product);
            }
        }
        return Optional.empty();
    }
}
~~~

`Main.java`

~~~java
import java.util.List;
import java.util.Map;
import java.util.Optional;
public class Main {
    public static void main(String[] args) {
        Catalog catalog = new Catalog(List.of(
                new Product("Coffee", 250),
                new Product("Book", 1500)));
        Optional<Product> coffee = catalog.findByName("Coffee");
        Optional<Product> pizza = catalog.findByName("Pizza");
        coffee.ifPresent(p -> System.out.println("Found " + p.name()));
        System.out.println("Pizza missing: " + pizza.isEmpty());
        int price = pizza.map(Product::priceInCents).orElse(0);
        System.out.println("Pizza price: " + price);
        Product drink = pizza.orElseGet(() -> new Product("Water", 100));
        System.out.println("Suggested: " + drink.name());
        Product book = catalog.findByName("Book").orElseThrow();
        System.out.println("Book costs " + book.priceInCents());
        Map<String, Integer> stock = Map.of("Coffee", 12);
        int pizzaStock = Optional.ofNullable(stock.get("Pizza")).orElse(0);
        System.out.println("Pizza stock: " + pizzaStock);
    }
}
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `Product.java`: lezione 19

## Esercizio 22: ricerca senza null

Obiettivo: Restituire un Optional e gestire esplicitamente l’assenza.

1. **Implementa `findBySku(products, sku)`**: restituisci `Optional` del primo `Product` con codice uguale a `sku` oppure `Optional.empty`.
2. **Implementa `priceOrZero`** usando `findBySku`, `map` e `orElse`: prezzo del prodotto trovato oppure `0`.

I dati non sono `null`.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
import java.util.*;

public class Exercise {

    public record Product(String sku, int priceInCents) {}

    public Optional<Product> findBySku(List<Product> products, String sku) {
        // TODO: completa questo blocco.
        // Suggerimento: Confronta i codici con equals, non con ==.
        // Puoi filtrare lo stream e usare findFirst(), che restituisce già un Optional.
        return Optional.empty();
    }

    public int priceOrZero(List<Product> products, String sku) {
        // TODO: completa questo blocco.
        // Suggerimento: Riusa findBySku: map legge il prezzo solo se il prodotto esiste.
        // orElse fornisce il valore da usare quando l’Optional è vuoto.
        return 0;
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
import java.util.*;

public class Exercise {

    public record Product(String sku, int priceInCents) {}

    public Optional<Product> findBySku(List<Product> products, String sku) {
        return products
            .stream()
            .filter(p -> p.sku().equals(sku))
            .findFirst();
    }

    public int priceOrZero(List<Product> products, String sku) {
        return findBySku(products, sku).map(Product::priceInCents).orElse(0);
    }
}
~~~

Vogliamo cercare un prodotto per codice e dire chiaramente, nel tipo restituito, che può non esserci.

In `findBySku` usiamo uno stream: `filter` tiene solo i prodotti per cui `p.sku().equals(sku)` è vero, e `findFirst()` prende il primo. Come abbiamo accennato nella lezione 22, `findFirst()` restituisce già un `Optional`: pieno se ha trovato qualcosa, vuoto altrimenti. Non dobbiamo scrivere né `Optional.of` né `Optional.empty`. Confrontiamo i codici con `equals` perché `==` confronta i riferimenti, non il testo.

In `priceOrZero` riusiamo `findBySku` e leggiamo la catena da sinistra a destra. `map(Product::priceInCents)` trasforma il prodotto nel suo prezzo, ma solo se l'`Optional` è pieno; se è vuoto, resta vuoto. `orElse(0)` apre la scatola: restituisce il prezzo se c'è, altrimenti 0. Niente `null` e niente `get()` senza controllo, come raccomanda la lezione.

Un errore tipico è restituire `null` quando il prodotto manca. Il test `modelsAbsenceWithoutNull` si aspetta `Optional.empty()`, e `null` non gli è uguale. Un altro errore è tenere l'ultimo prodotto trovato, per esempio con un ciclo che continua dopo la prima corrispondenza. Il test `returnsFirstMatch` ha due prodotti `B1`, da 100 e da 200 centesimi, e si aspetta `100`.

Va bene anche un for-each che restituisce `Optional.of(p)` alla prima corrispondenza e `Optional.empty()` dopo il ciclo.

## Riepilogo

- null non compare nel tipo, Optional sì
- Creare: of, ofNullable, empty
- Leggere: ifPresent, map, orElse, orElseGet, orElseThrow
