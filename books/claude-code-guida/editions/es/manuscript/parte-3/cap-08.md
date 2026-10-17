# Capítulo 8. Comandos personalizados y el plugin Superpowers

::: {.chapter-goals}
[Qué aprenderás]{.callout-title}

- Cuándo conviene convertir un prompt que repites en un comando personalizado, y cómo escribirlo.
- Cómo pasarle argumentos y contexto al comando: `$ARGUMENTS`, `$0`, `` !`comando` `` y `@file`.
- Tres comandos para usar desde hoy, más un `/commit` que mantiene limpio el historial de Git.
- Qué trae el plugin Superpowers y cómo instalarlo desde el marketplace oficial.

[Requisitos previos]{.callout-title}

Los capítulos 1-7, y al menos un `CLAUDE.md` escrito (capítulo 7).

:::

Piensa en cuántas veces has escrito "ejecuta los tests y dime cuál falla" o "haz un commit con un mensaje decente". Cada vez con palabras un poco distintas: un día pides "listar los imports que no se usan", al día siguiente "encontrar los imports sobrantes", y Claude hace dos cosas ligeramente diferentes. Las instrucciones cambian según la prisa y lo que recuerdes en ese momento, y el resultado cambia con ellas.

Un comando personalizado resuelve el problema de la forma más simple: escribes el prompt una vez, con calma, lo guardas en un archivo y a partir de ahí lo invocas con una barra. El prompt no cambia, así que el comportamiento también es predecible. Mi regla: la tercera vez que reescribo el mismo prompt, lo convierto en un comando. No antes, porque las dos primeras veces sirven para descubrir cómo formularlo bien.

También hay una ventaja para el equipo. Los comandos de proyecto viven en el repositorio, y cualquiera que abra Claude Code en esa carpeta (un compañero, un freelance recién llegado, tú en otro ordenador) se los encuentra listos, con su descripción en el menú.

## 8.1 Qué es un comando personalizado

Un comando personalizado es un archivo Markdown en una carpeta concreta. El nombre del archivo se convierte en el nombre del comando: `review-types.md` pasa a ser `/review-types`. Cuando lo invocas, Claude Code toma el contenido del archivo y lo usa como prompt, como si lo acabaras de escribir tú.

::: {.callout .callout-deep-dive}
[Bajo el capó]{.callout-title}

Hoy los comandos personalizados forman parte de las skills. Un archivo `.claude/commands/deploy.md` y una skill en `.claude/skills/deploy/SKILL.md` crean los dos `/deploy` y funcionan igual. Los archivos de `.claude/commands/` son el formato antiguo y siguen funcionando; para trabajo nuevo, la documentación recomienda las skills. Si un comando y una skill tienen el mismo nombre, gana la skill. Aquí uso `.claude/commands/` porque es la forma más rápida de empezar. En el capítulo 9 verás el formato skill, que hace lo mismo y algunas cosas más (archivos de apoyo, invocación automática, ejecución en un contexto separado).
:::

### La estructura

El formato mínimo es un frontmatter YAML y un cuerpo:

```markdown
---
description: Descripción breve que aparece en el autocompletado
---

Cuerpo del comando: las instrucciones que Claude ejecutará.
Aquí puedes escribir un prompt estructurado, tan largo como quieras,
con listas, condiciones y criterios de salida.
```

Todos los campos del frontmatter son opcionales, pero dos los usarás casi siempre. `description` es la línea que ves en el menú al pulsar `/`: que sea corta y clara, porque es lo que leen tú y tus compañeros cuando buscan el comando adecuado. También le sirve a Claude, y en la sección 8.3 verás por qué. `argument-hint` describe el argumento que espera el comando y aparece en el autocompletado después del nombre.

Los archivos de comando aceptan el mismo frontmatter que las skills, salvo `name` y `paths`. Así que ya puedes usar `allowed-tools` (los tools que Claude puede usar sin pedirte permiso mientras el comando está activo), `model` y `effort`, y `disable-model-invocation`, que verás en la sección 8.3. El capítulo 9 los retoma todos.

### Dónde guardar los archivos

Los comandos viven en dos sitios: `~/.claude/commands/` para los personales, disponibles en todos los proyectos de esa máquina, y `.claude/commands/` dentro del repositorio para los de proyecto, que se suben con un commit junto con el código.

```text
~/.claude/commands/          # personales, siempre disponibles
├── fix-tests.md
├── clean-imports.md
└── spawn-pr.md

mio-progetto/.claude/commands/   # de proyecto, en el repo con commit
├── analyze-schema.md
└── deploy-staging.md
```

Mi regla para elegir: si el comando menciona rutas, scripts o convenciones de ese proyecto (deploy a staging, informes desde la base de datos), pertenece al proyecto; si funcionaría en cualquier proyecto JavaScript o Python (revisión de tipos, limpieza de imports), va en la carpeta personal.

Puedes organizar los comandos en subcarpetas. Una subcarpeta añade un prefijo al nombre: `.claude/commands/frontend/component.md` se convierte en `/frontend:component`. Cuando los comandos de un proyecto pasan de la decena, el menú lo agradece.

### Un ejemplo completo

Un comando completo, para proyectos TypeScript:

```markdown
---
description: Revisa los tipos del archivo actual y sugiere mejoras
argument-hint: (opcional) ruta del archivo que analizar
---

Lee el archivo en el que estamos trabajando (o $ARGUMENTS si se indica).
Comprueba la calidad de los tipos TypeScript:

- Ningún `any` oculto o implícito
- Tipos de retorno siempre explícitos en las funciones públicas
- Generics donde tenga sentido usarlos
- Tipos unión exhaustivos con discriminante cuando sea posible

Para cada problema encontrado: indica el número de línea, explica por qué
es un problema y propón una corrección concreta. No apliques
nada, solo un informe con las propuestas.
```

Guardado como `~/.claude/commands/review-types.md`, queda disponible en todas tus sesiones. La próxima vez que trabajes en un archivo TypeScript escribes `/review-types` y recibes una revisión con los mismos criterios y el mismo formato de siempre.

### Por qué un archivo y no un prompt a mano

Escribir más rápido es la ganancia menos interesante. Importa más que tú y tus compañeros uséis el mismo prompt con los mismos criterios de salida, y que el prompt pase por Git: cuando dentro de un mes añadas un criterio a la revisión de tipos, el commit `feat: añade control de generics a review-types` le dice a todo el mundo cuándo y por qué cambió el comando. Y un comando no tiene por qué ser de tres líneas: puede describir una secuencia de pasos, leer archivos o pedir confirmación a mitad de camino, como los comandos de la sección 8.3.

## 8.2 Escribir el primer comando personalizado

Lo más directo es partir de un prompt que ya usas. Lo tomas tal cual, lo pegas en un archivo Markdown, añades el frontmatter y listo.

### Crea la carpeta y el archivo

Crea la carpeta, si todavía no existe, y el archivo. El nombre del archivo será el nombre del comando, así que para tener `/clean-imports`:

```bash
# comando personal
mkdir -p ~/.claude/commands
touch ~/.claude/commands/clean-imports.md

# o comando de proyecto, desde la raíz del repositorio
mkdir -p .claude/commands
touch .claude/commands/clean-imports.md
```

Abre el archivo y escribe el frontmatter y el cuerpo:

```markdown
---
description: Ordena y limpia los imports del archivo actual
---

Lee el archivo en el que estamos trabajando.

Ordena los imports en tres grupos separados por una línea en blanco:
1. Librerías estándar y node_modules (p. ej. `react`, `lodash`, `fs`)
2. Alias del proyecto (p. ej. `@app/`, `@shared/`, `~/`)
3. Imports relativos (p. ej. `./Component`, `../utils`)

Dentro de cada grupo, ordena alfabéticamente.
Elimina los imports que no se usan en el archivo.

Muéstrame el diff antes de aplicar cualquier cambio.
Espera mi confirmación.
```

### Prueba el comando

Si Claude Code ya estaba abierto cuando creaste el archivo, ejecuta `/reload-skills`: vuelve a leer las carpetas de skills y las de comandos, así que no hace falta salir y volver a entrar. Si no, cierra la sesión y ábrela de nuevo.

Escribe `/` y empieza a teclear `clean`. En el menú aparece `/clean-imports` con la descripción del frontmatter. Selecciónalo, pulsa `Enter` y Claude ejecuta el prompt del archivo.

### Los argumentos

Con `$ARGUMENTS` en el cuerpo, el comando acepta parámetros. Si escribes `/clean-imports src/services/auth.ts`, el texto `src/services/auth.ts` sustituye a `$ARGUMENTS` antes de que el prompt llegue a Claude.

Un comando pensado para recibir un argumento:

```markdown
---
description: Analiza el archivo indicado y propón refactorizaciones
argument-hint: ruta del archivo que analizar
---

Lee el archivo $ARGUMENTS.

Analiza el código y propón refactorizaciones en estos ejes:
- Funciones demasiado largas (>30 líneas): sugiere cómo dividirlas
- Lógica duplicada: identifica patrones repetidos
- Nombres poco descriptivos: propón mejores nombres para variables y funciones
- Complejidad ciclomática: señala las funciones con más de 4 ramas

Para cada propuesta: muestra el código actual, el código sugerido
y la justificación en una línea.
```

Guardado como `~/.claude/commands/refactor-file.md`, se usa así:

```text
/refactor-file src/components/DataTable.tsx
```

Cuando hay más de un argumento, puedes tomarlos por posición. `$ARGUMENTS[0]`, o la forma corta `$0`, es el primero, `$1` el segundo, y así sucesivamente: la numeración empieza en cero. Con un cuerpo que dice "Analiza el archivo $0 y céntrate en $1", el comando `/refactor-file src/api/client.ts duplicación` pone la ruta en `$0` y la palabra `duplicación` en `$1`. El frontmatter acepta también un campo `arguments` para dar nombre a los argumentos posicionales; lo verás en el capítulo 9.

Si el cuerpo no tiene ningún marcador, los argumentos no se pierden: Claude Code los añade al final del prompt como `ARGUMENTS: <valor>`.

### Contexto dinámico: `` !`comando` `` y `@file`

Con un prompt estático, Claude suele dar dos o tres vueltas de tools antes del trabajo de verdad: `git status`, el diff, el archivo de especificación. Puedes hacer que se encuentre esos datos ya preparados.

Un comando de shell escrito como `` !`comando` ``, al principio de una línea o después de un espacio, se ejecuta antes de que el prompt llegue a Claude, y su salida ocupa el lugar del marcador. Para varias líneas de shell hay un bloque delimitado que se abre con ` ```! `. El timeout es el del tool Bash, dos minutos, así que nada de comandos largos.

Una referencia `@ruta/del/archivo` en el cuerpo adjunta ese archivo al prompt, igual que cuando la escribes a mano en la sesión.

Un comando de proyecto para la Photogallery que usa las dos cosas:

```markdown
---
description: Compara el diff actual con DESIGN.md
allowed-tools: Bash(git diff *)
---

## Cambios en curso

!`git diff --stat`

## Especificación de referencia

@docs/DESIGN.md

Compara los cambios con la especificación: tipos de columna y nulabilidad,
forma de las respuestas, reglas de validación, status codes.
Enumera cada desviación con archivo y línea. Si no encuentras ninguna, dilo.
```

El repositorio companion de la Photogallery tiene un comando parecido, `.claude/commands/spec-check.md`, que le pide a Claude que ejecute él mismo `git diff` y lea `docs/DESIGN.md`; con la inyección, esos pasos desaparecen.

::: {.callout .callout-warning}
[Atención]{.callout-title}

Los comandos `` !`...` `` se ejecutan en tu máquina en cuanto invocas el comando, antes de que Claude vea nada. Si instalas comandos o skills escritos por otros, lee el archivo antes de usarlo. Si quieres desactivar la inyección por completo, el ajuste es `"disableSkillShellExecution": true`.
:::

## 8.3 Tres comandos personalizados para usar ya

Tres situaciones del día a día: tests que fallan, imports desordenados, trabajo que hay que llevar a un PR. Guarda los comandos en `~/.claude/commands/` y adáptalos a tu stack.

### /fix-tests, diagnóstico y propuesta de fix para cada test roto

El comando ejecuta la suite y, para cada fallo, lee el código, clasifica la causa y propone un fix. No aplica nada: te da una lista para leer.

Guárdalo como `~/.claude/commands/fix-tests.md`:

```markdown
---
description: Ejecuta los tests, diagnostica los fallos y propón fixes
---

Ejecuta el comando de tests del proyecto. Mira el package.json para
saber qué script usar (normalmente `pnpm test`, `npm test` o
`pytest`). Si no consigues determinarlo, pregúntame.

Para cada test que falle:
1. Lee el archivo de test y el archivo bajo test
2. Identifica la causa del fallo entre estas categorías:
   - Cambio de API: la firma de la función ha cambiado
   - Bug en el código: el código no hace lo que el test espera
   - Test obsoleto: el test comprueba un comportamiento eliminado a propósito
   - Problema de entorno: dependencia que falta, variable sin definir
3. Propón el fix concreto con el diff de los cambios necesarios

No apliques nada. Preséntame una lista estructurada con:
- Nombre del test que falla
- Categoría del fallo
- Causa identificada
- Fix propuesto (diff)

Al final dime cuántos tests hay en total, cuántos pasan y cuántos fallan.
```

En un proyecto Node con dos tests de autenticación rotos, la salida se parece a esta:

```text
> /fix-tests

pnpm test
  FAIL  src/auth.test.ts
    x login con credenciales incorrectas → esperado 401, recibido 200
    x token caducado → esperado 403, recibido 500

[1] auth.test.ts:42  Test obsoleto
    El mock JWT sigue usando la caducidad fija de antes del refactoring
    diff: -Date.now()  +Date.now() - 3600000
[2] auth.test.ts:87  Bug en el código
    El middleware no gestiona los tokens mal formados
    diff: +if (!token) return res.status(403).json(...)

Total: 24 tests, 22 pasan, 2 fallan
```

Las categorías están ahí porque un test obsoleto y un bug en el código se arreglan en direcciones opuestas: en el primer caso cambias el test, en el segundo el código. Si Claude tiene que declarar la categoría, la decisión sigue siendo tuya y no le dejas hacer pasar el test por el camino más cómodo.

### /clean-imports, la versión completa

Es el comando de la sección 8.2. La versión que tengo en `~/.claude/commands/` añade un bloque de reglas antes de la línea del diff:

```markdown
Reglas:
- Orden alfabético dentro de cada grupo
- Elimina los imports que no se usan en el archivo (compruébalo antes de eliminar)
- Mantén los comentarios que ya haya junto a los imports a los que se refieren
- No toques nada en el resto del archivo
```

Si el proyecto ya tiene un linter que ordena los imports (ESLint con `import/order`, Biome), el comando sobra: ejecuta el linter.

### /spawn-pr, un PR a partir del trabajo actual

El comando reúne los commits de la rama, escribe el título y la descripción y abre el pull request en GitHub, pero solo después de tu confirmación. Usa la inyección para arrancar ya con los datos en la mano.

Guárdalo como `~/.claude/commands/spawn-pr.md`:

````markdown
---
description: Crea un PR de GitHub con título y descripción a partir del trabajo actual
disable-model-invocation: true
allowed-tools: Bash(git log *) Bash(git diff *) Bash(git branch *)
---

## Contexto

- Rama: !`git branch --show-current`
- Commits que incluir: !`git log --oneline origin/HEAD..HEAD`
- Archivos modificados: !`git diff --stat origin/HEAD...HEAD`

## Qué hacer

Genera:
- Título del PR: 50 caracteres como máximo, en presente, sin punto final.
  Ejemplos: "Add user authentication", "Fix null check in DataTable"
- Descripción del PR en Markdown con estas secciones:
  - `## Cambios`: qué se ha modificado y cómo
  - `## Motivación`: por qué hacían falta estos cambios
  - `## Tests`: qué se ha probado y cómo comprobar que funciona

Muéstrame el título y la descripción propuestos y espera mi aprobación.

Solo después de la aprobación:
1. Ejecuta `git push origin HEAD`
2. Ejecuta `gh pr create --title "<título>" --body "<descripción>"`
3. Muéstrame la URL del PR abierto

Si `gh` no está instalado, avísame en lugar de continuar.
````

Fíjate en lo que he puesto en `allowed-tools`: solo los comandos de Git que leen. El `git push` y el `gh pr create` se quedan fuera, así que pasan por los permisos normales de la sesión y, si trabajas en modo Manual, te los pide uno por uno. El permiso que concede `allowed-tools` solo vale mientras el comando está activo y se reinicia con tu siguiente mensaje.

::: {.callout .callout-warning}
[Atención]{.callout-title}

Como comandos y skills son lo mismo, Claude puede decidir por su cuenta usar un comando cuando la descripción encaja con lo que está haciendo. Para un informe, perfecto. Para un comando que hace push, abre pull requests o hace deploy, no: con `disable-model-invocation: true` en el frontmatter, el comando solo arranca cuando lo escribes tú. Ponlo en todo lo que tenga efectos fuera de tu editor.
:::

## 8.4 El plugin Superpowers

Los comandos que has visto hasta ahora los escribes tú. Superpowers es un plugin open source de Jesse Vincent (`obra/superpowers` en GitHub) que lleva a Claude Code un método de trabajo ya codificado, escrito y pulido por otra persona. Un plugin es un paquete que puede contener skills, agentes, hooks y servidores MCP; lo instalas una vez y lo tienes todo junto.

### Qué contiene

La ficha de Superpowers en el marketplace oficial lo describe como brainstorming, desarrollo guiado por subagentes con code review integrada, depuración sistemática, TDD red/green e instrucciones para escribir y probar skills nuevas. En la práctica son sobre todo skills:

- brainstorming antes de implementar (`brainstorming`): preguntas, alternativas y, solo después, un diseño;
- desarrollo guiado por subagentes (`subagent-driven-development`): cada tarea del plan va a un subagente, con una code review antes de la tarea siguiente;
- depuración sistemática (`systematic-debugging`): reproducir, aislar, formular una hipótesis y comprobarla, en lugar de probar fixes al azar;
- TDD red/green (`test-driven-development`): primero un test que falla, luego el código mínimo que lo hace pasar;
- escritura de skills (`writing-skills`): cómo diseñar una y cómo comprobar que funciona.

Estas skills no tienes que invocarlas tú: Claude las carga solo cuando la situación coincide con su descripción. Pides una feature nueva y arranca el brainstorming; reportas un bug y arranca la depuración sistemática. Si quieres llamar a una a mano, las skills de un plugin llevan el prefijo del plugin, con la forma `/superpowers:<nombre-skill>`.

En la Photogallery (Parte VI) encontrarás el mismo ritmo: especificación, tareas, ejecución por waves con revisión entre una tarea y la siguiente. Superpowers no es obligatorio para seguir el libro, pero te acostumbra a trabajar así.

### Instalarlo

Superpowers está en el marketplace oficial de Anthropic, `claude-plugins-official`, que Claude Code añade por su cuenta en la primera sesión interactiva. Desde el prompt:

```text
/plugin install superpowers@claude-plugins-official
```

Un plugin se instala en uno de tres scopes: usuario (todos tus proyectos), proyecto (guardado en la configuración del repositorio y, por tanto, compartido con el equipo) o local (solo tú, solo en este proyecto). Para probarlo, usuario está bien.

También puedes pasar por el marketplace del autor:

```text
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```

Si prefieres los menús, `/plugin` abre el gestor con las pestañas Discover, Installed, Marketplaces y Errors: buscas "superpowers" en Discover e instalas desde ahí.

Después de la instalación ejecuta:

```text
/reload-plugins
```

Sin el reload, la sesión actual todavía no ve las skills nuevas. Para comprobarlo, `/plugin list` muestra los plugins instalados y `/skills` lista las skills disponibles: las de Superpowers aparecen con su prefijo.

<!-- TODO screenshot: output di /skills dopo l'installazione di Superpowers, con le skill del plugin elencate -->

### Cuánto cuesta en contexto

El nombre y la descripción de cada skill se quedan en la ventana de contexto aunque no las uses, porque así es como Claude sabe cuándo sacarlas. El gestor `/plugin` muestra una estimación del coste antes de instalar, y en el capítulo 15 verás `/context` y `/skill-doctor` para saber qué skills compensan el espacio que ocupan. Con Superpowers las cuentas salen; con diez plugins instalados por curiosidad, no.

Cómo es un plugin por dentro (el manifest `.claude-plugin/plugin.json`, las carpetas `skills/`, `agents/`, `hooks/`) lo verás en el capítulo 14, donde construyes uno propio.

## 8.5 El patrón del commit atómico con /commit

Cuando trabajas con un agente que modifica una docena de archivos en pocos minutos, el historial de Git se ensucia enseguida. Al final de la sesión te encuentras con un único commit enorme, o con cuatro commits llamados "wip". Un comando `/commit` bien escrito resuelve el problema, y cuando le pillas el hábito ya no vuelves atrás.

### El comando

Un `/commit` personal que siempre pide confirmación:

````markdown
---
description: Propón un commit atómico con mensaje Conventional Commits
disable-model-invocation: true
allowed-tools: Bash(git status *) Bash(git diff *)
---

## Estado del repositorio

!`git status --short`

## Cambios en staging

!`git diff --cached`

## Qué hacer

1. Si no hay nada en staging, dímelo y para.
2. Si los cambios en staging contienen más de un cambio lógico,
   dímelo y propón cómo dividirlos. No hagas commit.
3. Elige el tipo: feat, fix, refactor, test, docs, chore, perf.
4. Escribe el mensaje en formato Conventional Commits: título
   en imperativo, sin punto final, de menos de 72 caracteres; cuerpo
   opcional con el porqué del cambio.
5. Muéstrame los archivos incluidos y el mensaje propuesto, y espera mi confirmación.
6. Solo después de la confirmación ejecuta `git commit`. No hagas push.
````

Guárdalo como `~/.claude/commands/commit.md`. El comando trabaja sobre lo que tienes en staging, y es a propósito: tú decides qué entra en el commit, Claude escribe el mensaje y te avisa si has juntado dos cosas distintas.

El repositorio companion de la Photogallery tiene una versión de proyecto en `.claude/commands/commit.md`: además elige el scope a partir de los archivos modificados (`api`, `backend`, `frontend`, `filament`, `pipeline`, `db`), cita las secciones de `DESIGN.md` en el cuerpo y hace commit sin pedir confirmación, porque ahí el commit llega al final de una tarea ya revisada.

Si no quieres escribirlo tú, el marketplace oficial tiene un plugin `commit-commands` (`/plugin install commit-commands@claude-plugins-official`) con tres comandos ya hechos: `commit`, `commit-push-pr` (commit, push y PR en un solo paso) y `clean_gone` (limpieza de las ramas locales cuyo remoto se ha borrado). Igual que las skills, los comandos de un plugin llevan el prefijo del plugin, así que los ejecutas como `/commit-commands:commit` y no chocan con tu `/commit`.

### Qué pasa cuando lo ejecutas

Con tres archivos en staging después de una corrección en la autenticación, la respuesta se parece a esta:

```text
> /commit

Archivos en staging (3):
  M  src/auth/middleware.ts     (+12 / -3)
  M  src/auth/auth.test.ts      (+18 / -5)
  M  src/auth/token.service.ts  (+4 / -1)

Mensaje propuesto:
  fix: handle expired and malformed tokens

  - middleware returns 403 for malformed tokens
  - JWT mock resets expiry correctly in tests
  - TokenService handles null/undefined edge cases

¿Confirmas, quieres modificarlo o lo cancelo?
```

El formato Conventional Commits pone un prefijo (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`) delante de un título breve, seguido de un cuerpo opcional como el de arriba.

### Por qué commits atómicos

Un commit atómico contiene un solo cambio lógico, que se describe en una frase y se sostiene por sí mismo. Sin esa disciplina, un día de trabajo con un agente produce un log así:

```text
a1b2c3d WIP
d4e5f6a sigue en wip
g7h8i9j por fin funciona
j0k1l2m algunas cosas
```

Con `/commit` después de cada parte del trabajo, el mismo día queda así:

```text
a3f1c2d feat: add format_values helper for stats output
b7e4d8a feat: add write_markdown_report function
c2b9f1e feat: implement analyze-column python script
d8e3a7c test: add tests for analyze-column
e4c1b9f docs: add slash command analyze with description
```

La diferencia tiene efectos prácticos. `git bisect` funciona, porque cada commit es un estado coherente del proyecto. `git revert e4c1b9f` quita solo la documentación del comando sin tocar los tests ni la implementación. Quien hace la revisión lee un cambio cada vez en lugar de un diff de 400 líneas mezcladas. Y cuando un agente se equivoca de camino, sabes exactamente hasta dónde volver atrás.

### Lee el mensaje antes de confirmar

El mensaje hay que leerlo siempre, aunque te fíes. Se queda en el historial del proyecto: `feat: update auth` dentro de seis meses no te dice nada, `feat: add refresh token rotation on expiry` te dice qué buscar cuando el bug aparezca en producción. Y revisa el tipo: si Claude propone `refactor:` mientras estás añadiendo una funcionalidad, corrígelo a `feat:`; si no, el log pierde utilidad para quien filtra los commits por tipo, sea una persona o una herramienta que genera el changelog.

### Cuándo no usarlo

El comando funciona bien cuando lo que tienes en staging ya es coherente. En algunos casos conviene trabajar a mano. Si en el mismo archivo has cambiado dos features, sepáralas antes con `git add -p` y ejecuta `/commit` para cada una. Si tu equipo usa una convención distinta de Conventional Commits, cambia el comando (es un archivo, se modifica en un minuto) o escribe el commit a mano. Los merge commits, los revert y los cherry-pick tienen su propio contexto: mejor gestionarlos a mano.

### Un día típico

Con `/commit` y `/spawn-pr`, la sesión coge un ritmo regular. Trabajas con Claude en la feature X, que toca cuatro o cinco archivos relacionados; pasas los cambios a staging, ejecutas `/commit`, lees y confirmas. Pasas a la feature Y y repites. Cuando la rama está lista ejecutas `/spawn-pr`: push, pull request con título y descripción, URL en la respuesta. Tres semanas después, `git log --oneline` te pone al día antes incluso de abrir un archivo.

::: {.callout .callout-prompt}
[Prompt reutilizable]{.callout-title}

Cuando tienes un workflow recurrente y no sabes por dónde empezar, pídele a Claude que te escriba el comando:

```text
Crea un comando personalizado en .claude/commands/<nombre>.md para este
escenario recurrente: <describe el workflow que haces a menudo a mano>.

El comando debe:
- Tener un frontmatter con una description clara (máx. 60 caracteres)
- Tener un argument-hint si acepta parámetros
- Estructurar las instrucciones en pasos numerados
- Especificar explícitamente si debe mostrar el diff antes de aplicar
- Indicar si debe esperar confirmación o continuar automáticamente

Muéstrame el archivo completo listo para guardar.
```
:::

## Resumen {.unlisted}

- Un comando personalizado es un archivo `.md` en `~/.claude/commands/` (personal) o en `.claude/commands/` (de proyecto, para subirlo con un commit) que se convierte en `/nombre-archivo`; las subcarpetas añaden un prefijo, como `/frontend:component`.
- Las skills han absorbido los comandos: el formato `.claude/commands/` sigue funcionando, `.claude/skills/<nombre>/SKILL.md` es el recomendado para trabajo nuevo y gana si los nombres coinciden. El capítulo 9 parte de aquí.
- `$ARGUMENTS` recibe todo el texto que sigue al comando, `$0` y `$1` los argumentos individuales; `` !`comando` `` inyecta la salida de la shell antes de que Claude lea el prompt, `@file` adjunta un archivo.
- En los comandos con efectos externos (push, pull request, deploy) pon `disable-model-invocation: true`, y en `allowed-tools` solo los comandos que leen.
- Superpowers se instala con `/plugin install superpowers@claude-plugins-official` seguido de `/reload-plugins`, y trae skills para brainstorming, desarrollo con subagentes y revisión, depuración sistemática y TDD.
- Un `/commit` que trabaja sobre el staging, propone un mensaje Conventional Commits y espera tu confirmación te da un historial de Git que puedes usar con `bisect` y `revert`.

## Ejercicio {.unlisted}

Tiempo estimado: 25 minutos. Necesitas cualquier repositorio Git con algunos cambios pendientes.

1. Instala Superpowers con `/plugin install superpowers@claude-plugins-official`, ejecuta `/reload-plugins` y comprueba con `/skills` que aparecen sus skills.
2. Guarda el comando `/commit` de la sección 8.5 en `~/.claude/commands/commit.md`. Haz un cambio pequeño, pásalo a staging, ejecuta `/commit` y lee el mensaje propuesto antes de confirmar.
3. Busca un prompt que hayas escrito al menos tres veces esta semana, conviértelo en un archivo en `~/.claude/commands/` con `description` y, si hace falta, `argument-hint`; luego ejecuta `/reload-skills` y pruébalo. Si quieres un punto de partida, el prompt de la carpeta `cap-07/` del repositorio `github.com/hidran/claude-code-book-snippets` (numeración de la primera edición) genera un comando personalizado a partir de un escenario.

Has terminado cuando `git log -1` muestra un commit con un mensaje Conventional Commits creado por `/commit` y tu comando nuevo aparece en el menú de `/` con su descripción.
