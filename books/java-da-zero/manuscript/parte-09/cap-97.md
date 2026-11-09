# Lezione 74. Migrazioni con Flyway

## Punti chiave

### Chi crea lo schema?

- ddl-auto: Hibernate genera le tabelle dalle entità
- Comodo in sviluppo, rischioso in produzione
- Nessuna storia e nessuna revisione dei cambiamenti
- Migrazioni: script SQL numerati, versionati con il codice

### Le regole delle migrazioni

- Una migrazione applicata non si modifica più
- Ogni cambiamento è una nuova versione
- Checksum diverso: l'avvio si ferma
- Stessi script in test, sviluppo e produzione

### KISS: cosa non serve

- Un solo strumento: Flyway o Liquibase, non entrambi
- Niente ddl-auto update in produzione
- Niente script di undo: si corregge in avanti
- Niente data.sql accanto alle migrazioni

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
            <groupId>com.h2database</groupId>
            <artifactId>h2</artifactId>
            <scope>runtime</scope>
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
  port: 18104
~~~

`requests/create-product.http`

~~~http
### Create product
POST http://127.0.0.1:18104/api/products
Accept: application/json
Content-Type: application/json

{"name":"Webcam","priceInCents":3900}
~~~

`requests/list-products.http`

~~~http
### List products
GET http://127.0.0.1:18104/api/products
Accept: application/json
~~~

`src/test/java/com/shop/catalog/MigrationTests.java`

~~~java
package com.shop.catalog;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.simple.JdbcClient;

@SpringBootTest
class MigrationTests {
    @Autowired
    JdbcClient jdbc;

    @Test
    void flywayAppliedBothVersions() {
        var versions = jdbc.sql("""
                SELECT "version" FROM "flyway_schema_history"
                WHERE "type" = 'SQL' ORDER BY "installed_rank"
                """).query(String.class).list();
        assertThat(versions).containsExactly("1", "2");
    }
}
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `src/main/resources/db/migration/V1__create_product_table.sql`: lezione 69, file `src/main/resources/schema.sql`
- `src/main/resources/db/migration/V2__insert_demo_products.sql`: lezione 69, file `src/main/resources/data.sql`
- `.mvn/wrapper/maven-wrapper.properties`: lezione 46
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
- `src/test/java/com/shop/catalog/ProductServiceTests.java`: lezione 70

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw test
rm src/main/resources/data.sql
./mvnw clean test
./mvnw package
java -jar target/shop-0.0.1-SNAPSHOT.jar
~~~

## Riepilogo

- V1 crea la tabella, V2 inserisce i dati di prova
- Starter Flyway: migrazioni eseguite all'avvio
- flyway_schema_history registra ogni versione
- ddl-auto: validate al posto di create-drop
- Cinque test verdi, applicazione avviata alla versione 2
