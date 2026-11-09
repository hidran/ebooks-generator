# Lezione 12. Composizione prima dell'ereditarietà

## Punti chiave

### Ereditarietà: "è un"

- class DigitalProduct extends Product
- super(...) chiama il costruttore della classe madre
- @Override ridefinisce un metodo ereditato
- Un prodotto digitale è un prodotto

> Percorso: DigitalProduct, poi extends, poi Product.

### Composizione: "ha un"

- Una classe tiene altri oggetti nei suoi campi
- Un ordine ha un cliente e ha un prodotto
- Prova: se la frase con "è un" suona falsa, componi

> Percorso: Order, poi ha un, poi Customer + Product.

### Quando estendere, quando comporre

- Estendi solo se "è un" vale sempre
- Una classe estende una sola classe madre
- I record non si possono estendere
- Preferisci la composizione all'ereditarietà

## Codice della lezione

`Product.java`

~~~java
public class Product {
    private final String name;
    private final int priceInCents;
    public Product(String name, int priceInCents) {
        this.name = name;
        this.priceInCents = priceInCents;
    }
    public String getName() {
        return name;
    }
    public int getPriceInCents() {
        return priceInCents;
    }
    public String describe() {
        return name + ", " + priceInCents + " cents";
    }
}
~~~

`DigitalProduct.java`

~~~java
public class DigitalProduct extends Product {
    private final String downloadLink;
    public DigitalProduct(String name, int priceInCents, String link) {
        super(name, priceInCents);
        this.downloadLink = link;
    }
    @Override
    public String describe() {
        return super.describe() + ", link " + downloadLink;
    }
}
~~~

`Order.java`

~~~java
public record Order(Customer customer, Product product, int quantity) {
    public int totalInCents() {
        return product.getPriceInCents() * quantity;
    }
    public String summary() {
        return customer.name() + ": " + quantity + " x " + product.getName();
    }
}
record Customer(String name) {
}
~~~

`before/Order.java`

~~~java
public class Order extends Product {
    private final String customerName;
    public Order(String customerName, String productName, int priceInCents) {
        super(productName, priceInCents);
        this.customerName = customerName;
    }
}
~~~

`Main.java`

~~~java
public class Main {
    public static void main(String[] args) {
        var mug = new Product("Mug", 1200);
        var ebook = new DigitalProduct("Ebook", 1500, "shop.example/ebook");
        System.out.println(mug.describe());
        System.out.println(ebook.describe());
        System.out.println("Inherited name: " + ebook.getName());
        var order = new Order(new Customer("Anna"), ebook, 2);
        System.out.println(order.summary());
        System.out.println("Total: " + order.totalInCents() + " cents");
    }
}
~~~

`before/Product.java`: uguale al listato `Product.java` qui sopra.

## Esercizio 12: comporre un ordine

Obiettivo: Delegare il comportamento agli oggetti contenuti in un ordine.

`Customer` e `Product` sono già pronti.

**Completa il record `Order`**:

1. **`totalInCents`** moltiplica prezzo per quantità,
2. **`summary`** restituisce `"<cliente>: <prodotto> x<quantità> = <totale>"`.

Esempio: `Ada: Book x2 = 3000`.

**Usa gli accessori** degli oggetti contenuti.

Quantità sempre positiva; nessun valore `null`.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
public class Exercise {

    public record Customer(String name) {}

    public record Product(String name, int priceInCents) {}

    public record Order(Customer customer, Product product, int quantity) {
        public int totalInCents() {
            // TODO: completa questo blocco.
            // Suggerimento: Un record espone accessori con lo stesso nome dei componenti, seguiti da ().
            // Leggi il prezzo da product.priceInCents() e usa quantity.
            return 0;
        }

        public String summary() {
            // TODO: completa questo blocco.
            // Suggerimento: Leggi customer.name() e product.name(): sono oggetti contenuti nell’ordine.
            // Riusa totalInCents() per il totale e rispetta spazi e separatori richiesti.
            return "";
        }
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
public class Exercise {

    public record Customer(String name) {}

    public record Product(String name, int priceInCents) {}

    public record Order(Customer customer, Product product, int quantity) {
        public int totalInCents() {
            return product.priceInCents() * quantity;
        }

        public String summary() {
            return (
                customer.name() + ": " + product.name() + " x" + quantity + " = " + totalInCents()
            );
        }
    }
}
~~~

L'obiettivo è far calcolare a un ordine il totale e il riepilogo, delegando agli oggetti che contiene.

`Order` è un record che ha un cliente, un prodotto e una quantità. Come abbiamo visto nella lezione 12, questa è composizione: un ordine non è un prodotto, ha un prodotto. Per questo non estendiamo nulla e chiediamo i dati agli oggetti contenuti.

In `totalInCents` restituiamo `product.priceInCents() * quantity`. `product` è il componente del record, e `priceInCents()` è l'accessore generato per il record `Product`, con le parentesi e senza `get`. `quantity` invece è un `int`, un componente di `Order` stesso, e lo usiamo direttamente.

In `summary` costruiamo il testo con il segno più: `customer.name()`, poi `": "`, il nome del prodotto, `" x"` attaccato alla quantità, `" = "` e infine il totale. Per il totale richiamiamo `totalInCents()` invece di ripetere la moltiplicazione, così la formula resta in un posto solo. Le parentesi tonde intorno all'espressione servono solo ad andare a capo in modo ordinato.

L'errore più frequente riguarda gli spazi. La lettera `x` è attaccata alla quantità, `x2`, mentre intorno all'uguale ci sono due spazi: il test `totalsContainedProduct` si aspetta esattamente `Ada: Book x2 = 3000`, e `Ada: Book x 2 = 3000` fallisce. Un altro errore è scrivere `customer` invece di `customer.name()`: il più userebbe il `toString` del record e il testo comincerebbe con `Customer[name=Ada]`.

Il test `usesEachOrderData` prova un secondo ordine, `Luca: Mug x3 = 2400`, per assicurarsi che nessun valore sia scritto a mano.

## Riepilogo

- extends, super e @Override: la classe figlia
- Composizione: un oggetto ha altri oggetti e delega
- Record per i dati semplici: Customer e Order
