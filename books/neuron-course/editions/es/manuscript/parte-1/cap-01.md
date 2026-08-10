# Capítulo 1 — Qué significa realmente «agéntico»

## 1.1 LLM, chatbot, workflow, agente: la escalera de autonomía

En 2023 todo era un «chatbot». En 2025 todo es un «agente». La palabra se ha estirado tanto que ahora significa «software que llama a un LLM», lo cual es inútil como categoría de diseño. Antes de escribir una línea de PHP necesitamos una definición lo bastante afilada como para tomar decisiones arquitectónicas con ella.

La distinción útil no es *qué hace el software*. Es **quién decide qué pasa a continuación**.

Esa pregunta produce una escalera de cuatro peldaños y, al terminar esta sección, deberías poder situar en ella cualquier funcionalidad de IA que te pidan construir, y explicarle a un cliente por qué el peldaño importa más que el modelo.

### Los cuatro peldaños

**Peldaño 1 — La llamada desnuda al LLM.**
Envías texto y recibes texto. Tu código lo decide todo: qué enviar, cuándo enviarlo, qué hacer con la respuesta. El modelo no tiene ningún control sobre el flujo del programa.

```
Tu código → prompt → modelo → texto → tu código
```

Ejemplo: «resume este ticket de soporte en una frase». Hay una entrada, una salida, un camino. El noventa por ciento de las funcionalidades de IA que se publican en productos reales son esto, y está bien que así sea.

**Peldaño 2 — El chatbot.**
Igual que el peldaño 1, más el estado de la conversación. El modelo sigue sin poder hacer nada salvo producir texto, pero ahora ese texto depende de un historial creciente. El flujo sigue estando controlado por completo por tu código: recibir mensaje, añadir al historial, llamar al modelo, devolver la respuesta.

El único problema de ingeniería nuevo es la gestión de la memoria: qué conservas, qué descartas, qué pasa cuando el historial supera la context window del modelo.

**Peldaño 3 — El workflow de IA.**
Defines una secuencia fija de pasos y el modelo rellena algunos de ellos. Extraer entidades → buscarlas en la base de datos → generar una respuesta → clasificar el sentimiento. *El grafo lo escribes tú*; el modelo es un componente dentro de él, no el conductor.

Aquí vive gran parte del valor de producción, y está profundamente infravalorado porque no resulta vistoso. Un pipeline determinista de cinco nodos con tres llamadas al LLM es más fiable, más barato y más fácil de depurar que un agente autónomo, y resuelve la mayoría de los problemas de negocio.

**Peldaño 4 — El agente.**
Aquí está la línea divisoria real: **el modelo decide qué acción tomar a continuación, y el bucle continúa hasta que el modelo decide que ha terminado.**

Le das al modelo un objetivo y un conjunto de capacidades (tools). Tú no escribes la secuencia. El modelo elige la tool A, ve el resultado, decide que ahora necesita la tool C, ve ese resultado, decide que ya tiene bastante y escribe la respuesta final. El flujo de control es emergente, no escrito.

```
Objetivo → modelo → "llamar tool A" → ejecutar → resultado → modelo
         → "llamar tool C" → ejecutar → resultado → modelo → respuesta final
```

Ese bucle es toda la idea. Todo lo demás en este libro —memoria, RAG, workflows, aprobación humana, observabilidad— existe para que ese bucle sea sobrevivible en producción.

### Por qué el peldaño importa más que el modelo

Dos equipos construyen la misma funcionalidad. El equipo A usa una llamada de peldaño 1 con un modelo de frontera. El equipo B usa un agente de peldaño 4 con un modelo de gama media.

El equipo A puede testear su funcionalidad, sabe exactamente cuánto cuesta cada llamada y, cuando se comporta mal, lee un prompt.

El equipo B no puede predecir el coste por petición —el agente podría llamar a seis tools o a una—, no puede testear el flujo de forma determinista y, cuando se comporta mal, necesita un visor de traces para averiguar por qué el modelo eligió la tool equivocada en el paso cuatro.

El equipo B tiene más poder. También tiene un problema operativo mucho más duro. Elegir el peldaño 4 es un compromiso con la observabilidad, los guardrails y la evaluación. Elígelo deliberadamente.

::: {.callout .callout-tip}
[En la práctica]{.callout-title}

Imagina la escalera como cuatro líneas horizontales con un único marcador etiquetado *quién elige el paso siguiente*, deslizándose de izquierda (tu código) a derecha (el modelo) a medida que subes. Es mejor herramienta de diseño que cualquier lista de comprobación, porque fuerza la única pregunta que importa antes de haberte comprometido con nada.
:::

### Puntos clave

- La línea divisoria entre workflow y agente es **quién escribe el flujo de control**.
- El peldaño 4 compra flexibilidad y te cuesta determinismo, testabilidad y gasto predecible.
- La mayoría de los problemas de negocio se resuelven en el peldaño 1 o en el 3. Recurre al 4 cuando la secuencia de pasos genuinamente no pueda conocerse de antemano.

## 1.2 El bucle del agente

Antes de que NeuronAI ejecute por ti el bucle de llamada a tools, vale la pena entenderlo mecánicamente, porque saber exactamente qué se está automatizando es la diferencia entre configurar un framework y confiar en que funcione.

### La verdad incómoda sobre el tool calling

Un modelo de lenguaje no puede ejecutar nada. No puede llamar a una API, leer un archivo ni consultar tu base de datos. Solo produce tokens.

Lo que ocurre en realidad es una convención. Describes tus funciones disponibles al modelo como datos estructurados. El modelo, en lugar de producir prosa, produce un bloque estructurado que dice *«me gustaría llamar a `get_weather` con `{latitude: 45.07, longitude: 7.69}`»*. Tu código ve ese bloque, ejecuta la función PHP real y devuelve el resultado al modelo como un mensaje nuevo. El modelo continúa.

El modelo nunca toca tu sistema. **Tu código es siempre quien ejecuta.** Vale la pena decirlo bien alto, porque además es el modelo de seguridad: un agente solo puede hacer aquello para lo que le diste una tool.

### El bucle, en pseudocódigo

```
messages = [system_prompt, user_message]
tools    = [tool_definitions...]

loop:
    response = llm.call(messages, tools)

    if response contains tool calls:
        for each tool_call in response:
            result = execute(tool_call.name, tool_call.arguments)
            messages.append(assistant_tool_call_message)
            messages.append(tool_result_message)
        continue loop
    else:
        return response.text
```

Cuatro cosas que conviene notar, porque cada una se convierte en un capítulo de este libro:

**1. Es un bucle `while` sin salida garantizada.**
El modelo decide cuándo parar. Si sigue decidiendo llamar a tools, el bucle sigue. Por eso todo framework serio tiene una guarda de número máximo de ejecuciones, y por eso NeuronAI lanza una excepción cuando se alcanza el límite. La Sección 5.9 lo cubre.

**2. Cada iteración reenvía la conversación entera.**
El modelo no tiene estado. La quinta iteración envía el system prompt, el mensaje del usuario y las cuatro llamadas a tools anteriores con sus resultados. El uso de tokens crece de forma *cuadrática* con la longitud del bucle. Un agente de diez pasos no es diez veces más caro que uno de un paso: es considerablemente peor que eso.

**3. Los resultados de las tools son solo texto.**
Lo que devuelva tu función PHP se convierte en cadena y se le entrega al modelo como contexto. Devuelve un blob JSON de 4 MB y habrás quemado tu context window en una sola llamada. Diseñar la salida de una tool es diseñar prompts.

**4. La elección del modelo la impulsan enteramente los nombres y las descripciones.**
Nunca ha visto tu código. Ve `get_transcription` —«Recupera la transcripción de un vídeo de YouTube»— y un esquema de parámetros. Ese texto es toda la interfaz. El Capítulo 5 dedica un tiempo considerable a esto porque es donde los agentes fallan de verdad.

### Ejemplo resuelto: cómo es una ejecución con dos tools

El usuario pregunta: *«¿Cuál es la temperatura media actual entre Turín y Milán?»*

| Paso | Quién actúa | Qué ocurre |
|---|---|---|
| 1 | Tu código | Envía el system prompt + la pregunta + 3 definiciones de tools |
| 2 | Modelo | Devuelve dos llamadas a tools: `get_weather(45.07, 7.69)`, `get_weather(45.46, 9.19)` |
| 3 | Tu código | Ejecuta ambas y añade ambos resultados a los mensajes |
| 4 | Modelo | Recibe 14,2 y 16,8 y devuelve la llamada `mean([14.2, 16.8])` |
| 5 | Tu código | Ejecuta y añade el resultado 15,5 |
| 6 | Modelo | Devuelve prosa: «La media es de unos 15,5 °C.» |

Tres idas y vueltas al LLM. Tres ejecuciones de tools. Una pregunta del usuario. Interioriza esta tabla: es la mejor respuesta que existe a «¿por qué mi funcionalidad de IA es lenta y cara?».

### Puntos clave

- El modelo pide; tu código ejecuta. Siempre.
- El bucle es ilimitado por defecto y debe protegerse.
- El contexto crece con cada iteración; el coste crece más rápido que linealmente.
- Los nombres y las descripciones de las tools son la única interfaz que el modelo tiene con tu sistema.

## 1.3 Anatomía de una llamada al modelo

Cada componente que entra en una sola petición se corresponde con una perilla que más adelante girarás en `SystemPrompt`, `ChatHistory` o en la definición de una tool. Saber cuál es cuál ahorra muchísimas conjeturas.

### Qué viaja realmente por el cable

Quita el SDK y toda petición a un provider son las mismas cuatro cosas:

**1. Identificador del modelo.** Qué pesos responden a la pregunta. La elección del modelo es una decisión de coste/calidad/latencia, no de gusto, y debería ser configuración, nunca una cadena escrita a fuego.

**2. El array de mensajes.** Una lista ordenada de mensajes etiquetados por rol:

- `system` — las instrucciones. Se envían en absolutamente todas las peticiones. No se recuerdan; se retransmiten.
- `user` — lo que dijo la persona.
- `assistant` — lo que dijo el modelo antes, incluidas las peticiones de llamada a tools.
- `tool` — los resultados que tu código devolvió.

El orden es la conversación. No hay sesión del lado del provider. Este punto conviene repetirlo hasta el aburrimiento, porque casi toda la confusión sobre la «memoria» se disuelve en cuanto aceptas que el modelo no tiene ninguna.

**3. Definiciones de tools.** Un JSON Schema por tool: nombre, descripción, tipos de parámetros y cuáles son obligatorios. Se envían en cada petición, completas. Cincuenta tools significa que el esquema de las cincuenta se vuelve a subir en cada iteración del bucle. Por eso NeuronAI incluye un `ToolSearchMiddleware` para catálogos grandes.

**4. Parámetros de generación.** `max_tokens`, `temperature`, `top_p`, secuencias de parada. Para el trabajo agéntico normalmente quieres una temperatura baja: estás pidiendo una selección correcta de tools, no escritura creativa.

### El system prompt es el producto

Los desarrolladores junior tratan el system prompt como un saludo. Los senior lo tratan como la especificación de todo el sistema. Define:

- **Identidad** — qué es el agente y, sobre todo, qué no es
- **Procedimiento** — el orden de operaciones que quieres que se siga
- **Restricciones** — lo que nunca debe hacer
- **Contrato de salida** — formato, idioma, extensión

Una disciplina útil: escribe el system prompt como si estuvieras incorporando a un colaborador externo que es competente, rápido, no tiene contexto sobre tu empresa, no hará preguntas aclaratorias salvo que se lo digas y olvida todo entre tarea y tarea. Porque eso es exactamente lo que tienes.

NeuronAI formaliza tres de esas cuatro secciones en su clase `SystemPrompt` —`background`, `steps`, `output`—. La veremos en la Sección 3.5, y existe porque los prompts estructurados se siguen con más fiabilidad que un muro de prosa, y siguen siendo mantenibles cuando los editan seis personas.

### Leer una respuesta

La respuesta te da el contenido, un motivo de parada y estadísticas de uso. El bloque de uso —tokens de entrada, tokens de salida— es tu contador de costes. Regístralo desde el primer día. En el Capítulo 23 construimos presupuestos encima de él, y no puedes presupuestar lo que nunca registraste.

### Puntos clave

- Cada petición reenvía el system prompt, el historial completo y todos los esquemas de tools.
- No hay sesión del lado del servidor. La «memoria» es un asunto del cliente y siempre lo será.
- Temperatura baja para el trabajo agéntico.
- Captura el uso de tokens desde el primerísimo prototipo.

## 1.4 Context windows, coste y latencia

Esta sección es aritmética. Es también la sección con más probabilidades de cambiar lo que decidas construir, porque son las cuentas de servilleta que determinan si una arquitectura es viable, y casi nadie las hace por adelantado.

### Tokens

Un token es aproximadamente tres cuartos de una palabra inglesa. El italiano y el español van algo más densos; el código, más aún, por la puntuación. Cifras de trabajo útiles:

- 1.000 tokens ≈ 750 palabras ≈ 1,5 páginas
- Un correo de soporte típico ≈ 300 tokens
- Un PDF de 20 páginas ≈ 12.000 tokens
- Una clase PHP mediana ≈ 800 tokens

### La context window es un techo rígido

Todo modelo tiene un máximo: system prompt + historial completo + esquemas de tools + la respuesta, todo junto. Si lo superas, la petición se rechaza de plano; no se trunca, se rechaza.

Esto crea el error de producción más común de la IA conversacional: la aplicación funciona de maravilla durante veinte mensajes y luego empieza a lanzar 400. El historial creció por encima del techo.

NeuronAI lo gestiona con el recorte automático del componente `ChatHistory`, y la documentación da una indicación concreta que vale la pena memorizar: **configura tu context window entre un 5 y un 10 % por debajo del límite real del modelo.** El recortador busca un punto de corte que pierda el mínimo contexto posible, y necesita margen para encontrar uno bueno. Un modelo de 200K debería configurarse a 180–190K. Lo implementamos en la Sección 4.4.

### La aritmética de costes que cambia diseños

Los providers cobran los tokens de entrada y de salida por separado, y la salida suele ser varias veces más cara. Toma una tarifa plausible de gama media de 3 $ por millón de tokens de entrada y 15 $ por millón de salida.

Una sola llamada simple: 500 de entrada, 300 de salida ≈ 0,0060 $.

Ahora la misma funcionalidad como agente de cinco pasos. Como cada iteración lo reenvía todo, los tokens de entrada son aproximadamente acumulativos:

| Iteración | Entrada | Salida |
|---|---|---|
| 1 | 1.500 | 200 |
| 2 | 2.400 | 200 |
| 3 | 3.300 | 250 |
| 4 | 4.300 | 250 |
| 5 | 5.400 | 400 |
| **Total** | **16.900** | **1.300** |

≈ 0,0702 $. **Casi doce veces el coste de la llamada única.**

A 10.000 peticiones diarias eso es la diferencia entre 60 $/día y 700 $/día. Este es el número que decide si construyes en el peldaño 3 o en el 4, y es la razón por la que la Sección 1.1 insistía en que el peldaño importa más que el modelo.

### La latencia se acumula igual

Una llamada al modelo tarda de 1 a 4 segundos. Cinco iteraciones, más el tiempo de ejecución de las tools, y estás en 10–20 segundos de reloj. Ningún usuario espera 20 segundos ante una pantalla en blanco. Esto no es un argumento accesorio a favor del streaming (Capítulo 7): es la razón por la que el streaming existe.

### Las tres palancas

Cuando la aritmética sale mal, tienes exactamente tres movimientos:

1. **Menos iteraciones** — prompts más afilados, mejor diseño de tools, menos tools.
2. **Contexto más pequeño** — recorta el historial con agresividad, devuelve resultados de tools compactos, resume en lugar de acumular.
3. **Modelo más barato por paso** — un modelo pequeño para enrutar y clasificar, uno grande solo para la síntesis final. La interfaz de providers de NeuronAI lo vuelve trivial, y es uno de los argumentos más fuertes a favor del framework.

### Ejercicio

Toma una funcionalidad de tu trabajo actual. Estima los tokens por iteración y el número probable de iteraciones. Calcula el coste diario con tu tráfico real. Guarda el número; informará todas las decisiones de diseño de la Parte II.

### Puntos clave

- El contexto es un techo rígido; superarlo hace fallar la petición de plano.
- Configura el recortador entre un 5 y un 10 % por debajo del límite real.
- El coste de un agente crece de forma superlineal con la longitud del bucle: modélalo antes de construir.
- Tres palancas: menos pasos, contexto más pequeño, modelo más barato por paso.

## 1.5 No determinismo: escribir prompts no es programar

Estás a punto de trabajar con un componente que devuelve salidas distintas para entradas idénticas. Algunos de tus instintos de ingeniería sobreviven a eso; la mayoría necesitan ajustarse. Esta sección los ordena.

### La propiedad que lo rompe todo

Ejecuta el mismo código dos veces y obtén el mismo resultado. Esa suposición sostiene los tests unitarios, la depuración, la revisión de código y la CI. Un LLM la viola. Mismo prompt, mismo modelo, mismos parámetros: salida distinta.

Ni siquiera a temperatura cero obtienes determinismo real: la no asociatividad de los números en coma flotante entre lotes de GPU, actualizaciones del modelo del lado del provider detrás de un alias estable, enrutado dependiente de la carga. Trata «temperatura 0 significa determinista» como falso en producción.

### Qué se rompe

**Los tests unitarios tal como los conoces.** `assertEquals($expected, $agent->chat($input))` no pasará dos veces.

**Bisecar errores.** No puedes reproducir un fallo reejecutando con la misma entrada.

**La confianza al refactorizar.** Reformular un prompt de forma «inofensiva» puede desplazar el comportamiento de manera medible, y nada en tu cadena de herramientas te avisará.

**El versionado semántico de tu propio sistema.** Tu código no cambió y tu comportamiento sí. El provider actualizó un modelo detrás de un alias.

### Qué sobrevive, y qué sustituye al resto

**Testear contratos en lugar de salidas.** No hagas asertos sobre el texto. Hazlos sobre la forma: ¿devolvió JSON válido conforme al esquema?, ¿llamó a la tool esperada?, ¿está presente el campo obligatorio? El structured output (Capítulo 6) existe en gran medida para hacer esto posible.

**Componentes falsos en lugar de llamadas de red.** NeuronAI incluye providers y tools falsos precisamente para que tu CI sea determinista y gratuita. El Capítulo 10 construye esa suite. Esto no es opcional en un proyecto real.

**Evaluaciones en lugar de asertos.** Un conjunto fijo de entradas representativas, ejecutado contra propiedades esperadas y puntuado. No un pasa/falla en una ejecución, sino un porcentaje de calidad seguido en el tiempo, como un benchmark de rendimiento. NeuronAI tiene un componente `Evals`; lo cubrimos en la Sección 10.5.

**Trazado en lugar de depuración.** No puedes ir paso a paso por el razonamiento del modelo, pero puedes registrar cada prompt, llamada a tool, argumento y recuento de tokens. Eso es lo que hace Inspector, y por eso la observabilidad aparece como pilar de primera clase del framework y no como un añadido.

**Fijar versiones en lugar de confiar en alias.** Usa versiones de modelo explícitas en producción —un identificador de modelo fechado y plenamente cualificado en lugar de un alias móvil— para que una actualización del provider sea un despliegue que eliges y no un incidente que descubres.

### El cambio mental

Deja de pensar «función». Empieza a pensar «un colega junior competente pero inconsistente». No harías tests unitarios a un colega. Le darías instrucciones claras, limitarías sus permisos, revisarías su trabajo y seguirías su tasa de error. Todos los patrones arquitectónicos de este libro son una de esas cuatro cosas.

### Puntos clave

- Da por hecho el no determinismo incluso a temperatura 0.
- Testea contratos y formas, no cadenas.
- Componentes falsos para la CI; evaluaciones para la calidad; traces para depurar.
- Fija las versiones de los modelos en producción.

## 1.6 El panorama: frameworks de Python y dónde encaja NeuronAI

El vocabulario de este campo se inventó en Python, y vale la pena aprenderlo para que los artículos, las charlas de conferencias y las ofertas de empleo centradas en Python resulten legibles. También vale la pena ser honesto sobre lo que PHP tiene y lo que no.

### Los titulares en Python

**LangChain** — el primero en llegar y el más grande. Superficie de integración enorme, abstracción históricamente pesada. Convirtió las «cadenas» en el vocabulario por defecto, y dejó a mucha gente recelosa de la sobreabstracción.

**LangGraph** — la respuesta de LangChain a los límites de las cadenas lineales: un grafo explícito de nodos y aristas, con estado, bucles, checkpoints e interrupción con humano en el circuito. Si vas a leer una sola cosa del mundo Python para entender el `Workflow` de NeuronAI, lee la documentación de LangGraph. El solapamiento conceptual es directo y deliberado.

**LlamaIndex** — nació como biblioteca centrada en RAG: ingesta, indexación, recuperación. Su punto fuerte es el lado de los datos.

**CrewAI / AutoGen** — orquestación multiagente basada en roles. «Un agente investigador, un agente redactor, un agente crítico.» Demos excelentes; la parte difícil en producción es controlar el coste y las condiciones de parada.

### Qué asumen todos ellos

Asumen que tus datos y tu lógica de negocio están en Python, o son alcanzables por red. Para una gran parte del comercio mundial, no lo están. Están en una aplicación PHP con quince años de reglas de dominio acumuladas dentro.

El apaño estándar es un microservicio en Python junto a la aplicación PHP. Eso significa un segundo runtime, un segundo pipeline de despliegue, un segundo árbol de dependencias, un límite de API que ahora tienes que diseñar, autenticar y versionar y, algo crítico, el agente vive al lado equivocado de ese límite respecto de las reglas de negocio. Cada llamada a una tool se convierte en un salto de red hacia una aplicación que ya sabía la respuesta.

### Dónde encaja NeuronAI

NeuronAI es la implementación nativa en PHP de la misma arquitectura. Concretamente ofrece:

- Un bucle de agente con tool calling, sobre muchos providers detrás de una sola interfaz
- Un motor `Workflow` event-driven con estado, bucles, checkpoints e interrupción: la pieza con forma de LangGraph
- Un pipeline de RAG: loaders, embeddings, vector stores, procesadores previos y posteriores
- Soporte de cliente MCP
- Streaming con adaptadores de protocolos de interfaz
- Observabilidad de primera clase mediante Inspector

La comparación honesta: Python tiene un banquillo más profundo de utillaje de nivel investigación y una comunidad mucho mayor. PHP tiene tus datos, tu modelo de dominio, tu autenticación, tu cola y tu ORM. Para una enorme clase de aplicaciones de negocio gana la segunda lista, porque la mayor parte del valor agéntico proviene de actuar sobre datos propios con reglas propias, no de técnicas novedosas de modelos.

### Ser justos con las alternativas

No tienes por qué usar un framework. Puedes llamar a la API de un provider con Guzzle y escribir tú mismo el bucle de tools: quizá 150 líneas. Lo que entonces te pertenece es: la abstracción multi-provider, los reintentos, el parseo del streaming, la generación de esquemas, el recorte del historial, los checkpoints y un formato de traces. Ese es el alcance honesto de lo que te ahorra un framework. Juzga a NeuronAI con esa lista.

### Puntos clave

- NeuronAI implementa la misma arquitectura que LangGraph, en PHP.
- El argumento estratégico es la localidad de los datos: pon el agente donde ya está la lógica de negocio.
- Los frameworks te compran abstracción de providers, streaming, esquemas, gestión del historial, checkpoints y traces.

## 1.7 Elegir el peldaño correcto: un marco de decisión

La escalera solo es útil si se convierte en un procedimiento. Aquí va uno: cuatro preguntas, formuladas en orden, aplicadas a un requisito real en lugar de recurrir por defecto a «construyamos un agente».

### Cuatro preguntas, en orden

**P1. ¿Se puede conocer de antemano la secuencia de pasos?**
Sí → peldaño 1 o 3. No → considera el peldaño 4.
Esta es toda la cuestión. Si puedes dibujar el diagrama de flujo, escribe el diagrama de flujo. Un workflow que siempre hace las mismas tres cosas es más barato, más rápido, testeable y depurable.

**P2. ¿Necesita leer o escribir en sistemas de registro?**
No → no hacen falta tools. Sí → tools, e inmediatamente: qué permisos, qué traza de auditoría, qué acciones son irreversibles.

**P3. ¿Alguna acción es irreversible o cara?**
Sí → el humano en el circuito es obligatorio, no un objetivo aspiracional. Reembolsos, correos a clientes, borrados, pagos. Diseña la puerta de aprobación al mismo tiempo que la tool, nunca después.

**P4. ¿La corrección depende de conocimiento privado?**
Sí → RAG o tools de base de datos. Fíjate en que son respuestas distintas: RAG para prosa no estructurada, tools de base de datos para hechos estructurados. Usar RAG para responder «cuántos pedidos hizo este cliente» es un error de diseño: eso es una consulta SQL, y el modelo debería llamarla como tool.

### Casos de estudio

**Caso A — «Resumir los tickets de soporte entrantes.»**
P1 sí, P2 no, P3 no, P4 no. → **Peldaño 1.** Una llamada, un prompt. Construir un agente aquí es desarrollo guiado por el currículum.

**Caso B — «Responder preguntas de clientes a partir de nuestro centro de ayuda.»**
P1 sí, P2 solo lectura, P3 no, P4 sí. → **Peldaño 3 con RAG.** Recuperar, luego generar, luego citar. Un pipeline fijo de dos pasos. No se requiere autonomía.

**Caso C — «Gestionar una reclamación de cliente de principio a fin.»**
P1 no: no sabes de antemano si hará falta consultar un pedido, comprobar una política, hacer un reembolso, escalar, o las cuatro cosas. P2 sí, lectura y escritura. P3 sí, los reembolsos son irreversibles. P4 sí.
→ **Peldaño 4, con tools, RAG, puertas de aprobación y trazado completo.** Este es el Proyecto final B del Capítulo 25, y se gana cada pieza de la maquinaria de este libro.

**Caso D — «Generar un informe semanal a partir de nuestra base de datos.»**
P1 sí, P2 lectura, P3 no, P4 sí, estructurado. → **Peldaño 3.** Consulta fija, el modelo redacta la prosa. La tentación de dejar que un agente explore la base de datos es real; resístela en un trabajo programado donde las preguntas nunca cambian.

### El principio de escalado

Empieza en el peldaño más bajo que pueda funcionar. Publícalo. Escala solo cuando tengas evidencia —casos reales que fallen— de que el peldaño es insuficiente. Cada peldaño hacia arriba multiplica el coste, la latencia y la superficie operativa.

El camino inverso es mucho más doloroso: los equipos que empiezan en el peldaño 4 rara vez descienden, porque para entonces la flexibilidad ya es estructural y nadie sabe qué partes hacían falta de verdad.

### Ejercicio

Toma tres funcionalidades de tu propio producto. Para cada una: pasa las cuatro preguntas, indica el peldaño y justifícalo en cinco líneas. Encuentra un caso en el que al principio querías el peldaño 4 y las preguntas te empujaron al 3; casi siempre hay uno, y darte cuenta es la habilidad que este capítulo enseña.

### Puntos clave

- Si puedes dibujar el diagrama de flujo, construye el diagrama de flujo.
- Las acciones irreversibles exigen una puerta de aprobación diseñada en el mismo momento que la tool.
- RAG para prosa, tools de base de datos para hechos: no los confundas.
- Empieza bajo, escala con evidencia.
