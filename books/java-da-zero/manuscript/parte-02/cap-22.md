# Lezione 13. Interfacce e polimorfismo

## Punti chiave

### Un if per ogni tipo

- Il cliente paga con la carta oppure in contanti
- Senza interfaccia: if (type.equals("card")) ... else if (type.equals("cash")) ...
- Ogni nuovo pagamento aggiunge un ramo
- Gli if sul tipo si spargono nel codice

### L'interfaccia: un contratto

- Dice che cosa si sa fare, non come
- interface PaymentMethod { String pay(int amountInCents); }
- class CardPayment implements PaymentMethod
- Non si istanzia: serve una classe che la implementa

### Polimorfismo: niente if sul tipo

- PaymentMethod method = new CardPayment("4242");
- Stessa chiamata, method.pay(amount): decide l'oggetto vero
- Nuovo pagamento: una nuova classe, checkout non cambia

> Percorso: checkout, poi PaymentMethod, poi CardPayment o CashPayment.

## Codice della lezione

`PaymentMethod.java`

~~~java
public interface PaymentMethod {
    String pay(int amountInCents);
}
~~~

`CardPayment.java`

~~~java
public class CardPayment implements PaymentMethod {
    private final String lastDigits;
    public CardPayment(String lastDigits) {
        this.lastDigits = lastDigits;
    }
    @Override
    public String pay(int amountInCents) {
        return "Paid " + amountInCents + " cents by card ending " + lastDigits;
    }
}
~~~

`CashPayment.java`

~~~java
public class CashPayment implements PaymentMethod {
    @Override
    public String pay(int amountInCents) {
        return "Paid " + amountInCents + " cents in cash";
    }
}
~~~

`Main.java`

~~~java
public class Main {
    public static void main(String[] args) {
        PaymentMethod method = new CardPayment("4242");
        System.out.println(method.pay(1250));
        method = new CashPayment();
        System.out.println(method.pay(1250));
        checkout(new CardPayment("1881"), 3000);
        checkout(new CashPayment(), 499);
    }
    static void checkout(PaymentMethod method, int amount) {
        System.out.println("Checkout: " + method.pay(amount));
    }
}
~~~

## Esercizio 13: checkout polimorfico

Obiettivo: Invocare un contratto senza distinguere le implementazioni con if.

`PaymentMethod` è un’interfaccia.

**Implementa `checkout(method, amountInCents)`**: restituisci il risultato di `method.pay` con l’importo ricevuto.

**Non creare** una nuova implementazione dentro `checkout` e **non usare `instanceof`**.

Gli importi sono positivi e `method` non è `null`.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
public class Exercise {

    public interface PaymentMethod {
        String pay(int amountInCents);
    }

    public String checkout(PaymentMethod method, int amountInCents) {
        // TODO: completa questo blocco.
        // Suggerimento: method è già un oggetto che rispetta PaymentMethod.
        // Chiama il suo metodo pay con amountInCents e restituisci il risultato.
        return "";
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
public class Exercise {

    public interface PaymentMethod {
        String pay(int amountInCents);
    }

    public String checkout(PaymentMethod method, int amountInCents) {
        return method.pay(amountInCents);
    }
}
~~~

Vogliamo che `checkout` incassi un importo con qualsiasi metodo di pagamento, senza sapere quale sia.

La soluzione è una sola riga: `return method.pay(amountInCents);`. Funziona perché il parametro ha il tipo dell'interfaccia `PaymentMethod`. Come abbiamo visto nella lezione 13, un'interfaccia è un contratto: promette che l'oggetto sa fare `pay`, ma non dice come. Quando chiamiamo `method.pay`, a decidere il comportamento è l'oggetto vero che riceviamo. Questo è il polimorfismo: stessa chiamata, risultati diversi. Il valore restituito da `pay` è già la stringa che ci serve, quindi lo passiamo indietro così com'è.

Nota che `checkout` non conosce nessuna classe concreta. Se domani arriva un nuovo modo di pagare, scriviamo una nuova classe che implementa `PaymentMethod`, e `checkout` resta identico.

L'errore più comune è voler aiutare il metodo: un `if` con `instanceof`, oppure una stringa costruita a mano come `"CARD:" + amountInCents`. Il primo test passerebbe, perché si aspetta proprio `"CARD:1200"`. Il secondo però usa un'implementazione che non hai mai visto: restituisce `"APPROVED"` e si annota l'importo ricevuto. Il test controlla che il risultato sia `"APPROVED"` e che l'importo arrivato sia `2700`. Solo una vera delega a `pay` li soddisfa entrambi.

Le implementazioni nei test sono scritte come lambda, un modo compatto di implementare un'interfaccia con un solo metodo. Le vedremo nella lezione 20.

## Riepilogo

- Interfaccia: un contratto, con implements e @Override
- Variabili e parametri con il tipo dell'interfaccia
- Polimorfismo: stessa chiamata, comportamenti diversi
