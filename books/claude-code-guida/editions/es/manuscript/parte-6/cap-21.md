# Capítulo 21. Funcionalidades sobre la marcha

::: {.chapter-goals}
[Qué aprenderás]{.callout-title}

Cómo meter una funcionalidad en un proyecto SDD ya en marcha, primero en los documentos y después en el código, con tres casos del Photogallery: la pipeline batch de las fotos hacia S3, el registro que el plan perdió por el camino y los favoritos rehechos de columna booleana a tabla pivot. Después, cómo manejar un PR que toca backend y frontend a la vez.

[Requisitos previos]{.callout-title}

Los capítulos 17-20 (especificaciones, SDD, ejecución por oleadas, worktrees) y el repo companion en la rama `book/cap-14-phases-complete`.

:::

Al final del capítulo 20, la Wave 1 de `docs/TASKS.md` ya tiene merge en `main`: admin de Filament, setup y componentes del frontend React, pipeline de imágenes (Fases 3-6). El plan avanza. Entonces, un martes a las cinco de la tarde, llega el mensaje: "Ah, también necesitamos subir muchas fotos de golpe, hay gente que vuelve con 500 fotos de las vacaciones. ¿Y el registro? No lo había escrito, pero era obvio. Y ya que estás, los clientes siempre piden guardar sus fotos favoritas."

Las peticiones sobre la marcha llegan incluso con las mejores especificaciones: el stakeholder ve crecer la aplicación y se acuerda de cosas que daba por hechas, o el mercado cambia las prioridades. El caso más traicionero es otro: la funcionalidad estaba en los requisitos, pero se perdió cuando los requisitos se convirtieron en tareas, y nadie se dio cuenta hasta la primera prueba manual. No puedes evitarlas. Lo que sí puedes controlar es cómo entran en el proyecto, sin romper lo que funciona y sin perder el hilo del plan.

En el Photogallery cada uno de los tres casos tiene un sitio concreto. El batch parte de la pipeline que la Track A construyó en el capítulo 20 y la lleva a S3 y SQS, que en `TASKS.md` es la Fase 8, dentro de la Wave 2. El registro que falta es la distancia entre la user story US-30 y la task T070 de la Fase 5, cerrada más tarde por T121. Los favoritos son la Fase 6.5, una fase insertada a mitad de camino con el número de wave 1.5. La rama `book/cap-14-phases-complete` (290 archivos) contiene el proyecto con todas las fases de la 3 a la 14.

## 21.1 Procesamiento batch de las fotos en S3

### El requisito

La regla en la que se apoya la pipeline ya está en `main`: la subida responde enseguida y el procesamiento pesado lo hace un worker desde la cola. La petición de las 500 fotos pone a prueba los límites elegidos, y el paso a S3 pone a prueba lo que en local no se ve: reintentos, transacciones, permisos de archivos.

Estas son las líneas que importan de la sección F4 de `docs/REQUIREMENTS.md`, en inglés como todos los documentos del repo:

```markdown
### F4 — Upload
- F4.2 Client-side validation: MIME (JPG/PNG/WebP), size (≤ 10 MB)
- F4.3 Up to 20 files per submission
- F4.6 Upload returns immediately; processing happens in the background
```

El criterio AC-F4-3 dice que enviar 21 archivos muestra "Up to 20 files at once" y bloquea el envío. Así que las 500 fotos del stakeholder se convierten en 25 envíos de 20: un límite decidido de antemano y escrito en los requisitos, para que nadie lo descubra en producción.

### Primero los documentos, luego el código

Toda funcionalidad sobre la marcha arranca con el mismo prompt. Lo uso en Plan Mode (`Shift+Tab` hasta que aparezca `plan mode on`, o `/plan`), así Claude lee y propone sin tocar archivos:

::: {.callout .callout-prompt}
[Prompt reutilizable]{.callout-title}

```text
Tengo un proyecto con docs/REQUIREMENTS.md, docs/DESIGN.md y docs/TASKS.md
ya consolidados. Quiero añadir esta funcionalidad: [DESCRIPCIÓN DE LA FUNCIONALIDAD].

Sigue estos pasos en orden:

1. Lee los tres archivos para entender el estado actual
2. Propón la sección que hay que añadir a REQUIREMENTS.md
   (requisitos, restricciones y criterios de aceptación explícitos)
3. Propón los cambios en DESIGN.md (esquema, endpoints, componentes)
4. Propón las tareas que hay que añadir a TASKS.md, con dependencias,
   IDs nuevos que no choquen con los existentes y criterios de
   finalización verificables
5. Antes de ejecutar cualquier tarea, comprueba si la funcionalidad
   necesita una migración de la base de datos y si en el código ya hay
   algo parecido que pueda entrar en conflicto

No empieces a ejecutar hasta que haya aprobado los cambios en los tres archivos.
```
:::

El paso que la gente se salta es el cuarto: sin tareas en el plan, el trabajo nuevo flota sin dependencias y Claude no sabe cómo encajarlo en lo que ya está hecho.

Para el batch en S3 no hacen falta fases nuevas: el trabajo ya está en `TASKS.md` y es la Fase 8, "AWS migration (S3 + SQS via env vars)". La intención está en el nombre: el mismo código, solo cambia el archivo `.env`. Lo que hay que decidir es qué se hace ya y qué se deja para el deploy.

### Del disco local a S3

Gracias a los contratos de la Fase 6, S3 es cuestión de configuración. `PhotoStorage` está ligado a `DiskPhotoStorage` y no existe una clase `S3PhotoStorage`: la clase trabaja sobre dos discos de Laravel, `photos_private` para los originales y `photos` para las variantes, definidos desde T006, y `PHOTOS_DRIVER` decide si son carpetas locales o buckets de S3. El bloque de producción está en `DESIGN.md` §12.5:

```text
QUEUE_CONNECTION=sqs
SQS_QUEUE=photogallery-pro
SQS_REGION=eu-west-1

FILESYSTEM_DISK=photos
PHOTOS_DRIVER=s3
AWS_BUCKET_PUBLIC=photogallery-pro-prod
AWS_BUCKET_PRIVATE=photogallery-pro-prod-private
AWS_URL=https://cdn.example.com
```

Además de las credenciales `SQS_*` y `AWS_*`, que en el documento son marcadores de posición. El bucket privado guarda los originales, con Block Public Access activado y acceso solo mediante `temporaryUrl()` de 5 minutos. El público guarda las variantes, detrás de CloudFront.

En la rama, la Fase 8 está cerrada solo en parte. T089 está hecha: una auditoría que con `grep` busca `storage_path`, `storage/app`, `disk('public')` y `file_get_contents` dentro de `app/` y no encuentra nada fuera de `config/`. Es la tarea que importa ahora, porque una ruta local escrita a mano rompería la pipeline el día en que los discos pasen a ser buckets. T086 (`.env.production.example`), T087 (`docs/DEPLOY.md`) y T088 (el script `smoke-aws.php`) siguen abiertas hasta el deploy del capítulo 23.

En desarrollo, Sail arranca MinIO, y `backend/.env.example` ya apunta allí las variables `AWS_*` y sugiere cambiar `PHOTOS_DRIVER` a `s3` para probar en local el camino de producción. Antes, lee la rama `s3` de los discos `photos` y `photos_private` en `config/filesystems.php`: no lee `AWS_ENDPOINT` ni `AWS_USE_PATH_STYLE_ENDPOINT`, y toma los buckets de `AWS_BUCKET_PUBLIC` y `AWS_BUCKET_PRIVATE`, que están comentadas en el archivo de ejemplo. Sin `endpoint`, el SDK de AWS apunta a las direcciones reales de S3, así que tal como está el driver `s3` no habla con MinIO. El archivo de ejemplo no lo dice, y conviene convertirlo en una tarea enseguida.

### El flujo, en pocas líneas

Para razonar sobre reintentos y transacciones necesitas tener delante lo que la Track A del capítulo 20 dejó en `main`:

```text
Browser                 Backend Laravel                Cola              Storage
   |                          |                         |                   |
   |-- POST /photos --------->|                         |                   |
   |   (1-20 fotos)           |-- quitar GPS, original ----------------->  photos_private
   |                          |-- filas Photo (transacción)                 |
   |                          |-- Bus::batch(ProcessPhoto x N) -->|         |
   |<-- 202 + Location -------|                         |                   |
   |                          |                         |-- worker -------> photos
   |-- GET /photos/batch/{id} |                         |   (300/800/1600 px)
```

El controlador responde `202 Accepted` con una cabecera `Location`, y `useBatchPoll` consulta el endpoint cada segundo (`BATCH_MS` en `src/data/polling.ts`) hasta que la respuesta dice `finished: true`. En desarrollo la cola es la tabla `jobs` de la base de datos. En producción es SQS, con el worker bajo Supervisor: `php artisan queue:work sqs --queue=photogallery-pro --tries=3 --timeout=180 --sleep=3 --memory=512` (`DESIGN.md` §12.6).

### El dispatch fuera de la transacción

Primero haces commit de la transacción, luego el dispatch. Si encolas el job dentro de la transacción, un worker rápido puede cogerlo antes del commit, buscar una fila que todavía no existe y fallar con un error que no hace pensar en la transacción.

En la rama, la action devuelve los jobs desde la closure de la transacción y los encola después:

```php
[$photos, $jobs] = DB::transaction(function () use ($files, $user, $albumId, $tagNames, $titles, $description): array {
    $photos = [];
    $jobs = [];

    foreach ($files as $index => $file) {
        // quitar GPS, storeOriginal, Photo::create(...), tags, evento
        $photos[] = $photo;
        $jobs[] = new ProcessPhoto($photo);
    }

    return [$photos, $jobs];
});

$batch = Bus::batch($jobs)->dispatch();
```

No llegamos solos: la revisión de fin de fase había marcado como High justo un `Bus::batch()` dentro de `DB::transaction()`. El informe está en `docs/BATCH-2026-04-29.md`.

### El worker y la idempotencia

El job tiene que ser **idempotente**: procesar dos veces la misma foto debe dar el mismo resultado, sin archivos ni filas duplicados. Es el requisito que más fácilmente se olvida, y sin él cada reintento deja basura en S3.

```php
final class ProcessPhoto implements ShouldQueue
{
    public int $tries = 3;

    /** @var int[] */
    public array $backoff = [10, 30, 60];

    public function handle(ImageProcessor $processor, ExifExtractor $exif): void
    {
        $this->photo->update(['processing_status' => ProcessingStatus::Processing]);
        $processor->generate($this->photo);

        $absolutePath = Storage::disk('photos_private')->path($this->photo->original_path);
        $exifData = $exif->extract($absolutePath);

        // update: exif + processing_status Completed, luego event(PhotoProcessed)
    }

    public function failed(\Throwable $e): void
    {
        report($e);

        $this->photo->update([
            'processing_status' => ProcessingStatus::Failed,
            'processing_error' => 'Processing failed. Please try again or contact support.',
        ]);
    }
}
```

En SQS los reintentos son lo normal: un worker que muere a medias, un timeout, un mensaje que vuelve a ser visible. El job hace como máximo tres intentos: espera 10 segundos antes del segundo y 30 antes del tercero. El tercer valor de `$backoff`, 60, nunca entra en juego con `$tries = 3`; solo sirve si algún día subes los intentos. Tras el último, `failed()` marca la foto como `failed` con un mensaje genérico, y el texto de la excepción, que puede contener rutas del servidor, se queda en el log (esto también viene de un finding de la revisión).

Aquí la idempotencia sale de una clave determinista. `DiskPhotoStorage::storeVariant()` escribe cada variante en una ruta que depende solo del UUID de la foto y del nombre de la variante:

```php
public function storeVariant(string $photoId, string $variant, string $contents): string
{
    $relativePath = "{$variant}/{$photoId}.jpg";

    Storage::disk('photos')->put($relativePath, $contents);

    return $relativePath;
}
```

Un reintento sobrescribe `thumbnail/<uuid>.jpg` sobre sí mismo en lugar de crear un segundo archivo, y no deja variantes a medias de un intento interrumpido. Un worker que se inventa un nombre nuevo en cada ejecución, con tres intentos y envíos de veinte fotos, llena S3 de objetos huérfanos que pagas todos.

Hay una línea del job que en S3 no puede funcionar: `Storage::disk('photos_private')->path(...)`. En un disco `local` devuelve una ruta del sistema de archivos. En un disco `s3` devuelve la clave del objeto, que `exif_read_data` no puede abrir. Si el archivo no existe, el extractor devuelve un array vacío, así que no hay excepciones: las fotos simplemente salen sin EXIF. A decir verdad, en esta rama el EXIF falta también en local, porque `stripGps()` vuelve a codificar la imagen y, junto con el GPS, quita todos los metadatos antes de que se guarde el original. En la rama del capítulo 22 el EXIF se lee en el momento de la subida, del archivo subido y antes de `stripGps()`, y en el job queda solo como alternativa de respaldo.

Una última cosa sobre los batches. `UploadPhotosAction` llama a `Bus::batch($jobs)->dispatch()` sin `allowFailures()`, y con el comportamiento por defecto de Laravel el primer job que falla cancela el batch, que a partir de ese momento ya figura como `finished`. Las demás fotos se procesan igualmente, porque `ProcessPhoto` no comprueba si el batch se ha cancelado, pero `useBatchPoll` deja de consultar antes de que terminen. Con `allowFailures()` el problema se invierte: un batch con un fallo nunca llega a `finished`, y el polling no se detiene nunca. Si necesitas un estado fiable, calcúlalo a partir de las filas `Photo` del batch, que el endpoint ya devuelve una por una.

### Cuando el backend se convierte en el cuello de botella

En la rama, los bytes de las fotos siguen pasando por el backend, que quita los datos GPS y los escribe en `photos_private`. Para 20 archivos de 10 MB está bien. Si hicieran falta cientos de fotos a la vez, el siguiente paso sería la subida directa a S3: el backend firma una presigned URL de caducidad corta (15 minutos limitan el daño de una URL filtrada), el frontend hace el `PUT` directamente sobre el bucket y luego avisa al backend, que crea la fila `Photo` y encola el job. Tiene un coste: la eliminación de los datos GPS, que hoy ocurre antes de guardar el original, habría que pasarla al worker, y durante unos segundos el original con las coordenadas estaría en S3. A la escala del Photogallery no compensa, y por eso F4.3 dice 20 archivos.

### El 403 en las variantes

Durante el test end-to-end de T080, la subida real con el queue worker en marcha que el capítulo 20 deja para hacer a mano, las variantes se generaban, pero el navegador recibía `403 Forbidden` en las imágenes `medium` y `large`. El enlace simbólico `public/storage` estaba bien, y un `curl` directo daba el mismo 403.

El culpable era la opción `serve` de los discos locales. En Laravel 13, un disco `local` con `'serve' => true` registra una ruta `GET <url del disco>/{path}` que sirve los archivos a través de PHP, y un disco sin `url` la registra en `/storage`. El disco `local` del scaffolding tiene `serve` activada, así que su ruta `/storage/{path}` capturaba también `/storage/photos/...`. Para un disco privado esa ruta exige una URL firmada: sin firma responde 403, o 404 en producción.

La configuración de la rama, en `config/filesystems.php`, activa `serve` solo en el disco público de las variantes y la quita del disco `local`:

```php
'local' => [
    'driver' => 'local',
    'root' => storage_path('app/private'),
    'throw' => false,
    'report' => false,
],

// ...

'photos' => env('PHOTOS_DRIVER', 'local') === 's3'
    ? [ /* driver s3, bucket AWS_BUCKET_PUBLIC */ ]
    : [
        'driver' => 'local',
        'root' => storage_path('app/public/photos'),
        'url' => rtrim(env('APP_URL', 'http://localhost'), '/').'/storage/photos',
        'visibility' => 'public',
        'serve' => true,
        'throw' => true,
    ],
```

Un bug así no lo encuentra ningún test unitario: hace falta el recorrido completo, de la subida al navegador.

### La revisión de la fase

Junto con T080 arrancó la revisión de fin de fase, con Claude y Gemini sobre las Fases 5 y 6. El informe `docs/BATCH-2026-04-29.md` recoge, entre otros, estos findings. El más grave era un path traversal: las rutas de las variantes usaban el nombre de archivo que enviaba el cliente, y el fix usa el UUID de la foto y `basename()` sobre el nombre guardado. Luego, un archivo temporal de `PhpExifExtractor::stripGps()`, con el original completo y su GPS, que nunca se borraba; en la rama lo borra una `register_shutdown_function`. Estaba el dispatch dentro de la transacción, que ya hemos visto. Y un High sobre las fotos legibles sin autenticación, algo que el diseño prevé para el visitante anónimo de `REQUIREMENTS.md`: ahí la respuesta correcta era confirmar la intención, no cambiar el código.

Las cifras al final de la fase: 175 tests de backend en verde (más uno omitido y un fallo de CORS que ya estaba), cero errores de TypeScript, 110 KB gzip para el bundle principal después del code splitting por página (el presupuesto es de 200 KB).

::: {.callout .callout-deep-dive}
[Bajo el capó]{.callout-title}

En esta rama, `GET /photos/batch/{batchId}` encuentra las fotos del batch por usuario y por un `created_at` posterior a la creación del batch, una aproximación que confunden dos subidas muy seguidas. La columna `batch_id` en `photos` llega con las correcciones del capítulo 22 (`book/cap-15-post-review-fixes`).
:::

## 21.2 La página de registro que faltaba

### Cómo te das cuenta

Recorres la aplicación desde cero como un usuario nuevo y encuentras una página de login bien hecha, con validación y errores del servidor. Lo que no hay es manera de crear una cuenta: ningún enlace, ninguna ruta `/register`.

Vas a comprobarlo. En `REQUIREMENTS.md` el registro está: F9.1 "Email + password registration" y la user story US-30. En el backend, `POST /api/v1/auth/register` existe y lo cubre `AuthControllerTest`. En `src/data/copy.ts` están hasta los textos, desde `registerHeading: 'Create a new account'` hasta `noAccount: "Don't have an account?"`. Solo faltaba la interfaz que los usara.

### Qué decía el plan

Abre `TASKS.md` y busca la tarea de las páginas del frontend:

```markdown
### T070 — Pages: `GalleryPage`, `FavoritesPage`, `AlbumPage`, `LoginPage`, `NotFoundPage`
- **Status:** [x]
- **Acceptance:**
  - Each page reads filters from URL search params and feeds them into `usePhotos`.
  - LoginPage uses `useAuth.login`; redirects to intended route.
  - NotFoundPage renders empty state.
- **Commit:** `feat(frontend): page components wired to hooks`
```

El problema está en los criterios de aceptación. Quien escribió el requisito pensaba en "página de autenticación", es decir, login y registro. Pero la tarea solo dice `useAuth.login`, y Claude implementó exactamente eso. El informe del 29 de abril cierra T070 con "LoginPage (form + 422 errors)".

Un `[x]` en `TASKS.md` es una declaración de intenciones. La garantía llega con las pruebas: un commit, un test que ejercite el flujo, una captura del navegador. Vale para un compañero humano igual que para un agente.

### La auditoría: qué más está cerrado sin estar hecho

Si se ha colado un agujero así, hay más. Antes de corregir conviene una auditoría, también en Plan Mode:

```text
Lee docs/TASKS.md y, para cada tarea marcada con [x]:
1. Identifica el código que debería implementarla
2. Comprueba que ese código existe de verdad en el repositorio
3. Compara los criterios de aceptación de la tarea con los requisitos
   de REQUIREMENTS.md que la tarea dice cubrir
4. Señala cada caso en que la tarea está cerrada pero la implementación
   parece parcial, inexistente o más estrecha que el requisito

No corrijas nada: primero quiero la lista completa de huecos.
```

En el Photogallery esta auditoría tiene su propia tarea, T107, y una salida versionada: `docs/SPEC-COVERAGE.md`. Compara las 42 subsecciones de `DESIGN.md` con el código y los tests: 27 implementadas, 11 parciales, 4 ausentes. Entre las ausencias hay archivos que el diseño prometía y nadie creó, como `MarkFavoriteAction.php` (la lógica acabó en el controlador) o el test `BatchProgressTest.php`. No todo hay que corregirlo enseguida, pero cada entrada se convierte en una decisión: se hace, se actualiza el diseño o se declara fuera de alcance.

### El fix: un componente, dos modos

El registro bloquea el onboarding, así que va primero. La solución de la rama reutiliza `LoginPage` en lugar de crear un segundo componente: un estado `mode` alterna entre login y registro.

```tsx
type AuthMode = 'login' | 'register';

export function LoginPage() {
  const loginMutation = useLogin();
  const registerMutation = useRegister();
  const [mode, setMode] = useState<AuthMode>('login');
  // name, email, password, passwordConfirmation, errors...
  const isLogin = mode === 'login';

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // onSuccess navega a '/', onError muestra los errores 422 por campo
    if (isLogin) {
      loginMutation.mutate({ email, password }, { onSuccess, onError });
    } else {
      registerMutation.mutate(
        { name, email, password, password_confirmation: passwordConfirmation },
        { onSuccess, onError },
      );
    }
  };

  const toggleMode = () => setMode(isLogin ? 'register' : 'login'); // y limpia los errores
  // ... JSX del formulario
}
```

En modo registro el formulario muestra también los campos `name` y `password_confirmation`, el título y el botón toman los textos de `copy.auth`, y el enlace de abajo llama a `toggleMode` sin cambiar de página. La corrección completa: `useRegister` en `src/hooks/useAuth.ts` junto a `useLogin`, el estado `mode`, los campos extra en el JSX, los errores 422 por campo en los dos modos, la prueba manual del flujo (creación de la cuenta, login automático, redirección a la galería) y un commit que declara el hueco de alcance.

El commit importa: un mensaje como `fix(frontend): add register mode to LoginPage (scope gap in T070)` le explica a quien lea el historial por qué se reabrió una tarea cerrada. La ruta `/register` llegó después, con T121 de la Fase 14 (`feat(frontend): empty state CTA + /register route`), que la hace apuntar a la misma `LoginPage`.

Hay un detalle que la misma auditoría debería haber encontrado, y lo uso para el ejercicio de final de capítulo: `mode` siempre empieza en `'login'`, así que quien abre `/register` ve igualmente el formulario de login.

### El prompt de cierre de la wave

Para no repetir el error, al final de cada oleada uso un prompt de cierre fijo:

```text
Antes de marcar esta wave como completada, comprueba:

1. Para cada tarea marcada con [x]: ¿existe en el repositorio el código que
   corresponde a los criterios de aceptación? Quiero la ruta del archivo,
   no "debería existir".
2. Releyendo los requisitos que esta wave dice cubrir,
   ¿hay algo que las tareas no cubran?
3. ¿Existe al menos un test (automático, o manual documentado) que
   ejercite cada flujo de usuario citado en esos requisitos?

Si encuentras huecos, enuméralos. No cierres la wave hasta que la lista esté
vacía o las excepciones estén documentadas explícitamente como fuera de alcance.
```

Ningún prompt garantiza cero huecos, pero este obliga al control cruzado entre requisitos y tareas, justo el punto donde el flujo normal se rompe.

### El drift entre requisitos y tareas

El caso del registro tiene nombre: drift entre requisitos y tareas, la distancia que se acumula entre lo que dicen los requisitos y lo que implementan las tareas. Nace cuando conviertes un requisito en tareas con decisiones implícitas: "Auth" puede significar solo login, login y registro, o también el reset de la contraseña. Si la decisión no acaba en los criterios de aceptación, el resultado cubre menos que el requisito.

El drift va también en la otra dirección, del código hacia los documentos. AC-F8-5 dice que `GET /photos?is_favorite=1` devuelve los favoritos del usuario, pero `IndexPhotosRequest` y el frontend usan el parámetro `favorites`. El código funciona, los tests pasan, y el criterio de aceptación describe una API que no existe.

La defensa son criterios explícitos: cada página, ruta y endpoint del requisito aparece por su nombre en la tarea. Un criterio verificable suena así: "página `/login` funcionando, formulario de registro accesible desde `/register` y desde el selector de la página de login, llamada a `POST /api/v1/auth/register` con gestión de los errores 422".

## 21.3 Fotos favoritas, de booleano a tabla pivot

### El requisito

Cada usuario quiere su propia lista de fotos favoritas, que se gestiona con un clic y se encuentra en una vista dedicada. En `REQUIREMENTS.md` es la sección F8:

```markdown
### F8 — Favorites
- F8.1 Per-member favorites: any authenticated user can favorite any photo (many-to-many `users ↔ photos` via `favorites` pivot table)
- F8.3 Optimistic UI (heart fills before the request returns)
- F8.5 Favorite count visible per photo (how many users favorited it)
```

Con criterios como AC-F8-1: `PUT /photos/{id}/favorite` es idempotente, dos llamadas seguidas devuelven 204 e insertan una sola fila en `favorites`. Una funcionalidad pequeña y acotada, el tipo adecuado para añadir sobre la marcha.

### El error de modelado

La primera versión del diseño tenía la solución más obvia: una columna booleana `is_favorite` en la tabla `photos`, con un índice compuesto sobre `is_favorite` y `created_at`. Funciona mientras haya un solo usuario. Una columna en la foto representa un favorito global: la foto es favorita para todos o para nadie.

La relación entre usuarios y fotos favoritas es de N a M, y necesita una tabla intermedia. Si le pides a Claude "añade las fotos favoritas" sin más contexto, la columna booleana es una propuesta plausible, y aquí es donde hace falta alguien que supervise. Antes de aceptarla pregunta: "¿la relación usuario-foto favorita es de 1 a N o de N a M?". La respuesta decide el esquema, los endpoints y los componentes.

### La Fase 6.5

La corrección es una fase insertada entre la 6 y la 7, con wave 1.5 en la tabla resumen de `TASKS.md`:

```text
T090  Migración: pivot favorites, drop de is_favorite
T091  Relaciones favoritedBy y favoritePhotos
T092  PhotoController favorite/unfavorite, PhotoData con favorites_count
T093  Filament PhotoResource: favorites_count en lugar del toggle
T094  Hooks y componentes del frontend
T095  Tests (A marca como favorita la foto de B: aparece solo en la lista de A)
```

Fíjate en los IDs. T090-T095 ya existían: T090-T094 son los hooks de la Fase 9, T095 abre la Fase 10. La fase insertada retomó la numeración después de T080, y ahora `TASKS.md` tiene dos T090 distintas. Ningún test lo detecta, pero "haz la T092" dicho a Claude se vuelve ambiguo, igual que los mensajes de commit y la plantilla del PR, que pide citar los IDs. Cuando insertes una fase sobre la marcha, usa IDs posteriores al último existente (aquí, desde T125) o un prefijo propio: por eso el prompt reutilizable pide IDs que no choquen.

### La migración: crear, trasvasar, eliminar

La columna `is_favorite` ya existía y tenía datos, así que la migración hace tres cosas en secuencia: crea la estructura nueva, copia en ella los datos existentes y elimina la vieja. Esta es `2026_04_30_135152_create_favorites_table.php`:

```php
public function up(): void
{
    Schema::create('favorites', function (Blueprint $table) {
        $table->foreignUuid('user_id')->constrained('users')
            ->cascadeOnUpdate()->cascadeOnDelete();
        $table->foreignUuid('photo_id')->constrained('photos')
            ->cascadeOnUpdate()->cascadeOnDelete();
        $table->timestamp('created_at')->useCurrent();

        $table->primary(['user_id', 'photo_id']);
        $table->index('photo_id');
    });

    // Data migration: move existing is_favorite=true to pivot rows
    if (Schema::hasColumn('photos', 'is_favorite')) {
        DB::table('photos')
            ->where('is_favorite', true)
            ->orderBy('id')
            ->each(function (object $photo) {
                DB::table('favorites')->insertOrIgnore([
                    'user_id' => $photo->user_id,
                    'photo_id' => $photo->id,
                    'created_at' => now(),
                ]);
            });

        Schema::table('photos', function (Blueprint $table) {
            $table->dropIndex('photos_favorite_created_idx');
            $table->dropColumn('is_favorite');
        });
    }
}
```

Las claves son UUID (`foreignUuid`) porque todo el proyecto usa UUID v7. La clave primaria compuesta impide los duplicados en la propia base de datos, incluso con dos peticiones en paralelo, y `cascadeOnDelete` hace desaparecer los favoritos junto con la foto o con el usuario. El `hasColumn` hace que la migración sea segura en una base de datos nueva, donde `is_favorite` nunca existió. Los favoritos existentes pasan al propietario de la foto, la única atribución posible para un flag global, y `down()` hace el camino inverso. El mismo esquema en tres tiempos sirve para cualquier refactoring con datos que conservar.

### Relaciones y endpoints idempotentes

Con la tabla en su sitio, las relaciones en los modelos son un par de líneas cada una:

```php
// Photo
public function favoritedBy(): BelongsToMany
{
    return $this->belongsToMany(User::class, 'favorites')
        ->withPivot('created_at');
}
```

`User::favoritePhotos()` es su reflejo, con `Photo::class`. Se usa `withPivot('created_at')` en lugar de `withTimestamps()` porque el pivot solo tiene `created_at`.

Para la API, la tentación es un único endpoint de toggle con el `toggle()` de Eloquent. El proyecto usa en cambio dos endpoints idempotentes, como pide AC-F8-1:

```php
// PUT /photos/{photo}/favorite: idempotente, responde siempre 204
public function favorite(Request $request, Photo $photo): Response
{
    if (! $request->user()?->tokenCan(TokenAbility::PhotosWrite->value)) {
        throw new AuthorizationException;
    }

    $request->user()->favoritePhotos()->syncWithoutDetaching([$photo->id]);

    return response()->noContent();
}
```

`unfavorite()` es idéntico, con `detach($photo->id)` sobre `DELETE`. Un toggle repetido por un reintento de red, o por un doble clic, invierte el estado dos veces y te deja donde empezaste. `PUT` y `DELETE` expresan el estado final que quieres, y repetirlos no cambia nada. La comprobación `tokenCan` es la regla del proyecto para todo endpoint que modifica datos: el token de Sanctum debe tener la ability `photos:write`.

### El frontend: optimistic UI

El corazón de la tarjeta tiene que cambiar al hacer clic, antes de que responda el servidor (F8.3). Es la **optimistic UI**: actualizas la caché como si la petición ya hubiera salido bien y solo das marcha atrás si el servidor responde con un error. Este es `useToggleFavorite` en `src/hooks/usePhotos.ts`, con algunas líneas omitidas:

```typescript
export function useToggleFavorite() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, isFavorite }: { id: string; isFavorite: boolean }) =>
      isFavorite ? removeFavorite(id) : addFavorite(id),
    onMutate: async ({ id, isFavorite }) => {
      await queryClient.cancelQueries({ queryKey: ['photo', id] });
      await queryClient.cancelQueries({ queryKey: ['photos'] });
      const previousPhoto = queryClient.getQueryData<SingleResponse<Photo>>(['photo', id]);
      // ... actualización de la caché ['photo', id]

      // Update all infinite list caches (photos list)
      queryClient.setQueriesData<{ pages: PaginatedResponse<Photo>[]; pageParams: unknown[] }>(
        { queryKey: ['photos'] },
        (old) => {
          if (!old) return old;
          return {
            ...old,
            pages: old.pages.map((page) => ({
              ...page,
              data: page.data.map((photo) =>
                photo.id === id
                  ? { ...photo, is_favorite: !isFavorite,
                      favorites_count: photo.favorites_count + (isFavorite ? -1 : 1) }
                  : photo,
              ),
            })),
          };
        },
      );
      return { previousPhoto };
    },
    onError: (_err, { id }, context) => {
      if (context?.previousPhoto) {
        queryClient.setQueryData(['photo', id], context.previousPhoto);
      }
      queryClient.invalidateQueries({ queryKey: ['photos'] });
    },
    // onSettled invalida ['photos'] y ['photo', id]
  });
}
```

La primera versión fallaba en un detalle: la galería es una `useInfiniteQuery`, así que la actualización optimista tiene que tocar todas las páginas de las listas `['photos']`, además de la caché de la foto individual. Sin eso, el corazón se encendía en el lightbox pero no en la cuadrícula; la revisión de la Fase 5 lo había marcado como High. `mutationFn` elige `PUT` o `DELETE` según el estado actual, así que el toggle solo existe en la interfaz y la API sigue siendo idempotente.

En la tarjeta, `PhotoCard.tsx`:

```tsx
const handleFavoriteClick = (e: React.MouseEvent) => {
  e.stopPropagation();
  toggleFavorite.mutate({ id: photo.id, isFavorite: photo.is_favorite });
};

// ...

<button
  type="button"
  onClick={handleFavoriteClick}
  aria-label={photo.is_favorite ? copy.favorites.remove : copy.favorites.add}
  className="..."
>
  <Heart className={photo.is_favorite ? 'fill-red-500 text-red-500' : 'text-white'} />
  {photo.favorites_count > 0 && <span className="...">{photo.favorites_count}</span>}
</button>
```

Las clases de Tailwind están abreviadas; en el archivo hay muchas más.

`stopPropagation()` evita que el clic en el corazón abra el lightbox. El badge muestra `favorites_count` (F8.5), el total de todos los usuarios, mientras que `is_favorite` vale para quien está mirando. La vista dedicada es la ruta `/favorites`, que monta `FavoritesPage` y llama a la API con `favorites=1`. El flujo lo cubre `e2e/favorites.spec.ts` en Playwright, con la API mockeada.

### Cuánto se tarda, y con cuántos agentes

En la primera edición cronometré una funcionalidad de este tamaño: algo más de dos horas desde los requisitos hasta el merge, tests y revisión incluidos. La parte más larga son los requisitos, unos veinte minutos de discusión con Claude, y es tiempo que se recupera: un modelado equivocado o una API que no encaja con el frontend cuestan más cuando los descubres después.

Para funcionalidades así basta un desarrollador con un solo agente, en secuencia, en la misma sesión. Las tareas dependen unas de otras (el frontend no se escribe antes de que exista la API), así que no hay nada que paralelizar. Los worktrees y las sesiones en segundo plano (capítulo 20) sirven cuando las tracks son de verdad independientes, como la Fase 4 y la Fase 6.

## 21.4 PR que tocan backend y frontend

### Un PR o dos

Las tres funcionalidades del capítulo cruzan la misma frontera: los favoritos tienen una migración, dos endpoints, un recurso de Filament y un hook con optimistic UI. El orden ideal es un PR para el backend (migración, API, tests de integración) y, después del merge, otro para el frontend. Cada PR se revisa por separado y el frontend consume una API ya estable. Con Claude Code es más habitual el PR único, porque los dos lados nacen en la misma sesión y separarlos después significa reescribir el historial. Si quieres los dos PR sin ese trabajo, plantea la separación desde el principio: un worktree por lado, como en el capítulo 20, con la rama del frontend partiendo de la del backend.

El PR único aguanta mientras la revisión lo trate como lo que es. En el proyecto pasó uno muy grande: las Fases 3-14 llegaron a `main` con un solo squash merge, el commit `a0a5437`, 171 archivos cambiados.

### Dos pasadas de revisión sobre el mismo PR

Una sola pasada sobre un PR cross-stack mezcla las perspectivas y se queda en la superficie de ambas. Mejor dos pasadas, cada una con un foco declarado en el prompt. La primera mira el backend: consultas, permisos de cada endpoint, errores, idempotencia de los jobs, transacciones y dispatch, N+1. La segunda mira el frontend: `aria-label` y teclado, estados de carga y de error, optimistic UI y rollback, peso del bundle, cómo se ve en móvil. El capítulo 22 muestra cómo hacerlas con `/code-review` y con un segundo modelo.

### El orden del deploy

Incluso con un PR único, el deploy sigue siempre el mismo orden: primero el backend, luego el frontend.

Si llega primero el frontend, llama a endpoints que no existen y los usuarios ven errores. Si llega primero el backend, el frontend antiguo sigue funcionando con los endpoints que ya había, y el nuevo encuentra las APIs que espera. La secuencia es, por tanto: deploy del backend, comprobar que el frontend actual sigue funcionando, deploy del frontend, comprobar los flujos nuevos.

En GitHub Actions se convierte en un solo workflow, con una comprobación entre los dos deploys. El deploy real del Photogallery en AWS es el capítulo 23.

### Feature flags para las funcionalidades grandes

Para una funcionalidad tan grande como el batch hay una opción más, el feature flag: despliegas todo el backend, pero la parte nueva del frontend queda oculta detrás de un flag y solo la ve el equipo, o una parte de los usuarios, hasta que la abres a más gente. A la escala del Photogallery es excesivo. Con muchos usuarios activos marca la diferencia entre un lanzamiento controlado y un incendio que apagar de madrugada.

### La checklist antes del merge

El repo ya tiene un `.github/PULL_REQUEST_TEMPLATE.md` que pide los IDs de las tareas de `TASKS.md`, las secciones de `DESIGN.md` afectadas y el plan de pruebas (`php artisan test --compact`, `npm test -- --run`, Pint, Prettier, ESLint). Para los PR cross-stack añado esta lista:

```text
Backend
[ ] Ninguna consulta N+1 en las rutas nuevas (query log o QueryDetector)
[ ] Permisos en cada endpoint (autenticado o público, ability del token)
[ ] Migración probada en una BD vacía y en una BD con datos

Frontend
[ ] Ningún console.error en desarrollo
[ ] Componentes accesibles (aria-label, teclado)
[ ] Bundle dentro del presupuesto del proyecto (200 KB gzip)

Cross-stack
[ ] Contrato de la API idéntico entre frontend y backend (campos y parámetros)
[ ] Errores 401, 403, 404, 422, 500 mostrados correctamente
[ ] Orden del deploy escrito en la descripción del PR
```

La línea del contrato de la API es la que habría detectado el `favorites` frente a `is_favorite` de la sección 21.2.

## Resumen {.unlisted}

- Una funcionalidad sobre la marcha entra por los documentos: requisitos, diseño y tareas aprobados antes del código, con el prompt reutilizable de la sección 21.1 en Plan Mode.
- Para el batch en S3 hacen falta un job idempotente (una ruta determinista para cada variante), reintentos con esperas crecientes y el dispatch después del commit de la transacción. El paso a S3 y SQS es configuración, siempre que ningún archivo de `app/` use rutas locales.
- Una tarea cerrada no demuestra nada: pide rutas, tests y capturas, y cierra cada oleada con el prompt de verificación. El drift entre requisitos y tareas se previene con criterios de aceptación que nombran páginas, rutas y endpoints.
- Una relación de N a M necesita una tabla pivot, y un refactoring de esquema con datos sigue el orden crear, trasvasar, eliminar. Para los endpoints, prefiere `PUT` y `DELETE` idempotentes a un toggle.
- Una fase insertada sobre la marcha recibe IDs de tarea nuevos, nunca los que ya están en uso.
- Los PR cross-stack se revisan en dos pasadas (backend, luego frontend) y se despliegan siempre con el backend primero.

## Ejercicio {.unlisted}

Parte de la rama `book/cap-14-phases-complete` del repo companion y arregla el hueco que dejó T121: la ruta `/register` monta `LoginPage`, pero el formulario siempre arranca en modo login.

1. En Plan Mode, lanza el prompt reutilizable de la sección 21.1 con esta descripción: "al abrir `/register` el formulario debe arrancar en modo registro; al abrir `/login`, en modo login; el selector sigue funcionando".
2. Haz que Claude añada a `TASKS.md` una tarea con un ID nuevo (T125) y criterios que nombren las dos rutas.
3. Ejecuta la tarea con Claude, con un test de Playwright en `e2e/auth.spec.ts` que abra `/register` y compruebe el título "Create a new account".
4. Cierra con el prompt de verificación de la sección 21.2 y luego abre el PR con la plantilla del repo y la checklist cross-stack.

El ejercicio está completo cuando el nuevo test pasa junto con el resto de la suite (`npx playwright test` en la carpeta `frontend`) y T125 está marcada con `[x]` con el commit que la implementa. Como alternativa, aplica los mismos cuatro pasos a una funcionalidad pequeña de tu backlog, como un filtro de búsqueda o una exportación a CSV.
