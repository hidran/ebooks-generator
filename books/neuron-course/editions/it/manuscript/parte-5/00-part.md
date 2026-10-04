# Parte V — Laravel

Finora tutto ha girato da uno script CLI, per scelta. Ora si sposta dentro un'applicazione con utenti, un database, una coda, un layer HTTP e una fattura.

L'SDK Laravel di NeuronAI fornisce una parte dell'impianto — configurazione, facade dei componenti, generatori — e l'applicazione fornisce il resto: un service provider, una migration, un message store su Eloquent. I Capitoli 17 e 18 coprono entrambe le parti in fretta, perché i problemi interessanti non sono l'impianto.

I problemi interessanti sono quelli che ha solo la produzione. Tool che toccano i tuoi modelli veri e non devono farsi ingannare fino a toccare quelli di un altro tenant. Retrieval su dati che cambiano di continuo e vanno reindicizzati senza finestre di manutenzione. Token in streaming verso un browser via SSE e Livewire mentre il lavoro vero lo fa un queue worker. Workflow di approvazione che sopravvivono a un deploy avvenuto fra la richiesta e la decisione del manager. Costi che scalano con il comportamento degli utenti anziché col loro numero. Provider che ti applicano un rate limit nel momento peggiore possibile. Prompt injection che arriva dalla tua stessa casella di assistenza.

Il Capitolo 23 si chiude con una checklist di deploy e con la domanda di cui questo libro parla davvero: qual è la cosa peggiore che il tuo agent può fare, e cosa glielo impedisce?
