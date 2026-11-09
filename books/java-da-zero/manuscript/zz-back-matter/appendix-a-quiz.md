# Appendice A. Quiz di sezione

I quiz che chiudono ogni sezione del corso, con la risposta corretta e la spiegazione. Usali per capire cosa vale la pena rivedere, non per prendere un voto.

## Quiz: primi passi con Java

Verifica di aver capito compilazione, variabili, operatori, condizioni, cicli, metodi, array e stringhe.

**Domanda 1.** Che cosa produce il compilatore javac quando legge un file sorgente HelloWorld.java senza errori?

- a. Una copia corretta del file HelloWorld.java
- b. Niente: javac esegue subito il programma e stampa il risultato
- c. Un file HelloWorld.class che contiene bytecode
- d. Un programma nativo per macOS da avviare con un doppio clic

Risposta: c. Corretto: javac traduce il sorgente in bytecode e lo salva in un file .class, che poi esegue la JVM.

**Domanda 2.** Nel debugger di Visual Studio Code visto nella lezione, l'esecuzione è ferma su un punto di interruzione. Quale tasto esegue una sola riga e si ferma su quella successiva?

- a. F9
- b. F10
- c. Control F5
- d. F5

Risposta: b. Corretto: F10 avanza di una riga alla volta, e nella vista Variables si vedono i valori cambiare.

**Domanda 3.** Che cosa fa il comando java Greeting.java, scritto con l'estensione .java?

- a. Compila il file in memoria e lo esegue subito, in un solo passo
- b. Apre JShell e carica il file una riga alla volta
- c. Crea il file Greeting.class senza eseguirlo
- d. Dà sempre errore, perché java accetta solo il nome della classe

Risposta: a. Corretto: per un file singolo il comando java con il nome del sorgente compila ed esegue in un colpo solo, comodo per i piccoli esperimenti.

**Domanda 4.** Che cosa succede con questo codice?
```
var gravity = 10;
gravity = 9.81;
```

- a. Non compila: var richiede sempre un numero con la virgola
- b. Compila, e gravity diventa un double che vale 9.81
- c. Compila, e gravity vale 9 perché i decimali vengono tagliati
- d. Non compila: gravity è un int e 9.81 è un double

Risposta: d. Corretto: 10 è un intero, quindi var deduce int. Passare da double a int perderebbe la parte decimale e il compilatore lo blocca.

**Domanda 5.** Che cosa stampa questo codice?
```
double result = 7 / 2;
System.out.println(result);
```

- a. 3
- b. 4.0
- c. 3.0
- d. 3.5

Risposta: c. Corretto: 7 / 2 tra interi dà 3, senza decimali; solo dopo il 3 viene salvato nel double e stampato come 3.0.

**Domanda 6.** Che cosa stampa questo codice?
```
int first = 8;
int second = 4;
int average = first + second / 2;
System.out.println(average);
```

- a. 10
- b. 6
- c. Non compila, perché mancano le parentesi
- d. 12

Risposta: a. Corretto: la divisione ha la precedenza sulla somma, quindi prima 4 / 2 = 2, poi 8 + 2 = 10.

**Domanda 7.** In uno switch usato come espressione su un int (String name = switch (day) { case 1 -&gt; "Monday"; ... }) togliamo il caso default. Che cosa succede?

- a. Il codice compila e, per un giorno non previsto, name vale null
- b. La compilazione si ferma: lo switch non copre tutti i valori possibili
- c. Serve aggiungere break a ogni caso, altrimenti scivola nel successivo
- d. Il codice compila, ma il programma si ferma con un errore quando day vale 9

Risposta: b. Corretto: day è un int e potrebbe valere 9 o -5. Con default il compilatore sa che ogni valore produce un risultato.

**Domanda 8.** Quante righe stampa questo codice?
```
int tickets = 0;
do {
    System.out.println("tickets left: " + tickets);
    tickets--;
} while (tickets > 0);
```

- a. Una sola riga
- b. Nessuna, perché la condizione è falsa fin dall'inizio
- c. Infinite righe, perché tickets diventa negativo

Risposta: a. Corretto: il corpo del do while gira almeno una volta e stampa "tickets left: 0"; poi la condizione è falsa e il ciclo finisce.

**Domanda 9.** Nel programma degli esiti d'esame la soglia 60 era copiata in tre blocchi if quasi identici. Dopo il refactoring con i metodi printResult e outcome, qual è il vantaggio principale?

- a. Non serve più l'if, perché outcome sceglie l'esito da solo
- b. Il programma gira molto più velocemente
- c. Il programma stampa risultati diversi e più precisi
- d. La soglia è scritta in un solo punto: se cambia, si modifica lì e vale per tutti

Risposta: d. Corretto: è il principio DRY, Don't Repeat Yourself. Con il codice copiato ogni modifica andava fatta in tre punti.

**Domanda 10.** Che cosa stampa questo codice?
```
String language = "Java";
language.toUpperCase();
System.out.println(language);
```

- a. Niente, perché il risultato di toUpperCase va sempre assegnato o il codice non compila
- b. JAVA
- c. Java

Risposta: c. Corretto: le stringhe sono immutabili. Per avere il maiuscolo bisogna salvare il risultato, per esempio in String upper = language.toUpperCase().

**Domanda 11.** Un utente scrive 3 e preme Invio. Che cosa contiene name dopo queste righe?
```
Scanner scanner = new Scanner(System.in);
int quantity = scanner.nextInt();
String name = scanner.nextLine();
```

- a. Niente: il programma aspetta che l'utente scriva anche il nome
- b. La stringa "3"
- c. Una stringa vuota
- d. Il programma si ferma con una NumberFormatException

Risposta: c. Corretto: nextInt legge il 3 ma lascia l'Invio nel buffer. nextLine lo trova e restituisce una riga vuota. Si risolve con un nextLine in più, che consuma il resto della riga.

**Domanda 12.** L'utente deve scrivere una quantità. Perché Scanner con hasNextInt è più sicuro di Integer.parseInt(IO.readln("Quantity: "))?

- a. Perché parseInt non riesce a leggere i numeri più grandi di cento
- b. Perché IO.readln restituisce già un int e parseInt è inutile
- c. Perché hasNextInt è più veloce di parseInt
- d. Perché controlla il dato prima di leggerlo: con delle lettere il programma può stampare un messaggio invece di fermarsi

Risposta: d. Corretto: hasNextInt risponde false se non c'è un intero e il programma mostra Not a number. parseInt con abc lancia una NumberFormatException e ferma il programma.

**Domanda 13.** Nella cassa, menuChoice trasforma il testo dell'utente in un numero con uno switch sulle stringhe e un default che restituisce -1. Perché non usare direttamente Integer.parseInt?

- a. Perché lo switch è l'unico modo per leggere il numero zero
- b. Perché con il default ogni altro testo, lettere comprese, diventa -1 e la cassa risponde Unknown choice senza fermarsi
- c. Perché lo switch restituisce un valore e parseInt no
- d. Perché parseInt non funziona con i numeri negativi

Risposta: b. Corretto: il default raccoglie tutto il resto. parseInt con delle lettere lancerebbe un'eccezione e fermerebbe il programma.

**Domanda 14.** Nella classe Book il main chiama direttamente printHeader(), scritto così:
```
static void printHeader() {
    System.out.println("Book catalog");
}
```
Che cosa significa static?

- a. Il metodo non può più essere modificato dopo la compilazione
- b. Il metodo appartiene alla classe e si chiama direttamente, senza creare un oggetto con new
- c. Il metodo non restituisce niente e fa solo un'azione

Risposta: b. Corretto: per questo il main, che parte quando non esiste ancora nessun oggetto, è static, e può chiamare printHeader() solo con il nome.

**Domanda 15.** Che cosa fanno String e return in questo metodo?
```
public String describe() {
    return "Dune" + "|" + 412;
}
```

- a. String è il tipo del valore promesso e return lo consegna a chi ha chiamato il metodo
- b. String stampa il testo sullo schermo e return chiude il programma
- c. String vuol dire che il metodo non restituisce niente, e return serve solo a stamparlo
- d. Se al posto di String scriviamo void il codice compila lo stesso e restituisce il testo

Risposta: a. Corretto: describe promette un testo e return mantiene la promessa. Chi chiama, come println(new Book().describe()), usa il valore ricevuto.

**Domanda 16.** Che cosa stampa questo codice?
```
System.out.println("Pen" + "-" + 3 + "-" + false);
```

- a. Pen - 3 - false, con gli spazi attorno ai trattini
- b. Non compila, perché un testo non si può unire a un int e a un boolean
- c. Pen-3-false

Risposta: c. Corretto: il più unisce da sinistra a destra, un segno alla volta. Il 3 e il false diventano testo e non compaiono altri caratteri.

## Quiz: programmazione a oggetti

Verifica classi e oggetti, membri statici, overloading, record, ereditarietà e composizione, Object, classi astratte, pattern matching, eccezioni e package.

**Domanda 1.** Product ha il campo pubblico int priceInCents. Che cosa stampa questo codice?
```
Product coffee = new Product();
coffee.priceInCents = 250;
Product sameCoffee = coffee;
sameCoffee.priceInCents = 300;
System.out.println(coffee.priceInCents);
```

- a. 0, perché sameCoffee non è stato creato con new
- b. 250, perché sameCoffee è una copia del caffè
- c. Non compila: un oggetto non si può assegnare a un'altra variabile
- d. 300

Risposta: d. Corretto: le due variabili contengono lo stesso riferimento, quindi indicano un solo oggetto. Il prezzo cambiato tramite sameCoffee è quello del caffè.

**Domanda 2.** In Product, getCreatedCount() è static e getName() è un metodo di istanza. Perché Product.getCreatedCount() compila, mentre Product.getName() no?

- a. Perché il nome sta in ogni oggetto: senza un oggetto non c'è un nome
- b. Perché getName() è privato e non si vede da Main
- c. Perché prima di chiamare getName() bisogna chiamare getCreatedCount()
- d. Perché i metodi static si chiamano solo dentro la loro classe

Risposta: a. Corretto: un membro static appartiene alla classe e non ha this. Per chiamare un metodo di istanza serve un oggetto preciso.

**Domanda 3.** La classe Order ha già il metodo public void add(Product product). Che cosa succede se aggiungiamo anche questo metodo?
```
public int add(Product product) {
    return totalInCents;
}
```

- a. Compila: il compilatore sceglie la versione in base al tipo restituito
- b. Compila, ma la nuova versione sostituisce quella vecchia (overriding)
- c. Non compila: esiste già un add con gli stessi parametri

Risposta: c. Corretto: la firma è il nome più la lista dei parametri. Con order.add(product) il compilatore non saprebbe quale versione chiamare.

**Domanda 4.** Che cosa stampa questo codice?
```
record Product(String name, int priceInCents) { }

var pen = new Product("Pen", 150);
var samePen = new Product("Pen", 150);
System.out.println(pen.equals(samePen) + " " + (pen == samePen));
```

- a. false true
- b. true false
- c. true true
- d. false false

Risposta: b. Corretto: equals generato dal record confronta tutti i componenti, mentre == dice se le due variabili indicano lo stesso oggetto.

**Domanda 5.** Per riusare il nome e il prezzo, scriviamo class Order extends Product. Il codice compila. Che cosa ne dice la lezione?

- a. È una buona scelta: riusa i due campi senza copiarli, proprio come chiede il principio DRY visto con i metodi
- b. Non è possibile: Java non permette di estendere una classe con un costruttore
- c. È sbagliato: un ordine non è un prodotto, meglio comporre (un ordine ha un cliente e un prodotto)
- d. È sbagliato solo perché manca l'annotazione @Override

Risposta: c. Corretto: la prova del "è un" fallisce. Con la composizione Order tiene Customer e Product nei suoi campi e delega a loro il lavoro.

**Domanda 6.** In Product ridefiniamo equals (stesso nome e stesso prezzo) ma non hashCode. Qual è il problema?

- a. Il codice non compila: il compilatore pretende che equals e hashCode siano sempre dichiarati insieme, nella stessa classe
- b. Da quel momento == confronta il contenuto invece dei riferimenti
- c. equals smette di funzionare e restituisce sempre false
- d. Oggetti uguali per equals possono avere hashCode diversi, e HashSet o HashMap non li trovano

Risposta: d. Corretto: il contratto chiede lo stesso hashCode per oggetti uguali. HashSet e HashMap cercano prima per hashCode, poi chiamano equals.

**Domanda 7.** Quale affermazione su una classe astratta come Payment è corretta?

- a. Può avere campi e costruttori, ma new Payment(...) non compila
- b. Una classe può estendere più classi astratte insieme
- c. Non può avere costruttori, perché non si può istanziare
- d. Tutti i suoi metodi devono essere astratti, senza corpo, perché sarà la classe figlia a scriverli

Risposta: a. Corretto: una classe astratta è un progetto a metà. Le figlie concrete la completano implementando i metodi astratti, come fee().

**Domanda 8.** PaymentMethod è sealed e permette solo CardPayment(String lastFour) e CashPayment(int givenInCents). Perché questo switch non compila?
```
return switch (method) {
    case CardPayment(String lastFour) -> "Card " + lastFour;
    case CashPayment(int cents) -> "Cash: " + cents;
    case CashPayment(int cents) when cents >= 5000 -> "Check " + cents;
};
```

- a. Perché la variabile deve chiamarsi givenInCents, come il componente
- b. Il caso con when sta dopo il caso generale dello stesso tipo: non sarebbe mai raggiunto
- c. Perché manca il caso default

Risposta: b. Corretto: i casi più specifici vanno per primi. Spostando la riga con when prima del caso generale lo switch compila.

**Domanda 9.** Il portafoglio contiene 700 centesimi e withdraw lancia InsufficientFundsException se l'importo supera il saldo. Che cosa stampa questo codice?
```
try {
    wallet.withdraw(900);
    System.out.println("A");
} catch (InsufficientFundsException e) {
    System.out.println("B");
} finally { System.out.println("C"); }
```

- a. Solo B, perché dopo un catch il finally non viene eseguito
- b. Niente: il programma si ferma con una stack trace
- c. A, poi C
- d. B, poi C

Risposta: d. Corretto: l'eccezione salta il resto del try, il catch adatto stampa B e il finally, che gira sempre, stampa C.

**Domanda 10.** Nella classe com.shop.catalog.Product il campo è dichiarato final int priceInCents; senza modificatori di visibilità. Chi può leggerlo direttamente?

- a. Solo le classi del package com.shop.catalog
- b. Tutte le classi, perché è final e quindi non si può modificare
- c. Le classi del package e le sottoclassi in altri package
- d. Solo la classe Product

Risposta: a. Corretto: senza parola chiave il campo è package-private. Da com.shop.app il compilatore segnala che non è accessibile da fuori del package.

## Quiz: Java per applicazioni reali

Verifica collezioni, generics, lambda, stream, Optional, file, concorrenza, thread virtuali, test e Maven.

**Domanda 1.** Che cosa stampa questo codice?
```
Map<String, Integer> quantities = new LinkedHashMap<>();
quantities.put("Coffee", 2);
quantities.put("Coffee", 3);
System.out.println(quantities.get("Coffee") + " "
        + quantities.get("Pen") + " "
        + quantities.getOrDefault("Pen", 0));
```

- a. 5 0 0
- b. 3 null 0
- c. 3 0 0
- d. 2 null 0

Risposta: b. Corretto: le chiavi sono uniche, quindi il secondo put sostituisce il valore. get su una chiave assente restituisce null, getOrDefault il valore di riserva.

**Domanda 2.** Con una lista senza tipo, names.add(42) compila e l'errore esplode dopo, con una ClassCastException. Che cosa cambia se dichiariamo List&lt;String&gt; names = new ArrayList&lt;&gt;()?

- a. La lista accetta sia stringhe sia numeri, ma li converte da sola in String
- b. Il compilatore accetta add(42) ma lancia un'eccezione più chiara durante l'esecuzione
- c. names.add(42) non compila, e get non richiede più il cast
- d. Il programma diventa più veloce, perché non servono più i controlli

Risposta: c. Corretto: i generics spostano l'errore di tipo dall'esecuzione alla compilazione.

**Domanda 3.** products.removeIf(p -&gt; p.priceInCents() == 0) riceve una lambda che risponde vero o falso per ogni prodotto. Quale interfaccia funzionale di java.util.function rappresenta questo comportamento?

- a. Predicate&lt;Product&gt;
- b. Function&lt;Product, String&gt;
- c. Consumer&lt;Product&gt;
- d. Supplier&lt;Product&gt;

Risposta: a. Corretto: Predicate ha il metodo test e restituisce un boolean. removeIf toglie gli elementi per cui il predicato è vero.

**Domanda 4.** Che cosa stampa questo codice?
```
List<Integer> prices = List.of(150, 400, 650, 250, 300, 1500, 800);
List<Integer> cheapest = prices.stream()
        .filter(p -> p < 500)
        .sorted()
        .limit(3)
        .toList();
System.out.println(cheapest);
```

- a. [150, 400, 250]
- b. Niente, perché le operazioni intermedie sono pigre
- c. [150, 250, 300, 400]
- d. [150, 250, 300]

Risposta: d. Corretto: filter tiene 150, 400, 250 e 300; sorted li ordina; limit(3) tiene i primi tre. Il 400 resta fuori, come Notebook nella lezione.

**Domanda 5.** Secondo la lezione, dove ha senso usare Optional?

- a. Come parametro di un metodo, per rendere facoltativo un argomento
- b. Come tipo di ritorno di un metodo che può non trovare un risultato, come findByName
- c. Come campo di una classe, per ogni valore che al momento della creazione dell'oggetto non è ancora noto
- d. Attorno a una lista, per dire che potrebbe non avere elementi

Risposta: b. Corretto: la firma dichiara che il valore può mancare e costringe chi chiama a gestire l'assenza.

**Domanda 6.** Un importo in euro vale 2,00 con scala 1 in un BigDecimal e 2,00 con scala 2 in un altro. Come si confrontano correttamente?

- a. a.equals(b)
- b. a == b
- c. a.add(b).equals(BigDecimal.ZERO)
- d. a.compareTo(b) == 0

Risposta: d. Corretto: compareTo confronta il valore numerico e restituisce 0 quando i due importi valgono uguale, qualunque sia la scala.

**Domanda 7.** Per creare un BigDecimal che vale esattamente 0,1, quale riga è corretta?

- a. new BigDecimal("0.1")
- b. new BigDecimal(0.1)
- c. new BigDecimal(0.1 + 0.0)
- d. BigDecimal.valueOf(0.1f)

Risposta: a. Corretto: la String viene letta così com'è, quindi il valore è esattamente 0,1.

**Domanda 8.** Il metodo main chiama Files.writeString(file, text). Togliamo throws IOException dalla firma di main senza aggiungere try e catch. Che cosa succede?

- a. Compila, e se la scrittura fallisce l'errore viene ignorato
- b. Non compila, perché Files.writeString funziona solo dentro un try-with-resources
- c. Non compila: IOException è checked e va catturata o dichiarata con throws
- d. Compila, ma il programma si ferma sempre alla prima scrittura

Risposta: c. Corretto: il compilatore pretende una scelta. Nella lezione l'abbiamo gestita con un blocco try e il suo catch.

**Domanda 9.** Che cosa stampa questo codice su macOS o Linux?
```
Path base = Path.of("exports", "2026");
Path p = base.resolve("10/../09/orders.csv").normalize();
System.out.println(p);
```

- a. exports/2026/10/../09/orders.csv
- b. exports/2026/09/orders.csv
- c. 09/orders.csv
- d. exports/2026/10/09/orders.csv

Risposta: b. Corretto: resolve aggiunge il percorso relativo a base e normalize elimina 10/.., che entra in 10 e ne esce subito.

**Domanda 10.** Per scrivere un file in modo sicuro, perché scriviamo prima un file temporaneo nella stessa cartella e poi lo spostiamo con ATOMIC_MOVE?

- a. Perché Files.writeString non può sovrascrivere un file esistente.
- b. Perché un file temporaneo occupa meno spazio su disco.
- c. Perché chi legge trova sempre il file vecchio o quello nuovo completo, mai uno scritto a metà.
- d. Perché ATOMIC_MOVE comprime il file mentre lo sposta.

Risposta: c. Corretto: lo spostamento atomico nella stessa cartella avviene in un solo passo, tutto o niente.

**Domanda 11.** Che cosa stampa questo codice?
```
String s = "Caffè";
int bytes = s.getBytes(StandardCharsets.UTF_8).length;
System.out.println(s.length() + " " + bytes);
```

- a. 5 5
- b. 6 6
- c. 5 6
- d. 5 10

Risposta: c. Corretto: cinque caratteri, ma in UTF-8 la è occupa due byte: un file contiene byte, la codifica li trasforma in testo.

**Domanda 12.** In un ciclo con WatchService, dopo aver letto gli eventi di una WatchKey con pollEvents, che cosa dobbiamo chiamare per continuare a ricevere eventi da quella cartella?

- a. key.reset()
- b. register di nuovo sulla stessa cartella
- c. watcher.close()
- d. Niente: la chiave torna in ascolto da sola

Risposta: a. Corretto: reset rimette la chiave in ascolto; se restituisce false la cartella non è più sorvegliabile e usciamo dal ciclo.

**Domanda 13.** Leggiamo con Files.newBufferedReader un file scritto da un fornitore in Windows-1252, passando StandardCharsets.UTF_8. Che cosa succede?

- a. Java riconosce da solo il charset e il testo è sempre corretto
- b. Se nel file ci sono byte non validi in UTF-8, arriva una MalformedInputException
- c. Il file viene letto bene, perché UTF-8 comprende anche Windows-1252
- d. Java passa in silenzio a Latin-1 e mostra gli accenti corretti

Risposta: b. Corretto: newBufferedReader è severo e lancia l'eccezione, che si vede subito. Meglio di un nome rovinato che arriva sul sito in silenzio.

**Domanda 14.** Nell'import del CSV, perché si scrive line.split(";", -1) invece di line.split(";")?

- a. Perché -1 rende split più veloce sui file grandi
- b. Perché -1 toglie gli spazi all'inizio e alla fine di ogni campo
- c. Perché senza -1 split butta via i campi vuoti alla fine della riga
- d. Perché -1 toglie il BOM dalla prima riga

Risposta: c. Corretto: con -1 split tiene tutti i campi, anche quelli vuoti in fondo, e possiamo contarli e segnalare l'errore.

**Domanda 15.** Due thread incrementano lo stesso int condiviso con count++, centomila volte ciascuno. Che cosa succede di solito?

- a. Il risultato è spesso inferiore a 200000 e cambia a ogni esecuzione
- b. Il programma si ferma con un'eccezione appena i due thread scrivono insieme
- c. Il risultato è sempre 200000, perché ++ è un'operazione unica

Risposta: a. Corretto: alcuni aggiornamenti vanno persi. Le soluzioni sono non condividere dati modificabili oppure usare AtomicInteger.

**Domanda 16.** In quale caso la lezione consiglia i thread virtuali?

- a. Dentro un pool fisso di pochi thread virtuali, da riutilizzare con cura
- b. Solo come anteprima, perché in Java 25 non sono ancora definitivi
- c. Per un calcolo intensivo che usa sempre il processore
- d. Per attività che aspettano rete, database o file, con un thread per ogni attività

Risposta: d. Corretto: quando un thread virtuale si blocca, lascia libero il portatore. Per questo diecimila attività da un secondo finiscono quasi subito.

**Domanda 17.** Una classe di test contiene due metodi @Test e un metodo @ParameterizedTest con quattro righe in @CsvSource. Quanti test riporta l'esecuzione, se passano tutti?

- a. 4 tests passed
- b. 6 tests passed
- c. 3 tests passed
- d. 2 tests passed

Risposta: b. Corretto: due test normali più quattro esecuzioni del test parametrizzato, una per riga di @CsvSource.

**Domanda 18.** Il test di saveReceipt scrive nel file la data come 2026-11-07 e passa ogni giorno. Come è possibile?

- a. Il Cart riceve un Clock.fixed, un orologio fermo, e così la data è sempre la stessa
- b. LocalDate.now() restituisce sempre la data della prima esecuzione
- c. @TempDir cancella il file e lo ricrea con la data giusta
- d. assertSoftly ignora le differenze sulla data

Risposta: a. Corretto: l'orologio arriva dal costruttore e nel test è fermo su un istante. Con l'orologio vero il test fallirebbe già domani.

**Domanda 19.** Nel terminale lanciamo ./mvnw package. Che cosa fa Maven?

- a. Crea subito il jar, senza compilare né eseguire i test
- b. Crea il jar e poi esegue i test, per controllarlo alla fine
- c. Esegue validate, compile e test, e solo se i test passano crea il jar
- d. Cancella la cartella target e poi crea il jar

Risposta: c. Corretto: ogni fase esegue prima tutte le precedenti. Se un test fallisce la build si ferma e il jar non viene creato.

**Domanda 20.** Nel progetto ci sono la cartella target e un file .env con una chiave segreta. Che cosa conviene fare prima del primo commit?

- a. Fare il commit di tutto e cancellare il .env dopo, se serve
- b. Elencarli in un file .gitignore, così git add . non li mette nella storia
- c. Non usare git add e sperare che Git non li veda
- d. Spostarli nello stage e non fare il commit

Risposta: b. Corretto: una riga per percorso, e il .gitignore stesso va versionato per la squadra.

**Domanda 21.** Durante git merge compare "merge conflict in README.md". Che cosa significa e che cosa si fa?

- a. Due modifiche toccano lo stesso punto: si sistema il file, git add e un commit chiudono il merge
- b. Il repository è rotto e va ricreato con git init
- c. Il merge è riuscito, i segni nel file sono solo un avviso
- d. Git ha scelto da solo la versione del branch

Risposta: a. Corretto: Git non sa quale versione vogliamo, quindi decide una persona. In alternativa si annulla con git merge --abort.

## Quiz: clean code, SOLID, DRY e KISS

Verifica DRY e KISS, i cinque principi SOLID, i pattern Strategy, Factory e Builder, l'architettura esagonale e il dominio dello Shop.

**Domanda 1.** Nel codice ci sono due controlli identici: price &gt; 0 per i prezzi e quantity &gt; 0 per le quantità. Che cosa suggerisce la lezione?

- a. Lasciarli separati: sono due regole diverse che oggi si somigliano per caso
- b. Creare un'interfaccia Validator con due implementazioni, una per regola
- c. Copiarli anche in ogni altra classe che usa prezzi e quantità, per sicurezza
- d. Unirli subito in un solo metodo, perché DRY vieta due righe uguali

Risposta: a. Corretto: è una falsa duplicazione. Se domani la quantità avrà anche un massimo, un metodo comune romperebbe la regola del prezzo.

**Domanda 2.** Che cosa significa il principio di responsabilità singola, la S di SOLID?

- a. Ogni classe deve avere un solo metodo pubblico
- b. Una classe deve avere al massimo poche decine di righe
- c. Una classe dovrebbe avere una sola ragione per cambiare
- d. Ogni metodo deve stare in una classe diversa, per non mescolare nulla

Risposta: c. Corretto: le richieste di modifica devono arrivare dalla stessa direzione. Calcolo e IVA restano insieme perché cambiano insieme, la ricevuta va altrove.

**Domanda 3.** DiscountCalculator riceve una List&lt;DiscountRule&gt; e somma gli sconti delle regole. Arriva il Black Friday. Che cosa cambia nel codice, secondo il principio aperto chiuso?

- a. Si aggiunge un else if nel metodo discountInCents di DiscountCalculator
- b. Una nuova classe BlackFridayRule nella lista delle regole; DiscountCalculator non cambia
- c. Si aggiunge un valore BLACK_FRIDAY all'enum CustomerType e poi un nuovo case in ogni switch che usa il tipo di cliente

Risposta: b. Corretto: un caso nuovo è una classe nuova. L'unico punto toccato è quello che compone la lista, dove il caso costa una riga.

**Domanda 4.** DigitalProduct estende Product e ridefinisce shippingCostInCents() lanciando UnsupportedOperationException. Il codice compila. Qual è il problema e il rimedio visto nella lezione?

- a. Nessun problema: basta un if con instanceof nel metodo che somma le spedizioni
- b. Il problema è il messaggio dell'eccezione: va reso più chiaro
- c. Va dichiarata final la classe Product, così nessuno può estenderla
- d. La sottoclasse tradisce la promessa di Product: la spedizione va spostata nell'interfaccia Shippable, implementata solo dai prodotti fisici

Risposta: d. Corretto: è una violazione di Liskov. Con Shippable mettere un ebook tra i pacchi diventa un errore di compilazione, non di esecuzione.

**Domanda 5.** Dopo aver spezzato OrderOperations in ruoli piccoli, l'archivio diventa una sola riga: OrderExporter archive = () -&gt; "Book,Pen"; Perché è possibile?

- a. Perché OrderExporter ha un solo metodo astratto, quindi è un'interfaccia funzionale
- b. Perché ShopOrders implementa già tutte e quattro le interfacce
- c. Perché ogni interfaccia Java si può implementare con una lambda, qualunque sia il numero di metodi
- d. Perché ReportJob riceve l'esportatore dal costruttore

Risposta: a. Corretto: una lambda può implementare un'interfaccia con un solo metodo astratto. Prima l'archivio doveva scrivere cinque metodi, tre con eccezioni e uno vuoto.

**Domanda 6.** Quale frase distingue correttamente inversione delle dipendenze e iniezione delle dipendenze?

- a. Sono due nomi della stessa cosa: il servizio crea da solo, con new, gli oggetti concreti di cui ha bisogno per lavorare
- b. L'iniezione richiede sempre Spring, l'inversione no
- c. L'inversione è il principio (dipendere da astrazioni), l'iniezione la tecnica (l'oggetto arriva dal costruttore)
- d. L'inversione è la tecnica del costruttore, l'iniezione è il principio delle astrazioni

Risposta: c. Corretto: OrderService dipende da PaymentGateway, e il Main, la composition root, gli passa StripePayment o FakePayment.

**Domanda 7.** In OrderService la spedizione è amountInCents &lt; 2000 ? 500 : 0, e placeOrder addebita importo più spedizione al PaymentGateway ricevuto dal costruttore. Che cosa stampa questo codice?
```
var fake = new FakePayment();
var tested = new OrderService(fake);
tested.placeOrder("T1", 1200);
tested.placeOrder("T2", 3000);
System.out.println(fake.charges());
```

- a. Niente: FakePayment non è uno StripePayment e il costruttore lo rifiuta
- b. [1700, 3500]
- c. [1200, 3000]
- d. [1700, 3000]

Risposta: d. Corretto: 1200 + 500 e 3000 + 0. La regola è verificata senza addebitare nessuno, grazie al pagamento finto.

**Domanda 8.** In un test con Mockito hai scritto per abitudine una riga given su payment.charge, ma il servizio si ferma prima di chiamare il gateway. Che cosa succede con gli strict stubs?

- a. Niente, il test passa: gli stub in più sono sempre ammessi
- b. Mockito aggiunge una chiamata al gateway per usare lo stub
- c. Il test fallisce con UnnecessaryStubbingException: lo stub inutile è un segnale e va cancellato
- d. Il test fallisce perché il mock restituisce null

Risposta: c. Corretto: ogni risposta preparata deve essere usata. Uno stub inutile indica quasi sempre un test copiato o un codice che non passa da dove crediamo.

**Domanda 9.** Quando conviene il pattern Builder, secondo la lezione?

- a. Quando si vuole nascondere quale classe concreta viene creata
- b. Quando i parametri sono tanti e spesso facoltativi, perché Java non ha parametri con nome né valori predefiniti
- c. Quando bisogna scegliere un algoritmo mentre il programma gira
- d. Sempre, per ogni record: rende la creazione più professionale

Risposta: b. Corretto: con il builder ogni valore ha un nome, e build() controlla che l'oggetto sia completo prima di crearlo.

**Domanda 10.** Nell'architettura esagonale della lezione, dove sta l'interfaccia OrderRepository e chi la implementa?

- a. Sta nel dominio, insieme al record Order, e la implementa il caso d'uso PlaceOrderService dello strato applicazione
- b. Nell'applicazione, che la decide; la implementa l'adattatore InMemoryOrderRepository
- c. Sta nel Main, perché è lui che collega tutti gli strati
- d. Sta nell'infrastruttura, accanto al database, e la implementa il dominio

Risposta: b. Corretto: la porta la decide chi la usa, e l'infrastruttura dipende dal centro, mai il contrario.

**Domanda 11.** Il costruttore compatto di Order esegue lines = List.copyOf(lines). Che cosa stampa questo codice?
```
List<OrderLine> lines = new ArrayList<>();
lines.add(new OrderLine(pen, 1));
var order = new Order(lines);
lines.clear();
System.out.println(order.lines().size());
```

- a. Lancia IllegalArgumentException, perché l'ordine è diventato vuoto
- b. 0, perché l'ordine condivide la lista che abbiamo svuotato
- c. 1

Risposta: c. Corretto: l'ordine tiene la sua copia immutabile delle righe. È proprio il secondo test della lezione, keeps its own copy of the lines.

**Domanda 12.** Nel TDD si scrive un test per la spedizione e lo si esegue prima di scrivere la regola. Perché è importante vederlo fallire per il motivo giusto?

- a. Perché il TDD richiede almeno un test rosso prima di poter eseguire quelli verdi
- b. Perché un test che fallisce rende il refactoring più veloce
- c. Perché così non serve scrivere la lista dei test
- d. Perché vedendolo fallire sappiamo che distingue il codice giusto da quello sbagliato: un test mai visto fallire potrebbe non verificare niente

Risposta: d. Corretto: nella lezione il test fallisce con expected 500 but was 0, il valore e non un errore di compilazione. Un test che non è mai stato rosso potrebbe non controllare nulla.

## Quiz: Spring Core

Verifica inversione del controllo, bean, scansione, Primary e Qualifier, scope e ciclo di vita, configurazione esterna, eventi e test del container.

**Domanda 1.** Creiamo il contesto con new AnnotationConfigApplicationContext(InMemoryProductRepository.class, CatalogService.class). CatalogService ha un solo costruttore, che riceve un InMemoryProductRepository. Come arriva il repository al servizio?

- a. CatalogService deve estendere una classe di Spring per farsi iniettare il repository
- b. Serve @Autowired sul costruttore di CatalogService, altrimenti Spring non sa che cosa passare e il campo resta null
- c. Il main deve ancora chiamare new InMemoryProductRepository() e passarlo a getBean
- d. Spring legge il costruttore, crea prima il repository e lo passa al servizio, senza annotazioni

Risposta: d. Corretto: è l'inversione del controllo. Con un solo costruttore Spring sa già che cosa iniettare, e getBean consegna il servizio completo.

**Domanda 2.** In ShopConfig (con @Configuration) c'è questo metodo. Come si chiama il bean, e da dove arriva il parametro?
```
@Bean
public CatalogService catalogService(ProductRepository productRepository) {
    return new CatalogService(productRepository);
}
```

- a. Il bean si chiama CatalogService, come la classe restituita; il parametro lo passa il main quando chiama il metodo catalogService
- b. Il bean si chiama catalogService, come il metodo; il parametro è il bean di tipo ProductRepository, che Spring cerca nel contenitore
- c. Il bean si chiama productRepository; il parametro resta null finché non si chiama getBean

Risposta: b. Corretto: nome del bean = nome del metodo, tipo = tipo restituito, dipendenze = parametri del metodo.

**Domanda 3.** Con @ComponentScan("com.shop") Spring trova la classe InMemoryProductRepository annotata con @Repository. Con quale nome possiamo chiedere quel bean a getBean?

- a. "inMemoryProductRepository"
- b. "repository", il nome dello stereotipo usato
- c. "productRepository", il nome dell'interfaccia che implementa
- d. "InMemoryProductRepository", esattamente come la classe

Risposta: a. Corretto: un bean trovato dalla scansione si chiama come la sua classe, con l'iniziale minuscola.

**Domanda 4.** CardPayment e CashPayment implementano PaymentMethod, entrambe con @Component, e CardPayment ha anche @Primary. CheckoutService riceve un PaymentMethod senza annotazioni; CounterCheckout lo riceve con @Qualifier("cashPayment"). Che cosa succede all'avvio?

- a. Il contesto si ferma con NoUniqueBeanDefinitionException, perché i candidati sono due
- b. Entrambi ricevono CashPayment, perché @Qualifier vale per tutto il contesto
- c. CheckoutService riceve la carta, CounterCheckout i contanti
- d. Entrambi i servizi ricevono CardPayment, perché @Primary vince su @Qualifier

Risposta: c. Corretto: @Primary indica la scelta normale, @Qualifier sceglie per nome in un punto preciso e vince su @Primary.

**Domanda 5.** ShoppingCart è un @Component senza @Scope. Anna e Marco lo chiedono con getBean e Anna aggiunge una tastiera. Che cosa vede Marco, e che cosa cambia con @Scope("prototype")?

- a. Marco vede la tastiera in entrambi i casi, perché prototype cambia solo il momento della creazione
- b. Marco vede la tastiera di Anna; con prototype ognuno riceve un carrello nuovo e Marco lo vede vuoto
- c. Marco vede un carrello vuoto in entrambi i casi, perché getBean crea sempre un oggetto nuovo

Risposta: b. Corretto: di base il bean è un singleton condiviso da tutti. Con prototype Spring crea un oggetto nuovo a ogni getBean.

**Domanda 6.** ProductCache è un singleton con un metodo @PostConstruct load() e un metodo @PreDestroy clear(). Il main crea il contesto in un try con risorse e stampa "context ready" come prima riga del try. In che ordine compaiono le stampe?

- a. cache created, cache loaded, context ready, e cache cleared quando il try con risorse chiude il contesto
- b. cache created e context ready; load e clear vanno chiamati dal main
- c. context ready, poi cache created e cache loaded alla prima getBean, e cache cleared alla fine del main
- d. cache loaded, cache created, context ready; cache cleared non compare mai

Risposta: a. Corretto: costruttore, poi @PostConstruct dopo l'iniezione; @PreDestroy alla chiusura del contesto.

**Domanda 7.** shop.properties contiene solo shop.currency=EUR. Il costruttore di CheckoutService ha il parametro @Value("${shop.minimum-order:1000}") int minimumInCents. Quanto vale minimumInCents?

- a. Il contesto si ferma all'avvio, perché la chiave manca nel file
- b. 0, il valore predefinito di un int
- c. 1000
- d. La stringa "${shop.minimum-order:1000}", copiata così com'è

Risposta: c. Corretto: la chiave non è nel file, quindi vale il valore dopo i due punti. Spring converte anche il testo in int.

**Domanda 8.** placeOrder stampa "saved", pubblica OrderPlaced con publishEvent e poi stampa "completed". EmailListener (@Order(1)) stampa "email", StockListener (@Order(2)) stampa "stock". Senza @Async, in che ordine compaiono le righe?

- a. email, stock, saved, completed
- b. saved, completed, email, stock
- c. saved, stock, email, completed
- d. saved, email, stock, completed

Risposta: d. Corretto: i listener girano nello stesso thread, dentro publishEvent, nella sequenza fissata da @Order.

**Domanda 9.** CheckoutServiceTest crea il servizio con new e un PaymentGateway finto; ShopConfigTest usa @SpringJUnitConfig(ShopConfig.class). Dimentichiamo @Component su BankPaymentGateway. Quale test se ne accorge?

- a. Entrambi, perché tutti i test di un progetto Spring avviano il contesto
- b. CheckoutServiceTest, perché verifica la logica del checkout
- c. Nessuno dei due: un'annotazione mancante si scopre solo in produzione
- d. ShopConfigTest, che carica la configurazione vera

Risposta: d. Corretto: è il compito dei test del contesto. Pochi test di questo tipo in cima alla piramide, tanti test unitari alla base.

## Quiz: Spring Boot

Verifica Initializr, starter e autoconfigurazione, configurazione esterna, logging strutturato, DevTools, Actuator e i perimetri dei test in Spring Boot.

**Domanda 1.** Quale frase descrive correttamente i ruoli di Spring Initializr, Spring Boot e Spring Framework?

- a. Initializr genera anche i servizi e le regole del negozio a partire dal nome del progetto
- b. Initializr è una libreria che resta nel Jar e crea i bean a ogni avvio
- c. Spring Boot sostituisce Spring Framework, quindi container e iniezione dal costruttore non servono più
- d. Initializr genera il progetto; Boot prepara l'avvio; Spring gestisce i bean durante l'esecuzione

Risposta: d. Corretto: sono tre ruoli diversi. Initializr non scrive le regole del negozio, che restano nostre.

**Domanda 2.** Il progetto Shop appena generato non ha dipendenze web. Lanciamo java -jar target/shop-0.0.1-SNAPSHOT.jar. Che cosa succede?

- a. Errore: la parola SNAPSHOT indica una versione sperimentale di Spring Boot
- b. Parte Tomcat sulla porta 8080 e resta in ascolto
- c. Il contesto si avvia, ShopApplication risulta partita e il processo termina
- d. Il Jar non parte, perché un'applicazione Spring Boot ha sempre bisogno di un controller

Risposta: c. Corretto: è il comportamento previsto per il progetto iniziale. Il server compare solo quando aggiungiamo lo starter web MVC.

**Domanda 3.** Dopo aver aggiunto spring-boot-starter-webmvc, Tomcat parte, ma una richiesta a http://localhost:18080/ restituisce 404. Perché?

- a. Il server risponde, ma non esiste un controller per la radice
- b. Perché lo starter web MVC non è stato scaricato da Maven
- c. Perché il metodo main di ShopApplication va modificato per avviare davvero il server web incorporato
- d. Perché manca la versione nel blocco dependency del pom

Risposta: a. Corretto: Boot prepara l'infrastruttura web e la gestione predefinita degli errori, ma non inventa le risorse del negozio.

**Domanda 4.** Con lo starter web MVC nel Jar, avviamo l'applicazione con la proprietà spring.main.web-application-type=none. Che cosa osserviamo?

- a. Tomcat parte comunque, perché lo starter web ha la precedenza sulle proprietà
- b. Il contesto parte senza server web e torna il prompt, anche se le librerie web sono nel Jar
- c. L'avvio fallisce perché le librerie web e la proprietà sono in conflitto

Risposta: b. Corretto: il classpath è solo uno degli elementi della decisione. Anche le proprietà influenzano il comportamento di Boot.

**Domanda 5.** In application.yml c'è shop.shipping-in-cents: ${SHOP_SHIPPING:490}. Avviamo lo stesso Jar con la variabile d'ambiente SHOP_SHIPPING=190 e l'argomento --shop.shipping-in-cents=0. Quale valore mostra l'applicazione?

- a. 0
- b. 190, perché la variabile d'ambiente vince sempre
- c. Errore all'avvio, perché la stessa proprietà arriva da due sorgenti
- d. 490, il valore predefinito scritto nel file

Risposta: a. Corretto: nell'esempio della lezione l'argomento della riga di comando prevale sulla configurazione letta dal file e dal suo placeholder.

**Domanda 6.** Il servizio registra l'evento con log.atInfo().addKeyValue("orderId", orderId).addKeyValue("totalInCents", total).log("checkout_completed"). Avviamo l'applicazione con il livello del package com.shop impostato a WARN. Che cosa succede all'evento?

- a. Compare, ma senza i campi orderId e totalInCents
- b. Compare in JSON, perché il formato logstash mostra tutti gli eventi
- c. Compare come testo semplice invece che in JSON
- d. Non compare, perché è un evento INFO e il livello minimo è WARN

Risposta: d. Corretto: formato e livello sono scelte diverse. Il livello filtra gli eventi, il formato li rappresenta.

**Domanda 7.** L'applicazione gira con DevTools. Modifichiamo il messaggio da versione 1 a versione 2 e salviamo il file Java. Che cosa serve, nella demo, perché DevTools riavvii il contesto?

- a. Bisogna ricostruire il Jar con ./mvnw package
- b. Compilare, per esempio con ./mvnw compile, che aggiorna target/classes
- c. Chiamare l'endpoint /actuator/restart
- d. Basta il salvataggio: DevTools interpreta il sorgente Java a ogni modifica del file, senza compilare

Risposta: b. Corretto: DevTools rileva la modifica delle classi e riavvia il contesto. Se l'IDE compila da solo, il passaggio è automatico.

**Domanda 8.** /actuator/health risponde UP. Che cosa possiamo concludere, secondo la lezione?

- a. Che tutte le regole del negozio sono corrette
- b. Che l'applicazione non ha bisogno di test
- c. Che i controlli operativi configurati sono positivi, non che ogni caso d'uso funzioni
- d. Che anche /actuator/env è esposto e accessibile

Risposta: c. Corretto: Actuator descrive aspetti operativi. Disponibilità operativa e correttezza funzionale sono cose diverse.

**Domanda 9.** La specifica dice: spedizione gratuita da 5000 centesimi inclusi, altrimenti 490. Quanto restituisce shipping(5000) con questo codice, e quale test scopre il problema?
```
int shipping(int subtotalInCents) {
    return subtotalInCents > 5000 ? 0 : 490;
}
```

- a. 0; lo scopre il test con l'importo negativo
- b. 490; lo può scoprire solo un test @SpringBootTest con il contesto completo
- c. 0; nessun test lo scopre, perché il codice è corretto
- d. 490; lo scopre un test unitario proprio sul valore 5000, che si aspetta 0

Risposta: d. Corretto: è sul valore esatto che &gt; e &gt;= danno risultati diversi. Basta un oggetto Java, senza avviare Spring.

**Domanda 10.** Vogliamo verificare che QuoteController legga il parametro HTTP e deleghi al servizio, senza avviare tutta l'applicazione e senza dipendere dalla vera regola di spedizione. Quale combinazione usa la lezione?

- a. @SpringBootTest, con il vero ShippingService
- b. @SpringBootTest con una porta reale e un client HTTP esterno
- c. @WebMvcTest con MockMvc e @MockitoBean per il servizio
- d. Un test unitario che crea il controller con new e chiama direttamente il suo metodo, senza HTTP

Risposta: c. Corretto: la slice MVC carica solo il web layer, MockMvc simula le richieste senza server reale e il mock sostituisce il servizio.

## Quiz: Spring MVC e REST

Verifica il percorso di una richiesta, il contratto REST, DTO, validazione, ProblemDetail, paginazione, versionamento, OpenAPI, client HTTP e pagine Thymeleaf.

**Domanda 1.** Il metodo quote è dichiarato con @GetMapping("/api/shipping") e @RequestParam int subtotalInCents. Inviamo POST /api/shipping?subtotalInCents=2000. Quale stato riceviamo?

- a. 404, perché il percorso non esiste
- b. 400, perché il parametro non viene letto con POST
- c. 200, perché il percorso e il parametro sono corretti
- d. 405, metodo non consentito

Risposta: d. Corretto: abbiamo dichiarato solo GET su quel percorso. Il servizio di spedizione non viene nemmeno chiamato.

**Domanda 2.** Inviamo DELETE /api/products/2: risponde 204. Inviamo di nuovo la stessa DELETE: risponde 404. Che cosa dice la lezione su questo comportamento?

- a. È corretto perché DELETE è safe come GET
- b. È corretto: DELETE è idempotente rispetto all'effetto, il prodotto resta assente
- c. È un errore del server: una seconda DELETE dovrebbe ricreare il prodotto
- d. Dimostra che DELETE non è idempotente, quindi la seconda risposta dovrebbe essere ancora 204

Risposta: b. Corretto: nel contratto distinguiamo una rimozione avvenuta ora (204) da una risorsa già assente (404).

**Domanda 3.** Il record di dominio Product contiene anche supplierCostInCents. Il controller lo restituisce così com'è. Qual è la soluzione vista nella lezione?

- a. Scrivere a mano la stringa JSON nel controller, con i soli campi pubblici
- b. Togliere supplierCostInCents da Product, perché il client non deve vederlo
- c. Restituire un record ProductResponse con i soli id, name e priceInCents
- d. Aggiungere una libreria di mapping per convertire automaticamente Product

Risposta: c. Corretto: il DTO di risposta, creato con ProductResponse.from(product), sceglie i dati pubblici. Dominio e contratto HTTP hanno motivi diversi per cambiare.

**Domanda 4.** CreateProductRequest ha @NotBlank sul nome e @Positive sul prezzo, ma il parametro del controller è scritto solo come @RequestBody CreateProductRequest request. Che cosa succede con un prezzo zero?

- a. La richiesta viene accettata: senza @Valid i vincoli non vengono controllati
- b. Jackson rifiuta lo zero durante la conversione del JSON
- c. Spring risponde 400, perché i vincoli sul record si applicano sempre da soli
- d. La compilazione fallisce, perché @Positive richiede @Valid

Risposta: a. Corretto: le annotazioni descrivono le regole, ma serve @Valid sul parametro per applicarle prima del metodo del controller.

**Domanda 5.** In un ProblemDetail (RFC 9457), quale campo identifica la categoria del problema e non va cambiato una volta pubblicato, perché i client ci costruiscono sopra la loro logica?

- a. errors
- b. detail
- c. instance
- d. type

Risposta: d. Corretto: type è un identificatore stabile della categoria. I messaggi si possono migliorare, la categoria resta quella.

**Domanda 6.** Il catalogo ha 12 prodotti, con id da 1 a 12, già ordinati. Il servizio taglia la pagina come nella lezione. Che cosa stampa questo codice?
```
List<Integer> ids = IntStream.rangeClosed(1, 12).boxed().toList();
int page = 1;
int size = 3;
List<Integer> content = ids.stream().skip((long) page * size).limit(size).toList();
int totalPages = (ids.size() + size - 1) / size;
System.out.println(content + " " + totalPages);
```

- a. [4, 5, 6] 4
- b. [3, 4, 5] 4
- c. [4, 5, 6] 3
- d. [1, 2, 3] 4

Risposta: a. Corretto: skip salta page per size elementi, limit ne tiene size. Con 12 prodotti e 3 per pagina le pagine sono quattro.

**Domanda 7.** Con spring.mvc.apiversion configurato sull'header API-Version e default 1.0, quale modifica alla risposta del prodotto richiede davvero una nuova versione?

- a. Aggiungere un nuovo endpoint per la disponibilità
- b. Sostituire il numero priceInCents con un oggetto price con importo e valuta
- c. Aggiungere un nuovo campo, per esempio una descrizione
- d. Correggere un errore nel servizio senza cambiare la risposta

Risposta: b. Corretto: rinominare un campo o cambiarne il tipo è una modifica incompatibile. Solo allora serve una nuova versione.

**Domanda 8.** springdoc genera il contratto OpenAPI dal codice. Perché sulla risposta 404 di find scriviamo a mano il content, con application/problem+json e lo schema ProblemDetail?

- a. Perché springdoc non documenta mai le risposte di errore
- b. Perché senza quel content il server risponderebbe 500 invece di 404
- c. Perché altrimenti springdoc userebbe il tipo restituito dal metodo, cioè il prodotto, anche per il 404
- d. Perché Swagger UI mostra solo le risposte scritte a mano

Risposta: c. Corretto: così il contratto dice la verità anche sugli errori, che fanno parte dell'API quanto i successi.

**Domanda 9.** SupplierClient diventa un'interfaccia con @HttpExchange("/supplier") e un metodo @GetExchange("/stock/{productId}"). Chi scrive l'implementazione che esegue la chiamata HTTP?

- a. Spring genera un proxy, basato su RestClient, registrato come bean con @ImportHttpServices
- b. WebClient, perché le HTTP interface richiedono la programmazione reattiva
- c. La scriviamo noi in una classe annotata @Component che usa RestClient.Builder e l'indirizzo del fornitore, come prima del cambio
- d. Nessuno: un'interfaccia senza implementazione fa fallire l'avvio

Risposta: a. Corretto: ogni chiamata al metodo diventa una richiesta HTTP. L'indirizzo arriva da spring.http.serviceclient.supplier.base-url.

**Domanda 10.** Con MockRestServiceServer testi un client senza rete e senza porta aperta. Per quale caso devi invece passare a WireMock?

- a. Per far rispondere il fornitore con un errore 500
- b. Per simulare un timeout, una risposta lenta o una connessione interrotta
- c. Per controllare che il client chiami il percorso giusto
- d. Per testare un client scritto come HTTP interface

Risposta: b. Corretto: MockRestServiceServer sostituisce il pezzo che spedisce la richiesta e non apre una connessione. WireMock è un vero server HTTP e riproduce il comportamento della rete.

**Domanda 11.** In cima alla piramide dei test ci sono pochi test end to end. Perché non scrivere solo quelli?

- a. Perché non riescono a controllare lo stato e il corpo della risposta
- b. Perché la piramide vieta di usare un server vero
- c. Perché avviano un server e ogni configurazione diversa crea un altro contesto: costano di più, e li teniamo per i percorsi che contano
- d. Perché funzionano solo se si scrive la porta a mano

Risposta: c. Corretto: i test di fetta sono rapidi e dicono subito dove guardare. Ogni livello vede di più, ma costa di più.

**Domanda 12.** Nel metodo @PostMapping del form, con @Valid @ModelAttribute("product") ProductForm form e BindingResult, che cosa restituiamo dopo un salvataggio riuscito, e perché?

- a. Il nome della vista products/list, così l'utente vede subito l'elenco aggiornato
- b. "redirect:/products": il browser riceve un 302 e chiede l'elenco con una GET
- c. Una risposta JSON con il prodotto creato e lo stato 201
- d. Di nuovo la vista del form, con i campi vuoti

Risposta: b. Corretto: è il modello Post, Redirect, Get. Se l'utente ricarica, il form non viene inviato di nuovo.

**Domanda 13.** Il client invia un'immagine con nome ../../escaped.png e il server fa folder.resolve(nome). Qual è la difesa mostrata nella lezione?

- a. Togliere l'estensione dal nome del file.
- b. Normalizzare il percorso con normalize() e controllare che la cartella di arrivo sia proprio quella prevista.
- c. Accettare solo nomi più corti di 20 caratteri.
- d. Salvare i file dentro il Jar invece che in una cartella esterna.

Risposta: b. Corretto: normalize risolve i .., poi il controllo rifiuta il file se non resta nella cartella delle immagini (principio: mai fidarsi dell'input del client).

**Domanda 14.** Con spring.servlet.multipart.max-file-size impostato a 512KB, un client carica un'immagine di circa 576 KB. Che cosa riceve?

- a. 201 Created: il limite vale solo per il download
- b. 400 Bad Request, generato dal nostro controller
- c. 413 Content Too Large, prima che la richiesta arrivi al controller
- d. 500 Internal Server Error

Risposta: c. Corretto: Spring rifiuta la richiesta perché supera il limite (Maximum upload size exceeded).

## Quiz: Spring AOP

Verifica i concetti dell'AOP, gli advice @Before, @Around e @AfterReturning, i pointcut con annotazioni, le insidie dei proxy e quando non usare un aspetto.

**Domanda 1.** Nell'aspetto CallLoggingAspect troviamo @Before("execution(* com.shop.catalog.ProductService.*(..))") sopra un metodo che scrive una riga di log. Come si chiama la stringa execution(...) tra parentesi?

- a. Pointcut: l'espressione che sceglie i join point
- b. Advice: il codice da eseguire
- c. Aspect: la classe che riunisce tutto
- d. Join point: la chiamata di metodo in corso, cioè il punto in cui interveniamo

Risposta: a. Corretto: qui sceglie tutti i metodi di ProductService, con qualsiasi tipo di ritorno e qualsiasi parametro.

**Domanda 2.** Come fa Spring a eseguire l'advice quando un altro bean chiama ProductService?

- a. Legge un file XML con l'elenco dei metodi da intercettare
- b. Crea all'avvio un proxy che avvolge il servizio ed esegue l'advice
- c. Copia la riga di log dentro ogni metodo del servizio all'avvio
- d. Riscrive il file ProductService.class con il compilatore AspectJ durante la build

Risposta: b. Corretto: il chiamante parla con il proxy, che esegue l'advice e poi il metodo vero. È il weaving fatto da Spring, e per questo il test verificava che il servizio iniettato fosse un proxy.

**Domanda 3.** Questo advice @Around avvolge i metodi di ProductService. Che cosa riceve chi chiama productService.list()?
```
@Around("execution(* com.shop.catalog.ProductService.*(..))")
public Object time(ProceedingJoinPoint joinPoint) throws Throwable {
    long start = System.nanoTime();
    try { joinPoint.proceed(); return null; }
    finally { log.info("took {} ns", System.nanoTime() - start); }
}
```

- a. Un'eccezione, perché un advice @Around non può restituire null
- b. La lista dei prodotti, perché proceed() esegue il metodo vero
- c. null
- d. Niente: il metodo vero non viene eseguito, perché manca la riga di log prima di proceed()

Risposta: c. Corretto: il risultato di proceed() va restituito. Se lo dimentichiamo, il chiamante riceve null, come avverte la lezione.

**Domanda 4.** Nell'advice @Around corretto, il tempo viene scritto nel log dentro un blocco finally. Che cosa succede quando find(99) lancia ProductNotFoundException?

- a. La riga del tempo non compare, perché l'eccezione interrompe l'advice
- b. Spring rimuove il proxy dopo la prima eccezione
- c. La riga del tempo compare e l'aspetto trasforma l'eccezione in una risposta 200 vuota
- d. La riga del tempo compare e l'eccezione prosegue verso il chiamante, che risponde 404 come sempre

Risposta: d. Corretto: l'aspetto osserva e non cambia nulla. Il gestore degli errori riceve l'eccezione come se l'aspetto non ci fosse.

**Domanda 5.** Scriviamo l'annotazione @Audited con @Target(ElementType.METHOD) ma dimentichiamo @Retention(RetentionPolicy.RUNTIME). L'advice usa @AfterReturning("@annotation(audited)"). Che cosa succede?

- a. Il registro funziona lo stesso, perché @Target basta a Spring
- b. A runtime l'annotazione non si vede: il pointcut non trova metodi
- c. Il codice non compila, perché un'annotazione senza @Retention non è valida
- d. Vengono registrati tutti i metodi del servizio, anche le letture

Risposta: b. Corretto: con RUNTIME l'annotazione resta nel bytecode ed è visibile durante l'esecuzione. Senza, il registro resta vuoto.

**Domanda 6.** delete(99) è annotato con @Audited("product deleted") e lancia un'eccezione perché il prodotto non esiste. L'advice dell'audit è @AfterReturning. Il registro contiene una riga per questa cancellazione?

- a. Sì, con la parola failed accanto al nome dell'evento, per segnalare l'errore
- b. Sì, perché il metodo è annotato
- c. No: @AfterReturning parte solo dopo un ritorno normale

Risposta: c. Corretto: il registro contiene soltanto le operazioni riuscite, e uno dei quattro test lo verifica.

**Domanda 7.** In ProductService, importAll(drafts) chiama this.create(...) per ogni bozza, e create è annotato con @Audited. ProductImporter chiama productService.importAll(...). Perché i prodotti importati non finiscono nel registro?

- a. La chiamata interna con this salta il proxy, quindi l'advice non parte
- b. Perché create andava dichiarato final per essere intercettato
- c. Perché @Audited funziona solo se il metodo è chiamato dal controller
- d. Perché un metodo può avere un solo advice, e importAll lo ha già consumato prima di arrivare a create

Risposta: a. Corretto: nessun errore e nessun avviso. La soluzione più semplice è spostare il ciclo in un altro bean, ProductImporter, che chiama il proxy.

**Domanda 8.** Perché, secondo la lezione, a volte si sente dire che @Transactional "non funziona"?

- a. Perché va dichiarata anche nel costruttore del bean
- b. Perché funziona solo sulle classi final
- c. Perché @Transactional richiede sempre un compilatore AspectJ
- d. Perché segue le stesse regole del proxy: con this, su metodi private o final, la transazione non parte

Risposta: d. Corretto: stesso sintomo, stessa causa, stessa soluzione. E per capirlo non serve nemmeno un database.

**Domanda 9.** La regola "il prezzo deve essere positivo" viveva in PriceRuleAspect, con un pointcut solo su create, e changePrice la saltava. Dove la sposta la lezione, e perché?

- a. In un secondo aspetto @Around, più potente di @Before
- b. Nel costruttore compatto del record Product: è una regola del dominio
- c. Nel controller, che controlla il prezzo prima di chiamare il servizio, così il servizio riceve solo prezzi validi
- d. In un pointcut più largo, che copra anche changePrice

Risposta: b. Corretto: un Product con prezzo zero non può più esistere, da qualunque strada arrivi. Una classe in meno: è KISS.

## Quiz: persistenza con Spring Data JPA

Verifica JDBC e JPA, entità e repository, query e proiezioni, il problema N+1, le transazioni, Flyway, PostgreSQL con Docker Compose, Testcontainers e optimistic locking.

**Domanda 1.** In findById scriviamo la query con JdbcClient così. Perché usiamo :id e param invece di concatenare l'id nella stringa?
```
return jdbc.sql("SELECT id, name, price_in_cents FROM product WHERE id = :id")
        .param("id", id)
        .query(JdbcProductRepository::toProduct)
        .optional();
```

- a. Perché così Hibernate genera la query al posto nostro
- b. Perché JdbcClient accetta solo query senza numeri
- c. Perché con :id il database mette in cache la query e la esegue molto più velocemente
- d. Il valore resta separato dal testo della query: niente SQL injection

Risposta: d. Corretto: non concateniamo stringhe. Il valore arriva con param, e optional restituisce un Optional vuoto se la riga non c'è.

**Domanda 2.** Che cosa ci costa un ORM come JPA con Hibernate, secondo la lezione?

- a. Va controllato l'SQL generato: una relazione può produrre molte query
- b. Nulla: genera l'SQL ed è sempre più veloce di JDBC
- c. Non permette più di nascondere la persistenza dietro una porta come ProductRepository
- d. Obbliga a scrivere a mano INSERT e UPDATE per ogni tabella

Risposta: a. Corretto: vanno capiti anche il ciclo di vita delle entità e i proxy. In cambio scriviamo molto meno codice ripetitivo. Per report complessi o importazioni massive JDBC resta la scelta più semplice.

**Domanda 3.** Sostituiamo InMemoryProductRepository con JpaProductRepository, che implementa la stessa porta ProductRepository e delega a un repository Spring Data. Che cosa cambia in ProductService?

- a. Deve ricevere ProductEntity invece del record Product
- b. Niente: dipende solo dalla porta
- c. Va riscritto per ricevere ProductJpaRepository nel costruttore
- d. Va annotato con @Entity per poter salvare i prodotti

Risposta: b. Corretto: è l'inversione delle dipendenze, e gli stessi cinque test passano senza modifiche. Abbiamo cambiato tecnologia di persistenza sostituendo un solo dettaglio.

**Domanda 4.** Il listino con nome e prezzo diventa una query derivata che restituisce List&lt;ProductSummary&gt;, un record con due componenti. Con le statistiche di Hibernate, quante entità vengono caricate per costruire il listino di 5 prodotti?

- a. 1, perché tutte le righe finiscono in un'unica entità
- b. 5, una per ogni prodotto, come prima
- c. 0: la proiezione seleziona solo nome e prezzo e costruisce subito i record
- d. 3, perché Spring Data carica solo le entità nella fascia di prezzo

Risposta: c. Corretto: nessuna entità finisce nel contesto di persistenza. La select del listino non contiene nemmeno la colonna id.

**Domanda 5.** findAll legge 3 ordini; le righe sono LAZY e ogni riga punta a un prodotto, in tutto 5 prodotti diversi. Convertendo gli ordini nel dominio, quanti statement esegue Hibernate, e come si scende a uno solo?

- a. 9; si scende a uno con una query JPQL con left join fetch
- b. 9; mettendo FetchType.EAGER su tutte le relazioni
- c. 4 (1 per gli ordini e 3 per le righe); con @Transactional sul repository
- d. 1; non serve nulla, perché LAZY carica tutto in una volta

Risposta: a. Corretto: 1 select per gli ordini, 3 per le righe e 5 per i prodotti. È il problema N+1, e la fetch join, o @EntityGraph, carica ordini, righe e prodotti con una sola SELECT.

**Domanda 6.** Il metodo place di OrderService è annotato con @Transactional e, a metà, lancia un'eccezione checked (che estende Exception), senza rollbackFor. Che cosa fa Spring, per default?

- a. Niente: la transazione resta aperta finché il client non riprova
- b. Rollback, come per qualsiasi eccezione
- c. Commit: per un'eccezione checked serve rollbackFor per annullare
- d. Rollback solo dell'ultima scrittura, mantenendo le precedenti

Risposta: c. Corretto: è una regola che sorprende molti. Per questo la lezione usa eccezioni non controllate per gli errori di dominio.

**Domanda 7.** V1__create_product.sql è già stato applicato. Correggiamo un errore modificando direttamente quel file. Che cosa succede al prossimo avvio?

- a. Flyway riesegue V1 con la correzione
- b. Niente: Flyway ignora i file già applicati
- c. Hibernate corregge lo schema con ddl-auto validate
- d. L'avvio si ferma con un errore di validazione: il checksum non corrisponde

Risposta: d. Corretto: una migrazione applicata non si modifica più. Ogni cambiamento, anche una correzione, è una nuova versione, per esempio V3.

**Domanda 8.** Il progetto ha compose.yaml, spring-boot-docker-compose come dipendenza opzionale e H2 nello scope test. Perché i test passano anche su una macchina senza Docker?

- a. Perché i test usano la URL di PostgreSQL scritta in application.yml
- b. Nei test Spring Boot salta Docker Compose e usa H2
- c. Perché spring-boot-docker-compose finisce nel Jar e simula il database
- d. Perché Docker Compose avvia PostgreSQL anche senza Docker installato

Risposta: b. Corretto: è una scelta voluta, così i test restano veloci. L'applicazione avviata con spring-boot:run invece avvia PostgreSQL.

**Domanda 9.** Un @DataJpaTest controlla che il database sia PostgreSQL, ma non ha nessun container. Che cosa succede, e quali annotazioni sistemano il test?

- a. Trova H2; servono @Testcontainers, @Container e @ServiceConnection
- b. Il test usa PostgreSQL di compose.yaml; non serve aggiungere nulla
- c. Il test viene saltato; per farlo partire basta disabledWithoutDocker = false
- d. Il test fallisce perché manca una URL; basta scriverla in application-test.yml

Risposta: a. Corretto: senza un database per i test, @DataJpaTest usa uno incorporato. Con le tre annotazioni su un PostgreSQLContainer, Testcontainers avvia un PostgreSQL usa e getta e Spring Boot si collega da solo, senza @DynamicPropertySource.

**Domanda 10.** ProductEntity ha un campo @Version. Alice e Bob leggono la versione 0; Alice salva il nuovo prezzo. Bob invia il suo aggiornamento dichiarando ancora la versione 0. Che cosa succede?

- a. Il salvataggio di Bob sovrascrive quello di Alice, senza errori
- b. Hibernate unisce le due modifiche e porta la versione a 2
- c. Eccezione di optimistic locking, tradotta in 409 Conflict
- d. La riga resta bloccata finché Bob non chiude il client

Risposta: c. Corretto: l'UPDATE con WHERE id = ? AND version = ? non trova la riga. Api Error Handler restituisce un ProblemDetail 409 Conflict. Bob deve rileggere il prodotto, ora alla versione 1, e decidere se riprovare.

## Quiz: Spring Security

Verifica catena dei filtri, password come hash, utenti su database, JWT, OAuth2 con Keycloak, method security, CORS e CSRF, test della sicurezza, OWASP e segreti.

**Domanda 1.** Con la catena predefinita di Spring Security, Alice invia una POST di creazione con credenziali Basic corrette ma senza token CSRF. Quale stato riceve, e chi decide?

- a. 201, perché Alice è autenticata
- b. 500, perché il controller cerca il token CSRF nel corpo della richiesta e non lo trova
- c. 403, deciso dal CsrfFilter prima ancora di leggere le credenziali
- d. 401, perché il filtro Basic non accetta le POST

Risposta: c. Corretto: nel log compare Invalid CSRF token found. Il rifiuto dipende dalla forma della richiesta, non da chi è Alice.

**Domanda 2.** Che cosa stampa questo codice, con lo stesso valore dimostrativo codificato due volte?
```
PasswordEncoder encoder = PasswordEncoderFactories.createDelegatingPasswordEncoder();
String first = encoder.encode("demo-password");
String second = encoder.encode("demo-password");
System.out.println(first.equals(second) + " " + first.startsWith("{bcrypt}")
        + " " + encoder.matches("demo-password", first));
```

- a. false true false
- b. false true true
- c. false false true
- d. true true true

Risposta: b. Corretto: hash diversi per la stessa password, prefisso {bcrypt} del Delegating Password Encoder, e matches che riconosce comunque la password.

**Domanda 3.** Implementiamo UserDetailsService con JdbcClient. Che cosa fa il nostro loadUserByUsername, e che cosa resta a Spring Security?

- a. Trova l'utente con hash, ruolo e stato; il confronto della password lo fa Spring
- b. Cerca l'utente e confronta la password ricevuta con l'hash
- c. Restituisce la password in chiaro, che Spring poi codifica
- d. Sostituisce la SecurityFilterChain, che quindi va riscritta da capo con le nuove regole

Risposta: a. Corretto: se il nome non esiste lanciamo UsernameNotFoundException, e il client riceve 401 come per una password sbagliata.

**Domanda 4.** Un JWT emesso dall'endpoint /api/token è firmato RS256. Chi intercetta il token può leggerne i claim, per esempio sub e roles?

- a. No, perché il server tiene il contenuto in una sessione e il token è solo un identificativo
- b. No: il contenuto è cifrato con la chiave privata
- c. Solo se conosce la password dell'utente
- d. Sì, li legge, ma non può modificarli senza invalidare la firma

Risposta: d. Corretto: leggibile da tutti, modificabile da nessuno. Per questo la durata è breve, 15 minuti, e nel token non mettiamo segreti.

**Domanda 5.** L'API è un resource server configurato con issuer-uri verso Keycloak. I token contengono il ruolo USER, eppure Alice non riesce a creare un prodotto. Perché, e che cosa scriviamo?

- a. L'API deve chiamare Keycloak a ogni richiesta per conoscere i ruoli
- b. Il token è scaduto: basta allungarne la durata nell'applicazione
- c. Keycloak mette i ruoli in realm_access.roles, Spring legge scope: serve un convertitore
- d. Alice deve inviare anche la password all'API, insieme al token

Risposta: c. Corretto: il convertitore trasforma ogni ruolo in un'autorità con prefisso ROLE_, così hasRole funziona come prima.

**Domanda 6.** Scriviamo @PreAuthorize("hasRole('ADMIN')") sul metodo delete di ProductService, ma dimentichiamo @EnableMethodSecurity. Che cosa succede quando Alice, con il ruolo USER, chiama POST /api/clearance/2?

- a. Riceve 403: @PreAuthorize funziona sempre
- b. L'applicazione non parte, perché manca l'abilitazione della method security nella configurazione
- c. Riceve 401, perché il servizio non sa chi è
- d. L'annotazione viene ignorata in silenzio e la cancellazione riesce

Risposta: d. Corretto: con @EnableMethodSecurity il proxy valuta l'espressione prima del metodo, qualunque sia la strada HTTP.

**Domanda 7.** Quando serve davvero la protezione CSRF, secondo la lezione?

- a. Quando il browser allega da solo cookie o sessioni a richieste partite da un altro sito
- b. Quando il frontend si trova su un'altra origine, perché in quel caso CSRF prende il posto di CORS e decide chi legge
- c. Sempre, su ogni API: disattivarla è un errore
- d. Solo per le richieste GET

Risposta: a. Corretto: un'API stateless con credenziali in un'intestazione scritta dal client può farne a meno, sapendo perché.

**Domanda 8.** Nella catena dell'API le regole sono in quest'ordine. Un test con @WithMockUser(roles = "USER") prova a cancellare un prodotto. Che cosa succede?
```
.requestMatchers(HttpMethod.GET, "/api/products/**").permitAll()
.requestMatchers("/api/products/**").authenticated()
.requestMatchers(HttpMethod.DELETE, "/api/products/**").hasRole("ADMIN")
.anyRequest().authenticated()
```

- a. 403, perché la regola ADMIN vale per tutte le DELETE
- b. 204: basta essere autenticati, e la regola ADMIN non viene mai raggiunta
- c. L'applicazione non parte, perché due regole si sovrappongono
- d. 401, perché un utente finto non è un utente autenticato

Risposta: b. Corretto: è il difetto che il caso negativo ha scoperto. La riga in più era anche superflua: anyRequest().authenticated() la copre già.

**Domanda 9.** Alice chiede GET /api/orders/2, un ordine che appartiene a Bob. Dopo la correzione della lezione, che cosa risponde l'API, e perché?

- a. 401, perché deve autenticarsi di nuovo
- b. 200 con l'ordine, ma senza il campo owner
- c. 403, perché Alice non è la proprietaria
- d. 404, come per un ordine che non esiste

Risposta: d. Corretto: il servizio confronta il proprietario con l'utente autenticato e risponde come se l'ordine non esistesse.

**Domanda 10.** In application.yml c'era shop.payment.api-key: ${SHOP_PAYMENT_API_KEY:change-me}. Perché la lezione toglie il valore predefinito?

- a. Perché, se la variabile manca, l'app parte con una chiave finta senza avvisare
- b. Perché change-me è troppo corta per BCrypt
- c. Perché Spring Boot non accetta valori predefiniti nei segreti
- d. Per fare in modo che la chiave venga stampata nel log all'avvio, così possiamo controllarla

Risposta: a. Corretto: senza default, la validazione @NotBlank ferma l'avvio con un messaggio chiaro, che non contiene il segreto.

## Quiz: affidabilità e osservabilità

Verifica metriche e health check, tracing, caching, resilienza, job pianificati e asincroni, e i controlli di qualità nel build.

**Domanda 1.** Il nostro CatalogHealthIndicator risponde DOWN quando il catalogo è vuoto. In quale gruppo di health lo includiamo, e perché?

- a. In nessun gruppo: gli health indicator personalizzati non sono ammessi
- b. Nella readiness, che decide se mandare traffico
- c. In entrambi, con tutti i dettagli visibili a chiunque
- d. Nella liveness, così un catalogo vuoto fa riavviare l'applicazione

Risposta: b. Corretto: chi gestisce le istanze smette di mandare traffico finché l'applicazione non è pronta. Liveness e readiness rispondono a due domande diverse. Un test verifica che la liveness non dipenda dal catalogo.

**Domanda 2.** Nel servizio registriamo con Micrometer un Counter chiamato shop.products.added. Con quale nome lo troviamo nell'endpoint /actuator/prometheus?

- a. shop_products_added_count
- b. shop.products.added
- c. shop_products_added_total
- d. ShopProductsAdded

Risposta: c. Corretto: i punti diventano trattini bassi e il registry aggiunge il suffisso total, come vuole la convenzione per i contatori.

**Domanda 3.** Una richiesta arriva con l'header traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01. Nelle righe di log della nostra applicazione, che cosa vediamo tra parentesi quadre?

- a. Lo stesso trace id e uno span id nuovo
- b. Un trace id nuovo e lo span id 00f067aa0ba902b7
- c. Niente: gli identificativi compaiono solo se configuriamo un collector OTLP
- d. Il valore 01, che è il numero della richiesta

Risposta: a. Corretto: la nostra applicazione apre la sua operazione dentro la stessa traccia. È così che una traccia attraversa più servizi. Ognuno aggiunge i suoi span, tutti condividono il trace id.

**Domanda 4.** find è annotato così, mentre update non ha annotazioni di cache. Chiamiamo find(1), poi update(1, "Mechanical keyboard", 5200), poi di nuovo find(1). Quale nome restituisce l'ultima chiamata?
```
@Cacheable(cacheNames = "products", key = "#id")
public Product find(long id) { ... }

public Product update(long id, String name, int priceInCents) { ... }
```

- a. Un'eccezione, perché la voce in cache non corrisponde più al database
- b. null, perché update svuota la cache
- c. Mechanical keyboard, perché il repository è aggiornato
- d. Keyboard: serve @CachePut su update

Risposta: d. Corretto: sono i dati vecchi, il rischio principale di ogni cache. @CachePut scrive il valore nuovo con la stessa chiave, @CacheEvict su delete toglie la voce.

**Domanda 5.** Il metodo stock è annotato con @Retryable(includes = HttpServerErrorException.class, maxRetries = 2, delay = 200) e il fornitore risponde sempre 503. Abbiamo dimenticato @EnableResilientMethods. Quante chiamate arrivano al fornitore?

- a. 1: l'annotazione viene ignorata
- b. Infinite, finché il fornitore non risponde
- c. 2, cioè il valore di maxRetries
- d. 3: il primo tentativo più due nuovi tentativi

Risposta: a. Corretto: il primo errore arriva subito al chiamante. In Spring Framework 7 @Retryable e @ConcurrencyLimit funzionano solo se attiviamo i metodi resilienti. I test se ne sono accorti subito.

**Domanda 6.** Perché la lezione ritenta la lettura della disponibilità, ma non ritenterebbe un pagamento?

- a. Perché un pagamento ha già il suo circuit breaker incluso in Spring Boot 4
- b. Perché si ritentano solo operazioni idempotenti
- c. Perché i pagamenti sono sempre più veloci delle letture
- d. Perché @Retryable funziona solo sulle richieste GET

Risposta: b. Corretto: ritentare un pagamento potrebbe addebitarlo due volte. E ritentiamo solo errori temporanei del server, non i timeout né gli errori 4xx.

**Domanda 7.** Il job di pulizia dei carrelli ha @Scheduled(cron = "0 0 2 * * *"). Che cosa stampa questo codice?
```
CronExpression cron = CronExpression.parse("0 0 2 * * *");
LocalDateTime noon = LocalDateTime.of(2026, 10, 16, 12, 0);
System.out.println(cron.next(noon));
```

- a. 2026-10-16T14:00
- b. 2026-11-02T00:00
- c. 2026-10-17T02:00
- d. 2026-10-16T12:02

Risposta: c. Corretto: secondi, minuti, ore, giorno, mese, giorno della settimana. Dopo mezzogiorno, la prossima esecuzione è alle due di notte del giorno dopo.

**Domanda 8.** ConfirmationService.send è annotato con @Async e restituisce un CompletableFuture. Che cosa serve perché giri davvero su un thread virtuale?

- a. Un pool di thread configurato a mano, con una dimensione fissa pari al numero di processori
- b. Chiamare send da un altro metodo della stessa classe
- c. Basta @Async: il metodo è già asincrono e virtuale
- d. @EnableAsync e spring.threads.virtual.enabled: true

Risposta: d. Corretto: @EnableAsync crea il proxy, e la proprietà fa usare thread virtuali ad Async, allo scheduler e a Tomcat. Nessun pool configurato a mano.

**Domanda 9.** Con Spotless e Checkstyle nella fase validate e il check di JaCoCo nella fase verify, lanciamo ./mvnw verify. Il codice è formattato e rispetta lo stile, i test passano, ma la copertura delle righe è 0.76 con una soglia di 0.85. Che cosa succede?

- a. JaCoCo scrive da solo i test mancanti per arrivare all'85%
- b. Il build si ferma subito, nella fase validate, prima di compilare
- c. Il build riesce, perché tutti i test sono verdi
- d. Il build si ferma nella fase verify: la copertura è sotto la soglia

Risposta: d. Corretto: la soluzione è un test vero, come quello sulla cancellazione, non abbassare la soglia o portarla al 100%.

**Domanda 10.** ShippingPolicy ha copertura al 100% con JaCoCo, ma PIT uccide un solo mutante su otto. Che cosa significa?

- a. Che PIT è configurato male, perché JaCoCo dice che i test sono completi
- b. Che i test eseguono tutte le righe ma controllano quasi niente, e i mutanti sopravvissuti lo dimostrano
- c. Che servono più test, perché alcune righe non sono coperte
- d. Che il codice di produzione contiene sette bug

Risposta: b. Corretto: la copertura dice quali righe i test eseguono, non che cosa controllano. PIT ha fatto restituire zero al metodo e i test sono rimasti verdi.

**Domanda 11.** Perché PIT non si lega a verify e si limita con targetClasses e targetTests al cuore del dominio?

- a. Perché PIT funziona solo su classi con meno di dieci righe
- b. Perché PIT non è compatibile con JaCoCo
- c. Perché per ogni mutante bisogna rieseguire i test che lo coprono: su un codice grande il conto arriva a minuti o ore
- d. Perché il mutation score deve restare sempre al cento per cento

Risposta: c. Corretto: lo usiamo dove un errore piccolo costa caro, come prezzi e soglie, e lo lanciamo quando lavoriamo su una regola o in una pipeline separata.

## Quiz: Docker

Verifica immagini, container e volumi, Dockerfile multi stage, buildpacks e layer, immagini sicure, Docker Compose, healthcheck e segreti.

**Domanda 1.** Quale frase descrive correttamente immagine, container e registry?

- a. L'immagine è un container fermo, e il registry è la macchina virtuale Linux che esegue i container su macOS
- b. Immagine e container sono sinonimi; il registry è il comando docker
- c. Il container è il modello, l'immagine è il processo in esecuzione
- d. Immagine: modello in sola lettura a layer; container: immagine in esecuzione; registry: archivio

Risposta: d. Corretto: da una sola immagine possiamo avviare tanti container, ognuno con il suo processo, la sua rete e il suo file system.

**Domanda 2.** Avviamo PostgreSQL con -v shop-data:/var/lib/postgresql, creiamo dei dati, poi eseguiamo docker stop e docker rm. Avviamo un nuovo container con lo stesso volume. Che cosa succede?

- a. Il volume è stato cancellato insieme al container da docker rm
- b. PostgreSQL trova il database e salta l'inizializzazione: i dati sono ancora lì
- c. PostgreSQL inizializza un database vuoto, perché il container è nuovo
- d. Docker rifiuta di avviarlo, perché il volume appartiene al container cancellato

Risposta: b. Corretto: fermare e cancellare un container non tocca i volumi. Solo docker volume rm cancella davvero i dati.

**Domanda 3.** Nello stadio build del Dockerfile multi stage le istruzioni sono in quest'ordine. Modifichiamo una riga di Java e ricostruiamo. Quali passaggi Docker riprende dalla cache?
```
COPY mvnw pom.xml ./
COPY .mvn .mvn
RUN ./mvnw -B dependency:go-offline
COPY src src
RUN ./mvnw -B -o package -DskipTests
```

- a. Tutto, compreso il package, perché il pom non è cambiato
- b. Solo il package finale, perché con l'opzione -o Maven lavora offline e non guarda i sorgenti
- c. Pom, wrapper e dipendenze; ripartono solo COPY src e il package
- d. Nessuno: una modifica al codice ricostruisce tutto lo stadio

Risposta: c. Corretto: lo strato di go-offline dipende solo da pom e wrapper. Finché non cambiano, le dipendenze non vengono riscaricate.

**Domanda 4.** Che cosa contiene l'immagine finale della build multi stage della lezione?

- a. La JRE Temurin 25 e il solo app.jar, copiato con COPY --from=build
- b. Il JDK, Maven Wrapper, i sorgenti e il Jar, come nella versione a stadio unico
- c. Solo il Jar, senza nessun runtime Java
- d. Un plugin Maven per Docker che avvia l'applicazione

Risposta: a. Corretto: un'immagine più piccola, con meno software da aggiornare. È il refactoring KISS della lezione.

**Domanda 5.** Il Dockerfile copia i quattro layer estratti con jarmode tools (dependencies, spring-boot-loader, snapshot-dependencies, application), un COPY per layer. Modifichiamo solo il nostro codice. Quale strato dell'immagine cambia?

- a. Solo dependencies, perché contiene anche le nostre classi
- b. Solo application, lo strato più leggero
- c. Solo spring-boot-loader
- d. Tutti e quattro, perché il Jar è stato ricostruito

Risposta: b. Corretto: le dipendenze restano in cache, e chi scarica l'immagine trova già lo strato pesante. Una modifica al codice pesa pochi kilobyte.

**Domanda 6.** Per passare la password del database all'immagine, un collega propone ENV SPRING_DATASOURCE_PASSWORD=... nel Dockerfile. Che cosa dice la lezione?

- a. Mai: resta negli strati e chiunque scarichi l'immagine la legge, anche con docker history
- b. Va bene se aggiungiamo .env al .dockerignore
- c. Meglio ARG al posto di ENV, perché ARG non finisce nell'immagine
- d. Va bene, purché l'immagine giri con un utente non root

Risposta: a. Corretto: i segreti arrivano quando il container parte, dall'ambiente. Lo stesso vale per ARG e per i file copiati.

**Domanda 7.** Perché nello stadio finale scriviamo USER 10001:10001, con numeri e non con un nome?

- a. Perché con un numero al posto del nome il processo può aprire le porte privilegiate sotto la 1024
- b. Perché 10001 è il numero riservato all'utente root su Alpine
- c. Perché Alpine non accetta nomi di utente
- d. Non serve creare l'utente e chi esegue il container può verificare che non sia root

Risposta: d. Corretto: per esempio Kubernetes. I file copiati prima appartengono a root e il nostro utente può solo leggerli.

**Domanda 8.** Nel compose.yaml il servizio app ha depends_on: db con condition: service_healthy, e il servizio db ha un healthcheck con pg_isready. Come si collega l'applicazione al database?

- a. Con uno script di attesa che fa sleep finché il database non risponde
- b. Con la porta del database pubblicata su 127.0.0.1, che l'app usa dall'esterno
- c. Con jdbc:postgresql://db:5432/shop: nella rete di Compose ogni servizio si raggiunge con il suo nome
- d. Con jdbc:postgresql://localhost:5432/shop, perché i container sono sulla stessa macchina

Risposta: c. Corretto: e grazie a service_healthy l'app parte solo quando pg_isready risponde. Nessuna porta del database è pubblicata sul Mac.

**Domanda 9.** Nel compose.yaml la password diventa ${DB_PASSWORD:?set DB_PASSWORD in .env}. Lanciamo docker compose up senza file .env e senza variabile. Che cosa succede?

- a. I container partono con una password vuota
- b. Parte solo il database, mentre l'applicazione resta in attesa finché qualcuno non imposta la password
- c. Compose usa il valore scritto in .env.example
- d. Compose si ferma prima di creare i container, con il nostro messaggio

Risposta: d. Corretto: meglio un errore chiaro all'avvio. Il file .env vero resta fuori dal repository e dall'immagine.

## Quiz: microservizi

Verifica monolite modulare, bounded context, chiamate resilienti, Kafka, outbox, gateway, configurazione e discovery, sicurezza tra servizi, saghe e tracing distribuito.

**Domanda 1.** Nel monolite modulare, OrderService (modulo orders) importa com.shop.catalog.internal.InMemoryProductCatalog. I test sul calcolo del totale passano. Chi scopre il problema, e come si corregge?

- a. Nessuno: finché i test di comportamento passano, la struttura va bene
- b. Il compilatore, perché un package internal non è visibile da altri moduli
- c. Si risolve solo dividendo catalogo e ordini in due microservizi separati, ognuno con il suo database
- d. Il test ApplicationModules.verify(); si usa l'interfaccia ProductCatalog

Risposta: d. Corretto: il sottopackage internal è un dettaglio del catalogo. Dipendere dalla sua API pubblica è la D di SOLID.

**Domanda 2.** Nel servizio ordini, il record Order salva anche il nome e il prezzo unitario del prodotto. Perché, secondo la lezione?

- a. Conta il prezzo pagato all'acquisto, anche a catalogo fermo
- b. Perché il catalogo e gli ordini usano lo stesso database
- c. Perché i due servizi condividono la stessa classe Product
- d. Per pigrizia: sarebbe meglio leggere sempre il prezzo dal catalogo

Risposta: a. Corretto: ogni bounded context possiede i suoi dati. Nella demo, con il catalogo fermato, gli ordini rispondono ancora 201.

**Domanda 3.** In CatalogProductLookup.find, @Retryable ha includes = CatalogUnavailableException.class. Il catalogo risponde 404 per un prodotto inesistente. Che cosa succede?

- a. Gli ordini rispondono 503 Service Unavailable
- b. Nessun nuovo tentativo: il 404 diventa un Optional vuoto
- c. La richiesta resta appesa finché il prodotto non compare
- d. Gli ordini ritentano tre volte, perché ogni errore HTTP è temporaneo

Risposta: b. Corretto: solo connessione rifiutata, timeout o errore 500 diventano CatalogUnavailableException, ritentata e poi tradotta in 503.

**Domanda 4.** KafkaOrderEventPublisher pubblica sul topic orders.placed con kafka.send(TOPIC, String.valueOf(event.orderId()), event). Perché usiamo l'identificatore dell'ordine come chiave?

- a. Perché la chiave indica al consumatore quale classe Java usare per leggere il messaggio JSON
- b. Perché Kafka rifiuta i messaggi senza chiave
- c. Stesso ordine, stessa partizione: i messaggi restano in ordine
- d. Perché il servizio notifiche risponde agli ordini usando quella chiave

Risposta: c. Corretto: la chiave decide la partizione. Il produttore intanto non conosce i consumatori.

**Domanda 5.** Con il pattern outbox, Kafka è fermo e arriva un nuovo ordine. Che cosa succede?

- a. L'ordine resta in attesa di una transazione distribuita tra database e Kafka
- b. L'ordine viene rifiutato, perché l'evento non si può pubblicare
- c. L'ordine viene salvato e l'evento si perde
- d. 201: ordine ed evento salvati nella stessa transazione; il relay pubblica quando Kafka torna

Risposta: d. Corretto: il relay riprova finché non ci riesce, poi segna sent_at. Un evento può arrivare due volte, mai zero: i consumatori devono tollerare i doppioni.

**Domanda 6.** Catalogo e ordini contenevano lo stesso filtro che aggiunge l'intestazione X-Request-Id. Dopo l'introduzione del gateway, dove sta quella logica?

- a. Nel client, che deve generare l'identificativo prima di ogni chiamata
- b. In una libreria condivisa copiata in ogni servizio
- c. Nel gateway, una sola copia per entrambe le rotte (DRY)
- d. Ancora nei servizi, perché il gateway inoltra le richieste senza toccarle

Risposta: c. Corretto: nel gateway vanno gli aspetti comuni a ogni richiesta, come identificativi, sicurezza e limiti. Mai la logica di dominio.

**Domanda 7.** In order-service.yml, servito dal Config Server, l'indirizzo del catalogo diventa lb://catalog-service. Come lo usano gli ordini?

- a. Chiedono a Eureka dove si trova catalog-service
- b. Lo passano al gateway, che conosce tutte le porte
- c. Lo risolve il Config Server a ogni chiamata
- d. Lo trasformano in localhost:21050, scritto in un file di configurazione

Risposta: a. Corretto: lb indica il load balancer. Con due copie del catalogo, le userebbe a turno.

**Domanda 8.** Gli ordini devono leggere un prodotto dal catalogo, che richiede lo scope catalog.read. Come si presentano gli ordini?

- a. Con il token dell'utente arrivato dal gateway, che contiene sempre anche lo scope catalog.read
- b. Con un token proprio, ottenuto con client credentials
- c. Senza token: la rete interna è considerata fidata
- d. Con un segreto condiviso tra tutti i servizi

Risposta: b. Corretto: con @ClientRegistrationId sul client HTTP, Spring Security ottiene il token, lo riusa finché non scade e lo mette nell'intestazione Authorization.

**Domanda 9.** Nella saga a coreografia il catalogo ha riservato due monitor, poi il pagamento viene rifiutato. Che cosa succede?

- a. Una transazione distribuita annulla insieme ordine e riserva
- b. L'ordine resta PENDING per sempre, e la merce resta riservata
- c. Gli ordini pubblicano orders.cancelled e il catalogo rilascia la merce
- d. Gli ordini chiamano via HTTP il catalogo e modificano il suo magazzino

Risposta: c. Corretto: è la compensazione. Vive nel servizio che possiede i dati, e alla fine la disponibilità dei monitor torna a tre.

**Domanda 10.** Con Micrometer Tracing e il ponte OpenTelemetry, il trace id arriva al catalogo via HTTP, ma non alle notifiche via Kafka. Che cosa aggiunge la lezione?

- a. observation-enabled: true sul template Kafka degli ordini e sul listener delle notifiche
- b. sampling probability 0.1 al posto di 1.0
- c. Span scritti a mano in ogni metodo del listener
- d. Una nuova libreria nel pom delle notifiche

Risposta: a. Corretto: il template scrive il traceparent nel messaggio, e il listener apre il suo span come figlio. Jaeger mostra cinque span in una sola traccia.

## Quiz: verso la produzione

Verifica la pipeline CI con GitHub Actions, costi e benefici dell'immagine nativa e la revisione finale con SOLID, DRY, KISS e ArchUnit.

**Domanda 1.** Nel workflow ci.yml il passo Build and test esegue soltanto ./mvnw -B verify, invece di elencare compilazione, test e pacchetto come passi separati. Perché?

- a. Perché -B attiva la cache delle dipendenze di Maven
- b. Perché verify salta i test, così la pipeline è più veloce
- c. Il pom resta l'unica definizione della build (DRY)
- d. Perché GitHub Actions non sa eseguire più comandi Maven

Risposta: c. Corretto: il runner usa lo stesso comando che usiamo in locale. -B è la modalità batch, con un log pulito. Verify compila, esegue i test e crea il Jar.

**Domanda 2.** Il passo che carica la cartella dei rapporti di Surefire come artifact test-reports ha la condizione if: always(). Che cosa cambia?

- a. I rapporti diventano pubblici per sempre
- b. I rapporti si caricano anche quando i test falliscono
- c. I test vengono rieseguiti finché passano
- d. Il passo viene eseguito solo dopo un push sul ramo main, come la costruzione dell'immagine

Risposta: b. Corretto: senza always() il passo verrebbe saltato dopo un errore, e perderemmo i rapporti del job rosso.

**Domanda 3.** Nel workflow le azioni sono scritte come actions/checkout@&lt;hash del commit&gt; # v7, invece di actions/checkout@v7. Perché?

- a. Perché un'etichetta si può spostare su un altro commit, un hash no
- b. Perché l'hash è più corto da scrivere
- c. Perché GitHub non accetta più le etichette come v7
- d. Perché con l'hash il token del workflow può scrivere nel repository

Risposta: a. Corretto: la versione resta nel commento per chi legge, e Dependabot può proporre gli aggiornamenti in modo controllato.

**Domanda 4.** DemoCatalogLoader legge demo-products.csv dal classpath all'avvio. Sulla JVM funziona. Perché la lezione aggiunge un RuntimeHintsRegistrar che registra quella risorsa?

- a. Perché anche sulla JVM, senza registrazione, il file non viene trovato quando l'applicazione gira dal Jar
- b. Per rendere più veloce l'avvio sulla JVM
- c. Perché Spring Boot non sa leggere i file CSV
- d. L'immagine nativa è un mondo chiuso: le risorse lette a runtime vanno dichiarate

Risposta: d. Corretto: senza quella riga l'eseguibile partirebbe con il catalogo vuoto. Un test sulla JVM verifica l'hint senza compilare in nativo.

**Domanda 5.** Per quale servizio la lezione sconsiglia di passare all'immagine nativa?

- a. Tante istanze piccole in cui ogni megabyte di memoria conta
- b. Una funzione serverless che parte cento volte al giorno per pochi secondi
- c. Un job breve lanciato spesso da uno scheduler
- d. Un servizio che resta acceso per giorni sotto carico costante

Risposta: d. Corretto: lì la JVM va benissimo e, dopo il riscaldamento del JIT, spesso è più veloce. KISS: misuriamo e decidiamo con i numeri.

**Domanda 6.** ArchUnit fallisce su ProductStatsController, che ha un campo @Autowired ProductRepository e ricalcola le statistiche. Quale correzione fa la lezione?

- a. Creare un'interfaccia nuova davanti al repository
- b. Ricevere ProductService nel costruttore e delegare a service.stats()
- c. Aggiungere un'eccezione alle regole di ArchUnit per questa classe
- d. Spostare il campo nel costruttore, lasciando il repository nel controller

Risposta: b. Corretto: il servizio arriva in un campo final. Singola responsabilità, DRY e inversione delle dipendenze. Il controller traduce soltanto il risultato con CatalogStatsResponse.from.

**Domanda 7.** Dopo il refactoring di ProductStatsController, le regole di ArchUnit diventano verdi e il test dell'endpoint delle statistiche, che era verde, resta verde. Che cosa dimostra?

- a. Struttura cambiata, comportamento invariato: è un refactoring
- b. Che il test dell'endpoint era inutile e si può cancellare
- c. Che le regole di architettura girano solo in locale
- d. Che ArchUnit ha corretto il codice da solo

Risposta: a. Corretto: e da ora, se qualcuno inietta di nuovo un repository in un controller, la build fallisce da sola, in locale e nella pipeline.

## Quiz: progetto full-stack con Angular e Tailwind

Verifica SPA e API, TypeScript, Angular con signal e httpResource, routing, login con JWT, carrello, form con signal forms e il build di produzione.

**Domanda 1.** Che cosa cambia tra una pagina generata con Thymeleaf e una single page application dopo il primo caricamento?

- a. Il browser chiede al server ogni pagina in HTML completo
- b. Il browser chiede all'API solo dati JSON e Angular aggiorna la parte che cambia
- c. Il server genera l'HTML con Angular invece che con Thymeleaf
- d. Il database viene letto direttamente dal browser

Risposta: b. Corretto: Il browser scarica index.html con JavaScript e CSS una volta sola. Poi arrivano solo dati, e stato e navigazione diventano compito nostro.

**Domanda 2.** Per costruire l'interfaccia web dello Shop, che cosa si fa con il backend Spring Boot già pronto?

- a. Lo si riscrive in TypeScript, perché Angular lo richiede
- b. Lo si sposta dentro la cartella web, insieme ad Angular
- c. Resta com'è, nella cartella api, e il client Angular nasce in web
- d. Si sostituisce con file JSON statici letti dal client

Risposta: c. Corretto: L'API c'è già, completa e testata: ognuno dei due servizi ha la sua cartella e la sua porta.

**Domanda 3.** Perché per l'intestazione si aggiunge GET /api/me invece di far leggere al frontend il contenuto del token JWT?

- a. Il formato del token è affare del server: nome e ruoli si chiedono all'API
- b. Perché un token JWT non contiene mai il nome dell'utente
- c. Perché serve un backend for frontend separato per ogni schermata
- d. Perché un endpoint senza token è più sicuro di uno con il token

Risposta: a. Corretto: L'endpoint restituisce un DTO con i soli campi che servono allo schermo, username e roles.

**Domanda 4.** Perché la regola CORS dell'API permette una sola origine precisa, quella del server di sviluppo, e non un asterisco?

- a. Perché l'asterisco rallenta ogni risposta dell'API
- b. Perché senza CORS il browser blocca anche il server di sviluppo
- c. Perché il preflight OPTIONS funziona solo con le origini numeriche
- d. Permettiamo l'accesso al solo client che deve leggere le risposte, nessun altro sito

Risposta: d. Corretto: La pagina su 127.0.0.1:21131 e l'API su 21130 sono origini diverse: l'API dà il permesso solo a quella.

**Domanda 5.** Un oggetto TypeScript con tutti i campi dichiarati da interface Product, ma creato senza new e senza una classe Product, è valido?

- a. No, serve una classe che dichiari implements Product
- b. No, il compilatore rifiuta oggetti creati senza new
- c. Sì, perché conta la forma dell'oggetto e non il nome della classe
- d. Sì, ma solo se Node controlla i tipi durante l'esecuzione

Risposta: c. Corretto: L'interface descrive la forma. Durante l'esecuzione sparisce, perché i tipi servono all'editor e alla build.

**Domanda 6.** Quale traduzione tra Java e TypeScript è corretta secondo la lezione?

- a. enum diventa enum, e Node lo esegue senza problemi
- b. enum diventa un tipo unione di stringhe, Optional si usa con ?. e ??
- c. CompletableFuture diventa una lambda e join un ciclo
- d. record diventa una classe con il costruttore e il new

Risposta: b. Corretto: Sort = 'NAME' | 'PRICE' al posto dell'enum; ?. ricorda map di Optional e ?? ricorda orElse.

**Domanda 7.** Perché ng new si lancia con le opzioni scritte nel comando, per esempio --style tailwind e --ssr=false?

- a. Perché senza opzioni ng new non crea il progetto
- b. Perché le opzioni rendono il progetto più veloce a runtime
- c. Perché ng new accetta solo opzioni e mai domande
- d. Perché il risultato è sempre lo stesso, senza risposte da dare a mano

Risposta: d. Corretto: Foglio di stile, SSR e strumenti AI sono decisi dal comando. Zoneless, Vitest e nomi corti sono già predefiniti.

**Domanda 8.** Che cosa fa il proxy configurato in proxy.conf.json per il server di sviluppo?

- a. Inoltra /api/** all'API, così il browser parla con una sola origine
- b. Applica le regole CORS al posto di Spring
- c. Trasforma i file TypeScript in JavaScript per il browser
- d. Avvia l'API Spring Boot quando parte ng serve

Risposta: a. Corretto: Il browser chiede tutto alla porta del ng serve, che gira le richieste /api verso l'API. CORS non serve al web.

**Domanda 9.** In un componente Angular, come si legge e come si cambia un signal?

- a. Si legge come un campo, products, e si cambia con un assegnamento
- b. Si legge con get() e si cambia con push()
- c. Si legge con le parentesi, products(), e si cambia con set
- d. Si legge solo nel template e mai nella classe

Risposta: c. Corretto: Quando il valore cambia, Angular aggiorna soltanto i template che lo leggono.

**Domanda 10.** Perché la lezione dice che Angular oggi non ha più bisogno di zone.js?

- a. Perché zone.js è stato sostituito da un thread in background
- b. Perché si aggiorna quando cambia un signal del template o dopo un evento del template
- c. Perché la pagina si aggiorna una volta al secondo da sola
- d. Perché i componenti non possono più cambiare i dati

Risposta: b. Corretto: Zoneless è predefinito dalla 21, OnPush dalla 22. Non serve più controllare tutto dopo ogni evento o timer.

**Domanda 11.** In Tailwind, che cosa significa scrivere grid-cols-1 sm:grid-cols-2 lg:grid-cols-3?

- a. Una colonna a ogni larghezza, due da 640 px in su, tre da 1024 px in su
- b. Una colonna solo sul telefono e due solo sul tablet
- c. Tre colonne a ogni larghezza, perché l'ultima classe vince sempre
- d. Una griglia fissa di tre colonne che Tailwind ricalcola ogni secondo

Risposta: a. Corretto: Mobile first: la classe senza prefisso vale sempre, i prefissi si aggiungono da quella larghezza in su.

**Domanda 12.** Per avere un catalogo responsive in Tailwind, che cosa non serve?

- a. Le classi di utilità nel template
- b. I prefissi sm:, lg: e xl:
- c. Le dipendenze @tailwindcss/postcss e postcss
- d. Un tailwind.config.js e media query scritte a mano

Risposta: d. Corretto: I valori predefiniti e i prefissi bastano. Tailwind genera il CSS solo per le classi che usiamo.

**Domanda 13.** Che cosa restituisce HttpClient.get() e quando parte la richiesta?

- a. Restituisce i dati e la richiesta parte subito
- b. Restituisce un Observable pigro: parte solo quando qualcuno si iscrive
- c. Restituisce una Promise già risolta
- d. Restituisce un array di prodotti già tipizzato

Risposta: b. Corretto: Come uno Stream senza operazione terminale. firstValueFrom si iscrive e trasforma la prima risposta in una Promise.

**Domanda 14.** Che vantaggio dà httpResource rispetto al ProductService con firstValueFrom nel catalogo?

- a. È più veloce perché non usa HTTP
- b. Controlla a runtime che il JSON abbia i campi di Product
- c. Espone value, error e isLoading come signal, e la richiesta parte da sola
- d. Obbliga a scrivere sempre un interceptor

Risposta: c. Corretto: Il template può mostrare dati, errore o caricamento, senza servizio, costruttore o Promise non gestite.

**Domanda 15.** Perché aprendo direttamente /products/3 prima dell'introduzione del router lo Shop mostrava sempre il catalogo?

- a. Perché il server manda una pagina sola e l'app non aveva rotte: il tag del catalogo era scritto a mano
- b. Perché l'API non conosce l'indirizzo /products/3
- c. Perché Tailwind blocca gli indirizzi sconosciuti
- d. Perché il browser salva la pagina in cache

Risposta: a. Corretto: Il router sceglie il componente dall'indirizzo. Con zero rotte il catalogo compare sempre.

**Domanda 16.** Come arriva all'input id del dettaglio il valore di :id della rotta?

- a. Con ActivatedRoute e subscribe scritti a mano nel componente
- b. Con un parametro passato al costruttore del componente
- c. Con una variabile globale che il router imposta
- d. Con withComponentInputBinding, che lo porta nell'input con lo stesso nome

Risposta: d. Corretto: È una stringa, perché un indirizzo è testo. Se l'id cambia, httpResource rifà la richiesta da solo.

**Domanda 17.** Con loadComponent il dettaglio finisce in un chunk separato. Quando lo scarica il browser?

- a. Subito all'avvio, insieme a tutto il resto
- b. Alla prima visita della rotta
- c. Ogni volta che si cambia pagina
- d. Solo se l'utente è autenticato

Risposta: b. Corretto: Il catalogo resta eager, le altre pagine sono lazy. Vince la prima rotta che corrisponde, e ** va in fondo.

**Domanda 18.** Come fa il form di login a inviare nome e password, e che cosa tiene il frontend dopo il login?

- a. Li manda con un JSON nel corpo e conserva la password in localStorage
- b. Li manda in ogni richiesta, per verificare l'utente ogni volta
- c. Li manda una volta con Basic a POST /api/auth/token e conserva solo il JWT in un signal
- d. Li manda con Bearer e il server crea una sessione

Risposta: c. Corretto: Poi l'interceptor aggiunge Authorization con Bearer e il token. Il token sta in memoria.

**Domanda 19.** Che cosa fa l'interceptor funzionale dello Shop?

- a. Aggiunge Authorization con Bearer solo alle richieste a /api/ che non hanno già credenziali
- b. Aggiunge il token a ogni richiesta, anche verso siti esterni
- c. Modifica direttamente la richiesta originale
- d. Esegue il login quando il token è vuoto

Risposta: a. Corretto: La richiesta si clona perché non è modificabile. Così il token non parte verso altri siti e il login con Basic non viene toccato.

**Domanda 20.** Perché la pagina di login mostra "Wrong username or password" senza dire quale dei due era sbagliato?

- a. Perché l'API non sa quale dei due campi sia errato
- b. Perché il messaggio è più corto da tradurre
- c. Perché required impedisce di distinguere i due campi
- d. A chi prova a indovinare non si dà nessun indizio

Risposta: d. Corretto: Il 401 diventa un errore di tipo login, uguale in entrambi i casi.

**Domanda 21.** Dove tiene lo stato di pagina, ordine e filtri il catalogo, e perché?

- a. In un signal privato del componente, che è più semplice
- b. Nell'indirizzo, nei parametri della query, perché si ricarica uguale e si condivide con un link
- c. In localStorage, che sopravvive alla chiusura del browser
- d. In uno store globale per i filtri

Risposta: b. Corretto: Un evento cambia l'indirizzo con router.navigate, e httpResource rifà la richiesta da solo. Il tasto indietro funziona.

**Domanda 22.** A che cosa serve il timer di 300 ms nel campo di ricerca?

- a. A far ricaricare il catalogo ogni 300 ms
- b. A dare all'API il tempo di rispondere
- c. A cambiare l'indirizzo una volta sola, quando l'utente smette di scrivere
- d. A impedire che si scrivano più di 300 caratteri

Risposta: c. Corretto: A ogni tasto si cancella il timer e se ne avvia uno nuovo: bastano setTimeout e clearTimeout.

**Domanda 23.** Perché il CartService modifica le righe creando ogni volta un array nuovo con update?

- a. Perché un signal confronta i riferimenti: un array modificato sul posto non sarebbe notato
- b. Perché gli array di TypeScript non si possono modificare
- c. Perché così il carrello si salva da solo in localStorage
- d. Perché i computed funzionano solo con array vuoti

Risposta: a. Corretto: Per questo si usano spread, map e filter. Count e totalInCents sono computed e si ricalcolano da soli.

**Domanda 24.** Nel carrello e nell'ordine, chi decide il prezzo dei prodotti inviati con POST /api/orders?

- a. Il browser, che manda il prezzo di ogni riga
- b. Il CartService, che somma i decimali in euro
- c. L'utente, nel form del carrello
- d. L'API, che nel corpo riceve solo productId e quantity

Risposta: d. Corretto: Nomi e prezzi li prende dal suo catalogo. La risposta è 201 Created con l'ordine, tenuto in lastOrder.

**Domanda 25.** Il form admin ha validatori come required, maxLength e min. Che rapporto hanno con l'API?

- a. Sostituiscono i controlli dell'API, che quindi si possono togliere
- b. Rispecchiano le regole di Bean Validation per dare errori subito, ma l'API ricontrolla
- c. Funzionano solo se l'API è spenta
- d. Servono solo per il colore dei campi

Risposta: b. Corretto: Sono le stesse regole di ProductRequest, mostrate sotto i campi appena l'utente li tocca.

**Domanda 26.** Se l'API risponde 400 con un ProblemDetail con la mappa errors, che cosa fa il form?

- a. Mostra un solo messaggio generico in alto
- b. Cancella il modello e riparte da zero
- c. Riporta ogni messaggio sul suo campo, con un errore di tipo server
- d. Ignora la risposta e ricarica la pagina

Risposta: c. Corretto: Ogni voce di errors va al suo campo. Senza mappa, mostra il detail sul form.

**Domanda 27.** Che cosa garantisce l'admin guard della rotta del form?

- a. Che nessun altro possa creare prodotti
- b. Che il token JWT sia valido
- c. Che il form non si possa aprire senza compilare i campi
- d. Che la pagina sia nascosta a chi non è admin, ma l'API ricontrolla il ruolo

Risposta: d. Corretto: Senza login porta a /login, con login ma senza ADMIN porta a /. La sicurezza vera è nell'API.

**Domanda 28.** Perché in produzione nginx serve la build di Angular e inoltra /api/ all'API?

- a. Pagina e API stanno sulla stessa origine, quindi CORS non serve
- b. Perché l'API non può ascoltare su nessuna porta
- c. Perché nginx traduce TypeScript in JavaScript ad ogni richiesta
- d. Perché senza nginx il browser non può leggere il JSON

Risposta: a. Corretto: Nginx ha location /api/ con proxy_pass verso l'API, e try_files rimanda ogni altro percorso a index.html.

**Domanda 29.** Perché in nginx c'è try_files $uri $uri/ /index.html per le rotte dell'app?

- a. Per velocizzare le risposte dell'API
- b. Perché le rotte di Angular non sono file: ricaricando /products/3 va servito index.html
- c. Per bloccare i percorsi che non esistono
- d. Per scaricare i file dal database

Risposta: b. Corretto: Altrimenti nginx risponderebbe 404 a un indirizzo che esiste solo nel router.

**Domanda 30.** Un test del componente App con Vitest e TestBed controlla l'header e usa provideRouter([]). Perché?

- a. Per avviare un server vero con il router
- b. Perché Vitest richiede sempre un router
- c. Perché il template contiene routerLink, che ha bisogno del router
- d. Per salvare il test sul disco

Risposta: c. Corretto: Nei test provideRouter dà il router a RouterLink; poi await fixture.whenStable() e si controlla il testo.

**Domanda 31.** Nei test dei servizi che usano HttpClient, a che cosa serve HttpTestingController?

- a. A chiamare l'API vera durante il test
- b. A creare un database di prova
- c. A misurare i tempi di risposta dell'API
- d. A intercettare la richiesta, controllarla e rispondere con dati finti

Risposta: d. Corretto: Così il test è veloce e non dipende dall'API.
