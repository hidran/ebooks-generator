# Lezione 26. Thread virtuali e scoped values

## Punti chiave

### Thread di piattaforma e thread virtuali

- Thread di piattaforma: uno per thread del sistema operativo, costoso
- Thread virtuale: gestito dalla JVM, eseguito da pochi portatori
- Quando si blocca lascia libero il portatore. Finali da Java 21

> Percorso: migliaia di thread virtuali, poi pochi portatori, poi sistema operativo.

### Quando usarli

- Sì: attività che aspettano (rete, database, file)
- Un thread virtuale per ogni richiesta, nessun pool
- No: calcolo intensivo, che non si blocca mai
- Per il calcolo: executor con un numero fisso di thread

### ScopedValue al posto di ThreadLocal

- ScopedValue.where(USER, "anna").run(...): un valore per una chiamata
- Immutabile: niente set, si legge con get()
- Finito run, il legame sparisce da solo
- Finale da Java 25 (JEP 506)

### In anteprima: concorrenza strutturata

- StructuredTaskScope: un gruppo di attività come un'unica unità
- Partono, terminano e gestiscono gli errori insieme
- In Java 25 è ancora in anteprima: niente codice nel corso

## Codice della lezione

`VirtualThreads.java`

~~~java
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
public class VirtualThreads {
    static int chargeCoffee() throws InterruptedException {
        Thread.sleep(Duration.ofSeconds(1));
        return 250;
    }
    public static void main(String[] args) throws Exception {
        Thread first = Thread.ofVirtual().start(() -> System.out.println("Order received"));
        first.join();
        System.out.println("Virtual: " + first.isVirtual());
        List<Future<Integer>> payments = new ArrayList<>();
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < 10_000; i++) {
                payments.add(executor.submit(() -> chargeCoffee()));
            }
        }
        int total = 0;
        for (Future<Integer> payment : payments) {
            total += payment.get();
        }
        System.out.println("Payments: " + payments.size());
        System.out.println("Total cents: " + total);
    }
}
~~~

`CurrentUser.java`

~~~java
public class CurrentUser {
    static final ScopedValue<String> USER = ScopedValue.newInstance();
    static String placeOrder(String product) {
        return USER.get() + " ordered " + product;
    }
    public static void main(String[] args) {
        ScopedValue.where(USER, "anna").run(() -> System.out.println(placeOrder("Coffee")));
        ScopedValue.where(USER, "marco").run(() -> System.out.println(placeOrder("Book")));
        System.out.println("Bound outside: " + USER.isBound());
    }
}
~~~

## Esercizio 26: eseguire task con thread virtuali

Obiettivo: Avviare un’attività su un virtual thread e gestire il completamento.

**Implementa `runVirtual(task)`**:

1. apri `Executors.newVirtualThreadPerTaskExecutor()` in un `try-with-resources`,
2. consegna `task` con `submit`,
3. restituisci il risultato di `get()` sul `Future` ottenuto.

Il metodo dichiara `Exception`, perché `get` lancia eccezioni *checked*. Gli errori del task non sono oggetto di questa attività.

Il task deve girare su un **thread virtuale**, non su un thread di piattaforma.

`ScopedValue` richiede la versione del JDK usata nel corso e va provato localmente.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.function.Supplier;

public class Exercise {

    public <T> T runVirtual(Supplier<T> task) throws Exception {
        // TODO: completa questo blocco.
        // Suggerimento: Apri Executors.newVirtualThreadPerTaskExecutor() in un try-with-resources.
        // Con submit consegna una lambda che esegue task.get(): restituisce un Future<T>.
        // Restituisci future.get(), che aspetta il risultato del thread virtuale.
        return null;
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.function.Supplier;

public class Exercise {

    public <T> T runVirtual(Supplier<T> task) throws Exception {
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            Future<T> future = executor.submit(() -> task.get());
            return future.get();
        }
    }
}
~~~

Vogliamo eseguire un'attività su un thread virtuale, aspettare che finisca e restituirne il risultato.

Usiamo l'executor della lezione: `Executors.newVirtualThreadPerTaskExecutor()` avvia un thread virtuale nuovo per ogni attività, e lo apriamo in un try-with-resources, così `close` aspetta la fine dei compiti. Dentro consegniamo il lavoro con `executor.submit(() -> task.get())`, che restituisce subito un `Future<T>`: la promessa di un risultato. Infine `future.get()` aspetta il thread virtuale e ci dà il valore, che restituiamo.

Perché non un `Thread` con `join`? `Thread.ofVirtual().start` accetta un `Runnable`, che non restituisce niente, e una lambda non può assegnare una variabile locale del metodo. Il `Future` risolve il problema: porta il risultato fuori dal thread senza condividere stato. Come abbiamo visto nella lezione 26, bloccarsi in `get` costa poco, perché il thread virtuale lo gestisce la JVM. `get` può lanciare eccezioni checked, quindi la firma dichiara `throws Exception`.

Un primo errore è usare un executor di piattaforma, per esempio `Executors.newFixedThreadPool(1)`: il test `actuallyUsesVirtualThread` esegue `Thread.currentThread().isVirtual()` dentro il task e si aspetta `true`. Un secondo è restituire `null` senza aspettare il `Future`: `waitsForTaskAndReturnsValue` si aspetta `"ready"` e `42`. Il test `handlesNullResult` controlla invece che un task che restituisce `null` dia `null`, cosa che `Future.get` fa senza casi speciali.

La versione con `ScopedValue` della lezione funziona con il JDK 25 del corso; qui restiamo sulle API stabili in Java 21.

## Riepilogo

- Thread virtuali: uno per attività, bloccarsi costa poco
- Adatti alle attività che aspettano, non al calcolo intensivo
- ScopedValue: un dato immutabile per la durata di una chiamata
