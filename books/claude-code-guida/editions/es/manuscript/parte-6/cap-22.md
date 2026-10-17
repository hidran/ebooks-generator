# Capítulo 22. QA previa al deploy, /code-review y revisión multi-LLM

::: {.chapter-goals}
[Qué aprenderás]{.callout-title}

A preparar la Photogallery para producción con una checklist de QA que de verdad bloquea el deploy, a dar con las tareas huérfanas que quedaron tras las oleadas, a usar la revisión integrada de Claude Code (`/code-review`, `REVIEW.md`, ultrareview) y a saber cuándo sigue haciendo falta un segundo modelo como Gemini, Codex o Kimi. Cerramos con una auditoría de seguridad dedicada: middleware, CSP, HTTPS y secrets.

[Requisitos previos]{.callout-title}

La Photogallery tal como queda al final del capítulo 21 (rama `book/cap-14-phases-complete`), con los tests en verde. Para ultrareview necesitas una cuenta de claude.ai; para la revisión multi-LLM, acceso a por lo menos un segundo modelo.

:::

En local, un bug es una molestia: lo ves, lo corriges, haces push y nadie se entera. En producción, ese mismo bug puede significar fotos de un usuario visibles para otro, sesiones comprometidas, datos perdidos y un correo de disculpas a los usuarios. Corregir un problema durante el desarrollo cuesta una hora; después del deploy hay que sumarle el incidente, el rollback, la comunicación y el post-mortem, y la hora se convierte en unos cuantos días.

Por eso las últimas 24-48 horas antes del lanzamiento son para la QA, en el orden en que la hago con la Photogallery: checklist, tareas huérfanas, revisión del código y, por último, auditoría de seguridad.

## 22.1 La checklist de QA previa al deploy

Una checklist previa al deploy solo tiene sentido si es vinculante: si un punto no pasa, el deploy no sale. Una lista que puedes saltarte cuando vas con prisa es una lista de deseos, y el día del lanzamiento siempre vas con prisa.

La paso uno o dos días antes del deploy, cuando todavía hay tiempo para corregir con calma. El mismo día ya es tarde.

### Flujos funcionales

Los tests automáticos comprueban lo que se te ocurrió probar. La prueba manual encuentra el resto. Antes del deploy recorro a mano estos flujos:

- registro, con la verificación del correo si la hay
- login y logout
- recuperación de contraseña
- cada operación CRUD principal (fotos, álbumes, etiquetas, fotos favoritas)
- subida con archivos válidos, archivos de más de 10 MB y archivos con la extensión equivocada
- paginación y filtros
- los flujos del panel de administración de Filament

Cada flujo lo pruebo tres veces: como usuario no autenticado, como usuario autenticado y como admin. Los bugs de autorización aparecen casi siempre cuando un rol intenta hacer algo que no debería poder hacer.

Luego, los errores. Cada camino de error tiene que acabar en una UI razonable: nada de pantalla en blanco, nada de volcados de JSON, nada de stack traces a la vista del usuario. Cada formulario valida en el cliente por la UX y en el servidor por la seguridad, porque la validación del navegador se salta en un segundo. Las páginas 404 y 500 tienen que existir y decir algo útil. Dos comprobaciones rápidas desde la terminal:

```bash
# Una página que no existe debe responder 404 (no 200 con una página en blanco)
curl -s -o /dev/null -w "%{http_code}\n" https://tua-app.dev/pagina-che-non-esiste

# Un endpoint protegido sin token debe responder 401 (no 500)
curl -s -o /dev/null -w "%{http_code}\n" https://tua-app.dev/api/v1/auth/me
```

### Rendimiento: números, no impresiones

"Parece rápido" no es una métrica. Para el frontend empiezo por Lighthouse y apunto a una puntuación por encima de 85 en las páginas clave (galería, álbum, detalle de la foto). Por debajo de 70 lo normal es que también sufran los Core Web Vitals, que son los que Google usa en el ranking.

```bash
# Lighthouse desde la línea de comandos (necesitas Chrome instalado)
npx lighthouse https://tua-app.dev/pagina-chiave \
  --output=json \
  --output-path=./lighthouse-report.json \
  --chrome-flags="--headless"
```

En la API miro la mediana de las llamadas principales, que tiene que quedarse por debajo de 200 ms. El percentil 99 lo optimizas después: la mediana es la experiencia de la mayoría de los usuarios. Este script lanza cien peticiones al listado de fotos e imprime la mediana real, no la media:

```bash
# Latencia del endpoint principal en 100 peticiones: imprime la mediana
for i in $(seq 1 100); do
  curl -s -o /dev/null -w "%{time_total}\n" https://tua-app.dev/api/v1/photos
done | sort -n | awk '{t[NR]=$1} END {print "Mediana:", t[int((NR+1)/2)] "s"}'
```

Con los assets, las reglas son pocas. Las imágenes que se sirven a los usuarios van en WebP o AVIF, no en JPEG o PNG a resolución completa. CSS y JavaScript, comprimidos con gzip o brotli. Una foto de 4 MB en la cuadrícula de la galería es un bug de rendimiento, aunque exista el pipeline de miniaturas: basta con un componente que apunte al original en lugar de a la miniatura.

En la base de datos, cada consulta frecuente necesita su índice. Si `WHERE user_id = ?` se ejecuta en cada petición autenticada, `user_id` tiene que estar indexada; si no, la consulta recorre la tabla entera y va cada vez más lenta a medida que crecen los datos. En la Photogallery pasó de verdad: la migration de `photos` usaba `foreignUuid('user_id')->constrained()`, que en SQLite y PostgreSQL no crea el índice de apoyo. Lo encontró la revisión del pull request de la fase 1, y la corrección está en `docs/REVIEW-FIXES.md` (punto F1).

```sql
-- Comprueba el índice (MySQL/MariaDB)
EXPLAIN SELECT * FROM photos WHERE user_id = 'uuid-di-un-utente' ORDER BY created_at DESC LIMIT 20;
-- Si la columna "type" vale "ALL", falta el índice
```

### Seguridad básica

Estas son las comprobaciones que haces en media hora. La auditoría completa llega en la sección 22.6.

- Rutas de admin y mutaciones: cada endpoint que modifica datos o lee datos de otros usuarios exige autenticación y control de permisos. Siempre, no casi siempre. Prueba cada endpoint de admin con el token de un usuario normal y comprueba que responde 403.
- Validación de la entrada: todo lo que llega de fuera (parámetros de URL, body JSON, archivos, cabeceras) pasa por una Form Request en Laravel, o por un esquema Zod en el lado de TypeScript.
- CSRF: si la autenticación usa cookies, el CSRF es un riesgo real. La Photogallery usa tokens Bearer de Sanctum en la API, pero el panel de Filament usa la sesión web: comprueba que la protección esté activa ahí, sobre todo después de un refactoring.
- Rate limiting en el login y el registro. Sin él, un atacante prueba miles de combinaciones de contraseñas en pocas horas.

### Integridad de los datos: el backup que nadie prueba

Si esta noche se corrompe la base de datos, ¿podrás restaurarla mañana por la mañana? No vale "en teoría sí, el backup es automático": ¿has hecho alguna vez un restore desde ese backup? Antes del deploy haz uno de prueba en una base de datos temporal. Si no funciona ahora, tampoco funcionará en plena emergencia.

```bash
# Restore de prueba desde un backup en S3 (adáptalo a tu setup)
aws s3 cp s3://tuo-bucket/backup-latest.sql.gz ./restore-test.sql.gz
gunzip restore-test.sql.gz
mysql -u root -p test_restore < restore-test.sql

# Comprueba que las tablas existen y tienen datos razonables
mysql -u root -p test_restore -e "SELECT COUNT(*) FROM users;"
```

Prueba también las migrations contra una copia de la base de datos de producción, o contra un dump anonimizado reciente, no solo contra la base de datos local. Con datos reales, las migrations fallan de maneras que en desarrollo no ves. Y escribe el plan de rollback: si el deploy sale mal, qué haces y cuánto tardas en volver a la versión anterior. Tiene que estar por escrito, no en tu cabeza.

### Observabilidad

Antes del deploy compruebo que estén:

- logs estructurados en JSON, que puedes filtrar, agregar y usar para las alertas (un `console.log("errore!")` en producción no le sirve a nadie)
- seguimiento de errores con Sentry, Bugsnag o similares, para que cada excepción no controlada te llegue a ti antes que a un usuario
- un endpoint de health que compruebe las dependencias reales
- tres métricas básicas en CloudWatch o Grafana: número de peticiones, tasa de errores y latencia; con diez segundos te basta para saber si el deploy ha empeorado algo

El endpoint de health es el que consulta el load balancer para decidir si un contenedor está vivo. En la Photogallery es `GET /api/v1/health` (DESIGN §6.5): escribe, vuelve a leer y borra un archivo marcador en el disco de las fotos, y consulta la tabla `failed_jobs` para comprobar la conexión de la cola. Responde 200 si todo va bien y 503 con el detalle si algo falla:

```json
{
  "status": "ok",
  "storage": "ok",
  "queue": "ok"
}
```

La checklist completa para tu stack te la puede generar Claude. Yo la uso como punto de partida y luego la recorto.

::: {.callout .callout-prompt}
[Prompt reutilizable]{.callout-title}

```text
Eres un QA engineer senior. Mi proyecto es [describe el stack y el tipo de app].
Genera una checklist previa al deploy organizada por categoría:
Funcional, Rendimiento, Seguridad, Integridad de datos, Observabilidad.
Para cada punto indica: qué comprobar, cómo comprobarlo (comando o acción),
criterio de éxito. Formato: tabla Markdown.
```
:::

## 22.2 A la caza de tareas huérfanas

Todo proyecto desarrollado con Spec Driven Development y un agente tiene el mismo problema silencioso: las tareas huérfanas. Funcionalidades a medio implementar, endpoints registrados pero vacíos, componentes creados y nunca importados. Código que existe y pasa los tests, porque los tests no comprueban lo que no sabes que falta.

Nacen de dos maneras. La primera es una sesión que se corta a mitad de una tarea: un `/clear`, una compactación, una sesión en segundo plano cerrada demasiado pronto. Cuando retomas, Claude no recuerda hasta dónde había llegado, y si en `docs/TASKS.md` hay una tarea marcada como en curso, puede darla por terminada sin haberla cerrado de verdad.

La segunda es más sutil: una tarea se marca como hecha porque la parte principal funciona, pero algún detalle nunca llega (la validación de un caso límite, la gestión del 413, la vista móvil). Con un agente que produce código a esta velocidad, estos huecos se acumulan sin que nadie los vea.

### Auditoría con grep

La primera pasada es mecánica: buscar en el código las señales de trabajo incompleto. Lanza estos comandos desde la raíz del repositorio.

```bash
# TODO, FIXME, HACK, XXX y stubs (sin node_modules, vendor ni build)
grep -rn \
  --include='*.ts' --include='*.tsx' --include='*.js' --include='*.jsx' \
  --include='*.php' --include='*.py' \
  -E "(TODO|FIXME|XXX|HACK|placeholder|implement me|not implemented)" \
  --exclude-dir={node_modules,vendor,.git,dist,build} \
  .
```

Hay que leer cada resultado. Algunos TODO son optimizaciones futuras legítimas, otros son huecos funcionales, y la diferencia solo la ves por el contexto. Después busco los endpoints que devuelven vacío:

```bash
# Controllers que devuelven null, arrays vacíos o un TODO
grep -rn "return null" backend/app/Http/Controllers/
grep -rn "return \[\]" backend/app/Http/Controllers/
grep -rn "// TODO: implement" backend/app/
```

Para el frontend, un script de Node que lista los componentes que nadie importa. Se lanza desde la carpeta `frontend/` y necesita el paquete `glob` (`npm install -D glob`):

```bash
# Componentes creados pero nunca importados
node -e "
const fs = require('fs');
const glob = require('glob');
const path = require('path');

const components = glob.sync('src/components/**/*.{tsx,jsx}');
const allCode = glob.sync('src/**/*.{tsx,jsx,ts,js}')
  .filter(f => !f.includes('.test.'))
  .map(f => fs.readFileSync(f, 'utf8'))
  .join('\n');

components.forEach(comp => {
  const name = path.basename(comp, path.extname(comp));
  if (!allCode.includes('/' + name) && !allCode.includes(name + \"'\")) {
    console.log('Componente non importato:', comp);
  }
});
"
```

Para el backend busco las columnas que añaden las migrations y que casi no aparecen en el código. Desde `backend/`:

```bash
# Columnas declaradas en las migrations
grep -hE -e "->(string|integer|boolean|text|json)\(" database/migrations/*.php \
  | grep -oP "\('\K[^']+" | sort -u > migration_columns.txt

# Cuántas veces aparece cada una en app/
while read col; do
  count=$(grep -rn "$col" app/ --include="*.php" | wc -l)
  if [ "$count" -lt 2 ]; then
    echo "Colonna probabilmente orfana: $col (trovata $count volte)"
  fi
done < migration_columns.txt
```

### Un subagente que caza huérfanos

grep encuentra patrones de texto. Un subagente (capítulo 10) lee el proyecto entero y razona sobre el contexto: se da cuenta de que un endpoint se llama `export` pero no exporta nada, algo que ningún grep te va a decir. Le paso este prompt:

```text
Actúa como un senior software engineer que hace una auditoría de calidad
previa al deploy. Analiza el proyecto entero (backend + frontend) y busca:

1. Funcionalidades implementadas a medias (endpoints que no hacen lo
   que sugiere su nombre, componentes con funcionalidad comentada,
   formularios sin handler)

2. Código huérfano (funciones nunca llamadas, componentes nunca importados,
   migrations con columnas sin usar, rutas registradas pero no implementadas)

3. Stubs y placeholders (return null, throw new Error("not implemented"),
   TODO sin fecha ni responsable)

Para cada hallazgo, indica:
- Archivo y número de línea
- Descripción del problema
- Probabilidad de que haya que completarlo (alta/media/baja)
- Alternativa: ¿eliminarlo?

Salida: tabla Markdown ordenada por probabilidad de completarlo.
```

En la Photogallery esta auditoría encontró cuatro cosas:

- un componente Lightbox duplicado, dos versiones casi idénticas de las que una no se usaba
- un método `purge` en el servicio de fotos al que nadie llamaba
- una ruta `GET /api/v1/photos/export` registrada en el router, con un controller que solo contenía el comentario `// TODO: CSV export`
- tres etiquetas `<meta>` de Open Graph en la plantilla HTML que apuntaban a propiedades que nunca recibían valor

### La regla de las tres D

Para cada huérfano elijo uno de tres destinos.

Delete. Si la funcionalidad no forma parte del MVP y no hay un plan concreto para hacerla, el código muerto se borra. Es código que nadie mantiene y nadie prueba. Un endpoint vacío que responde 200 es peor que un endpoint que no existe, porque promete una funcionalidad que no está.

Complete. Si la funcionalidad está en el MVP pero a medias, la terminas ahora, no después del deploy. Una subida sin validación del tipo MIME es una vulnerabilidad abierta, aunque todo lo demás funcione.

Document and defer. Si la funcionalidad no está en el MVP pero tiene sentido más adelante, abre una issue con todos los detalles y quita el esqueleto de la rama de deploy.

Cuando hay muchos huérfanos, le pido a Claude que proponga la decisión:

```text
He encontrado estos elementos huérfanos en el proyecto:
[lista de hallazgos]

Para cada uno, dame una recomendación: Delete / Complete / Document and Defer.
Justifica la elección según: impacto en el MVP, riesgo de dejarlo como está,
coste estimado de completarlo ahora frente a después.
```

## 22.3 La revisión integrada de Claude Code

En el capítulo 19 hicimos la code review con prompts escritos a mano y con el revisor de Superpowers. Sigue funcionando, y sigue siendo la forma adecuada de hacer una revisión guiada por la spec. Mientras tanto, Claude Code ha incorporado herramientas de revisión propias: un comando local, una revisión a fondo en la nube hecha por varios agentes y una revisión automática de los pull requests en GitHub. Son la primera línea de defensa, la que usas en cada push.

### `/code-review` en local

`/code-review` (alias `/review`) revisa los commits de la rama que todavía no están en el remoto, más los cambios sin commit. Busca bugs de corrección, es decir, lo que rompe el programa, no el estilo. Se ejecuta como subagente en segundo plano con su propio contexto: no llena la conversación y mientras tanto puedes seguir trabajando. Los resultados llegan cuando termina, con archivo, línea y gravedad de cada problema.

Para asegurarme de que encuentre algo, en la Photogallery meto dos defectos a propósito en una rama de prueba: quito la llamada `$this->authorize('update', $photo)` de `PhotoController::update` y la regla `mimes:jpg,jpeg,png,webp` de `StorePhotosRequest`. Hago commit y lanzo la revisión:

```bash
git switch -c review/demo-bug
# ... introduce los dos defectos y luego:
git commit -am "demo: due difetti per la review"
```

```text
/code-review high main...review/demo-bug
```

El comando acepta un nivel de effort y un objetivo. El effort va de `low` a `max` (`low`, `medium`, `high`, `xhigh`, `max`): con `low` solo informa de los problemas de los que está más seguro, así que hay pocos falsos positivos; al subir, la cobertura se amplía y llegan también avisos menos seguros. El objetivo puede ser un archivo, el número de un pull request, una rama o un rango como `main...review/demo-bug`.

```text
/code-review low
/code-review high main...feat/albums-api
/code-review 42
/code-review --max-findings all
```

Ojo con un detalle: si no indicas un nivel, `/code-review` reutiliza el último que escribiste, incluso en una sesión anterior. Lo mismo vale para `--max-findings`, que se queda puesto hasta que pasas `--max-findings default`.

<!-- TODO screenshot: risultato di /code-review high sul branch review/demo-bug, con i due problemi (autorizzazione mancante e validazione dell'upload) e file, riga e gravità -->

### Aplicar las correcciones y publicarlas

Con `--fix`, la revisión aplica las correcciones directamente en el working tree. Con `--comment`, publica los resultados como comentarios en el pull request, en GitHub o GitLab:

```text
/code-review --fix main...review/demo-bug
/code-review --comment 42
```

::: {.callout .callout-warning}
[Atención]{.callout-title}

`/rewind` no deshace las correcciones que `--fix` aplica en segundo plano. Para volver atrás, usa Git: haz commit antes de lanzar la revisión, así `git diff` te enseña exactamente qué ha cambiado y `git restore .` te devuelve al punto de partida.
:::

Después del fix miro `git diff --stat` y vuelvo a ejecutar los tests: si la corrección rompe otra cosa, te lo dice la suite de Pest.

### `REVIEW.md` y Code Review en GitHub

`/code-review` lee el `CLAUDE.md` como cualquier sesión de Claude Code. Por eso las convenciones de la Photogallery valen también para la revisión: SOLID, transacciones en las escrituras múltiples, eager loading explícito y doble control de autorización en cada mutación (token ability más policy, regla 10 del `CLAUDE.md`).

Para los pull requests está Code Review en GitHub, un servicio gestionado para los planes Team y Enterprise que se paga por revisión. Varios agentes analizan cada pull request, una pasada de verificación descarta los falsos positivos y el resultado llega como comentarios en línea ordenados por gravedad, más un check run llamado "Claude Code Review". Nunca aprueba ni bloquea el pull request: la decisión sigue siendo tuya. Para pedir una revisión nueva, escribe un comentario `@claude review` en el pull request. No está disponible con Zero Data Retention, HIPAA ni CMEK. Lo activa un Owner de la organización de Claude, en claude.ai, en Admin settings > Claude Code, sección Code review: instala la Claude GitHub App y elige los repositorios, el nivel de revisión y cuándo se lanzan las revisiones. No hacen falta archivos de workflow en el repositorio.

Code Review en GitHub se personaliza con un archivo `REVIEW.md` en la raíz del repositorio, junto al `CLAUDE.md`; puedes añadir otros en las subcarpetas para reglas locales. En él escribes qué es grave en tu proyecto, cuántos detalles menores quieres como máximo, qué ignorar y qué comprobar siempre. Este es el de la Photogallery:

```markdown
# Instrucciones de revisión

## Qué es Important

Reserva Important para los problemas que rompen el comportamiento o exponen datos:
consultas no filtradas por el usuario propietario de la foto, subidas sin
validación de tipo y tamaño, endpoints sin policy de autorización,
migraciones que rompen la compatibilidad hacia atrás. Estilo y naming son, como mucho, Nit.

## Limita los Nit

Informa de cinco Nit como máximo por revisión. Si encuentras más, escribe
"y N elementos parecidos más" en el resumen.

## No señales

- Lo que la CI ya comprueba: lint, formato, tipos
- Archivos generados y lockfiles

## Comprueba siempre

- Cada ruta nueva bajo /api/v1 tiene un test de integración de Pest
- Los contratos de la API corresponden a docs/DESIGN.md
- Cada mutación comprueba tanto tokenCan() como la policy
- exif y processing_error solo son visibles para el propietario y los admins
- Ningún log contiene correos ni tokens
```

La sección "Comprueba siempre" retoma los criterios de la spec: los contratos de la API tienen que corresponder a `docs/DESIGN.md`, como exigimos en el capítulo 18. El tercer y el cuarto punto vienen de problemas reales encontrados en las revisiones de las oleadas y registrados en `docs/REVIEW-FIXES.md`: el `AlbumController@store` que solo comprobaba la token ability (S3) y los campos `exif` y `processing_error` devueltos también a los usuarios anónimos, con las coordenadas GPS dentro (S1).

Los problemas encontrados tienen tres niveles. Important hay que corregirlo antes del merge. Nit es un detalle menor. Pre-existing es un bug que ya existía y que el pull request no ha introducido: conviene saberlo, pero no es motivo para bloquear el merge.

Recuerda que el comando local `/code-review` no lee `REVIEW.md`: solo lee el `CLAUDE.md`. Si necesitas una regla en los dos sitios, escríbela en el `CLAUDE.md`.

### Ultrareview en la nube

Para los pull requests importantes está ultrareview, en research preview. En lugar de un solo revisor, un equipo de agentes especializados analiza el código en la nube, cada uno a la caza de un tipo distinto de problema, y una pasada de verificación descarta los falsos positivos. Los resultados vuelven a tu sesión cuando están listos.

```text
/code-review ultra
/code-review ultra revisa sobre todo autorizaciones y subidas
/code-review ultra --fix
```

Sin argumentos, compara la rama actual con la rama principal, incluidos los cambios sin commit. Puedes pasarle una rama, o una nota en lenguaje natural para orientar la revisión, como en el segundo ejemplo. Con `--fix` aplica las correcciones; para un pull request en github.com, desde la ventana de lanzamiento puedes elegir publicar los resultados en el pull request. `/ultrareview` es un alias.

Necesitas iniciar sesión con una cuenta de claude.ai. En Bedrock, Agent Platform de Google Cloud (el antiguo Vertex AI) o Foundry, `/code-review ultra` recurre a una revisión local; con Zero Data Retention o HIPAA no está disponible. En los planes Pro y Max tienes tres ejecuciones gratuitas y después se paga con créditos de uso: por eso no la lanzo en cada push.

Para scripts y CI está el comando `claude ultrareview [target]`, que espera los resultados y los imprime. `--json` produce una salida que otro programa puede leer, `--timeout` fija la espera máxima en minutos (por defecto, 45) y `--post` publica los resultados como comentario en el pull request.

```bash
claude ultrareview --json --timeout 30 > ultrareview.json
```

## 22.4 Un segundo modelo para las partes críticas

Claude Code escribió el código de la Photogallery con sus patrones y su idea de cuál es la arquitectura correcta. Cuando el mismo modelo revisa ese código, tiende a dar por buenos justo esos patrones. Es el problema de quien relee su propio trabajo: ve lo que creía haber escrito. En el log de revisiones de la Photogallery hay una frase que lo dice con claridad: la sesión que había escrito el código no había visto ninguno de los problemas que encontró después un revisor independiente.

La revisión integrada atenúa el problema, porque se ejecuta con un contexto limpio y, con ultrareview, con varios agentes y una verificación. Pero el modelo sigue siendo uno, y los equipos llevan décadas resolviendo esto de la misma forma: el revisor tiene que ser distinto del autor. Con los LLM, eso significa un modelo distinto. Gemini, Codex y Kimi están entrenados con datos distintos, con técnicas distintas, y tienen puntos ciegos distintos de los de Claude: lo que un modelo considera normal, otro lo señala.

¿Sigue teniendo sentido ahora que existe `/code-review`? Sí, pero no en todas partes. Un segundo modelo cuesta tiempo, porque la revisión la orquestas a mano. Yo lo uso en las partes críticas (autenticación, subidas, autorización, pipeline de fotos) antes del deploy, no en cada push.

### Qué encontraron en la Photogallery

Lo que sigue es lo que observé en este proyecto, con las versiones de los modelos disponibles en la primavera de 2026. No es una clasificación general: los modelos cambian cada pocos meses, y con otro código los resultados pueden ser distintos.

Claude, usado como revisor con los prompts del capítulo 19, fue el más útil en arquitectura: violaciones de SOLID, dependencias circulares, patrones que no encajan con el dominio. Explica mucho y propone correcciones detalladas, pero con el código que ha escrito él es más indulgente.

Gemini fue el más fuerte en rendimiento y uso de memoria. Encontró tres problemas que Claude no había señalado:

- un `file_get_contents` (y el mismo esquema con `Storage::get`) que cargaba el archivo entero en RAM en lugar de usar un stream, con riesgo de quedarse sin memoria con las fotos grandes
- `UploadPhotosAction`, que escribía los archivos en disco dentro de una transacción: si la transacción hacía rollback, los archivos se quedaban escritos
- las coordenadas GPS de los metadatos EXIF servidas a los usuarios, incluidos terceros no autorizados

Codex fue preciso con los tipos, los contratos de la API y la gestión de errores: funciones que prometen más de lo que devuelven, `catch` demasiado amplios que se tragan errores reales, respuestas incoherentes entre endpoints del mismo controller. Informes más cortos que los de Claude, pero certeros.

Kimi fue el más quisquilloso con los casos límite de seguridad, y encontró cosas que ni Claude ni Gemini habían visto:

- la columna `is_admin` entre los campos fillable del modelo `User`: cualquiera podía enviar `is_admin: true` en la petición y convertirse en admin
- URL firmadas generadas antes del control de la policy: la URL existía y funcionaba aunque luego el usuario no pasara la autorización
- autenticación gestionada a mano en lugar de con `Auth::attempt` de Laravel
- la verificación del correo ausente, junto con una forma de saltarse el rate limiter
- el token de Sanctum guardado en `localStorage` en lugar de en una cookie HttpOnly

Ninguno de estos era un falso positivo: todos estaban en el código. El último es un caso aparte, porque era un compromiso ya documentado en DESIGN §10.5: la v1 guardaba el token Bearer en `localStorage` y mitigaba el riesgo con un TTL de 24 horas, una CSP restrictiva, la prohibición de HTML en bruto en el frontend y las token abilities. La revisión lo volvió a sacar a la luz, y la corrección (commit `9ebef16`) movió el token a `sessionStorage`, que desaparece cuando cierras la pestaña. Un script inyectado también puede leerlo ahí, así que todas las mitigaciones se mantienen. `DESIGN.md` §10.5, en la rama final, sigue hablando de `localStorage`: hasta un documento sincronizado hay que releerlo. Hoy los únicos campos fillable de `User` son `name`, `email` y `password`.

El informe consolidado contaba 3 problemas CRITICAL, 7 HIGH, 14 MEDIUM y 7 LOW. El más grave, según el informe, era una fuga de datos entre usuarios en `BatchController`: las fotos se asociaban a un lote de subida por timestamp, se cargaban para todos los usuarios y se filtraban por propietario en PHP en lugar de en la consulta. La corrección (commit `5e6c41c`) añade una columna `batch_id` a la tabla `photos` y filtra por lote y por usuario directamente en SQL.

![El informe consolidado de la revisión previa al deploy: los tres problemas CRITICAL, entre ellos la fuga de fotos entre usuarios en BatchController](figures/cap-22/fig-01.png)

![Una parte de los 14 problemas MEDIUM: fiabilidad del pipeline, rendimiento del panel de administración, calidad de las imágenes y accesibilidad con teclado](figures/cap-22/fig-02.png)

![Del informe: la deriva entre el patrón Actions previsto en DESIGN.md y la lógica que acabó en los controllers, el stripping síncrono de GPS durante la subida y el compromiso del token en localStorage](figures/cap-22/fig-03.png)

### El flujo de la revisión multi-LLM

El primer paso es preparar el changeset:

```bash
# Todo el diff de la rama respecto a main
git diff main...HEAD > changeset.diff

# O, si el diff es demasiado grande, solo las partes críticas
git diff main...HEAD -- backend/app/Http/Controllers/ backend/app/Actions/ frontend/src/api/ > changeset-critical.diff
```

Después, el mismo prompt a todos los modelos. El prompt tiene que ser idéntico; si no, estás comparando respuestas a preguntas distintas. Uso el del recuadro del final de esta sección y pego el diff al final.

Con los informes reunidos, los agrego por consenso:

| Encontrado por | Prioridad |
| :---- | :---- |
| Todos los modelos | Crítica, corrección obligatoria antes del deploy |
| Tres modelos | Alta, corrección muy recomendable |
| Dos modelos | Media, valora el contexto |
| Un solo modelo | Baja, léelo y decide |

El consenso te dice por dónde empezar. Un problema que solo encuentra un modelo no es por fuerza un falso positivo: el `is_admin` fillable solo lo había visto Kimi.

Por último, le paso los hallazgos a Claude para las correcciones, en una sesión nueva o después de un `/clear`:

```text
Tienes delante los resultados de una revisión cross-LLM del proyecto.
Estos problemas los encontraron Gemini y Kimi y los confirmó Codex:

[pega los hallazgos críticos y altos]

Organízalos en una lista de tareas y resuélvelos de uno en uno, empezando
por los Critical. Para cada fix, explica qué has cambiado y por qué.
```

La sesión nueva importa. El contexto de la sesión de desarrollo empuja a Claude a volver a proponer los mismos patrones que se acaban de señalar como problemáticos; desde un contexto limpio los trata como lo que son, problemas que corregir. Después de las correcciones vuelvo a lanzar `/code-review high` sobre la rama, para comprobar que los fixes no han introducido nada más.

¿Cuánto cuesta? En la Photogallery, la revisión con cuatro modelos costó en total entre 10 y 15 dólares; depende del tamaño del diff y de los planes que tengas. Un bug como la fuga de fotos entre usuarios, descubierto en producción, cuesta días entre el incidente, la comunicación a los usuarios y, si hay datos personales de por medio, las obligaciones legales.

::: {.callout .callout-prompt}
[Prompt reutilizable]{.callout-title}

Para pegarlo idéntico en Claude, Gemini, Codex y Kimi.

```text
Actúa como un senior software engineer con más de 10 años de experiencia.
Haz una revisión crítica del siguiente código.

Evalúalo según estos ejes:
1. Buenas prácticas y estándares del lenguaje/framework
2. Principios SOLID y patrones de diseño (SRP, OCP, LSP, ISP, DIP)
3. Seguridad (inyección, autenticación, autorización, exposición de datos)
4. Escalabilidad y rendimiento (consultas N+1, uso de memoria, caché)
5. Fiabilidad y gestión de errores (manejo de excepciones, rollback)
6. Casos límite no gestionados (entradas extremas, concurrencia, estados intermedios)

Para cada problema:
- Gravedad: Critical / High / Medium / Low
- Archivo y línea (si aplica)
- Descripción concisa del problema
- Fix recomendado con un fragmento de código

Salida: lista Markdown ordenada por gravedad decreciente.
No rellenes: si no encuentras problemas en un área, dilo explícitamente.

[pega aquí el diff de git o los archivos que hay que revisar]
```
:::

### Qué revisión usar y cuándo

| Enfoque | Puntos fuertes | Límites | Cuándo usarlo |
| --- | --- | --- | --- |
| Prompts de revisión escritos a mano (capítulo 19) | Control total sobre qué se mira | Requiere tiempo y prompts bien escritos | Revisiones guiadas por la spec |
| `/code-review` | Rápido, en segundo plano, `--fix` y `--comment` | Un solo modelo, solo lee `CLAUDE.md` | Antes de cada push |
| `/code-review ultra` | Varios agentes, verificación de falsos positivos | Necesita una cuenta de claude.ai, consume más | Pull requests grandes o críticos |
| Code Review en GitHub (Team y Enterprise) | Automática en cada pull request, lee `REVIEW.md` | Se paga por revisión, solo GitHub | Workflow de equipo |
| Segundo modelo (Gemini, Codex, Kimi) | Perspectiva independiente | Orquestado a mano | Seguridad y rendimiento en el código crítico |

El flujo que recomiendo, y el que uso en la Photogallery:

1. `/code-review high` antes de cada push.
2. Ultrareview en los pull requests grandes o que tocan autenticación, subidas y datos.
3. Una revisión con un segundo modelo en las partes críticas, antes del deploy.

## 22.5 Plugins de seguridad

Para la seguridad también hay herramientas dedicadas. En el marketplace oficial `claude-plugins-official` tienes dos plugins de Anthropic: security-guidance, que revisa los cambios de Claude mientras trabaja, y Claude Security, que hace un escaneo multiagente de vulnerabilidades y convierte en parches los problemas que elijas. Los encuentras en `/plugin`, pestaña Discover, buscando "security", o los instalas por nombre con `/plugin install security-guidance@claude-plugins-official` y `/plugin install claude-security@claude-plugins-official`; el capítulo 14 explica la instalación y los scopes.

Además está el comando `/security-review`, que hace una revisión de seguridad de los cambios pendientes en la rama actual. En la Photogallery lo lanzo antes de la auditoría final de la siguiente sección: es un buen filtro para los problemas evidentes, y así la auditoría se centra en la configuración.

Ninguno de los tres sustituye a la auditoría, que comprueba también lo que no está en el diff: cabeceras que faltan, configuraciones por defecto, secrets en el historial de Git.

## 22.6 Auditoría de seguridad: middleware, CSP, HTTPS, secrets

La auditoría de seguridad es el último paso antes del deploy y merece una sesión y un prompt propios. Los problemas de seguridad no siempre salen como bugs durante las pruebas funcionales: un endpoint que no comprueba la autorización responde 200 y parece funcionar de maravilla, hasta que alguien le pasa el token de otro usuario.

El punto de partida es que los valores por defecto de los frameworks están pensados para el desarrollo. La configuración CORS por defecto de Laravel tiene `allowed_origins` a `*`, y la Photogallery cayó en ello: el scaffold de Laravel 13 no publica `config/cors.php`, así que `FRONTEND_URL`, documentada en `.env.example` para la allowlist, no la leía nadie y estaba activo el comodín (REVIEW-FIXES, punto S2). Ningún framework activa una CSP por defecto, ni fuerza HTTPS o HSTS. Cada medida de esta sección es explícita: si no la configuras tú, no la configura nadie.

### Middleware y cabeceras

El middleware es la capa que atraviesa cada petición antes del controller, así que es el sitio adecuado para los controles de seguridad: se aplica a todas las rutas y no puedes olvidarte de ninguna. En Laravel, las cabeceras de seguridad las añades con un middleware propio:

```php
<?php

declare(strict_types=1);

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

final class SecurityHeaders
{
    public function handle(Request $request, Closure $next): Response
    {
        $response = $next($request);

        $response->headers->set('X-Frame-Options', 'DENY');
        $response->headers->set('X-Content-Type-Options', 'nosniff');
        $response->headers->set('Referrer-Policy', 'strict-origin-when-cross-origin');
        $response->headers->set('Permissions-Policy', 'geolocation=(), microphone=()');

        if (app()->environment('production')) {
            $response->headers->set(
                'Strict-Transport-Security',
                'max-age=31536000; includeSubDomains'
            );
        }

        return $response;
    }
}
```

y lo registras para todas las peticiones en `bootstrap/app.php`, dentro de `withMiddleware`:

```php
$middleware->append(\App\Http\Middleware\SecurityHeaders::class);
```

Con Node y Express, las mismas cabeceras las consigues con Helmet en una línea, `app.use(helmet())`.

CORS: en producción, nunca `Access-Control-Allow-Origin: *`. La Photogallery ahora solo permite el origen de la SPA, leído del entorno, y solo en la API. El panel de Filament en `/admin` queda fuera y mantiene sus propias reglas de CSRF:

```php
return [
    'paths' => ['api/*'],
    'allowed_methods' => ['*'],
    'allowed_origins' => [
        env('FRONTEND_URL', 'http://localhost:5173'),
    ],
    'allowed_origins_patterns' => [],
    'allowed_headers' => ['*'],
    'exposed_headers' => ['ETag', 'Retry-After'],
    'max_age' => 0,
    // Token Bearer en la cabecera Authorization: nada de CORS con credenciales
    'supports_credentials' => false,
];
```

Límites del body: sin un límite, un atacante envía un body de 1 GB y te consume la memoria del servidor. En PHP, el techo lo ponen `post_max_size` y `upload_max_filesize`; por encima, la Photogallery valida cada archivo con `image|mimes:jpg,jpeg,png,webp|max:10240` (10 MB) y convierte `PostTooLargeException` en una respuesta 413 con el envelope JSON estándar.

Proxies de confianza: detrás de un load balancer, un CDN o un reverse proxy, tienes que decirle al framework que se fíe de las IP del proxy. Si no, `$request->ip()` devuelve la IP del proxy para todos, el rate limiter por IP se convierte en un único cubo compartido y la protección contra el credential stuffing deja de servir para nada. En la Photogallery, el problema lo encontró la revisión de la fase 2 (punto S4), y la corrección en `bootstrap/app.php` lee la configuración del entorno:

```php
$trustedProxies = env('TRUSTED_PROXIES', '');
if ($trustedProxies !== '') {
    $middleware->trustProxies(
        at: $trustedProxies === '*' ? '*' : explode(',', $trustedProxies),
    );
}
```

En local, `TRUSTED_PROXIES` se queda vacía; detrás del ALB del capítulo 23 la configuras. En Express, el equivalente es `app.set('trust proxy', 1)`.

### Content Security Policy

La CSP es la defensa más eficaz contra el Cross-Site Scripting. Si un atacante consigue inyectar JavaScript en tus páginas, con una CSP bien configurada el navegador se niega a ejecutar el código no autorizado. Una política básica que sirve para la mayoría de las aplicaciones:

```text
Content-Security-Policy:
  default-src 'self';
  script-src 'self';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  font-src 'self' https://fonts.gstatic.com;
  connect-src 'self' https://api.tua-app.com;
  frame-ancestors 'none';
  base-uri 'self';
  form-action 'self';
```

`frame-ancestors 'none'` es el sustituto moderno de `X-Frame-Options: DENY`: impide que el sitio se incruste en un iframe de otro dominio (clickjacking). `'unsafe-inline'` en los estilos suele hacer falta para CSS-in-JS y para los estilos inline de los componentes; en los scripts, evítalo, y si tienes scripts inline imprescindibles, usa nonces.

La Photogallery tiene su política en DESIGN §10.5, y es una de las mitigaciones que justifican el token en el navegador en lugar de en una cookie HttpOnly:

```text
default-src 'self'; img-src 'self' https://cdn.example.com data:; script-src 'self'; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'self'
```

No actives la CSP en modo bloqueante en el primer deploy. Empieza con `Content-Security-Policy-Report-Only` y un `report-uri`, revisa las violaciones durante unos días y pasa al modo bloqueante solo cuando estés seguro de que no bloquea nada legítimo:

```text
Content-Security-Policy-Report-Only:
  default-src 'self';
  report-uri https://tua-app.com/api/csp-report;
```

La CSP que cuenta para la SPA es la del HTML de la SPA, no la de las respuestas JSON de la API. La SPA de React sale de la build de Vite como archivos estáticos: la política va donde se sirven (en la distribución de CloudFront, en el capítulo 23) o, como red de seguridad, en una etiqueta `<meta>` en el `index.html`, que vale también cuando los assets llegan desde el CDN sin pasar por el servidor de aplicación:

```html
<meta
  http-equiv="Content-Security-Policy"
  content="default-src 'self'; frame-ancestors 'none';"
/>
```

Una precisión: los navegadores ignoran `frame-ancestors` cuando llega en una etiqueta `<meta>`, así que la protección contra el clickjacking tiene que viajar también en una cabecera HTTP.

### HTTPS y HSTS

En producción, HTTPS es obligatorio: sin él, cualquiera que esté en la misma red puede leer tokens, cookies de sesión y datos personales. Cada petición HTTP tiene que redirigirse a HTTPS, tanto en la infraestructura (load balancer, CloudFront) como en el código. En Laravel fuerzas el esquema de las URL generadas en `AppServiceProvider`:

```php
public function boot(): void
{
    if ($this->app->environment('production')) {
        \Illuminate\Support\Facades\URL::forceScheme('https');
    }
}
```

HSTS le dice al navegador, después del primer acceso por HTTPS, que no vuelva a intentar HTTP durante un periodo determinado. Con `max-age=31536000` (un año), aunque el usuario escriba `http://` en la barra de direcciones, el navegador pasa solo a HTTPS, sin enviar la petición en claro que podría interceptarse. El middleware `SecurityHeaders` de antes lo configura en producción:

```text
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

Los certificados: con Let's Encrypt, comprueba que la renovación automática funciona (`certbot renew --dry-run`); con AWS Certificate Manager, la renovación es automática. En cualquier caso, configura una alerta treinta días antes de la caducidad, porque un certificado caducado deja fuera a todos los usuarios.

### Gestión de los secrets

Un secret que acaba en el repositorio se queda en el historial de Git aunque lo quites en el commit siguiente. Antes del deploy hago un escaneo con gitleaks, historial incluido:

```bash
# Instalación
brew install gitleaks   # macOS
# o bien: go install github.com/gitleaks/gitleaks/v8@latest

# Escaneo completo, incluido el historial de Git
gitleaks detect --source . --verbose
```

Si gitleaks encuentra algo, ese secret hay que darlo por comprometido: no basta con quitarlo, hay que rotarlo.

En el código y en los archivos de configuración con commit no va ningún valor sensible: las API keys, las cadenas de conexión y las credenciales SMTP van en variables de entorno. En local y en CI, las variables de entorno sirven; en producción, usa un secret manager (AWS Secrets Manager, GCP Secret Manager, HashiCorp Vault), que te da el registro de quién leyó qué y cuándo, la rotación automática y la revocación sin tocar el código. Rota las claves cada noventa días: una clave que nunca se rota sigue siendo válida para siempre en manos de quien la encontró.

La auditoría de seguridad que se hizo en una de las oleadas de la Photogallery (`docs/BATCH-2025-04-28.md`) encontró dos problemas de este tipo: un fallback `'password'` escrito a fuego en el seeder del usuario admin, que habría llegado a producción si faltaba la variable de entorno, y un `.env` con `APP_DEBUG=true`. El primero se corrige haciendo que el seeder falle cuando falta la variable; el segundo, con `APP_DEBUG=false` fuera del entorno local y el `.env` en el `.gitignore`.

### Autenticación

Para las contraseñas usa argon2id o bcrypt, nunca SHA-256, SHA-512 o MD5: no tienen un work factor configurable y, con un dump de la base de datos y hardware moderno, se rompen enseguida. Laravel usa bcrypt por defecto, y la Photogallery fija `BCRYPT_ROUNDS=12` en `.env.example`. Para pasar a argon2id basta con `HASH_DRIVER=argon2id` en el `.env`, siempre que tu PHP esté compilado con soporte para argon2.

Los tokens de Sanctum de la Photogallery caducan a las 24 horas (`SANCTUM_TOKEN_EXPIRATION=1440`, que lee `config/sanctum.php`: también esta se había quedado desconectada hasta la revisión de la fase 1, punto F3) y el logout borra el token actual con `currentAccessToken()->delete()`. Las token abilities (`photos:write`, `albums:write`, `admin`) limitan los daños si alguien roba un token. Sobre la decisión de guardar el token en el navegador (hoy en `sessionStorage`), vale lo dicho en la sección 22.4: es un compromiso documentado; si quieres cambiarlo, el camino es el modo stateful de Sanctum con cookies HttpOnly, a cambio de un flujo de CSRF más complejo.

### Rate limiting

Un rate limiting sin números no protege nada. La Photogallery tiene los límites de DESIGN §6.0 en `AppServiceProvider`: 10 peticiones por minuto por IP en las rutas de autenticación y, en el resto de la API, dos techos a la vez, 120 por minuto por IP y 300 por minuto por usuario autenticado.

```php
private function configureRateLimiters(): void
{
    $authPerIp = (int) config('photogallery.rate_limits.auth_per_ip_per_minute', 10);
    $apiPerIp = (int) config('photogallery.rate_limits.api_per_ip_per_minute', 120);
    $apiPerUser = (int) config('photogallery.rate_limits.api_per_user_per_minute', 300);

    RateLimiter::for('auth', fn (Request $request) => Limit::perMinute($authPerIp)->by($request->ip()));

    RateLimiter::for('api', function (Request $request) use ($apiPerIp, $apiPerUser) {
        $limits = [Limit::perMinute($apiPerIp)->by($request->ip())];
        if ($request->user()) {
            $limits[] = Limit::perMinute($apiPerUser)->by('user:'.$request->user()->id);
        }

        return $limits;
    });
}
```

Las rutas usan `throttle:auth` y `throttle:api` en `routes/api.php`. El límite por usuario hace falta porque detrás de un NAT o de un proxy corporativo muchos usuarios comparten la misma IP, y un límite solo por IP los bloquearía a todos a la vez. El límite por IP en la autenticación, en cambio, solo funciona si los proxies de confianza están configurados, como vimos antes. `/api/v1/health` queda fuera del throttling, para que los probes del load balancer no disparen el limiter. La misma auditoría de oleada señaló que el login de Filament no tenía límite: el panel de administración es una puerta de entrada como cualquier otra.

### El prompt de la auditoría final

Este es el último prompt que lanzo antes de dar el proyecto por listo para el deploy, en una sesión dedicada:

```text
Eres un security engineer. Examina el proyecto entero (código,
configuración, dependencias) y haz una auditoría previa a producción.

Verifica explícitamente:
1. Middleware de seguridad (cabeceras de seguridad, CORS, límites del body)
2. Content Security Policy (presente, bien configurada)
3. HTTPS forzado y HSTS
4. Gestión de los secrets (ningún secret en el código, uso de variables de entorno)
5. Hashing de contraseñas (algoritmo correcto, work factor adecuado)
6. Tokens y sesiones (caducidad, revocabilidad, almacenamiento seguro)
7. Rate limiting (login, registro, API general, panel de administración)
8. Proxies de confianza configurados
9. Validación completa de la entrada (cada endpoint externo)
10. Autorización en cada ruta (ningún endpoint sin control de auth)

Para cada punto:
- Estado: OK / PROBLEMA / NO VERIFICABLE
- Si es PROBLEMA: descripción del riesgo y fix recomendado
- Prioridad: Bloqueante / Alta / Media

Separa los problemas del código de los problemas de configuración del entorno
(estos últimos se resuelven en la fase de deploy, no en el código).
```

La última instrucción separa dos listas de trabajo distintas. Los problemas del código los cierras en el repositorio, ahora. Los de configuración (`TRUSTED_PROXIES`, `APP_DEBUG`, la CSP en la distribución de CloudFront, el secret manager) pasan a ser puntos del provisioning, y los vuelves a encontrar en la plantilla de CloudFormation del capítulo 23.

## Resumen {.unlisted}

- La checklist previa al deploy cubre flujos funcionales, rendimiento, seguridad básica, integridad de los datos y observabilidad, y se pasa uno o dos días antes del lanzamiento: si un punto no pasa, el deploy no sale.
- Las tareas huérfanas se cazan con grep y con un subagente dedicado; para cada una eliges entre Delete, Complete y Document and defer.
- `/code-review` con effort alto antes de cada push, con `--fix` y `--comment` para actuar sobre los resultados; las correcciones de `--fix` se deshacen con Git, no con `/rewind`.
- `REVIEW.md` personaliza Code Review en GitHub (Team y Enterprise), pero no el comando local, que solo lee `CLAUDE.md`; ultrareview es para los pull requests grandes o críticos.
- Un segundo modelo sigue siendo útil en las partes críticas antes del deploy: en la Photogallery encontró el `is_admin` fillable y las URL firmadas generadas antes de la policy.
- La auditoría final separa los problemas del código de los de configuración, que pasan al provisioning.

## Ejercicio {.unlisted}

Haz la QA completa previa al deploy en tu Photogallery, partiendo de la rama `book/cap-14-phases-complete`.

1. Crea una rama dedicada: `git switch -c cap-22-pre-deploy-qa`.
2. Lanza el grep de tareas huérfanas y el subagente con el prompt de la sección 22.2, y aplica la regla de las tres D a cada hallazgo.
3. Añade el `REVIEW.md` de la sección 22.3 y lanza `/code-review high main...cap-22-pre-deploy-qa`.
4. Envía el prompt de la revisión multi-LLM a por lo menos un segundo modelo (Gemini, Codex o Kimi) sobre el diff de los controllers y de las Actions, y agrega los hallazgos por consenso.
5. Lanza `/security-review` y después el prompt de la auditoría final de la sección 22.6.
6. En una sesión nueva, corrige todos los hallazgos críticos y altos, y luego vuelve a lanzar `/code-review high` y la suite de tests.

El ejercicio está terminado cuando `./vendor/bin/sail test` y `pnpm test` pasan, la última `/code-review high` no informa de problemas Important y los problemas de configuración están apuntados en una lista aparte para el capítulo 23. Lleva 3-4 horas; no tengas prisa con la agregación de los hallazgos, porque ahí es donde decides qué se corrige de verdad.

La rama de referencia es `book/cap-15-post-review-fixes` en el repositorio `claude-code-book-photogallery`: contiene todas las correcciones de la revisión (3 CRITICAL, 7 HIGH, 14 MEDIUM y 7 LOW, más la corrección de la fuga de los datos EXIF con las rutas firmadas) y un `docs/DESIGN.md` alineado con la implementación real.
