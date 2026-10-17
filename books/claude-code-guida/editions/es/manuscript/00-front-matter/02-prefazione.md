# Prefacio {.unnumbered}

## Por qué este libro

La primera vez que construí algo serio con Claude Code me pasé tres horas buscando en Google.

El problema no era difícil. Buscaba cosas básicas: cómo preparar un proyecto para que Claude no perdiera el hilo después de cincuenta mensajes, por qué el comando de un tutorial no existía en la versión que tenía delante, cómo hacer que trabajara sobre varios archivos sin pegar su contenido cada vez. Recorrí documentación desactualizada, hilos de Reddit y vídeos de doce minutos en los que el autor presentaba como método el hecho de pedirle a Claude que escribiera código.

Si aquella noche alguien me hubiera explicado lo que fui descubriendo en los meses siguientes, habría terminado en media hora. Este libro es la explicación que me habría gustado tener.

Desde entonces uso Claude Code a diario, en el trabajo y en mis proyectos: scripts de Python que generan informes de Excel para un cliente, landing pages, automatizaciones, herramientas internas, hasta una aplicación full-stack con autenticación, subida de archivos a S3, panel de administración y deploy en AWS. Lo he usado con Python, JavaScript y PHP, en repositorios pequeños y en bases de código de cientos de archivos, solo y en equipo.

Lo que aprendí es que el salto de "lo he probado un par de veces" a "tengo un proyecto en producción" depende poco de los comandos. Depende de cómo trabajas: cómo preparas una sesión, cuándo planificas y cuándo no, qué pones en CLAUDE.md, cuándo una tarea merece un agente aparte, cómo compruebas lo que ha hecho el agente. Los comandos cambian casi cada semana. Esas costumbres siguen siendo útiles mucho más tiempo, y el libro insiste en ellas.

## Para quién es

Para quien escribe código al menos una vez por semana, en cualquier lenguaje: desarrolladores front-end y back-end, quien escribe scripts y automatizaciones, analistas de datos que se montan sus propios informes.

Para quien ya ha probado ChatGPT, Copilot o Cursor para reescribir una función o explicar un error, pero nunca ha terminado un proyecto entero con un agente. No sabe muy bien cuánto fiarse del resultado ni cómo encajarlo en su forma de trabajar.

Para quien quiere un método repetible. Trucos hay de sobra en internet; un proceso que funcione también la décima vez, en un proyecto distinto, es más difícil de encontrar.

Probablemente no es el libro adecuado para tres tipos de lector. El responsable que quiere saber si Claude Code sustituye a los desarrolladores: la respuesta es no, y el libro está escrito para quien escribe el código. Quien busca un análisis académico de los modelos de lenguaje o una comparación rigurosa entre agentes: ese libro existe, pero no es este. Y quien nunca ha abierto un terminal: Claude Code da por hechas las bases, una variable, un bucle, un comando de shell. Si estás en ese punto, haz antes un curso introductorio de Python o JavaScript y luego vuelve.

## Cómo está organizado

El libro sigue una curva pensada: cada parte se apoya en las anteriores.

La **Parte I** (capítulos 1-3) instala Claude Code, explica cómo trabaja un agente dentro del terminal y cómo escribir prompts que consigan el resultado al primer o segundo intento. La Parte II (capítulos 4-6) lo aplica todo a datos reales: un CSV, un informe de Excel, gráficos, un dashboard y un PDF. La Parte III (capítulos 7-10) amplía Claude Code con CLAUDE.md, comandos personalizados, skills y agentes. La Parte IV (capítulos 11-15) es nueva en esta edición: permisos y sandbox, hooks, MCP, plugins, gestión del contexto y de la memoria. La Parte V (capítulo 16) es el primer proyecto completo, una landing page desde el mockup hasta el deploy en Firebase. La Parte VI (capítulos 17-23) es el proyecto principal, la Photogallery: especificaciones, Spec Driven Development, ejecución por oleadas, revisión, QA y deploy en AWS con CloudFormation.

Al final hay cinco apéndices para tener a mano: glosario, resolución de problemas, prompts listos para usar, recursos y registro de cambios.

## Qué cambia en la segunda edición

La primera edición, publicada en mayo de 2026, describía Claude Code con Claude Opus 4.7 y Sonnet 4.6. Cinco meses después muchas cosas son distintas: el modelo predeterminado es Claude Opus 5.5 con un millón de tokens de contexto, Claude Code arranca en auto mode y pide confirmación mucho menos, los comandos personalizados se han fusionado con las skills, el asistente `/agents` ya no existe, la code review viene integrada y puedes hacer trabajar varias sesiones en paralelo sobre worktrees separados.

He actualizado todos los capítulos a octubre de 2026 y he añadido seis: el capítulo 2 sobre cómo funciona un agente, los cinco capítulos de la Parte IV y el capítulo 20 sobre las oleadas en paralelo. El capítulo 22 compara ahora la revisión integrada de Claude Code con la de un segundo modelo. También he reescrito el texto de principio a fin, quitando repeticiones y frases de relleno, porque un libro técnico tiene que ahorrarle tiempo a quien lo lee. La lista completa de cambios está en el Apéndice E.

Muchas de las novedades las grabé primero como lecciones de mi curso de Claude Code y después las traje aquí. Si hiciste el curso, reconocerás el proyecto de laboratorio de la Parte IV.

## Qué cambiará mientras lees

Claude Code saca versiones nuevas casi a diario. Mientras lees, algún comando habrá cambiado de nombre, alguna opción habrá desaparecido y habrán llegado otras. Donde algo es especialmente inestable, como el nombre del modelo predeterminado, el texto te dice cómo comprobarlo en tu instalación en lugar de fiarte de la página impresa.

El método, en cambio, aguanta: especificaciones escritas, criterios de aceptación verificables, restricciones impuestas con permisos y hooks en lugar de recomendaciones, revisión antes del merge. Las novedades que lleguen encajan en ese flujo.

## Agradecimientos

Gracias a Anthropic, por construir una herramienta lo bastante rica como para merecer un libro entero.

Gracias a Jesse Vincent y a la comunidad de Superpowers por el plugin, las ideas y las discusiones que influyeron en la Parte III.

Gracias a los alumnos de mi curso online, que trabajaron con las versiones preliminares de estos capítulos, encontraron los errores más vergonzosos antes que tú e hicieron las preguntas que me convencieron para añadir secciones que no tenía previstas. Y gracias a los lectores de la primera edición que me escribieron: muchas correcciones de esta edición vienen de ellos.

Gracias a mis compañeros de Spryker por las tardes de pair programming con IA, de las que salieron más ejemplos de los que cito.

Gracias a mi familia, que durante muchas noches soportó mis "cinco minutos más y voy a cenar".

Hidran Arias, octubre de 2026
