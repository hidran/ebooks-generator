# 21. Upload de avatares con `$_FILES` y GD

El upload de avatares hace más realista el User Management System: el form debe enviar archivos, PHP debe validarlos, moverlos a una carpeta controlada, crear imágenes derivadas y guardar la ruta en el registro del usuario.

Hay que decirlo enseguida, porque es lo más importante del capítulo: **el upload de archivos es el input más peligroso que una aplicación web puede recibir**. Un campo de texto, en el peor de los casos, te inyecta SQL o HTML — y ya hemos visto cómo defenderte. Un archivo, en cambio, acaba *en el disco de tu server*, y si un atacante consigue subir un archivo `.php` a una carpeta servida por el web server y luego invocarlo por URL, ese código **se ejecuta en tu server**. Es el salto de "el atacante manipula una página" a "el atacante ejecuta código arbitrario", y es la razón por la que cada línea de este capítulo es, en el fondo, una medida defensiva. Tenlo presente mientras lees: aquí no solo estamos moviendo imágenes, estamos cerrando la puerta más ancha de una aplicación web.

## Opciones de upload

Los ajustes están en `config.php`:

```php
'uploadDir' => 'avatar',
'mimeTypes' => ['image/jpeg', 'image/png', 'image/gif'],
'maxFileSize' => convertMaxUploadSizeToBytes(),
'thumbnailWidth' => 120,
'intermediateWidth' => 800,
```

Código completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-21/es/parte-06/cap-21/listing-01.php)

Fuente real: [`config.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/config.php).

Tres decisiones de seguridad están ya aquí, declaradas en un único sitio en lugar de dispersas por el código. `uploadDir` es la carpeta de destino: una sola, controlada, no "donde caiga". `mimeTypes` es la **whitelist** de los tipos permitidos — de nuevo el principio del capítulo anterior, enumerar lo que está permitido en lugar de intentar adivinar lo que está prohibido. `maxFileSize` es el límite de tamaño, leído de la configuración de PHP mediante `convertMaxUploadSizeToBytes()` para que el form y la validación del lado servidor hablen el mismo idioma y no se contradigan. Centralizar estas tres cosas en `config.php` no es solo orden: significa que el día que quieras añadir `image/webp` o subir el límite, cambias *un* valor y todo lo demás se ajusta.

## Form multipart

El form debe declarar `multipart/form-data` y enviar también `MAX_FILE_SIZE`:

```php
<form enctype="multipart/form-data" class="mt-4" action="controller/updateRecord.php" method="post">
    <input type="hidden" name="id" value="<?= $user['id'] ?>">
    <input type="hidden" name="action" value="<?= $action ?>">
```

Código completo: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-21/es/parte-06/cap-21/listing-02.php)

Fuente real: [`view/userForm.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/view/userForm.php).

El atributo `enctype="multipart/form-data"` es obligatorio: sin él, el browser envía solo el *nombre* del archivo, no su contenido. Es el primer error que comete todo el mundo cuando el upload "no funciona y no entiendo por qué" — el archivo no llega porque el form no está declarado para transportarlo. El `multipart` divide la petición en partes separadas, una por cada campo, y los bytes del archivo viajan en una de ellas.

```php
<input type="hidden" name="MAX_FILE_SIZE" value="<?= getConfig('maxFileSize') ?>">
<input type="file" accept="<?= implode(',', getConfig('mimeTypes')) ?>" id="avatar" class="form-control"
       value="<?= $user['avatar'] ?>" name="avatar">
```

Código completo: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-21/es/parte-06/cap-21/listing-03.php)

Fuente real: [`view/userForm.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/view/userForm.php).

Aquí hay dos ayudas del lado cliente, y es esencial entender que son **solo** ayudas. El atributo `accept` hace que el diálogo de selección del sistema operativo muestre por defecto solo imágenes: comodidad para el usuario honesto, nada más. El campo oculto `MAX_FILE_SIZE` pide al browser que rechace archivos demasiado grandes antes incluso de empezar el upload, ahorrando ancho de banda. Pero ambos viven en el browser, y **el browser está bajo el control del atacante**. Con un par de clics en las herramientas de desarrollo, o con una petición construida a mano con `curl`, el atributo `accept` desaparece y `MAX_FILE_SIZE` se convierte en lo que él quiera. Son pistas para la interfaz, no controles de seguridad.

![El formulario de usuario con el campo de carga del avatar. El formulario declara `enctype="multipart/form-data"` y muestra el tamaño máximo de subida calculado a partir de `php.ini`.](figures/cap-21/user-form-upload.png)

La regla, que a estas alturas reconoces porque es la misma de todo el libro, es: **la validación de verdad está en el server**. El cliente embellece la experiencia; el server decide. Y es exactamente lo que hace la función del próximo apartado.

## Validar el archivo

`validateFileUpload()` comprueba el error de upload, el MIME real y el tamaño:

```php
function validateFileUpload(array $file): array
{
    $errors = [];

    if ($file['error'] !== UPLOAD_ERR_OK) {
        $errors[] = getUploadError($file['error']);
        return $errors;
    }
    $config = require 'config.php';

    $fileinfo = new finfo(FILEINFO_MIME_TYPE);
    $mimeType = $fileinfo->file($file['tmp_name']);
```

Código completo: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-21/es/parte-06/cap-21/listing-04.php)

Fuente real: [`functions.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/functions.php).

La función hace tres comprobaciones, en un orden que no es casual. La primera es `$file['error'] !== UPLOAD_ERR_OK`. Cuando PHP recibe un upload, rellena `$_FILES['avatar']['error']` con un código: `UPLOAD_ERR_OK` (cero) si todo fue bien, o una de las constantes que señalan un problema — archivo demasiado grande para el límite del `php.ini`, upload interrumpido a mitad, carpeta temporal ausente. Comprobar este código **primero** es esencial: si el upload falló, `tmp_name` puede estar vacío y cada comprobación posterior trabajaría sobre la nada. Es de nuevo el *fail fast*: si no hay un archivo válido, no tiene sentido continuar.

La segunda comprobación es el corazón de la seguridad, y es la que casi todo el mundo hace mal. Para saber qué tipo de archivo es, la función no mira `$_FILES['avatar']['type']`, y tampoco mira la extensión del nombre. Usa **`finfo`**, que inspecciona los **bytes reales** del archivo para determinar su tipo. ¿Por qué? Porque `$_FILES['type']` es una cadena que **llega del browser**: el atacante la escribe como quiere. Puede coger un script PHP malicioso, llamarlo `foto.jpg`, y hacer que el browser declare `Content-Type: image/jpeg`. La extensión dice `.jpg`, el tipo declarado dice imagen, pero el contenido es código ejecutable. `finfo` no se deja engañar: abre el archivo, lee los primeros bytes (los llamados *magic numbers*, la firma que identifica el formato) y te dice lo que **realmente** es. Regla para grabar en la memoria: **el tipo de un archivo subido se determina a partir de su contenido, nunca de lo que declara quien lo envía**.

La tercera comprobación compara `$file['size']` con `maxFileSize`, y es la defensa del lado servidor contra los archivos enormes — la de verdad, que no depende del `MAX_FILE_SIZE` del form que el atacante puede ignorar. La función recoge todos los errores en un array y los devuelve juntos, así el usuario ve de una vez todo lo que está mal, en lugar de descubrirlo un problema cada vez.

## Guardar con nombre seguro

`handleAvatarUpload()` genera un nombre aleatorio y usa la extensión derivada del MIME:

```php
function handleAvatarUpload(array $file, ?int $userId = null): ?string
{
    $config = require 'config.php';
    $uploadDir = $config['uploadDir'] ?? 'avatar';
    $uploadDirPath = realpath(__DIR__) . '/' . $uploadDir . '/';
    $mimeMap = [
        'image/jpeg' => 'jpg',
        'image/png' => 'png',
        'image/gif' => 'gif'
    ];
    $fileinfo = new finfo(FILEINFO_MIME_TYPE);
    $mimeType = $fileinfo->file($file['tmp_name']);
```

Código completo: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-21/es/parte-06/cap-21/listing-05.php)

Fuente real: [`functions.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/functions.php).

Fíjate en cómo se construye el nombre con el que se guardará el archivo, porque cada pieza evita un ataque. La extensión **no** se toma del nombre original: se deriva del MIME verificado con `finfo`, a través de `$mimeMap`. Si `finfo` dice `image/png`, la extensión será `png`, y punto. El nombre original del archivo — que sigue siendo una cadena elegida por el atacante — no toca el nombre final.

```php
$extension = $mimeMap[$mimeType];
$fileName = ($userId ? $userId . '_' : '') . bin2hex(random_bytes(8)) . '.' . $extension;
$res = move_uploaded_file($file['tmp_name'], $uploadDirPath . $fileName);
return $res ? $uploadDir . '/' . $fileName : null;
```

Código completo: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-21/es/parte-06/cap-21/listing-06.php)

Fuente real: [`functions.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/functions.php).

El nombre final es un valor aleatorio, `bin2hex(random_bytes(8))`, eventualmente prefijado con el id del usuario. No usar nunca el nombre original enviado por el usuario no es tiquismiquis: resuelve tres problemas de una vez. Primero, el **path traversal**: un nombre como `../../index.php` intentaría escribir fuera de la carpeta de upload, sobrescribiendo archivos de la aplicación — un nombre aleatorio no contiene rutas. Segundo, la **sobrescritura**: dos usuarios que suben `avatar.jpg` no se pisan, porque los nombres generados son únicos. Tercero, de nuevo la **ejecución**: aunque algo se hubiera escapado de las comprobaciones, el archivo ya no lleva una extensión elegida por el atacante.

`move_uploaded_file()` merece una nota aparte: no es un mero sinónimo de `rename()` o `copy()`. Esta función **verifica** que `tmp_name` sea de verdad un archivo llegado a través de un upload HTTP de esta petición, y no una ruta cualquiera del sistema de archivos que un atacante podría haber inyectado en `$_FILES`. Es una comprobación más, gratis, y no hay motivo para usar `copy()` en su lugar cuando se mueven uploads. Fíjate por último en que la función devuelve `null` si algo falla: quien la llama debe gestionar ese caso y no dar por supuesto que siempre hay una ruta.

## Thumbnail e imagen intermedia

El proyecto crea dos versiones de la imagen:

```php
function createThumbnailAndIntermediate(string $avatarPath): void
{
    $config = require 'config.php';
    $fileName = basename($avatarPath);
    $uploadDirPath = getUploadDir();
    $thumbnailPath = $uploadDirPath . 'thumbnail_' . $fileName;
    $intermediatePath = $uploadDirPath . 'intermediate_' . $fileName;
    $sourcePath = $uploadDirPath . $fileName;
    $thumbnailWidth = $config['thumbnailWidth'] ?? 120;
    $intermediateWidth = $config['intermediateWidth'] ?? 800;
```

Código completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-21/es/parte-06/cap-21/listing-07.php)

Fuente real: [`functions.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/functions.php).

Crear una thumbnail (120px para el listado) y una versión intermedia (800px para la visualización) es ante todo una decisión de sentido común: servir la imagen original a plena resolución dentro de una tabla de listado desperdicia ancho de banda y ralentiza la página. Pero hay un segundo efecto, menos obvio y valioso desde el punto de vista de la seguridad. La función `resizeImage()`, que usa la librería **GD**, lee la imagen original y **redibuja una nueva** desde cero. Este proceso, de hecho, recodifica los píxeles y descarta todo lo que no sea dato-imagen: cualquier payload escondido en los metadatos o código pegado al final de un falso JPEG no sobrevive a la regeneración. Pasar un upload a través de GD es una forma de **sanitización**: lo que sale es una imagen limpia, construida por ti, no el archivo que te llegó. `basename()` sobre la ruta es otra pequeña salvaguarda: elimina cualquier componente de carpeta, así ningún nombre puede hacer que las versiones derivadas se escriban fuera de la carpeta prevista.

## Eliminar imágenes antiguas

Cuando un usuario se elimina o cambia de avatar, los archivos derivados también deben eliminarse:

```php
function deleteUserImages(string $avatarPath): void
{
    if (!$avatarPath) {
        return;
    }
    $uploadDir = getUploadDir();
    $fileName = basename($avatarPath);
    $avatarFile = $uploadDir . $fileName;
    $thumbnail = $uploadDir . 'thumbnail_' . $fileName;
    $intermediate = $uploadDir . 'intermediate_' . $fileName;
```

Código completo: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-21/es/parte-06/cap-21/listing-08.php)

Fuente real: [`functions.php` en `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/functions.php).

Esta es la pieza que, en un tutorial apresurado, no estaría. Un upload parece "terminado" cuando el archivo está guardado, pero no lo está: has creado **tres** archivos (original, thumbnail, intermedia) y los has vinculado a un registro. El día que el usuario cambia de avatar, o se elimina, esos tres archivos deben eliminarse — de lo contrario la carpeta de upload se llena hasta el infinito de imágenes huérfanas que ya nadie sirve, ocupan espacio y, en el caso de datos personales, se quedan por ahí cuando no deberían. Pensar en el **ciclo de vida** completo de un archivo — creación *y* destrucción — es lo que distingue a quien ha escrito un upload en producción de quien copió uno de un tutorial. `basename()` vuelve aquí también, con la misma función defensiva de antes.

## En resumen

El upload de archivos es el input más arriesgado de una aplicación web, y este capítulo ha puesto en fila las defensas que lo hacen seguro. La **configuración centralizada** declara en un único sitio carpeta, tipos permitidos y límite de tamaño. El **form multipart** transporta los bytes, pero sus ayudas del lado cliente (`accept`, `MAX_FILE_SIZE`) son comodidades, no seguridad. La **validación del lado servidor** comprueba el código de error, el tamaño y — sobre todo — el MIME real con `finfo`, nunca el tipo declarado por el browser. El **guardado** usa un nombre aleatorio con extensión derivada del MIME verificado, y `move_uploaded_file()` para asegurarse de que es un upload auténtico. Las **imágenes derivadas** creadas con GD redimensionan y, como efecto colateral, sanean el contenido. La **eliminación** cierra el ciclo de vida, quitando los archivos cuando el registro cambia o desaparece.

El hilo, una vez más, es el de toda la Parte VI: no te fíes nunca del input, y determina la naturaleza de un dato a partir de su contenido, no de lo que el usuario declara. Con el upload lo que está en juego es simplemente mayor, porque aquí un error no manipula una página — pone código en tu server.
