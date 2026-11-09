# Lezione 73. Transazioni con @Transactional

## Punti chiave

### Una transazione: tutto o niente

- Più scritture, un solo esito: commit o rollback
- ACID: atomicità, consistenza, isolamento, durabilità
- Senza confine ogni save fa da sé
- Il confine giusto è il metodo del servizio

### Quali eccezioni annullano

- RuntimeException ed Error: rollback
- Eccezioni checked: commit, salvo rollbackFor
- Errori di dominio come eccezioni non controllate
- readOnly = true: niente flush, intenzione dichiarata

### Propagazione

- REQUIRED (default): si unisce a quella esistente
- REQUIRES_NEW: sospende e ne apre una nuova
- MANDATORY: pretende una transazione già aperta
- SUPPORTS, NOT_SUPPORTED, NEVER, NESTED: casi rari

### Livelli di isolamento

- READ_UNCOMMITTED: letture sporche
- READ_COMMITTED: default di PostgreSQL e H2
- REPEATABLE_READ: rilettura stabile
- SERIALIZABLE: come in fila, il più costoso

### Il proxy e KISS

- @Transactional passa da un proxy di Spring
- Una chiamata interna con this salta il proxy
- Solo sui metodi del servizio che sono casi d'uso
- Default finché non c'è un motivo per cambiarli

## Codice della lezione

`src/main/java/com/shop/order/OrderService.java`

~~~java
package com.shop.order;

import com.shop.catalog.ProductNotFoundException;
import com.shop.catalog.ProductRepository;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class OrderService {
    private final OrderRepository orders;
    private final ProductRepository products;

    public OrderService(OrderRepository orders, ProductRepository products) {
        this.orders = orders;
        this.products = products;
    }

    @Transactional
    public long place(List<OrderItem> items) {
        long orderId = orders.create();
        for (OrderItem item : items) {
            if (products.findById(item.productId()).isEmpty()) {
                throw new ProductNotFoundException(item.productId());
            }
            orders.addLine(orderId, item.productId(), item.quantity());
        }
        return orderId;
    }

    @Transactional(readOnly = true)
    public Order find(long id) {
        return orders.findById(id).orElseThrow(() -> new OrderNotFoundException(id));
    }
}
~~~

`src/test/java/com/shop/order/OrderServiceTests.java`

~~~java
package com.shop.order;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.shop.catalog.ProductNotFoundException;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.simple.JdbcClient;

@SpringBootTest
class OrderServiceTests {
    @Autowired
    OrderService service;
    @Autowired
    JdbcClient jdbc;

    @Test
    void placedOrderIsReadWithItsLines() {
        long id = service.place(List.of(new OrderItem(1, 2), new OrderItem(2, 1)));
        Order order = service.find(id);
        assertThat(order.status()).isEqualTo(OrderStatus.NEW);
        assertThat(order.totalInCents()).isEqualTo(12300);
    }

    @Test
    void failedOrderLeavesNothingBehind() {
        long ordersBefore = count("orders");
        long linesBefore = count("order_line");
        assertThatThrownBy(() -> service.place(List.of(new OrderItem(1, 1), new OrderItem(999, 1))))
                .isInstanceOf(ProductNotFoundException.class);
        assertThat(count("orders")).isEqualTo(ordersBefore);
        assertThat(count("order_line")).isEqualTo(linesBefore);
    }

    private long count(String table) {
        return jdbc.sql("SELECT COUNT(*) FROM " + table).query(Long.class).single();
    }
}
~~~

`pom.xml`

~~~xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>4.1.1</version>
        <relativePath/>
    </parent>
    <groupId>com.shop</groupId>
    <artifactId>shop</artifactId>
    <version>0.0.1-SNAPSHOT</version>
    <properties>
        <java.version>25</java.version>
    </properties>
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>com.h2database</groupId>
            <artifactId>h2</artifactId>
            <scope>runtime</scope>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
~~~

`src/main/java/com/shop/catalog/ProductJpaRepository.java`

~~~java
package com.shop.catalog;

import org.springframework.data.jpa.repository.JpaRepository;

public interface ProductJpaRepository extends JpaRepository<ProductEntity, Long> {
}
~~~

`src/main/java/com/shop/order/JpaOrderRepository.java`

~~~java
package com.shop.order;

import com.shop.catalog.ProductJpaRepository;
import java.util.Optional;
import org.springframework.stereotype.Repository;

@Repository
public class JpaOrderRepository implements OrderRepository {
    private final OrderJpaRepository orders;
    private final OrderLineJpaRepository lines;
    private final ProductJpaRepository products;

    public JpaOrderRepository(OrderJpaRepository orders, OrderLineJpaRepository lines, ProductJpaRepository products) {
        this.orders = orders;
        this.lines = lines;
        this.products = products;
    }

    @Override
    public long create() {
        return orders.save(new OrderEntity(OrderStatus.NEW)).getId();
    }

    @Override
    public void addLine(long orderId, long productId, int quantity) {
        OrderEntity order = orders.getReferenceById(orderId);
        lines.save(new OrderLineEntity(order, products.getReferenceById(productId), quantity));
    }

    @Override
    public Optional<Order> findById(long id) {
        return orders.findById(id).map(OrderEntity::toOrder);
    }
}
~~~

`src/main/java/com/shop/order/OrderEntity.java`

~~~java
package com.shop.order;

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
    @OneToMany(mappedBy = "order")
    @OrderBy("id")
    private List<OrderLineEntity> lines = new ArrayList<>();

    protected OrderEntity() {
    }

    OrderEntity(OrderStatus status) {
        this.status = status;
    }

    Long getId() {
        return id;
    }

    Order toOrder() {
        return new Order(id, status, lines.stream().map(OrderLineEntity::toOrderLine).toList());
    }
}
~~~

`src/main/java/com/shop/order/OrderItem.java`

~~~java
package com.shop.order;

public record OrderItem(long productId, int quantity) {
}
~~~

`src/main/java/com/shop/order/OrderJpaRepository.java`

~~~java
package com.shop.order;

import org.springframework.data.jpa.repository.JpaRepository;

interface OrderJpaRepository extends JpaRepository<OrderEntity, Long> {
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

    OrderLineEntity(OrderEntity order, ProductEntity product, int quantity) {
        this.order = order;
        this.product = product;
        this.quantity = quantity;
    }

    OrderLine toOrderLine() {
        Product item = product.toProduct();
        return new OrderLine(item.name(), item.priceInCents(), quantity);
    }
}
~~~

`src/main/java/com/shop/order/OrderLineJpaRepository.java`

~~~java
package com.shop.order;

import org.springframework.data.jpa.repository.JpaRepository;

interface OrderLineJpaRepository extends JpaRepository<OrderLineEntity, Long> {
}
~~~

`src/main/java/com/shop/order/OrderNotFoundException.java`

~~~java
package com.shop.order;

public class OrderNotFoundException extends RuntimeException {
    public OrderNotFoundException(long id) {
        super("Order " + id + " not found");
    }
}
~~~

`src/main/java/com/shop/order/OrderRepository.java`

~~~java
package com.shop.order;

import java.util.Optional;

public interface OrderRepository {
    long create();

    void addLine(long orderId, long productId, int quantity);

    Optional<Order> findById(long id);
}
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `.mvn/wrapper/maven-wrapper.properties`: lezione 46
- `src/main/java/com/shop/ShopApplication.java`: lezione 52
- `src/main/java/com/shop/catalog/JpaProductRepository.java`: lezione 70
- `src/main/java/com/shop/catalog/Product.java`: lezione 57
- `src/main/java/com/shop/catalog/ProductEntity.java`: lezione 72
- `src/main/java/com/shop/catalog/ProductNotFoundException.java`: lezione 64
- `src/main/java/com/shop/catalog/ProductRepository.java`: lezione 57
- `src/main/java/com/shop/order/Order.java`: lezione 72
- `src/main/java/com/shop/order/OrderLine.java`: lezione 72
- `src/main/java/com/shop/order/OrderStatus.java`: lezione 72
- `src/main/resources/application.yml`: lezione 71
- `src/main/resources/data.sql`: lezione 69

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw test
~~~

## Riepilogo

- Confine della transazione nel servizio
- Rollback su eccezione non controllata, verificato da un test
- readOnly per le letture con relazioni Lazy
- Propagazione e isolamento: default sensati
- Chiamate interne: niente proxy, niente transazione
