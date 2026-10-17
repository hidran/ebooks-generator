# KDP listing, second edition (October 2026)

Paste-ready Amazon KDP metadata for the three second editions. The description blocks use
the HTML subset KDP supports (`<b>`, `<i>`, `<h5>`, `<ul>`, `<li>`); paste them into the
description field as they are. The back-cover blocks are plain text for Cover Creator.
Every description stays under the 4,000-character limit and every keyword under 50
characters. The first-edition listing is in Git history (commit `0d1015e`).

## Publishing checklist (same for IT, EN, ES)

1. **Create a new title**, don't edit the old one: Bookshelf > "+ Create" > Kindle eBook
   (then Paperback). Use exactly the same title, author and series data, so Amazon can relate
   the two editions; if it doesn't link them on the product page after publication, ask KDP
   support to link the editions.
2. **Edition number: 2.** Title and subtitle as below (unchanged, they match the interior).
   Author: Hidran Arias.
3. **Paperback:** new ISBN (the free KDP ISBN is fine), trim 6 x 9 in, interior
   `build/claude-code-guida[-en|-es].pdf`, black and white interior, white paper.
   New cover: the spine width comes from the page count (IT 640, EN 641, ES 671 pages);
   KDP's cover calculator gives the exact width.
4. **eBook:** upload `build/claude-code-guida[-en|-es].epub`. Preview it in the online
   previewer, check the table of contents and a code-heavy chapter (12 or 18).
5. **After the second edition is live:** unpublish the first edition (Bookshelf > "..." >
   Unpublish). Buyers keep it in their library; it just stops being sold.
6. **Launch:** tell first-edition readers (course students, the snippets repo README, your
   channels) and, if the eBook is in KDP Select, plan 2-3 free or Countdown Deal days in
   the first week so they can get the new edition at no or low cost.
7. **"Look inside"** is generated from the new files. **A+ content**, if you used it on the
   first edition, is attached to the old ASIN: recreate it for the new one.

Categories (KDP allows 3; the tree is in English on every marketplace and Amazon localizes
the browse node on Amazon.it and Amazon.es). Same for all editions:

1. Computers > Artificial Intelligence > General
2. Computers > Software Development & Engineering > Tools
3. Computers > Programming > General

"Claude" and "Claude Code" are Anthropic trademarks: every description ends with a
one-line independence disclaimer.

Optional subtitle, if you want the new topics on the cover too (then update `book.yaml` and
the copyright page in all three editions before building):
IT "Dall'installazione al deploy su AWS: agenti, skill, hook, MCP e Spec Driven Development
su progetti reali"; EN "From installation to AWS deployment: agents, skills, hooks, MCP, and
Spec Driven Development on real projects"; ES "De la instalación al deploy en AWS: agentes,
skills, hooks, MCP y Spec Driven Development en proyectos reales".

---

## Italian edition: `claude-code-guida.epub` / `.docx` / `.pdf`

**Title:** Claude Code: la guida pratica
**Subtitle:** Dall'installazione al deploy AWS: skills, agents, Spec Driven Development e progetti reali
**Edition number:** 2

### Description (HTML)

```html
<b>Seconda edizione, aggiornata a ottobre 2026: Claude Opus 5.5, auto mode, hook, MCP, plugin e wave in parallelo.</b>

Hai già chiesto a un'AI di scrivere una funzione. Questo libro ti accompagna oltre: un progetto intero, scritto con Claude Code e portato in produzione, con un metodo che puoi ripetere sul prossimo.

Claude Code legge il tuo repository, pianifica, modifica file, lancia test e comandi. Il difficile è farlo lavorare bene su un progetto vero: dargli il contesto giusto, mettere paletti a quello che può fare, verificare il risultato prima del merge. Il libro mostra come, passo per passo, su codice reale che trovi su GitHub.

<h5>Cosa c'è di nuovo in questa edizione</h5>
<ul>
<li>Sette capitoli nuovi: come lavora un agente (tool, loop agentico, sandbox), permessi e auto mode, hook, MCP, plugin e marketplace, contesto e memoria, wave in parallelo con git worktree, /goal e agent view</li>
<li>La code review integrata (/code-review, ultrareview, REVIEW.md) messa a confronto con la review di un secondo modello</li>
<li>Ogni capitolo riscritto e aggiornato a Claude Code 2.1: installer nativo, skill al posto dei vecchi custom command, subagent in background</li>
<li>Il progetto Photogallery allineato al codice del repository: Laravel 13, Filament v5, React 19</li>
</ul>

<h5>Cosa imparerai</h5>
<ul>
<li>Scrivere prompt che arrivano al risultato e usare Plan Mode prima di toccare il codice</li>
<li>Analizzare dati reali: da un CSV a report Excel con formule vere, grafici, una dashboard Flask e un PDF</li>
<li>Scrivere un CLAUDE.md che Claude segue davvero, e quando passare a command, skill e agent</li>
<li>Controllare l'agente con modalità di permesso, regole allow/ask/deny, sandbox e hook che scattano sempre</li>
<li>Collegare Claude a GitHub e ai database con MCP, e impacchettare tutto in un plugin per il team</li>
<li>Lavorare con lo Spec Driven Development: requisiti, design e 124 task atomici prima del codice</li>
<li>Fare QA, review e audit di sicurezza prima del deploy</li>
</ul>

<h5>Due progetti completi</h5>
Una <b>landing page</b> dal mockup al deploy su Firebase. Poi la <b>Photogallery</b>, un'applicazione full-stack con API Laravel, pannello admin Filament, frontend React, upload elaborati in coda e deploy su <b>AWS</b> con CloudFormation. Il codice è pubblico, con un branch per ogni tappa.

<h5>Pensato per essere usato</h5>
Ogni capitolo si chiude con un riepilogo e un esercizio. In fondo trovi un glossario, una guida al troubleshooting, una raccolta di prompt pronti, le risorse ufficiali e il changelog completo della nuova edizione.

<b>Per chi è:</b> per chi scrive codice almeno una volta a settimana, in qualunque linguaggio, e ha provato Copilot, ChatGPT o Cursor senza mai portare a termine un progetto intero con un agente.

<i>Libro indipendente, non affiliato ad Anthropic né approvato da Anthropic.</i>
```

### Back cover text (plain text for Cover Creator)

```text
SECONDA EDIZIONE, AGGIORNATA A OTTOBRE 2026

Hai già chiesto a un'AI di scrivere una funzione. Qui costruisci un progetto intero con Claude Code e lo porti in produzione, con un metodo che puoi ripetere.

COSA IMPARERAI
• Prompt che arrivano al risultato e Plan Mode prima del codice
• CLAUDE.md, command, skill e agent: quando usare cosa
• Permessi, auto mode, sandbox e hook per tenere l'agente sotto controllo
• MCP e plugin per collegare Claude ai tuoi strumenti e al team
• Spec Driven Development e wave in parallelo con git worktree
• Code review integrata, review con un secondo modello e audit di sicurezza

DUE PROGETTI COMPLETI
Una landing page dal mockup al deploy su Firebase. La Photogallery, un'applicazione Laravel e React con pannello admin, upload in coda e deploy su AWS con CloudFormation. Tutto il codice è su GitHub.

NOVITÀ DI QUESTA EDIZIONE
Sette capitoli nuovi, ogni capitolo riscritto e aggiornato a Claude Code 2.1 e Claude Opus 5.5.

Libro indipendente, non affiliato ad Anthropic.
```

### Keywords (7 slots, max 50 chars each)

| # | Keyword | Chars |
|---|---------|-------|
| 1 | agenti AI per sviluppatori | 26 |
| 2 | spec driven development | 23 |
| 3 | sviluppo software con intelligenza artificiale | 46 |
| 4 | hook MCP e plugin per assistenti di codice | 42 |
| 5 | code review con AI | 18 |
| 6 | deploy AWS CloudFormation Laravel React | 39 |
| 7 | automazione analisi dati Python Excel | 37 |

---

## English edition: `claude-code-guida-en.epub` / `.docx` / `.pdf`

**Title:** Claude Code: The Practical Guide
**Subtitle:** From installation to AWS deployment: skills, agents, Spec Driven Development, and real projects
**Edition number:** 2

### Description (HTML)

```html
<b>Second edition, updated for October 2026: Claude Opus 5.5, auto mode, hooks, MCP, plugins, and parallel waves.</b>

You've asked an AI to write a function. This book takes you further: a whole project, written with Claude Code and shipped to production, with a method you can repeat on the next one.

Claude Code reads your repository, plans, edits files, runs tests and commands. The hard part is getting it to work well on a real project: giving it the right context, putting limits on what it can do, and checking the result before you merge. The book shows how, step by step, on real code you can find on GitHub.

<h5>What's new in this edition</h5>
<ul>
<li>Seven new chapters: how an agent works (tools, the agentic loop, the sandbox), permissions and auto mode, hooks, MCP, plugins and marketplaces, context and memory, parallel waves with git worktrees, /goal, and agent view</li>
<li>Built-in code review (/code-review, ultrareview, REVIEW.md) compared with a review by a second model</li>
<li>Every chapter rewritten and updated for Claude Code 2.1: native installer, skills replacing the old custom commands, background subagents</li>
<li>The Photogallery project aligned with the code in its repository: Laravel 13, Filament v5, React 19</li>
</ul>

<h5>What you'll learn</h5>
<ul>
<li>Write prompts that get results, and use Plan Mode before touching the code</li>
<li>Analyze real data: from a CSV to Excel reports with real formulas, charts, a Flask dashboard, and a PDF</li>
<li>Write a CLAUDE.md that Claude actually follows, and know when to move to commands, skills, and agents</li>
<li>Keep the agent in check with permission modes, allow/ask/deny rules, the sandbox, and hooks that always fire</li>
<li>Connect Claude to GitHub and your databases with MCP, and package it all as a plugin for your team</li>
<li>Work with Spec Driven Development: requirements, design, and 124 atomic tasks before any code</li>
<li>Run QA, code review, and a security audit before you deploy</li>
</ul>

<h5>Two complete projects</h5>
A <b>landing page</b> from mockup to deployment on Firebase. Then the <b>Photogallery</b>, a full-stack application with a Laravel API, a Filament admin panel, a React front end, queued uploads, and a deployment to <b>AWS</b> with CloudFormation. The code is public, with a branch for each milestone.

<h5>Built to be used</h5>
Every chapter ends with a summary and an exercise. At the back you'll find a glossary, a troubleshooting guide, a collection of ready-made prompts, the official resources, and the full changelog of the new edition.

<b>Who it's for:</b> anyone who writes code at least once a week, in any language, and has tried Copilot, ChatGPT, or Cursor without ever finishing a whole project with an agent.

<i>Independent publication; not affiliated with or endorsed by Anthropic.</i>
```

### Back cover text (plain text for Cover Creator)

```text
SECOND EDITION, UPDATED FOR OCTOBER 2026

You've asked an AI to write a function. Here you build a whole project with Claude Code and ship it to production, with a method you can repeat.

WHAT YOU'LL LEARN
• Prompts that get results, and Plan Mode before the code
• CLAUDE.md, commands, skills, and agents: when to use which
• Permissions, auto mode, the sandbox, and hooks to keep the agent in check
• MCP and plugins to connect Claude to your tools and your team
• Spec Driven Development and parallel waves with git worktrees
• Built-in code review, a second-model review, and a security audit

TWO COMPLETE PROJECTS
A landing page from mockup to Firebase deployment. The Photogallery, a Laravel and React application with an admin panel, queued uploads, and an AWS deployment with CloudFormation. All the code is on GitHub.

NEW IN THIS EDITION
Seven new chapters, every chapter rewritten and updated for Claude Code 2.1 and Claude Opus 5.5.

Independent publication; not affiliated with Anthropic.
```

### Keywords (7 slots, max 50 chars each)

| # | Keyword | Chars |
|---|---------|-------|
| 1 | agentic coding for software developers | 38 |
| 2 | spec driven development | 23 |
| 3 | AI coding assistant | 19 |
| 4 | hooks MCP and plugins for AI coding agents | 42 |
| 5 | AI code review | 14 |
| 6 | AWS CloudFormation Laravel React deployment | 43 |
| 7 | automate data analysis Python Excel | 35 |

---

## Spanish edition: `claude-code-guida-es.epub` / `.docx` / `.pdf`

**Title:** Claude Code: la guía práctica
**Subtitle:** De la instalación al deploy en AWS: skills, agents, Spec Driven Development y proyectos reales
**Edition number:** 2

### Description (HTML)

```html
<b>Segunda edición, actualizada a octubre de 2026: Claude Opus 5.5, auto mode, hooks, MCP, plugins y oleadas en paralelo.</b>

Ya le has pedido a una IA que escriba una función. Este libro te lleva más lejos: un proyecto entero, escrito con Claude Code y llevado a producción, con un método que puedes repetir en el siguiente.

Claude Code lee tu repositorio, planifica, modifica archivos, ejecuta tests y comandos. Lo difícil es que trabaje bien en un proyecto real: darle el contexto adecuado, ponerle límites a lo que puede hacer y comprobar el resultado antes del merge. El libro enseña cómo, paso a paso, sobre código real que encuentras en GitHub.

<h5>Qué hay de nuevo en esta edición</h5>
<ul>
<li>Siete capítulos nuevos: cómo trabaja un agente (tools, bucle agéntico, sandbox), permisos y auto mode, hooks, MCP, plugins y marketplaces, contexto y memoria, oleadas en paralelo con git worktrees, /goal y agent view</li>
<li>La code review integrada (/code-review, ultrareview, REVIEW.md) comparada con la revisión de un segundo modelo</li>
<li>Todos los capítulos reescritos y actualizados a Claude Code 2.1: instalador nativo, skills en lugar de los antiguos comandos personalizados, subagentes en segundo plano</li>
<li>El proyecto Photogallery alineado con el código de su repositorio: Laravel 13, Filament v5, React 19</li>
</ul>

<h5>Qué aprenderás</h5>
<ul>
<li>Escribir prompts que llegan al resultado y usar Plan Mode antes de tocar el código</li>
<li>Analizar datos reales: de un CSV a informes de Excel con fórmulas de verdad, gráficos, un dashboard con Flask y un PDF</li>
<li>Escribir un CLAUDE.md que Claude sigue de verdad, y saber cuándo pasar a comandos, skills y agentes</li>
<li>Controlar al agente con modos de permisos, reglas allow/ask/deny, el sandbox y hooks que saltan siempre</li>
<li>Conectar Claude con GitHub y con tus bases de datos mediante MCP, y empaquetarlo todo en un plugin para el equipo</li>
<li>Trabajar con Spec Driven Development: requisitos, diseño y 124 tareas atómicas antes del código</li>
<li>Hacer QA, code review y una auditoría de seguridad antes del deploy</li>
</ul>

<h5>Dos proyectos completos</h5>
Una <b>landing page</b> desde el mockup hasta el deploy en Firebase. Después, la <b>Photogallery</b>, una aplicación full-stack con una API en Laravel, un panel de administración con Filament, un frontend en React, subidas procesadas en cola y un deploy en <b>AWS</b> con CloudFormation. El código es público, con una rama para cada etapa.

<h5>Pensado para usarse</h5>
Cada capítulo termina con un resumen y un ejercicio. Al final encontrarás un glosario, una guía de resolución de problemas, una colección de prompts listos, los recursos oficiales y el registro de cambios completo de la nueva edición.

<b>Para quién es:</b> para quien escribe código al menos una vez por semana, en cualquier lenguaje, y ha probado Copilot, ChatGPT o Cursor sin llegar a terminar nunca un proyecto entero con un agente.

<i>Publicación independiente, no afiliada a Anthropic ni avalada por Anthropic.</i>
```

### Back cover text (plain text for Cover Creator)

```text
SEGUNDA EDICIÓN, ACTUALIZADA A OCTUBRE DE 2026

Ya le has pedido a una IA que escriba una función. Aquí construyes un proyecto entero con Claude Code y lo llevas a producción, con un método que puedes repetir.

QUÉ APRENDERÁS
• Prompts que llegan al resultado y Plan Mode antes del código
• CLAUDE.md, comandos, skills y agentes: cuándo usar cada uno
• Permisos, auto mode, sandbox y hooks para tener al agente bajo control
• MCP y plugins para conectar Claude con tus herramientas y tu equipo
• Spec Driven Development y oleadas en paralelo con git worktrees
• Code review integrada, revisión con un segundo modelo y auditoría de seguridad

DOS PROYECTOS COMPLETOS
Una landing page desde el mockup hasta el deploy en Firebase. La Photogallery, una aplicación Laravel y React con panel de administración, subidas en cola y deploy en AWS con CloudFormation. Todo el código está en GitHub.

NOVEDADES DE ESTA EDICIÓN
Siete capítulos nuevos, todos los capítulos reescritos y actualizados a Claude Code 2.1 y Claude Opus 5.5.

Publicación independiente, no afiliada a Anthropic.
```

### Keywords (7 slots, max 50 chars each)

| # | Keyword | Chars |
|---|---------|-------|
| 1 | agentes de IA para desarrolladores | 34 |
| 2 | spec driven development | 23 |
| 3 | asistente de programación con IA | 32 |
| 4 | hooks MCP y plugins para agentes de código | 42 |
| 5 | code review con IA | 18 |
| 6 | despliegue en AWS con CloudFormation | 36 |
| 7 | automatizar análisis de datos Python Excel | 42 |
