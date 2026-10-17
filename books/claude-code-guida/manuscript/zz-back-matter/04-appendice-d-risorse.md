# Appendice D. Risorse

Qui trovi i link su cui si appoggiano i capitoli, controllati a ottobre 2026: la documentazione ufficiale di Claude Code divisa per parte del libro, gli indirizzi per seguire le novità, i repository companion e la documentazione degli strumenti usati nei progetti. Ho tenuto solo pagine ufficiali che ho aperto e verificato. Se un link non risponde più, cerca il titolo della pagina nell'indice della documentazione.

## D.1 La documentazione ufficiale di Claude Code

La documentazione di Claude Code sta su `code.claude.com`. La prima edizione puntava a `docs.anthropic.com`: se trovi quel dominio in un vecchio tutorial, cerca la stessa pagina sul sito nuovo.

L'indice completo, una riga per pagina, è un file di testo: <https://code.claude.com/docs/llms.txt>.

Ogni pagina ha anche una versione Markdown, che ottieni aggiungendo `.md` all'indirizzo (`https://code.claude.com/docs/en/hooks-guide.md`). È quella da passare a Claude quando vuoi che lavori sulla documentazione aggiornata invece che su quello che ricorda.

::: {.callout .callout-tip}
[Suggerimento]{.callout-title}

Prima di fidarti di un comando letto qui o altrove, apri la pagina `commands` o `cli-reference` sulla tua versione. Le tabelle di quelle due pagine spesso dicono anche da quale versione un comando è cambiato.
:::

### Da tenere sempre a portata di mano

- Tutti gli slash command: <https://code.claude.com/docs/en/commands>
- Le opzioni della riga di comando: <https://code.claude.com/docs/en/cli-reference>
- Scorciatoie da tastiera e modalità interattiva: <https://code.claude.com/docs/en/interactive-mode>
- Troubleshooting generale: <https://code.claude.com/docs/en/troubleshooting>

### Parti I e II, fondamenta e analisi dati (capitoli 1-6)

- Installazione e canali di aggiornamento: <https://code.claude.com/docs/en/setup>
- Quickstart: <https://code.claude.com/docs/en/quickstart>
- Problemi di installazione: <https://code.claude.com/docs/en/troubleshoot-install>
- Login, API key e ordine delle credenziali: <https://code.claude.com/docs/en/authentication>
- I tool a disposizione dell'agente: <https://code.claude.com/docs/en/tools-reference>
- Modalità di permesso, Plan Mode compreso: <https://code.claude.com/docs/en/permission-modes>
- La sandbox per i comandi Bash: <https://code.claude.com/docs/en/sandboxing>
- Modelli, alias ed effort: <https://code.claude.com/docs/en/model-config>
- Modalità headless (`claude -p`): <https://code.claude.com/docs/en/headless>
- Estensione per VS Code: <https://code.claude.com/docs/en/vs-code>
- Plugin per JetBrains: <https://code.claude.com/docs/en/jetbrains>
- App desktop: <https://code.claude.com/docs/en/desktop>

### Parte III, estendere Claude Code (capitoli 7-10)

- `CLAUDE.md`, `.claude/rules/`, `AGENTS.md` e memoria automatica: <https://code.claude.com/docs/en/memory>
- Skill e custom command: <https://code.claude.com/docs/en/skills>
- Subagent: <https://code.claude.com/docs/en/sub-agents>
- I marketplace di Anthropic, da cui si installa Superpowers: <https://code.claude.com/docs/en/plugins/anthropic-marketplaces>

### Parte IV, controllare e automatizzare (capitoli 11-15)

- Regole allow, ask e deny: <https://code.claude.com/docs/en/permissions>
- Modalità di permesso e auto mode: <https://code.claude.com/docs/en/permission-modes>
- Sandbox: <https://code.claude.com/docs/en/sandboxing>
- Hook: <https://code.claude.com/docs/en/hooks-guide>
- MCP: <https://code.claude.com/docs/en/mcp>
- Panoramica dei plugin: <https://code.claude.com/docs/en/plugins/overview>
- Creare un plugin: <https://code.claude.com/docs/en/plugins/create>
- Comandi `claude plugin`: <https://code.claude.com/docs/en/plugins/cli-reference>
- Eval dei plugin (`claude plugin eval`): <https://code.claude.com/docs/en/plugin-evals>
- Memoria e contesto, la stessa pagina del capitolo 7: <https://code.claude.com/docs/en/memory>

### Parti V e VI, i progetti (capitoli 16-23)

- Sessioni parallele con i worktree: <https://code.claude.com/docs/en/worktrees>
- Agent view e sessioni in background: <https://code.claude.com/docs/en/agent-view>
- `/goal`: <https://code.claude.com/docs/en/goal>
- Code Review: <https://code.claude.com/docs/en/code-review>
- Personalizzare la review con `REVIEW.md`: <https://code.claude.com/docs/en/code-review-customize>
- La review sulle pull request di GitHub: <https://code.claude.com/docs/en/code-review-pull-requests>
- Ultrareview: <https://code.claude.com/docs/en/ultrareview>
- GitHub Actions e `@claude`: <https://code.claude.com/docs/en/github-actions>
- Sessioni nel cloud: <https://code.claude.com/docs/en/claude-code-on-the-web>

## D.2 Restare aggiornati

Claude Code esce con una versione nuova quasi ogni giorno, e seguirle tutte non serve. Io guardo due pagine.

Il digest settimanale raccoglie le novità che cambiano il modo di lavorare, con esempi e link alla pagina che ne parla: <https://code.claude.com/docs/en/whats-new>. Mentre chiudo questa edizione l'ultimo digest pubblicato è quello della settimana 37 (7-11 settembre 2026); per quello che è uscito dopo c'è solo il changelog.

Il changelog ha una voce per ogni versione ed è generato dal `CHANGELOG.md` del repository `anthropics/claude-code`: <https://code.claude.com/docs/en/changelog>. Lo apro quando un comando del libro si comporta in modo diverso e voglio sapere in che versione è cambiato.

Nel terminale ti bastano tre comandi:

```bash
claude --version   # la versione installata, per esempio "2.1.302 (Claude Code)"
claude update      # controlla e installa subito l'ultima versione
claude doctor      # diagnostica in sola lettura, compreso l'esito dell'ultimo aggiornamento
```

Con l'installer nativo l'aggiornamento avviene da solo in background e vale dal riavvio successivo. Con Homebrew e WinGet no: aggiorni tu con `brew upgrade claude-code` o `winget upgrade Anthropic.ClaudeCode`.

Il canale di aggiornamento si sceglie in `/config`, alla voce Auto-update channel (nel file di impostazioni è `autoUpdatesChannel`). `latest`, il default, riceve ogni versione appena esce. `stable` resta circa una settimana indietro e salta le versioni con regressioni importanti: è la scelta giusta se preferisci la prudenza, per esempio in un team. Puoi anche installare direttamente un canale:

```bash
curl -fsSL https://claude.ai/install.sh | bash -s stable
```

Quando arriva una novità che ti interessa, provala da sola su un progetto piccolo prima di portarla nel lavoro vero, e controlla se rende superato un passaggio del libro. Se succede, la segnalazione è benvenuta (vedi D.3).

## D.3 I repository del libro

Il codice dei progetti è pubblico su GitHub. I branch `book/...` fotografano le tappe dei capitoli e portano ancora i numeri della prima edizione: la corrispondenza completa è nell'Appendice E.

- Photogallery, Parte VI: <https://github.com/hidran/claude-code-book-photogallery>. Il branch `main` è il progetto finito: API Laravel 13 sotto `/api/v1`, admin Filament v5, SPA React 19 con Vite 6 e Tailwind CSS v4, token Sanctum, e i documenti `docs/REQUIREMENTS.md`, `docs/DESIGN.md` e `docs/TASKS.md`.
- Landing page FluentAiPro, capitolo 16: <https://github.com/hidran/fluentaipro-claude-landingpage>, con un branch per ogni fase (`book/cap-10-1-mockups`, `book/cap-10-2-spec`, `book/cap-10-3-execution`, `book/cap-10-5-deploy-ready`).
- Snippet e prompt: <https://github.com/hidran/claude-code-book-snippets>. Raccoglie i prompt riusabili capitolo per capitolo e la raccolta dell'Appendice C in testo semplice, comoda per il copia e incolla.

Le issue del repository `claude-code-book-snippets` sono anche il canale per segnalare errori nel libro. L'Appendice E spiega cosa scrivere nella segnalazione.

## D.4 Plugin e marketplace

- Il marketplace ufficiale `claude-plugins-official`, che Claude Code aggiunge da solo alla prima sessione interattiva: <https://github.com/anthropics/claude-plugins-official>
- Il marketplace della community `claude-community`: <https://github.com/anthropics/claude-plugins-community>
- Superpowers di Jesse Vincent, il plugin dei capitoli 8, 16 e 19: <https://github.com/obra/superpowers>. Si installa dal marketplace ufficiale con `/plugin install superpowers@claude-plugins-official`.

::: {.callout .callout-warning}
[Attenzione]{.callout-title}

Le istruzioni più vecchie dicono di lanciare `/plugin marketplace add anthropics/claude-code`. Quel comando aggiunge il marketplace dimostrativo `claude-code-plugins`, che non è quello ufficiale.
:::

## D.5 Gli strumenti dei progetti

La documentazione ufficiale degli strumenti che Claude usa nei capitoli. Quando un'API di libreria ti sembra strana, controlla qui prima di chiedere a Claude di indovinare.

| Strumento | Capitoli | Documentazione |
|---|---|---|
| pandas | 4-6 | <https://pandas.pydata.org/docs/> |
| openpyxl | 5 | <https://openpyxl.readthedocs.io/> |
| matplotlib | 6 | <https://matplotlib.org/> |
| ReportLab | 6 | <https://docs.reportlab.com/> |
| React | 16-23 | <https://react.dev/> |
| Vite | 16-23 | <https://vite.dev/> |
| Tailwind CSS | 16-23 | <https://tailwindcss.com/docs> |
| Firebase Hosting | 16 | <https://firebase.google.com/docs/hosting> |
| Laravel | 17-23 | <https://laravel.com/docs> |
| Filament | 17-23 | <https://filamentphp.com/docs> |
| AWS CloudFormation | 23 | <https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/Welcome.html> |

Le versioni contano più del solito. Photogallery usa Laravel 13 e Filament v5, e molti esempi in rete sono scritti per versioni precedenti: indica sempre la versione nel prompt, oppure scrivila nel `CLAUDE.md` del progetto come nel capitolo 18.
