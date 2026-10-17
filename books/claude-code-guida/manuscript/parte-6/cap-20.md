# Capitolo 20. Wave in parallelo con worktree, /goal e agent view

::: {.chapter-goals}
[Cosa imparerai]{.callout-title}

Come eseguire in parallelo le track indipendenti di una wave della Photogallery, ognuna nel suo git worktree e con una condizione di completamento che Claude deve dimostrare di aver raggiunto. Poi come seguire più sessioni in background da una sola schermata, come dare un worktree anche ai subagent e come rimettere insieme il lavoro senza lasciare in giro copie e branch.

[Prerequisiti]{.callout-title}

Il repo della Photogallery allo stato di fine capitolo 19 (branch `book/cap-13-wave-2-api` del companion repo) e la GitHub CLI (`gh`) configurata come nel capitolo 19.

:::

Alla fine del capitolo 19 la Photogallery ha la Fase 1 (modelli, migrazioni, seeder) e la Fase 2 (API) mergiate in `main`. In `docs/TASKS.md` restano aperte la Fase 3 (admin Filament, da T046 a T054), la Fase 4 (setup del frontend React, da T055 a T062), la Fase 5 (componenti React, da T063 a T071) e la Fase 6 (pipeline delle immagini, da T072 a T080), più tre task della Fase 2 rinviati alla 6: T029, T032 e T035. Sono 38 task.

Il `CLAUDE.md` del progetto dice già come eseguirli. La sezione "Parallelization rules" raggruppa queste fasi nella Wave 1, divisa in tre track: Track A (Fase 2, poi Fase 6), Track B (Fase 3), Track C (Fase 4, poi Fase 5). E aggiunge: "each in its own git worktree", ogni track nel suo worktree. Nel capitolo 19 abbiamo chiesto a Claude di usare i subagent dove i task erano indipendenti, e per due scaffolding andava bene. Con decine di task su backend e frontend, tutti nella stessa cartella, prima o poi due agenti toccano lo stesso file. Qui diamo a ogni track il suo worktree, come chiede il file.

Una nota sui nomi. I branch del companion repo chiamano "wave 1" e "wave 2" le prime due fasi eseguite nel capitolo 19. In `docs/TASKS.md` la Fase 1 appartiene alla Wave 0 e l'API è la Track A della Wave 1. Da qui in avanti uso i nomi del file, perché sono quelli che leggerà Claude.

## 20.1 Tre modi di lavorare in parallelo

Claude Code offre tre strumenti per fare più cose insieme, e ognuno isola una cosa diversa.

| Strumento | Cosa isola | Quando usarlo |
| --- | --- | --- |
| Subagent | Il contesto, dentro una sessione | Ricerche e sottotask brevi, come nei capitoli 10 e 19 |
| Worktree (`claude --worktree`) | I file: ogni sessione ha la sua copia e il suo branch | Task che modificano file diversi nello stesso momento |
| Sessione in background (`claude --bg`, `claude agents`) | Il terminale: la sessione gira senza di te | Più task lunghi da seguire da una sola schermata |

Un subagent ha una context window tutta sua, ma legge e scrive nella stessa cartella della sessione che l'ha lanciato. Se due subagent modificano `routes/api.php` nello stesso momento, uno dei due sovrascrive l'altro, oppure i test di uno falliscono per colpa delle modifiche a metà dell'altro. Un worktree risolve il problema dei file. Una sessione in background risolve un altro problema, quello di dover tenere aperti cinque terminali per cinque lavori. I tre strumenti si combinano: una sessione in background lavora in un worktree, e un subagent può avere il suo worktree temporaneo.

## 20.2 Scegliere le track e preparare il repo

### Le dipendenze nascoste

Il `CLAUDE.md` dice che le tre track "share zero files", non condividono file. Prima di lanciarle insieme, però, leggi i task e non solo i titoli delle fasi. T048 chiede un'azione Filament di riprocessamento che chiama `ProcessPhoto::dispatch($record)`: il job `ProcessPhoto` nasce con T077, nella Fase 6. Il campo `Depends on` di T048 cita solo T047, quindi il problema si vede soltanto nei criteri di accettazione. Se lanci la Track B insieme alla Fase 6, la sessione dell'admin trova una classe che non esiste e o si ferma o se la inventa.

Per questo il primo giro mette insieme due track che davvero non si toccano:

- Track A, continuazione: la Fase 6 (T072-T080) più T029, T032 e T035, tutto nel backend;
- Track C: la Fase 4 (T055-T062), solo nel frontend.

Il secondo giro, quando la pipeline è in `main`, lancia la Fase 3 e la Fase 5.

C'è un file che tutte le sessioni toccano: `docs/TASKS.md`, perché la regola 2 del `CLAUDE.md` vuole la casella spuntata nello stesso commit del task. Le sessioni però modificano righe di sezioni diverse, quindi Git di solito le unisce senza conflitti. Gli altri file "calamita" elencati nel `CLAUDE.md` (`composer.json`, `package.json`, `bootstrap/app.php`, `App.tsx`, `main.tsx`) restano a una sessione alla volta. Sul branch del capitolo 19 `composer.json` contiene già `filament/filament` e `intervention/image-laravel`, quindi sulla carta nessuna track del primo giro deve toccarlo.

### .gitignore, .worktreeinclude e baseRef

Tre preparativi, da committare su `main` prima di aprire le sessioni.

Il primo: Claude Code crea i worktree in `.claude/worktrees/` dentro il repo, e quella cartella non deve finire in Git. La Photogallery non ha un `.gitignore` nella radice (ci sono solo quelli di `backend/` e `frontend/`), quindi lo crei:

```text
.claude/worktrees/
```

Il secondo riguarda i file ignorati. Un worktree è un checkout pulito: tutto quello che Git ignora non c'è. Per i test del backend serve `backend/.env`, che contiene `APP_KEY` (il `phpunit.xml` imposta SQLite in memoria ma non la chiave). Il file `.worktreeinclude` nella radice elenca i file ignorati che Claude Code copia in ogni nuovo worktree:

```text
backend/.env
```

Il frontend non ha un `.env`: `src/api/client.ts` usa `/api/v1` quando `VITE_API_BASE_URL` non è impostata. Se tu ne hai uno, aggiungi `frontend/.env.local` alla lista. `vendor/` e `node_modules/` non vanno nell'elenco: si reinstallano, ed è più veloce che copiarli.

Il terzo è il punto di partenza. Per default un worktree parte dal `main` remoto. Se hai mergiato qualcosa in locale e non l'hai ancora pushato, le nuove sessioni non lo vedono. Per partire dal tuo `HEAD` locale aggiungi la chiave `worktree` a `.claude/settings.json`, accanto agli hook che il file contiene già:

```json
{
  "worktree": {
    "baseRef": "head"
  }
}
```

Nel primo giro non cambia niente, perché `main` coincide con il remoto. Servirà nel secondo, se deciderai di mergiare in locale (paragrafo 20.5).

```bash
git add .gitignore .worktreeinclude .claude/settings.json
git commit -m "chore: worktree setup for parallel tracks"
git push
```

## 20.3 Due sessioni, due worktree

Un worktree è una seconda cartella di lavoro dello stesso repository, con i suoi file e il suo branch ma la stessa storia Git. Con `--worktree` e un nome, Claude Code crea il worktree in `.claude/worktrees/<nome>` su un branch nuovo `worktree-<nome>` e avvia la sessione lì dentro.

Apri due terminali nella radice del repo. Nel primo:

```bash
claude --worktree fase6-pipeline
```

Nel secondo:

```bash
claude --worktree fase4-frontend
```

Da uno dei due controlla cosa è successo, con il prefisso `!` che esegue un comando di shell dalla sessione:

```text
!git worktree list
```

```text
~/projects/photogallery                                  5d1f2a9 [main]
~/projects/photogallery/.claude/worktrees/fase6-pipeline 5d1f2a9 [worktree-fase6-pipeline]
~/projects/photogallery/.claude/worktrees/fase4-frontend 5d1f2a9 [worktree-fase4-frontend]
```

Tre cartelle, tre branch, un solo repository. `backend/.env` è già al suo posto in entrambi i worktree, mentre le dipendenze mancano. Nella prima sessione:

```text
installa le dipendenze del backend con composer install
```

Nella seconda:

```text
installa le dipendenze del frontend con npm ci
```

In un progetto vero questo è il primo passo in ogni worktree, e su un Laravel con Filament richiede qualche minuto.

Le copie condividono la storia Git e la memoria automatica, che Claude Code tiene in `~/.claude/projects/<progetto>/memory/` per tutto il repository. Il `CLAUDE.md` invece è un file versionato: ogni worktree ha il suo, identico a quello di `main` al momento della creazione. Se lo modifichi in `main` mentre le sessioni lavorano, loro non vedono la modifica finché non la mergi nei loro branch.

<!-- TODO screenshot: due terminali affiancati con claude --worktree fase6-pipeline e fase4-frontend, e l'output di git worktree list -->

::: {.callout .callout-warning}
[Attenzione]{.callout-title}

Se lanci Laravel Sail in due worktree contemporaneamente, i container si contendono le stesse porte (80, 3306, 6379) e, siccome in entrambe le copie la cartella si chiama `backend`, anche lo stesso nome di progetto Docker Compose. Per questo capitolo Sail non serve: i test girano su SQLite in memoria con `composer test`. Se ti serve l'applicazione in esecuzione, tienila accesa in un solo worktree alla volta, oppure cambia `APP_PORT` e `FORWARD_DB_PORT` nel `.env` di uno dei due.
:::

## 20.4 Un obiettivo verificabile con /goal

Di norma ogni sessione lavora un turno e poi si ferma ad aspettarti. Con undici task davanti vuol dire tornare al terminale ogni pochi minuti a scrivere "continua". `/goal` imposta una condizione di completamento: Claude continua a lavorare, turno dopo turno, finché la condizione non è soddisfatta. A giudicarla è un valutatore separato, che la controlla alla fine di ogni turno e, se manca qualcosa, rimanda Claude al lavoro.

### Scrivere la condizione

Il valutatore non esegue comandi e non apre file. Giudica quello che Claude ha mostrato nella conversazione. Per questo la condizione deve nominare un controllo che Claude esegue e il cui risultato finisce sullo schermo. Prendi una condizione come questa:

```text
/goal la pipeline delle immagini funziona
```

Il valutatore non ha modo di saperlo. Vedrà Claude scrivere che la pipeline funziona e gli darà ragione, o non gliela darà mai. Lo stesso principio vale per i criteri di accettazione del capitolo 18: "testabile, non aspirazionale", come dice l'intestazione di `docs/TASKS.md`.

Nella sessione `fase6-pipeline`:

```text
/goal i task T029, T032, T035 e da T072 a T079 hanno Status [x] in docs/TASKS.md (mostrami le righe Status con grep), "composer test" nella cartella backend esce con codice 0 e ogni task ha il suo commit sul branch del worktree (mostrami git log --oneline)
```

Nella sessione `fase4-frontend`:

```text
/goal i task da T055 a T061 hanno Status [x] in docs/TASKS.md (mostrami le righe Status con grep), "npm run build" e "npm run lint" nella cartella frontend escono con codice 0 e ogni task ha il suo commit sul branch del worktree (mostrami git log --oneline)
```

Le scelte dietro queste due righe:

- `composer test` è lo script del `composer.json` del backend: pulisce la cache della configurazione e lancia `php artisan test`, cioè Pest;
- nel frontend, su questo branch, `package.json` non ha ancora uno script `test` (Vitest è installato, ma i primi test arrivano con la Fase 5), quindi il controllo sono build e lint, gli stessi che chiede T062;
- T080 e T062 restano fuori. Sono i task di review della fase: T080 vuole un upload reale con il queue worker acceso, T062 un `curl` verso il proxy di Vite con Laravel in esecuzione. Li fai tu, come nel capitolo 19;
- il "mostrami" serve al valutatore: senza l'output di `grep` e di `git log` nella conversazione, il valutatore non ha prove che i task siano spuntati e committati.

Il prompt non spiega come lavorare. Leggere le sezioni di `DESIGN.md` indicate in `Reads`, un commit per task con il messaggio del campo `Commit`, test prima del commit: sono le regole 1, 2, 4 e 5 del `CLAUDE.md` del progetto, e ogni sessione le carica anche nel worktree, perché il file è versionato.

### Le due sessioni al lavoro

Dopo l'invio le due sessioni partono. Alla fine di un turno, invece di fermarsi con un riepilogo, Claude riprende: il valutatore ha visto che mancano dei task e lo ha rimandato al lavoro. `/goal` senza argomenti apre il pannello con la condizione e il suo stato, che si chiude con `Esc`. `/goal clear` annulla l'obiettivo, se ti accorgi che la condizione era sbagliata.

`/goal` si combina con auto mode, la modalità di permesso predefinita (capitolo 11). Auto mode evita le richieste di permesso dentro il turno, `/goal` evita che Claude si fermi tra un turno e l'altro. Insieme ti lasciano libero di guardare altro per un po'. Se però una sessione chiede qualcosa che il classificatore non lascia passare, o una domanda vera (la regola 1 del `CLAUDE.md` dice di fermarsi quando un task è ambiguo), resta in attesa finché non rispondi.

Quando la condizione è soddisfatta la sessione si ferma da sola. Il lavoro è già committato sul branch del worktree:

```bash
git log --oneline -4
```

```text
e41c2d7 feat(pipeline): wire UploadPhotosAction to ProcessPhoto
9b07a15 feat(backend): domain events
3fd8c61 feat(pipeline): ProcessPhoto job
a52e0f9 chore(backend): bind service contracts
```

<!-- TODO screenshot: sessione fase6-pipeline con il pannello di /goal aperto e lo stato della condizione -->

::: {.callout .callout-tip}
[Suggerimento]{.callout-title}

Prima di scrivere un `/goal` lungo, prova il controllo a mano nel worktree: `composer test` in `backend/`, `npm run build` in `frontend/`. Se la suite è già rossa all'inizio (sul branch del capitolo 19 T042 e T043 sono ancora `[~]`), la sessione passerà il tempo a sistemare test che non c'entrano con la sua fase. In quel caso chiudi prima T042 e T043 su `main`, poi apri i worktree.
:::

## 20.5 Chiudere il primo giro

Ogni track finisce in una pull request, come nel capitolo 19: una PR per fase. Dalla sessione:

```text
pusha il branch e apri una pull request verso main con gh, titolo "Phase 6: image processing pipeline", e nel corpo l'elenco dei task chiusi
```

Poi fai i due task di review a mano, T080 sul worktree del backend e T062 su quello del frontend, e rivedi le PR. Per riprendere una PR in un secondo momento senza toccare il tuo checkout, `claude --worktree "#12"` (con il numero della tua PR) apre una sessione in un worktree che parte da quella pull request. La review con `/code-review` è l'argomento del capitolo 22. Quando entrambe sono mergiate, aggiorna `main` in locale:

```bash
git switch main
git pull
```

Se invece preferisci mergiare in locale senza passare da GitHub, `worktree.baseRef: "head"` diventa necessario: le sessioni del secondo giro devono vedere la pipeline anche se non l'hai pushata.

## 20.6 Tutto da una schermata con l'agent view

Due terminali si gestiscono. Con quattro o cinque sessioni diventa scomodo, e il secondo giro ne ha almeno due: la Fase 3 (admin Filament, ora che `ProcessPhoto` esiste) e la Fase 5 (componenti React).

### Sessioni in background

`claude --bg` avvia una sessione direttamente in background, con un nome e un prompt. Non serve creare il worktree a mano: prima di modificare file, una sessione in background si sposta da sola in un worktree isolato sotto `.claude/worktrees/`. `.worktreeinclude` vale per ogni worktree che Claude Code crea con git, quindi anche qui `backend/.env` arriva da solo.

```bash
claude --bg --name fase3-admin '/goal i task da T046 a T053 hanno Status [x] in docs/TASKS.md (mostrami le righe Status), "composer test" nella cartella backend esce con codice 0 e ogni task ha il suo commit'
claude --bg --name fase5-componenti '/goal i task da T063 a T070 hanno Status [x] in docs/TASKS.md (mostrami le righe Status), "npx vitest run" e "npm run build" nella cartella frontend escono con codice 0 e ogni task ha il suo commit'
```

Gli apici singoli servono perché la condizione contiene i doppi apici. Per la Fase 5 il controllo è `npx vitest run` e non `npm test`: Vitest è tra le dipendenze, ma non è detto che a questo punto ci sia uno script `test`, e `vitest` senza `run` resterebbe in ascolto delle modifiche. Anche qui T054 e T071, le review di fase, restano a te. Ogni sessione parte da un worktree senza `vendor/` o `node_modules/` e li installa da sola prima di lanciare i test.

Puoi anche mandare in background una sessione già aperta. `/background` (alias `/bg`) stacca la sessione corrente, e `/fork` (capitolo 15) ne copia la conversazione in una nuova sessione in background mentre tu continui in quella attuale.

### L'agent view

```bash
claude agents
```

L'agent view mostra tutte le sessioni in background in una schermata, raggruppate per stato: Working, Needs input, Completed. Quelle che hanno bisogno di te stanno in alto. Ogni riga ha il nome, un riassunto di cosa sta facendo e da quanto tempo gira.

I tasti che userai:

| Tasto | Cosa fa |
| --- | --- |
| `Space` | Anteprima della riga selezionata: l'ultimo messaggio o la domanda in sospeso. Puoi rispondere da lì senza entrare |
| `Enter` | Entra nella sessione completa |
| `←` su prompt vuoto | Torna alla lista. Da qualsiasi sessione aperta manda la sessione in background e apre l'agent view |
| `Ctrl+T` | Fissa in alto la sessione selezionata |

Nel nostro caso la sessione da tenere d'occhio è `fase3-admin`: T046 lancia `php artisan filament:install --panels`, un installer che fa domande, ed è il punto in cui la sessione rischia di fermarsi. Fissala con `Ctrl+T`. Se a metà lavoro chiede se può aggiungere un pacchetto a `composer.json`, la vedi passare in Needs input, rispondi dall'anteprima con `Space` e torni alla lista.

Le sessioni continuano a girare anche se chiudi il terminale. Dalla shell le gestisci per id:

```bash
claude attach <id>    # riapre la sessione in questo terminale
claude logs <id>      # mostra l'output senza entrare
claude stop <id>      # ferma la sessione
claude rm <id>        # la toglie dalla lista
```

<!-- TODO screenshot: agent view con fase3-admin fissata in alto (Working) e fase5-componenti, anteprima aperta con Space -->

### Quando una sessione finisce

Una sessione in background che ha finito salva il lavoro: committa, pusha il branch se il repo ha un remote e, quando il task lo richiede, apre una pull request in bozza. Il numero della PR compare sulla riga come etichetta `#N`, colorata per stato: gialla in attesa dei controlli o della review, verde pronta, viola mergiata. Sulla Photogallery, con la CI di GitHub Actions configurata nel capitolo 19, l'etichetta resta gialla finché i job di backend e frontend non sono passati.

<!-- TODO screenshot: riga completata nell'agent view con l'etichetta #N della PR -->

## 20.7 Un subagent con il suo worktree

Se preferisci restare in una sola sessione, puoi dare il worktree ai subagent. La Fase 5 è il caso più adatto: `docs/TASKS.md` la definisce "heavily parallelizable" e, completato T063, i task T064, T065 e T066 dipendono solo da cose già in `main`. È l'alternativa alla sessione `fase5-componenti` del paragrafo precedente: scegli una delle due strade, non tutte e due.

Il wizard di `/agents` non esiste più, quindi il subagent si crea scrivendo il file `.claude/agents/task-executor.md` (oppure chiedendo a Claude di scriverlo):

```markdown
---
name: task-executor
description: Esegue un singolo task di docs/TASKS.md in un worktree isolato, con test e commit. Usalo per i task indipendenti di una wave.
isolation: worktree
---

Ricevi l'ID di un task di docs/TASKS.md.

1. Leggi il task e le sezioni di docs/DESIGN.md elencate in Reads.
2. Implementa solo quel task, rispettando DESIGN.md e i criteri di Acceptance.
3. Installa le dipendenze se mancano. Scrivi o aggiorna i test ed eseguili
   finché passano: "composer test" in backend, "npx vitest run" in frontend.
4. Spunta lo Status del task e committa nello stesso commit, con il messaggio
   indicato nel campo Commit.
5. Se il task richiede di modificare composer.json o package.json, fermati e
   riportalo invece di procedere.
6. Riporta: file modificati, esito dei test, nome del branch.
```

`isolation: worktree` dà a ogni istanza un worktree temporaneo, che Claude Code rimuove se l'istanza non ha modificato niente. Il punto 5 viene dalla lista dei file calamita: tre istanze che aggiungono pacchetti in parallelo producono tre `package-lock.json` diversi da conciliare.

In una sessione normale nella radice del repo:

```text
usa task-executor in parallelo sui task T064, T065 e T066
```

I subagent girano in background per default: la sessione principale mostra che sta aspettando gli agent in corso, `/tasks` li elenca e tu puoi continuare a scrivere. Ogni istanza lavora nella sua copia e nessuna vede le modifiche a metà delle altre. Se da un altro terminale lanci `git worktree list` mentre lavorano, vedi comparire un worktree per istanza, ciascuno sul suo branch. Quando finiscono, le copie senza modifiche spariscono da sole e quelle con dei commit restano, con il loro branch, pronte per il merge. A quel punto chiedi alla sessione principale di mergiarle in `main` e di rilanciare `npx vitest run`, poi passi a T067, che dipende da T066.

Un dettaglio sul punto di partenza: il worktree di un subagent segue la stessa regola di `--worktree`. Parte dal branch principale sul remote, oppure dal tuo `HEAD` locale se hai impostato `worktree.baseRef: "head"` come nel paragrafo 20.2. In entrambi i casi T063 deve essere già lì: se lo hai fatto in un altro worktree e non l'hai ancora integrato, i tre subagent non trovano `ErrorBoundary` e `Modal`.

## 20.8 Integrare e fare pulizia

Quando le PR del secondo giro sono pronte, le rivedi e le mergi come quelle del primo. Il merge di `docs/TASKS.md` è il punto in cui un conflitto è più probabile, perché tutte le sessioni l'hanno modificato. Le righe sono in sezioni diverse, quindi di solito Git le unisce da solo. Se non ci riesce, il conflitto riguarda solo delle caselle `[ ]` e `[x]` e si risolve tenendo le `[x]`.

Poi fai pulizia. Prima guarda cosa è rimasto:

```bash
git worktree list
```

Quando esci da una sessione avviata con `--worktree`, Claude Code ti chiede se tenere o rimuovere il worktree, se contiene del lavoro. Per le sessioni in background, `claude rm <id>` toglie la sessione dalla lista insieme al suo worktree, quando è sicuro farlo. Quello che resta lo togli con Git:

```bash
git worktree remove .claude/worktrees/fase6-pipeline
git branch -d worktree-fase6-pipeline
```

`git worktree remove` rifiuta di cancellare un worktree con modifiche non committate, e `git branch -d` rifiuta un branch non mergiato. Se uno dei due si lamenta, guarda prima di aggiungere `--force`: di solito c'è un commit che non è arrivato in `main`.

### Quanto costa

Ogni sessione consuma la quota del tuo piano come una sessione normale, e lo stesso vale per ogni istanza di subagent. Quattro sessioni Opus in parallelo consumano circa quattro volte più in fretta di una, e la Wave 1 della Photogallery non è un lavoro da cinque minuti. `/usage` mostra cosa sta consumando i limiti, con il dettaglio per subagent. Usa il parallelo per track che davvero non si toccano, come Fase 4 e Fase 6, e lascia in sequenza il resto: la Wave 3 di `docs/TASKS.md` (Fasi 12 e 13) è dichiarata sequenziale proprio perché ogni passo dipende dal precedente.

## 20.9 Comandi di riferimento

| Comando | A cosa serve |
| --- | --- |
| `claude --worktree <nome>` | Sessione in un worktree isolato in `.claude/worktrees/<nome>`, branch `worktree-<nome>` |
| `claude --worktree "#123"` | Worktree che parte da una pull request |
| `.worktreeinclude` | File ignorati da Git da copiare in ogni nuovo worktree |
| `{"worktree": {"baseRef": "head"}}` | I worktree partono dall'`HEAD` locale invece che dal `main` remoto |
| `/goal <condizione>`, `/goal`, `/goal clear` | Imposta, mostra, annulla l'obiettivo |
| `claude --bg --name <nome> "<prompt>"` | Sessione in background |
| `/background` (`/bg`), `/fork` | Stacca la sessione corrente, copia la conversazione in background |
| `claude agents` | Agent view |
| `claude attach`, `logs`, `stop`, `rm <id>` | Gestire le sessioni in background dalla shell |
| `isolation: worktree` | Nel frontmatter di un subagent: un worktree temporaneo per istanza |
| `git worktree list`, `git worktree remove <percorso>` | Vedere e rimuovere i worktree |

## Riepilogo {.unlisted}

- Un subagent isola il contesto, un worktree isola file e branch, una sessione in background libera il terminale. Per task che scrivono codice in parallelo serve il worktree.
- Prima di parallelizzare leggi dipendenze e criteri di accettazione dei task: T048 dipende da `ProcessPhoto` anche se il suo `Depends on` non lo dice.
- `.claude/worktrees/` va nel `.gitignore`, `.worktreeinclude` copia `backend/.env`, `worktree.baseRef: "head"` serve quando mergi in locale senza pushare.
- Una condizione di `/goal` funziona solo se nomina un controllo che Claude esegue e mostra: `composer test` esce con codice 0, le righe Status, il `git log`.
- `claude --bg` e `claude agents` ti fanno seguire più sessioni da una schermata. Ogni sessione consuma quota come una normale.

## Esercizio {.unlisted}

Parti dal branch `book/cap-13-wave-2-api` del companion repo e fai il primo giro di questo capitolo con i due strumenti diversi: committa `.gitignore`, `.worktreeinclude` e `baseRef`, avvia la Track A con `claude --worktree fase6-pipeline` e il `/goal` del paragrafo 20.4, e lancia la Track C come sessione in background con `claude --bg --name fase4-frontend` e il suo `/goal`. Segui la seconda dall'agent view fino a Completed.

L'esercizio è finito quando `git log --oneline` sul branch della pipeline mostra un commit per ciascuno dei task T029, T032, T035 e da T072 a T079, `composer test` passa in quel worktree, `npm run build` e `npm run lint` passano sul branch del frontend e, dopo merge e pulizia, `git worktree list` mostra soltanto la cartella principale.
