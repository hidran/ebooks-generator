# Lezione 24b. Cartelle e percorsi

## Punti chiave

### Percorsi con Path

- resolve: aggiunge un pezzo in fondo al percorso
- relativize: la strada da una cartella a un file
- normalize: toglie i passaggi inutili come ..
- Un Path è solo un indirizzo: non crea niente sul disco

> Percorso: exports, poi 2026, poi 10, poi orders-01.csv.

### Cartelle, elenchi, filtri

- Files.createDirectories: crea tutta la catena di cartelle
- Files.list: un livello; Files.walk: tutto l'albero
- Stream aperti sulla cartella: sempre try-with-resources
- Glob orders-*.csv: l'asterisco vale qualsiasi testo

### Cosa non ci serve

- Stringhe incollate con la barra: resolve sceglie il separatore
- Un controllo con exists prima di createDirectories
- Un metodo ricorsivo per le sottocartelle: c'è walk
- Librerie esterne: basta java.nio.file

### Buone abitudini

- list, walk e DirectoryStream non garantiscono l'ordine
- Quando l'ordine conta: sorted
- Glob dentro uno stream: PathMatcher da FileSystems.getDefault()
- Percorso relativo: parte dalla cartella di lavoro

## Codice della lezione

`Main.java`, passaggio intermedio («paths»)

~~~java
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.stream.Stream;
public class Main {
    public static void main(String[] args) throws IOException {
        Path exports = Path.of("exports");
        Path year = exports.resolve("2026");
        Path october = year.resolve("10");
        Path file = october.resolve("orders-01.csv");
        System.out.println("File: " + file);
        Path messy = october.resolve("../09");
        Path september = messy.normalize();
        System.out.println(messy + " becomes " + september);
    }
}
~~~

`Main.java`, passaggio intermedio («list»)

~~~java
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.stream.Stream;
public class Main {
    public static void main(String[] args) throws IOException {
        Path exports = Path.of("exports");
        Path year = exports.resolve("2026");
        Path october = year.resolve("10");
        Path file = october.resolve("orders-01.csv");
        System.out.println("File: " + file);
        Path messy = october.resolve("../09");
        Path september = messy.normalize();
        System.out.println(messy + " becomes " + september);
        Files.createDirectories(october);
        Files.createDirectories(september);
        Files.writeString(file, "");
        Files.writeString(october.resolve("orders-15.csv"), "");
        Files.writeString(october.resolve("notes.txt"), "");
        Files.writeString(september.resolve("orders-30.csv"), "");
        try (Stream<Path> months = Files.list(year)) {
            months.map(Path::getFileName)
                    .sorted()
                    .forEach(p -> System.out.println("Month: " + p));
        }
    }
}
~~~

`Main.java`, passaggio intermedio («walk»)

~~~java
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.stream.Stream;
public class Main {
    public static void main(String[] args) throws IOException {
        Path exports = Path.of("exports");
        Path year = exports.resolve("2026");
        Path october = year.resolve("10");
        Path file = october.resolve("orders-01.csv");
        System.out.println("File: " + file);
        Path messy = october.resolve("../09");
        Path september = messy.normalize();
        System.out.println(messy + " becomes " + september);
        Files.createDirectories(october);
        Files.createDirectories(september);
        Files.writeString(file, "");
        Files.writeString(october.resolve("orders-15.csv"), "");
        Files.writeString(october.resolve("notes.txt"), "");
        Files.writeString(september.resolve("orders-30.csv"), "");
        try (Stream<Path> months = Files.list(year)) {
            months.map(Path::getFileName)
                    .sorted()
                    .forEach(p -> System.out.println("Month: " + p));
        }
        try (Stream<Path> tree = Files.walk(exports)) {
            tree.filter(Files::isRegularFile)
                    .map(exports::relativize)
                    .sorted()
                    .forEach(p -> System.out.println("Tree: " + p));
        }
    }
}
~~~

`Main.java`

~~~java
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.stream.Stream;
public class Main {
    public static void main(String[] args) throws IOException {
        Path exports = Path.of("exports");
        Path year = exports.resolve("2026");
        Path october = year.resolve("10");
        Path file = october.resolve("orders-01.csv");
        System.out.println("File: " + file);
        Path messy = october.resolve("../09");
        Path september = messy.normalize();
        System.out.println(messy + " becomes " + september);
        Files.createDirectories(october);
        Files.createDirectories(september);
        Files.writeString(file, "");
        Files.writeString(october.resolve("orders-15.csv"), "");
        Files.writeString(october.resolve("notes.txt"), "");
        Files.writeString(september.resolve("orders-30.csv"), "");
        try (Stream<Path> months = Files.list(year)) {
            months.map(Path::getFileName)
                    .sorted()
                    .forEach(p -> System.out.println("Month: " + p));
        }
        try (Stream<Path> tree = Files.walk(exports)) {
            tree.filter(Files::isRegularFile)
                    .map(exports::relativize)
                    .sorted()
                    .forEach(p -> System.out.println("Tree: " + p));
        }
        String glob = "orders-*.csv";
        try (var orders = Files.newDirectoryStream(october, glob)) {
            for (Path order : orders) {
                System.out.println("Order: " + order.getFileName());
            }
        }
    }
}
~~~

## Esercizio 24b: cartelle per anno e per mese

Obiettivo: Costruire percorsi con resolve, creare cartelle con createDirectories, elencare un albero con Files.walk e filtrare con un glob.

1. **Implementa `monthFolder(base, year, month)`**: restituisci `base/anno/mese`, con il mese *sempre a due cifre* (`3` diventa `03`), costruito con `resolve`, e crea le cartelle che mancano; una seconda chiamata con gli stessi valori non deve fallire.
2. **Implementa `orderFiles(month)`**: i nomi dei file della cartella che corrispondono al glob `orders-*.csv`, *solo a quel livello*, in ordine alfabetico.
3. **Implementa `tree(base)`**: i percorsi di tutti i file regolari sotto `base`, a qualsiasi profondità, relativi a `base` e in ordine alfabetico; le cartelle non compaiono.

**Chiudi sempre gli stream** sulle cartelle con `try-with-resources`.

Le cartelle ricevute esistono, tranne quelle che `monthFolder` deve creare.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
import java.io.IOException;
import java.nio.file.*;
import java.util.*;
import java.util.stream.Stream;

public class Exercise {

    public Path monthFolder(Path base, int year, int month) throws IOException {
        // TODO: completa questo blocco.
        // Suggerimento: Costruisci il percorso con base.resolve(...).resolve(...).
        // Formatta il mese con String.format("%02d", month); Files.createDirectories crea i livelli mancanti.
        return base;
    }

    public List<String> orderFiles(Path month) throws IOException {
        // TODO: completa questo blocco.
        // Suggerimento: Files.newDirectoryStream(month, "orders-*.csv") seleziona solo quel livello.
        // Chiudi la risorsa con try-with-resources, raccogli getFileName().toString() e ordina i nomi.
        return List.of();
    }

    public List<String> tree(Path base) throws IOException {
        // TODO: completa questo blocco.
        // Suggerimento: Files.walk(base) visita anche le sottocartelle e va chiuso con try-with-resources.
        // Tieni solo Files.isRegularFile, rendi i percorsi relativi con base.relativize e ordina.
        return List.of();
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
import java.io.IOException;
import java.nio.file.*;
import java.util.*;
import java.util.stream.Stream;

public class Exercise {

    public Path monthFolder(Path base, int year, int month) throws IOException {
        Path folder = base.resolve(String.valueOf(year)).resolve(String.format("%02d", month));
        return Files.createDirectories(folder);
    }

    public List<String> orderFiles(Path month) throws IOException {
        List<String> names = new ArrayList<>();
        try (DirectoryStream<Path> files = Files.newDirectoryStream(month, "orders-*.csv")) {
            for (Path file : files) {
                if (Files.isRegularFile(file)) names.add(file.getFileName().toString());
            }
        }
        Collections.sort(names);
        return names;
    }

    public List<String> tree(Path base) throws IOException {
        try (Stream<Path> paths = Files.walk(base)) {
            return paths
                .filter(Files::isRegularFile)
                .map(base::relativize)
                .sorted()
                .map(Path::toString)
                .toList();
        }
    }
}
~~~

Dobbiamo organizzare i file in cartelle per anno e per mese, poi elencarli in due modi diversi.

In `monthFolder` costruiamo il percorso con due `resolve`: il primo aggiunge l'anno con `String.valueOf(year)`, il secondo il mese con `String.format("%02d", month)`, che trasforma 3 in `"03"`. Come abbiamo visto nella lezione 24b, `resolve` aggiunge un pezzo alla volta e sceglie da solo il separatore. Poi `Files.createDirectories` crea tutta la catena che manca e non fallisce se esiste già, quindi non serve un controllo con `exists`. Restituisce il percorso stesso, e lo usiamo direttamente nel `return`.

In `orderFiles` apriamo un `DirectoryStream` con il glob `orders-*.csv` dentro un try-with-resources, che chiude la cartella anche in caso di errore. Guarda un solo livello: le sottocartelle restano fuori. Per ogni voce teniamo i file regolari e salviamo `getFileName().toString()`, cioè il nome senza la cartella. L'ordine non è garantito, quindi chiudiamo con `Collections.sort`.

In `tree` usiamo `Files.walk`, che visita tutto l'albero, sempre in un try-with-resources. `filter(Files::isRegularFile)` scarta le cartelle, `map(base::relativize)` toglie il prefisso di `base` e `sorted()` mette tutto in ordine.

Un errore tipico è dimenticare l'ordinamento: su un sistema il test passa per caso, su un altro no. I test si aspettano `orders-01.csv` prima di `orders-15.csv`, anche se i file sono stati creati al contrario. Un altro errore è usare `walk` anche in `orderFiles`: comparirebbe `orders-99.csv` della cartella `archive`, che il test esclude.

## Riepilogo

- resolve, relativize e normalize costruiscono i percorsi
- createDirectories crea le cartelle, anche se esistono già
- list per un livello, walk per l'albero, in try-with-resources
- newDirectoryStream con un glob: solo i file che servono
