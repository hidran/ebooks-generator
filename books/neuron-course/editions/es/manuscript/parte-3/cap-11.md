# Capítulo 11 — Teoría de la recuperación

::: {.callout .callout-tip}
[El código de este capítulo]{.callout-title}

Este capítulo es conceptual y no tiene código propio, pero el repositorio complementario [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) contiene versiones ejecutables de todo lo que el libro construye.
:::

## 11.1 El problema que resuelve el RAG

### La brecha

Un modelo de lenguaje sabe lo que había en sus datos de entrenamiento. No conoce la política de devoluciones de tu empresa, tus runbooks internos, el acta del consejo de la semana pasada ni la especificación del producto que publicaste ayer.

Pregúntaselo igualmente y ocurrirá una de dos cosas. Dirá que no lo sabe, lo cual es honesto pero inútil. O producirá algo plausible y equivocado, que es peor que inútil.

### La definición

El RAG es el proceso de proporcionar referencias a una base de conocimiento externa a los datos de entrenamiento del modelo antes de generar una respuesta.

El mecanismo, en su forma más simple:

1. El usuario hace una pregunta.
2. Tu sistema busca en una base de conocimiento pasajes relevantes para esa pregunta.
3. Esos pasajes se añaden al prompt.
4. El modelo responde usándolos.

El modelo no ha aprendido nada. Se le ha entregado la página relevante y se le ha pedido que la lea.

### Por qué esto es rentable

La documentación plantea el argumento económico directamente: el RAG extiende las capacidades de un LLM a un dominio concreto o a la base de conocimiento interna de una organización **sin reentrenar el modelo.**

Esa palabra —reentrenar— es la alternativa, y merece cuantificarse:

| | RAG | Ajuste fino |
|---|---|---|
| Coste de puesta en marcha | Horas | De días a semanas, más cómputo |
| Coste de actualización | Reindexar el documento cambiado | Reentrenar |
| Latencia de actualización | Minutos | Días |
| Puede citar fuentes | Sí | No |
| Funciona con cualquier modelo | Sí | No, queda atado al que ajustaste |
| Gestiona datos que cambian a menudo | Sí | No |

Para «el modelo debería conocer nuestra documentación», el RAG gana en todas las filas. Los casos interesantes en los que gana el ajuste fino tienen que ver con *estilo y formato*, no con conocimiento; la Sección 11.4 lo cubre como es debido.

### El otro uso, fácil de pasar por alto

El RAG suele venderse como acceso a datos privados. Pero el mismo mecanismo suministra información **reciente**: investigación actual, estadísticas de este trimestre, noticias de hoy. La fecha de corte de entrenamiento del modelo es una frontera de conocimiento, y la recuperación la cruza igual que cruza la frontera de tu cortafuegos.

### Para qué no sirve el RAG

Conviene enunciarlo ya, porque la confusión es cara y la Sección 4.5 ya lo preparó:

**No para hechos que tu base de datos conoce.** «¿Cuántos pedidos hizo este cliente?» es SQL. Una búsqueda vectorial sobre prosa te dará una respuesta aproximadamente correcta, que para un recuento es sencillamente incorrecta.

**No para la memoria del usuario.** «Recuerda que soy vegetariano» es memoria a largo plazo, no recuperación de conocimiento.

**No para razonar.** El RAG suministra hechos. No mejora la lógica, la aritmética ni la planificación del modelo.

**No para corpus pequeños.** Si toda tu base de conocimiento son 3.000 tokens, ponla en el prompt de sistema. Sin incrustaciones, sin almacén vectorial, sin pipeline. La infraestructura solo se gana su sitio cuando el corpus supera lo que puedes permitirte enviar cada vez.

Esa última es la más ignorada, y es el equivalente RAG del «si puedes dibujar el diagrama de flujo, construye el diagrama de flujo» de la Sección 1.1.

### Puntos clave

- El RAG le entrega al modelo la página relevante; no le enseña nada.
- Más barato que el ajuste fino en todas las dimensiones que importan para el conocimiento.
- También cruza la frontera de la fecha de corte de entrenamiento, no solo la del cortafuegos.
- No para hechos contables, memoria de usuario, razonamiento ni corpus lo bastante pequeños como para incrustarlos.

## 11.2 Incrustaciones y búsqueda por similitud

### La intuición

Una incrustación es una lista de números que representa el *significado* de un fragmento de texto. Un modelo típico produce 768, 1024 o 1536 números por texto.

La propiedad útil: **los textos con significado similar producen listas de números similares.**

«El gato se sentó en la alfombra» y «Un felino descansaba sobre el tapete» apenas comparten palabras. Sus incrustaciones están cerca. «El gato se sentó en la alfombra» y «Los ingresos trimestrales subieron un 12 %» comparten la palabra «los». Sus incrustaciones están lejos.

La búsqueda por palabras clave ve las palabras. Las incrustaciones ven el significado.

### Búsqueda por similitud

Guarda la incrustación de cada fragmento de tu base de conocimiento. Cuando llegue una pregunta, embébela y encuentra los vectores guardados más cercanos.

Esa operación es para lo que existe un **almacén vectorial**. La interfaz de NeuronAI es exactamente esta:

```php
public function similaritySearch(array $embedding, int $k = 4): iterable;
```

Le das un vector y te devuelve los `k` documentos más cercanos. `k` —cuántos fragmentos recuperar— se suele llamar top-K, y es una de las dos perillas que más afectan a la calidad. La otra es el tamaño de fragmento (Sección 11.3).

### Puntuaciones, no distancias

Un detalle que NeuronAI hace explícito, y que previene un error real:

> `similaritySearch` debería devolver documentos con una **puntuación** de similitud, no una **distancia** de similitud.

Corren en direcciones opuestas. Una distancia de 0 significa idéntico; una puntuación de 1 significa idéntico. Confúndelas y tu lógica de «mejor coincidencia» devolverá silenciosamente los peores resultados.

Cuando una base de datos devuelve distancia, conviértela:

```php
use NeuronAI\RAG\VectorSimilarity;

$document->setScore(
    VectorSimilarity::similarityFromDistance($distance)
);
```

Quien implemente un almacén propio necesita esto. Es también un buen ejemplo de un framework codificando una convención para prevenir una categoría de error.

### Tres cosas que sorprenden

**Las incrustaciones son específicas del modelo.** Los vectores del modelo de OpenAI no pueden compararse con los del modelo de Voyage. Son sistemas de coordenadas distintos. Cambia tu proveedor de incrustaciones y **debes reembeber todo tu corpus.** Trata el modelo de incrustaciones como parte de tu esquema de datos, no como un ajuste intercambiable.

Conviene enunciarlo con firmeza porque es uno de los pocos sitios donde la libertad de cambio de interfaz de la Sección 3.6 no aplica. La interfaz cambia; los datos no la siguen.

**Las dimensiones deben coincidir con el almacén.** Si tu modelo de incrustaciones produce 1536 números y la columna de tu almacén vectorial está declarada como 1024, nada funciona. El esquema de MariaDB de los documentos escribe a fuego `VECTOR(1536)` exactamente por eso.

**Similitud no es relevancia.** Dos fragmentos pueden estar semánticamente cerca y solo uno de ellos responder a la pregunta. Esa es la brecha que la reordenación existe para cerrar (Sección 12.7).

### Coste

Embeber es muchísimo más barato que generar: típicamente una pequeña fracción del precio por token de un modelo de chat. Pero embebes el corpus entero una vez y cada consulta para siempre, así que a escala es una partida real.

**Ollama ejecuta modelos de incrustación en local, gratis.** Para todos los laboratorios de esta parte, y para muchísimos sistemas de producción, un modelo de incrustación local es enteramente adecuado. Dado que la Sección 3.6 ya estableció Ollama, el RAG puede aprenderse de principio a fin a coste cero.

### Puntos clave

- Una incrustación es una representación numérica del significado; los significados similares quedan cerca.
- `similaritySearch($embedding, $k)`: top-K es una de las dos perillas de calidad.
- Devuelve puntuaciones, no distancias; convierte con `VectorSimilarity`.
- Las incrustaciones son específicas del modelo: cambiar de modelo significa reembeberlo todo.
- Los modelos de incrustación locales hacen que aprender RAG sea gratis.

## 11.3 Chunking: la decisión que determina la calidad

Esta es la sección de mayor calado del capítulo.

### Por qué dividir

Dos razones, y ambas importan:

**Precisión de la recuperación.** Si embebes un manual entero de 40 páginas como un solo vector, ese vector representa el significado medio de todo el manual, es decir, casi nada. Una pregunta sobre un párrafo no casará bien con él.

**Presupuesto de contexto.** Recuperas fragmentos para ponerlos en el prompt. Un manual entero no cabe y, aunque cupiera, la aritmética de la Sección 1.4 dice que no querrías pagarlo en cada turno.

Así que: divide el documento en piezas, embebe cada pieza, recupera las que casan.

### El compromiso central

La documentación enuncia el principio con claridad:

> Cuanto más largas sean tus unidades de texto, menos precisa será la representación por incrustaciones.

**Fragmentos pequeños** — incrustaciones precisas, coincidencia exacta, pero cada pieza recuperada puede carecer del contexto necesario para ser útil. Casas la frase exacta y resulta ser incomprensible sin el párrafo que la rodea.

**Fragmentos grandes** — contexto de sobra, pero incrustaciones borrosas y tokens desperdiciados. Recuperas 800 palabras para responder una pregunta que el modelo podría haber respondido con 40.

No hay un valor universalmente correcto. Hay un valor correcto *para tu contenido*, y encontrarlo es empírico.

### Los tres parámetros

**Longitud máxima.** Cuánto puede crecer un fragmento. El divisor por defecto de NeuronAI usa 1.000 caracteres.

**Separador.** Dónde se permite cortar. El valor por defecto es el punto: fronteras de frase. Pero si tus documentos son Markdown con secciones encabezadas, cortar por `\n## ` produce fragmentos alineados con la propia estructura semántica del documento, que casi siempre es mejor que cortar por frases.

Esa es la sugerencia práctica más útil de aquí: **haz coincidir el separador con la estructura de tu contenido**, no aceptes el valor por defecto solo porque está ahí.

**Solapamiento.** Palabras arrastradas del fragmento anterior al siguiente. El valor por defecto es cero.

### Por qué existe el solapamiento

La documentación lo describe como un aumento de la conexión semántica entre secciones adyacentes. En concreto, arregla este fallo:

> Fragmento 1: «…la ventana de reembolso es de 30 días desde la entrega.»
>
> Fragmento 2: «Pasado este periodo, solo hay saldo en tienda disponible.»

El fragmento 2 por sí solo es irresoluble: *¿pasado qué periodo?* Con solapamiento, el fragmento 2 comienza con la cola del fragmento 1 y lleva su propio contexto.

Coste: texto duplicado significa más fragmentos, más llamadas de incrustación, más almacenamiento. Un punto de partida razonable es el 10–15 % del tamaño de fragmento. Cero solo es correcto cuando tus fragmentos son genuinamente independientes: unas preguntas frecuentes donde cada entrada se sostiene sola, un catálogo de productos.

### Chunking consciente de la estructura

El mejor chunking respeta lo que el documento *es*:

| Contenido | Dividir por |
|---|---|
| Documentación en Markdown | Encabezados (`##`) |
| Preguntas frecuentes | Un fragmento por pregunta |
| Código | Fronteras de función o clase |
| Transcripción | Turnos de habla o marcas de tiempo |
| Texto legal | Cláusula o artículo |
| Prosa | Párrafos, y luego frases |

Un divisor propio (Sección 12.3) suele ser veinte líneas y produce una mejora de calidad mayor que cualquier cantidad de afinado de prompts. Este es el código propio con más palanca de un sistema RAG, y conviene decirlo explícitamente: la gente espera que la palanca esté en el prompt, y normalmente no lo está.

### Cómo elegir de verdad

No supongas. Mide, y ya tienes la herramienta del Capítulo 10.

1. Construye un conjunto de datos de 20 preguntas reales con respuestas correctas conocidas.
2. Indexa el corpus con tres configuraciones (por ejemplo 500/1000/2000 caracteres, 0/10/20 % de solapamiento).
3. Ejecuta el evaluador contra cada una, usando `FaithfulnessJudge` y `CorrectnessJudge`.
4. Compara las puntuaciones.

Por eso las evaluaciones venían antes que el RAG en este libro. El chunking es un parámetro empírico, y sin un banco de medición estás afinando por intuición.

### Puntos clave

- Divide por precisión de recuperación y por presupuesto de contexto.
- Fragmentos más largos significan incrustaciones más borrosas: ese es el compromiso central.
- Haz coincidir el separador con la estructura de tu contenido; no aceptes el valor por defecto.
- El solapamiento arregla los fragmentos que solos no significan nada; empieza en el 10–15 %.
- Elige los parámetros por evaluación, no por intuición.

## 11.4 RAG, ajuste fino, relleno de contexto y herramientas

### Las cuatro opciones

**1. Relleno de contexto.** Ponlo todo en el prompt de sistema. Simple, exacto, sin infraestructura. Limitado por la ventana de contexto y pagado en absolutamente cada petición.

**2. RAG.** Recupera los pasajes relevantes en tiempo de consulta. Escala a cualquier tamaño de corpus, admite citación, se actualiza reindexando.

**3. Herramientas.** Deja que el modelo consulte un sistema en vivo. Exacto, actual, estructurado.

**4. Ajuste fino.** Entrena el modelo con tus datos. Caro, lento de actualizar, pero cambia el comportamiento por defecto del modelo.

### La tabla de decisión

| Situación | Mecanismo |
|---|---|
| Menos de ~2.000 tokens de referencia estable | Relleno de contexto |
| Corpus documental grande y no estructurado | RAG |
| Hechos contables o consultables | Herramientas |
| Datos que cambian minuto a minuto | Herramientas |
| Necesita citar un documento fuente | RAG |
| Estilo o formato de salida consistente | Ajuste fino |
| Vocabulario de dominio que el modelo malinterpreta | Ajuste fino |
| «El modelo debería conocer nuestras políticas» | RAG |
| «El modelo debería sonar como nuestra marca» | Ajuste fino |

### La distinción que la gente confunde

**El ajuste fino enseña comportamiento. El RAG suministra hechos.**

Ajustar finamente un modelo con tu documentación es un error común y caro. El modelo aprende la *forma* de tu escritura —el vocabulario, el registro, la estructura— pero no aprende los hechos de forma fiable y, cuando tu documentación cambie, tendrás que rehacerlo todo. Mientras tanto no puedes citar nada, porque no hay nada que citar.

Si alguien dice «queremos que el modelo conozca nuestro producto», quiere RAG. Si dice «queremos que escriba como nuestro equipo de soporte», eso es terreno de ajuste fino, y aun así un buen prompt de sistema con tres ejemplos recorre la mayor parte del camino por una fracción del coste.

### La otra distinción que la gente confunde

**RAG para prosa. Herramientas para registros.**

Este es el punto de la Sección 4.5, y merece repetirse aquí porque es donde se comete el error.

- *«¿Cuál es nuestra política de reembolsos?»* → RAG. Está escrita en un documento.
- *«¿Se ha reembolsado el pedido 4471?»* → Herramienta. Es una fila de una tabla.
- *«¿Qué clientes tuvieron un reembolso el mes pasado?»* → Herramienta. Es una consulta.

Indexar tu tabla de pedidos en un almacén vectorial para responder a la segunda pregunta es un error de diseño que produce respuestas aproximadas dichas con seguridad. La búsqueda vectorial recupera cosas que *se parecen*; no computa.

### Se componen

Los mejores sistemas usan varios. La Sección 12.1 muestra que el framework lo soporta directamente: una clase `RAG` **es** un `Agent`, así que puede tener herramientas.

El ejemplo documentado está bien elegido: un agente de consejos de entrenamiento con una base de conocimiento de información sobre ejercicios (RAG) más una herramienta que lee el estado de entrenamiento actual del usuario desde la base de datos (llamada a herramientas). Prosa de la recuperación, hechos de la herramienta, una sola respuesta.

### Puntos clave

- Cuatro mecanismos: relleno, RAG, herramientas, ajuste fino.
- El ajuste fino cambia el comportamiento; el RAG suministra hechos.
- RAG para prosa, herramientas para registros: la confusión más común y más cara.
- Por debajo de ~2.000 tokens estables, sáltate la infraestructura por completo.
- Los sistemas reales los combinan; el diseño «RAG es un Agent» de NeuronAI lo soporta directamente.

## 11.5 Los límites del RAG ingenuo

### El RAG ingenuo

Embebe la pregunta, recupera el top-K, mételo en el prompt, genera. Funciona sorprendentemente bien, y luego falla de formas concretas y reconocibles. Conocer las seis es la diferencia entre diagnosticar un problema y concluir «la IA no funciona».

### Fallo 1 — La pregunta no se parece a la respuesta

El usuario pregunta *«¿Por qué está roto mi trasto?»*. El documento dice *«El código de error 4021 indica asignación de disco insuficiente en el volumen primario.»*

Semánticamente distantes. La recuperación falla.

**Solución:** transformación de la consulta. Reescribe o expande la pregunta antes de embeberla; NeuronAI incluye `QueryTransformationPreProcessor` justo para esto, y se ejecuta en `PreProcessQueryNode` (Sección 12.7).

### Fallo 2 — Similar no es relevante

Recuperas cinco fragmentos, todos sobre reembolsos. Solo uno cubre la ventana de 30 días que preguntaba el usuario. Los otros cuatro son ruido, y el ruido cuesta tokens y puede distraer al modelo hacia responder desde el pasaje equivocado.

**Solución:** reordenación. Recupera de forma amplia y luego repuntúa con un modelo que lea la consulta y cada documento a la vez. Sección 12.7.

### Fallo 3 — La respuesta abarca varios fragmentos

*«¿Cómo interactúan nuestras políticas de reembolso y de envío para pedidos internacionales?»* Los reembolsos están en un documento, los envíos en otro, la excepción internacional en un tercero. Una recuperación top-K sobre una consulta encuentra uno de ellos.

**Solución:** recuperación multiconsulta, o una K más alta más reordenación. Genuinamente difícil: aquí es donde el RAG ingenuo enseña sus costuras.

### Fallo 4 — Preguntas de agregación

*«¿Cuántos artículos mencionan el RGPD?»* La búsqueda vectorial recupera los documentos *más similares*, no *todos* los que coinciden. No hay operación de recuento.

**Solución:** esta no es una pregunta de RAG. Usa una herramienta, o filtrado por metadatos con búsqueda híbrida. Reconocerlo es la solución.

### Fallo 5 — Alucinación con seguridad

La recuperación no devuelve nada útil, y el modelo responde de todos modos desde su conocimiento general: con fluidez, de forma plausible, y mal.

**Este es el fallo más peligroso**, porque tiene exactamente el aspecto del éxito.

**Solución, en tres partes:**

1. **Instruye explícitamente.** En la sección `background`: *«Responde solo a partir de los documentos proporcionados. Si no contienen la respuesta, dilo.»*
2. **Mídelo.** El `FaithfulnessJudge` de la Sección 10.5 existe precisamente para esto. Es la razón por la que las evaluaciones vinieron primero.
3. **Cita.** Exige que la respuesta referencie el documento fuente. Una cita que el usuario puede comprobar convierte un fallo invisible en uno visible.

### Fallo 6 — Índice desactualizado

Alguien actualiza el documento de política. El almacén vectorial todavía contiene los fragmentos del trimestre pasado. El agente responde con seguridad desde información obsoleta.

**Solución:** reindexación, que NeuronAI aborda con `reindexBySource()` (Sección 12.6). También una cuestión operativa: qué dispara una reindexación y cómo sabes que se ejecutó.

### El resumen honesto

El RAG ingenuo te lleva quizá el 70 % del camino. El 30 % restante es transformación de consultas, reordenación, filtrado por metadatos, búsqueda híbrida y evaluación, que es exactamente por lo que el pipeline de NeuronAI tiene procesadores previos y posteriores como etapas de primera clase y no como un añadido de última hora.

Quien crea que el RAG es «embeber y recuperar» publicará algo que se demuestra maravillosamente y decepciona en la segunda semana. Conocer los seis modos de fallo es lo que te permite reconocer qué estás mirando.

### Puntos clave

- Seis modos de fallo: desajuste de consulta, similar pero irrelevante, respuestas repartidas entre fragmentos, agregación, alucinación, obsolescencia.
- La alucinación con seguridad es la más peligrosa porque se parece al éxito.
- Instruye, mide con `FaithfulnessJudge` y cita.
- El RAG ingenuo es ~70 %; las etapas del pipeline son el resto.
