# 1. Introducción a PHP

Bienvenido. En este capítulo conoceremos PHP: de dónde viene, cómo ha evolucionado y por qué, décadas después de su nacimiento, sigue siendo uno de los lenguajes más utilizados en el mundo para construir la web. Un poco de historia también sirve para disipar un prejuicio: algunas personas creen que PHP no es un lenguaje de programación "real" en comparación con Java o C#. Suelen ser personas que conocen el PHP de hace veinte años, no el PHP de hoy.

En la segunda parte del capítulo veremos una descripción completa de lo que cubre este libro, parte por parte, y los dos proyectos prácticos que construiremos juntos: un **Sistema de gestión de usuarios** completo y una plataforma de blogs basada en el patrón **MVC**.

## Un poco de historia: del script personal al lenguaje web

PHP no comenzó como un lenguaje de programación. Fue creado por **Rasmus Lerdorf**, un danés a quien tuve la oportunidad de conocer en persona en 2014, en el PHP Day en Verona. Nos dijo que creó este lenguaje de scripting, llamado PHP (en ese momento el acrónimo significaba *Página de inicio personal*) para una necesidad muy concreta: procesar los **formularios** de las páginas HTML. El mecanismo es el que utilizaremos a lo largo del libro: tenemos un formulario, el usuario lo rellena y los datos se envían al servidor. Lerdorf escribió una serie de scripts en C para ser llamados directamente desde páginas HTML, con el fin de procesar esos datos en el lado del servidor, y para la sintaxis tomó prestados elementos de C, C++ y Perl.

Había creado esos guiones para él mismo, para uso personal. Pero a la gente le gustó el lenguaje, otros desarrolladores comenzaron a agregar nuevas funciones y PHP se convirtió en un proyecto de **código abierto**. En ese momento **Zeev Suraski** y **Andi Gutmans** entraron en escena, reescribiendo el corazón del lenguaje: muy poco quedaba del código original de Lerdorf. El nuevo motor, llamado **Zend Engine**, hizo que PHP fuera mucho más rápido.

A partir de ahí la evolución fue continua:

- **PHP 4** introdujo la primera programación orientada a objetos y **gestión de sesiones**;
- **PHP 5** trajo, entre otras cosas, **namespace**;
- con **PHP 8**, la versión en la que se basa este libro, el lenguaje ya no tiene nada que envidiar a los demás: ofrece una programación orientada a objetos completa y madura, construcciones de programación funcionales y un rendimiento excelente.

Hoy en día, entre otras cosas, el acrónimo PHP ya no significa "Página de inicio personal" sino que se ha vuelto recursivo: *PHP: Preprocesador de hipertexto*. Si tienes curiosidad por conocer la historia completa, puedes encontrar todos los detalles en Wikipedia; lo que nos importa es entender que el PHP moderno es un lenguaje profundamente diferente a sus orígenes.

## PHP hoy: mucho más que un lenguaje para la web

El PHP actual no es sólo un lenguaje para generar páginas web. Con PHP puedes escribir scripts que se ejecutan en el servidor directamente desde la **línea de comando**: hacer llamadas a servicios externos, abrir sockets, conectarte vía FTP o SSH; puedes hacer casi cualquier cosa, incluso aplicaciones de escritorio. Es un lenguaje muy versátil y actualmente muy fuerte.

Las versiones recientes han agregado herramientas cada vez más modernas: desde 8.1, por ejemplo, tenemos **enum** (que veremos en el Capítulo 28) y constantes `final` en las clases. Veremos estas características a lo largo del libro, hasta las novedades de PHP 8.5.

Y los números hablan por sí solos: PHP sigue siendo fuerte. Los grandes sitios de comercio electrónico se ejecutan en plataformas escritas en PHP, como Magento o PrestaShop, los frameworks de referencia para la creación de tiendas online. Existe WordPress y, en general, casi el 80% de las páginas web funcionan con código PHP. Si estás aquí es porque te gusta PHP o quieres descubrirlo: en ambos casos estás en el lugar indicado.

## Lo que encontrarás en este libro

Ahora obtengamos una descripción general de lo que estudiaremos, para que sepa qué esperar de cada parte del libro y dónde encajan los proyectos prácticos.

### De lo básico del idioma a la web
En **Parte I** preparamos el entorno de desarrollo. Hay capítulos dedicados a cada sistema operativo: si estás en Windows sigue el Capítulo 2, donde instalamos PHP con Laragon (en el Apéndice A encontrarás las alternativas, como XAMPP); si estás en macOS, sigue el Capítulo 3; si estás en Linux Capítulo 4, donde configuramos una pila LAMP. Cerramos la parte configurando Visual Studio Code para PHP. Un consejo práctico: si ya tiene un entorno de desarrollo con una versión reciente de PHP, está listo: puede saltarse los capítulos de instalación que no se apliquen a su caso e ir directamente a la Parte II.

En **Parte II** cubrimos todos los fundamentos del lenguaje: la sintaxis básica, variables, tipos y constantes, operadores y estructuras de control como `if`/`else`, y bucles.

**La Parte III** está dedicada a las funciones: cómo declararlas y usarlas, y luego las funciones para trabajar con cadenas y aquellas para trabajar con arrays.

En la **Parte IV** ingresamos a PHP para la web: variables **superglobals**, administración de cookies, todas las características para acceder al sistema de archivos con `include` y `require`, cómo procesar XML y el DOM con PHP, y finalmente JSON.

En la **Parte V** veremos cómo conectarse a **MySQL**: qué es, cómo usar phpMyAdmin y una descripción general rápida de `SELECT`, `INSERT`, `UPDATE` y `DELETE`, para que tengas todo lo que necesitas para pasar a tu primer proyecto práctico.

### El primer proyecto: el Sistema de Gestión de Usuarios

**La Parte VI**, la parte más grande del libro, está enteramente dedicada a construir, paso a paso, un **Sistema de gestión de usuarios** (UMS): un sistema completo de gestión de usuarios conectado a una base de datos. Te daré una vista previa de cómo es el resultado final, para que sepas hacia dónde vamos.

La aplicación presenta una lista de usuarios leídos de la base de datos, con posibilidad de insertar un nuevo usuario, modificarlo y eliminarlo. Está la búsqueda: si buscas "Carlos" por ejemplo, la lista se filtra en tiempo real; y hay **paginación** de los resultados. También gestionamos la carga y el procesamiento de imágenes del perfil de cada usuario. Luego construimos un sistema completo de **iniciar sesión**, con la función "recordarme" creada con cookies y la gestión de **roles**: un usuario administrador ve los botones editar y eliminar, mientras que un usuario normal no los vería en absoluto.

Puedes reutilizar este proyecto en cualquiera de tus trabajos donde necesites conectarte a una base de datos, mostrar datos, insertar, modificar y eliminar registros, además de administrar perfiles. Comenzamos desde cero, estilo **procedimental**, y lo evolucionamos gradualmente hacia una estructura organizada que separa responsabilidades, una especie de mini MVC, incluso si aún no usamos clases.

### Programación orientada a objetos y PHP profesional

En la **Parte VII** cubrimos toda la programación orientada a objetos, desde cero hasta los aspectos más avanzados: clases y propiedades, interfaces, clases abstractas, enumeraciones, los **métodos mágicos** de PHP, y luego los namespace y la **autoload**.

En la **Parte VIII** pasamos a las herramientas PHP profesionales: **Composer**, para incluir paquetes externos en nuestros proyectos, y gestión de errores y excepciones.

### El segundo proyecto: el Blog MVC enterprise

En la **Parte IX** tomamos una plataforma de blogging MVC y la llevamos hacia una estructura enterprise: Composer, PSR-4, router con tests, controllers finos, models como DTO, repositories con PDO, services, dependency injection, PSR-7/15, migraciones, autenticación, Docker, Redis y CI/CD. Cada paso sigue los tags del repositorio `phpenterpriseblog`, para que puedas ver el código commit por commit.

En el blog terminado, un usuario puede registrarse o iniciar sesión, publicar un nuevo artículo y, si es el propietario de una publicación, editarlo y eliminarlo; También puedes agregar comentarios. Un visitante que no ha iniciado sesión todavía ve publicaciones de blog públicas.

**La Parte X** cierra el libro, donde llevamos nuestro trabajo hacia producción: JSON y health check, deploy y envío de email con PHP.

Necesitamos estos dos proyectos para poner en práctica todo lo que aprenderemos: nunca nos quedaremos en la pura teoría. Así que comencemos desde cero.

## En resumen
- PHP nació como un conjunto de scripts C creados por Rasmus Lerdorf para procesar formularios de páginas HTML; la sintaxis toma prestados elementos de C, C++ y Perl.
- Ahora de código abierto, su corazón ha sido reescrito por Zeev Suraski y Andi Gutmans con el motor Zend, mucho más rápido; PHP 4 trajo objetos y sesiones, PHP 5 namespace y PHP 8 lo convierte en un lenguaje moderno por derecho propio.
- El PHP actual no es sólo para la web: también se utiliza en la línea de comandos para scripts, sockets, FTP, SSH e incluso aplicaciones de escritorio.
- PHP sigue dominando: WordPress, Magento y la mayoría de las páginas web se ejecutan en PHP.
- El libro cubre todo el lenguaje, desde los conceptos básicos hasta la programación orientada a objetos, desde MySQL hasta Composer, y lo pone en práctica con dos proyectos completos: el Sistema de gestión de usuarios (Parte VI) y el Blog MVC (Parte IX).
