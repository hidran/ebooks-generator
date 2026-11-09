# Lezione 56. Errori standard con ProblemDetail

## Punti chiave

### Il client riceve un errore

- HTTP 400 dice che la richiesta non va bene
- Non dice quale campo correggere
- Il corpo dell'errore fa parte del contratto dell'API

### RFC 9457: Problem Details

- Media type: application/problem+json
- type: categoria stabile del problema
- title e status: nome leggibile e codice HTTP
- detail e instance: questa occorrenza
- Proprietà di estensione, per esempio errors

### ProblemDetail in Spring

- @RestControllerAdvice: un handler per tutti i controller
- Estende ResponseEntityExceptionHandler
- Override di handleMethodArgumentNotValid
- errors: un messaggio per ogni campo

### Messaggi sicuri, contratto stabile

- Niente stack trace, classi interne o dati di altri utenti
- type non cambia una volta pubblicato
- Successi invariati: 201 e Location
- KISS: una mappa, non una gerarchia di errori

## Codice della lezione

`src/test/java/com/shop/ProblemDetailTests.java`

~~~java
package com.shop;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.test.web.servlet.MockMvc;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class ProblemDetailTests {
    @Autowired MockMvc mvc;

    @Test
    void invalidFieldsReturnAnRfc9457Problem() throws Exception {
        mvc.perform(post("/api/products").contentType("application/json")
                        .content("{\"name\":\"   \",\"priceInCents\":0}"))
                .andExpect(status().isBadRequest())
                .andExpect(content().contentTypeCompatibleWith("application/problem+json"))
                .andExpect(jsonPath("$.type").value(
                        "https://api.shop.example/problems/validation-error"))
                .andExpect(jsonPath("$.title").value("Request validation failed"))
                .andExpect(jsonPath("$.status").value(400))
                .andExpect(jsonPath("$.detail").value("One or more fields are invalid."))
                .andExpect(jsonPath("$.errors.name").value("must not be blank"))
                .andExpect(jsonPath("$.errors.priceInCents").value("must be greater than 0"));
    }

    @Test
    void missingNameIdentifiesTheFieldToCorrect() throws Exception {
        mvc.perform(post("/api/products").contentType("application/json")
                        .content("{\"priceInCents\":2500}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.errors.name").value("must not be blank"));
    }
}
~~~

`src/main/java/com/shop/ApiErrorHandler.java`

~~~java
package com.shop;

import java.net.URI;
import java.util.Map;
import java.util.TreeMap;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
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

`requests/create-invalid-fields.http`

~~~http
### Invalid product fields
POST http://127.0.0.1:18086/api/products
Accept: application/problem+json
Accept-Language: en
Content-Type: application/json

{"name":"   ","priceInCents":0}
~~~

`requests/create-missing-name.http`

~~~http
### Missing product name
POST http://127.0.0.1:18086/api/products
Accept: application/problem+json
Accept-Language: en
Content-Type: application/json

{"priceInCents":2500}
~~~

`requests/create-valid.http`

~~~http
### Valid product
POST http://127.0.0.1:18086/api/products
Accept: application/json
Content-Type: application/json

{"name":"Mouse","priceInCents":2500}
~~~

`src/main/resources/application.yml`

~~~yaml
spring:
  application:
    name: shop
server:
  address: 127.0.0.1
  port: 18086
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `.mvn/wrapper/maven-wrapper.properties`: lezione 46
- `src/main/java/com/shop/CreateProductRequest.java`: lezione 55
- `src/main/java/com/shop/Product.java`: lezione 53
- `src/main/java/com/shop/ProductCatalog.java`: lezione 53
- `src/main/java/com/shop/ProductController.java`: lezione 55
- `src/main/java/com/shop/ShopApplication.java`: lezione 52
- `src/test/java/com/shop/ProductApiTests.java`: lezione 55

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw package -DskipTests
java -jar target/shop-0.0.1-SNAPSHOT.jar
./mvnw test
./mvnw package
~~~

## Riepilogo

- RFC 9457 dà una forma standard agli errori
- Un handler comune evita duplicazione nei controller
- type, title, detail ed errors guidano il client
- I test MockMvc verificano il contratto
