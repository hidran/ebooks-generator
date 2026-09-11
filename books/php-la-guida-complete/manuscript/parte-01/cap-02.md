# 2. Installare PHP su Windows con Laragon

In questo capitolo prepariamo un ambiente di sviluppo PHP completo su Windows usando **Laragon**: installeremo il web server Apache, PHP e MySQL/MariaDB in un colpo solo, scriveremo ed eseguiremo il nostro primo file PHP sia dalla riga di comando sia nel browser, configureremo Visual Studio Code e Git Bash e impareremo a gestire più versioni di PHP e del database sulla stessa macchina. Alla fine avrai una postazione di lavoro identica, nella sostanza, a quella che uso io ogni giorno per sviluppare.

Perché proprio Laragon? Perché è un ambiente **portabile**: tutto ciò che installa vive dentro un'unica cartella, senza toccare i registri di sistema di Windows. Se un giorno non vorrai più usarlo, ti basterà cancellare quella cartella. E soprattutto rende banali due operazioni che con altri strumenti sono noiose: cambiare versione di PHP e creare **virtual host** locali per i tuoi progetti.

## Installare Laragon

Laragon è un ambiente di sviluppo per Windows che include tutto quello che ci occorre: nella versione **full** troviamo Apache 2.4, MySQL, memcached, la gestione dei log, npm e Git, tutto installato in una sola cartella. Ti consiglio di scaricare proprio la versione full: npm e Node ci possono servire per il frontend e anche per sviluppare nel backend, e avere tutto pronto da subito non costa nulla.

### Download e installazione

Vai sul sito di Laragon, clicca su **Download** e scarica *Laragon Full*. Una volta scaricato l'eseguibile, fai doppio click e accetta di installare l'applicazione. La procedura guidata ti chiede alcune cose:

1. **La lingua.** Puoi lasciare l'inglese di default o scegliere l'italiano.
2. **La cartella di installazione.** Per esempio `C:\laragon`; va bene qualsiasi cartella in cui il tuo utente abbia il permesso di scrittura.
3. **L'avvio automatico.** Puoi far partire Laragon all'avvio di Windows: comodo se lo userai spesso, altrimenti deseleziona l'opzione e lo lancerai manualmente.
4. **I virtual host automatici.** Lascia attiva l'opzione che crea i virtual host per i nostri siti: è una delle funzioni più utili di Laragon e la vedremo tra poco.
5. **Le voci del menu contestuale.** Puoi aggiungere al tasto destro di Windows le voci per aprire un file di testo con Notepad e per aprire il terminale in una cartella. Lascia tutto selezionato.

Clicca **Next** e poi **Install**, attendi qualche secondo e l'installazione è completata.

### Avviare i servizi

Cerca Laragon nel menu Start e avvialo (oppure, se hai scelto l'avvio automatico, lo trovi già attivo: clicca sulla freccina nell'area di notifica vicino all'orologio e vedrai la sua icona). Nella finestra principale clicca **Start All**: Laragon avvia tutti i servizi, e in particolare Apache sulla porta 80 e MySQL.

Attenzione: se la porta 80 è già occupata da un altro sistema, Apache non parte. Il caso tipico è avere già installato **XAMPP**: in tal caso apri il pannello di controllo di XAMPP e ferma Apache e MySQL prima di avviare Laragon (oppure continua pure con XAMPP, ma questo capitolo è dedicato a Laragon). In alternativa puoi cambiare le porte dalle preferenze, come vedremo subito.

### Le preferenze

Facendo click sull'icona a forma di ingranaggio si aprono le preferenze di Laragon. Vale la pena passarle in rassegna:

- **Avvio.** Puoi decidere se lanciare Laragon quando Windows si avvia, se farlo partire minimizzato e se avviare i servizi automaticamente.
- **Lingua.** Da qui puoi cambiare la lingua dell'interfaccia.
- **Document Root.** È la cartella radice dove metteremo i nostri progetti, di default `C:\laragon\www`. Se hai vecchi progetti in XAMPP, ti basta copiarne le cartelle da `htdocs` dentro `www`. Se preferisci tenere i progetti altrove (per esempio in `D:\projects`), puoi cambiare qui la document root: da quel momento il web server servirà i siti da quella cartella.
- **Data directory.** È la cartella dove finiscono i dati, per esempio i file dei database MySQL.
- **Virtual host automatici.** Quando creeremo un'applicazione in una sottocartella di `www`, potremo accedervi dal browser con `nomecartella.test`: Laragon aggiunge automaticamente il nome al file `hosts` di Windows e crea il virtual host in Apache.
- **Services & Ports.** Da qui cambi le porte dei servizi: se la porta 80 è occupata puoi usare per esempio la 8000 o la 4000. Puoi abilitare SSL, e vedere o modificare le porte di nginx, Redis e memcached se li usi. In questo libro useremo principalmente Apache e MySQL.
- **Mail catcher.** Quando usiamo la funzione `mail()` di PHP senza avere un server SMTP configurato, Laragon cattura l'invio e mostra una finestra con il contenuto dell'email: non parte nessuna email vera, ma possiamo verificare che il codice funzioni. C'è anche una sezione *Mail sender* dove impostare un account SMTP reale, per esempio quello di Gmail: io l'ho provato e non ha funzionato; se vuoi tentare fallo pure, ma nel Capitolo 38 vedremo come inviare email in modo affidabile usando servizi dedicati.

### La versione di PHP e le estensioni

Dal menu di Laragon (tasto destro sull'icona nell'area di notifica, oppure il pulsante **Menu** della finestra) trovi la voce **PHP**. Qui vedi la versione attiva — al momento della stesura Laragon include per esempio la 8.1.10 — e più avanti in questo capitolo vedremo come installarne un'altra: basterà copiare la cartella della nuova versione dentro `bin\php` di Laragon e selezionarla da questo stesso menu.

Sempre dal menu PHP puoi attivare **Xdebug**, il debugger di PHP, tramite la voce di installazione rapida. Per la maggior parte di questo libro non ne avremo bisogno, ma quando vorrai fare debugging vero troverai qui il punto di partenza.

Nella sottovoce **Extensions** trovi le estensioni di PHP che possiamo abilitare o disabilitare: per esempio `mbstring` e `pdo_mysql`, che useremo nei progetti, `gd` per gestire le immagini e `fileinfo` per avere informazioni sui file, già selezionate di default. Se ti serve un'estensione in più, per esempio `opcache`, basta spuntarla qui.

### Il terminale di Laragon (Cmder)

Un'ultima cosa importante: Laragon include un terminale, **Cmder**, che apri dal pulsante **Terminal**. Usa sempre questo terminale quando lavori con Laragon, per due motivi. Primo: supporta i comandi Linux (`ls`, `pwd` e così via), gli stessi che si usano su macOS e sui server di produzione. Secondo: dentro Cmder hai automaticamente accesso alla versione di PHP attiva in Laragon, qualunque essa sia. Con qualsiasi altro terminale, invece, dovremmo aggiungere PHP alla variabile d'ambiente `Path` di Windows — e aggiornarla ogni volta che cambiamo versione. Lo faremo comunque tra poco, perché è utile, ma ricordati la regola: in caso di dubbi, apri il terminale di Laragon e sarai sicuro di usare il PHP giusto.

Verifichiamo subito che tutto funzioni. Apri il terminale e digita:

```bash
php -v
```

Codice completo: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/it/parte-01/cap-02/listing-01.sh)


```text
PHP 8.1.10 (cli) (built: ...)
```

Codice completo: [listing-02.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/it/parte-01/cap-02/listing-02.txt)


PHP risponde con la sua versione: l'ambiente è pronto.

## Il primo file PHP

Ora che l'ambiente è installato, scriviamo il primo file PHP e impariamo i due modi fondamentali per eseguirlo: dalla riga di comando e attraverso il web server.

### Creare la cartella e il file

Nella finestra di Laragon clicca sul pulsante **Root**: si apre la cartella radice `www` che abbiamo predisposto per i nostri siti, dove trovi già un file `index.php` di default. Qui dentro crea una nuova cartella e chiamala `test`.

Entra nella cartella `test`, fai tasto destro, **Nuovo → Documento di testo**, e rinomina il file in `index.php`. Fai molta attenzione all'estensione: il file deve chiamarsi esattamente `index.php` e non `index.php.txt`, altrimenti PHP non lo interpreterebbe. Il nome non è casuale: `index.php` è il **file di default** che il web server carica ed esegue quando visitiamo una cartella senza indicare il nome di un file.

Apri il file con un editor qualsiasi (nel prossimo paragrafo installeremo Visual Studio Code, che sarà il nostro editor per tutto il libro) e scrivi:

```php
<?php
echo '<h1>Hello world</h1>';
?>
<h2>Mi chiamo Hidran</h2>
```

Codice completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/it/parte-01/cap-02/listing-03.php)


Analizziamo ogni riga, perché qui c'è già molta sostanza:

- `<?php` è il **tag di apertura** di PHP: indica al web server che da questo punto in poi c'è codice PHP da eseguire. `?>` è il tag di chiusura, e **non è obbligatorio** se il file contiene solo PHP e non lo mescoliamo con HTML.
- Tutto ciò che sta **fuori** dai tag PHP viene inviato così com'è, come HTML: è il caso del nostro `<h2>` dopo il tag di chiusura.
- `echo` è un costrutto di PHP che mostra un contenuto sulla console di uscita: se eseguiamo il file dalla riga di comando, l'output finisce nel terminale; se lo eseguiamo attraverso il web server, finisce nella pagina che il browser riceve. Dipende da come eseguiamo PHP.
- Quando vogliamo mostrare una **stringa** — cioè un pezzo di testo — la racchiudiamo tra apici. E dentro una stringa possiamo tranquillamente mettere dell'HTML, come il tag `<h1>` dell'esempio.
- In PHP ogni istruzione termina con il punto e virgola. Quando c'è un'unica riga prima del tag di chiusura il punto e virgola si può omettere, ma è buona abitudine metterlo sempre.

Tutta questa sintassi la studieremo in dettaglio nei prossimi capitoli: per ora ci serve solo a verificare che PHP funzioni. Salva il file.

### Eseguire il file dalla riga di comando

Apri il terminale di Laragon (pulsante **Terminal**, oppure tasto destro sull'icona e poi *Terminal*). Il terminale si apre nella cartella `www`: entriamo nella cartella del nostro progetto e controlliamo cosa contiene:

```bash
cd test
ls -la
```

Codice completo: [listing-04.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/it/parte-01/cap-02/listing-04.sh)


`ls -la` è un comando Linux — Cmder li supporta — che elenca i file della cartella: verifica che ci sia `index.php` e non `index.php.txt`. Ora eseguiamo il file passando il suo nome al comando `php`:

```bash
php index.php
```

Codice completo: [listing-05.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/it/parte-01/cap-02/listing-05.sh)


```text
<h1>Hello world</h1>
<h2>Mi chiamo Hidran</h2>
```

Codice completo: [listing-06.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/it/parte-01/cap-02/listing-06.txt)


L'output compare direttamente nella console. Nota che i tag HTML **non** vengono renderizzati: il terminale non è un browser, quindi mostra il testo esattamente come PHP lo produce.

Questa piccola prova ci dice una cosa importante: PHP si può usare **dalla riga di comando**, come Python o Bash, ma anche come **servizio del web server**. In quel secondo caso Apache carica PHP come modulo, esegue il codice e invia l'output di PHP al browser.

### Eseguire il file nel browser

Torniamo a Laragon e clicchiamo sul pulsante **Web**: si apre il browser predefinito puntato su `localhost`, cioè sulla cartella `www`. Per entrare nel nostro progetto aggiungiamo una barra e il nome della cartella:

```text
http://localhost/test
```

Codice completo: [listing-07.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/it/parte-01/cap-02/listing-07.txt)


Ecco la nostra pagina: "Hello world" come titolo grande e "Mi chiamo Hidran" come titolo più piccolo. Funziona perché nella cartella `test` c'è il file `index.php`, che viene eseguito di default quando non indichiamo alcun file; infatti anche scrivendo esplicitamente `http://localhost/test/index.php` otteniamo lo stesso risultato. Se fai tasto destro e scegli *Visualizza sorgente*, vedrai l'`<h1>` seguito dall'`<h2>`: esattamente lo stesso output che abbiamo visto nel terminale, solo che qui il browser lo renderizza.

Due precisazioni pratiche prima di proseguire:

- Per eseguire PHP **dalla riga di comando** il codice può stare in qualsiasi cartella del disco: se vuoi creare i tuoi script in `D:\projects` va benissimo.
- Per accedere alle cartelle **attraverso il web server** di Laragon (`localhost/nomecartella`), le cartelle devono invece stare dentro `www` — oppure devi cambiare la document root nelle impostazioni, come abbiamo visto, in modo che punti alla cartella dove tieni i siti.

E ricorda: il terminale di Laragon usa sempre il PHP attivo in Laragon. Se invece apri il prompt dei comandi di Windows o PowerShell e lanci `php -v`, non è detto che venga trovato il PHP di Laragon: potrebbe esserci un altro PHP nella `Path` di sistema, o nessuno. Sistemiamo subito questa cosa.

## Aggiungere PHP alla PATH di Windows

Aggiungere PHP alla variabile d'ambiente **Path** significa poter lanciare il comando `php` da qualunque terminale e da qualunque cartella, non solo da Cmder.

Prima individuiamo la cartella giusta. Se hai installato Laragon in `C:\laragon`, apri la cartella `C:\laragon\bin`: qui dentro trovi tutti i programmi inclusi — Apache, Cmder, Composer e gli altri software che aggiungeremo a Laragon. Nella sottocartella `php` ci sono tutte le versioni di PHP installate. Se ne hai più di una, controlla qual è quella attiva: tasto destro sull'icona di Laragon, **PHP → Version**, e vedi la versione selezionata. Apri la cartella di quella versione: contiene il file `php.exe`, l'eseguibile di PHP. Copia il percorso completo della cartella dalla barra degli indirizzi, per esempio:

```text
C:\laragon\bin\php\php-8.1.10-Win32-vs16-x64
```

Codice completo: [listing-08.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/it/parte-01/cap-02/listing-08.txt)


Ora aggiungiamolo alla `Path`. Su Windows 10 e 11:

1. Cerca "variabili" nel menu Start e apri **Modifica le variabili di ambiente relative al sistema**.
2. Clicca il pulsante **Variabili d'ambiente**.
3. Puoi aggiungere il percorso a livello di utente o a livello di sistema: seleziona la variabile **Path** (per esempio quella dell'utente), poi **Modifica**.
4. Clicca **Nuovo**, incolla il percorso della cartella dove si trova `php.exe` e conferma con **OK** su tutte le finestre.

A questo punto apri un terminale qualsiasi — cerca `cmd` e apri il prompt dei comandi — e lancia:

```bash
php -v
```

Codice completo: [listing-09.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/it/parte-01/cap-02/listing-09.sh)


Se ti risponde con la versione di PHP, il gioco è fatto: puoi lanciare PHP da qualunque cartella del tuo sistema. Puoi anche eseguire:

```bash
php -i
```

Codice completo: [listing-10.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/it/parte-01/cap-02/listing-10.sh)


che stampa tutte le informazioni di PHP: scorrendo l'output vedi la configurazione completa e cosa è installato.

Un'avvertenza dall'esperienza: la versione nella `Path` e quella attiva nel web server possono divergere. Se in Laragon attivi la 8.2 ma nella `Path` hai lasciato la cartella della 8.1, dal prompt dei comandi continuerai a usare la 8.1. Ogni volta che cambi versione, quindi, o aggiorni la `Path` (rimuovendo il vecchio percorso e incollando il nuovo) oppure usi il terminale di Laragon, che punta sempre alla versione attiva.

## Visual Studio Code e Git Bash

Ora che abbiamo un web server con PHP incluso e un terminale con i comandi Linux, ci serve un buon editor. In questo libro useremo **Visual Studio Code** (VS Code): è gratuito, leggero e con le estensioni giuste diventa un ottimo ambiente per PHP. Se in azienda usi già NetBeans o PhpStorm va benissimo: quello che vedremo qui è un'alternativa. Nel Capitolo 5 approfondiremo VS Code; qui facciamo l'installazione e la configurazione minima per lavorare.

### Installare VS Code e le estensioni per PHP

Vai sul sito di Visual Studio Code, clicca **Download**, scarica la versione per Windows ed esegui l'installazione. Al primo avvio compare una finestra di benvenuto: VS Code si può usare per PHP, Python, C#, qualsiasi linguaggio; per adattarlo a PHP dobbiamo installare alcune estensioni.

Clicca sull'icona **Extensions** nella barra laterale (oppure premi `Ctrl+Shift+X`) e cerca "PHP". Ti consiglio queste estensioni:

- **PHP Intelephense** — fornisce l'autocompletamento del codice PHP: mentre scrivi ti suggerisce funzioni, parametri e documentazione.
- **PHP Debug** — permette di usare Xdebug per fare il debug del codice.
- **PHP Extension Pack** — un pacchetto che include già sia PHP Debug sia Intelephense: installando questo le ottieni entrambe in un colpo solo.
- **PHP Server** — un'estensione molto comoda che esegue un server PHP senza aprire il terminale: basta fare tasto destro sul file e scegliere di servire il progetto come pagina web. È la stessa cosa che possiamo fare a mano dalla riga di comando, come vedremo tra poco.

Queste sono il minimo indispensabile per PHP. Poi, a seconda del framework che userai, potrai aggiungerne altre: se per esempio lavori con Laravel, cerca "Laravel" e trovi estensioni come *Laravel Extra Intellisense*, *Laravel Artisan* per i comandi di Artisan e gli snippet per i template Blade.

### Il terminale integrato

VS Code include un terminale integrato: apri il menu **View → Terminal** (oppure **Terminal → New Terminal**, o ancora la scorciatoia `Ctrl+`` con il backtick). Di default su Windows si apre **PowerShell**.

Durante tutto il libro userò comandi Linux. Perché? Perché PHP normalmente si usa su Linux: quando farai il deploy di un'applicazione PHP, anche su Azure o su Amazon, quasi sempre selezionerai una macchina Linux. Conviene quindi abituarsi da subito agli stessi comandi. Per le operazioni più semplici PowerShell basta: se digiti `pwd` ti dice in quale cartella ti trovi, e `ls` elenca i file, perché molti comandi di PowerShell sono simili a quelli di Bash. Ma per avere un vero terminale in stile Unix su Windows le strade sono due: installare **WSL** (Windows Subsystem for Linux) con una macchina Ubuntu e programmare direttamente lì dentro, oppure — molto più semplice — installare **Git Bash**.

Un paio di gesti utili sul terminale integrato: passando il mouse sopra un terminale aperto puoi chiuderlo cliccando sull'icona del cestino; con la freccia accanto al pulsante `+` scegli invece quale tipo di terminale aprire.

### Installare Git Bash

Git Bash arriva con **Git for Windows**: cerca "git bash" nel browser e apri il sito ufficiale, `git-scm.com/downloads`. Ci sono le versioni per macOS, Linux e Windows: clicca **Download for Windows** e scegli la versione a 64 bit (in alternativa puoi installarlo da PowerShell con `winget install`, o cliccare direttamente sul link "Click here to download the latest version").

Installandolo ottieni due cose insieme:

1. **Un terminale di tipo bash**, come se fossimo su Linux o su macOS, cioè su un sistema con base Unix: gli stessi comandi che impari per Linux li puoi usare qui, e non avrai nessuna difficoltà a eseguire i comandi bash in Windows.
2. **Git**, il sistema di controllo di versione: ti servirà per salvare le modifiche del codice e, per esempio, condividere i tuoi progetti su GitHub.

Esegui il file scaricato, permetti all'app di fare modifiche al sistema, clicca **Next** e poi **Install**. Al termine puoi lanciare subito Git Bash: si apre la console con il prompt che termina con il simbolo `$` (che indica appunto il prompt di bash: non va scritto nei comandi). Facciamo due prove:

```bash
pwd
ls -l
```

Codice completo: [listing-11.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/it/parte-01/cap-02/listing-11.sh)


`pwd` sta per *print working directory* e ti dice in quale cartella ti trovi; `ls -l` (*list*) elenca i file con le loro proprietà; con `cd nomecartella` entri in una cartella. Sono i comandi che useremo continuamente: per un programmatore PHP conoscere i comandi principali di bash è molto importante.

### Git Bash come terminale predefinito di VS Code

Ora impostiamo Git Bash come terminale predefinito di VS Code. Il metodo più rapido: apri il terminale, clicca sulla freccia accanto al `+` e scegli **Select Default Profile**; nell'elenco che compare — ci sono tutti i terminali disponibili: PowerShell, Git Bash, ed eventualmente Ubuntu se hai WSL — seleziona **Git Bash**. Da questo momento, ogni nuovo terminale (e ogni riavvio di VS Code) si aprirà direttamente in bash.

In alternativa puoi passare dalle impostazioni: dalla stessa freccia scegli *Configure Terminal Settings* e cerca il profilo del terminale per Windows, dove va indicato il percorso dell'eseguibile di bash, che di solito è:

```text
C:\Program Files\Git\bin\bash.exe
```

Codice completo: [listing-12.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/it/parte-01/cap-02/listing-12.txt)


Se non lo trovi lì, apri Esplora risorse, vai in `Program Files\Git`, individua l'eseguibile, e con tasto destro → *Proprietà* (o *Copia come percorso*) recuperi il percorso esatto da incollare. Chiudi e riapri VS Code, apri il terminale: si posiziona in Git Bash.

### Un progetto di prova con VS Code

Mettiamo tutto insieme con un piccolo test. In VS Code vai su **File → Open Folder** e crea una cartella per i tuoi progetti: per esempio, dentro *Documenti*, tasto destro → *New Folder* e chiamala `php`. Selezionala e conferma che ti fidi della cartella (*trust*). Ora crea un file: clicca sull'icona *New File* con il simbolo `+` (o **File → New File**) e chiamalo `index.php`. Come abbiamo visto, `index.php` è di solito il primo file che si crea in una cartella, perché è quello eseguito di default dal web server.

Scriviamo dentro:

```php
<?php
phpinfo();
```

Codice completo: [listing-13.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/it/parte-01/cap-02/listing-13.php)


`phpinfo()` è una funzione globale di PHP che stampa una pagina con tutte le informazioni sull'installazione. Nota il punto e virgola: ogni istruzione in PHP va terminata con `;`. E nota di nuovo il tag `<?php`: PHP si può usare *embedded* in una pagina HTML, cioè possiamo mescolare PHP e HTML nello stesso file, quindi l'unico modo per dire al parser dove inizia il codice PHP è aprire questo tag.

Salva il file e fai tasto destro nell'area dell'editor: grazie all'estensione PHP Server compare la voce **PHP Server: Serve project**. Selezionala: si apre automaticamente il browser su `localhost` alla porta 3000, con `index.php` eseguito. Vediamo la pagina di `phpinfo()` con la versione di PHP — nel mio caso la 8.3.12 — e tutta la configurazione.

Ora la stessa cosa dalla riga di comando. Apri il terminale integrato: si apre già nella cartella del progetto. Verifichiamo che PHP sia nella `Path` e poi eseguiamo il file:

```bash
php -v
php index.php
```

Codice completo: [listing-14.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/it/parte-01/cap-02/listing-14.sh)


Il primo comando mostra la versione (se risponde, significa che possiamo eseguire PHP da qualsiasi cartella); il secondo esegue il file e riversa nel terminale tutto l'HTML prodotto da `phpinfo()`.

Facciamo una prova più chiara con un secondo file. Crea `test.php`:

```php
<?php
echo 2 + 2;
```

Codice completo: [listing-15.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/it/parte-01/cap-02/listing-15.php)


Nel terminale digita `clear` per pulire lo schermo, poi:

```bash
php test.php
```

Codice completo: [listing-16.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/it/parte-01/cap-02/listing-16.sh)


```text
4
```

Codice completo: [listing-17.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/it/parte-01/cap-02/listing-17.txt)


Compare `4`, perché `echo` scrive l'output là dove PHP viene eseguito: sul terminale se lanciamo PHP dalla riga di comando, in una pagina web se passa attraverso un web server.

E a proposito di web server: PHP ne ha uno **integrato**, che possiamo lanciare senza estensioni e senza Apache. La sintassi è `php -S host:porta`:

```bash
php -S localhost:4000 index.php
```

Codice completo: [listing-18.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/it/parte-01/cap-02/listing-18.sh)


`-S` indica che vogliamo avviare un server; `localhost` è l'host (siamo sul nostro computer); dopo i due punti c'è la porta su cui vogliamo servire la pagina, per esempio la 4000; infine il file da servire. Fai `Ctrl+click` sull'URL mostrato nel terminale (o copialo nel browser): funziona esattamente come il web server dell'estensione PHP Server. Attenzione invece ad aprire il file direttamente da Esplora risorse nel browser: non funzionerebbe, perché il file verrebbe solo letto e non eseguito da PHP.

Verifichiamo infine l'autocompletamento di Intelephense. Sostituisci il contenuto di `index.php` con una prova sulle stringhe: appena digiti `str` compare l'elenco delle funzioni che iniziano così, tra cui `strpos()`. Selezionandola, VS Code ci mostra la firma: il primo parametro è la stringa in cui cercare, il secondo è cosa stiamo cercando; la funzione ritorna la **posizione** in cui si trova la sottostringa.

```php
<?php
echo strpos('Imparo PHP', 'PHP');
?>
<h2>Test in PHP</h2>
```

Codice completo: [listing-19.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/it/parte-01/cap-02/listing-19.php)


Ricarica la pagina del web server (o riesegui `php index.php` nel terminale): l'output è `7`. Possiamo contare: ricorda che **le posizioni cominciano da zero** — zero, uno, due, tre, quattro, cinque, sei, sette — e infatti la documentazione lo dice esplicitamente: *string position starts at 0, and not 1*. La funzione ritorna la posizione in cui si trova ciò che cerchiamo, relativa all'inizio della stringa.

Nota anche il tag `<h2>` fuori dal blocco PHP: nel browser "Test in PHP" viene renderizzato, e guardando il sorgente della pagina lo vediamo scritto esattamente come nel file. PHP interpreta solo la parte racchiusa nei suoi tag: il resto lo invia così com'è.

### Sincronizzare le impostazioni

Un ultimo consiglio su VS Code: nelle preferenze puoi attivare la sincronizzazione delle impostazioni facendo l'accesso con un account GitHub o Microsoft. Se non hai un account GitHub, ti consiglio di crearlo: oltre a servirti per condividere codice, ti permette di sincronizzare impostazioni ed estensioni, così quando userai VS Code su un altro computer ritroverai tutto l'ambiente configurato. VS Code offre molto altro — estensioni per i database, per le chiamate alle REST API, per Docker — e le vedremo quando serviranno; intanto prendi confidenza con l'editor: apri file, salva, prova le impostazioni.

## Installare una nuova versione di PHP e creare virtual host con Apache

Una delle grandi comodità di Laragon è poter tenere più versioni di PHP fianco a fianco e passare dall'una all'altra in un click. Vediamo come installare una nuova versione — e già che ci siamo, scopriamo come Laragon crea i virtual host di Apache per i nostri progetti.

Prima, due strumenti utili dal menu di Laragon. Sotto **Apache** trovi il file di configurazione del web server e i comandi per fermarlo e riavviarlo. Sotto **PHP**, oltre alle estensioni che abbiamo già visto, c'è l'accesso rapido al file `php.ini` con tutte le impostazioni di PHP: se per esempio cerchi `display_errors` lo trovi attivo, ed è giusto così — quando sviluppiamo va bene che gli errori di PHP vengano mostrati, perché siamo in sviluppo e non in produzione.

### Scaricare una nuova versione di PHP

Supponiamo di voler installare PHP 8.2 (al momento della stesura è la più recente; se quando leggi c'è una versione più nuova, la procedura è identica). Vai sul sito di PHP, `php.net`, e segui il link **Windows Downloads**: vedrai le diverse versioni disponibili. Per ciascuna ci sono più varianti, e devi scegliere:

- **L'architettura.** Verifica la versione del tuo Windows: normalmente è `vs16 x64`, cioè a 64 bit.
- **Thread Safe o Non Thread Safe.** Per lo sviluppo non fa differenza: possiamo prendere la **Non Thread Safe** (NTS).

Scarica il file zip. Nella cartella dei download fai tasto destro → **Estrai tutto** e indica la cartella dove estrarre (se vuoi, puoi installare il programma **7-Zip**, che è più veloce dell'estrazione integrata di Windows, ma il risultato è lo stesso). Ottieni una cartella decompressa con dentro PHP: copiala e incollala dentro la cartella delle versioni PHP di Laragon:

```text
C:\laragon\bin\php\
```

Codice completo: [listing-20.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/it/parte-01/cap-02/listing-20.txt)


La stessa identica procedura vale se volessimo installare una nuova versione di Apache o di MySQL: si scarica lo zip, si estrae e si copia la cartella nella rispettiva sottocartella di `C:\laragon\bin`.

### Attivare la nuova versione

Torna su Laragon: tasto destro sull'icona → **PHP → Version** e vedrai elencata anche la 8.2, semplicemente perché ne abbiamo messo la cartella al posto giusto. Selezionala per attivarla.

Come verifichiamo che siamo davvero sulla 8.2? Dal menu PHP la versione risulta selezionata, ma se clicchiamo su **Web** e guardiamo la pagina principale di Laragon, l'informazione su PHP dice ancora 8.1. Perché? Perché abbiamo attivato la nuova versione, ma Apache non l'ha ancora presa: dobbiamo riavviarlo. Tasto destro → **Apache → Reload** (o *Restart*), poi ricarica la pagina: ora compare la 8.2, e cliccando sul link di info vediamo tutta la configurazione della nuova versione.

Due promemoria importanti quando cambi versione:

1. **Le estensioni vanno riattivate.** Ogni versione di PHP ha il suo `php.ini`: dopo il cambio, torna in **PHP → Extensions** e attiva di nuovo le estensioni che ti servono (quelle di default ci sono già, ma tutto ciò che avevi aggiunto va riabilitato).
2. **La PATH va aggiornata.** Apri il terminale di Laragon e lancia `php -v`: vedrai la 8.2, perché il terminale di Laragon punta sempre alla versione attiva. Ma se apri il normale prompt dei comandi di Windows e lanci lo stesso `php -v`, ti darà ancora la 8.1: è quella che c'è nella `Path`. Per avere la 8.2 in qualsiasi terminale, torna nelle variabili d'ambiente come abbiamo fatto la prima volta: cerca "variabili d'ambiente", apri **Variabili d'ambiente → Path → Modifica**, rimuovi il vecchio percorso di PHP e incolla quello della nuova cartella, poi conferma con **OK** su tutte le finestre. Apri un **nuovo** terminale (quelli già aperti conservano le vecchie impostazioni) e `php -v` mostrerà la 8.2.

### I virtual host automatici di Apache

Ricordi la cartella `test` creata sotto `www`? Laragon le ha già dedicato un **virtual host** di Apache, automaticamente. Andiamo a vederlo: dal menu, sotto **Apache**, trovi la voce con i siti abilitati (`sites-enabled`), e lì c'è un file di configurazione creato per `test`. Aprendolo vedi la direttiva `VirtualHost` con la **document root** che punta a `C:/laragon/www/test`, il **server name** impostato a `test.test`, e anche la sezione con i certificati, se vogliamo collegarci via SSL.

Che cosa significa in pratica? Che se apriamo un tab del browser e scriviamo:

```text
http://test.test
```

Codice completo: [listing-21.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/it/parte-01/cap-02/listing-21.txt)


vediamo la nostra cartella con il file `index.php` eseguito — la stessa cosa che succede visitando `localhost/test`, perché la cartella `test` sta sotto la radice di `localhost`. Il vantaggio è poter dare ai nostri siti locali un nome vero e proprio: il nome della cartella con l'estensione `.test`, un dominio fittizio che il browser non andrà a cercare su internet ma risolverà in locale. Ogni volta che creeremo una nuova cartella sotto `www`, Laragon creerà automaticamente il virtual host corrispondente.

Come fa il browser a sapere che `test.test` è locale? Grazie al file `hosts` di Windows. Apriamo:

```text
C:\Windows\System32\drivers\etc\hosts
```

Codice completo: [listing-22.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/it/parte-01/cap-02/listing-22.txt)


In questo file sono definiti i nomi risolti localmente: c'è `127.0.0.1 localhost` — l'IP 127.0.0.1 è appunto quello di localhost — e Laragon vi ha aggiunto la riga per `test.test`. Quando visitiamo quel nome, Windows lo risolve sull'IP locale e Apache ci serve la cartella corrispondente.

Se `test.test` non funziona, quasi sempre significa che Laragon non ha i diritti di amministratore per scrivere dentro `System32` e aggiornare il file `hosts`. In quel caso puoi fare a mano quello che Laragon fa in automatico: apri il file `hosts` come amministratore e aggiungi la riga:

```text
127.0.0.1 test.test
```

Codice completo: [listing-23.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/it/parte-01/cap-02/listing-23.txt)


Se vuoi definire più siti sulla stessa riga, separa i nomi con uno spazio. Ma normalmente non serve: Laragon fa tutto da solo.

## Installare MySQL o MariaDB e usare HeidiSQL

Chiudiamo il capitolo con il database. **MariaDB** è il fork completamente open source di MySQL, compatibile con esso: per i nostri scopi i due sono intercambiabili, e ti mostro come installare l'ultima versione dell'uno o dell'altro. Per questo libro va bene qualsiasi versione di MySQL dalla 8 in su (approfondiremo MySQL nel Capitolo 18).

### Installare una nuova versione del database

Laragon arriva già con una versione di MySQL: dal menu, sotto **MySQL → Version**, puoi vedere quella inclusa, per esempio la 8.0.30. Al momento della registrazione l'ultima versione di MySQL è la 8.4, ma attenzione: quella versione **non funziona con Laragon**. Nessun problema: installiamo l'ultima MariaDB, con la stessa identica procedura che useresti per una versione di MySQL compatibile.

1. Cerca MariaDB nel browser e vai nella pagina di **download** del sito ufficiale.
2. Scegli la versione: al momento la 11.3.2, o comunque la versione stabile disponibile quando leggerai queste pagine.
3. Come sistema operativo seleziona Windows con architettura `x86_64`.
4. Come tipo di pacchetto **non** scegliere l'installer (quello installa MariaDB direttamente nel sistema): per usarlo con Laragon seleziona lo **ZIP file** e clicca download.
5. Quando il file è nella cartella dei download, spacchettalo: con 7-Zip scegli *Extract* e indica come destinazione la cartella `C:\laragon\bin\mysql` (o l'equivalente, se hai installato Laragon altrove). In alternativa estrai lo zip e copia la cartella decompressa dentro `C:\laragon\bin\mysql`.

Aprendo `C:\laragon\bin\mysql` vedrai le diverse versioni di MySQL o MariaDB una accanto all'altra, ognuna con la sua sottocartella `bin`; Laragon crea automaticamente anche il file `my.ini` con la configurazione di default.

Ora attiviamo la nuova versione: menu → **MySQL** (la voce si chiamerà *MariaDB* una volta selezionata una versione MariaDB) → **Version**, seleziona la versione appena copiata e poi clicca **Start All** per avviare il servizio. Se ti serve cambiare la porta del database, la trovi nelle preferenze sotto *Services & Ports*.

### HeidiSQL: creare un database e una tabella

Per lavorare con il database ci serve un client. Laragon include **HeidiSQL**: clicca sul pulsante **Database** e HeidiSQL si apre con una sessione già configurata — utente `root`, nessuna password di default — quindi basta cliccare **Open** per collegarsi.

Creiamo il nostro primo database: tasto destro nel pannello di sinistra → **Create new → Database**. Diamogli il nome `test` e come *collation* scegliamo `utf8mb4_general_ci`: così supportiamo i caratteri di tutte le lingue. Il database `test` compare nell'elenco.

Ora creiamo una tabella: tasto destro sul database → **Create new → Table** e chiamiamola `test_table`. Con il pulsante **Add** aggiungiamo le colonne una alla volta:

- **`name`** — tipo di dato `VARCHAR` (doppio click sulla cella del tipo per selezionarlo) con lunghezza `500`. Nella colonna *Allow NULL* decidiamo se, inserendo un record, il nome possa restare vuoto: diciamo di no, quindi `NOT NULL`.
- **`age`** — per l'età scegliamo il tipo giusto: un `TINYINT`, che da *signed* va da -128 a 127 e da *unsigned* va da 0 a 255. Un'età non è mai negativa, quindi spuntiamo **Unsigned**; e permettiamo che il campo resti vuoto, quindi *Allow NULL* sì.
- **`salary`** — per un salario ci serve un valore reale: selezioniamo `DECIMAL` con precisione 20, di cui 6 decimali.
- **`id`** — la colonna identificativa: tipo `INT`, **Unsigned** (sarà un contatore, mai negativo), `NOT NULL`. Su questa colonna facciamo tasto destro → **Create new index → PRIMARY**: la impostiamo cioè come **chiave primaria**, il che significa che identifica univocamente un record nella nostra tabella. Infine, nella cella del valore di default, scegliamo **AUTO_INCREMENT**: il valore si incrementa automaticamente a ogni inserimento, così non dovremo mai inserire l'ID a mano.

Clicca **Save** e la tabella è creata. Nella scheda della definizione HeidiSQL mostra anche il codice SQL corrispondente, che è l'equivalente di:

```sql
CREATE TABLE test_table (
  name   VARCHAR(500) NOT NULL,
  age    TINYINT UNSIGNED NULL,
  salary DECIMAL(20,6) NULL,
  id     INT UNSIGNED NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (id)
);
```

Codice completo: [listing-24.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/it/parte-01/cap-02/listing-24.sql)


Con il tasto destro sulla tabella hai le operazioni principali: *Edit* per modificarne la struttura, *Drop* per eliminarla (o svuotarla di tutti i record), l'esportazione dei dati, eccetera.

### Inserire dati ed eseguire query

Passiamo alla scheda **Data** della tabella: qui possiamo inserire i dati. Clicca sul segno `+` per aggiungere una riga e compila i campi: come `name` mettiamo per esempio `hidran`, e come `salary`… mettiamoci un bel salario di 100.000, magari. Nota che l'`id` viene inserito automaticamente con il valore `1`, grazie all'auto increment. Puoi salvare con l'apposita icona, ma i dati vengono salvati automaticamente anche quando esci dalla riga.

Ora la scheda **Query**, dove possiamo scrivere ed eseguire query SQL. Una select:

```sql
SELECT * FROM test_table;
```

Codice completo: [listing-25.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/it/parte-01/cap-02/listing-25.sql)


Clicca l'icona di esecuzione e vedi il record selezionato. Proviamo un update:

```sql
UPDATE test_table SET name = 'Hidran Arias' WHERE id = 1;
```

Codice completo: [listing-26.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/it/parte-01/cap-02/listing-26.sql)


Eseguiamo, torniamo nella scheda *Data* e clicchiamo l'icona di **refresh**: il nome ora è "Hidran Arias". Questa è solo una panoramica di quello che possiamo fare con HeidiSQL; a questo server puoi comunque collegarti con qualsiasi altro client — per esempio **DBeaver**, che trovi facilmente cercandolo e scaricandolo dal suo sito.

### Il client mysql dalla riga di comando

Al database possiamo collegarci certamente anche dalla riga di comando. Il client `mysql` si trova nella cartella `bin` della versione installata, per esempio `C:\laragon\bin\mysql\<versione>\bin`: apri quella cartella, fai tasto destro → *Apri nel terminale* e collegati con:

```bash
mysql -u root
```

Codice completo: [listing-27.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/it/parte-01/cap-02/listing-27.sh)


Funziona però solo se sei dentro quella cartella `bin`; per usare `mysql` da qualsiasi posizione dobbiamo — come per PHP — aggiungerlo alle variabili d'ambiente: copia il percorso della cartella `bin`, cerca "variabili d'ambiente", apri **Variabili d'ambiente**, seleziona **Path → Modifica → Nuovo** e incolla il percorso (puoi farlo a livello utente o di sistema). Chiudi e riapri il terminale, e da qualunque cartella:

```bash
mysql -u root -p
```

Codice completo: [listing-28.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/it/parte-01/cap-02/listing-28.sh)


`-u root` indica l'utente, `-p` chiede la password: lasciala vuota e premi Invio, perché di default non c'è nessuna password. Una volta dentro possiamo esplorare il server — ricordando di terminare ogni comando con il punto e virgola:

```sql
SHOW DATABASES;
USE test;
SHOW TABLES;
SELECT * FROM test_table;
```

Codice completo: [listing-29.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-2/it/parte-01/cap-02/listing-29.sql)


`SHOW DATABASES` elenca i database e tra questi vediamo `test`; `USE test` lo seleziona; `SHOW TABLES` mostra le tabelle, tra cui la nostra `test_table`; e la `SELECT` ci restituisce i dati inseriti. Interagire con MySQL dalla riga di comando è un pochino più impegnativo, perché dobbiamo fare attenzione ai comandi che scriviamo; nella pratica puoi usare indifferentemente la riga di comando, HeidiSQL o qualsiasi altro client tu abbia installato.

## In sintesi

- **Laragon** è un ambiente di sviluppo portabile per Windows: Apache, PHP, MySQL, npm e Git in una sola cartella, senza toccare i registri di sistema; per disinstallarlo basta cancellare la cartella.
- I progetti serviti dal web server vivono sotto la **document root** `www`; con **Start All** avvii i servizi, e se la porta 80 è occupata (per esempio da XAMPP) puoi cambiarla o fermare l'altro ambiente.
- Un file PHP inizia con il tag `<?php`; ciò che sta fuori dai tag viene inviato come HTML. `echo` scrive l'output sul terminale o nella pagina web, a seconda di come esegui PHP: `php file.php` dalla riga di comando, oppure tramite Apache visitando `localhost/cartella` (dove `index.php` è il file di default).
- Aggiungendo la cartella di `php.exe` alla variabile d'ambiente **Path** puoi lanciare `php` da qualsiasi terminale; il terminale di Laragon (Cmder) punta invece sempre alla versione attiva.
- **VS Code** con le estensioni *PHP Intelephense*, *PHP Debug* e *PHP Server* è un ottimo editor per PHP; **Git Bash** ti dà Git e un terminale bash in stile Linux, impostabile come predefinito in VS Code. Con `php -S localhost:porta` avvii il web server integrato di PHP.
- Per installare una **nuova versione di PHP** basta scaricare lo zip (x64, Non Thread Safe) da php.net, estrarlo in `C:\laragon\bin\php` e attivarlo dal menu; poi ricordati di riavviare Apache, riattivare le estensioni e aggiornare la `Path`.
- Per ogni cartella sotto `www` Laragon crea automaticamente un **virtual host** Apache (`nomecartella.test`) e la voce corrispondente nel file `hosts` di Windows; se non ha i permessi, puoi aggiungere la riga `127.0.0.1 nome.test` a mano.
- Nuove versioni di **MySQL/MariaDB** si installano copiando lo zip estratto in `C:\laragon\bin\mysql` e selezionandole dal menu; con **HeidiSQL** crei database, tabelle (colonne, tipi, chiave primaria, auto increment) ed esegui query, mentre il client `mysql` fa lo stesso dalla riga di comando.
