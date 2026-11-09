# Lezione 51. Test unitari, slice MVC e contesto Spring Boot

## Punti chiave

### Scegliere il perimetro del test

- Unitario: regola Java, nessun contesto Spring
- Slice MVC: contratto HTTP e collaboratore sostituito
- @SpringBootTest: contesto applicativo e collegamenti reali
- Non usare il contesto completo per ogni controllo

### Un caso limite concreto

- Spedizione: 490 sotto 5000 centesimi
- Spedizione gratuita da 5000 inclusi
- Importi negativi rifiutati
- Il test alla soglia scopre &gt; al posto di &gt;=

### Slice MVC

- @WebMvcTest(QuoteController.class)
- MockMvc esegue richieste senza server reale
- @MockitoBean sostituisce ShippingService
- Verificare parametro, risposta e delega
- Il servizio non viene validato tramite il suo mock

### Contesto completo

- @SpringBootTest trova la configurazione principale
- Controller collegato al vero ShippingService
- Ambiente web predefinito MOCK, senza porta reale
- Un collegamento reale può fallire anche con unitari verdi

### Piramide dei test

- Molti test rapidi delle regole
- Meno test dei confini e delle integrazioni
- Pochi controlli ampi dei percorsi importanti
- Sei test con responsabilità esplicite

## Codice della lezione

`src/main/java/com/shop/ShippingService.java`

~~~java
package com.shop;

import org.springframework.stereotype.Service;

@Service
public class ShippingService {
    public int fee(int subtotalInCents) {
        if (subtotalInCents < 0) {
            throw new IllegalArgumentException("Subtotal must be non-negative");
        }
        return subtotalInCents >= 5000 ? 0 : 490;
    }
}
~~~

`src/test/java/com/shop/QuoteControllerTests.java`

~~~java
package com.shop;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(QuoteController.class)
class QuoteControllerTests {
    @Autowired
    MockMvc mvc;
    @MockitoBean
    ShippingService shipping;

    @Test
    void mapsRequestAndDelegatesToService() throws Exception {
        when(shipping.fee(2000)).thenReturn(490);
        mvc.perform(get("/shipping").param("subtotalInCents", "2000"))
                .andExpect(status().isOk()).andExpect(content().string("490"));
        verify(shipping).fee(2000);
    }

    @Test
    void rejectsMissingParameter() throws Exception {
        mvc.perform(get("/shipping")).andExpect(status().isBadRequest());
        verifyNoInteractions(shipping);
    }
}
~~~

`src/test/java/com/shop/ShopIntegrationTests.java`

~~~java
package com.shop;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import static org.junit.jupiter.api.Assertions.assertEquals;

@SpringBootTest
class ShopIntegrationTests {
    @Autowired
    QuoteController controller;

    @Test
    void wiresControllerToRealShippingService() {
        assertEquals(490, controller.quote(2000));
        assertEquals(0, controller.quote(5000));
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

`src/main/java/com/shop/QuoteController.java`

~~~java
package com.shop;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class QuoteController {
    private final ShippingService shipping;

    public QuoteController(ShippingService shipping) {
        this.shipping = shipping;
    }

    @GetMapping("/shipping")
    public int quote(@RequestParam int subtotalInCents) {
        return shipping.fee(subtotalInCents);
    }
}
~~~

`src/main/resources/application.yml`

~~~yaml
spring:
  application:
    name: shop
~~~

`src/test/java/com/shop/ShippingServiceTests.java`

~~~java
package com.shop;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class ShippingServiceTests {
    private final ShippingService shipping = new ShippingService();

    @Test
    void chargesBelowThreshold() {
        assertEquals(490, shipping.fee(4999));
    }

    @Test
    void freeAtThreshold() {
        assertEquals(0, shipping.fee(5000));
    }

    @Test
    void rejectsNegativeSubtotal() {
        assertThrows(IllegalArgumentException.class, () -> shipping.fee(-1));
    }
}
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `.mvn/wrapper/maven-wrapper.properties`: lezione 46
- `src/main/java/com/shop/ShopApplication.java`: lezione 46

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw -Dtest=ShippingServiceTests test
./mvnw -Dtest=QuoteControllerTests test
./mvnw test
~~~

## Riepilogo

- Il perimetro segue il rischio che vogliamo verificare
- La soglia è corretta e tutti i test passano
- KISS: scegliere il controllo più piccolo sufficiente
