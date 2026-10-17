# Apéndice D. Recursos

Aquí tienes los enlaces en los que se apoyan los capítulos, revisados en octubre de 2026: la documentación oficial de Claude Code dividida por partes del libro, dónde seguir las novedades, los repositorios companion y la documentación de las herramientas que se usan en los proyectos. Solo he dejado páginas oficiales que he abierto y comprobado. Si un enlace deja de responder, busca el título de la página en el índice de la documentación.

## D.1 La documentación oficial de Claude Code

La documentación de Claude Code está en `code.claude.com`. La primera edición apuntaba a `docs.anthropic.com`: si encuentras ese dominio en un tutorial antiguo, busca la misma página en el sitio nuevo.

El índice completo, una línea por página, es un archivo de texto: <https://code.claude.com/docs/llms.txt>.

Cada página tiene también una versión Markdown, que obtienes añadiendo `.md` a la dirección (`https://code.claude.com/docs/en/hooks-guide.md`). Es la que conviene pasarle a Claude cuando quieres que trabaje con la documentación actualizada y no con lo que recuerda.

::: {.callout .callout-tip}
[Consejo]{.callout-title}

Antes de fiarte de un comando que hayas leído aquí o en otro sitio, abre la página `commands` o `cli-reference` de tu versión. Las tablas de esas dos páginas suelen indicar también desde qué versión ha cambiado un comando.
:::

### Para tener siempre a mano

- Todos los slash commands: <https://code.claude.com/docs/en/commands>
- Las opciones de la línea de comandos: <https://code.claude.com/docs/en/cli-reference>
- Atajos de teclado y modo interactivo: <https://code.claude.com/docs/en/interactive-mode>
- Troubleshooting general: <https://code.claude.com/docs/en/troubleshooting>

### Partes I y II, fundamentos y análisis de datos (capítulos 1-6)

- Instalación y canales de actualización: <https://code.claude.com/docs/en/setup>
- Quickstart: <https://code.claude.com/docs/en/quickstart>
- Problemas de instalación: <https://code.claude.com/docs/en/troubleshoot-install>
- Login, API keys y orden de las credenciales: <https://code.claude.com/docs/en/authentication>
- Los tools a disposición del agente: <https://code.claude.com/docs/en/tools-reference>
- Modos de permisos, Plan Mode incluido: <https://code.claude.com/docs/en/permission-modes>
- El sandbox para los comandos Bash: <https://code.claude.com/docs/en/sandboxing>
- Modelos, alias y effort: <https://code.claude.com/docs/en/model-config>
- Modo headless (`claude -p`): <https://code.claude.com/docs/en/headless>
- Extensión para VS Code: <https://code.claude.com/docs/en/vs-code>
- Plugin para JetBrains: <https://code.claude.com/docs/en/jetbrains>
- App de escritorio: <https://code.claude.com/docs/en/desktop>

### Parte III, ampliar Claude Code (capítulos 7-10)

- `CLAUDE.md`, `.claude/rules/`, `AGENTS.md` y memoria automática: <https://code.claude.com/docs/en/memory>
- Skills y comandos personalizados: <https://code.claude.com/docs/en/skills>
- Subagentes: <https://code.claude.com/docs/en/sub-agents>
- Los marketplaces de Anthropic, desde los que se instala Superpowers: <https://code.claude.com/docs/en/plugins/anthropic-marketplaces>

### Parte IV, control y automatización (capítulos 11-15)

- Reglas allow, ask y deny: <https://code.claude.com/docs/en/permissions>
- Modos de permisos y auto mode: <https://code.claude.com/docs/en/permission-modes>
- Sandbox: <https://code.claude.com/docs/en/sandboxing>
- Hooks: <https://code.claude.com/docs/en/hooks-guide>
- MCP: <https://code.claude.com/docs/en/mcp>
- Visión general de los plugins: <https://code.claude.com/docs/en/plugins/overview>
- Crear un plugin: <https://code.claude.com/docs/en/plugins/create>
- Comandos `claude plugin`: <https://code.claude.com/docs/en/plugins/cli-reference>
- Evals de los plugins (`claude plugin eval`): <https://code.claude.com/docs/en/plugin-evals>
- Memoria y contexto, la misma página del capítulo 7: <https://code.claude.com/docs/en/memory>

### Partes V y VI, los proyectos (capítulos 16-23)

- Sesiones en paralelo con worktrees: <https://code.claude.com/docs/en/worktrees>
- Agent view y sesiones en segundo plano: <https://code.claude.com/docs/en/agent-view>
- `/goal`: <https://code.claude.com/docs/en/goal>
- Code Review: <https://code.claude.com/docs/en/code-review>
- Personalizar la review con `REVIEW.md`: <https://code.claude.com/docs/en/code-review-customize>
- La review en los pull requests de GitHub: <https://code.claude.com/docs/en/code-review-pull-requests>
- Ultrareview: <https://code.claude.com/docs/en/ultrareview>
- GitHub Actions y `@claude`: <https://code.claude.com/docs/en/github-actions>
- Sesiones en la nube: <https://code.claude.com/docs/en/claude-code-on-the-web>

## D.2 Mantenerse al día

Claude Code saca una versión nueva casi cada día, y no hace falta seguirlas todas. Yo miro dos páginas.

El resumen semanal reúne las novedades que cambian la forma de trabajar, con ejemplos y enlaces a la página que habla de ellas: <https://code.claude.com/docs/en/whats-new>. Mientras cierro esta edición, el último resumen publicado es el de la semana 37 (7-11 de septiembre de 2026); para lo que ha salido después solo está el changelog.

El changelog tiene una entrada por versión y se genera a partir del `CHANGELOG.md` del repositorio `anthropics/claude-code`: <https://code.claude.com/docs/en/changelog>. Lo abro cuando un comando del libro se comporta de otra manera y quiero saber en qué versión cambió.

En la terminal te bastan tres comandos:

```bash
claude --version   # la versión instalada, por ejemplo "2.1.302 (Claude Code)"
claude update      # comprueba e instala ya la última versión
claude doctor      # diagnóstico de solo lectura, incluido el resultado de la última actualización
```

Con el instalador nativo, la actualización se hace sola en segundo plano y se aplica en el siguiente reinicio. Con Homebrew y WinGet no: actualizas tú con `brew upgrade claude-code` o `winget upgrade Anthropic.ClaudeCode`.

El canal de actualización se elige en `/config`, en la opción Auto-update channel (en el archivo de configuración es `autoUpdatesChannel`). `latest`, el predeterminado, recibe cada versión en cuanto sale. `stable` va más o menos una semana por detrás y se salta las versiones con regresiones importantes: es la opción adecuada si prefieres ir con cuidado, por ejemplo en un equipo. También puedes instalar directamente un canal:

```bash
curl -fsSL https://claude.ai/install.sh | bash -s stable
```

Cuando llegue una novedad que te interese, pruébala por separado en un proyecto pequeño antes de llevarla al trabajo real, y comprueba si deja obsoleto algún paso del libro. Si es así, el aviso será bienvenido (ver D.3).

## D.3 Los repositorios del libro

El código de los proyectos es público en GitHub. Las ramas `book/...` reflejan las etapas de los capítulos y conservan los números de la primera edición: la correspondencia completa está en el Apéndice E.

- Photogallery, Parte VI: <https://github.com/hidran/claude-code-book-photogallery>. La rama `main` es el proyecto terminado: API Laravel 13 bajo `/api/v1`, admin con Filament v5, SPA React 19 con Vite 6 y Tailwind CSS v4, tokens Sanctum, y los documentos `docs/REQUIREMENTS.md`, `docs/DESIGN.md` y `docs/TASKS.md`.
- Landing page de FluentAiPro, capítulo 16: <https://github.com/hidran/fluentaipro-claude-landingpage>, con una rama por fase (`book/cap-10-1-mockups`, `book/cap-10-2-spec`, `book/cap-10-3-execution`, `book/cap-10-5-deploy-ready`).
- Snippets y prompts: <https://github.com/hidran/claude-code-book-snippets>. Reúne los prompts reutilizables capítulo por capítulo y la colección del Apéndice C en texto plano, cómoda para copiar y pegar.

Las issues del repositorio `claude-code-book-snippets` son también el canal para avisar de errores en el libro. El Apéndice E explica qué escribir en el aviso.

## D.4 Plugins y marketplaces

- El marketplace oficial `claude-plugins-official`, que Claude Code añade por su cuenta en la primera sesión interactiva: <https://github.com/anthropics/claude-plugins-official>
- El marketplace de la comunidad `claude-community`: <https://github.com/anthropics/claude-plugins-community>
- Superpowers de Jesse Vincent, el plugin de los capítulos 8, 16 y 19: <https://github.com/obra/superpowers>. Se instala desde el marketplace oficial con `/plugin install superpowers@claude-plugins-official`.

::: {.callout .callout-warning}
[Atención]{.callout-title}

Las instrucciones más antiguas dicen que ejecutes `/plugin marketplace add anthropics/claude-code`. Ese comando añade el marketplace de demostración `claude-code-plugins`, que no es el oficial.
:::

## D.5 Las herramientas de los proyectos

La documentación oficial de las herramientas que Claude usa en los capítulos. Cuando la API de una librería te parezca rara, mírala aquí antes de pedirle a Claude que adivine.

| Herramienta | Capítulos | Documentación |
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

Las versiones importan más de lo normal. Photogallery usa Laravel 13 y Filament v5, y muchos ejemplos de internet están escritos para versiones anteriores: indica siempre la versión en el prompt, o escríbela en el `CLAUDE.md` del proyecto como en el capítulo 18.
