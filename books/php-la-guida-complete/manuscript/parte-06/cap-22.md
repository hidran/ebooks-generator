# 22. Login, registrazione, sessioni e CSRF

Dopo il CRUD, lo User Management System deve sapere **chi** sta usando l'applicazione. Fino a qui ogni visitatore era uguale a tutti gli altri: chiunque poteva aprire la lista utenti, modificare un record, cancellarlo. Adesso introduciamo due concetti che sembrano lo stesso ma non lo sono affatto, e conviene tenerli separati fin da subito.

L'**autenticazione** risponde alla domanda *"chi sei?"*. È il momento in cui l'utente dimostra la propria identità, di solito con email e password. L'**autorizzazione** risponde a *"che cosa puoi fare?"*. È il controllo che avviene dopo, ogni volta che l'utente prova a compiere un'azione. Sono due passaggi distinti: un utente autenticato non è automaticamente autorizzato a tutto, ed è proprio dalla confusione tra i due che nascono molti buchi di sicurezza.

In questo capitolo mettiamo insieme quattro pezzi: le **sessioni** (per ricordare chi è l'utente tra una richiesta e l'altra), gli **hash delle password** (per non conservare mai una password leggibile), i **token CSRF** (per essere sicuri che una richiesta arrivi davvero dal nostro form) e i **ruoli** (per decidere chi può fare cosa). Il repository pubblico li implementa in forma procedurale, con funzioni raccolte in `includes/`: è volutamente la versione più semplice possibile, quella che ti fa vedere il meccanismo senza l'astrazione di un framework.

![Il form di login di UMS. La casella "Remember me" alimenta il meccanismo di token persistente che vedremo nel capitolo 24.](figures/cap-22/login-form.png)

## Cookie di sessione

Prima di tutto, un ripasso su cosa sia davvero una sessione, perché è il pezzo su cui si regge tutto il resto. HTTP è un protocollo **senza stato**: ogni richiesta arriva al server senza memoria di quelle precedenti. Se l'utente fa login e poi clicca su un link, la seconda richiesta di per sé non sa nulla della prima. La sessione risolve il problema in due tempi: PHP crea sul **server** un contenitore di dati identificato da un ID casuale, e manda al **browser** un cookie che contiene solo quell'ID. Nei dati restano email, ruolo, tutto quello che ci serve; nel cookie viaggia soltanto l'identificativo. È una distinzione importante: chi ruba il cookie non legge i tuoi dati, ma può **impersonare** l'utente, che è anche peggio.

Ecco perché `includes/session.php` configura il cookie *prima* di chiamare `session_start()`:

```php
<?php

declare(strict_types=1);
$secure = !empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off';
session_set_cookie_params([
    'path' => '/',
    'domain' => '',
    'secure' => $secure,
    'httponly' => true,
    'samesite' => 'Lax'
]);
ini_set('session.use_strict_mode', 1);
session_name('ums_sid');
session_start();
```

Codice completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-22/it/parte-06/cap-22/listing-01.php)

Sorgente reale: [`includes/session.php` a `0fa560f`](https://github.com/hidran/php-user-management-system/blob/0fa560f/includes/session.php).

L'ordine non è un dettaglio: `session_set_cookie_params()` va chiamata prima di `session_start()`, perché è quest'ultima a emettere il cookie. Invertirle significa configurare qualcosa che è già stato spedito.

Vediamo le opzioni una per una, perché ognuna chiude una porta precisa:

- **`httponly => true`** impedisce a JavaScript di leggere il cookie tramite `document.cookie`. Se un domani ti sfugge una vulnerabilità XSS in una pagina, l'attaccante può comunque iniettare script, ma non può esfiltrare l'ID di sessione e riusarlo comodamente altrove. È una rete di sicurezza, non un permesso per essere sciatti con l'escaping.
- **`secure => $secure`** dice al browser di inviare il cookie solo su HTTPS. In locale lavoriamo spesso in HTTP, quindi il valore viene calcolato dinamicamente: in produzione, dove c'è il certificato, diventa `true` da solo. Senza questo flag un cookie di sessione può passare in chiaro su una rete Wi-Fi pubblica.
- **`samesite => 'Lax'`** limita l'invio del cookie quando la richiesta parte da un **altro sito**. È la prima linea di difesa contro il CSRF di cui parliamo tra poco: con `Lax` il cookie viaggia sulle navigazioni normali (l'utente clicca un link e arriva sul nostro sito) ma non sulle richieste POST cross-site. Non sostituisce il token CSRF — i browser vecchi non lo rispettano e alcune configurazioni lo aggirano — ma alza parecchio l'asticella.
- **`session.use_strict_mode = 1`** è il più oscuro dei quattro e vale la pena spiegarlo bene. Di default PHP accetta qualsiasi ID di sessione gli arrivi dal browser: se gli mando un cookie con ID `abc123` e quell'ID non esiste, PHP lo *crea*. Un attaccante può quindi scegliere lui l'ID, convincere la vittima a usarlo (basta un link tipo `?PHPSESSID=abc123` su configurazioni permissive) e poi presentarsi con lo stesso ID a login avvenuto. Si chiama **session fixation**. Con `use_strict_mode` attivo, PHP rifiuta gli ID che non ha generato lui e ne emette uno nuovo.
- **`session_name('ums_sid')`** rinomina il cookie, che di default si chiama `PHPSESSID`. Non è sicurezza vera — chiunque guardi la risposta capisce che è un ID di sessione — ma evita di annunciare a scanner automatici "qui gira PHP", e su un server condiviso tiene separate le sessioni di applicazioni diverse.

Nessuna di queste righe fa "funzionare" il login: il login funzionerebbe identico anche senza. Fanno la differenza tra un sistema che regge un attacco banale e uno che no.

## Token CSRF

Questo è il punto in cui conviene fermarsi e capire **l'attacco**, perché il codice della difesa è di tre righe e senza il contesto sembra una formula magica da copiare.

**CSRF** sta per *Cross-Site Request Forgery*, in italiano "falsificazione di richiesta tra siti". Immagina questo scenario. Tu sei loggato nel nostro UMS: hai il cookie di sessione nel browser, valido. In un'altra scheda apri un sito qualsiasi — un forum, una pagina arrivata via email. Quella pagina contiene, nascosto, un form come questo:

```html
<form action="https://ums.example.com/controller/updateRecord.php" method="POST">
    <input type="hidden" name="action" value="delete">
    <input type="hidden" name="id" value="1">
</form>
<script>document.forms[0].submit();</script>
```

Il browser invia la richiesta al nostro server **e allega il cookie di sessione**, perché i cookie vengono inviati in base al dominio di destinazione, non in base a chi ha originato la richiesta. Dal punto di vista del server è una POST perfettamente valida, da un utente autenticato, con i permessi giusti. Il record viene cancellato. L'utente non ha cliccato niente di consapevole.

Nota il punto chiave: l'attaccante **non ha bisogno di leggere** il cookie, né di conoscere la sessione. Gli basta far partire la richiesta dal browser della vittima. È per questo che `httponly` non protegge dal CSRF, e per questo serve un meccanismo diverso.

La difesa si chiama **synchronizer token pattern** e si basa su una semplice asimmetria: il browser della vittima invia automaticamente i cookie, ma **non** conosce il contenuto delle nostre pagine. Se ogni form contiene un valore segreto che solo chi ha davvero caricato la pagina può conoscere, l'attaccante non può replicarlo dall'esterno.

```php
<?php

function csrf_token(): string
{
    return $_SESSION['csrf_token'] ??= bin2hex(random_bytes(32));
}

function csrf_field(): string
{
    return '<input type="hidden" name="csrf_token" value="' . csrf_token() . '">' . "\n";
}

function csrf_validate(string $token): bool
{
    return hash_equals($token, csrf_token());
}
```

Codice completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-22/it/parte-06/cap-22/listing-02.php)

Sorgente reale: [`includes/csrf.php` a `bfc58e7`](https://github.com/hidran/php-user-management-system/blob/bfc58e7/includes/csrf.php).

Tre funzioni, tre dettagli che meritano attenzione.

**`random_bytes(32)`** genera 32 byte **crittograficamente sicuri**, cioè imprevedibili anche conoscendo i valori generati prima. È diverso da `rand()` o `mt_rand()`, che sono veloci ma prevedibili: dato un numero sufficiente di output si può ricostruire lo stato del generatore e predire i successivi. Per un token di sicurezza questo è fatale, quindi la regola è secca: per qualsiasi valore segreto — token CSRF, token di reset password, identificatori di sessione — si usa `random_bytes()` (o `random_int()` per i numeri), mai `rand()`. `bin2hex()` converte poi i byte in 64 caratteri esadecimali, adatti a finire in un attributo HTML.

**L'operatore `??=`** (null coalescing assignment, PHP 7.4, lo abbiamo visto nel Capitolo 8) fa sì che il token venga generato **una volta sola per sessione**: se `$_SESSION['csrf_token']` esiste già, viene restituito quello. Questo significa che tutti i form della sessione condividono lo stesso token. È una scelta di compromesso consapevole: un token diverso per ogni form sarebbe più robusto, ma si rompe non appena l'utente apre due schede o usa il tasto "indietro", perché il token della pagina vecchia non è più quello valido. Per un'applicazione come questa, un token per sessione è l'equilibrio giusto tra sicurezza e usabilità.

**`hash_equals()`** invece di `===` è il dettaglio che quasi tutti saltano. Un confronto normale tra stringhe si ferma al primo carattere diverso: confrontare `"aaaa"` con `"baaa"` è più veloce che confrontare `"aaaa"` con `"aaab"`, perché nel secondo caso il confronto deve arrivare fino in fondo. La differenza è di nanosecondi, ma è **misurabile**, e ripetendo la misura migliaia di volte un attaccante può indovinare il token un carattere alla volta invece di doverlo azzeccare tutto insieme. Si chiama **timing attack**. `hash_equals()` confronta le due stringhe in un tempo che non dipende da quanti caratteri iniziali coincidono, e chiude la porta. La regola pratica: ogni volta che confronti un segreto — token, hash, firma — usa `hash_equals()`, non `==` né `===`.

Una nota sulla firma: la documentazione di PHP definisce `hash_equals(string $known_string, string $user_string)`, con il valore noto per primo. Qui gli argomenti sono invertiti rispetto alla convenzione; il confronto resta a tempo costante, ma conviene abituarsi all'ordine documentato, perché rende il codice più leggibile a chi lo rivede.

Il resto è disciplina, ed è la parte che nessuna funzione può farti al posto tuo: **ogni form che modifica qualcosa deve stampare `csrf_field()`, e ogni controller che riceve quella POST deve chiamare `csrf_validate()` prima di toccare il database**. Un solo endpoint dimenticato annulla il lavoro fatto su tutti gli altri.

## Avvio della sessione utente

Quando le credenziali risultano corrette, il progetto non si limita a scrivere i dati in sessione:

```php
function start_session(array $user): void
{
    session_regenerate_id(true);
    $_SESSION['user_data'] = $user;
    $_SESSION['user_logged_in'] = true;
}
```

Codice completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-22/it/parte-06/cap-22/listing-03.php)

Sorgente reale: [`includes/auth.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

`session_regenerate_id(true)` è la seconda difesa contro la **session fixation** di cui parlavamo prima, e agisce da un'angolazione diversa rispetto a `use_strict_mode`. Il ragionamento è questo: anche ammesso che un attaccante sia riuscito a far usare alla vittima un ID di sessione che lui conosce, quell'ID **viene buttato via nel momento esatto in cui il login riesce**. L'utente autenticato prosegue con un ID nuovo, che l'attaccante non ha mai visto. Il momento del login è quello in cui la sessione cambia di valore — prima era una sessione anonima, adesso è una sessione con privilegi — ed è esattamente lì che l'identificativo va rinnovato.

L'argomento `true` dice a PHP di **eliminare** il file della vecchia sessione invece di lasciarlo lì. Senza, il vecchio ID resterebbe valido sul server: l'attaccante potrebbe continuare a usarlo e si tornerebbe al punto di partenza. È un parametro che si dimentica facilmente e che rende la riga quasi inutile se omesso.

## Verificare il login

`verify_login()` mette in fila i controlli, e l'ordine racconta una logica precisa:

```php
function verify_login(mysqli $conn, string $email, string $password, string $token): array
{
    $res = ['success' => true, 'message' => ''];
    if (!csrf_validate($token)) {
        $res['success'] = false;
        $res['message'] = 'Invalid token';
        return $res;
    }
    if (!validatePassword($password) || !verifyEmail($email)) {
        $res['success'] = false;
        $res['message'] = 'Invalid email or password';
        return $res;
    }
    $user = find_user_by_email($conn, $email);
```

Codice completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-22/it/parte-06/cap-22/listing-04.php)

Sorgente reale: [`includes/auth.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

Prima il token CSRF, poi la forma dei dati, e solo alla fine il database. È il principio del **fail fast**: i controlli che non costano nulla vengono per primi, così una richiesta malformata o falsificata viene respinta senza aver mai aperto una connessione o interrogato una tabella. Ogni ramo di errore fa `return` immediato — non ci sono `else` annidati, e non si arriva mai al codice successivo per sbaglio.

Guarda anche il messaggio del secondo blocco: `'Invalid email or password'`, senza dire quale dei due è sbagliato. Non è pigrizia. Se il sistema rispondesse "questa email non esiste", un attaccante potrebbe provare migliaia di indirizzi e costruirsi l'elenco degli utenti registrati — si chiama **user enumeration**, ed è il primo passo per un attacco mirato. Rispondere sempre allo stesso modo, che sia l'email inesistente o la password sbagliata, non dà informazioni gratis.

Il confronto della password è il pezzo più importante del capitolo:

```php
if (!$user || !password_verify($password, $user['password'])) {
    $res['success'] = false;
    $res['message'] = 'Wrong password or user doesn´t exist';
    return $res;
}
if (password_needs_rehash($user['password'], PASSWORD_DEFAULT)) {
    update_password_hash($conn, $user['id'], password_hash($password, PASSWORD_DEFAULT));
}
```

Codice completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-22/it/parte-06/cap-22/listing-05.php)

Sorgente reale: [`includes/auth.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

Nel database **non c'è nessuna password**. C'è il risultato di `password_hash()`, una funzione a senso unico: dalla password si ottiene l'hash, dall'hash non si torna indietro. Quando l'utente fa login non confrontiamo due password, ma diamo in pasto a `password_verify()` la password appena digitata e l'hash salvato, e lasciamo che sia lei a dire se corrispondono.

Perché non un semplice `md5($password)`, come si vedeva in tanto codice PHP di quindici anni fa? Per due motivi. Il primo è che MD5 e SHA-1 sono **veloci**, e per gli hash di password la velocità è un difetto: una GPU moderna prova miliardi di combinazioni al secondo, quindi un database rubato si trasforma in un elenco di password in chiaro nel giro di ore. `password_hash()` usa bcrypt (o Argon2), algoritmi progettati per essere **lenti** e con un costo configurabile che si può alzare man mano che l'hardware migliora. Il secondo motivo è il **salt**: `password_hash()` genera automaticamente un valore casuale diverso per ogni utente e lo incorpora nell'hash risultante. Due utenti con la stessa password ottengono hash diversi, e le rainbow table — tabelle precalcolate di hash comuni — diventano inutili. Non devi gestire il salt tu: è già dentro la stringa che salvi, insieme all'algoritmo e al costo, ed è per questo che la colonna `password` è larga 255 caratteri e non 32.

`password_needs_rehash()` è la parte lungimirante. Gli algoritmi invecchiano: fra qualche anno `PASSWORD_DEFAULT` punterà a qualcosa di più robusto, o vorrai alzare il costo di bcrypt. Ma gli hash già nel database restano quelli vecchi, e non puoi ricalcolarli perché non conosci le password. L'unico momento in cui la password ti passa davanti in chiaro è il login: allora, se l'hash salvato non rispetta più i parametri correnti, lo si ricalcola al volo e lo si aggiorna. Il risultato è che il database si aggiorna da solo, un utente alla volta, senza chiedere a nessuno di cambiare password. Tre righe che ti risparmiano una migrazione dolorosa fra cinque anni.

## Registrazione

`verify_signup()` segue la stessa struttura, con in più il problema dei duplicati:

```php
function verify_signup(mysqli $conn, string $email, string $password, $username, string $token): array
{
    $res = ['success' => true, 'message' => ''];
    if (!csrf_validate($token)) {
        $res['success'] = false;
        $res['message'] = 'Invalid token';
        return $res;
    }
    if (!validateUserName($username)) {
        $res['success'] = false;
        $res['message'] = 'Invalid user name';
        return $res;
    }
```

Codice completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-22/it/parte-06/cap-22/listing-06.php)

Sorgente reale: [`includes/auth.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

Anche qui: token, poi formato, poi database. La funzione prosegue verificando che l'email non sia già registrata e che la password rispetti i requisiti minimi definiti in `config.php`.

Due osservazioni che valgono oltre questo progetto. La prima: il controllo "esiste già un utente con questa email?" fatto in PHP **non basta da solo**. Fra il momento in cui interroghi la tabella e quello in cui scrivi la riga passa un istante, e due registrazioni simultanee con la stessa email possono passare entrambe il controllo. È una **race condition**, e l'unica difesa vera è il vincolo `UNIQUE` sulla colonna a livello di database — che infatti c'è nello schema della tabella `users`. Il controllo in PHP serve a dare un messaggio di errore gentile; il vincolo serve a garantire l'integrità.

La seconda: quando la validazione passa, `controller/signup.php` salva l'utente con ruolo `user`, **sempre**. Il ruolo non arriva mai dal form. Sembra ovvio detto così, ma è esattamente il tipo di dettaglio che salta: se il campo del ruolo fosse un `<select>` inviato dal client, chiunque potrebbe registrarsi come `admin` modificando l'HTML con gli strumenti per sviluppatori del browser. **Tutto ciò che decide dei privilegi si stabilisce sul server.**

![Il form di registrazione, servito dalla stessa pagina tramite tab. Entrambi i form includono il campo hidden con il token CSRF.](figures/cap-22/signup-form.png)

## Ruoli

Con l'autenticazione a posto, passiamo all'autorizzazione. `includes/acl.php` (da *Access Control List*) tiene insieme i ruoli e le funzioni che li interrogano:

```php
<?php

declare(strict_types=1);

const ROLE_USER = 'user';
const ROLE_ADMIN = 'admin';
const ROLE_EDITOR = 'editor';

function get_user_login_data(): array
{
    return $_SESSION['user_data'] ?? [];
}

function get_user_role(): string
{
    return get_user_login_data()['role_type'] ?? 'user';
}

function user_can_update(): bool
{
    return in_array(get_user_role(), [ROLE_ADMIN, ROLE_EDITOR]);
}

function user_can_delete(): bool
{
    return get_user_role() === ROLE_ADMIN;
}
```

Codice completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-22/it/parte-06/cap-22/listing-07.php)

Sorgente reale: [`includes/acl.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/acl.php).

I ruoli sono **costanti** e non stringhe sparse nel codice: se scrivi `'admin'` a mano in dieci punti, il giorno che sbagli a digitarne uno il controllo fallisce in silenzio e l'utente semplicemente non riesce più a fare qualcosa. Con `ROLE_ADMIN`, un errore di battitura diventa un errore di PHP, che è molto più facile da trovare.

Nota il valore di default in `get_user_role()`: se in sessione non c'è nulla, la funzione restituisce `'user'`, cioè il ruolo **meno privilegiato**. È un'applicazione del principio *fail closed* (o *fail secure*): quando qualcosa non è chiaro, il sistema deve negare, non concedere. Il contrario — restituire `'admin'` in caso di dubbio, o peggio una stringa vuota che poi passa un confronto lasco — è il genere di scelta che trasforma un bug banale in un incidente.

Queste funzioni tornano un booleano e servono a due scopi diversi, che vanno usati **entrambi**. Nella view decidono se mostrare o meno un pulsante:

```php
<?php if (user_can_delete()): ?>
    <a class="btn btn-danger" href="...">DELETE</a>
<?php endif; ?>
```

Nel controller decidono se l'azione può essere eseguita. E qui sta il punto che non va mai dimenticato: **nascondere un pulsante non è sicurezza**. Il pulsante nascosto non impedisce a nessuno di aprire gli strumenti per sviluppatori, leggere l'URL dell'azione e chiamarla a mano. La verifica nella view serve all'esperienza d'uso — non mostrare all'utente cose che non può fare; la verifica nel controller serve alla sicurezza. Se ne devi saltare una, salta quella nella view. Nel prossimo capitolo vediamo proprio come il progetto applica il controllo sui controller e sulle rotte.

## In sintesi

Un sistema di login si regge su cinque pezzi che lavorano insieme, e ognuno chiude una porta diversa. Il **cookie di sessione** configurato con `httponly`, `secure`, `SameSite` e `use_strict_mode` protegge l'identificativo da furto e da fissazione. La **rigenerazione dell'ID** al login butta via ogni sessione che l'utente potrebbe aver ricevuto da un attaccante. Il **token CSRF**, confrontato con `hash_equals()`, garantisce che una POST arrivi davvero dal nostro form e non da un sito ostile. Gli **hash delle password** con `password_hash()`, `password_verify()` e `password_needs_rehash()` fanno sì che un database rubato non si trasformi in un elenco di credenziali. I **ruoli**, verificati sul server e non solo nella view, decidono chi può fare cosa.

Nessuno di questi pezzi è opzionale, e nessuno compensa l'assenza di un altro: sono difese in profondità, pensate perché un singolo errore non diventi una compromissione. Il repository UMS li mostra in forma procedurale, con funzioni globali e stato in `$_SESSION`, ed è il modo migliore per vedere il meccanismo nudo. Nella Parte IX gli stessi concetti torneranno sotto forma di servizi iniettati, middleware e sessioni gestite dal container: cambierà l'impacchettamento, non la sostanza di quello che abbiamo appena visto.
