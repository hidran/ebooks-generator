# Lezione 8d. Mini progetto: la cassa da terminale

## Punti chiave

### La cassa che costruiamo

- Un menu con tre prodotti e i loro prezzi
- Scelta e quantità: la cassa stampa la riga dello scontrino
- 0 per pagare: la cassa stampa il totale
- Un dato sbagliato? Un messaggio, e si continua

> Percorso: Menu, poi Scelta, poi Quantità, poi Riga, poi Totale.

### I pezzi della sezione

- Array: nomi e prezzi in centesimi, legati dall'indice
- Metodi statici: un compito ciascuno
- while e switch: il ciclo e la scelta del menu
- / e %: dai centesimi agli euro; Scanner per la quantità

### Dividere il lavoro

- main: il dialogo con l'utente
- readQuantity: legge e controlla la quantità
- formatCents, menuChoice, lineTotal, receiptLine: solo calcoli
- DRY: formatCents scritto una volta, usato in tre punti

## Codice della lezione

`Checkout.java`

~~~java
import java.util.Scanner;
public class Checkout {
    public static void main(String[] args) {
        String[] names = {"Mug", "T-shirt", "Notebook"};
        int[] pricesInCents = {1500, 2490, 705};
        printMenu(names, pricesInCents);
        Scanner scanner = new Scanner(System.in);
        int totalInCents = 0;
        boolean open = true;
        while (open) {
            System.out.print("Choice: ");
            int choice = menuChoice(scanner.nextLine());
            if (choice == 0) {
                open = false;
            } else if (choice > 0) {
                int item = choice - 1;
                int quantity = readQuantity(scanner);
                int lineInCents = lineTotal(pricesInCents[item], quantity);
                totalInCents = totalInCents + lineInCents;
                System.out.println(receiptLine(names[item], quantity, lineInCents));
            } else {
                System.out.println("Unknown choice");
            }
        }
        System.out.println("Total: " + formatCents(totalInCents));
    }
    static void printMenu(String[] names, int[] prices) {
        for (int i = 0; i < names.length; i++) {
            System.out.println((i + 1) + ". " + names[i] + " " + formatCents(prices[i]));
        }
        System.out.println("0. Pay");
    }
    static String formatCents(int cents) {
        int euros = cents / 100;
        int rest = cents % 100;
        if (rest < 10) {
            return euros + ",0" + rest + " euro";
        }
        return euros + "," + rest + " euro";
    }
    static int menuChoice(String text) {
        return switch (text) {
            case "1" -> 1;
            case "2" -> 2;
            case "3" -> 3;
            case "0" -> 0;
            default -> -1;
        };
    }
    static int readQuantity(Scanner scanner) {
        int quantity = 0;
        while (quantity < 1) {
            System.out.print("Quantity: ");
            if (scanner.hasNextInt()) {
                quantity = scanner.nextInt();
                scanner.nextLine();
            } else {
                System.out.println("Not a number: " + scanner.nextLine());
            }
        }
        return quantity;
    }
    static int lineTotal(int priceInCents, int quantity) {
        return priceInCents * quantity;
    }
    static String receiptLine(String name, int quantity, int cents) {
        return name + " x " + quantity + " = " + formatCents(cents);
    }
}
~~~

`Checkout.java`, passaggio intermedio («menu»)

~~~java
public class Checkout {
    public static void main(String[] args) {
        String[] names = {"Mug", "T-shirt", "Notebook"};
        int[] pricesInCents = {1500, 2490, 705};
        printMenu(names, pricesInCents);
    }
    static void printMenu(String[] names, int[] prices) {
        for (int i = 0; i < names.length; i++) {
            System.out.println((i + 1) + ". " + names[i] + " " + formatCents(prices[i]));
        }
        System.out.println("0. Pay");
    }
    static String formatCents(int cents) {
        int euros = cents / 100;
        int rest = cents % 100;
        if (rest < 10) {
            return euros + ",0" + rest + " euro";
        }
        return euros + "," + rest + " euro";
    }
}
~~~

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
java Checkout.java
1
2
3
abc
7
0
~~~

## Esercizio 08d: i calcoli della cassa

Obiettivo: Separare i calcoli dalla tastiera: trasformare i centesimi in euro, interpretare la scelta del menu e costruire la riga dello scontrino.

In `Exercise.java` **completa quattro metodi** *static*, le parti di calcolo della cassa.

1. **`lineTotal(priceInCents, quantity)`** restituisce il prezzo per la quantità.
2. **`formatCents(cents)`** scrive i centesimi in euro, con la virgola e *sempre due cifre di centesimi*: `705` diventa `"7,05 euro"`, `1500` diventa `"15,00 euro"`, `5` diventa `"0,05 euro"`.
3. **`menuChoice(text)`** restituisce `1`, `2` o `3` per i prodotti e `0` per pagare quando `text` è esattamente `"1"`, `"2"`, `"3"` o `"0"`; per qualsiasi altro testo (vuoto, lettere, spazi, numeri fuori menu) restituisce **`-1`**.
4. **`receiptLine(name, quantity, cents)`** restituisce la riga dello scontrino, per esempio `"Mug x 2 = 30,00 euro"`, scrivendo l’importo con `formatCents`.

Gli importi non sono negativi e `text` non è `null`.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
public class Exercise {

    public static int lineTotal(int priceInCents, int quantity) {
        // TODO: completa questo blocco.
        // Suggerimento: Il totale della riga è il prezzo moltiplicato per la quantità.
        return 0;
    }

    public static String formatCents(int cents) {
        // TODO: completa questo blocco.
        // Suggerimento: Gli euro sono cents / 100 (divisione intera), i centesimi sono il resto cents % 100.
        // Se il resto è minore di 10 serve uno zero davanti: euros + ",0" + rest + " euro".
        // Altrimenti euros + "," + rest + " euro".
        return "";
    }

    public static int menuChoice(String text) {
        // TODO: completa questo blocco.
        // Suggerimento: Usa uno switch expression su text con return switch (text) { ... }.
        // Quattro case con il testo tra virgolette ("1", "2", "3", "0") che restituiscono il loro numero,
        // e un default che restituisce -1.
        return 0;
    }

    public static String receiptLine(String name, int quantity, int cents) {
        // TODO: completa questo blocco.
        // Suggerimento: Unisci con + il nome, " x ", la quantità, " = " e l’importo.
        // L’importo si scrive chiamando formatCents(cents): non rifare la divisione qui.
        return "";
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
public class Exercise {

    public static int lineTotal(int priceInCents, int quantity) {
        return priceInCents * quantity;
    }

    public static String formatCents(int cents) {
        int euros = cents / 100;
        int rest = cents % 100;
        if (rest < 10) {
            return euros + ",0" + rest + " euro";
        }
        return euros + "," + rest + " euro";
    }

    public static int menuChoice(String text) {
        return switch (text) {
            case "1" -> 1;
            case "2" -> 2;
            case "3" -> 3;
            case "0" -> 0;
            default -> -1;
        };
    }

    public static String receiptLine(String name, int quantity, int cents) {
        return name + " x " + quantity + " = " + formatCents(cents);
    }
}
~~~

La cassa della lezione 8d mescola dialogo e calcoli. Qui isoliamo i calcoli, che non leggono la tastiera e non stampano: `lineTotal`, `formatCents`, `menuChoice` e `receiptLine`, tutti `static`. Ricevono valori e ne restituiscono uno, per questo sono facili da verificare senza digitare niente nel terminale.

`formatCents` usa la divisione intera `cents / 100` per gli euro e il resto `cents % 100` per i centesimi. Se il resto è minore di 10 serve uno zero davanti, altrimenti 705 centesimi diventerebbero `7,5 euro`. `menuChoice` è uno `switch` sulle stringhe: ogni `case` confronta il testo intero e il `default` restituisce `-1` per qualunque altra cosa, senza `Integer.parseInt`, che con le lettere fermerebbe il programma. `receiptLine` chiama `formatCents` invece di rifare la divisione: è il principio DRY.

Il test `putsAZeroInFrontOfSingleDigitCents` prende chi dimentica lo zero, mentre `doesNotAddAZeroWhenCentsAreTen` prende chi scrive `rest <= 10` e ottiene `3,010` al posto di `3,10`. Chi controlla solo l'inizio del testo con `startsWith`, o usa `contains`, fa passare `"11"` o `"1a"`: `menuChoiceAcceptsOnlyTheExactText` li respinge. Chi lascia il punto al posto della virgola fallisce `formatsCentsWithTwoDigits`, e chi stampa i centesimi grezzi in `receiptLine` fallisce `receiptLineShowsNameQuantityAndEuros`. Infine `formatKeepsEveryCentForAnyAmount` prova tutti gli importi fino a 5000, quindi non basta scrivere nel codice i valori d'esempio. Il test `aWholeSaleWorksWithTheFourMethodsTogether` li fa lavorare insieme come nel `main` della cassa.

## Riepilogo

- Due array legati dallo stesso indice
- while con un boolean, switch sulle stringhe per il menu
- hasNextInt() prima di nextInt(), poi nextLine()
- cents / 100 e cents % 100, con lo zero davanti
