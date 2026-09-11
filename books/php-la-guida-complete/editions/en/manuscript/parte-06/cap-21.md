# 21. Avatar Uploads with `$_FILES` and GD

Avatar uploads make the User Management System more realistic: the form must submit files, PHP must validate them, move them into a controlled directory, create derived images, and save the path on the user record.

Let's say it right away, because it is the most important thing in the chapter: **a file upload is the most dangerous input a web application can receive**. A text field, at worst, injects SQL or HTML into you — and we have seen how to defend against that. A file, instead, ends up *on your server's disk*, and if an attacker manages to upload a `.php` file into a directory served by the web server and then invoke it via URL, that code **runs on your server**. It is the leap from "the attacker manipulates a page" to "the attacker executes arbitrary code", and it is the reason every single line of this chapter is, at bottom, a defensive measure. Keep it in mind as you read: here we are not just moving images around, we are closing the widest door in a web application.

## Upload Options

The settings live in `config.php`:

```php
'uploadDir' => 'avatar',
'mimeTypes' => ['image/jpeg', 'image/png', 'image/gif'],
'maxFileSize' => convertMaxUploadSizeToBytes(),
'thumbnailWidth' => 120,
'intermediateWidth' => 800,
```

Full source: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-21/en/parte-06/cap-21/listing-01.php)

Real source: [`config.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/config.php).

Three security decisions are already here, declared in one place instead of scattered through the code. `uploadDir` is the destination directory: a single, controlled one, not "wherever". `mimeTypes` is the **whitelist** of allowed types — again the principle from the previous chapter, listing what is permitted instead of trying to guess what is forbidden. `maxFileSize` is the size limit, read from the PHP configuration through `convertMaxUploadSizeToBytes()` so that the form and the server-side validation speak the same language and do not contradict each other. Centralizing these three things in `config.php` is not just tidiness: it means that the day you want to add `image/webp` or raise the limit, you change *one* value and everything else adjusts.

## Multipart Form

The form must declare `multipart/form-data` and also send `MAX_FILE_SIZE`:

```php
<form enctype="multipart/form-data" class="mt-4" action="controller/updateRecord.php" method="post">
    <input type="hidden" name="id" value="<?= $user['id'] ?>">
    <input type="hidden" name="action" value="<?= $action ?>">
```

Full source: [listing-02.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-21/en/parte-06/cap-21/listing-02.php)

Real source: [`view/userForm.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/view/userForm.php).

The `enctype="multipart/form-data"` attribute is mandatory: without it, the browser sends only the file's *name*, not its content. It is the first mistake everyone makes when an upload "doesn't work and I don't understand why" — the file does not arrive because the form is not declared to carry it. The `multipart` encoding splits the request into separate parts, one for each field, and the file's bytes travel in one of them.

```php
<input type="hidden" name="MAX_FILE_SIZE" value="<?= getConfig('maxFileSize') ?>">
<input type="file" accept="<?= implode(',', getConfig('mimeTypes')) ?>" id="avatar" class="form-control"
       value="<?= $user['avatar'] ?>" name="avatar">
```

Full source: [listing-03.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-21/en/parte-06/cap-21/listing-03.php)

Real source: [`view/userForm.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/view/userForm.php).

Here there are two client-side aids, and it is essential to understand that they are **only** aids. The `accept` attribute makes the operating system's file picker show images by default: a convenience for the honest user, nothing more. The hidden `MAX_FILE_SIZE` field asks the browser to reject files that are too large before the upload even starts, saving bandwidth. But both live in the browser, and **the browser is under the attacker's control**. With a couple of clicks in the developer tools, or with a request hand-built using `curl`, the `accept` attribute disappears and `MAX_FILE_SIZE` becomes whatever they want. They are hints for the interface, not security controls.

![The user form with the avatar upload field. The form declares `enctype="multipart/form-data"` and shows the maximum upload size computed from `php.ini`.](figures/cap-21/user-form-upload.png)

The rule, which by now you recognize because it is the same throughout the book, is: **the real validation is on the server**. The client polishes the experience; the server decides. And that is exactly what the function in the next section does.

## Validating the File

`validateFileUpload()` checks the upload error, the real MIME, and the size:

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

Full source: [listing-04.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-21/en/parte-06/cap-21/listing-04.php)

Real source: [`functions.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/functions.php).

The function makes three checks, in an order that is not accidental. The first is `$file['error'] !== UPLOAD_ERR_OK`. When PHP receives an upload, it populates `$_FILES['avatar']['error']` with a code: `UPLOAD_ERR_OK` (zero) if everything went well, or one of the constants that signal a problem — file too large for the `php.ini` limit, upload interrupted halfway, temporary folder missing. Checking this code **first** is essential: if the upload failed, `tmp_name` may be empty and every later check would be working on nothing. It is again *fail fast*: if there is no valid file, there is no point continuing.

The second check is the heart of the security, and it is the one almost everyone gets wrong. To know what type of file it is, the function does not look at `$_FILES['avatar']['type']`, and it does not look at the extension of the name either. It uses **`finfo`**, which inspects the file's **real bytes** to determine its type. Why? Because `$_FILES['type']` is a string that **comes from the browser**: the attacker writes it however they like. They can take a malicious PHP script, call it `photo.jpg`, and have the browser declare `Content-Type: image/jpeg`. The extension says `.jpg`, the declared type says image, but the content is executable code. `finfo` is not fooled: it opens the file, reads the first bytes (the so-called *magic numbers*, the signature that identifies the format) and tells you what it **really** is. A rule to burn into memory: **the type of an uploaded file is determined from its content, never from what the sender declares**.

The third check compares `$file['size']` against `maxFileSize`, and it is the server-side defence against huge files — the real one, which does not depend on the form's `MAX_FILE_SIZE` that the attacker can ignore. The function collects all the errors into an array and returns them together, so the user sees at once everything that is wrong, instead of discovering it one problem at a time.

## Saving with a Safe Name

`handleAvatarUpload()` generates a random name and uses the extension derived from the MIME:

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

Full source: [listing-05.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-21/en/parte-06/cap-21/listing-05.php)

Real source: [`functions.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/functions.php).

Look at how the name the file will be saved under is built, because every piece prevents an attack. The extension is **not** taken from the original name: it is derived from the MIME verified with `finfo`, through `$mimeMap`. If `finfo` says `image/png`, the extension will be `png`, full stop. The original file name — which is still a string chosen by the attacker — never touches the final name.

```php
$extension = $mimeMap[$mimeType];
$fileName = ($userId ? $userId . '_' : '') . bin2hex(random_bytes(8)) . '.' . $extension;
$res = move_uploaded_file($file['tmp_name'], $uploadDirPath . $fileName);
return $res ? $uploadDir . '/' . $fileName : null;
```

Full source: [listing-06.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-21/en/parte-06/cap-21/listing-06.php)

Real source: [`functions.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/functions.php).

The final name is a random value, `bin2hex(random_bytes(8))`, optionally prefixed with the user id. Never using the original name sent by the user is not fussiness: it solves three problems at once. First, **path traversal**: a name like `../../index.php` would try to write outside the upload directory, overwriting application files — a random name contains no path. Second, **overwriting**: two users uploading `avatar.jpg` do not clobber each other, because the generated names are unique. Third, again **execution**: even if something had slipped past the checks, the file no longer carries an attacker-chosen extension.

`move_uploaded_file()` deserves a note of its own: it is not a mere synonym for `rename()` or `copy()`. This function **verifies** that `tmp_name` really is a file that arrived through an HTTP upload of this request, and not some arbitrary filesystem path that an attacker might have injected into `$_FILES`. It is one extra check, free of charge, and there is no reason to use `copy()` in its place when moving uploads. Note finally that the function returns `null` if something fails: the caller must handle that case and not assume a path is always there.

## Thumbnail and Intermediate Image

The project creates two versions of the image:

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

Full source: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-21/en/parte-06/cap-21/listing-07.php)

Real source: [`functions.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/functions.php).

Creating a thumbnail (120px for the list) and an intermediate version (800px for display) is first of all a sensible choice: serving the full-resolution original inside a listing table wastes bandwidth and slows the page. But there is a second, less obvious effect, and it is valuable from a security standpoint. The `resizeImage()` function, which uses the **GD** library, reads the original image and **redraws a new one** from scratch. This process effectively re-encodes the pixels and discards everything that is not image data: any payload hidden in the metadata or code appended to the tail of a fake JPEG does not survive the regeneration. Passing an upload through GD is a form of **sanitization**: what comes out is a clean image, built by you, not the file that reached you. `basename()` on the path is a further small safeguard: it strips any directory component, so no name can make the derived versions be written outside the intended folder.

## Deleting Old Images

When a user is deleted or changes their avatar, the derived files must be removed too:

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

Full source: [listing-08.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-21/en/parte-06/cap-21/listing-08.php)

Real source: [`functions.php` at `8769ecc`](https://github.com/hidran/php-user-management-system/blob/8769ecc/functions.php).

This is the piece that, in a hurried tutorial, would not be there. An upload seems "finished" when the file is saved, but it is not: you have created **three** files (original, thumbnail, intermediate) and linked them to a record. The day the user changes avatar, or is deleted, those three files must be removed — otherwise the upload folder fills up endlessly with orphaned images that nobody serves any more, taking up space and, in the case of personal data, lingering when they should not. Thinking about the complete **life cycle** of a file — creation *and* destruction — is what distinguishes someone who has written an upload in production from someone who copied one from a tutorial. `basename()` returns here too, with the same defensive purpose as before.

## In summary

A file upload is the riskiest input in a web application, and this chapter lined up the defences that make it safe. The **centralized configuration** declares directory, allowed types, and size limit in one place. The **multipart form** carries the bytes, but its client-side aids (`accept`, `MAX_FILE_SIZE`) are conveniences, not security. The **server-side validation** checks the error code, the size, and — above all — the real MIME with `finfo`, never the type declared by the browser. The **saving** uses a random name with an extension derived from the verified MIME, and `move_uploaded_file()` to make sure it is a genuine upload. The **derived images** created with GD resize and, as a side effect, sanitize the content. The **deletion** closes the life cycle, removing the files when the record changes or disappears.

The thread, once again, is that of the whole of Part VI: never trust the input, and determine the nature of a piece of data from its content, not from what the user declares. With uploads the stakes are simply higher, because here a mistake does not manipulate a page — it puts code on your server.
