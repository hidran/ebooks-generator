# Lezione 75. PostgreSQL con Docker Compose

## Punti chiave

### Perché un database vero in sviluppo

- Ogni database ha il suo dialetto
- H2 nasconde differenze che emergono in produzione
- Twelve-factor: sviluppo e produzione simili
- H2 resta nei test: veloci e senza Docker

### Il supporto Docker Compose di Spring Boot

- Trova compose.yaml nella cartella del progetto
- docker compose up all'avvio, stop alla chiusura
- Aspetta che PostgreSQL sia pronto
- DataSource creato dal container: nessuna URL scritta
- Solo sviluppo: escluso dal Jar e saltato nei test

### Sicurezza e KISS

- Immagine con versione fissa: postgres:18.6-alpine
- Porta pubblicata solo su 127.0.0.1
- Password da variabile d'ambiente, valore demo dichiarato
- Nessun file .env nel progetto
- In produzione il database non si avvia con Compose

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

`compose.yaml`

~~~yaml
services:
  postgres:
    image: postgres:18.6-alpine
    environment:
      POSTGRES_DB: shop
      POSTGRES_USER: shop
      # Demo default for local development only: set POSTGRES_PASSWORD to override it.
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-shop-demo-password}
    ports:
      - "127.0.0.1:5432:5432"
~~~

`requests/create-product.http`

~~~http
### Create product
POST http://127.0.0.1:18105/api/products
Accept: application/json
Content-Type: application/json

{"name":"Webcam","priceInCents":3900}
~~~

`requests/list-products.http`

~~~http
### List products
GET http://127.0.0.1:18105/api/products
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
  port: 18105
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

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
- `src/main/resources/db/migration/V1__create_product_table.sql`: lezione 69, file `src/main/resources/schema.sql`
- `src/main/resources/db/migration/V2__insert_demo_products.sql`: lezione 69, file `src/main/resources/data.sql`
- `src/test/java/com/shop/catalog/MigrationTests.java`: lezione 74
- `src/test/java/com/shop/catalog/ProductServiceTests.java`: lezione 70

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw spring-boot:run
./mvnw test
~~~

## Riepilogo

- H2 solo nei test, PostgreSQL in sviluppo
- compose.yaml: un servizio postgres descritto in dieci righe
- spring-boot-docker-compose, driver PostgreSQL, flyway-database-postgresql
- Connessione automatica e migrazioni applicate su PostgreSQL
- Stesso codice Java, nessuna configurazione della connessione
