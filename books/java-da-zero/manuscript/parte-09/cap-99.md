# Lezione 76. Test di persistenza con Testcontainers

## Punti chiave

### Lo stesso database della produzione

- Un test verde su H2 non garantisce PostgreSQL
- Testcontainers avvia container Docker dai test JUnit
- Container usa e getta, eliminato alla fine
- @ServiceConnection: connessione creata da Spring Boot

> Percorso: Test JUnit, poi Testcontainers, poi PostgreSQL 18.6, poi DataSource.

### H2 o Testcontainers?

- Logica di servizio e mapping: test veloci, senza Docker
- Query, migrazioni, vincoli e tipi: database vero
- Piramide dei test: molti test rapidi, meno integrazione
- disabledWithoutDocker: saltati in locale, mai in CI

### KISS: cosa non serve

- Un container statico per classe, non per metodo
- Stessa immagine di compose.yaml: postgres:18.6-alpine
- Niente @DynamicPropertySource: basta @ServiceConnection
- Configurazione condivisa solo quando le classi crescono

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
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-flyway</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-docker-compose</artifactId>
            <scope>runtime</scope>
            <optional>true</optional>
        </dependency>
        <dependency>
            <groupId>org.postgresql</groupId>
            <artifactId>postgresql</artifactId>
            <scope>runtime</scope>
        </dependency>
        <dependency>
            <groupId>org.flywaydb</groupId>
            <artifactId>flyway-database-postgresql</artifactId>
        </dependency>
        <dependency>
            <groupId>com.h2database</groupId>
            <artifactId>h2</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-webmvc-test</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa-test</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-testcontainers</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.testcontainers</groupId>
            <artifactId>testcontainers-postgresql</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.testcontainers</groupId>
            <artifactId>testcontainers-junit-jupiter</artifactId>
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

`src/test/java/com/shop/catalog/PostgresProductRepositoryTests.java`

~~~java
package com.shop.catalog;

import static org.assertj.core.api.Assertions.assertThat;

import java.sql.Connection;
import java.sql.SQLException;
import javax.sql.DataSource;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.data.jpa.test.autoconfigure.DataJpaTest;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.context.annotation.Import;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.postgresql.PostgreSQLContainer;

@DataJpaTest
@Import(JpaProductRepository.class)
@Testcontainers(disabledWithoutDocker = true)
class PostgresProductRepositoryTests {
    @Container
    @ServiceConnection
    static PostgreSQLContainer postgres = new PostgreSQLContainer("postgres:18.6-alpine");
    @Autowired
    JpaProductRepository products;
    @Autowired
    DataSource dataSource;

    @Test
    void runsOnPostgres() throws SQLException {
        try (Connection connection = dataSource.getConnection()) {
            assertThat(connection.getMetaData().getDatabaseProductName()).isEqualTo("PostgreSQL");
        }
    }

    @Test
    void migrationsCreatedTheDemoProducts() {
        assertThat(products.findAll()).extracting(Product::name)
                .containsExactly("Keyboard", "Mouse", "Monitor");
    }

    @Test
    void savedProductGetsAnIdFromTheDatabase() {
        Product saved = products.save(new Product(0, "Webcam", 3900));
        assertThat(saved.id()).isPositive();
        assertThat(products.findById(saved.id())).contains(saved);
    }
}
~~~

`requests/create-product.http`

~~~http
### Create product
POST http://127.0.0.1:18106/api/products
Accept: application/json
Content-Type: application/json

{"name":"Webcam","priceInCents":3900}
~~~

`requests/list-products.http`

~~~http
### List products
GET http://127.0.0.1:18106/api/products
Accept: application/json
~~~

`src/main/resources/application.yml`

~~~yaml
spring:
  application:
    name: shop
  jpa:
    open-in-view: false
    hibernate:
      ddl-auto: validate
server:
  address: 127.0.0.1
  port: 18106
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `.mvn/wrapper/maven-wrapper.properties`: lezione 46
- `compose.yaml`: lezione 75
- `src/main/java/com/shop/ShopApplication.java`: lezione 52
- `src/main/java/com/shop/catalog/JpaProductRepository.java`: lezione 70
- `src/main/java/com/shop/catalog/Product.java`: lezione 57
- `src/main/java/com/shop/catalog/ProductEntity.java`: lezione 70
- `src/main/java/com/shop/catalog/ProductJpaRepository.java`: lezione 70
- `src/main/java/com/shop/catalog/ProductNotFoundException.java`: lezione 64
- `src/main/java/com/shop/catalog/ProductRepository.java`: lezione 57
- `src/main/java/com/shop/catalog/ProductService.java`: lezione 64
- `src/main/java/com/shop/web/ApiErrorHandler.java`: lezione 70
- `src/main/java/com/shop/web/CreateProductRequest.java`: lezione 70
- `src/main/java/com/shop/web/ProductController.java`: lezione 70
- `src/main/java/com/shop/web/ProductResponse.java`: lezione 70
- `src/main/resources/db/migration/V1__create_product_table.sql`: lezione 69, file `src/main/resources/schema.sql`
- `src/main/resources/db/migration/V2__insert_demo_products.sql`: lezione 69, file `src/main/resources/data.sql`
- `src/test/java/com/shop/catalog/MigrationTests.java`: lezione 74
- `src/test/java/com/shop/catalog/ProductServiceTests.java`: lezione 70

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw test
~~~

## Riepilogo

- Test di persistenza che girava su H2 senza saperlo
- @Testcontainers(disabledWithoutDocker = true)
- @Container e @ServiceConnection su PostgreSQLContainer
- Migrazioni, query e salvataggio verificati su PostgreSQL
