# Lezione 66. Pointcut e annotazioni personalizzate

## Punti chiave

### Un pointcut troppo largo

- execution(* com.shop.catalog.ProductService.*(..))
- Sceglie tutti i metodi, anche le letture
- Nel registro finisce il nome del metodo, non l'evento
- Un nuovo metodo viene registrato senza deciderlo

### Espressioni di pointcut

- execution(* com.shop..*Service.*(..)): firma dei metodi
- within(com.shop.catalog..*): tutte le classi di un package
- bean(productService): un bean per nome
- @annotation(com.shop.audit.Audited): metodi annotati
- Si combinano con &&, || e !

### Un'annotazione nostra

- @Target(ElementType.METHOD): solo sui metodi
- @Retention(RetentionPolicy.RUNTIME): visibile a Spring durante l'esecuzione
- value(): il nome dell'evento da registrare
- @annotation(audited) lega l'annotazione al parametro dell'advice

### Cosa non serve

- Nessun pointcut costruito sui nomi dei metodi
- Nessuna annotazione su ogni metodo: solo dove serve
- Nessun @Pointcut con nome se l'espressione si usa una volta
- Nessuna riflessione scritta a mano per leggere l'annotazione

## Codice della lezione

`src/test/java/com/shop/audit/AuditAspectTests.java`

~~~java
package com.shop.audit;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.shop.catalog.Product;
import com.shop.catalog.ProductNotFoundException;
import com.shop.catalog.ProductService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.system.CapturedOutput;
import org.springframework.boot.test.system.OutputCaptureExtension;

@SpringBootTest
@ExtendWith(OutputCaptureExtension.class)
class AuditAspectTests {
    @Autowired
    ProductService service;

    @Test
    void createIsAudited(CapturedOutput output) {
        service.create("Webcam", 5900);
        assertTrue(output.getOut().contains("AUDIT product-created [Webcam, 5900]"), "create is not audited");
    }

    @Test
    void deleteIsAudited(CapturedOutput output) {
        Product product = service.create("Headset", 7900);
        service.delete(product.id());
        assertTrue(output.getOut().contains("AUDIT product-deleted [" + product.id() + "]"), "delete is not audited");
    }

    @Test
    void readsAreNotAudited(CapturedOutput output) {
        service.list();
        service.find(1);
        assertFalse(output.getOut().contains("AUDIT"), "a read was audited");
    }

    @Test
    void failedDeleteIsNotAudited(CapturedOutput output) {
        assertThrows(ProductNotFoundException.class, () -> service.delete(99));
        assertFalse(output.getOut().contains("AUDIT"), "a failed delete was audited");
    }
}
~~~

`src/main/java/com/shop/audit/AuditAspect.java`

~~~java
package com.shop.audit;

import java.util.Arrays;
import org.aspectj.lang.JoinPoint;
import org.aspectj.lang.annotation.AfterReturning;
import org.aspectj.lang.annotation.Aspect;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Aspect
@Component
public class AuditAspect {
    private static final Logger log = LoggerFactory.getLogger(AuditAspect.class);
    @AfterReturning("@annotation(audited)")
    public void audit(JoinPoint joinPoint, Audited audited) {
        log.info("AUDIT {} {}", audited.value(), Arrays.toString(joinPoint.getArgs()));
    }
}
~~~

`src/main/java/com/shop/audit/Audited.java`

~~~java
package com.shop.audit;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface Audited {
    String value();
}
~~~

`src/main/java/com/shop/catalog/ProductService.java`

~~~java
package com.shop.catalog;

import com.shop.audit.Audited;
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

    @Audited("product-created")
    public Product create(String name, int priceInCents) {
        return repository.save(new Product(0, name, priceInCents));
    }

    @Audited("product-deleted")
    public void delete(long id) {
        if (!repository.deleteById(id)) {
            throw new ProductNotFoundException(id);
        }
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
  port: 18096
logging:
  pattern:
    console: "%-5level %logger{0} : %msg%n"
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `.mvn/wrapper/maven-wrapper.properties`: lezione 46
- `pom.xml`: lezione 64
- `src/main/java/com/shop/ShopApplication.java`: lezione 52
- `src/main/java/com/shop/catalog/InMemoryProductRepository.java`: lezione 64
- `src/main/java/com/shop/catalog/Product.java`: lezione 57
- `src/main/java/com/shop/catalog/ProductNotFoundException.java`: lezione 64
- `src/main/java/com/shop/catalog/ProductRepository.java`: lezione 57

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw test
~~~

## Riepilogo

- Il pointcut decide dove agisce l'aspetto
- execution, within, bean e @annotation si combinano
- Un'annotazione RUNTIME rende la scelta esplicita nel codice
- @AfterReturning registra solo le operazioni riuscite
