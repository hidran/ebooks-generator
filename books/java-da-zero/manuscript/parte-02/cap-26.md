# Lezione 16. Eccezioni e strategia degli errori

## Punti chiave

### Che cos'è un'eccezione

- Un oggetto che segnala un problema durante l'esecuzione
- throw la lancia: il flusso normale si interrompe
- Risale le chiamate finché un catch la cattura
- Nessun catch: il programma si ferma con una stack trace

> Percorso: throw, poi risale le chiamate, poi catch.

### Leggere una stack trace

- Exception in thread "main" InsufficientFundsException: Balance 700, requested 900
- at Wallet.withdraw(Wallet.java:15)
- at Main.main(Main.java:7)
- Si legge dall'alto: dove è nata, poi chi l'ha chiamata

### Checked e unchecked

- Unchecked: estendono RuntimeException, il catch è facoltativo
- Checked: estendono Exception, per esempio IOException
- Le checked vanno catturate o dichiarate con throws
- Eccezioni di dominio: di solito unchecked

### Eccezioni per i casi eccezionali

- Non al posto di un if nel flusso normale
- Bug (IllegalArgumentException): si corregge il codice
- Errore recuperabile: si cattura dove si può reagire
- Mai un catch vuoto; per file e connessioni: try-with-resources

## Codice della lezione

`InsufficientFundsException.java`

~~~java
public class InsufficientFundsException extends RuntimeException {
    public InsufficientFundsException(String message) {
        super(message);
    }
}
~~~

`Wallet.java`

~~~java
public class Wallet {
    private int balanceInCents;
    public Wallet(int balanceInCents) {
        this.balanceInCents = balanceInCents;
    }
    public int getBalanceInCents() {
        return balanceInCents;
    }
    public void withdraw(int amountInCents) {
        if (amountInCents <= 0) {
            throw new IllegalArgumentException("Amount must be positive");
        }
        if (amountInCents > balanceInCents) {
            String message = "Balance " + balanceInCents + ", requested " + amountInCents;
            throw new InsufficientFundsException(message);
        }
        balanceInCents -= amountInCents;
    }
}
~~~

`Main.java`

~~~java
public class Main {
    public static void main(String[] args) {
        Wallet wallet = new Wallet(1000);
        try {
            wallet.withdraw(300);
            System.out.println("Withdrawn 300, balance " + wallet.getBalanceInCents());
            wallet.withdraw(900);
            System.out.println("Withdrawn 900");
        } catch (InsufficientFundsException e) {
            System.out.println("Payment refused: " + e.getMessage());
        } finally {
            System.out.println("Final balance " + wallet.getBalanceInCents());
        }
        System.out.println("Goodbye");
    }
}
~~~

## Esercizio 16: prelievi e errori di dominio

Obiettivo: Lanciare eccezioni appropriate mantenendo lo stato valido dopo un errore.

`Exercise` rappresenta un portafoglio inizializzato con saldo non negativo.

**Implementa `withdraw(amount)`**:

- un importo minore di `1` causa `IllegalArgumentException`;
- un importo superiore al saldo causa `InsufficientFundsException`;
- altrimenti sottrai l’importo.

Un errore **non deve cambiare il saldo**.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
public class Exercise {

    public static class InsufficientFundsException extends RuntimeException {

        public InsufficientFundsException(String message) {
            super(message);
        }
    }

    private int balance;

    public Exercise(int balance) {
        this.balance = balance;
    }

    public int balance() {
        return balance;
    }

    public void withdraw(int amount) {
        // TODO: completa questo blocco.
        // Suggerimento: Controlla prima amount < 1, poi confronta l’importo con balance.
        // Lancia l’eccezione richiesta per ciascun errore e aggiorna balance solo dopo i controlli.
        // Il metodo è void: non deve restituire il nuovo saldo.
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
public class Exercise {

    public static class InsufficientFundsException extends RuntimeException {

        public InsufficientFundsException(String message) {
            super(message);
        }
    }

    private int balance;

    public Exercise(int balance) {
        this.balance = balance;
    }

    public int balance() {
        return balance;
    }

    public void withdraw(int amount) {
        if (amount <= 0) {
            throw new IllegalArgumentException("Amount must be positive");
        }
        if (amount > balance) {
            throw new InsufficientFundsException("Insufficient funds");
        }
        balance -= amount;
    }
}
~~~

Il metodo `withdraw` deve prelevare dal saldo, ma rifiutare le richieste sbagliate lasciando il portafoglio intatto.

La soluzione fa due controlli e solo alla fine modifica lo stato. Il primo, `if (amount <= 0)`, equivale a "minore di 1" per un `int` e lancia `IllegalArgumentException`. Come abbiamo visto nella lezione 16, questa eccezione segnala un errore di chi chiama: prelevare zero o un importo negativo non ha senso. Il secondo, `if (amount > balance)`, lancia la nostra `InsufficientFundsException`, un'eccezione di dominio. Estende `RuntimeException`, quindi è unchecked e il metodo non deve dichiararla con `throws`. Solo se entrambi i controlli passano arriviamo a `balance -= amount`.

L'ordine è il cuore dell'esercizio. `throw` interrompe subito il metodo, quindi dopo un errore la sottrazione non avviene mai. Il confronto usa `>` e non `>=`: prelevare tutto il saldo è permesso.

Il primo errore tipico è sottrarre prima e controllare dopo. Il saldo cambierebbe anche in caso di errore, e i test se ne accorgono: dopo `withdraw(701)` su un saldo di 700, `reportsInsufficientFundsWithoutMutation` controlla che il saldo valga ancora `700`. Lo stesso vale per `withdraw(0)` e `withdraw(-1)`. Il secondo errore è usare `>=` nel controllo dei fondi. Il test `withdrawsAndAcceptsExactBalance` preleva prima 200 e poi esattamente i 500 rimasti, e si aspetta un saldo di `0`, non un'eccezione.

## Riepilogo

- try, catch e finally: tentativo, reazione, lavoro finale
- Eccezione di dominio: nome chiaro, messaggio con i dati
- Checked e unchecked; eccezioni solo per i casi eccezionali
