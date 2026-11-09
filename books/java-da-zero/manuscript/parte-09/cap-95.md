# Lezione 72. Relazioni e problema N+1

## Punti chiave

### Relazioni tra entità

- @OneToMany(mappedBy): l'ordine conosce le sue righe
- @ManyToOne: la riga punta a ordine e prodotto
- La chiave esterna sta nella tabella order_line
- FetchType.LAZY: la relazione si carica quando serve

> Percorso: OrderEntity, poi OrderLineEntity, poi ProductEntity.

### Il problema N+1

- 1 SELECT per i tre ordini
- 3 SELECT per le righe, una per ordine
- 5 SELECT per i prodotti diversi
- Totale misurato: 9 statement invece di 1

### Fetch join o @EntityGraph

- JPQL: left join fetch o.lines e l.product
- @EntityGraph(attributePaths = {"lines", "lines.product"})
- Una sola SELECT con le join
- show-sql e format_sql attivi mentre sviluppiamo

### KISS: carichiamo ciò che usiamo

- LAZY sulle @ManyToOne, che di default sono EAGER
- Fetch join solo nelle query che usano le righe
- EAGER ovunque sposta il problema, non lo risolve
- open-in-view disattivato: nessuna query nascosta

## Codice della lezione

`src/main/java/com/shop/order/OrderEntity.java`

~~~java
package com.shop.order;

import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.OneToMany;
import jakarta.persistence.OrderBy;
import jakarta.persistence.Table;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "orders")
public class OrderEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private OrderStatus status;
    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL, orphanRemoval = true)
    @OrderBy("id")
    private List<OrderLineEntity> lines = new ArrayList<>();

    protected OrderEntity() {
    }

    Order toOrder() {
        return new Order(id, status, lines.stream().map(OrderLineEntity::toOrderLine).toList());
    }
}
~~~

`src/main/java/com/shop/order/OrderLineEntity.java`

~~~java
package com.shop.order;

import com.shop.catalog.Product;
import com.shop.catalog.ProductEntity;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

@Entity
@Table(name = "order_line")
public class OrderLineEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "order_id")
    private OrderEntity order;
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "product_id")
    private ProductEntity product;
    private int quantity;

    protected OrderLineEntity() {
    }

    OrderLine toOrderLine() {
        Product item = product.toProduct();
        return new OrderLine(item.name(), item.priceInCents(), quantity);
    }
}
~~~

`src/main/java/com/shop/order/JpaOrderRepository.java`

~~~java
package com.shop.order;

import java.util.List;
import org.springframework.stereotype.Repository;

@Repository
public class JpaOrderRepository implements OrderRepository {
    private final OrderJpaRepository jpa;

    public JpaOrderRepository(OrderJpaRepository jpa) {
        this.jpa = jpa;
    }

    @Override
    public List<Order> findAll() {
        return jpa.findAllWithLines().stream().map(OrderEntity::toOrder).toList();
    }
}
~~~

`src/main/java/com/shop/order/OrderJpaRepository.java`

~~~java
package com.shop.order;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

interface OrderJpaRepository extends JpaRepository<OrderEntity, Long> {
    @Query("select o from OrderEntity o left join fetch o.lines l"
            + " left join fetch l.product order by o.id")
    List<OrderEntity> findAllWithLines();
}
~~~

`src/main/java/com/shop/catalog/ProductEntity.java`

~~~java
package com.shop.catalog;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "product")
public class ProductEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @Column(nullable = false, length = 100)
    private String name;
    private int priceInCents;

    protected ProductEntity() {
    }

    private ProductEntity(Long id, String name, int priceInCents) {
        this.id = id;
        this.name = name;
        this.priceInCents = priceInCents;
    }

    static ProductEntity from(Product product) {
        Long id = product.id() == 0 ? null : product.id();
        return new ProductEntity(id, product.name(), product.priceInCents());
    }

    public Product toProduct() {
        return new Product(id, name, priceInCents);
    }
}
~~~

`src/main/java/com/shop/order/Order.java`

~~~java
package com.shop.order;

import java.util.List;

public record Order(long id, OrderStatus status, List<OrderLine> lines) {
    public int totalInCents() {
        return lines.stream().mapToInt(OrderLine::subtotalInCents).sum();
    }
}
~~~

`src/main/java/com/shop/order/OrderLine.java`

~~~java
package com.shop.order;

public record OrderLine(String productName, int unitPriceInCents, int quantity) {
    public int subtotalInCents() {
        return unitPriceInCents * quantity;
    }
}
~~~

`src/main/java/com/shop/order/OrderRepository.java`

~~~java
package com.shop.order;

import java.util.List;

public interface OrderRepository {
    List<Order> findAll();
}
~~~

`src/main/java/com/shop/order/OrderStatus.java`

~~~java
package com.shop.order;

public enum OrderStatus {
    NEW, PAID, SHIPPED, CANCELLED
}
~~~

`src/main/resources/application.yml`

~~~yaml
spring:
  application:
    name: shop
  jpa:
    defer-datasource-initialization: true
    open-in-view: false
    show-sql: true
    properties:
      hibernate:
        format_sql: true
~~~

`src/main/resources/data.sql`

~~~sql
INSERT INTO product (name, price_in_cents) VALUES ('Keyboard', 4900);
INSERT INTO product (name, price_in_cents) VALUES ('Mouse', 2500);
INSERT INTO product (name, price_in_cents) VALUES ('Monitor', 18900);
INSERT INTO product (name, price_in_cents) VALUES ('Webcam', 3900);
INSERT INTO product (name, price_in_cents) VALUES ('Laptop', 129900);
INSERT INTO orders (status) VALUES ('NEW');
INSERT INTO orders (status) VALUES ('PAID');
INSERT INTO orders (status) VALUES ('SHIPPED');
INSERT INTO order_line (order_id, product_id, quantity) VALUES (1, 1, 1);
INSERT INTO order_line (order_id, product_id, quantity) VALUES (1, 2, 2);
INSERT INTO order_line (order_id, product_id, quantity) VALUES (2, 3, 1);
INSERT INTO order_line (order_id, product_id, quantity) VALUES (2, 4, 1);
INSERT INTO order_line (order_id, product_id, quantity) VALUES (3, 5, 1);
INSERT INTO order_line (order_id, product_id, quantity) VALUES (3, 2, 1);
~~~

`src/test/java/com/shop/order/OrderRepositoryTests.java`

~~~java
package com.shop.order;

import static org.assertj.core.api.Assertions.assertThat;

import jakarta.persistence.EntityManagerFactory;
import org.hibernate.SessionFactory;
import org.hibernate.stat.Statistics;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.data.jpa.test.autoconfigure.DataJpaTest;
import org.springframework.context.annotation.Import;

@DataJpaTest(properties = "spring.jpa.properties.hibernate.generate_statistics=true")
@Import(JpaOrderRepository.class)
class OrderRepositoryTests {
    @Autowired
    JpaOrderRepository orders;
    @Autowired
    EntityManagerFactory entityManagerFactory;
    Statistics statistics;

    @BeforeEach
    void resetStatistics() {
        statistics = entityManagerFactory.unwrap(SessionFactory.class).getStatistics();
        statistics.clear();
    }

    @Test
    void findAllMapsOrdersWithTheirLines() {
        assertThat(orders.findAll()).extracting(Order::totalInCents).containsExactly(9900, 22800, 132400);
    }

    @Test
    void findAllUsesASingleQuery() {
        orders.findAll();
        assertThat(statistics.getPrepareStatementCount()).isEqualTo(1);
    }
}
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `.mvn/wrapper/maven-wrapper.properties`: lezione 46
- `pom.xml`: lezione 71
- `src/main/java/com/shop/ShopApplication.java`: lezione 52
- `src/main/java/com/shop/catalog/Product.java`: lezione 57

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw test
~~~

## Riepilogo

- Ordini, righe e prodotti mappati con @OneToMany e @ManyToOne
- N+1 reso visibile con show-sql e misurato: 9 statement
- Fetch join in JPQL: 1 statement
- Dominio e porta invariati, due test verdi
