# Lezione 65. Il primo aspetto, log e tempi di esecuzione

## Punti chiave

### Tipi di advice

- @Before: prima della chiamata
- @AfterReturning e @AfterThrowing: dopo un successo o un errore
- @After: dopo, in ogni caso
- @Around: avvolge la chiamata e decide quando eseguirla

### @Around passo per passo

- ProceedingJoinPoint rappresenta la chiamata in corso
- proceed() esegue il metodo vero
- Restituire il suo risultato, altrimenti il chiamante riceve null o un errore
- finally: il tempo si registra anche se il metodo lancia un'eccezione

> Percorso: Inizio, poi proceed(), poi finally, poi Log SLF4J.

### Cosa non serve

- Nessun cronometro copiato in ogni metodo
- Nessuna libreria di metriche per un log di tempi
- Nessuna asserzione sulle durate reali nei test
- Il log di sviluppo non sostituisce il monitoraggio in produzione

## Codice della lezione

`src/test/java/com/shop/monitoring/TimingAspectTests.java`

~~~java
package com.shop.monitoring;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.shop.catalog.ProductNotFoundException;
import com.shop.catalog.ProductService;
import java.util.regex.Pattern;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.system.CapturedOutput;
import org.springframework.boot.test.system.OutputCaptureExtension;

@SpringBootTest
@ExtendWith(OutputCaptureExtension.class)
class TimingAspectTests {
    @Autowired
    ProductService service;

    @Test
    void logsTheExecutionTime(CapturedOutput output) {
        service.list();
        Pattern line = Pattern.compile("ProductService\\.list\\(\\) took \\d+ ms");
        assertTrue(line.matcher(output.getOut()).find(), "no timing line for list");
    }

    @Test
    void keepsTheReturnValue() {
        assertEquals("Keyboard", service.find(1).name());
    }

    @Test
    void logsTheTimeEvenWhenTheMethodFails(CapturedOutput output) {
        assertThrows(ProductNotFoundException.class, () -> service.find(99));
        assertTrue(output.getOut().contains("ProductService.find(..) took"), "no timing line for a failed find");
    }
}
~~~

`src/main/java/com/shop/monitoring/TimingAspect.java`

~~~java
package com.shop.monitoring;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Aspect
@Component
public class TimingAspect {
    private static final Logger log = LoggerFactory.getLogger(TimingAspect.class);
    @Around("execution(* com.shop.catalog.ProductService.*(..))")
    public Object measure(ProceedingJoinPoint joinPoint) throws Throwable {
        long start = System.nanoTime();
        try {
            return joinPoint.proceed();
        } finally {
            long elapsedMillis = (System.nanoTime() - start) / 1_000_000;
            log.info("{} took {} ms", joinPoint.getSignature().toShortString(), elapsedMillis);
        }
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
            <artifactId>spring-boot-starter-aspectj</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-webmvc-test</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-aspectj-test</artifactId>
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

`requests/list-products.http`

~~~http
### List products
GET http://127.0.0.1:18095/api/products
Accept: application/json
~~~

`requests/read-missing.http`

~~~http
### Read a product that does not exist
GET http://127.0.0.1:18095/api/products/99
Accept: application/json
~~~

`src/main/java/com/shop/web/ApiErrorHandler.java`

~~~java
package com.shop.web;

import com.shop.catalog.ProductNotFoundException;
import java.net.URI;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class ApiErrorHandler {
    @ExceptionHandler(ProductNotFoundException.class)
    public ProblemDetail handleNotFound(ProductNotFoundException exception) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, exception.getMessage());
        problem.setType(URI.create("https://api.shop.example/problems/product-not-found"));
        problem.setTitle("Product not found");
        return problem;
    }
}
~~~

`src/main/java/com/shop/web/ProductController.java`

~~~java
package com.shop.web;

import com.shop.catalog.ProductService;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
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
}
~~~

`src/main/resources/application.yml`

~~~yaml
spring:
  application:
    name: shop
server:
  address: 127.0.0.1
  port: 18095
logging:
  pattern:
    console: "%-5level %logger{0} : %msg%n"
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `.mvn/wrapper/maven-wrapper.properties`: lezione 46
- `src/main/java/com/shop/ShopApplication.java`: lezione 52
- `src/main/java/com/shop/catalog/InMemoryProductRepository.java`: lezione 64
- `src/main/java/com/shop/catalog/Product.java`: lezione 57
- `src/main/java/com/shop/catalog/ProductNotFoundException.java`: lezione 64
- `src/main/java/com/shop/catalog/ProductRepository.java`: lezione 57
- `src/main/java/com/shop/catalog/ProductService.java`: lezione 64
- `src/main/java/com/shop/web/ProductResponse.java`: lezione 57

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw test
./mvnw package
java -jar target/shop-0.0.1-SNAPSHOT.jar
~~~

## Riepilogo

- @Around avvolge la chiamata con ProceedingJoinPoint
- proceed() esegue il metodo e il suo risultato va restituito
- finally registra il tempo anche quando il metodo fallisce
- Test deterministici sul formato del log, mai sulla durata
