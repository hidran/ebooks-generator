# Lezione 34. D, dipendere da astrazioni

## Punti chiave

### Un new dentro il servizio

- OrderService crea da solo new StripePayment()
- La regola del negozio dipende da un dettaglio tecnico
- Cambiare fornitore significa modificare il servizio
- Ogni prova addebita davvero

> Percorso: OrderService, poi StripePayment.

### Dipendere da astrazioni

- L'alto livello non dipende dal basso livello
- Entrambi dipendono da un'astrazione
- L'astrazione la decide chi la usa: PaymentGateway

> Percorso: OrderService, poi PaymentGateway, poi StripePayment o FakePayment.

### Inversione e iniezione

- Inversione: il principio, le dipendenze puntano alle astrazioni
- Iniezione: la tecnica, l'oggetto arriva dal costruttore
- Campo final: il servizio nasce completo
- Main come composition root (dalla sezione 5 lo farà Spring)

### Quando serve un'interfaccia

- Ai confini: pagamenti, email, database, orologio
- Dove serve un sostituto per le prove
- Non davanti a ogni classe: KISS
- Una sola implementazione per sempre? Forse non serve

## Codice della lezione

`StripePayment.java`

~~~java
public class StripePayment implements PaymentGateway {
    @Override
    public void charge(int amountInCents) {
        System.out.println("charged " + amountInCents + " cents via Stripe");
    }
}
~~~

`before/StripePayment.java`

~~~java
public class StripePayment {
    public void charge(int amountInCents) {
        System.out.println("charged " + amountInCents + " cents via Stripe");
    }
}
~~~

`OrderService.java`

~~~java
public class OrderService {
    private final PaymentGateway payment;
    public OrderService(PaymentGateway payment) {
        this.payment = payment;
    }
    public void placeOrder(String orderId, int amountInCents) {
        int shipping = amountInCents < 2000 ? 500 : 0;
        payment.charge(amountInCents + shipping);
        System.out.println("order " + orderId + " placed");
    }
}
~~~

`before/OrderService.java`

~~~java
public class OrderService {
    private final StripePayment payment = new StripePayment();
    public void placeOrder(String orderId, int amountInCents) {
        int shipping = amountInCents < 2000 ? 500 : 0;
        payment.charge(amountInCents + shipping);
        System.out.println("order " + orderId + " placed");
    }
}
~~~

`PaymentGateway.java`

~~~java
public interface PaymentGateway {
    void charge(int amountInCents);
}
~~~

`FakePayment.java`

~~~java
import java.util.ArrayList;
import java.util.List;
public class FakePayment implements PaymentGateway {
    private final List<Integer> charges = new ArrayList<>();
    @Override
    public void charge(int amountInCents) {
        charges.add(amountInCents);
    }
    public List<Integer> charges() {
        return List.copyOf(charges);
    }
}
~~~

`Main.java`

~~~java
public class Main {
    public static void main(String[] args) {
        OrderService shop = new OrderService(new StripePayment());
        shop.placeOrder("A-1", 2500);
        FakePayment fake = new FakePayment();
        OrderService tested = new OrderService(fake);
        tested.placeOrder("T-1", 1200);
        tested.placeOrder("T-2", 3000);
        System.out.println("fake charges: " + fake.charges());
    }
}
~~~

## Esercizio 34: iniettare il gateway

Obiettivo: Applicare DIP e testare un servizio senza chiamare sistemi reali.

**Completa `OrderService.checkout(amountInCents)`**:

1. valida che l’importo sia positivo,
2. poi invoca **esattamente una volta** `gateway.charge`.

Restituisci il risultato del gateway, anche quando è `false`.

Per importi non validi lancia `IllegalArgumentException` **senza chiamare** `gateway`.

La dipendenza è già iniettata dal costruttore.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
public class Exercise {

    public interface PaymentGateway {
        boolean charge(int amountInCents);
    }

    public static class OrderService {

        private final PaymentGateway gateway;

        public OrderService(PaymentGateway gateway) {
            this.gateway = gateway;
        }

        public boolean checkout(int amountInCents) {
            // TODO: completa questo blocco.
            // Suggerimento: Controlla l’importo prima di usare gateway: i valori non positivi vanno rifiutati.
            // Per l’importo valido restituisci direttamente gateway.charge, senza una seconda chiamata.
            return false;
        }
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
public class Exercise {

    public interface PaymentGateway {
        boolean charge(int amountInCents);
    }

    public static class OrderService {

        private final PaymentGateway gateway;

        public OrderService(PaymentGateway gateway) {
            this.gateway = gateway;
        }

        public boolean checkout(int amountInCents) {
            if (amountInCents <= 0) {
                throw new IllegalArgumentException("Amount must be positive");
            }
            return gateway.charge(amountInCents);
        }
    }
}
~~~

Vogliamo un servizio d'ordine che valida l'importo e addebita tramite un gateway che riceve dall'esterno.

In `checkout` controlliamo per prima cosa `amountInCents <= 0` e, in quel caso, lanciamo `IllegalArgumentException`. Il gateway non viene nemmeno toccato. Poi restituiamo direttamente `gateway.charge(amountInCents)`: una chiamata sola, e il suo risultato passa così com'è, anche quando è `false`.

È il principio di inversione delle dipendenze, la D di SOLID della lezione 34. `OrderService` dipende dall'astrazione `PaymentGateway`, decisa da chi la usa, e la riceve dal costruttore in un campo `final`. Senza questo principio avremmo un `new StripePayment()` dentro il servizio. Cambiare fornitore vorrebbe dire modificare il servizio, e ogni prova addebiterebbe soldi veri. Grazie all'iniezione, nei test basta una lambda che conta le chiamate.

Un errore tipico è chiamare il gateway due volte, per esempio `if (gateway.charge(a)) return true;` seguito da un'altra chiamata. Il test `delegatesExactlyOnceWithCorrectAmount` conta le chiamate e vuole esattamente `1`, con importo `1500`. Un altro è restituire sempre `true` dopo l'addebito: `preservesDeclinedPayment` usa un gateway che rifiuta e si aspetta `false`. Infine, se validi dopo aver chiamato il gateway, `rejectsInvalidAmountBeforeExternalCall` trova una chiamata invece di zero.

Nella sezione su Spring vedremo che sarà il framework a fare l'iniezione al posto nostro.

## Riepilogo

- Alto e basso livello dipendono da un'astrazione
- La dipendenza arriva dal costruttore, in un campo final
- Main compone gli oggetti: iniezione fatta a mano
