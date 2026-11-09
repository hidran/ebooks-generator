# Lezione 52. Spring MVC: DispatcherServlet, controller e richieste HTTP

## Punti chiave

### Il percorso di una richiesta

- Il client HTTP invia una richiesta HTTP a Tomcat
- DispatcherServlet coordina Spring MVC
- HandlerMapping trova il metodo associato
- HandlerAdapter prepara gli argomenti e invoca il controller
- Il valore restituito viene scritto nel corpo della risposta

### Un controller piccolo

- @RestController: componente e corpo della risposta
- @GetMapping: percorso e verbo HTTP
- @RequestParam: parametro della query convertito in int
- ShippingService ricevuto dal costruttore
- Il controller delega la regola al servizio

### Controllare anche gli errori

- GET con subtotalInCents=2000: 200 e 490
- Parametro mancante o non numerico: 400
- POST sul percorso GET: 405
- Percorso sconosciuto: 404
- Binding e selezione del metodo precedono la delega

### MVC e risposte

- @Controller può restituire il nome di una vista
- @RestController scrive il valore nel corpo
- Gli HttpMessageConverter producono la rappresentazione
- Un endpoint HTTP da solo non definisce un progetto REST

## Codice della lezione

`src/main/java/com/shop/ShippingController.java`

~~~java
package com.shop;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class ShippingController {
    private final ShippingService shipping;

    public ShippingController(ShippingService shipping) {
        this.shipping = shipping;
    }

    @GetMapping("/api/shipping")
    public int quote(@RequestParam int subtotalInCents) {
        return shipping.fee(subtotalInCents);
    }
}
~~~

`requests/invalid-parameter.http`

~~~http
### Invalid parameter
GET http://127.0.0.1:18082/api/shipping?subtotalInCents=text
Accept: application/json
~~~

`requests/missing-parameter.http`

~~~http
### Missing parameter
GET http://127.0.0.1:18082/api/shipping
Accept: application/json
~~~

`requests/shipping-quote.http`

~~~http
### Shipping quote
GET http://127.0.0.1:18082/api/shipping?subtotalInCents=2000
Accept: application/json
~~~

`requests/unknown-path.http`

~~~http
### Unknown path
GET http://127.0.0.1:18082/api/unknown
Accept: application/json
~~~

`requests/wrong-method.http`

~~~http
### Wrong method
POST http://127.0.0.1:18082/api/shipping
Accept: application/json
~~~

`src/main/java/com/shop/ShopApplication.java`

~~~java
package com.shop;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

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
server:
  address: 127.0.0.1
  port: 18082
~~~

`src/main/resources/static/rest-client.html`: la pagina che nel video fa da client HTTP per provare le API. È uno strumento della registrazione, non parte del progetto da studiare: la trovi nel repository del codice, e qui non la riportiamo.

`src/test/java/com/shop/ShippingControllerTests.java`

~~~java
package com.shop;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(ShippingController.class)
class ShippingControllerTests {
    @Autowired MockMvc mvc;
    @MockitoBean ShippingService shipping;

    @Test
    void bindsParameterAndDelegates() throws Exception {
        when(shipping.fee(2000)).thenReturn(490);
        mvc.perform(get("/api/shipping").param("subtotalInCents", "2000"))
                .andExpect(status().isOk()).andExpect(content().string("490"));
        verify(shipping).fee(2000);
    }

    @Test
    void rejectsMissingParameter() throws Exception {
        mvc.perform(get("/api/shipping")).andExpect(status().isBadRequest());
        verifyNoInteractions(shipping);
    }

    @Test
    void rejectsInvalidNumber() throws Exception {
        mvc.perform(get("/api/shipping").param("subtotalInCents", "text"))
                .andExpect(status().isBadRequest());
        verifyNoInteractions(shipping);
    }

    @Test
    void rejectsPost() throws Exception {
        mvc.perform(post("/api/shipping")).andExpect(status().isMethodNotAllowed());
        verifyNoInteractions(shipping);
    }
}
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `.mvn/wrapper/maven-wrapper.properties`: lezione 46
- `pom.xml`: lezione 51
- `src/main/java/com/shop/ShippingService.java`: lezione 51

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw test
./mvnw package
java -jar target/shop-0.0.1-SNAPSHOT.jar
~~~

## Riepilogo

- Abbiamo seguito una richiesta dal server al servizio
- Mapping e binding rendono esplicito il contratto
- Quattro test e richieste reali confermano il comportamento
- La regola di spedizione rimane nel servizio
