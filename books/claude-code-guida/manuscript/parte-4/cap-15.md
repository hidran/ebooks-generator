# Capitolo 15. Contesto e memoria sotto controllo

## Cosa imparerai

- A leggere come si riempie la finestra di contesto con `/context`, `/skill-doctor` e `/usage`.
- Quando usare `/compact`, `/rewind`, `/fork` e `/clear` in una conversazione lunga.
- Cosa salva la memoria automatica, dove la trovi e come la correggi o la spegni.
- A far controllare configurazione e istruzioni a `/doctor` e `/doctor prompt-audit`.

Nei capitoli 11-14 hai riempito `cc-advanced-lab` di cose utili: regole di permesso in `.claude/settings.json`, gli hook che formattano il Python e proteggono `data/`, i server MCP, il plugin `cc-lab-toolkit`. Ognuno di questi pezzi occupa un po' di spazio in ogni sessione, anche quando non lo usi. Questo capitolo chiude la Parte IV con gli strumenti per vedere quanto spazio, per gestire una conversazione che si è allungata troppo e per tenere in ordine le istruzioni che Claude legge all'avvio, sia quelle che scrivi tu sia quelle che scrive lui.

Prerequisiti: il progetto `cc-advanced-lab` del capitolo 11, con quello che gli hanno aggiunto i capitoli 12-14. Se hai saltato qualche capitolo va bene lo stesso: vedrai meno voci nei pannelli, ma i comandi funzionano uguale.

## 15.1 Cosa c'è nella finestra di contesto

La finestra di contesto è tutto quello che il modello vede quando prepara la risposta successiva. Dentro ci sono i tuoi messaggi e parecchio altro, e conviene sapere cosa, perché è questo che determina come va una sessione lunga.

Le voci sono quattro. C'è il system prompt, cioè le istruzioni interne di Claude Code e le definizioni dei tool di base (`Read`, `Edit`, `Bash`, `Agent` e gli altri del capitolo 2). Ci sono le estensioni: skill, agent, plugin e server MCP. Di ognuna Claude Code carica sempre nome e descrizione, perché è da lì che il modello capisce quando usarla; il corpo di una skill arriva solo quando serve (lo hai visto nel capitolo 9). Ci sono i file di memoria: `CLAUDE.md`, le regole in `.claude/rules/` e l'indice della memoria automatica. E infine c'è la conversazione: i messaggi, ogni file che Claude ha letto, l'output di ogni comando lanciato.

Con Claude Opus 5.5 la finestra di default è di un milione di token, quindi di spazio ce n'è parecchio (il modello e la sua finestra possono cambiare: controlla `/model`). Il limite pratico arriva prima di quello tecnico, per due motivi. Ogni turno elabora tutto il contesto, quindi una sessione gonfia consuma di più i limiti del tuo piano. E più materiale c'è, più le istruzioni e le decisioni dell'inizio competono con quello che è arrivato dopo: in una sessione lunga e piena di argomenti diversi Claude comincia a dimenticare convenzioni che all'inizio rispettava.

## 15.2 Misurare con /context, /skill-doctor e /usage

Prima di gestire il contesto conviene guardarlo. Apri `cc-advanced-lab` e lancia `claude`. Perché i pannelli abbiano qualcosa da mostrare, fai tre domande di sola lettura:

```text
leggi src/report.py e il suo test e dimmi cosa fanno
```

```text
quante righe ha data/vendite.csv e quali colonne contiene?
```

```text
come si lanciano i test in questo progetto?
```

Sono domande innocue: non modificano niente e in auto mode passano senza richieste di conferma.

### /context

Scrivi `/context`. Il pannello mostra come è suddivisa la finestra: quanto occupano il system prompt e i tool di sistema, i tool dei server MCP, gli agent, le skill, i file di memoria e i messaggi, più lo spazio ancora libero.

<!-- TODO screenshot: /context in cc-advanced-lab dopo le tre domande, con le categorie system prompt, tool, MCP, skill, agent, memory files, messaggi -->

La prima cosa da notare è che una parte del contesto è occupata prima ancora che tu scriva il primo prompt. Skill, agent e plugin pesano anche se in questa sessione non li usi, perché nome e descrizione sono sempre caricati. Per i server MCP il conto è più basso di quanto ti aspetteresti: grazie al tool search del capitolo 13, all'avvio Claude Code carica solo i nomi dei tool e recupera le definizioni complete quando servono.

La seconda cosa è la voce dei messaggi. Dopo tre domande è piccola. Dopo un'ora di lavoro, con qualche file grosso letto per intero e l'output di una suite di test, diventa la voce principale. È quella che `/compact` e `/clear` riducono.

### /skill-doctor

`/skill-doctor` risponde a una domanda precisa: quali skill valgono il loro costo? Per ogni skill mostra quanto contesto occupa e quanto spesso viene usata.

Una skill leggera e usata spesso va benissimo. Una skill con una descrizione lunghissima che non hai mai attivato è una candidata da disattivare: se è una skill di progetto la togli da `.claude/skills/`, se arriva da un plugin decidi dal manager `/plugin` (capitolo 14) se il plugin ti serve ancora. Lo stesso pannello è un buon motivo per tenere corte le descrizioni delle skill che scrivi (capitolo 9).

### /usage

`/usage` guarda la stessa cosa da un altro lato: cosa consuma i limiti del tuo piano. La ripartizione è per skill, subagent, plugin e server MCP. Se un subagent che lanci spesso legge mezzo repository a ogni giro, qui lo vedi.

Tutti e tre i pannelli si chiudono con `Esc`.

## 15.3 Compattare, riavvolgere, biforcare, ripartire

Per una conversazione che si è allungata hai quattro strumenti: `/compact`, `/rewind`, `/fork` e `/clear`. Fanno cose diverse e conviene provarli in ordine nella stessa sessione, così vedi l'effetto di ciascuno.

### /compact con istruzioni

`/compact` riassume la conversazione e libera spazio. Il riassunto prende il posto dei messaggi più vecchi: la sessione resta la stessa, ma Claude ricorda i dettagli in forma compatta. Il comando accetta istruzioni su cosa conservare, e conviene darle sempre:

```text
/compact Mantieni la struttura del progetto, le decisioni prese e i test che falliscono
```

Senza istruzioni il riassunto decide da solo cosa tenere, e quello che a te sembra importante (il nome scelto per una funzione, il test che fallisce in modo intermittente) può finire in una frase generica o sparire. Con le istruzioni gli dici cosa non deve perdere. Nella Parte VI, quando una fase del Photogallery si allunga, compatterai proprio così: stato dei task, decisioni prese, finding ancora aperti (capitolo 19).

Claude Code compatta anche da solo quando la finestra si avvicina al limite. Va bene come rete di sicurezza, ma una compattazione automatica arriva quando decide lui e senza le tue istruzioni. Se il progetto ha bisogno che certe informazioni tornino sempre in contesto dopo una compattazione, usa l'hook `SessionStart` con matcher `compact` del capitolo 12.

::: {.callout .callout-tip}
[Suggerimento]{.callout-title}

Compatta quando chiudi un pezzo di lavoro, non quando le risposte cominciano a peggiorare. Dopo che un task è finito e i test passano sai esattamente cosa vale la pena tenere, e il riassunto viene meglio.
:::

### /rewind e il doppio Esc

Per avere qualcosa da riavvolgere, chiedi a Claude una modifica piccola:

```text
aggiungi in cima a src/report.py un commento di una riga che spiega cosa fa il modulo
```

Ora premi `Esc` due volte (oppure scrivi `/rewind`). Si apre un menu con i punti precedenti della conversazione, uno per ogni tuo prompt. Scegli il punto a cui tornare e decidi cosa ripristinare: il codice, la conversazione o entrambi. In più ci sono due opzioni di riassunto, che sono una compattazione mirata su una parte sola: `Summarize from here` comprime la conversazione dal punto scelto in avanti, `Summarize up to here` quella che lo precede e lascia intatti i messaggi successivi. Nessuna delle due tocca i file.

Le tre combinazioni servono in situazioni diverse:

- Ripristini codice e conversazione quando Claude ha imboccato una strada sbagliata e vuoi riprovare con un prompt migliore, come se il tentativo non fosse mai avvenuto.
- Ripristini solo il codice quando la discussione ti è servita (hai capito perché l'approccio non funziona) ma i file devono tornare com'erano.
- Ripristini solo la conversazione quando la modifica ti va bene ma il dialogo che l'ha prodotta è andato fuori tema e occupa spazio.

Nella prova con il commento, ripristina solo il codice e poi lancia `git diff`: `src/report.py` è tornato com'era.

::: {.callout .callout-warning}
[Attenzione]{.callout-title}

I checkpoint di `/rewind` tengono traccia delle modifiche fatte con i tool di modifica dei file, come `Edit` e `Write`. Quello che cambia un comando lanciato con `Bash` (un `rm`, una migrazione sul database) resta com'è. Anche le correzioni applicate da `/code-review --fix` (capitolo 22) non si annullano con `/rewind`. Per tutto questo la rete di sicurezza è Git: committa prima di lasciare a Claude un lavoro grosso.
:::

### /fork

`/fork` copia la conversazione in una nuova sessione in background. La sessione principale resta dov'è, con tutto il suo contesto, e la copia parte dallo stesso punto. Serve quando vuoi esplorare un'alternativa senza perdere il filo, per esempio tentare un refactoring di cui non sei sicuro mentre la sessione principale resta sul codice che funziona.

La copia la ritrovi tra le sessioni in background, nell'agent view che aprirai con `claude agents` nel capitolo 20. Ricorda che è una sessione vera: consuma il piano come una sessione normale.

### /clear

`/clear` riparte da zero. La conversazione sparisce dal contesto e Claude Code ricarica i file di memoria come all'avvio. I file sul disco restano come sono, perché `/clear` tocca solo la conversazione. Si usa quando cambi argomento. Gli hook `SessionStart` scattano anche dopo un `/clear`, con origine `clear`: un hook senza matcher, o con matcher `clear`, rimette in contesto quello che stampa. Quello con matcher `compact` del capitolo 12 qui non parte.

Se stai per fare `/clear` a metà di un lavoro, prima chiedi a Claude di scrivere su file dove sei arrivato:

```text
scrivi in STATE.md cosa abbiamo fatto, le decisioni prese e cosa resta da fare
```

Dopo il `/clear` riparti con un prompt che dice di leggere `STATE.md`. Nel Photogallery il ruolo di `STATE.md` lo fanno le specifiche e `docs/TASKS.md`: stanno sul disco, quindi tra una fase e l'altra puoi azzerare il contesto senza perdere niente (capitoli 18 e 19).

### Quale usare

| Situazione | Comando |
| --- | --- |
| Il task va avanti, la finestra è piena di dettagli che non servono più | `/compact` con istruzioni |
| Claude ha preso una strada sbagliata, vuoi tornare a prima | `Esc Esc` o `/rewind` |
| Vuoi provare un'alternativa senza toccare la sessione principale | `/fork` |
| Il task è finito e passi a un altro argomento | `/clear` |

## 15.4 Un task, una sessione

La regola pratica che tiene insieme il paragrafo precedente è questa: un task, una sessione. Le conversazioni lunghe su argomenti diversi sono il modo più rapido per peggiorare i risultati, perché ogni argomento lascia in contesto file letti, tentativi scartati e decisioni che con il task successivo non c'entrano.

In `cc-advanced-lab` vuol dire, per esempio, che se hai appena sistemato un test di `src/report.py` e adesso vuoi il report settimanale delle vendite, fai `/clear` o apri una sessione nuova. Il report non ha bisogno di sapere come hai debuggato il test, e il debug lasciato in contesto può solo confondere la richiesta nuova.

Quello che deve sopravvivere tra un task e l'altro non va lasciato nella conversazione: va su file. Le convenzioni stabili stanno in `CLAUDE.md`, lo stato di un lavoro a metà in un file come `STATE.md` o nella lista dei task, le preferenze personali nella memoria automatica.

## 15.5 Le istruzioni che scrivi tu, in breve

Il capitolo 7 spiega `CLAUDE.md` per intero: i livelli, cosa scriverci e cosa no, le regole per percorso, AGENTS.md. Qui serve solo un promemoria, perché le sezioni successive ci tornano sopra.

I livelli sono quattro: organizzazione (un percorso gestito dall'IT), utente (`~/.claude/CLAUDE.md`), progetto (`./CLAUDE.md` o `./.claude/CLAUDE.md`, condiviso via Git) e locale (`./CLAUDE.local.md`, fuori da Git). Resta sotto le duecento righe e scrivi istruzioni verificabili: "usa due spazi di indentazione" funziona meglio di "formatta bene il codice". Per `cc-advanced-lab` basta poco:

```markdown
# cc-advanced-lab

## Comandi
- Test: `python -m pytest -q`
- Formattazione: `ruff format src tests`

## Regole
- Non modificare mai i file in `data/`: lavora su copie in `tmp/`
- Ogni nuova funzione in `src/` ha un test in `tests/`

<!-- Nota per i manutentori: le regole Python stanno in .claude/rules/python.md -->
```

Le regole che valgono solo per i file Python stanno in `.claude/rules/python.md`, con il campo `paths:` nel frontmatter, e si caricano solo quando Claude lavora su un file che corrisponde. Il commento HTML in fondo viene tolto prima di arrivare a Claude: è una nota per i colleghi che non costa contesto.

Le istruzioni si caricano all'avvio, quindi dopo aver scritto i due file esci e rilancia `claude`. Chiedi di leggere `src/report.py`, così la regola Python entra in gioco, poi scrivi `/memory`: vedi l'elenco dei file di istruzioni caricati. In `/context` gli stessi file compaiono nella sezione Memory files, ciascuno con il suo peso.

Due cose da tenere a mente anche in questo capitolo. `CLAUDE.md` orienta Claude, ma non lo vincola: "non modificare mai i file in `data/`" è un'istruzione che di solito viene seguita, mentre l'hook `protect-files.sh` del capitolo 12 blocca ogni volta le modifiche fatte con `Edit` e `Write`. E se un repository ha un `AGENTS.md` e nessun `CLAUDE.md`, Claude Code legge quello.

## 15.6 La memoria automatica

Oltre a `CLAUDE.md`, che scrivi tu, c'è la memoria automatica, che scrive Claude. Ci finiscono le tue preferenze, le correzioni che gli dai durante il lavoro e il contesto del progetto che non può ricavare leggendo il codice. Claude decide da solo cosa vale la pena annotare, e quando gli chiedi esplicitamente di ricordare qualcosa lo salva lì.

Prova in `cc-advanced-lab`:

```text
ricorda che in questo progetto preferisco pytest con l'opzione -q e messaggi di commit in italiano
```

Claude sceglie dove scrivere, crea i file e ti avvisa con un messaggio di memoria salvata. Se risponde solo a parole senza salvare niente, riformula in modo più diretto: "salva in memoria che...".

<!-- TODO screenshot: messaggio di memoria salvata dopo il prompt "ricorda che..." -->

### Dove vive

La memoria sta nella tua home, sotto `~/.claude/projects/`, con una cartella per progetto e dentro una cartella `memory/`. È condivisa tra i worktree dello stesso repository: una preferenza salvata nel worktree di una feature vale anche nel checkout principale, il che tornerà utile con le wave parallele del capitolo 20. Visto che sta nella home e non nel repository, i colleghi non la vedono e non ti segue su un altro computer.

Il nome della cartella del progetto deriva dal percorso completo del repository, con i separatori sostituiti da trattini, quindi contiene anche il tuo nome utente. Per guardarne il contenuto senza scrivere quel percorso, usa un glob dal prompt di Claude Code (il prefisso `!` lancia un comando di shell):

```bash
!cat ~/.claude/projects/*cc-advanced-lab/memory/*.md
```

Vedrai due file: `MEMORY.md` e quello con le preferenze appena salvate. `MEMORY.md` fa da indice. Viene caricato a ogni sessione, fino a duecento righe o 25 KB, e rimanda agli altri file, che Claude legge quando gli servono. Se l'indice supera quel limite, la parte in fondo non entra in contesto all'avvio.

### Leggere, correggere, spegnere

Sono file Markdown normali. Puoi aprirli con l'editor, correggere una preferenza che non vale più, cancellare un file intero. Se Claude ha annotato una cosa sbagliata (succede, per esempio quando hai dato una correzione valida per un caso solo), la correzione più rapida è a mano sul file.

`/memory` mostra i file di istruzioni caricati e la cartella della memoria automatica. Dallo stesso menu attivi o disattivi la memoria automatica. Spegnerla ha senso in un repository dimostrativo, durante una registrazione o quando vuoi che ogni sessione parta solo da quello che hai scritto tu.

L'interruttore di `/memory` salva `autoMemoryEnabled` in `~/.claude/settings.json`, quindi vale per tutti i tuoi progetti. Per spegnerla in un progetto solo, scrivi `"autoMemoryEnabled": false` nelle impostazioni di quel progetto. Esiste anche la variabile d'ambiente `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`, comoda negli script.

## 15.7 CLAUDE.md o memoria automatica?

I due meccanismi finiscono entrambi in contesto all'avvio, ma hanno un padrone diverso.

| | `CLAUDE.md` | Memoria automatica |
| --- | --- | --- |
| Chi lo scrive | Tu | Claude |
| Cosa contiene | Comandi, convenzioni, regole | Preferenze, correzioni, contesto |
| Dove sta | Nel repository (o nella tua home, a livello utente) | `~/.claude/projects/<progetto>/memory/` |
| Chi lo vede | Il team, via Git | Solo tu, su questa macchina |
| Quando cambia | Quando lo modifichi tu | Quando Claude annota o tu dici "ricorda" |

Una regola semplice per scegliere: se l'informazione serve a chiunque lavori sul progetto, va in `CLAUDE.md`. Il comando dei test, la cartella da non toccare, il formato dei messaggi di commit concordato con il team sono istruzioni di progetto. "Preferisco risposte brevi" o "uso pytest con `-q`" sono preferenze tue, e la memoria automatica è il posto giusto.

Ogni tanto apri la cartella della memoria e cerca annotazioni che dovrebbero stare altrove. Se Claude ha imparato da una tua correzione che "le migrazioni non si lanciano mai sul database di produzione", quella è una regola che il team deve conoscere: spostala in `CLAUDE.md`, falla passare da una review e cancellala dalla memoria. E se è una regola che non deve mai essere violata, nessuno dei due file basta: serve una regola di permesso (capitolo 11) o un hook (capitolo 12).

## 15.8 Far controllare la configurazione

A questo punto in `cc-advanced-lab` ci sono istruzioni sparse in parecchi posti: `CLAUDE.md`, la regola Python, le skill, gli agent, il plugin, la memoria automatica. Tenerli coerenti a mano è noioso, e Claude Code ha due comandi che lo fanno per te.

### /doctor

`/doctor` fa un controllo completo della configurazione e può anche correggere i problemi che trova. Tra le altre cose guarda `CLAUDE.md` e ti suggerisce di togliere quello che Claude può ricavare da solo leggendo il codice, come l'elenco delle cartelle o delle dipendenze. È lo stesso consiglio del capitolo 7, solo che stavolta te lo dà lo strumento, riga per riga. Il pannello si chiude con `Esc`.

### /doctor prompt-audit

`/doctor prompt-audit` va più a fondo sulle istruzioni. Legge `CLAUDE.md`, le regole, le skill e gli agent, e segnala tre tipi di problemi: istruzioni scritte per modelli vecchi (gli avvertimenti del tipo "ricordati di leggere il file prima di modificarlo" che oggi sono solo rumore), riferimenti a file che non esistono più e istruzioni che si contraddicono tra loro, magari una in `CLAUDE.md` e l'altra in una skill.

L'analisi è un giro del modello, quindi ci mette qualche decina di secondi e consuma il piano come un prompt normale. Alla fine propone le modifiche ma non tocca niente finché non glielo chiedi. Lo puoi verificare con `git status` subito dopo: il working tree è com'era.

::: {.callout .callout-example}
[Esempio]{.callout-title}

Immagina che in `cc-advanced-lab` il `CLAUDE.md` dica di lanciare i test con `python -m pytest -q`, mentre un agent o una skill scritti mesi prima usano ancora `pytest -v`. Nessuno dei due è sbagliato da solo, ma insieme danno a Claude due istruzioni diverse per la stessa cosa. È esattamente il genere di conflitto che `prompt-audit` mette in evidenza.
:::

### claude doctor dal terminale

La stessa diagnosi si lancia anche fuori da Claude Code, dalla shell:

```bash
claude doctor
```

Mostra lo stato dell'installazione, gli errori nei file di impostazioni e le correzioni suggerite, senza avviare una sessione. È il comando da ricordare quando Claude Code non parte, oppure parte e ignora un `settings.json` che hai appena modificato: un JSON malformato salta fuori qui.

::: {.callout .callout-warning}
[Attenzione]{.callout-title}

L'output di `/doctor` e di `claude doctor` contiene il percorso dell'installazione, che include il tuo nome utente, e `/memory` mostra il nome della cartella del progetto, che lo contiene pure. Se fai screenshot o registri il terminale per un collega, copri quelle righe.
:::

## 15.9 Promemoria dei comandi

| Comando | A cosa serve |
| --- | --- |
| `/context` | Come è suddivisa la finestra di contesto |
| `/skill-doctor` | Costo in contesto e frequenza d'uso di ogni skill |
| `/usage` | Cosa consuma i limiti del piano, per skill, subagent, plugin e server MCP |
| `/compact [istruzioni]` | Riassume la conversazione, conservando quello che indichi |
| `/rewind` o `Esc Esc` | Torna a un punto precedente: codice, conversazione o entrambi |
| `/fork` | Copia la conversazione in una sessione in background |
| `/clear` | Riparte con una conversazione vuota |
| `/memory` | File di istruzioni caricati, cartella e interruttore della memoria automatica |
| `/doctor` | Controllo completo della configurazione, con correzioni |
| `/doctor prompt-audit` | Istruzioni obsolete, file mancanti, conflitti; propone senza applicare |
| `claude doctor` | La diagnosi dalla shell, senza avviare una sessione |

## 15.10 Dalla Parte IV ai progetti

Con questo capitolo hai tutti gli strumenti della Parte IV: i permessi e la sandbox decidono cosa Claude può fare, gli hook automatizzano i controlli che non vuoi delegare al modello, MCP e i plugin lo collegano ai servizi e al team, e adesso sai misurare quanto costa tutto questo in contesto e tenerlo in ordine.

Da qui il libro cambia passo. Nella Parte V costruisci una landing page dall'idea al deploy su Firebase, nella Parte VI il Photogallery, un'applicazione Laravel e React con 124 task divisi in 14 fasi. Sono progetti lunghi, fatti di molte sessioni: userai `/compact` con istruzioni quando una fase si allunga, `/clear` prima di cominciare la successiva e un `CLAUDE.md` corto che ogni sessione nuova rilegge all'avvio.

## Riepilogo

- `/context` mostra come è suddivisa la finestra; skill, agent e plugin occupano spazio anche quando non li usi, perché nome e descrizione sono sempre caricati.
- `/skill-doctor` ti dice quali skill pesano senza essere usate, `/usage` cosa consuma i limiti del piano.
- `/compact` con istruzioni quando il task continua, `Esc Esc` per tornare indietro, `/fork` per un'alternativa in background, `/clear` quando cambi argomento. I checkpoint non coprono i comandi `Bash`: per quelli c'è Git.
- Un task, una sessione: quello che deve sopravvivere va su file (`CLAUDE.md`, `STATE.md`, la lista dei task).
- La memoria automatica la scrive Claude in `~/.claude/projects/<progetto>/memory/`, con `MEMORY.md` come indice caricato fino a duecento righe; la correggi a mano e la spegni da `/memory`.
- `/doctor` e `/doctor prompt-audit` tengono pulita la configurazione; `claude doctor` funziona anche quando Claude Code non parte.

## Esercizio

In `cc-advanced-lab`, con il lavoro dei capitoli 11-14 al suo posto:

1. Avvia `claude`, fai le tre domande di sola lettura del paragrafo 15.2 e annota da `/context` quanto pesano messaggi, skill e file di memoria. Lancia `/skill-doctor` e segna la skill che pesa di più in rapporto all'uso.
2. Chiedi a Claude di aggiungere un commento in cima a `src/report.py`, poi usa `Esc Esc` e ripristina solo il codice. Controlla che `git status` non mostri modifiche a `src/report.py`.
3. Chiedi a Claude di ricordare una tua preferenza (per esempio i messaggi di commit in italiano). Trova il file nella cartella della memoria, correggi a mano la preferenza (per esempio aggiungi che il messaggio deve iniziare con un verbo all'imperativo), fai `/clear` e chiedi a Claude un messaggio di commit per una modifica qualsiasi.
4. Lancia `/doctor prompt-audit` e leggi il rapporto senza applicare niente.

L'esercizio è completo quando il messaggio di commit del punto 3 rispetta la preferenza che hai corretto a mano, e `git status` dopo il punto 4 mostra lo stesso stato di prima dell'audit.
