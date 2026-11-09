# Lezione 28. Maven, dipendenze, build e ciclo di vita

## Punti chiave

### Perché Maven

- Scarica le librerie, compila, esegue i test, impacchetta
- Stessi comandi su ogni computer e sul server di build
- Il progetto è descritto da un file: pom.xml
- Struttura standard: src/main/java e src/test/java

> Percorso: pom.xml, poi Maven, poi file jar.

### Il ciclo di vita

- Ogni fase esegue prima tutte le precedenti
- Un test che fallisce ferma la build: niente jar
- clean è un ciclo a parte: cancella la cartella target

> Percorso: validate, poi compile, poi test, poi package, poi verify, poi install.

### Dipendenze e repository locale

- Transitive: le dipendenze delle nostre dipendenze
- Scaricate una volta sola da Maven Central
- Conservate nel repository locale: ~/.m2/repository
- dependency:tree mostra l'albero completo

> Percorso: Maven Central, poi ~/.m2/repository, poi ogni progetto.

## Codice della lezione

Il progetto parte dal modello Maven del corso: questi sono il suo `pom.xml` e il wrapper.

`pom.xml`: uguale a quello della lezione 27.

`.mvn/wrapper/maven-wrapper.properties`: uguale a quello della lezione 27.

`src/main/java/PriceCalculator.java`

~~~java
public class PriceCalculator {
    public static int total(int priceInCents, int quantity) {
        return priceInCents * quantity;
    }
    public static int applyDiscount(int amountInCents, int percent) {
        return amountInCents - amountInCents * percent / 100;
    }
    public static void main(String[] args) {
        int total = applyDiscount(total(1200, 3), 10);
        System.out.println("Total with discount: " + total + " cents");
    }
}
~~~

`src/test/java/PriceCalculatorTest.java`

~~~java
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;
class PriceCalculatorTest {
    @Test
    void multipliesPriceByQuantity() {
        assertThat(PriceCalculator.total(1200, 3)).isEqualTo(3600);
    }
    @Test
    void appliesPercentDiscount() {
        assertThat(PriceCalculator.applyDiscount(3600, 10)).isEqualTo(3240);
    }
    @Test
    void zeroDiscountKeepsTheAmount() {
        assertThat(PriceCalculator.applyDiscount(3600, 0)).isEqualTo(3600);
    }
}
~~~

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
ls
ls src/main/java src/test/java
cat src/main/java/PriceCalculator.java
cat .mvn/wrapper/maven-wrapper.properties
./mvnw -v
./mvnw test
./mvnw clean package
ls target
java -cp target/classes PriceCalculator
java -cp target/lab-1.0-SNAPSHOT.jar PriceCalculator
./mvnw test -Dtest=PriceCalculatorTest#appliesPercentDiscount
./mvnw dependency:tree
~~~

## Riepilogo

- pom.xml: coordinate, properties, dipendenze con scope, plugin
- Wrapper mvnw: la stessa versione di Maven per tutti
- Fasi in ordine: ognuna esegue le precedenti
