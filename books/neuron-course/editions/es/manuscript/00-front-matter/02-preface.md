# Prefacio {.unnumbered}

## Una pregunta

Toda idea de este libro desciende de una sola pregunta:

> **¿Quién decide qué pasa a continuación?**

Cuando llamas a un modelo de lenguaje para resumir un ticket de soporte, decide tu código. Decide qué enviar, cuándo enviarlo y qué hacer con la respuesta. El modelo produce texto y nada más.

Cuando construyes un agente, le entregas esa decisión al modelo. Le das un objetivo y un conjunto de capacidades, y él elige qué capacidad usar, ve el resultado, vuelve a elegir y sigue hasta que decide que ha terminado. Esa secuencia no la escribiste tú. Emergió.

Esa transferencia de control es todo el tema. Todo lo demás en este libro —memoria, tools, structured output, recuperación, workflows, aprobación humana, observabilidad— existe para que esa transferencia sea sobrevivible en producción. Dale a un modelo la capacidad de actuar y heredarás un conjunto de problemas que el PHP corriente no tiene: no puedes predecir cuánto costará una petición, no puedes testear el flujo de forma determinista y, cuando se comporta mal, necesitas un trace para averiguar por qué eligió el tool equivocado en el paso cuatro.

Este libro trata de ganarse ese poder deliberadamente, y de saber cuándo no hacerlo.

## Por qué PHP

La conversación sobre IA agéntica se ha desarrollado casi por completo en Python. Eso es un accidente de la historia de la investigación, no una afirmación sobre dónde está el trabajo. Una enorme proporción de la lógica de negocio del mundo —los CRM, los sistemas de facturación, los motores de reservas, las herramientas internas que sostienen calladamente a las empresas— está escrita en PHP, y ya está sentada junto a la base de datos, la cola, la capa de autenticación y los usuarios que se beneficiarían de un agente.

Atornillar un microservicio en Python a una aplicación Laravel para llamar a un LLM es una decisión arquitectónica real con costes reales: otro runtime, otro despliegue, otro conjunto de credenciales, otro salto de red y una copia de tu modelo de dominio que se desviará. A veces es la decisión correcta. A menudo no lo es, y la única razón por la que ocurre es que nadie le mostró al equipo de PHP la alternativa.

**NeuronAI** es la alternativa. Es un framework PHP para construir agentes —instalado como `neuron-core/neuron-ai`, documentado en neuron-ai.dev— y es el tema de este libro. Cubre el mismo terreno que los conocidos frameworks de Python: providers, tools, memoria, structured output, generación aumentada por recuperación, workflows guiados por eventos, interrupción con humano en el circuito, observabilidad. Lo hace con interfaces, inyección de dependencias y clases tipadas, de una forma que le resultará poco sorprendente a cualquiera que haya usado un framework PHP moderno, que es exactamente el objetivo.

Una nota sobre el nombre, porque el ecosistema es inconsistente al respecto. La biblioteca es **NeuronAI**. El paquete de Composer es `neuron-core/neuron-ai`, el binario de la CLI es `vendor/bin/neuron` y el namespace raíz es `NeuronAI\`. Este libro dice NeuronAI en la prosa y deja cada nombre de paquete, comando y namespace exactamente como debes teclearlo.

## Para quién es este libro

Escribes PHP. Te manejas con Composer, namespaces, interfaces y un IDE moderno. Probablemente hayas usado Laravel, aunque las Partes I a IV no lo requieren: se ejecutan sobre PHP puro y un script de CLI, deliberadamente, para que puedas ver cada pieza en movimiento antes de que un framework te oculte alguna.

No necesitas saber nada de aprendizaje automático. En este libro no hay más matemáticas que la aritmética sobre costes. No necesitas haber llamado antes a la API de un LLM. Lo que sí necesitas es el instinto que hace que un buen desarrollador de backend desconfíe de la magia, porque ese instinto es el que este libro recompensa.

Si ya has construido algo con un LLM y te ha resultado poco fiable, caro o imposible de depurar, eres el lector para quien se escribió este libro. Esos tres fallos tienen causas, y las causas tienen nombre.

## Qué vas a construir

El libro alterna teoría, PHP puro y Laravel, en ese orden, y construye de forma continua en lugar de con fragmentos inconexos.

Al final de la Parte II tendrás un agente ejecutándose desde un script de CLI con tools que no escribió ningún código para invocar, un historial de chat que sobrevive a los reinicios, salida tipada y validada, respuestas en streaming, comprensión de imágenes y documentos, una conexión MCP a servidores de tools externos y un trace de todo lo que hizo.

Al final de la Parte IV tendrás un pipeline de recuperación sobre tu propia documentación, workflows guiados por eventos que iteran y se ramifican, workflows que se pausan a mitad de ejecución para que un humano apruebe una acción y luego se reanudan desde un checkpoint, y un sistema multiagente donde agentes especializados se pasan el trabajo entre sí.

Al final de la Parte V, todo ello está dentro de una aplicación Laravel: facades e inyección de dependencias, historial de conversación en Eloquent, tools que tocan tus modelos reales, recuperación sobre los propios datos de tu aplicación, aislamiento por tenant, streaming de tokens sobre SSE y Livewire, workflows de aprobación que encolan y notifican, controles de coste, resiliencia frente a los límites de tasa, defensas contra la prompt injection y una lista de comprobación de despliegue.

La Parte VI son dos proyectos finales —un auditor de repositorios como CLI en PHP puro y un servicio de soporte agéntico en Laravel— más tres capítulos sobre las cosas que nadie te cuenta: cómo elegir una versión y sobrevivir a ella, qué ofrece realmente el ecosistema alrededor del framework y cómo usar asistencia de IA para escribir este tipo de código sin dejar que escriba las partes que importan.

## Sobre el código

Cada muestra de código se escribió contra **NeuronAI v3** y, para la Parte V, el **SDK de NeuronAI para Laravel 1.3.0**, que requiere `neuron-ai: ^3.15`. Se asume PHP 8.2 o posterior en todo el libro.

Esto importa más de lo habitual. NeuronAI cambió los namespaces entre v1/v2 y v3 —`NeuronAI\Agent` pasó a ser `NeuronAI\Agent\Agent`, `NeuronAI\SystemPrompt` pasó a ser `NeuronAI\Agent\SystemPrompt`— y gran cantidad de material publicado, incluidas partes de la documentación oficial, no se ha puesto al día. Un tutorial que era correcto hace dos años ahora fallará en su primera instrucción `use`.

La documentación oficial también se contradice a sí misma en más de cuarenta lugares: tres firmas de constructor distintas para el mismo vector store, dos API de ejecución distintas para los workflows en páginas contiguas, nombres de clase con erratas, un método que es `public` en un ejemplo y `protected` en el siguiente. Cada uno de ellos produce un error para quien copia la página.

El **Apéndice A** es la lista. Los cuarenta y cuatro puntos, agrupados por el capítulo al que afectan, con un conjunto de scripts de sondeo breves que resuelven grupos enteros de golpe contra la versión que realmente tienes instalada. Recorrerlo lleva una tarde y es lo más valioso que puedes hacer antes de escribir código de producción con esta biblioteca. Empieza por ahí si eres de los que leen los apéndices primero.

Todos los laboratorios de las Partes II a IV están diseñados para ejecutarse **gratis y sin conexión** sobre Ollama con un modelo local. Solo necesitarás credenciales de API de pago allí donde el ejercicio dependa genuinamente de la calidad de un modelo de frontera, y el libro lo dice explícitamente cada vez.

## La pregunta que este libro plantea de verdad

El último capítulo se cierra con una pregunta que deberías poder responder sobre cualquier cosa que despliegues después de leer esto:

> **¿Qué es lo peor que puede hacer tu agente, y qué lo detiene?**

Si no puedes responderla, no has terminado de construir.

*Hidran Arias, 2026*
