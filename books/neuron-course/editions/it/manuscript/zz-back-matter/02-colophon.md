# Colophon {.unnumbered}

## Versioni

Il codice di questo libro è stato scritto contro, e verificato su:

| Componente | Versione |
|---|---|
| `neuron-core/neuron-ai` | 4.0.2 |
| `neuron-core/neuron-laravel` | 2.0.0 — richiede `neuron-ai` ^4.0 |
| PHP | 8.5 con `ext-curl` per il codice del libro — verificato su 8.5.4 (il pacchetto `neuron-ai` in sé dichiara `^8.1`) |
| Laravel | 13 |
| Modelli Ollama | `llama3.2` (chat), `nomic-embed-text` (embedding) |

Ogni listato PHP del libro è stato compilato con PHP 8.5.4, con tutte le deprecazioni segnalate. Il codice dei repository di accompagnamento, da cui è tratta la maggior parte dei listati, supera PHPStan al livello 8 contro quelle versioni. Anche gli esempi del repository di accompagnamento sono stati eseguiti — contro un modello Ollama locale dove ne serve uno, e contro il fake provider del framework stesso dove non serve; i pochi che richiedono un'infrastruttura che un portatile non fa girare, come un vector store MariaDB, sono stati controllati solo staticamente. I test di contratto del repository di accompagnamento fissano ogni classe, metodo e argomento nominato da cui il libro dipende, così falliscono in modo evidente il giorno in cui una release ne cambia uno.

Gli identificatori di modello che compaiono negli esempi — `claude-sonnet-4-5`, `gpt-4.1-mini`, `gemini-2.0-flash`, `mistral-large-latest` — erano attuali quando sono stati scritti e non lo resteranno. Consulta l'elenco dei modelli del tuo provider invece di fidarti di un libro, incluso questo.

Prima di fare affidamento su un'affermazione riguardo alle versioni in una qualunque di queste pagine:

```bash
composer show neuron-core/neuron-ai
```

## Produzione

Scritto in Markdown. Costruito con pandoc in EPUB3 e in un DOCX da 7,5×9,25 pollici, convertito in PDF con LibreOffice. L'EPUB è validato con epubcheck; la dimensione di pagina del PDF è verificata come esattamente 540 × 666 punti.

Gli strumenti di build sono un piccolo insieme di script di shell e di supporti Python: `bookcfg.py` fa il parsing della configurazione del libro, `make-metadata.py` produce i metadati pandoc per ciascuna edizione, e `fix-pdf-trim.py` allinea il PDF alla dimensione di taglio esatta. Nulla nella pipeline chiama un servizio esterno.

I diagrammi sono in ASCII dentro blocchi di codice delimitati — deliberatamente, così da sopravvivere al riflusso a qualunque dimensione di carattere su qualunque lettore, cosa che nessuna immagine raster fa.

## Edizioni

Pubblicato in inglese, italiano e spagnolo. Le edizioni italiana e spagnola sono traduzioni del testo inglese, governate da un glossario condiviso che fissa come invariabili i nomi di prodotti, pacchetti, classi e comandi.

Le due traduzioni divergono deliberatamente su un punto. L'italiano assorbe il vocabolario tecnico inglese così com'è — *il tool*, *il workflow*, *l'embedding* — che è il modo in cui scrive la professione in Italia. Lo spagnolo lo traduce: *herramienta*, *flujo de trabajo*, *incrustación*, *transmisión*, *proveedor*, *fragmento*. Lì sopravvivono in inglese solo `prompt`, `token` e `middleware`, nessuno dei quali ha un equivalente spagnolo consolidato.

Il codice è identico in tutte e tre le edizioni. Commenti, stringhe letterali e identificatori non vengono mai tradotti.

## Correzioni

Il software si muove. Se trovi in questo libro qualcosa che non corrisponde più alla libreria, l'Appendice A spiega come determinare che cosa sia davvero vero sulla tua installazione — che è la risposta che questo libro ti darebbe comunque.

## Sull'autore

Hidran Arias costruisce e insegna sistemi PHP. Questo libro è nato da un corso in ventitré moduli sullo stesso materiale, e dalla convinzione che la conversazione sull'AI agentica si sia svolta quasi interamente in Python per ragioni che non hanno nulla a che vedere con dove il lavoro si trova davvero.

---

*Agentic AI in PHP con NeuronAI*
Prima edizione, 2026
