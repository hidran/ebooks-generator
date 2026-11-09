# Lezione 59. Versionamento delle API

## Punti chiave

### Una modifica che rompe

- I client di oggi leggono priceInCents
- La nuova app vuole un prezzo con valuta
- Aggiungere un campo è compatibile
- Rinominare o cambiare tipo rompe i client

### Dove mettere la versione

- Nel percorso: /api/v1/products
- In un header: API-Version
- In un parametro della query o del media type
- Scegliamo l'header; senza header vale 1.0

### Cosa non serve

- Un controller copiato per ogni versione
- Una versione su ogni endpoint
- Una libreria esterna di versionamento

## Codice della lezione

`src/main/resources/application.yml`

~~~yaml
spring:
  application:
    name: shop
  mvc:
    apiversion:
      use:
        header: API-Version
      default: 1.0
server:
  address: 127.0.0.1
  port: 18089
~~~

`src/main/java/com/shop/web/ProductResponseV2.java`

~~~java
package com.shop.web;

import com.shop.catalog.Product;

public record ProductResponseV2(long id, String name, PriceResponse price) {
    public static ProductResponseV2 from(Product product) {
        PriceResponse price = new PriceResponse(product.priceInCents(), "EUR");
        return new ProductResponseV2(product.id(), product.name(), price);
    }
}
~~~

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

    @GetMapping(path = "/{id}", version = "1.0")
    public ProductResponse find(@PathVariable long id) {
        return ProductResponse.from(service.find(id));
    }

    @GetMapping(path = "/{id}", version = "2.0")
    public ProductResponseV2 findV2(@PathVariable long id) {
        return ProductResponseV2.from(service.find(id));
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

`requests/read-default.http`

~~~http
### Product without a version
GET http://127.0.0.1:18089/api/products/1
Accept: application/json
~~~

`requests/read-v2.http`

~~~http
### Product, version 2
GET http://127.0.0.1:18089/api/products/1
Accept: application/json
API-Version: 2.0
~~~

`requests/read-v3.http`

~~~http
### Product, version 3
GET http://127.0.0.1:18089/api/products/1
Accept: application/json
API-Version: 3.0
~~~

`src/main/java/com/shop/web/PriceResponse.java`

~~~java
package com.shop.web;

public record PriceResponse(int amountInCents, String currency) {
}
~~~

`src/test/java/com/shop/web/ProductVersionTests.java`

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
class ProductVersionTests {
    @Autowired MockMvc mvc;

    @Test
    void requestWithoutAVersionGetsVersionOne() throws Exception {
        mvc.perform(get("/api/products/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.priceInCents").value(4900))
                .andExpect(jsonPath("$.price").doesNotExist());
    }

    @Test
    void versionOneKeepsThePriceInCents() throws Exception {
        mvc.perform(get("/api/products/1").header("API-Version", "1.0"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.priceInCents").value(4900));
    }

    @Test
    void versionTwoReturnsAPriceObject() throws Exception {
        mvc.perform(get("/api/products/1").header("API-Version", "2.0"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.price.amountInCents").value(4900))
                .andExpect(jsonPath("$.price.currency").value("EUR"))
                .andExpect(jsonPath("$.priceInCents").doesNotExist());
    }

    @Test
    void unsupportedVersionIsRejected() throws Exception {
        mvc.perform(get("/api/products/1").header("API-Version", "3.0"))
                .andExpect(status().isBadRequest());
    }
}
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `.mvn/wrapper/maven-wrapper.properties`: lezione 46
- `pom.xml`: lezione 55
- `src/main/java/com/shop/ShopApplication.java`: lezione 52
- `src/main/java/com/shop/catalog/InMemoryProductRepository.java`: lezione 58
- `src/main/java/com/shop/catalog/Product.java`: lezione 57
- `src/main/java/com/shop/catalog/ProductNotFoundException.java`: lezione 57
- `src/main/java/com/shop/catalog/ProductPage.java`: lezione 58
- `src/main/java/com/shop/catalog/ProductRepository.java`: lezione 57
- `src/main/java/com/shop/catalog/ProductService.java`: lezione 58
- `src/main/java/com/shop/catalog/ProductSort.java`: lezione 58
- `src/main/java/com/shop/web/ApiErrorHandler.java`: lezione 57
- `src/main/java/com/shop/web/CreateProductRequest.java`: lezione 57
- `src/main/java/com/shop/web/ProductPageResponse.java`: lezione 58
- `src/main/java/com/shop/web/ProductResponse.java`: lezione 57
- `src/test/java/com/shop/web/ProductApiTests.java`: lezione 58
- `src/test/java/com/shop/web/ProductListTests.java`: lezione 58

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw test
./mvnw package
java -jar target/shop-0.0.1-SNAPSHOT.jar
~~~

## Riepilogo

- Nuova versione solo per modifiche incompatibili
- spring.mvc.apiversion: header e versione predefinita
- version sulle annotazioni di mapping
- Versione sconosciuta: 400 con ProblemDetail
- I client esistenti non cambiano nulla
