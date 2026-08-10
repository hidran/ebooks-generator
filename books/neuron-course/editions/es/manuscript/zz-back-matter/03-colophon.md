# Colofón {.unnumbered}

## Versiones

El código de este libro se escribió contra:

| Componente | Versión |
|---|---|
| `neuron-core/neuron-ai` | ^3.x — la v3 es la estable actual |
| `neuron-core/neuron-laravel` | ^1.3 — la 1.3.0 requiere `neuron-ai: ^3.15` |
| PHP | 8.1+ para el paquete core, 8.2+ para el SDK de Laravel |
| Laravel | de la 10 a la 13 |
| Modelos de Ollama | `qwen2.5:7b` (chat), `nomic-embed-text` (embeddings) |

Los identificadores de modelo que aparecen en los ejemplos —`claude-sonnet-4-5`, `gpt-4.1-mini`, `gemini-2.0-flash`, `mistral-large-latest`— eran actuales cuando se escribieron y no lo seguirán siendo. Consulta la lista de modelos de tu provider en lugar de fiarte de ningún libro, incluido este.

Antes de fiarte de cualquier afirmación sobre versiones en estas páginas:

```bash
composer show neuron-core/neuron-ai --all
```

## Producción

Escrito en Markdown. Construido con pandoc a EPUB3 y a un DOCX de 6×9 pulgadas, convertido a PDF con LibreOffice. El EPUB se valida con epubcheck; el tamaño de página del PDF se comprueba para que sea exactamente 432 × 648 puntos.

Las herramientas de construcción son un pequeño conjunto de scripts de shell y ayudantes en Python: `bookcfg.py` parsea la configuración del libro, `make-metadata.py` produce los metadatos de pandoc por edición y `fix-pdf-trim.py` ajusta el PDF al tamaño de corte exacto. Nada del pipeline llama a un servicio externo.

Los diagramas son ASCII dentro de bloques de código delimitados, deliberadamente, para que sobrevivan al reflujo a cualquier tamaño de letra en cualquier lector, cosa que ninguna imagen rasterizada hace.

## Ediciones

Publicado en inglés, italiano y español. Las ediciones italiana y española son traducciones del texto en inglés, gobernadas por un glosario compartido que fija como invariables los nombres de productos, paquetes, clases y comandos y mantiene en inglés el vocabulario de industria consolidado: prompt, token, tool, workflow, embedding, streaming.

El código es idéntico en las tres ediciones. Los comentarios, las cadenas literales y los identificadores no se traducen nunca.

## Correcciones

El software se mueve. Si encuentras en este libro algo que ya no coincide con la biblioteca, el Apéndice A explica cómo determinar qué es realmente cierto en tu instalación, que es la respuesta que este libro te daría de todos modos.

## Sobre el autor

Hidran Arias construye y enseña sistemas PHP. Este libro nació de un curso de veintitrés módulos sobre el mismo material, y de la convicción de que la conversación sobre IA agéntica se ha desarrollado casi por completo en Python por razones que nada tienen que ver con dónde está realmente el trabajo.

---

*IA agéntica en PHP con NeuronAI*
Primera edición, 2026
