# Appendice C. Prompt pronti

Questa appendice raccoglie i prompt riusabili del libro, ordinati per il lavoro da fare invece che per capitolo. La prima edizione aveva qui cinquanta prompt generici. Sono rimasti quelli che i capitoli usano davvero, nella versione corretta di questa edizione, con i nomi del progetto sostituiti da segnaposto tra parentesi quadre: `[FILE]`, `[OBIETTIVO]`, `[STACK]`. Sostituiscili con file, comandi e criteri di verifica reali del tuo progetto, e togli le righe che non ti servono. Ogni prompt indica il capitolo in cui è spiegato: se il risultato non è quello che ti aspetti, torna lì prima di riscriverlo.

Gli stessi prompt sono in testo semplice nel repository `github.com/hidran/claude-code-book-snippets`, comodi per il copia e incolla.

## C.1 Onboarding su un progetto o un dataset

### Primo contatto con un progetto

Quando apri un repository che non conosci, prima di chiedere qualunque modifica (capitolo 1).

```text
Leggi i file nel progetto e dimmi:
1. Quale stack tecnologico vedi
2. Quale parte sembra più recente e quale più vecchia
3. Quale file è il punto di ingresso (entry point)
4. Cosa NON capisci subito guardando i nomi delle cartelle
```

### Primo contatto con un dataset

Su qualsiasi CSV, prima di cominciare l'analisi vera (capitolo 4).

```text
Leggi @[FILE CSV]. Riporta:
1. Struttura: numero di righe, colonne con nome e tipo
2. Valori mancanti o anomali
3. Pattern temporali, se ci sono colonne data
4. Eventuali outlier evidenti nelle colonne numeriche

Poi dimmi 3 domande di business interessanti che si
possono fare su questi dati: non risponderne ancora,
voglio prima capire se sono quelle giuste.
```

## C.2 Pianificare con Plan Mode

Questo prompt, come i template della landing page (C.3) e della feature nuova (C.10), va lanciato in Plan Mode: ci entri con `Shift+Tab` fino a `plan mode on`, oppure con `/plan`. Claude legge ed esplora, ma non modifica niente finché non approvi il piano.

### Il piano prima del codice

Per qualsiasi task che va oltre qualche riga (capitolo 3).

```text
Pianifica come faresti [OBIETTIVO]. Non scrivere codice. Solo passi
numerati con: file da creare o modificare, motivo di ogni modifica,
dipendenze tra i passi, possibili punti critici.
```

## C.3 Feature e refactoring

### Aggiungere una feature

Il template di base per una richiesta che Claude deve eseguire senza indovinare (capitolo 3).

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

### Refactoring guidato

Quando vuoi cambiare la struttura del codice senza cambiarne il comportamento (capitolo 3).

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

### Una landing page dal brief al deploy

Per un sito vetrina nuovo, con Superpowers installato. Con le conferme manuali conta 60-90 minuti di sessione (capitolo 16).

```text
Voglio costruire una landing page per [NOME PRODOTTO].

Descrizione del prodotto:
[2-3 frasi che descrivono il prodotto e il suo valore principale]

Audience:
[chi sono gli utenti target]

Call to action principale:
[es. "Inizia gratis", "Prenota una demo", "Scarica l'app"]

Sezioni da includere:
- Hero con titolo, sottotitolo, CTA e immagine/video
- Features (4-6 feature principali con icone)
- [sezione opzionale, es. "How it works" con 3 passi]
- Social proof (testimonial o loghi clienti)
- Pricing (N piani, con toggle mensile/annuale se presente)
- FAQ (6-8 domande più frequenti)
- Footer con CTA finale

Stile:
[es. "dark mode, accent viola, tipografia bold, tech forward"
 oppure "light, colori caldi, friendly, startup consumer"]

Stack:
React + Vite + Tailwind CSS (ultima versione)

Deploy target:
Firebase Hosting

Workflow:
1. Usa visual companion per mostrarmi 3 varianti di layout
2. Dopo l'approvazione del layout, genera le specifiche in docs/SPEC.md
3. Crea il piano in docs/PLAN.md con task atomici e criteri di done
4. Esegui un task alla volta, aspetta la mia conferma
5. Code review dopo tutti i componenti, prima del deploy
6. Build + firebase deploy --only hosting

Inizia dal Plan Mode. Non scrivere codice fino all'approvazione delle spec.
```

## C.4 Debugging

### Un test che fallisce

Dai a Claude il nome del test, l'errore e i file da leggere, e tieni per te la decisione sul fix (capitolo 3).

```text
Il test "[NOME TEST]" in [FILE DI TEST]
fallisce con [ERRORE].
Leggi il test e la funzione [FUNZIONE] in [FILE]. Trova la
causa e proponimi un fix, ma non applicarlo finché non ho approvato.
```

### Un bug intermittente

Per i problemi difficili, dove serve più ragionamento per un solo turno: `ultrathink` vale solo per quel messaggio (capitolo 3).

```text
ultrathink. [DESCRIZIONE DEL SINTOMO, es. Il test di integrazione degli
ordini fallisce una volta su cinque, solo in CI]. Leggi [FILE E CARTELLE]
e proponimi le tre cause più probabili, in ordine, con il modo per
verificare ciascuna.
```

## C.5 Test

### Una funzione con i suoi test

Il criterio di verifica dentro il prompt: Claude sa quando ha finito perché glielo hai detto tu (capitolo 3).

```text
Scrivi una funzione [FIRMA DELLA FUNZIONE] con [TIPI DI INPUT E OUTPUT].
Scrivi anche i test per questi casi: [CASI, es. file vuoto, file con
solo l'header, righe con campi mancanti, righe valide]. I test devono
passare con [COMANDO DEI TEST].
```

## C.6 Analisi dati e report

### I pattern che contano

Per passare dalle statistiche descrittive alle conclusioni utili a chi decide (capitolo 4).

```text
@[FILE CSV] guarda il CSV. Quali sono i 3 pattern
più importanti per [CHI LEGGE, es. chi gestisce un SaaS]? Spiegamelo in
italiano semplice. Usa i numeri solo quando sono il punto
principale, non come riempitivo.
```

### Report Excel con pivot e formule

Un file Excel formattato, con i totali in formula e i parametri da riga di comando (capitolo 5).

```text
Leggi [FILE CSV]. Scrivi uno script Python tools/genera_excel.py che genera
[FILE XLSX] con:

1. Sheet "Dati": tutti i dati del CSV come tabella filtrabile (auto_filter),
   intestazione con sfondo blu scuro (#1F4E78) e testo bianco in grassetto,
   larghezza colonne adattata al contenuto, freeze sulla prima riga,
   zebra striping sulle righe pari (#F2F2F2).

2. Sheet "Riepilogo": tabella pivot con [CAMPO RIGHE] come righe e
   [CAMPO COLONNE] come colonne, valori = somma di [METRICA].
   Riga dei totali con formule SUM, non valori hardcoded.

3. Sheet "Grafici": un line chart per [METRICA TEMPORALE] nel tempo
   suddiviso per [SEGMENTAZIONE], un pie chart per la distribuzione
   totale di [METRICA] per [SEGMENTAZIONE].

Usa openpyxl. Aggiungi argparse con --input, --output, --region (opzionale).
Se --output non specificato, usa report_YYYY-MM.xlsx con timestamp automatico.
Installa le dipendenze e aggiorna requirements.txt.
```

### Mini dashboard web

Una webapp Flask con Chart.js su qualsiasi CSV tabellare (capitolo 6).

```text
A partire da [FILE CSV], crea una mini dashboard Flask:
- app.py con route GET / e GET /api/data
- templates/index.html con Chart.js CDN e tre canvas:
  [GRAFICO 1] (tipo: [line|bar|pie]),
  [GRAFICO 2] (tipo: [line|bar|pie]),
  [GRAFICO 3] (tipo: [line|bar|pie])
- static/style.css con layout grid 2 colonne, font Inter,
  card bianche su sfondo grigio chiaro, responsive mobile
- Bottone "Aggiorna dati" che ri-fetcha /api/data e chiama
  chart.update() senza reload
Avvio: python app.py, server su http://localhost:5000
```

## C.7 CLAUDE.md, regole e memoria

Per la prima bozza di `CLAUDE.md` su un progetto esistente c'è `/init` (capitolo 7). I prompt qui sotto servono dopo.

### Aggiungere una regola

La scorciatoia `#` non esiste più: lo chiedi a Claude, oppure apri il file con `/memory` (capitolo 7).

```text
aggiungi a CLAUDE.md, nella sezione [SEZIONE, es. NON fare mai]: [REGOLA]
```

### Revisione periodica di CLAUDE.md

Ogni due o tre mesi, o dopo un refactoring importante (capitolo 7).

```text
Leggi il file CLAUDE.md in questo progetto e dimmi:
1. Ci sono informazioni duplicate con quello che puoi già dedurre dal codice?
2. Ci sono sezioni troppo verbose che potrebbero essere condensate?
3. Mancano informazioni importanti che ti hanno già causato errori
   o che ti avrebbero aiutato in questa sessione?
4. Il file ha sezioni obsolete rispetto allo stack attuale del progetto?
5. Ci sono istruzioni che valgono solo per una parte del codice e che
   starebbero meglio in .claude/rules/ con il campo paths?

Proponi una versione revisionata con al massimo 200 righe.
```

## C.8 Skill, custom command e agent

### Un custom command per un workflow ricorrente

Quando ripeti la stessa sequenza a mano e non sai da dove partire (capitolo 8).

```text
Crea un custom command in .claude/commands/[NOME].md per questo
scenario ricorrente: [descrivi il workflow che fai spesso a mano].

Il comando deve:
- Avere un frontmatter con description chiara (max 60 caratteri)
- Avere un argument-hint se accetta parametri
- Strutturare le istruzioni in passi numerati
- Specificare esplicitamente se mostrare diff prima di applicare
- Indicare se aspettare conferma o procedere automaticamente

Mostrami il file completo pronto da salvare.
```

### Lo schizzo di una skill

Da dare a Claude direttamente, o per chiarirti le idee prima di usare lo skill-creator (capitolo 9).

```text
Voglio creare una skill per Claude Code che si chiama [NOME-SKILL].

Deve attivarsi quando l'utente chiede [DESCRIVI IL TRIGGER IN PAROLE NATURALI].
Il workflow prevede questi passi:
1. [PASSO 1]
2. [PASSO 2]
3. [PASSO 3]

Ha bisogno di [script Python / references / templates]? [SÌ/NO, specifica]

Crea la struttura di cartelle in .claude/skills/[NOME-SKILL]/ (oppure in
~/.claude/skills/[NOME-SKILL]/ se serve in tutti i miei progetti),
scrivi SKILL.md con un frontmatter ottimizzato per il trigger automatico,
e aggiungi eventuali file di supporto nelle sottocartelle appropriate.
```

### Creare un agent

Il wizard di `/agents` non c'è più: descrivi l'agent e Claude scrive il file in `.claude/agents/` (capitolo 10).

```text
Voglio un agent per [descrizione del compito].

Persona: [es. senior TypeScript code reviewer, data scientist SaaS]
Input: [cosa riceve l'agent, es. un file controller, un dataset CSV]
Formato del rapporto: [es. problemi ordinati per gravità, con file:riga]
Tool consentiti: [es. Read, Grep, solo lettura]
Modello: [sonnet / opus / haiku / inherit]
Scope: [progetto / utente]

Crea l'agent in .claude/agents/ (o in ~/.claude/agents/ se è di livello utente).
```

## C.9 MCP e contesto

Permessi, sandbox, hook e plugin (capitoli 11, 12 e 14) si configurano con file e comandi, non con prompt: i capitoli li accompagnano con i prompt di prova che verificano ogni configurazione. Qui restano i due prompt della Parte IV che uso più spesso.

### Lavorare su GitHub da un server MCP

Con il server GitHub remoto configurato, senza uscire dalla sessione (capitolo 13).

```text
elenca le ultime 5 issue aperte del repository [UTENTE]/[REPOSITORY], solo numero e titolo
```

### Compattare senza perdere il filo

`/compact` accetta istruzioni su cosa conservare nel riassunto (capitoli 4, 15 e 19).

```text
/compact Mantieni [COSA CONSERVARE, es. la struttura del progetto, le decisioni prese e i test che falliscono]
```

## C.10 Specifiche e Spec Driven Development

### Descrivere il problema prima dello stack

Il primo prompt di un progetto nuovo dice cosa deve fare l'applicazione e lascia aperta la scelta delle tecnologie (capitolo 17).

```text
Voglio costruire [TIPO DI APPLICAZIONE].
Gli utenti devono poter:
- [FUNZIONALITÀ 1, con i vincoli che conosci, es. formati e dimensioni]
- [FUNZIONALITÀ 2]
- [FUNZIONALITÀ 3]

[REQUISITI DI CONTORNO, es. pannello di amministrazione, ambienti]

Non scegliere ancora lo stack. Prima dimmi quali stack
consiglieresti per questo tipo di progetto, con i tradeoff
di ognuno. Voglio tecnologie standard e mature, niente hype.
```

### Il brief tecnico

Da iterare due o tre volte prima di considerarlo pronto (capitolo 17).

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

### Requisiti, design e task

Dalla spec ai tre file dello Spec Driven Development, con gli ID che li collegano (capitolo 18).

```text
Leggi SPEC.md[, ALTRI DOCUMENTI DI RIFINITURA].

Genera tre file nella cartella docs/:

1. docs/REQUIREMENTS.md, cosa costruire
   - Vision e cosa il prodotto NON è
   - Personas ([RUOLI])
   - User stories per persona, con ID (US-01, US-02, ...)
   - Criteri di accettazione testabili, con ID (AC-F1-1, ...)
   - Vincoli (formati file, dimensioni, naming)
   - Non-functional requirements con numeri (performance, sicurezza, scalabilità)
   - Out of scope esplicito
   Niente decisioni tecniche, niente schemi, niente codice.

2. docs/DESIGN.md, come costruirlo
   - Stack con versioni precise
   - Struttura delle cartelle di [CARTELLE DEL PROGETTO]
   - Schema del database: tabelle, colonne, tipi, vincoli, indici, ON DELETE
   - Contratti API: verbo, URL, body, shape della risposta, status code
   - Interfacce dei servizi ([SERVIZI]) per la DIP
   - Autenticazione, gestione degli errori, [ALTRE PIPELINE]

3. docs/TASKS.md, la lista di lavoro
   - Task atomici, al massimo 30 minuti ciascuno, raggruppati in fasi
   - Per ogni task: ID (T001, ...), stato [ ], owner (backend-dev,
     frontend-dev, code-reviewer), Depends on, Parallel with, Reads
     (sezioni da leggere), Acceptance (definition of done), Commit
   - Riferimenti alle sezioni di DESIGN.md e agli ID di REQUIREMENTS.md

Usa gli ID per la tracciabilità nelle due direzioni: ogni criterio di
accettazione deve comparire in almeno un task.
```

### Una feature nuova su un progetto con le spec

Quando requisiti, design e task sono già consolidati: Claude aggiorna i tre documenti prima di toccare il codice (capitolo 21).

```text
Ho un progetto con docs/REQUIREMENTS.md, docs/DESIGN.md e docs/TASKS.md
già consolidati. Voglio aggiungere questa feature: [DESCRIZIONE FEATURE].

Esegui questi passi in ordine:

1. Leggi i tre file per capire lo stato attuale
2. Proponi la sezione da aggiungere a REQUIREMENTS.md
   (requisiti, vincoli e criteri di accettazione espliciti)
3. Proponi le modifiche a DESIGN.md (schema, endpoint, componenti)
4. Proponi i task da aggiungere a TASKS.md, con dipendenze, ID nuovi
   che non collidano con quelli esistenti e criteri di completamento
   verificabili
5. Prima di eseguire qualsiasi task, verifica se la feature richiede
   una migrazione DB e se nel codice c'è già qualcosa di simile
   che rischia di confliggere

Non iniziare l'esecuzione finché non ho approvato le modifiche ai tre file.
```

## C.11 Esecuzione a wave e /goal

### Avviare una fase

Volutamente semplice: il lavoro vero è già scritto in `docs/TASKS.md` (capitolo 19).

```text
Procedi con i task della Fase [N] secondo docs/TASKS.md.
Un commit per task, una pull request per fase.
Usa subagent dove i task sono indipendenti.
```

### Una condizione per /goal

Il valutatore giudica solo quello che Claude mostra nella conversazione: la condizione deve nominare controlli che Claude esegue davanti a te (capitolo 20).

```text
/goal i task da [ID INIZIALE] a [ID FINALE] hanno Status [x] in docs/TASKS.md (mostrami le righe Status con grep), "[COMANDO DEI TEST]" nella cartella [CARTELLA] esce con codice 0 e ogni task ha il suo commit sul branch del worktree (mostrami git log --oneline)
```

### Chiudere una wave

Il prompt fisso di fine wave (capitolo 21).

```text
Prima di marcare questa wave come completata, verifica:

1. Per ogni task marcato [x]: esiste nel repository il codice che
   corrisponde ai criteri di accettazione? Voglio il path del file,
   non "dovrebbe esistere".
2. Rileggendo i requisiti che questa wave dichiara di coprire,
   c'è qualcosa che i task non coprono?
3. Esiste almeno un test (automatico, o manuale documentato) che
   esercita ogni flusso utente citato in quei requisiti?

Se trovi gap, elencali. Non chiudere la wave finché la lista non è vuota
o le eccezioni non sono documentate esplicitamente come fuori scope.
```

## C.12 Review e QA

### La review integrata

`/code-review` (alias `/review`) gira come subagent in background. Senza target guarda i commit non pushati più le modifiche non committate; senza livello riusa l'ultimo che hai scritto (capitolo 22).

```text
/code-review high main...[BRANCH]
/code-review [NUMERO PR]
/code-review --fix main...[BRANCH]
/code-review --comment [NUMERO PR]
/code-review ultra [NOTA PER I REVISORI]
```

### Wave review con quattro agent

A fine fase, più reviewer specializzati in parallelo e un report unico (capitolo 19).

```text
Wave review della Fase [N], [NOME FASE] (task [ID INIZIALE]-[ID FINALE]).
Lancia quattro subagent in parallelo, in sola lettura (nessuna modifica
ai file), modello sonnet:

1. security-auditor
   Cerca: auth bypass, input validation mancante, esposizione di dati
   non autorizzata, segreti nel codice, CORS troppo permissivo.

2. performance-reviewer
   Cerca: query N+1, eager loading mancante, indici DB assenti sulle
   colonne filtrate, operazioni sincrone che dovrebbero essere job.

3. api-consistency
   Cerca: error envelope non uniforme, status code sbagliati,
   [PATTERN DEL PROGETTO NON RISPETTATI], naming non uniforme.

4. test-coverage
   Cerca: percorsi critici senza test, edge case mancanti, test che
   bypassano la policy, N+1 nei test, factory incomplete.

Per ogni finding: file, riga, severità (CRITICAL / HIGH / MAJOR /
MEDIUM / LOW), fix proposto. Aggrega i quattro report in un documento
unico, in ordine di priorità.
```

### La checklist QA pre-deploy

Per partire da una lista sensata invece che dalla memoria (capitolo 22).

```text
Sei un QA engineer senior. Il mio progetto è [descrivi stack e tipo di app].
Genera una checklist pre-deploy strutturata per categoria:
Funzionale, Performance, Security, Data Integrity, Observability.
Per ogni voce specifica: cosa verificare, come verificarlo (comando o azione),
criterio di successo. Formato: tabella Markdown.
```

### Review multi-LLM

Da incollare identico in Claude, Gemini, Codex e Kimi, poi confronti i risultati (capitolo 22).

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

## C.13 Deploy

Il deploy della landing page su Firebase è già dentro il template della sezione C.3. Per AWS il punto di partenza è il template CloudFormation.

### Un template CloudFormation

La versione generica del template della Photogallery: adatta nome, stack, database e regione (capitolo 23).

```text
Genera un template CloudFormation YAML per un'applicazione [NOME] con:
- Stack: [backend in Laravel/Node.js/Python] + [frontend in React/Vue/Angular]
- Database: [MariaDB/MySQL/PostgreSQL] gestito su RDS
- Regione AWS: [eu-west-1/us-east-1/...]
- Deployment target: ECS Fargate per il backend, S3 + CloudFront per il frontend
- Ambienti: staging e production tramite Parameters

Il template deve includere:
- VPC con 2 subnet pubbliche (ALB) e 2 private (ECS, RDS) in 2 AZ
- Security group con least privilege (ECS verso RDS solo sulla porta del DB)
- IAM execution role per ECS (ECR, Secrets Manager, log) e task role per l'app
- ECR repository per l'immagine Docker
- CloudWatch log group per ogni container
- Outputs: ALBDnsName, CloudFrontDomainName, EcrRepositoryUri

Output: infra/cloudformation.yaml. Aggiungi commenti inline per le sezioni
non ovvie (es. perché quel DependsOn, perché quella policy IAM).
```

