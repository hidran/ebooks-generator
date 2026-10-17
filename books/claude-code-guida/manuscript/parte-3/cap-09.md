# Capitolo 9. Skill, da comando a capacità riusabile

::: {.chapter-goals}
[Cosa imparerai]{.callout-title}

- Quando un custom command va promosso a skill, e cosa ti dà la cartella in più.
- Come è fatto un `SKILL.md`: i campi del frontmatter e una description che fa scattare la skill al momento giusto.
- Due skill scritte a mano: `report-pdf`, che da un CSV tira fuori un report PDF, e `data-analysis-saas-monthly`, con script, riferimenti e template.
- Come usare lo skill-creator, dove trovare skill pronte e come tenere in ordine quelle che accumuli.

[Prerequisiti]{.callout-title}

Il capitolo 8 (file di comando, argomenti, `` !`comando` ``), il progetto `analisi-saas` dei capitoli 4-6 e il laboratorio `cc-advanced-lab` del capitolo 2.

:::

Nel capitolo 8 hai scritto comandi in `.claude/commands/`: un file, un prompt, una barra per richiamarlo. Vanno benissimo finché il prompt basta da solo. Quando il comando ha bisogno di una guida di stile, di un template per la mail o di uno script Python che faccia i conti sempre nello stesso modo, il file unico diventa stretto: o incolli tutto dentro, e ogni invocazione si porta dietro pagine che servono una volta su dieci, o scrivi "cerca lo script da qualche parte" e speri.

Una skill è la stessa cosa con una cartella intorno. Le istruzioni stanno in `SKILL.md`, accanto metti i file di supporto, e Claude li legge o li esegue solo quando servono. La description fa da interruttore: quando la tua richiesta le corrisponde, Claude carica la skill da solo. Un collega appena arrivato che scrive "mi prepari il report di giugno?" ottiene la procedura del team senza sapere che esiste.

## 9.1 Comandi e skill, un solo sistema

Nella prima edizione comandi e skill erano due meccanismi separati, e i comandi sembravano destinati a sparire. Oggi Claude Code li ha fusi. Un file `.claude/commands/report.md` e una skill `.claude/skills/report/SKILL.md` creano entrambi `/report` e funzionano allo stesso modo. I file di comando sono il formato più vecchio, continuano a funzionare e accettano lo stesso frontmatter delle skill, tranne `name` e `paths`. Per il lavoro nuovo la documentazione consiglia le skill, e se un comando e una skill hanno lo stesso nome vince la skill.

La scelta quindi riguarda la forma: un file solo o una cartella. Io decido così:

| Ti serve | Formato |
| :---- | :---- |
| Un prompt riusabile, senza file di supporto | File in `.claude/commands/`, oppure skill con il solo `SKILL.md` |
| Una procedura che lancia script Python o Bash | Skill con `scripts/` |
| Guide, regole di calcolo o esempi da consultare solo quando servono | Skill con `references/` |
| Testi di base per l'output, come una mail o un'intestazione | Skill con `templates/` |
| Attivazione automatica solo su certi file del progetto | Skill con `paths` |

Due esempi dal libro. `/fix-tests` del capitolo 8 resta un comando: è un prompt e non ha bisogno di niente intorno. Il report mensile SaaS del capitolo 6 invece ha tre script, delle regole di calcolo e un testo fisso per la mail: diventa la skill `data-analysis-saas-monthly` del paragrafo 9.4. Passi alla cartella quando ti accorgi che stai incollando risorse nel file del comando solo per tenerle vicine al prompt.

## 9.2 Anatomia di una skill

### La cartella

Una skill è una cartella con un nome in minuscolo con i trattini, e dentro almeno un file `SKILL.md`. Il resto è facoltativo. Questa è la struttura che uso:

```text
.claude/skills/nome-skill/
├── SKILL.md          obbligatorio: frontmatter e istruzioni
├── references/       guide e regole, lette quando servono
│   ├── style-guide.md
│   └── business-rules.md
├── scripts/          script da eseguire
│   ├── analyze.py
│   └── generate-report.sh
└── templates/        basi per l'output
    ├── email-summary.txt
    └── report-header.md
```

I nomi delle sottocartelle sono una convenzione: Claude Code non li tratta in modo speciale, e lo skill-creator di Anthropic chiama `assets/` quella dei template. Conta che `SKILL.md` dica quando aprire quale file. Claude Code carica una skill a tre livelli:

1. Nome e description sono nel contesto di ogni sessione, anche quando non usi la skill. È da lì che Claude capisce quando servirebbe.
2. Il corpo di `SKILL.md` entra nel contesto quando la skill scatta o quando la invochi tu.
3. I file di supporto entrano solo quando Claude li legge, seguendo le istruzioni del corpo. Gli script vengono eseguiti, e nel contesto arriva solo il loro output.

Il primo livello ha un costo che paghi sempre, e `/skills` te lo mostra skill per skill.

![L'elenco di /skills con le skill di progetto e quelle personali, ognuna con il peso della sua description in token](figures/cap-09/fig-02.png)

L'elenco mette insieme le skill di `.claude/skills` e i comandi di `.claude/commands`. Il secondo livello conviene tenerlo corto: lo skill-creator suggerisce di restare sotto le 500 righe e di spostare il resto in file separati, richiamati da `SKILL.md`.

### Il frontmatter

`SKILL.md` comincia con un blocco YAML tra due righe `---`, seguito dalle istruzioni in Markdown. Tutti i campi sono facoltativi, ma senza `description` Claude non ha modo di sapere quando usare la skill. Quelli che ti servono davvero:

| Campo | A cosa serve |
| :---- | :---- |
| `name` | Il nome, e quindi il comando: `report-pdf` diventa `/report-pdf`. Minuscole, numeri e trattini. Se manca vale il nome della cartella |
| `description` | Cosa fa la skill e quando usarla. Claude decide da qui se caricarla |
| `when_to_use` | Altri casi in cui usarla, aggiunti alla description. Insieme vengono troncate a 1.536 caratteri |
| `argument-hint` | Il suggerimento sugli argomenti che compare nel menu, per esempio `<file-csv>` |
| `arguments` | I nomi degli argomenti posizionali, da usare nel corpo come `$nome` |
| `disable-model-invocation` | Con `true` la skill parte solo quando la scrivi tu |
| `user-invocable` | Con `false` sparisce dal menu `/` e la usa solo Claude |
| `allowed-tools` | I tool che Claude usa senza chiedere mentre la skill è attiva |
| `model`, `effort` | Modello e livello di ragionamento per il resto del turno |
| `context: fork` | Esegue la skill in un subagent; il campo `agent` dice quale |
| `paths` | Glob che limitano l'attivazione automatica ai file che corrispondono |

Gli argomenti funzionano come nei comandi del capitolo 8: `$ARGUMENTS` prende tutto, `$0`, `$1` e così via prendono le parole per posizione, e `${CLAUDE_SKILL_DIR}` è il percorso della cartella della skill, utile per lanciare i suoi script da qualunque directory. Con `arguments` dai un nome alle posizioni, e il corpo diventa più leggibile: `$csv` invece di `$0`. Lo usi nel paragrafo 9.4.

Su `allowed-tools` c'è un equivoco frequente. Il campo aggiunge permessi e basta: i tool elencati partono senza conferma finché la skill è attiva, fino al tuo messaggio successivo, e gli altri restano disponibili con i permessi normali della sessione. Per impedire a una skill di usare un tool il campo è `disallowed-tools`.

Con `context: fork` la skill gira in un subagent con un contesto suo, che parte vuoto: non vede la conversazione, quindi il corpo di `SKILL.md` deve contenere tutto quello che serve. Dalla versione 2.1.218 una skill in fork gira in background e il tuo turno non la aspetta; per aspettare il risultato aggiungi `background: false`. Serve per i lavori lunghi che riempirebbero il contesto principale di output intermedio (i subagent sono il tema del capitolo 10).

Se vuoi caricare la skill anche su claude.ai o usarla con le API, lo standard Agent Skills accetta solo `name`, `description`, `license`, `compatibility`, `metadata` e `allowed-tools`; il resto è un'estensione di Claude Code.

### La description è il trigger

L'errore più comune la prima volta è scrivere la description come documentazione per un collega. La legge un modello, che da quelle due righe deve capire se la tua richiesta rientra nella skill. Una description vaga produce una skill che non scatta mai, o che scatta quando non c'entra:

```yaml
# troppo vaga
description: Analizza dati.
```

Questa invece dice cosa fa, su quali dati e con quali parole la chiederà l'utente:

```yaml
# precisa
description: Esegue un'analisi statistica di una colonna di un file CSV
  (tipo, count, valori mancanti, media, deviazione standard, min, max,
  quartili, outlier). Usala quando l'utente chiede di analizzare,
  descrivere, profilare o ispezionare una colonna, anche in inglese
  (describe column, profile column).
```

Comincia da cosa fa, con un verbo. Nomina il dominio (CSV, colonna, report) e i formati. Aggiungi una frase esplicita su quando usarla, con le parole che userà davvero chi scrive il prompt: se il team lavora in italiano e in inglese, mettile in tutte e due le lingue. Le istruzioni dello skill-creator aggiungono un consiglio utile: Claude tende a usare le skill meno di quanto dovrebbe, quindi una description un po' insistente ("usala anche se l'utente non nomina esplicitamente il report") funziona meglio di una prudente. Il limite opposto è la lunghezza: la description pesa in ogni sessione, e quattro o cinque righe bastano quasi sempre.

Un ultimo dettaglio spiega molti "la mia skill non parte": Claude consulta le skill per i compiti che non risolve facilmente da solo. Una richiesta di un passo, tipo "leggi questo file", può non attivare nessuna skill anche con una description perfetta, perché Claude la esegue direttamente con i tool di base. Le richieste con più passaggi, o specifiche di un dominio, sono quelle in cui la description fa la differenza.

## 9.3 La prima skill: report-pdf

Parti da una skill piccola, nel laboratorio del capitolo 2. `cc-advanced-lab` ha un CSV di tre righe, `data/vendite.csv`, con le vendite di gennaio, febbraio e marzo 2026. La skill `report-pdf` ne ricava una tabella di riepilogo in chat e lo stesso report in PDF, con ReportLab come nel capitolo 6.

```bash
cd ~/cc-advanced-lab
mkdir -p .claude/skills/report-pdf
```

Crea `.claude/skills/report-pdf/SKILL.md`:

```markdown
---
name: report-pdf
description: Prepara un report di vendite da un file CSV, con una tabella di riepilogo in chat e lo stesso report in PDF nella cartella output/. Usala quando l'utente chiede un report, un riepilogo, i totali o un PDF a partire da un file CSV.
argument-hint: <file-csv>
allowed-tools: Read Write Bash(python3 *)
---

Il file da usare è $ARGUMENTS. Se è vuoto, usa il CSV citato nella
richiesta; se non ce n'è nessuno, chiedi quale analizzare.

1. Leggi il CSV e individua la colonna numerica.
2. Rispondi con una tabella Markdown con il numero di righe, il totale,
   il minimo, il massimo e la media della colonna, la media con due
   decimali.
3. Crea output/report-<nome del CSV senza estensione>.pdf con ReportLab:
   titolo "Report vendite", data di oggi, la tabella del punto 2 e,
   sotto, tutte le righe del CSV. Usa lo script output/genera_pdf.py,
   che prende il percorso del CSV come primo argomento: se non esiste,
   scrivilo, poi lancialo con python3.
4. Se ReportLab non è installato, fermati e suggerisci
   `pip install reportlab`. Non installarlo da solo.

Non modificare mai il CSV di input.
```

La description contiene le parole con cui chiederai il lavoro: report, riepilogo, totali, PDF, CSV. `allowed-tools` evita le conferme per lo script e per `python3` in modalità Manual. Il punto 3 fa riusare lo script se esiste già: la prima volta Claude lo scrive, dalla seconda il PDF esce sempre uguale. La skill sta tutta in un file di proposito, perché nel capitolo 14 la copi in un plugin con un solo `cp` di `SKILL.md`. ReportLab invece ti serve: se manca nell'ambiente Python del laboratorio, `pip install reportlab`.

Se Claude Code era già aperto, lancia `/reload-skills`, che rilegge le cartelle delle skill e dei comandi, poi `/skills`: `report-pdf` deve comparire tra le skill di progetto. Adesso provala senza nominarla:

```text
mi prepari un report in PDF delle vendite di data/vendite.csv?
```

Claude carica la skill e risponde con la tabella. I numeri devono essere questi: 3 righe, totale 358, minimo 95, massimo 143, media 119,33. Il totale è lo stesso che controlla `tests/test_report.py`, quindi hai un riscontro immediato. Il PDF finisce in `output/report-vendite.pdf`. Poi prova l'invocazione esplicita, che è quella che userai negli script e nel capitolo 14:

```text
/report-pdf data/vendite.csv
```

Se con il prompt in linguaggio naturale Claude risponde senza caricare la skill, il problema è quasi sempre la description: non contiene le parole con cui hai chiesto. Quando funziona, committa `.claude/skills/report-pdf/`, e se non vuoi i PDF nel repository aggiungi `output/` al `.gitignore`.

## 9.4 Una skill completa: data-analysis-saas-monthly

Adesso la skill anticipata nel capitolo 6. Da un CSV di metriche SaaS come `saas_metrics.csv` produce tre file per un cliente (il report PDF, una dashboard HTML statica con Chart.js che si apre senza server, l'Excel con dati e sommario) e la mail che li accompagna.

La metto nel progetto perché colonne e regole di calcolo sono di questo progetto: in `~/.claude/skills/` peserebbe sul contesto di ogni sessione, anche dove non serve.

### Passo 1: la struttura

```bash
cd ~/progetti/analisi-saas
mkdir -p .claude/skills/data-analysis-saas-monthly/{scripts,references,templates}
```

Se preferisci, chiedilo a Claude con un prompt di una riga: per le cartelle non c'è differenza.

### Passo 2: SKILL.md

Crea `.claude/skills/data-analysis-saas-monthly/SKILL.md`:

```markdown
---
name: data-analysis-saas-monthly
description: Genera il report mensile SaaS di un cliente da un CSV di metriche (mrr, churn_rate, plan, region) e produce PDF, dashboard HTML ed Excel. Usala quando l'utente chiede il report mensile, l'analisi del mese o un riepilogo di MRR e churn per un cliente, anche se non nomina i formati (monthly report, SaaS metrics, MRR report).
argument-hint: <csv> <cliente> <mese>
arguments: [csv, cliente, mese]
allowed-tools: Read Bash(python3 *)
---

# Report mensile SaaS

Input: il CSV $csv, il cliente $cliente, il mese $mese.
Se manca uno dei tre, chiedilo prima di cominciare.
Tutti i file prodotti vanno in output/$cliente/.
I percorsi references/, scripts/ e templates/ sono relativi a
${CLAUDE_SKILL_DIR}.

## Risorse

- references/struttura-csv.md: colonne obbligatorie e opzionali.
- references/regole-metriche.md: come si calcolano le metriche derivate.
- templates/email-riepilogo.txt: la mail che accompagna i file.
- scripts/: gli script si lanciano, non serve leggerli.

## Fase 1: validazione

1. Confronta le colonne di $csv con references/struttura-csv.md.
   Se manca una colonna obbligatoria, fermati e dimmi quale.
2. Lancia `python3 ${CLAUDE_SKILL_DIR}/scripts/metriche.py $csv output/$cliente`.
   Lo script stampa il sommario per mese e scrive metriche.xlsx.

## Fase 2: analisi

3. Sul sommario applica references/regole-metriche.md: variazione
   mese su mese, outlier, trend degli ultimi tre mesi.
4. Non ricalcolare a mano i numeri che lo script ha già stampato.

## Fase 3: output

5. Lancia scripts/genera_grafici.py e scripts/genera_report.py con
   `--csv $csv --outdir output/$cliente`; a genera_report.py passa
   anche `--cliente "$cliente, $mese"`.
6. Scrivi output/$cliente/dashboard.html: una sola pagina con Chart.js
   da CDN e i dati del sommario incorporati come JSON, senza server.
7. Compila templates/email-riepilogo.txt e salvalo come
   output/$cliente/email.txt.

## Fase 4: chiusura

8. Elenca i file prodotti con il loro percorso.
9. Indica le tre metriche che meritano attenzione e perché.
10. Proponi un prossimo passo concreto.
```

Le fasi servono anche a te: quando qualcosa va storto vedi subito se il lavoro si è fermato alla validazione o all'output. Il punto 4 c'è perché, senza, Claude può rifare i conti per conto suo sul CSV e arrivare a un totale diverso da quello dello script; così i numeri li calcola il codice e Claude si occupa di commentarli.

### Passo 3: i riferimenti

`references/struttura-csv.md` descrive il CSV che la skill si aspetta, con le colonne del dataset del capitolo 4:

```markdown
# Struttura attesa del CSV

Colonne obbligatorie:
- month (int, 1-12)
- plan (string: free | silver | gold)
- region (string: Europe | North America | Asia Pacific)
- new_signups (int)
- cancellations (int)
- mrr (float, euro)
- churn_rate (float, percentuale)

Colonne opzionali (se mancano, salta le metriche che le usano):
- date (YYYY-MM-DD)
- retention_rate
- support_tickets
- ai_voice_usage, ai_text_usage
```

`references/regole-metriche.md` fissa le regole di business, quelle che altrimenti Claude interpreterebbe a modo suo ogni volta:

```markdown
# Regole per le metriche

- MRR del mese: somma di mrr sulle righe silver e gold. Il piano free
  non contribuisce e va escluso.
- Variazione MoM: (MRR del mese - MRR del mese prima) / MRR del mese prima.
- Churn del mese: media di churn_rate sulle righe a pagamento. Nel report
  chiamalo "churn medio", perché non è ricalcolato sui clienti.
- Outlier: valori oltre 2 deviazioni standard dalla media della stessa
  combinazione di piano e regione. Vanno segnalati, non rimossi.
- Trend: regressione lineare semplice sull'MRR degli ultimi tre mesi.
```

### Passo 4: gli script

Due script ce li hai già: `tools/genera_grafici.py` e `tools/genera_report.py` del capitolo 6. Lavorano sul CSV del progetto, quindi nelle copie per la skill serve poter indicare il file e la cartella di output:

```text
Copia tools/genera_grafici.py e tools/genera_report.py in
.claude/skills/data-analysis-saas-monthly/scripts/.
Nelle copie aggiungi gli argomenti --csv (file di input) e --outdir
(cartella di output, default output/); a genera_report.py aggiungi
anche --cliente, da mettere nel titolo del PDF.
Lascia invariati gli originali in tools/.
```

Il terzo script è nuovo. Valida le colonne, calcola il sommario per mese e scrive l'Excel. Salvalo come `.claude/skills/data-analysis-saas-monthly/scripts/metriche.py`:

```python
#!/usr/bin/env python3
"""Valida il CSV delle metriche SaaS, stampa il sommario e scrive l'Excel.

Uso: python3 metriche.py <csv> <cartella-output>
"""
import sys
from pathlib import Path

import pandas as pd

RICHIESTE = [
    "month", "plan", "region", "new_signups",
    "cancellations", "mrr", "churn_rate",
]


def carica(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    mancanti = [c for c in RICHIESTE if c not in df.columns]
    if mancanti:
        sys.exit(f"Colonne mancanti: {mancanti}")
    return df


def sommario(df: pd.DataFrame) -> pd.DataFrame:
    pagati = df[df["plan"] != "free"]
    per_mese = pagati.groupby("month").agg(
        mrr=("mrr", "sum"),
        nuovi=("new_signups", "sum"),
        cancellazioni=("cancellations", "sum"),
        churn_medio=("churn_rate", "mean"),
    )
    per_mese["mrr_mom_pct"] = per_mese["mrr"].pct_change() * 100
    return per_mese.round(2).reset_index()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("Uso: python3 metriche.py <csv> <cartella-output>")
    df = carica(sys.argv[1])
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    tabella = sommario(df)
    with pd.ExcelWriter(out / "metriche.xlsx", engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Dati", index=False)
        tabella.to_excel(writer, sheet_name="Sommario", index=False)
    print(tabella.to_string(index=False))
    print(f"Excel scritto in {out / 'metriche.xlsx'}")
```

Lo script stampa il sommario su stdout perché è così che i numeri arrivano a Claude: nel contesto entra la tabella di sei righe, non il codice e non le 54 righe del CSV. Se manca una colonna obbligatoria esce con un messaggio chiaro, e Claude ti riporta quello invece di analizzare dati sbagliati.

### Passo 5: il template della mail

`templates/email-riepilogo.txt`:

```text
Oggetto: Report SaaS mensile, [CLIENTE] [MESE]

Ciao [NOME],

ecco il riepilogo delle metriche di [CLIENTE] per [MESE].

NUMERI DEL MESE
MRR totale:        [MRR_TOTALE] EUR
Variazione MoM:    [DELTA_MOM]%
Churn medio:       [CHURN]%
Nuovi iscritti:    [NUOVI]

TRE COSE DA GUARDARE
1. [PUNTO_1]
2. [PUNTO_2]
3. [PUNTO_3]

IN ALLEGATO
report.pdf       report completo con grafici
metriche.xlsx    dati grezzi e sommario per mese
dashboard.html   grafici interattivi, si apre nel browser

PROSSIMO PASSO
[SUGGERIMENTO]

Generato con Claude Code, skill data-analysis-saas-monthly
```

### Passo 6: la prova

Lancia `/reload-skills` e controlla con `/skills` che la skill compaia tra quelle di progetto. Poi chiedi il lavoro senza nominarla, come farebbe un collega:

```text
Ho le metriche SaaS di giugno in data/saas_metrics.csv.
Mi prepari il report mensile per startup_alpha?
```

Claude carica la skill, lancia `metriche.py`, legge le regole, genera i file in `output/startup_alpha/` e chiude con l'elenco dei file e le tre metriche da guardare. La forma esplicita, utile quando hai più clienti in fila come l'agenzia del capitolo 6, è:

```text
/data-analysis-saas-monthly data/saas_metrics.csv startup_alpha giugno
```

### Gli edge case

Dopo le prime prove ne trovi sempre qualcuno: un cliente con colonne in meno, un CSV esportato da un gestionale vecchio in latin-1, un mese con MRR a zero che fa saltare la variazione mese su mese. Aggiungi una sezione in fondo a `SKILL.md`:

```markdown
## Edge case

- Colonne opzionali mancanti: salta le metriche che le usano e
  scrivilo nell'executive summary.
- MRR del mese precedente a zero (cliente nuovo): la variazione MoM
  è n/d, non un errore e non un valore infinito.
- CSV non trovato: chiedi il percorso completo prima di procedere.
- Lo script fallisce con UnicodeDecodeError: salva una copia del CSV
  in UTF-8 in output/$cliente/ e rilancia su quella.
```

Aggiungi una regola alla volta e provala con un CSV costruito apposta. Se una modifica a `SKILL.md` non sembra arrivata, `/reload-skills`.

## 9.5 Lo skill-creator

Scrivere `SKILL.md` a mano serve a capire come è fatta una skill. Nel lavoro di tutti i giorni è più rapido lo skill-creator, una skill di Anthropic che costruisce altre skill attraverso una conversazione e poi le mette alla prova. Si installa come plugin dal marketplace ufficiale:

```text
/plugin install skill-creator@claude-plugins-official
```

Dopo `/reload-plugins` la invochi con il prefisso del plugin, `/skill-creator:skill-creator`, oppure scrivi che vuoi creare o migliorare una skill e lascia che scatti da sola. Se accedi con un account claude.ai su cui lo skill-creator è attivo, la skill arriva già sincronizzata: `/skills` la elenca sotto `claude.ai sync` e la lanci come `/anthropic-skills:skill-creator`, senza installare il plugin.

### Come lavora

La prima cosa che fa è guardare la conversazione. Se hai appena fatto un lavoro a mano, per esempio i grafici di un CSV, ti propone di trasformare quello in una skill e ne ricava i passaggi dalla cronologia.

![Lo skill-creator propone le opzioni in base alla conversazione: migliorare una skill appena usata, crearne una nuova o trasformare in skill il lavoro sui grafici](figures/cap-09/fig-01.png)

Se parti da zero, ti fa quattro domande: cosa deve fare la skill, quando deve attivarsi, che formato ha l'output e se vuoi dei casi di test. Poi chiede degli edge case, dei formati di input, delle dipendenze. Per una skill di profiling dei CSV, alla domanda su cosa fare e quando basta una risposta come questa:

```text
Analizza un file CSV facendo profiling completo per rilevare anomalie e
outlier. Usala quando l'utente chiede analyze, profile, describe, check
su una colonna o su un dataset, oppure quando chiede di trovare outlier
o anomalie statistiche.
```

Da questa risposta esce la description del frontmatter, già scritta per far scattare la skill. Se nella conversazione dici che può usare Python, lo skill-creator scrive anche lo script in `scripts/`.

La parte che vale l'installazione è la verifica. Lo skill-creator scrive alcuni prompt di prova e per ognuno lancia due subagent nello stesso turno, uno con la skill e uno senza. I risultati li vedi affiancati in una pagina nel browser, commenti ogni output, e lui riscrive la skill e rilancia. Se nota che tutte le esecuzioni hanno scritto lo stesso script di supporto, ti propone di metterlo in `scripts/` una volta per tutte.

Alla fine propone di ottimizzare la description. Prepara una ventina di richieste, metà che devono attivare la skill e metà che le somigliano ma non devono, le lancia tre volte ciascuna, prova fino a cinque versioni della description e tiene quella che va meglio su un gruppo di richieste tenuto da parte. Ogni esecuzione consuma il tuo piano, quindi su una skill banale salta questo passo.

### Quando farne a meno

Lo skill-creator conviene quando la skill ha degli script o quando vuoi misurare la differenza con e senza skill prima di condividerla. Scrivo a mano quando modifico una skill esistente e quando la skill è un `SKILL.md` di venti righe come `report-pdf`: lì interviste e benchmark costano più della skill. Le due strade si combinano, con lo scaffolding dallo skill-creator e la rifinitura a mano. Se hai installato Superpowers nel capitolo 8, la sua skill `writing-skills` copre lo stesso terreno con un approccio più vicino al TDD.

::: {.callout .callout-prompt}
[Prompt riusabile]{.callout-title}

Lo schizzo di una nuova skill, da dare a Claude direttamente o da usare per chiarirti le idee prima dello skill-creator:

```text
Voglio creare una skill per Claude Code che si chiama [NOME-SKILL].

Deve attivarsi quando l'utente chiede [DESCRIVI IL TRIGGER IN PAROLE NATURALI].
Il workflow prevede questi passi:
1. [PASSO 1]
2. [PASSO 2]
3. [PASSO 3]

Ha bisogno di [script Python / references / templates]? [SÌ/NO, specifica]

Crea la struttura di cartelle in .claude/skills/[NOME-SKILL]/ (oppure in
~/.claude/skills/[NOME-SKILL]/ se serve in tutti i miei progetti),
scrivi SKILL.md con un frontmatter ottimizzato per il trigger automatico,
e aggiungi eventuali file di supporto nelle sottocartelle appropriate.
```
:::

## 9.6 Skill pronte

Prima di scrivere una skill da zero, cerca se qualcuno l'ha già fatta. Le skill di terzi arrivano quasi sempre dentro un plugin, da un marketplace. Quello ufficiale di Anthropic, `claude-plugins-official`, è configurato al primo avvio; quello della community, `claude-community` (repository `anthropics/claude-plugins-community`), lo aggiungi quando nell'ufficiale non trovi quello che cerchi. Nell'ufficiale molti vendor pubblicano le loro skill: a ottobre 2026 c'erano per esempio `duckdb-skills` e `huggingface-skills`, accanto allo skill-creator e a Superpowers. Li sfogli nella scheda Discover di `/plugin`; il capitolo 14 spiega come valutarli.

Per uno sviluppatore il punto di partenza resta Superpowers, che hai installato nel capitolo 8. Le sue skill da conoscere subito:

| Skill | Cosa fa |
| :---- | :---- |
| `test-driven-development` | Guida il ciclo TDD: prima il test che fallisce, poi il codice |
| `systematic-debugging` | Divide il debug in fasi: riproduzione, ipotesi, verifica, fix |
| `brainstorming` | Esplora le alternative di design prima di scrivere codice |
| `verification-before-completion` | Controlla che il lavoro sia finito davvero prima di dichiararlo chiuso |
| `writing-skills` | Progetta e verifica skill nuove |

Per la code review non serve un plugin: `/code-review` è una skill inclusa in Claude Code, e la usi sulla Photogallery nel capitolo 22.

::: {.callout .callout-warning}
[Attenzione]{.callout-title}

Prima di installare una skill di terzi apri il suo `SKILL.md` nel repository e leggilo. Le righe `` !`comando` `` girano sulla tua macchina appena la skill si attiva, prima che Claude veda qualcosa, e gli script in `scripts/` girano con i tuoi permessi. Leggendo scopri anche cosa si aspetta dal progetto: alcune skill danno per scontata una certa struttura di cartelle o tool già installati come pytest o eslint. Se non ti fidi dell'iniezione di comandi, `"disableSkillShellExecution": true` nelle impostazioni la spegne.
:::

Una skill tua la togli cancellando la sua cartella. Quelle dei plugin le gestisci dal plugin: la scheda Installed di `/plugin` lo disattiva o lo rimuove, e da terminale ci sono `claude plugin update` e `claude plugin uninstall`.

## 9.7 Organizzare le skill

### Dove vivono

| Livello | Percorso | Note |
| :---- | :---- | :---- |
| Personale | `~/.claude/skills/<nome>/SKILL.md` | In tutti i tuoi progetti, su questa macchina |
| Progetto | `.claude/skills/<nome>/SKILL.md` | Nel repository, la riceve chi lo clona |
| Sottocartella | `<cartella>/.claude/skills/...` | Con nomi uguali si invoca come `/apps/web:deploy` |
| `--add-dir` | `.claude/skills/` nelle cartelle aggiunte | Utile per le prove |
| Plugin | `<plugin>/skills/<nome>/SKILL.md` | Con il prefisso: `/nome-plugin:nome-skill` |
| Account claude.ai | Skill sincronizzate | Prefisso `anthropic-skills:` |

La regola che seguo: in `~/.claude/skills/` i flussi generici che uso ovunque, in `.claude/skills/` quelli legati al dominio del progetto, come le due skill di questo capitolo. Le skill di progetto si committano, e chi fa `git pull` le riceve senza istruzioni di setup.

### Nomi e sincronizzazione

Dopo qualche mese una lista di cartelle come `report-generator`, `my-skill-v2`, `test-cosa` non ti dice più cosa è stabile e cosa è un esperimento. Io uso tre prefissi:

| Prefisso | Significato | Esempio |
| :---- | :---- | :---- |
| `personal-` | Skill personali, da non condividere | `personal-daily-standup` |
| `team-` | Skill del team, committate nel repo | `team-code-review-checklist` |
| `wip-` | Skill in sviluppo, non ancora stabili | `wip-deploy-to-k8s` |

Le skill personali le tengo in un repository di dotfiles, con un link simbolico al posto della cartella in `~/.claude/`:

```bash
# struttura nel repo dotfiles:
#   dotfiles/claude/skills/personal-daily-standup/
#   dotfiles/claude/skills/personal-code-explain/
ln -s ~/dotfiles/claude/skills ~/.claude/skills
```

Se `~/.claude/skills` esiste già, sposta prima il contenuto nel repository, altrimenti `ln` crea il link dentro la cartella.

Le skill sperimentali stanno fuori dai percorsi che Claude Code legge, in `~/skills-wip/.claude/skills/`, dove non pesano su nessuna sessione. Per provarne una avvio `claude --add-dir ~/skills-wip`, che le carica solo per quella sessione. Quando è stabile la sposto nella posizione definitiva e tolgo `wip-`.

### Quanto costano

Ogni skill ti costa la sua description in ogni sessione. Con tre skill non te ne accorgi; con trenta, tra le tue e quelle dei plugin, occupi una fetta di contesto e aumentano le occasioni in cui scatta quella sbagliata. Per le skill che lanci solo tu, come un deploy, `disable-model-invocation: true` toglie anche la description dal contesto: Claude non può più usarla da solo, quindi non ha bisogno di vederla. Con `paths` invece limiti l'attivazione automatica ai file che contano, per esempio ai CSV di `data/`.

Il peso di ogni description lo vedi in `/skills`. Nel capitolo 15 usi `/skill-doctor`, che affianca il costo in contesto alla frequenza d'uso e ti dice quali skill valgono lo spazio che occupano.

### Quando una skill non compare

Se una skill appena creata non compare in `/skills`, controlla nell'ordine:

1. Il file si chiama esattamente `SKILL.md` e sta un livello sotto `skills/`, come in `.claude/skills/report-pdf/SKILL.md`.
2. Il frontmatter è YAML valido: due righe `---`, spazi e non tabulazioni, virgolette chiuse.
3. `name` è in minuscolo con i trattini, e conviene che coincida con il nome della cartella: lo standard Agent Skills lo richiede.
4. Hai lanciato `/reload-skills` dopo aver creato la cartella.
5. Non c'è un'altra skill con lo stesso nome a un livello diverso.

Se non trovi il problema, incolla il file a Claude e descrivigli cosa succede.

## Riepilogo {.unlisted}

- Comandi e skill sono lo stesso sistema: il file in `.claude/commands/` basta per un prompt, la cartella `.claude/skills/<nome>/` serve per script, riferimenti e template.
- Di ogni skill Claude vede sempre nome e description; il corpo arriva quando la skill scatta, i file di supporto quando le istruzioni li richiamano.
- La description decide se la skill parte: cosa fa, su quali dati, con quali parole la chiederà l'utente.
- Negli script calcola i numeri e stampali, e nel `SKILL.md` di' a Claude di non rifarli a mano.
- Lo skill-creator, dal marketplace ufficiale, scrive la skill e la confronta con un'esecuzione senza.
- Le skill di dominio vanno nel progetto e si committano, quelle generiche in `~/.claude/skills/`; `/skills` e `/skill-doctor` ti dicono quanto pesano.

## Esercizio {.unlisted}

Scegli un lavoro che ripeti almeno una volta a settimana: la revisione di una PR, il changelog di un rilascio, i test per una funzione nuova, il setup di un ambiente di sviluppo.

1. Installa lo skill-creator e chiedigli di creare una skill per quel lavoro.
2. Rispondi alle sue domande: cosa fa, quando deve attivarsi, che output produce, quali edge case conosci.
3. Accetta la verifica con i prompt di prova e confronta gli output con e senza skill.
4. Apri il `SKILL.md` generato e rileggi la description: deve contenere le parole che useresti tu per chiedere quel lavoro.
5. In un progetto reale scrivi una richiesta in linguaggio naturale, senza nominare la skill.

L'esercizio è fatto quando la skill compare in `/skills`, scatta al punto 5 senza che tu la nomini e, nel confronto del punto 3, il risultato con la skill è migliore di quello senza. Ci vuole circa mezz'ora.

Se vuoi chiarirti le idee prima di aprire lo skill-creator, parti dal prompt nella cartella `cap-08/` del repository `github.com/hidran/claude-code-book-snippets` (numerazione della prima edizione): ti fa fissare nome, trigger e passi della skill.
