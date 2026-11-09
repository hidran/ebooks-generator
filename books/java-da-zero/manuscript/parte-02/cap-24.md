# Lezione 14. Enum e tipi sealed

## Punti chiave

### Enum: un insieme chiuso di valori

- enum OrderStatus { NEW, PAID, SHIPPED }
- Ogni valore è un oggetto unico: si confronta con ==
- values() restituisce tutti i valori
- Può avere campi e metodi, come una classe

> Percorso: NEW, poi PAID, poi SHIPPED.

### Sealed: un insieme chiuso di tipi

- sealed interface PaymentMethod permits CardPayment, CashPayment
- Solo i tipi elencati in permits possono implementarla
- Ogni tipo ammesso è final, sealed o non-sealed: i record sono già final
- Chi legge e il compilatore conoscono tutti i casi

### L'errore tipico

- record GiftCard(int cents) implements PaymentMethod
- Non compila: GiftCard non è elencato in permits
- javac: "is not listed in its 'permits' clause"
- Un nuovo caso si aggiunge modificando permits, in un punto solo

## Codice della lezione

`OrderStatus.java`

~~~java
public enum OrderStatus {
    NEW, PAID, SHIPPED;
    public boolean isFinal() {
        return this == SHIPPED;
    }
}
~~~

`PaymentMethod.java`

~~~java
public sealed interface PaymentMethod permits CardPayment, CashPayment {
    String describe();
}
~~~

`CardPayment.java`

~~~java
public record CardPayment(int cents, String last4) implements PaymentMethod {
    @Override
    public String describe() {
        return "Paid " + cents + " cents by card ending " + last4;
    }
}
~~~

`CashPayment.java`

~~~java
public record CashPayment(int cents) implements PaymentMethod {
    @Override
    public String describe() {
        return "Paid " + cents + " cents in cash";
    }
}
~~~

`Main.java`

~~~java
public class Main {
    public static void main(String[] args) {
        OrderStatus status = OrderStatus.PAID;
        String message = switch (status) {
            case NEW -> "Waiting for payment";
            case PAID -> "Ready to ship";
            case SHIPPED -> "On its way";
        };
        System.out.println(status + ": " + message);
        for (OrderStatus each : OrderStatus.values()) {
            System.out.println(each + " final? " + each.isFinal());
        }
        PaymentMethod card = new CardPayment(2500, "4242");
        PaymentMethod cash = new CashPayment(1200);
        System.out.println(card.describe());
        System.out.println(cash.describe());
    }
}
~~~

## Esercizio 14: stati ed esiti chiusi

Obiettivo: Gestire un enum e una gerarchia sealed senza casi imprevisti.

`OrderStatus` ha `NEW`, `PAID` e `SHIPPED`.

**Implementa `canShip`**: `true` *soltanto* per `PAID`.

`Payment` è *sealed*, ammette `Card` e `Cash` e dichiara il metodo `label()`.

**Implementa `label()`** nei due record **senza cambiare `permits`**:

- `Card` restituisce `"card"`,
- `Cash` restituisce `"cash"`.

Implementa poi **`paymentLabel`**, che restituisce l’etichetta del pagamento ricevuto chiamando `label()`.

Gli argomenti non sono `null`.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
public class Exercise {

    public enum OrderStatus {
        NEW,
        PAID,
        SHIPPED,
    }

    public sealed interface Payment permits Card, Cash {
        String label();
    }

    public record Card(String last4) implements Payment {
        @Override
        public String label() {
            // TODO: completa questo blocco.
            // Suggerimento: Restituisci l’etichetta di questo tipo di pagamento.
            // La stringa last4 non deve entrare nell’etichetta richiesta.
            return "";
        }
    }

    public record Cash() implements Payment {
        @Override
        public String label() {
            // TODO: completa questo blocco.
            // Suggerimento: Restituisci l’etichetta di questo tipo di pagamento.
            return "";
        }
    }

    public boolean canShip(OrderStatus status) {
        // TODO: completa questo blocco.
        // Suggerimento: I valori di un enum si possono confrontare con ==.
        return false;
    }

    public String paymentLabel(Payment payment) {
        // TODO: completa questo blocco.
        // Suggerimento: Ogni record di Payment sa già dare la propria etichetta con label().
        // Chiama il metodo sul pagamento ricevuto: Java sceglie la versione del record giusto.
        return "";
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
public class Exercise {

    public enum OrderStatus {
        NEW,
        PAID,
        SHIPPED,
    }

    public sealed interface Payment permits Card, Cash {
        String label();
    }

    public record Card(String last4) implements Payment {
        @Override
        public String label() {
            return "card";
        }
    }

    public record Cash() implements Payment {
        @Override
        public String label() {
            return "cash";
        }
    }

    public boolean canShip(OrderStatus status) {
        return status == OrderStatus.PAID;
    }

    public String paymentLabel(Payment payment) {
        return payment.label();
    }
}
~~~

L'obiettivo è lavorare con due insiemi chiusi: i valori di un enum e i tipi di una gerarchia sealed.

In `canShip` scriviamo `return status == OrderStatus.PAID;`. Come abbiamo visto nella lezione 14, ogni valore di un enum è un oggetto unico, quindi `==` è il confronto giusto. Il confronto stesso è già un `boolean`: non serve un `if` che restituisca `true` o `false`.

Per i pagamenti usiamo il polimorfismo della lezione 13, dentro un insieme chiuso. L'interfaccia `Payment` è `sealed` e dichiara `label()`. Ogni record la implementa a modo suo: `Card` restituisce `"card"`, `Cash` restituisce `"cash"`. Così `paymentLabel` si riduce a `return payment.label();`: a runtime parte la versione del record vero, senza controllare il tipo a mano. Poiché `permits` elenca solo `Card` e `Cash`, nessun altro tipo può comparire: se un giorno ne aggiungessimo uno, il compilatore ci obbligherebbe a scrivere anche la sua `label()`.

Un errore tipico in `canShip` è ragionare per esclusione, con `status != OrderStatus.NEW`. Sembra giusto, ma il test `shipsOnlyPaidOrders` prova tutti e tre i valori e si aspetta `false` anche per `SHIPPED`: un ordine già spedito non si spedisce di nuovo. Un altro errore è infilare le ultime cifre della carta nell'etichetta. Il test `handlesEveryPermittedType` passa `new Card("4242")` e si aspetta esattamente `"card"`, e `eachRecordKnowsItsOwnLabel` controlla `label()` direttamente su ciascun record.

## Riepilogo

- enum: insieme chiuso di valori, con metodi e values()
- switch su un enum: niente default se copre tutti i valori
- sealed e permits: insieme chiuso di tipi, record come implementazioni
