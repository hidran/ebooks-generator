# Lezione 20. Lambda e interfacce funzionali

## Punti chiave

### Comportamento come dato

- sort sa ordinare una lista, ma non sa confrontare due prodotti
- Il confronto glielo passo io, come un valore
- Per prezzo o per nome: stesso sort, comportamento diverso

> Percorso: products, poi sort(byPrice), poi ordinati per prezzo.

### Interfaccia funzionale e lambda

- Interfaccia funzionale: un solo metodo astratto
- Comparator&lt;Product&gt; ha solo compare
- Lambda: (a, b) -&gt; Integer.compare(...)
- Parametri, freccia, corpo: i tipi li ricava il compilatore

### Le interfacce di java.util.function

- Predicate&lt;T&gt;: test, risponde true o false (removeIf)
- Function&lt;T, R&gt;: apply, trasforma T in R
- Supplier&lt;T&gt;: get, fornisce un valore
- Consumer&lt;T&gt;: accept, usa un valore (forEach)

## Codice della lezione

`sort/Main.java`

~~~java
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
public class Main {
    public static void main(String[] args) {
        List<Product> products = new ArrayList<>(List.of(
                new Product("Pen", 150),
                new Product("Book", 1200),
                new Product("Coffee", 250)));
        Comparator<Product> byPrice =
                (a, b) -> Integer.compare(a.priceInCents(), b.priceInCents());
        products.sort(byPrice);
        products.forEach(p -> System.out.println(p));
        products.sort(Comparator.comparing(Product::name));
        products.forEach(p -> System.out.println(p.name()));
    }
}
~~~

`Main.java`

~~~java
import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;
import java.util.function.Function;
import java.util.function.Predicate;
import java.util.function.Supplier;
public class Main {
    public static void main(String[] args) {
        Supplier<Product> gift = () -> new Product("Sticker", 0);
        List<Product> products = new ArrayList<>(List.of(
                new Product("Pen", 150),
                new Product("Book", 1200),
                new Product("Coffee", 250),
                gift.get()));
        Predicate<Product> isFree = p -> p.priceInCents() == 0;
        products.removeIf(isFree);
        PriceRule discount = cents -> cents * 90 / 100;
        Function<Product, String> label = Product::name;
        Consumer<Product> print = p -> {
            int price = discount.apply(p.priceInCents());
            System.out.println(label.apply(p) + ": " + price);
        };
        products.forEach(print);
        System.out.println("Products left: " + products.size());
    }
}
~~~

`PriceRule.java`

~~~java
@FunctionalInterface
public interface PriceRule {
    int apply(int priceInCents);
}
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `sort/Product.java`: lezione 19, file `Product.java`
- `Product.java`: lezione 19

## Esercizio 20: prezzi come comportamento

Obiettivo: Passare una trasformazione tramite un’interfaccia funzionale.

**Implementa `transformPrices(prices, rule)`**: crea una **nuova lista** applicando `IntUnaryOperator` `rule` a ogni prezzo nell’ordine originale.

**Non modificare** `prices` e **non sostituire la regola** ricevuta con una formula fissa.

Lista e regola non sono `null`.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
import java.util.*;
import java.util.function.IntUnaryOperator;

public class Exercise {

    public List<Integer> transformPrices(List<Integer> prices, IntUnaryOperator rule) {
        // TODO: completa questo blocco.
        // Suggerimento: Crea una nuova ArrayList<Integer> e visita prices nell’ordine ricevuto.
        // rule.applyAsInt(prezzo) esegue la regola passata dal chiamante.
        // Aggiungi ogni risultato alla nuova lista, poi restituiscila.
        return new ArrayList<>();
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
import java.util.*;
import java.util.function.IntUnaryOperator;

public class Exercise {

    public List<Integer> transformPrices(List<Integer> prices, IntUnaryOperator rule) {
        List<Integer> result = new ArrayList<>();
        for (int price : prices) result.add(rule.applyAsInt(price));
        return result;
    }
}
~~~

Dobbiamo applicare a ogni prezzo di una lista una regola che riceviamo come parametro.

Creiamo una nuova `ArrayList<Integer>` per il risultato, così la lista originale resta intatta. Poi scorriamo `prices` con un for-each, nell'ordine in cui arrivano, e per ognuno aggiungiamo `rule.applyAsInt(price)`. La variabile del ciclo è un `int`: Java estrae da solo il numero da ogni `Integer` della lista, e lo rimette in un `Integer` quando lo aggiungiamo al risultato.

Il punto dell'esercizio è che `transformPrices` non sa quale calcolo esegue. Come abbiamo visto nella lezione 20, una lambda è un comportamento passato come dato. `IntUnaryOperator` è un'interfaccia funzionale di `java.util.function`, simile a `Function` ma pensata per gli `int`: il suo unico metodo astratto, `applyAsInt`, riceve un `int` e ne restituisce un altro. Chiamandolo eseguiamo la lambda scelta da chi chiama, che sia uno sconto o un supplemento.

Un errore tipico è scrivere la formula dello sconto dentro il metodo, per esempio `price * 90 / 100`. Il primo test passerebbe, perché si aspetta `[900, 1800]`. Il secondo però passa la regola `p + 50` e si aspetta `[150, 250]`, e solo `applyAsInt` lo soddisfa. Un altro errore è sostituire gli elementi direttamente nella lista ricevuta. Il test `handlesEmptyAndPreservesInput` controlla che l'input resti `[100]`, e che una lista vuota produca una lista vuota.

## Riepilogo

- Interfaccia funzionale: un metodo astratto, @FunctionalInterface
- Lambda: parametri, freccia, corpo
- Riferimento a metodo: Product::name
