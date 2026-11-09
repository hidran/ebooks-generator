# Lezione 24. File e I/O con java.nio.file

## Punti chiave

### Path e Files

- Path: l'indirizzo di un file, Path.of("orders.txt")
- Files: metodi statici che fanno il lavoro
- Scrivere, leggere, controllare, creare, cancellare

> Percorso: Path, poi Files.writeString, poi orders.txt, poi Files.readString.

### Testo, codifica ed errori

- Un file contiene byte: serve una codifica
- UTF-8: qualsiasi alfabeto, predefinita nei metodi di Files
- IOException è checked: si cattura o si dichiara con throws

### Buone abitudini

- Un percorso relativo dipende dalla cartella di lavoro
- writeString sovrascrive; per accodare: StandardOpenOption.APPEND
- readAllLines per file piccoli; lines con try-with-resources
- File di lavoro: createTempFile o createTempDirectory, poi delete

## Codice della lezione

`Main.java`, prima versione

~~~java
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
public class Main {
    public static void main(String[] args) throws IOException {
        Path file = Path.of("orders.txt");
        String text = "1001;Book;1500\n"
                + "1002;Coffee;300\n"
                + "1003;Lamp;4500\n";
        Files.writeString(file, text, StandardCharsets.UTF_8);
        System.out.println("orders.txt exists: " + Files.exists(file));
        String content = Files.readString(file, StandardCharsets.UTF_8);
        System.out.print(content);
        Path missing = Path.of("missing.txt");
        System.out.println("missing.txt exists: " + Files.exists(missing));
    }
}
~~~

`Main.java`

~~~java
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.stream.Stream;
public class Main {
    private static int priceOf(String line) {
        return Integer.parseInt(line.split(";")[2]);
    }
    public static void main(String[] args) {
        Path file = Path.of("orders.txt");
        String text = "1001;Book;1500\n"
                + "1002;Coffee;300\n"
                + "1003;Lamp;4500\n";
        try {
            Files.writeString(file, text);
            List<String> lines = Files.readAllLines(file);
            int total = 0;
            for (String line : lines) {
                total += priceOf(line);
            }
            System.out.println(lines.size() + " orders, " + total + " cents");
            try (Stream<String> stream = Files.lines(file)) {
                long big = stream.filter(line -> priceOf(line) > 1000).count();
                System.out.println("Over 1000 cents: " + big);
            }
            Path temp = Files.createTempFile("orders", ".txt");
            Files.writeString(temp, lines.getFirst());
            System.out.println("Temp copy: " + Files.readString(temp));
            Files.delete(temp);
            System.out.println("Temp deleted: " + !Files.exists(temp));
            System.out.println(Files.readString(Path.of("missing.txt")));
        } catch (IOException e) {
            System.out.println("Error: " + e);
        }
    }
}
~~~

## Esercizio 24: salvare e leggere un file

Obiettivo: Usare Path e Files con UTF-8 e propagare IOException.

**Implementa `roundTrip(file, content)`**:

1. scrivi `content` nel percorso ricevuto con `Files.writeString` e `UTF-8`,
2. poi rileggilo con `Files.readString`,
3. restituisci **il testo letto dal file**, non la stringa ricevuta.

Una seconda chiamata sullo stesso file deve **sostituire** il contenuto precedente.

**Non usare percorsi assoluti fissi**. Il file si trova in una cartella esistente.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;

public class Exercise {

    public String roundTrip(Path file, String content) throws IOException {
        // TODO: completa questo blocco.
        // Suggerimento: Usa il Path ricevuto: non serve creare un percorso fisso.
        // Scrivi con Files.writeString e poi restituisci Files.readString, entrambi con UTF-8.
        return "";
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;

public class Exercise {

    public String roundTrip(Path file, String content) throws IOException {
        Files.writeString(file, content, StandardCharsets.UTF_8);
        return Files.readString(file, StandardCharsets.UTF_8);
    }
}
~~~

Dobbiamo scrivere un testo in un file e rileggerlo, restituendo quello che troviamo davvero sul disco.

Il metodo ha due righe. `Files.writeString(file, content, StandardCharsets.UTF_8)` scrive il testo nel percorso ricevuto, e `Files.readString(file, StandardCharsets.UTF_8)` lo rilegge. Come abbiamo visto nella lezione 24, `Path` indica il file e `Files` fa il lavoro. Usiamo il `Path` che ci passano, senza costruire percorsi fissi: così il metodo funziona in qualsiasi cartella, compresi i file temporanei che i test creano con `createTempFile`.

UTF-8 è già la codifica predefinita dei metodi di `Files`, ma scriverla rende chiara l'intenzione, ed è un'abitudine che ti evita sorprese con le lettere accentate. `writeString` senza opzioni sovrascrive il file, ed è proprio quello che chiede la consegna. `IOException` è un'eccezione checked: la firma la dichiara con `throws`, quindi non serve nessun `try`, e un eventuale errore arriva a chi chiama.

Un errore tipico è aggiungere `StandardOpenOption.APPEND`. Il test `replacesExistingContentIncludingEmptyString` scrive prima `"old content"` e poi `"new"`, e si aspetta `"new"`, non il testo accodato. Lo stesso test scrive infine una stringa vuota e si aspetta `""`. Il test `preservesUnicodeAndNewlines` usa invece `"Caffè\nJava è utile"`, con accenti e un a capo. Una scorciatoia è restituire `content` senza rileggere: il metodo non dimostrerebbe più che il testo è arrivato sul disco. Il test `returnsTheTextReadBackFromTheFile` la scopre, perché una stringa letta dal file è un oggetto nuovo e `assertNotSame` si aspetta che sia diversa da quella ricevuta.

## Riepilogo

- Path indica il file, Files fa il lavoro
- writeString, readString, readAllLines, lines, exists
- UTF-8 sempre; IOException con throws o catch
