# Apéndice C. Prompts listos para usar

Este apéndice reúne los prompts reutilizables del libro, ordenados por el trabajo que hay que hacer y no por capítulo. La primera edición tenía aquí cincuenta prompts genéricos. Se han quedado los que los capítulos usan de verdad, en la versión corregida de esta edición, con los nombres del proyecto sustituidos por marcadores entre corchetes: `[ARCHIVO]`, `[OBJETIVO]`, `[STACK]`. Cámbialos por archivos, comandos y criterios de verificación reales de tu proyecto, y quita las líneas que no te sirvan. Cada prompt indica el capítulo en el que se explica: si el resultado no es el que esperabas, vuelve allí antes de reescribirlo.

Los mismos prompts están en texto plano en el repositorio `github.com/hidran/claude-code-book-snippets`, cómodos para copiar y pegar.

## C.1 Conocer un proyecto o un dataset

### Primer contacto con un proyecto

Cuando abres un repositorio que no conoces, antes de pedir ningún cambio (capítulo 1).

```text
Lee los archivos del proyecto y dime:
1. Qué stack tecnológico ves
2. Qué parte parece más reciente y cuál más antigua
3. Qué archivo es el punto de entrada (entry point)
4. Qué NO entiendes a primera vista mirando los nombres de las carpetas
```

### Primer contacto con un dataset

Con cualquier CSV, antes de empezar el análisis de verdad (capítulo 4).

```text
Lee @[ARCHIVO CSV]. Indica:
1. Estructura: número de filas, columnas con nombre y tipo
2. Valores faltantes o anómalos
3. Patrones temporales, si hay columnas de fecha
4. Outliers evidentes en las columnas numéricas

Después dime 3 preguntas de negocio interesantes que se
pueden hacer sobre estos datos: no las respondas todavía,
primero quiero saber si son las correctas.
```

## C.2 Planificar con Plan Mode

Este prompt, igual que las plantillas de la landing page (C.3) y de la feature nueva (C.10), se lanza en Plan Mode: entras con `Shift+Tab` hasta ver `plan mode on`, o con `/plan`. Claude lee y explora, pero no modifica nada hasta que apruebas el plan.

### El plan antes que el código

Para cualquier tarea que vaya más allá de unas pocas líneas (capítulo 3).

```text
Planifica cómo harías [OBJETIVO]. No escribas código. Solo pasos
numerados con: archivos que crear o modificar, motivo de cada cambio,
dependencias entre los pasos, posibles puntos críticos.
```

## C.3 Features y refactoring

### Añadir una feature

La plantilla básica para una petición que Claude tiene que ejecutar sin adivinar (capítulo 3).

```text
Contexto: [qué existe, qué archivo, qué función, por qué existe]

Objetivo: [qué debe cambiar o crearse, de forma medible]

Restricciones:
- No modifiques [archivo/API/comportamiento]
- Sigue el patrón que ya se usa en [archivo de referencia]
- [Otras limitaciones: versión de Node, dependencias, compatibilidad]

Ejemplos: lee [archivo existente] para ver el patrón que hay que seguir

Salida: [primero enséñame el plan / crea el archivo / enséñame solo el diff]
```

### Refactoring guiado

Cuando quieres cambiar la estructura del código sin cambiar su comportamiento (capítulo 3).

```text
Contexto: lee [ruta del archivo]. La función/clase [nombre] hace
[descripción de lo que hace y de por qué existe actualmente].

Objetivo: [qué debe cambiar, de forma medible. Ej.: separar las
responsabilidades en X funciones puras / hacer la clase testeable con
mocks / eliminar la dependencia de [librería]]

Restricciones:
- La firma pública de [función/interfaz] debe quedar idéntica
- No toques [archivo o carpeta relacionada]
- Los tests de [ruta de los tests] deben seguir pasando sin cambios

Ejemplo del patrón objetivo: mira [archivo que ya tiene el estilo que quieres]

Salida: primero enséñame un plan numerado con los pasos y los archivos
afectados. No ejecutes nada hasta que lo apruebe.
```

### Una landing page del brief al deploy

Para un sitio de presentación nuevo, con Superpowers instalado. Con las confirmaciones manuales, cuenta con 60-90 minutos de sesión (capítulo 16).

```text
Quiero construir una landing page para [NOMBRE DEL PRODUCTO].

Descripción del producto:
[2-3 frases que describan el producto y su valor principal]

Audiencia:
[quiénes son los usuarios objetivo]

Call to action principal:
[p. ej. "Empieza gratis", "Reserva una demo", "Descarga la app"]

Secciones que incluir:
- Hero con título, subtítulo, CTA e imagen/vídeo
- Features (4-6 features principales con iconos)
- [sección opcional, p. ej. "How it works" con 3 pasos]
- Social proof (testimonios o logos de clientes)
- Pricing (N planes, con selector mensual/anual si lo hay)
- FAQ (6-8 preguntas más frecuentes)
- Footer con CTA final

Estilo:
[p. ej. "dark mode, acento violeta, tipografía bold, tech forward"
 o bien "light, colores cálidos, friendly, startup de consumo"]

Stack:
React + Vite + Tailwind CSS (última versión)

Deploy target:
Firebase Hosting

Workflow:
1. Usa el visual companion para enseñarme 3 variantes de layout
2. Cuando apruebe el layout, genera las especificaciones en docs/SPEC.md
3. Crea el plan en docs/PLAN.md con tareas atómicas y criterios de done
4. Ejecuta una tarea cada vez y espera mi confirmación
5. Code review después de todos los componentes, antes del deploy
6. Build + firebase deploy --only hosting

Empieza en Plan Mode. No escribas código hasta que se aprueben las specs.
```

## C.4 Depuración

### Un test que falla

Dale a Claude el nombre del test, el error y los archivos que tiene que leer, y quédate tú con la decisión sobre el fix (capítulo 3).

```text
El test "[NOMBRE DEL TEST]" de [ARCHIVO DE TEST]
falla con [ERROR].
Lee el test y la función [FUNCIÓN] de [ARCHIVO]. Encuentra la
causa y propónme un fix, pero no lo apliques hasta que lo haya aprobado.
```

### Un bug intermitente

Para los problemas difíciles, donde hace falta más razonamiento en un solo turno: `ultrathink` vale solo para ese mensaje (capítulo 3).

```text
ultrathink. [DESCRIPCIÓN DEL SÍNTOMA, p. ej. El test de integración de los
pedidos falla una de cada cinco veces, solo en CI]. Lee [ARCHIVOS Y CARPETAS]
y propónme las tres causas más probables, por orden, con la forma de
comprobar cada una.
```

## C.5 Tests

### Una función con sus tests

El criterio de verificación va dentro del prompt: Claude sabe cuándo ha terminado porque se lo has dicho tú (capítulo 3).

```text
Escribe una función [FIRMA DE LA FUNCIÓN] con [TIPOS DE ENTRADA Y SALIDA].
Escribe también los tests para estos casos: [CASOS, p. ej. archivo vacío,
archivo con solo la cabecera, filas con campos ausentes, filas válidas].
Los tests deben pasar con [COMANDO DE LOS TESTS].
```

## C.6 Análisis de datos e informes

### Los patrones que importan

Para pasar de las estadísticas descriptivas a conclusiones útiles para quien decide (capítulo 4).

```text
@[ARCHIVO CSV] mira el CSV. ¿Cuáles son los 3 patrones
más importantes para [QUIÉN LO LEE, p. ej. quien gestiona un SaaS]? Explícamelo en
español sencillo. Usa los números solo cuando sean lo
principal, no como relleno.
```

### Informe Excel con tabla dinámica y fórmulas

Un archivo Excel con formato, con los totales en fórmula y los parámetros por línea de comandos (capítulo 5).

```text
Lee [ARCHIVO CSV]. Escribe un script de Python tools/genera_excel.py que genere
[ARCHIVO XLSX] con:

1. Hoja "Dati": todos los datos del CSV como tabla filtrable (auto_filter),
   encabezado con fondo azul oscuro (#1F4E78) y texto blanco en negrita,
   ancho de columnas ajustado al contenido, freeze en la primera fila,
   zebra striping en las filas pares (#F2F2F2).

2. Hoja "Riepilogo": tabla dinámica con [CAMPO DE FILAS] como filas y
   [CAMPO DE COLUMNAS] como columnas, valores = suma de [MÉTRICA].
   Fila de totales con fórmulas SUM, no valores hardcodeados.

3. Hoja "Grafici": un line chart de [MÉTRICA TEMPORAL] a lo largo del tiempo
   desglosado por [SEGMENTACIÓN], un pie chart de la distribución
   total de [MÉTRICA] por [SEGMENTACIÓN].

Usa openpyxl. Añade argparse con --input, --output, --region (opcional).
Si no se indica --output, usa report_YYYY-MM.xlsx con timestamp automático.
Instala las dependencias y actualiza requirements.txt.
```

### Mini dashboard web

Una webapp Flask con Chart.js sobre cualquier CSV tabular (capítulo 6).

```text
A partir de [ARCHIVO CSV], crea un mini dashboard Flask:
- app.py con las rutas GET / y GET /api/data
- templates/index.html con Chart.js desde CDN y tres canvas:
  [GRÁFICO 1] (tipo: [line|bar|pie]),
  [GRÁFICO 2] (tipo: [line|bar|pie]),
  [GRÁFICO 3] (tipo: [line|bar|pie])
- static/style.css con layout en grid de 2 columnas, fuente Inter,
  tarjetas blancas sobre fondo gris claro, responsive para móvil
- Un botón "Actualizar datos" que vuelve a hacer fetch de /api/data y llama
  a chart.update() sin recargar la página
Arranque: python app.py, servidor en http://localhost:5000
```

## C.7 CLAUDE.md, reglas y memoria

Para el primer borrador de `CLAUDE.md` en un proyecto existente está `/init` (capítulo 7). Los prompts de aquí abajo sirven después.

### Añadir una regla

El atajo `#` ya no existe: se lo pides a Claude, o abres el archivo con `/memory` (capítulo 7).

```text
añade a CLAUDE.md, en la sección [SECCIÓN, p. ej. NUNCA hagas]: [REGLA]
```

### Revisión periódica de CLAUDE.md

Cada dos o tres meses, o después de un refactoring importante (capítulo 7).

```text
Lee el archivo CLAUDE.md de este proyecto y dime:
1. ¿Hay información que duplica lo que ya puedes deducir del código?
2. ¿Hay secciones demasiado largas que se podrían condensar?
3. ¿Falta información importante que ya te ha causado errores
   o que te habría ayudado en esta sesión?
4. ¿El archivo tiene secciones obsoletas respecto al stack actual del proyecto?
5. ¿Hay instrucciones que valen solo para una parte del código y que
   estarían mejor en .claude/rules/ con el campo paths?

Propón una versión revisada de 200 líneas como máximo.
```

## C.8 Skills, comandos personalizados y agentes

### Un comando personalizado para un workflow recurrente

Cuando repites la misma secuencia a mano y no sabes por dónde empezar (capítulo 8).

```text
Crea un comando personalizado en .claude/commands/[NOMBRE].md para este
escenario recurrente: [describe el workflow que haces a menudo a mano].

El comando debe:
- Tener un frontmatter con una description clara (máx. 60 caracteres)
- Tener un argument-hint si acepta parámetros
- Estructurar las instrucciones en pasos numerados
- Especificar explícitamente si debe mostrar el diff antes de aplicar
- Indicar si debe esperar confirmación o continuar automáticamente

Muéstrame el archivo completo listo para guardar.
```

### El boceto de una skill

Para dárselo a Claude directamente, o para aclararte las ideas antes de usar el skill-creator (capítulo 9).

```text
Quiero crear una skill para Claude Code que se llame [NOMBRE-SKILL].

Debe activarse cuando el usuario pida [DESCRIBE EL TRIGGER CON PALABRAS NORMALES].
El workflow tiene estos pasos:
1. [PASO 1]
2. [PASO 2]
3. [PASO 3]

¿Necesita [scripts de Python / references / templates]? [SÍ/NO, especifica]

Crea la estructura de carpetas en .claude/skills/[NOMBRE-SKILL]/ (o en
~/.claude/skills/[NOMBRE-SKILL]/ si la necesito en todos mis proyectos),
escribe SKILL.md con un frontmatter optimizado para la activación automática,
y añade los archivos de apoyo que hagan falta en las subcarpetas adecuadas.
```

### Crear un agente

El asistente de `/agents` ya no existe: describes el agente y Claude escribe el archivo en `.claude/agents/` (capítulo 10).

```text
Quiero un agente para [descripción de la tarea].

Persona: [p. ej. senior TypeScript code reviewer, data scientist SaaS]
Input: [qué recibe el agente, p. ej. un archivo de controlador, un dataset CSV]
Formato del informe: [p. ej. problemas ordenados por gravedad, con archivo:línea]
Tools permitidos: [p. ej. Read, Grep, solo lectura]
Modelo: [sonnet / opus / haiku / inherit]
Alcance: [proyecto / usuario]

Crea el agente en .claude/agents/ (o en ~/.claude/agents/ si es de nivel usuario).
```

## C.9 MCP y contexto

Los permisos, el sandbox, los hooks y los plugins (capítulos 11, 12 y 14) se configuran con archivos y comandos, no con prompts: los capítulos acompañan cada configuración con los prompts de prueba que la verifican. Aquí quedan los dos prompts de la Parte IV que más uso.

### Trabajar en GitHub desde un servidor MCP

Con el servidor remoto de GitHub configurado, sin salir de la sesión (capítulo 13).

```text
lista las últimas 5 issues abiertas del repositorio [USUARIO]/[REPOSITORIO], solo número y título
```

### Compactar sin perder el hilo

`/compact` acepta instrucciones sobre qué conservar en el resumen (capítulos 4, 15 y 19).

```text
/compact Conserva [QUÉ CONSERVAR, p. ej. la estructura del proyecto, las decisiones tomadas y los tests que fallan]
```

## C.10 Especificaciones y Spec Driven Development

### Describir el problema antes que el stack

El primer prompt de un proyecto nuevo dice qué tiene que hacer la aplicación y deja abierta la elección de tecnologías (capítulo 17).

```text
Quiero construir [TIPO DE APLICACIÓN].
Los usuarios tienen que poder:
- [FUNCIONALIDAD 1, con las restricciones que conozcas, p. ej. formatos y tamaños]
- [FUNCIONALIDAD 2]
- [FUNCIONALIDAD 3]

[REQUISITOS GENERALES, p. ej. panel de administración, entornos]

No elijas todavía el stack. Primero dime qué stacks
recomendarías para este tipo de proyecto, con los tradeoffs
de cada uno. Quiero tecnologías estándar y maduras, nada de hype.
```

### El brief técnico

Itéralo dos o tres veces antes de darlo por listo (capítulo 17).

```text
Contexto: estoy construyendo [descripción del proyecto en 2-3 frases].
Stack tecnológico: [lista del stack elegido, con la motivación].

Genera un brief técnico estructurado que incluya:
1. Requisitos funcionales: funcionalidades por rol (visitante / usuario / admin)
   con criterios de aceptación para cada una
2. Requisitos no funcionales: rendimiento, seguridad (autenticación,
   autorización, validaciones), escalabilidad (orden de magnitud
   de los usuarios y de los datos esperados)
3. Restricciones: stack cerrado, hosting objetivo, presupuesto orientativo, plazos
4. Decisiones técnicas clave: estrategia de autenticación (tokens / sesiones),
   subida (vía API / presigned URL), enfoque de la base de datos (migrations /
   ORM / SQL), almacenamiento (local / S3 / otro)
5. Fuera de alcance: qué no construimos en la primera versión, y por qué
6. Cuotas, límites y audit log, si están dentro del alcance

Genera un documento de 3-4 páginas en Markdown.
Después del borrador espera mi revisión antes de seguir
con las especificaciones operativas.
```

### Requisitos, diseño y tareas

De la spec a los tres archivos del Spec Driven Development, con los ID que los conectan (capítulo 18).

```text
Lee SPEC.md[, OTROS DOCUMENTOS DE REFINAMIENTO].

Genera tres archivos en la carpeta docs/:

1. docs/REQUIREMENTS.md, qué construir
   - Visión y qué NO es el producto
   - Personas ([ROLES])
   - User stories por persona, con ID (US-01, US-02, ...)
   - Criterios de aceptación testeables, con ID (AC-F1-1, ...)
   - Restricciones (formatos de archivo, tamaños, naming)
   - Non-functional requirements con números (rendimiento, seguridad, escalabilidad)
   - Out of scope explícito
   Nada de decisiones técnicas, nada de esquemas, nada de código.

2. docs/DESIGN.md, cómo construirlo
   - Stack con versiones exactas
   - Estructura de carpetas de [CARPETAS DEL PROYECTO]
   - Esquema de la base de datos: tablas, columnas, tipos, restricciones, índices, ON DELETE
   - Contratos de la API: verbo, URL, body, forma de la respuesta, status code
   - Interfaces de los servicios ([SERVICIOS]) para la DIP
   - Autenticación, gestión de errores, [OTROS PIPELINES]

3. docs/TASKS.md, la lista de trabajo
   - Tareas atómicas, de 30 minutos como máximo cada una, agrupadas en fases
   - Para cada tarea: ID (T001, ...), estado [ ], owner (backend-dev,
     frontend-dev, code-reviewer), Depends on, Parallel with, Reads
     (secciones que leer), Acceptance (definition of done), Commit
   - Referencias a las secciones de DESIGN.md y a los ID de REQUIREMENTS.md

Usa los ID para la trazabilidad en las dos direcciones: cada criterio de
aceptación tiene que aparecer en al menos una tarea.
```

### Una feature nueva en un proyecto con specs

Cuando requisitos, diseño y tareas ya están consolidados: Claude actualiza los tres documentos antes de tocar el código (capítulo 21).

```text
Tengo un proyecto con docs/REQUIREMENTS.md, docs/DESIGN.md y docs/TASKS.md
ya consolidados. Quiero añadir esta feature: [DESCRIPCIÓN DE LA FEATURE].

Ejecuta estos pasos en orden:

1. Lee los tres archivos para entender el estado actual
2. Propón la sección que hay que añadir a REQUIREMENTS.md
   (requisitos, restricciones y criterios de aceptación explícitos)
3. Propón los cambios en DESIGN.md (esquema, endpoints, componentes)
4. Propón las tareas que hay que añadir a TASKS.md, con dependencias, ID nuevos
   que no choquen con los existentes y criterios de finalización
   verificables
5. Antes de ejecutar ninguna tarea, comprueba si la feature necesita
   una migración de la base de datos y si en el código ya hay algo parecido
   que pueda entrar en conflicto

No empieces la ejecución hasta que haya aprobado los cambios en los tres archivos.
```

## C.11 Ejecución por waves y /goal

### Arrancar una fase

Simple a propósito: el trabajo de verdad ya está escrito en `docs/TASKS.md` (capítulo 19).

```text
Procede con las tareas de la Fase [N] según docs/TASKS.md.
Un commit por tarea, un pull request por fase.
Usa subagentes donde las tareas sean independientes.
```

### Una condición para /goal

El evaluador juzga solo lo que Claude enseña en la conversación: la condición tiene que nombrar comprobaciones que Claude ejecuta delante de ti (capítulo 20).

```text
/goal las tareas de [ID INICIAL] a [ID FINAL] tienen Status [x] en docs/TASKS.md (muéstrame las líneas Status con grep), "[COMANDO DE LOS TESTS]" en la carpeta [CARPETA] termina con código 0 y cada tarea tiene su commit en la rama del worktree (muéstrame git log --oneline)
```

### Cerrar una wave

El prompt fijo de final de oleada (capítulo 21).

```text
Antes de marcar esta wave como completada, comprueba:

1. Para cada tarea marcada [x]: ¿existe en el repositorio el código que
   corresponde a los criterios de aceptación? Quiero la ruta del archivo,
   no "debería existir".
2. Releyendo los requisitos que esta wave dice cubrir,
   ¿hay algo que las tareas no cubren?
3. ¿Existe al menos un test (automático, o manual documentado) que
   ejercite cada flujo de usuario citado en esos requisitos?

Si encuentras huecos, haz una lista. No cierres la wave hasta que la lista esté vacía
o las excepciones estén documentadas explícitamente como fuera de alcance.
```

## C.12 Review y QA

### La review integrada

`/code-review` (alias `/review`) se ejecuta como subagente en segundo plano. Sin objetivo mira los commits sin push más los cambios sin commit; sin nivel reutiliza el último que escribiste (capítulo 22).

```text
/code-review high main...[RAMA]
/code-review [NÚMERO DEL PR]
/code-review --fix main...[RAMA]
/code-review --comment [NÚMERO DEL PR]
/code-review ultra [NOTA PARA LOS REVISORES]
```

### Wave review con cuatro agentes

Al final de una fase, varios revisores especializados en paralelo y un único informe (capítulo 19).

```text
Wave review de la Fase [N], [NOMBRE DE LA FASE] (tareas [ID INICIAL]-[ID FINAL]).
Lanza cuatro subagentes en paralelo, en solo lectura (sin modificar
archivos), modelo sonnet:

1. security-auditor
   Busca: auth bypass, falta de validación de input, exposición de datos
   no autorizada, secretos en el código, CORS demasiado permisivo.

2. performance-reviewer
   Busca: consultas N+1, falta de eager loading, índices de base de datos
   ausentes en las columnas filtradas, operaciones síncronas que deberían ser jobs.

3. api-consistency
   Busca: error envelope no uniforme, status code incorrectos,
   [PATRONES DEL PROYECTO QUE NO SE RESPETAN], naming no uniforme.

4. test-coverage
   Busca: caminos críticos sin tests, edge cases ausentes, tests que
   se saltan la policy, N+1 en los tests, factories incompletas.

Para cada finding: archivo, línea, severidad (CRITICAL / HIGH / MAJOR /
MEDIUM / LOW), fix propuesto. Agrega los cuatro informes en un único
documento, por orden de prioridad.
```

### La checklist de QA antes del deploy

Para partir de una lista sensata en lugar de tirar de memoria (capítulo 22).

```text
Eres un QA engineer senior. Mi proyecto es [describe el stack y el tipo de app].
Genera una checklist previa al deploy estructurada por categoría:
Funcional, Performance, Security, Data Integrity, Observability.
Para cada punto especifica: qué verificar, cómo verificarlo (comando o acción),
criterio de éxito. Formato: tabla Markdown.
```

### Revisión multi-LLM

Para pegarlo idéntico en Claude, Gemini, Codex y Kimi, y después comparar los resultados (capítulo 22).

```text
Actúa como un senior software engineer con más de 10 años de experiencia.
Haz una critical review del siguiente código.

Evalúalo en estos ejes:
1. Buenas prácticas y estándares del lenguaje/framework
2. Principios SOLID y design patterns (SRP, OCP, LSP, ISP, DIP)
3. Seguridad (injection, autenticación, autorización, exposición de datos)
4. Escalabilidad y rendimiento (consultas N+1, uso de memoria, caching)
5. Fiabilidad y gestión de errores (exception handling, rollback)
6. Edge cases no gestionados (input límite, concurrencia, estados intermedios)

Para cada problema:
- Gravedad: Critical / High / Medium / Low
- Archivo y línea (si aplica)
- Descripción concisa del problema
- Fix recomendado con un snippet de código

Salida: lista Markdown ordenada por gravedad descendente.
Nada de relleno: si no encuentras problemas en un área, dilo explícitamente.

[pega aquí el diff de git o los archivos que hay que revisar]
```

## C.13 Deploy

El deploy de la landing page en Firebase ya está dentro de la plantilla de la sección C.3. Para AWS el punto de partida es la plantilla de CloudFormation.

### Una plantilla de CloudFormation

La versión genérica de la plantilla de la Photogallery: adapta nombre, stack, base de datos y región (capítulo 23).

```text
Genera una plantilla CloudFormation en YAML para una aplicación [NOMBRE] con:
- Stack: [backend en Laravel/Node.js/Python] + [frontend en React/Vue/Angular]
- Base de datos: [MariaDB/MySQL/PostgreSQL] gestionada en RDS
- Región de AWS: [eu-west-1/us-east-1/...]
- Deployment target: ECS Fargate para el backend, S3 + CloudFront para el frontend
- Entornos: staging y production mediante Parameters

La plantilla debe incluir:
- VPC con 2 subredes públicas (ALB) y 2 privadas (ECS, RDS) en 2 AZ
- Security groups con least privilege (ECS hacia RDS solo en el puerto de la base de datos)
- IAM execution role para ECS (ECR, Secrets Manager, logs) y task role para la app
- Repositorio ECR para la imagen Docker
- CloudWatch log group para cada contenedor
- Outputs: ALBDnsName, CloudFrontDomainName, EcrRepositoryUri

Salida: infra/cloudformation.yaml. Añade comentarios inline en las secciones
que no son obvias (p. ej. por qué ese DependsOn, por qué esa policy de IAM).
```
