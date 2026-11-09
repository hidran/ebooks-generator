# Lezione 37. Il dominio dello Shop

## Punti chiave

### Nasce il progetto Shop

- Si parte dal centro dell'esagono: il dominio
- Le regole del negozio, in Java puro
- Nessuna libreria, nessun database
- Un progetto che terremo e faremo crescere

> Percorso: infrastructure, poi application, poi domain.

### Il modello del dominio

- Product: sku, nome, prezzo in centesimi maggiore di zero
- OrderLine: prodotto, quantità maggiore di zero, subtotale
- Order: almeno una riga, totale
- Record immutabili, regole nel costruttore compatto

> Percorso: Order, poi OrderLine, poi Product.

### Un dominio solido

- Valori immutabili: record e List.copyOf
- Regole nel costruttore: nessun oggetto non valido
- Comportamento vicino ai dati: subtotale e totale
- Java puro: test veloci con JUnit e AssertJ

## Codice della lezione

Il progetto parte dal modello Maven del corso: questi sono il suo `pom.xml` e il wrapper.

`pom.xml`: uguale a quello della lezione 27.

`.mvn/wrapper/maven-wrapper.properties`: uguale a quello della lezione 27.

`src/main/java/com/shop/domain/Product.java`

~~~java
package com.shop.domain;
public record Product(String sku, String name, int priceInCents) {
    public Product {
        if (priceInCents <= 0) {
            throw new IllegalArgumentException("Price must be positive");
        }
    }
}
~~~

`src/main/java/com/shop/domain/OrderLine.java`

~~~java
package com.shop.domain;
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
~~~

`src/main/java/com/shop/domain/Order.java`

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
}
~~~

## Esercizio 37: un dominio Shop immutabile

Obiettivo: Applicare invarianti di dominio e copie difensive a un ordine.

`Product` è già validato.

1. **Completa `OrderLine`**: quantità positiva, altrimenti `IllegalArgumentException`; `subtotal` restituisce prezzo × quantità.
2. **Completa `Order`**: rifiuta lista vuota con `IllegalArgumentException`, conserva una *copia immutabile* tramite `List.copyOf` e calcola `total` sommando i subtotali.

Gli elementi e la lista non sono `null`.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
import java.util.List;

public class Exercise {

    public record Product(String sku, int priceInCents) {
        public Product {
            if (priceInCents <= 0) {
                throw new IllegalArgumentException("Invalid price");
            }
        }
    }

    public record OrderLine(Product product, int quantity) {
        public OrderLine {
            // TODO: completa questo blocco.
            // Suggerimento: Nel costruttore compatto rifiuta quantity non positiva; Java assegna i componenti.
            // Completa il costruttore compatto qui.
        }

        public int subtotal() {
            // TODO: completa questo blocco.
            // Suggerimento: Leggi il prezzo da product.priceInCents() e usa quantity.
            return 0;
        }
    }

    public record Order(List<OrderLine> lines) {
        public Order {
            // TODO: completa questo blocco.
            // Suggerimento: Controlla prima lines.isEmpty(), poi assegna a lines una copia con List.copyOf.
            // La copia evita che cambiamenti alla lista originale modifichino l’ordine.
            // Completa il costruttore compatto qui.
        }

        public int total() {
            // TODO: completa questo blocco.
            // Suggerimento: Somma subtotal() di tutte le righe, con un ciclo oppure uno stream.
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

    public record Product(String sku, int priceInCents) {
        public Product {
            if (priceInCents <= 0) {
                throw new IllegalArgumentException("Invalid price");
            }
        }
    }

    public record OrderLine(Product product, int quantity) {
        public OrderLine {
            if (quantity <= 0) {
                throw new IllegalArgumentException("Invalid quantity");
            }
        }

        public int subtotal() {
            return product.priceInCents() * quantity;
        }
    }

    public record Order(List<OrderLine> lines) {
        public Order {
            if (lines.isEmpty()) {
                throw new IllegalArgumentException("Empty order");
            }
            lines = List.copyOf(lines);
        }

        public int total() {
            return lines.stream().mapToInt(OrderLine::subtotal).sum();
        }
    }
}
~~~

Vogliamo un dominio Shop in cui non si possano creare righe o ordini non validi, e in cui un ordine non cambi dopo la creazione.

Nel costruttore compatto di `OrderLine` rifiutiamo `quantity <= 0` con `IllegalArgumentException`. Java assegna poi i componenti da solo. `subtotal` moltiplica `product.priceInCents()` per `quantity`: il calcolo sta vicino ai dati, come abbiamo visto nella lezione 37.

Nel costruttore compatto di `Order` rifiutiamo la lista vuota. Poi riassegniamo il parametro: `lines = List.copyOf(lines)`. Nel costruttore compatto il parametro si può sostituire prima che Java lo copi nel campo, ed è proprio quello che ci serve. La copia ha due effetti. Chi ha creato l'ordine non può più cambiarlo modificando la sua lista originale. E la copia è immutabile, quindi nemmeno `order.lines()` permette di aggiungere o togliere righe. `total` somma i subtotali con `mapToInt(OrderLine::subtotal).sum()`.

L'errore più comune è dimenticare `List.copyOf`. Il test `protectsOrderFromExternalMutation` crea l'ordine con un `ArrayList`, poi lo svuota con `lines.clear()`. Senza copia, l'ordine si svuota con lui e `total` dà `0` invece di `100`. Lo stesso test vuole che `order.lines().clear()` lanci `UnsupportedOperationException`: con l'`ArrayList` originale non succederebbe. Un altro errore è controllare la quantità solo in `subtotal`: il test vuole l'eccezione già quando costruisci `new OrderLine(..., 0)`.

Un ciclo `for` che accumula i subtotali in un `int` è un'alternativa altrettanto corretta per `total`.

## Riepilogo

- Il progetto Shop nasce dal dominio: com.shop.domain
- Product, OrderLine e Order: record con le loro regole
- Il totale si calcola dove stanno i dati
- Tre test: totale, copia delle righe, ordine vuoto rifiutato
