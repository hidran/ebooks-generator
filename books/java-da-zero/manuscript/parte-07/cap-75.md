# Lezione 55. Validation con Bean Validation

## Punti chiave

### Richiesta senza vincoli

- JSON convertito in CreateProductRequest
- Nome vuoto raggiunge il servizio e causa 500
- Prezzo zero passa senza un vincolo
- Quattro test: un passaggio, tre fallimenti attesi

### Jakarta Bean Validation

- spring-boot-starter-validation
- @NotBlank sul nome
- @Positive sul prezzo
- Provider: Hibernate Validator

### Attivare il controllo

- @Valid sul parametro @RequestBody
- Conversione JSON prima della validazione
- Validazione prima del metodo controller
- Vincolo violato: HTTP 400

### Verifica

- Nome e prezzo validi: 201 Created e Location
- Nome fatto di spazi: 400 Bad Request
- Prezzo zero: 400 Bad Request
- Nome assente: 400 Bad Request
- Quattro test verdi

## Codice della lezione

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
            <artifactId>spring-boot-starter</artifactId>
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

`src/main/java/com/shop/CreateProductRequest.java`

~~~java
package com.shop;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;

public record CreateProductRequest(
        @NotBlank String name,
        @Positive int priceInCents
) {}
~~~

`src/main/java/com/shop/ProductController.java`

~~~java
package com.shop;

import java.net.URI;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/products")
public class ProductController {
    private final ProductCatalog catalog;

    public ProductController(ProductCatalog catalog) {
        this.catalog = catalog;
    }

    @GetMapping
    public List<Product> all() {
        return catalog.all();
    }

    @GetMapping("/{id}")
    public ResponseEntity<Product> find(@PathVariable long id) {
        return ResponseEntity.of(catalog.find(id));
    }

    @PostMapping
    public ResponseEntity<Product> create(@Valid @RequestBody CreateProductRequest request) {
        Product product = catalog.create(request.name(), request.priceInCents());
        URI location = URI.create("/api/products/" + product.id());
        return ResponseEntity.created(location).body(product);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable long id) {
        return catalog.delete(id)
                ? ResponseEntity.noContent().build()
                : ResponseEntity.notFound().build();
    }
}
~~~

`requests/create-blank-name.http`

~~~http
### Blank product name
POST http://127.0.0.1:18085/api/products
Accept: application/json
Content-Type: application/json

{"name":"   ","priceInCents":2500}
~~~

`requests/create-missing-name.http`

~~~http
### Missing product name
POST http://127.0.0.1:18085/api/products
Accept: application/json
Content-Type: application/json

{"priceInCents":2500}
~~~

`requests/create-product.http`

~~~http
### Create product
POST http://127.0.0.1:18085/api/products
Accept: application/json
Content-Type: application/json

{"name":"Mouse","priceInCents":2500}
~~~

`requests/create-valid.http`

~~~http
### Valid product
POST http://127.0.0.1:18085/api/products
Accept: application/json
Content-Type: application/json

{"name":"Mouse","priceInCents":2500}
~~~

`requests/create-zero-price.http`

~~~http
### Zero price
POST http://127.0.0.1:18085/api/products
Accept: application/json
Content-Type: application/json

{"name":"Mouse","priceInCents":0}
~~~

`requests/delete-again.http`

~~~http
### Delete again
DELETE http://127.0.0.1:18085/api/products/2
Accept: application/json
~~~

`requests/delete-product.http`

~~~http
### Delete product
DELETE http://127.0.0.1:18085/api/products/2
Accept: application/json
~~~

`requests/list-products.http`

~~~http
### List products
GET http://127.0.0.1:18085/api/products
Accept: application/json
~~~

`requests/read-deleted.http`

~~~http
### Read deleted
GET http://127.0.0.1:18085/api/products/2
Accept: application/json
~~~

`requests/read-product.http`

~~~http
### Read product
GET http://127.0.0.1:18085/api/products/2
Accept: application/json
~~~

`requests/unsupported-content.http`

~~~http
### Unsupported content
POST http://127.0.0.1:18085/api/products
Accept: application/json
Content-Type: text/plain

Mouse
~~~

`src/main/resources/application.yml`

~~~yaml
spring:
  application:
    name: shop
server:
  address: 127.0.0.1
  port: 18085
~~~

`src/test/java/com/shop/ProductApiTests.java`

~~~java
package com.shop;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class ProductApiTests {
    @Autowired MockMvc mvc;

    @Test
    void validProductIsCreated() throws Exception {
        mvc.perform(post("/api/products").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"name\":\"Mouse\",\"priceInCents\":2500}"))
                .andExpect(status().isCreated());
    }

    @Test
    void blankNameIsRejected() throws Exception {
        mvc.perform(post("/api/products").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"name\":\"   \",\"priceInCents\":2500}"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void zeroPriceIsRejected() throws Exception {
        mvc.perform(post("/api/products").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"name\":\"Mouse\",\"priceInCents\":0}"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void missingNameIsRejected() throws Exception {
        mvc.perform(post("/api/products").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"priceInCents\":2500}"))
                .andExpect(status().isBadRequest());
    }
}
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `.mvn/wrapper/maven-wrapper.properties`: lezione 46
- `src/main/java/com/shop/Product.java`: lezione 53
- `src/main/java/com/shop/ProductCatalog.java`: lezione 53
- `src/main/java/com/shop/ShopApplication.java`: lezione 52

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw test
./mvnw package
java -jar target/shop-0.0.1-SNAPSHOT.jar
~~~

## Riepilogo

- Regole dichiarate sul DTO
- @Valid attiva la validazione al confine HTTP
- Controller e catalogo ricevono soltanto dati validi
- I vincoli impediscono dati non validi nel controller
