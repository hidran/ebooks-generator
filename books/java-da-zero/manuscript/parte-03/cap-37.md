# Lezione 24c. Copiare, spostare, cancellare

## Punti chiave

### Copiare e spostare

- Files.copy(da, a): l'originale resta al suo posto
- Files.move(da, a): l'originale sparisce
- Destinazione già presente: errore, a meno di REPLACE_EXISTING
- ATOMIC_MOVE: lo spostamento avviene in un solo passo

> Percorso: exports, poi Files.move, poi archive.

### Eccezioni con un nome preciso

- NoSuchFileException: il file non esiste
- FileAlreadyExistsException: la destinazione c'è già
- DirectoryNotEmptyException: la cartella non è vuota
- Sono tutte sottoclassi di IOException

### Quello che non ci serve (KISS)

- Una libreria esterna per copiare o cancellare
- Un FileVisitor: bastano walk e una lista rovesciata
- La vecchia java.io.File: delete restituisce solo false
- Files ci dà già eccezioni con un nome preciso

### La scrittura sicura

- Prima: writeString direttamente sul file finale
- Chi legge a metà scrittura trova un file incompleto
- Dopo: file temporaneo nella stessa cartella, poi ATOMIC_MOVE
- Principio: atomicità, tutto o niente

> Percorso: testo, poi safe123.tmp, poi ATOMIC_MOVE, poi index.txt.

## Codice della lezione

`Archiver.java`, prima versione

~~~java
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.attribute.FileTime;
public class Archiver {
    public static void main(String[] args) {
        Path from = Path.of("exports", "2026", "09", "orders.csv");
        Path to = Path.of("archive", "2026-09-orders.csv");
        try {
            long size = Files.size(from);
            FileTime modified = Files.getLastModifiedTime(from);
            System.out.println(size + " bytes, modified " + modified);
            Files.copy(from, to);
            System.out.println("In archive: " + Files.exists(to));
            System.out.println("In exports: " + Files.exists(from));
        } catch (IOException e) {
            System.out.println("Error: " + e);
        }
    }
}
~~~

`Archiver.java`, passaggio intermedio («copy»)

~~~java
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.attribute.FileTime;
public class Archiver {
    public static void main(String[] args) {
        Path from = Path.of("exports", "2026", "09", "orders.csv");
        Path to = Path.of("archive", "2026-09-orders.csv");
        try {
            long size = Files.size(from);
            FileTime modified = Files.getLastModifiedTime(from);
            System.out.println(size + " bytes, modified " + modified);
            Files.copy(from, to, StandardCopyOption.REPLACE_EXISTING);
            System.out.println("In archive: " + Files.exists(to));
            System.out.println("In exports: " + Files.exists(from));
        } catch (IOException e) {
            System.out.println("Error: " + e);
        }
    }
}
~~~

`Archiver.java`

~~~java
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.attribute.FileTime;
public class Archiver {
    public static void main(String[] args) {
        Path from = Path.of("exports", "2026", "09", "orders.csv");
        Path to = Path.of("archive", "2026-09-orders.csv");
        try {
            long size = Files.size(from);
            FileTime modified = Files.getLastModifiedTime(from);
            System.out.println(size + " bytes, modified " + modified);
            Files.move(from, to, StandardCopyOption.REPLACE_EXISTING);
            System.out.println("In archive: " + Files.exists(to));
            System.out.println("In exports: " + Files.exists(from));
        } catch (IOException e) {
            System.out.println("Error: " + e);
        }
    }
}
~~~

`Cleanup.java`, prima versione

~~~java
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
public class Cleanup {
    public static void main(String[] args) {
        Path old = Path.of("exports", "2025");
        try {
            Files.delete(old);
        } catch (IOException e) {
            System.out.println("Error: " + e);
        }
    }
}
~~~

`Cleanup.java`

~~~java
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.stream.Stream;
public class Cleanup {
    public static void main(String[] args) {
        Path old = Path.of("exports", "2025");
        try (Stream<Path> walk = Files.walk(old)) {
            List<Path> all = walk.toList().reversed();
            for (Path path : all) {
                Files.delete(path);
                System.out.println("Deleted " + path);
            }
            System.out.println("Still there: " + Files.exists(old));
        } catch (IOException e) {
            System.out.println("Error: " + e);
        }
    }
}
~~~

`ArchiveIndex.java`, prima del refactoring

~~~java
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
public class ArchiveIndex {
    public static void main(String[] args) {
        Path index = Path.of("archive", "index.txt");
        String text = "2026-09-orders.csv;archived\n2025;deleted\n";
        try {
            Files.writeString(index, text);
            System.out.println("Index bytes: " + Files.size(index));
        } catch (IOException e) {
            System.out.println("Error: " + e);
        }
    }
}
~~~

`ArchiveIndex.java`

~~~java
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
public class ArchiveIndex {
    private static void safeWrite(Path file, String text)
            throws IOException {
        Path dir = file.getParent();
        Path tmp = Files.createTempFile(dir, "safe", ".tmp");
        Files.writeString(tmp, text);
        Files.move(tmp, file, StandardCopyOption.ATOMIC_MOVE,
                StandardCopyOption.REPLACE_EXISTING);
    }
    public static void main(String[] args) {
        Path index = Path.of("archive", "index.txt");
        String text = "2026-09-orders.csv;archived\n2025;deleted\n";
        try {
            safeWrite(index, text);
            System.out.println("Index bytes: " + Files.size(index));
        } catch (IOException e) {
            System.out.println("Error: " + e);
        }
    }
}
~~~

## Esercizio 24c: copiare, archiviare, scrivere in sicurezza

Obiettivo: Copiare e spostare con REPLACE_EXISTING, scrivere un file con un temporaneo e ATOMIC_MOVE, cancellare un albero in ordine inverso.

1. **Implementa `backup(file)`**: copia il file nella stessa cartella con il nome originale più `.bak` (`orders.csv` diventa `orders.csv.bak`) e restituisci il percorso della copia; l'originale resta dov'è e una copia precedente va sostituita.
2. **Implementa `archive(file, archiveDir)`**: sposta il file nella cartella `archiveDir` con lo stesso nome e restituisci il nuovo percorso; un file con lo stesso nome già presente va sostituito.
3. **Implementa `safeWrite(file, text)`**: scrivi il testo in `UTF-8` in un file temporaneo nella stessa cartella, poi spostalo sul file con la **sola** opzione `ATOMIC_MOVE`, che sostituisce il file esistente; alla fine nella cartella non deve restare nessun file temporaneo. Il file di `safeWrite` ha sempre una cartella genitore (è un percorso completo, non un semplice nome).
4. **Implementa `deleteTree(root)`**: cancella `root` con tutto il suo contenuto, visitandolo con `Files.walk` in un `try-with-resources` e cancellando in *ordine inverso*, e restituisci quanti elementi hai cancellato, cartelle comprese.

Le cartelle ricevute esistono.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.stream.Stream;

public class Exercise {

    public Path backup(Path file) throws IOException {
        // TODO: completa questo blocco.
        // Suggerimento: Costruisci il percorso della copia con Path.of(file + ".bak"): resta nella stessa cartella.
        // Files.copy può usare REPLACE_EXISTING.
        return file;
    }

    public Path archive(Path file, Path archiveDir) throws IOException {
        // TODO: completa questo blocco.
        // Suggerimento: Costruisci la destinazione con archiveDir.resolve(file.getFileName()).
        // Usa Files.move con REPLACE_EXISTING e restituisci il percorso di destinazione.
        return archiveDir;
    }

    public void safeWrite(Path file, String text) throws IOException {
        // TODO: completa questo blocco.
        // Suggerimento: Crea il temporaneo con Files.createTempFile(file.getParent(), "safe", ".tmp"): file ha sempre una cartella.
        // Scrivi il testo in UTF-8 con Files.writeString, poi usa Files.move con la sola opzione ATOMIC_MOVE:
        // con ATOMIC_MOVE le altre opzioni vengono ignorate, quindi REPLACE_EXISTING non serve.
    }

    public int deleteTree(Path root) throws IOException {
        // TODO: completa questo blocco.
        // Suggerimento: Raccogli i percorsi di Files.walk(root) in ordine inverso: i figli vanno cancellati prima dei genitori.
        // Chiudi lo stream e cancella i percorsi raccolti contando anche le cartelle.
        return 0;
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
import java.util.*;
import java.util.stream.Stream;

public class Exercise {

    public Path backup(Path file) throws IOException {
        Path copy = Path.of(file + ".bak");
        return Files.copy(file, copy, StandardCopyOption.REPLACE_EXISTING);
    }

    public Path archive(Path file, Path archiveDir) throws IOException {
        return Files.move(
            file,
            archiveDir.resolve(file.getFileName()),
            StandardCopyOption.REPLACE_EXISTING
        );
    }

    public void safeWrite(Path file, String text) throws IOException {
        Path tmp = Files.createTempFile(file.getParent(), "safe", ".tmp");
        Files.writeString(tmp, text, StandardCharsets.UTF_8);
        Files.move(tmp, file, StandardCopyOption.ATOMIC_MOVE);
    }

    public int deleteTree(Path root) throws IOException {
        try (Stream<Path> walk = Files.walk(root)) {
            List<Path> all = walk.toList().reversed();
            for (Path path : all) Files.delete(path);
            return all.size();
        }
    }
}
~~~

Dobbiamo scrivere quattro operazioni sui file: una copia di riserva, un'archiviazione, una scrittura sicura e la cancellazione di un albero.

`backup` costruisce il percorso della copia con `Path.of(file + ".bak")`: aggiungere il suffisso al percorso intero la lascia accanto all'originale. Come abbiamo visto nella lezione 24c, con `Files.copy` l'originale resta al suo posto, e `REPLACE_EXISTING` sostituisce una copia precedente invece di lanciare `FileAlreadyExistsException`. `archive` usa `Files.move` verso `archiveDir.resolve(file.getFileName())`: il file sparisce dalla cartella di partenza, e `REPLACE_EXISTING` sostituisce la versione vecchia.

`safeWrite` crea il temporaneo con `Files.createTempFile(file.getParent(), "safe", ".tmp")`, nella cartella del file. Così lo spostamento resta sullo stesso disco e può essere atomico. Poi scrive il testo con `Files.writeString` e sposta il temporaneo con la sola opzione `ATOMIC_MOVE`: quando c'è, le altre opzioni vengono ignorate, quindi aggiungere `REPLACE_EXISTING` non cambierebbe nulla. Chi legge vede sempre un file intero.

`deleteTree` raccoglie i percorsi di `Files.walk` e li rovescia con `reversed()`. `walk` elenca ogni cartella prima del suo contenuto, quindi la lista rovesciata cancella prima i file e le cartelle più profonde. La dimensione della lista è il conteggio.

Un errore tipico è cancellare nell'ordine di `walk`: arriva una `DirectoryNotEmptyException`. Il test si aspetta `6` elementi. Se lasci il temporaneo in giro, `safeWriteReplacesTheContentAndLeavesNoTemporaryFile` lo scopre. Scrivere direttamente nel file passa quel test, ma non `safeWriteReplacesTheFileByMovingATemporaryOne`, che confronta `fileKey()` prima e dopo. Un nome fisso come `orders.csv.bak` cade sul secondo file dei test di `backup` e `archive`.

## Riepilogo

- copy lascia l'originale, move lo sposta
- size e getLastModifiedTime leggono gli attributi
- Un albero si cancella: walk, ordine inverso, delete
- Scrittura sicura: temporaneo e ATOMIC_MOVE
- NoSuchFile, FileAlreadyExists, DirectoryNotEmpty
