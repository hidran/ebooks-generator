# Lezione 17. Package, visibilità e organizzazione del codice

## Punti chiave

### Package e cartelle

- Un package raggruppa le classi per responsabilità
- package com.shop.catalog; è la prima riga del file
- Un solo tipo public per file, con il nome del file
- import per gli altri package; java.lang è sempre importato

> Percorso: com.shop.catalog, poi cartelle com/shop/catalog, poi Product.java.

### Quattro livelli di visibilità

- public: tutti
- protected: il package e le sottoclassi, anche altrove
- package-private (nessuna parola): solo il package
- private: solo la classe
- Regola: il livello più ristretto che funziona

### protected e classi annidate

- protected: una sottoclasse in un altro package lo usa nei propri metodi
- static class Line dentro Order: si crea da sola, Order.Line
- Inner class (senza static): legata a un oggetto della classe esterna
- Senza bisogno di quel legame: static

## Codice della lezione

`com/shop/catalog/Product.java`

~~~java
package com.shop.catalog;
public class Product {
    private final String name;
    final int priceInCents;
    public Product(String name, int priceInCents) {
        this.name = name;
        this.priceInCents = priceInCents;
    }
    public String name() {
        return name;
    }
    public int priceInCents() {
        return priceInCents;
    }
}
~~~

`com/shop/app/Order.java`

~~~java
package com.shop.app;
import com.shop.catalog.Product;
public class Order {
    public static class Line {
        private final Product product;
        private final int quantity;
        public Line(Product product, int quantity) {
            this.product = product;
            this.quantity = quantity;
        }
    }
    private final Line[] lines;
    public Order(Line[] lines) {
        this.lines = lines;
    }
    public int totalInCents() {
        int total = 0;
        for (Line line : lines) {
            total += line.product.priceInCents() * line.quantity;
        }
        return total;
    }
}
~~~

`com/shop/app/Main.java`, versione con un errore voluto: non compila o il test fallisce, per leggere il messaggio

~~~java
package com.shop.app;
import com.shop.catalog.Product;
public class Main {
    public static void main(String[] args) {
        Product coffee = new Product("Coffee", 250);
        Product tea = new Product("Tea", 180);
        System.out.println(coffee.name() + ": " + coffee.priceInCents);
        Order.Line[] lines = {new Order.Line(coffee, 2), new Order.Line(tea, 3)};
        Order order = new Order(lines);
        System.out.println("Total: " + order.totalInCents());
    }
}
~~~

`com/shop/app/Main.java`

~~~java
package com.shop.app;
import com.shop.catalog.Product;
public class Main {
    public static void main(String[] args) {
        Product coffee = new Product("Coffee", 250);
        Product tea = new Product("Tea", 180);
        System.out.println(coffee.name() + ": " + coffee.priceInCents());
        Order.Line[] lines = {new Order.Line(coffee, 2), new Order.Line(tea, 3)};
        Order order = new Order(lines);
        System.out.println("Total: " + order.totalInCents());
    }
}
~~~

## Riepilogo

- Package = responsabilità = cartelle; import, tranne java.lang
- Un tipo public per file; public, protected, package-private, private
