# Capitolo 8. Custom command e il plugin Superpowers

## Cosa imparerai

- Quando conviene trasformare un prompt che ripeti in un custom command, e come scriverlo.
- Come passare argomenti e contesto al comando: `$ARGUMENTS`, `$0`, `` !`comando` `` e `@file`.
- Tre comandi da usare da subito, più un `/commit` che tiene pulita la storia Git.
- Cosa porta il plugin Superpowers e come installarlo dal marketplace ufficiale.

Prerequisiti: i capitoli 1-7, e almeno un `CLAUDE.md` scritto (capitolo 7).

Pensa a quante volte hai scritto "lancia i test e dimmi quale fallisce" o "fai un commit con un messaggio decente". Ogni volta con parole un po' diverse: un giorno chiedi di "elencare gli import non usati", il giorno dopo di "trovare gli import inutili", e Claude fa due cose leggermente diverse. Le istruzioni cambiano con la fretta e con la memoria del momento, e il risultato cambia con loro.

Un custom command risolve il problema in modo banale: scrivi il prompt una volta, con calma, lo salvi in un file e da lì in poi lo richiami con una barra. Il prompt resta identico, quindi anche il comportamento resta prevedibile. La regola che uso: alla terza volta che riscrivo lo stesso prompt, lo trasformo in un comando. Non prima, perché le prime due volte servono a capire come formularlo bene.

C'è anche un lato di squadra. I comandi di progetto stanno nel repository, e chiunque apra Claude Code in quella cartella (un collega, un freelance appena arrivato, tu su un altro computer) li trova già pronti, con la loro descrizione nel menu.

## 8.1 Cos'è un custom command

Un custom command è un file Markdown in una cartella precisa. Il nome del file diventa il nome del comando: `review-types.md` diventa `/review-types`. Quando lo invochi, Claude Code prende il contenuto del file e lo usa come prompt, come se lo avessi scritto tu in quel momento.

::: {.callout .callout-deep-dive}
[Sotto il cofano]{.callout-title}

Oggi i custom command fanno parte delle skill. Un file `.claude/commands/deploy.md` e una skill in `.claude/skills/deploy/SKILL.md` creano entrambi `/deploy` e funzionano allo stesso modo. I file in `.claude/commands/` sono il formato più vecchio e continuano a funzionare; per il lavoro nuovo la documentazione consiglia le skill. Se un comando e una skill hanno lo stesso nome, vince la skill. Qui uso `.claude/commands/` perché è il modo più rapido per partire. Nel capitolo 9 vedi il formato skill, che fa le stesse cose e qualcuna in più (file di supporto, invocazione automatica, esecuzione in un contesto separato).
:::

### La struttura

Il formato minimo è un frontmatter YAML e un corpo:

```markdown
---
description: Descrizione breve che appare nell'autocompletamento
---

Corpo del comando: le istruzioni che Claude eseguirà.
Qui puoi scrivere un prompt strutturato, lungo quanto vuoi,
con elenchi, condizioni, criteri di output.
```

Tutti i campi del frontmatter sono facoltativi, ma due li userai quasi sempre. `description` è la riga che vedi nel menu quando premi `/`: tienila corta e chiara, perché è quello che leggete tu e i colleghi quando cercate il comando giusto. Serve anche a Claude, e nella sezione 8.3 vedi perché. `argument-hint` descrive l'argomento che il comando si aspetta e compare nell'autocompletamento dopo il nome.

I file di comando accettano lo stesso frontmatter delle skill, tranne `name` e `paths`. Quindi puoi già usare `allowed-tools` (i tool che Claude può usare senza chiederti il permesso mentre il comando è attivo), `model` ed `effort`, e `disable-model-invocation`, che vedi nella sezione 8.3. Il capitolo 9 li riprende tutti.

### Dove salvare i file

I comandi vivono in due posti: `~/.claude/commands/` per quelli personali, disponibili in ogni progetto su quella macchina, e `.claude/commands/` dentro il repository per quelli di progetto, da committare insieme al codice.

```text
~/.claude/commands/          # personali, sempre disponibili
├── fix-tests.md
├── clean-imports.md
└── spawn-pr.md

mio-progetto/.claude/commands/   # di progetto, committati nel repo
├── analyze-schema.md
└── deploy-staging.md
```

La regola che uso per scegliere: se il comando cita percorsi, script o convenzioni di quel progetto (deploy su staging, report dal database), appartiene al progetto; se funzionerebbe su qualsiasi progetto JavaScript o Python (review dei tipi, pulizia degli import), va nella cartella personale.

Puoi organizzare i comandi in sottocartelle. Una sottocartella aggiunge un prefisso al nome: `.claude/commands/frontend/component.md` diventa `/frontend:component`. Quando i comandi di un progetto superano la decina, il menu ne guadagna.

### Un esempio completo

Un comando completo, per i progetti TypeScript:

```markdown
---
description: Rileggi i tipi nel file corrente e suggerisci miglioramenti
argument-hint: (opzionale) path del file da analizzare
---

Leggi il file su cui stiamo lavorando (o $ARGUMENTS se specificato).
Controlla la qualità dei tipi TypeScript:

- Nessun `any` nascosto o implicito
- Tipi di ritorno sempre espliciti per le funzioni pubbliche
- Generics dove sarebbe appropriato usarli
- Tipi unione esaustivi con discriminante quando possibile

Per ogni problema trovato: indica il numero di riga, spiega perché
è un problema e proponi una correzione specifica. Non applicare
nulla, solo un report con le proposte.
```

Salvato come `~/.claude/commands/review-types.md`, diventa disponibile in tutte le tue sessioni. La prossima volta che lavori su un file TypeScript scrivi `/review-types` e ricevi una review con gli stessi criteri e lo stesso formato di sempre.

### Perché un file e non un prompt a mano

La velocità di digitazione è il guadagno meno interessante. Conta di più che tu e i colleghi usiate lo stesso prompt con gli stessi criteri di output, e che il prompt passi da Git: quando fra un mese aggiungi un criterio alla review dei tipi, il commit `feat: aggiungi controllo generics a review-types` dice a tutti quando e perché il comando è cambiato. E un comando non deve per forza essere di tre righe: può descrivere una sequenza di passi, leggere file, chiedere conferma a metà strada, come i comandi della sezione 8.3.

## 8.2 Scrivere il primo custom command

Il modo più diretto è partire da un prompt che usi già. Lo prendi così com'è, lo incolli in un file Markdown, aggiungi il frontmatter e hai finito.

### Crea la cartella e il file

Crea la cartella, se non esiste ancora, e il file. Il nome del file diventa il nome del comando, quindi per avere `/clean-imports`:

```bash
# comando personale
mkdir -p ~/.claude/commands
touch ~/.claude/commands/clean-imports.md

# oppure comando di progetto, dalla radice del repository
mkdir -p .claude/commands
touch .claude/commands/clean-imports.md
```

Apri il file e scrivi frontmatter e corpo:

```markdown
---
description: Riordina e pulisce gli import del file corrente
---

Leggi il file su cui stiamo lavorando.

Riordina gli import in tre gruppi separati da una riga vuota:
1. Librerie standard e node_modules (es. `react`, `lodash`, `fs`)
2. Alias del progetto (es. `@app/`, `@shared/`, `~/`)
3. Import relativi (es. `./Component`, `../utils`)

All'interno di ogni gruppo, ordina alfabeticamente.
Rimuovi gli import non utilizzati nel file.

Mostrami il diff prima di applicare qualsiasi modifica.
Aspetta la mia conferma.
```

### Prova il comando

Se Claude Code era già aperto quando hai creato il file, lancia `/reload-skills`: rilegge le cartelle delle skill e quelle dei comandi, quindi non serve uscire e rientrare. In alternativa chiudi la sessione e riaprila.

Digita `/` e comincia a scrivere `clean`. Nel menu compare `/clean-imports` con la descrizione del frontmatter. Selezionalo, premi `Invio`, e Claude esegue il prompt del file.

### Gli argomenti

Con `$ARGUMENTS` nel corpo il comando diventa parametrico. Se scrivi `/clean-imports src/services/auth.ts`, il testo `src/services/auth.ts` prende il posto di `$ARGUMENTS` prima che il prompt arrivi a Claude.

Un comando pensato per ricevere un argomento:

```markdown
---
description: Analizza il file specificato e proponi refactoring
argument-hint: path del file da analizzare
---

Leggi il file $ARGUMENTS.

Analizza il codice e proponi refactoring su questi assi:
- Funzioni troppo lunghe (>30 righe): suggerisci come spezzarle
- Duplicazione di logica: identifica pattern ripetuti
- Nomi non descrittivi: proponi nomi migliori per variabili e funzioni
- Complessità ciclomatica: segnala le funzioni con più di 4 branch

Per ogni proposta: mostra il codice attuale, il codice suggerito,
e la motivazione in una riga.
```

Salvato come `~/.claude/commands/refactor-file.md`, lo usi così:

```text
/refactor-file src/components/DataTable.tsx
```

Quando gli argomenti sono più di uno puoi prenderli per posizione. `$ARGUMENTS[0]` o la forma breve `$0` è il primo, `$1` il secondo, e così via: la numerazione parte da zero. Con un corpo che dice "Analizza il file $0 e concentrati su $1", il comando `/refactor-file src/api/client.ts duplicazione` mette il path in `$0` e la parola `duplicazione` in `$1`. Il frontmatter accetta anche un campo `arguments` per dare un nome agli argomenti posizionali; lo vedi nel capitolo 9.

Se nel corpo non c'è nessun segnaposto, gli argomenti non vanno persi: Claude Code li aggiunge in fondo al prompt come `ARGUMENTS: <valore>`.

### Contesto dinamico: `` !`comando` `` e `@file`

Con un prompt statico Claude spesso fa due o tre giri di tool prima del lavoro vero: `git status`, il diff, il file di specifica. Puoi fargli trovare quei dati già pronti.

Un comando shell scritto come `` !`comando` ``, all'inizio di una riga o dopo uno spazio, viene eseguito prima che il prompt arrivi a Claude, e il suo output prende il posto del segnaposto. Per più righe di shell c'è un blocco recintato che si apre con ` ```! `. Il timeout è quello del tool Bash, due minuti, quindi niente comandi lunghi.

Un riferimento `@percorso/del/file` nel corpo fa allegare quel file al prompt, come quando lo scrivi a mano nella sessione.

Un comando di progetto per la Photogallery che usa tutti e due:

```markdown
---
description: Confronta il diff corrente con DESIGN.md
allowed-tools: Bash(git diff *)
---

## Modifiche in corso

!`git diff --stat`

## Specifica di riferimento

@docs/DESIGN.md

Confronta le modifiche con la specifica: tipi di colonna e nullabilità,
forma delle risposte, regole di validazione, status code.
Elenca ogni scostamento con file e riga. Se non ne trovi, dillo.
```

Il repository companion della Photogallery ha un comando simile, `.claude/commands/spec-check.md`, che chiede a Claude di lanciare lui `git diff` e leggere `docs/DESIGN.md`; con l'iniezione quei passaggi spariscono.

::: {.callout .callout-warning}
[Attenzione]{.callout-title}

I comandi `` !`...` `` girano sulla tua macchina appena invochi il comando, prima che Claude veda qualcosa. Se installi comandi o skill scritti da altri, leggi il file prima di usarlo. Se vuoi spegnere del tutto l'iniezione, l'impostazione è `"disableSkillShellExecution": true`.
:::

## 8.3 Tre custom command da usare subito

Tre situazioni di tutti i giorni: test che falliscono, import in disordine, lavoro da portare in una PR. Salva i comandi in `~/.claude/commands/` e adattali al tuo stack.

### /fix-tests, diagnosi e proposta di fix per ogni test rotto

Il comando lancia la suite, e per ogni fallimento legge il codice, classifica la causa e propone un fix. Non applica niente: ti dà un elenco da leggere.

Salva come `~/.claude/commands/fix-tests.md`:

```markdown
---
description: Esegui i test, diagnostica i fallimenti e proponi fix
---

Esegui il comando di test del progetto. Guarda il package.json per
capire quale script usare (di solito `pnpm test`, `npm test` o
`pytest`). Se non riesci a determinarlo, chiedimi.

Per ogni test fallito:
1. Leggi il file di test e il file sotto test
2. Identifica la causa del fallimento tra queste categorie:
   - Cambio di API: la firma della funzione è cambiata
   - Bug nel codice: il codice non fa quello che il test si aspetta
   - Test obsoleto: il test verifica un comportamento rimosso intenzionalmente
   - Problema di ambiente: dipendenza mancante, variabile non impostata
3. Proponi il fix specifico con il diff delle modifiche necessarie

Non applicare nulla. Presentami un elenco strutturato con:
- Nome del test fallito
- Categoria del fallimento
- Causa identificata
- Fix proposto (diff)

Alla fine dimmi quanti test ci sono in totale, quanti passano e quanti falliscono.
```

Su un progetto Node con due test di autenticazione rotti, l'output somiglia a questo:

```text
> /fix-tests

pnpm test
  FAIL  src/auth.test.ts
    x login con credenziali errate → atteso 401, ricevuto 200
    x token scaduto → atteso 403, ricevuto 500

[1] auth.test.ts:42  Test obsoleto
    Il mock JWT usa ancora la scadenza fissa di prima del refactoring
    diff: -Date.now()  +Date.now() - 3600000
[2] auth.test.ts:87  Bug nel codice
    Il middleware non gestisce i token malformati
    diff: +if (!token) return res.status(403).json(...)

Totale: 24 test, 22 passano, 2 falliscono
```

Le categorie servono perché un test obsoleto e un bug nel codice si sistemano in direzioni opposte: nel primo caso cambi il test, nel secondo il codice. Se Claude deve dichiarare la categoria, la scelta resta a te e non gli lasci far passare il test nel modo più comodo.

### /clean-imports, la versione completa

È il comando della sezione 8.2. La versione che tengo in `~/.claude/commands/` ha in più un blocco di regole, prima della riga sul diff:

```markdown
Regole:
- Ordine alfabetico all'interno di ogni gruppo
- Rimuovi gli import non usati nel file (verifica prima di rimuovere)
- Mantieni i commenti già presenti vicino agli import a cui si riferiscono
- Non toccare nulla nel resto del file
```

Se il progetto ha già un linter che ordina gli import (ESLint con `import/order`, Biome), il comando è superfluo: lancia il linter.

### /spawn-pr, una PR dal lavoro corrente

Il comando raccoglie i commit del branch, scrive titolo e descrizione e apre la pull request su GitHub, ma solo dopo la tua conferma. Usa l'iniezione per partire già con i dati in mano.

Salva come `~/.claude/commands/spawn-pr.md`:

````markdown
---
description: Crea una PR GitHub con titolo e descrizione dal lavoro corrente
disable-model-invocation: true
allowed-tools: Bash(git log *) Bash(git diff *) Bash(git branch *)
---

## Contesto

- Branch: !`git branch --show-current`
- Commit da includere: !`git log --oneline origin/HEAD..HEAD`
- File toccati: !`git diff --stat origin/HEAD...HEAD`

## Cosa fare

Genera:
- Titolo PR: massimo 50 caratteri, tempo presente, senza punto finale.
  Esempi: "Add user authentication", "Fix null check in DataTable"
- Descrizione PR in Markdown con queste sezioni:
  - `## Cambiamenti`: cosa è stato modificato e come
  - `## Motivazione`: perché questi cambiamenti erano necessari
  - `## Test`: cosa è stato testato e come verificare il funzionamento

Mostrami titolo e descrizione proposti e aspetta la mia approvazione.

Solo dopo approvazione:
1. Esegui `git push origin HEAD`
2. Esegui `gh pr create --title "<titolo>" --body "<descrizione>"`
3. Mostrami l'URL della PR aperta

Se `gh` non è installato, avvisami invece di procedere.
````

Nota cosa ho messo in `allowed-tools`: solo i comandi Git che leggono. Il `git push` e il `gh pr create` restano fuori, quindi passano dai permessi normali della sessione e, se lavori in modalità Manual, ti vengono chiesti uno per uno. Il permesso concesso da `allowed-tools` vale solo finché il comando è attivo e si azzera al tuo messaggio successivo.

::: {.callout .callout-warning}
[Attenzione]{.callout-title}

Dato che comandi e skill sono la stessa cosa, Claude può decidere da solo di usare un comando quando la descrizione corrisponde a quello che sta facendo. Per un report va benissimo. Per un comando che pusha, apre PR o fa il deploy no: con `disable-model-invocation: true` nel frontmatter il comando parte solo quando lo scrivi tu. Mettilo su tutto quello che ha effetti fuori dal tuo editor.
:::

## 8.4 Il plugin Superpowers

I comandi visti finora li scrivi tu. Superpowers è un plugin open source di Jesse Vincent (`obra/superpowers` su GitHub) che porta in Claude Code un metodo di lavoro già codificato, scritto e rifinito da qualcun altro. Un plugin è un pacchetto che può contenere skill, agent, hook e server MCP; lo installi una volta e hai tutto insieme.

### Cosa contiene

La voce di Superpowers nel marketplace ufficiale lo descrive come brainstorming, sviluppo guidato da subagent con code review integrata, debugging sistematico, TDD red/green, e istruzioni per scrivere e testare skill nuove. In pratica sono soprattutto skill:

- brainstorming prima di implementare: domande, alternative, e solo dopo un design;
- sviluppo guidato da subagent: ogni task del piano va a un subagent, con una code review prima del task successivo;
- debugging sistematico: riprodurre, isolare, formulare un'ipotesi, verificarla, invece di provare fix a caso;
- TDD red/green: prima un test che fallisce, poi il codice minimo che lo fa passare;
- scrittura di skill: come progettarne una e come verificare che funzioni.

<!-- VERIFY: nomi esatti delle skill nel plugin (es. brainstorming, systematic-debugging, test-driven-development, subagent-driven-development, writing-skills, writing-plans) e se esistono ancora slash command dedicati; FACTS conferma solo la descrizione del marketplace -->

Queste skill non le devi invocare tu: Claude le carica da solo quando la situazione corrisponde alla loro descrizione. Chiedi una feature nuova e parte il brainstorming; segnali un bug e parte il debugging sistematico. Se vuoi richiamarne una a mano, le skill di un plugin hanno il prefisso del plugin, nella forma `/superpowers:<nome-skill>`.

Nella Photogallery (Parte VI) ritrovi lo stesso ritmo: specifica, task, esecuzione a wave con review fra un task e l'altro. Superpowers non è obbligatorio per seguire il libro, ma ti ci abitua.

### Installarlo

Superpowers è nel marketplace ufficiale di Anthropic, `claude-plugins-official`, che Claude Code aggiunge da solo alla prima sessione interattiva. Dal prompt:

```text
/plugin install superpowers@claude-plugins-official
```

Un plugin si installa in uno di tre scope: utente (tutti i tuoi progetti), progetto (salvato nella configurazione del repository, quindi condiviso con il team) o locale (solo tu, solo in questo progetto). Per provarlo va bene utente.

In alternativa puoi passare dal marketplace dell'autore:

```text
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```

Se preferisci i menu, `/plugin` apre il gestore con le schede Discover, Installed e Marketplaces: cerchi "superpowers" in Discover e installi da lì.

Dopo l'installazione lancia:

```text
/reload-plugins
```

Senza il reload la sessione corrente non vede ancora le skill nuove. Per verificare, `/plugin list` mostra i plugin installati e `/skills` elenca le skill disponibili: quelle di Superpowers compaiono con il loro prefisso.

<!-- TODO screenshot: output di /skills dopo l'installazione di Superpowers, con le skill del plugin elencate -->

### Quanto costa in contesto

Nome e descrizione di ogni skill restano nella finestra di contesto anche quando non le usi, perché è così che Claude sa quando tirarle fuori. Il gestore `/plugin` mostra una stima del costo prima di installare, e nel capitolo 15 vedi `/context` e `/skill-doctor` per capire quali skill valgono lo spazio che occupano. Con Superpowers il conto torna; con dieci plugin installati per curiosità, no.

Come è fatto un plugin dentro (il manifest `.claude-plugin/plugin.json`, le cartelle `skills/`, `agents/`, `hooks/`) lo vedi nel capitolo 14, dove ne costruisci uno tuo.

## 8.5 Il pattern del commit atomico con /commit

Quando lavori con un agent che modifica una dozzina di file in pochi minuti, la storia Git si sporca in fretta. Alla fine della sessione ti ritrovi con un unico commit enorme, o con quattro commit chiamati "wip". Un comando `/commit` scritto bene risolve il problema, e una volta che ci hai preso l'abitudine non torni indietro.

### Il comando

Un `/commit` personale, che chiede sempre conferma:

````markdown
---
description: Proponi un commit atomico con messaggio Conventional Commits
disable-model-invocation: true
allowed-tools: Bash(git status *) Bash(git diff *)
---

## Stato del repository

!`git status --short`

## Modifiche in staging

!`git diff --cached`

## Cosa fare

1. Se non c'è nulla in staging, dimmelo e fermati.
2. Se le modifiche in staging contengono più di un cambiamento logico,
   dimmelo e proponi come dividerle. Non committare.
3. Scegli il tipo: feat, fix, refactor, test, docs, chore, perf.
4. Scrivi il messaggio in formato Conventional Commits: titolo
   all'imperativo, senza punto finale, sotto i 72 caratteri; corpo
   facoltativo con il perché della modifica.
5. Mostrami file inclusi e messaggio proposto, e aspetta la mia conferma.
6. Solo dopo la conferma esegui `git commit`. Non fare push.
````

Salvalo come `~/.claude/commands/commit.md`. Il comando lavora su quello che hai in staging, e la scelta è voluta: decidi tu cosa fa parte del commit, Claude scrive il messaggio e ti avvisa se hai messo insieme due cose diverse.

Il repository companion della Photogallery ha una versione di progetto in `.claude/commands/commit.md`: sceglie anche lo scope dai file toccati (`api`, `backend`, `frontend`, `filament`, `pipeline`, `db`), cita le sezioni di `DESIGN.md` nel corpo e committa senza chiedere conferma, perché lì il commit arriva alla fine di un task già rivisto.

Se non vuoi scriverlo tu, il marketplace ufficiale ha un plugin `commit-commands` (`/plugin install commit-commands@claude-plugins-official`) con comandi già pronti per commit, commit più push più PR e pulizia dei branch locali il cui remoto è stato cancellato.

<!-- VERIFY: nomi dei comandi del plugin commit-commands (/commit, /commit-push-pr, /clean_gone) e come si invocano dopo l'installazione; la prima edizione li attribuiva a Superpowers, FACTS non lo conferma -->

### Cosa succede quando lo lanci

Con tre file in staging dopo una correzione all'autenticazione, la risposta somiglia a questa:

```text
> /commit

File in staging (3):
  M  src/auth/middleware.ts     (+12 / -3)
  M  src/auth/auth.test.ts      (+18 / -5)
  M  src/auth/token.service.ts  (+4 / -1)

Messaggio proposto:
  fix: handle expired and malformed tokens

  - middleware returns 403 for malformed tokens
  - JWT mock resets expiry correctly in tests
  - TokenService handles null/undefined edge cases

Confermi, vuoi modificarlo o annullo?
```

Il formato Conventional Commits mette un prefisso (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`) davanti a un titolo breve, seguito da un corpo facoltativo come quello qui sopra.

### Perché i commit atomici

Un commit atomico contiene un solo cambiamento logico, che si descrive in una frase e sta in piedi da solo. Senza questa disciplina, una giornata con un agent produce un log così:

```text
a1b2c3d WIP
d4e5f6a ancora wip
g7h8i9j funziona finalmente
j0k1l2m alcune cose
```

Con `/commit` dopo ogni pezzo di lavoro, la stessa giornata diventa:

```text
a3f1c2d feat: add format_values helper for stats output
b7e4d8a feat: add write_markdown_report function
c2b9f1e feat: implement analyze-column python script
d8e3a7c test: add tests for analyze-column
e4c1b9f docs: add slash command analyze with description
```

La differenza ha effetti pratici. `git bisect` funziona, perché ogni commit è uno stato coerente del progetto. `git revert e4c1b9f` toglie solo la documentazione del comando senza toccare test e implementazione. Chi fa la review legge un cambiamento alla volta invece di un diff da 400 righe mescolate. E quando un agent sbaglia strada, sai esattamente fino a dove tornare indietro.

### Leggi il messaggio prima di confermare

Il messaggio va letto ogni volta, anche quando ti fidi. Resta nella storia del progetto: `feat: update auth` fra sei mesi non ti dice niente, `feat: add refresh token rotation on expiry` ti dice cosa cercare quando il bug salta fuori in produzione. E controlli il tipo: se Claude propone `refactor:` mentre stai aggiungendo una funzionalità, correggi in `feat:`, altrimenti il log diventa meno utile a chi filtra i commit per tipo, persona o tool che genera il changelog.

### Quando non usarlo

Il comando funziona bene quando quello che hai in staging è già coerente. In alcuni casi conviene lavorare a mano. Se nello stesso file hai cambiato due feature, separale prima con `git add -p` e lancia `/commit` per ciascuna. Se il tuo team usa una convenzione diversa da Conventional Commits, cambia il comando (è un file, si modifica in un minuto) oppure scrivi il commit a mano. Merge commit, revert e cherry-pick hanno un contesto loro: meglio gestirli a mano.

### Una giornata tipo

Con `/commit` e `/spawn-pr` la sessione prende un ritmo regolare. Lavori con Claude sulla feature X, che tocca quattro o cinque file legati fra loro; metti in staging, lanci `/commit`, leggi, confermi. Passi alla feature Y e ripeti. Quando il branch è pronto lanci `/spawn-pr`: push, PR con titolo e descrizione, URL in risposta. Tre settimane dopo, `git log --oneline` ti rimette in pari prima ancora di aprire un file.

::: {.callout .callout-prompt}
[Prompt riusabile]{.callout-title}

Quando hai un workflow ricorrente e non sai da dove partire, fatti scrivere il comando da Claude:

```text
Crea un custom command in .claude/commands/<nome>.md per questo
scenario ricorrente: <descrivi il workflow che fai spesso a mano>.

Il comando deve:
- Avere un frontmatter con description chiara (max 60 caratteri)
- Avere un argument-hint se accetta parametri
- Strutturare le istruzioni in passi numerati
- Specificare esplicitamente se mostrare diff prima di applicare
- Indicare se aspettare conferma o procedere automaticamente

Mostrami il file completo pronto da salvare.
```
:::

## Riepilogo

- Un custom command è un file `.md` in `~/.claude/commands/` (personale) o `.claude/commands/` (di progetto, da committare) che diventa `/nome-file`; le sottocartelle aggiungono un prefisso, come `/frontend:component`.
- I comandi sono stati assorbiti dalle skill: il formato `.claude/commands/` funziona ancora, `.claude/skills/<nome>/SKILL.md` è quello consigliato per il lavoro nuovo e vince in caso di nome uguale. Il capitolo 9 parte da qui.
- `$ARGUMENTS` riceve tutto il testo dopo il comando, `$0` e `$1` i singoli argomenti; `` !`comando` `` inietta l'output della shell prima che Claude legga il prompt, `@file` allega un file.
- Sui comandi con effetti esterni (push, PR, deploy) metti `disable-model-invocation: true`, e in `allowed-tools` solo i comandi che leggono.
- Superpowers si installa con `/plugin install superpowers@claude-plugins-official` seguito da `/reload-plugins`, e porta skill per brainstorming, sviluppo con subagent e review, debugging sistematico e TDD.
- Un `/commit` che lavora sullo staging, propone un messaggio Conventional Commits e aspetta la conferma ti dà una storia Git che puoi usare con `bisect` e `revert`.

## Esercizio

Tempo stimato: 25 minuti. Ti serve un qualsiasi repository Git con qualche modifica in sospeso.

<!-- VERIFY: la prima edizione indicava il branch di partenza "cap-07-commands", che nel repository companion della Photogallery non esiste (ci sono solo i branch book/cap-11 ... book/cap-15 e main). Confermare se va creato o se il riferimento va tolto. -->

1. Installa Superpowers con `/plugin install superpowers@claude-plugins-official`, lancia `/reload-plugins` e controlla con `/skills` che le sue skill compaiano.
2. Salva il comando `/commit` della sezione 8.5 in `~/.claude/commands/commit.md`. Fai una piccola modifica, mettila in staging, lancia `/commit` e leggi il messaggio proposto prima di confermare.
3. Trova un prompt che hai scritto almeno tre volte questa settimana, trasformalo in un file in `~/.claude/commands/` con `description` e, se serve, `argument-hint`, poi lancia `/reload-skills` e provalo.

Hai finito quando `git log -1` mostra un commit con un messaggio Conventional Commits creato da `/commit` e il tuo comando nuovo compare nel menu di `/` con la sua descrizione.
