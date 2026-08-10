# Cómo usar este libro {.unnumbered}

## La estructura en tres tiempos

Casi todos los temas de este libro se presentan tres veces, con niveles crecientes de comodidad.

**Primero la teoría.** Qué está ocurriendo realmente por debajo: el bucle del agente, los tokens y el coste, las incrustaciones, el modelo guiado por eventos. Sin código. Estas secciones existen para que, cuando un framework haga algo por ti, sepas exactamente qué está haciendo.

**Luego PHP puro.** La misma idea implementada con Composer y un script de CLI, sin framework, sin magia, sin contenedor de servicios. Ves construirse cada objeto y hacerse cada llamada.

**Luego Laravel.** La misma idea otra vez, integrada en una aplicación real: inyección de dependencias, Eloquent, colas, HTTP, una interfaz que un usuario puede mirar.

Este orden de «desnudo primero, vestido después» es deliberado. Los desarrolladores de PHP tienden a desconfiar de la magia, con razón, y la forma más rápida de hacer que un framework resulte fiable es mostrar qué sustituyó. Si ya conoces bien Laravel puedes avanzar deprisa por las implementaciones en PHP puro, pero no te las saltes: las Partes II a IV son donde realmente se enseñan los conceptos, y la Parte V los da todos por sabidos.

## Las seis partes

**Parte I — Fundamentos** (Capítulos 1–2). Nada de código. La escalera de autonomía, el bucle del agente, la anatomía de una llamada a un modelo, cuánto cuesta una ventana de contexto, por qué escribir prompts no es programar, dónde se sitúa NeuronAI entre los frameworks de Python y cómo está construido NeuronAI. Dos capítulos, y son los que cambian tu forma de diseñar.

**Parte II — PHP puro y Composer** (Capítulos 3–10). Configuración y tu primer agente, mensajes y memoria, herramientas en profundidad, salida estructurada con validación, transmisión, multimodalidad, MCP y observabilidad con evaluación en CI. Es la parte más larga del libro y su núcleo.

**Parte III — Recuperación** (Capítulos 11–12). Por qué existe la recuperación y qué no resuelve, y luego el pipeline de NeuronAI de principio a fin: cargadores, divisores, incrustaciones, almacenes vectoriales, filtrado por metadatos, reindexación y procesadores previos y posteriores.

**Parte IV — Flujos de trabajo** (Capítulos 13–16). El modelo guiado por eventos, bucles y ramas, estado tipado, transmisión desde dentro de un flujo de trabajo, humano en el circuito con puntos de control y reanudación, y orquestación multiagente.

**Parte V — Laravel** (Capítulos 17–23). El SDK, facades e inyección de dependencias, historial de chat en Eloquent, multiinquilino, herramientas sobre tus modelos reales, recuperación sobre los datos de la aplicación, transmisión con SSE y Livewire, flujos de trabajo de aprobación en producción, control de costes, resiliencia, seguridad y una lista de comprobación de despliegue.

**Parte VI — Proyectos finales** (Capítulos 24–26). Dos proyectos completos, y luego estrategia de versiones, el ecosistema circundante y el desarrollo asistido por IA.

## Ejecutar el código

### El repositorio compañero

Los ejemplos están escritos para teclearse, pero también existen como repositorio organizado como monorepo:

```
neuron-course/
├── 01-plain-php/          # Composer, CLI, zero framework
│   ├── composer.json
│   ├── .env.example
│   ├── src/
│   └── examples/          # one script per chapter section
├── 02-laravel-app/        # Laravel 12 + neuron-laravel
└── 99-capstone/           # the final projects
```

Cada sección tiene una etiqueta de Git, de modo que `git checkout chapter-05-tools` te deja en el estado inicial exacto de esa sección. El repositorio incluye un `composer.lock` versionado, lo que significa que la API que obtienes es la API contra la que se escribió este libro, incluso dentro de años. Si un fragmento del libro no coincide con la biblioteca que instalaste hoy, el archivo de bloqueo es el árbitro de lo que quería decir el texto.

### Proveedores, y cómo no gastar dinero

El coste de la API es la razón principal por la que la gente abandona a mitad un proyecto como este. Los laboratorios están estructurados para que no sea un factor.

**Instala Ollama y descarga dos modelos.** Todo lo de las Partes II a IV está diseñado para ejecutarse en local, gratis y sin conexión:

```bash
ollama pull qwen2.5:7b        # chat, tool calling, structured output
ollama pull nomic-embed-text  # embeddings for Part III
```

`qwen2.5:7b` es el modelo local recomendado porque hace llamada a herramientas y salida estructurada con solvencia, cosa que muchos modelos pequeños no logran. Si tu máquina sufre, una cuantización menor completará igualmente todos los laboratorios, solo que con menos fiabilidad, y ver a un modelo más débil fallar al elegir herramientas es genuinamente instructivo.

**Usa un proveedor de pago solo donde la calidad sea el objetivo.** Anthropic, OpenAI y Gemini aparecen en los ejercicios que dependen de la calidad de llamada a herramientas o salida estructurada de un modelo de frontera, y en la Parte V, donde el tema es el comportamiento en producción. Cada uno de esos ejercicios lo indica al principio.

El Capítulo 3 dedica una sección entera a cambiar de proveedor, porque un cambio de proveedor de una línea es la característica más inmediatamente valiosa de NeuronAI y la que impide que te quedes atrapado mientras aún estás aprendiendo.

## Convenciones

**Código.** PHP 8.2+, `declare(strict_types=1)` en los archivos de aplicación, tipos explícitos donde ayudan y secretos en el entorno en lugar de en el código fuente. Los bloques de código son lo bastante completos como para ejecutarse salvo que el texto diga lo contrario; cuando un fragmento es parcial, la clase o función circundante aparece en el bloque inmediatamente anterior.

**Nombres.** Cada nombre de clase, namespace, método, paquete, comando, ruta de archivo y variable de entorno está escrito exactamente como debes teclearlo. Cuando la documentación oficial muestra un nombre distinto del que funciona, el libro usa el que funciona y el Apéndice A registra la discrepancia.

**Notas de versión.** Cuando una API cambió entre versiones mayores, o cuando el material publicado sigue mostrando la forma antigua, el texto lo indica en el punto de uso. No son incisos; son la diferencia entre código que se ejecuta y código que no.

**En la práctica.** Los incisos breves marcados como *En la práctica* llevan técnica que no encaja en la línea principal del argumento: eso que te diría un colega mirando por encima de tu hombro.

**Puntos clave.** Cada sección se cierra con las tres o cuatro afirmaciones que vale la pena recordar. Si estás repasando en lugar de leyendo, son un índice utilizable del argumento del libro.

## Laboratorios y proyectos finales

Dieciséis laboratorios se distribuyen por el libro, cada uno al final del capítulo cuyo material ejercita:

| Lab | Capítulo | Qué construyes |
|---|---|---|
| 1 | 3 | El esqueleto del proyecto en PHP puro y tu primer agente funcionando, intercambiable entre tres proveedores |
| 2 | 4 | Una CLI de chat interactiva de varios turnos con historial en disco y un comando `/reset` |
| 3 | 5 | Un agente del tiempo y calculadora: una herramienta propia sobre una API pública más `CalculatorToolkit` |
| 4 | 5 | Un agente analista de base de datos sobre un esquema real, en solo lectura, con el esquema reducido a las tablas relevantes |
| 5 | 6 | Extracción tipada y validada: correos de pedidos en texto libre convertidos en un DTO `Order` con líneas y totales |
| 6 | 8 | Un agente que lee la captura de pantalla de una factura y devuelve un DTO estructurado |
| 7 | 10 | Una suite de PHPUnit sobre un agente con un proveedor falso y herramientas falsas: sin red, totalmente determinista |
| 8 | 12 | Recuperación sobre documentación a coste cero: ingesta de Markdown, `FileVectorStore`, incrustaciones de Ollama |
| 9 | 12 | La misma recuperación sobre un almacén de producción con búsqueda híbrida |
| 10 | 16 | La fábrica de contenidos: investigador, redactor y revisor con un bucle de corrección, aprobación humana y publicador |
| 11 | 17 | `POST /api/ask` respondido a través de la facade: cinco minutos desde `composer require` hasta la primera respuesta |
| 12 | 18 | Chat persistente por usuario con múltiples hilos e historial en la base de datos |
| 13 | 19 | Un agente de comercio electrónico con `search_orders`, `get_order_status` y `request_refund`: los reembolsos necesitan aprobación |
| 14 | 20 | Una base de conocimiento corporativa: artículos en Eloquent, indexados por cola, respondidos con citas de las fuentes |
| 15 | 21 | Una interfaz de chat con transmisión token a token y un indicador de «usando la herramienta X» |
| 16 | 22 | Aprobación de reembolsos de principio a fin: el agente prepara el caso, se detiene, un responsable aprueba y el flujo de trabajo se reanuda |

Algunos laboratorios se recorren de principio a fin, con todo el código. Otros están especificados en lugar de resueltos: requisitos, criterios de aceptación y las pistas que necesitas, con la implementación en tus manos. La proporción se desplaza deliberadamente a medida que avanza el libro: para la Parte V ya has visto todos los patrones que el laboratorio necesita, y que te den la respuesta desperdiciaría el ejercicio.

Los laboratorios son el libro. Leer un capítulo sobre herramientas te enseña qué es una herramienta; escribir uno te enseña por qué las descripciones de herramientas son ingeniería de prompts. Presupuesta tiempo real para ellos.

Los dos proyectos finales de la Parte VI son deliberadamente más grandes y deliberadamente poco especificados: enuncian requisitos, no pasos, porque a esas alturas decidir los pasos es la habilidad que se está evaluando.

## Los apéndices

**Apéndice A — Dónde la documentación se desvía del código.** Cuarenta y cuatro discrepancias verificadas entre la documentación oficial de NeuronAI y la biblioteca publicada, agrupadas por capítulo, con scripts de sondeo que las resuelven en bloque contra tu versión instalada. Léelo antes de escribir código de producción.

**Apéndice B — Glosario.** El vocabulario, definido una vez.

## Si tienes prisa

Si necesitas algo funcionando esta semana en lugar de entender el campo, lee el Capítulo 1 (cambiará lo que decidas construir), el Capítulo 3 (configuración y primer agente), el Capítulo 5 (herramientas) y el Capítulo 6 (salida estructurada). Con eso basta para publicar una funcionalidad útil de tercer peldaño.

Después vuelve al Capítulo 10, porque la diferencia entre una demo y un producto es saber qué hizo realmente tu agente.
