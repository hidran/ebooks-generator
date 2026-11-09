# Lezione 70. Entità e repository JPA

## Punti chiave

### Prima e dopo: inversione delle dipendenze

- Prima: InMemoryProductRepository implementa la porta
- Dopo: JpaProductRepository implementa la stessa porta
- ProductService non cambia, i test nemmeno

> Percorso: ProductService, poi ProductRepository, poi JpaProductRepository, poi ProductJpaRepository.

### Tre modelli, tre motivi per cambiare

- Product: il dominio, record immutabile senza annotazioni
- ProductEntity: la forma della tabella, regole JPA
- CreateProductRequest e ProductResponse: il contratto HTTP
- Il mapping esplicito tiene separati i tre mondi

### KISS: cosa non serve

- Nessun DAO generico: Spring Data genera i metodi CRUD
- Nessuna libreria di mapping per tre campi
- Nessuna annotazione JPA sul record di dominio
- Un solo adattatore per porta: niente codice morto

## Codice della lezione

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

    Product toProduct() {
        return new Product(id, name, priceInCents);
    }
}
~~~

`src/main/java/com/shop/catalog/ProductJpaRepository.java`

~~~java
package com.shop.catalog;

import org.springframework.data.jpa.repository.JpaRepository;

interface ProductJpaRepository extends JpaRepository<ProductEntity, Long> {
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
            <artifactId>spring-boot-starter-webmvc</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>
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
            <artifactId>spring-boot-starter-webmvc-test</artifactId>
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

`requests/create-product.http`

~~~http
### Create product
POST http://127.0.0.1:18100/api/products
Accept: application/json
Content-Type: application/json

{"name":"Webcam","priceInCents":3900}
~~~

`requests/list-products.http`

~~~http
### List products
GET http://127.0.0.1:18100/api/products
Accept: application/json
~~~

`src/main/java/com/shop/web/ApiErrorHandler.java`

~~~java
package com.shop.web;

import com.shop.catalog.ProductNotFoundException;
import java.net.URI;
import java.util.Map;
import java.util.TreeMap;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.WebRequest;
import org.springframework.web.servlet.mvc.method.annotation.ResponseEntityExceptionHandler;

@RestControllerAdvice
public class ApiErrorHandler extends ResponseEntityExceptionHandler {
    @Override
    protected ResponseEntity<Object> handleMethodArgumentNotValid(MethodArgumentNotValidException exception,
            HttpHeaders headers, HttpStatusCode status, WebRequest request) {
        Map<String, String> errors = new TreeMap<>();
        exception.getBindingResult().getFieldErrors()
                .forEach(error -> errors.putIfAbsent(error.getField(), error.getDefaultMessage()));
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(status, "One or more fields are invalid.");
        problem.setType(URI.create("https://api.shop.example/problems/validation-error"));
        problem.setTitle("Request validation failed");
        problem.setProperty("errors", errors);
        return handleExceptionInternal(exception, problem, headers, status, request);
    }

    @ExceptionHandler(ProductNotFoundException.class)
    public ProblemDetail handleNotFound(ProductNotFoundException exception) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, exception.getMessage());
        problem.setType(URI.create("https://api.shop.example/problems/product-not-found"));
        problem.setTitle("Product not found");
        return problem;
    }
}
~~~

`src/main/java/com/shop/web/CreateProductRequest.java`

~~~java
package com.shop.web;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;

public record CreateProductRequest(@NotBlank String name, @Positive int priceInCents) {
}
~~~

`src/main/java/com/shop/web/ProductController.java`

~~~java
package com.shop.web;

import com.shop.catalog.Product;
import com.shop.catalog.ProductService;
import jakarta.validation.Valid;
import java.net.URI;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/products")
public class ProductController {
    private final ProductService service;

    public ProductController(ProductService service) {
        this.service = service;
    }

    @GetMapping
    public List<ProductResponse> list() {
        return service.list().stream().map(ProductResponse::from).toList();
    }

    @GetMapping("/{id}")
    public ProductResponse find(@PathVariable long id) {
        return ProductResponse.from(service.find(id));
    }

    @PostMapping
    public ResponseEntity<ProductResponse> create(@Valid @RequestBody CreateProductRequest request) {
        Product product = service.create(request.name(), request.priceInCents());
        URI location = URI.create("/api/products/" + product.id());
        return ResponseEntity.created(location).body(ProductResponse.from(product));
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable long id) {
        service.delete(id);
    }
}
~~~

`src/main/java/com/shop/web/ProductResponse.java`

~~~java
package com.shop.web;

import com.shop.catalog.Product;

public record ProductResponse(long id, String name, int priceInCents) {
    static ProductResponse from(Product product) {
        return new ProductResponse(product.id(), product.name(), product.priceInCents());
    }
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
server:
  address: 127.0.0.1
  port: 18100
~~~

`src/test/java/com/shop/catalog/ProductPersistenceTests.java`

~~~java
package com.shop.catalog;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.simple.JdbcClient;

@SpringBootTest
class ProductPersistenceTests {
    @Autowired
    ProductService service;
    @Autowired
    JdbcClient jdbc;

    @Test
    void createdProductIsStoredInTheProductTable() {
        service.create("Headset", 5900);
        long rows = jdbc.sql("SELECT COUNT(*) FROM product WHERE name = 'Headset'").query(Long.class).single();
        assertThat(rows).isEqualTo(1);
    }
}
~~~

`src/test/java/com/shop/catalog/ProductServiceTests.java`

~~~java
package com.shop.catalog;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class ProductServiceTests {
    @Autowired
    ProductService service;

    @Test
    void listStartsWithTheDemoProducts() {
        assertThat(service.list()).extracting(Product::name).startsWith("Keyboard", "Mouse", "Monitor");
    }

    @Test
    void createAssignsAnIdThatFindReturns() {
        Product created = service.create("Webcam", 3900);
        assertThat(created.id()).isPositive();
        assertThat(service.find(created.id())).isEqualTo(created);
    }

    @Test
    void findOfAMissingProductThrows() {
        assertThatThrownBy(() -> service.find(999)).isInstanceOf(ProductNotFoundException.class);
    }

    @Test
    void deleteRemovesTheProduct() {
        Product created = service.create("Lamp", 2900);
        service.delete(created.id());
        assertThatThrownBy(() -> service.find(created.id())).isInstanceOf(ProductNotFoundException.class);
    }
}
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `src/main/java/com/shop/catalog/ProductService.java`: lezione 64
- `.mvn/wrapper/maven-wrapper.properties`: lezione 46
- `src/main/java/com/shop/ShopApplication.java`: lezione 52
- `src/main/java/com/shop/catalog/Product.java`: lezione 57
- `src/main/java/com/shop/catalog/ProductNotFoundException.java`: lezione 64
- `src/main/java/com/shop/catalog/ProductRepository.java`: lezione 57
- `src/main/resources/data.sql`: lezione 69

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw test
rm src/main/java/com/shop/catalog/InMemoryProductRepository.java
./mvnw package
java -jar target/shop-0.0.1-SNAPSHOT.jar
~~~

## Riepilogo

- @Entity, @Id e @GeneratedValue mappano la tabella product
- ProductJpaRepository estende JpaRepository
- JpaProductRepository implementa la porta e converte i modelli
- Repository in memoria eliminato, servizio invariato
- Cinque test verdi e dati reali su H2
