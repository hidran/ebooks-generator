# Lezione 22b. Soldi senza sorprese con BigDecimal

## Punti chiave

### Perché double sbaglia i conti

- 0.1 + 0.2 fa 0.30000000000000004
- double scrive i numeri in base 2: 0.1 ha infinite cifre
- Un errore minuscolo che si somma fattura dopo fattura
- Regola: mai double o float per un importo

### BigDecimal: decimali esatti

- In base 10: un intero senza virgola più una scala
- 18.75 è l'intero 1875 con scala 2
- Costanti nel codice: new BigDecimal("0.22")
- Centesimi in un long: BigDecimal.valueOf(cents, 2)
- Mai new BigDecimal(0.1): copia l'errore del double

### Arrotondare: HALF_UP e HALF_EVEN

- setScale(2, RoundingMode...): due decimali e una regola esplicita
- HALF_UP, quello della scuola: 4.125 diventa 4.13
- HALF_EVEN, del banchiere: 4.125 diventa 4.12, 4.135 diventa 4.14
- La regola la scrivono i requisiti, non chi programma
- divide senza scala: ArithmeticException se le cifre non finiscono

### Quale scegliere (KISS)

- double: mai per i soldi
- Centesimi interi: int nello Shop, long quando i totali crescono
- BigDecimal: percentuali, tassi, cambi, divisioni
- Prezzo come testo: new BigDecimal("1.15"); con double e cast a int, 114 centesimi

## Codice della lezione

`MoneyBasics.java`, prima versione

~~~java
public class MoneyBasics {
    public static void main(String[] args) {
        double sum = 0.1 + 0.2;
        System.out.println("double: " + sum);
        System.out.println("Is it 0.3? " + (sum == 0.3));
        int priceInCents = 150_000_000;
        int quantity = 20;
        System.out.println("int: " + priceInCents * quantity);
        long exact = Math.multiplyExact((long) priceInCents, quantity);
        System.out.println("long: " + exact);
    }
}
~~~

`MoneyBasics.java`

~~~java
import java.math.BigDecimal;
public class MoneyBasics {
    public static void main(String[] args) {
        double sum = 0.1 + 0.2;
        System.out.println("double: " + sum);
        System.out.println("Is it 0.3? " + (sum == 0.3));
        int priceInCents = 150_000_000;
        int quantity = 20;
        System.out.println("int: " + priceInCents * quantity);
        long exact = Math.multiplyExact((long) priceInCents, quantity);
        System.out.println("long: " + exact);
        System.out.println("From double: " + new BigDecimal(0.1));
        System.out.println("From String: " + new BigDecimal("0.1"));
        System.out.println("valueOf: " + BigDecimal.valueOf(0.1));
    }
}
~~~

`Cents.java`

~~~java
import java.math.BigDecimal;
public final class Cents {
    private Cents() {
    }
    public static long lineTotal(long priceInCents, int quantity) {
        return Math.multiplyExact(priceInCents, quantity);
    }
    public static BigDecimal toEuro(long cents) {
        return BigDecimal.valueOf(cents, 2);
    }
}
~~~

`VatCalculator.java`

~~~java
import java.math.BigDecimal;
import java.math.RoundingMode;
public record VatCalculator(BigDecimal rate, RoundingMode rounding) {
    public static final BigDecimal ITALIAN_STANDARD_RATE = new BigDecimal("0.22");
    public BigDecimal vatOn(BigDecimal net) {
        return net.multiply(rate).setScale(2, rounding);
    }
    public BigDecimal grossOf(BigDecimal net) {
        return net.add(vatOn(net));
    }
}
~~~

`Cart.java`

~~~java
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.text.NumberFormat;
import java.util.Locale;
public class Cart {
    public static void main(String[] args) {
        BigDecimal subtotal = Cents.toEuro(Cents.lineTotal(625, 3));
        BigDecimal rate = VatCalculator.ITALIAN_STANDARD_RATE;
        var halfUp = new VatCalculator(rate, RoundingMode.HALF_UP);
        var halfEven = new VatCalculator(rate, RoundingMode.HALF_EVEN);
        System.out.println("Subtotal: " + subtotal);
        System.out.println("VAT half up: " + halfUp.vatOn(subtotal));
        System.out.println("VAT half even: " + halfEven.vatOn(subtotal));
        var euro = NumberFormat.getCurrencyInstance(Locale.ITALY);
        System.out.println("To pay: " + euro.format(halfUp.grossOf(subtotal)));
        System.out.println("Big: " + euro.format(new BigDecimal("1234.50")));
    }
}
~~~

`MoneyTraps.java`

~~~java
import java.math.BigDecimal;
public class MoneyTraps {
    public static void main(String[] args) {
        BigDecimal two = new BigDecimal("2.0");
        BigDecimal twoWithCents = new BigDecimal("2.00");
        System.out.println("equals: " + two.equals(twoWithCents));
        System.out.println("compareTo: " + two.compareTo(twoWithCents));
        BigDecimal total = new BigDecimal("10.00");
        total.add(new BigDecimal("5.00"));
        System.out.println("Lost: " + total);
        total = total.add(new BigDecimal("5.00"));
        System.out.println("Kept: " + total);
    }
}
~~~

## Esercizio 22b: il totale con l’IVA, al centesimo

Obiettivo: Sommare prezzi scritti come testo con BigDecimal e calcolare l’IVA al 22% con due decimali e arrotondamento HALF_UP.

Il carrello dello Shop arriva come lista di prezzi scritti in `String`, per esempio `"6.25"`. **Non usare mai `double`** per gli importi: ogni prezzo diventa un `BigDecimal` con il costruttore che riceve la `String`.

1. **Completa `netTotal(prices)`**: somma tutti i prezzi e restituisce il totale senza IVA; con la lista vuota restituisce zero.
2. **Completa `vatOn(net)`**: moltiplica il netto per `VAT_RATE`, cioè il 22%, e porta il risultato a **due decimali** con `RoundingMode.HALF_UP`.
3. **Completa `totalWithVat(prices)`**: restituisce netto più IVA, con l’IVA calcolata *una sola volta sul totale* e non riga per riga. Il risultato ha sempre **scala 2**, anche per `"10"` (che dà `12.20`) e per la lista vuota (che dà `0.00`).
4. **Completa `sameAmount(a, b)`**: restituisce `true` se i due importi valgono uguale anche con scale diverse, per esempio `2.0` e `2.00`. Qui `equals` è la trappola, perché guarda anche la scala.

I prezzi hanno al massimo due decimali e il punto come separatore. Se un prezzo non è un numero, lascia che il costruttore lanci la sua `NumberFormatException`. `BigDecimal` è *immutabile*: **usa sempre il valore restituito** da `add` e dagli altri metodi, e non modificare la lista ricevuta.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.List;

public class Exercise {

    private static final BigDecimal VAT_RATE = new BigDecimal("0.22");

    public BigDecimal netTotal(List<String> prices) {
        // TODO: completa questo blocco.
        // Suggerimento: Parti da new BigDecimal("0") e per ogni prezzo della lista somma new BigDecimal(price).
        // BigDecimal è immutabile: assegna il risultato di add alla variabile, altrimenti il prezzo si perde.
        return new BigDecimal("0");
    }

    public BigDecimal vatOn(BigDecimal net) {
        // TODO: completa questo blocco.
        // Suggerimento: Moltiplica net per VAT_RATE: le scale si sommano, quindi il risultato ha più decimali.
        // Poi chiama setScale(2, RoundingMode.HALF_UP) sul risultato di multiply e restituiscilo.
        return new BigDecimal("0");
    }

    public BigDecimal totalWithVat(List<String> prices) {
        // TODO: completa questo blocco.
        // Suggerimento: Calcola il netto con netTotal(prices) una volta sola.
        // Restituisci net.add(vatOn(net)): l'IVA si calcola sul totale, non su ogni riga.
        return new BigDecimal("0");
    }

    public boolean sameAmount(BigDecimal a, BigDecimal b) {
        // TODO: completa questo blocco.
        // Suggerimento: equals guarda anche la scala (2.0 e 2.00 sono diversi): usa a.compareTo(b) == 0.
        return false;
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.List;

public class Exercise {

    private static final BigDecimal VAT_RATE = new BigDecimal("0.22");

    public BigDecimal netTotal(List<String> prices) {
        BigDecimal net = new BigDecimal("0");
        for (String price : prices) {
            net = net.add(new BigDecimal(price));
        }
        return net;
    }

    public BigDecimal vatOn(BigDecimal net) {
        return net.multiply(VAT_RATE).setScale(2, RoundingMode.HALF_UP);
    }

    public BigDecimal totalWithVat(List<String> prices) {
        BigDecimal net = netTotal(prices);
        return net.add(vatOn(net));
    }

    public boolean sameAmount(BigDecimal a, BigDecimal b) {
        return a.compareTo(b) == 0;
    }
}
~~~

In questo esercizio calcoli il totale di un carrello con l'IVA al 22% senza perdere un centesimo. I prezzi arrivano come testo, per esempio `"6.25"`, e tu completi quattro metodi: `netTotal` somma i prezzi, `vatOn` calcola l'IVA, `totalWithVat` mette insieme netto e IVA, `sameAmount` confronta due importi. Due fatti guidano tutto: un `BigDecimal` non cambia mai dopo la creazione, e la scala fa parte del suo valore.

La soluzione funziona perché ogni prezzo nasce da una `String` con `new BigDecimal(price)`, quindi è esatto. `vatOn` moltiplica per `0.22` e chiama subito `setScale(2, RoundingMode.HALF_UP)`: il carrello della lezione vale 18.75, l'IVA esatta è 4.1250 e arrotondata diventa 4.13, per un totale di 22.88. `totalWithVat` calcola il netto una volta sola e somma l'IVA, e la scala resta sempre 2.

Gli errori tipici sono cinque. Se scrivi `net.add(...)` senza assegnare il risultato, il prezzo sparisce e `netTotalAddsTheThreeNotebooksOfTheLesson` fallisce, come i test del carrello lungo. Con `HALF_EVEN` al posto di `HALF_UP` ottieni 4.12 e `vatOnRoundsTheTieUpNotToTheEvenNeighbour` ti ferma. Se calcoli l'IVA riga per riga sbagli di un centesimo, e `vatIsComputedOnTheTotalNotOnEachLine` lo mostra con tre righe da 0.25. Se dimentichi la scala, `totalWithVatKeepsScaleTwoForWholeNumbers` e il carrello vuoto non tornano, perché `equals` guarda anche i decimali. Infine, in `sameAmount` l'`equals` rende `2.0` e `2.00` diversi: `sameAmountIgnoresTheScale` vuole `compareTo(b) == 0`. Il nome del test fallito ti dice quale comportamento manca, quindi leggilo prima di toccare il codice.

> Per andare oltre: il capitolo «Approfondimento 1. Soldi senza sorprese», nella parte Java in azienda, riprende questo argomento con i casi che si incontrano nei sistemi reali.

## Riepilogo

- Centesimi esatti: long e Math.multiplyExact contro l'overflow
- BigDecimal da una String o con valueOf
- setScale con HALF_UP o HALF_EVEN, come dicono i requisiti
- equals guarda la scala, compareTo no; usare il valore restituito
- divide vuole scala e regola; NumberFormat con Locale.ITALY
