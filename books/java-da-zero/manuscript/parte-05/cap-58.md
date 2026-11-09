# Lezione 38. Spring e l'inversione del controllo

## Punti chiave

### Collegare a mano non scala

- Lezioni 34 e 36: il main crea e collega ogni oggetto
- Decine di classi: ordine di creazione, istanze condivise
- Ogni nuova dipendenza cambia il main
- Codice ripetitivo, senza regole del negozio

> Percorso: main, poi new repository, poi new servizio.

### Inversione del controllo

- Noi descriviamo le classi, il container le crea e le collega
- Il container di Spring: ApplicationContext
- Bean: un oggetto gestito dal container
- Nel pom: spring-context (Spring Framework 7)

> Percorso: classi, poi ApplicationContext, poi bean pronti.

### Che cosa fa il container

- Legge i costruttori delle classi registrate
- Crea prima le dipendenze, poi chi le usa
- Un solo costruttore: nessuna annotazione necessaria
- getBean consegna il bean completo; close chiude il container
- Le nostre classi non conoscono Spring

## Codice della lezione

`pom.xml`

~~~xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.shop</groupId>
    <artifactId>lab</artifactId>
    <version>1.0-SNAPSHOT</version>
    <properties>
        <maven.compiler.release>25</maven.compiler.release>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>
    <dependencyManagement>
        <dependencies>
            <dependency>
                <groupId>org.springframework</groupId>
                <artifactId>spring-framework-bom</artifactId>
                <version>7.0.9</version>
                <type>pom</type>
                <scope>import</scope>
            </dependency>
            <dependency>
                <groupId>org.junit</groupId>
                <artifactId>junit-bom</artifactId>
                <version>6.1.3</version>
                <type>pom</type>
                <scope>import</scope>
            </dependency>
        </dependencies>
    </dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>org.springframework</groupId>
            <artifactId>spring-context</artifactId>
        </dependency>
        <dependency>
            <groupId>jakarta.annotation</groupId>
            <artifactId>jakarta.annotation-api</artifactId>
            <version>3.0.0</version>
        </dependency>
        <dependency>
            <groupId>org.springframework</groupId>
            <artifactId>spring-test</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.assertj</groupId>
            <artifactId>assertj-core</artifactId>
            <version>3.27.7</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.16.0</version>
            </plugin>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.6.0</version>
            </plugin>
        </plugins>
    </build>
</project>
~~~

`src/main/java/com/shop/Main.java`, passaggio intermedio («manual»)

~~~java
package com.shop;
import com.shop.catalog.CatalogService;
import com.shop.catalog.InMemoryProductRepository;
public class Main {
    public static void main(String[] args) {
        InMemoryProductRepository repository = new InMemoryProductRepository();
        CatalogService service = new CatalogService(repository);
        System.out.println("By hand: " + service.totalInCents("pen", 3));
    }
}
~~~

`src/main/java/com/shop/catalog/InMemoryProductRepository.java`

~~~java
package com.shop.catalog;
import java.util.Map;
public class InMemoryProductRepository {
    private final Map<String, Integer> prices = Map.of("pen", 150, "notebook", 400);
    public int priceOf(String name) {
        return prices.get(name);
    }
}
~~~

`src/main/java/com/shop/catalog/CatalogService.java`

~~~java
package com.shop.catalog;
public class CatalogService {
    private final InMemoryProductRepository repository;
    public CatalogService(InMemoryProductRepository repository) {
        this.repository = repository;
        System.out.println("CatalogService created");
    }
    public int totalInCents(String name, int quantity) {
        return repository.priceOf(name) * quantity;
    }
}
~~~

`src/main/java/com/shop/Main.java`

~~~java
package com.shop;
import com.shop.catalog.CatalogService;
import com.shop.catalog.InMemoryProductRepository;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
public class Main {
    public static void main(String[] args) {
        InMemoryProductRepository repository = new InMemoryProductRepository();
        CatalogService service = new CatalogService(repository);
        System.out.println("By hand: " + service.totalInCents("pen", 3));
        try (var context = new AnnotationConfigApplicationContext(
                InMemoryProductRepository.class, CatalogService.class)) {
            CatalogService managed = context.getBean(CatalogService.class);
            System.out.println("With Spring: " + managed.totalInCents("pen", 3));
        }
    }
}
~~~

## Riepilogo

- Inversione del controllo: gli oggetti li crea il container
- AnnotationConfigApplicationContext con le classi da gestire
- Iniezione dal costruttore, getBean per il bean pronto
