# Capitolo 17. Photogallery, dal prompt alle specifiche

## Cosa imparerai

Come si passa da un'idea scritta in dieci righe a una specifica tecnica che Claude Code può eseguire senza inventare niente. Parti da un prompt che descrive il problema, scegli lo stack con argomenti presi dai requisiti, iteri un brief fino a farlo diventare un megaprompt, generi la spec e la rivedi area per area. Alla fine sai anche quando smettere di iterare, e perché saltare questa fase costa più di quanto fa risparmiare.

Prerequisiti: i capitoli 1-16, in particolare Plan Mode (Capitolo 4) e `CLAUDE.md` (Capitolo 7), più le basi del web: API REST, SQL relazionale, autenticazione a token. Laravel e React non sono richiesti: li incontri attraverso le spec.

Fin qui hai lavorato su progetti contenuti: uno script Python, un'analisi dati, una landing page. Da questo capitolo costruiamo Photogallery, un'applicazione full-stack per gestire fotografie, e la portiamo fino al deploy su AWS. È piccola abbastanza da stare in testa e abbastanza ricca da costringerti alle decisioni che contano: autenticazione, upload di file, code, relazioni molti-a-molti, paginazione, ricerca, cloud. E il dominio lo conosci già, quindi l'attenzione resta sulle scelte tecniche. Le funzionalità:

- caricamento di foto JPEG, PNG e WebP fino a 10 MB ciascuna, da 1 a 20 file alla volta;
- album, tag e ricerca per titolo, descrizione, tag, album e preferite;
- galleria a griglia masonry con lightbox a schermo intero e scorciatoie da tastiera (`←`, `→`, `Escape`, `F`, `Delete`, `/`);
- elaborazione asincrona: l'upload risponde subito, poi un job in coda genera tre formati (300, 800 e 1600 px di larghezza) ed estrae i dati EXIF;
- lo stesso codice in locale e in produzione: disco locale e coda su database sul portatile, S3 e SQS su AWS, cambiano solo le variabili d'ambiente;
- autenticazione con token Sanctum e un pannello admin Filament su `/admin`, con il monitoraggio della coda.

Qui scegli lo stack e scrivi le specifiche. Il Capitolo 18 le trasforma nei tre file canonici dello Spec Driven Development, il 19 esegue il piano con la code review, il 20 lancia le wave in parallelo, il 21 aggiunge feature a progetto avviato, il 22 fa il QA prima del deploy e il 23 porta tutto su AWS con CloudFormation.

Il codice è nel repo companion `github.com/hidran/claude-code-book-photogallery`. Ogni fase del libro ha il suo branch, e i nomi seguono la numerazione della prima edizione: questo capitolo corrisponde a `book/cap-11-prompts-and-spec` (il motivo è spiegato in "Come leggere questo libro"). In quel branch non c'è ancora codice, solo prompt e spec.

## 17.1 Prompt base: scegliere lo stack consapevolmente

Il primo prompt di un progetto pesa più degli altri. Se è sbagliato produce codice plausibile che si rivela sbagliato settimane dopo, quando tornare indietro costa.

### Descrivi il cosa, non il come

La tentazione è aprire con una lista di tecnologie. Il primo prompt invece descrive il problema:

```text
Voglio costruire un'applicazione web full-stack per una galleria di foto.
Gli utenti devono poter:
- caricare foto (JPEG, PNG, WebP, max 10 MB) singolarmente o in batch
- organizzare le foto in album
- taggare le foto con parole chiave libere
- cercare per titolo, tag, album e preferite
- vedere le foto in griglia con lightbox a schermo intero
- navigare con i tasti freccia da tastiera
- marcare le foto come preferite
- registrarsi e autenticarsi

Ci deve essere un pannello di amministrazione.
L'app deve funzionare in locale per lo sviluppo e su AWS in produzione.

Non scegliere ancora lo stack. Prima dimmi quali stack
consiglieresti per questo tipo di progetto, con i tradeoff
di ognuno. Voglio tecnologie standard e mature, niente hype.
```

L'ultima frase chiede un confronto prima della scelta. Invece di andare dritto al codice, come nel vibecoding, usi Claude come consulente per la fase di design. Nota anche cosa manca: nessun framework, nessun database, nessuna libreria. Se parti dallo stack escludi in partenza le soluzioni a cui non avevi pensato; se parti dai requisiti, lo stack lo ricavi.

::: {.callout .callout-tip}
[Suggerimento]{.callout-title}

Per il lavoro di design e per le spec alza il livello di ragionamento con `/effort high` (il selettore va da `low` a `xhigh`). Per una singola domanda difficile basta scrivere `ultrathink` nel messaggio: vale solo per quel prompt.
:::

### Le alternative che propone Claude

Claude risponde con due o tre stack candidati. Una risposta tipica ha questa forma.

Stack A: Node.js con Express o Fastify, PostgreSQL, React con Vite. Un solo linguaggio, tanta documentazione, deploy semplice. Il contro è che Express non impone una struttura: moduli e layer li organizzi tu.

Stack B: NestJS con React, TanStack Query e MySQL. TypeScript ovunque, dependency injection e decoratori già pronti, una struttura modulare che regge la crescita. Il contro è una curva di apprendimento più ripida e un po' di boilerplate all'inizio.

Stack C: Laravel con Filament per il pannello admin, e sul frontend Inertia con React oppure una SPA React separata che consuma un'API REST. Velocità di sviluppo alta e un admin quasi pronto. Il contro è lo stack misto, PHP sul backend e TypeScript sul frontend.

Sono validi tutti e tre. La domanda utile è quale si adatta meglio ai tuoi requisiti, a quello che il team sa già fare e al posto dove andrà in produzione.

### Leggere la risposta con occhio critico

Non fermarti alla colonna dei pro. Fai domande di follow-up sui requisiti che pesano di più:

```text
Per lo Stack B con NestJS: il pannello admin deve avere CRUD,
filtri, bulk action e un widget sullo stato della coda.
Quanto di questo devo scrivere a mano?
```

```text
Per lo Stack C con una SPA React separata: come gestisco
l'autenticazione? Sanctum in modalità token o in modalità cookie,
con quali compromessi di sicurezza?
```

Sono le domande che tirano fuori i tradeoff che la prima risposta non mostra. Un pannello admin con tabelle, filtri, bulk action e permessi scritto da zero sono settimane di lavoro, anche se nell'elenco dei requisiti occupa una riga. Claude risponde bene a domande precise; da solo non le anticipa tutte.

### La scelta: Laravel 13, Filament v5 e React 19

Photogallery usa lo Stack C nella variante con API separata. Un backend Laravel 13 espone un'API REST JSON sotto `/api/v1`, il pannello Filament v5 è montato nella stessa applicazione su `/admin`, e una SPA React 19 con Vite 6 e Tailwind CSS v4 consuma l'API. La SPA si autentica con i token di Laravel Sanctum. I motivi vengono dai requisiti, uno alla volta.

Il pannello admin è un requisito, e Filament lo copre quasi per intero: resource con tabelle, filtri, bulk action, form e widget, dentro la stessa app e sugli stessi modelli Eloquent. Con NestJS quel pannello andava scritto.

"In locale e su AWS" si traduce in due astrazioni che Laravel ha già: la facade `Storage` e i driver delle code. In sviluppo il disco è locale e la coda gira sul database, in produzione diventano S3 e SQS; il codice chiama sempre `Storage::disk('photos')` e cambia solo il file `.env`. L'elaborazione delle immagini è un job accodato con retry e backoff, il caricamento in batch usa il batching delle code con la tabella `job_batches`, e Sanctum gestisce nello stesso progetto token Bearer per la SPA e sessione web per Filament.

Il frontend resta una SPA separata, in TypeScript. Inertia avrebbe eliminato l'API, ma qui un'API versionata serve: la SPA si builda e si deploya per conto suo, e il contratto tra i due lati diventa un documento che puoi verificare. Il database è relazionale, MySQL o MariaDB, con un indice FULLTEXT per la ricerca e RDS in produzione. L'ultimo motivo è il più pratico: il team conosce PHP e Laravel, e il costo di apprendimento di uno stack è un requisito non funzionale come gli altri.

Nella prima stesura di questo progetto la scelta era NestJS, per avere TypeScript su entrambi i lati. È cambiata durante l'iterazione delle spec, quando pannello admin, code e storage sono passati da righe di un elenco a requisiti con i loro dettagli. Il workflow dei prossimi capitoli è lo stesso con qualunque stack.

Comunica la scelta a Claude, insieme ai vincoli:

```text
Scelgo lo Stack C, nella variante con API separata:
backend Laravel 13 (API REST JSON) + Filament v5 per l'admin,
frontend React 19 + Vite 6 + Tailwind CSS v4 come SPA separata.
Motivi: Filament copre il pannello admin; Storage e code di Laravel
passano da locale ad AWS cambiando solo le variabili d'ambiente;
il team conosce PHP e Laravel.

Vincoli da rispettare in tutte le spec:
- API sotto /api/v1
- Autenticazione della SPA con token Sanctum (header Authorization: Bearer),
  non cookie; Filament usa la sessione web standard
- Upload multipart verso l'API, da 1 a 20 file per richiesta;
  la risposta arriva subito, resize ed EXIF girano in un job in coda
- Chiavi primarie UUID su tutte le tabelle
- Tailwind v4 solo con il plugin @tailwindcss/vite: niente
  tailwind.config.js, niente postcss.config.js

Usa questa scelta per tutto il progetto.
```

I vincoli servono a prevenire le derive. Senza, nelle spec Claude potrebbe proporre l'autenticazione a cookie, un `tailwind.config.js` che Tailwind v4 non usa, il resize dentro il controller: scelte plausibili e contrarie a quello che hai deciso. Nel repo questi vincoli finiscono anche nel `CLAUDE.md` del progetto, tra le regole critiche: la quinta dice che il setup di Tailwind v4 "is non-negotiable".

### L'anti-pattern della scelta non motivata

"Uso React perché lo conosco, Express perché è semplice e MongoDB perché non voglio pensare allo schema." Per un side project da solo funziona. Per un progetto che deve reggere in produzione, o che dovrà mantenere qualcun altro, no. Prima del primo file chiediti se lo stack regge i requisiti non funzionali, se il team lo conosce o può impararlo a un costo accettabile, se ha documentazione e supporto a lungo termine, e come si comporta in produzione tra deploy, monitoraggio e debug. Claude ti aiuta su ognuna di queste domande, se gliela fai. Un ultimo controllo utile prima di fissare lo stack:

```text
Elenca i tre rischi principali dello stack che ho scelto per Photogallery.
Per ognuno dimmi come lo vedrei arrivare e cosa posso fare adesso, in fase
di spec, per ridurlo.
```

Se ai rischi che emergono non sai rispondere, ti mancano informazioni per scegliere. Se sai rispondere, vai avanti.

## 17.2 Dal prompt base al brief tecnico

Hai lo stack e un'idea chiara delle funzionalità. Il passo successivo è il brief tecnico, un documento che uno sviluppatore potrebbe leggere e usare per costruire il sistema senza farti altre domande. Si scrive prima del codice e resta la fonte di verità per tutta la durata del progetto.

La differenza con il prompt base è concreta:

| Prompt base | Brief tecnico |
| :---- | :---- |
| "Vuole caricare foto" | Da 1 a 20 file per richiesta, JPEG, PNG o WebP, massimo 10 MB ciascuno. L'originale si salva subito e la risposta è immediata; i tre formati e l'EXIF li produce un job in coda, con 3 tentativi |
| "Autenticazione utenti" | Token Sanctum per la SPA con header `Authorization: Bearer`, sessione web per Filament. Le GET sono pubbliche, le scritture richiedono token e proprietà della risorsa |
| "Deve andare in produzione" | Stesso codice in locale e su AWS: coda su database e disco locale in sviluppo, SQS e S3 in produzione. Cambiano solo le variabili d'ambiente |
| "Gli utenti gestiscono le loro foto" | Ogni foto e ogni album hanno un proprietario (`user_id`). In v1 la cancellazione è definitiva, senza soft delete; cancellare un album lascia le sue foto senza album |

Ogni riga del brief è una decisione presa e scritta prima del codice. Ogni riga del prompt base è una decisione lasciata a Claude, che sceglierà qualcosa di ragionevole ma non per forza quello che avevi in testa.

### Round 1: il primo draft

Per il primo draft usa un prompt generico, che ti servirà anche per i prossimi progetti. Per Photogallery il contesto sono le funzionalità del prompt base, e lo stack è quello appena scelto con i suoi motivi.

::: {.callout .callout-prompt}
[Prompt riusabile]{.callout-title}

Brief tecnico in una sessione. Sostituisci i campi tra parentesi quadre e itera 2-3 volte prima di considerare il brief pronto. I punti 5 e 6 sono i temi del round 2.

```text
Contesto: sto costruendo [descrizione del progetto in 2-3 frasi].
Stack tecnologico: [lista dello stack scelto con motivazione].

Genera un brief tecnico strutturato che includa:
1. Requisiti funzionali: funzionalità per ruolo (visitatore / utente / admin)
   con criteri di accettazione per ognuna
2. Requisiti non funzionali: prestazioni, sicurezza (autenticazione,
   autorizzazione, validazioni), scalabilità (ordine di grandezza
   degli utenti e dei dati attesi)
3. Vincoli: stack bloccato, hosting target, budget indicativo, tempi
4. Decisioni tecniche chiave: strategia di autenticazione (token / sessioni),
   upload (via API / presigned URL), approccio al DB (migration / ORM /
   SQL), storage (locale / S3 / altro)
5. Fuori scope: cosa non costruiamo nella prima versione, e perché
6. Quote, limiti e audit log, se sono in scope

Genera un documento di 3-4 pagine in Markdown.
Dopo il draft aspetta la mia revisione prima di procedere
con le specifiche operative.
```
:::

Leggi ogni sezione del draft con attenzione. Qualcosa che manca, o che non corrisponde a quello che hai in testa, lo trovi sempre: è normale per un primo draft. Il tuo lavoro è trovare i buchi e descriverli con precisione nei round successivi. Cosa cercare:

- Le funzionalità sono verificabili? "L'utente può cercare le foto" non lo è. "La ricerca filtra per titolo e descrizione, per uno o più tag in AND, per album e per preferite, con risultati paginati" lo è.
- I requisiti non funzionali descrivono comportamenti osservabili? "L'app deve essere veloce" non è un requisito. "La griglia ha 2 colonne su mobile, 3 su tablet e 4 su desktop" e "la risposta all'upload non aspetta il resize" lo sono.
- Le decisioni sono motivate? Se il brief dice token Sanctum deve dire anche perché: SPA e API sono due artefatti separati, e un header `Authorization: Bearer` evita il giro di CSRF dei cookie.

### Round 2: decidere cosa resta fuori

Un primo draft tende a crescere. Quote di spazio per utente, audit log, soft delete con cestino, commenti sotto le foto: sono idee sensate, e ognuna pesa sullo schema e sulle query. Un `deleted_at`, per esempio, obbliga ogni query a escludere i record cancellati. Decidi adesso cosa entra in v1 e scrivilo:

```text
Aggiungi al brief una sezione "Fuori scope (v1)". Elenca in modo
esplicito cosa non costruiamo nella prima versione:
- soft delete e ripristino: le cancellazioni sono definitive
- quote per utente (spazio, numero di foto)
- commenti, like e reazioni
- modifica delle immagini (crop, rotazione, filtri), tranne
  l'auto-orientamento da EXIF al caricamento
- app native iOS e Android
- autenticazione a due fattori
- interfaccia multilingua

Per ogni voce aggiungi una riga sul perché la rimandiamo.
```

La sezione serve anche a Claude: una voce scritta fuori scope smette di comparire nelle risposte come aggiunta "per completezza". Nel progetto finale questa lista vive in `docs/REQUIREMENTS.md`, nella sezione "Out of scope (v1)".

### Round 3: upload ed elaborazione delle immagini

L'upload è la parte più delicata del sistema, e le strade sono due.

Con le presigned URL di S3 il client chiede al backend un URL firmato e carica il file direttamente nel bucket. Il backend non tocca mai i byte e scala senza fatica. In cambio la validazione arriva dopo che il file è già su S3, e in sviluppo ti serve un S3 locale anche solo per caricare una foto.

Con l'upload attraverso l'API il client manda una richiesta multipart a Laravel. Una FormRequest controlla tipo e dimensione prima che venga salvato qualsiasi cosa, il controller salva l'originale e risponde subito, e il lavoro pesante (resize ed EXIF) passa a un job in coda. I byte attraversano il backend, ma con file da 10 MB e al massimo 20 per richiesta è un costo che v1 si può permettere, e lo stesso codice gira con il disco locale.

Photogallery prende la seconda strada. Se un giorno l'upload diventerà il collo di bottiglia, le presigned URL saranno l'evoluzione naturale, e la spec è il posto dove scriverlo. Il round 3 definisce la pipeline:

```text
Rivedi la sezione sull'upload. L'upload passa dall'API Laravel
come multipart/form-data, da 1 a 20 file per richiesta.

Quando arriva una foto:
1. Salva subito l'originale
2. Rispondi subito, senza far aspettare l'utente
3. Accoda un job che genera tre formati:
   - thumbnail: 300 px di larghezza, qualità JPEG 80%
   - medium: 800 px, qualità 85%
   - large: 1600 px, qualità 90%
4. Il job estrae anche i dati EXIF (fotocamera, ISO, diaframma, ecc.)
5. Traccia lo stato nel database: pending, processing, completed, failed
6. Se il job fallisce riprova fino a 3 volte, poi segna la foto come failed

In sviluppo: coda su database e filesystem locale.
In produzione: coda AWS SQS e storage S3, stesso codice, cambiano
solo le variabili d'ambiente. Per le immagini usa Intervention Image v3.

Aggiorna il brief con il flusso e con le implicazioni per la sicurezza:
chi può vedere l'originale, e quali dati EXIF non vanno pubblicati.
```

La domanda sulla sicurezza, nella spec finale, produce due dischi distinti. `photos_private` contiene gli originali, che non vengono mai serviti in pubblico e si raggiungono solo con URL firmati validi 5 minuti. `photos` contiene i tre formati generati ed è pubblico. Le coordinate GPS vengono tolte dai dati EXIF prima del salvataggio.

### Round 4: il brief diventa il megaprompt

Dopo tre o quattro round il brief contiene dettagli che al primo colpo non avresti scritto. Nel repo la versione finale è `docs/PROMPT.md`, il megaprompt da cui Claude genera la spec. Descrive cosa fa l'app, l'architettura in due cartelle (`backend/` e `frontend/`), le entità del database con i campi principali, la pipeline del round 3, gli endpoint sotto `/api/v1`, il pannello Filament, le funzionalità del frontend (fino al debounce di 300 ms sulla ricerca), autenticazione, errori, dettagli tecnici come Tailwind v4 senza file di configurazione, il piano di test e infine i principi di ingegneria: SOLID, REST, KISS e DRY, con esempi presi da questo progetto.

Quest'ultima sezione è arrivata con un commit a parte ("Adds SOLID, KISS, DRY principles") ed è quella che rende la spec opinionata. Un estratto, tradotto dall'inglese del repo:

```text
### KISS
- Niente astrazioni premature: non creare un Repository se c'è
  un solo uso del modello Eloquent. Usa il modello direttamente.
- Niente ottimizzazioni premature: non aggiungere una cache Redis
  prima di aver misurato che il database è lento.
- Pattern standard di Laravel: Eloquent, Form Request, API Resource,
  Policy. Niente middleware custom per cose che Laravel fa già.
- Leggibile prima che furbo: un metodo ovvio di 10 righe batte
  un metodo di 3 righe fatto di closure dentro closure.
```

La chiusura del megaprompt dice cosa generare. All'inizio chiedeva un solo file, `SPEC.md`; l'ultima versione chiede quattro file (`CLAUDE.md`, `docs/REQUIREMENTS.md`, `docs/DESIGN.md`, `docs/TASKS.md`) ed è il ponte verso il Capitolo 18. Nel branch trovi anche `docs/megaprompt-template.md`, la stessa struttura con i campi da riempire, pronta per il tuo progetto.

Iterare il brief costa poco: riscrivere un paragrafo è questione di minuti. Correggere lo stesso errore quando è già diventato migration, controller e componenti vuol dire toccare ogni file in cui si è propagato. Il tempo va speso qui.

## 17.3 Generare le specifiche complete

Il brief dice cosa costruisci e perché. La spec dice come funziona ogni pezzo, in forma di contratto: lo schema ha quelle colonne o non le ha, l'endpoint risponde con quella forma o è sbagliato.

Un esempio sui tag. Il brief dice "gli utenti taggano le foto con parole chiave libere". La spec finale di Photogallery dice:

- tabella `tags` con `id` UUID, `name` VARCHAR(100) unico, `slug` VARCHAR(120) unico, timestamp gestiti da Laravel;
- lo slug nasce dal nome con `Str::slug()` nell'hook `booted()` del modello, e in caso di collisione riceve un suffisso numerico (`-2`, `-3`);
- i tag sono globali, senza `user_id`: due utenti che usano "sunset" puntano allo stesso record;
- la pivot `photo_tag` ha la chiave primaria composta (`photo_id`, `tag_id`), un `created_at` e `ON DELETE CASCADE` su entrambe le foreign key;
- `GET /api/v1/tags` restituisce tutti i tag con il conteggio delle foto (`withCount('photos')`), senza paginazione perché l'insieme è piccolo;
- `POST /tags` non esiste: un tag nuovo si crea passando `new_tags[]` nell'upload o nella modifica di una foto.

Nessuna di queste righe si ricava dal brief. Con la spec, invece, Claude può scrivere migration, modello, controller e test senza farti domande.

### Dal megaprompt a SPEC.md

Nel branch ci sono due spec. `SPEC-original.md` è la prima, generata da un prompt più corto: circa 13 KB, tre tabelle applicative più la pivot, un flag `is_favorite` sulla foto, SQLite in sviluppo e PostgreSQL in produzione.

![SPEC-original.md in VS Code alla tabella dello stack, con Claude Code nel terminale sotto](figures/cap-17/fig-01.png)

`SPEC.md` è quella finale, generata dal megaprompt e poi rivista: circa 123 KB, quasi 2.400 righe in 15 sezioni, dallo schema del database alla disciplina di test e commit, più un'appendice sulle variabili d'ambiente. Tenere anche la prima versione ha senso: il confronto tra le due mostra quanto lavoro fanno le iterazioni.

![SPEC.md affiancato alla sua anteprima Markdown: la tabella dello stack con le voci separate per sviluppo e produzione](figures/cap-17/fig-02.png)

Generare tutto in un colpo dal megaprompt va bene. Rivederlo tutto in un colpo no: un documento di quelle dimensioni letto per intero ti fa approvare inconsistenze che, prese una sezione alla volta, vedresti subito. La revisione quindi procede per area, nell'ordine in cui le aree dipendono l'una dall'altra:

1. database
2. API
3. autenticazione
4. pannello admin e frontend
5. build workflow

Per ogni area scrivi un prompt di revisione, leggi il diff e approvi. Una sessione per area tiene pulito il contesto; tra un'area e l'altra usa `/clear`. I prompt di revisione del branch sono in inglese (`docs/database-refinement.md`, `docs/api-refinement.md`, `docs/claude-code-build-workflow.md`); qui li trovi tradotti.

### Spec DB: schema e vincoli

```text
Rivedi lo schema del database in SPEC.md. Per ogni tabella verifica che:
1. Ogni colonna abbia un tipo E i vincoli (nullable, default, unique,
   foreign key)
2. Il comportamento ON DELETE delle foreign key sia specificato
   (cascade, set null, ecc.)
3. La tabella pivot abbia una chiave primaria composta
4. Tutte le colonne timestamp siano specificate

Aggiorna la spec con i dettagli mancanti.
```

Poi leggi lo schema come il DBA che deve approvare le migration. I punti da controllare uno per uno:

- `photo_tag` ha la chiave primaria composta (`photo_id`, `tag_id`) e nessun `id` separato? Con un id generato la stessa coppia potrebbe comparire due volte; la chiave composta lo impedisce per costruzione.
- Ogni foreign key dichiara `ON DELETE`? In Photogallery cancellare un album mette a `NULL` l'`album_id` delle sue foto, che restano; cancellare la foto usata come copertina mette a `NULL` il `cover_photo_id` dell'album; cancellare una foto elimina le sue righe in `photo_tag`, mentre i tag restano.
- C'è un indice su ogni foreign key e sulle colonne usate per filtrare e ordinare?
- Chi scrive i timestamp? La spec finale dice che `created_at` e `updated_at` li gestisce Eloquent: colonne nullable, senza default lato database. Se la spec tace, Claude sceglie per te.
- Ci sono dipendenze circolari? `albums.cover_photo_id` punta a `photos`, e `photos.album_id` punta ad `albums`. La spec risolve con tre migration: prima `albums` senza la foreign key della copertina, poi `photos`, infine una migration che aggiunge il vincolo. Senza questa nota la prima `migrate:fresh` fallisce.

### Spec API: endpoint e convenzioni

```text
Rivedi la sezione API. Per ogni endpoint verifica che:
1. Tutti i parametri di query di GET /photos siano elencati con il tipo
2. Il formato della risposta sia descritto (quali campi, quali relazioni
   annidate)
3. Le risposte di errore siano specificate (quali status code, quale
   formato del messaggio)
4. L'endpoint di upload specifichi multipart/form-data e i nomi dei campi

Aggiorna la spec.
```

Le convenzioni vanno scritte una volta sola, in testa alla sezione, e ogni endpoint le eredita. Nella spec finale stanno nel paragrafo 6.0: base URL `/api/v1`, risposte sempre JSON, multipart solo per gli upload, header `Authorization: Bearer` sulle rotte protette, rate limit per IP e per utente autenticato, ogni payload avvolto in `{ "data": ... }`, ETag su `GET /photos/{id}` e `GET /albums/{id}`. Quando rivedi un dominio dopo l'altro, fai rileggere a Claude quel paragrafo prima di toccare il resto:

```text
Leggi la sezione 6.0 di SPEC.md (envelope, paginazione, formato degli
errori, rate limit). Poi rivedi gli endpoint degli album e allineali
alle stesse convenzioni degli endpoint delle foto.
```

È il modo più semplice per evitare che ogni dominio finisca con convenzioni leggermente diverse.

### Spec auth: token Sanctum e un compromesso dichiarato

Filament usa la sessione standard di Laravel con la guard `web`. La SPA usa Sanctum in modalità token: gli endpoint sono `register`, `login`, `logout` e `me`, il login restituisce `{ "data": { "token": ..., "expires_at": ..., "user": ... } }`, il token dura 24 ore e Axios lo aggiunge come header `Authorization: Bearer`.

La parte più utile della sezione è una decisione scritta insieme alle sue conseguenze. Il token sta nel `localStorage`, sotto la chiave `pgp_token`, dove qualunque script iniettato con un attacco XSS può leggerlo. L'alternativa più sicura è la modalità cookie di Sanctum, che costa un flusso CSRF più complicato. La spec sceglie il token e mette per iscritto le mitigazioni: TTL di 24 ore invece di 30 giorni, una Content Security Policy stretta in produzione, `dangerouslySetInnerHTML` vietato da una regola ESLint, token con abilità limitate (`photos:write`, `albums:write`) che non arrivano ai permessi di admin. E fissa la condizione per cambiare idea: se l'uso multi-utente diventa il caso principale, si passa ai cookie.

Una decisione scritta così non torna in discussione a ogni sessione, né per te né per Claude.

### Spec admin e frontend

Prima di scrivere una riga di React la spec deve rispondere ad alcune domande: quante pagine ci sono e quali richiedono il login, com'è fatta la gerarchia dei componenti, dove vive lo stato del server e dove quello locale, come si gestiscono caricamento, errori e rete assente. Il prompt di revisione chiede proprio questo: rotte con path e accesso, componenti con props tipizzate, i flussi principali passo per passo (login, upload con polling dello stato, filtri, ricerca, lightbox da tastiera), per ogni query TanStack Query la `queryKey` e le mutation che la invalidano.

La spec finale risponde con cinque rotte (`/`, `/favorites`, `/albums/:albumId`, `/login` e una pagina 404), ogni pagina caricata con `React.lazy`, lo stato del server solo in TanStack Query e un client Axios con `baseURL: '/api/v1'` che davanti a un 401 cancella il token e porta a `/login`.

Per Filament la spec scende allo stesso livello di dettaglio, resource per resource. La tabella di `PhotoResource` mostra miniatura, titolo, album, tag come badge, dimensione del file, toggle dei preferiti e stato di elaborazione colorato; i filtri coprono album, tag, preferite, intervallo di date e stato; le bulk action cancellano, assegnano a un album, cambiano i preferiti e rilanciano l'elaborazione. La dashboard ha tre widget: statistiche generali, ultimi upload e monitor della coda.

![L'anteprima di SPEC-original.md alla sezione del pannello Filament: resource, filtri e bulk action](figures/cap-17/fig-03.png)

### Il build workflow

L'ultima sezione da chiedere è l'ordine di costruzione:

```text
Aggiungi alla spec una sezione "Claude Code Build Workflow".
Elenca l'ordine esatto di costruzione, fase per fase:

Fase 1: fondamenta del backend (modelli, migration, seed)
Fase 2: layer API (controller, route, resource, request)
Fase 3: pannello admin Filament (resource, widget, dashboard)
Fase 4: setup del frontend React (scaffold, Tailwind v4, servizio API)
Fase 5: componenti React (griglia, lightbox, upload, sidebar, tastiera)
Fase 6: pipeline di elaborazione delle immagini (job, coda, batch)
Fase 7: monitoraggio della coda in Filament (widget, azioni di reprocess)
Fase 8: migrazione ad AWS (S3 + SQS tramite variabili d'ambiente)
Fase 9: hook (formattazione automatica, test automatici, sicurezza)
Fase 10: test (Pest + Vitest + Playwright)
Fase 11: Git + PR (GitHub MCP)
Fase 12: sviluppo multi-agent in parallelo
Fase 13: spec check finale + deploy

Per ogni fase scrivi il prompt esatto da dare a Claude Code.
```

Il risultato è la sezione 13 di `SPEC.md`, il runbook operativo. Ogni fase ha un obiettivo, un prompt da incollare in Claude Code, un blocco di verifica da lanciare e il messaggio del commit finale: la Fase 1, per esempio, si chiude con `feat(backend): database schema, models, and seeders`. Ogni prompt dalla Fase 2 in poi è preceduto dallo stesso preambolo, qui tradotto:

```text
Stai lavorando in questo repo. La spec è SPEC.md nella root ed è
autoritativa. Leggi le sezioni citate nel prompt e seguile alla lettera.
NON inventare campi, endpoint o percorsi di file che non sono nella spec.
Esegui la verifica prima di dichiarare il lavoro finito. Alla fine
committa con il messaggio indicato nel prompt.
```

Nel Capitolo 18 queste fasi diventano `docs/TASKS.md`: 124 task atomici in 14 fasi, con dipendenze e indicazioni su cosa può girare in parallelo.

### Cosa c'è nel branch

Alla fine di questa fase il branch `book/cap-11-prompts-and-spec` contiene dieci file:

```text
CLAUDE.md
SPEC-original.md
SPEC.md
docs/
  PROMPT.md
  megaprompt-template.md
  database-refinement.md
  api-refinement.md
  claude-code-build-workflow.md
  SPEC-REVIEW.md
  SPEC-VALIDATION.md
```

`SPEC-REVIEW.md` e `SPEC-VALIDATION.md` sono il prodotto della sezione 17.4. `CLAUDE.md` è la costituzione del progetto (Capitolo 7): dice come si lavora nel repo e rimanda a `SPEC.md` per cosa costruire. La prima delle regole critiche è "`SPEC.md` is authoritative"; la quarta, "Ask before deviating", chiede a Claude di segnalare un punto della spec che sembra sbagliato e proporre opzioni, invece di correggerlo in silenzio.

## 17.4 Iterare le spec: DB e API più solidi

La prima spec di Claude è un buon punto di partenza e niente di più. Come un programmatore esperto al primo giro, produce qualcosa di giusto nella sostanza e incompleto nei dettagli che vengono dall'esperienza: tipi espliciti, vincoli, indici sulle colonne giuste, una forma di risposta uguale per tutti gli endpoint, una paginazione che regge quando le righe crescono.

Una rilettura che finisce con "sembra tutto a posto" dice solo che mancano errori evidenti. I problemi veri stanno nelle assunzioni implicite: una colonna senza `NOT NULL` che accetterà valori nulli, un endpoint senza il caso 403 che il frontend gestirà con un fallback generico.

### Iterazione 1: tipi e vincoli espliciti

Il modo più rapido per vedere cosa fa questa iterazione è confrontare la tabella `photos` nelle due spec del branch. Alcune righe di `SPEC-original.md`:

```text
| id          | uuid        | primary key, default uuid() |
| path        | string(255) | not null (storage path)     |
| file_size   | integer     | nullable (bytes)            |
| is_favorite | boolean     | default false               |
```

Le righe corrispondenti, e quelle nuove, in `SPEC.md`:

```text
| id                  | CHAR(36)         | NOT NULL | —         | PRIMARY KEY (UUID v7) |
| user_id             | CHAR(36)         | NOT NULL | —         | FK users(id), ON DELETE CASCADE |
| original_path       | VARCHAR(500)     | NOT NULL | —         | disco privato, mai servito in pubblico |
| thumbnail_path      | VARCHAR(500)     | NULL     | NULL      | scritto dal job ProcessPhoto |
| file_size           | BIGINT UNSIGNED  | NOT NULL | —         | byte |
| processing_status   | ENUM('pending','processing','completed','failed') | NOT NULL | 'pending' | |
| processing_attempts | TINYINT UNSIGNED | NOT NULL | 0         | |
| processing_error    | TEXT             | NULL     | NULL      | messaggio dell'eccezione |
```

È comparso il proprietario, perché il modello di autorizzazione dice che ognuno modifica solo le proprie foto. Il percorso unico si è diviso tra l'originale privato e i tre formati pubblici. `file_size` è diventato obbligatorio e abbastanza grande, e lo stato di elaborazione ha i suoi tentativi e il suo errore. Ogni modifica viene da un requisito che era già nel brief e non era ancora arrivato nello schema. Dopo ogni prompt di revisione leggi il diff, non il riassunto che ne fa Claude.

### Iterazione 2: indici per le query frequenti

```text
Rileggi la sezione 4 di SPEC.md e aggiungi gli indici mancanti per
le query più frequenti di Photogallery:
- foto di un album, dalla più recente: INDEX(album_id, created_at)
- ordinamento con le preferite in testa: INDEX(is_favorite, created_at)
- dashboard della coda in Filament: INDEX(processing_status, created_at)
- ordinamento di default per data: INDEX(created_at)
- ricerca per titolo e descrizione: FULLTEXT(title, description),
  interrogato con MATCH ... AGAINST

Aggiungi anche i vincoli di integrità: UNIQUE su users.email,
UNIQUE su tags.name e tags.slug, UNIQUE composto (user_id, name)
su albums.
```

Il FULLTEXT sostituisce un `LIKE '%parola%'`, che su una colonna di testo significa leggere l'intera tabella. Il nome dell'album unico per utente, e non globale, è una decisione che la spec motiva: due utenti diversi devono poter avere entrambi un album "Viaggi".

### Iterazione 3: paginazione a cursore

La paginazione a offset (`?page=5&per_page=24`) ha un problema noto. Per arrivare alla pagina richiesta il database deve scorrere e scartare tutte le righe precedenti:

```sql
SELECT * FROM photos ORDER BY created_at DESC LIMIT 24 OFFSET 100000;
```

Questa query legge 100.024 righe per restituirne 24, e rallenta a ogni pagina. La review della spec di Photogallery lo segnala come problema già oltre le 10.000 foto. Con la paginazione a cursore il client passa un cursore opaco che codifica la posizione dell'ultimo elemento visto, e il backend lo traduce in una condizione `WHERE` su colonne indicizzate: il costo resta lo stesso in qualunque punto della collezione.

```text
Aggiorna gli endpoint di lista in SPEC.md per usare la paginazione a
cursore (cursorPaginate() di Laravel) invece di quella a offset.

- Il parametro di query diventa `cursor` (stringa opaca, opzionale)
- `per_page`: default 24, minimo 1, massimo 100
- La risposta include `links` (first, next, prev) e `meta` con
  per_page, next_cursor, prev_cursor e path
- Niente conteggio totale: con i cursori non serve

Le chiavi primarie devono essere UUID v7, ordinabili per data di
creazione. Il trait HasUuids di default genera v4: va sovrascritto.
```

Il risultato, nel paragrafo 6.0 della spec finale:

```json
{
  "data": [ /* Resource[] */ ],
  "links": {
    "first": "https://api.example.com/api/v1/photos?cursor=...",
    "next":  "https://api.example.com/api/v1/photos?cursor=...",
    "prev":  null
  },
  "meta": {
    "per_page": 24,
    "next_cursor": "eyJpZCI6IjAxOTM...",
    "prev_cursor": null,
    "path": "https://api.example.com/api/v1/photos"
  }
}
```

::: {.callout .callout-deep-dive}
[Sotto il cofano]{.callout-title}

Un UUID v4 è casuale, mentre un UUID v7 comincia con il timestamp di creazione. Con il v7 `ORDER BY id` equivale in pratica a `ORDER BY created_at`, e i cursori restano stabili anche mentre arrivano foto nuove. Photogallery ottiene il v7 con un trait, `HasUuidV7`, che sovrascrive `newUniqueId()` e restituisce `Str::uuid7()`.
:::

### Iterazione 4: un contratto REST uniforme

La forma delle risposte sembra un dettaglio finché non scrivi il frontend. Se un endpoint risponde `{ "photo": {...} }`, un altro `{ "data": {...} }` e un terzo con l'oggetto nudo, il client diventa una collezione di casi speciali. Nelle prime stesure di Photogallery login e preferiti rispondevano senza envelope. La spec finale lo dice in chiaro: ogni endpoint avvolge il payload in `{ "data": ... }`, senza eccezioni.

```text
Rivedi tutti gli endpoint di SPEC.md come un contratto REST:
1. Ogni risposta di successo è avvolta in { "data": ... }, anche login,
   registrazione e preferiti
2. Niente toggle non idempotenti: il preferito diventa
   PUT /photos/{id}/favorite (aggiunge) e DELETE /photos/{id}/favorite
   (toglie), entrambi 204 e sicuri da ripetere
3. Un solo endpoint di upload, POST /photos, per 1-20 file: il client
   non deve scegliere tra upload singolo e batch
4. Le operazioni asincrone rispondono 202 Accepted con l'header Location
5. Ogni endpoint elenca i propri codici di errore oltre a quelli
   universali (401, 429, 500)
```

Per gli errori la spec tiene il formato standard di Laravel: un campo `message` e, per il 422, un oggetto `errors` con i messaggi per campo. Lo produce l'exception handler in `bootstrap/app.php`, e un middleware forza JSON su `/api/*` perché una pagina di errore HTML non arrivi mai alla SPA. La tabella degli errori fissa i casi: 413 oltre i 10 MB, 415 per un formato diverso da JPG, PNG e WebP, 403 quando mancano l'abilità del token o la proprietà della risorsa.

### La review completa della spec

Dopo le iterazioni per area restano i problemi che nascono dall'incrocio tra le sezioni: lo schema sembra giusto, le API sembrano giuste, e messe insieme lasciano un caso scoperto. Per questi serve una review dell'intero documento:

```text
Rivedi SPEC.md rispetto ai principi SOLID, REST e KISS, più le buone
pratiche specifiche di backend (Laravel), frontend (React e TypeScript)
e database (MySQL/Postgres).

Per ogni problema scrivi un ID, la sezione della spec, il principio
violato e il fix proposto. Raggruppa per area.

Aggiungi:
- un piano di parallelizzazione: dipendenze tra le fasi del build
  workflow e cosa può girare in parallelo
- una disciplina di test e commit: cos'è un task, quale test serve
  prima del commit per ogni tipo di task, convenzioni dei messaggi

Salva il risultato in docs/SPEC-REVIEW.md. Non modificare ancora SPEC.md.
```

La review del branch, datata 26 aprile 2026, ha trovato tra le altre cose:

- la `PhotoResource` di Filament e la `PhotoResource` delle API Resource di Laravel avevano lo stesso nome: le seconde diventano `PhotoData`, `AlbumData` e `TagData`;
- `StorageManager` e `ProcessBatchUpload` comparivano nella struttura delle cartelle senza che nessuna sezione li usasse, e sono stati tolti;
- un worker della coda con `--timeout=120` rischia di interrompere il resize di un'immagine grande, quindi serve un budget esplicito di dimensioni;
- lightbox e modali non avevano il focus trap, e mancavano gli error boundary.

Le correzioni sono entrate in sette cluster, ciascuno come modifica separata di `SPEC.md`. Così la spec resta l'unica fonte di verità, e `SPEC-REVIEW.md` rimane nel repo come registro delle decisioni con le loro motivazioni. Non sei obbligato ad accettare tutto: per ogni voce decidi se si fa adesso, dopo o mai, e scrivi la decisione. Il piano di parallelizzazione della review, con le sue wave, torna nel Capitolo 20.

### Quando fermarsi

Le spec non saranno mai perfette, e inseguire la perfezione è un anti-pattern quanto saltarle. Un test pratico: sono pronte quando sai rispondere a domande come queste senza aprire il file.

- Come si chiama la colonna con il percorso dell'originale? `original_path`, sul disco privato.
- Cosa succede alle foto quando cancello un album? Restano, con `album_id` a `NULL`, e la risposta è un `204`.
- Cosa fa il frontend quando riceve un 401? Cancella il token e porta a `/login`.

Se una risposta ti costringe a cercare, quella sezione ha ancora bisogno di lavoro. Lo stesso test lo puoi far fare a Claude, ed è la parte più istruttiva. Nel branch c'è `docs/SPEC-VALIDATION.md`, un controllo di comprensione del 25 aprile ottenuto con un prompt di questo tipo:

```text
Rispondi a queste domande usando solo SPEC.md. Per ogni risposta cita
la sezione e rileggila dal file, non andare a memoria.
1. Quante tabelle ha il database, e con quali colonne?
2. Quanti endpoint API ci sono? Elencali.
3. Quali resource e widget ha il pannello Filament?
4. Quali sono i tre formati delle immagini, con larghezza e qualità?
5. Quali sono le scorciatoie da tastiera?
6. Quale driver di coda si usa in locale e quale in produzione?
7. Descrivi il flusso completo dell'upload di una foto.
8. Cosa succede quando cancello un album? E quando cancello una foto?
9. Come funziona il toggle mensile/annuale dei prezzi?
```

Claude ha contato nove tabelle (cinque applicative e quattro del framework), diciotto endpoint, tre resource e tre widget, ognuno con la sua sezione. La domanda 9 è un trabocchetto: Photogallery non ha prezzi né abbonamenti, il toggle mensile/annuale appartiene alla landing page del Capitolo 16. Claude ha risposto che nella spec non c'è e che probabilmente riguarda l'altro progetto, senza mescolarli. Se invece inventa una risposta, sta lavorando a memoria o su un contesto sbagliato, e conviene saperlo prima dell'esecuzione.

### Salvare le spec come checkpoint

Prima di passare all'implementazione committa le spec, anche se per il codice non usi ancora Git in modo formale. Sono un artefatto da condividere con i colleghi, da usare per l'onboarding e da rileggere mesi dopo come documentazione del sistema.

```bash
git init
git add CLAUDE.md SPEC.md SPEC-original.md docs/
git commit -m "docs(spec): SPEC.md rivista e validata per Photogallery v1"
```

Il formato del messaggio segue le convenzioni che la spec stessa fissa nella sezione 15: tipo, scope, oggetto. Da qui in avanti ogni modifica alle spec passa da una revisione deliberata, non da un'improvvisazione durante la scrittura del codice.

## 17.5 Anti-pattern: saltare le spec e andare dritti al codice

Hai lo stack in testa e la voglia di vedere qualcosa girare. Pensi che se chiedi subito il backend a Claude ti risparmi tutto questo lavoro, e che le spec le sistemerai dopo. Prova l'esperimento:

```text
Crea un backend Laravel completo per una photogallery.
Gli utenti si autenticano, caricano foto, le organizzano in album, le taggano.
```

Claude genera codice, probabilmente decente. Dopo venti minuti hai modelli, migration, qualche controller e il login. Sembra un grande passo avanti, finché non guardi i dettagli.

Lo schema è una stima: `id`, `filename`, `path`, `user_id`. Manca lo stato di elaborazione, perché nessuno ha detto che l'elaborazione è asincrona, e mancano i percorsi dei tre formati. La colonna del proprietario magari c'è, le policy che la fanno rispettare no. L'upload è sincrono e il resize sta nel controller: con una foto piccola funziona, con venti foto da 10 MB la richiesta va in timeout.

La paginazione è a offset, perché è il default più ovvio, e te ne accorgi quando le foto crescono. I test coprono il percorso felice degli endpoint appena scritti: senza una spec da confrontare, Claude non ha modo di sapere quali casi di errore contano.

### Il costo del rilavoro

Il codice imperfetto si corregge. Il guaio è quando è imperfetto in modo coerente: se migliaia di righe seguono la stessa architettura sbagliata, non correggi un file, correggi il pattern ovunque sia stato applicato. E gli errori si vedono a lavoro avanzato:

- Costruisci la galleria e scopri che alcuni endpoint rispondono `{ "photo": {...} }`, altri `{ "data": {...} }`, altri un array nudo. Normalizzi il client o tieni un parser per ogni endpoint.
- Arrivi al deploy su ECS con più task dietro il load balancer e scopri che le foto finiscono sul disco locale del container che ha ricevuto la richiesta. Il worker che deve elaborarle gira altrove e non le trova, e lo storage va riscritto.
- Aggiungi i preferiti per utente e scopri che `is_favorite` è una colonna della foto, cioè un preferito condiviso da tutti.

L'ultimo caso è capitato anche a Photogallery, con le spec in mano. `SPEC.md` ha `is_favorite` sulla tabella `photos`; più avanti i preferiti diventano per utente, con una tabella pivot, e in `docs/TASKS.md` c'è una fase apposta, la 6.5 ("Favorites refactor"). Qui il cambio parte dalla spec, che dice quali migration, endpoint e componenti toccare. Lo vedi nel Capitolo 21.

Senza spec, a quel punto le strade sono due. Vai avanti con l'architettura sbagliata e accumuli debito tecnico: ogni feature costa più della precedente e i bug compaiono dove non li aspetti. Oppure rifai da capo e perdi il tempo del primo tentativo più quello del refactoring, che con una scadenza davanti fa male. Entrambe si evitano con un giorno o due di lavoro sulle spec prima di toccare il codice.

### Lo Spec Driven Development come risposta

Lo Spec Driven Development, che il Capitolo 18 tratta per intero, affronta il problema in quattro fasi:

1. Spec prima: brief, schema, endpoint, componenti e autenticazione, rivisti finché sono chiari. È la fase di questo capitolo.
2. Piano dalle spec: Claude legge le spec e genera un piano diviso in task piccoli e verificabili, con criteri di accettazione presi dalle spec.
3. Codice dal piano: ogni task si implementa secondo la spec. Se salta fuori un caso non coperto si aggiorna prima la spec, poi il codice (Capitolo 19).
4. Verifica contro la spec: a ogni fase completata controlli che il codice faccia quello che la spec descrive, né di più né di meno (Capitolo 22).

Il risultato è codice che puoi passare a un altro sviluppatore, o a Claude in una sessione nuova, sapendo che le spec bastano per continuare.

### Quando le spec cambiano

Le spec cambiano, ed è normale. Un requisito si rivela ambiguo durante l'implementazione, un vincolo di prestazioni emerge dai test, il cliente cambia idea sugli album. Con le spec il cambiamento è deliberato: aggiorni il file, committi con un messaggio che spiega il perché, e le conseguenze a valle (codice, test, endpoint) le trovi in modo sistematico.

Senza spec il cambiamento resta in una conversazione. Decidi con Claude di cambiare il formato di una risposta, modifichi il codice e vai avanti. Tre settimane dopo nessuno ricorda perché quella colonna esiste, e nessuno osa toccarla. La memoria automatica di Claude Code (Capitolo 15) conserva preferenze e correzioni, ma il registro delle decisioni di design deve stare in un file versionato con Git, dove lo leggono tutti: tu, il team e la prossima sessione di Claude.

## Riepilogo

- Il primo prompt descrive il problema e chiede le alternative; lo stack si sceglie dopo, con ragioni prese dai requisiti.
- Photogallery usa Laravel 13 come API REST sotto `/api/v1`, Filament v5 per l'admin, React 19 + Vite 6 + Tailwind CSS v4 per la SPA e token Sanctum per l'autenticazione.
- Il brief si itera (primo draft, fuori scope, upload e pipeline) e la versione finale diventa il megaprompt `docs/PROMPT.md`.
- La spec si può generare tutta insieme, ma si rivede per area: database, API, autenticazione, frontend, build workflow.
- Una review contro SOLID, REST e KISS e un controllo di comprensione con una domanda trabocchetto ti dicono quando la spec è pronta.
- Saltare le spec sposta i problemi a lavoro avanzato, quando correggerli vuol dire toccare ogni file.

## Esercizio

Scegli un progetto personale piccolo: un tracker di letture, un gestore di note, un portfolio. Poi:

1. Apri Claude Code in una cartella vuota e scrivi il prompt dei requisiti, senza stack.
2. Fatti proporre due o tre stack, fai almeno due domande di follow-up e scegli con una motivazione scritta.
3. Itera il brief per almeno tre round, compreso uno sul fuori scope, partendo dal prompt riusabile della sezione 17.2 o da `docs/megaprompt-template.md`.
4. Genera la spec e rivedi almeno database e API, con un prompt di revisione ciascuno.
5. Prepara un controllo di comprensione con almeno cinque domande, una delle quali trabocchetto.
6. Committa spec, prompt e review.

L'esercizio è finito quando nel repo c'è il commit con la spec e Claude, in una sessione nuova, risponde a tutte le domande citando la sezione giusta e dice che la domanda trabocchetto non ha risposta nella spec. Tempo stimato: 60-90 minuti. Per confrontare il tuo lavoro con quello del libro, clona il branch del companion:

```bash
git clone -b book/cap-11-prompts-and-spec https://github.com/hidran/claude-code-book-photogallery.git
```
