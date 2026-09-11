# 39. Ambienti e strumenti avanzati

Nel libro abbiamo usato strumenti diversi: Laragon, Herd, XAMPP, Homebrew, Valet, Visual Studio Code, PhpStorm, NetBeans, Xdebug, Apache, phpMyAdmin. Non devi usarli tutti. Devi capire quale problema risolve ciascuno.

## Scegliere l'ambiente

Per iniziare:

- Windows: Laragon;
- macOS: Herd;
- Linux: XAMPP o pacchetti della distribuzione.

Per lavoro professionale potresti passare a Docker, Valet, DDEV, Laravel Sail o ambienti aziendali. Il principio resta: PHP, web server, database e strumenti devono parlare tra loro.

## Installare PHP 8 manualmente

Quando installi PHP manualmente devi controllare:

```bash
php -v
php --ini
php -m
```

Codice completo: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-39/it/parte-10/cap-39/listing-01.sh)


La versione, il file `php.ini` e i moduli caricati spiegano quasi tutti i problemi iniziali.

## Apache e virtual host

Un virtual host associa un dominio locale a una cartella:

```apache
<VirtualHost *:80>
    ServerName blog.test
    DocumentRoot "/path/to/blog/public"
</VirtualHost>
```

Codice completo: [listing-02.apache](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-39/it/parte-10/cap-39/listing-02.apache)


La root deve puntare a `public`, non all'intero progetto. In questo modo file di configurazione, sorgenti e `vendor/` non sono esposti direttamente.

## Homebrew, Apache e MariaDB

Su macOS puoi installare anche stack manuale:

```bash
brew install php
brew install httpd
brew install mariadb
```

Codice completo: [listing-03.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-39/it/parte-10/cap-39/listing-03.sh)


Poi avviare servizi:

```bash
brew services start httpd
brew services start mariadb
```

Codice completo: [listing-04.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-39/it/parte-10/cap-39/listing-04.sh)


È una buona strada se vuoi capire ogni componente, ma richiede più manutenzione di Herd.

## Xdebug su Windows e Linux

Xdebug deve essere compatibile con versione PHP, architettura e thread safety. Quando non si carica:

- controlla `php -v`;
- controlla `php --ini`;
- controlla se il file `.dll` o `.so` è nel percorso giusto;
- verifica la porta `9003`;
- guarda `php -m`.

La configurazione moderna include:

```ini
xdebug.mode=debug
xdebug.start_with_request=yes
xdebug.client_port=9003
```

Codice completo: [listing-05.ini](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-39/it/parte-10/cap-39/listing-05.ini)


## Editor diversi

Visual Studio Code è rapido e modulare. PhpStorm è più completo e integrato. NetBeans resta utile se preferisci un IDE tradizionale. La scelta non cambia PHP: cambia la produttività.

Qualunque editor tu scelga, deve poter fare tre cose:

- aprire il progetto come cartella;
- usare il PHP corretto;
- avviare o ascoltare Xdebug.

## phpMyAdmin e strumenti database

phpMyAdmin va bene per ispezionare dati. HeidiSQL, TablePlus, DBeaver e gli strumenti integrati degli IDE offrono alternative. Impara comunque SQL: l'interfaccia visuale aiuta, ma non sostituisce la comprensione delle query.

## In sintesi

Non esiste un unico ambiente giusto. Esiste un ambiente coerente, riproducibile e comprensibile. Quando qualcosa non funziona, riduci il problema: quale PHP sto usando? Quale `php.ini`? Quale server? Quale database? Questa capacità di diagnosi vale più del nome dello strumento.
