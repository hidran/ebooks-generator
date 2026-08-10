# Parte II — PHP puro y Composer

Sin framework. Composer, un script de CLI y la biblioteca.

Es la parte más larga del libro y la que más enseña, porque aquí nada tiene dónde esconderse. Cada objeto se construye delante de ti, cada llamada es explícita, y cuando algo va mal no hay ningún contenedor de servicios al que culpar.

Empezarás con un esqueleto de proyecto y un primer agente, y luego recorrerás las piezas que convierten una llamada a un modelo en un sistema: el modelo de mensajes y los varios tipos de memoria que necesita una conversación; los tools en verdadera profundidad, que es donde vive la mayor parte de la dificultad práctica del software agéntico; structured output tipado, validado y reintentado cuando el modelo se equivoca; el streaming y los objetos chunk que produce; imágenes y documentos; MCP, para conectar con servidores de tools que no escribiste tú; y, por último, observabilidad y evaluación, para que puedas averiguar qué hizo realmente tu agente y si está empeorando.

Todos los laboratorios de esta parte se ejecutan gratis y sin conexión sobre Ollama.

Si viniste por Laravel, resiste la tentación de saltar adelante. La Parte V integra estas ideas; no las enseña.
