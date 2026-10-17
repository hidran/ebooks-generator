# Come leggere il libro {.unnumbered}

## In che ordine

Se è la prima volta, leggilo in ordine, dal capitolo 1 al 23. Ogni parte dà per scontato quello che hai visto nelle precedenti: se arrivi alla Photogallery senza aver mai usato Plan Mode o senza sapere cosa ci va in un CLAUDE.md, alcuni passaggi ti sembreranno salti nel vuoto. All'inizio di ogni capitolo i prerequisiti dicono da quali capitoli dipende; se non ce ne sono, puoi leggerlo da solo.

Se usi già Claude Code e ti interessa soprattutto il metodo per i progetti, c'è una strada più corta: leggi il capitolo 2, poi la Parte III (capitoli 7-10), la Parte IV (capitoli 11-15) e salta alla Photogallery (capitolo 17). Perdi l'analisi dati della Parte II e la landing page, che puoi recuperare dopo.

Dopo la prima lettura il libro funziona come riferimento. Le appendici sono fatte apposta: il glossario, il troubleshooting, i prompt pronti, le risorse e il changelog non si leggono dall'inizio alla fine, ci vai quando ti serve qualcosa.

## Convenzioni

Il testo in `carattere monospaziato` è qualcosa da scrivere esattamente così: un comando, un percorso, il nome di un file, un'opzione, un tasto. Se vedi `CLAUDE.md` in questo formato, intendo quel file con quel nome.

I comandi da terminale sono in blocchi come questo, senza il prompt della shell davanti:

```bash
claude --version
```

I blocchi con un'etichetta diversa (`json`, `python`, `markdown`, `text`) contengono codice, configurazioni o il testo di un prompt da incollare in Claude Code. I prompt sono in italiano: Claude li capisce benissimo, e lavorare nella tua lingua ti fa scrivere richieste più precise.

Qua e là trovi dei riquadri. **Suggerimento** è una scorciatoia o un'abitudine che fa risparmiare tempo. **Attenzione** segnala un errore comune o un rischio concreto. **Sotto il cofano** è un approfondimento tecnico che puoi saltare senza perdere il filo. **Esempio** mostra un caso con input e output reali. **Prompt riusabile** è un prompt pronto da adattare ai tuoi progetti.

Ogni capitolo si apre con quello che imparerai e si chiude con un riepilogo e un esercizio. Gli esercizi non sono obbligatori, ma sono il modo più veloce per accorgerti di cosa non ti è chiaro.

## I repository di supporto

Il codice dei progetti è pubblico su GitHub.

`github.com/hidran/claude-code-book-photogallery` contiene la Photogallery della Parte VI. Il branch `main` è il progetto finito; i branch `book/...` fotografano le tappe intermedie, così puoi confrontare il tuo lavoro o ripartire da un punto preciso.

`github.com/hidran/fluentaipro-claude-landingpage` contiene la landing page del capitolo 16, con un branch `book/...` per ogni fase.

`github.com/hidran/claude-code-book-snippets` raccoglie i prompt riusabili capitolo per capitolo e la raccolta completa dell'Appendice C in testo semplice, comoda per il copia e incolla.

::: {.callout .callout-warning}
[Attenzione ai numeri nei nomi dei branch]{.callout-title}

I branch sono stati creati per la prima edizione e portano il numero di capitolo di allora. Per esempio, `book/cap-13-wave-1-backend` corrisponde al capitolo 19 di questa edizione e `book/cap-10-3-execution` al capitolo 16. Nel testo trovi sempre il nome esatto del branch da usare, quindi non devi fare conversioni a mano.
:::

Per segnalare un errore, un comando che non esiste più o un comportamento diverso da quello descritto, apri una issue nel repository `claude-code-book-snippets`. Le segnalazioni verificate finiscono nella revisione successiva e nel changelog dell'Appendice E.

## Aggiornamenti

Claude Code cambia in fretta, e il libro viene aggiornato quando i cambiamenti toccano il modo di lavorare: comandi rinominati, funzioni rimosse, comportamenti diversi dei modelli. Questa è la seconda edizione, aggiornata a ottobre 2026. Su Kindle puoi ricevere le nuove versioni attivando gli aggiornamenti automatici dei libri nelle impostazioni di Amazon (Gestisci contenuti e dispositivi).
