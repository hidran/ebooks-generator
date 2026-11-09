# Lezione 33. I, interfacce piccole e mirate

## Punti chiave

### Un'interfaccia troppo larga

- OrderOperations: create, cancel, refund, printReceipt, exportCsv
- Cashier usa solo create, ReportJob usa solo exportCsv
- Le implementazioni finte lanciano eccezioni o non fanno niente

> Percorso: 1 interfaccia, poi 5 metodi, poi client che ne usano 1.

### Interfacce piccole e mirate

- Nessuno deve dipendere da metodi che non usa
- Un ruolo per interfaccia: OrderCreator, OrderCanceller, ReceiptPrinter, OrderExporter
- Una classe concreta, ShopOrders, implementa più ruoli
- Ogni client chiede solo il ruolo che usa

> Percorso: Cashier, poi OrderCreator, poi ShopOrders.

### Perché conviene

- Le modifiche agli altri ruoli non toccano il client
- Implementazioni oneste: niente eccezioni, Liskov rispettato
- Responsabilità unica applicata ai contratti
- Non esagerare: si spezza per ruoli reali

## Codice della lezione

`Main.java`

~~~java
public class Main {
    public static void main(String[] args) {
        ShopOrders orders = new ShopOrders();
        Cashier cashier = new Cashier(orders);
        cashier.sell("Coffee");
        cashier.sell("Tea");
        new ReportJob(orders).run();
        OrderExporter archive = () -> "Book,Pen";
        new ReportJob(archive).run();
    }
}
~~~

`ReportJob.java`

~~~java
public class ReportJob {
    private final OrderExporter orders;
    public ReportJob(OrderExporter orders) {
        this.orders = orders;
    }
    public void run() {
        System.out.println("Report: " + orders.exportCsv());
    }
}
~~~

`OrderCreator.java`

~~~java
public interface OrderCreator {
    void create(String item);
}
~~~

`OrderCanceller.java`

~~~java
public interface OrderCanceller {
    void cancel(int id);
    void refund(int id);
}
~~~

`ReceiptPrinter.java`

~~~java
public interface ReceiptPrinter {
    void printReceipt(int id);
}
~~~

`OrderExporter.java`

~~~java
public interface OrderExporter {
    String exportCsv();
}
~~~

`ShopOrders.java`

~~~java
import java.util.ArrayList;
import java.util.List;
public class ShopOrders implements OrderCreator, OrderCanceller,
        ReceiptPrinter, OrderExporter {
    private final List<String> items = new ArrayList<>();
    @Override
    public void create(String item) {
        items.add(item);
    }
    @Override
    public void cancel(int id) {
        items.set(id - 1, "cancelled");
    }
    @Override
    public void refund(int id) {
        System.out.println("Refund for order " + id);
    }
    @Override
    public void printReceipt(int id) {
        System.out.println("Receipt: " + items.get(id - 1));
    }
    @Override
    public String exportCsv() {
        return String.join(",", items);
    }
}
~~~

`Cashier.java`

~~~java
public class Cashier {
    private final OrderCreator orders;
    public Cashier(OrderCreator orders) {
        this.orders = orders;
    }
    public void sell(String item) {
        orders.create(item);
        System.out.println("Sold: " + item);
    }
}
~~~

`before/ReportJob.java`

~~~java
public class ReportJob {
    private final OrderOperations orders;
    public ReportJob(OrderOperations orders) {
        this.orders = orders;
    }
    public void run() {
        System.out.println("Report: " + orders.exportCsv());
    }
}
~~~

`before/ArchiveOrders.java`

~~~java
public class ArchiveOrders implements OrderOperations {
    @Override
    public void create(String item) {
        throw new UnsupportedOperationException("create");
    }
    @Override
    public void cancel(int id) {
        throw new UnsupportedOperationException("cancel");
    }
    @Override
    public void refund(int id) {
        throw new UnsupportedOperationException("refund");
    }
    @Override
    public void printReceipt(int id) {
    }
    @Override
    public String exportCsv() {
        return "Book,Pen";
    }
}
~~~

`before/Main.java`

~~~java
public class Main {
    public static void main(String[] args) {
        OrderOperations archive = new ArchiveOrders();
        new ReportJob(archive).run();
        archive.printReceipt(1);
        try {
            archive.cancel(1);
        } catch (UnsupportedOperationException e) {
            System.out.println("Not supported: " + e.getMessage());
        }
    }
}
~~~

`before/OrderOperations.java`

~~~java
public interface OrderOperations {
    void create(String item);
    void cancel(int id);
    void refund(int id);
    void printReceipt(int id);
    String exportCsv();
}
~~~

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
cd isp/before
cat OrderOperations.java
cat ReportJob.java
cat ArchiveOrders.java
cat Main.java
java Main.java
~~~

## Esercizio 33: interfacce per ruolo

Obiettivo: Fare dipendere un client soltanto dalla capacità che utilizza.

`OrderCreator` ha solo `create(customer)`. `OrderExporter` ha `exportCsv()`. `Cashier` riceve *esclusivamente* `OrderCreator` dal costruttore.

**Completa `checkout(customer)`**: delega a `creator.create` e restituisci il codice ottenuto.

**Non introdurre dipendenze** da `OrderExporter` né implementazioni concrete.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
public class Exercise {

    public interface OrderCreator {
        String create(String customer);
    }

    public interface OrderExporter {
        String exportCsv();
    }

    public static class Cashier {

        private final OrderCreator creator;

        public Cashier(OrderCreator creator) {
            this.creator = creator;
        }

        public String checkout(String customer) {
            // TODO: completa questo blocco.
            // Suggerimento: creator è stato salvato nel costruttore: riusa questo oggetto.
            // Passa customer a create e restituisci il codice ricevuto.
            return "";
        }
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
public class Exercise {

    public interface OrderCreator {
        String create(String customer);
    }

    public interface OrderExporter {
        String exportCsv();
    }

    public static class Cashier {

        private final OrderCreator creator;

        public Cashier(OrderCreator creator) {
            this.creator = creator;
        }

        public String checkout(String customer) {
            return creator.create(customer);
        }
    }
}
~~~

Vogliamo una cassa che crei ordini dipendendo soltanto dalla capacità che usa davvero.

Il metodo `checkout` fa una sola cosa: `return creator.create(customer);`. Passa il cliente al ruolo ricevuto dal costruttore e restituisce il codice dell'ordine così com'è. `Cashier` non conosce nessuna classe concreta e non sa nemmeno che esiste `OrderExporter`.

È il principio di segregazione delle interfacce, la I di SOLID della lezione 33: nessuno deve dipendere da metodi che non usa. Ricordi `OrderOperations` con cinque metodi? Se `Cashier` dipendesse da quella, ogni modifica a `exportCsv` o a `refund` lo toccherebbe. Ogni implementazione finta per le prove dovrebbe scrivere anche i metodi inutili, spesso lanciando eccezioni. Con un ruolo piccolo come `OrderCreator`, nei test basta una lambda: `name -> "ORDER:" + name`. Una classe vera come `ShopOrders` può comunque implementare più ruoli insieme.

Un errore tipico è costruire il codice dentro la cassa, per esempio `"ORDER:" + customer`. Il primo test passerebbe per caso. Il secondo no: il suo creator restituisce `"42"` e registra il nome ricevuto, e il test controlla sia il risultato `"42"` sia che sia arrivato proprio `"Luca"`. Allo stesso modo, aggiungere un campo `OrderExporter` al costruttore cambierebbe la firma e i test non compilerebbero più.

## Riepilogo

- Nessuno deve dipendere da metodi che non usa
- Interfaccia troppo larga: implementazioni finte
- Ruoli piccoli; una classe può implementarne più d'uno
