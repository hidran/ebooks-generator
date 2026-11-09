# Lezione 5. Condizioni, if e switch come espressione

## Punti chiave

### Decidere con if

- if (condizione): il blocco gira solo se è vera
- else if: altre condizioni, controllate in ordine
- else: tutti i casi rimasti
- Il primo ramo vero vince, gli altri si saltano

> Percorso: if, poi else if, poi else.

### switch come espressione

- case 1 -&gt; "Monday": un valore per ogni caso
- Restituisce un valore: String name = switch (day) { ... };
- Nessun fallthrough, niente break
- default copre tutti gli altri valori

### Quale scegliere

- if: condizioni diverse tra loro o intervalli (score &gt;= 90)
- switch: un solo valore confrontato con casi fissi
- switch come espressione: il compilatore controlla che ogni caso sia coperto

## Codice della lezione

`if/DayName.java`

~~~java
public class DayName {
    public static void main(String[] args) {
        int day = 6;
        String name;
        if (day == 1) {
            name = "Monday";
        } else if (day == 2) {
            name = "Tuesday";
        } else if (day == 3) {
            name = "Wednesday";
        } else if (day == 4) {
            name = "Thursday";
        } else if (day == 5) {
            name = "Friday";
        } else if (day == 6) {
            name = "Saturday";
        } else if (day == 7) {
            name = "Sunday";
        } else {
            name = "Unknown";
        }
        System.out.println("Day " + day + " is " + name);
    }
}
~~~

`DayName.java`

~~~java
public class DayName {
    public static void main(String[] args) {
        int day = 9;
        String name = switch (day) {
            case 1 -> "Monday";
            case 2 -> "Tuesday";
            case 3 -> "Wednesday";
            case 4 -> "Thursday";
            case 5 -> "Friday";
            case 6 -> "Saturday";
            case 7 -> "Sunday";
            default -> "Unknown";
        };
        System.out.println("Day " + day + " is " + name);
    }
}
~~~

`switch/DayName.java`

~~~java
public class DayName {
    public static void main(String[] args) {
        int day = 3;
        String name = switch (day) {
            case 1 -> "Monday";
            case 2 -> "Tuesday";
            case 3 -> "Wednesday";
            case 4 -> "Thursday";
            case 5 -> "Friday";
            case 6 -> "Saturday";
            case 7 -> "Sunday";
            default -> "Unknown";
        };
        System.out.println("Day " + day + " is " + name);
    }
}
~~~

`DayName.java`, versione con un errore voluto: non compila o il test fallisce, per leggere il messaggio

~~~java
public class DayName {
    public static void main(String[] args) {
        int day = 3;
        String name = switch (day) {
            case 1 -> "Monday";
            case 2 -> "Tuesday";
            case 3 -> "Wednesday";
            case 4 -> "Thursday";
            case 5 -> "Friday";
            case 6 -> "Saturday";
            case 7 -> "Sunday";
        };
        System.out.println("Day " + day + " is " + name);
    }
}
~~~

## Esercizio 05: tariffe di spedizione

Obiettivo: Scegliere rami corretti con if e switch come espressione.

**Implementa `shipping(totalInCents, country)`**.

- Se il totale è almeno `5000` la spedizione è **gratuita** per ogni paese.
- Altrimenti `IT` costa `490`, `FR` e `DE` costano `990`, ogni altro codice costa `1490`.

Gli input non sono `null` e il totale è non negativo.

Usa **`if`** per la soglia e **`switch`** per i codici.

Lo `switch` accetta anche una `String`: `case "IT" -> 490`; confronta il codice con il testo tra virgolette, e *ogni codice ha il suo `case`*.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
public class Exercise {

    public int shipping(int totalInCents, String country) {
        // TODO: completa questo blocco.
        // Suggerimento: Controlla per prima la soglia: un return termina subito il metodo.
        // Se la soglia non vale, scegli il costo con switch (country): un case per ogni codice, FR e DE compresi, e un default.
        return 0;
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
public class Exercise {

    public int shipping(int totalInCents, String country) {
        if (totalInCents >= 5000) return 0;
        return switch (country) {
            case "IT" -> 490;
            case "FR" -> 990;
            case "DE" -> 990;
            default -> 1490;
        };
    }
}
~~~

L'obiettivo è scegliere il costo di spedizione giusto, prima con una soglia e poi in base al paese.

In `shipping` controlliamo per prima cosa la soglia: se `totalInCents >= 5000` restituiamo subito 0. Un `return` termina il metodo, quindi tutto quello che segue non viene eseguito. Come abbiamo visto nella lezione 5, `if` è lo strumento giusto per gli intervalli, mentre `switch` serve a confrontare un solo valore con casi fissi.

Se la soglia non vale, restituiamo direttamente il risultato di uno `switch` usato come espressione. Il valore confrontato qui è una stringa, `country`, e funziona come con i numeri della lezione: le etichette sono testi tra virgolette. Ogni caso usa la freccia e produce un valore, senza `break` e senza fallthrough. Per FR e DE scriviamo due `case` separati, ciascuno con 990: come nella lezione, ogni caso ha il suo valore, ed è la forma più semplice da leggere. Il `default` copre ogni altro codice e rende lo switch completo. Il punto e virgola dopo la graffa di chiusura c'è perché lo switch intero è un'espressione dentro il `return`.

L'errore più comune è il confine della soglia. Se scrivi `totalInCents > 5000`, un totale di esattamente 5000 paga la spedizione, e il test `handlesFreeShippingBoundary` se ne accorge con `shipping(5000, "IT")`, che deve dare 0. Un altro errore è mettere il controllo della soglia solo nel caso `"IT"`: lo stesso test verifica che `shipping(7000, "US")` sia gratuito, anche se `"US"` finisce nel `default`.

## Riepilogo

- if, else if, else: il primo ramo vero vince
- switch con la freccia: un valore per caso, niente fallthrough
- default rende lo switch completo
