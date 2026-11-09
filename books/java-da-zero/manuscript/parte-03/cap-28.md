# Lezione 18. Collezioni, List, Set, Map e sequenced collections

## Punti chiave

### Perché le collezioni

- Un array ha una lunghezza fissa
- Un carrello cresce e si svuota
- Collezioni: oggetti che contengono altri oggetti
- Metodi pronti per aggiungere, cercare e scorrere

> Percorso: array, lunghezza fissa, poi collezione, cresce quando serve.

### Tre famiglie

- List: sequenza ordinata, duplicati ammessi
- Set: ogni elemento una volta sola
- Map: una chiave associata a un valore
- Sono interfacce: ArrayList, HashSet e HashMap le realizzano

### Sequenced collections (Java 21)

- getFirst(), getLast(), reversed()
- Prima: list.get(list.size() - 1)
- List, LinkedHashSet, LinkedHashMap (firstEntry, lastEntry)
- HashSet e HashMap: nessun ordine, niente metodi sequenced

### Quale collezione scegliere

- Ordine e duplicati: List (ArrayList)
- Solo elementi distinti: Set (HashSet, LinkedHashSet)
- Ricerca per chiave: Map (HashMap, LinkedHashMap)
- Variabile con l'interfaccia: List&lt;String&gt; cart = new ArrayList&lt;&gt;()

## Codice della lezione

`Lists.java`

~~~java
import java.util.ArrayList;
import java.util.List;
public class Lists {
    public static void main(String[] args) {
        List<String> cart = new ArrayList<>();
        cart.add("Coffee");
        cart.add("Book");
        cart.add("Coffee");
        cart.add("Pen");
        System.out.println(cart.size() + " items: " + cart);
        System.out.println("Second: " + cart.get(1));
        System.out.println("First: " + cart.getFirst());
        System.out.println("Last: " + cart.getLast());
        System.out.println("Reversed: " + cart.reversed());
        List<String> gifts = List.of("Tea", "Mug");
        try {
            gifts.add("Pen");
        } catch (UnsupportedOperationException e) {
            System.out.println("Read-only: " + gifts);
        }
    }
}
~~~

`Sets.java`

~~~java
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
public class Sets {
    public static void main(String[] args) {
        List<String> items = List.of("Tea", "Pen", "Tea", "Mug", "Pen");
        Set<String> unique = new HashSet<>(items);
        Set<String> ordered = new LinkedHashSet<>(items);
        System.out.println("Items: " + items.size());
        System.out.println("Distinct: " + unique.size());
        System.out.println("In order: " + ordered);
        System.out.println("Has Mug: " + ordered.contains("Mug"));
        System.out.println("Added again: " + ordered.add("Tea"));
    }
}
~~~

`Maps.java`

~~~java
import java.util.LinkedHashMap;
import java.util.Map;
public class Maps {
    public static void main(String[] args) {
        Map<String, Integer> quantities = new LinkedHashMap<>();
        quantities.put("Coffee", 2);
        quantities.put("Book", 1);
        quantities.put("Coffee", 3);
        System.out.println("Coffee: " + quantities.get("Coffee"));
        System.out.println("Pen: " + quantities.get("Pen"));
        System.out.println("Pen or 0: " + quantities.getOrDefault("Pen", 0));
        for (Map.Entry<String, Integer> entry : quantities.entrySet()) {
            System.out.println(entry.getKey() + " x " + entry.getValue());
        }
    }
}
~~~

## Esercizio 18: conteggio del catalogo

Obiettivo: Usare una Map per contare le occorrenze di valori ripetuti.

**Implementa `counts(skus)`**: restituisci una **nuova** `Map` che associa a ogni SKU il numero di occorrenze.

Le stringhe non sono `null` e il confronto è *case sensitive*.

**Non modificare** la lista ricevuta. Una lista vuota produce una mappa vuota.

Per ogni SKU:

1. leggi il conteggio attuale con `getOrDefault`,
2. salva il valore aumentato con `put`.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
import java.util.*;

public class Exercise {

    public Map<String, Integer> counts(List<String> skus) {
        // TODO: completa questo blocco.
        // Suggerimento: Crea una nuova HashMap<String, Integer> prima del ciclo.
        // Per ogni sku leggi il conteggio con getOrDefault(sku, 0), poi salva il valore aumentato.
        // Restituisci la mappa dopo aver visitato tutti gli elementi.
        return new HashMap<>();
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
import java.util.*;

public class Exercise {

    public Map<String, Integer> counts(List<String> skus) {
        Map<String, Integer> result = new HashMap<>();
        for (String sku : skus) result.put(sku, result.getOrDefault(sku, 0) + 1);
        return result;
    }
}
~~~

Dobbiamo contare quante volte compare ogni SKU in una lista.

Creiamo una nuova `HashMap<String, Integer>`. Come abbiamo visto nella lezione 18, una `Map` associa una chiave a un valore: qui la chiave è lo SKU e il valore è il suo conteggio. Poi scorriamo la lista con un for-each. La lista la leggiamo soltanto, e alla fine restituiamo la mappa nuova.

Dentro il ciclo scriviamo `result.put(sku, result.getOrDefault(sku, 0) + 1);`, con i due metodi della lezione. `getOrDefault(sku, 0)` legge il conteggio attuale, oppure 0 se lo SKU non è ancora nella mappa. Aggiungiamo 1 e `put` salva il nuovo valore al posto del vecchio, perché le chiavi di una mappa sono uniche.

La mappa confronta le chiavi con `equals`, che distingue maiuscole e minuscole. Per questo `"a"` e `"A"` restano due chiavi diverse, come chiede la consegna.

Il test `groupsDuplicates` conta tre `"B1"` e un `"M2"`: il primo `B1` parte da 0 e arriva a 1, il secondo a 2, il terzo a 3. Questo è il motivo per cui il valore di partenza di `getOrDefault` è 0 e non 1.

Un errore tipico è scrivere `result.put(sku, 1)` a ogni passo: il conteggio non supera mai 1, e `groupsDuplicates` troverebbe `B1=1` invece di `B1=3`. Un altro è uniformare il testo con `toLowerCase()`: il test `handlesEmptyAndCaseSensitiveValues` si aspetta `{a=1, A=1}`, non `{a=2}`. Infine `leavesInputUntouched` controlla che la lista ricevuta resti `[X, X]`.

## Riepilogo

- List: ordine e duplicati; List.of è immutabile
- Set: niente duplicati; Map: put, get, getOrDefault, entrySet
- Java 21: getFirst, getLast, reversed
