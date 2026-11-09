# Lezione 15. Pattern matching con instanceof, switch e record pattern

## Punti chiave

### instanceof senza cast

- Prima: method instanceof CardPayment, poi il cast (CardPayment) method
- Ora: if (method instanceof CardPayment card)
- card esiste solo se il controllo riesce, con il tipo giusto
- Niente cast, niente tipo ripetuto

### switch sui tipi e record pattern

- case CardPayment card -&gt; ...: un case per ogni tipo
- Tipo sealed: switch esaustivo, senza default
- case CardPayment(String last4) -&gt; ...: componenti estratti subito
- when aggiunge una condizione al case

### Due errori tipici

- Case con when dopo il case generale dello stesso tipo: non compila
- I casi più specifici vanno per primi
- default su un tipo sealed: spegne il controllo di esaustività
- Un tipo nuovo finirebbe in silenzio nel default

## Codice della lezione

`Receipt.java`, passaggio intermedio («instanceof»)

~~~java
public class Receipt {
    public static void main(String[] args) {
        System.out.println(describe(new CardPayment("4242")));
        System.out.println(describe(new CashPayment(2000)));
        System.out.println(describe(new CashPayment(5000)));
    }
    static String describe(PaymentMethod method) {
        if (method instanceof CardPayment card) {
            return "Card ending in " + card.last4();
        }
        if (method instanceof CashPayment cash) {
            return "Cash: " + cash.givenInCents();
        }
        return "Unknown payment";
    }
}
~~~

`Receipt.java`, passaggio intermedio («switch»)

~~~java
public class Receipt {
    public static void main(String[] args) {
        System.out.println(describe(new CardPayment("4242")));
        System.out.println(describe(new CashPayment(2000)));
        System.out.println(describe(new CashPayment(5000)));
    }
    static String describe(PaymentMethod method) {
        return switch (method) {
            case CardPayment card -> "Card ending in " + card.last4();
            case CashPayment cash -> "Cash: " + cash.givenInCents();
        };
    }
}
~~~

`Receipt.java`

~~~java
public class Receipt {
    public static void main(String[] args) {
        System.out.println(describe(new CardPayment("4242")));
        System.out.println(describe(new CashPayment(2000)));
        System.out.println(describe(new CashPayment(5000)));
    }
    static String describe(PaymentMethod method) {
        return switch (method) {
            case CardPayment(String last4) -> "Card ending in " + last4;
            case CashPayment(int cents) when cents >= 5000 -> "Check " + cents;
            case CashPayment(int cents) -> "Cash: " + cents;
        };
    }
}
~~~

`PaymentMethod.java`

~~~java
public sealed interface PaymentMethod permits CardPayment, CashPayment {
}
~~~

`CardPayment.java`

~~~java
public record CardPayment(String last4) implements PaymentMethod {
}
~~~

`CashPayment.java`

~~~java
public record CashPayment(int givenInCents) implements PaymentMethod {
}
~~~

## Esercizio 15: pattern matching negli esiti

Obiettivo: Usare record pattern e switch esaustivo con un caso specifico prima di quello generale.

**Implementa `label(Result)`**:

- `Success` con `amountInCents` almeno `10000` restituisce `"large:<importo>"`;
- gli altri `Success` restituiscono `"ok:<importo>"`;
- `Failure` restituisce `"error:<motivo>"`.

Usa **`switch`, record pattern e una guardia `when`**, **senza `default`**.

Gli argomenti non sono `null`.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
public class Exercise {

    public sealed interface Result permits Success, Failure {}

    public record Success(int amountInCents) implements Result {}

    public record Failure(String reason) implements Result {}

    public String label(Result result) {
        // TODO: completa questo blocco.
        // Suggerimento: Scrivi uno switch che restituisce un valore, con un case per ciascun record.
        // Metti il caso Success con guardia when prima del caso Success generale.
        // Il record pattern estrae importo o motivo in una variabile da usare nel testo.
        return "";
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
public class Exercise {

    public sealed interface Result permits Success, Failure {}

    public record Success(int amountInCents) implements Result {}

    public record Failure(String reason) implements Result {}

    public String label(Result result) {
        return switch (result) {
            case Success(int amount) when amount >= 10000 -> "large:" + amount;
            case Success(int amount) -> "ok:" + amount;
            case Failure(String reason) -> "error:" + reason;
        };
    }
}
~~~

Vogliamo trasformare un `Result` in un'etichetta, distinguendo i pagamenti grandi da quelli normali.

Lo switch ha tre `case`, e il loro ordine è la parte importante. Il primo è `case Success(int amount) when amount >= 10000`. Come abbiamo visto nella lezione 15, il record pattern controlla il tipo ed estrae subito la componente nella variabile `amount`; la guardia `when` aggiunge una condizione. Il secondo, `case Success(int amount)`, raccoglie tutti gli altri successi. Il terzo, `case Failure(String reason)`, estrae il motivo. Ogni ramo concatena il prefisso con il valore estratto.

Il caso specifico viene prima di quello generale perché lo switch prova i `case` dall'alto. Se li invertissimo, il caso generale catturerebbe ogni `Success`, e il compilatore se ne accorge: il codice non compila. Non serve nemmeno `default`, perché `Result` è sealed e i tre `case` coprono tutte le possibilità. Anzi, un `default` spegnerebbe il controllo di esaustività.

L'errore più facile riguarda la soglia. "Almeno 10000" vuol dire `>=`, non `>`. Con `>`, il test `putsSpecificCaseBeforeGeneral` riceverebbe `"ok:10000"` invece di `"large:10000"`. Lo stesso test controlla il valore vicino, `9999`, che deve dare `"ok:9999"`, e `handlesZeroAmount` verifica che `Success(0)` dia `"ok:0"`. Un altro errore è restituire solo il prefisso, `"large:"`, dimenticando l'importo: tutte le stringhe attese contengono anche il valore estratto.

## Riepilogo

- instanceof con variabile di pattern: niente cast
- switch su un tipo sealed: esaustivo, senza default
- Record pattern e when: componenti e condizioni nel case
