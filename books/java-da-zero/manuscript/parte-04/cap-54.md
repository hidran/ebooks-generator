# Lezione 35. Pattern essenziali, Strategy, Factory e Builder

## Punti chiave

### Pattern: un vocabolario comune

- Soluzioni collaudate a problemi che ritornano
- Un nome che tutti riconoscono: il codice si spiega in una parola
- Un vocabolario, non un obiettivo: prima il problema, poi il pattern
- Un pattern senza motivo è solo un livello in più (KISS)

### Strategy

- Una famiglia di algoritmi dietro la stessa interfaccia
- Si sceglie mentre il programma gira; il chiamante non cambia
- Java moderno: una lambda per ogni strategia (come Comparator)

> Percorso: checkout, poi ShippingStrategy, poi standard, express, promo.

### Factory method statico

- Un metodo statico al posto di new: PaymentMethod.of("card")
- Un nome che spiega, la classe concreta resta nascosta
- Tipo sconosciuto: IllegalArgumentException, subito
- Nel JDK: List.of, Path.of, LocalDate.of

### Builder

- Molti parametri facoltativi: un nome per ogni valore
- Java non ha parametri con nome né valori predefiniti
- build() controlla che l'oggetto sia completo
- Pochi parametri? Basta il costruttore del record (KISS)

## Codice della lezione

`Shipping.java`

~~~java
public class Shipping {
    @FunctionalInterface
    interface ShippingStrategy {
        int cost(int totalInCents);
    }
    static int checkout(int totalInCents, ShippingStrategy strategy) {
        return totalInCents + strategy.cost(totalInCents);
    }
    public static void main(String[] args) {
        ShippingStrategy standard = total -> 500;
        ShippingStrategy express = total -> 1200;
        ShippingStrategy promo = total -> total >= 5000 ? 0 : 500;
        System.out.println("Standard: " + checkout(4000, standard));
        System.out.println("Express: " + checkout(4000, express));
        System.out.println("Promo: " + checkout(6000, promo));
    }
}
~~~

`Payments.java`

~~~java
public class Payments {
    interface PaymentMethod {
        String pay(int cents);
        static PaymentMethod of(String type) {
            return switch (type) {
                case "card" -> new CardPayment();
                case "cash" -> new CashPayment();
                default -> throw new IllegalArgumentException(
                        "Unknown payment: " + type);
            };
        }
    }
    private static class CardPayment implements PaymentMethod {
        @Override
        public String pay(int cents) {
            return "Card charged " + cents;
        }
    }
    private static class CashPayment implements PaymentMethod {
        @Override
        public String pay(int cents) {
            return "Cash received " + cents;
        }
    }
    public static void main(String[] args) {
        PaymentMethod card = PaymentMethod.of("card");
        System.out.println(card.pay(2500));
        System.out.println(PaymentMethod.of("cash").pay(1200));
        try {
            PaymentMethod.of("crypto");
        } catch (IllegalArgumentException e) {
            System.out.println("Error: " + e.getMessage());
        }
    }
}
~~~

`Order.java`

~~~java
import java.util.ArrayList;
import java.util.List;
public record Order(String customer, List<String> lines, String coupon,
        boolean gift) {
    public static Builder builder() {
        return new Builder();
    }
    public static class Builder {
        private String customer;
        private final List<String> lines = new ArrayList<>();
        private String coupon = "none";
        private boolean gift;
        public Builder customer(String customer) {
            this.customer = customer;
            return this;
        }
        public Builder line(String product) {
            lines.add(product);
            return this;
        }
        public Builder coupon(String coupon) {
            this.coupon = coupon;
            return this;
        }
        public Builder gift() {
            gift = true;
            return this;
        }
        public Order build() {
            if (customer == null || lines.isEmpty()) {
                throw new IllegalStateException("Incomplete order");
            }
            return new Order(customer, List.copyOf(lines), coupon, gift);
        }
    }
    public static void main(String[] args) {
        Order plain = new Order("Marco", List.of("Book"), "none", false);
        Order built = Order.builder()
                .customer("Anna")
                .line("Pen")
                .line("Coffee")
                .coupon("WELCOME10")
                .gift()
                .build();
        System.out.println(plain);
        System.out.println(built);
    }
}
~~~

## Esercizio 35: scegliere una Strategy con Factory

Obiettivo: Creare strategie tramite una factory semplice senza modificare il chiamante.

**Implementa `shipping(type)`**:

- per `"standard"` restituisci una strategia che costa `490` sotto `5000` e `0` da `5000` in su;
- per `"express"` una strategia che costa sempre `990`.

Qualsiasi altro nome, incluso `null`, causa `IllegalArgumentException`.

La factory restituisce **`ShippingStrategy`**, non il costo.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
public class Exercise {

    public interface ShippingStrategy {
        int cost(int totalInCents);
    }

    public ShippingStrategy shipping(String type) {
        // TODO: completa questo blocco.
        // Suggerimento: Questo metodo restituisce un oggetto ShippingStrategy: una lambda può implementare cost.
        // Distingui qui il nome con if ("standard".equals(type)) e if ("express".equals(type)): equals su un letterale funziona anche con type null.
        // La soglia del totale va valutata nella lambda; alla fine lancia IllegalArgumentException per ogni altro nome.
        return totalInCents -> 0;
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
public class Exercise {

    public interface ShippingStrategy {
        int cost(int totalInCents);
    }

    public ShippingStrategy shipping(String type) {
        if ("standard".equals(type)) {
            return total -> total >= 5000 ? 0 : 490;
        }
        if ("express".equals(type)) {
            return total -> 990;
        }
        throw new IllegalArgumentException("Unknown shipping");
    }
}
~~~

Vogliamo una factory che, dato un nome, restituisce la strategia di spedizione giusta.

La soluzione usa due `if` in fila. Il primo confronta con `"standard".equals(type)` e restituisce la lambda `total -> total >= 5000 ? 0 : 490`. Il secondo confronta con `"express".equals(type)` e restituisce `total -> 990`. Se nessuno dei due scatta, l'ultima riga lancia `IllegalArgumentException`. Scrivere il letterale a sinistra è il dettaglio che conta: `"standard".equals(null)` vale semplicemente `false`, mentre `type.equals("standard")` con `type` nullo lancerebbe `NullPointerException`. Grazie a questo, `null` e `"drone"` finiscono nello stesso ramo finale e non servono controlli separati.

Qui lavorano insieme i due pattern della lezione 35. La Strategy è l'interfaccia `ShippingStrategy`: una famiglia di algoritmi intercambiabili, ognuno scritto come lambda, come facevamo con `Comparator`. La Factory nasconde la scelta: il chiamante chiede un nome e riceve un oggetto, senza sapere quale lambda c'è dietro. Senza la factory, ogni chiamante dovrebbe ripetere la stessa scelta, e una nuova tariffa vorrebbe dire modificarli tutti. La factory decide quale strategia, la soglia dei 5000 centesimi la valuta la strategia quando viene usata.

Un errore tipico è sbagliare il confine: con `total > 5000`, il test `standardUsesThreshold` riceverebbe `490` invece di `0` per `cost(5000)`. Un altro è usare `type.equals(...)`: con `null` arriva una `NullPointerException` e `factoryRejectsUnknownTypes` fallisce. Lo stesso test pretende un'eccezione anche per `"Standard"` e `"EXPRESS"`: i nomi distinguono maiuscole e minuscole, quindi `equalsIgnoreCase` non va bene.

## Riepilogo

- Strategy: algoritmi intercambiabili, spesso una lambda
- Factory statico: of nasconde new e la scelta della classe
- Builder: valori con nome quando i parametri sono tanti
