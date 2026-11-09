# Lezione 3. Variabili, tipi e var

## Punti chiave

### Una variabile: nome, tipo e valore

- Il tipo dice che cosa può contenere
- Il nome serve a ritrovarla: in inglese, lowerCamelCase
- Il valore può cambiare, il tipo no

> Percorso: Tipo int, poi Nome moons, poi Valore 1.

### I tipi di base

- int e long: numeri interi (long oltre i 2 miliardi)
- double: numeri con la virgola, 9.81
- boolean: true o false; char: un carattere, 'E'
- String: un testo, "Earth" (è una classe)

### var con giudizio

- var deduce il tipo dal valore, durante la compilazione
- Il tipo resta fisso: var gravity = 10 è e resta un int
- Sì quando il tipo si legge a destra: var name = "Earth"
- No quando il valore lo nasconde: meglio double e long espliciti

## Codice della lezione

`Planet.java`

~~~java
public class Planet {
    public static void main(String[] args) {
        var name = "Earth";
        var moons = 1;
        long population = 8_200_000_000L;
        double gravity = 9.81;
        var habitable = true;
        var initial = 'E';
        System.out.println(name);
        System.out.println(moons);
        System.out.println(population);
        System.out.println(gravity);
        System.out.println(habitable);
        System.out.println(initial);
    }
}
~~~

`Planet.java`, prima versione

~~~java
public class Planet {
    public static void main(String[] args) {
        String name = "Earth";
        int moons = 1;
        long population = 8_200_000_000L;
        double gravity = 9.81;
        boolean habitable = true;
        char initial = 'E';
        System.out.println(name);
        System.out.println(moons);
        System.out.println(population);
        System.out.println(gravity);
        System.out.println(habitable);
        System.out.println(initial);
    }
}
~~~

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
jshell
~~~

Dentro JShell scriviamo:

~~~text
int moons = 1
moons = 2
moons = "one"
var gravity = 10
gravity = 9.81
/exit
~~~

## Esercizio 03: variabili per il catalogo

Obiettivo: Dichiarare dati con tipi appropriati e costruire una descrizione del prodotto.

Dentro `describe` **dichiara**:

- `productName` di tipo `String` con valore `"Notebook"`,
- `priceInCents` di tipo `int` con valore `2490`,
- `available` di tipo `boolean` con valore `true`.

**Restituisci** i tre valori concatenati con il separatore `|`, *senza spazi*: **`Notebook|2490|true`**.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
public class Exercise {

    public String describe() {
        // TODO: completa questo blocco.
        // Suggerimento: Dichiara ogni variabile con tipo, nome e valore: per esempio int quantity = 2;
        // String contiene testo tra virgolette; boolean contiene true oppure false.
        // Unisci le tre variabili con + e inserisci "|" tra un valore e il successivo.
        return "";
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
public class Exercise {

    public String describe() {
        String productName = "Notebook";
        int priceInCents = 2490;
        boolean available = true;
        return productName + "|" + priceInCents + "|" + available;
    }
}
~~~

L'obiettivo è dichiarare tre variabili con il tipo giusto e restituire una descrizione che le unisce.

Dentro `describe` scriviamo una variabile per riga, sempre nella forma tipo, nome, valore. `productName` è un `String`, perché contiene un testo tra virgolette. `priceInCents` è un `int`: come abbiamo visto nella lezione 3, i prezzi in centesimi sono numeri interi e non hanno bisogno di decimali. `available` è un `boolean`, che può valere solo `true` oppure `false`. I nomi seguono il lowerCamelCase: prima parola minuscola, le successive con l'iniziale maiuscola.

Nel `return` uniamo le tre variabili con il segno più, mettendo `"|"` tra un valore e il successivo. Siccome la prima variabile è un testo, ogni più che segue attacca il valore alla stringa: il numero 2490 e il boolean `true` diventano parte del testo. Il risultato è `Notebook|2490|true`.

Un errore tipico è scrivere il prezzo come `"2490"` tra virgolette, o `available` come `"true"`. Il test passerebbe lo stesso, perché confronta solo la stringa finale, ma il tipo della variabile sarebbe sbagliato e lo scopo dell'esercizio andrebbe perso. Quello che il test `describesProductWithRequiredValues` intercetta subito sono gli spazi e l'ordine: `Notebook | 2490 | true` oppure i valori invertiti non sono uguali a `Notebook|2490|true`.

Potresti anche usare `var` per `productName`, perché il tipo si legge chiaramente a destra. Per il prezzo e il boolean, però, il tipo esplicito rende il codice più chiaro.

## Riepilogo

- Una variabile ha nome, tipo e valore; il tipo non cambia
- int, long, double, boolean, char, String
- var solo quando il tipo è evidente
