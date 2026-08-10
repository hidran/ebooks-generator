# Colophon {.unnumbered}

## Versioni

Il codice di questo libro è stato scritto contro:

| Componente | Versione |
|---|---|
| `neuron-core/neuron-ai` | ^3.x — la v3 è la stabile corrente |
| `neuron-core/neuron-laravel` | ^1.3 — la 1.3.0 richiede `neuron-ai: ^3.15` |
| PHP | 8.1+ per il pacchetto core, 8.2+ per l'SDK Laravel |
| Laravel | dalla 10 alla 13 |
| Modelli Ollama | `qwen2.5:7b` (chat), `nomic-embed-text` (embedding) |

Gli identificatori di modello che compaiono negli esempi — `claude-sonnet-4-5`, `gpt-4.1-mini`, `gemini-2.0-flash`, `mistral-large-latest` — erano attuali quando sono stati scritti e non lo resteranno. Consulta l'elenco dei modelli del tuo provider invece di fidarti di un libro, incluso questo.

Prima di fare affidamento su un'affermazione riguardo alle versioni in una qualunque di queste pagine:

```bash
composer show neuron-core/neuron-ai --all
```

## Produzione

Scritto in Markdown. Costruito con pandoc in EPUB3 e in un DOCX da 6×9 pollici, convertito in PDF con LibreOffice. L'EPUB è validato con epubcheck; la dimensione di pagina del PDF è verificata come esattamente 432 × 648 punti.

Gli strumenti di build sono un piccolo insieme di script di shell e di supporti Python: `bookcfg.py` fa il parsing della configurazione del libro, `make-metadata.py` produce i metadati pandoc per ciascuna edizione, e `fix-pdf-trim.py` allinea il PDF alla dimensione di taglio esatta. Nulla nella pipeline chiama un servizio esterno.

I diagrammi sono in ASCII dentro blocchi di codice delimitati — deliberatamente, così da sopravvivere al riflusso a qualunque dimensione di carattere su qualunque lettore, cosa che nessuna immagine raster fa.

## Edizioni

Pubblicato in inglese, italiano e spagnolo. Le edizioni italiana e spagnola sono traduzioni del testo inglese, governate da un glossario condiviso che fissa come invariabili i nomi di prodotti, pacchetti, classi e comandi e mantiene in inglese il vocabolario di settore consolidato — prompt, token, tool, agent, workflow, embedding, streaming.

Il codice è identico in tutte e tre le edizioni. Commenti, stringhe letterali e identificatori non vengono mai tradotti.

## Correzioni

Il software si muove. Se trovi in questo libro qualcosa che non corrisponde più alla libreria, l'Appendice A spiega come determinare che cosa sia davvero vero sulla tua installazione — che è la risposta che questo libro ti darebbe comunque.

## Sull'autore

Hidran Arias costruisce e insegna sistemi PHP. Questo libro è nato da un corso in ventitré moduli sullo stesso materiale, e dalla convinzione che la conversazione sull'AI agentica si sia svolta quasi interamente in Python per ragioni che non hanno nulla a che vedere con dove il lavoro si trova davvero.

---

*Agentic AI in PHP con NeuronAI*
Prima edizione, 2026
