# Lezione 12b. La classe Object, toString, equals e hashCode

## Punti chiave

### Ogni classe estende Object

- class Product equivale a class Product extends Object
- Object è la radice di tutte le classi
- Ogni oggetto eredita toString, equals e hashCode
- I record li generano da soli (lezione 11)

> Percorso: Object, poi Product, poi DigitalProduct.

### Tre metodi da ridefinire

- toString: il testo che println stampa
- equals: uguali per contenuto, non per riferimento
- hashCode: un numero intero che riassume l'oggetto
- Oggi li scriviamo a mano, con @Override

### Il contratto di equals e hashCode

- Oggetti uguali per equals: stesso hashCode
- Si ridefiniscono in coppia, sugli stessi campi
- Set e Map (lezione 18) cercano prima per hashCode
- IntelliJ li genera con Code &gt; Generate

## Codice della lezione

`Product.java`, versione di partenza

~~~java
public class Product {
    private final String name;
    private final int priceInCents;
    public Product(String name, int priceInCents) {
        this.name = name;
        this.priceInCents = priceInCents;
    }
}
~~~

`Main.java`

~~~java
public class Main {
    public static void main(String[] args) {
        Product coffee = new Product("Coffee", 250);
        Product sameCoffee = new Product("Coffee", 250);
        System.out.println(coffee);
        System.out.println("Same object: " + (coffee == sameCoffee));
        System.out.println("Equal: " + coffee.equals(sameCoffee));
        System.out.println("Same hash: " + (coffee.hashCode() == sameCoffee.hashCode()));
    }
}
~~~

`Product.java`, passaggio intermedio («tostring»)

~~~java
public class Product {
    private final String name;
    private final int priceInCents;
    public Product(String name, int priceInCents) {
        this.name = name;
        this.priceInCents = priceInCents;
    }
    @Override
    public String toString() {
        return "Product[name=" + name + ", priceInCents=" + priceInCents + "]";
    }
}
~~~

`Product.java`, passaggio intermedio («equals»)

~~~java
import java.util.Objects;
public class Product {
    private final String name;
    private final int priceInCents;
    public Product(String name, int priceInCents) {
        this.name = name;
        this.priceInCents = priceInCents;
    }
    @Override
    public String toString() {
        return "Product[name=" + name + ", priceInCents=" + priceInCents + "]";
    }
    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (o == null || getClass() != o.getClass()) {
            return false;
        }
        Product other = (Product) o;
        return priceInCents == other.priceInCents && Objects.equals(name, other.name);
    }
}
~~~

`Product.java`

~~~java
import java.util.Objects;
public class Product {
    private final String name;
    private final int priceInCents;
    public Product(String name, int priceInCents) {
        this.name = name;
        this.priceInCents = priceInCents;
    }
    @Override
    public String toString() {
        return "Product[name=" + name + ", priceInCents=" + priceInCents + "]";
    }
    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (o == null || getClass() != o.getClass()) {
            return false;
        }
        Product other = (Product) o;
        return priceInCents == other.priceInCents && Objects.equals(name, other.name);
    }
    @Override
    public int hashCode() {
        return Objects.hash(name, priceInCents);
    }
}
~~~

## Esercizio 12b: uguaglianza per codice prodotto

Obiettivo: Rispettare il contratto fra equals e hashCode in una classe ordinaria.

`Exercise` rappresenta un codice SKU immutabile.

1. **Implementa `equals`** per confrontare il contenuto del campo `sku`, gestendo anche `null` e oggetti di altro tipo.
2. **`hashCode`** deve dipendere dallo stesso campo.
3. **`toString`** deve restituire `"Sku[<sku>]"`.

`sku` non è mai `null`.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
public final class Exercise {

    private final String sku;

    public Exercise(String sku) {
        this.sku = sku;
    }

    @Override
    public boolean equals(Object other) {
        // TODO: completa questo blocco.
        // Suggerimento: Controlla prima se this e other sono lo stesso oggetto.
        // Poi restituisci false se other è null oppure se getClass() è diverso da other.getClass().
        // Fai il cast a Exercise e confronta i due sku con equals, perché sono stringhe.
        return false;
    }

    @Override
    public int hashCode() {
        // TODO: completa questo blocco.
        // Suggerimento: Usa lo stesso campo usato in equals: stringhe uguali hanno lo stesso hashCode().
        return 0;
    }

    @Override
    public String toString() {
        // TODO: completa questo blocco.
        // Suggerimento: Costruisci il testo con il campo sku, includendo le parentesi quadre.
        return "";
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
public final class Exercise {

    private final String sku;

    public Exercise(String sku) {
        this.sku = sku;
    }

    @Override
    public boolean equals(Object other) {
        if (this == other) return true;
        if (other == null || getClass() != other.getClass()) return false;
        Exercise value = (Exercise) other;
        return sku.equals(value.sku);
    }

    @Override
    public int hashCode() {
        return sku.hashCode();
    }

    @Override
    public String toString() {
        return "Sku[" + sku + "]";
    }
}
~~~

L'obiettivo è ridefinire `equals`, `hashCode` e `toString` in modo che due codici SKU con lo stesso testo siano uguali.

In `equals` controlliamo prima se `this == other`: se è lo stesso oggetto, la risposta è sicuramente `true`. Poi scartiamo `null` e gli oggetti di un'altra classe con `other == null || getClass() != other.getClass()`, la stessa forma che abbiamo scritto in `Product` nella lezione. A questo punto il cast a `Exercise` è sicuro e confrontiamo i due campi con `sku.equals(value.sku)`, perché sono stringhe.

`hashCode` restituisce `sku.hashCode()`. Come abbiamo visto nella lezione 12b, oggetti uguali per `equals` devono avere lo stesso hashCode: usando lo stesso campo lo otteniamo gratis. `toString` restituisce `"Sku[" + sku + "]"`.

L'errore più insidioso è scrivere `sku == value.sku`. Con due testi scritti tra virgolette sembra funzionare, perché Java riusa lo stesso oggetto, ma con testi costruiti a runtime i riferimenti sono diversi. Il test `comparesSkuTextAndNotTheStringReference` crea gli SKU con `new String("B1")` e lo smaschera. Il test `comparesValueAndHandlesOtherTypes` vuole invece che due `Exercise("B1")` siano uguali, che `Exercise("B2")` sia diverso e che `null` e la stringa `"B1"` non risultino uguali: chi controlla solo il campo senza controllare il tipo, o dimentica `null`, fallisce lì. Il test `equalObjectsHaveEqualHashes` controlla la coppia: mette due `Exercise("B1")` in un `HashSet` e si aspetta un solo elemento. Si aspetta anche hash diversi per `B1` e `B2`, quindi un `hashCode` che restituisce sempre 0 non passa. Anche `b1` contro `B1` e `B10` contro `B1` devono risultare diversi.

## Riepilogo

- Ogni classe estende Object
- == confronta i riferimenti, equals il contenuto
- equals e hashCode sempre insieme
