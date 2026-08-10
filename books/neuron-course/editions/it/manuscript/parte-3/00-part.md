# Parte III — Retrieval

Un modello sa quello che c'era nei suoi dati di addestramento e quello che gli metti nel prompt. Nient'altro. Non conosce il tuo catalogo prodotti, il tuo wiki interno, lo storico dei ticket, né nulla di quanto è accaduto dopo il suo cutoff.

Il retrieval-augmented generation è la risposta standard, ed è largamente frainteso come "dai i tuoi documenti al modello". Quello che è davvero: un problema di ricerca travestito da problema di generazione. Quasi ogni sistema RAG deludente delude perché il retrieval è cattivo, non perché lo sia il modello.

Il Capitolo 11 copre la teoria e, altrettanto importante, che cosa il retrieval *non* risolve — le domande a cui risponderà sempre male e i casi in cui dovresti invece interrogare un database.

Il Capitolo 12 costruisce la pipeline NeuronAI dall'inizio alla fine: loader, splitter, provider di embedding, vector store, filtri sui metadati, reindicizzazione quando i documenti cambiano, e i pre- e post-processor che separano una demo da qualcosa che faresti usare a un cliente.

Entrambi i laboratori girano a costo zero su embedding locali.
