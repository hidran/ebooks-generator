# Lezione 71. Query derivate, @Query e proiezioni

## Punti chiave

### Leggere solo ciò che serve

- Filtrare in Java carica tutte le righe
- Ogni riga diventa un'entità gestita
- Le statistiche di Hibernate contano i caricamenti
- Il filtro va nella query, non nel codice

### Proiezioni: record o interfaccia

- Record: List&lt;ProductSummary&gt;, costruttore con i campi
- Interfaccia: soli getter, oggetto generato da Spring Data
- SELECT con le sole colonne richieste
- Nessuna entità nel contesto di persistenza

### KISS: la query più semplice che basta

- Nome breve e chiaro: query derivata
- Nome illeggibile o join: @Query con JPQL
- Funzioni specifiche del database: nativeQuery
- Niente Specification o Querydsl per filtri fissi

## Codice della lezione

`src/main/java/com/shop/catalog/ProductJpaRepository.java`

~~~java
package com.shop.catalog;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

interface ProductJpaRepository extends JpaRepository<ProductEntity, Long> {
    List<ProductEntity> findByNameContainingIgnoreCaseOrderByName(String text);
    @Query("select p from ProductEntity p where p.priceInCents between :min and :max"
            + " order by p.priceInCents")
    List<ProductEntity> findInPriceRange(int min, int max);
    List<ProductSummary> findByPriceInCentsLessThanEqualOrderByPriceInCents(int max);
}
~~~

`src/main/java/com/shop/catalog/JpaProductRepository.java`

~~~java
package com.shop.catalog;

import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Repository;

@Repository
public class JpaProductRepository implements ProductRepository {
    private final ProductJpaRepository jpa;

    public JpaProductRepository(ProductJpaRepository jpa) {
        this.jpa = jpa;
    }

    @Override
    public List<Product> findAll() {
        return jpa.findAll(Sort.by("id")).stream().map(ProductEntity::toProduct).toList();
    }

    @Override
    public Optional<Product> findById(long id) {
        return jpa.findById(id).map(ProductEntity::toProduct);
    }

    @Override
    public Product save(Product product) {
        return jpa.save(ProductEntity.from(product)).toProduct();
    }

    @Override
    public boolean deleteById(long id) {
        if (!jpa.existsById(id)) {
            return false;
        }
        jpa.deleteById(id);
        return true;
    }

    @Override
    public List<Product> search(String text) {
        return jpa.findByNameContainingIgnoreCaseOrderByName(text).stream()
                .map(ProductEntity::toProduct)
                .toList();
    }

    @Override
    public List<Product> findInPriceRange(int min, int max) {
        return jpa.findInPriceRange(min, max).stream().map(ProductEntity::toProduct).toList();
    }

    @Override
    public List<ProductSummary> priceList(int maxPriceInCents) {
        return jpa.findByPriceInCentsLessThanEqualOrderByPriceInCents(maxPriceInCents);
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
            <artifactId>spring-boot-starter-data-jpa-test</artifactId>
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

`src/main/java/com/shop/catalog/ProductRepository.java`

~~~java
package com.shop.catalog;

import java.util.List;
import java.util.Optional;

public interface ProductRepository {
    List<Product> findAll();

    Optional<Product> findById(long id);

    Product save(Product product);

    boolean deleteById(long id);

    List<Product> search(String text);

    List<Product> findInPriceRange(int min, int max);

    List<ProductSummary> priceList(int maxPriceInCents);
}
~~~

`src/main/java/com/shop/catalog/ProductService.java`

~~~java
package com.shop.catalog;

import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class ProductService {
    private final ProductRepository repository;

    public ProductService(ProductRepository repository) {
        this.repository = repository;
    }

    public List<Product> list() {
        return repository.findAll();
    }

    public Product find(long id) {
        return repository.findById(id).orElseThrow(() -> new ProductNotFoundException(id));
    }

    public Product create(String name, int priceInCents) {
        return repository.save(new Product(0, name, priceInCents));
    }

    public void delete(long id) {
        if (!repository.deleteById(id)) {
            throw new ProductNotFoundException(id);
        }
    }

    public List<Product> search(String text) {
        return repository.search(text);
    }

    public List<Product> inPriceRange(int min, int max) {
        return repository.findInPriceRange(min, max);
    }

    public List<ProductSummary> priceList(int maxPriceInCents) {
        return repository.priceList(maxPriceInCents);
    }
}
~~~

`src/main/java/com/shop/catalog/ProductSummary.java`

~~~java
package com.shop.catalog;

public record ProductSummary(String name, int priceInCents) {
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
~~~

`src/main/resources/data.sql`

~~~sql
INSERT INTO product (name, price_in_cents) VALUES ('Keyboard', 4900);
INSERT INTO product (name, price_in_cents) VALUES ('Mouse', 2500);
INSERT INTO product (name, price_in_cents) VALUES ('Monitor', 18900);
INSERT INTO product (name, price_in_cents) VALUES ('Webcam', 3900);
INSERT INTO product (name, price_in_cents) VALUES ('Laptop', 129900);
~~~

`src/test/java/com/shop/catalog/ProductQueriesTests.java`

~~~java
package com.shop.catalog;

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
@Import(JpaProductRepository.class)
class ProductQueriesTests {
    @Autowired
    JpaProductRepository products;
    @Autowired
    EntityManagerFactory entityManagerFactory;
    Statistics statistics;

    @BeforeEach
    void resetStatistics() {
        statistics = entityManagerFactory.unwrap(SessionFactory.class).getStatistics();
        statistics.clear();
    }

    @Test
    void searchMatchesPartOfTheNameIgnoringCase() {
        assertThat(products.search("MO")).extracting(Product::name).containsExactly("Monitor", "Mouse");
    }

    @Test
    void priceRangeReturnsTheMatchingProducts() {
        assertThat(products.findInPriceRange(2000, 5000)).extracting(Product::name)
                .containsExactly("Mouse", "Webcam", "Keyboard");
    }

    @Test
    void priceRangeLoadsOnlyTheMatchingRows() {
        products.findInPriceRange(2000, 5000);
        assertThat(statistics.getEntityLoadCount()).isEqualTo(3);
    }

    @Test
    void priceListReadsNoEntities() {
        assertThat(products.priceList(5000)).containsExactly(
                new ProductSummary("Mouse", 2500),
                new ProductSummary("Webcam", 3900),
                new ProductSummary("Keyboard", 4900));
        assertThat(statistics.getEntityLoadCount()).isZero();
    }
}
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `.mvn/wrapper/maven-wrapper.properties`: lezione 46
- `src/main/java/com/shop/ShopApplication.java`: lezione 52
- `src/main/java/com/shop/catalog/Product.java`: lezione 57
- `src/main/java/com/shop/catalog/ProductEntity.java`: lezione 70
- `src/main/java/com/shop/catalog/ProductNotFoundException.java`: lezione 64

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw test
~~~

## Riepilogo

- Query derivata: findByNameContainingIgnoreCaseOrderByName
- @Query JPQL: fascia di prezzo con parametri con nome
- Proiezione su record: listino senza entità
- Statistiche: da 5 a 3 entità, da 5 a 0 per il listino
- Porta e servizio invariati, quattro test verdi
