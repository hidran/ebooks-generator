# Lezione 29. KISS e DRY con un refactoring reale

## Punti chiave

### DRY: non ripeterti

- Ogni conoscenza ha un'unica rappresentazione
- Formule, regole e soglie scritte in un posto solo
- Tre copie della stessa regola: prima o poi una resta indietro

> Percorso: tre copie della formula, poi discounted(), poi un solo punto da cambiare.

### KISS: la soluzione più semplice che funziona

- Il codice complicato non è più potente: è più fragile
- Segnali: if annidati, flag, condizioni ripetute
- Rimedio: return anticipati, un caso per riga

### Quando non unificare

- Falsa duplicazione: codice uguale per caso, regole diverse
- price &gt; 0 e quantity &gt; 0: oggi uguali, domani no
- Astrazione prematura: interfacce e gerarchie per una riga
- Regola del tre, poi la forma più semplice: un metodo

## Codice della lezione

`Checkout.java`, prima del refactoring

~~~java
public class Checkout {
    public static void main(String[] args) {
        int coffee = 1200;
        int coffeeOnSale = coffee - coffee * 10 / 100;
        System.out.println("Coffee beans: " + coffeeOnSale);
        int book = 3000;
        int bookOnSale = book - book * 20 / 100;
        System.out.println("Java book: " + bookOnSale);
        int cart = coffeeOnSale + bookOnSale;
        System.out.println("Cart: " + cart);
        System.out.println("Member pays: " + total(cart, true));
        System.out.println("Guest pays: " + total(cart, false));
    }
    static int total(int cartInCents, boolean member) {
        int result = 0;
        boolean shipping = true;
        if (member) {
            result = cartInCents - cartInCents * 5 / 100;
            shipping = false;
        } else {
            if (cartInCents >= 5000) {
                result = cartInCents;
                shipping = false;
            } else {
                result = cartInCents;
            }
        }
        if (shipping == true) {
            result = result + 490;
        }
        return result;
    }
}
~~~

`Checkout.java`, passaggio intermedio («dry»)

~~~java
public class Checkout {
    public static void main(String[] args) {
        int coffeeOnSale = discounted(1200, 10);
        System.out.println("Coffee beans: " + coffeeOnSale);
        int bookOnSale = discounted(3000, 20);
        System.out.println("Java book: " + bookOnSale);
        int cart = coffeeOnSale + bookOnSale;
        System.out.println("Cart: " + cart);
        System.out.println("Member pays: " + total(cart, true));
        System.out.println("Guest pays: " + total(cart, false));
    }
    static int discounted(int priceInCents, int percent) {
        return priceInCents - priceInCents * percent / 100;
    }
    static int total(int cartInCents, boolean member) {
        int result = 0;
        boolean shipping = true;
        if (member) {
            result = cartInCents - cartInCents * 5 / 100;
            shipping = false;
        } else {
            if (cartInCents >= 5000) {
                result = cartInCents;
                shipping = false;
            } else {
                result = cartInCents;
            }
        }
        if (shipping == true) {
            result = result + 490;
        }
        return result;
    }
}
~~~

`Checkout.java`

~~~java
public class Checkout {
    public static void main(String[] args) {
        int coffeeOnSale = discounted(1200, 10);
        System.out.println("Coffee beans: " + coffeeOnSale);
        int bookOnSale = discounted(3000, 20);
        System.out.println("Java book: " + bookOnSale);
        int cart = coffeeOnSale + bookOnSale;
        System.out.println("Cart: " + cart);
        System.out.println("Member pays: " + total(cart, true));
        System.out.println("Guest pays: " + total(cart, false));
    }
    static int discounted(int priceInCents, int percent) {
        return priceInCents - priceInCents * percent / 100;
    }
    static int total(int cartInCents, boolean member) {
        if (member) {
            return discounted(cartInCents, 5);
        }
        if (cartInCents >= 5000) {
            return cartInCents;
        }
        return cartInCents + 490;
    }
}
~~~

## Esercizio 29: refactoring KISS e DRY

Obiettivo: Riunire una regola di sconto e usare ritorni anticipati mantenendo il comportamento.

1. **Implementa `discounted(priceInCents, percent)`**: restituisci il prezzo meno lo sconto calcolato con *divisione intera*.
2. **Implementa `checkout(priceInCents, quantity, vip)`**: quantità non positiva dà `0`; altrimenti applica lo sconto VIP del `20%` al subtotale, o nessuno sconto.

**Riusa `discounted`** senza duplicare la formula.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
public class Exercise {

    public int discounted(int priceInCents, int percent) {
        // TODO: completa questo blocco.
        // Suggerimento: Calcola lo sconto sul prezzo ricevuto, con moltiplicazione prima della divisione.
        return 0;
    }

    public int checkout(int priceInCents, int quantity, boolean vip) {
        // TODO: completa questo blocco.
        // Suggerimento: Gestisci prima la quantità non valida con un return.
        // Calcola il subtotale e richiama discounted con percentuale 20 oppure 0 in base a vip.
        return 0;
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
public class Exercise {

    public int discounted(int priceInCents, int percent) {
        return priceInCents - (priceInCents * percent) / 100;
    }

    public int checkout(int priceInCents, int quantity, boolean vip) {
        if (quantity <= 0) return 0;
        return discounted(priceInCents * quantity, vip ? 20 : 0);
    }
}
~~~

Vogliamo una sola formula di sconto e un `checkout` che la riusa, con un ritorno anticipato per le quantità non valide.

In `discounted` scriviamo `priceInCents - (priceInCents * percent) / 100`. Prima la moltiplicazione, poi la divisione intera: così l'arrotondamento avviene una volta sola e sempre nello stesso modo. È il DRY della lezione 29: la regola dello sconto vive in un posto solo. Se domani cambia l'arrotondamento, la modifichiamo lì e basta. Con la formula copiata in `checkout`, prima o poi una copia resterebbe indietro.

In `checkout` la prima riga è `if (quantity <= 0) return 0;`. Questo è il KISS della lezione: un caso per riga, niente flag né `if` annidati. Superato il controllo, passiamo il subtotale a `discounted` con `vip ? 20 : 0`. Lo sconto zero restituisce il subtotale intatto, quindi non serve un secondo ramo.

L'errore più insidioso è proprio nell'arrotondamento. Il test `definesIntegerRoundingOnce` si aspetta `800` da `discounted(999, 20)`. Se dividi prima, `999 / 100` dà `9` e ottieni `819`. Anche `priceInCents * (100 - percent) / 100` sembra equivalente, ma dà `799`: arrotonda il prezzo finale invece dello sconto. Un altro errore è dimenticare le quantità negative: il test prova sia `0` sia `-1` e vuole `0` in entrambi i casi.

## Riepilogo

- DRY: la conoscenza ripetuta diventa un metodo con un nome chiaro
- KISS: return anticipati al posto di flag e if annidati
- Refactoring: stesso output, struttura migliore
