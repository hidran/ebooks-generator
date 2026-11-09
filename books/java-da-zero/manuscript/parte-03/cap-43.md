# Lezione 27. Test con JUnit 6 e AssertJ

## Punti chiave

### Perché i test automatici

- Controllo a occhio: lento, da ripetere ogni volta
- Un test è codice che verifica altro codice
- Veloce, ripetibile, avvisa appena qualcosa si rompe
- Una rete di sicurezza per cambiare il codice senza paura

> Percorso: codice, poi test, poi verde o rosso.

### Anatomia di un test

- Given, when, then: dati, azione, verifica
- Un solo comportamento per test
- Nomi leggibili: totalRejectsZeroQuantity
- JUnit 6 trova ed esegue i metodi con @Test

### Asserzioni fluenti con AssertJ

- assertThat(valore) seguito da verifiche in catena
- isEqualTo, contains, isPositive, startsWith
- assertThatThrownBy(...).isInstanceOf(...).hasMessage(...)
- Messaggio chiaro: expected 700 but was 750

## Codice della lezione

Il progetto parte dal modello Maven del corso: questi sono il suo `pom.xml` e il wrapper.

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

`.mvn/wrapper/maven-wrapper.properties`

~~~properties
wrapperVersion=3.3.4
distributionType=only-script
distributionUrl=https://repo.maven.apache.org/maven2/org/apache/maven/apache-maven/3.9.16/apache-maven-3.9.16-bin.zip
~~~

`src/test/java/PriceCalculatorTest.java`, prima versione

~~~java
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;
class PriceCalculatorTest {
    private final PriceCalculator calculator = new PriceCalculator();
    @Test
    void totalMultipliesPriceByQuantity() {
        int unitPriceInCents = 250;
        int quantity = 3;
        int total = calculator.totalInCents(unitPriceInCents, quantity);
        assertThat(total).isEqualTo(750);
    }
}
~~~

`src/test/java/PriceCalculatorTest.java`

~~~java
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
class PriceCalculatorTest {
    private final PriceCalculator calculator = new PriceCalculator();
    @Test
    void totalMultipliesPriceByQuantity() {
        int unitPriceInCents = 250;
        int quantity = 3;
        int total = calculator.totalInCents(unitPriceInCents, quantity);
        assertThat(total).isEqualTo(750);
    }
    @Test
    void totalRejectsZeroQuantity() {
        assertThatThrownBy(() -> calculator.totalInCents(250, 0))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Quantity must be positive");
    }
    @ParameterizedTest
    @CsvSource({
            "1000, 0, 1000",
            "1000, 10, 900",
            "2000, 25, 1500",
            "800, 100, 0"
    })
    void discountLowersPrice(int priceInCents, int percent, int expected) {
        int result = calculator.applyDiscount(priceInCents, percent);
        assertThat(result).isEqualTo(expected);
    }
}
~~~

`src/test/java/PriceCalculatorTest.java`, versione con un errore voluto: non compila o il test fallisce, per leggere il messaggio

~~~java
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;
class PriceCalculatorTest {
    private final PriceCalculator calculator = new PriceCalculator();
    @Test
    void totalMultipliesPriceByQuantity() {
        int unitPriceInCents = 250;
        int quantity = 3;
        int total = calculator.totalInCents(unitPriceInCents, quantity);
        assertThat(total).isEqualTo(700);
    }
}
~~~

`src/test/java/PriceCalculatorTest.java`, passaggio intermedio («exception»)

~~~java
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
class PriceCalculatorTest {
    private final PriceCalculator calculator = new PriceCalculator();
    @Test
    void totalMultipliesPriceByQuantity() {
        int unitPriceInCents = 250;
        int quantity = 3;
        int total = calculator.totalInCents(unitPriceInCents, quantity);
        assertThat(total).isEqualTo(750);
    }
    @Test
    void totalRejectsZeroQuantity() {
        assertThatThrownBy(() -> calculator.totalInCents(250, 0))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Quantity must be positive");
    }
}
~~~

`src/main/java/PriceCalculator.java`

~~~java
public class PriceCalculator {
    public int totalInCents(int unitPriceInCents, int quantity) {
        if (quantity <= 0) {
            throw new IllegalArgumentException("Quantity must be positive");
        }
        return unitPriceInCents * quantity;
    }
    public int applyDiscount(int priceInCents, int percent) {
        return priceInCents - priceInCents * percent / 100;
    }
}
~~~

## Riepilogo

- Test automatici: veloci, ripetibili, senza paura di cambiare
- Given, when, then e un comportamento per test
- AssertJ per verifiche leggibili, anche delle eccezioni
- @ParameterizedTest con @CsvSource: un metodo, tanti casi
