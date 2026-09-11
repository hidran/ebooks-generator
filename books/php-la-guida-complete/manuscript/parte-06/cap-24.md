# 24. Remember me

Il remember me permette all'utente di essere riconosciuto anche dopo la scadenza della sessione PHP: è la casella "ricordami" che spunti al login e che ti fa ritrovare loggato il giorno dopo, senza reinserire le credenziali. Sembra una comodità banale, ed è invece uno dei meccanismi più insidiosi da implementare bene, perché sposta un pezzo di autenticazione **fuori dalla sessione**, in un cookie che vive per settimane sul dispositivo dell'utente.

Partiamo da come **non** si fa, perché è l'errore che quasi tutti fanno la prima volta. La tentazione è salvare nel cookie l'email e la password dell'utente, o l'id, e rileggerli alla visita successiva. È una catastrofe: un cookie è memorizzato in chiaro sul disco, viaggia a ogni richiesta, ed è esattamente il tipo di dato che un attacco XSS o un computer condiviso espongono. Salvare la password in un cookie significa regalarla. Salvare l'id significa che chiunque scriva `user_id=1` nel proprio browser diventa l'amministratore. Serve qualcosa di completamente diverso: non un'identità salvata, ma un **protocollo di prova**. È il pattern **selector/validator**, ed è quello che il repository `php-user-management-system` implementa nel commit `8769ecc` — selector, token, hash, cookie `HttpOnly`, auto-login, rotazione e revoca. Vediamolo pezzo per pezzo.

## Tabella dei token

Il token persistente non va salvato in chiaro. Il database conserva un selector pubblico e l'hash del token segreto:

```sql
create table remember_tokens
(
    id         bigint unsigned auto_increment
        primary key,
    user_id    bigint unsigned                    not null,
    token_hash char(64)                           not null,
    expires_at datetime                           not null,
    created_at datetime default CURRENT_TIMESTAMP not null,
    user_agent varchar(255)                       null,
    ip_address varbinary(16)                      not null,
    selector   char(18)                           not null,
    constraint uk_selector_remember_me
        unique (selector),
    constraint remember_tokens_users_id_fk
        foreign key (user_id) references users (id)
            on delete cascade
);
```

Codice completo: [listing-01.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-24/it/parte-06/cap-24/listing-01.sql)

Sorgente reale: [`data/remember_tokens.sql` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/data/remember_tokens.sql).

La tabella racconta già tutto il protocollo, se sai leggerla. Ci sono due valori separati: il **selector**, con un vincolo `unique`, e il **token_hash**. Il cookie che finirà nel browser conterrà `selector:token` — due pezzi uniti da due punti. Il selector serve a **trovare la riga** velocemente (è indicizzato, univoco), il token serve a **dimostrare** che il browser possiede il segreto. Perché due valori invece di uno solo? Perché separano le due esigenze in conflitto: cercare velocemente nel database vuole un valore indicizzato, ma cercare per un *segreto* indicizzato aprirebbe una via a certi attacchi di temporizzazione sull'indice. Con la coppia, la ricerca avviene sul selector pubblico e il confronto di sicurezza sul token.

Il dettaglio cruciale è che il database salva `token_hash`, **non il token**. Esattamente come per le password del Capitolo 22, il segreto vero non viene mai conservato in chiaro: si salva la sua impronta SHA-256. Così, se un attaccante ruba l'intera tabella `remember_tokens`, non ottiene i token spendibili — ottiene i loro hash, dai quali non può risalire ai token originali. Il furto del database non basta a impersonare nessuno. Nota anche `on delete cascade` sul vincolo: quando un utente viene cancellato, i suoi token spariscono automaticamente, senza codice da ricordarsi di scrivere. E i campi `user_agent`, `ip_address`, `expires_at` servono per tracciabilità e scadenza: un token non vale per sempre.

## Creare il cookie

`saveRememberMe()` genera selector e token con `random_bytes()`, salva l'hash SHA-256 e invia il cookie:

```php
function saveRememberMe(mysqli $conn, int $userId): bool
{
    $selector = base64url_encode(random_bytes(12));
    $token = base64url_encode(random_bytes(33));
    $tokenHash = hash('sha256', $token);
    $ttl = getConfig('rememberMeTTL');
    $expiresAt = (new DateTimeImmutable('+' . $ttl . ' seconds'))->format('Y-m-d H:i:s');
    $ip = $_SERVER['REMOTE_ADDR'];
    $userAgent = mb_substr($_SERVER['HTTP_USER_AGENT'], 0, 255);
    $sql = 'INSERT INTO remember_tokens (user_id, token_hash, selector, expires_at, ip_address, user_agent) VALUES (?,?,?,?,?,?)';
```

Codice completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-24/it/parte-06/cap-24/listing-02.php)

Sorgente reale: [`includes/auth.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

Selector e token nascono entrambi da `random_bytes()`, la stessa funzione crittograficamente sicura del token CSRF nel Capitolo 22 — perché anche qui prevedere il valore significa poterlo falsificare. Guarda cosa entra nel database e cosa no: viene inserito `$tokenHash`, l'impronta, **non** `$token`. Il token in chiaro, quello che serve davvero per l'auto-login, esiste solo per un istante dentro questa funzione, il tempo di metterlo nel cookie; poi PHP lo dimentica e nel database resta solo l'hash. È la stessa asimmetria delle password: il sistema conserva abbastanza per **verificare** un segreto, mai abbastanza per **ricostruirlo**.

La parte finale invia al browser il valore completo:

```php
$value = $selector . ':' . $token;
$cookieName = getConfig('rememberMeCookieName');

$cookieOptions = getRememberCookieOpts();
setcookie($cookieName, $value, $cookieOptions);

return $res;
```

Codice completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-24/it/parte-06/cap-24/listing-03.php)

Sorgente reale: [`includes/auth.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

Nel cookie va `selector:token`: il selector che il database conosce, e il token in chiaro di cui il database ha solo l'hash. È l'unico momento in cui il token viaggia in chiaro, ed è inevitabile — il browser deve pur riceverlo per poterlo restituire dopo. Da qui in avanti tutto il gioco è proteggere questo cookie, ed è quello che fanno le opzioni del prossimo paragrafo.

## Opzioni del cookie

Il cookie è `HttpOnly`, `SameSite=Strict` e dura quanto il TTL configurato:

```php
function getRememberCookieOpts(): array
{
    $ttl = getConfig('rememberMeTTL');
    $secure = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off');

    return [

        'expires' => time() + $ttl,
        'path' => '/',
        'domain' => '',
        'secure' => $secure,
        'httponly' => true,
        'samesite' => 'Strict'
    ];
}
```

Codice completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-24/it/parte-06/cap-24/listing-04.php)

Sorgente reale: [`includes/auth.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

Sono le stesse difese che abbiamo visto sul cookie di sessione nel Capitolo 22, e qui contano ancora di più, perché questo cookie vive per settimane invece che per la durata di una scheda del browser. `httponly => true` lo rende invisibile a JavaScript, così un attacco XSS non può leggerlo ed esfiltrarlo — cruciale per un cookie a lunga vita. `secure` lo confina a HTTPS in produzione, dove il valore diventa `true` da solo. E qui `samesite => 'Strict'`, più restrittivo del `'Lax'` della sessione: il cookie di remember me non viene inviato **mai** su richieste che partono da altri siti, nemmeno sulle navigazioni normali. Ha senso — è un cookie che serve solo per l'auto-login all'ingresso nel nostro sito, non c'è motivo che viaggi in nessun altro contesto, e chiudere del tutto quella porta è gratis. Più a lungo vive un cookie, più stretta deve essere la sua configurazione.

## Auto-login

`tryAutoLogin()` viene chiamata in `index.php` prima del controllo `is_user_logged_in()`:

```php
function tryAutoLogin(): void
{
    if (!empty($_SESSION['user_logged_in'])) {
        return;
    }
    $cookieName = getConfig('rememberMeCookieName');

    $cookie = $_COOKIE[$cookieName] ?? '';

    if (!$cookie || !str_contains($cookie, ':')) {
        return;
    }
    [$selector, $token] = explode(':', $cookie);
```

Codice completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-24/it/parte-06/cap-24/listing-05.php)

Sorgente reale: [`includes/auth.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

Ecco il protocollo in azione, in senso inverso rispetto alla creazione. La funzione parte con un *fail fast*: se c'è già una sessione attiva, non c'è niente da fare, esce subito. Altrimenti legge il cookie e lo spezza sui due punti nelle sue due parti, `$selector` e `$token`. Il selector servirà a trovare la riga, il token a dimostrarne il possesso.

La query unisce token e utente, così l'auto-login fallisce se l'utente non esiste più:

```php
$conn = getConnection();
$st = $conn->prepare(
    'SELECT  t.id,t.expires_at,t.token_hash, u.id as uid, u.email, u.username, u.role_type FROM remember_tokens as t INNER JOIN users as u ON t.user_id=u.id WHERE selector=?'
);
$st->bind_param('s', $selector);
$res = $st->execute();
```

Codice completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-24/it/parte-06/cap-24/listing-06.php)

Sorgente reale: [`includes/auth.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

La ricerca avviene **sul selector**, non sul token — è questo il motivo per cui il protocollo usa due valori. Il selector è indicizzato e univoco, quindi il database trova la riga in modo diretto ed efficiente. E naturalmente è un prepared statement con il selector legato come parametro: siamo nella Parte VI, la regola dell'SQL vale anche qui. La `JOIN` con la tabella `users` fa una cosa intelligente in un colpo solo: recupera i dati dell'utente e, se quell'utente nel frattempo è stato cancellato, non restituisce alcuna riga — l'auto-login fallisce da sé, senza controlli aggiuntivi.

Il confronto usa l'hash del token ricevuto:

```php
$calcHash = hash('sha256', $token);
if (!hash_equals($row['token_hash'], $calcHash)) {
    deleteRememberTokenById($row['id']);
    clearRememberMe();
    return;
}
```

Codice completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-24/it/parte-06/cap-24/listing-07.php)

Sorgente reale: [`includes/auth.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

Trovata la riga tramite il selector, si verifica il token: si calcola l'hash SHA-256 del token ricevuto dal cookie e lo si confronta con quello salvato nel database. Il confronto passa da `hash_equals()`, la funzione a tempo costante del Capitolo 22, per lo stesso motivo — impedire il timing attack sul confronto del segreto. Se gli hash non coincidono, qualcosa non va: il token è scaduto, manomesso, o è un tentativo di indovinare. La reazione è drastica e giusta: si **cancella** la riga (`deleteRememberTokenById`) e si pulisce il cookie. Un token sospetto non viene solo rifiutato, viene distrutto — meglio costringere l'utente legittimo a un nuovo login che lasciare in giro un token su cui qualcuno sta lavorando.

## Rotazione

Dopo un auto-login riuscito, il token viene ruotato:

```php
function rotateRememberToken(mysqli $conn, int $id): void
{
    $token = base64url_encode(random_bytes(33));
    $tokenHash = hash('sha256', $token);
    $ttl = getConfig('rememberMeTTL');
    $expiresAt = (new DateTimeImmutable('+' . $ttl . ' seconds'))->format('Y-m-d H:i:s');
    $sql = 'SELECT selector FROM remember_tokens WHERE id=?';
```

Codice completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-24/it/parte-06/cap-24/listing-08.php)

Sorgente reale: [`includes/auth.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

Questa è la parte che eleva il meccanismo da "funzionante" a "robusto", ed è quella che i tutorial saltano quasi sempre. Dopo ogni auto-login riuscito, il token usato viene **buttato e sostituito** con uno nuovo: nuovo `random_bytes()`, nuovo hash, nuova scadenza. Perché? Perché riduce drasticamente la finestra utile di un token rubato. Immagina che un attaccante riesca a copiare il cookie di remember me. Senza rotazione, quel cookie vale per settimane, per tutta la durata del TTL. Con la rotazione, appena il proprietario legittimo torna sul sito e fa auto-login, il token cambia — e la copia in mano all'attaccante diventa carta straccia. Ancora meglio: se è l'attaccante a usare per primo il token rubato, sarà il *legittimo* proprietario a ritrovarsi con un token non più valido, un segnale che qualcosa non va. La rotazione trasforma un token persistente da chiave permanente a chiave usa-e-rinnova.

## Revoca al logout

Il logout cancella il cookie, revoca il token del dispositivo corrente (o tutti i token dell'utente) e infine distrugge la sessione:

```php
clearRememberMe();
if ($fromAll) {
    revokeAllRememberMeTokens(get_user_id());
} else {
    revokeDeviceRememberMeToken(get_user_id());
}
$_SESSION = [];
$p = session_get_cookie_params();
setcookie(session_name(), '', time() - 4200, $p['path'], $p['domain'], $p['secure'], $p['httponly']);
session_destroy();

redirect('/login.php');
```

Attenzione all'ordine, perché sono tre operazioni distinte e servono tutte e tre. `$_SESSION = []` svuota l'array in memoria per la richiesta corrente, ma da solo non cancella nulla sul server. La `setcookie()` con scadenza nel passato dice al browser di buttare via il cookie di sessione: senza questo passaggio il browser continuerebbe a inviare un ID di sessione ormai inutile. E `session_destroy()` elimina i dati della sessione sul server. Fermarsi a `$_SESSION = []` è l'errore classico: l'utente sembra disconnesso, ma il file di sessione resta sul server e il cookie resta nel browser, quindi quell'ID è ancora spendibile.

Codice completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-24/it/parte-06/cap-24/listing-09.php)

Sorgente reale: [`controller/logout.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/controller/logout.php).

C'è un dettaglio di prodotto, oltre che di sicurezza, in quel `if ($fromAll)`. Il logout normale revoca solo il token del **dispositivo corrente**: se sei loggato sul portatile e sul telefono, uscire dal portatile non ti butta fuori dal telefono. Ma l'opzione `fromAll` revoca **tutti** i token dell'utente in un colpo solo — è il classico "disconnetti tutti i dispositivi" che offri quando qualcuno teme che l'account sia compromesso. Poterlo fare è possibile solo perché ogni token è una riga separata nel database, collegata all'utente: revocarli tutti è un `DELETE WHERE user_id=?`. Ecco perché la revoca è così esplicita:

```php
function revokeAllRememberMeTokens(int $userId): void
{
    $conn = getConnection();
    $st = $conn->prepare('DELETE FROM remember_tokens WHERE user_id=?');
    $st->bind_param('i', $userId);
    $st->execute();
    $st->close();
}
```

Codice completo: [listing-10.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-24/it/parte-06/cap-24/listing-10.php)

Sorgente reale: [`includes/auth.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/auth.php).

Un `DELETE` con il `user_id` legato come parametro, e tutti i token dell'utente spariscono. La revoca è possibile perché lo stato vive nel **database**, non solo nel cookie: potendo cancellare la riga, puoi invalidare un accesso quando vuoi. È la differenza sostanziale rispetto a salvare le credenziali nel cookie, dove non avresti alcun modo di "richiamare" un token già distribuito.

## In sintesi

Remember me non è una password salvata in un cookie — è un **protocollo**, e ora sai perché ogni suo pezzo esiste. Il **selector pubblico** trova la riga in fretta; il **token segreto** dimostra il possesso; l'**hash nel database** fa sì che un furto della tabella non produca token spendibili; la **scadenza** limita la durata; il **cookie `HttpOnly`, `Secure`, `SameSite=Strict`** protegge il segreto in transito e a riposo; l'**auto-login** verifica con `hash_equals()`; la **rotazione** accorcia la vita di un token rubato; la **revoca** — di un dispositivo o di tutti — è possibile perché lo stato vive nel database. Il repository UMS mostra l'intero ciclo in codice procedurale: nella Parte IX gli stessi principi si ritrovano in un servizio dedicato, ma il protocollo è esattamente questo. Se hai capito perché servono due valori invece di uno, e perché si salva l'hash e non il token, hai capito la parte difficile.
