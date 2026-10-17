# Capitolo 22. QA pre-deploy, /code-review e review multi-LLM

Cosa imparerai: a preparare la Photogallery per la produzione con una checklist QA che blocca davvero il deploy, a stanare i task orfani rimasti dopo le wave, a usare la review integrata di Claude Code (`/code-review`, `REVIEW.md`, ultrareview) e a capire quando serve ancora un secondo modello come Gemini, Codex o Kimi. Chiudiamo con un audit di sicurezza dedicato: middleware, CSP, HTTPS e secrets.

Prerequisiti: la Photogallery al punto del Capitolo 21 (branch `book/cap-14-phases-complete`), con test che passano. Per ultrareview ti serve un account claude.ai; per la review multi-LLM, l'accesso ad almeno un secondo modello.

In locale un bug è un fastidio: lo vedi, lo correggi, fai il push e nessuno se ne accorge. In produzione lo stesso bug può voler dire foto di un utente visibili a un altro, sessioni compromesse, dati persi. E di solito finisce con una mail di scuse agli utenti, che è la parte che piace meno a tutti. Correggere un problema durante lo sviluppo costa un'ora; dopo il deploy ci aggiungi l'incidente, il rollback, la comunicazione e la post-mortem, e l'ora diventa qualche giorno.

Per questo le ultime 24-48 ore prima del rilascio le dedichiamo alla QA. Il capitolo segue l'ordine in cui la faccio io sulla Photogallery: prima la checklist, poi la caccia ai task orfani, poi la review del codice in tre livelli (la review integrata di Claude Code, un secondo modello sulle parti critiche, i plugin di sicurezza) e per ultimo l'audit di sicurezza.

## 22.1 La checklist QA pre-deploy

Una checklist pre-deploy ha senso solo se è vincolante: se una voce non passa, il deploy non parte. Una lista che puoi ignorare quando hai fretta è una lista di desideri, e il giorno del rilascio hai sempre fretta.

La eseguo uno o due giorni prima del deploy, quando c'è ancora tempo per correggere con calma. Il giorno stesso è tardi.

### Flussi funzionali

I test automatici verificano quello che hai pensato di testare. Il test manuale trova il resto. Prima del deploy provo a mano questi flussi:

- registrazione, con la verifica email se c'è
- login e logout
- recupero password
- ogni operazione CRUD principale (foto, album, tag, foto preferite)
- upload con file validi, file oltre i 10 MB, file con estensione sbagliata
- paginazione e filtri
- i flussi del pannello admin Filament

Ogni flusso lo provo tre volte: da utente non autenticato, da utente autenticato e da admin. I bug di autorizzazione saltano fuori quasi sempre quando un ruolo prova a fare qualcosa che non dovrebbe poter fare.

Poi gli errori. Ogni percorso di errore deve produrre una UI sensata: niente schermata bianca, niente dump JSON, niente stack trace visibili all'utente. Ogni form valida lato client per la UX e lato server per la sicurezza, perché la validazione nel browser si aggira in un secondo. Le pagine 404 e 500 devono esistere e dire qualcosa di utile. Due controlli veloci da terminale:

```bash
# Una pagina che non esiste deve rispondere 404 (non 200 con una pagina bianca)
curl -s -o /dev/null -w "%{http_code}\n" https://tua-app.dev/pagina-che-non-esiste

# Un endpoint protetto senza token deve rispondere 401 (non 500)
curl -s -o /dev/null -w "%{http_code}\n" https://tua-app.dev/api/v1/auth/me
```

### Performance: numeri, non sensazioni

"Sembra veloce" non è una metrica. Per il frontend parto da Lighthouse e punto a un punteggio sopra 85 sulle pagine chiave (galleria, album, dettaglio foto). Sotto 70 gli utenti iniziano ad abbandonare e Google ti penalizza nel ranking.

```bash
# Lighthouse da riga di comando (serve Chrome installato)
npx lighthouse https://tua-app.dev/pagina-chiave \
  --output=json \
  --output-path=./lighthouse-report.json \
  --chrome-flags="--headless"
```

Per le API guardo la mediana delle chiamate principali, che deve stare sotto i 200 ms. Il 99esimo percentile lo ottimizzi dopo: la mediana è l'esperienza della maggior parte degli utenti. Questo script fa cento richieste all'elenco delle foto e stampa la mediana vera, non la media:

```bash
# Latenza dell'endpoint principale su 100 richieste: stampa la mediana
for i in $(seq 1 100); do
  curl -s -o /dev/null -w "%{time_total}\n" https://tua-app.dev/api/v1/photos
done | sort -n | awk '{t[NR]=$1} END {print "Mediana:", t[int((NR+1)/2)] "s"}'
```

Sugli asset le regole sono poche. Le immagini servite agli utenti vanno in WebP o AVIF, non in JPEG o PNG a piena risoluzione. CSS e JavaScript compressi con gzip o brotli. Una foto da 4 MB nella griglia della galleria è un bug di performance, anche se la pipeline delle miniature esiste: basta un componente che punta all'originale invece che alla miniatura.

Sul database, ogni query frequente deve avere il suo indice. Se `WHERE user_id = ?` gira a ogni richiesta autenticata, `user_id` va indicizzata, altrimenti la query fa una scansione completa della tabella e rallenta sempre di più man mano che i dati crescono. Nella Photogallery è successo davvero: la migration di `photos` usava `foreignUuid('user_id')->constrained()`, che su SQLite e PostgreSQL non crea l'indice di supporto. L'ha trovato la review della PR della fase 1, e la correzione è in `docs/REVIEW-FIXES.md` (voce F1).

```sql
-- Controlla l'indice (MySQL/MariaDB)
EXPLAIN SELECT * FROM photos WHERE user_id = 1 ORDER BY created_at DESC LIMIT 20;
-- Se la colonna "type" vale "ALL", l'indice manca
```

### Sicurezza di base

Questi sono i controlli che fai in mezz'ora. L'audit completo arriva nel paragrafo 22.6.

- Route admin e mutazioni: ogni endpoint che modifica dati o legge dati di altri utenti richiede autenticazione e controllo dei permessi. Sempre, non di solito. Prova ogni endpoint admin con il token di un utente normale e verifica che risponda 403.
- Validazione dell'input: tutto quello che arriva da fuori (parametri URL, body JSON, file, header) passa da una Form Request in Laravel, o da uno schema Zod lato TypeScript.
- CSRF: se l'autenticazione usa cookie, il CSRF è un rischio reale. La Photogallery usa token Bearer di Sanctum sulle API, ma il pannello Filament usa la sessione web: verifica che la protezione sia attiva lì, soprattutto dopo un refactoring.
- Rate limiting su login e registrazione. Senza, un attaccante prova migliaia di combinazioni di password in poche ore.

### Integrità dei dati: il backup che nessuno prova

Se stanotte il database si corrompe, domani mattina riesci a ripristinarlo? Non "in teoria sì, il backup è automatico": hai mai fatto un restore da quel backup? Prima del deploy fanne uno di prova su un database temporaneo. Se non funziona adesso, non funzionerà nemmeno durante un'emergenza.

```bash
# Restore di prova da un backup su S3 (adattalo al tuo setup)
aws s3 cp s3://tuo-bucket/backup-latest.sql.gz ./restore-test.sql.gz
gunzip restore-test.sql.gz
mysql -u root -p test_restore < restore-test.sql

# Controlla che le tabelle esistano e contengano dati sensati
mysql -u root -p test_restore -e "SELECT COUNT(*) FROM users;"
```

Prova anche le migration su una copia del database di produzione, o su un dump anonimizzato recente, non solo sul database locale. Sui dati reali le migration falliscono in modi che in sviluppo non vedi. E scrivi il piano di rollback: se il deploy va male, cosa fai e in quanto tempo torni alla versione precedente. Va messo per iscritto, non tenuto a mente.

### Osservabilità

Prima del deploy verifico che ci siano:

- log strutturati in JSON, che puoi filtrare, aggregare e usare per gli alert (un `console.log("errore!")` in produzione non serve a nessuno)
- error tracking con Sentry, Bugsnag o simili, così ogni eccezione non gestita arriva a te prima che a un utente
- un endpoint di health che controlla le dipendenze vere
- tre metriche di base su CloudWatch o Grafana: numero di richieste, tasso di errore, latenza; ti bastano dieci secondi per capire se il deploy ha peggiorato qualcosa

L'endpoint di health è quello che il load balancer interroga per decidere se un container è vivo. Nella Photogallery è `GET /api/v1/health` (DESIGN §6.5): scrive, rilegge e cancella un file marcatore sul disco delle foto e interroga la tabella `failed_jobs` per verificare la connessione della coda. Risponde 200 se tutto va, 503 con il dettaglio se qualcosa fallisce:

```json
{
  "status": "ok",
  "storage": "ok",
  "queue": "ok"
}
```

La checklist completa per il tuo stack te la può generare Claude. La uso come punto di partenza e poi la taglio.

::: {.callout .callout-prompt}
[Prompt riusabile]{.callout-title}

```text
Sei un QA engineer senior. Il mio progetto è [descrivi stack e tipo di app].
Genera una checklist pre-deploy strutturata per categoria:
Funzionale, Performance, Security, Data Integrity, Observability.
Per ogni voce specifica: cosa verificare, come verificarlo (comando o azione),
criterio di successo. Formato: tabella Markdown.
```
:::

## 22.2 Caccia ai task orfani

Ogni progetto sviluppato con Spec Driven Development e un agente ha lo stesso problema silenzioso: i task orfani. Feature implementate a metà, endpoint registrati ma vuoti, componenti creati e mai importati. Codice che esiste e supera i test, perché i test non controllano quello che non sai che manca.

Nascono in due modi. Il primo è una sessione che si interrompe a metà task: un `/clear`, una compattazione, una sessione in background chiusa troppo presto. Quando riparti, Claude non ricorda dove era arrivato, e se in `docs/TASKS.md` c'è un task segnato in corso può darlo per finito senza averlo chiuso davvero.

Il secondo è più sottile. Un task viene spuntato perché la parte principale funziona, ma qualche dettaglio non arriva mai: la validazione di un caso limite, la gestione del 413, la vista mobile. In un team di persone la code review di solito li cattura. Con un agente che produce codice a questa velocità, i buchi si accumulano senza che nessuno li veda.

### Audit con grep

Il primo passaggio è meccanico: cercare nel codice i segnali di lavoro incompleto. Lancia questi comandi dalla root del repository.

```bash
# TODO, FIXME, HACK, XXX e stub (esclusi node_modules, vendor e build)
grep -rn \
  --include='*.ts' --include='*.tsx' --include='*.js' --include='*.jsx' \
  --include='*.php' --include='*.py' \
  -E "(TODO|FIXME|XXX|HACK|placeholder|implement me|not implemented)" \
  --exclude-dir={node_modules,vendor,.git,dist,build} \
  .
```

Ogni risultato va letto. Alcuni TODO sono ottimizzazioni future legittime, altri sono buchi funzionali, e la differenza la capisci solo dal contesto. Poi cerco gli endpoint che restituiscono vuoto:

```bash
# Controller che restituiscono null, array vuoti o un TODO
grep -rn "return null" backend/app/Http/Controllers/
grep -rn "return \[\]" backend/app/Http/Controllers/
grep -rn "// TODO: implement" backend/app/
```

Per il frontend, uno script Node che elenca i componenti mai importati. Va lanciato dalla cartella `frontend/` e richiede il pacchetto `glob` (`npm install -D glob`):

```bash
# Componenti creati ma mai importati
node -e "
const fs = require('fs');
const glob = require('glob');
const path = require('path');

const components = glob.sync('src/components/**/*.{tsx,jsx}');
const allCode = glob.sync('src/**/*.{tsx,jsx,ts,js}')
  .filter(f => !f.includes('.test.'))
  .map(f => fs.readFileSync(f, 'utf8'))
  .join('\n');

components.forEach(comp => {
  const name = path.basename(comp, path.extname(comp));
  if (!allCode.includes('/' + name) && !allCode.includes(name + \"'\")) {
    console.log('Componente non importato:', comp);
  }
});
"
```

Per il backend cerco le colonne aggiunte dalle migration che non compaiono quasi mai nel codice. Da `backend/`:

```bash
# Colonne dichiarate nelle migration
grep -hE -e "->(string|integer|boolean|text|json)\(" database/migrations/*.php \
  | grep -oP "\('\K[^']+" | sort -u > migration_columns.txt

# Quante volte compare ciascuna in app/
while read col; do
  count=$(grep -rn "$col" app/ --include="*.php" | wc -l)
  if [ "$count" -lt 2 ]; then
    echo "Colonna probabilmente orfana: $col (trovata $count volte)"
  fi
done < migration_columns.txt
```

### Un subagent che caccia gli orfani

Il grep trova i pattern testuali. Un subagent (Capitolo 10) legge il progetto intero e ragiona sul contesto: si accorge che un endpoint si chiama `export` ma non esporta niente, cosa che nessun grep ti dice. Gli passo questo prompt:

```text
Agisci come un senior software engineer che fa un audit di qualità
pre-deploy. Analizza l'intero progetto (backend + frontend) e cerca:

1. Feature parzialmente implementate (endpoint che non fanno quello
   che il nome suggerisce, componenti con funzionalità commentata,
   form senza handler)

2. Codice orfano (funzioni mai chiamate, componenti mai importati,
   migration con colonne non usate, route registrate ma non implementate)

3. Stub e placeholder (return null, throw new Error("not implemented"),
   TODO senza data né owner)

Per ogni finding, indica:
- File e numero di riga
- Descrizione del problema
- Probabilità che sia da completare (alta/media/bassa)
- Alternativa: da eliminare?

Output: tabella Markdown ordinata per probabilità di completamento.
```

Sulla Photogallery questo audit ha trovato quattro cose:

- un componente Lightbox duplicato, due versioni quasi identiche di cui una non usata
- un metodo `purge` nel servizio delle foto che nessuno chiamava
- una route `GET /api/v1/photos/export` registrata nel router, con un controller che conteneva solo il commento `// TODO: CSV export`
- tre tag `<meta>` Open Graph nel template HTML che puntavano a proprietà mai valorizzate

### La regola delle tre D

Per ogni orfano scelgo uno di tre destini.

Delete. Se la feature non fa parte dell'MVP e non c'è un piano concreto per farla, il codice morto si cancella. È codice che nessuno manutiene e nessuno testa. Un endpoint vuoto che risponde 200 è peggio di un endpoint che non esiste, perché promette una funzionalità che non c'è.

Complete. Se la feature è nell'MVP ma è a metà, la completi adesso, non dopo il deploy. Un upload senza validazione del tipo MIME non è quasi finito: è una vulnerabilità aperta.

Document and defer. Se la feature non è nell'MVP ma ha senso più avanti, apri una issue con tutti i dettagli e togli lo scheletro dal branch di deploy. L'issue ti serve, lo scheletro no.

Quando gli orfani sono tanti, faccio proporre la decisione a Claude:

```text
Ho trovato questi elementi orfani nel progetto:
[lista dei finding]

Per ognuno, dammi una raccomandazione: Delete / Complete / Document and Defer.
Motiva la scelta in base a: impatto sul MVP, rischio di lasciarlo com'è,
costo stimato per completarlo ora vs dopo.
```

## 22.3 La review integrata di Claude Code

Nel Capitolo 19 la code review l'abbiamo fatta con prompt scritti a mano e con il reviewer di Superpowers. Funziona ancora, e resta il modo giusto per una review guidata dalla spec. Nel frattempo però Claude Code ha guadagnato strumenti di review propri: un comando locale, una review approfondita nel cloud fatta da più agent e una review automatica delle pull request su GitHub. Sono il primo livello di difesa, quello che usi a ogni push.

### `/code-review` in locale

`/code-review` (alias `/review`) controlla i commit del branch che non sono ancora sul remote, più le modifiche non committate. Cerca bug di correttezza, cioè le cose che rompono il programma, non lo stile. Gira come subagent in background con un contesto suo: non riempie la conversazione e nel frattempo puoi continuare a lavorare. I risultati arrivano quando ha finito, con file, riga e gravità per ogni problema.

Per vederlo trovare qualcosa di sicuro, sulla Photogallery introduco due difetti apposta su un branch di prova: tolgo la chiamata `$this->authorize('update', $photo)` da `PhotoController::update` e la regola `mimes:jpg,jpeg,png,webp` da `StorePhotosRequest`. Committo e lancio la review:

```bash
git switch -c review/demo-bug
# ... introduci i due difetti, poi:
git commit -am "demo: due difetti per la review"
```

```text
/code-review high main...review/demo-bug
```

Il comando accetta un livello di effort e un target. L'effort va da `low` a `max` (`low`, `medium`, `high`, `xhigh`, `max`): con `low` riporta solo i problemi di cui è più sicuro, quindi pochi falsi positivi; salendo la copertura si allarga e arrivano anche segnalazioni meno certe. Il target può essere un file, il numero di una PR, un branch o un intervallo come `main...review/demo-bug`.

```text
/code-review low
/code-review high main...feat/albums-api
/code-review 42
/code-review --max-findings all
```

Attenzione a un dettaglio: se non indichi un livello, `/code-review` riusa l'ultimo che hai scritto, anche in una sessione precedente. Lo stesso vale per `--max-findings`, che resta impostato finché non passi `--max-findings default`.

<!-- TODO screenshot: risultato di /code-review high sul branch review/demo-bug, con i due problemi (autorizzazione mancante e validazione dell'upload) e file, riga e gravità -->

### Applicare le correzioni e pubblicarle

Con `--fix` la review applica le correzioni direttamente nel working tree. Con `--comment` pubblica i risultati come commenti sulla PR, su GitHub o GitLab:

```text
/code-review --fix main...review/demo-bug
/code-review --comment 42
```

::: {.callout .callout-warning}
[Attenzione]{.callout-title}

Le correzioni applicate in background da `--fix` non vengono annullate da `/rewind`. Per tornare indietro usa Git: committa prima di lanciare la review, così `git diff` ti mostra esattamente cosa ha cambiato e `git restore .` ti riporta al punto di partenza.
:::

Dopo il fix guardo sempre `git diff --stat` e rilancio i test. La review corregge il bug che ha trovato, ma non sa se la correzione rompe qualcos'altro: lo dice la suite di Pest.

### `REVIEW.md` e Code Review su GitHub

`/code-review` legge il `CLAUDE.md` come ogni sessione di Claude Code. Le convenzioni della Photogallery valgono quindi anche per la review: SOLID, transazioni sulle scritture multiple, eager loading esplicito, doppio controllo di autorizzazione su ogni mutazione (token ability più policy, regola 10 del `CLAUDE.md`).

Per le pull request c'è Code Review su GitHub, un servizio gestito per i piani Team ed Enterprise, pagato per singola review. Più agent analizzano ogni PR, un passaggio di verifica scarta i falsi positivi, e il risultato arriva come commenti inline ordinati per gravità più un check run chiamato "Claude Code Review". Non approva e non blocca mai la PR: la decisione resta a te. Per chiedere una nuova review scrivi un commento `@claude review` sulla PR. Non è disponibile con Zero Data Retention, HIPAA o CMEK.

<!-- VERIFY: come si attiva Code Review per l'organizzazione (pagina code-review su code.claude.com) -->

Code Review su GitHub si personalizza con un file `REVIEW.md` nella root del repository, affiancato al `CLAUDE.md`; puoi aggiungerne altri nelle sottocartelle per regole locali. Ci scrivi cosa è grave nel tuo progetto, quanti dettagli minori vuoi al massimo, cosa ignorare e cosa controllare sempre. Questo è quello della Photogallery:

```markdown
# Istruzioni di revisione

## Cosa è Important

Riserva Important ai problemi che rompono il comportamento o espongono dati:
query non filtrate per l'utente proprietario della foto, upload senza
validazione di tipo e dimensione, endpoint senza policy di autorizzazione,
migrazioni non retrocompatibili. Stile e naming sono al massimo Nit.

## Limita i Nit

Riporta al massimo cinque Nit per revisione. Se ne trovi altri, scrivi
"più N elementi simili" nel riepilogo.

## Non segnalare

- Quello che la CI già controlla: lint, formattazione, tipi
- File generati e lockfile

## Controlla sempre

- Ogni nuova rotta sotto /api/v1 ha un test di integrazione Pest
- I contratti API corrispondono a docs/DESIGN.md
- Ogni mutazione controlla sia tokenCan() sia la policy
- exif e processing_error sono visibili solo al proprietario e agli admin
- Nessun log contiene email o token
```

La sezione "Controlla sempre" riprende i criteri della spec: i contratti API devono corrispondere a `docs/DESIGN.md`, come abbiamo imposto nel Capitolo 18. Le ultime due voci vengono da problemi veri trovati nelle review delle wave e registrati in `docs/REVIEW-FIXES.md`: l'`AlbumController@store` che controllava solo la token ability (S3) e i campi `exif` e `processing_error` restituiti anche agli utenti anonimi, con dentro le coordinate GPS (S1).

I problemi trovati hanno tre livelli. Important va corretto prima del merge. Nit è un dettaglio minore. Pre-existing è un bug che esisteva già e che la PR non ha introdotto: utile saperlo, ma non è un motivo per bloccare il merge.

Ricorda che il comando locale `/code-review` non legge `REVIEW.md`: legge solo il `CLAUDE.md`. Se una regola ti serve in entrambi i posti, scrivila nel `CLAUDE.md`.

### Ultrareview nel cloud

Per le PR importanti c'è ultrareview, in research preview. Invece di un solo revisore, una squadra di agent specializzati analizza il codice nel cloud, ognuno a caccia di un tipo diverso di problema, e un passaggio di verifica scarta i falsi positivi. I risultati tornano nella tua sessione quando sono pronti.

```text
/code-review ultra
/code-review ultra controlla soprattutto autorizzazioni e upload
/code-review ultra --fix
```

Senza argomenti confronta il branch corrente con il branch principale, incluse le modifiche non committate. Puoi passare un branch, oppure una nota in linguaggio naturale per orientare la review, come nel secondo esempio. Con `--fix` applica le correzioni; per una PR su github.com, dalla finestra di avvio puoi scegliere di pubblicare i risultati sulla PR. `/ultrareview` è un alias.

Serve il login con un account claude.ai. Su Bedrock, Agent Platform di Google Cloud (l'ex Vertex AI) o Foundry, `/code-review ultra` ripiega su una review locale; con Zero Data Retention o HIPAA non è disponibile. Sui piani Pro e Max hai tre esecuzioni gratuite, poi si paga con i crediti di utilizzo: per questo non la lancio a ogni push.

Per script e CI c'è il comando `claude ultrareview [target]`, che aspetta i risultati e li stampa. `--json` produce un output leggibile da un altro programma, `--timeout` imposta l'attesa massima in minuti (il default è 45) e `--post` pubblica i risultati come commento sulla PR.

```bash
claude ultrareview --json --timeout 30 > ultrareview.json
```

## 22.4 Un secondo modello per le parti critiche

Claude Code ha scritto il codice della Photogallery con i suoi pattern e la sua idea di architettura giusta. Quando lo stesso modello rivede quel codice, tende a riconoscere come corretti proprio quei pattern. È il problema di chi rilegge il proprio lavoro: vede quello che pensava di aver scritto. Nel log delle review della Photogallery c'è una frase che lo dice chiaramente: la sessione che aveva scritto il codice non aveva visto nessuno dei problemi trovati poi da un reviewer indipendente.

La review integrata del paragrafo precedente attenua il problema, perché gira con un contesto pulito e, nel caso di ultrareview, con più agent e una verifica. Ma il modello resta uno. I team risolvono la questione da decenni nello stesso modo: il revisore deve essere diverso dall'autore. Con gli LLM vuol dire un modello diverso. Gemini, Codex e Kimi sono addestrati su dati diversi, con tecniche diverse, e hanno punti ciechi diversi da quelli di Claude: quello che un modello considera normale, un altro lo segnala.

Ha ancora senso, ora che c'è `/code-review`? Sì, ma non ovunque. Un secondo modello costa tempo, perché la review la orchestri a mano. Lo uso sulle parti critiche (autenticazione, upload, autorizzazioni, pipeline delle foto) prima del deploy, non su ogni push.

### Cosa hanno trovato sulla Photogallery

Quello che segue è quanto ho osservato su questo progetto, con le versioni dei modelli disponibili a primavera 2026. Non è una classifica generale: i modelli cambiano ogni pochi mesi, e su un altro codice i risultati possono essere diversi.

Claude, usato come revisore con i prompt del Capitolo 19, è stato il più utile sull'architettura: violazioni SOLID, dipendenze circolari, pattern fuori posto per il dominio. Spiega molto e propone correzioni dettagliate, ma sul codice che ha scritto lui è più indulgente.

Gemini è stato il più forte su performance e uso della memoria. Ha trovato tre problemi che Claude non aveva segnalato:

- un `file_get_contents` (e lo stesso schema con `Storage::get`) che caricava in RAM il file intero invece di usare uno stream, con il rischio di out of memory sulle foto grandi
- `UploadPhotosAction` che scriveva i file su disco dentro una transazione: se la transazione andava in rollback, i file restavano scritti
- le coordinate GPS nei metadati EXIF servite agli utenti, compresi terzi non autorizzati

Codex è stato preciso su tipi, contratti API e gestione degli errori: funzioni che promettono più di quello che restituiscono, `catch` troppo larghi che inghiottono errori veri, risposte incoerenti tra endpoint dello stesso controller. Report più corti di quelli di Claude, ma mirati.

Kimi è stato il più pignolo sui casi limite di sicurezza, e ha trovato cose che né Claude né Gemini avevano visto:

- la colonna `is_admin` tra i campi fillable del model `User`: chiunque poteva mandare `is_admin: true` nella richiesta e diventare admin
- URL firmati generati prima del controllo della policy: l'URL esisteva e funzionava anche se poi l'utente non superava l'autorizzazione
- autenticazione gestita a mano invece di `Auth::attempt` di Laravel
- la verifica email aggirabile scavalcando il rate limiter
- il token Sanctum salvato in `localStorage` invece che in un cookie HttpOnly

Nessuno di questi era un falso positivo: erano tutti nel codice. L'ultimo è un caso a parte, perché era un compromesso già documentato in DESIGN §10.5: la v1 tiene il token Bearer in `localStorage` e mitiga il rischio con TTL di 24 ore, una CSP restrittiva, il divieto di HTML grezzo nel frontend e le token ability. La review l'ha riportato a galla, e la decisione è stata riconfermata per iscritto invece di restare implicita. Oggi in `User` i campi fillable sono solo `name`, `email` e `password`.

Il report consolidato contava 3 problemi CRITICAL, 7 HIGH, 14 MEDIUM e 7 LOW. Il più grave era una fuga di dati tra utenti in `BatchController`: le foto venivano associate a un batch di upload per timestamp e filtrate in PHP invece che in SQL, quindi due utenti che caricavano nello stesso istante potevano vedere le foto l'uno dell'altro. La correzione è stata una colonna `batch_id` sulla tabella `photos`.

![Il report consolidato della review pre-deploy: i tre problemi CRITICAL, tra cui la fuga di foto tra utenti in BatchController](figures/cap-22/fig-01.png)

![Una parte dei 14 problemi MEDIUM: affidabilità della pipeline, performance del pannello admin, qualità delle immagini e accessibilità da tastiera](figures/cap-22/fig-02.png)

![Dal report: la deriva tra il pattern Actions previsto in DESIGN.md e la logica finita nei controller, lo stripping GPS sincrono durante l'upload e il compromesso sul token in localStorage](figures/cap-22/fig-03.png)

### Il flusso della review multi-LLM

Il primo passo è preparare il changeset:

```bash
# Tutto il diff del branch rispetto a main
git diff main...HEAD > changeset.diff

# Oppure, se il diff è troppo grande, solo le parti critiche
git diff main...HEAD -- backend/app/Http/Controllers/ backend/app/Actions/ frontend/src/api/ > changeset-critical.diff
```

Poi lo stesso prompt a tutti i modelli. Il prompt deve essere identico, altrimenti stai confrontando risposte a domande diverse. Uso quello del riquadro alla fine del paragrafo e incollo il diff in fondo.

Raccolti i report, li aggrego per consenso:

| Trovato da | Priorità |
| :---- | :---- |
| Tutti i modelli | Critica, correzione obbligatoria prima del deploy |
| Tre modelli | Alta, correzione fortemente consigliata |
| Due modelli | Media, valuta il contesto |
| Un solo modello | Bassa, leggi e decidi |

Il consenso serve a decidere da dove partire, non a scartare. Un problema trovato da un solo modello non è per forza un falso positivo: `is_admin` fillable l'aveva visto solo Kimi.

Infine passo i finding a Claude per le correzioni, in una sessione nuova o dopo un `/clear`:

```text
Hai di fronte i risultati di una cross-LLM review del progetto.
Questi problemi sono stati trovati da Gemini e Kimi e confermati da Codex:

[incolla i finding critici e alti]

Organizzali in una todo list e risolvili uno alla volta, partendo
dai Critical. Per ogni fix, spiega cosa hai cambiato e perché.
```

La sessione nuova conta. Il contesto della sessione di sviluppo spinge Claude a riproporre gli stessi pattern appena segnalati come problematici; da un contesto pulito li tratta per quello che sono, problemi da correggere. Dopo le correzioni rilancio `/code-review high` sul branch, per verificare che i fix non abbiano introdotto altro.

Quanto costa? Sulla Photogallery la review con quattro modelli è costata intorno ai 10-15 dollari in tutto; dipende dalla dimensione del diff e dai piani che hai. Un bug come la fuga di foto tra utenti, scoperto in produzione, costa giorni tra incidente, comunicazione agli utenti e, se ci sono di mezzo dati personali, adempimenti legali.

::: {.callout .callout-prompt}
[Prompt riusabile]{.callout-title}

Da incollare identico in Claude, Gemini, Codex e Kimi.

```text
Agisci come un senior software engineer con 10+ anni di esperienza.
Fai una critical review del seguente codice.

Valuta su questi assi:
1. Best practices e standard del linguaggio/framework
2. Principi SOLID e design patterns (SRP, OCP, LSP, ISP, DIP)
3. Sicurezza (injection, autenticazione, autorizzazione, esposizione dati)
4. Scalabilità e performance (query N+1, uso memoria, caching)
5. Affidabilità e gestione degli errori (exception handling, rollback)
6. Edge case non gestiti (input limite, concorrenza, stati intermedi)

Per ogni problema:
- Gravità: Critical / High / Medium / Low
- File e riga (se applicabile)
- Descrizione concisa del problema
- Fix consigliato con snippet di codice

Output: lista Markdown ordinata per gravità decrescente.
Non fare padding: se non trovi problemi in un'area, dillo esplicitamente.

[incolla qui il diff git o i file da revisionare]
```
:::

### Quale review usare e quando

| Approccio | Punti di forza | Limiti | Quando usarlo |
| --- | --- | --- | --- |
| Prompt di review scritti a mano (Capitolo 19) | Controllo completo su cosa guardare | Richiede tempo e prompt ben scritti | Review guidate dalla spec |
| `/code-review` | Veloce, in background, `--fix` e `--comment` | Un solo modello, legge solo `CLAUDE.md` | Prima di ogni push |
| `/code-review ultra` | Più agent, verifica dei falsi positivi | Serve un account claude.ai, consuma di più | PR grandi o critiche |
| Code Review su GitHub (Team ed Enterprise) | Automatica su ogni PR, legge `REVIEW.md` | Pagata per review, solo GitHub | Workflow di team |
| Secondo modello (Gemini, Codex, Kimi) | Prospettiva indipendente | Orchestrata a mano | Sicurezza e performance sul codice critico |

Il flusso che consiglio, e che uso sulla Photogallery:

1. `/code-review high` prima di ogni push.
2. Ultrareview sulle PR grandi o che toccano autenticazione, upload e dati.
3. Una review con un secondo modello sulle parti critiche, prima del deploy.

## 22.5 Plugin di sicurezza

Per la sicurezza ci sono anche strumenti dedicati. Nel marketplace ufficiale `claude-plugins-official` trovi due plugin di Anthropic: security-guidance, che controlla le modifiche di Claude mentre lavora, e Claude Security, che fa una scansione multi-agent delle vulnerabilità e trasforma in patch i problemi che scegli. Li trovi da `/plugin`, scheda Discover, cercando "security"; il Capitolo 14 spiega installazione e scope.

<!-- VERIFY: nomi esatti dei due plugin nel marketplace per il comando /plugin install -->

C'è poi il comando `/security-review`, che fa una review di sicurezza delle modifiche in sospeso sul branch corrente. Sulla Photogallery lo lancio prima dell'audit finale del prossimo paragrafo: è un buon filtro per i problemi ovvi, così l'audit si concentra sulla configurazione.

security-guidance lavora durante lo sviluppo, `/security-review` e Claude Security a valle. Nessuno dei tre sostituisce l'audit, che controlla anche quello che nel diff non c'è: header mancanti, configurazioni di default, secrets nella history di Git.

## 22.6 Audit di sicurezza: middleware, CSP, HTTPS, secrets

L'audit di sicurezza è l'ultimo passo prima del deploy e merita una sessione e un prompt dedicati. I problemi di sicurezza non sempre emergono come bug durante i test funzionali: un endpoint che non controlla l'autorizzazione risponde 200 e sembra funzionare benissimo, finché qualcuno non ci passa il token di un altro utente.

Il punto di partenza è che i default dei framework sono pensati per lo sviluppo. Laravel pubblica una configurazione CORS con `allowed_origins` a `*`, e la Photogallery ci è cascata: il file `.env.example` documentava `FRONTEND_URL` per la allowlist, ma nessun `config/cors.php` la leggeva, quindi era attiva la wildcard (REVIEW-FIXES, voce S2). Nessun framework attiva una CSP di default, né forza HTTPS o HSTS. Ogni misura di questo paragrafo è esplicita: se non la configuri tu, non la configura nessuno.

### Middleware e header

Il middleware è lo strato che ogni richiesta attraversa prima del controller, quindi è il posto giusto per i controlli di sicurezza: si applica a tutte le route e non puoi dimenticarne una. In Laravel gli header di sicurezza li aggiungi con un middleware tuo:

```php
<?php

declare(strict_types=1);

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

final class SecurityHeaders
{
    public function handle(Request $request, Closure $next): Response
    {
        $response = $next($request);

        $response->headers->set('X-Frame-Options', 'DENY');
        $response->headers->set('X-Content-Type-Options', 'nosniff');
        $response->headers->set('Referrer-Policy', 'strict-origin-when-cross-origin');
        $response->headers->set('Permissions-Policy', 'geolocation=(), microphone=()');

        if (app()->environment('production')) {
            $response->headers->set(
                'Strict-Transport-Security',
                'max-age=31536000; includeSubDomains'
            );
        }

        return $response;
    }
}
```

e lo registri per tutte le richieste in `bootstrap/app.php`, dentro `withMiddleware`:

```php
$middleware->append(\App\Http\Middleware\SecurityHeaders::class);
```

Chi lavora con Node ed Express ottiene gli stessi header con Helmet, una riga: `app.use(helmet())`. Helmet imposta tra gli altri `X-Content-Type-Options: nosniff`, `X-Frame-Options` e `X-XSS-Protection: 0`, che è il valore moderno: il vecchio filtro XSS dei browser è deprecato e disattivarlo è corretto.

CORS: in produzione mai `Access-Control-Allow-Origin: *`. La Photogallery ora consente solo l'origine della SPA, letta dall'ambiente, e solo sulle API. Il pannello Filament su `/admin` resta fuori e tiene le sue regole CSRF:

```php
return [
    'paths' => ['api/*'],
    'allowed_methods' => ['*'],
    'allowed_origins' => [
        env('FRONTEND_URL', 'http://localhost:5173'),
    ],
    'allowed_origins_patterns' => [],
    'allowed_headers' => ['*'],
    'exposed_headers' => ['ETag', 'Retry-After'],
    'max_age' => 0,
    // Token Bearer nell'header Authorization: niente CORS con credenziali
    'supports_credentials' => false,
];
```

Limiti sul body: senza un limite, un attaccante manda un body da 1 GB e ti consuma la memoria del server. In PHP il tetto lo mettono `post_max_size` e `upload_max_filesize`; sopra, la Photogallery valida ogni file con `image|mimes:jpg,jpeg,png,webp|max:10240` (10 MB) e trasforma `PostTooLargeException` in una risposta 413 con l'envelope JSON standard.

Proxy fidati: dietro un load balancer, un CDN o un reverse proxy, devi dire al framework di fidarsi degli IP del proxy. Senza, `$request->ip()` restituisce l'IP del proxy per tutti, il rate limiter per IP diventa un unico secchio condiviso e la protezione contro il credential stuffing non serve più a niente. Nella Photogallery il problema l'ha trovato la review della fase 2 (voce S4), e la correzione in `bootstrap/app.php` legge la configurazione dall'ambiente:

```php
$trustedProxies = env('TRUSTED_PROXIES', '');
if ($trustedProxies !== '') {
    $middleware->trustProxies(
        at: $trustedProxies === '*' ? '*' : explode(',', $trustedProxies),
    );
}
```

In locale `TRUSTED_PROXIES` resta vuota; dietro l'ALB del Capitolo 23 la imposti. In Express l'equivalente è `app.set('trust proxy', 1)`.

### Content Security Policy

La CSP è la difesa più efficace contro il Cross-Site Scripting. Se un attaccante riesce a iniettare JavaScript nelle tue pagine, con una CSP ben configurata il browser si rifiuta di eseguire il codice non autorizzato. Una policy di base che va bene per la maggior parte delle applicazioni:

```text
Content-Security-Policy:
  default-src 'self';
  script-src 'self';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  font-src 'self' https://fonts.gstatic.com;
  connect-src 'self' https://api.tua-app.com;
  frame-ancestors 'none';
  base-uri 'self';
  form-action 'self';
```

`frame-ancestors 'none'` è il sostituto moderno di `X-Frame-Options: DENY`: impedisce che il sito venga incorporato in un iframe di un altro dominio (clickjacking). `'unsafe-inline'` sugli stili spesso serve per CSS-in-JS e stili inline dei componenti; sugli script evitalo, e se hai script inline indispensabili usa i nonce.

La Photogallery ha la sua policy in DESIGN §10.5, ed è una delle mitigazioni che giustificano il token in `localStorage`:

```text
default-src 'self'; img-src 'self' https://cdn.example.com data:; script-src 'self'; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'self'
```

Non attivare la CSP in modalità bloccante al primo deploy. Parti con `Content-Security-Policy-Report-Only` e un `report-uri`, guarda le violazioni per qualche giorno e passa alla modalità bloccante solo quando sei sicuro che non blocchi niente di legittimo:

```text
Content-Security-Policy-Report-Only:
  default-src 'self';
  report-uri https://tua-app.com/api/csp-report;
```

La CSP che conta per la SPA è quella sull'HTML della SPA, non quella sulle risposte JSON delle API. La SPA React esce dalla build di Vite come file statici: la policy va messa dove vengono serviti (sulla distribuzione CloudFront, nel Capitolo 23) o, come rete di sicurezza, in un tag `<meta>` nell'`index.html`, che vale anche quando gli asset arrivano dal CDN senza passare dal server applicativo:

```html
<meta
  http-equiv="Content-Security-Policy"
  content="default-src 'self'; frame-ancestors 'none';"
/>
```

Una precisazione: i browser ignorano `frame-ancestors` quando arriva da un tag `<meta>`, quindi la protezione dal clickjacking deve viaggiare anche in un header HTTP.

### HTTPS e HSTS

In produzione HTTPS è obbligatorio: senza, chiunque sia sulla stessa rete può leggere token, cookie di sessione e dati personali. Ogni richiesta HTTP va rediretta su HTTPS, sia a livello di infrastruttura (load balancer, CloudFront) sia nel codice. In Laravel forzi lo schema degli URL generati in `AppServiceProvider`:

```php
public function boot(): void
{
    if ($this->app->environment('production')) {
        \Illuminate\Support\Facades\URL::forceScheme('https');
    }
}
```

HSTS dice al browser, dopo il primo accesso in HTTPS, di non provare mai più HTTP per un certo periodo. Con `max-age=31536000` (un anno), anche se l'utente digita `http://` nella barra degli indirizzi il browser passa da solo a HTTPS, senza mandare la richiesta in chiaro che potrebbe essere intercettata. Il middleware `SecurityHeaders` di prima lo imposta in produzione:

```text
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

I certificati: con Let's Encrypt verifica che il rinnovo automatico funzioni (`certbot renew --dry-run`); con AWS Certificate Manager il rinnovo è automatico. In ogni caso imposta un alert trenta giorni prima della scadenza, perché un certificato scaduto blocca tutti gli utenti.

### Gestione dei secrets

Un secret finito nel repository resta nella history di Git anche se lo togli nel commit successivo. Prima del deploy faccio una scansione con gitleaks, history compresa:

```bash
# Installazione
brew install gitleaks   # macOS
# oppure: go install github.com/gitleaks/gitleaks/v8@latest

# Scansione completa, inclusa la history di Git
gitleaks detect --source . --verbose
```

Se gitleaks trova qualcosa, quel secret va considerato compromesso: non basta toglierlo, va ruotato.

Nel codice e nei file di configurazione committati non ci va nessun valore sensibile: API key, stringhe di connessione, credenziali SMTP stanno in variabili d'ambiente. In locale e in CI le variabili d'ambiente vanno bene; in produzione usa un secret manager (AWS Secrets Manager, GCP Secret Manager, HashiCorp Vault), che ti dà il registro di chi ha letto cosa e quando, la rotazione automatica e la revoca senza toccare il codice. Le chiavi che non ruoti mai restano valide per sempre se qualcuno le trova: mettiti un promemoria ogni novanta giorni.

L'audit di sicurezza fatto su una delle wave della Photogallery (`docs/BATCH-2025-04-28.md`) ha trovato due problemi di questo tipo: un fallback `'password'` cablato nel seeder dell'utente admin, che sarebbe finito in produzione se la variabile d'ambiente mancava, e un `.env` con `APP_DEBUG=true`. Il primo si corregge facendo fallire il seeder quando la variabile manca; il secondo con `APP_DEBUG=false` fuori dall'ambiente locale e il `.env` nel `.gitignore`.

### Autenticazione

Per le password usa argon2id o bcrypt, mai SHA-256, SHA-512 o MD5: non hanno un work factor configurabile, e con un dump del database e hardware moderno si forzano in fretta. Laravel usa bcrypt di default, e la Photogallery imposta `BCRYPT_ROUNDS=12` in `.env.example`. Per passare ad argon2id basta `HASH_DRIVER=argon2id` nel `.env`, se il tuo PHP è compilato con il supporto argon2.

I token Sanctum della Photogallery scadono dopo 24 ore (`SANCTUM_TOKEN_EXPIRATION=1440`, letta da `config/sanctum.php`: anche questa era rimasta scollegata fino alla review della fase 1, voce F3) e il logout cancella il token corrente con `currentAccessToken()->delete()`. Le token ability (`photos:write`, `albums:write`, `admin`) limitano i danni se un token viene rubato. Sulla scelta di tenere il token in `localStorage` vale quanto detto nel paragrafo 22.4: è un compromesso documentato, non una svista, e se lo cambi la strada è la modalità stateful di Sanctum con cookie HttpOnly, al prezzo di un flusso CSRF più complesso.

### Rate limiting

Un rate limiting senza numeri non protegge niente. La Photogallery ha i limiti di DESIGN §6.0 in `AppServiceProvider`: 10 richieste al minuto per IP sulle route di autenticazione, e sul resto delle API due tetti insieme, 120 al minuto per IP e 300 al minuto per utente autenticato.

```php
private function configureRateLimiters(): void
{
    $authPerIp = (int) config('photogallery.rate_limits.auth_per_ip_per_minute', 10);
    $apiPerIp = (int) config('photogallery.rate_limits.api_per_ip_per_minute', 120);
    $apiPerUser = (int) config('photogallery.rate_limits.api_per_user_per_minute', 300);

    RateLimiter::for('auth', fn (Request $request) => Limit::perMinute($authPerIp)->by($request->ip()));

    RateLimiter::for('api', function (Request $request) use ($apiPerIp, $apiPerUser) {
        $limits = [Limit::perMinute($apiPerIp)->by($request->ip())];
        if ($request->user()) {
            $limits[] = Limit::perMinute($apiPerUser)->by('user:'.$request->user()->id);
        }

        return $limits;
    });
}
```

Le route usano `throttle:auth` e `throttle:api` in `routes/api.php`. Il limite per utente serve perché dietro un NAT o un proxy aziendale molti utenti condividono lo stesso IP, e un limite solo per IP li bloccherebbe tutti insieme. Il limite per IP sull'autenticazione, invece, funziona solo se i proxy fidati sono configurati, come visto sopra. `/api/v1/health` resta fuori dal throttling, così i probe del load balancer non fanno scattare il limiter. Lo stesso audit di wave ha segnalato che il login di Filament non aveva un limite: il pannello admin è una porta d'ingresso come le altre.

### Il prompt dell'audit finale

Questo è l'ultimo prompt che lancio prima di dichiarare il progetto pronto per il deploy, in una sessione dedicata:

```text
Sei un security engineer. Esamina l'intero progetto (codice,
configurazione, dipendenze) e fai un audit pre-produzione.

Verifica esplicitamente:
1. Middleware di sicurezza (header di sicurezza, CORS, limiti sul body)
2. Content Security Policy (presente, configurata correttamente)
3. HTTPS forzato e HSTS
4. Gestione dei secrets (nessun secret nel codice, uso di env vars)
5. Password hashing (algoritmo corretto, work factor adeguato)
6. Token e sessioni (scadenza, revocabilità, storage sicuro)
7. Rate limiting (login, registrazione, API generale, pannello admin)
8. Trusted proxies configurati
9. Input validation completa (ogni endpoint esterno)
10. Autorizzazione su ogni route (nessun endpoint privo di auth check)

Per ogni punto:
- Stato: OK / PROBLEMA / NON VERIFICABILE
- Se PROBLEMA: descrizione del rischio e fix consigliato
- Priorità: Bloccante / Alta / Media

Separa i problemi del codice dai problemi di configurazione d'ambiente
(questi ultimi si risolvono in fase di deploy, non nel codice).
```

L'ultima istruzione separa due liste di lavoro diverse. I problemi del codice li chiudi nel repository, adesso. Quelli di configurazione (`TRUSTED_PROXIES`, `APP_DEBUG`, la CSP sulla distribuzione CloudFront, il secret manager) diventano voci del provisioning, e li ritrovi nel template CloudFormation del Capitolo 23.

## Riepilogo

- La checklist pre-deploy copre flussi funzionali, performance, sicurezza di base, integrità dei dati e osservabilità, e si esegue uno o due giorni prima del rilascio: se una voce non passa, il deploy non parte.
- I task orfani si stanano con grep e con un subagent dedicato; per ognuno scegli tra Delete, Complete e Document and defer.
- `/code-review` a effort alto prima di ogni push, con `--fix` e `--comment` per agire sui risultati; le correzioni di `--fix` si annullano con Git, non con `/rewind`.
- `REVIEW.md` personalizza Code Review su GitHub (Team ed Enterprise) ma non il comando locale, che legge solo `CLAUDE.md`; ultrareview è per le PR grandi o critiche.
- Un secondo modello resta utile sulle parti critiche prima del deploy: sulla Photogallery ha trovato `is_admin` fillable e gli URL firmati generati prima della policy.
- L'audit finale separa i problemi del codice da quelli di configurazione, che passano al provisioning.

## Esercizio

Esegui la QA pre-deploy completa sulla tua Photogallery, partendo dal branch `book/cap-14-phases-complete`.

1. Crea un branch dedicato: `git switch -c cap-22-pre-deploy-qa`.
2. Lancia il grep dei task orfani e il subagent con il prompt del paragrafo 22.2, e applica la regola delle tre D a ogni finding.
3. Aggiungi il `REVIEW.md` del paragrafo 22.3 e lancia `/code-review high main...cap-22-pre-deploy-qa`.
4. Manda il prompt della review multi-LLM ad almeno un secondo modello (Gemini, Codex o Kimi) sul diff dei controller e delle Actions, e aggrega i finding per consenso.
5. Lancia `/security-review` e poi il prompt dell'audit finale del paragrafo 22.6.
6. Correggi in una sessione nuova tutti i finding critici e alti, poi rilancia `/code-review high` e la suite di test.

L'esercizio è finito quando `./vendor/bin/sail test` e `pnpm test` passano, l'ultima `/code-review high` non riporta problemi Important e i problemi di configurazione sono scritti in una lista a parte per il Capitolo 23. Ci vogliono 3-4 ore; non affrettare l'aggregazione dei finding, è lì che decidi cosa correggere davvero.

Il branch di riferimento è `book/cap-15-post-review-fixes` nel repository `claude-code-book-photogallery`: contiene tutte le correzioni della review (3 CRITICAL, 7 HIGH, 14 MEDIUM e 7 LOW, più la correzione della fuga dei dati EXIF con le route firmate) e un `docs/DESIGN.md` allineato all'implementazione reale.
