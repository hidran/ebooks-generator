# Capitolo 16. Una landing page dall'idea al deploy su Firebase

## Cosa imparerai

- Usare il visual companion di Superpowers per decidere il design su mockup HTML prima di scrivere una riga di React.
- Trasformare i mockup approvati in una spec e in un piano a task atomici, ed eseguirlo un task alla volta con review e commit.
- Replicare un design esistente, per esempio una pagina fatta con Lovable, partendo da uno screenshot.
- Pubblicare la landing su Firebase Hosting, passando da un preview channel prima della produzione.

## Prerequisiti

Node.js 20 o successivo, un account Google per la console Firebase e il plugin Superpowers installato (capitolo 8). La Firebase CLI la installiamo strada facendo.

Una landing page è il progetto giusto per mettere insieme per la prima volta tutto quello che hai visto finora. È solo frontend: niente backend, niente database, niente autenticazione. Il deploy è semplice. La struttura è prevedibile (hero, features, pricing, testimonial, FAQ, footer), però ha abbastanza pezzi da richiedere un piano, una suddivisione in componenti e qualche giro di iterazione sul design.

Il prodotto si chiama FluentAiPro: un'app immaginaria per imparare le lingue con un tutor AI, con conversazioni in oltre 50 lingue, feedback sulla pronuncia e percorsi adattivi. Il prodotto resta immaginario: costruiamo la pagina che lo presenta e porta l'utente alla registrazione, in React, Vite e Tailwind CSS, con deploy su Firebase Hosting.

Il codice è nel repo companion `github.com/hidran/fluentaipro-claude-landingpage`. Ogni branch è una fotografia del progetto alla fine di una sezione: `book/cap-10-1-mockups`, `book/cap-10-2-spec`, `book/cap-10-3-execution`, `book/cap-10-5-deploy-ready`. Il numero 10 viene dalla prima edizione, dove questo era il capitolo 10. I branch hanno tenuto il nome per non rompere i link già in giro. Lo stack reale del repo è React 19, Vite 6, Tailwind CSS 4.2 e Vitest 4.

Il capitolo è lungo perché copre tutto il percorso, dall'idea all'URL pubblico. Leggilo con il terminale aperto.

## 16.1 Il visual companion, dal "voglio una landing" al mockup

### Perché i mockup prima del codice

Il visual companion fa parte della skill `brainstorming` di Superpowers. Genera bozze HTML e CSS, le serve da un piccolo server locale e te le mostra nel browser. Tu commenti in linguaggio naturale, Claude aggiorna la bozza, ricarichi la pagina.

Il problema che risolve lo conosci. Descrivi a Claude un'interfaccia ("una hero scura, titolo grande, due bottoni, un'immagine a destra") e ottieni codice che rispetta la descrizione alla lettera. Il risultato può essere corretto e brutto. Per sistemarlo devi leggere i componenti, capire cosa ha fatto Claude, correggere, aspettare l'HMR. Ogni giro costa tempo e token.

Con il visual companion quel giro avviene prima, su file HTML statici: niente dipendenze da installare, niente progetto React da avviare. Quando il mockup ti convince, passi al codice. È la stessa separazione tra decidere e costruire che trovi nello Spec Driven Development dei capitoli 17-19, applicata al design.

### Setup

Crea una cartella vuota e avvia Claude Code al suo interno:

```bash
mkdir fluent-ai-landing && cd fluent-ai-landing
git init
claude
```

Il `git init` subito serve dopo: ogni task del piano diventerà un commit. Controlla con `/status` di essere sull'account giusto.

Poi entra in Plan Mode: premi `Shift+Tab` finché la barra di stato mostra `plan mode on`, oppure usa `/plan`. In Plan Mode Claude esplora e propone, ma non modifica file finché non approvi.

### Il prompt iniziale

```text
Voglio costruire una landing page per FluentAiPro,
una web app per imparare le lingue con il supporto dell'AI.
Gli utenti possono:
- praticare in conversazione con un tutor AI in oltre 50 lingue
- ricevere feedback in tempo reale su pronuncia e grammatica
- seguire percorsi di apprendimento adattivi
- ascoltare podcast tematici in lingua straniera

Comincia a esplorare il progetto e proponimi un piano.
Voglio che tu usi il visual companion per mostrarmi bozze
visive prima di toccare il codice.
```

Claude guarda la cartella (vuota), carica la skill `brainstorming` e ti chiede se vuoi usare il companion nel browser. Rispondi di sì. A quel punto lancia lo script `start-server.sh` della skill: in auto mode di solito passa da solo, in Manual mode te lo fa approvare.

Il server ascolta su `localhost` con una porta scelta a caso, e Claude ti dà l'indirizzo completo da aprire, chiave di sessione compresa. Le bozze finiscono nella cartella del progetto, sotto `.superpowers/brainstorm/<id-sessione>/`. Nel branch `book/cap-10-1-mockups` trovi quelli della mia sessione: `sections.html`, `approaches.html`, `hero-design.html` e `hero-design-v2.html`, `features-design.html` e `features-design-v2.html`, `social-pricing.html`, `pricing-v2.html`. Si aprono con un doppio clic, senza build. Il server si spegne da solo dopo quattro ore di inattività. Se riprendi il lavoro il giorno dopo, Claude lo riavvia sulla stessa porta.

### Le domande del brainstorming

Prima di disegnare, la skill fa domande, una alla volta. Alcune arrivano nel terminale, altre come pagina cliccabile nel browser. Queste sono le risposte che ho dato io (adattale a gusto):

- Call to action principale: "Start for free". L'obiettivo è la registrazione diretta, senza lista d'attesa.
- Audience: studenti e professionisti, con lo stesso peso. Il tono non deve escludere nessuno dei due.
- Sezioni: la pagina `sections.html` ne propone otto (Hero, Features, Social proof, Pricing, Language showcase, App demo, FAQ, Footer con CTA finale). Le ho selezionate tutte.

Subito dopo arriva `approaches.html` con tre direzioni visive: A, Glassmorphism (fondo scuro, card in vetro smerigliato, gradiente dal viola al ciano, alone luminoso sullo sfondo), consigliata da Claude; B, Deep Space + Gold (blu notte e accento oro); C, Stark Minimal (quasi nero, tipografia bianca, zero decorazioni). Per un'app AI ho scelto la A.

### Tre round di iterazione

Da qui Claude disegna una sezione alla volta, e ogni bozza è un punto di partenza. Il suffisso `-v2` nei nomi dei file corrisponde ai miei commenti.

Il primo round riguarda hero e navbar. La struttura era giusta, le proporzioni no:

```text
Va bene, ma i link del menu devono essere più grandi
ed evidenziati quando la sezione è attiva.
Il titolo della hero deve essere più grande: è il messaggio principale.
```

Claude riscrive l'HTML in pochi secondi, ricarichi e vedi `hero-design-v2.html`. Sono modifiche di CSS: nessun componente, nessun bundle.

Il secondo round tocca features e pricing. Le card avevano testo piccolo e poco contrasto, e i prezzi erano segnaposto:

```text
Card delle features: testo più grande e più contrasto
tra titolo e descrizione.
Pricing: usa questi piani reali:
- Free: 0 €/mese, 10 conversazioni AI al mese, 1 lingua
- Silver: 12,99 €/mese, conversazioni illimitate, 3 lingue
- Gold: 24,99 €/mese, tutte le 50+ lingue, supporto prioritario
Aggiungi un toggle mensile/annuale con il 20% di sconto sull'annuale.
```

Il toggle compare subito, ma nel mockup è solo grafica. La logica arriva con React.

Il terzo round chiude i colori. Claude riassume la palette che è uscita dai giri precedenti: fondo `#0a0a0f`, gradiente da `#7c3aed` (viola) a `#06b6d4` (ciano), testo bianco, testo secondario bianco al 65% di opacità. La confermi e Claude la registra come design token per la spec:

```text
La palette va bene. Confermala e salva i design token.
```

A questo punto hai un mockup navigabile con sezioni, palette e gerarchia decise. Claude non ha creato `package.json`, non ha lanciato `npm install`, non ha scritto un file `.jsx`. Ha lavorato in una cartella di servizio separata dal codice, quindi buttare via una bozza non costa niente.

::: {.callout .callout-tip}
[Suggerimento]{.callout-title}

Nel repo companion la cartella `.superpowers/` è committata apposta, per farti vedere i mockup. Nei tuoi progetti puoi aggiungerla al `.gitignore`: quello che conta del design finisce comunque nella spec.
:::

## 16.2 Dal mockup al piano a task atomici

### Chiudere la fase di design

Quando il mockup ti convince, chiudi la fase con un messaggio esplicito:

```text
Il mockup è approvato. Ora costruiamo il progetto vero
in React + Vite + Tailwind CSS (versione più recente).
Genera prima le specifiche complete, poi il piano di
implementazione con task atomici.
```

Da qui in poi Claude pianifica lavoro concreto: struttura del progetto, componenti, dipendenze, deploy. Tutto quello che vuoi nella pagina deve essere detto adesso.

### La spec

Superpowers chiude il brainstorming scrivendo una spec. Nel repo è `docs/superpowers/specs/2026-03-25-fluentaipro-landing-page-design.md`, nel branch `book/cap-10-2-spec`. Senza Superpowers la chiedi tu:

```text
Prima di scrivere codice, crea una cartella docs/ e
scrivi le specifiche complete del progetto: stack,
struttura, componenti, design tokens, accessibilità.
```

La spec reale contiene lo stack (React 19 con Vite, Tailwind CSS v4 tramite il plugin `@tailwindcss/vite`, nessun routing, Firebase Hosting, animazioni solo CSS), i design token della palette, la scala tipografica con il font Inter, l'ordine delle nove sezioni e, per ognuna, testi, layout e comportamento responsive. Chiudono la spec una sezione sull'accessibilità (contrasti calcolati, `aria-expanded` sulla FAQ, `prefers-reduced-motion`) e una checklist di verifica finale. È in inglese, come i testi della landing: il prodotto parla a un pubblico internazionale.

Due dettagli mostrano quanto una spec scritta bene risparmi lavoro dopo. La navbar diventa "di vetro" quando un `<div id="nav-sentinel">` posto subito sotto esce dal viewport, osservato con `IntersectionObserver`. I prezzi annuali sono scritti per esteso (10,39 € Silver, 19,99 € Gold) invece di lasciare il calcolo al componente. Sono decisioni che, senza spec, Claude prenderebbe da solo in mezzo all'esecuzione.

::: {.callout .callout-warning}
[Attenzione]{.callout-title}

Leggi la spec prima di approvarla. È l'ultimo momento in cui aggiungere un requisito, togliere una sezione o cambiare un testo costa una riga di Markdown. Dopo, ogni cambio è un task di fix su codice già scritto.
:::

### Il piano

Approvata la spec, Superpowers passa alla skill `writing-plans` e genera il piano di implementazione: una lista numerata di task, ognuno con i file che tocca, i task da cui dipende e un criterio di completamento verificabile. Nella mia sessione i task erano dieci. I titoli li vedi nella figura; file e criteri qui sotto li ho ricostruiti dalla spec, perché il file del piano non è nel repo.

```text
Task 1: Project Scaffolding
  File: package.json, vite.config.js, vitest.config.js, index.html,
        src/main.jsx, src/App.jsx, src/index.css, tests/setup.js
  Dipende da: nessuno
  Done: npm run dev parte senza errori, npx vitest run è verde

Task 2: Shared UI Components
  File: src/components/ui/Badge.jsx, Button.jsx, GlassCard.jsx,
        GradientText.jsx, tests/ui/Button.test.jsx, GlassCard.test.jsx
  Dipende da: Task 1
  Done: i componenti si renderizzano con le props principali, test verdi

Task 3: Navbar
  File: src/components/sections/Navbar.jsx, tests/sections/Navbar.test.jsx
  Dipende da: Task 2
  Done: navbar sticky, effetto vetro dopo lo scroll tramite il sentinel

Task 4: Hero Section
  File: src/components/sections/Hero.jsx, tests/sections/Hero.test.jsx
  Dipende da: Task 2
  Done: titolo, sottotitolo, due CTA, barra statistiche; h1 a 40px su mobile

Task 5: Features Section
  File: src/components/sections/Features.jsx
  Dipende da: Task 2
  Done: card larga con mockup della chat più 4 card; una colonna sotto 768px

Task 6: Demo, Languages, Testimonials
  File: src/components/sections/Demo.jsx, Languages.jsx, Testimonials.jsx
  Dipende da: Task 2
  Done: mockup animato (fermo con prefers-reduced-motion), 18 lingue
        più il chip "+32 more", 3 testimonial

Task 7: Pricing Section
  File: src/components/sections/Pricing.jsx, tests/sections/Pricing.test.jsx
  Dipende da: Task 2
  Done: toggle mensile/annuale, annuale a 10.39 (Silver) e 19.99 (Gold)

Task 8: FAQ Section
  File: src/components/sections/FAQ.jsx, tests/sections/FAQ.test.jsx
  Dipende da: Task 2
  Done: accordion con aria-expanded, animazione su maxHeight

Task 9: Footer + Full Assembly
  File: src/components/sections/Footer.jsx, src/App.jsx, tests/App.test.jsx
  Dipende da: Task 3-8
  Done: 9 sezioni nell'ordine della spec, layout corretto a 375, 768, 1280 px

Task 10: Firebase Deployment
  File: firebase.json, .firebaserc
  Dipende da: Task 9
  Done: npm run build pulito, firebase deploy --only hosting riuscito
```

![Il piano a dieci task nel terminale di VS Code, accanto al package.json appena generato](figures/cap-16/fig-01.png)

### Perché task così piccoli

Un task atomico porta il progetto da uno stato coerente al successivo con il minimo lavoro possibile. "Crea la sezione Hero" è atomico, "crea la landing" no.

Il vantaggio si vede in tre punti dell'esecuzione. Se ogni task è un commit, `git log` diventa il diario del progetto e un bug si ritrova in un commit preciso. Se il Task 7 rompe il pricing, fai `git revert` di quel commit senza perdere la Hero e le Features. E una review su un componente da 60 righe si fa con attenzione, una su 1.200 righe nuove no.

Se non usi Superpowers, chiedi di salvare il piano in un file e committalo per primo:

```text
Salva il piano in docs/PLAN.md e committalo come primo
commit del progetto.
```

Con il piano su disco puoi fare `/clear` quando vuoi: Claude rilegge il file e sa dove eravate arrivati.

## 16.3 Esecuzione, un task alla volta

### Subagent driven

Quando dici "esegui il piano" hai due strade. La prima è l'esecuzione in linea: Claude lavora nel contesto principale e tu vedi tutto nella conversazione, ma la context window si riempie in fretta. La seconda è la modalità subagent driven di Superpowers (skill `subagent-driven-development`): per ogni task parte un subagent con un contesto pulito, che legge il task, scrive i file, lancia i comandi e restituisce solo l'esito. File letti, output di build e log dei test restano nel contesto del subagent.

Per questa landing scegli la seconda:

```text
Ora esegui il piano in modalità subagent driven.
Un sotto-agente per ogni task. Aspetta la mia conferma
dopo ogni task prima di passare al successivo.
```

La richiesta di conferma va scritta: senza, la skill esegue tutto il piano di fila e si ferma solo davanti a un blocco. Ti lascia il controllo del ritmo: guardi il diff, apri il browser, poi dai il via al task successivo. Qui i task vanno in fila uno dopo l'altro. Nel capitolo 20 vedrai come far girare in parallelo i task indipendenti, ognuno nel suo worktree, quando il progetto è grande abbastanza da giustificarlo.

### Task 1, scaffolding

Il subagent del Task 1 crea il progetto Vite e aggiunge Tailwind e Vitest:

```bash
npx create-vite@latest . --template react
npm install
npm install -D tailwindcss @tailwindcss/vite
npm install -D vitest jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event
```

Tailwind v4 non ha più `tailwind.config.js`: si attiva con il plugin di Vite e una riga di CSS. Il `vite.config.js` del repo è questo:

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
})
```

In `src/index.css` la prima riga è `@import "tailwindcss";`, seguita dai design token della spec, dichiarati sia in `:root` sia in `@theme`. Alla fine il subagent riporta file creati, esito di `npm run dev` e commit. Apri `http://localhost:5173`, controlla che la pagina di Vite si veda e rispondi:

```text
Task 1 ok. Procedi con Task 2.
```

### Task 2, componenti condivisi

Il Task 2 crea in `src/components/ui/` i quattro mattoni riusati da tutte le sezioni: `Badge` (l'etichetta a pillola), `Button` (varianti `primary` e `secondary`, link o bottone a seconda che riceva `href`), `GlassCard` (il contenitore in vetro) e `GradientText` (il testo con il gradiente viola-ciano). Sono componenti minuscoli. `GlassCard` intero sta in sette righe:

```jsx
export default function GlassCard({ children, className = '', ...props }) {
  return (
    <div className={`glass-card ${className}`} {...props}>
      {children}
    </div>
  )
}
```

Lo stile vive in classi BEM dentro `index.css` (`.glass-card`, `.btn-primary`), e il `CLAUDE.md` che Claude ha scritto per il repo lo dice in chiaro: niente utility Tailwind inline per gli stili strutturali o di brand.

Insieme ai componenti arrivano i primi test con Vitest e React Testing Library, in `tests/` con la stessa struttura di `src/`. Niente TDD in senso stretto, solo una rete minima che ti avvisa prima del deploy se un refactoring rompe il `Button`.

![Il test App renders without crashing e la lista dei task mentre l'esecuzione procede](figures/cap-16/fig-02.png)

### Task 4, la Hero

La Hero è il task che si vede di più. Tieni aperto il browser mentre gira: con l'HMR di Vite la pagina si aggiorna a ogni file salvato. Questo è il componente nel branch `book/cap-10-3-execution`:

```jsx
import React from 'react'
import Badge from '../ui/Badge'
import GradientText from '../ui/GradientText'
import Button from '../ui/Button'
import { APP_URL } from '../../constants.js'

const STATS = [
  { number: '50+', label: 'Languages' },
  { number: '10M+', label: 'Conversations' },
  { number: '98%', label: 'Accuracy Rate' },
  { number: '4.9★', label: 'User Rating' },
]

export default function Hero() {
  return (
    <section id="hero" className="hero">
      <div className="hero__glow hero__glow--violet" aria-hidden="true" />
      <div className="hero__glow hero__glow--cyan" aria-hidden="true" />

      <Badge>AI-Powered Language Learning</Badge>

      <h1 className="hero__title">
        Learn any language<br />
        with your <GradientText>AI tutor</GradientText>
      </h1>

      <p className="hero__subtitle">
        Practice real conversations in 50+ languages. Get instant pronunciation
        feedback and a learning path that adapts to you.
      </p>

      <div className="hero__actions">
        <Button href={APP_URL} variant="primary">Start for free →</Button>
        <Button href="#features" variant="secondary">▶ See how it works</Button>
      </div>

      <div className="hero__stats" role="list">
        {STATS.map(({ number, label }, i) => (
          <React.Fragment key={label}>
            {i > 0 && <div className="hero__stats-divider" aria-hidden="true" />}
            <div className="hero__stat" role="listitem">
              <span className="hero__stat-number gradient-text">{number}</span>
              <span className="hero__stat-label">{label}</span>
            </div>
          </React.Fragment>
        ))}
      </div>
    </section>
  )
}
```

Titolo, sottotitolo e statistiche sono quelli della spec, parola per parola. Gli aloni colorati sono due `div` decorativi con `aria-hidden`, e l'URL della CTA viene da `src/constants.js`, così si cambia in un posto solo. I numeri delle statistiche sono segnaposto di marketing da sostituire con dati veri prima del lancio.

### Non eseguire tutto il piano in un colpo

L'errore più comune con un piano approvato è scrivere "esegui tutto senza chiedermi conferma". Ti ritrovi con decine di file nuovi in un'unica ondata. Se il toggle del pricing è rotto devi capire quale dei trenta file è il colpevole, la review diventa una lettura in diagonale e la history Git è un blocco unico.

Un task alla volta sembra più lento. In pratica è più veloce, perché ogni errore lo vedi quando è appena nato. Per ogni task bastano un'occhiata al diff e un controllo nel browser.

### Task 7, il pricing con il toggle

Il pricing è la sezione con più logica. Nel mockup il toggle cambiava solo l'aspetto; qui diventa stato React. Questo è un estratto di `Pricing.jsx` (Silver e Gold hanno la stessa forma del piano Free):

```jsx
import { useState } from 'react'
import GlassCard from '../ui/GlassCard'
import { APP_URL } from '../../constants.js'

const PLANS = [
  {
    icon: '🌱', name: 'Free',
    monthly: '0', yearly: '0', yearlyTotal: null,
    desc: 'Try it out, no strings attached',
    features: [
      { label: '1 language', included: true },
      { label: '10 AI conversations / month', included: true },
      { label: 'Basic pronunciation feedback', included: true },
      { label: 'Adaptive learning path', included: false },
      { label: 'Progress analytics', included: false },
      { label: 'Priority support', included: false },
    ],
    cta: 'Get started free', ctaVariant: 'outline',
  },
  // Silver: monthly '12.99', yearly '10.39', yearlyTotal '124.70', featured: true
  // Gold:   monthly '24.99', yearly '19.99', yearlyTotal '239.88'
]

export default function Pricing() {
  const [cycle, setCycle] = useState('monthly')
  const isYearly = cycle === 'yearly'

  return (
    <section id="pricing" className="section section--centered">
      {/* ... titolo e sottotitolo ... */}
      <div className="pricing__toggle-row">
        <button
          className={`pricing__toggle-label${!isYearly ? ' pricing__toggle-label--active' : ''}`}
          onClick={() => setCycle('monthly')}
        >
          Monthly
        </button>
        <button
          className="pricing__toggle-track"
          onClick={() => setCycle(isYearly ? 'monthly' : 'yearly')}
          role="switch"
          aria-checked={isYearly}
          aria-label={isYearly ? 'Switch to monthly billing' : 'Switch to yearly billing'}
        >
          <span className={`pricing__toggle-knob${isYearly ? ' pricing__toggle-knob--right' : ''}`} />
        </button>
        <button
          className={`pricing__toggle-label${isYearly ? ' pricing__toggle-label--active' : ''}`}
          onClick={() => setCycle('yearly')}
        >
          Yearly
        </button>
        {isYearly && <span className="pricing__save-badge">Save 20%</span>}
      </div>
      {/* ... le tre GlassCard: price = isYearly ? yearly : monthly ... */}
    </section>
  )
}
```

Clicchi e i prezzi cambiano. Lo stato è una stringa, `'monthly'` o `'yearly'`, come chiedeva la spec, e il toggle ha `role="switch"` con `aria-checked`, così uno screen reader lo annuncia per quello che è. I prezzi annuali sono scritti nei dati e non calcolati, quindi il test può controllarli direttamente:

```jsx
test('shows yearly prices after toggling to yearly', async () => {
  const user = userEvent.setup()
  render(<Pricing />)
  await user.click(screen.getByRole('button', { name: /yearly/i }))
  expect(screen.getByText('10.39')).toBeInTheDocument()
  expect(screen.getByText('19.99')).toBeInTheDocument()
})
```

### La code review

In modalità subagent driven la review non aspetta la fine. Nella mia sessione, a marzo 2026, dopo ogni task Superpowers faceva due controlli: uno verificava che il codice rispettasse la spec, l'altro (il subagent `superpowers:code-reviewer`) guardava la qualità. Nella figura il Task 2 è in review mentre il Task 3 sta partendo. Dalla versione 6 del plugin i due controlli sono diventati un solo reviewer per task, più una review di tutto il branch alla fine.

![Il subagent code-reviewer di Superpowers rivede il Task 2 mentre parte il Task 3](figures/cap-16/fig-03.png)

Quando tutte le sezioni sono pronte, prima del deploy, fai comunque una review d'insieme. Certi problemi si vedono solo guardando le sezioni una accanto all'altra:

```text
Ora esegui una code review sui componenti in src/components/sections/.
Controlla:
- colori hardcoded che dovrebbero passare dai design token
- CSS duplicato tra sezioni
- accessibilità (aria-label, contrasti, focus states)
- naming convention consistente
- file che non dovrebbero essere in Git (dist/, .env.local)
```

Su un progetto così le segnalazioni tipiche sono un colore come `#7c3aed` scritto a mano in un componente invece di `var(--color-grad-from)`, lo stesso padding ripetuto in sette sezioni, `dist/` assente dal `.gitignore`, un bottone senza nome accessibile. Nel codice finale del repo vedi il risultato delle correzioni: la classe condivisa `.section` in `index.css`, `dist/` nel `.gitignore`, `aria-label` sul toggle. Chiedi a Claude di sistemare le segnalazioni e committa a parte, con un messaggio come `fix: code review, design token, gitignore, accessibilità`.

Oggi Claude Code ha anche un comando integrato, `/code-review`, che rivede le modifiche non pushate cercando bug di correttezza: lo trovi nel capitolo 22. La checklist qui sopra resta utile per token, duplicazioni e accessibilità, e il capitolo 19 riprende la review su un progetto più grande.

## 16.4 Replicare un design esistente, il caso Lovable

### Quando il design c'è già

Finora sei partito da zero. Capita spesso il contrario: il design c'è già. Può essere una landing fatta su Lovable, un mockup Figma o il sito di un concorrente che ti piace, e lo vuoi rifare nel tuo stack.

Lovable (`lovable.dev`) genera interfacce React da una descrizione, dentro un editor visuale. Il risultato è curato, ma il codice vive sulla piattaforma ed è scomodo da portare in un flusso di sviluppo normale. La landing di FluentAiPro era stata costruita prima anche su Lovable, e il confronto con la versione fatta in Claude Code è istruttivo.

### Replicare da uno screenshot

Claude Code legge le immagini, quindi puoi mostrargli una schermata e chiedergli di rifarla.

Primo passo: cattura la pagina. Se è lunga, fai uno screenshot per ogni sezione principale e salvali nel progetto:

```bash
mkdir -p docs/design-reference
# copia qui gli screenshot
```

Secondo passo: passa l'immagine a Claude. Puoi incollarla nel prompt con `Ctrl+V` (anche su macOS, non `Cmd+V`), trascinarla nel terminale o citarla con `@`:

```text
Guarda @docs/design-reference/lovable-landing.png

Replica questa landing page in React + Vite + Tailwind CSS.
Specifiche di stile:
- Dark mode, sfondo quasi nero
- Accent color viola (#7c3aed)
- Tipografia bold-condensed per i titoli
- Effetti glassmorphism sulle card
- Animazioni sottili (fade-in on scroll)
```

Terzo passo: Claude analizza l'immagine. Ricava layout, palette, tipografia e numero di blocchi, poi genera i componenti. Testi, prezzi e nomi delle sezioni che non si leggono bene dallo screenshot diventano segnaposto da aggiornare.

### Quattro round di iterazione visiva

La prima replica raramente è perfetta. Da un'immagine statica non si ricavano spaziature esatte, stati hover, animazioni e breakpoint. Si itera con commenti precisi, un tema per round.

Proporzioni generali:

```text
La replica è buona come struttura, ma:
- Il padding verticale della hero è troppo stretto
- Le card delle features sono più alte nell'originale
- Il font del titolo principale dovrebbe essere più grassetto
```

Dettagli interattivi:

```text
Aggiungi:
- Hover state sulle card: leggero glow viola sul bordo
- Transizione smooth sul toggle del pricing (0.3s ease)
- Scroll behaviour smooth sui link anchor del menu
```

Animazioni:

```text
Aggiungi animazioni fade-in on scroll sulle sezioni
features, testimonials e pricing. Usa IntersectionObserver
o una libreria leggera come framer-motion.
Niente di eccessivo: solo opacity da 0 a 1 con translate-y
piccolo (20px), duration 0.5s.
```

Mobile:

```text
Rivedi la versione mobile (375px):
- La navbar deve collassare in hamburger menu
- La griglia delle features deve essere 1 colonna su mobile
- I prezzi devono essere leggibili senza scroll orizzontale
```

Dopo quattro giri hai una replica fedele in React e Tailwind standard, nel tuo repo, che puoi mantenere con qualunque strumento.

### Replicare o partire da zero

La replica conviene quando il design è già validato: l'hai provato con degli utenti sul prototipo Lovable, il cliente l'ha approvato, oppure è lo schema classico delle landing SaaS e reinventarlo non serve. Parti da zero con il visual companion quando non hai un riferimento, quando il brand ha un'identità da costruire o quando il cliente non ha ancora visto niente e hai margine per proporre.

Per molte landing commerciali la replica fa risparmiare tempo: struttura, gerarchia e CTA funzionano già, e tu personalizzi i dettagli. I due strumenti convivono bene: Lovable per mostrare un'idea al cliente in pochi minuti, Claude Code per portarla in produzione con codice versionato e testato.

## 16.5 Commit, deploy su Firebase e URL live

### La history prima del deploy

Se hai seguito un task alla volta, hai già una serie di commit. Controlla prima del deploy:

```bash
git log --oneline
```

Dovresti vedere qualcosa del genere, un commit per task più quello della review:

```text
a7b3c2d fix: code review, design token, gitignore, accessibilità
f1e9d8c feat: Footer e assemblaggio delle 9 sezioni
2d4e5f6 feat: FAQ accordion con aria-expanded
3f2e1d0 feat: Pricing con toggle mensile/annuale
9c8b7a0 feat: Demo, Languages, Testimonials
8a7b6c5 feat: Features con card larga e mockup chat
4d3c2b1 feat: Hero con statistiche e glow
7e6f5d4 feat: Navbar sticky con effetto vetro
b9a8c7d feat: componenti UI Badge, Button, GlassCard, GradientText
1f0e9d8 feat: scaffolding Vite + React + Tailwind + Vitest
0c1b2a3 docs: spec e piano di implementazione
```

Ogni riga si può leggere, rivedere e revertire da sola. I branch del repo companion sono fotografie con un solo commit ciascuno, quindi questa history non la trovi lì: la costruisci tu.

### Il progetto Firebase

Se non hai ancora un progetto Firebase:

1. Vai su `console.firebase.google.com` e crea un nuovo progetto.
2. Dagli un nome, per esempio `fluent-ai-pro-landing`. Firebase ne ricava l'ID del progetto, che puoi modificare adesso: dopo la creazione non si cambia più.
3. Salta i passi facoltativi, l'assistenza AI e Google Analytics: per una landing statica non servono.
4. Conferma con Create project.

Annota l'ID del progetto. Spesso coincide con il nome, a volte ha un suffisso. Ti serve nella CLI.

### La Firebase CLI

Puoi installarla globalmente:

```bash
npm install -g firebase-tools
firebase login
```

oppure usarla al volo con `npx firebase-tools`, come ha fatto Claude nella mia sessione. Se scegli `npx`, metti `npx firebase-tools` al posto di `firebase` in tutti i comandi di questa sezione. `firebase login` apre il browser per l'autenticazione Google. Poi verifica:

```bash
firebase projects:list
```

Il progetto appena creato deve comparire nella lista.

### firebase init hosting

Dalla cartella del progetto:

```bash
firebase init hosting
```

La CLI fa qualche domanda:

- Progetto: usa quello esistente e selezionalo dalla lista.
- Public directory: `dist`, la cartella che produce `npm run build`.
- Single-page app: sì. Tutte le URL vengono riscritte su `index.html`, e ti servirà se un giorno aggiungi React Router.
- Build e deploy automatici con GitHub: no, per ora.
- Se esiste già `dist/index.html` e la CLI chiede di sovrascriverlo, rispondi no.

Il risultato è il `firebase.json` del branch `book/cap-10-5-deploy-ready`:

```json
{
  "hosting": {
    "public": "dist",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [{ "source": "**", "destination": "/index.html" }]
  }
}
```

E un `.firebaserc` che lega la cartella al progetto. Nel repo l'ID è `fluentapipro`, tu vedrai il tuo:

```json
{
  "projects": {
    "default": "fluentapipro"
  }
}
```

![Claude scrive firebase.json e .firebaserc durante il task di deploy](figures/cap-16/fig-04.png)

Committa la configurazione:

```bash
git add firebase.json .firebaserc
git commit -m "chore: Firebase Hosting configuration"
```

Nello stesso branch trovi anche `.github/workflows/deploy.yml` e `docs/ci-cd-vercel.md`: una pipeline GitHub Actions che lancia i test e pubblica su Vercel, con un deploy di anteprima per ogni PR. È un'alternativa a Firebase, e la puoi ignorare per seguire il capitolo.

### Preview channel, prima di andare live

Firebase Hosting ha i preview channel: URL temporanei, validi 7 giorni di default, per far vedere una versione a un cliente o a un collega senza toccare il sito di produzione.

```bash
npm run build
firebase hosting:channel:deploy preview-v1
```

L'output finisce con l'URL del canale e la data di scadenza:

```text
✔  hosting:channel:deploy complete!

Channel URL (fluent-ai-pro-landing):
https://fluent-ai-pro-landing--preview-v1-xyz123.web.app

[expires 2026-05-23 14:32:10]
```

Apri l'URL e verifica tutto: naviga con i link del menu, prova il toggle del pricing e controlla i prezzi annuali, apri e chiudi le FAQ, stringi la finestra a 375px, controlla che le CTA puntino all'URL giusto. Se serve una modifica, rifai il deploy sul canale: il sito di produzione non lo tocchi.

### Il deploy in produzione

Quando l'anteprima è approvata:

```bash
npm run build
firebase deploy --only hosting
```

Firebase legge `firebase.json`, carica il contenuto di `dist/` sulla sua CDN e pubblica la nuova versione:

```text
=== Deploying to 'fluent-ai-pro-landing-a1b2c'...

i  deploying hosting
i  hosting[fluent-ai-pro-landing]: beginning deploy...
i  hosting[fluent-ai-pro-landing]: found 18 files in dist
✔  hosting[fluent-ai-pro-landing]: file upload complete
i  hosting[fluent-ai-pro-landing]: finalizing version...
✔  hosting[fluent-ai-pro-landing]: version finalized
i  hosting[fluent-ai-pro-landing]: releasing new version...
✔  hosting[fluent-ai-pro-landing]: release complete

✔  Deploy complete!

Project Console: https://console.firebase.google.com/project/...
Hosting URL: https://fluent-ai-pro-landing-a1b2c.web.app
```

La landing è online, con HTTPS e CDN, senza aver configurato un server e senza pagare un hosting: il piano gratuito di Firebase basta per una pagina statica.

### Dopo il deploy

Per un dominio personalizzato vai nella console, sezione Hosting, e aggiungi il dominio. Firebase ti dà i record DNS da inserire presso il registrar ed emette da solo il certificato HTTPS. La propagazione DNS può richiedere da qualche ora fino a un giorno; nel frattempo il sito resta raggiungibile su `.web.app`.

Firebase conserva la cronologia dei rilasci. Se un deploy introduce un problema, dalla console di Hosting riporti online una versione precedente con un clic. Se invece l'anteprima approvata è esattamente quello che vuoi in produzione, puoi copiarla sul canale live senza rifare la build:

```bash
firebase hosting:clone fluent-ai-pro-landing:preview-v1 fluent-ai-pro-landing:live
```

Se un giorno porti la landing su Next.js, attiva l'export statico in `next.config.js`:

```javascript
const nextConfig = {
  output: 'export',
  trailingSlash: true,
};
```

`next build` produce HTML statico nella cartella `out/` invece di `dist/`, senza bisogno di un server Node.js. Ricordati di cambiare `public` in `firebase.json`.

Ultimo caso, molto comune. Provando l'anteprima potresti notare che la voce di menu attiva non segue lo scroll. Si risolve con uno scrollspy:

```text
Aggiungi scrollspy alla Navbar: usa IntersectionObserver
per rilevare quale sezione è visibile e applicare la
classe active al link corrispondente nel menu.
```

Nel `Navbar.jsx` del repo lo trovi nel secondo `useEffect`: un `IntersectionObserver` con soglia 0.3 tiene traccia della sezione visibile più in alto. Claude lo implementa, tu committi e rifai il deploy:

```bash
npm run build
firebase deploy --only hosting
```

Con il ciclo di deploy già configurato, una modifica di questo tipo è online in un paio di minuti.

## 16.6 Cosa hai fatto e cosa resta fuori

In questo capitolo hai messo in fila quasi tutto quello che hai visto nelle parti I-IV: Superpowers con il brainstorming e il visual companion, Plan Mode, una spec scritta prima del codice, un piano a task atomici, i subagent, la review dopo ogni task, un commit per task e il deploy con anteprima.

Per essere onesti, una landing lascia fuori molto di quello che serve in un prodotto vero:

- nessun backend e nessuna API: la pagina non chiama endpoint e non salva dati;
- nessun database;
- nessuna autenticazione: "Start for free" porta a un'app esterna, la registrazione avviene lì;
- nessun form serio: un modulo di contatto con validazione, CAPTCHA e invio email non c'è;
- nessuno stato condiviso tra pagine, perché la pagina è una sola;
- niente analytics né A/B test, che su una landing reale servono per misurare le conversioni;
- una sola lingua, l'inglese.

È voluto: un progetto piccolo ti fa imparare il ritmo del workflow senza distrazioni infrastrutturali, e se qualcosa va storto non succede niente.

| Progetto | Stack | Dimensione |
|---|---|---|
| Landing (capitolo 16) | React 19, Vite 6, Tailwind CSS v4, Firebase Hosting | 1 pagina, 10 task |
| Photogallery (capitoli 17-23) | Laravel 13, Filament v5, React 19, Vite 6, Tailwind CSS v4, AWS | API REST e admin, 124 task in 14 fasi |

La Parte VI costruisce la Photogallery: una API REST in Laravel 13 sotto `/api/v1`, un pannello admin in Filament v5, un frontend React con login tramite token Sanctum, job in coda per il resize delle foto e l'estrazione dei dati EXIF, e il deploy su AWS con CloudFormation. Il metodo è lo stesso di questo capitolo (spec, task atomici, review, commit), con requisiti, design e task in tre documenti separati, l'esecuzione a wave e la review fatta anche con altri modelli. Cambia la scala: qui avevi 10 task, là ne avrai 124.

::: {.callout .callout-prompt}
[Prompt riusabile]{.callout-title}

Per la tua prossima landing, adatta questo template:

```text
Voglio costruire una landing page per [NOME PRODOTTO].

Descrizione del prodotto:
[2-3 frasi che descrivono il prodotto e il suo valore principale]

Audience:
[chi sono gli utenti target]

Call to action principale:
[es. "Inizia gratis", "Prenota una demo", "Scarica l'app"]

Sezioni da includere:
- Hero con titolo, sottotitolo, CTA e immagine/video
- Features (4-6 feature principali con icone)
- [sezione opzionale, es. "How it works" con 3 passi]
- Social proof (testimonial o loghi clienti)
- Pricing (N piani, con toggle mensile/annuale se presente)
- FAQ (6-8 domande più frequenti)
- Footer con CTA finale

Stile:
[es. "dark mode, accent viola, tipografia bold, tech forward"
 oppure "light, colori caldi, friendly, startup consumer"]

Stack:
React + Vite + Tailwind CSS (ultima versione)

Deploy target:
Firebase Hosting

Workflow:
1. Usa visual companion per mostrarmi 3 varianti di layout
2. Dopo l'approvazione del layout, genera le specifiche in docs/SPEC.md
3. Crea il piano in docs/PLAN.md con task atomici e criteri di done
4. Esegui un task alla volta, aspetta la mia conferma
5. Code review dopo tutti i componenti, prima del deploy
6. Build + firebase deploy --only hosting

Inizia dal Plan Mode. Non scrivere codice fino all'approvazione delle spec.
```

Con le conferme manuali conta 60-90 minuti di sessione, un po' meno in modalità subagent driven.
:::

## Riepilogo

- Prima di scrivere React, decidi il design con il visual companion: le bozze HTML in `.superpowers/brainstorm/` costano poco e si buttano senza rimpianti.
- Rileggi la spec prima di approvarla. Testi, prezzi e comportamenti decisi lì non diventano task di fix dopo.
- Esegui il piano un task alla volta, con conferma, diff e controllo nel browser. Un commit per task rende ogni errore facile da trovare e da revertire.
- Fai una review d'insieme su tutte le sezioni prima del deploy, anche se Superpowers ha già rivisto ogni task.
- Per pubblicare bastano `firebase init hosting` con `dist` come public directory, poi `npm run build` e `firebase deploy --only hosting`. Passa da un preview channel quando qualcuno deve approvare.
- Se il design esiste già, replicalo da uno screenshot e itera un tema alla volta.

## Esercizio

Costruisci la tua landing, non quella di FluentAiPro: un side project, il tuo portfolio, un progetto open source che merita una pagina migliore.

1. Crea una cartella nuova, fai `git init` e avvia Claude Code in Plan Mode.
2. Con il visual companion fatti proporre tre direzioni visive, scegline una e itera sulle sezioni.
3. Fai generare spec e piano a task atomici, e leggili prima di approvarli.
4. Esegui un task alla volta e committa dopo ognuno.
5. Fai una review d'insieme prima del deploy e committa le correzioni a parte.
6. Pubblica su un preview channel, poi in produzione.

Inizia piccolo, con hero, features e footer, e aggiungi sezioni dopo. È più facile far crescere una struttura minima che tagliare una struttura troppo ambiziosa. Per confrontare il tuo lavoro con il mio, il punto di arrivo è il branch `book/cap-10-5-deploy-ready`.

L'esercizio è finito quando il tuo URL `.web.app` risponde in HTTPS, `npx vitest run` è verde e `git log --oneline` mostra un commit per ogni task del piano.
