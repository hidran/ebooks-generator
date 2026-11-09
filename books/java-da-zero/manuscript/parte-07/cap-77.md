# Lezione 57. Service layer e repository in memoria

## Punti chiave

### Un controller, troppe responsabilità

- Conserva i prodotti e assegna gli identificatori
- Applica la regola sul nome
- Traduce tutto in HTTP
- SRP: un solo motivo per cambiare

### Dipendere da una porta


> Percorso: ProductController, poi ProductService, poi ProductRepository.

- Il servizio dipende dall'interfaccia, non dalla mappa
- InMemoryProductRepository implementa la porta
- DIP: i dettagli dipendono dalle astrazioni

### Cosa non serve

- Un'interfaccia per un servizio con una sola implementazione
- Una libreria di mapping per tre campi
- Un controllo del valore nullo in ogni endpoint

## Codice della lezione

`src/main/java/com/shop/web/ProductController.java`

~~~java
package com.shop.web;

import com.shop.catalog.Product;
import com.shop.catalog.ProductService;
import jakarta.validation.Valid;
import java.net.URI;
import java.util.List;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

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
    public ResponseEntity<Void> delete(@PathVariable long id) {
        service.delete(id);
        return ResponseEntity.noContent().build();
    }
}
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
}
~~~

`src/main/java/com/shop/catalog/InMemoryProductRepository.java`

~~~java
package com.shop.catalog;

import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;
import org.springframework.stereotype.Repository;

@Repository
public class InMemoryProductRepository implements ProductRepository {
    private final Map<Long, Product> products = new ConcurrentHashMap<>();
    private final AtomicLong sequence = new AtomicLong(1);

    public InMemoryProductRepository() {
        products.put(1L, new Product(1L, "Keyboard", 4900));
    }

    @Override
    public List<Product> findAll() {
        return products.values().stream().sorted(Comparator.comparingLong(Product::id)).toList();
    }

    @Override
    public Optional<Product> findById(long id) {
        return Optional.ofNullable(products.get(id));
    }

    @Override
    public Product save(Product product) {
        long id = product.id() == 0 ? sequence.incrementAndGet() : product.id();
        Product stored = new Product(id, product.name(), product.priceInCents());
        products.put(id, stored);
        return stored;
    }

    @Override
    public boolean deleteById(long id) {
        return products.remove(id) != null;
    }
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
        return repository.save(new Product(0, name.strip(), priceInCents));
    }

    public void delete(long id) {
        if (!repository.deleteById(id)) {
            throw new ProductNotFoundException(id);
        }
    }
}
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
    protected ResponseEntity<Object> handleMethodArgumentNotValid(
            MethodArgumentNotValidException exception,
            HttpHeaders headers,
            HttpStatusCode status,
            WebRequest request) {
        Map<String, String> errors = new TreeMap<>();
        exception.getBindingResult().getFieldErrors().forEach(error ->
                errors.putIfAbsent(error.getField(), error.getDefaultMessage()));

        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
                status, "One or more fields are invalid.");
        problem.setType(URI.create("https://api.shop.example/problems/validation-error"));
        problem.setTitle("Request validation failed");
        problem.setProperty("errors", errors);

        return handleExceptionInternal(exception, problem, headers, status, request);
    }

    @ExceptionHandler(ProductNotFoundException.class)
    public ProblemDetail handleProductNotFound(ProductNotFoundException exception) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
                HttpStatus.NOT_FOUND, exception.getMessage());
        problem.setType(URI.create("https://api.shop.example/problems/product-not-found"));
        problem.setTitle("Product not found");
        return problem;
    }
}
~~~

`requests/read-missing.http`

~~~http
### Read missing product
GET http://127.0.0.1:18087/api/products/99
Accept: application/json
~~~

`requests/read-product.http`

~~~http
### Read product
GET http://127.0.0.1:18087/api/products/1
Accept: application/json
~~~

`src/main/java/com/shop/catalog/Product.java`

~~~java
package com.shop.catalog;

public record Product(long id, String name, int priceInCents) {
}
~~~

`src/main/java/com/shop/catalog/ProductNotFoundException.java`

~~~java
package com.shop.catalog;

public class ProductNotFoundException extends RuntimeException {
    public ProductNotFoundException(long id) {
        super("Product " + id + " does not exist.");
    }
}
~~~

`src/main/java/com/shop/web/CreateProductRequest.java`

~~~java
package com.shop.web;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;

public record CreateProductRequest(
        @NotBlank String name,
        @Positive int priceInCents
) {}
~~~

`src/main/java/com/shop/web/ProductResponse.java`

~~~java
package com.shop.web;

import com.shop.catalog.Product;

public record ProductResponse(long id, String name, int priceInCents) {
    public static ProductResponse from(Product product) {
        return new ProductResponse(product.id(), product.name(), product.priceInCents());
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
  port: 18087
~~~

`src/test/java/com/shop/web/ProductApiTests.java`

~~~java
package com.shop.web;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.test.web.servlet.MockMvc;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class ProductApiTests {
    @Autowired MockMvc mvc;

    @Test
    void listStartsWithTheKeyboard() throws Exception {
        mvc.perform(get("/api/products"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].name").value("Keyboard"));
    }

    @Test
    void existingProductIsFound() throws Exception {
        mvc.perform(get("/api/products/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.priceInCents").value(4900));
    }

    @Test
    void createdProductHasATrimmedName() throws Exception {
        mvc.perform(post("/api/products").contentType("application/json")
                        .content("{\"name\":\"  Mouse  \",\"priceInCents\":2500}"))
                .andExpect(status().isCreated())
                .andExpect(header().exists("Location"))
                .andExpect(jsonPath("$.name").value("Mouse"));
    }

    @Test
    void invalidProductReturnsAValidationProblem() throws Exception {
        mvc.perform(post("/api/products").contentType("application/json")
                        .content("{\"name\":\" \",\"priceInCents\":0}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.errors.name").value("must not be blank"));
    }

    @Test
    void deletedProductIsGone() throws Exception {
        String location = mvc.perform(post("/api/products").contentType("application/json")
                        .content("{\"name\":\"Monitor\",\"priceInCents\":18900}"))
                .andReturn().getResponse().getHeader("Location");
        mvc.perform(delete(location)).andExpect(status().isNoContent());
        mvc.perform(get(location)).andExpect(status().isNotFound());
    }

    @Test
    void unknownProductReturnsAProblemDetail() throws Exception {
        mvc.perform(get("/api/products/99"))
                .andExpect(status().isNotFound())
                .andExpect(content().contentTypeCompatibleWith("application/problem+json"))
                .andExpect(jsonPath("$.type").value(
                        "https://api.shop.example/problems/product-not-found"))
                .andExpect(jsonPath("$.title").value("Product not found"))
                .andExpect(jsonPath("$.detail").value("Product 99 does not exist."));
    }
}
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `.mvn/wrapper/maven-wrapper.properties`: lezione 46
- `pom.xml`: lezione 55
- `src/main/java/com/shop/ShopApplication.java`: lezione 52

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw test
./mvnw package
java -jar target/shop-0.0.1-SNAPSHOT.jar
~~~

## Riepilogo

- Controller sottile: HTTP e DTO
- ProductService: casi d'uso, regole e ProductNotFoundException
- ProductRepository è la porta, la mappa un dettaglio
- Prodotto assente: 404 con ProblemDetail
- Stessi test verdi prima e dopo il refactoring
