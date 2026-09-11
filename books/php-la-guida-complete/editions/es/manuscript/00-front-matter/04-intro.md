# Introducción {.unnumbered}

Soy Hidran Arias y desarrollo con PHP desde 2001. Este libro recoge esa experiencia diaria y la transforma en un recorrido completo: desde las primeras líneas de código hasta aplicaciones estructuradas listas para producción. No es un manual de referencia para consultar a saltos -aunque puedes usarlo así- sino un camino progresivo en el que cada capítulo se construye sobre los anteriores.

## ¿A quién va dirigido?

Para quienes empiezan desde cero con PHP, pero también para desarrolladores que ya lo usan y quieren cubrir lagunas en las características modernas del lenguaje: desde PHP 7 hasta PHP 8.5, con typed properties, enum, readonly, property hooks, el pipe operator, la extensión URI y mucho más. Es útil tener conocimientos básicos de HTML y CSS; todo lo demás se explica paso a paso.

## Cómo está organizado el libro

La ruta se divide en diez partes. En **Partes I a III** preparamos el entorno de desarrollo en Windows, macOS y Linux y aprendemos los fundamentos del lenguaje: sintaxis, variables, tipos, operadores, estructuras de control y funciones. En la **Parte IV** traemos PHP a la web: superglobals, cookies, sistemas de archivos, XML y JSON. **Parte V** presenta MySQL y phpMyAdmin.

Con la **Parte VI** comienza el primer gran proyecto del libro: un completo Sistema de Gestión de Usuarios, con una lista de usuarios ordenable y paginada, búsqueda, CRUD, carga de imágenes, autenticación con inicio de sesión, registro, recordarme y gestión de roles. **Las Partes VII y VIII** cubren la programación orientada a objetos, desde las funciones básicas hasta las más recientes, junto con Composer y el manejo de excepciones.

En **Parte IX** construimos el segundo proyecto: tomamos el blog MVC inicial y lo llevamos hacia el repositorio público `phpenterpriseblog`, con Composer, PSR-4, router testeado, PDO, repositories, services, PSR-7/15, migraciones, autenticación, tests, Docker, Redis y CI/CD. **Parte X** cierra el recorrido con JSON y health check, deploy, envío de email, herramientas avanzadas y una checklist final para PHP 8.5.

## Convenciones

El código aparece en bloques como este:

```php
<?php
echo "Hola, PHP!";
```

Código completo: [listing-01.php](https://github.com/hidran/php-la-guida-completa-code/blob/localized-v4-front-matter-introduction/es/00-front-matter/04-intro/listing-01.php)


Los comandos que se ejecutan en la terminal van precedidos por el contexto en el que se lanzan; los nombres de archivos, funciones y variables aparecen en el texto con `texto monoespaciado`. Los términos técnicos consolidados en inglés (array, form, query, cookie...) permanecen en inglés, como en el uso profesional diario.

Todo el código del libro está diseñado para escribirse y ejecutarse junto con el autor: la mejor manera de leer este libro es con el editor abierto al lado.

Buen viaje por el mundo de PHP.
