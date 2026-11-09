# Lezione 8. Array, String e text block

## Punti chiave

### Array: più valori, un solo nome

- int[] scores = {7, 9, 6};
- L'indice parte da zero: scores[0] è il primo
- scores.length dice quanti sono, e non cambia
- Si scorre con for oppure con for each

> Percorso: [0] 7, poi [1] 9, poi [2] 6.

### String e text block

- Metodi: length, charAt, toUpperCase, substring, contains, equals
- Le stringhe sono immutabili: ogni metodo restituisce una stringa nuova
- Text block: testo su più righe, tra """ e """

### Due errori tipici

- Indice fuori dai limiti: ArrayIndexOutOfBoundsException
- L'ultimo indice valido è length - 1
- == confronta gli oggetti, non il testo
- Per il contenuto delle stringhe: equals

## Codice della lezione

`Scores.java`

~~~java
public class Scores {
    public static void main(String[] args) {
        int[] scores = {7, 9, 6};
        scores[2] = 8;
        System.out.println("First: " + scores[0]);
        System.out.println("Length: " + scores.length);
        int total = 0;
        for (int i = 0; i < scores.length; i++) {
            total += scores[i];
        }
        System.out.println("Total: " + total);
        for (int score : scores) {
            System.out.println("Score: " + score);
        }
    }
}
~~~

`Words.java`

~~~java
public class Words {
    public static void main(String[] args) {
        String language = "Java";
        System.out.println("Length: " + language.length());
        System.out.println("First: " + language.charAt(0));
        System.out.println("Middle: " + language.substring(1, 3));
        System.out.println("Has va: " + language.contains("va"));
        language.toUpperCase();
        System.out.println("After: " + language);
        String upper = language.toUpperCase();
        System.out.println("Upper: " + upper);
        System.out.println("Equals: " + upper.equals("JAVA"));
    }
}
~~~

`Menu.java`

~~~java
public class Menu {
    public static void main(String[] args) {
        String menu = """
            Menu of the day:
              1. Pasta
              2. "Special" pizza
            """;
        System.out.print(menu);
        System.out.println("Characters: " + menu.length());
    }
}
~~~

## Esercizio 08: ripulire i nomi dei prodotti

Obiettivo: Scorrere un array e trasformare stringhe preservando i dati originali.

**Implementa `normalize(names)`**: **crea un nuovo array** della stessa lunghezza.

Per ciascun nome:

1. elimina gli spazi iniziali e finali con `trim`,
2. convertilo in maiuscolo con `toUpperCase(Locale.ROOT)`.

**Non modificare** l’array ricevuto. I nomi non sono `null`.

*Gestisci anche un array vuoto.*

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
import java.util.Locale;

public class Exercise {

    public String[] normalize(String[] names) {
        // TODO: completa questo blocco.
        // Suggerimento: Crea il risultato con new String[names.length]. Gli indici partono da 0.
        // Per ogni indice leggi names[i], applica trim() e poi toUpperCase(Locale.ROOT).
        // Scrivi nel nuovo array e restituiscilo dopo il ciclo.
        return new String[0];
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
import java.util.Locale;

public class Exercise {

    public String[] normalize(String[] names) {
        String[] result = new String[names.length];
        for (int i = 0; i < names.length; i++) result[i] = names[i].trim().toUpperCase(Locale.ROOT);
        return result;
    }
}
~~~

L'obiettivo è produrre un nuovo array con i nomi ripuliti, lasciando intatto quello ricevuto.

In `normalize` creiamo per prima cosa `result` con `new String[names.length]`. Come abbiamo visto nella lezione 8, la lunghezza di un array è fissa, quindi la decidiamo subito: tanti posti quanti sono i nomi. Poi scorriamo gli indici con un `for` che parte da 0 e si ferma prima di `names.length`, perché l'ultimo indice valido è `length - 1`.

A ogni giro leggiamo `names[i]` e concateniamo due chiamate. `trim()` toglie gli spazi all'inizio e alla fine, poi `toUpperCase(Locale.ROOT)` converte in maiuscolo. `Locale.ROOT` dice a Java di non applicare le regole di una lingua particolare, così il risultato è lo stesso su ogni computer. Le stringhe sono immutabili: nessuno dei due metodi cambia `names[i]`, entrambi restituiscono una stringa nuova, che scriviamo in `result[i]`. Con un array vuoto il ciclo non gira mai e restituiamo un array vuoto.

L'errore tipico è chiamare `names[i].trim()` senza usare il risultato, come nel primo tentativo con `toUpperCase` della lezione: la stringa resta quella di prima e il test `normalizesEveryElement` riceve `" book "` invece di `"BOOK"`. Un altro errore è scrivere il risultato dentro `names` e restituire lo stesso array. Il test `doesNotModifyInput` controlla che `names` contenga ancora `" coffee "` e, con `assertNotSame`, che l'array restituito sia un oggetto diverso.

Funziona anche l'ordine inverso, prima `toUpperCase` e poi `trim`, perché gli spazi non hanno maiuscole.

## Riepilogo

- Array: indice da zero, length fissa, for e for each
- String: metodi utili, immutabile, confronto con equals
- Text block: testo su più righe, leggibile
