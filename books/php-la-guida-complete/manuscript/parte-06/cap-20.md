# 20. CRUD, ricerca, ordinamento e paginazione

Nel repository `php-user-management-system` la lista utenti cresce in modo progressivo: prima mostra tutti i record, poi aggiunge ordinamento, ricerca, paginazione e infine le azioni di inserimento, aggiornamento ed eliminazione. È il capitolo in cui uno *script* diventa un'**applicazione**: non più una pagina che stampa una tabella, ma un insieme di funzioni che leggono parametri dalla request, li usano per costruire query e restituiscono viste diverse a seconda di cosa chiede l'utente.

Proprio perché è il primo pezzo che riceve input dall'esterno e lo trasforma in SQL, è anche il capitolo dove si annidano i primi rischi seri. Lo affronteremo in modo onesto: mostro il codice del progetto così com'è — procedurale, diretto, pensato per farti vedere il meccanismo — e nei punti in cui prende una scorciatoia che in produzione non va bene, mi fermo a spiegare perché e come si corregge.

![La lista utenti di UMS: intestazioni di colonna ordinabili, filtro di ricerca, selettore dei record per pagina e barra di paginazione. Qui i 47 utenti di esempio sono distribuiti su 5 pagine.](figures/cap-20/user-list-pagination.png)

## Leggere utenti con parametri

La funzione `getUsers()` riceve i parametri della pagina e costruisce la query:

```php
function getUsers(array $params = []): array
{
    $conn = getConnection();

    $records = [];

    $limit = $params['recordsPerPage'] ?? 10;
    $orderBy = $params['orderBy'] ?? 'id';
    $orderDir = $params['orderDir'] ?? 'DESC';
    $search = $params['search'] ?? '';
    $page = $params['page'] ?? 1;
    $start = $limit * ($page - 1);
    $sql = 'SELECT * FROM users';
```

Codice completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-20/it/parte-06/cap-20/listing-01.php)

Sorgente reale: [`functions.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/functions.php).

Cinque parametri, e ognuno arriva dalla **request**: `recordsPerPage` e `page` decidono quanti record leggere e da quale punto, `orderBy` e `orderDir` la colonna e il verso dell'ordinamento, `search` il testo da cercare. L'operatore `??` fornisce un default a ciascuno, così la funzione lavora anche alla prima visita, quando la URL non porta ancora nessun parametro. Fin qui tutto bene.

Il problema è cosa succede a questi valori subito dopo. Nel repository la query si completa così — e qui devo mostrarti il codice reale, perché è esattamente il punto su cui voglio farti ragionare:

```php
$sql .= " ORDER BY $orderBy $orderDir  LIMIT  $start,$limit ";
```

Quei quattro valori — `$orderBy`, `$orderDir`, `$start`, `$limit` — finiscono **dentro la stringa SQL per interpolazione diretta**. E se `search` è valorizzato, anche lui viene interpolato nel `WHERE`. Ogni volta che un dato che arriva dall'utente entra in una query concatenandolo come testo, devi accendere un allarme in testa: è la porta d'ingresso della **SQL injection**, la vulnerabilità più classica e più diffusa delle applicazioni web.

Facciamo l'esempio concreto. Immagina che `search` venga preso dalla URL e incollato dentro `WHERE username LIKE '%$search%'`. Un utente normale cerca `mario` e la query diventa `... LIKE '%mario%'`. Ma un attaccante non scrive `mario`: scrive `x' OR '1'='1`. La query risultante non cerca più un nome, contiene una **condizione logica iniettata** dall'esterno che il database esegue come se l'avessi scritta tu. Con payload più elaborati si arriva a leggere altre tabelle, estrarre gli hash delle password, in certi casi modificare o cancellare dati. Non è teoria: è il primo attacco che chiunque prova contro un form di ricerca.

"Ma io filtro l'input", potresti pensare. Nel progetto, prima di arrivare qui, `search` passa da `strip_tags(trim($search))`. Attenzione: `strip_tags()` rimuove i **tag HTML**, non ha niente a che vedere con l'SQL. Un apice singolo `'` — il carattere che serve per l'injection — passa indenne. Filtrare per un contesto (HTML) non protegge da un altro (SQL): ogni contesto ha le sue regole di *escaping*, e mescolarle dà una falsa sensazione di sicurezza. Questa, tra l'altro, è la ragione per cui la funzione gemella `getTotalUserCount()` che vedremo tra poco chiama almeno `real_escape_string()` sul termine di ricerca, mentre `getUsers()` non lo fa nemmeno: due funzioni nate insieme, con due livelli di protezione diversi. È proprio il tipo di incoerenza che un *prepared statement* elimina alla radice.

Vediamo allora la versione corretta. Il termine di ricerca va **legato come parametro**, non concatenato:

```php
function getUsers(array $params, array $allowedColumns): array
{
    $conn = getConnection();
    $limit   = (int) ($params['recordsPerPage'] ?? 10);
    $page    = max(1, (int) ($params['page'] ?? 1));
    $start   = $limit * ($page - 1);
    $search  = (string) ($params['search'] ?? '');

    // orderBy è un IDENTIFICATORE, non un valore: va messo a whitelist
    $want    = $params['orderBy'] ?? 'id';
    $orderBy = in_array($want, $allowedColumns, true) ? $want : 'id';
    $orderDir = ($params['orderDir'] ?? 'DESC') === 'ASC' ? 'ASC' : 'DESC';

    $sql = 'SELECT * FROM users';
    $types = '';
    $values = [];
    if ($search !== '') {
        $sql .= ' WHERE fiscalcode LIKE ? OR email LIKE ? OR username LIKE ?';
        $like = '%' . $search . '%';
        $types = 'sss';
        $values = [$like, $like, $like];
    }
    $sql .= " ORDER BY $orderBy $orderDir LIMIT ?, ?";
    $types .= 'ii';
    $values[] = $start;
    $values[] = $limit;

    $stmt = $conn->prepare($sql);
    $stmt->bind_param($types, ...$values);
    $stmt->execute();
    $result = $stmt->get_result();

    $records = [];
    while ($row = $result->fetch_assoc()) {
        $records[] = $row;
    }
    return $records;
}
```

Guarda la differenza. Il testo di ricerca non tocca più la stringa SQL: al suo posto c'è un `?`, un **segnaposto**, e il valore vero viaggia separato tramite `bind_param()`. Il database riceve la struttura della query e i dati per due canali distinti, e non può più confondere un dato con un comando. Se l'attaccante scrive `x' OR '1'='1`, quel testo diventa semplicemente la stringa da cercare — il database prova a trovare un utente il cui username contiene letteralmente `x' OR '1'='1`, non ne trova, e restituisce zero righe. L'attacco si spegne senza fare danni. La ricerca legittima continua a funzionare esattamente come prima.

Un dettaglio che confonde tutti, e che merita di essere chiarito una volta per tutte: `$orderBy` e `$orderDir` **non possono** essere passati come `?`. I segnaposto dei prepared statement legano **valori** — un numero, una stringa, una data — non **identificatori** come i nomi di colonna o le parole chiave `ASC`/`DESC`. `ORDER BY ?` non funziona: il database si aspetta lì un nome di colonna, non un dato. La difesa corretta per gli identificatori è diversa e si chiama **whitelist**: si confronta il valore ricevuto con un elenco chiuso di colonne ammesse (`in_array($want, $allowedColumns, true)`) e, se non è nell'elenco, si ripiega su un default sicuro. La direzione si riduce a due sole possibilità, `ASC` o `DESC`, con lo stesso principio. Regola generale, tienila a mente: **i valori si legano, gli identificatori si mettono a whitelist**. È la distinzione che separa chi ha capito la SQL injection da chi la conosce solo per sentito dire.

Nel progetto enterprise della Parte IX questa logica finirà dentro un *repository* testabile, dove la costruzione della query è isolata e le colonne ammesse sono dichiarate in un punto solo. Ma il principio è identico a quello che hai appena visto: parametri per i valori, whitelist per gli identificatori.

## Ricerca e paginazione

Il conteggio totale usa una funzione separata. Serve per calcolare quante pagine mostrare:

```php
function getTotalUserCount(string $search = ''): int
{
    $conn = getConnection();

    $sql = 'SELECT COUNT(*) as total FROM users';
    if ($search) {
        $sql .= ' WHERE';
        if (is_numeric($search)) {
            $sql .= " id = $search OR age = $search";
        } else {
            $search = $conn->real_escape_string($search);
            $sql .= " fiscalcode like '%$search%' OR email like '%$search%' OR
             username like '%$search%'";
        }
    }
```

Codice completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-20/it/parte-06/cap-20/listing-02.php)

Sorgente reale: [`functions.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/functions.php).

Qui il progetto usa `real_escape_string()`, che è un passo avanti rispetto a `getUsers()`: la funzione fa l'*escape* dei caratteri speciali — l'apice `'` diventa `\'` — così il testo non può più chiudere la stringa e iniettare SQL. Funziona, ma vale la pena capire perché i prepared statement restano comunque la scelta migliore. L'*escaping* è una difesa che devi ricordarti di applicare **ogni volta**, su **ogni** variabile, con la funzione giusta per il tipo giusto: basta un `real_escape_string()` dimenticato in un punto e la porta si riapre. Il prepared statement, invece, separa dati e comandi per costruzione: non c'è niente da ricordarsi di fare. La differenza tra le due funzioni sorelle di questo progetto — una con l'escape, una senza — è la prova vivente di quanto sia fragile affidarsi alla memoria. Nota anche il ramo `is_numeric($search)`: lì il valore va nella query senza nemmeno l'escape, sul presupposto che se è numerico non può fare danni. È un presupposto che regge per il singolo carattere, ma è di nuovo il tipo di ragionamento caso-per-caso che i prepared statement rendono superfluo.

Al di là della sicurezza, c'è una scelta di **design** giusta e vale la pena riconoscerla: `getTotalUserCount()` è una funzione a parte, distinta da `getUsers()`. Perché contare le righe e leggerle sono due responsabilità diverse. La lista serve solo i record della pagina corrente — dieci righe, con `LIMIT` — mentre il conteggio deve sapere quanti record esistono **in totale**, ignorando il `LIMIT`, perché è quel numero a dirci quante pagine servono. Sono due domande diverse, quindi due query diverse, quindi due funzioni. È una piccola applicazione del principio di singola responsabilità: se avessi messo tutto in una funzione sola, avresti dovuto restituire due cose scollegate — le righe *e* il totale — e prima o poi qualcuno le avrebbe usate in modo confuso.

È il conteggio a rendere possibile la matematica della paginazione, che è più semplice di quanto sembri. Con `recordsPerPage` record per pagina, la pagina `page` deve saltare le righe delle pagine precedenti: `start = recordsPerPage * (page - 1)`. La pagina 1 parte da 0, la pagina 2 da 10, la pagina 3 da 20, e così via. La clausola `LIMIT start, recordsPerPage` dice al database "salta `start` righe, poi dammene `recordsPerPage`". Il numero totale di pagine è `ceil(totale / recordsPerPage)`: con 47 utenti e 10 per pagina vengono 5 pagine, l'ultima con solo 7 record. Tre formule, ed è tutta qui la paginazione che vedi in fondo alla lista.

![La stessa lista dopo una ricerca: la clausola `WHERE` riduce i risultati e i parametri di ricerca restano nei link di ordinamento e di paginazione.](figures/cap-20/search-filter.png)

Un dettaglio dell'esperienza d'uso che si vede nella figura: quando cerchi, i parametri di ricerca restano nei link delle colonne e nella barra di paginazione. Non è un caso — è codice che, in ogni link, ricostruisce la *query string* completa. Senza, cambiare pagina o riordinare azzererebbe la ricerca, e l'utente si troverebbe di colpo davanti a tutti i record. È il genere di dettaglio che distingue un'applicazione curata da un esercizio.

## Form unico per create e update

La view `userForm.php` decide se il form sta creando o aggiornando un utente:

```php
<?php

$action = 'store';
$buttonName = 'SAVE';
$formTile = 'INSERT USER';
if ($user && $user['id']) {
    $action = 'update';
    $buttonName = 'UPDATE';
    $formTile = 'UPDATE USER';
}
foreach ($user as &$value) {
    $value = htmlspecialchars($value ?? '');
}
?>
```

Codice completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-20/it/parte-06/cap-20/listing-03.php)

Sorgente reale: [`view/userForm.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/view/userForm.php).

Un **solo** form per due operazioni. La logica è semplice: se ci arriva un `$user` con un `id`, siamo in modifica e prepariamo azione, etichetta del pulsante e titolo di conseguenza; altrimenti siamo in creazione. È un'applicazione concreta del principio **DRY** (*Don't Repeat Yourself*): i campi del form — username, email, età, ruolo — sono identici nei due casi, e mantenere due form quasi uguali significherebbe correggere ogni modifica in due punti, con la certezza statistica di dimenticarne uno. Un form solo, che cambia solo le poche cose che davvero differiscono, è più corto da scrivere e più sicuro da mantenere.

La riga davvero importante è il `foreach` finale, ed è di nuovo una questione di sicurezza — stavolta di un'altra famiglia. Prima di reinserire i valori nei campi del form, ogni valore passa da `htmlspecialchars()`. Il motivo: questi dati arrivano dal **database**, ma nel database ci sono finiti perché *qualcuno li ha digitati*. Se un utente si fosse registrato con username `<script>alert(document.cookie)</script>`, stamparlo tale e quale dentro un attributo `value` del form eseguirebbe quello script nel browser di chiunque apra la pagina di modifica. È l'attacco **XSS** (*Cross-Site Scripting*), il cugino della SQL injection ma sul lato client. `htmlspecialchars()` converte i caratteri pericolosi nelle loro entità HTML — `<` diventa `&lt;`, `"` diventa `&quot;` — così il testo viene *mostrato* invece che *eseguito*.

Il principio da portarsi a casa è simmetrico a quello dell'SQL: **fai l'escape dei dati nel contesto in cui li inserisci**. Verso il database, parametri; verso l'HTML, `htmlspecialchars()`. E soprattutto: non fidarti mai di un dato solo perché "viene dal database" e non direttamente dall'utente. Nel database ci arriva comunque roba scritta da qualcuno, e quel qualcuno potrebbe non avere buone intenzioni.

## Salvare un nuovo utente

`storeUser()` usa prepared statement e salva la password con `password_hash()`:

```php
function storeUser(array $data): int
{
    $conn = getConnection();
    $sql = 'INSERT INTO users (username,email,fiscalcode,age,avatar, password,role_type) values( ?, ?, ?,?,?,?,?)';
    $stm = $conn->prepare($sql);
    $password = password_hash($data['password'], PASSWORD_DEFAULT);
    $stm->bind_param(
        'sssisss',
        $data['username'],
        $data['email'],
        $data['fiscalcode'],
        $data['age'],
        $data['avatar'],
        $password,
        $data['role_type']

    );
    $stm->execute();
```

Codice completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-20/it/parte-06/cap-20/listing-04.php)

Sorgente reale: [`model/User.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/model/User.php).

Qui il progetto fa le cose per bene, ed è utile confrontare questa funzione con la `getUsers()` di prima: dove la lettura prendeva la scorciatoia, la scrittura usa un prepared statement pieno. Sette segnaposto `?` nella query, sette valori passati a `bind_param()`, e nessun dato dell'utente che tocca la stringa SQL. Un `INSERT` è potenzialmente più pericoloso di una `SELECT` — scrive sul database — quindi è giusto che qui la disciplina sia rigorosa.

Il primo argomento di `bind_param()`, la stringa `'sssisss'`, è il pezzo che spiazza chi lo vede per la prima volta. È la dichiarazione dei **tipi**, un carattere per ogni segnaposto, nell'ordine: `s` per *string*, `i` per *integer*, `d` per *double*, `b` per *blob*. Qui: username stringa, email stringa, fiscalcode stringa, età **intero**, avatar stringa, password stringa, ruolo stringa — da cui `sssisss`. La stringa dei tipi e la lista dei valori devono corrispondere in numero e in ordine: se sbagli e dichiari `s` dove il valore è un intero, di solito non è un dramma, ma se scambi l'ordine dei valori scrivi l'email nella colonna del fiscalcode senza che PHP protesti. È l'unico punto fragile dei prepared statement con mysqli, e nella Parte IX vedremo che PDO offre un'alternativa con parametri **nominati** (`:username`) che elimina il problema del conteggio.

Nota anche che la password non viene mai salvata così com'è: passa da `password_hash()` prima di entrare nel `bind_param()`, esattamente come abbiamo spiegato nel Capitolo 22. Nel database finisce l'hash, mai la password in chiaro.

## Aggiornare un utente

L'update costruisce dinamicamente i campi opzionali per password e ruolo:

```php
function updateUser(array $data, int $id): bool
{
    $conn = getConnection();
    $types = 'sssis';
    $values = [
        $data['username'],
        $data['email'],
        $data['fiscalcode'],
        $data['age'],
        $data['avatar']
    ];
    $sql = 'UPDATE users SET username = ?, email = ?, fiscalcode = ?, age = ?,avatar=? ';
    if ($data['password']) {
        $sql .= ', password = ? ';
        $types .= 's';
        $values[] = password_hash($data['password'], PASSWORD_DEFAULT);
    }
```

Codice completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-20/it/parte-06/cap-20/listing-05.php)

Sorgente reale: [`model/User.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/model/User.php).

L'update ha un requisito in più rispetto all'insert: alcuni campi sono **opzionali**. Se l'utente in fase di modifica lascia vuoto il campo password, non vogliamo sovrascrivere l'hash esistente con una stringa vuota — vogliamo lasciare la password com'era. Lo stesso vale per il ruolo. La soluzione del progetto è costruire la query **pezzo per pezzo**: si parte dai campi sempre presenti (`username`, `email`, `fiscalcode`, `age`, `avatar`), e solo se `$data['password']` è valorizzato si aggiunge `, password = ?` alla query, `s` alla stringa dei tipi e il nuovo hash alla lista dei valori.

Il punto delicato di questo schema è che **tre cose devono restare allineate**: il testo SQL, la stringa dei tipi e l'array dei valori. Ogni volta che aggiungi un `?` alla query devi aggiungere il carattere di tipo corrispondente *e* il valore, nello stesso ordine. Il codice lo fa con cura — nota come i tre aggiornamenti (`$sql .=`, `$types .=`, `$values[] =`) viaggiano sempre insieme, in blocco. È un pattern che funziona ma richiede disciplina: è esattamente la ripetitività che nella Parte IX un *query builder* o un ORM tolgono di mezzo, generando i segnaposto e i tipi in automatico. Qui, allo stato procedurale, vederlo a mano ti fa capire cosa quelle astrazioni fanno per te.

Una nota di metodo che vale oltre questa funzione: conviene validare bene `$data` *prima* di arrivare al model. Il model dovrebbe ricevere dati già coerenti — età che è davvero un numero, email che ha davvero la forma di un'email — e occuparsi solo di salvarli. Mescolare validazione e persistenza nella stessa funzione è un'altra di quelle scorciatoie che sembrano innocue e poi rendono il codice difficile da testare e da riusare.

## Controller delle azioni

Il controller `updateRecord.php` protegge le azioni e indirizza `store`, `update` e `delete`:

```php
<?php

declare(strict_types=1);
require_once '../includes/session.php';
require '../functions.php';
require_once '../includes/acl.php';
if (!is_user_logged_in() || !user_can_update()) {
    redirect('../login.php');
}

require '../model/User.php';
$action = getParam('action');
switch ($action) {
```

Codice completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-20/it/parte-06/cap-20/listing-06.php)

Sorgente reale: [`controller/updateRecord.php` a `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/controller/updateRecord.php).

Il controller è la porta d'ingresso delle azioni che modificano dati, e la prima cosa che fa — prima ancora di guardare *quale* azione — è il controllo di accesso: `is_user_logged_in()` verifica l'autenticazione, `user_can_update()` l'autorizzazione. Se manca una delle due, `redirect()` e la richiesta finisce lì. Solo dopo aver superato questo cancello si carica il model e si smista l'azione con lo `switch`.

L'ordine è la cosa importante, ed è la stessa logica del *fail fast* che abbiamo visto nel Capitolo 22: **prima autorizzi, poi agisci**. Non un solo record viene toccato prima che il controllo sia passato. Metterlo in cima, e non sparso dentro i singoli `case`, garantisce che nessun ramo dello `switch` possa essere raggiunto per sbaglio senza controllo.

E qui torna il punto che ho anticipato nel capitolo precedente e che vale la pena martellare, perché è l'errore concettuale più comune sull'autorizzazione: **il controller non deve fidarsi della view**. Nel Capitolo 23 vedremo che il menu nasconde i pulsanti "modifica" ed "elimina" agli utenti senza i permessi. Ma nascondere un pulsante è solo cosmetica: l'URL `controller/updateRecord.php?action=delete&id=5` esiste comunque, e chiunque può digitarlo a mano nella barra degli indirizzi o costruirlo con `curl`. Se l'unica difesa fosse il pulsante nascosto, un utente normale potrebbe cancellare record semplicemente indovinando la URL. È il controllo *qui, nel controller*, sul server, a rendere l'azione davvero protetta. La view migliora l'esperienza; il controller garantisce la sicurezza. Quando devi sceglierne uno solo, scegli sempre il controller.

## In sintesi

Questo capitolo è il primo salto vero da script ad applicazione, e mette in fila i temi che ci accompagneranno fino alla fine del libro. La **lettura parametrica** (`getUsers`) ci ha costretti ad affrontare la SQL injection: i valori si legano con i prepared statement, gli identificatori come `ORDER BY` si mettono a whitelist — mai concatenare input dell'utente nella stringa SQL. Il **conteggio separato** (`getTotalUserCount`) ci ha dato la matematica della paginazione e un esempio di responsabilità ben divise. Il **form unico** per create e update ha mostrato il principio DRY e l'escaping con `htmlspecialchars()` contro l'XSS. Le funzioni di **scrittura** (`storeUser`, `updateUser`) hanno usato i prepared statement come si deve, con la stringa dei tipi e la costruzione dinamica dei campi opzionali. Il **controller** ha messo l'autorizzazione prima dell'azione, sul server, senza fidarsi di ciò che la view mostra o nasconde.

Il filo che li lega è uno solo: **ogni dato che attraversa un confine — dalla request alla query, dal database all'HTML — va trattato secondo le regole del contesto in cui entra**. Il repository UMS lo fa in forma procedurale, con qualche incoerenza che ho preferito mostrarti invece di nascondere, perché è imparando a riconoscerle che si diventa capaci di correggerle. Nella Parte IX gli stessi meccanismi torneranno dentro repository, query builder e validazione centralizzata: spariranno le scorciatoie, ma i principi resteranno esattamente questi.
