# Lezione 9. Classi e oggetti

## Punti chiave

### Classe e oggetto

- Classe: lo stampo, descrive un concetto
- Oggetto: un'istanza concreta, con i propri valori
- new crea un nuovo oggetto a partire dalla classe

> Percorso: classe Product, poi new Product(), poi oggetti coffee e book.

### Campi e metodi

- Campi: lo stato dell'oggetto (name, priceInCents)
- Prezzo in centesimi: un int, niente decimali
- Metodi di istanza: il comportamento, senza static
- Si usano con il punto: coffee.describe()

### Riferimenti e null

- Una variabile Product contiene un riferimento, non l'oggetto
- sameCoffee = coffee: due variabili, un solo oggetto
- Campi mai assegnati: 0 per i numeri, null per i riferimenti
- Metodo chiamato su null: NullPointerException

## Codice della lezione

`Main.java`, prima versione

~~~java
public class Main {
    public static void main(String[] args) {
        Product coffee = new Product();
        coffee.name = "Coffee";
        coffee.priceInCents = 250;
        Product book = new Product();
        book.name = "Book";
        book.priceInCents = 1500;
        System.out.println(coffee.describe());
        System.out.println(book.describe());
        System.out.println("Three coffees: " + coffee.priceFor(3));
    }
}
~~~

`Main.java`

~~~java
public class Main {
    public static void main(String[] args) {
        Product coffee = new Product();
        coffee.name = "Coffee";
        coffee.priceInCents = 250;
        Product book = new Product();
        book.name = "Book";
        book.priceInCents = 1500;
        System.out.println(coffee.describe());
        System.out.println(book.describe());
        System.out.println("Three coffees: " + coffee.priceFor(3));
        Product sameCoffee = coffee;
        sameCoffee.priceInCents = 300;
        System.out.println(coffee.describe());
        Product tea = new Product();
        System.out.println(tea.describe());
    }
}
~~~

`Product.java`

~~~java
public class Product {
    String name;
    int priceInCents;
    String describe() {
        return name + ": " + priceInCents + " cents";
    }
    int priceFor(int quantity) {
        return priceInCents * quantity;
    }
}
~~~

## Esercizio 09: oggetti indipendenti

Obiettivo: Associare stato e comportamento a ciascuna istanza di una classe.

`Exercise` rappresenta un prodotto: i campi pubblici `name` e `priceInCents` sono già dichiarati.

**Implementa `describe()`** in modo che restituisca `name` seguito da `" costs "` e dal prezzo in centesimi. Esempio: `Book costs 1500`.

Il metodo deve **usare i campi del proprio oggetto**.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
public class Exercise {

    public String name;
    public int priceInCents;

    public String describe() {
        // TODO: completa questo blocco.
        // Suggerimento: name e priceInCents sono i campi di questo oggetto: non ridichiararli come variabili locali.
        // Unisci i campi e il testo " costs " con +, poi usa return.
        return "";
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
public class Exercise {

    public String name;
    public int priceInCents;

    public String describe() {
        return name + " costs " + priceInCents;
    }
}
~~~

L'obiettivo è scrivere un metodo di istanza che descrive il prodotto usando i campi del proprio oggetto.

In `describe` restituiamo `name + " costs " + priceInCents`. Non dichiariamo nessuna variabile: `name` e `priceInCents` sono i campi dell'oggetto, già dichiarati nella classe. Come abbiamo visto nella lezione 9, un metodo senza `static` lavora sempre su un oggetto preciso, quello su cui lo chiami con il punto. Quando il test scrive `book.describe()`, dentro il metodo `name` vale `"Book"` e `priceInCents` vale 1500, cioè i valori assegnati proprio a `book`. Il testo `" costs "` contiene uno spazio prima e uno dopo, così le parole non si attaccano.

Ogni oggetto creato con `new` ha la sua copia dei campi. Il test `keepsObjectsIndependent` crea due prodotti, `a` e `b`, e controlla che ognuno descriva sé stesso: `Mug costs 800` e `Pen costs 200`.

L'errore più comune è ridichiarare i campi dentro il metodo, per esempio `String name = "Book";`. La variabile locale nasconde il campo, e il metodo restituisce sempre lo stesso testo, qualunque oggetto lo chiami. Il primo test passerebbe, ma `keepsObjectsIndependent` riceverebbe `Book costs 1500` per entrambi gli oggetti. Un altro errore riguarda gli spazi: `name + "costs" + priceInCents` produce `Bookcosts1500`.

Potresti anche scrivere `this.name + " costs " + this.priceInCents`. È equivalente, e rende esplicito che stai leggendo i campi dell'oggetto corrente.

## Riepilogo

- Classe: lo stampo; oggetto: un'istanza creata con new
- Campi e metodi di istanza, accesso con il punto
- Variabili di tipo classe: riferimenti, anche null
