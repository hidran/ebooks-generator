# Lezione 64. AOP, i concetti

## Punti chiave

### Interessi trasversali

- Log, tempi, sicurezza, transazioni: servono ovunque
- Copiati in ogni metodo: codice sparso e mescolato
- Una copia dimenticata, un testo diverso
- La logica del servizio si legge peggio

### Il vocabolario dell'AOP

- Join point: un punto dell'esecuzione, per Spring una chiamata di metodo
- Pointcut: l'espressione che sceglie i join point
- Advice: il codice da eseguire, per esempio @Before
- Aspect: la classe che riunisce pointcut e advice

### Weaving e proxy

- Weaving: collegare l'aspetto al codice
- Spring lo fa all'avvio, creando un proxy
- Il proxy esegue l'advice, poi chiama il metodo vero

> Percorso: Chiamante, poi Proxy, poi Advice, poi ProductService.

### Cosa non serve

- Nessun compilatore AspectJ e nessun XML
- Nessun agente Java: bastano i proxy di Spring
- Boot 4: spring-boot-starter-aspectj (prima starter-aop)
- Nessun aspetto per una riga usata una volta

## Codice della lezione

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
        return repository.save(new Product(0, name, priceInCents));
    }

    public void delete(long id) {
        if (!repository.deleteById(id)) {
            throw new ProductNotFoundException(id);
        }
    }
}
~~~

`src/main/java/com/shop/monitoring/CallLoggingAspect.java`

~~~java
package com.shop.monitoring;

import org.aspectj.lang.JoinPoint;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.annotation.Before;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Aspect
@Component
public class CallLoggingAspect {
    private static final Logger log = LoggerFactory.getLogger(CallLoggingAspect.class);
    @Before("execution(* com.shop.catalog.ProductService.*(..))")
    public void logCall(JoinPoint joinPoint) {
        log.info("Calling {}", joinPoint.getSignature().toShortString());
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
            <artifactId>spring-boot-starter-aspectj</artifactId>
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

`src/main/java/com/shop/catalog/InMemoryProductRepository.java`

~~~java
package com.shop.catalog;

import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;
import org.springframework.stereotype.Repository;

@Repository
public class InMemoryProductRepository implements ProductRepository {
    private final ConcurrentHashMap<Long, Product> products = new ConcurrentHashMap<>();
    private final AtomicLong sequence = new AtomicLong();

    public InMemoryProductRepository() {
        save(new Product(0, "Keyboard", 4900));
        save(new Product(0, "Mouse", 2500));
        save(new Product(0, "Monitor", 18900));
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
        Product saved = new Product(id, product.name(), product.priceInCents());
        products.put(id, saved);
        return saved;
    }

    @Override
    public boolean deleteById(long id) {
        return products.remove(id) != null;
    }
}
~~~

`src/main/java/com/shop/catalog/ProductNotFoundException.java`

~~~java
package com.shop.catalog;

public class ProductNotFoundException extends RuntimeException {
    public ProductNotFoundException(long id) {
        super("Product " + id + " not found");
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
  port: 18094
logging:
  pattern:
    console: "%-5level %logger{0} : %msg%n"
~~~

`src/test/java/com/shop/catalog/ProductServiceLoggingTests.java`

~~~java
package com.shop.catalog;

import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.aop.support.AopUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.system.CapturedOutput;
import org.springframework.boot.test.system.OutputCaptureExtension;

@SpringBootTest
@ExtendWith(OutputCaptureExtension.class)
class ProductServiceLoggingTests {
    @Autowired
    ProductService service;

    @Test
    void listIsLogged(CapturedOutput output) {
        service.list();
        assertTrue(output.getOut().contains("Calling ProductService.list"), "list is not logged");
    }

    @Test
    void findIsLogged(CapturedOutput output) {
        service.find(1);
        assertTrue(output.getOut().contains("Calling ProductService.find"), "find is not logged");
    }

    @Test
    void createIsLogged(CapturedOutput output) {
        service.create("Webcam", 5900);
        assertTrue(output.getOut().contains("Calling ProductService.create"), "create is not logged");
    }

    @Test
    void deleteIsLogged(CapturedOutput output) {
        Product product = service.create("Headset", 7900);
        service.delete(product.id());
        assertTrue(output.getOut().contains("Calling ProductService.delete"), "delete is not logged");
    }

    @Test
    void serviceIsAProxy() {
        assertTrue(AopUtils.isAopProxy(service), "the service is not a proxy");
    }
}
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `.mvn/wrapper/maven-wrapper.properties`: lezione 46
- `src/main/java/com/shop/ShopApplication.java`: lezione 52
- `src/main/java/com/shop/catalog/Product.java`: lezione 57
- `src/main/java/com/shop/catalog/ProductRepository.java`: lezione 57

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw test
~~~

## Riepilogo

- Un interesse trasversale copiato si dimentica e diverge
- Pointcut sceglie, advice esegue, aspect li riunisce
- Spring applica l'aspetto con un proxy
- DRY: una sola definizione, cinque test verdi
