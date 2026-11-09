# Lezione 27b. JUnit oltre le basi

## Punti chiave

### Test che si leggono come una specifica

- Tanti test in fila: preparazione ripetuta, report piatto
- @Nested raggruppa i test per situazione
- @DisplayName dà nomi leggibili nel report
- Il report diventa la specifica della classe

> Percorso: Cart, poi when empty, poi has a zero total.

### Il ciclo di vita di un test

- Un oggetto di test nuovo per ogni test
- @BeforeEach prepara prima di ogni test
- @AfterEach pulisce dopo: file, connessioni
- Prima i @BeforeEach esterni, poi quelli @Nested

> Percorso: @BeforeEach, poi @Test, poi @AfterEach.

### Tempo e file sotto controllo

- Il tempo entra dal costruttore: un Clock
- Nel programma: Clock.systemDefaultZone()
- Nel test: Clock.fixed(...), sempre la stessa data
- @TempDir: una cartella nuova per test, cancellata alla fine

## Codice della lezione

Il progetto parte dal modello Maven del corso: questi sono il suo `pom.xml` e il wrapper.

`pom.xml`: uguale a quello della lezione 27.

`.mvn/wrapper/maven-wrapper.properties`: uguale a quello della lezione 27.

`src/main/java/Cart.java`, passaggio intermedio («initial»)

~~~java
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.LocalDate;
public class Cart {
    private final Clock clock;
    private int itemCount;
    private int totalInCents;
    public Cart(Clock clock) {
        this.clock = clock;
    }
    public void add(int priceInCents, int quantity) {
        itemCount += 1;
        totalInCents += priceInCents;
    }
    public int itemCount() {
        return itemCount;
    }
    public int totalInCents() {
        return totalInCents;
    }
    public Path saveReceipt(Path folder) throws IOException {
        Path receipt = folder.resolve("receipt.txt");
        String text = LocalDate.now(clock) + " total " + totalInCents;
        return Files.writeString(receipt, text);
    }
}
~~~

`src/main/java/Cart.java`

~~~java
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.LocalDate;
public class Cart {
    private final Clock clock;
    private int itemCount;
    private int totalInCents;
    public Cart(Clock clock) {
        this.clock = clock;
    }
    public void add(int priceInCents, int quantity) {
        itemCount += quantity;
        totalInCents += priceInCents * quantity;
    }
    public int itemCount() {
        return itemCount;
    }
    public int totalInCents() {
        return totalInCents;
    }
    public Path saveReceipt(Path folder) throws IOException {
        Path receipt = folder.resolve("receipt.txt");
        String text = LocalDate.now(clock) + " total " + totalInCents;
        return Files.writeString(receipt, text);
    }
}
~~~

`src/test/java/CartTest.java`, prima versione

~~~java
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneId;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;
@DisplayName("Cart")
class CartTest {
    private final Clock clock =
            Clock.fixed(Instant.parse("2026-11-07T10:15:00Z"), ZoneId.of("UTC"));
    private Cart cart;
    @BeforeEach
    void createCart() {
        cart = new Cart(clock);
    }
    @Nested
    @DisplayName("when empty")
    class WhenEmpty {
        @Test
        @DisplayName("has a zero total")
        void hasZeroTotal() {
            assertThat(cart.totalInCents()).isZero();
        }
    }
    @Nested
    @DisplayName("with two products")
    class WithTwoProducts {
        @BeforeEach
        void addProducts() {
            cart.add(150, 2);
            cart.add(400, 1);
        }
        @Test
        @DisplayName("counts items and sums the total")
        void countsItemsAndSumsTotal() {
            assertThat(cart.itemCount()).isEqualTo(3);
            assertThat(cart.totalInCents()).isEqualTo(700);
        }
    }
}
~~~

`src/test/java/CartTest.java`

~~~java
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneId;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.SoftAssertions.assertSoftly;
@DisplayName("Cart")
class CartTest {
    private final Clock clock =
            Clock.fixed(Instant.parse("2026-11-07T10:15:00Z"), ZoneId.of("UTC"));
    private Cart cart;
    @BeforeEach
    void createCart() {
        cart = new Cart(clock);
    }
    @Nested
    @DisplayName("when empty")
    class WhenEmpty {
        @Test
        @DisplayName("has a zero total")
        void hasZeroTotal() {
            assertThat(cart.totalInCents()).isZero();
        }
    }
    @Nested
    @DisplayName("with two products")
    class WithTwoProducts {
        @BeforeEach
        void addProducts() {
            cart.add(150, 2);
            cart.add(400, 1);
        }
        @Test
        @DisplayName("counts items and sums the total")
        void countsItemsAndSumsTotal() {
            assertSoftly(softly -> {
                softly.assertThat(cart.itemCount()).isEqualTo(3);
                softly.assertThat(cart.totalInCents()).isEqualTo(700);
            });
        }
        @Test
        @DisplayName("saves a dated receipt")
        void savesDatedReceipt(@TempDir Path folder) throws IOException {
            Path receipt = cart.saveReceipt(folder);
            assertThat(Files.readString(receipt)).isEqualTo("2026-11-07 total 700");
        }
    }
}
~~~

`src/test/java/CartTest.java`, passaggio intermedio («soft»)

~~~java
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneId;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.SoftAssertions.assertSoftly;
@DisplayName("Cart")
class CartTest {
    private final Clock clock =
            Clock.fixed(Instant.parse("2026-11-07T10:15:00Z"), ZoneId.of("UTC"));
    private Cart cart;
    @BeforeEach
    void createCart() {
        cart = new Cart(clock);
    }
    @Nested
    @DisplayName("when empty")
    class WhenEmpty {
        @Test
        @DisplayName("has a zero total")
        void hasZeroTotal() {
            assertThat(cart.totalInCents()).isZero();
        }
    }
    @Nested
    @DisplayName("with two products")
    class WithTwoProducts {
        @BeforeEach
        void addProducts() {
            cart.add(150, 2);
            cart.add(400, 1);
        }
        @Test
        @DisplayName("counts items and sums the total")
        void countsItemsAndSumsTotal() {
            assertSoftly(softly -> {
                softly.assertThat(cart.itemCount()).isEqualTo(3);
                softly.assertThat(cart.totalInCents()).isEqualTo(700);
            });
        }
    }
}
~~~

## Esercizio 27b: un carrello con l’orologio iniettato

Obiettivo: Scrivere codice facile da testare: la data arriva da un Clock ricevuto dal costruttore e lo scontrino si salva in una cartella data.

In `Exercise.java` **completa la classe `Cart`**, un carrello che riceve un `Clock` dal costruttore invece di leggere l’orologio del computer.

1. **`add(priceInCents, quantity)`** lancia `IllegalArgumentException` se il prezzo è negativo o la quantità è minore di `1`, *senza modificare il carrello*; il prezzo `0` è valido. Se i valori sono validi, `itemCount` aumenta di `quantity` pezzi e `totalInCents` di prezzo per quantità.
2. **`receiptText()`** restituisce la data dell’orologio, il testo `" total "` e il totale, per esempio `"2026-11-07 total 700"`: `LocalDate.now(clock)` legge la data dal `Clock` ricevuto e, unita con `+` a un testo, si scrive nel formato `2026-11-07`. La data si legge **ogni volta** che si chiede lo scontrino.
3. **`saveReceipt(folder)`** scrive `receiptText()` nel file `receipt.txt` dentro la cartella ricevuta, sostituendo un file precedente, e restituisce il `Path` del file.

I test controllano l’orologio, che può cambiare giorno o fuso orario: il codice **non deve mai chiamare `LocalDate.now()` senza argomenti**.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.LocalDate;

public class Exercise {

    public static class Cart {

        private final Clock clock;
        private int itemCount;
        private int totalInCents;

        public Cart(Clock clock) {
            this.clock = clock;
        }

        public void add(int priceInCents, int quantity) {
            // TODO: completa questo blocco.
            // Suggerimento: Prima controlla: se priceInCents è negativo o quantity è minore di 1,
            // lancia IllegalArgumentException senza modificare niente.
            // Poi aggiungi quantity a itemCount e priceInCents * quantity a totalInCents.
        }

        public int itemCount() {
            return itemCount;
        }

        public int totalInCents() {
            return totalInCents;
        }

        public String receiptText() {
            // TODO: completa questo blocco.
            // Suggerimento: La data si legge dall’orologio ricevuto: LocalDate.now(clock), mai LocalDate.now() senza argomenti.
            // Unisci con + la data, il testo " total " e totalInCents: per esempio 2026-11-07 total 700.
            return "";
        }

        public Path saveReceipt(Path folder) throws IOException {
            // TODO: completa questo blocco.
            // Suggerimento: Il file si chiama receipt.txt dentro folder: folder.resolve("receipt.txt").
            // Files.writeString(file, testo) scrive il testo e restituisce il Path del file: restituiscilo.
            // Il testo è receiptText(): non rifare il calcolo della data qui.
            return folder;
        }
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.LocalDate;

public class Exercise {

    public static class Cart {

        private final Clock clock;
        private int itemCount;
        private int totalInCents;

        public Cart(Clock clock) {
            this.clock = clock;
        }

        public void add(int priceInCents, int quantity) {
            if (priceInCents < 0 || quantity < 1) {
                throw new IllegalArgumentException("Invalid price or quantity");
            }
            itemCount = itemCount + quantity;
            totalInCents = totalInCents + priceInCents * quantity;
        }

        public int itemCount() {
            return itemCount;
        }

        public int totalInCents() {
            return totalInCents;
        }

        public String receiptText() {
            return LocalDate.now(clock) + " total " + totalInCents;
        }

        public Path saveReceipt(Path folder) throws IOException {
            Path receipt = folder.resolve("receipt.txt");
            return Files.writeString(receipt, receiptText());
        }
    }
}
~~~

Udemy corregge `Exercise.java` con i nostri test, quindi il codice deve essere facile da provare dall'esterno. Completi `Cart`, un carrello che riceve un `Clock` dal costruttore: `add` valida e aggiorna i contatori, `receiptText` produce la data e il totale, `saveReceipt` scrive il file `receipt.txt` in una cartella ricevuta.

La soluzione legge la data con `LocalDate.now(clock)` ogni volta che serve lo scontrino. Il tempo entra dal costruttore, quindi i test possono passare un orologio fermo, o uno che avanza di un giorno, e il risultato diventa prevedibile. In `add` i controlli vengono prima delle modifiche, così un errore non lascia il carrello a metà. `Files.writeString` crea o sostituisce il file e restituisce il `Path`.

Gli errori tipici sono questi. `LocalDate.now()` senza argomenti viene smascherato da `comesFromTheClock`. Convertire l'istante in UTC a mano non supera `usesTheZoneOfTheClock`, perché alle 23:30 UTC a Roma è già il giorno dopo e a Los Angeles è ancora lo stesso, quindi una zona di sistema fissa fallisce comunque. Salvare la data nel costruttore non supera `isReadWhenRequested`. Se aggiorni i contatori prima di validare, `leavesCartUnchanged` trova il carrello cambiato. Se accetti la quantità zero o rifiuti il prezzo zero, falliscono `rejectsQuantityZero` e `acceptsFreeProduct`. Se aggiungi al file invece di sostituirlo, `replacesThePreviousReceipt` trova nel file due scontrini di fila. I test sono raggruppati con `@Nested`: nel report di JUnit li leggi come la specifica del carrello.

## Riepilogo

- @BeforeEach e @AfterEach: preparare e pulire
- @Nested e @DisplayName: un report che si legge
- assertSoftly: tutti gli errori in una volta
- @TempDir e Clock.fixed: test ripetibili
