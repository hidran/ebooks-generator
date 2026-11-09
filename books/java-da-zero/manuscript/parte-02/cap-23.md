# Lezione 13b. Classi astratte, metodi default e static

## Punti chiave

### Una classe a metà

- CardPayment e CashPayment: stesso importo, costruttore e ricevuta
- Un'interfaccia non ha campi né costruttori
- Serve una classe madre da estendere, ma non da istanziare

> Percorso: Payment, poi CardPayment o CashPayment.

### Classi e metodi astratti

- abstract class Payment: new Payment(...) non compila
- Metodo astratto, solo la firma: abstract int fee();
- Ogni sottoclasse concreta deve implementarlo
- Campi, costruttore e metodi completi restano possibili

### Classe astratta o interfaccia

- Classe astratta: stato e codice comuni a classi parenti
- Interfaccia: una capacità, con metodi default e static, senza stato
- Si estende una sola classe, si implementano molte interfacce
- Nel dubbio, prima l'interfaccia

### Chiudere con final

- Campo final: il valore non cambia (lezione 10)
- Metodo final: nessuna sottoclasse lo ridefinisce, come receipt
- Classe final: nessuno la estende, come CardPayment e String

## Codice della lezione

`Main.java`, versione con un errore voluto: non compila o il test fallisce, per leggere il messaggio

~~~java
public class Main {
    public static void main(String[] args) {
        Payment payment = new Payment(2500);
    }
}
~~~

`Main.java`, prima versione

~~~java
public class Main {
    public static void main(String[] args) {
        Payment[] payments = {new CardPayment(2500), new CashPayment(2500)};
        for (Payment payment : payments) {
            System.out.println(payment.receipt());
        }
    }
}
~~~

`Main.java`

~~~java
public class Main {
    public static void main(String[] args) {
        Payment[] payments = {new CardPayment(2500), new CashPayment(2500)};
        for (Payment payment : payments) {
            System.out.println(payment.receipt());
        }
        Discount sale = new SummerSale();
        Payment discounted = new CardPayment(sale.apply(2500));
        System.out.println(discounted.receipt());
        System.out.println("Saving: " + sale.saving(2500));
    }
}
~~~

`Payment.java`

~~~java
public abstract class Payment {
    private final int amountInCents;
    public Payment(int amountInCents) {
        this.amountInCents = amountInCents;
    }
    public int getAmountInCents() {
        return amountInCents;
    }
    public abstract int fee();
    public final String receipt() {
        return "Paid " + (amountInCents + fee()) + " cents, fee " + fee();
    }
}
~~~

`CardPayment.java`

~~~java
public final class CardPayment extends Payment {
    public CardPayment(int amountInCents) {
        super(amountInCents);
    }
    @Override
    public int fee() {
        return getAmountInCents() * 2 / 100;
    }
}
~~~

`CashPayment.java`

~~~java
public class CashPayment extends Payment {
    public CashPayment(int amountInCents) {
        super(amountInCents);
    }
    @Override
    public int fee() {
        return 0;
    }
}
~~~

`Discount.java`

~~~java
public interface Discount {
    int apply(int priceInCents);
    default int saving(int priceInCents) {
        return priceInCents - apply(priceInCents);
    }
    static int percentOf(int priceInCents, int percent) {
        return priceInCents * percent / 100;
    }
}
~~~

`SummerSale.java`

~~~java
public class SummerSale implements Discount {
    @Override
    public int apply(int priceInCents) {
        return priceInCents - Discount.percentOf(priceInCents, 20);
    }
}
~~~

## Esercizio 13b: completare una classe astratta

Obiettivo: Specializzare un comportamento astratto riusando il codice comune.

`Payment` contiene importo e `receipt()` *final* già pronti.

1. **Implementa `fee()` di `CardPayment`**: commissione pari al `2%` dell’importo con *divisione intera*.
2. In **`CashPayment`** la commissione è **zero**.

**Non riscrivere** `receipt` e **non cambiare la gerarchia**.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
public class Exercise {

    public abstract static class Payment {

        private final int amountInCents;

        public Payment(int amountInCents) {
            this.amountInCents = amountInCents;
        }

        public int getAmountInCents() {
            return amountInCents;
        }

        public abstract int fee();

        public final String receipt() {
            return "Total: " + (amountInCents + fee());
        }
    }

    public static final class CardPayment extends Payment {

        public CardPayment(int amountInCents) {
            super(amountInCents);
        }

        @Override
        public int fee() {
            // TODO: completa questo blocco.
            // Suggerimento: Leggi l’importo con il metodo getAmountInCents() ereditato da Payment.
            // Calcola la percentuale con interi: moltiplica prima, dividi dopo.
            return 0;
        }
    }

    public static final class CashPayment extends Payment {

        public CashPayment(int amountInCents) {
            super(amountInCents);
        }

        @Override
        public int fee() {
            // TODO: completa questo blocco.
            // Suggerimento: Per i contanti non ci sono commissioni: sostituisci il -1 provvisorio con la commissione giusta.
            return -1;
        }
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
public class Exercise {

    public abstract static class Payment {

        private final int amountInCents;

        public Payment(int amountInCents) {
            this.amountInCents = amountInCents;
        }

        public int getAmountInCents() {
            return amountInCents;
        }

        public abstract int fee();

        public final String receipt() {
            return "Total: " + (amountInCents + fee());
        }
    }

    public static final class CardPayment extends Payment {

        public CardPayment(int amountInCents) {
            super(amountInCents);
        }

        @Override
        public int fee() {
            return getAmountInCents() * 2 / 100;
        }
    }

    public static final class CashPayment extends Payment {

        public CashPayment(int amountInCents) {
            super(amountInCents);
        }

        @Override
        public int fee() {
            return 0;
        }
    }
}
~~~

Dobbiamo completare le due sottoclassi di `Payment`, scrivendo soltanto la commissione di ciascuna.

In `CardPayment`, `fee()` restituisce `getAmountInCents() * 2 / 100`. Il campo `amountInCents` è `private` nella classe madre, quindi la figlia lo legge con il getter pubblico, come nella lezione. L'ordine delle operazioni conta: moltiplichiamo prima e dividiamo dopo. Come abbiamo visto nella lezione 4, una divisione fra interi tronca la parte decimale. In `CashPayment`, `fee()` restituisce semplicemente `0`.

Non tocchiamo `receipt()`. Come abbiamo visto nella lezione 13b, `Payment` è astratta perché ha codice comune ma un pezzo mancante: il metodo `abstract int fee()`. La ricevuta è `final`, quindi nessuna figlia la può ridefinire, e al suo interno chiama `fee()`. Durante l'esecuzione parte la versione della sottoclasse vera. Così, con 1500 centesimi, la carta produce `"Total: 1530"` e i contanti `"Total: 1500"`, con lo stesso codice.

Un errore tipico è dividere prima: `amountInCents / 100 * 2`. Con 1500 dà ancora 30, ma il test `truncatesFractionalCent` usa 99 centesimi. `99 / 100` vale 0, e la commissione diventa 0 invece di `1`. Un altro errore è scrivere `amountInCents * 0.02`: il risultato è un `double`, e il metodo non compila senza un cast.

Anche con le parentesi, `(getAmountInCents() * 2) / 100`, il risultato è lo stesso: Java calcola da sinistra a destra, quindi la moltiplicazione avviene comunque per prima.

## Riepilogo

- Classe astratta: non si istanzia, le figlie completano i metodi abstract
- Interfaccia: default già pronti, static di supporto, niente stato
- final chiude un metodo o una classe
