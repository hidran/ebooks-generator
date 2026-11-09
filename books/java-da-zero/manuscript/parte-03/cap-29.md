# Lezione 19. Generics

## Punti chiave

### Perché i generics

- Lista senza tipo: accetta tutto, servono i cast
- L'errore compare solo durante l'esecuzione: ClassCastException
- List&lt;String&gt;: il compilatore controlla ogni add e ogni get

> Percorso: errore in esecuzione, poi generics, poi errore di compilazione.

### Parametri di tipo

- Classe generica: class Box&lt;T&gt;
- Metodo generico: static &lt;T&gt; T firstOf(List&lt;T&gt; items)
- Diamante: new ArrayList&lt;&gt;(), il tipo lo deduce il compilatore
- Anche un record: record Pair&lt;A, B&gt;(A first, B second)

### Limiti e wildcard

- &lt;T extends Comparable&lt;T&gt;&gt;: solo tipi confrontabili
- In cambio si usano i loro metodi: compareTo
- Wildcard, solo un cenno: List&lt;? extends Number&gt; per leggere

## Codice della lezione

`Product.java`

~~~java
public record Product(String name, int priceInCents) {
}
~~~

`Main.java`

~~~java
import java.util.ArrayList;
import java.util.List;
public class Main {
    public static void main(String[] args) {
        List<String> names = new ArrayList<>();
        names.add("Coffee");
        names.add("Tea");
        String first = names.get(0);
        System.out.println("First: " + first.toUpperCase());
        String second = names.get(1);
        System.out.println("Second: " + second.toUpperCase());
    }
}
~~~

`Main.java`, passaggio intermedio («raw»)

~~~java
import java.util.ArrayList;
import java.util.List;
public class Main {
    public static void main(String[] args) {
        List names = new ArrayList();
        names.add("Coffee");
        names.add(42);
        String first = (String) names.get(0);
        System.out.println("First: " + first.toUpperCase());
        String second = (String) names.get(1);
        System.out.println("Second: " + second.toUpperCase());
    }
}
~~~

`Main.java`, versione con un errore voluto: non compila o il test fallisce, per leggere il messaggio

~~~java
import java.util.ArrayList;
import java.util.List;
public class Main {
    public static void main(String[] args) {
        List<String> names = new ArrayList<>();
        names.add("Coffee");
        names.add(42);
        String first = names.get(0);
        System.out.println("First: " + first.toUpperCase());
        String second = names.get(1);
        System.out.println("Second: " + second.toUpperCase());
    }
}
~~~

`Box.java`

~~~java
public class Box<T> {
    private final T content;
    public Box(T content) {
        this.content = content;
    }
    public T get() {
        return content;
    }
}
~~~

`Shop.java`

~~~java
import java.util.List;
public class Shop {
    static <T> T firstOf(List<T> items) {
        return items.get(0);
    }
    static <T extends Comparable<T>> T max(List<T> items) {
        T best = items.get(0);
        for (T item : items) {
            if (item.compareTo(best) > 0) {
                best = item;
            }
        }
        return best;
    }
    public static void main(String[] args) {
        Box<Product> box = new Box<>(new Product("Coffee", 250));
        Product product = box.get();
        System.out.println("In the box: " + product.name());
        List<Integer> prices = List.of(250, 1500, 120);
        List<String> names = List.of("Tea", "Coffee", "Water");
        Integer firstPrice = firstOf(prices);
        String firstName = firstOf(names);
        System.out.println("First price: " + firstPrice);
        System.out.println("First name: " + firstName);
        System.out.println("Highest price: " + max(prices));
        System.out.println("Last alphabetically: " + max(names));
    }
}
~~~

`Shop.java`, prima versione

~~~java
import java.util.List;
public class Shop {
    static <T> T firstOf(List<T> items) {
        return items.get(0);
    }
    public static void main(String[] args) {
        Box<Product> box = new Box<>(new Product("Coffee", 250));
        Product product = box.get();
        System.out.println("In the box: " + product.name());
        List<Integer> prices = List.of(250, 1500, 120);
        List<String> names = List.of("Tea", "Coffee", "Water");
        Integer firstPrice = firstOf(prices);
        String firstName = firstOf(names);
        System.out.println("First price: " + firstPrice);
        System.out.println("First name: " + firstName);
    }
}
~~~

## Esercizio 19: un contenitore generico

Obiettivo: Scrivere un metodo generico che preserva il tipo senza cast.

**Implementa `firstOr(values, fallback)`**, mantenendo il parametro di tipo `T`:

- restituisci il primo elemento quando la lista non è vuota,
- altrimenti `fallback`.

**Non usare `Object`** come tipo restituito e **non modificare la lista**.

La lista non è `null`.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
import java.util.List;

public class Exercise {

    public <T> T firstOr(List<T> values, T fallback) {
        // TODO: completa questo blocco.
        // Suggerimento: T è il tipo scelto da chi chiama: usa lo stesso tipo per elemento e risultato.
        // Con un if controlla isEmpty() prima di leggere l’indice 0: se la lista è vuota restituisci fallback.
        return fallback;
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
import java.util.List;

public class Exercise {

    public <T> T firstOr(List<T> values, T fallback) {
        if (values.isEmpty()) return fallback;
        return values.get(0);
    }
}
~~~

Vogliamo un metodo che restituisca il primo elemento di una lista, o un valore di riserva, mantenendo il tipo scelto da chi chiama.

Il cuore è già nella firma: `<T> T firstOr(List<T> values, T fallback)`. Come abbiamo visto nella lezione 19, `<T>` dichiara un parametro di tipo. La lista, il valore di riserva e il risultato condividono lo stesso `T`. Quando un test passa una `List<String>`, il compilatore deduce che `T` è `String`, e il risultato finisce in una variabile `String` senza cast. Con `List.of(42, 7)` lo stesso metodo restituisce un `Integer`.

Il corpo ha due righe: `if (values.isEmpty()) return fallback;` e poi `return values.get(0);`. Controlliamo `isEmpty()` prima di leggere l'indice 0 perché `get(0)` su una lista vuota lancia un'eccezione. Il `return` dentro l'`if` termina subito il metodo, quindi la seconda riga arriva solo quando la lista ha almeno un elemento.

Un errore tipico è leggere `values.get(0)` senza controllo. Il test `returnsFallbackForEmptyList` passa `List.<String>of()` e si aspetta `"Missing"`. Lo stesso test usa `null` come riserva su una lista vuota di `Integer`, e il metodo lo restituisce senza problemi. Un altro errore è cambiare il tipo restituito in `Object`: in `preservesStringType` la riga `String value = new Exercise().firstOr(...)` non compilerebbe più senza un cast. Infine `preservesIntegerType` verifica lo stesso comportamento con `List.of(42, 7)`.

## Riepilogo

- Gli errori di tipo passano dall'esecuzione alla compilazione
- Niente cast: il tipo si scrive tra parentesi angolari
- Classe generica, metodo generico, limite con extends
