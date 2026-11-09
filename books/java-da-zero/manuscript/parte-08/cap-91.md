# Lezione 68. Quando non usare l'AOP

## Punti chiave

### Una regola nascosta

- Il prezzo deve essere positivo: è una regola del dominio
- Vive in PriceRuleAspect, lontano da Product e ProductService
- Il pointcut copre solo create: changePrice la salta
- Chi legge il servizio non sa che la regola esiste

### Prima e dopo: KISS

- Prima: aspetto, pointcut con args e binding dei parametri
- Dopo: cinque righe nel costruttore compatto di Product
- Ogni Product valido, da qualunque strada arrivi
- Una classe in meno e nessuna magia da spiegare

### Alternative più semplici

- Chiamata esplicita o regola nel dominio: la scelta di default
- Decorator: avvolge un solo bean attraverso la sua interfaccia
- Filter o HandlerInterceptor: richieste e risposte HTTP
- Micrometer @Observed o Actuator: metriche e tracce

### Quando un aspetto è giusto

- Interesse tecnico, non regola di business
- Lo stesso comportamento in molti punti
- Tempi, audit, transazioni, sicurezza dei metodi
- Pointcut preciso e documentato, testato come il resto

## Codice della lezione

`src/test/java/com/shop/catalog/PriceRuleTests.java`

~~~java
package com.shop.catalog;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.system.CapturedOutput;
import org.springframework.boot.test.system.OutputCaptureExtension;

@SpringBootTest
@ExtendWith(OutputCaptureExtension.class)
class PriceRuleTests {
    @Autowired
    ProductService service;

    @Test
    void createRejectsZeroPrice() {
        assertThrows(InvalidPriceException.class, () -> service.create("Mouse", 0));
    }

    @Test
    void changePriceRejectsZeroPrice() {
        assertThrows(InvalidPriceException.class, () -> service.changePrice(1, 0));
    }

    @Test
    void productRejectsZeroPrice() {
        assertThrows(InvalidPriceException.class, () -> new Product(1, "Mouse", 0));
    }

    @Test
    void validPriceIsAccepted() {
        assertEquals(2500, service.create("Mouse", 2500).priceInCents());
    }

    @Test
    void serviceCallsAreStillTimed(CapturedOutput output) {
        service.list();
        assertTrue(output.getOut().contains("ProductService.list() took"), "the timing aspect is gone");
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
        return repository.save(new Product(0, name, priceInCents));
    }

    public Product changePrice(long id, int newPriceInCents) {
        Product current = find(id);
        return repository.save(new Product(current.id(), current.name(), newPriceInCents));
    }
}
~~~

`src/main/java/com/shop/catalog/Product.java`

~~~java
package com.shop.catalog;

public record Product(long id, String name, int priceInCents) {
    public Product {
        if (priceInCents <= 0) {
            throw new InvalidPriceException(priceInCents);
        }
    }
}
~~~

`src/main/java/com/shop/catalog/InvalidPriceException.java`

~~~java
package com.shop.catalog;

public class InvalidPriceException extends RuntimeException {
    public InvalidPriceException(int priceInCents) {
        super("Price must be positive: " + priceInCents);
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
  port: 18098
logging:
  pattern:
    console: "%-5level %logger{0} : %msg%n"
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `.mvn/wrapper/maven-wrapper.properties`: lezione 46
- `pom.xml`: lezione 64
- `src/main/java/com/shop/ShopApplication.java`: lezione 52
- `src/main/java/com/shop/catalog/InMemoryProductRepository.java`: lezione 64
- `src/main/java/com/shop/catalog/ProductNotFoundException.java`: lezione 64
- `src/main/java/com/shop/catalog/ProductRepository.java`: lezione 57
- `src/main/java/com/shop/monitoring/TimingAspect.java`: lezione 65

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw test
rm src/main/java/com/shop/catalog/PriceRuleAspect.java
~~~

## Riepilogo

- Le regole del dominio stanno nel dominio
- Un aspetto nasconde il comportamento a chi legge
- KISS: la soluzione più semplice che funziona
- TimingAspect resta: è un vero interesse trasversale
