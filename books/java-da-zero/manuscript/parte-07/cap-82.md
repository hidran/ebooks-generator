# Lezione 61b. Testare un client HTTP

## Punti chiave

### Un server finto in memoria

- MockRestServiceServer si aggancia al RestClient
- Nessuna porta e nessuna rete: intercetta le richieste
- requestTo e method: la richiesta attesa
- withSuccess, withServerError, withStatus: la risposta
- verify: le richieste attese sono arrivate

### La fetta @RestClientTest

- Modulo spring-boot-restclient-test di Boot 4.1
- Starter spring-boot-starter-restclient-test, scope test
- Carica JSON e RestClient.Builder, già legato al server finto
- Solo il componente indicato: niente controller, servizi, server web

### L'HTTP interface e la fetta

- I gruppi hanno una loro autoconfigurazione
- @RestClientTest non la carica (richiesta aperta in Boot 4.x)
- Senza di essa il proxy non riceve il server finto
- @ImportAutoConfiguration con le due classi dei gruppi

### Quando serve WireMock

- MockRestServiceServer non apre connessioni
- Niente timeout, ritardi o connessioni interrotte
- WireMock: un vero server HTTP su una porta
- KISS: prima lo strumento già incluso

### Cosa non serve

- La rete o il fornitore vero
- L'applicazione avviata sulla sua porta
- Una libreria esterna per i casi semplici

## Codice della lezione

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
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-restclient</artifactId>
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
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-restclient-test</artifactId>
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

`src/main/java/com/shop/supplier/SupplierRestClient.java`

~~~java
package com.shop.supplier;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

@Component
public class SupplierRestClient {
    private final RestClient restClient;

    public SupplierRestClient(RestClient.Builder builder,
            @Value("${spring.http.serviceclient.supplier.base-url}") String baseUrl) {
        this.restClient = builder.baseUrl(baseUrl).build();
    }

    public SupplierStock stock(long productId) {
        return restClient.get()
                .uri("/supplier/stock/{productId}", productId)
                .retrieve()
                .body(SupplierStock.class);
    }
}
~~~

`src/test/java/com/shop/supplier/SupplierRestClientTests.java`

~~~java
package com.shop.supplier;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.restclient.test.autoconfigure.RestClientTest;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.springframework.http.HttpMethod.GET;
import static org.springframework.http.HttpStatus.NOT_FOUND;
import static org.springframework.http.MediaType.APPLICATION_JSON;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withServerError;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withStatus;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

@RestClientTest(components = SupplierRestClient.class,
        properties = "spring.http.serviceclient.supplier.base-url=http://supplier.test")
class SupplierRestClientTests {
    @Autowired SupplierRestClient client;
    @Autowired MockRestServiceServer server;

    @Test
    void readsTheStockFromTheSupplier() {
        String json = "{\"productId\":1,\"available\":12}";
        server.expect(requestTo("http://supplier.test/supplier/stock/1"))
                .andExpect(method(GET))
                .andRespond(withSuccess(json, APPLICATION_JSON));
        assertThat(client.stock(1)).isEqualTo(new SupplierStock(1, 12));
        server.verify();
    }

    @Test
    void serverErrorBecomesAnException() {
        server.expect(requestTo("http://supplier.test/supplier/stock/1"))
                .andRespond(withServerError());
        assertThatThrownBy(() -> client.stock(1))
                .isInstanceOf(HttpServerErrorException.class);
    }

    @Test
    void unknownProductIsNotFound() {
        server.expect(requestTo("http://supplier.test/supplier/stock/99"))
                .andRespond(withStatus(NOT_FOUND));
        assertThatThrownBy(() -> client.stock(99))
                .isInstanceOf(HttpClientErrorException.NotFound.class);
    }
}
~~~

`src/test/java/com/shop/supplier/SupplierClientTests.java`

~~~java
package com.shop.supplier;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.ImportAutoConfiguration;
import org.springframework.boot.http.client.autoconfigure.service.HttpServiceClientPropertiesAutoConfiguration;
import org.springframework.boot.restclient.autoconfigure.service.HttpServiceClientAutoConfiguration;
import org.springframework.boot.restclient.test.autoconfigure.RestClientTest;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.springframework.http.HttpMethod.GET;
import static org.springframework.http.HttpStatus.NOT_FOUND;
import static org.springframework.http.MediaType.APPLICATION_JSON;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withServerError;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withStatus;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

@RestClientTest(
        properties = "spring.http.serviceclient.supplier.base-url=http://supplier.test")
@ImportAutoConfiguration({HttpServiceClientPropertiesAutoConfiguration.class,
        HttpServiceClientAutoConfiguration.class})
class SupplierClientTests {
    @Autowired SupplierClient client;
    @Autowired MockRestServiceServer server;

    @Test
    void readsTheStockFromTheSupplier() {
        String json = "{\"productId\":1,\"available\":12}";
        server.expect(requestTo("http://supplier.test/supplier/stock/1"))
                .andExpect(method(GET))
                .andRespond(withSuccess(json, APPLICATION_JSON));
        assertThat(client.stock(1)).isEqualTo(new SupplierStock(1, 12));
        server.verify();
    }

    @Test
    void serverErrorBecomesAnException() {
        server.expect(requestTo("http://supplier.test/supplier/stock/1"))
                .andRespond(withServerError());
        assertThatThrownBy(() -> client.stock(1))
                .isInstanceOf(HttpServerErrorException.class);
    }

    @Test
    void unknownProductIsNotFound() {
        server.expect(requestTo("http://supplier.test/supplier/stock/99"))
                .andRespond(withStatus(NOT_FOUND));
        assertThatThrownBy(() -> client.stock(99))
                .isInstanceOf(HttpClientErrorException.NotFound.class);
    }
}
~~~

`src/main/resources/application.yml`

~~~yaml
spring:
  application:
    name: shop
  http:
    serviceclient:
      supplier:
        base-url: http://127.0.0.1:18191
server:
  address: 127.0.0.1
  port: 18191
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `.mvn/wrapper/maven-wrapper.properties`: lezione 46
- `src/main/java/com/shop/ShopApplication.java`: lezione 61
- `src/main/java/com/shop/catalog/InMemoryProductRepository.java`: lezione 58
- `src/main/java/com/shop/catalog/Product.java`: lezione 57
- `src/main/java/com/shop/catalog/ProductNotFoundException.java`: lezione 57
- `src/main/java/com/shop/catalog/ProductPage.java`: lezione 58
- `src/main/java/com/shop/catalog/ProductRepository.java`: lezione 57
- `src/main/java/com/shop/catalog/ProductService.java`: lezione 58
- `src/main/java/com/shop/catalog/ProductSort.java`: lezione 58
- `src/main/java/com/shop/supplier/SupplierClient.java`: lezione 61
- `src/main/java/com/shop/supplier/SupplierStock.java`: lezione 61
- `src/main/java/com/shop/supplier/SupplierStubController.java`: lezione 61
- `src/main/java/com/shop/web/ApiErrorHandler.java`: lezione 57
- `src/main/java/com/shop/web/AvailabilityController.java`: lezione 61
- `src/main/java/com/shop/web/AvailabilityResponse.java`: lezione 61
- `src/main/java/com/shop/web/CreateProductRequest.java`: lezione 57
- `src/main/java/com/shop/web/ProductController.java`: lezione 58
- `src/main/java/com/shop/web/ProductPageResponse.java`: lezione 58
- `src/main/java/com/shop/web/ProductResponse.java`: lezione 57
- `src/test/java/com/shop/web/ProductApiTests.java`: lezione 58
- `src/test/java/com/shop/web/ProductListTests.java`: lezione 58

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw test -Dtest=SupplierRestClientTests
./mvnw test -Dtest=SupplierClientTests
./mvnw test
~~~

## Riepilogo

- @RestClientTest: una fetta piccola per il client
- expect descrive la richiesta, withSuccess e gli altri la risposta
- Errori 500 e 404 provati a comando
- HTTP interface: si aggiunge la configurazione dei gruppi
- Stessi test per i due client
