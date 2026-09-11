# Prefacio {.unnumbered}

## Por qué existe este libro

Este libro está estructurado como un recorrido para desarrolladores: primero construyes fundamentos sólidos, luego los aplicas en proyectos reales y, finalmente, aprendes a organizar, proteger y publicar código. La estructura sigue el patrón de los buenos manuales técnicos: cada parte introduce un problema, explica las herramientas necesarias y cierra con ejemplos que puedes ejecutar.

PHP se usa en contextos muy distintos: sitios pequeños, aplicaciones empresariales, API, CMS y frameworks modernos. Por eso el libro alterna capítulos de fundamentos, capítulos de proyecto y capítulos de práctica profesional. No necesitas saberlo todo antes de empezar; necesitas aprenderlo en un orden útil.

## A quién va dirigido

El libro es para quienes quieren aprender PHP de forma progresiva y para desarrolladores que ya usan PHP pero quieren alinearse con PHP moderno. Es útil conocer HTML y CSS básicos. SQL, JavaScript, HTTP, Composer y herramientas de deploy se introducen cuando se vuelven necesarios.

## Cómo leer los ejemplos

Los ejemplos están pensados para PHP 8.5 y usan un estilo adecuado para el trabajo diario: tipos explícitos cuando ayudan, `declare(strict_types=1)` en archivos de aplicación, prepared statements para el database, output escapado, password hashes seguros, tokens generados con `random_bytes()` y configuración separada de la lógica.

En los primeros capítulos algunos ejemplos son deliberadamente pequeños porque aíslan un concepto. En los capítulos de proyecto, el código se acerca más al trabajo real: validación, redirect-after-POST, CSRF, sesiones, PDO, autoload, dependency injection y manejo de errores.

## Convenciones tipográficas

- Los nombres de funciones, variables, archivos, comandos y clases aparecen en `monospace`.
- Los bloques PHP representan archivos completos cuando empiezan con `<?php`.
- Los bloques de terminal muestran comandos que debes escribir.
- Las query SQL se separan del código PHP para que el límite entre database y aplicación sea claro.

## Estructura de referencia

El libro sigue convenciones comunes de los manuscritos técnicos: front matter con título, copyright, índice, prefacio e introducción; cuerpo dividido en partes y capítulos; back matter con checklist, conclusiones y colophon. Cada capítulo tiene un objetivo práctico, secciones breves, ejemplos ejecutables y un resumen final.
