# Lezione 53. Progettare API REST: risorse, metodi e risposte HTTP

## Punti chiave

### Risorse e operazioni

- Collezione: /api/products
- Risorsa: /api/products/{id}
- GET legge senza modificare lo stato applicativo
- POST crea nella collezione
- DELETE rimuove la risorsa indicata

### Stato, intestazioni e corpo

- GET esistente: 200 e rappresentazione
- Risorsa assente: 404
- POST riuscito: 201, Location e rappresentazione
- DELETE riuscito: 204, senza corpo
- Media type non supportato: 415

### Correggere il contratto

- Prima: una creazione riuscita restituisce 200
- Test: creazione attesa con 201 e Location
- Dopo: ResponseEntity.created(location).body(product)
- La regola di creazione resta nel catalogo

### Proprietà dei metodi

- GET è safe e idempotente
- DELETE è idempotente rispetto all'effetto
- Due DELETE possono restituire stati diversi
- POST non offre idempotenza automatica
- La memoria del processo non è persistenza

## Codice della lezione

`src/main/java/com/shop/ProductController.java`

~~~java
package com.shop;

import java.net.URI;
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
    public ResponseEntity<Product> create(@RequestBody CreateProductRequest request) {
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

`requests/create-product.http`

~~~http
### Create product
POST http://127.0.0.1:18083/api/products
Accept: application/json
Content-Type: application/json

{"name":"Mouse","priceInCents":2500}
~~~

`requests/delete-again.http`

~~~http
### Delete again
DELETE http://127.0.0.1:18083/api/products/2
Accept: application/json
~~~

`requests/delete-product.http`

~~~http
### Delete product
DELETE http://127.0.0.1:18083/api/products/2
Accept: application/json
~~~

`requests/list-products.http`

~~~http
### List products
GET http://127.0.0.1:18083/api/products
Accept: application/json
~~~

`requests/read-deleted.http`

~~~http
### Read deleted
GET http://127.0.0.1:18083/api/products/2
Accept: application/json
~~~

`requests/read-product.http`

~~~http
### Read product
GET http://127.0.0.1:18083/api/products/2
Accept: application/json
~~~

`requests/unsupported-content.http`

~~~http
### Unsupported content
POST http://127.0.0.1:18083/api/products
Accept: application/json
Content-Type: text/plain

Mouse
~~~

`src/main/java/com/shop/CreateProductRequest.java`

~~~java
package com.shop;

public record CreateProductRequest(String name, int priceInCents) {
}
~~~

`src/main/java/com/shop/Product.java`

~~~java
package com.shop;

public record Product(long id, String name, int priceInCents) {
}
~~~

`src/main/java/com/shop/ProductCatalog.java`

~~~java
package com.shop;

import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;
import org.springframework.stereotype.Service;

@Service
public class ProductCatalog {
    private final ConcurrentHashMap<Long, Product> products = new ConcurrentHashMap<>();
    private final AtomicLong sequence = new AtomicLong(1);

    public ProductCatalog() {
        products.put(1L, new Product(1L, "Keyboard", 4900));
    }

    public List<Product> all() {
        return products.values().stream().sorted(Comparator.comparingLong(Product::id)).toList();
    }

    public Optional<Product> find(long id) {
        return Optional.ofNullable(products.get(id));
    }

    public Product create(String name, int priceInCents) {
        if (name == null || name.isBlank() || priceInCents < 0) {
            throw new IllegalArgumentException("Invalid product");
        }
        long id = sequence.incrementAndGet();
        Product product = new Product(id, name, priceInCents);
        products.put(id, product);
        return product;
    }

    public boolean delete(long id) {
        return products.remove(id) != null;
    }
}
~~~

`src/main/resources/application.yml`

~~~yaml
spring:
  application:
    name: shop
server:
  address: 127.0.0.1
  port: 18083
~~~

`src/test/java/com/shop/ProductApiTests.java`

~~~java
package com.shop;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.test.web.servlet.MockMvc;
import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class ProductApiTests {
    @Autowired MockMvc mvc;

    @Test
    void listsSeedProduct() throws Exception {
        mvc.perform(get("/api/products"))
                .andExpect(status().isOk()).andExpect(jsonPath("$[0].name").value("Keyboard"));
    }

    @Test
    void unknownProductIsNotFound() throws Exception {
        mvc.perform(get("/api/products/999"))
                .andExpect(status().isNotFound());
    }

    @Test
    void createsReadsAndDeletesAResource() throws Exception {
        String location = mvc.perform(post("/api/products").contentType("application/json")
                        .content("{\"name\":\"Mouse\",\"priceInCents\":2500}"))
                .andExpect(status().isCreated()).andExpect(header().string("Location", startsWith("/api/products/")))
                .andExpect(jsonPath("$.name").value("Mouse"))
                .andReturn().getResponse().getHeader("Location");
        mvc.perform(get(location)).andExpect(status().isOk())
                .andExpect(jsonPath("$.priceInCents").value(2500));
        mvc.perform(delete(location)).andExpect(status().isNoContent())
                .andExpect(content().string(""));
        mvc.perform(delete(location)).andExpect(status().isNotFound());
        mvc.perform(get(location)).andExpect(status().isNotFound());
    }

    @Test
    void postRejectsUnsupportedMediaType() throws Exception {
        mvc.perform(post("/api/products").contentType("text/plain").content("Mouse"))
                .andExpect(status().isUnsupportedMediaType());
    }
}
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `.mvn/wrapper/maven-wrapper.properties`: lezione 46
- `pom.xml`: lezione 51
- `src/main/java/com/shop/ShopApplication.java`: lezione 52

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw test
./mvnw package
java -jar target/shop-0.0.1-SNAPSHOT.jar
~~~

## Riepilogo

- Nomi di risorse e metodi HTTP rendono leggibile il contratto
- Creazione verificata tramite Location
- Eliminazione senza corpo, assenza con 404
- Quattro test e ciclo completo sul server reale
