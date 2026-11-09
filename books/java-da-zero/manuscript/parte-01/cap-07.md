# Lezione 4. Operatori ed espressioni

## Punti chiave

### Espressioni e operatori aritmetici

- Un'espressione combina valori e operatori in un solo risultato
- Somma, sottrazione, prodotto, divisione: + - * /
- Il modulo % restituisce il resto della divisione
- Tra due int il risultato è un int

### La precedenza

- Prima * / %, poi + e -
- A parità di precedenza, da sinistra a destra
- Le parentesi decidono l'ordine

> Percorso: 8 + 4 / 2, poi 8 + 2, poi 10.

### Confronti e operatori logici

- == != &lt; &gt; &lt;= &gt;= producono un boolean
- = assegna un valore, == confronta due valori
- && vero se lo sono entrambi, || vero se almeno uno lo è
- ! inverte il valore

## Codice della lezione

`Arithmetic.java`

~~~java
public class Arithmetic {
    public static void main(String[] args) {
        int a = 7;
        int b = 2;
        System.out.println("a + b = " + (a + b));
        System.out.println("a - b = " + (a - b));
        System.out.println("a * b = " + (a * b));
        System.out.println("a / b = " + (a / b));
        System.out.println("a % b = " + (a % b));
    }
}
~~~

`Division.java`

~~~java
public class Division {
    public static void main(String[] args) {
        System.out.println("int / int: " + (7 / 2));
        System.out.println("double / int: " + (7.0 / 2));
        double result = 7 / 2;
        System.out.println("saved in a double: " + result);
    }
}
~~~

`Precedence.java`

~~~java
public class Precedence {
    public static void main(String[] args) {
        int first = 8;
        int second = 4;
        int wrongAverage = first + second / 2;
        int average = (first + second) / 2;
        System.out.println("wrong average: " + wrongAverage);
        System.out.println("average: " + average);
    }
}
~~~

`Comparison.java`

~~~java
public class Comparison {
    public static void main(String[] args) {
        int age = 16;
        boolean withAdult = true;
        System.out.println("adult: " + (age >= 18));
        System.out.println("exactly 16: " + (age == 16));
        System.out.println("can enter: " + (age >= 18 || withAdult));
        System.out.println("minor and alone: " + (age < 18 && !withAdult));
    }
}
~~~

## Esercizio 04: prezzi e divisione

Obiettivo: Usare aritmetica intera, modulo e confronti senza perdere informazioni.

**Implementa `total(priceInCents, quantity, discountPercent)`**:

1. calcola prima *prezzo × quantità*,
2. poi sottrai lo *sconto percentuale* con *divisione intera*.

Gli input sono non negativi e lo sconto è tra `0` e `100`.

In **`fullBoxes`** restituisci il numero di scatole complete da `6` prodotti; in **`remainder`** i prodotti rimasti fuori.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
public class Exercise {

    public int total(int priceInCents, int quantity, int discountPercent) {
        // TODO: completa questo blocco.
        // Suggerimento: Calcola prima il subtotale, poi lo sconto su quel subtotale.
        // Con due int, la divisione / scarta la parte decimale.
        return 0;
    }

    public int fullBoxes(int items) {
        // TODO: completa questo blocco.
        // Suggerimento: La divisione intera per 6 conta soltanto le scatole complete.
        return 0;
    }

    public int remainder(int items) {
        // TODO: completa questo blocco.
        // Suggerimento: Il modulo % restituisce il resto della divisione.
        return 0;
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
public class Exercise {

    public int total(int priceInCents, int quantity, int discountPercent) {
        int subtotal = priceInCents * quantity;
        return subtotal - (subtotal * discountPercent) / 100;
    }

    public int fullBoxes(int items) {
        return items / 6;
    }

    public int remainder(int items) {
        return items % 6;
    }
}
~~~

L'obiettivo è calcolare un totale scontato e dividere i prodotti in scatole, usando solo aritmetica intera.

In `total` salviamo prima il subtotale in una variabile, `priceInCents * quantity`. Poi calcoliamo lo sconto su quel subtotale: `(subtotal * discountPercent) / 100`. L'ordine conta. Come abbiamo visto nella lezione 4, la divisione tra due `int` scarta la parte decimale, quindi conviene moltiplicare prima e dividere alla fine, per perdere il meno possibile. Le parentesi rendono esplicito l'ordine, anche se qui la precedenza da sinistra a destra darebbe lo stesso risultato. Poi lo sottraiamo dal subtotale.

`fullBoxes` restituisce `items / 6`: la divisione intera conta solo le scatole complete, quindi con 14 prodotti ne riempiamo 2. `remainder` usa il modulo, `items % 6`, che restituisce il resto: con 14 prodotti ne avanzano 2, con 12 nessuno.

L'errore più insidioso è dividere troppo presto. Se scrivi `subtotal * (discountPercent / 100)`, la divisione `10 / 100` tra interi vale 0, lo sconto sparisce e il test `computesDiscountAfterMultiplication` riceve 6000 invece di 5400. Il test `preservesIntegerDiscountRule` controlla invece l'arrotondamento: con 999 centesimi e il 10 per cento lo sconto è 99, non 99,9, e il totale deve essere 900. Un altro errore è applicare lo sconto al prezzo unitario prima di moltiplicare per la quantità: con valori diversi da quelli dei test il risultato può cambiare per colpa degli arrotondamenti.

Si può fare a meno di `subtotal`, ma ripetere il prodotto due volte rende il codice meno leggibile.

## Riepilogo

- Divisione tra int: la parte decimale si perde
- Il tipo dei valori decide il tipo del risultato
- Nel dubbio, parentesi
