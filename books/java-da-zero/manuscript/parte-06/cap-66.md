# Lezione 46. Creare Shop con Spring Initializr

## Punti chiave

### Dal container all'applicazione

- Spring Framework crea e collega i bean
- Spring Boot prepara configurazione, dipendenze e avvio
- Initializr genera la struttura iniziale del progetto
- Il codice e le regole del negozio restano nostri

> Percorso: Initializr, poi progetto Maven, poi applicazione Spring Boot.

### Le scelte del progetto

- Maven e Java, JDK 25
- Spring Boot 4.1.1 stabile, senza preview
- Group: com.shop, Artifact e Name: shop
- Package: com.shop, Packaging: Jar
- Nessuna dipendenza aggiuntiva in questa prima applicazione

### Aprire il progetto

- Estrarre lo ZIP, aprire la cartella con pom.xml
- Attendere l'importazione Maven e controllare il JDK
- src/main/java: applicazione; src/test/java: test
- src/main/resources: configurazione

### Verificare e distribuire

- Il test generato verifica l'avvio del contesto
- ./mvnw test: esegue i test
- ./mvnw clean package: test e JAR eseguibile
- java -jar target/shop-0.0.1-SNAPSHOT.jar
- Senza dipendenze web non parte un server HTTP

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
		<relativePath/> <!-- lookup parent from repository -->
	</parent>
	<groupId>com.shop</groupId>
	<artifactId>shop</artifactId>
	<version>0.0.1-SNAPSHOT</version>
	<name>shop</name>
	<description/>
	<url/>
	<licenses>
		<license/>
	</licenses>
	<developers>
		<developer/>
	</developers>
	<scm>
		<connection/>
		<developerConnection/>
		<tag/>
		<url/>
	</scm>
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

@SpringBootApplication
public class ShopApplication {

    public static void main(String[] args) {
        SpringApplication.run(ShopApplication.class, args);
    }

}
~~~

`.mvn/wrapper/maven-wrapper.properties`

~~~properties
wrapperVersion=3.3.4
distributionType=only-script
distributionUrl=https://repo.maven.apache.org/maven2/org/apache/maven/apache-maven/3.10.0/apache-maven-3.10.0-bin.zip
~~~

`src/main/resources/application.properties`

~~~properties
spring.application.name=shop
~~~

`src/test/java/com/shop/ShopApplicationTests.java`

~~~java
package com.shop;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class ShopApplicationTests {

    @Test
    void contextLoads() {
    }

}
~~~

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
curl -fsS 'https://start.spring.io/starter.zip?type=maven-project&bootVersion=4.1.1&javaVersion=25&groupId=com.shop&artifactId=shop&name=shop&packageName=com.shop&baseDir=shop' -o shop.zip
unzip -oq shop.zip && cd shop && ls
./mvnw test
./mvnw clean package
ls target
java -jar target/shop-0.0.1-SNAPSHOT.jar
~~~

## Riepilogo

- Initializr genera un punto di partenza riproducibile
- ShopApplication avvia Spring Boot
- Maven Wrapper, test e JAR: dal sorgente all'esecuzione
