# Capitolo 5. Da CSV a Excel, report tabellari con Python

**Cosa imparerai.** In questo capitolo prendi il CSV del Capitolo 4 e lo trasformi in un file Excel da consegnare: intestazioni formattate, un foglio di riepilogo con totali in formula, un grafico, e uno script che rigeneri il mese dopo con un comando. Il lavoro lo fa uno script Python con openpyxl, scritto da Claude e raffinato in quattro round di prompt.

**Prerequisiti.** Python 3 con `pip` e il file `saas_metrics.csv` del Capitolo 4 nella cartella `data/` del progetto. Qualunque CSV con dati strutturati va bene lo stesso, ma dovrai adattare i nomi delle colonne nei prompt.

Ogni piattaforma di Business Intelligence promette di mandare in pensione Excel, ed Excel resta lì. Tableau, Power BI, Looker e Metabase funzionano bene, ma chiedono account e configurazione. Excel invece il responsabile commerciale ce l'ha già aperto sul laptop, e il cliente apre l'allegato senza installare nulla. Se consegni un `.xlsx` ben fatto, non chiedi a nessuno di cambiare strumento.

Il guaio è che un Excel decente costa fatica. `df.to_excel()` di pandas produce un foglio piatto, senza formattazione né formule. Un report da mandare a un cliente ha intestazioni colorate, colonne della larghezza giusta, righe alternate, un foglio di riepilogo e uno con i grafici. A mano ci vogliono ore, e scriverlo in codice vuol dire studiarsi le API di openpyxl o xlsxwriter, che non sono le più amichevoli.

Con Claude Code il flusso diventa questo: descrivi il report che vuoi, Claude scrive lo script, tu lo lanci e apri il file. Se qualcosa non ti piace, scrivi un altro prompt. E lo script resta nel repository, versionato: il mese dopo, con un CSV nuovo o per un'altra regione, lo rilanci con un argomento diverso e hai lo stesso report aggiornato.

## 5.1 Perché passare da uno script Python

Excel importa un CSV da solo, e mezzo mondo ha un pulsante "esporta in xlsx". Lo script in mezzo si giustifica per tre ragioni.

La prima è la ripetibilità. L'esportazione manuale la rifai a ogni aggiornamento del dataset, sempre con gli stessi clic. Lo script lo scrivi una volta e poi lo lanci.

La seconda è la trasformazione. Un CSV grezzo quasi mai è pronto per un report: ci sono colonne da rinominare, date da convertire, aggregazioni da calcolare. pandas fa tutto questo in poche righe prima ancora di aprire il file Excel. L'alternativa è rifare gli stessi passaggi dentro Excel a ogni aggiornamento.

La terza riguarda il file che ottieni. Excel che importa un CSV produce valori. Uno script con openpyxl può scrivere formule. Un totale calcolato in Python è un numero fisso, un totale scritto come `=SUM(...)` si ricalcola quando qualcuno cambia i dati. La sezione 5.4 è dedicata a questa differenza.

### La pipeline in quattro passi

1. Parti da un CSV con dati grezzi. Qui usiamo `data/saas_metrics.csv`, lo stesso dataset del Capitolo 4: sei mesi di metriche di un prodotto SaaS, con le colonne `month` (1-6), `date`, `plan` (free, silver, gold), `region` (Europe, North America, Asia Pacific), `mrr` e le altre che hai già esplorato.
2. Chiedi a Claude uno script Python. Il prompt descrive il file di input, quello di output, i fogli che vuoi, lo stile delle intestazioni e le aggregazioni. Claude scrive lo script in un colpo solo, con gli import, la gestione degli errori e i commenti.
3. Lo script usa openpyxl, la libreria Python più diffusa per creare e modificare file `.xlsx`. Non serve Excel installato: openpyxl scrive il formato direttamente e funziona allo stesso modo su macOS, Linux e Windows.
4. Lanci lo script e apri il file con Excel, LibreOffice Calc o Numbers.

```bash
python tools/genera_excel.py
```

### openpyxl o xlsxwriter

Le due librerie si sovrappongono parecchio, ma hanno priorità diverse. openpyxl legge e modifica file esistenti oltre a crearne di nuovi: è quella giusta quando devi aggiornare un template, aggiungere un foglio a un file che ti hanno mandato o leggere i dati da un Excel ricevuto. xlsxwriter scrive soltanto, in compenso ha un'API più comoda per i grafici, la formattazione condizionale e le tabelle Excel. Nessuna delle due crea tabelle pivot native di Excel: la pivot la calcoli con pandas e la scrivi come una tabella normale, ed è quello che faremo.

Se nel prompt nomini la libreria, Claude usa quella. Se non la nomini, la scelta la fa lui: meglio dirlo e non avere sorprese quando aggiorni `requirements.txt`.

## 5.2 Il primo prompt

Apri il terminale nella cartella del progetto e avvia Claude Code:

```bash
claude
```

Il primo prompt deve dire tre cose: dove sono i dati, dove va l'output e come è fatto il file. Non serve essere esaustivi, i dettagli arrivano con l'iterazione, ma più contesto dai e migliore è la base da cui parti.

```text
Leggi il file data/saas_metrics.csv. Scrivi uno script Python
tools/genera_excel.py che crea un file output/report.xlsx con i dati
come tabella formattata.

Requisiti:
- Una singola sheet "Dati" con tutte le colonne del CSV
- Intestazione con sfondo blu scuro (#1F4E78) e testo bianco in grassetto
- Larghezza delle colonne adattata automaticamente al contenuto
- Prima riga bloccata (freeze pane) per lo scroll
- Installa pandas e openpyxl se mancano e aggiungili a requirements.txt
```

Claude legge il CSV, ricava colonne, tipi e numero di righe, poi scrive lo script. In auto mode, la modalità predefinita, il classificatore lascia passare le azioni coerenti con la richiesta, quindi Claude crea il file e installa le dipendenze senza fermarsi a ogni passo. Se preferisci vedere ogni diff prima che venga scritto, passa alla modalità manuale con `Shift+Tab` (il Capitolo 11 descrive tutte le modalità).

Per un prompt di questa lunghezza ha senso anche partire da Plan Mode, come hai fatto nel Capitolo 4: premi `Shift+Tab` finché la barra di stato mostra `plan mode on`, oppure avvia la sessione con `claude --permission-mode plan`. Claude esplora il CSV, ti propone la struttura dello script e non tocca nulla finché non approvi.

![Plan Mode su una richiesta simile scritta in inglese: Claude esplora il CSV prima di proporre lo script con i fogli dati, riepilogo e grafici.](figures/cap-05/fig-02.png)

<!-- VERIFY: fig-02 shows Plan Mode entered with `/plan` and an older model name in the status bar. FACTS-verified lists `/plan [description]`; confirm /plan still exists, otherwise reshoot with Shift+Tab and an Italian prompt. -->

### Cosa esce dal primo round

Lo script è diviso in funzioni: una carica il CSV in un DataFrame pandas, una crea il workbook e il foglio, una scrive le intestazioni con lo stile richiesto, una scrive i dati e calcola la larghezza delle colonne, e una `main()` mette insieme il tutto e salva il file.

La parte che formatta l'intestazione ha questo aspetto:

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

header_fill = PatternFill(
    start_color="1F4E78",
    end_color="1F4E78",
    fill_type="solid"
)
header_font = Font(bold=True, color="FFFFFF")

for col_idx, column_name in enumerate(df.columns, start=1):
    cell = ws.cell(row=1, column=col_idx, value=column_name)
    cell.fill = header_fill
    cell.font = header_font
    cell.alignment = Alignment(horizontal="center")
```

E questa è la larghezza automatica delle colonne:

```python
for col_idx, column in enumerate(df.columns, start=1):
    max_length = max(
        len(str(column)),
        df[column].astype(str).map(len).max()
    )
    ws.column_dimensions[get_column_letter(col_idx)].width = max_length + 4
```

Lanci lo script e trovi `report.xlsx` nella cartella `output/`:

```bash
python tools/genera_excel.py
```

<!-- TODO screenshot: the "Dati" sheet of output/report.xlsx open in LibreOffice Calc or Excel after round 1 (blue header, frozen first row). Old fig-01 dropped: it showed tools/generate_report_pdf.py from the PDF chapter. -->

### I difetti del primo giro

Il file si apre, le intestazioni sono blu, le colonne hanno una larghezza sensata. Guardandolo con occhio critico, però, qualcosa manca.

La colonna `date` arriva come testo. `2025-01-01` nel CSV è una stringa, pandas la lascia così se non gli chiedi `parse_dates`, ed Excel la tratta come testo: il filtro per data non funziona e l'ordinamento è alfabetico.

Anche i numeri vanno controllati. Basta un valore sporco nel CSV perché `mrr` venga letta come stringa, e a quel punto Excel non la somma.

Mancano i totali: il foglio mostra i dati grezzi e nient'altro. E manca la pivot: se vuoi il ricavo per piano e per mese, te la devi costruire a mano.

## 5.3 Iterare fino al report

Il metodo è semplice: apri il file, guardi cosa manca o cosa non va, e scrivi un prompt che descrive solo quelle modifiche. Ogni round sistema un aspetto. Il primo prompt serviva a sbloccare il lavoro e ad avere qualcosa di concreto da correggere, quindi non doveva essere perfetto.

### Round 2: il foglio Riepilogo

```text
Lo script genera la sheet Dati correttamente. Adesso aggiungi:

1. Una seconda sheet "Riepilogo" con una tabella pivot dove:
   - Le righe sono i mesi (ordinati cronologicamente)
   - Le colonne sono i piani di abbonamento (free, silver, gold)
   - I valori sono la somma del MRR (Monthly Recurring Revenue)
   - Ultima riga: totale per colonna

2. Nella sheet Dati, assicurati che la colonna mrr venga scritta
   come numero (float), non come stringa, e che la colonna date
   sia una data Excel vera.
```

Claude aggiunge una funzione `write_summary_sheet()`, calcola la pivot con `pivot_table()` di pandas e scrive il risultato nel foglio Riepilogo con lo stesso stile di intestazione. Aprendo il file vedi subito quanto rende ogni piano mese per mese, con il totale per piano in fondo.

### Round 3: filtri e totali in formula

Nel round 2 i totali sono numeri calcolati da Python. Ora li vuoi come formule.

```text
Adesso voglio filtri automatici su ogni colonna della sheet Dati, e
nella sheet Riepilogo i totali in fondo devono essere formule SUM
invece di valori hardcoded calcolati da Python.

La formula nella cella B[ultima_riga] della sheet Riepilogo deve sommare
la colonna B dalla riga 2 in su, così: =SUM(B2:B{n}).
```

Claude aggiorna lo script così:

```python
# Filtri automatici sulla sheet Dati
ws_dati.auto_filter.ref = ws_dati.dimensions

# Formule SUM nella riga totali della sheet Riepilogo
last_row = len(pivot_df) + 1  # +1 per l'intestazione
for col_idx in range(2, len(pivot_df.columns) + 2):
    col_letter = get_column_letter(col_idx)
    total_cell = ws_riepilogo.cell(row=last_row + 1, column=col_idx)
    total_cell.value = f"=SUM({col_letter}2:{col_letter}{last_row})"
    total_cell.font = Font(bold=True)
```

Ora ogni intestazione della sheet Dati ha l'icona del filtro, e le celle dei totali del Riepilogo contengono formule. Attenzione a cosa ricalcolano: sommano le celle del Riepilogo, che restano valori scritti da Python. Se qualcuno corregge un valore nel Riepilogo, il totale si aggiorna; se lo corregge nella sheet Dati, no. Per collegare i due fogli servono formule che leggono la sheet Dati, e le trovi nella sezione 5.4.

L'autofiltro non è una Tabella Excel vera e propria, quella con nome e stile che vedi in Inserisci, Tabella. Se ti serve, chiedila esplicitamente: openpyxl la crea con `openpyxl.worksheet.table.Table`.

### Round 4: righe alternate e grafico a torta

```text
Nella sheet Dati, colora le righe pari con sfondo grigio chiarissimo
(#F2F2F2) per il pattern zebra. Nella sheet Riepilogo aggiungi un
grafico a torta che mostra la distribuzione del revenue totale per piano.
```

Per le righe alternate Claude aggiunge un ciclo sulle righe della sheet Dati:

```python
zebra_fill = PatternFill(
    start_color="F2F2F2",
    end_color="F2F2F2",
    fill_type="solid"
)

for row_idx, row in enumerate(ws_dati.iter_rows(min_row=2), start=2):
    if row_idx % 2 == 0:
        for cell in row:
            cell.fill = zebra_fill
```

Per la torta, i dati giusti sono nella riga dei totali: una fetta per piano.

```python
from openpyxl.chart import PieChart, Reference

total_row = last_row + 1
last_col = len(pivot_df.columns) + 1

pie = PieChart()
labels = Reference(ws_riepilogo, min_col=2, max_col=last_col, min_row=1)
data = Reference(ws_riepilogo, min_col=2, max_col=last_col, min_row=total_row)
pie.add_data(data, from_rows=True, titles_from_data=False)
pie.set_categories(labels)
pie.title = "Revenue per piano"
ws_riepilogo.add_chart(pie, "G2")
```

::: {.callout .callout-tip}
[Suggerimento]{.callout-title}

Controlla sempre da dove un grafico prende i dati. Nel Riepilogo i mesi stanno sulle righe e i piani sulle colonne: una torta costruita su una colonna mostra come si distribuisce un solo piano nei sei mesi, che è un grafico diverso da quello che hai chiesto. Se le fette sono sei invece di tre, Claude ha preso la colonna: diglielo e fagli usare la riga dei totali con `from_rows=True`.
:::

<!-- TODO screenshot: the "Riepilogo" sheet after round 4, with the SUM totals row and the pie chart with three slices (free, silver, gold). -->

## 5.4 Formule vive e valori fissi

Quando generano Excel da codice, molti sviluppatori non pensano a cosa farà chi riceve il file. A vederli, un report con valori fissi e uno con formule sono identici; la differenza salta fuori quando il destinatario modifica una cella.

### Il report con valori fissi

Ogni cella contiene un numero calcolato da Python. Chi apre il file vede tutto corretto, ma se modifica un valore il resto non si muove: i totali restano quelli, le medie pure, il grafico mostra i numeri di prima.

Per aggiornarlo devono tornare da te: correggi il CSV, rilanci lo script e mandi un file nuovo. E se il destinatario vuole fare un'ipotesi del tipo "e se alzassimo del 10% il prezzo del piano gold?", da solo non può.

### Il report con formule

Le celle dei totali non contengono 12500 ma `=SUM(B2:B7)`. Le percentuali non contengono 0,23 ma `=B8/E8`. I grafici sono collegati alle celle, quindi si aggiornano quando un valore cambia.

Chi lo riceve ha in mano uno strumento: modifica i dati nella sheet Dati, passa al Riepilogo e vede i totali cambiare. L'ipotesi sul piano gold se la fa da solo, senza chiamarti.

### Come chiedere le formule a Claude

Devi essere esplicito. Se non lo chiedi, Claude tende a calcolare i valori in Python e scriverli come numeri, che è la strada più semplice e con meno possibilità di sbagliare un riferimento. Per avere le formule, scrivilo:

```text
Nella sheet Riepilogo, usa formule Excel invece di valori calcolati in Python.
Le celle della pivot e dei totali devono contenere formule SUMIFS o SUM che
fanno riferimento alle celle della sheet Dati. I valori devono aggiornarsi
automaticamente se l'utente modifica i dati.
```

Con questo prompt ogni cella della pivot diventa una `SUMIFS` che legge la sheet Dati: somma `mrr` dove il mese è quello della riga e il piano è quello della colonna.

```python
mrr_col = get_column_letter(df.columns.get_loc("mrr") + 1)
plan_col = get_column_letter(df.columns.get_loc("plan") + 1)

# B2: MRR del mese in A2 per il piano in B1
ws_riepilogo["B2"] = (
    f"=SUMIFS(Dati!{mrr_col}:{mrr_col},"
    f"Dati!A:A,$A2,"
    f"Dati!{plan_col}:{plan_col},B$1)"
)
```

La sintassi `NomeFoglio!Colonna` è la stessa che useresti a mano in Excel. Ricavare le lettere da `df.columns` evita il classico errore di scrivere `Dati!G:G` e scoprire che nel CSV del mese dopo la colonna `mrr` si è spostata. Una somma semplice per un singolo piano sull'intera colonna si scrive allo stesso modo:

```python
cell.value = f'=SUMIF(Dati!{plan_col}:{plan_col},"gold",Dati!{mrr_col}:{mrr_col})'
```

### Quando usare le formule

Le formule non servono sempre. Se il file è generato in automatico e nessuno lo apre per modificarlo, il valore fisso va benissimo: è più facile da scrivere e non rischi riferimenti sbagliati.

Valgono quando il destinatario usa Excel con una certa dimestichezza e vuole lavorarci sopra, e quando il report ha una vita lunga, aggiornato ogni mese con dati nuovi. Su un report letto una volta e archiviato sono lavoro sprecato.

Una regola pratica: se il file va a un manager o a un cliente che "lavora in Excel", metto le formule. Se va a un sistema automatico o a un ingegnere che ne estrae i dati con il codice, bastano i valori.

### Excel, Google Sheets o un database

Excel è il formato giusto quando il destinatario lavora con allegati, magari offline, e il documento deve stare tutto in un file senza dipendere da servizi esterni. Vale anche quando chi lo riceve conosce Excel e non ha voglia di imparare altro.

Google Sheets ha senso quando più persone lavorano sullo stesso documento in contemporanea, o quando vuoi un report sempre aggiornato senza spedire file nuovi. Si genera da codice con le API di Google Sheets, con un approccio simile a quello di questo capitolo, ma con credenziali (un service account o OAuth) al posto di una libreria che scrive un file locale.

Un database, o una piattaforma BI, serve quando i dati sono troppi per Excel (il limite è 1.048.576 righe per foglio, e il file diventa lento molto prima), quando le query devono girare veloci su anni di storico, o quando più sistemi leggono gli stessi dati. In quei casi Excel diventa il punto in cui presenti il risultato di qualche query, e i dati vivono altrove.

Per il caso di questo capitolo, un report periodico su dati aziendali per persone che non scrivono codice, Excel è la scelta corretta. Il Capitolo 6 aggiunge grafici, una dashboard web e un report PDF, e discute quando scegliere ciascuno.

## 5.5 Parametri e scheduling

Uno script che funziona su un solo file con il nome scritto nel codice è ancora un prototipo. Per riusarlo deve accettare parametri.

### Aggiungere argparse

```text
Aggiungi argparse allo script. I parametri devono essere:
- --input: percorso del CSV (default: data/saas_metrics.csv)
- --output: percorso del file Excel di output (default: output/report.xlsx)
- --region: filtra i dati per regione (opzionale, se non specificato usa tutti i dati)
- --months: lista di mesi da includere, come numeri da 1 a 6 (opzionale, default: tutti)

Se il file di input non esiste, lo script deve uscire con un messaggio
di errore chiaro. Se la cartella di output non esiste, deve crearla.
```

Claude aggiunge il blocco argparse classico:

```python
import argparse
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Genera un report Excel da un CSV di metriche SaaS"
    )
    parser.add_argument(
        "--input",
        default="data/saas_metrics.csv",
        help="Percorso del file CSV sorgente"
    )
    parser.add_argument(
        "--output",
        default="output/report.xlsx",
        help="Percorso del file Excel di output"
    )
    parser.add_argument(
        "--region",
        default=None,
        help="Filtra per regione (es. Europe, North America)"
    )
    parser.add_argument(
        "--months",
        nargs="+",
        type=int,
        default=None,
        help="Mesi da includere (es. 1 2 3)"
    )
    return parser.parse_args()
```

Adesso lo script si lancia con parametri espliciti:

```bash
python tools/genera_excel.py \
  --input data/saas_metrics.csv \
  --output output/report_europe_q1.xlsx \
  --region Europe \
  --months 1 2 3
```

<!-- TODO screenshot: terminal running the command above, plus `python tools/genera_excel.py --help` showing the four options. -->

### Nome del file con la data

Per non sovrascrivere i report precedenti, fai mettere il mese nel nome del file:

```text
Se --output non è specificato, usa un nome automatico nel formato
report_YYYY-MM.xlsx basato sul mese corrente.
```

Claude porta il default di `--output` a `None` e aggiunge:

```python
from datetime import datetime

if not args.output:
    timestamp = datetime.now().strftime("%Y-%m")
    output_path = Path(f"output/report_{timestamp}.xlsx")
else:
    output_path = Path(args.output)

output_path.parent.mkdir(parents=True, exist_ok=True)
```

Se lasciasse `default="output/report.xlsx"`, `args.output` non sarebbe mai vuoto e il ramo con la data non scatterebbe mai: è il genere di dettaglio da controllare nel diff.

### Scheduling con cron (macOS e Linux)

Una volta parametrizzato, lo script può girare da solo. Su macOS e Linux il modo più semplice è cron. Per lanciarlo il primo di ogni mese alle 8:00 apri il crontab:

```bash
crontab -e
```

e aggiungi questa riga:

```text
0 8 1 * * cd /percorso/assoluto/progetto && /usr/bin/python3 tools/genera_excel.py >> /tmp/genera_excel.log 2>&1
```

Il `cd` serve perché cron parte dalla tua home, e i percorsi di default dello script (`data/saas_metrics.csv`, `output/`) sono relativi alla cartella del progetto. Se usi un virtualenv, sostituisci `/usr/bin/python3` con il Python del virtualenv, per esempio `.venv/bin/python`. `>> /tmp/genera_excel.log 2>&1` manda stdout e stderr in un file di log, così quando qualcosa va storto sai dove guardare.

### Scheduling con Task Scheduler (Windows)

Su Windows l'equivalente è l'Utilità di pianificazione (Task Scheduler). Il cmdlet PowerShell `New-ScheduledTaskTrigger` non ha un'opzione mensile, quindi conviene `schtasks`. Prima crea nel progetto un file `genera_report.bat` che si sposta nella cartella giusta:

```bat
@echo off
cd /d C:\percorso\progetto
python tools\genera_excel.py >> output\genera_excel.log 2>&1
```

Poi registra l'attività per il primo di ogni mese alle 8:00:

```powershell
schtasks /Create /SC MONTHLY /D 1 /ST 08:00 /TN "GeneraReportExcel" /TR "C:\percorso\progetto\genera_report.bat"
```

Se il computer deve restare spento, le routine di Claude Code eseguono un agent nel cloud su un calendario o su un evento GitHub (`/schedule` le crea con una conversazione guidata); per uno script deterministico come questo, però, cron o Task Scheduler bastano.

### Invio automatico via email

Se vuoi che il report arrivi in casella senza toccare niente, chiedi a Claude un flag `--email`:

```text
Aggiungi un parametro opzionale --email. Se specificato, dopo aver generato
il file Excel invia un'email all'indirizzo indicato con il file in allegato.
Usa smtplib e le variabili d'ambiente SMTP_HOST, SMTP_USER, SMTP_PASSWORD
per le credenziali.
```

::: {.callout .callout-warning}
[Attenzione]{.callout-title}

cron non carica il profilo della tua shell, quindi le variabili `SMTP_*` che hai esportato in `.zshrc` o `.bashrc` lì non esistono. Falle leggere allo script da un file `.env` escluso da Git, oppure definiscile in cima al crontab. In nessun caso la password va scritta dentro lo script.
:::

Per scenari più articolati, come una notifica su Slack, il caricamento su Google Drive o un webhook, conviene un servizio come Make o Zapier che riceve il file, invece di far crescere lo script Python.

::: {.callout .callout-prompt}
[Prompt riusabile]{.callout-title}

Excel report con pivot e formule. Sostituisci i segnaposto tra parentesi angolari con i nomi del tuo dataset.

```text
Leggi <file_csv>. Scrivi uno script Python tools/genera_excel.py che genera
<output.xlsx> con:

1. Sheet "Dati": tutti i dati del CSV come tabella filtrabile (auto_filter),
   intestazione con sfondo blu scuro (#1F4E78) e testo bianco in grassetto,
   larghezza colonne adattata al contenuto, freeze sulla prima riga,
   zebra striping sulle righe pari (#F2F2F2).

2. Sheet "Riepilogo": tabella pivot con <campo_righe> come righe e
   <campo_colonne> come colonne, valori = somma di <metrica>.
   Riga dei totali con formule SUM, non valori hardcoded.

3. Sheet "Grafici": un line chart per <metrica_temporale> nel tempo
   suddiviso per <segmentazione>, un pie chart per la distribuzione
   totale di <metrica> per <segmentazione>.

Usa openpyxl. Aggiungi argparse con --input, --output, --region (opzionale).
Se --output non specificato, usa report_YYYY-MM.xlsx con timestamp automatico.
Installa le dipendenze e aggiorna requirements.txt.
```
:::

<!-- TODO screenshot: old fig-03 dropped (VS Code with ReportLab PDF code from the PDF chapter). A replacement here could show the finished workbook with its three sheets. -->

## Riepilogo

- Per un Excel che dovrai rifare, fai scrivere a Claude uno script Python: lo rilanci, lo parametrizzi e lo tieni in Git.
- openpyxl legge e scrive, xlsxwriter scrive soltanto ma ha un'API più comoda per grafici e formattazione condizionale; la pivot in entrambi i casi la calcoli con pandas.
- Procedi per round: tabella formattata, poi riepilogo, poi totali in formula, poi grafici e righe alternate. Dopo ogni round apri il file e controlla, grafici compresi.
- Le formule servono solo se puntano ai dati che l'utente modifica: per un Riepilogo che segue la sheet Dati chiedi `SUMIFS` che la leggono.
- Con argparse e un nome file con la data lo script è pronto per cron o Task Scheduler; ricordati del `cd` nella cartella del progetto.

## Esercizio

Prendi `data/saas_metrics.csv` del Capitolo 4, o un altro CSV con dati strutturati, e ripercorri il capitolo in circa 20 minuti:

1. Lancia il primo prompt della sezione 5.2 e ottieni la sheet Dati formattata.
2. Aggiungi il foglio Riepilogo con la pivot (round 2).
3. Sostituisci i totali calcolati da Python con formule `SUM` (round 3).
4. Aggiungi argparse con `--input` e `--output`.

L'esercizio è finito quando lanci lo script su un secondo CSV con le stesse colonne, senza toccare il codice, e nel nuovo file la riga dei totali del Riepilogo contiene formule (clicca su una cella: nella barra della formula devi vedere `=SUM(...)`).

Branch di riferimento: `cap-04-excel-report` nel repository claude-code-book-snippets.
