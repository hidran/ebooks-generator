# Capitolo 6. Grafici, dashboard e report PDF

::: {.chapter-goals}
[Cosa imparerai]{.callout-title}

Dallo stesso CSV dei capitoli 4 e 5 tiri fuori tre cose diverse: una serie di grafici matplotlib pronti per le slide, una piccola dashboard web con Flask e Chart.js, un report PDF generato con ReportLab. Poi vedi come scegliere il formato in base a chi lo legge, e come l'intera pipeline può diventare una skill, l'argomento del capitolo 9.

[Prerequisiti]{.callout-title}

I capitoli 4 e 5 (stesso progetto, stesso `data/saas_metrics.csv`), Python 3 e un browser.

:::

Hai un CSV con le metriche mensili di un prodotto SaaS: MRR, churn, piani, regioni, utilizzo delle feature. L'analisi l'hai già fatta nel capitolo 4, l'Excel nel capitolo 5. Adesso devi farla vedere a qualcuno, e il formato dipende da chi è quel qualcuno.

Il manager vuole un PDF nella casella di posta il venerdì mattina, da stampare o allegare a una presentazione senza aprire nessun programma. Il team di prodotto vuole una pagina nel browser dove passare il mouse sui punti e nascondere un piano dalla legenda. L'analista finanziario vuole l'Excel con i dati grezzi e la pivot, per fare i suoi conti.

Claude Code produce tutti e tre gli output dallo stesso CSV con pochi prompt: installa le librerie, scrive gli script, li lancia e corregge gli errori. Tu decidi cosa deve uscire e controlli che i numeri tornino.

## 6.1 Grafici matplotlib, un round alla volta

Un grafico buono non esce al primo prompt, e non serve che esca. Funziona meglio un giro per volta: prima un grafico qualsiasi con i dati giusti, poi lo rendi leggibile, poi fissi risoluzione e proporzioni, infine lo produci in serie.

L'ordine conta. Se al primo giro le colonne sono invertite o i mesi sono in ordine alfabetico, te ne accorgi subito, prima di aver speso tempo su font e colori. Con un unico prompt lungo rischi di ottenere un grafico bellissimo e sbagliato, e di non notarlo.

### Round 1: il grafico grezzo

Si parte dal prompt più semplice possibile:

```text
Leggi data/saas_metrics.csv e genera un grafico dei tassi di
cancellazione mensili (churn rate) con matplotlib. Salvalo come
figures/churn_mensile.png.
```

Claude legge il CSV, trova la colonna `churn_rate`, installa matplotlib se manca e scrive uno script Python. Il risultato è il grafico di default: linea blu su sfondo bianco, mesi sull'asse X, percentuali sull'asse Y, nessuna griglia, nessun titolo. Va bene per controllare i dati. In una presentazione no.

Se il progetto ha un virtualenv, diglielo nel primo prompt ("usa `.venv`"), altrimenti le librerie finiscono nel Python di sistema. In modalità auto, quella di default, il classificatore di norma lascia passare il `pip install` senza chiederti niente. In modalità manuale Claude ti chiede il permesso.

### Round 2: leggibilità e colori

```text
Migliora il grafico: aggiungi un titolo chiaro ("Churn Rate Mensile
H1 2025"), etichette sugli assi (Mese / Churn Rate %), una griglia
leggera (alpha=0.3, linestyle='--'), font sans-serif (DejaVu Sans),
e usa i colori brand #1f77b4 per la linea e #ff7f0e per i marker.
Aggiungi una legenda.
```

La griglia leggera aiuta a leggere i valori senza rubare la scena, il titolo dice subito cosa stai guardando. I due colori dell'esempio sono il blu e l'arancione di default di matplotlib: al posto loro metti quelli del tuo brand. Questo è il minimo per mandare un grafico ai colleghi.

### Round 3: risoluzione e proporzioni

```text
Salva il grafico come PNG ad alta risoluzione in formato 16:9 per le
presentazioni: plt.figure(figsize=(12, 6.75)) e
plt.savefig(..., dpi=150, bbox_inches='tight').
```

A 150 DPI una figura da 12 per 6,75 pollici diventa circa 1800 per 1012 pixel, abbastanza per una slide a tutto schermo. Se ti serve esattamente 1200 per 675, usa `figsize=(8, 4.5)` con lo stesso DPI. `bbox_inches='tight'` ritaglia il bianco e impedisce che titolo ed etichette vengano tagliati ai bordi, un difetto frequente nei grafici generati da script. Il prezzo è che le dimensioni finali cambiano di qualche pixel.

### Round 4: produzione in serie

```text
Produci tre grafici separati a partire dallo stesso CSV:
1. figures/churn_mensile.png: linea del churn rate mese per mese
2. figures/distribuzione_piani.png: grafico a torta con la
   distribuzione percentuale dell'MRR per piano (free, silver, gold)
3. figures/utilizzo_features.png: grafico a barre orizzontali con
   l'utilizzo delle feature principali
Usa gli stessi parametri DPI/dimensioni/stile dei round precedenti.
Salva tutti i file in figures/ con nomi descrittivi.
```

Claude scrive uno script `genera_grafici.py` che con una sola esecuzione produce i tre file. È già una piccola pipeline di reporting.

I tipi di grafico del prompt seguono la regola di chi fa dataviz di mestiere: linee per il churn, perché è un andamento nel tempo; torta per i piani, perché sono parti di un totale; barre orizzontali per le feature, perché confronti categorie con nomi lunghi. Se nel prompt non li indichi, Claude di solito arriva alle stesse scelte. Se una non ti convince, scrivila.

Un'attenzione sulle feature. Nel CSV d'esempio `ai_voice_usage` è in minuti e `ai_text_usage` in messaggi: due barre sulla stessa scala sembrano confrontabili e non lo sono. Chiedi di normalizzarle (per esempio fatto 100 il valore di gennaio) oppure di fare due grafici separati.


![Una sessione reale: Claude ha scritto `dashboard.py`, ha installato le dipendenze e ha salvato cinque grafici in `docs/charts/`](figures/cap-06/fig-01.png)

<!-- TODO screenshot: fig-01, fig-02 e fig-03 sono a 560x315 pixel, troppo pochi per la stampa; rifarle a risoluzione piena. In fig-01 e fig-03 la status line mostra il modello e la modalità di allora. -->

### Lo script, letto riga per riga

Gli script che Claude produce per questo tipo di lavoro hanno quasi sempre la stessa forma. Non li scriverai a mano, ma saperli leggere ti serve per controllarli:

```python
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# Carica i dati
df = pd.read_csv("data/saas_metrics.csv")

# Nove righe per mese (piano per regione): media del churn per mese.
# churn_rate è già in percentuale (4.2 significa 4,2%)
churn = df.groupby("month")["churn_rate"].mean()

# Grafico 1: churn rate
fig, ax = plt.subplots(figsize=(12, 6.75))
ax.plot(churn.index.astype(str), churn.values,
        color="#1f77b4", linewidth=2,
        marker="o", markersize=6, markerfacecolor="#ff7f0e")
ax.set_title("Churn Rate Mensile H1 2025", fontsize=16, pad=12)
ax.set_xlabel("Mese", fontsize=12)
ax.set_ylabel("Churn Rate (%)", fontsize=12)
ax.yaxis.set_major_formatter(mtick.PercentFormatter())
ax.grid(axis="y", linestyle="--", alpha=0.3)
ax.tick_params(labelsize=10)
plt.tight_layout()
plt.savefig("figures/churn_mensile.png", dpi=150, bbox_inches="tight")
plt.close()
```

Due dettagli da cercare quando rileggi. Il primo è il `groupby`: il CSV ha 54 righe, sei mesi per tre piani per tre regioni, e se disegni le righe così come sono ottieni una linea a zig-zag che non vuol dire niente. Il secondo è la scala: `churn_rate` è già una percentuale, quindi `PercentFormatter()` va usato senza moltiplicare per 100. Se il tuo CSV salva il churn come frazione (0.03), lo script deve moltiplicare, altrimenti il grafico segna 0,03%. Claude di solito se ne accorge guardando i valori, ma controllalo tu.

![Lo script `dashboard.py` aperto nell'IDE, con gli import di matplotlib e seaborn e le palette per piani e regioni](figures/cap-06/fig-02.png)

Nello screenshot gli import sono sottolineati con "could not be resolved", eppure lo script gira: l'IDE usa un interprete Python diverso da quello in cui Claude ha installato le librerie. Si sistema puntando l'IDE al virtualenv del progetto.

### matplotlib, seaborn o plotly

Sono le tre librerie che Claude propone più spesso. matplotlib ti dà il controllo su ogni elemento del grafico: chiede più codice, ma il risultato è prevedibile, ed è la scelta naturale per PNG da mettere in un PDF o in una slide. seaborn sta sopra matplotlib e produce grafici statistici (distribuzioni, heatmap, pairplot) con meno righe, in cambio di meno controllo sul layout. plotly fa grafici interattivi per il web, con hover e zoom già pronti; esporta in HTML o in immagine statica, ma nei PDF rende peggio.

In pratica: matplotlib per PDF e stampa, plotly per le dashboard, seaborn per l'analisi esplorativa. Nel resto del capitolo usi matplotlib per il PDF e Chart.js, servito da Flask, per la webapp.

## 6.2 Una dashboard con Flask e Chart.js

I grafici statici vanno bene in un PDF. Se invece vuoi che il team esplori i dati da solo, passando il mouse sui punti e leggendo il valore esatto senza aprire Excel, ti serve una pagina web.

Flask più Chart.js è il minimo che funziona. Flask espone i dati come JSON, Chart.js disegna i grafici nel browser. Niente React, niente bundler: un file Python, un template HTML, un CSS, e si avvia con `python app.py`. La costruisci in quattro passi.

### Passo 1: lo scheletro Flask

```text
Crea app.py nella root del progetto. Deve avere:
- Route GET / che renderizza templates/index.html
- Route GET /api/data che legge data/saas_metrics.csv con pandas
  e restituisce un JSON con tre dataset aggregati:
  {
    "churn": [{"month": 1, "value": 4.2}, ...],
    "piani": [{"piano": "gold", "pct": 35}, ...],
    "features": [{"feature": "ai_voice_usage", "utilizzo": 0.72}, ...]
  }
- Debug mode attivo (app.run(debug=True))
Installa Flask e pandas se necessario.
```

Claude scrive `app.py` con le due route, aggrega i dati con pandas e li serializza in JSON. La route `/api/data` tiene separati i dati dalla presentazione: se domani cambia il CSV, il template HTML resta com'è.

### Passo 2: il template con Chart.js

```text
Crea templates/index.html. Deve:
- Includere Chart.js via CDN (versione 4.x)
- Definire tre canvas: lineChart (churn mensile), pieChart
  (distribuzione piani), featuresChart (utilizzo features, barre
  orizzontali)
- Al caricamento della pagina, fetcha /api/data con fetch() e
  inizializza i tre grafici con i dati ricevuti
- Aggiungi titoli H2 sopra ciascun grafico
```

Il template carica i dati con `fetch('/api/data').then(r => r.json()).then(data => { ... })`, senza ricaricare la pagina, e Chart.js disegna i grafici dagli array che riceve. Jinja2 qui rende solo la pagina vuota: i dati arrivano tutti dall'API.

### Passo 3: layout e stile

```text
Crea static/style.css con:
- Layout grid 2 colonne: il lineChart occupa tutta la prima riga
  (grid-column: 1 / -1), pieChart e featuresChart si dividono
  la seconda riga
- Font Inter (via Google Fonts) con fallback sans-serif
- Padding generoso (24px nei card), sfondo grigio chiaro (#f5f5f5),
  card bianche con border-radius 8px e box-shadow leggera
- Responsive: su mobile (max-width: 768px) una colonna sola
```

Una CSS grid basta per questa dashboard: niente framework, una ventina di righe, e il risultato si può già mostrare.

### Passo 4: aggiornare i dati senza ricaricare

```text
Nel template, aggiungi un bottone "Aggiorna dati" (id="refresh-btn")
in alto a destra. Al click, ri-fetcha /api/data e aggiorna i dati
dei tre grafici usando chart.data.datasets[0].data = newData seguita
da chart.update(). Non ricaricare la pagina.
```

Senza bottone, quando il CSV cambia l'utente deve ricaricare la pagina e perde quello che aveva fatto: lo zoom, la serie nascosta dalla legenda. Chart.js espone `.update()` per ridisegnare un grafico senza ricrearlo:

```javascript
document.getElementById("refresh-btn").addEventListener("click", function () {
    fetch("/api/data")
        .then(r => r.json())
        .then(data => {
            // Aggiorna i dataset dei grafici
            lineChart.data.labels = data.churn.map(d => d.month);
            lineChart.data.datasets[0].data = data.churn.map(d => d.value);
            lineChart.update();

            pieChart.data.datasets[0].data = data.piani.map(d => d.pct);
            pieChart.update();

            featuresChart.data.datasets[0].data = data.features.map(d => d.utilizzo);
            featuresChart.update();
        });
});
```

Cambi solo `.data` e chiami `.update()`: Chart.js anima la transizione da solo, senza lampeggi. Lo stesso schema (fetch, aggiorna i dati, update) vale per filtri, date picker e menu a tendina. Cambia solo il parametro che passi all'endpoint.

### Avviare e provare

```bash
python app.py
```

Apri `http://localhost:5000`. Passi il mouse su un punto della linea e compare il tooltip con il valore. Clicchi su un piano nella legenda della torta e lo nascondi. Premi "Aggiorna dati" e i grafici si aggiornano senza ricaricare la pagina.

::: {.callout .callout-warning}
[Attenzione]{.callout-title}

Su macOS la porta 5000 è spesso occupata dal ricevitore AirPlay. Se il browser ti risponde con un 403 o Flask non parte, disattiva il ricevitore AirPlay nelle impostazioni di sistema oppure chiedi a Claude di avviare l'app su un'altra porta, per esempio `app.run(debug=True, port=5001)`.
:::

Perché Flask e non FastAPI o Django? Per una dashboard interna senza login e senza database, Flask si legge in cinque minuti. Con FastAPI lo schema è identico, una route che restituisce JSON e Chart.js che lo disegna. Django funziona, ma porta con sé ORM, admin e autenticazione che qui non ti servono.

### Cosa ti dà in più una webapp

Rispetto ai PNG la dashboard risponde a domande puntuali: quanto era il churn di marzo lo leggi nel tooltip. Su un server, anche interno, basta un link e tutti vedono la stessa versione. Aggiungere un quarto grafico vuol dire aggiungere un canvas e un campo in `/api/data`. E un menu "Filtra per regione" è un parametro in più nella chiamata: Flask filtra il DataFrame prima di restituire il JSON.

Il limite è che serve un server acceso: non la alleghi a una mail e offline non funziona. Per renderla raggiungibile dal team la metti su qualsiasi macchina che esegue Python, un'istanza EC2, un container Docker, un servizio come Render. Il codice resta quello, e per il resto basta un prompt come "crea un Dockerfile per questa webapp Flask".

### La strada corta: la skill frontend-design

I quattro passi danno una dashboard prevedibile, perché hai deciso tu ogni dettaglio. Se l'aspetto conta più del controllo, puoi delegare il design a una skill. Anthropic pubblica nel marketplace ufficiale il plugin frontend-design, che contiene una skill con istruzioni su tipografia, palette e layout. Claude la carica da solo quando chiedi un'interfaccia web.

```text
/plugin install frontend-design@claude-plugins-official
```

Nello screenshot il prompt era una riga sola: una webapp locale per mostrare i grafici generati dallo script Python. Claude ha caricato la skill (`Skill(frontend-design)`), ha guardato i grafici esistenti e ha scelto una direzione estetica prima di scrivere codice: sfondo scuro, accenti colorati, card con bordi luminosi.

![Claude carica la skill frontend-design e sceglie la direzione estetica prima di costruire la webapp](figures/cap-06/fig-03.png)

Il risultato di solito è più curato della dashboard dei quattro passi, ma meno prevedibile: font, colori e layout li sceglie la skill. Per una dashboard interna che deve solo funzionare, i quattro passi bastano. Per una demo davanti a un cliente, la skill ti evita di scrivere il CSS a mano. Come funzionano le skill lo vedi nel capitolo 9, i plugin e i marketplace nel capitolo 14.

::: {.callout .callout-prompt}
[Prompt riusabile]{.callout-title}

Mini dashboard webapp. Sostituisci `<csv_path>`, `<grafico1/2/3>` e i tipi di grafico con i tuoi dati: funziona su qualsiasi CSV tabellare.

```text
A partire da <csv_path>, crea una mini dashboard Flask:
- app.py con route GET / e GET /api/data
- templates/index.html con Chart.js CDN e tre canvas:
  <grafico1> (tipo: <line|bar|pie>),
  <grafico2> (tipo: <line|bar|pie>),
  <grafico3> (tipo: <line|bar|pie>)
- static/style.css con layout grid 2 colonne, font Inter,
  card bianche su sfondo grigio chiaro, responsive mobile
- Bottone "Aggiorna dati" che ri-fetcha /api/data e chiama
  chart.update() senza reload
Avvio: python app.py → server su http://localhost:5000
```
:::

## 6.3 Report PDF con ReportLab

Il PDF è il formato senza sorprese: non dipende dal browser né dai programmi di chi lo apre, e il layout è lo stesso su ogni schermo. Va bene per il cliente esterno, per il manager che stampa, per il report che arriva per mail il primo del mese.

ReportLab è la libreria Python più usata per generare PDF da codice. Non è la più semplice, ma ti dà controllo fine su ogni elemento, tabelle native, immagini e stili tipografici. Le alternative in due righe: WeasyPrint converte HTML e CSS in PDF, ottimo se hai già un template HTML (Claude può scrivere l'HTML e poi convertirlo); fpdf2 è più semplice ma controlla meno il layout. ReportLab conviene quando sai esattamente come dev'essere fatto il documento e devi inserirci grafici generati da codice, che è il caso di questo capitolo.

### Il prompt completo

```text
Scrivi tools/genera_report.py che genera output/report_mensile.pdf.
Il PDF deve avere:

1. Pagina di copertina: logo (static/logo.png se esiste, altrimenti
   testo "SaaS Co."), titolo "Report Metriche SaaS H1 2025",
   mese corrente, sfondo #1f77b4 con testo bianco.

2. Pagina executive summary: i 3 KPI principali in box grandi
   (MRR totale, churn medio, piani attivi), il grafico
   figures/churn_mensile.png incorporato come immagine, 3 bullet
   di takeaway generati analizzando i dati del CSV.

3. Pagina dettaglio piani: grafico a torta (figures/distribuzione_piani.png),
   tabella con una riga per piano (free / silver / gold) e colonne
   MRR, Nuove iscrizioni, Cancellazioni, Churn %.

4. Pagina raccomandazioni: testo libero (3-5 bullet) suggerito da
   Claude analizzando i trend del dataset.

Usa SimpleDocTemplate, Paragraph con ParagraphStyle, Image, Table,
TableStyle, PageBreak di ReportLab. Installa reportlab se necessario.
```

Claude installa ReportLab, scrive lo script e lo lancia. Se c'è un errore (un import sbagliato, una parentesi mancante, un argomento che ReportLab non accetta), lo legge dall'output e corregge da solo. È qui che si sente la differenza con una chat: lì ricevi il codice, lo esegui tu, copi l'errore, lo incolli, aspetti la correzione e riparti. Claude Code chiude il ciclo nella stessa sessione, e spesso vedi solo il PDF finito.

I takeaway e le raccomandazioni delle pagine 2 e 4 sono testo scritto da Claude sui tuoi dati. Rileggili prima di mandare il PDF: è la parte del report in cui un errore di interpretazione passa più facilmente inosservato.

### I mattoni di ReportLab

Non lo scriverai a mano, ma conoscere i pezzi principali ti aiuta a scrivere prompt più precisi e a capire cosa è andato storto quando il layout non torna:

```python
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Image, Table,
    TableStyle, PageBreak, Spacer,
)

# Contenitore principale: dimensioni pagina e margini
doc = SimpleDocTemplate("output/report_mensile.pdf",
                        pagesize=A4,
                        topMargin=2*cm, bottomMargin=2*cm,
                        leftMargin=2*cm, rightMargin=2*cm)

# Stile per i titoli
stile_titolo = ParagraphStyle("Titolo",
    fontSize=24, leading=28, textColor=colors.white,
    spaceAfter=12, fontName="Helvetica-Bold")

# Un grafico matplotlib già salvato su disco, in 16:9
img_churn = Image("figures/churn_mensile.png", width=14*cm, height=7.875*cm)

# Tabella piani
dati_tabella = [["Piano", "MRR", "Churn %", "Nuove iscrizioni"],
                ["Gold", "€ 48.200", "1,2%", "1.240"],
                ["Silver", "€ 22.100", "2,8%", "890"],
                ["Free", "€ 0", "6,1%", "3.400"]]
tabella = Table(dati_tabella, colWidths=[4*cm, 4*cm, 3*cm, 4*cm])
tabella.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f77b4")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
]))

# Lo sfondo della copertina si disegna sulla pagina, non è un flowable
def sfondo_copertina(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#1f77b4"))
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    canvas.restoreState()

# copertina, executive_summary, ... sono liste di Paragraph, Image, Table
story = [*copertina, PageBreak(),
         *executive_summary, PageBreak(),
         *dettaglio_piani, PageBreak(),
         *raccomandazioni]
doc.build(story, onFirstPage=sfondo_copertina)
```

Il modello mentale è la lista `story`: ci metti dentro gli elementi nell'ordine in cui devono comparire (paragrafi, immagini, tabelle, salti pagina) e `doc.build(story)` li impagina. La lista deve essere piatta, per questo le sezioni sono espanse con `*`: se passi a `build` una lista dentro l'altra, ReportLab si ferma con un errore. Quello che non è contenuto di pagina, come lo sfondo pieno della copertina, si disegna sul canvas con le funzioni `onFirstPage` e `onLaterPages`. Se la copertina esce bianca con il titolo bianco, il problema è quasi sempre lì: chiedi a Claude di disegnare lo sfondo in `onFirstPage`.

### I grafici in memoria

Se i grafici sono già su disco, come quelli del paragrafo 6.1, li inserisci con `Image("percorso/del/file.png")`. Se preferisci non avere file intermedi, puoi passare a ReportLab un buffer in memoria:

```python
import io
import matplotlib.pyplot as plt
from reportlab.lib.units import cm
from reportlab.platypus import Image

# Genera il grafico e salvalo in memoria, non su disco
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(mesi, valori_churn, color="#1f77b4", linewidth=2)
# ... stile ...

buffer = io.BytesIO()
plt.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
buffer.seek(0)
plt.close()

# Inserisci direttamente nel PDF
img = Image(buffer, width=14*cm, height=7*cm)
```

`io.BytesIO()` si comporta come un file: matplotlib ci scrive il PNG, ReportLab lo legge da lì. Niente PNG temporanei e niente dipendenza dall'ordine in cui girano gli script. Usa un buffer per ogni grafico e non riusarlo: ReportLab legge l'immagine al momento del `build`, non quando crei l'oggetto `Image`.

### Parametrizzare lo script

Come per la webapp, lo script diventa utile davvero quando accetta parametri:

```text
Modifica tools/genera_report.py per accettare argomenti CLI:
--region (es. Europe, North America, Asia Pacific)
--months (es. 1,2,3)
--output (path del PDF, default output/report_mensile.pdf)
Aggiungi commenti d'uso e validazione degli argomenti con argparse.
Esempio: python tools/genera_report.py --region Europe --months 1,2 --output output/europe_jan_feb.pdf
```

A questo punto chiunque nel team genera il report per la sua regione e i mesi che gli interessano, senza aprire il codice:

```bash
python tools/genera_report.py --region "North America" --months 4,5,6 --output output/na_q2.pdf
```

Le virgolette servono perché "North America" contiene uno spazio.

## 6.4 PDF, webapp o Excel

Il formato lo decide chi legge, e cosa farà con i numeri.

| Output | Quando usarlo | Pro | Contro |
| :---- | :---- | :---- | :---- |
| PDF | Stakeholder esterni, report periodico, consegna formale | Si apre ovunque, non cambia, porta il tuo brand, si allega a una mail | Statico, va rigenerato quando cambiano i dati |
| Webapp | Team interno, dati che cambiano spesso, esplorazione | Interattiva, sempre aggiornata, si estende, filtri dinamici | Serve un server (anche solo locale), offline non va, non si allega |
| Excel | Chi vuole rielaborare i numeri, analisti finanziari | Familiare, modificabile, pivot e formule vive | Difficile da versionare, nessun aggiornamento in tempo reale, copie diverse in giro |

Di solito ne combini due o tre. Per il report mensile di un SaaS il PDF parte il primo del mese verso manager e clienti, la webapp interna resta accesa per il team di prodotto e l'Excel lo generi quando l'analista lo chiede per il board. Per un lancio basta la webapp di monitoraggio più un PDF di chiusura a fine sprint. Per un audit esterno vale il contrario: PDF firmato e datato come documento ufficiale, Excel con i dati grezzi per le verifiche dell'auditor, nessuna webapp.

Prima di scegliere, chiediti come userà il file chi lo riceve. Se lo apre sul suo computer, magari senza rete, e vuole rifare i conti, gli serve l'Excel. Se deve esplorare i dati da solo nel browser, con i filtri, la webapp. Se lo riceve per mail, lo legge e forse lo stampa, il PDF. Quando la risposta non è chiara, il PDF è la scelta più sicura.

## 6.5 Anteprima: la pipeline diventa una skill

Adesso hai uno script per i grafici, una webapp Flask con tre grafici interattivi e un generatore di PDF con parametri. Funzionano sui tuoi dati, sulla tua macchina, in questo progetto.

Il mese prossimo devi rifare lo stesso lavoro per un altro cliente, con un CSV che ha colonne leggermente diverse. Senza nessuna struttura ricominci da capo: riprendi i prompt, adatti i nomi delle colonne, sistemi i parametri. Con una skill di Claude Code ti basta un comando.

### Cos'è una skill, in breve

Una skill è una cartella con un file `SKILL.md`: in `~/.claude/skills/<nome>/` vale per tutti i tuoi progetti, in `.claude/skills/<nome>/` solo per il progetto e la condividi con il team via Git. Il frontmatter contiene un nome e una descrizione, il corpo le istruzioni. Claude legge sempre le descrizioni delle skill installate: quando una richiesta corrisponde, carica la skill e segue le istruzioni. Oppure la chiami tu per nome, come uno slash command.

Accanto a `SKILL.md` la cartella può contenere script e file di supporto. Per questa pipeline vuol dire che i tre script che hai appena scritto possono vivere dentro la skill, e `SKILL.md` spiega a Claude quando e come lanciarli. Uno schizzo:

```markdown
---
name: data-analysis-saas-monthly
description: Genera il report mensile SaaS (PDF, dashboard HTML, Excel) da un CSV di metriche. Da usare quando l'utente chiede il report mensile di un cliente.
---

Argomenti: $0 percorso del CSV, $1 nome del cliente, $2 mese.

1. Controlla che il CSV abbia le colonne month, plan, region, mrr, churn_rate.
   Se mancano, fermati e dimmi quali.
2. Lancia ${CLAUDE_SKILL_DIR}/scripts/genera_grafici.py sul CSV.
3. Lancia ${CLAUDE_SKILL_DIR}/scripts/genera_report.py con il nome
   del cliente nel titolo.
4. Genera la dashboard HTML statica e l'Excel in output/$1/.
```

Come si scrive, si testa e si distribuisce una skill lo vedi nel capitolo 9. Per ora ti basta il meccanismo.

### La skill data-analysis-saas-monthly

La skill dello schizzo prende il CSV, il nome del cliente (finisce nei titoli) e il mese, e produce tre file: il PDF del paragrafo 6.3, una dashboard HTML statica con i grafici Chart.js, che a differenza della webapp Flask funziona offline e si allega a una mail, e l'Excel del capitolo 5.

Immagina un'agenzia di analytics che segue tre clienti SaaS, `startup_alpha`, `scaleup_beta` ed `enterprise_gamma`, ognuno con il suo CSV, i suoi piani e le sue metriche. Con la skill installata il lavoro del mese diventa:

```text
Genera il report mensile per startup_alpha usando data/alpha_may.csv
```

```text
Genera il report mensile per scaleup_beta usando data/beta_may.csv
```

```text
Genera il report mensile per enterprise_gamma usando data/gamma_may.csv
```

Tre prompt, nove file. Il tempo che resta lo passi ad aprire i PDF e controllare che i numeri siano quelli giusti.

Tutto questo regge perché nessun pezzo del capitolo è legato a un file o a un cliente: lo script del report accetta parametri con argparse, la webapp separa i dati (l'API Flask) dalla presentazione (Chart.js), `SimpleDocTemplate` impagina qualunque quantità di contenuto.

Con il prossimo capitolo entri nella Parte III: CLAUDE.md nel capitolo 7, custom command nell'8, skill nel 9, agent nel 10. Il lavoro di analisi di questa parte diventa lì qualcosa che riusi invece di rifare.

## Riepilogo {.unlisted}

- Costruisci un grafico matplotlib a giri: prima i dati giusti, poi leggibilità, poi risoluzione e proporzioni, infine la produzione in serie.
- Quando rileggi lo script controlla ordine dei mesi, aggregazione delle righe e unità di misura: sono i punti in cui un grafico sbaglia senza darlo a vedere.
- Flask più Chart.js ti dà una dashboard con un endpoint `/api/data` e un bottone che aggiorna i grafici con `chart.update()`, senza ricaricare la pagina.
- ReportLab costruisce il PDF da una lista piatta di elementi (`story`); sfondi e decorazioni di pagina vanno nelle funzioni `onFirstPage` e `onLaterPages`.
- Scegli il formato in base a chi legge: PDF per chi riceve e stampa, webapp per chi esplora, Excel per chi rifà i conti.
- Uno script con parametri è già mezza skill: nel capitolo 9 lo impacchetti.

## Esercizio {.unlisted}

Prendi il `saas_metrics.csv` dei capitoli precedenti e produci i tre output in un'unica sessione:

1. Lancia `genera_grafici.py` e controlla che in `figures/` ci siano i tre PNG.
2. Avvia la webapp Flask ed esplora i dati nel browser.
3. Lancia `genera_report.py` e apri il PDF in `output/`.

L'esercizio è finito quando il churn di marzo è identico nel tooltip della webapp, nel grafico del PDF e nella colonna del CSV aggregata a mano. Se non lo è, chiedi a Claude di trovare la differenza: di solito è un'aggregazione diversa tra le due pipeline (media contro media pesata, o un filtro per regione rimasto attivo).

Se devi rifare la webapp da capo, il prompt della mini dashboard Flask è nella cartella `cap-05/` del repository `github.com/hidran/claude-code-book-snippets` (numerazione della prima edizione).
