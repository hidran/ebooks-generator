# Style guide: Claude Code, la guida pratica (second edition)

Readers called the first edition "AI slop". They were reacting to a voice, not to the
content: the workflow, the projects and the code are good. This guide is the rulebook
for the rewrite. It applies to every edition (IT, EN, ES). The linter
`tools/slop-lint.py` checks the mechanical rules; the rest is judgement.

The target voice is a senior engineer who has shipped the Photogallery, explaining it
to a colleague at the next desk. Concrete, a little dry, opinionated where they have
earned it, honest about what went wrong. Think of a good O'Reilly or Pragmatic
Bookshelf book, or of the author's own video narrations in
`claude-course-studio/courses/claude-code/lessons/*/narration.it.md`: short spoken
sentences, direct address, everyday phrasing, exact technical content.

## 1. Punctuation (hard rules, the linter enforces them)

- **No em dash (—) and no en dash (–) as punctuation.** Not in prose, not in headings,
  not in lists, not in captions. Use a comma, a colon, parentheses, a full stop, or
  rewrite the sentence. Number ranges use a hyphen: `capitoli 4-6`, `3-4 ore`.
  The only place a dash may survive is inside a code block or quoted program output.
- **No arrows (→, ⇒, ←) in prose.** Write "poi", "diventa", "fino a". Arrows are fine
  inside code blocks, diagrams and quoted UI text (e.g. the `←` key in agent view).
- **No emoji.** Not in callouts, not in lists, not in headings. Severity markers in
  quoted tool output (e.g. `🔴 Important`) may stay inside code blocks only.
- **Bold is rare.** At most one or two bold phrases per section, and only for a term
  being defined for the first time or a warning the reader must not miss. Never bold
  the lead word of every bullet. Never bold random words mid-sentence for emphasis.
- **Scare quotes are rare.** Do not wrap ordinary words in quotes to sound clever
  (“vero”, “utile”, “magia”). Quotes are for things someone actually says or types.
- **Semicolons sparingly.** Two sentences are usually better.
- **Ellipses (…) never** for dramatic effect.
- **Headings never contain a dash.** Chapter heading format:
  `# Capitolo 7. CLAUDE.md, la memoria del progetto` (IT),
  `# Chapter 7. CLAUDE.md, the project's memory` (EN),
  `# Capítulo 7. CLAUDE.md, la memoria del proyecto` (ES).
  Section headings keep their number: `## 7.2 Cosa scrivere dentro`.
  Keep titles short; avoid a colon in a chapter title when the "Capitolo N." prefix
  already precedes it, prefer a comma.

## 2. Sentence patterns to remove (the "AI tells")

Rewrite every instance. The linter flags the common Italian forms.

1. **"Non è X, è Y" / "Non X. Y."** contrast framing, and its cousins: "Non si tratta
   di X, si tratta di Y", "Il problema non è X. Il problema è Y.", "Not X, but Y",
   "It's not about X, it's about Y", "No es X, es Y". One per chapter at most, and
   only when the contrast is the actual point.
2. **Triplets and cascades.** "coerente, testabile e riproducibile", "Non è coeso, non
   è testabile, non è manutenibile". Use the one adjective that matters, or give a
   concrete example instead of a list of virtues.
3. **One-line dramatic paragraphs.** "Questo libro è quel workflow." "Il workflow resta."
   "Moltiplicata per sedici capitoli." Fold the thought into the paragraph or cut it.
4. **Aphorism endings.** Sections that close with a moral ("L'agente lavora meglio, non
   di più.", "Quella cambia la sintassi, non il metodo."). End on the last useful fact.
5. **Signposting filler.** Delete: "Vediamo insieme", "Ecco cosa...", "Ecco i passi",
   "In questo capitolo vedremo", "Come vedremo", "È importante notare che", "Vale la
   pena sottolineare", "Questa distinzione è importante", "Il punto chiave è", "Ma c'è
   di più", "In sintesi", "In altre parole", "Facciamo un passo indietro". EN: "Let's
   dive in", "It's worth noting", "Here's the thing", "In a nutshell", "Let's break it
   down". ES: "Veamos", "Cabe destacar", "Es importante señalar", "En resumen".
6. **Inflated vocabulary.** IT: fondamentale, cruciale, potente, rivoluzionario,
   incredibile, straordinario, magia/magico, game changer, alla radice, a colpo
   d'occhio, senza soluzione di continuità, un vero e proprio, sinergia, ecosistema
   (unless literal), paradigma (once, if ever). EN: delve, leverage, robust, seamless,
   unlock, empower, elevate, crucial, powerful, game-changer, landscape, journey,
   supercharge, harness (as a verb; "the harness" as the program around the model is
   a real term and stays). ES: crucial, potente, revolucionario, increíble, mágico,
   sinergia, ecosistema, potenciar, sin fisuras.
7. **Rhetorical-question openers.** "Ti sei mai chiesto perché...?" Start with the fact,
   the problem or the story.
8. **Fake precision and fake experience.** "dieci volte più facile", "risparmi il 70%",
   "decine di progetti", "centinaia di sessioni". Use a real number from the project
   (124 task, 14 fasi, 10 MB per foto) or say nothing. Keep the author's real anecdotes
   from the preface; do not invent new ones.
9. **Symmetric scaffolding.** Do not force every section into "problema, soluzione,
   esempio, riepilogo". Vary the rhythm. A short section can be two paragraphs.
10. **Hedging and throat-clearing.** "In linea di massima", "tipicamente", "in un certo
    senso" when they add nothing.
11. **Personification hype.** "Claude capisce", "Claude pensa", "Claude decide" are
    acceptable in moderation (devs talk this way). "Claude diventa il tuo collega" and
    similar marketing lines are not.

## 3. Chapter furniture

The KDP listing promises "Cosa imparerai" at the start and a summary plus an exercise at
the end, so keep them, but lean:

- **Cosa imparerai** (`What you'll learn`, `Qué aprenderás`): one short paragraph or
  at most four plain bullets, no bold, no restating the table of contents.
- **Prerequisiti**: only when real, one or two lines.
- No "Premessa:" section heading. If the chapter needs an opening, it is the first
  paragraphs after "Cosa imparerai", without a heading.
- **Riepilogo**: three to six bullets of things the reader can now do or must remember,
  not a recap of every section.
- **Esercizio**: one concrete exercise with a clear done condition. Keep the companion
  branch reference if the original has one.

Callouts use pandoc fenced divs styled by `tools/lib/kindle.css`. No emoji, a plain
title:

```markdown
::: {.callout .callout-tip}
[Suggerimento]{.callout-title}

Testo del suggerimento.
:::
```

Classes: `callout-tip` (Suggerimento / Tip / Consejo), `callout-warning`
(Attenzione / Warning / Atención), `callout-deep-dive` (Sotto il cofano / Under the
hood / Bajo el capó), `callout-example` (Esempio / Example / Ejemplo),
`callout-prompt` (Prompt riusabile / Reusable prompt / Prompt reutilizable). Use a
callout only when the content really is a side note. Two or three per chapter is
plenty; a chapter that is all callouts is a slide deck.

## 4. Code, commands and figures

- Every command, file path, flag, key, identifier and slash command goes in backticks:
  `claude --version`, `/compact`, `CLAUDE.md`, `Shift+Tab`.
- Every code block is fenced with a language tag (`bash`, `json`, `python`, `php`,
  `markdown`, `yaml`, `text`). The source export lost all fences and escaped
  characters (`\-`, `\_`, `\$`, `\#`, `\*`, `\[`); restore them. Shell commands are
  written without a `$` prompt. When the original code exists in the companion repos
  (`snippets/cap-NN/`, old numbering, or the Photogallery repo), copy it from there.
- Prompts the reader types stay in the edition's language (IT prompts in the IT
  edition, EN prompts in EN). Long prompts go in a ```text block.
- Figures: `![Didascalia](figures/cap-NN/fig-XX.png)` on its own line, followed by
  nothing else; pandoc makes the alt text the caption. One caption, written once, no
  "Figura 1.1:" prefix and no second italic caption line. Several screenshots show an
  old UI (e.g. Sonnet 4.6 in `/model`, `/cost`): keep them only if the text around them
  is still true, otherwise drop the figure and list it in the chapter's TODO comment
  for a new screenshot.

## 5. Language and jargon

Write the way working engineers in that language actually talk and write in a good
technical blog or internal wiki. Not translated-from-English, not marketing.

### Italian

Italian devs use English nouns with Italian articles and Italianised verbs. Use:
il deploy / fare il deploy / deployare, il commit / committare, il push / pushare,
il branch, il merge / mergiare, la PR (la pull request), il repo / il repository,
la build / buildare, lanciare i test, il test che fallisce / che passa, il bug,
debuggare, il refactoring, la feature, il task, il prompt, il token, la sessione,
il tool, l'agent / gli agent (product term; "agente" also fine in prose about the
concept), la skill / le skill (plural invariable, never "skills" inside Italian
prose except in quoted English titles), l'hook / gli hook, il plugin / i plugin,
il server MCP, la context window / la finestra di contesto, il frontmatter, lo
scaffolding, il setup, il worktree, il diff, il mock, lo stack, il backend, il
frontend, il framework, l'endpoint, il payload, il file `.env`.

Avoid stiff translations: ramo (branch), archivio/deposito (repository),
distribuzione/rilascio for deploy, istantanea, cartella di lavoro for working tree
when "working tree" is meant, "compilazione" for a JS build. Avoid gratuitous English
where Italian is natural and common: "hands-on" (pratico), "trick" (trucco),
"reference" (riferimento), "end-to-end" is fine once per chapter, "tips"
(consigli/suggerimenti), "use case" (caso d'uso), "insight" (spunto, risultato,
scoperta; keep only in the data-analysis sense if needed).

Second person singular ("tu"), present tense, active voice. Plural English nouns
are invariable in Italian prose: "le skill", "gli agent", "i task", "i commit".

### English

Plain, direct, contractions welcome ("you'll", "don't"). American spelling. Sentences
that a senior engineer would say out loud. Use real dev idiom: ship, wire up, spin up,
tear down, flaky test, green build, the happy path, bikeshedding (rarely). Avoid the
vocabulary in section 2.6.

### Spanish

Neutral Spanish readable in Spain and Latin America, "tú". Spanish devs mix English
nouns too, but translate more than Italians: hacer deploy / desplegar, hacer commit,
la rama (common and natural), el repo / el repositorio, la build / compilar, correr
(LatAm) or ejecutar los tests, el bug, depurar, la feature / la funcionalidad, la
tarea (task, but keep "task" for SDD task IDs and file names), el prompt, el token,
la skill / las skills, el agente / los agentes, el hook / los hooks, el plugin, el
servidor MCP, la ventana de contexto, el frontmatter, el worktree, el pull request
(masculine in most dev communities), el endpoint, el backend, el frontend.

## 6. Accuracy

- Facts about Claude Code must match `FACTS.md` (verified October 2026). If the old
  text says something FACTS.md contradicts, fix it. If the old text says something
  FACTS.md does not cover and you are not sure it is still true, keep it neutral and
  add an HTML comment `<!-- VERIFY: ... -->` right there. Never invent a command,
  flag, setting or version.
- Facts about the Photogallery must match the companion repo
  (`github.com/hidran/claude-code-book-photogallery`): Laravel 13 REST API under
  `/api/v1`, Filament v5 admin, React 19 + Vite 6 + Tailwind CSS v4, Sanctum tokens,
  queued jobs for resize and EXIF, docs in `docs/REQUIREMENTS.md`, `docs/DESIGN.md`,
  `docs/TASKS.md` (124 task, 14 fasi). The first edition mentions NestJS in places;
  that is wrong for this project.
- Companion repo branch names are real and keep the first edition's chapter numbers
  (`book/cap-13-wave-1-backend`, `book/cap-10-3-execution`). Quote them verbatim even
  when the chapter number changed; `00-front-matter/03-come-leggere.md` explains why.
- Chapter cross-references use the NEW numbering in `CHAPTER-MAP.md`.

## 7. Length

Do not pad and do not gut. A chapter that was 30k characters should land between
roughly 20k and 30k: the cut comes from filler, repetition and restated summaries,
not from technical content, code or steps. Keep every working example, prompt and
command that is still correct.
