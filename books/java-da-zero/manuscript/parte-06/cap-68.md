# Lezione 48. Configurazione esterna, profili e ambiente

## Punti chiave

### Configurazione separata dal codice

- Stesso Jar in ambienti diversi
- Valori di base in application.yml
- Profili per gruppi coerenti di impostazioni
- Variabili d'ambiente per scelte del deployment
- Configurazione esterna come pratica 12-factor

### Un gruppo di proprietà tipizzato

- shop.currency e shop.shipping-in-cents
- ShopSettings: record con @ConfigurationProperties
- Registrazione con @EnableConfigurationProperties
- StartupReport riceve le impostazioni dal costruttore

### Default e override

- ${SHOP_SHIPPING:490}: ambiente oppure default 490
- application-demo.yml sostituisce soltanto la spedizione
- --spring.profiles.active=demo attiva il profilo
- Nel nostro esempio: CLI prevale su ambiente e file

### Verificare ogni sorgente

- Default: EUR, 490 centesimi
- Profilo demo: EUR, 290 centesimi
- SHOP_SHIPPING=190: EUR, 190 centesimi
- --shop.shipping-in-cents=0: EUR, zero
- Il Jar rimane identico tra queste esecuzioni

## Codice della lezione

`src/main/resources/application.yml`

~~~yaml
spring:
  application:
    name: shop
shop:
  currency: EUR
  shipping-in-cents: ${SHOP_SHIPPING:490}
~~~

`src/main/java/com/shop/ShopSettings.java`

~~~java
package com.shop;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "shop")
public record ShopSettings(String currency, int shippingInCents) {
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

`src/main/java/com/shop/ShopApplication.java`

~~~java
package com.shop;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;

@SpringBootApplication
@EnableConfigurationProperties(ShopSettings.class)
public class ShopApplication {
    public static void main(String[] args) {
        SpringApplication.run(ShopApplication.class, args);
    }
}
~~~

`src/main/java/com/shop/StartupReport.java`

~~~java
package com.shop;

import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

@Component
public class StartupReport implements CommandLineRunner {
    private final ShopSettings settings;

    public StartupReport(ShopSettings settings) {
        this.settings = settings;
    }

    @Override
    public void run(String... args) {
        System.out.println("Currency: " + settings.currency());
        System.out.println("Shipping: " + settings.shippingInCents());
    }
}
~~~

`src/main/resources/application-demo.yml`

~~~yaml
shop:
  shipping-in-cents: 290
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `.mvn/wrapper/maven-wrapper.properties`: lezione 46
- `src/test/java/com/shop/ShopApplicationTests.java`: lezione 46

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw package
java -jar target/shop-0.0.1-SNAPSHOT.jar
java -jar target/shop-0.0.1-SNAPSHOT.jar --spring.profiles.active=demo
SHOP_SHIPPING=190 java -jar target/shop-0.0.1-SNAPSHOT.jar
SHOP_SHIPPING=190 java -jar target/shop-0.0.1-SNAPSHOT.jar --shop.shipping-in-cents=0
~~~

## Riepilogo

- YAML e binding tipizzato rendono esplicite le impostazioni
- Profili e ambiente cambiano valori senza cambiare codice
- La precedenza va verificata con esempi controllati
- Non stampare segreti o l'intero ambiente
