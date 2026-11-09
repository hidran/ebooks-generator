# Lezione 11. Record, dati immutabili

## Punti chiave

### Le classi contenitore

- Product della lezione 10: campi privati, costruttore, getter
- Per stampare e confrontare: toString, equals e hashCode a mano
- Tante righe ripetitive per due soli dati

### Un record in una riga

- record Product(String name, int priceInCents)
- Generati: campi private final, costruttore, name() e priceInCents()
- Generati anche: toString, equals e hashCode

> Percorso: class Product, oltre 30 righe, poi record Product, 7 righe.

### Quando usare un record

- Dati semplici: un prodotto, un indirizzo, un risultato
- Immutabile: per un valore diverso si crea un nuovo record
- Costruttore compatto: valida i dati prima di assegnarli
- Stato che cambia nel tempo: classe normale

## Codice della lezione

`Main.java`, passaggio intermedio («validation»)

~~~java
public class Main {
    public static void main(String[] args) {
        Product book = new Product("Book", 1200);
        System.out.println("Created: " + book);
        Product broken = new Product("Broken", -500);
        System.out.println("Never printed: " + broken);
    }
}
~~~

`Product.java`

~~~java
public record Product(String name, int priceInCents) {
    public Product {
        if (priceInCents < 0) {
            throw new IllegalArgumentException("Negative price: " + priceInCents);
        }
    }
    public Product withDiscount(int percent) {
        int discount = priceInCents * percent / 100;
        return new Product(name, priceInCents - discount);
    }
}
~~~

`Main.java`, passaggio intermedio («basics»)

~~~java
public class Main {
    public static void main(String[] args) {
        Product pen = new Product("Pen", 150);
        System.out.println(pen);
        System.out.println(pen.name() + " costs " + pen.priceInCents());
        Product samePen = new Product("Pen", 150);
        System.out.println("Equal: " + pen.equals(samePen));
        System.out.println("Same hash: " + (pen.hashCode() == samePen.hashCode()));
        System.out.println("Same object: " + (pen == samePen));
        Product cheaperPen = pen.withDiscount(20);
        System.out.println("Discounted: " + cheaperPen);
        System.out.println("Original: " + pen);
    }
}
~~~

## Esercizio 11: record con invarianti

Obiettivo: Usare un record con costruttore compatto e accessori generati.

La validazione con `IllegalArgumentException` è *già fornita*. **Non devi scrivere né modificare** le istruzioni `throw`: le eccezioni saranno spiegate nella lezione 16.

**Completa soltanto i TODO** indicati nei commenti.

**Completa il costruttore compatto** del record `Product`:

- `name` non deve essere `null` o *blank*,
- `priceInCents` deve essere positivo.

In caso contrario lancia `IllegalArgumentException`.

**Elimina gli spazi esterni** dal nome.

Gli accessori, `equals` e `hashCode` sono generati da Java.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
public class Exercise {

    public record Product(String name, int priceInCents) {
        public Product {
            if (name == null || name.isBlank() || priceInCents <= 0) {
                throw new IllegalArgumentException("Invalid product");
            }
            // TODO: completa questo blocco.
            // Suggerimento: La validazione è già pronta. Nel costruttore compatto usi i nomi dei componenti.
            // Assegna a name il risultato di trim(); Java salverà i componenti automaticamente.
        }
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
public class Exercise {

    public record Product(String name, int priceInCents) {
        public Product {
            if (name == null || name.isBlank() || priceInCents <= 0) {
                throw new IllegalArgumentException("Invalid product");
            }
            name = name.trim();
        }
    }
}
~~~

L'obiettivo è completare il costruttore compatto di un record, così che ogni `Product` nasca con un nome ripulito e dati validi.

Il controllo iniziale è già fornito: rifiuta un nome `null` o fatto solo di spazi, e un prezzo che non sia positivo. Delle eccezioni parleremo nella lezione 16. Dopo il controllo scriviamo una sola riga: `name = name.trim()`.

Come abbiamo visto nella lezione 11, il costruttore compatto non ha la lista dei parametri. Dentro, `name` e `priceInCents` sono i valori ricevuti, e alla fine del blocco Java li assegna da solo ai campi del record. Se riassegniamo `name`, è il nome ripulito che finisce nel campo. Non dobbiamo toccare `priceInCents`, perché va salvato così com'è.

L'errore più frequente è scrivere `this.name = name.trim()`, come in una classe normale. In un costruttore compatto non si possono assegnare i campi: lo fa Java alla fine, quindi il compilatore si ferma con un errore. Un altro errore è chiamare `name.trim()` senza riassegnarlo. Le stringhe sono immutabili, il risultato si perde, e il test `createsValueWithAccessors` riceve `" Book "` invece di `"Book"` da `p.name()`.

Il test `comparesByValue` mostra il vantaggio dei record: due `Product` con gli stessi dati sono uguali, perché `equals` è generato e confronta i componenti. Il test `rejectsInvalidData` verifica invece il controllo già pronto con `" "`, `null` e un prezzo pari a 0.

## Riepilogo

- Una riga di componenti, il resto lo genera il compilatore
- Accessori senza get: name(), priceInCents()
- Immutabile e sempre valido grazie al costruttore compatto
