# 3. Installare PHP su macOS con Laravel Herd e Homebrew

Su macOS il modo più rapido per iniziare a lavorare con PHP è usare Laravel Herd. Herd installa PHP, configura un web server locale e permette di cambiare versione del linguaggio senza dover modificare manualmente Apache, Nginx o file di configurazione sparsi nel sistema.

L'obiettivo di questo capitolo non è costruire un ambiente perfetto per ogni scenario, ma avere una macchina pronta per seguire il libro: eseguire file PHP dal terminale, aprire progetti nel browser, usare MySQL o MariaDB e preparare il debug con Xdebug.

## Installare Laravel Herd

Scarica Herd dal sito ufficiale di Laravel e installalo come una normale applicazione macOS. Una volta avviato, Herd registra una cartella di lavoro e rende disponibili i siti locali con domini comodi, di solito usando estensioni come `.test`.

Il vantaggio principale è che non devi ricordare il percorso dell'eseguibile PHP: Herd lo espone nella PATH e lo rende disponibile anche dal terminale.

Per verificare l'installazione apri il terminale ed esegui:

```bash
php -v
```

Codice completo: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/it/parte-01/cap-03/listing-01.sh)


Se il comando mostra la versione di PHP, puoi già creare il primo file:

```php
<?php
echo "PHP funziona su macOS";
```

Codice completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/it/parte-01/cap-03/listing-02.php)


Salvalo come `index.php` dentro una cartella di progetto e aprilo con Herd o con il server integrato:

```bash
php -S localhost:8000
```

Codice completo: [listing-03.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/it/parte-01/cap-03/listing-03.sh)


Nel browser visita `http://localhost:8000`. Se vedi il messaggio stampato, l'ambiente è pronto.

## Cambiare versione di PHP

Uno dei motivi per usare Herd è la gestione delle versioni. Durante il libro incontrerai funzionalità introdotte in PHP 7.4, PHP 8.0, PHP 8.1, PHP 8.2, PHP 8.4 e PHP 8.5. È utile poter provare gli esempi con versioni diverse.

Da Herd puoi selezionare la versione globale oppure quella associata a un sito. Quando lavori su un progetto reale conviene controllare la versione richiesta dal progetto, spesso dichiarata in `composer.json`:

```json
{
  "require": {
    "php": "^8.5"
  }
}
```

Codice completo: [listing-04.json](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/it/parte-01/cap-03/listing-04.json)


La versione usata dal terminale e quella usata dal web server devono coincidere. Molti errori strani nascono proprio da questa differenza: il comando `php -v` mostra una versione, mentre il browser ne usa un'altra.

## Installare Homebrew

Homebrew è il gestore di pacchetti più usato su macOS. Anche se Herd basta per PHP, Homebrew è utile per installare database, utility da terminale e strumenti come `wget`, `git`, `composer`, MariaDB o phpMyAdmin.

Verifica se è già presente:

```bash
brew --version
```

Codice completo: [listing-05.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/it/parte-01/cap-03/listing-05.sh)


Se non è installato, segui il comando indicato dal sito ufficiale di Homebrew. Dopo l'installazione chiudi e riapri il terminale, poi ripeti il controllo.

## Installare MariaDB o MySQL

Per i capitoli sul database puoi usare MySQL oppure MariaDB. Ai fini del percorso del libro le differenze non sono importanti: useremo SQL standard e funzionalità comuni.

Con Homebrew puoi installare MariaDB così:

```bash
brew install mariadb
brew services start mariadb
```

Codice completo: [listing-06.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/it/parte-01/cap-03/listing-06.sh)


Poi entra nel client:

```bash
mariadb
```

Codice completo: [listing-07.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/it/parte-01/cap-03/listing-07.sh)


oppure, se hai installato MySQL:

```bash
mysql -u root
```

Codice completo: [listing-08.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/it/parte-01/cap-03/listing-08.sh)


Il primo controllo da fare è creare un database di prova:

```sql
CREATE DATABASE php_guida;
SHOW DATABASES;
```

Codice completo: [listing-09.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/it/parte-01/cap-03/listing-09.sql)


Quando il database risponde, PHP può collegarsi usando PDO, come vedremo nei capitoli successivi.

## phpMyAdmin su macOS

phpMyAdmin non è indispensabile, ma aiuta molto nelle prime fasi perché mostra database, tabelle e record in modo visuale.

Con Homebrew puoi installarlo:

```bash
brew install phpmyadmin
```

Codice completo: [listing-10.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/it/parte-01/cap-03/listing-10.sh)


La configurazione precisa dipende dal web server usato. Se stai seguendo il libro per imparare PHP, non perdere troppo tempo su questo punto: il client da terminale basta per capire SQL, e nei progetti useremo codice PHP per leggere e scrivere dati.

## Configurare Xdebug

Il debug è il salto di qualità rispetto ai `var_dump()` sparsi nel codice. Xdebug permette di fermare l'esecuzione su un breakpoint, vedere il valore delle variabili e avanzare riga per riga.

Con Herd la configurazione è semplificata: controlla nelle impostazioni se Xdebug è disponibile per la versione di PHP selezionata. Dal terminale puoi verificare i moduli caricati:

```bash
php -m | grep xdebug
```

Codice completo: [listing-11.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/it/parte-01/cap-03/listing-11.sh)


Se il modulo è attivo, configura l'editor per ascoltare le connessioni di debug. In Visual Studio Code l'estensione tipica è "PHP Debug"; in PhpStorm il supporto è integrato.

## Laravel Valet

Un'alternativa a Herd è Laravel Valet. Valet crea domini locali per le cartelle di progetto e usa Nginx in background. È più manuale di Herd, ma rimane molto usato.

L'installazione passa da Composer:

```bash
composer global require laravel/valet
valet install
```

Codice completo: [listing-12.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/it/parte-01/cap-03/listing-12.sh)


Poi scegli una cartella e registrala:

```bash
cd ~/Sites
valet park
```

Codice completo: [listing-13.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-3/it/parte-01/cap-03/listing-13.sh)


Una cartella `blog` sarà disponibile come `http://blog.test`. Se stai iniziando adesso, usa Herd; se vuoi capire meglio cosa succede sotto il cofano, Valet è un buon secondo passo.

## In sintesi

Su macOS puoi seguire tutto il libro con Herd, un editor, Composer e MariaDB o MySQL. Homebrew completa l'ambiente quando servono pacchetti aggiuntivi. Verifica sempre tre cose: `php -v` dal terminale, la versione PHP usata dal browser e la disponibilità del database. Quando questi tre elementi sono allineati, puoi concentrarti sul codice.
