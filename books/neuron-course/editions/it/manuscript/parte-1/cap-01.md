# Capitolo 1 — Che cosa significa davvero "agentico"

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

Questo capitolo è concettuale e non ha codice a sé stante, ma il repository di accompagnamento [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) contiene le versioni eseguibili di tutto ciò che il libro costruisce.
:::

## 1.1 LLM, chatbot, workflow, agent: la scala dell'autonomia

Nel 2023 tutto era un "chatbot". Nel 2025 tutto è un "agent". La parola è stata tirata così tanto che ormai significa "software che chiama un LLM", il che è inutile come categoria di progetto. Prima di scrivere una riga di PHP ci serve una definizione abbastanza affilata da poterci prendere decisioni architetturali.

La distinzione utile non è *che cosa fa il software*. È **chi decide che cosa succede dopo**.

Quella domanda produce una scala a quattro pioli, e alla fine di questa sezione dovresti saper collocare su di essa qualunque funzionalità AI ti venga chiesto di costruire — e spiegare a un cliente perché il piolo conta più del modello.

### I quattro pioli

**Piolo 1 — La chiamata nuda all'LLM.**
Mandi testo, ricevi testo. Il tuo codice decide tutto: cosa mandare, quando mandarlo, cosa fare della risposta. Il modello non ha alcun controllo sul flusso del programma.

```
Il tuo codice → prompt → modello → testo → il tuo codice
```

Esempio: "riassumi questo ticket di assistenza in una frase". C'è un input, un output, un percorso. Il novanta per cento delle funzionalità AI presenti nei prodotti reali è questo, e va benissimo così.

**Piolo 2 — Il chatbot.**
Come il piolo 1, più lo stato della conversazione. Il modello continua a non poter fare nulla se non produrre testo, ma ora il testo dipende da una cronologia che cresce. Il flusso resta interamente controllato dal tuo codice: ricevi il messaggio, lo appendi alla cronologia, chiami il modello, restituisci la risposta.

L'unico problema ingegneristico nuovo è la gestione della memoria: cosa tieni, cosa scarti, cosa succede quando la cronologia supera la context window del modello.

**Piolo 3 — Il workflow AI.**
Definisci una sequenza fissa di passi e il modello ne riempie alcuni. Estrai entità → cercale nel database → genera una risposta → classifica il sentiment. *Il grafo lo scrivi tu*; il modello è un componente al suo interno, non il guidatore.

È qui che vive gran parte del valore in produzione, ed è profondamente sottovalutato perché non è affascinante. Una pipeline deterministica a cinque nodi con tre chiamate all'LLM è più affidabile, più economica e più facile da debuggare di un agent autonomo, e risolve la maggior parte dei problemi aziendali.

**Piolo 4 — L'agent.**
Ecco la vera linea di demarcazione: **il modello decide quale azione compiere dopo, e il ciclo continua finché il modello decide di aver finito.**

Dai al modello un obiettivo e un insieme di capacità (i tool). La sequenza non la scrivi tu. Il modello sceglie il tool A, vede il risultato, decide che ora gli serve il tool C, vede quel risultato, decide di averne abbastanza e scrive la risposta finale. Il flusso di controllo è emergente, non scritto.

```
Obiettivo → modello → "chiama il tool A" → esegui → risultato → modello
          → "chiama il tool C" → esegui → risultato → modello → risposta finale
```

Quel ciclo è tutta l'idea. Tutto il resto in questo libro — memoria, RAG, workflow, approvazione umana, observability — esiste per rendere quel ciclo sostenibile in produzione.

### Perché il piolo conta più del modello

Due team costruiscono la stessa funzionalità. Il team A usa una chiamata di piolo 1 con un modello di frontiera. Il team B usa un agent di piolo 4 con un modello di fascia media.

Il team A può testare la propria funzionalità con test unitari, sa esattamente quanto costa per chiamata e, quando si comporta male, legge un prompt.

Il team B non può prevedere il costo per richiesta — l'agent potrebbe chiamare sei tool o uno — non può testare il flusso in modo deterministico, e quando si comporta male gli serve un visualizzatore di trace per scoprire perché al quarto passo il modello ha scelto il tool sbagliato.

Il team B ha più potere. Ha anche un problema operativo molto più difficile. Scegliere il piolo 4 è un impegno verso observability, guardrail e valutazione. Sceglilo deliberatamente.

::: {.callout .callout-tip}
[In pratica]{.callout-title}

Immagina la scala come quattro linee orizzontali con un unico indicatore etichettato *chi sceglie il passo successivo*, che scivola da sinistra (il tuo codice) a destra (il modello) man mano che sali. È uno strumento di progettazione migliore di qualsiasi checklist, perché costringe a porsi l'unica domanda che conta prima di esserti impegnato su qualcosa.
:::

### Punti chiave

- La linea di demarcazione fra workflow e agent è **chi scrive il flusso di controllo**.
- Il piolo 4 compra flessibilità e ti costa determinismo, testabilità e spesa prevedibile.
- La maggior parte dei problemi aziendali si risolve al piolo 1 o al piolo 3. Ricorri al piolo 4 quando la sequenza dei passi non può davvero essere nota in anticipo.

## 1.2 Il ciclo dell'agent

Prima che NeuronAI esegua il ciclo di tool calling al posto tuo, vale la pena capirlo meccanicamente — perché sapere esattamente che cosa viene automatizzato è la differenza fra configurare un framework e sperare che funzioni.

### La scomoda verità sul tool calling

Un modello linguistico non può eseguire nulla. Non può chiamare un'API, leggere un file o interrogare il tuo database. Produce solo token.

Quello che succede davvero è una convenzione. Descrivi al modello le funzioni disponibili come dati strutturati. Il modello, invece di produrre prosa, produce un blocco strutturato che dice *"vorrei chiamare `get_weather` con `{latitude: 45.07, longitude: 7.69}`"*. Il tuo codice vede quel blocco, esegue la vera funzione PHP e rimanda il risultato al modello come nuovo messaggio. Il modello prosegue.

Il modello non tocca mai il tuo sistema. **A eseguire è sempre il tuo codice.** Vale la pena dirlo ad alta voce, perché è anche il modello di sicurezza: un agent può fare solo ciò per cui gli hai dato un tool.

### Il ciclo, in pseudocodice

```
messages = [system_prompt, user_message]
tools    = [tool_definitions...]

loop:
    response = llm.call(messages, tools)

    if response contains tool calls:
        for each tool_call in response:
            result = execute(tool_call.name, tool_call.arguments)
            messages.append(assistant_tool_call_message)
            messages.append(tool_result_message)
        continue loop
    else:
        return response.text
```

Quattro cose da notare, perché ognuna diventa un capitolo di questo libro:

**1. È un ciclo `while` senza uscita garantita.**
È il modello a decidere quando fermarsi. Se continua a decidere di chiamare tool, il ciclo continua. Per questo ogni framework serio ha una guardia sul numero massimo di esecuzioni, ed è per questo che NeuronAI solleva un'eccezione quando il limite viene superato. Lo copre la Sezione 5.9.

**2. Ogni iterazione rimanda l'intera conversazione.**
Il modello è stateless. La quinta iterazione manda il system prompt, il messaggio dell'utente e tutte e quattro le chiamate a tool precedenti con i loro risultati. Il consumo di token cresce in modo *quadratico* con la lunghezza del ciclo. Un agent in dieci passi non è dieci volte più costoso di uno in un passo: è considerevolmente peggio.

**3. I risultati dei tool sono solo testo.**
Qualunque cosa la tua funzione PHP restituisca viene convertita in stringa e passata al modello come contesto. Restituisci un blob JSON da 4 MB e hai bruciato la tua context window in una sola chiamata. Progettare l'output di un tool è progettare un prompt.

**4. La scelta del modello è guidata interamente da nomi e descrizioni.**
Non ha mai visto il tuo codice. Vede `get_transcription` — "Recupera la trascrizione di un video YouTube" — e uno schema di parametri. Quel testo è l'intera interfaccia. Il Capitolo 5 ci dedica molto spazio perché è qui che gli agent falliscono davvero.

### Esempio svolto: com'è fatta un'esecuzione con due tool

L'utente chiede: *"Che temperatura media c'è adesso fra Torino e Milano?"*

| Passo | Chi agisce | Cosa succede |
|---|---|---|
| 1 | Il tuo codice | Manda system prompt + domanda + 3 definizioni di tool |
| 2 | Modello | Restituisce due chiamate: `get_weather(45.07, 7.69)`, `get_weather(45.46, 9.19)` |
| 3 | Il tuo codice | Esegue entrambe, appende entrambi i risultati ai messaggi |
| 4 | Modello | Riceve 14.2 e 16.8, restituisce la chiamata `mean([14.2, 16.8])` |
| 5 | Il tuo codice | Esegue, appende il risultato 15.5 |
| 6 | Modello | Restituisce prosa: "La media è circa 15,5 °C." |

Tre andate e ritorno verso l'LLM. Tre esecuzioni di tool. Una domanda dell'utente. Interiorizza questa tabella: è la migliore risposta possibile a "perché la mia funzionalità AI è lenta e costosa?"

### Punti chiave

- Il modello richiede; il tuo codice esegue. Sempre.
- Il ciclo è illimitato per default e va protetto.
- Il contesto cresce a ogni iterazione; il costo cresce più che linearmente.
- Nomi e descrizioni dei tool sono l'unica interfaccia del modello verso il tuo sistema.

## 1.3 Anatomia di una chiamata al modello

Ogni componente che entra in una singola richiesta corrisponde a una manopola che girerai più avanti in `SystemPrompt`, `ChatHistory` o nella definizione di un tool. Sapere quale è quale risparmia moltissimi tentativi a caso.

### Che cosa c'è davvero sul filo

Togli l'SDK e ogni richiesta a un provider è fatta delle stesse quattro cose:

**1. Identificativo del modello.** Quali pesi rispondono alla domanda. La scelta del modello è una decisione di costo/qualità/latenza, non di gusto, e dovrebbe essere configurazione, mai una stringa hardcoded.

**2. L'array dei messaggi.** Un elenco ordinato di messaggi etichettati per ruolo:

- `system` — le istruzioni. Inviate a ogni singola richiesta. Non vengono ricordate: vengono ritrasmesse.
- `user` — quello che ha detto l'essere umano.
- `assistant` — quello che il modello ha detto in precedenza, incluse le richieste di chiamata a tool.
- `tool` — i risultati che il tuo codice ha rimandato indietro.

L'ordine è la conversazione. Dal lato del provider non esiste alcuna sessione. Vale la pena ripeterlo fino alla noia, perché quasi ogni confusione sulla "memoria" si dissolve appena accetti che il modello non ne ha.

**3. Definizioni dei tool.** Uno JSON Schema per tool: nome, descrizione, tipi dei parametri, quali sono obbligatori. Inviati a ogni richiesta, per intero. Cinquanta tool significa che lo schema di tutti e cinquanta viene ricaricato a ogni iterazione del ciclo. È per questo che NeuronAI include un `ToolSearchMiddleware` per cataloghi ampi.

**4. Parametri di generazione.** `max_tokens`, `temperature`, `top_p`, sequenze di stop. Per il lavoro agentico in genere vuoi una temperatura bassa: stai chiedendo una selezione corretta dei tool, non scrittura creativa.

### Il system prompt è il prodotto

Gli sviluppatori junior trattano il system prompt come un saluto. Quelli senior lo trattano come la specifica dell'intero sistema. Definisce:

- **Identità** — che cosa l'agent è e, soprattutto, che cosa non è
- **Procedura** — l'ordine delle operazioni che vuoi venga seguito
- **Vincoli** — che cosa non deve mai fare
- **Contratto di output** — formato, lingua, lunghezza

Una disciplina utile: scrivi il system prompt come se stessi facendo l'onboarding a un consulente competente, veloce, senza alcun contesto sulla tua azienda, che non farà domande di chiarimento se non gli viene detto e che dimentica tutto fra un compito e l'altro. Perché è esattamente quello che hai.

NeuronAI formalizza tre di quelle quattro sezioni nella classe `SystemPrompt` — `background`, `steps`, `output`. La incontriamo nella Sezione 3.5, ed esiste perché i prompt strutturati vengono seguiti in modo più affidabile di un muro di prosa e restano manutenibili quando ci mettono mano in sei.

### Leggere una risposta

La risposta ti dà il contenuto, un motivo di arresto e le statistiche d'uso. Il blocco d'uso — token in ingresso, token in uscita — è il tuo contatore dei costi. Loggalo dal primo giorno. Nel Capitolo 23 ci costruiamo sopra i budget, e non puoi mettere a budget ciò che non hai mai registrato.

### Punti chiave

- Ogni richiesta rimanda system prompt, cronologia completa e tutti gli schemi dei tool.
- Non esiste sessione lato server. La "memoria" è una questione lato client, e lo sarà sempre.
- Temperatura bassa per il lavoro agentico.
- Registra il consumo di token fin dal primo prototipo.

## 1.4 Context window, costo e latenza

Questa sezione è aritmetica. È anche la sezione con più probabilità di cambiare ciò che deciderai di costruire, perché è il conto sul tovagliolo che determina se un'architettura è sostenibile — e quasi nessuno lo fa in anticipo.

### Token

Un token è circa ¾ di una parola inglese. Italiano e spagnolo sono un po' più densi; il codice lo è ancora di più per via della punteggiatura. Cifre di lavoro utili:

- 1.000 token ≈ 750 parole ≈ 1,5 pagine
- Una tipica email di assistenza ≈ 300 token
- Un PDF di 20 pagine ≈ 12.000 token
- Una classe PHP di media grandezza ≈ 800 token

### La context window è un tetto rigido

Ogni modello ha un massimo: system prompt + cronologia completa + schemi dei tool + la risposta, tutto insieme. Superalo e la richiesta viene rifiutata del tutto — non troncata, rifiutata.

Questo genera il bug di produzione più comune nell'AI conversazionale: l'applicazione funziona benissimo per venti messaggi e poi inizia a restituire 400. La cronologia ha superato il tetto.

NeuronAI gestisce la cosa con il trimming automatico nel componente `ChatHistory`, e la documentazione dà un'indicazione precisa che vale la pena memorizzare: **configura la context window il 5–10 % sotto il limite reale del modello.** Il trimmer cerca un punto di taglio che perda meno contesto possibile, e per trovarne uno buono ha bisogno di margine. Un modello da 200K va configurato a 180–190K. Lo implementiamo nella Sezione 4.4.

### L'aritmetica dei costi che cambia i progetti

I provider prezzano separatamente token in ingresso e in uscita, e l'uscita è tipicamente parecchie volte più cara. Prendi una tariffa plausibile di fascia media: 3 dollari per milione di token in ingresso e 15 per milione in uscita.

Una singola chiamata semplice: 500 in ingresso, 300 in uscita ≈ 0,0060 $.

Ora la stessa funzionalità come agent in cinque passi. Poiché ogni iterazione rimanda tutto, i token in ingresso sono grosso modo cumulativi:

| Iterazione | Ingresso | Uscita |
|---|---|---|
| 1 | 1.500 | 200 |
| 2 | 2.400 | 200 |
| 3 | 3.300 | 250 |
| 4 | 4.300 | 250 |
| 5 | 5.400 | 400 |
| **Totale** | **16.900** | **1.300** |

≈ 0,0702 $. **Quasi dodici volte il costo della singola chiamata.**

A 10.000 richieste al giorno è la differenza fra 60 $ e 700 $ al giorno. È il numero che decide se costruisci al piolo 3 o al piolo 4, ed è il motivo per cui la Sezione 1.1 insisteva che il piolo conta più del modello.

### La latenza si accumula allo stesso modo

Una chiamata al modello richiede 1–4 secondi. Cinque iterazioni, più il tempo di esecuzione dei tool, e sei a 10–20 secondi di tempo reale. Nessun utente aspetta 20 secondi davanti a uno schermo vuoto. Questo non è un argomento accessorio a favore dello streaming (Capitolo 7): è il motivo per cui lo streaming esiste.

### Le tre leve

Quando l'aritmetica viene fuori sbagliata, hai esattamente tre mosse:

1. **Meno iterazioni** — prompt più affilati, tool progettati meglio, meno tool.
2. **Contesto più piccolo** — taglia la cronologia con decisione, restituisci risultati compatti dai tool, riassumi invece di accumulare.
3. **Modello più economico per passo** — un modello piccolo per instradamento e classificazione, uno grande solo per la sintesi finale. L'interfaccia dei provider di NeuronAI rende la cosa banale, ed è uno degli argomenti più forti a favore del framework.

### Esercizio

Prendi una funzionalità del tuo lavoro attuale. Stima i token per iterazione e il numero probabile di iterazioni. Calcola il costo giornaliero sul tuo traffico reale. Conserva il numero: informerà ogni decisione di progetto della Parte II.

### Punti chiave

- Il contesto è un tetto rigido; superarlo fa fallire la richiesta del tutto.
- Configura il trimmer il 5–10 % sotto il limite reale.
- Il costo di un agent cresce in modo super-lineare con la lunghezza del ciclo: modellalo prima di costruire.
- Tre leve: meno passi, contesto più piccolo, modello più economico per passo.

## 1.5 Non determinismo: il prompting non è programmazione

Stai per lavorare con un componente che restituisce output diversi a parità di input. Alcuni dei tuoi istinti ingegneristici sopravvivono; la maggior parte va corretta. Questa sezione fa ordine.

### La proprietà che rompe tutto

Esegui lo stesso codice due volte, ottieni lo stesso risultato. Quell'assunzione regge test unitari, debugging, code review e CI. Un LLM la viola. Stesso prompt, stesso modello, stessi parametri — output diverso.

Nemmeno a temperatura zero ottieni vero determinismo: non associatività in virgola mobile fra batch GPU, aggiornamenti del modello lato provider dietro un alias stabile, instradamento dipendente dal carico. In produzione, considera falsa l'affermazione "temperatura 0 significa deterministico".

### Che cosa si rompe

**I test unitari come li conosci.** `assertEquals($expected, $agent->chat($input))` non passerà mai due volte.

**La bisezione dei bug.** Non puoi riprodurre un fallimento rieseguendo con lo stesso input.

**La fiducia nel refactoring.** Una riformulazione "innocua" del prompt può spostare il comportamento in modo misurabile, e nulla nella tua toolchain ti avviserà.

**Il versioning semantico del tuo stesso sistema.** Il tuo codice non è cambiato e il comportamento sì. Il provider ha aggiornato un modello dietro un alias.

### Che cosa sopravvive, e che cosa sostituisce il resto

**Test di contratto invece di test sull'output.** Non asserire il testo. Asserisci la forma: ha restituito JSON valido conforme allo schema, ha chiamato il tool atteso, il campo obbligatorio è presente. Lo structured output (Capitolo 6) esiste in gran parte per rendere possibile questo.

**Componenti fake invece di chiamate di rete.** NeuronAI include provider e tool fake proprio perché la tua CI possa essere deterministica e gratuita. Il Capitolo 10 costruisce questa suite. In un progetto vero non è opzionale.

**Valutazioni invece di asserzioni.** Un insieme fisso di input rappresentativi, eseguiti contro proprietà attese, con un punteggio. Non passa/fallisce su una singola esecuzione: una percentuale di qualità tracciata nel tempo, come un benchmark di performance. NeuronAI ha un componente `Evals`; lo trattiamo nella Sezione 10.5.

**Tracing invece di debugging.** Non puoi entrare passo passo nel ragionamento del modello, ma puoi registrare ogni prompt, chiamata a tool, argomento e conteggio di token. È quello che fa Inspector, ed è il motivo per cui l'observability compare come pilastro di prima classe del framework anziché come aggiunta.

**Pinning invece di fiducia negli alias.** Usa versioni esplicite del modello in produzione — un identificativo datato e pienamente qualificato invece di un alias mobile — così che un aggiornamento del provider sia un deploy che scegli tu e non un incidente che scopri.

### Il cambio di mentalità

Smetti di pensare "funzione". Inizia a pensare "un collega junior competente ma incoerente". Non faresti test unitari su un collega. Gli daresti istruzioni chiare, limiteresti i suoi permessi, revisioneresti il suo lavoro e terresti traccia del suo tasso di errore. Ogni pattern architetturale di questo libro è una di quelle quattro cose.

### Punti chiave

- Presumi il non determinismo anche a temperatura 0.
- Testa contratti e forme, non stringhe.
- Componenti fake per la CI; eval per la qualità; trace per il debugging.
- Fissa le versioni dei modelli in produzione.

## 1.6 Il panorama: i framework Python e dove si colloca NeuronAI

Il vocabolario di questo campo è stato inventato in Python, e vale la pena impararlo perché articoli, talk e annunci di lavoro Python-centrici siano leggibili. Vale anche la pena essere onesti su ciò che PHP ha e non ha.

### Gli incumbent Python

**LangChain** — il primo arrivato e il più grande. Superficie di integrazione enorme, storicamente pesante di astrazione. Ha reso "chain" il vocabolario di default, e ha reso molte persone diffidenti verso l'over-abstraction.

**LangGraph** — la risposta di LangChain ai limiti delle catene lineari: un grafo esplicito di nodi e archi, con stato, cicli, checkpoint e interruzione human-in-the-loop. Se leggi una cosa sola dal mondo Python per capire il `Workflow` di NeuronAI, leggi la documentazione di LangGraph. La sovrapposizione concettuale è diretta e voluta.

**LlamaIndex** — nato come libreria RAG-first: ingestion, indicizzazione, retrieval. Il più forte sul lato dati.

**CrewAI / AutoGen** — orchestrazione multi-agente basata sui ruoli. "Un agent ricercatore, un agent scrittore, un agent critico." Demo eccellenti; la parte difficile in produzione è controllare i costi e le condizioni di arresto.

### Che cosa presumono tutti quanti

Presumono che i tuoi dati e la tua logica di business siano in Python, o raggiungibili via rete. Per una grossa fetta del commercio mondiale non è così. Sono in un'applicazione PHP con quindici anni di regole di dominio accumulate dentro.

L'aggiramento standard è un microservizio Python accanto all'app PHP. Significa un secondo runtime, una seconda pipeline di deploy, un secondo albero di dipendenze, un confine API che ora devi progettare, autenticare e versionare — e, cosa cruciale, l'agent vive dal lato sbagliato di quel confine rispetto alle regole di business. Ogni chiamata a tool diventa un salto di rete dentro un'applicazione che la risposta la sapeva già.

### Dove si colloca NeuronAI

NeuronAI è l'implementazione PHP-nativa della stessa architettura. In concreto fornisce:

- Un ciclo di agent con tool calling, su molti provider dietro un'unica interfaccia
- Un motore `Workflow` event-driven con stato, cicli, checkpoint e interruzione — il pezzo in forma LangGraph
- Una pipeline RAG: loader, embedding, vector store, pre/post processor
- Supporto client MCP
- Streaming con adapter per protocolli di interfaccia
- Observability di prima classe tramite Inspector

Il confronto onesto: Python ha una panchina più profonda di strumenti di livello ricerca e una comunità molto più grande. PHP ha i tuoi dati, il tuo modello di dominio, la tua autenticazione, la tua coda e il tuo ORM. Per un'enorme classe di applicazioni gestionali vince il secondo elenco, perché la maggior parte del valore agentico viene dall'agire su dati proprietari con regole proprietarie, non da tecniche di modello inedite.

### Essere corretti verso le alternative

Non sei obbligato a usare un framework. Puoi chiamare l'API di un provider con Guzzle e scriverti il ciclo dei tool da solo: saranno centocinquanta righe. Quello di cui poi ti fai carico è: astrazione multi-provider, retry, parsing dello streaming, generazione degli schemi, trimming della cronologia, checkpoint e un formato di trace. Questa è la portata onesta di ciò che un framework ti risparmia. Giudica NeuronAI su quell'elenco.

### Punti chiave

- NeuronAI implementa la stessa architettura di LangGraph, in PHP.
- L'argomento strategico è la località dei dati: metti l'agent dove la logica di business già si trova.
- I framework ti comprano astrazione dei provider, streaming, schemi, gestione della cronologia, checkpoint e trace.

## 1.7 Scegliere il piolo giusto: un framework decisionale

La scala è utile solo se si trasforma in una procedura. Eccone una: quattro domande, poste in ordine, applicate a un requisito reale invece di ripiegare su "costruiamo un agent".

### Quattro domande, in ordine

**D1. La sequenza dei passi è conoscibile in anticipo?**
Sì → piolo 1 o 3. No → considera il piolo 4.
È tutta la questione. Se sai disegnare il diagramma di flusso, scrivi il diagramma di flusso. Un workflow che fa sempre le stesse tre cose è più economico, più veloce, testabile e debuggabile.

**D2. Deve leggere o scrivere sistemi di registrazione?**
No → nessun tool necessario. Sì → tool, e subito: quali permessi, quale tracciamento d'audit, quali azioni sono irreversibili.

**D3. Qualche azione è irreversibile o costosa?**
Sì → l'human-in-the-loop è obbligatorio, non un obiettivo aggiuntivo. Rimborsi, email ai clienti, cancellazioni, pagamenti. Progetta il cancello di approvazione insieme al tool, mai dopo.

**D4. La correttezza dipende da conoscenza privata?**
Sì → RAG oppure tool di database. Nota che sono risposte diverse: RAG per prosa non strutturata, tool di database per fatti strutturati. Usare RAG per rispondere a "quanti ordini ha fatto questo cliente" è un errore di progetto: quella è una query SQL, e il modello dovrebbe chiamarla come tool.

### Casi di studio

**Caso A — "Riassumi i ticket di assistenza in arrivo."**
D1 sì, D2 no, D3 no, D4 no. → **Piolo 1.** Una chiamata, un prompt. Costruire un agent qui è sviluppo guidato dal curriculum.

**Caso B — "Rispondi alle domande dei clienti usando il nostro centro assistenza."**
D1 sì, D2 sola lettura, D3 no, D4 sì. → **Piolo 3 con RAG.** Recupera, poi genera, poi cita. Una pipeline fissa in due passi. Nessuna autonomia richiesta.

**Caso C — "Gestisci un reclamo di un cliente dall'inizio alla fine."**
D1 no — non sai in anticipo se servirà una ricerca dell'ordine, una verifica di policy, un rimborso, un'escalation o tutte e quattro. D2 sì, lettura e scrittura. D3 sì, i rimborsi sono irreversibili. D4 sì.
→ **Piolo 4, con tool, RAG, cancelli di approvazione e tracing completo.** È il Progetto finale B nel Capitolo 25, e si guadagna ogni pezzo di macchinario di questo libro.

**Caso D — "Genera un report settimanale dal nostro database."**
D1 sì, D2 lettura, D3 no, D4 sì-strutturato. → **Piolo 3.** Query fissa, il modello formatta la prosa. La tentazione di lasciare che un agent esplori il database è reale; resistile per un job schedulato in cui le domande non cambiano mai.

### Il principio di escalation

Parti dal piolo più basso che potrebbe funzionare. Mettilo in produzione. Sali solo quando hai prove — casi reali di fallimento — che quel piolo non basta. Ogni piolo verso l'alto moltiplica costi, latenza e superficie operativa.

Il percorso inverso è molto più doloroso: i team che partono dal piolo 4 raramente scendono, perché a quel punto la flessibilità è portante e nessuno sa quali parti servissero davvero.

### Esercizio

Prendi tre funzionalità del tuo prodotto. Per ciascuna: applica le quattro domande, dichiara il piolo e giustificalo in cinque righe. Trova un caso in cui inizialmente volevi il piolo 4 e le domande ti hanno spinto giù al piolo 3 — ce n'è quasi sempre uno, e accorgersene è l'abilità che questo capitolo insegna.

### Punti chiave

- Se sai disegnare il diagramma di flusso, costruisci il diagramma di flusso.
- Le azioni irreversibili richiedono un cancello di approvazione progettato nello stesso momento del tool.
- RAG per la prosa, tool di database per i fatti: non confonderli.
- Parti in basso, sali sulla base delle prove.
