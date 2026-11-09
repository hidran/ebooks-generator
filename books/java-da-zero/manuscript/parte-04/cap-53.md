# Lezione 34b. Test double e Mockito senza Spring

## Punti chiave

### Una dipendenza da sostituire

- OrderService riceve PaymentGateway dal costruttore (lezione 34)
- Nei test niente Stripe vero: lento, costoso, fuori dal nostro controllo
- Al suo posto un doppione di test: test double

> Percorso: OrderServiceTest, poi OrderService, poi doppione di PaymentGateway.

### Quattro tipi di doppione

- Stub: risposte preparate, nessuna logica
- Mock: risponde e registra le chiamate, da verificare
- Fake: implementazione vera ma semplice, scritta a mano
- Spy: avvolge un oggetto vero e ne registra le chiamate (raro)

### Mockito senza Spring

- Senza -javaagent, da Java 21 la JVM avvisa:
- WARNING: A Java agent has been loaded dynamically
- WARNING: ... will be disallowed by default

### Fake o mock?

- Fake: lo stesso comportamento in molti test
- Mock: una risposta diversa in ogni test
- Niente mock di record e valori: Charge si crea con new
- Niente mock di repository in memoria semplici: si usano e basta

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
        <dependency>
            <groupId>org.mockito</groupId>
            <artifactId>mockito-junit-jupiter</artifactId>
            <version>5.24.0</version>
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
                <artifactId>maven-dependency-plugin</artifactId>
                <version>3.11.0</version>
                <executions>
                    <execution>
                        <goals>
                            <goal>properties</goal>
                        </goals>
                    </execution>
                </executions>
            </plugin>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.6.0</version>
                <configuration>
                    <argLine>-javaagent:${org.mockito:mockito-core:jar} -Xshare:off</argLine>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
~~~

`src/main/java/Charge.java`

~~~java
public record Charge(String orderId, int amountInCents) {
}
~~~

`src/main/java/PaymentGateway.java`

~~~java
public interface PaymentGateway {
    boolean charge(Charge charge);
}
~~~

`src/main/java/OrderService.java`

~~~java
public class OrderService {
    private final PaymentGateway payment;
    public OrderService(PaymentGateway payment) {
        this.payment = payment;
    }
    public String placeOrder(String orderId, int amountInCents) {
        if (amountInCents <= 0) {
            throw new IllegalArgumentException("amount must be positive");
        }
        int shipping = amountInCents < 2000 ? 500 : 0;
        boolean paid = payment.charge(new Charge(orderId, amountInCents + shipping));
        return paid ? "order " + orderId + " placed" : "order " + orderId + " declined";
    }
}
~~~

`src/test/java/FakePayment.java`

~~~java
import java.util.ArrayList;
import java.util.List;
public class FakePayment implements PaymentGateway {
    private final List<Charge> charges = new ArrayList<>();
    @Override
    public boolean charge(Charge charge) {
        charges.add(charge);
        return true;
    }
    public List<Charge> charges() {
        return List.copyOf(charges);
    }
}
~~~

`src/test/java/OrderServiceTest.java`, passaggio intermedio («fake»)

~~~java
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;
class OrderServiceTest {
    @Test
    void smallOrderPaysShipping() {
        FakePayment fake = new FakePayment();
        String result = new OrderService(fake).placeOrder("T-1", 1200);
        assertThat(result).isEqualTo("order T-1 placed");
        assertThat(fake.charges()).containsExactly(new Charge("T-1", 1700));
    }
}
~~~

`src/test/java/OrderServiceTest.java`

~~~java
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {
    @Mock
    PaymentGateway payment;
    @Test
    void smallOrderPaysShipping() {
        FakePayment fake = new FakePayment();
        String result = new OrderService(fake).placeOrder("T-1", 1200);
        assertThat(result).isEqualTo("order T-1 placed");
        assertThat(fake.charges()).containsExactly(new Charge("T-1", 1700));
    }
    @Test
    void declinedCardIsReported() {
        given(payment.charge(new Charge("T-2", 3000))).willReturn(false);
        String result = new OrderService(payment).placeOrder("T-2", 3000);
        assertThat(result).isEqualTo("order T-2 declined");
    }
    @Test
    void invalidAmountNeverCharges() {
        assertThatThrownBy(() -> new OrderService(payment).placeOrder("T-3", 0))
                .isInstanceOf(IllegalArgumentException.class);
        verify(payment, never()).charge(any());
    }
    @Test
    void largeOrderShipsForFree() {
        new OrderService(payment).placeOrder("T-4", 2500);
        ArgumentCaptor<Charge> captor = ArgumentCaptor.forClass(Charge.class);
        verify(payment).charge(captor.capture());
        assertThat(captor.getValue().amountInCents()).isEqualTo(2500);
    }
}
~~~

`src/test/java/OrderServiceTest.java`, passaggio intermedio («stub»)

~~~java
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {
    @Mock
    PaymentGateway payment;
    @Test
    void smallOrderPaysShipping() {
        FakePayment fake = new FakePayment();
        String result = new OrderService(fake).placeOrder("T-1", 1200);
        assertThat(result).isEqualTo("order T-1 placed");
        assertThat(fake.charges()).containsExactly(new Charge("T-1", 1700));
    }
    @Test
    void declinedCardIsReported() {
        given(payment.charge(new Charge("T-2", 3000))).willReturn(false);
        String result = new OrderService(payment).placeOrder("T-2", 3000);
        assertThat(result).isEqualTo("order T-2 declined");
    }
    @Test
    void invalidAmountNeverCharges() {
        given(payment.charge(any())).willReturn(true);
        assertThatThrownBy(() -> new OrderService(payment).placeOrder("T-3", 0))
                .isInstanceOf(IllegalArgumentException.class);
        verify(payment, never()).charge(any());
    }
    @Test
    void largeOrderShipsForFree() {
        new OrderService(payment).placeOrder("T-4", 2500);
        ArgumentCaptor<Charge> captor = ArgumentCaptor.forClass(Charge.class);
        verify(payment).charge(captor.capture());
        assertThat(captor.getValue().amountInCents()).isEqualTo(2500);
    }
}
~~~

`src/test/java/OrderServiceTest.java`, passaggio intermedio («mock»)

~~~java
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {
    @Mock
    PaymentGateway payment;
    @Test
    void smallOrderPaysShipping() {
        FakePayment fake = new FakePayment();
        String result = new OrderService(fake).placeOrder("T-1", 1200);
        assertThat(result).isEqualTo("order T-1 placed");
        assertThat(fake.charges()).containsExactly(new Charge("T-1", 1700));
    }
    @Test
    void declinedCardIsReported() {
        given(payment.charge(new Charge("T-2", 3000))).willReturn(false);
        String result = new OrderService(payment).placeOrder("T-2", 3000);
        assertThat(result).isEqualTo("order T-2 declined");
    }
}
~~~

`src/main/java/StripePayment.java`

~~~java
public class StripePayment implements PaymentGateway {
    @Override
    public boolean charge(Charge charge) {
        System.out.println("charged " + charge.amountInCents() + " cents via Stripe");
        return true;
    }
}
~~~

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw test
~~~

## Esercizio 34b: un fake a mano e il servizio che lo usa

Obiettivo: Sostituire il gateway di pagamento con un fake scritto a mano e completare il servizio che lo riceve dal costruttore.

*Su Udemy non c’è Mockito*: il doppione lo scrivi tu. In `Exercise.java` trovi `Charge`, `PaymentGateway` e `OrderService`, gli stessi nomi della lezione.

**Completa `FakePayment`**, un *fake* di `PaymentGateway`:

- il costruttore riceve `approves`, la risposta che il fake darà sempre;
- `charge` annota ogni `Charge` ricevuto, *anche quando rifiuta*, e restituisce `approves`;
- `charges()` restituisce una **copia** della lista degli addebiti, nell’ordine in cui sono arrivati, che non cambia quando ne arrivano altri.

Poi **completa `OrderService.placeOrder(orderId, amountInCents)`**:

- se l’importo è zero o negativo lancia `IllegalArgumentException` **senza toccare il gateway**;
- sotto i `2000` centesimi aggiunge `500` di spedizione, da `2000` in su niente;
- chiama `payment.charge` **una sola volta** con `new Charge(orderId, importo più spedizione)`;
- restituisce `"order " + orderId + " placed"` se il gateway approva, altrimenti `"order " + orderId + " declined"`.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
import java.util.ArrayList;
import java.util.List;

public class Exercise {

    public record Charge(String orderId, int amountInCents) {
    }

    public interface PaymentGateway {
        boolean charge(Charge charge);
    }

    public static class FakePayment implements PaymentGateway {

        private final boolean approves;
        private final List<Charge> charges = new ArrayList<>();

        public FakePayment(boolean approves) {
            this.approves = approves;
        }

        @Override
        public boolean charge(Charge charge) {
            // TODO: completa questo blocco.
            // Suggerimento: Aggiungi charge alla lista charges, anche quando il fake risponde false.
            // Poi restituisci il campo approves: il fake non decide niente, ripete la risposta con cui è stato creato.
            return false;
        }

        public List<Charge> charges() {
            // TODO: completa questo blocco.
            // Suggerimento: Restituisci una copia della lista, List.copyOf(charges), non la lista interna:
            // chi riceve la copia non può modificare il fake e non vede gli addebiti successivi.
            return List.of();
        }
    }

    public static class OrderService {

        private final PaymentGateway payment;

        public OrderService(PaymentGateway payment) {
            this.payment = payment;
        }

        public String placeOrder(String orderId, int amountInCents) {
            // TODO: completa questo blocco.
            // Suggerimento: Se amountInCents è zero o negativo lancia IllegalArgumentException prima di toccare payment.
            // Sotto 2000 centesimi aggiungi 500 di spedizione, da 2000 in su niente.
            // Chiama payment.charge una volta sola con new Charge(orderId, importo + spedizione).
            // Se risponde true restituisci "order " + orderId + " placed", altrimenti "order " + orderId + " declined".
            return "";
        }
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
import java.util.ArrayList;
import java.util.List;

public class Exercise {

    public record Charge(String orderId, int amountInCents) {
    }

    public interface PaymentGateway {
        boolean charge(Charge charge);
    }

    public static class FakePayment implements PaymentGateway {

        private final boolean approves;
        private final List<Charge> charges = new ArrayList<>();

        public FakePayment(boolean approves) {
            this.approves = approves;
        }

        @Override
        public boolean charge(Charge charge) {
            charges.add(charge);
            return approves;
        }

        public List<Charge> charges() {
            return List.copyOf(charges);
        }
    }

    public static class OrderService {

        private final PaymentGateway payment;

        public OrderService(PaymentGateway payment) {
            this.payment = payment;
        }

        public String placeOrder(String orderId, int amountInCents) {
            if (amountInCents <= 0) {
                throw new IllegalArgumentException("amount must be positive");
            }
            int shipping = 0;
            if (amountInCents < 2000) {
                shipping = 500;
            }
            boolean paid = payment.charge(new Charge(orderId, amountInCents + shipping));
            if (paid) {
                return "order " + orderId + " placed";
            }
            return "order " + orderId + " declined";
        }
    }
}
~~~

Nella lezione 34b sostituiamo il gateway di pagamento con un doppione. Su Udemy non c'è Mockito, quindi il doppione lo scrivi tu: `FakePayment`, che implementa `PaymentGateway`, e `OrderService`, che lo riceve dal costruttore. Un fake conviene quando lo stesso comportamento serve in molti test; il parametro `approves` gli dà la flessibilità di un mock, senza librerie.

Il fake annota ogni `Charge` in una lista e ripete la risposta decisa alla creazione, così lo stesso fake sa approvare o rifiutare. `charges()` restituisce `List.copyOf`, una copia: chi la legge non modifica il fake e non vede gli addebiti arrivati dopo. Il servizio controlla l'importo prima di toccare il gateway, aggiunge 500 centesimi sotto i 2000, chiama `charge` una volta sola e traduce la risposta in `placed` o `declined`.

Se il fake risponde sempre `true`, `fakeDeclinesWhenCreatedToDecline` fallisce. Se restituisce la lista interna, `fakeGivesASnapshotThatLaterChargesDoNotChange` la vede crescere. Se non annota gli addebiti rifiutati, `fakeRecordsDeclinedChargesToo` lo segnala. Nel servizio, `<=` al posto di `<` sulla soglia fa fallire `orderFromTwentyEuroShipsForFree`, mentre un secondo tentativo dopo il rifiuto rompe `callsTheGatewayExactlyOnceEvenWhenDeclined`. Validare dopo l'addebito è l'errore più grave: `rejectsAZeroAmountWithoutCallingTheGateway` trova una chiamata invece di zero. I test del servizio usano un gateway scritto nel test stesso, indipendente dal tuo fake. Infine `serviceAndFakeWorkTogetherForADeclinedOrder` li usa insieme, come il primo test della lezione.

## Riepilogo

- Prima il fake a mano, Mockito quando serve
- @ExtendWith(MockitoExtension.class) e @Mock
- given prepara, verify e never controllano
- Stub rigorosi: risposta mai usata, test rosso
- Mockito agente in argLine: niente avvisi
