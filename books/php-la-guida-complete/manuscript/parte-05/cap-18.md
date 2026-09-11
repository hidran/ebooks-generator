# 18. MySQL, phpMyAdmin e le basi di SQL

Un sito dinamico ha bisogno di conservare dati: utenti, post, commenti, impostazioni, token, log. PHP può leggere e scrivere file, ma per dati strutturati e interrogazioni reali serve un database. In questo libro useremo MySQL o MariaDB.

## Collegarsi dalla riga di comando

Apri il client:

```bash
mysql -u root -p
```

Codice completo: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/it/parte-05/cap-18/listing-01.sh)


oppure, con MariaDB:

```bash
mariadb -u root -p
```

Codice completo: [listing-02.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/it/parte-05/cap-18/listing-02.sh)


In ambienti locali come Laragon o XAMPP la password di root può essere vuota. In produzione non deve esserlo.

## Creare un database

```sql
CREATE DATABASE php_guida
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

Codice completo: [listing-03.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/it/parte-05/cap-18/listing-03.sql)


Poi selezionalo:

```sql
USE php_guida;
```

Codice completo: [listing-04.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/it/parte-05/cap-18/listing-04.sql)


`utf8mb4` è la scelta corretta per supportare caratteri accentati, emoji e testi internazionali.

## Creare una tabella

Una tabella `users` minima:

```sql
CREATE TABLE users (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(190) NOT NULL UNIQUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Codice completo: [listing-05.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/it/parte-05/cap-18/listing-05.sql)


Alcune decisioni importanti:

- `id` identifica ogni record;
- `AUTO_INCREMENT` genera il valore automaticamente;
- `PRIMARY KEY` rende l'identificatore univoco;
- `NOT NULL` obbliga a inserire un valore;
- `UNIQUE` impedisce email duplicate.

## Inserire record

```sql
INSERT INTO users (first_name, last_name, email)
VALUES ('Mario', 'Rossi', 'mario@example.com');
```

Codice completo: [listing-06.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/it/parte-05/cap-18/listing-06.sql)


Puoi inserire più righe:

```sql
INSERT INTO users (first_name, last_name, email)
VALUES
  ('Lucia', 'Bianchi', 'lucia@example.com'),
  ('Anna', 'Verdi', 'anna@example.com');
```

Codice completo: [listing-07.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/it/parte-05/cap-18/listing-07.sql)


## Leggere record

```sql
SELECT * FROM users;
```

Codice completo: [listing-08.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/it/parte-05/cap-18/listing-08.sql)


In applicazioni reali evita `SELECT *` quando sai quali colonne servono:

```sql
SELECT id, first_name, last_name, email
FROM users
ORDER BY last_name ASC;
```

Codice completo: [listing-09.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/it/parte-05/cap-18/listing-09.sql)


Per filtrare:

```sql
SELECT id, first_name, email
FROM users
WHERE email = 'mario@example.com';
```

Codice completo: [listing-10.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/it/parte-05/cap-18/listing-10.sql)


## Aggiornare record

```sql
UPDATE users
SET first_name = 'Marco'
WHERE id = 1;
```

Codice completo: [listing-11.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/it/parte-05/cap-18/listing-11.sql)


La clausola `WHERE` è essenziale. Senza `WHERE`, aggiorni tutte le righe della tabella.

## Cancellare record

```sql
DELETE FROM users
WHERE id = 1;
```

Codice completo: [listing-12.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/it/parte-05/cap-18/listing-12.sql)


Anche qui: senza `WHERE`, cancelli tutto. Quando stai imparando, esegui prima una `SELECT` con la stessa condizione:

```sql
SELECT * FROM users WHERE id = 1;
```

Codice completo: [listing-13.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/it/parte-05/cap-18/listing-13.sql)


Se la selezione mostra il record giusto, allora esegui la `DELETE`.

## Aggiungere colonne e indici

Per aggiungere una colonna:

```sql
ALTER TABLE users
ADD role_type VARCHAR(20) NOT NULL DEFAULT 'user';
```

Codice completo: [listing-14.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/it/parte-05/cap-18/listing-14.sql)


Per aggiungere un indice:

```sql
CREATE INDEX users_last_name_index ON users (last_name);
```

Codice completo: [listing-15.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/it/parte-05/cap-18/listing-15.sql)


Gli indici velocizzano ricerche e ordinamenti, ma hanno un costo in scrittura e spazio. Nei progetti iniziali li useremo dove hanno senso: email, chiavi esterne, colonne usate spesso nei filtri.

## phpMyAdmin

phpMyAdmin permette di fare le stesse operazioni da browser: creare database, tabelle, colonne, indici e record. È utile per vedere la struttura e controllare i dati mentre scrivi PHP.

Usalo per esplorare, ma non dimenticare SQL. Nel codice non cliccherai pulsanti: costruirai query, userai connessioni e gestirai risultati.

## Connettersi da PHP con PDO

Per il codice nuovo useremo PDO: funziona con più database, espone un'interfaccia coerente e rende naturale l'uso dei prepared statement. Ecco un esempio minimo con errori gestiti tramite eccezioni e output HTML sanificato:

```php
<?php
declare(strict_types=1);

$pdo = new PDO(
    'mysql:host=localhost;dbname=php_guida;charset=utf8mb4',
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

Codice completo: [listing-16.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/it/parte-05/cap-18/listing-16.php)


Quando una query usa dati provenienti dall'utente, non concatenarli mai nella stringa SQL. Usa sempre prepared statement:

```php
<?php
declare(strict_types=1);

$stmt = $pdo->prepare(
    'SELECT id, first_name, email FROM users WHERE email = :email',
);

$stmt->execute(['email' => $email]);

$user = $stmt->fetch();
```

Codice completo: [listing-17.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-18/it/parte-05/cap-18/listing-17.php)


## In sintesi

MySQL conserva dati strutturati e SQL permette di crearli, leggerli, aggiornarli e cancellarli. Devi conoscere bene `CREATE TABLE`, `INSERT`, `SELECT`, `UPDATE`, `DELETE`, `WHERE`, `ORDER BY`, indici e chiavi primarie. Da qui in avanti questi concetti diventeranno codice PHP nello User Management System.
