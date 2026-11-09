# Lezione 24e. Sorvegliare una cartella

## Punti chiave

### WatchService in quattro mosse

- register: la cartella e gli eventi che ci interessano
- take: aspetta la prossima WatchKey
- pollEvents: gli eventi arrivati, con il nome del file
- reset: la chiave torna in ascolto

> Percorso: register, poi take, poi pollEvents, poi reset.

### Gli eventi

- ENTRY_CREATE: un file nuovo nella cartella
- ENTRY_MODIFY: un file cambiato, anche più volte di seguito
- ENTRY_DELETE: un file sparito o spostato altrove
- OVERFLOW: eventi persi, si rilegge la cartella
- Solo le novità: i file già presenti non generano eventi

### Attenzione a

- Cartelle di rete: gli eventi possono non arrivare
- Editor che salvano con file temporanei: filtrare per estensione
- File scritti a metà: nome temporaneo, poi move
- File già presenti all'avvio: elaborarli prima del ciclo

### KISS: cosa non ci serve

- Spesso basta un controllo periodico: Files.list ogni minuto
- Vede anche i file già presenti e regge un riavvio
- I job schedulati arrivano nella lezione 91
- WatchService solo se serve una reazione immediata

## Codice della lezione

`Main.java`

~~~java
import java.io.IOException;
import java.nio.file.FileSystems;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardWatchEventKinds;
import java.nio.file.WatchKey;
import java.util.List;
public class Main {
    record Product(String name, int priceInCents) {
    }
    static final Path PROCESSED = Path.of("processed");
    static final Path REJECTED = Path.of("rejected");
    static Product toProduct(String line) {
        String[] parts = line.split(",");
        if (parts.length != 2) {
            throw new IllegalArgumentException("bad line: " + line);
        }
        return new Product(parts[0], Integer.parseInt(parts[1]));
    }
    static void importFile(Path file) throws IOException {
        Path name = file.getFileName();
        try {
            List<Product> products = Files.readAllLines(file).stream()
                    .map(Main::toProduct)
                    .toList();
            products.forEach(System.out::println);
            Files.move(file, PROCESSED.resolve(name));
            System.out.println(name + " -> processed");
        } catch (IllegalArgumentException e) {
            String reason = e.getMessage();
            Files.move(file, REJECTED.resolve(name));
            Path note = REJECTED.resolve(name + ".reason.txt");
            Files.writeString(note, reason + "\n");
            System.out.println(name + " -> rejected: " + reason);
        }
    }
    public static void main(String[] args)
            throws IOException, InterruptedException {
        Path inbox = Path.of("inbox");
        try (var watcher = FileSystems.getDefault().newWatchService()) {
            inbox.register(watcher,
                    StandardWatchEventKinds.ENTRY_CREATE);
            System.out.println("Watching " + inbox);
            boolean running = true;
            while (running) {
                WatchKey key = watcher.take();
                for (var event : key.pollEvents()) {
                    Path name = (Path) event.context();
                    if (name.toString().equals("stop")) {
                        Files.delete(inbox.resolve(name));
                        running = false;
                    } else {
                        importFile(inbox.resolve(name));
                    }
                }
                if (!key.reset()) {
                    running = false;
                }
            }
        }
        System.out.println("Stopped");
    }
}
~~~

`Main.java`, versione di partenza

~~~java
import java.io.IOException;
import java.nio.file.FileSystems;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardWatchEventKinds;
import java.nio.file.WatchKey;
import java.util.List;
public class Main {
    record Product(String name, int priceInCents) {
    }
    static final Path PROCESSED = Path.of("processed");
    static final Path REJECTED = Path.of("rejected");
    static Product toProduct(String line) {
        String[] parts = line.split(",");
        if (parts.length != 2) {
            throw new IllegalArgumentException("bad line: " + line);
        }
        return new Product(parts[0], Integer.parseInt(parts[1]));
    }
    static void importFile(Path file) throws IOException {
        Path name = file.getFileName();
        try {
            List<Product> products = Files.readAllLines(file).stream()
                    .map(Main::toProduct)
                    .toList();
            products.forEach(System.out::println);
            Files.move(file, PROCESSED.resolve(name));
            System.out.println(name + " -> processed");
        } catch (IllegalArgumentException e) {
            String reason = e.getMessage();
            Files.move(file, REJECTED.resolve(name));
            Path note = REJECTED.resolve(name + ".reason.txt");
            Files.writeString(note, reason + "\n");
            System.out.println(name + " -> rejected: " + reason);
        }
    }
}
~~~

`samples/kitchen.csv`

~~~csv
Mug,1200
Teapot,3500
~~~

`samples/lamps.csv`

~~~csv
Desk lamp,2900
Floor lamp
~~~

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
cat samples/kitchen.csv
mv samples/kitchen.csv inbox/
cat samples/lamps.csv
mv samples/lamps.csv inbox/
touch inbox/stop
ls inbox processed rejected
cat rejected/lamps.csv.reason.txt
~~~

## Esercizio 24e: una cartella inbox per i prodotti

Obiettivo: Leggere un CSV, spostare il file in processed o in rejected e sorvegliare una cartella con WatchService fino a un file di stop.

1. **Implementa `toProduct(line)`**: una riga `nome,prezzo in centesimi` diventa un `Product`; se la riga non ha esattamente due campi lancia `IllegalArgumentException` con il messaggio `bad line:` seguito dalla riga; un prezzo non numerico lancia `NumberFormatException`.
2. **Implementa `importFile(file, processed, rejected)`**: converti tutte le righe; se sono tutte valide sposta il file in `processed` con lo stesso nome e restituisci i prodotti; se una riga è sbagliata sposta il file in `rejected`, scrivi il messaggio dell'errore in un file con lo stesso nome più `.reason.txt` accanto a lui e restituisci una lista vuota.
3. **Implementa `watch(inbox, processed, rejected)`**: registra `inbox` per `ENTRY_CREATE`, importa ogni file nuovo; quando arriva un file chiamato `stop` cancellalo ed esci dal ciclo; ricorda `key.reset` dopo ogni gruppo di eventi e chiudi il `WatchService` con `try-with-resources`. Restituisci il numero totale di prodotti importati.

Le cartelle ricevute esistono.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
import java.io.IOException;
import java.nio.file.*;
import java.util.*;

public class Exercise {

    public record Product(String name, int priceInCents) {}

    public Product toProduct(String line) {
        // TODO: completa questo blocco.
        // Suggerimento: Separa con split(","), controlla che ci siano due campi e usa Integer.parseInt sul prezzo.
        // Non catturare qui NumberFormatException: sarà gestita da importFile.
        return new Product("", 0);
    }

    public List<Product> importFile(Path file, Path processed, Path rejected) throws IOException {
        // TODO: completa questo blocco.
        // Suggerimento: Converti tutte le righe dentro try prima di spostare il file in processed.
        // NumberFormatException deriva da IllegalArgumentException: un catch di questa gestisce entrambe.
        // Nel catch sposta in rejected, scrivi getMessage() nel file .reason.txt e restituisci List.of().
        return List.of();
    }

    public int watch(Path inbox, Path processed, Path rejected)
        throws IOException, InterruptedException {
        // TODO: completa questo blocco.
        // Suggerimento: Crea un WatchService con try-with-resources e registra inbox per ENTRY_CREATE.
        // take() attende un gruppo di eventi: ignora OVERFLOW e leggi il Path relativo da event.context().
        // Se il nome è stop, cancellalo e termina; altrimenti riusa importFile e accumula i prodotti.
        // Chiama key.reset() dopo ogni gruppo; se restituisce false termina il ciclo.
        return 0;
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

public class Exercise {

    public record Product(String name, int priceInCents) {}

    public Product toProduct(String line) {
        String[] parts = line.split(",");
        if (parts.length != 2) {
            throw new IllegalArgumentException("bad line: " + line);
        }
        return new Product(parts[0], Integer.parseInt(parts[1]));
    }

    public List<Product> importFile(Path file, Path processed, Path rejected) throws IOException {
        Path name = file.getFileName();
        try {
            List<Product> products = Files.readAllLines(file)
                .stream()
                .map(this::toProduct)
                .toList();
            Files.move(file, processed.resolve(name));
            return products;
        } catch (IllegalArgumentException e) {
            Files.move(file, rejected.resolve(name));
            Files.writeString(rejected.resolve(name + ".reason.txt"), e.getMessage() + "\n");
            return List.of();
        }
    }

    public int watch(Path inbox, Path processed, Path rejected)
        throws IOException, InterruptedException {
        int imported = 0;
        try (WatchService watcher = FileSystems.getDefault().newWatchService()) {
            inbox.register(watcher, StandardWatchEventKinds.ENTRY_CREATE);
            boolean running = true;
            while (running) {
                WatchKey key = watcher.take();
                for (WatchEvent<?> event : key.pollEvents()) {
                    if (event.kind() == StandardWatchEventKinds.OVERFLOW) {
                        continue;
                    }
                    Path name = (Path) event.context();
                    if (name.toString().equals("stop")) {
                        Files.delete(inbox.resolve(name));
                        running = false;
                    } else {
                        imported += importFile(inbox.resolve(name), processed, rejected).size();
                    }
                }
                if (!key.reset()) {
                    running = false;
                }
            }
        }
        return imported;
    }
}
~~~

Vogliamo una cartella inbox che importa i CSV di prodotti appena arrivano e smista ogni file in processed o in rejected.

`toProduct` divide la riga con `split(",")`. Se i pezzi non sono esattamente due lancia `IllegalArgumentException` con `"bad line: " + line`. Il prezzo lo converte `Integer.parseInt`, che per un testo come `twelve` lancia già da solo `NumberFormatException`.

`importFile` converte tutte le righe prima di spostare il file. Il `catch` su `IllegalArgumentException` prende anche `NumberFormatException`, che ne è una sottoclasse. Se qualcosa va storto nessun prodotto viene importato: il file finisce in `rejected` e il messaggio dell'eccezione va nel file `.reason.txt` accanto. Altrimenti il file va in `processed` con lo stesso nome.

`watch` segue le quattro mosse della lezione 24e: `register` per `ENTRY_CREATE`, `take` che aspetta senza consumare CPU, `pollEvents` e infine `reset`. Il `WatchService` sta in un try-with-resources, quindi si chiude anche se qualcosa fallisce. Saltiamo gli eventi `OVERFLOW`, cancelliamo il file `stop` e usciamo dal ciclo. Se `reset` restituisce `false` la cartella non è più valida e ci fermiamo comunque.

Un errore tipico è dimenticare `key.reset()`: la chiave non torna in ascolto, il secondo file `lamps.csv` non viene mai visto e il test fallisce con "nessun evento per lamps.csv entro 20 secondi". Un altro è spostare il file prima di aver controllato tutte le righe: `importFileRejectsWholeFileWithReason` vuole `processed` vuota e `bad line: Floor lamp` nel file del motivo.

Il test conta 2 prodotti: i due di `kitchen.csv`, zero da `lamps.csv`, che è stato rifiutato.

## Riepilogo

- newWatchService dentro un try-with-resources
- register con ENTRY_CREATE, poi take, pollEvents, reset
- Uno stop pulito: il file stop chiude il ciclo
- Ogni file va in processed, o in rejected con il motivo
- Prima chiediamoci se basta un controllo periodico
