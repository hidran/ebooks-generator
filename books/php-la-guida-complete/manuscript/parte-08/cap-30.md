# 30. Eccezioni, error handler e Sentry

Gli errori non sono tutti uguali, e saperli distinguere è metà del mestiere. Alcuni sono **bug** del codice — una svista da correggere. Altri sono **condizioni previste**: un file che manca, un record non trovato, un input non valido, un servizio esterno momentaneamente irraggiungibile. Non sono la stessa cosa e non vanno trattati allo stesso modo: i primi vanno resi visibili il prima possibile per essere corretti, i secondi vanno gestiti con grazia perché fanno parte del funzionamento normale. Le **eccezioni** e gli **handler** di PHP sono gli strumenti per farlo, e questo capitolo li mette in fila fino ad arrivare al monitoraggio degli errori in produzione con Sentry.

## `try`, `catch` e `finally`

Il blocco `try/catch/finally` è la struttura base per gestire un'operazione che può fallire:

```php
<?php
try {
    $pdo = new PDO($dsn, $user, $password);
} catch (PDOException $e) {
    echo "Connessione non riuscita";
} finally {
    // codice eseguito comunque
}
```

Codice completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-30/it/parte-08/cap-30/listing-01.php)


I tre blocchi hanno ruoli distinti. Nel `try` metti il codice che *potrebbe* fallire — qui l'apertura della connessione al database. Il `catch` intercetta un tipo specifico di eccezione, `PDOException`, e decide cosa fare quando quel fallimento avviene. Il `finally` è il meno ovvio ma spesso il più utile: viene eseguito **in ogni caso**, sia che il `try` sia andato a buon fine, sia che sia scattato il `catch`. È il posto dove liberare risorse che vanno chiuse comunque — un file aperto, un lock, una transazione — perché ti garantisce che quel codice giri qualunque strada prenda l'esecuzione.

## Lanciare eccezioni

Un'eccezione la puoi anche **sollevare** tu, con `throw`, quando rilevi una condizione che il codice non sa o non deve gestire lì:

```php
<?php
function divide(float $a, float $b): float
{
    if ($b === 0.0) {
        throw new InvalidArgumentException("Divisione per zero");
    }

    return $a / $b;
}
```

Codice completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-30/it/parte-08/cap-30/listing-02.php)


Il punto chiave è cosa succede dopo il `throw`: l'eccezione **interrompe** il flusso normale e **risale** la catena delle chiamate finché non trova un `catch` capace di gestirla. È un salto verso l'alto, non un valore di ritorno. Ed è proprio questa la differenza rispetto ai vecchi codici di errore restituiti come valore: un valore di ritorno il chiamante può ignorarlo per distrazione e tirare avanti con un dato sbagliato; un'eccezione no, non puoi far finta di niente — o qualcuno la cattura, o l'applicazione si ferma. Il fallimento diventa impossibile da ignorare in silenzio. Qui uso `InvalidArgumentException`, una delle eccezioni standard di PHP pensata proprio per gli argomenti non validi.

## Eccezioni custom

Oltre a quelle standard, puoi definire eccezioni **tue**, estendendo una classe base come `RuntimeException`:

```php
<?php
class UserNotFoundException extends RuntimeException
{
}

function find_user(int $id): array
{
    $user = null;

    if (!$user) {
        throw new UserNotFoundException("Utente $id non trovato");
    }

    return $user;
}
```

Codice completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-30/it/parte-08/cap-30/listing-03.php)


A prima vista una classe vuota che estende `RuntimeException` sembra inutile — non aggiunge codice. Ma aggiunge la cosa più importante: un **tipo**. E il tipo permette di distinguere gli errori e catturarli in modo selettivo:

```php
<?php
try {
    $user = find_user(10);
} catch (UserNotFoundException $e) {
    http_response_code(404);
}
```

Codice completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-30/it/parte-08/cap-30/listing-04.php)


Qui il `catch` intercetta **solo** `UserNotFoundException` e la traduce in un 404, la risposta HTTP giusta per "risorsa non trovata". Qualunque altra eccezione — un errore di database, un bug — non viene catturata da questo blocco e continua a risalire, dove verrà gestita diversamente. È questo il valore delle eccezioni custom: dare un nome preciso alle condizioni di errore del tuo dominio, così che ognuna possa essere trattata come merita. Nel progetto MVC della Parte IX vedrai un intero insieme di eccezioni di dominio costruite esattamente su questo principio.

## Error handler

C'è una zona d'ombra: oltre alle eccezioni, PHP ha un vecchio sistema di **warning**, **notice** e **deprecation** che non sono eccezioni e, di default, non fermano nulla — al massimo stampano una riga. Puoi però convertirli in eccezioni con un error handler:

```php
<?php
set_error_handler(function (int $severity, string $message, string $file, int $line): bool {
    throw new ErrorException($message, 0, $severity, $file, $line);
});
```

Codice completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-30/it/parte-08/cap-30/listing-05.php)


Registrando questa funzione, ogni warning che PHP emetterebbe viene trasformato in un'`ErrorException` e immesso nel sistema delle eccezioni, dove puoi catturarlo come tutti gli altri. In sviluppo è preziosissimo: invece di ignorare un warning che segnala un problema reale (un indice di array mancante, una variabile non definita), **fallisci subito** e lo vedi. È di nuovo il principio del *fail loud* — un problema visibile all'istante costa molto meno di uno che si nasconde e riaffiora giorni dopo, lontano dalla causa.

## Exception handler globale

E se un'eccezione non viene catturata da nessun `catch`? Serve un'ultima rete di sicurezza, l'**exception handler globale**:

```php
<?php
set_exception_handler(function (Throwable $e): void {
    error_log($e);

    http_response_code(500);
    echo "Errore interno";
});
```

Codice completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-30/it/parte-08/cap-30/listing-06.php)


Questo handler viene invocato per qualunque eccezione arrivi in cima senza essere stata gestita. Fa tre cose sensate: registra l'errore nel log (`error_log`), imposta lo stato HTTP 500 e mostra all'utente un messaggio pulito invece di uno stack trace. Attenzione però a non fraintenderne il ruolo: è l'**ultima** difesa, non la strategia. Non deve sostituire la gestione locale degli errori previsti — quelli li catturi vicino a dove nascono, come il 404 di prima. L'handler globale c'è per ciò che *non* avevi previsto, e il suo compito è evitare che un imprevisto si trasformi in una schermata tecnica sputata in faccia all'utente.

## Ambiente sviluppo e produzione

Ed eccoci al punto più delicato per la sicurezza. Il comportamento degli errori deve essere **opposto** tra sviluppo e produzione. In sviluppo vuoi vedere tutto:

```php
<?php
ini_set("display_errors", "1");
error_reporting(E_ALL);
```

Codice completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-30/it/parte-08/cap-30/listing-07.php)


In produzione, invece, gli errori non devono **mai** essere mostrati all'utente: vanno spenti sullo schermo e scritti nei log:

```php
<?php
ini_set("display_errors", "0");
ini_set("log_errors", "1");
```

Codice completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-30/it/parte-08/cap-30/listing-08.php)


Non è una questione di pulizia estetica, è una **vulnerabilità** vera e propria. Uno stack trace mostrato in pagina rivela i percorsi assoluti del server, frammenti di query SQL, nomi di variabili, a volte credenziali di connessione: è una miniera d'oro per chi vuole attaccarti, che gli regala la mappa interna dell'applicazione. La regola è netta: in produzione l'utente vede un messaggio generico, tu leggi i dettagli nel log. Mai il contrario.

## Loggare con Sentry

Scrivere gli errori in un file di log va bene, ma su un server serio quei file crescono, si perdono, e nessuno li guarda finché non è troppo tardi. **Sentry** è un servizio che centralizza la raccolta di eccezioni ed errori in produzione: con Composer installi il pacchetto e inizializzi il client con un DSN, e da lì gli errori arrivano a una dashboard dove vengono raggruppati, contati e notificati. Il flusso concettuale è "cattura, invia, rilancia":

```php
<?php
try {
    // codice applicativo
} catch (Throwable $e) {
    // invia a Sentry
    throw $e;
}
```

Codice completo: [listing-09.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-30/it/parte-08/cap-30/listing-09.php)


Nota il `throw $e` finale: dopo aver segnalato l'errore a Sentry, lo **rilancia**, perché il compito qui non è nasconderlo o gestirlo — di quello si occupa già l'handler globale — ma *registrarlo*. E registrarlo **con contesto**: Sentry non salva solo il messaggio, ma l'URL richiesto, l'utente coinvolto, l'ambiente, la versione dell'applicazione. È la differenza tra sapere che "qualcosa è andato storto" e poter riprodurre esattamente il bug che un utente ha incontrato tre ore fa su una pagina che tu, in locale, non riesci a far fallire.

## In sintesi

Le eccezioni rendono i fallimenti **espliciti** e impossibili da ignorare in silenzio: usa le eccezioni custom per dare un nome ai casi di errore del tuo dominio e catturarli in modo selettivo, l'error handler per far emergere subito i warning in sviluppo, e l'exception handler globale come ultima difesa per l'imprevisto. In produzione non mostrare **mai** gli errori all'utente — sarebbe una falla di sicurezza — ma loggali, meglio ancora con un servizio come Sentry che li arricchisce di contesto. Il filo che lega tutto è un'idea di maturità professionale: un'applicazione solida non è quella che non sbaglia mai, ma quella che sa fallire in modo **controllato e osservabile**.
