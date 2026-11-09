# Lezione 61. RestClient e HTTP interface

## Punti chiave

### Chiamare un'altra API

- Il fornitore espone GET /supplier/stock/{productId}
- Nel laboratorio è un controller finto nella stessa app
- Il nostro endpoint compone catalogo e fornitore
- I test chiamano il fornitore finto via HTTP

### Un client dichiarativo

- Interfaccia con @HttpExchange e @GetExchange
- Spring genera l'implementazione con un RestClient
- @ImportHttpServices registra il gruppo supplier
- spring.http.serviceclient.supplier.base-url

### Cosa non serve

- WebClient e la programmazione reattiva
- Una libreria esterna per i client HTTP
- Un secondo progetto per il fornitore finto

## Codice della lezione

`src/main/java/com/shop/supplier/SupplierClient.java`

~~~java
package com.shop.supplier;

import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.service.annotation.GetExchange;
import org.springframework.web.service.annotation.HttpExchange;

@HttpExchange("/supplier")
public interface SupplierClient {
    @GetExchange("/stock/{productId}")
    SupplierStock stock(@PathVariable long productId);
}
~~~

`src/main/java/com/shop/supplier/SupplierStubController.java`

~~~java
package com.shop.supplier;

import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/supplier")
public class SupplierStubController {
    private static final Map<Long, Integer> STOCK = Map.of(1L, 12, 2L, 0, 3L, 4);

    @GetMapping("/stock/{productId}")
    public SupplierStock stock(@PathVariable long productId) {
        return new SupplierStock(productId, STOCK.getOrDefault(productId, 0));
    }
}
~~~

`src/main/java/com/shop/web/AvailabilityController.java`

~~~java
package com.shop.web;

import com.shop.catalog.Product;
import com.shop.catalog.ProductService;
import com.shop.supplier.SupplierClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class AvailabilityController {
    private final ProductService products;
    private final SupplierClient supplier;

    public AvailabilityController(ProductService products, SupplierClient supplier) {
        this.products = products;
        this.supplier = supplier;
    }

    @GetMapping("/api/products/{id}/availability")
    public AvailabilityResponse availability(@PathVariable long id) {
        Product product = products.find(id);
        int available = supplier.stock(id).available();
        return new AvailabilityResponse(product.id(), product.name(), available);
    }
}
~~~

`src/main/java/com/shop/ShopApplication.java`

~~~java
package com.shop;

import com.shop.supplier.SupplierClient;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.service.registry.ImportHttpServices;

@ImportHttpServices(group = "supplier", types = SupplierClient.class)
@SpringBootApplication
public class ShopApplication {
    public static void main(String[] args) {
        SpringApplication.run(ShopApplication.class, args);
    }
}
~~~

`src/main/resources/application.yml`

~~~yaml
spring:
  application:
    name: shop
  http:
    serviceclient:
      supplier:
        base-url: http://127.0.0.1:18091
server:
  address: 127.0.0.1
  port: 18091
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
            <artifactId>spring-boot-starter-restclient</artifactId>
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

`requests/availability-1.http`

~~~http
### Availability of product 1
GET http://127.0.0.1:18091/api/products/1/availability
Accept: application/json
~~~

`requests/availability-2.http`

~~~http
### Availability of product 2
GET http://127.0.0.1:18091/api/products/2/availability
Accept: application/json
~~~

`src/main/java/com/shop/supplier/SupplierStock.java`

~~~java
package com.shop.supplier;

public record SupplierStock(long productId, int available) {
}
~~~

`src/main/java/com/shop/web/AvailabilityResponse.java`

~~~java
package com.shop.web;

public record AvailabilityResponse(long id, String name, int available) {
}
~~~

`src/test/java/com/shop/supplier/SupplierClientTests.java`

~~~java
package com.shop.supplier;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.SpringBootTest.WebEnvironment;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.test.web.servlet.MockMvc;
import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest(webEnvironment = WebEnvironment.DEFINED_PORT)
@AutoConfigureMockMvc
class SupplierClientTests {
    @Autowired SupplierClient client;
    @Autowired MockMvc mvc;

    @Test
    void readsTheStockFromTheSupplier() {
        assertThat(client.stock(1)).isEqualTo(new SupplierStock(1, 12));
    }

    @Test
    void productWithoutStockHasZeroUnits() {
        assertThat(client.stock(2).available()).isZero();
    }

    @Test
    void availabilityCombinesCatalogAndSupplier() throws Exception {
        mvc.perform(get("/api/products/1/availability"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name").value("Keyboard"))
                .andExpect(jsonPath("$.available").value(12));
    }
}
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `.mvn/wrapper/maven-wrapper.properties`: lezione 46
- `src/main/java/com/shop/catalog/InMemoryProductRepository.java`: lezione 58
- `src/main/java/com/shop/catalog/Product.java`: lezione 57
- `src/main/java/com/shop/catalog/ProductNotFoundException.java`: lezione 57
- `src/main/java/com/shop/catalog/ProductPage.java`: lezione 58
- `src/main/java/com/shop/catalog/ProductRepository.java`: lezione 57
- `src/main/java/com/shop/catalog/ProductService.java`: lezione 58
- `src/main/java/com/shop/catalog/ProductSort.java`: lezione 58
- `src/main/java/com/shop/web/ApiErrorHandler.java`: lezione 57
- `src/main/java/com/shop/web/CreateProductRequest.java`: lezione 57
- `src/main/java/com/shop/web/ProductController.java`: lezione 58
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

- RestClient: la chiamata scritta passo per passo
- HTTP interface: la chiamata descritta da annotazioni
- Gruppo e indirizzo nella configurazione di Boot
- Stessi test verdi prima e dopo il cambio
- Chi usa il client non cambia
