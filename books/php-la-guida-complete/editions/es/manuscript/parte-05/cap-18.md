# 18. MySQL, phpMyAdmin y conceptos básicos de SQL

Un sitio dinámico necesita almacenar datos: usuarios, publicaciones, comentarios, configuraciones, tokens, registros. PHP puede leer y escribir archivos, pero para datos estructurados y consultas reales necesita una base de datos. En este libro usaremos MySQL o MariaDB.

## Conéctese desde la línea de comando

Abra el cliente:

```bash
mysql -u root -p
```

Código completo: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/es/parte-05/cap-18/listing-01.sh)


o, con MariaDB:

```bash
mariadb -u root -p
```

Código completo: [listing-02.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/es/parte-05/cap-18/listing-02.sh)


En entornos locales como Laragon o XAMPP, la contraseña de root puede estar en blanco. En producción no tiene por qué ser así.

## Crear una base de datos

```sql
CREATE DATABASE php_guia
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

Código completo: [listing-03.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/es/parte-05/cap-18/listing-03.sql)


Luego selecciónelo:

```sql
USE php_guia;
```

Código completo: [listing-04.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/es/parte-05/cap-18/listing-04.sql)


`utf8mb4` es la opción correcta para admitir caracteres acentuados, emojis y textos internacionales.

## Crea una tabla

Una tabla `users` mínima:

```sql
CREATE TABLE users (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(190) NOT NULL UNIQUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Código completo: [listing-05.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/es/parte-05/cap-18/listing-05.sql)


Algunas decisiones importantes:

- `id` identifica cada registro;
- `AUTO_INCREMENT` genera el valor automáticamente;
- `PRIMARY KEY` hace que el identificador sea único;
- `NOT NULL` te obliga a insertar un valor;
- `UNIQUE` evita correos electrónicos duplicados.

## Insertar registro

```sql
INSERT INTO users (first_name, last_name, email)
VALUES ('Juan', 'García', 'juan@example.com');
```

Código completo: [listing-06.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/es/parte-05/cap-18/listing-06.sql)


Puede insertar varias líneas:

```sql
INSERT INTO users (first_name, last_name, email)
VALUES
  ('Lucía', 'López', 'lucia.lopez@example.com'),
  ('Ana', 'Torres', 'ana@example.com');
```

Código completo: [listing-07.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/es/parte-05/cap-18/listing-07.sql)


## Leer registros

```sql
SELECT * FROM users;
```

Código completo: [listing-08.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/es/parte-05/cap-18/listing-08.sql)


En aplicaciones reales, evite `SELECT *` cuando sepa qué columnas son necesarias:

```sql
SELECT id, first_name, last_name, email
FROM users
ORDER BY last_name ASC;
```

Código completo: [listing-09.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/es/parte-05/cap-18/listing-09.sql)


Para filtrar:

```sql
SELECT id, first_name, email
FROM users
WHERE email = 'juan@example.com';
```

Código completo: [listing-10.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/es/parte-05/cap-18/listing-10.sql)


## Actualizar registros

```sql
UPDATE users
SET first_name = 'Marco'
WHERE id = 1;
```

Código completo: [listing-11.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/es/parte-05/cap-18/listing-11.sql)


La cláusula `WHERE` es esencial. Sin `WHERE`, actualiza todas las filas de la tabla.

## Eliminar registros

```sql
DELETE FROM users
WHERE id = 1;
```

Código completo: [listing-12.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/es/parte-05/cap-18/listing-12.sql)


Aquí también: sin `WHERE`, borras todo. Cuando estés aprendiendo, primero haz un `SELECT` con la misma condición:

```sql
SELECT * FROM users WHERE id = 1;
```

Código completo: [listing-13.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/es/parte-05/cap-18/listing-13.sql)


Si la selección muestra el registro correcto, ejecute `DELETE`.

## Agregar columnas e índices

Para agregar una columna:

```sql
ALTER TABLE users
ADD role_type VARCHAR(20) NOT NULL DEFAULT 'user';
```

Código completo: [listing-14.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/es/parte-05/cap-18/listing-14.sql)


Para agregar un índice:

```sql
CREATE INDEX users_last_name_index ON users (last_name);
```

Código completo: [listing-15.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/es/parte-05/cap-18/listing-15.sql)


Los índices aceleran las búsquedas y la clasificación, pero tienen un coste en escritura y espacio. En proyectos iniciales los usaremos donde tengan sentido: correos electrónicos, claves externas, columnas que se usan a menudo en filtros.

## phpMyAdmin

phpMyAdmin te permite realizar las mismas operaciones que un navegador: crear bases de datos, tablas, columnas, índices y registros. Es útil para ver la estructura y comprobar datos mientras se escribe PHP.

Úselo para explorar, pero no olvide SQL. En el código, no hará clic en botones: creará consultas, utilizará conexiones y administrará resultados.

## Conectarse desde PHP con PDO

Para código nuevo, este libro usa PDO: funciona con varios databases, expone una interfaz coherente y hace que los prepared statements sean el hábito por defecto. El siguiente ejemplo mínimo activa excepciones y escapa la salida antes de imprimir HTML:

```php
<?php
declare(strict_types=1);

$pdo = new PDO(
    'mysql:host=localhost;dbname=php_guia;charset=utf8mb4',
    'root',
    '',
    [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    ],
);

$stmt = $pdo->query('SELECT id, first_name, email FROM users');

foreach ($stmt as $user) {
    echo htmlspecialchars($user['first_name'], ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8')
        . ' - '
        . htmlspecialchars($user['email'], ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8')
        . '<br>';
}
```

Código completo: [listing-16.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/es/parte-05/cap-18/listing-16.php)


Cuando una query usa datos proporcionados por el usuario, nunca los concatene dentro de la cadena SQL. Use siempre prepared statements:

```php
<?php
declare(strict_types=1);

$stmt = $pdo->prepare(
    'SELECT id, first_name, email FROM users WHERE email = :email',
);

$stmt->execute(['email' => $email]);

$user = $stmt->fetch();
```

Código completo: [listing-17.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/es/parte-05/cap-18/listing-17.php)


## En resumen

MySQL almacena datos estructurados y SQL le permite crearlos, leerlos, actualizarlos y eliminarlos. Debe estar familiarizado con `CREATE TABLE`, `INSERT`, `SELECT`, `UPDATE`, `DELETE`, `WHERE`, `ORDER BY`, índices y claves primarias. A partir de ahora estos conceptos se convertirán en código PHP en el Sistema de Gestión de Usuarios.
