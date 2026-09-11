# 29. Composer e pacchetti

Nel capitolo precedente hai scritto un autoloader a mano; Composer è lo strumento che ti solleva da quel lavoro e da molto altro. È il **gestore di dipendenze** standard di PHP, e fa due cose che nel mondo moderno sono inseparabili dal concetto stesso di "progetto": installa e tiene aggiornate le librerie di terze parti, dichiarando quali pacchetti e quali versioni servono, e genera automaticamente l'**autoload PSR-4** — cioè esattamente il meccanismo nome-percorso del Capitolo 28, ma scritto e ottimizzato per te. È lo strumento che trasforma un mucchio di file `.php` in un progetto governabile.

## Installare Composer

Composer è un programma da riga di comando che installi una volta sola sul sistema. Per verificare che ci sia:

```bash
composer --version
```

Codice completo: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-29/it/parte-08/cap-29/listing-01.sh)


Se il comando risponde con un numero di versione, sei pronto. Altrimenti installalo seguendo la procedura ufficiale per il tuo sistema operativo: è un'operazione da fare una volta, non a ogni progetto.

## `composer.json`

Il cuore di tutto è `composer.json`, il **manifesto** del progetto: un solo file che dichiara cosa serve.

```json
{
  "name": "hidran/php-guida",
  "require": {
    "php": "^8.5"
  },
  "autoload": {
    "psr-4": {
      "App\\": "src/"
    }
  }
}
```

Codice completo: [listing-02.json](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-29/it/parte-08/cap-29/listing-02.json)


Leggilo riga per riga, perché ogni chiave conta. `name` è l'identità del progetto nella forma `vendor/pacchetto`. `require` elenca le dipendenze: qui c'è solo `php` con il vincolo `^8.5`, dove il *caret* significa "questa versione o una successiva compatibile" — è la sintassi con cui dichiari un intervallo invece di inchiodarti a una versione unica. E `autoload.psr-4` contiene la mappatura `App\ → src/`: è la convenzione del Capitolo 28, ora scritta una volta sola in un posto dichiarativo. Dopo aver creato o modificato il file, chiedi a Composer di generare l'autoloader:

```bash
composer dump-autoload
```

Codice completo: [listing-03.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-29/it/parte-08/cap-29/listing-03.sh)


Composer legge la mappatura PSR-4 e produce `vendor/autoload.php`: la versione industriale, e già ottimizzata, dell'autoloader che nel capitolo scorso avevi scritto a mano.

## Usare l'autoload di Composer

Nel punto di ingresso dell'applicazione basta una riga:

```php
<?php
require __DIR__ . "/../vendor/autoload.php";

use App\Controllers\PostController;

$controller = new PostController();
```

Codice completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-29/it/parte-08/cap-29/listing-04.php)


Quel singolo `require __DIR__ . "/../vendor/autoload.php"` sostituisce **tutti** i `require` manuali del Capitolo 28. Da questo momento nomini una classe di `App\` — `PostController` — e Composer la carica per te, calcolando il percorso dal namespace. Nota anche la convenzione del percorso: l'autoload sta in `vendor/`, il punto di ingresso in `public/`, e da lì risali con `../`. È l'organizzazione che ritroverai nel progetto MVC della Parte IX.

## Installare un pacchetto

Il vero potere di Composer è dare accesso a un intero ecosistema di librerie già scritte. Invece di reinventare l'invio delle email, installi un pacchetto che lo fa già:

```bash
composer require phpmailer/phpmailer
```

Codice completo: [listing-05.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-29/it/parte-08/cap-29/listing-05.sh)


Con un comando Composer aggiorna `composer.json` aggiungendo la dipendenza, crea o modifica `composer.lock` (ci arriviamo tra poco) e scarica il codice del pacchetto in `vendor/`. Da quel momento la libreria è disponibile tramite l'autoload, senza un solo `require` in più:

```php
<?php
use PHPMailer\PHPMailer\PHPMailer;

$mail = new PHPMailer(true);
```

Codice completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-29/it/parte-08/cap-29/listing-06.php)


Questo è il senso di un gestore di dipendenze: il codice di terze parti si integra nel tuo con la stessa naturalezza delle tue classi, e ne riusi la manutenzione fatta da altri invece di riscrivere — e mantenere — funzionalità complesse come un client SMTP.

## `composer.lock`

Qui sta una distinzione che genera parecchia confusione, e vale la pena chiarirla bene. `composer.json` dichiara **vincoli** di versione — `^8.5` è un intervallo, non un numero preciso. `composer.lock`, invece, registra le versioni **esatte** effettivamente installate, risolte a partire da quei vincoli. In un'applicazione il lock file **va versionato** in Git, ed è la regola più importante del capitolo: committare il lock garantisce che il tuo portatile, la macchina di un collega, la CI e la produzione installino tutti le stesse identiche versioni, byte per byte. Senza, ognuno risolverebbe i vincoli per conto suo e ti ritroveresti con build sottilmente diverse — il classico "sulla mia macchina funziona". Da qui la differenza tra i due comandi:

```bash
composer install
composer update
```

Codice completo: [listing-07.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-29/it/parte-08/cap-29/listing-07.sh)


`install` legge il lock file e installa **esattamente** quelle versioni: è deterministico, ed è il comando da usare in deploy. `update` invece ricalcola le versioni consentite dai vincoli, scarica le più recenti e **riscrive** il lock. È un'operazione da fare consapevolmente, sul tuo ambiente di sviluppo, testando ciò che ne esce: non lanciare mai `update` alla cieca in produzione, o rischi di aggiornare mezza applicazione senza accorgertene.

## Pacchetti da GitHub

Come fa Composer a trovare `phpmailer/phpmailer`? Attraverso **Packagist**, l'indice pubblico dei pacchetti PHP, dove gli autori pubblicano le loro librerie (spesso ospitate su GitHub). È da lì che `require` pesca per default:

```bash
composer require vendor/package
```

Codice completo: [listing-08.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-29/it/parte-08/cap-29/listing-08.sh)


Se un pacchetto non è su Packagist, puoi dichiarare un repository personalizzato dentro `composer.json` e puntare Composer direttamente a un repo Git. È possibile, ma fallo solo quando serve davvero: per iniziare, resta sui pacchetti pubblicati e attivamente mantenuti. Ogni dipendenza è codice altrui che entra nel tuo progetto, e scegliere librerie diffuse e curate è una prima, concreta forma di sicurezza della *supply chain*.

## Script utili

`composer.json` può contenere anche degli **script**, cioè scorciatoie per i comandi ricorrenti del progetto:

```json
{
  "scripts": {
    "start": "php -S localhost:8000 -t public",
    "autoload": "composer dump-autoload"
  }
}
```

Codice completo: [listing-09.json](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-29/it/parte-08/cap-29/listing-09.json)


Definito lo script `start`, chiunque lavori sul progetto può avviare il server locale con:

```bash
composer start
```

Codice completo: [listing-10.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-29/it/parte-08/cap-29/listing-10.sh)


È un modo semplice ma efficace di **documentare** i comandi del progetto dove è naturale cercarli — nel `composer.json` — invece di affidarli a un file README che nessuno legge. Chi arriva nuovo non deve indovinare come si avvia l'applicazione: gli basta guardare gli script.

## In sintesi

Composer risolve i due problemi che, superata la manciata di file, ogni progetto PHP incontra: le **dipendenze** e l'**autoload**. Con `composer.json` dichiari in un solo posto i pacchetti, la versione di PHP richiesta e la mappatura PSR-4; con `vendor/autoload.php` carichi tutto — tuo codice e librerie — in modo coerente e con una riga sola. Ricordati la coppia `composer.json`/`composer.lock`: il primo dichiara i vincoli, il secondo inchioda le versioni esatte, e va committato per avere build riproducibili ovunque. Nei prossimi capitoli Composer sarà la base del progetto MVC e il modo con cui integreremo librerie esterne come PHPMailer: da qui in poi, ogni progetto serio parte da un `composer.json`.
