# Colofón {.unnumbered}

## Versiones

El código de este libro se escribió contra, y se verificó sobre:

| Componente | Versión |
|---|---|
| `neuron-core/neuron-ai` | 4.0.3 |
| `neuron-core/neuron-laravel` | 2.0.0 — requiere `neuron-ai` ^4.0 |
| PHP | 8.5 con `ext-curl` para el código del libro — verificado en 8.5.4 (el propio paquete `neuron-ai` declara `^8.1`) |
| Laravel | 13 |
| Modelos de Ollama | `llama3.2` (chat), `nomic-embed-text` (incrustaciones) |

Cada listado PHP del libro se compiló con PHP 8.5.4, con todos los avisos de obsolescencia activados. El código de los repositorios complementarios, del que se toman la mayoría de los listados, pasa PHPStan en el nivel 8 contra esas versiones. Los ejemplos del repositorio complementario también se ejecutaron: contra un modelo local de Ollama donde lo necesitan, y contra el proveedor falso del propio framework donde no; los pocos que necesitan una infraestructura que un portátil no ejecuta, como un almacén vectorial MariaDB, solo se comprobaron de forma estática. Las pruebas de contrato del repositorio complementario fijan cada clase, método y argumento con nombre del que depende el libro, de modo que fallan de forma evidente el día en que una versión cambie alguno.

Los identificadores de modelo que aparecen en los ejemplos —`claude-sonnet-4-5`, `gpt-4.1-mini`, `gemini-2.0-flash`, `mistral-large-latest`— eran actuales cuando se escribieron y no lo seguirán siendo. Consulta la lista de modelos de tu proveedor en lugar de fiarte de ningún libro, incluido este.

neuron-ai 4.1.0 se publicó el 4 de octubre de 2026, después de que el libro se verificara con la 4.0.3. Las pruebas de los repositorios complementarios y todos los ejemplos ejecutables se probaron también con ella y pasan. Añade `Toolkit::add()` (añadir tools a un toolkit sin heredar de él), un canal de streaming Mercure y la inicialización diferida de los vector stores; ningún listado de este libro depende de ellas, y `^4.0.3` la acepta.

Antes de fiarte de cualquier afirmación sobre versiones en estas páginas:

```bash
composer show neuron-core/neuron-ai
```

## Producción

Escrito en Markdown. Construido con pandoc a EPUB3 y a un DOCX de 7,5×9,25 pulgadas, convertido a PDF con LibreOffice. El EPUB se valida con epubcheck; el tamaño de página del PDF se comprueba para que sea exactamente 540 × 666 puntos.

Las herramientas de construcción son un pequeño conjunto de scripts de shell y ayudantes en Python: `bookcfg.py` parsea la configuración del libro, `make-metadata.py` produce los metadatos de pandoc por edición y `fix-pdf-trim.py` ajusta el PDF al tamaño de corte exacto. Nada del pipeline llama a un servicio externo.

Los diagramas son ASCII dentro de bloques de código delimitados, deliberadamente, para que sobrevivan al reflujo a cualquier tamaño de letra en cualquier lector, cosa que ninguna imagen rasterizada hace.

## Ediciones

Publicado en inglés, italiano y español. Las ediciones italiana y española son traducciones del texto en inglés, gobernadas por un glosario compartido que fija como invariables los nombres de productos, paquetes, clases y comandos.

Las dos traducciones divergen a propósito en un punto. El italiano absorbe el vocabulario técnico inglés tal cual —*il tool*, *il workflow*, *l'embedding*—, que es como escribe la profesión en Italia. El español lo traduce: herramienta, flujo de trabajo, incrustación, transmisión, proveedor, fragmento, punto de control, almacén vectorial. En esta edición solo sobreviven en inglés `prompt`, `token` y `middleware`, porque ninguno tiene un equivalente asentado en castellano.

El código es idéntico en las tres ediciones. Los comentarios, las cadenas literales y los identificadores no se traducen nunca.

## Correcciones

El software se mueve. Si encuentras en este libro algo que ya no coincide con la biblioteca, comprueba las guías de actualización y las skills que trae tu versión instalada, en `vendor/neuron-core/neuron-ai`, y ejecuta `vendor/bin/neuron --help` para ver qué comandos existen realmente: esa es la respuesta que este libro te daría de todos modos.

## Sobre el autor

Hidran Arias construye y enseña sistemas PHP. Este libro nació de un curso de veintitrés módulos sobre el mismo material, y de la convicción de que la conversación sobre IA agéntica se ha desarrollado casi por completo en Python por razones que nada tienen que ver con dónde está realmente el trabajo.

---

*IA agéntica en PHP con NeuronAI*
Primera edición, 2026
