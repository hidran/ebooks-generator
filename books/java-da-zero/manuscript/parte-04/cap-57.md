# Lezione 37b. TDD sul dominio Shop

## Punti chiave

### Prima il test

- Rosso: un test per un comportamento che ancora non c'è
- Verde: il codice minimo che lo fa passare
- Refactoring: codice migliore, test sempre verdi
- Un solo comportamento per ciclo

> Percorso: rosso, poi verde, poi refactoring.

### La regola della spedizione

- Sotto i 30 euro: tariffa standard, 500 centesimi
- Da 30 euro: tariffa ridotta, 200 centesimi
- Da 50 euro: spedizione gratuita, 0
- Prima la lista dei test, poi il codice

### Quando conviene il TDD

- Sì: regole, calcoli, soglie e casi limite
- Meno: la disposizione di un'interfaccia grafica
- Meno: esperimenti usa e getta
- Uno strumento, non un obbligo

## Codice della lezione

Il progetto parte dal modello Maven del corso: questi sono il suo `pom.xml` e il wrapper.

`pom.xml`: uguale a quello della lezione 27.

`.mvn/wrapper/maven-wrapper.properties`: uguale a quello della lezione 27.

`src/test/java/com/shop/domain/OrderTest.java`, passaggio intermedio («list»)

~~~java
package com.shop.domain;
import org.junit.jupiter.api.Test;
import java.util.ArrayList;
import java.util.List;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
class OrderTest {
    private final Product book = new Product("BK-1", "Book", 1500);
    private final Product pen = new Product("PN-1", "Pen", 200);
    @Test
    void totalSumsTheLineSubtotals() {
        OrderLine books = new OrderLine(book, 2);
        OrderLine pens = new OrderLine(pen, 3);
        Order order = new Order(List.of(books, pens));
        assertThat(order.totalInCents()).isEqualTo(3600);
    }
    @Test
    void keepsItsOwnCopyOfTheLines() {
        List<OrderLine> lines = new ArrayList<>();
        lines.add(new OrderLine(pen, 1));
        Order order = new Order(lines);
        lines.clear();
        assertThat(order.lines()).hasSize(1);
    }
    @Test
    void rejectsAnEmptyOrder() {
        assertThatThrownBy(() -> new Order(List.of()))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Order must have lines");
    }
    // TODO under 30 euro: standard fee, 5 euro
    // TODO from 50 euro: free shipping
    // TODO from 30 euro: reduced fee, 2 euro
}
~~~

`src/test/java/com/shop/domain/OrderTest.java`

~~~java
package com.shop.domain;
import org.junit.jupiter.api.Test;
import java.util.ArrayList;
import java.util.List;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
class OrderTest {
    private final Product book = new Product("BK-1", "Book", 1500);
    private final Product pen = new Product("PN-1", "Pen", 200);
    @Test
    void totalSumsTheLineSubtotals() {
        OrderLine books = new OrderLine(book, 2);
        OrderLine pens = new OrderLine(pen, 3);
        Order order = new Order(List.of(books, pens));
        assertThat(order.totalInCents()).isEqualTo(3600);
    }
    @Test
    void keepsItsOwnCopyOfTheLines() {
        List<OrderLine> lines = new ArrayList<>();
        lines.add(new OrderLine(pen, 1));
        Order order = new Order(lines);
        lines.clear();
        assertThat(order.lines()).hasSize(1);
    }
    @Test
    void rejectsAnEmptyOrder() {
        assertThatThrownBy(() -> new Order(List.of()))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Order must have lines");
    }
    @Test
    void standardFeeUnderThirtyEuro() {
        assertThat(orderWorth(2999).shippingInCents()).isEqualTo(500);
    }
    @Test
    void freeShippingFromFiftyEuro() {
        assertThat(orderWorth(5000).shippingInCents()).isEqualTo(0);
    }
    @Test
    void reducedFeeFromThirtyEuro() {
        assertThat(orderWorth(3000).shippingInCents()).isEqualTo(200);
    }
    private Order orderWorth(int cents) {
        Product item = new Product("IT-1", "Item", cents);
        return new Order(List.of(new OrderLine(item, 1)));
    }
}
~~~

`src/test/java/com/shop/domain/OrderTest.java`, prima versione

~~~java
package com.shop.domain;
import org.junit.jupiter.api.Test;
import java.util.ArrayList;
import java.util.List;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
class OrderTest {
    private final Product book = new Product("BK-1", "Book", 1500);
    private final Product pen = new Product("PN-1", "Pen", 200);
    @Test
    void totalSumsTheLineSubtotals() {
        OrderLine books = new OrderLine(book, 2);
        OrderLine pens = new OrderLine(pen, 3);
        Order order = new Order(List.of(books, pens));
        assertThat(order.totalInCents()).isEqualTo(3600);
    }
    @Test
    void keepsItsOwnCopyOfTheLines() {
        List<OrderLine> lines = new ArrayList<>();
        lines.add(new OrderLine(pen, 1));
        Order order = new Order(lines);
        lines.clear();
        assertThat(order.lines()).hasSize(1);
    }
    @Test
    void rejectsAnEmptyOrder() {
        assertThatThrownBy(() -> new Order(List.of()))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Order must have lines");
    }
    @Test
    void standardFeeUnderThirtyEuro() {
        assertThat(orderWorth(2999).shippingInCents()).isEqualTo(500);
    }
    // TODO from 50 euro: free shipping
    // TODO from 30 euro: reduced fee, 2 euro
    private Order orderWorth(int cents) {
        Product item = new Product("IT-1", "Item", cents);
        return new Order(List.of(new OrderLine(item, 1)));
    }
}
~~~

`src/main/java/com/shop/domain/Order.java`, passaggio intermedio («stub»)

~~~java
package com.shop.domain;
import java.util.List;
public record Order(List<OrderLine> lines) {
    public Order {
        if (lines.isEmpty()) {
            throw new IllegalArgumentException("Order must have lines");
        }
        lines = List.copyOf(lines);
    }
    public int totalInCents() {
        return lines.stream().mapToInt(OrderLine::subtotalInCents).sum();
    }
    public int shippingInCents() {
        return 0;
    }
}
~~~

`src/main/java/com/shop/domain/Order.java`

~~~java
package com.shop.domain;
import java.util.List;
public record Order(List<OrderLine> lines) {
    private static final int FREE_SHIPPING_FROM = 5000;
    private static final int STANDARD_FEE = 500;
    private static final int REDUCED_SHIPPING_FROM = 3000;
    private static final int REDUCED_FEE = 200;
    public Order {
        if (lines.isEmpty()) {
            throw new IllegalArgumentException("Order must have lines");
        }
        lines = List.copyOf(lines);
    }
    public int totalInCents() {
        return lines.stream().mapToInt(OrderLine::subtotalInCents).sum();
    }
    public int shippingInCents() {
        int total = totalInCents();
        if (total >= FREE_SHIPPING_FROM) {
            return 0;
        }
        if (total >= REDUCED_SHIPPING_FROM) {
            return REDUCED_FEE;
        }
        return STANDARD_FEE;
    }
}
~~~

`src/main/java/com/shop/domain/Order.java`, passaggio intermedio («fake»)

~~~java
package com.shop.domain;
import java.util.List;
public record Order(List<OrderLine> lines) {
    public Order {
        if (lines.isEmpty()) {
            throw new IllegalArgumentException("Order must have lines");
        }
        lines = List.copyOf(lines);
    }
    public int totalInCents() {
        return lines.stream().mapToInt(OrderLine::subtotalInCents).sum();
    }
    public int shippingInCents() {
        return 500;
    }
}
~~~

`src/test/java/com/shop/domain/OrderTest.java`, passaggio intermedio («second»)

~~~java
package com.shop.domain;
import org.junit.jupiter.api.Test;
import java.util.ArrayList;
import java.util.List;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
class OrderTest {
    private final Product book = new Product("BK-1", "Book", 1500);
    private final Product pen = new Product("PN-1", "Pen", 200);
    @Test
    void totalSumsTheLineSubtotals() {
        OrderLine books = new OrderLine(book, 2);
        OrderLine pens = new OrderLine(pen, 3);
        Order order = new Order(List.of(books, pens));
        assertThat(order.totalInCents()).isEqualTo(3600);
    }
    @Test
    void keepsItsOwnCopyOfTheLines() {
        List<OrderLine> lines = new ArrayList<>();
        lines.add(new OrderLine(pen, 1));
        Order order = new Order(lines);
        lines.clear();
        assertThat(order.lines()).hasSize(1);
    }
    @Test
    void rejectsAnEmptyOrder() {
        assertThatThrownBy(() -> new Order(List.of()))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Order must have lines");
    }
    @Test
    void standardFeeUnderThirtyEuro() {
        assertThat(orderWorth(2999).shippingInCents()).isEqualTo(500);
    }
    @Test
    void freeShippingFromFiftyEuro() {
        assertThat(orderWorth(5000).shippingInCents()).isEqualTo(0);
    }
    // TODO from 30 euro: reduced fee, 2 euro
    private Order orderWorth(int cents) {
        Product item = new Product("IT-1", "Item", cents);
        return new Order(List.of(new OrderLine(item, 1)));
    }
}
~~~

`src/main/java/com/shop/domain/Order.java`, passaggio intermedio («free»)

~~~java
package com.shop.domain;
import java.util.List;
public record Order(List<OrderLine> lines) {
    public Order {
        if (lines.isEmpty()) {
            throw new IllegalArgumentException("Order must have lines");
        }
        lines = List.copyOf(lines);
    }
    public int totalInCents() {
        return lines.stream().mapToInt(OrderLine::subtotalInCents).sum();
    }
    public int shippingInCents() {
        if (totalInCents() >= 5000) {
            return 0;
        }
        return 500;
    }
}
~~~

`src/main/java/com/shop/domain/Order.java`, passaggio intermedio («named»)

~~~java
package com.shop.domain;
import java.util.List;
public record Order(List<OrderLine> lines) {
    private static final int FREE_SHIPPING_FROM = 5000;
    private static final int STANDARD_FEE = 500;
    public Order {
        if (lines.isEmpty()) {
            throw new IllegalArgumentException("Order must have lines");
        }
        lines = List.copyOf(lines);
    }
    public int totalInCents() {
        return lines.stream().mapToInt(OrderLine::subtotalInCents).sum();
    }
    public int shippingInCents() {
        if (totalInCents() >= FREE_SHIPPING_FROM) {
            return 0;
        }
        return STANDARD_FEE;
    }
}
~~~

`src/main/java/com/shop/domain/Order.java`, passaggio intermedio («reduced»)

~~~java
package com.shop.domain;
import java.util.List;
public record Order(List<OrderLine> lines) {
    private static final int FREE_SHIPPING_FROM = 5000;
    private static final int STANDARD_FEE = 500;
    private static final int REDUCED_SHIPPING_FROM = 3000;
    private static final int REDUCED_FEE = 200;
    public Order {
        if (lines.isEmpty()) {
            throw new IllegalArgumentException("Order must have lines");
        }
        lines = List.copyOf(lines);
    }
    public int totalInCents() {
        return lines.stream().mapToInt(OrderLine::subtotalInCents).sum();
    }
    public int shippingInCents() {
        if (totalInCents() >= FREE_SHIPPING_FROM) {
            return 0;
        }
        if (totalInCents() >= REDUCED_SHIPPING_FROM) {
            return REDUCED_FEE;
        }
        return STANDARD_FEE;
    }
}
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `src/main/java/com/shop/domain/Order.java`, versione di partenza: lezione 37, file `src/main/java/com/shop/domain/Order.java`
- `src/main/java/com/shop/domain/OrderLine.java`: lezione 37
- `src/main/java/com/shop/domain/Product.java`: lezione 37
- `src/test/java/com/shop/domain/OrderTest.java`, versione di partenza: lezione 37, file `src/test/java/com/shop/domain/OrderTest.java`

## Esercizio 37b: la regola della spedizione

Obiettivo: Implementare la regola della spedizione di un ordine con le soglie dei 30 e dei 50 euro, confini compresi.

`Order` calcola già `totalInCents`.

**Completa `shippingInCents`**, la regola della lezione, in centesimi:

- sotto i `3000` la spedizione costa `500` (tariffa standard);
- da `3000` compresi fino a `4999` costa `200` (tariffa ridotta);
- da `5000` compresi in su è gratuita, cioè `0`.

La regola usa il totale di tutte le righe.

Fai attenzione ai **confini**: `3000` e `5000` appartengono alla fascia più alta.

Completa poi **`grandTotalInCents`**, che restituisce totale più spedizione richiamando i due metodi.

Gli ordini hanno almeno una riga e i prezzi sono positivi.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
import java.util.List;

public class Exercise {

    public record Product(String sku, String name, int priceInCents) {
        public Product {
            if (priceInCents <= 0) {
                throw new IllegalArgumentException("Price must be positive");
            }
        }
    }

    public record OrderLine(Product product, int quantity) {
        public OrderLine {
            if (quantity <= 0) {
                throw new IllegalArgumentException("Quantity must be positive");
            }
        }

        public int subtotalInCents() {
            return product.priceInCents() * quantity;
        }
    }

    public record Order(List<OrderLine> lines) {

        public Order {
            if (lines.isEmpty()) {
                throw new IllegalArgumentException("Order must have lines");
            }
            lines = List.copyOf(lines);
        }

        public int totalInCents() {
            return lines.stream().mapToInt(OrderLine::subtotalInCents).sum();
        }

        public int shippingInCents() {
            // TODO: completa questo blocco.
            // Suggerimento: Calcola il totale una volta sola: int total = totalInCents().
            // Con un primo if, se total >= 5000 restituisci 0. Con un secondo if, se total >= 3000 restituisci 200.
            // Alla fine restituisci 500. Prima la soglia più alta, poi la più bassa.
            return 0;
        }

        public int grandTotalInCents() {
            // TODO: completa questo blocco.
            // Suggerimento: Somma totalInCents() e shippingInCents(): richiama i due metodi, non ripetere la regola.
            return 0;
        }
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
import java.util.List;

public class Exercise {

    public record Product(String sku, String name, int priceInCents) {
        public Product {
            if (priceInCents <= 0) {
                throw new IllegalArgumentException("Price must be positive");
            }
        }
    }

    public record OrderLine(Product product, int quantity) {
        public OrderLine {
            if (quantity <= 0) {
                throw new IllegalArgumentException("Quantity must be positive");
            }
        }

        public int subtotalInCents() {
            return product.priceInCents() * quantity;
        }
    }

    public record Order(List<OrderLine> lines) {

        private static final int FREE_SHIPPING_FROM = 5000;
        private static final int REDUCED_SHIPPING_FROM = 3000;
        private static final int REDUCED_FEE = 200;
        private static final int STANDARD_FEE = 500;

        public Order {
            if (lines.isEmpty()) {
                throw new IllegalArgumentException("Order must have lines");
            }
            lines = List.copyOf(lines);
        }

        public int totalInCents() {
            return lines.stream().mapToInt(OrderLine::subtotalInCents).sum();
        }

        public int shippingInCents() {
            int total = totalInCents();
            if (total >= FREE_SHIPPING_FROM) {
                return 0;
            }
            if (total >= REDUCED_SHIPPING_FROM) {
                return REDUCED_FEE;
            }
            return STANDARD_FEE;
        }

        public int grandTotalInCents() {
            return totalInCents() + shippingInCents();
        }
    }
}
~~~

La lezione 37b costruisce la regola della spedizione con il TDD: prima il test, poi il codice. Qui i test sono già scritti e tu rendi verde `shippingInCents`: 500 centesimi sotto i 3000, 200 da 3000 a 4999, zero da 5000 in su. Poi `grandTotalInCents` somma totale e spedizione.

La soluzione calcola il totale una volta sola e confronta dalla soglia più alta alla più bassa: `>= 5000` restituisce 0, `>= 3000` restituisce 200, e in fondo resta 500. Il maggiore o uguale traduce "da 30 euro" e "da 50 euro", e fa appartenere 3000 e 5000 alla fascia più alta. L'ordine degli `if` conta, perché la soglia bassa verrebbe prima. `grandTotalInCents` richiama i due metodi senza ripetere la regola.

L'errore classico è il confine: con `>` al posto di `>=` falliscono `reducedFeeFromThirtyEuro` e `freeShippingFromFiftyEuro`. C'è anche il confine che la lezione non aveva provato: `reducedFeeJustUnderFiftyEuro` controlla 4999 e blocca chi sposta la soglia di un centesimo. Se scambi l'ordine degli `if`, un ordine da 5000 paga 200. Se guardi solo la prima riga, `shippingDependsOnTheTotalOfAllLines` fallisce, e se ignori la quantità fallisce `shippingCountsTheQuantityOfEachLine`. Chi scrive nel codice solo i valori d'esempio viene fermato da `ruleHoldsForEveryTotalUpToSixtyEuro`, che li prova tutti da 1 a 6000.

## Riepilogo

- Una lista dei test, poi un comportamento alla volta
- Rosso per il motivo giusto, verde con il minimo
- Refactoring solo con i test verdi
- Order.shippingInCents: 500, 200 o 0 centesimi
