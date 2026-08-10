# Prefazione {.unnumbered}

## Una domanda

Ogni idea di questo libro discende da una sola domanda:

> **Chi decide che cosa succede dopo?**

Quando chiami un modello linguistico per riassumere un ticket di assistenza, decide il tuo codice. Decide cosa mandare, quando mandarlo e cosa fare della risposta. Il modello produce testo, e nient'altro.

Quando costruisci un agent, quella decisione la consegni al modello. Gli dai un obiettivo e un insieme di capacità: sceglie quale usare, vede il risultato, sceglie di nuovo, e va avanti finché non decide di aver finito. Quella sequenza non l'hai scritta tu. È emersa.

Questo trasferimento di controllo è l'intero argomento del libro. Tutto il resto — memoria, tool, structured output, retrieval, workflow, approvazione umana, observability — esiste per rendere quel trasferimento sostenibile in produzione. Dai a un modello la capacità di agire ed erediti una serie di problemi che il PHP normale non ha: non puoi prevedere quanto costerà una richiesta, non puoi testare il flusso in modo deterministico, e quando si comporta male ti serve un trace per capire perché al quarto passo ha scelto il tool sbagliato.

Questo libro parla di guadagnarsi quel potere in modo deliberato, e di sapere quando non serve.

## Perché PHP

La conversazione sull'AI agentica si è svolta quasi interamente in Python. È un incidente della storia della ricerca, non un'affermazione su dove sia il lavoro. Una quota enorme della logica di business del mondo — i CRM, i sistemi di fatturazione, i motori di prenotazione, gli strumenti interni che mandano avanti le aziende in silenzio — è scritta in PHP, ed è già accanto al database, alla coda, al layer di autenticazione e agli utenti che trarrebbero beneficio da un agent.

Attaccare un microservizio Python a un'applicazione Laravel per chiamare un LLM è una decisione architetturale vera, con costi veri: un altro runtime, un altro deploy, un altro set di credenziali, un altro salto di rete e una copia del tuo modello di dominio destinata a divergere. A volte è la scelta giusta. Spesso non lo è, e l'unico motivo per cui accade è che nessuno ha mostrato al team PHP l'alternativa.

**NeuronAI** è l'alternativa. È un framework PHP per costruire agent — si installa come `neuron-core/neuron-ai`, documentato su neuron-ai.dev — ed è l'argomento di questo libro. Copre lo stesso terreno dei noti framework Python: provider, tool, memoria, structured output, retrieval-augmented generation, workflow event-driven, interruzione human-in-the-loop, observability. Lo fa con interfacce, dependency injection e classi tipizzate, in un modo che sembrerà del tutto ordinario a chiunque abbia usato un framework PHP moderno — ed è esattamente il punto.

Una nota sul nome, perché l'ecosistema è incoerente al riguardo. La libreria si chiama **NeuronAI**. Il pacchetto Composer è `neuron-core/neuron-ai`, il binario CLI è `vendor/bin/neuron` e il namespace radice è `NeuronAI\`. Questo libro scrive NeuronAI nella prosa e lascia ogni nome di pacchetto, comando e namespace esattamente come devi digitarlo.

## A chi si rivolge

Scrivi PHP. Hai dimestichezza con Composer, namespace, interfacce e un IDE moderno. Probabilmente hai usato Laravel, anche se le Parti da I a IV non lo richiedono: girano su PHP puro e uno script CLI, deliberatamente, così puoi vedere ogni pezzo in movimento prima che un framework te ne nasconda qualcuno.

Non ti serve sapere nulla di machine learning. In questo libro non c'è matematica oltre all'aritmetica sui costi. Non serve aver già chiamato l'API di un LLM. Quello che serve è l'istinto che rende un buon sviluppatore backend diffidente verso la magia, perché è proprio l'istinto che questo libro premia.

Se hai già costruito qualcosa con un LLM e l'hai trovato inaffidabile, costoso o impossibile da debuggare, sei il lettore per cui è stato scritto. Quei tre fallimenti hanno cause, e le cause hanno un nome.

## Che cosa costruirai

Il libro alterna teoria, PHP puro e Laravel, in quest'ordine, e costruisce in modo continuo invece che a frammenti scollegati.

Alla fine della Parte II avrai un agent che gira da uno script CLI con tool che non ha scritto una riga di codice per invocare, una cronologia della conversazione che sopravvive ai riavvii, output tipizzato e validato, risposte in streaming, comprensione di immagini e documenti, una connessione MCP a server di tool esterni e un trace di tutto ciò che ha fatto.

Alla fine della Parte IV avrai una pipeline di retrieval sulla tua documentazione, workflow event-driven con cicli e diramazioni, workflow che si fermano a metà esecuzione perché un essere umano approvi un'azione e riprendono da un checkpoint, e un sistema multi-agente in cui agent specializzati si passano il lavoro.

Alla fine della Parte V tutto questo è dentro un'applicazione Laravel: facade e dependency injection, cronologia in Eloquent, tool che toccano i tuoi modelli veri, retrieval sui dati della tua applicazione, isolamento per tenant, streaming di token via SSE e Livewire, workflow di approvazione con code e notifiche, controllo dei costi, resilienza ai rate limit, difese contro la prompt injection e una checklist di deploy.

La Parte VI è composta da due progetti finali — un auditor di repository come CLI in PHP puro e un help desk agentico in Laravel — più tre capitoli sulle cose che nessuno ti dice: come scegliere una versione e sopravviverle, cosa offre davvero l'ecosistema intorno al framework e come usare l'assistenza AI per scrivere questo tipo di codice senza lasciarle scrivere le parti che contano.

## Sul codice

Ogni esempio di codice è stato scritto su **NeuronAI v3** e, per la Parte V, sull'**SDK Laravel di NeuronAI 1.3.0**, che richiede `neuron-ai: ^3.15`. Si dà per scontato PHP 8.2 o superiore.

Questo conta più del solito. NeuronAI ha cambiato i namespace tra v1/v2 e v3 — `NeuronAI\Agent` è diventato `NeuronAI\Agent\Agent`, `NeuronAI\SystemPrompt` è diventato `NeuronAI\Agent\SystemPrompt` — e una gran quantità di materiale pubblicato, comprese parti della documentazione ufficiale, non si è adeguata. Un tutorial corretto due anni fa oggi fallisce già sulla prima istruzione `use`.

Anche la documentazione ufficiale è in disaccordo con sé stessa in più di quaranta punti: tre firme di costruttore diverse per lo stesso vector store, due API di esecuzione diverse per i workflow su pagine adiacenti, nomi di classe scritti male, un metodo `public` in un esempio e `protected` in quello successivo. Ognuno di questi produce un errore per chi copia la pagina.

L'**Appendice A** è l'elenco. Tutti e quarantaquattro i punti, raggruppati per il capitolo che riguardano, con una serie di brevi script di verifica che risolvono interi gruppi in un colpo solo sulla versione che hai davvero installato. Lavorarci sopra richiede un pomeriggio ed è la cosa di maggior valore che puoi fare prima di scrivere codice di produzione con questa libreria. Se sei il tipo di persona che legge prima le appendici, comincia da lì.

Ogni laboratorio delle Parti da II a IV è pensato per girare **gratis e offline** su Ollama con un modello locale. Ti serviranno credenziali API a pagamento solo dove l'esercizio dipende davvero dalla qualità di un modello di frontiera, e il libro lo dice esplicitamente ogni volta.

## La domanda che questo libro sta davvero facendo

L'ultimo capitolo si chiude con una domanda a cui dovresti saper rispondere per qualunque cosa metterai in produzione dopo averlo letto:

> **Qual è la cosa peggiore che il tuo agent può fare, e cosa glielo impedisce?**

Se non sai rispondere, non hai finito di costruire.

*Hidran Arias, 2026*
