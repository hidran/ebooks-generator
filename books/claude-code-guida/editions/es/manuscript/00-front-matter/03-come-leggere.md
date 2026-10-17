# Cómo leer este libro {.unnumbered}

## En qué orden

Si es la primera vez, léelo en orden, del capítulo 1 al 23. Cada parte da por sabido lo que has visto en las anteriores: si llegas a la Photogallery sin haber usado nunca Plan Mode o sin saber qué va en un CLAUDE.md, algunos pasos te parecerán saltos al vacío. Al principio de cada capítulo, los requisitos previos dicen de qué capítulos depende; si no hay ninguno, puedes leerlo por separado.

Si ya usas Claude Code y te interesa sobre todo el método para los proyectos, hay un camino más corto: lee el capítulo 2, luego la Parte III (capítulos 7-10), la Parte IV (capítulos 11-15) y salta a la Photogallery (capítulo 17). Te saltas el análisis de datos de la Parte II y la landing page, que puedes recuperar después.

Tras la primera lectura, el libro funciona como referencia. Los apéndices están pensados para eso: el glosario, la resolución de problemas, los prompts listos, los recursos y el registro de cambios no se leen de principio a fin, vas a ellos cuando necesitas algo.

## Convenciones

El texto en `monoespaciado` es algo que hay que escribir exactamente así: un comando, una ruta, el nombre de un archivo, una opción, una tecla. Si ves `CLAUDE.md` en este formato, me refiero a ese archivo con ese nombre.

Los comandos de terminal aparecen en bloques como este, sin el prompt de la shell delante:

```bash
claude --version
```

Los bloques con otra etiqueta (`json`, `python`, `markdown`, `text`) contienen código, configuración o el texto de un prompt que pegar en Claude Code. Los prompts están en español: Claude los entiende perfectamente, y trabajar en tu idioma te ayuda a escribir peticiones más precisas.

Aquí y allá encontrarás recuadros. **Consejo** es un atajo o una costumbre que ahorra tiempo. **Atención** señala un error habitual o un riesgo concreto. **Bajo el capó** es una explicación técnica que puedes saltarte sin perder el hilo. **Ejemplo** muestra un caso con entrada y salida reales. **Prompt reutilizable** es un prompt listo para adaptar a tus proyectos.

Cada capítulo empieza con lo que aprenderás y termina con un resumen y un ejercicio. Los ejercicios no son obligatorios, pero son la forma más rápida de darte cuenta de lo que no te ha quedado claro.

## Los repositorios de apoyo

El código de los proyectos es público en GitHub.

`github.com/hidran/claude-code-book-photogallery` contiene la Photogallery de la Parte VI. La rama `main` es el proyecto terminado; las ramas `book/...` fotografían las etapas intermedias, para que puedas comparar tu trabajo o volver a empezar desde un punto concreto.

`github.com/hidran/fluentaipro-claude-landingpage` contiene la landing page del capítulo 16, con una rama `book/...` para cada fase.

`github.com/hidran/claude-code-book-snippets` reúne los prompts reutilizables capítulo a capítulo y la colección completa del Apéndice C en texto plano, cómoda para copiar y pegar.

::: {.callout .callout-warning}
[Ojo con los números de las ramas]{.callout-title}

Las ramas se crearon para la primera edición y llevan el número de capítulo de entonces. Por ejemplo, `book/cap-13-wave-1-backend` corresponde al capítulo 19 de esta edición y `book/cap-10-3-execution` al capítulo 16. En el texto siempre tienes el nombre exacto de la rama que usar, así que no tienes que hacer conversiones a mano.
:::

Para avisar de un error, de un comando que ya no existe o de un comportamiento distinto del que describe el libro, abre un issue en el repositorio `claude-code-book-snippets`. Los avisos verificados entran en la siguiente revisión y en el registro de cambios del Apéndice E.

## Actualizaciones

Claude Code cambia deprisa, y el libro se actualiza cuando los cambios afectan a la forma de trabajar: comandos renombrados, funciones eliminadas, comportamientos distintos de los modelos. Esta es la segunda edición, actualizada a octubre de 2026. En Kindle puedes recibir las versiones nuevas activando las actualizaciones automáticas de libros en la configuración de Amazon (Administrar contenido y dispositivos).
