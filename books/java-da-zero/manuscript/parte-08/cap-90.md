# Lezione 67. Proxy e insidie

## Punti chiave

### Il proxy sta fuori

- Spring inietta una sottoclasse generata: ProductService$$SpringCGLIB$$0
- Una chiamata da un altro bean passa dal proxy e dall'advice
- this.create() parte dall'oggetto vero e salta il proxy
- Nessun errore e nessun avviso: l'advice semplicemente non viene eseguito

> Percorso: ProductImporter, poi Proxy, poi Advice, poi ProductService.

### Altre trappole dello stesso meccanismo

- Metodi private: il proxy non li vede
- Metodi final: niente advice, il metodo gira sul proxy con i campi null
- Spring 7 lo segnala con un WARN di CglibAopProxy all'avvio
- Classi final: Spring non riesce a creare il proxy e l'avvio fallisce
- Chiamate nel costruttore: il proxy non esiste ancora

### @Transactional usa lo stesso proxy

- La transazione si apre nell'advice del proxy
- Metodo transazionale chiamato con this: nessuna transazione nuova
- Metodo private o final: l'annotazione viene ignorata
- Stesso sintomo, stessa causa, stessa soluzione

### Le soluzioni

- KISS: spostare il metodo in un altro bean
- Iniettare il bean in se stesso: funziona, ma confonde
- AopContext.currentProxy(): lega il codice a Spring AOP
- Weaving AspectJ completo: troppo per questo problema

## Codice della lezione

`src/main/java/com/shop/catalog/ProductImporter.java`

~~~java
package com.shop.catalog;

import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class ProductImporter {
    private final ProductService productService;

    public ProductImporter(ProductService productService) {
        this.productService = productService;
    }

    public List<Product> importAll(List<ProductDraft> drafts) {
        return drafts.stream()
                .map(draft -> productService.create(draft.name(), draft.priceInCents()))
                .toList();
    }
}
~~~

`src/test/java/com/shop/catalog/ProductImportTests.java`

~~~java
package com.shop.catalog;

import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.aop.support.AopUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.system.CapturedOutput;
import org.springframework.boot.test.system.OutputCaptureExtension;

@SpringBootTest
@ExtendWith(OutputCaptureExtension.class)
class ProductImportTests {
    @Autowired
    ProductService service;

    @Autowired
    ProductImporter importer;

    @Test
    void createIsAudited(CapturedOutput output) {
        service.create("Mouse", 2500);
        assertTrue(output.getOut().contains("AUDIT product-created [Mouse, 2500]"), "create is not audited");
    }

    @Test
    void importAuditsEveryProduct(CapturedOutput output) {
        importer.importAll(List.of(new ProductDraft("Webcam", 5900), new ProductDraft("Headset", 7900)));
        assertTrue(output.getOut().contains("AUDIT product-created [Webcam, 5900]"), "Webcam is not audited");
        assertTrue(output.getOut().contains("AUDIT product-created [Headset, 7900]"), "Headset is not audited");
    }

    @Test
    void serviceIsAProxySubclass() {
        assertTrue(AopUtils.isCglibProxy(service), "the service is not a CGLIB proxy");
        assertNotEquals(ProductService.class, service.getClass());
    }
}
~~~

`src/main/java/com/shop/catalog/ProductDraft.java`

~~~java
package com.shop.catalog;

public record ProductDraft(String name, int priceInCents) {
}
~~~

`src/main/resources/application.yml`

~~~yaml
spring:
  application:
    name: shop
server:
  address: 127.0.0.1
  port: 18097
logging:
  pattern:
    console: "%-5level %logger{0} : %msg%n"
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `src/main/java/com/shop/catalog/ProductService.java`: lezione 66
- `.mvn/wrapper/maven-wrapper.properties`: lezione 46
- `pom.xml`: lezione 64
- `src/main/java/com/shop/ShopApplication.java`: lezione 52
- `src/main/java/com/shop/audit/AuditAspect.java`: lezione 66
- `src/main/java/com/shop/audit/Audited.java`: lezione 66
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

- Gli aspetti di Spring passano da un proxy
- Le chiamate interne con this saltano il proxy
- Private, final e costruttori restano fuori dagli aspetti
- @Transactional segue le stesse regole
- Un altro bean: la soluzione più semplice
