# Lezione 30. S, una sola responsabilità

## Punti chiave

### SOLID e la prima lettera

- SOLID: cinque principi per codice facile da cambiare
- S: Single Responsibility, responsabilità singola
- Una classe ha una sola ragione per cambiare
- Non vuol dire un solo metodo o poche righe

### Il test della congiunzione "e"

- Descrivi la classe in una frase
- Calcola il totale e applica l'IVA e prepara la ricevuta e salva
- Ogni "e" è un indizio, non una condanna
- Chi mi chiederà di cambiare questo codice?

### Quanto dividere

- Calcolo e IVA restano insieme: cambiano insieme
- Troppe classi minuscole: si torna a violare KISS
- Si divide quando le richieste arrivano da esigenze diverse
- In cambio: modifiche piccole, test mirati, meno conflitti

> Percorso: Order, poi PriceCalculator, poi Totals, poi ReceiptFormatter, poi Ricevuta.

## Codice della lezione

`OrderService.java`, prima del refactoring

~~~java
public class OrderService {
    private static final int VAT_PERCENT = 22;
    public void checkout(Order order) {
        int subtotal = order.lines().stream()
                .mapToInt(line -> line.priceInCents() * line.quantity())
                .sum();
        int vat = subtotal * VAT_PERCENT / 100;
        int total = subtotal + vat;
        String receipt = "Customer: " + order.customer()
                + "\nSubtotal: " + subtotal
                + "\nVAT: " + vat
                + "\nTotal: " + total;
        System.out.println(receipt);
        System.out.println("Order saved for " + order.customer());
    }
}
~~~

`OrderService.java`

~~~java
public class OrderService {
    private final PriceCalculator calculator = new PriceCalculator();
    private final ReceiptFormatter formatter = new ReceiptFormatter();
    public void checkout(Order order) {
        Totals totals = calculator.totals(order);
        System.out.println(formatter.format(order, totals));
        System.out.println("Order saved for " + order.customer());
    }
}
~~~

`Main.java`

~~~java
import java.util.List;
public class Main {
    public static void main(String[] args) {
        Order order = new Order("Anna", List.of(
                new OrderLine("Book", 1500, 1),
                new OrderLine("Coffee", 250, 2)));
        new OrderService().checkout(order);
    }
}
~~~

`Order.java`

~~~java
import java.util.List;
public record Order(String customer, List<OrderLine> lines) {
}
record OrderLine(String product, int priceInCents, int quantity) {
}
~~~

`PriceCalculator.java`

~~~java
public class PriceCalculator {
    private static final int VAT_PERCENT = 22;
    public Totals totals(Order order) {
        int subtotal = order.lines().stream()
                .mapToInt(line -> line.priceInCents() * line.quantity())
                .sum();
        int vat = subtotal * VAT_PERCENT / 100;
        return new Totals(subtotal, vat, subtotal + vat);
    }
}
record Totals(int subtotal, int vat, int total) {
}
~~~

`ReceiptFormatter.java`

~~~java
public class ReceiptFormatter {
    public String format(Order order, Totals totals) {
        return "Customer: " + order.customer()
                + "\nSubtotal: " + totals.subtotal()
                + "\nVAT: " + totals.vat()
                + "\nTotal: " + totals.total();
    }
}
~~~

## Esercizio 30: separare calcolo e ricevuta

Obiettivo: Applicare SRP dividendo calcolo dei prezzi e formattazione.

**Completa `PriceCalculator.total` e `ReceiptFormatter.format`**.

- Il *calcolatore* restituisce prezzo × quantità, **senza costruire testi**.
- Il *formatter* riceve il totale già calcolato e restituisce `"Total: <totale> cents"`, **senza ricalcolarlo**.

Gli input sono non negativi.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
public class Exercise {

    public static class PriceCalculator {

        public int total(int price, int quantity) {
            // TODO: completa questo blocco.
            // Suggerimento: Questo oggetto fa solo il calcolo numerico: usa prezzo e quantità.
            return 0;
        }
    }

    public static class ReceiptFormatter {

        public String format(int total) {
            // TODO: completa questo blocco.
            // Suggerimento: Il totale è già calcolato: costruisci soltanto la stringa richiesta.
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

    public static class PriceCalculator {

        public int total(int price, int quantity) {
            return price * quantity;
        }
    }

    public static class ReceiptFormatter {

        public String format(int total) {
            return "Total: " + total + " cents";
        }
    }
}
~~~

Vogliamo separare due lavori diversi: calcolare il totale e trasformarlo nel testo della ricevuta.

`PriceCalculator.total` restituisce `price * quantity` e nient'altro. Non sa come verrà mostrato il numero. `ReceiptFormatter.format` riceve il totale già pronto e costruisce `"Total: " + total + " cents"`. Non sa da dove arrivi quel numero.

È il principio di responsabilità singola, la S di SOLID della lezione 30: una classe ha una sola ragione per cambiare. Prova il test della congiunzione "e": "calcola il totale e prepara la ricevuta" ha una "e" di troppo. Le richieste arrivano da persone diverse. Se il negozio vuole la ricevuta in euro con la virgola, tocchiamo solo il formatter. Se cambia la regola del prezzo, tocchiamo solo il calcolatore. Con un'unica classe, ogni modifica al testo rischierebbe di rompere il calcolo, e i test dell'uno e dell'altro non si potrebbero più fare separatamente.

Un errore tipico è far calcolare qualcosa anche al formatter, per esempio passandogli prezzo e quantità: cambieresti la firma di `format` e i test non compilerebbero più. Il test `formatsProvidedTotalWithoutRecalculation` gli passa direttamente `1257` e vuole esattamente `"Total: 1257 cents"`. Attenzione anche agli spazi: uno in meno o in più fa fallire `assertEquals`. Il test del calcolatore controlla anche il caso `quantity` zero, che deve dare `0`.

## Riepilogo

- Una classe, una sola ragione per cambiare
- Il test della "e" scopre le classi che fanno troppo
- Refactoring: cambia la struttura, l'output resta identico
