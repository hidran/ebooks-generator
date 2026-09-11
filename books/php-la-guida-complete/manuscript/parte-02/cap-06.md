# 6. La sintassi di base

Con l'ambiente di sviluppo pronto, è il momento di scrivere le prime righe di PHP. In questo capitolo impariamo gli elementi fondamentali della sintassi: i tag che delimitano il codice PHP, il punto e virgola che chiude ogni istruzione, i commenti e il costrutto `echo`. Vedremo anche le due modalità con cui possiamo eseguire uno script PHP — dal terminale, come un normale programma, e attraverso un web server, come pagina web — e scopriremo che PHP si comporta in modo leggermente diverso nei due casi.

Nella seconda parte del capitolo ci concentriamo su **espressioni** e **letterali**: che cosa succede quando scriviamo `2 + 2;` in un file PHP, dove finisce il risultato e perché, senza un posto in cui conservarlo, quel risultato svanisce subito. È la premessa perfetta per il prossimo capitolo, dedicato a variabili, tipi e costanti.

## Organizzare il codice e creare il primo file

Prima di tutto, crea una cartella in cui raccogliere tutto il codice di questo libro, e al suo interno una sottocartella per ogni capitolo o argomento: così avrai il codice sempre organizzato e facile da ritrovare. Per questo capitolo useremo una cartella chiamata `intro`.

Apri la cartella con il tuo editor — negli esempi uso Visual Studio Code, ma va bene qualsiasi editor tu preferisca — e crea al suo interno un file chiamato `index.php`. VS Code riconosce subito l'estensione `.php` e mostra l'icona di PHP accanto al nome del file.

Come abbiamo visto nel Capitolo 5, conviene installare dalla vista delle estensioni (cerca "PHP") alcuni componenti che ci accompagneranno per tutto il libro:

- **PHP Debug**, per il debug del codice;
- **PHP Intelephense**, per l'autocompletamento intelligente;
- **PHP Extension Pack**, che raggruppa in un colpo solo quasi tutti i pacchetti utili;
- **PHP Server**, per avviare un web server "al volo" e provare subito il codice.

### Il percorso dell'eseguibile di PHP

Da VS Code puoi aprire il terminale integrato dal menu Terminal → New Terminal. La prima cosa da verificare quando entriamo in un terminale è che PHP sia disponibile. Su macOS e Linux puoi scoprire dove si trova l'eseguibile con:

```bash
which php
```

Codice completo: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-01.sh)


Il comando risponde con il percorso completo di PHP, ad esempio:

```text
/opt/homebrew/bin/php
```

Codice completo: [listing-02.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-02.txt)


Questo percorso ti serve anche in VS Code: se l'editor segnala che l'eseguibile di PHP non è installato, significa che non lo trova nelle impostazioni. Apri Settings, cerca "PHP" e vedrai le impostazioni delle varie estensioni PHP installate: nel campo dedicato al percorso dell'eseguibile (ad esempio `php.validate.executablePath`) inserisci il percorso restituito da `which php`. Imposta lo stesso percorso anche nelle opzioni dell'estensione PHP Server, così l'autocompletamento e la validazione del codice funzioneranno correttamente.

Attenzione se usi la sincronizzazione delle impostazioni di VS Code (quella collegata al tuo account GitHub): può capitare che l'editor erediti il percorso da un'altra macchina. A me, ad esempio, la sincronizzazione aveva riportato su Mac il percorso di Windows: su Windows con Laragon PHP si trova in una cartella come `C:\laragon\bin\php\php-8.x\php.exe`, mentre su questo Mac è in `/opt/homebrew/bin/php`. Il percorso corretto dipende sempre dal sistema che stai utilizzando.

## I tag di PHP

Ora possiamo cominciare a programmare. La prima cosa da fare in un file PHP è dichiarare che stiamo utilizzando PHP. Perché? Perché PHP, essendo un **linguaggio di scripting**, si può includere all'interno di una pagina HTML: quando il web server processa la pagina, tutto quello che si trova *al di fuori* dei tag di PHP viene lasciato così com'è, mentre viene interpretato solo ciò che sta *all'interno* dei tag.

Il **tag di apertura**, che dice al web server (o all'interprete di PHP) "da qui in poi c'è codice PHP", è:

```php
<?php
```

Codice completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-03.php)


Già con questo possiamo cominciare a scrivere PHP. In molti esempi in giro vedrai anche il **tag di chiusura** `?>`, ma è necessario solo se stiamo mescolando PHP con HTML. Se il file è puro PHP non c'è bisogno di chiuderlo — anzi, è meglio *non* chiuderlo: dopo un `?>` una riga vuota in fondo al file, che magari non vediamo nemmeno, verrebbe inviata in output e potrebbe causare errori difficili da individuare.

La prima cosa che possiamo fare per verificare che PHP funzioni è usare la funzione `phpinfo()`:

```php
<?php
phpinfo();
```

Codice completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-04.php)


Nota il **punto e virgola** alla fine: PHP ne ha bisogno per capire dove finisce ogni **istruzione** (in inglese *statement*). Attenzione: il punto e virgola non va messo "a ogni riga", ma alla fine di ogni istruzione. Più avanti, quando scriveremo ad esempio un `if` o una funzione, vedremo che un'istruzione può tranquillamente proseguire su più righe.

## Eseguire PHP dal terminale

Eseguiamo il nostro primo script. Dal terminale, entriamo nella cartella del progetto:

```bash
cd intro
ls -al
```

Codice completo: [listing-05.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-05.sh)


`ls -al` è un comando di Linux (e macOS) che mostra il contenuto di una cartella. Se sei su Windows hai due strade per avere gli stessi comandi:

- **WSL2** (Windows Subsystem for Linux), che è a tutti gli effetti un Linux dentro Windows;
- **Git Bash**: cercando "Git for Windows" puoi installare Git — comodo comunque, perché avrai anche uno strumento di versionamento del codice — e insieme ottieni la shell Bash. Git esiste per macOS, Windows e Linux, e su Windows l'installazione ti offre proprio quella console.

In VS Code, quando apri il terminale da Terminal → New Terminal, puoi cliccare sulla freccia accanto al pulsante `+` e scegliere tra le diverse console disponibili: su Windows vedrai il terminale classico, PowerShell, Git Bash e così via. Negli esempi uso Bash, ma il comando per eseguire PHP è identico su qualsiasi sistema — Linux, Windows o macOS: basta scrivere `php`, uno spazio e il nome del file.

```bash
php index.php
```

Codice completo: [listing-06.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-06.sh)


Funziona! L'output però è enorme: `phpinfo()` stampa tutte le informazioni sull'installazione di PHP — la versione, tutte le direttive di configurazione che si trovano nel file `php.ini` (lo vedremo più avanti), le librerie e le estensioni installate, e così via. È una funzione preziosa: se hai un servizio di hosting e vuoi verificare com'è configurato PHP senza passare dall'interfaccia del provider, ti basta caricare un file con questo codice e avrai tutte le informazioni.

## Eseguire PHP come pagina web

Se eseguiamo lo stesso `index.php` attraverso un web server, invece del testo grezzo vedremo una vera pagina web. Ci sono due modi comodi per farlo.

### L'estensione PHP Server

Con l'estensione PHP Server installata, fai clic destro sul file e scegli la voce di PHP Server per servire il progetto. Se la voce non compare nel menu contestuale, premi Shift+Cmd+P su Mac (Ctrl+Shift+P su Windows) e scrivi "server": scegli **PHP Server**, non Live Server — Live Server va bene solo per pagine HTML statiche. In alternativa, in alto a destra nell'editor c'è l'icona dell'estensione: un clic e il server parte.

PHP Server crea automaticamente un web server locale su una porta dedicata e apre il browser sulla nostra pagina `index.php`: questa volta `phpinfo()` appare come una pagina formattata, con tabelle e colori. Se facciamo clic destro nel browser e guardiamo il sorgente della pagina, vediamo i tag HTML che dal terminale non c'erano. Perché? Perché PHP *si accorge* di come viene eseguito: quando gira dalla riga di comando produce testo semplice, quando gira dietro un web server produce HTML.

### Il server integrato di PHP

Quello che fa VS Code con l'estensione possiamo farlo anche noi dalla riga di comando: PHP include di serie un web server di sviluppo. Basta avere PHP installato e lanciare `php -S` (con la S maiuscola) seguito da host e porta; con l'opzione `-t` indichiamo la cartella da servire. Se ad esempio ci troviamo nella cartella del progetto e vogliamo servire la sottocartella `intro`:

```bash
php -S localhost:8000 -t intro
```

Codice completo: [listing-07.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-07.sh)


Ora apriamo il browser su `http://localhost:8000` e vediamo la nostra pagina. Un consiglio pratico: se la porta è già occupata — a me è successo con un progetto Laravel in ascolto sulla 8000 — basta fermare il server con Ctrl+C e rilanciarlo su un'altra porta, ad esempio la 3000:

```bash
php -S localhost:3000 -t intro
```

Codice completo: [listing-08.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-08.sh)


### I commenti

Se non vogliamo che una riga di codice venga eseguita, possiamo **commentarla**. Un commento su una singola riga si scrive con la doppia barra `//`; esiste anche il commento a blocco, che si apre con `/*` e si chiude con `*/` e può estendersi su più righe — lo riprenderemo più avanti.

```php
<?php
// phpinfo();  questa riga ora è un commento e non viene eseguita

/*
  Questo è un commento
  su più righe.
*/
```

Codice completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-09.php)


Commentiamo la chiamata a `phpinfo()` e rieseguiamo il file dalla riga di comando: non esce più niente. Ricarichiamo la pagina nel browser: anche qui, pagina vuota. Il commento ha "spento" l'unica istruzione del file.

## Mescolare PHP e HTML

Facciamo un esperimento: aggiungiamo, *prima* del tag PHP, un normale tag HTML.

```php
<h1>Hello World</h1>
<?php
```

Codice completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-10.php)


Riavviamo il web server e ricarichiamo la pagina: il titolo appare. Come dicevamo, il web server serve l'HTML così com'è; solo ciò che sta dentro i tag PHP viene interpretato.

E se aggiungiamo del PHP? Impariamo subito il primo comando di PHP: `echo`, che scrive in output qualsiasi cosa gli passiamo. Apriamo le virgolette, scriviamo una stringa e chiudiamo con il punto e virgola, perché lì finisce l'istruzione:

```php
<h1>Hello World</h1>
<?php
echo "My name is Hidran";
```

Codice completo: [listing-11.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-11.php)


Ricarichiamo la pagina: con PHP abbiamo scritto questa stringa nella pagina web. E non è tutto: possiamo mettere dell'HTML *dentro* la stringa, ad esempio un tag `<h3>`:

```php
<h1>Hello World</h1>
<?php
echo "<h3>My name is Hidran</h3>";
```

Codice completo: [listing-12.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-12.php)


Che cosa sta succedendo esattamente? Stiamo inviando al browser una pagina web, e il browser interpreta ciò che riceve come HTML: ricaricando la pagina il testo appare formattato come un titolo di terzo livello, e guardando il sorgente vediamo che abbiamo *generato* dell'HTML con PHP.

Se ora lanciamo lo stesso file dal terminale, in un'altra scheda del terminale:

```bash
php intro/index.php
```

Codice completo: [listing-13.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-13.sh)


```text
<h1>Hello World</h1><h3>My name is Hidran</h3>
```

Codice completo: [listing-14.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-14.txt)


viene eseguita la stessa cosa, ma qui non vediamo una pagina web: non siamo in un browser, siamo nella riga di comando, quindi vediamo l'output HTML grezzo che PHP genera.

Infine, come anticipato, possiamo anche chiudere il tag PHP con `?>` e, dopo la chiusura, scrivere altro HTML:

```php
<h1>Hello World</h1>
<?php
echo "<h3>My name is Hidran</h3>";
?>
<p>PHP è super</p>
```

Codice completo: [listing-15.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-15.php)


Dal terminale vediamo anche il paragrafo nell'output; nel browser, senza bisogno di guardare il sorgente, il paragrafo appare in pagina. Ricorda però la regola: il tag di chiusura serve solo quando dopo c'è dell'HTML; in un file di puro PHP è meglio ometterlo.

### PHP oltre il web

Riassumendo: possiamo eseguire PHP dalla riga di comando, quindi PHP non è per forza legato al web. Uno script PHP potrebbe fare una chiamata FTP e scaricare un file da un server, copiare file da una cartella all'altra, creare cartelle nel file system, collegarsi a un database, chiamare un'API — qualsiasi cosa, senza che ci sia HTML di mezzo. E naturalmente PHP può anche girare dietro un web server, come quello integrato che abbiamo appena usato, per servire pagine web. PHP è, a tutti gli effetti, un linguaggio multiuso.

## Espressioni e letterali

Ora che sappiamo scrivere ed eseguire un file PHP, vediamo come PHP gestisce i dati che gli diamo. Questo ci servirà da introduzione alle variabili e alle costanti del prossimo capitolo: capiremo *perché* ci servono.

Creiamo una nuova cartella — la chiamo `variabili` — con dentro un nuovo `index.php`. Un'**espressione letterale** è un'espressione che scriviamo così com'è, come in matematica. Ad esempio:

```php
2 + 2;
```

Codice completo: [listing-16.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-16.php)


Ricordati il punto e virgola: con quello, questa è un'istruzione PHP corretta. Eseguiamo il file dal terminale — non c'è nulla di "web" qui, nessun tag HTML, quindi la riga di comando è perfetta per verificare se il file funziona. Se hai aggiunto PHP al PATH del sistema, per questa parte di base va bene qualunque versione di PHP:

```bash
php variabili/index.php
```

Codice completo: [listing-17.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-17.sh)


```text
2 + 2;
```

Codice completo: [listing-18.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-18.txt)


Sorpresa: vediamo letteralmente `2 + 2`. Che cosa sta succedendo? PHP, non trovando un tag di apertura dentro il file — anche se il file si chiama `index.php` — tratta tutto ciò che è fuori dai tag come testo: lo restituisce *as is*, così com'è, senza interpretarlo.

### Lo standard output e fwrite

Il posto in cui il terminale mostra i risultati si chiama, in programmazione, **standard output**. PHP mette a disposizione una costante — vedremo più avanti che cosa sono le costanti — chiamata `STDOUT`, che rappresenta proprio lo standard output: in questo caso, la nostra console. Attenzione: `STDOUT` esiste solo quando PHP viene eseguito dalla riga di comando, non quando gira dietro un web server.

Per scrivere sullo standard output possiamo usare la funzione `fwrite()`, che vuol dire appunto "scrivere" (*write*): è una funzione pensata per scrivere su un file, e lo standard output si comporta esattamente come un file verso cui mandiamo dei dati — `STDOUT` è infatti una **risorsa** di tipo file, un "canale" già aperto per noi. Studieremo queste funzioni più avanti; per ora ci serve solo per l'esperimento:

```php
<?php
fwrite(STDOUT, 2 + 2);
```

Codice completo: [listing-19.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-19.php)


Nota che questa volta abbiamo aperto il tag `<?php`: senza, come abbiamo appena visto, PHP non interpreterebbe nulla. Rilanciamo:

```text
4
```

Codice completo: [listing-20.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-20.txt)


Ecco il 4: questa volta PHP ha *valutato* l'espressione `2 + 2` e ne ha scritto il risultato sullo standard output. Al posto del numero potremmo scrivere una stringa — le vedremo in dettaglio più avanti; per ora sappi che una **stringa** si scrive tra apici singoli o virgolette doppie:

```php
<?php
fwrite(STDOUT, 'Hidran');
```

Codice completo: [listing-21.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-21.php)


E vediamo il nome in console. Ma proviamo a servire lo stesso file con il web server integrato:

```bash
php -S localhost:3000 -t variabili
```

Codice completo: [listing-22.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-22.sh)


Aprendo `http://localhost:3000` il risultato è un errore: la costante `STDOUT` non è definita. Come dicevamo, esiste solo quando PHP viene eseguito dalla riga di comando.

### Il costrutto echo

Per mandare l'output sia sul browser sia sulla console, la scelta giusta è il costrutto `echo` che abbiamo già incontrato: fa "uscire" qualunque risultato verso l'output corrente, ovunque PHP stia girando. Commentiamo la riga con `fwrite()` usando `//` e proviamo:

```php
<?php
// fwrite(STDOUT, 'Hidran');
2 + 2;
echo 'Hello World';
```

Codice completo: [listing-23.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-23.php)


```text
Hello World
```

Codice completo: [listing-24.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-24.txt)


Funziona sia dal terminale sia dal browser. Ma nota una cosa interessante: la riga `2 + 2;` non produce nulla. PHP la valuta — l'espressione viene davvero eseguita — ma del risultato non succede niente: non finisce nell'output e non viene messo in un'area di memoria che potremmo riutilizzare. Se vogliamo vederlo, dobbiamo passarlo a `echo`:

```php
<?php
echo 2 + 2;
echo 'Hello World';
```

Codice completo: [listing-25.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-25.php)


```text
4Hello World
```

Codice completo: [listing-26.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-26.txt)


Il 4 c'è, ma la stringa gli appare attaccata subito dopo: non c'è un a capo. Vedremo il perché quando parleremo delle stringhe; per ora basta sapere che in una stringa tra virgolette doppie la sequenza `\n` (backslash + n) rappresenta il carattere di a capo:

```php
<?php
echo 2 + 2;
echo "\n";
echo 'Hello World';
```

Codice completo: [listing-27.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-27.php)


```text
4
Hello World
```

Codice completo: [listing-28.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-28.txt)


### Perché ci servono le variabili

Quindi: se non usiamo `echo`, il risultato di un'espressione non lo vediamo. Ma c'è di più. Supponiamo che io voglia *conservare* il risultato di quell'operazione per inviarlo per email o salvarlo su un database: non potrei. Una volta che la riga è stata eseguita, quel risultato non esiste più.

Ed ecco che entrano in gioco le **variabili**, che ci permettono di immagazzinare questi risultati: una stringa, un numero, un record letto dal database — qualunque tipo di valore supportato da PHP può finire in una variabile. In PHP il nome di una variabile deve essere preceduto dal simbolo del dollaro `$` (vedremo il perché nel prossimo capitolo): è così che PHP capisce che si tratta di una variabile.

```php
<?php
$result = 2 + 2;
echo $result;
```

Codice completo: [listing-29.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-29.php)


```text
4
```

Codice completo: [listing-30.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-30.txt)


Attenzione al significato del segno `=`: non stiamo dicendo che qualcosa "è uguale a" due più due, come in matematica. In programmazione, e quindi in PHP, il segno uguale è un'**assegnazione**: "esegui l'operazione che c'è a destra e assegna il risultato alla variabile di sinistra". E quando usiamo la variabile, il dollaro è obbligatorio: se scrivessimo `echo result;` PHP penserebbe che `result` sia una costante.

Lo stesso vale per le stringhe. Se scrivo il mio nome tra apici, da solo su una riga:

```php
<?php
'Hidran';
```

Codice completo: [listing-31.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-31.php)


eseguo il codice e non vedo nulla: devo farne l'`echo`, oppure metterlo in una variabile per poterlo conservare:

```php
<?php
$name = 'Hidran';
```

Codice completo: [listing-32.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-32.php)


Da questo momento con `$name` posso fare quello che voglio: mandarla per email, scriverla nel file system. Ad esempio, con una funzione che studieremo più avanti — te la mostro solo come anteprima, non preoccuparti — posso dirle come si deve chiamare il file e quale contenuto scriverci:

```php
<?php
$name = 'Hidran';
file_put_contents('text.txt', $name);
```

Codice completo: [listing-33.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-6/it/parte-02/cap-06/listing-33.php)


Eseguiamo il codice e, guardando nella cartella, PHP ha creato il file `text.txt` con dentro il valore della nostra variabile. Tutte le funzioni per scrivere su file le vedremo a tempo debito (nel Capitolo 15): qui volevo solo mostrarti l'importanza delle variabili.

Nel prossimo capitolo vedremo come dichiarare una variabile, le convenzioni per i nomi e i diversi tipi di dato: le stringhe che abbiamo già intravisto, i numeri, i booleani, gli array, fino a classi e oggetti.

## In sintesi

- Il codice PHP vive tra il tag di apertura `<?php` e l'eventuale tag di chiusura `?>`: tutto ciò che sta fuori viene restituito così com'è. In un file di puro PHP il tag di chiusura va omesso.
- Ogni **istruzione** termina con un punto e virgola; il punto e virgola chiude l'istruzione, non la riga.
- `phpinfo()` mostra versione, configurazione (`php.ini`) ed estensioni dell'installazione di PHP: utile anche per ispezionare un hosting.
- Uno script PHP si esegue dal terminale con `php nomefile.php` oppure via web server: con l'estensione PHP Server di VS Code o con il server integrato `php -S localhost:porta -t cartella`. PHP adatta l'output al contesto in cui gira.
- I commenti si scrivono con `//` (riga singola) o `/* ... */` (blocco).
- `echo` scrive in output ovunque PHP stia girando; `STDOUT` e `fwrite()` funzionano solo dalla riga di comando.
- PHP valuta le espressioni come `2 + 2`, ma senza `echo` il risultato non si vede e senza una variabile va perduto: `$result = 2 + 2;` è un'**assegnazione**, che calcola la parte destra e la conserva nella variabile a sinistra.
- PHP non è solo web: dalla riga di comando può copiare file, collegarsi a database, chiamare API — è un linguaggio multiuso.
