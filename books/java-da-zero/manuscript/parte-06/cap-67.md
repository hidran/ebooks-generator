# Lezione 47. Starter e autoconfigurazione

## Punti chiave

### Tre responsabilità diverse

- Starter: dipendenze raggruppate per una funzionalità
- Parent di Boot: versioni compatibili e impostazioni Maven
- Autoconfigurazione: bean scelti all'avvio in base alle condizioni
- Le regole del negozio rimangono nel nostro codice

> Percorso: Starter, poi classpath, poi condizioni, poi bean Spring.

### Prima e dopo

- Prima: starter di base, contesto senza server HTTP
- Dopo: spring-boot-starter-webmvc, Spring MVC e Tomcat
- Stessa ShopApplication, nessun controller aggiunto
- Un server avviato non equivale a un'API già implementata

### Una dipendenza mirata

- In Boot 4 usiamo spring-boot-starter-webmvc
- Aggiungiamo solo il blocco dependency
- La versione arriva dal parent di Boot
- Maven mostra le dipendenze transitive con dependency:tree

### Leggere le decisioni di Boot

- --debug abilita il rapporto delle condizioni
- Positive matches: condizioni soddisfatte
- Negative matches: condizioni non soddisfatte
- Classi presenti, tipo di applicazione e bean già definiti
- Un risultato negativo può essere normale

### Mantenere il controllo

- Una proprietà può cambiare il tipo di applicazione
- Un nostro bean può far arretrare una configurazione predefinita
- Leggere il rapporto prima di aggiungere configurazione manuale
- KISS: configurare solo ciò che serve

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
            <artifactId>spring-boot-starter</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-webmvc</artifactId>
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

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `.mvn/wrapper/maven-wrapper.properties`: lezione 46
- `src/main/java/com/shop/ShopApplication.java`: lezione 46
- `src/main/resources/application.properties`: lezione 46
- `src/test/java/com/shop/ShopApplicationTests.java`: lezione 46

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw package
java -jar target/shop-0.0.1-SNAPSHOT.jar
./mvnw dependency:tree -Dincludes=org.springframework.boot:spring-boot-starter-webmvc,org.springframework:spring-webmvc,org.apache.tomcat.embed:tomcat-embed-core
java -jar target/shop-0.0.1-SNAPSHOT.jar --server.port=18080 --debug > boot.log 2>&1 & boot_pid=$!
grep -E 'Tomcat started|Started ShopApplication' boot.log
curl -s -o /dev/null -w 'HTTP %{http_code}\n' http://localhost:18080/
grep -A 6 '^   TomcatServletWebServerAutoConfiguration matched:' boot.log
grep -A 3 '^   TomcatReactiveWebServerAutoConfiguration:' boot.log
kill "$boot_pid"
java -jar target/shop-0.0.1-SNAPSHOT.jar --spring.main.web-application-type=none
~~~

## Riepilogo

- Lo starter porta dipendenze; Boot decide quali bean creare
- Il parent coordina le versioni; non inventa regole di dominio
- Albero Maven e rapporto delle condizioni spiegano il risultato
