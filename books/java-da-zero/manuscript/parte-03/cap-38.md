# Lezione 24d. Byte, stream e archivi ZIP

## Punti chiave

### Testo e byte

- Un file contiene solo byte
- Una codifica (charset) trasforma i byte in caratteri
- UTF-8: "Caffè" ha 5 caratteri e 6 byte
- Stessa codifica in scrittura e in lettura: sempre UTF-8

> Percorso: testo, poi UTF-8, poi byte, poi file.

### Due famiglie di stream

- InputStream e OutputStream: byte (archivi, immagini, copie)
- Reader e Writer: caratteri, sempre con una codifica
- Files.newBufferedReader e newBufferedWriter: testo a blocchi
- Files.newInputStream e newOutputStream: byte
- in.transferTo(out): copia tutto da uno stream all'altro

### Cosa non ci serve (KISS)

- Una libreria CSV per un formato semplice
- Serve quando i campi contengono virgole, virgolette o a capo
- "Penne, confezione da 10": virgolette, quelle interne raddoppiate
- Una libreria ZIP: java.util.zip è già nel JDK

### Prima e dopo: KISS

- Prima: byte[] buffer = new byte[8192]; int n;
- while ((n = in.read(buffer)) != -1) out.write(buffer, 0, n);
- Dopo: in.transferTo(out);
- Stesso risultato, meno codice da leggere e da sbagliare

## Codice della lezione

`CsvExport.java`

~~~java
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
public class CsvExport {
    private static final String[] PRODUCTS = {"Book", "Lamp", "Caffè", "Mug"};
    private static final int[] PRICES = {1500, 4500, 300, 800};
    private static String csvLine(int id) {
        return id + "," + PRODUCTS[id % 4] + "," + PRICES[id % 4] + "\n";
    }
    public static void main(String[] args) throws IOException {
        String word = "Caffè";
        System.out.println(word + ": " + word.length() + " chars, "
                + word.getBytes(StandardCharsets.UTF_8).length + " bytes");
        Path month = Files.createDirectories(Path.of("exports", "2026-09"));
        Path csv = month.resolve("orders.csv");
        try (BufferedWriter out =
                Files.newBufferedWriter(csv, StandardCharsets.UTF_8)) {
            out.write("id,product,cents\n");
            for (int id = 1; id <= 100_000; id++) {
                out.write(csvLine(id));
            }
        }
        System.out.println("CSV: " + Files.size(csv) + " bytes");
        long count = 0;
        long total = 0;
        try (BufferedReader in =
                Files.newBufferedReader(csv, StandardCharsets.UTF_8)) {
            in.readLine();
            String line;
            while ((line = in.readLine()) != null) {
                count++;
                total += Integer.parseInt(line.split(",")[2]);
            }
        }
        String summary = count + " orders, " + total + " cents";
        Files.writeString(month.resolve("summary.txt"), summary);
        System.out.println(summary);
    }
}
~~~

`MonthArchive.java`

~~~java
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import java.util.zip.ZipOutputStream;
public class MonthArchive {
    public static void main(String[] args) throws IOException {
        Path month = Path.of("exports", "2026-09");
        Path zip = Path.of("exports", "2026-09.zip");
        try (ZipOutputStream out =
                new ZipOutputStream(Files.newOutputStream(zip))) {
            for (String name : List.of("orders.csv", "summary.txt")) {
                out.putNextEntry(new ZipEntry(name));
                try (InputStream in = Files.newInputStream(month.resolve(name))) {
                    in.transferTo(out);
                }
                out.closeEntry();
            }
        }
        System.out.println("Archive: " + Files.size(zip) + " bytes");
        try (ZipInputStream in =
                new ZipInputStream(Files.newInputStream(zip))) {
            ZipEntry entry;
            while ((entry = in.getNextEntry()) != null) {
                long bytes = in.transferTo(OutputStream.nullOutputStream());
                System.out.println(entry.getName() + ": " + bytes + " bytes");
            }
        }
    }
}
~~~

## Esercizio 24d: CSV a mano e archivio ZIP

Obiettivo: Scrivere e leggere testo con Buffered Writer e Buffered Reader in UTF-8, copiare byte con transferTo e creare un archivio ZIP.

1. **Implementa `exportCsv(csv, orders)`**: scrivi nel file l'intestazione `id,product,cents` e poi una riga per ordine, con i campi separati da virgole; ogni riga finisce con `\n`. Usa `Files.newBufferedWriter` con `UTF-8`: un contenuto precedente va sostituito. I nomi dei prodotti non contengono virgole né virgolette.
2. **Implementa `totalCents(csv)`**: leggi il file riga per riga con `Files.newBufferedReader` e `UTF-8`, salta l'intestazione e restituisci la somma del terzo campo; il file può essere grande, quindi **non caricarlo tutto in memoria** (niente `Files.readAllLines`, `Files.readString` o `Files.readAllBytes`), e il totale può superare il limite di un `int`.
3. **Implementa `zipFiles(zip, files)`**: crea l'archivio con `ZipOutputStream` e una voce per ogni file, nell'ordine ricevuto; il nome della voce è solo il nome del file, senza cartelle, e il contenuto si copia byte per byte con `transferTo`.

I file e le loro cartelle esistono.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

public class Exercise {

    public record Order(int id, String product, int cents) {}

    public void exportCsv(Path csv, List<Order> orders) throws IOException {
        // TODO: completa questo blocco.
        // Suggerimento: Apri Files.newBufferedWriter con UTF-8 in un try-with-resources.
        // Scrivi prima l’intestazione, poi i campi di ogni Order con gli accessori e una nuova riga.
    }

    public long totalCents(Path csv) throws IOException {
        // TODO: completa questo blocco.
        // Suggerimento: Apri il reader in un try-with-resources e leggi una prima riga per saltare l’intestazione.
        // Continua con readLine() fino a null; split(",") separa i campi.
        // Usa long per la somma e Long.parseLong per il terzo campo.
        return 0;
    }

    public void zipFiles(Path zip, List<Path> files) throws IOException {
        // TODO: completa questo blocco.
        // Suggerimento: Apri ZipOutputStream in un try-with-resources.
        // Per ogni Path crea una ZipEntry col solo nome, chiama putNextEntry e apri l’InputStream.
        // Copia con transferTo, chiudi l’input e chiama closeEntry prima del prossimo file.
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

public class Exercise {

    public record Order(int id, String product, int cents) {}

    public void exportCsv(Path csv, List<Order> orders) throws IOException {
        try (BufferedWriter out = Files.newBufferedWriter(csv, StandardCharsets.UTF_8)) {
            out.write("id,product,cents\n");
            for (Order order : orders) {
                out.write(order.id() + "," + order.product() + "," + order.cents() + "\n");
            }
        }
    }

    public long totalCents(Path csv) throws IOException {
        long total = 0;
        try (BufferedReader in = Files.newBufferedReader(csv, StandardCharsets.UTF_8)) {
            in.readLine();
            String line;
            while ((line = in.readLine()) != null) {
                total += Long.parseLong(line.split(",")[2]);
            }
        }
        return total;
    }

    public void zipFiles(Path zip, List<Path> files) throws IOException {
        try (ZipOutputStream out = new ZipOutputStream(Files.newOutputStream(zip))) {
            for (Path file : files) {
                out.putNextEntry(new ZipEntry(file.getFileName().toString()));
                try (InputStream in = Files.newInputStream(file)) {
                    in.transferTo(out);
                }
                out.closeEntry();
            }
        }
    }
}
~~~

Vogliamo scrivere un piccolo CSV, rileggerlo per sommare gli importi e poi impacchettare dei file in uno ZIP, usando solo il JDK.

In `exportCsv` apriamo un `BufferedWriter` con `Files.newBufferedWriter` e `StandardCharsets.UTF_8` dentro un try-with-resources. Senza opzioni, il file viene creato o svuotato, quindi il vecchio contenuto sparisce. Ogni ordine diventa una riga con le virgole e un `\n` finale: come abbiamo visto nella lezione 24d, per un formato così semplice una libreria CSV non serve.

In `totalCents` leggiamo con un `BufferedReader` una riga alla volta. Il primo `readLine` scarta l'intestazione, il `while` si ferma quando `readLine` restituisce `null`. Sommiamo il terzo campo in un `long` con `Long.parseLong`, così il file non sta mai tutto in memoria e il totale non va in overflow.

In `zipFiles` appoggiamo uno `ZipOutputStream` su `Files.newOutputStream`. Per ogni file, `putNextEntry` apre una voce con il solo `getFileName()`, `transferTo` copia i byte e `closeEntry` chiude la voce.

L'errore più comune è sommare in un `int`: il test con tre auto da `2000000000` centesimi si aspetta `6_000_000_000L` e con un `int` otterresti un numero negativo. Un altro è dimenticare di saltare l'intestazione: `Long.parseLong("cents")` lancia `NumberFormatException`. Se invece usi l'intero percorso come nome della voce, il test non trova `logo.bin` e `orders.csv` nell'ordine atteso.

Anche `Files.readAllLines`, `Files.readString` e `Files.readAllBytes` caricano tutto il file in memoria, proprio ciò che il testo ci chiede di evitare. Il test `totalCentsReadsLineByLineWithoutLoadingTheWholeFile` passa a `totalCents` un file generato al volo e fallisce se il metodo usa uno di questi tre.

## Riepilogo

- Un file è fatto di byte: UTF-8 li trasforma in testo
- Byte: InputStream, OutputStream; testo: Reader, Writer
- File grandi: readLine riga per riga; readAllLines solo se piccoli
- try-with-resources: close scrive l'ultimo blocco e l'indice dello ZIP
- ZipOutputStream, putNextEntry, transferTo; ZipInputStream rilegge
