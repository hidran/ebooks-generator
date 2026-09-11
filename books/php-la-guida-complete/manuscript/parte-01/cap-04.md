# 4. Installare PHP su Linux con XAMPP

Su Linux puoi installare PHP in molti modi: pacchetti della distribuzione, Docker, compilazione manuale, Apache con mod PHP, PHP-FPM con Nginx o ambienti integrati. Per iniziare velocemente, XAMPP resta una strada semplice perché include Apache, PHP, MariaDB e phpMyAdmin in un unico pacchetto.

Nel lavoro professionale userai spesso strumenti più specifici, ma XAMPP è comodo mentre impari in locale: installi, avvii i servizi, crei un file `index.php` e vedi subito il risultato nel browser.

## Installare XAMPP

Scarica il pacchetto per Linux dal sito di Apache Friends. Dopo il download rendi eseguibile il file:

```bash
chmod +x xampp-linux-*-installer.run
```

Codice completo: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/it/parte-01/cap-04/listing-01.sh)


Poi avvia l'installer con privilegi amministrativi:

```bash
sudo ./xampp-linux-*-installer.run
```

Codice completo: [listing-02.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/it/parte-01/cap-04/listing-02.sh)


Di default XAMPP viene installato in `/opt/lampp`. La cartella principale dei siti è:

```text
/opt/lampp/htdocs
```

Codice completo: [listing-03.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/it/parte-01/cap-04/listing-03.txt)


Per avviare i servizi:

```bash
sudo /opt/lampp/lampp start
```

Codice completo: [listing-04.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/it/parte-01/cap-04/listing-04.sh)


Per fermarli:

```bash
sudo /opt/lampp/lampp stop
```

Codice completo: [listing-05.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/it/parte-01/cap-04/listing-05.sh)


## Il primo file PHP

Crea una cartella di prova dentro `htdocs`:

```bash
sudo mkdir /opt/lampp/htdocs/php-guida
```

Codice completo: [listing-06.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/it/parte-01/cap-04/listing-06.sh)


Poi crea `index.php`:

```php
<?php
echo "PHP funziona con XAMPP su Linux";
```

Codice completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/it/parte-01/cap-04/listing-07.php)


Apri il browser su:

```text
http://localhost/php-guida/
```

Codice completo: [listing-08.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/it/parte-01/cap-04/listing-08.txt)


Se il messaggio appare, Apache sta passando correttamente il file a PHP.

## Permessi della cartella di lavoro

Un problema frequente su Linux è modificare file dentro `/opt/lampp/htdocs` senza permessi. Puoi cambiare proprietario della cartella del progetto:

```bash
sudo chown -R "$USER":"$USER" /opt/lampp/htdocs/php-guida
```

Codice completo: [listing-09.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/it/parte-01/cap-04/listing-09.sh)


Evita di lavorare sempre con `sudo`: rende scomodo l'editor, crea file con proprietari diversi e nasconde problemi che poi riappariranno in produzione.

## Usare PHP dal terminale

XAMPP installa il binario PHP dentro `/opt/lampp/bin`. Puoi eseguire:

```bash
/opt/lampp/bin/php -v
```

Codice completo: [listing-10.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/it/parte-01/cap-04/listing-10.sh)


Se vuoi richiamarlo semplicemente con `php`, aggiungi il percorso alla PATH nel file di configurazione della shell:

```bash
export PATH="/opt/lampp/bin:$PATH"
```

Codice completo: [listing-11.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/it/parte-01/cap-04/listing-11.sh)


Dopo aver riaperto il terminale:

```bash
php -v
```

Codice completo: [listing-12.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/it/parte-01/cap-04/listing-12.sh)


Il terminale è importante perché molti strumenti PHP, compreso Composer, vengono usati da riga di comando.

## phpMyAdmin e MariaDB

XAMPP include phpMyAdmin. Lo trovi nel browser:

```text
http://localhost/phpmyadmin
```

Codice completo: [listing-13.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/it/parte-01/cap-04/listing-13.txt)


Da qui puoi creare database, tabelle, colonne e record senza ricordare subito tutti i comandi SQL. Non usare però phpMyAdmin come scorciatoia permanente: nei capitoli su MySQL vedremo le query perché un'applicazione PHP deve saper parlare direttamente con il database.

Un controllo rapido dal terminale:

```bash
/opt/lampp/bin/mysql -u root
```

Codice completo: [listing-14.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/it/parte-01/cap-04/listing-14.sh)


Poi:

```sql
SHOW DATABASES;
```

Codice completo: [listing-15.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/it/parte-01/cap-04/listing-15.sql)


## Alternative: pacchetti della distribuzione

Su Ubuntu e Debian puoi installare PHP dai repository:

```bash
sudo apt update
sudo apt install php php-cli php-mysql apache2 mariadb-server
```

Codice completo: [listing-16.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/it/parte-01/cap-04/listing-16.sh)


Questa strada è più vicina a un server reale, ma richiede più configurazione. Per imparare il linguaggio va benissimo XAMPP; quando inizierai a fare deploy, sarà più utile capire PHP-FPM, web server e variabili d'ambiente.

## NetBeans su Ubuntu

Anche NetBeans resta utile. È un IDE storico per PHP: meno leggero di Visual Studio Code, ma comodo se vuoi un ambiente già strutturato con progetti, esecuzione, completamento e debug.

La cosa importante è configurare il percorso di PHP nelle preferenze dell'IDE. Se usi XAMPP, il binario è:

```text
/opt/lampp/bin/php
```

Codice completo: [listing-17.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/it/parte-01/cap-04/listing-17.txt)


Se usi i pacchetti della distribuzione, di solito è:

```text
/usr/bin/php
```

Codice completo: [listing-18.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/it/parte-01/cap-04/listing-18.txt)


## In sintesi

Con Linux devi fare attenzione a tre aspetti: avvio dei servizi, permessi dei file e percorso del binario PHP. XAMPP semplifica il primo setup e ti permette di concentrarti su linguaggio, database e progetti. Quando tutto funziona, mantieni una regola semplice: lo stesso codice deve poter essere eseguito dal browser e dal terminale senza sorprese.
