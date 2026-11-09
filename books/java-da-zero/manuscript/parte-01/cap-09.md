# Lezione 6. Cicli

## Punti chiave

### Tre cicli

- for: quando sai quante volte ripetere
- while: finché una condizione è vera
- do while: il corpo gira almeno una volta

> Percorso: Condizione, poi Corpo, poi Aggiornamento.

### Quale ciclo scegliere

- Conti da un valore a un altro: for
- Ripeti finché succede qualcosa: while
- Serve almeno un giro: do while

### break, continue e il ciclo infinito

- break esce dal ciclo, continue passa al giro successivo
- Con parsimonia: spesso basta una condizione migliore
- Qualcosa nel corpo deve rendere falsa la condizione
- Ciclo bloccato: Stop nel pannello Run di IntelliJ

## Codice della lezione

`Laps.java`

~~~java
public class Laps {
    public static void main(String[] args) {
        int totalLaps = 3;
        for (int lap = 1; lap <= totalLaps; lap++) {
            System.out.println("Lap " + lap + " of " + totalLaps);
        }
        System.out.println("Race over");
    }
}
~~~

`Savings.java`

~~~java
public class Savings {
    public static void main(String[] args) {
        int balance = 100;
        int years = 0;
        while (balance < 150) {
            balance = balance + balance / 10;
            years++;
            System.out.println("Year " + years + ": " + balance);
        }
        System.out.println("Target reached in " + years + " years");
    }
}
~~~

`AtLeastOnce.java`

~~~java
public class AtLeastOnce {
    public static void main(String[] args) {
        int tickets = 0;
        while (tickets > 0) {
            System.out.println("while: tickets left " + tickets);
            tickets--;
        }
        do {
            System.out.println("do while: tickets left " + tickets);
            tickets--;
        } while (tickets > 0);
    }
}
~~~

`FirstMultiple.java`

~~~java
public class FirstMultiple {
    public static void main(String[] args) {
        for (int n = 50; n <= 60; n++) {
            if (n % 7 != 0) {
                continue;
            }
            System.out.println("First multiple of 7: " + n);
            break;
        }
        System.out.println("Search over");
    }
}
~~~

## Esercizio 06: sommare i numeri pari

Obiettivo: Scrivere un ciclo che termina e gestisce correttamente gli estremi.

**Implementa `sumEvenUpTo(limit)`**: somma tutti i numeri *pari* da `1` fino a `limit` incluso.

Se `limit` è minore di `2` **restituisci `0`**.

**Usa un ciclo** e **non una formula matematica**.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
public class Exercise {

    public int sumEvenUpTo(int limit) {
        // TODO: completa questo blocco.
        // Suggerimento: Parti da una variabile somma uguale a zero.
        // Scorri da 1 fino a limit incluso; un numero è pari se il resto della divisione per 2 è zero.
        // Quando è pari, aggiungilo alla somma con somma = somma + numero.
        // Restituisci la somma dopo il ciclo, non dentro il ciclo.
        return 0;
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
public class Exercise {

    public int sumEvenUpTo(int limit) {
        int sum = 0;
        for (int number = 1; number <= limit; number++) {
            if (number % 2 == 0) sum = sum + number;
        }
        return sum;
    }
}
~~~

L'obiettivo è sommare con un ciclo tutti i numeri pari fino a `limit` incluso.

In `sumEvenUpTo` partiamo da una variabile `sum` uguale a zero. Poi usiamo un `for`, perché, come abbiamo visto nella lezione 6, è il ciclo giusto quando contiamo da un valore a un altro. Il contatore `number` parte da 1 e avanza di uno a ogni giro, con `number++`. Nel corpo un `if` con `number % 2 == 0` lascia passare solo i pari, come nella lezione 4, e li aggiungiamo con `sum = sum + number`.

La condizione `number <= limit` include `limit` quando è pari, e fa finire il ciclo, perché `number` cresce a ogni giro. Se `limit` è minore di 2, il corpo non somma mai nulla e restituiamo 0 senza bisogno di un controllo a parte. Il `return` arriva dopo il ciclo, a somma completa.

Un errore tipico è usare `<` al posto di `<=`. Con `limit` uguale a 6 il 6 resterebbe fuori, e il test `includesEvenUpperBoundary` riceverebbe 6 invece di 12. Il test `excludesOddUpperBoundary` usa 7 e si aspetta ancora 12: chi somma anche i dispari ottiene 28. Un altro errore è mettere il `return` dentro il ciclo: il metodo uscirebbe al primo giro. Il test `handlesEmptyRange` controlla anche 0, 1 e -3, che devono dare tutti 0, e `handlesFirstEvenNumber` verifica che il primo pari, il 2, venga contato.

## Riepilogo

- for conta, while aspetta, do while gira almeno una volta
- break e continue con misura
- Ogni ciclo deve poter finire
