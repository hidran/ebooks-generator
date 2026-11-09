# Lezione 25. Concorrenza con thread, executor e CompletableFuture

## Punti chiave

### Che cos'è un thread

- Un flusso di esecuzione dentro il programma
- main gira nel thread "main"
- Più thread lavorano insieme, sui diversi core
- L'ordine non è prevedibile: join aspetta la fine

> Percorso: main, poi start, poi lavoro in parallelo, poi join, poi risultato.

### Il contatore condiviso

- count++ sono tre passi: leggi, somma, scrivi
- Due thread leggono lo stesso valore: un aggiornamento perso
- 2 thread x 100.000 incrementi: spesso meno di 200.000
- Soluzioni: non condividere, oppure AtomicInteger

### Regole per lavorare in parallelo

- Niente dati modificabili condivisi: record e oggetti immutabili
- Contatore condiviso: AtomicInteger e incrementAndGet
- Risultati con join o get, mai l'ordine dei thread
- Executor sempre chiuso: shutdown nel finally

## Codice della lezione

`Main.java`, passaggio intermedio («threads»)

~~~java
import java.util.List;
public class Main {
    public static void main(String[] args) throws InterruptedException {
        Order first = new Order("A1", List.of(1200, 800, 450));
        Order second = new Order("B2", List.of(2500, 300));
        int[] totals = new int[2];
        Thread one = Thread.ofPlatform().start(() -> totals[0] = first.total());
        Thread two = Thread.ofPlatform().start(() -> totals[1] = second.total());
        one.join();
        two.join();
        System.out.println(first.id() + " total: " + totals[0]);
        System.out.println(second.id() + " total: " + totals[1]);
        System.out.println("Grand total: " + (totals[0] + totals[1]));
    }
}
~~~

`Main.java`, passaggio intermedio («executor»)

~~~java
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.atomic.AtomicInteger;
public class Main {
    private static final AtomicInteger processed = new AtomicInteger();
    private static int totalOf(Order order) {
        processed.incrementAndGet();
        return order.total();
    }
    public static void main(String[] args) throws Exception {
        Order first = new Order("A1", List.of(1200, 800, 450));
        Order second = new Order("B2", List.of(2500, 300));
        ExecutorService pool = Executors.newFixedThreadPool(2);
        try {
            Future<Integer> firstTotal = pool.submit(() -> totalOf(first));
            Future<Integer> secondTotal = pool.submit(() -> totalOf(second));
            int grandTotal = firstTotal.get() + secondTotal.get();
            System.out.println("Orders processed: " + processed.get());
            System.out.println("Grand total: " + grandTotal);
        } finally {
            pool.shutdown();
        }
    }
}
~~~

`Main.java`

~~~java
import java.util.List;
import java.util.concurrent.CompletableFuture;
public class Main {
    public static void main(String[] args) {
        Order first = new Order("A1", List.of(1200, 800, 450));
        Order second = new Order("B2", List.of(2500, 300));
        int shippingInCents = 500;
        var firstTotal = CompletableFuture.supplyAsync(first::total)
                .thenApply(total -> total + shippingInCents);
        var secondTotal = CompletableFuture.supplyAsync(second::total)
                .thenApply(total -> total + shippingInCents);
        int grandTotal = firstTotal.join() + secondTotal.join();
        System.out.println(first.id() + " with shipping: " + firstTotal.join());
        System.out.println(second.id() + " with shipping: " + secondTotal.join());
        System.out.println("Grand total: " + grandTotal);
    }
}
~~~

`Order.java`

~~~java
import java.util.List;
public record Order(String id, List<Integer> pricesInCents) {
    public int total() {
        return pricesInCents.stream().mapToInt(Integer::intValue).sum();
    }
}
~~~

## Esercizio 25: comporre due attività asincrone

Obiettivo: Combinare CompletableFuture senza condividere stato mutabile.

**Implementa `combine(first, second)`**: restituisci un `CompletableFuture` che concatena il risultato del primo, `":"` e quello del secondo, mantenendo quest’ordine anche se il secondo completa prima.

Usa **`thenCombine` senza `join` o `get`** nel metodo: è il fratello di `thenApply` che aspetta due future, per esempio `a.thenCombine(b, (x, y) -> x + y)` restituisce subito un nuovo future con la somma dei due risultati.

Un errore di uno dei future deve **propagarsi** al risultato.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
import java.util.concurrent.CompletableFuture;

public class Exercise {

    public CompletableFuture<String> combine(
        CompletableFuture<String> first,
        CompletableFuture<String> second
    ) {
        // TODO: completa questo blocco.
        // Suggerimento: thenCombine riceve l’altro future e una lambda con i due risultati.
        // La lambda costruisce il testo nell’ordine primo, separatore, secondo.
        // Restituisci il future composto senza attendere qui il completamento.
        return CompletableFuture.completedFuture("");
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
import java.util.concurrent.CompletableFuture;

public class Exercise {

    public CompletableFuture<String> combine(
        CompletableFuture<String> first,
        CompletableFuture<String> second
    ) {
        return first.thenCombine(second, (a, b) -> a + ":" + b);
    }
}
~~~

Vogliamo combinare il risultato di due `CompletableFuture` in una sola stringa, `primo:secondo`, senza mai bloccare il thread che chiama.

Basta una riga: `first.thenCombine(second, (a, b) -> a + ":" + b)`. Nella lezione 25 abbiamo usato `thenApply` per trasformare il risultato di un solo future. `thenCombine`, che la consegna presenta con un esempio, è il fratello che ne aspetta due: restituisce subito un nuovo future, e la lambda parte solo quando entrambi sono completati. L'ordine dei parametri segue quello dei future, non quello in cui finiscono, quindi `a` è sempre il primo. Non c'è stato condiviso, come chiedono le regole della lezione.

Se uno dei due future fallisce, la lambda non viene eseguita e il future risultante fallisce con la stessa causa. Il metodo non deve fare niente di speciale: chi chiama `join()` riceve una `CompletionException` e recupera `IllegalStateException("unavailable")` con `getCause()`.

L'errore tipico è chiamare `join()` dentro `combine`, anche nascosto in un `supplyAsync`: il test `neverCallsJoinOrGetOnTheInputs` usa future che ricordano se qualcuno ha chiamato `join()` o `get()`. I test avvolgono la chiamata in un timeout di due secondi, così un metodo che aspetta fallisce con un messaggio chiaro invece di restare bloccato. `combinesResultsInArgumentOrder` completa prima `b` e poi `a`; `keepsTheOrderWhenTheSecondFutureCompletesLast` fa l'inverso e smaschera chi legge il secondo future con `getNow`. Per gli errori ci sono due test distinti: `propagatesFailureOfTheFirstFuture` e `propagatesFailureOfTheSecondFuture`. Chi ripara il secondo future con `exceptionally` supera il primo e fallisce nel secondo.

## Riepilogo

- Thread.ofPlatform().start(...) e join
- ExecutorService: submit, Future.get, shutdown
- CompletableFuture: supplyAsync, thenApply, join
