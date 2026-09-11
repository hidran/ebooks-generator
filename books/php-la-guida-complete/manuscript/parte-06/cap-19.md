# 19. User Management System: struttura, dati e layout

Lo User Management System è il primo progetto completo del libro. Qui non usiamo ancora un framework e non usiamo ancora Composer: il progetto pubblico di riferimento, [`php-user-management-system`](https://github.com/hidran/php-user-management-system), nasce come applicazione procedurale con `mysqli`, file inclusi esplicitamente, template PHP e controller separati.

Questa scelta è voluta, e vale la pena difenderla apertamente perché a qualcuno sembrerà un passo indietro. Nel resto del libro parliamo di *enterprise PHP*: MVC, PSR-4, dependency injection, repository, test. Perché allora ripartire da un'applicazione procedurale con `mysqli` e `require` a mano? Perché un framework è, in fondo, un insieme di risposte a domande che devi prima esserti posto. Se non hai mai sentito il dolore di includere venti file a mano, l'autoload di Composer è magia incomprensibile; se non hai mai mescolato logica e HTML nello stesso file, la separazione controller/view è una regola che subisci invece di capirla; se non hai mai scritto una query concatenando stringhe, non capisci davvero cosa ti risparmia un query builder. Questo progetto ti fa vivere il flusso più diretto — configurazione, connessione, query, template, form, sessioni, redirect — così che nella Parte IX, quando lo stesso codice diventerà classi e servizi, tu sappia *perché*. Costruiamo prima la versione che un framework poi migliora.

## Repository e commit

Puoi leggere la storia del progetto così:

```bash
git clone https://github.com/hidran/php-user-management-system.git
cd php-user-management-system
git log --reverse --oneline
```

Codice completo: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-19/it/parte-06/cap-19/listing-01.sh)

Sorgente reale: [repository `php-user-management-system`](https://github.com/hidran/php-user-management-system).

Vale la pena leggere il progetto **attraverso la sua storia**, non solo nel suo stato finale. `git log --reverse` mostra i commit dal primo all'ultimo, e quell'ordine è di per sé un percorso didattico: prima configurazione e connessione MySQL, poi lista utenti, ordinamento, ricerca, paginazione, CRUD, upload, ruoli, login, CSRF, sessioni e remember me. Ogni commit aggiunge una funzionalità sopra la precedente, e leggendoli in ordine vedi l'applicazione **crescere** invece di trovartela già fatta. È un modo di studiare codice altrui che ti consiglio oltre questo libro: un buon storico Git è una spiegazione scritta un pezzo alla volta.

## Configurazione applicativa

Il file `config.php` contiene le impostazioni centrali. Nel commit finale include database, paginazione, colonne ordinabili, upload, ruoli e remember me:

```php
<?php

return [
    'mysql_host' => 'db',
    'mysql_user' => 'root',
    'mysql_password' => 'hidran',
    'mysql_db' => 'corsophp',
    'recordsPerPage' => 10,
    'maxLinks' => 10,
    'orderByColumns' =>
        ['id', 'username', 'fiscalcode', 'age', 'email', 'role_type'],
    'uploadDir' => 'avatar',
    'mimeTypes' => ['image/jpeg', 'image/png', 'image/gif'],
    'roleTypes' => ['user', 'admin', 'editor'],
    'rememberMeTTL' => 60 * 60 * 24 * 30,
    'rememberMeCookieName' => 'ums_remember_token'
];
```

Codice completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-19/it/parte-06/cap-19/listing-02.php)

Sorgente reale: [`config.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/config.php).

Un singolo file che restituisce un array associativo: è il modo più semplice di centralizzare la configurazione, e nonostante la sua semplicità applica un principio importante. Tutto ciò che potresti voler cambiare senza toccare la logica — quanti record per pagina, quali colonne sono ordinabili, quali tipi di file accettare, quanto dura il remember me — sta **in un punto solo**. È un anticipo dell'idea di configurazione separata dal codice: le funzioni del progetto leggono da qui invece di avere valori "magici" sparsi al loro interno.

Detto questo, c'è un limite che è giusto riconoscere subito, perché è esattamente ciò che il progetto enterprise correggerà: qui la password del database è **scritta in chiaro dentro il codice**. Per un progetto didattico che gira in locale va bene, ma in produzione le credenziali non devono mai stare in un file versionato in Git — finirebbero nella storia del repository, visibili a chiunque vi acceda. Nel blog enterprise della Parte IX faremo il passo successivo: spostare i valori sensibili fuori dal codice e leggerli dall'**ambiente** (le variabili d'ambiente, il file `.env`). Per ora tienilo a mente come un "da correggere" annotato a margine.

## Connessione con `mysqli`

La connessione viene incapsulata in una funzione, non riscritta in ogni file:

```php
<?php

declare(strict_types=1);
function getConnection(): mysqli
{
    $config = require 'config.php';

    $mysqli = new mysqli(
        $config['mysql_host'],
        $config['mysql_user'],
        $config['mysql_password'],
        $config['mysql_db']
    );

    if ($mysqli->connect_error) {
        die($mysqli->connect_error);
    }
    return $mysqli;
}
```

Codice completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-19/it/parte-06/cap-19/listing-03.php)

Sorgente reale: [`connection.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/connection.php).

Una funzione sola per stabilire la connessione, richiamata ovunque serva. Sembra banale, ma è un'applicazione del principio **DRY**: la logica di connessione — leggere la config, creare l'oggetto `mysqli`, gestire l'errore — esiste in un punto solo. Il giorno che cambi database, o aggiungi un parametro di charset, o vuoi gestire l'errore in modo diverso, correggi qui e tutto il resto dell'applicazione ne beneficia. Se ogni file aprisse la propria connessione a mano, quella stessa modifica andrebbe ripetuta in decine di posti. Incapsulare rende anche **esplicito il confine** con MySQL: c'è un unico punto in cui l'applicazione tocca il database driver, ed è più facile da trovare, capire e — più avanti — sostituire. Nella Parte IX questo stesso concetto diventerà una factory PDO registrata nel container, ma l'idea di fondo — un solo posto responsabile della connessione — è già qui.

## Tabella utenti

La tabella `users` contiene dati anagrafici, avatar, password hash e ruolo:

```sql
create table users
(
    id         bigint unsigned auto_increment
        primary key,
    username   varchar(64)                                                not null,
    email      varchar(64)                                                not null,
    fiscalcode char(16)                                                   not null,
    age        smallint unsigned                                          not null,
    avatar     varchar(255)                                               not null,
    password   varchar(255)                                               not null,
    role_type  enum ('user', 'editor', 'admin') default 'user'            not null,
    created_at datetime                         default CURRENT_TIMESTAMP not null on update CURRENT_TIMESTAMP,
    updated_at datetime                         default CURRENT_TIMESTAMP null,
    deleted_at datetime                                                   null,
    constraint u_fiscalcode
        unique (fiscalcode)
)
    collate = utf8mb3_unicode_ci;
```

Codice completo: [listing-04.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-19/it/parte-06/cap-19/listing-04.sql)

Sorgente reale: [`data/users.sql` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/data/users.sql).

Lo schema della tabella non è un dettaglio tecnico da sorvolare: è dove si decide molto della sicurezza e della correttezza dell'applicazione, ancora prima di scrivere una riga di PHP. Guarda alcune scelte. La colonna `password` è larga **255 caratteri**, non 32: perché non conterrà una password, ma l'hash prodotto da `password_hash()` (Capitolo 22), che comprende algoritmo, costo e salt. Il `role_type` è un `enum` con tre valori fissi: il database stesso rifiuta un ruolo che non sia `user`, `editor` o `admin` — un vincolo di integrità che nessun errore di PHP può aggirare. Il vincolo `unique` su `fiscalcode` è la difesa vera contro i duplicati di cui parlavamo nel Capitolo 22: la garanzia non sta in un controllo applicativo, sta qui. E le tre colonne temporali `created_at`, `updated_at`, `deleted_at` raccontano un'intenzione: `deleted_at` in particolare suggerisce la **soft delete**, cancellare marcando una data invece di rimuovere fisicamente la riga, così un utente eliminato per errore è recuperabile. Il progetto gestisce ancora l'SQL a mano, e questo è prezioso proprio perché ti costringe a vedere esattamente quali colonne servono a ogni funzionalità.

## Entry point

`index.php` avvia sessione, connessione, funzioni comuni, ACL e autenticazione. Poi prova l'auto-login e protegge la pagina principale:

```php
<?php

require_once 'includes/session.php';
require_once 'connection.php';
require_once 'functions.php';
require_once 'includes/acl.php';
require_once 'includes/auth.php';
tryAutoLogin();
if (!is_user_logged_in()) {
    redirect('login.php');
}
require_once 'includes/csrf.php';
```

Codice completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-19/it/parte-06/cap-19/listing-05.php)

Sorgente reale: [`index.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/index.php).

L'`index.php` è il **front controller** ante litteram: il punto unico da cui passano le richieste alla pagina principale. Il flusso si legge dall'alto in basso come una lista di priorità: prima si caricano le dipendenze (sessione, connessione, funzioni, ACL, auth), poi si stabilisce **se** l'utente può stare qui (auto-login, controllo della sessione, eventuale redirect), e solo dopo si passa a costruire l'interfaccia. È lo stesso ordine — dipendenze, autorizzazione, rendering — che ritroverai in qualsiasi framework, solo scritto a mano. Quella catena di `require_once` all'inizio è esattamente ciò che l'autoload di Composer, nella Parte VIII, farà sparire: qui la vedi nuda, e capirla ora rende l'autoload una comodità invece che una magia.

## Controller e view

Il controller della lista prepara parametri, conteggio e record:

```php
<?php

declare(strict_types=1);
$orderBy = $orderBy ?? 'ASC';
$recordsPerPage = $recordsPerPage ?? 10;
$search = $search ?? '';
$currentPage = $currentPage ?? 1;
$currentOrderDir = $currentOrderDir ?? 'DESC';
$params = [
    'orderBy' => $orderBy,
    'recordsPerPage' => $recordsPerPage,
    'orderDir' => $currentOrderDir,
    'search' => $search,
    'page' => $currentPage
];
$totalRecords = getTotalUserCount($search);

$users = $totalRecords ? getUsers($params) : [];

require 'view/userList.php';
```

Codice completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-19/it/parte-06/cap-19/listing-06.php)

Sorgente reale: [`controller/displayUsers.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/controller/displayUsers.php).

Qui si intravede, in forma embrionale, la separazione **controller/view** che sarà il cuore della Parte IX. Il controller non stampa niente: raccoglie i parametri, chiama le funzioni che parlano col database (`getTotalUserCount`, `getUsers`) e prepara le variabili che serviranno alla presentazione. Solo alla fine `require 'view/userList.php'` passa il testimone al file che si occupa dell'HTML. Nota la piccola ottimizzazione `$totalRecords ? getUsers($params) : []`: se non c'è nemmeno un record, si evita la seconda query — inutile chiedere le righe di una pagina che sarà vuota.

La view si occupa dell'HTML:

```php
<table class="table table-dark table-striped">
    <caption>USERS LIST</caption>
    <thead>
    <tr>
        <th colspan="8" class="text-center text-bg-dark">
            <?= $totalRecords ?> RECORDS FOUND.
            PAGE <?= $currentPage ?> of <?= $totalPages ?>
        </th>
    </tr>
```

Codice completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-19/it/parte-06/cap-19/listing-07.php)

Sorgente reale: [`view/userList.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/view/userList.php).

La view è quasi solo HTML, con qualche `<?= ?>` che inserisce i dati preparati dal controller. È ancora PHP tradizionale — nessun motore di template, nessuna classe — ma il confine è già visibile e ha un valore concreto: chi lavora sulla grafica tocca la view senza rischiare di rompere la logica, e chi lavora sui dati tocca il controller senza perdersi nell'HTML. Questa divisione di responsabilità, qui ottenuta con la semplice disciplina di tenere i file separati, nella Parte IX diventerà una regola imposta dall'architettura. Vederla nascere per convenzione, prima che per costrizione, ti fa capire *perché* la separazione conviene.

## In sintesi

Lo User Management System parte con strumenti diretti — `config.php`, `connection.php`, funzioni comuni, controller procedurali e template PHP — e questa base semplice non è un ripiego, è una scelta didattica. Ogni pezzo che vedi qui è la versione "a mano" di qualcosa che un framework poi automatizza: la configurazione centralizzata anticipa le variabili d'ambiente, la funzione di connessione anticipa la factory nel container, la catena di `require_once` anticipa l'autoload, la separazione controller/view anticipa l'MVC vero. Costruire prima questa versione rende chiaro, quando arriveremo alla Parte IX, che cosa esattamente le classi, i repository, i servizi e i middleware vengono a **migliorare** — e perché. Un framework capito è molto più utile di un framework subìto.
