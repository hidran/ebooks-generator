# Introduzione {.unnumbered}

Sono Hidran Arias e sviluppo con PHP dal 2001. Questo libro raccoglie quell'esperienza quotidiana e la trasforma in un percorso completo: dalle prime righe di codice fino ad applicazioni strutturate pronte per la produzione. Non è un manuale di riferimento da consultare a salti — anche se puoi usarlo così — ma un cammino progressivo in cui ogni capitolo costruisce sui precedenti.

## A chi si rivolge

A chi parte da zero con PHP, ma anche a chi lo usa già e vuole colmare le lacune sulle funzionalità moderne del linguaggio: da PHP 7 fino a PHP 8.5, con typed property, enum, readonly, property hook, pipe operator, estensione URI e molto altro. È utile una conoscenza di base di HTML e CSS; tutto il resto viene spiegato passo dopo passo.

## Come è organizzato il libro

Il percorso è diviso in dieci parti. Nelle **Parti I–III** prepariamo l'ambiente di sviluppo su Windows, macOS e Linux e impariamo le fondamenta del linguaggio: sintassi, variabili, tipi, operatori, strutture di controllo e funzioni. Nella **Parte IV** portiamo PHP sul web: superglobali, cookie, file system, XML e JSON. La **Parte V** introduce MySQL e phpMyAdmin.

Con la **Parte VI** inizia il primo grande progetto del libro: uno User Management System completo, con elenco utenti ordinabile e paginato, ricerca, CRUD, upload di immagini, autenticazione con login, registrazione, remember me e gestione dei ruoli. Le **Parti VII e VIII** affrontano la programmazione orientata agli oggetti — dalle basi fino alle funzionalità più recenti — insieme a Composer e alla gestione delle eccezioni.

Nella **Parte IX** costruiamo il secondo progetto: prendiamo il blog MVC iniziale e lo portiamo verso il repository pubblico `phpenterpriseblog`, con Composer, PSR-4, router testato, PDO, repository, servizi, PSR-7/15, migrazioni, autenticazione, test, Docker, Redis e CI/CD. La **Parte X** chiude il cerchio con JSON e health check, deploy, invio di email, strumenti avanzati e una checklist finale per PHP 8.5.

## Convenzioni

Il codice appare in blocchi come questo:

```php
<?php
echo "Ciao, PHP!";
```

Codice completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-front-matter-introduction/it/00-front-matter/04-intro/listing-01.php)


I comandi da eseguire nel terminale sono preceduti dal contesto in cui vanno lanciati; i nomi di file, funzioni e variabili compaiono nel testo con il `carattere a spaziatura fissa`. I termini tecnici consolidati in inglese (array, form, query, cookie…) restano in inglese, come nell'uso professionale quotidiano.

Tutto il codice del libro è pensato per essere scritto ed eseguito insieme all'autore: il modo migliore di leggere questo libro è con l'editor aperto a fianco.

Buon viaggio nel mondo di PHP.
