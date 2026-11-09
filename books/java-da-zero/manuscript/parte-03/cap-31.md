# Lezione 21. Stream e Gatherers

## Punti chiave

### Dai cicli agli stream

- stream(): una sorgente di elementi, per esempio una lista
- Operazioni intermedie: filter, map, sorted, limit
- Operazione terminale: toList(), count(), sum(), collect(...)

> Percorso: Sorgente, poi Operazioni intermedie, poi Operazione terminale, poi Risultato.

### Una pipeline pigra

- Le operazioni intermedie descrivono il lavoro, non lo eseguono
- Tutto parte con l'operazione terminale
- Gli elementi attraversano la pipeline uno alla volta
- Uno stream si consuma una sola volta

### La novità: i Gatherers

- stream.gather(...): operazioni intermedie su misura (JEP 485, finale da Java 24)
- Gatherers.windowFixed(n): finestre separate di n elementi
- Gatherers.windowSliding(n): finestre che scorrono di un elemento
- Gatherers.fold e scan: accumulare un valore

> Percorso: Pen, Notebook, Stapler, poi windowFixed(2), poi [Pen, Notebook], [Stapler].

## Codice della lezione

`Main.java`, prima versione

~~~java
import java.util.Comparator;
import java.util.List;
public class Main {
    public static void main(String[] args) {
        List<Product> products = List.of(
                new Product("Pen", "office", 150),
                new Product("Notebook", "office", 400),
                new Product("Stapler", "office", 650),
                new Product("Coffee", "food", 250),
                new Product("Tea", "food", 300),
                new Product("Book", "books", 1500),
                new Product("Comic", "books", 800));
        List<String> cheapest = products.stream()
                .filter(p -> p.priceInCents() < 500)
                .sorted(Comparator.comparingInt(Product::priceInCents))
                .map(Product::name)
                .limit(3)
                .toList();
        System.out.println("Cheapest three: " + cheapest);
        long expensive = products.stream()
                .filter(p -> p.priceInCents() >= 500)
                .count();
        System.out.println("Expensive items: " + expensive);
        int total = products.stream()
                .mapToInt(Product::priceInCents)
                .sum();
        System.out.println("Catalog total: " + total);
    }
}
~~~

`Main.java`

~~~java
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.stream.Collectors;
import java.util.stream.Gatherers;
public class Main {
    public static void main(String[] args) {
        List<Product> products = List.of(
                new Product("Pen", "office", 150),
                new Product("Notebook", "office", 400),
                new Product("Stapler", "office", 650),
                new Product("Coffee", "food", 250),
                new Product("Tea", "food", 300),
                new Product("Book", "books", 1500),
                new Product("Comic", "books", 800));
        Map<String, Long> countByCategory = products.stream()
                .collect(Collectors.groupingBy(Product::category, TreeMap::new,
                        Collectors.counting()));
        System.out.println("Count: " + countByCategory);
        Map<String, Integer> totalByCategory = products.stream()
                .collect(Collectors.groupingBy(Product::category, TreeMap::new,
                        Collectors.summingInt(Product::priceInCents)));
        System.out.println("Total: " + totalByCategory);
        List<List<String>> pages = products.stream()
                .map(Product::name)
                .gather(Gatherers.windowFixed(2))
                .toList();
        System.out.println("Pages: " + pages);
    }
}
~~~

`Product.java`

~~~java
public record Product(String name, String category, int priceInCents) {
}
~~~

## Esercizio 21: pipeline di stream

Obiettivo: Filtrare e aggregare con Stream senza effetti collaterali.

**Implementa `totalAbove(prices, minimum)`**:

1. considera i prezzi maggiori o uguali a `minimum`,
2. restituisci la loro somma usando `stream`, `filter` e `mapToInt`.

**Non modificare** la lista. Una lista vuota o senza prezzi ammessi dà `0`.

I *Gatherers* del video si provano localmente con Java 25.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
import java.util.List;

public class Exercise {

    public int totalAbove(List<Integer> prices, int minimum) {
        // TODO: completa questo blocco.
        // Suggerimento: Parti da prices.stream(); filter sceglie i valori che rispettano la soglia inclusiva.
        // mapToInt trasforma gli Integer in int; sum conclude il calcolo.
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

    public int totalAbove(List<Integer> prices, int minimum) {
        return prices
            .stream()
            .filter(p -> p >= minimum)
            .mapToInt(Integer::intValue)
            .sum();
    }
}
~~~

Dobbiamo sommare i prezzi che raggiungono una soglia, senza toccare la lista.

La pipeline segue lo schema della lezione 21: sorgente, operazioni intermedie, operazione terminale. `prices.stream()` è la sorgente. `filter(p -> p >= minimum)` lascia passare solo i prezzi uguali o maggiori della soglia; la lambda è un `Predicate`, come abbiamo visto nella lezione 20. `mapToInt(Integer::intValue)` trasforma lo stream di `Integer` in un `IntStream`, uno stream di `int` che sa fare `sum()`. Il riferimento a metodo `Integer::intValue` dice come ricavare l'`int` da ogni oggetto. Infine `sum()` è l'operazione terminale che fa partire tutto il lavoro. Su uno stream vuoto restituisce `0`, quindi non serve gestire a parte né la lista vuota né il caso senza prezzi ammessi.

Lo stream legge la lista senza cambiarla, e non aggiorniamo variabili esterne: nessun effetto collaterale. Il test `doesNotMutateInput` lo verifica, controllando che la lista `[3, 1, 2]` resti così.

L'errore più comune è la soglia esclusiva, `p > minimum`. Il test `includesBoundaryAndAggregatesDuplicates` usa la soglia 100 sulla lista `[50, 100, 200, 200]` e si aspetta `500`: con `>` otterresti 400. Un altro errore è togliere i doppioni con `distinct()`, che darebbe 300.

I Gatherers della lezione sono finali solo da Java 24, per questo l'esercizio non li usa; gli esempi del video funzionano con il JDK 25 del corso.

## Riepilogo

- Sorgente, operazioni intermedie, operazione terminale
- Pipeline pigra; ogni stream si usa una volta sola
- groupingBy con TreeMap; gather con Gatherers.windowFixed
