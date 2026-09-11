# 33. Domain model, repository, PDO e migrazioni

Nello User Management System della Parte VI l'accesso ai dati era diretto e sparso: `mysqli` chiamato dentro le funzioni, la SQL mescolata alla logica. Funzionava, ma ogni query era un punto in cui potevi sbagliare da solo. Nel blog enterprise il **data layer** — lo strato che parla con il database — viene riorganizzato attorno a tre confini netti: PDO configurato una volta sola con opzioni sicure, i **model** che diventano oggetti dati tipizzati senza una riga di SQL, e i **repository** che sono gli unici a possedere le query. Ognuno di questi confini risponde a una domanda che nella Parte VI restava aperta, e in questo capitolo li costruiamo uno per uno seguendo il codice reale del progetto.

Repository UMS di riferimento: [php-user-management-system](https://github.com/hidran/php-user-management-system). Il commit finale implementa remember me con selector, token hash, rotazione e revoca.

## Connessione PDO sicura

La connessione non deve essere ricreata a mano in ogni controller. Il progetto usa una factory che legge l'ambiente e crea un `PDO` con opzioni **non negoziabili**:

```php
<?php

declare(strict_types=1);

final class PdoConnection
{
    public function __construct(array $options)
    {
        $defaultOptions = [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
        ];

        $this->pdo = new PDO(
            $options['dsn'],
            $options['user'],
            $options['password'],
            $defaultOptions,
        );
    }
}
```

Codice completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-33/it/parte-09/cap-33/listing-01.php)


Sorgente reale: [`src/Database/PdoConnection.php` a `lesson-1-4`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-4/src/Database/PdoConnection.php).


Quelle tre opzioni sono chiamate "non negoziabili" perché stabiliscono, in un posto solo, il comportamento di **ogni** query dell'applicazione, e ciascuna risolve un problema concreto. `PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION` fa sì che un errore SQL sollevi un'eccezione invece di fallire in silenzio: è il *fail loud* del Capitolo 30 applicato al database, così una query rotta si nota subito e non lascia proseguire con dati mancanti. `PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC` restituisce le righe come array associativi puliti, senza il doppione con indici numerici che PDO produrrebbe di default. La terza è la più importante per la sicurezza: `PDO::ATTR_EMULATE_PREPARES => false` obbliga PDO a usare i **prepared statement reali** del driver, invece di simularli lato PHP incollando i valori nella stringa. È la forma più solida della difesa contro la SQL injection che hai imparato a fatica nel Capitolo 20: qui non è più una disciplina da ricordare a ogni query, è impostata una volta per tutte all'origine.

La factory, dal canto suo, costruisce il DSN a partire dai parametri d'ambiente:

```php
<?php

declare(strict_types=1);

$dsn = sprintf(
    '%s:host=%s;port=%d;dbname=%s;charset=utf8mb4',
    $driver,
    $host,
    $port,
    $database,
);
```

Codice completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-33/it/parte-09/cap-33/listing-02.php)


Sorgente reale: [`src/Database/ConnectionFactory.php` a `lesson-1-4`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-4/src/Database/ConnectionFactory.php).


Nota `charset=utf8mb4`: è il set di caratteri Unicode completo, che gestisce correttamente qualunque testo (emoji comprese) ed evita vecchi trucchi di injection legati a codifiche parziali. Ma il cambiamento architetturale più importante è cosa **non** c'è più: nessun Singleton globale, nessuna funzione `getConnection()` richiamata ovunque come nella Parte VI. La connessione viene creata una volta, registrata nel container e **iniettata** dove serve. Chi ha bisogno del database lo dichiara nel costruttore e lo riceve — non va a prenderselo da una variabile globale.

## Model come DTO

Il model `Post` non contiene una riga di SQL. Descrive soltanto la forma di un post:

```php
<?php

declare(strict_types=1);

final class Post
{
    public function __construct(
        public readonly int $id,
        public readonly string $title,
        public readonly string $message,
        public readonly int $userId,
        public readonly string $datecreated,
        public readonly string $email,
    ) {
    }
}
```

Codice completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-33/it/parte-09/cap-33/listing-03.php)


Sorgente reale: [`src/Models/Post.php` a `lesson-1-5`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-5/src/Models/Post.php).


È un **DTO** immutabile, costruito con la property promotion e i `readonly` del Capitolo 25: un oggetto che trasporta dati e nient'altro. Non sa come si legge o si scrive nel database, non contiene logica: è la forma tipizzata di una riga della tabella `posts`. Questa separazione — il model è il *dato*, il repository è l'*accesso al dato* — non è un capriccio, tanto che nel progetto è messa nero su bianco in un **ADR** (Architecture Decision Record, il documento con cui un team registra le decisioni di architettura e il loro perché). Il vantaggio pratico è la tranquillità: un `Post` che non ha accesso al database non potrà mai, per distrazione, lanciare una query nel mezzo di una view. È solo dati che scorrono, tipizzati, tra i livelli dell'applicazione.

## Repository per la SQL

Se il model è il dato, il **repository** è l'unico a sapere come leggerlo e scriverlo. Legge righe dal database e le trasforma in model:

```php
<?php

declare(strict_types=1);

class PostRepository
{
    public function __construct(protected readonly PDO $pdo)
    {
    }

    public function findById(int $id): ?Post
    {
        $sql = 'SELECT p.*, u.email FROM posts p '
             . 'INNER JOIN users u ON u.id = p.user_id '
             . 'WHERE p.id = :id';

        $stmt = $this->pdo->prepare($sql);
        $stmt->execute(['id' => $id]);

        $row = $stmt->fetch();

        return $row === false ? null : Post::fromRow($row);
    }
}
```

Codice completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-33/it/parte-09/cap-33/listing-04.php)


Sorgente reale: [`src/Repositories/PostRepository.php` a `lesson-1-5`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-5/src/Repositories/PostRepository.php).


Guarda `findById()`: prepara la query, la esegue **legando** l'`id` come parametro (`:id`) — mai concatenato nella stringa — recupera la riga e la trasforma in un `Post`, oppure restituisce `null` se non esiste. Ci sono tre lezioni dei capitoli precedenti condensate qui: il prepared statement con valore legato (Capitolo 20, contro la SQL injection), il tipo di ritorno `?Post` che rende esplicita l'assenza (Capitolo 27), e la conversione riga→oggetto che tiene i dati grezzi del database fuori dal resto del codice. Il controller non conosce né la tabella né la query: chiede `findById()` e riceve un `?Post`. Se un domani cambi il database, o passi a un ORM, cambi solo il repository — tutto il resto continua a funzionare, perché dipende dal metodo, non dalla SQL che ci sta dietro.

![Una pagina di post del blog enterprise: il post arriva da `findById()` nel `PostRepository`, i commenti da un secondo repository. Il controller si limita a coordinarli e a passarli alla view.](figures/cap-33/enterprise-blog-post-detail.png)

## Salvare post senza bug ereditati

Il vecchio progetto conteneva un bug didatticamente prezioso: una colonna veniva valorizzata con il campo sbagliato. Nel nuovo repository il metodo `save()` rende **esplicita** la forma dei dati, e questo da solo rende il bug più difficile da commettere:

```php
<?php

declare(strict_types=1);

public function save(array $data): int
{
    $sql = 'INSERT INTO posts (title, user_id, message, datecreated) '
         . 'VALUES (:title, :user_id, :message, NOW())';

    $stmt = $this->pdo->prepare($sql);
    $stmt->execute([
        'title' => $data['title'],
        'user_id' => $data['user_id'],
        'message' => $data['message'],
    ]);

    return (int) $this->pdo->lastInsertId();
}
```

Codice completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-33/it/parte-09/cap-33/listing-05.php)


Sorgente reale: [`src/Repositories/PostRepository.php` a `lesson-1-5`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-5/src/Repositories/PostRepository.php).


La corrispondenza tra colonne e parametri è messa in fila, leggibile: `title` va in `title`, `user_id` in `user_id`, `message` in `message`. Anche l'inserimento usa parametri legati, coerente con `findById()`, e restituisce l'id generato con `lastInsertId()`. Ma la vera difesa contro il ritorno del bug arriverà più avanti sotto forma di **test di regressione**: uno di quei test che non verifica una feature nuova, ma "blocca" un comportamento corretto perché non torni a rompersi. Il bug scoperto una volta diventa un test per sempre — è così che un difetto smette di essere un rischio ricorrente.

## User e Comment

Il blog enterprise non butta via ciò che hai costruito nella Parte VI: ne riusa i concetti di sicurezza, ridistribuendoli tra le classi giuste. Ritrovi tutto quello dello User Management System:

- utente autenticato;
- password salvate con `password_hash()`;
- verifica con `password_verify()`;
- ruoli;
- sessione;
- CSRF;
- contenuti collegati a `user_id`.

La differenza è dove vive questa logica: non più sparsa tra include e funzioni, ma distribuita tra `UserRepository` (i dati utente), `AuthService` (le regole di autenticazione), controller e view. È il servizio di autenticazione a concentrare la logica:

```php
<?php

declare(strict_types=1);

public function verifyLogin(
    string $email,
    string $password,
    string $token,
    string $sessionToken
): AuthResult {
    if (!hash_equals($sessionToken, $token)) {
        return AuthResult::failure('TOKEN MISMATCH');
    }

    $user = $this->users->findByEmail($email);

    if ($user === null || !password_verify($password, $user->password)) {
        return AuthResult::failure('WRONG PASSWORD');
    }

    return AuthResult::success('LOGGED IN', $user);
}
```

Codice completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-33/it/parte-09/cap-33/listing-06.php)


Sorgente reale: [`src/Services/AuthService.php` a `lesson-1-8`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-8/src/Services/AuthService.php).


`verifyLogin()` racchiude in un solo posto le regole che nella Parte VI erano distribuite: prima confronta il token CSRF con `hash_equals()` — il confronto a tempo costante contro i timing attack del Capitolo 22 — poi cerca l'utente per email, e infine verifica la password con `password_verify()`. Nota che non restituisce un semplice `true`/`false`: restituisce un `AuthResult`, un oggetto che porta con sé sia l'esito sia il motivo (`TOKEN MISMATCH`, `WRONG PASSWORD`, oppure l'utente in caso di successo). È l'autenticazione trattata come un servizio con una responsabilità sola, testabile in isolamento. Un'avvertenza pratica: quei messaggi sono stringhe tecniche del codice; in un'applicazione reale, se devono comparire all'utente, li porteresti in un layer di traduzione invece di mostrarli così.

## Migrazioni forward-only

C'è un ultimo confine da sistemare: la **struttura** del database. Non va creata a mano in phpMyAdmin — un rito manuale che nessuno ricorda e nessun ambiente riproduce uguale — ma descritta in file SQL versionati in Git:

```sql
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS users (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    username VARCHAR(64) NOT NULL,
    email VARCHAR(128) NOT NULL,
    password VARCHAR(255) NOT NULL,
    roletype ENUM('admin','editor','user') NOT NULL DEFAULT 'user',
    PRIMARY KEY (id),
    UNIQUE KEY uniq_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

Codice completo: [listing-07.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-33/it/parte-09/cap-33/listing-07.sql)


Sorgente reale: [`database/migrations/0001_init.sql` a `lesson-1-13`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-13/database/migrations/0001_init.sql).


Il file `0001_init.sql` è la prima **migrazione**: uno script numerato che descrive un passo dell'evoluzione dello schema. Ritroverai qui le buone scelte del Capitolo 19 — il `password` largo 255 caratteri per l'hash, il `roletype` come `enum`, l'`email` `UNIQUE` — ma ora versionate, così ogni ambiente costruisce lo stesso identico database a partire dagli stessi file. Ad applicarle è un runner che tiene traccia di quali sono già state eseguite e applica solo le nuove:

```php
<?php

declare(strict_types=1);

$pending = array_filter(
    $files,
    static fn(string $file): bool => !isset($applied[basename($file)])
);

foreach ($pending as $file) {
    $this->apply($file);
}
```

Codice completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-33/it/parte-09/cap-33/listing-08.php)


Sorgente reale: [`src/Console/MigrateCommand.php` a `lesson-1-14`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-14/src/Console/MigrateCommand.php).


Il runner filtra le migrazioni **non ancora applicate** e esegue solo quelle: rilanciarlo è sicuro, perché non riapplica ciò che è già stato fatto. E c'è una scelta di fondo, dichiarata nel nome: le migrazioni sono **forward-only**, si va solo avanti. Niente `down`, niente "rollback". In produzione è più onesto e più sicuro aggiungere un cambiamento compatibile e, se qualcosa va storto, correggere con una nuova migrazione in avanti, piuttosto che illudersi che uno script di `down` possa restituire dati che una `DROP COLUMN` ha già cancellato. I dati distrutti non tornano: meglio un modello che lo riconosce.

## In sintesi

Il data layer enterprise ha confini chiari, ciascuno erede di una lezione dei capitoli precedenti: PDO configurato una volta con opzioni sicure (prepared statement reali contro la SQL injection), model come DTO immutabili che trasportano dati e basta, repository come unici custodi della SQL, servizi come `AuthService` che concentrano la logica applicativa, e migrazioni versionate e forward-only per lo schema. È la stessa applicazione blog degli altri capitoli, ma con l'accesso ai dati organizzato in modo che sia **testabile** — ogni pezzo isolabile e sostituibile con un finto — e **deployabile** — ogni ambiente ricostruibile dagli stessi file. È la differenza tra codice che funziona sul tuo portatile e codice che funziona ovunque.
