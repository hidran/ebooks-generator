# Lezione 50. DevTools e primo sguardo ad Actuator

## Punti chiave

### Sviluppo e osservabilità

- DevTools aiuta durante lo sviluppo
- Un riavvio richiede una modifica del classpath
- Salvare un sorgente non equivale a compilarlo
- Actuator espone informazioni operative selezionate

### Dipendenze e configurazione

- DevTools dichiarato optional
- Actuator e starter web MVC
- Server dimostrativo limitato a 127.0.0.1:18081
- Esposizione HTTP limitata a health e info
- Health senza dettagli interni

### Verifiche locali

- /actuator/health: stato UP
- /actuator/info: metadati fittizi training
- /actuator/env: non esposto, HTTP 404
- Esposizione e autorizzazione sono decisioni diverse

### Riavvio riproducibile

- Avvio da Maven con classi del progetto
- Modifica del messaggio v1 -&gt; v2
- ./mvnw compile aggiorna target/classes
- DevTools rileva la modifica e riavvia il contesto

### Artefatto distribuito

- Arrestare il processo della demo
- ./mvnw package crea il Jar eseguibile
- Il repackaging standard esclude DevTools
- Non rendere pubblici tutti gli endpoint per comodità

## Codice della lezione

`src/main/java/com/shop/ShopApplication.java`

~~~java
package com.shop;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

@SpringBootApplication
public class ShopApplication {
    private static final Logger LOGGER = LoggerFactory.getLogger(ShopApplication.class);

    public static void main(String[] args) {
        SpringApplication.run(ShopApplication.class, args);
    }

    @Bean
    CommandLineRunner startup() {
        return args -> LOGGER.info("Shop ready v2");
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
            <artifactId>spring-boot-starter-actuator</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-devtools</artifactId>
            <optional>true</optional>
        </dependency>
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
            <artifactId>spring-boot-starter-test</artifactId>
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
server:
  address: 127.0.0.1
  port: 18081
management:
  endpoints:
    web:
      exposure:
        include: health,info
  endpoint:
    health:
      show-details: never
  info:
    env:
      enabled: true
info:
  app:
    name: shop
    mode: training
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `.mvn/wrapper/maven-wrapper.properties`: lezione 46
- `src/test/java/com/shop/ShopApplicationTests.java`: lezione 46

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw spring-boot:run > dev.log 2>&1 & boot_pid=$!
grep -E 'Tomcat started|Shop ready' dev.log
curl -s http://127.0.0.1:18081/actuator/health | jq
curl -s http://127.0.0.1:18081/actuator/info | jq
curl -s -o /dev/null -w 'HTTP %{http_code}\n' http://127.0.0.1:18081/actuator/env
./mvnw compile
grep 'Shop ready' dev.log
kill -- -"$boot_pid"
./mvnw package
"$JAVA_HOME/bin/jar" tf target/shop-0.0.1-SNAPSHOT.jar | grep spring-boot-devtools || echo "DevTools excluded from Jar"
~~~

## Riepilogo

- DevTools riduce il ciclo modifica, compila, riavvia
- Actuator descrive aspetti operativi, non correttezza del dominio
- Esporre soltanto ciò che serve e proteggere l'accesso
