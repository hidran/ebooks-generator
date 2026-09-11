# Prefazione {.unnumbered}

## Perché questo libro

Questo libro è pensato come un percorso da sviluppatore: prima costruisci basi solide, poi applichi quelle basi in progetti reali, infine impari a organizzare, proteggere e pubblicare il codice. La struttura segue un criterio pratico, simile a quello dei buoni manuali tecnici: ogni parte introduce un problema, mostra gli strumenti necessari e chiude con esempi che puoi eseguire.

PHP è usato in contesti molto diversi: piccoli siti, applicazioni aziendali, API, CMS, framework moderni. Per questo il libro alterna capitoli fondamentali, capitoli di progetto e capitoli professionali. Non serve conoscere tutto prima di iniziare: serve capire in che ordine impararlo.

## A chi è destinato

Il libro è per chi vuole imparare PHP in modo progressivo e per chi lo usa già ma vuole riallinearsi al PHP moderno. È utile conoscere HTML e CSS di base. Quando servono SQL, JavaScript, HTTP, Composer o strumenti di deploy, vengono introdotti nel contesto in cui diventano necessari.

## Come leggere gli esempi

Gli esempi sono pensati per PHP 8.5, con uno stile compatibile con il lavoro quotidiano: tipi espliciti quando aiutano, `declare(strict_types=1)` nei file applicativi, prepared statement per il database, escaping dell'output, password hash sicuri, token generati con `random_bytes()` e configurazione separata dal codice.

Nei capitoli iniziali alcuni esempi restano volutamente piccoli, perché devono isolare un concetto. Nei capitoli di progetto il codice diventa più vicino a un'applicazione reale: validazione, redirect dopo POST, CSRF, sessioni, PDO, autoload, dependency injection e gestione degli errori.

## Convenzioni tipografiche

- I nomi di funzioni, variabili, file, comandi e classi sono scritti in `monospace`.
- I blocchi PHP rappresentano file completi quando iniziano con `<?php`.
- I comandi di terminale indicano ciò che devi digitare.
- Le query SQL sono separate dal codice PHP per rendere chiaro il confine tra database e applicazione.

## Standard di riferimento

La struttura del libro segue le convenzioni comuni dei manuali tecnici: front matter con titolo, copyright, indice, prefazione e introduzione; corpo diviso in parti e capitoli; back matter con checklist, conclusioni e colophon. Ogni capitolo ha un obiettivo pratico, sezioni brevi, esempi eseguibili e un riepilogo finale.
