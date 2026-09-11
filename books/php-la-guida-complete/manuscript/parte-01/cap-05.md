# 5. Editor, IDE e debugging

Scrivere PHP non significa solo conoscere la sintassi. Serve anche un ambiente che ti aiuti a leggere il codice, trovare errori, navigare tra file e controllare l'esecuzione. Puoi seguire tutto il libro con Visual Studio Code, PhpStorm o NetBeans; l'importante è configurare bene PHP, il terminale e Xdebug.

## Visual Studio Code

Visual Studio Code è leggero, gratuito e molto flessibile. Per PHP conviene installare alcune estensioni:

- un'estensione per il supporto PHP e il completamento del codice;
- un'estensione per Xdebug;
- un formatter, se vuoi mantenere stile coerente;
- il supporto Git, già integrato ma migliorabile con estensioni dedicate.

Apri una cartella di progetto, non un singolo file. In questo modo l'editor può capire i percorsi, indicizzare il codice e usare un terminale integrato nella posizione corretta.

## Il terminale integrato

Nel terminale integrato prova subito:

```bash
php -v
```

Codice completo: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-5/it/parte-01/cap-05/listing-01.sh)


Se VS Code non trova PHP ma il terminale di sistema sì, il problema è la PATH con cui l'applicazione è stata avviata. Su macOS e Linux spesso basta riaprire VS Code dal terminale:

```bash
code .
```

Codice completo: [listing-02.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-5/it/parte-01/cap-05/listing-02.sh)


Su Windows puoi usare Git Bash come terminale predefinito. È comodo perché molti comandi del mondo PHP e Composer sono documentati con sintassi Unix.

## Eseguire un file dall'editor

Un file PHP si può eseguire in due modi diversi:

```bash
php script.php
```

Codice completo: [listing-03.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-5/it/parte-01/cap-05/listing-03.sh)


oppure tramite web server:

```bash
php -S localhost:8000
```

Codice completo: [listing-04.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-5/it/parte-01/cap-05/listing-04.sh)


La differenza è fondamentale. Dal terminale non esistono `$_GET`, `$_POST`, cookie e sessioni come in una richiesta web. Dal browser, invece, PHP lavora dentro il ciclo richiesta-risposta.

## Configurare Xdebug in VS Code

Il debug con breakpoint richiede tre elementi:

- Xdebug installato e attivo nella versione di PHP usata;
- l'editor in ascolto;
- una richiesta che avvii la sessione di debug.

Un file `.vscode/launch.json` essenziale può essere:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Listen for Xdebug",
      "type": "php",
      "request": "launch",
      "port": 9003
    }
  ]
}
```

Codice completo: [listing-05.json](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-5/it/parte-01/cap-05/listing-05.json)


Xdebug 3 usa di default la porta `9003`. Se trovi guide più vecchie con `9000`, controlla la versione: molte configurazioni non funzionano solo perché mischiano impostazioni di Xdebug 2 e Xdebug 3.

## `php.ini` e moduli caricati

Quando PHP si comporta in modo inatteso, chiedigli quale configurazione sta usando:

```bash
php --ini
```

Codice completo: [listing-06.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-5/it/parte-01/cap-05/listing-06.sh)


Per controllare i moduli:

```bash
php -m
```

Codice completo: [listing-07.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-5/it/parte-01/cap-05/listing-07.sh)


Per cercare Xdebug:

```bash
php -m | grep xdebug
```

Codice completo: [listing-08.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-5/it/parte-01/cap-05/listing-08.sh)


Ricorda che PHP CLI e PHP del web server possono leggere file `php.ini` diversi. Se abiliti un'estensione nella CLI ma il browser non la vede, probabilmente stai modificando il file sbagliato.

## PhpStorm

PhpStorm è un IDE commerciale molto completo. Offre refactoring, navigazione tra classi, integrazione con Composer, database tool, test runner e debug già pensati per PHP.

Per usarlo bene:

- imposta l'interprete PHP del progetto;
- configura Composer;
- collega Xdebug;
- registra eventuali server locali se usi path mapping.

Il path mapping serve quando il percorso del file visto dal browser non coincide con quello locale. È frequente con Docker o macchine virtuali, meno con Herd, Laragon o XAMPP.

## NetBeans

NetBeans è un'alternativa valida quando vuoi un IDE tradizionale. Nei progetti PHP devi configurare:

- il percorso di PHP;
- la cartella del progetto;
- l'URL locale per eseguire l'applicazione;
- l'eventuale debugger.

Se l'IDE non esegue il file giusto, controlla prima la cartella root del progetto e poi l'URL di avvio.

## Debug pratico: `var_dump()` o breakpoint?

`var_dump()` resta utilissimo:

```php
<?php
var_dump($_GET);
```

Codice completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-5/it/parte-01/cap-05/listing-09.php)


Lo userai spesso per capire cosa contiene una variabile. Ma quando il flusso diventa più lungo, un breakpoint è più efficace: puoi vedere lo stato del programma senza modificare il codice e senza riempire le pagine di output temporanei.

## In sintesi

Scegli l'editor che preferisci, ma verifica sempre che usi la versione corretta di PHP. Impara presto a distinguere esecuzione da terminale ed esecuzione dal browser. Quando qualcosa non torna, controlla `php -v`, `php --ini`, `php -m` e la configurazione di Xdebug: nella maggior parte dei casi il problema è lì.
