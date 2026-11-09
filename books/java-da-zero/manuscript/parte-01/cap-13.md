# Lezione 8c. Leggere l'input: argomenti e tastiera

## Punti chiave

### Due strade per i dati

- Argomenti di avvio: java Greeting.java Anna
- Arrivano nell'array args del metodo main
- Tastiera: il programma fa una domanda mentre gira

> Percorso: Utente, poi Testo, poi Controllo, poi Programma.

### Prima controllare, poi usare

- args può essere vuoto: prima args.length, poi args[0]
- Integer.parseInt("abc") ferma il programma
- Scanner: hasNextInt() prima di nextInt()
- Si esegue nel terminale: java Nome.java, poi si risponde

### IO.readln o Scanner?

- KISS (keep it simple): una riga di testo? IO.readln
- Controllare il tipo prima di leggere? Scanner e hasNextInt()
- Tanti valori di seguito? Scanner
- Dopo nextInt(), un nextLine() consuma l'Invio

## Codice della lezione

`Greeting.java`

~~~java
public class Greeting {
    public static void main(String[] args) {
        if (args.length > 0) {
            System.out.println("Hello, " + args[0] + "!");
        } else {
            System.out.println("Usage: java Greeting.java name");
        }
    }
}
~~~

`LineTotal.java`

~~~java
public class LineTotal {
    public static void main(String[] args) {
        String name = IO.readln("Product: ");
        String text = IO.readln("Quantity: ");
        int quantity = Integer.parseInt(text);
        int priceInCents = 1500;
        System.out.println(name + " x " + quantity + " = " + quantity * priceInCents + " cents");
    }
}
~~~

`SafeLineTotal.java`

~~~java
import java.util.Scanner;
public class SafeLineTotal {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        int priceInCents = 1500;
        System.out.print("Quantity: ");
        if (scanner.hasNextInt()) {
            int quantity = scanner.nextInt();
            scanner.nextLine();
            System.out.print("Product: ");
            String name = scanner.nextLine();
            System.out.println(name + " x " + quantity + " = " + quantity * priceInCents + " cents");
        } else {
            System.out.println("Not a number: " + scanner.nextLine());
        }
    }
}
~~~

`SafeLineTotal.java`, prima del refactoring

~~~java
import java.util.Scanner;
public class SafeLineTotal {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        int priceInCents = 1500;
        System.out.print("Quantity: ");
        if (scanner.hasNextInt()) {
            int quantity = scanner.nextInt();
            System.out.print("Product: ");
            String name = scanner.nextLine();
            System.out.println(name + " x " + quantity + " = " + quantity * priceInCents + " cents");
        } else {
            System.out.println("Not a number: " + scanner.nextLine());
        }
    }
}
~~~

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
cat Greeting.java
java Greeting.java Anna
java Greeting.java
java LineTotal.java
Mug
3
abc
java SafeLineTotal.java
~~~

## Esercizio 08c: leggere una quantità senza eccezioni

Obiettivo: Controllare un testo digitato dall’utente prima di convertirlo in numero e rifiutarlo con un messaggio, senza far fermare il programma.

In `Exercise.java` **completa due metodi** *static*.

**`parseQuantity(text)`** trasforma in `int` il testo scritto dall’utente: restituisce il numero se `text` contiene soltanto cifre da `0` a `9` (`007` vale `7`, `0` vale `0`), altrimenti **`-1`**.

Sono *errori*:

- il testo vuoto,
- le lettere,
- gli spazi,
- il segno meno,
- il punto decimale.

`text` non è `null` e ha al massimo `9` caratteri, quindi `Integer.parseInt` non va mai in errore.

**`describeLine(name, quantityText, priceInCents)`** usa `parseQuantity`:

- se la quantità è valida restituisce la riga dello scontrino, per esempio `"Mug x 3 = 4500 cents"` (nome, `" x "`, quantità, `" = "`, totale, `" cents"`);
- altrimenti restituisce `"Not a number: "` seguito dal testo ricevuto, per esempio `"Not a number: abc"`.

*Per riconoscere una cifra*, un `char` si confronta con un altro `char` scritto tra apici singoli: `c >= '0' && c <= '9'` è `true` solo per le cifre, per esempio `'7' >= '0' && '7' <= '9'` è `true`.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
public class Exercise {

    public static int parseQuantity(String text) {
        // TODO: completa questo blocco.
        // Suggerimento: Se text è vuoto (length() == 0) restituisci -1. Poi scorri i caratteri con un ciclo for
        // e charAt(i): appena un carattere non è una cifra restituisci -1.
        // Se il ciclo finisce, il testo ha solo cifre: restituisci Integer.parseInt(text).
        return 0;
    }

    public static String describeLine(String name, String quantityText, int priceInCents) {
        // TODO: completa questo blocco.
        // Suggerimento: Chiama parseQuantity(quantityText) e tieni il risultato in un int.
        // Se è -1 restituisci "Not a number: " seguito da quantityText; altrimenti costruisci la riga con +.
        return "";
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
public class Exercise {

    public static int parseQuantity(String text) {
        if (text.length() == 0) {
            return -1;
        }
        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            if (c < '0' || c > '9') {
                return -1;
            }
        }
        return Integer.parseInt(text);
    }

    public static String describeLine(String name, String quantityText, int priceInCents) {
        int quantity = parseQuantity(quantityText);
        if (quantity < 0) {
            return "Not a number: " + quantityText;
        }
        return name + " x " + quantity + " = " + quantity * priceInCents + " cents";
    }
}
~~~

Vogliamo trasformare in numero il testo che l'utente scrive, senza fermare il programma quando scrive lettere. `parseQuantity` restituisce il numero se il testo contiene solo cifre, altrimenti `-1`. `describeLine` usa quel risultato per costruire la riga dello scontrino oppure il messaggio `Not a number: abc`.

La soluzione scarta prima il testo vuoto con `length() == 0`. Poi un `for` con `charAt(i)` guarda ogni carattere: un `char` si confronta come un numero, quindi `c < '0' || c > '9'` riconosce tutto ciò che non è una cifra e fa uscire il metodo con `-1`. Solo se il ciclo finisce `Integer.parseInt` converte il testo, e a quel punto non può più andare in errore. È la regola della lezione 8c: prima controlliamo, poi usiamo. `describeLine` riusa `parseQuantity` e non ripete il controllo.

Un errore tipico è guardare solo il primo carattere: `aLetterAfterTheDigitsIsMinusOne` lo smaschera, mentre `aLetterBeforeTheDigitsIsMinusOne` smaschera chi guarda solo l'ultimo. Un altro è sbagliare i confini dell'intervallo: con `<=` e `>=` lo `0` e il `9` verrebbero rifiutati e `firstAndLastDigitAreAccepted` fallisce, mentre con un intervallo troppo largo passerebbero `/` e `:`, che `charactersNextToTheDigitRangeAreRejected` controlla. Chi chiama `trim()` fa passare `" 5"`, e `spacesAreNotDigits` lo blocca. Infine `0` è una quantità valida: `zeroIsANumberNotAnError` impedisce di confonderlo con l'errore, e `parsesEveryNumberFromZeroTo2000` impedisce di barare con valori scritti nel codice. Le cifre di altri alfabeti, come quelle arabe, non sono cifre per questa regola: `digitsOutsideTheAsciiRangeAreNotDigits` ferma chi usa `Character.isDigit`. E `printsTheNumberNotTheTypedText` vuole `Mug x 7` anche quando l'utente scrive `007`.

## Riepilogo

- args.length prima di args[0]
- IO.readln restituisce sempre una String
- parseInt con lettere: errore; hasNextInt() controlla prima
- Prima controllare, poi usare
