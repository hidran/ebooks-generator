# Lezione 62b. Test end to end dell'API

## Punti chiave

### Un vero server, un vero client

- RANDOM_PORT: Tomcat vero su una porta libera
- RestTestClient: richieste HTTP vere (Spring Framework 7)
- Costruito su RestClient, con asserzioni sulla risposta
- exchange() invia, expect...() controlla

### Da dove arriva

- RestTestClient è in spring-test
- @AutoConfigureRestTestClient: modulo spring-boot-resttestclient
- Lo porta già spring-boot-starter-webmvc-test
- Nel pom non aggiungiamo niente

### La piramide dei test


> Percorso: Unità, poi Fetta, poi Contesto completo, poi End to end.

- In basso tanti test veloci, in cima pochi test lenti
- Le fette dicono subito dove sta il problema
- Gli end to end provano rete e strati insieme

### Cosa non serve

- Avviare il Jar a mano o fissare una porta
- Nuove dipendenze nel pom
- Ripetere ogni caso: basta uno per tipo di risposta

## Codice della lezione

`src/test/java/com/shop/web/ProductEndToEndTests.java`

~~~java
package com.shop.web;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.resttestclient.autoconfigure.AutoConfigureRestTestClient;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.SpringBootTest.WebEnvironment;
import org.springframework.http.MediaType;
import org.springframework.http.ProblemDetail;
import org.springframework.test.web.servlet.client.RestTestClient;
import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
@AutoConfigureRestTestClient
class ProductEndToEndTests {
    @Autowired RestTestClient client;

    @Test
    void createdProductCanBeReadBack() {
        ProductResponse created = client.post().uri("/api/products")
                .body(new CreateProductRequest("Webcam HD", 6900))
                .exchange()
                .expectStatus().isCreated()
                .expectBody(ProductResponse.class).returnResult().getResponseBody();
        client.get().uri("/api/products/" + created.id())
                .exchange()
                .expectStatus().isOk()
                .expectBody().jsonPath("$.name").isEqualTo("Webcam HD");
    }

    @Test
    void unknownProductIsAProblemDetail() {
        ProblemDetail problem = client.get().uri("/api/products/999")
                .exchange()
                .expectStatus().isNotFound()
                .expectHeader().contentType(MediaType.APPLICATION_PROBLEM_JSON)
                .expectBody(ProblemDetail.class).returnResult().getResponseBody();
        assertThat(problem.getTitle()).isEqualTo("Product not found");
        assertThat(problem.getType())
                .hasToString("https://api.shop.example/problems/product-not-found");
    }

    @Test
    void invalidProductIsRejected() {
        client.post().uri("/api/products")
                .body(new CreateProductRequest(" ", 0))
                .exchange()
                .expectStatus().isBadRequest()
                .expectBody()
                .jsonPath("$.errors.name").exists()
                .jsonPath("$.errors.priceInCents").exists();
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
  port: 18192
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `.mvn/wrapper/maven-wrapper.properties`: lezione 46
- `pom.xml`: lezione 55
- `src/main/java/com/shop/ShopApplication.java`: lezione 52
- `src/main/java/com/shop/catalog/InMemoryProductRepository.java`: lezione 58
- `src/main/java/com/shop/catalog/Product.java`: lezione 57
- `src/main/java/com/shop/catalog/ProductNotFoundException.java`: lezione 57
- `src/main/java/com/shop/catalog/ProductPage.java`: lezione 58
- `src/main/java/com/shop/catalog/ProductRepository.java`: lezione 57
- `src/main/java/com/shop/catalog/ProductService.java`: lezione 58
- `src/main/java/com/shop/catalog/ProductSort.java`: lezione 58
- `src/main/java/com/shop/web/ApiErrorHandler.java`: lezione 57
- `src/main/java/com/shop/web/CreateProductRequest.java`: lezione 57
- `src/main/java/com/shop/web/ProductController.java`: lezione 58
- `src/main/java/com/shop/web/ProductPageResponse.java`: lezione 58
- `src/main/java/com/shop/web/ProductResponse.java`: lezione 57
- `src/test/java/com/shop/web/ProductApiTests.java`: lezione 58
- `src/test/java/com/shop/web/ProductControllerTests.java`: lezione 62
- `src/test/java/com/shop/web/ProductListTests.java`: lezione 58

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw test -Dtest=ProductEndToEndTests
./mvnw test
~~~

## Riepilogo

- @SpringBootTest(webEnvironment = RANDOM_PORT) avvia un server vero
- @AutoConfigureRestTestClient collega il client a quel server
- Creare, rileggere, 404 con ProblemDetail, 400 sulla validazione
- Molti test di fetta, pochi test end to end
