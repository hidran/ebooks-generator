# Lezione 62. Testare i controller con MockMvc

## Punti chiave

### Una fetta dell'applicazione

- @SpringBootTest avvia tutto: servizi, repository, configurazione
- @WebMvcTest carica solo lo strato web
- Dentro: controller, advice, JSON e validazione
- Fuori: servizi e repository

### Mock e asserzioni

- @MockitoBean mette un mock nel contesto
- given(...).willReturn(...) decide la risposta
- MockMvcTester: richieste e asserzioni AssertJ
- verifyNoInteractions: il servizio non viene chiamato

### Cosa non serve

- Avviare il server o aprire una porta
- Un database o dati reali
- Eliminare i test completi con @SpringBootTest

## Codice della lezione

`src/test/java/com/shop/web/ProductControllerTests.java`

~~~java
package com.shop.web;

import com.shop.catalog.Product;
import com.shop.catalog.ProductNotFoundException;
import com.shop.catalog.ProductService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.assertj.MockMvcTester;
import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.verifyNoInteractions;

@WebMvcTest(ProductController.class)
class ProductControllerTests {
    @Autowired MockMvcTester mvc;
    @MockitoBean ProductService service;

    @Test
    void readsAProductFromTheService() {
        given(service.find(1)).willReturn(new Product(1, "Keyboard", 4900));
        assertThat(mvc.get().uri("/api/products/1"))
                .hasStatusOk()
                .bodyJson().extractingPath("$.name").isEqualTo("Keyboard");
    }

    @Test
    void missingProductBecomesAProblemDetail() {
        given(service.find(99)).willThrow(new ProductNotFoundException(99));
        assertThat(mvc.get().uri("/api/products/99"))
                .hasStatus(HttpStatus.NOT_FOUND)
                .hasContentType("application/problem+json")
                .bodyJson().extractingPath("$.title").isEqualTo("Product not found");
    }

    @Test
    void invalidProductNeverReachesTheService() {
        assertThat(mvc.post().uri("/api/products").contentType(MediaType.APPLICATION_JSON)
                .content("{\"name\":\" \",\"priceInCents\":0}"))
                .hasStatus(HttpStatus.BAD_REQUEST);
        verifyNoInteractions(service);
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
  port: 18092
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
- `src/test/java/com/shop/web/ProductListTests.java`: lezione 58

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw test -Dtest=ProductControllerTests
./mvnw test
~~~

## Riepilogo

- @WebMvcTest isola il controller
- @MockitoBean sostituisce il servizio
- MockMvcTester rende le asserzioni leggibili
- Stato, JSON, errori e validazione senza il servizio vero
- Pochi test completi, molti test di fetta
