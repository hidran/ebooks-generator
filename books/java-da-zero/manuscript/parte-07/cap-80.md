# Lezione 60. Documentare con OpenAPI

## Punti chiave

### Un contratto per chi usa l'API

- Endpoint, parametri, risposte ed errori
- Un documento scritto a mano invecchia
- OpenAPI: formato standard in JSON o YAML
- springdoc lo genera dal codice

### springdoc per Spring Boot 4

- springdoc-openapi-starter-webmvc-ui 3.1.1
- Contratto in /v3/api-docs
- Pagina di consultazione in /swagger-ui/index.html
- Parametri, record e vincoli letti dal codice

### Cosa non serve

- Scrivere il contratto a mano
- Un'annotazione su ogni parametro
- api-docs e Swagger UI in produzione: si disattivano con springdoc

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
            <groupId>org.springdoc</groupId>
            <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
            <version>3.1.1</version>
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

`src/main/resources/application.yml`

~~~yaml
spring:
  application:
    name: shop
springdoc:
  default-produces-media-type: application/json
server:
  address: 127.0.0.1
  port: 18090
~~~

`src/main/java/com/shop/ShopApplication.java`

~~~java
package com.shop;

import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.info.Info;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@OpenAPIDefinition(info = @Info(title = "Shop API", version = "1.0",
        description = "Products of the Shop catalog"))
@SpringBootApplication
public class ShopApplication {
    public static void main(String[] args) {
        SpringApplication.run(ShopApplication.class, args);
    }
}
~~~

`src/main/java/com/shop/web/ProductController.java`

~~~java
package com.shop.web;

import com.shop.catalog.Product;
import com.shop.catalog.ProductService;
import com.shop.catalog.ProductSort;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import java.net.URI;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@Tag(name = "Products", description = "Read and change the product catalog")
@RestController
@RequestMapping("/api/products")
public class ProductController {
    private final ProductService service;

    public ProductController(ProductService service) {
        this.service = service;
    }

    @Operation(summary = "List products, one page at a time")
    @GetMapping
    public ProductPageResponse list(
            @RequestParam(defaultValue = "") String name,
            @RequestParam(defaultValue = "ID") ProductSort sort,
            @RequestParam(defaultValue = "0") @Min(0) int page,
            @RequestParam(defaultValue = "5") @Min(1) @Max(20) int size) {
        return ProductPageResponse.from(service.search(name, sort, page, size));
    }

    @Operation(summary = "Read one product")
    @ApiResponse(responseCode = "200", description = "The product")
    @ApiResponse(responseCode = "404", description = "Product not found",
            content = @Content(mediaType = "application/problem+json",
                    schema = @Schema(implementation = ProblemDetail.class)))
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

`requests/api-docs.http`

~~~http
### OpenAPI contract
GET http://127.0.0.1:18090/v3/api-docs
Accept: application/json
~~~

`requests/page-too-large.http`

~~~http
### Page too large
GET http://127.0.0.1:18090/api/products?size=100
Accept: application/json
~~~

`src/test/java/com/shop/web/OpenApiDocsTests.java`

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
class OpenApiDocsTests {
    @Autowired MockMvc mvc;

    @Test
    void contractHasTheShopTitle() throws Exception {
        mvc.perform(get("/v3/api-docs"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.info.title").value("Shop API"))
                .andExpect(jsonPath("$.info.version").value("1.0"));
    }

    @Test
    void listOperationHasASummary() throws Exception {
        mvc.perform(get("/v3/api-docs"))
                .andExpect(jsonPath("$.paths['/api/products'].get.summary")
                        .value("List products, one page at a time"));
    }

    @Test
    void readOperationDocumentsTheMissingProduct() throws Exception {
        mvc.perform(get("/v3/api-docs"))
                .andExpect(jsonPath("$.paths['/api/products/{id}'].get.responses['404'].description")
                        .value("Product not found"));
    }

    @Test
    void sizeLimitComesFromTheConstraints() throws Exception {
        mvc.perform(get("/v3/api-docs"))
                .andExpect(jsonPath("$.paths['/api/products'].get.parameters[?(@.name == 'size')].schema.maximum")
                        .value(20));
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
- `src/main/java/com/shop/web/ProductPageResponse.java`: lezione 58
- `src/main/java/com/shop/web/ProductResponse.java`: lezione 57
- `src/test/java/com/shop/web/ProductApiTests.java`: lezione 58
- `src/test/java/com/shop/web/ProductListTests.java`: lezione 58

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw test
./mvnw package -DskipTests
java -jar target/shop-0.0.1-SNAPSHOT.jar
./mvnw package
~~~

## Riepilogo

- Contratto OpenAPI generato dal codice
- @OpenAPIDefinition: titolo e versione
- @Tag e @Operation descrivono gruppi ed endpoint
- @ApiResponse documenta anche il 404 con ProblemDetail
- I test proteggono anche il contratto
