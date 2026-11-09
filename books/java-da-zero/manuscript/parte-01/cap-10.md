# Lezione 7. Metodi e riuso del codice

## Punti chiave

### Perché i metodi

- Un metodo dà un nome a un blocco di codice
- Si scrive una volta, si chiama quando serve
- main e println sono già metodi
- Il main diventa più corto e leggibile

### Firma e chiamata

- static int add(int a, int b): tipo di ritorno, nome, parametri
- return restituisce il valore a chi chiama
- void: esegue un'azione, non restituisce nulla

> Percorso: main, poi add(3, 4), poi return 7, poi sum.

### DRY: Don't Repeat Yourself

- Codice copiato: ogni modifica va fatta in più punti
- Un metodo, un nome chiaro, un solo scopo
- Refactoring: stessa uscita, codice più semplice da cambiare

> Percorso: Codice ripetuto, poi Metodo con un nome, poi Stesso output.

## Codice della lezione

`FirstMethods.java`

~~~java
public class FirstMethods {
    public static void main(String[] args) {
        int sum = add(3, 4);
        System.out.println("3 + 4 = " + sum);
        System.out.println("10 + 5 = " + add(10, 5));
        greet("Anna");
    }

    static int add(int a, int b) {
        return a + b;
    }

    static void greet(String name) {
        System.out.println("Hello, " + name + "!");
    }
}
~~~

`ExamResults.java`

~~~java
public class ExamResults {
    public static void main(String[] args) {
        printResult("Anna", 72);
        printResult("Marco", 45);
        printResult("Sara", 60);
    }

    static void printResult(String name, int score) {
        System.out.println(name + ": " + score + " " + outcome(score));
    }

    static String outcome(int score) {
        if (score >= 60) {
            return "passed";
        }
        return "failed";
    }
}
~~~

`ExamResults.java`, prima del refactoring

~~~java
public class ExamResults {
    public static void main(String[] args) {
        int annaScore = 72;
        if (annaScore >= 60) {
            System.out.println("Anna: " + annaScore + " passed");
        } else {
            System.out.println("Anna: " + annaScore + " failed");
        }
        int marcoScore = 45;
        if (marcoScore >= 60) {
            System.out.println("Marco: " + marcoScore + " passed");
        } else {
            System.out.println("Marco: " + marcoScore + " failed");
        }
        int saraScore = 60;
        if (saraScore >= 60) {
            System.out.println("Sara: " + saraScore + " passed");
        } else {
            System.out.println("Sara: " + saraScore + " failed");
        }
    }
}
~~~

## Esercizio 07: un solo calcolo del totale

Obiettivo: Estrarre un metodo riusabile e richiamarlo senza duplicare una formula.

1. **Implementa `lineTotal(priceInCents, quantity)`**, che restituisce il prodotto dei due argomenti.
2. **Implementa `cartTotal(firstPrice, firstQuantity, secondPrice, secondQuantity)`**: richiama `lineTotal` **due volte** e somma i risultati.

Gli input sono non negativi.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
public class Exercise {

    public int lineTotal(int priceInCents, int quantity) {
        // TODO: completa questo blocco.
        // Suggerimento: Usa i parametri ricevuti per calcolare il totale della singola riga.
        return 0;
    }

    public int cartTotal(int firstPrice, int firstQuantity, int secondPrice, int secondQuantity) {
        // TODO: completa questo blocco.
        // Suggerimento: Richiama lineTotal con prezzo e quantità della prima riga, poi della seconda.
        // Somma i due risultati: non riscrivere qui la formula della riga.
        return 0;
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
public class Exercise {

    public int lineTotal(int priceInCents, int quantity) {
        return priceInCents * quantity;
    }

    public int cartTotal(int firstPrice, int firstQuantity, int secondPrice, int secondQuantity) {
        return lineTotal(firstPrice, firstQuantity) + lineTotal(secondPrice, secondQuantity);
    }
}
~~~

L'obiettivo è scrivere la formula del totale di una riga una sola volta e riusarla per il carrello.

In `lineTotal` restituiamo `priceInCents * quantity`. Il metodo riceve i due valori come parametri e consegna il risultato con `return`: è la stessa firma che abbiamo visto nella lezione 7, con tipo di ritorno, nome e parametri.

In `cartTotal` richiamiamo `lineTotal` due volte, una con prezzo e quantità della prima riga e una con quelli della seconda, e sommiamo i due risultati. Ogni chiamata restituisce un `int`, quindi possiamo usarla direttamente dentro un'espressione, come se fosse un numero. Questo è il principio DRY: la regola per il totale di una riga vive in un posto solo. Se un giorno cambia, per esempio con uno sconto per riga, modifichi `lineTotal` e `cartTotal` si aggiorna da solo.

L'errore che l'esercizio vuole evitare è riscrivere la formula: `firstPrice * firstQuantity + secondPrice * secondQuantity` dà lo stesso numero e i test passano, ma la regola ora vive in due posti. Un errore che i test intercettano è scambiare le quantità tra le righe, con `lineTotal(firstPrice, secondQuantity)` e `lineTotal(secondPrice, firstQuantity)`. Con i valori di `combinesDifferentLines` otterresti 150 per 2 più 350 per 3, cioè 1350 invece di 1150. Il test `handlesEmptyQuantities` controlla invece che con quantità zero il totale sia 0.

Potresti anche salvare i due risultati in variabili, come `int first = lineTotal(...)`, prima di sommarli. È corretto, e con molte righe a volte più leggibile.

## Riepilogo

- Firma: tipo di ritorno, nome, parametri
- return restituisce un valore, void non restituisce nulla
- Copia e incolla? Scrivi un metodo
