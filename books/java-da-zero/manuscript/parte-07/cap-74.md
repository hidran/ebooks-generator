# Lezione 54. DTO con record e Jackson 3: separare API e dominio

## Punti chiave

### Dominio e contratto pubblico

- Il dominio contiene anche supplierCostInCents
- Restituire direttamente il dominio espone quel componente
- Il DTO di risposta sceglie i dati pubblici
- Il DTO di richiesta descrive ciò che il client può inviare

### Record per il contratto

- ProductResponse: id, name, priceInCents
- Costruttore canonico e accessori generati
- Mapping esplicito dal dominio
- Nessuna regola commerciale nel controller
- Nessuna libreria di mapping per tre campi

### Jackson 3 e Spring Boot 4

- JSON convertito tramite HttpMessageConverter
- Boot configura JsonMapper dalle dipendenze
- Package databind: tools.jackson.databind
- Record supportati senza costruttore vuoto o setter
- Le annotazioni Jackson restano in com.fasterxml.jackson.annotation

### Testare la rappresentazione

- Stato 200 e application/json
- Tre campi pubblici con tipi corretti
- supplierCostInCents assente
- Lettura JSON nel record con costruttore canonico
- Il dominio conserva i propri dati interni

## Codice della lezione

`src/main/java/com/shop/ProductController.java`

~~~java
package com.shop;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class ProductController {
    private final ProductCatalog catalog;

    public ProductController(ProductCatalog catalog) {
        this.catalog = catalog;
    }

    @GetMapping("/api/products/featured")
    public ProductResponse featured() {
        return ProductResponse.from(catalog.featured());
    }
}
~~~

`src/main/java/com/shop/ProductResponse.java`

~~~java
package com.shop;

public record ProductResponse(long id, String name, int priceInCents) {
    public static ProductResponse from(Product product) {
        return new ProductResponse(product.id(), product.name(), product.priceInCents());
    }
}
~~~

`src/test/java/com/shop/ProductJsonTests.java`

~~~java
package com.shop;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.test.web.servlet.MockMvc;
import tools.jackson.databind.json.JsonMapper;
import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class ProductJsonTests {
    @Autowired MockMvc mvc;
    @Autowired JsonMapper json;

    @Test
    void endpointExposesOnlyThePublicContract() throws Exception {
        mvc.perform(get("/api/products/featured"))
                .andExpect(status().isOk()).andExpect(content().contentTypeCompatibleWith("application/json"))
                .andExpect(jsonPath("$.id").value(1)).andExpect(jsonPath("$.name").value("Keyboard"))
                .andExpect(jsonPath("$.priceInCents").value(4900))
                .andExpect(jsonPath("$.supplierCostInCents").doesNotExist());
    }

    @Test
    void serializesTheRecordWithTypedValues() throws Exception {
        String text = json.writeValueAsString(new ProductResponse(1L, "Keyboard", 4900));
        var tree = json.readTree(text);
        assertEquals(3, tree.size());
        assertTrue(tree.get("priceInCents").isIntegralNumber());
        assertEquals(4900, tree.get("priceInCents").intValue());
    }

    @Test
    void readsTheRecordThroughItsCanonicalConstructor() throws Exception {
        ProductResponse dto = json.readValue(
                "{\"id\":1,\"name\":\"Keyboard\",\"priceInCents\":4900}", ProductResponse.class);
        assertEquals(new ProductResponse(1L, "Keyboard", 4900), dto);
    }

    @Test
    void mappingPreservesTheDomainObject() {
        Product product = new Product(1L, "Keyboard", 4900, 2100);
        assertEquals(new ProductResponse(1L, "Keyboard", 4900), ProductResponse.from(product));
        assertEquals(2100, product.supplierCostInCents());
    }
}
~~~

`requests/featured-after.http`

~~~http
### Featured after
GET http://127.0.0.1:18084/api/products/featured
Accept: application/json
~~~

`requests/featured-before.http`

~~~http
### Featured before
GET http://127.0.0.1:18084/api/products/featured
Accept: application/json
~~~

`src/main/java/com/shop/Product.java`

~~~java
package com.shop;

public record Product(long id, String name, int priceInCents, int supplierCostInCents) {
}
~~~

`src/main/java/com/shop/ProductCatalog.java`

~~~java
package com.shop;

import org.springframework.stereotype.Service;

@Service
public class ProductCatalog {
    public Product featured() {
        return new Product(1L, "Keyboard", 4900, 2100);
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
  port: 18084
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `.mvn/wrapper/maven-wrapper.properties`: lezione 46
- `pom.xml`: lezione 51
- `src/main/java/com/shop/ShopApplication.java`: lezione 52

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw package -DskipTests
java -jar target/shop-0.0.1-SNAPSHOT.jar
./mvnw test
./mvnw package
~~~

## Riepilogo

- Contratto API separato dal dominio
- Jackson 3 converte i record senza JSON manuale
- Mapping esplicito, piccolo e verificabile
- Quattro test e risposta reale senza il costo interno
