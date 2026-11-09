# Lezione 2b. Anatomia di un programma: classe, main, static e return

## Punti chiave

### Tutto vive in una classe

- Ogni riga di codice sta dentro le graffe di una classe
- Il file si chiama come la classe pubblica: Book.java
- Il programma parte dal metodo main

> Percorso: Book.java, poi class Book, poi main.

### Tre metodi nella classe Book

- main: il punto da cui parte il programma
- static void printHeader(): fa un'azione, senza oggetto
- String describe(): si chiama su un oggetto e restituisce un testo
- new Book().describe(): crea l'oggetto e chiama il metodo

### Il più unisce testo e valori

- "Dune" + "|" + 412 + "|" + true diventa Dune|412|true
- Si legge da sinistra a destra, un più alla volta
- Con un testo da una parte, il più unisce; con due numeri, somma
- Spazi e separatori si scrivono tra virgolette

## Codice della lezione

`Book.java`

~~~java
public class Book {
    public static void main(String[] args) {
        printHeader();
        System.out.println(new Book().describe());
    }

    static void printHeader() {
        System.out.println("Book catalog");
    }

    public String describe() {
        return "Dune" + "|" + 412 + "|" + true;
    }
}
~~~

## Esercizio 2b: un metodo static e un metodo che restituisce testo

Obiettivo: Scrivere un metodo static che restituisce un int e un metodo non static che restituisce un String unendo testo e valori con +.

In `Exercise.java` **completa due metodi**.

1. Il metodo *static* **`shelfSize`** non ha parametri e restituisce l'`int` `12`.
2. Il metodo **`shelfLabel`** non è *static*, non ha parametri e restituisce un `String` che unisce con `+` il testo `"Lamp"`, il separatore `"#"`, il numero `12`, il separatore `"#"` e il valore `true`: **`Lamp#12#true`**, *senza spazi*.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
public class Exercise {

    static int shelfSize() {
        // TODO: completa questo blocco.
        // Suggerimento: static permette di chiamare il metodo sulla classe, senza creare un oggetto.
        // Il tipo int richiede un numero: return consegna quel numero a chi chiama.
        return 0;
    }

    public String shelfLabel() {
        // TODO: completa questo blocco.
        // Suggerimento: String richiede un testo. Il segno + unisce testo e valori da sinistra a destra.
        // Non usare println: il risultato deve essere restituito con return.
        return "";
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
public class Exercise {

    static int shelfSize() {
        return 12;
    }

    public String shelfLabel() {
        return "Lamp" + "#" + 12 + "#" + true;
    }
}
~~~

L'obiettivo è scrivere due metodi che restituiscono un valore: un numero da un metodo `static` e un testo da un metodo di istanza.

In `shelfSize` scriviamo soltanto `return 12`. Il metodo è `static`, quindi, come abbiamo visto nella lezione 2b, si chiama sulla classe: `Exercise.shelfSize()`, senza creare nessun oggetto. Il tipo di ritorno `int` promette un numero intero, e `return` lo consegna a chi ha chiamato il metodo.

`shelfLabel` invece non è `static`: per usarlo serve un oggetto, ed è proprio quello che fa il test con `new Exercise().shelfLabel()`. Il tipo di ritorno è `String`, quindi restituiamo un testo. Il segno più lavora da sinistra a destra, un passo alla volta. `"Lamp" + "#"` dà `Lamp#`, poi arriva il numero 12, che viene attaccato al testo e non sommato, perché a sinistra c'è già una stringa. Lo stesso succede con il secondo `"#"` e con il boolean `true`. Il più non aggiunge spazi da solo, quindi il risultato è esattamente `Lamp#12#true`.

L'errore più comune è stampare invece di restituire. Se scrivi `System.out.println("Lamp#12#true")` e lasci `return ""`, il test `labelJoinsTextAndValuesWithPlus` riceve una stringa vuota e fallisce. Un altro inciampo sono gli spazi: `"Lamp " + "# "` produce un testo con spazi in mezzo, e il confronto con `Lamp#12#true` non perdona nemmeno uno spazio in più.

Funzionerebbe anche scrivere direttamente `return "Lamp#12#true"`, ma l'esercizio serve a farti vedere come il più unisce testo e valori di tipo diverso.

## Riepilogo

- Tutto il codice in una classe; il file ha il nome della classe pubblica
- public static void main: la JVM lo chiama senza creare oggetti
- static: si chiama con la classe; senza static: su un oggetto, con new
- void fa un'azione; un tipo di ritorno con return restituisce un valore
