# Parte II — PHP puro e Composer

Niente framework. Composer, uno script CLI e la libreria.

È la parte più lunga del libro e quella che insegna di più, perché non c'è posto dove nascondersi. Ogni oggetto viene costruito davanti a te, ogni chiamata è esplicita, e quando qualcosa va storto non c'è un service container da incolpare.

Partirai da uno scheletro di progetto e da un primo agent, poi attraverserai i pezzi che trasformano una chiamata al modello in un sistema: il modello dei messaggi e i diversi tipi di memoria di cui una conversazione ha bisogno; i tool in profondità reale, dove vive la maggior parte della difficoltà pratica del software agentico; structured output tipizzato, validato e ritentato quando il modello sbaglia; streaming e i chunk che produce; immagini e documenti; MCP, per collegarti a server di tool che non hai scritto tu; e infine observability e valutazione, per scoprire che cosa ha fatto davvero il tuo agent e se sta peggiorando.

Ogni laboratorio di questa parte gira gratis e offline su Ollama.

Se sei qui per Laravel, resisti alla tentazione di saltare avanti. La Parte V integra queste idee; non le insegna.
