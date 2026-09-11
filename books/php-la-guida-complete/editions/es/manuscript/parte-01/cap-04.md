# 4. Instalar PHP en Linux con XAMPP

En Linux puedes instalar PHP de muchas formas: paquetes de distribución, Docker, compilación manual, Apache con mods de PHP, PHP-FPM con Nginx o entornos integrados. Para comenzar rápidamente, XAMPP sigue siendo una manera fácil de hacerlo porque incluye Apache, PHP, MariaDB y phpMyAdmin en un solo paquete.

En el trabajo profesional, a menudo utilizarás herramientas más específicas, pero XAMPP es cómodo mientras aprendes en local: lo instalas, inicias los servicios, creas un archivo `index.php` e inmediatamente ves el resultado en el navegador.

## Instalar XAMPP

Descargue el paquete de Linux del sitio de Apache Friends. Después de la descarga, haga que el archivo sea ejecutable:

```bash
chmod +x xampp-linux-*-installer.run
```

Código completo: [listing-01.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/es/parte-01/cap-04/listing-01.sh)


Luego inicie el instalador con privilegios administrativos:

```bash
sudo ./xampp-linux-*-installer.run
```

Código completo: [listing-02.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/es/parte-01/cap-04/listing-02.sh)


De forma predeterminada, XAMPP está instalado en `/opt/lampp`. La carpeta principal de sitios es:

```text
/opt/lampp/htdocs
```

Código completo: [listing-03.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/es/parte-01/cap-04/listing-03.txt)


Para iniciar servicios:

```bash
sudo /opt/lampp/lampp start
```

Código completo: [listing-04.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/es/parte-01/cap-04/listing-04.sh)


Para detenerlos:

```bash
sudo /opt/lampp/lampp stop
```

Código completo: [listing-05.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/es/parte-01/cap-04/listing-05.sh)


## El primer archivo PHP

Cree una carpeta de prueba dentro de `htdocs`:

```bash
sudo mkdir /opt/lampp/htdocs/php-guia
```

Código completo: [listing-06.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/es/parte-01/cap-04/listing-06.sh)


Luego crea `index.php`:

```php
<?php
echo "PHP funciona con XAMPP en Linux";
```

Código completo: [listing-07.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/es/parte-01/cap-04/listing-07.php)


Abra su navegador para:

```text
http://localhost/php-guia/
```

Código completo: [listing-08.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/es/parte-01/cap-04/listing-08.txt)


Si aparece el mensaje, Apache está pasando exitosamente el archivo a PHP.

## Permisos del libro de trabajo

Un problema común en Linux es editar archivos en `/opt/lampp/htdocs` sin permisos. Puede cambiar el propietario de la carpeta del proyecto:

```bash
sudo chown -R "$USER":"$USER" /opt/lampp/htdocs/php-guia
```

Código completo: [listing-09.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/es/parte-01/cap-04/listing-09.sh)


Evite trabajar siempre con `sudo`: incomoda al editor, crea archivos con diferentes propietarios y oculta problemas que luego reaparecerán en producción.

## Usa PHP desde la terminal

XAMPP instala el binario PHP dentro de `/opt/lampp/bin`. Puedes ejecutar:

```bash
/opt/lampp/bin/php -v
```

Código completo: [listing-10.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/es/parte-01/cap-04/listing-10.sh)


Si desea simplemente invocarlo con `php`, agregue la ruta a PATH en el archivo de configuración del shell:

```bash
export PATH="/opt/lampp/bin:$PATH"
```

Código completo: [listing-11.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/es/parte-01/cap-04/listing-11.sh)


Después de reabrir la terminal:

```bash
php -v
```

Código completo: [listing-12.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/es/parte-01/cap-04/listing-12.sh)


La terminal es importante porque muchas herramientas PHP, incluido Composer, se utilizan desde la línea de comandos.

## phpMyAdmin y MariaDB

XAMPP incluye phpMyAdmin. Puedes encontrarlo en tu navegador:

```text
http://localhost/phpmyadmin
```

Código completo: [listing-13.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/es/parte-01/cap-04/listing-13.txt)


Desde aquí puede crear bases de datos, tablas, columnas y registros sin recordar inmediatamente todos los comandos SQL. Sin embargo, no utilice phpMyAdmin como un acceso directo permanente: en los capítulos sobre MySQL veremos las consultas porque una aplicación PHP debe poder comunicarse directamente con la base de datos.

Una comprobación rápida desde la terminal:

```bash
/opt/lampp/bin/mysql -u root
```

Código completo: [listing-14.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/es/parte-01/cap-04/listing-14.sh)


Entonces:

```sql
SHOW DATABASES;
```

Código completo: [listing-15.sql](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/es/parte-01/cap-04/listing-15.sql)


## Alternativas: paquetes de distribución

En Ubuntu y Debian puedes instalar PHP desde los repositorios:

```bash
sudo apt update
sudo apt install php php-cli php-mysql apache2 mariadb-server
```

Código completo: [listing-16.sh](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/es/parte-01/cap-04/listing-16.sh)


Esta ruta se acerca más a un servidor real, pero requiere más configuración. Para aprender el idioma, XAMPP está bien; Cuando comience a implementar, será más útil comprender PHP-FPM, el servidor web y las variables de entorno.

## NetBeans en Ubuntu

NetBeans también sigue siendo útil. Es un IDE histórico para PHP: menos liviano que Visual Studio Code, pero conveniente si deseas un entorno ya estructurado con proyectos, ejecución, autocompletado y depuración.

Lo importante es configurar la ruta PHP en las preferencias del IDE. Si usas XAMPP, el binario es:

```text
/opt/lampp/bin/php
```

Código completo: [listing-17.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/es/parte-01/cap-04/listing-17.txt)


Si usas los paquetes de la distribución, normalmente son:

```text
/usr/bin/php
```

Código completo: [listing-18.txt](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-chapter-4/es/parte-01/cap-04/listing-18.txt)


## En resumen

Con Linux hay que prestar atención a tres aspectos: inicio de servicios, permisos de archivos y ruta al binario PHP. XAMPP simplifica la primera configuración y le permite centrarse en el idioma, la base de datos y los proyectos. Cuando todo funcione, siga una regla simple: el mismo código debe poder ser ejecutado por el navegador y el terminal sin sorpresas.
