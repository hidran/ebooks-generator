# Capitolo 3. I primi prompt utili

**Cosa imparerai**

Come scrivere un prompt che Claude Code porta a termine senza sorprese: cosa metterci dentro, quali errori costano di più su un progetto vero, tre pattern da usare ogni giorno e come rivedere il lavoro in Plan Mode prima che tocchi i file. In fondo trovi anche come regolare quanto ragiona il modello, con l'effort e `ultrathink`.

**Prerequisiti**

Claude Code installato e funzionante (capitolo 1). Il capitolo 2, sul loop agentico, spiega perché i consigli che seguono funzionano.

I comandi di Claude Code si imparano in fretta: in un pomeriggio sai usare gli slash command e le scorciatoie che servono davvero. Scrivere prompt che arrivano al risultato giusto al primo giro richiede più pratica, e la differenza tra una sessione produttiva e una frustrante sta quasi sempre lì.

Nel capitolo 2 hai visto come lavora un agent: raccoglie contesto, agisce, verifica il risultato e ripete finché il lavoro è finito o finché ha bisogno di te. Visto da qui, un buon prompt fa due cose. Dà al loop un obiettivo chiaro, così Claude sa dove sta andando, e gli dà un modo per verificare, così sa quando è arrivato. Quasi tutto il capitolo è una variazione su questi due punti.

Non troverai prompt engineering generico, né trucchi per far rispondere meglio un chatbot. Le tecniche servono quando il modello scrive codice nel tuo progetto, dentro un repo che ha le sue convenzioni e la sua storia. Claude Code legge i file e lancia comandi da solo, quindi non devi portargli il codice nella conversazione. Per lo stesso motivo un prompt vago costa più che in una chat: Claude riempie i buchi con quello che trova nel repo, e può riempirli in modo diverso da come avevi in testa.

## 3.1 Cosa rende utile un prompt per Claude Code

Tre caratteristiche di Claude Code cambiano il modo di scrivere un prompt rispetto a una chat.

### Tre differenze rispetto a una chat

La prima: legge i file da solo. Non serve incollare codice. Scrivi "leggi `src/services/userService.ts`" e Claude apre il file, con il testo esatto. In alternativa digiti `@` seguito dal percorso, con l'autocompletamento che ti aiuta a trovarlo. Incollare cento righe quando potresti indicare il file rende il prompt più lungo e più rumoroso, e basta un errore di copia per mandare Claude fuori strada.

La seconda: lancia comandi, quindi può controllare le tue ipotesi invece di prenderle per buone. "Prima di modificare il router, leggi tutti i file in `routes/` e dimmi quante route ci sono e come validano i parametri." Claude elenca la cartella, apre i file e risponde con quello che ha trovato. Il prompt diventa un'indagine preliminare, e la modifica vera parte da dati reali.

La terza: prima di agire Claude si costruisce un piano, anche quando non te lo mostra. Quel piano è buono quanto le informazioni che gli dai. Un prompt con obiettivo, vincoli ed esempi produce un piano che puoi rivedere prima che venga scritta una riga di codice; nella sezione 3.5 vedi come renderlo esplicito con Plan Mode.

### Il contesto che Claude ha già

All'avvio Claude Code carica il `CLAUDE.md` del progetto, il file di istruzioni che vedrai nel capitolo 7. Se lì hai scritto lo stack, i comandi di build e di test e le convenzioni del team, non devi ripeterli in ogni prompt. Il resto Claude non lo conosce in anticipo: non esplora il repo prima che tu scriva, lo legge quando gli serve. Il prompt quindi si concentra su quello che è specifico di questa richiesta e indica dove guardare quando il punto di partenza non è ovvio.

### Prompt vago e prompt utile, tre esempi

Il primo caso è un refactoring. Il prompt vago:

```text
Rendi questo migliore.
```

Quello utile:

```text
Leggi src/utils/csvParser.ts. La funzione parseCsv mescola lettura del
file, parsing e validazione in un unico blocco da 80 righe. Separala in
tre funzioni (readFile, parseRaw, validateRows), con parsing e
validazione come funzioni pure, senza cambiare il comportamento esterno:
la firma pubblica deve restare identica e i test esistenti devono
continuare a passare.
```

Con il primo Claude farà qualcosa, ma non sai cosa: può rinominare variabili, aggiungere commenti o riscrivere la logica. Con il secondo sa cosa fare e dove fermarsi, e ha già la verifica a disposizione: i test esistenti.

Il secondo caso è un bug. Il prompt vago è "Sistema questo bug." Quello utile:

```text
Il test "rifiuta il login con password errata" in tests/auth.test.ts
fallisce con TypeError: Cannot read properties of null (reading 'id').
Leggi il test e la funzione loginUser in src/auth/service.ts. Trova la
causa e proponimi un fix, ma non applicarlo finché non ho approvato.
```

Il primo non dice quale bug, dove e in quale condizione si presenta. Il secondo dà le coordinate: il test, il messaggio d'errore, i due file da leggere. E chiede di fermarsi prima di toccare il codice. Tieni presente che con auto mode attivo quella richiesta è un'istruzione che Claude segue, non un blocco: se vuoi la garanzia usa Plan Mode (sezione 3.5).

Il terzo caso è una feature nuova. Il prompt vago è "Aggiungi la paginazione." Quello utile:

```text
Aggiungi la paginazione lato server agli endpoint GET /api/users e
GET /api/products. Parametri: limit (default 20, massimo 100) e offset
(default 0). La risposta deve avere la forma
{ data: [], total: number, limit: number, offset: number }.
Guarda come sono scritti i controller in src/controllers/ e segui le
stesse convenzioni. Aggiorna anche le pagine React
src/pages/UsersPage.tsx e src/pages/ProductsPage.tsx. Scrivi i test
per i nuovi comportamenti.
```

Il secondo prompt è più lungo, ma quello che conta è la precisione: parametri, formato della risposta, dove trovare le convenzioni, quali file aggiornare, cosa testare. Claude non deve inventare nessuna di queste scelte, perché le hai già fatte tu.

<!-- TODO screenshot: la vecchia fig-01 (Claude Code appena avviato con `! ls -al`) è stata rimossa perché banner e barra di stato mostrano Sonnet 4.6. Se serve un'immagine qui: sessione appena avviata con Opus 5.5 nel banner e un prompt che usa `@` per indicare un file. -->

## 3.2 L'anatomia di un prompt che funziona

Dagli esempi si ricava uno schema. I prompt che funzionano con Claude Code contengono quasi sempre cinque elementi. Non servono tutti ogni volta, ma ognuno che aggiungi toglie un'ipotesi che Claude altrimenti farebbe da solo.

Il contesto è la situazione attuale: cosa esiste, dove si trova, perché c'è. Non devi spiegare il progetto, basta orientare Claude sulla parte che ti interessa. "La funzione `calculateDiscount` in `src/pricing/engine.ts` applica gli sconti agli ordini B2B" è sufficiente; il resto Claude lo legge dal file.

L'obiettivo è cosa deve cambiare dopo l'intervento, detto in modo che si possa controllare. Non "miglioralo" ma "separala in tre funzioni". Non "sistemalo" ma "il test `test_discount_negative` deve passare". È questa parte che permette a Claude, e poi a te, di capire se il lavoro è finito.

I vincoli dicono cosa non deve cambiare. È l'elemento che si dimentica più spesso, e la sua assenza sta dietro a buona parte degli errori della prossima sezione: "non toccare l'API pubblica", "resta compatibile con Node 18", "niente dipendenze nuove", "segui il pattern già usato in `userService.ts`".

Gli esempi sono file già scritti come vuoi tu. "Guarda come è strutturato `src/services/userService.ts` e segui lo stesso pattern" vale più di un paragrafo di spiegazioni: Claude legge il file e ne ricava le convenzioni che nessuno ha mai messo per iscritto, dai nomi delle funzioni alla gestione degli errori.

L'output desiderato è la forma del risultato: "mostrami solo il diff", "crea il file completo", "prima un piano numerato, senza eseguire niente", "elenca i file che toccheresti". Così Claude sa se deve agire subito o aspettarti, e tu sai cosa ti arriva.

::: {.callout .callout-prompt}
[Prompt riusabile]{.callout-title}

Template per aggiungere una feature:

```text
Contesto: [cosa esiste, quale file, quale funzione, perché esiste]

Obiettivo: [cosa deve cambiare o essere creato, in modo misurabile]

Vincoli:
- Non modificare [file/API/comportamento]
- Segui il pattern già usato in [file di riferimento]
- [Altre limitazioni: versione Node, dipendenze, compatibilità]

Esempi: leggi [file esistente] per il pattern da seguire

Output: [prima mostrami il piano / crea il file / mostrami solo il diff]
```
:::

Il template è un punto di partenza. Per un task piccolo bastano due righe; per uno grosso, ogni elemento che manca dovrebbe mancare per una ragione precisa.

### Quanto deve essere lungo un prompt

Quanto serve a togliere l'ambiguità, e non di più. Tre righe precise valgono più di venti righe piene di ripetizioni e di qualche contraddizione. Un test pratico: rileggi il prompt e chiediti se, senza sapere niente del progetto, avresti tutto quello che ti serve per fare il task. Se la risposta è sì, è abbastanza lungo.

## 3.3 Cinque errori di prompting da evitare

Sono gli errori che si pagano su un progetto vero, con una storia, delle dipendenze e parti che non si possono toccare. In una cartella di prova vuota non li noti nemmeno. Ognuno ha una correzione semplice.

### Errore 1: chiedere senza dare il contesto

Scrivi "aggiungi il logging alle funzioni principali" e basta. Claude non sa quale libreria di logging usi, quindi ne sceglie una. Non sa quali funzioni consideri principali, e sceglie anche quelle. Il codice che ottieni funziona ma non c'entra con il tuo progetto: usa winston dove tu usi pino, scrive JSON dove il team legge testo semplice, tocca le funzioni sbagliate.

La correzione è indicare il contesto che esiste già: "Leggi `src/logger.ts` per vedere libreria e formato che usiamo, e `src/api/` per le funzioni che mi interessano." Se è un'informazione che ti serve spesso, scrivila una volta nel `CLAUDE.md` (capitolo 7) e smetti di ripeterla.

### Errore 2: un solo prompt per cinque task

Metti tutto in una richiesta: "Refactora la classe User, aggiungi i test unitari, aggiorna la documentazione, correggi il bug nella validazione dell'email e prepara un commit con un messaggio convenzionale." Claude parte, ma è facile che una delle cinque cose resti indietro, o che due obiettivi si pestino i piedi. Il refactoring, per esempio, rompe i test che puntano all'implementazione attuale, e Claude deve decidere da solo chi dei due ha ragione.

Spezza in prompt successivi. Prima il refactoring, e lo controlli. Poi i test, e li controlli. Poi il bug, infine il commit. Ogni prompt ha un solo obiettivo e un risultato che verifichi prima di passare al successivo. Scrivere quattro prompt invece di uno costa qualche minuto; rimettere a posto un errore che si è propagato su tre modifiche ne costa molti di più.

### Errore 3: non dire cosa non toccare

Chiedi di "sistemare il controller degli ordini". Claude legge il file, vede funzioni scritte con stili diversi e decide di uniformarle. Nel farlo cambia anche parti che funzionavano, che i colleghi conoscono a memoria e da cui un'integrazione esterna si aspetta un formato preciso.

Aggiungi sempre i vincoli: "non cambiare la firma pubblica delle funzioni", "non toccare `src/legacy/`", "il formato della risposta resta com'è, ci sono client in produzione che lo leggono". Sono due righe, e separano un refactoring controllato da un cambiamento che scopri quando un client smette di funzionare.

### Errore 4: saltare il piano sui task complessi

Devi aggiungere il login OAuth a un'app che non ce l'ha. Scrivi il prompt e lasci lavorare Claude, che crea file, ne modifica altri e aggiunge dipendenze. A metà salta fuori un conflitto tra il nuovo sistema di sessione e il middleware esistente, e a quel punto i file modificati sono già dieci.

Per lavori così parti da Plan Mode. Claude esplora il codice e scrive un piano senza modificare niente: vedi i passi, i file coinvolti, i conflitti possibili. Fai domande, chiedi modifiche e approvi solo quando il piano ti convince. La sezione 3.5 spiega come.

### Errore 5: non leggere il diff

Claude ha finito, tu dai un'occhiata veloce, sembra a posto e vai avanti. Tre ore dopo, durante i test di integrazione, scopri che ha modificato anche una funzione di utilità condivisa per adattarla al nuovo caso, cambiando un comportamento voluto che nessuno aveva documentato.

In auto mode, la modalità di partenza delle sessioni interattive (capitolo 2), Claude non ti chiede conferma per ogni modifica ai file: quando ti scrive che ha finito, le modifiche sono già su disco e il diff lo leggi dopo, con `git diff`, prima del commit. In modalità Manual invece ogni modifica ti arriva come diff da approvare. In tutti e due i casi la revisione è quella che faresti sulla pull request di un collega: prima i file nuovi, che sono meno rischiosi, poi le modifiche ai file esistenti, con un occhio in più per le funzioni e le interfacce usate da altri moduli. Se qualcosa non va, `/rewind` (oppure `Esc` due volte con il prompt vuoto) riporta il codice a un checkpoint precedente.

::: {.callout .callout-warning}
[Attenzione]{.callout-title}

La volta in cui salti il diff perché ti fidi è quasi sempre quella in cui Claude ha toccato un file che non ti aspettavi. Leggere il diff fa parte della normale revisione del codice, come per quello scritto da chiunque altro. I file nuovi si guardano in fretta; le modifiche a codice che è già in produzione meritano tutta l'attenzione.
:::

## 3.4 Pattern ricorrenti: piano, esempi, verifica

Oltre allo schema e agli errori ci sono tre abitudini che valgono per quasi ogni task, qualunque sia il tipo. Completano i cinque elementi della sezione 3.2.

### Chiedi il piano prima del codice

Per qualsiasi task che va oltre qualche riga, il primo prompt chiede un piano, non codice:

```text
Pianifica come faresti [obiettivo]. Non scrivere codice. Solo passi
numerati con: file da creare o modificare, motivo di ogni modifica,
dipendenze tra i passi, possibili punti critici.
```

Ne ricavi due cose. Puoi correggere il piano prima che Claude tocchi i file, e sistemare dieci righe di piano costa molto meno che rimettere a posto cinquanta righe di codice. E il piano resta come documento: lo mostri a un collega, lo incolli in un ticket, ci scrivi sopra il messaggio di commit.

Letto il piano, rispondi in uno di tre modi. "Va bene, procedi", e Claude esegue. "Cambia il passo 3 così: ...", e Claude aggiorna il piano e aspetta. "Il passo 2 non può toccare quel file, proponi un'alternativa", e Claude cerca un'altra strada. Plan Mode (sezione 3.5) fa la stessa cosa con una garanzia in più: finché non approvi, i file non cambiano.

### Mostra un esempio

Le istruzioni sullo stile scritte a parole restano vaghe. "Usa la dependency injection" si può fare in parecchi modi, e "segui le convenzioni del progetto" non dice niente se Claude non sa quali sono. Funziona meglio un esempio:

```text
Leggi src/services/userService.ts. Crea src/services/productService.ts
con lo stesso pattern: dependency injection nel costruttore, metodi
pubblici che validano l'input con Zod prima di chiamare il database,
errori gestiti con le classi custom in src/errors/.
```

Claude legge `userService.ts`, ne ricava la struttura della classe, i nomi, il modo in cui tratta tipi ed errori, e applica tutto al nuovo file. Ottieni un file che assomiglia al resto del progetto, invece di uno corretto ma scritto con un approccio diverso da tutti gli altri. Il pattern vale per test, componenti React, controller REST, query SQL, configurazioni Terraform: quando vuoi qualcosa di nuovo nello stile di qualcosa che esiste, indica il file che quello stile lo mostra meglio.

### Definisci come si verifica

Un prompt che dice cosa fare va bene. Uno che dice anche come controllare che sia fatto bene chiude il loop agentico, perché Claude ha un criterio per sapere se ha finito.

Senza criterio: "Scrivi una funzione che legge il CSV." Con criterio:

```text
Scrivi una funzione parseCsv(path: string): Promise<Row[]> con
Row = { date: Date, amount: number, currency: string }. Scrivi anche i
test per questi casi: file vuoto, file con solo l'header, righe con campi
mancanti, righe con date in formato errato, righe valide. I test devono
passare con pnpm test.
```

Nella seconda versione il criterio è misurabile: `pnpm test` passa oppure no. Claude lancia i test, vede cosa fallisce e ci torna sopra finché diventano verdi, che è esattamente il passo di verifica del loop. Anche tu controlli senza leggere ogni riga, perché ti basta lanciare i test. I criteri che funzionano meglio sono di questo tipo:

- test precisi che devono passare;
- comandi che devono dare un certo risultato, come `pnpm build` senza errori o un `curl` sull'endpoint che risponde 200;
- soglie misurabili, come nessun warning di TypeScript o una copertura dei test di almeno l'80%.

Nel capitolo 20 trovi `/goal`, che porta questa idea fino in fondo: Claude continua a lavorare, turno dopo turno, finché un valutatore separato non giudica soddisfatta una condizione come "`npm test` esce con codice 0".

I tre pattern si combinano bene nello stesso prompt. Per un refactoring li puoi mettere insieme così:

::: {.callout .callout-prompt}
[Prompt riusabile]{.callout-title}

Refactoring guidato:

```text
Contesto: leggi [percorso file]. La funzione/classe [nome] fa [descrizione
di cosa fa e perché esiste attualmente].

Obiettivo: [cosa deve cambiare, in modo misurabile. Es: separare le
responsabilità in X funzioni pure / rendere la classe testabile con mock /
eliminare la dipendenza da [libreria]]

Vincoli:
- La firma pubblica di [funzione/interfaccia] deve restare identica
- Non toccare [file o cartella correlata]
- I test in [percorso test] devono continuare a passare senza modifiche

Esempio di pattern target: guarda [file che ha già lo stile che vuoi]

Output: prima mostrami un piano numerato con i passi e i file impattati.
Non eseguire finché non approvo.
```
:::

Sostituisci le parti tra parentesi quadre con il tuo caso. Il template va bene per qualsiasi refactoring, dalla separazione di due responsabilità alla riscrittura di un modulo intero.

## 3.5 Plan Mode: il prompt più importante di tutti

Plan Mode merita una sezione a sé. Si attiva in un secondo, e sui task complessi incide sul risultato più di qualsiasi altro accorgimento di questo capitolo.

### Cos'è Plan Mode

Plan Mode è una delle modalità di permesso di Claude Code, che trovi tutte nel capitolo 11. In questa modalità Claude legge i file e lancia comandi per esplorare il progetto, ma non modifica il codice finché non approvi. Alla fine ti presenta un piano. La parte di ricerca la affida al subagent Plan integrato, che lavora in sola lettura con un contesto tutto suo.

La differenza rispetto a scrivere "non scrivere codice" nel prompt sta in chi fa rispettare la regola. La frase nel prompt è un'istruzione che il modello segue quasi sempre. Plan Mode è un limite che applica il harness, il programma intorno al modello: le modifiche ai file non partono finché non dici di sì.

Anche l'esplorazione dipende dalla modalità di partenza. Se auto mode è disponibile, i comandi lanciati durante la pianificazione li valuta il classificatore, e non ti arriva una richiesta di conferma per ogni `ls` o `grep`. Altrimenti i comandi che non sono di sola lettura ti chiedono il permesso.

### Come si entra

Hai quattro strade:

- `Shift+Tab` cambia modalità a giro (su alcune configurazioni Windows il tasto è `Alt+M`). Partendo da auto mode, la prima pressione porta a Manual, la seconda ad Accept edits, la terza a Plan. La barra di stato mostra `⏸ plan mode on`.
- `/plan` dal prompt entra in Plan Mode. Se aggiungi una descrizione, per esempio `/plan aggiungi la paginazione agli endpoint degli utenti`, Claude comincia subito a pianificare.
- `claude --permission-mode plan` avvia la sessione già in Plan Mode.
- Nel `settings.json`, `"permissions": {"defaultMode": "plan"}` lo rende la modalità di partenza. In VS Code l'impostazione equivalente è `claudeCode.initialPermissionMode: "plan"`.

La frase "Pianifica... non scrivere codice" del pattern precedente resta utile per i task piccoli, quando cambiare modalità ti sembra eccessivo. Per i task che contano usa Plan Mode.

### Quando usarlo

Quasi sempre, tranne per le correzioni piccole e ovvie. Se aggiungi un parametro a una funzione che conosci bene, puoi farne a meno. Usalo invece quando:

- aggiungi una feature che tocca più di tre file;
- modifichi un'interfaccia pubblica usata in più punti;
- introduci una dipendenza nuova;
- cambi il flusso di autenticazione o di autorizzazione;
- lavori su codice che non conosci.

In questi casi il piano ti evita di annullare modifiche su dieci file perché a metà è emerso un conflitto che avresti visto subito.

### Cosa ti restituisce

Un piano utile contiene:

1. i passi numerati, nell'ordine in cui verranno eseguiti;
2. per ogni passo, i file da creare o modificare e il motivo;
3. le dipendenze tra i passi (il passo 3 usa quello che produce il passo 1);
4. i punti critici e le domande aperte, per esempio "non trovo la configurazione del database, dove si trova?".

Se manca una di queste parti, chiedila prima di approvare.

### Approvare, correggere, ripartire

Quando il piano è pronto, Claude Code ti chiede come procedere. Le opzioni sono tre, con il testo in inglese dell'interfaccia:

- `Yes, and use auto mode`: approvi ed esci da Plan Mode in auto mode. Se auto mode non è disponibile, al suo posto trovi `Yes, auto-accept edits`.
- `Yes, manually approve edits`: approvi, ma ogni modifica ai file ti arriva da confermare.
- `No, keep planning`: resti in Plan Mode e scrivi cosa cambiare, per esempio "Il passo 2 non può modificare `authMiddleware.ts`, lo usano altri team. Proponi un approccio che non lo tocchi." Claude rifà il piano.

Con `Ctrl+G` apri il piano nel tuo editor e lo correggi a mano prima di approvarlo. Conviene quando le correzioni sono tante o riguardano dettagli che faresti prima a scrivere che a spiegare.

<!-- TODO screenshot: piano completato in Plan Mode con il menu di approvazione (Yes, and use auto mode / Yes, manually approve edits / No, keep planning), Opus 5.5 nella barra di stato. -->

La prima opzione va capita bene. Con auto mode come modalità predefinita, approvare con `Yes, and use auto mode` vuol dire che Claude esegue tutto il piano senza chiederti conferma per ogni modifica. Il classificatore continua a bloccare le azioni rischiose, come un force push, una cancellazione irreversibile o un deploy in produzione, ma le modifiche ai file passano. Il piano diventa quindi il tuo punto di revisione: leggilo come leggeresti una PR, perché dopo l'approvazione la prossima occasione per guardare il lavoro è il diff finale. Se preferisci vedere ogni modifica mentre succede, scegli `Yes, manually approve edits`.

A volte il piano ti dice che era sbagliata la richiesta. Se per ottenere il risultato servono trenta file, scegli di continuare a pianificare e riformula: "Così tocchi trenta file. Trova un approccio che ottenga lo stesso risultato modificandone meno di cinque." Finché lavori sul piano, ogni correzione costa un messaggio.

### Un esempio completo

Con Plan Mode attivo:

```text
Pianifica come aggiungere un endpoint POST /api/orders al backend NestJS.

Specifiche:
- validare il body con un DTO e class-validator (orderId, items[], total)
- salvare su Postgres con Prisma (tabella orders, relazione con users)
- rispondere 201 con l'ordine creato
- gestire gli errori: 400 per un body non valido, 404 se l'utente non
  esiste, 500 per errori del database

Non scrivere codice. Solo passi numerati con:
- file da creare (nome e tipo)
- file da modificare (nome e cosa cambia)
- test da scrivere (cosa devono coprire)
- dipendenze da installare, se servono
```

In Plan Mode la riga "Non scrivere codice" è ridondante, ma la lascio perché così il prompt funziona anche se lo incolli in una sessione in un'altra modalità. Il piano che ottieni si legge in un paio di minuti, e quando approvi sai cosa sta per succedere nel progetto. Nel capitolo 4 userai lo stesso flusso su un caso reale, l'analisi di un CSV.

### Quanto ragiona Claude: effort e ultrathink

Quanto ragionamento il modello mette in un compito lo decide l'effort. I livelli sono `low`, `medium`, `high`, `xhigh` e `max`. Su Opus 5.5, il modello predefinito, l'effort di partenza è `medium`. Lo cambi con `/effort`, che apre un selettore, oppure con le frecce sinistra e destra dentro `/model`. Il livello attivo si vede nel logo e nello spinner; `max` vale solo per la sessione corrente.

`medium` va bene per le domande veloci e le modifiche piccole. Per un lavoro di progettazione, un bug difficile o la stesura di una specifica, alza a `high` prima di chiedere il piano: consumi più token, ma il piano è più ragionato. Sui modelli 5.5 il ragionamento non si può spegnere; il modello stabilisce da solo quanto pensare entro il livello che hai scelto. Se vuoi contenere i costi, l'alias `opusplan` usa Opus mentre pianifichi e Sonnet quando esegui (`/model opusplan`).

Se ti serve più ragionamento per un solo prompt, scrivi `ultrathink` in qualsiasi punto del messaggio. Claude Code aggiunge un'istruzione a quel turno e il modello ragiona più a fondo, mentre l'effort della sessione resta quello che era. Altre formule come "think hard" o "pensaci bene" non sono parole chiave: il modello le legge come normale testo del prompt.

```text
ultrathink. Il test di integrazione degli ordini fallisce una volta su
cinque, solo in CI. Leggi tests/orders.e2e-spec.ts e src/orders/ e
proponimi le tre cause più probabili, in ordine, con il modo per
verificare ciascuna.
```

## Riepilogo

- Un prompt utile dà al loop agentico un obiettivo controllabile e un modo per verificarlo; contesto, vincoli, esempi e formato dell'output tolgono il resto delle ipotesi.
- Indica i file invece di incollarli, e scrivi nel `CLAUDE.md` quello che altrimenti ripeteresti a ogni sessione.
- Un task per prompt, con i vincoli espliciti su cosa non toccare.
- Per i task complessi entra in Plan Mode (`Shift+Tab`, `/plan` o `claude --permission-mode plan`) e rivedi il piano prima di approvare: con `Yes, and use auto mode` è l'ultimo controllo prima del diff finale, che leggi comunque prima del commit.
- Alza l'effort a `high` per progettazione e bug difficili; `ultrathink` vale per un solo prompt, "think hard" non fa niente di speciale.

## Esercizio

Lavora sulla mini codebase del branch `cap-02-prompts-exercise` nel repository companion `claude-code-book-snippets`. Il nome del branch usa la numerazione della prima edizione, come spiegato nelle pagine iniziali del libro.

<!-- VERIFY: al 17 ottobre 2026 il repo hidran/claude-code-book-snippets ha solo il branch main; cap-02-prompts-exercise va creato (parser CSV, controller REST, file di test a metà, script npm test) prima della pubblicazione. -->

```bash
git clone https://github.com/hidran/claude-code-book-snippets.git
cd claude-code-book-snippets
git checkout cap-02-prompts-exercise
claude
```

Dentro trovi tre file: un parser CSV, un controller REST e un file di test scritto a metà. L'esercizio richiede circa 15 minuti.

1. Chiedi di migliorare il parser con un prompt vago ("rendilo migliore") e guarda cosa fa Claude, poi leggi il risultato con `git diff`. Annulla con `/rewind`, scrivi la versione con i cinque elementi della sezione 3.2 e confronta i due diff.
2. Entra in Plan Mode e chiedi il piano per un endpoint di ricerca nel controller. Scegli `No, keep planning` e chiedi una modifica, per esempio "il passo 3 deve usare i query parameter, non il body". Approva la versione rivista.
3. Chiedi di completare i test scritti a metà, con la condizione esplicita che passino con `npm test`.

Hai finito quando `npm test` esce con codice 0, il piano dell'endpoint è stato corretto almeno una volta prima dell'approvazione e hai salvato i due prompt del primo passo, vago e preciso, per confrontarli quando rileggerai questo capitolo.
