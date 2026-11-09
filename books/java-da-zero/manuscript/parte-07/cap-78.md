# Lezione 58. Paginazione, ordinamento e filtri

## Punti chiave

### Liste senza limiti

- Dodici prodotti oggi, centomila domani
- Memoria e tempo per serializzare tutto
- La rete e il client pagano ogni byte
- Un solo client può rallentare tutti

### Pagina, ordinamento, filtro

- page da 0, size da 1 a 20, default 5
- sort soltanto tra ID, NAME e PRICE
- name filtra senza distinguere le maiuscole
- Risposta: content, page, size, totalElements, totalPages

### Cosa non serve

- Spring Data per paginare una lista in memoria
- Ordinamento su qualunque proprietà
- Link di navigazione nella risposta

## Codice della lezione

`src/main/java/com/shop/web/ProductController.java`

~~~java
package com.shop.web;

import com.shop.catalog.Product;
import com.shop.catalog.ProductService;
import com.shop.catalog.ProductSort;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import java.net.URI;
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
    public ProductPageResponse list(
            @RequestParam(defaultValue = "") String name,
            @RequestParam(defaultValue = "ID") ProductSort sort,
            @RequestParam(defaultValue = "0") @Min(0) int page,
            @RequestParam(defaultValue = "5") @Min(1) @Max(20) int size) {
        return ProductPageResponse.from(service.search(name, sort, page, size));
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

`src/main/java/com/shop/catalog/ProductSort.java`

~~~java
package com.shop.catalog;

import java.util.Comparator;

public enum ProductSort {
    ID(Comparator.comparingLong(Product::id)),
    NAME(Comparator.comparing(Product::name)),
    PRICE(Comparator.comparingInt(Product::priceInCents));

    private final Comparator<Product> comparator;

    ProductSort(Comparator<Product> comparator) {
        this.comparator = comparator;
    }

    public Comparator<Product> comparator() {
        return comparator;
    }
}
~~~

`src/main/java/com/shop/catalog/ProductPage.java`

~~~java
package com.shop.catalog;

import java.util.List;

public record ProductPage(List<Product> content, int page, int size, long totalElements) {
    public int totalPages() {
        return (int) ((totalElements + size - 1) / size);
    }
}
~~~

`src/main/java/com/shop/catalog/ProductService.java`

~~~java
package com.shop.catalog;

import java.util.List;
import java.util.Locale;
import org.springframework.stereotype.Service;

@Service
public class ProductService {
    private final ProductRepository repository;

    public ProductService(ProductRepository repository) {
        this.repository = repository;
    }

    public ProductPage search(String name, ProductSort sort, int page, int size) {
        String text = name.strip().toLowerCase(Locale.ROOT);
        List<Product> matching = repository.findAll().stream()
                .filter(product -> product.name().toLowerCase(Locale.ROOT).contains(text))
                .sorted(sort.comparator())
                .toList();
        List<Product> content = matching.stream()
                .skip((long) page * size).limit(size).toList();
        return new ProductPage(content, page, size, matching.size());
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

`requests/filter-by-name.http`

~~~http
### Filter by name
GET http://127.0.0.1:18088/api/products?name=mouse
Accept: application/json
~~~

`requests/list-products.http`

~~~http
### List products
GET http://127.0.0.1:18088/api/products
Accept: application/json
~~~

`requests/page-too-large.http`

~~~http
### Page too large
GET http://127.0.0.1:18088/api/products?size=100
Accept: application/json
~~~

`requests/sort-by-price.http`

~~~http
### Second page by price
GET http://127.0.0.1:18088/api/products?sort=PRICE&page=1&size=3
Accept: application/json
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
    private static final List<Product> DEMO_PRODUCTS = List.of(
            new Product(1, "Keyboard", 4900), new Product(2, "Mouse", 2500),
            new Product(3, "Monitor", 18900), new Product(4, "Webcam", 5900),
            new Product(5, "Headset", 7900), new Product(6, "Laptop stand", 3900),
            new Product(7, "USB hub", 2900), new Product(8, "Desk lamp", 3400),
            new Product(9, "Microphone", 9900), new Product(10, "Speakers", 6900),
            new Product(11, "Mouse pad", 1500), new Product(12, "Docking station", 15900));

    private final Map<Long, Product> products = new ConcurrentHashMap<>();
    private final AtomicLong sequence = new AtomicLong(DEMO_PRODUCTS.size());

    public InMemoryProductRepository() {
        DEMO_PRODUCTS.forEach(product -> products.put(product.id(), product));
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

`src/main/java/com/shop/web/ProductPageResponse.java`

~~~java
package com.shop.web;

import com.shop.catalog.ProductPage;
import java.util.List;

public record ProductPageResponse(
        int page, int size, long totalElements, int totalPages, List<ProductResponse> content) {
    public static ProductPageResponse from(ProductPage page) {
        List<ProductResponse> content = page.content().stream().map(ProductResponse::from).toList();
        return new ProductPageResponse(
                page.page(), page.size(), page.totalElements(), page.totalPages(), content);
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
  port: 18088
~~~

`src/test/java/com/shop/web/ProductApiTests.java`

~~~java
package com.shop.web;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.web.servlet.MockMvc;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@DirtiesContext
class ProductApiTests {
    @Autowired MockMvc mvc;

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

`src/test/java/com/shop/web/ProductListTests.java`

~~~java
package com.shop.web;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.test.web.servlet.MockMvc;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class ProductListTests {
    @Autowired MockMvc mvc;

    @Test
    void firstPageHasFiveProductsAndTheTotals() throws Exception {
        mvc.perform(get("/api/products"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content.length()").value(5))
                .andExpect(jsonPath("$.totalElements").value(12))
                .andExpect(jsonPath("$.totalPages").value(3));
    }

    @Test
    void sortsByPrice() throws Exception {
        mvc.perform(get("/api/products").param("sort", "PRICE").param("size", "3"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content[0].name").value("Mouse pad"))
                .andExpect(jsonPath("$.content[1].name").value("Mouse"))
                .andExpect(jsonPath("$.content[2].name").value("USB hub"));
    }

    @Test
    void filtersByName() throws Exception {
        mvc.perform(get("/api/products").param("name", "mouse"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(2));
    }

    @Test
    void rejectsAPageThatIsTooLarge() throws Exception {
        mvc.perform(get("/api/products").param("size", "100"))
                .andExpect(status().isBadRequest())
                .andExpect(content().contentTypeCompatibleWith("application/problem+json"));
    }
}
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `.mvn/wrapper/maven-wrapper.properties`: lezione 46
- `pom.xml`: lezione 55
- `src/main/java/com/shop/ShopApplication.java`: lezione 52
- `src/main/java/com/shop/catalog/Product.java`: lezione 57
- `src/main/java/com/shop/catalog/ProductNotFoundException.java`: lezione 57
- `src/main/java/com/shop/catalog/ProductRepository.java`: lezione 57
- `src/main/java/com/shop/web/ApiErrorHandler.java`: lezione 57
- `src/main/java/com/shop/web/CreateProductRequest.java`: lezione 57
- `src/main/java/com/shop/web/ProductResponse.java`: lezione 57

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw package -DskipTests
java -jar target/shop-0.0.1-SNAPSHOT.jar
./mvnw test
./mvnw package
~~~

## Riepilogo

- Un elenco pubblico ha sempre un limite
- Parametri con valori predefiniti e vincoli
- Ordinamento da un elenco chiuso di valori
- Un record descrive la pagina e i totali
- size oltre il limite: 400 con ProblemDetail
