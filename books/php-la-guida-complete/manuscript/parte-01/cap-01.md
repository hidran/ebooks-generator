# 1. Introduzione a PHP

Benvenuto. In questo capitolo faremo conoscenza con PHP: da dove viene, come si è evoluto e perché, a distanza di decenni dalla sua nascita, è ancora uno dei linguaggi più usati al mondo per costruire il web. Un minimo di storia serve anche a sfatare un pregiudizio: alcune persone ritengono che PHP non sia un "vero" linguaggio di programmazione rispetto a Java o C#. Di solito sono persone che conoscono il PHP di venti anni fa, non il PHP di oggi.

Nella seconda parte del capitolo vedremo invece una panoramica completa di ciò che questo libro copre, parte per parte, e dei due progetti pratici che costruiremo insieme: uno **User Management System** completo e una piattaforma di blogging basata sul pattern **MVC**.

## Un po' di storia: da script personale a linguaggio del web

PHP non è nato come un linguaggio di programmazione. È stato creato da **Rasmus Lerdorf**, un danese che ho avuto la possibilità di conoscere di persona nel 2014, al PHP Day di Verona. Ci raccontava di aver creato questo linguaggio di scripting, chiamato PHP — all'epoca l'acronimo stava per *Personal Home Page* — per un'esigenza molto concreta: processare i **form** delle pagine HTML. Il meccanismo è quello che useremo per tutto il libro: abbiamo un form, l'utente lo compila e i dati vengono inviati al server. Lerdorf scrisse in C una serie di script da richiamare direttamente dalle pagine HTML, in modo da elaborare quei dati sul lato server, e per la sintassi prese in prestito elementi da C, C++ e Perl.

Aveva creato quegli script per sé, per uso personale. Ma il linguaggio piacque, altri sviluppatori iniziarono ad aggiungere nuove funzionalità e PHP divenne un progetto **open source**. A quel punto entrarono in scena **Zeev Suraski** e **Andi Gutmans**, che riscrissero il cuore del linguaggio: del codice originale di Lerdorf rimase ben poco. Il nuovo motore, chiamato **Zend Engine**, rese PHP molto più veloce.

Da lì l'evoluzione è stata continua:

- **PHP 4** introdusse la prima programmazione orientata agli oggetti e la gestione delle **sessioni**;
- **PHP 5** portò, tra le altre cose, i **namespace**;
- con **PHP 8**, la versione su cui si basa questo libro, il linguaggio non ha più nulla da invidiare agli altri: offre una programmazione a oggetti completa e matura, costrutti di programmazione funzionale e prestazioni eccellenti.

Oggi, tra l'altro, l'acronimo PHP non significa più "Personal Home Page" ma è diventato ricorsivo: *PHP: Hypertext Preprocessor*. Se ti incuriosisce la storia completa, su Wikipedia trovi tutti i dettagli; quello che conta per noi è capire che il PHP moderno è un linguaggio profondamente diverso da quello delle origini.

## PHP oggi: molto più di un linguaggio per il web

Il PHP di oggi non è solo un linguaggio per generare pagine web. Con PHP puoi scrivere script che girano sul server direttamente dalla **riga di comando**: fare chiamate verso servizi esterni, aprire socket, collegarti via FTP o SSH — si può fare praticamente qualsiasi cosa, perfino applicazioni desktop. È un linguaggio molto versatile e attualmente molto forte.

Le versioni recenti hanno aggiunto strumenti sempre più moderni: dalla 8.1, per esempio, abbiamo le **enumerazioni** (le *enum*, che approfondiremo nel Capitolo 28) e le costanti `final` nelle classi. Tutte cose che vedremo nel corso del libro, arrivando fino alle novità di PHP 8.5.

E i numeri parlano chiaro: PHP è ancora alla grande. Grandi siti di e-commerce girano su piattaforme scritte in PHP, come Magento o PrestaShop, i framework di riferimento per creare negozi online. C'è WordPress, e complessivamente quasi l'80% delle pagine web è servito da codice PHP. Se sei qui è perché PHP ti piace o lo vuoi scoprire: in entrambi i casi sei nel posto giusto.

## Cosa troverai in questo libro

Vediamo ora una panoramica di ciò che studieremo, così sai cosa aspettarti da ogni parte del libro e dove si inseriscono i progetti pratici.

### Dalle basi del linguaggio al web

Nella **Parte I** prepariamo l'ambiente di sviluppo. Ci sono capitoli dedicati a ciascun sistema operativo: se sei su Windows segui il Capitolo 2, dove installiamo PHP con Laragon (in Appendice A trovi le alternative, come XAMPP); se sei su macOS segui il Capitolo 3; se sei su Linux il Capitolo 4, dove configuriamo uno stack LAMP. Chiudiamo la parte configurando Visual Studio Code per PHP. Un consiglio pratico: se hai già un ambiente di sviluppo con una versione recente di PHP, sei a posto — puoi saltare i capitoli di installazione che non ti riguardano e passare direttamente alla Parte II.

Nella **Parte II** copriamo tutte le fondamenta del linguaggio: la sintassi di base, le variabili, i tipi e le costanti, gli operatori e le strutture di controllo come `if`/`else` e i cicli.

La **Parte III** è dedicata alle funzioni: come dichiararle e usarle, e poi le funzioni per lavorare con le stringhe e quelle per lavorare con gli array.

Nella **Parte IV** entriamo nel PHP per il web: le variabili **superglobali**, la gestione dei cookie, tutte le funzionalità per accedere al file system con `include` e `require`, come processare XML e il DOM con PHP, e infine JSON.

Nella **Parte V** vedremo come collegarci a **MySQL**: che cos'è, come usare phpMyAdmin e una panoramica veloce di `SELECT`, `INSERT`, `UPDATE` e `DELETE`, in modo da avere tutto il necessario per passare al primo progetto pratico.

### Il primo progetto: lo User Management System

La **Parte VI** — la più corposa del libro — è interamente dedicata a costruire, passo dopo passo, uno **User Management System** (UMS): un sistema completo di gestione utenti collegato a un database. Ti anticipo com'è il risultato finale, così sai dove stiamo andando.

L'applicazione presenta un elenco di utenti letto dal database, con la possibilità di inserire un nuovo utente, modificarlo ed eliminarlo. C'è la ricerca: se cerchi ad esempio "Roberto", l'elenco viene filtrato in tempo reale; e c'è la **paginazione** dei risultati. Gestiamo anche l'**upload** e l'elaborazione delle immagini per il profilo di ciascun utente. Poi costruiamo un sistema di **login** completo, con la funzione "ricordami" realizzata con i cookie, e la gestione dei **ruoli**: un utente admin vede i pulsanti di modifica ed eliminazione, mentre un utente normale non li vedrebbe affatto.

Questo progetto lo potrai riutilizzare in qualunque tuo lavoro in cui devi collegarti a un database, mostrare dei dati, inserire, modificare ed eliminare record, con in più la gestione dei profili. Cominciamo da zero, in stile **procedurale**, e lo facciamo evolvere gradualmente verso una struttura organizzata che separa le responsabilità — una sorta di mini MVC, anche se non usiamo ancora le classi.

### La programmazione a oggetti e il PHP professionale

Nella **Parte VII** affrontiamo tutta la programmazione orientata agli oggetti, da zero fino agli aspetti più avanzati: le classi e le proprietà, le interfacce, le classi astratte, le enumerazioni, i **metodi magici** di PHP, e poi i namespace e l'**autoloading**.

Nella **Parte VIII** passiamo agli strumenti del PHP professionale: **Composer**, per includere pacchetti esterni nei nostri progetti, e la gestione degli errori e delle eccezioni.

### Il secondo progetto: il Blog MVC enterprise

Nella **Parte IX** riprendiamo una piattaforma di blogging MVC e la portiamo verso una struttura enterprise: Composer, PSR-4, router con test, controller sottili, model come DTO, repository con PDO, servizi, dependency injection, PSR-7/15, migrazioni, autenticazione, Docker, Redis e CI/CD. Ogni passaggio segue i tag del repository `phpenterpriseblog`, così puoi vedere il codice commit per commit.

Nel blog finito, un utente può registrarsi o fare il login, pubblicare un nuovo articolo, e — se è il proprietario di un post — modificarlo ed eliminarlo; può inoltre aggiungere commenti. Un visitatore non loggato vede comunque i post pubblici del blog.

Chiude il libro la **Parte X**, dove portiamo il nostro lavoro verso la produzione: JSON e health check, deploy e invio di email con PHP.

Questi due progetti ci servono per mettere in pratica tutto quello che impareremo: non resteremo mai sulla pura teoria. Quindi cominciamo — da zero.

## In sintesi

- PHP nasce come insieme di script in C creati da Rasmus Lerdorf per processare i form delle pagine HTML; la sintassi prende in prestito elementi da C, C++ e Perl.
- Divenuto open source, il suo cuore è stato riscritto da Zeev Suraski e Andi Gutmans con il motore Zend Engine, molto più veloce; PHP 4 ha portato oggetti e sessioni, PHP 5 i namespace, e PHP 8 ne fa un linguaggio moderno a tutti gli effetti.
- Il PHP di oggi non serve solo per il web: si usa anche da riga di comando per script, socket, FTP, SSH e perfino applicazioni desktop.
- PHP è tuttora dominante: WordPress, Magento e gran parte delle pagine web girano su PHP.
- Il libro copre l'intero linguaggio — dalle basi alla programmazione a oggetti, da MySQL a Composer — e lo mette in pratica con due progetti completi: lo User Management System (Parte VI) e il Blog MVC (Parte IX).
