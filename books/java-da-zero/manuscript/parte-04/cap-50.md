# Lezione 32. L, sostituibilità di Liskov

## Punti chiave

### Sostituibilità

- Dove il codice si aspetta Product, ogni sottoclasse deve funzionare
- Nessuna sorpresa per chi usa la superclasse
- La L di SOLID, dal nome di Barbara Liskov

> Percorso: Codice che usa Product, poi Product, poi Qualsiasi sottoclasse.

### Il contratto di un metodo

- Precondizioni: che cosa chiede a chi lo chiama
- Garanzie: che cosa promette in cambio
- La sottoclasse non chiede di più e non dà di meno

### Segnali di una gerarchia sbagliata

- Un override che lancia UnsupportedOperationException
- Un override che non fa nulla
- Un if con instanceof nel codice che usa la gerarchia
- Rimedio: spostare il comportamento in un'interfaccia mirata

## Codice della lezione

`Product.java`

~~~java
public class Product {
    private final String name;
    private final int priceInCents;
    public Product(String name, int priceInCents) {
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

`before/Product.java`

~~~java
public class Product {
    private final String name;
    private final int priceInCents;
    public Product(String name, int priceInCents) {
        this.name = name;
        this.priceInCents = priceInCents;
    }
    public String getName() {
        return name;
    }
    public int getPriceInCents() {
        return priceInCents;
    }
    public int shippingCostInCents() {
        return 500;
    }
}
~~~

`DigitalProduct.java`

~~~java
public class DigitalProduct extends Product {
    public DigitalProduct(String name, int priceInCents) {
        super(name, priceInCents);
    }
}
~~~

`PhysicalProduct.java`

~~~java
public class PhysicalProduct extends Product implements Shippable {
    public PhysicalProduct(String name, int priceInCents) {
        super(name, priceInCents);
    }
    @Override
    public int shippingCostInCents() {
        return 500;
    }
}
~~~

`before/DigitalProduct.java`

~~~java
public class DigitalProduct extends Product {
    public DigitalProduct(String name, int priceInCents) {
        super(name, priceInCents);
    }
    @Override
    public int shippingCostInCents() {
        throw new UnsupportedOperationException("Cannot be shipped");
    }
}
~~~

`Main.java`

~~~java
import java.util.List;
public class Main {
    static int totalShipping(List<Shippable> parcels) {
        return parcels.stream()
                .mapToInt(Shippable::shippingCostInCents)
                .sum();
    }
    public static void main(String[] args) {
        PhysicalProduct book = new PhysicalProduct("Book", 1500);
        PhysicalProduct mug = new PhysicalProduct("Mug", 800);
        DigitalProduct ebook = new DigitalProduct("Ebook", 900);
        List<Product> cart = List.of(book, mug, ebook);
        List<Shippable> parcels = List.of(book, mug);
        int price = cart.stream().mapToInt(Product::getPriceInCents).sum();
        System.out.println("Cart price: " + price);
        System.out.println("Shipping: " + totalShipping(parcels));
    }
}
~~~

`before/Main.java`

~~~java
import java.util.List;
public class Main {
    static int totalShipping(List<Product> products) {
        return products.stream()
                .mapToInt(Product::shippingCostInCents)
                .sum();
    }
    public static void main(String[] args) {
        Product book = new Product("Book", 1500);
        Product mug = new Product("Mug", 800);
        Product ebook = new DigitalProduct("Ebook", 900);
        List<Product> physical = List.of(book, mug);
        List<Product> mixed = List.of(book, mug, ebook);
        System.out.println("Physical only: " + totalShipping(physical));
        try {
            System.out.println("With ebook: " + totalShipping(mixed));
        } catch (UnsupportedOperationException e) {
            System.out.println("Checkout failed: " + e.getMessage());
        }
    }
}
~~~

`Shippable.java`

~~~java
public interface Shippable {
    int shippingCostInCents();
}
~~~

## Esercizio 32: un contratto sostituibile

Obiettivo: Separare la capacità di spedire dai prodotti che non la possiedono.

`Shippable` espone `shippingCost()`. `PhysicalProduct` la implementa, `DigitalProduct` ne è indipendente.

**Implementa `shippingTotal`** per sommare il costo di ogni `Shippable` ricevuto **senza controllare il tipo concreto**.

Lista vuota: `0`. Nessun oggetto `null`.

**Non aggiungere spedizione** a `DigitalProduct`.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
import java.util.List;

public class Exercise {

    public interface Shippable {
        int shippingCost();
    }

    public record PhysicalProduct(int shippingCost) implements Shippable {}

    public record DigitalProduct(String downloadUrl) {}

    public int shippingTotal(List<Shippable> products) {
        // TODO: completa questo blocco.
        // Suggerimento: Visita ogni elemento come Shippable e chiamane shippingCost().
        // Accumula i costi partendo da zero: non servono controlli sui tipi concreti.
        return 0;
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
import java.util.List;

public class Exercise {

    public interface Shippable {
        int shippingCost();
    }

    public record PhysicalProduct(int shippingCost) implements Shippable {}

    public record DigitalProduct(String downloadUrl) {}

    public int shippingTotal(List<Shippable> products) {
        int total = 0;
        for (Shippable p : products) total += p.shippingCost();
        return total;
    }
}
~~~

Vogliamo sommare il costo di spedizione di una lista di oggetti spedibili, senza chiederci che cosa siano davvero.

Il metodo `shippingTotal` parte da `int total = 0`, scorre la lista con un `for` e somma `p.shippingCost()` di ogni elemento. Lavora solo con l'interfaccia `Shippable`: qualunque implementazione onesta va bene.

È il principio di sostituibilità di Liskov, la L di SOLID della lezione 32. Dove il codice si aspetta uno `Shippable`, ogni implementazione deve funzionare senza sorprese. Per questo `DigitalProduct` non implementa `Shippable`. Se lo facesse, dovrebbe restituire un costo finto, o lanciare `UnsupportedOperationException`. Sono proprio i segnali di una gerarchia sbagliata visti nella lezione. Il codice che somma le spedizioni dovrebbe poi difendersi con un `instanceof`, e ogni nuovo prodotto senza spedizione lo costringerebbe a cambiare ancora. Separando la capacità in un'interfaccia mirata, il problema non nasce.

Un errore tipico è controllare il tipo concreto, per esempio con `if (p instanceof PhysicalProduct pp)`. Il test `acceptsAnyHonestImplementation` passa anche la lambda `() -> 400`, che non è un `PhysicalProduct`: con quel controllo la salteresti e otterresti `490` invece di `890`. Il test `digitalProductDoesNotClaimShippingCapability` verifica invece che `DigitalProduct` non sia diventato `Shippable`. La lista vuota deve dare `0`, e il nostro `total` iniziale lo garantisce.

Uno stream con `mapToInt(Shippable::shippingCost).sum()` è un'alternativa altrettanto corretta.

## Riepilogo

- Una sottoclasse sostituisce la superclasse senza sorprese
- Non restringe le precondizioni, non indebolisce le garanzie
- Comportamento di alcuni tipi soltanto: un'interfaccia, come Shippable
