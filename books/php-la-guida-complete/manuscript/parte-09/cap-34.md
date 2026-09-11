# 34. Autenticazione, test e quality gate

Un progetto enterprise non è credibile perché "funziona sul mio computer". È credibile perché ha controlli ripetibili: test automatici, style check, analisi statica e refactoring guidato. Nel repository `phpenterpriseblog` questi controlli arrivano subito dopo la fondazione MVC.

Il punto non è aggiungere strumenti per sentirsi più professionali. Il punto è costruire un sistema in cui un cambiamento può essere fatto, verificato e corretto senza affidarsi alla memoria dello sviluppatore. In un blog MVC piccolo puoi cliccare due pagine e convincerti che tutto vada bene. In un progetto che cresce, quel metodo non scala: dimentichi un caso limite, cambi una query e rompi una pagina lontana, aggiorni PHP e scopri troppo tardi che una firma non è più coerente. I quality gate servono a ridurre questo rischio prima del deploy.

Da architetto PHP, io leggo questi strumenti come livelli diversi dello stesso controllo:

- PHPUnit verifica il comportamento che abbiamo deciso;
- PHP_CodeSniffer e Slevomat verificano la disciplina del codice;
- PHPStan verifica la coerenza dei tipi e dei contratti;
- Rector applica refactoring meccanici in modo ripetibile;
- Composer mette tutto dentro comandi eseguibili anche dalla CI.

Nessuno di questi strumenti sostituisce il giudizio tecnico. Insieme, però, impediscono che il progetto dipenda solo dall'attenzione del momento.

## Autenticazione come servizio

Nel progetto UMS la logica di login cresceva dentro funzioni e controller. Nel blog la estraiamo in `AuthService`, così possiamo testarla senza browser e senza database reale:

```php
<?php

declare(strict_types=1);

final class AuthService
{
    public function __construct(private readonly UserRepositoryInterface $users)
    {
    }

    public function verifySignup(
        string $email,
        string $password,
        string $token,
        string $sessionToken
    ): AuthResult {
        if (!hash_equals($sessionToken, $token)) {
            return AuthResult::failure('TOKEN MISMATCH');
        }

        if ($this->users->findByEmail($email) !== null) {
            return AuthResult::failure('USER ALREADY EXISTS');
        }

        return AuthResult::success('SIGNUP OK');
    }
}
```

Codice completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-34/it/parte-09/cap-34/listing-01.php)


Sorgente reale: [`src/Services/AuthService.php` a `lesson-1-8`](https://github.com/hidran/phpenterpriseblog/blob/lesson-1-8/src/Services/AuthService.php).

La dipendenza è un'interfaccia (`UserRepositoryInterface`), non una classe concreta. Questo rende il servizio testabile con mock.

Questa è una scelta architetturale, non solo un trucco per PHPUnit. `AuthService` contiene regole applicative: verificare il token CSRF, cercare l'utente, controllare la password, restituire un risultato esplicito. Se questa logica resta dentro un controller, per testarla devi simulare request HTTP, sessione, database e rendering. Se invece sta in un servizio, puoi testare la regola direttamente.

Un buon servizio applicativo ha tre caratteristiche: riceve dipendenze dall'esterno, restituisce un risultato comprensibile e non decide dettagli di infrastruttura come redirect o template. Il controller può occuparsi di HTTP; il servizio decide se il login è valido. Questa separazione è il motivo per cui il test unitario diventa naturale.

## PHPUnit: unit e integration

La configurazione separa test unitari e di integrazione:

```xml
<testsuites>
    <testsuite name="unit">
        <directory>tests/Unit</directory>
    </testsuite>
    <testsuite name="integration">
        <directory>tests/Integration</directory>
    </testsuite>
</testsuites>
```

Codice completo: [listing-02.xml](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-34/it/parte-09/cap-34/listing-02.xml)


Sorgente reale: [`phpunit.xml.dist` a `lesson-3-1`](https://github.com/hidran/phpenterpriseblog/blob/lesson-3-1/phpunit.xml.dist).

I test unitari devono essere veloci e isolati. I test di integrazione possono toccare MySQL o Redis, ma stanno in una suite separata.

La differenza è pratica. Un unit test verifica una decisione in memoria: dato questo input e questa dipendenza simulata, il servizio restituisce questo risultato. Non deve partire MySQL, non deve esistere Redis, non deve esserci un web server. Se fallisce, vuoi capire subito quale regola è sbagliata.

Un integration test verifica invece che due o più parti reali parlino correttamente tra loro. Un repository con PDO, per esempio, non è davvero verificato se testi solo che chiama `prepare()`: devi anche sapere che la query funziona contro lo schema reale, che i nomi delle colonne sono corretti, che il mapping da riga SQL a oggetto non perde dati. Lo stesso vale per Redis, migrazioni, session handler e configurazione.

Per questo le suite sono separate. I test unitari devono poter girare continuamente mentre sviluppi. I test di integrazione possono essere più lenti e richiedere servizi Docker, quindi li esegui prima di aprire una pull request, in CI, o quando tocchi un confine infrastrutturale. Separarli evita due errori comuni: rendere tutti i test lenti oppure chiamare "unitario" un test che in realtà dipende da mezzo sistema.

## Testare l'autenticazione con mock

Un test non deve creare utenti veri nel database solo per verificare una password sbagliata:

```php
<?php

declare(strict_types=1);

public function testLoginRejectsUnknownUser(): void
{
    $repo = $this->createMock(UserRepositoryInterface::class);
    $repo->method('findByEmail')->willReturn(null);

    $service = new AuthService($repo);

    self::assertSame(
        'USER NOT FOUND',
        $service->verifyLogin('a@b.co', 'secret123', 't', 't')->message
    );
}
```

Codice completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-34/it/parte-09/cap-34/listing-03.php)


Sorgente reale: [`tests/Unit/Services/AuthServiceTest.php` a `lesson-3-2`](https://github.com/hidran/phpenterpriseblog/blob/lesson-3-2/tests/Unit/Services/AuthServiceTest.php).

Qui testiamo il contratto del servizio: quando il repository non trova l'utente, il risultato è un fallimento controllato.

Un mock è utile quando vuoi isolare una regola dal suo confine esterno. In questo caso non ci interessa se `UserRepository` sappia parlare con MySQL: quello sarà coperto da un test di integrazione. Qui ci interessa il comportamento di `AuthService` quando il repository risponde "nessun utente".

Il rischio dei mock è usarli per testare l'implementazione invece del comportamento. Se un test dice "deve chiamare esattamente questi tre metodi in questo ordine" ma non descrive un risultato utile per l'applicazione, diventa fragile. Un buon test unitario parla il linguaggio del dominio: login rifiutato, token non valido, utente già esistente, password corretta.

## Test di regressione

Un bug risolto deve diventare un test. Nel repository c'è un caso preciso: `PostRepository::save()` non deve scrivere l'email nel corpo del post.

```php
<?php

declare(strict_types=1);

$stmt->expects($this->once())
    ->method('execute')
    ->with($this->callback(function (array $params): bool {
        self::assertSame('actual message body', $params['message']);
        self::assertArrayNotHasKey('email', $params);

        return true;
    }));
```

Codice completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-34/it/parte-09/cap-34/listing-04.php)


Sorgente reale: [`tests/Unit/Repositories/PostRepositorySaveRegressionTest.php` a `lesson-3-3`](https://github.com/hidran/phpenterpriseblog/blob/lesson-3-3/tests/Unit/Repositories/PostRepositorySaveRegressionTest.php).

Il test descrive il comportamento che non deve rompersi più.

Questo è il valore di un test di regressione: non dimostra che tutto il repository sia perfetto, ma blocca un errore reale che è già costato tempo. Ogni volta che correggi un bug, chiediti quale test avrebbe intercettato l'errore prima. Se riesci a scriverlo, quel bug non è più solo "risolto": è documentato come comportamento atteso.

Nel blog enterprise questa mentalità è più importante della quantità di test. Non devi testare ogni getter o ogni riga. Devi proteggere le regole, i bug già trovati e i confini dove il costo di una regressione è alto: autenticazione, salvataggio dei post, escaping delle view, migrazioni e integrazione con servizi esterni.

## PHP_CodeSniffer e Slevomat

Il primo quality gate è meccanico: PSR-12 più regole Slevomat per tipi e `strict_types`.

```xml
<rule ref="PSR12"/>
<rule ref="SlevomatCodingStandard.TypeHints.ParameterTypeHint"/>
<rule ref="SlevomatCodingStandard.TypeHints.ReturnTypeHint"/>
<rule ref="SlevomatCodingStandard.TypeHints.PropertyTypeHint"/>
<rule ref="SlevomatCodingStandard.TypeHints.DeclareStrictTypes"/>
```

Codice completo: [listing-05.xml](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-34/it/parte-09/cap-34/listing-05.xml)


Sorgente reale: [`phpcs.xml` a `lesson-2-1`](https://github.com/hidran/phpenterpriseblog/blob/lesson-2-1/phpcs.xml).

Lo scopo non è discutere spazi o parentesi. Lo scopo è togliere al reviewer il lavoro meccanico e far fallire il build quando mancano tipi.

PHP_CodeSniffer legge il codice e verifica che rispetti uno standard. PSR-12 dà una base comune: indentazione, namespace, import, parentesi, dichiarazioni. Slevomat aggiunge regole più orientate alla qualità del PHP moderno: parametri tipizzati, return type, property type, `declare(strict_types=1)`.

Per un senior developer il valore è molto concreto: la code review deve concentrarsi su architettura, sicurezza, query, transazioni, error handling e nomi di dominio. Se metà della review riguarda formattazione o tipi mancanti, stai sprecando attenzione umana su problemi che una macchina può rilevare in modo più coerente.

PHPCS non sa se la query è giusta e non sa se il design è buono. Ma crea una base uniforme. Quando tutti i file seguono le stesse regole, il codice diventa più leggibile, gli strumenti lavorano meglio e le differenze nei commit mostrano cambiamenti reali, non rumore.

## PHPStan

PHPStan trova incoerenze che i test potrebbero non attraversare:

```yaml
includes:
  - phpstan-baseline.neon
parameters:
  level: 8
  paths:
    - src
    - bin
    - config
    - public
    - tests
```

Codice completo: [listing-06.yml](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-34/it/parte-09/cap-34/listing-06.yml)


Sorgente reale: [`phpstan.neon` a `lesson-8-3`](https://github.com/hidran/phpenterpriseblog/blob/lesson-8-3/phpstan.neon).

Il progetto inizia con una baseline a livello 6 e poi alza l'asticella a livello 8. È una migrazione pragmatica: attivi il controllo presto, poi riduci il debito in modo esplicito.

PHPStan è un analizzatore statico: non esegue il programma, ma legge il codice e prova a capire se i contratti sono coerenti. Se una funzione promette `Post` ma può restituire `false`, PHPStan lo segnala. Se un array viene usato come se avesse una chiave sempre presente, ma quella chiave non è garantita, PHPStan ti costringe a essere esplicito. Se un metodo riceve `int` e tu gli passi `string|null`, lo scopri prima di arrivare al browser.

Questo è particolarmente importante in PHP perché il linguaggio è flessibile. La flessibilità è utile, ma nei progetti grandi può nascondere errori: array con forme implicite, valori `mixed`, proprietà inizializzate tardi, ritorni diversi nello stesso metodo. PHPStan riduce quella zona grigia.

La baseline non è una scusa per ignorare gli errori. È uno strumento di migrazione. Quando introduci PHPStan in un progetto esistente, potresti avere troppi problemi per sistemarli subito. La baseline registra il debito attuale e impedisce di aggiungerne altro. Poi, commit dopo commit, rimuovi voci dalla baseline e alzi il livello. Arrivare a livello 8 significa chiedere al codice contratti molto più chiari.

PHPStan non sostituisce i test. Un codice può essere staticamente corretto e comunque sbagliare una regola di business. Ma PHPStan trova un'altra classe di problemi: incoerenze che i test potrebbero non attraversare mai.

## Rector verso PHP 8.5

Rector aiuta a mantenere il codice allineato al linguaggio:

```php
<?php

declare(strict_types=1);

return RectorConfig::configure()
    ->withPaths([__DIR__ . '/src', __DIR__ . '/bin', __DIR__ . '/config', __DIR__ . '/tests'])
    ->withSets([
        LevelSetList::UP_TO_PHP_85,
        SetList::CODE_QUALITY,
        SetList::DEAD_CODE,
        SetList::TYPE_DECLARATION,
    ]);
```

Codice completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-34/it/parte-09/cap-34/listing-07.php)


Sorgente reale: [`rector.php` a `lesson-2-3`](https://github.com/hidran/phpenterpriseblog/blob/lesson-2-3/rector.php).

Non sostituisce il giudizio umano, ma rende meccaniche molte modernizzazioni.

Rector lavora sull'albero sintattico del codice, non su semplici sostituzioni di testo. Questo significa che può applicare trasformazioni strutturali: aggiungere tipi quando sono deducibili, sostituire costrutti obsoleti, semplificare codice morto, aggiornare pattern verso versioni moderne del linguaggio.

Il valore architetturale di Rector è la ripetibilità. Se decidi che il progetto deve essere allineato a PHP 8.5, non vuoi fare centinaia di micro-refactor a mano. Vuoi una regola eseguibile, una diff leggibile e una suite di test che confermi che il comportamento non è cambiato.

Rector va usato con disciplina: eseguilo in commit piccoli, leggi la diff, non accettare trasformazioni che non capisci, poi fai passare test e analisi statica. È un acceleratore, non un pilota automatico. Se una trasformazione cambia il significato del codice, il problema non è solo dello strumento: significa che mancavano test o che il codice era ambiguo.

## Il comando CI locale

Il valore dei gate è poterli eseguire sempre nello stesso modo:

```bash
composer ci
```

Codice completo: [listing-08.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-34/it/parte-09/cap-34/listing-08.sh)


Sorgente reale: [`composer.json` al commit `eb2e62a`](https://github.com/hidran/phpenterpriseblog/blob/eb2e62a774f6b20539e72f40f7d3fe9205ef4c5d/composer.json).

Ogni blocco di lavoro dovrebbe chiudersi con una verifica reale. Non basta dire "dovrebbe funzionare": esegui il comando, leggi l'output e solo dopo considera stabile quel punto del progetto.

L'ordine dei gate conta. Prima vuoi fallire su problemi economici da correggere: formattazione, standard, tipi ovvi. Poi passi ad analisi statica e test unitari. Solo dopo ha senso eseguire test di integrazione, E2E o pipeline più costose. Una CI ben organizzata non è un unico muro finale: è una serie di filtri che restituiscono feedback il prima possibile.

In un team, `composer ci` è anche un contratto sociale. Significa che tutti usano lo stesso comando, localmente e in CI. Non ci sono istruzioni nascoste nella testa di una persona. Se il comando passa sulla tua macchina e passa in CI, il progetto ha una definizione condivisa di "verificato".

## In sintesi

Autenticazione e quality gate stanno nello stesso capitolo perché condividono un principio: comportamento esplicito e verificabile. `AuthService` rende testabile il login; PHPUnit blocca regressioni; PHP_CodeSniffer e Slevomat rendono uniforme lo stile e obbligano tipi chiari; PHPStan controlla i contratti senza eseguire l'applicazione; Rector automatizza refactoring e aggiornamenti verso PHP 8.5. Uno sviluppatore senior pragmatico non deve usarli per moda: deve usarli perché riducono in modo misurabile il rischio di cambiare codice.
