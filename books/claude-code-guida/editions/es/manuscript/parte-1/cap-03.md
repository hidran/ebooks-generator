# Capítulo 3. Los primeros prompts útiles

::: {.chapter-goals}
[Qué aprenderás]{.callout-title}

Cómo escribir un prompt que Claude Code lleve a término sin sorpresas: qué poner en él, qué errores salen más caros en un proyecto real, tres patrones para usar a diario y cómo revisar el trabajo en Plan Mode antes de que toque los archivos. Al final también verás cómo ajustar cuánto razona el modelo, con el effort y `ultrathink`.

[Requisitos previos]{.callout-title}

Claude Code instalado y funcionando (capítulo 1). El capítulo 2, sobre el bucle agéntico, explica por qué funcionan los consejos que siguen.

:::

Los comandos de Claude Code se aprenden rápido: en una tarde ya manejas los slash commands y los atajos que de verdad hacen falta. Escribir prompts que lleguen al resultado correcto a la primera exige más práctica, y la diferencia entre una sesión productiva y una frustrante casi siempre está ahí.

En el capítulo 2 viste cómo trabaja un agente: reúne contexto, actúa, comprueba el resultado y repite hasta que el trabajo está terminado o hasta que te necesita. Visto desde ahí, un buen prompt hace dos cosas. Le da al bucle un objetivo claro, para que Claude sepa adónde va, y le da una forma de comprobarlo, para que sepa cuándo ha llegado. Casi todo el capítulo es una variación sobre estos dos puntos.

Aquí no hay prompt engineering genérico ni trucos para que un chatbot responda mejor. Las técnicas sirven cuando el modelo escribe código en tu proyecto, dentro de un repo con sus propias convenciones y su propia historia. Claude Code lee los archivos y ejecuta comandos por su cuenta, así que no tienes que llevarle el código a la conversación. Por el mismo motivo, un prompt vago sale más caro que en un chat: Claude rellena los huecos con lo que encuentra en el repo, y puede rellenarlos de una forma distinta a la que tenías en mente.

## 3.1 Qué hace útil un prompt para Claude Code

Hay tres características de Claude Code que cambian la forma de escribir un prompt respecto a un chat.

### Tres diferencias respecto a un chat

La primera: lee los archivos por su cuenta. No hace falta pegar código. Escribes "lee `src/services/userService.ts`" y Claude abre el archivo, con el texto exacto. También puedes escribir `@` seguido de la ruta, con el autocompletado para ayudarte a encontrarla. Pegar cien líneas cuando podrías señalar el archivo hace el prompt más largo y más ruidoso, y basta un error al copiar para que Claude se desvíe.

La segunda: ejecuta comandos, así que puede comprobar tus suposiciones en lugar de darlas por buenas. "Antes de modificar el router, lee todos los archivos de `routes/` y dime cuántas rutas hay y cómo validan los parámetros." Claude lista la carpeta, abre los archivos y responde con lo que ha encontrado. El prompt se convierte en una investigación previa, y el cambio de verdad arranca de datos reales.

La tercera: antes de actuar, Claude se arma un plan, aunque no te lo enseñe. Ese plan es tan bueno como la información que le das. Un prompt con objetivo, restricciones y ejemplos produce un plan que puedes revisar antes de que se escriba una sola línea de código; en la sección 3.5 verás cómo hacerlo explícito con Plan Mode.

### El contexto que Claude ya tiene

Al arrancar, Claude Code carga el `CLAUDE.md` del proyecto, el archivo de instrucciones que verás en el capítulo 7. Si ahí has escrito el stack, los comandos de build y de test y las convenciones del equipo, no tienes que repetirlos en cada prompt. Todo lo demás Claude no lo conoce de antemano: no explora el repo antes de que escribas, lo lee cuando lo necesita. Por eso el prompt se centra en lo específico de esta petición e indica dónde mirar cuando el punto de partida no es obvio.

### Prompt vago y prompt útil, tres ejemplos

El primer caso es un refactoring. El prompt vago:

```text
Haz esto mejor.
```

El útil:

```text
Lee src/utils/csvParser.ts. La función parseCsv mezcla la lectura del
archivo, el parsing y la validación en un único bloque de 80 líneas.
Sepárala en tres funciones (readFile, parseRaw, validateRows), con el
parsing y la validación como funciones puras, sin cambiar el
comportamiento externo: la firma pública debe quedar idéntica y los
tests existentes deben seguir pasando.
```

Con el primero Claude hará algo, pero no sabes qué: puede renombrar variables, añadir comentarios o reescribir la lógica. Con el segundo sabe qué hacer y dónde parar, y ya tiene la comprobación a mano: los tests existentes.

El segundo caso es un bug. El prompt vago es "Arregla este bug." El útil:

```text
El test "rechaza el login con contraseña incorrecta" de tests/auth.test.ts
falla con TypeError: Cannot read properties of null (reading 'id').
Lee el test y la función loginUser de src/auth/service.ts. Encuentra la
causa y propónme un fix, pero no lo apliques hasta que lo haya aprobado.
```

El primero no dice qué bug, dónde ni en qué condición aparece. El segundo da las coordenadas: el test, el mensaje de error, los dos archivos que hay que leer. Y pide parar antes de tocar el código. Ten en cuenta que, con auto mode activo, esa petición es una instrucción que Claude sigue, no un bloqueo: si quieres la garantía, usa Plan Mode (sección 3.5).

El tercer caso es una feature nueva. El prompt vago es "Añade la paginación." El útil:

```text
Añade paginación del lado del servidor a los endpoints GET /api/users y
GET /api/products. Parámetros: limit (por defecto 20, máximo 100) y
offset (por defecto 0). La respuesta debe tener la forma
{ data: [], total: number, limit: number, offset: number }.
Mira cómo están escritos los controladores en src/controllers/ y sigue
las mismas convenciones. Actualiza también las páginas React
src/pages/UsersPage.tsx y src/pages/ProductsPage.tsx. Escribe los tests
de los nuevos comportamientos.
```

El segundo prompt es más largo, pero lo que cuenta es la precisión: parámetros, formato de la respuesta, dónde encontrar las convenciones, qué archivos actualizar, qué probar. Claude no tiene que inventarse ninguna de estas decisiones, porque ya las has tomado tú.

<!-- TODO screenshot: la vecchia fig-01 (Claude Code appena avviato con `! ls -al`) è stata rimossa perché banner e barra di stato mostrano Sonnet 4.6. Se serve un'immagine qui: sessione appena avviata con Opus 5.5 nel banner e un prompt che usa `@` per indicare un file. -->

## 3.2 La anatomía de un prompt que funciona

De los ejemplos sale un esquema. Los prompts que funcionan con Claude Code contienen casi siempre cinco elementos. No hacen falta todos cada vez, pero cada uno que añades elimina una suposición que Claude haría por su cuenta.

El contexto es la situación actual: qué existe, dónde está, por qué está ahí. No tienes que explicar el proyecto, basta con orientar a Claude sobre la parte que te interesa. "La función `calculateDiscount` de `src/pricing/engine.ts` aplica los descuentos a los pedidos B2B" es suficiente; el resto Claude lo lee del archivo.

El objetivo es qué tiene que cambiar después de la intervención, dicho de forma que se pueda comprobar. No "mejóralo", sino "sepárala en tres funciones". No "arréglalo", sino "el test `test_discount_negative` tiene que pasar". Esta parte es la que permite a Claude, y después a ti, saber si el trabajo está terminado.

Las restricciones dicen qué no debe cambiar. Es el elemento que más se olvida, y su ausencia está detrás de buena parte de los errores de la próxima sección: "no toques la API pública", "mantén la compatibilidad con Node 18", "nada de dependencias nuevas", "sigue el patrón que ya se usa en `userService.ts`".

Los ejemplos son archivos ya escritos como tú quieres. "Mira cómo está estructurado `src/services/userService.ts` y sigue el mismo patrón" vale más que un párrafo de explicaciones: Claude lee el archivo y saca de él las convenciones que nadie ha puesto nunca por escrito, desde los nombres de las funciones hasta el manejo de errores.

La salida deseada es la forma del resultado: "enséñame solo el diff", "crea el archivo completo", "primero un plan numerado, sin ejecutar nada", "lista los archivos que tocarías". Así Claude sabe si tiene que actuar enseguida o esperarte, y tú sabes qué te va a llegar.

::: {.callout .callout-prompt}
[Prompt reutilizable]{.callout-title}

Plantilla para añadir una feature:

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
:::

La plantilla es un punto de partida. Para una tarea pequeña bastan dos líneas; para una grande, cada elemento que falte debería faltar por una razón concreta.

### Qué longitud debe tener un prompt

La que haga falta para eliminar la ambigüedad, y no más. Tres líneas precisas valen más que veinte llenas de repeticiones y de alguna contradicción. Una prueba práctica: relee el prompt y pregúntate si, sin saber nada del proyecto, tendrías todo lo necesario para hacer la tarea. Si la respuesta es sí, es lo bastante largo.

## 3.3 Cinco errores de prompting que conviene evitar

Son los errores que se pagan en un proyecto real, con historia, dependencias y partes que no se pueden tocar. En una carpeta de pruebas vacía ni los notas. Cada uno tiene una corrección sencilla.

### Error 1: pedir sin dar contexto

Escribes "añade logging a las funciones principales" y nada más. Claude no sabe qué librería de logging usas, así que elige una. No sabe qué funciones consideras principales, y también las elige. El código que obtienes funciona, pero no encaja con tu proyecto: usa winston donde tú usas pino, escribe JSON donde el equipo lee texto plano, toca las funciones equivocadas.

La corrección es señalar el contexto que ya existe: "Lee `src/logger.ts` para ver la librería y el formato que usamos, y `src/api/` para las funciones que me interesan." Si es información que necesitas a menudo, escríbela una vez en el `CLAUDE.md` (capítulo 7) y deja de repetirla.

### Error 2: un solo prompt para cinco tareas

Lo metes todo en una petición: "Refactoriza la clase User, añade los tests unitarios, actualiza la documentación, corrige el bug de la validación del email y prepara un commit con un mensaje convencional." Claude arranca, pero es fácil que una de las cinco cosas se quede atrás o que dos objetivos se pisen. El refactoring, por ejemplo, rompe los tests que apuntan a la implementación actual, y Claude tiene que decidir por su cuenta cuál de los dos tiene razón.

Divídelo en prompts sucesivos. Primero el refactoring, y lo revisas. Después los tests, y los revisas. Luego el bug y, por último, el commit. Cada prompt tiene un único objetivo y un resultado que compruebas antes de pasar al siguiente. Escribir cuatro prompts en vez de uno te cuesta unos minutos; arreglar un error que se ha propagado por tres cambios cuesta muchos más.

### Error 3: no decir qué no tocar

Pides "arreglar el controlador de pedidos". Claude lee el archivo, ve funciones escritas con estilos distintos y decide unificarlas. De paso cambia también partes que funcionaban, que tus compañeros conocen de memoria y de las que una integración externa espera un formato concreto.

Añade siempre las restricciones: "no cambies la firma pública de las funciones", "no toques `src/legacy/`", "el formato de la respuesta se queda como está, hay clientes en producción que lo leen". Son dos líneas, y separan un refactoring controlado de un cambio que descubres cuando un cliente deja de funcionar.

### Error 4: saltarse el plan en las tareas complejas

Tienes que añadir login con OAuth a una app que no lo tiene. Escribes el prompt y dejas trabajar a Claude, que crea archivos, modifica otros y añade dependencias. A mitad de camino aparece un conflicto entre el nuevo sistema de sesiones y el middleware existente, y para entonces ya hay diez archivos modificados.

Para trabajos así, empieza en Plan Mode. Claude explora el código y escribe un plan sin modificar nada: ves los pasos, los archivos implicados, los posibles conflictos. Haces preguntas, pides cambios y apruebas solo cuando el plan te convence. La sección 3.5 explica cómo.

### Error 5: no leer el diff

Claude ha terminado, echas un vistazo rápido, parece que está bien y sigues adelante. Tres horas después, durante los tests de integración, descubres que también ha modificado una función de utilidad compartida para adaptarla al nuevo caso, y ha cambiado un comportamiento intencionado que nadie había documentado.

En auto mode, el modo con el que arrancan las sesiones interactivas (capítulo 2), Claude no te pide confirmación para cada cambio en los archivos: cuando te dice que ha terminado, los cambios ya están en disco y el diff lo lees después, con `git diff`, antes de hacer commit. En el modo Manual, en cambio, cada cambio te llega como un diff que tienes que aprobar. En los dos casos, la revisión es la que harías en el pull request de un compañero: primero los archivos nuevos, que son menos arriesgados, y después los cambios en archivos existentes, con más atención a las funciones e interfaces que usan otros módulos. Si algo no cuadra, `/rewind` (o `Esc` dos veces con el prompt vacío) devuelve el código a un checkpoint anterior.

::: {.callout .callout-warning}
[Atención]{.callout-title}

La vez que te saltas el diff porque confías es casi siempre la vez en que Claude ha tocado un archivo que no esperabas. Leer el diff forma parte de la revisión de código normal, igual que con el código escrito por cualquier otra persona. Los archivos nuevos se revisan rápido; los cambios en código que ya está en producción merecen toda tu atención.
:::

## 3.4 Patrones recurrentes: plan, ejemplos, verificación

Además del esquema y de los errores, hay tres hábitos que valen para casi cualquier tarea, sea del tipo que sea. Completan los cinco elementos de la sección 3.2.

### Pide el plan antes que el código

Para cualquier tarea que vaya más allá de unas pocas líneas, el primer prompt pide un plan, no código:

```text
Planifica cómo harías [objetivo]. No escribas código. Solo pasos
numerados con: archivos que crear o modificar, motivo de cada cambio,
dependencias entre los pasos, posibles puntos críticos.
```

Sacas dos cosas. Puedes corregir el plan antes de que Claude toque los archivos, y arreglar diez líneas de plan cuesta mucho menos que rehacer cincuenta líneas de código. Y el plan queda como documento: se lo enseñas a un compañero, lo pegas en un ticket, escribes a partir de él el mensaje del commit.

Una vez leído el plan, respondes de una de tres maneras. "Está bien, adelante", y Claude lo ejecuta. "Cambia el paso 3 así: ...", y Claude actualiza el plan y espera. "El paso 2 no puede tocar ese archivo, propón una alternativa", y Claude busca otro camino. Plan Mode (sección 3.5) hace lo mismo con una garantía más: mientras no apruebes, los archivos no cambian.

### Enseña un ejemplo

Las instrucciones de estilo escritas con palabras se quedan en algo vago. "Usa inyección de dependencias" se puede hacer de muchas maneras, y "sigue las convenciones del proyecto" no dice nada si Claude no sabe cuáles son. Funciona mejor un ejemplo:

```text
Lee src/services/userService.ts. Crea src/services/productService.ts
con el mismo patrón: inyección de dependencias en el constructor,
métodos públicos que validan la entrada con Zod antes de llamar a la
base de datos, errores gestionados con las clases personalizadas de
src/errors/.
```

Claude lee `userService.ts`, saca de él la estructura de la clase, los nombres y la forma de tratar tipos y errores, y lo aplica todo al nuevo archivo. Obtienes un archivo que se parece al resto del proyecto, en lugar de uno correcto pero escrito con un enfoque distinto al de todos los demás. El patrón vale para tests, componentes React, controladores REST, consultas SQL y configuraciones de Terraform: cuando quieras algo nuevo al estilo de algo que ya existe, señala el archivo que mejor muestra ese estilo.

### Define cómo se comprueba

Un prompt que dice qué hacer está bien. Uno que además dice cómo comprobar que está bien hecho cierra el bucle agéntico, porque Claude tiene un criterio para saber si ha terminado.

Sin criterio: "Escribe una función que lea el CSV." Con criterio:

```text
Escribe una función parseCsv(path: string): Promise<Row[]> con
Row = { date: Date, amount: number, currency: string }. Escribe también
los tests para estos casos: archivo vacío, archivo con solo la cabecera,
filas con campos ausentes, filas con fechas en formato incorrecto, filas
válidas. Los tests deben pasar con pnpm test.
```

En la segunda versión el criterio es medible: `pnpm test` pasa o no pasa. Claude ejecuta los tests, ve qué falla y vuelve sobre ello hasta que salen en verde, que es justo el paso de verificación del bucle. Tú también lo compruebas sin leer cada línea, porque te basta con ejecutar los tests. Los criterios que mejor funcionan son de este tipo:

- tests concretos que tienen que pasar;
- comandos que deben dar un resultado determinado, como `pnpm build` sin errores o un `curl` al endpoint que responde 200;
- umbrales medibles, como ningún warning de TypeScript o una cobertura de tests de al menos el 80%.

En el capítulo 20 encontrarás `/goal`, que lleva esta idea hasta el final: Claude sigue trabajando, turno tras turno, hasta que un evaluador independiente da por cumplida una condición como "`npm test` sale con código 0".

Los tres patrones se combinan bien en el mismo prompt. Para un refactoring puedes juntarlos así:

::: {.callout .callout-prompt}
[Prompt reutilizable]{.callout-title}

Refactoring guiado:

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
:::

Sustituye las partes entre corchetes por tu caso. La plantilla sirve para cualquier refactoring, desde separar dos responsabilidades hasta reescribir un módulo entero.

## 3.5 Plan Mode: el prompt más importante de todos

Plan Mode merece una sección propia. Se activa en un segundo y, en las tareas complejas, influye en el resultado más que cualquier otro recurso de este capítulo.

### Qué es Plan Mode

Plan Mode es uno de los modos de permisos de Claude Code, que verás todos en el capítulo 11. En este modo Claude lee los archivos y ejecuta comandos para explorar el proyecto, pero no modifica el código hasta que apruebes. Al final te presenta un plan. La parte de investigación se la encarga al subagente Plan integrado, que trabaja en solo lectura con un contexto propio.

La diferencia con escribir "no escribas código" en el prompt está en quién hace cumplir la regla. La frase en el prompt es una instrucción que el modelo sigue casi siempre. Plan Mode es un límite que aplica el harness, el programa que rodea al modelo: los cambios en los archivos no arrancan hasta que dices que sí.

La exploración también depende del modo de partida. Si auto mode está disponible, los comandos que se ejecutan durante la planificación los evalúa el clasificador, y no te llega una petición de confirmación para cada `ls` o `grep`. Si no, los comandos que no son de solo lectura te piden permiso.

### Cómo se entra

Tienes cuatro caminos:

- `Shift+Tab` va pasando de un modo a otro en ciclo (en algunas configuraciones de Windows la tecla es `Alt+M`). Partiendo de auto mode, la primera pulsación lleva a Manual, la segunda a Accept edits y la tercera a Plan. La barra de estado muestra `⏸ plan mode on`.
- `/plan` desde el prompt entra en Plan Mode. Si añades una descripción, por ejemplo `/plan añade la paginación a los endpoints de usuarios`, Claude empieza a planificar enseguida.
- `claude --permission-mode plan` arranca la sesión ya en Plan Mode.
- En `settings.json`, `"permissions": {"defaultMode": "plan"}` lo convierte en el modo de partida. En VS Code el ajuste equivalente es `claudeCode.initialPermissionMode: "plan"`.

### Cuándo usarlo

Casi siempre, salvo para correcciones pequeñas y obvias. Si añades un parámetro a una función que conoces bien, puedes prescindir de él. Úsalo, en cambio, cuando:

- añades una feature que toca más de tres archivos;
- modificas una interfaz pública que se usa en varios sitios;
- introduces una dependencia nueva;
- cambias el flujo de autenticación o de autorización;
- trabajas sobre código que no conoces.

En estos casos el plan te evita deshacer cambios en diez archivos porque a mitad de camino ha surgido un conflicto que habrías visto enseguida.

### Qué te devuelve

Un plan útil contiene:

1. los pasos numerados, en el orden en que se van a ejecutar;
2. para cada paso, los archivos que hay que crear o modificar y el motivo;
3. las dependencias entre los pasos (el paso 3 usa lo que produce el paso 1);
4. los puntos críticos y las preguntas abiertas, por ejemplo "no encuentro la configuración de la base de datos, ¿dónde está?".

Si falta alguna de estas partes, pídela antes de aprobar.

### Aprobar, corregir, volver a empezar

Cuando el plan está listo, Claude Code te pregunta cómo seguir. Hay tres opciones, con el texto en inglés de la interfaz:

- `Yes, and use auto mode`: apruebas y sales de Plan Mode en auto mode. Si auto mode no está disponible, en su lugar aparece `Yes, auto-accept edits`.
- `Yes, manually approve edits`: apruebas, pero cada cambio en los archivos te llega para que lo confirmes.
- `No, keep planning`: te quedas en Plan Mode y escribes qué cambiar, por ejemplo "El paso 2 no puede modificar `authMiddleware.ts`, lo usan otros equipos. Propón un enfoque que no lo toque." Claude rehace el plan.

Con `Ctrl+G` abres el plan en tu editor y lo corriges a mano antes de aprobarlo. Compensa cuando las correcciones son muchas o afectan a detalles que tardarías menos en escribir que en explicar.

<!-- TODO screenshot: piano completato in Plan Mode con il menu di approvazione (Yes, and use auto mode / Yes, manually approve edits / No, keep planning), Opus 5.5 nella barra di stato. -->

La primera opción conviene entenderla bien. Con auto mode como modo predeterminado, aprobar con `Yes, and use auto mode` significa que Claude ejecuta todo el plan sin pedirte confirmación para cada cambio. El clasificador sigue bloqueando las acciones arriesgadas, como un force push, un borrado irreversible o un deploy a producción, pero los cambios en los archivos pasan. Por eso el plan se convierte en tu punto de revisión: léelo como leerías un PR, porque después de aprobarlo la siguiente ocasión de mirar el trabajo es el diff final. Si prefieres ver cada cambio mientras ocurre, elige `Yes, manually approve edits`.

A veces el plan te revela que la petición estaba mal planteada. Si para conseguir el resultado hacen falta treinta archivos, elige seguir planificando y reformula: "Así tocas treinta archivos. Busca un enfoque que consiga el mismo resultado modificando menos de cinco." Mientras trabajas sobre el plan, cada corrección cuesta un mensaje.

### Un ejemplo completo

Con Plan Mode activo:

```text
Planifica cómo añadir un endpoint POST /api/orders al backend NestJS.

Especificaciones:
- validar el body con un DTO y class-validator (orderId, items[], total)
- guardar en Postgres con Prisma (tabla orders, relación con users)
- responder 201 con el pedido creado
- gestionar los errores: 400 para un body no válido, 404 si el usuario
  no existe, 500 para errores de la base de datos

No escribas código. Solo pasos numerados con:
- archivos que crear (nombre y tipo)
- archivos que modificar (nombre y qué cambia)
- tests que escribir (qué deben cubrir)
- dependencias que instalar, si hacen falta
```

En Plan Mode la línea "No escribas código" sobra, pero la dejo porque así el prompt funciona aunque lo pegues en una sesión que esté en otro modo. El plan que obtienes se lee en un par de minutos y, cuando lo apruebas, sabes qué va a pasar en el proyecto. En el capítulo 4 usarás el mismo flujo en un caso real, el análisis de un CSV.

### Cuánto razona Claude: effort y ultrathink

Cuánto razonamiento pone el modelo en una tarea lo decide el effort. Los niveles son `low`, `medium`, `high`, `xhigh` y `max`. En Opus 5.5, el modelo predeterminado, el effort inicial es `medium`. Lo cambias con `/effort`, que abre un selector, o con las flechas izquierda y derecha dentro de `/model`. El nivel activo se ve en el logo y en el spinner; `max` solo vale para la sesión actual.

`medium` va bien para las preguntas rápidas y los cambios pequeños. Para un trabajo de diseño, un bug difícil o la redacción de una especificación, sube a `high` antes de pedir el plan: consumes más tokens, pero el plan está más razonado. En los modelos 5.5 el razonamiento no se puede desactivar; el modelo decide por su cuenta cuánto pensar dentro del nivel que has elegido. Si quieres contener los costes, el alias `opusplan` usa Opus mientras planificas y Sonnet cuando ejecutas (`/model opusplan`).

Si necesitas más razonamiento para un solo prompt, escribe `ultrathink` en cualquier parte del mensaje. Claude Code añade una instrucción a ese turno y el modelo razona más a fondo, mientras el effort de la sesión se queda como estaba. Otras fórmulas como "think hard" o "piénsalo bien" no son palabras clave: el modelo las lee como texto normal del prompt.

```text
ultrathink. El test de integración de los pedidos falla una de cada
cinco veces, solo en CI. Lee tests/orders.e2e-spec.ts y src/orders/ y
propónme las tres causas más probables, por orden, con la forma de
comprobar cada una.
```

## Resumen {.unlisted}

- Un prompt útil le da al bucle agéntico un objetivo comprobable y una forma de verificarlo; el contexto, las restricciones, los ejemplos y el formato de la salida eliminan el resto de las suposiciones.
- Señala los archivos en lugar de pegarlos, y escribe en el `CLAUDE.md` lo que de otro modo repetirías en cada sesión.
- Una tarea por prompt, con restricciones explícitas sobre lo que no hay que tocar.
- Para las tareas complejas entra en Plan Mode (`Shift+Tab`, `/plan` o `claude --permission-mode plan`) y revisa el plan antes de aprobar: con `Yes, and use auto mode` es el último control antes del diff final, que lees igualmente antes de hacer commit.
- Sube el effort a `high` para diseño y bugs difíciles; `ultrathink` vale para un solo prompt, y "think hard" no hace nada especial.

## Ejercicio {.unlisted}

Necesitas una mini codebase en la que equivocarte sin hacer daño. Pídesela a Claude en una carpeta nueva:

```bash
mkdir -p ~/projects/prompts-lab && cd ~/projects/prompts-lab
git init
claude
```

```text
Crea un pequeño proyecto Node.js con tres archivos: src/csv-parser.js, un
parser CSV mínimo; src/products-controller.js, un controlador REST con
Express y las rutas GET /products y GET /products/:id sobre un array en
memoria; tests/parser.test.js, con dos tests que pasan y tres tests
vacíos con un comentario TODO. Añade un package.json con el script npm
test que use node --test. No escribas nada más.
```

Cuando los archivos estén creados, sal, ejecuta `npm install` y haz commit de todo (`git add -A && git commit -m "punto di partenza"`), para que cada diff posterior parta de ahí. Para la versión precisa del paso 1 puedes partir de la plantilla de refactoring guiado de la carpeta `cap-02/` del repositorio `github.com/hidran/claude-code-book-snippets`, que sigue la numeración de la primera edición. El ejercicio lleva unos 15 minutos.

1. Pide que mejore el parser con un prompt vago ("hazlo mejor") y mira qué hace Claude; después lee el resultado con `git diff`. Deshazlo con `/rewind`, escribe la versión con los cinco elementos de la sección 3.2 y compara los dos diffs.
2. Entra en Plan Mode y pide el plan para un endpoint de búsqueda en el controlador. Elige `No, keep planning` y pide un cambio, por ejemplo "el paso 3 tiene que usar query parameters, no el body". Aprueba la versión revisada.
3. Pide que complete los tests a medio escribir, con la condición explícita de que pasen con `npm test`.

Has terminado cuando `npm test` sale con código 0, el plan del endpoint se ha corregido al menos una vez antes de aprobarlo y has guardado los dos prompts del primer paso, el vago y el preciso, para compararlos cuando vuelvas a leer este capítulo.
