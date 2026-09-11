# 23. Navigazione protetta e azioni basate sui ruoli

Nel repository `php-user-management-system` il login non passa da AJAX. Le richieste sono form POST tradizionali e redirect. Questo capitolo quindi si concentra su ciò che il codice pubblico implementa davvero: pagine protette, menu condizionale e azioni consentite in base al ruolo.

Il tema di fondo è uno solo, e lo hai già incontrato nei capitoli precedenti: l'**autorizzazione**. Ma qui lo vediamo da un'angolazione nuova, quella della **difesa in profondità**. Vedrai lo stesso permesso — "questo utente può modificare? può cancellare?" — controllato in più punti diversi dell'applicazione: quando si rende la pagina, quando si costruisce il menu, quando si mostrano i pulsanti della lista, e di nuovo dentro il controller. A prima vista sembra ripetizione inutile. Non lo è, ed è proprio il punto che questo capitolo deve chiarire: **ogni strato protegge una cosa diversa, e nessuno da solo basta**.

## Proteggere la pagina principale

`index.php` prova prima l'auto-login tramite remember me, poi verifica la sessione:

```php
require_once 'includes/acl.php';
require_once 'includes/auth.php';
tryAutoLogin();
if (!is_user_logged_in()) {
    redirect('login.php');
}
require_once 'includes/csrf.php';
```

Codice completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-23/it/parte-06/cap-23/listing-01.php)

Sorgente reale: [`index.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/index.php).

Il primo strato è il più esterno: prima ancora di produrre una sola riga di HTML, la pagina decide se l'utente ha il diritto di essere lì. La sequenza conta. Si tenta l'auto-login (che abbiamo visto nel Capitolo 24), così un utente con un cookie di remember me valido viene riconosciuto; poi si controlla `is_user_logged_in()` e, se la sessione non c'è, `redirect()` porta al login e la richiesta finisce lì. Il dettaglio importante è che questo controllo sta **prima del rendering**. Se l'utente non è autorizzato non deve vedere nemmeno la pagina parziale — niente header, niente tabella vuota, niente. Mettere il controllo in cima, e non a metà pagina, garantisce che nessun frammento riservato raggiunga il browser di chi non ha diritto di vederlo.

## Leggere i dati dell'utente

Le funzioni ACL leggono lo stato dalla sessione:

```php
function is_user_logged_in(): bool
{
    return !empty($_SESSION['user_logged_in']);
}

function get_user_login_data(): array
{
    return $_SESSION['user_data'] ?? [];
}

function get_user_role(): string
{
    return get_user_login_data()['role_type'] ?? 'user';
}
```

Codice completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-23/it/parte-06/cap-23/listing-02.php)

Sorgente reale: [`includes/acl.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/includes/acl.php).

C'è un principio in queste tre funzioni che vale più di quanto sembri: la fonte dell'identità dell'utente è **una sola**, la sessione. Il ruolo si legge da `$_SESSION['user_data']['role_type']`, mai da un parametro `GET` o `POST`. È fondamentale capire perché. La sessione vive sul **server** ed è stata popolata al login, dopo la verifica della password: l'utente non può modificarla. Un parametro `GET` o `POST`, invece, è scritto dal client e l'utente può metterci quello che vuole. Se anche solo in un punto il codice decidesse i permessi guardando `$_GET['role']` invece della sessione, chiunque potrebbe promuoversi ad amministratore aggiungendo `?role=admin` alla URL. Una sola fonte di verità per l'identità, e quella fonte è sotto il controllo del server: è la fondazione su cui poggiano tutti gli strati successivi. Nota anche il default `'user'` in `get_user_role()` — se manca il dato, si assume il ruolo meno privilegiato, il *fail closed* che abbiamo già discusso nel Capitolo 22.

## Menu condizionale

La navbar mostra il menu applicativo solo se l'utente è loggato:

```php
<?php
if (is_user_logged_in()): ?>
    <ul class="navbar-nav me-auto mb-2 mb-md-0">
        <li class="nav-item">
            <a class="nav-link <?= $indexActive ?>" aria-current="page" href="<?= $indexPage ?>"><i
                        class="fa-solid fa-users"></i>Users</a>
        </li>
```

Codice completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-23/it/parte-06/cap-23/listing-03.php)

Sorgente reale: [`view/nav.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/view/nav.php).

Il secondo strato è il menu. Mostrare le voci applicative solo a chi è loggato è **usabilità**: non ha senso proporre "Utenti" o "Nuovo utente" a un visitatore che deve ancora autenticarsi. Ma attenzione a non confondere i piani: questo è un abbellimento dell'interfaccia, **non** una misura di sicurezza. Il menu decide cosa l'utente *vede*, non cosa l'utente *può fare*. Un link assente non impedisce a nessuno di digitare a mano l'URL corrispondente. La sicurezza vera non è qui — è nei controller, e ci arriviamo tra due paragrafi.

## Azioni nella lista

La lista utenti mostra update e delete in base al ruolo:

```php
<?php
if (user_can_update()): ?>
    <div class="row">

        <div class="col-6">
            <a class="btn btn-success" href="?id=<?= $user['id'] ?>&action=edit&<?= $navParams ?>">
                <i class="fa fa-pen"></i>
                UPDATE
            </a>
        </div>
```

Codice completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-23/it/parte-06/cap-23/listing-04.php)

Sorgente reale: [`view/userList.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/view/userList.php).

Il terzo strato è più fine del menu: non decide se mostrare *l'applicazione*, ma se mostrare le singole *azioni*. Il pulsante UPDATE appare solo se `user_can_update()`, e più avanti nella stessa view il pulsante DELETE appare solo se `user_can_delete()`. Un utente con ruolo `user` vede l'elenco ma non i pulsanti d'azione; un `editor` vede UPDATE; solo un `admin` vede anche DELETE. È esattamente ciò che si osserva nella figura del Capitolo 20, dove l'amministratore ha entrambi i pulsanti accanto a ogni riga.

E vale, per la terza volta, la stessa avvertenza: nascondere il pulsante è comodità, non sicurezza. Non fidarti mai del fatto che un pulsante non compaia. L'URL dell'azione esiste comunque, e va protetto altrove.

## Controller protetto

`controller/updateRecord.php` rifiuta chi non è loggato o non può aggiornare:

```php
require_once '../includes/acl.php';
if (!is_user_logged_in() || !user_can_update()) {
    redirect('../login.php');
}

require '../model/User.php';
$action = getParam('action');
switch ($action) {
```

Codice completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-23/it/parte-06/cap-23/listing-05.php)

Sorgente reale: [`controller/updateRecord.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/controller/updateRecord.php).

Ecco lo strato che conta davvero — quello che i tre precedenti *non* possono sostituire. Qui, nel controller, sul server, prima di eseguire qualsiasi azione, si ricontrolla `is_user_logged_in()` e `user_can_update()`. Questa è la sicurezza vera. Adesso puoi vedere perché gli strati non sono ridondanti: il controllo nel menu e nella lista impedisce all'utente onesto di *vedere* cose che non lo riguardano, ma è il controllo nel controller a impedire all'utente malevolo di *fare* cose che non gli spettano. Il primo migliora l'esperienza, il secondo protegge il dato. Se ti chiedessi di eliminarne uno, elimineresti quelli nelle view — non questo. È la regola che ho ripetuto nel Capitolo 20 e che ripeto qui perché è l'errore concettuale più comune sull'autorizzazione: **il pulsante nascosto è cosmetica, il controllo nel controller è sicurezza**.

La cancellazione richiede un controllo ancora più stretto:

```php
case 'delete':
    if (!user_can_delete()) {
        redirect('../login.php');
    }

    $id = (int)getParam('id', 0);
    $user = getUserById($id);
```

Codice completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-23/it/parte-06/cap-23/listing-06.php)

Sorgente reale: [`controller/updateRecord.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/controller/updateRecord.php).

Nota la gradazione dei permessi. Per entrare nel controller basta `user_can_update()` — che vale per `editor` e `admin`. Ma il `case 'delete'` aggiunge un controllo **più stretto**, `user_can_delete()`, che vale solo per `admin`. È il principio del **minimo privilegio** applicato all'azione: un editor può modificare, ma non distruggere. L'azione più pericolosa richiede il permesso più alto, e il controllo specifico sta dentro il ramo che esegue quell'azione, così non c'è modo di arrivare alla cancellazione con i soli permessi di modifica.

## Logout via POST

Il logout usa POST e CSRF, non un semplice link GET:

```php
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(419);
    exit('Invalid request method');
}
$fromAll = getParam('fromAll');
if (!csrf_validate(post_string('csrf_token'))) {
    http_response_code(419);
    exit('Invalid token');
}
```

Codice completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-23/it/parte-06/cap-23/listing-07.php)

Sorgente reale: [`controller/logout.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/controller/logout.php).

Anche il logout, che sembra l'azione più innocua del mondo, ha le sue regole. Il progetto rifiuta le richieste che non sono POST (`http_response_code(419)`) e valida il token CSRF prima di procedere. Perché tanta cautela per "uscire"? Perché il logout **cambia lo stato** — termina una sessione — e le azioni che cambiano stato non devono mai essere esposte come semplici link GET. Se il logout fosse un `<a href="logout.php">`, un attaccante potrebbe mettere in una pagina un'immagine `<img src="https://ilnostrosito/logout.php">` e il tuo browser, caricandola, ti disconnetterebbe a tua insaputa. È un CSRF di logout: fastidioso più che dannoso, ma dello stesso identico stampo dell'attacco che abbiamo studiato nel Capitolo 22. La regola è netta e vale per **ogni** azione che modifica qualcosa — login, logout, creazione, cancellazione: si passa per POST, e si valida il token CSRF. I GET sono per leggere, i POST per cambiare.

## In sintesi

Il progetto UMS non implementa login AJAX: implementa un flusso classico e solido, e la sua lezione più importante è la **difesa in profondità**. L'identità ha una **sola fonte**, la sessione, mai un parametro del client. Il permesso viene poi controllato a più strati, e ognuno ha un compito diverso: il controllo **prima del rendering** tiene fuori chi non è loggato; il **menu condizionale** e i **pulsanti d'azione** adattano l'interfaccia a ciò che l'utente può fare, ma sono usabilità; il **controllo nel controller**, sul server, è l'unico che protegge davvero il dato, con un requisito **più stretto** per l'azione più pericolosa. Infine, le azioni che cambiano stato passano per **POST con CSRF**, logout compreso.

Se dovessi ridurre tutto a una frase: gli strati nelle view servono all'utente onesto, il controllo nel controller serve contro quello malevolo — e siccome non sai in anticipo con quale dei due hai a che fare, li tieni tutti. Nella Parte IX questa logica sparsa in funzioni e view diventerà un middleware di autorizzazione, un punto unico attraversato da ogni richiesta; ma il principio della difesa in profondità resterà esattamente questo.
