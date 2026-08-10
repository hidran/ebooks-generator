# Capitolo 11 — Teoria del retrieval

## 11.1 Il problema che il RAG risolve

### Il divario

Un modello linguistico sa quello che c'era nei suoi dati di addestramento. Non conosce la politica di reso della tua azienda, i tuoi runbook interni, il verbale del consiglio della settimana scorsa né la specifica del prodotto che hai rilasciato ieri.

Chiediglielo comunque e succede una di due cose. Dice di non saperlo, il che è onesto ma inutile. Oppure produce qualcosa di plausibile e sbagliato, che è peggio che inutile.

### La definizione

Il RAG è il processo di fornire riferimenti a una base di conoscenza esterna ai dati di addestramento del modello prima di generare una risposta.

Il meccanismo, nella sua forma più semplice:

1. L'utente pone una domanda.
2. Il tuo sistema cerca in una base di conoscenza i passaggi rilevanti per quella domanda.
3. Quei passaggi vengono aggiunti al prompt.
4. Il modello risponde usandoli.

Il modello non ha imparato nulla. Gli è stata consegnata la pagina rilevante e gli è stato chiesto di leggerla.

### Perché è conveniente

La documentazione fa l'argomento economico in modo diretto: il RAG estende le capacità di un LLM a un dominio specifico o alla base di conoscenza interna di un'organizzazione **senza riaddestrare il modello.**

Quella parola — riaddestrare — è l'alternativa, e vale la pena quantificarla:

| | RAG | Fine-tuning |
|---|---|---|
| Costo di allestimento | Ore | Da giorni a settimane, più il calcolo |
| Costo di aggiornamento | Reindicizzare il documento cambiato | Riaddestrare |
| Latenza di aggiornamento | Minuti | Giorni |
| Può citare le fonti | Sì | No |
| Funziona con qualunque modello | Sì | No — legato a quello che hai messo a punto |
| Gestisce dati che cambiano spesso | Sì | No |

Per "il modello dovrebbe conoscere la nostra documentazione", il RAG vince su ogni riga. I casi interessanti in cui vince il fine-tuning riguardano *stile e formato*, non conoscenza — la Sezione 11.4 lo tratta come si deve.

### L'altro uso, facile da perdere

Il RAG viene di solito presentato come accesso a dati riservati. Ma lo stesso meccanismo fornisce informazioni **recenti**: ricerca attuale, statistiche di questo trimestre, notizie di oggi. Il cutoff di addestramento del modello è un confine di conoscenza, e il retrieval lo attraversa allo stesso modo in cui attraversa il confine del tuo firewall.

### A che cosa il RAG non serve

Vale la pena dirlo ora, perché la confusione è costosa e la Sezione 4.5 l'aveva già preparata:

**Non per i fatti che il tuo database conosce.** "Quanti ordini ha fatto questo cliente?" è SQL. Una ricerca vettoriale su prosa ti darà una risposta approssimativamente giusta, che per un conteggio è semplicemente sbagliata.

**Non per la memoria dell'utente.** "Ricorda che sono vegetariano" è memoria a lungo termine, non recupero di conoscenza.

**Non per il ragionamento.** Il RAG fornisce fatti. Non rende il modello migliore in logica, aritmetica o pianificazione.

**Non per corpus piccoli.** Se la tua intera base di conoscenza è di 3.000 token, mettila nel system prompt. Niente embedding, niente vector store, niente pipeline. L'infrastruttura si guadagna il posto solo quando il corpus supera ciò che puoi permetterti di mandare ogni volta.

Quest'ultima è la più ignorata, ed è l'equivalente RAG del "se sai disegnare il diagramma di flusso, costruisci il diagramma di flusso" della Sezione 1.1.

### Punti chiave

- Il RAG consegna al modello la pagina rilevante; non gli insegna nulla.
- Più economico del fine-tuning su ogni dimensione che conta per la conoscenza.
- Attraversa anche il confine del cutoff di addestramento, non solo il firewall.
- Non per fatti numerabili, memoria dell'utente, ragionamento o corpus abbastanza piccoli da stare inline.

## 11.2 Embedding e ricerca per similarità

### L'intuizione

Un embedding è un elenco di numeri che rappresenta il *significato* di un pezzo di testo. Un modello tipico produce 768, 1024 o 1536 numeri per testo.

La proprietà utile: **testi con significato simile producono elenchi di numeri simili.**

"Il gatto stava sul tappeto" e "Un felino riposava sulla stuoia" non condividono quasi nessuna parola. I loro embedding sono vicini. "Il gatto stava sul tappeto" e "I ricavi trimestrali sono cresciuti del 12%" condividono la parola "il". I loro embedding sono lontani.

La ricerca per parole chiave vede le parole. Gli embedding vedono il significato.

### Ricerca per similarità

Conserva l'embedding di ogni chunk della tua base di conoscenza. Quando arriva una domanda, calcolane l'embedding e trova i vettori memorizzati più vicini.

Quell'operazione è ciò per cui esiste un **vector store**. L'interfaccia di NeuronAI è esattamente questa:

```php
public function similaritySearch(array $embedding, int $k = 4): iterable;
```

Le dai un vettore, ottieni i `k` documenti più vicini. `k` — quanti chunk recuperare — è spesso chiamato top-K, ed è una delle due manopole che più influenzano la qualità. L'altra è la dimensione dei chunk (Sezione 11.3).

### Punteggi, non distanze

Un dettaglio che NeuronAI esplicita, e che previene un bug reale:

> `similaritySearch` dovrebbe restituire documenti con un **punteggio** di similarità, non con una **distanza** di similarità.

Vanno in direzioni opposte. Una distanza di 0 significa identico; un punteggio di 1 significa identico. Confondili e la tua logica di "miglior corrispondenza" restituisce silenziosamente i risultati peggiori.

Quando un database restituisce una distanza, convertila:

```php
use NeuronAI\RAG\VectorSimilarity;

$document->setScore(
    VectorSimilarity::similarityFromDistance($distance)
);
```

Serve a chiunque implementi uno store personalizzato. È anche un bell'esempio di framework che codifica una convenzione per prevenire un'intera categoria di errore.

### Tre cose che sorprendono

**Gli embedding sono specifici del modello.** I vettori del modello di OpenAI non possono essere confrontati con quelli del modello di Voyage. Sono sistemi di coordinate diversi. Cambia il provider di embedding e **devi ricalcolare gli embedding dell'intero corpus.** Tratta il modello di embedding come parte dello schema dei tuoi dati, non come un'impostazione intercambiabile.

Vale la pena dirlo con fermezza perché è uno dei pochi punti in cui la libertà di scambio delle interfacce della Sezione 3.6 non si applica. L'interfaccia si scambia; i dati non la seguono.

**Le dimensioni devono corrispondere allo store.** Se il tuo modello di embedding produce 1536 numeri e la colonna del tuo vector store è dichiarata a 1024, non funziona nulla. Lo schema MariaDB nei documenti fissa `VECTOR(1536)` proprio per questo.

**La similarità non è rilevanza.** Due chunk possono essere semanticamente vicini e solo uno dei due rispondere alla domanda. È il divario che il reranking esiste per colmare (Sezione 12.7).

### Costo

Calcolare embedding è molto più economico che generare — tipicamente una piccola frazione del prezzo per token di un modello di chat. Ma calcoli l'embedding dell'intero corpus una volta e di ogni query per sempre, quindi su scala è una voce di costo reale.

**Ollama esegue modelli di embedding in locale, gratis.** Per ogni laboratorio di questa parte, e per moltissimi sistemi in produzione, un modello di embedding locale è del tutto adeguato. Dato che la Sezione 3.6 ha già introdotto Ollama, il RAG si può imparare dall'inizio alla fine a costo zero.

### Punti chiave

- Un embedding è una rappresentazione numerica del significato; i significati simili stanno vicini.
- `similaritySearch($embedding, $k)` — il top-K è una delle due manopole di qualità.
- Restituisci punteggi, non distanze; converti con `VectorSimilarity`.
- Gli embedding sono specifici del modello: cambiare modello significa ricalcolare tutto.
- I modelli di embedding locali rendono gratuito imparare il RAG.

## 11.3 Chunking: la decisione che determina la qualità

È la sezione più consequenziale del capitolo.

### Perché dividere

Due motivi, ed entrambi contano:

**Precisione del retrieval.** Se calcoli l'embedding di un intero manuale di 40 pagine come un solo vettore, quel vettore rappresenta il significato medio dell'intero manuale — cioè, quasi nulla. Una domanda su un paragrafo non gli corrisponderà bene.

**Budget di contesto.** Recuperi chunk per metterli nel prompt. Un manuale intero non ci sta, e anche se ci stesse, l'aritmetica della Sezione 1.4 dice che non vorresti pagarlo a ogni turno.

Quindi: dividi il documento in pezzi, calcola l'embedding di ogni pezzo, recupera i pezzi che corrispondono.

### Il compromesso centrale

La documentazione dichiara il principio in modo netto:

> Più lunghe sono le tue unità di testo, meno accurata sarà la rappresentazione degli embedding.

**Chunk piccoli** — embedding precisi, corrispondenza accurata, ma ogni pezzo recuperato può mancare del contesto necessario a essere utile. Trovi la frase esatta e si rivela priva di senso senza il paragrafo attorno.

**Chunk grandi** — molto contesto, ma embedding sfocati e token sprecati. Recuperi 800 parole per rispondere a una domanda a cui il modello avrebbe risposto con 40.

Non esiste un valore universalmente corretto. Esiste un valore corretto *per il tuo contenuto*, e trovarlo è empirico.

### I tre parametri

**Lunghezza massima.** Quanto può diventare grande un chunk. Lo splitter di default di NeuronAI usa 1.000 caratteri.

**Separatore.** Dove è consentito tagliare. Il default è il punto — i confini di frase. Ma se i tuoi documenti sono Markdown con sezioni intestate, tagliare su `\n## ` produce chunk allineati alla struttura semantica del documento stesso, che è quasi sempre meglio che tagliare sulle frasi.

È il consiglio pratico più utile di questa sezione: **fai corrispondere il separatore alla struttura del tuo contenuto**, non accettare il default solo perché c'è.

**Sovrapposizione.** Parole portate dal chunk precedente in quello successivo. Il default è zero.

### Perché esiste la sovrapposizione

La documentazione la descrive come un aumento della connessione semantica fra sezioni adiacenti. In concreto, risolve questo fallimento:

> Chunk 1: "...la finestra di rimborso è di 30 giorni dalla consegna."
>
> Chunk 2: "Dopo questo periodo è disponibile solo un credito d'acquisto."

Il chunk 2 da solo è incomprensibile — *dopo quale periodo?* Con la sovrapposizione, il chunk 2 inizia con la coda del chunk 1 e porta con sé il proprio contesto.

Costo: il testo duplicato significa più chunk, più chiamate di embedding, più spazio. Un punto di partenza ragionevole è il 10–15 % della dimensione del chunk. Zero è giusto solo quando i tuoi chunk sono davvero indipendenti — una FAQ in cui ogni voce sta in piedi da sola, un catalogo prodotti.

### Chunking consapevole della struttura

Il chunking migliore rispetta ciò che il documento *è*:

| Contenuto | Dividi su |
|---|---|
| Documentazione Markdown | Intestazioni (`##`) |
| FAQ | Un chunk per domanda |
| Codice | Confini di funzione o classe |
| Trascrizione | Turni di parola o timestamp |
| Testo legale | Clausola o articolo |
| Prosa | Paragrafi, poi frasi |

Uno splitter personalizzato (Sezione 12.3) è spesso venti righe e produce un miglioramento di qualità maggiore di qualunque quantità di messa a punto del prompt. È il codice personalizzato con più leva in un sistema RAG, e vale la pena dirlo esplicitamente: ci si aspetta che la leva sia nel prompt, e di solito non lo è.

### Come scegliere davvero

Non indovinare. Misura — e lo strumento ce l'hai già dal Capitolo 10.

1. Costruisci un dataset di 20 domande reali con risposte corrette note.
2. Indicizza il corpus in tre configurazioni (diciamo 500/1000/2000 caratteri, 0/10/20 % di sovrapposizione).
3. Esegui l'evaluator su ciascuna, usando `FaithfulnessJudge` e `CorrectnessJudge`.
4. Confronta i punteggi.

È il motivo per cui le eval sono venute prima del RAG in questo libro. Il chunking è un parametro empirico, e senza un'impalcatura di misura stai regolando a intuito.

### Punti chiave

- Dividi per precisione del retrieval e per budget di contesto.
- Chunk più lunghi significano embedding più sfocati: è il compromesso centrale.
- Fai corrispondere il separatore alla struttura del contenuto; non accettare il default.
- La sovrapposizione risolve i chunk privi di senso da soli; parti dal 10–15 %.
- Scegli i parametri con la valutazione, non con l'intuito.

## 11.4 RAG, fine-tuning, riempimento del contesto e tool

### Le quattro opzioni

**1. Riempimento del contesto.** Metti tutto nel system prompt. Semplice, esatto, nessuna infrastruttura. Limitato dalla context window e pagato a ogni singola richiesta.

**2. RAG.** Recupera i passaggi rilevanti al momento della query. Scala a qualunque dimensione di corpus, supporta la citazione, si aggiorna reindicizzando.

**3. Tool.** Lascia che il modello interroghi un sistema vivo. Esatto, attuale, strutturato.

**4. Fine-tuning.** Addestra il modello sui tuoi dati. Costoso, lento da aggiornare, ma cambia il comportamento di default del modello.

### La tabella decisionale

| Situazione | Meccanismo |
|---|---|
| Sotto i ~2.000 token di riferimento stabile | Riempimento del contesto |
| Grande corpus documentale non strutturato | RAG |
| Fatti numerabili o interrogabili | Tool |
| Dati che cambiano di minuto in minuto | Tool |
| Deve citare un documento fonte | RAG |
| Stile o formato di output coerente | Fine-tuning |
| Vocabolario di dominio che il modello legge male | Fine-tuning |
| "Il modello dovrebbe conoscere le nostre policy" | RAG |
| "Il modello dovrebbe suonare come il nostro brand" | Fine-tuning |

### La distinzione che si sbaglia

**Il fine-tuning insegna comportamenti. Il RAG fornisce fatti.**

Fare fine-tuning di un modello sulla tua documentazione è un errore comune e costoso. Il modello impara la *forma* della tua scrittura — il vocabolario, il registro, la struttura — ma non impara i fatti in modo affidabile, e quando la documentazione cambia devi rifare tutto. Nel frattempo non puoi citare nulla, perché non c'è nulla da citare.

Se qualcuno dice "vogliamo che il modello conosca il nostro prodotto", vuole il RAG. Se dice "vogliamo che scriva come il nostro team di assistenza", quello è territorio da fine-tuning — e anche allora, un buon system prompt con tre esempi arriva quasi allo stesso risultato a una frazione del costo.

### L'altra distinzione che si sbaglia

**RAG per la prosa. Tool per i record.**

È il punto della Sezione 4.5, e merita di essere ripetuto qui perché è dove si commette l'errore.

- *"Qual è la nostra politica di reso?"* → RAG. È scritta in un documento.
- *"L'ordine 4471 è stato rimborsato?"* → Tool. È una riga in una tabella.
- *"Quali clienti hanno avuto un rimborso il mese scorso?"* → Tool. È una query.

Indicizzare la tua tabella ordini in un vector store per rispondere alla seconda domanda è un errore di progetto che produce risposte sicure di sé e approssimative. La ricerca vettoriale recupera cose che *sembrano simili*; non calcola.

### Si compongono

I sistemi migliori ne usano più d'uno. La Sezione 12.1 mostra che il framework lo supporta direttamente: una classe `RAG` **è** un `Agent`, quindi può avere tool.

L'esempio documentato è scelto bene — un agent di consigli di allenamento con una base di conoscenza di informazioni sugli esercizi (RAG) più un tool che legge lo stato di allenamento attuale dell'utente dal database (tool calling). Prosa dal retrieval, fatti dal tool, una risposta.

### Punti chiave

- Quattro meccanismi: riempimento, RAG, tool, fine-tuning.
- Il fine-tuning cambia il comportamento; il RAG fornisce fatti.
- RAG per la prosa, tool per i record: la confusione più comune e più costosa.
- Sotto i ~2.000 token stabili, salta del tutto l'infrastruttura.
- I sistemi reali li combinano; il progetto RAG-è-un-Agent di NeuronAI lo supporta direttamente.

## 11.5 I limiti del RAG ingenuo

### Il RAG ingenuo

Calcola l'embedding della domanda, recupera i top-K, riempi il prompt, genera. Funziona sorprendentemente bene, e poi fallisce in modi specifici e riconoscibili. Conoscere i sei è la differenza fra diagnosticare un problema e concludere che "l'AI non funziona".

### Fallimento 1 — La domanda non assomiglia alla risposta

L'utente chiede *"Perché la mia cosa è rotta?"* Il documento dice *"Il codice errore 4021 indica allocazione disco insufficiente sul volume primario."*

Semanticamente distanti. Il retrieval fallisce.

**Soluzione:** trasformazione della query. Riscrivi o espandi la domanda prima di calcolarne l'embedding — NeuronAI include `QueryTransformationPreProcessor` proprio per questo, e gira in `PreProcessQueryNode` (Sezione 12.7).

### Fallimento 2 — Simile non è rilevante

Recuperi cinque chunk, tutti sui rimborsi. Solo uno copre la finestra di 30 giorni chiesta dall'utente. Gli altri quattro sono rumore, e il rumore costa token e può distrarre il modello facendogli rispondere dal passaggio sbagliato.

**Soluzione:** reranking. Recupera in modo ampio, poi riassegna il punteggio con un modello che legge insieme la query e ciascun documento. Sezione 12.7.

### Fallimento 3 — La risposta è distribuita fra chunk

*"Come interagiscono le nostre politiche di reso e spedizione per gli ordini internazionali?"* I rimborsi sono in un documento, le spedizioni in un altro, l'eccezione internazionale in un terzo. Il retrieval top-K su una query ne trova uno.

**Soluzione:** retrieval multi-query, oppure un K più alto più reranking. Genuinamente difficile: è qui che il RAG ingenuo mostra i suoi limiti.

### Fallimento 4 — Domande di aggregazione

*"Quanti articoli menzionano il GDPR?"* La ricerca vettoriale recupera i documenti *più simili*, non *tutti* quelli corrispondenti. Non esiste un'operazione di conteggio.

**Soluzione:** questa non è una domanda da RAG. Usa un tool, o il filtraggio sui metadati con una ricerca ibrida. Riconoscerlo è la soluzione.

### Fallimento 5 — Allucinazione sicura di sé

Il retrieval non restituisce nulla di utile, e il modello risponde comunque dalla sua conoscenza generale: in modo fluente, plausibile, sbagliato.

**È il fallimento più pericoloso**, perché sembra esattamente un successo.

**Soluzione, in tre parti:**

1. **Istruisci esplicitamente.** Nella sezione `background`: *"Rispondi solo a partire dai documenti forniti. Se non contengono la risposta, dillo."*
2. **Misuralo.** `FaithfulnessJudge` della Sezione 10.5 esiste esattamente per questo. È il motivo per cui le eval sono venute prima.
3. **Cita.** Richiedi che la risposta faccia riferimento al documento fonte. Una citazione che l'utente può verificare converte un fallimento invisibile in uno visibile.

### Fallimento 6 — Indice obsoleto

Qualcuno aggiorna il documento di policy. Il vector store contiene ancora i chunk del trimestre scorso. L'agent risponde con sicurezza da informazioni superate.

**Soluzione:** la reindicizzazione, che NeuronAI affronta con `reindexBySource()` (Sezione 12.6). È anche una questione operativa: che cosa innesca una reindicizzazione, e come sai che è avvenuta?

### Il riassunto onesto

Il RAG ingenuo ti porta forse al 70 %. Il restante 30 % è trasformazione della query, reranking, filtraggio sui metadati, ricerca ibrida e valutazione — che è esattamente il motivo per cui la pipeline di NeuronAI ha pre-processor e post-processor come stadi di prima classe e non come ripensamento.

Chi crede che il RAG sia "calcola l'embedding e recupera" metterà in produzione qualcosa che si dimostra benissimo e delude alla seconda settimana. Conoscere i sei modi di fallire è ciò che ti permette di riconoscere quello che hai davanti.

### Punti chiave

- Sei modi di fallire: disallineamento della query, simile-ma-non-rilevante, risposte fra chunk, aggregazione, allucinazione, obsolescenza.
- L'allucinazione sicura di sé è la più pericolosa perché somiglia al successo.
- Istruisci, misura con `FaithfulnessJudge` e cita.
- Il RAG ingenuo è al ~70 %; gli stadi della pipeline sono il resto.
