# Capítulo 17. Photogallery, del prompt a las especificaciones

::: {.chapter-goals}
[Qué aprenderás]{.callout-title}

Cómo se pasa de una idea escrita en diez líneas a una especificación que Claude Code puede ejecutar sin inventarse nada: elegir el stack a partir de los requisitos, iterar un brief hasta convertirlo en un megaprompt, generar la spec y revisarla área por área, y saber cuándo parar.

[Requisitos previos]{.callout-title}

Los capítulos 1-16 (sobre todo el 7, sobre `CLAUDE.md`) y las bases de la web: APIs REST, SQL relacional, autenticación con tokens. A Laravel y React los conocerás a través de las specs.

:::

Hasta aquí has trabajado en proyectos acotados: un script de Python, un análisis de datos, una landing page. A partir de este capítulo construimos Photogallery, una aplicación full-stack para gestionar fotografías, y la llevamos hasta el deploy en AWS. Es lo bastante pequeña para caber en la cabeza y lo bastante rica para obligarte a tomar las decisiones que importan: autenticación, subida de archivos, colas, relaciones muchos a muchos, paginación, búsqueda, cloud. Además el dominio ya lo conoces, así que la atención se queda en las decisiones técnicas. Las funcionalidades:

- subida de fotos JPEG, PNG y WebP de hasta 10 MB cada una, de 1 a 20 archivos a la vez;
- álbumes, etiquetas y búsqueda por título, descripción, etiqueta, álbum y favoritas;
- galería en cuadrícula masonry con lightbox a pantalla completa y atajos de teclado (`←`, `→`, `Escape`, `F`, `Delete`, `/`);
- procesamiento asíncrono: el upload responde enseguida y luego un job en cola genera tres tamaños (300, 800 y 1600 px de ancho) y extrae los datos EXIF;
- el mismo código en local y en producción: disco local y cola en base de datos en el portátil, S3 y SQS en AWS; solo cambian las variables de entorno;
- autenticación con tokens de Sanctum y un panel de administración Filament en `/admin`, con la monitorización de la cola.

Aquí eliges el stack y escribes las especificaciones. El capítulo 18 las convierte en los tres archivos canónicos del Spec Driven Development, el 19 ejecuta el plan con code review, el 20 lanza las waves en paralelo, el 21 añade features a un proyecto ya en marcha, el 22 hace el QA antes del deploy y el 23 lo lleva todo a AWS con CloudFormation.

El código está en el repo companion `github.com/hidran/claude-code-book-photogallery`, con una rama por cada fase. Los nombres siguen la numeración de la primera edición (consulta "Cómo leer este libro"): este capítulo corresponde a `book/cap-11-prompts-and-spec`, que contiene solo prompts y specs.

## 17.1 Prompt base: elegir el stack con criterio

El primer prompt de un proyecto pesa más que los demás. Si está mal, produce código verosímil que resulta estar mal semanas después, cuando dar marcha atrás sale caro.

### Describe el qué, no el cómo

La tentación es empezar con una lista de tecnologías. El primer prompt, en cambio, describe el problema:

```text
Quiero construir una aplicación web full-stack para una galería de fotos.
Los usuarios deben poder:
- subir fotos (JPEG, PNG, WebP, máx. 10 MB) de una en una o en lote
- organizar las fotos en álbumes
- etiquetar las fotos con palabras clave libres
- buscar por título, etiqueta, álbum y favoritas
- ver las fotos en cuadrícula con lightbox a pantalla completa
- navegar con las flechas del teclado
- marcar fotos como favoritas
- registrarse e iniciar sesión

Tiene que haber un panel de administración.
La app debe funcionar en local para desarrollo y en AWS en producción.

No elijas todavía el stack. Primero dime qué stacks
recomendarías para este tipo de proyecto, con los tradeoffs
de cada uno. Quiero tecnologías estándar y maduras, nada de hype.
```

La última frase pide una comparación antes de la elección. En lugar de ir directo al código, como en el vibecoding, usas a Claude como consultor para la fase de diseño. Fíjate también en lo que falta: ningún framework, ninguna base de datos, ninguna librería. Si partes del stack, descartas de entrada las soluciones en las que no habías pensado; si partes de los requisitos, el stack sale de ellos.

::: {.callout .callout-tip}
[Consejo]{.callout-title}

Para el trabajo de diseño y para las specs, sube el nivel de razonamiento con `/effort high` (el selector va de `low` a `xhigh`). Para una sola pregunta difícil basta con escribir `ultrathink` en el mensaje: vale solo para ese prompt.
:::

### Las alternativas que propone Claude

Claude responde con dos o tres stacks candidatos, más o menos así.

Stack A: Node.js con Express o Fastify, PostgreSQL, React con Vite. Un solo lenguaje, mucha documentación, deploy sencillo. La contra es que Express no impone ninguna estructura: los módulos y las capas los organizas tú.

Stack B: NestJS con React, TanStack Query y MySQL. TypeScript en todas partes, inyección de dependencias y decoradores listos para usar, una estructura modular que aguanta el crecimiento. La contra es una curva de aprendizaje más empinada y algo de boilerplate al principio.

Stack C: Laravel con Filament para el panel de administración y, en el frontend, Inertia con React o bien una SPA de React separada que consume una API REST. Mucha velocidad de desarrollo y un panel de administración casi hecho. La contra es el stack mixto, PHP en el backend y TypeScript en el frontend.

Los tres son válidos. La pregunta útil es cuál se adapta mejor a tus requisitos, a lo que el equipo ya sabe hacer y al sitio donde va a correr en producción.

### Leer la respuesta con ojo crítico

No te quedes en la columna de los pros. Haz preguntas de seguimiento sobre los requisitos que más pesan:

```text
Para el Stack B con NestJS: el panel de administración necesita CRUD,
filtros, bulk actions y un widget con el estado de la cola.
¿Cuánto de esto tengo que escribir a mano?
```

```text
Para el Stack C con una SPA de React separada: ¿cómo gestiono
la autenticación? ¿Sanctum en modo token o en modo cookie,
y con qué compromisos de seguridad?
```

Son las preguntas que sacan a la luz los tradeoffs ocultos. Un panel de administración con tablas, filtros, bulk actions y permisos escrito desde cero son semanas de trabajo, aunque en la lista de requisitos ocupe una línea.

### La elección: Laravel 13, Filament v5 y React 19

Photogallery usa el Stack C en la variante con API separada. Un backend Laravel 13 expone una API REST JSON bajo `/api/v1`, el panel Filament v5 está montado en la misma aplicación en `/admin`, y una SPA React 19 con Vite 6 y Tailwind CSS v4 consume la API. La SPA se autentica con los tokens de Laravel Sanctum. Los motivos salen de los requisitos, uno por uno.

El panel de administración es un requisito, y Filament lo cubre casi entero: resources con tablas, filtros, bulk actions, formularios y widgets, dentro de la misma app y sobre los mismos modelos Eloquent. Con NestJS ese panel había que escribirlo.

"En local y en AWS" se traduce en dos abstracciones que Laravel ya tiene: la facade `Storage` y los drivers de colas. En desarrollo el disco es local y la cola corre sobre la base de datos; en producción pasan a ser S3 y SQS. El código llama siempre a `Storage::disk('photos')` y solo cambia el archivo `.env`. El procesamiento de imágenes es un job en cola con reintentos y backoff, la subida en lote usa el batching de colas con la tabla `job_batches`, y Sanctum gestiona en el mismo proyecto tokens Bearer para la SPA y la sesión web para Filament.

El frontend sigue siendo una SPA separada, en TypeScript. Inertia habría eliminado la API, pero aquí una API versionada compensa: la SPA se compila y se despliega por su cuenta, y el contrato entre los dos lados se convierte en un documento que puedes verificar. La base de datos es relacional, MySQL o MariaDB, con un índice FULLTEXT para la búsqueda y RDS en producción. El último motivo es el más práctico: el equipo conoce PHP y Laravel, y el coste de aprender un stack es un requisito no funcional como cualquier otro.

En el primer borrador de este proyecto la elección era NestJS, para tener TypeScript en ambos lados. Cambió durante la iteración de las specs, cuando el panel de administración, las colas y el almacenamiento pasaron de ser líneas de una lista a requisitos con sus detalles. El workflow de los próximos capítulos es el mismo con cualquier stack.

Comunica la elección a Claude, junto con las restricciones:

```text
Elijo el Stack C, en la variante con API separada:
backend Laravel 13 (API REST JSON) + Filament v5 para la administración,
frontend React 19 + Vite 6 + Tailwind CSS v4 como SPA separada.
Motivos: Filament cubre el panel de administración; Storage y las colas
de Laravel pasan de local a AWS cambiando solo las variables de entorno;
el equipo conoce PHP y Laravel.

Restricciones que hay que respetar en todas las specs:
- API bajo /api/v1
- Autenticación de la SPA con tokens de Sanctum (header Authorization: Bearer),
  no cookies; Filament usa la sesión web estándar
- Upload multipart hacia la API, de 1 a 20 archivos por petición;
  la respuesta llega enseguida, el resize y el EXIF corren en un job en cola
- Claves primarias UUID en todas las tablas
- Tailwind v4 solo con el plugin @tailwindcss/vite: nada de
  tailwind.config.js, nada de postcss.config.js

Usa esta elección para todo el proyecto.
```

Las restricciones sirven para evitar desviaciones. Sin ellas, en las specs Claude podría proponer autenticación con cookies, un `tailwind.config.js` que Tailwind v4 no usa, o el resize dentro del controller: decisiones verosímiles y contrarias a lo que has decidido. En el repo estas restricciones acaban también en el `CLAUDE.md` del proyecto, entre las reglas críticas: la quinta dice que el setup de Tailwind v4 "is non-negotiable".

### El antipatrón de la elección sin motivo

"Uso React porque lo conozco, Express porque es sencillo y MongoDB porque no quiero pensar en el esquema." Para un side project en solitario funciona. Para un proyecto que tiene que aguantar en producción, o que mantendrá otra persona, no. Antes del primer archivo, pregúntate si el stack soporta los requisitos no funcionales, si el equipo lo conoce o puede aprenderlo a un coste aceptable, si tiene documentación y soporte a largo plazo, y cómo se comporta en producción entre deploys, monitorización y depuración. Claude te ayuda con cada una de estas preguntas, si se la haces. Un último control útil antes de fijar el stack:

```text
Enumera los tres riesgos principales del stack que he elegido para Photogallery.
Para cada uno dime cómo lo vería venir y qué puedo hacer ahora, en la fase
de spec, para reducirlo.
```

Si no sabes responder a uno de los riesgos, te falta información: vuelve a las preguntas de seguimiento antes de fijar el stack.

## 17.2 Del prompt base al brief técnico

El paso siguiente es el brief técnico, un documento que un desarrollador podría usar para construir el sistema sin hacerte más preguntas. Se escribe antes del código y sigue siendo la fuente de verdad durante todo el proyecto. La diferencia con el prompt base es concreta:

| Prompt base | Brief técnico |
| :---- | :---- |
| "Quiere subir fotos" | De 1 a 20 archivos por petición, JPEG, PNG o WebP, máximo 10 MB cada uno. El original se guarda enseguida y la respuesta es inmediata; los tres tamaños y el EXIF los produce un job en cola, con 3 intentos |
| "Autenticación de usuarios" | Tokens de Sanctum para la SPA con el header `Authorization: Bearer`, sesión web para Filament. Los GET son públicos; las escrituras requieren token y propiedad del recurso |
| "Tiene que ir a producción" | El mismo código en local y en AWS: cola en base de datos y disco local en desarrollo, SQS y S3 en producción. Solo cambian las variables de entorno |
| "Los usuarios gestionan sus fotos" | Cada foto y cada álbum tienen un propietario (`user_id`). En la v1 el borrado es definitivo, sin soft delete; borrar un álbum deja sus fotos sin álbum |

Cada línea del prompt base deja una decisión en manos de Claude, que elegirá algo razonable, pero no necesariamente lo que tenías en la cabeza.

### Ronda 1: el primer borrador

Para el primer borrador usa un prompt genérico, que también te servirá en tus próximos proyectos. Para Photogallery el contexto son las funcionalidades del prompt base, y el stack es el que acabas de elegir, con sus motivos.

::: {.callout .callout-prompt}
[Prompt reutilizable]{.callout-title}

Brief técnico en una sesión. Sustituye los campos entre corchetes e itera 2-3 veces antes de dar el brief por listo. Los puntos 5 y 6 son los temas de la ronda 2.

```text
Contexto: estoy construyendo [descripción del proyecto en 2-3 frases].
Stack tecnológico: [lista del stack elegido con su justificación].

Genera un brief técnico estructurado que incluya:
1. Requisitos funcionales: funcionalidades por rol (visitante / usuario / admin)
   con criterios de aceptación para cada una
2. Requisitos no funcionales: rendimiento, seguridad (autenticación,
   autorización, validaciones), escalabilidad (orden de magnitud
   de los usuarios y de los datos esperados)
3. Restricciones: stack cerrado, hosting de destino, presupuesto orientativo, plazos
4. Decisiones técnicas clave: estrategia de autenticación (tokens / sesiones),
   upload (vía API / presigned URLs), enfoque de la base de datos (migrations /
   ORM / SQL), almacenamiento (local / S3 / otro)
5. Fuera de alcance: qué no construimos en la primera versión, y por qué
6. Cuotas, límites y audit log, si están dentro del alcance

Genera un documento de 3-4 páginas en Markdown.
Después del borrador, espera mi revisión antes de pasar
a las especificaciones operativas.
```
:::

En el primer borrador siempre encontrarás algo que falta o que no coincide con lo que tienes en la cabeza. Tu trabajo es encontrar los huecos y describirlos con precisión en las rondas siguientes. Qué buscar:

- ¿Las funcionalidades son verificables? "El usuario puede buscar fotos" no lo es. "La búsqueda filtra por título y descripción, por una o más etiquetas combinadas con AND, por álbum y por favoritas, con resultados paginados" sí lo es.
- ¿Los requisitos no funcionales describen comportamientos observables? "La app tiene que ser rápida" no es un requisito. "La cuadrícula tiene 2 columnas en móvil, 3 en tablet y 4 en escritorio" y "la respuesta al upload no espera al resize" sí lo son.
- ¿Las decisiones están justificadas? Si el brief dice tokens de Sanctum, tiene que decir también por qué: la SPA y la API son dos artefactos separados, y el header `Authorization: Bearer` se ahorra la vuelta del CSRF que exigen las cookies.

### Ronda 2: decidir qué se queda fuera

Un primer borrador tiende a crecer. Cuotas de espacio por usuario, audit log, soft delete con papelera, comentarios debajo de las fotos: son ideas sensatas, y cada una pesa sobre el esquema y las consultas. Una columna `deleted_at`, por ejemplo, obliga a que cada consulta excluya los registros borrados. Decide ahora qué entra en la v1 y escríbelo:

```text
Añade al brief una sección "Fuera de alcance (v1)". Enumera de forma
explícita lo que no construimos en la primera versión:
- soft delete y restauración: los borrados son definitivos
- cuotas por usuario (espacio, número de fotos)
- comentarios, likes y reacciones
- edición de imágenes (recorte, rotación, filtros), salvo
  la autoorientación según el EXIF al subir
- apps nativas para iOS y Android
- autenticación de dos factores
- interfaz multilingüe

Para cada punto añade una línea sobre por qué lo aplazamos.
```

Un punto escrito como fuera de alcance deja además de reaparecer en las respuestas de Claude como añadido "para que esté completo". En el proyecto final la lista vive en `docs/REQUIREMENTS.md`, en la sección "Out of scope (v1)".

### Ronda 3: upload y procesamiento de imágenes

El upload es la parte más delicada del sistema, y hay dos caminos.

Con las presigned URLs de S3, el cliente le pide al backend una URL firmada y sube el archivo directamente al bucket. El backend no toca los bytes y escala sin esfuerzo, pero la validación llega cuando el archivo ya está en S3, y en desarrollo necesitas un S3 local aunque solo sea para subir una foto.

Con el upload a través de la API, el cliente envía una petición multipart a Laravel. Una FormRequest comprueba tipo y tamaño antes de guardar nada, el controller guarda el original y responde enseguida, y el trabajo pesado (resize y EXIF) pasa a un job en cola. Los bytes atraviesan el backend, pero con archivos de 10 MB y como mucho 20 por petición es un coste que la v1 se puede permitir, y el mismo código funciona con el disco local.

Photogallery toma el segundo camino. Si algún día el upload se convierte en el cuello de botella, las presigned URLs serán la evolución natural, y la spec es el sitio donde dejarlo escrito. La ronda 3 define el pipeline:

```text
Revisa la sección sobre el upload. El upload pasa por la API de Laravel
como multipart/form-data, de 1 a 20 archivos por petición.

Cuando llega una foto:
1. Guarda el original enseguida
2. Responde enseguida, sin hacer esperar al usuario
3. Encola un job que genera tres tamaños:
   - thumbnail: 300 px de ancho, calidad JPEG 80%
   - medium: 800 px, calidad 85%
   - large: 1600 px, calidad 90%
4. El job extrae también los datos EXIF (cámara, ISO, apertura, etc.)
5. Registra el estado en la base de datos: pending, processing, completed, failed
6. Si el job falla, reintenta hasta 3 veces y luego marca la foto como failed

En desarrollo: cola en base de datos y sistema de archivos local.
En producción: cola AWS SQS y almacenamiento S3, el mismo código, solo
cambian las variables de entorno. Para las imágenes usa Intervention Image v3.

Actualiza el brief con el flujo y con las implicaciones de seguridad:
quién puede ver el original y qué datos EXIF no se deben publicar.
```

En la spec final, la pregunta sobre seguridad produce dos discos distintos. `photos_private` contiene los originales, que nunca se sirven en público y solo se alcanzan con URLs firmadas válidas durante 5 minutos. `photos` contiene los tres tamaños generados y es público. Las coordenadas GPS se eliminan de los datos EXIF antes de guardarlos.

### Ronda 4: el brief se convierte en el megaprompt

Después de tres o cuatro rondas, el brief contiene detalles que no habrías escrito a la primera. En el repo la versión final es `docs/PROMPT.md`, el megaprompt a partir del cual Claude genera la spec. Describe qué hace la app, la arquitectura en dos carpetas (`backend/` y `frontend/`), las entidades de la base de datos con sus campos principales, el pipeline de la ronda 3, los endpoints bajo `/api/v1`, el panel Filament, las funcionalidades del frontend (hasta el debounce de 300 ms en la búsqueda), la autenticación, los errores, detalles técnicos como Tailwind v4 sin archivos de configuración, el plan de tests y, por último, los principios de ingeniería: SOLID, REST, KISS y DRY, con ejemplos sacados de este proyecto.

Esta última sección llegó en un commit aparte ("Adds SOLID, KISS, DRY principles") y es la que hace que la spec tenga opiniones propias. Un extracto, traducido del inglés del repo:

```text
### KISS
- Nada de abstracciones prematuras: no crees un Repository si el modelo
  Eloquent se usa en un solo sitio. Usa el modelo directamente.
- Nada de optimizaciones prematuras: no añadas una caché Redis
  antes de haber medido que la base de datos es lenta.
- Patrones estándar de Laravel: Eloquent, Form Request, API Resource,
  Policy. Nada de middleware personalizado para cosas que Laravel ya hace.
- Legible antes que ingenioso: un método obvio de 10 líneas gana a
  un método de 3 líneas hecho de closures dentro de closures.
```

El final del megaprompt dice qué generar. Al principio pedía un solo archivo, `SPEC.md`; la última versión pide cuatro (`CLAUDE.md`, `docs/REQUIREMENTS.md`, `docs/DESIGN.md`, `docs/TASKS.md`) y es el puente hacia el capítulo 18. En la rama encontrarás también `docs/megaprompt-template.md`, la misma estructura con los campos por rellenar, lista para tu proyecto.

Reescribir un párrafo del brief es cuestión de minutos. Corregir el mismo error cuando ya se ha convertido en migrations, controllers y componentes significa tocar cada archivo al que se ha propagado.

## 17.3 Generar las especificaciones completas

El brief dice qué construyes y por qué. La spec dice cómo funciona cada pieza, en forma de contrato: el esquema tiene esas columnas o no las tiene, el endpoint responde con esa forma o está mal.

Un ejemplo con las etiquetas. El brief dice "los usuarios etiquetan las fotos con palabras clave libres". La spec final de Photogallery dice:

- tabla `tags` con `id` UUID, `name` VARCHAR(100) único, `slug` VARCHAR(120) único y timestamps gestionados por Laravel;
- el slug nace del nombre con `Str::slug()` en el hook `booted()` del modelo y, si hay colisión, recibe un sufijo numérico (`-2`, `-3`);
- las etiquetas son globales, sin `user_id`: dos usuarios que usan "sunset" apuntan al mismo registro;
- la pivot `photo_tag` tiene la clave primaria compuesta (`photo_id`, `tag_id`), un `created_at` y `ON DELETE CASCADE` en las dos foreign keys;
- `GET /api/v1/tags` devuelve todas las etiquetas con el recuento de fotos (`withCount('photos')`), sin paginación porque el conjunto es pequeño;
- `POST /tags` no existe: una etiqueta nueva se crea pasando `new_tags[]` al subir o modificar una foto.

Ninguna de estas líneas se deduce del brief, y con ellas Claude escribe migration, modelo, controller y tests sin hacerte preguntas.

### Del megaprompt a SPEC.md

En la rama hay dos specs. `SPEC-original.md` es la primera, generada a partir de un prompt más corto: unos 13 KB, tres tablas de aplicación más la pivot, un flag `is_favorite` en la foto, SQLite en desarrollo y PostgreSQL en producción.

![SPEC-original.md en VS Code en la tabla del stack, con Claude Code en el terminal de abajo](figures/cap-17/fig-01.png)

`SPEC.md` es la final, generada a partir del megaprompt y revisada después: unos 123 KB, casi 2.400 líneas en 15 secciones, desde el esquema de la base de datos hasta la disciplina de tests y commits, más un apéndice sobre las variables de entorno. Conservar también la primera versión tiene sentido: la comparación entre las dos muestra cuánto trabajo hacen las iteraciones.

![SPEC.md junto a su vista previa en Markdown: la tabla del stack con entradas separadas para desarrollo y producción](figures/cap-17/fig-02.png)

Generarlo todo de una vez a partir del megaprompt está bien. Revisarlo todo de una vez, no: si lees entero un documento de ese tamaño, acabas aprobando incoherencias que, sección a sección, verías enseguida. Así que la revisión avanza por áreas, en el orden en que las áreas dependen unas de otras: base de datos, API, autenticación, panel de administración y frontend, build workflow. Para cada área escribe un prompt de revisión, lee el diff y aprueba. Una sesión por área mantiene limpio el contexto; entre un área y otra usa `/clear`. Los prompts de revisión de la rama están en inglés (`docs/database-refinement.md`, `docs/api-refinement.md`, `docs/claude-code-build-workflow.md`); aquí los tienes traducidos.

### Spec de la base de datos: esquema y restricciones

```text
Revisa el esquema de la base de datos en SPEC.md. Para cada tabla comprueba que:
1. Cada columna tenga un tipo Y restricciones (nullable, default, unique,
   foreign key)
2. El comportamiento ON DELETE de las foreign keys esté especificado
   (cascade, set null, etc.)
3. La tabla pivot tenga una clave primaria compuesta
4. Todas las columnas de timestamp estén especificadas

Actualiza la spec con los detalles que falten.
```

Después lee el esquema como el DBA que tiene que aprobar las migrations. Los puntos que hay que comprobar uno por uno:

- ¿`photo_tag` tiene la clave primaria compuesta (`photo_id`, `tag_id`) y ningún `id` aparte? Con un id generado, el mismo par podría aparecer dos veces; la clave compuesta lo impide por construcción.
- ¿Cada foreign key declara `ON DELETE`? En Photogallery, borrar un álbum pone a `NULL` el `album_id` de sus fotos, que se quedan; borrar la foto usada como portada pone a `NULL` el `cover_photo_id` del álbum; borrar una foto elimina sus filas en `photo_tag`, mientras que las etiquetas se quedan.
- ¿Hay un índice en cada foreign key y en las columnas que se usan para filtrar y ordenar?
- ¿Quién escribe los timestamps? La spec final dice que `created_at` y `updated_at` los gestiona Eloquent: columnas nullable, sin default en la base de datos. Si la spec no dice nada, Claude elige por ti.
- ¿Hay dependencias circulares? `albums.cover_photo_id` apunta a `photos`, y `photos.album_id` apunta a `albums`. La spec lo resuelve con tres migrations: primero `albums` sin la foreign key de la portada, luego `photos` y, por último, una migration que añade la restricción. Sin esta nota, el primer `migrate:fresh` falla.

### Spec de la API: endpoints y convenciones

```text
Revisa la sección de la API. Para cada endpoint comprueba que:
1. Todos los parámetros de query de GET /photos estén enumerados con su tipo
2. El formato de la respuesta esté descrito (qué campos, qué relaciones
   anidadas)
3. Las respuestas de error estén especificadas (qué status codes, qué
   formato de mensaje)
4. El endpoint de upload especifique multipart/form-data y los nombres de los campos

Actualiza la spec.
```

Las convenciones se escriben una sola vez, al principio de la sección, y cada endpoint las hereda. En la spec final están en el apartado 6.0: base URL, content type, header `Authorization: Bearer`, rate limit por IP y por usuario, envelope `{ "data": ... }`, ETag en los recursos individuales. Cuando revises un dominio tras otro, haz que Claude relea ese apartado antes de tocar el resto, para que los dominios no acaben con convenciones ligeramente distintas:

```text
Lee la sección 6.0 de SPEC.md (envelope, paginación, formato de los
errores, rate limit). Después revisa los endpoints de los álbumes y
alinéalos con las mismas convenciones que los endpoints de las fotos.
```

### Spec de autenticación: tokens de Sanctum y un compromiso declarado

Filament usa la sesión estándar de Laravel con el guard `web`. La SPA usa Sanctum en modo token: los endpoints son `register`, `login`, `logout` y `me`, el login devuelve `{ "data": { "token": ..., "expires_at": ..., "user": ... } }`, el token dura 24 horas y Axios lo añade como header `Authorization: Bearer`.

La parte más útil de la sección es una decisión escrita junto con sus consecuencias. El token está en el `localStorage`, bajo la clave `pgp_token`, donde cualquier script inyectado mediante un ataque XSS puede leerlo. La alternativa más segura es el modo cookie de Sanctum, que cuesta un flujo CSRF más complicado. La spec elige el token y deja por escrito las mitigaciones: un TTL de 24 horas en lugar de 30 días, una Content Security Policy estricta en producción, `dangerouslySetInnerHTML` prohibido por una regla de ESLint, y tokens con habilidades limitadas (`photos:write`, `albums:write`) que no llegan a los permisos de administración. Y fija la condición para cambiar de idea: si el uso multiusuario pasa a ser el caso principal, se cambia a cookies. Escrita así, la decisión no vuelve a discutirse en cada sesión.

### Spec del panel de administración y del frontend

Antes de escribir una línea de React, la spec tiene que decir qué páginas requieren login, cómo es la jerarquía de componentes, dónde vive el estado del servidor y dónde el local, y cómo se gestionan los errores y la falta de red. El prompt de revisión pide rutas, componentes con props tipadas, los flujos principales paso a paso y, para cada query de TanStack Query, las mutations que la invalidan.

La spec final responde con cinco rutas (`/`, `/favorites`, `/albums/:albumId`, `/login` y una página 404), cada página cargada con `React.lazy`, el estado del servidor solo en TanStack Query y un cliente Axios con `baseURL: '/api/v1'` que, ante un 401, borra el token y lleva a `/login`.

Para Filament la spec baja al mismo nivel, resource por resource. La tabla de `PhotoResource` muestra miniatura, título, álbum, etiquetas como badges, el toggle de favoritas y el estado de procesamiento; los filtros cubren álbum, etiquetas, favoritas, fechas y estado; las bulk actions borran, asignan a un álbum y relanzan el procesamiento. El dashboard tiene tres widgets, entre ellos el monitor de la cola.

![La vista previa de SPEC-original.md en la sección del panel Filament: resources, filtros y bulk actions](figures/cap-17/fig-03.png)

### El build workflow

La última sección que hay que pedir es el orden de construcción:

```text
Añade a la spec una sección "Claude Code Build Workflow".
Enumera el orden exacto de construcción, fase por fase:

Fase 1: base del backend (modelos, migrations, seed)
Fase 2: capa de API (controllers, rutas, resources, requests)
Fase 3: panel de administración Filament (resources, widgets, dashboard)
Fase 4: setup del frontend React (scaffold, Tailwind v4, servicio de API)
Fase 5: componentes React (cuadrícula, lightbox, upload, sidebar, teclado)
Fase 6: pipeline de procesamiento de imágenes (job, cola, batch)
[... fases 7-12: monitorización de la cola, migración a AWS, hooks, tests,
Git + PR, desarrollo multiagente en paralelo ...]
Fase 13: spec check final + deploy

Para cada fase escribe el prompt exacto que hay que darle a Claude Code.
```

El resultado es la sección 13 de `SPEC.md`, el runbook operativo. Cada fase tiene un objetivo, un prompt para pegar en Claude Code, un bloque de verificación que ejecutar y el mensaje del commit final: la Fase 1, por ejemplo, se cierra con `feat(backend): database schema, models, and seeders`. Todos los prompts a partir de la Fase 2 van precedidos del mismo preámbulo, aquí traducido:

```text
Estás trabajando en este repo. La spec es SPEC.md en la raíz y tiene
autoridad. Lee las secciones citadas en el prompt y síguelas al pie de la letra.
NO inventes campos, endpoints ni rutas de archivos que no estén en la spec.
Ejecuta la verificación antes de dar el trabajo por terminado. Al final
haz commit con el mensaje indicado en el prompt.
```

En el capítulo 18 estas fases se convierten en `docs/TASKS.md`: 124 tareas atómicas en 14 fases, con dependencias e indicaciones sobre qué puede correr en paralelo.

### Qué hay en la rama

Al final de esta fase, la rama `book/cap-11-prompts-and-spec` contiene diez archivos:

```text
CLAUDE.md
SPEC-original.md
SPEC.md
docs/
  PROMPT.md
  megaprompt-template.md
  database-refinement.md
  api-refinement.md
  claude-code-build-workflow.md
  SPEC-REVIEW.md
  SPEC-VALIDATION.md
```

`SPEC-REVIEW.md` y `SPEC-VALIDATION.md` son el producto de la sección 17.4. `CLAUDE.md` (capítulo 7) dice cómo se trabaja en el repo y remite a `SPEC.md` para saber qué construir. Una de sus reglas críticas, "Ask before deviating", le pide a Claude que señale un punto de la spec que parezca incorrecto en lugar de corregirlo en silencio.

## 17.4 Iterar las specs: una base de datos y una API más sólidas

La primera spec de Claude es un buen punto de partida y nada más. Como un programador experto en una primera pasada, produce algo correcto en lo sustancial e incompleto en los detalles que da la experiencia: tipos explícitos, restricciones, índices, una forma de respuesta igual para todos los endpoints, una paginación que aguanta cuando crecen las filas. Una relectura que termina con "parece que todo está bien" solo dice que no hay errores evidentes. Los problemas de verdad están en las suposiciones implícitas, como una columna sin `NOT NULL` o un endpoint sin el caso 403.

### Iteración 1: tipos y restricciones explícitos

La forma más rápida de ver qué hace esta iteración es comparar la tabla `photos` en las dos specs de la rama. Algunas filas de `SPEC-original.md`:

```text
| id          | uuid        | primary key, default uuid() |
| path        | string(255) | not null (storage path)     |
| file_size   | integer     | nullable (bytes)            |
| is_favorite | boolean     | default false               |
```

Las filas correspondientes, y las nuevas, en `SPEC.md`:

```text
| id                  | CHAR(36)         | NOT NULL | —         | PRIMARY KEY (UUID v7) |
| user_id             | CHAR(36)         | NOT NULL | —         | FK users(id), ON DELETE CASCADE |
| original_path       | VARCHAR(500)     | NOT NULL | —         | disco privado, nunca servido en público |
| thumbnail_path      | VARCHAR(500)     | NULL     | NULL      | lo escribe el job ProcessPhoto |
| file_size           | BIGINT UNSIGNED  | NOT NULL | —         | bytes |
| processing_status   | ENUM('pending','processing','completed','failed') | NOT NULL | 'pending' | |
| processing_attempts | TINYINT UNSIGNED | NOT NULL | 0         | |
| processing_error    | TEXT             | NULL     | NULL      | mensaje de la excepción |
```

Ha aparecido el propietario, porque el modelo de autorización dice que cada uno modifica solo sus propias fotos. La ruta única se ha dividido entre el original privado y los tres tamaños públicos. `file_size` se ha vuelto obligatorio y lo bastante grande, y el estado de procesamiento tiene sus intentos y su error. Cada cambio viene de un requisito que ya estaba en el brief y todavía no había llegado al esquema. Después de cada prompt de revisión lee el diff, no el resumen que hace Claude.

### Iteración 2: índices para las consultas frecuentes

```text
Relee la sección 4 de SPEC.md y añade los índices que faltan para
las consultas más frecuentes de Photogallery:
- fotos de un álbum, de la más reciente a la más antigua: INDEX(album_id, created_at)
- ordenación con las favoritas primero: INDEX(is_favorite, created_at)
- dashboard de la cola en Filament: INDEX(processing_status, created_at)
- ordenación por defecto por fecha: INDEX(created_at)
- búsqueda por título y descripción: FULLTEXT(title, description),
  consultado con MATCH ... AGAINST

Añade también las restricciones de integridad: UNIQUE en users.email,
UNIQUE en tags.name y tags.slug, UNIQUE compuesto (user_id, name)
en albums.
```

El FULLTEXT sustituye a un `LIKE '%palabra%'`, que significa leer la tabla entera. El nombre del álbum es único por usuario porque dos usuarios distintos tienen que poder tener los dos un álbum "Viajes".

### Iteración 3: paginación por cursor

La paginación por offset (`?page=5&per_page=24`) tiene un problema conocido. Para llegar a la página pedida, la base de datos tiene que recorrer y descartar todas las filas anteriores:

```sql
SELECT * FROM photos ORDER BY created_at DESC LIMIT 24 OFFSET 100000;
```

Esta consulta lee 100.024 filas para devolver 24, y la review de la spec de Photogallery señala el problema ya a partir de las 10.000 fotos. Con la paginación por cursor, el cliente pasa un cursor opaco con la posición del último elemento visto, y el backend lo traduce en una condición `WHERE` sobre columnas indexadas: el coste es el mismo en cualquier punto de la colección.

```text
Actualiza los endpoints de listado en SPEC.md para usar la paginación
por cursor (cursorPaginate() de Laravel) en lugar de la paginación por offset.

- El parámetro de query pasa a ser `cursor` (cadena opaca, opcional)
- `per_page`: por defecto 24, mínimo 1, máximo 100
- La respuesta incluye `links` (first, next, prev) y `meta` con
  per_page, next_cursor, prev_cursor y path
- Sin recuento total: con cursores no hace falta

Las claves primarias tienen que ser UUID v7, ordenables por fecha de
creación. El trait HasUuids genera v4 por defecto: hay que sobrescribirlo.
```

La restricción de los UUID v7 está ahí por los cursores. Un UUID v4 es aleatorio; un v7 empieza por el timestamp de creación. Con el v7, `ORDER BY id` equivale en la práctica a `ORDER BY created_at`, y los cursores se mantienen estables mientras llegan fotos nuevas. Photogallery lo consigue con un trait, `HasUuidV7`, que sobrescribe `newUniqueId()` y devuelve `Str::uuid7()`.

### Iteración 4: un contrato REST uniforme

La forma de las respuestas parece un detalle hasta que escribes el frontend, que con envelopes distintos se convierte en una colección de casos especiales. En los primeros borradores de Photogallery, el login y las favoritas respondían sin envelope; la spec final envuelve cada payload en `{ "data": ... }`, sin excepciones.

```text
Revisa todos los endpoints de SPEC.md como un contrato REST:
1. Cada respuesta de éxito va envuelta en { "data": ... }, también el login,
   el registro y las favoritas
2. Nada de toggles no idempotentes: la favorita pasa a ser
   PUT /photos/{id}/favorite (añade) y DELETE /photos/{id}/favorite
   (quita), ambos 204 y seguros de repetir
3. Un solo endpoint de upload, POST /photos, para 1-20 archivos: el cliente
   no tiene que elegir entre upload individual y en lote
4. Las operaciones asíncronas responden 202 Accepted con el header Location
5. Cada endpoint enumera sus propios códigos de error además de los
   universales (401, 429, 500)
```

Para los errores, la spec mantiene el formato estándar de Laravel: un campo `message` y, para el 422, un objeto `errors` con los mensajes por campo. Lo produce el exception handler en `bootstrap/app.php`, y un middleware fuerza JSON en `/api/*` para que una página de error HTML no llegue nunca a la SPA. La tabla de errores fija los casos: 413 por encima de 10 MB, 415 para un formato distinto de JPG, PNG y WebP, 403 cuando faltan la habilidad del token o la propiedad del recurso.

### La review completa de la spec

Después de las iteraciones por área quedan los problemas que nacen del cruce entre secciones. Para esos hace falta una review del documento entero:

```text
Revisa SPEC.md frente a los principios SOLID, REST y KISS, más las buenas
prácticas específicas de backend (Laravel), frontend (React y TypeScript)
y base de datos (MySQL/Postgres).

Para cada problema escribe un ID, la sección de la spec, el principio
violado y el fix propuesto. Agrupa por área.

Añade:
- un plan de paralelización: dependencias entre las fases del build
  workflow y qué puede correr en paralelo
- una disciplina de tests y commits: qué es una tarea, qué test hace falta
  antes del commit para cada tipo de tarea, convenciones de los mensajes

Guarda el resultado en docs/SPEC-REVIEW.md. No modifiques todavía SPEC.md.
```

La review de la rama, con fecha del 26 de abril de 2026, encontró, entre otras cosas:

- el `PhotoResource` de Filament y el `PhotoResource` de las API Resources de Laravel tenían el mismo nombre: los segundos pasan a ser `PhotoData`, `AlbumData` y `TagData`;
- `StorageManager` y `ProcessBatchUpload` aparecían en la estructura de carpetas sin que ninguna sección los usara, y se eliminaron;
- un worker de la cola con `--timeout=120` corre el riesgo de interrumpir el resize de una imagen grande, así que hace falta un presupuesto explícito de tamaños;
- el lightbox y los modales no tenían focus trap, y faltaban los error boundaries.

Las correcciones entraron en siete clusters, cada uno como un cambio separado de `SPEC.md`. Así la spec sigue siendo la única fuente de verdad, y `SPEC-REVIEW.md` se queda en el repo como registro de las decisiones con sus motivos. No estás obligado a aceptarlo todo: para cada punto decide si se hace ahora, después o nunca, y escribe la decisión. El plan de paralelización de la review, con sus waves, vuelve en el capítulo 20.

### Cuándo parar

Las specs nunca serán perfectas, y perseguir la perfección es tan antipatrón como saltárselas. Una prueba práctica: están listas cuando sabes responder a preguntas como estas sin abrir el archivo.

- ¿Cómo se llama la columna con la ruta del original? `original_path`, en el disco privado.
- ¿Qué pasa con las fotos cuando borro un álbum? Se quedan, con `album_id` a `NULL`, y la respuesta es un `204`.
- ¿Qué hace el frontend cuando recibe un 401? Borra el token y lleva a `/login`.

Si una respuesta te obliga a buscar, esa sección todavía necesita trabajo. La misma prueba se la puedes hacer a Claude. En la rama está `docs/SPEC-VALIDATION.md`, un control de comprensión hecho el 25 de abril, el día antes de la review: conviene hacerlo antes y repetirlo después de cada ronda de cambios. El prompt es de este tipo:

```text
Responde a estas preguntas usando solo SPEC.md. Para cada respuesta cita
la sección y reléela del archivo, no respondas de memoria.
1. ¿Cuántas tablas tiene la base de datos, y con qué columnas?
2. ¿Cuántos endpoints de API hay? Enuméralos.
3. ¿Qué resources y widgets tiene el panel Filament?
4. ¿Cuáles son los tres tamaños de las imágenes, con ancho y calidad?
5. ¿Cuáles son los atajos de teclado?
6. ¿Qué driver de cola se usa en local y cuál en producción?
7. Describe el flujo completo del upload de una foto.
8. ¿Qué pasa cuando borro un álbum? ¿Y cuando borro una foto?
9. ¿Cómo funciona el toggle mensual/anual de los precios?
```

Claude contó nueve tablas (cinco de aplicación y cuatro del framework), dieciocho endpoints, tres resources y tres widgets, cada uno con su sección. La pregunta 9 es una trampa: Photogallery no tiene precios ni suscripciones; el toggle mensual/anual pertenece a la landing page del capítulo 16. Claude respondió que en la spec no aparece y que probablemente se refiere al otro proyecto, sin mezclarlos. Si en cambio se inventa una respuesta, está trabajando de memoria o sobre un contexto equivocado, y te conviene saberlo antes de la ejecución.

### Guardar las specs como checkpoint

Antes de pasar a la implementación, haz commit de las specs: son un artefacto para compartir con los compañeros y para releer meses después como documentación del sistema.

```bash
git init
git add CLAUDE.md SPEC.md SPEC-original.md docs/
git commit -m "docs(spec): SPEC.md revisada y validada para Photogallery v1"
```

El mensaje sigue las convenciones que la propia spec fija en la sección 15 (tipo, scope, asunto). De aquí en adelante, cada cambio en las specs pasa por una revisión deliberada.

## 17.5 Antipatrón: saltarse las specs e ir directo al código

Tienes el stack en la cabeza y ganas de ver algo funcionando: le pides el backend a Claude enseguida, y las specs ya las arreglarás después. Haz el experimento:

```text
Crea un backend Laravel completo para una galería de fotos.
Los usuarios inician sesión, suben fotos, las organizan en álbumes y las etiquetan.
```

Claude genera código, probablemente decente. A los veinte minutos tienes modelos, migrations, algunos controllers y el login. Parece un gran paso adelante, hasta que miras los detalles.

El esquema es una estimación: `id`, `filename`, `path`, `user_id`. Falta el estado de procesamiento, porque nadie ha dicho que el procesamiento es asíncrono, y faltan las rutas de los tres tamaños. Puede que la columna del propietario esté, pero las policies que la hacen cumplir no. El upload es síncrono y el resize está en el controller: con una foto pequeña funciona; con veinte fotos de 10 MB la petición da timeout.

La paginación es por offset, porque es el default más obvio, y te das cuenta cuando las fotos crecen. Los tests cubren el happy path de los endpoints recién escritos: sin una spec con la que comparar, Claude no tiene forma de saber qué casos de error importan.

### El coste del retrabajo

El problema es que el código es imperfecto de forma coherente: si miles de líneas siguen la misma arquitectura equivocada, corriges el patrón en todos los sitios donde se ha aplicado. Y los errores se ven con el trabajo ya avanzado:

- Construyes la galería y descubres que algunos endpoints responden `{ "photo": {...} }`, otros `{ "data": {...} }` y otros un array desnudo. O normalizas el cliente o mantienes un parser por endpoint.
- Llegas al deploy en ECS con varias tasks detrás del load balancer y descubres que las fotos acaban en el disco local del contenedor que recibió la petición. El worker que tiene que procesarlas corre en otro sitio y no las encuentra, y hay que reescribir el almacenamiento.
- Añades las favoritas por usuario y descubres que `is_favorite` es una columna de la foto, es decir, una favorita compartida por todos.

El último caso le pasó también a Photogallery, con las specs en la mano. `SPEC.md` tiene `is_favorite` en la tabla `photos`; más adelante las favoritas pasan a ser por usuario, con una tabla pivot, y en `docs/TASKS.md` hay una fase dedicada, la 6.5 ("Favorites refactor"). Aquí el cambio parte de la spec, que dice qué migrations, endpoints y componentes hay que tocar. Lo verás en el capítulo 21.

Sin specs, llegado ese punto, o sigues adelante con la arquitectura equivocada y acumulas deuda técnica, o empiezas de cero y pierdes el tiempo del primer intento más el del refactoring. Los dos caminos se evitan con uno o dos días de trabajo en las specs antes de tocar el código.

### El Spec Driven Development como respuesta

El Spec Driven Development, que el capítulo 18 trata a fondo, aborda el problema en cuatro fases:

1. Primero las specs, revisadas hasta que estén claras: la fase de este capítulo.
2. Un plan a partir de las specs: tareas pequeñas y verificables, con criterios de aceptación sacados de las specs.
3. Código a partir del plan: si aparece un caso no cubierto, primero se actualiza la spec y después el código (capítulo 19).
4. Verificación contra la spec: en cada fase el código hace lo que describe la spec, ni más ni menos (capítulo 22).

El resultado es código que puedes pasar a otro desarrollador, o a Claude en una sesión nueva, sabiendo que las specs bastan para seguir.

### Cuando las specs cambian

Las specs cambian, y es normal: un requisito resulta ambiguo, una restricción de rendimiento sale de los tests, el cliente cambia de idea sobre los álbumes. Con specs, el cambio es deliberado. Actualizas el archivo, haces commit con un mensaje que explica el porqué, y encuentras las consecuencias aguas abajo de forma sistemática. Sin specs, el cambio se queda en una conversación, y tres semanas después nadie recuerda por qué existe esa columna, ni se atreve a tocarla. La memoria automática de Claude Code (capítulo 15) conserva preferencias y correcciones, pero el registro de las decisiones de diseño tiene que estar en un archivo versionado con Git, donde lo lean todos: tú, el equipo y la próxima sesión de Claude.

## Resumen {.unlisted}

- El primer prompt describe el problema y pide alternativas; el stack se elige después, con motivos sacados de los requisitos.
- Photogallery usa Laravel 13 como API REST bajo `/api/v1`, Filament v5 para la administración, React 19 + Vite 6 + Tailwind CSS v4 para la SPA y tokens de Sanctum para la autenticación.
- El brief se itera (primer borrador, fuera de alcance, upload y pipeline) y la versión final se convierte en el megaprompt `docs/PROMPT.md`.
- La spec se puede generar de una vez, pero se revisa por áreas: base de datos, API, autenticación, frontend, build workflow.
- Una review frente a SOLID, REST y KISS y un control de comprensión con una pregunta trampa te dicen cuándo está lista la spec.
- Saltarse las specs desplaza los problemas al trabajo ya avanzado, cuando corregirlos significa tocar cada archivo.

## Ejercicio {.unlisted}

Elige un proyecto personal pequeño: un registro de lecturas, un gestor de notas, un portfolio. Después:

1. Abre Claude Code en una carpeta vacía y escribe el prompt de los requisitos, sin stack.
2. Pide que te proponga dos o tres stacks, haz al menos dos preguntas de seguimiento y elige uno con una justificación escrita.
3. Itera el brief durante al menos tres rondas, incluida una sobre lo que queda fuera de alcance, partiendo del prompt reutilizable de la sección 17.2 o de `docs/megaprompt-template.md`.
4. Genera la spec y revisa al menos la base de datos y la API, con un prompt de revisión para cada una.
5. Prepara un control de comprensión con al menos cinco preguntas, una de ellas trampa.
6. Haz commit de la spec, los prompts y la review.

El ejercicio está terminado cuando en el repo está el commit con la spec y Claude, en una sesión nueva, responde a todas las preguntas citando la sección correcta y dice que la pregunta trampa no tiene respuesta en la spec. Tiempo estimado: 60-90 minutos. Para comparar tu trabajo con el del libro, clona la rama del companion:

```bash
git clone -b book/cap-11-prompts-and-spec https://github.com/hidran/claude-code-book-photogallery.git
```
