# Lezione 24f. File che arrivano da altri sistemi: charset e CSV

## Punti chiave

### Che cos'è un charset

- Un byte è un numero da 0 a 255
- ASCII: da 0 a 127, niente lettere accentate
- ISO-8859-1 e Windows-1252: un byte, la "è" vale 232
- UTF-8: la "è" occupa due byte

> Percorso: carattere, poi charset, poi byte.

### Il charset si scrive sempre

- Il file non dice il suo charset: va chiesto a chi lo scrive
- StandardCharsets.UTF_8, ISO_8859_1, US_ASCII
- Charset.forName("windows-1252") per gli altri
- Windows-1252 ha l'euro e le virgolette curve, ISO-8859-1 no

### Il listino del fornitore

- Export di Excel: separatore punto e virgola
- Prima riga: id;name;priceInCents
- Righe buone nei prodotti, righe sbagliate negli scarti
- Ogni scarto: numero di riga, riga e motivo

### Errori tipici e altri formati

- "1003;Lamp;;".split(";") dà 2 campi, con -1 ne dà 4
- Il BOM e i byte: "Caffè" è 5 caratteri, 6 byte in UTF-8
- Larghezza fissa: il tracciato conta da 1, substring da 0
- Mainframe: EBCDIC, per l'Italia Charset.forName("IBM280")

## Codice della lezione

`Product.java`

~~~java
public record Product(long id, String name, int priceInCents) {
}
~~~

`ImportResult.java`

~~~java
import java.util.List;
public record ImportResult(List<Product> products,
        List<Rejected> rejected) {
    public record Rejected(int lineNumber, String line, String reason) {
    }
}
~~~

`supplier/products.csv`

~~~csv
id;name;priceInCents
1001;Book;1500
1002;Caffè;300
1003;Lamp;
abc;Pen;120
1005;Tazza;-50
~~~

`supplier/products-bom.csv`

~~~csv
﻿id;name;priceInCents
2001;Tè verde;450
2002;Moka;2490
~~~

`ProductCsvReader.java`, passaggio intermedio («nobom»)

~~~java
import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
public final class ProductCsvReader {
    private static final String HEADER = "id;name;priceInCents";
    public ImportResult read(Path file, Charset charset)
            throws IOException {
        List<Product> products = new ArrayList<>();
        List<ImportResult.Rejected> rejected = new ArrayList<>();
        try (var reader = Files.newBufferedReader(file, charset)) {
            String header = reader.readLine();
            if (header == null) {
                throw new IOException("Empty file: " + file);
            }
            if (!header.equals(HEADER)) {
                throw new IOException("Unexpected header: " + header);
            }
            int lineNumber = 1;
            String line;
            while ((line = reader.readLine()) != null) {
                lineNumber++;
                if (line.isBlank()) {
                    continue;
                }
                try {
                    products.add(parse(line));
                } catch (IllegalArgumentException e) {
                    rejected.add(new ImportResult.Rejected(
                            lineNumber, line, e.getMessage()));
                }
            }
        }
        return new ImportResult(products, rejected);
    }
    private Product parse(String line) {
        String[] fields = line.split(";", -1);
        if (fields.length != 3) {
            throw new IllegalArgumentException(
                    "expected 3 fields, found " + fields.length);
        }
        long id = Long.parseLong(fields[0].strip());
        String name = fields[1].strip();
        if (name.isEmpty()) {
            throw new IllegalArgumentException("name is empty");
        }
        int priceInCents = Integer.parseInt(fields[2].strip());
        if (priceInCents < 0) {
            throw new IllegalArgumentException(
                    "negative price: " + priceInCents);
        }
        return new Product(id, name, priceInCents);
    }
}
~~~

`Main.java`, prima versione

~~~java
import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.file.Path;
public class Main {
    public static void main(String[] args) {
        Path file = Path.of("supplier/products.csv");
        Charset charset = Charset.forName("windows-1252");
        ProductCsvReader reader = new ProductCsvReader();
        try {
            ImportResult result = reader.read(file, charset);
            result.products().forEach(System.out::println);
            result.rejected().forEach(System.out::println);
        } catch (IOException e) {
            System.out.println("Import failed: " + e);
        }
    }
}
~~~

`Main.java`, passaggio intermedio («utf8»)

~~~java
import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
public class Main {
    public static void main(String[] args) {
        Path file = Path.of("supplier/products.csv");
        Charset charset = StandardCharsets.UTF_8;
        ProductCsvReader reader = new ProductCsvReader();
        try {
            ImportResult result = reader.read(file, charset);
            result.products().forEach(System.out::println);
            result.rejected().forEach(System.out::println);
        } catch (IOException e) {
            System.out.println("Import failed: " + e);
        }
    }
}
~~~

`Main.java`

~~~java
import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
public class Main {
    public static void main(String[] args) {
        Path file = Path.of("supplier/products-bom.csv");
        Charset charset = StandardCharsets.UTF_8;
        ProductCsvReader reader = new ProductCsvReader();
        try {
            ImportResult result = reader.read(file, charset);
            result.products().forEach(System.out::println);
            result.rejected().forEach(System.out::println);
        } catch (IOException e) {
            System.out.println("Import failed: " + e);
        }
    }
}
~~~

`ProductCsvReader.java`

~~~java
import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
public final class ProductCsvReader {
    private static final String HEADER = "id;name;priceInCents";
    private static final String BOM = "\uFEFF";
    public ImportResult read(Path file, Charset charset)
            throws IOException {
        List<Product> products = new ArrayList<>();
        List<ImportResult.Rejected> rejected = new ArrayList<>();
        try (var reader = Files.newBufferedReader(file, charset)) {
            String header = reader.readLine();
            if (header == null) {
                throw new IOException("Empty file: " + file);
            }
            if (header.startsWith(BOM)) {
                header = header.substring(1);
            }
            if (!header.equals(HEADER)) {
                throw new IOException("Unexpected header: " + header);
            }
            int lineNumber = 1;
            String line;
            while ((line = reader.readLine()) != null) {
                lineNumber++;
                if (line.isBlank()) {
                    continue;
                }
                try {
                    products.add(parse(line));
                } catch (IllegalArgumentException e) {
                    rejected.add(new ImportResult.Rejected(
                            lineNumber, line, e.getMessage()));
                }
            }
        }
        return new ImportResult(products, rejected);
    }
    private Product parse(String line) {
        String[] fields = line.split(";", -1);
        if (fields.length != 3) {
            throw new IllegalArgumentException(
                    "expected 3 fields, found " + fields.length);
        }
        long id = Long.parseLong(fields[0].strip());
        String name = fields[1].strip();
        if (name.isEmpty()) {
            throw new IllegalArgumentException("name is empty");
        }
        int priceInCents = Integer.parseInt(fields[2].strip());
        if (priceInCents < 0) {
            throw new IllegalArgumentException(
                    "negative price: " + priceInCents);
        }
        return new Product(id, name, priceInCents);
    }
}
~~~

`CharsetDemo.java`

~~~java
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
public class CharsetDemo {
    public static void main(String[] args) {
        Charset windows = Charset.forName("windows-1252");
        byte[] utf8 = "Caffè".getBytes(StandardCharsets.UTF_8);
        byte[] ansi = "Caffè".getBytes(windows);
        System.out.println(Arrays.toString(utf8));
        System.out.println(Arrays.toString(ansi));
        System.out.println(new String(utf8, windows));
        System.out.println(new String(ansi, StandardCharsets.UTF_8));
    }
}
~~~

## Esercizio 24f: una riga di listino da un altro sistema

Obiettivo: Leggere una riga CSV con punto e virgola senza perdere i campi vuoti, togliendo il BOM iniziale e decodificando i byte con il charset giusto.

Il fornitore dello Shop manda un listino CSV con il punto e virgola: `id;name;priceInCents`, per esempio `7;Tea;120`. `Product` e la costante `BOM` sono già pronti.

1. **Completa `parseLine(line)`**: se la riga inizia con il *BOM* (`\uFEFF`, il carattere invisibile che Excel mette all’inizio dei file UTF-8), toglilo con `substring(1)`. Dividi poi la riga con `split(";", -1)`: il secondo argomento `-1` **tiene anche i campi vuoti** in fondo.
2. I campi devono essere **esattamente tre**, altrimenti lancia `IllegalArgumentException` con il messaggio `expected 3 fields, found N`, dove `N` è il numero trovato. Dopo `strip()` l’id è un `long`, il prezzo un `int`; il nome non può essere vuoto (`name is empty`) e il prezzo non può essere negativo (`negative price: -5`). Gli errori di `Long.parseLong` e `Integer.parseInt` non vanno catturati: sono `NumberFormatException`, una sottoclasse di `IllegalArgumentException`.
3. **Completa `decodeLine(bytes, charset)`**: trasforma i byte in testo con `new String(bytes, charset)`, usando **il charset ricevuto**, e passa il testo a `parseLine`.

Un file non dice in che charset è scritto: lo decide chi lo produce, per questo il charset si passa sempre in modo esplicito e mai quello predefinito.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
import java.nio.charset.Charset;

public class Exercise {

    public record Product(long id, String name, int priceInCents) {}

    private static final String BOM = "\uFEFF";

    public Product parseLine(String line) {
        // TODO: completa questo blocco.
        // Suggerimento: Se line.startsWith(BOM), togli il primo carattere con line.substring(1).
        // Poi line.split(";", -1) tiene anche i campi vuoti: se i campi non sono esattamente 3,
        // lancia IllegalArgumentException("expected 3 fields, found " + fields.length).
        // Long.parseLong sull'id, strip() sul nome (vuoto: "name is empty") e Integer.parseInt sul prezzo
        // (negativo: "negative price: " + priceInCents). Applica strip() anche a id e prezzo prima di convertirli.
        return new Product(0, "", 0);
    }

    public Product decodeLine(byte[] bytes, Charset charset) {
        // TODO: completa questo blocco.
        // Suggerimento: Trasforma i byte in testo con new String(bytes, charset): il charset è quello ricevuto.
        // Poi passa il testo a parseLine, che sa già togliere il BOM.
        return new Product(0, "", 0);
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
import java.nio.charset.Charset;

public class Exercise {

    public record Product(long id, String name, int priceInCents) {}

    private static final String BOM = "\uFEFF";

    public Product parseLine(String line) {
        if (line.startsWith(BOM)) {
            line = line.substring(1);
        }
        String[] fields = line.split(";", -1);
        if (fields.length != 3) {
            throw new IllegalArgumentException("expected 3 fields, found " + fields.length);
        }
        long id = Long.parseLong(fields[0].strip());
        String name = fields[1].strip();
        if (name.isEmpty()) {
            throw new IllegalArgumentException("name is empty");
        }
        int priceInCents = Integer.parseInt(fields[2].strip());
        if (priceInCents < 0) {
            throw new IllegalArgumentException("negative price: " + priceInCents);
        }
        return new Product(id, name, priceInCents);
    }

    public Product decodeLine(byte[] bytes, Charset charset) {
        return parseLine(new String(bytes, charset));
    }
}
~~~

In questo esercizio leggi una riga del listino che un fornitore ti manda in CSV, con il punto e virgola. Completi `parseLine`, che trasforma la riga in un `Product`, e `decodeLine`, che parte dai byte e da un charset che ricevi dal chiamante. Il file arriva da un altro sistema, quindi non puoi dare per scontato ciò che contiene.

La soluzione funziona in tre mosse. Prima toglie il BOM, il carattere invisibile `U+FEFF` che Excel mette all'inizio dei file UTF-8 e che Java non elimina da solo. Poi divide con `split(";", -1)`: il `-1` conserva i campi vuoti in fondo, così puoi contare i campi davvero presenti e rifiutare le righe che non ne hanno tre. Infine pulisce ogni campo con `strip()` e li converte uno alla volta. `decodeLine` usa `new String(bytes, charset)` con il charset ricevuto, mai quello della JVM.

Gli errori tipici sono questi. Senza il `-1`, la riga `7;Tea;120;` sembra corretta e `parseLineKeepsTheEmptyFieldAtTheEndAndSeesAFourthField` fallisce, mentre `7;Tea;` produce l'errore sbagliato e lo smaschera `parseLineKeepsTheEmptyPriceAtTheEnd`. Se dimentichi il BOM, `parseLineRemovesTheLeadingBom` e `decodeLineRemovesTheBomOfAUtf8File` ricevono una `NumberFormatException`. Se ignori `strip()`, il `\r` dei file Windows rompe `parseLineIgnoresTheCarriageReturnOfWindowsFiles`. Se decodifichi sempre in UTF-8, `decodeLineReadsWindows1252WithAnExplicitCharset` mostra il mojibake, e `decodeLineUsesTheCharsetItReceivesNotAnotherOne` verifica che il charset passato venga davvero usato. Leggi il nome del test fallito prima di cambiare il codice: dice quale comportamento manca.

> Per andare oltre: il capitolo «Approfondimento 3. File che arrivano da altri sistemi», nella parte Java in azienda, riprende questo argomento con i casi che si incontrano nei sistemi reali.

## Riepilogo

- Un charset collega caratteri e byte: il file non dice il suo
- Charset sbagliato: mojibake o MalformedInputException
- Il charset si passa sempre a newBufferedReader e readString
- split(";", -1), via il BOM, e gli scarti con il motivo
