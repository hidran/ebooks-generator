# Prefazione {.unnumbered}

## Perché questo libro

La prima volta che ho costruito qualcosa di serio con Claude Code ho passato tre ore a cercare su Google.

Il problema non era difficile. Cercavo cose banali: come impostare un progetto perché Claude non perdesse il filo dopo cinquanta messaggi, perché il comando visto in un tutorial non esisteva più nella versione che avevo davanti, come farlo lavorare su più file senza incollare ogni volta il contenuto. Ho girato tra documentazione non aggiornata, thread di Reddit e video di dodici minuti in cui l'autore presentava come metodo il fatto di chiedere a Claude di scrivere codice.

Se qualcuno quella sera mi avesse spiegato quello che ho scoperto nei mesi successivi, avrei finito in mezz'ora. Questo libro è la spiegazione che avrei voluto.

Da allora uso Claude Code ogni giorno, per lavoro e per i miei progetti: script Python che generano report Excel per un cliente, landing page, automazioni, tool interni, fino a un'applicazione full-stack con autenticazione, upload su S3, pannello admin e deploy su AWS. L'ho usato con Python, JavaScript e PHP, su repository piccoli e su codebase da centinaia di file, da solo e in team.

La cosa che ho imparato è che il salto da "ho fatto due esperimenti" a "ho un progetto in produzione" dipende poco dai comandi. Dipende da come lavori: come imposti una sessione, quando pianifichi e quando no, cosa metti in CLAUDE.md, quando un compito merita un agent separato, come verifichi quello che l'agente ha fatto. I comandi cambiano quasi ogni settimana. Queste abitudini restano utili molto più a lungo, ed è su queste che il libro insiste.

## Per chi è

Per chi scrive codice almeno una volta a settimana, in qualunque linguaggio: sviluppatori front-end e back-end, chi scrive script e automazioni, data analyst che si costruiscono i propri report.

Per chi ha già provato ChatGPT, Copilot o Cursor per riscrivere una funzione o spiegare un errore, ma non ha mai portato a termine un progetto intero con un agente. Non sa bene quanto fidarsi dell'output, né come farlo entrare nel modo in cui lavora già.

Per chi vuole un metodo ripetibile. Trucchi online se ne trovano quanti ne vuoi; un procedimento che funziona anche la decima volta, su un progetto diverso, è più raro.

Probabilmente non è il libro giusto per tre tipi di lettore. Il manager che vuole sapere se Claude Code sostituisce gli sviluppatori: la risposta è no, e il libro è scritto per chi il codice lo scrive. Chi cerca un'analisi accademica dei modelli linguistici o un confronto rigoroso tra agenti: quel libro esiste, ma non è questo. E chi non ha mai aperto un terminale: Claude Code presuppone le basi, una variabile, un ciclo, un comando da shell. Se sei a quel punto, fai prima un corso introduttivo di Python o JavaScript e poi torna qui.

## Come è organizzato

Il libro segue una curva precisa: ogni parte usa quello che hai imparato nelle precedenti.

La **Parte I** (capitoli 1-3) installa Claude Code, spiega come lavora un agente dentro il terminale e come scrivere prompt che ottengono il risultato al primo o al secondo tentativo. La Parte II (capitoli 4-6) applica tutto all'analisi di dati reali: un CSV, un report Excel, grafici, una dashboard e un PDF. La Parte III (capitoli 7-10) estende Claude Code con CLAUDE.md, custom command, skill e agent. La Parte IV (capitoli 11-15) è nuova in questa edizione: permessi e sandbox, hook, MCP, plugin, gestione del contesto e della memoria. La Parte V (capitolo 16) è il primo progetto completo, una landing page dal mockup al deploy su Firebase. La Parte VI (capitoli 17-23) è il progetto principale, la Photogallery: specifiche, Spec Driven Development, esecuzione a ondate, review, QA e deploy su AWS con CloudFormation.

In fondo trovi cinque appendici da tenere a portata di mano: glossario, troubleshooting, prompt pronti, risorse e changelog.

## Cosa cambia nella seconda edizione

La prima edizione, uscita a maggio 2026, descriveva Claude Code con Claude Opus 4.7 e Sonnet 4.6. Cinque mesi dopo molte cose sono diverse: il modello predefinito è Claude Opus 5.5 con un milione di token di contesto, Claude Code parte in auto mode e chiede conferma molto meno spesso, i custom command sono confluiti nelle skill, la procedura guidata `/agents` non esiste più, la code review è integrata, si possono far lavorare più sessioni in parallelo su worktree separati.

Ho aggiornato ogni capitolo a ottobre 2026 e ne ho aggiunti sette: il capitolo 2 sul funzionamento di un agente, i cinque capitoli della Parte IV e il capitolo 20 sulle wave in parallelo. Il capitolo 22 ora mette a confronto la review integrata di Claude Code con quella fatta da un secondo modello. Ho anche riscritto il testo da capo a fondo, togliendo ripetizioni e formule di comodo, perché un libro tecnico deve far risparmiare tempo a chi lo legge. L'elenco completo delle modifiche è nell'Appendice E.

Molte delle novità le ho prima registrate come lezioni del mio corso su Claude Code, poi le ho portate qui. Se hai seguito il corso, riconoscerai il progetto di laboratorio della Parte IV.

## Cosa cambierà mentre leggi

Claude Code esce con nuove versioni quasi ogni giorno. Mentre leggi, qualche comando avrà cambiato nome, qualche opzione sarà sparita e ne saranno arrivate altre. Dove una cosa è particolarmente instabile, come il nome del modello predefinito, il testo ti dice come controllarla sulla tua installazione invece di fidarti della pagina stampata.

Il metodo invece regge: specifiche scritte, criteri di accettazione verificabili, vincoli imposti con permessi e hook invece che con raccomandazioni, review prima del merge. Le novità che arriveranno si inseriscono in questo flusso.

## Ringraziamenti

Grazie ad Anthropic, che ha costruito uno strumento abbastanza ricco da meritare un libro intero.

Grazie a Jesse Vincent e alla community di Superpowers per il plugin, le idee e le discussioni che hanno influenzato la Parte III.

Grazie agli studenti del mio corso online, che hanno lavorato sulle versioni preliminari di questi capitoli, hanno trovato gli errori più imbarazzanti prima che li trovassi tu e hanno fatto le domande che mi hanno convinto ad aggiungere sezioni che non avevo previsto. E grazie ai lettori della prima edizione che mi hanno scritto: molte correzioni di questa edizione vengono da loro.

Grazie ai miei colleghi di Spryker per i pomeriggi di pair programming con l'AI, da cui sono nati più esempi di quanti ne citi.

Grazie alla mia famiglia, che per molte sere ha sopportato i miei "ancora cinque minuti e vengo a cena".

Hidran Arias, ottobre 2026
