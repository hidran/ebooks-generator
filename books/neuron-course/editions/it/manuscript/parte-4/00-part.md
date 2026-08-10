# Parte IV — Workflow

Un agent decide da sé il proprio flusso di controllo. È la sua forza, e in produzione è anche il problema: non puoi promettere a un cliente che un ciclo autonomo seguirà una procedura di compliance.

I workflow sono la risposta. Il grafo lo scrivi tu; il modello riempie i nodi. Il risultato è deterministico dove deve esserlo e intelligente dove serve, il che descrive la maggior parte del software gestionale di valore.

Il Capitolo 13 introduce il modello event-driven che NeuronAI usa. Il Capitolo 14 aggiunge cicli, diramazioni e stato tipizzato. Il Capitolo 15 copre la funzionalità che rende i workflow davvero pronti per la produzione: l'interruzione. Un workflow può fermarsi a metà esecuzione, persistere un checkpoint, aspettare quanto serve a un essere umano e riprendere.

Il Capitolo 15 contiene anche l'avvertimento di correttezza più importante di tutto il libro. Un nodo ripreso si riesegue dall'inizio, quindi una chiamata all'LLM senza checkpoint produrrà *contenuto diverso da quello che l'essere umano ha approvato*. È una correzione di una riga e un problema di audit se te la lasci sfuggire.

Il Capitolo 16 mette più agent in un unico sistema e li fa passare il lavoro l'uno all'altro.
