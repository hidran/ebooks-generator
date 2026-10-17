# Capitolo 4. Analizzare un CSV con Plan Mode

**Cosa imparerai**

- far leggere un CSV a Claude Code così com'è, senza prepararlo prima
- scrivere prompt che producono conclusioni sui dati, oltre a medie e deviazioni standard
- usare Plan Mode per far progettare un'analisi prima che Claude scriva una riga di codice
- gestire file grandi e trasformare una sessione esplorativa in uno script da rilanciare

**Prerequisiti**: capitoli 1-3. Python 3 installato (serve per gli script che Claude propone, non devi saperlo scrivere) e un CSV qualsiasi, oppure `data/saas_metrics.csv`, che generi con lo script del §4.1.

Se cerchi un primo lavoro vero da affidare a Claude Code, un CSV va benissimo. Claude legge il file direttamente dal disco con il tool `Read`, quindi niente copia e incolla in una chat e niente upload. Sui contenuti ragiona con le nozioni di dominio che ha già: sa cos'è il churn rate e sa che un aumento dei ticket al supporto seguito da più cancellazioni è un segnale da guardare. Quando hai trovato quello che cercavi, ti scrive lo script Python che rifà la stessa analisi il mese prossimo sui dati nuovi.

Il dataset del capitolo contiene metriche di un prodotto SaaS: tre piani di abbonamento, tre regioni, sei mesi di iscrizioni, cancellazioni, MRR e ticket. Si parte dall'apertura del file e si arriva a quattro grafici PNG, passando per Plan Mode. Il procedimento si applica a qualsiasi CSV.

## 4.1 Far leggere il CSV a Claude

Il primo passo è il più semplice: avvii Claude Code nella cartella che contiene il file e gli chiedi di leggerlo. Non serve convertire niente né preparare script di import.

### Posizionarsi nella cartella giusta

Apri il terminale e crea una cartella di lavoro, se non ce l'hai già:

```bash
mkdir -p ~/progetti/analisi-saas
cd ~/progetti/analisi-saas
```

Mettici il CSV in una sottocartella `data/`. Negli esempi uso `data/saas_metrics.csv`, che generi tra un attimo con lo script della sezione "Il dataset di esempio". Poi avvia Claude:

```bash
claude
```

La prima volta che apri Claude Code in una cartella nuova ti chiede se ti fidi del suo contenuto: conferma. Al primo avvio di una versione recente compare anche l'avviso di auto mode, la modalità di permesso di default che hai visto nel Capitolo 2. Claude lancia da solo i comandi coerenti con la tua richiesta e un classificatore blocca quelli rischiosi, quindi per leggere file o lanciare `ls` non ti chiede niente.

### Guardare cosa c'è nella cartella

Prima di interrogare il CSV conviene sapere cosa c'è intorno. Hai due strade.

La prima è la shell mode: scrivi `!` all'inizio del prompt, seguito dal comando.

```text
! ls -al
```

Il comando gira nel terminale, l'output entra nella conversazione e Claude lo commenta. Se compare una cartella `.claude`, lì dentro ci sono le impostazioni di progetto, di cui parliamo nel Capitolo 11.

La seconda è chiederlo a parole:

```text
Elenca i file presenti in questa cartella
```

Claude lancia `ls` per conto suo e ti riporta l'elenco. Il risultato è lo stesso: con `!` il comando lo scegli tu, a parole lo sceglie lui.

### Il primo prompt di lettura

Per citare un file nel prompt scrivi `@` seguito dal nome. Claude Code ti propone i percorsi che corrispondono e `Tab` completa quello giusto.

```text
@data/saas_metrics.csv leggi il file e dimmi:
- numero di righe e colonne
- nomi delle colonne
- primi 5 valori per le colonne "plan" e "region"
- eventuali valori mancanti o anomali
```

Claude legge il file con `Read` e risponde con qualcosa di simile:

```text
Il file data/saas_metrics.csv contiene:
- 54 righe, 12 colonne
- Colonne: month, date, plan, region, new_signups,
  cancellations, mrr, churn_rate, ai_voice_usage,
  ai_text_usage, support_tickets, retention_rate
- Valori univoci "plan": free, silver, gold
- Valori univoci "region": Europe, North America, Asia Pacific
- Periodo coperto: gennaio - giugno 2025
- Nessun valore mancante rilevato
```

Con un dataset nuovo questa è la parte più noiosa: capire quali colonne ci sono, di che tipo, dove mancano dati. Di solito ci va un'ora tra notebook e `df.info()`. Qui ti costa un prompt, e il tempo che resta lo spendi a ragionare su cosa significano i numeri.

::: {.callout .callout-deep-dive}
[Sotto il cofano]{.callout-title}

Claude non apre il file come farebbe Excel. Il tool `Read` gli restituisce il contenuto come testo, che finisce nella finestra di contesto insieme al resto della conversazione. Un CSV di 54 righe entra intero e occupa pochissimo; con un export da centinaia di migliaia di righe il discorso cambia, e lo affrontiamo nel §4.4. Quanto contesto stai usando te lo dice `/context`, il modello in uso lo controlli con `/model`. A ottobre 2026 il default è Claude Opus 5.5 con una finestra di contesto da 1M token, ma i default cambiano spesso, quindi controlla sempre `/model`.
:::

### Il dataset di esempio

Tutto il capitolo usa `data/saas_metrics.csv`. Simula sei mesi di metriche (gennaio-giugno 2025) di un prodotto SaaS con tre piani, free, silver e gold, venduto in tre regioni: Europe, North America e Asia Pacific. C'è una riga per ogni combinazione di mese, piano e regione, da cui le 54 righe. I numeri sono sintetici: per avere esattamente il mio stesso file, salva questo script come `genera_dati.py` nella cartella di lavoro e lancialo con `python3 genera_dati.py`.

```python
"""Genera data/saas_metrics.csv, il dataset dei capitoli 4-6."""
import csv
import random
from pathlib import Path

random.seed(2025)

PIANI = {"free": 0, "silver": 12.99, "gold": 24.99}
REGIONI = {"Europe": 1.0, "North America": 1.3, "Asia Pacific": 0.7}
ABBONATI_INIZIALI = {"free": 4000, "silver": 1200, "gold": 500}

righe = []
for regione, peso in REGIONI.items():
    for piano, prezzo in PIANI.items():
        abbonati = int(ABBONATI_INIZIALI[piano] * peso)
        for mese in range(1, 7):
            iscritti = int(abbonati * random.uniform(0.06, 0.10))
            churn = {"free": 6.0, "silver": 4.0, "gold": 1.5}[piano]
            if piano == "free" and mese == 3:
                churn += 4.0          # a marzo scadono le prove gratuite
            if piano == "silver":
                churn += mese * 0.3   # il silver peggiora mese dopo mese
            churn = round(churn + random.uniform(-0.4, 0.4), 2)
            cancellazioni = int(abbonati * churn / 100)
            ticket = int(abbonati * 0.02 + cancellazioni * (0.8 if piano == "silver" else 0.3))
            abbonati = abbonati + iscritti - cancellazioni
            righe.append({
                "month": mese,
                "date": f"2025-{mese:02d}-01",
                "plan": piano,
                "region": regione,
                "new_signups": iscritti,
                "cancellations": cancellazioni,
                "mrr": round(abbonati * prezzo, 2),
                "churn_rate": churn,
                "ai_voice_usage": int(abbonati * random.uniform(2, 6)),
                "ai_text_usage": int(abbonati * random.uniform(20, 40)),
                "support_tickets": ticket,
                "retention_rate": round(100 - churn, 2),
            })

righe.sort(key=lambda r: (r["month"], r["plan"], r["region"]))
Path("data").mkdir(exist_ok=True)
with open("data/saas_metrics.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=righe[0].keys())
    writer.writeheader()
    writer.writerows(righe)
print(f"Scritte {len(righe)} righe in data/saas_metrics.csv")
```

Lo stesso file ti serve nei capitoli 5 e 6, quindi tienilo da parte.

Le colonne che userai di più:

| Colonna | Descrizione |
| :---- | :---- |
| `month` | Mese di riferimento (1-6) |
| `date` | Data di inizio mese |
| `plan` | Piano: free, silver, gold |
| `region` | Area geografica |
| `new_signups` | Nuovi iscritti nel mese |
| `cancellations` | Cancellazioni nel mese |
| `mrr` | Monthly Recurring Revenue (€) |
| `churn_rate` | Tasso di abbandono (%) |
| `ai_voice_usage` | Uso della feature voce AI (minuti) |
| `ai_text_usage` | Uso della feature testo AI (messaggi) |
| `support_tickets` | Ticket aperti al supporto |
| `retention_rate` | Tasso di retention (%) |

È abbastanza piccolo da stare tutto nel contesto e abbastanza ricco per ogni analisi delle prossime sezioni.

::: {.callout .callout-prompt}
[Prompt riusabile]{.callout-title}

Onboarding su un dataset nuovo. Funziona su qualsiasi CSV come primo contatto, prima di cominciare l'analisi vera.

```text
Leggi @<file.csv>. Riporta:
1. Struttura: numero di righe, colonne con nome e tipo
2. Valori mancanti o anomali
3. Pattern temporali, se ci sono colonne data
4. Eventuali outlier evidenti nelle colonne numeriche

Poi dimmi 3 domande di business interessanti che si
possono fare su questi dati: non risponderne ancora,
voglio prima capire se sono quelle giuste.
```
:::

## 4.2 Dai numeri alle conclusioni

Le statistiche descrittive di un CSV te le dà qualsiasi strumento. Da Claude vuoi l'interpretazione, e quella dipende da come chiedi. Prendi questo prompt:

```text
Dammi le statistiche descrittive del file
```

Ottieni una tabella con media, mediana e deviazione standard per ogni colonna numerica. Va bene come controllo di sanità, ma non ti aiuta a decidere niente. Confrontalo con questo:

```text
@data/saas_metrics.csv guarda il CSV. Quali sono i 3 pattern
più importanti per chi gestisce un SaaS? Spiegamelo in
italiano semplice. Usa i numeri solo quando sono il punto
principale, non come riempitivo.
```

Qui Claude deve scegliere cosa conta e dirlo in parole semplici, come farebbe un analista che presenta i dati a chi li deve usare. Le domande che seguono funzionano bene sullo stesso dataset e coprono i casi più comuni.

### Trend temporali

```text
@data/saas_metrics.csv analizza i tassi di cancellazione mese
per mese. Vedi un trend chiaro? Ci sono picchi anomali
rispetto alla media? Cosa potrebbe spiegarli?
```

Claude cerca un andamento, lo confronta con la media e propone ipotesi. Su questo dataset potrebbe farti notare che il churn del piano free sale a marzo, quando di solito scadono i periodi di prova, che il gold resta stabile, e suggerirti di guardare meglio il silver, che forse ha un problema di proposta di valore.

### Correlazioni

```text
@data/saas_metrics.csv c'è correlazione tra il numero di
support ticket aperti e il tasso di abbandono del piano?
Se sì, in quale piano la correlazione è più forte?
```

Claude incrocia due colonne. La risposta di solito contiene una direzione («sì, nel piano silver più ticket vanno insieme a più cancellazioni») e un'ipotesi su cosa la spieghi. Tieni presente che una correlazione su 54 righe è un indizio, non una prova: se la conclusione finisce in una decisione, chiedi a Claude quanto è solida e cosa servirebbe per confermarla.

### Segmentazione per piano

```text
@data/saas_metrics.csv quale piano contribuisce di più al MRR?
C'è un piano che sta sottoperformando rispetto alla sua
base utenti? Descrivilo come faresti in una slide per il CEO.
```

L'ultima frase, «come faresti in una slide per il CEO», è un trucco efficace: obbliga Claude a sintetizzare, a togliere il rumore e a chiudere con una conclusione. Spesso il testo lo puoi incollare così com'è in una presentazione.

### Anomalie

```text
@data/saas_metrics.csv ci sono settimane o mesi con metriche
fuori scala rispetto alla media? Identifica gli outlier
e proponi 2-3 possibili spiegazioni per ognuno.
```

Oltre a segnalare i valori fuori scala, Claude ragiona sulle cause plausibili. Un picco di iscrizioni in un mese può essere una campagna marketing o un post diventato virale; un crollo della retention può far pensare a un downtime o a un cambio di prezzo. Restano ipotesi: le verifichi tu, con chi conosce il prodotto.

### Piano e regione insieme

Funziona molto bene anche il prompt che incrocia due dimensioni di segmentazione:

```text
@data/saas_metrics.csv in quale combinazione di piano e regione
la crescita è più forte? E in quale la situazione è più
preoccupante? Descrivi ciascuna con una frase e proponi
un'azione concreta per ognuna.
```

Claude costruisce la matrice piano per regione, individua le celle che vanno meglio e quelle che vanno peggio, e per ognuna propone qualcosa da fare. Chiedere un'azione concreta lo costringe a passare dalla descrizione alla raccomandazione.

### Come iterare

La prima risposta è un punto di partenza. Il giro che funziona meglio è questo:

1. Fai il prompt orientato alle conclusioni.
2. Leggi la risposta e scegli il punto più interessante.
3. Scava su quel punto con una domanda mirata: «approfondisci la questione del piano silver che hai citato: hai abbastanza dati per stimare l'impatto sull'MRR annuale?»
4. Quando hai qualcosa su cui si può agire, fattelo scrivere come raccomandazione: «scrivi questa conclusione come potrebbe apparire in un report per il management, tre frasi al massimo».

## 4.3 Plan Mode: pianificare un'analisi complessa

Finora hai lavorato a domande e risposte, che per esplorare va benissimo. Quando vuoi un risultato concreto, come un grafico, una dashboard o un report PDF, ti serve prima un piano.

**Plan Mode** è la modalità di permesso che separa la pianificazione dall'esecuzione. Claude legge i file, lancia i comandi che gli servono per esplorare e scrive un piano a passi numerati, ma non modifica niente finché non lo approvi. Usalo ogni volta che il task tocca più file, mette insieme più strumenti o produce qualcosa che vuoi fatto bene al primo colpo.

### Come attivare Plan Mode

Il modo più rapido è `Shift+Tab`. Ogni pressione passa alla modalità successiva: da auto mode, che è il default, a manual, poi accept edits, poi plan, e di nuovo auto. Ti fermi quando la riga di stato mostra `plan mode on`.

Se sai già che vuoi cominciare pianificando, avvia la sessione direttamente in Plan Mode:

```bash
claude --permission-mode plan
```

Dal prompt puoi usare anche il comando `/plan`, che entra in Plan Mode; se gli passi una descrizione, il piano parte subito.

![Una sessione già in Plan Mode dopo l'analisi per regione: `/plan` conferma che la modalità è attiva e che non c'è ancora un piano](figures/cap-04/fig-01.png)

<!-- TODO screenshot: fig-01 è piccola e la riga di stato mostra il modello di allora; rifarla con la UI attuale (`/plan` in una sessione già in Plan Mode) a risoluzione piena -->

Scrivere nel prompt «non scrivere codice, pianifica solo» in una sessione normale di solito produce un piano in chat, ma la modalità resta quella di prima. In auto mode, al messaggio successivo Claude può già mettersi a creare file. La garanzia che non tocchi niente finché non dici di sì te la dà solo Plan Mode.

### Quando usarlo

La regola pratica: Plan Mode quando vuoi un output concreto (un file, un grafico, una dashboard, uno script), non per le domande esplorative sui dati. Per il botta e risposta del §4.2 rallenta senza aggiungere niente. Per «costruisci una dashboard con quattro grafici» usalo sempre.

### Plan Mode in azione: la dashboard SaaS

L'obiettivo è una dashboard di quattro grafici sul dataset che hai appena analizzato: trend dell'MRR mensile, iscrizioni per regione, churn rate per piano e una heatmap dell'uso delle feature AI. Passa in Plan Mode con `Shift+Tab` e invia questo prompt:

```text
Analizza il file saas_metrics.csv e proponi una strategia
per costruire una dashboard con quattro grafici:
- MRR trend mensile per piano (free, silver, gold)
- Signup per regione mese per mese
- Churn rate confrontato per piano
- Heatmap utilizzo feature AI (ai_voice_usage, ai_text_usage)

Stack: Python + matplotlib. Voglio immagini PNG statiche
salvate in una cartella docs/charts/.
Non scrivere codice: pianifica solo.
```

Claude legge il CSV, controlla che le colonne necessarie per ogni grafico esistano e lancia qualche comando di sola lettura per esplorare. Con auto mode disponibile, quei comandi li valuta il classificatore invece di chiederli a te. Dopo qualche secondo arriva un piano di questo tipo:

```text
Piano di implementazione

1. Analisi struttura CSV
   - Verifica colonne: month, plan, region, mrr, new_signups,
     churn_rate, ai_voice_usage, ai_text_usage
   - Conferma periodo: gennaio-giugno 2025 (6 mesi)

2. Setup ambiente
   - Creare requirements.txt con: pandas, matplotlib, seaborn
   - Creare struttura cartelle: data/, docs/charts/

3. Script principale dashboard.py
   - Lettura CSV con pandas
   - Grafico 1: MRR trend (line chart, pivot per plan)
   - Grafico 2: Signup per regione (grouped bar chart)
   - Grafico 3: Churn rate (line chart, pivot per plan)
   - Grafico 4: Heatmap utilizzo AI (seaborn heatmap,
     asse x = mesi, asse y = feature, cella = media utilizzo)
   - Salvataggio PNG in docs/charts/

4. Salvataggio piano in docs/plan.md

5. Esecuzione:
   - pip install -r requirements.txt
   - python dashboard.py
```

<!-- TODO screenshot: il piano della dashboard in Plan Mode (Python + matplotlib, docs/charts/). Sostituisce la vecchia fig-02, che mostrava un piano HTML + Chart.js + Firebase Hosting in contrasto con il testo -->

### Rivedere e modificare il piano

Il piano è una proposta. Prima di approvarlo leggilo con occhio critico: cerca passi ridondanti, cose che mancano, uno stack che non ti convince.

In questo caso il passo 4, salvare il piano in `docs/plan.md`, è un'aggiunta da tenere. Tra due settimane, quando riapri il progetto, quel file ti ricorda perché hai fatto certe scelte, come un piccolo ADR (Architecture Decision Record) che non hai dovuto scrivere tu.

Per cambiare qualcosa resti in Plan Mode e lo chiedi:

```text
Nel grafico 2, aggiungi anche una linea con il totale
aggregato di tutte le regioni. Per il grafico 4, usa
una palette di colori che vada dal bianco al blu scuro
(più uso = più scuro). Aggiorna il piano.
```

Claude aggiorna il piano senza toccare il codice, e puoi ripetere finché ti convince. Se preferisci correggerlo a mano, `Ctrl+G` apre il piano nel tuo editor.

### Approvare ed eseguire

Quando il piano è quello giusto, Claude ti chiede come procedere:

- `Yes, and use auto mode`: Claude esegue tutti i passi in auto mode. Il classificatore lascia passare le azioni coerenti con il piano e ferma quelle rischiose. Per un task chiaro e a basso rischio come questo è la scelta giusta. Se auto mode non è disponibile, l'opzione si chiama `Yes, auto-accept edits`.
- `Yes, manually approve edits`: Claude ti chiede conferma prima di ogni modifica ai file. Utile quando tocca file importanti o quando vuoi guardare le dipendenze una per una.
- `No, keep planning`: resti in Plan Mode e aggiungi vincoli o correzioni prima di partire.

<!-- TODO screenshot: la richiesta di approvazione del piano con le opzioni attuali (Yes, and use auto mode / Yes, manually approve edits / No, keep planning). Sostituisce la vecchia fig-03, che mostrava un piano Firebase e le opzioni di approvazione precedenti -->

Con la prima opzione Claude procede da solo: crea `data/` e ci sposta il CSV, scrive `docs/plan.md` e `dashboard.py`, lancia `pip install -r requirements.txt` e poi lo script. Alla fine trovi quattro PNG in `docs/charts/`, pronti da inserire in qualsiasi documento. Se il classificatore blocca un'azione, la trovi in `/permissions`, nella scheda Recently denied, e da lì puoi riprovarla.

::: {.callout .callout-tip}
[Suggerimento]{.callout-title}

Su molte distribuzioni Linux recenti e con il Python di Homebrew, `pip install` fuori da un ambiente virtuale viene rifiutato con l'errore `externally-managed-environment`. Aggiungi al piano un passo che crei l'ambiente con `python3 -m venv .venv` e installi lì le dipendenze: Claude aggiorna anche i comandi di esecuzione.
:::

## 4.4 Dataset grandi e contesto

Il dataset di esempio ha 54 righe e 15 colonne. Quelli che incontri al lavoro sono export da un CRM, log di eventi, dati di fatturazione, e arrivano facilmente a centinaia di migliaia di righe.

### Il problema del contesto

Tutto quello che Claude legge finisce nella finestra di contesto. Con il modello di default è grande, 1M token, ma un export da 500.000 righe non ci sta comunque, e anche solo una parte ti riempirebbe la sessione di numeri che non servono. Su un file così Claude non legge tutto in un colpo: una chiamata a `Read` restituisce al massimo 25.000 token, e un file oltre i 256 KB va letto a pezzi. Più spesso Claude lo esplora con `wc -l`, `head` e comandi simili. L'analisi che ottieni è fatta su un campione, che per i pattern generali spesso basta. Quando il dettaglio conta, chiedigli esplicitamente quante righe ha letto davvero.

Per tenere d'occhio la situazione hai `/context`, che mostra come è divisa la finestra: istruzioni di sistema, tool, server MCP, skill, file di memoria e messaggi. Quando la conversazione si allunga, `/compact` la riassume e libera spazio, e puoi dirgli cosa conservare:

```text
/compact conserva le conclusioni sul piano silver e la struttura delle colonne del CSV
```

Vale poi la regola pratica di un task per sessione. Se dopo l'analisi del churn passi a una domanda che non c'entra, `/clear` e riparti pulito. Il Capitolo 15 entra nei dettagli di contesto e memoria.

### Pattern 1: far scrivere lo script a Claude

Con i file grandi conviene rovesciare l'approccio: invece di far leggere il file a Claude, gli fai scrivere il codice che lo elabora.

```text
Scrivi uno script Python analisi_grandi.py che legge
saas_metrics_full.csv (potenzialmente molto grande)
e produce: conteggio righe per piano, media mensile
del churn rate per regione, i 10 mesi con più cancellazioni.
Lo script deve funzionare anche su file da 500.000 righe.
```

Per un requisito del genere Claude usa pandas leggendo il file a blocchi (`chunksize`), dichiarando i tipi delle colonne (`dtype`) e caricando solo quelle che servono (`usecols`). Lo script lo lanci tu, guardi i risultati e, se uno ti incuriosisce, lo riporti a Claude nel messaggio successivo. Nel contesto entrano poche righe di output al posto di mezzo milione di righe di dati.

### Pattern 2: campioni stratificati

A volte vuoi che Claude veda i dati veri prima di pianificare, ma il file è troppo grande per leggerlo tutto. Chiedi un campione stratificato:

```text
Mostrami 3 righe per ogni valore unico della colonna
"plan" e 3 righe per ogni "region". Voglio capire
la struttura reale dei dati prima di procedere.
```

Claude estrae le righe con `head`, `grep` o due righe di pandas. Hai abbastanza contesto per fare domande sensate senza saturare la finestra.

### Pattern 3: salvare i risultati intermedi

Se l'analisi dura più sessioni, salva i risultati intermedi in JSON e riparti da lì:

```text
Salva il riepilogo dell'analisi che abbiamo appena fatto
in un file analisi_risultati.json. Lo userò come
punto di partenza nella prossima sessione.
```

La sessione successiva comincia così:

```text
@analisi_risultati.json riprendiamo dall'analisi
di ieri. Voglio approfondire il dato sul piano silver.
```

Non ricominci da zero e il ragionamento prosegue da una sessione all'altra. Nel Capitolo 7 vedrai come mettere in `CLAUDE.md` il contesto stabile del progetto (lo stack, il dataset corrente, le decisioni già prese), che Claude legge a ogni avvio.

## 4.5 Da conversazione a script: quando consolidare

Dopo mezz'ora di analisi hai esplorato il dataset, trovato i pattern interessanti e magari visto qualche grafico. Puoi chiudere la sessione e la prossima volta ricominciare da capo, oppure consolidare: trasformare l'esplorazione in uno script riutilizzabile. Claude lo fa bene perché ha tutta la conversazione nel contesto e sa quali risultati ti sono sembrati utili.

### Il prompt di consolidamento

```text
Riassumi tutta l'analisi che abbiamo fatto in uno script
Python analisi.py che, eseguito su un nuovo CSV con la
stessa struttura di saas_metrics.csv, produce:
- un report PDF con i 4 grafici principali (usa matplotlib
  con backend PDF)
- un CSV aggregato saas_aggregato.csv con le metriche
  mensili per piano e per regione
- un file testo riepilogo.txt con i pattern principali
  scritti in italiano per un manager non tecnico

Lo script deve accettare il nome del file CSV come
argomento: python analisi.py dati_luglio.csv
```

Lo script che Claude scrive riprende quello che è emerso nella sessione: le aggregazioni che ti sono servite, i grafici che hai tenuto, il livello di dettaglio giusto per il riepilogo testuale.

Il mese dopo arriva il CSV nuovo e non devi riaprire Claude né rifare l'analisi:

```bash
python analisi.py dati_luglio.csv
```

In pochi secondi hai il PDF con i grafici aggiornati, il CSV aggregato e il riepilogo. La sessione di esplorazione è diventata un tool che rilanci quando vuoi.

### Quando consolidare e quando no

Consolida se sai che ripeterai la stessa analisi su dati nuovi con la stessa struttura: ogni mese, ogni trimestre, su file diversi. Se stai esplorando un dataset una volta sola, o se le domande cambiano ogni volta, lo script non ripaga il tempo che ci metti. In quel caso basta un riepilogo a fine sessione:

```text
Riassumi in 5 bullet point i principali insight
che abbiamo trovato in questa sessione.
```

Incollalo in un documento di progetto e hai comunque traccia del lavoro fatto. Nel Capitolo 5 lo stesso approccio produce un report Excel con pivot table, formule e grafici nativi, generato in Python con openpyxl senza aprire Excel.

## Riepilogo

- Claude legge un CSV direttamente dal disco con `Read`: lo citi con `@` e non devi prepararlo.
- I prompt utili chiedono pattern e conclusioni («quali sono i 3 pattern più importanti?»); le statistiche descrittive servono solo come controllo iniziale.
- Per un output concreto entra in Plan Mode (`Shift+Tab` fino a `plan mode on`, oppure `claude --permission-mode plan`): Claude non modifica niente finché non approvi il piano.
- Il piano si corregge restando in Plan Mode o con `Ctrl+G`; poi scegli se eseguirlo in auto mode o approvando ogni modifica.
- Con i file grandi fai scrivere a Claude lo script che li elabora, controlla `/context` e usa `/compact` dicendo cosa conservare.
- Se ripeterai l'analisi, consolidala in uno script che prende il CSV come argomento.

## Esercizio

Quattro passi, una decina di minuti in tutto. Usa `data/saas_metrics.csv` generato con `genera_dati.py`, oppure un CSV che hai già sul computer.

1. Struttura. Avvia Claude nella cartella del CSV e usa il prompt riusabile di onboarding del §4.1. Controlla che la risposta riporti la struttura completa e tre domande di business.
2. Conclusioni. Scegli una delle tre domande e approfondiscila con un prompt orientato alle conclusioni. Fai almeno un giro in più chiedendo di approfondire il punto più interessante della risposta.
3. Plan Mode. Passa in Plan Mode con `Shift+Tab` e chiedi a Claude di pianificare un grafico che mostri il pattern trovato al passo 2. Modifica almeno un aspetto del piano, poi approvalo e controlla che il grafico venga prodotto.
4. Consolidamento. Chiedi a Claude uno script `analisi_rapida.py` che, ricevuto il CSV come argomento, produca il grafico e un riepilogo testuale di tre righe.

L'esercizio è finito quando `python analisi_rapida.py <file.csv>`, lanciato da te in un terminale fuori da Claude Code, genera il grafico e le tre righe di riepilogo senza errori.
